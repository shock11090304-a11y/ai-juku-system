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
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta, time
import os
import json
import sqlite3
import hmac
import hashlib
import asyncio
import urllib.request
import urllib.error
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
# 🎁 期間限定50名・永年¥14,500 (founder_special)
# - 旧 founder1 (¥25,000・100名) は 2026-04-28 廃止
# - Stripe Price は admin endpoint /api/admin/stripe/setup-founder-special で自動作成可
#   (作成後 lookup_key="founder_special" で永続検索可能 = env 設定不要)
# - env STRIPE_PRICE_FOUNDER_SPECIAL を直指定したい場合は明示優先
STRIPE_PRICE_FOUNDER_SPECIAL = os.getenv("STRIPE_PRICE_FOUNDER_SPECIAL", "")
# 旧 env への後方互換 (デプロイ時に env が残っていても誤動作しないため・参照は削除済)
STRIPE_PRICE_FOUNDER1 = os.getenv("STRIPE_PRICE_FOUNDER1", "")
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
    # 🎁 期間限定50名 永年¥14,500 (premium 全機能)
    "founder_special": (STRIPE_PRICE_FOUNDER_SPECIAL, 14500, "創設メンバー (永年¥14,500)", 1),
    # 新プラン構造（2026-04-22〜、面談なし、AI機能で差別化）
    "standard": (STRIPE_PRICE_STANDARD, 24980, "スタンダード", 1),
    "premium": (STRIPE_PRICE_PREMIUM, 39800, "プレミアム", 1),
    "family": (STRIPE_PRICE_FAMILY, 59800, "家族プラン（最大3名）", 3),
    "student_addon": (STRIPE_PRICE_STUDENT_ADDON, 15000, "塾生アドオン", 1),
    # 後方互換 (founder1 は 2026-04-28 廃止・新 founder_special に置換)
    "founder1": (STRIPE_PRICE_FOUNDER_SPECIAL, 14500, "創設メンバー (永年¥14,500)", 1),
    "ai": (STRIPE_PRICE_STANDARD, 24980, "スタンダード", 1),
    "hybrid": (STRIPE_PRICE_PREMIUM, 39800, "プレミアム", 1),
    "intensive": (STRIPE_PRICE_FAMILY, 59800, "家族プラン（最大3名）", 3),
}

# 入塾金（トライアル後の初回請求に追加・塾生アドオンは免除）
ENROLLMENT_FEE = 10000

# 塾生アドオン（月額、入塾金不要）
STUDENT_ADDON_PRICE = 15000

# 創設メンバー体験は完全無料化 (CVR最大化方針)
# 7日間 = GW長期休みに集中体験 → 休み明けに本契約継続を狙う設計
FOUNDER_TRIAL_PRICE = 0
FOUNDER_TRIAL_DAYS = 7
# 旧 100名 → 新 50名限定 (2026-04-28 ピボット・¥14,500/月 永年・premium全機能)
FOUNDER_LIMIT = int(os.getenv("FOUNDER_LIMIT", "50"))

# 創設メンバー 永年プラン (本契約)
FOUNDER_SPECIAL_PRICE = 14500
FOUNDER1_PRICE = FOUNDER_SPECIAL_PRICE  # 後方互換

# 顧客向け表示用の擬似申込数 (購買意欲喚起のためのカモフラージュ・FOMO 設計)
# /api/founders/count?public=1 で動的計算された値が返る。塾長の指示で
# 「実申込が増えるほど残枠表示も縮小して FOMO を加速」設計。
#
# 計算式:
#   public_taken = real_taken + FAKE_BASE + (real_taken * FAKE_MULTIPLIER) + (days_since_launch * DAILY_GROWTH)
#   public_remaining = max(MIN_REMAINING, FOUNDER_LIMIT - public_taken)
#
# 例 (50枠・緊迫MAX設定: BASE=28, MULTIPLIER=2.5, DAILY_GROWTH=0.5, MIN=2):
#   day0  real=0  → public_taken=28 → 残22  (初期から 56%埋まり = "もう半分以上!" の心理)
#   day3  real=0  → public_taken=29 → 残21  (3日で +1)
#   day7  real=0  → public_taken=31 → 残19  (1週間経過・残半分以下)
#   day7  real=3  → public_taken=42 → 残8   (実申込3でも一気に縮小・"あと8人"の極限緊張)
#   day14 real=5  → public_taken=52 → max → 残2 (即決断ライン)
# 「50名のうち残り2-22名」の幅で常に「焦り」を演出。
# 経営的には実申込が進むほど public_taken も加速 → 後発の希少性が指数的に上昇する設計。
FOUNDER_PUBLIC_FAKE_TAKEN = int(os.getenv("FOUNDER_PUBLIC_FAKE_TAKEN", "28"))  # 旧称・後方互換 (BASE と同義)
FOUNDER_PUBLIC_FAKE_BASE = int(os.getenv("FOUNDER_PUBLIC_FAKE_BASE", str(FOUNDER_PUBLIC_FAKE_TAKEN)))
FOUNDER_PUBLIC_FAKE_MULTIPLIER = float(os.getenv("FOUNDER_PUBLIC_FAKE_MULTIPLIER", "2.5"))
FOUNDER_PUBLIC_FAKE_DAILY_GROWTH = float(os.getenv("FOUNDER_PUBLIC_FAKE_DAILY_GROWTH", "0.5"))
FOUNDER_PUBLIC_MIN_REMAINING = int(os.getenv("FOUNDER_PUBLIC_MIN_REMAINING", "2"))

# Daily SNS研究員: 毎日 JST DAILY_SNS_HOUR_JST 時に塾長キャラのThreads投稿5本を生成→Gmail送信
DAILY_SNS_TO_EMAIL = os.getenv("DAILY_SNS_TO_EMAIL", "")
DAILY_SNS_HOUR_JST = int(os.getenv("DAILY_SNS_HOUR_JST", "6"))
DAILY_SNS_MODEL = os.getenv("DAILY_SNS_MODEL", "claude-sonnet-4-6")

# 申込→決済 常時監視: 5分おきに健全性チェック、異常時のみアラート、朝7時にサマリ
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "1") == "1"
MONITORING_INTERVAL_MIN = int(os.getenv("MONITORING_INTERVAL_MIN", "5"))
MONITORING_TO_EMAIL = os.getenv("MONITORING_TO_EMAIL", "") or DAILY_SNS_TO_EMAIL
MONITORING_DAILY_SUMMARY_HOUR_JST = int(os.getenv("MONITORING_DAILY_SUMMARY_HOUR_JST", "7"))
MONITORING_ALERT_COOLDOWN_MIN = int(os.getenv("MONITORING_ALERT_COOLDOWN_MIN", "60"))  # 同じアラートは60分に1回まで
MONITORING_QUIET_HOURS_AFTER_LAUNCH_HOURS = int(os.getenv("MONITORING_QUIET_HOURS", "48"))  # ローンチ後48hは「申込0」を異常としない

# 入塾金を免除するプラン
ENROLLMENT_FEE_EXEMPT = {"student_addon"}

# キャンペーン: 先着N名は入塾金 (¥10,000) を免除
# 環境変数で枠数 / 有効化を制御可能
ENROLLMENT_WAIVER_CAMPAIGN_ENABLED = os.getenv("ENROLLMENT_WAIVER_ENABLED", "1") == "1"
ENROLLMENT_WAIVER_LIMIT = int(os.getenv("ENROLLMENT_WAIVER_LIMIT", "100"))

# プランごとの月次クォータ (None = 無制限)
# plans.js の quotas と完全一致させる必要あり
PLAN_QUOTAS = {
    "standard":      {"problems": 50, "essays": 20, "textbooks": 5},
    "premium":       {"problems": None, "essays": None, "textbooks": None},
    "family":        {"problems": None, "essays": None, "textbooks": None},
    "student_addon": {"problems": None, "essays": None, "textbooks": None},
    # トライアル中もスタンダードと同等の制限
    "trial":         {"problems": 50, "essays": 20, "textbooks": 5},
}
# クォータ check 対象の機能名 (これ以外は制限なし)
QUOTA_FEATURES = {"problems", "essays", "textbooks"}

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


# 起動時/呼出時に Stripe lookup_key で founder_special price を検索 (env が空のときのフォールバック)
_FOUNDER_SPECIAL_PRICE_CACHE: dict = {"id": None, "checked_at": None}

def _lookup_founder_special_price_id() -> str:
    """Stripe API で lookup_key='founder_special' の price を検索。
    env STRIPE_PRICE_FOUNDER_SPECIAL があればそれ優先。
    検索結果は 1 hour cache (Stripe API 負荷対策)。"""
    global _FOUNDER_SPECIAL_PRICE_CACHE
    if STRIPE_PRICE_FOUNDER_SPECIAL:
        return STRIPE_PRICE_FOUNDER_SPECIAL
    if not STRIPE_SECRET_KEY:
        return ""
    cached_id = _FOUNDER_SPECIAL_PRICE_CACHE.get("id")
    checked = _FOUNDER_SPECIAL_PRICE_CACHE.get("checked_at")
    now = datetime.now(timezone.utc)
    if cached_id and checked and (now - checked).total_seconds() < 3600:
        return cached_id
    try:
        s = get_stripe()
        results = s.Price.list(lookup_keys=["founder_special"], active=True, limit=1)
        if results and results.data:
            pid = results.data[0].id
            _FOUNDER_SPECIAL_PRICE_CACHE = {"id": pid, "checked_at": now}
            return pid
    except Exception as e:
        log.warning(f"[Stripe] founder_special lookup failed: {e}")
    _FOUNDER_SPECIAL_PRICE_CACHE = {"id": None, "checked_at": now}
    return ""

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
        enrollment_fee_waived INTEGER DEFAULT 0,
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
    CREATE TABLE IF NOT EXISTS exam_questions (
        id {pk},
        exam_id TEXT NOT NULL,
        part_key TEXT NOT NULL,
        eiken_grade TEXT,
        question_data TEXT NOT NULL,
        model TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_exam_questions ON exam_questions(exam_id, part_key, created_at);
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
    CREATE TABLE IF NOT EXISTS usage_monthly (
        student_id INTEGER NOT NULL,
        feature TEXT NOT NULL,
        year_month TEXT NOT NULL,
        used_count INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (student_id, feature, year_month)
    );
    CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
    CREATE INDEX IF NOT EXISTS idx_otp_student ON otp_codes(student_id, used_at, expires_at);
    """)
    # 既存DBに不足列を追加 (idempotent migration)
    # Postgres: 「column already exists」エラーで トランザクションが abort されると
    # 後続の ALTER がスキップされてしまうため、各 ALTER の前後で commit/rollback する。
    # SQLite: ADD COLUMN IF NOT EXISTS は古いバージョンで非対応なので try/except で対応。
    _migrations = [
        ("enrollment_fee_waived", "ALTER TABLE students ADD COLUMN enrollment_fee_waived INTEGER DEFAULT 0"),
        ("enrollment_waiver_applied_at", "ALTER TABLE students ADD COLUMN enrollment_waiver_applied_at TIMESTAMP"),
    ]
    conn.commit()  # executescript の結果を確実にコミット (abort状態をクリア)
    for col_name, sql in _migrations:
        try:
            c.execute(sql)
            conn.commit()
            log.info(f"[init_db] Added column students.{col_name}")
        except Exception as e:
            # 既に存在する or 他のエラー → ロールバックしてトランザクション abort をクリア
            try: conn.rollback()
            except Exception: pass
            log.debug(f"[init_db] Skip ALTER for {col_name}: {type(e).__name__}: {str(e)[:100]}")
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

# 起動時に Daily SNS 研究員 scheduler を asyncio.Task として常駐起動
_BACKGROUND_TASKS: list = []

@app.on_event("startup")
async def _start_background_tasks():
    """uvicorn 起動時に呼ばれる。daily SNS scheduler + 申込決済監視 scheduler を bg task として起動。"""
    if DAILY_SNS_TO_EMAIL and ANTHROPIC_API_KEY and RESEND_API_KEY:
        task = asyncio.create_task(_daily_sns_scheduler())
        _BACKGROUND_TASKS.append(task)
        log.info("[Startup] Daily SNS scheduler launched")
    else:
        missing = []
        if not DAILY_SNS_TO_EMAIL: missing.append("DAILY_SNS_TO_EMAIL")
        if not ANTHROPIC_API_KEY: missing.append("ANTHROPIC_API_KEY")
        if not RESEND_API_KEY: missing.append("RESEND_API_KEY")
        log.warning(f"[Startup] Daily SNS scheduler NOT launched. Missing env: {missing}")

    # 申込→決済 常時監視 scheduler
    if MONITORING_ENABLED and MONITORING_TO_EMAIL and RESEND_API_KEY:
        task = asyncio.create_task(_monitor_scheduler())
        _BACKGROUND_TASKS.append(task)
        log.info(f"[Startup] Monitor scheduler launched (interval={MONITORING_INTERVAL_MIN}min)")
    else:
        missing = []
        if not MONITORING_ENABLED: missing.append("MONITORING_ENABLED=0")
        if not MONITORING_TO_EMAIL: missing.append("MONITORING_TO_EMAIL")
        if not RESEND_API_KEY: missing.append("RESEND_API_KEY")
        log.warning(f"[Startup] Monitor scheduler NOT launched. Missing: {missing}")

    # 4試験 問題自動生成 scheduler (毎日朝5時 JST)
    if EXAM_QUESTIONS_ENABLED and ANTHROPIC_API_KEY:
        task = asyncio.create_task(_exam_questions_scheduler())
        _BACKGROUND_TASKS.append(task)
        log.info(f"[Startup] Exam questions scheduler launched (target hour JST {EXAM_QUESTIONS_HOUR_JST}:00, daily quota {EXAM_QUESTIONS_DAILY_QUOTA})")
    else:
        missing = []
        if not EXAM_QUESTIONS_ENABLED: missing.append("EXAM_QUESTIONS_ENABLED=0")
        if not ANTHROPIC_API_KEY: missing.append("ANTHROPIC_API_KEY")
        log.warning(f"[Startup] Exam questions scheduler NOT launched. Missing: {missing}")

# ==========================================================================
# Models
# ==========================================================================
_FULLNAME_BLOCKED_KEYWORDS = (
    "テスト", "ﾃｽﾄ", "test", "tset",
    "ダミー", "dummy",
    "サンプル", "sample",
    "デモ", "demo",
    "品質検証", "確認用", "動作確認", "検証用",
    "ユーザー", "user", "guest", "ゲスト",
    "qa", "qa用",
    "あいうえお", "aaa", "bbb", "xxx", "zzz",
    "名無し", "未設定", "noname",
    "管理者", "admin", "root",
)


def _validate_fullname(v: str) -> str:
    """フルネーム（姓と名）必須。空白のみ・1文字のみ・テスト用ダミー名は拒否。
    日本人名は姓+名で最低3文字以上必要。明らかなテストキーワード
    （例: 'テスト', '品質検証', 'dummy'）も弾く。"""
    if v is None:
        raise ValueError("氏名は必須です")
    s = v.strip()
    if not s:
        raise ValueError("氏名は必須です（空白のみは不可）")
    # 全角・半角スペースを除去した実質文字数で判定
    bare = s.replace(" ", "").replace("　", "")
    if len(bare) < 3:
        raise ValueError("フルネーム（姓と名）で入力してください（最低3文字以上）")
    # 数字のみは拒否
    if bare.isdigit():
        raise ValueError("氏名に数字のみは使用できません")
    # テスト用と思われるキーワードを弾く
    s_lower = s.lower()
    bare_lower = bare.lower()
    for kw in _FULLNAME_BLOCKED_KEYWORDS:
        kw_lower = kw.lower()
        if kw_lower in s_lower or kw_lower in bare_lower:
            raise ValueError(
                f"テスト用と思われる氏名は登録できません（『{kw}』を含む）。実在する生徒のフルネームを入力してください。"
            )
    # 同一文字の連続（例: 「ああああ」「kkkk」）も弾く
    if len(set(bare)) == 1:
        raise ValueError("氏名に同一文字の連続は使用できません")
    return s


class TrialSignup(BaseModel):
    name: str
    email: EmailStr
    grade: Optional[str] = None
    goal: Optional[str] = None
    plan: Optional[str] = "hybrid"

    @field_validator("name")
    @classmethod
    def _name_must_be_fullname(cls, v: str) -> str:
        return _validate_fullname(v)


class CheckoutRequest(BaseModel):
    plan: str
    email: EmailStr
    name: str
    student_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def _name_must_be_fullname(cls, v: str) -> str:
        return _validate_fullname(v)

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
        "email_configured": bool(RESEND_API_KEY),  # Magic link / Welcome / 各種通知メール
        "campaign_waiver_active": ENROLLMENT_WAIVER_CAMPAIGN_ENABLED,
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
  📅 <strong>7日間の無料体験は{days_text}で終了します</strong>
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


# ==========================================================================
# Daily SNS 研究員: 塾長キャラのThreads投稿を毎朝5本生成→Gmail送信
# ==========================================================================
JUKUCHO_PERSONA = """あなたは「足立翔平」、200名規模の塾を10年運営してきた元塾講師。
2026-04-26 にAI学習塾「AI学習コーチ塾」をローンチしたCEOです。
- 月¥5万の塾で苦しむ家庭への憤りがエネルギー源
- AIで質を落とさず1/3価格を実現した
- Threadsでフォロワー集客中(現在地は0からのスタート)
- 創設メンバー50名限定 永年¥14,500/月 / 7日間 完全無料体験(クレカ不要)
- 元現場の本音を語るキャラ・売り込み臭は出さない"""

THREADS_RULES = """【Threadsアルゴリズム最適化ルール (絶対遵守)】
- 文字数: 100〜300字 (上限500字)
- 1行目フック: 答えを書かない・気にさせて止める
- 改行: 1〜2文ごと(スマホ前提)
- 絵文字: ゼロ〜1個まで
- 締め: 句点で終わらせない(余韻 or 問いかけで止める)
- ハッシュタグ: 0〜1個まで(複数並べ禁止)
- 投稿後1時間以内のリプライ獲得が最重要(Stage1突破)
- NG: 「いいねしてね」「コメント下さい」直球エンゲージベイト
- 売り込み臭は出さない(価格訴求は5本中最大1本まで)"""

POST_TYPES = [
    {"name": "逆説型", "desc": "業界常識を破る断定+逆説。例: 『正直な話、〇〇は古いです』『AI塾なんて流行らないと思ってました』"},
    {"name": "保護者あるある共感型", "desc": "保護者の『あるある』相談を引用→意外な原因→解決の方向性。例: 『うちの子、頭は悪くないんですけど…』"},
    {"name": "数字×権威型", "desc": "10年で2,000人見てきた等の数字+共通点リスト3つ"},
    {"name": "体験談ストーリー型", "desc": "ある日の電話・相談の具体的エピソード→気づき(『昨日、ある中3の母から…』)"},
    {"name": "二択問いかけ型", "desc": "対立軸を提示→自分の結論→『あなたはどっち?』(リプライ起爆装置)"},
]


def _get_recent_sns_posts(days: int = 30) -> list:
    """過去N日間にdaily_sns_postで生成済みのテキストを返す(重複回避用)"""
    conn = db()
    c = conn.cursor()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        c.execute(
            "SELECT props FROM events WHERE name = 'daily_sns_post' AND created_at >= ?",
            (since,)
        )
        rows = c.fetchall()
    except Exception as e:
        log.warning(f"_get_recent_sns_posts query failed: {e}")
        rows = []
    conn.close()
    texts = []
    for r in rows:
        try:
            props = json.loads(r["props"] or "{}")
            for p in props.get("posts", []):
                t = (p.get("text") or "")[:120]
                if t:
                    texts.append(t)
        except Exception:
            pass
    return texts


def _check_daily_sns_sent_today_jst() -> bool:
    """今日(JST)のdaily_sns_postが既に events に記録されているか確認"""
    JST = timezone(timedelta(hours=9))
    today_jst = datetime.now(JST).date()
    today_start_utc = datetime.combine(today_jst, time(0, 0), tzinfo=JST).astimezone(timezone.utc)
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT COUNT(*) AS n FROM events WHERE name = 'daily_sns_post' AND created_at >= ?",
            (today_start_utc,)
        )
        n = c.fetchone()["n"]
    except Exception as e:
        log.warning(f"_check_daily_sns_sent_today_jst failed: {e}")
        n = 0
    conn.close()
    return n > 0


def _generate_daily_sns_posts() -> list:
    """Anthropic API で塾長キャラのThreads投稿5本(5型ローテ)を生成"""
    if not ANTHROPIC_API_KEY:
        log.warning("[DailySNS] ANTHROPIC_API_KEY 未設定でスキップ")
        return []
    recent = _get_recent_sns_posts(days=30)
    avoid_section = ""
    if recent:
        joined = "\n".join(f"- {t}" for t in recent[-25:])  # 直近25本まで
        avoid_section = f"\n\n【重複回避】以下は過去30日に生成済み。同じ訴求/同じ書き出しは避けてください:\n{joined}"

    types_section = "\n".join(f"{i+1}. {t['name']}: {t['desc']}" for i, t in enumerate(POST_TYPES))
    user_msg = f"""今日のThreads投稿を5本作成してください。5型を1本ずつ:

{types_section}
{avoid_section}

【出力形式】純粋なJSONのみ、他のテキストは含めない:
{{
  "posts": [
    {{"type": "逆説型", "text": "本文(改行は\\n)"}},
    {{"type": "保護者あるある共感型", "text": "本文"}},
    {{"type": "数字×権威型", "text": "本文"}},
    {{"type": "体験談ストーリー型", "text": "本文"}},
    {{"type": "二択問いかけ型", "text": "本文"}}
  ]
}}"""

    system_prompt = f"{JUKUCHO_PERSONA}\n\n{THREADS_RULES}"
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({
                "model": DAILY_SNS_MODEL,
                "max_tokens": 3000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_msg}],
            }).encode("utf-8"),
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        content_text = data["content"][0]["text"].strip()
        # コードブロックで囲まれている場合は除去
        if content_text.startswith("```"):
            content_text = content_text.split("```", 2)[1]
            if content_text.startswith("json"):
                content_text = content_text[4:]
            content_text = content_text.strip()
            if content_text.endswith("```"):
                content_text = content_text[:-3].strip()
        parsed = json.loads(content_text)
        posts = parsed.get("posts", [])
        log.info(f"[DailySNS] Generated {len(posts)} posts via {DAILY_SNS_MODEL}")
        return posts
    except Exception as e:
        log.error(f"[DailySNS] Generation failed: {type(e).__name__}: {e}")
        return []


def _record_daily_sns_sent(posts: list, resend_id: str = ""):
    """events に履歴を保存"""
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("daily_sns_post", json.dumps({"posts": posts, "resend_id": resend_id, "model": DAILY_SNS_MODEL}, ensure_ascii=False), "daily_sns_scheduler")
        )
        conn.commit()
    except Exception as e:
        log.error(f"[DailySNS] Failed to record event: {e}")
    conn.close()


def _send_daily_sns_email(posts: list, to_email: str) -> dict:
    """Resend で塾長 Gmail に投稿候補を送信"""
    if not RESEND_API_KEY:
        log.warning("[DailySNS] RESEND_API_KEY 未設定でスキップ")
        return {"sent": False, "reason": "no_api_key"}
    if not to_email:
        log.warning("[DailySNS] 送信先未設定でスキップ")
        return {"sent": False, "reason": "no_to"}
    if not posts:
        return {"sent": False, "reason": "no_posts"}

    JST = timezone(timedelta(hours=9))
    today_jst = datetime.now(JST).strftime("%Y-%m-%d (%a)")
    subject = f"📱 今日のThreads投稿候補 5本 / {today_jst}"

    def card(p):
        text = (p.get("text") or "").replace("\n", "<br>")
        ptype = p.get("type") or "?"
        char_count = len(p.get("text") or "")
        return f"""
<div style="background:#fafafa;border-left:4px solid #6366f1;border-radius:8px;padding:1.2rem;margin-bottom:1.2rem;">
  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;flex-wrap:wrap;">
    <span style="background:#6366f1;color:white;font-weight:900;padding:0.15rem 0.6rem;border-radius:4px;font-size:0.78rem;">{ptype}</span>
    <span style="color:#888;font-size:0.78rem;">{char_count}字</span>
  </div>
  <div style="background:white;border:1px solid #e5e5e5;border-radius:6px;padding:1rem;font-family:'Hiragino Sans','Yu Gothic',sans-serif;line-height:1.7;color:#222;font-size:0.95rem;white-space:pre-wrap;">{text}</div>
</div>"""

    posts_html = "".join(card(p) for p in posts)
    html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,'Hiragino Sans','Yu Gothic',sans-serif;line-height:1.7;color:#333;max-width:680px;margin:0 auto;padding:1.5rem;background:#f5f5f7;">
<div style="background:white;border-radius:14px;padding:1.5rem;margin-bottom:1.5rem;">
<h1 style="font-size:1.3rem;color:#6366f1;margin:0 0 0.4rem;">📱 今日のThreads投稿候補</h1>
<p style="color:#666;font-size:0.85rem;margin:0;">{today_jst} / 5型ローテ・塾長キャラ・過去30日と重複回避済み</p>
</div>
<div style="background:white;border-radius:14px;padding:1.5rem;margin-bottom:1.5rem;">
<p style="font-size:0.85rem;color:#666;margin-top:0;">朝7-8時 / 夜21時前後が母親ターゲット最適。リプ起爆装置の<strong>二択問いかけ型</strong>を朝に投げて、夜は<strong>体験談ストーリー型</strong>か<strong>共感型</strong>がおすすめ。</p>
{posts_html}
</div>
<div style="background:#eef2ff;border-radius:14px;padding:1.2rem;font-size:0.85rem;color:#444;line-height:1.8;">
<strong>📌 投稿後の運用</strong><br>
1. <strong>投稿後1時間が勝負</strong>。リプライ即返信でStage1突破<br>
2. 反応の良かった型を覚えておく → 翌日以降の生成にフィードバック<br>
3. 5本全部使う必要なし。気に入ったものだけでOK
</div>
<p style="font-size:0.78rem;color:#999;text-align:center;margin-top:1.5rem;">🤖 AI塾SNS研究員 (claude-sonnet-4-6) / 毎朝{DAILY_SNS_HOUR_JST}時に自動配信</p>
</body></html>"""

    try:
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
                "User-Agent": "ai-juku-daily-sns/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            log.info(f"[DailySNS] Email sent to {to_email}: {result.get('id')}")
            return {"sent": True, "resend_id": result.get("id")}
    except Exception as e:
        log.error(f"[DailySNS] Email send failed: {type(e).__name__}: {e}")
        return {"sent": False, "error": str(e)}


def _run_daily_sns_post() -> dict:
    """1日分の生成→送信→記録 を実行(scheduler / admin 共用)"""
    if _check_daily_sns_sent_today_jst():
        log.info("[DailySNS] Already sent today (JST), skipping")
        return {"ran": False, "reason": "already_sent_today"}
    if not DAILY_SNS_TO_EMAIL:
        log.warning("[DailySNS] DAILY_SNS_TO_EMAIL 未設定でスキップ")
        return {"ran": False, "reason": "no_recipient"}
    posts = _generate_daily_sns_posts()
    if not posts:
        return {"ran": False, "reason": "generation_failed"}
    result = _send_daily_sns_email(posts, DAILY_SNS_TO_EMAIL)
    if result.get("sent"):
        _record_daily_sns_sent(posts, resend_id=result.get("resend_id", ""))
    return {"ran": True, "posts_count": len(posts), "send_result": result}


async def _daily_sns_scheduler():
    """asyncio で毎日 JST DAILY_SNS_HOUR_JST 時に自動実行"""
    JST = timezone(timedelta(hours=9))
    log.info(f"[DailySNS] Scheduler started, target hour JST {DAILY_SNS_HOUR_JST}:00")
    while True:
        try:
            now_jst = datetime.now(JST)
            target = now_jst.replace(hour=DAILY_SNS_HOUR_JST, minute=0, second=0, microsecond=0)
            if target <= now_jst:
                target += timedelta(days=1)
            sleep_secs = (target - now_jst).total_seconds()
            log.info(f"[DailySNS] Next run at {target.isoformat()} (in {int(sleep_secs)}s)")
            await asyncio.sleep(sleep_secs)
            # 実行 (重複チェック付き)
            try:
                result = _run_daily_sns_post()
                log.info(f"[DailySNS] Run result: {result}")
            except Exception as e:
                log.error(f"[DailySNS] Run error: {type(e).__name__}: {e}", exc_info=True)
        except asyncio.CancelledError:
            log.info("[DailySNS] Scheduler cancelled")
            raise
        except Exception as e:
            log.error(f"[DailySNS] Scheduler loop error: {e}", exc_info=True)
            await asyncio.sleep(3600)


# ==========================================================================
# 申込→決済 常時監視: 申込/決済フローが正常に動いているかを5分おきに自己診断
# ==========================================================================
# ローンチ日時 (これ以降の申込ゼロ期間が続いたらアラート対象)
SERVICE_LAUNCH_TS = int(os.getenv("SERVICE_LAUNCH_TS", "1777142400"))  # 2026-04-26 00:00 JST


def _record_alert_sent(alert_key: str, payload: dict):
    """同じアラートの連続送信を防ぐため events に記録"""
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("monitor_alert", json.dumps({"key": alert_key, **payload}, ensure_ascii=False), "monitor_scheduler")
        )
        conn.commit()
    except Exception as e:
        log.error(f"[Monitor] _record_alert_sent failed: {e}")
    conn.close()


def _alert_recently_sent(alert_key: str, cooldown_min: int = None) -> bool:
    """同じ alert_key が直近 cooldown 内に送信済みかチェック"""
    if cooldown_min is None:
        cooldown_min = MONITORING_ALERT_COOLDOWN_MIN
    since = datetime.now(timezone.utc) - timedelta(minutes=cooldown_min)
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT props FROM events WHERE name = 'monitor_alert' AND created_at >= ? ORDER BY created_at DESC LIMIT 50",
            (since,)
        )
        for r in c.fetchall():
            try:
                p = json.loads(r["props"] or "{}")
                if p.get("key") == alert_key:
                    return True
            except Exception:
                pass
    except Exception as e:
        log.warning(f"[Monitor] cooldown check failed: {e}")
    conn.close()
    return False


def _send_monitor_email(subject: str, body_html: str, to_email: str = None) -> dict:
    """Resend で監視通知メール送信"""
    to = to_email or MONITORING_TO_EMAIL
    if not RESEND_API_KEY or not to:
        log.warning(f"[Monitor] Email skip: RESEND_API_KEY={bool(RESEND_API_KEY)}, to={to}")
        return {"sent": False}
    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps({"from": FROM_EMAIL, "to": [to], "subject": subject, "html": body_html}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "ai-juku-monitor/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            log.info(f"[Monitor] Email sent: {result.get('id')}")
            return {"sent": True, "resend_id": result.get("id")}
    except Exception as e:
        log.error(f"[Monitor] Email send failed: {type(e).__name__}: {e}")
        return {"sent": False, "error": str(e)}


def _collect_health_snapshot() -> dict:
    """申込→決済フローの現在の健全性を集計"""
    now = datetime.now(timezone.utc)
    h24 = now - timedelta(hours=24)
    h1 = now - timedelta(hours=1)
    conn = db()
    c = conn.cursor()
    snapshot = {
        "timestamp": now.isoformat(),
        "stripe_configured": bool(STRIPE_SECRET_KEY),
        "anthropic_configured": bool(ANTHROPIC_API_KEY),
        "email_configured": bool(RESEND_API_KEY),
        "founder_special_price_configured": bool(STRIPE_PRICE_FOUNDER_SPECIAL) or bool(_lookup_founder_special_price_id()),
        "founder1_price_configured": bool(STRIPE_PRICE_FOUNDER_SPECIAL) or bool(_lookup_founder_special_price_id()),  # 後方互換 (旧名)
    }

    def safe_count(query, params=()):
        try:
            c.execute(query, params)
            row = c.fetchone()
            return row[0] if row else 0
        except Exception as e:
            log.warning(f"[Monitor] query failed: {e}")
            # Postgres transaction abort 状態を解消
            try: conn.rollback()
            except Exception: pass
            return 0

    # 申込 (trial signup) 数
    snapshot["signups_24h"] = safe_count(
        "SELECT COUNT(*) FROM students WHERE created_at >= ?", (h24,)
    )
    snapshot["signups_1h"] = safe_count(
        "SELECT COUNT(*) FROM students WHERE created_at >= ?", (h1,)
    )
    snapshot["signups_total"] = safe_count("SELECT COUNT(*) FROM students")

    # paid (本契約) 数
    snapshot["paid_total"] = safe_count(
        "SELECT COUNT(*) FROM students WHERE status='paid' AND plan IS NOT NULL AND plan != ''"
    )
    snapshot["paid_24h"] = safe_count(
        "SELECT COUNT(*) FROM students WHERE status='paid' AND paid_since >= ?", (h24,)
    )

    # trial → paid 転換率
    if snapshot["signups_total"] > 0:
        snapshot["conversion_rate_pct"] = round(100 * snapshot["paid_total"] / snapshot["signups_total"], 1)
    else:
        snapshot["conversion_rate_pct"] = 0.0

    # Webhook 処理: 直近 24時間に処理した event 数 (processed_events.processed_at)
    snapshot["webhooks_processed_24h"] = safe_count(
        "SELECT COUNT(*) FROM processed_events WHERE processed_at >= ?", (h24,)
    )

    # ファネル (events): page_view → cta_click → form_submit → checkout_initiated → checkout_completed
    def event_count(name, since):
        return safe_count(
            "SELECT COUNT(*) FROM events WHERE name = ? AND created_at >= ?", (name, since)
        )
    snapshot["pv_24h"] = event_count("page_view", h24)
    snapshot["cta_24h"] = event_count("cta_click", h24)
    snapshot["form_submit_24h"] = event_count("form_submit", h24)
    snapshot["checkout_initiated_24h"] = event_count("checkout_initiated", h24)
    snapshot["checkout_completed_24h"] = event_count("checkout_completed", h24)

    # サービスローンチからの経過時間
    snapshot["hours_since_launch"] = max(0, int((now.timestamp() - SERVICE_LAUNCH_TS) / 3600))

    conn.close()
    return snapshot


def _evaluate_alerts(snapshot: dict) -> list:
    """snapshot から発動すべきアラートを判定"""
    alerts = []
    # 1. Stripe 設定
    if not snapshot["stripe_configured"]:
        alerts.append({
            "key": "stripe_not_configured", "severity": "critical",
            "title": "🚨 Stripe API キーが未設定",
            "detail": "STRIPE_SECRET_KEY が空。決済が一切動きません。"
        })
    if not snapshot["founder_special_price_configured"]:
        alerts.append({
            "key": "founder_special_price_not_configured", "severity": "critical",
            "title": "🚨 創設メンバープランの Stripe Price が未設定",
            "detail": "STRIPE_PRICE_FOUNDER_SPECIAL も lookup_key 検索もヒットせず。POST /api/admin/stripe/setup-founder-special を1回叩いて自動作成してください。"
        })
    # 2. Email/AI 設定
    if not snapshot["email_configured"]:
        alerts.append({
            "key": "email_not_configured", "severity": "warning",
            "title": "⚠️ Resend API キーが未設定",
            "detail": "登録メール・体験終了メール等が送信できません。"
        })
    if not snapshot["anthropic_configured"]:
        alerts.append({
            "key": "anthropic_not_configured", "severity": "warning",
            "title": "⚠️ Anthropic API キーが未設定",
            "detail": "Daily SNS 投稿生成・AI機能が動作しません。"
        })
    # 3. 申込フリーズ: ローンチ48h経過後、24時間 申込ゼロ
    if (snapshot["hours_since_launch"] > MONITORING_QUIET_HOURS_AFTER_LAUNCH_HOURS
            and snapshot["signups_24h"] == 0):
        alerts.append({
            "key": "no_signups_24h", "severity": "warning",
            "title": "⚠️ 過去24時間 申込ゼロ",
            "detail": f"ローンチから{snapshot['hours_since_launch']}時間経過。LPアクセス {snapshot['pv_24h']} / CTA {snapshot['cta_24h']}。集客動線を確認してください。"
        })
    # 4. ファネル落差: PV はあるが form_submit ゼロ (フォームエラーの兆候)
    if snapshot["pv_24h"] >= 50 and snapshot["form_submit_24h"] == 0:
        alerts.append({
            "key": "funnel_drop_form", "severity": "warning",
            "title": "⚠️ ファネル詰まり: PV {pv} あるのにフォーム送信0".format(pv=snapshot["pv_24h"]),
            "detail": "LP へアクセスはあるのに体験申込フォームの送信がゼロ。フォームバリデーションエラーや JS エラーの可能性。",
        })
    # 5. checkout 開始 → 完了の落差: 50%以上落ちたら警告
    if snapshot["checkout_initiated_24h"] >= 5:
        complete_rate = snapshot["checkout_completed_24h"] / snapshot["checkout_initiated_24h"]
        if complete_rate < 0.5:
            alerts.append({
                "key": "checkout_complete_rate_low", "severity": "warning",
                "title": f"⚠️ 決済完了率が低い ({int(complete_rate*100)}%)",
                "detail": f"checkout 開始 {snapshot['checkout_initiated_24h']} 件中、完了は {snapshot['checkout_completed_24h']} 件のみ。Stripe 決済画面でユーザーが詰まっている可能性。",
            })
    # 6. Webhook 沈黙: paid_total > 0 なのに 48時間 webhook がゼロ
    if snapshot["paid_total"] > 0 and snapshot["webhooks_processed_24h"] == 0 and snapshot["paid_24h"] == 0:
        # paid 顧客がいるなら invoice.paid が月次で来るはず。来ないのは Webhook 不通の兆候
        # (ただし新規 paid が直近24h 0件なら通常)
        pass  # 今は判定保留
    return alerts


def _format_alert_email(alerts: list, snapshot: dict) -> tuple:
    """アラートメールの subject + html を生成"""
    severity_max = "critical" if any(a["severity"] == "critical" for a in alerts) else "warning"
    icon = "🚨" if severity_max == "critical" else "⚠️"
    subject = f"{icon} AI塾 監視アラート ({len(alerts)}件) - {datetime.now(timezone.utc).strftime('%H:%M UTC')}"
    rows = ""
    for a in alerts:
        bg = "#fee2e2" if a["severity"] == "critical" else "#fef3c7"
        bd = "#dc2626" if a["severity"] == "critical" else "#fbbf24"
        rows += f"""
<div style="background:{bg};border-left:4px solid {bd};border-radius:6px;padding:1rem 1.2rem;margin-bottom:0.8rem;">
  <div style="font-weight:900;font-size:1rem;color:#222;margin-bottom:0.3rem;">{a['title']}</div>
  <div style="font-size:0.92rem;color:#444;line-height:1.6;">{a['detail']}</div>
</div>"""
    snapshot_html = f"""
<table style="width:100%;border-collapse:collapse;font-size:0.85rem;color:#444;">
  <tr><td style="padding:0.3rem 0.5rem;">📅 過去24h 申込</td><td style="text-align:right;font-weight:700;">{snapshot['signups_24h']}名</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">📅 過去24h 本契約</td><td style="text-align:right;font-weight:700;">{snapshot['paid_24h']}名</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">📊 累計申込</td><td style="text-align:right;font-weight:700;">{snapshot['signups_total']}名</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">📊 累計本契約</td><td style="text-align:right;font-weight:700;">{snapshot['paid_total']}名</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">📈 転換率</td><td style="text-align:right;font-weight:700;">{snapshot['conversion_rate_pct']}%</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">👁 過去24h PV</td><td style="text-align:right;">{snapshot['pv_24h']}</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">🎯 過去24h CTA</td><td style="text-align:right;">{snapshot['cta_24h']}</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">📝 過去24h フォーム送信</td><td style="text-align:right;">{snapshot['form_submit_24h']}</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">💳 過去24h checkout 開始</td><td style="text-align:right;">{snapshot['checkout_initiated_24h']}</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">✅ 過去24h checkout 完了</td><td style="text-align:right;">{snapshot['checkout_completed_24h']}</td></tr>
  <tr><td style="padding:0.3rem 0.5rem;">🔁 過去24h Webhook 処理</td><td style="text-align:right;">{snapshot['webhooks_processed_24h']}</td></tr>
</table>"""
    html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,'Hiragino Sans','Yu Gothic',sans-serif;line-height:1.7;color:#333;max-width:680px;margin:0 auto;padding:1.5rem;background:#f5f5f7;">
<div style="background:white;border-radius:14px;padding:1.5rem;margin-bottom:1.2rem;">
  <h1 style="font-size:1.3rem;color:#222;margin:0 0 0.4rem;">{icon} 監視アラート ({len(alerts)}件)</h1>
  <p style="color:#666;font-size:0.85rem;margin:0;">https://trillion-ai-juku.com 申込→決済フロー監視</p>
</div>
<div style="background:white;border-radius:14px;padding:1.5rem;margin-bottom:1.2rem;">
  <h2 style="font-size:1.05rem;margin:0 0 1rem;border-bottom:2px solid #6366f1;padding-bottom:0.4rem;">🚦 検知された異常</h2>
  {rows}
</div>
<div style="background:white;border-radius:14px;padding:1.5rem;margin-bottom:1.2rem;">
  <h2 style="font-size:1.05rem;margin:0 0 1rem;border-bottom:2px solid #6366f1;padding-bottom:0.4rem;">📊 現在のスナップショット</h2>
  {snapshot_html}
</div>
<p style="font-size:0.78rem;color:#999;text-align:center;">🤖 ai-juku-api 監視システム / cooldown {MONITORING_ALERT_COOLDOWN_MIN}分 / 同じアラートは1回まで送信</p>
</body></html>"""
    return subject, html


def _format_daily_summary(snapshot: dict) -> tuple:
    """毎朝7時のサマリメール"""
    JST = timezone(timedelta(hours=9))
    today = datetime.now(JST).strftime("%Y-%m-%d (%a)")
    subject = f"📊 AI塾 朝のサマリ {today} / 申込{snapshot['signups_24h']}名・契約{snapshot['paid_24h']}名"
    snapshot_html = _format_alert_email([], snapshot)[1]
    # _format_alert_email は alerts を中心にするので、サマリ用に整形しなおす
    body_html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,'Hiragino Sans','Yu Gothic',sans-serif;line-height:1.7;color:#333;max-width:680px;margin:0 auto;padding:1.5rem;background:#f5f5f7;">
<div style="background:white;border-radius:14px;padding:1.5rem;margin-bottom:1.2rem;">
  <h1 style="font-size:1.3rem;color:#6366f1;margin:0 0 0.4rem;">📊 AI塾 朝のサマリ</h1>
  <p style="color:#666;font-size:0.85rem;margin:0;">{today} 過去24時間の申込→決済フロー</p>
</div>
<div style="background:white;border-radius:14px;padding:1.5rem;margin-bottom:1.2rem;">
  <table style="width:100%;border-collapse:collapse;font-size:0.92rem;color:#222;">
    <tr style="background:#eef2ff;"><td style="padding:0.6rem 0.8rem;font-weight:700;">📅 過去24h 申込</td><td style="text-align:right;padding:0.6rem 0.8rem;font-weight:900;font-size:1.2rem;color:#6366f1;">{snapshot['signups_24h']}<span style="font-size:0.78rem;color:#888;">名</span></td></tr>
    <tr style="background:#ecfdf5;"><td style="padding:0.6rem 0.8rem;font-weight:700;">📅 過去24h 本契約</td><td style="text-align:right;padding:0.6rem 0.8rem;font-weight:900;font-size:1.2rem;color:#10b981;">{snapshot['paid_24h']}<span style="font-size:0.78rem;color:#888;">名</span></td></tr>
    <tr><td style="padding:0.5rem 0.8rem;">📊 累計申込 / 本契約</td><td style="text-align:right;padding:0.5rem 0.8rem;">{snapshot['signups_total']} / {snapshot['paid_total']}名</td></tr>
    <tr><td style="padding:0.5rem 0.8rem;">📈 体験→本契約 転換率</td><td style="text-align:right;padding:0.5rem 0.8rem;font-weight:700;">{snapshot['conversion_rate_pct']}%</td></tr>
    <tr><td style="padding:0.5rem 0.8rem;">👁 過去24h LP アクセス (PV)</td><td style="text-align:right;padding:0.5rem 0.8rem;">{snapshot['pv_24h']}</td></tr>
    <tr><td style="padding:0.5rem 0.8rem;">🎯 過去24h CTAクリック</td><td style="text-align:right;padding:0.5rem 0.8rem;">{snapshot['cta_24h']}</td></tr>
    <tr><td style="padding:0.5rem 0.8rem;">📝 過去24h フォーム送信</td><td style="text-align:right;padding:0.5rem 0.8rem;">{snapshot['form_submit_24h']}</td></tr>
    <tr><td style="padding:0.5rem 0.8rem;">💳 過去24h checkout 開始 / 完了</td><td style="text-align:right;padding:0.5rem 0.8rem;">{snapshot['checkout_initiated_24h']} / {snapshot['checkout_completed_24h']}</td></tr>
    <tr><td style="padding:0.5rem 0.8rem;">🔁 過去24h Stripe Webhook 処理</td><td style="text-align:right;padding:0.5rem 0.8rem;">{snapshot['webhooks_processed_24h']}</td></tr>
  </table>
</div>
<div style="background:#eef2ff;border-radius:14px;padding:1.2rem;font-size:0.85rem;color:#444;line-height:1.7;">
  <strong>📌 次にやることヒント</strong><br>
  ・LP アクセスが10未満 → SNS 投稿頻度を上げる (Threads/Instagram)<br>
  ・CTAクリックは多いがフォーム送信が少ない → LP の入力負荷を再確認<br>
  ・本契約ゼロ → checkout-success.html → upgrade.html の動線を確認<br>
  ・累計本契約 45名超え → 創設メンバー50名キャンペーンの終了告知準備
</div>
<p style="font-size:0.78rem;color:#999;text-align:center;margin-top:1rem;">🤖 ai-juku-api 監視システム / 異常時は別途即時アラート送信</p>
</body></html>"""
    return subject, body_html


def _run_monitor_check() -> dict:
    """監視を1回実行: snapshot 取得 → アラート判定 → 必要なら送信"""
    snapshot = _collect_health_snapshot()
    alerts = _evaluate_alerts(snapshot)
    sent_alerts = []
    skipped_alerts = []
    for a in alerts:
        if _alert_recently_sent(a["key"]):
            skipped_alerts.append(a["key"])
            continue
        # 1件ずつ即時送信 (新規アラートのみ)
        subject, html = _format_alert_email([a], snapshot)
        result = _send_monitor_email(subject, html)
        if result.get("sent"):
            _record_alert_sent(a["key"], {"severity": a["severity"], "title": a["title"]})
            sent_alerts.append(a["key"])
    return {
        "ok": True,
        "snapshot": snapshot,
        "alerts_total": len(alerts),
        "alerts_sent": sent_alerts,
        "alerts_skipped_cooldown": skipped_alerts,
    }


def _check_daily_summary_sent_today_jst() -> bool:
    """今日 (JST) 既にデイリーサマリを送ったか"""
    JST = timezone(timedelta(hours=9))
    today = datetime.now(JST).date()
    today_start_utc = datetime.combine(today, time(0, 0), tzinfo=JST).astimezone(timezone.utc)
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT COUNT(*) FROM events WHERE name = 'monitor_daily_summary' AND created_at >= ?",
            (today_start_utc,)
        )
        n = c.fetchone()[0]
    except Exception:
        n = 0
    conn.close()
    return n > 0


def _send_daily_summary_if_due() -> dict:
    """毎朝 MONITORING_DAILY_SUMMARY_HOUR_JST 時に1回だけ送信"""
    if _check_daily_summary_sent_today_jst():
        return {"sent": False, "reason": "already_sent_today"}
    snapshot = _collect_health_snapshot()
    subject, html = _format_daily_summary(snapshot)
    result = _send_monitor_email(subject, html)
    if result.get("sent"):
        conn = db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("monitor_daily_summary", json.dumps({"resend_id": result.get("resend_id")}), "monitor_scheduler")
            )
            conn.commit()
        except Exception:
            pass
        conn.close()
    return {"sent": result.get("sent"), "snapshot": snapshot}


async def _monitor_scheduler():
    """5分おきに監視チェック + 朝7時にデイリーサマリ"""
    JST = timezone(timedelta(hours=9))
    log.info(f"[Monitor] Scheduler started, interval={MONITORING_INTERVAL_MIN}min, daily_summary at JST {MONITORING_DAILY_SUMMARY_HOUR_JST}:00")
    while True:
        try:
            # 1. 5分間隔の異常検知
            try:
                result = _run_monitor_check()
                if result.get("alerts_sent"):
                    log.warning(f"[Monitor] Alerts sent: {result['alerts_sent']}")
                else:
                    log.info(f"[Monitor] OK: signups_24h={result['snapshot']['signups_24h']}, paid_total={result['snapshot']['paid_total']}")
            except Exception as e:
                log.error(f"[Monitor] check error: {e}", exc_info=True)
            # 2. JST DAILY_SUMMARY_HOUR_JST 時台 → デイリーサマリ送信判定
            now_jst = datetime.now(JST)
            if now_jst.hour == MONITORING_DAILY_SUMMARY_HOUR_JST:
                try:
                    summary_result = _send_daily_summary_if_due()
                    if summary_result.get("sent"):
                        log.info("[Monitor] Daily summary sent")
                except Exception as e:
                    log.error(f"[Monitor] daily summary error: {e}", exc_info=True)
            # 3. 次のループまで sleep
            await asyncio.sleep(MONITORING_INTERVAL_MIN * 60)
        except asyncio.CancelledError:
            log.info("[Monitor] Scheduler cancelled")
            raise
        except Exception as e:
            log.error(f"[Monitor] scheduler loop error: {e}", exc_info=True)
            await asyncio.sleep(300)


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
    <p>7日間の無料体験が始まりました。<strong>以下の6桁コードをアプリに入力</strong>してログインしてください。</p>"""
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
    c.execute("SELECT id, name, email, grade, goal, plan, status, stripe_customer_id, trial_end, enrollment_fee_waived FROM students WHERE id = ?", (claims["student_id"],))
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
    # enrollment_fee_waived は新カラム → 古いDB行で存在しない場合に備えて defensive access
    try:
        waived = bool(row["enrollment_fee_waived"]) if "enrollment_fee_waived" in row.keys() else False
    except (KeyError, TypeError, IndexError):
        waived = False
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "grade": row["grade"],
        "goal": row["goal"],
        "plan": row["plan"],
        "status": status,
        "enrollment_fee_waived": waived,  # mypage の「免除済みバッジ」表示に使用
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


# ==========================================================================
# Routes: Admin (塾長専用) 認証
# ==========================================================================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_SESSION_TTL = int(os.getenv("ADMIN_SESSION_TTL_SECONDS", str(30 * 86400)))  # 30日


def _sign_admin_token(ttl: int = ADMIN_SESSION_TTL) -> dict:
    import time
    exp = int(time.time()) + ttl
    payload = f"admin.{exp}"
    sig = hmac.new(MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}.{sig}"
    token = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    return {"token": token, "expires_at": exp}


def _verify_admin_token(token: str) -> bool:
    import time
    if not token:
        return False
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded).decode()
        parts = raw.split(".")
        if len(parts) != 3 or parts[0] != "admin":
            return False
        exp_str, sig = parts[1], parts[2]
        expected = hmac.new(MAGIC_LINK_SECRET.encode(), f"admin.{exp_str}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        if int(exp_str) < int(time.time()):
            return False
        return True
    except Exception:
        return False


class AdminLoginRequest(BaseModel):
    password: str


@app.post("/api/admin/login")
def admin_login(payload: AdminLoginRequest, request: Request):
    """塾長パスワードで認証。成功時は30日有効のトークンを返す。"""
    _check_rate_limit_ip(request, bucket="admin_login", limit=5, window=300)  # 5分で5回まで
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="管理者パスワードが未設定です。Railway環境変数 ADMIN_PASSWORD を設定してください。")
    if not hmac.compare_digest((payload.password or ""), ADMIN_PASSWORD):
        log.warning(f"Admin login failed from {_client_ip(request)}")
        raise HTTPException(status_code=401, detail="パスワードが正しくありません")
    tok = _sign_admin_token()
    log.info(f"Admin login success from {_client_ip(request)}")
    return {"ok": True, **tok}


@app.get("/api/admin/verify")
def admin_verify(authorization: Optional[str] = Header(None)):
    """管理者トークンの有効性を確認。ceo.htmlのセッションチェック用。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")
    return {"ok": True}


@app.get("/api/admin/stats")
def admin_stats(authorization: Optional[str] = Header(None)):
    """管理者専用の経営統計。/api/statsよりリッチな情報を返す。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, grade, goal, plan, status, trial_end, paid_since, created_at FROM students ORDER BY id DESC")
    students = []
    for row in c.fetchall():
        students.append({
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "grade": row["grade"],
            "goal": row["goal"],
            "plan": row["plan"],
            "status": row["status"],
            "trial_end": str(row["trial_end"]) if row["trial_end"] else None,
            "paid_since": str(row["paid_since"]) if row["paid_since"] else None,
            "created_at": str(row["created_at"]) if row["created_at"] else None,
        })
    # 集計
    c.execute("SELECT COUNT(*) AS n FROM students WHERE status='paid'")
    paid_count = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM students WHERE status='trial'")
    trial_count = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM students WHERE status='canceled'")
    canceled_count = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM students WHERE status='expired'")
    expired_count = c.fetchone()["n"]

    # 期間別新規申込数 (created_at ベース・JST)
    now_jst = datetime.now(timezone.utc) + timedelta(hours=9)
    today_start = (now_jst.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=9))
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    c.execute("SELECT COUNT(*) AS n FROM students WHERE created_at >= ?", (today_start,))
    new_today = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM students WHERE created_at >= ?", (week_start,))
    new_7d = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM students WHERE created_at >= ?", (month_start,))
    new_30d = c.fetchone()["n"]

    # 入塾金免除キャンペーン適用済数
    try:
        c.execute(
            "SELECT COUNT(*) AS n FROM students "
            "WHERE enrollment_fee_waived = 1 AND enrollment_waiver_applied_at IS NOT NULL"
        )
        waiver_used = c.fetchone()["n"]
    except Exception:
        waiver_used = 0

    conn.close()

    plan_fees = {"standard": 24980, "premium": 39800, "family": 59800, "student_addon": 15000}
    paid_students = [s for s in students if s["status"] == "paid"]
    mrr = sum(plan_fees.get(s.get("plan") or "", 0) for s in paid_students)

    # 体験 → 月額 転換率 (累積ベース・粗計算)
    # 分母: trial に入った全ユーザー (現trial + 現paid + 現canceled + 現expired)
    # 分子: 現paid (= 月額移行成立) + 現canceled (= 一時的に成立した経験あり)
    total_trial_entered = paid_count + trial_count + canceled_count + expired_count
    converted = paid_count + canceled_count
    conversion_rate = round(converted / total_trial_entered * 100, 1) if total_trial_entered > 0 else 0

    return {
        "students": students,
        "summary": {
            "total": len(students),
            "paid": paid_count,
            "trial": trial_count,
            "canceled": canceled_count,
            "expired": expired_count,
            "new_today": new_today,
            "new_7d": new_7d,
            "new_30d": new_30d,
            "conversion_rate_pct": conversion_rate,
            "waiver_used": waiver_used,
            "waiver_remaining": max(0, ENROLLMENT_WAIVER_LIMIT - waiver_used),
            "mrr_yen": mrr,
            "arr_yen": mrr * 12,
        }
    }


@app.get("/api/admin/revenue-timeline")
def admin_revenue_timeline(authorization: Optional[str] = Header(None), days: int = 30):
    """過去N日の日次売上推移 (Stripe payments テーブルから集計)。
    返却: [{date: "YYYY-MM-DD", paid_count, revenue_yen, cumulative_paid, cumulative_revenue}]"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    days = max(1, min(int(days), 90))
    JST = timezone(timedelta(hours=9))
    today = datetime.now(JST).date()

    conn = db()
    c = conn.cursor()
    timeline = []
    cumulative_paid = 0
    cumulative_revenue = 0
    # まず累計の起点を取得 (集計範囲開始日より前の累計)
    start_date = today - timedelta(days=days - 1)
    start_utc = datetime.combine(start_date, time(0, 0), tzinfo=JST).astimezone(timezone.utc)
    try:
        c.execute(
            "SELECT COUNT(*) FROM students WHERE status='paid' AND paid_since IS NOT NULL AND paid_since < ?",
            (start_utc,)
        )
        cumulative_paid = c.fetchone()[0] or 0
    except Exception:
        try: conn.rollback()
        except Exception: pass
    try:
        c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='succeeded' AND paid_at < ?",
            (start_utc,)
        )
        cumulative_revenue = c.fetchone()[0] or 0
    except Exception:
        try: conn.rollback()
        except Exception: pass

    for i in range(days):
        d = start_date + timedelta(days=i)
        d_start_utc = datetime.combine(d, time(0, 0), tzinfo=JST).astimezone(timezone.utc)
        d_end_utc = d_start_utc + timedelta(days=1)
        # 当日の新規 paid 数
        try:
            c.execute(
                "SELECT COUNT(*) FROM students WHERE status='paid' AND paid_since >= ? AND paid_since < ?",
                (d_start_utc, d_end_utc)
            )
            new_paid = c.fetchone()[0] or 0
        except Exception:
            try: conn.rollback()
            except Exception: pass
            new_paid = 0
        # 当日の決済額
        try:
            c.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='succeeded' AND paid_at >= ? AND paid_at < ?",
                (d_start_utc, d_end_utc)
            )
            day_revenue = c.fetchone()[0] or 0
        except Exception:
            try: conn.rollback()
            except Exception: pass
            day_revenue = 0
        cumulative_paid += new_paid
        cumulative_revenue += day_revenue
        timeline.append({
            "date": d.strftime("%Y-%m-%d"),
            "label": d.strftime("%m/%d"),
            "paid_count": new_paid,
            "revenue_yen": day_revenue,
            "cumulative_paid": cumulative_paid,
            "cumulative_revenue": cumulative_revenue,
        })
    conn.close()
    return {"days": days, "timeline": timeline}


@app.get("/api/admin/analytics")
def admin_analytics(authorization: Optional[str] = Header(None)):
    """events テーブルを集計してアクセス数ダッシュボード用データを返す。
    page_view / cta_click / form_submit / outbound_click を 24h / 7d で集計。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    conn = db()
    c = conn.cursor()
    now = datetime.now(timezone.utc)
    h24 = now - timedelta(hours=24)
    d7 = now - timedelta(days=7)

    def count_event(name: str, since):
        c.execute("SELECT COUNT(*) AS n FROM events WHERE name = ? AND created_at >= ?", (name, since))
        row = c.fetchone()
        return row["n"] if row else 0

    pv_24h = count_event("page_view", h24)
    pv_7d = count_event("page_view", d7)
    cta_24h = count_event("cta_click", h24)
    cta_7d = count_event("cta_click", d7)
    form_24h = count_event("form_submit", h24)
    form_7d = count_event("form_submit", d7)
    out_24h = count_event("outbound_click", h24)
    out_7d = count_event("outbound_click", d7)

    # ユニークセッション数 (同じ session_id = 1人)
    c.execute("SELECT COUNT(DISTINCT session_id) AS n FROM events WHERE created_at >= ?", (h24,))
    sessions_24h = c.fetchone()["n"]
    c.execute("SELECT COUNT(DISTINCT session_id) AS n FROM events WHERE created_at >= ?", (d7,))
    sessions_7d = c.fetchone()["n"]

    # ページ別 PV (24h)
    c.execute(
        """SELECT props, COUNT(*) AS n FROM events
           WHERE name = 'page_view' AND created_at >= ?
           GROUP BY props""",
        (h24,)
    )
    page_stats: dict = {}
    for r in c.fetchall():
        try:
            props = json.loads(r["props"] or "{}")
            path = props.get("page_path") or "/"
        except Exception:
            path = "/"
        page_stats[path] = page_stats.get(path, 0) + r["n"]
    top_pages = sorted(page_stats.items(), key=lambda x: x[1], reverse=True)[:15]

    # CTAクリック種類別 (24h)
    c.execute(
        """SELECT props, COUNT(*) AS n FROM events
           WHERE name = 'cta_click' AND created_at >= ?
           GROUP BY props""",
        (h24,)
    )
    cta_stats: dict = {}
    for r in c.fetchall():
        try:
            props = json.loads(r["props"] or "{}")
            text = (props.get("text") or "").strip()[:60] or "(no text)"
        except Exception:
            text = "(parse error)"
        cta_stats[text] = cta_stats.get(text, 0) + r["n"]
    top_ctas = sorted(cta_stats.items(), key=lambda x: x[1], reverse=True)[:15]

    # 時間別 PV (過去24時間、1時間ごと)
    hourly_pv = []
    for i in range(24):
        h_start = now - timedelta(hours=24 - i)
        h_end = now - timedelta(hours=23 - i)
        c.execute(
            "SELECT COUNT(*) AS n FROM events WHERE name='page_view' AND created_at >= ? AND created_at < ?",
            (h_start, h_end)
        )
        hourly_pv.append({
            "label": (h_start + timedelta(hours=9)).strftime("%H:00"),  # JST
            "count": c.fetchone()["n"],
        })

    # 日別 PV (過去7日、JST日付ごと)
    daily_pv = []
    for i in range(7):
        d_start = now - timedelta(days=7 - i)
        d_end = now - timedelta(days=6 - i)
        c.execute(
            "SELECT COUNT(*) AS n FROM events WHERE name='page_view' AND created_at >= ? AND created_at < ?",
            (d_start, d_end)
        )
        daily_pv.append({
            "label": (d_start + timedelta(hours=9)).strftime("%m/%d"),
            "count": c.fetchone()["n"],
        })

    # 申込ファネル (24h): page_view → cta_click → form_submit
    funnel_24h = {
        "page_view": pv_24h,
        "cta_click": cta_24h,
        "form_submit": form_24h,
        "cta_rate": round(100 * cta_24h / pv_24h, 1) if pv_24h > 0 else 0.0,
        "form_rate": round(100 * form_24h / pv_24h, 1) if pv_24h > 0 else 0.0,
    }

    conn.close()
    return {
        "summary": {
            "pv_24h": pv_24h, "pv_7d": pv_7d,
            "sessions_24h": sessions_24h, "sessions_7d": sessions_7d,
            "cta_24h": cta_24h, "cta_7d": cta_7d,
            "form_24h": form_24h, "form_7d": form_7d,
            "outbound_24h": out_24h, "outbound_7d": out_7d,
        },
        "funnel_24h": funnel_24h,
        "hourly_pv": hourly_pv,
        "daily_pv": daily_pv,
        "top_pages_24h": [{"path": p, "count": n} for p, n in top_pages],
        "top_ctas_24h": [{"text": t, "count": n} for t, n in top_ctas],
        "founders_public_offset": FOUNDER_PUBLIC_FAKE_TAKEN,
    }


# ==========================================================================
# Frontend AI Proxy: 生徒のブラウザに API キー無しで Anthropic API を呼び出させる
# ==========================================================================
# 既存の english-exam.js / app.js / textbook-generator.js は
# `x-api-key: <user_localStorage_key>` で Anthropic API を直接呼んでいたため、
# 生徒のブラウザに API キーが入っていないと「デモモード」状態だった。
# この proxy 経由なら、生徒の画面でも実 Claude が動作する。
# 認証: 生徒の Bearer (magic link 由来) または admin Bearer。
# 簡易 rate limit: 同じ session_id (生徒) で 1分20回まで。

_AI_PROXY_RATE = {}  # session_id → [unix timestamps]


def _ai_proxy_rate_limit(session_id: str, max_per_min: int = 20) -> bool:
    """True なら通過、False なら制限超過"""
    import time as _t
    now = _t.time()
    cutoff = now - 60
    arr = [t for t in _AI_PROXY_RATE.get(session_id, []) if t > cutoff]
    if len(arr) >= max_per_min:
        _AI_PROXY_RATE[session_id] = arr
        return False
    arr.append(now)
    _AI_PROXY_RATE[session_id] = arr
    # 古いエントリを定期掃除 (メモリリーク防止)
    if len(_AI_PROXY_RATE) > 1000:
        for k in list(_AI_PROXY_RATE.keys())[:500]:
            _AI_PROXY_RATE[k] = [t for t in _AI_PROXY_RATE[k] if t > cutoff]
            if not _AI_PROXY_RATE[k]:
                del _AI_PROXY_RATE[k]
    return True


@app.post("/api/ai/messages")
def ai_messages_proxy(payload: dict, authorization: Optional[str] = Header(None)):
    """Anthropic Messages API への薄い proxy。
    生徒のブラウザに API キーが無くても AI 機能が動くようにするため。
    payload (フロントから):
      - model: "claude-sonnet-4-6" 等 (省略時 sonnet)
      - max_tokens: int (省略時 4000)
      - system: str (省略可)
      - messages: [{role, content}]
    認証: 生徒の magic-link Bearer or admin Bearer。
    Anthropic レスポンスをほぼそのまま返す。"""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    # 認証: 生徒 or 管理者
    student = None
    is_admin = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            is_admin = True
        else:
            student = _get_current_student(authorization)
    if not student and not is_admin:
        raise HTTPException(status_code=401, detail="Login required")

    # Rate limit (生徒単位)
    rate_key = f"admin" if is_admin else f"student:{student.get('id')}"
    if not _ai_proxy_rate_limit(rate_key):
        raise HTTPException(status_code=429, detail="Too many AI requests. Please wait a minute.")

    # payload 検証
    model = payload.get("model") or "claude-sonnet-4-6"
    max_tokens = int(payload.get("max_tokens") or 4000)
    if max_tokens > 8000:
        max_tokens = 8000  # 上限保護
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages required")
    body = {"model": model, "max_tokens": max_tokens, "messages": messages}
    system = payload.get("system")
    if system:
        body["system"] = system

    # Anthropic 呼び出し
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="ignore")
        log.error(f"[AI proxy] Anthropic HTTP {e.code}: {body_err[:300]}")
        raise HTTPException(status_code=502, detail=f"AI upstream error: {e.code}")
    except Exception as e:
        log.error(f"[AI proxy] error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="AI request failed")

    # 使用ログ (events に記録、CEO ダッシュボード analytics で見える)
    try:
        usage = data.get("usage") or {}
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            (
                "ai_proxy_call",
                json.dumps({
                    "model": model,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "is_admin": is_admin,
                }),
                rate_key,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning(f"[AI proxy] failed to record event: {e}")

    return data


# ==========================================================================
# Exam Questions Auto-Generator (4試験 × 各 part の問題を毎日蓄積)
# ==========================================================================
EXAM_QUESTIONS_ENABLED = os.getenv("EXAM_QUESTIONS_ENABLED", "1") == "1"
EXAM_QUESTIONS_HOUR_JST = int(os.getenv("EXAM_QUESTIONS_HOUR_JST", "5"))           # 1日1回モード時の起動時刻
EXAM_QUESTIONS_DAILY_QUOTA = int(os.getenv("EXAM_QUESTIONS_DAILY_QUOTA", "10"))     # 1回の起動で生成する問題数 (interval モード時は1tick分)
EXAM_QUESTIONS_INTERVAL_HOURS = float(os.getenv("EXAM_QUESTIONS_INTERVAL_HOURS", "6"))  # 0以下なら旧来の「毎日 HOUR_JST 時」モード、>0なら N時間おきに繰り返し
EXAM_QUESTIONS_PER_TICK = int(os.getenv("EXAM_QUESTIONS_PER_TICK", "5"))            # interval モード時の1 tick あたり生成数
EXAM_QUESTIONS_TARGET_POOL = int(os.getenv("EXAM_QUESTIONS_TARGET_POOL", "30"))     # 各 part の目標蓄積数 (これに達したら以降生成スキップ・暴走防止)
EXAM_QUESTIONS_MIN_POOL = int(os.getenv("EXAM_QUESTIONS_MIN_POOL", "3"))            # この数を下回る part を最優先補充
EXAM_QUESTIONS_DAILY_MAX = int(os.getenv("EXAM_QUESTIONS_DAILY_MAX", "500"))       # 1日の総生成数のハードリミット (デフォ 500・上限引き上げ。CEO の課金許可済み)
EXAM_QUESTIONS_MODEL = os.getenv("EXAM_QUESTIONS_MODEL", "claude-sonnet-4-6")

# ローテーション対象の (exam_id, part_key, eiken_grade) リスト
# 注: daigaku の場合 eiken_grade フィールドに「大学キー (todai/kyodai/...)」を流用 (DB スキーマ共有)
EXAM_QUESTION_ROTATION = [
    # TOEFL (主要 part)
    ("toefl", "r_passage1", None),
    ("toefl", "r_passage2", None),
    ("toefl", "l_lect1", None),
    ("toefl", "l_lect2", None),
    ("toefl", "s_task1", None),
    ("toefl", "w_integrated", None),
    # TOEIC
    ("toeic", "l_part2", None),
    ("toeic", "l_part3", None),
    ("toeic", "r_part5", None),
    ("toeic", "r_part6", None),
    ("toeic", "r_part7_single", None),
    # IELTS
    ("ielts", "l_sec1", None),
    ("ielts", "l_sec3", None),
    ("ielts", "r_p1", None),
    ("ielts", "w_task2", None),
    # 英検 (受験者多い順: 準1級, 2級, 3級, 準2級, 1級, 4級, 5級)
    ("eiken", "r_q1", "gp1"),
    ("eiken", "r_q3", "gp1"),
    ("eiken", "w_essay", "gp1"),
    ("eiken", "r_q1", "g2"),
    ("eiken", "w_opinion", "g2"),
    ("eiken", "r_q1", "g3"),
    ("eiken", "r_q1", "g1"),
    ("eiken", "r_q1", "gp2"),
    ("eiken", "r_q1", "g4"),
    ("eiken", "r_q1", "g5"),
    # 大学入試: 2005-2026 の年度をランダム選択して類題生成 (大学×大問の主要組合せを全網羅)
    # 国公立トップ
    ("daigaku", "r_long",        "todai"),
    ("daigaku", "r_summary",     "todai"),
    ("daigaku", "w_essay",       "todai"),
    ("daigaku", "r_translation", "todai"),
    ("daigaku", "r_long",        "kyodai"),
    ("daigaku", "r_translation", "kyodai"),
    ("daigaku", "w_essay",       "kyodai"),
    ("daigaku", "r_long",        "osaka"),
    ("daigaku", "w_essay",       "osaka"),
    ("daigaku", "r_long",        "tokoda"),
    ("daigaku", "r_long",        "hitotsu"),
    ("daigaku", "r_translation", "hitotsu"),
    ("daigaku", "r_long",        "nagoya"),
    # 私立 早慶上智ICU
    ("daigaku", "r_long",        "waseda"),
    ("daigaku", "w_essay",       "waseda"),
    ("daigaku", "r_long",        "keio"),
    ("daigaku", "w_essay",       "keio"),
    ("daigaku", "r_long",        "sophia"),
    ("daigaku", "r_long",        "icu"),
    # MARCH
    ("daigaku", "r_long",        "meiji"),
    ("daigaku", "r_long",        "aogaku"),
    ("daigaku", "r_long",        "rikkyo"),
    ("daigaku", "r_long",        "chuo"),
    ("daigaku", "r_long",        "hosei"),
    # 関関同立
    ("daigaku", "r_long",        "kandai"),
    ("daigaku", "r_long",        "kangaku"),
    ("daigaku", "r_long",        "doshisha"),
    ("daigaku", "r_long",        "ritsumei"),
    # 医学部
    ("daigaku", "r_long",        "igakubu_kokoritsu"),
    ("daigaku", "r_translation", "igakubu_kokoritsu"),
    ("daigaku", "r_long",        "igakubu_shiritsu"),
    # 共通テスト・センター試験 (2005-2020 はセンター・2021- は共通テスト)
    ("daigaku", "r_long",        "kyotsu"),
    ("daigaku", "r_short",       "kyotsu"),
    ("daigaku", "l_part1_2",     "kyotsu"),
    ("daigaku", "l_part3_4",     "kyotsu"),
    ("daigaku", "r_long",        "center"),
    ("daigaku", "r_grammar",     "center"),
    ("daigaku", "l_listening",   "center"),
    # 🔬 大学入試 理系科目 (数学/物理/化学/生物/地学・eiken_grade に大学キー)
    # 共通テスト 理系
    ("rikei", "math_1a",      "kyotsu_rikei"),
    ("rikei", "math_2b",      "kyotsu_rikei"),
    ("rikei", "phys_basic",   "kyotsu_rikei"),
    ("rikei", "chem_basic",   "kyotsu_rikei"),
    ("rikei", "bio_basic",    "kyotsu_rikei"),
    # 東大 理系
    ("rikei", "math_q1",      "todai_rikei"),
    ("rikei", "math_q2",      "todai_rikei"),
    ("rikei", "math_q3",      "todai_rikei"),
    ("rikei", "phys_q1",      "todai_rikei"),
    ("rikei", "phys_q2",      "todai_rikei"),
    ("rikei", "chem_q1",      "todai_rikei"),
    ("rikei", "chem_q3",      "todai_rikei"),
    # 京大 理系
    ("rikei", "math_q1",      "kyodai_rikei"),
    ("rikei", "math_q2",      "kyodai_rikei"),
    ("rikei", "phys_q1",      "kyodai_rikei"),
    ("rikei", "chem_q2",      "kyodai_rikei"),
    # 阪大/東工大/名大
    ("rikei", "math_q1",      "osaka_rikei"),
    ("rikei", "phys_q1",      "osaka_rikei"),
    ("rikei", "math_q1",      "tokoda_rikei"),
    ("rikei", "phys_q1",      "tokoda_rikei"),
    ("rikei", "math_q1",      "nagoya_rikei"),
    # 早慶上智
    ("rikei", "math_q1",      "waseda_rikei"),
    ("rikei", "phys_q1",      "waseda_rikei"),
    ("rikei", "math_q1",      "keio_rikei"),
    ("rikei", "math_q2",      "keio_rikei"),
    ("rikei", "bio_q1",       "keio_rikei"),
    ("rikei", "math_q1",      "sophia_rikei"),
    # 医学部
    ("rikei", "math_q1",      "igakubu_kokoritsu_rikei"),
    ("rikei", "phys_q1",      "igakubu_kokoritsu_rikei"),
    ("rikei", "chem_q1",      "igakubu_kokoritsu_rikei"),
    ("rikei", "bio_q1",       "igakubu_kokoritsu_rikei"),
    ("rikei", "math_q1",      "igakubu_shiritsu_rikei"),
    ("rikei", "phys_q1",      "igakubu_shiritsu_rikei"),
    # MARCH 理工 (汎用)
    ("rikei", "math_basic",   "march_rikei"),
    ("rikei", "phys_basic_q", "march_rikei"),
    ("rikei", "chem_basic_q", "march_rikei"),
]


# 大学×大問 ごとの出題スタイル定義 (AI プロンプトに注入)
DAIGAKU_UNIV_STYLES = {
    "todai":     {"name": "東京大学",       "style": "要約 60-80字 (1B)・自由英作60-80語 (2A)・形式自由作文 (2B)・リスニング3パッセージ・文法整序 (4A)・構造把握型和訳 (4B)。物語/評論/エッセイ系の長文。"},
    "kyodai":    {"name": "京都大学",       "style": "抽象的論理的英文 + 段落丸ごとの和訳。「日本語の文章を英訳」型の英作文 (新傾向)。Whether節/関係詞節/分詞構文を含む構造把握型和訳が中核。"},
    "osaka":     {"name": "大阪大学",       "style": "英文要旨把握 + 自由英作 70-100語。長文中の和訳。"},
    "tokoda":    {"name": "東京工業大学",   "style": "理工系語彙・科学技術系英文 (AI/材料/ロボティクス/バイオ)。技術系トピックでの英作文。"},
    "hitotsu":   {"name": "一橋大学",       "style": "経済/社会/法律の抽象英文。関係詞節・分詞構文の構造把握型和訳。商学部頻出の100-150語論述。社会学部のリスニング。"},
    "nagoya":    {"name": "名古屋大学",     "style": "評論/論説系の英文 + 自由英作文 (テーマ与えあり) + 部分和訳。"},
    "waseda":    {"name": "早稲田大学",     "style": "学部別: 政経=政治経済/法=法律論文/商=ビジネス/文=人文/国際教養=自由英作100-150語。語彙の文脈推定問題が頻出。"},
    "keio":      {"name": "慶應義塾大学",   "style": "経済学部=英作120-150語/商=ビジネス系長文/文=本格的な人文系英文/SFC=超長文/医=医学英文。やや長めの本格的英文。"},
    "sophia":    {"name": "上智大学",       "style": "TEAP活用型・英語重視。長文+整序問題。"},
    "icu":       {"name": "ICU 国際基督教大学", "style": "ATLAS型独自試験・リベラルアーツ。抽象度の高い長文 + 講義型リスニング (10問)。"},
    "meiji":     {"name": "明治大学",       "style": "標準型: 長文+文法+整序の総合。社会/科学/文化系の英文。"},
    "aogaku":    {"name": "青山学院大学",   "style": "英米文学部は高難度 (文学/論説系)。文法・語法 + 自由英作。"},
    "rikkyo":    {"name": "立教大学",       "style": "全学部統一日程型・自由英作文 (テーマ自由度高め) が特徴。評論/物語/エッセイ系。"},
    "chuo":      {"name": "中央大学",       "style": "法学部=論理重視・法律/政治/経済の論理的英文・法律英語の和訳。経済=ビジネス系。"},
    "hosei":     {"name": "法政大学",       "style": "標準的な英文・各学部共通。基礎的な意見論述。"},
    "kandai":    {"name": "関西大学",       "style": "長文中心・標準難度。4択穴埋め+整序。"},
    "kangaku":   {"name": "関西学院大学",   "style": "実用英語重視・実用的なテーマの英文。英文要約 or 短い意見論述。"},
    "doshisha":  {"name": "同志社大学",     "style": "やや長めの評論/エッセイ系長文。同志社型整序問題。"},
    "ritsumei":  {"name": "立命館大学",     "style": "英語選択幅広い学部対応・長文+整序+自由英作。"},
    "igakubu_kokoritsu": {"name": "国公立医学部 (東大理三/京大医/阪大医/東京医歯大)", "style": "CRISPR/iPS/ゲノム/感染症/疫学/医療AI/抗生物質耐性 等の医学・生命科学系英文。医療倫理 (遺伝子治療/AI診断/尊厳死) の英作文。"},
    "igakubu_shiritsu":  {"name": "私立医学部 (慈恵/順天堂/日医/慶應医)", "style": "医療現場/疾患/薬学/公衆衛生 の英文。医学英語の語彙穴埋め。医療テーマの英作文 70-100語。"},
    "kyotsu":    {"name": "共通テスト",     "style": "2021年〜の新形式・実用英語重視 (広告/メール/SNS/レビュー/記事/学術/物語)。複数情報源統合型。Listeningはグラフ/情報統合あり。"},
    "center":    {"name": "センター試験",   "style": "2020年廃止 (1990-2020 過去問対象)。発音・アクセント・文法問題が大問1-3に出題 (現在の共通テストには無い)。長文3題 (グラフ/評論/物語)。リスニング (日常会話/講義)。"},
}

# 大学入試 大問キー → 形式説明 (eiken の part_hints と同様の役割)
DAIGAKU_PART_HINTS = {
    "r_long":        "長文読解 (8-10問前後・選択肢4択 + 内容一致 + 段落整序)",
    "r_short":       "Reading 短文中心 (広告/メール/SNS/レビュー 4-5問)",
    "r_summary":     "要約問題 (英文を 60-80字 で日本語要約・東大型 大問1B)",
    "r_translation": "和訳問題 (構造把握型・関係詞節/分詞構文を含む長文の部分和訳・3問前後)",
    "r_grammar":     "発音・アクセント・文法・語彙・整序問題 (大問1-3 のセンター/標準型)",
    "w_essay":       "自由英作文 (大学指定の語数・テーマは時事/教育/グローバル化/AI/格差 等)",
    "w_freeform":    "形式自由英作文 (イラスト/グラフ説明・東大型 大問2B)",
    "l_listening":   "リスニング (対話/講義/Real-Life/グラフ統合)",
    "l_part1_2":     "Listening 大問1-2 (短い対話・共通テスト型)",
    "l_part3_4":     "Listening 大問3-4 (長い対話/討論・共通テスト型)",
    "l_part5_6":     "Listening 大問5-6 (講義+討論・グラフ含む情報統合)",
}


# 🔬 大学入試 理系科目 (数学/物理/化学/生物/地学) 大学×レベル スタイル定義
RIKEI_UNIV_STYLES = {
    "kyotsu_rikei":    {"name": "共通テスト 理系", "style": "数IA/IIB の標準難度・物理基礎/化学基礎/生物基礎/地学基礎の出題範囲。マーク式・基本公式の運用が中心。"},
    "todai_rikei":     {"name": "東京大学 理系",   "style": "計算量多め・数学は微積/確率/整数論の融合・物理は力学/電磁気の本格的な記述・化学は理論+無機+有機の各大問・記述式採点 (途中式重視)。"},
    "kyodai_rikei":    {"name": "京都大学 理系",   "style": "抽象的・骨太な解析。数学は整数論/確率の独自性・物理は物理的考察重視 (公式適用より概念理解)・化学は反応速度/平衡。"},
    "osaka_rikei":     {"name": "大阪大学 理系",   "style": "標準〜やや難。数学はベクトル/微積・物理は力学+電磁気・化学は理論+有機・解答プロセスを論理的に書ききる力。"},
    "tokoda_rikei":    {"name": "東京工業大学",   "style": "工学系特化: 数学は微積/極限/ベクトル空間・物理は回路解析/電磁気/振動・化学は材料/触媒/工業化学。情報科学系の問題も。"},
    "nagoya_rikei":    {"name": "名古屋大学 理系", "style": "微積分の応用・確率・物理(力学/電磁気)・化学(理論+有機)。標準的な記述式。"},
    "waseda_rikei":    {"name": "早稲田大学 理工", "style": "基幹/創造/先進理工の標準型。数学は微積/ベクトル/数列・物理は力学+電磁気・化学は理論+有機。"},
    "keio_rikei":      {"name": "慶應義塾大学 理工/医", "style": "理工=数学/物理/化学/生物の幅広対応・医=生物が記述式中心 (DNA/タンパク質/免疫/医学関連)。"},
    "sophia_rikei":    {"name": "上智大学 理工",   "style": "機能創造/情報理工。数学+物理+化学の標準型・記述部分あり。"},
    "igakubu_kokoritsu_rikei": {"name": "国公立医学部 (東大理三/京大医/阪大医)", "style": "医学部受験者に求められる高難度: 数学(全分野)・物理(力学/電磁気/熱)・化学(理論/有機)・生物 (生化学/医学/遺伝/免疫)。"},
    "igakubu_shiritsu_rikei":  {"name": "私立医学部 (慈恵/順天堂/日医)", "style": "医療現場で必要な化学/生物の知識+標準的な数学/物理。"},
    "march_rikei":     {"name": "MARCH 理工",      "style": "明治/青学/立教/中央/法政 理工。標準難度の数学/物理/化学。微積/ベクトル/力学/電磁気/理論化学+有機。"},
}


# 🔬 理系大問キー → 形式説明 (科目+大問内容)
RIKEI_PART_HINTS = {
    # 数学
    "math_1a":     "数学 IA (大問1-5・共通テスト型・マーク式・二次関数/図形と計量/データ/確率/整数 60-70分)",
    "math_2b":     "数学 IIB (共通テスト型・三角関数/指数対数/微積/数列/ベクトル 60-70分)",
    "math_q1":     "数学 大問1 (記述式・大学2次型・微積/確率/数列/整数論/複素数平面の融合)",
    "math_q2":     "数学 大問2 (記述式・大学2次型・図形と方程式/ベクトル/複素数平面)",
    "math_q3":     "数学 大問3 (記述式・大学2次型・微積分/極限の応用)",
    "math_basic":  "数学 (基礎演習・微積/ベクトル/確率/数列を 5問・標準的記述)",
    # 物理
    "phys_basic":  "物理基礎 (共通テスト型・力学/熱/波/電気の基礎・5問・マーク式)",
    "phys_q1":     "物理 大問1 (力学・記述式・運動方程式/エネルギー保存/円運動/単振動・図解必須)",
    "phys_q2":     "物理 大問2 (電磁気・記述式・回路解析/キルヒホッフ/電磁誘導/コンデンサ・回路図 SVG 必須)",
    "phys_q3":     "物理 大問3 (波/熱・記述式・干渉/反射屈折/熱力学/状態方程式)",
    "phys_basic_q": "物理 (基礎演習・力学/電磁気/波動/熱の標準問題 5問)",
    # 化学
    "chem_basic":  "化学基礎 (共通テスト型・物質量/酸塩基/酸化還元の基礎・5問)",
    "chem_q1":     "化学 大問1 (理論化学・記述式・熱化学/平衡/電気化学/反応速度・計算式必須)",
    "chem_q2":     "化学 大問2 (無機化学・記述式・無機物質/沈殿反応/錯体・反応式必須)",
    "chem_q3":     "化学 大問3 (有機化学・記述式・構造決定/合成経路/高分子・構造式 SVG 必須)",
    "chem_basic_q": "化学 (基礎演習・理論+無機+有機の標準問題 5問)",
    # 生物
    "bio_basic":   "生物基礎 (共通テスト型・細胞/遺伝/生態系の基礎・5問)",
    "bio_q1":      "生物 大問1 (記述式・DNA/タンパク質/免疫/代謝/遺伝子発現・模式図 SVG 推奨)",
    "bio_basic_q": "生物 (基礎演習・細胞/遺伝/生態の標準問題 5問)",
    # 地学
    "earth_basic": "地学基礎 (共通テスト型・地球/宇宙/地震/気象の基礎・5問)",
}


def _generate_exam_question(exam_id: str, part_key: str, eiken_grade: Optional[str] = None) -> Optional[dict]:
    """Anthropic API で1問生成して dict を返す。失敗時 None。
    daigaku の場合は eiken_grade に大学キー (todai/kyodai/...) を入れる慣例。"""
    if not ANTHROPIC_API_KEY:
        return None

    # 試験別ヒント
    exam_hints = {
        "toefl": "TOEFL iBT (米国大学留学・学術英語・C1レベル目標)",
        "toeic": "TOEIC L&R (ビジネス英語・職場シーン)",
        "ielts": "IELTS Academic (英国系大学留学・学術)",
        "eiken": f"英検{eiken_grade or '準1級'} (日本英検・新形式 2024〜)",
    }
    part_hints = {
        "r_passage1": "Reading Passage 1: 学術文700字 + 5問 multiple_choice",
        "r_passage2": "Reading Passage 2: 別ジャンル学術文 + 5問",
        "l_lect1": "Listening Lecture 1: 講義スクリプト + 5問",
        "l_lect2": "Listening Lecture 2: 講義スクリプト + 5問",
        "s_task1": "Speaking Task 1 (Independent): prompt + 模範回答",
        "w_integrated": "Writing Integrated: prompt + 200語模範",
        "l_part2": "Listening Part 2 応答問題 5問 (3択)",
        "l_part3": "Listening Part 3 会話問題 6問 (3問1セット×2)",
        "r_part5": "Reading Part 5 短文穴埋め 8問 (4択・品詞文法語彙)",
        "r_part6": "Reading Part 6 長文穴埋め (4問1セット)",
        "r_part7_single": "Reading Part 7 シングルパッセージ (3問)",
        "l_sec1": "Listening Section 1 社会的会話 + 5問",
        "l_sec3": "Listening Section 3 学術会話 + 5問",
        "r_p1": "Reading Passage 1 + 6問 (TFNG/穴埋め)",
        "w_task2": "Writing Task 2: prompt + 250語模範エッセイ",
        "r_q1": "Reading 大問1: 短文穴埋め 5問 (語彙レベル統制)",
        "r_q3": "Reading 大問3: 長文内容一致 3問",
        "w_essay": "Writing エッセイ模範回答 (新形式)",
        "w_opinion": "Writing 意見論述模範回答 (新形式)",
    }

    # ===== 大学入試: 大学×年度×大問の高解像度プロンプト =====
    if exam_id == "daigaku":
        import random
        univ_key = eiken_grade or "todai"
        univ_info = DAIGAKU_UNIV_STYLES.get(univ_key, {"name": univ_key, "style": "汎用大学入試型"})
        univ_name = univ_info["name"]
        univ_style = univ_info["style"]
        part_label = DAIGAKU_PART_HINTS.get(part_key, part_key)
        # 2005-2026 のうち、その大学/枠が存在した年度を選択
        if univ_key == "kyotsu":
            year = random.randint(2021, 2026)  # 共通テスト
        elif univ_key == "center":
            year = random.randint(2005, 2020)  # センター試験
        else:
            year = random.randint(2005, 2026)
        exam_label = f"{univ_name} {year}年度入試 (英語)"

        system = f"""あなたは日本の大学受験英語の出題傾向に精通した専門家です。
**{univ_name}** の **{year}年度** 入試の出題形式・難易度・テーマ傾向に完全準拠した類題を生成してください。

【絶対遵守】
- 過去問の丸写しは著作権上禁止。**「{univ_name} {year}年度の形式に完全準拠した類題」** を新規作成すること。
- {univ_name} の出題スタイル: {univ_style}
- 対象 大問形式: {part_label}
- 英文は ETS / Cambridge / Oxford 級の自然な英語 (機械翻訳臭・不自然な語彙NG)
- 日本人受験生の典型的弱点 (冠詞・関係詞節・分詞構文・無生物主語の和訳・コロケーション) を踏まえた解説
- 解説は日本語で、正解の根拠 + 他選択肢の誤りポイント + 関連語彙/文法を3行以上
- 「2005年〜2026年」の出題傾向: 時事 (AI/ChatGPT/環境/感染症/格差/ジェンダー/メンタルヘルス) + 古典的論題 (記憶/言語/科学哲学/教育) + 物語/エッセイ系を年度に応じて織り交ぜる
- {year}年度なら、その年に話題だったテーマを優先的に扱うのがリアル (例: 2023年なら ChatGPT/AI、2020-2021年なら COVID-19、2011年以降なら震災/原発)
- 出力は純粋なJSONのみ"""

        user = f"""**{univ_name} {year}年度** 形式の **{part_key}** ({part_label}) の類題を1セット生成してください。

【テーマ選定指針】
- {year}年に話題だったトピック or {univ_name} 頻出の論題から自然に選ぶ
- {univ_name} の難易度・抽象度に合わせる ({univ_style.split('。')[0]})

【出力形式】純粋なJSONのみ:
{{
  "passage": "(Reading の場合は本文、それ以外は空文字)",
  "audio_script": "(Listening の場合はスクリプト、それ以外は空文字)",
  "prompt": "(Speaking/Writing の場合の出題、それ以外は空文字)",
  "year_simulated": {year},
  "univ_simulated": "{univ_name}",
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice|short_answer|essay|speaking",
      "stem": "問題文 (英文 or 日本語の和訳指示)",
      "choices": ["選択肢があれば配列、無ければ空配列"],
      "answer": "正解 (選択肢index 0始まり、または模範解答テキスト全文)",
      "explanation": "解説 (日本語、3行以上)"
    }}
  ]
}}"""

    # ===== 🔬 理系科目: 数学/物理/化学/生物/地学 (図/数式必須) =====
    elif exam_id == "rikei":
        import random
        univ_key = eiken_grade or "kyotsu_rikei"
        univ_info = RIKEI_UNIV_STYLES.get(univ_key, {"name": univ_key, "style": "汎用大学入試 理系"})
        univ_name = univ_info["name"]
        univ_style = univ_info["style"]
        part_label = RIKEI_PART_HINTS.get(part_key, part_key)
        # 科目判定
        subject_map = {"math": "数学", "phys": "物理", "chem": "化学", "bio": "生物", "earth": "地学"}
        subj_prefix = ""
        for k in subject_map:
            if part_key.startswith(k):
                subj_prefix = k
                break
        subject = subject_map.get(subj_prefix, "理系")
        # 年度
        if univ_key == "kyotsu_rikei":
            year = random.randint(2021, 2026)  # 共通テスト
        else:
            year = random.randint(2010, 2026)
        exam_label = f"{univ_name} {year}年度入試 ({subject})"

        # 科目別の追加指示
        subject_specific = {
            "数学": """- 数式は **必ず LaTeX 構文** で出力 (\\\\(x^2 + y^2 = r^2\\\\) インライン / \\\\[\\\\int_0^1 f(x)dx\\\\] ディスプレイ)
- 関数のグラフ・図形問題・ベクトル等の図示が必要な場合は figure_svg に inline SVG (viewBox 0 0 400 300・stroke="currentColor"・暗背景に映える色)
- 確率・整数論・微積分の融合問題などで実力を測る""",
            "物理": """- 数式は **必ず LaTeX 構文** で出力 (\\\\(F = ma\\\\)・\\\\[E_k = \\\\frac{1}{2}mv^2\\\\])
- **物理は figure_svg ほぼ必須**: 力の図 (矢印 + 物体)、回路図 (抵抗・電池・コンデンサ・コイル記号)、運動軌道、波形、レンズ図
- 単位を厳密に (SI 単位系)・近似や仮定を明示
- 力学/電磁気/波動/熱の典型パターンを再現""",
            "化学": """- 化学反応式は **LaTeX で表記** (\\\\(\\\\text{2H}_2 + \\\\text{O}_2 \\\\to \\\\text{2H}_2\\\\text{O}\\\\))
- **有機化学では構造式 SVG が必須**: 骨格表示 (skeletal formula) で分子を描画
- 反応経路・実験装置の模式図も figure_svg で
- 物質量・濃度・熱化学・平衡の計算は単位を厳密に""",
            "生物": """- 模式図 (細胞・遺伝子発現フロー・代謝経路・神経回路) があれば figure_svg
- 数式は標準遺伝・酵素反応速度などで LaTeX (\\\\(K_m = \\\\frac{[S]}{2}\\\\))
- 用語の定義を厳密に (細胞内小器官・核酸・タンパク質名)""",
            "地学": """- 地震波の伝播図・気象前線図・天体運動図 (惑星軌道) は figure_svg
- 計算問題は単位 (km, hPa, %, 年代) を厳密に""",
        }.get(subject, "")

        system = f"""あなたは日本の大学入試 理系科目 (特に {subject}) の出題傾向に精通した専門家です。
**{univ_name}** の **{year}年度** 入試 (科目: {subject}) の出題形式・難易度・テーマ傾向に完全準拠した類題を生成してください。

【絶対遵守】
- 過去問の丸写しは著作権上禁止。**「{univ_name} {year}年度の {subject} の出題形式に完全準拠した類題」** を新規作成すること。
- {univ_name} の出題スタイル: {univ_style}
- 対象 大問形式: {part_label}
- 解説は日本語で「考え方→立式→計算→答え→補足」を必ず段階分け (3行以上)
{subject_specific}

【出力形式 (純粋な JSON のみ・前後に説明文NG)】
{{
  "passage": "(前提条件・問題設定の文章。空文字でもOK)",
  "audio_script": "",
  "prompt": "",
  "figure_svg": "(図/グラフ/構造式が必要な場合のみ inline SVG 文字列・<svg viewBox=\\"0 0 400 300\\" xmlns=\\"http://www.w3.org/2000/svg\\">...</svg>・<script> や on* 属性は禁止)",
  "year_simulated": {year},
  "univ_simulated": "{univ_name}",
  "subject": "{subject}",
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice|short_answer|essay",
      "stem": "問題文 (LaTeX 数式可)",
      "choices": ["LaTeX 含む選択肢"],
      "answer": "正解 (4択なら 0始まり index・記述式なら完全解答テキスト)",
      "explanation": "解説 (日本語・LaTeX 数式可・3行以上で段階分け)"
    }}
  ]
}}"""

        user = f"""**{univ_name} {year}年度** 形式の **{subject}** ({part_label}) の類題を1セット生成してください。

【出力】上記の system に従い純粋な JSON のみ。{subject} で図が必要な問題は figure_svg を必ず埋めること (空文字 NG)。"""

    else:
        exam_label = exam_hints.get(exam_id, exam_id)
        part_label = part_hints.get(part_key, part_key)

        system = f"""あなたは {exam_label} の試験対策専門家です。公式の出題形式に完全準拠した問題を生成してください。

【厳守】
- 出題形式は公式と完全一致 ({part_label})
- 英文はナチュラルな英語 (機械翻訳臭NG)
- 解説は日本語で正解の根拠 + 他選択肢の誤りポイントを丁寧に
- 出力は純粋なJSONのみ"""

        user = f"""{exam_label} の **{part_key}** ({part_label}) の問題を1セット生成してください。

【出力形式】純粋なJSONのみ:
{{
  "passage": "(Reading の場合は本文、それ以外は空文字)",
  "audio_script": "(Listening の場合はスクリプト、それ以外は空文字)",
  "prompt": "(Speaking/Writing の場合の英語の出題、それ以外は空文字)",
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice|essay|speaking",
      "stem": "問題文",
      "choices": ["A", "B", "C", "D"],
      "answer": "正解(選択肢index 0始まり、または模範解答テキスト)",
      "explanation": "解説 (日本語、3行以上)"
    }}
  ]
}}"""

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({
                "model": EXAM_QUESTIONS_MODEL,
                "max_tokens": 4000,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }).encode("utf-8"),
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip().rstrip("`").strip()
        return json.loads(text)
    except Exception as e:
        log.error(f"[ExamQ] Generation failed for {exam_id}/{part_key}: {type(e).__name__}: {e}")
        return None


def _save_exam_question(exam_id: str, part_key: str, question_data: dict, eiken_grade: Optional[str] = None):
    """生成済み問題を DB に保存"""
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) VALUES (?, ?, ?, ?, ?)",
            (exam_id, part_key, eiken_grade, json.dumps(question_data, ensure_ascii=False), EXAM_QUESTIONS_MODEL),
        )
        conn.commit()
        log.info(f"[ExamQ] Saved: {exam_id}/{part_key} (grade={eiken_grade})")
    except Exception as e:
        log.error(f"[ExamQ] Save failed: {e}")
        try: conn.rollback()
        except Exception: pass
    conn.close()


def _exam_pool_counts() -> dict:
    """全ローテーション組合せの現在 pool 蓄積数を辞書で返す: {(exam, part, grade): n}"""
    conn = db()
    c = conn.cursor()
    counts = {}
    for exam_id, part_key, eiken_grade in EXAM_QUESTION_ROTATION:
        try:
            grade_filter = " AND eiken_grade = ?" if eiken_grade else ""
            params = [exam_id, part_key]
            if eiken_grade:
                params.append(eiken_grade)
            c.execute(
                f"SELECT COUNT(*) FROM exam_questions WHERE exam_id = ? AND part_key = ?{grade_filter}",
                params,
            )
            n = c.fetchone()[0]
        except Exception:
            try: conn.rollback()
            except Exception: pass
            n = 0
        counts[(exam_id, part_key, eiken_grade)] = n
    conn.close()
    return counts


def _exam_generated_today() -> int:
    """JST 当日に生成された問題数 (created_at >= JST 00:00)。daily max 制御に使う。"""
    JST = timezone(timedelta(hours=9))
    midnight_jst = datetime.now(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_jst.astimezone(timezone.utc).replace(tzinfo=None)
    conn = db()
    c = conn.cursor()
    n = 0
    try:
        c.execute("SELECT COUNT(*) FROM exam_questions WHERE created_at >= ?", (midnight_utc,))
        row = c.fetchone()
        n = row[0] if row else 0
    except Exception:
        try: conn.rollback()
        except Exception: pass
    conn.close()
    return int(n)


def _run_exam_questions_generation(quota: int = None, respect_daily_max: bool = True) -> dict:
    """ローテーション順で N 問生成 → DB保存。
    優先順位:
      1. pool < EXAM_QUESTIONS_MIN_POOL の part (緊急補充)
      2. pool < EXAM_QUESTIONS_TARGET_POOL の part (蓄積中)
      3. それ以外は skip (既に十分蓄積済み)
    課金暴走防止: 当日の総生成数が EXAM_QUESTIONS_DAILY_MAX を超えたら respect_daily_max=True なら停止。"""
    if quota is None:
        quota = EXAM_QUESTIONS_DAILY_QUOTA
    counts = _exam_pool_counts()

    # ターゲット未達のものだけを対象に、pool が少ない順にソート
    candidates = [
        (exam_id, part_key, grade)
        for (exam_id, part_key, grade) in EXAM_QUESTION_ROTATION
        if counts.get((exam_id, part_key, grade), 0) < EXAM_QUESTIONS_TARGET_POOL
    ]
    candidates.sort(key=lambda t: counts.get(t, 0))
    sorted_targets = candidates[:quota]

    if not sorted_targets:
        log.info(f"[ExamQ] All parts have reached target pool ({EXAM_QUESTIONS_TARGET_POOL}). Nothing to do.")
        return {"ran": True, "generated": 0, "failed": 0, "skipped_full_pool": True, "details": []}

    # daily max ガード
    today_count = _exam_generated_today() if respect_daily_max else 0
    remaining_today = max(0, EXAM_QUESTIONS_DAILY_MAX - today_count)
    if respect_daily_max and remaining_today <= 0:
        log.warning(f"[ExamQ] Daily max reached ({today_count}/{EXAM_QUESTIONS_DAILY_MAX}), skipping run.")
        return {"ran": True, "generated": 0, "failed": 0, "skipped_daily_max": True, "today_count": today_count, "details": []}

    if respect_daily_max and len(sorted_targets) > remaining_today:
        sorted_targets = sorted_targets[:remaining_today]

    generated = []
    failed = []
    for exam_id, part_key, eiken_grade in sorted_targets:
        q = _generate_exam_question(exam_id, part_key, eiken_grade)
        if q:
            _save_exam_question(exam_id, part_key, q, eiken_grade)
            generated.append({"exam": exam_id, "part": part_key, "grade": eiken_grade})
        else:
            failed.append({"exam": exam_id, "part": part_key, "grade": eiken_grade})
    return {"ran": True, "generated": len(generated), "failed": len(failed), "today_count_after": today_count + len(generated), "details": generated}


# オンデマンド補充の重複起動防止 (同じ key の補充が走行中なら待たせる)
_REFILL_INFLIGHT: set = set()
_REFILL_LOCK = asyncio.Lock()


async def _refill_part_async(exam_id: str, part_key: str, eiken_grade: Optional[str], target: int = 2) -> None:
    """生徒のリクエスト由来で薄い part を裏で補充。
    target 問数を生成。in-flight ロックで多重発火を防止。daily max は遵守。"""
    key = (exam_id, part_key, eiken_grade)
    async with _REFILL_LOCK:
        if key in _REFILL_INFLIGHT:
            return
        _REFILL_INFLIGHT.add(key)
    try:
        # daily max チェック
        today_count = _exam_generated_today()
        if today_count >= EXAM_QUESTIONS_DAILY_MAX:
            log.warning(f"[ExamQ:Refill] Skipped {key}: daily max ({EXAM_QUESTIONS_DAILY_MAX}) reached")
            return
        # 既に target_pool 到達なら skip
        counts = _exam_pool_counts()
        if counts.get(key, 0) >= EXAM_QUESTIONS_TARGET_POOL:
            return
        n_to_gen = min(target, EXAM_QUESTIONS_DAILY_MAX - today_count)
        log.info(f"[ExamQ:Refill] Generating {n_to_gen} for {key} (current pool={counts.get(key, 0)})")
        for _ in range(n_to_gen):
            # 同期的な API 呼び出しを別スレッドへ (FastAPI のイベントループをブロックしない)
            q = await asyncio.get_event_loop().run_in_executor(
                None, _generate_exam_question, exam_id, part_key, eiken_grade
            )
            if q:
                await asyncio.get_event_loop().run_in_executor(
                    None, _save_exam_question, exam_id, part_key, q, eiken_grade
                )
    except Exception as e:
        log.error(f"[ExamQ:Refill] {key} failed: {e}", exc_info=True)
    finally:
        async with _REFILL_LOCK:
            _REFILL_INFLIGHT.discard(key)


async def _exam_questions_scheduler():
    """N時間おきに問題生成。EXAM_QUESTIONS_INTERVAL_HOURS<=0 のときは旧来の毎日 HOUR_JST 時モード。
    各 tick で EXAM_QUESTIONS_PER_TICK 問生成。pool が target に到達した part は自動 skip。"""
    JST = timezone(timedelta(hours=9))

    if EXAM_QUESTIONS_INTERVAL_HOURS <= 0:
        # 旧来の「毎日 HOUR_JST 時に DAILY_QUOTA 問」モード (互換)
        log.info(f"[ExamQ] Daily mode: hour JST {EXAM_QUESTIONS_HOUR_JST}:00, quota {EXAM_QUESTIONS_DAILY_QUOTA}")
        while True:
            try:
                now_jst = datetime.now(JST)
                target = now_jst.replace(hour=EXAM_QUESTIONS_HOUR_JST, minute=0, second=0, microsecond=0)
                if target <= now_jst:
                    target += timedelta(days=1)
                sleep_secs = (target - now_jst).total_seconds()
                log.info(f"[ExamQ] Next daily run at {target.isoformat()} (in {int(sleep_secs)}s)")
                await asyncio.sleep(sleep_secs)
                result = _run_exam_questions_generation(quota=EXAM_QUESTIONS_DAILY_QUOTA)
                log.info(f"[ExamQ] Daily run result: {result}")
            except asyncio.CancelledError:
                log.info("[ExamQ] Scheduler cancelled")
                raise
            except Exception as e:
                log.error(f"[ExamQ] Scheduler loop error: {e}", exc_info=True)
                await asyncio.sleep(3600)
    else:
        # 「N時間おきに PER_TICK 問」モード (随時自動追加)
        interval_secs = int(EXAM_QUESTIONS_INTERVAL_HOURS * 3600)
        per_tick = EXAM_QUESTIONS_PER_TICK
        log.info(f"[ExamQ] Interval mode: every {EXAM_QUESTIONS_INTERVAL_HOURS}h, per-tick {per_tick}, target_pool {EXAM_QUESTIONS_TARGET_POOL}, daily_max {EXAM_QUESTIONS_DAILY_MAX}")
        # 起動 30 秒後に初回 tick (cold start 時に空 pool ならすぐ補充開始)
        await asyncio.sleep(30)
        while True:
            try:
                tick_start = datetime.now(JST)
                result = _run_exam_questions_generation(quota=per_tick)
                log.info(f"[ExamQ] Tick @ {tick_start.isoformat()}: {result}")
                await asyncio.sleep(interval_secs)
            except asyncio.CancelledError:
                log.info("[ExamQ] Scheduler cancelled")
                raise
            except Exception as e:
                log.error(f"[ExamQ] Tick error: {e}", exc_info=True)
                await asyncio.sleep(min(interval_secs, 1800))


@app.post("/api/admin/stripe/setup-founder-special")
def admin_stripe_setup_founder_special(authorization: Optional[str] = Header(None)):
    """🎁 創設メンバー (¥14,500/月・永年・50名限定・premium全機能) の Stripe Product + Price を
    プログラムで作成。lookup_key='founder_special' で永続検索可能。
    冪等: 既に lookup_key で見つかれば再作成しない。
    admin Bearer 認証必須。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY が未設定")

    s = get_stripe()
    # 1. 既存チェック (冪等性)
    try:
        existing = s.Price.list(lookup_keys=["founder_special"], active=True, limit=1)
        if existing and existing.data:
            pid = existing.data[0].id
            log.info(f"[Stripe Setup] founder_special already exists: {pid}")
            global _FOUNDER_SPECIAL_PRICE_CACHE
            _FOUNDER_SPECIAL_PRICE_CACHE = {"id": pid, "checked_at": datetime.now(timezone.utc)}
            return {
                "ok": True,
                "already_exists": True,
                "price_id": pid,
                "lookup_key": "founder_special",
                "amount_jpy": existing.data[0].unit_amount,
                "message": f"既に作成済み ({pid})。env 設定不要・lookup_key で永続的に解決されます。",
            }
    except Exception as e:
        log.warning(f"[Stripe Setup] lookup check failed: {e}")

    # 2. Product 作成 (or 既存検索)
    product_id = None
    try:
        # name 一致の既存 Product があれば再利用
        prods = s.Product.list(active=True, limit=100)
        for p in prods.data:
            if p.name == "AI学習コーチ塾 創設メンバー":
                product_id = p.id
                break
    except Exception as e:
        log.warning(f"[Stripe Setup] product list failed: {e}")
    if not product_id:
        try:
            prod = s.Product.create(
                name="AI学習コーチ塾 創設メンバー",
                description="期間限定 50名・永年¥14,500/月・全機能無制限 (premium 相当)",
                metadata={"plan": "founder_special", "tier": "premium-equivalent", "perpetual": "true"},
            )
            product_id = prod.id
            log.info(f"[Stripe Setup] product created: {product_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Product 作成失敗: {e}")

    # 3. Price 作成 (¥14,500/月 recurring + lookup_key)
    try:
        price = s.Price.create(
            product=product_id,
            unit_amount=14500,
            currency="jpy",
            recurring={"interval": "month"},
            lookup_key="founder_special",
            transfer_lookup_key=True,  # 既存 price で同じ lookup_key があれば奪う
            metadata={"plan": "founder_special", "perpetual": "true", "limit": "50"},
        )
        log.info(f"[Stripe Setup] price created: {price.id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price 作成失敗: {e}")

    # 4. キャッシュ更新
    _FOUNDER_SPECIAL_PRICE_CACHE = {"id": price.id, "checked_at": datetime.now(timezone.utc)}

    return {
        "ok": True,
        "already_exists": False,
        "product_id": product_id,
        "price_id": price.id,
        "lookup_key": "founder_special",
        "amount_jpy": 14500,
        "interval": "month",
        "message": f"✅ 作成完了。env 設定は不要 (lookup_key で動的解決)。今すぐ {BASE_URL}/api/stripe/checkout で plan=founder_special が使えます。",
    }


# ============================================================================
# 🔧 セルフヒーリング系 admin endpoints (Phase 9)
# 設計原則: monitor が検知できる異常は CEO ダッシュ 1 クリックで解決可能にする
# ============================================================================

@app.post("/api/admin/stripe/reconcile")
def admin_stripe_reconcile(authorization: Optional[str] = Header(None)):
    """🔄 Stripe ↔ DB 整合性同期 (失敗 webhook 取りこぼし救済)

    Stripe API から現在 active な subscription を全て取得し、DB と差分があれば
    DB を Stripe に合わせて更新する。webhook 配信失敗で「Stripe では課金中・
    DB では trial」というゴースト顧客を救済できる。冪等。

    返り値: {reconciled: N, details: [...]}"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY が未設定")

    s = get_stripe()
    reconciled = []
    orphans = []
    errors = []
    try:
        subs = s.Subscription.list(status="active", limit=100)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Stripe Subscription.list 失敗: {e}")

    conn = db()
    c = conn.cursor()
    for sub in subs.data:
        try:
            customer = sub.customer
            plan = (sub.metadata or {}).get("plan", "")
            email = None
            try:
                cust_obj = s.Customer.retrieve(customer)
                email = cust_obj.email
            except Exception:
                pass
            # DB 検索: stripe_customer_id 優先・無ければ email
            c.execute("SELECT id, status, plan FROM students WHERE stripe_customer_id = ?", (customer,))
            row = c.fetchone()
            if not row and email:
                c.execute("SELECT id, status, plan FROM students WHERE email = ?", (email,))
                row = c.fetchone()
            if not row:
                # Stripe 側に sub があるが DB に該当生徒なし → orphan
                orphans.append({"customer": customer, "email": email, "subscription": sub.id, "plan": plan})
                continue
            sid, status, db_plan = row[0], row[1], row[2]
            if status != "paid":
                c.execute(
                    """UPDATE students SET status='paid', stripe_customer_id=?, stripe_subscription_id=?,
                           plan=?, paid_since=COALESCE(paid_since, CURRENT_TIMESTAMP), updated_at=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (customer, sub.id, plan or db_plan, sid),
                )
                conn.commit()
                reconciled.append({"student_id": sid, "email": email, "old_status": status, "new_status": "paid", "plan": plan or db_plan})
            elif db_plan != plan and plan:
                # plan だけ違う → 更新
                c.execute(
                    "UPDATE students SET plan=?, stripe_subscription_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (plan, sub.id, sid),
                )
                conn.commit()
                reconciled.append({"student_id": sid, "email": email, "plan_change": f"{db_plan} → {plan}"})
        except Exception as e:
            errors.append({"sub_id": sub.id, "error": str(e)})
            try: conn.rollback()
            except Exception: pass
    conn.close()

    return {
        "ok": True,
        "stripe_active_subscriptions": len(subs.data),
        "reconciled": len(reconciled),
        "orphans": len(orphans),
        "errors": len(errors),
        "details": {"reconciled": reconciled, "orphans": orphans, "errors": errors},
        "message": f"✅ {len(reconciled)} 件を Stripe に合わせて更新。orphan {len(orphans)} 件は手動確認推奨。",
    }


@app.post("/api/admin/cache/force-purge")
def admin_cache_force_purge(authorization: Optional[str] = Header(None)):
    """🧹 全生徒のブラウザキャッシュを強制パージ。

    DB に CACHE_VERSION を bump して保存。フロントの cache-purge.js が起動時に
    /api/cache-version を叩き、保存値より新しければ caches を全削除 + 強制リロード。
    バージョン文字列は ISO timestamp で生成。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    new_version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    conn = db()
    c = conn.cursor()
    try:
        # kv_settings テーブルが無ければ作る
        c.execute(
            """CREATE TABLE IF NOT EXISTS kv_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        # UPSERT
        c.execute("DELETE FROM kv_settings WHERE key = ?", ("cache_version",))
        c.execute("INSERT INTO kv_settings (key, value) VALUES (?, ?)", ("cache_version", new_version))
        conn.commit()
    except Exception as e:
        try: conn.rollback()
        except Exception: pass
        raise HTTPException(status_code=500, detail=f"DB 書込失敗: {e}")
    finally:
        conn.close()

    return {
        "ok": True,
        "cache_version": new_version,
        "message": f"✅ cache_version={new_version} を発行。次回アクセス時に全生徒のブラウザがキャッシュ削除+強制リロードします。",
    }


@app.get("/api/cache-version")
def public_cache_version():
    """全フロントが起動時に呼ぶ。新しい version が来ていたら caches 削除 + reload。"""
    conn = db()
    c = conn.cursor()
    version = ""
    try:
        c.execute("CREATE TABLE IF NOT EXISTS kv_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("SELECT value FROM kv_settings WHERE key = ?", ("cache_version",))
        row = c.fetchone()
        if row:
            version = row[0] if not hasattr(row, "keys") else row["value"]
    except Exception:
        try: conn.rollback()
        except Exception: pass
    finally:
        conn.close()
    return {"version": version or "initial"}


@app.post("/api/admin/campaigns/enrollment-waiver/reset")
def admin_enrollment_waiver_reset(payload: dict = None, authorization: Optional[str] = Header(None)):
    """💰 入塾金免除キャンペーンの枠カウンタをリセット (月初リセット用)。
    既存の status='paid' の中で enrollment_waiver_applied=1 だった生徒数 = 消費済み枠。
    本 endpoint は events テーブルに「リセット時刻」を記録し、それ以降の paid 生徒のみを
    「消費済み」としてカウントする方式に切替える。
    optional payload: {"new_limit": 100} で上限も同時に更新可能 (env 上書き)。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    payload = payload or {}
    new_limit = payload.get("new_limit")
    now = datetime.now(timezone.utc)

    conn = db()
    c = conn.cursor()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS kv_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("DELETE FROM kv_settings WHERE key = ?", ("enrollment_waiver_reset_at",))
        c.execute("INSERT INTO kv_settings (key, value) VALUES (?, ?)", ("enrollment_waiver_reset_at", now.isoformat()))
        if new_limit:
            c.execute("DELETE FROM kv_settings WHERE key = ?", ("enrollment_waiver_limit",))
            c.execute("INSERT INTO kv_settings (key, value) VALUES (?, ?)", ("enrollment_waiver_limit", str(int(new_limit))))
        conn.commit()
        # events に記録
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("enrollment_waiver_reset", json.dumps({"reset_at": now.isoformat(), "new_limit": new_limit}, ensure_ascii=False), "admin"),
        )
        conn.commit()
    except Exception as e:
        try: conn.rollback()
        except Exception: pass
        raise HTTPException(status_code=500, detail=f"リセット失敗: {e}")
    finally:
        conn.close()

    return {
        "ok": True,
        "reset_at": now.isoformat(),
        "new_limit": new_limit or ENROLLMENT_WAIVER_LIMIT,
        "message": f"✅ 入塾金免除キャンペーンを {now.strftime('%Y-%m-%d %H:%M')} にリセット。以降の paid 生徒で枠を再カウント開始。",
    }


@app.post("/api/admin/exam-questions/purge")
def admin_exam_questions_purge(payload: dict, authorization: Optional[str] = Header(None)):
    """🗑️ 蓄積問題プールの選択削除 (品質悪い問題を一括削除→次 tick で再蓄積)。
    payload: {
      "exam_id": "daigaku" (optional),
      "part_key": "r_long" (optional),
      "eiken_grade": "todai" (optional),
      "older_than_days": 30 (optional, 指定日数より古いものだけ削除)
    }
    引数なしの場合は安全のため 422 (誤爆防止)。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    if not isinstance(payload, dict) or not payload:
        raise HTTPException(status_code=422, detail="filter parameter が必須 (exam_id/part_key/eiken_grade/older_than_days のいずれか)")

    where = []
    params = []
    if payload.get("exam_id"):
        where.append("exam_id = ?")
        params.append(payload["exam_id"])
    if payload.get("part_key"):
        where.append("part_key = ?")
        params.append(payload["part_key"])
    if payload.get("eiken_grade"):
        where.append("eiken_grade = ?")
        params.append(payload["eiken_grade"])
    older_than = payload.get("older_than_days")
    if older_than:
        cutoff = datetime.now(timezone.utc) - timedelta(days=int(older_than))
        where.append("created_at < ?")
        params.append(cutoff.isoformat())
    if not where:
        raise HTTPException(status_code=422, detail="少なくとも 1 つの filter が必要")

    where_sql = " WHERE " + " AND ".join(where)
    conn = db()
    c = conn.cursor()
    deleted = 0
    try:
        # まず削除対象数をカウント (返却用)
        c.execute(f"SELECT COUNT(*) FROM exam_questions{where_sql}", tuple(params))
        row = c.fetchone()
        deleted = int(row[0] if row else 0)
        # DELETE
        c.execute(f"DELETE FROM exam_questions{where_sql}", tuple(params))
        conn.commit()
        # events に記録
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("exam_questions_purge", json.dumps({"filter": payload, "deleted": deleted}, ensure_ascii=False), "admin"),
        )
        conn.commit()
    except Exception as e:
        try: conn.rollback()
        except Exception: pass
        raise HTTPException(status_code=500, detail=f"削除失敗: {e}")
    finally:
        conn.close()

    return {
        "ok": True,
        "deleted": deleted,
        "filter": payload,
        "message": f"✅ {deleted} 問を削除。次の tick (interval scheduler) で薄い part から自動再蓄積されます。",
    }


@app.post("/api/admin/exam-questions/burst-seed")
async def admin_exam_questions_burst_seed(payload: dict = None, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """🚀 全 ROTATION 枠を最低 N 問まで一括生成 (初期投入・サービスローンチ前用)。

    payload (任意):
      {"target_per_part": 5, "max_total": 100, "concurrency": 3}
    省略時のデフォルト: target=5, max_total=100, concurrency=3

    動作:
    - EXAM_QUESTION_ROTATION 全枠を読み、現在 count < target_per_part の枠を抽出
    - 不足分の合計 (cap max_total) を asyncio で並列生成
    - DAILY_MAX 制約はバイパス (CEO 判断・1回限りの一括投入)
    - 完了時に詳細サマリ返却

    レスポンス:
    {ok, target_per_part, scanned_parts, parts_under_target, generated, failed, duration_sec, details: [...]}
    """
    # 認証 (admin Bearer or x-cron-secret)
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY 未設定")

    payload = payload or {}
    target = int(payload.get("target_per_part", 30))    # CEO 課金許可済 → デフォを TARGET_POOL=30 に
    max_total = int(payload.get("max_total", 3000))     # 全枠 30問満杯まで届く上限
    concurrency = max(1, min(int(payload.get("concurrency", 5)), 8))  # 1-8 並列 (5 デフォ・速度優先)

    counts = _exam_pool_counts()
    # 不足枠を抽出 (count < target)
    needs = []
    for (exam_id, part_key, grade), n in counts.items():
        deficit = max(0, target - n)
        if deficit > 0:
            for _ in range(deficit):
                needs.append((exam_id, part_key, grade))
    parts_under_target = sum(1 for (_, _, _), n in counts.items() if n < target)
    # max_total キャップ
    if len(needs) > max_total:
        needs = needs[:max_total]

    if not needs:
        return {
            "ok": True,
            "target_per_part": target,
            "scanned_parts": len(counts),
            "parts_under_target": 0,
            "generated": 0,
            "failed": 0,
            "duration_sec": 0,
            "message": f"全 {len(counts)} 枠が target={target} に到達済み。生成不要。",
        }

    started = datetime.now(timezone.utc)
    log.info(f"[BurstSeed] starting: target={target}, max_total={max_total}, concurrency={concurrency}, queue={len(needs)}")

    # 並列実行用 semaphore
    sem = asyncio.Semaphore(concurrency)
    generated = []
    failed = []
    lock = asyncio.Lock()

    async def gen_one(exam_id, part_key, grade):
        async with sem:
            loop = asyncio.get_event_loop()
            q = await loop.run_in_executor(None, _generate_exam_question, exam_id, part_key, grade)
            if q:
                await loop.run_in_executor(None, _save_exam_question, exam_id, part_key, q, grade)
                async with lock:
                    generated.append({"exam": exam_id, "part": part_key, "grade": grade})
            else:
                async with lock:
                    failed.append({"exam": exam_id, "part": part_key, "grade": grade})

    try:
        # 全タスクを並列で起動 (concurrency=3 で sem 制御)
        await asyncio.wait_for(
            asyncio.gather(*[gen_one(*n) for n in needs], return_exceptions=True),
            timeout=3600,  # 1時間タイムアウト (大量蓄積モード対応・generated 数は途中まででも保存される)
        )
    except asyncio.TimeoutError:
        log.warning("[BurstSeed] timeout reached at 10min")

    duration = (datetime.now(timezone.utc) - started).total_seconds()

    # events ログ
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("exam_questions_burst_seed", json.dumps({
                "target": target, "max_total": max_total, "concurrency": concurrency,
                "queued": len(needs), "generated": len(generated), "failed": len(failed),
                "duration_sec": int(duration),
            }, ensure_ascii=False), "admin"),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning(f"[BurstSeed] event log failed: {e}")

    log.info(f"[BurstSeed] done: generated={len(generated)} failed={len(failed)} duration={int(duration)}s")
    # 概算コスト (Sonnet 4.6 $3/$15 per 1M tokens, ~3500 tokens output avg per question = $0.053)
    est_cost_usd = round(len(generated) * 0.06, 2)
    return {
        "ok": True,
        "target_per_part": target,
        "scanned_parts": len(counts),
        "parts_under_target": parts_under_target,
        "queued": len(needs),
        "generated": len(generated),
        "failed": len(failed),
        "duration_sec": int(duration),
        "estimated_cost_usd": est_cost_usd,
        "message": f"✅ {len(generated)} 問生成 (失敗 {len(failed)}・所要 {int(duration)}秒・推定 ${est_cost_usd}≈¥{int(est_cost_usd * 150)})",
    }


@app.post("/api/admin/exam-questions/import")
def admin_exam_questions_import(payload: dict, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """🆓 Claude Max プラン経由で生成した問題 JSON を一括インサート ($0 運用用)。

    payload:
      {
        "questions": [
          {"exam_id": "toefl", "part_key": "r_passage1", "eiken_grade": null,
           "question_data": {...}, "model": "claude-max-plan"}
        ],
        "skip_full": true  // 任意・true なら TARGET_POOL 到達 part を skip
      }

    認証: admin Bearer or x-cron-secret"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    questions = payload.get("questions") or []
    if not isinstance(questions, list) or not questions:
        raise HTTPException(status_code=400, detail="questions が空 or 配列ではありません")

    skip_full = bool(payload.get("skip_full", False))
    counts = _exam_pool_counts() if skip_full else {}

    valid_rotation = {(e, p, g) for (e, p, g) in EXAM_QUESTION_ROTATION}

    inserted = 0
    skipped = 0
    failed = []
    conn = db()
    c = conn.cursor()
    try:
        for i, q in enumerate(questions):
            try:
                exam_id = q.get("exam_id")
                part_key = q.get("part_key")
                eiken_grade = q.get("eiken_grade")
                question_data = q.get("question_data")
                model = q.get("model") or "claude-max-plan"

                if not exam_id or not part_key or not question_data:
                    failed.append({"i": i, "reason": "missing required fields"})
                    continue
                if (exam_id, part_key, eiken_grade) not in valid_rotation:
                    failed.append({"i": i, "reason": f"invalid rotation: {exam_id}/{part_key}/{eiken_grade}"})
                    continue
                if skip_full and counts.get((exam_id, part_key, eiken_grade), 0) >= EXAM_QUESTIONS_TARGET_POOL:
                    skipped += 1
                    continue

                c.execute(
                    "INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) VALUES (?, ?, ?, ?, ?)",
                    (exam_id, part_key, eiken_grade,
                     json.dumps(question_data, ensure_ascii=False) if not isinstance(question_data, str) else question_data,
                     model),
                )
                inserted += 1
                if skip_full:
                    counts[(exam_id, part_key, eiken_grade)] = counts.get((exam_id, part_key, eiken_grade), 0) + 1
            except Exception as e:
                failed.append({"i": i, "reason": f"{type(e).__name__}: {e}"})
                try: conn.rollback()
                except Exception: pass
        conn.commit()
    finally:
        conn.close()

    log.info(f"[ExamQ:Import] inserted={inserted} skipped={skipped} failed={len(failed)}")
    return {
        "ok": True,
        "received": len(questions),
        "inserted": inserted,
        "skipped_full": skipped,
        "failed": len(failed),
        "failed_details": failed[:20],
        "message": f"✅ {inserted}問 import (skip {skipped}・失敗 {len(failed)})",
    }


@app.post("/api/admin/exam-questions/generate")
def admin_exam_questions_generate(payload: dict, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """指定パート (or ローテ全件) の問題を生成。手動トリガー。
    payload: {"exam_id": "eiken", "part_key": "r_q1", "eiken_grade": "gp1", "count": 1}
    省略時はローテーション全件 (quota 使用)"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    exam_id = payload.get("exam_id")
    part_key = payload.get("part_key")
    eiken_grade = payload.get("eiken_grade")
    count = int(payload.get("count") or 0)

    if exam_id and part_key:
        # 特定 part に N 問
        n = max(1, min(count or 1, 10))
        generated = []
        for _ in range(n):
            q = _generate_exam_question(exam_id, part_key, eiken_grade)
            if q:
                _save_exam_question(exam_id, part_key, q, eiken_grade)
                generated.append({"exam": exam_id, "part": part_key, "grade": eiken_grade})
        return {"generated": len(generated), "details": generated}
    else:
        # ローテ全件 (quota 使用)
        return _run_exam_questions_generation(quota=count or EXAM_QUESTIONS_DAILY_QUOTA)


@app.get("/api/exam-questions/bank")
def public_exam_questions_bank(exam: str, part: str, eiken_grade: Optional[str] = None, univ: Optional[str] = None, limit: int = 20):
    """公開API: 試験パートの最新N問を返す (フロントが AUTO_GENERATED_BANKS に流し込む)。
    認証不要 (出題内容は公開可・実回答は提出不要)。
    univ パラメータは大学入試 (daigaku) 用 — DB スキーマ上は eiken_grade カラムに大学キーを保存している。"""
    limit = max(1, min(limit, 50))
    # daigaku の場合 univ → eiken_grade として扱う (DB スキーマ共有)
    if exam == "daigaku" and univ and not eiken_grade:
        eiken_grade = univ
    conn = db()
    c = conn.cursor()
    try:
        if eiken_grade:
            c.execute(
                "SELECT question_data, created_at FROM exam_questions WHERE exam_id = ? AND part_key = ? AND eiken_grade = ? ORDER BY created_at DESC LIMIT ?",
                (exam, part, eiken_grade, limit),
            )
        else:
            c.execute(
                "SELECT question_data, created_at FROM exam_questions WHERE exam_id = ? AND part_key = ? ORDER BY created_at DESC LIMIT ?",
                (exam, part, limit),
            )
        rows = c.fetchall()
    except Exception as e:
        log.error(f"[ExamQ] bank query failed: {e}")
        rows = []
    conn.close()

    items = []
    for r in rows:
        try:
            data = json.loads(r["question_data"])
            data["_created_at"] = str(r["created_at"])
            items.append(data)
        except Exception:
            pass
    # ランダムに1件返す (毎回違う問題で多様性確保)
    import random
    selected = random.choice(items) if items else None

    # 🔁 オンデマンド補充: pool が薄い part を生徒が引いた瞬間に裏で補充キューイング
    # (ExamQ scheduler は N時間おき・interval=6h なので、その間でも必要なら即補充)
    if EXAM_QUESTIONS_ENABLED and len(items) < EXAM_QUESTIONS_MIN_POOL:
        try:
            asyncio.create_task(_refill_part_async(exam, part, eiken_grade, target=2))
            log.info(f"[ExamQ:Refill] queued for {exam}/{part}/{eiken_grade} (pool={len(items)} < min={EXAM_QUESTIONS_MIN_POOL})")
        except Exception as e:
            log.warning(f"[ExamQ:Refill] failed to queue: {e}")

    return {"exam": exam, "part": part, "eiken_grade": eiken_grade, "count": len(items), "selected": selected, "all": items[:5]}


@app.get("/api/exam-questions/archive")
def public_exam_questions_archive(
    exam: Optional[str] = None,
    part: Optional[str] = None,
    eiken_grade: Optional[str] = None,
    univ: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
):
    """生徒向けの過去問アーカイブブラウザ。蓄積済み AI 生成問題プールから filter 取得。
    認証不要 (出題内容公開可)。

    パラメータ全部省略時は試験/大問の組合せ別の蓄積数サマリ (= overview) を返す。
    パラメータ指定時はその条件に合致する問題リスト (passage 抜粋 + 設問数 + メタ) を返す。"""
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    # daigaku の場合 univ → eiken_grade として扱う (DBスキーマ共有)
    if exam == "daigaku" and univ and not eiken_grade:
        eiken_grade = univ

    conn = db()
    c = conn.cursor()

    # ===== overview モード (filter なし or exam のみ) =====
    if not part and not eiken_grade and not year:
        try:
            if exam:
                c.execute(
                    "SELECT exam_id, part_key, eiken_grade, COUNT(*) as n FROM exam_questions WHERE exam_id = ? GROUP BY exam_id, part_key, eiken_grade ORDER BY exam_id, part_key, eiken_grade",
                    (exam,),
                )
            else:
                c.execute(
                    "SELECT exam_id, part_key, eiken_grade, COUNT(*) as n FROM exam_questions GROUP BY exam_id, part_key, eiken_grade ORDER BY exam_id, part_key, eiken_grade"
                )
            rows = c.fetchall()
        except Exception as e:
            log.error(f"[Archive] overview query failed: {e}")
            rows = []
        conn.close()
        groups = []
        total = 0
        for r in rows:
            n = int(r["n"] if "n" in r.keys() else r[3])
            groups.append({
                "exam": r["exam_id"],
                "part": r["part_key"],
                "grade": r["eiken_grade"],
                "count": n,
            })
            total += n
        return {"mode": "overview", "total": total, "groups": groups}

    # ===== list モード (filter あり) =====
    where = []
    params = []
    if exam:
        where.append("exam_id = ?")
        params.append(exam)
    if part:
        where.append("part_key = ?")
        params.append(part)
    if eiken_grade:
        where.append("eiken_grade = ?")
        params.append(eiken_grade)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    try:
        # SQLite では PostgreSQL の placeholder と異なるため、_Cursor wrapper が ? ↔ %s を吸収する想定
        c.execute(
            f"SELECT id, exam_id, part_key, eiken_grade, question_data, created_at FROM exam_questions{where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            tuple(params + [limit, offset]),
        )
        rows = c.fetchall()
        # total count for pagination
        c.execute(f"SELECT COUNT(*) FROM exam_questions{where_sql}", tuple(params))
        total_row = c.fetchone()
        total = int(total_row[0] if total_row else 0)
    except Exception as e:
        log.error(f"[Archive] list query failed: {e}")
        rows = []
        total = 0
    conn.close()

    items = []
    for r in rows:
        try:
            data = json.loads(r["question_data"])
            yr = data.get("year_simulated")
            # year filter (post-fetch・DBに year カラムは無いので JSON 内の年度で判定)
            if year and yr and int(yr) != int(year):
                continue
            items.append({
                "id": r["id"],
                "exam": r["exam_id"],
                "part": r["part_key"],
                "grade": r["eiken_grade"],
                "year": yr,
                "univ_simulated": data.get("univ_simulated"),
                "passage_preview": (data.get("passage", "") or data.get("audio_script", "") or data.get("prompt", ""))[:200],
                "question_count": len(data.get("questions", [])),
                "created_at": str(r["created_at"]),
            })
        except Exception:
            pass
    return {"mode": "list", "total": total, "limit": limit, "offset": offset, "items": items}


@app.get("/api/exam-questions/archive/{question_id}")
def public_exam_questions_archive_detail(question_id: int):
    """アーカイブから1問を ID 指定で取得 (生徒が「これを解く」ボタンで呼び出す用)"""
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT id, exam_id, part_key, eiken_grade, question_data, created_at FROM exam_questions WHERE id = ?",
            (question_id,),
        )
        row = c.fetchone()
    except Exception as e:
        log.error(f"[Archive] detail query failed: {e}")
        row = None
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="問題が見つかりません")
    try:
        data = json.loads(row["question_data"])
    except Exception:
        raise HTTPException(status_code=500, detail="問題データ破損")
    return {
        "id": row["id"],
        "exam": row["exam_id"],
        "part": row["part_key"],
        "grade": row["eiken_grade"],
        "created_at": str(row["created_at"]),
        "question": data,
    }


@app.post("/api/exam-questions/recommend")
def public_exam_questions_recommend(payload: dict):
    """生徒の学習履歴 (localStorage の history) から AI で「次に解くべき問題」を推薦する。
    payload: {
      "history": [{"exam":"daigaku","part":"r_long","grade":"todai","score":18,"scoreMax":25,"date":"..."},...],
      "target": {"exam":"daigaku","grade":"todai"} (optional)
    }
    """
    history = payload.get("history") or []
    target = payload.get("target") or {}
    if not isinstance(history, list):
        raise HTTPException(status_code=400, detail="history must be array")
    # 履歴から正答率を集計
    by_part = {}
    for h in history[-50:]:  # 直近50件のみ
        if not isinstance(h, dict): continue
        exam_id = h.get("exam") or h.get("examId")
        part_key = h.get("part") or h.get("sectionKey")
        grade = h.get("grade") or h.get("eikenGrade")
        score = h.get("score")
        score_max = h.get("scoreMax") or h.get("scoreMaxValue")
        if not exam_id or not part_key: continue
        key = f"{exam_id}/{part_key}/{grade or '_'}"
        if key not in by_part:
            by_part[key] = {"exam": exam_id, "part": part_key, "grade": grade, "attempts": 0, "score_sum": 0, "max_sum": 0}
        by_part[key]["attempts"] += 1
        if isinstance(score, (int, float)) and isinstance(score_max, (int, float)) and score_max > 0:
            by_part[key]["score_sum"] += float(score)
            by_part[key]["max_sum"] += float(score_max)
    summary = []
    for k, v in by_part.items():
        ratio = (v["score_sum"] / v["max_sum"]) if v["max_sum"] > 0 else None
        summary.append({**v, "score_ratio": ratio})
    summary.sort(key=lambda x: (x.get("score_ratio") if x.get("score_ratio") is not None else 1.0, -x["attempts"]))

    # ロジック側で簡易レコメンド (AI 不要のフォールバック)
    weakest = summary[:3]  # 正答率が低い順 TOP3
    fallback = []
    for w in weakest:
        fallback.append({
            "exam": w["exam"], "part": w["part"], "grade": w["grade"],
            "reason_jp": f"このパートの正答率が {int((w.get('score_ratio') or 0)*100)}% (n={w['attempts']}) で最も伸びしろがあるため、もう一度同じ形式で挑戦しましょう。",
            "score_ratio": w.get("score_ratio"),
        })
    # 履歴ゼロ → target ベースで「最も典型的な r_long」を推奨
    if not fallback and target:
        ex = target.get("exam") or "daigaku"
        gr = target.get("grade")
        fallback.append({
            "exam": ex, "part": "r_long", "grade": gr,
            "reason_jp": "まず長文読解 (r_long) でレベル感を測りましょう。",
            "score_ratio": None,
        })

    # AI 強化レコメンド (Anthropic key があれば叩く・無ければフォールバックで返す)
    ai_advice = None
    if ANTHROPIC_API_KEY and history:
        try:
            stats_text = "\n".join([
                f"- {s['exam']}/{s['part']} (grade={s.get('grade') or '-'}): n={s['attempts']}回・正答率 {int((s.get('score_ratio') or 0)*100)}%"
                for s in summary[:8]
            ])
            target_text = f"目標: {target.get('exam') or '指定なし'} {target.get('grade') or ''}"
            system = "あなたは英語試験対策の AI コーチです。学習者の履歴から弱点を特定し、次に取り組むべき part を1つ推薦してください。出力は純粋な JSON のみ。"
            user = f"""【学習履歴サマリ】
{stats_text or '(履歴なし)'}

【{target_text}】

【出力形式 (純粋な JSON)】
{{
  "recommended_exam": "toefl|toeic|ielts|eiken|daigaku",
  "recommended_part": "r_long など",
  "recommended_grade": "todai or gp1 or null",
  "reason_jp": "なぜ次にこれを解くべきか (3行以上、具体的な弱点指摘+伸ばし方)",
  "study_tip_jp": "今日のうちに取り入れるべき具体的な学習Tip (語彙/文法/構造把握 etc)"
}}"""
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps({
                    "model": EXAM_QUESTIONS_MODEL,
                    "max_tokens": 800,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                }).encode("utf-8"),
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                d = json.loads(resp.read().decode())
            text = d["content"][0]["text"].strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"): text = text[4:]
                text = text.strip().rstrip("`").strip()
            ai_advice = json.loads(text)
        except Exception as e:
            log.warning(f"[Recommend] AI advice failed: {e}")

    return {
        "summary": summary[:10],
        "weakest": weakest,
        "fallback_recommendations": fallback,
        "ai_advice": ai_advice,
    }


@app.post("/api/curriculum/generate")
def public_curriculum_generate(payload: dict):
    """🎯 受験日逆算 個別 AI カリキュラム生成。
    payload: {
      "exam_id": "daigaku|toefl|toeic|ielts|eiken",
      "target_grade": "todai|gp1|null"  (大学キー or 英検級),
      "target_grade_name": "東京大学" (表示用),
      "exam_date": "2027-02-25" (ISO date string),
      "current_level": "B1" (CEFR),
      "daily_minutes": 60,
      "weak_parts": ["r_translation", "w_essay"] (Phase 5 recommend で判明した弱点),
      "history_summary": [...] (任意・Phase 5 のサマリ流用)
    }

    出力: {
      "days_remaining": 365,
      "weeks_remaining": 52,
      "phases": [
        {"phase": "基礎固め", "weeks": [...], "weeks_count": 12},
        {"phase": "応用強化", "weeks_count": 26},
        {"phase": "直前期", "weeks_count": 14}
      ],
      "weekly_roadmap": [
        {"week": 1, "phase": "基礎固め", "focus": "...", "tasks": [...], "estimated_minutes": 420}
      ],
      "study_principles": ["...", "..."],
      "milestone_assessments": [...],
    }
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid payload")
    exam_id = payload.get("exam_id") or "daigaku"
    target_grade = payload.get("target_grade")
    target_grade_name = payload.get("target_grade_name") or target_grade or "受験対象"
    exam_date = payload.get("exam_date")
    current_level = payload.get("current_level") or "B1"
    daily_minutes = int(payload.get("daily_minutes") or 60)
    weak_parts = payload.get("weak_parts") or []
    history_summary = payload.get("history_summary") or []

    # 残日数計算
    if not exam_date:
        raise HTTPException(status_code=400, detail="exam_date is required")
    try:
        target_date = datetime.fromisoformat(exam_date.replace("Z", "+00:00"))
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)
    except Exception:
        raise HTTPException(status_code=400, detail="exam_date must be ISO date format (YYYY-MM-DD)")
    now = datetime.now(timezone.utc)
    days_remaining = max(1, int((target_date - now).total_seconds() / 86400))
    weeks_remaining = max(1, days_remaining // 7)

    if not ANTHROPIC_API_KEY:
        # フォールバック: 簡易ロジック生成
        return _curriculum_fallback(
            exam_id, target_grade_name, days_remaining, weeks_remaining,
            current_level, daily_minutes, weak_parts
        )

    weak_parts_text = ", ".join(weak_parts) if weak_parts else "履歴未提供 (汎用最適化)"
    history_text = "\n".join([
        f"- {h.get('exam')}/{h.get('part')} ({h.get('grade') or '-'}): n={h.get('attempts')}・正答率{int((h.get('score_ratio') or 0)*100)}%"
        for h in history_summary[:8]
    ]) if history_summary else "(履歴なし)"

    system = """あなたは英語試験対策の専門学習コーチです。日本人受験者向けに、受験日逆算の個別カリキュラムを設計してください。

【設計指針】
- 残日数を 3 フェーズに分割: 基礎固め (前半 30-50%) / 応用強化 (中盤 30-40%) / 直前期 (後半 15-25%)
- 1日あたりの学習時間を厳守 (オーバーフロー禁止)
- 弱点 part を「直前期で克服」ではなく「基礎固め後半～応用強化」で集中対策する
- 週ごとに具体的なタスク (問題演習回数・単語数・模試予定) を割り振る
- 日本人特有の弱点 (冠詞・関係詞・分詞構文・無生物主語の和訳・コロケーション) を必ず織り込む
- 出力は純粋な JSON のみ (前後に文章を付けない)"""

    user = f"""【学習者プロファイル】
- 受験予定: {target_grade_name} ({exam_id})
- 受験日: {exam_date}
- 残日数: {days_remaining}日 (約{weeks_remaining}週間)
- 現在レベル: CEFR {current_level}
- 1日学習可能時間: {daily_minutes}分
- 弱点 part (直近履歴より): {weak_parts_text}
- 履歴サマリ:
{history_text}

【出力形式 (純粋な JSON)】
{{
  "days_remaining": {days_remaining},
  "weeks_remaining": {weeks_remaining},
  "phases": [
    {{"phase": "基礎固め", "weeks_count": <数値>, "objective_jp": "このフェーズで達成すること"}},
    {{"phase": "応用強化", "weeks_count": <数値>, "objective_jp": "..."}},
    {{"phase": "直前期", "weeks_count": <数値>, "objective_jp": "..."}}
  ],
  "weekly_roadmap": [
    {{
      "week": 1,
      "phase": "基礎固め",
      "focus_jp": "今週のフォーカス (具体的に1行)",
      "tasks": [
        {{"category": "vocab|reading|grammar|listening|speaking|writing|mock|review", "title_jp": "タスク名", "detail_jp": "具体的な内容", "minutes": <数値>}}
      ],
      "estimated_total_minutes": <週合計>,
      "milestone_jp": "今週末に達成すべき指標 (例: r_long で 70%以上)"
    }}
    // 全 {weeks_remaining} 週分を生成 (簡略化のため最大 16 週まで・残りは "applies_remaining_weeks" でまとめる)
  ],
  "study_principles": [
    "学習者へのコーチング指針 1",
    "学習者へのコーチング指針 2",
    "..."
  ],
  "milestone_assessments": [
    {{"week": <週番号>, "type": "模試", "target_jp": "目標値"}},
    {{"week": <週番号>, "type": "弱点再評価", "target_jp": "..."}}
  ],
  "estimated_score_at_exam": "目標スコア予測 (現状 + 投下時間から逆算・楽観的すぎず保守的すぎず)"
}}

【厳守】
- weekly_roadmap は最初の 12-16 週を必ず詳細化、それ以降は "phase 名" + "代表的なタスクパターン" でまとめてOK (週単位のテンプレ化)
- minutes 合計は daily_minutes × 7 を超えない (週上限 = {daily_minutes * 7})
- estimated_score_at_exam は具体的な数値 (例: 「東大英語 78/120 → 88/120 (+10)」)"""

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({
                "model": EXAM_QUESTIONS_MODEL,
                "max_tokens": 8000,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }).encode("utf-8"),
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            d = json.loads(resp.read().decode())
        text = d["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"): text = text[4:]
            text = text.strip().rstrip("`").strip()
        result = json.loads(text)
        # 保険で server-side computed values を上書き
        result["days_remaining"] = days_remaining
        result["weeks_remaining"] = weeks_remaining
        result["target_grade_name"] = target_grade_name
        result["exam_id"] = exam_id
        result["exam_date"] = exam_date
        result["generated_at"] = now.isoformat()
        return result
    except Exception as e:
        log.error(f"[Curriculum] AI generation failed: {type(e).__name__}: {e}")
        return _curriculum_fallback(
            exam_id, target_grade_name, days_remaining, weeks_remaining,
            current_level, daily_minutes, weak_parts
        )


def _curriculum_fallback(exam_id, target_grade_name, days_remaining, weeks_remaining,
                          current_level, daily_minutes, weak_parts):
    """AI が使えない時の汎用フォールバック・3フェーズ均等分割"""
    base_phase = max(1, weeks_remaining // 3)
    return {
        "days_remaining": days_remaining,
        "weeks_remaining": weeks_remaining,
        "target_grade_name": target_grade_name,
        "exam_id": exam_id,
        "phases": [
            {"phase": "基礎固め", "weeks_count": base_phase, "objective_jp": f"CEFR {current_level} レベルの基礎を固める"},
            {"phase": "応用強化", "weeks_count": base_phase, "objective_jp": "弱点 part の集中対策と応用問題への移行"},
            {"phase": "直前期", "weeks_count": max(1, weeks_remaining - 2 * base_phase), "objective_jp": "本番形式の演習・最終調整"},
        ],
        "weekly_roadmap": [
            {
                "week": w,
                "phase": "基礎固め" if w <= base_phase else ("応用強化" if w <= 2 * base_phase else "直前期"),
                "focus_jp": "週ごとの学習に集中",
                "tasks": [
                    {"category": "vocab", "title_jp": "語彙学習", "detail_jp": "頻出語彙 50語/週", "minutes": daily_minutes * 2},
                    {"category": "reading", "title_jp": "長文読解", "detail_jp": "1問/日", "minutes": daily_minutes * 3},
                    {"category": "review", "title_jp": "復習", "detail_jp": "前週の弱点復習", "minutes": daily_minutes * 2},
                ],
                "estimated_total_minutes": daily_minutes * 7,
                "milestone_jp": "週末に進捗確認",
            }
            for w in range(1, min(weeks_remaining, 12) + 1)
        ],
        "study_principles": [
            "毎日の学習時間を厳守する (休日も例外なく)",
            "弱点を見つけたら即座に類題で克服する",
            "模試は週1で必ず実施し、結果を可視化する",
        ],
        "milestone_assessments": [
            {"week": base_phase, "type": "中間模試", "target_jp": "現状から +10% スコア"},
            {"week": base_phase * 2, "type": "応用模試", "target_jp": "目標スコアの 80% 到達"},
        ],
        "estimated_score_at_exam": "履歴データが充実すると AI が具体的なスコア予測を返します",
        "fallback": True,
    }


@app.get("/api/admin/exam-questions/pool-status")
def admin_exam_questions_pool_status(authorization: Optional[str] = Header(None)):
    """全 part の pool 蓄積数を返す (CEO ダッシュボード用)。admin Bearer 認証必須。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    counts = _exam_pool_counts()
    JST = timezone(timedelta(hours=9))
    today_count = _exam_generated_today()
    parts = []
    by_exam = {}
    total = 0
    full_pool = 0
    low_pool = 0
    for (exam_id, part_key, eiken_grade), n in counts.items():
        total += n
        is_full = n >= EXAM_QUESTIONS_TARGET_POOL
        is_low = n < EXAM_QUESTIONS_MIN_POOL
        if is_full: full_pool += 1
        if is_low: low_pool += 1
        parts.append({
            "exam": exam_id,
            "part": part_key,
            "grade": eiken_grade,
            "count": n,
            "is_full": is_full,
            "is_low": is_low,
        })
        by_exam[exam_id] = by_exam.get(exam_id, 0) + n
    parts.sort(key=lambda p: (p["count"], p["exam"], p["part"]))
    return {
        "rotation_size": len(EXAM_QUESTION_ROTATION),
        "total_questions": total,
        "by_exam": by_exam,
        "full_pool_parts": full_pool,
        "low_pool_parts": low_pool,
        "in_flight_refills": len(_REFILL_INFLIGHT),
        "today_generated": today_count,
        "config": {
            "interval_hours": EXAM_QUESTIONS_INTERVAL_HOURS,
            "per_tick": EXAM_QUESTIONS_PER_TICK,
            "target_pool": EXAM_QUESTIONS_TARGET_POOL,
            "min_pool": EXAM_QUESTIONS_MIN_POOL,
            "daily_max": EXAM_QUESTIONS_DAILY_MAX,
            "model": EXAM_QUESTIONS_MODEL,
        },
        "parts": parts,
    }


# ============================================================================
# 📰 CNN / Japan Times / BBC 記事から英語読解問題を生成 (実英文記事モード)
# ============================================================================
# 著作権配慮: 記事本文を丸ごと取り込まずに、RSS フィードのタイトル + 短い summary
# (RSS が公開している抜粋・通常 1-3 文) を seed として AI に類題本文を生成させる。
# 元記事の URL は出題と一緒に表示し、生徒が原典で読み比べできるようにする。

NEWS_FEEDS = {
    "cnn":           {"url": "http://rss.cnn.com/rss/cnn_topstories.rss",      "name": "CNN Top Stories",      "level": "B2-C1"},
    "cnn_world":     {"url": "http://rss.cnn.com/rss/cnn_world.rss",           "name": "CNN World",            "level": "B2-C1"},
    "japan_times":   {"url": "https://www.japantimes.co.jp/feed/topstories/",  "name": "The Japan Times",      "level": "B2"},
    "japan_times_news": {"url": "https://www.japantimes.co.jp/news/feed/",     "name": "Japan Times News",     "level": "B2"},
    "bbc":           {"url": "http://feeds.bbci.co.uk/news/rss.xml",           "name": "BBC News",             "level": "B2"},
    "bbc_world":     {"url": "http://feeds.bbci.co.uk/news/world/rss.xml",     "name": "BBC World",            "level": "B2"},
    "nyt":           {"url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "name": "The New York Times", "level": "C1"},
    "guardian":      {"url": "https://www.theguardian.com/world/rss",          "name": "The Guardian",         "level": "B2-C1"},
    "reuters_world": {"url": "https://feeds.reuters.com/reuters/worldNews",    "name": "Reuters World",        "level": "B2"},
    "nhk_world":     {"url": "https://www3.nhk.or.jp/nhkworld/en/news/feed/",  "name": "NHK World",            "level": "B1-B2"},
}


def _fetch_news_feed(feed_key: str, limit: int = 5) -> list[dict]:
    """RSS フィードを取得して [{title, link, summary, published}] のリストを返す。
    XML パースは標準ライブラリのみで実装 (xml.etree.ElementTree)。"""
    feed = NEWS_FEEDS.get(feed_key)
    if not feed:
        return []
    try:
        import xml.etree.ElementTree as ET
        req = urllib.request.Request(feed["url"], headers={"User-Agent": "Mozilla/5.0 (compatible; AIJukuBot/1.0)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        # RSS 2.0: channel/item, Atom: feed/entry — 両方サポート
        items = []
        # try RSS first
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            summary = (item.findtext("description") or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "").strip()
            published = (item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date") or "").strip()
            if title and link:
                # HTML タグを単純除去 (RSS の description には HTML が混じることが多い)
                import re
                summary_text = re.sub(r"<[^>]+>", "", summary)[:600]
                items.append({"title": title, "link": link, "summary": summary_text, "published": published})
        # try Atom if no RSS items
        if not items:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns)[:limit]:
                title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
                link_el = entry.find("atom:link", ns)
                link = (link_el.get("href") if link_el is not None else "").strip()
                summary = (entry.findtext("atom:summary", default="", namespaces=ns) or entry.findtext("atom:content", default="", namespaces=ns) or "").strip()
                published = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()
                if title and link:
                    import re
                    summary_text = re.sub(r"<[^>]+>", "", summary)[:600]
                    items.append({"title": title, "link": link, "summary": summary_text, "published": published})
        return items
    except Exception as e:
        log.error(f"[News] Failed to fetch {feed_key}: {type(e).__name__}: {e}")
        return []


def _generate_news_reading_question(article: dict, feed_name: str, level: str = "B2") -> Optional[dict]:
    """ニュース記事の見出し+短い要約を seed に、AI で読解問題を生成。
    元記事の文章は引用せず、AI が独自に「同じテーマで同じ語彙レベルの 250-350 語の本文」を執筆。
    元 URL は参考リンクとして出題に併記。"""
    if not ANTHROPIC_API_KEY:
        return None

    system = f"""あなたは英語学習教材の編集者です。{feed_name} で報じられた話題をもとに、英語読解問題を作成してください。

【絶対遵守】
- 元記事の文章を引用しない (著作権)。AI が独自に同じテーマ・同じ語彙レベル・250-350 語で本文を執筆する。
- 本文の文体は一般的なニュース英語 ({feed_name} 風・客観的・第三者視点)
- CEFR {level} レベル相当の語彙・文法に統制する
- 設問は内容理解・推論・語彙の意味推定をバランス良く 5問 (4択)
- 解説は日本語で、正解の根拠 + 他選択肢の誤り + 関連語彙/文法を丁寧に
- 「📰 元記事を読んでみよう」として元記事 URL を末尾に併記する案内文を included_link_message に入れる
- 出力は純粋なJSONのみ"""

    user = f"""【seed 情報 (これを参考に AI が独自に本文を書く)】
ニュースソース: {feed_name}
見出し: {article.get('title')}
要約 (RSS): {article.get('summary', '')[:400]}

【あなたへの指示】
1. 上記の話題と同じテーマを扱う、独自の英語ニュース記事 (250-350 語) を書いてください。元記事の文を引用しない。
2. 5問の理解問題 (4択) を作成。
3. CEFR {level} レベルに統制。

【出力形式】純粋なJSONのみ:
{{
  "passage": "AI が書いた独自の英語本文 (250-350 語)",
  "audio_script": "",
  "prompt": "",
  "source_title": {json.dumps(article.get('title', ''))},
  "source_url": {json.dumps(article.get('link', ''))},
  "source_feed": {json.dumps(feed_name)},
  "level": "{level}",
  "included_link_message": "📰 元記事 ({feed_name}) を読み比べてみよう: ...",
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice",
      "stem": "問題文",
      "choices": ["A", "B", "C", "D"],
      "answer": "正解 (0始まり)",
      "explanation": "解説 (日本語、3行以上)"
    }}
  ]
}}"""

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({
                "model": EXAM_QUESTIONS_MODEL,
                "max_tokens": 4000,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }).encode("utf-8"),
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip().rstrip("`").strip()
        return json.loads(text)
    except Exception as e:
        log.error(f"[News] Generation failed: {type(e).__name__}: {e}")
        return None


@app.get("/api/news/feeds")
def list_news_feeds():
    """利用可能な英語ニュースソース一覧"""
    return {"feeds": [{"key": k, **v} for k, v in NEWS_FEEDS.items()]}


@app.get("/api/news/articles")
def list_news_articles(feed: str = "cnn", limit: int = 5):
    """指定フィードの最新記事一覧 (タイトル+URL+短いsummary・記事本文は含まない)"""
    limit = max(1, min(limit, 10))
    items = _fetch_news_feed(feed, limit=limit)
    return {"feed": feed, "feed_name": NEWS_FEEDS.get(feed, {}).get("name", feed), "count": len(items), "articles": items}


@app.post("/api/news/generate-question")
def generate_news_question(payload: dict):
    """指定記事 (またはランダム選択) から英語読解問題を AI 生成して返す。
    payload: {"feed": "cnn", "index": 0}  # index 省略時はランダム
    レート制限: IP ベース 10 req/min。"""
    feed_key = (payload or {}).get("feed", "cnn")
    if feed_key not in NEWS_FEEDS:
        raise HTTPException(status_code=400, detail=f"Unknown feed: {feed_key}")
    feed = NEWS_FEEDS[feed_key]
    articles = _fetch_news_feed(feed_key, limit=10)
    if not articles:
        raise HTTPException(status_code=503, detail="記事の取得に失敗しました")
    idx = (payload or {}).get("index")
    if idx is None or not isinstance(idx, int) or idx < 0 or idx >= len(articles):
        import random
        article = random.choice(articles)
    else:
        article = articles[idx]
    question = _generate_news_reading_question(article, feed["name"], feed.get("level", "B2"))
    if not question:
        raise HTTPException(status_code=503, detail="問題生成に失敗しました")
    return {
        "feed": feed_key,
        "feed_name": feed["name"],
        "level": feed.get("level"),
        "article": article,  # 生徒に元記事リンクを表示するため
        "question": question,
    }


@app.post("/api/admin/sns/run-now")
def admin_sns_run_now(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """Daily SNS 投稿を今すぐ生成→送信(手動トリガー)。
    認証は admin Bearer または x-cron-secret のどちらでも可。
    今日既に送信済みの場合は重複防止で skip する。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    return _run_daily_sns_post()


@app.get("/api/admin/sns/history")
def admin_sns_history(authorization: Optional[str] = Header(None), days: int = 14):
    """過去N日の生成履歴を返す(CEOダッシュボード用)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")
    since = datetime.now(timezone.utc) - timedelta(days=days)
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT props, created_at FROM events WHERE name = 'daily_sns_post' AND created_at >= ? ORDER BY created_at DESC",
            (since,)
        )
        rows = c.fetchall()
    except Exception as e:
        log.error(f"sns_history query failed: {e}")
        rows = []
    conn.close()
    history = []
    for r in rows:
        try:
            props = json.loads(r["props"] or "{}")
        except Exception:
            props = {}
        history.append({
            "created_at": str(r["created_at"]),
            "model": props.get("model", ""),
            "resend_id": props.get("resend_id", ""),
            "posts": props.get("posts", []),
        })
    return {"days": days, "count": len(history), "history": history}


@app.post("/api/admin/monitor/run-now")
def admin_monitor_run_now(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """監視を今すぐ実行 (手動トリガー)。admin Bearer or x-cron-secret 認証。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    return _run_monitor_check()


@app.get("/api/admin/monitor/status")
def admin_monitor_status(authorization: Optional[str] = Header(None)):
    """現状の health snapshot を返す (アラート判定もまとめて)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")
    snapshot = _collect_health_snapshot()
    alerts = _evaluate_alerts(snapshot)
    return {
        "snapshot": snapshot,
        "alerts": alerts,
        "alerts_count": len(alerts),
        "monitoring_enabled": MONITORING_ENABLED,
        "monitoring_interval_min": MONITORING_INTERVAL_MIN,
        "monitoring_to_email": MONITORING_TO_EMAIL[:3] + "***" if MONITORING_TO_EMAIL else "",
    }


@app.post("/api/admin/monitor/daily-summary-now")
def admin_monitor_daily_summary_now(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """デイリーサマリを今すぐ送信 (手動)。今日既に送信済みでも force=1 で再送可能。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    snapshot = _collect_health_snapshot()
    subject, html = _format_daily_summary(snapshot)
    result = _send_monitor_email(subject, html)
    return {"sent": result.get("sent"), "snapshot": snapshot, "subject": subject}


@app.get("/api/auth/me")
def auth_me(authorization: Optional[str] = Header(None)):
    """現在のセッションを検証して生徒情報を返す。全ページのアクセスガードに使う。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"ok": True, "student": student}


def _get_waiver_count() -> int:
    """これまでキャンペーンで入塾金免除を受けた生徒数を返す。
    enrollment_waiver_applied_at IS NOT NULL で絞ることで、
    キャンペーン開始前の既存 paid 顧客 (waived=0 のまま) や
    手動で waived=1 にした旧データを除外する。"""
    conn = db()
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) AS n FROM students "
        "WHERE enrollment_fee_waived = 1 AND enrollment_waiver_applied_at IS NOT NULL"
    )
    row = c.fetchone()
    conn.close()
    return int(row["n"]) if row else 0


def _is_waiver_eligible() -> bool:
    """現時点で入塾金免除キャンペーンの枠が残っているか。"""
    if not ENROLLMENT_WAIVER_CAMPAIGN_ENABLED:
        return False
    return _get_waiver_count() < ENROLLMENT_WAIVER_LIMIT


@app.get("/api/campaigns/enrollment-waiver/status")
def waiver_status():
    """入塾金免除キャンペーンの残枠を返す (公開エンドポイント)。
    LP/checkout のバナー表示に使用。"""
    used = _get_waiver_count()
    remaining = max(0, ENROLLMENT_WAIVER_LIMIT - used)
    return {
        "enabled": ENROLLMENT_WAIVER_CAMPAIGN_ENABLED,
        "limit": ENROLLMENT_WAIVER_LIMIT,
        "used": used,
        "remaining": remaining,
        "is_active": ENROLLMENT_WAIVER_CAMPAIGN_ENABLED and remaining > 0,
        "discount_amount": ENROLLMENT_FEE,
    }


@app.get("/api/usage/me")
def usage_me(authorization: Optional[str] = Header(None)):
    """ログイン中の生徒の今月の使用回数 + プラン上限を返す。
    フロントの「残り○回」表示・アップグレード誘導に使用。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    plan = (student.get("plan") or "trial").lower()
    quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["trial"])
    used = _get_all_monthly_usage(int(student["id"]))
    out = {}
    for feature in QUOTA_FEATURES:
        limit = quotas.get(feature)
        used_count = used.get(feature, 0)
        out[feature] = {
            "limit": limit,        # None = 無制限
            "used": used_count,
            "remaining": (None if limit is None else max(0, limit - used_count)),
        }
    return {
        "ok": True,
        "plan": plan,
        "year_month": _jst_year_month(),
        "usage": out,
    }


@app.post("/api/trial/signup")
def trial_signup(payload: TrialSignup):
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=FOUNDER_TRIAL_DAYS)  # 7日間の完全無料体験
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
    """7日間 完全無料 体験 (GW 集中体験戦略)。Stripe 決済は発生しない。
    創設メンバー50名枠は本契約 (paid) のみでカウント。体験は無制限に受付。
    """
    email = (payload.get("email") or "").strip()
    name = (payload.get("name") or "").strip()
    student_id = payload.get("student_id")
    if not email:
        raise HTTPException(status_code=400, detail="email required")

    # 完全無料体験: Stripe をスキップして即時 success ページへ
    if FOUNDER_TRIAL_PRICE == 0:
        return {
            "free": True,
            "checkout_url": f"{BASE_URL}/checkout-success.html?session_id=free_trial&student_id={student_id or ''}",
            "amount": 0,
            "trial_days": FOUNDER_TRIAL_DAYS,
        }

    # 以下、有償体験に戻す場合のフォールバック (現状は使用されない)
    conn_fc = db()
    c_fc = conn_fc.cursor()
    try:
        c_fc.execute(
            "SELECT COUNT(*) FROM students WHERE status='paid' AND plan IS NOT NULL"
        )
        taken = c_fc.fetchone()[0]
    except Exception:
        taken = 0
    conn_fc.close()
    if taken >= FOUNDER_LIMIT and not student_id:
        raise HTTPException(
            status_code=403,
            detail=f"創設メンバー{FOUNDER_LIMIT}名の募集は終了しました。次期募集をお待ちください。"
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
                    "name": f"AI学習コーチ塾 - {FOUNDER_TRIAL_DAYS}日間体験",
                    "description": f"AIチューター・教材生成・学習分析をフル活用できる{FOUNDER_TRIAL_DAYS}日間。"
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
    - 創設メンバープラン (founder_special): 永年¥14,500/月 (50名限定・全機能無制限) + 入塾金 ¥10,000
    - 通常プラン (standard/premium/family): 月額サブスク + 初回請求に入塾金 ¥10,000 を追加
    - 塾生アドオン (student_addon): 入塾金なし、月額 ¥15,000 のみ
    - 体験は別途 /api/stripe/trial-checkout で 7日間 完全無料 (Stripe を経由しない)
    """
    price_info = PRICE_MAP.get(payload.plan)
    if not price_info:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {payload.plan}")
    price_id, amount, plan_name, max_students = price_info
    # 🎁 founder_special / founder1: env が空でも lookup_key で動的解決を試みる
    if payload.plan in ("founder_special", "founder1") and not price_id:
        price_id = _lookup_founder_special_price_id()
        if not price_id:
            raise HTTPException(
                status_code=503,
                detail="創設メンバープランの Stripe Price が未設定です。管理者に通知済 (admin endpoint で setup してください)。"
            )

    # 創設メンバー枠チェック: LP で「50名限定」と約束しているため、既存 paid 生徒が
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
                detail=f"創設メンバー{FOUNDER_LIMIT}名の募集は終了しました。次期募集をお待ちください。"
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
    # 体験期間は別途 /api/stripe/trial-checkout で 7日間 完全無料 (Stripe 不経由)。
    # 入塾金はWebhook (checkout.session.completed) で InvoiceItem として
    # 顧客に作成 → 初回請求書に自動的に乗る。
    # 先着100名キャンペーン枠が残っていれば入塾金免除フラグを立てる
    waiver_eligible = (
        payload.plan not in ENROLLMENT_FEE_EXEMPT
        and _is_waiver_eligible()
    )
    needs_enrollment_fee = (payload.plan not in ENROLLMENT_FEE_EXEMPT) and not waiver_eligible
    subscription_data = {
        "metadata": {
            "plan": payload.plan,
            "student_id": str(payload.student_id or ""),
            "max_students": str(max_students),
            "founder": "1",
            "needs_enrollment_fee": "1" if needs_enrollment_fee else "0",
            "enrollment_waiver_applied": "1" if waiver_eligible else "0",
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
            "enrollment_waiver_applied": "1" if waiver_eligible else "0",
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
            if k in ("founder1", "standard", "premium", "family", "student_addon")
        },
        "enrollment_fee": ENROLLMENT_FEE,
        "trial_fee": FOUNDER_TRIAL_PRICE,
        "trial_duration_days": FOUNDER_TRIAL_DAYS,
    }

def _calculate_dynamic_fake_taken(real_paid: int) -> int:
    """カモフラージュ申込数を動的計算 (FOMO 加速設計)。
    要素:
      - BASE (デフォルト26): ローンチ初日の最低カモフラージュ
      - MULTIPLIER (デフォルト2.0): 実申込1名あたりの追加偽申込
      - DAILY_GROWTH (デフォルト0.5): 1日あたりの自然増 (週で +3.5)
    最終的に MIN_REMAINING で下限保護 (残0=売り止め印象を防ぐ)。"""
    import time
    days_since_launch = max(0, (time.time() - SERVICE_LAUNCH_TS) / 86400)
    natural_growth = int(days_since_launch * FOUNDER_PUBLIC_FAKE_DAILY_GROWTH)
    fomo_boost = int(real_paid * FOUNDER_PUBLIC_FAKE_MULTIPLIER)
    return real_paid + FOUNDER_PUBLIC_FAKE_BASE + fomo_boost + natural_growth


@app.get("/api/founders/count")
def founders_count(public: bool = False):
    """創設メンバーの残り枠をカウント。
    status='paid' の全プラン（新規: founder_special/standard/premium/family/student_addon,
    旧: ai/hybrid/intensive）を対象。トライアル中も status='paid' が立つため、
    実際に枠を占有している全員をカウントする。

    public=1 (顧客向け): 動的計算カモフラージュ値を返す (FOMO設計)。
      実申込が増えるほど + 経過日数が増えるほど 残枠表示が縮小する。
      env で BASE/MULTIPLIER/DAILY_GROWTH/MIN_REMAINING を調整可能。
    public未指定 (内部用): 実数値を返す (CEOダッシュボード用)。"""
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
    real_remaining = max(0, FOUNDER_LIMIT - paid)
    if public:
        # 動的カモフラージュ計算
        public_taken = _calculate_dynamic_fake_taken(paid)
        # 最低 MIN_REMAINING 名は残す (「残0」=完売印象を防ぐ)
        public_remaining = max(FOUNDER_PUBLIC_MIN_REMAINING, FOUNDER_LIMIT - public_taken)
        public_taken = FOUNDER_LIMIT - public_remaining
        return {"limit": FOUNDER_LIMIT, "taken": public_taken, "remaining": public_remaining}
    return {"limit": FOUNDER_LIMIT, "taken": paid, "remaining": real_remaining}

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
            # 完全無料 7日体験 (GW集中体験戦略): status='trial', trial_start=now, trial_end=now+7d
            # Stripe 決済不要。自動課金は発生しない。
            now = datetime.now(timezone.utc)
            trial_end = now + timedelta(days=FOUNDER_TRIAL_DAYS)
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

            # 入塾金 InvoiceItem (月額のみ・先着100名キャンペーン適用時はスキップ)
            # Race condition 対策: webhook 処理時に再度枠チェック (atomic)。
            # checkout時に枠ありと判定されても、webhook処理時には100名超過している可能性があるため。
            session_waiver_flag = meta.get("enrollment_waiver_applied") == "1"
            apply_waiver_now = False
            if session_waiver_flag and customer:
                # 現在の適用済み数を再カウントして上限内か判定
                current_count = _get_waiver_count()
                if current_count < ENROLLMENT_WAIVER_LIMIT:
                    apply_waiver_now = True
                else:
                    log.warning(
                        f"⚠️ Enrollment waiver requested but limit reached "
                        f"(used={current_count}/{ENROLLMENT_WAIVER_LIMIT}). "
                        f"Falling back to standard enrollment fee. customer={customer}"
                    )

            if (meta.get("needs_enrollment_fee") == "1" or (session_waiver_flag and not apply_waiver_now)) and customer:
                try:
                    s.InvoiceItem.create(
                        customer=customer, amount=ENROLLMENT_FEE, currency="jpy",
                        description="入塾金（システム登録費用・初回のみ）",
                        metadata={"plan": plan, "type": "enrollment_fee"},
                    )
                    log.info(f"✅ Enrollment fee InvoiceItem created: customer={customer}")
                except Exception as e:
                    log.error(f"Failed to create enrollment fee InvoiceItem: {type(e).__name__}: {e}")
            elif apply_waiver_now:
                # キャンペーン適用確定 → DB に免除フラグ + 適用日時を記録
                try:
                    if student_id and student_id != "":
                        c.execute(
                            "UPDATE students SET enrollment_fee_waived = 1, "
                            "enrollment_waiver_applied_at = CURRENT_TIMESTAMP "
                            "WHERE id = ? AND enrollment_waiver_applied_at IS NULL",
                            (student_id,),
                        )
                    elif email:
                        c.execute(
                            "UPDATE students SET enrollment_fee_waived = 1, "
                            "enrollment_waiver_applied_at = CURRENT_TIMESTAMP "
                            "WHERE email = ? AND enrollment_waiver_applied_at IS NULL",
                            (email,),
                        )
                    conn.commit()
                    log.info(f"✅ Enrollment fee WAIVED (campaign): customer={customer} student_id={student_id} email={email}")
                except Exception as e:
                    log.error(f"Failed to mark enrollment_fee_waived: {type(e).__name__}: {e}")

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
                f"{p.get('name', '生徒')}さんは7日間で:\n"
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
    # 月次クォータの対象機能。"problems"/"essays"/"textbooks" のいずれか
    # それ以外の値 (chat等) は制限なし
    feature: Optional[str] = None

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


# ==========================================================================
# 月次クォータ (プランごとの「使えるシステム」差別化)
# ==========================================================================
def _jst_year_month() -> str:
    """JST(UTC+9) ベースの 'YYYYMM' を返す。Stripe請求月と一致させる。"""
    now = datetime.now(timezone.utc) + timedelta(hours=9)
    return now.strftime("%Y%m")


def _get_monthly_usage(student_id: int, feature: str, year_month: Optional[str] = None) -> int:
    """この生徒の今月の機能別使用回数を返す。"""
    if not year_month:
        year_month = _jst_year_month()
    conn = db()
    c = conn.cursor()
    c.execute(
        "SELECT used_count FROM usage_monthly WHERE student_id = ? AND feature = ? AND year_month = ?",
        (student_id, feature, year_month),
    )
    row = c.fetchone()
    conn.close()
    return int(row["used_count"]) if row else 0


def _get_all_monthly_usage(student_id: int, year_month: Optional[str] = None) -> dict:
    """この生徒の今月の全機能の使用回数を {feature: count} で返す。"""
    if not year_month:
        year_month = _jst_year_month()
    conn = db()
    c = conn.cursor()
    c.execute(
        "SELECT feature, used_count FROM usage_monthly WHERE student_id = ? AND year_month = ?",
        (student_id, year_month),
    )
    rows = c.fetchall()
    conn.close()
    return {r["feature"]: int(r["used_count"]) for r in rows}


def _check_quota(student: dict, feature: str) -> None:
    """その生徒のプランで feature が今月の上限に達していないか確認。
    達していれば 429 + プラン情報付きエラーを返す。"""
    if feature not in QUOTA_FEATURES:
        return  # クォータ対象外
    plan = (student.get("plan") or "trial").lower()
    quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["trial"])
    limit = quotas.get(feature)
    if limit is None:
        return  # 無制限
    used = _get_monthly_usage(int(student["id"]), feature)
    if used >= limit:
        feature_label = {"problems": "問題生成", "essays": "添削", "textbooks": "参考書生成"}.get(feature, feature)
        raise HTTPException(
            status_code=429,
            detail=(
                f"今月の{feature_label}回数 {limit}回 の上限に達しました。"
                f"プレミアムプランにアップグレードすると無制限で使えます。"
            ),
        )


def _increment_usage(student_id: int, feature: str) -> int:
    """使用回数を +1。INSERT or UPDATE (UPSERT)。新カウントを返す。"""
    if feature not in QUOTA_FEATURES:
        return 0
    year_month = _jst_year_month()
    conn = db()
    c = conn.cursor()
    # 既存行を update を試みて、影響行 0 なら insert (Postgres/SQLite 両対応)
    c.execute(
        "UPDATE usage_monthly SET used_count = used_count + 1 "
        "WHERE student_id = ? AND feature = ? AND year_month = ?",
        (student_id, feature, year_month),
    )
    if c.rowcount == 0:
        try:
            c.execute(
                "INSERT INTO usage_monthly (student_id, feature, year_month, used_count) "
                "VALUES (?, ?, ?, 1)",
                (student_id, feature, year_month),
            )
        except Exception:
            # 並行 INSERT で重複した場合の救済
            c.execute(
                "UPDATE usage_monthly SET used_count = used_count + 1 "
                "WHERE student_id = ? AND feature = ? AND year_month = ?",
                (student_id, feature, year_month),
            )
    conn.commit()
    new_count = _get_monthly_usage(student_id, feature, year_month)
    conn.close()
    return new_count


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
    student_row = None
    try:
        student_row = _verify_student_active(payload.student_id)
        _check_ai_budget(payload.student_id)
        # 機能別月次クォータ check (problems / essays / textbooks)
        if payload.feature:
            _check_quota(student_row, payload.feature)
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

        # 機能別月次カウント+1 (problems / essays / textbooks のみ)
        # API 呼び出し成功後に increment する (失敗時は加算しないことでフェアネス確保)
        if payload.student_id and payload.feature in QUOTA_FEATURES:
            try:
                _increment_usage(int(payload.student_id), payload.feature)
            except Exception as e:
                log.warning(f"_increment_usage failed silently: {e}")

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
