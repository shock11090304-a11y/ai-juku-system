"""神テスト サブスク申込 → Stripe Checkout Session (mode=subscription) を作る。

Endpoint: POST /api/checkout   (kamitest の Vercel プロジェクト・Root Directory=exam-app)

Body (JSON):
  { "email": "...", "password": "...", "name": "山田 太郎",
    "grade": "高校3年", "school": "○○高校" }

流れ (docs/book-exam.md §22):
  1. Supabase にアカウントを **ban 付きで** 先に作る (パスワードは本人が決めたもの。
     Stripe の metadata にパスワードを流さないための順序。支払いが完了するまで
     ban されたままなのでログインはできない)
  2. Stripe Checkout へ誘導 (月額・初回のみ 3 日間無料体験)
  3. 支払い完了 → webhook (stripe-webhook.py) が ban を解除 → 本人のパスワードで即ログイン可

Env (kamitest の Vercel プロジェクトにだけ設定する。リポジトリに書かない):
  STRIPE_SECRET_KEY          Stripe の Secret key
  STRIPE_PRICE_ID            月額 1,250 円の Price ID (price_...)
  SUPABASE_URL               https://<ref>.supabase.co
  SUPABASE_SERVICE_ROLE_KEY  Supabase の service_role (アカウント作成に必要)
  PUBLIC_BASE_URL            (任意) 既定 https://exam.trillion-ai-juku.com
  EXAM_SIGNUP_HOSTS          (任意) 申込を受け付ける Host のカンマ区切り
  STRIPE_API_BASE            (検査用) 既定 https://api.stripe.com

★ このファイルは他の api/*.py と同じく **自己完結** (共有モジュールを import しない)。
  Vercel は各ファイルを別々の関数としてデプロイするので、共有した瞬間に壊れ方が増える。
★ 検査: python3 scripts/book_exam/check_signup.py が偽の Stripe/Supabase を立てて
  このハンドラを実際に HTTP で叩く。ロジックを変えたら必ず回すこと。
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import sys
import urllib.error
import urllib.parse
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


# ─────────────── 定数 ───────────────

SYSTEM_TAG = "kamitest-subscription"     # AI塾の Stripe イベントと見分ける印 (両 webhook が見る)
BAN_10Y = "87600h"                       # 「実質無期限」の ban。解除は "none"
TRIAL_DAYS = 3
# ★ signup.html の <select> と一致していること (check_signup.py が突き合わせる)
GRADE_OPTIONS = ("中学1年", "中学2年", "中学3年", "高校1年", "高校2年", "高校3年",
                 "既卒・浪人", "その他")
# 契約が生きているとみなす status (この状態で再申込されたら二重契約なので断る)
ACTIVE_STATUSES = ("trialing", "active", "past_due")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _allowed_hosts():
    env = os.environ.get("EXAM_SIGNUP_HOSTS", "").strip()
    if env:
        return {h.strip().lower() for h in env.split(",") if h.strip()}
    return {"exam.trillion-ai-juku.com", "kamitest.vercel.app"}


def _req_host(handler):
    host = (handler.headers.get("X-Forwarded-Host") or handler.headers.get("Host") or "").strip()
    return host.split(":")[0].lower()      # ポートは見ない


def _base_url(handler):
    base = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base:
        return base
    proto = handler.headers.get("X-Forwarded-Proto") or "https"
    host = (handler.headers.get("X-Forwarded-Host") or handler.headers.get("Host")
            or "exam.trillion-ai-juku.com")
    return f"{proto}://{host}"


# ─────────────── バリデーション ───────────────

def validate(payload):
    errs = []
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""       # ★ trim しない (本人が決めた文字列)
    name = (payload.get("name") or "").strip()
    grade = (payload.get("grade") or "").strip()
    school = (payload.get("school") or "").strip()

    if not email or not EMAIL_RE.match(email) or len(email) > 200:
        errs.append("メールアドレスが不正です")
    if not isinstance(password, str) or len(password) < 8 or len(password) > 72:
        errs.append("パスワードは 8〜72 文字にしてください")
    if not name or len(name) > 80:
        errs.append("氏名を入力してください (80 文字まで)")
    if grade not in GRADE_OPTIONS:
        errs.append("学年を選んでください")
    if not school or len(school) > 120:
        errs.append("通塾学校名を入力してください (120 文字まで)")
    return errs, {"email": email, "password": password, "name": name,
                  "grade": grade, "school": school}


# ─────────────── Stripe ───────────────

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


# ─────────────── Supabase (service_role) ───────────────

def _sb_headers(extra=None):
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"].strip()
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def _sb_call(method, path, payload=None, extra_headers=None, timeout=15):
    url = os.environ["SUPABASE_URL"].strip().rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=_sb_headers(extra_headers),
                                 method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def find_user_by_email(email):
    """GoTrue admin にはメール検索が無いのでページを繰って探す。
    見つからなければ None。★上限まで見ても埋まっていたら「探し切れていない」ので
    例外にする (見落として二重作成に進むより、正直に止まる)。"""
    want = email.strip().lower()
    per_page = 200
    for page in range(1, 26):                       # 200 × 25 = 5000 人まで
        res = _sb_call("GET", f"/auth/v1/admin/users?page={page}&per_page={per_page}")
        users = res.get("users") if isinstance(res, dict) else res
        users = users or []
        for u in users:
            if (u.get("email") or "").strip().lower() == want:
                return u
        if len(users) < per_page:
            return None
    raise RuntimeError("ユーザー数が検索上限 (5000) を超えている — 検索方法の見直しが必要")


def _is_banned(user):
    """banned_until が未来なら ban 中。読めない値は「ban ではない」に倒す
    (ban 扱いを誤ると他人のパスワードを上書きする側に転ぶため、安全側は False)。"""
    raw = (user.get("banned_until") or "").strip()
    if not raw or raw.lower() == "none":
        return False
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return ts > datetime.now(timezone.utc)
    except ValueError:
        return False


def create_banned_user(clean):
    return _sb_call("POST", "/auth/v1/admin/users", {
        "email": clean["email"],
        "password": clean["password"],
        "email_confirm": True,               # 確認メールなしで即ログイン可能な状態にしておく
        "ban_duration": BAN_10Y,             # ★支払い完了までログイン不可 (webhook が解除)
        "user_metadata": {"student_name": clean["name"], "grade": clean["grade"],
                          "school": clean["school"], "signup_source": SYSTEM_TAG},
    })


def set_password(user_id, clean):
    return _sb_call("PUT", f"/auth/v1/admin/users/{user_id}", {
        "password": clean["password"],
        "user_metadata": {"student_name": clean["name"], "grade": clean["grade"],
                          "school": clean["school"], "signup_source": SYSTEM_TAG},
    })


def password_matches(email, password):
    """既存アカウントの本人確認。成功したときだけ True。"""
    try:
        _sb_call("POST", "/auth/v1/token?grant_type=password",
                 {"email": email, "password": password})
        return True
    except urllib.error.HTTPError:
        return False


def get_subscription_row(user_id):
    rows = _sb_call("GET", f"/rest/v1/subscriptions?user_id=eq.{user_id}&select=*")
    return rows[0] if isinstance(rows, list) and rows else None


# ─────────────── Checkout Session ───────────────

def build_session_form(clean, user_id, row, base_url):
    """検査しやすいように「フォームを組む」だけを分離した純関数。"""
    def cap(s, n=200):
        return str(s or "")[:n]
    meta = {
        "system": SYSTEM_TAG,
        "supabase_user_id": user_id,
        "email": cap(clean["email"]),
        "student_name": cap(clean["name"], 80),
        "grade": cap(clean["grade"], 20),
        "school": cap(clean["school"], 120),
    }
    form = [
        ("mode", "subscription"),
        ("line_items[0][price]", os.environ["STRIPE_PRICE_ID"].strip()),
        ("line_items[0][quantity]", "1"),
        ("locale", "ja"),
        ("success_url", f"{base_url}/signup-done.html"),
        ("cancel_url", f"{base_url}/signup.html?canceled=1"),
    ]
    # 一度でも契約したことがある (行がある) 人には無料体験を付けない
    if row is None:
        form.append(("subscription_data[trial_period_days]", str(TRIAL_DAYS)))
    # 前の契約の Stripe Customer が分かっていれば再利用 (Stripe 上の重複を防ぐ)
    if row and (row.get("stripe_customer_id") or "").strip():
        form.append(("customer", row["stripe_customer_id"].strip()))
    else:
        form.append(("customer_email", clean["email"]))
    for k, v in meta.items():
        form.append((f"metadata[{k}]", v))
        form.append((f"subscription_data[metadata][{k}]", v))
    return form


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

            errs, clean = validate(payload)
            if errs:
                _json(self, 400, {"error": "VALIDATION_FAILED",
                                  "message": "入力内容を確認してください", "details": errs})
                return

            host = _req_host(self)
            if host not in _allowed_hosts():
                # 他塾ドメイン (§21 の B2B 顧客) から自塾の Stripe に申込が入る事故を止める
                _log(f"checkout: host not allowed: {host}")
                _json(self, 403, {"error": "HOST_NOT_ALLOWED",
                                  "message": "このドメインからはお申し込みできません"})
                return

            missing = [k for k in ("STRIPE_SECRET_KEY", "STRIPE_PRICE_ID",
                                   "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
                       if not os.environ.get(k, "").strip()]
            if missing:
                _log(f"checkout: env not set: {missing}")
                _json(self, 503, {"error": "NOT_CONFIGURED",
                                  "message": "お申し込みの準備がまだ整っていません。しばらくお待ちください。"})
                return

            # --- アカウントの用意 -------------------------------------------
            user = find_user_by_email(clean["email"])
            row = None
            if user is None:
                created = create_banned_user(clean)
                user_id = created.get("id", "")
                if not user_id:
                    raise RuntimeError("アカウント作成に失敗 (id が返らない)")
                _log(f"checkout: created banned user {user_id} for {clean['email']}")
            else:
                user_id = user.get("id", "")
                row = get_subscription_row(user_id)
                if row and (row.get("status") or "") in ACTIVE_STATUSES:
                    _json(self, 409, {"error": "ALREADY_SUBSCRIBED",
                                      "message": "このメールアドレスには有効な契約があります。そのままログインしてください。"})
                    return
                if _is_banned(user):
                    # 支払い前に離脱した申込 or 解約済み。本人以外はこのメールで
                    # ログインできた実績が無いので、今回のパスワードで作り直す。
                    set_password(user_id, clean)
                    _log(f"checkout: reset password of banned user {user_id}")
                else:
                    # ログインできる生きたアカウント (先生発行の無料アカウント等)。
                    # ★パスワードが合った時だけ先へ (合わないのに進めると乗っ取りになる)
                    if not password_matches(clean["email"], clean["password"]):
                        _json(self, 401, {"error": "PASSWORD_MISMATCH",
                                          "message": "このメールアドレスは既に使われています。"
                                                     "そのアカウントのパスワードを入力してください。"})
                        return

            # --- Stripe Checkout ---------------------------------------------
            form = build_session_form(clean, user_id, row, _base_url(self))
            try:
                session = _stripe_post("checkout/sessions", form)
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                _log(f"checkout: stripe HTTPError {e.code}: {detail[:500]}")
                _json(self, 502, {"error": "STRIPE_API_ERROR",
                                  "message": "決済ページの作成に失敗しました。しばらくして再度お試しください。"})
                return

            url = session.get("url")
            if not url:
                _json(self, 502, {"error": "NO_CHECKOUT_URL",
                                  "message": "決済ページのURLが取得できませんでした"})
                return
            _json(self, 200, {"checkoutUrl": url,
                              "trial": row is None, "trialDays": TRIAL_DAYS})
        except Exception as e:
            _log(f"checkout internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR",
                              "message": "システムエラーが発生しました。しばらくして再度お試しください。"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
