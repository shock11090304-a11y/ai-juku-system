"""Vercel Function: uncertain (timeout) 状態の手動 reconcile + 個別再請求

Endpoint: POST /payment/api/admin-charge-reconcile

塾長専用。timeout などで charge:uncertain に残った record を、
Stripe Dashboard で実際の状態を確認後、塾長が手動で確定/取消する。

Body (JSON):
  {
    "action": "mark_paid" | "mark_unpaid" | "retry",
    "registrationId": "reg_xxx",
    "month": "2026-05",            // 必須・操作ミス防止
    "paymentIntentId": "pi_xxx"    // mark_paid 時に指定 (Stripe Dashboard で確認した PI)
  }

- mark_paid: Stripe で実際は課金されていた → charge:done を success にマーク + charge:history 作成
- mark_unpaid: Stripe で実際は未課金 → charge:uncertain と done_key を削除 (再実行可能化)
- retry: mark_unpaid 後に新規 Idempotency-Key で即時再請求 (=execute と同じロジックを 1 件だけ)

Response:
  {"ok": true, "action": "mark_paid", "registrationId": "reg_xxx", "month": "2026-05"}

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import secrets
import sys
import time
import hmac
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta


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


def _current_month_jst():
    JST = timezone(timedelta(hours=9))
    return datetime.now(JST).strftime("%Y-%m")


def _stripe_get(secret_key, path):
    try:
        req = urllib.request.Request(
            f"https://api.stripe.com/v1/{path}",
            headers={"Authorization": f"Bearer {secret_key}", "Stripe-Version": "2024-06-20"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"stripe GET {path} error: {e}")
        return None


def _stripe_post(secret_key, path, form, idempotency_key=None):
    body = urllib.parse.urlencode(form).encode()
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(f"https://api.stripe.com/v1/{path}", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_record(key):
    got = _redis("GET", key)
    if not got or not isinstance(got, dict): return None
    s = got.get("result")
    if not s: return None
    try: return json.loads(s)
    except Exception: return None


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

            action = (payload.get("action") or "").strip()
            rid = (payload.get("registrationId") or "").strip()
            month = (payload.get("month") or "").strip()
            pi_id = (payload.get("paymentIntentId") or "").strip()

            if action not in ("mark_paid", "mark_unpaid", "retry"):
                _json(self, 400, {"error": "INVALID_ACTION", "message": "action は mark_paid / mark_unpaid / retry のいずれか"})
                return
            if not rid or not month:
                _json(self, 400, {"error": "MISSING_PARAMS", "message": "registrationId と month は必須"})
                return

            # registration 存在確認
            reg = _get_record(f"reg:completed:{rid}")
            if not reg:
                _json(self, 404, {"error": "REGISTRATION_NOT_FOUND"})
                return

            uncertain_key = f"charge:uncertain:{rid}:{month}"
            done_key = f"charge:done:{rid}:{month}"

            if action == "mark_paid":
                # Stripe で実際は課金されていた → charge:done + charge:history を作成
                amount = int(reg.get("monthly_fee", 0) or 0)
                student_name = reg.get("studentName") or reg.get("student_name") or ""
                email = reg.get("email", "")
                phone = reg.get("phone", "")
                now_ts = int(time.time())
                # PI ID を Stripe で verify (任意・指定された場合のみ)
                if pi_id:
                    secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
                    if secret_key:
                        pi = _stripe_get(secret_key, f"payment_intents/{pi_id}")
                        if not pi or pi.get("status") not in ("succeeded", "processing"):
                            _json(self, 400, {
                                "error": "PI_NOT_VERIFIED",
                                "message": f"指定された PaymentIntent ({pi_id}) は succeeded/processing でないため mark_paid できません",
                                "pi_status": pi.get("status") if pi else None,
                            })
                            return
                _redis("SET", done_key, json.dumps({
                    "payment_intent_id": pi_id,
                    "status": "succeeded",
                    "amount": amount,
                    "charged_at": now_ts,
                    "manually_reconciled": True,
                }, ensure_ascii=False), "EX", "5184000")
                _redis("ZADD", "charge:history:index", str(now_ts), f"{rid}:{month}")
                _history_record_mr = {
                    "payment_intent_id": pi_id,
                    "registration_id": rid,
                    "month": month,
                    "amount": amount,
                    "student_name": student_name,
                    "email": email,
                    "phone": phone,
                    "charged_at": now_ts,
                    "status": "succeeded",
                    "manually_reconciled": True,
                    "source": "manual-mark-paid",
                }
                _redis("SET", f"charge:history:{rid}:{month}", json.dumps(_history_record_mr, ensure_ascii=False), "EX", "31536000")
                # 🚨 3rd review fix: append-only audit log
                _redis("RPUSH", f"charge:history:audit:{rid}:{month}", json.dumps(_history_record_mr, ensure_ascii=False))
                _redis("EXPIRE", f"charge:history:audit:{rid}:{month}", "31536000")
                _redis("DEL", uncertain_key)
                # uncertain index からも削除
                _redis("ZREM", "charge:uncertain:index", f"{rid}:{month}")
                # 🚨 Round 4 fix (H1): tombstone も削除 (mark_unpaid → mark_paid 順序の整合性)
                _redis("DEL", f"charge:unpaid-tombstone:{rid}:{month}")
                _log(f"reconcile: mark_paid rid={rid} month={month} pi={pi_id}")
                _json(self, 200, {"ok": True, "action": "mark_paid", "registrationId": rid, "month": month})
                return

            if action == "mark_unpaid":
                # Stripe で実際は未課金 → done_key + uncertain を削除 (再実行可能化)
                # 🚨 3rd review fix: tombstone を SET して webhook auto-reconcile による「幽霊復活」を防ぐ
                # mark_unpaid 後に SCA 後の payment_intent.succeeded event が遅延到着しても、
                # webhook 側で tombstone check して auto-reconcile を skip する
                _redis("DEL", done_key)
                _redis("DEL", uncertain_key)
                _redis("ZREM", "charge:uncertain:index", f"{rid}:{month}")
                # tombstone (30 日 TTL・retry/再実行が完了するまで)
                _redis("SET", f"charge:unpaid-tombstone:{rid}:{month}", json.dumps({
                    "marked_at": int(time.time()),
                    "reason": "manually marked unpaid by admin",
                }, ensure_ascii=False), "EX", "2592000")  # 30 days
                _log(f"reconcile: mark_unpaid rid={rid} month={month} (tombstone set)")
                _json(self, 200, {"ok": True, "action": "mark_unpaid", "registrationId": rid, "month": month})
                return

            if action == "retry":
                # 個別再請求: execute と同じロジックを 1 件だけ実行
                # 🚨 2nd review fix: retry 開始前に SET NX EX で in-flight lock を取得 (二重課金回避)
                # 同時 2 連打を防ぎ、Stripe Idempotency と二重防御
                retry_lock_key = f"charge:retry-inflight:{rid}:{month}"
                lock_acquired = _redis("SET", retry_lock_key, "1", "NX", "EX", "120")  # 120s in-flight
                if not lock_acquired or not isinstance(lock_acquired, dict) or lock_acquired.get("result") != "OK":
                    _json(self, 429, {
                        "error": "RETRY_IN_PROGRESS",
                        "message": "別の retry が進行中です。2 分後に再度お試しください",
                    })
                    return
                # 必ず mark_unpaid 状態 (= done_key が無い) を確認
                check = _redis("GET", done_key)
                if check and isinstance(check, dict) and check.get("result"):
                    _redis("DEL", retry_lock_key)  # lock 解除
                    _json(self, 400, {
                        "error": "ALREADY_LOCKED",
                        "message": "done_key が既に存在します。先に mark_unpaid してから retry してください",
                    })
                    return
                # 再請求実行
                secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
                if not secret_key:
                    _redis("DEL", retry_lock_key)
                    _json(self, 503, {"error": "STRIPE_SECRET_KEY_NOT_SET"})
                    return
                customer_id = reg.get("stripe_customer_id", "")
                payment_method_id = reg.get("stripe_payment_method_id", "")
                monthly_fee = int(reg.get("monthly_fee", 0) or 0)
                if not customer_id or not payment_method_id or monthly_fee <= 0:
                    _redis("DEL", retry_lock_key)
                    _json(self, 400, {"error": "INVALID_REG", "message": "customer/pm/fee が欠落"})
                    return
                student_name = reg.get("studentName") or reg.get("student_name") or ""
                email = reg.get("email", "")
                # 🚨 Idempotency-Key 衝突回避: secrets.token_hex(4) を含めて連続 retry でも別 key になる
                # Stripe 公式仕様: 同じ key で同じ body 再送 = cached response、同じ key で異 body = 400
                # token_hex で衝突確率実質ゼロ → 連打 retry でも別 PI 作成
                idempotency = f"juku-monthly-retry-{rid}-{month}-{monthly_fee}-{int(time.time())}-{secrets.token_hex(4)}"
                form = [
                    ("amount", str(monthly_fee)),
                    ("currency", "jpy"),
                    ("customer", customer_id),
                    ("payment_method", payment_method_id),
                    ("off_session", "true"),
                    ("confirm", "true"),
                    ("description", f"AI学習コーチ塾 月謝 — {student_name} ({month}・手動 retry)"[:220]),
                ]
                if email and "@" in email:
                    form.append(("receipt_email", email))
                _meta = {
                    "system": "juku-payment-monthly",
                    "registration_id": rid,
                    "student_name": student_name,
                    "month": month,
                    "monthly_fee": str(monthly_fee),
                    "email": email,
                    "source": "month-end-batch-retry-v1",
                    "retried_at": str(int(time.time())),
                }
                for k, v in _meta.items():
                    if v is None: continue
                    form.append((f"metadata[{k}]", str(v)[:240]))
                try:
                    pi = _stripe_post(secret_key, "payment_intents", form, idempotency_key=idempotency)
                    pi_new_id = pi.get("id", "")
                    pi_status = pi.get("status", "")
                    if pi_status in ("succeeded", "processing"):
                        now_ts = int(time.time())
                        # 🚨 3rd review fix: retry 成功時は tombstone を削除 (再度 webhook auto-reconcile を許可)
                        _redis("DEL", f"charge:unpaid-tombstone:{rid}:{month}")
                        _redis("SET", done_key, json.dumps({
                            "payment_intent_id": pi_new_id,
                            "status": pi_status,
                            "amount": monthly_fee,
                            "charged_at": now_ts,
                            "retry": True,
                            "retry_count_inc": True,
                        }, ensure_ascii=False), "EX", "5184000")
                        # 🚨 2nd review fix: charge:history は retry suffix で別 key に保存 (元 history を消さない・監査履歴保全)
                        # メインの charge:history:{rid}:{month} は最新成功 PI を上書き OK だが、
                        # それとは別に charge:history-retry:{rid}:{month}:{retry_count} で履歴を残す
                        _redis("ZADD", "charge:history:index", str(now_ts), f"{rid}:{month}")
                        _history_record_retry = {
                            "payment_intent_id": pi_new_id,
                            "registration_id": rid,
                            "month": month,
                            "amount": monthly_fee,
                            "student_name": student_name,
                            "email": email,
                            "phone": reg.get("phone", ""),
                            "charged_at": now_ts,
                            "status": pi_status,
                            "retry": True,
                            "source": "manual-retry",
                            "idempotency_key": idempotency,
                        }
                        _redis("SET", f"charge:history:{rid}:{month}", json.dumps(_history_record_retry, ensure_ascii=False), "EX", "31536000")
                        # 🚨 3rd review fix: append-only audit log
                        _redis("RPUSH", f"charge:history:audit:{rid}:{month}", json.dumps(_history_record_retry, ensure_ascii=False))
                        _redis("EXPIRE", f"charge:history:audit:{rid}:{month}", "31536000")
                        # 履歴追跡: retry 回数を ZADD で記録 (元の history と並列で時系列保存)
                        _redis("ZADD", f"charge:history-retries:{rid}:{month}", str(now_ts), pi_new_id)
                        _redis("SET", f"charge:retry:{rid}:{month}:{pi_new_id}", json.dumps({
                            "payment_intent_id": pi_new_id,
                            "registration_id": rid,
                            "month": month,
                            "amount": monthly_fee,
                            "student_name": student_name,
                            "idempotency_key": idempotency,
                            "retried_at": now_ts,
                            "status": pi_status,
                        }, ensure_ascii=False), "EX", "31536000")
                        _redis("DEL", retry_lock_key)  # in-flight lock 解除
                        _json(self, 200, {
                            "ok": True, "action": "retry", "registrationId": rid, "month": month,
                            "paymentIntentId": pi_new_id, "stripeStatus": pi_status,
                        })
                        return
                    _redis("DEL", retry_lock_key)
                    _json(self, 200, {
                        "ok": False, "action": "retry", "registrationId": rid, "month": month,
                        "paymentIntentId": pi_new_id, "stripeStatus": pi_status,
                        "message": f"unexpected status: {pi_status}",
                    })
                    return
                except urllib.error.HTTPError as e:
                    _redis("DEL", retry_lock_key)
                    detail = ""
                    try: detail = e.read().decode("utf-8", errors="replace")[:300]
                    except Exception: pass
                    _json(self, 502, {"error": "STRIPE_API_ERROR", "detail": detail})
                    return
                except Exception as e:
                    _redis("DEL", retry_lock_key)
                    _json(self, 500, {"error": "RETRY_FAILED", "message": str(e)[:200]})
                    return
        except Exception as e:
            _log(f"reconcile internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
