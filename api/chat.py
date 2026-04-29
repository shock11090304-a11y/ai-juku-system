"""Vercel Function: アプリ内チャット (juku-payment v2)

塾長 ↔ 生徒/保護者の 1:1 チャット。Upstash Redis (Vercel KV) で永続化。

Endpoints (vercel.json で /payment/api/chat に rewrite):
  GET  /payment/api/chat?action=threads&admin=1
       → CEO 側: 全スレッド一覧 (未読・最終時刻でソート)
  GET  /payment/api/chat?action=messages&thread={sid}&since={iso}&admin=1
       → メッセージ取得 (since 以降のみ差分)
  GET  /payment/api/chat?action=messages&thread={sid}&token={hmac}
       → 生徒/保護者側: 招待トークン認証
  POST /payment/api/chat
       Body: { action: 'send', thread, sender, body, token? }
       → メッセージ送信
  POST /payment/api/chat
       Body: { action: 'read', thread, reader }
       → 既読化 (sender_typeと反対側のunreadをリセット)
  POST /payment/api/chat
       Body: { action: 'invite', thread, student_name, expiry_days? }
       Auth: admin only
       → 招待トークン (HMAC) 生成

Env:
  KV_REST_API_URL        Upstash Redis REST URL (Vercel KV 自動付与)
  KV_REST_API_TOKEN      Upstash Redis REST token
  CHAT_SIGNING_SECRET    招待トークン署名用シークレット (32 byte 推奨)
  CHAT_ADMIN_PASSWORD    CEO 側アクセス用パスワード (簡易ガード)

Redis Keys:
  chat:thread:{sid}              ZSET (score=ts, member=msg_json)  全メッセージ履歴
  chat:thread:{sid}:meta         HASH {last_msg_at, last_msg_preview, student_name, unread_admin, unread_participant}
  chat:threads:index             ZSET (score=last_msg_ts, member=sid)  全スレッド lookup

依存: 標準ライブラリのみ (cryptography 不要、hmac/hashlib で署名)
"""

from http.server import BaseHTTPRequestHandler
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
import urllib.error


# ─────────────── Upstash Redis REST ヘルパ ───────────────

def _redis(*args, pipeline=False):
    """Upstash Redis REST API を呼ぶ。args = ['SET','key','value'] 形式。"""
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        raise RuntimeError("KV_REST_API_URL / KV_REST_API_TOKEN が設定されていません。Vercel Storage で Upstash Redis を Connect してください。")
    if pipeline:
        # args は コマンド配列の配列
        body = json.dumps(args).encode()
        req = urllib.request.Request(
            f"{url}/pipeline",
            data=body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
    else:
        body = json.dumps(list(args)).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data


# ─────────────── HMAC 招待トークン ───────────────

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    s = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _sign_invite(thread_id: str, expiry_ts: int) -> str:
    """{thread_id}.{exp}.{hmac} を生成"""
    secret = os.environ.get("CHAT_SIGNING_SECRET", "").encode()
    if not secret:
        raise RuntimeError("CHAT_SIGNING_SECRET 未設定")
    payload = f"{thread_id}.{expiry_ts}".encode()
    sig = hmac.new(secret, payload, hashlib.sha256).digest()
    return f"{thread_id}.{expiry_ts}.{_b64url(sig)}"


def _verify_invite(token: str) -> str:
    """成功なら thread_id を返す。失敗なら raise"""
    secret = os.environ.get("CHAT_SIGNING_SECRET", "").encode()
    if not secret:
        raise ValueError("CHAT_SIGNING_SECRET 未設定")
    try:
        thread_id, exp_str, sig_b64 = token.split(".")
        exp = int(exp_str)
    except Exception:
        raise ValueError("token format invalid")
    if exp < int(time.time()):
        raise ValueError("token expired")
    payload = f"{thread_id}.{exp}".encode()
    expected = hmac.new(secret, payload, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise ValueError("token signature invalid")
    return thread_id


def _verify_admin(handler) -> bool:
    """X-Admin-Password ヘッダ or ?admin_pw=... で認証"""
    expected = os.environ.get("CHAT_ADMIN_PASSWORD", "").strip()
    if not expected:
        return False
    got = handler.headers.get("X-Admin-Password", "").strip()
    if not got:
        # クエリ経由 (デバッグ用)
        qs = urllib.parse.urlparse(handler.path).query
        got = (urllib.parse.parse_qs(qs).get("admin_pw", [""])[0] or "").strip()
    return hmac.compare_digest(got, expected) if got else False


# ─────────────── レスポンスヘルパ ───────────────

def _json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


# ─────────────── ビジネスロジック ───────────────

def _post_message(thread_id: str, sender: str, body: str, student_name: str = ""):
    """メッセージ送信。Redis に追記 + メタ更新。"""
    if not body or not body.strip():
        raise ValueError("body empty")
    body = body.strip()[:2000]  # 上限 2000 chars
    if sender not in ("admin", "participant"):
        raise ValueError("invalid sender")
    ts = int(time.time() * 1000)  # ms
    msg_id = f"{ts}-{secrets.token_hex(4)}"
    msg = {
        "id": msg_id,
        "ts": ts,
        "sender": sender,
        "body": body,
    }
    msg_json = json.dumps(msg, ensure_ascii=False)
    thread_key = f"chat:thread:{thread_id}"
    meta_key = f"chat:thread:{thread_id}:meta"
    index_key = "chat:threads:index"
    preview = body[:60]
    other_unread_field = "unread_admin" if sender == "participant" else "unread_participant"
    pipeline = [
        ["ZADD", thread_key, str(ts), msg_json],
        ["EXPIRE", thread_key, "31536000"],  # 1年
        ["HSET", meta_key, "last_msg_at", str(ts), "last_msg_preview", preview, "last_sender", sender],
        ["HINCRBY", meta_key, other_unread_field, "1"],
        ["EXPIRE", meta_key, "31536000"],
        ["ZADD", index_key, str(ts), thread_id],
    ]
    if student_name:
        pipeline.append(["HSET", meta_key, "student_name", student_name])
    _redis(*pipeline, pipeline=True)
    return msg


def _list_messages(thread_id: str, since_ts: int = 0, limit: int = 200):
    """since_ts 以降のメッセージを取得 (古い順)"""
    thread_key = f"chat:thread:{thread_id}"
    # ZRANGEBYSCORE で since_ts より大きい score
    min_score = f"({since_ts}" if since_ts > 0 else "-inf"
    res = _redis("ZRANGEBYSCORE", thread_key, min_score, "+inf", "LIMIT", "0", str(limit))
    items = res.get("result", []) if isinstance(res, dict) else []
    msgs = []
    for raw in items:
        try:
            msgs.append(json.loads(raw))
        except Exception:
            continue
    return msgs


def _list_threads():
    """全スレッド一覧 (CEO 側用)"""
    res = _redis("ZREVRANGE", "chat:threads:index", "0", "200", "WITHSCORES")
    items = res.get("result", []) if isinstance(res, dict) else []
    threads = []
    # items = [sid, score, sid, score, ...]
    for i in range(0, len(items), 2):
        sid = items[i]
        last_ts = int(items[i + 1]) if i + 1 < len(items) else 0
        meta_res = _redis("HGETALL", f"chat:thread:{sid}:meta")
        meta_arr = meta_res.get("result", []) if isinstance(meta_res, dict) else []
        meta = dict(zip(meta_arr[::2], meta_arr[1::2])) if meta_arr else {}
        threads.append({
            "thread_id": sid,
            "student_name": meta.get("student_name", ""),
            "last_msg_at": int(meta.get("last_msg_at", last_ts) or last_ts),
            "last_msg_preview": meta.get("last_msg_preview", ""),
            "last_sender": meta.get("last_sender", ""),
            "unread_admin": int(meta.get("unread_admin", "0") or 0),
            "unread_participant": int(meta.get("unread_participant", "0") or 0),
        })
    return threads


def _mark_read(thread_id: str, reader: str):
    if reader not in ("admin", "participant"):
        raise ValueError("invalid reader")
    field = f"unread_{reader}"
    _redis("HSET", f"chat:thread:{thread_id}:meta", field, "0")


# ─────────────── HTTP Handler ───────────────

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = urllib.parse.urlparse(self.path).query
            params = {k: v[0] for k, v in urllib.parse.parse_qs(qs).items()}
            action = params.get("action", "")

            if action == "threads":
                if not _verify_admin(self):
                    _json(self, 401, {"error": "UNAUTHORIZED", "message": "管理者認証が必要です"})
                    return
                threads = _list_threads()
                _json(self, 200, {"threads": threads})
                return

            if action == "messages":
                thread = params.get("thread", "").strip()
                if not thread:
                    _json(self, 400, {"error": "MISSING_THREAD"})
                    return
                since = int(params.get("since", "0") or 0)
                # 認証: admin or 招待トークン
                if not _verify_admin(self):
                    token = params.get("token", "").strip()
                    if not token:
                        _json(self, 401, {"error": "UNAUTHORIZED"})
                        return
                    try:
                        verified = _verify_invite(token)
                    except ValueError as e:
                        _json(self, 401, {"error": "INVALID_TOKEN", "message": str(e)})
                        return
                    if verified != thread:
                        _json(self, 403, {"error": "FORBIDDEN", "message": "thread mismatch"})
                        return
                msgs = _list_messages(thread, since)
                # メタも返す
                meta_res = _redis("HGETALL", f"chat:thread:{thread}:meta")
                meta_arr = meta_res.get("result", []) if isinstance(meta_res, dict) else []
                meta = dict(zip(meta_arr[::2], meta_arr[1::2])) if meta_arr else {}
                _json(self, 200, {
                    "thread_id": thread,
                    "messages": msgs,
                    "next_since": msgs[-1]["ts"] if msgs else since,
                    "meta": {
                        "student_name": meta.get("student_name", ""),
                        "unread_admin": int(meta.get("unread_admin", "0") or 0),
                        "unread_participant": int(meta.get("unread_participant", "0") or 0),
                    },
                })
                return

            _json(self, 400, {"error": "INVALID_ACTION", "message": f"unknown action: {action!r}"})
        except RuntimeError as e:
            _json(self, 503, {"error": "SETUP_REQUIRED", "message": str(e)})
        except Exception as e:
            _json(self, 500, {"error": "INTERNAL", "message": str(e)})

    def do_POST(self):
        try:
            content_len = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return
            action = payload.get("action", "")

            if action == "send":
                thread = str(payload.get("thread", "")).strip()
                sender = payload.get("sender", "")
                body = payload.get("body", "")
                if not thread:
                    _json(self, 400, {"error": "MISSING_THREAD"})
                    return
                # 認証
                if sender == "admin":
                    if not _verify_admin(self):
                        _json(self, 401, {"error": "UNAUTHORIZED"})
                        return
                elif sender == "participant":
                    token = payload.get("token", "").strip()
                    if not token:
                        _json(self, 401, {"error": "UNAUTHORIZED"})
                        return
                    try:
                        verified = _verify_invite(token)
                    except ValueError as e:
                        _json(self, 401, {"error": "INVALID_TOKEN", "message": str(e)})
                        return
                    if verified != thread:
                        _json(self, 403, {"error": "FORBIDDEN"})
                        return
                else:
                    _json(self, 400, {"error": "INVALID_SENDER"})
                    return
                student_name = str(payload.get("student_name", "")).strip()
                msg = _post_message(thread, sender, body, student_name=student_name)
                _json(self, 200, {"message": msg})
                return

            if action == "read":
                thread = str(payload.get("thread", "")).strip()
                reader = payload.get("reader", "")
                if not thread:
                    _json(self, 400, {"error": "MISSING_THREAD"})
                    return
                # admin or participant (token)
                if reader == "admin":
                    if not _verify_admin(self):
                        _json(self, 401, {"error": "UNAUTHORIZED"})
                        return
                elif reader == "participant":
                    token = payload.get("token", "").strip()
                    try:
                        verified = _verify_invite(token)
                    except ValueError as e:
                        _json(self, 401, {"error": "INVALID_TOKEN"})
                        return
                    if verified != thread:
                        _json(self, 403, {"error": "FORBIDDEN"})
                        return
                else:
                    _json(self, 400, {"error": "INVALID_READER"})
                    return
                _mark_read(thread, reader)
                _json(self, 200, {"ok": True})
                return

            if action == "invite":
                if not _verify_admin(self):
                    _json(self, 401, {"error": "UNAUTHORIZED"})
                    return
                thread = str(payload.get("thread", "")).strip()
                if not thread:
                    _json(self, 400, {"error": "MISSING_THREAD"})
                    return
                student_name = str(payload.get("student_name", "")).strip()
                expiry_days = int(payload.get("expiry_days", 365))
                exp = int(time.time()) + expiry_days * 86400
                token = _sign_invite(thread, exp)
                # メタにも student_name 保存しておく
                if student_name:
                    _redis("HSET", f"chat:thread:{thread}:meta", "student_name", student_name)
                _json(self, 200, {
                    "token": token,
                    "expires_at": exp,
                    "thread_id": thread,
                })
                return

            _json(self, 400, {"error": "INVALID_ACTION"})
        except RuntimeError as e:
            _json(self, 503, {"error": "SETUP_REQUIRED", "message": str(e)})
        except ValueError as e:
            _json(self, 400, {"error": "VALIDATION", "message": str(e)})
        except Exception as e:
            _json(self, 500, {"error": "INTERNAL", "message": str(e)})
