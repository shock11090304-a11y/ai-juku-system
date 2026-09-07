#!/usr/bin/env python3
"""📚 学習記録ダッシュボード 改修 (2026-09-06) の回帰テスト (in-process・一時 SQLite・READ-ONLY で本番に触れない)。

3視点レビュー (ロジック/データ/UX) で「集計は正しいが、塾長が表を眺める以外に気づく経路が無い」と
確定した 5 点を直した。壊すと元の silent failure に戻るので、それぞれの契約をここで固定する。

  1. 記録の修正 (PATCH /api/study-logs/{id})
       - 自分の記録だけ直せる (他人は 403・未認証は 401・無い記録は 404)
       - 検証は投稿と同じ (0分/1441分/未来日/不正な科目/変更なし は 400)
       - 塾長コメント付きでも直せる (削除は従来どおり 409 のまま)・直してもリアクションは残る
  2. いいね/コメントの生徒への通知 (in-app messages)
       - 1 リアクション = 1 通、宛先はその生徒だけ、二重いいね (already) では増えない
       - コメント本文が通知に入る
  3. タイムラインの生徒絞込 (student_id) と、ヒートマップ行の student_id (行の導線用)
  4. 弱点の退役履歴: 30日再測定の無い弱点は消す前に student_weakness_history へ写し、
       learning-digest が expired_topics として返す。現役の弱点には鮮度 (last_seen_days) が付く
  5. 合格スコア: _recompute_admission_all が全員分を更新し、digest の残日数は保存値でなく本番日から
       毎回計算される。算出日の古さは age_days で見える。scheduler への配線も固定する

使い方: python3 scripts/health_check/test_study_log_improvements.py   (CI: server-tests.yml)
終了コード: 1 件でも ❌ があれば 1。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []

# 架空アドレス (RFC 2606 の予約ドメイン)。★example.com は学習記録ダッシュボードの母集団から
# 意図的に除外される (テスト垢フィルタ) ので、ここでは example.org を使う。
STUDENT_A = "student-a@example.org"
STUDENT_B = "student-b@example.org"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    """一時 SQLite + ダミー env で server/main.py を in-process ロード。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="studylog_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_studylog", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def student_token(mod, sid, hours=1):
    """_verify_session_token の新フォーマット (session.sid.exp.sig)。"""
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def make_student(mod, name, email):
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, plan, trial_end, course, grade, goal) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, "paid", "founder_special", far, "kokuritsu_nankan", "高校3年", "国公立大学"),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


def main():
    print("📚 学習記録ダッシュボード 改修 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    sid_a = make_student(mod, "Student A", STUDENT_A)
    sid_b = make_student(mod, "Student B", STUDENT_B)
    tok_a = {"Authorization": "Bearer " + student_token(mod, sid_a)}
    tok_b = {"Authorization": "Bearer " + student_token(mod, sid_b)}
    mod._RATE_LIMIT_STORE.clear()
    today = mod._today_jst()
    utcnow = datetime.datetime.utcnow()

    # ---------------------------------------------------------------- 1. 記録の修正 (PATCH)
    print("1) 記録の修正 (PATCH /api/study-logs/{id})")
    r = client.post("/api/study-logs", json={"subject": "英語", "minutes": 60, "material": "単語帳"}, headers=tok_a)
    check("生徒が記録を投稿できる", r.status_code == 200, r.text)
    log_id = (r.json() or {}).get("id")
    r = client.patch(f"/api/study-logs/{log_id}", json={"minutes": 45, "subject": "数学", "note": "直した"}, headers=tok_a)
    check("PATCH で時間・科目・メモを修正できる", r.status_code == 200, r.text)
    me = client.get("/api/study-logs/me?days=7&limit=50", headers=tok_a).json()
    lg = next((x for x in me.get("logs", []) if x["id"] == log_id), None)
    check("修正が /me に反映 (45分・数学・メモ)", bool(lg) and lg["minutes"] == 45 and lg["subject"] == "数学" and lg["note"] == "直した", lg)
    check("教材は触っていないので残る", bool(lg) and lg["material"] == "単語帳", lg)
    future = (today + datetime.timedelta(days=1)).isoformat()
    for label, body in [("0分は 400", {"minutes": 0}), ("1441分以上は 400", {"minutes": 2000}),
                        ("未来日は 400", {"studied_date": future}), ("不正な科目は 400", {"subject": "宇宙"}),
                        ("変更なしは 400", {}), ("ページ数 -1 は 400", {"pages": -1})]:
        r = client.patch(f"/api/study-logs/{log_id}", json=body, headers=tok_a)
        check(label, r.status_code == 400, f"{r.status_code} {r.text}")
    r = client.patch(f"/api/study-logs/{log_id}", json={"minutes": 30}, headers=tok_b)
    check("他人の記録は 403", r.status_code == 403, f"{r.status_code} {r.text}")
    r = client.patch(f"/api/study-logs/{log_id}", json={"minutes": 30})
    check("未認証は 401", r.status_code == 401, f"{r.status_code} {r.text}")
    r = client.patch("/api/study-logs/999999", json={"minutes": 30}, headers=tok_a)
    check("存在しない記録は 404", r.status_code == 404, f"{r.status_code} {r.text}")
    me = client.get("/api/study-logs/me?days=7&limit=50", headers=tok_a).json()
    lg = next((x for x in me.get("logs", []) if x["id"] == log_id), None)
    check("弾かれた PATCH は何も変えない (45分のまま)", bool(lg) and lg["minutes"] == 45, lg)

    # ---------------------------------------------------------------- 2. リアクション → 生徒へ通知
    print("2) いいね/コメントの生徒への in-app 通知")
    r = client.post(f"/api/admin/study-logs/{log_id}/react", json={"kind": "like"}, headers=adm)
    check("いいね 200 + notified=true", r.status_code == 200 and r.json().get("notified") is True, r.text)
    r = client.post(f"/api/admin/study-logs/{log_id}/react", json={"kind": "comment", "comment": "いいペースです"}, headers=adm)
    check("コメント 200 + notified=true", r.status_code == 200 and r.json().get("notified") is True, r.text)
    inbox = client.get("/api/messages/me", headers=tok_a).json()
    msgs = inbox.get("messages", [])
    subs = [(m.get("subject") or "") for m in msgs]
    check("生徒の受信箱に未読 2 通", inbox.get("unread_count") == 2, subs)
    check("いいね通知の件名", any("いいね" in s for s in subs), subs)
    check("コメント通知の本文にコメント文", any("いいペースです" in (m.get("body") or "") for m in msgs), [m.get("body") for m in msgs])
    check("通知の本文に日付・科目・分数 (数学 45分)", any("数学 45分" in (m.get("body") or "") for m in msgs), [m.get("body") for m in msgs])
    check("他生徒には届かない", client.get("/api/messages/me", headers=tok_b).json().get("unread_count") == 0)
    r = client.post(f"/api/admin/study-logs/{log_id}/react", json={"kind": "like"}, headers=adm)
    check("二重いいねは already=true", r.status_code == 200 and r.json().get("already") is True, r.text)
    check("二重いいねで通知が増えない", client.get("/api/messages/me", headers=tok_a).json().get("unread_count") == 2)
    r = client.post(f"/api/admin/study-logs/{log_id}/react", json={"kind": "like"}, headers=tok_a)
    check("生徒トークンではリアクションできない (401)", r.status_code == 401, f"{r.status_code}")
    r = client.patch(f"/api/study-logs/{log_id}", json={"minutes": 50}, headers=tok_a)
    check("塾長コメント付きでも修正できる", r.status_code == 200, r.text)
    # ⏱ 1 日 16 時間の上限は「分数を増やす / 日付を動かす」編集だけ検査 (2026-09-07 再点検: メモだけの修正まで 400 だった)
    sid_z = make_student(mod, "Student Z", "z@example.org"); tok_z = {"Authorization": "Bearer " + student_token(mod, sid_z)}
    r = client.post("/api/study-logs", json={"subject": "英語", "minutes": 900}, headers=tok_z)
    check("Z: 900 分の記録", r.status_code == 200, r.text)
    r = client.post("/api/study-logs", json={"subject": "数学", "minutes": 50}, headers=tok_z)
    check("Z: 同日 50 分 (合計 950 ≤ 960)", r.status_code == 200, r.text)
    z_id = r.json().get("id") or r.json().get("log", {}).get("id")
    if not z_id:
        me_z = client.get("/api/study-logs/me?days=1&limit=10", headers=tok_z).json()
        z_id = next((x["id"] for x in me_z.get("logs", []) if x.get("minutes") == 50), None)
    r = client.patch(f"/api/study-logs/{z_id}", json={"minutes": 70}, headers=tok_z)
    check("上限超え (900+70) に増やす修正は 400", r.status_code == 400, f"{r.status_code} {r.text[:80]}")
    r = client.patch(f"/api/study-logs/{z_id}", json={"note": "メモだけ"}, headers=tok_z)
    check("メモだけの修正は通る", r.status_code == 200, r.text[:120])
    r = client.patch(f"/api/study-logs/{z_id}", json={"minutes": 60}, headers=tok_z)
    check("ちょうど上限 (900+60=960) は通る", r.status_code == 200, r.text[:120])
    r = client.patch(f"/api/study-logs/{z_id}", json={"minutes": 40}, headers=tok_z)
    check("減らす修正は通る", r.status_code == 200, r.text[:120])
    # 後続の検査 (タイムライン・合格スコア再計算の人数) は A/B の 2 名前提なので Z は片付ける
    conn = mod.db(); c = conn.cursor()
    c.execute("DELETE FROM study_logs WHERE student_id = ?", (sid_z,)); c.execute("DELETE FROM students WHERE id = ?", (sid_z,))
    conn.commit(); conn.close()
    r = client.delete(f"/api/study-logs/{log_id}", headers=tok_a)
    check("塾長コメント付きの削除は従来どおり 409", r.status_code == 409, f"{r.status_code} {r.text}")
    me = client.get("/api/study-logs/me?days=7&limit=50", headers=tok_a).json()
    lg = next((x for x in me.get("logs", []) if x["id"] == log_id), None)
    rx = (lg or {}).get("reactions") or {}
    check("修正後もリアクションが残る (いいね1・コメント1)", rx.get("likes") == 1 and len(rx.get("comments") or []) == 1, rx)

    # ---------------------------------------------------------------- 3. タイムライン絞込 / ヒートマップ行
    print("3) タイムラインの生徒絞込・ヒートマップ行の student_id")
    r = client.post("/api/study-logs", json={"subject": "英語", "minutes": 20}, headers=tok_b)
    check("B も記録を投稿できる", r.status_code == 200, r.text)
    tl = client.get(f"/api/admin/study-logs/timeline?days=7&limit=200&student_id={sid_a}", headers=adm).json()
    ids = [l.get("student_id") for l in tl.get("logs", [])]
    check("student_id 絞込で A の記録だけ", bool(ids) and all(i == sid_a for i in ids), ids)
    tl_all = client.get("/api/admin/study-logs/timeline?days=7&limit=200", headers=adm).json()
    check("絞込なしなら A と B の両方", {l.get("student_id") for l in tl_all.get("logs", [])} == {sid_a, sid_b}, tl_all.get("logs"))
    hm = client.get("/api/admin/study-logs/heatmap?days=7", headers=adm).json()
    rows = hm.get("students", [])
    check("ヒートマップの各行に student_id (行の導線用)", bool(rows) and all(s.get("student_id") for s in rows) and any(s["student_id"] == sid_a for s in rows), rows)
    row_a = next((s for s in rows if s.get("student_id") == sid_a), {})
    check("ヒートマップの合計は修正後の値 (50分)", row_a.get("total") == 50, row_a)

    # ---------------------------------------------------------------- 4. 弱点の退役履歴
    print("4) 弱点の退役履歴 (student_weakness_history) と digest の expired_topics")
    conn = mod.db()
    c = conn.cursor()
    old = (utcnow - datetime.timedelta(days=40)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts, last_seen_at, aggregated_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (sid_a, "english", "仮定法", 6, 0.4, 6, old, old),
    )
    # 30 日以内の演習が 1 件も無いと集計が早期 return して退役処理まで進まないので、別トピックを 1 件入れる
    c.execute(
        "INSERT INTO question_attempts (student_id, source, subject, topic, is_correct, created_at) VALUES (?,?,?,?,?,?)",
        (sid_a, "practice", "english", "時制", 0, utcnow.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()
    res = mod._run_weakness_aggregation(only_student_id=sid_a)
    check("退役行が履歴へ写されてから消える (archived=1, deleted=1)", res.get("stale_rows_archived") == 1 and res.get("stale_rows_deleted") == 1, res)
    conn = mod.db()
    c = conn.cursor()
    c.execute("SELECT subject, topic, qa_accuracy, qa_attempts, retired_at FROM student_weakness_history WHERE student_id = ?", (sid_a,))
    hist = [dict(x) for x in c.fetchall()]
    check("履歴表に元の値 (仮定法・6回・正答40%) が残る", len(hist) == 1 and hist[0]["topic"] == "仮定法" and hist[0]["qa_attempts"] == 6 and abs(hist[0]["qa_accuracy"] - 0.4) < 1e-6 and hist[0]["retired_at"], hist)
    c.execute("SELECT COUNT(*) AS n FROM student_weakness WHERE student_id = ? AND topic = '仮定法'", (sid_a,))
    check("現役表からは従来どおり消える (配信ロジックは変わらない)", c.fetchone()["n"] == 0)
    c.execute("SELECT COUNT(*) AS n FROM student_weakness WHERE student_id = ? AND topic = '時制'", (sid_a,))
    check("直近の弱点 (時制) は現役表に残る", c.fetchone()["n"] == 1)
    conn.close()
    dg = client.get(f"/api/admin/learning-digest?student_id={sid_a}", headers=adm).json()
    st = (dg.get("students") or [{}])[0]
    ex = st.get("expired_topics") or []
    check("digest の expired_topics に退役弱点 (english/仮定法)", any(e.get("topic") == "仮定法" and e.get("subject") == "english" for e in ex), ex)
    check("退役弱点に鮮度 (last_seen_days ≈ 40)", bool(ex) and ex[0].get("last_seen_days") is not None and 39 <= ex[0]["last_seen_days"] <= 41, ex)
    check("退役弱点に retired_days=0 (今日消えた)", bool(ex) and ex[0].get("retired_days") == 0, ex)
    wt = st.get("weak_topics") or []
    check("現役弱点 (時制) に last_seen_days=0 が付く", any(w.get("topic") == "時制" and w.get("last_seen_days") == 0 for w in wt), wt)
    # 二重集計しても履歴が増殖しない (退役行はもう無い)
    res2 = mod._run_weakness_aggregation(only_student_id=sid_a)
    check("もう一度集計しても履歴は増えない", res2.get("stale_rows_archived") == 0, res2)

    # ---------------------------------------------------------------- 5. 合格スコア再計算・残日数ライブ・算出日
    print("5) 合格スコアの再計算・残日数のライブ計算・算出日 (age_days)")
    res = mod._recompute_admission_all()
    check("現役生徒 2 名が更新される (failed=0)", res.get("updated") == 2 and res.get("failed") == 0, res)
    dg = client.get(f"/api/admin/learning-digest?student_id={sid_a}", headers=adm).json()
    st = (dg.get("students") or [{}])[0]
    adm_a = st.get("admission") or {}
    check("digest に age_days=0 (今日算出)", adm_a.get("age_days") == 0, {k: adm_a.get(k) for k in ("age_days", "days_remaining", "generated_at")})
    exam_date = (adm_a.get("breakdown") or {}).get("exam_date")
    check("breakdown に exam_date", bool(exam_date), adm_a.get("breakdown"))
    expect = max(0, (datetime.date.fromisoformat(str(exam_date)[:10]) - today).days) if exam_date else None
    check("残日数は本番想定日から算出", expect is not None and st.get("days_to_exam") == expect, (st.get("days_to_exam"), expect))
    conn = mod.db()
    c = conn.cursor()
    ten = (utcnow - datetime.timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE admission_likelihood SET generated_at = ?, days_remaining = ? WHERE student_id = ?", (ten, 999, sid_a))
    conn.commit()
    conn.close()
    dg = client.get(f"/api/admin/learning-digest?student_id={sid_a}", headers=adm).json()
    st = (dg.get("students") or [{}])[0]
    check("算出日が 10 日前なら age_days=10 (古さが見える)", (st.get("admission") or {}).get("age_days") == 10, st.get("admission"))
    check("残日数は保存値 (999) ではなくライブ計算のまま", st.get("days_to_exam") == expect, (st.get("days_to_exam"), expect))
    src = open(MAIN_PY, encoding="utf-8").read()
    check("scheduler に admission_recompute_run の配線 (毎朝 4:00 に自動再計算)",
          "admission_recompute_run" in src and "await asyncio.to_thread(_recompute_admission_all)" in src)
    r = client.post("/api/admin/admission/recompute-all", headers=adm)
    check("手動ボタンの API も同じ関数で動く", r.status_code == 200 and r.json().get("updated") == 2, r.text)

    # ---------------------------------------------------------------- 6. 生徒削除の cascade (孤児化防止・CLAUDE.md ルール)
    print("6) 生徒に紐づく新テーブルが削除 cascade の全リストに入っている")
    check("_ORPHAN_SWEEP_TABLES に student_weakness_history", "student_weakness_history" in mod._ORPHAN_SWEEP_TABLES)
    check("プレビュー/個別削除/purge の 3 リストにも入っている (ソース出現 4 箇所以上)", src.count('"student_weakness_history"') >= 4, src.count('"student_weakness_history"'))

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
