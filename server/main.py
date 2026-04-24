"""
AI学習コーチ塾 — Backend API
FastAPI + SQLite + Stripe + LINE Messaging API

起動方法:
    cd server
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env  # 編集してAPIキー設定
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import os
import json
import sqlite3
import hmac
import hashlib
import base64
import pathlib
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).parent

# DATABASE_URL が設定されていれば Postgres、未設定なら SQLite（ローカル開発用）。
# Railway で Postgres プラグインを追加すると DATABASE_URL が自動注入される。
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))

if USE_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg import errors as pg_errors
    # psycopg3 は postgresql:// スキームのみ受け付ける
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
    IntegrityError = pg_errors.IntegrityError
else:
    IntegrityError = sqlite3.IntegrityError

# ローカル開発用 SQLite ファイルパス（Postgres 使用時は無視）
DB_PATH = pathlib.Path(os.getenv("DB_PATH", str(ROOT / "data.db")))
if not USE_POSTGRES:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
STATIC_DIR = ROOT.parent  # Serve the parent HTML/CSS/JS as static

# ==========================================================================
# Environment Variables
# ==========================================================================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
# 新プラン用 Price ID
STRIPE_PRICE_STANDARD = os.getenv("STRIPE_PRICE_STANDARD") or os.getenv("STRIPE_PRICE_AI", "price_standard_placeholder")
STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM") or os.getenv("STRIPE_PRICE_HYBRID", "price_premium_placeholder")
STRIPE_PRICE_FAMILY = os.getenv("STRIPE_PRICE_FAMILY") or os.getenv("STRIPE_PRICE_INTENSIVE", "price_family_placeholder")
STRIPE_PRICE_STUDENT_ADDON = os.getenv("STRIPE_PRICE_STUDENT_ADDON", "price_student_addon_placeholder")
STRIPE_PRICE_TRIAL = os.getenv("STRIPE_PRICE_TRIAL", "price_trial_placeholder")
STRIPE_PRICE_ENROLLMENT = os.getenv("STRIPE_PRICE_ENROLLMENT", "price_enrollment_placeholder")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CRON_SECRET = os.getenv("CRON_SECRET", "")  # 未設定時は cron 系エンドポイントを全拒否
STATS_TOKEN = os.getenv("STATS_TOKEN", "")  # 未設定時は /api/stats を全拒否
# HMAC 署名鍵（保護者ビュー署名・他の署名用途で利用）
APP_SECRET = os.getenv("APP_SECRET", "")

PRICE_MAP = {
    # 新プラン構造（2026-04-22〜、面談なし、AI機能で差別化）
    "standard": (STRIPE_PRICE_STANDARD, 24980, "スタンダード", 1),
    "premium": (STRIPE_PRICE_PREMIUM, 39800, "プレミアム", 1),
    "family": (STRIPE_PRICE_FAMILY, 59800, "家族プラン（最大3名）", 3),
    "student_addon": (STRIPE_PRICE_STUDENT_ADDON, 15000, "塾生アドオン", 1),
    # 後方互換
    "ai": (STRIPE_PRICE_STANDARD, 24980, "スタンダード", 1),
    "hybrid": (STRIPE_PRICE_PREMIUM, 39800, "プレミアム", 1),
    "intensive": (STRIPE_PRICE_FAMILY, 59800, "家族プラン（最大3名）", 3),
}

# 入塾金（トライアル後の初回請求に追加・塾生アドオンは免除）
ENROLLMENT_FEE = 10000

# 塾生アドオン（月額、入塾金不要）
STUDENT_ADDON_PRICE = 15000

# 第1期生トライアル価格（月額の1/10固定）
FOUNDER_TRIAL_PRICE = 1980
FOUNDER_LIMIT = 100

# 入塾金を免除するプラン
ENROLLMENT_FEE_EXEMPT = {"student_addon"}

# 本番で許可するフロントエンドのオリジン
# カンマ区切りで env 上書き可能: ALLOWED_ORIGINS=https://foo.com,https://bar.com
_default_origins = "https://trillion-ai-juku.com,https://www.trillion-ai-juku.com,http://localhost:8090,http://localhost:8000"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()]

# 1日あたり1生徒が消費できるAIトークン上限 (input+output の合計)
# 100K tokens ≒ Opus で $10、Sonnet で $1 程度。通常利用では十分超えない。
AI_DAILY_TOKEN_BUDGET = int(os.getenv("AI_DAILY_TOKEN_BUDGET", "100000"))

# ==========================================================================
# 認証（マジックリンク方式）
# ==========================================================================
# HMAC-SHA256 署名によるステートレストークン。30日有効。
# セキュリティ要件: MAGIC_LINK_SECRET は 32文字以上のランダム値を推奨
MAGIC_LINK_SECRET = os.getenv("MAGIC_LINK_SECRET", "") or APP_SECRET or "dev-secret-DO-NOT-USE-IN-PROD"
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", str(30 * 86400)))  # 30日

# Resend (メール送信) — 未設定時はコンソール出力にフォールバック
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "AI学習コーチ塾 <onboarding@resend.dev>")

# Stripe SDK (lazy import)
stripe = None
def get_stripe():
    global stripe
    if stripe is None:
        import stripe as _stripe
        _stripe.api_key = STRIPE_SECRET_KEY
        stripe = _stripe
    return stripe

# ==========================================================================
# Database Setup (SQLite / Postgres 両対応)
# ==========================================================================
class _Cursor:
    """sqlite3/psycopg 両対応のカーソル薄いラッパ。
    `?` プレースホルダを Postgres 用に `%s` へ変換し、fetchone/fetchall の
    結果を dict ライクに統一する。"""
    def __init__(self, cur, is_pg):
        self._cur = cur
        self._is_pg = is_pg
        self.lastrowid = None

    def execute(self, sql, params=()):
        if self._is_pg:
            sql = sql.replace("?", "%s")
        self._cur.execute(sql, params)
        if not self._is_pg:
            self.lastrowid = self._cur.lastrowid
        return self

    def executescript(self, sql):
        if self._is_pg:
            self._cur.execute(sql.replace("?", "%s"))
        else:
            self._cur.executescript(sql)
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return row

    def fetchall(self):
        return self._cur.fetchall()


class _Connection:
    def __init__(self, conn, is_pg):
        self._conn = conn
        self._is_pg = is_pg

    def cursor(self):
        if self._is_pg:
            cur = self._conn.cursor(row_factory=dict_row)
        else:
            cur = self._conn.cursor()
        return _Cursor(cur, self._is_pg)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def db():
    if USE_POSTGRES:
        return _Connection(psycopg.connect(DATABASE_URL), is_pg=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return _Connection(conn, is_pg=False)


def row_to_dict(row):
    return dict(row) if row else None


def init_db():
    # Postgres と SQLite で自動採番カラムの記法が異なる
    pk = "BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    conn = db()
    c = conn.cursor()
    c.executescript(f"""
    CREATE TABLE IF NOT EXISTS students (
        id {pk},
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        grade TEXT,
        goal TEXT,
        plan TEXT,
        status TEXT DEFAULT 'trial',
        stripe_customer_id TEXT,
        stripe_subscription_id TEXT,
        line_user_id TEXT,
        trial_start TIMESTAMP,
        trial_end TIMESTAMP,
        paid_since TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS payments (
        id {pk},
        student_id INTEGER,
        stripe_payment_intent TEXT,
        amount INTEGER,
        status TEXT,
        paid_at TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    );
    CREATE TABLE IF NOT EXISTS notifications (
        id {pk},
        student_id INTEGER,
        channel TEXT,
        template TEXT,
        payload TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        success INTEGER DEFAULT 0,
        error TEXT
    );
    CREATE TABLE IF NOT EXISTS events (
        id {pk},
        name TEXT,
        props TEXT,
        session_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS processed_events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS otp_codes (
        id {pk},
        student_id INTEGER NOT NULL,
        code TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
    CREATE INDEX IF NOT EXISTS idx_otp_student ON otp_codes(student_id, used_at, expires_at);
    """)
    conn.commit()
    conn.close()
init_db()

# ==========================================================================
# FastAPI App
# ==========================================================================
app = FastAPI(title="AI学習コーチ塾 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-cron-secret", "stripe-signature", "x-line-signature"],
)

# ==========================================================================
# Models
# ==========================================================================
class TrialSignup(BaseModel):
    name: str
    email: EmailStr
    grade: Optional[str] = None
    goal: Optional[str] = None
    plan: Optional[str] = "hybrid"

class CheckoutRequest(BaseModel):
    plan: str
    email: EmailStr
    name: str
    student_id: Optional[int] = None

class LinePushRequest(BaseModel):
    student_id: int
    template: str
    params: Optional[dict] = {}

class EventTrack(BaseModel):
    name: str
    props: Optional[dict] = {}
    session_id: Optional[str] = None

# ==========================================================================
# Routes: Health & Status
# ==========================================================================
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "stripe_configured": bool(STRIPE_SECRET_KEY),
        "line_configured": bool(LINE_CHANNEL_ACCESS_TOKEN),
        "anthropic_configured": bool(ANTHROPIC_API_KEY),
    }

@app.get("/api/stats")
def stats(x_stats_token: str = Header(None)):
    """CEO dashboard 用の集計情報。
    STATS_TOKEN env で保護。未設定時は全拒否、設定済みならヘッダ x-stats-token で認証。"""
    if not STATS_TOKEN:
        raise HTTPException(status_code=503, detail="Stats endpoint not configured")
    if not x_stats_token or not hmac.compare_digest(x_stats_token, STATS_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")
    now = datetime.now(timezone.utc)
    # Postgres TIMESTAMP 比較のため datetime オブジェクトで渡す
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM students WHERE status='paid'")
    paid = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM students WHERE status='trial'")
    trial = c.fetchone()["n"]
    c.execute("SELECT SUM(amount) AS s FROM payments WHERE status='paid' AND paid_at > ?", (thirty_days_ago,))
    mrr = c.fetchone()["s"] or 0
    c.execute("SELECT COUNT(*) AS n FROM notifications WHERE sent_at > ?", (seven_days_ago,))
    notifs = c.fetchone()["n"]
    conn.close()
    return {"paid_students": paid, "trial_students": trial, "mrr_yen": mrr, "notifications_7d": notifs}

# ==========================================================================
# Routes: Trial Signup (called from LP form)
# ==========================================================================
# ==========================================================================
# Auth helpers: magic link token sign/verify & email send
# ==========================================================================
def _sign_session_token(student_id: int, ttl_seconds: int = SESSION_TTL_SECONDS) -> str:
    """student_id と expiry を HMAC-SHA256 で署名し、URL-safe Base64 エンコード。"""
    import time
    exp = int(time.time()) + ttl_seconds
    payload = f"{student_id}.{exp}"
    sig = hmac.new(MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}.{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _verify_session_token(token: str) -> Optional[dict]:
    """トークンを検証して {student_id, exp} を返す。無効/期限切れなら None。"""
    import time
    if not token:
        return None
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded).decode()
        parts = raw.split(".")
        if len(parts) != 3:
            return None
        sid_str, exp_str, sig = parts
        expected = hmac.new(MAGIC_LINK_SECRET.encode(), f"{sid_str}.{exp_str}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        exp = int(exp_str)
        if exp < int(time.time()):
            return None
        return {"student_id": int(sid_str), "exp": exp}
    except Exception:
        return None


# In-memory rate limit tracker: {(ip, bucket): [timestamps]}
_RATE_LIMIT_STORE: dict = {}

def _client_ip(request) -> str:
    """X-Forwarded-For を考慮して本物のクライアントIPを取得（Railway等のプロキシ対応）。"""
    if not request:
        return "unknown"
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        # 先頭が元のクライアントIP（カンマ区切り）
        return xff.split(",")[0].strip()
    xri = request.headers.get("x-real-ip", "")
    if xri:
        return xri.strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit_ip(request, bucket: str, limit: int = 10, window: int = 60) -> None:
    """IPアドレス単位の簡易レートリミッタ。超過時は HTTPException 429 を投げる。
    プロセス内のin-memoryなのでマルチワーカーでは厳密ではないが、ブルートフォース抑制には十分。"""
    import time as _t
    ip = _client_ip(request)
    key = (ip, bucket)
    now = _t.time()
    timestamps = _RATE_LIMIT_STORE.get(key, [])
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= limit:
        raise HTTPException(status_code=429, detail="リクエストが多すぎます。しばらく待ってから再度お試しください。")
    timestamps.append(now)
    _RATE_LIMIT_STORE[key] = timestamps
    # メモリ肥大化対策: 古いバケットを定期的にクリーンアップ
    if len(_RATE_LIMIT_STORE) > 10000:
        cutoff = now - 3600
        for k in list(_RATE_LIMIT_STORE.keys()):
            _RATE_LIMIT_STORE[k] = [t for t in _RATE_LIMIT_STORE[k] if t > cutoff]
            if not _RATE_LIMIT_STORE[k]:
                del _RATE_LIMIT_STORE[k]


def _send_trial_ending_email(to_email: str, student_name: str, days_left: int, upgrade_url: str) -> dict:
    """体験終了リマインダーメール。継続したい人向けに本契約フォームへの誘導。
    体験終了時の自動課金は行わないので、何もしなければアカウントは自動失効する（データは保持）。
    """
    import html as _html
    if not RESEND_API_KEY:
        log.warning(f"[DEV-MODE] Trial reminder skipped for {to_email}")
        return {"sent": False, "dev_mode": True}
    safe_name = _html.escape(student_name or "")
    greeting = f"{safe_name}さまの保護者さま" if safe_name else "保護者さま"
    days_text = "あと1日" if days_left <= 1 else f"あと{days_left}日"
    subject = f"【AI学習コーチ塾】体験は{days_text}で終了 — 継続のご案内"
    html = f"""<!DOCTYPE html>
<html><body style="font-family: -apple-system, sans-serif; line-height: 1.7; color: #333; max-width: 560px; margin: 0 auto; padding: 2rem;">
<h1 style="font-size: 1.4rem; color: #6366f1;">🎓 AI学習コーチ塾</h1>
<p>{greeting}、体験のご利用ありがとうございます。</p>

<p style="background:#f8f9fc; padding:1rem; border-left:4px solid #6366f1; border-radius:4px; margin: 1.5rem 0;">
  📅 <strong>3日間の体験は{days_text}で終了します</strong>
</p>

<p><strong>継続してご利用されたい方</strong>は、以下のボタンから月額プランの本登録をお願いします。</p>

<p style="text-align:center; margin: 2rem 0;">
  <a href="{upgrade_url}" style="display:inline-block; padding: 1rem 2rem; background:linear-gradient(135deg,#6366f1,#ec4899); color:white; text-decoration:none; border-radius:8px; font-weight:700; font-size:1.05rem;">
    🎓 継続登録する（月額プラン）
  </a>
</p>

<div style="background:#fafafa; padding:1rem; border-radius:6px; margin: 1.5rem 0; font-size: 0.9rem;">
  <strong>💡 何もしなかった場合</strong><br>
  体験終了日に自動的にアクセスが失効します（<strong>自動課金は発生しません</strong>）。<br>
  アカウントデータは保持され、後日いつでも再開できます。
</div>

<p style="font-size:0.85rem; color:#666;">ご不明な点はお問い合わせください。</p>
<hr style="margin:2rem 0; border:none; border-top:1px solid #eee;">
<p style="font-size:0.8rem; color:#999;">
  お問い合わせ: <a href="mailto:info@trillion-ai-juku.com" style="color:#6366f1;">info@trillion-ai-juku.com</a>
</p>
</body></html>"""
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps({"from": FROM_EMAIL, "to": [to_email], "subject": subject, "html": html}).encode("utf-8"),
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json", "User-Agent": "ai-juku-system/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            log.info(f"Trial reminder sent to {to_email}: {result.get('id')}")
            return {"sent": True, "resend_id": result.get("id")}
    except Exception as e:
        log.error(f"Trial reminder email failed for {to_email}: {type(e).__name__}: {e}")
        return {"sent": False, "error": str(e)}


def _create_otp(student_id: int, ttl_seconds: int = 600) -> str:
    """6桁数字のOTPコードを生成しDBに保存。10分有効。"""
    import secrets
    code = f"{secrets.randbelow(1000000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    conn = db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO otp_codes (student_id, code, expires_at) VALUES (?, ?, ?)",
        (student_id, code, expires_at.isoformat())
    )
    conn.commit()
    conn.close()
    return code


def _send_magic_link_email(to_email: str, student_name: str, magic_url: str, otp_code: str = "", is_welcome: bool = False) -> dict:
    """Resend 経由でマジックリンクメール送信。OTPコードも含める。未設定ならコンソール出力。"""
    import html as _html
    subject_welcome = "【AI学習コーチ塾】ご登録ありがとうございます（ログインコード）"
    subject_relogin = "【AI学習コーチ塾】ログインコードをお送りします"
    subject = subject_welcome if is_welcome else subject_relogin

    # XSS対策: student_name に含まれる特殊文字をエスケープ
    safe_name = _html.escape(student_name or "")
    greeting = f"{safe_name}さまの保護者さま" if safe_name else "保護者さま"
    body_intro = (
        f"""<p>{greeting}、ご登録ありがとうございます 🎉</p>
    <p>3日間のトライアルが始まりました。<strong>以下の6桁コードをアプリに入力</strong>してログインしてください。</p>"""
        if is_welcome else
        f"<p>{greeting}、以下の6桁コードをアプリに入力してログインしてください。</p>"
    )

    # OTPコード表示ブロック (視認性重視、コピーしやすいフォーマット)
    otp_block = f"""
  <div style="text-align:center; margin: 2rem 0;">
    <p style="font-size:0.8rem; color:#666; margin-bottom:0.5rem;">ログインコード（10分間有効）</p>
    <p style="font-size: 2.5rem; font-weight: 900; letter-spacing: 0.5rem; font-family: 'SF Mono', monospace; color: #6366f1; background: #f5f5f5; padding: 1rem; border-radius: 12px; margin: 0;">
      {otp_code}
    </p>
  </div>""" if otp_code else ""

    html = f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, sans-serif; line-height: 1.7; color: #333; max-width: 560px; margin: 0 auto; padding: 2rem;">
  <h1 style="font-size: 1.4rem; color: #6366f1;">🎓 AI学習コーチ塾</h1>
  {body_intro}
  {otp_block}
  <p style="font-size:0.85rem; color:#666; text-align:center;">または以下のリンクから直接ログイン（30日間有効）:</p>
  <p style="text-align:center; margin: 1rem 0 2rem;">
    <a href="{magic_url}" style="display:inline-block; padding: 0.7rem 1.5rem; background:linear-gradient(135deg,#6366f1,#ec4899); color:white; text-decoration:none; border-radius:8px; font-weight:700; font-size:0.9rem;">
      🔗 ワンクリックでログイン
    </a>
  </p>
  <hr style="margin:2rem 0; border:none; border-top:1px solid #eee;">
  <p style="font-size:0.8rem; color:#999;">
    このメールに心当たりがない場合は無視してください（コードは10分、リンクは30日で自動失効します）。<br>
    お問い合わせ: <a href="mailto:info@trillion-ai-juku.com" style="color:#6366f1;">info@trillion-ai-juku.com</a>
  </p>
</body>
</html>"""

    if not RESEND_API_KEY:
        # Dev モード: コンソールにログ出力してテストを可能に
        log.warning(f"[DEV-MODE] RESEND_API_KEY 未設定のため送信スキップ。magic URL:\n  {magic_url}")
        return {"sent": False, "dev_mode": True, "magic_url": magic_url}

    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps({
                "from": FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "ai-juku-system/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            log.info(f"Magic link sent to {to_email}: {result.get('id')}")
            return {"sent": True, "resend_id": result.get("id")}
    except Exception as e:
        log.error(f"Resend API error for {to_email}: {type(e).__name__}: {e}")
        return {"sent": False, "error": str(e)[:200]}


def _get_current_student(authorization: Optional[str], allow_canceled: bool = False) -> Optional[dict]:
    """Authorization: Bearer <token> ヘッダからセッション検証し生徒レコードを返す。

    ステータスゲート:
    - 'paid': 常に許可
    - 'trial': trial_end が未来なら許可（体験期間中）
    - 'canceled' / 'expired': 拒否（allow_canceled=True の時のみ canceled は許可）
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[len("Bearer "):].strip()
    claims = _verify_session_token(token)
    if not claims:
        return None
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, grade, goal, plan, status, stripe_customer_id, trial_end FROM students WHERE id = ?", (claims["student_id"],))
    row = c.fetchone()
    conn.close()
    if not row:
        return None

    status = row["status"]
    now = datetime.now(timezone.utc)
    is_allowed = False
    if status == "paid":
        is_allowed = True
    elif status == "trial":
        # trial_end 未経過なら許可
        te = row["trial_end"]
        if te:
            try:
                if isinstance(te, str):
                    te_dt = datetime.fromisoformat(te.replace("Z", "+00:00"))
                else:
                    te_dt = te
                if te_dt.tzinfo is None:
                    te_dt = te_dt.replace(tzinfo=timezone.utc)
                if te_dt > now:
                    is_allowed = True
            except Exception:
                pass
    elif status == "canceled" and allow_canceled:
        is_allowed = True

    if not is_allowed:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "grade": row["grade"],
        "goal": row["goal"],
        "plan": row["plan"],
        "status": status,
    }


# ==========================================================================
# Routes: Authentication (Magic Link)
# ==========================================================================
class MagicLinkRequest(BaseModel):
    email: EmailStr


@app.post("/api/auth/magic-link")
def request_magic_link(payload: MagicLinkRequest, request: Request):
    """メールアドレスから生徒を検索し、ログインURLをメール送信する。
    存在しないメールでも 200 を返す（アカウント列挙攻撃対策）。"""
    email_lower = (payload.email or "").lower().strip()
    if not email_lower:
        raise HTTPException(status_code=400, detail="Email required")
    # レート制限: 同一IPから1分間に5回まで
    _check_rate_limit_ip(request, bucket="magic_link", limit=5, window=60)

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, status FROM students WHERE LOWER(email) = ? LIMIT 1", (email_lower,))
    row = c.fetchone()
    conn.close()

    # 体験期間中の trial ユーザーも送信対象（trial_end 未経過のみ）
    is_sendable = False
    if row:
        if row["status"] == "paid":
            is_sendable = True
        elif row["status"] == "trial":
            # trial_end チェック
            c = db().cursor()
            c.execute("SELECT trial_end FROM students WHERE id=?", (row["id"],))
            te_row = c.fetchone()
            if te_row and te_row["trial_end"]:
                try:
                    te = te_row["trial_end"]
                    if isinstance(te, str):
                        te_dt = datetime.fromisoformat(te.replace("Z", "+00:00"))
                    else:
                        te_dt = te
                    if te_dt.tzinfo is None:
                        te_dt = te_dt.replace(tzinfo=timezone.utc)
                    if te_dt > datetime.now(timezone.utc):
                        is_sendable = True
                except Exception:
                    pass

    if is_sendable:
        token = _sign_session_token(row["id"])
        magic_url = f"{BASE_URL}/auth.html?t={token}"
        otp_code = _create_otp(row["id"])
        _send_magic_link_email(row["email"], row["name"] or "", magic_url, otp_code=otp_code, is_welcome=False)
    else:
        # 存在しない or 期限切れでも同じレスポンスを返す（列挙対策）
        log.info(f"Magic link requested for unknown/inactive email: {email_lower}")

    return {"ok": True, "message": "該当するアカウントがあればメールをお送りしました。届かない場合は迷惑メールフォルダもご確認ください。"}


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


@app.post("/api/auth/verify-code")
def verify_code(payload: VerifyCodeRequest, request: Request):
    """6桁OTPコードでログイン。成功時は session token を返す。

    セキュリティ対策:
    - 1つのOTPに対して最大5回まで失敗を許容。超えたら全OTP無効化
    - IPごとに1分あたり10リクエストまで（in-memory）
    - 原子的 UPDATE ... RETURNING で競合防止
    - 失敗時の応答を一定にして列挙攻撃対策
    """
    import time
    email_lower = (payload.email or "").lower().strip()
    code = (payload.code or "").strip()
    if not email_lower or not code or len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=400, detail="有効なメールアドレスと6桁のコードを入力してください")

    # シンプルなIP rate limit (in-memory)
    _check_rate_limit_ip(request, bucket="verify_code", limit=10, window=60)

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, grade, goal, plan, status, trial_end FROM students WHERE LOWER(email) = ? LIMIT 1", (email_lower,))
    student = c.fetchone()

    generic_401 = HTTPException(status_code=401, detail="コードが正しくないか、有効期限が切れています")

    # trial_end 未経過の trial ユーザーも許可
    _active = False
    if student:
        if student["status"] == "paid":
            _active = True
        elif student["status"] == "trial" and student["trial_end"]:
            try:
                te = student["trial_end"]
                if isinstance(te, str):
                    te_dt = datetime.fromisoformat(te.replace("Z", "+00:00"))
                else:
                    te_dt = te
                if te_dt.tzinfo is None:
                    te_dt = te_dt.replace(tzinfo=timezone.utc)
                if te_dt > datetime.now(timezone.utc):
                    _active = True
            except Exception:
                pass
    if not _active:
        c.execute("SELECT 1")
        conn.close()
        raise generic_401

    # 原子的に「未使用かつ有効なコード」を消費する
    c.execute(
        """UPDATE otp_codes
           SET used_at = CURRENT_TIMESTAMP
           WHERE student_id = ? AND code = ? AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP
           RETURNING id""",
        (student["id"], code)
    )
    otp = c.fetchone()
    if not otp:
        # 失敗カウントをインクリメント、5回超えたらこのユーザーの全OTPを無効化
        c.execute(
            "SELECT COUNT(*) AS n FROM otp_codes WHERE student_id = ? AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP",
            (student["id"],)
        )
        active_count = c.fetchone()["n"]
        # 記録目的で failed_attempts テーブルは作らない（シンプル化）。代わりに、
        # 5分以内の失敗試行をカウントしてlockoutする
        # ここでは「直近5分の verify-code 失敗 >= 5」を発火条件に
        c.execute(
            """SELECT COUNT(*) AS n FROM notifications
               WHERE student_id = ? AND template='otp_fail'
                 AND sent_at > CURRENT_TIMESTAMP - INTERVAL '5 minutes'"""
            if USE_POSTGRES else
            """SELECT COUNT(*) AS n FROM notifications
               WHERE student_id = ? AND template='otp_fail'
                 AND sent_at > datetime('now', '-5 minutes')""",
            (student["id"],)
        )
        fail_count = c.fetchone()["n"]
        # 失敗記録
        c.execute(
            "INSERT INTO notifications (student_id, channel, template, payload, success) VALUES (?, 'internal', 'otp_fail', ?, 0)",
            (student["id"], json.dumps({"ip": (request.client.host if request.client else None)}))
        )
        if fail_count >= 4:
            # 5回目の失敗(=既に4回記録+今回で5): このユーザーの有効OTPを全て無効化
            c.execute(
                "UPDATE otp_codes SET used_at = CURRENT_TIMESTAMP WHERE student_id = ? AND used_at IS NULL",
                (student["id"],)
            )
            log.warning(f"OTP lockout triggered for student {student['id']} ({email_lower}): invalidated all active codes")
        conn.commit()
        conn.close()
        raise generic_401

    conn.commit()
    conn.close()

    # セッショントークン発行
    token = _sign_session_token(student["id"])
    import time
    exp = int(time.time()) + SESSION_TTL_SECONDS
    log.info(f"OTP verified for student_id={student['id']} ({email_lower})")
    return {
        "ok": True,
        "token": token,
        "expires_at": exp,
        "student": {
            "id": student["id"],
            "name": student["name"],
            "email": student["email"],
            "grade": student["grade"],
            "goal": student["goal"],
            "plan": student["plan"],
        }
    }


@app.get("/api/auth/verify")
def verify_magic_link(t: str):
    """auth.html からのトークン検証。有効なら生徒情報を返す。
    成功時に同じトークンを返し、クライアントは localStorage にセッションとして保存する。"""
    claims = _verify_session_token(t)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired link")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, grade, goal, plan, status, trial_end FROM students WHERE id = ?", (claims["student_id"],))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")

    # paid or trial(未経過)のみ許可
    _allowed = False
    if row["status"] == "paid":
        _allowed = True
    elif row["status"] == "trial" and row["trial_end"]:
        try:
            te = row["trial_end"]
            if isinstance(te, str):
                te_dt = datetime.fromisoformat(te.replace("Z", "+00:00"))
            else:
                te_dt = te
            if te_dt.tzinfo is None:
                te_dt = te_dt.replace(tzinfo=timezone.utc)
            if te_dt > datetime.now(timezone.utc):
                _allowed = True
        except Exception:
            pass
    if not _allowed:
        raise HTTPException(status_code=403, detail="体験期間が終了しました。継続登録をご希望の方はLPからお申し込みください。")

    return {
        "ok": True,
        "token": t,
        "expires_at": claims["exp"],
        "student": {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "grade": row["grade"],
            "goal": row["goal"],
            "plan": row["plan"],
            "status": row["status"],
        }
    }


@app.get("/api/auth/me")
def auth_me(authorization: Optional[str] = Header(None)):
    """現在のセッションを検証して生徒情報を返す。全ページのアクセスガードに使う。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"ok": True, "student": student}


@app.post("/api/trial/signup")
def trial_signup(payload: TrialSignup):
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=3)  # 3日間の無料体験
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            """INSERT INTO students (name, email, grade, goal, plan, status, trial_start, trial_end)
               VALUES (?, ?, ?, ?, ?, 'trial', ?, ?)
               RETURNING id""",
            (payload.name, payload.email, payload.grade, payload.goal,
             payload.plan or "hybrid", now.isoformat(), trial_end.isoformat())
        )
        returned = c.fetchone()
        student_id = returned["id"] if returned else None
        conn.commit()
    except IntegrityError:
        conn.rollback()
        c.execute("SELECT id FROM students WHERE email = ?", (payload.email,))
        row = c.fetchone()
        student_id = row["id"] if row else None
        if not student_id:
            raise HTTPException(status_code=400, detail="Email conflict")
    conn.close()

    log.info(f"Trial signup: {payload.email} -> student_id={student_id}")
    return {"ok": True, "student_id": student_id, "trial_end": trial_end.isoformat()}

# ==========================================================================
# Routes: Stripe Checkout
# ==========================================================================
@app.post("/api/stripe/trial-checkout")
def create_trial_checkout(payload: dict):
    """3日間体験のための ¥1,980 単発決済。サブスク無し（自動課金なし）。
    体験終了後、ユーザーが明示的に継続登録する必要がある。
    """
    email = (payload.get("email") or "").strip()
    name = (payload.get("name") or "").strip()
    student_id = payload.get("student_id")
    if not email:
        raise HTTPException(status_code=400, detail="email required")

    # 第1期生枠チェック
    conn_fc = db()
    c_fc = conn_fc.cursor()
    try:
        c_fc.execute(
            "SELECT COUNT(*) FROM students WHERE status IN ('paid', 'trial') AND plan IS NOT NULL"
        )
        taken = c_fc.fetchone()[0]
    except Exception:
        taken = 0
    conn_fc.close()
    if taken >= FOUNDER_LIMIT and not student_id:
        raise HTTPException(
            status_code=403,
            detail=f"第1期生{FOUNDER_LIMIT}名の募集は終了しました。次期募集をお待ちください。"
        )

    if not STRIPE_SECRET_KEY:
        return {
            "mock": True,
            "checkout_url": f"{BASE_URL}/checkout-success.html?session_id=mock_trial",
            "amount": FOUNDER_TRIAL_PRICE,
        }

    s = get_stripe()
    session = s.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "jpy",
                "product_data": {
                    "name": "AI学習コーチ塾 - 3日間体験",
                    "description": "AIチューター・教材生成・学習分析をフル活用できる3日間。期間終了後に継続ご希望の方のみ、別途本契約フォームからお進みください。"
                },
                "unit_amount": FOUNDER_TRIAL_PRICE,
            },
            "quantity": 1,
        }],
        customer_email=email,
        success_url=f"{BASE_URL}/checkout-success.html?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/checkout-cancel.html",
        metadata={
            "purchase_type": "trial",
            "student_id": str(student_id or ""),
            "name": name,
        }
    )
    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "amount": FOUNDER_TRIAL_PRICE,
    }


@app.post("/api/stripe/checkout")
def create_checkout_session(payload: CheckoutRequest):
    """
    新プラン構造でのチェックアウト:
    - 通常プラン (standard/premium/family): 月額サブスク（3日間トライアル）+ トライアル後の初回請求に入塾金 ¥10,000 を追加
    - 塾生アドオン (student_addon): 入塾金なし、月額 ¥15,000 のみ
    - トライアル開始時は ¥1,980 のみ即時課金、入塾金はトライアル後の初回請求書に計上
    """
    price_info = PRICE_MAP.get(payload.plan)
    if not price_info:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {payload.plan}")
    price_id, amount, plan_name, max_students = price_info

    # 第1期生枠チェック: LP で「100名限定」と約束しているため、既存 paid 生徒が
    # FOUNDER_LIMIT に達している場合はここで停止する。これがないと URL 直打ちで
    # 101名目以降の決済が通ってしまい、マーケ上の約束を破ることになる。
    # ただし、既存 paid 生徒の更新（再課金・プラン変更）は許可する。
    if not payload.student_id:
        conn_fc = db()
        c_fc = conn_fc.cursor()
        try:
            c_fc.execute(
                "SELECT COUNT(*) FROM students WHERE status='paid' AND plan IS NOT NULL AND plan != ''"
            )
            paid_count = c_fc.fetchone()[0]
        except Exception as e:
            log.error(f"Founder check query failed: {e}")
            paid_count = 0
        conn_fc.close()
        if paid_count >= FOUNDER_LIMIT:
            raise HTTPException(
                status_code=403,
                detail=f"第1期生{FOUNDER_LIMIT}名の募集は終了しました。次期募集をお待ちください。"
            )

    # student_id が指定されている場合、email との一致を検証する。
    # これをしないと連番IDで他生徒の stripe_customer_id を上書きでき、課金を奪える。
    if payload.student_id:
        conn_ck = db()
        c_ck = conn_ck.cursor()
        c_ck.execute("SELECT email FROM students WHERE id = ?", (payload.student_id,))
        _row_ck = c_ck.fetchone()
        conn_ck.close()
        if not _row_ck:
            raise HTTPException(status_code=404, detail="Student not found")
        if (_row_ck["email"] or "").lower() != (payload.email or "").lower():
            raise HTTPException(status_code=403, detail="student_id/email mismatch")

    if not STRIPE_SECRET_KEY:
        # Mock mode: return fake checkout URL（API key未設定時のデモ用）
        return {
            "mock": True,
            "checkout_url": f"{BASE_URL}/checkout-success.html?session_id=mock_{payload.plan}",
            "plan": payload.plan,
            "plan_name": plan_name,
            "amount": amount,
            "max_students": max_students,
            "enrollment_fee": ENROLLMENT_FEE if payload.plan not in ENROLLMENT_FEE_EXEMPT else 0,
            "trial_fee": FOUNDER_TRIAL_PRICE if payload.plan != "student_addon" else 0,
            "note": "Stripe API key未設定。ENVに STRIPE_SECRET_KEY を設定すると実際の決済画面に誘導されます。"
        }

    s = get_stripe()

    # 塾生アドオン: 入塾金なし・トライアルなしの単純サブスク
    if payload.plan == "student_addon":
        session = s.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=payload.email,
            success_url=f"{BASE_URL}/checkout-success.html?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/checkout-cancel.html",
            subscription_data={
                "metadata": {"plan": payload.plan, "student_id": str(payload.student_id or ""), "type": "student_addon"}
            },
            metadata={"plan": payload.plan, "student_id": str(payload.student_id or ""), "type": "student_addon"}
        )
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "plan_name": plan_name,
            "monthly_fee": amount,
            "enrollment_fee": 0,
        }

    # 継続本契約: 月額サブスク。トライアル無し（即時課金）。
    # 体験期間は別途 /api/stripe/trial-checkout で単発¥1,980決済済み。
    # 入塾金はWebhook (checkout.session.completed) で InvoiceItem として
    # 顧客に作成 → 初回請求書に自動的に乗る。
    needs_enrollment_fee = payload.plan not in ENROLLMENT_FEE_EXEMPT
    subscription_data = {
        "metadata": {
            "plan": payload.plan,
            "student_id": str(payload.student_id or ""),
            "max_students": str(max_students),
            "founder": "1",
            "needs_enrollment_fee": "1" if needs_enrollment_fee else "0",
            "purchase_type": "monthly",
        }
    }

    session_kwargs = {
        "mode": "subscription",
        "payment_method_types": ["card"],
        "line_items": [{"price": price_id, "quantity": 1}],
        "customer_email": payload.email,
        "success_url": f"{BASE_URL}/checkout-success.html?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{BASE_URL}/checkout-cancel.html",
        "subscription_data": subscription_data,
        "metadata": {
            "plan": payload.plan,
            "plan_name": plan_name,
            "student_id": str(payload.student_id or ""),
            "max_students": str(max_students),
            "purchase_type": "monthly",
            "needs_enrollment_fee": "1" if needs_enrollment_fee else "0",
        }
    }

    try:
        session = s.checkout.Session.create(**session_kwargs)
    except Exception as e:
        log.error(f"Stripe checkout.Session.create failed for plan={payload.plan}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {type(e).__name__}: {str(e)[:500]}")

    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "plan_name": plan_name,
        "monthly_fee": amount,
        "trial_fee": FOUNDER_TRIAL_PRICE,
        "enrollment_fee": ENROLLMENT_FEE if payload.plan not in ENROLLMENT_FEE_EXEMPT else 0,
        "max_students": max_students,
    }


@app.get("/api/plans")
def list_plans():
    """フロントエンドがプラン一覧を動的取得する用"""
    return {
        "plans": {
            k: {"price": v[1], "name": v[2], "max_students": v[3]}
            for k, v in PRICE_MAP.items()
            if k in ("standard", "premium", "family", "student_addon")
        },
        "enrollment_fee": ENROLLMENT_FEE,
        "trial_fee": FOUNDER_TRIAL_PRICE,
        "trial_duration_days": 3,
    }

@app.get("/api/founders/count")
def founders_count():
    """第1期生の残り枠をカウント。
    status='paid' の全プラン（新規: standard/premium/family/student_addon,
    旧: ai/hybrid/intensive）を対象。トライアル中も status='paid' が立つため、
    実際に枠を占有している全員をカウントする。"""
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT COUNT(*) FROM students WHERE status='paid' AND plan IS NOT NULL AND plan != ''"
        )
        paid = c.fetchone()[0]
    except Exception as e:
        log.error(f"founders_count query failed: {e}")
        paid = 0
    conn.close()
    remaining = max(0, FOUNDER_LIMIT - paid)
    return {"limit": FOUNDER_LIMIT, "taken": paid, "remaining": remaining}

# ==========================================================================
# Routes: Stripe Webhook
# ==========================================================================
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    if not STRIPE_WEBHOOK_SECRET:
        log.warning("Stripe webhook called but STRIPE_WEBHOOK_SECRET not set")
        return {"received": True, "mock": True}

    payload = await request.body()
    s = get_stripe()
    try:
        event = s.Webhook.construct_event(payload, stripe_signature, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        log.error(f"Webhook signature error: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 冪等性ガード: Stripe は webhook を再送するため、同じ event.id が2回処理されると
    # InvoiceItem の二重作成などで多重課金に直結する。processed_events に UNIQUE 制約で
    # 先勝ちINSERTし、既に入っていれば即座に return。
    event_id = event.get("id")
    if event_id:
        conn = db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO processed_events (event_id, event_type) VALUES (?, ?)",
                (event_id, event.get("type", "")),
            )
            conn.commit()
        except IntegrityError:
            conn.rollback()
            conn.close()
            log.info(f"Stripe webhook duplicate ignored: id={event_id}, type={event.get('type')}")
            return {"received": True, "duplicate": True}
        conn.close()

    log.info(f"Stripe webhook: {event['type']} id={event_id}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {}) or {}
        purchase_type = meta.get("purchase_type", "monthly")  # 既定は月額（旧互換）
        plan = meta.get("plan")
        student_id = meta.get("student_id")
        max_students = meta.get("max_students", "1")
        name_from_meta = meta.get("name", "")
        conn = db()
        c = conn.cursor()
        customer = session.get("customer")
        subscription = session.get("subscription")
        email = session.get("customer_details", {}).get("email") or session.get("customer_email")

        if purchase_type == "trial":
            # 3日間体験(単発¥1,980): status='trial', trial_start=now, trial_end=now+3d
            # サブスク無し。自動課金は発生しない。
            now = datetime.now(timezone.utc)
            trial_end = now + timedelta(days=3)
            if student_id and student_id != "":
                c.execute(
                    """UPDATE students SET status='trial', stripe_customer_id=?,
                           trial_start=?, trial_end=?, updated_at=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (customer, now.isoformat(), trial_end.isoformat(), student_id)
                )
            elif email:
                c.execute("SELECT id FROM students WHERE email=?", (email,))
                row = c.fetchone()
                if row:
                    c.execute(
                        """UPDATE students SET status='trial', stripe_customer_id=?,
                               trial_start=?, trial_end=?, updated_at=CURRENT_TIMESTAMP
                           WHERE id=?""",
                        (customer, now.isoformat(), trial_end.isoformat(), row[0])
                    )
                else:
                    c.execute(
                        """INSERT INTO students (name, email, status, stripe_customer_id, trial_start, trial_end)
                           VALUES (?, ?, 'trial', ?, ?, ?)""",
                        (name_from_meta or "（新規）", email, customer, now.isoformat(), trial_end.isoformat())
                    )
            conn.commit()

        else:  # purchase_type == "monthly" (旧互換含む)
            # 月額サブスク登録: status='paid'、入塾金 InvoiceItem 作成
            if student_id and student_id != "":
                c.execute(
                    """UPDATE students SET status='paid', stripe_customer_id=?, stripe_subscription_id=?,
                           paid_since=CURRENT_TIMESTAMP, plan=?, updated_at=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (customer, subscription, plan, student_id)
                )
            elif email:
                c.execute("SELECT id FROM students WHERE email=?", (email,))
                row = c.fetchone()
                if row:
                    c.execute(
                        """UPDATE students SET status='paid', stripe_customer_id=?, stripe_subscription_id=?,
                               paid_since=CURRENT_TIMESTAMP, plan=?, updated_at=CURRENT_TIMESTAMP
                           WHERE id=?""",
                        (customer, subscription, plan, row[0])
                    )
                else:
                    c.execute(
                        """INSERT INTO students (name, email, plan, status, stripe_customer_id, stripe_subscription_id, paid_since)
                           VALUES (?, ?, ?, 'paid', ?, ?, CURRENT_TIMESTAMP)""",
                        ("（新規）", email, plan, customer, subscription)
                    )
            conn.commit()

            # 入塾金 InvoiceItem (月額のみ)
            if meta.get("needs_enrollment_fee") == "1" and customer:
                try:
                    s.InvoiceItem.create(
                        customer=customer, amount=ENROLLMENT_FEE, currency="jpy",
                        description="入塾金（システム登録費用・初回のみ）",
                        metadata={"plan": plan, "type": "enrollment_fee"},
                    )
                    log.info(f"✅ Enrollment fee InvoiceItem created: customer={customer}")
                except Exception as e:
                    log.error(f"Failed to create enrollment fee InvoiceItem: {type(e).__name__}: {e}")

        # Welcome email (どちらのタイプも共通: ログインコード+リンク送信)
        try:
            if student_id and student_id != "":
                c.execute("SELECT id, name, email FROM students WHERE id=?", (student_id,))
            elif email:
                c.execute("SELECT id, name, email FROM students WHERE email=?", (email,))
            else:
                c.execute("SELECT id, name, email FROM students WHERE 1=0")
            s_row = c.fetchone()
            if s_row and s_row["email"]:
                _token = _sign_session_token(s_row["id"])
                _magic_url = f"{BASE_URL}/auth.html?t={_token}"
                _otp_code = _create_otp(s_row["id"])
                _send_magic_link_email(s_row["email"], s_row["name"] or "", _magic_url, otp_code=_otp_code, is_welcome=True)
        except Exception as e:
            log.error(f"Failed to send welcome magic link: {type(e).__name__}: {e}")

        conn.close()
        log.info(f"✅ Checkout completed: type={purchase_type}, plan={plan}, customer={customer}")

    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        conn = db()
        c = conn.cursor()
        c.execute(
            """INSERT INTO payments (stripe_payment_intent, amount, status, paid_at)
               VALUES (?, ?, 'paid', CURRENT_TIMESTAMP)""",
            (invoice.get("payment_intent"), invoice.get("amount_paid", 0))
        )
        conn.commit()
        conn.close()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.canceled"):
        sub = event["data"]["object"]
        conn = db()
        c = conn.cursor()
        c.execute("UPDATE students SET status='canceled', updated_at=CURRENT_TIMESTAMP WHERE stripe_subscription_id=?",
                  (sub.get("id"),))
        conn.commit()
        conn.close()

    return {"received": True}

# ==========================================================================
# Routes: LINE Messaging
# ==========================================================================
LINE_TEMPLATES = {
    "weekly_report": lambda p: {
        "type": "text",
        "text": f"📊 {p.get('name', '生徒')}さんの今週のレポート\n\n"
                f"🔥 学習時間: {p.get('hours', 0)}時間\n"
                f"💯 平均正答率: {p.get('accuracy', 0)}%\n"
                f"💬 AI質問数: {p.get('questions', 0)}回\n\n"
                f"詳しくはマイページをご確認ください👇\n"
                f"{p.get('url', BASE_URL)}"
    },
    "streak_reminder": lambda p: {
        "type": "text",
        "text": f"{p.get('name', '生徒')}さん、こんばんは🌙\n"
                f"今日はまだ学習時間がありません。\n"
                f"5分だけでもOKです。\n"
                f"ストリーク🔥{p.get('streak', 0)}日を途切れさせない！"
    },
    "achievement": lambda p: {
        "type": "text",
        "text": f"🎉 アチーブメント獲得！\n\n"
                f"「{p.get('achievement', '')}」\n"
                f"{p.get('description', '')}\n\n"
                f"+{p.get('xp', 0)} XP"
    },
    "trial_ending": lambda p: {
        "type": "text",
        "text": f"⏰ 無料体験終了まであと{p.get('days_left', 3)}日\n\n"
                f"{p.get('name', '生徒')}さんは3日間で:\n"
                f"⏱ {p.get('hours', 0)}時間学習\n"
                f"💬 AI質問 {p.get('questions', 0)}回\n\n"
                f"継続するにはこちら👇\n"
                f"{BASE_URL}/checkout.html?email={p.get('email', '')}"
    },
}

def _do_line_push(student_id: int, template: str, params: Optional[dict] = None) -> dict:
    """LINE push の内部実装。cron からは HTTP ではなくこちらを直接呼ぶ。"""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        log.warning("LINE push called but not configured")
        return {"ok": False, "mock": True, "message": "LINE_CHANNEL_ACCESS_TOKEN未設定"}

    conn = db()
    c = conn.cursor()
    c.execute("SELECT line_user_id, name FROM students WHERE id = ?", (student_id,))
    row = c.fetchone()
    if not row or not row["line_user_id"]:
        raise HTTPException(status_code=404, detail="Student or LINE user ID not found")

    tmpl_fn = LINE_TEMPLATES.get(template)
    if not tmpl_fn:
        raise HTTPException(status_code=400, detail=f"Unknown template: {template}")

    # 念のため params 側の name を上書きし、URL パラメータも quote してフィッシングリンク偽装を防ぐ
    import urllib.parse as _urlparse
    safe_email = _urlparse.quote(str((params or {}).get("email", "")), safe="")
    merged = {**(params or {}), "name": row["name"], "email": safe_email}
    message = tmpl_fn(merged)

    import urllib.request as _urlreq
    req = _urlreq.Request(
        "https://api.line.me/v2/bot/message/push",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        },
        data=json.dumps({"to": row["line_user_id"], "messages": [message]}).encode("utf-8")
    )
    try:
        with _urlreq.urlopen(req, timeout=10) as resp:
            success = resp.status == 200
    except Exception as e:
        log.error(f"LINE push failed: {e}")
        success = False

    c.execute(
        """INSERT INTO notifications (student_id, channel, template, payload, success)
           VALUES (?, 'line', ?, ?, ?)""",
        (student_id, template, json.dumps(merged, ensure_ascii=False), 1 if success else 0)
    )
    conn.commit()
    conn.close()
    return {"ok": success}


@app.post("/api/line/push")
def line_push(payload: LinePushRequest, x_cron_secret: str = Header(None)):
    """LINE push の公開エンドポイント。CRON_SECRET を必須化し、
    任意の塾外の攻撃者が生徒にフィッシング誘導メッセージを送れないようにする。"""
    if not CRON_SECRET:
        raise HTTPException(status_code=503, detail="LINE push not configured (CRON_SECRET missing)")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return _do_line_push(payload.student_id, payload.template, payload.params)


@app.post("/api/line/webhook")
async def line_webhook(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    if LINE_CHANNEL_SECRET:
        hash_ = hmac.new(LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256).digest()
        if base64.b64encode(hash_).decode() != x_line_signature:
            raise HTTPException(status_code=400, detail="Invalid signature")
    data = json.loads(body)
    # Handle follow events: bind LINE user id to student via email/name
    for event in data.get("events", []):
        if event["type"] == "follow":
            log.info(f"LINE follow: {event['source']['userId']}")
    return {"ok": True}

# ==========================================================================
# Routes: Cron-style (triggered externally)
# ==========================================================================
def _compute_weekly_stats(student_id: int, days: int = 7) -> dict:
    """過去N日間の活動統計を events テーブルから集計"""
    conn = db()
    c = conn.cursor()
    since_dt = datetime.now(timezone.utc) - timedelta(days=days)
    # 活動ログ集計
    c.execute(
        """SELECT name, props FROM events
           WHERE session_id = ? AND created_at >= ?""",
        (str(student_id), since_dt)
    )
    rows = c.fetchall()
    conn.close()

    hours = 0.0
    questions = 0
    problems_done = 0
    correct = 0
    total_answered = 0
    subject_stats = {}

    for r in rows:
        name = r["name"] or ""
        try:
            props = json.loads(r["props"] or "{}")
        except Exception:
            props = {}
        if name == "activity_study_session":
            hours += float(props.get("minutes", 0)) / 60.0
        elif name == "activity_chat_message" or name == "activity_ai_question":
            questions += 1
        elif name == "activity_problem_solved":
            problems_done += 1
            total_answered += 1
            if props.get("correct"):
                correct += 1
            subj = props.get("subject", "その他")
            if subj not in subject_stats:
                subject_stats[subj] = {"correct": 0, "total": 0}
            subject_stats[subj]["total"] += 1
            if props.get("correct"):
                subject_stats[subj]["correct"] += 1
        elif name == "activity_ai_call":
            questions += 1

    accuracy = round(100 * correct / total_answered) if total_answered > 0 else 0
    weakest_subject = None
    if subject_stats:
        weakest = min(subject_stats.items(), key=lambda x: (x[1]["correct"] / x[1]["total"]) if x[1]["total"] else 1)
        weakest_subject = weakest[0]

    return {
        "hours": round(hours, 1),
        "questions": questions,
        "problems_done": problems_done,
        "accuracy": accuracy,
        "weakest_subject": weakest_subject,
        "subject_stats": subject_stats,
        "days": days,
    }


@app.post("/api/cron/expire-trials")
def cron_expire_trials(x_cron_secret: str = Header(None), dry_run: bool = False):
    """体験期間終了した trial ユーザーを 'expired' に変更。毎日実行。
    自動課金は行わないので、何もしなければデータは保持されたまま失効する。"""
    if not CRON_SECRET:
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = db()
    c = conn.cursor()
    now = datetime.now(timezone.utc)
    # trial かつ trial_end 経過済みのユーザーを expired に
    c.execute(
        "SELECT id, name, email, trial_end FROM students WHERE status='trial' AND trial_end IS NOT NULL AND trial_end < ?",
        (now.isoformat(),)
    )
    candidates = list(c.fetchall())
    expired_ids = []
    for row in candidates:
        if dry_run:
            expired_ids.append({"id": row["id"], "email": row["email"]})
            continue
        c.execute("UPDATE students SET status='expired', updated_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
        expired_ids.append(row["id"])
    conn.commit()
    conn.close()
    log.info(f"Trial expiry: {len(expired_ids)} students marked as expired")
    return {"expired": len(expired_ids), "candidates": len(candidates), "preview": expired_ids if dry_run else None}


@app.post("/api/cron/trial-reminders")
def cron_trial_reminders(x_cron_secret: str = Header(None), dry_run: bool = False):
    """毎日1回外部cronから呼び出し。trial_end が 1-2 日先の生徒にリマインダー送信。
    notifications テーブルで重複送信防止。"""
    if not CRON_SECRET:
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = db()
    c = conn.cursor()
    now = datetime.now(timezone.utc)
    t_start = now + timedelta(hours=24)   # 24時間後以降
    t_end = now + timedelta(hours=48)     # 48時間以内
    # status='paid' はStripeトライアル中、'trial'はまだ未決済のトライアル
    c.execute(
        """SELECT id, name, email, trial_end, status FROM students
           WHERE status IN ('trial','paid') AND email IS NOT NULL
             AND trial_end IS NOT NULL
             AND trial_end > ? AND trial_end <= ?""",
        (t_start.isoformat(), t_end.isoformat())
    )
    candidates = list(c.fetchall())

    sent = 0
    skipped = 0
    preview = []
    for row in candidates:
        # 重複チェック: この生徒に trial_ending 通知を既に送っていたらスキップ
        c.execute(
            "SELECT id FROM notifications WHERE student_id=? AND template='trial_ending' AND success=1 LIMIT 1",
            (row["id"],)
        )
        if c.fetchone():
            skipped += 1
            continue
        # trial_end までの残日数を概算
        try:
            te = row["trial_end"]
            if isinstance(te, str):
                te = datetime.fromisoformat(te.replace("Z", "+00:00"))
            if te.tzinfo is None:
                te = te.replace(tzinfo=timezone.utc)
            days_left = max(1, int((te - now).total_seconds() / 86400))
        except Exception:
            days_left = 2
        if dry_run:
            preview.append({"student_id": row["id"], "email": row["email"], "days_left": days_left})
            continue
        result = _send_trial_ending_email(row["email"], row["name"] or "", days_left, f"{BASE_URL}/upgrade.html?email={row['email']}")
        c.execute(
            """INSERT INTO notifications (student_id, channel, template, payload, success, error)
               VALUES (?, 'email', 'trial_ending', ?, ?, ?)""",
            (row["id"], json.dumps({"days_left": days_left}), 1 if result.get("sent") else 0, result.get("error", ""))
        )
        if result.get("sent"):
            sent += 1
    conn.commit()
    conn.close()
    return {"sent": sent, "skipped": skipped, "candidates": len(candidates), "preview": preview if dry_run else None}


@app.post("/api/billing/portal-session")
def create_billing_portal_session(authorization: Optional[str] = Header(None)):
    """Stripe Customer Portal のURLを返す。有料ユーザーが解約・支払方法変更に使う。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = db()
    c = conn.cursor()
    c.execute("SELECT stripe_customer_id, status FROM students WHERE id=?", (student["id"],))
    row = c.fetchone()
    conn.close()
    if not row or not row["stripe_customer_id"]:
        raise HTTPException(status_code=400, detail="Stripe顧客情報がありません。お問い合わせください。")
    _stripe = get_stripe()
    if not _stripe:
        raise HTTPException(status_code=503, detail="決済サービスが利用できません")
    try:
        session = _stripe.billing_portal.Session.create(
            customer=row["stripe_customer_id"],
            return_url=f"{BASE_URL}/mypage.html",
        )
        return {"url": session.url}
    except Exception as e:
        log.error(f"Portal session create failed for student {student['id']}: {e}")
        raise HTTPException(status_code=500, detail="ポータル作成に失敗しました")


@app.post("/api/billing/cancel-trial")
def cancel_trial(authorization: Optional[str] = Header(None)):
    """解約: Stripe側で解約(成功時のみwebhookがstatus更新) or 純trial(Stripe顧客なし)ならDB直接更新。

    Stripe失敗を飲み込むと課金継続 & アクセス遮断の最悪事故になるため、
    失敗時はHTTPExceptionを投げる（DBには何も書かない）。
    """
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = db()
    c = conn.cursor()
    c.execute("SELECT stripe_customer_id, stripe_subscription_id, status FROM students WHERE id=?", (student["id"],))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    # Stripe有料購読中なら、Stripe経由で解約（webhookがstatus更新）
    if row["stripe_subscription_id"]:
        _stripe = get_stripe()
        if not _stripe:
            conn.close()
            raise HTTPException(status_code=503, detail="決済サービスが一時的に利用できません。しばらくしてから再度お試しください。")
        try:
            _stripe.Subscription.delete(row["stripe_subscription_id"])
            log.info(f"Stripe subscription canceled for student {student['id']}")
        except Exception as e:
            log.error(f"Stripe cancel failed for student {student['id']}: {type(e).__name__}: {e}")
            conn.close()
            raise HTTPException(
                status_code=502,
                detail="Stripeでの解約処理に失敗しました。お手数ですが info@trillion-ai-juku.com までお問い合わせください。"
            )
        # DB更新はStripe webhook (customer.subscription.deleted) が担当する。
        # ただしwebhook到達まで遅延があるためクライアントには即時成功を返す。
        conn.close()
        return {"ok": True, "message": "解約手続きを受け付けました。現在のご契約期間終了まではご利用いただけます。"}

    # 純trial (Stripe顧客なし) の場合のみDBを直接更新
    c.execute("UPDATE students SET status='canceled', updated_at=CURRENT_TIMESTAMP WHERE id=?", (student["id"],))
    conn.commit()
    conn.close()
    return {"ok": True, "message": "トライアルを解約しました。再契約をご希望の際はトライアル申込ページからお願いします。"}


@app.post("/api/cron/weekly-reports")
def cron_weekly_reports(x_cron_secret: str = Header(None), dry_run: bool = False):
    """毎週日曜20時に外部cronから呼び出し（GitHub Actions scheduled workflow）"""
    if not CRON_SECRET:
        log.error("CRON_SECRET not configured; refusing cron request")
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, line_user_id FROM students WHERE status IN ('trial', 'paid')")
    students = list(c.fetchall())
    conn.close()

    sent = 0
    skipped = 0
    previews = []
    for row in students:
        try:
            stats = _compute_weekly_stats(row["id"], days=7)
            # 活動が全くない週はスキップ（スパム防止）
            if stats["hours"] == 0 and stats["questions"] == 0 and stats["problems_done"] == 0:
                skipped += 1
                continue
            params = {
                "hours": stats["hours"],
                "accuracy": stats["accuracy"],
                "questions": stats["questions"],
                "url": f"{BASE_URL}/mypage.html",
            }
            if dry_run:
                previews.append({"student_id": row["id"], "name": row["name"], "stats": stats, "would_send_line": bool(row["line_user_id"])})
                continue
            if row["line_user_id"]:
                _do_line_push(row["id"], "weekly_report", params)
                sent += 1
        except Exception as e:
            log.error(f"Weekly report failed for {row['id']}: {e}")
    return {"sent": sent, "skipped": skipped, "total_students": len(students), "previews": previews if dry_run else None}


@app.post("/api/weekly-reports/preview")
def weekly_reports_preview(payload: dict, request: Request, x_stats_token: str = Header(None)):
    """塾長ダッシュボードから、特定生徒の今週レポートをプレビュー"""
    if not _origin_allowed(request):
        raise HTTPException(status_code=403, detail="Origin not allowed")
    # 塾長認証（STATS_TOKEN）
    if STATS_TOKEN and (not x_stats_token or not hmac.compare_digest(x_stats_token, STATS_TOKEN)):
        raise HTTPException(status_code=401, detail="Unauthorized")
    student_id = payload.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id required")
    stats = _compute_weekly_stats(int(student_id), days=int(payload.get("days", 7)))
    return {"ok": True, "stats": stats}


@app.post("/api/weekly-reports/send-one")
def weekly_reports_send_one(payload: dict, request: Request, x_stats_token: str = Header(None)):
    """塾長ダッシュボードから、特定生徒にレポートを即送信"""
    if not _origin_allowed(request):
        raise HTTPException(status_code=403, detail="Origin not allowed")
    if STATS_TOKEN and (not x_stats_token or not hmac.compare_digest(x_stats_token, STATS_TOKEN)):
        raise HTTPException(status_code=401, detail="Unauthorized")
    student_id = payload.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id required")
    stats = _compute_weekly_stats(int(student_id), days=7)
    params = {
        "hours": stats["hours"],
        "accuracy": stats["accuracy"],
        "questions": stats["questions"],
        "url": f"{BASE_URL}/mypage.html",
    }
    return _do_line_push(int(student_id), "weekly_report", params)

# ==========================================================================
# Routes: Analytics
# ==========================================================================
# ==========================================================================
# Routes: AI Proxy（塾長のAPIキーで全顧客のAI呼び出しを代理）
# 顧客は自分でAPIキーを設定不要。月謝に含まれるシームレスなUX。
# ==========================================================================
class AIProxyRequest(BaseModel):
    system: str
    messages: List[dict]
    model: Optional[str] = "claude-opus-4-7"
    max_tokens: Optional[int] = 2000
    thinking: Optional[bool] = False
    thinking_budget: Optional[int] = 4000
    kind: Optional[str] = "chat"
    student_id: Optional[int] = None

def _origin_allowed(request: Request) -> bool:
    """Origin/Referer が許可リストに含まれるか。サーバ間呼び出しを排除するため
    Origin または Referer のどちらかが ALLOWED_ORIGINS の接頭辞と一致することを要求。"""
    origin = (request.headers.get("origin") or "").rstrip("/")
    referer = request.headers.get("referer") or ""
    for allowed in ALLOWED_ORIGINS:
        a = allowed.rstrip("/")
        if origin == a or referer.startswith(a + "/") or referer == a:
            return True
    return False


def _verify_student_active(student_id: int) -> dict:
    """student_id が trial/paid で有効期限内なら student row (dict) を返す。
    無効なら HTTPException を raise。"""
    if not student_id or student_id <= 0:
        raise HTTPException(status_code=400, detail="student_id が必要です")
    conn = db()
    c = conn.cursor()
    c.execute(
        "SELECT id, status, trial_end, plan FROM students WHERE id = ?",
        (student_id,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="生徒が見つかりません")
    status = row["status"]
    if status == "paid":
        return dict(row)
    if status == "trial":
        # トライアル期限切れチェック（Postgres は datetime、SQLite は str で返す）
        trial_end_raw = row["trial_end"]
        if trial_end_raw:
            te = None
            if isinstance(trial_end_raw, str):
                try:
                    te = datetime.fromisoformat(trial_end_raw.replace("Z", "+00:00"))
                except ValueError:
                    te = None
            else:
                te = trial_end_raw  # datetime (Postgres)
            if te is not None:
                if te.tzinfo is None:
                    te = te.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > te:
                    raise HTTPException(status_code=403, detail="トライアル期間が終了しています。契約を継続してください。")
        return dict(row)
    raise HTTPException(status_code=403, detail=f"契約状態が無効です (status={status})")


def _check_ai_budget(student_id: int) -> None:
    """その生徒が直近24hで消費したAIトークンが AI_DAILY_TOKEN_BUDGET を超えていないか確認。"""
    # Postgres は TIMESTAMP (tz なし) カラムと tz 付き ISO 文字列の比較で
    # エラーを返すため、datetime オブジェクトをそのまま渡して psycopg に
    # 型変換を任せる（SQLite も datetime を受け付ける）。
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    conn = db()
    c = conn.cursor()
    # psycopg は % をプレースホルダ誤検知するため LIKE パターンもパラメータで渡す
    c.execute(
        """SELECT props FROM events
           WHERE session_id = ?
             AND name LIKE ?
             AND created_at > ?""",
        (str(student_id), 'ai_call_%', one_day_ago),
    )
    total = 0
    for row in c.fetchall():
        try:
            p = json.loads(row["props"] or "{}")
            total += int(p.get("input_tokens", 0)) + int(p.get("output_tokens", 0))
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    conn.close()
    if total >= AI_DAILY_TOKEN_BUDGET:
        raise HTTPException(
            status_code=429,
            detail=f"1日あたりのAI利用上限（{AI_DAILY_TOKEN_BUDGET:,}トークン）に達しました。明日またお試しください。",
        )


@app.post("/api/ai/call")
async def ai_proxy(payload: AIProxyRequest, request: Request):
    """顧客の全AI呼び出しを塾長のAPIキーで代理実行。
    Origin検証・student_id存在/有効性検証・1日あたりトークンbudgetで多層防御。"""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI サービスが構成されていません。管理者にお問い合わせください。",
        )

    # 1) Origin/Referer が許可ドメインか
    if not _origin_allowed(request):
        log.warning(
            f"/api/ai/call blocked by origin check: origin={request.headers.get('origin')} referer={request.headers.get('referer')} ip={request.client.host if request.client else '?'}"
        )
        raise HTTPException(status_code=403, detail="Origin not allowed")

    # 2-3) student_id と budget 検証。DBエラー時は 500 を裸文字列ではなく JSON で返す。
    try:
        _verify_student_active(payload.student_id)
        _check_ai_budget(payload.student_id)
    except HTTPException:
        raise  # 4xx はそのまま伝搬
    except Exception as e:
        log.error(f"/api/ai/call validation exception: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"validation error: {type(e).__name__}: {str(e)[:200]}")

    # 4) モデルとトークン数の上限ガード（異常値を弾く）。
    #    30〜50問の大量生成・市販参考書級のテキスト教材に対応するため 24000 まで許容。
    max_tokens = max(1, min(int(payload.max_tokens or 2000), 24000))

    # 5) Prompt Injection 緩和: system / messages のサイズと明白な jailbreak フレーズを弾く。
    #    完全な防御は不可能だが、学生端末を経由した塾のAPIキー横取り用途を大幅に抑制する。
    _JAILBREAK_PATTERNS = (
        "ignore previous", "ignore all prior", "disregard previous",
        "system prompt", "developer mode", "jailbreak",
        "you are now", "act as dan", "dan mode",
    )
    _sys = (payload.system or "")
    if len(_sys) > 6000:
        raise HTTPException(status_code=400, detail="system prompt too long")
    _sys_low = _sys.lower()
    if any(p in _sys_low for p in _JAILBREAK_PATTERNS):
        log.warning(f"/api/ai/call blocked by jailbreak pattern check: student_id={payload.student_id}")
        raise HTTPException(status_code=403, detail="prohibited system prompt")
    # messages 総長も上限（画像除く）
    _msg_text_total = 0
    for m in (payload.messages or []):
        content = m.get("content") if isinstance(m, dict) else None
        if isinstance(content, str):
            _msg_text_total += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    _msg_text_total += len(part.get("text") or "")
    if _msg_text_total > 40000:
        raise HTTPException(status_code=413, detail="messages too long")

    import urllib.request

    body = {
        "model": payload.model,
        "max_tokens": max_tokens,
        "system": payload.system,
        "messages": payload.messages,
    }
    if payload.thinking:
        # Claude Opus 4.7 は "enabled" thinking を受け付けず "adaptive" + output_config.effort を要求。
        # Sonnet 4.6 以下は "enabled" が依然有効なのでモデル名で分岐。
        if (payload.model or "").startswith("claude-opus-4-7"):
            # adaptive: effort は "low" / "medium" / "high" / "auto"。
            # thinking_budget (tokens) → effort への大雑把な換算
            budget = int(payload.thinking_budget or 4000)
            effort = "high" if budget >= 4000 else ("medium" if budget >= 1500 else "low")
            body["thinking"] = {"type": "adaptive"}
            body["output_config"] = {"effort": effort}
            body["temperature"] = 1.0
        else:
            body["temperature"] = 1.0
            body["thinking"] = {"type": "enabled", "budget_tokens": min(int(payload.thinking_budget or 4000), 16000)}

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        data=json.dumps(body).encode("utf-8"),
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Track cost per student (for CEO analytics)
        usage = data.get("usage", {})
        if payload.student_id and usage:
            conn = db()
            c = conn.cursor()
            c.execute(
                """INSERT INTO events (name, props, session_id)
                   VALUES (?, ?, ?)""",
                (
                    f"ai_call_{payload.kind}",
                    json.dumps({
                        "model": payload.model,
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                    }),
                    str(payload.student_id),
                ),
            )
            # Update last activity
            c.execute(
                "UPDATE students SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (payload.student_id,),
            )
            conn.commit()
            conn.close()

        return data
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")[:300]
        log.error(f"AI proxy error: {e.code} {err}")
        raise HTTPException(status_code=e.code, detail=err)
    except Exception as e:
        log.error(f"AI proxy exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/status")
def ai_status():
    """フロントエンドがバックエンドAI proxyの有無を確認"""
    return {
        "backend_ai_available": bool(ANTHROPIC_API_KEY),
        "hosted_mode": bool(ANTHROPIC_API_KEY),
    }

# ==========================================================================
# Routes: Auto-Alert System
# ==========================================================================
class AlertCheckRequest(BaseModel):
    threshold_days: int = 3

class AlertTestRequest(BaseModel):
    type: str
    destination: str

@app.post("/api/activity/log")
def log_activity(payload: dict, request: Request):
    """生徒の活動を記録（ログイン、質問、クエスト完了等）。
    無認証POSTでDB汚染（他人のupdated_at偽装、events爆撃）されないよう
    Origin検証＋生徒有効性検証＋サイズ上限を課す。"""
    if not _origin_allowed(request):
        raise HTTPException(status_code=403, detail="Origin not allowed")
    if len(json.dumps(payload)) > 4000:
        raise HTTPException(status_code=413, detail="payload too large")
    student_id = payload.get("student_id")
    activity_type = str(payload.get("type", "unknown"))[:64]
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id required")
    _verify_student_active(int(student_id))
    conn = db()
    c = conn.cursor()
    c.execute(
        "UPDATE students SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (student_id,)
    )
    c.execute(
        "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
        (f"activity_{activity_type}", json.dumps(payload), str(student_id))
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/api/alerts/check-inactivity")
def check_inactivity(payload: AlertCheckRequest, x_cron_secret: str = Header(None)):
    """外部cronから呼び出し、非活動生徒を検知してアラート送信"""
    if not CRON_SECRET:
        log.error("CRON_SECRET not configured; refusing cron request")
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    threshold_dt = datetime.now(timezone.utc) - timedelta(days=payload.threshold_days)
    conn = db()
    c = conn.cursor()
    # Find students inactive for N days（N日以上更新がない生徒）
    c.execute(
        """SELECT id, name, line_user_id, status, updated_at
           FROM students
           WHERE status IN ('trial', 'paid')
             AND updated_at <= ?""",
        (threshold_dt,)
    )
    inactive = c.fetchall()
    conn.close()

    now = datetime.now(timezone.utc)
    sent_count = 0
    for row in inactive:
        updated = row["updated_at"]
        if isinstance(updated, str):
            try:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if updated_dt.tzinfo is None:
                    updated_dt = updated_dt.replace(tzinfo=timezone.utc)
            except ValueError:
                updated_dt = now
        else:
            updated_dt = updated if updated.tzinfo else updated.replace(tzinfo=timezone.utc)
        days = int((now - updated_dt).total_seconds() / 86400)
        level = 3 if days >= 7 else 2 if days >= 5 else 1
        try:
            if row["line_user_id"]:
                template = "streak_reminder" if level == 1 else "trial_ending"
                _do_line_push(
                    row["id"],
                    template,
                    {"days_inactive": days, "streak": 0},
                )
                sent_count += 1
        except Exception as e:
            log.error(f"Alert send failed for student {row['id']}: {e}")

    return {"inactive_count": len(inactive), "sent": sent_count}

@app.post("/api/alerts/test")
def test_alert(payload: AlertTestRequest):
    """テスト配信"""
    log.info(f"Test alert dispatch: type={payload.type} dest={payload.destination}")
    # In production, actually send via LINE/Email
    return {"ok": True, "type": payload.type, "destination": payload.destination, "mock": not bool(LINE_CHANNEL_ACCESS_TOKEN)}

@app.post("/api/cron/daily-alerts")
def cron_daily_alerts(x_cron_secret: str = Header(None)):
    """毎日夜21時に外部cronから呼び出し、三段階の通知を自動実行"""
    if not CRON_SECRET:
        log.error("CRON_SECRET not configured; refusing cron request")
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check inactivity at 3/5/7 day thresholds
    results = {}
    for threshold, level in [(3, 1), (5, 2), (7, 3)]:
        r = check_inactivity(AlertCheckRequest(threshold_days=threshold), x_cron_secret)
        results[f"level_{level}"] = r
    return results

# ==========================================================================
# Routes: Problem Library (保存・再利用)
# ==========================================================================
@app.post("/api/problems/save")
def save_problem(payload: dict, request: Request):
    """生成した問題をDBに保存（後で再利用可能）。
    DB書込DoS/PII注入防止: Origin検証・サイズ上限・生徒存在確認。"""
    if not _origin_allowed(request):
        raise HTTPException(status_code=403, detail="Origin not allowed")
    if len(json.dumps(payload, ensure_ascii=False)) > 20000:
        raise HTTPException(status_code=413, detail="payload too large")
    sid = payload.get("student_id")
    if sid:
        try:
            _verify_student_active(int(sid))
        except HTTPException:
            pass  # student_id は任意。無効なら None として保存
    pk = "BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    conn = db()
    c = conn.cursor()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS problems (
            id {pk},
            subject TEXT,
            topic TEXT,
            difficulty TEXT,
            format TEXT,
            content TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute(
        """INSERT INTO problems (subject, topic, difficulty, format, content, created_by)
           VALUES (?, ?, ?, ?, ?, ?)
           RETURNING id""",
        (payload.get("subject"), payload.get("topic"), payload.get("difficulty"),
         payload.get("format"), payload.get("content"), payload.get("student_id"))
    )
    returned = c.fetchone()
    new_id = returned["id"] if returned else None
    conn.commit()
    conn.close()
    return {"ok": True, "problem_id": new_id}

@app.get("/api/problems/library")
def problem_library(subject: str = None, topic: str = None):
    """問題ライブラリから検索"""
    conn = db()
    c = conn.cursor()
    try:
        query = "SELECT id, subject, topic, difficulty, format, content, created_at FROM problems WHERE 1=1"
        args = []
        if subject:
            query += " AND subject LIKE ?"
            args.append(f"%{subject}%")
        if topic:
            query += " AND topic LIKE ?"
            args.append(f"%{topic}%")
        query += " ORDER BY created_at DESC LIMIT 100"
        c.execute(query, args)
        problems = [dict(row) for row in c.fetchall()]
    except sqlite3.OperationalError:
        problems = []
    conn.close()
    return {"problems": problems}

# ==========================================================================
# Routes: Parent portal signed tokens
# ==========================================================================
def _sign_parent_token(student_id: int, expires_at_unix: int) -> str:
    """HMAC署名付きの保護者トークンを生成。形式: base64url(payload).base64url(sig)
    payload = f"{student_id}:{expires_at_unix}"
    """
    if not APP_SECRET:
        raise HTTPException(status_code=503, detail="APP_SECRET not configured")
    payload = f"{student_id}:{expires_at_unix}".encode("utf-8")
    sig = hmac.new(APP_SECRET.encode("utf-8"), payload, hashlib.sha256).digest()
    p_b64 = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    s_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")
    return f"{p_b64}.{s_b64}"


def _verify_parent_token(token: str) -> Optional[int]:
    """トークンを検証して student_id を返す。無効または期限切れなら None。"""
    if not APP_SECRET or not token or "." not in token:
        return None
    try:
        p_b64, s_b64 = token.split(".", 1)
        pad = "=" * (-len(p_b64) % 4)
        payload = base64.urlsafe_b64decode(p_b64 + pad)
        pad = "=" * (-len(s_b64) % 4)
        sig = base64.urlsafe_b64decode(s_b64 + pad)
        expected = hmac.new(APP_SECRET.encode("utf-8"), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        student_id_str, exp_str = payload.decode("utf-8").split(":", 1)
        if int(exp_str) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return int(student_id_str)
    except (ValueError, TypeError, UnicodeDecodeError):
        return None


@app.post("/api/parent/token")
def issue_parent_token(payload: dict, x_stats_token: str = Header(None)):
    """保護者招待リンクを発行する。CEO専用のためSTATS_TOKEN認証。
    body: {"student_id": int, "days": int=30}
    """
    if not STATS_TOKEN:
        raise HTTPException(status_code=503, detail="Stats endpoint not configured")
    if not x_stats_token or not hmac.compare_digest(x_stats_token or "", STATS_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")
    student_id = int(payload.get("student_id", 0))
    days = int(payload.get("days", 30))
    if student_id <= 0:
        raise HTTPException(status_code=400, detail="student_id required")
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id FROM students WHERE id=?", (student_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
    conn.close()
    exp = int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())
    token = _sign_parent_token(student_id, exp)
    return {
        "token": token,
        "student_id": student_id,
        "expires_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat(),
        "parent_url": f"{BASE_URL}/?role=parent&token={token}",
    }


@app.get("/api/parent/verify")
def verify_parent_token(token: str):
    """保護者ビューが起動時に呼び出してトークン検証し、student_id を得る。"""
    student_id = _verify_parent_token(token)
    if student_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"ok": True, "student_id": student_id}


@app.post("/api/track")
def track_event(event: EventTrack, request: Request):
    if not _origin_allowed(request):
        raise HTTPException(status_code=403, detail="Origin not allowed")
    # event.name / event.props の長さ制限でDBスパム防止
    name = (event.name or "")[:128]
    props_str = json.dumps(event.props or {}, ensure_ascii=False)
    if len(props_str) > 4000:
        raise HTTPException(status_code=413, detail="props too large")
    conn = db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
        (name, props_str, event.session_id)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

# ==========================================================================
# Static file serving (frontend)
# ==========================================================================
@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "lp.html")

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
