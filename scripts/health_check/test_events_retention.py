#!/usr/bin/env python3
"""🧹🗄️ events の保持期限 / /api/track のレート制限 / R2 バックアップの省メモリ dump (2026-09-07) の回帰テスト。
in-process・一時 SQLite・本番に触れない。

システム点検で確定した点:
  - DELETE FROM events が 1 箇所も無く、監視 (5分ごと) と計測が無限に積み上がっていた → 名前を挙げた計測/監視
    イベントだけを 90日/180日で消す。監査用 (*_run, admin_*, 決済系 …) は名前を挙げていないので絶対に消えない。
  - /api/track は Origin 一致だけで無制限に書けた → IP ごと 120 回/分。
  - バックアップ dump は全テーブルを RAM に載せていた → 一時ファイルへ流し (Postgres は server-side cursor)、
    upload_file でストリーミング PUT。bytes 互換ラッパも残す。
"""
import datetime
import gzip
import importlib.util
import json
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
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="events_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_events", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def insert_event(mod, name, days_ago, props=None):
    conn = mod.db(); c = conn.cursor()
    ts = (datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO events (name, props, session_id, created_at) VALUES (?, ?, ?, ?)",
              (name, json.dumps(props or {}), "t", ts))
    conn.commit(); conn.close()


def count(mod, name):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM events WHERE name = ?", (name,))
    n = c.fetchone()["n"]; conn.close(); return n


def main():
    print("🧹🗄️ イベント掃除・計測制限・バックアップ dump 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    src = open(MAIN_PY, encoding="utf-8").read()

    print("1) events の保持期限")
    insert_event(mod, "synthetic_checkout_test", 100); insert_event(mod, "synthetic_checkout_test", 10)
    insert_event(mod, "js_error", 100); insert_event(mod, "js_error", 89)
    insert_event(mod, "page_view", 200); insert_event(mod, "page_view", 100)
    insert_event(mod, "lp_view", 181)
    insert_event(mod, "weekly_reports_run", 400, {"sent": 3})          # 監査: 消えない
    insert_event(mod, "admin_student_deleted", 400)                   # 監査: 消えない
    insert_event(mod, "textbook_request_missing", 400)                # 業務: 消えない
    insert_event(mod, "mock_exam_submit", 400)                        # 挙げていない名前: 消えない
    res = mod._run_events_retention()
    check("90日超の監視/JSエラーが消える (2件)", res.get("deleted_90d") == 2, res)
    check("180日超の計測が消える (page_view 200d + lp_view 181d = 2件)", res.get("deleted_180d") == 2, res)
    check("90日以内の監視/JSエラーは残る", count(mod, "synthetic_checkout_test") == 1 and count(mod, "js_error") == 1)
    check("180日以内の page_view は残る", count(mod, "page_view") == 1)
    for nm in ("weekly_reports_run", "admin_student_deleted", "textbook_request_missing", "mock_exam_submit"):
        check(f"{nm} は 400 日前でも消えない", count(mod, nm) == 1)
    res2 = mod._run_events_retention()
    check("再実行で追加削除なし (冪等)", res2.get("deleted_90d") == 0 and res2.get("deleted_180d") == 0, res2)
    check("監査用の名前は保持リストに無い", not any(n.endswith("_run") or n.startswith("admin_") or n.startswith("r2_backup") or n == "auto_rollback"
                                              for names in mod._EVENTS_RETENTION.values() for n in names))
    check("scheduler に events_retention_run の配線", "events_retention_run" in mod._SCHEDULER_MAX_AGE_DAYS and "await asyncio.to_thread(_run_events_retention)" in src)

    print("2) /api/track のレート制限")
    origin = {"Origin": "https://trillion-ai-juku.com"}
    r = client.post("/api/track", json={"name": "page_view", "props": {"p": "/"}, "session_id": "s1"}, headers=origin)
    check("通常は 200", r.status_code == 200, f"{r.status_code} {r.text[:120]}")
    mod._RATE_LIMIT_STORE[("testclient", "track")] = [time.time()] * 120
    r = client.post("/api/track", json={"name": "page_view", "props": {}, "session_id": "s1"}, headers=origin)
    check("上限到達後は 429", r.status_code == 429, f"{r.status_code}")
    mod._RATE_LIMIT_STORE.clear()

    print("3) バックアップ dump (一時ファイル・ストリーミング)")
    conn = mod.db(); c = conn.cursor()
    far = (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat()
    for i in range(3):
        c.execute("INSERT INTO students (name, email, status, plan, trial_end) VALUES (?, ?, ?, ?, ?)",
                  (f"S{i}", f"s{i}@example.org", "paid", "premium", far))
    conn.commit()
    check("_Cursor.fetchmany が使える", len(c.execute("SELECT id FROM students").fetchmany(2)) == 2)
    conn.close()
    path, rows, tables = mod._dump_db_to_jsonl_gz_file()
    try:
        check("一時ファイルが作られる", os.path.exists(path) and path.endswith(".jsonl.gz"), path)
        with gzip.open(path, "rb") as f:
            body = f.read().decode("utf-8")
        check("students テーブルが含まれる", "-- TABLE: students" in body and '"_table": "students"' in body)
        check("行数が返る", rows >= 3 and tables >= 5, (rows, tables))
        check("末尾に TOTAL 行", "-- TOTAL:" in body)
    finally:
        try: os.remove(path)
        except Exception: pass
    data = mod._dump_db_to_jsonl_gz()
    check("bytes 互換ラッパは gzip を返し一時ファイルを残さない", data[:2] == b"\x1f\x8b" and not os.path.exists(path))
    check("_run_r2_backup は一時ファイル + upload_file を使う", "_dump_db_to_jsonl_gz_file()" in src[src.index("def _run_r2_backup"):][:2500]
          and "def _r2_upload_backup_file" in src and "cli.upload_file(" in src)
    check("Postgres では名前付きカーソルで流す", 'cursor(name="r2dump"' in src)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
