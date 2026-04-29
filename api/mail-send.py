"""Vercel Function: Resend API 直送 (juku-payment v3.1)

mailto 廃止 → サーバ側で Resend API 経由メール送信。BCC 漏れ事故防止 + Mac メモリ問題解消。

Endpoint (vercel.json で /payment/api/mail-send に rewrite):
  POST /payment/api/mail-send
  Headers: X-Admin-Password: <CHAT_ADMIN_PASSWORD>
  Body: {
    "subject": "件名",
    "body": "本文 (plain text)",
    "recipients": [
      { "email": "parent@example.com", "name": "田中太郎", "vars": {...} },
      ...
    ],
    "type": "broadcast" | "individual",   // ログ用
    "from_name": "塾名 (optional)",
    "reply_to": "塾長メアド (optional)"
  }

Response (200): {
  "sent": 18, "failed": 2,
  "results": [
    { "email": "...", "ok": true, "id": "resend_msg_id" },
    { "email": "...", "ok": false, "error": "..." }
  ]
}

Env:
  RESEND_API_KEY        Resend API key (re_xxx)
  FROM_EMAIL            送信元 (デフォルト 'noreply@trillion-ai-juku.com')
  CHAT_ADMIN_PASSWORD   admin 認証パスワード (chat と共有)
  KV_REST_API_URL       audit log 用 (省略可)
  KV_REST_API_TOKEN

依存: 標準ライブラリのみ。Resend SDK 不要。
"""

from http.server import BaseHTTPRequestHandler
import hmac
import json
import os
import re
import time
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


def _verify_admin(handler) -> bool:
    expected = os.environ.get("CHAT_ADMIN_PASSWORD", "").strip()
    if not expected:
        return False
    got = handler.headers.get("X-Admin-Password", "").strip()
    return hmac.compare_digest(got, expected) if got else False


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _sanitize_subject(s: str) -> str:
    """CRLF injection 防止"""
    return re.sub(r"[\r\n\t\x00-\x1F]", " ", str(s or "")).strip()[:200]


def _render_template(tpl: str, vars_dict: dict) -> str:
    def replace(m):
        key = m.group(1)
        return str(vars_dict.get(key, m.group(0)))
    return re.sub(r"\{\{(\w+)\}\}", replace, str(tpl or ""))


def _resend_send(api_key: str, from_email: str, to_email: str, reply_to: str,
                 subject: str, text: str) -> dict:
    """Resend API 1通送信"""
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": text,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _audit_log_kv(action: str, payload_summary: dict):
    """Vercel KV (Upstash) に audit log を append (best-effort)"""
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        return
    try:
        ts = int(time.time() * 1000)
        entry = {
            "ts": ts,
            "action": action,
            **payload_summary,
        }
        # ZADD audit:log score=ts member=entry_json
        cmd = ["ZADD", "audit:log", str(ts), json.dumps(entry, ensure_ascii=False)]
        req = urllib.request.Request(
            url,
            data=json.dumps(cmd).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass  # log 失敗は無視 (主機能を阻害しない)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED", "message": "管理者認証が必要です"})
                return

            api_key = os.environ.get("RESEND_API_KEY", "").strip()
            if not api_key:
                _json(self, 503, {
                    "error": "RESEND_API_KEY_NOT_SET",
                    "message": "Resend API キーが Vercel に設定されていません",
                    "hint": "Vercel Dashboard → Settings → Environment Variables → RESEND_API_KEY を追加してください。",
                })
                return

            content_len = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return

            subject_tpl = _sanitize_subject(payload.get("subject", ""))
            body_tpl = str(payload.get("body", "") or "")
            recipients = payload.get("recipients", [])
            mail_type = str(payload.get("type", "broadcast"))[:20]
            from_name = str(payload.get("from_name", "")).strip()[:80]
            reply_to = str(payload.get("reply_to", "")).strip()
            if reply_to and not EMAIL_RE.match(reply_to):
                reply_to = ""

            if not subject_tpl or not body_tpl or not recipients:
                _json(self, 400, {"error": "MISSING_FIELDS", "message": "subject/body/recipients は必須です"})
                return
            if len(recipients) > 500:
                _json(self, 400, {"error": "TOO_MANY", "message": "1リクエスト最大500名まで"})
                return

            from_email_raw = os.environ.get("FROM_EMAIL", "noreply@trillion-ai-juku.com").strip()
            if from_name:
                from_email = f"{from_name} <{from_email_raw}>" if "<" not in from_email_raw else from_email_raw
            else:
                from_email = from_email_raw

            results = []
            sent = 0
            failed = 0
            # 1 通ずつ送信 (BCC/CC は使わない = 漏洩事故防止)
            for r in recipients:
                email = str(r.get("email", "")).strip()
                name = str(r.get("name", "")).strip()
                vars_dict = r.get("vars") or {}
                if not EMAIL_RE.match(email):
                    results.append({"email": email, "name": name, "ok": False, "error": "invalid email"})
                    failed += 1
                    continue
                # テンプレ変数展開
                subj = _sanitize_subject(_render_template(subject_tpl, vars_dict))
                text = _render_template(body_tpl, vars_dict)
                try:
                    res = _resend_send(api_key, from_email, email, reply_to, subj, text)
                    results.append({"email": email, "name": name, "ok": True, "id": res.get("id", "")})
                    sent += 1
                except urllib.error.HTTPError as e:
                    detail = ""
                    try:
                        detail = e.read().decode("utf-8", errors="replace")[:200]
                    except Exception:
                        pass
                    results.append({"email": email, "name": name, "ok": False, "error": f"HTTP {e.code}: {detail}"})
                    failed += 1
                except Exception as e:
                    results.append({"email": email, "name": name, "ok": False, "error": str(e)[:200]})
                    failed += 1

            # Audit log
            _audit_log_kv(f"mail.send.{mail_type}", {
                "subject": subject_tpl[:100],
                "recipient_count": len(recipients),
                "sent": sent,
                "failed": failed,
            })

            _json(self, 200, {
                "sent": sent,
                "failed": failed,
                "results": results,
            })
        except Exception as e:
            _json(self, 500, {"error": "INTERNAL", "message": str(e)})

    def do_GET(self):
        _json(self, 405, {"error": "METHOD_NOT_ALLOWED", "message": "POST のみサポートします"})
