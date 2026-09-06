#!/usr/bin/env python3
"""🩺 定期実行の失敗検知と DB バックアップの可視化 (2026-09-07) の回帰テスト (in-process・一時 SQLite)。

システム点検で「バッチが失敗しても『今日は実行済み』扱いで無音、バックアップは誰も見ていない」と確定した点を直した。

  1. _SCHEDULER_MAX_AGE_DAYS に r2_backup_success / admission_recompute_run がある (停止検知の対象)
  2. /api/health に r2_backup_configured が出る (未設定なら点検スクリプトが FAIL にする)
  3. 最後の実行が props.error で終わったスケジューラは failed=True になり、_failed_schedulers が拾い、
     監視の alert (scheduler_failed / critical) に乗る
  4. 「実行履歴なし」は停止とも失敗とも扱わない (未有効化との誤報防止・従来どおり)
  5. R2 バックアップの失敗は塾長にメールする配線がある (ソース検査)
"""
import datetime
import importlib.util
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="sched_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid", "R2_ACCOUNT_ID": "",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_sched", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def insert_event(mod, name, props, days_ago=0):
    conn = mod.db()
    c = conn.cursor()
    ts = (datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO events (name, props, session_id, created_at) VALUES (?, ?, ?, ?)",
              (name, json.dumps(props, ensure_ascii=False), "test", ts))
    conn.commit()
    conn.close()


def main():
    print("🩺 定期実行の失敗検知 / バックアップ可視化 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    src = open(MAIN_PY, encoding="utf-8").read()

    print("1) 停止検知の対象")
    for k in ("r2_backup_success", "admission_recompute_run"):
        check(f"_SCHEDULER_MAX_AGE_DAYS に {k}", k in mod._SCHEDULER_MAX_AGE_DAYS, list(mod._SCHEDULER_MAX_AGE_DAYS))

    print("2) /api/health の r2_backup_configured")
    h = client.get("/api/health").json()
    check("フィールドがあり、R2 未設定なら False", h.get("r2_backup_configured") is False, {k: h.get(k) for k in ("r2_backup_configured",)})

    print("3) 失敗したスケジューラの検知")
    insert_event(mod, "weekly_reports_run", {"error": "RuntimeError: boom"}, days_ago=0)          # 今日走ったが失敗
    insert_event(mod, "weakness_aggregation_run", {"students_processed": 3}, days_ago=3)         # 3 日前に成功 → 停止
    insert_event(mod, "trial_mgmt_run", {"expire-trials": {"ok": True}}, days_ago=0)            # 今日成功
    rows = {r["name"]: r for r in mod._scheduler_status_rows()}
    check("weekly_reports_run は failed=True", rows["weekly_reports_run"].get("failed") is True, rows["weekly_reports_run"])
    check("trial_mgmt_run は failed=False", rows["trial_mgmt_run"].get("failed") is False, rows["trial_mgmt_run"])
    check("weakness_aggregation_run は stale=True (3日前)", rows["weakness_aggregation_run"].get("stale") is True, rows["weakness_aggregation_run"])
    failed = [e["name"] for e in mod._failed_schedulers(list(rows.values()))]
    stalled = [e["name"] for e in mod._stalled_schedulers(list(rows.values()))]
    check("_failed_schedulers = [weekly_reports_run]", failed == ["weekly_reports_run"], failed)
    check("_stalled_schedulers = [weakness_aggregation_run]", stalled == ["weakness_aggregation_run"], stalled)
    print("4) 実行履歴なしは発報しない")
    check("r2_backup_success は履歴なし → stalled/failed に含まれない", "r2_backup_success" not in failed and "r2_backup_success" not in stalled)
    print("   監視 snapshot → alert")
    try:
        snap = mod._collect_health_snapshot()
        alerts = mod._evaluate_alerts(snap)
        keys = {a["key"]: a for a in alerts}
        check("snapshot に failed_schedulers", [f["name"] for f in snap.get("failed_schedulers", [])] == ["weekly_reports_run"], snap.get("failed_schedulers"))
        check("alert scheduler_failed (critical) が出る", "scheduler_failed" in keys and keys["scheduler_failed"]["severity"] == "critical", list(keys))
        check("alert の本文にジョブ名とエラー", "scheduler_failed" in keys and "週次レポート" in keys["scheduler_failed"]["detail"] and "boom" in keys["scheduler_failed"]["detail"], keys.get("scheduler_failed"))
        check("alert scheduler_stalled も従来どおり出る", "scheduler_stalled" in keys, list(keys))
    except Exception as e:
        check("監視 snapshot / alert の評価が例外なく走る", False, f"{type(e).__name__}: {e}")

    print("5) バックアップ失敗のメール配線 (ソース検査)")
    blk = src[src.index("async def _r2_backup_scheduler"):][:4000]
    check("_r2_backup_scheduler の except で _send_monitor_email を呼ぶ", "_send_monitor_email" in blk and "r2_backup_failed" in blk)
    hc = open(os.path.join(REPO, "scripts", "health_check", "prod_healthcheck.py"), encoding="utf-8").read()
    check("prod_healthcheck は r2_backup_configured=False を FAIL にする", 'h.get("r2_backup_configured")' in hc and "FAIL" in hc[hc.index('h.get("r2_backup_configured")'):][:400])
    check("prod_healthcheck の scheduler_live に r2_backup_success", '"r2_backup_success": 2' in hc)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
