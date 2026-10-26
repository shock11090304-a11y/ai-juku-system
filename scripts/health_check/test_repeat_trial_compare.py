#!/usr/bin/env python3
"""🤝 「体験の重複再取得」の赤枠で 2 つのアカウントを見比べて統合する (2026-10-27) の回帰テスト (in-process・一時 SQLite)。

  背景: 通塾生も status='trial' (trial_end 10 年後) で作られるので、塾生アプリに別メールで登録し直した在籍生が赤枠に出る
        (2026-10-26 に 2 名)。そこで「本契約へ切替」を押すと status='expired' になりアプリから締め出される。
  1. 一覧 API: 比べる相手 (理由文の最後の #ID) の要約 (登録日・最終ログイン・受講クラス・学習の量・カード登録)。
     can_convert は疑いの側か相手のどちらかが通塾生なら false。相手が統合・削除済みなら prior=None
  2. 「本契約へ切替」API は通塾生 (相手が通塾生のときも) を 409 で止め、何も書かない。通塾生でない体験者は従来どおり
  3. 統合 API を止める 2 つ: 赤枠から (from_repeat_trial) でどちらも通塾生でない / 両方に別々の Stripe サブスク → 409
  4. 統合の下見: 出欠の食い違いを attend_diffs で返し、件数は実行と同じ数え方。何も書かない
  5. 統合の実行: 出欠は「塾長の記録 → 新しい申告」(出欠が同じでも塾長の記録を残す・'T' と ' ' の書式混在でも順序どおり)。
     疑いフラグは残す側の疑いが消す側を指すときだけ外す。カード指紋も引き継ぐ。消す側のメールでログインできるかを返す
  6. AI: 体験終了・解約・公開ページの 7 日体験の「AI 可」は数えない。逆向き (残す側の AI 可が体験の名残) でも AIなし枠のまま
  7. Stripe: 両方に別々のサブスク ID / 片方だけ通塾生で、もう片方にサブスク ID が残る → 409 (解約 webhook が通塾生を canceled にする)。
     生きているかは status でなく ID の有無で見る (支払い遅延の降格は status=canceled でも ID を残す)。顧客 ID とサブスク ID は組で
     引き継ぐ。退塾した元塾生は通塾生に数えない
  8. 画面 (ceo.html): 統合ボタンは「どちらかが通塾生」のときだけ (氏名違いの同一カードには出さない)。切替は can_convert で出し分け
"""
import importlib.util
import json
import os
import sys
import tempfile
import time
import base64, hashlib, hmac

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []
FAR = "2036-10-23T00:00:00"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="repeat_cmp_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_repeat_cmp", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    mod._REPEAT_BACKFILL_DONE = True   # 遡及スキャンは別の関心事。ここでは入れたフラグだけを見る
    return mod


def admin_token(mod, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = mod._admin_token_payload(str(exp))
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def add_student(c, name, email, status="trial", course="kokuritsu_nankan", created="2026-10-01 00:00:00", classes=None,
                last_login=None, ai_disabled=0, trial_end=FAR, **extra):
    cols = {"name": name, "email": email, "status": status, "trial_end": trial_end, "course": course, "grade": "高2",
            "class_labels": json.dumps(classes or [], ensure_ascii=False), "ai_disabled": ai_disabled,
            "created_at": created, "last_login_at": last_login, **extra}
    c.execute(f"INSERT INTO students ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", tuple(cols.values()))
    c.execute("SELECT id FROM students WHERE email = ?", (email,))
    return c.fetchone()["id"]


def attend(c, sid, label, day, status, source, updated):
    c.execute("INSERT INTO class_attend (student_id, class_label, att_date, status, source, updated_at) VALUES (?,?,?,?,?,?)",
              (sid, label, day, status, source, updated))


def flag_against(mod, suspect_id, prior_id, kind="name"):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT id, name, email, grade, trial_end, paid_since, status, created_at FROM students WHERE id = ?", (prior_id,))
    reason = mod._repeat_reason_text(dict(c.fetchone()), kind)
    conn.close()
    mod._flag_repeat_suspect(suspect_id, reason)


def one(c, sql, *params):
    c.execute(sql, params)
    return c.fetchone()


def main():
    print("🤝 体験の重複再取得: 見比べて統合 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    merge = lambda keep, frm, **kw: client.post(f"/api/admin/students/{keep}/merge", json={"from_id": frm, **kw}, headers=adm)
    L1, L2 = "月曜2限 英文法 Lv.1", "月曜3限 長文読解 Lv.1"

    conn = mod.db(); c = conn.cursor()
    # ① 通塾生の二重アカウント: 前からある P1 (学習データあり) と、塾生アプリの登録し直しで今日できた S1
    p1 = add_student(c, "重複 一郎", "old-addr@example.org", created="2026-09-03 12:00:00", classes=[L1, L2, "金曜2限 英検2級対策"],
                     last_login="2026-10-22 15:00:00", payment_fingerprint="fp_test_1")
    s1 = add_student(c, "重複　一郎", "new-addr@example.org", created="2026-10-26 13:00:00", classes=[L1, L2],
                     last_login="2026-10-26 14:15:00", ai_disabled=1)
    for i in range(3):
        c.execute("INSERT INTO study_logs (student_id, studied_date, subject, minutes) VALUES (?,?,?,?)", (p1, f"2026-10-0{i+1}", "英語", 30))
    for i in range(2):
        c.execute("INSERT INTO question_attempts (student_id, source, subject, topic, is_correct, created_at) VALUES (?,?,?,?,?,?)", (p1, "practice", "english", "時制", 1, "2026-10-03 10:00:00"))
    c.execute("INSERT INTO homework_assignments (student_id, title) VALUES (?,?)", (p1, "宿題 1"))
    # 出欠: A=消す側で後から欠席申告 / B=塾長の記録 vs 新しい自己申告 / C=同じ / D=時刻の書式が 'T' と ' ' で混在 /
    #       E=出欠は同じで P1 だけ塾長の記録
    attend(c, p1, L2, "2026-10-26", "present", "self", "2026-10-20 10:00:00")       # A (古い)
    attend(c, s1, L2, "2026-10-26", "absent", "self", "2026-10-26 14:20:00")        # A (新しい)
    attend(c, p1, L1, "2026-10-19", "absent", "admin", "2026-10-01 09:00:00")       # B (塾長の記録・古い)
    attend(c, s1, L1, "2026-10-19", "present", "self", "2026-10-26 14:21:00")       # B (自己申告・新しい)
    attend(c, p1, L1, "2026-10-26", "present", "self", "2026-10-20 10:00:00")       # C
    attend(c, s1, L1, "2026-10-26", "present", "self", "2026-10-26 14:22:00")       # C
    attend(c, p1, L1, "2026-10-12", "late", "self", "2026-10-26T15:00:00")          # D (新しい・'T' 区切り)
    attend(c, s1, L1, "2026-10-12", "present", "self", "2026-10-26 14:00:00")       # D (古い・' ' 区切り)
    attend(c, p1, L1, "2026-10-05", "present", "admin", "2026-10-05 09:00:00")      # E (塾長の記録・古い)
    attend(c, s1, L1, "2026-10-05", "present", "self", "2026-10-26 14:23:00")       # E (自己申告・新しい)
    # ② 通塾生でない体験の取り直し: 前の体験 P2 と、新しい体験 S2 (切替はこれまでどおり出す・統合は止める)
    p2 = add_student(c, "体験 次郎", "lp-old@example.org", status="expired", course=None, created="2026-08-01 00:00:00", trial_end="2026-08-15T00:00:00")
    s2 = add_student(c, "体験 次郎", "lp-new@example.org", course=None, created="2026-10-25 00:00:00", trial_end="2026-11-10T00:00:00")
    # ③ 相手が統合・削除済み
    s3 = add_student(c, "相手 不明", "gone@example.org", course=None, created="2026-10-24 00:00:00")
    # ④ AIなし枠の通塾生 S4 と、体験が終わった古い体験アカウント P4 (AI 可のまま)
    p4 = add_student(c, "古体験 四郎", "old-trial4@example.org", status="expired", course=None, trial_end="2026-05-01T00:00:00", ai_disabled=0)
    s4 = add_student(c, "古体験 四郎", "juku4@example.org", ai_disabled=1)
    # ⑤ 通塾生 P5 が公開ページの体験で作り直した S5 (S5 は通塾生ではない)
    p5 = add_student(c, "在籍 五郎", "juku5@example.org", ai_disabled=1)
    s5 = add_student(c, "在籍 五郎", "lp5@example.org", course=None, trial_end="2026-11-10T00:00:00")
    # ⑥ 両方に別々の Stripe サブスク
    p6 = add_student(c, "両方 六子", "sub6a@example.org", stripe_subscription_id="sub_test_a")
    s6 = add_student(c, "両方 六子", "sub6b@example.org", stripe_subscription_id="sub_test_b")
    # ⑦ 前のアカウントの氏名に「#5)」がある (理由文の最初の #数字) を拾わない)
    p7 = add_student(c, "名前 #5) 七海", "p7@example.org")
    s7 = add_student(c, "名前 #5) 七海", "s7@example.org")
    # ⑧ 残す側 Q8 の疑いは第三のアカウント (#777777) を指す / Q8 は子メール登録済み (消す側のメールは保護者メール欄へ)
    q8 = add_student(c, "三重 八重", "q8@example.org", student_email="kid8@example.org", student_email_verified=1)
    r8 = add_student(c, "三重 八重", "r8@example.org")
    # ⑨ 通塾生 P9 と、カード登録つきの公開ページの体験 S9 (在籍中のサブスク)
    p9 = add_student(c, "九 九", "juku9@example.org")
    s9 = add_student(c, "九 九", "lp9@example.org", course=None, trial_end="2026-11-10T00:00:00", stripe_customer_id="cus_test_9", stripe_subscription_id="sub_test_9")
    # ⑩ 通塾生どうし: 残す側は顧客 ID だけ (サブスクなし)、消す側は顧客とサブスクの組
    p10 = add_student(c, "十 十", "p10@example.org", stripe_customer_id="cus_test_a")
    s10 = add_student(c, "十 十", "s10@example.org", stripe_customer_id="cus_test_b", stripe_subscription_id="sub_test_b")
    # ⑪ 退塾した元塾生 P11 (course は残る・status=canceled だが支払い遅延の降格でサブスク ID は残る) と、在籍中の通塾生 S11 (別のサブスク)
    p11 = add_student(c, "十一 退塾", "p11@example.org", status="canceled", stripe_customer_id="cus_test_old", stripe_subscription_id="sub_test_old")
    s11 = add_student(c, "十一 退塾", "s11@example.org", stripe_customer_id="cus_test_new", stripe_subscription_id="sub_test_new")
    s12 = add_student(c, "十一 退塾", "lp12@example.org", course=None, trial_end="2026-11-10T00:00:00")
    conn.commit(); conn.close()
    flag_against(mod, s1, p1); flag_against(mod, s2, p2); flag_against(mod, s4, p4); flag_against(mod, s5, p5)
    flag_against(mod, s6, p6); flag_against(mod, s7, p7); flag_against(mod, s12, p11)
    mod._flag_repeat_suspect(s3, "氏名一致: 過去に「相手 不明」(別メール・登録 2026-01-01・体験終了・#999999) が存在。体験の再取得の可能性。")
    mod._flag_repeat_suspect(q8, "氏名一致: 過去に「三重八重」(別メール・登録 2026-01-01・体験中・#777777) が存在。体験の再取得の可能性。")

    print("1) 一覧 API: 比べる相手の要約と can_convert")
    r = client.get("/api/admin/students/repeat-trial-suspects", headers=adm)
    check("200", r.status_code == 200, r.text[:200])
    rows = {x["id"]: x for x in (r.json().get("suspects") if r.status_code == 200 else [])}
    check("9 名が出る", set(rows) == {s1, s2, s3, s4, s5, s6, s7, q8, s12}, sorted(rows))
    x1 = rows.get(s1, {})
    check("S1: prior_id は理由文の #ID (= P1)", x1.get("prior_id") == p1, x1.get("prior_id"))
    a1, pr1 = x1.get("account") or {}, x1.get("prior") or {}
    check("S1: 通塾生 → can_convert=false / account.enrolled", x1.get("can_convert") is False and a1.get("enrolled") is True, (x1.get("can_convert"), a1.get("enrolled")))
    check("P1 の要約: 学習記録 3 件 (最終 2026-10-03)・解答 2・宿題 1・出欠 5・受講クラス 3",
          pr1.get("study_logs") == 3 and pr1.get("study_logs_last") == "2026-10-03" and pr1.get("attempts") == 2
          and pr1.get("homework") == 1 and pr1.get("attend") == 5 and len(pr1.get("classes") or []) == 3, pr1)
    check("P1 の要約: メール・登録日・最終ログイン・カード登録なし",
          pr1.get("email") == "old-addr@example.org" and str(pr1.get("created_at", "")).startswith("2026-09-03")
          and str(pr1.get("last_login_at", "")).startswith("2026-10-22") and pr1.get("card") is False, pr1)
    check("P6 の要約: カード登録あり", (rows.get(s6, {}).get("prior") or {}).get("card") is True, rows.get(s6, {}).get("prior"))
    x2 = rows.get(s2, {})
    check("S2 (どちらも通塾生でない): can_convert=true・prior=P2", x2.get("can_convert") is True and (x2.get("prior") or {}).get("id") == p2, x2)
    check("S5 (相手 P5 が通塾生): can_convert=false", rows.get(s5, {}).get("can_convert") is False, rows.get(s5))
    x3 = rows.get(s3, {})
    check("S3: 相手 #999999 は無い → prior=None・prior_id は残す", x3.get("prior") is None and x3.get("prior_id") == 999999, x3)
    check("S7: 氏名の「#5)」ではなく最後の #ID (= P7) を拾う", rows.get(s7, {}).get("prior_id") == p7, rows.get(s7, {}).get("prior_id"))
    check("S12: 相手 P11 は退塾した元塾生 (canceled) → 通塾生に数えず can_convert=true",
          rows.get(s12, {}).get("can_convert") is True and (rows.get(s12, {}).get("prior") or {}).get("enrolled") is False, rows.get(s12))

    print("2) 「本契約へ切替」は通塾生を止める")
    r = client.post(f"/api/admin/students/{s1}/repeat-trial-convert", headers=adm)
    check("通塾生 → 409", r.status_code == 409, f"{r.status_code} {r.text[:200]}")
    r = client.post(f"/api/admin/students/{s5}/repeat-trial-convert", headers=adm)
    check("相手が通塾生 → 409", r.status_code == 409, f"{r.status_code} {r.text[:200]}")
    conn = mod.db(); c = conn.cursor()
    row1, row5 = one(c, "SELECT status, repeat_trial_suspect FROM students WHERE id = ?", s1), one(c, "SELECT status, repeat_trial_suspect FROM students WHERE id = ?", s5)
    check("何も書かない (trial のまま・疑いフラグも残る)", all(x["status"] == "trial" and int(x["repeat_trial_suspect"] or 0) == 1 for x in (row1, row5)), (dict(row1), dict(row5)))
    conn.close()

    print("3) 統合 API を止める 2 つ")
    r = merge(p2, s2, dry_run=True, from_repeat_trial=True)
    check("赤枠から・どちらも通塾生でない → 409 (下見でも)", r.status_code == 409, f"{r.status_code} {r.text[:200]}")
    r = merge(p6, s6, dry_run=True)
    check("両方に別々の Stripe サブスク → 409 (下見でも)", r.status_code == 409, f"{r.status_code} {r.text[:200]}")
    r = client.post(f"/api/admin/students/{s2}/repeat-trial-convert", headers=adm)
    check("通塾生でない体験者は従来どおり切替できる (200)", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

    print("4) 統合の下見")
    r = merge(p1, s1, dry_run=True, from_repeat_trial=True)
    check("200", r.status_code == 200, r.text[:200])
    diffs = {(d["class_label"], d["att_date"]): d for d in (r.json().get("attend_diffs") if r.status_code == 200 else [])}
    check("食い違いは 3 日 (出欠が同じ日 C・E は出さない)", len(diffs) == 3 and (L1, "2026-10-26") not in diffs and (L1, "2026-10-05") not in diffs, list(diffs))
    check("A: 消す側の新しい欠席を残す", (diffs.get((L2, "2026-10-26")) or {}).get("kept") == "from", diffs.get((L2, "2026-10-26")))
    check("B: 塾長の記録 (残す側) を残す", (diffs.get((L1, "2026-10-19")) or {}).get("kept") == "keep", diffs.get((L1, "2026-10-19")))
    check("D: 'T' 区切りの新しい方 (残す側の遅刻) を残す", (diffs.get((L1, "2026-10-12")) or {}).get("kept") == "keep", diffs.get((L1, "2026-10-12")))
    rp = merge(s1, p1, dry_run=True, from_repeat_trial=True).json()   # 実行と同じ向きの下見 (件数を実行と比べる)
    conn = mod.db(); c = conn.cursor()
    check("下見では何も書かない (P1 の出欠は元のまま・S1 も残る)",
          one(c, "SELECT status FROM class_attend WHERE student_id = ? AND class_label = ? AND att_date = ?", p1, L2, "2026-10-26")["status"] == "present"
          and one(c, "SELECT COUNT(*) AS n FROM students WHERE id = ?", s1)["n"] == 1)
    conn.close()

    print("5) 統合の実行 (残す側=疑いの付いた S1・from_repeat_trial)")
    r = merge(s1, p1, dry_run=False, from_repeat_trial=True)
    check("200", r.status_code == 200, r.text[:200])
    j = r.json() if r.status_code == 200 else {}
    check("応答の attend_diffs は 3 件", len(j.get("attend_diffs") or []) == 3, j.get("attend_diffs"))
    check("出欠の件数は下見と実行で同じ (移る 3 / 片方だけ残す 2)",
          (rp.get("moved") or {}).get("class_attend") == (j.get("moved") or {}).get("class_attend") == 3
          and (rp.get("conflicts") or {}).get("class_attend") == (j.get("conflicts") or {}).get("class_attend") == 2, (rp.get("moved"), rp.get("conflicts"), j.get("moved"), j.get("conflicts")))
    check("消す側のメールでログインできる (子メール欄・確認済み)", j.get("from_email_login") is True and j.get("from_email_saved_as") == "student_email", j)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT class_label, att_date, status, source FROM class_attend WHERE student_id = ?", (s1,))
    att = {(x["class_label"], str(x["att_date"])[:10]): (x["status"], x["source"]) for x in c.fetchall()}
    check("A: 残す側 (S1) の新しい欠席", att.get((L2, "2026-10-26")) == ("absent", "self"), att.get((L2, "2026-10-26")))
    check("B: 消す側 (P1) の塾長の記録 (欠席) が勝つ", att.get((L1, "2026-10-19")) == ("absent", "admin"), att.get((L1, "2026-10-19")))
    check("C: 同じ出席は 1 行", att.get((L1, "2026-10-26")) == ("present", "self"), att.get((L1, "2026-10-26")))
    check("D: 消す側の新しい遅刻 ('T' 区切り) が勝つ", att.get((L1, "2026-10-12")) == ("late", "self"), att.get((L1, "2026-10-12")))
    check("E: 出欠は同じでも消す側の塾長の記録を残す", att.get((L1, "2026-10-05")) == ("present", "admin"), att.get((L1, "2026-10-05")))
    check("出欠は 5 行 (重複なし)", len(att) == 5 and one(c, "SELECT COUNT(*) AS n FROM class_attend WHERE student_id = ?", s1)["n"] == 5, att)
    row = one(c, "SELECT repeat_trial_suspect, repeat_trial_reason, class_labels, payment_fingerprint, ai_disabled FROM students WHERE id = ?", s1)
    check("S1 の疑いフラグは外れ、理由文は残る (遡及スキャンが立て直さない)", int(row["repeat_trial_suspect"] or 0) == 0 and bool(row["repeat_trial_reason"]), dict(row))
    check("受講クラスは和集合 (金曜2限 も入る)", "金曜2限 英検2級対策" in (row["class_labels"] or ""), row["class_labels"])
    check("カード指紋を引き継ぐ", row["payment_fingerprint"] == "fp_test_1", row["payment_fingerprint"])
    check("通塾生どうし (P1 は在籍中・AI 可) → AI は使える", int(row["ai_disabled"] or 0) == 0, row["ai_disabled"])
    check("P1 は削除・学習記録は S1 へ", one(c, "SELECT COUNT(*) AS n FROM students WHERE id = ?", p1)["n"] == 0
          and one(c, "SELECT COUNT(*) AS n FROM study_logs WHERE student_id = ?", s1)["n"] == 3)
    ev = json.loads(one(c, "SELECT props FROM events WHERE name = 'admin_student_merge' ORDER BY id DESC LIMIT 1")["props"])
    check("監査 event に attend_diffs 件数と cleared_repeat_flag", ev.get("attend_diffs") == 3 and ev.get("cleared_repeat_flag") is True, ev)
    conn.close()
    mod._backfill_repeat_suspects()
    conn = mod.db(); c = conn.cursor()
    check("遡及スキャン後も S1 のフラグは 0", one(c, "SELECT COUNT(*) AS n FROM students WHERE id = ? AND COALESCE(repeat_trial_suspect,0) = 1", s1)["n"] == 0)
    conn.close()

    print("6) 疑いフラグ・メール・AI の細かい決まり")
    r = merge(q8, r8, dry_run=False, from_repeat_trial=True)
    j8 = r.json() if r.status_code == 200 else {}
    check("Q8←R8 は 200", r.status_code == 200, r.text[:200])
    check("子メール登録済みの残す側: 消す側のメールは保護者メール欄・ログインには使えない", j8.get("from_email_login") is False and j8.get("from_email_saved_as") == "parent_email", j8)
    conn = mod.db(); c = conn.cursor()
    check("Q8 の疑いは第三のアカウント (#777777) を指す → フラグは残す", int(one(c, "SELECT repeat_trial_suspect FROM students WHERE id = ?", q8)["repeat_trial_suspect"] or 0) == 1)
    conn.close()
    r = merge(s4, p4, dry_run=True, from_repeat_trial=True)
    check("S4←P4 (AIなし枠の通塾生 ← 体験終了・AI 可): 200 で ai_disabled は変えない",
          r.status_code == 200 and "ai_disabled" not in (r.json().get("field_changes") or {}), r.text[:300])
    r = merge(p4, s4, dry_run=True, from_repeat_trial=True)
    check("逆向き P4←S4 (残す側の AI 可は体験終了の名残): ai_disabled=1 (AIなし枠のまま)",
          r.status_code == 200 and (r.json().get("field_changes") or {}).get("ai_disabled") == 1, r.text[:300])
    r = merge(p5, s5, dry_run=True, from_repeat_trial=True)
    check("P5←S5 (AIなし枠の通塾生 ← 期限内の 7 日体験・AI 可): ai_disabled は変えない",
          r.status_code == 200 and "ai_disabled" not in (r.json().get("field_changes") or {}), r.text[:300])

    print("7) Stripe のサブスク")
    r = merge(p9, s9, dry_run=True, from_repeat_trial=True)
    check("通塾生 ← 在籍中のサブスクを持つ体験: 409 (下見でも)", r.status_code == 409, f"{r.status_code} {r.text[:200]}")
    r = merge(s9, p9, dry_run=True, from_repeat_trial=True)
    check("向きを逆にしても 409", r.status_code == 409, f"{r.status_code} {r.text[:200]}")
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET status = 'canceled', stripe_subscription_id = NULL WHERE id = ?", (s9,))   # 家庭が解約 → webhook が canceled・ID を NULL に
    conn.commit(); conn.close()
    r = merge(p9, s9, dry_run=True, from_repeat_trial=True)
    fc9 = (r.json() if r.status_code == 200 else {}).get("field_changes") or {}
    check("解約後 (ID が消えた後) は統合でき、サブスクは通塾生に引き継がない",
          r.status_code == 200 and "stripe_subscription_id" not in fc9, r.text[:300])
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET stripe_subscription_id = 'sub_test_9b' WHERE id = ?", (s9,))   # 支払い遅延の降格: canceled だが ID は残る
    conn.commit(); conn.close()
    r = merge(p9, s9, dry_run=True, from_repeat_trial=True)
    check("status が canceled でもサブスク ID が残っていれば 409 (降格は Stripe のサブスクを止めていない)", r.status_code == 409, f"{r.status_code} {r.text[:200]}")
    r = merge(p10, s10, dry_run=True)
    fc10 = (r.json() if r.status_code == 200 else {}).get("field_changes") or {}
    check("通塾生どうし・消す側だけサブスク: 顧客とサブスクを組で引き継ぐ (顧客 A + B のサブスクにしない)",
          fc10.get("stripe_customer_id") == "cus_test_b" and fc10.get("stripe_subscription_id") == "sub_test_b", r.text[:300])
    r = merge(p11, s11, dry_run=True)
    check("残す側は退塾 (status=canceled でもサブスク ID が残る)・消す側にも別のサブスク: 409", r.status_code == 409, f"{r.status_code} {r.text[:200]}")

    r = client.get("/api/admin/students/repeat-trial-suspects", headers=adm)
    ids = sorted(x["id"] for x in r.json().get("suspects", []))
    # S10 は 5) の遡及スキャンが同名の P10 に対して拾う (S9 も拾われるが、7) で解約済み = 一覧の対象外)
    check("赤枠: S1 (統合)・S2 (切替)・R8 (統合で消えた) が消え、残りは出たまま", ids == sorted([s3, s4, s5, s6, s7, q8, s10, s12]), ids)

    print("8) 画面 (ceo.html)")
    with open(os.path.join(REPO, "ceo.html"), encoding="utf-8") as f:
        html = f.read()
    check("切替ボタンは can_convert が false なら出さない", "s.can_convert === false ? '' :" in html)
    check("統合ボタンは「どちらかが通塾生」のときだけ・氏名違いの同一カードには出さない・主ボタンは氏名が同じときだけ",
          "const canMerge = enrolledPair && (sameName || !cardMatch);" in html and "${canMerge ? mergeBtn(first, second, sameName)" in html)
    check("統合ボタン (data-rt-action=\"merge\" と残す側・消す側の ID)", 'data-rt-action="merge" data-rt-keep=' in html and "data-rt-from=" in html)
    check("下見 (dry_run: true) をしてから実行・どちらも from_repeat_trial",
          "dry_run: true, from_repeat_trial: true" in html and "dry_run: false, from_repeat_trial: true" in html
          and html.index("dry_run: true, from_repeat_trial: true") < html.index("dry_run: false, from_repeat_trial: true"))
    check("確認文のログイン案内はサーバの from_email_login で出し分け", "p.from_email_login ?" in html)
    check("統合中は自動更新で描き直さない・統合後は名簿も取り直す",
          "if (_rtState.busy && !force) return;" in html and "loadRepeatTrialSuspects({ force: true })" in html and "loadLiveMetrics({ dropOlder: true })" in html)
    check("const は初回の呼び出しより前に宣言", html.index("const _rtState =") < html.index("      loadRepeatTrialSuspects();\n"))

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗")
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
