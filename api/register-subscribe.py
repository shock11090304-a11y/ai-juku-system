"""Vercel Function: 月謝カード払い 自己登録 → Stripe Checkout Session (Setup Mode) 生成

🆕 v2 (2026-05-13): mode=subscription → mode=setup に変更。
カード登録時の即時引き落としを廃止し、月末バッチで一斉引き落とす運用に切替。
塾長指示「カード登録した瞬間に引き落としが確定するのは困る・月末に一斉に」(2026-05-13)。

Endpoint: POST /payment/api/register-subscribe
  (vercel.json の rewrites で /api/register-subscribe に流れる)

Body (JSON):
  {
    "studentName": "山田 太郎",
    "grade": "高校2年",
    "parentName": "山田 花子",
    "email": "yamada@example.com",
    "phone": "090-1234-5678",
    "courses": ["kou2-grammar", "eiken-jun1"],
    "options": ["facility-1500"]
  }

Env:
  STRIPE_SECRET_KEY    Stripe Dashboard → Developers → API keys → Secret key
  KV_REST_API_URL      Upstash Redis REST URL (Vercel KV 自動付与)
  KV_REST_API_TOKEN    Upstash Redis REST token
  PUBLIC_BASE_URL      (任意) https://www.trillion-ai-juku.com 既定値

Response (200):
  { "checkoutUrl": "https://checkout.stripe.com/...", "amount": 33500, "registrationId": "reg_..." }
  ※ amount は「月額予定」として保存するだけで即課金されない (setup mode)
Response (400): バリデーションエラー
Response (503): STRIPE_SECRET_KEY 未設定
Response (502): Stripe API エラー

🚨 AIコーチングとの分離強化:
  全 Stripe Object に metadata.system="juku-payment-monthly" を付与し、ai-juku webhook 側で skip 可能。
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path


def _log(msg):
    """server-side log only (stdout → Vercel logs). Never returned to client."""
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


# ─────────────── コースカタログ (server-side single source of truth) ───────────────
# courses.json と同期。価格改定時はこちらも更新すること。
COURSES = {
    "ronin":         {"name": "浪人生",        "price": 30000},
    "kokuritsu":     {"name": "国公立難関大学", "price": 25000},
    "kanri":         {"name": "学習管理",      "price": 22500},
    "kanri-monitor": {"name": "学習管理モニター", "price": 16500},
    "gmarch":        {"name": "GMARCH",     "price": 12500},
    "soukei":        {"name": "早慶クラス",     "price": 12500},
    "eiken-jun1":    {"name": "英検準１級",     "price": 8500},
    "chu2":          {"name": "中学2年",       "price": 7500},
    "chu1":          {"name": "中学基礎中学1年", "price": 7500},
    "chu3-monday":   {"name": "月曜中３英文法",   "price": 7500},
    "grammar-1":     {"name": "英文法レベル１",   "price": 7500},
    "grammar-2":     {"name": "英文法レベル２",   "price": 7500},
    "kaishaku":      {"name": "英文解釈",       "price": 7500},
    "eiken-jun2":    {"name": "英検準２級",     "price": 7500},
    "eiken-2":       {"name": "英検２級",      "price": 7500},
    "long-1":        {"name": "英語長文レベル１", "price": 7500},
    "long-2":        {"name": "英語長文レベル２", "price": 7500},
    "kou2-grammar":  {"name": "高校2年英文法",   "price": 7500},
}
OPTIONS = {
    "facility-1500": {"name": "設備費 (¥1,500)", "price": 1500},
    "facility-1350": {"name": "設備費 (¥1,350)", "price": 1350},
}


# ─────────────── Upstash Redis (オプション、未設定なら skip) ───────────────

def _redis_safe(*args):
    """KV が未設定でも fail しない (登録自体は Stripe 側で記録される)"""
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        return None
    try:
        body = json.dumps(list(args)).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"redis error: {e}")
        return None


# ─────────────── Rate Limiting ───────────────

def _client_ip(handler):
    fwd = handler.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return handler.client_address[0] if handler.client_address else "unknown"


def _rl_check(ip, email):
    """IP: 10/5min, email: 3/1hour. KV 未設定時は通過 (fail-open)。"""
    # IP-based
    ip_key = f"rl:reg:ip:{ip}"
    res = _redis_safe("INCR", ip_key)
    if res and isinstance(res, dict):
        n = res.get("result", 0)
        if n == 1:
            _redis_safe("EXPIRE", ip_key, "300")
        if n > 10:
            return False, "登録試行が多すぎます。5分後に再度お試しください。"
    # email-based (lower-case for normalization)
    email_norm = (email or "").strip().lower()
    if email_norm:
        e_key = f"rl:reg:email:{email_norm}"
        res = _redis_safe("INCR", e_key)
        if res and isinstance(res, dict):
            n = res.get("result", 0)
            if n == 1:
                _redis_safe("EXPIRE", e_key, "3600")
            if n > 3:
                return False, "同じメールアドレスでの登録試行が多すぎます。1時間後に再度お試しください。"
    return True, None


# ─────────────── バリデーション ───────────────

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
GRADE_OPTIONS = {"中学1年", "中学2年", "中学3年", "高校1年", "高校2年", "高校3年", "浪人", "その他"}


def _validate(payload):
    errs = []
    student_name = (payload.get("studentName") or "").strip()
    grade = (payload.get("grade") or "").strip()
    parent_name = (payload.get("parentName") or "").strip()
    email = (payload.get("email") or "").strip()
    phone = (payload.get("phone") or "").strip()
    courses = payload.get("courses") or []
    options = payload.get("options") or []

    if not student_name or len(student_name) > 80:
        errs.append("生徒氏名が不正です")
    if grade not in GRADE_OPTIONS:
        errs.append("学年が不正です")
    if not parent_name or len(parent_name) > 80:
        errs.append("保護者氏名が不正です")
    if not email or not EMAIL_RE.match(email) or len(email) > 200:
        errs.append("メールアドレスが不正です")
    if phone and len(phone) > 30:
        errs.append("電話番号が長すぎます")
    if not isinstance(courses, list) or not courses:
        errs.append("受講コースを1つ以上選択してください")
    invalid_courses = [c for c in courses if c not in COURSES]
    if invalid_courses:
        errs.append(f"不明なコースID: {invalid_courses}")
    if not isinstance(options, list):
        errs.append("オプションが不正です")
    invalid_options = [o for o in options if o not in OPTIONS]
    if invalid_options:
        errs.append(f"不明なオプションID: {invalid_options}")
    facility_opts = [o for o in options if o.startswith("facility-")]
    if len(facility_opts) > 1:
        errs.append("設備費は1つだけ選択可能です")

    return errs, {
        "studentName": student_name,
        "grade": grade,
        "parentName": parent_name,
        "email": email,
        "phone": phone,
        "courses": list(dict.fromkeys(courses)),
        "options": list(dict.fromkeys(options)),
    }


def _calculate_fee(courses, options):
    total = 0
    breakdown = []
    for c in courses:
        info = COURSES.get(c)
        if info:
            total += info["price"]
            breakdown.append(f"{info['name']} ¥{info['price']:,}")
    for o in options:
        info = OPTIONS.get(o)
        if info:
            total += info["price"]
            breakdown.append(f"{info['name']} ¥{info['price']:,}")
    return total, breakdown


# ─────────────── Stripe Checkout Session ───────────────

def _stripe_post(secret_key, path, form, idempotency_key=None):
    """Stripe POST API helper"""
    body = urllib.parse.urlencode(form).encode()
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(
        f"https://api.stripe.com/v1/{path}",
        data=body,
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _create_or_find_customer(secret_key, payload, registration_id, metadata):
    """🆕 v2 (CRITICAL fix 2026-05-13): Customer を明示的に先行作成。
    mode=setup の Customer 自動作成挙動に依存せず、確実に customer_id を確保する。
    Idempotency-Key に registration_id を含めるので 1 registration につき 1 Customer のみ作成される。
    """
    student = payload["studentName"]
    parent = payload["parentName"]
    form = [
        ("email", payload["email"]),
        ("name", f"{parent} (生徒: {student})"[:240]),
        ("phone", payload.get("phone", "") or ""),
        ("description", f"AIコーチング 月謝 — 保護者: {parent} / 生徒: {student} ({payload.get('grade', '')})"[:240]),
    ]
    for k, v in metadata.items():
        if v is None: continue
        form.append((f"metadata[{k}]", str(v)))
    # 同じ registration_id で再叩きされても 1 customer のみ作成
    idempotency = f"juku-customer-{registration_id}"
    return _stripe_post(secret_key, "customers", form, idempotency_key=idempotency)


def _create_checkout_session(secret_key, payload, fee, breakdown, registration_id, base_url):
    """🆕 v2 (2026-05-13 CRITICAL fix): mode=setup でカード保存のみ (即課金なし)。

    変更点:
      - Customer を明示的に先行作成 (mode=setup の自動作成に頼らない・全件 skip 事故防止)
      - SetupIntent で card を保存 → 自動的に customer に attach
      - 月末バッチで一斉引き落とし
    """
    student = payload["studentName"]
    desc_detail = " / ".join(breakdown)[:240]

    # Stripe metadata は各 value 500 字制限。安全側で 240 でtruncate
    def _cap(s, n=240):
        return (str(s) or "")[:n]
    # 🆕 AIコーチングとの完全分離: system=juku-payment-monthly を必ず付与
    metadata = {
        "registration_id": _cap(registration_id, 60),
        "student_name": _cap(student, 80),
        "grade": _cap(payload["grade"], 20),
        "parent_name": _cap(payload["parentName"], 80),
        "email": _cap(payload["email"], 200),
        "phone": _cap(payload.get("phone", ""), 30),
        "courses": _cap(",".join(payload["courses"])),
        "options": _cap(",".join(payload["options"])),
        "fee_breakdown": _cap(desc_detail),
        "monthly_fee": str(fee),  # 月額 (yen) を metadata に保存 → 月末バッチで参照
        "source": "self-register-v2-setup",
        "system": "juku-payment-monthly",  # ai-juku webhook と区別する識別子
    }

    # 🚨 Step 1: Customer を先行作成 (CRITICAL fix・Stripe mode=setup の自動作成挙動に依存しない)
    # Stripe doc 公式: mode=setup でも customer or customer_email + customer_creation の組合せ
    # 明示的に customer 作成 → session に customer=cus_xxx を渡す方が安全 (全件 skip 事故防止)
    customer = _create_or_find_customer(secret_key, payload, registration_id, metadata)
    customer_id = customer.get("id", "")
    if not customer_id:
        raise RuntimeError("Customer 作成に失敗しました (customer.id 取得不能)")

    # Step 2: Checkout Session (mode=setup) で customer=cus_xxx を明示
    # 🚨 2026-05-13 緊急 fix: Round 5 で誤って追加した setup_intent_data[usage] は
    # Stripe Checkout Session API で「parameter_unknown」エラー (400) を返す無効パラメータだった。
    # Setup Mode では SetupIntent.usage は自動的に "off_session" になるため明示指定は不要。
    # ※ /v1/setup_intents 直接 API では usage は有効だが、Checkout Session の setup_intent_data 下では拒否される
    form = [
        ("mode", "setup"),
        ("payment_method_types[]", "card"),
        ("customer", customer_id),  # 🆕 明示的に customer を渡す
        ("locale", "ja"),
        ("success_url", f"{base_url}/payment/register-complete.html?session_id={{CHECKOUT_SESSION_ID}}"),
        ("cancel_url", f"{base_url}/payment/register.html?canceled=1"),
    ]
    for k, v in metadata.items():
        if v is None:
            continue
        form.append((f"metadata[{k}]", str(v)))
        # setup_intent_data にも同じ metadata を載せる → SetupIntent + PaymentMethod に伝播
        form.append((f"setup_intent_data[metadata][{k}]", str(v)))

    session = _stripe_post(secret_key, "checkout/sessions", form)
    # KV pending に customer_id も保存 (webhook 失敗時の復元用)
    session["_juku_customer_id"] = customer_id
    return session


# ─────────────── ハンドラ ───────────────

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON", "message": "JSONとして解釈できませんでした"})
                return

            errs, clean = _validate(payload)
            if errs:
                _json(self, 400, {"error": "VALIDATION_FAILED", "message": "入力内容にエラーがあります", "details": errs})
                return

            # Rate limiting (best-effort、KV 未設定なら通過)
            ip = _client_ip(self)
            ok, rl_msg = _rl_check(ip, clean["email"])
            if not ok:
                _log(f"rate-limit: ip={ip} email={clean['email']}")
                _json(self, 429, {"error": "RATE_LIMITED", "message": rl_msg})
                return

            secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            if not secret_key:
                _json(self, 503, {
                    "error": "STRIPE_SECRET_KEY_NOT_SET",
                    "message": "決済システムの準備が整っていません。塾長にご連絡ください。",
                })
                return

            fee, breakdown = _calculate_fee(clean["courses"], clean["options"])
            if fee <= 0:
                _json(self, 400, {"error": "INVALID_FEE", "message": "月額が 0 円になっています"})
                return

            # 🚨 2026-05-13 H1 fix: 同じ email で既に completed 登録があれば重複登録を拒否
            # (= Stripe に同じ保護者の Customer が複数作られて二重課金されるリスク回避)
            # 既存 reg を上書きしたい場合は塾長が先に「🗑 退塾処理」してから再登録するフロー
            try:
                email_norm = (clean.get("email") or "").strip().lower()
                if email_norm:
                    # reg:completed:index を辿って同じ email の record があるかチェック
                    zr = _redis_safe("ZRANGE", "reg:completed:index", "0", "-1", "REV")
                    if zr and isinstance(zr, dict):
                        rids = zr.get("result") or []
                        if isinstance(rids, list):
                            for rid_existing in rids[:200]:  # 最新 200 件のみチェック (性能配慮)
                                got = _redis_safe("GET", f"reg:completed:{rid_existing}")
                                if got and isinstance(got, dict):
                                    s = got.get("result")
                                    if s:
                                        try:
                                            r = json.loads(s)
                                            existing_email = (r.get("email") or "").strip().lower()
                                            if existing_email == email_norm:
                                                _log(f"register: duplicate email blocked - {email_norm} existing rid={rid_existing}")
                                                _json(self, 409, {
                                                    "error": "ALREADY_REGISTERED",
                                                    "message": f"このメールアドレス ({clean['email']}) は既に登録されています。カード情報の変更や月額の更新は塾長 LINE までご連絡ください。",
                                                    "existingRegistrationId": rid_existing,
                                                })
                                                return
                                        except Exception:
                                            pass
            except Exception as _e:
                # 重複チェック失敗は best-effort (KV 通信失敗時は通過させる・登録停止しない)
                _log(f"duplicate-email check failed (best-effort skip): {_e}")


            registration_id = "reg_" + secrets.token_urlsafe(12)

            # 🚨 2026-05-13: 塾長指示の apex primary 運用 (memory: feedback_vercel_apex_primary.md) に整合
            # success_url / cancel_url の host が apex/www mismatch すると Stripe Checkout から complete page への
            # 遷移時に session_id query が失われる致命傷を防ぐため、apex (trillion-ai-juku.com) を明示 fallback
            base_url = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
            if not base_url:
                host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "trillion-ai-juku.com"
                # www. prefix が来た場合は apex に正規化
                if host.startswith("www."):
                    host = host[4:]
                proto = self.headers.get("X-Forwarded-Proto") or "https"
                base_url = f"{proto}://{host}"

            try:
                session = _create_checkout_session(secret_key, clean, fee, breakdown, registration_id, base_url)
            except urllib.error.HTTPError as e:
                detail = ""
                stripe_error_code = ""
                stripe_error_message = ""
                try:
                    detail = e.read().decode("utf-8", errors="replace")
                    err_obj = json.loads(detail).get("error", {})
                    stripe_error_code = err_obj.get("code", "") or err_obj.get("type", "")
                    stripe_error_message = err_obj.get("message", "")
                except Exception:
                    pass
                _log(f"stripe HTTPError {e.code} reg={registration_id}: {detail[:1000]}")
                # 🚨 2026-05-13: 塾長からの「決済エラーありえない」緊急対応で、Stripe error detail を response に含めて即座に診断可能化
                _json(self, 502, {
                    "error": "STRIPE_API_ERROR",
                    "message": "決済セッションの作成に失敗しました。しばらくしてから再度お試しください。",
                    "registrationId": registration_id,
                    "stripeErrorCode": stripe_error_code,
                    "stripeErrorMessage": stripe_error_message[:500],
                    "stripeHttpCode": e.code,
                })
                return
            except urllib.error.URLError as e:
                _log(f"stripe URLError reg={registration_id}: {e}")
                _json(self, 502, {"error": "NETWORK_ERROR", "message": "決済システムへの接続に失敗しました。", "detail": str(e)[:200]})
                return
            except RuntimeError as e:
                # _create_or_find_customer の Customer 作成失敗
                _log(f"customer creation failed reg={registration_id}: {e}")
                _json(self, 502, {"error": "CUSTOMER_CREATION_FAILED", "message": str(e)[:200], "registrationId": registration_id})
                return
            except Exception as e:
                _log(f"register-subscribe unexpected error reg={registration_id}: {type(e).__name__}: {e}")
                _json(self, 500, {"error": "UNEXPECTED_ERROR", "message": f"{type(e).__name__}: {str(e)[:200]}", "registrationId": registration_id})
                return

            checkout_url = session.get("url")
            session_id = session.get("id")
            if not checkout_url:
                _json(self, 502, {"error": "NO_CHECKOUT_URL", "message": "Stripe からURLが返却されませんでした"})
                return

            # 登録待ちレコードを KV に保存 (best-effort)
            # 🆕 v2: customer_id を pending 時点で保存 (webhook 失敗時のフォールバック復元用)
            now_ts = int(time.time())
            preset_customer_id = session.get("_juku_customer_id", "") or session.get("customer", "")
            record = {
                "registration_id": registration_id,
                "session_id": session_id,
                "status": "pending",
                "created_at": now_ts,
                "fee": fee,
                "monthly_fee": fee,  # 月末バッチ参照用
                "breakdown": breakdown,
                "fee_breakdown": " / ".join(breakdown)[:240],
                "stripe_customer_id": preset_customer_id,  # 🆕 先行作成済 customer_id
                "checkout_mode": "setup",  # 🆕 mode 識別
                "system": "juku-payment-monthly",
                **clean,
            }
            _redis_safe("SET", f"reg:pending:{registration_id}", json.dumps(record, ensure_ascii=False), "EX", "604800")  # 7 days TTL
            _redis_safe("ZADD", "reg:index", str(now_ts), registration_id)

            _json(self, 200, {
                "checkoutUrl": checkout_url,
                "amount": fee,
                "registrationId": registration_id,
                "breakdown": breakdown,
            })
        except Exception as e:
            _log(f"register-subscribe internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": "システムエラーが発生しました。塾長にご連絡ください。"})

    def do_OPTIONS(self):
        # CORS preflight (同一オリジンなので不要だが念のため)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
