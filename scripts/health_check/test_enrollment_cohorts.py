#!/usr/bin/env python3
"""💳🎖 在籍・体験の母集団 (2026-09-07) の回帰テスト (in-process・一時 SQLite・本番に触れない)。

システム点検で確定した 2 点を直した:
  12. past_due (決済失敗) は 30 日の猶予期間中は在籍 (アプリを使える) なのに、週次レポート・一斉送信・
      学習状況・digest・ヒートマップの母集団 status IN ('trial','paid') から消えていた → _enrolled_sql に統一。
  13. 「体験中」「今日の新規」「転換率」が本科 (course='kokuritsu_nankan') と塾生アプリ承認 (ai_disabled=1) の
      status='trial' で膨らみ、転換率の定義が画面ごとに違った → _saas_trial_sql / _saas_conversion に統一。
      満了前キューは stripe_customer_id ではなく stripe_subscription_id で「カード未登録」を判定する
      (体験生に請求書を 1 枚出すと customer が付いてキューから消えていた)。
"""
import datetime
import importlib.util
import os
import sys
import tempfile
import time
import base64, hashlib, hmac

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="cohort_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_cohort", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = mod._admin_token_payload(str(exp))
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def mk(mod, name, email, status, course=None, past_due_days=None, ai_disabled=0, trial_end_days=365,
       stripe_customer_id=None):
    conn = mod.db()
    c = conn.cursor()
    now = datetime.datetime.utcnow()
    trial_end = (now + datetime.timedelta(days=trial_end_days)).isoformat()
    pds = (now - datetime.timedelta(days=past_due_days)).strftime("%Y-%m-%d %H:%M:%S") if past_due_days is not None else None
    c.execute(
        "INSERT INTO students (name, email, status, plan, trial_end, course, grade, past_due_since, ai_disabled, stripe_customer_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, status, "premium", trial_end, course, "高校3年", pds, ai_disabled, stripe_customer_id),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


def main():
    print("💳🎖 在籍・体験の母集団 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    src = open(MAIN_PY, encoding="utf-8").read()

    A = mk(mod, "Paid A", "a@example.org", "paid")                                   # SaaS 有料
    B = mk(mod, "Trial B", "b@example.org", "trial", trial_end_days=2, stripe_customer_id="cus_test_b")  # SaaS 体験 (請求書で customer 付き)
    C = mk(mod, "Honka C", "c@example.org", "trial", course="kokuritsu_nankan", trial_end_days=3650)     # 本科 (体験ではない)
    D = mk(mod, "PastDue D", "d@example.org", "past_due", course="kokuritsu_nankan", past_due_days=5)    # 猶予中
    E = mk(mod, "PastDue E", "e@example.org", "past_due", course="kokuritsu_nankan", past_due_days=40)   # 猶予切れ
    F = mk(mod, "Expired F", "f@example.org", "expired")
    G = mk(mod, "Canceled G", "g@example.org", "canceled")
    H = mk(mod, "JukuApp H", "h@example.org", "trial", ai_disabled=1)                # 塾生アプリ承認 (体験ではない)

    print("12) 在籍 (_enrolled_sql): past_due は猶予期間中だけ在籍")
    conn = mod.db(); c = conn.cursor()
    c.execute(f"SELECT id FROM students WHERE {mod._enrolled_sql()} ORDER BY id")
    ids = [r["id"] for r in c.fetchall()]
    check("paid / trial / 猶予中 past_due が在籍", set(ids) >= {A, B, C, D, H}, ids)
    check("猶予切れ past_due / expired / canceled は在籍ではない", not ({E, F, G} & set(ids)), ids)
    cohort = {s["id"] for s in mod._study_log_dashboard_students(c, (datetime.date.today() - datetime.timedelta(days=6)).isoformat())}
    conn.close()
    check("ヒートマップ母集団に 猶予中 past_due の本科生 (D) が入る", D in cohort and C in cohort, cohort)
    check("ヒートマップ母集団から 猶予切れ past_due (E) は外れる", E not in cohort, cohort)
    dg = client.get("/api/admin/learning-digest", headers=adm).json()
    dids = {s["id"] for s in dg.get("students", [])}
    check("learning-digest (やるべきこと/学習状況) に D が入り E は入らない", D in dids and E not in dids, dids)
    r = client.post("/api/admin/messages/send", json={"target": "broadcast", "broadcast_filter": "all", "subject": "t", "body": "hello", "send_email": False}, headers=adm)
    check("一斉送信 (all) が 200", r.status_code == 200, r.text[:200])
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT recipient_id FROM messages WHERE recipient_type = 'student' AND subject = 't'")
    rcpt = {r_["recipient_id"] for r_ in c.fetchall()}
    conn.close()
    check("一斉送信の宛先に 猶予中 past_due (D) が含まれる", D in rcpt, rcpt)
    check("一斉送信の宛先に 猶予切れ (E) / expired / canceled は含まれない", not ({E, F, G} & rcpt), rcpt)
    r = client.post("/api/admin/messages/send", json={"target": "student", "student_id": D, "subject": "t2", "body": "hi", "send_email": False}, headers=adm)
    check("個別送信も 猶予中 past_due に送れる", r.status_code == 200, r.text[:150])
    wk = src[src.index("def cron_weekly_reports"):][:3000]
    check("週次レポートの母集団が _enrolled_sql (past_due の家庭にも届く)", "_enrolled_sql()" in wk and "status IN ('paid', 'past_due')" in wk)
    for fn in ("_run_weekly_worksheet_generation", "admin_students_ai_usage", "check_inactivity", "admin_list_students_by_course", "_recompute_admission_all"):
        blk = src[src.index(f"def {fn}"):][:4000]
        check(f"{fn} が _enrolled_sql を使う", "_enrolled_sql(" in blk)

    print("13) 体験中 / 新規 / 転換率 (SaaS だけを数える)")
    st = client.get("/api/admin/stats", headers=adm).json()
    sm = st.get("summary") or {}
    check("体験中 = SaaS の trial だけ (B の 1 名)", sm.get("trial") == 1, sm)
    check("本科/塾生アプリの trial は別枠 trial_honka (C, H = 2)", sm.get("trial_honka") == 2, sm)
    check("支払い遅延 past_due が summary に出る (D, E = 2)", sm.get("past_due") == 2, sm)
    check("今日の新規 = SaaS の 4 名 (A,B,F,G)、全体は 8", sm.get("new_today") == 4 and sm.get("new_today_all") == 8, sm)
    check("転換率 = 一度でも月額 (A,G) / SaaS 体験入り (A,B,F,G) = 50.0%", sm.get("conversion_rate_pct") == 50.0 and sm.get("conversion_signups") == 4 and sm.get("conversion_converted") == 2, sm)
    conn = mod.db(); c = conn.cursor()
    conv = mod._saas_conversion(c)
    conn.close()
    check("_saas_conversion は summary と同じ値 (単一定義)", conv["rate_pct"] == sm.get("conversion_rate_pct"), conv)
    snap = mod._collect_health_snapshot()
    check("監視 snapshot の転換率も同じ定義", snap.get("conversion_rate_pct") == 50.0, {k: snap.get(k) for k in ("conversion_rate_pct", "conversion_signups", "conversion_converted")})
    q = client.get("/api/admin/trial/expiring-queue?days=3", headers=adm).json()
    qids = {x.get("id") for x in (q.get("students") or [])}
    check("満了前キュー: customer 付きでもサブスク未登録の体験生 (B) が載る", B in qids, q)
    ap = src[src.index("def admin_autopilot_dashboard"):][:6000]
    check("autopilot の体験申込は _saas_trial_sql + 合成除外", "_saas_trial_sql()" in ap and "_synth_exclude_sql()" in ap[ap.index("_saas_trial_sql()"):][:200])

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
