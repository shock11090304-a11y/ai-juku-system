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


# 🔐 2026-09-07 総当たり対策 (システム点検で確定): パスワード比較だけで試行回数の上限が無く、月末の一括引き落とし・
#   スポット課金・任意宛先メール・顧客一覧が総当たりで開く状態だった。失敗回数を Upstash KV (webhook の冪等化で
#   常用) に IP ごと・全体で記録し、上限に達したら比較せずに拒否する。KV が無い環境では従来どおり比較のみ。
#   ★9 本の関数に同じ塊を置いている (Vercel の Python 関数は 1 ファイル 1 関数で共有モジュールを持たない)。
#     直すときは全部一緒に直すこと。scripts/health_check/test_vercel_admin_guard.py が 9 本とも検査する。
_ADMIN_FAIL_IP_LIMIT = 10        # 同一 IP: 10 回/時
_ADMIN_FAIL_GLOBAL_LIMIT = 60    # 全体: 60 回/時 (IP を変えながらの総当たりを止める)
_ADMIN_FAIL_WINDOW_SEC = 3600


def _admin_kv(*args):
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        return None
    try:
        req = urllib.request.Request(url, data=json.dumps(list(args)).encode(),
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _admin_client_ip(handler) -> str:
    # Vercel が付ける x-real-ip を優先 (x-forwarded-for の先頭は利用者側で細工できる)
    ip = (handler.headers.get("x-real-ip") or "").strip()
    if not ip:
        xff = (handler.headers.get("x-forwarded-for") or "").strip()
        ip = xff.split(",")[-1].strip() if xff else ""
    return (ip or "unknown")[:64]


def _admin_fail_count(key) -> int:
    r = _admin_kv("GET", key)
    try:
        return int((r or {}).get("result") or 0)
    except (TypeError, ValueError, AttributeError):
        return 0


def _admin_fail_record(key):
    r = _admin_kv("INCR", key)
    try:
        if int((r or {}).get("result") or 0) == 1:
            _admin_kv("EXPIRE", key, str(_ADMIN_FAIL_WINDOW_SEC))
    except (TypeError, ValueError, AttributeError):
        pass


def _verify_admin(handler) -> bool:
    """X-Admin-Password ヘッダで認証。失敗が上限 (IP 10回/時・全体 60回/時) に達していると正しくても通さない。"""
    expected = os.environ.get("CHAT_ADMIN_PASSWORD", "").strip()
    if not expected:
        return False
    got = handler.headers.get("X-Admin-Password", "").strip()
    if not got:
        return False
    ip_key = f"adminfail:ip:{_admin_client_ip(handler)}"
    if (_admin_fail_count(ip_key) >= _ADMIN_FAIL_IP_LIMIT
            or _admin_fail_count("adminfail:global") >= _ADMIN_FAIL_GLOBAL_LIMIT):
        return False
    if hmac.compare_digest(got, expected):
        return True
    _admin_fail_record(ip_key)
    _admin_fail_record("adminfail:global")
    return False


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
                                "monthly_fee": r.get("monthly_fee", 0),
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
