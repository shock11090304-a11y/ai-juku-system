"""Vercel Function: Stripe Webhook 受信

Endpoint: POST /payment/api/stripe-webhook
  (vercel.json の rewrites で /api/stripe-webhook に流れる)

Stripe Dashboard 設定:
  Developers → Webhooks → Add endpoint
    URL:    https://www.trillion-ai-juku.com/payment/api/stripe-webhook
    Events: checkout.session.completed
            invoice.payment_failed
            invoice.payment_succeeded
            customer.subscription.deleted
            payment_intent.succeeded   (🆕 v2 月末バッチ請求用)
            payment_intent.payment_failed   (🆕 v2 バッチ請求失敗時)

Env:
  STRIPE_WEBHOOK_SECRET   Stripe webhook signing secret (whsec_...)
  KV_REST_API_URL         Upstash Redis REST URL (Vercel KV 自動付与)
  KV_REST_API_TOKEN       Upstash Redis REST token

機能:
  1. checkout.session.completed → KV pending → completed に更新、registrations index に追加
  2. invoice.payment_failed → KV failures index に追加 (塾長ダッシュで一覧表示用)
  3. customer.subscription.deleted → KV cancellations index に追加
  4. その他のイベントは ack のみして無視 (安全)

依存: 標準ライブラリのみ
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import time
import hmac
import hashlib
import urllib.request
import urllib.error


def _log(msg):
    try:
        print(msg, file=sys.stderr, flush=True)
    except Exception:
        pass


def _json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _redis_safe(*args):
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        return None
    try:
        body = json.dumps(list(args)).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"redis error: {e}")
        return None


def _verify_signature(raw_payload: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
    """Stripe-Signature ヘッダ: t=1234,v1=hex,v1=hex,...
    timing-safe HMAC-SHA256 検証 + timestamp tolerance (default 5min)
    """
    if not sig_header or not secret:
        return False
    try:
        items = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
    except Exception:
        return False
    timestamp = items.get("t")
    if not timestamp:
        return False
    # v1 が複数ある場合は最初の v1
    sigs = []
    for part in sig_header.split(","):
        k, _, v = part.partition("=")
        if k == "v1":
            sigs.append(v)
    if not sigs:
        return False
    try:
        ts_int = int(timestamp)
    except Exception:
        return False
    if abs(int(time.time()) - ts_int) > tolerance:
        return False
    signed = f"{timestamp}.".encode() + raw_payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


def _stripe_get(secret_key, path):
    """Stripe GET API helper (SetupIntent 取得用)"""
    if not secret_key:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.stripe.com/v1/{path}",
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Stripe-Version": "2024-06-20",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"stripe GET {path} error: {e}")
        return None


def _handle_checkout_completed(event):
    """🆕 v2 (2026-05-13): mode=setup 対応。
    旧 mode=subscription も後方互換のため一応動くようにしておく。
    """
    obj = event.get("data", {}).get("object", {})
    session_id = obj.get("id", "")
    metadata = obj.get("metadata", {}) or {}
    reg_id = metadata.get("registration_id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")  # mode=subscription 時のみ存在
    setup_intent_id = obj.get("setup_intent", "")  # mode=setup 時のみ存在
    mode = obj.get("mode", "")
    amount = obj.get("amount_total", 0)
    email = obj.get("customer_email") or obj.get("customer_details", {}).get("email", "")

    # 🚨 AIコーチングとの完全分離: system metadata で識別
    # juku-payment 系 (system=juku-payment-monthly or reg_id 有り) 以外は skip
    system_tag = metadata.get("system", "")
    if not reg_id and system_tag != "juku-payment-monthly":
        _log(f"webhook: not juku-payment event (mode={mode} system={system_tag}) — skip")
        return

    if not reg_id:
        _log(f"webhook: missing registration_id (mode={mode}) — skip")
        return

    # 🆕 mode=setup: SetupIntent から payment_method を取得
    # 🚨 2nd review fix: STRIPE_SECRET_KEY 未設定時の warning + customer 取得 fallback
    payment_method = ""
    monthly_fee = 0
    setup_intent_customer = ""  # SetupIntent.customer (Customer 取得 fallback)
    if mode == "setup" and setup_intent_id:
        secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
        if not secret_key:
            _log(f"webhook CRITICAL: STRIPE_SECRET_KEY missing in webhook env (rid={reg_id}) - payment_method will be empty")
        si = _stripe_get(secret_key, f"setup_intents/{setup_intent_id}") if secret_key else None
        if si and isinstance(si, dict):
            payment_method = si.get("payment_method") or ""
            setup_intent_customer = si.get("customer") or ""
        # metadata.monthly_fee は register-subscribe.py で必ず設定される
        try:
            monthly_fee = int(metadata.get("monthly_fee", "0"))
        except Exception:
            monthly_fee = 0

    # 🚨 fallback: session.customer が空でも SetupIntent.customer から復元
    if not customer and setup_intent_customer:
        customer = setup_intent_customer
        _log(f"webhook: customer fallback from SetupIntent rid={reg_id} customer={customer}")

    # pending → completed (KV 失敗時は metadata から最低限復元)
    existing_raw = _redis_safe("GET", f"reg:pending:{reg_id}")
    existing = {}
    if existing_raw and isinstance(existing_raw, dict):
        r = existing_raw.get("result")
        if r:
            try: existing = json.loads(r)
            except Exception: pass
    # KV pending が消失していても Stripe metadata から最低限の情報を復元
    if not existing:
        existing = {
            "registration_id": reg_id,
            "student_name": metadata.get("student_name", ""),
            "grade": metadata.get("grade", ""),
            "parent_name": metadata.get("parent_name", ""),
            "phone": metadata.get("phone", ""),
            "courses": [c for c in metadata.get("courses", "").split(",") if c],
            "options": [o for o in metadata.get("options", "").split(",") if o],
            "fee_breakdown": metadata.get("fee_breakdown", ""),
            "restored_from_metadata": True,
        }
    # 🆕 mode によって record の意味が異なる:
    #   mode=setup       : amount=0 / payment_method 必須 / monthly_fee で月額保存
    #   mode=subscription: amount=初回課金額 / subscription_id 必須 (legacy)
    record = {
        **existing,
        "registration_id": reg_id,
        "session_id": session_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,  # setup 時は空
        "stripe_payment_method_id": payment_method,  # 🆕 setup 時のみ
        "stripe_setup_intent_id": setup_intent_id,  # 🆕 setup 時のみ
        "checkout_mode": mode,  # "setup" or "subscription"
        "status": "completed",
        "completed_at": int(time.time()),
        "amount": amount,  # setup 時は 0
        "monthly_fee": monthly_fee or existing.get("monthly_fee", 0),  # 🆕 月額 (バッチ請求用)
        "email": email or existing.get("email", ""),
        "system": "juku-payment-monthly",
    }
    _redis_safe("SET", f"reg:completed:{reg_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("DEL", f"reg:pending:{reg_id}")
    _redis_safe("ZADD", "reg:completed:index", str(record["completed_at"]), reg_id)
    _log(f"webhook: completed reg={reg_id} mode={mode} customer={customer} pm={payment_method} monthly_fee={monthly_fee}")


def _handle_payment_failed(event):
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング invoice event の混入防止)
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    sub_meta = (obj.get("subscription_details") or {}).get("metadata", {}) or {}
    sys_tag = (meta.get("system") or sub_meta.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: invoice.payment_failed skipped (system={sys_tag} - not juku-payment)")
        return
    invoice_id = obj.get("id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")
    amount_due = obj.get("amount_due", 0)
    next_attempt = obj.get("next_payment_attempt")
    email = obj.get("customer_email", "")
    failure_msg = (obj.get("last_finalization_error") or {}).get("message", "") or ""

    record = {
        "invoice_id": invoice_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,
        "amount_due": amount_due,
        "next_attempt": next_attempt,
        "email": email,
        "failure_message": failure_msg[:300],
        "failed_at": int(time.time()),
    }
    _redis_safe("SET", f"pay:failed:{invoice_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "pay:failed:index", str(record["failed_at"]), invoice_id)
    _log(f"webhook: payment_failed invoice={invoice_id} amount={amount_due}")


def _handle_subscription_deleted(event):
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング subscription event の混入防止)
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    sys_tag = (meta.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: subscription_deleted skipped (system={sys_tag} - not juku-payment)")
        return
    sub_id = obj.get("id", "")
    customer = obj.get("customer", "")
    canceled_at = obj.get("canceled_at") or int(time.time())
    record = {
        "stripe_subscription_id": sub_id,
        "stripe_customer_id": customer,
        "canceled_at": canceled_at,
        "metadata": meta,
    }
    _redis_safe("SET", f"sub:canceled:{sub_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "sub:canceled:index", str(canceled_at), sub_id)
    _log(f"webhook: subscription_deleted sub={sub_id}")


def _handle_payment_succeeded(event):
    """invoice.payment_succeeded — 月次サブスク or 過去未納分の請求書が支払われた時"""
    obj = event.get("data", {}).get("object", {})
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング invoice 混入防止)
    metadata = obj.get("metadata", {}) or {}
    sys_tag = (metadata.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: invoice.payment_succeeded skipped (system={sys_tag} - not juku-payment)")
        return
    invoice_id = obj.get("id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")
    amount_paid = obj.get("amount_paid", 0)
    source = metadata.get("source", "")
    student_name = metadata.get("student_name", "")
    month = metadata.get("month", "")

    record = {
        "invoice_id": invoice_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,
        "amount_paid": amount_paid,
        "metadata": metadata,
        "paid_at": int(time.time()),
        "source": source,
    }
    _redis_safe("SET", f"pay:succeeded:{invoice_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "pay:succeeded:index", str(record["paid_at"]), invoice_id)

    # past-due 由来なら専用 index にも記録 (塾長ダッシュ用)
    if source == "past-due-invoice-v1":
        _redis_safe("SET", f"pastdue:paid:{invoice_id}", json.dumps(record, ensure_ascii=False))
        _redis_safe("ZADD", "pastdue:paid:index", str(record["paid_at"]), invoice_id)
        _log(f"webhook: past-due paid invoice={invoice_id} student={student_name} month={month} amount={amount_paid}")
    else:
        _log(f"webhook: payment_succeeded invoice={invoice_id} amount={amount_paid}")


def _handle_payment_intent_succeeded(event):
    """🆕 v2 (2026-05-13): 月末バッチ請求の PaymentIntent 成功 event を非同期 reconcile 用に記録。
    execute.py が同期 response で既に charge:history を書いているが、SCA 後の銀行 async 承認 etc で
    後から成功になる case を捕捉するための補完。
    """
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    # 🚨 Round 5 fix (C2): 既存 3 handler と統一して startswith 判定 (空文字 = 既存挙動維持)
    # 将来 juku-payment-yearly 等の派生 system を追加した時にも自動的に処理対象になる
    _pi_sys = (meta.get("system") or "").strip()
    if _pi_sys and not _pi_sys.startswith("juku-payment"):
        _log(f"webhook: PaymentIntent skipped (system={_pi_sys} - not juku-payment)")
        return
    pi_id = obj.get("id", "")
    customer = obj.get("customer", "")
    amount = obj.get("amount_received", 0) or obj.get("amount", 0)
    rid = meta.get("registration_id", "")
    month = meta.get("month", "")
    record = {
        "payment_intent_id": pi_id,
        "stripe_customer_id": customer,
        "registration_id": rid,
        "month": month,
        "amount": amount,
        "metadata": meta,
        "status": "succeeded",
        "succeeded_at": int(time.time()),
        "source_event": "payment_intent.succeeded",
    }
    _redis_safe("SET", f"pi:succeeded:{pi_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "pi:succeeded:index", str(record["succeeded_at"]), pi_id)
    # 🚨 2nd/3rd/4th review fix: 自動 reconcile (uncertain + requires_action 両方の case を処理)
    # done_key が既に他の status (succeeded/manually_reconciled/retry) で確定済なら override しない
    # tombstone (unpaid マーク済) があれば auto-reconcile を完全に skip (幽霊復活防止)
    if rid and month:
        tombstone_key = f"charge:unpaid-tombstone:{rid}:{month}"
        tombstone_check = _redis_safe("GET", tombstone_key)
        if tombstone_check and isinstance(tombstone_check, dict) and tombstone_check.get("result"):
            _log(f"webhook: tombstone found, skipping auto-reconcile rid={rid} month={month} pi={pi_id}")
        else:
            uncertain_key = f"charge:uncertain:{rid}:{month}"
            requires_action_key = f"charge:requires_action:{rid}:{month}"
            done_key = f"charge:done:{rid}:{month}"
            existing_uncertain = _redis_safe("GET", uncertain_key)
            existing_requires_action = _redis_safe("GET", requires_action_key)
            should_auto_reconcile = False
            source_state = None
            if existing_uncertain and isinstance(existing_uncertain, dict) and existing_uncertain.get("result"):
                should_auto_reconcile = True
                source_state = "uncertain"
            # 🚨 Round 4 fix (C-BUG-1): requires_action → succeeded の遷移を捕捉
            # SCA 認証完了後の async PI.succeeded で正常に charge:history を書く
            elif existing_requires_action and isinstance(existing_requires_action, dict) and existing_requires_action.get("result"):
                should_auto_reconcile = True
                source_state = "requires_action"

            if should_auto_reconcile:
                # done_key の既存状態を check
                existing_done_raw = _redis_safe("GET", done_key)
                existing_done = None
                if existing_done_raw and isinstance(existing_done_raw, dict):
                    ed_s = existing_done_raw.get("result")
                    if ed_s:
                        try: existing_done = json.loads(ed_s)
                        except Exception: pass
                # 既存 done が succeeded/manually_reconciled なら、上書きせず source state だけ削除
                # 🚨 Round 5 fix (H3): manually_reconciled も skip 条件に追加 (mark_paid との race 防御)
                if existing_done and (
                    existing_done.get("status") in ("succeeded", "processing") or
                    existing_done.get("manually_reconciled") is True
                ):
                    if source_state == "uncertain": _redis_safe("DEL", uncertain_key)
                    elif source_state == "requires_action":
                        _redis_safe("DEL", requires_action_key)
                        _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")
                    _log(f"webhook: {source_state} cleared (done already finalized) rid={rid} month={month} pi={pi_id}")
                else:
                    # 🚨 Round 5 fix (C1): SET NX で atomic に書き込む (手動 mark_paid との同時実行 race 防御)
                    # NX が失敗 = 別経路 (mark_paid 等) で既に書き込まれた → 自分の SET は skip
                    now_ts = int(time.time())
                    nx_result = _redis_safe("SET", done_key, json.dumps({
                        "payment_intent_id": pi_id, "status": "succeeded",
                        "amount": amount, "charged_at": now_ts,
                        "auto_reconciled_from": source_state,
                    }, ensure_ascii=False), "NX", "EX", "5184000")
                    nx_ok = nx_result and isinstance(nx_result, dict) and nx_result.get("result") == "OK"
                    if not nx_ok:
                        # 手動 mark_paid が先に書いた → source state だけ削除して終了
                        if source_state == "uncertain": _redis_safe("DEL", uncertain_key)
                        elif source_state == "requires_action":
                            _redis_safe("DEL", requires_action_key)
                            _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")
                        _log(f"webhook: race detected (manual mark_paid won) {source_state} cleared rid={rid} month={month}")
                        return
                    # 🚨 Round 4 fix: requires_action → succeeded の場合も charge:history に記録
                    # (売上集計から漏れる致命傷を防ぐ)
                    if source_state == "requires_action":
                        student_name = meta.get("student_name", "")
                        email = meta.get("email", "")
                        _history_rec = {
                            "payment_intent_id": pi_id,
                            "registration_id": rid,
                            "month": month,
                            "amount": amount,
                            "student_name": student_name,
                            "email": email,
                            "charged_at": now_ts,
                            "status": "succeeded",
                            "auto_reconciled_from": "requires_action",
                            "source": "sca-async-completion",
                        }
                        _redis_safe("ZADD", "charge:history:index", str(now_ts), f"{rid}:{month}")
                        _redis_safe("SET", f"charge:history:{rid}:{month}", json.dumps(_history_rec, ensure_ascii=False), "EX", "31536000")
                        _redis_safe("RPUSH", f"charge:history:audit:{rid}:{month}", json.dumps(_history_rec, ensure_ascii=False))
                        _redis_safe("EXPIRE", f"charge:history:audit:{rid}:{month}", "31536000")
                        _redis_safe("DEL", requires_action_key)
                        _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")
                    else:
                        _redis_safe("DEL", uncertain_key)
                    _log(f"webhook: auto-reconciled {source_state} → succeeded rid={rid} month={month} pi={pi_id} amount={amount}")
    _log(f"webhook: payment_intent.succeeded rid={rid} month={month} pi={pi_id} amount={amount}")


def _handle_payment_intent_failed(event):
    """🆕 v2 (2026-05-13): 月末バッチ請求の PaymentIntent 失敗 event を記録。
    execute.py が同期 HTTPError で既に charge:failed を書いているが、SCA 後の銀行 async 拒否で
    後から失敗になる case を捕捉するための補完。
    """
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    # 🚨 Round 5 fix (C2): 既存 3 handler と統一して startswith 判定 (空文字 = 既存挙動維持)
    # 将来 juku-payment-yearly 等の派生 system を追加した時にも自動的に処理対象になる
    _pi_sys = (meta.get("system") or "").strip()
    if _pi_sys and not _pi_sys.startswith("juku-payment"):
        _log(f"webhook: PaymentIntent skipped (system={_pi_sys} - not juku-payment)")
        return
    pi_id = obj.get("id", "")
    rid = meta.get("registration_id", "")
    month = meta.get("month", "")
    last_error = obj.get("last_payment_error", {}) or {}
    error_code = last_error.get("code", "")
    decline_code = last_error.get("decline_code", "")
    error_msg = last_error.get("message", "")[:300]
    record = {
        "payment_intent_id": pi_id,
        "registration_id": rid,
        "month": month,
        "amount": obj.get("amount", 0),
        "metadata": meta,
        "error_code": error_code,
        "decline_code": decline_code,
        "error_message": error_msg,
        "failed_at": int(time.time()),
        "source_event": "payment_intent.payment_failed",
    }
    _redis_safe("SET", f"pi:failed:{pi_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "pi:failed:index", str(record["failed_at"]), pi_id)
    _log(f"webhook: payment_intent.payment_failed rid={rid} month={month} pi={pi_id} code={error_code} decline={decline_code}")


HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "invoice.payment_failed": _handle_payment_failed,
    "invoice.payment_succeeded": _handle_payment_succeeded,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "payment_intent.succeeded": _handle_payment_intent_succeeded,
    "payment_intent.payment_failed": _handle_payment_intent_failed,
}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            sig_header = self.headers.get("Stripe-Signature", "")
            secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()

            # 署名検証 (env 未設定なら 503)
            if not secret:
                _log("webhook: STRIPE_WEBHOOK_SECRET not set")
                _json(self, 503, {"error": "WEBHOOK_SECRET_NOT_SET"})
                return

            if not _verify_signature(raw, sig_header, secret):
                _log("webhook: signature verification failed")
                _json(self, 401, {"error": "INVALID_SIGNATURE"})
                return

            try:
                event = json.loads(raw.decode("utf-8"))
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return

            event_type = event.get("type", "")
            event_id = event.get("id", "")

            # idempotency: SET NX EX で原子的に重複検知 (race condition 対策)
            # Stripe が並行リトライしても最初の1件だけが処理される
            seen_key = f"webhook:seen:{event_id}"
            seen = _redis_safe("SET", seen_key, "1", "NX", "EX", "86400")
            # Upstash REST: SET NX で既存キーがある場合 result=null、新規なら "OK"
            if seen and isinstance(seen, dict) and seen.get("result") != "OK":
                _log(f"webhook: duplicate event {event_id} ({event_type}) ignored")
                _json(self, 200, {"received": True, "duplicate": True})
                return

            handler_fn = HANDLERS.get(event_type)
            if handler_fn:
                try:
                    handler_fn(event)
                except Exception as e:
                    _log(f"webhook handler error ({event_type}): {e!r}")
                    # Stripe には 200 を返す (本体は KV best-effort なので失敗してもリトライ要らない)
            else:
                _log(f"webhook: ignored event type {event_type}")

            _json(self, 200, {"received": True, "type": event_type})
        except Exception as e:
            _log(f"webhook internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR"})
