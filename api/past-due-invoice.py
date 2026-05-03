"""Vercel Function: 過去未納分 Stripe Invoice 発行 (1 件 or 複数)

Endpoint: POST /payment/api/past-due-invoice

Body (JSON):
  {
    "items": [
      {
        "customerId": "cus_xxx",       # Stripe Customer ID (登録時に保存)
        "studentName": "山田 太郎",
        "month": "2026-04",            # 請求対象月 (記録用、metadata)
        "amount": 7500,                # JPY 整数 (zero-decimal)
        "description": "AI学習コーチ塾 2026年4月分 月謝"
      },
      ...
    ]
  }

各 item に対し:
  1. Invoice Item 作成 (customer + amount + description)
  2. Invoice 作成 (collection_method=send_invoice、days_until_due=7)
  3. finalize → send → hosted_invoice_url 取得 → Stripe からメール自動送信

Response:
  {
    "results": [
      {
        "studentName": "山田 太郎",
        "month": "2026-04",
        "status": "success",
        "invoiceId": "in_xxx",
        "hostedInvoiceUrl": "https://invoice.stripe.com/...",
        "amountDue": 7500
      },
      {
        "studentName": "佐藤 花子",
        "status": "error",
        "error": "no_payment_method"
      },
      ...
    ],
    "summary": { "total": 10, "success": 9, "failed": 1 }
  }

Env:
  STRIPE_SECRET_KEY    Stripe Secret Key (Vercel に既に設定済)
  KV_REST_API_*        Upstash Redis (任意、過去請求履歴を記録)
  CHAT_ADMIN_PASSWORD  認証 (X-Admin-Password ヘッダ)
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


def _verify_admin(handler) -> bool:
    expected = os.environ.get("CHAT_ADMIN_PASSWORD", "").strip()
    if not expected:
        return False
    got = handler.headers.get("X-Admin-Password", "").strip()
    return hmac.compare_digest(got, expected) if got else False


def _redis_safe(*args):
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


def _stripe_post(secret_key, path, params, idempotency_key=None):
    body = urllib.parse.urlencode(params, doseq=True).encode()
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(f"https://api.stripe.com{path}", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _lookup_registered_customer(customer_id):
    """KV から登録済 Customer 情報を取得。この塾の顧客でなければ None"""
    if not customer_id or not customer_id.startswith("cus_"):
        return None
    zr = _redis_safe("ZRANGE", "reg:completed:index", "0", "-1")
    if not zr or not isinstance(zr, dict):
        return None
    ids = zr.get("result") or []
    if not isinstance(ids, list):
        return None
    for rid in ids:
        got = _redis_safe("GET", f"reg:completed:{rid}")
        if not got or not isinstance(got, dict):
            continue
        s = got.get("result")
        if not s:
            continue
        try:
            r = json.loads(s)
            if r.get("stripe_customer_id") == customer_id:
                return r
        except Exception:
            continue
    return None


def _create_one_invoice(secret_key, item):
    """1 顧客分の Invoice 発行。例外発生時は呼び出し側でハンドル"""
    customer_id = item.get("customerId", "").strip()
    student_name = (item.get("studentName") or "").strip()[:80]
    month = (item.get("month") or "").strip()[:10]
    amount = int(item.get("amount", 0))
    description = (item.get("description") or "").strip()[:240] or f"AI学習コーチ塾 {month} 月謝"

    if not customer_id.startswith("cus_"):
        return {"status": "error", "error": "invalid_customer_id", "studentName": student_name, "month": month}
    if amount <= 0 or amount > 10_000_000:
        return {"status": "error", "error": "invalid_amount", "studentName": student_name, "month": month}

    # 🛡 顧客検証 + 金額検証 (この塾の登録顧客であり、月謝額が登録時と整合するか)
    registered = _lookup_registered_customer(customer_id)
    if not registered:
        _log(f"customer not in our registry: {customer_id}")
        return {"status": "error", "error": "customer_not_registered", "studentName": student_name, "month": month}
    registered_amount = int(registered.get("amount") or 0)
    # 月謝の ±50% 以内まで許容 (オプション増減対応)。攻撃者が任意金額請求できないようガード。
    if registered_amount > 0:
        if amount < registered_amount * 0.5 or amount > registered_amount * 1.5:
            _log(f"amount mismatch: requested={amount} registered={registered_amount} cust={customer_id}")
            return {"status": "error", "error": "amount_out_of_range", "studentName": student_name, "month": month}

    metadata = {
        "metadata[source]": "past-due-invoice-v1",
        "metadata[student_name]": student_name,
        "metadata[month]": month,
    }

    # Idempotency: 同じ Customer × Month で重複発行を防ぐ
    # (Stripe Idempotency-Key + KV 状態の二重保険)
    idempotency_key = f"pastdue-{customer_id}-{month}"
    issued_key = f"pastdue:issued:{customer_id}:{month}"
    issued_check = _redis_safe("GET", issued_key)
    if issued_check and isinstance(issued_check, dict) and issued_check.get("result"):
        _log(f"already issued for {customer_id} {month}")
        existing = issued_check.get("result", "")
        try:
            existing_data = json.loads(existing)
            return {
                "status": "duplicate",
                "studentName": student_name,
                "month": month,
                "invoiceId": existing_data.get("invoice_id", ""),
                "issuedAt": existing_data.get("issued_at", 0),
                "error": "already_issued",
            }
        except Exception:
            return {"status": "error", "error": "already_issued", "studentName": student_name, "month": month}

    try:
        # 1. Invoice 先作成 (collection_method=send_invoice + auto_advance=false で finalize/send 完全手動)
        # auto_advance=false により Stripe が自動 finalize しない → /send 二重発火を防ぐ
        inv_params = {
            "customer": customer_id,
            "collection_method": "send_invoice",
            "days_until_due": "7",
            "auto_advance": "false",
            "description": description[:500],
            "footer": "ご不明点は塾長までLINEでお気軽にお問い合わせください。",
            **metadata,
        }
        inv_resp = _stripe_post(secret_key, "/v1/invoices", inv_params, idempotency_key=idempotency_key)
        invoice_id = inv_resp["id"]

        # 2. Invoice Item を作成し、上で作った Invoice に紐付け (invoice=in_xxx 必須)
        # これで月次サブスクの Invoice に紛れ込まない
        item_params = {
            "customer": customer_id,
            "amount": str(amount),
            "currency": "jpy",
            "description": description[:500],
            "invoice": invoice_id,
            **metadata,
        }
        _stripe_post(secret_key, "/v1/invoiceitems", item_params, idempotency_key=f"{idempotency_key}-item")

        # 3. Finalize (draft → open)
        _stripe_post(secret_key, f"/v1/invoices/{invoice_id}/finalize", {})

        # 4. Send (顧客にメール送信)
        sent = _stripe_post(secret_key, f"/v1/invoices/{invoice_id}/send", {})

        # KV に履歴
        record = {
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "student_name": student_name,
            "month": month,
            "amount": amount,
            "description": description,
            "hosted_invoice_url": sent.get("hosted_invoice_url", ""),
            "status": sent.get("status", "open"),
            "issued_at": int(time.time()),
        }
        _redis_safe("SET", f"pastdue:{invoice_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")  # 1 year
        _redis_safe("ZADD", "pastdue:index", str(record["issued_at"]), invoice_id)
        # 重複ガード: customer + month で 90 日 (この期間内は再発行不可)
        guard = json.dumps({"invoice_id": invoice_id, "issued_at": record["issued_at"]}, ensure_ascii=False)
        _redis_safe("SET", issued_key, guard, "EX", "7776000")  # 90 days

        return {
            "status": "success",
            "invoiceId": invoice_id,
            "hostedInvoiceUrl": sent.get("hosted_invoice_url", ""),
            "amountDue": amount,
            "studentName": student_name,
            "month": month,
        }
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        _log(f"invoice creation HTTPError {e.code}: {detail}")
        # Stripe error message を保護者向けに無難な日本語にマップ
        msg = "no_payment_method" if "payment_method" in detail.lower() else f"stripe_error_{e.code}"
        return {"status": "error", "error": msg, "studentName": student_name, "month": month}
    except Exception as e:
        _log(f"invoice creation error: {e!r}")
        return {"status": "error", "error": "internal", "studentName": student_name, "month": month}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED"})
                return

            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return

            items = payload.get("items") or []
            if not isinstance(items, list) or not items:
                _json(self, 400, {"error": "VALIDATION_FAILED", "message": "items 配列が必要です"})
                return
            if len(items) > 200:
                _json(self, 400, {"error": "TOO_MANY_ITEMS", "message": "1リクエスト 200 件まで"})
                return

            secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            if not secret_key:
                _json(self, 503, {"error": "STRIPE_KEY_NOT_SET"})
                return

            results = []
            success_count = 0
            failed_count = 0
            for it in items:
                res = _create_one_invoice(secret_key, it)
                results.append(res)
                if res.get("status") == "success":
                    success_count += 1
                else:
                    failed_count += 1

            _json(self, 200, {
                "results": results,
                "summary": {"total": len(items), "success": success_count, "failed": failed_count},
            })
        except Exception as e:
            _log(f"past-due-invoice internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR"})
