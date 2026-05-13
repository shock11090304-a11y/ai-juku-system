"""Vercel Function: 旧 Subscription mode 登録の Setup mode 移行 (1-shot 用)

Endpoint: POST /payment/api/admin-migrate-legacy-subscription

塾長指示「既存 3 名を月末バッチ運用に自動移行」(2026-05-13) で実装。
旧 mode=subscription で登録された顧客 (現在 Stripe で自動課金中) を
新 mode=setup の月末バッチ対象に **手間ゼロで** 移行する 1-shot endpoint。

【処理内容】各 registration_id について:
  1. Stripe Customer から default_payment_method (or 最新の attached PM) を取得
  2. Stripe Subscription を `cancel_at_period_end=true` でキャンセル予約
     → 当月分の自動課金は走る (Stripe による) / 翌月から自動課金なし
  3. KV `reg:completed:{rid}` を更新:
     - checkout_mode = "setup"
     - stripe_payment_method_id = pm_xxx
     - monthly_fee = (KV の amount field を使用)
     - migrated_at = unix timestamp
     - legacy_subscription_id = sub_xxx (audit 用に保持)
     - cancel_at_period_end = true
     - system = "juku-payment-monthly"

【二重課金回避】
- Subscription は `cancel_at_period_end=true` (= 当月分は Stripe が自動課金・翌月から無し)
- KV に `cancel_at_period_end_until` の period_end timestamp を保存
- preview endpoint で「移行月 (= cancel period 内)」は重複表示しないように...
- ※ 本 endpoint 実行は **月末バッチ実行前** が安全
- ※ 移行後の月: Stripe で自動課金 (= 当月最後の課金) → 翌月から月末バッチで請求

Body (JSON):
  {
    "registrationIds": ["reg_xxx", ...],
    "dryRun": false,    // true: Stripe 変更せずシミュレーションのみ
    "confirmText": "MIGRATE_LEGACY_SUBSCRIPTIONS"  // 必須・誤実行防止
  }

Response (200):
  {
    "migrated": [{"registrationId": "reg_xxx", "studentName": "...", "customerId": "cus_xxx",
                  "paymentMethodId": "pm_xxx", "monthlyFee": 15000,
                  "legacySubscriptionId": "sub_xxx", "subscriptionCanceledAtPeriodEnd": true}],
    "failed": [{"registrationId": "reg_xxx", "error": "..."}],
    "summary": {"total": 3, "migrated": 3, "failed": 0},
    "dryRun": false
  }

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import time
import hmac
import urllib.parse
import urllib.request
import urllib.error


def _log(msg):
    try: print(msg, file=sys.stderr, flush=True)
    except Exception: pass


def _json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _verify_admin(handler):
    expected = os.environ.get("CHAT_ADMIN_PASSWORD", "").strip()
    if not expected:
        return False
    got = handler.headers.get("X-Admin-Password", "").strip()
    return hmac.compare_digest(got, expected) if got else False


def _redis(*args):
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        return None
    try:
        body = json.dumps(list(args)).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"redis error: {e}")
        return None


def _stripe_get(secret_key, path):
    try:
        req = urllib.request.Request(
            f"https://api.stripe.com/v1/{path}",
            headers={"Authorization": f"Bearer {secret_key}", "Stripe-Version": "2024-06-20"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"stripe GET {path} error: {e}")
        raise


def _stripe_post(secret_key, path, form, idempotency_key=None):
    body = urllib.parse.urlencode(form).encode() if form else b""
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
        "Content-Length": str(len(body)),
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(f"https://api.stripe.com/v1/{path}", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_kv_record(key):
    got = _redis("GET", key)
    if not got or not isinstance(got, dict): return None
    s = got.get("result")
    if not s: return None
    try: return json.loads(s)
    except Exception: return None


def _resolve_payment_method(secret_key, customer_id, subscription):
    """Customer or Subscription から有効な PaymentMethod ID を取得"""
    # 優先順位:
    # 1. Subscription.default_payment_method
    # 2. Customer.invoice_settings.default_payment_method
    # 3. Customer.default_source (legacy)
    # 4. List payment_methods?customer=cus_xxx&type=card → 先頭
    if subscription:
        pm = subscription.get("default_payment_method")
        if pm: return pm if isinstance(pm, str) else pm.get("id")
    customer = _stripe_get(secret_key, f"customers/{customer_id}")
    inv = customer.get("invoice_settings", {}) or {}
    pm = inv.get("default_payment_method")
    if pm: return pm if isinstance(pm, str) else pm.get("id")
    # fallback: list attached payment methods
    pm_list = _stripe_get(secret_key, f"payment_methods?customer={customer_id}&type=card&limit=10")
    pms = pm_list.get("data", [])
    if pms:
        # 最新 (data の先頭) を返す
        return pms[0].get("id")
    return None


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED"})
                return
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return

            confirm = (payload.get("confirmText") or "").strip()
            if confirm != "MIGRATE_LEGACY_SUBSCRIPTIONS":
                _json(self, 400, {
                    "error": "CONFIRM_TEXT_MISMATCH",
                    "message": "confirmText に 'MIGRATE_LEGACY_SUBSCRIPTIONS' を指定してください",
                })
                return

            rids = payload.get("registrationIds") or []
            if not isinstance(rids, list) or not rids:
                _json(self, 400, {"error": "MISSING_RIDS"})
                return

            dry_run = bool(payload.get("dryRun", False))
            secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            if not secret_key:
                _json(self, 503, {"error": "STRIPE_SECRET_KEY_NOT_SET"})
                return

            migrated = []
            failed = []

            for rid in rids[:50]:  # 安全上限 50 件
                try:
                    reg = _get_kv_record(f"reg:completed:{rid}")
                    if not reg:
                        failed.append({"registrationId": rid, "error": "registration not found in KV"})
                        continue

                    student_name = reg.get("studentName") or reg.get("student_name") or ""
                    customer_id = reg.get("stripe_customer_id", "")
                    subscription_id = reg.get("stripe_subscription_id", "")
                    monthly_fee = int(reg.get("monthly_fee", 0) or reg.get("amount", 0) or 0)

                    if not customer_id:
                        failed.append({"registrationId": rid, "studentName": student_name,
                                      "error": "stripe_customer_id 欠落"})
                        continue
                    if monthly_fee <= 0:
                        failed.append({"registrationId": rid, "studentName": student_name,
                                      "error": "monthly_fee/amount 欠落 or 0"})
                        continue

                    # 1. Subscription 情報取得 (default_payment_method 探索のため)
                    subscription_obj = None
                    if subscription_id:
                        try:
                            subscription_obj = _stripe_get(secret_key, f"subscriptions/{subscription_id}")
                        except urllib.error.HTTPError as e:
                            # subscription not found = 既にキャンセル済 or 削除済 → 続行
                            _log(f"migrate {rid}: subscription {subscription_id} fetch failed: {e.code}")

                    # 2. PaymentMethod 解決
                    payment_method_id = _resolve_payment_method(secret_key, customer_id, subscription_obj)
                    if not payment_method_id:
                        failed.append({"registrationId": rid, "studentName": student_name,
                                      "error": "PaymentMethod 取得不能 (Customer に attach されていない)"})
                        continue

                    # 3. Subscription を cancel_at_period_end (実行は dry_run でなければ)
                    sub_canceled = False
                    sub_period_end = None
                    if subscription_obj and not dry_run:
                        sub_status = subscription_obj.get("status", "")
                        if sub_status in ("active", "trialing", "past_due"):
                            # 既に cancel_at_period_end=true なら scriptは冪等 (再呼び出し OK)
                            try:
                                updated_sub = _stripe_post(
                                    secret_key,
                                    f"subscriptions/{subscription_id}",
                                    [("cancel_at_period_end", "true"),
                                     ("metadata[migrated_to_setup_mode]", "true"),
                                     ("metadata[migration_rid]", rid),
                                     ("metadata[system]", "juku-payment-monthly")],
                                    idempotency_key=f"migrate-cancel-{rid}-{int(time.time())}",
                                )
                                sub_canceled = bool(updated_sub.get("cancel_at_period_end"))
                                sub_period_end = updated_sub.get("current_period_end")
                            except urllib.error.HTTPError as e:
                                detail_raw = b""
                                try: detail_raw = e.read()
                                except Exception: pass
                                detail = detail_raw.decode("utf-8", errors="replace")[:300]
                                failed.append({"registrationId": rid, "studentName": student_name,
                                              "error": f"subscription cancel 失敗: {detail}"})
                                continue
                        elif sub_status == "canceled":
                            sub_canceled = True  # 既にキャンセル済
                            sub_period_end = subscription_obj.get("current_period_end")
                        else:
                            _log(f"migrate {rid}: subscription status={sub_status} - skipping cancel")

                    # 4. KV record を新形式に更新 (dry_run でなければ)
                    if not dry_run:
                        now_ts = int(time.time())
                        updated_rec = {
                            **reg,
                            "checkout_mode": "setup",
                            "stripe_payment_method_id": payment_method_id,
                            "monthly_fee": monthly_fee,
                            "system": "juku-payment-monthly",
                            "migrated_at": now_ts,
                            "migration_source": "legacy-subscription-to-setup-v1",
                            "legacy_subscription_id": subscription_id,
                            "legacy_subscription_canceled_at_period_end": sub_canceled,
                            "legacy_subscription_period_end": sub_period_end,
                        }
                        _redis("SET", f"reg:completed:{rid}", json.dumps(updated_rec, ensure_ascii=False))

                    migrated.append({
                        "registrationId": rid,
                        "studentName": student_name,
                        "customerId": customer_id,
                        "paymentMethodId": payment_method_id,
                        "monthlyFee": monthly_fee,
                        "legacySubscriptionId": subscription_id,
                        "subscriptionCanceledAtPeriodEnd": sub_canceled,
                        "subscriptionPeriodEnd": sub_period_end,
                        "dryRun": dry_run,
                    })
                except urllib.error.HTTPError as e:
                    detail_raw = b""
                    try: detail_raw = e.read()
                    except Exception: pass
                    detail = detail_raw.decode("utf-8", errors="replace")[:300]
                    failed.append({"registrationId": rid, "error": f"Stripe API error: {detail}"})
                except Exception as e:
                    failed.append({"registrationId": rid, "error": f"{type(e).__name__}: {str(e)[:200]}"})

            _json(self, 200, {
                "migrated": migrated,
                "failed": failed,
                "summary": {
                    "total": len(rids),
                    "migrated": len(migrated),
                    "failed": len(failed),
                },
                "dryRun": dry_run,
            })
        except Exception as e:
            _log(f"migrate internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
