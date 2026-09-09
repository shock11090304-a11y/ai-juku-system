#!/usr/bin/env python3
"""🎯 生徒画面レビュー反映 (2026-09-09) の回帰テスト (in-process・一時 SQLite・メール/LINE は偽物)。

3 視点レビューで見つかった「続ける仕組みが端末の中で閉じている」問題への対処を固定する:
  - /api/student/activity-summary: 演習・学習記録・「できた！」から連続日数と最終活動日をサーバ実績で算出
  - /api/student/coach-done: 1 日 1 回の冪等記録 (events name='coach_done')
  - /api/auth/me が line_linked (真偽値) を返し、LINE の userId 自体は返さない
  - 週次レポート: 演習ゼロ週でも「直近 28 日に演習あり」の生徒には短い軽量メール (生徒+保護者)・週 1 回・最大 2 週連続、
    休眠層と一度も解いていない生徒は従来どおりスキップ
  - 週半ばの一声 cron: 今週 0 問 かつ 直近 4 週に演習ありの生徒だけ・LINE 優先・6 日 dedup・dry_run は無送信・ENABLED=0 で無送信
  - mypage.html / mypage.js のソース検査: 無限待ちの打ち切り・タイムアウト・?v= バンプ・演習カード統合・NEW バッジ撤去
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
CRON = "test-cron-secret"
JST = datetime.timezone(datetime.timedelta(hours=9))


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="sux_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid", "CRON_SECRET": CRON,
        "MIDWEEK_NUDGE_ENABLED": "1", "ZERO_WEEK_REPORT_ENABLED": "1",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_sux", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def student_token(mod, sid, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def mk(mod, name, email, status="paid", course=None, student_email=None, verified=0, parent_email=None, line_user_id=None):
    conn = mod.db(); c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, plan, trial_end, course, grade, student_email, student_email_verified, "
        "parent_email, parent_email_enabled, line_user_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (name, email, status, "founder_special", far, course, "高校2年", student_email, verified, parent_email, 1, line_user_id),
    )
    conn.commit(); c.execute("SELECT id FROM students WHERE email = ?", (email,)); sid = c.fetchone()["id"]
    conn.close()
    return sid


def utc_str(dt):
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def add_attempt(mod, sid, at, correct=1):
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO question_attempts (student_id, source, subject, is_correct, created_at) VALUES (?,?,?,?,?)",
              (sid, "practice", "english", correct, utc_str(at)))
    conn.commit(); conn.close()


def add_notification(mod, sid, template, days_ago, success=1):
    conn = mod.db(); c = conn.cursor()
    at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)
    c.execute("INSERT INTO notifications (student_id, channel, template, payload, success, sent_at) VALUES (?,?,?,?,?,?)",
              (sid, "email", template, "{}", success, utc_str(at)))
    conn.commit(); conn.close()


def main():
    print("🎯 生徒画面レビュー反映 (2026-09-09) 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    now = datetime.datetime.now(datetime.timezone.utc)
    today_jst = datetime.datetime.now(JST).date()
    monday_jst = today_jst - datetime.timedelta(days=today_jst.weekday())
    monday_utc = datetime.datetime.combine(monday_jst, datetime.time(0, 0), tzinfo=JST).astimezone(datetime.timezone.utc)

    # ---------------------------------------------------------------- 1) 活動サマリ / できた！
    print("1) 活動サマリ API")
    S1 = mk(mod, "Student S1", "s1@example.org", line_user_id="Uxxxxxxxx")
    S2 = mk(mod, "Student S2", "s2@example.org")
    S3 = mk(mod, "Student S3", "s3@example.org")
    add_attempt(mod, S1, now - datetime.timedelta(minutes=1))
    add_attempt(mod, S1, now - datetime.timedelta(minutes=2), correct=0)
    add_attempt(mod, S1, now - datetime.timedelta(hours=24))
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO study_logs (student_id, studied_date, subject, minutes) VALUES (?,?,?,?)",
              (S1, (today_jst - datetime.timedelta(days=3)).isoformat(), "英語", 30))
    conn.commit(); conn.close()
    add_attempt(mod, S2, now - datetime.timedelta(days=10))

    h1 = {"Authorization": "Bearer " + student_token(mod, S1)}
    h2 = {"Authorization": "Bearer " + student_token(mod, S2)}
    h3 = {"Authorization": "Bearer " + student_token(mod, S3)}
    r = client.get("/api/student/activity-summary", headers=h1); j = r.json()
    check("S1: 今日+昨日で連続 2 日 (3 日前の学習記録は繋がらない)", r.status_code == 200 and j["streak_days"] == 2, j)
    check("S1: 今日の演習 2 問・正解 1", j["today_problems"] == 2 and j["today_correct"] == 1 and j["active_today"] is True, j)
    check("S1: 直近 14 日配列は 14 要素で末尾が 1", len(j["recent_days"]) == 14 and j["recent_days"][-1] == 1, j["recent_days"])
    r = client.get("/api/student/activity-summary", headers=h2); j2 = r.json()
    check("S2: 10 日前が最後 → streak 0 / days_since 10 / ever_active", j2["streak_days"] == 0 and j2["days_since_activity"] == 10 and j2["ever_active"] is True, j2)
    r = client.get("/api/student/activity-summary", headers=h3); j3 = r.json()
    check("S3: 一度も無し → days_since None / ever_active False", j3["days_since_activity"] is None and j3["ever_active"] is False, j3)
    r = client.get("/api/student/activity-summary")
    check("未認証は 401", r.status_code == 401, r.status_code)

    print("2) できた！ の記録")
    r = client.post("/api/student/coach-done", json={"title": "ドリル「仮定法」をやろう"}, headers=h2); j = r.json()
    check("初回は recorded=True・streak 1・coach_done_today", r.status_code == 200 and j["recorded"] is True and j["streak_days"] == 1 and j["coach_done_today"] is True, j)
    r = client.post("/api/student/coach-done", json={}, headers=h2); j = r.json()
    check("同日 2 回目は recorded=False (冪等)", j["recorded"] is False and j["streak_days"] == 1, j)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM events WHERE name='coach_done' AND session_id=?", (str(S2),)); n = c.fetchone()["n"]; conn.close()
    check("events に coach_done が 1 行だけ", n == 1, n)

    print("3) /api/auth/me の line_linked")
    r = client.get("/api/auth/me", headers=h1); st = r.json().get("student", {})
    check("LINE 連携済みは line_linked=True", r.status_code == 200 and st.get("line_linked") is True, st)
    check("LINE の userId は返さない", "line_user_id" not in st, list(st.keys()))
    r = client.get("/api/auth/me", headers=h2); st = r.json().get("student", {})
    check("未連携は line_linked=False", st.get("line_linked") is False, st)

    # ---------------------------------------------------------------- 4) 演習ゼロ週の軽量レポート
    print("4) 週次レポート: 演習ゼロ週の軽量メール")
    Z1 = mk(mod, "Student Z1", "z1-parent@example.org", student_email="z1-child@example.org", verified=1, parent_email="z1-parent@example.org")
    Z2 = mk(mod, "Student Z2", "z2@example.org")          # 60 日前が最後 = 休眠
    Z3 = mk(mod, "Student Z3", "z3@example.org")          # 一度も解いていない
    Z4 = mk(mod, "Student Z4", "z4@example.org")          # 既に 2 週連続で送付済み (実運用どおり 7 日・14 日前)
    Z6 = mk(mod, "Student Z6", "z6-parent@example.org", student_email="z6-child@example.org", verified=1, parent_email="z6-parent@example.org")  # 水曜に一声が届いている
    add_attempt(mod, Z1, now - datetime.timedelta(days=5))
    add_attempt(mod, Z2, now - datetime.timedelta(days=60))
    add_attempt(mod, Z4, now - datetime.timedelta(days=5))
    add_attempt(mod, Z6, now - datetime.timedelta(days=6))
    add_notification(mod, Z4, "weekly_report_zero_week", 7)
    add_notification(mod, Z4, "weekly_report_zero_week_parent", 7)
    add_notification(mod, Z4, "weekly_report_zero_week", 14)
    add_notification(mod, Z6, "midweek_nudge", 3)
    Z7 = mk(mod, "Student Z7", "z7@example.org")          # 1 週だけ送付済み (7 日前) → 2 週目は送る
    add_attempt(mod, Z7, now - datetime.timedelta(days=5))
    add_notification(mod, Z7, "weekly_report_zero_week", 7)
    zero_stats = {"hours": 0, "questions": 0, "problems_done": 0, "accuracy": 0, "weakest_subject": None, "subject_stats": {}, "days": 7}
    mod._compute_weekly_stats = lambda sid, days=7, week_aligned=True: dict(zero_stats)
    sent = []
    mod._send_zero_week_report_email = lambda to, name, zw, is_parent: (sent.append((to, is_parent, zw["days_since"])) or {"sent": True})
    d = mod._zero_week_report_decision(Z1); check("Z1 (5 日前) は送る判定", bool(d) and d["days_since"] == 5, d)
    check("Z2 (60 日前) は送らない", mod._zero_week_report_decision(Z2) is None)
    check("Z3 (未演習) は送らない", mod._zero_week_report_decision(Z3) is None)
    check("Z4 (2 週連続で送付済み) は送らない", mod._zero_week_report_decision(Z4) is None)
    d7 = mod._zero_week_report_decision(Z7); check("Z7 (1 週だけ送付済み) は 2 週目も送る", bool(d7), d7)
    check("Z1 は直近ログイン無し → recent_login False", d.get("recent_login") is False, d)
    r = client.post("/api/cron/weekly-reports?dry_run=true", headers={"X-Cron-Secret": CRON}); j = r.json()
    pz = {p["student_id"]: p for p in (j.get("previews") or []) if p.get("zero_week")}
    check("dry_run: Z1 が zero_week として preview に載り、子と親の両方が宛先", Z1 in pz and pz[Z1]["student_copy_to"] == "z1-child@example.org" and pz[Z1]["parent_copy_to"] == "z1-parent@example.org", pz.get(Z1))
    check("dry_run: Z2/Z3/Z4 は載らない・送信ゼロ", not ({Z2, Z3, Z4} & set(pz)) and not sent, (sorted(pz), sent))
    r = client.post("/api/cron/weekly-reports", headers={"X-Cron-Secret": CRON}); j = r.json()
    to_z1 = sorted((t, p) for (t, p, _) in sent if t.startswith("z1-"))
    check("本番: Z1 の子 (生徒コピー) と親 (保護者コピー) に 1 通ずつ", to_z1 == [("z1-child@example.org", False), ("z1-parent@example.org", True)], sent)
    check("本番: Z2/Z3/Z4 には送らない", not [t for (t, _, _) in sent if t.startswith(("z2", "z3", "z4"))], sent)
    check("本番: 水曜に一声が届いた Z6 は保護者宛だけ (生徒本人には重ねない)", sorted((t, p) for (t, p, _) in sent if t.startswith("z6-")) == [("z6-parent@example.org", True)], sent)
    check("本番: Z7 (2 週目) には送る", any(t == "z7@example.org" for (t, _, _) in sent), sent)
    check("結果に zero_week 通数が載る", j.get("zero_week", 0) >= 2 and j.get("zero_week_queued", 0) >= 3, j)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT template, success FROM notifications WHERE student_id=? AND template LIKE 'weekly_report_zero_week%' ORDER BY template", (Z1,))
    rows = [(x["template"], x["success"]) for x in c.fetchall()]; conn.close()
    check("notifications に生徒用/保護者用のテンプレートで記録", rows == [("weekly_report_zero_week", 1), ("weekly_report_zero_week_parent", 1)], rows)
    sent.clear()
    r = client.post("/api/cron/weekly-reports", headers={"X-Cron-Secret": CRON})
    check("同じ週にもう一度回しても再送しない (6 日 dedup)", not sent, sent)
    mod.ZERO_WEEK_REPORT_ENABLED = False
    add_notification(mod, Z1, "weekly_report_zero_week", 7); sent.clear()
    Z5 = mk(mod, "Student Z5", "z5@example.org"); add_attempt(mod, Z5, now - datetime.timedelta(days=4))
    r = client.post("/api/cron/weekly-reports", headers={"X-Cron-Secret": CRON}); j = r.json()
    check("ZERO_WEEK_REPORT_ENABLED=0 なら従来どおり完全スキップ", not sent and j.get("zero_week") == 0, (sent, j))
    mod.ZERO_WEEK_REPORT_ENABLED = True
    # 枠: ZERO_WEEK_REPORT_CAP=1 なら 1 通で止まり、残りは capped に数える (Z5 と Z8 の 2 家庭が待っている状態)
    Z8 = mk(mod, "Student Z8", "z8@example.org"); add_attempt(mod, Z8, now - datetime.timedelta(days=4))
    mod.ZERO_WEEK_REPORT_CAP = 1; sent.clear()
    r = client.post("/api/cron/weekly-reports", headers={"X-Cron-Secret": CRON}); j = r.json()
    check("ZERO_WEEK_REPORT_CAP で通数が止まり capped に数える", len(sent) == 1 and j.get("zero_week") == 1 and j.get("capped", 0) >= 1, (sent, j))
    mod.ZERO_WEEK_REPORT_CAP = 24
    src_v = mod._weekly_report_verdict([{"name": "weekly_reports_run", "stale": False,
                                          "props": {"sent_email": 3, "sent_line": 0, "zero_week": 3, "skipped": 10, "zero_week_queued": 2}}])
    check("verdict はゼロ週メールを『送信』に数えない (通常 0 件なら断絶疑い)", "送信 0 件" in src_v, src_v)

    # ---------------------------------------------------------------- 5) 週半ばの一声
    print("5) 週半ばの一声 cron")
    M1 = mk(mod, "Student M1", "m1@example.org", line_user_id="Um1")                                   # LINE 連携済み
    M2 = mk(mod, "Student M2", "m2-parent@example.org", student_email="m2-child@example.org", verified=1)  # 子メール確認済み
    M3 = mk(mod, "Student M3", "m3@example.org")                                                       # 今週すでに演習
    M4 = mk(mod, "Student M4", "m4@example.org")                                                       # 40 日前 = 休眠
    add_attempt(mod, M1, monday_utc - datetime.timedelta(days=2))
    add_attempt(mod, M2, monday_utc - datetime.timedelta(days=2))
    add_attempt(mod, M3, now - datetime.timedelta(minutes=1))
    add_attempt(mod, M4, now - datetime.timedelta(days=40))
    line_calls = []; mail_calls = []

    def _fake_line_push(sid, tmpl, params=None):
        # 本物の _do_line_push は成功/失敗を notifications (channel='line') に自分で記録する。cron 側はそれに依存して
        # LINE 成功時に二重記録しないので、偽物も同じように記録する
        line_calls.append((sid, tmpl, (params or {}).get("url")))
        _c = mod.db(); _cur = _c.cursor()
        _cur.execute("INSERT INTO notifications (student_id, channel, template, payload, success) VALUES (?, 'line', ?, '{}', 1)", (sid, tmpl))
        _c.commit(); _c.close()
        return {"ok": True}
    mod._do_line_push = _fake_line_push
    mod._send_midweek_nudge_email = lambda to, name: (mail_calls.append((to, name)) or {"sent": True})
    check("LINE テンプレート midweek_nudge が登録されている", "midweek_nudge" in mod.LINE_TEMPLATES and "text" in mod.LINE_TEMPLATES["midweek_nudge"]({"name": "A", "url": "u"}))
    r = client.post("/api/cron/midweek-nudge?dry_run=true", headers={"X-Cron-Secret": CRON}); j = r.json()
    prev = {p["student_id"]: p for p in (j.get("preview") or [])}
    check("dry_run: M1 (LINE) と M2 (子メール) が対象・M3/M4 は外", M1 in prev and M2 in prev and M3 not in prev and M4 not in prev, prev)
    check("dry_run: M2 の宛先は確認済みの子メール", prev.get(M2, {}).get("channel") == "email" and prev.get(M2, {}).get("email_to") == "m2-child@example.org", prev.get(M2))
    check("dry_run: 送信していない", not line_calls and not mail_calls)
    r = client.post("/api/cron/midweek-nudge", headers={"X-Cron-Secret": CRON}); j = r.json()
    check("本番: M1 は LINE で 1 通 (テンプレ midweek_nudge・?today=1 リンク)", [(s, t) for (s, t, _) in line_calls] == [(M1, "midweek_nudge")] and line_calls[0][2].endswith("mypage.html?today=1"), line_calls)
    check("本番: M2 は子メールに 1 通・M3/M4 には送らない", ("m2-child@example.org", "Student M2") in mail_calls and not [t for (t, _) in mail_calls if t.startswith(("m3", "m4"))], mail_calls)
    check("結果カウント", j["sent_line"] >= 1 and j["sent_email"] >= 1 and j["failed"] == 0, j)
    line_calls.clear(); mail_calls.clear()
    r = client.post("/api/cron/midweek-nudge", headers={"X-Cron-Secret": CRON}); j = r.json()
    check("同じ週にもう一度回しても再送しない (6 日 dedup)", not line_calls and not mail_calls and j["matched"] == 0, (line_calls, mail_calls, j))
    r = client.post("/api/cron/midweek-nudge", headers={"X-Cron-Secret": "wrong"})
    check("秘密が違えば 401", r.status_code == 401, r.status_code)
    mod.MIDWEEK_NUDGE_ENABLED = False
    conn = mod.db(); c = conn.cursor(); c.execute("DELETE FROM notifications WHERE template='midweek_nudge'"); conn.commit(); conn.close()
    r = client.post("/api/cron/midweek-nudge", headers={"X-Cron-Secret": CRON}); j = r.json()
    check("MIDWEEK_NUDGE_ENABLED=0 なら無送信 (enabled=False)", j.get("enabled") is False and not line_calls and not mail_calls, j)
    mod.MIDWEEK_NUDGE_ENABLED = True
    src = open(MAIN_PY, encoding="utf-8").read()
    check("水曜 18 時のスケジューラが起動時に登録される", "asyncio.create_task(_midweek_nudge_scheduler())" in src and '"midweek_nudge_run": 8' in src)

    # ---------------------------------------------------------------- 6) フロントのソース検査
    print("6) mypage.html / mypage.js ソース検査")
    html = open(os.path.join(REPO, "mypage.html"), encoding="utf-8").read()
    js = open(os.path.join(REPO, "mypage.js"), encoding="utf-8").read()
    check("initWidgets の待ちに上限 (無限ポーリングの打ち切り)", "_ajWidgetWait < 50" in html)
    check("slApiFetch にタイムアウト (AbortController)", "AbortController" in js and "timeoutMs" in js)
    check("コーチカードがサーバの活動サマリを使う (おかえり・できた！の記録)", "/api/student/activity-summary" in js and "/api/student/coach-done" in js and "おかえり" in js)
    check("要対応チップ (AJ_TODO) と受け皿 #cnmTodo", "window.AJ_TODO" in js and 'id="cnmTodo"' in html)
    check("演習の入口が 1 枚 (practiceChooser) に統合・NEW バッジ撤去", 'id="practiceChooser"' in html and "action-badge-new" not in html)
    check("LINE 連携 CTA は line_linked===false で表示", "line_linked === false" in html)
    check("合格可能性スコアは失敗時に消えず再試行を案内", "showFetchError(" in html)
    check("mypage.js / mypage.css の ?v= を 2026-09-09 に更新", "mypage.js?v=20260909" in html and "mypage.css?v=20260909" in html)
    check("learning-brain.js の ?v= が最終変更 (2026-07-14) より新しい", "learning-brain.js?v=20260909" in html)
    import re as _re
    visible = _re.sub(r"<!--.*?-->", "", html, flags=_re.S)  # HTML コメントは生徒に見えないので除外
    check("専門語 (SRS / Leitner / 3 mode) を生徒向けの言葉に", "(SRS)" not in visible and "Leitner Box" not in visible and "3 mode" not in visible)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
