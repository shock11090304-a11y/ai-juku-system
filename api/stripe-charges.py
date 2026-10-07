"""Vercel Function: Stripe Charges 取得 (juku-payment 月謝管理用)

Endpoint: GET /payment/api/stripe-charges?month=YYYY-MM
  (vercel.json の rewrites で /api/stripe-charges に流れる)

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)。他の管理 API と同じ総当たり上限つき。
  🔐 2026-10-08 まで無認証で、URL を知っていれば誰でも月の決済一覧 (支払者の氏名・メール) を取れた。

Env:
  STRIPE_SECRET_KEY  Stripe Dashboard → Developers → API keys → Secret key
                     (sk_live_... / sk_test_...)
  CHAT_ADMIN_PASSWORD  管理パスワード (未設定なら常に 401)
  KV_REST_API_URL / KV_REST_API_TOKEN  失敗回数の記録 (無ければ比較のみ)

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
        "customer_name": "(カード名義)",
        "receipt_email": "...",
        "metadata": {...}
      },
      ...
    ]
  }

Response (401): 管理パスワードが無い・違う・失敗が上限 (IP 10回/時・全体 60回/時) に達している
Response (503): STRIPE_SECRET_KEY 未設定
Response (400): month 形式不正
Response (502): Stripe API エラー (生エラー転送)

依存: 標準ライブラリのみ (stripe SDK 不要)
"""

from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone
import hmac
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


# 🔐 2026-09-07 総当たり対策 (システム点検で確定): パスワード比較だけで試行回数の上限が無く、月末の一括引き落とし・
#   スポット課金・任意宛先メール・顧客一覧が総当たりで開く状態だった。失敗回数を Upstash KV (webhook の冪等化で
#   常用) に IP ごと・全体で記録し、上限に達したら比較せずに拒否する。KV が無い環境では従来どおり比較のみ。
#   ★10 本の関数に同じ塊を置いている (Vercel の Python 関数は 1 ファイル 1 関数で共有モジュールを持たない)。
#     直すときは全部一緒に直すこと。scripts/health_check/test_vercel_admin_guard.py が 10 本とも検査する。
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
            # 🔐 Stripe を呼ぶ前・設定の有無を返す前に認証する (支払者の氏名・メールを返す API のため)
            if not _verify_admin(self):
                _json(self, 401, {
                    "error": "UNAUTHORIZED",
                    "message": "管理パスワードが違うか、入力されていません。失敗が続くと 1 時間ほど受け付けなくなります。",
                    # 認証を付ける前の画面 (開いたままの月謝アプリ) は管理パスワードを送らず、hint だけを表示する
                    "hint": "画面が古いままの場合は再読み込み (Mac は ⌘R・Dock のアプリは開き直す) すると、"
                            "この枠に「🔒 管理パスワード」欄が出ます。",
                })
                return

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
