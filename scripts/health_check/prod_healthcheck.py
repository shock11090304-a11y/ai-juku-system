#!/usr/bin/env python3
"""ai-juku 本番 健全性チェック (READ-ONLY・決定的)。

2026-07-02 の多視点監査で「見つかったけれど気づけていなかった」バグ群を、今後は
毎回・機械的に検出できるようにするための常設ツール。各チェックは今回の実所見に対応:

  deploy_freshness   … Vercel 12関数上限による本番ビルド凍結(HEADと本番のmd5不一致)
  api_health         … 本番API/主要公開ページの死活
  vercel_cap         … api/*.py が 12 を超えていないか(超過=デプロイ全体失敗)
  subject_canonical  … question_attempts/student_weakness の非canonical subject
                       (弱点集計・CEO科目配信が空振りする原因)
  orphan_rows        … 削除済み生徒を参照する活動行(KPI水増し・ゾンビassignment)
  drill_stored_live  … grammar_drills の「N問」表記と実出題(active=1)のズレ
  answer_bias        … 直近取込 grammar_questions の正解位置の偏り(取込前均等化漏れ)
  weekly_report      … 週次レポートが全生徒スキップ(集計ソース断絶で無音no-op)
  monitor_storm      … 監視 monitor_alert の誤発報ストーム(本物のcriticalが埋もれる)
  scheduler_live     … in-process スケジューラの最終実行時刻(停止検知)

使い方:
  # 静的/APIチェックのみ(DB不要・どこでも可)
  python3 scripts/health_check/prod_healthcheck.py

  # DBチェックも含める(本番Postgresへ read-only 接続)
  railway run -s Postgres python3 scripts/health_check/prod_healthcheck.py

  # 静的チェックを飛ばして DB のみ / JSON出力
  ... prod_healthcheck.py --db-only
  ... prod_healthcheck.py --json

終了コード: FAIL が1件でもあれば 1、WARN のみ/全PASS なら 0。CI/cron から使える。
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = "https://ai-juku-api-production.up.railway.app"
SITE = "https://trillion-ai-juku.com"
CANON = {"english", "math", "physics", "chemistry", "biology", "earth", "japanese", "social"}
# 本番と HEAD の md5 が一致すべき主要静的ファイル(Vercelビルド凍結の検知)
FRESHNESS_FILES = [
    "app.js", "ceo.html", "mypage.html", "dojo-drill.html",
    "enrollment.html", "class.html", "checkout.js",
]

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
results = []  # (section, level, message)


def add(section, level, message):
    results.append((section, level, message))


def _http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-juku-healthcheck/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.getcode(), r.read()


# ---------------------------------------------------------------- 静的/API 系
def check_api_health():
    try:
        code, _ = _http_get(f"{API}/api/health")
        add("api_health", PASS if code == 200 else FAIL, f"GET /api/health = {code}")
    except Exception as e:
        add("api_health", FAIL, f"GET /api/health 失敗: {type(e).__name__}: {e}")
    for path in ("mypage.html", "ceo.html", "dojo-drill.html", "enrollment.html"):
        try:
            code, _ = _http_get(f"{SITE}/{path}")
            add("api_health", PASS if code == 200 else FAIL, f"GET /{path} = {code}")
        except Exception as e:
            add("api_health", FAIL, f"GET /{path} 失敗: {type(e).__name__}: {e}")


def check_deploy_freshness():
    """git HEAD のファイル内容と本番配信の md5 を比較。不一致=本番が古い(Vercel凍結の疑い)。"""
    for f in FRESHNESS_FILES:
        try:
            head = subprocess.run(["git", "-C", REPO, "show", f"HEAD:{f}"],
                                   capture_output=True, timeout=20)
            if head.returncode != 0:
                add("deploy_freshness", WARN, f"{f}: HEAD に存在せず(スキップ)")
                continue
            head_md5 = hashlib.md5(head.stdout).hexdigest()
            code, body = _http_get(f"{SITE}/{f}")
            if code != 200:
                add("deploy_freshness", WARN, f"{f}: 本番 HTTP {code}")
                continue
            prod_md5 = hashlib.md5(body).hexdigest()
            if head_md5 == prod_md5:
                add("deploy_freshness", PASS, f"{f}: 本番=HEAD 一致")
            else:
                add("deploy_freshness", FAIL,
                    f"{f}: 本番と HEAD が不一致 (本番が古い/デプロイ凍結の疑い) "
                    f"head={head_md5[:8]} prod={prod_md5[:8]}")
        except Exception as e:
            add("deploy_freshness", WARN, f"{f}: 比較失敗 {type(e).__name__}: {e}")


def check_vercel_cap():
    script = os.path.join(REPO, "scripts", "check_vercel_function_cap.sh")
    if not os.path.exists(script):
        add("vercel_cap", WARN, "check_vercel_function_cap.sh が見つからない")
        return
    try:
        r = subprocess.run(["bash", script], capture_output=True, text=True, timeout=30)
        add("vercel_cap", PASS if r.returncode == 0 else FAIL,
            (r.stdout.strip().splitlines() or ["(no output)"])[-1])
    except Exception as e:
        add("vercel_cap", WARN, f"実行失敗 {type(e).__name__}: {e}")


# ---------------------------------------------------------------- DB 系
def _connect():
    url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import psycopg
    except ImportError:
        add("db", WARN, "psycopg 未インストール — DBチェックをスキップ")
        return None
    try:
        return psycopg.connect(url)
    except Exception as e:
        add("db", FAIL, f"DB接続失敗: {type(e).__name__}: {e}")
        return None


def _table_exists(cur, name):
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name=%s", (name,))
    return cur.fetchone() is not None


def check_subject_canonical(cur):
    for tbl in ("question_attempts", "student_weakness"):
        if not _table_exists(cur, tbl):
            continue
        cur.execute(f"SELECT subject, COUNT(*) FROM {tbl} "
                    f"WHERE subject IS NOT NULL GROUP BY subject")
        rows = cur.fetchall()
        noncanon = [(s, n) for (s, n) in rows if (s or "").strip().lower() not in CANON]
        if not noncanon:
            add("subject_canonical", PASS, f"{tbl}: 全 subject が canonical")
        else:
            total = sum(n for _, n in noncanon)
            top = ", ".join(f"{s}={n}" for s, n in sorted(noncanon, key=lambda x: -x[1])[:6])
            add("subject_canonical", WARN,
                f"{tbl}: 非canonical subject {total}件 (弱点集計/配信が空振りし得る) [{top}]")


def check_orphan_rows(cur):
    for tbl in ("question_attempts", "student_weakness", "grammar_drill_assignments"):
        if not _table_exists(cur, tbl):
            continue
        try:
            cur.execute(
                f"SELECT COUNT(*) FROM {tbl} t "
                f"WHERE t.student_id IS NOT NULL AND t.student_id > 0 "
                f"AND NOT EXISTS (SELECT 1 FROM students s WHERE s.id = t.student_id)")
            n = cur.fetchone()[0]
            add("orphan_rows", PASS if n == 0 else WARN,
                f"{tbl}: 削除済み生徒を参照する orphan {n}件")
        except Exception as e:
            add("orphan_rows", WARN, f"{tbl}: 照会失敗 {type(e).__name__}: {e}")


def check_drill_stored_live(cur):
    if not (_table_exists(cur, "grammar_drills") and _table_exists(cur, "grammar_questions")):
        return
    try:
        cur.execute(
            "SELECT id, question_ids FROM grammar_drills "
            "WHERE created_at >= NOW() - INTERVAL '14 days'")
        mism = 0
        for did, qids_raw in cur.fetchall():
            try:
                qids = json.loads(qids_raw) if isinstance(qids_raw, str) else (qids_raw or [])
            except Exception:
                qids = []
            if not qids:
                continue
            ph = ",".join(["%s"] * len(qids))
            cur.execute(f"SELECT COUNT(*) FROM grammar_questions WHERE id IN ({ph}) AND active=1",
                        tuple(qids))
            live = cur.fetchone()[0]
            if live != len(qids):
                mism += 1
        add("drill_stored_live", PASS if mism == 0 else WARN,
            f"直近14日ドリル: stored≠live(active) {mism}本 (「N問」表記と実出題のズレ)")
    except Exception as e:
        add("drill_stored_live", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_answer_bias(cur):
    if not _table_exists(cur, "grammar_questions"):
        return
    try:
        cur.execute(
            "SELECT source, COUNT(*) FROM grammar_questions "
            "WHERE created_at >= NOW() - INTERVAL '7 days' AND source IS NOT NULL "
            "GROUP BY source HAVING COUNT(*) >= 12")
        sources = cur.fetchall()
        if not sources:
            add("answer_bias", PASS, "直近7日に新規取込バッチなし")
            return
        for src, cnt in sources:
            cur.execute("SELECT answer, COUNT(*) FROM grammar_questions "
                        "WHERE source=%s GROUP BY answer", (src,))
            dist = {int(a): n for a, n in cur.fetchall() if a is not None}
            tot = sum(dist.values()) or 1
            worst = max(dist.values()) / tot if dist else 0
            missing0 = any(dist.get(i, 0) == 0 for i in range(4))
            if worst > 0.5 or missing0:
                add("answer_bias", WARN,
                    f"source='{src}' ({cnt}問): 正解位置に偏り {dist} "
                    f"(取込前ラウンドロビン均等化を推奨)")
            else:
                add("answer_bias", PASS, f"source='{src}' ({cnt}問): 正解位置は均等 {dist}")
    except Exception as e:
        add("answer_bias", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_weekly_report(cur):
    if not _table_exists(cur, "events"):
        return
    try:
        cur.execute(
            "SELECT props FROM events WHERE name='weekly_reports_run' "
            "ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            add("weekly_report", WARN, "weekly_reports_run イベントが無い(未実行?)")
            return
        props = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
        sent = int(props.get("sent_email", 0)) + int(props.get("sent_line", 0))
        skipped = int(props.get("skipped", 0))
        total = int(props.get("total_students", 0) or (sent + skipped))
        if total > 0 and sent == 0:
            add("weekly_report", FAIL,
                f"直近の週次レポートが全スキップ (sent=0 / skipped={skipped} / total={total}) "
                f"= 集計ソース断絶の無音no-op")
        else:
            add("weekly_report", PASS, f"直近の週次レポート sent={sent} skipped={skipped}")
    except Exception as e:
        add("weekly_report", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_monitor_storm(cur):
    if not _table_exists(cur, "events"):
        return
    try:
        cur.execute(
            "SELECT props FROM events WHERE name='monitor_alert' "
            "AND created_at >= NOW() - INTERVAL '24 hours'")
        counts = {}
        for (p,) in cur.fetchall():
            try:
                key = (json.loads(p) if isinstance(p, str) else (p or {})).get("key", "?")
            except Exception:
                key = "?"
            counts[key] = counts.get(key, 0) + 1
        storms = {k: v for k, v in counts.items() if v > 12}  # 24hで12通超=cooldown想定を超える誤発報
        if storms:
            top = ", ".join(f"{k}={v}" for k, v in sorted(storms.items(), key=lambda x: -x[1]))
            add("monitor_storm", WARN,
                f"監視アラートのストーム(24h>12通): {top} = 誤発報で本物の critical が埋もれる恐れ")
        else:
            add("monitor_storm", PASS, f"監視アラート24h={sum(counts.values())}通・ストームなし")
    except Exception as e:
        add("monitor_storm", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_scheduler_live(cur):
    if not _table_exists(cur, "events"):
        return
    watched = {
        "weakness_aggregation_run": 2,   # 日次想定 → 2日以内
        "weekly_reports_run": 8,         # 週次(日曜) → 8日以内
        "weekly_worksheet_run": 8,       # 週次プリント生成
        "trial_mgmt_run": 2,             # 体験フォロー/リマインダの日次バッチ(実イベント名)
    }
    for name, max_days in watched.items():
        try:
            cur.execute(
                "SELECT MAX(created_at) FROM events WHERE name=%s", (name,))
            last = cur.fetchone()[0]
            if last is None:
                add("scheduler_live", WARN, f"{name}: 実行履歴なし")
                continue
            cur.execute("SELECT (NOW() - %s) < (%s || ' days')::interval", (last, max_days))
            ok = cur.fetchone()[0]
            add("scheduler_live", PASS if ok else WARN,
                f"{name}: 最終実行 {last} ({'OK' if ok else f'{max_days}日以上前=停止の疑い'})")
        except Exception as e:
            add("scheduler_live", WARN, f"{name}: 照会失敗 {type(e).__name__}: {e}")


def run_db_checks():
    conn = _connect()
    if conn is None:
        if not any(s == "db" for s, _, _ in results):
            add("db", WARN,
                "DATABASE_PUBLIC_URL 未設定 — DBチェックをスキップ "
                "(`railway run -s Postgres python3 ...` で実行すると有効)")
        return
    try:
        cur = conn.cursor()
        for fn in (check_subject_canonical, check_orphan_rows, check_drill_stored_live,
                   check_answer_bias, check_weekly_report, check_monitor_storm,
                   check_scheduler_live):
            try:
                fn(cur)
            except Exception as e:
                add(fn.__name__, WARN, f"チェック中に例外 {type(e).__name__}: {e}")
                try:
                    conn.rollback()
                except Exception:
                    pass
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-only", action="store_true", help="静的/APIチェックを飛ばす")
    ap.add_argument("--static-only", action="store_true", help="DBチェックを飛ばす")
    ap.add_argument("--json", action="store_true", help="結果を JSON で出力")
    args = ap.parse_args()

    if not args.db_only:
        check_api_health()
        check_deploy_freshness()
        check_vercel_cap()
    if not args.static_only:
        run_db_checks()

    n_fail = sum(1 for _, lv, _ in results if lv == FAIL)
    n_warn = sum(1 for _, lv, _ in results if lv == WARN)

    if args.json:
        print(json.dumps({
            "summary": {"fail": n_fail, "warn": n_warn,
                        "pass": sum(1 for _, lv, _ in results if lv == PASS)},
            "results": [{"section": s, "level": lv, "message": m} for s, lv, m in results],
        }, ensure_ascii=False, indent=2))
    else:
        icon = {PASS: "✅", WARN: "⚠️ ", FAIL: "❌"}
        last_section = None
        for section, lv, msg in results:
            if section != last_section:
                print(f"\n== {section} ==")
                last_section = section
            print(f"  {icon[lv]} {msg}")
        print(f"\n=== 合計: FAIL={n_fail}  WARN={n_warn}  "
              f"PASS={sum(1 for _, lv, _ in results if lv == PASS)} ===")

    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
