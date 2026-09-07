#!/usr/bin/env python3
"""📊 ダッシュボードの数字 (2026-09-07) の回帰テスト (in-process・一時 SQLite)。

システム点検で「数字が狂う」と確定した点:
  1. 弱点ヒートマップの分母が存在しない status 'active' → 在籍 (paid/trial/猶予中 past_due) + 合成除外
  2. ユニークセッションが監視の signup_email_status で水増し → サイト訪問の計測イベントだけ数える
  3. 売上推移の「新規本契約」が現在 status='paid' 基準で、解約すると過去の棒が減る → 一度でも月額になった人で数える
  4. 残日数が ceil / floor で経路により違う → _trial_days_left (JST 暦日差) に統一
  5. 週次レポートの集計窓 (実行時刻から 168h) がグラフ (月曜起点) と違う → 既定で JST 月曜 0:00 起点
  6. 生徒向け比較の 30 日窓が JST 日付文字列 vs UTC で 9 時間ずれ → JST 0:00 を UTC に変換
"""
import datetime
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
JST = datetime.timezone(datetime.timedelta(hours=9))


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="numbers_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_numbers", MAIN_PY)
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


def mk(mod, name, email, status, paid_since=None, past_due_days=None):
    conn = mod.db(); c = conn.cursor()
    now = datetime.datetime.utcnow()
    far = (now + datetime.timedelta(days=365)).isoformat()
    pds = (now - datetime.timedelta(days=past_due_days)).strftime("%Y-%m-%d %H:%M:%S") if past_due_days is not None else None
    c.execute("INSERT INTO students (name, email, status, plan, trial_end, paid_since, past_due_since) VALUES (?,?,?,?,?,?,?)",
              (name, email, status, "premium", far, paid_since, pds))
    conn.commit(); c.execute("SELECT id FROM students WHERE email = ?", (email,)); sid = c.fetchone()["id"]; conn.close()
    return sid


def find_list_with(obj, key):
    """レスポンスの中から key を持つ dict のリストを探す (top-level のキー名に依存しない)。"""
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and key in obj[0]:
        return obj
    if isinstance(obj, dict):
        for v in obj.values():
            r = find_list_with(v, key)
            if r: return r
    return None


def main():
    print("📊 ダッシュボードの数字 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    src = open(MAIN_PY, encoding="utf-8").read()
    y = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    A = mk(mod, "Paid A", "a@example.org", "paid", paid_since=y)
    B = mk(mod, "Trial B", "b@example.org", "trial")
    C = mk(mod, "PastDue C", "c@example.org", "past_due", past_due_days=5)
    D = mk(mod, "Expired D", "d@example.org", "expired")
    G = mk(mod, "Canceled G", "g@example.org", "canceled", paid_since=y)
    E = mk(mod, "Monitor", "sentinel@synthetic-monitor.local", "trial")

    print("1) 弱点ヒートマップの分母")
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts, last_seen_at) VALUES (?,?,?,?,?,?,?)",
              (A, "english", "仮定法", 6, 0.4, 6, datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()
    r = client.get("/api/admin/weakness-heatmap?days=30&top_n=20", headers=adm)
    check("weakness-heatmap 200", r.status_code == 200, r.text[:150])
    items = find_list_with(r.json(), "student_count") or []
    it = next((x for x in items if x.get("topic") == "仮定法"), None)
    cov = None
    if it:
        cov = next((v for k, v in it.items() if "coverage" in k or "pct" in k or "percent" in k), None)
    check("分母 = 在籍 3 名 (paid/trial/猶予中) → 1/3 ≈ 33%", cov is not None and 30 <= float(cov) <= 34, (it, cov))
    check("ソース: 'active' の分母が消えている", "status IN ('active', 'trial')" not in src)

    print("2) ユニークセッション")
    conn = mod.db(); c = conn.cursor()
    now_s = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    for name, sess in (("signup_email_status", "student:999"), ("synthetic_checkout_test", "monitor"), ("page_view", "visitor-1"), ("cta_click", "visitor-1"), ("lp_view", "visitor-2")):
        c.execute("INSERT INTO events (name, props, session_id, created_at) VALUES (?, ?, ?, ?)", (name, "{}", sess, now_s))
    conn.commit(); conn.close()
    r = client.get("/api/admin/analytics", headers=adm)
    check("analytics 200", r.status_code == 200, r.text[:150])
    j = r.json()
    s24 = j.get("sessions_24h") if "sessions_24h" in j else (find_list_with(j, "sessions_24h") or [{}])[0].get("sessions_24h")
    if s24 is None:
        # ネストされている場合を探す
        def walk(o):
            if isinstance(o, dict):
                if "sessions_24h" in o: return o["sessions_24h"]
                for v in o.values():
                    r_ = walk(v)
                    if r_ is not None: return r_
            return None
        s24 = walk(j)
    check("訪問イベントのセッションだけ数える (visitor-1, visitor-2 = 2)", s24 == 2, s24)
    check("ソース: 監視アカウント削除時に events も消す", 'DELETE FROM events WHERE session_id = ?' in src[src.index("def _cleanup_sentinel"):][:2500])

    print("3) 売上推移の新規本契約")
    r = client.get("/api/admin/revenue-timeline?days=3", headers=adm)
    check("revenue-timeline 200", r.status_code == 200, r.text[:150])
    rows = find_list_with(r.json(), "paid_count") or []
    total_new = sum(int(x.get("paid_count") or 0) for x in rows)
    check("昨日の新規本契約 = 2 (現在 paid の A + 解約済みの G)", total_new == 2, rows)

    print("4) 残日数の単一定義")
    # 🗓 JST の暦日差 (2026-09-07 再点検で ceil → 暦日差)。now = 2026-09-07 10:00 JST に固定
    now = datetime.datetime(2026, 9, 7, 1, 0, tzinfo=datetime.timezone.utc)
    check("36 時間後 (明日 22:00 に終了) → 1 日 = 「あと1日」", mod._trial_days_left(now + datetime.timedelta(hours=36), now) == 1)
    check("47 時間後 (明後日 9:00 に終了) → 2 日", mod._trial_days_left(now + datetime.timedelta(hours=47), now) == 2)
    check("30 分後 (今日が最終日) → 1 日", mod._trial_days_left(now + datetime.timedelta(minutes=30), now) == 1)
    check("過ぎていれば 0", mod._trial_days_left(now - datetime.timedelta(hours=1), now) == 0)
    check("文字列 (ISO) でも計算できる", mod._trial_days_left((now + datetime.timedelta(hours=36)).isoformat(), now) == 1)
    check("tz 無し文字列は UTC 扱い", mod._trial_days_left((now + datetime.timedelta(hours=47)).replace(tzinfo=None).isoformat(), now) == 2)
    check("ソース: floor 版 (max(1, int(...)/86400)) が残っていない", "max(1, int((te - now).total_seconds() / 86400))" not in src)

    print("5) 週次集計の境界 (JST 月曜 0:00)")
    today_jst = datetime.datetime.now(JST).date()
    monday = datetime.datetime(today_jst.year, today_jst.month, today_jst.day, tzinfo=JST) - datetime.timedelta(days=today_jst.weekday())
    in_week = (monday + datetime.timedelta(minutes=30)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    last_week = (monday - datetime.timedelta(hours=1)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")  # 前週日曜 23:00 JST
    conn = mod.db(); c = conn.cursor()
    for ts in (in_week, last_week):
        c.execute("INSERT INTO question_attempts (student_id, source, subject, topic, is_correct, created_at) VALUES (?,?,?,?,?,?)", (B, "practice", "english", "時制", 1, ts))
    conn.commit(); conn.close()
    # 🗓 集計窓は曜日で変わる (日曜=今週 / 月〜土=先週)。既存の「今週」検査は窓を今週に固定して行う
    _jst = datetime.timezone(datetime.timedelta(hours=9))
    _td = datetime.datetime.now(_jst).date(); _mon = _td - datetime.timedelta(days=_td.weekday())
    _orig_win = mod._weekly_report_window
    mod._weekly_report_window = lambda now_jst=None: (datetime.datetime(_mon.year, _mon.month, _mon.day, tzinfo=_jst).astimezone(datetime.timezone.utc), None)
    try:
        aligned = mod._compute_weekly_stats(B)
        rolling = mod._compute_weekly_stats(B, days=7, week_aligned=False)
    finally:
        mod._weekly_report_window = _orig_win
    # 🗓 2026-09-07 再点検: 月曜以降の手動再実行で窓が「今週月曜 0:00〜現在」の数時間になり全員 skip → 曜日で切替
    _sun = mod._weekly_report_window(datetime.datetime(2026, 9, 13, 19, 0, tzinfo=_jst))
    _wed = mod._weekly_report_window(datetime.datetime(2026, 9, 9, 10, 0, tzinfo=_jst))
    _mon_run = mod._weekly_report_window(datetime.datetime(2026, 9, 7, 9, 0, tzinfo=_jst))
    _d = lambda y, m, d: datetime.datetime(y, m, d, tzinfo=_jst).astimezone(datetime.timezone.utc)
    check("日曜 19:00 の窓 = 今週月曜 0:00 〜 現在", _sun == (_d(2026, 9, 7), None), _sun)
    check("水曜の窓 = 先週月曜 0:00 〜 今週月曜 0:00 (完了した週)", _wed == (_d(2026, 8, 31), _d(2026, 9, 7)), _wed)
    check("月曜朝の再実行も先週分", _mon_run == (_d(2026, 8, 31), _d(2026, 9, 7)), _mon_run)
    # 先週水曜の演習を足すと、月〜土の既定窓 (先週) は 2 問 (日曜 23:00 + 水曜)、日曜の既定窓 (今週) は 1 問になる
    mid_last_week = (monday - datetime.timedelta(days=4)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO question_attempts (student_id, source, subject, topic, is_correct, created_at) VALUES (?,?,?,?,?,?)", (B, "practice", "math", "二次関数", 1, mid_last_week))
    conn.commit(); conn.close()
    _ws = mod._compute_weekly_stats(B)
    _exp = 1 if _td.weekday() == 6 else 2
    check(f"既定の窓は曜日で切替 (今日は {'日曜 → 今週 1 問' if _exp == 1 else '月〜土 → 先週 2 問'})", _ws.get("problems_done") == _exp, _ws)
    check("今週 (月曜 0:00〜) の演習は 1 問", aligned.get("problems_done") == 1, aligned)
    check("rolling 7 日なら前週日曜 23:00 も入る (2 問)", rolling.get("problems_done") == 2, rolling)

    print("6) 生徒向け比較の 30 日窓")
    blk = src[src.index("def student_comparison_overview"):][:6000]
    check("cutoff30 は JST 0:00 を UTC に変換", "astimezone(timezone.utc)" in blk[blk.index("_c30 ="):][:400])

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
