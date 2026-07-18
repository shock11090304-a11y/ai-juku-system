"""Vercel Function: 顧客の登録解除 (退塾処理)

Endpoint: POST /payment/api/admin-registration-cancel

塾長専用。退塾した顧客の Stripe Customer / PaymentMethod を deactivate し、
KV から `reg:completed` を削除。以降の月末バッチで preview に出ない & 引き落とされない。

Body (JSON):
  {
    "registrationId": "reg_xxx",
    "reason": "退塾",  // 任意・KV にアーカイブ記録
    "confirmStudentName": "山田 太郎"  // 必須・誤操作防止 (実際の studentName と一致しないと 400)
  }

処理内容:
  1. KV から reg:completed:{rid} を読む
  2. Stripe PaymentMethod を detach (= 以降使用不可)
  3. Stripe Customer に metadata.canceled_at + metadata.cancel_reason を追加
     (Customer 自体は削除しない・領収書 / 監査履歴を残すため)
  4. KV reg:completed:{rid} を reg:canceled:{rid} に rename + reg:completed:index から削除
  5. canceled index に追加 (退塾履歴の保存)

Response:
  {"ok": true, "registrationId": "reg_xxx", "canceled_at": ...}

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


def _stripe_post(secret_key, path, form, idempotency_key=None):
    """Stripe POST with proper empty-body handling (Content-Length: 0 for empty form)"""
    body = urllib.parse.urlencode(form).encode() if form else b""
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
        "Content-Length": str(len(body)),  # 🚨 空 body でも明示 (Stripe 400 回避)
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(
        f"https://api.stripe.com/v1/{path}",
        data=body,
        headers=headers,
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

            rid = (payload.get("registrationId") or "").strip()
            reason = (payload.get("reason") or "退塾").strip()[:120]
            confirm_name = (payload.get("confirmStudentName") or "").strip()
            if not rid:
                _json(self, 400, {"error": "MISSING_REG_ID"})
                return

            # 🔀 action="update_fee": 月謝額の更新 (生徒一覧の月謝編集を月末引き落とし額=registration.monthly_fee に同期)。
            #    旧Vercel Hobby の Serverless Function 12個上限のため独立 function にせず本 function に同居 (2026-07-18 Pro化で上限解消・同居はそのまま維持)。
            #    action 未指定/その他 = 従来の退塾(cancel)処理 (既存クライアント完全互換)。退塾ロジックは下記で無改変。
            #    安全: read-modify-write で全フィールド保持・EX無し・index/done_key/history 不可侵・customerId 二重照合。
            action = (payload.get("action") or "").strip()
            if action == "update_fee":
                raw_fee = payload.get("monthly_fee", None)
                if raw_fee is None:
                    _json(self, 400, {"error": "MISSING_FEE"}); return
                try:
                    new_fee = int(raw_fee)
                except (TypeError, ValueError):
                    _json(self, 400, {"error": "INVALID_FEE", "message": "monthly_fee は整数で指定してください"}); return
                if new_fee < 0 or new_fee > 1000000:
                    _json(self, 400, {"error": "FEE_OUT_OF_RANGE", "message": "monthly_fee は 0〜1,000,000 の範囲で指定してください"}); return
                fee_breakdown = payload.get("fee_breakdown", None)
                if fee_breakdown is not None:
                    fee_breakdown = str(fee_breakdown)[:300]
                expect_customer_id = (payload.get("expectCustomerId") or "").strip()
                got_u = _redis("GET", f"reg:completed:{rid}")
                if not got_u or not isinstance(got_u, dict) or not got_u.get("result"):
                    _json(self, 404, {"error": "REGISTRATION_NOT_FOUND",
                                      "message": "登録が見つかりません(未紐付け/解除済み)。引き落とし額は更新されません。"}); return
                try:
                    reg_u = json.loads(got_u["result"])
                except Exception:
                    _json(self, 500, {"error": "PARSE_ERROR"}); return
                # 🛡️ 誤レコード更新防止: expectCustomerId が送られたら KV の stripe_customer_id と一致を確認 (重複登録対策)
                actual_cust = (reg_u.get("stripe_customer_id") or "").strip()
                if expect_customer_id and actual_cust and expect_customer_id != actual_cust:
                    _json(self, 409, {"error": "CUSTOMER_MISMATCH",
                                      "message": "紐付け情報と登録レコードの顧客IDが一致しません。重複登録の可能性があるため更新を中止しました。"}); return
                prev_fee = int(reg_u.get("monthly_fee", 0) or 0)
                now_u = int(time.time())
                # read-modify-write: 全既存フィールド保持・monthly_fee(+任意 breakdown)のみ更新・EX 付けない
                record_u = {**reg_u, "monthly_fee": new_fee, "monthly_fee_prev": prev_fee,
                            "monthly_fee_edited_at": now_u, "monthly_fee_edited_by": "admin-roster-edit"}
                if fee_breakdown is not None:
                    record_u["fee_breakdown"] = fee_breakdown
                set_u = _redis("SET", f"reg:completed:{rid}", json.dumps(record_u, ensure_ascii=False))
                if not set_u or not isinstance(set_u, dict) or set_u.get("result") != "OK":
                    _log(f"update-fee SET failed rid={rid} res={set_u}")
                    _json(self, 502, {"error": "KV_WRITE_FAILED", "message": "登録金額の保存に失敗しました。再度お試しください。"}); return
                sname_u = (reg_u.get("studentName") or reg_u.get("student_name") or "").strip()
                _log(f"update-fee: rid={rid} fee {prev_fee} -> {new_fee} customer={actual_cust} name={sname_u}")
                _json(self, 200, {"ok": True, "registrationId": rid, "monthly_fee": new_fee, "prev": prev_fee,
                                  "studentName": sname_u,
                                  "message": f"{sname_u} さんの月末引き落とし額を ¥{prev_fee:,} → ¥{new_fee:,} に更新しました"})
                return
            # ===== 以下、従来の退塾(cancel)処理 (action 未指定時・無改変) =====

            # KV から取得
            got = _redis("GET", f"reg:completed:{rid}")
            if not got or not isinstance(got, dict) or not got.get("result"):
                _json(self, 404, {"error": "REGISTRATION_NOT_FOUND"})
                return
            try:
                reg = json.loads(got["result"])
            except Exception:
                _json(self, 500, {"error": "PARSE_ERROR"})
                return

            actual_name = (reg.get("studentName") or reg.get("student_name") or "").strip()
            if not confirm_name or confirm_name != actual_name:
                _json(self, 400, {
                    "error": "NAME_MISMATCH",
                    "message": f"確認のため生徒氏名 (正しくは '{actual_name}') を正確に入力してください",
                    "expected_name": actual_name,
                })
                return

            customer_id = reg.get("stripe_customer_id", "")
            payment_method_id = reg.get("stripe_payment_method_id", "")
            now_ts = int(time.time())

            # Stripe 側操作
            # 🚨 2nd review fix: PaymentMethod detach 失敗時は KV を canceled 化しない (Stripe 側で card が残るリスク回避)
            #    detach 失敗 → 502 を返して塾長に retry を促す。Customer metadata 更新は best-effort (失敗でも続行)
            secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            stripe_errors = []
            detach_failed = False
            if secret_key:
                # PaymentMethod を detach (= 以降使用不可)・最重要操作
                if payment_method_id:
                    try:
                        # Idempotency-Key で連打防止
                        _stripe_post(secret_key, f"payment_methods/{payment_method_id}/detach", [],
                                     idempotency_key=f"juku-detach-{rid}-{payment_method_id}")
                    except urllib.error.HTTPError as e:
                        try: msg = e.read().decode("utf-8", errors="replace")[:300]
                        except Exception: msg = str(e)
                        # "already detached" のような既に detached 状態のエラーは成功と見なす
                        if "not previously attached" in msg.lower() or "already detached" in msg.lower():
                            stripe_errors.append(f"PM was already detached: {msg[:100]}")
                        else:
                            stripe_errors.append(f"detach PM failed: {msg}")
                            detach_failed = True
                    except Exception as e:
                        stripe_errors.append(f"detach PM exception: {str(e)[:200]}")
                        detach_failed = True
                # Customer に metadata 追加 (削除はしない・領収書 / 監査履歴を残す)
                # ※ Customer metadata 更新失敗は致命傷ではない → best-effort
                if customer_id:
                    try:
                        _stripe_post(secret_key, f"customers/{customer_id}", [
                            ("metadata[canceled_at]", str(now_ts)),
                            ("metadata[cancel_reason]", reason),
                            ("metadata[canceled_by]", "admin-registration-cancel"),
                        ])
                    except urllib.error.HTTPError as e:
                        try: msg = e.read().decode("utf-8", errors="replace")[:200]
                        except Exception: msg = str(e)
                        stripe_errors.append(f"update Customer metadata failed (non-fatal): {msg}")
                    except Exception as e:
                        stripe_errors.append(f"update Customer exception (non-fatal): {str(e)[:200]}")

            # 🚨 detach 失敗時は KV を変更せず 502 を返す (Stripe で card 残り KV canceled の不整合回避)
            if detach_failed:
                _log(f"cancel ABORTED: detach failed rid={rid} pm={payment_method_id} errors={stripe_errors}")
                _json(self, 502, {
                    "error": "STRIPE_DETACH_FAILED",
                    "message": "Stripe で PaymentMethod の detach に失敗しました。Stripe Dashboard で状態を確認後、再度お試しください。KV は変更していません。",
                    "stripe_errors": stripe_errors,
                    "registrationId": rid,
                })
                return

            # KV から reg:completed を canceled に rename
            canceled_record = {
                **reg,
                "canceled_at": now_ts,
                "cancel_reason": reason,
                "stripe_errors": stripe_errors,
                "detach_status": "success" if not detach_failed else "failed",
            }
            _redis("SET", f"reg:canceled:{rid}", json.dumps(canceled_record, ensure_ascii=False), "EX", "31536000")  # 1 year
            _redis("ZADD", "reg:canceled:index", str(now_ts), rid)
            _redis("DEL", f"reg:completed:{rid}")
            _redis("ZREM", "reg:completed:index", rid)

            _log(f"cancel: rid={rid} customer={customer_id} pm={payment_method_id} stripe_errors={stripe_errors}")
            _json(self, 200, {
                "ok": True,
                "registrationId": rid,
                "canceled_at": now_ts,
                "stripe_errors": stripe_errors,
                "message": f"{actual_name} さんの登録を解除しました" + (f" (Stripe metadata 更新で一部 warning: {len(stripe_errors)} 件)" if stripe_errors else ""),
            })
        except Exception as e:
            _log(f"cancel internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
