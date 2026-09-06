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
