#!/usr/bin/env python3
"""📉 学習記録の連続未記録アラート (2026-09-07) の回帰テスト (in-process・一時 SQLite・メールは偽物)。

システム点検の残件 1: 難関コース生は既存の日次アラートから除外され、学習記録が止まっても誰にも通知されなかった。
  - 学習記録ダッシュボードと同じ母集団で「最終記録日から何日」を数える
  - 閾値 (既定 3 日) 以上の生徒だけを塾長にメール。該当ゼロなら送らない。dry_run は送らない
  - ランキング API に zero_streak_days / never_logged が載る
  - 毎朝 10:00 の体験管理バッチに登録されている (ソース検査)
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


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="streak_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid", "STUDY_LOG_ZERO_STREAK_DAYS": "3",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_streak", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod):
    exp = int(time.time()) + 3600
    payload = mod._admin_token_payload(str(exp))
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def mk(mod, name, email, last_log_days_ago=None, course="kokuritsu_nankan"):
    conn = mod.db(); c = conn.cursor()
    far = (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat()
    c.execute("INSERT INTO students (name, email, status, plan, trial_end, course, grade) VALUES (?,?,?,?,?,?,?)",
              (name, email, "paid", "premium", far, course, "高校3年"))
    conn.commit(); c.execute("SELECT id FROM students WHERE email = ?", (email,)); sid = c.fetchone()["id"]
    if last_log_days_ago is not None:
        d = (mod._today_jst() - datetime.timedelta(days=last_log_days_ago)).isoformat()
        c.execute("INSERT INTO study_logs (student_id, studied_date, subject, minutes) VALUES (?,?,?,?)", (sid, d, "英語", 30))
        conn.commit()
    conn.close()
    return sid


def main():
    print("📉 連続未記録アラート 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    A = mk(mod, "Student A", "a@example.org", last_log_days_ago=0)     # 今日記録
    B = mk(mod, "Student B", "b@example.org", last_log_days_ago=5)     # 5 日止まっている
    C = mk(mod, "Student C", "c@example.org", last_log_days_ago=None)  # 一度も無い
    E = mk(mod, "Student E", "e@example.org", last_log_days_ago=2)     # 2 日 (閾値未満)
    sent = []
    mod._send_monitor_email = lambda subject, body_html, to_email=None: (sent.append((subject, body_html)) or {"sent": True})

    print("1) 集計")
    conn = mod.db(); rows = {r["id"]: r for r in mod._study_log_zero_streaks(conn.cursor())}; conn.close()
    check("A は 0 日", rows[A]["streak"] == 0, rows[A])
    check("B は 5 日", rows[B]["streak"] == 5, rows[B])
    check("E は 2 日", rows[E]["streak"] == 2, rows[E])
    check("C は never", rows[C]["never"] is True and rows[C]["streak"] is None, rows[C])

    print("2) アラート")
    r = mod._run_zero_streak_alert(dry_run=True)
    check("dry_run: 該当 1 名 (B)・送信しない", r["hit"] == 1 and r["never"] == 1 and r["sent"] is False and not sent, r)
    r = mod._run_zero_streak_alert()
    check("本番: メール 1 通", r["sent"] is True and len(sent) == 1, r)
    subj, body = sent[0] if sent else ("", "")
    check("件名に人数", "1 名" in subj, subj)
    check("本文に B の名前と 5 日、E は入らない", "Student B" in body and "5 日" in body and "Student E" not in body, body[:300])
    check("本文に「一度も記録なし 1 名」", "一度も記録していない対象生徒: 1 名" in body, body[:300])
    # 該当ゼロなら送らない
    conn = mod.db(); c = conn.cursor(); c.execute("INSERT INTO study_logs (student_id, studied_date, subject, minutes) VALUES (?,?,?,?)", (B, mod._today_jst().isoformat(), "英語", 10)); conn.commit(); conn.close()
    sent.clear()
    r = mod._run_zero_streak_alert()
    check("該当ゼロなら送らない", r["hit"] == 0 and r["sent"] is False and not sent, r)

    print("3) API")
    r = client.post("/api/admin/study-logs/zero-streak-alert/run", json={"dry_run": True}, headers=adm)
    check("即時実行 API (dry_run) が 200", r.status_code == 200 and r.json().get("ok"), r.text[:150])
    r = client.get("/api/admin/study-logs/students?days=7", headers=adm).json()
    by = {s["student_id"]: s for s in r.get("students", [])}
    check("ランキング API に zero_streak_days / never_logged", by[C]["never_logged"] is True and by[E]["zero_streak_days"] == 2 and by[A]["zero_streak_days"] == 0, by)
    check("閾値も返す", r.get("zero_streak_threshold") == 3, r.get("zero_streak_threshold"))
    src = open(MAIN_PY, encoding="utf-8").read()
    check("毎朝 10:00 の体験管理バッチに登録", '("study-log-zero-streak", lambda: _run_zero_streak_alert())' in src)
    js = open(os.path.join(REPO, "ceo.js"), encoding="utf-8").read()
    check("ceo.js のランキングが氏名付きの連続未記録リストを出す", "zero_streak_days" in js and "一度も記録なし" in js)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
