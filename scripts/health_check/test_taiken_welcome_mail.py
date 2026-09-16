#!/usr/bin/env python3
"""🎓 体験授業 (taiken.html・¥1,500 支払いリンク) の決済完了 → 申込者への案内メール (2026-09-17) の回帰テスト。
本体 webhook の TAIKEN_TRIAL_PLINK_ID 分岐で、従来の塾長通知に加えて申込者へ案内メールを送る。メールは記録器に差し替え。

  1. paid セッション → 申込者へ 1 通 (件名・LINE URL・受付番号・金額・決済画面で選んだ体験クラス)
  2. custom_fields (dropdown/text) を「ラベル: 値」に直す。無ければ空行を作らない
  3. livemode=false / TAIKEN_WELCOME_ENABLED=0 / メール無し → 送らない (例外にもしない)
  4. 塾長通知には体験クラスが「目標:」として載る
  5. 署名付き webhook を通しても同じ (CI の stripe 11.x で実行・ローカル 14+ はスキップ)
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

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []
PLINK = "plink_test_taiken_123"
SECRET = "whsec_test_taiken"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="taiken_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "sk_test_dummy_taiken", "STRIPE_WEBHOOK_SECRET": SECRET,
        "TAIKEN_TRIAL_PLINK_ID": PLINK, "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "re_dummy", "BASE_URL": "https://example.invalid", "DAILY_SNS_TO_EMAIL": "owner@example.invalid",
    })
    os.environ.pop("TAIKEN_WELCOME_ENABLED", None)
    spec = importlib.util.spec_from_file_location("aijuku_main_taiken", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def session(sid="cs_live_t1", paid=True, fields=True, email="parent@example.invalid", livemode=True):
    s = {"id": sid, "object": "checkout.session", "payment_link": PLINK, "payment_status": "paid" if paid else "unpaid",
         "amount_total": 1500, "currency": "jpy", "livemode": livemode, "customer": "cus_t1",
         "customer_details": {"email": email, "name": "テスト 花子"}, "metadata": {}}
    if fields:
        s["custom_fields"] = [
            {"key": "class", "type": "dropdown", "label": {"type": "custom", "custom": "体験したいクラス"},
             "dropdown": {"value": "g1", "options": [{"label": "英文法 Lv.1（標準・高1/2）", "value": "g1"}, {"label": "長文読解 Lv.2", "value": "l2"}]}},
            {"key": "student", "type": "text", "label": {"type": "custom", "custom": "生徒氏名"}, "text": {"value": "テスト 太郎"}},
        ]
    return s


def main():
    mod = load_main()
    print("🎓 体験授業 案内メール 回帰テスト")
    MAILS, OWNER = [], []
    mod._course_send_email = lambda to, subject, body: (MAILS.append({"to": to, "subject": subject, "body": body}) or {"sent": True, "resend_id": "re_t"})
    orig_notify = mod._notify_admin_new_trial
    mod._notify_admin_new_trial = lambda name, email, source, goal=None, amount_jpy=None, repeat_warning=None: OWNER.append({"name": name, "email": email, "source": source, "goal": goal, "amount": amount_jpy})

    # ---- 1/2. 直接呼び出し ----
    r = mod._send_taiken_welcome_email(session())
    check("1a. paid セッションで申込者へ 1 通", r.get("sent") and len(MAILS) == 1 and MAILS[0]["to"] == "parent@example.invalid", (r, MAILS))
    b = MAILS[0]["body"] if MAILS else ""
    check("1b. 件名", MAILS and MAILS[0]["subject"] == "【トリリオン英語塾】体験授業のお申し込みありがとうございます（日程のご相談）", MAILS and MAILS[0]["subject"])
    check("1c. 本文に 宛名・金額・LINE URL・受付番号・入塾時の差し引き", all(x in b for x in ["テスト 花子 様", "1,500円", "https://lin.ee/ZHlrRjh", "cs_live_t1", "初月の月謝から差し引き"]), b[:500])
    check("2a. custom_fields が「ラベル: 値」で載る (dropdown は選択肢のラベル)", "・体験したいクラス: 英文法 Lv.1（標準・高1/2）" in b and "・生徒氏名: テスト 太郎" in b, b[:400])
    MAILS.clear()
    mod._send_taiken_welcome_email(session(sid="cs_live_t2", fields=False))
    b2 = MAILS[0]["body"] if MAILS else ""
    check("2b. custom_fields 無しなら余計な空行を作らない", "ありがとうございます。\n\n■ これからの流れ" in b2, b2[:300])

    # ---- 3. 送らないケース ----
    MAILS.clear()
    mod._send_taiken_welcome_email(session(sid="cs_test_1", livemode=False))
    os.environ["TAIKEN_WELCOME_ENABLED"] = "0"
    mod._send_taiken_welcome_email(session(sid="cs_live_t3"))
    os.environ.pop("TAIKEN_WELCOME_ENABLED", None)
    r3 = mod._send_taiken_welcome_email(session(sid="cs_live_t4", email=""))
    check("3. livemode=false / 無効化 / メール無し は送らず例外にもしない", len(MAILS) == 0 and r3.get("error") == "no email", (MAILS, r3))

    # ---- 5. 署名付き webhook (CI の stripe 11.x) ----
    import stripe as _stripe_lib
    _major = int(str(getattr(_stripe_lib, "VERSION", "0")).split(".")[0] or 0)
    if _major >= 14:
        print(f"  ⏭ 5. 署名付き webhook: stripe {_stripe_lib.VERSION} ではスキップ (CI の 11.x で実行)")
    else:
        from fastapi.testclient import TestClient
        client = TestClient(mod.app)
        MAILS.clear(); OWNER.clear()
        payload = json.dumps({"id": "evt_taiken_1", "object": "event", "api_version": "2024-06-20", "created": int(time.time()), "livemode": True,
                              "type": "checkout.session.completed", "data": {"object": session(sid="cs_live_wh")}}).encode()
        ts = int(time.time()); sig = hmac.new(SECRET.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
        wr = client.post("/api/stripe/webhook", data=payload, headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"})
        check("5a. webhook 200 + taiken 分岐", wr.status_code == 200 and wr.json().get("handled") == "taiken_trial_payment", (wr.status_code, wr.text[:200]))
        check("5b. 申込者メール 1 通 + 塾長通知 1 通", len(MAILS) == 1 and MAILS[0]["to"] == "parent@example.invalid" and len(OWNER) == 1 and OWNER[0]["source"] == "taiken_paid", (MAILS, OWNER))
        check("4. 塾長通知の goal に体験クラス", OWNER and OWNER[0]["goal"] and "体験したいクラス: 英文法 Lv.1" in OWNER[0]["goal"], OWNER)
        MAILS.clear(); OWNER.clear()
        wr2 = client.post("/api/stripe/webhook", data=payload, headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"})
        check("5c. 同じ event の再送は duplicate で何も送らない", wr2.status_code == 200 and wr2.json().get("duplicate") and not MAILS and not OWNER, (wr2.text[:120], MAILS, OWNER))
        conn = mod.db(); c = conn.cursor(); c.execute("SELECT COUNT(*) AS n FROM students"); n = c.fetchone()["n"]; conn.close()
        check("5d. students は増えない (体験はアカウント無し)", n == 0, n)
    mod._notify_admin_new_trial = orig_notify

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}"); sys.exit(1)
    print("✅ 全件 OK")


if __name__ == "__main__":
    main()
