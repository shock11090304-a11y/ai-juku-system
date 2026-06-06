"""Vercel Function: 登録(registration)の月謝額を更新

Endpoint: POST /payment/api/admin-update-registration

塾長専用。生徒一覧で月謝(コース/金額)を編集した時に、紐付け済みの登録レコード
`reg:completed:{rid}` の monthly_fee を名簿の新金額に同期する。
→ 月末引き落とし(preview/execute/「この人だけ」/滞納)が新金額で計算されるようになる。

⚠️ 背景: 月末引き落としは KV の registration.monthly_fee を使う(クライアント金額は不使用)。
   この monthly_fee は従来カード登録時(stripe-webhook)に1回 set されたきりで、名簿の月謝編集が
   反映されず旧金額で引き落とされていた。本endpointが「名簿編集→登録金額」の同期経路。

Body (JSON):
  {
    "registrationId": "reg_xxx",      // 必須・紐付け✓確定済みの regId のみ
    "monthly_fee": 26500,             // 必須・新しい月謝(整数・0〜1,000,000)
    "fee_breakdown": "国公立難関大学 / 設備費",  // 任意・preview 表示用の内訳(表示専用・金額計算には無関係)
    "expectCustomerId": "cus_xxx"     // 任意・送られたら KV の stripe_customer_id と一致確認(誤レコード更新防止)
  }

安全設計:
  - admin パスワード必須 (CHAT_ADMIN_PASSWORD・hmac.compare_digest)
  - read-modify-write: {**reg, "monthly_fee": new} で**全既存フィールドを保持**(customer/pm 等を消さない)
  - SET に EX を付けない (reg:completed は永続。TTL を変えない)
  - reg:completed:index / charge:done:* / charge:history:* / 冪等キー には一切触れない
    (= 当月の二重請求防止機構を壊さない。当月引き落とし済みなら done_key で skip され、差額の追い課金も走らない)
  - 監査: monthly_fee_prev / monthly_fee_edited_at / monthly_fee_edited_by を記録
  - Stripe は呼ばない (月末バッチは KV monthly_fee のみ参照・Stripe metadata は不使用)

Response:
  {"ok": true, "registrationId": "reg_xxx", "monthly_fee": 26500, "prev": 21500, "studentName": "..."}

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import time
import hmac
import urllib.request


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
            if not rid:
                _json(self, 400, {"error": "MISSING_REG_ID"})
                return

            # monthly_fee の検証 (整数・0〜1,000,000)。0 や桁ミスはフロント側で confirm 済み。
            raw_fee = payload.get("monthly_fee", None)
            if raw_fee is None:
                _json(self, 400, {"error": "MISSING_FEE"})
                return
            try:
                new_fee = int(raw_fee)
            except (TypeError, ValueError):
                _json(self, 400, {"error": "INVALID_FEE", "message": "monthly_fee は整数で指定してください"})
                return
            if new_fee < 0 or new_fee > 1000000:
                _json(self, 400, {"error": "FEE_OUT_OF_RANGE", "message": "monthly_fee は 0〜1,000,000 の範囲で指定してください"})
                return

            fee_breakdown = payload.get("fee_breakdown", None)
            if fee_breakdown is not None:
                fee_breakdown = str(fee_breakdown)[:300]
            expect_customer_id = (payload.get("expectCustomerId") or "").strip()

            # KV から registration を取得
            got = _redis("GET", f"reg:completed:{rid}")
            if not got or not isinstance(got, dict) or not got.get("result"):
                _json(self, 404, {"error": "REGISTRATION_NOT_FOUND",
                                  "message": "登録が見つかりません(未紐付け・解除済み等)。引き落とし額は更新されません。"})
                return
            try:
                reg = json.loads(got["result"])
            except Exception:
                _json(self, 500, {"error": "PARSE_ERROR"})
                return

            # 🛡️ 誤レコード更新防止: expectCustomerId が送られたら KV の stripe_customer_id と一致を確認。
            #    (太田來瞳のような重複登録で、紐付け先と違う registration を誤って更新するのを防ぐ二重照合)
            actual_customer_id = (reg.get("stripe_customer_id") or "").strip()
            if expect_customer_id and actual_customer_id and expect_customer_id != actual_customer_id:
                _json(self, 409, {
                    "error": "CUSTOMER_MISMATCH",
                    "message": "紐付け情報と登録レコードの顧客IDが一致しません。重複登録の可能性があるため更新を中止しました。",
                })
                return

            prev_fee = int(reg.get("monthly_fee", 0) or 0)
            now_ts = int(time.time())

            # read-modify-write: 全既存フィールドを保持し monthly_fee のみ(+任意 breakdown)更新。
            record = {
                **reg,
                "monthly_fee": new_fee,
                "monthly_fee_prev": prev_fee,
                "monthly_fee_edited_at": now_ts,
                "monthly_fee_edited_by": "admin-roster-edit",
            }
            if fee_breakdown is not None:
                record["fee_breakdown"] = fee_breakdown

            # ⚠️ EX を付けない (reg:completed は永続)。index/done_key/history には触れない。
            set_res = _redis("SET", f"reg:completed:{rid}", json.dumps(record, ensure_ascii=False))
            if not set_res or not isinstance(set_res, dict) or set_res.get("result") != "OK":
                _log(f"update-registration SET failed rid={rid} res={set_res}")
                _json(self, 502, {"error": "KV_WRITE_FAILED",
                                  "message": "登録金額の保存に失敗しました。再度お試しください。"})
                return

            student_name = (reg.get("studentName") or reg.get("student_name") or "").strip()
            _log(f"update-registration: rid={rid} fee {prev_fee} -> {new_fee} customer={actual_customer_id} name={student_name}")
            _json(self, 200, {
                "ok": True,
                "registrationId": rid,
                "monthly_fee": new_fee,
                "prev": prev_fee,
                "studentName": student_name,
                "message": f"{student_name} さんの月末引き落とし額を ¥{prev_fee:,} → ¥{new_fee:,} に更新しました",
            })
        except Exception as e:
            _log(f"update-registration internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
