"""Vercel Function: 月謝のカード変更リンク (登録はそのまま・カードだけ差し替える) — 2026-10-20

Endpoint: POST /payment/api/admin-card-update
  (vercel.json の rewrites で /api/admin-card-update に流れる)

塾長専用 (X-Admin-Password = CHAT_ADMIN_PASSWORD)。保護者から「カードを変えたい」と言われたら、月謝アプリの
「🪪 カード変更」からこの API でリンク (Stripe Checkout・mode=setup・その登録の Stripe 顧客) を作り、LINE で送る。
保護者が新しいカードを入れると、webhook (stripe-webhook.py `_handle_card_update_checkout`) が
同じ reg:completed:{rid} の stripe_payment_method_id を新しいカードに差し替える (rid・月額・台帳・名簿の紐付けはそのまま)。

なぜ必要か (2026-10-20 塾長の質問「塾の支払いの Stripe のカード情報の変更はどうすればいい？」):
  月末一斉・個別・再請求は KV の stripe_payment_method_id を名指しで使うので、Stripe の画面でカードを替えても効かない。
  それまでの回り道 (🗑 退塾処理 → register.html で再登録 → 紐付け直し) は rid が新しくなり、引き落とし済みの台帳
  (charge:done / charge:history は rid 単位) が引き継がれず、前のカードで払った月が「未請求」に見えた (二重取りの穴)。

Body (JSON):
  {"action": "create_link" | "status", "registrationId": "reg_xxx", "expectCustomerId": "cus_xxx" (任意・名簿の紐付けと照合),
   "replace": true (create_link だけ・まだ使えるリンクがあっても作り直す。無ければ 409 LINK_ACTIVE で今のリンクを返す)}

Response (200):
  create_link: {"ok": true, "url": "https://checkout.stripe.com/...", "expiresAt": 1789000000, "sessionId": "cs_...",
                "studentName": "...", "expiredPrevious": true|false}
  status:      {"ok": true, "studentName": "...", "card": {"brand", "last4", "exp", "updatedAt"} | null,
                "link": {"url", "createdAt", "expiresAt"} | null}
               (画面がダイアログを開いたときに呼ぶ。送ったリンクがまだ使える = 保護者がまだ入力していない、を出して
                作り直しによる失効を防ぐ。カード変更は webhook がリンクの記録を消すので、残っていれば未入力)

設計の要点:
  - metadata.system = "juku-payment-card-update"。本体 (Railway) の webhook は juku-payment 前方一致で skip する。
  - rid は metadata.card_update_rid に入れる。★registration_id には入れない: webhook の従来の分岐は registration_id が
    あると「新規のカード登録」とみなして reg:completed を作り直す (月額 0 円の別物で上書きされる) ので、
    デプロイの順序や分岐漏れがあっても事故にならないよう、鍵の名前を変えている。
  - 新しいリンクを作ってから、前に出したリンクがまだ開いていれば失効させる (同じ生徒で使えるリンクは常に 1 本)。
  - KV `card_update:link:{rid}` に最新のリンクを 2 日残す (表示・調査用。webhook はこれに頼らない)。
  - 登録・台帳・名簿には一切書かない。保護者が入力を終えるまで何も変わらない (リンクを捨てても害はない)。
  - 断る登録: 旧方式のサブスク (checkout_mode≠setup・Stripe が自動課金するので KV のカードは使われない)、
    Stripe 顧客 ID の無い登録、一覧から外れた登録 (reg:zombie = Stripe に顧客/カードが無かった → 登録し直し)。

テスト: scripts/health_check/test_card_update_link.py
認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)
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


CARD_UPDATE_SYSTEM_TAG = "juku-payment-card-update"   # stripe-webhook.py と同じ値 (本体の webhook は juku-payment 前方一致で skip)
LINK_RECORD_TTL = 2 * 86400                           # Checkout の既定の有効期限 (24 時間) より長く残す
PUBLIC_BASE_DEFAULT = "https://trillion-ai-juku.com"  # apex が正 (www は 308)。戻り先の完了ページ (payment/card-update-complete.html)
REREGISTER_STEPS = ("🗑 で今の登録を外してから、カードの登録ページ https://trillion-ai-juku.com/payment/register.html を保護者に送り、"
                    "登録できたら「👥 全生徒」でこの生徒に ✓確定")


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
#   ★11 本の関数に同じ塊を置いている (Vercel の Python 関数は 1 ファイル 1 関数で共有モジュールを持たない)。
#     直すときは全部一緒に直すこと。scripts/health_check/test_vercel_admin_guard.py が 11 本とも検査する。
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


def _stripe_post(secret_key, path, form, idempotency_key=None):
    """Stripe POST (空の form でも Content-Length: 0 を明示。admin-registration-cancel.py と同じ形)"""
    body = urllib.parse.urlencode(form).encode() if form else b""
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
        "Content-Length": str(len(body)),
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(f"https://api.stripe.com/v1/{path}", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _stripe_error_message(e):
    """HTTPError の本文から Stripe のエラー (code, message) を取り出す"""
    try:
        raw = e.read().decode("utf-8", errors="replace")
    except Exception:
        raw = ""
    try:
        err = json.loads(raw).get("error", {}) or {}
        return str(err.get("code") or ""), str(err.get("message") or raw)[:300]
    except Exception:
        return "", raw[:300]


def _kv_json(key):
    """(ok, value): ok=False は KV の応答なし。value はキーが無ければ None、壊れた JSON は {}"""
    got = _redis("GET", key)
    if not got or not isinstance(got, dict):
        return False, None
    raw = got.get("result")
    if not raw:
        return True, None
    try:
        v = json.loads(raw)
        return True, (v if isinstance(v, dict) else {})
    except Exception:
        return True, {}


def _submit_message(student):
    """決済画面のボタンの下に出す文。★「本日の課金はありません」とは書かない: 引き落としに失敗した月を、塾長がカード変更の直後に
    新しいカードで取り直すことがある (同じ日に引き落とされる)。どちらの場合も正しい言い方にする"""
    who = f"{student}さんの" if student else ""
    return (f"{who}月謝のお支払いカードを、ここで入力するカードに変更します。カードを入力しただけでは料金はかかりません。"
            "これからの月謝は新しいカードで引き落とし、前のカードは使わなくなります。")


def _create_link(secret_key, rid, rec, base_url):
    """Checkout Session (mode=setup・既存の顧客) を作る。metadata は Session と SetupIntent の両方に載せる"""
    student = str(rec.get("studentName") or rec.get("student_name") or "").strip()
    metadata = {
        "system": CARD_UPDATE_SYSTEM_TAG,
        "purpose": "card_update",
        "card_update_rid": rid[:60],          # ★registration_id にしない (モジュール docstring)
        "student_name": student[:80],
        "source": "admin-card-update",
    }
    form = [
        ("mode", "setup"),
        ("payment_method_types[]", "card"),
        ("customer", rec.get("stripe_customer_id", "")),
        ("locale", "ja"),
        ("success_url", f"{base_url}/payment/card-update-complete.html"),
        ("cancel_url", f"{base_url}/payment/card-update-complete.html?canceled=1"),
        ("custom_text[submit][message]", _submit_message(student)[:1000]),
        ("setup_intent_data[description]", f"月謝のお支払いカード変更 — 生徒: {student}"[:200]),
    ]
    for k, v in metadata.items():
        form.append((f"metadata[{k}]", v))
        form.append((f"setup_intent_data[metadata][{k}]", v))
    return _stripe_post(secret_key, "checkout/sessions", form)


def _expire_session(secret_key, session_id):
    """まだ開いているリンクを失効させる。完了済み・失効済みは Stripe が 400 を返すので、それは「もう使えない」とみなす"""
    if not session_id:
        return False
    try:
        _stripe_post(secret_key, f"checkout/sessions/{session_id}/expire", [])
        return True
    except urllib.error.HTTPError as e:
        code, msg = _stripe_error_message(e)
        _log(f"card-update: expire previous {session_id} skipped ({e.code} {code}: {msg[:120]})")
        return False
    except Exception as e:
        _log(f"card-update: expire previous {session_id} error: {e!r}")
        return False


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED", "message": "管理パスワードが違います。入れ直してください (何度も間違えると 1 時間使えなくなります)。"})
                return
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                payload = None
            if not isinstance(payload, dict):
                _json(self, 400, {"error": "INVALID_JSON", "message": "送られた内容が読めません。画面を再読み込みしてから、もう一度押してください。"})
                return
            action = str(payload.get("action") or "").strip()
            if action not in ("create_link", "status"):
                _json(self, 400, {"error": "UNKNOWN_ACTION", "message": "action は create_link / status だけです。"})
                return
            rid = str(payload.get("registrationId") or "").strip()
            if not rid or len(rid) > 60 or not all(ch.isascii() and (ch.isalnum() or ch in "_-") for ch in rid):
                _json(self, 400, {"error": "MISSING_REG_ID", "message": "カード登録 (registrationId) が指定されていません。"})
                return
            expect_customer_id = str(payload.get("expectCustomerId") or "").strip()

            secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            if not secret_key and action == "create_link":
                _json(self, 503, {"error": "STRIPE_NOT_CONFIGURED", "message": "Stripe のキーが未設定です (Vercel の環境変数 STRIPE_SECRET_KEY)。"})
                return

            ok, rec = _kv_json(f"reg:completed:{rid}")
            if not ok:
                _json(self, 503, {"error": "KV_UNAVAILABLE", "message": "保存先 (KV) が応答しません。少し待ってからもう一度押してください。"})
                return
            if rec is None:
                _json(self, 404, {"error": "REGISTRATION_NOT_FOUND",
                                  "message": "この生徒のカード登録が見つかりません (退塾処理で外したか、まだ登録されていません)。カードの登録から必要です。"})
                return
            if not rec:
                _json(self, 500, {"error": "PARSE_ERROR", "message": "登録データが読めません。"})
                return
            student = str(rec.get("studentName") or rec.get("student_name") or "").strip()
            customer_id = str(rec.get("stripe_customer_id") or "").strip()
            if str(rec.get("checkout_mode") or "") != "setup":
                _json(self, 409, {"error": "NOT_SETUP_MODE",
                                  "message": f"{student} さんは旧方式の登録 (Stripe の定期課金) のため、このリンクではカードを変えられません。Claude に相談してください。"})
                return
            if not customer_id:
                _json(self, 409, {"error": "NO_CUSTOMER",
                                  "message": f"{student} さんの登録に Stripe の顧客がありません。カードの登録し直しが必要です"
                                             f" ({REREGISTER_STEPS})。"})
                return
            if expect_customer_id and expect_customer_id != customer_id:
                _json(self, 409, {"error": "CUSTOMER_MISMATCH",
                                  "message": "名簿の紐付けと登録の Stripe 顧客が一致しません。重複登録の可能性があるので、紐付けを確認してください。"})
                return
            zok, zombie = _kv_json(f"reg:zombie:{rid}")
            if zok and zombie is not None:
                _json(self, 409, {"error": "ZOMBIE_REGISTRATION",
                                  "message": f"{student} さんの登録は、Stripe に顧客かカードが見つからず一覧から外れています。カードの登録し直しが必要です"
                                             f" ({REREGISTER_STEPS})。"})
                return

            now = int(time.time())
            pok, prev = _kv_json(f"card_update:link:{rid}")
            if not pok:
                _json(self, 503, {"error": "KV_UNAVAILABLE", "message": "保存先 (KV) が応答しません。少し待ってからもう一度押してください。"})
                return
            prev_active = bool(prev and prev.get("session_id") and int(prev.get("expires_at") or 0) > now)

            if action == "status":
                card = None
                if rec.get("card_last4"):
                    card = {"brand": rec.get("card_brand", ""), "last4": rec.get("card_last4", ""), "exp": rec.get("card_exp", ""),
                            "updatedAt": int(rec.get("card_updated_at") or 0)}
                link = None
                if prev_active and prev.get("url"):
                    link = {"url": prev.get("url"), "createdAt": int(prev.get("created_at") or 0), "expiresAt": int(prev.get("expires_at") or 0)}
                _json(self, 200, {"ok": True, "studentName": student, "card": card, "link": link})
                return

            # まだ使えるリンクがあるのに作り直すと、保護者に送ったリンクが使えなくなる。画面で確認したとき (replace: true) だけ作り直す
            if prev_active and payload.get("replace") is not True:
                link = {"url": prev.get("url") or "", "createdAt": int(prev.get("created_at") or 0), "expiresAt": int(prev.get("expires_at") or 0)}
                _json(self, 409, {"error": "LINK_ACTIVE", "link": link, "studentName": student,
                                  "message": "前に作ったリンクがまだ使えます (保護者はまだ入力していません)。新しく作らずに、その文面を送り直してください。"})
                return

            base_url = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/") or PUBLIC_BASE_DEFAULT
            try:
                session = _create_link(secret_key, rid, rec, base_url)
            except urllib.error.HTTPError as e:
                code, msg = _stripe_error_message(e)
                _log(f"card-update: create session failed rid={rid} {e.code} {code}: {msg}")
                if code == "resource_missing" or "no such customer" in msg.lower():
                    _json(self, 502, {"error": "CUSTOMER_MISSING",
                                      "message": f"Stripe に {student} さんの顧客が見つかりません (削除済み)。カードの登録し直しが必要です"
                                                 f" ({REREGISTER_STEPS})。"})
                else:
                    _json(self, 502, {"error": "STRIPE_ERROR", "message": f"Stripe でリンクを作れませんでした: {msg[:160]}"})
                return
            url = session.get("url") or ""
            session_id = session.get("id") or ""
            if not url or not session_id:
                _json(self, 502, {"error": "STRIPE_ERROR", "message": "Stripe からリンクが返ってきませんでした。もう一度押してください。"})
                return
            expires_at = int(session.get("expires_at") or (now + 86400))

            # 前に出したリンク: 新しいリンクを作れてから失効させる (作るのに失敗したときは前のリンクが生きたまま)
            prev_sid = str((prev or {}).get("session_id") or "")
            expired_previous = False
            if prev_active and prev_sid != session_id:
                expired_previous = _expire_session(secret_key, prev_sid)
            # url も残す: ダイアログを開き直したときに同じリンクをもう一度コピーできる (作り直して前のリンクを殺さずに済む)。KV は非公開
            _redis("SET", f"card_update:link:{rid}", json.dumps({
                "session_id": session_id, "url": url, "created_at": now, "expires_at": expires_at,
                "customer_id": customer_id, "student_name": student,
            }, ensure_ascii=False), "EX", str(LINK_RECORD_TTL))
            _log(f"card-update: link created rid={rid} session={session_id} customer={customer_id} expired_previous={expired_previous}")
            _json(self, 200, {"ok": True, "url": url, "sessionId": session_id, "expiresAt": expires_at,
                              "studentName": student, "expiredPrevious": expired_previous})
        except Exception as e:
            _log(f"admin-card-update internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": "内部エラーです。もう一度押してください。続くときは Claude に相談してください。"})
