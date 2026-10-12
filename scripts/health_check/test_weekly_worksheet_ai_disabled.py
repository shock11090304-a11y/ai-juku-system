#!/usr/bin/env python3
"""📅 週次弱点プリントを「塾生アプリのみ枠 (AIなし)」の生徒に配らない回帰テスト (2026-10-12)。

背景: AIなし枠 (students.ai_disabled=1) の生徒から「LINE に『今週の弱点プリントが届きました』と来たが
  マイページに見当たらない。開くと一瞬『高校受験モード』が見えてすぐ塾生アプリ (予定・宿題・動画・メッセージ) に
  戻る」と問い合わせ。週次プリント (_run_weekly_worksheet_generation) の抽出 SQL が ai_disabled を見ておらず、
  宿題ドリルで弱点が溜まった AIなし枠の生徒にも LINE/メールを送っていた。リンク先の mypage はその生徒を
  class.html へ送り返し (mypage.html の feed.ai_home_available)、/api/student/worksheet/this-week も AI 遮断で 403。

固定する性質 (実際の関数を一時 SQLite で回す・外部通信なし):
  1. 通常の生徒 (ai_disabled=0) にはプリントを作り、LINE を送る
  2. AIなし枠 (ai_disabled=1) にはプリントを作らず、LINE もメールも送らない
  3. AIなし枠でも期限付き AI 体験中 (ai_trial_until が未来) なら作る (_ai_blocked_now と同じ)
  4. AI 体験の期限が過ぎた AIなし枠には作らない
  5. AIなし枠の生徒は this-week API が 403 (= プリントを作っても見る場所が無い。前提の確認)

実行:
    python3 scripts/health_check/test_weekly_worksheet_ai_disabled.py
    # exit 0 = PASS / 1 = FAIL
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="ws_ai_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_ws_ai", MAIN_PY)
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


def main():
    mod = load_main()
    now = datetime.datetime.now(datetime.timezone.utc)
    te = (now + datetime.timedelta(days=3650)).isoformat()
    future = mod._utc_naive_iso(now + datetime.timedelta(days=5))
    past = mod._utc_naive_iso(now - datetime.timedelta(days=1))

    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO exam_questions (exam_id, part_key, question_data) VALUES ('daigaku', 'r_long', ?)",
              (json.dumps({"questions": [{"q": "x"}]}),))

    def make(name, email, ai_disabled, ai_trial_until=None):
        c.execute(
            "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, ai_trial_until, line_user_id) "
            "VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', '高校3年', '国公立大学', ?, ?, ?)",
            (name, email, te, ai_disabled, ai_trial_until, "U-" + email.split("@")[0]),
        )
        c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
        sid = c.fetchone()["id"]
        c.execute("INSERT INTO student_weakness (student_id, subject, topic, question_count, avg_confidence_score, last_seen_at) "
                  "VALUES (?, 'english', NULL, 5, 0.5, ?)", (sid, now.isoformat()))
        return sid

    sid_ai = make("AIあり A", "ws-a@example.org", 0)
    sid_noai = make("AIなし B", "ws-b@example.org", 1)
    sid_trial = make("AIなし 体験中 C", "ws-c@example.org", 1, future)
    sid_expired = make("AIなし 体験切れ D", "ws-d@example.org", 1, past)
    conn.commit(); conn.close()
    mod._AI_DISABLED_CACHE.clear()

    mails, lines = [], []
    orig_mail, orig_line = mod._send_monitor_email, mod._do_line_push
    mod._send_monitor_email = lambda subj, body, to_email=None: (mails.append(to_email) or {"sent": True})
    mod._do_line_push = lambda sid, tmpl, params: (lines.append((sid, tmpl)) or {"ok": True})
    try:
        res = mod._run_weekly_worksheet_generation()
    finally:
        mod._send_monitor_email, mod._do_line_push = orig_mail, orig_line

    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT student_id FROM worksheet_archives")
    made = {r["student_id"] for r in c.fetchall()}
    conn.close()
    line_sids = {s for s, t in lines if t == "weekly_worksheet"}

    print("[1] 週次弱点プリントの対象")
    check("通常の生徒 (AIあり) には作る・LINE を送る", sid_ai in made and sid_ai in line_sids, (made, lines, res))
    check("AIなし枠には作らない", sid_noai not in made, made)
    check("AIなし枠には LINE もメールも送らない", sid_noai not in line_sids and "ws-b@example.org" not in mails, (lines, mails))
    check("AIなし枠でも AI 体験中なら作る (_ai_blocked_now と同じ)", sid_trial in made and sid_trial in line_sids, (made, lines))
    check("AI 体験の期限が過ぎた AIなし枠には作らない", sid_expired not in made and sid_expired not in line_sids, (made, lines))
    check("述語が一致: 作った生徒 = _ai_blocked_now が False の生徒",
          made == {s for s, dis, tu in ((sid_ai, 0, None), (sid_noai, 1, None), (sid_trial, 1, future), (sid_expired, 1, past))
                   if not mod._ai_blocked_now(dis, tu)}, made)

    print("[2] 前提: AIなし枠は this-week を読めない (作っても見る場所が無い)")
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    r = client.get("/api/student/worksheet/this-week", headers={"Authorization": "Bearer " + student_token(mod, sid_noai)})
    check("AIなし枠の this-week は 403", r.status_code == 403, (r.status_code, r.text[:200]))
    r = client.get("/api/student/worksheet/this-week", headers={"Authorization": "Bearer " + student_token(mod, sid_ai)})
    check("通常の生徒の this-week は 200 で今週分が返る", r.status_code == 200 and (r.json() or {}).get("worksheet"),
          (r.status_code, r.text[:200]))

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ PASS")


if __name__ == "__main__":
    main()
