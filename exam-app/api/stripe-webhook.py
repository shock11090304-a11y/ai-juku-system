"""神テスト サブスクの Stripe Webhook 受信。

Endpoint: POST /api/stripe-webhook   (kamitest の Vercel プロジェクト)

Stripe Dashboard 設定 (docs/book-exam.md §22):
  Developers → Webhooks → Add endpoint
    URL:    https://exam.trillion-ai-juku.com/api/stripe-webhook
    Events: checkout.session.completed
            customer.subscription.created
            customer.subscription.updated
            customer.subscription.deleted

やること:
  支払い完了   → アカウントの ban を解除 (checkout.py が ban 付きで作っている)
  状態の変化   → subscriptions 行を上書き (trialing/active/past_due は利用可のまま)
  解約・不払い → アカウントを ban (支払い済み期間の終わりに Stripe が deleted を送る)

★ AI塾 (月謝) と同じ Stripe アカウントを共有する前提。metadata.system が
  "kamitest-subscription" のイベント **だけ** を処理する (AI塾側の webhook も
  同様に自分のイベントだけ処理するので、互いに素通りし合う)。
★ 処理は全部冪等 (upsert + ban/unban は絶対値)。失敗したら 500 を返して
  Stripe に再送させる (黙って 200 を返すと「解約したのに使える」が残る)。

Env:
  STRIPE_WEBHOOK_SECRET      whsec_... (このエンドポイント固有)
  SUPABASE_URL               https://<ref>.supabase.co
  SUPABASE_SERVICE_ROLE_KEY  ban/解除と行の upsert に必要

検査: python3 scripts/book_exam/check_signup.py (署名・冪等・素通りを機械で確認)
"""

from http.server import BaseHTTPRequestHandler
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone


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


SYSTEM_TAG = "kamitest-subscription"
BAN_10Y = "87600h"
UNBAN_STATUSES = {"trialing", "active", "past_due"}   # past_due は Stripe の再請求中 = 使える
BAN_STATUSES = {"canceled", "unpaid", "incomplete_expired"}
DB_STATUSES = {"incomplete", "incomplete_expired", "trialing", "active",
               "past_due", "canceled", "unpaid", "paused"}


def _verify_signature(raw_payload: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
    """Stripe-Signature: t=1234,v1=hex,... を timing-safe に検証 (api/stripe-webhook.py と同じ)。"""
    if not sig_header or not secret:
        return False
    try:
        items = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
    except Exception:
        return False
    timestamp = items.get("t")
    if not timestamp:
        return False
    sigs = []
    for part in sig_header.split(","):
        k, _, v = part.partition("=")
        if k == "v1":
            sigs.append(v)
    if not sigs:
        return False
    try:
        ts_int = int(timestamp)
    except Exception:
        return False
    if abs(int(time.time()) - ts_int) > tolerance:
        return False
    signed = f"{timestamp}.".encode() + raw_payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


# ─────────────── Supabase (service_role) ───────────────

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


def set_ban(user_id, banned):
    res = _sb_call("PUT", f"/auth/v1/admin/users/{user_id}",
                   {"ban_duration": BAN_10Y if banned else "none"})
    if not res.get("id"):
        raise RuntimeError(f"ban 更新が空応答 (user={user_id})")
    _log(f"webhook: {'ban' if banned else 'unban'} user={user_id}")


def upsert_row(fields):
    """subscriptions を user_id で upsert。★返却行数で成否を判定する
    (0 行なのに成功と言うのが一番危ない)。"""
    rows = _sb_call("POST", "/rest/v1/subscriptions?on_conflict=user_id", [fields],
                    {"Prefer": "resolution=merge-duplicates,return=representation"})
    if not (isinstance(rows, list) and len(rows) == 1):
        raise RuntimeError(f"subscriptions upsert が {rows!r} を返した (1 行のはず)")
    return rows[0]


def get_row(user_id):
    rows = _sb_call("GET", f"/rest/v1/subscriptions?user_id=eq.{user_id}&select=*")
    return rows[0] if isinstance(rows, list) and rows else None


# ─────────────── イベント処理 ───────────────

def _meta(obj):
    return obj.get("metadata") or {}


def _is_ours(obj):
    return _meta(obj).get("system", "") == SYSTEM_TAG


def _uid(obj):
    return (_meta(obj).get("supabase_user_id") or "").strip()


def _period_end_iso(sub):
    """subscription の期末。古い API 版は直下、2025 春以降の版は items の中にある。"""
    v = sub.get("current_period_end")
    if not v:
        items = ((sub.get("items") or {}).get("data")) or []
        if items and isinstance(items[0], dict):
            v = items[0].get("current_period_end")
    if isinstance(v, (int, float)) and v > 0:
        return datetime.fromtimestamp(int(v), tz=timezone.utc).isoformat()
    return None


def on_checkout_completed(event):
    obj = event.get("data", {}).get("object", {})
    if not _is_ours(obj):
        _log("webhook: checkout.completed skipped (not kamitest)")
        return
    uid = _uid(obj)
    if not uid:
        _log("webhook: checkout.completed without supabase_user_id — skip")
        return
    meta = _meta(obj)
    email = ((obj.get("customer_details") or {}).get("email")
             or meta.get("email") or "")
    fields = {"user_id": uid, "email": email,
              "student_name": meta.get("student_name", ""),
              "grade": meta.get("grade", ""),
              "school": meta.get("school", "")}
    if obj.get("customer"):
        fields["stripe_customer_id"] = obj["customer"]
    if obj.get("subscription"):
        fields["stripe_subscription_id"] = obj["subscription"]
    upsert_row(fields)
    # 支払い (または体験開始) が確定したのでログインできるようにする
    set_ban(uid, banned=False)
    _log(f"webhook: checkout completed user={uid} sub={obj.get('subscription')}")


def on_subscription_event(event):
    """customer.subscription.created / updated / deleted を 1 本で処理する。"""
    obj = event.get("data", {}).get("object", {})
    if not _is_ours(obj):
        _log(f"webhook: {event.get('type')} skipped (not kamitest)")
        return
    uid = _uid(obj)
    if not uid:
        _log(f"webhook: {event.get('type')} without supabase_user_id — skip")
        return

    deleted = event.get("type") == "customer.subscription.deleted"
    status = "canceled" if deleted else (obj.get("status") or "")
    if status not in DB_STATUSES:
        _log(f"webhook: unknown status '{status}' — skip (Stripe の新語彙?)")
        return
    sub_id = obj.get("id", "")

    row = get_row(uid)
    # ★遅延再送ガード: 解約で終わった契約 (canceled) が、同じ subscription の
    #   古い active/trialing イベントの再送で復活してはいけない。Stripe 上で
    #   canceled は終端で、再開は必ず新しい subscription id になる。
    if (row and row.get("status") == "canceled"
            and (row.get("stripe_subscription_id") or "") == sub_id
            and status in UNBAN_STATUSES):
        _log(f"webhook: stale event for canceled sub={sub_id} — skip")
        return

    # ★ email は upsert に**毎回**入れる。Postgres の INSERT … ON CONFLICT は既存行の
    #   更新でも挿入側の NOT NULL 検査を先に通すため、email (default 無し) を省くと
    #   400 Bad Request になる (実測 2026-08-16: subscription 系イベントだけ 500 で
    #   「お支払い手続き中」のまま止まった)。値は metadata → 既存行 → '' の順で選ぶ。
    fields = {"user_id": uid, "status": status, "stripe_subscription_id": sub_id,
              "email": (_meta(obj).get("email", "")
                        or (row or {}).get("email") or "")}
    if obj.get("customer"):
        fields["stripe_customer_id"] = obj["customer"]
    pe = _period_end_iso(obj)
    if pe:
        fields["current_period_end"] = pe
    if not row:                                   # 行が無い = checkout より先に届いた
        fields["student_name"] = _meta(obj).get("student_name", "")
        fields["grade"] = _meta(obj).get("grade", "")
        fields["school"] = _meta(obj).get("school", "")
    upsert_row(fields)

    if status in UNBAN_STATUSES:
        set_ban(uid, banned=False)
    elif status in BAN_STATUSES:
        set_ban(uid, banned=True)
    # incomplete / paused は auth に触らない (支払い前 or 一時停止中の中間状態)
    _log(f"webhook: {event.get('type')} user={uid} status={status}")


HANDLERS = {
    "checkout.session.completed": on_checkout_completed,
    "customer.subscription.created": on_subscription_event,
    "customer.subscription.updated": on_subscription_event,
    "customer.subscription.deleted": on_subscription_event,
}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
            if not secret:
                _log("webhook: STRIPE_WEBHOOK_SECRET not set")
                _json(self, 503, {"error": "WEBHOOK_SECRET_NOT_SET"})
                return
            if not _verify_signature(raw, self.headers.get("Stripe-Signature", ""), secret):
                _log("webhook: signature verification failed")
                _json(self, 401, {"error": "INVALID_SIGNATURE"})
                return

            try:
                event = json.loads(raw.decode("utf-8"))
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return

            fn = HANDLERS.get(event.get("type", ""))
            if fn:
                try:
                    fn(event)
                except Exception as e:
                    # ★500 で返して Stripe に再送させる。処理は冪等なので再送は安全。
                    #   (200 で握り潰すと「解約したのにログインできる」が永久に残る)
                    _log(f"webhook handler error ({event.get('type')}): {e!r}")
                    _json(self, 500, {"error": "HANDLER_FAILED"})
                    return
            else:
                _log(f"webhook: ignored event type {event.get('type')}")
            _json(self, 200, {"received": True})
        except Exception as e:
            _log(f"webhook internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR"})
