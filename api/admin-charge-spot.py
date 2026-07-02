"""Vercel Function: 講習費用などの「単発スポット課金」(任意金額・任意名目・即時カード引落)

Endpoint: POST /payment/api/admin-charge-spot

塾長専用・手動。カード紐付け済み(checkout_mode=setup)の生徒の保存カードに、
**月謝とは別に・一回だけ**任意金額を即時引き落とす (off_session PaymentIntent)。
夏期/冬期などの講習費用を「そのままカード請求」する用途。

🚨 月末バッチとの分離 (二重請求防止):
  - monthly_fee は一切変更しない (継続課金額に影響しない)。
  - 月末バッチの `charge:done:{rid}:{month}` ロックは使わず、専用の
    `spot:lock:{rid}:{idemToken}` (SET NX) と Stripe Idempotency-Key で
    二重押下/二重課金を防止する。月次請求とは独立。
  - 記録も `spot:history:*` 名前空間に保存し、月次の入金済みマークには触れない。

Body (JSON):
  {
    "registrationId": "reg_xxx",   // 必須 (カード紐付け済み生徒)
    "amount": 8500,                // 必須・整数円 (1000〜500000)
    "label": "講習費用",            // 任意 (Stripe 明細名目・既定「講習費用」)
    "idemToken": "spot-...."        // 必須・二重押下防止トークン (クライアント生成・確認ごとに一意)
  }

Response (200): {"status":"success","paymentIntentId":"pi_xxx","amount":8500,"studentName":"...","label":"講習費用"}
  失敗時も 200 で {"status":"failed"/"requires_action"/"uncertain", "error":"...", ...}
  入力/認証/前提不備は 4xx。

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD) — 月末バッチ系と同一。
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


SPOT_AMOUNT_MIN = 1000
SPOT_AMOUNT_MAX = 500000


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


def _create_payment_intent(secret_key, customer_id, payment_method_id, amount, description, metadata, idempotency_key):
    """Stripe PaymentIntent 作成 + off_session 即時確定 (=保存済カードから引き落とし)。
    description は呼び出し側指定 (講習費用 等)。月末バッチの同名関数と同方式。"""
    form = [
        ("amount", str(amount)),
        ("currency", "jpy"),
        ("customer", customer_id),
        ("payment_method", payment_method_id),
        ("off_session", "true"),
        ("confirm", "true"),
        ("description", str(description)[:220]),
    ]
    _email = (metadata.get("email") or "").strip()
    if _email and "@" in _email:
        form.append(("receipt_email", _email))
    for k, v in metadata.items():
        if v is None: continue
        form.append((f"metadata[{k}]", str(v)[:240]))

    body = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(
        "https://api.stripe.com/v1/payment_intents",
        data=body,
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Stripe-Version": "2024-06-20",
            "Idempotency-Key": idempotency_key,
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


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

            rid = str(payload.get("registrationId") or "").strip()
            if not rid:
                _json(self, 400, {"error": "REGISTRATION_ID_REQUIRED"})
                return

            # 金額: 整数円・範囲チェック (誤入力で過大課金しないようサーバ側で厳格化)
            try:
                amount = int(payload.get("amount"))
            except (TypeError, ValueError):
                _json(self, 400, {"error": "AMOUNT_INVALID", "message": "amount は整数(円)で指定してください。"})
                return
            if amount < SPOT_AMOUNT_MIN or amount > SPOT_AMOUNT_MAX:
                _json(self, 400, {
                    "error": "AMOUNT_OUT_OF_RANGE",
                    "message": f"金額は {SPOT_AMOUNT_MIN:,}〜{SPOT_AMOUNT_MAX:,} 円の範囲で指定してください (入力: {amount:,})。",
                })
                return

            label = (payload.get("label") or "講習費用").strip()[:40] or "講習費用"

            # 二重押下防止トークン (クライアントが確認ごとに一意生成)。必須。
            idem_token = str(payload.get("idemToken") or "").strip()[:80]
            if not idem_token:
                _json(self, 400, {"error": "IDEM_TOKEN_REQUIRED"})
                return

            secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            if not secret_key:
                _json(self, 503, {"error": "STRIPE_SECRET_KEY_NOT_SET"})
                return

            got = _redis("GET", f"reg:completed:{rid}")
            s = got.get("result") if (got and isinstance(got, dict)) else None
            if not s:
                _json(self, 404, {"error": "REGISTRATION_NOT_FOUND"})
                return
            try:
                r = json.loads(s)
            except Exception:
                _json(self, 500, {"error": "REGISTRATION_PARSE_ERROR"})
                return

            customer_id = r.get("stripe_customer_id", "")
            payment_method_id = r.get("stripe_payment_method_id", "")
            checkout_mode = r.get("checkout_mode", "")
            email = r.get("email", "")
            student_name = r.get("studentName") or r.get("student_name") or ""

            if checkout_mode != "setup":
                _json(self, 400, {"error": "NOT_CARD_LINKED",
                                  "message": f"この生徒はカード即時引落の対象外です (checkout_mode={checkout_mode})。"})
                return
            if not customer_id or not payment_method_id:
                _json(self, 400, {"error": "NO_CARD_ON_FILE",
                                  "message": "保存カード (customer / payment_method) が見つかりません。"})
                return

            # 二重押下防止(1): token 単位ロック (同一操作の再送を弾く・月末の charge:done とは別名前空間)。
            lock_key = f"spot:lock:{rid}:{idem_token}"
            nx = _redis("SET", lock_key, "pending", "NX", "EX", "604800")  # 7 days
            if not nx or not isinstance(nx, dict) or nx.get("result") != "OK":
                _json(self, 409, {"error": "DUPLICATE_SUBMIT",
                                  "message": "同じ操作が既に処理中/処理済みです (二重押下防止)。"})
                return

            # 二重押下防止(2)・安全網: 同一生徒×同一金額の短時間重複を弾く (誤って2回確定した時の二重課金防止)。
            #   別 idemToken でも (rid, amount) が60秒以内に重なれば 409。意図的な再課金は約1分後 or 別金額で可能。
            #   未課金が確定する失敗(HTTPError/canceled/failed)時は recent も解放し、正当な再試行を妨げない。
            recent_key = f"spot:recent:{rid}:{amount}"
            rnx = _redis("SET", recent_key, idem_token, "NX", "EX", "60")
            if not rnx or not isinstance(rnx, dict) or rnx.get("result") != "OK":
                _redis("DEL", lock_key)  # この token では未課金 → token ロック解除
                _json(self, 409, {"error": "RECENT_DUPLICATE",
                                  "message": f"同額 ({amount:,}円) の講習費用を直近に請求済みです（誤操作防止）。本当に2回課金する場合は約1分後、または別金額で再実行してください。"})
                return

            # Stripe 側でも重複防止 (token 単位)。amount も含めて誤retry時の旧額返却を防ぐ。
            idempotency = f"juku-spot-{rid}-{idem_token}-{amount}"
            desc = f"{label} — {student_name}" if student_name else label
            pi_metadata = {
                "system": "juku-payment-spot",
                "registration_id": rid,
                "student_name": student_name,
                "amount": str(amount),
                "label": label,
                "email": email,
                "source": "spot-charge-v1",
                # 🆕 2026-07-02: webhook (payment_intent.succeeded/payment_failed) が
                # spot:history:{rid}:{idem_token} を再構成して 3DS 完了後の status を
                # succeeded/failed に確定更新するための key 素材 (無いと要確認が永久に残る)
                "idem_token": idem_token,
            }

            def _record(status, pi_id, extra=None):
                rec = {
                    "payment_intent_id": pi_id,
                    "registration_id": rid,
                    "amount": amount,
                    "label": label,
                    "student_name": student_name,
                    "email": email,
                    "phone": r.get("phone", ""),
                    "idem_token": idem_token,
                    "status": status,
                    "source": "spot-charge-v1",
                    "at": int(time.time()),
                }
                if extra:
                    rec.update(extra)
                rec_json = json.dumps(rec, ensure_ascii=False)
                _redis("SET", f"spot:history:{rid}:{idem_token}", rec_json, "EX", "31536000")  # 1y
                _redis("ZADD", "spot:history:index", str(int(time.time())), f"{rid}:{idem_token}")
                _redis("RPUSH", f"spot:history:audit:{rid}", rec_json)
                _redis("EXPIRE", f"spot:history:audit:{rid}", "31536000")

            try:
                pi = _create_payment_intent(secret_key, customer_id, payment_method_id,
                                            amount, desc, pi_metadata, idempotency)
                pi_id = pi.get("id", "")
                pi_status = pi.get("status", "")
                if pi_status in ("succeeded", "processing"):
                    _redis("SET", lock_key, json.dumps({
                        "payment_intent_id": pi_id, "status": pi_status,
                        "amount": amount, "charged_at": int(time.time()),
                    }, ensure_ascii=False), "EX", "604800")
                    _record(pi_status, pi_id)
                    _json(self, 200, {
                        "status": "success", "paymentIntentId": pi_id,
                        "studentName": student_name, "amount": amount,
                        "label": label, "stripeStatus": pi_status,
                    })
                elif pi_status == "requires_action":
                    # 3DS 認証が必要 → ロック保持 (重複防止)・顧客にカード会社の本人確認が走る
                    next_action = pi.get("next_action", {}) or {}
                    redirect = (next_action.get("redirect_to_url") or {}).get("url", "")
                    _record("requires_action", pi_id, {"redirect_url": redirect})
                    _json(self, 200, {
                        "status": "requires_action", "paymentIntentId": pi_id,
                        "studentName": student_name, "amount": amount, "label": label,
                        "redirectUrl": redirect,
                        "error": "3DS 認証が必要です (顧客のカード会社の本人確認後に課金が確定します)。",
                    })
                else:
                    # canceled/failed 等 → ロック解除 (再試行可・未課金確定なので recent も解放)
                    _redis("DEL", lock_key)
                    _redis("DEL", recent_key)
                    _record("failed", pi_id, {"stripe_status": pi_status})
                    _json(self, 200, {
                        "status": "failed", "paymentIntentId": pi_id,
                        "studentName": student_name, "amount": amount, "label": label,
                        "stripeStatus": pi_status, "error": f"unexpected status: {pi_status}",
                    })
            except urllib.error.HTTPError as e:
                # Stripe がエラー応答 = リクエストは届いた = 課金は走っていない → ロック解除し再試行可
                detail_raw = b""
                try: detail_raw = e.read()
                except Exception: pass
                detail = detail_raw.decode("utf-8", errors="replace")[:500]
                error_code = ""; decline_code = ""
                try:
                    err_obj = json.loads(detail).get("error", {})
                    error_code = err_obj.get("code", "")
                    decline_code = err_obj.get("decline_code", "")
                except Exception:
                    pass
                _redis("DEL", lock_key)
                _redis("DEL", recent_key)  # 未課金確定 → 同額の正当な再試行を妨げない
                _record("failed", "", {"error_code": error_code, "decline_code": decline_code,
                                       "error_detail": detail[:300]})
                _json(self, 200, {
                    "status": "failed", "studentName": student_name, "amount": amount, "label": label,
                    "errorCode": error_code, "declineCode": decline_code, "error": detail[:200],
                })
            except (urllib.error.URLError, Exception) as e:
                # timeout / 想定外 = 課金有無が不明 → ロック保持 (二重課金回避)・要 Stripe Dashboard 確認
                _log(f"spot PI uncertain reg={rid}: {e!r} - keeping lock")
                _redis("SET", lock_key, json.dumps({
                    "status": "uncertain", "amount": amount, "idempotency_key": idempotency,
                    "noted_at": int(time.time()), "error": str(e)[:200],
                }, ensure_ascii=False), "EX", "604800")
                _record("uncertain", "", {"idempotency_key": idempotency, "error": str(e)[:300]})
                _json(self, 200, {
                    "status": "uncertain", "studentName": student_name, "amount": amount, "label": label,
                    "error": f"ネットワーク等で課金有無が不明です。Stripe Dashboard で確認してください: {str(e)[:150]}",
                })
        except Exception as e:
            _log(f"spot charge internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
