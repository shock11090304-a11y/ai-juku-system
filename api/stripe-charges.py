"""Vercel Function: Stripe Charges 取得 (juku-payment 月謝管理用)

Endpoint: GET /payment-api/stripe-charges?month=YYYY-MM
  (vercel.json の rewrites で /api/stripe-charges に流れる)

Env:
  STRIPE_SECRET_KEY  Stripe Dashboard → Developers → API keys → Secret key
                     (sk_live_... / sk_test_...)

Response (200):
  {
    "month": "2026-04",
    "count": 12,
    "charges": [
      {
        "id": "ch_xxx",
        "amount": 16500,
        "created": 1714003200,
        "currency": "jpy",
        "description": "...",
        "customer_email": "...",
        "customer_name": "ナオイ サチコ",
        "receipt_email": "...",
        "metadata": {...}
      },
      ...
    ]
  }

Response (503): STRIPE_SECRET_KEY 未設定
Response (400): month 形式不正
Response (502): Stripe API エラー (生エラー転送)

依存: 標準ライブラリのみ (stripe SDK 不要)
"""

from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone
import json
import os
import urllib.parse
import urllib.request
import urllib.error


def _json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _month_range(month_str):
    """'YYYY-MM' → (start_ts, end_ts) UTC unix seconds"""
    year, mon = (int(x) for x in month_str.split("-"))
    start = datetime(year, mon, 1, tzinfo=timezone.utc)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)
    return int(start.timestamp()), int(end.timestamp())


def _fetch_stripe_charges(secret_key, start_ts, end_ts):
    """Stripe Charges API を全ページ取得 (status=succeeded のみ)"""
    charges = []
    starting_after = None
    for _page in range(20):  # 安全弁: 最大 100 * 20 = 2000 件
        qs_parts = [
            f"created[gte]={start_ts}",
            f"created[lt]={end_ts}",
            "limit=100",
        ]
        if starting_after:
            qs_parts.append(f"starting_after={starting_after}")
        url = "https://api.stripe.com/v1/charges?" + "&".join(qs_parts)
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Stripe-Version": "2024-06-20",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for ch in data.get("data", []):
            if not (ch.get("paid") and ch.get("status") == "succeeded"):
                continue
            currency = ch.get("currency", "jpy")
            raw_amount = ch.get("amount", 0)
            # JPY は zero-decimal currency (Stripe 仕様) → そのまま
            # USD など decimal は /100
            amount = raw_amount if currency == "jpy" else raw_amount // 100
            bd = ch.get("billing_details") or {}
            charges.append({
                "id": ch.get("id"),
                "amount": amount,
                "created": ch.get("created"),
                "currency": currency,
                "description": ch.get("description") or "",
                "customer_email": bd.get("email") or "",
                "customer_name": bd.get("name") or "",
                "receipt_email": ch.get("receipt_email") or "",
                "metadata": ch.get("metadata") or {},
            })
        if not data.get("has_more"):
            break
        last = data.get("data", [])
        if not last:
            break
        starting_after = last[-1]["id"]
    return charges


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            month = (params.get("month", [""])[0] or "").strip()

            secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            if not secret_key:
                _json(self, 503, {
                    "error": "STRIPE_SECRET_KEY_NOT_SET",
                    "message": "Stripe API キーが Vercel に設定されていません",
                    "hint": "Vercel Dashboard → ai-juku-system → Settings → Environment Variables → STRIPE_SECRET_KEY を追加し、Re-deploy してください。",
                    "dashboard": "https://vercel.com/dashboard",
                })
                return

            try:
                start_ts, end_ts = _month_range(month)
            except Exception:
                _json(self, 400, {
                    "error": "INVALID_MONTH",
                    "message": f"month クエリは YYYY-MM 形式で指定してください (受信値: {month!r})",
                })
                return

            try:
                charges = _fetch_stripe_charges(secret_key, start_ts, end_ts)
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                _json(self, 502, {
                    "error": "STRIPE_API_ERROR",
                    "status": e.code,
                    "message": f"Stripe API がエラーを返しました (HTTP {e.code})",
                    "detail": detail,
                })
                return
            except urllib.error.URLError as e:
                _json(self, 502, {
                    "error": "STRIPE_NETWORK_ERROR",
                    "message": f"Stripe API への通信に失敗しました: {e.reason}",
                })
                return

            _json(self, 200, {
                "month": month,
                "count": len(charges),
                "charges": charges,
            })
        except Exception as e:
            _json(self, 500, {
                "error": "INTERNAL",
                "message": str(e),
            })
