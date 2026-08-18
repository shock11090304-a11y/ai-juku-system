"""神テスト 契約管理 — Stripe カスタマーポータルへの入口。

Endpoint: POST /api/portal   (kamitest の Vercel プロジェクト)
Headers:  Authorization: Bearer <Supabase セッションの access_token>

ログイン中の契約者に、Stripe のポータル (カード変更・解約) の URL を返す。
account.html がこれを呼んで遷移する。特商法の「解約方法」の実体でもあるので、
このエンドポイントを消すときは exam-app/legal.html の解約方法も直すこと。

★ 本人確認は Supabase の access_token で行う (トークンの持ち主の user_id しか使わない
  ので、他人の契約のポータルは開けない)。
★ 事前に Stripe Dashboard で Customer portal を有効化しておくこと (§22)。

Env: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY / STRIPE_SECRET_KEY
     PUBLIC_BASE_URL (任意) / STRIPE_API_BASE (検査用)

検査: python3 scripts/book_exam/check_signup.py
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


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


def _sb_call(method, path, payload=None, extra_headers=None, timeout=15):
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"].strip()
    headers = {"apikey": key, "Authorization": f"Bearer {key}",
               "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    url = os.environ["SUPABASE_URL"].strip().rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def user_from_token(access_token):
    """トークンの持ち主を GoTrue に聞く。無効なら None。"""
    try:
        res = _sb_call("GET", "/auth/v1/user", None,
                       {"Authorization": f"Bearer {access_token}"})
        return res if isinstance(res, dict) and res.get("id") else None
    except urllib.error.HTTPError:
        return None


def _stripe_post(path, form):
    key = os.environ["STRIPE_SECRET_KEY"].strip()
    base = os.environ.get("STRIPE_API_BASE", "https://api.stripe.com").rstrip("/")
    body = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(
        f"{base}/v1/{path}", data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/x-www-form-urlencoded",
                 "Stripe-Version": "2024-06-20"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _base_url(handler):
    base = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base:
        return base
    proto = handler.headers.get("X-Forwarded-Proto") or "https"
    host = (handler.headers.get("X-Forwarded-Host") or handler.headers.get("Host")
            or "exam.trillion-ai-juku.com")
    return f"{proto}://{host}"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            missing = [k for k in ("STRIPE_SECRET_KEY", "SUPABASE_URL",
                                   "SUPABASE_SERVICE_ROLE_KEY")
                       if not os.environ.get(k, "").strip()]
            if missing:
                _log(f"portal: env not set: {missing}")
                _json(self, 503, {"error": "NOT_CONFIGURED",
                                  "message": "契約管理の準備がまだ整っていません"})
                return

            auth = (self.headers.get("Authorization") or "").strip()
            token = auth[len("Bearer "):].strip() if auth.lower().startswith("bearer ") else ""
            if not token:
                _json(self, 401, {"error": "NO_TOKEN", "message": "ログインしてください"})
                return
            user = user_from_token(token)
            if not user:
                _json(self, 401, {"error": "BAD_TOKEN",
                                  "message": "ログインし直してください"})
                return

            rows = _sb_call("GET",
                            f"/rest/v1/subscriptions?user_id=eq.{user['id']}&select=*")
            row = rows[0] if isinstance(rows, list) and rows else None
            customer = (row or {}).get("stripe_customer_id", "").strip()
            if not customer:
                # 先生発行の無料アカウント (行が無い) はここに来る
                _json(self, 404, {"error": "NO_SUBSCRIPTION",
                                  "message": "このアカウントに月額契約はありません"})
                return

            try:
                session = _stripe_post("billing_portal/sessions", [
                    ("customer", customer),
                    ("return_url", f"{_base_url(self)}/account.html"),
                ])
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                _log(f"portal: stripe HTTPError {e.code}: {detail[:500]}")
                _json(self, 502, {"error": "STRIPE_API_ERROR",
                                  "message": "契約管理ページを開けませんでした。しばらくして再度お試しください。"})
                return
            url = session.get("url")
            if not url:
                _json(self, 502, {"error": "NO_PORTAL_URL",
                                  "message": "契約管理ページのURLが取得できませんでした"})
                return
            _json(self, 200, {"portalUrl": url})
        except Exception as e:
            _log(f"portal internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR",
                              "message": "システムエラーが発生しました"})
