#!/usr/bin/env python3
"""📒 週次レポートの「🔥 学習時間」に学習記録 (study_logs.minutes) を入れる (2026-11-24 塾長「直して」) の回帰テスト。

それまでの学習時間は「アプリで解いた時間」(question_attempts.elapsed_ms) だけだった。宿題ドリルの提出は elapsed_ms を持たないので、
毎日学習記録を付けていた生徒にも「学習時間: 0.0時間」が届いた。

固定する性質 (一時 SQLite・架空の生徒):
  [1] 学習記録だけの週: 合計の分数が学習時間になる (540 分 → 9.0 時間)・self_reported_minutes に分数
  [2] 週の境目は JST の日付: 窓の前の日曜・窓の後の月曜の記録は数えない・ほかの生徒の記録も数えない
  [3] 二重に数えない: アプリで解いた時間と学習記録は多いほうを採る (足さない)
  [4] 学習記録が無ければ今までどおり (アプリで解いた時間)・app_hours はアプリで解いた時間
実行:
    python3 scripts/health_check/test_weekly_stats_study_logs.py
"""
import datetime
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []
UTC = datetime.timezone.utc
JST = datetime.timezone(datetime.timedelta(hours=9))


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="wr_studylogs_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと本番 Postgres に書き込む
        "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "", "ANTHROPIC_API_KEY": "", "LINE_CHANNEL_ACCESS_TOKEN": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_wr_studylogs", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def ex(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor(); c.execute(sql, params); conn.commit(); conn.close()


def main():
    mod = load_main()
    # 窓を固定: 水曜 (月〜土) の実行 = 先週月曜 0:00 JST 〜 今週月曜 0:00 JST
    since, until = mod._weekly_report_window(datetime.datetime(2026, 11, 25, 7, 0, tzinfo=JST))
    mod._weekly_report_window = lambda now_jst=None: (since, until)
    mon = since.astimezone(JST).date()  # 2026-11-16
    A, B, C = 9001, 9002, 9003

    def log(sid, d, m):
        ex(mod, "INSERT INTO study_logs (student_id, studied_date, subject, minutes) VALUES (?, ?, '英語', ?)",
           (sid, d.isoformat(), m))

    def attempt(sid, dt, ems):
        ex(mod, "INSERT INTO question_attempts (student_id, source, subject, is_correct, elapsed_ms, created_at) "
                "VALUES (?, 'practice', 'english', 1, ?, ?)",
           (sid, ems, dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")))

    print("[1] 学習記録だけの週")
    for i, m in enumerate([180, 60, 30, 60, 90, 60, 60]):
        log(A, mon + datetime.timedelta(days=i), m)
    print("[2] 境目とほかの生徒")
    log(A, mon - datetime.timedelta(days=1), 500)   # 前の週の日曜
    log(A, mon + datetime.timedelta(days=7), 500)   # 次の週の月曜
    log(B, mon + datetime.timedelta(days=2), 999)
    st = mod._compute_weekly_stats(A)
    check("540 分 → 9.0 時間", st["hours"] == 9.0, st)
    check("self_reported_minutes = 540", st.get("self_reported_minutes") == 540, st)
    check("アプリで解いた時間は 0", st.get("app_hours") == 0.0, st)

    print("[3] 二重に数えない (多いほう)")
    # C: アプリ 2 時間 (40 分 × 3) と学習記録 60 分 → 2.0 時間 (足して 3.0 にしない)
    t0 = since + datetime.timedelta(days=2, hours=3)
    for k in range(3):
        attempt(C, t0 + datetime.timedelta(minutes=k), 40 * 60 * 1000)
    log(C, mon + datetime.timedelta(days=2), 60)
    st = mod._compute_weekly_stats(C)
    check("アプリ 2.0 > 記録 1.0 → 2.0", st["hours"] == 2.0 and st["app_hours"] == 2.0, st)
    log(C, mon + datetime.timedelta(days=3), 240)
    st = mod._compute_weekly_stats(C)
    check("記録 5.0 > アプリ 2.0 → 5.0", st["hours"] == 5.0, st)

    print("[4] 学習記録が無い生徒は今までどおり")
    D = 9004
    attempt(D, since + datetime.timedelta(days=1), 30 * 60 * 1000)
    st = mod._compute_weekly_stats(D)
    check("アプリ 0.5 時間のまま", st["hours"] == 0.5 and st["self_reported_minutes"] == 0, st)
    st = mod._compute_weekly_stats(9999)
    check("何も無い生徒は 0", st["hours"] == 0.0, st)

    print("PASS" if not FAILURES else f"FAIL: {FAILURES}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
