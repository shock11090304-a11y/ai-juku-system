#!/usr/bin/env python3
"""💳 Stripe webhook の署名検証と二重処理防止 (invoice.paid → payments) の回帰テスト (in-process・一時 SQLite)。

システム点検で「決済 webhook (1,200 行超) に自動テストが無く、push すると未検査のまま本番に出る」と確定した点の対処。
署名は stripe ライブラリの検証に通る形 (t=..,v1=HMAC-SHA256(secret, f"{t}.{payload}")) で自前生成する。

  1. 正しい署名の invoice.paid → 200、対象生徒の payments に 1 行 (金額・invoice キー)
  2. 同じ event.id の再送 → duplicate:true、payments は増えない (processed_events の先勝ち)
  3. 別 event.id で同じ invoice (invoice.payment_succeeded として届く) → payments は増えない (invoice キー dedup)
  4. 署名が違う → 400、何も書かない
  5. 生徒に紐づかない有料 invoice → payments に書かず、critical event (payment_unmatched_invoice) を残す
stripe ライブラリが必要 (CI は server/requirements.txt を入れる)。
"""
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
SECRET = "whsec_test_secret_for_regression"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="webhook_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": SECRET,
        "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "", "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_webhook", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def sign(payload: bytes, secret: str = SECRET, ts: int = None) -> str:
    ts = ts or int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def invoice_event(event_id, inv_id, sub_id, customer, amount=19800, etype="invoice.paid"):
    now = int(time.time())
    return {
        "id": event_id, "object": "event", "type": etype, "created": now, "livemode": False,
        "api_version": "2024-06-20",
        "data": {"object": {
            "id": inv_id, "object": "invoice", "customer": customer, "subscription": sub_id,
            "amount_paid": amount, "amount_due": amount, "currency": "jpy", "status": "paid",
            "payment_intent": f"pi_{inv_id}", "created": now, "status_transitions": {"paid_at": now},
            "metadata": {}, "lines": {"object": "list", "data": []},
        }},
    }


def count_payments(mod, sid):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amt FROM payments WHERE student_id = ?", (sid,))
    r = c.fetchone(); conn.close()
    return int(r["n"]), int(r["amt"] or 0)


def main():
    print("💳 Stripe webhook 署名検証・二重処理防止 回帰テスト\n")
    try:
        import stripe  # noqa: F401
    except ImportError:
        print("❌ stripe ライブラリが無い (pip install -r server/requirements.txt)")
        sys.exit(1)
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    conn = mod.db(); c = conn.cursor()
    far = (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat()
    c.execute("INSERT INTO students (name, email, status, plan, trial_end, stripe_customer_id, stripe_subscription_id) VALUES (?,?,?,?,?,?,?)",
              ("Paid W", "w@example.org", "paid", "premium", far, "cus_test_w", "sub_test_w"))
    conn.commit()
    c.execute("SELECT id FROM students WHERE email = ?", ("w@example.org",)); sid = c.fetchone()["id"]
    conn.close()

    def post(ev, sig=None):
        body = json.dumps(ev).encode()
        return client.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": sig or sign(body), "Content-Type": "application/json"})

    print("1) 正しい署名の invoice.paid")
    r = post(invoice_event("evt_test_1", "in_test_1", "sub_test_w", "cus_test_w"))
    check("200 で受理", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
    n, amt = count_payments(mod, sid)
    check("payments に 1 行・金額 19800", n == 1 and amt == 19800, (n, amt))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT stripe_payment_intent FROM payments WHERE student_id = ?", (sid,)); key = c.fetchone()["stripe_payment_intent"]; conn.close()
    check("dedup キーは invoice id に正規化", key == "invoice:in_test_1", key)

    print("2) 同じ event.id の再送")
    r = post(invoice_event("evt_test_1", "in_test_1", "sub_test_w", "cus_test_w"))
    check("duplicate:true で受理", r.status_code == 200 and (r.json() or {}).get("duplicate") is True, r.text[:200])
    check("payments は増えない", count_payments(mod, sid)[0] == 1)

    print("3) 別 event.id・同じ invoice (invoice.payment_succeeded)")
    r = post(invoice_event("evt_test_2", "in_test_1", "sub_test_w", "cus_test_w", etype="invoice.payment_succeeded"))
    check("200 で受理", r.status_code == 200, r.text[:200])
    check("payments は増えない (invoice キーで dedup)", count_payments(mod, sid)[0] == 1)

    print("4) 署名が違う")
    ev = invoice_event("evt_test_3", "in_test_3", "sub_test_w", "cus_test_w")
    r = post(ev, sig=sign(json.dumps(ev).encode(), secret="whsec_wrong"))
    check("400 で拒否", r.status_code == 400, f"{r.status_code} {r.text[:120]}")
    check("payments は増えない", count_payments(mod, sid)[0] == 1)
    r = post(ev, sig=sign(json.dumps(ev).encode(), ts=int(time.time()) - 3600))
    check("古い署名 (1 時間前) も拒否", r.status_code == 400, f"{r.status_code}")

    print("5) 生徒に紐づかない有料 invoice")
    r = post(invoice_event("evt_test_4", "in_test_4", "sub_unknown", "cus_unknown"))
    check("200 で受理 (再送ループを作らない)", r.status_code == 200, r.text[:200])
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM payments WHERE stripe_payment_intent = ?", ("invoice:in_test_4",)); n4 = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM events WHERE name = 'payment_unmatched_invoice'"); ev4 = c.fetchone()["n"]
    conn.close()
    check("payments には書かない", n4 == 0)
    check("critical event (payment_unmatched_invoice) を残す", ev4 >= 1)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
