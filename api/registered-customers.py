"""Vercel Function: 登録済 Stripe Customer 一覧取得 (塾長ダッシュ用)

Endpoint: GET /payment/api/registered-customers

KV `reg:completed:index` ZSET から全 registration_id を読み、
各 `reg:completed:{rid}` を取得して一覧を返す。

Response:
  {
    "count": 42,
    "customers": [
      {
        "registrationId": "reg_xxx",
        "customerId": "cus_xxx",
        "subscriptionId": "sub_xxx",
        "studentName": "山田 太郎",
        "grade": "高校2年",
        "parentName": "山田 花子",
        "email": "yamada@example.com",
        "amount": 7500,
        "completedAt": 1714000000,
        "courses": ["kou2-grammar"],
        "options": []
      },
      ...
    ]
  }

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
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
    def do_GET(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED"})
                return

            # ZRANGE で全 registration_id を取得 (新しい順)
            zr = _redis("ZRANGE", "reg:completed:index", "0", "-1", "REV")
            if not zr or not isinstance(zr, dict):
                _json(self, 200, {"count": 0, "customers": []})
                return
            ids = zr.get("result") or []
            if not isinstance(ids, list):
                ids = []

            customers = []
            for rid in ids[:500]:  # 最大 500 件
                got = _redis("GET", f"reg:completed:{rid}")
                if got and isinstance(got, dict):
                    s = got.get("result")
                    if s:
                        try:
                            r = json.loads(s)
                            customers.append({
                                "registrationId": r.get("registration_id", rid),
                                "customerId": r.get("stripe_customer_id", ""),
                                "subscriptionId": r.get("stripe_subscription_id", ""),
                                "studentName": r.get("studentName") or r.get("student_name") or "",
                                "grade": r.get("grade", ""),
                                "parentName": r.get("parentName") or r.get("parent_name") or "",
                                "email": r.get("email", ""),
                                "phone": r.get("phone", ""),
                                "amount": r.get("amount", 0),
                                "completedAt": r.get("completed_at", 0),
                                "courses": r.get("courses", []),
                                "options": r.get("options", []),
                                "feeBreakdown": r.get("fee_breakdown", ""),
                            })
                        except Exception as e:
                            _log(f"parse error for {rid}: {e}")

            _json(self, 200, {"count": len(customers), "customers": customers})
        except Exception as e:
            _log(f"registered-customers internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR"})
