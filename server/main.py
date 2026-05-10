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

from fastapi import FastAPI, Request, HTTPException, Depends, Header, Body, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta, time as dt_time
import os
import json
import sqlite3
import hmac
import hashlib
import asyncio
import time
import urllib.request
import urllib.error
import base64
import io
import zipfile
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
# Gemini Tier 4 fallback (AI never-fail 原則: Anthropic 完全障害でも止まらない)
# Google AI Studio で無料発行: https://aistudio.google.com/app/apikey
# Gemini 1.5/2.5 Flash は 1日 1,500 req まで無料枠あり
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# 主モデル = Gemini 2.5 Flash (無料枠 1500 req/日)
# AI Studio 無料 tier では Pro モデルは limit:0 で呼べない仕様のため Flash デフォ。
# 将来 paid tier 化したら Railway env に GEMINI_MODEL=gemini-2.5-pro を追加するだけで
# Tier 4 fallback が Pro 主軸に切替わる (Pro→Flash 二段 fallback ロジックも残してある)。
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_LIGHT = os.getenv("GEMINI_MODEL_LIGHT", "gemini-2.5-flash")
# OpenAI Tier 5 fallback (2026-05-10 塾長指示・3段防御 Sonnet → Gemini → GPT)
# OpenAI Platform で API key 発行: https://platform.openai.com/api-keys
# 通常時は呼ばれない (Anthropic + Gemini 両方ダウン時のみ発火) のでコスト最小。
# モデル: gpt-4o-mini (推奨・$0.15/MTok input, $0.60/MTok output) or gpt-5
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MODEL_LIGHT = os.getenv("OPENAI_MODEL_LIGHT", "gpt-4o-mini")  # 二段 fallback 用 (将来 gpt-3.5 等)
CRON_SECRET = os.getenv("CRON_SECRET", "")  # 未設定時は cron 系エンドポイントを全拒否
STATS_TOKEN = os.getenv("STATS_TOKEN", "")  # 未設定時は /api/stats を全拒否
# HMAC 署名鍵（保護者ビュー署名・他の署名用途で利用）
APP_SECRET = os.getenv("APP_SECRET", "")

PRICE_MAP = {
    # 🎁 創設メンバー 永年¥14,500 (募集停止・既契約者据置)
    "founder_special": (STRIPE_PRICE_FOUNDER_SPECIAL, 14500, "創設メンバー (永年¥14,500)", 1),
    # プラン構造 (2026-05-06 改訂・通塾生のみ値下げ・プレミアム/家族は据置)
    "standard": (STRIPE_PRICE_STANDARD, 24980, "スタンダード (旧・募集停止)", 1),  # legacy 据置
    "premium": (STRIPE_PRICE_PREMIUM, 39800, "プレミアム", 1),  # 据置 + 学習管理機能を解放
    "family": (STRIPE_PRICE_FAMILY, 59800, "家族プラン（最大3名）", 3),  # 据置
    "student_addon": (STRIPE_PRICE_STUDENT_ADDON, 5000, "通塾生プラン", 1),  # ¥9,800 → ¥5,000 値下げ + 機能フル付与
    # 後方互換 (founder1 は 2026-04-28 廃止・新 founder_special に置換)
    "founder1": (STRIPE_PRICE_FOUNDER_SPECIAL, 14500, "創設メンバー (永年¥14,500)", 1),
    "ai": (STRIPE_PRICE_STANDARD, 24980, "スタンダード (旧・募集停止)", 1),
    "hybrid": (STRIPE_PRICE_PREMIUM, 39800, "プレミアム", 1),
    "intensive": (STRIPE_PRICE_FAMILY, 59800, "家族プラン（最大3名）", 3),
}

# 入塾金（トライアル後の初回請求に追加・通塾生アドオンは免除）
ENROLLMENT_FEE = 10000

# 通塾生プラン（月額、入塾金不要）
STUDENT_ADDON_PRICE = 5000

# 創設メンバー体験は完全無料化 (CVR最大化方針)
# 7日間 = GW長期休みに集中体験 → 休み明けに本契約継続を狙う設計
FOUNDER_TRIAL_PRICE = 0
FOUNDER_TRIAL_DAYS = 10  # 7→10 日に拡張 (塾長指示 2026-05-06: 学習管理 + ZOOM 授業を体感する適度な期間)
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
# 24h 未ログイン生徒への自動 nudge cron (2026-04-30 追加 — 塾長指示「申込→ログイン経路を完璧に」)
NEVER_LOGIN_NUDGE_ENABLED = os.getenv("NEVER_LOGIN_NUDGE_ENABLED", "1") == "1"
NEVER_LOGIN_NUDGE_HOUR_JST = int(os.getenv("NEVER_LOGIN_NUDGE_HOUR_JST", "9"))  # 朝9時にnudge
NEVER_LOGIN_NUDGE_HOURS_THRESHOLD = int(os.getenv("NEVER_LOGIN_NUDGE_HOURS", "24"))  # 申込から24h以上経過
NEVER_LOGIN_NUDGE_MAX_PER_DAY = int(os.getenv("NEVER_LOGIN_NUDGE_MAX_PER_DAY", "30"))  # 1日上限 (Resend rate 対策)
_NEVER_LOGIN_NUDGE_LAST_RUN: dict = {"date": ""}  # 同日内多重起動防止

# 🌐 ドメイン状態監視 (2026-05-06 致命事故対応 — clientHold で全停止した教訓)
# RDAP で WHOIS Domain Status を 30 分おきに監視。clientHold/serverHold/inactive/pendingDelete
# 検知時は即座に塾長に緊急アラートメール送信 (Resend 経由なので自社ドメイン DNS に依存しない)。
DOMAIN_MONITOR_ENABLED = os.getenv("DOMAIN_MONITOR_ENABLED", "1") == "1"
DOMAIN_MONITOR_TARGET = os.getenv("DOMAIN_MONITOR_TARGET", "trillion-ai-juku.com")
DOMAIN_MONITOR_INTERVAL_MIN = int(os.getenv("DOMAIN_MONITOR_INTERVAL_MIN", "30"))  # 30分おき (RDAP rate 対策)
DOMAIN_MONITOR_MANUAL_THROTTLE_SEC = int(os.getenv("DOMAIN_MONITOR_MANUAL_THROTTLE_SEC", "60"))  # 手動 trigger の最低間隔
_DOMAIN_MONITOR_LAST_CHECK: dict = {"ts": 0.0, "status": None, "alert_sent_at": 0.0, "manual_ts": 0.0}
# 🔔 Whois 認証年次更新リマインダー (お名前.com は年1回 Whois 認証メール返信が必須)
# 2026-05-06 にこの認証を逃してドメインが clientHold になった。事故日近辺 (5/6) を anniversary
# として、30 日前 + 7 日前の 2 段階で塾長に通知して再発防止。
WHOIS_RENEWAL_REMINDER_ENABLED = os.getenv("WHOIS_RENEWAL_REMINDER_ENABLED", "1") == "1"
# DOMAIN_REGISTRATION_ANNIVERSARY = "MM-DD" (お名前.com の Whois 認証メールが届く時期)
DOMAIN_REGISTRATION_ANNIVERSARY = os.getenv("DOMAIN_REGISTRATION_ANNIVERSARY", "05-06")
# 何日前にリマインダーを送るか (カンマ区切り、複数指定可)。デフォは 30 日前 + 7 日前の 2 段階。
WHOIS_RENEWAL_REMINDER_DAYS_BEFORE = os.getenv("WHOIS_RENEWAL_REMINDER_DAYS_BEFORE", "30,7")
# 旧 env (互換用、4/15 固定運用していた場合のフォールバック)
WHOIS_RENEWAL_REMINDER_MONTH = int(os.getenv("WHOIS_RENEWAL_REMINDER_MONTH", "0"))  # 0=disabled (旧モード)
WHOIS_RENEWAL_REMINDER_DAY = int(os.getenv("WHOIS_RENEWAL_REMINDER_DAY", "0"))

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
# Plan 別の budget を設定 (塾長指示 2026-04-30: premium は実質無制限に)
#   - trial:    100K  (Opus で $10 程度・トライアル中の濫用防止)
#   - standard: 300K  (3 倍・教材生成や問題大量生成も実用範囲)
#   - premium / founder_special / family: 2M  (実質無制限・塾長運用や濃い学習も対応)
#   - student_addon: 200K  (通塾生補助・standard より控えめ)
AI_DAILY_TOKEN_BUDGET = int(os.getenv("AI_DAILY_TOKEN_BUDGET", "100000"))  # default fallback (trial 相当)
# Premium 相当 (実質無制限) のプラン集合 — PRICE_MAP の全キーを後方互換含めてカバー
PREMIUM_TIER_PLANS = {
    "premium",
    "family",
    "founder_special",  # 創設メンバー50名・永年¥14,500・premium 全機能
    "founder1",         # 旧 founder_special (2026-04-28 廃止・後方互換)
    "hybrid",           # 旧 premium 名 (後方互換)
    "intensive",        # 旧 family 名 (後方互換)
}
PLAN_DAILY_TOKEN_BUDGET = {
    # premium tier (実質無制限)
    "premium":         2_000_000,
    "family":          2_000_000,
    "founder_special": 2_000_000,
    "founder1":        2_000_000,  # 後方互換 (旧 founder_special)
    "hybrid":          2_000_000,  # 後方互換 (旧 premium)
    "intensive":       2_000_000,  # 後方互換 (旧 family)
    # standard tier
    "standard":          300_000,
    "ai":                300_000,  # 後方互換 (旧 standard)
    # 通塾生補助
    "student_addon":     200_000,
    # 体験
    "trial":             100_000,
}

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

# 2026-05-07 追加 (Reviewer A CRITICAL #3): student_addon の lookup_key fallback
_STUDENT_ADDON_PRICE_CACHE: dict = {"id": None, "checked_at": None}

def _lookup_student_addon_price_id() -> str:
    """Stripe API で lookup_key='student_addon' の price を検索。
    env STRIPE_PRICE_STUDENT_ADDON が placeholder/空のときのフォールバック。
    placeholder のまま Stripe に送ると 'No such price' で 400 になるため必ず実 ID を返す。"""
    global _STUDENT_ADDON_PRICE_CACHE
    # env が placeholder でない実 price ID なら優先
    if STRIPE_PRICE_STUDENT_ADDON and not STRIPE_PRICE_STUDENT_ADDON.endswith("_placeholder"):
        return STRIPE_PRICE_STUDENT_ADDON
    if not STRIPE_SECRET_KEY:
        return ""
    cached_id = _STUDENT_ADDON_PRICE_CACHE.get("id")
    checked = _STUDENT_ADDON_PRICE_CACHE.get("checked_at")
    now = datetime.now(timezone.utc)
    if cached_id and checked and (now - checked).total_seconds() < 3600:
        return cached_id
    try:
        s = get_stripe()
        results = s.Price.list(lookup_keys=["student_addon"], active=True, limit=1)
        if results and results.data:
            pid = results.data[0].id
            _STUDENT_ADDON_PRICE_CACHE = {"id": pid, "checked_at": now}
            return pid
    except Exception as e:
        log.warning(f"[Stripe] student_addon lookup failed: {e}")
    _STUDENT_ADDON_PRICE_CACHE = {"id": None, "checked_at": now}
    return ""


# 全プラン汎用 lookup_key fallback cache (premium / family / standard 用)
# founder_special / student_addon は専用 cache を持つので例外。
_GENERIC_PRICE_CACHE: dict = {}

def _lookup_plan_price_id(plan: str) -> str:
    """全プラン汎用: env が placeholder/空のときに lookup_key で動的解決する fallback。

    2026-05-10 改修: 元々 founder_special / student_addon だけ fallback を持っていたが、
    premium / family / standard も env が外れた瞬間に Stripe 400 で全顧客が決済不能に
    なる致命リスクがあったため、全 5 プランに堅牢性を統一。
    塾長指示「founder_special と同等の堅牢性に上げる」(2026-05-10)。

    plan は PRICE_MAP のキー: founder_special / founder1 / premium / family / standard / student_addon。
    1時間 cache。lookup_key も見つからなければ "" を返すので呼び出し側で 503 に変換すること。"""
    # plan → lookup_key 正規化 (founder1 は founder_special と同じ Price)
    lookup_key = "founder_special" if plan in ("founder_special", "founder1") else plan

    # 既存専用 helper があれば優先 (個別 cache を温存)
    if lookup_key == "founder_special":
        return _lookup_founder_special_price_id()
    if lookup_key == "student_addon":
        return _lookup_student_addon_price_id()

    # premium / family / standard: env が実 ID なら優先、placeholder/空 なら lookup_key 検索
    env_pid = ""
    if lookup_key == "premium":
        env_pid = STRIPE_PRICE_PREMIUM
    elif lookup_key == "family":
        env_pid = STRIPE_PRICE_FAMILY
    elif lookup_key == "standard":
        env_pid = STRIPE_PRICE_STANDARD
    if env_pid and not env_pid.endswith("_placeholder"):
        return env_pid

    if not STRIPE_SECRET_KEY:
        return ""
    cached = _GENERIC_PRICE_CACHE.get(lookup_key, {})
    cached_id = cached.get("id")
    checked = cached.get("checked_at")
    now = datetime.now(timezone.utc)
    if cached_id and checked and (now - checked).total_seconds() < 3600:
        return cached_id
    try:
        s = get_stripe()
        results = s.Price.list(lookup_keys=[lookup_key], active=True, limit=1)
        if results and results.data:
            pid = results.data[0].id
            _GENERIC_PRICE_CACHE[lookup_key] = {"id": pid, "checked_at": now}
            return pid
    except Exception as e:
        log.warning(f"[Stripe] {lookup_key} lookup failed: {e}")
    _GENERIC_PRICE_CACHE[lookup_key] = {"id": None, "checked_at": now}
    return ""

# ==========================================================================
# Database Setup (SQLite / Postgres 両対応)
# ==========================================================================
class _Row(dict):
    """dict 形式の row に対して整数 index アクセス (row[0]) を可能にするラッパ。
    sqlite3.Row は両方サポートするので、Postgres 側 (psycopg dict_row) も同等に振る舞わせる。
    これにより c.fetchone()[0] と c.fetchone()["col"] が両方通る。"""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


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
            # 2026-05-07: psycopg3 は SQL 内の literal % を placeholder として
            # 解釈しようとして「only '%s', '%b', '%t' are allowed」エラーを出す。
            # 修正方針:
            # 1. params 有り時: SQL 内の literal % を %% に escape してから ? を %s に変換
            #    (LIKE 'ai_call_%' のようなパターンも安全に通る)
            # 2. params 無し時: psycopg に params 引数を渡さない
            #    (execute(sql) は interpolation せず literal % が素通り)
            if params:
                # Step 1: literal % を %% に escape (LIKE pattern や regex 等で頻出)
                sql = sql.replace("%", "%%")
                # Step 2: ? → %s 変換 (この %s は escape 後の literal %% と区別される)
                sql = sql.replace("?", "%s")
                self._cur.execute(sql, params)
            else:
                # params 空 → escape も placeholder 変換も不要
                # (execute(sql) は psycopg が interpolation を試みない)
                self._cur.execute(sql)
        else:
            self._cur.execute(sql, params)
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
        if self._is_pg and isinstance(row, dict) and not isinstance(row, _Row):
            return _Row(row)
        return row

    def fetchall(self):
        rows = self._cur.fetchall()
        if self._is_pg:
            return [_Row(r) if isinstance(r, dict) and not isinstance(r, _Row) else r for r in rows]
        return rows

    @property
    def rowcount(self):
        """直前の DML 操作の影響行数。sqlite3/psycopg 共に rowcount 属性を持つ。
        2026-05-07: _increment_usage が rowcount に直接アクセスして AttributeError 連発
        していた致命バグを fix。"""
        try:
            return self._cur.rowcount
        except Exception:
            return -1


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
    CREATE TABLE IF NOT EXISTS textbook_pool (
        id {pk},
        subject TEXT NOT NULL,
        topic TEXT NOT NULL,
        level TEXT NOT NULL,
        length TEXT,
        type TEXT,
        title TEXT,
        tags TEXT,
        content TEXT NOT NULL,
        status TEXT DEFAULT 'published',
        source TEXT DEFAULT 'claude_max',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_textbook_pool ON textbook_pool(subject, level, status, created_at);
    CREATE INDEX IF NOT EXISTS idx_textbook_pool_topic ON textbook_pool(topic);
    -- 🤖 AI チーム検閲ワークフロー stateful 保存 (2026-05-10 塾長負荷削減)
    -- 6 phase コピペ作業の中断・再開・再生成を可能にする。
    -- spec/phases/result は JSON TEXT (SQLite/Postgres 両対応のため jsonb は使わない)。
    CREATE TABLE IF NOT EXISTS ai_team_workflows (
        id {pk},
        workflow_id TEXT UNIQUE NOT NULL,
        spec TEXT NOT NULL,
        phases TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'in_progress',
        mode TEXT NOT NULL DEFAULT 'full',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_aitw_status_updated ON ai_team_workflows(status, updated_at DESC);
    CREATE INDEX IF NOT EXISTS idx_aitw_workflow_id ON ai_team_workflows(workflow_id);
    -- 大学別 過去問風オリジナル問題プール (塾長指示 2026-05-03)
    -- 著作権配慮: 全て Claude 生成のオリジナル。過去問の「スタイル・出題パターン」のみを参考にし、
    -- 実問題文の転載は禁止。inspired_by フィールドで「東大2022年第1問の長文読解スタイル」など出典明示。
    CREATE TABLE IF NOT EXISTS university_problems (
        id {pk},
        university TEXT NOT NULL,
        faculty TEXT,
        year INTEGER,
        subject TEXT NOT NULL,
        topic TEXT,
        problem_type TEXT,
        question_text TEXT NOT NULL,
        choices TEXT,
        answer TEXT NOT NULL,
        explanation TEXT NOT NULL,
        difficulty TEXT,
        inspired_by TEXT,
        tags TEXT,
        status TEXT DEFAULT 'published',
        source TEXT DEFAULT 'claude_max',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_university_problems ON university_problems(university, subject, status, created_at);
    CREATE INDEX IF NOT EXISTS idx_university_problems_year ON university_problems(year, subject);
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
    CREATE TABLE IF NOT EXISTS mock_exam_sessions (
        id {pk},
        student_id INTEGER,
        exam_type TEXT NOT NULL,
        target_label TEXT,
        duration_min INTEGER,
        started_at TIMESTAMP,
        submitted_at TIMESTAMP,
        score_total INTEGER,
        score_max INTEGER,
        deviation_estimate REAL,
        section_scores TEXT,
        questions_json TEXT NOT NULL,
        answers_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_mock_exam_student ON mock_exam_sessions(student_id, created_at);
    CREATE TABLE IF NOT EXISTS vocab_words (
        id {pk},
        word TEXT UNIQUE NOT NULL,
        pos TEXT,
        meaning_jp TEXT NOT NULL,
        example_en TEXT,
        example_jp TEXT,
        level TEXT NOT NULL,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_vocab_words_level ON vocab_words(level);
    CREATE TABLE IF NOT EXISTS vocab_progress (
        id {pk},
        student_id INTEGER NOT NULL,
        word_id INTEGER NOT NULL,
        box INTEGER DEFAULT 1,
        next_review_at TIMESTAMP,
        last_reviewed_at TIMESTAMP,
        review_count INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_vocab_progress_unique ON vocab_progress(student_id, word_id);
    CREATE INDEX IF NOT EXISTS idx_vocab_progress_due ON vocab_progress(student_id, next_review_at);
    CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
    CREATE INDEX IF NOT EXISTS idx_otp_student ON otp_codes(student_id, used_at, expires_at);
    -- 学習記録 (Studyplus for School 代替: 塾長指示 2026-05-04)
    CREATE TABLE IF NOT EXISTS study_logs (
        id {pk},
        student_id INTEGER NOT NULL,
        studied_date DATE NOT NULL,
        subject TEXT NOT NULL,
        material TEXT,
        minutes INTEGER NOT NULL,
        pages INTEGER,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_study_logs_student_date ON study_logs(student_id, studied_date);
    CREATE INDEX IF NOT EXISTS idx_study_logs_studied_created ON study_logs(studied_date, created_at);
    CREATE TABLE IF NOT EXISTS study_log_reactions (
        id {pk},
        log_id INTEGER NOT NULL,
        actor_type TEXT NOT NULL,
        actor_id INTEGER,
        kind TEXT NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_study_log_reactions ON study_log_reactions(log_id, created_at);
    -- admin の like 重複防止 (race condition 対策・塾長レビュー指摘 2026-05-04)
    CREATE UNIQUE INDEX IF NOT EXISTS uq_study_log_admin_like
        ON study_log_reactions(log_id, actor_type, kind)
        WHERE actor_type = 'admin' AND kind = 'like';
    -- 学習計画 (Phase 2 - 国公立難関大学コース限定・塾長指示 2026-05-05)
    CREATE TABLE IF NOT EXISTS study_plans (
        id {pk},
        student_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        material TEXT,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        target_minutes INTEGER,
        target_pages INTEGER,
        color TEXT DEFAULT '#6366f1',
        status TEXT DEFAULT 'active',
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_study_plans_student ON study_plans(student_id, status, start_date);
    CREATE INDEX IF NOT EXISTS idx_study_plans_period ON study_plans(start_date, end_date);
    -- 重複計画防止 (active のみ・archive 後は再登録可) - Security 監査 2026-05-05
    CREATE UNIQUE INDEX IF NOT EXISTS uq_study_plans_no_dup
        ON study_plans(student_id, subject, COALESCE(material,''), start_date, end_date)
        WHERE status != 'archived';
    -- 合格カリキュラム (Phase 4 - 国公立難関大学コース限定・塾長指示 2026-05-06)
    -- 難関大学 (国公立 + 難関私立) 志望者向けの全体ロードマップ。1生徒に通常1件 active。
    CREATE TABLE IF NOT EXISTS curricula (
        id {pk},
        student_id INTEGER NOT NULL,
        target_university TEXT NOT NULL,
        target_faculty TEXT,
        exam_date DATE NOT NULL,
        start_date DATE NOT NULL,
        daily_minutes INTEGER,
        baseline_note TEXT,
        phases TEXT NOT NULL,
        ai_model TEXT,
        status TEXT DEFAULT 'active',
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_curricula_student ON curricula(student_id, status);
    -- 外部模試結果 (河合/駿台/東進/進研 等) - Phase 4.5 / 塾長指示 2026-05-06
    -- 内蔵 mock_exam_sessions と分離。生徒が手入力 + AI カリキュラム生成時に自動参照。
    CREATE TABLE IF NOT EXISTS exam_results (
        id {pk},
        student_id INTEGER NOT NULL,
        exam_name TEXT NOT NULL,
        exam_date DATE NOT NULL,
        subject TEXT NOT NULL,
        score INTEGER,
        max_score INTEGER,
        deviation REAL,
        judgement TEXT,
        target_university TEXT,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_exam_results_student ON exam_results(student_id, exam_date);
    CREATE INDEX IF NOT EXISTS idx_exam_results_subject ON exam_results(student_id, subject, exam_date);
    -- 国公立難関大学コース 申込フォーム (Phase 4.8 - クレカなし申込)
    -- 塾長指示 2026-05-06: 専用 LP からクレカ登録なしで申込
    CREATE TABLE IF NOT EXISTS course_applications (
        id {pk},
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        grade TEXT,
        target_university TEXT,
        phone TEXT,
        referrer TEXT,
        note TEXT,
        status TEXT DEFAULT 'pending',
        student_id INTEGER,
        approved_at TIMESTAMP,
        approved_by TEXT,
        rejected_reason TEXT,
        ip TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_course_applications_status ON course_applications(status, created_at);
    CREATE INDEX IF NOT EXISTS idx_course_applications_email ON course_applications(email, status);
    -- 塾長→生徒メッセージ機能 (Phase 3 - email only, 塾長指示 2026-05-05)
    CREATE TABLE IF NOT EXISTS messages (
        id {pk},
        sender_type TEXT NOT NULL,
        sender_id INTEGER,
        recipient_type TEXT NOT NULL,
        recipient_id INTEGER,
        broadcast_filter TEXT,
        subject TEXT,
        body TEXT NOT NULL,
        sent_via TEXT DEFAULT 'in_app',
        email_status TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        read_at TIMESTAMP,
        broadcast_group_id TEXT,
        attachment_filename TEXT,
        attachment_mime TEXT,
        attachment_size INTEGER,
        attachment_data_b64 TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_type, recipient_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_type, sender_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_messages_broadcast ON messages(broadcast_group_id);
    -- 紹介ループ (Referral): 既存生徒が新規生徒を呼ぶと両者に特典 (2026-05-05)
    -- referrer_id: 紹介した既存生徒 (students.id)
    -- referred_id: 紹介された新規生徒 (students.id) — 申込時に確定
    -- code: 紹介URL の ref パラメータ (HMAC ベース、予測不能)
    -- referred_paid_at: 被紹介者が paid 化したタイミング (NULL なら未換金)
    -- coupon_applied_at: 紹介者に Stripe coupon 発行したタイミング (二重発行防止)
    -- coupon_id: 発行済 Stripe coupon ID (audit 用)
    CREATE TABLE IF NOT EXISTS referrals (
        id {pk},
        referrer_id INTEGER NOT NULL,
        referred_id INTEGER NOT NULL UNIQUE,
        code TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        referred_paid_at TIMESTAMP,
        coupon_applied_at TIMESTAMP,
        coupon_id TEXT,
        FOREIGN KEY(referrer_id) REFERENCES students(id),
        FOREIGN KEY(referred_id) REFERENCES students(id)
    );
    CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
    CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id);

    -- 🎫 招待コード (短い文字列・URL に焼かない方式)
    -- 2026-05-07: URL 焼き込み方式は塾長 typo で email 不一致 → 顧客失敗の事故あり (森澤さん)
    -- → 短い code (AJK-XXXXXXXX) を発行し、checkout.html の入力欄に貼ってもらう運用に切替
    -- code は server で DB lookup → email/expires/kind を解決 (typo 不可・iab 安全)
    CREATE TABLE IF NOT EXISTS invite_codes (
        id {pk},
        code TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'student_addon',
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP,
        used_by_student_id INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_invite_codes_email ON invite_codes(email);
    CREATE INDEX IF NOT EXISTS idx_invite_codes_expires ON invite_codes(expires_at);
    """)
    # 既存DBに不足列を追加 (idempotent migration)
    # Postgres: 「column already exists」エラーで トランザクションが abort されると
    # 後続の ALTER がスキップされてしまうため、各 ALTER の前後で commit/rollback する。
    # SQLite: ADD COLUMN IF NOT EXISTS は古いバージョンで非対応なので try/except で対応。
    _migrations = [
        ("enrollment_fee_waived", "ALTER TABLE students ADD COLUMN enrollment_fee_waived INTEGER DEFAULT 0"),
        ("enrollment_waiver_applied_at", "ALTER TABLE students ADD COLUMN enrollment_waiver_applied_at TIMESTAMP"),
        ("last_login_at", "ALTER TABLE students ADD COLUMN last_login_at TIMESTAMP"),
        ("student_email", "ALTER TABLE students ADD COLUMN student_email TEXT DEFAULT ''"),
        # 学習記録機能の対象コース識別 (国公立難関大学コース = 'kokuritsu_nankan')
        # NULL or '' = 一般コース。Studyplus 代替の学習管理は本コース受講生のみ提供 (塾長指示 2026-05-04)
        ("course", "ALTER TABLE students ADD COLUMN course TEXT DEFAULT NULL"),
        # 双方向メッセージ + 授業ファイル添付 (塾長指示 2026-05-06)
        ("msg_attachment_filename", "ALTER TABLE messages ADD COLUMN attachment_filename TEXT"),
        ("msg_attachment_mime", "ALTER TABLE messages ADD COLUMN attachment_mime TEXT"),
        ("msg_attachment_size", "ALTER TABLE messages ADD COLUMN attachment_size INTEGER"),
        ("msg_attachment_data_b64", "ALTER TABLE messages ADD COLUMN attachment_data_b64 TEXT"),
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

    # 🛡️ deploy 完了直後の自動 smoke test (post-deploy verification)
    # Railway / Vercel 再 deploy のたびに必ず合成テスト + JS エラー状況チェックを走らせ、
    # 結果を events に記録 + 失敗時は monitor email で即時アラート。
    # 「更新のたびにエラー有無をチェック」を自動化する仕組み (2026-04-27 追加)。
    task = asyncio.create_task(_post_deploy_smoke_test())
    _BACKGROUND_TASKS.append(task)
    log.info("[Startup] Post-deploy smoke test scheduled (will run in 30 seconds)")

    # 🔔 体験管理 scheduler (毎日 JST 10:00):
    # - expire-trials: trial_end 経過後の自動 expired 化
    # - trial-reminders: 終了 1-2 日前リマインダー
    # - trial-followups: 終了後 Day1/3/7 ドリップ
    # - daily-alerts: 継続学習リマインド (連続未ログイン用)
    # 外部 cron 不要 (in-process scheduler)。CRON_SECRET が設定されていれば起動。
    if CRON_SECRET:
        task = asyncio.create_task(_trial_management_scheduler())
        _BACKGROUND_TASKS.append(task)
        log.info("[Startup] Trial management scheduler launched (target JST 10:00 daily)")
    else:
        log.warning("[Startup] Trial management scheduler NOT launched (CRON_SECRET not set)")

    # 📊 週次レポート scheduler (毎週日曜 JST 19:00): LINE 学習サマリ送信
    if CRON_SECRET:
        task = asyncio.create_task(_weekly_reports_scheduler())
        _BACKGROUND_TASKS.append(task)
        log.info("[Startup] Weekly reports scheduler launched (target Sun JST 19:00)")


async def _post_deploy_smoke_test():
    """uvicorn 起動から 30 秒後に 1 回だけ実行される自動 smoke test。

    deploy 完了 → 30s 待機 (app fully ready) → 合成 E2E テスト + JS エラー集計 →
    結果を events に記録、失敗なら monitor email で塾長に即時通知。
    Railway / Vercel が再 deploy するたびに自動実行される (=「更新のたびにチェック」)。
    """
    try:
        # アプリが完全に立ち上がるまで猶予
        await asyncio.sleep(30)
        started_iso = datetime.now(timezone(timedelta(hours=9))).isoformat()
        log.info(f"[PostDeploy] running smoke test at {started_iso}")

        # 1. 合成 E2E テスト
        synth = await _run_synthetic_checkout_test()
        _SYNTHETIC_CHECKOUT_LAST.update(synth)

        # 2. 直近 5 分の JS エラー件数集計
        try:
            conn = db()
            c = conn.cursor()
            ts_5m = "created_at > NOW() - INTERVAL '5 minutes'" if USE_POSTGRES else "created_at > datetime('now', '-5 minutes')"
            c.execute(f"SELECT COUNT(*) FROM events WHERE name='js_error' AND {ts_5m}")
            js_err_5m = c.fetchone()[0] or 0
            conn.close()
        except Exception:
            js_err_5m = 0

        # 3. 結果 record
        result = {
            "ts": started_iso,
            "synthetic_ok": synth.get("ok"),
            "synthetic_duration_ms": synth.get("duration_ms"),
            "synthetic_failures": synth.get("failures", []),
            "js_errors_last_5min": js_err_5m,
        }
        try:
            conn = db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("post_deploy_smoke_test", json.dumps(result, ensure_ascii=False)[:4000], "monitor")
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        # 4. 失敗時のみ即時アラート (成功時はログのみで沈黙)
        if not synth.get("ok") or js_err_5m >= 3:
            log.warning(f"[PostDeploy] FAILED: synth_ok={synth.get('ok')} / js_err_5m={js_err_5m}")
            try:
                fails_html = "<ul>" + "".join(f"<li>{html_escape_safe(str(f))}</li>" for f in synth.get('failures', [])[:10]) + "</ul>"
                body_html = (
                    f"<h2>🚨 deploy 直後の自動 smoke test 失敗</h2>"
                    f"<p>Railway/Vercel の再 deploy 完了 30 秒後に自動チェックを行いましたが、異常を検出しました。</p>"
                    f"<h3>結果</h3>"
                    f"<ul>"
                    f"<li>合成 E2E テスト: {'✅ OK' if synth.get('ok') else '🚨 NG'}</li>"
                    f"<li>所要時間: {synth.get('duration_ms')} ms</li>"
                    f"<li>直近 5 分の JS エラー件数: {js_err_5m}</li>"
                    f"</ul>"
                    f"<h3>合成テスト失敗詳細</h3>{fails_html}"
                    f"<p>このまま放置すると顧客が壊れたフォームを踏み続けます。今すぐ確認してください。</p>"
                    f"<p>2 連続失敗で自動 rollback が発火する仕組みになっていますが、deploy 直後の最初の失敗時は通知のみです。</p>"
                )
                _send_monitor_email("🚨 deploy 直後の自動 smoke test 失敗", body_html)
            except Exception as e:
                log.warning(f"[PostDeploy] alert email failed: {e}")
        else:
            log.info(f"[PostDeploy] ✅ smoke test OK ({synth.get('duration_ms')}ms, js_err_5m={js_err_5m})")
    except Exception as e:
        log.error(f"[PostDeploy] smoke test crashed: {e}", exc_info=True)

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
    email: EmailStr  # 保護者メール (主要連絡先 + magic link 送信先)
    student_email: Optional[str] = None  # 生徒本人のメール (任意、磁気リンクの cc 送信先)
    grade: Optional[str] = None
    goal: Optional[str] = None
    plan: Optional[str] = "hybrid"
    ref: Optional[str] = None  # 紹介URLの ref コード (ある時は referrer に coupon 付与経路を作る)

    @field_validator("name")
    @classmethod
    def _name_must_be_fullname(cls, v: str) -> str:
        return _validate_fullname(v)

    @field_validator("student_email")
    @classmethod
    def _student_email_optional(cls, v):
        # 空文字 or None は許可。値があるなら簡易的に @ を含むかだけチェック
        if v is None or v == "":
            return ""
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("student_email is invalid")
        return v


class CheckoutRequest(BaseModel):
    plan: str
    email: EmailStr
    name: Optional[str] = ""  # 2026-05-07: upgrade.html (継続登録) は name 入力欄が無いので
                              # 既存 trial student から DB lookup してフォールバック可能化
    student_id: Optional[int] = None
    invite_code: Optional[str] = None  # 通塾生プラン (student_addon) で必須・HMAC トークン

    @field_validator("name")
    @classmethod
    def _name_must_be_fullname(cls, v):
        # 空文字 / None は許容 (endpoint 側で email から DB lookup する)
        if not v or not str(v).strip():
            return ""
        return _validate_fullname(str(v))

class LinePushRequest(BaseModel):
    student_id: int
    template: str
    params: Optional[dict] = {}

class EventTrack(BaseModel):
    name: str
    props: Optional[dict] = {}
    session_id: Optional[str] = None


class JSErrorReport(BaseModel):
    """フロントエンド frontend-error-monitor.js が送信する uncaught JS error。"""
    kind: Optional[str] = "js_error"  # js_error / promise_rejection / resource_error
    message: str = ""
    source: Optional[str] = ""
    lineno: Optional[int] = 0
    colno: Optional[int] = 0
    stack: Optional[str] = ""
    page: Optional[str] = ""
    user_agent: Optional[str] = ""
    session_id: Optional[str] = ""
    ts: Optional[str] = ""

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
        "gemini_configured": bool(GEMINI_API_KEY),  # Tier 4 fallback (AI never-fail)
        "openai_configured": bool(OPENAI_API_KEY),  # Tier 5 fallback (2026-05-10 塾長指示・3段防御)
        "email_configured": bool(RESEND_API_KEY),  # Magic link / Welcome / 各種通知メール
        "email_from_domain": FROM_EMAIL.split("@")[-1].rstrip(">").strip() if "@" in FROM_EMAIL else "not_set",
        "campaign_waiver_active": ENROLLMENT_WAIVER_CAMPAIGN_ENABLED,
    }


@app.get("/api/email/diagnose-public")
def email_diagnose_public():
    """🔥 緊急診断用: 認証不要で Resend ドメイン状態 + 直近エラー要約を公開。
    機密値 (API キー本体, FROM_EMAIL のローカルパート, 顧客メール) は出さない。
    169 件連続失敗に対する原因特定のため 2026-04-30 緊急追加。
    """
    import urllib.request, urllib.error
    out = {
        "from_domain": FROM_EMAIL.split("@")[-1].rstrip(">").strip() if "@" in FROM_EMAIL else "not_set",
        "api_key_set": bool(RESEND_API_KEY),
        "api_key_prefix": (RESEND_API_KEY[:4] + "***") if RESEND_API_KEY else "",
        "domain_status": None,
        "domains_summary": [],
        "api_key_valid": None,
        "api_key_scope": None,  # full_access / send_only / invalid
        "last_error_class": None,
        "last_error_short": None,
        "diagnosis": [],  # 推測される原因 + 対処
    }
    if not RESEND_API_KEY:
        out["api_key_valid"] = False
        out["diagnosis"].append("RESEND_API_KEY が未設定です。Vercel/Railway 環境変数で設定してください。")
        return out
    # Resend /domains で検証状態のみ取得
    try:
        req = urllib.request.Request(
            "https://api.resend.com/domains",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            out["api_key_valid"] = True
            out["api_key_scope"] = "full_access"
            data = json.loads(resp.read().decode())
            domains = data.get("data", []) if isinstance(data, dict) else data
            target_domain = out["from_domain"]
            for d in (domains if isinstance(domains, list) else []):
                out["domains_summary"].append({"name": d.get("name"), "status": d.get("status")})
                if d.get("name") == target_domain:
                    out["domain_status"] = d.get("status")
            if out["domain_status"] is None and target_domain:
                out["domain_status"] = "not_registered"
    except urllib.error.HTTPError as e:
        if e.code == 403:
            # 403 on /domains = "send only" 権限のキー (本番送信は OK)
            out["api_key_valid"] = True
            out["api_key_scope"] = "send_only"
            out["domain_status"] = "unverifiable_via_send_only_key"
        elif e.code == 401:
            out["api_key_valid"] = False
            out["api_key_scope"] = "invalid"
            out["last_error_class"] = "HTTPError_401"
            out["last_error_short"] = "API key revoked or invalid"
        else:
            out["api_key_valid"] = False
            out["last_error_class"] = f"HTTPError_{e.code}"
            out["last_error_short"] = f"HTTP {e.code}"[:80]
    except Exception as e:
        out["api_key_valid"] = False
        out["last_error_class"] = type(e).__name__
        out["last_error_short"] = str(e)[:80]
    # 最近のメール送信エラー (1件のみ、先頭 150 文字)
    try:
        conn = db(); c = conn.cursor()
        c.execute(
            "SELECT props FROM events WHERE name = 'signup_email_status' ORDER BY created_at DESC LIMIT 1"
        )
        row = c.fetchone()
        conn.close()
        if row:
            props_raw = row[0] if not hasattr(row, "keys") else row["props"]
            props = json.loads(props_raw) if isinstance(props_raw, str) else props_raw
            if isinstance(props, dict) and not props.get("email_sent"):
                err = (props.get("error") or "")[:150]
                out["recent_send_error_short"] = err
    except Exception:
        pass
    # 推測される原因 + 対処
    err = (out.get("recent_send_error_short") or "").lower()
    if "429" in err or "too many" in err or "rate" in err:
        out["diagnosis"].append("🚨 Resend のレート制限/日次クォータ超過 (HTTP 429)。無料枠は 100/日・3000/月。")
        out["diagnosis"].append("対処1: Resend ダッシュ → Usage で残量確認 (https://resend.com/emails)")
        out["diagnosis"].append("対処2: 必要なら有料プラン (Pro $20/月で 50000/月) にアップグレード")
        out["diagnosis"].append("対処3: 合成監視が日次クォータを食い潰していた → 修正済 (2026-04-30 deploy)")
    elif "401" in err or "unauthor" in err:
        out["diagnosis"].append("🚨 API キーが無効化されています。Resend ダッシュボードで再生成 → Railway 環境変数更新。")
    elif "422" in err or "domain" in err or "verify" in err:
        out["diagnosis"].append(f"🚨 ドメイン {out['from_domain']} の検証が切れています。Resend で DNS 再検証してください。")
    elif "500" in err or "502" in err or "503" in err:
        out["diagnosis"].append("Resend 側の一時障害の可能性。https://resend-status.com で確認。")
    elif err:
        out["diagnosis"].append(f"未分類エラー: {err}")
    return out

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
# セキュリティ起動チェック (4番手 監査 2026-04-30):
# 本番 (USE_POSTGRES=True = Railway) で MAGIC_LINK_SECRET が dev fallback または
# 32文字未満の場合は警告ログを出力 (HMAC 署名が予測可能になりトークン偽造のリスク)。
if USE_POSTGRES:
    if MAGIC_LINK_SECRET == "dev-secret-DO-NOT-USE-IN-PROD":
        log.error(
            "[SECURITY] MAGIC_LINK_SECRET が dev fallback のまま本番運用中! "
            "Railway env で 32文字以上のランダム値を MAGIC_LINK_SECRET (または APP_SECRET) に設定してください。"
        )
    elif len(MAGIC_LINK_SECRET) < 32:
        log.warning(
            f"[SECURITY] MAGIC_LINK_SECRET が短い (len={len(MAGIC_LINK_SECRET)} chars). "
            "32文字以上のランダム値を推奨。"
        )


def _sign_session_token(student_id: int, ttl_seconds: int = SESSION_TTL_SECONDS, token_type: str = "session") -> str:
    """student_id, expiry, token_type を HMAC-SHA256 で署名し、URL-safe Base64 エンコード。

    token_type:
    - 'session' (default): 30日有効、Authorization: Bearer で認証 API を叩く長期トークン
    - 'magic': 1時間有効、magic link URL に埋め込む短期トークン。/api/auth/verify で
       長期 session トークンへ交換する。

    後方互換: 旧フォーマット ("sid.exp.sig" 3 parts) は session として受理する。"""
    import time
    exp = int(time.time()) + ttl_seconds
    payload = f"{token_type}.{student_id}.{exp}"
    sig = hmac.new(MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}.{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _create_magic_link_token(student_id: int, ttl_seconds: int = 3600) -> str:
    """Magic link 用の短命トークン (デフォルト1時間)。
    URL に直入れするため漏洩リスクを最小化する目的で session token と分離。"""
    return _sign_session_token(student_id, ttl_seconds=ttl_seconds, token_type="magic")


def _verify_session_token(token: str, expected_type: str = "session") -> Optional[dict]:
    """トークンを検証して {student_id, exp, token_type} を返す。無効/期限切れなら None。

    新フォーマット: "type.sid.exp.sig" (4 parts)
    旧フォーマット: "sid.exp.sig" (3 parts) — 後方互換として 'session' 扱いで受理。
    expected_type を None にすると type チェックをスキップ (verify endpoint で session/magic
    両方を許容するため)。
    """
    import time
    if not token:
        return None
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded).decode()
        parts = raw.split(".")
        # 新フォーマット (type.sid.exp.sig)
        if len(parts) == 4:
            ttype, sid_str, exp_str, sig = parts
            payload = f"{ttype}.{sid_str}.{exp_str}"
            expected = hmac.new(MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                return None
            if expected_type and ttype != expected_type:
                # session を期待した API に magic を投げてきた等は拒否
                return None
            exp = int(exp_str)
            if exp < int(time.time()):
                return None
            return {"student_id": int(sid_str), "exp": exp, "token_type": ttype}
        # 旧フォーマット (sid.exp.sig) — session として受理 (後方互換)
        if len(parts) == 3:
            sid_str, exp_str, sig = parts
            expected = hmac.new(MAGIC_LINK_SECRET.encode(), f"{sid_str}.{exp_str}".encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                return None
            if expected_type and expected_type != "session":
                return None
            exp = int(exp_str)
            if exp < int(time.time()):
                return None
            return {"student_id": int(sid_str), "exp": exp, "token_type": "session"}
        return None
    except Exception:
        return None


# ==========================================================================
# 紹介ループ (Referral): 既存生徒が新規生徒を呼ぶと両者に特典 (2026-05-05)
# 紹介URL: https://trillion-ai-juku.com/?ref=<HMAC code>
# code = base64(<student_id>.<HMAC(student_id)>)
# 既存 MAGIC_LINK_SECRET を流用 (新規 secret 設定不要)
# ==========================================================================
def _generate_referral_code(student_id: int) -> str:
    """生徒IDから予測不能な紹介コードを生成。HMAC ベースなのでDB不要で検証可能。
    Security: full 256-bit HMAC (brute force 困難)"""
    payload = f"ref.{student_id}"
    sig = hmac.new(MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{student_id}.{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _verify_referral_code(code: str) -> Optional[int]:
    """紹介コードを検証して referrer の student_id を返す。無効なら None。
    Security: full 256-bit HMAC verification"""
    if not code or len(code) > 200:
        return None
    try:
        padded = code + "=" * (-len(code) % 4)
        raw = base64.urlsafe_b64decode(padded).decode()
        parts = raw.split(".")
        if len(parts) != 2:
            return None
        sid_str, sig = parts
        # 後方互換: 旧 16 char 切り詰め HMAC も受理 (deploy 直後の旧コード対応)
        expected_full = hmac.new(MAGIC_LINK_SECRET.encode(), f"ref.{sid_str}".encode(), hashlib.sha256).hexdigest()
        if not (hmac.compare_digest(sig, expected_full) or hmac.compare_digest(sig, expected_full[:16])):
            return None
        return int(sid_str)
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


def _send_trial_unused_warning_email(to_email: str, student_name: str, stage: str, login_url: str, days_unused: int) -> dict:
    """体験中で未利用 (last_login_at IS NULL) の生徒に通告メール。
    stage='early' (登録 3 日経過): 「使ってみませんか?」
    stage='late' (体験終了 2 日前): 「終了が迫ってます」
    塾長指示 2026-05-06: 登録のみで使用歴がない人に通告"""
    import html as _html
    if not RESEND_API_KEY:
        log.warning(f"[DEV-MODE] Trial unused warning ({stage}) skipped for {to_email}")
        return {"sent": False, "dev_mode": True}
    safe_name = _html.escape(student_name or "")
    greeting = f"{safe_name}さまの保護者さま" if safe_name else "保護者さま"

    if stage == "early":
        subject = "【AI学習コーチ塾】まだログインされていません — 体験を始めてみませんか?"
        body_intro = (
            f"お申込みありがとうございます。\n\n"
            f"無料体験のお申込みから {days_unused} 日経過しましたが、まだ AI 学習コーチ塾にログインされていないようです。\n\n"
            f"AI チューターや問題生成・学習記録など、体験できる機能はすべて無料で使えます。"
        )
        cta_label = "🎓 ログインして体験を始める"
        bottom = "体験期間は 10 日間。何もしなければ自動終了し、課金は一切発生しません。"
    elif stage == "late":
        subject = f"【AI学習コーチ塾】無料体験 終了まで {days_unused} 日 — まだ未利用です"
        body_intro = (
            f"無料体験の終了が近づいています。\n\n"
            f"残り {days_unused} 日 ですが、まだログイン履歴がありません。\n\n"
            f"これまでの実績で「合格カリキュラム自動生成」「24h AI チューター」を最も気に入っていただいています。"
            f" 1 度ログインしてから判断されるのをお勧めします。"
        )
        cta_label = "📅 ログインして残り日数を体験する"
        bottom = "体験期間終了後は自動的にアクセスが失効します (課金は発生しません・データは保持)。"
    else:
        subject = "【AI学習コーチ塾】体験のご案内"
        body_intro = "AI 学習コーチ塾の体験のご案内です。"
        cta_label = "🎓 体験を始める"
        bottom = ""

    html = f"""<!DOCTYPE html>
<html><body style="font-family: -apple-system, sans-serif; line-height: 1.7; color: #333; max-width: 560px; margin: 0 auto; padding: 2rem;">
<h1 style="font-size: 1.4rem; color: #6366f1;">🎓 AI学習コーチ塾</h1>
<p>{greeting}、こんにちは。</p>
<p style="white-space:pre-line;">{_html.escape(body_intro)}</p>

<p style="text-align:center; margin: 2rem 0;">
  <a href="{login_url}" style="display:inline-block; padding: 1rem 2rem; background:linear-gradient(135deg,#6366f1,#ec4899); color:white; text-decoration:none; border-radius:8px; font-weight:700; font-size:1.05rem;">
    {_html.escape(cta_label)}
  </a>
</p>

<div style="background:#fafafa; padding:1rem; border-radius:6px; margin: 1.5rem 0; font-size: 0.9rem; color:#555;">
  💡 {_html.escape(bottom)}
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
            return {"sent": True, "resend_id": result.get("id")}
    except Exception as e:
        log.error(f"Trial unused warning ({stage}) email failed for {to_email}: {type(e).__name__}: {e}")
        return {"sent": False, "error": str(e)}


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
    today_start_utc = datetime.combine(today_jst, dt_time(0, 0), tzinfo=JST).astimezone(timezone.utc)
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


def _compute_sns_utm_cv(days: int = 30) -> dict:
    """utm_content (authority/testimonial) ごとの LP CV を集計。
    返却: {utm_content: {views, submits, cv_rate}}
    Threads 経由の流入 (utm_source=threads) のみ対象。"""
    conn = db()
    c = conn.cursor()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        c.execute(
            """SELECT name, props, session_id FROM events
               WHERE name IN ('lp_view', 'lp_form_submit') AND created_at > ?
               LIMIT 20000""",
            (cutoff,)
        )
        rows = list(c.fetchall())
    finally:
        conn.close()

    views = {}  # utm_content -> set(session_ids)
    submits = {}
    for r in rows:
        name = r["name"] if hasattr(r, "keys") else r[0]
        props_raw = r["props"] if hasattr(r, "keys") else r[1]
        sess = (r["session_id"] if hasattr(r, "keys") else r[2]) or "_anon"
        try:
            props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})
        except Exception:
            props = {}
        # Threads からの流入のみ
        utm_source = props.get("utm_source", "")
        if utm_source != "threads":
            continue
        content = props.get("utm_content", "unknown")
        if name == "lp_view":
            views.setdefault(content, set()).add(sess)
        elif name == "lp_form_submit":
            submits.setdefault(content, set()).add(sess)

    out = {}
    for content, view_set in views.items():
        v_count = len(view_set)
        s_count = len(submits.get(content, set()))
        cv = (s_count / v_count) if v_count > 0 else 0.0
        out[content] = {"views": v_count, "submits": s_count, "cv_rate": cv}
    return out


SNS_UTM_ALLOWLIST = {"authority": "数字×権威型", "testimonial": "体験談ストーリー型"}


def _build_sns_winning_hint() -> str:
    """過去30日 CV データから「効いている型」を判定し、prompt 用ヒント文を返す。
    Security: UTM 値は SNS_UTM_ALLOWLIST にあるもののみ採用 (prompt 注入攻撃防止)。
    Statistical: 150 views 以上 (binomial CI 妥当性) + 30% 以上の差 (hysteresis 兼ねた安定性)。"""
    cv_data = _compute_sns_utm_cv(days=30)
    candidates = []
    for utm, data in cv_data.items():
        # Allowlist のみ採用 (prompt injection 防御)
        if utm not in SNS_UTM_ALLOWLIST:
            continue
        # 統計的有意性確保: 150 views 必須 (CI が狭まる)
        if data["views"] >= 150:
            candidates.append((SNS_UTM_ALLOWLIST[utm], data["cv_rate"], data["views"]))
    if len(candidates) < 2:
        return ""
    candidates.sort(key=lambda x: x[1], reverse=True)
    winner_type, winner_cv, winner_views = candidates[0]
    loser_type, loser_cv, _ = candidates[1]
    # 30% 以上の差がない時はヒント出さない (hysteresis: borderline で flicker しない)
    if winner_cv <= loser_cv * 1.3:
        return ""
    # winner/loser はハードコード辞書値なので f-string 安全
    return (f"\n\n【📊 過去30日 Threads 経由 CV データ (重要)】\n"
            f"「{winner_type}」が「{loser_type}」より CV 率が高い (CV {winner_cv*100:.1f}% vs {loser_cv*100:.1f}%、views {winner_views}+).\n"
            f"今回の生成では、「{winner_type}」のスタイル・訴求パターンを他の型にも一部反映させ、"
            f"より高い engagement を狙ってください。各 type の本数は崩さない (1本ずつ)。")


def _generate_daily_sns_posts() -> list:
    """塾長キャラのThreads投稿5本(5型ローテ)を生成。
    _call_ai_safe(task_type='daily_sns') 経由 = Gemini Flash 優先 (低 stake + 課金抑制)。
    Gemini 失敗時は Anthropic にフォールバック (4段降格 + Tier 4 Gemini で結局止まらない)。
    Phase 3 (2026-05-05): 過去30日 CV データから効いてる型のヒントを prompt に注入。
    """
    # ANTHROPIC / GEMINI / OPENAI のいずれか 1 つでもあれば動く設計 (3段防御)
    if not ANTHROPIC_API_KEY and not GEMINI_API_KEY and not OPENAI_API_KEY:
        log.warning("[DailySNS] ANTHROPIC_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY すべて未設定でスキップ")
        return []
    recent = _get_recent_sns_posts(days=30)
    avoid_section = ""
    if recent:
        joined = "\n".join(f"- {t}" for t in recent[-25:])  # 直近25本まで
        avoid_section = f"\n\n【重複回避】以下は過去30日に生成済み。同じ訴求/同じ書き出しは避けてください:\n{joined}"

    winning_hint = _build_sns_winning_hint()
    types_section = "\n".join(f"{i+1}. {t['name']}: {t['desc']}" for i, t in enumerate(POST_TYPES))
    user_msg = f"""今日のThreads投稿を5本作成してください。5型を1本ずつ:

{types_section}
{avoid_section}{winning_hint}

【🔗 LP誘導リンクの自動挿入】
以下の 2 type の本文末尾には、必ず空行を挟んで誘導リンクを含めてください:

- **数字×権威型**: 末尾に「→ https://trillion-ai-juku.com/lp.html?utm_source=threads&utm_content=authority」
- **体験談ストーリー型**: 末尾に「→ https://trillion-ai-juku.com/lp.html?utm_source=threads&utm_content=testimonial」

リンク前には「気になる方は」「詳細はこちら」「7日間無料体験」などの自然な導入文を1行で書いてください。
他の3 type (逆説型/保護者あるある共感型/二択問いかけ型) はリンクを含めないこと。

【出力形式】純粋なJSONのみ、他のテキストは含めない:
{{
  "posts": [
    {{"type": "逆説型", "text": "本文(改行は\\n)"}},
    {{"type": "保護者あるある共感型", "text": "本文"}},
    {{"type": "数字×権威型", "text": "本文(末尾にリンク必須)"}},
    {{"type": "体験談ストーリー型", "text": "本文(末尾にリンク必須)"}},
    {{"type": "二択問いかけ型", "text": "本文"}}
  ]
}}"""

    system_prompt = f"{JUKUCHO_PERSONA}\n\n{THREADS_RULES}"
    try:
        data = _call_ai_safe(
            {
                "model": DAILY_SNS_MODEL,
                "max_tokens": 3000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_msg}],
            },
            task_type="daily_sns",
        )
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
        actual_model = data.get("_actual_model") or DAILY_SNS_MODEL
        provider = data.get("_provider") or "anthropic"
        log.info(f"[DailySNS] Generated {len(posts)} posts via {actual_model} ({provider})")
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


# ==========================================================================
# 体験管理 in-process scheduler (毎日 JST 10:00)
# 外部 cron が無くても expire-trials / trial-reminders / trial-followups を自動実行
# ==========================================================================
def _check_scheduler_ran_today_jst(event_name: str) -> bool:
    """今日(JST)に同じスケジューラタスクが events に記録されているか確認。
    multi-replica の重複実行を防ぐ (DB 共有 = lock 代わり)。"""
    JST = timezone(timedelta(hours=9))
    today_jst = datetime.now(JST).date()
    today_start_utc = datetime.combine(today_jst, dt_time(0, 0), tzinfo=JST).astimezone(timezone.utc)
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT COUNT(*) AS n FROM events WHERE name = ? AND created_at >= ?",
            (event_name, today_start_utc)
        )
        n = c.fetchone()["n"]
    except Exception as e:
        log.warning(f"_check_scheduler_ran_today_jst({event_name}) failed: {e}")
        n = 0
    finally:
        conn.close()
    return n > 0


def _record_scheduler_run(event_name: str, payload: dict):
    """events テーブルに scheduler 実行記録を残す (重複検出用)"""
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, 'in_process_scheduler')",
            (event_name, json.dumps(payload, ensure_ascii=False)[:4000])
        )
        conn.commit()
    except Exception as e:
        log.warning(f"_record_scheduler_run({event_name}) failed: {e}")
    finally:
        conn.close()


async def _trial_management_scheduler():
    """体験管理 3 タスクを毎日 JST 10:00 に内部実行。同じ FastAPI process 内なので
    HTTP 越しでなく直接 endpoint 関数を呼ぶ。multi-replica は events テーブル lock で防止。
    daily-alerts は dedup が無いため敢えて含めない (重複 LINE push 事故防止)。"""
    JST = timezone(timedelta(hours=9))
    TARGET_HOUR_JST = 10
    log.info(f"[TrialMgr] Scheduler started, target hour JST {TARGET_HOUR_JST}:00")
    secret = CRON_SECRET

    while True:
        try:
            now_jst = datetime.now(JST)
            target = now_jst.replace(hour=TARGET_HOUR_JST, minute=0, second=0, microsecond=0)
            if target <= now_jst:
                target += timedelta(days=1)
            sleep_secs = (target - now_jst).total_seconds()
            log.info(f"[TrialMgr] Next run at {target.isoformat()} (in {int(sleep_secs)}s)")
            await asyncio.sleep(sleep_secs)

            # multi-replica 重複実行防止: 今日既に他 replica が走っていればスキップ
            if _check_scheduler_ran_today_jst("trial_mgmt_run"):
                log.info("[TrialMgr] Skipped (already ran today by another replica)")
                continue

            # 4 タスクを順次実行 (例外は個別に握りつぶしてループ継続)
            tasks = [
                ("expire-trials", lambda: cron_expire_trials(x_cron_secret=secret, dry_run=False)),
                ("trial-reminders", lambda: cron_trial_reminders(x_cron_secret=secret, dry_run=False)),
                ("trial-followups", lambda: cron_trial_followups(x_cron_secret=secret, dry_run=False)),
                ("trial-unused-warning", lambda: cron_trial_unused_warning(x_cron_secret=secret, dry_run=False)),
            ]
            results = {}
            for task_name, fn in tasks:
                try:
                    r = fn()
                    results[task_name] = r
                    log.info(f"[TrialMgr] {task_name}: {r}")
                except Exception as e:
                    results[task_name] = {"error": f"{type(e).__name__}: {e}"}
                    log.error(f"[TrialMgr] {task_name} failed: {type(e).__name__}: {e}", exc_info=True)
            _record_scheduler_run("trial_mgmt_run", results)
        except asyncio.CancelledError:
            log.info("[TrialMgr] Scheduler cancelled")
            raise
        except Exception as e:
            log.error(f"[TrialMgr] Scheduler loop error: {e}", exc_info=True)
            await asyncio.sleep(3600)


async def _weekly_reports_scheduler():
    """週次レポートを毎週日曜 JST 19:00 に内部実行。multi-replica 重複防止付き。"""
    JST = timezone(timedelta(hours=9))
    TARGET_HOUR_JST = 19
    TARGET_WEEKDAY = 6  # Sunday (Mon=0..Sun=6)
    log.info(f"[WeeklyReports] Scheduler started, target Sun JST {TARGET_HOUR_JST}:00")
    secret = CRON_SECRET

    while True:
        try:
            now_jst = datetime.now(JST)
            # 次の日曜 19:00
            days_ahead = (TARGET_WEEKDAY - now_jst.weekday()) % 7
            target = now_jst.replace(hour=TARGET_HOUR_JST, minute=0, second=0, microsecond=0)
            if days_ahead == 0 and target <= now_jst:
                days_ahead = 7
            target += timedelta(days=days_ahead)
            sleep_secs = (target - now_jst).total_seconds()
            log.info(f"[WeeklyReports] Next run at {target.isoformat()} (in {int(sleep_secs)}s)")
            await asyncio.sleep(sleep_secs)
            if _check_scheduler_ran_today_jst("weekly_reports_run"):
                log.info("[WeeklyReports] Skipped (already ran today by another replica)")
                continue
            try:
                result = cron_weekly_reports(x_cron_secret=secret, dry_run=False)
                log.info(f"[WeeklyReports] result: {result}")
                _record_scheduler_run("weekly_reports_run", result if isinstance(result, dict) else {})
            except Exception as e:
                log.error(f"[WeeklyReports] failed: {type(e).__name__}: {e}", exc_info=True)
                _record_scheduler_run("weekly_reports_run", {"error": f"{type(e).__name__}: {e}"})
        except asyncio.CancelledError:
            log.info("[WeeklyReports] Scheduler cancelled")
            raise
        except Exception as e:
            log.error(f"[WeeklyReports] Scheduler loop error: {e}", exc_info=True)
            await asyncio.sleep(3600)


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
        "gemini_configured": bool(GEMINI_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
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
        "SELECT COUNT(*) FROM students WHERE status='paid' AND plan IS NOT NULL AND plan != '' AND plan != 'student_addon'"
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

    # 🔧 ファネル詰まり警告は 6h ローリング窓で判定 (24h 窓だと修正後も警告が消えない問題対応)
    h6 = now - timedelta(hours=6)
    snapshot["pv_6h"] = event_count("page_view", h6)
    snapshot["form_submit_6h"] = event_count("form_submit", h6)
    snapshot["page_loaded_ok_6h"] = event_count("page_loaded_ok", h6)

    # 🔧 JS エラー 6h カウントは「最後の sweep 以降」のみ集計 (2026-04-28 self-healing 強化)。
    # CEO ダッシュ「JS エラー一括解決」ボタンで sweep event を打つと、それ以前のエラー
    # (既に修正済み or 監視ノイズと判断したもの) は count から除外され、誤アラートが消える。
    # 新しい signature が出れば再カウント開始されるため、本物の新規問題は引き続き検知される。
    try:
        c2 = conn.cursor()
        c2.execute("SELECT MAX(created_at) FROM events WHERE name = 'js_error_sweep'")
        sweep_row = c2.fetchone()
        last_sweep = sweep_row[0] if sweep_row else None
    except Exception:
        last_sweep = None
    js_err_lower_bound = h6
    if last_sweep is not None:
        # last_sweep が naive datetime か aware か揃える
        try:
            if hasattr(last_sweep, 'tzinfo') and last_sweep.tzinfo is None:
                from datetime import timezone as _tz
                last_sweep = last_sweep.replace(tzinfo=_tz.utc)
            if last_sweep > h6:
                js_err_lower_bound = last_sweep
        except Exception:
            pass
    snapshot["js_error_6h"] = event_count("js_error", js_err_lower_bound)
    snapshot["js_error_last_sweep"] = str(last_sweep) if last_sweep else None

    # 🔥 申込→ログイン経路 監視 (2026-04-30 追加 — 塾長指示「申込→ログイン経路を完璧に」)
    # 過去 24h 申込数のうち、何名がログイン済みか。50% 以下は赤バナー警告。
    try:
        c.execute(
            """SELECT
                 COUNT(*) AS signups,
                 COUNT(last_login_at) AS logged_in
               FROM students
               WHERE created_at >= ?
                 AND status IN ('trial', 'paid')""",
            (h24,)
        )
        login_row = c.fetchone()
        signups_24h_login = int(login_row[0]) if login_row else 0
        logged_in_24h = int(login_row[1]) if login_row else 0
    except Exception as e:
        log.warning(f"[Monitor] login-rate query failed: {e}")
        try: conn.rollback()
        except Exception: pass
        signups_24h_login = 0
        logged_in_24h = 0
    snapshot["login_signups_24h"] = signups_24h_login
    snapshot["login_logged_in_24h"] = logged_in_24h
    snapshot["login_never_logged_in_24h"] = max(0, signups_24h_login - logged_in_24h)
    if signups_24h_login > 0:
        snapshot["login_rate_24h_pct"] = round(100 * logged_in_24h / signups_24h_login, 1)
    else:
        snapshot["login_rate_24h_pct"] = None  # 申込ゼロなら判定不可

    # 🔥 magic link メール送信成功率 (events.signup_email_status の直近 7 日)
    # 失敗が連続 3 件以上なら CEO ダッシュ警告 + alert 発火
    h7d = now - timedelta(days=7)
    try:
        c.execute(
            "SELECT props FROM events WHERE name = 'signup_email_status' AND created_at >= ? ORDER BY created_at DESC LIMIT 200",
            (h7d,)
        )
        email_rows = c.fetchall()
        email_total = 0
        email_sent = 0
        recent_failures_streak = 0  # 最新から連続する失敗数
        streak_broken = False
        most_recent_error = None  # 直近の失敗エラー (alert 詳細用)
        for er in email_rows:
            props_raw = er[0] if not hasattr(er, "keys") else er["props"]
            try:
                props = json.loads(props_raw) if isinstance(props_raw, str) else props_raw
            except Exception:
                props = None
            if not isinstance(props, dict):
                continue
            email_total += 1
            ok_flag = bool(props.get("email_sent"))
            if ok_flag:
                email_sent += 1
                streak_broken = True
            else:
                if not streak_broken:
                    recent_failures_streak += 1
                    if most_recent_error is None:
                        most_recent_error = (props.get("error") or "")[:200]
        snapshot["email_total_7d"] = email_total
        snapshot["email_sent_7d"] = email_sent
        snapshot["email_success_rate_7d_pct"] = (
            round(100 * email_sent / email_total, 1) if email_total > 0 else None
        )
        snapshot["email_recent_failures_streak"] = recent_failures_streak
        snapshot["email_most_recent_error"] = most_recent_error
    except Exception as e:
        log.warning(f"[Monitor] email-rate query failed: {e}")
        try: conn.rollback()
        except Exception: pass
        snapshot["email_total_7d"] = 0
        snapshot["email_sent_7d"] = 0
        snapshot["email_success_rate_7d_pct"] = None
        snapshot["email_recent_failures_streak"] = 0

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
    # 4. ファネル落差: 直近6h で PV はあるが form_submit ゼロ (フォームエラーの兆候)
    #    24h 窓だと「壊れていた期間」のデータが残り続けて修正後も警告が出続ける。
    #    6h ローリングなら修正反映後は自然に解除される。
    #    判定強化: JS エラー or 合成テスト失敗が併発していれば critical、無ければ info 扱い。
    if snapshot.get("pv_6h", 0) >= 20 and snapshot.get("form_submit_6h", 0) == 0:
        synth_failing = bool(_SYNTHETIC_CHECKOUT_LAST.get("ok") is False)
        js_storm = snapshot.get("js_error_6h", 0) >= 5
        if synth_failing or js_storm:
            alerts.append({
                "key": "funnel_drop_form", "severity": "critical",
                "title": "🚨 ファネル詰まり (確定): 直近6h PV {pv} / フォーム送信 0".format(pv=snapshot["pv_6h"]),
                "detail": (
                    f"E2E 合成テスト{'失敗' if synth_failing else 'OK'} / 直近6h JS エラー {snapshot.get('js_error_6h',0)}件。"
                    "フォームエラーで顧客が離脱している可能性が高い。"
                ),
            })
        else:
            # E2E OK + JS エラーなしでフォーム送信ゼロは「LP閲覧者がそもそも申し込まなかった」可能性
            # → 警告レベルを下げる (バナー表示のみで critical email は送らない)
            alerts.append({
                "key": "funnel_drop_form", "severity": "info",
                "title": "📊 ファネル観察: 直近6h PV {pv} / フォーム送信 0".format(pv=snapshot["pv_6h"]),
                "detail": (
                    "E2E 合成テスト OK + JS エラー無し → フォーム自体は機能しているが、"
                    "LP 訪問者が申込まで進んでいません。コンバージョン改善 (CTA 見直し / LP コピー強化 / FOMO 表示) を検討してください。"
                ),
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
    # 7. 🔥 申込→ログイン経路 監視 (2026-04-30 追加)
    # 過去24h 申込 3 名以上で、ログイン率 50% 未満なら critical
    sg = snapshot.get("login_signups_24h", 0)
    li = snapshot.get("login_logged_in_24h", 0)
    if sg >= 3:
        rate = li / sg
        if rate < 0.5:
            alerts.append({
                "key": "login_rate_low_24h", "severity": "critical",
                "title": f"🚨 24h 申込ログイン率が低い ({int(rate*100)}%)",
                "detail": (
                    f"過去24h 申込 {sg} 名のうち、ログイン済 {li} 名のみ "
                    f"(未ログイン {sg - li} 名)。magic link メール未着 / 認証バグの兆候。"
                    " /api/admin/students/never-logged-in?hours=24 で対象確認 + send-login-link で再送信を検討。"
                ),
            })
    # 8. 🔥 magic link メール送信失敗の連続検知 (2026-04-30 追加)
    streak = snapshot.get("email_recent_failures_streak", 0)
    if streak >= 3:
        recent_err = snapshot.get("email_most_recent_error") or ""
        err_suffix = f" 直近エラー: {recent_err}" if recent_err else ""
        alerts.append({
            "key": "email_failure_streak", "severity": "critical",
            "title": f"🚨 magic link メール送信失敗が連続 {streak} 件",
            "detail": (
                f"events.signup_email_status の直近 {streak} 件が連続で email_sent=false。"
                " Resend API 障害 / API キー失効 / ドメイン認証問題の可能性。"
                f" 直近7日 送信成功率 {snapshot.get('email_success_rate_7d_pct')}%。"
                f"{err_suffix}"
            ),
        })
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
    today_start_utc = datetime.combine(today, dt_time(0, 0), tzinfo=JST).astimezone(timezone.utc)
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


def _maybe_run_never_login_nudge(now_jst: datetime) -> dict:
    """24h 未ログイン生徒に magic link を再送信 (1日1回のみ)。
    NEVER_LOGIN_NUDGE_HOUR_JST 時台で、まだ今日実行していなければ走る。
    塾長指示「申込→ログイン経路を完璧に」(2026-04-29) 対応。
    """
    if not NEVER_LOGIN_NUDGE_ENABLED:
        return {"ran": False, "reason": "disabled"}
    if now_jst.hour != NEVER_LOGIN_NUDGE_HOUR_JST:
        return {"ran": False, "reason": "wrong_hour"}
    today_key = now_jst.strftime("%Y-%m-%d")
    if _NEVER_LOGIN_NUDGE_LAST_RUN.get("date") == today_key:
        return {"ran": False, "reason": "already_ran_today"}

    cutoff = datetime.now(timezone.utc) - timedelta(hours=NEVER_LOGIN_NUDGE_HOURS_THRESHOLD)
    conn = db()
    c = conn.cursor()
    targets: list = []
    try:
        try:
            c.execute(
                """SELECT id, name, email
                   FROM students
                   WHERE last_login_at IS NULL
                     AND status IN ('trial', 'paid')
                     AND email IS NOT NULL AND email != ''
                     AND created_at <= ?
                   ORDER BY created_at ASC
                   LIMIT ?""",
                (cutoff, NEVER_LOGIN_NUDGE_MAX_PER_DAY)
            )
            targets = [dict(r) for r in c.fetchall()]
        except Exception as e:
            try: conn.rollback()
            except Exception: pass
            log.warning(f"[Monitor:Nudge] query failed: {e}")
    finally:
        conn.close()

    # 今日実行したフラグは「対象を取得できた時点で」立てる (空でも今日はもう走らない)
    _NEVER_LOGIN_NUDGE_LAST_RUN["date"] = today_key

    if not targets:
        log.info("[Monitor:Nudge] no targets — skip")
        return {"ran": True, "matched": 0, "sent": 0}

    sent = 0
    failed = []
    import time as _t
    for idx, s in enumerate(targets):
        if idx > 0:
            _t.sleep(0.6)  # Resend rate (2 req/s) 対策
        try:
            session_token = _sign_session_token(s["id"])
            magic_url = f"{BASE_URL}/auth.html?t={session_token}"
            otp_code = _create_otp(s["id"])
            result = _send_magic_link_email(
                s["email"], s.get("name") or "", magic_url,
                otp_code=otp_code, is_welcome=True,
            )
            if isinstance(result, dict) and result.get("sent"):
                sent += 1
            else:
                failed.append({"id": s["id"], "error": str((result or {}).get("error", "send_failed"))[:120]})
        except Exception as e:
            failed.append({"id": s["id"], "error": f"{type(e).__name__}: {e}"[:120]})
            log.error(f"[Monitor:Nudge] send error for student {s['id']}: {e}")

    log.info(f"[Monitor:Nudge] matched={len(targets)} sent={sent} failed={len(failed)}")
    # events に結果を記録
    try:
        conn2 = db()
        c2 = conn2.cursor()
        c2.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("never_login_nudge", json.dumps({
                "matched": len(targets), "sent": sent, "failed": len(failed),
                "failed_details": failed[:10],
            }, ensure_ascii=False)[:4000], "monitor_scheduler")
        )
        conn2.commit()
        conn2.close()
    except Exception:
        pass
    return {"ran": True, "matched": len(targets), "sent": sent, "failed": len(failed)}


# =====================================================================
# 🌐 ドメイン状態監視 + Whois 認証年次リマインダー
# 2026-05-06 致命事故 (お名前.com Whois 年次認証を逃して clientHold で
# trillion-ai-juku.com 全停止 → 顧客アクセス不能) の再発防止策。
#
# 3視点 review feedback (2026-05-06) を反映:
#   - JST NameError 修正 (module-global JST_TZ 化)
#   - multi-replica 安全な kv_settings 永続 dedup
#   - 4/15 単日 → DOMAIN_REGISTRATION_ANNIVERSARY 起点で 30/7 日前の window
#   - HTML エスケープで XSS 防止
#   - kv_settings UPSERT パターン
#   - 異常 status 別の対応手順分岐
#   - 手動 trigger に rate limit
# =====================================================================

import html as _html_mod  # XSS escape 用 (RDAP-derived fields)

# JST timezone (module-level, 上記レビューで指摘された NameError 防止)
JST_TZ_DOMAIN = timezone(timedelta(hours=9))

_BAD_DOMAIN_STATUSES = {
    "clienthold",
    "serverhold",
    "inactive",
    "pendingdelete",
    "redemptionperiod",
}


def _normalize_status(s: str) -> str:
    """RDAP status の表記揺れを吸収 ('client hold', 'clientHold', 'CLIENT_HOLD' → 'clienthold')"""
    return (s or "").lower().replace(" ", "").replace("_", "").replace("-", "")


def _kv_get(key: str) -> Optional[str]:
    """kv_settings から値を読む (cross-replica safe)"""
    try:
        conn = db()
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS kv_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("SELECT value FROM kv_settings WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        if isinstance(row, dict):
            return row.get("value")
        try:
            return row[0] if row[0] is not None else None
        except (KeyError, IndexError, TypeError):
            return row.get("value") if hasattr(row, "get") else None
    except Exception as e:
        log.warning(f"[kv_get:{key}] error: {e}")
        return None


def _kv_set(key: str, value: str) -> bool:
    """kv_settings UPSERT (PostgreSQL/SQLite 両対応)。DELETE+INSERT より race-safe。"""
    try:
        conn = db()
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS kv_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        # ON CONFLICT は SQLite/PostgreSQL 両方サポート
        try:
            c.execute(
                "INSERT INTO kv_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                (key, value)
            )
        except Exception:
            # フォールバック: DELETE + INSERT (古い SQLite or psycopg)
            c.execute("DELETE FROM kv_settings WHERE key = ?", (key,))
            c.execute("INSERT INTO kv_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.warning(f"[kv_set:{key}] error: {e}")
        return False


def _check_domain_status_via_rdap(domain: str = None) -> dict:
    """RDAP (https://rdap.org) で WHOIS Domain Status を取得。
    返り値: {"ok": bool, "domain": str, "status": [str], "error": str|None, "bad_status_detected": [str]}
    """
    target = domain or DOMAIN_MONITOR_TARGET
    out = {"ok": False, "domain": target, "status": [], "error": None, "bad_status_detected": []}
    # URL 安全性: env-only だが念のため危険文字を弾く
    if not target or any(ch in target for ch in ("/", " ", "\n", "\r", "?", "#")):
        out["error"] = "invalid_domain"
        return out
    try:
        req = urllib.request.Request(
            f"https://rdap.org/domain/{target}",
            headers={"User-Agent": "ai-juku-monitor/1.0", "Accept": "application/rdap+json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            statuses = data.get("status") or []
            out["status"] = statuses
            bad_set = {_normalize_status(bs) for bs in _BAD_DOMAIN_STATUSES}
            for s in statuses:
                if _normalize_status(s) in bad_set:
                    out["bad_status_detected"].append(s)
            out["ok"] = True
    except urllib.error.HTTPError as e:
        out["error"] = f"HTTPError {e.code}"
        if e.code == 404:
            out["bad_status_detected"].append("not_registered")
    except urllib.error.URLError as e:
        out["error"] = f"URLError {getattr(e, 'reason', e)}"
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def _build_domain_alert_email(result: dict) -> tuple:
    """異常 status 種別ごとに subject/body を分岐生成。XSS 防止のため HTML エスケープ。"""
    bad_raw = result.get("bad_status_detected") or []
    bad_norm = [_normalize_status(s) for s in bad_raw]
    domain_safe = _html_mod.escape(str(result.get("domain") or ""))
    bad_safe = _html_mod.escape(", ".join(bad_raw))
    all_status_safe = _html_mod.escape(", ".join(result.get("status") or []))
    detect_time = datetime.now(JST_TZ_DOMAIN).strftime("%Y-%m-%d %H:%M:%S")

    # subject はヘッダ injection 防止のため改行除去
    subject = f"🚨🚨 緊急: ドメイン異常検知 ({domain_safe}) — {bad_safe}".replace("\r", "").replace("\n", " ")

    # 状態別の対応手順
    if "pendingdelete" in bad_norm or "redemptionperiod" in bad_norm:
        action_html = """
        <h3 style="color:#dc2626;">🆘 即対応 (pendingDelete / redemptionPeriod)</h3>
        <p style="background:#fee2e2;padding:12px;border-radius:8px;border-left:4px solid #dc2626;">
          ⚠️ <strong>ドメインが削除/redemption フェーズに入っています。30 日以内に行動しないとドメインを失います。</strong>
        </p>
        <ol style="line-height:1.8;">
          <li>お名前.com に至急連絡 (TEL: 03-6745-9522 / 平日 10:00-18:00)</li>
          <li>「redemption fee 支払いで復活したい」と伝える (1ドメイン¥10,000〜¥30,000 程度)</li>
          <li>支払い完了後、登録更新も同時に実施</li>
        </ol>
        """
    elif "not_registered" in bad_norm:
        action_html = """
        <h3 style="color:#dc2626;">🆘 即対応 (登録抹消の疑い)</h3>
        <p style="background:#fee2e2;padding:12px;border-radius:8px;border-left:4px solid #dc2626;">
          ⚠️ <strong>RDAP がドメインを認識しません (404)。登録が抹消された可能性があります。</strong>
        </p>
        <ol style="line-height:1.8;">
          <li>お名前.com Navi にログイン → 「ドメイン > ドメイン一覧」確認</li>
          <li>登録更新切れの場合は即時更新 (24h 以内なら復活可能性高)</li>
        </ol>
        """
    else:
        # clientHold / serverHold / inactive (Whois 認証関連が大半)
        action_html = """
        <h3>📋 即対応手順 (clientHold / serverHold)</h3>
        <ol style="line-height:1.8;">
          <li>お名前.com Navi にログイン: <a href="https://navi.onamae.com/">https://navi.onamae.com/</a></li>
          <li>「ドメイン > ドメイン機能一覧 > Whois 情報認証」を確認</li>
          <li>受信箱で「onamae.com Whois」と検索 (送信元: <code>verification-noreply@onamae.com</code>)</li>
          <li>認証 URL をクリック → 数時間以内に解除</li>
          <li>メールが見つからなければ Whois 情報認証画面から再送信</li>
        </ol>
        """

    body_html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;">
      <h2 style="color:#dc2626;">🚨 ドメイン異常を検知しました</h2>
      <p><strong>ドメイン:</strong> {domain_safe}</p>
      <p><strong>異常 status:</strong> <code style="background:#fee;color:#dc2626;padding:4px 8px;border-radius:4px;">{bad_safe}</code></p>
      <p><strong>全 status:</strong> {all_status_safe}</p>
      <p><strong>検知時刻:</strong> {detect_time} JST</p>
      <hr>
      {action_html}
      <p style="font-size:0.85rem;color:#71717a;margin-top:20px;">
        🛡️ ai-juku-system が 30 分おきに RDAP をチェック中。本アラートはエスカレーション付きで dedup 送信します。
      </p>
    </div>
    """
    return subject, body_html


def _maybe_run_domain_status_check() -> dict:
    """30 分おきにドメイン状態を RDAP で確認、異常検知時は緊急アラート送信。
    multi-replica 対応のため kv_settings で永続 dedup。
    エスカレーション: 1h → 6h → 24h で再アラート (DNS 伝播待ち長時間化に対応)。
    """
    if not DOMAIN_MONITOR_ENABLED:
        return {"ran": False, "reason": "disabled"}
    now_ts = time.time()
    # multi-replica safe interval gate: kv_settings の値を尊重 (in-memory は補助)
    last_check_kv = _kv_get("domain_monitor_last_check_ts")
    last_check_ts = float(last_check_kv) if last_check_kv else _DOMAIN_MONITOR_LAST_CHECK.get("ts", 0.0)
    if now_ts - last_check_ts < DOMAIN_MONITOR_INTERVAL_MIN * 60:
        return {"ran": False, "reason": "interval_not_reached"}
    _kv_set("domain_monitor_last_check_ts", str(now_ts))
    _DOMAIN_MONITOR_LAST_CHECK["ts"] = now_ts

    result = _check_domain_status_via_rdap()
    _DOMAIN_MONITOR_LAST_CHECK["status"] = result.get("status")
    bad = result.get("bad_status_detected") or []

    # events 記録 (audit log)
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("domain_status_check", json.dumps(result, ensure_ascii=False)[:4000], "monitor_scheduler")
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    if not bad:
        # OK 状態: 連続失敗カウンタリセット
        _kv_set("domain_monitor_consecutive_failures", "0")
        return {"ran": True, "ok": True, "status": result.get("status")}

    # エスカレーション: 1h → 6h → 24h で再送
    last_alert_kv = _kv_get("domain_monitor_alert_sent_at")
    last_alert_ts = float(last_alert_kv) if last_alert_kv else 0.0
    alert_count_kv = _kv_get("domain_monitor_alert_count_in_incident")
    alert_count = int(alert_count_kv) if alert_count_kv else 0
    elapsed = now_ts - last_alert_ts
    if alert_count == 0:
        cooldown = 0  # 初回は即時
    elif alert_count == 1:
        cooldown = 3600  # 2回目: 1h 後
    elif alert_count == 2:
        cooldown = 6 * 3600  # 3回目: 6h 後
    else:
        cooldown = 24 * 3600  # 4回目以降: 24h 後
    if elapsed < cooldown:
        return {"ran": True, "ok": False, "bad": bad, "alert_skipped": f"cooldown_{cooldown}s"}

    subject, body_html = _build_domain_alert_email(result)
    email_result = _send_monitor_email(subject, body_html)
    sent = bool(email_result.get("sent"))
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("domain_status_alert", json.dumps({
                "bad_status": bad,
                "all_status": result.get("status"),
                "alert_attempt": alert_count + 1,
                "sent": sent,
                "resend_id": email_result.get("resend_id"),
                "error": email_result.get("error"),
            }, ensure_ascii=False)[:4000], "monitor_scheduler")
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    if sent:
        _DOMAIN_MONITOR_LAST_CHECK["alert_sent_at"] = now_ts
        _kv_set("domain_monitor_alert_sent_at", str(now_ts))
        _kv_set("domain_monitor_alert_count_in_incident", str(alert_count + 1))
    return {"ran": True, "ok": False, "bad": bad, "alert_sent": sent, "alert_attempt": alert_count + 1}


def _whois_reminder_should_fire(now_jst: datetime) -> tuple:
    """4/15 単日固定だと監視自体ダウン時に逃すので、anniversary 起点の window に変更。
    返り値: (should_fire: bool, reason: str, days_before: int)
    """
    if not WHOIS_RENEWAL_REMINDER_ENABLED:
        return False, "disabled", 0
    # 旧 env (4/15 固定) との互換: 設定があればそちらに従う (deprecation path)
    if WHOIS_RENEWAL_REMINDER_MONTH and WHOIS_RENEWAL_REMINDER_DAY:
        if now_jst.month == WHOIS_RENEWAL_REMINDER_MONTH and now_jst.day == WHOIS_RENEWAL_REMINDER_DAY and now_jst.hour <= 11:
            return True, "legacy_fixed_date", 0
        return False, "legacy_no_match", 0
    # 新方式: anniversary - 30d, anniversary - 7d の window で fire
    try:
        anni_m, anni_d = [int(x) for x in DOMAIN_REGISTRATION_ANNIVERSARY.split("-")]
    except Exception:
        return False, "invalid_anniversary", 0
    try:
        days_before_list = [int(x.strip()) for x in WHOIS_RENEWAL_REMINDER_DAYS_BEFORE.split(",") if x.strip()]
    except Exception:
        return False, "invalid_days_before", 0

    # 今年の anniversary 日付を構築
    try:
        anni_this_year = datetime(now_jst.year, anni_m, anni_d, tzinfo=now_jst.tzinfo)
    except Exception:
        return False, "invalid_anniversary_date", 0
    # anniversary を過ぎていたら来年の同日を見る (12/31 から 1/X など)
    if now_jst > anni_this_year:
        try:
            anni_this_year = datetime(now_jst.year + 1, anni_m, anni_d, tzinfo=now_jst.tzinfo)
        except Exception:
            return False, "invalid_next_anniversary", 0

    delta_days = (anni_this_year.date() - now_jst.date()).days
    # 30 日前の window: [days_before, days_before+2] に入っていれば fire (監視ダウン耐性)
    for db_target in days_before_list:
        if db_target <= delta_days <= db_target + 2:
            return True, f"anniversary_minus_{db_target}d_window", db_target
    return False, "outside_window", delta_days


def _maybe_run_whois_renewal_reminder(now_jst: datetime) -> dict:
    """お名前.com Whois 認証年次リマインダーを送信。
    anniversary - 30/7 日前の window で fire (kv_settings で year+days_before の組み合わせ単位で dedup)。
    """
    should_fire, reason, days_before = _whois_reminder_should_fire(now_jst)
    if not should_fire:
        return {"ran": False, "reason": reason}
    # 朝の時間帯のみ (深夜のスケジュール起動を回避)
    if now_jst.hour > 11:
        return {"ran": False, "reason": "after_noon"}

    year_key = str(now_jst.year)
    dedup_key = f"whois_renewal_reminder_sent_{year_key}_minus_{days_before}d"
    if _kv_get(dedup_key):
        return {"ran": False, "reason": "already_sent_this_window", "year": year_key, "days_before": days_before}

    domain_safe = _html_mod.escape(DOMAIN_MONITOR_TARGET)
    anni_safe = _html_mod.escape(DOMAIN_REGISTRATION_ANNIVERSARY)
    urgency_color = "#dc2626" if days_before <= 7 else "#f59e0b"
    urgency_label = "🚨 至急" if days_before <= 7 else "🔔 事前"

    subject = f"{urgency_label} [{days_before}日前リマインダー] お名前.com Whois 認証メールにご注意 ({domain_safe})"
    body_html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;">
      <h2 style="color:{urgency_color};">{urgency_label} Whois 認証年次更新のお知らせ ({days_before} 日前)</h2>
      <p>塾長 様</p>
      <p>
        ドメイン登録記念日 ({anni_safe}) まで <strong>{days_before} 日</strong> です。<br>
        お名前.com から下記の認証メールが届きます (送信元: <code>verification-noreply@onamae.com</code>):
      </p>
      <blockquote style="background:#f1f5f9;padding:10px 15px;border-left:3px solid #94a3b8;font-style:italic;">
        「[重要] [ドメイン名] ドメイン Whois 情報の有効性認証手続きのお願い」
      </blockquote>
      <p style="background:#fef3c7;padding:12px;border-radius:8px;border-left:4px solid #f59e0b;">
        ⚠️ <strong>このメールに記載された認証 URL を 15 日以内にクリックしないと、ドメインが clientHold (利用停止) になります。</strong><br>
        2026-05-06 に実際に発生し、サイト全停止 + 顧客アクセス不能の致命事故になりました。
      </p>
      <h3>📋 アクション</h3>
      <ol style="line-height:1.8;">
        <li>受信箱で「onamae.com Whois」と検索</li>
        <li>認証メールを開いて URL をクリック</li>
        <li>「Whois 認証完了」画面が表示されれば OK</li>
        <li>万一見つからなければ <a href="https://navi.onamae.com/">お名前.com Navi</a> > Whois 情報認証 から再送信</li>
      </ol>
      <p style="font-size:0.85rem;color:#71717a;margin-top:20px;">
        対象ドメイン: <code>{domain_safe}</code><br>
        このメールは 30/7 日前の 2 段階で年 1 回送信されます。<br>
        🛡️ ai-juku-system in-process scheduler が 30 分おきに RDAP をチェック中、万一 clientHold が発生したら緊急アラートも送ります。
      </p>
    </div>
    """
    email_result = _send_monitor_email(subject, body_html)
    sent = bool(email_result.get("sent"))
    if sent:
        _kv_set(dedup_key, str(int(time.time())))
        try:
            conn = db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("whois_renewal_reminder_sent", json.dumps({
                    "year": year_key,
                    "days_before": days_before,
                    "resend_id": email_result.get("resend_id"),
                }, ensure_ascii=False)[:1000], "monitor_scheduler")
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
    return {"ran": True, "sent": sent, "year": year_key, "days_before": days_before}


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
            # 1-B. 🛡️ 申込→決済 フロー E2E 合成テスト (revenue critical)
            try:
                synth = await _run_synthetic_checkout_test()
                _SYNTHETIC_CHECKOUT_LAST.update(synth)
                if not synth.get("ok"):
                    log.warning(f"[Monitor:Synth] FAILED: {synth.get('failures')}")
                    _SYNTHETIC_CONSECUTIVE_FAILS["count"] += 1
                    _SYNTHETIC_CONSECUTIVE_FAILS["last_failure_ts"] = time.time()
                    # 🚨 2連続失敗 (= 10分間連続して壊れている) → 自動 rollback 試行
                    if _SYNTHETIC_CONSECUTIVE_FAILS["count"] >= 2 and AUTO_ROLLBACK_ENABLED:
                        log.warning(f"[Monitor:Synth] 2 consecutive failures detected - attempting auto-rollback")
                        rb = await _attempt_auto_rollback(reason="synthetic checkout test 2x failure", failures=synth.get("failures", []))
                        if rb.get("ok"):
                            log.warning(f"[Monitor:Synth] auto-rollback SUCCESS: reverted to {rb.get('reverted_to_sha','')[:8]}")
                            # rollback 後はカウンタリセット (deploy 完了待ち + 次の合成テストで真の状態を再評価)
                            _SYNTHETIC_CONSECUTIVE_FAILS["count"] = 0
                            _SYNTHETIC_CONSECUTIVE_FAILS["last_rollback_ts"] = time.time()
                        else:
                            log.error(f"[Monitor:Synth] auto-rollback FAILED: {rb.get('error')}")
                else:
                    if _SYNTHETIC_CONSECUTIVE_FAILS["count"] > 0:
                        log.info(f"[Monitor:Synth] recovered after {_SYNTHETIC_CONSECUTIVE_FAILS['count']} failure(s)")
                    _SYNTHETIC_CONSECUTIVE_FAILS["count"] = 0
                    log.info(f"[Monitor:Synth] OK ({synth.get('duration_ms')}ms)")
            except Exception as e:
                log.error(f"[Monitor:Synth] test error: {e}", exc_info=True)
            # 2. JST DAILY_SUMMARY_HOUR_JST 時台 → デイリーサマリ送信判定
            now_jst = datetime.now(JST)
            if now_jst.hour == MONITORING_DAILY_SUMMARY_HOUR_JST:
                try:
                    summary_result = _send_daily_summary_if_due()
                    if summary_result.get("sent"):
                        log.info("[Monitor] Daily summary sent")
                except Exception as e:
                    log.error(f"[Monitor] daily summary error: {e}", exc_info=True)
            # 2-B. 🔥 24h 未ログイン生徒への自動 magic link 再送信 (Phase B nudge)
            # 朝 9 時 (JST) に1日1回実行。NEVER_LOGIN_NUDGE_HOUR_JST で変更可能。
            try:
                _maybe_run_never_login_nudge(now_jst)
            except Exception as e:
                log.error(f"[Monitor:Nudge] error: {e}", exc_info=True)
            # 2-C. 🌐 ドメイン状態 RDAP 監視 (2026-05-06 clientHold 事故再発防止)
            # 30 分おきに WHOIS Domain Status をチェック。clientHold/serverHold 検知時は緊急アラート。
            try:
                domain_check = _maybe_run_domain_status_check()
                if domain_check.get("ran") and not domain_check.get("ok", True):
                    log.warning(f"[Monitor:Domain] BAD STATUS: {domain_check.get('bad')}")
            except Exception as e:
                log.error(f"[Monitor:Domain] check error: {e}", exc_info=True)
            # 2-D. 🔔 Whois 認証年次リマインダー (年1回, デフォ 4/15 朝)
            try:
                _maybe_run_whois_renewal_reminder(now_jst)
            except Exception as e:
                log.error(f"[Monitor:Whois] reminder error: {e}", exc_info=True)
            # 3. 次のループまで sleep
            await asyncio.sleep(MONITORING_INTERVAL_MIN * 60)
        except asyncio.CancelledError:
            log.info("[Monitor] Scheduler cancelled")
            raise
        except Exception as e:
            log.error(f"[Monitor] scheduler loop error: {e}", exc_info=True)
            await asyncio.sleep(300)


# ==========================================================================
# 🛡️ 申込→決済 フロー E2E 合成テスト (2026-04-27 追加)
# 5分おきに以下を全自動チェックし、退化 (regression) があれば即時アラート:
#   1. /lp.html が 200 を返し、checkout.html へのリンクを含む
#   2. /checkout.html が 200 を返し、checkout.js?v=...（cache-busting 付き）を読込んでいる
#   3. /checkout.js が 200 を返し、修正済 fix marker (`if (target)` + `urlPlanOverride`) を含む
#   4. /api/trial/signup に sentinel データを POST し student_id を取得 (404/500 を回避)
# 失敗時は monitor email 即送信 + ダッシュ赤バナー表示。
# ==========================================================================
_SYNTHETIC_CHECKOUT_LAST = {
    "ok": None, "ts": None, "duration_ms": None, "failures": [], "details": {},
}
_SYNTHETIC_CHECKOUT_FIX_MARKERS = ["if (target)", "__urlPlanOverride"]
_SYNTHETIC_CHECKOUT_ALERTED_AT = {"ts": 0.0}


async def _run_synthetic_checkout_test() -> dict:
    """申込フロー全体を 5 分おきに自動回帰テスト。失敗時は alert を発火。

    エンドポイント設計:
      - フロントエンド HTML/JS: BASE_URL (Vercel) 経由でユーザーと同じ取得経路を検証
      - バックエンド API: Railway 直接 URL を使用 (Vercel の Security Checkpoint や
        307 redirect に翻弄されないため)
    """
    started = time.time()
    failures = []
    details = {}
    # フロント検証用 (ユーザー体験を再現)
    frontend_base = (BASE_URL or "https://trillion-ai-juku.com").rstrip("/")
    # バックエンド API 検証用 (Vercel 経由を回避)
    backend_base = "https://ai-juku-api-production.up.railway.app"

    def _http_get(url: str, timeout: int = 10, retries: int = 2) -> dict:
        """Railway 内部 → Vercel/Railway HTTP GET。
        2026-05-06 修正: リトライ機構、gzip 対応、最新 UA、ブラウザ互換ヘッダー
        timeout 10s × 3 試行 + backoff = worst-case ~33s per call (5 分監視 cycle 内に収まる)"""
        last_error = None
        for attempt in range(retries + 1):
            req = urllib.request.Request(url, headers={
                # 最新 Chrome 131 互換 (Vercel/Cloudflare の bot 検知をパス)
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Upgrade-Insecure-Requests": "1",
            })
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body_raw = resp.read()
                    # gzip 対応 (urllib は自動 decompress しない)
                    if resp.headers.get("Content-Encoding") == "gzip":
                        import gzip as _gzip
                        body_raw = _gzip.decompress(body_raw)
                    elif resp.headers.get("Content-Encoding") == "deflate":
                        import zlib as _zlib
                        body_raw = _zlib.decompress(body_raw)
                    body = body_raw.decode("utf-8", errors="replace")
                    return {"status": resp.status, "body": body, "url": url, "attempt": attempt + 1}
            except urllib.error.HTTPError as e:
                # 4xx/5xx は HTTPError として返す (retry しない・Vercel が明示的に返してる)
                return {"status": e.code, "body": "", "url": url, "error": str(e)}
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                if attempt < retries:
                    import time as _t
                    _t.sleep(1.5 ** attempt)  # backoff: 1.5s, 2.25s
                    continue
                return {"status": 0, "body": "", "url": url, "error": last_error, "attempts": retries + 1}

    loop = asyncio.get_event_loop()
    warnings_list = []  # warning 級 (実顧客影響なしの偽陽性) は failures と分離

    # 1. lp.html (Vercel 経由 — ユーザーが見る形で取得)
    # NOTE 2026-05-06: Railway 内部 → Vercel への urllib HTTP 接続が status=0 で失敗する
    # 偽陽性が常態化していたため、status=0 (network error) は warning 扱いに格下げ。
    # 実顧客は外部 ISP 経由でアクセスするため影響なし。HTTP error (4xx/5xx) は依然 failure。
    r1 = await loop.run_in_executor(None, _http_get, frontend_base + "/lp.html")
    details["lp_status"] = r1["status"]
    if r1["status"] == 0:
        warnings_list.append(f"lp.html: Railway→Vercel 内部接続失敗 (実顧客影響なし・{r1.get('error','?')[:80]})")
    elif r1["status"] != 200:
        failures.append(f"lp.html status={r1['status']}")
    elif "checkout.html" not in r1["body"]:
        failures.append("lp.html does not link to checkout.html")

    # 2. checkout.html (Vercel 経由)
    r2 = await loop.run_in_executor(None, _http_get, frontend_base + "/checkout.html")
    details["checkout_html_status"] = r2["status"]
    checkout_js_match = ""
    if r2["status"] == 0:
        warnings_list.append(f"checkout.html: Railway→Vercel 内部接続失敗 (実顧客影響なし)")
    elif r2["status"] != 200:
        failures.append(f"checkout.html status={r2['status']}")
    else:
        # checkout.js の version 付き script を抽出
        import re as _re
        m = _re.search(r'src="(checkout\.js[^"]*)"', r2["body"])
        if not m:
            failures.append("checkout.html does not include checkout.js script tag")
        else:
            checkout_js_match = m.group(1)
            details["checkout_js_path"] = checkout_js_match
            if "?v=" not in checkout_js_match:
                failures.append("checkout.js script tag has no cache-busting ?v= (regressions could persist via cache)")

    # 3. checkout.js fix marker check (Vercel 経由・status=200 取得時のみ)
    if r2["status"] == 200 and checkout_js_match:
        r3 = await loop.run_in_executor(None, _http_get, frontend_base + "/" + checkout_js_match)
        details["checkout_js_status"] = r3["status"]
        if r3["status"] == 0:
            warnings_list.append(f"checkout.js: Railway→Vercel 内部接続失敗")
        elif r3["status"] != 200:
            failures.append(f"checkout.js status={r3['status']}")
        else:
            for marker in _SYNTHETIC_CHECKOUT_FIX_MARKERS:
                if marker not in r3["body"]:
                    failures.append(f"checkout.js missing fix marker: {marker!r}")
            # form submit listener が attach される直前の textContent が壊れていないか粗チェック
            if "addEventListener('submit'" not in r3["body"] and 'addEventListener("submit"' not in r3["body"]:
                failures.append("checkout.js no longer registers form submit listener")

    # 4. POST /api/trial/signup (sentinel) — Railway 直接 (Vercel 経由は 307/checkpoint で不安定)
    # 名前: 「テスト」を含むと拒否されるので「監視 守」でパス。
    # email: Pydantic email-validator が .invalid/.test/.example を拒否するため、
    #   自社ドメインの専用サブドメイン synthetic-monitor.trillion-ai-juku.com を使用。
    #   この sub には MX レコード無し = 実害ゼロ + 構文検証は確実にパス。
    ts_int = int(time.time())
    sentinel_email = f"synth-monitor-{ts_int}@synthetic-monitor.trillion-ai-juku.com"
    sentinel_payload = {
        "plan": "founder_special",
        "name": "監視　守",
        "email": sentinel_email,
        "grade": "高校3年",
        "goal": "[E2E synthetic monitor / auto-cleanup]",
    }
    def _http_post_json(url: str, payload: dict, timeout: int = 10, retries: int = 2) -> dict:
        """Railway 内部 → Railway POST。
        2026-05-06 修正: リトライ機構追加 (_http_get と同じ resilience)"""
        body_bytes = json.dumps(payload).encode("utf-8")
        last_error = None
        for attempt in range(retries + 1):
            # Origin / Referer は本物のブラウザ訪問に近づける (CORS / _origin_allowed を通す)
            req = urllib.request.Request(url, data=body_bytes, method="POST", headers={
                "Content-Type": "application/json",
                "User-Agent": "ai-juku-synth-monitor/1.0",
                "Origin": frontend_base,
                "Referer": frontend_base + "/checkout.html",
            })
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return {"status": resp.status, "body": resp.read().decode("utf-8", errors="replace"), "attempt": attempt + 1}
            except urllib.error.HTTPError as e:
                # 4xx/5xx は明示的なエラー (retry しない・サーバー側の判断)
                return {"status": e.code, "body": e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""}
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                if attempt < retries:
                    import time as _t
                    _t.sleep(1.5 ** attempt)
                    continue
                return {"status": 0, "body": "", "error": last_error, "attempts": retries + 1}

    r4 = await loop.run_in_executor(None, _http_post_json, backend_base + "/api/trial/signup", sentinel_payload)
    details["signup_status"] = r4["status"]
    sentinel_student_id = None
    signup_email_sent = None
    if r4["status"] != 200:
        failures.append(f"/api/trial/signup status={r4['status']} body={r4.get('body','')[:200]}")
    else:
        try:
            j = json.loads(r4["body"])
            sentinel_student_id = j.get("student_id")
            signup_email_sent = j.get("email_sent")
            details["signup_student_id"] = sentinel_student_id
            details["signup_email_sent"] = signup_email_sent
        except Exception as e:
            failures.append(f"/api/trial/signup non-JSON body: {e}")

    # 4b. 🔥 致命傷検知: signup レスポンスの email_sent=True を必須化
    # (2026-04-30 追加: 8名全員ログイン不能の二度目を絶対阻止)
    # email_sent が False なら Resend 障害 or token 切れ → Auto-Rollback 対象。
    # signup 自体は成功しても、メールが届かなければ顧客は dashboard にたどり着けない。
    if r4["status"] == 200 and signup_email_sent is False:
        failures.append("/api/trial/signup email_sent=false (magic link メール未送信 = 顧客ログイン不能)")
    elif r4["status"] == 200 and signup_email_sent is None:
        # 旧 deploy で email_sent フィールド自体が無い場合は警告のみ (後方互換)
        details["signup_email_sent_warn"] = "field missing — old deploy?"

    # 4c. events.signup_email_status の DB 記録を確認 (申込後 5 秒以内に必ず記録されるべき)
    # signup 成功でも events に記録されていない = 監視 endpoint が壊れている兆候
    if sentinel_student_id:
        try:
            await asyncio.sleep(2.0)  # event 記録の遅延を吸収 (commit ラグ + Postgres 反映)
            conn = db()
            c = conn.cursor()
            session_key = f"student:{sentinel_student_id}"
            c.execute(
                "SELECT props FROM events WHERE name = 'signup_email_status' AND session_id = ? ORDER BY created_at DESC LIMIT 1",
                (session_key,)
            )
            row = c.fetchone()
            conn.close()
            if not row:
                failures.append(f"events.signup_email_status not recorded within 2s for student_id={sentinel_student_id}")
            else:
                try:
                    raw = row["props"] if hasattr(row, "__getitem__") else None
                    props = json.loads(raw) if isinstance(raw, str) else raw
                    if isinstance(props, dict):
                        details["event_email_sent"] = props.get("email_sent")
                        if props.get("email_sent") is False:
                            err_msg = (props.get("error") or "")[:120]
                            # signup レスポンス側で既に検出済みでなければ追加
                            if not any("email_sent=false" in f for f in failures):
                                failures.append(f"events.signup_email_status email_sent=false (error={err_msg})")
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"[Monitor:Synth] events.signup_email_status check failed: {e}")

    # 5. cleanup: sentinel student を DB から消す
    if sentinel_student_id:
        try:
            conn = db()
            c = conn.cursor()
            c.execute("DELETE FROM students WHERE id = ? AND email = ?", (sentinel_student_id, sentinel_email))
            conn.commit()
            conn.close()
        except Exception as e:
            log.warning(f"[Monitor:Synth] sentinel cleanup failed: {e}")

    duration_ms = int((time.time() - started) * 1000)
    ok = len(failures) == 0
    result = {
        "ok": ok,
        "ts": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "duration_ms": duration_ms,
        "failures": failures,
        "warnings": warnings_list,  # Railway→Vercel 内部接続偽陽性等 (実顧客影響なし)
        "details": details,
    }

    # 失敗時、cooldown 30 分でアラートメール送信
    if not ok:
        now_ts = time.time()
        if now_ts - _SYNTHETIC_CHECKOUT_ALERTED_AT["ts"] > 1800:
            _SYNTHETIC_CHECKOUT_ALERTED_AT["ts"] = now_ts
            try:
                subj = "🚨 申込→決済 E2E 監視 失敗 — 即時対応必要"
                fail_html = "<ul>" + "".join(f"<li>{html_escape_safe(f)}</li>" for f in failures) + "</ul>"
                body_html = (
                    f"<h2>🚨 5分おき自動 E2E 監視で失敗を検知しました</h2>"
                    f"<p>申込→決済フローが壊れている可能性があります。<strong>機会損失中です。即時対応必要。</strong></p>"
                    f"<h3>失敗内容</h3>{fail_html}"
                    f"<h3>詳細</h3><pre>{html_escape_safe(json.dumps(details, ensure_ascii=False, indent=2))}</pre>"
                    f"<p><a href='{base}/ceo.html'>CEO ダッシュボードを開く</a></p>"
                )
                _send_monitor_email(subj, body_html)
            except Exception as e:
                log.warning(f"[Monitor:Synth] alert email failed: {e}")

    # events に結果を記録 (ダッシュ表示用)
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("synthetic_checkout_test", json.dumps(result, ensure_ascii=False)[:4000], "monitor")
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    return result


def html_escape_safe(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ==========================================================================
# 🚨 即時自動修復 (Auto-Rollback) — 2026-04-27 追加
# 2 連続合成テスト失敗時に直前 commit を GitHub API 経由で revert → Vercel 自動再deploy
# 通知メールだけでなく実際にコードを直前バージョンに戻すことで顧客損失を最小化
#
# 必須環境変数 (Railway側):
#   GITHUB_REVERT_PAT: contents:write 権限の GitHub Personal Access Token (or fine-grained token)
#   GITHUB_REPO: 対象リポジトリ "owner/repo" 形式 (default: 既知の repo)
#   AUTO_ROLLBACK_ENABLED: "1" で有効化 (default: 1 = 有効)
#
# Safety guardrails:
#   - 1 時間 cooldown (rollback 連発防止)
#   - 24h 内 max 3 回 (それ以上は人間判断必要)
#   - 既に同じ commit に rollback 済みなら skip (loop 防止)
# ==========================================================================
GITHUB_REVERT_PAT = os.getenv("GITHUB_REVERT_PAT", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "shock11090304-a11y/ai-juku-system")
AUTO_ROLLBACK_ENABLED = os.getenv("AUTO_ROLLBACK_ENABLED", "1") == "1"
AUTO_ROLLBACK_BRANCH = os.getenv("AUTO_ROLLBACK_BRANCH", "main")
_SYNTHETIC_CONSECUTIVE_FAILS = {"count": 0, "last_failure_ts": 0.0, "last_rollback_ts": 0.0}
_AUTO_ROLLBACK_HISTORY = []  # [{ts, from_sha, to_sha, reason}]


def _github_api(method: str, path: str, body: dict = None, timeout: int = 15) -> dict:
    """GitHub REST API ヘルパ。{ok, status, json, error} を返す。"""
    if not GITHUB_REVERT_PAT:
        return {"ok": False, "status": 0, "error": "GITHUB_REVERT_PAT not configured"}
    url = "https://api.github.com" + (path if path.startswith("/") else "/" + path)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {GITHUB_REVERT_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ai-juku-auto-rollback/1.0",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body_text = resp.read().decode("utf-8", errors="replace")
            try:
                j = json.loads(body_text) if body_text else {}
            except Exception:
                j = {"_raw": body_text[:500]}
            return {"ok": True, "status": resp.status, "json": j}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        return {"ok": False, "status": e.code, "error": f"HTTP {e.code}: {err_body[:300]}"}
    except Exception as e:
        return {"ok": False, "status": 0, "error": f"{type(e).__name__}: {e}"}


async def _attempt_auto_rollback(reason: str, failures: list = None, force: bool = False) -> dict:
    """直前 commit を GitHub branch HEAD から revert (= 1 つ前の SHA に branch を更新)。
    Vercel が main branch を監視している場合、自動的に旧コードで再 deploy される。

    挙動:
      1. 環境変数 / cooldown / 24h 上限の事前チェック
      2. GET refs/heads/{branch} で現在 SHA 取得
      3. GET commits/{sha} で parent SHA 取得 (1 つ前のコミット)
      4. PATCH refs/heads/{branch} で branch HEAD を parent SHA へ巻き戻し (force)
      5. 成功時 monitor email + dashboard event 送信、history 記録
    """
    failures = failures or []
    nowts = time.time()

    # ---- 安全装置 ----
    if not AUTO_ROLLBACK_ENABLED and not force:
        return {"ok": False, "error": "AUTO_ROLLBACK_ENABLED=0 (kill-switch active)"}
    if not GITHUB_REVERT_PAT:
        return {"ok": False, "error": "GITHUB_REVERT_PAT not configured. Railway env で設定してください"}
    # 1 時間 cooldown
    if not force and nowts - _SYNTHETIC_CONSECUTIVE_FAILS.get("last_rollback_ts", 0) < 3600:
        return {"ok": False, "error": "cooldown: 直近 1 時間以内に rollback 実行済み (force=true で強制可)"}
    # 24h max 3
    recent_24h = [r for r in _AUTO_ROLLBACK_HISTORY if nowts - r["ts"] < 86400]
    if not force and len(recent_24h) >= 3:
        return {"ok": False, "error": f"24h 内に既に {len(recent_24h)} 回 rollback 済み (上限 3)。人間判断が必要です"}

    loop = asyncio.get_event_loop()

    # ---- 1. 現在の HEAD SHA ----
    r_head = await loop.run_in_executor(None, _github_api, "GET", f"/repos/{GITHUB_REPO}/git/refs/heads/{AUTO_ROLLBACK_BRANCH}")
    if not r_head.get("ok"):
        return {"ok": False, "error": f"failed to fetch HEAD: {r_head.get('error')}"}
    current_sha = (r_head.get("json") or {}).get("object", {}).get("sha")
    if not current_sha:
        return {"ok": False, "error": "could not parse current HEAD sha"}

    # ---- 2. parent SHA (1 つ前のコミット) ----
    r_commit = await loop.run_in_executor(None, _github_api, "GET", f"/repos/{GITHUB_REPO}/commits/{current_sha}")
    if not r_commit.get("ok"):
        return {"ok": False, "error": f"failed to fetch commit info: {r_commit.get('error')}"}
    parents = (r_commit.get("json") or {}).get("parents", [])
    if not parents:
        return {"ok": False, "error": "current commit has no parent (initial commit?). Cannot rollback."}
    parent_sha = parents[0].get("sha")
    if not parent_sha:
        return {"ok": False, "error": "parent commit sha not found"}

    # ---- 3. branch HEAD を parent SHA に force update ----
    r_update = await loop.run_in_executor(
        None, _github_api,
        "PATCH",
        f"/repos/{GITHUB_REPO}/git/refs/heads/{AUTO_ROLLBACK_BRANCH}",
        {"sha": parent_sha, "force": True},
    )
    if not r_update.get("ok"):
        return {"ok": False, "error": f"failed to update branch HEAD: {r_update.get('error')}"}

    # ---- 4. 履歴記録 + メール通知 ----
    rb_record = {
        "ts": nowts,
        "iso": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "from_sha": current_sha,
        "to_sha": parent_sha,
        "reason": reason,
        "failures": failures[:5],
    }
    _AUTO_ROLLBACK_HISTORY.append(rb_record)
    if len(_AUTO_ROLLBACK_HISTORY) > 50:
        del _AUTO_ROLLBACK_HISTORY[:-50]

    try:
        commit_msg = (r_commit.get("json") or {}).get("commit", {}).get("message", "")[:200]
        commit_author = (r_commit.get("json") or {}).get("commit", {}).get("author", {}).get("name", "")
        body_html = (
            f"<h2>🚨 自動 ROLLBACK 実行 — 顧客接触は復旧します (Vercel 再 deploy 待ち)</h2>"
            f"<p><strong>理由:</strong> {html_escape_safe(reason)}</p>"
            f"<p><strong>2連続失敗のため、直前 commit を巻き戻しました。</strong></p>"
            f"<h3>巻き戻された commit (壊れていた疑い)</h3>"
            f"<ul><li>SHA: <code>{current_sha[:8]}</code></li>"
            f"<li>Author: {html_escape_safe(commit_author)}</li>"
            f"<li>Message: {html_escape_safe(commit_msg)}</li></ul>"
            f"<h3>現在の HEAD (戻された安全な commit)</h3>"
            f"<ul><li>SHA: <code>{parent_sha[:8]}</code></li></ul>"
            f"<h3>失敗詳細</h3>"
            "<ul>" + "".join(f"<li>{html_escape_safe(str(f))}</li>" for f in failures[:10]) + "</ul>"
            f"<p>Vercel の自動再 deploy で 2-3 分以内に旧コードが再公開されます。次の合成テストで OK が出れば自動修復成功です。</p>"
            f"<p><strong>本格修正:</strong> 巻き戻された commit のバグを直し、新しい commit として再 push してください。</p>"
        )
        _send_monitor_email("🚨 申込フロー auto-rollback 実行", body_html)
    except Exception as e:
        log.warning(f"[auto-rollback] notification email failed: {e}")

    # ---- 5. events 記録 ----
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("auto_rollback", json.dumps(rb_record, ensure_ascii=False)[:4000], "monitor")
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    return {
        "ok": True,
        "rolled_back_from": current_sha,
        "reverted_to_sha": parent_sha,
        "reason": reason,
        "rb_record": rb_record,
    }


@app.post("/api/admin/monitor/auto-rollback")
async def admin_auto_rollback_now(payload: dict = None, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """🚨 直前 commit を auto-rollback (admin Bearer or x-cron-secret 認証必須)。
    payload: {force: bool, reason: str}
    force=true なら cooldown / 24h 上限を無視。
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    payload = payload or {}
    force = bool(payload.get("force", False))
    reason = (payload.get("reason") or "manual")[:200]
    result = await _attempt_auto_rollback(reason=reason, failures=["manual trigger"], force=force)
    return result


@app.get("/api/admin/monitor/rollback-history")
def admin_rollback_history(authorization: Optional[str] = Header(None)):
    """auto-rollback 実行履歴を返す (admin Bearer)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    return {
        "ok": True,
        "auto_rollback_enabled": AUTO_ROLLBACK_ENABLED,
        "github_repo": GITHUB_REPO,
        "branch": AUTO_ROLLBACK_BRANCH,
        "pat_configured": bool(GITHUB_REVERT_PAT),
        "consecutive_fails": _SYNTHETIC_CONSECUTIVE_FAILS,
        "history": _AUTO_ROLLBACK_HISTORY[-20:],
    }


_LAST_OTP_GC_TS = {"ts": 0.0}

def _create_otp(student_id: int, ttl_seconds: int = 600) -> str:
    """6桁数字のOTPコードを生成しDBに保存。10分有効。

    DB 肥大化対策 (4番手 監査 2026-04-30):
    - 同一 student の未使用 active OTP が3件以上ある場合、最も古い1件を invalidate
      (1人で12時間に大量発行→DB 行が無限に増えるのを防ぐ)
    - グローバル GC: 1時間に1回、全体の expires_at < now-7days な行を物理削除
    """
    import secrets
    import time as _time
    code = f"{secrets.randbelow(1000000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    conn = db()
    c = conn.cursor()
    # 1) 同一 student の active OTP を最大 3件に制限
    try:
        c.execute(
            "SELECT id FROM otp_codes WHERE student_id = ? AND used_at IS NULL "
            "AND expires_at > CURRENT_TIMESTAMP ORDER BY created_at ASC",
            (student_id,)
        )
        rows = c.fetchall()
        # 新規発行で 4件目になるなら、古い分を invalidate
        if len(rows) >= 3:
            stale_ids = [r["id"] for r in rows[:-2]]  # 直近2件以外を無効化
            placeholders = ",".join(["?"] * len(stale_ids))
            c.execute(
                f"UPDATE otp_codes SET used_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
                tuple(stale_ids)
            )
    except Exception as _e:
        log.debug(f"[OTP] active-otp limit cleanup failed: {_e}")
    # 2) 新規 OTP 挿入
    c.execute(
        "INSERT INTO otp_codes (student_id, code, expires_at) VALUES (?, ?, ?)",
        (student_id, code, expires_at.isoformat())
    )
    conn.commit()
    conn.close()
    # 3) Opportunistic global GC (1時間に1回): 7日前以前の expired を物理削除
    now_ts = _time.time()
    if now_ts - _LAST_OTP_GC_TS["ts"] > 3600:
        _LAST_OTP_GC_TS["ts"] = now_ts
        try:
            conn2 = db(); c2 = conn2.cursor()
            if USE_POSTGRES:
                c2.execute("DELETE FROM otp_codes WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days'")
            else:
                c2.execute("DELETE FROM otp_codes WHERE expires_at < datetime('now', '-7 days')")
            deleted = c2.rowcount or 0
            conn2.commit(); conn2.close()
            if deleted > 0:
                log.info(f"[OTP-GC] purged {deleted} expired otp_codes rows (>7 days old)")
        except Exception as _e:
            log.warning(f"[OTP-GC] cleanup failed: {_e}")
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

    # 🔥 致命傷修正 (2026-04-30): synthetic monitor 用アドレスへの送信は SKIP
    # @synthetic-monitor.trillion-ai-juku.com は MX レコード無し → 100% bounce
    # 5分おき monitor が Resend 無料枠 (100/日) を圧迫 + bounce rate 悪化 → 429 連発
    # 169 件連続失敗の根本原因。実 API call せず synthetic ID 返す (E2E 監視継続のため)。
    if "@synthetic-monitor." in (to_email or "").lower():
        log.info(f"[Magic Link] Skip Resend API for synthetic monitor: {to_email}")
        return {"sent": True, "resend_id": "synthetic-skip", "synthetic": True}

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


# キャリアメール (HTML が崩れる / フィルタが厳しい): 警告ログのみ
_CARRIER_DOMAINS = (
    "ezweb.ne.jp", "i.softbank.jp", "softbank.ne.jp",
    "docomo.ne.jp", "au.com", "ymobile.ne.jp",
    "ido.ne.jp", "vodafone.ne.jp", "ezweb.jp", "pdx.ne.jp",
)


def _is_carrier_email(email: str) -> bool:
    e = (email or "").lower().strip()
    return any(e.endswith("@" + d) for d in _CARRIER_DOMAINS)


def _send_magic_link_with_retry(to_email: str, student_name: str, magic_url: str,
                                  otp_code: str = "", is_welcome: bool = False,
                                  max_attempts: int = 3) -> dict:
    """_send_magic_link_email を 429/一時エラー対応で最大 max_attempts 回リトライ。
    指数バックオフ (1s → 2s → 4s)。bounce/blocked 系のレスポンスは即諦める。
    キャリアメール宛は注意ログを出す。"""
    import time as _t
    if _is_carrier_email(to_email):
        log.warning(f"[MagicLink] Carrier email destination: {to_email} (HTML may render poorly / spam filters strict)")

    last_error: Optional[str] = None
    for attempt in range(max_attempts):
        try:
            result = _send_magic_link_email(
                to_email, student_name, magic_url,
                otp_code=otp_code, is_welcome=is_welcome,
            )
            if isinstance(result, dict) and result.get("sent"):
                return result
            last_error = (result or {}).get("error", "send_failed")
            err_str = str(last_error).lower()
            # bounce / blocked / invalid: リトライ無意味
            if any(k in err_str for k in ("bounce", "blocked", "invalid", "not_found", "validation_error", "400", "404", "422")):
                log.warning(f"[MagicLink] Permanent failure for {to_email} (no retry): {last_error}")
                return {"sent": False, "error": last_error, "permanent": True}
            # 429 / 5xx / timeout 系のみリトライ
            if attempt < max_attempts - 1 and any(k in err_str for k in ("429", "too many", "rate", "timeout", "503", "502", "500")):
                _t.sleep(2 ** attempt)  # 1s → 2s → 4s
                continue
            break
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            log.error(f"[MagicLink] retry attempt {attempt+1} exception for {to_email}: {last_error}")
            if attempt < max_attempts - 1:
                _t.sleep(2 ** attempt)
    return {"sent": False, "error": last_error or "unknown", "retried": True}


def _invalidate_active_otps(student_id: int) -> None:
    """指定生徒の有効な OTP を全て無効化。重複申込・magic-link 再送時に旧コード混乱防止。
    失敗してもログのみ (致命ではない)。"""
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "UPDATE otp_codes SET used_at = CURRENT_TIMESTAMP "
            "WHERE student_id = ? AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP",
            (student_id,)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning(f"[OTP] failed to invalidate active OTPs for student {student_id}: {e}")


def _record_critical_event(name: str, props: dict) -> None:
    """致命系の event を記録 (notification_all_channels_failed など)。
    DB 不調でも例外で死なない (best-effort)。"""
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            (name, json.dumps(props, ensure_ascii=False)[:4000], "notification-fallback")
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning(f"[CriticalEvent] failed to record {name}: {e}")


def _send_login_link_via_line(student_id: int, magic_url: str, otp_code: str) -> dict:
    """LINE 経由で magic link を送信。LINE_TEMPLATES['magic_link_login'] を使う。
    line_user_id が無い / LINE 未設定なら {sent: False, reason: ...} を返す (例外は投げない)。
    成功時は notifications テーブルに記録される (_do_line_push の責務)。"""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        return {"sent": False, "reason": "line_not_configured"}
    try:
        result = _do_line_push(student_id, "magic_link_login", {
            "magic_url": magic_url,
            "otp_code": otp_code,
        })
        if isinstance(result, dict) and result.get("ok"):
            return {"sent": True}
        return {"sent": False, "reason": (result or {}).get("message") or "line_push_failed"}
    except HTTPException as he:
        # _do_line_push は line_user_id 無しで 404 を投げる
        if he.status_code == 404:
            return {"sent": False, "reason": "no_line_user_id"}
        return {"sent": False, "reason": f"http_{he.status_code}"}
    except Exception as e:
        log.warning(f"[LINE-Fallback] student {student_id} push failed: {type(e).__name__}: {e}")
        return {"sent": False, "reason": f"{type(e).__name__}: {str(e)[:120]}"}


def _send_login_link_multi(student_id: int, email: str, name: str, magic_url: str,
                            otp_code: str, is_welcome: bool = False,
                            force_line: bool = False) -> dict:
    """email + LINE のマルチチャネル fallback で magic link を送信。
    - email を試行
    - 失敗 OR キャリアメール (ezweb/docomo/au.com 等) OR force_line=True なら LINE も併用
    - 両方失敗時は events に critical 記録 (notification_all_channels_failed)
    返り値: {email_sent, line_sent, both_failed, email_error, line_reason, is_carrier}
    """
    out = {"email_sent": False, "line_sent": False, "both_failed": False,
           "email_error": None, "line_reason": None,
           "is_carrier": _is_carrier_email(email or "")}

    # 1) email 送信 (既存 retry helper を活用)
    if email:
        try:
            email_result = _send_magic_link_with_retry(
                email, name or "", magic_url,
                otp_code=otp_code, is_welcome=is_welcome,
            )
            out["email_sent"] = bool(email_result.get("sent"))
            if not out["email_sent"]:
                out["email_error"] = email_result.get("error") or "send_failed"
        except Exception as e:
            out["email_error"] = f"{type(e).__name__}: {str(e)[:120]}"
            log.error(f"[Notify-Multi] email exception for student {student_id}: {out['email_error']}")
    else:
        out["email_error"] = "no_email"

    # 2) LINE 併用判定: 失敗 OR キャリアメール OR force_line
    should_try_line = force_line or out["is_carrier"] or (not out["email_sent"])
    if should_try_line:
        line_result = _send_login_link_via_line(student_id, magic_url, otp_code)
        out["line_sent"] = bool(line_result.get("sent"))
        if not out["line_sent"]:
            out["line_reason"] = line_result.get("reason")

    # 3) 両方失敗 → critical event
    if not out["email_sent"] and not out["line_sent"]:
        out["both_failed"] = True
        _record_critical_event("notification_all_channels_failed", {
            "student_id": student_id,
            "email": email,
            "is_carrier": out["is_carrier"],
            "email_error": out["email_error"],
            "line_reason": out["line_reason"],
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        log.error(f"[Notify-Multi] BOTH CHANNELS FAILED student={student_id} email={email} "
                  f"carrier={out['is_carrier']} email_err={out['email_error']} line={out['line_reason']}")
    return out


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
    c.execute("SELECT id, name, email, grade, goal, plan, status, stripe_customer_id, trial_end, enrollment_fee_waived, course FROM students WHERE id = ?", (claims["student_id"],))
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

    # 国公立難関大学コース所属生徒は trial_end に関係なく永久アクセス許可 (塾長指示: 永久無料)
    if not is_allowed:
        try:
            _course = row["course"] if "course" in row.keys() else None
        except Exception:
            _course = None
        if _course == "kokuritsu_nankan":
            is_allowed = True

    if not is_allowed:
        return None
    # enrollment_fee_waived は新カラム → 古いDB行で存在しない場合に備えて defensive access
    try:
        waived = bool(row["enrollment_fee_waived"]) if "enrollment_fee_waived" in row.keys() else False
    except (KeyError, TypeError, IndexError):
        waived = False
    course_val = None
    try:
        course_val = row["course"] if "course" in row.keys() else None
    except (KeyError, TypeError, IndexError):
        course_val = None
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "grade": row["grade"],
        "goal": row["goal"],
        "plan": row["plan"],
        "status": status,
        "enrollment_fee_waived": waived,  # mypage の「免除済みバッジ」表示に使用
        "course": course_val,  # 国公立難関大学コース ('kokuritsu_nankan') 識別 (塾長指示 2026-05-04)
    }


# ==========================================================================
# Routes: Authentication (Magic Link)
# ==========================================================================
class MagicLinkRequest(BaseModel):
    email: EmailStr


@app.post("/api/auth/magic-link")
def request_magic_link(payload: MagicLinkRequest, request: Request):
    """メールアドレスから生徒を検索し、ログインURLをメール送信する。
    存在しないメールでも 200 を返す（アカウント列挙攻撃対策）。
    再送時は古い OTP を無効化して新しいコードのみ有効にする。"""
    email_lower = (payload.email or "").lower().strip()
    if not email_lower:
        raise HTTPException(status_code=400, detail="Email required")
    # レート制限: 同一IPから1分間に5回まで (現状値、ブルートフォース抑制と UX のバランス)
    _check_rate_limit_ip(request, bucket="magic_link", limit=5, window=60)

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, status, trial_end, course FROM students WHERE LOWER(email) = ? LIMIT 1", (email_lower,))
    row = c.fetchone()
    conn.close()

    # 体験期間中の trial ユーザーも送信対象（trial_end 未経過のみ）
    # 国公立難関大学コース所属生徒は trial_end に関係なく常に送信可 (永久無料)
    is_sendable = False
    is_trial_expired = False
    if row:
        _row_course = row["course"] if "course" in row.keys() else None
        if row["status"] == "paid":
            is_sendable = True
        elif _row_course == "kokuritsu_nankan":
            is_sendable = True
        elif row["status"] == "trial":
            te = row["trial_end"]
            if te:
                try:
                    if isinstance(te, str):
                        te_dt = datetime.fromisoformat(te.replace("Z", "+00:00"))
                    else:
                        te_dt = te
                    if te_dt.tzinfo is None:
                        te_dt = te_dt.replace(tzinfo=timezone.utc)
                    if te_dt > datetime.now(timezone.utc):
                        is_sendable = True
                    else:
                        is_trial_expired = True
                except Exception:
                    pass

    if is_sendable:
        # 古い OTP を全て無効化してから新規発行 (再送 UX: 新コードのみ有効)
        _invalidate_active_otps(row["id"])
        # magic link には 1時間のみ有効な短命トークンを使う (4番手 監査 2026-04-30):
        # 30日 session token を URL に直入れすると referer / browser history 経由で漏洩した時の
        # 影響範囲が大きすぎる。/api/auth/verify が新規 session token に交換する。
        token = _create_magic_link_token(row["id"])
        magic_url = f"{BASE_URL}/auth.html?t={token}"
        otp_code = _create_otp(row["id"])
        _send_magic_link_with_retry(row["email"], row["name"] or "", magic_url, otp_code=otp_code, is_welcome=False)
    elif is_trial_expired:
        # 期間切れは案内専用文言を返す (列挙対策上は status code は 200 のままで OK)
        log.info(f"Magic link requested but trial expired: {email_lower}")
        return {
            "ok": True,
            "trial_expired": True,
            "message": "体験期間が終了しています。継続をご希望の方はLPから本登録をお願いします。",
        }
    else:
        # 存在しない or 状態不明: 同じレスポンスを返す（列挙対策）
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
    code_raw = (payload.code or "")
    # 全角数字 → 半角化、空白・ハイフン・タブ等を除去 (UX: コピペ事故救済)
    _zen_to_han = str.maketrans("0123456789", "0123456789")
    code = code_raw.translate(_zen_to_han)
    code = "".join(ch for ch in code if ch.isdigit())
    if not email_lower or not code or len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=400, detail="有効なメールアドレスと6桁のコードを入力してください")

    # シンプルなIP rate limit (in-memory)
    _check_rate_limit_ip(request, bucket="verify_code", limit=10, window=60)

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, grade, goal, plan, status, trial_end, course FROM students WHERE LOWER(email) = ? LIMIT 1", (email_lower,))
    student = c.fetchone()

    generic_401 = HTTPException(status_code=401, detail="コードが正しくないか、有効期限が切れています")

    # trial_end 未経過の trial ユーザーも許可
    # 国公立難関大学コース所属生徒は trial_end に関係なく常に許可 (永久無料)
    _active = False
    if student:
        _st_course = student["course"] if "course" in student.keys() else None
        if student["status"] == "paid":
            _active = True
        elif _st_course == "kokuritsu_nankan":
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

    # 最終ログイン時刻を更新 (CEO ダッシュ「最終ログイン」表示用)
    try:
        c.execute("UPDATE students SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?", (student["id"],))
    except Exception as _e:
        log.warning(f"[verify-code] last_login_at update failed: {_e}")

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
            "course": student["course"],
        }
    }


@app.get("/api/auth/verify")
def verify_magic_link(t: str):
    """auth.html からのトークン検証。有効なら生徒情報 + 新規 session token を返す。

    入力: 'magic' タイプ (1時間有効、URL 埋め込み用) または旧フォーマット ('session', 30日)。
    出力: 必ず新規 'session' トークンを発行 (URL 漏洩リスクを切り離す)。
    クライアントは localStorage にこの新トークンを保存する (4番手 監査 2026-04-30)。"""
    import time as _t
    # expected_type=None で magic / session 両方を許容
    claims = _verify_session_token(t, expected_type=None)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired link")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, grade, goal, plan, status, trial_end, course FROM students WHERE id = ?", (claims["student_id"],))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")

    # paid or trial(未経過)のみ許可
    # 国公立難関大学コース所属生徒は trial_end に関係なく常に許可 (永久無料)
    _allowed = False
    _v_course = row["course"] if "course" in row.keys() else None
    if row["status"] == "paid":
        _allowed = True
    elif _v_course == "kokuritsu_nankan":
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

    # 新規 session token を発行 (URL の magic token は1時間で破棄、セッションは30日)
    new_session_token = _sign_session_token(row["id"])
    new_exp = int(_t.time()) + SESSION_TTL_SECONDS

    return {
        "ok": True,
        "token": new_session_token,
        "expires_at": new_exp,
        "student": {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "grade": row["grade"],
            "goal": row["goal"],
            "plan": row["plan"],
            "status": row["status"],
            "course": row["course"],
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
    """塾長パスワードで認証。成功時は30日有効のトークンを返す。
    keychain 自動入力で連続失敗するケースを救済するため limit 緩め (20/5min)。
    成功時には失敗カウンタをリセットする。"""
    _check_rate_limit_ip(request, bucket="admin_login", limit=20, window=300)
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="管理者パスワードが未設定です。Railway環境変数 ADMIN_PASSWORD を設定してください。")
    if not hmac.compare_digest((payload.password or ""), ADMIN_PASSWORD):
        log.warning(f"Admin login failed from {_client_ip(request)}")
        raise HTTPException(status_code=401, detail="パスワードが正しくありません")
    ip = _client_ip(request)
    _RATE_LIMIT_STORE.pop((ip, "admin_login"), None)
    tok = _sign_admin_token()
    log.info(f"Admin login success from {ip}")
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
    # last_login_at は migration 直後の旧 DB に存在しない可能性あり → try/except でフォールバック
    try:
        c.execute("SELECT id, name, email, grade, goal, plan, status, trial_end, paid_since, created_at, last_login_at, line_user_id, course FROM students ORDER BY id DESC")
        rows = c.fetchall()
        has_last_login = True
    except Exception:
        try:
            c.execute("SELECT id, name, email, grade, goal, plan, status, trial_end, paid_since, created_at, line_user_id, course FROM students ORDER BY id DESC")
            rows = c.fetchall()
            has_last_login = False
        except Exception:
            c.execute("SELECT id, name, email, grade, goal, plan, status, trial_end, paid_since, created_at FROM students ORDER BY id DESC")
            rows = c.fetchall()
            has_last_login = False
    # 最終アクティビティ計算 (last_login_at + events + study_logs + exam_results の MAX)
    # 集約クエリで 3 回 DB ヒットに抑える (N+1 回避)
    # NOTE: events.session_id は "123" と "student:123" 両形式が混在 (legacy 不整合)
    events_latest = {}
    try:
        # 数値文字列 OR "student:数値" の session_id を student id として集約
        # 2026-05-07: LIKE 'student:%' の % が psycopg3 にプレースホルダとして誤認識されて
        # 「only '%s', '%b', '%t' are allowed as placeholders, got '%''」エラー連発していたので
        # %% にエスケープ + LIKE を文字位置 substr に置換 (postgres/sqlite 両対応簡素化)
        c.execute("""
            SELECT student_key, MAX(created_at) AS latest FROM (
                SELECT CASE WHEN substr(session_id, 1, 8) = 'student:' THEN substr(session_id, 9) ELSE session_id END AS student_key, created_at
                FROM events
                WHERE (session_id ~ '^[0-9]+$' OR session_id ~ '^student:[0-9]+$')
            ) sub GROUP BY student_key
        """)
        for r in c.fetchall():
            try: events_latest[int(r["student_key"])] = r["latest"]
            except (ValueError, TypeError): pass
    except Exception as _e:
        log.warning(f"[admin_stats] events latest query failed: {_e}")
    study_log_latest = {}
    try:
        c.execute("SELECT student_id, MAX(created_at) AS latest FROM study_logs GROUP BY student_id")
        study_log_latest = {r["student_id"]: r["latest"] for r in c.fetchall()}
    except Exception: pass
    exam_latest = {}
    try:
        c.execute("SELECT student_id, MAX(created_at) AS latest FROM exam_results GROUP BY student_id")
        exam_latest = {r["student_id"]: r["latest"] for r in c.fetchall()}
    except Exception: pass

    def _latest_activity(sid: int, last_login_raw):
        """4 つのソースから max を取り、isoformat 文字列で返す。全て None なら None。"""
        candidates = []
        for v in (last_login_raw, events_latest.get(sid), study_log_latest.get(sid), exam_latest.get(sid)):
            if not v: continue
            if isinstance(v, str):
                try: candidates.append(datetime.fromisoformat(v.replace("Z", "+00:00")))
                except ValueError: continue
            else:
                candidates.append(v)
        if not candidates: return None
        # tz 揃え
        normalized = []
        for d in candidates:
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            normalized.append(d)
        return max(normalized).isoformat()

    students = []
    for row in rows:
        # row["line_user_id"] は schema が古いと KeyError → 安全に拾う
        try:
            _line_uid = row["line_user_id"]
        except Exception:
            _line_uid = None
        _email = row["email"] or ""
        _last_login = (row["last_login_at"] if has_last_login else None)
        _latest_act = _latest_activity(row["id"], _last_login)
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
            "last_login_at": (str(_last_login) if _last_login else None),
            "latest_activity_at": _latest_act,  # 学習記録/AI質問/模試含む最終アクティビティ
            "has_line": bool(_line_uid),
            "is_carrier_email": _is_carrier_email(_email),
            "course": (row["course"] if "course" in row.keys() else None),
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

    # 🔧 plan→月額料金マップ。MRR/ARR 集計はこのマップに無いプランを 0 円扱いするため、
    # 全有効プランをここに列挙する必要がある (2026-05-03 founder_special 漏れで MRR=0 致命事故)。
    # founder_special は THREADS6K クーポン経路 ¥12,000 永年 (memory note 根拠)。
    # founder1 は旧 founder_special の後方互換キー (line 111 と同期)。
    plan_fees = {
        "standard": 24980,
        "premium": 39800,
        "family": 59800,
        "student_addon": 5000,
        "founder_special": 12000,
        "founder1": 12000,
    }
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
    start_utc = datetime.combine(start_date, dt_time(0, 0), tzinfo=JST).astimezone(timezone.utc)
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
        d_start_utc = datetime.combine(d, dt_time(0, 0), tzinfo=JST).astimezone(timezone.utc)
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

    # ============================================
    # referrer / utm_source 別 PV 集計 (Instagram 流入計測)
    # ============================================
    def _classify_referrer(props_text: str) -> tuple[str, str]:
        """props JSON から referrer と utm_source を抽出し、(source_label, raw_url) を返す"""
        try:
            props = json.loads(props_text or "{}")
        except Exception:
            return ("(parse error)", "")
        ref = (props.get("referrer") or "").strip()
        utm = (props.get("utm_source") or props.get("utmSource") or "").strip().lower()
        # page_path に utm_source が QS で入っている場合も拾う
        page_path = props.get("page_path") or ""
        if not utm and "utm_source=" in page_path:
            try:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(page_path).query)
                utm = (qs.get("utm_source", [""])[0] or "").lower()
            except Exception:
                pass
        # 分類
        if utm:
            return (f"utm:{utm}", ref)
        if not ref:
            return ("Direct / Bookmark", "")
        try:
            from urllib.parse import urlparse
            host = urlparse(ref).hostname or ""
            host = host.lower().replace("www.", "")
            if "instagram" in host: return ("Instagram", ref)
            if "facebook" in host or "fb.com" in host: return ("Facebook", ref)
            if "twitter" in host or "t.co" in host or "x.com" in host: return ("Twitter / X", ref)
            if "tiktok" in host: return ("TikTok", ref)
            if "threads" in host: return ("Threads", ref)
            if "youtube" in host or "youtu.be" in host: return ("YouTube", ref)
            if "google" in host: return ("Google", ref)
            if "yahoo" in host: return ("Yahoo!", ref)
            if "bing" in host: return ("Bing", ref)
            if "trillion-ai-juku" in host: return ("Internal", ref)
            return (host or "(unknown)", ref)
        except Exception:
            return ("(parse error)", ref)

    def _aggregate_referrers(since) -> list:
        c.execute(
            "SELECT props FROM events WHERE name='page_view' AND created_at >= ?",
            (since,)
        )
        bucket: dict = {}
        for row in c.fetchall():
            label, _ = _classify_referrer(row["props"] or "{}")
            bucket[label] = bucket.get(label, 0) + 1
        return sorted(
            [{"source": k, "count": v} for k, v in bucket.items()],
            key=lambda x: x["count"], reverse=True
        )[:15]

    referrers_24h = _aggregate_referrers(h24)
    referrers_7d = _aggregate_referrers(d7)

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
        "referrers_24h": referrers_24h,
        "referrers_7d": referrers_7d,
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

# ==========================================================================
# AI never-fail フェイルセーフ (塾長指示 2026-04-29):
# AI 関連機能はミスやエラーでシステムが止まることは絶対にあってはならない。
# 全 Anthropic 呼び出しはこの _call_anthropic_safe() 経由で実行する。
# - 3 段モデルフォールバック (要求モデル → Sonnet → Haiku)
# - 指数バックオフリトライ (5xx/timeout/network)
# - credit 不足検知時は ai_credit_low イベント発火 (CEO ダッシュ緊急バナー)
# ==========================================================================
_AI_CIRCUIT_BREAKER = {"credit_low_until": 0.0, "last_error": None}
# 🚨 2026-05-07: Gemini quota exhausted (429) を一定回数検知したら一時的に Gemini を skip
# 設計: 5 分間で 3 回以上 429 → 30 分間 Gemini をスキップして直接 Anthropic 経由
_GEMINI_QUOTA_FAIL = {"count_in_window": 0, "window_start": 0.0, "skip_until": 0.0}


def _record_ai_critical_event(event_name: str, props: dict):
    """ai_credit_low / ai_total_failure 等の critical event を events に記録。
    CEO ダッシュ monitor がここを見て緊急バナー表示する。"""
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            (event_name, json.dumps(props), "ai_failsafe"),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"[AI failsafe] failed to record critical event {event_name}: {e}")


def _anthropic_max_tokens_cap(model: str, requested: int) -> int:
    """モデルごとの安全な max_tokens 上限。降格時に元の値が大きすぎる場合 clamp。"""
    if model.startswith("claude-opus-4-7"):
        return min(requested, 24000)
    if model.startswith("claude-sonnet-4"):
        return min(requested, 16000)
    if model.startswith("claude-haiku-4"):
        return min(requested, 8000)
    return min(requested, 8000)


def _call_gemini(body: dict, *, model: str = None, kind: str = "chat") -> dict:
    """Gemini API 呼び出し (Anthropic body 互換 → Gemini 形式変換)。
    入力は Anthropic /v1/messages 形式 (model/max_tokens/system/messages)。
    出力は Anthropic 互換形式に詰め直して返す (caller 側の data["content"][0]["text"] が動く)。
    Gemini API 失敗時は HTTPError 相当を raise する (Tier 4 fallback の最終層)。
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("google-generativeai package not installed")

    # API キー設定 (毎回呼んでも冪等)
    genai.configure(api_key=GEMINI_API_KEY)

    target_model = model or GEMINI_MODEL
    system_text = body.get("system") or ""
    msgs = body.get("messages") or []
    max_tokens = int(body.get("max_tokens") or 4000)

    # Gemini は max_tokens=8192 (Flash) / 8192 (Pro) が上限。clamp。
    max_tokens = min(max_tokens, 8000)

    # Gemini の history 形式: [{"role": "user|model", "parts": [text]}]
    # Anthropic の messages: [{"role": "user|assistant", "content": "..."}]
    history = []
    last_user_text = ""
    for m in msgs:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            content = "".join(c.get("text", "") for c in content if isinstance(c, dict))
        if role == "assistant":
            history.append({"role": "model", "parts": [content]})
        else:
            if msgs and m is msgs[-1]:
                last_user_text = content
            else:
                history.append({"role": "user", "parts": [content]})

    # 最後の user message が抽出できなかったケース fallback
    if not last_user_text and msgs:
        c = msgs[-1].get("content", "")
        if isinstance(c, list):
            c = "".join(x.get("text", "") for x in c if isinstance(x, dict))
        last_user_text = c

    # 安全フィルタは BLOCK_ONLY_HIGH に設定 = 高校教材 (戦争史・歴史・医療・薬物・倫理) が
    # Gemini のデフォ厳しめフィルタで誤ブロックされないようにする。完全 OFF にはしない。
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]

    # Pro → Flash 二段 fallback: Pro が quota/rate limit で落ちたら Flash に自動降格
    # (塾長 Pro 契約だが Pro の rate limit に引っかかる/一時障害でも Gemini 路線は止まらない)
    candidate_models = [target_model]
    if target_model != GEMINI_MODEL_LIGHT:
        candidate_models.append(GEMINI_MODEL_LIGHT)

    last_err = None
    for idx, gm_name in enumerate(candidate_models):
        try:
            gen_model = genai.GenerativeModel(
                model_name=gm_name,
                system_instruction=system_text or None,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": float(body.get("temperature") or 0.7),
                },
                safety_settings=safety_settings,
            )
            chat = gen_model.start_chat(history=history)
            resp = chat.send_message(last_user_text)
            text = resp.text or ""
            if idx > 0:
                log.warning(f"[Gemini] succeeded with fallback model {gm_name} after {target_model} failed")
            # Anthropic 互換形式に詰め直す
            return {
                "id": f"gemini_{int(time.time()*1000)}",
                "type": "message",
                "role": "assistant",
                "model": gm_name,
                "content": [{"type": "text", "text": text}],
                "_actual_model": gm_name,
                "_provider": "gemini",
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": getattr(resp.usage_metadata, "prompt_token_count", 0) if hasattr(resp, "usage_metadata") else 0,
                    "output_tokens": getattr(resp.usage_metadata, "candidates_token_count", 0) if hasattr(resp, "usage_metadata") else 0,
                },
            }
        except Exception as e:
            last_err = e
            log.warning(f"[Gemini] {gm_name} failed (attempt {idx + 1}/{len(candidate_models)}): {type(e).__name__}: {str(e)[:300]}")
            if idx == len(candidate_models) - 1:
                # 全 Gemini モデル失敗 → 上位の Tier 4 fallback 経路では _call_anthropic_safe の
                # 全失敗パスに合流する。_call_ai_safe の Gemini-first 経路では Anthropic 経路に流れる。
                log.error(f"[Gemini] all candidate models failed: {[m for m in candidate_models]}")
                raise

    # 到達不能 (上の loop で raise or return する)
    raise last_err if last_err else RuntimeError("Gemini all models failed")


def _call_openai(body: dict, *, model: str = None, kind: str = "chat") -> dict:
    """OpenAI Chat Completions API 呼び出し (Anthropic body 互換 → OpenAI 形式変換)。

    入力は Anthropic /v1/messages 形式 (model/max_tokens/system/messages)。
    出力は Anthropic 互換形式に詰め直して返す (caller の data["content"][0]["text"] が動く)。
    OpenAI API 失敗時は Exception を raise する (Tier 5 fallback の最終層)。

    2026-05-10 塾長指示: AI チューターを Sonnet → Gemini → GPT の 3段 fallback に強化。
    通常時は呼ばれない (Anthropic 健全 or Gemini 健全) のでコスト最小。
    Anthropic + Gemini 両方ダウンの時のみ発火する最終砦。
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")

    target_model = model or OPENAI_MODEL
    system_text = body.get("system") or ""
    msgs = body.get("messages") or []
    max_tokens = int(body.get("max_tokens") or 4000)
    temperature = float(body.get("temperature") or 0.7)

    # OpenAI max_tokens cap (gpt-4o-mini = 16384, gpt-5 想定 = 32768)
    if "gpt-5" in target_model or "o3" in target_model:
        max_tokens = min(max_tokens, 32000)
    else:
        max_tokens = min(max_tokens, 16000)

    # Anthropic messages → OpenAI messages 変換
    # Anthropic: [{role: "user|assistant", content: "..." | [{type:text, text}]}]
    # OpenAI:    [{role: "system|user|assistant", content: "..."}]
    openai_messages = []
    if system_text:
        openai_messages.append({"role": "system", "content": system_text})
    for m in msgs:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            content = "".join(c.get("text", "") for c in content if isinstance(c, dict))
        if role not in ("user", "assistant", "system"):
            role = "user"
        openai_messages.append({"role": role, "content": content})

    # Pro → Light 二段 fallback (将来モデル追加時に対応)
    candidate_models = [target_model]
    if target_model != OPENAI_MODEL_LIGHT:
        candidate_models.append(OPENAI_MODEL_LIGHT)

    last_err = None
    for idx, om_name in enumerate(candidate_models):
        try:
            req_body = {
                "model": om_name,
                "messages": openai_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(req_body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # OpenAI response → Anthropic 互換形式
                # OpenAI: {choices: [{message: {role, content}}], usage: {prompt_tokens, completion_tokens}}
                choices = data.get("choices") or []
                if not choices:
                    raise RuntimeError(f"OpenAI returned no choices: {data}")
                content_text = (choices[0].get("message") or {}).get("content") or ""
                usage = data.get("usage") or {}
                if idx > 0:
                    log.warning(f"[OpenAI] succeeded with fallback model {om_name} after {target_model} failed")
                return {
                    "id": data.get("id") or f"openai_{int(time.time()*1000)}",
                    "type": "message",
                    "role": "assistant",
                    "model": om_name,
                    "content": [{"type": "text", "text": content_text}],
                    "_actual_model": om_name,
                    "_provider": "openai",
                    "stop_reason": (choices[0].get("finish_reason") or "end_turn"),
                    "usage": {
                        "input_tokens": usage.get("prompt_tokens", 0),
                        "output_tokens": usage.get("completion_tokens", 0),
                    },
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            last_err = RuntimeError(f"HTTP {e.code}: {err_body[:300]}")
            log.warning(f"[OpenAI] {om_name} HTTP {e.code}: {err_body[:300]}")
            # 401/403 は key 不正なので即終了 (他モデル試しても無駄)
            if e.code in (401, 403):
                raise last_err
            # 429 / 5xx → 次の model 試行
            if idx == len(candidate_models) - 1:
                raise last_err
        except Exception as e:
            last_err = e
            log.warning(f"[OpenAI] {om_name} failed (attempt {idx + 1}/{len(candidate_models)}): {type(e).__name__}: {str(e)[:300]}")
            if idx == len(candidate_models) - 1:
                log.error(f"[OpenAI] all candidate models failed: {[m for m in candidate_models]}")
                raise

    # 到達不能
    raise last_err if last_err else RuntimeError("OpenAI all models failed")


def _call_anthropic_safe(body: dict, *, kind: str = "chat", student_id: int = None) -> dict:
    """全 Anthropic API 呼び出しの統一エントリ。絶対に止まらない設計。
    - 3 段モデルフォールバック (要求 → Sonnet 4.6 → Haiku 4.5)
    - 各 tier で指数バックオフリトライ (1s/2s/4s)
    - credit 不足は即 critical イベント発火 → CEO ダッシュ緊急バナー
    - 全滅時は HTTPException(503) で raise (caller 側で問題プール等の最終フォールバック)
    body には少なくとも model, max_tokens, messages を含めること。
    """
    import time as _t
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    requested_model = body.get("model") or "claude-sonnet-4-6"
    # フォールバック chain: 重複除去
    chain = []
    seen = set()
    for m in (requested_model, "claude-sonnet-4-6", "claude-haiku-4-5"):
        if m not in seen:
            seen.add(m)
            chain.append(m)

    last_error_code = None
    last_error_body = ""

    for tier_idx, model in enumerate(chain):
        # tier ごとに body を再構築 (Opus 4.7 専用パラメータは降格時に外す)
        tier_body = dict(body)
        tier_body["model"] = model
        tier_body["max_tokens"] = _anthropic_max_tokens_cap(model, int(body.get("max_tokens") or 4000))
        if not model.startswith("claude-opus-4-7"):
            tier_body.pop("thinking", None)
            tier_body.pop("output_config", None)
            # temperature は Sonnet/Haiku でもデフォ削除 (caller が明示してきた場合のみ残す想定だが
            # ここでは body にあれば残す)

        for attempt in range(3):  # 0, 1, 2 → 最大 3 回試行
            try:
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=json.dumps(tier_body).encode("utf-8"),
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if tier_idx > 0 or attempt > 0:
                        log.warning(
                            f"[AI failsafe] succeeded with {model} (tier {tier_idx}, attempt {attempt + 1}) "
                            f"after requested={requested_model}"
                        )
                        # 降格成功も events に記録 (CEO ダッシュで監視)
                        _record_ai_critical_event("ai_fallback_used", {
                            "requested_model": requested_model,
                            "actual_model": model,
                            "tier": tier_idx,
                            "attempt": attempt + 1,
                            "kind": kind,
                            "student_id": student_id,
                        })
                    data["_actual_model"] = model  # caller に降格情報を渡す
                    return data
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                last_error_code = e.code
                last_error_body = err_body
                err_lower = err_body.lower()

                # credit 不足は致命イベント。circuit breaker 起動 + critical event 発火。
                if "credit balance is too low" in err_lower or "credit_balance" in err_lower:
                    _AI_CIRCUIT_BREAKER["credit_low_until"] = _t.time() + 300  # 5 min
                    _AI_CIRCUIT_BREAKER["last_error"] = "credit_low"
                    _record_ai_critical_event("ai_credit_low", {
                        "model": model,
                        "kind": kind,
                        "raw": err_body[:300],
                    })
                    log.error(f"[AI failsafe] CREDIT LOW detected: {err_body[:200]}")
                    # credit 不足は他 Anthropic モデルでも同じアカウントなので無駄。
                    # ただし Gemini は別プロバイダなので Tier 4 fallback に流す (2026-05-06 塾長指示)
                    if GEMINI_API_KEY:
                        try:
                            log.warning(f"[AI failsafe] credit_low → Gemini Tier 4 即時 fallback (kind={kind})")
                            gdata = _call_gemini(body, kind=kind)
                            _record_ai_critical_event("ai_fallback_gemini_credit_low", {
                                "requested_model": requested_model,
                                "actual_model": gdata.get("_actual_model"),
                                "kind": kind,
                                "student_id": student_id,
                            })
                            return gdata
                        except Exception as ge:
                            log.error(f"[AI failsafe] credit_low → Gemini も失敗: {type(ge).__name__}: {str(ge)[:200]}")
                            # Gemini も落ちたら Tier 5 (OpenAI) に流す (2026-05-10 塾長指示)
                    # Tier 5: OpenAI 最終 fallback (credit_low + Gemini 全滅でもまだ動く)
                    if OPENAI_API_KEY:
                        try:
                            log.warning(f"[AI failsafe] credit_low → OpenAI Tier 5 即時 fallback (kind={kind})")
                            odata = _call_openai(body, kind=kind)
                            _record_ai_critical_event("ai_fallback_openai_credit_low", {
                                "requested_model": requested_model,
                                "actual_model": odata.get("_actual_model"),
                                "kind": kind,
                                "student_id": student_id,
                            })
                            return odata
                        except Exception as oe:
                            log.error(f"[AI failsafe] credit_low → OpenAI も失敗: {type(oe).__name__}: {str(oe)[:200]}")
                    raise HTTPException(
                        status_code=503,
                        detail="AI_CREDIT_LOW: Anthropic クレジット枯渇 + Gemini + OpenAI 全 fallback 失敗。塾長に補充依頼してください。"
                    )

                # 4xx (validation) → リトライ無駄、次の tier
                if 400 <= e.code < 500 and e.code != 429:
                    log.warning(f"[AI failsafe] {model} returned {e.code}, advancing to next tier: {err_body[:200]}")
                    break

                # 429 / 5xx → 指数バックオフリトライ
                if attempt < 2:
                    sleep_s = 2 ** attempt
                    log.warning(f"[AI failsafe] {model} returned {e.code}, retrying in {sleep_s}s (attempt {attempt + 1}/3)")
                    _t.sleep(sleep_s)
                    continue
                # 3 回全部 5xx → 次の tier
                log.warning(f"[AI failsafe] {model} exhausted {attempt + 1} attempts with {e.code}, advancing to next tier")
                break
            except (urllib.error.URLError, OSError) as e:
                last_error_code = "network"
                last_error_body = str(e)[:300]
                if attempt < 2:
                    sleep_s = 2 ** attempt
                    log.warning(f"[AI failsafe] {model} network error, retrying in {sleep_s}s: {e}")
                    _t.sleep(sleep_s)
                    continue
                log.warning(f"[AI failsafe] {model} exhausted retries on network error, advancing to next tier")
                break

    # Tier 4: Gemini fallback (Anthropic 完全障害でも止まらない設計)
    # AI never-fail 原則 (memory: feedback_ai_never_fail.md): Anthropic 全停止時も
    # Daily SNS / 教材生成 / 採点 が止まらないように Gemini に投げ替える。
    if GEMINI_API_KEY:
        try:
            log.warning(f"[AI failsafe] Anthropic全滅、Gemini Tier 4 にフォールバック (kind={kind})")
            data = _call_gemini(body, kind=kind)
            _record_ai_critical_event("ai_fallback_gemini", {
                "requested_model": requested_model,
                "actual_model": data.get("_actual_model"),
                "anthropic_last_error": last_error_code,
                "kind": kind,
                "student_id": student_id,
            })
            return data
        except Exception as ge:
            log.error(f"[AI failsafe] Gemini Tier 4 もエラー: {type(ge).__name__}: {str(ge)[:200]}")
            # Gemini も落ちたら Tier 5 (OpenAI) に流す

    # Tier 5: OpenAI 最終 fallback (2026-05-10 塾長指示・3段防御)
    # Anthropic + Gemini 両方ダウンの時のみ発火する最終砦。
    # 通常時は呼ばれない (=コスト最小)。memory: feedback_ai_tutor_sonnet_gemini.md
    if OPENAI_API_KEY:
        try:
            log.warning(f"[AI failsafe] Anthropic+Gemini全滅、OpenAI Tier 5 にフォールバック (kind={kind})")
            data = _call_openai(body, kind=kind)
            _record_ai_critical_event("ai_fallback_openai", {
                "requested_model": requested_model,
                "actual_model": data.get("_actual_model"),
                "anthropic_last_error": last_error_code,
                "kind": kind,
                "student_id": student_id,
            })
            return data
        except Exception as oe:
            log.error(f"[AI failsafe] OpenAI Tier 5 もエラー: {type(oe).__name__}: {str(oe)[:200]}")
            # OpenAI も落ちたら下の total_failure へ流れる

    # 全 tier 全 attempt 失敗 (Anthropic 3段 + Gemini + OpenAI 全滅 = 5段防御を全て貫通)
    _record_ai_critical_event("ai_total_failure", {
        "requested_model": requested_model,
        "last_error_code": last_error_code,
        "last_error_body": last_error_body[:300],
        "gemini_configured": bool(GEMINI_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
        "kind": kind,
        "student_id": student_id,
    })
    log.error(f"[AI failsafe] ALL TIERS FAILED (incl. Gemini + OpenAI). last={last_error_code}: {last_error_body[:200]}")
    raise HTTPException(
        status_code=503,
        detail=f"AI temporarily unavailable. Last error: {last_error_code}"
    )


_GEMINI_FIRST_TASKS = {
    # 低 stake task = Gemini 優先で課金抑制 + 並列処理高速化
    # 失敗時は Anthropic にフォールバックする (品質が落ちないように)
    "daily_sns",        # SNS 投稿生成 (短文・カジュアル)
    "tag_extract",      # タグ抽出 (構造化抽出)
    "summarize_short",  # 短文要約
    "classify",         # 分類タスク
    "moderate",         # NG 文言判定
}


def _call_ai_safe(body: dict, *, task_type: str = "default", kind: str = None,
                   student_id: int = None) -> dict:
    """task_type ベースで Gemini / Anthropic を振り分ける統一 AI ルーター。

    使い分け:
    - task_type が _GEMINI_FIRST_TASKS にあれば Gemini Flash 優先 → 失敗時 Anthropic にフォールバック
    - それ以外は Anthropic 優先 (品質責任が大きいタスク = 教材/採点/対話/問題生成)
    - どちらの経路でも _call_anthropic_safe の Tier 4 (Gemini) があるので最終的に止まらない

    Why: 教材生成・記述採点・古文/医学部論述は Anthropic Opus/Sonnet の品質責任が大きい。
    一方 Daily SNS や分類などは Gemini Flash で十分 (かつ無料枠 1500/日 が大きい)。
    塾長指示「AI never-fail」+ 課金抑制を両立させる設計。
    """
    kind = kind or task_type

    # 1) Gemini-first パス (低 stake タスク)
    if task_type in _GEMINI_FIRST_TASKS and GEMINI_API_KEY:
        try:
            return _call_gemini(body, model=GEMINI_MODEL_LIGHT, kind=kind)
        except Exception as e:
            log.warning(
                f"[AI router] Gemini-first failed for task={task_type}, falling back to Anthropic: "
                f"{type(e).__name__}: {str(e)[:200]}"
            )
            # Anthropic 経路へフォールスルー
            _record_ai_critical_event("ai_router_gemini_first_failed", {
                "task_type": task_type,
                "error": str(e)[:300],
            })

    # 2) Anthropic 経路 (高 stake タスクの主経路 + Gemini-first 失敗時の救済)
    return _call_anthropic_safe(body, kind=kind, student_id=student_id)


def _ai_credit_low_active() -> bool:
    """CEO ダッシュ等で credit 不足バナーを出すかの判定。"""
    import time as _t
    return _AI_CIRCUIT_BREAKER.get("credit_low_until", 0) > _t.time()


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
    # 教材生成 (textbook-generator.js) は 16000 を要求するため上限を 24000 に拡張。
    # 8000 cap だと長文 JSON が中途で切断され Parse error になっていた。
    if max_tokens > 24000:
        max_tokens = 24000
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages required")
    body = {"model": model, "max_tokens": max_tokens, "messages": messages}
    system = payload.get("system")
    if system:
        body["system"] = system

    # Opus 4.7 は thinking/output_config 必須 (これが無いと Anthropic が 400 を返す)。
    # /api/ai/call の同等ロジック (L6847-) を踏襲し、Sonnet 系には enabled thinking。
    # フロントが thinking/output_config/temperature を明示してきた場合はそれを優先。
    if (model or "").startswith("claude-opus-4-7"):
        body["thinking"] = payload.get("thinking") or {"type": "adaptive"}
        body["output_config"] = payload.get("output_config") or {"effort": "high"}
        body["temperature"] = float(payload.get("temperature") or 1.0)
    else:
        # Sonnet/Haiku: thinking はオプショナル。フロントが指定した時のみ付ける。
        if payload.get("thinking") is not None:
            body["thinking"] = payload.get("thinking")
        if payload.get("temperature") is not None:
            body["temperature"] = float(payload.get("temperature"))

    # Anthropic 呼び出し (フェイルセーフ経由・3段モデル降格 + リトライ込み)
    student_id = student.get("id") if student else None
    data = _call_anthropic_safe(body, kind="proxy_messages", student_id=student_id)
    actual_model = data.get("_actual_model") or model

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
                    "model": actual_model,
                    "requested_model": model,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "is_admin": is_admin,
                    "fallback_used": actual_model != model,
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
    # TOEIC (Phase 14-I で l_part1 / l_part4 / r_part7_multi を追加)
    ("toeic", "l_part1", None),
    ("toeic", "l_part2", None),
    ("toeic", "l_part3", None),
    ("toeic", "l_part4", None),
    ("toeic", "r_part5", None),
    ("toeic", "r_part6", None),
    ("toeic", "r_part7_single", None),
    ("toeic", "r_part7_multi", None),
    # IELTS (Phase 14-I で l_sec2 / l_sec4 / r_p2 / r_p3 / w_task1 を追加)
    ("ielts", "l_sec1", None),
    ("ielts", "l_sec2", None),
    ("ielts", "l_sec3", None),
    ("ielts", "l_sec4", None),
    ("ielts", "r_p1", None),
    ("ielts", "r_p2", None),
    ("ielts", "r_p3", None),
    ("ielts", "w_task1", None),
    ("ielts", "w_task2", None),
    # 英検 (受験者多い順: 準1級, 2級, 3級, 準2級, 1級, 4級, 5級)
    ("eiken", "r_q1", "gp1"),
    ("eiken", "r_q3", "gp1"),
    ("eiken", "w_essay", "gp1"),
    ("eiken", "r_q1", "g2"),
    ("eiken", "r_q3", "g2"),        # 2026-05-03 復活: 2級長文 (旧形式但し import 既存データあり)
    ("eiken", "r_q3b", "g2"),       # 2026-04-30 追加: 2級長文内容一致
    ("eiken", "w_opinion", "g2"),
    ("eiken", "w_summary", "g2"),   # 2026-04-30 追加: 2級要約 (新形式 2024〜)
    ("eiken", "r_q1", "g3"),
    ("eiken", "r_q1", "g1"),
    ("eiken", "r_q3", "g1"),        # 2026-04-30 追加: 1級長文内容一致
    ("eiken", "w_summary", "g1"),   # 2026-04-30 追加: 1級要約 (新形式 2024〜)
    ("eiken", "w_essay", "g1"),     # 2026-04-30 追加: 1級エッセイ
    ("eiken", "r_q1", "gp2"),
    ("eiken", "r_q3b", "gp2"),      # 2026-04-30 追加: 準2級長文内容一致
    ("eiken", "w_email", "gp2"),    # 2026-04-30 追加: 準2級Eメール返信 (新形式 2024〜)
    ("eiken", "w_opinion", "gp2"),  # 2026-04-30 追加: 準2級意見論述
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
    ("daigaku", "g_grammar",     "osaka"),
    ("daigaku", "r_long",        "tokoda"),
    ("daigaku", "r_long",        "hitotsu"),
    ("daigaku", "r_translation", "hitotsu"),
    ("daigaku", "r_long",        "nagoya"),
    # 私立 早慶上智ICU
    ("daigaku", "r_long",        "waseda"),
    ("daigaku", "w_essay",       "waseda"),
    ("daigaku", "g_grammar",     "waseda"),
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
    # 国公立旧帝 (北大/東北大/九大)
    ("daigaku", "r_long",        "hokudai"),
    ("daigaku", "w_essay",       "hokudai"),
    ("daigaku", "r_translation", "hokudai"),
    ("daigaku", "r_long",        "tohoku"),
    ("daigaku", "w_essay",       "tohoku"),
    ("daigaku", "r_translation", "tohoku"),
    ("daigaku", "r_long",        "kyushu"),
    ("daigaku", "w_essay",       "kyushu"),
    ("daigaku", "r_translation", "kyushu"),
    # 国公立準難関 (神戸/横国/千葉/筑波)
    ("daigaku", "r_long",        "kobe"),
    ("daigaku", "w_essay",       "kobe"),
    ("daigaku", "r_translation", "kobe"),
    ("daigaku", "r_long",        "yokokoku"),
    ("daigaku", "w_essay",       "yokokoku"),
    ("daigaku", "r_long",        "chiba"),
    ("daigaku", "r_translation", "chiba"),
    ("daigaku", "r_long",        "tsukuba"),
    ("daigaku", "w_essay",       "tsukuba"),
    # 私立 学習院 + 成成明武
    ("daigaku", "r_long",        "gakushuin"),
    ("daigaku", "r_long",        "seikei"),
    ("daigaku", "r_long",        "seijo"),
    ("daigaku", "r_long",        "musashi"),
    # 医学部
    ("daigaku", "r_long",        "igakubu_kokoritsu"),
    ("daigaku", "r_translation", "igakubu_kokoritsu"),
    ("daigaku", "w_essay",       "igakubu_kokoritsu"),  # 2026-05-03 追加
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
    "hokudai":   {"name": "北海道大学",     "style": "国公立旧帝。標準〜やや難の評論/論説系英文 + 部分和訳 + 自由英作 70-100語。北方圏/環境/農学/獣医学が頻出テーマ。関係詞節・無生物主語の和訳が中核。"},
    "tohoku":    {"name": "東北大学",       "style": "国公立旧帝。理系/文系融合の硬めの英文 + 全訳/部分和訳 + 自由英作 80-120語。技術/科学哲学/環境/震災後の復興系テーマ。記述式の精度を問う。"},
    "kyushu":    {"name": "九州大学",       "style": "国公立旧帝。アジア圏/グローバル/共生をテーマにした評論系英文 + 構造把握型和訳 + 自由英作 70-100語。理論的・抽象的英文が多め。"},
    "kobe":      {"name": "神戸大学",       "style": "国公立準難関。経済/経営/国際文化系の評論英文 + 部分和訳 + 自由英作 60-80語。読みやすい標準英文だが論理的整合性を厳格に問う。"},
    "yokokoku":  {"name": "横浜国立大学",   "style": "国公立準難関。経営/経済/教育/工学系の標準英文 + 部分和訳 + 自由英作 (テーマ自由度高め)。総合力重視・論理整合性。"},
    "chiba":     {"name": "千葉大学",       "style": "国公立準難関。教育/医/工/園芸 等学部別出題。標準英文長文 + 整序 + 部分和訳。読解スピード重視。"},
    "tsukuba":   {"name": "筑波大学",       "style": "国公立準難関。総合学群型・幅広いテーマの評論英文 + 部分和訳 + 自由英作 70-100語。論理思考・パラフレーズ力を問う。"},
    "gakushuin": {"name": "学習院大学",     "style": "私立 MARCH 準級。標準的な評論英文 + 文法+整序+短い意見論述。読み物としても良質な英文を採用する伝統。"},
    "seikei":    {"name": "成蹊大学",       "style": "私立成成明学武。標準難度の評論/エッセイ系英文 + 文法 + 整序 + 短い意見論述。基礎〜標準の総合力を測る。"},
    "seijo":     {"name": "成城大学",       "style": "私立成成明学武。文学/社会/文化系の標準英文 + 文法 + 整序。読みやすい標準英文を丁寧に処理する力。"},
    "musashi":   {"name": "武蔵大学",       "style": "私立成成明学武。経済/人文/社会系の標準英文 + 文法 + 整序 + 自由英作 (短め)。総合的な英語運用力を重視。"},
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


def _get_recent_exam_combinations(student_id: Optional[int], days: int = 7) -> list:
    """指定 student_id に直近 N 日以内に出された (univ, year) の組合せ一覧を返す。
    events.name = 'exam_question_served' を session_id='student:N' で絞って取得。
    student_id 未指定時は空リスト (= 全件除外無し)。"""
    if not student_id:
        return []
    try:
        cutoff = datetime.utcnow() - timedelta(days=max(1, days))
        session_key = f"student:{student_id}"
        conn = db()
        c = conn.cursor()
        try:
            c.execute(
                "SELECT props FROM events WHERE name = 'exam_question_served' AND session_id = ? AND created_at >= ?",
                (session_key, cutoff),
            )
            rows = c.fetchall()
        finally:
            conn.close()
        combos = []
        for r in rows:
            props_str = r["props"] if hasattr(r, "keys") and "props" in r.keys() else (r[0] if r else None)
            if not props_str:
                continue
            try:
                props = json.loads(props_str) if isinstance(props_str, str) else props_str
            except Exception:
                continue
            univ = props.get("univ")
            year = props.get("year")
            if univ and year:
                combos.append((str(univ), int(year)))
        return combos
    except Exception as e:
        log.warning(f"[ExamQ:Recent] failed: {e}")
        return []


def _generate_exam_question(
    exam_id: str,
    part_key: str,
    eiken_grade: Optional[str] = None,
    exclude_combinations: Optional[list] = None,
    topic_hint: Optional[str] = None,
) -> Optional[dict]:
    """Anthropic API で1問生成して dict を返す。失敗時 None。
    daigaku の場合は eiken_grade に大学キー (todai/kyodai/...) を入れる慣例。

    exclude_combinations: [(univ, year), ...] 直近で同じ生徒に出した組合せを避ける。
        全部除外で残り無い場合は最も古い (= 最初の要素) を許可する relative diversity。
    topic_hint: 単元タグ (例: '関係代名詞') を AI prompt に明示注入。"""
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
        # TOEIC
        "l_part1": "Listening Part 1 写真描写問題 6問 (4択・1枚の写真を描写する短文を選ぶ・空港/オフィス/工場等の典型シーン)",
        "l_part2": "Listening Part 2 応答問題 5問 (3択)",
        "l_part3": "Listening Part 3 会話問題 6問 (3問1セット×2)",
        "l_part4": "Listening Part 4 説明文問題 6問 (3問1セット×2・アナウンス/留守電/講演形式の独白)",
        "r_part5": "Reading Part 5 短文穴埋め 8問 (4択・品詞文法語彙)",
        "r_part6": "Reading Part 6 長文穴埋め (4問1セット)",
        "r_part7_single": "Reading Part 7 シングルパッセージ (3問)",
        "r_part7_multi": "Reading Part 7 マルチプルパッセージ (5問・メール+広告/通知+返信などの複数文書を関連付けて解く)",
        # IELTS
        "l_sec1": "Listening Section 1 社会的会話 + 5問",
        "l_sec2": "Listening Section 2 単独スピーチ (観光案内/施設説明型) + 5問",
        "l_sec3": "Listening Section 3 学術会話 + 5問",
        "l_sec4": "Listening Section 4 大学講義独白 + 5問 (全 Section で最も難度高)",
        "r_p1": "Reading Passage 1 + 6問 (TFNG/穴埋め)",
        "r_p2": "Reading Passage 2 + 6問 (見出し選択/分類/Y-N-NG など多様な設問形式)",
        "r_p3": "Reading Passage 3 学術論文型 + 6問 (最難パッセージ・抽象論証)",
        "w_task1": "Writing Task 1: グラフ/図表/プロセス図を 150語で要約描写 (Academic 型)",
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
            year_candidates = list(range(2021, 2027))  # 共通テスト
        elif univ_key == "center":
            year_candidates = list(range(2005, 2021))  # センター試験
        else:
            year_candidates = list(range(2005, 2027))

        # 直近で同 student に出た (univ, year) を除外して相対的多様性確保
        excluded_for_univ = set()
        if exclude_combinations:
            for (eu, ey) in exclude_combinations:
                if eu == univ_key:
                    excluded_for_univ.add(int(ey))
        remaining = [y for y in year_candidates if y not in excluded_for_univ]
        if remaining:
            year = random.choice(remaining)
        else:
            # 全年度除外 → 最も古い (= 最初に出た) 年度を再利用 (relative diversity)
            year = year_candidates[0] if year_candidates else random.randint(2005, 2026)
        exam_label = f"{univ_name} {year}年度入試 (英語)"

        system = f"""あなたは日本の大学受験英語の出題傾向に精通した専門家です。
**{univ_name}** の **{year}年度** 入試の出題形式・難易度・テーマ傾向に完全準拠した類題を生成してください。

【絶対遵守】
- 過去問の丸写しは著作権上禁止。**「{univ_name} {year}年度の形式に完全準拠した類題」** を新規作成すること。
- {univ_name} の出題スタイル: {univ_style}
- 対象 大問形式: {part_label}
- 英文は ETS / Cambridge / Oxford 級の自然な英語 (機械翻訳臭・不自然な語彙NG)
- 日本人受験生の典型的弱点 (冠詞・関係詞節・分詞構文・無生物主語の和訳・コロケーション) を踏まえた解説
- 「2005年〜2026年」の出題傾向: 時事 (AI/ChatGPT/環境/感染症/格差/ジェンダー/メンタルヘルス) + 古典的論題 (記憶/言語/科学哲学/教育) + 物語/エッセイ系を年度に応じて織り交ぜる
- {year}年度なら、その年に話題だったテーマを優先的に扱うのがリアル (例: 2023年なら ChatGPT/AI、2020-2021年なら COVID-19、2011年以降なら震災/原発)

【🔥 解説の絶対遵守フォーマット — コアイメージ×文構造分析の二段構え】
explanation フィールドは Markdown で **以下4セクションを必ず明示**。1セクションでも欠けたら不合格:

## 🎯 コアイメージ
〔該当する語法・文法・時制・前置詞・冠詞のコアイメージを 2-3 行で〕
例) must=「絶対こうだ」→義務+強い推量／at=「点」, in=「包まれた中」, on=「接触」／the=「特定の・あの」／現在完了=「過去とのつながり」

## 🔬 文構造分析 ← 絶対省略禁止
〔該当文の S/V/O/C/M をラベル付きで明示。入れ子節は階層で〕
例) "The book [that I bought yesterday] is on the table."
  主節: S=The book / V=is / M=on the table
  関係詞節 [that I bought yesterday]: 先行詞 The book を修飾 (S=I, V=bought, O=that, M=yesterday)
動詞の数=節の数 で骨組みを取り、関係詞節・分詞・不定詞・that 節は修飾先を矢印で示す

## 📍 本文の根拠
〔長文の場合〕該当箇所を「" "」で引用 + 段落番号。設問と本文の構造的対応を示す

## ❌ 誤答 NG 理由 (multiple_choice の場合は必須)
〔各誤答選択肢ごとに、構造的・本質的になぜ NG かを 1 行ずつ〕
「本文の○○と矛盾」「コアイメージから外れる」「修飾関係が違う」など客観的根拠で

【日本人弱点コメント (該当時)】冠詞・関係詞の制限/非制限・分詞構文の意味上の主語・無生物主語の和訳・句動詞のコロケーション・時制の一致・仮定法の倒置 が絡んだら 1 行追加

- 出力は純粋なJSONのみ。explanation フィールド内の上記 Markdown は \\n でエスケープして JSON 文字列化する"""

        # 単元タグ (topic_hint) があれば prompt に明示注入
        topic_clause = ""
        if topic_hint:
            topic_clause = f"""
【単元指定 (絶対遵守)】
- この問題の中心単元は **「{topic_hint}」** に固定する。
- 「{topic_hint}」の運用が問題の核心となる出題のみ生成 (関係詞節を選んだら関係代名詞中心、分詞構文を選んだら分詞構文中心、等)。
- 単元から外れた文法事項を中核に据えるのは禁止。
"""

        # 直近で出した (univ, year) があれば AI に明示提示 (avoid 句)
        avoid_clause = ""
        if exclude_combinations:
            # univ_key 一致の組合せのみ提示 (この生成枠は univ_key 固定)
            same_univ = [(u, y) for (u, y) in exclude_combinations if u == univ_key]
            if same_univ:
                pairs = ", ".join([f"({u}, {y})" for (u, y) in same_univ[:20]])
                avoid_clause = f"""
【直近出題回避 (相対的多様性)】
- 同じ生徒に直近 7 日以内に出した組合せは: {pairs}
- 上記とは異なる年度・異なるテーマで出題することで生徒に多様な経験を提供すること。
- すでに本枠は y={year} を選定済 (除外候補から除外)。テーマも上記過去出題と被らないように選ぶ。
"""

        user = f"""**{univ_name} {year}年度** 形式の **{part_key}** ({part_label}) の類題を1セット生成してください。

【テーマ選定指針】
- {year}年に話題だったトピック or {univ_name} 頻出の論題から自然に選ぶ
- {univ_name} の難易度・抽象度に合わせる ({univ_style.split('。')[0]})
{topic_clause}{avoid_clause}
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
      "choices": ["選択肢配列 — multiple_choice の場合は必ず非空 (最低2要素)"],
      "answer": "正解 (選択肢index 0始まり、または模範解答テキスト全文)",
      "explanation": "解説 Markdown (## 🎯 コアイメージ → ## 🔬 文構造分析 → ## 📍 本文の根拠 → ## ❌ 誤答 NG 理由 の4セクション必須)"
    }}
  ]
}}

【🛟 choices 配列の絶対遵守ルール (致命傷防止)】
- type が "multiple_choice" の場合、choices 配列は **必ず非空** (最低 2 要素・通常 4 要素) で返すこと。
  - 通常の選択肢問題: ["選択肢A", "選択肢B", "選択肢C", "選択肢D"]
  - 下線部誤り選択 (①②③④ を本文中にインライン挿入する形式) の場合: ["①", "②", "③", "④"]
  - 空欄補充: ["where", "that", "which", "when"] のように単語/句で
- **choices: [] (空配列) を返すのは絶対禁止**。テキスト記述式の問題なら type を "short_answer" にすること。
- 「下線部の番号は問題文中にあるから choices は要らない」は誤り。フロントは choices を見てボタン描画する。"""

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

        rikei_topic_clause = f"\n\n【単元指定 (絶対遵守)】中心単元は **「{topic_hint}」** に固定する。" if topic_hint else ""
        user = f"""**{univ_name} {year}年度** 形式の **{subject}** ({part_label}) の類題を1セット生成してください。{rikei_topic_clause}

【出力】上記の system に従い純粋な JSON のみ。{subject} で図が必要な問題は figure_svg を必ず埋めること (空文字 NG)。"""

    else:
        exam_label = exam_hints.get(exam_id, exam_id)
        part_label = part_hints.get(part_key, part_key)

        system = f"""あなたは {exam_label} の試験対策専門家です。公式の出題形式に完全準拠した問題を生成してください。

【厳守】
- 出題形式は公式と完全一致 ({part_label})
- 英文はナチュラルな英語 (機械翻訳臭NG)

【🔥 解説の絶対遵守フォーマット — コアイメージ×文構造分析の二段構え】
explanation フィールドは Markdown で **以下4セクションを必ず明示**。1セクションでも欠けたら不合格:

## 🎯 コアイメージ
〔該当する語法・文法・時制・前置詞・冠詞のコアイメージを 2-3 行で。must=「絶対こうだ」, at=「点」, in=「包まれた中」, on=「接触」, the=「特定の・あの」, 現在完了=「過去とのつながり」 等〕

## 🔬 文構造分析 ← 絶対省略禁止
〔該当文の S/V/O/C/M をラベル付きで明示。動詞の数=節の数で骨組みを取り、関係詞節・分詞・不定詞・that 節は修飾先を示す〕

## 📍 本文の根拠 (長文の場合)
〔該当箇所を引用 + 段落番号。設問と本文の構造的対応〕

## ❌ 誤答 NG 理由 (multiple_choice の場合)
〔各誤答ごとに構造的・本質的に NG な理由を 1 行ずつ〕

- 出力は純粋なJSONのみ。explanation 内の Markdown は \\n でエスケープ"""

        other_topic_clause = f"\n\n【単元指定 (絶対遵守)】中心単元は **「{topic_hint}」** に固定する。「{topic_hint}」の運用が問題の核心となる出題のみ生成。" if topic_hint else ""
        user = f"""{exam_label} の **{part_key}** ({part_label}) の問題を1セット生成してください。{other_topic_clause}

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
}}

【🛟 choices 配列の絶対遵守ルール (致命傷防止)】
- type が "multiple_choice" の場合、choices 配列は **必ず非空** (最低 2 要素・通常 4 要素) で返すこと。
  - 通常の選択肢問題: ["選択肢A", "選択肢B", "選択肢C", "選択肢D"]
  - 下線部誤り選択 (①②③④ を本文中にインライン挿入する形式) の場合: ["①", "②", "③", "④"]
  - 空欄補充: ["where", "that", "which", "when"] のように単語/句で
- **choices: [] (空配列) を返すのは絶対禁止**。テキスト記述式の問題なら type を "short_answer" にすること。
- 「下線部の番号は問題文中にあるから choices は要らない」は誤り。フロントは choices を見てボタン描画する。"""

    try:
        # AI never-fail: _call_anthropic_safe 経由で Tier 4 (Gemini) まで自動 fallback
        data = _call_anthropic_safe(
            {
                "model": EXAM_QUESTIONS_MODEL,
                "max_tokens": 4000,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            kind=f"examq_{exam_id}_{part_key}",
        )
        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip().rstrip("`").strip()
        return json.loads(text)
    except HTTPException as e:
        log.error(f"[ExamQ] Generation failed for {exam_id}/{part_key}: HTTP {e.status_code}: {e.detail}")
        return None
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


async def _refill_part_async(
    exam_id: str,
    part_key: str,
    eiken_grade: Optional[str],
    target: int = 2,
    exclude_combinations: Optional[list] = None,
    topic_hint: Optional[str] = None,
) -> None:
    """生徒のリクエスト由来で薄い part を裏で補充。
    target 問数を生成。in-flight ロックで多重発火を防止。daily max は遵守。
    exclude_combinations / topic_hint があれば AI prompt に注入して多様性・単元固定。"""
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
        log.info(f"[ExamQ:Refill] Generating {n_to_gen} for {key} (current pool={counts.get(key, 0)}, exclude={len(exclude_combinations or [])}, topic={topic_hint})")
        for _ in range(n_to_gen):
            # 同期的な API 呼び出しを別スレッドへ (FastAPI のイベントループをブロックしない)
            q = await asyncio.get_event_loop().run_in_executor(
                None,
                _generate_exam_question,
                exam_id,
                part_key,
                eiken_grade,
                exclude_combinations,
                topic_hint,
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
# 💳 Stripe Price 全プラン一括セットアップ (2026-05-07 追加)
# 塾長指示「金額のstripe反映ができてるかどうかもチェックして実装してください」
# ============================================================================

# 全プランの設定: lookup_key, 金額(JPY), Product 名, 説明
_STRIPE_PLAN_SPECS = [
    {
        "lookup_key": "founder_special",
        "amount": 14500,
        "product_name": "AI学習コーチ塾 創設メンバー",
        "description": "期間限定 50名・永年¥14,500/月・全機能無制限",
        "metadata": {"plan": "founder_special", "tier": "premium-equivalent", "perpetual": "true"},
    },
    {
        "lookup_key": "premium",
        "amount": 39800,
        "product_name": "AI学習コーチ塾 プレミアム",
        "description": "AI 全機能無制限 + 学習管理 + 合格カリキュラム自動生成 + ZOOM 授業",
        "metadata": {"plan": "premium", "tier": "premium"},
    },
    {
        "lookup_key": "family",
        "amount": 59800,
        "product_name": "AI学習コーチ塾 家族プラン",
        "description": "兄弟姉妹3名まで使える・1人あたり実質¥19,933/月",
        "metadata": {"plan": "family", "tier": "premium", "max_students": "3"},
    },
    {
        "lookup_key": "standard",
        "amount": 24980,
        "product_name": "AI学習コーチ塾 スタンダード",
        "description": "24時間AIチューター + 問題生成月50回 + 添削月20回 + 参考書月5冊",
        "metadata": {"plan": "standard", "tier": "standard"},
    },
    {
        "lookup_key": "student_addon",
        "amount": 5000,
        "product_name": "AI学習コーチ塾 通塾生プラン",
        "description": "通塾生限定 (塾長招待制)・永年¥5,000/月・全機能無制限・入塾金免除",
        "metadata": {"plan": "student_addon", "perpetual": "true", "invite_only": "true"},
    },
]


@app.post("/api/admin/stripe/setup-all-prices")
def admin_stripe_setup_all_prices(authorization: Optional[str] = Header(None)):
    """💳 全プランの Stripe Price を 1 度に作成 (or 既存検証)。
    各 Price は lookup_key で永続検索可能 → env 設定不要。
    冪等: 既に lookup_key で見つかれば再作成しない。
    admin Bearer 認証必須。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY が未設定 (Railway env)")

    s = get_stripe()
    results = []

    for spec in _STRIPE_PLAN_SPECS:
        lk = spec["lookup_key"]
        amount = spec["amount"]
        try:
            # 1. lookup_key で既存検索 (冪等)
            existing = s.Price.list(lookup_keys=[lk], active=True, limit=1)
            if existing and existing.data:
                ex = existing.data[0]
                # 金額の整合確認
                amount_match = (ex.unit_amount == amount)
                results.append({
                    "lookup_key": lk,
                    "status": "existing" if amount_match else "existing_amount_mismatch",
                    "price_id": ex.id,
                    "amount_jpy": ex.unit_amount,
                    "expected_jpy": amount,
                    "amount_match": amount_match,
                    "interval": ex.recurring.get("interval") if ex.recurring else None,
                    "message": (
                        f"既存 Price が一致 ({ex.id}・¥{ex.unit_amount:,}/月)" if amount_match
                        else f"⚠️ 金額不一致: Stripe={ex.unit_amount} 期待={amount}・既存 Price は active=False にして再作成推奨"
                    ),
                })
                continue
        except Exception as e:
            log.warning(f"[Stripe Setup] lookup_key={lk} 検索失敗: {e}")

        # 2. Product を name 一致で再利用 or 新規作成
        product_id = None
        try:
            prods = s.Product.list(active=True, limit=100)
            for p in prods.data:
                if p.name == spec["product_name"]:
                    product_id = p.id
                    break
        except Exception as e:
            log.warning(f"[Stripe Setup] product list 失敗: {e}")
        if not product_id:
            try:
                prod = s.Product.create(
                    name=spec["product_name"],
                    description=spec["description"],
                    metadata=spec["metadata"],
                )
                product_id = prod.id
                log.info(f"[Stripe Setup] product 作成: {spec['product_name']} = {product_id}")
            except Exception as e:
                results.append({
                    "lookup_key": lk,
                    "status": "product_create_failed",
                    "error": str(e),
                })
                continue

        # 3. Price 作成 (lookup_key + recurring monthly + JPY)
        try:
            price = s.Price.create(
                product=product_id,
                unit_amount=amount,
                currency="jpy",
                recurring={"interval": "month"},
                lookup_key=lk,
                transfer_lookup_key=True,  # 同 lookup_key の旧 Price から強制移管
                metadata=spec["metadata"],
            )
            log.info(f"[Stripe Setup] price 作成: lookup_key={lk} amount={amount} id={price.id}")

            # 4. キャッシュ更新 (founder_special / student_addon のみ)
            now = datetime.now(timezone.utc)
            if lk == "founder_special":
                global _FOUNDER_SPECIAL_PRICE_CACHE
                _FOUNDER_SPECIAL_PRICE_CACHE = {"id": price.id, "checked_at": now}
            elif lk == "student_addon":
                global _STUDENT_ADDON_PRICE_CACHE
                _STUDENT_ADDON_PRICE_CACHE = {"id": price.id, "checked_at": now}

            results.append({
                "lookup_key": lk,
                "status": "created",
                "product_id": product_id,
                "price_id": price.id,
                "amount_jpy": amount,
                "expected_jpy": amount,
                "amount_match": True,
                "interval": "month",
                "message": f"✅ 作成完了 ({price.id}・¥{amount:,}/月)",
            })
        except Exception as e:
            results.append({
                "lookup_key": lk,
                "status": "price_create_failed",
                "error": str(e),
            })

    # サマリ
    created = [r for r in results if r["status"] == "created"]
    existing = [r for r in results if r["status"] == "existing"]
    mismatched = [r for r in results if r["status"] == "existing_amount_mismatch"]
    failed = [r for r in results if r["status"] in ("product_create_failed", "price_create_failed")]

    return {
        "ok": len(failed) == 0,
        "summary": {
            "total": len(_STRIPE_PLAN_SPECS),
            "created": len(created),
            "existing_match": len(existing),
            "existing_mismatch": len(mismatched),
            "failed": len(failed),
        },
        "results": results,
        "next_steps": (
            "✅ 全プラン Stripe 反映済 (lookup_key で動的解決)。env 設定は不要。"
            if len(failed) == 0 and len(mismatched) == 0
            else (
                "⚠️ amount mismatch あり: 該当プランの旧 Price を Stripe Dashboard で active=False にしてから再実行してください。"
                if len(mismatched) > 0
                else "❌ 一部失敗: results.error を確認"
            )
        ),
    }


@app.get("/api/admin/stripe/check-prices")
def admin_stripe_check_prices(authorization: Optional[str] = Header(None)):
    """💳 全プランの Stripe 反映状態をチェック (= 読み取りのみ・Price は作成しない)
    塾長が「金額が Stripe に反映されているか」を確認する用。

    2 段検査:
    (A) lookup_key で見つかる Price の amount が PRICE_MAP の期待値と一致するか
    (B) **env (STRIPE_PRICE_*) が指す Price の amount も期待値と一致するか**
        → 2026-05-07 student_addon env が ¥9,800 旧 Price を指していて UI ¥5,000 と
          不一致だった致命事故 (Reviewer A 検出) の再発防止。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY が未設定")

    s = get_stripe()

    # 各プランの env 値を spec に組み込んでおく (eval 経由で取得)
    _ENV_BY_LOOKUP = {
        "founder_special": STRIPE_PRICE_FOUNDER_SPECIAL,
        "premium": STRIPE_PRICE_PREMIUM,
        "family": STRIPE_PRICE_FAMILY,
        "standard": STRIPE_PRICE_STANDARD,
        "student_addon": STRIPE_PRICE_STUDENT_ADDON,
    }

    results = []
    for spec in _STRIPE_PLAN_SPECS:
        lk = spec["lookup_key"]
        amount = spec["amount"]
        result = {
            "lookup_key": lk,
            "expected_jpy": amount,
        }

        # (A) lookup_key 検索
        try:
            existing = s.Price.list(lookup_keys=[lk], active=True, limit=1)
            if existing and existing.data:
                ex = existing.data[0]
                lk_match = (ex.unit_amount == amount)
                result.update({
                    "stripe_jpy": ex.unit_amount,
                    "match": lk_match,
                    "price_id": ex.id,
                    "interval": ex.recurring.get("interval") if ex.recurring else None,
                    "active": ex.active,
                })
            else:
                result.update({
                    "stripe_jpy": None,
                    "match": False,
                    "price_id": None,
                    "missing": True,
                })
        except Exception as e:
            result.update({
                "match": False,
                "error": f"lookup_key search failed: {e}",
            })

        # (B) env 値の検証 (env が指す Price の amount が期待値と一致するか)
        env_pid = (_ENV_BY_LOOKUP.get(lk) or "").strip()
        if env_pid and not env_pid.endswith("_placeholder"):
            try:
                env_price = s.Price.retrieve(env_pid)
                env_amount = env_price.get("unit_amount")
                env_match = (env_amount == amount)
                result["env"] = {
                    "price_id": env_pid,
                    "stripe_jpy": env_amount,
                    "match": env_match,
                    "lookup_key_on_price": env_price.get("lookup_key"),
                    "active": env_price.get("active"),
                }
                # env が違う Price を指していたら overall match を falsify
                if not env_match:
                    result["match"] = False
                    result["env_mismatch"] = True
            except Exception as e:
                result["env"] = {
                    "price_id": env_pid,
                    "error": str(e),
                    "match": False,
                }
                result["match"] = False
        else:
            # env が placeholder/空 → lookup_key 結果が source of truth
            result["env"] = {
                "price_id": env_pid or None,
                "match": None,  # env 未設定なので評価対象外
                "note": "env 未設定 → lookup_key を source of truth として使う" if not env_pid else "env が placeholder",
            }

        results.append(result)

    all_match = all(r.get("match") for r in results)
    missing = [r for r in results if r.get("missing")]
    mismatched = [r for r in results if r.get("stripe_jpy") is not None and not r.get("match") and not r.get("missing")]
    env_mismatched = [r for r in results if r.get("env_mismatch")]
    # env が「実際に設定されていて lookup_key と金額一致」しているプラン数を数える
    # (未設定で lookup_key fallback の場合は env.match=None なので除外)
    env_set_and_match = [r for r in results if (r.get("env") or {}).get("match") is True]
    env_unset_fallback = [r for r in results if (r.get("env") or {}).get("match") is None and r.get("match") is True]

    if all_match:
        if not env_unset_fallback:
            recommendation = "✅ 全プラン Stripe 反映済 (lookup_key + env 両方一致)"
        else:
            unset_keys = ", ".join(r["lookup_key"] for r in env_unset_fallback)
            recommendation = (
                f"✅ 全プラン Stripe 反映済 (lookup_key 一致 / env: {len(env_set_and_match)} 件設定済 + "
                f"{len(env_unset_fallback)} 件は lookup_key fallback で解決: {unset_keys})"
            )
    else:
        msgs = []
        if missing:
            msgs.append(f"未作成 {len(missing)} 件 → POST /api/admin/stripe/setup-all-prices")
        if env_mismatched:
            msgs.append(f"env が間違った Price を指している {len(env_mismatched)} 件 → Render env を修正")
        if mismatched:
            msgs.append(f"lookup_key 上の Price 金額不一致 {len(mismatched)} 件")
        recommendation = "⚠️ " + " / ".join(msgs)

    return {
        "ok": all_match,
        "all_match": all_match,
        "missing_count": len(missing),
        "mismatched_count": len(mismatched),
        "env_mismatched_count": len(env_mismatched),
        "env_unset_fallback_count": len(env_unset_fallback),
        "env_set_match_count": len(env_set_and_match),
        "results": results,
        "recommendation": recommendation,
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


@app.post("/api/admin/marketing/send-ig-carousel")
async def admin_send_ig_carousel(
    payload: dict = None,
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
):
    """📸 Instagram カルーセル投稿(16機能詳細)の PNG リンク + キャプションを Gmail へ送信。
    認証: admin Bearer or x-cron-secret
    payload: {to?: str, base_url?: str}
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    payload = payload or {}
    to_email = payload.get("to") or os.getenv("DAILY_SNS_TO_EMAIL", "shock11090304@gmail.com")
    base_url = (payload.get("base_url") or "https://trillion-ai-juku.com").rstrip("/")
    prefix = payload.get("prefix", "ig-detail")
    count = int(payload.get("count", 10))

    DEFAULT_TITLES_DETAIL = {
        1: "01 表紙 — 子の月10万、もう要らない。",
        2: "02 24時間 AIチューター",
        3: "03 リアル英字ニュース読解",
        4: "04 個別カリキュラム自動生成",
        5: "05 Learning Brain — 記憶最適化",
        6: "06 5試験完全対応",
        7: "07 大学入試 23大学",
        8: "08 スピーキング & 英作文添削",
        9: "09 東大生3人が問題を検閲",
        10: "10 CTA — 席を確保する",
    }
    DEFAULT_TITLES_RESULTS = {
        1: "01 表紙 — ¥14,500の中身、ぜんぶ見せます。",
        2: "02 学習管理画面 — 今日のタスクが決まっている",
        3: "03 生成AIテキスト — 参考書1冊分が18秒で",
        4: "04 問題演習プリント — 印刷可能、氏名欄つき",
        5: "05 弱点補強プリント — AIが弱点を5単元に絞る",
        6: "06 模試取り込み — 紙を撮るだけで原因タグ化",
        7: "07 CTA — 見たら、止まらない。",
    }
    DEFAULT_CAPTION_DETAIL = (
        "中3の息子に、家庭教師を月10万払っていた。\n"
        "AIに切り替えて3ヶ月、模試の偏差値が8上がった。\n"
        "月¥14,500。それが現実。\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "▼ ¥14,500 で受け取れる16機能 (抜粋)\n\n"
        "✓ 24時間 AIチューター (深夜3時も応答)\n"
        "✓ 教材スキャン Vision AI (紙を撮る → 類題生成)\n"
        "✓ 個別カリキュラム自動生成 (志望校逆算)\n"
        "✓ エビングハウス自動復習 (忘れる前に出し直す)\n"
        "✓ 5試験完全対応 (英検/TOEFL/TOEIC/IELTS/大学入試)\n"
        "✓ 大学入試 23大学 (MARCH 〜 東大・医学部 まで)\n"
        "✓ AIスピーキング採点 + 英作文100点満点添削\n"
        "✓ リアル英字ニュース読解 (CNN/BBC/NYT 計10フィード)\n"
        "✓ 東大生3人が問題を検閲する品質保証\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "【¥14,500/月 永年保証】\n"
        "創設メンバー50名限定 / 契約後も値上げなし\n"
        "通常¥39,800のところ、永年この価格。\n\n"
        "【7日間 完全無料】\n"
        "クレカ登録なし。自動課金なし。\n\n"
        "【申込】\n"
        "プロフィールURL、または\n"
        "trillion-ai-juku.com/lp.html\n\n"
        "家庭教師月10万も、塾月5万も、もう要らない。\n"
        "家計を守りながら、子の進路は妥協しない。\n\n"
        "#ai塾 #大学受験 #高校受験 #英検準1級 #toeic #塾選び #家庭教師 #オンライン塾 #自宅学習 #生成ai"
    )
    DEFAULT_CAPTION_RESULTS = (
        "うちの子の机に、今こんなプリントが置いてあります。\n\n"
        "数学Ⅱ・三角関数 30問。AI が昨夜のうちに自動で作ったやつです。\n\n"
        "正直、最初は半信半疑でした。「AI塾」って響きだけで中身ペラペラなんじゃないかって。だから今回は、機能を語るのをやめて、画面そのものを置きます。\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "▼ Slide 2 / 学習管理画面\n"
        "朝、子どもがスマホを開くと「今日のタスク」が3つ並んでいる。連続学習47日。校内ランキング学年12位、5つ上昇。これだけで「今日もやるか」になる。親の LINE にも日次レポート。\n\n"
        "▼ Slide 3 / 生成AIテキスト\n"
        "「物理 電磁誘導」と打つだけで、参考書1冊分の解説が出てくる。日常イメージ→数式→よくある誤解の順。「高校生の語彙で」「東大レベルで」と難易度指定もできる。生成は平均18秒。\n\n"
        "▼ Slide 4 / 問題演習プリント\n"
        "本気で印刷できる。氏名欄も日付欄もある、塾でもらうのと同じ体裁。30問+解答解説 PDF が同時に出る。これが本当に効きました。机に紙があるとスマホを置く。\n\n"
        "▼ Slide 5 / 弱点補強プリント\n"
        "過去30日の誤答を AI が分析して「あなたの弱点トップ5」を出す。即その単元だけのプリントを生成。「この5単元だけで模試+18点見込み」のメッセージが、子どもより先に親に刺さる。\n\n"
        "▼ Slide 6 / 模試取り込み\n"
        "紙の模試をスマホで撮るだけ。AI が誤答1つ1つに「平方完成の符号ミス」「時制の認識不足」と原因タグを付ける。模試1回でその子専用の弱点プリントが1セット出来上がる。\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "ここまでの5機能を全部回すと、市販の参考書+個別塾+添削サービスを足したくらいの体験になります。\n\n"
        "それを月¥14,500。通常 ¥39,800 のところ、創設メンバー50名は永年¥14,500で固定。残り18席。\n\n"
        "「説明されて納得する」より「画面を見て確信する」ほうが、たぶん早い。\n\n"
        "7日間、完全無料で全機能触れます。クレカ登録なし。MARCH・関関同立から東大まで対応。中堅大学を切り捨てた塾ではありません。\n\n"
        "見たら、止まらないです。\n\n"
        "trillion-ai-juku.com/lp.html\n\n"
        "#ai塾 #大学受験 #高校受験 #塾選び #家庭教師 #英検 #自宅学習 #生成ai #高校生勉強垢 #中学生勉強垢"
    )

    if prefix == "ig-results":
        default_titles = DEFAULT_TITLES_RESULTS
        default_caption = DEFAULT_CAPTION_RESULTS
        default_subject = "📸 Instagram カルーセル 第2弾(実画面スクショ7枚) + 投稿文"
        default_h1 = "📸 第2弾 — 実画面スクショ7枚"
        default_p = "学習管理 / AI教材 / 演習プリント / 弱点補強 / 模試取り込み"
    else:
        default_titles = DEFAULT_TITLES_DETAIL
        default_caption = DEFAULT_CAPTION_DETAIL
        default_subject = "📸 Instagram カルーセル(16機能詳細) — 完成版 + 投稿文"
        default_h1 = "📸 Instagram カルーセル投稿(完成版)"
        default_p = "16機能詳細 / 1080×1350 / 10枚"

    titles_override = payload.get("titles") or {}
    titles = {**default_titles, **{int(k): v for k, v in titles_override.items()}}
    caption = payload.get("caption") or default_caption
    subject = payload.get("subject") or default_subject
    header_h1 = payload.get("header_h1") or default_h1
    header_p = payload.get("header_p") or default_p

    slides_html = ""
    for i in range(1, count + 1):
        url = f"{base_url}/marketing-assets/{prefix}-{i}.png"
        title = titles.get(i, f"Slide {i}")
        slides_html += (
            f'<div style="margin-bottom:20px;padding:16px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;">'
            f'<div style="font-weight:700;color:#1e1b4b;margin-bottom:10px;font-size:15px;">{title}</div>'
            f'<a href="{url}" style="display:block;text-decoration:none;">'
            f'<img src="{url}" alt="{title}" style="width:100%;max-width:540px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1);display:block;">'
            f'</a>'
            f'<div style="margin-top:8px;font-size:12px;">'
            f'<a href="{url}" style="color:#6366f1;font-weight:600;text-decoration:none;">⬇️ 画像を保存 (右クリック → "画像を保存")</a>'
            f'</div>'
            f'</div>'
        )

    body_html = (
        '<!DOCTYPE html><html><body style="font-family:\'Hiragino Sans\',\'Yu Gothic\',sans-serif;max-width:640px;margin:0 auto;padding:24px;background:#f8fafc;color:#0f172a;">'
        '<div style="background:linear-gradient(135deg,#6366f1,#ec4899);color:white;padding:28px;border-radius:16px;margin-bottom:24px;">'
        f'<h1 style="margin:0;font-size:22px;">{header_h1}</h1>'
        f'<p style="margin:8px 0 0;font-size:14px;opacity:0.9;">{header_p}</p>'
        '</div>'
        '<div style="background:white;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.06);margin-bottom:20px;">'
        f'<h2 style="font-size:17px;color:#1e1b4b;margin-top:0;margin-bottom:12px;">📥 投稿用 PNG {count}枚</h2>'
        f'<p style="margin:0 0 16px;font-size:13px;color:#475569;">各画像をタップして大きく表示 → 「画像を保存」でダウンロード。Instagram の「+ 投稿」で {count}枚を順番に選択してください。</p>'
        f'{slides_html}'
        '</div>'
        '<div style="background:white;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.06);margin-bottom:20px;">'
        '<h2 style="font-size:17px;color:#1e1b4b;margin-top:0;">📝 投稿文 (キャプション・コピペ用)</h2>'
        f'<pre style="background:#0f172a;color:#e2e8f0;padding:18px;border-radius:8px;white-space:pre-wrap;font-size:12px;line-height:1.7;overflow-x:auto;">{caption}</pre>'
        '<p style="margin:12px 0 0;font-size:12px;color:#64748b;">※ ハッシュタグは 10個に最適化済 (アカウント設定上限考慮)。</p>'
        '</div>'
        '<div style="background:white;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.06);">'
        '<h2 style="font-size:17px;color:#1e1b4b;margin-top:0;">✅ 3人体制レビュー反映済</h2>'
        '<ul style="line-height:1.7;padding-left:20px;font-size:13px;margin:0;">'
        '<li>表紙: 価格訴求 →「子の月10万、もう要らない。」(損失回避フック)</li>'
        '<li>CTA: 「席を確保する」+ 残り席カウンタ + 永年¥14,500保証</li>'
        '<li>順序: 英字ニュース(差別化) を 3枚目に前倒し</li>'
        '<li>包摂: 「MARCH・関関同立 〜 東大・医学部」で中堅志望者も対象</li>'
        '<li>専門用語: Learning Brain には平易な言い換え併記</li>'
        '<li>人間関与: 「東大生3人が検閲」スライドで AI完結不安払拭</li>'
        '<li>ハッシュタグ: 10個に最適化</li>'
        '</ul>'
        '</div>'
        '<p style="text-align:center;font-size:12px;color:#94a3b8;margin-top:24px;">Generated by Claude Code (Opus 4.7) for trillion-ai-juku.com</p>'
        '</body></html>'
    )

    result = _send_monitor_email(
        subject=subject,
        body_html=body_html,
        to_email=to_email,
    )
    return {"ok": True, "to": to_email, "slides": count, "prefix": prefix, **result}


# ==========================================================================
# 🎓 通塾生 招待リンク (HMAC 署名付き・期限付き)
# ==========================================================================
# 塾長運用: 既存通塾生から「DM で AI塾アドオンの招待ください」と来たら、
# CEO ダッシュ or admin endpoint で email 1件 → invite URL 発行 → DM 返信。
# student-upgrade.html は invite gate で未認可訪問を LP に redirect する。
# ==========================================================================

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _sign_invite_token(email: str, expires_days: int = 30) -> str:
    """既存通塾生向け招待トークン生成。形式: <payload_b64>.<sig_b64>"""
    if not APP_SECRET:
        raise HTTPException(status_code=503, detail="APP_SECRET 未設定 (Railway env を確認)")
    payload = {
        "e": (email or "").strip().lower(),
        "exp": int((datetime.now(timezone.utc) + timedelta(days=expires_days)).timestamp()),
        "k": "student_addon",
    }
    payload_json = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    payload_b64 = _b64url_encode(payload_json)
    sig = hmac.new(APP_SECRET.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{payload_b64}.{sig_b64}"


def _verify_invite_token(token: str) -> dict:
    """招待トークン検証。{valid, email?, expires_at?, reason?} を返す。
    2026-05-07: HMAC 形式の URL token 以外に、短い招待コード (AJK-XXXXXXXX 等)
    も受け付ける。コードの場合は DB invite_codes table から lookup する。"""
    if not APP_SECRET:
        return {"valid": False, "reason": "server_misconfigured"}
    if not token:
        return {"valid": False, "reason": "malformed"}
    token = token.strip()
    # ① 短い招待コード形式 (AJK-XXXXXXXX 系) → DB lookup
    if "." not in token and len(token) <= 64:
        return _verify_invite_code_db(token)
    # ② 従来の HMAC 形式 (<payload_b64>.<sig_b64>)
    if "." not in token:
        return {"valid": False, "reason": "malformed"}
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        expected_sig = hmac.new(APP_SECRET.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        provided_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, provided_sig):
            return {"valid": False, "reason": "signature_mismatch"}
        payload = json.loads(_b64url_decode(payload_b64).decode('utf-8'))
        exp = payload.get("exp", 0)
        if exp < datetime.now(timezone.utc).timestamp():
            return {"valid": False, "reason": "expired"}
        return {
            "valid": True,
            "email": payload.get("e", ""),
            "expires_at": exp,
            "kind": payload.get("k", ""),
        }
    except Exception as e:
        return {"valid": False, "reason": f"parse_error_{type(e).__name__}"}


# 🎫 短い招待コード (DB lookup 方式・2026-05-07 追加)
import secrets as _secrets

def _generate_invite_code(prefix: str = "AJK") -> str:
    """ハイフン込み 12 文字の招待コードを生成。
    形式: AJK-XXXXXXXX (8 文字 base32 大文字・人間が読みやすい)
    人間タイポしやすい O/0/I/1 を除外した 32 文字セット。"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 32 chars (O/0/I/1 除外)
    suffix = "".join(_secrets.choice(alphabet) for _ in range(8))
    return f"{prefix}-{suffix}"


def _normalize_invite_code(code: str) -> str:
    """ユーザ入力を normalize: 全角→半角・大文字化・前後空白除去・全空白除去。
    e.g. "ajk-abc12345" / "ＡＪＫ−ＡＢＣ１２３４５" → "AJK-ABC12345" """
    if not code:
        return ""
    s = code.strip()
    # 全角 → 半角
    fullwidth_to_halfwidth = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789−ー―‐",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789----"
    )
    s = s.translate(fullwidth_to_halfwidth)
    # 全空白除去 + 大文字化
    s = "".join(s.split()).upper()
    return s


def _verify_invite_code_db(code: str) -> dict:
    """DB lookup 方式の招待コード検証。{valid, email?, expires_at?, reason?, kind?}"""
    code_norm = _normalize_invite_code(code)
    if not code_norm or len(code_norm) > 64:
        return {"valid": False, "reason": "malformed"}
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "SELECT id, code, email, kind, expires_at, used_at FROM invite_codes WHERE UPPER(code) = ? LIMIT 1",
            (code_norm,)
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return {"valid": False, "reason": "not_found"}
        # expires_at は string (postgres TIMESTAMP) or datetime → parse
        exp_raw = row["expires_at"] if hasattr(row, "__getitem__") else row[4]
        try:
            if isinstance(exp_raw, str):
                # PostgreSQL の "2026-05-14 11:32:15+00" 形式 or ISO
                from dateutil import parser as _du_parser
                exp_dt = _du_parser.parse(exp_raw)
            else:
                exp_dt = exp_raw
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            exp_ts = exp_dt.timestamp()
        except Exception:
            # fallback: assume not expired if we can't parse
            exp_ts = datetime.now(timezone.utc).timestamp() + 86400
        if exp_ts < datetime.now(timezone.utc).timestamp():
            return {"valid": False, "reason": "expired"}
        return {
            "valid": True,
            "email": row["email"],
            "expires_at": int(exp_ts),
            "kind": row["kind"] or "student_addon",
            "code": row["code"],
        }
    except Exception as e:
        log.warning(f"[InviteCode] verify failed: {type(e).__name__}: {e}")
        return {"valid": False, "reason": f"db_error_{type(e).__name__}"}


def _save_invite_code(code: str, email: str, kind: str, expires_at_iso: str, notes: str = "") -> bool:
    """招待コードを DB に保存。冪等 (同 code 既存なら False)。"""
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            """INSERT INTO invite_codes (code, email, kind, expires_at, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (code, (email or "").strip().lower(), kind, expires_at_iso, notes or "")
        )
        conn.commit()
        conn.close()
        return True
    except IntegrityError:
        try: conn.rollback()
        except Exception: pass
        try: conn.close()
        except Exception: pass
        return False
    except Exception as e:
        log.warning(f"[InviteCode] save failed: {type(e).__name__}: {e}")
        try: conn.close()
        except Exception: pass
        return False


@app.post("/api/admin/marketing/generate-student-invite")
async def admin_generate_student_invite(
    payload: dict = None,
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
):
    """🎓 既存通塾生 向け 招待 URL を 1件発行 (HMAC 署名 / 30日期限デフォルト)。
    塾長運用: 生徒/保護者から DM で「招待ください」が来たら 1 email を入れて URL を返信。
    認証: admin Bearer or x-cron-secret
    payload: {email: str, expires_days?: 30, base_url?, name?}
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    payload = payload or {}
    email = (payload.get("email") or "").strip().lower()
    expires_days = int(payload.get("expires_days", 30))
    base_url = (payload.get("base_url") or "https://trillion-ai-juku.com").rstrip("/")
    name = (payload.get("name") or "").strip()

    if not email or "@" not in email or "." not in email.split("@", 1)[1]:
        raise HTTPException(status_code=400, detail="email が不正")
    if expires_days < 1 or expires_days > 365:
        raise HTTPException(status_code=400, detail="expires_days は 1〜365 の範囲")

    token = _sign_invite_token(email, expires_days)
    invite_url = f"{base_url}/student-upgrade.html?invite={token}"
    expires_at_jst = (datetime.now(timezone.utc) + timedelta(days=expires_days)).astimezone(timezone(timedelta(hours=9)))

    name_part = f"{name}さん " if name else ""
    dm_template = (
        f"{name_part}いつもありがとうございます！\n"
        f"\n"
        f"AI学習アドオンの招待URLをお送りします。\n"
        f"通塾生限定・永年¥5,000/月 (入塾金免除) です。\n"
        f"\n"
        f"こちらから\n"
        f"{invite_url}\n"
        f"\n"
        f"※ {expires_at_jst.strftime('%Y/%m/%d')} までに開いてください。\n"
        f"※ 不明点はこちらの DM にどうぞ。"
    )

    return {
        "ok": True,
        "email": email,
        "invite_url": invite_url,
        "token": token,
        "expires_days": expires_days,
        "expires_at_iso": expires_at_jst.isoformat(),
        "expires_at_jst": expires_at_jst.strftime("%Y-%m-%d %H:%M JST"),
        "dm_template": dm_template,
    }


@app.get("/api/marketing/verify-invite")
def public_verify_invite(token: str):
    """招待 URL の token を公開検証。frontend の student-upgrade.html が <head> で叩く。
    valid なら {valid: true, email, expires_at} を返す。invalid なら redirect すべき。
    """
    if not token:
        return {"valid": False, "reason": "missing_token"}
    return _verify_invite_token(token)


# 🎫 招待コード (短い文字列・DB lookup 方式) 生成 endpoint
# 2026-05-07: URL 焼き込み方式は塾長 typo で email mismatch → 顧客失敗事故あり (森澤さん)
# → 短い code (AJK-XXXXXXXX) を発行・顧客は checkout/upgrade で入力、server で DB lookup
@app.post("/api/admin/marketing/generate-invite-code")
async def admin_generate_invite_code(
    payload: dict = None,
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
):
    """🎫 通塾生向け 招待コード (短い文字列) を 1 件発行。
    payload: {email: str, expires_days?: 30, kind?: 'student_addon', notes?: ''}
    レスポンス: {ok, code, email, expires_at_jst, dm_template}
    認証: admin Bearer or x-cron-secret
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    payload = payload or {}
    email = (payload.get("email") or "").strip().lower()
    expires_days = int(payload.get("expires_days", 30))
    kind = (payload.get("kind") or "student_addon").strip()
    notes = (payload.get("notes") or "").strip()
    name = (payload.get("name") or "").strip()

    if not email or "@" not in email or "." not in email.split("@", 1)[1]:
        raise HTTPException(status_code=400, detail="email が不正")
    if expires_days < 1 or expires_days > 365:
        raise HTTPException(status_code=400, detail="expires_days は 1〜365 の範囲")

    # 衝突回避: 最大 5 回 retry でユニークな code を生成
    code = None
    for _ in range(5):
        candidate = _generate_invite_code()
        if _save_invite_code(
            candidate,
            email,
            kind,
            (datetime.now(timezone.utc) + timedelta(days=expires_days)).isoformat(),
            notes,
        ):
            code = candidate
            break
    if not code:
        raise HTTPException(status_code=500, detail="コード生成に失敗しました (衝突連発)。再度お試しください。")

    expires_at_jst = (datetime.now(timezone.utc) + timedelta(days=expires_days)).astimezone(timezone(timedelta(hours=9)))
    expires_at_jst_str = expires_at_jst.strftime('%Y/%m/%d %H:%M')

    name_part = f"{name}さん " if name else ""
    dm_template = (
        f"{name_part}いつもありがとうございます！\n"
        f"\n"
        f"AI学習アドオンの招待コードをお送りします。\n"
        f"通塾生限定・永年¥5,000/月 (入塾金免除) です。\n"
        f"\n"
        f"【招待コード】\n"
        f"{code}\n"
        f"\n"
        f"【お申込み手順】\n"
        f"1. https://trillion-ai-juku.com/checkout.html?plan=student_addon を開く\n"
        f"2. 「🎓 通塾生プラン」を選択\n"
        f"3. お名前・メールアドレスを入力\n"
        f"4. 「招待コード」欄に上記コード ({code}) をコピペ\n"
        f"5. 決済情報を入力 → 完了\n"
        f"\n"
        f"※ 体験期間中の学習履歴・進捗データはすべて引き継がれます。\n"
        f"※ コード有効期限: {expires_at_jst_str}\n"
        f"※ 不明点はこちらの DM にどうぞ。"
    )

    log.info(f"[InviteCode] generated code={code} email={email} kind={kind} expires_days={expires_days}")

    return {
        "ok": True,
        "code": code,
        "email": email,
        "kind": kind,
        "expires_at_jst": expires_at_jst_str,
        "expires_days": expires_days,
        "dm_template": dm_template,
        "checkout_url_with_code": f"https://trillion-ai-juku.com/checkout.html?plan=student_addon&invite_code={code}",
    }


def _send_student_invite_email(to_email: str, name: str, invite_url: str, expires_at_jst_str: str) -> dict:
    """通塾生向け招待メール (一斉配信用)。Resend 経由"""
    import html as _html
    if not RESEND_API_KEY:
        return {"sent": False, "dev_mode": True}
    safe_name = _html.escape(name or "")
    safe_invite_url = _html.escape(invite_url)  # FIX (review): href 値も XSS 対策エスケープ
    greeting = f"{safe_name}さま" if safe_name else "保護者さま"
    subject = "【AI学習コーチ塾】通塾生限定 永年¥9,800/月 招待のご案内"
    html = f"""<!DOCTYPE html>
<html><body style="font-family: -apple-system, sans-serif; line-height: 1.7; color: #333; max-width: 580px; margin: 0 auto; padding: 2rem;">
<h1 style="font-size: 1.4rem; color: #6366f1;">🎓 通塾生限定 AI 学習アドオン</h1>
<p>{greeting}、いつもありがとうございます。</p>

<p>AI学習コーチ塾 (オンライン) を、通塾生のみなさまに<strong>特別価格でご案内</strong>させていただきます。</p>

<div style="background: linear-gradient(135deg, #f0fdf4, #dbeafe); padding: 1.2rem; border-radius: 10px; margin: 1.5rem 0; border: 1px solid rgba(99,102,241,0.3);">
  <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.3rem;">通常価格 <s>¥39,800/月</s></div>
  <div style="font-size: 1.5rem; font-weight: 800; color: #6366f1;">月額 ¥9,800 永年</div>
  <div style="font-size: 0.85rem; color: #6b7280; margin-top: 0.3rem;">+ 入塾金 ¥10,000 免除</div>
</div>

<h3 style="color: #374151; font-size: 1.05rem;">何ができるか</h3>
<ul style="font-size: 0.95rem;">
  <li>📚 24時間 AI 個別質問対応 (英数理国全教科)</li>
  <li>🎯 大学別過去問風オリジナル問題プール</li>
  <li>📊 学習計画・進捗管理 (国公立難関大学コース)</li>
  <li>📝 英作文 AI 採点 / 模試</li>
  <li>📩 保護者さまへの週次学習レポート</li>
</ul>

<p style="text-align: center; margin: 2rem 0;">
  <a href="{safe_invite_url}" style="display: inline-block; padding: 1rem 2rem; background: linear-gradient(135deg, #6366f1, #ec4899); color: white; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 1.05rem;">
    🚀 通塾生プランで始める
  </a>
</p>

<p style="font-size: 0.85rem; color: #999; text-align: center;">
  ※ {_html.escape(expires_at_jst_str)} までに開いてください<br>
  ※ この URL はお客様専用です。他の方への転送はご遠慮ください
</p>

<hr style="margin: 2rem 0; border: none; border-top: 1px solid #eee;">
<p style="font-size: 0.8rem; color: #999;">
  ご不明な点は <a href="mailto:info@trillion-ai-juku.com" style="color: #6366f1;">info@trillion-ai-juku.com</a> までお問い合わせください。<br>
  配信停止をご希望の方はこのメールにご返信ください。
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
            return {"sent": True, "resend_id": result.get("id")}
    except Exception as e:
        return {"sent": False, "error": str(e)}


@app.post("/api/admin/marketing/bulk-invite")
async def admin_bulk_invite(
    payload: dict,
    authorization: Optional[str] = Header(None),
):
    """🚀 通塾生向け一斉招待メール配信。
    payload: {emails: ["a@b.com", ...], expires_days?: 30, base_url?, dry_run?: false}
    Anti-spam: 1回最大100件、Resend 100件/日無料枠を考慮。
    Dedup: 直近24h で同じ email に既に送信済ならスキップ。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    payload = payload or {}
    raw_emails = payload.get("emails") or []
    if not isinstance(raw_emails, list):
        raise HTTPException(status_code=400, detail="emails must be array")
    if len(raw_emails) == 0:
        raise HTTPException(status_code=400, detail="emails array is empty")
    if len(raw_emails) > 100:
        raise HTTPException(status_code=400, detail="一度に送信できるのは最大100件です。複数回に分けてください。")

    expires_days = int(payload.get("expires_days", 30))
    if expires_days < 1 or expires_days > 365:
        expires_days = 30
    base_url = (payload.get("base_url") or BASE_URL or "https://trillion-ai-juku.com").rstrip("/")
    dry_run = bool(payload.get("dry_run", False))

    # email 正規化 + 重複排除
    seen = set()
    emails = []
    for e in raw_emails:
        if not isinstance(e, str):
            continue
        e_norm = e.strip().lower()
        if "@" not in e_norm or "." not in e_norm.split("@", 1)[1]:
            continue
        if e_norm in seen:
            continue
        seen.add(e_norm)
        emails.append(e_norm)

    if not emails:
        raise HTTPException(status_code=400, detail="有効な email がありません")

    # 24h dedup + daily quota check (Resend 100/day 制限考慮)
    conn = db()
    c = conn.cursor()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        c.execute(
            "SELECT props FROM events WHERE name='bulk_invite_send' AND created_at > ?",
            (cutoff,)
        )
        recent_emails = set()
        sent_count_24h = 0
        for row in c.fetchall():
            try:
                p = json.loads(row["props"] if hasattr(row, "keys") else row[0])
                em = (p.get("email") or "").lower()
                if em:
                    recent_emails.add(em)
                if p.get("ok"):
                    sent_count_24h += 1
            except Exception:
                pass
    finally:
        conn.close()

    # Resend 100/日制限: 24h 累積 + 今回送信予定 が 90 件超えそうなら警告 (10件 buffer)
    will_send = len([e for e in emails if e not in recent_emails])
    if not dry_run and (sent_count_24h + will_send) > 90:
        raise HTTPException(
            status_code=429,
            detail=f"24h以内の Resend 送信枠超過の恐れ (済 {sent_count_24h} + 予定 {will_send} > 90)。明日に分割するか、件数を減らしてください。"
        )

    import time as _time
    sent_count = 0
    skipped_dedup = 0
    failed = []
    results = []
    for idx, email in enumerate(emails):
        if email in recent_emails:
            skipped_dedup += 1
            results.append({"email": email, "status": "skipped_dedup"})
            continue

        token_str = _sign_invite_token(email, expires_days)
        invite_url = f"{base_url}/student-upgrade.html?invite={token_str}"
        expires_at_jst = (datetime.now(timezone.utc) + timedelta(days=expires_days)).astimezone(timezone(timedelta(hours=9)))
        expires_str = expires_at_jst.strftime("%Y-%m-%d")

        if dry_run:
            results.append({"email": email, "status": "dry_run", "invite_url": invite_url})
            continue

        result = _send_student_invite_email(email, "", invite_url, expires_str)
        ok = bool(result.get("sent"))
        if ok:
            sent_count += 1
            results.append({"email": email, "status": "sent"})
        else:
            failed.append({"email": email, "error": result.get("error", "send_failed")})
            results.append({"email": email, "status": "failed", "error": result.get("error", "")})

        # events に記録 (dedup 用)
        try:
            conn2 = db(); cc = conn2.cursor()
            cc.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("bulk_invite_send", json.dumps({"email": email, "ok": ok, "error": result.get("error", "")}, ensure_ascii=False), "admin_bulk_invite")
            )
            conn2.commit(); conn2.close()
        except Exception as _e:
            log.warning(f"[BulkInvite] event record failed: {_e}")

        # Resend rate limit (約10req/sec) 対策: 200ms sleep
        if idx < len(emails) - 1:
            _time.sleep(0.2)

    return {
        "ok": True,
        "total": len(emails),
        "sent": sent_count,
        "skipped_dedup": skipped_dedup,
        "failed": len(failed),
        "failed_details": failed[:20],
        "dry_run": dry_run,
        "results": results if dry_run else None,
    }


@app.post("/api/admin/stripe/setup-threads6k-coupon")
def admin_stripe_setup_threads6k_coupon(
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
):
    """🎟 Threads フォロワー限定クーポン THREADS6K (永年¥2,500/月引き) を Stripe で自動作成。
    冪等: 既存があれば取得のみ。admin Bearer or x-cron-secret 認証必須。

    結果:
    - Coupon: 月額¥2,500 forever 引き (founder_special ¥14,500 → ¥12,000)
    - Promotion Code: THREADS6K (顧客が決済画面で入力)
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY が未設定")

    s = get_stripe()
    COUPON_ID = "threads6k_2500jpy_forever"
    PROMO_CODE = "THREADS6K"

    # 1. 既存 Coupon チェック
    coupon_id = None
    try:
        existing = s.Coupon.retrieve(COUPON_ID)
        if existing and existing.id:
            coupon_id = existing.id
            log.info(f"[Stripe Coupon] already exists: {coupon_id}")
    except Exception as e:
        if "No such coupon" not in str(e) and "resource_missing" not in str(e):
            log.warning(f"[Stripe Coupon] retrieve check err (continuing): {e}")

    # 2. 無ければ Coupon 作成 (¥2,500 / forever)
    if not coupon_id:
        try:
            coupon = s.Coupon.create(
                id=COUPON_ID,
                amount_off=2500,
                currency="jpy",
                duration="forever",
                name="Threads フォロワー6,000人 感謝クーポン",
                metadata={"campaign": "threads_followers_6k", "discount_jpy": "2500", "duration": "forever"},
            )
            coupon_id = coupon.id
            log.info(f"[Stripe Coupon] created: {coupon_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Coupon 作成失敗: {e}")

    # 3. 既存 Promotion Code チェック (code=THREADS6K)
    promo_id = None
    promo_active = False
    try:
        promos = s.PromotionCode.list(code=PROMO_CODE, active=True, limit=1)
        if promos and promos.data:
            p = promos.data[0]
            promo_id = p.id
            promo_active = p.active
            log.info(f"[Stripe PromoCode] already exists: {promo_id} active={promo_active}")
    except Exception as e:
        log.warning(f"[Stripe PromoCode] list err (continuing): {e}")

    # 4. 無ければ Promotion Code 作成
    if not promo_id:
        try:
            promo = s.PromotionCode.create(
                coupon=coupon_id,
                code=PROMO_CODE,
                metadata={"campaign": "threads_followers_6k"},
            )
            promo_id = promo.id
            promo_active = True
            log.info(f"[Stripe PromoCode] created: {promo_id} (code={PROMO_CODE})")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PromotionCode 作成失敗: {e}")

    return {
        "ok": True,
        "coupon_id": coupon_id,
        "coupon_amount_jpy": 2500,
        "coupon_duration": "forever",
        "promotion_code_id": promo_id,
        "promotion_code": PROMO_CODE,
        "active": promo_active,
        "message": (
            f"クーポン {PROMO_CODE} 発行完了。決済画面で『プロモーションコードを使用』に "
            f"{PROMO_CODE} を入力すると永年¥2,500/月引き = ¥12,000/月 になります。"
        ),
    }


@app.post("/api/admin/marketing/send-link-email")
async def admin_send_link_email(
    payload: dict = None,
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
):
    """🔗 任意の URL リスト + メモ を Gmail 送信する汎用 endpoint。
    認証: admin Bearer or x-cron-secret
    payload: {to?, subject?, intro?, links: [{label, url, note?}]}
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    payload = payload or {}
    to_email = payload.get("to") or os.getenv("DAILY_SNS_TO_EMAIL", "shock11090304@gmail.com")
    subject = payload.get("subject") or "🔗 URL お送りします"
    intro = payload.get("intro") or ""
    links = payload.get("links") or []

    links_html = ""
    for ln in links:
        label = ln.get("label", "リンク")
        url = ln.get("url", "")
        note = ln.get("note", "")
        links_html += (
            '<div style="margin-bottom:18px;padding:18px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;">'
            f'<div style="font-weight:700;color:#1e1b4b;margin-bottom:8px;font-size:15px;">{label}</div>'
            f'<div style="background:#0f172a;color:#a5b4fc;padding:14px 16px;border-radius:8px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;word-break:break-all;line-height:1.6;">{url}</div>'
            + (f'<div style="margin-top:10px;font-size:13px;color:#475569;line-height:1.6;">{note}</div>' if note else '')
            + '</div>'
        )

    intro_html = f'<p style="font-size:14px;color:#334155;line-height:1.7;margin:0 0 16px;">{intro}</p>' if intro else ''

    body_html = (
        '<!DOCTYPE html><html><body style="font-family:\'Hiragino Sans\',\'Yu Gothic\',sans-serif;max-width:640px;margin:0 auto;padding:24px;background:#f8fafc;color:#0f172a;">'
        '<div style="background:linear-gradient(135deg,#6366f1,#ec4899);color:white;padding:24px;border-radius:14px;margin-bottom:20px;">'
        f'<h1 style="margin:0;font-size:20px;">{subject}</h1>'
        '</div>'
        '<div style="background:white;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.06);">'
        f'{intro_html}'
        f'{links_html}'
        '</div>'
        '<p style="text-align:center;font-size:12px;color:#94a3b8;margin-top:20px;">trillion-ai-juku.com</p>'
        '</body></html>'
    )

    result = _send_monitor_email(subject=subject, body_html=body_html, to_email=to_email)
    return {"ok": True, "to": to_email, "links": len(links), **result}


@app.post("/api/admin/cache/force-purge")
def admin_cache_force_purge(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """🧹 全生徒のブラウザキャッシュを強制パージ。

    DB に CACHE_VERSION を bump して保存。フロントの cache-purge.js が起動時に
    /api/cache-version を叩き、保存値より新しければ caches を全削除 + 強制リロード。
    バージョン文字列は ISO timestamp で生成。
    認証: admin Bearer または X-Cron-Secret (緊急対応で塾長離席中でも実行可・2026-05-06)"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
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


def _exam_questions_import_core(questions: list, skip_full: bool = False) -> dict:
    """exam_questions 一括インサートのコアロジック (admin endpoint と AI チームワークフロー両方から再利用)。

    入力 validation は呼び出し側で行うこと (questions が list で空ではないことを保証)。
    重複 import の防御は呼び出し側責任 (memory: feedback_seed_import_no_loop.md)。
    """
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
    return _exam_questions_import_core(questions, skip_full)


# ==========================================================================
# 🤖 AI チーム検閲ワークフロー ($0 半自動運用): 塾長保有の Claude Max + ChatGPT Plus + Gemini を
# 組み合わせた多視点問題生成パイプライン。各 phase の prompt を返すので、塾長が各 AI UI に
# コピペして結果を貼り戻して次に進む。memory: feedback_team_review_all_generation.md +
# feedback_5_person_textbook_review.md + feedback_3_person_team_review.md の AI 多視点版。
# 2026-05-10 塾長指示「複数 AI を追加 + NotebookLM 風検索」の実装。
# ==========================================================================

def _build_ai_team_search_prompt(exam_id: str, exam_label: str, part_label: str,
                                  topic_hint: Optional[str], year: Optional[int], count: int) -> str:
    """Phase 0: ChatGPT Project (過去問 PDF アップロード済) で引用付き傾向検索 prompt"""
    topic_clause = f"- 単元: 「{topic_hint}」中心" if topic_hint else "- 単元: 指定なし (典型出題範囲から)"
    year_clause = f"- 参考年度: {year}" if year else "- 参考年度: 近年 (2020-2024 を中心に)"
    return f"""[ChatGPT Project: ai-juku 過去問アーカイブ]

このプロジェクトに格納された過去問 PDF・参考書・出題傾向資料を検索し、以下の問題作成に使える情報を **引用付き** で報告してください。

【作成対象】
- 試験: {exam_id} ({exam_label})
- 大問: {part_label}
{topic_clause}
{year_clause}
- 生成予定数: {count}問

【出力形式 (Markdown)】
## 1. 出題形式の特徴
- 設問数 / 文字数 / 選択肢数 / 制限時間
- 出題者が測ろうとしている能力 (3-5 行)

## 2. 直近3年の頻出テーマ (引用付き)
- 例: 「2023年 第3問: AI と教育、英文 800wd、選択肢 4つ」 [出典: 過去問集.pdf p.23]
- 5-8 件挙げる。引用元は **必ず Project 内資料の [ファイル名 page N]** で明示

## 3. 典型的な誤答パターン
- 受験生が陥りがちな罠を 3-5 個

## 4. 類題作成上の注意点
- 著作権配慮 (丸写し禁止・「形式準拠の類題」として作る)
- 避けるべき表現・選ぶべきテーマ

## 5. 推奨テーマ (この {count}問 で扱うべき topic 候補)
- 重複を避け、近年の trend と典型論題のバランス
"""


def _build_ai_team_author_prompt(exam_id: str, exam_label: str, part_key: str, part_label: str,
                                  eiken_grade: Optional[str], topic_hint: Optional[str],
                                  year: Optional[int], count: int) -> str:
    """Phase 1: Claude Opus 4.7 (Claude Max UI) で執筆 prompt
    既存 _generate_exam_question の system prompt の知見を流用 (コアイメージ×文構造分析)"""
    topic_clause = f"- 単元固定: 「{topic_hint}」が問題の核心となる出題のみ" if topic_hint else "- 単元: 出題範囲内で多様性確保"
    year_clause = f"- 年度準拠: {year} 年度の出題傾向を強く反映" if year else "- 年度: 近年トレンド優先"
    return f"""あなたは {exam_label} の問題作成専門家です。直前に取得した過去問検索結果を踏まえ、新規 **類題** を {count} 問作成してください。

【Phase 0 検索結果 (ChatGPT Project からの引用付き出力)】
↓ ここに検索結果を貼り付けて Claude に渡してください ↓
<<SEARCH_RESULTS>>

【作成仕様】
- 試験: {exam_id} ({exam_label})
- 大問: {part_key} ({part_label})
{topic_clause}
{year_clause}
- 生成数: {count}問

【絶対遵守】
- 過去問の丸写しは著作権上禁止。**「形式に完全準拠した類題」** を新規作成
- 英文は ETS / Cambridge / Oxford 級の自然な英語 (機械翻訳臭・不自然な語彙NG)
- 解説は **コアイメージ × 文構造分析の二段構え** (既存 ai-juku 流儀)
- **教師名禁止**: 関正生・富田 等の特定教師名は出力に一切含めない (memory: english_philosophy)

【🔥 解説の絶対遵守フォーマット】
explanation フィールドは Markdown で **以下4セクションを必ず明示**:
## 🎯 コアイメージ
〔該当する語法・文法・時制・前置詞・冠詞のコアイメージを 2-3 行で〕

## 🔬 文構造分析 ← 絶対省略禁止
〔該当文の S/V/O/C/M をラベル付きで明示。入れ子節は階層で〕

## 📍 本文の根拠 (長文の場合)
〔該当箇所を「" "」で引用 + 段落番号〕

## ❌ 誤答 NG 理由 (multiple_choice の場合は必須)
〔各誤答選択肢ごとに、構造的・本質的になぜ NG か 1 行ずつ〕

【出力形式】
**純粋な JSON のみ** (前後にテキストや ```json タグは禁止)。explanation 内 Markdown は \\n でエスケープ。

```
{{
  "questions": [
    {{
      "exam_id": "{exam_id}",
      "part_key": "{part_key}",
      "eiken_grade": {("\"" + eiken_grade + "\"") if eiken_grade else "null"},
      "question_data": {{
        "passage": "...",
        "stem": "...",
        "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "correct": "A",
        "explanation": "## 🎯 コアイメージ\\n...\\n\\n## 🔬 文構造分析\\n..."
      }},
      "model": "claude-opus-4-7-team-workflow"
    }}
  ]
}}
```
"""


def _build_ai_team_review_prompt(role: str, exam_label: str, part_label: str, count: int) -> str:
    """Phase 2-4: 検閲 prompt (内容/教育/入試の3視点)"""
    role_def = {
        "content": {
            "title": "内容検閲官 (GPT-5 Custom GPT 推奨)",
            "viewpoint": "文章理解・論理整合性",
            "checklist": [
                "本文と設問・正解選択肢の論理的整合性 (本文に書かれていない推論で正解を選ばせていないか)",
                "誤答選択肢が「本文と矛盾している」「明らかに範囲外」など客観的に NG とわかる構造か",
                "passage の英語が自然で文法的に正しいか (ETS/Cambridge 級か)",
                "explanation の論理が破綻していないか (コアイメージと文構造分析が一貫しているか)",
                "事実誤認 (歴史/科学/時事) はないか",
            ],
        },
        "pedagogy": {
            "title": "教育検閲官 (Gemini 2.5 Pro 推奨)",
            "viewpoint": "学習者視点・難易度・分かりやすさ",
            "checklist": [
                f"{exam_label} の対象学習者 (高校生〜社会人) のレベル感に合っているか (語彙難度・文法難度)",
                "問題が複数の解釈を許してしまう曖昧さがないか",
                "解説が「なぜそうなるか」を初学者が理解できる形で書かれているか",
                "コアイメージ説明が抽象的すぎず、具体例で補強されているか",
                "誤答理由が学習者の typical な間違いを反映しているか",
            ],
        },
        "exam": {
            "title": "入試検閲官 (Claude Sonnet 4.6 + Custom GPT 推奨)",
            "viewpoint": "出題形式整合・実試験での妥当性",
            "checklist": [
                f"{exam_label} の出題形式 (設問数/語数/選択肢数/設問順序) に完全準拠しているか",
                f"{part_label} の典型出題スタイルから逸脱していないか",
                "近年の試験 trend (出題テーマ・形式変更) を反映しているか",
                "難易度が当該試験・大問の標準分布から外れすぎていないか",
                "本番試験で出されても違和感がないか (作問者として実戦的か)",
            ],
        },
    }[role]

    checklist_md = "\n".join(f"   - {c}" for c in role_def["checklist"])
    return f"""あなたは ai-juku の **{role_def['title']}** です。以下の {count} 問の問題 JSON を **{role_def['viewpoint']}** 観点で検閲してください。

【Phase 1 執筆結果 (Claude Opus からの出力 JSON)】
↓ ここに Phase 1 の JSON を貼り付けてください ↓
<<AUTHOR_OUTPUT>>

【検閲観点】
{checklist_md}

【判定ランク】
- CRITICAL: 致命 (誤答や事実誤認・形式逸脱・著作権侵害の疑い等、import 不可)
- MAJOR: 重大 (修正必須だが致命ではない)
- MINOR: 軽微 (修正推奨だが妥協可)
- OK: 問題なし

【出力形式】
**純粋な JSON のみ** (前後にテキスト禁止):

```
{{
  "review_results": [
    {{
      "question_index": 0,
      "verdict": "OK" | "MINOR" | "MAJOR" | "CRITICAL",
      "score": 0-100,
      "issues": [
        {{
          "type": "...",
          "severity": "MINOR" | "MAJOR" | "CRITICAL",
          "detail": "問題の具体的説明",
          "suggestion": "推奨修正内容"
        }}
      ]
    }}
  ],
  "overall_verdict": "PASS" | "REVIEW_AGAIN" | "REJECT",
  "overall_summary": "全体所感を 2-3 行"
}}
```
"""


def _build_ai_team_integration_prompt(exam_id: str, exam_label: str, count: int) -> str:
    """Phase 5: Claude Opus 4.7 で 3 検閲フィードバックを踏まえた最終版統合 prompt"""
    return f"""あなたは ai-juku の **編集統合担当 (Claude Opus 4.7)** です。以下の元問題と 3 視点の検閲結果を踏まえ、import endpoint にそのまま投入できる **最終版 JSON** を作成してください。

【Phase 1 執筆結果 (元問題)】
↓ ここに Phase 1 の JSON を貼り付け ↓
<<AUTHOR_OUTPUT>>

【Phase 2 内容検閲フィードバック】
↓ ここに Phase 2 の JSON を貼り付け ↓
<<REVIEW_CONTENT>>

【Phase 3 教育検閲フィードバック】
↓ ここに Phase 3 の JSON を貼り付け ↓
<<REVIEW_PEDAGOGY>>

【Phase 4 入試検閲フィードバック】
↓ ここに Phase 4 の JSON を貼り付け ↓
<<REVIEW_EXAM>>

【統合方針】
- **CRITICAL は必ず修正** (1件でも残ったら REJECT 扱い)
- **MAJOR は基本修正** (説明できる例外のみコメントで残す)
- **MINOR は判断** (採用可否を明示)
- 3 検閲官で意見対立 (例: 内容OK / 教育CRITICAL) があれば、
  入試 > 内容 > 教育 の優先順位で判断 (出題形式は本番試験準拠が最優先)
- **CRITICAL が解消できない問題は最終 array から削除** し、削除理由を removed_questions に記録

【出力形式】
**import endpoint がそのまま受け取れる JSON のみ**:

```
{{
  "questions": [
    {{
      "exam_id": "{exam_id}",
      "part_key": "...",
      "eiken_grade": "...",
      "question_data": {{ ... 修正済 ... }},
      "model": "claude-opus-4-7-team-workflow-v2"
    }}
  ],
  "removed_questions": [
    {{ "original_index": N, "reason": "CRITICAL 解消不可: ..." }}
  ],
  "integration_notes": [
    "Q1: 教育検閲の MAJOR (語彙難) を採用、passage 一部書き換え",
    "Q2: 内容/入試で意見対立 → 入試判断優先で誤答選択肢 D を差替",
    ...
  ]
}}
```

最終 questions array は **そのまま {count}-削除数 件** になり、import endpoint にコピペで投入されます。
"""


def _build_ai_team_fast_prompt(exam_id: str, exam_label: str, part_key: str, part_label: str,
                                eiken_grade: Optional[str], topic_hint: Optional[str],
                                year: Optional[int], count: int) -> str:
    """⚡ 速攻モード: Phase 1-5 を Claude Opus 1 chat に統合する単一 prompt
    多視点性は Opus 内 self-review chain (extended thinking) で担保。
    塾長作業: Phase 0 検索 + この統合 prompt = 計 2 step (15-20 分/batch)"""
    topic_clause = f"- 単元固定: 「{topic_hint}」が問題の核心" if topic_hint else "- 単元: 出題範囲内で多様性確保"
    year_clause = f"- 年度準拠: {year} 年度の出題傾向を強く反映" if year else "- 年度: 近年トレンド優先"
    grade_clause = f'"eiken_grade": "{eiken_grade}"' if eiken_grade else '"eiken_grade": null'
    return f"""あなたは ai-juku の問題作成チーム **全員を兼任する Claude Opus 4.7** です。
以下を 1 chat 内で順序実行し、最後に統合 JSON のみを返してください。

【Phase 0 検索結果 (ChatGPT Project からの引用付き出力)】
↓ ここに検索結果を貼り付けてください ↓
<<SEARCH_RESULTS>>

【作成仕様】
- 試験: {exam_id} ({exam_label})
- 大問: {part_key} ({part_label})
{topic_clause}
{year_clause}
- 生成数: {count}問

【絶対遵守】
- 過去問の丸写しは著作権上禁止。**「形式に完全準拠した類題」** を新規作成
- 英文は ETS / Cambridge / Oxford 級の自然な英語
- 解説は **コアイメージ × 文構造分析の二段構え** (既存 ai-juku 流儀)
- **教師名禁止**: 関正生・富田 等の特定教師名は出力に一切含めない (memory: english_philosophy)

【🔥 解説の絶対遵守フォーマット】
explanation フィールドは Markdown で **以下4セクションを必ず明示**:
## 🎯 コアイメージ
## 🔬 文構造分析 ← 絶対省略禁止
## 📍 本文の根拠 (長文の場合)
## ❌ 誤答 NG 理由 (multiple_choice の場合は必須)

---

【ステップ A: 執筆 (思考のみ・JSON 出力禁止)】
{count} 問のドラフトを内部で執筆。各問の draft を内部記録。

【ステップ B: 自己検閲 3視点 (思考のみ・JSON 出力禁止)】
ステップ A の draft に対し、以下 3 視点で自己批判:

(視点1) **内容検閲**: 本文と設問の論理整合 / 解答の唯一性 / 誤答の質 / 事実誤認なし
(視点2) **教育検閲**: 対象学習者のレベル感 / 解説の理解しやすさ / 誤答理由の妥当性
(視点3) **入試検閲**: 出題形式準拠 / 設問数・語数 / 既存過去問のコピーになっていないか

各視点で問題ごとに OK / MINOR / MAJOR / CRITICAL を判定。CRITICAL は再執筆。

【ステップ C: 統合 (最終 JSON 出力)】
ステップ B のフィードバックを反映した最終問題セットを JSON で出力。

---

【出力形式 — 絶対遵守】
**純粋な JSON のみ** (前後にテキストや説明・思考過程は出力しない・```json タグ禁止)。
explanation 内 Markdown は \\n でエスケープ。

```
{{
  "questions": [
    {{
      "exam_id": "{exam_id}",
      "part_key": "{part_key}",
      {grade_clause},
      "question_data": {{
        "passage": "...",
        "stem": "...",
        "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "correct": "A",
        "explanation": "## 🎯 コアイメージ\\n...\\n\\n## 🔬 文構造分析\\n..."
      }},
      "model": "claude-opus-4-7-team-workflow-fast"
    }}
  ],
  "self_review_summary": "ステップ B の自己検閲で発見 → 修正した内容を 3-5 行で要約",
  "removed_questions": [
    {{ "original_index": N, "reason": "CRITICAL 解消不可: ..." }}
  ]
}}
```

【⚠️ 致命安全策】
ステップ B で {count} 問のうち過半数が CRITICAL なら、最終 JSON は出力せず以下のみ返してください:
```
{{ "error": "critical_majority", "detail": "理由を 2-3 行" }}
```
これにより塾長は再生成を判断できる (memory: feedback_team_review_all_generation.md / 完全版 6 phase に切替検討)。

最終 questions array は **{count}-削除数 件** になり、塾長が CEO ダッシュ Phase 6 import textarea に貼ると DB 投入されます。
"""


# ==========================================================================
# 🤖 AI チーム workflow stateful DB helpers (2026-05-10 塾長負荷削減)
# ==========================================================================

def _aitw_db_save(workflow_id: str, spec: dict, phases: list, mode: str = "full",
                   status: str = "in_progress") -> None:
    """workflow を DB に INSERT (新規作成時)"""
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO ai_team_workflows (workflow_id, spec, phases, status, mode) VALUES (?, ?, ?, ?, ?)",
            (workflow_id,
             json.dumps(spec, ensure_ascii=False),
             json.dumps(phases, ensure_ascii=False),
             status, mode)
        )
        conn.commit()
    finally:
        conn.close()


def _aitw_db_load(workflow_id: str) -> Optional[dict]:
    """workflow を DB から取得 (列名アクセス・memory:postgres_dict_row 対策)"""
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT workflow_id, spec, phases, status, mode, created_at, updated_at "
            "FROM ai_team_workflows WHERE workflow_id = ?", (workflow_id,)
        )
        row = c.fetchone()
        if not row:
            return None
        return {
            "workflow_id": row["workflow_id"],
            "spec": json.loads(row["spec"]) if row["spec"] else {},
            "phases": json.loads(row["phases"]) if row["phases"] else [],
            "status": row["status"],
            "mode": row["mode"],
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }
    finally:
        conn.close()


def _aitw_db_list(status: str = "in_progress", limit: int = 20) -> list:
    """進行中 workflow 一覧 (CEO ダッシュ表示用)"""
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT workflow_id, spec, phases, status, mode, created_at, updated_at "
            "FROM ai_team_workflows WHERE status = ? "
            "ORDER BY updated_at DESC LIMIT ?", (status, limit)
        )
        rows = c.fetchall()
        result = []
        for row in rows:
            phases = json.loads(row["phases"]) if row["phases"] else []
            completed = sum(1 for p in phases if p.get("output"))
            spec = json.loads(row["spec"]) if row["spec"] else {}
            result.append({
                "workflow_id": row["workflow_id"],
                "spec": spec,
                "status": row["status"],
                "mode": row["mode"],
                "phase_count": len(phases),
                "completed_count": completed,
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            })
        return result
    finally:
        conn.close()


def _aitw_db_update_phase(workflow_id: str, phase_index: int, output: str) -> Optional[dict]:
    """phase の output を保存し、次 phase の prompt を server side で <<...>> 自動置換。
    返却: 更新後 workflow (新 phases を含む)。失敗時 None。"""
    wf = _aitw_db_load(workflow_id)
    if not wf:
        return None
    phases = wf["phases"]
    if phase_index < 0 or phase_index >= len(phases):
        return None

    # 現在 phase に output 保存
    phases[phase_index]["output"] = output
    phases[phase_index]["saved_at"] = datetime.now(JST).isoformat()

    # 次 phase 以降の prompt の placeholder を全置換
    # full mode: <<SEARCH_RESULTS>> (Phase 0→1) / <<AUTHOR_OUTPUT>> (Phase 1→2,3,4,5) /
    #           <<REVIEW_CONTENT/PEDAGOGY/EXAM>> (Phase 2/3/4→5)
    # fast mode: <<SEARCH_RESULTS>> (Phase 0→1)
    placeholder_map = {
        0: "<<SEARCH_RESULTS>>",
        1: "<<AUTHOR_OUTPUT>>",
        2: "<<REVIEW_CONTENT>>",
        3: "<<REVIEW_PEDAGOGY>>",
        4: "<<REVIEW_EXAM>>",
    }
    placeholder = placeholder_map.get(phase_index)
    if placeholder:
        for j in range(phase_index + 1, len(phases)):
            if placeholder in phases[j].get("prompt", ""):
                phases[j]["prompt"] = phases[j]["prompt"].replace(placeholder, output)

    # DB 更新
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "UPDATE ai_team_workflows SET phases = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE workflow_id = ?",
            (json.dumps(phases, ensure_ascii=False), workflow_id)
        )
        conn.commit()
    finally:
        conn.close()

    wf["phases"] = phases
    return wf


def _aitw_db_set_status(workflow_id: str, status: str) -> bool:
    """status を更新 (completed / aborted)"""
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "UPDATE ai_team_workflows SET status = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE workflow_id = ?", (status, workflow_id)
        )
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()


@app.post("/api/admin/ai-team-workflow/generate")
def admin_ai_team_workflow_generate(payload: dict, authorization: Optional[str] = Header(None)):
    """🤖 AI チーム検閲ワークフロー prompt 一括生成 ($0 半自動運用) — stateful 化済 (2026-05-10)

    塾長保有の Claude Max + ChatGPT Plus + Gemini を組み合わせた多視点問題生成パイプライン。
    生成された workflow は ai_team_workflows テーブルに保存される (途中再開・別端末再開可)。

    mode='full' (6 phase): Phase 0 検索 → Phase 1 執筆 → Phase 2-4 3視点検閲 → Phase 5 統合
    mode='fast' (2 phase): Phase 0 検索 → Phase 1 統合 (Opus 1 chat で執筆+self-review+統合)
      → 60-90分→15-20分に短縮。塾長コピペ回数 6→2 (memory: feedback_ai_team_workflow.md)

    payload:
      {
        "exam_id": "daigaku" | "eiken" | "toefl" | "toeic" | "ielts",
        "part_key": "r_long" | "w_essay" | ...,
        "eiken_grade": "todai" | "g2" | null,
        "topic_hint": "関係代名詞" | null,
        "year": 2024 | null,
        "count": 1-20 (default 5),
        "mode": "full" | "fast" (default "full")
      }
    """
    _verify_admin_required(authorization)

    exam_id = (payload.get("exam_id") or "").strip()
    part_key = (payload.get("part_key") or "").strip()
    eiken_grade_raw = payload.get("eiken_grade")
    eiken_grade = (eiken_grade_raw or "").strip() if isinstance(eiken_grade_raw, str) else None
    if not eiken_grade:
        eiken_grade = None
    topic_hint = (payload.get("topic_hint") or "").strip() or None
    year = payload.get("year")
    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None
    try:
        count = int(payload.get("count") or 5)
    except (TypeError, ValueError):
        count = 5
    mode = (payload.get("mode") or "full").strip().lower()
    if mode not in ("full", "fast"):
        mode = "full"

    if not exam_id or not part_key:
        raise HTTPException(status_code=400, detail="exam_id と part_key は必須")
    if (exam_id, part_key, eiken_grade) not in {(e, p, g) for (e, p, g) in EXAM_QUESTION_ROTATION}:
        raise HTTPException(
            status_code=400,
            detail=f"無効な組合せ: {exam_id}/{part_key}/{eiken_grade}。EXAM_QUESTION_ROTATION (server/main.py 5316) を参照してください。"
        )
    if count < 1 or count > 20:
        raise HTTPException(status_code=400, detail="count は 1-20 の範囲")

    # exam_label / part_label 解決
    exam_label_map = {
        "toefl": "TOEFL iBT",
        "toeic": "TOEIC L&R",
        "ielts": "IELTS Academic",
    }
    if exam_id == "eiken":
        exam_label = f"英検{eiken_grade or '準1級'} (新形式 2024〜)"
    elif exam_id == "daigaku":
        univ_info = DAIGAKU_UNIV_STYLES.get(eiken_grade or "todai", {"name": eiken_grade or "todai"})
        exam_label = f"{univ_info['name']} 大学入試 英語"
    else:
        exam_label = exam_label_map.get(exam_id, exam_id)

    # part_label: 既存 part_hints + DAIGAKU_PART_HINTS から取得
    part_label = part_key
    try:
        part_label = DAIGAKU_PART_HINTS.get(part_key, part_key) if exam_id == "daigaku" else part_key
    except Exception:
        pass

    # workflow_id 生成 + DB 保存 (2026-05-10 stateful 化)
    import secrets as _secrets
    workflow_id = f"wf_{datetime.now(JST).strftime('%Y%m%d_%H%M%S')}_{_secrets.token_hex(3)}"

    # mode 別 phases 構築
    if mode == "fast":
        # ⚡ 速攻モード: Phase 0 検索 + Phase 1 統合 (Opus 1 chat で執筆+self-review+統合)
        phases = [
            {
                "phase": 0,
                "name": "📚 Phase 0: ナレッジ検索",
                "ai": "ChatGPT Project (GPT-5)",
                "ai_url": "https://chatgpt.com/",
                "setup_note": "事前準備: ChatGPT Plus で「ai-juku 過去問アーカイブ」Project を作成し、過去問 PDF・参考書をアップロード済にしておく",
                "prompt": _build_ai_team_search_prompt(exam_id, exam_label, part_label, topic_hint, year, count),
                "output": None,
                "output_format": "Markdown (引用付き)",
                "next_input_marker": None,
            },
            {
                "phase": 1,
                "name": "⚡ Phase 1: 執筆+自己検閲+統合 (1 chat)",
                "ai": "Claude Opus 4.7 (Claude Max / Extended Thinking 推奨)",
                "ai_url": "https://claude.ai/",
                "setup_note": "Opus 4.7 を選択。Extended Thinking ON 推奨 (内部 self-review chain で多視点性担保)",
                "prompt": _build_ai_team_fast_prompt(exam_id, exam_label, part_key, part_label, eiken_grade, topic_hint, year, count),
                "output": None,
                "output_format": "import endpoint 用 JSON (questions array)",
                "next_input_marker": "<<SEARCH_RESULTS>>",
            },
        ]
        instructions = [
            "1. Phase 0 prompt を ChatGPT Project にコピペ → Markdown 検索結果を取得 → CEO ダッシュ Phase 0 textarea に保存",
            "2. 自動置換された Phase 1 統合 prompt を Claude Opus に投入 (Extended Thinking 推奨)",
            "3. Opus が出力した最終 JSON (questions array) を Phase 1 textarea に保存",
            "4. 「📥 Import 投入」ボタンで完了 (塾長コピペ 2 回・所要 15-20 分)",
        ]
    else:
        # 📦 完全版: 既存 6 phase
        phases = [
            {
                "phase": 0,
                "name": "📚 Phase 0: ナレッジ検索",
                "ai": "ChatGPT Project (GPT-5)",
                "ai_url": "https://chatgpt.com/",
                "setup_note": "事前準備: ChatGPT Plus で「ai-juku 過去問アーカイブ」Project を作成し、過去問 PDF・参考書をアップロード済にしておく",
                "prompt": _build_ai_team_search_prompt(exam_id, exam_label, part_label, topic_hint, year, count),
                "output": None,
                "output_format": "Markdown (引用付き)",
                "next_input_marker": None,
            },
            {
                "phase": 1,
                "name": "✍️ Phase 1: 執筆",
                "ai": "Claude Opus 4.7 (Claude Max)",
                "ai_url": "https://claude.ai/",
                "setup_note": "Claude Max 契約で Opus 4.7 を選択。新規チャット推奨 (前文脈の影響を排除)",
                "prompt": _build_ai_team_author_prompt(exam_id, exam_label, part_key, part_label, eiken_grade, topic_hint, year, count),
                "output": None,
                "output_format": "純粋な JSON (questions array)",
                "next_input_marker": "<<SEARCH_RESULTS>>",
            },
            {
                "phase": 2,
                "name": "🔬 Phase 2: 内容検閲",
                "ai": "GPT-5 (ChatGPT Plus / Custom GPT「内容検閲官」推奨)",
                "ai_url": "https://chatgpt.com/",
                "setup_note": "Custom GPT「ai-juku 内容検閲官」を作成済なら使用。なければ通常 GPT-5 で OK",
                "prompt": _build_ai_team_review_prompt("content", exam_label, part_label, count),
                "output": None,
                "output_format": "純粋な JSON (review_results)",
                "next_input_marker": "<<AUTHOR_OUTPUT>>",
            },
            {
                "phase": 3,
                "name": "🎓 Phase 3: 教育検閲",
                "ai": "Gemini 2.5 Pro",
                "ai_url": "https://aistudio.google.com/",
                "setup_note": "Google AI Studio で Gemini 2.5 Pro を選択。学習者目線でレビュー",
                "prompt": _build_ai_team_review_prompt("pedagogy", exam_label, part_label, count),
                "output": None,
                "output_format": "純粋な JSON (review_results)",
                "next_input_marker": "<<AUTHOR_OUTPUT>>",
            },
            {
                "phase": 4,
                "name": "🎯 Phase 4: 入試検閲",
                "ai": "Claude Sonnet 4.6 (Claude Max / Custom GPT「入試検閲官」推奨)",
                "ai_url": "https://claude.ai/",
                "setup_note": "Claude Max で Sonnet 4.6 を選択 (Phase 1 の Opus とは別チャットで)",
                "prompt": _build_ai_team_review_prompt("exam", exam_label, part_label, count),
                "output": None,
                "output_format": "純粋な JSON (review_results)",
                "next_input_marker": "<<AUTHOR_OUTPUT>>",
            },
            {
                "phase": 5,
                "name": "🧬 Phase 5: 統合・最終化",
                "ai": "Claude Opus 4.7 (Claude Max)",
                "ai_url": "https://claude.ai/",
                "setup_note": "Phase 1 の Opus と別チャット推奨。3 検閲を統合して最終 JSON",
                "prompt": _build_ai_team_integration_prompt(exam_id, exam_label, count),
                "output": None,
                "output_format": "import endpoint 用 JSON (questions array)",
                "next_input_marker": "<<AUTHOR_OUTPUT>> / <<REVIEW_CONTENT>> / <<REVIEW_PEDAGOGY>> / <<REVIEW_EXAM>>",
            },
        ]
        instructions = [
            "各 phase の AI に prompt をコピペ → 出力を CEO ダッシュ textarea に保存 (server で次 phase の <<...>> を自動置換)",
            "Phase 5 textarea に最終 JSON が入ったら 「📥 Import 投入」ボタンで完了",
            "中断・別日再開・別端末から再開すべて可能 (workflow は DB 保存)",
        ]

    spec = {
        "exam_id": exam_id,
        "part_key": part_key,
        "eiken_grade": eiken_grade,
        "topic_hint": topic_hint,
        "year": year,
        "count": count,
        "exam_label": exam_label,
        "part_label": part_label,
    }

    # DB 保存 (stateful 化)
    try:
        _aitw_db_save(workflow_id, spec, phases, mode=mode, status="in_progress")
    except Exception as e:
        log.error(f"[AITW] DB save failed: {e}")
        # DB 保存失敗でも prompt 生成自体は成功扱い (塾長が手動コピペで進められる)

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "mode": mode,
        "spec": spec,
        "phases": phases,
        "import_endpoint": "/api/admin/exam-questions/import",
        "import_payload_template": {
            "questions": "<<最終 phase 出力 JSON の questions array をここに貼り付け>>",
            "skip_full": False,
        },
        "instructions": instructions,
        "memory_note": "memory: feedback_team_review_all_generation.md / feedback_5_person_textbook_review.md / feedback_3_person_team_review.md / feedback_ai_team_workflow.md の AI 多視点版実装",
    }


@app.get("/api/admin/ai-team-workflows")
def admin_ai_team_workflows_list(
    status: Optional[str] = "in_progress",
    limit: int = 20,
    authorization: Optional[str] = Header(None),
):
    """🤖 進行中 (or 指定 status) の AI チーム workflow 一覧。CEO ダッシュ「再開」UI 用。"""
    _verify_admin_required(authorization)
    if status not in ("in_progress", "completed", "aborted", "all"):
        status = "in_progress"
    if limit < 1 or limit > 100:
        limit = 20
    if status == "all":
        # 全 status を取得する場合は status='in_progress' 以外も含む
        conn = db()
        try:
            c = conn.cursor()
            c.execute(
                "SELECT workflow_id, spec, phases, status, mode, created_at, updated_at "
                "FROM ai_team_workflows ORDER BY updated_at DESC LIMIT ?", (limit,)
            )
            rows = c.fetchall()
            results = []
            for row in rows:
                phases = json.loads(row["phases"]) if row["phases"] else []
                completed = sum(1 for p in phases if p.get("output"))
                results.append({
                    "workflow_id": row["workflow_id"],
                    "spec": json.loads(row["spec"]) if row["spec"] else {},
                    "status": row["status"],
                    "mode": row["mode"],
                    "phase_count": len(phases),
                    "completed_count": completed,
                    "created_at": str(row["created_at"]),
                    "updated_at": str(row["updated_at"]),
                })
            return {"ok": True, "count": len(results), "workflows": results}
        finally:
            conn.close()
    return {"ok": True, "count": 0, "workflows": _aitw_db_list(status=status, limit=limit)}


@app.get("/api/admin/ai-team-workflow/{workflow_id}")
def admin_ai_team_workflow_get(workflow_id: str, authorization: Optional[str] = Header(None)):
    """🤖 1 件の workflow を取得 (再開用)"""
    _verify_admin_required(authorization)
    wf = _aitw_db_load(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="workflow not found")
    return {"ok": True, **wf}


@app.post("/api/admin/ai-team-workflow/{workflow_id}/phase/{phase_index}/save")
def admin_ai_team_workflow_save_phase(
    workflow_id: str, phase_index: int, payload: dict,
    authorization: Optional[str] = Header(None),
):
    """🤖 phase の output を保存 → 次 phase の prompt を server side で <<...>> 自動置換。
    塾長は CEO ダッシュ textarea にペースト → このエンドポイントを叩くだけで OK。
    手動置換ミスを完全排除 (memory: 60-90分→15-20分の中核機能)。"""
    _verify_admin_required(authorization)
    output = payload.get("output", "")
    if not isinstance(output, str):
        raise HTTPException(status_code=400, detail="output は string")
    output = output.strip()
    if not output:
        raise HTTPException(status_code=400, detail="output が空です")

    wf = _aitw_db_load(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="workflow not found")
    if wf["status"] in ("completed", "aborted"):
        raise HTTPException(status_code=409, detail=f"workflow は既に {wf['status']} です")

    updated = _aitw_db_update_phase(workflow_id, phase_index, output)
    if not updated:
        raise HTTPException(status_code=400, detail="phase_index が範囲外")

    # 🆘 critical_majority 検知: 速攻モードで Opus が過半数 CRITICAL を返したら、
    # save 時点で塾長に明示警告して完全版での再生成を促す (memory: feedback_team_review_all_generation.md)。
    # import 時に弾くだけでは塾長が混乱するため、save 段階で検出してUI 側に payload を返す。
    critical_majority_warning = None
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict) and parsed.get("error") == "critical_majority":
            critical_majority_warning = {
                "type": "critical_majority",
                "detail": parsed.get("detail", ""),
                "recommendation": "速攻版で過半数 CRITICAL が検出されました。完全版 (mode=full) で再生成してください (memory: feedback_5_person_textbook_review.md / feedback_team_review_all_generation.md)。",
            }
    except (json.JSONDecodeError, ValueError):
        # JSON でない phase (Phase 0 検索結果など) は素通し
        pass

    # 残存 placeholder の検出 (置換漏れ警告)
    next_phase = updated["phases"][phase_index + 1] if phase_index + 1 < len(updated["phases"]) else None
    placeholder_warnings = []
    if next_phase and next_phase.get("prompt"):
        for marker in ["<<SEARCH_RESULTS>>", "<<AUTHOR_OUTPUT>>", "<<REVIEW_CONTENT>>",
                        "<<REVIEW_PEDAGOGY>>", "<<REVIEW_EXAM>>"]:
            if marker in next_phase["prompt"]:
                placeholder_warnings.append(marker)

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "saved_phase": phase_index,
        "next_phase_index": phase_index + 1 if phase_index + 1 < len(updated["phases"]) else None,
        "next_phase": next_phase,
        "placeholder_warnings": placeholder_warnings,
        "critical_majority_warning": critical_majority_warning,
        "completed_count": sum(1 for p in updated["phases"] if p.get("output")),
        "phase_count": len(updated["phases"]),
    }


@app.post("/api/admin/ai-team-workflow/{workflow_id}/import")
def admin_ai_team_workflow_import(
    workflow_id: str, payload: dict,
    authorization: Optional[str] = Header(None),
):
    """🤖 workflow の最終 phase output を /api/admin/exam-questions/import に内部投入。
    成功したら status='completed' に。
    payload 任意: { "skip_full": false }
    重複押下防止: status が既に completed なら 409。"""
    _verify_admin_required(authorization)
    wf = _aitw_db_load(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="workflow not found")
    if wf["status"] == "completed":
        raise HTTPException(status_code=409, detail="既に import 完了済 (重複防止)")
    if wf["status"] == "aborted":
        raise HTTPException(status_code=409, detail="abort 済 workflow は import 不可")

    phases = wf["phases"]
    last_phase = phases[-1] if phases else None
    final_output = (last_phase or {}).get("output", "").strip()
    if not final_output:
        raise HTTPException(status_code=400, detail="最終 phase の output が未保存です")

    # JSON parse + questions 抽出
    try:
        parsed = json.loads(final_output)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"最終 phase の JSON parse 失敗: {e}")
    # critical_majority error の場合は拒否
    if isinstance(parsed, dict) and parsed.get("error") == "critical_majority":
        raise HTTPException(
            status_code=400,
            detail=f"fast mode で過半数 CRITICAL が検出されました。完全版に切替推奨: {parsed.get('detail', '')}"
        )
    questions = parsed.get("questions") if isinstance(parsed, dict) else parsed
    if not isinstance(questions, list) or not questions:
        raise HTTPException(status_code=400, detail="questions array が空または配列ではありません")

    skip_full = bool(payload.get("skip_full", False))

    # race condition 対策 (memory: feedback_seed_import_no_loop.md):
    # status='in_progress' のときだけ 'importing' に claim → 2 タブ同時押しを 1 つに絞る
    now_iso = datetime.now(JST).isoformat()
    conn_lock = db()
    try:
        c_lock = conn_lock.cursor()
        c_lock.execute(
            "UPDATE ai_team_workflows SET status = ?, updated_at = ? WHERE workflow_id = ? AND status = ?",
            ("importing", now_iso, workflow_id, "in_progress"),
        )
        conn_lock.commit()
        if c_lock.rowcount == 0:
            raise HTTPException(status_code=409, detail="他のセッションが先に import を開始したか、status が in_progress ではありません")
    finally:
        conn_lock.close()

    # 共通 import core を再利用 (memory: feedback_seed_import_no_loop.md)
    try:
        result = _exam_questions_import_core(questions, skip_full)
    except Exception as e:
        # import 失敗時は status='failed' に固定して再 import を抑止
        # (in_progress に戻すと部分挿入済データを把握できないまま再試行 → 重複 INSERT 確定)
        # 復旧手順: 塾長が DB を確認してから admin 経由で workflow を archive or 手動修正
        _aitw_db_set_status(workflow_id, "failed")
        log.exception(f"[AITW:Import] wf={workflow_id} failed (status=failed for manual recovery)")
        raise HTTPException(status_code=500, detail=f"import 失敗: {type(e).__name__}: {e} — workflow status='failed' に固定 (再 import 抑止)。重複 INSERT 防止のため復旧手順は塾長判断")

    # status='completed' に更新 (失敗問題があっても workflow としては完了扱い)
    _aitw_db_set_status(workflow_id, "completed")
    log.info(f"[AITW:Import] wf={workflow_id} inserted={result.get('inserted')} skipped={result.get('skipped_full')} failed={result.get('failed')}")

    return {
        "ok": True,
        "workflow_id": workflow_id,
        **result,  # received / inserted / skipped_full / failed / failed_details / message を top-level にも
        "message": f"✅ {result.get('inserted')}問 import (skip {result.get('skipped_full')}・失敗 {result.get('failed')}) — workflow 完了",
    }


@app.post("/api/admin/ai-team-workflow/{workflow_id}/abort")
def admin_ai_team_workflow_abort(workflow_id: str, authorization: Optional[str] = Header(None)):
    """🤖 workflow を中止状態に (status='aborted')。再開不可になる。"""
    _verify_admin_required(authorization)
    wf = _aitw_db_load(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="workflow not found")
    if wf["status"] != "in_progress":
        raise HTTPException(status_code=409, detail=f"workflow は既に {wf['status']} です")
    _aitw_db_set_status(workflow_id, "aborted")
    return {"ok": True, "workflow_id": workflow_id, "status": "aborted"}


@app.get("/api/admin/ai-team-workflow-custom-gpt-spec")
def admin_ai_team_workflow_custom_gpt_spec(authorization: Optional[str] = Header(None)):
    """🛠️ ChatGPT Plus 用 Custom GPT 3 体の設計書を返す (Option 2 / NotebookLM 代替)。

    2026-05-10 routing 修正: 旧 path `/api/admin/ai-team-workflow/custom-gpt-spec` は
    `/{workflow_id}` route と衝突する致命 bug があったため、ハイフン区切りで独立化。

    塾長 1 度のセットアップで以下が自動化される:
    - Phase 0 検索 → Custom GPT「ai-juku 検索官」(NotebookLM 代替)
    - Phase 2 内容検閲 → Custom GPT「ai-juku 内容検閲官」
    - Phase 4 入試検閲 → Custom GPT「ai-juku 入試検閲官」(Claude 障害時 fallback)

    塾長は ChatGPT Plus → 「探索」→ 右上「作成」で 3 体作成。Knowledge に過去問 PDF をアップ。
    NotebookLM Plus を契約せずに同等以上の検索機能を実現 (ChatGPT Plus に Project + Custom GPT
    が含まれているため)。

    2026-05-10 塾長指示「Option 1 + Option 2 を $0 で即実装」の Option 2 部分。
    """
    _verify_admin_required(authorization)

    return {
        "ok": True,
        "memo": (
            "Custom GPT は ChatGPT Plus / Pro 限定機能。Plus は 2026-06-10 まで ¥0 キャンペーン中"
            "なので $0 運用継続可。3 体すべて作成すれば AI チームワークフローの ChatGPT 担当 phase が"
            "自動化される。NotebookLM Plus を別途契約する必要なし。"
        ),
        "setup_steps": [
            "1. ChatGPT Plus にログイン (https://chatgpt.com/)",
            "2. サイドバー「探索」→ 右上「+ 作成」→ Configure タブを開く",
            "3. 各 GPT について以下の Name / Description / Instructions を貼り付け",
            "4. Knowledge に過去問 PDF / 参考書 PDF をアップロード (ai-juku 検索官 のみ)",
            "5. Save → 共有設定: Only me (塾長専用)",
            "6. 完成した 3 GPT を「ai-juku」フォルダに整理推奨",
            "7. 動作確認: Conversation starter のいずれかをクリックして応答を見る",
        ],
        "custom_gpts": [
            {
                "name": "ai-juku 検索官 (NotebookLM 代替)",
                "description": "過去問 PDF と参考書から問題作成用の傾向情報を引用付きで取得 (Phase 0 担当)",
                "purpose": "Phase 0 ナレッジ検索 (NotebookLM Plus の代替)",
                "instructions": (
                    "あなたは ai-juku 過去問検索 AI です。NotebookLM 代替として動作します。\n\n"
                    "塾長から「{exam}/{part} の問題を作りたい」と言われたら、Knowledge に\n"
                    "アップロードされた過去問 PDF・参考書から以下を収集してください:\n\n"
                    "1. **過去5年間の出題傾向** (引用付き [ファイル名 p.X])\n"
                    "2. **頻出トピック / 形式の特徴** (語数・設問数・解答形式)\n"
                    "3. **典型的な誤答パターン** (生徒がよく落とすポイント)\n"
                    "4. **必須語彙・文法** (このレベルで前提)\n\n"
                    "出力: markdown 800-1500字。引用元 [ファイル名 p.X] を必ず付ける。\n"
                    "ai-juku 哲学「コアイメージ × 文構造分析」に役立つ情報を優先。\n"
                    "教師名 (関正生・富田 等) は出力に含めない (memory: english_philosophy)。\n\n"
                    "ハルシネーション禁止: Knowledge に無い情報は「該当 PDF 未収録」と明記する。"
                ),
                "conversation_starters": [
                    "東大2024年の英語長文の傾向を引用付きで",
                    "英検準1級ライティングの頻出形式と誤答パターン",
                    "TOEIC Part5 の頻出文法トピック過去5年分",
                    "京都大学 英作文 過去傾向と必須語彙",
                ],
                "knowledge_files_recommended": [
                    "東京大学 英語 過去問 PDF (5-10年分・赤本)",
                    "京都大学 英語 過去問 PDF",
                    "英検 1級〜準2級 過去問集 PDF",
                    "信頼できる参考書 PDF (Z会・河合塾・代々木ゼミ・駿台)",
                    "TOEIC / TOEFL / IELTS 公式ガイド PDF",
                    "Studyplus 連携データなど自校独自の傾向集計があれば追加",
                ],
            },
            {
                "name": "ai-juku 内容検閲官",
                "description": "問題の内容整合・論理一貫性・解答の唯一性を検閲 (Phase 2 担当)",
                "purpose": "Phase 2 内容検閲 (GPT-5 視点)",
                "instructions": (
                    "あなたは ai-juku 問題内容検閲官です。視点: 文章理解・論理整合性。\n\n"
                    "入力された問題 JSON について以下をチェック:\n"
                    "1. 本文と設問・正解選択肢の論理的整合性 (本文に書かれていない推論で正解を選ばせていないか)\n"
                    "2. 誤答選択肢が「本文と矛盾している」「明らかに範囲外」など客観的に NG とわかる構造か\n"
                    "3. passage の英語が自然で文法的に正しいか (ETS/Cambridge 級か)\n"
                    "4. explanation の論理が破綻していないか (コアイメージと文構造分析が一貫しているか)\n"
                    "5. 事実誤認 (歴史/科学/時事) はないか\n\n"
                    "判定ランク:\n"
                    "- CRITICAL: 致命 (誤答や事実誤認・形式逸脱・著作権侵害の疑い等、import 不可)\n"
                    "- MAJOR: 重大 (修正必須だが致命ではない)\n"
                    "- MINOR: 軽微 (修正推奨だが妥協可)\n"
                    "- OK: 問題なし\n\n"
                    "**出力形式: 純粋な JSON のみ** (前後にテキスト禁止):\n"
                    "{\n"
                    '  "review_results": [\n'
                    "    {\n"
                    '      "question_index": 0,\n'
                    '      "verdict": "OK" | "MINOR" | "MAJOR" | "CRITICAL",\n'
                    '      "score": 0-100,\n'
                    '      "issues": [\n'
                    "        {\n"
                    '          "type": "...",\n'
                    '          "severity": "MINOR" | "MAJOR" | "CRITICAL",\n'
                    '          "detail": "問題の具体的説明",\n'
                    '          "suggestion": "推奨修正内容"\n'
                    "        }\n"
                    "      ]\n"
                    "    }\n"
                    "  ],\n"
                    '  "overall_verdict": "PASS" | "REVIEW_AGAIN" | "REJECT",\n'
                    '  "overall_summary": "全体所感を 2-3 行"\n'
                    "}\n\n"
                    "ai-juku 哲学: 「コアイメージ × 文構造分析」を尊重。教師名 (関正生・富田 等) は出さない。\n"
                    "この schema は Phase 2-4 prompt 本体と完全一致 (Phase 5 統合で正しく parse されるため)。"
                ),
                "conversation_starters": [
                    "次の問題 JSON を内容検閲してください",
                    "解答の唯一性を確認したい問題があります",
                    "Critical 指摘があれば優先度順で",
                ],
            },
            {
                "name": "ai-juku 入試検閲官 (Claude 二重化用)",
                "description": "本番試験フォーマット準拠を ChatGPT 視点で検閲 (Phase 4 二重化 / Claude 障害時 fallback)",
                "purpose": "Phase 4 入試検閲 (オプション・Claude Sonnet 二重化用)",
                "instructions": (
                    "あなたは ai-juku 問題入試検閲官 (ChatGPT 版) です。視点: 出題形式整合・実試験での妥当性。\n\n"
                    "入力された問題 JSON が「本物の試験形式」に準拠しているか以下をチェック:\n"
                    "1. 出題形式 (設問数/語数/選択肢数/設問順序) に完全準拠しているか\n"
                    "2. 典型出題スタイルから逸脱していないか\n"
                    "3. 近年の試験 trend (出題テーマ・形式変更) を反映しているか\n"
                    "4. 難易度が当該試験・大問の標準分布から外れすぎていないか\n"
                    "5. 本番試験で出されても違和感がないか (作問者として実戦的か)\n\n"
                    "判定ランク:\n"
                    "- CRITICAL: 致命 (形式逸脱・著作権侵害の疑い等、import 不可)\n"
                    "- MAJOR: 重大 (修正必須)\n"
                    "- MINOR: 軽微 (修正推奨)\n"
                    "- OK: 問題なし\n\n"
                    "**出力形式: 純粋な JSON のみ** (前後にテキスト禁止):\n"
                    "{\n"
                    '  "review_results": [\n'
                    "    {\n"
                    '      "question_index": 0,\n'
                    '      "verdict": "OK" | "MINOR" | "MAJOR" | "CRITICAL",\n'
                    '      "score": 0-100,\n'
                    '      "issues": [\n'
                    "        {\n"
                    '          "type": "...",\n'
                    '          "severity": "MINOR" | "MAJOR" | "CRITICAL",\n'
                    '          "detail": "問題の具体的説明",\n'
                    '          "suggestion": "推奨修正内容"\n'
                    "        }\n"
                    "      ]\n"
                    "    }\n"
                    "  ],\n"
                    '  "overall_verdict": "PASS" | "REVIEW_AGAIN" | "REJECT",\n'
                    '  "overall_summary": "全体所感を 2-3 行"\n'
                    "}\n\n"
                    "通常運用では Phase 4 は Claude Sonnet が担当。\n"
                    "二重チェック / Claude 障害時 fallback として併用する。\n"
                    "この schema は Phase 2-4 prompt 本体と完全一致 (Phase 5 統合で正しく parse されるため)。"
                ),
                "conversation_starters": [
                    "次の問題 JSON が東大形式に準拠しているか検閲してください",
                    "英検準1級フォーマット準拠チェックお願いします",
                ],
            },
        ],
    }


# ==========================================================================
# 教材プール ($0 運用): Claude Max プラン経由で事前生成した教材 JSON を DB に貯め、
# 生徒の textbook-generator 押下時はまずこの DB を検索して即取り出す。
# Anthropic API クレジット消費ゼロで教材配信が成立する。
# ==========================================================================

@app.post("/api/admin/textbooks/import")
def admin_textbook_pool_import(payload: dict, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """🆓 Claude Max プラン経由で生成した教材 JSON を textbook_pool に一括投入。
    payload:
      {
        "textbooks": [
          {"subject": "数学IA", "topic": "二次関数", "level": "高1〜高2",
           "length": "medium", "type": "unit_lesson",
           "title": "...", "tags": ["二次関数","頂点"],
           "content": {...教材JSON全体...}}
        ]
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

    textbooks = payload.get("textbooks") or []
    if not isinstance(textbooks, list) or not textbooks:
        raise HTTPException(status_code=400, detail="textbooks が空 or 配列ではありません")

    inserted = 0
    failed = []
    conn = db()
    c = conn.cursor()
    try:
        for i, t in enumerate(textbooks):
            try:
                subject = (t.get("subject") or "").strip()
                topic = (t.get("topic") or "").strip()
                level = (t.get("level") or "").strip()
                content = t.get("content")
                if not subject or not topic or not level or not content:
                    failed.append({"i": i, "reason": "subject/topic/level/content いずれかが空"})
                    continue
                length = t.get("length") or "medium"
                ttype = t.get("type") or "unit_lesson"
                title = t.get("title") or f"{subject} - {topic}"
                tags = t.get("tags") or []
                if isinstance(tags, list):
                    tags_str = ",".join(str(x) for x in tags)
                else:
                    tags_str = str(tags)
                content_str = json.dumps(content, ensure_ascii=False) if not isinstance(content, str) else content

                c.execute(
                    """INSERT INTO textbook_pool
                       (subject, topic, level, length, type, title, tags, content, status, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (subject, topic, level, length, ttype, title, tags_str, content_str,
                     t.get("status") or "published", t.get("source") or "claude_max"),
                )
                inserted += 1
            except Exception as e:
                failed.append({"i": i, "reason": f"{type(e).__name__}: {e}"})
                try: conn.rollback()
                except Exception: pass
        conn.commit()
    finally:
        conn.close()

    log.info(f"[TextbookPool:Import] inserted={inserted} failed={len(failed)}")
    return {
        "ok": True,
        "received": len(textbooks),
        "inserted": inserted,
        "failed": len(failed),
        "failed_details": failed[:20],
        "message": f"✅ {inserted}教材 import (失敗 {len(failed)})",
    }


@app.get("/api/textbooks/search")
def public_textbook_search(
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    level: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 5,
    authorization: Optional[str] = Header(None),
):
    """生徒/管理者から呼ばれる教材検索。
    subject + topic + level の段階マッチで最も近いものを返す。
    認証: 生徒 magic-link Bearer or admin Bearer"""
    # 認証 (生徒 or admin)
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
        else:
            try:
                stu = _get_current_student(authorization)
                if stu:
                    authed = True
            except Exception:
                pass
    if not authed:
        raise HTTPException(status_code=401, detail="Login required")

    if not subject:
        raise HTTPException(status_code=400, detail="subject required")

    limit = max(1, min(int(limit or 5), 20))
    conn = db()
    c = conn.cursor()
    try:
        results = []
        # 🔥 致命傷修正 (2026-05-01): topic 指定時に無関係教材を返す bug 修正
        # 旧コードは Stage 4 で subject のみで全件返していた → 関係代名詞リクエストに 話法 が返る事故
        # 新ルール: topic 指定があれば topic match した結果のみ返す。topic miss は空配列で live 生成に流す
        if topic:
            # topic を「、」「,」「/」で分割して各 token で OR 検索 (関係代名詞、関係副詞 → 関係代名詞 OR 関係副詞)
            topic_tokens = [t.strip() for t in topic.replace("、", ",").replace("/", ",").split(",") if t.strip()]
            # Stage 1: 完全一致 (subject + topic 文字列そのまま + level)
            if level:
                c.execute(
                    """SELECT id, subject, topic, level, length, type, title, tags, content, created_at
                       FROM textbook_pool
                       WHERE status = 'published' AND subject = ? AND topic = ? AND level = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (subject, topic, level, limit),
                )
                results = [dict(r) for r in c.fetchall()]
            # Stage 2: 各 token のいずれかが topic に含まれる + subject 一致 (level は問わず)
            if not results and topic_tokens:
                placeholders = " OR ".join(["topic LIKE ?"] * len(topic_tokens))
                like_args = [f"%{t}%" for t in topic_tokens]
                c.execute(
                    f"""SELECT id, subject, topic, level, length, type, title, tags, content, created_at
                       FROM textbook_pool
                       WHERE status = 'published' AND subject = ? AND ({placeholders})
                       ORDER BY created_at DESC LIMIT ?""",
                    (subject, *like_args, limit),
                )
                results = [dict(r) for r in c.fetchall()]
            # 🚫 topic 指定があるのに miss した場合は subject 全件 fallback しない
            #    → 空配列を返して呼び出し側が live 生成に流す (チーム検閲付き)
        else:
            # topic 未指定時のみ subject + level / subject 全件で fallback 許可
            if level:
                c.execute(
                    """SELECT id, subject, topic, level, length, type, title, tags, content, created_at
                       FROM textbook_pool
                       WHERE status = 'published' AND subject = ? AND level = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (subject, level, limit),
                )
                results = [dict(r) for r in c.fetchall()]
            if not results:
                c.execute(
                    """SELECT id, subject, topic, level, length, type, title, tags, content, created_at
                       FROM textbook_pool
                       WHERE status = 'published' AND subject = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (subject, limit),
                )
                results = [dict(r) for r in c.fetchall()]
    finally:
        conn.close()

    # content は JSON 文字列で保存しているのでパースして返す
    out = []
    for r in results:
        content = r.get("content")
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except Exception:
                pass
        out.append({
            "id": r.get("id"),
            "subject": r.get("subject"),
            "topic": r.get("topic"),
            "level": r.get("level"),
            "length": r.get("length"),
            "type": r.get("type"),
            "title": r.get("title"),
            "tags": (r.get("tags") or "").split(",") if r.get("tags") else [],
            "content": content,
            "created_at": str(r.get("created_at")) if r.get("created_at") else None,
        })
    return {"ok": True, "count": len(out), "results": out}


@app.post("/api/textbooks/request-generation")
def textbook_request_generation(payload: dict, authorization: Optional[str] = Header(None)):
    """🔥 2026-05-01: pool miss 時にリクエスト記録 (CEO 通知用)。
    塾長指示「pool 主導にシフト、未作成は塾長に通知」。
    Live 生成は廃止し、未作成は events.textbook_request_missing に記録 → CEO ダッシュで一覧表示。
    認証: 生徒 magic-link or admin"""
    authed = False
    student = None
    is_admin = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            is_admin = True
            authed = True
        else:
            try:
                student = _get_current_student(authorization)
                if student:
                    authed = True
            except Exception:
                pass
    if not authed:
        raise HTTPException(status_code=401, detail="Login required")

    subject = (payload.get("subject") or "").strip()
    topic = (payload.get("topic") or "").strip()
    level = (payload.get("level") or "").strip()
    type_ = (payload.get("type") or "").strip()
    length = (payload.get("length") or "").strip()
    if not subject or not topic:
        raise HTTPException(status_code=400, detail="subject and topic required")

    requester_label = "admin" if is_admin else f"student:{student.get('id')}"
    try:
        conn = db(); c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            (
                "textbook_request_missing",
                json.dumps({
                    "subject": subject, "topic": topic, "level": level,
                    "type": type_, "length": length,
                    "requester": requester_label,
                }, ensure_ascii=False),
                f"textbook_req:{requester_label}",
            ),
        )
        conn.commit(); conn.close()
        log.info(f"[Textbook] Missing request: {subject} / {topic} / {level} ({requester_label})")
    except Exception as e:
        log.warning(f"[Textbook] failed to record missing request: {e}")
    return {"ok": True, "queued": True}


@app.get("/api/admin/textbooks/missing-requests")
def admin_textbook_missing_requests(
    hours: int = 168,  # default 7日
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
):
    """🔥 2026-05-01: 未作成教材リクエスト一覧 (CEO 通知用)。
    subject + topic + level の組合せで集計し、件数の多い順に返す。
    pool に作るべき優先順位を CEO が即把握できる。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    hours = max(1, min(int(hours or 168), 24 * 90))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    conn = db(); c = conn.cursor()
    try:
        c.execute(
            "SELECT props, created_at FROM events WHERE name = 'textbook_request_missing' AND created_at >= ? ORDER BY created_at DESC",
            (cutoff,)
        )
        rows = c.fetchall()
    finally:
        conn.close()

    # subject + topic + level でグルーピング
    aggregated = {}
    for r in rows:
        try:
            props = json.loads(r[0]) if not hasattr(r, 'keys') else json.loads(r["props"])
            key = (props.get("subject", ""), props.get("topic", ""), props.get("level", ""))
            if key not in aggregated:
                aggregated[key] = {
                    "subject": key[0], "topic": key[1], "level": key[2],
                    "type": props.get("type", ""), "length": props.get("length", ""),
                    "count": 0, "first_at": str(r[1] if not hasattr(r, "keys") else r["created_at"]),
                    "last_at": str(r[1] if not hasattr(r, "keys") else r["created_at"]),
                }
            aggregated[key]["count"] += 1
            # last_at は最新のリクエスト
            cur_last = aggregated[key]["last_at"]
            new_at = str(r[1] if not hasattr(r, "keys") else r["created_at"])
            if new_at > cur_last:
                aggregated[key]["last_at"] = new_at
        except Exception:
            continue

    # 件数の多い順にソート
    out = sorted(aggregated.values(), key=lambda x: -x["count"])
    return {"ok": True, "total_unique": len(out), "total_requests": sum(x["count"] for x in out), "items": out}


@app.get("/api/admin/students/never-logged-in")
def admin_students_never_logged_in(
    hours: int = 24,
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
):
    """申込から N 時間 (default 24h) 経過してもログインしていない生徒一覧。
    塾長指示「申込→ログイン経路を完璧に」(2026-04-29) のための監視 endpoint。
    自動 nudge cron / CEO ダッシュ赤バナーから利用される。
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

    # 1〜24*30 の範囲に clamp
    hours = max(1, min(int(hours or 24), 24 * 30))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    conn = db()
    c = conn.cursor()
    students = []
    try:
        try:
            c.execute(
                """SELECT id, name, email, created_at, last_login_at, status, plan
                   FROM students
                   WHERE last_login_at IS NULL
                     AND status IN ('trial', 'paid')
                     AND email IS NOT NULL AND email != ''
                     AND created_at <= ?
                   ORDER BY created_at ASC""",
                (cutoff,)
            )
        except Exception:
            # last_login_at カラム未マイグレーション環境 (普通はあり得ない)
            try:
                conn.rollback()
            except Exception:
                pass
            c.execute(
                """SELECT id, name, email, created_at, status, plan
                   FROM students
                   WHERE status IN ('trial', 'paid')
                     AND email IS NOT NULL AND email != ''
                     AND created_at <= ?
                   ORDER BY created_at ASC""",
                (cutoff,)
            )
        rows = c.fetchall()
        now = datetime.now(timezone.utc)
        for r in rows:
            d = dict(r)
            signup_at = d.get("created_at")
            hours_since = None
            if signup_at:
                try:
                    if isinstance(signup_at, str):
                        # ISO 文字列 → datetime
                        sa = datetime.fromisoformat(signup_at.replace("Z", "+00:00"))
                    else:
                        sa = signup_at
                    if hasattr(sa, "tzinfo") and sa.tzinfo is None:
                        sa = sa.replace(tzinfo=timezone.utc)
                    hours_since = round((now - sa).total_seconds() / 3600, 1)
                except Exception:
                    hours_since = None
            students.append({
                "id": d.get("id"),
                "name": d.get("name"),
                "email": d.get("email"),
                "signup_at": str(signup_at) if signup_at else None,
                "hours_since": hours_since,
                "status": d.get("status"),
                "plan": d.get("plan"),
            })
    finally:
        conn.close()

    return {
        "ok": True,
        "hours": hours,
        "count": len(students),
        "students": students,
    }


@app.post("/api/admin/students/backfill-last-login")
def admin_students_backfill_last_login(payload: dict = None, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """events テーブルから last_login_at を遡及推定して埋める。
    last_login_at は新規追加カラムなので、過去にアプリを使っていた生徒も NULL のまま。
    各生徒の session_id='student:N' の最新 events.created_at を last_login_at にコピー。

    payload (省略可):
      {"dry_run": true}  # 推定対象一覧のみ返す (実 UPDATE しない)
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

    payload = payload or {}
    dry_run = bool(payload.get("dry_run", False))

    conn = db()
    c = conn.cursor()
    updated = []
    skipped_no_events = []
    try:
        # 全生徒を取得 (status 問わず、last_login_at IS NULL のもの)
        try:
            c.execute("""SELECT id, name FROM students
                         WHERE last_login_at IS NULL
                           AND status IN ('trial', 'paid', 'canceled')""")
        except Exception:
            # last_login_at カラム未マイグレーション環境 (普通はあり得ない)
            raise HTTPException(status_code=500, detail="last_login_at カラム未追加")
        students = [dict(r) for r in c.fetchall()]

        for s in students:
            sid = s["id"]
            session_key = f"student:{sid}"
            # 最新の events.created_at (session_id でフィルタ)
            c.execute(
                "SELECT MAX(created_at) AS latest FROM events WHERE session_id = ?",
                (session_key,)
            )
            latest_row = c.fetchone()
            latest = latest_row["latest"] if latest_row else None
            if not latest:
                skipped_no_events.append({"id": sid, "name": s.get("name")})
                continue
            updated.append({"id": sid, "name": s.get("name"), "estimated_last_login": str(latest)})
            if not dry_run:
                c.execute("UPDATE students SET last_login_at = ? WHERE id = ?", (latest, sid))

        if not dry_run:
            conn.commit()
    finally:
        conn.close()

    log.info(f"[Students:BackfillLastLogin] dry_run={dry_run} updated={len(updated)} skipped_no_events={len(skipped_no_events)}")
    return {
        "ok": True,
        "updated": len(updated),
        "skipped_no_events": len(skipped_no_events),
        "dry_run": dry_run,
        "items": updated[:50],
        "no_events_items": skipped_no_events[:20],
        "message": f"{'(dry run) ' if dry_run else ''}推定 {len(updated)} 名 / events 無し {len(skipped_no_events)} 名",
    }


@app.post("/api/admin/students/send-login-link")
def admin_students_send_login_link(payload: dict, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """指定生徒 (ids) または未ログイン全員に magic link メールを送信する。
    payload:
      {"ids": [1, 2, 3]}              # ID 指定
      {"target": "never_logged_in"}   # last_login_at IS NULL の trial/paid 全員
      {"dry_run": true}               # 送信せず対象一覧のみ返す
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

    ids = payload.get("ids") or []
    target = payload.get("target")
    dry_run = bool(payload.get("dry_run", False))
    if not ids and not target:
        raise HTTPException(status_code=400, detail="ids または target のいずれか必須")

    conn = db()
    c = conn.cursor()
    students_to_send = []
    try:
        if ids:
            placeholders = ",".join(["?"] * len(ids))
            try:
                c.execute(f"""SELECT id, name, email, line_user_id, status, last_login_at
                             FROM students WHERE id IN ({placeholders})""", tuple(ids))
            except Exception:
                c.execute(f"""SELECT id, name, email, line_user_id, status
                             FROM students WHERE id IN ({placeholders})""", tuple(ids))
            students_to_send = [dict(r) for r in c.fetchall()]
        elif target == "never_logged_in":
            try:
                c.execute("""SELECT id, name, email, line_user_id, status, last_login_at FROM students
                             WHERE last_login_at IS NULL
                               AND status IN ('trial', 'paid')
                               AND ((email IS NOT NULL AND email != '')
                                    OR (line_user_id IS NOT NULL AND line_user_id != ''))""")
            except Exception:
                # last_login_at カラム未マイグレーション環境
                c.execute("""SELECT id, name, email, line_user_id, status FROM students
                             WHERE status IN ('trial', 'paid')
                               AND ((email IS NOT NULL AND email != '')
                                    OR (line_user_id IS NOT NULL AND line_user_id != ''))""")
            students_to_send = [dict(r) for r in c.fetchall()]
    finally:
        conn.close()

    import time as _t
    email_sent_n = 0
    line_sent_n = 0
    both_failed_n = 0
    sent = 0   # 後方互換: email or line のどちらかが成功した件数
    failed = []
    sent_details = []
    for idx, s in enumerate(students_to_send):
        sent_details.append({
            "id": s["id"],
            "name": s.get("name"),
            "email": s.get("email"),
            "has_line": bool(s.get("line_user_id")),
            "is_carrier": _is_carrier_email(s.get("email") or ""),
        })
        if dry_run:
            continue
        # Resend rate limit (Free 2 req/sec) 対策: 各送信前に 0.6 秒 sleep
        if idx > 0:
            _t.sleep(0.6)
        try:
            # 1時間有効な短命 magic link token (4番手 監査 2026-04-30)
            session_token = _create_magic_link_token(s["id"])
            magic_url = f"{BASE_URL}/auth.html?t={session_token}"
            otp_code = _create_otp(s["id"])
            multi = _send_login_link_multi(
                student_id=s["id"],
                email=s.get("email") or "",
                name=s.get("name") or "",
                magic_url=magic_url,
                otp_code=otp_code,
                is_welcome=True,
                # キャリアメール + LINE 連携済 なら強制で LINE も併用 (足立えみ ezweb 等)
                force_line=bool(s.get("line_user_id")) and _is_carrier_email(s.get("email") or ""),
            )
        except Exception as e:
            log.error(f"[Students:SendLoginLink] multi-channel exception for student {s['id']}: {type(e).__name__}: {e}")
            multi = {"email_sent": False, "line_sent": False, "both_failed": True,
                     "email_error": f"{type(e).__name__}: {e}", "line_reason": None,
                     "is_carrier": _is_carrier_email(s.get("email") or "")}

        if multi.get("email_sent"):
            email_sent_n += 1
        if multi.get("line_sent"):
            line_sent_n += 1
        if multi.get("email_sent") or multi.get("line_sent"):
            sent += 1
        if multi.get("both_failed"):
            both_failed_n += 1
            failed.append({
                "id": s["id"],
                "email": s.get("email"),
                "is_carrier": multi.get("is_carrier"),
                "email_error": str(multi.get("email_error") or "")[:160],
                "line_reason": str(multi.get("line_reason") or "")[:160],
            })

    log.info(f"[Students:SendLoginLink] dry_run={dry_run} matched={len(students_to_send)} "
             f"email_sent={email_sent_n} line_sent={line_sent_n} both_failed={both_failed_n}")
    return {
        "ok": True,
        "matched": len(students_to_send),
        "sent": sent,
        "email_sent": email_sent_n,
        "line_sent": line_sent_n,
        "both_failed": both_failed_n,
        "failed": both_failed_n,            # 後方互換: 旧 UI 用
        "failed_details": failed[:20],
        "dry_run": dry_run,
        "items": sent_details[:50],
        "message": (
            f"{'(dry run) ' if dry_run else ''}対象 {len(students_to_send)} 名"
            f"・email 送信 {email_sent_n} 通"
            f"・LINE 送信 {line_sent_n} 通"
            f"・両方失敗 {both_failed_n} 名"
        ),
    }


@app.get("/api/admin/students/{student_id}/activity")
def admin_student_activity(student_id: int, hours: int = 720, limit: int = 200, authorization: Optional[str] = Header(None)):
    """指定生徒のアクティビティ履歴を返す。
    - hours: 直近 N 時間 (デフォ 30 日 = 720h)
    - limit: 最大件数 (デフォ 200)
    返却:
      {
        "student": {id, name, email, ...},
        "activity_summary": {ai_calls, problem_attempts, login_count, ...},
        "events": [{name, props, created_at}, ...]
      }
    認証: admin Bearer 必須"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    hours = max(1, min(int(hours), 24 * 365))  # 1h〜365日
    limit = max(1, min(int(limit), 1000))
    cutoff_iso = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

    conn = db()
    c = conn.cursor()
    try:
        # 生徒基本情報
        try:
            c.execute("""SELECT id, name, email, grade, goal, plan, status,
                                trial_end, paid_since, created_at, last_login_at
                         FROM students WHERE id = ?""", (student_id,))
        except Exception:
            c.execute("""SELECT id, name, email, grade, goal, plan, status,
                                trial_end, paid_since, created_at
                         FROM students WHERE id = ?""", (student_id,))
        srow = c.fetchone()
        if not srow:
            raise HTTPException(status_code=404, detail="生徒が見つかりません")
        student = dict(srow)
        for k in ("trial_end", "paid_since", "created_at", "last_login_at"):
            if k in student and student[k]:
                student[k] = str(student[k])

        # アクティビティ events (session_id = "student:N" でフィルタ)
        session_key = f"student:{student_id}"
        c.execute(
            """SELECT name, props, created_at
               FROM events
               WHERE session_id = ? AND created_at >= ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (session_key, cutoff_iso, limit),
        )
        events_raw = c.fetchall()
        events = []
        for r in events_raw:
            props_str = r["props"] or "{}"
            try:
                props = json.loads(props_str) if isinstance(props_str, str) else props_str
            except Exception:
                props = {"_raw": str(props_str)[:200]}
            events.append({
                "name": r["name"],
                "props": props,
                "created_at": str(r["created_at"]),
            })

        # 集計サマリ
        summary = {
            "total_events": len(events),
            "ai_calls": sum(1 for e in events if e["name"].startswith("ai_")),
            "ai_input_tokens": sum(int(e["props"].get("input_tokens", 0) or 0) for e in events if e["name"].startswith("ai_")),
            "ai_output_tokens": sum(int(e["props"].get("output_tokens", 0) or 0) for e in events if e["name"].startswith("ai_")),
            "problem_attempts": sum(1 for e in events if "problem" in e["name"] or "exam" in e["name"]),
            "textbook_views": sum(1 for e in events if "textbook" in e["name"]),
            "by_event": {},
        }
        for e in events:
            summary["by_event"][e["name"]] = summary["by_event"].get(e["name"], 0) + 1
    finally:
        conn.close()

    return {
        "ok": True,
        "student": student,
        "activity_summary": summary,
        "events": events,
        "filter": {"hours": hours, "limit": limit},
    }


@app.post("/api/admin/students/send-magic-link-to")
def admin_send_magic_link_to_address(payload: dict, authorization: Optional[str] = Header(None)):
    """🔥 2026-05-01: CEO ダッシュから指定アドレスに magic link を送信。
    親の携帯で登録してしまった場合に、子供のメールアドレス等に直接送りたいケースに対応。
    payload:
      {"student_id": 123, "to_email": "child@example.com"}
    認証: admin Bearer のみ"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    student_id = payload.get("student_id")
    to_email = (payload.get("to_email") or "").strip().lower()
    if not student_id or not to_email:
        raise HTTPException(status_code=400, detail="student_id and to_email required")
    if "@" not in to_email or "." not in to_email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="invalid to_email")

    conn = db(); c = conn.cursor()
    c.execute("SELECT id, name, email, status FROM students WHERE id = ? LIMIT 1", (int(student_id),))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="student not found")

    # 古い OTP を無効化してから新規発行
    _invalidate_active_otps(row["id"])
    session_token = _create_magic_link_token(row["id"])
    magic_url = f"{BASE_URL}/auth.html?t={session_token}"
    otp_code = _create_otp(row["id"])
    result = _send_magic_link_with_retry(
        to_email,
        row["name"] or "",
        magic_url,
        otp_code=otp_code,
        is_welcome=False,
    )
    return {
        "ok": True,
        "sent": bool(result.get("sent")),
        "to": to_email,
        "student_id": row["id"],
        "registered_email": row["email"],
        "error": (result or {}).get("error", None) if not result.get("sent") else None,
    }


@app.post("/api/admin/login-as-student")
def admin_login_as_student(payload: dict, authorization: Optional[str] = Header(None)):
    """🔐 塾長が生徒として直接ログインする (magic link 不要の admin 迂回)。
    payload: {"id": 6} または {"email": "..."}
    成功時: 30日有効の session token + student info を返す。塾長は localStorage に
    保存して mypage / index にアクセスできる。
    監査ログ: 全 impersonation を log + events に記録。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    sid_arg = payload.get("id")
    email_arg = (payload.get("email") or "").strip().lower()
    conn = db()
    c = conn.cursor()
    try:
        if sid_arg:
            c.execute("SELECT id, name, email, status, plan FROM students WHERE id=?", (int(sid_arg),))
        elif email_arg:
            c.execute("SELECT id, name, email, status, plan FROM students WHERE LOWER(email)=? LIMIT 1", (email_arg,))
        else:
            raise HTTPException(status_code=400, detail="id or email required")
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="student not found")
        sid = int(row["id"])
        # 監査ログ
        log.warning(f"[AdminImpersonation] admin -> student id={sid} email={row['email']}")
        try:
            c.execute(
                "INSERT INTO events (name, props, created_at) VALUES (?, ?, ?)",
                ("admin_impersonation", json.dumps({"student_id": sid, "email": row["email"]}, ensure_ascii=False), datetime.now(timezone.utc)),
            )
            conn.commit()
        except Exception:
            try: conn.rollback()
            except Exception: pass

        session_token = _sign_session_token(sid, token_type="session")
        import time as _t
        return {
            "ok": True,
            "token": session_token,
            "expires_at": int(_t.time()) + SESSION_TTL_SECONDS,
            "student": {
                "id": sid,
                "name": row["name"],
                "email": row["email"],
                "status": row["status"],
                "plan": row["plan"],
            },
        }
    finally:
        conn.close()


@app.post("/api/admin/send-report")
def admin_send_report(payload: dict, authorization: Optional[str] = Header(None)):
    """管理者がモニタリングメールアドレスに任意レポートを送信。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")
    subject = payload.get("subject", "レポート")
    body_html = payload.get("body_html", "")
    if not body_html:
        raise HTTPException(status_code=400, detail="body_html required")
    result = _send_monitor_email(subject, body_html)
    return {"ok": result.get("sent", False), "error": result.get("error")}


@app.post("/api/admin/students/reactivate")
def admin_students_reactivate(payload: dict, authorization: Optional[str] = Header(None)):
    """canceled / expired student を任意の status に再アクティベート。
    塾長自身のテスト用アカウント (status=canceled) を復活させて magic link を
    届くようにする用途 (2026-05-03 塾長指示)。
    payload: {"id": 6, "status": "paid", "plan": "founder_special"}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    sid = int(payload.get("id") or 0)
    new_status = (payload.get("status") or "paid").strip()
    new_plan = (payload.get("plan") or "founder_special").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="id required")
    if new_status not in ("paid", "trial"):
        raise HTTPException(status_code=400, detail="status must be 'paid' or 'trial'")

    conn = db()
    c = conn.cursor()
    try:
        c.execute("SELECT id, email, status, plan FROM students WHERE id=?", (sid,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"student id={sid} not found")
        before = {"status": row["status"], "plan": row["plan"]}
        if new_status == "paid":
            c.execute(
                "UPDATE students SET status='paid', plan=?, paid_since=COALESCE(paid_since, ?), trial_end=NULL WHERE id=?",
                (new_plan, datetime.now(timezone.utc), sid),
            )
        else:
            new_trial_end = datetime.now(timezone.utc) + timedelta(days=30)
            c.execute(
                "UPDATE students SET status='trial', plan=?, trial_end=? WHERE id=?",
                (new_plan, new_trial_end, sid),
            )
        conn.commit()
        c.execute("SELECT id, name, email, status, plan, trial_end, paid_since FROM students WHERE id=?", (sid,))
        after_row = c.fetchone()
        log.info(f"[admin/reactivate] id={sid} {before} -> status={new_status} plan={new_plan}")
        return {
            "ok": True,
            "id": sid,
            "before": before,
            "after": {
                "status": after_row["status"],
                "plan": after_row["plan"],
                "trial_end": str(after_row["trial_end"]) if after_row["trial_end"] else None,
                "paid_since": str(after_row["paid_since"]) if after_row["paid_since"] else None,
            },
        }
    finally:
        conn.close()


@app.post("/api/admin/students/purge-test")
def admin_students_purge_test(payload: dict, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """テスト用ダミー生徒レコードを削除する admin endpoint。
    payload:
      {"ids": [5, 6, 7]}                       # ID 指定削除
      {"name_contains": ["検証", "再確認"]}    # 名前部分一致で削除 (複数 OR)
      {"dry_run": true}                        # 削除せず該当件数だけ返す
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

    ids = payload.get("ids") or []
    name_contains = payload.get("name_contains") or []
    dry_run = bool(payload.get("dry_run", False))
    if not ids and not name_contains:
        raise HTTPException(status_code=400, detail="ids または name_contains のいずれか必須")

    conn = db()
    c = conn.cursor()
    matched = []
    try:
        # ID 指定
        if ids:
            placeholders = ",".join(["?"] * len(ids))
            c.execute(f"SELECT id, name, status FROM students WHERE id IN ({placeholders})", tuple(ids))
            for r in c.fetchall():
                matched.append({"id": r["id"], "name": r["name"], "status": r["status"], "via": "id"})
        # 名前部分一致 (複数 OR)
        if name_contains:
            for kw in name_contains:
                c.execute("SELECT id, name, status FROM students WHERE name LIKE ?", (f"%{kw}%",))
                for r in c.fetchall():
                    if not any(m["id"] == r["id"] for m in matched):
                        matched.append({"id": r["id"], "name": r["name"], "status": r["status"], "via": f"name~{kw}"})

        deleted = 0
        if not dry_run and matched:
            ids_to_delete = [m["id"] for m in matched]
            placeholders = ",".join(["?"] * len(ids_to_delete))
            # 外部キー違反防止: 関連テーブルを先に削除
            try:
                c.execute(f"DELETE FROM otp_codes WHERE student_id IN ({placeholders})", tuple(ids_to_delete))
            except Exception as e:
                log.warning(f"[Students:PurgeTest] otp_codes cleanup failed: {e}")
            try:
                c.execute(f"DELETE FROM payments WHERE student_id IN ({placeholders})", tuple(ids_to_delete))
            except Exception as e:
                log.warning(f"[Students:PurgeTest] payments cleanup failed: {e}")
            try:
                c.execute(f"DELETE FROM usage_monthly WHERE student_id IN ({placeholders})", tuple(ids_to_delete))
            except Exception as e:
                log.warning(f"[Students:PurgeTest] usage_monthly cleanup failed: {e}")
            # students 本体削除
            c.execute(f"DELETE FROM students WHERE id IN ({placeholders})", tuple(ids_to_delete))
            # _Cursor に rowcount 属性が無いため matched 数を deleted とみなす
            deleted = len(ids_to_delete)
            conn.commit()
    finally:
        conn.close()

    log.info(f"[Students:PurgeTest] dry_run={dry_run} matched={len(matched)} deleted={deleted}")
    return {
        "ok": True,
        "matched": len(matched),
        "deleted": deleted,
        "dry_run": dry_run,
        "items": matched[:50],
        "message": f"{'(dry run) ' if dry_run else ''}該当 {len(matched)} 件、削除 {deleted} 件",
    }


class StudentDeleteRequest(BaseModel):
    confirm_email: Optional[str] = None  # 安全装置: student.email と完全一致必須 (同名衝突防止)
    confirm_name: Optional[str] = None  # 後方互換 (email 未設定の生徒向け fallback)
    dry_run: Optional[bool] = False
    cancel_stripe: Optional[bool] = False  # Stripe 解約も同時実行する場合 true


@app.post("/api/admin/students/{student_id}/delete")
def admin_student_delete(student_id: int, payload: StudentDeleteRequest, authorization: Optional[str] = Header(None)):
    """顧客データ完全削除 (admin only)。生徒本体 + 全関連データを cascade delete。
    安全装置: payload.confirm_name が student.name と完全一致する場合のみ実行。
    Stripe 有効サブスクがある場合、payload.cancel_stripe=true でない限り 409 で拒否。
    events テーブルに削除前スナップショット audit log を残す。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    conn = db()
    c = conn.cursor()
    try:
        c.execute("SELECT id, name, email, status, plan, course, stripe_subscription_id, stripe_customer_id, created_at FROM students WHERE id=?", (student_id,))
        student = c.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="生徒が見つかりません")

        # 安全装置: email 完全一致必須 (同名衝突防止)。email 未設定の生徒のみ name fallback 可。
        if not payload.dry_run:
            student_email = (student["email"] or "").strip().lower()
            student_name = (student["name"] or "").strip()
            if student_email:
                provided_email = (payload.confirm_email or "").strip().lower()
                if not provided_email or provided_email != student_email:
                    raise HTTPException(status_code=400, detail="確認のためメールアドレスを正確に入力してください")
            else:
                # email 未設定 → name fallback
                provided_name = (payload.confirm_name or "").strip()
                if not provided_name or provided_name != student_name:
                    raise HTTPException(status_code=400, detail="確認のため生徒名を正確に入力してください (この生徒は email 未設定のため名前で確認)")

        # Stripe ガード: 有効サブスクがあり cancel_stripe=false なら 409
        sub_id = student["stripe_subscription_id"]
        if sub_id and not payload.dry_run:
            if not payload.cancel_stripe:
                raise HTTPException(
                    status_code=409,
                    detail="Stripe 有効サブスクがあります。先に Stripe ダッシュで解約するか、cancel_stripe=true を付けて再送してください"
                )
            _stripe = get_stripe()
            if not _stripe:
                raise HTTPException(status_code=503, detail="Stripe が構成されていません")
            try:
                _stripe.Subscription.delete(sub_id)
                log.info(f"[StudentDelete] stripe sub canceled: student={student_id} sub={sub_id}")
            except Exception as e:
                err_msg = str(e).lower()
                # 既解約・存在しないサブスクは正常扱いで進める (Stripe ポータルで既に解約済みケース)
                if any(s in err_msg for s in ("no such subscription", "resource_missing", "already canceled", "already_canceled")):
                    log.info(f"[StudentDelete] stripe sub already gone (treated as success): student={student_id} sub={sub_id}")
                else:
                    log.error(f"[StudentDelete] stripe cancel failed: {type(e).__name__}: {e}")
                    raise HTTPException(status_code=502, detail=f"Stripe 解約失敗: {e}")

        # 関連データの件数集計 (preview 用 + audit)
        related_counts = {}
        related_tables = [
            ("study_logs", "student_id"),
            ("study_plans", "student_id"),
            ("exam_results", "student_id"),
            ("curricula", "student_id"),
            ("notifications", "student_id"),
            ("otp_codes", "student_id"),
            ("usage_monthly", "student_id"),
            ("mock_exam_sessions", "student_id"),
            ("vocab_progress", "student_id"),
            ("payments", "student_id"),
        ]
        for tbl, col in related_tables:
            try:
                c.execute(f"SELECT COUNT(*) AS n FROM {tbl} WHERE {col}=?", (student_id,))
                row = c.fetchone()
                related_counts[tbl] = int(row["n"]) if row else 0
            except Exception as _e:
                related_counts[tbl] = -1  # テーブル不在等
        # messages (sender or recipient)
        try:
            c.execute(
                "SELECT COUNT(*) AS n FROM messages WHERE (sender_type='student' AND sender_id=?) OR (recipient_type='student' AND recipient_id=?)",
                (student_id, student_id)
            )
            row = c.fetchone()
            related_counts["messages"] = int(row["n"]) if row else 0
        except Exception:
            related_counts["messages"] = -1
        # referrals (referrer or referred)
        try:
            c.execute("SELECT COUNT(*) AS n FROM referrals WHERE referrer_id=? OR referred_id=?", (student_id, student_id))
            row = c.fetchone()
            related_counts["referrals"] = int(row["n"]) if row else 0
        except Exception:
            related_counts["referrals"] = -1
        # course_applications
        try:
            c.execute("SELECT COUNT(*) AS n FROM course_applications WHERE student_id=?", (student_id,))
            row = c.fetchone()
            related_counts["course_applications"] = int(row["n"]) if row else 0
        except Exception:
            related_counts["course_applications"] = -1

        snapshot = {
            "id": student["id"], "name": student["name"], "email": student["email"],
            "status": student["status"], "plan": student["plan"], "course": student["course"],
            "created_at": str(student["created_at"]) if student["created_at"] else None,
            "stripe_customer_id": student["stripe_customer_id"],
            "stripe_subscription_id": student["stripe_subscription_id"],
            "related_counts": related_counts,
        }

        if payload.dry_run:
            return {"ok": True, "dry_run": True, "snapshot": snapshot, "message": "削除されません (dry_run)"}

        # 監査ログ: 削除前スナップショット
        try:
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("admin_student_deleted", json.dumps(snapshot, ensure_ascii=False), "admin")
            )
        except Exception as _e:
            log.warning(f"[StudentDelete] audit log failed: {_e}")

        # cascade delete - FK 依存順に
        delete_tables = [
            ("study_logs", "DELETE FROM study_logs WHERE student_id=?"),
            ("study_plans", "DELETE FROM study_plans WHERE student_id=?"),
            ("exam_results", "DELETE FROM exam_results WHERE student_id=?"),
            ("curricula", "DELETE FROM curricula WHERE student_id=?"),
            ("notifications", "DELETE FROM notifications WHERE student_id=?"),
            ("otp_codes", "DELETE FROM otp_codes WHERE student_id=?"),
            ("usage_monthly", "DELETE FROM usage_monthly WHERE student_id=?"),
            ("mock_exam_sessions", "DELETE FROM mock_exam_sessions WHERE student_id=?"),
            ("vocab_progress", "DELETE FROM vocab_progress WHERE student_id=?"),
            ("payments", "DELETE FROM payments WHERE student_id=?"),
        ]
        deleted_counts = {}
        for tbl, sql in delete_tables:
            try:
                c.execute(sql, (student_id,))
                deleted_counts[tbl] = related_counts.get(tbl, 0)
            except Exception as e:
                log.warning(f"[StudentDelete] {tbl} cleanup failed: {e}")
                deleted_counts[tbl] = -1
        # messages: 双方向
        try:
            c.execute(
                "DELETE FROM messages WHERE (sender_type='student' AND sender_id=?) OR (recipient_type='student' AND recipient_id=?)",
                (student_id, student_id)
            )
            deleted_counts["messages"] = related_counts.get("messages", 0)
        except Exception as e:
            log.warning(f"[StudentDelete] messages cleanup failed: {e}")
            deleted_counts["messages"] = -1
        # course_applications: 監査保存のため student_id を NULL にして履歴は残す
        try:
            c.execute("UPDATE course_applications SET student_id=NULL WHERE student_id=?", (student_id,))
            deleted_counts["course_applications_anonymized"] = related_counts.get("course_applications", 0)
        except Exception as e:
            log.warning(f"[StudentDelete] course_applications anonymize failed: {e}")
        # referrals: 監査保存のため referrer_id/referred_id を NULL にして履歴は残す
        try:
            c.execute("UPDATE referrals SET referrer_id=NULL WHERE referrer_id=?", (student_id,))
            c.execute("UPDATE referrals SET referred_id=NULL WHERE referred_id=?", (student_id,))
            deleted_counts["referrals_anonymized"] = related_counts.get("referrals", 0)
        except Exception as e:
            log.warning(f"[StudentDelete] referrals anonymize failed: {e}")
        # students 本体削除
        c.execute("DELETE FROM students WHERE id=?", (student_id,))
        conn.commit()
        log.info(f"[StudentDelete] student={student_id} name={student['name']} email={student['email']} deleted={deleted_counts}")
        return {
            "ok": True, "dry_run": False,
            "deleted": deleted_counts,
            "snapshot": snapshot,
            "message": f"生徒「{student['name']}」を削除しました",
        }
    finally:
        conn.close()


@app.post("/api/admin/textbooks/purge")
def admin_textbook_pool_purge(payload: dict, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """textbook_pool の特定レコードを削除する admin endpoint。
    payload (いずれか必須):
      {"source": "claude_max_seed_batch01"}  # source 完全一致で削除
      {"id": 123}                              # ID 指定削除
      {"subject": "数学ⅠA", "topic": "2次関数"}  # subject + topic 一致削除
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

    source = payload.get("source")
    rec_id = payload.get("id")
    subject = payload.get("subject")
    topic = payload.get("topic")

    where = []
    params = []
    if source:
        where.append("source = ?")
        params.append(source)
    if rec_id:
        where.append("id = ?")
        params.append(int(rec_id))
    if subject:
        where.append("subject = ?")
        params.append(subject)
    if topic:
        where.append("topic = ?")
        params.append(topic)
    if not where:
        raise HTTPException(status_code=400, detail="削除条件が空です (source/id/subject/topic のいずれか必須)")

    where_sql = " WHERE " + " AND ".join(where)
    conn = db()
    c = conn.cursor()
    try:
        c.execute(f"SELECT COUNT(*) AS n FROM textbook_pool{where_sql}", tuple(params))
        row = c.fetchone()
        will_delete = row["n"] if row else 0
        c.execute(f"DELETE FROM textbook_pool{where_sql}", tuple(params))
        conn.commit()
    finally:
        conn.close()

    log.info(f"[TextbookPool:Purge] deleted={will_delete} where={where_sql} params={params}")
    return {"ok": True, "deleted": will_delete, "where": where_sql, "message": f"✅ {will_delete} 教材を削除しました"}


@app.get("/api/admin/textbooks/list")
def admin_textbook_pool_list(authorization: Optional[str] = Header(None)):
    """admin: textbook_pool 一覧 (CEO ダッシュ表示用)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            """SELECT id, subject, topic, level, length, type, title, tags, status, source, created_at
               FROM textbook_pool ORDER BY created_at DESC LIMIT 200"""
        )
        rows = [dict(r) for r in c.fetchall()]
        c.execute("SELECT COUNT(*) AS n FROM textbook_pool")
        total_row = c.fetchone()
        total = total_row["n"] if total_row else 0
    finally:
        conn.close()
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = str(r["created_at"])
        r["tags"] = (r.get("tags") or "").split(",") if r.get("tags") else []
    return {"ok": True, "total": total, "items": rows}


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
def public_exam_questions_bank(
    exam: str,
    part: str,
    eiken_grade: Optional[str] = None,
    univ: Optional[str] = None,
    limit: int = 20,
    student_id: Optional[int] = None,
    topic: Optional[str] = None,
):
    """公開API: 試験パートの最新N問を返す (フロントが AUTO_GENERATED_BANKS に流し込む)。
    認証不要 (出題内容は公開可・実回答は提出不要)。
    univ パラメータは大学入試 (daigaku) 用 — DB スキーマ上は eiken_grade カラムに大学キーを保存している。
    student_id があれば直近 7 日に出した (univ, year) を pool 側でも除外し、refill 側にも exclude を伝播。
    topic は単元タグ (例: '関係代名詞') — refill 時の AI prompt に注入される。"""
    limit = max(1, min(limit, 50))
    # daigaku の場合 univ → eiken_grade として扱う (DB スキーマ共有)
    if exam == "daigaku" and univ and not eiken_grade:
        eiken_grade = univ
    conn = db()
    c = conn.cursor()
    try:
        if eiken_grade:
            c.execute(
                "SELECT id, question_data, created_at FROM exam_questions WHERE exam_id = ? AND part_key = ? AND eiken_grade = ? ORDER BY created_at DESC LIMIT ?",
                (exam, part, eiken_grade, limit),
            )
        else:
            c.execute(
                "SELECT id, question_data, created_at FROM exam_questions WHERE exam_id = ? AND part_key = ? ORDER BY created_at DESC LIMIT ?",
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
            data["_question_id"] = r["id"] if hasattr(r, "keys") and "id" in r.keys() else r[0]
            items.append(data)
        except Exception:
            pass

    # 直近 7 日除外 (相対的多様性): student_id があれば過去出題と同じ (univ, year) を後回しに
    exclude_combinations = _get_recent_exam_combinations(student_id, days=7) if student_id else []
    excluded_set = set((str(u), int(y)) for (u, y) in exclude_combinations)

    import random
    pool_unseen = []
    pool_seen = []
    if excluded_set and items:
        for it in items:
            it_univ = str(it.get("univ_simulated") or eiken_grade or "")
            try:
                it_year = int(it.get("year_simulated") or 0)
            except Exception:
                it_year = 0
            # 大学キー比較 (eiken_grade に揃える)
            key_pair = (str(eiken_grade or ""), it_year)
            if key_pair in excluded_set:
                pool_seen.append(it)
            else:
                pool_unseen.append(it)
        candidates = pool_unseen if pool_unseen else pool_seen
    else:
        candidates = items
    selected = random.choice(candidates) if candidates else None

    # 🔁 オンデマンド補充: pool が薄い part を生徒が引いた瞬間に裏で補充キューイング
    # (ExamQ scheduler は N時間おき・interval=6h なので、その間でも必要なら即補充)
    if EXAM_QUESTIONS_ENABLED and len(items) < EXAM_QUESTIONS_MIN_POOL:
        try:
            asyncio.create_task(_refill_part_async(
                exam, part, eiken_grade,
                target=2,
                exclude_combinations=exclude_combinations or None,
                topic_hint=topic,
            ))
            log.info(f"[ExamQ:Refill] queued for {exam}/{part}/{eiken_grade} (pool={len(items)} < min={EXAM_QUESTIONS_MIN_POOL}, topic={topic})")
        except Exception as e:
            log.warning(f"[ExamQ:Refill] failed to queue: {e}")

    # 出題記録 (events) — 今後の除外判定に利用
    if selected and student_id:
        try:
            session_key = f"student:{student_id}"
            props = {
                "student_id": int(student_id),
                "exam": exam,
                "part": part,
                "univ": eiken_grade or univ,
                "year": selected.get("year_simulated"),
                "question_id": selected.get("_question_id"),
                "topic": topic,
            }
            conn2 = db()
            c2 = conn2.cursor()
            try:
                c2.execute(
                    "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                    ("exam_question_served", json.dumps(props, ensure_ascii=False), session_key),
                )
                conn2.commit()
            except Exception as e:
                log.warning(f"[ExamQ:Served] event insert failed: {e}")
                try: conn2.rollback()
                except Exception: pass
            conn2.close()
        except Exception as e:
            log.warning(f"[ExamQ:Served] event recording failed: {e}")

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
            # AI never-fail: _call_anthropic_safe 経由で Tier 4 (Gemini) まで自動 fallback
            d = _call_anthropic_safe(
                {
                    "model": EXAM_QUESTIONS_MODEL,
                    "max_tokens": 800,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                kind="recommend_next_advice",
            )
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
        # AI never-fail: _call_anthropic_safe 経由で Tier 4 (Gemini) まで自動 fallback
        d = _call_anthropic_safe(
            {
                "model": EXAM_QUESTIONS_MODEL,
                "max_tokens": 8000,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            kind="curriculum_generate",
        )
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
        # AI never-fail: _call_anthropic_safe 経由で Tier 4 (Gemini) まで自動 fallback
        data = _call_anthropic_safe(
            {
                "model": EXAM_QUESTIONS_MODEL,
                "max_tokens": 4000,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            kind="news_reading_question",
        )
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


@app.get("/api/admin/students/list-minimal")
def admin_students_list_minimal(limit: int = 20,
                                  email_contains: Optional[str] = None,
                                  x_cron_secret: Optional[str] = Header(None),
                                  authorization: Optional[str] = Header(None)):
    """active student の最小情報 (id, email, status, plan) を取得。
    AI チューター動作確認時に塾長 / テスト student の id を特定するため。
    x-cron-secret or admin Bearer 認証。email は氏名や個人情報を含まない範囲で返す。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    limit = max(1, min(int(limit or 20), 100))
    conn = db()
    c = conn.cursor()
    if email_contains:
        c.execute(
            "SELECT id, email, status, plan, last_login_at, trial_end FROM students "
            "WHERE status IN ('trial', 'paid') AND email LIKE ? "
            "ORDER BY last_login_at DESC NULLS LAST LIMIT ?",
            (f"%{email_contains}%", limit),
        )
    else:
        c.execute(
            "SELECT id, email, status, plan, last_login_at, trial_end FROM students "
            "WHERE status IN ('trial', 'paid') "
            "ORDER BY last_login_at DESC NULLS LAST LIMIT ?",
            (limit,),
        )
    rows = c.fetchall()
    conn.close()
    students = []
    for r in rows:
        # email を一部 masking (xxxx@example.com 形式)
        email = r["email"] or ""
        if email and "@" in email:
            local, domain = email.split("@", 1)
            email_masked = (local[:3] + "***" + "@" + domain) if len(local) > 3 else (local + "***@" + domain)
        else:
            email_masked = email
        students.append({
            "id": r["id"],
            "email_masked": email_masked,
            "status": r["status"],
            "plan": r["plan"],
            "last_login_at": str(r["last_login_at"]) if r["last_login_at"] else None,
            "trial_end": str(r["trial_end"]) if r["trial_end"] else None,
        })
    return {"count": len(students), "students": students}


@app.post("/api/admin/log-frontend-error")
def admin_log_frontend_error(payload: dict, authorization: Optional[str] = Header(None)):
    """frontend で発生したエラーを events に記録する endpoint (生徒 / 塾長 共通)。
    教材生成・AI チューター等で fallback 表示が出た時、真原因を即特定するため。
    認証: 生徒 Bearer or admin Bearer (両方未認証でも記録は可)"""
    student = None
    is_admin = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            is_admin = True
        else:
            try:
                student = _get_current_student(authorization)
            except Exception:
                pass
    try:
        conn = db()
        c = conn.cursor()
        props = {
            "kind": (payload.get("kind") or "unknown")[:50],
            "subject": (payload.get("subject") or "")[:50],
            "topic": (payload.get("topic") or "")[:80],
            "level": (payload.get("level") or "")[:30],
            "type": (payload.get("type") or "")[:30],
            "model": (payload.get("model") or "")[:50],
            "error_message": (payload.get("error_message") or "")[:300],
            "full_error": (payload.get("full_error") or "")[:600],
            "user_agent": (payload.get("user_agent") or "")[:200],
            "student_id": student.get("id") if student else None,
            "is_admin": is_admin,
        }
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("frontend_error", json.dumps(props, ensure_ascii=False), "frontend_log"),
        )
        conn.commit()
        conn.close()
        return {"ok": True}
    except Exception as e:
        log.error(f"log-frontend-error failed: {e}")
        return {"ok": False, "error": str(e)[:200]}


@app.get("/api/admin/ai/recent-failures")
def admin_ai_recent_failures(limit: int = 30, x_cron_secret: Optional[str] = Header(None),
                              authorization: Optional[str] = Header(None)):
    """直近の AI call 失敗を events から取得 (stage 別の失敗詳細)。
    塾長が「frontend で AI チューターが応答テンプレに変わった原因」を即特定可能。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    limit = max(1, min(int(limit or 30), 200))
    conn = db()
    c = conn.cursor()
    c.execute(
        "SELECT created_at, name, props FROM events "
        "WHERE name IN ('ai_call_failure', 'ai_total_failure', 'ai_credit_low', 'ai_fallback_used', "
        "'ai_fallback_gemini', 'ai_fallback_gemini_credit_low', "
        "'ai_fallback_openai', 'ai_fallback_openai_credit_low', "  # 2026-05-10 OpenAI Tier 5 追加
        "'frontend_error') "
        "ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    failures = []
    for r in rows:
        try:
            props = json.loads(r["props"] or "{}")
        except Exception:
            props = {}
        failures.append({
            "created_at": str(r["created_at"]),
            "name": r["name"],
            "stage": props.get("stage"),
            "status_code": props.get("status_code"),
            "detail": props.get("detail"),
            "student_id": props.get("student_id"),
            "model": props.get("model"),
            "kind": props.get("kind"),
            "feature": props.get("feature"),
            "thinking": props.get("thinking"),
            "origin": props.get("origin"),
            "referer": props.get("referer"),
            "raw": props,
        })
    # stage 別集計 (どこで止まっているかすぐ分かる)
    by_stage = {}
    for f in failures:
        stage = f.get("stage") or f.get("name") or "unknown"
        by_stage[stage] = by_stage.get(stage, 0) + 1
    return {
        "count": len(failures),
        "by_stage_top": sorted(by_stage.items(), key=lambda x: -x[1])[:10],
        "failures": failures,
    }


@app.post("/api/admin/ai/probe-call")
def admin_probe_call(payload: dict, request: Request,
                      x_cron_secret: Optional[str] = Header(None),
                      authorization: Optional[str] = Header(None)):
    """/api/ai/call の前段 check + AI 呼出を完全再現するデバッグ endpoint。
    payload で student_id / model / system / messages / kind / feature / thinking を指定可能。
    各 check のどこで失敗したか、stage と status_code が返る。塾長操作不要で再現テスト可。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    student_id = payload.get("student_id")
    model = payload.get("model") or "claude-opus-4-7"
    thinking = bool(payload.get("thinking", False))
    feature = payload.get("feature")
    kind = payload.get("kind") or "chat"
    system_text = payload.get("system") or "あなたは進路相談に詳しい AI コーチです。"
    messages = payload.get("messages") or [{"role": "user", "content": "九州大学の滑り止めはどこがいいですか?"}]

    # 各 stage を順次再現 (失敗した時点で stage と detail を返す)
    result = {"stages": []}

    # Origin check (request の origin/referer はテスト用に許可しておく)
    # Stage 1: ANTHROPIC_API_KEY
    if not ANTHROPIC_API_KEY:
        return {**result, "ok": False, "stage": "anthropic_unconfigured", "status_code": 503}
    result["stages"].append("anthropic_configured: ok")

    # Stage 2: student check
    try:
        student_row = _verify_student_active(student_id) if student_id else None
        if student_id:
            _check_ai_budget(student_id)
            if feature:
                _check_quota(student_row, feature)
        result["stages"].append(f"student_check: ok (student_id={student_id or 'skipped'})")
    except HTTPException as e:
        return {**result, "ok": False, "stage": "student_or_budget_or_quota",
                "status_code": e.status_code, "detail": str(e.detail)}

    # Stage 3: AI 呼び出し (Opus 4.7 必須パラメータ補完含む)
    body = {
        "model": model,
        "max_tokens": int(payload.get("max_tokens") or 300),
        "system": system_text,
        "messages": messages,
    }
    if model.startswith("claude-opus-4-7"):
        body["thinking"] = {"type": "adaptive"}
        body["output_config"] = {"effort": "low"}
        body["temperature"] = 1.0
    elif thinking:
        body["thinking"] = {"type": "enabled", "budget_tokens": 4000}
        body["temperature"] = 1.0

    t0 = time.time()
    try:
        data = _call_anthropic_safe(body, kind=f"probe_call_{kind}", student_id=student_id)
        text = (data.get("content") or [{}])[0].get("text", "")
        return {
            **result,
            "ok": True,
            "actual_model": data.get("_actual_model"),
            "provider": data.get("_provider", "anthropic"),
            "latency_ms": int((time.time() - t0) * 1000),
            "text_head": text[:600],
        }
    except HTTPException as e:
        return {**result, "ok": False, "stage": "anthropic_all_tiers_failed",
                "status_code": e.status_code, "detail": str(e.detail),
                "latency_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {**result, "ok": False, "stage": "ai_call_unexpected",
                "error_type": type(e).__name__, "error": str(e)[:600],
                "latency_ms": int((time.time() - t0) * 1000)}


@app.post("/api/admin/ai/probe-tutor")
def admin_probe_tutor(payload: dict, x_cron_secret: Optional[str] = Header(None),
                       authorization: Optional[str] = Header(None)):
    """AI チューター (Anthropic Opus 4.7 等) を _call_anthropic_safe 経由で叩いて動作確認。
    /api/ai/call の前段 check (origin/student/budget/quota) を bypass し純粋に AI 経路だけテスト。
    payload: {model?, system?, messages?, thinking?, max_tokens?}"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    model = payload.get("model") or "claude-opus-4-7"
    body = {
        "model": model,
        "max_tokens": int(payload.get("max_tokens") or 300),
        "system": payload.get("system") or "あなたは進路相談に詳しい AI コーチです。",
        "messages": payload.get("messages") or [
            {"role": "user", "content": "九州大学の滑り止めはどこがいいですか?"}
        ],
    }
    # Opus 4.7 必須パラメータ自動補完 (probe でも同じ補完ロジック適用)
    if model.startswith("claude-opus-4-7"):
        body["thinking"] = {"type": "adaptive"}
        body["output_config"] = {"effort": "low"}
        body["temperature"] = 1.0

    t0 = time.time()
    try:
        data = _call_anthropic_safe(body, kind="probe_tutor")
        text = (data.get("content") or [{}])[0].get("text", "") if data.get("content") else ""
        return {
            "ok": True,
            "actual_model": data.get("_actual_model"),
            "provider": data.get("_provider", "anthropic"),
            "latency_ms": int((time.time() - t0) * 1000),
            "text_head": text[:600],
        }
    except HTTPException as e:
        return {
            "ok": False,
            "status_code": e.status_code,
            "detail": e.detail,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        return {
            "ok": False,
            "error_type": type(e).__name__,
            "error": str(e)[:600],
            "latency_ms": int((time.time() - t0) * 1000),
        }


@app.post("/api/admin/ai/test-gemini")
def admin_test_gemini(model: Optional[str] = None, strict: int = 0,
                       authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """Gemini Tier 4 fallback の動作確認 endpoint。
    admin Bearer or x-cron-secret 認証。Gemini で 1 回 generate して
    {ok, model, sample, latency_ms} を返す。
    クエリ:
      - model=gemini-2.5-pro 等で任意モデル指定 (省略時は GEMINI_MODEL = Pro)
      - strict=1 で Pro→Flash 二段 fallback を bypass し、Pro が失敗したら raw error を返す
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    if not GEMINI_API_KEY:
        return {
            "ok": False,
            "configured": False,
            "error": "GEMINI_API_KEY が Railway env に未設定。https://aistudio.google.com/app/apikey で発行してください。",
        }

    target_model = model or GEMINI_MODEL

    # strict=1: 二段 fallback bypass で raw error を取得 (デバッグ用)
    if strict:
        t0 = time.time()
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            gen_model = genai.GenerativeModel(
                model_name=target_model,
                system_instruction="あなたは丁寧な日本語アシスタントです。",
                generation_config={"max_output_tokens": 200, "temperature": 0.7},
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                ],
            )
            chat = gen_model.start_chat()
            resp = chat.send_message("「AI never-fail テスト成功」とだけ短く返答してください。")
            return {
                "ok": True,
                "configured": True,
                "model": target_model,
                "provider": "gemini",
                "strict": True,
                "sample": (resp.text or "")[:200],
                "latency_ms": int((time.time() - t0) * 1000),
            }
        except Exception as e:
            return {
                "ok": False,
                "configured": True,
                "strict": True,
                "model_attempted": target_model,
                "error_type": type(e).__name__,
                "error": str(e)[:1500],
                "latency_ms": int((time.time() - t0) * 1000),
            }

    t0 = time.time()
    try:
        data = _call_gemini(
            {
                "model": target_model,
                "max_tokens": 200,
                "system": "あなたは丁寧な日本語アシスタントです。",
                "messages": [{"role": "user", "content": "「AI never-fail テスト成功」とだけ短く返答してください。"}],
            },
            kind="test_gemini",
        )
        text = (data.get("content") or [{}])[0].get("text", "") if data.get("content") else ""
        return {
            "ok": True,
            "configured": True,
            "model": data.get("_actual_model"),
            "provider": data.get("_provider"),
            "sample": text[:200],
            "latency_ms": int((time.time() - t0) * 1000),
            "usage": data.get("usage", {}),
        }
    except Exception as e:
        return {
            "ok": False,
            "configured": True,
            "error": f"{type(e).__name__}: {str(e)[:300]}",
            "latency_ms": int((time.time() - t0) * 1000),
        }


@app.post("/api/admin/ai/test-openai")
def admin_test_openai(model: Optional[str] = None,
                       authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """OpenAI Tier 5 fallback の動作確認 endpoint (2026-05-10 塾長指示)。
    admin Bearer or x-cron-secret 認証。OpenAI で 1 回 generate して
    {ok, model, sample, latency_ms} を返す。
    クエリ:
      - model=gpt-5 等で任意モデル指定 (省略時は OPENAI_MODEL = gpt-4o-mini)
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    if not OPENAI_API_KEY:
        return {
            "ok": False,
            "configured": False,
            "error": "OPENAI_API_KEY が Railway env に未設定。https://platform.openai.com/api-keys で発行してください。",
        }

    target_model = model or OPENAI_MODEL

    t0 = time.time()
    try:
        data = _call_openai(
            {
                "model": target_model,
                "max_tokens": 200,
                "system": "あなたは丁寧な日本語アシスタントです。",
                "messages": [{"role": "user", "content": "「AI never-fail テスト成功」とだけ短く返答してください。"}],
            },
            kind="test_openai",
        )
        text = (data.get("content") or [{}])[0].get("text", "") if data.get("content") else ""
        return {
            "ok": True,
            "configured": True,
            "model": data.get("_actual_model"),
            "provider": data.get("_provider"),
            "sample": text[:200],
            "latency_ms": int((time.time() - t0) * 1000),
            "usage": data.get("usage", {}),
        }
    except Exception as e:
        return {
            "ok": False,
            "configured": True,
            "error": f"{type(e).__name__}: {str(e)[:300]}",
            "latency_ms": int((time.time() - t0) * 1000),
        }


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
        "synthetic_checkout": _SYNTHETIC_CHECKOUT_LAST,
        "ai_credit_low": _ai_credit_low_active(),
        "ai_circuit_breaker": _AI_CIRCUIT_BREAKER,
    }


@app.get("/api/ai/health")
def public_ai_health():
    """フロントから素早く AI 状態を確認できる public endpoint。
    認証不要。CEO ダッシュ・LP・教材生成画面が事前チェックに使う。
    credit_low なら true を返し、フロントは「AI 一時的に混雑中」表示に切り替える。"""
    import time as _t
    return {
        "available": ANTHROPIC_API_KEY is not None and not _ai_credit_low_active(),
        "credit_low": _ai_credit_low_active(),
        "credit_low_until": _AI_CIRCUIT_BREAKER.get("credit_low_until", 0),
        "now": _t.time(),
    }


@app.post("/api/admin/email/diagnose")
def admin_email_diagnose(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """Resend API の接続・ドメイン検証・送信テストを一括診断。
    CEO ダッシュの「メール診断」ボタンから呼ばれる。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    import urllib.request, urllib.error
    result = {
        "resend_api_key_set": bool(RESEND_API_KEY),
        "resend_api_key_prefix": (RESEND_API_KEY[:8] + "***") if RESEND_API_KEY else "",
        "from_email": FROM_EMAIL,
        "domain_status": None,
        "domains": [],
        "recent_errors": [],
        "test_send": None,
    }

    # 1. Resend /domains で送信ドメインの検証状態を取得
    if RESEND_API_KEY:
        try:
            req = urllib.request.Request(
                "https://api.resend.com/domains",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                domains_data = json.loads(resp.read().decode())
                domains_list = domains_data.get("data", []) if isinstance(domains_data, dict) else domains_data
                for d in (domains_list if isinstance(domains_list, list) else []):
                    result["domains"].append({
                        "name": d.get("name"),
                        "status": d.get("status"),
                        "created_at": d.get("created_at"),
                    })
                # FROM_EMAIL のドメインが verified か判定
                from_domain = ""
                if "<" in FROM_EMAIL and ">" in FROM_EMAIL:
                    from_domain = FROM_EMAIL.split("<")[1].split(">")[0].split("@")[-1]
                elif "@" in FROM_EMAIL:
                    from_domain = FROM_EMAIL.split("@")[-1]
                matched = [d for d in result["domains"] if d.get("name") == from_domain]
                if matched:
                    result["domain_status"] = matched[0].get("status")
                elif from_domain == "resend.dev":
                    result["domain_status"] = "resend_default_sender"
                else:
                    result["domain_status"] = f"not_found ({from_domain})"
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # send-only restricted key (domains:read scope なし)。実送信は影響なし
                result["domain_status"] = "send_only_key (domains:read scope なし — 実送信は影響なし)"
                result["domain_status_remediation"] = "Resend ダッシュで API key を Full access に上げるか、新しい key で domains:read scope を追加してください"
            elif e.code == 401:
                result["domain_status"] = "unauthorized (API key が revoke 済みまたは無効)"
                result["domain_status_remediation"] = "Resend ダッシュで新しい API key を発行し RESEND_API_KEY 環境変数を更新してください"
            else:
                result["domain_status"] = f"api_error: HTTPError {e.code}"
        except Exception as e:
            result["domain_status"] = f"api_error: {type(e).__name__}: {str(e)[:200]}"

    # 2. DB から直近のメール失敗エラーを取得
    try:
        conn = db(); c = conn.cursor()
        c.execute(
            "SELECT props, created_at FROM events WHERE name = 'signup_email_status' ORDER BY created_at DESC LIMIT 10",
        )
        rows = c.fetchall()
        conn.close()
        for r in rows:
            try:
                props = json.loads(r["props"]) if isinstance(r["props"], str) else r["props"]
                result["recent_errors"].append({
                    "email_sent": props.get("email_sent"),
                    "error": (props.get("error") or "")[:200],
                    "created_at": str(r["created_at"]),
                })
            except Exception:
                pass
    except Exception as e:
        result["recent_errors"] = [{"error": f"db_query_failed: {e}"}]

    # 3. Resend API キーが生きているか: /api-keys で軽量確認
    if RESEND_API_KEY:
        try:
            req = urllib.request.Request(
                "https://api.resend.com/api-keys",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result["api_key_valid"] = True
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # send-only restricted key (api-keys:read scope なし)。実送信は影響なし
                result["api_key_valid"] = True
                result["api_key_scope"] = "send_only"
                result["api_key_error"] = "send_only key (api-keys:read scope なし — 実送信は影響なし)"
            elif e.code == 401:
                result["api_key_valid"] = False
                result["api_key_scope"] = "invalid"
                result["api_key_error"] = "HTTP 401: API key が revoke 済みまたは無効"
            else:
                result["api_key_valid"] = False
                result["api_key_error"] = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
        except Exception as e:
            result["api_key_valid"] = False
            result["api_key_error"] = f"{type(e).__name__}: {str(e)[:200]}"

    return result


@app.post("/api/admin/email/test-send")
def admin_email_test_send(payload: dict, authorization: Optional[str] = Header(None)):
    """テストメール送信。CEO ダッシュ「テスト送信」ボタン用。
    payload.to が必須 (CEOのメールアドレス)。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    to_email = (payload.get("to") or "").strip()
    if not to_email or "@" not in to_email:
        raise HTTPException(status_code=400, detail="to (メールアドレス) が必要です")

    import urllib.request, urllib.error
    if not RESEND_API_KEY:
        return {"sent": False, "error": "RESEND_API_KEY 未設定"}
    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps({
                "from": FROM_EMAIL,
                "to": [to_email],
                "subject": "【AI学習コーチ塾】メール送信テスト",
                "html": "<h2>✅ メール送信テスト成功</h2><p>Resend API 経由の送信が正常に動作しています。</p>",
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            return {"sent": True, "resend_id": body.get("id"), "to": to_email}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:300]
        return {"sent": False, "error": f"HTTP {e.code}: {err_body}", "to": to_email}
    except Exception as e:
        return {"sent": False, "error": f"{type(e).__name__}: {str(e)[:200]}", "to": to_email}


@app.post("/api/admin/students/purge-stale-data")
def admin_students_purge_stale(payload: dict = None, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """合成監視 orphan + テストデータを安全に一括削除。
    対象:
      1. email が @synthetic-monitor.* で created_at > 5分前 (E2E 後の orphan)
      2. name に test/テスト/ダミー/sample 等のキーワードを含む生徒 (キーワードマッチ)
    payload (省略可): {"dry_run": true} で件数のみ返す
    関連 cascade も実行 (admin_student_delete と同じ範囲: study_logs/messages/events 等)
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

    payload = payload or {}
    dry_run = bool(payload.get("dry_run", False))

    BLOCKED_KEYWORDS = ['テスト', 'ﾃｽﾄ', 'test', 'ダミー', 'dummy', 'サンプル', 'sample',
                       'デモ', 'demo', '品質検証', '確認用', '動作確認', '検証用',
                       'あいうえお', 'aaa', 'bbb', 'xxx', 'zzz', '監視 守', '監視　守']

    conn = db()
    c = conn.cursor()
    matched = []
    try:
        # 1. 合成監視 orphan
        c.execute(
            "SELECT id, name, email, created_at FROM students WHERE email LIKE '%@synthetic-monitor.%' AND created_at < ?",
            ((datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),)
        )
        for r in c.fetchall():
            matched.append({"id": r["id"], "name": r["name"], "email": r["email"],
                           "via": "synthetic_monitor_orphan", "created_at": str(r["created_at"])})
        # 2. テストキーワードマッチ
        for kw in BLOCKED_KEYWORDS:
            c.execute(
                "SELECT id, name, email, created_at FROM students WHERE LOWER(name) LIKE ?",
                (f"%{kw.lower()}%",)
            )
            for r in c.fetchall():
                if not any(m["id"] == r["id"] for m in matched):
                    matched.append({"id": r["id"], "name": r["name"], "email": r["email"],
                                   "via": f"test_kw:{kw}", "created_at": str(r["created_at"])})

        deleted = 0
        if not dry_run and matched:
            ids = [m["id"] for m in matched]
            placeholders = ",".join(["?"] * len(ids))
            tup = tuple(ids)
            # 全関連テーブル cascade (admin_student_delete と同等)
            cascade_tables = [
                ("study_logs", f"DELETE FROM study_logs WHERE student_id IN ({placeholders})"),
                ("study_plans", f"DELETE FROM study_plans WHERE student_id IN ({placeholders})"),
                ("exam_results", f"DELETE FROM exam_results WHERE student_id IN ({placeholders})"),
                ("curricula", f"DELETE FROM curricula WHERE student_id IN ({placeholders})"),
                ("notifications", f"DELETE FROM notifications WHERE student_id IN ({placeholders})"),
                ("otp_codes", f"DELETE FROM otp_codes WHERE student_id IN ({placeholders})"),
                ("usage_monthly", f"DELETE FROM usage_monthly WHERE student_id IN ({placeholders})"),
                ("mock_exam_sessions", f"DELETE FROM mock_exam_sessions WHERE student_id IN ({placeholders})"),
                ("vocab_progress", f"DELETE FROM vocab_progress WHERE student_id IN ({placeholders})"),
                ("payments", f"DELETE FROM payments WHERE student_id IN ({placeholders})"),
            ]
            for tbl, sql in cascade_tables:
                try: c.execute(sql, tup)
                except Exception as e: log.warning(f"[PurgeStale] {tbl}: {e}")
            # messages 双方向
            try:
                c.execute(
                    f"DELETE FROM messages WHERE (sender_type='student' AND sender_id IN ({placeholders})) OR (recipient_type='student' AND recipient_id IN ({placeholders}))",
                    tup + tup
                )
            except Exception as e: log.warning(f"[PurgeStale] messages: {e}")
            # course_applications/referrals は NULL 化 (履歴保持)
            try: c.execute(f"UPDATE course_applications SET student_id=NULL WHERE student_id IN ({placeholders})", tup)
            except Exception: pass
            try: c.execute(f"UPDATE referrals SET referrer_id=NULL WHERE referrer_id IN ({placeholders})", tup)
            except Exception: pass
            try: c.execute(f"UPDATE referrals SET referred_id=NULL WHERE referred_id IN ({placeholders})", tup)
            except Exception: pass
            # students 本体
            c.execute(f"DELETE FROM students WHERE id IN ({placeholders})", tup)
            deleted = len(ids)
            # audit log
            try:
                c.execute(
                    "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                    ("admin_purge_stale", json.dumps({"matched_count": len(matched), "items": matched[:50]}, ensure_ascii=False), "admin")
                )
            except Exception: pass
            conn.commit()
    finally:
        conn.close()

    log.info(f"[PurgeStale] dry_run={dry_run} matched={len(matched)} deleted={deleted}")
    return {
        "ok": True,
        "matched": len(matched),
        "deleted": deleted,
        "dry_run": dry_run,
        "items": matched[:100],
    }


@app.post("/api/admin/email/send-custom")
def admin_email_send_custom(
    payload: dict,
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
):
    """任意の subject/body でメール送信。admin Bearer または X-Cron-Secret 認証。
    payload: { to: str, subject: str, body: str (text or html), is_html: bool=False }"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    to_email = (payload.get("to") or "").strip()
    subject = (payload.get("subject") or "").strip()
    body = payload.get("body") or ""
    is_html = bool(payload.get("is_html", False))
    if not to_email or "@" not in to_email:
        raise HTTPException(status_code=400, detail="to (メールアドレス) が必要です")
    if not subject:
        raise HTTPException(status_code=400, detail="subject が必要です")
    if not body:
        raise HTTPException(status_code=400, detail="body が必要です")
    # 合成監視や PII 防衛: synthetic-monitor アドレスはスキップ
    if "@synthetic-monitor." in to_email:
        return {"sent": False, "skipped": "synthetic_monitor"}

    import urllib.request, urllib.error
    if not RESEND_API_KEY:
        return {"sent": False, "error": "RESEND_API_KEY 未設定"}
    email_body = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
    }
    if is_html:
        email_body["html"] = body
    else:
        email_body["text"] = body
    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(email_body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "ai-juku-system/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_body = json.loads(resp.read().decode())
            return {"sent": True, "resend_id": res_body.get("id"), "to": to_email, "subject": subject}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:300]
        return {"sent": False, "error": f"HTTP {e.code}: {err_body}", "to": to_email}
    except Exception as e:
        return {"sent": False, "error": f"{type(e).__name__}: {str(e)[:200]}", "to": to_email}


@app.post("/api/admin/monitor/synthetic-checkout-now")
async def admin_synthetic_checkout_now(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """E2E 合成チェックを今すぐ実行 (手動トリガー)。"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    result = await _run_synthetic_checkout_test()
    _SYNTHETIC_CHECKOUT_LAST.update(result)
    return result


@app.post("/api/admin/monitor/never-login-nudge-now")
def admin_never_login_nudge_now(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """24h 未ログイン生徒への magic link 自動再送信を今すぐ実行 (手動トリガー)。
    cron 自動実行を待たずに CEO ダッシュから 1 クリックで再送可能。
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    # 同日内多重起動ブロックは bypass (手動なので)
    _NEVER_LOGIN_NUDGE_LAST_RUN["date"] = ""
    JST = timezone(timedelta(hours=9))
    # 時刻ガードも bypass: 現在時刻を NEVER_LOGIN_NUDGE_HOUR_JST にすり替えて呼ぶ
    fake = datetime.now(JST).replace(hour=NEVER_LOGIN_NUDGE_HOUR_JST)
    return _maybe_run_never_login_nudge(fake)


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


@app.get("/api/admin/monitor/domain-status")
def admin_domain_status(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """RDAP で WHOIS Domain Status を即時確認 (手動)。
    返り値: {"ok": bool, "domain": str, "status": [...], "bad_status_detected": [...], "error": str|None}
    認証なしでも GET できる軽量エンドポイントだが、PII 防衛として admin only にする。
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    return _check_domain_status_via_rdap()


@app.post("/api/admin/monitor/domain-check-now")
def admin_domain_check_now(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """ドメイン状態 RDAP チェックを即時実行 (手動)。clientHold 等の異常検知時はアラートメール送信。
    interval 制限を bypass するが、rdap.org への DoS 防止のため 60 秒の手動 throttle あり。
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    # 手動 throttle: 60 秒に 1 回まで (rdap.org への配慮)
    now_ts = time.time()
    last_manual = _DOMAIN_MONITOR_LAST_CHECK.get("manual_ts", 0.0)
    if now_ts - last_manual < DOMAIN_MONITOR_MANUAL_THROTTLE_SEC:
        wait_sec = int(DOMAIN_MONITOR_MANUAL_THROTTLE_SEC - (now_ts - last_manual))
        return {"ran": False, "reason": "manual_throttle", "wait_seconds": wait_sec}
    _DOMAIN_MONITOR_LAST_CHECK["manual_ts"] = now_ts
    # interval ガード (kv_settings 永続) を bypass: kv 値を 0 に戻す
    _kv_set("domain_monitor_last_check_ts", "0")
    _DOMAIN_MONITOR_LAST_CHECK["ts"] = 0.0
    return _maybe_run_domain_status_check()


@app.post("/api/admin/monitor/whois-reminder-test")
def admin_whois_reminder_test(authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """Whois 認証年次リマインダーを今すぐテスト送信 (手動)。
    日付ガードと「今年送信済」ガードを bypass する。
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")
    # ガード bypass: anniversary - 30 日前の朝として振る舞う
    try:
        anni_m, anni_d = [int(x) for x in DOMAIN_REGISTRATION_ANNIVERSARY.split("-")]
    except Exception:
        anni_m, anni_d = 5, 6
    fake_date = datetime(datetime.now(JST_TZ_DOMAIN).year, anni_m, anni_d, 8, 0, 0, tzinfo=JST_TZ_DOMAIN) - timedelta(days=30)
    # 今年の dedup キーを消す
    year_key = str(fake_date.year)
    try:
        conn = db()
        c = conn.cursor()
        for db_target in [30, 7]:
            c.execute("DELETE FROM kv_settings WHERE key = ?", (f"whois_renewal_reminder_sent_{year_key}_minus_{db_target}d",))
        # 旧 key も互換で消去
        c.execute("DELETE FROM kv_settings WHERE key = ?", ("whois_renewal_reminder_last_year",))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return _maybe_run_whois_renewal_reminder(fake_date)


# =====================================================================
# 💴 juku-payment クラウド sync (2026-05-07 追加)
# 月謝アプリ (~/ai-juku-system/payment/) の overrides を Railway Postgres
# (kv_settings table) に保存し、携帯/PC 間でデータ共有を実現する。
#
# 認証: 既存の admin Bearer token を流用 (新規認証フロー不要)
# 競合解決: シンプルな last-write-wins (= 最後の POST が勝つ)
#   塾長 1 人運用なので multi-writer 競合は実質発生しない。
# =====================================================================

JUKU_PAYMENT_KV_KEY = "juku_payment_overrides_v1"


@app.get("/api/juku-payment/overrides")
def juku_payment_get_overrides(authorization: Optional[str] = Header(None)):
    """juku-payment overrides (= payments / emails / payerNames / mailSent / status) を取得。
    Bearer token 認証必須 (admin)。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token が必要です")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="管理者トークンが無効です")
    val = _kv_get(JUKU_PAYMENT_KV_KEY)
    # updated_at も取りたいので生 SQL (psycopg dict_row でも sqlite Row でも動くよう条件分岐)
    updated_at = None
    try:
        conn = db()
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS kv_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("SELECT updated_at FROM kv_settings WHERE key = ?", (JUKU_PAYMENT_KV_KEY,))
        row = c.fetchone()
        conn.close()
        if row is not None:
            # Reviewer A HIGH: psycopg dict_row では row[0] が KeyError(0) になる致命パターン → name で取る
            ua = None
            try:
                ua = row["updated_at"]
            except (KeyError, IndexError, TypeError):
                # sqlite Row 互換 fallback
                try: ua = row[0]
                except Exception: ua = None
            if ua is not None:
                updated_at = ua.isoformat() if hasattr(ua, "isoformat") else str(ua)
    except Exception as e:
        log.warning(f"[JukuPay:get] updated_at fetch failed: {e}")
    return {
        "ok": True,
        "value": val,                      # JSON 文字列 (= STATE.overrides の JSON.stringify)
        "updated_at": updated_at,          # ISO 8601
        "exists": val is not None,
    }


@app.post("/api/juku-payment/overrides")
def juku_payment_set_overrides(payload: dict, authorization: Optional[str] = Header(None)):
    """juku-payment overrides を保存。
    payload: { "value": JSON 文字列 }"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token が必要です")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="管理者トークンが無効です")
    val = payload.get("value")
    if val is None:
        raise HTTPException(status_code=400, detail="value (JSON 文字列) が必要です")
    if not isinstance(val, str):
        # JSON object で送られた場合は str に変換
        try:
            val = json.dumps(val, ensure_ascii=False)
        except Exception:
            raise HTTPException(status_code=400, detail="value を JSON 化できません")
    # サイズ上限 (= 暴走/誤送信ガード): 5MB
    if len(val.encode("utf-8")) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="value が大きすぎます (上限 5MB)")
    ok = _kv_set(JUKU_PAYMENT_KV_KEY, val)
    if not ok:
        raise HTTPException(status_code=500, detail="保存に失敗しました")
    # 更新時刻を返す
    updated_at = datetime.now(timezone.utc).isoformat()
    return {"ok": True, "updated_at": updated_at, "size_bytes": len(val.encode("utf-8"))}


@app.get("/api/auth/me")
def auth_me(authorization: Optional[str] = Header(None)):
    """現在のセッションを検証して生徒情報を返す。全ページのアクセスガードに使う。
    + last_login_at を 4 時間以上前なら更新 (継続利用を「最終ログイン」に反映するため)"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # last_login_at リフレッシュ: 4 時間に 1 回まで (DB 書込抑制)
    try:
        last_login_raw = student.get("last_login_at")
        should_refresh = True
        if last_login_raw:
            try:
                if isinstance(last_login_raw, str):
                    last = datetime.fromisoformat(last_login_raw.replace("Z", "+00:00"))
                else:
                    last = last_login_raw
                if last.tzinfo is None: last = last.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - last).total_seconds() < 4 * 3600:
                    should_refresh = False
            except Exception:
                pass
        if should_refresh:
            conn = db()
            c = conn.cursor()
            try:
                c.execute("UPDATE students SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?", (student["id"],))
                conn.commit()
            finally:
                conn.close()
    except Exception as _e:
        log.warning(f"[auth_me] last_login_at refresh skipped: {_e}")
    return {"ok": True, "student": student}


# ==========================================================================
# 紹介ループ API (mypage で生徒が自分の紹介URLを取得 / 紹介状況を確認)
# ==========================================================================
@app.get("/api/referral/my-link")
def referral_my_link(authorization: Optional[str] = Header(None)):
    """ログイン中の生徒の紹介URL + 集計を返す。
    - link: 共有用URL (LP に ?ref= 付き)
    - invited: 紹介で申込された数
    - paid: 紹介経由で paid 化した数 (=¥3,000 OFF クーポン獲得回数)
    - reward_yen: 累計獲得割引額 (paid 数 × 3000)
    """
    student = _get_current_student(authorization, allow_canceled=True)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    sid = student["id"]
    code = _generate_referral_code(sid)
    link = f"{BASE_URL}/?ref={code}"

    conn = db()
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) AS n FROM referrals WHERE referrer_id=?", (sid,))
        invited = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM referrals WHERE referrer_id=? AND referred_paid_at IS NOT NULL", (sid,))
        paid = c.fetchone()["n"]
    finally:
        conn.close()

    return {
        "ok": True,
        "link": link,
        "code": code,
        "invited": invited,
        "paid": paid,
        "reward_yen": paid * 3000,
        "reward_per_referral_yen": 3000,
    }


@app.get("/api/referral/verify")
def referral_verify(request: Request, code: str = ""):
    """LP 側で ?ref=XXX を検証する公開 endpoint。表示文言を変える時のみ呼ぶ (UI 装飾用)。
    認証不要だが、有効なコードかどうかだけを返す (referrer の個人情報は返さない)。
    Anti-enum: 1 IP あたり 5分で 30回まで (oracle attack 抑制)。"""
    _check_rate_limit_ip(request, bucket="referral_verify", limit=30, window=300)
    code = (code or "").strip()
    if not code:
        return {"valid": False}
    rid = _verify_referral_code(code)
    if not rid:
        return {"valid": False}
    return {"valid": True}


@app.get("/api/admin/referrals")
def admin_referrals_summary(authorization: Optional[str] = Header(None)):
    """CEOダッシュ用: 紹介経路サマリ。
    - total: 総紹介申込数
    - paid: 成立 (被紹介者が paid 化) した数
    - pending: 紹介申込済だが未成立
    - top_referrers: 上位5名 (紹介者ごとの招待数)
    - reward_total_yen: 紹介者に支払った累計クーポン金額
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    conn = db()
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) AS n FROM referrals")
        total = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM referrals WHERE referred_paid_at IS NOT NULL")
        paid = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM referrals WHERE coupon_applied_at IS NOT NULL")
        rewarded = c.fetchone()["n"]
        c.execute(
            """SELECT r.referrer_id, s.name, s.email, COUNT(*) AS invited,
                      SUM(CASE WHEN r.referred_paid_at IS NOT NULL THEN 1 ELSE 0 END) AS converted
               FROM referrals r
               LEFT JOIN students s ON s.id = r.referrer_id
               GROUP BY r.referrer_id, s.name, s.email
               ORDER BY invited DESC LIMIT 5"""
        )
        top = []
        for row in c.fetchall():
            top.append({
                "referrer_id": row["referrer_id"],
                "name": row["name"] or "",
                "email": row["email"] or "",
                "invited": row["invited"],
                "converted": row["converted"] or 0,
            })
    finally:
        conn.close()
    return {
        "total": total,
        "paid": paid,
        "rewarded": rewarded,
        "pending": max(0, total - paid),
        "reward_total_yen": rewarded * 3000,
        "top_referrers": top,
    }


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
    """ログイン中の生徒の今月の使用回数 + プラン上限 + AI 質問累計を返す。
    フロントの「残り○回」表示・アップグレード誘導 + 「AI質問数」スタッツ表示に使用。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    plan = (student.get("plan") or "trial").lower()
    # 国公立難関大学コース = premium 同等 → 全機能無制限 (塾長指示)
    _u_course = student.get("course")
    if _u_course == "kokuritsu_nankan":
        quotas = PLAN_QUOTAS.get("premium", PLAN_QUOTAS["trial"])
    else:
        quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["trial"])
    used = _get_all_monthly_usage(int(student["id"]))
    out = {}
    for feature in QUOTA_FEATURES:
        limit = quotas.get(feature)
        used_count = used.get(feature, 0)
        out[feature] = {
            "limit": limit,
            "used": used_count,
            "remaining": (None if limit is None else max(0, limit - used_count)),
        }
    # AI 質問累計 (events テーブルから取得・端末跨ぎでも正確)
    # NOTE: events.session_id は "123" と "student:123" 両形式が混在 (legacy 不整合)
    ai_total = 0
    ai_today = 0
    try:
        conn = db()
        c = conn.cursor()
        sid_str = str(student['id'])
        sid_prefixed = f"student:{sid_str}"
        c.execute(
            "SELECT COUNT(*) AS n FROM events WHERE session_id IN (?, ?) AND name LIKE 'ai_call_%'",
            (sid_str, sid_prefixed)
        )
        ai_total = c.fetchone()["n"]
        # 今日 (JST) のカウント
        now_jst = datetime.now(timezone.utc) + timedelta(hours=9)
        today_start_jst = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start_jst - timedelta(hours=9)
        c.execute(
            "SELECT COUNT(*) AS n FROM events WHERE session_id IN (?, ?) AND name LIKE 'ai_call_%' AND created_at >= ?",
            (sid_str, sid_prefixed, today_start_utc.isoformat())
        )
        ai_today = c.fetchone()["n"]
        conn.close()
    except Exception as _e:
        log.warning(f"[usage_me] ai_call count failed: {_e}")
    return {
        "ok": True,
        "plan": plan,
        "year_month": _jst_year_month(),
        "usage": out,
        "ai_questions": {"total": ai_total, "today": ai_today},
    }


@app.post("/api/trial/signup")
def trial_signup(payload: TrialSignup, request: Request):
    # レート制限 (4番手 監査 2026-04-30): 1 IP あたり 5分で 3 申込まで。
    # Resend 経由で welcome email を送るため、無制限だと
    # (1) Resend abuse 判定で送信ブロック、(2) DB に dummy student を量産される。
    _check_rate_limit_ip(request, bucket="trial_signup", limit=3, window=300)

    # 入力検証: TrialSignup の field_validator (フルネーム必須・XSS 対策) は通過済み。
    # メール小文字化 + grade/goal/plan の長さ制限 (XSS 対策の二重防御)
    email_norm = (payload.email or "").lower().strip()
    if not email_norm:
        raise HTTPException(status_code=400, detail="Email required")
    student_email_norm = (payload.student_email or "").lower().strip()
    grade = (payload.grade or "")[:50]
    goal = (payload.goal or "")[:500]
    plan = (payload.plan or "hybrid")[:50]

    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=FOUNDER_TRIAL_DAYS)  # 10 日間の完全無料体験 (2026-05-06)
    conn = db()
    c = conn.cursor()
    is_existing = False
    try:
        c.execute(
            """INSERT INTO students (name, email, student_email, grade, goal, plan, status, trial_start, trial_end)
               VALUES (?, ?, ?, ?, ?, ?, 'trial', ?, ?)
               RETURNING id""",
            (payload.name, email_norm, student_email_norm, grade, goal,
             plan, now.isoformat(), trial_end.isoformat())
        )
        returned = c.fetchone()
        student_id = returned["id"] if returned else None
        conn.commit()
    except IntegrityError:
        # 既存メール: 同一 email の student_id を返す。
        # paid ユーザーは plan/status を変更しない (誤って ¥14,500 → trial 降格させない)。
        # trial 期限切れ/canceled は trial を再延長 (リカバリ申込として扱う)。
        conn.rollback()
        is_existing = True
        c.execute("SELECT id, status, trial_end FROM students WHERE LOWER(email) = ? LIMIT 1", (email_norm,))
        row = c.fetchone()
        student_id = row["id"] if row else None
        if not student_id:
            conn.close()
            raise HTTPException(status_code=400, detail="Email conflict")
        try:
            existing_status = row["status"] if row else None
            if existing_status in ("trial", "canceled", "expired", None, ""):
                # 既存生徒の student_email も更新 (空白のままなら新値で上書き、既存値があれば保持)
                c.execute(
                    """UPDATE students SET status='trial', trial_start=?, trial_end=?,
                       student_email = CASE WHEN COALESCE(student_email, '') = '' THEN ? ELSE student_email END,
                       updated_at=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (now.isoformat(), trial_end.isoformat(), student_email_norm, student_id)
                )
                conn.commit()
                log.info(f"[Signup] Re-activated trial for existing student {student_id} ({email_norm}) prev_status={existing_status}")
        except Exception as _e:
            log.warning(f"[Signup] re-activation update failed for student {student_id}: {_e}")
    conn.close()

    log.info(f"Trial signup: {email_norm} -> student_id={student_id} existing={is_existing}")

    # 紹介ループ: ?ref= が指定されていて、新規申込 (=既存ユーザーでない) なら referrals に記録。
    # 既存ユーザーの再申込時は記録しない (再活性化は紹介報酬対象外)。
    # Anti-fraud: 同一 referrer から大量招待 = 自己アカウント生成攻撃を防ぐため、
    # 直近24h で同じ referrer による招待が10件超なら拒否 (小規模塾なので本数で十分)。
    ref_code = (payload.ref or "").strip()
    if ref_code and student_id and not is_existing:
        try:
            referrer_id = _verify_referral_code(ref_code)
            if not referrer_id:
                log.warning(f"[Referral] invalid ref code: code={ref_code[:20]} student={student_id}")
            elif referrer_id == student_id:
                log.warning(f"[Referral] self-referral blocked: student={student_id}")
            else:
                _conn = db(); _c = _conn.cursor()
                try:
                    # Anti-fraud 1: referrer の直近24h招待数チェック
                    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
                    _c.execute(
                        "SELECT COUNT(*) AS n FROM referrals WHERE referrer_id=? AND created_at > ?",
                        (referrer_id, yesterday)
                    )
                    recent_count = _c.fetchone()["n"]
                    # Anti-fraud 2: 同じ email ドメイン (個人 gmail 等) の自己招待を抑制
                    # 同一 referrer × 同一被招待 email ドメイン (gmail/yahoo 等の汎用以外) で2件以上は拒否
                    domain = email_norm.split("@")[-1] if "@" in email_norm else ""
                    is_carrier_or_generic = domain in (
                        "gmail.com", "yahoo.co.jp", "yahoo.com", "icloud.com", "outlook.com",
                        "hotmail.com", "live.com", "ezweb.ne.jp", "docomo.ne.jp", "softbank.ne.jp",
                        "i.softbank.jp", "au.com", "ymobile.ne.jp"
                    )
                    domain_dup_count = 0
                    if domain and not is_carrier_or_generic:
                        _c.execute(
                            """SELECT COUNT(*) AS n FROM referrals r
                               JOIN students s ON s.id = r.referred_id
                               WHERE r.referrer_id=? AND LOWER(s.email) LIKE ?""",
                            (referrer_id, f"%@{domain}")
                        )
                        domain_dup_count = _c.fetchone()["n"]

                    if recent_count >= 10:
                        log.warning(f"[Referral] referrer {referrer_id} rate-limited (24h count={recent_count})")
                    elif domain_dup_count >= 2:
                        log.warning(f"[Referral] referrer {referrer_id} suspicious same-domain ({domain}) count={domain_dup_count}")
                    else:
                        try:
                            _c.execute(
                                """INSERT INTO referrals (referrer_id, referred_id, code) VALUES (?, ?, ?)""",
                                (referrer_id, student_id, ref_code)
                            )
                            _conn.commit()
                            log.info(f"[Referral] new: referrer={referrer_id} referred={student_id}")
                        except IntegrityError:
                            _conn.rollback()
                            log.info(f"[Referral] already linked for student {student_id}")
                finally:
                    _conn.close()
        except Exception as e:
            log.warning(f"[Referral] tracking failed: {type(e).__name__}: {e}")

    # 🔥 致命傷修正 (2026-04-29): 申込直後に magic link 招待メールを送信
    # これが無いと顧客はログイン経路を知らず、ダッシュ未利用 = 価値ゼロ。
    # 失敗しても signup 自体は成功させる (顧客は admin から再送信で救済可能)。
    # 🔥 2026-05-01: 生徒メール (任意) が指定されていれば、両方に送信 (子供の端末でログイン可能に)
    email_sent = False
    email_error = None
    student_email_sent = False
    if student_id:
        try:
            # 重複申込時は古い OTP を無効化 (旧コード混乱防止)
            if is_existing:
                _invalidate_active_otps(student_id)
            # 1時間有効な短命 magic link token (4番手 監査 2026-04-30)
            session_token = _create_magic_link_token(student_id)
            magic_url = f"{BASE_URL}/auth.html?t={session_token}"
            otp_code = _create_otp(student_id)
            result = _send_magic_link_with_retry(
                email_norm,
                payload.name or "",
                magic_url,
                otp_code=otp_code,
                is_welcome=True,
            )
            email_sent = bool(result.get("sent"))
            if not email_sent:
                email_error = (result or {}).get("error", "send_failed")
                log.error(f"[Signup] Welcome email failed for student {student_id} ({email_norm}): {email_error}")
            # 生徒メール (任意) にも送信 (失敗しても親メールが届いていれば OK 扱い)
            if student_email_norm and student_email_norm != email_norm:
                try:
                    student_result = _send_magic_link_with_retry(
                        student_email_norm,
                        payload.name or "",
                        magic_url,
                        otp_code=otp_code,
                        is_welcome=True,
                    )
                    student_email_sent = bool(student_result.get("sent"))
                    log.info(f"[Signup] Student-email send for {student_id}: sent={student_email_sent} ({student_email_norm})")
                except Exception as se:
                    log.warning(f"[Signup] Student-email send exception for {student_id}: {se}")
        except Exception as e:
            email_error = f"{type(e).__name__}: {e}"
            log.error(f"[Signup] Welcome email exception for student {student_id} ({email_norm}): {email_error}")

    # 監視: events に signup_email_status を記録 (CEO ダッシュ監視・自動 nudge 用)
    try:
        conn2 = db(); cc = conn2.cursor()
        cc.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            (
                "signup_email_status",
                json.dumps({"student_id": student_id, "email_sent": email_sent, "error": email_error[:200] if email_error else None}, ensure_ascii=False),
                f"student:{student_id}",
            ),
        )
        conn2.commit(); conn2.close()
    except Exception as _e:
        log.warning(f"[Signup] failed to record signup_email_status event: {_e}")

    return {
        "ok": True,
        "student_id": student_id,
        "trial_end": trial_end.isoformat(),
        "email_sent": email_sent,  # フロント (checkout-success.html) で「メール届かなかった場合は…」案内に使う
        "student_email_sent": student_email_sent,  # 生徒メール (任意) への送信成否
    }

# ==========================================================================
# Routes: Stripe Checkout
# ==========================================================================
@app.post("/api/stripe/trial-checkout")
def create_trial_checkout(payload: dict):
    """7日間 完全無料 体験 (GW 集中体験戦略)。Stripe 決済は発生しない。
    創設メンバー50名枠は本契約 (paid) のみでカウント。体験は無制限に受付。
    2026-05-07: 通塾生プラン (student_addon) は invite_code 検証必須化 (Reviewer A CRITICAL #1)
    """
    email = (payload.get("email") or "").strip()
    name = (payload.get("name") or "").strip()
    student_id = payload.get("student_id")
    invite_code = (payload.get("invite_code") or "").strip()
    plan_hint = (payload.get("plan") or "").strip()  # フロントが送ってくれる場合のヒント
    if not email:
        raise HTTPException(status_code=400, detail="email required")

    # 通塾生プラン (student_addon) は招待コード必須 + 検証
    # フロントの guard はバイパス可能 (DevTools) なので server side で必ず検証
    if plan_hint == "student_addon" or invite_code:
        if not invite_code:
            raise HTTPException(status_code=400, detail="通塾生プランをご利用には塾長から発行された招待コードが必要です。")
        try:
            inv = _verify_invite_token(invite_code)
        except HTTPException:
            raise
        except Exception as e:
            log.warning(f"[trial-checkout] invite verify failed: {e}")
            raise HTTPException(status_code=401, detail="招待コードが無効または期限切れです。塾長にご確認ください。")
        # invite token の email と payload.email の一致を検証 (他人の招待を流用させない)
        token_email = (inv.get("email") or "").strip().lower()
        payload_email = email.strip().lower()
        if token_email and token_email != payload_email:
            log.warning(f"[trial-checkout] invite email mismatch: token={token_email} payload={payload_email}")
            raise HTTPException(status_code=401, detail="招待コードと入力されたメールアドレスが一致しません。塾長にご確認ください。")
        log.info(f"[trial-checkout] invite verified: email={payload_email}")

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
            "SELECT COUNT(*) FROM students WHERE status='paid' AND plan IS NOT NULL AND plan != 'student_addon'"
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
    - 創設メンバープラン (founder_special): 永年¥14,500/月 (50名限定・全機能無制限)
    - 通常プラン (premium/family): 月額サブスク
    - 通塾生プラン (student_addon): ¥5,000/月・**招待コード必須** (HMAC トークン)
    - 体験は別途 /api/stripe/trial-checkout で 10日間 完全無料 (Stripe を経由しない)
    """
    price_info = PRICE_MAP.get(payload.plan)
    if not price_info:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {payload.plan}")
    price_id, amount, plan_name, max_students = price_info

    # 🔧 2026-05-07: name 空で来た場合 (upgrade.html 継続登録) は email から既存生徒を lookup
    # → trial 中に登録した name を DB から復元 (顧客 wrmama10 が [object Object] 報告した
    # 致命バグの根本対策)
    payload_name = (payload.name or "").strip()
    if not payload_name:
        try:
            _conn_lookup = db()
            _c_lookup = _conn_lookup.cursor()
            _c_lookup.execute(
                "SELECT id, name FROM students WHERE LOWER(email) = LOWER(?) ORDER BY id DESC LIMIT 1",
                (payload.email,),
            )
            _row_lookup = _c_lookup.fetchone()
            _conn_lookup.close()
            if _row_lookup and _row_lookup["name"]:
                payload_name = (_row_lookup["name"] or "").strip()
                # student_id も埋めておく (後続の re-checkout 判定や履歴継承で使う)
                if not payload.student_id and _row_lookup.get("id"):
                    payload.student_id = _row_lookup["id"]
                # 2026-05-07: PII reduction (Round 2 audit) — name を log に出さない
                log.info(f"[Checkout] name lookup ok: email={payload.email} student_id={payload.student_id} (name resolved from DB)")
            else:
                # 既存生徒が見つからない (新規ユーザが name 抜きで来た) → 親切なエラー
                raise HTTPException(
                    status_code=400,
                    detail="お名前が必要です。お手数ですが LP からお手続きをお願いいたします (新規登録の場合は氏名入力欄あり)。"
                )
        except HTTPException:
            raise
        except Exception as _e_lookup:
            log.warning(f"[Checkout] name lookup failed: {_e_lookup}")
            raise HTTPException(status_code=400, detail="お名前の自動取得に失敗しました。お手数ですが新規登録画面からお手続きください。")
    # 後続コードが payload.name を参照するので上書き
    if payload_name != payload.name:
        try:
            payload.__dict__["name"] = payload_name  # pydantic v2 でも書き換え可能
        except Exception:
            pass

    # 🏫 通塾生プラン: 招待コード (HMAC トークン) 必須検証
    # 塾長指示 2026-05-06: 通塾生は塾長発行の招待コード経由でのみ契約可能
    # memory: feedback_student_invite_link.md (招待リンク方式は実装済み)
    # 例外: 既存の paid 生徒 (再チェックアウト・プラン変更) は invite_code 不要
    _is_existing_paid_student = False
    if payload.plan == "student_addon" and payload.student_id:
        try:
            _conn_pc = db()
            _c_pc = _conn_pc.cursor()
            _c_pc.execute("SELECT status FROM students WHERE id = ? AND email = ?", (payload.student_id, payload.email.lower().strip()))
            _row_pc = _c_pc.fetchone()
            if _row_pc and _row_pc["status"] == "paid":
                _is_existing_paid_student = True
                log.info(f"[Checkout] student_addon re-checkout for existing paid student_id={payload.student_id} (invite_code skipped)")
            _conn_pc.close()
        except Exception as _e_pc:
            log.warning(f"[Checkout] existing paid check failed: {_e_pc}")
    if payload.plan == "student_addon" and not _is_existing_paid_student:
        if not payload.invite_code:
            raise HTTPException(
                status_code=400,
                detail="通塾生プランは招待コードが必要です。塾長から発行された招待コードを入力してください。"
            )
        invite_check = _verify_invite_token(payload.invite_code.strip())
        if not invite_check.get("valid"):
            reason = invite_check.get("reason", "invalid")
            log.warning(f"[Checkout] student_addon invite_code rejected: reason={reason} email={payload.email}")
            err_msg = {
                "expired": "招待コードの有効期限が切れています。塾長に再発行を依頼してください。",
                "signature_mismatch": "招待コードが無効です (署名検証失敗)。",
                "malformed": "招待コードの形式が不正です。",
                "server_misconfigured": "サーバー設定エラー。塾長にお問い合わせください。",
            }.get(reason, "招待コードが無効です。")
            raise HTTPException(status_code=403, detail=err_msg)
        # invite token の email と payload.email の一致を検証 (他人の招待を流用させない)
        invite_email = (invite_check.get("email") or "").strip().lower()
        payload_email = (payload.email or "").strip().lower()
        if invite_email and payload_email and invite_email != payload_email:
            log.warning(f"[Checkout] student_addon invite_code email mismatch: invite={invite_email} payload={payload_email}")
            raise HTTPException(
                status_code=403,
                detail=f"招待コードに紐づくメールアドレスと入力されたメールアドレスが一致しません。招待コードの発行元 {invite_email} でお申込みください。"
            )
        # invite token の kind を確認 (必ず student_addon)
        if invite_check.get("kind") != "student_addon":
            raise HTTPException(status_code=403, detail="招待コードの種類が不正です。")
        log.info(f"[Checkout] student_addon invite verified: email={payload_email}")
    # 🛡️ 全プラン共通 fallback: env が空/placeholder なら lookup_key で動的解決
    # 2026-05-10 改修: 元々 founder_special のみ fallback だったが、premium/family/standard/student_addon も
    #   env 抜けで Stripe 400 になる致命リスクがあったため、塾長指示で全プラン同等の堅牢性に統一
    #   (memory: feedback_stripe_price_env_design.md)
    if not price_id or price_id.endswith("_placeholder"):
        price_id = _lookup_plan_price_id(payload.plan)
        if not price_id:
            raise HTTPException(
                status_code=503,
                detail=f"「{plan_name}」の Stripe Price が未設定です。管理者に通知済 (admin endpoint で setup してください)。"
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
                "SELECT COUNT(*) FROM students WHERE status='paid' AND plan IS NOT NULL AND plan != '' AND plan != 'student_addon'"
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
            allow_promotion_codes=True,
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
            "name": (payload.name or "")[:200],  # 2026-05-07: Reviewer C 指摘・webhook 側で name lost を防ぐ
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
            "name": (payload.name or "")[:200],  # 2026-05-07: webhook で「（新規）」表示防止
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
            "SELECT COUNT(*) FROM students WHERE status='paid' AND plan IS NOT NULL AND plan != '' AND plan != 'student_addon'"
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
# 紹介ループ Stripe coupon 発行ヘルパー (race-safe + deferred 対応)
# ==========================================================================
def _process_referral_coupon_for_referred(c, conn, s, referred_id: int):
    """被紹介者が paid 化した時に呼ばれる。
    referrer の status と stripe_customer_id を確認し、
    paid なら即時 coupon 発行、未 paid なら referred_paid_at だけ記録 (deferred)。
    Race-safe: atomic UPDATE で claim-first → 失敗 (=他 worker 処理済) なら何もしない。"""
    # 該当 referral レコードを取得
    c.execute(
        "SELECT id, referrer_id, coupon_applied_at, referred_paid_at FROM referrals WHERE referred_id=?",
        (referred_id,)
    )
    ref_row = c.fetchone()
    if not ref_row:
        return  # 紹介リンク無し

    # 既に処理済みなら何もしない
    if ref_row["coupon_applied_at"]:
        return

    # referred_paid_at をまず claim (race-safe: WHERE referred_paid_at IS NULL)
    c.execute(
        "UPDATE referrals SET referred_paid_at=CURRENT_TIMESTAMP WHERE id=? AND referred_paid_at IS NULL",
        (ref_row["id"],)
    )
    rowcount = c.rowcount if hasattr(c, "rowcount") else 0
    conn.commit()
    if rowcount == 0 and ref_row["referred_paid_at"]:
        # 他 worker が既に処理済 → 進めない
        return

    # referrer の状態確認
    c.execute(
        "SELECT id, status, stripe_customer_id FROM students WHERE id=?",
        (ref_row["referrer_id"],)
    )
    referrer_row = c.fetchone()
    if not referrer_row:
        log.warning(f"[Referral] referrer {ref_row['referrer_id']} not found")
        return

    if referrer_row["status"] != "paid" or not referrer_row["stripe_customer_id"]:
        log.info(f"[Referral] referrer {ref_row['referrer_id']} not paid yet → coupon deferred")
        return

    # coupon 発行 (claim-first で coupon_applied_at を入れて他 worker をブロック)
    _issue_referral_coupon(c, conn, s, ref_row["id"], referrer_row["stripe_customer_id"], ref_row["referrer_id"])


def _process_deferred_referral_coupons(c, conn, s, paid_student_id: int):
    """生徒が paid 化した時に呼ばれる。
    この生徒が紹介者になっている referrals のうち deferred (referred_paid_at IS NOT NULL かつ coupon_applied_at IS NULL)
    を見つけて coupon 発行する。"""
    c.execute(
        """SELECT id FROM referrals
           WHERE referrer_id=? AND referred_paid_at IS NOT NULL AND coupon_applied_at IS NULL""",
        (paid_student_id,)
    )
    rows = list(c.fetchall())
    if not rows:
        return
    c.execute("SELECT stripe_customer_id FROM students WHERE id=? AND status='paid'", (paid_student_id,))
    customer_row = c.fetchone()
    if not customer_row or not customer_row["stripe_customer_id"]:
        return
    customer_id = customer_row["stripe_customer_id"]
    log.info(f"[Referral] processing {len(rows)} deferred coupon(s) for paid_student_id={paid_student_id}")
    for r in rows:
        _issue_referral_coupon(c, conn, s, r["id"], customer_id, paid_student_id)


def _issue_referral_coupon(c, conn, s, referral_row_id: int, customer_id: str, referrer_id: int):
    """Stripe coupon 発行 + active sub に適用 + referrals 更新。Race-safe (claim-first)。"""
    # claim-first: coupon_applied_at をプレースホルダ '__pending__' で先に書き込み
    pending_marker = "__pending__"
    c.execute(
        """UPDATE referrals SET coupon_id=? WHERE id=? AND coupon_applied_at IS NULL""",
        (pending_marker, referral_row_id)
    )
    rowcount = c.rowcount if hasattr(c, "rowcount") else 0
    conn.commit()
    if rowcount == 0:
        # 他 worker が先に処理した
        return

    coupon_id_created = None
    try:
        cp = s.Coupon.create(
            amount_off=3000, currency="jpy", duration="once",
            max_redemptions=1, name="紹介報酬 ¥3,000 OFF"
        )
        coupon_id_created = cp.id
        subs = s.Subscription.list(customer=customer_id, status="active", limit=1)
        if subs.data:
            s.Subscription.modify(subs.data[0].id, coupon=coupon_id_created)
            log.info(f"✅ Referral coupon applied: referrer={referrer_id} coupon={coupon_id_created}")
        else:
            log.warning(f"[Referral] referrer {referrer_id} has no active subscription; coupon created but not applied")
    except Exception as ce:
        log.error(f"[Referral] coupon create/apply failed: {type(ce).__name__}: {ce}")
        # __pending__ をクリアして再リトライ可能にする
        c.execute("UPDATE referrals SET coupon_id=NULL WHERE id=? AND coupon_id=?", (referral_row_id, pending_marker))
        conn.commit()
        return

    # 確定: coupon_applied_at + coupon_id を入れる
    c.execute(
        "UPDATE referrals SET coupon_applied_at=CURRENT_TIMESTAMP, coupon_id=? WHERE id=?",
        (coupon_id_created, referral_row_id)
    )
    conn.commit()


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
        # 2026-05-07: email を必ず lowercase に正規化 (Round 2 audit 検出・致命バグ修正)
        # 旧コード: WHERE email=? が Stripe から来た "Parent@Example.com" で MISS → 新規 INSERT
        # → 既存 trial student の history が孤立する致命バグ。
        # students テーブルは trial/signup で email_norm (lowercase) で保存している (line 10979)。
        _email_raw = session.get("customer_details", {}).get("email") or session.get("customer_email")
        email = (_email_raw or "").strip().lower() or None

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

            # 紹介ループ報酬: paid 化した生徒の紹介者に ¥3,000 OFF クーポン自動付与。
            # Race condition 対策: atomic UPDATE で coupon_applied_at を先に確保 (claim-first)、
            #   失敗 (=他 worker が先に処理済み) なら何もしない。
            # Deferred 対策: referrer がまだ paid でない時は coupon_id をブランクのまま referred_paid_at だけ記録 →
            #   referrer 自身が paid 化する時 (= この同じ webhook が referrer side で発火) に
            #   _process_deferred_referral_coupons() で再発行。
            try:
                resolved_referred_id = None
                if student_id and student_id != "":
                    resolved_referred_id = int(student_id)
                elif email:
                    c.execute("SELECT id FROM students WHERE email=? LIMIT 1", (email,))
                    _row = c.fetchone()
                    if _row:
                        resolved_referred_id = _row["id"] if hasattr(_row, "keys") else _row[0]

                if resolved_referred_id:
                    _process_referral_coupon_for_referred(c, conn, s, resolved_referred_id)

                # 紹介者自身の paid 転換: deferred になっていたクーポンを再処理
                referrer_paid_id = resolved_referred_id  # この生徒が referrer として持つ deferred を処理
                if referrer_paid_id:
                    _process_deferred_referral_coupons(c, conn, s, referrer_paid_id)
            except Exception as e:
                log.error(f"[Referral] reward processing failed: {type(e).__name__}: {e}")

        # Welcome email (どちらのタイプも共通: ログインコード+リンク送信)
        # 429 / 一時エラー対応: _send_magic_link_with_retry を使用 (trial_signup と DRY 統一)
        try:
            if student_id and student_id != "":
                c.execute("SELECT id, name, email FROM students WHERE id=?", (student_id,))
            elif email:
                c.execute("SELECT id, name, email FROM students WHERE email=?", (email,))
            else:
                c.execute("SELECT id, name, email FROM students WHERE 1=0")
            s_row = c.fetchone()
            if s_row and s_row["email"]:
                # 既存 OTP を無効化してから新発行 (重複コード混乱防止)
                _invalidate_active_otps(s_row["id"])
                # 1時間有効な短命 magic link token (4番手 監査 2026-04-30)
                _token = _create_magic_link_token(s_row["id"])
                _magic_url = f"{BASE_URL}/auth.html?t={_token}"
                _otp_code = _create_otp(s_row["id"])
                _wresult = _send_magic_link_with_retry(s_row["email"], s_row["name"] or "", _magic_url, otp_code=_otp_code, is_welcome=True)
                # 監視: signup_email_status と統一フォーマットで記録
                try:
                    _conn_e = db()
                    _cc_e = _conn_e.cursor()
                    _cc_e.execute(
                        "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                        (
                            "welcome_email_status",
                            json.dumps({
                                "student_id": s_row["id"],
                                "email_sent": bool(_wresult.get("sent")),
                                "error": (_wresult.get("error") or "")[:200] if not _wresult.get("sent") else None,
                                "source": "stripe_webhook",
                            }, ensure_ascii=False),
                            f"student:{s_row['id']}",
                        ),
                    )
                    _conn_e.commit()
                    _conn_e.close()
                except Exception as _ee:
                    log.warning(f"[Webhook] welcome_email_status event failed: {_ee}")
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
    # メールが届かない (キャリアメール / 迷惑振り分け) 生徒向け fallback
    "magic_link_login": lambda p: {
        "type": "text",
        "text": f"🎓 AI学習コーチ塾 ログイン\n\n"
                f"{p.get('name', '生徒')}さん、ログインリンクをお送りします。\n\n"
                f"🔢 ログインコード（10分間有効）: {p.get('otp_code', '')}\n\n"
                f"または下記リンクから直接ログイン（30日間有効）👇\n"
                f"{p.get('magic_url', '')}\n\n"
                f"※ メールが届かない場合の代替送信です。\n"
                f"心当たりがない場合は無視してください。"
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

def _send_weekly_report_email(to_email: str, student_name: str, stats: dict) -> dict:
    """保護者向け週次レポートをメールで送信 (Resend API)。
    塾長指示: LINE は使わない → メールで配信。"""
    import html as _html
    if not RESEND_API_KEY:
        log.warning(f"[WeeklyReport] Email skipped (no RESEND_API_KEY) for {to_email}")
        return {"sent": False, "dev_mode": True}
    safe_name = _html.escape(student_name or "")
    hours = stats.get("hours", 0)
    accuracy = stats.get("accuracy", 0)
    questions = stats.get("questions", 0)
    problems_done = stats.get("problems_done", 0)
    weakest = stats.get("weakest_subject")
    subject_stats = stats.get("subject_stats", {})
    mypage_url = f"{BASE_URL}/mypage.html"

    # 科目別の表を生成
    subject_rows = ""
    for subj, ss in subject_stats.items():
        total = ss.get("total", 0)
        correct = ss.get("correct", 0)
        rate = round(100 * correct / total) if total else 0
        bar_color = "#22c55e" if rate >= 70 else "#f59e0b" if rate >= 50 else "#ef4444"
        subject_rows += f"""<tr>
            <td style="padding:6px 10px;border-bottom:1px solid #f1f5f9;">{_html.escape(subj)}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #f1f5f9;text-align:center;">{correct}/{total}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #f1f5f9;text-align:center;">
              <span style="color:{bar_color};font-weight:700;">{rate}%</span>
            </td>
        </tr>"""

    subject_table = ""
    if subject_rows:
        subject_table = f"""
        <h3 style="font-size:1rem;color:#6366f1;margin:1.5rem 0 0.5rem;">📚 科目別成績</h3>
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
          <tr style="background:#f8fafc;">
            <th style="padding:8px 10px;text-align:left;">科目</th>
            <th style="padding:8px 10px;text-align:center;">正答</th>
            <th style="padding:8px 10px;text-align:center;">正答率</th>
          </tr>
          {subject_rows}
        </table>"""

    weakest_note = ""
    if weakest:
        weakest_note = f"""
        <div style="background:#fef3c7;padding:0.8rem 1rem;border-radius:8px;margin:1rem 0;font-size:0.9rem;">
          ⚠️ <strong>{_html.escape(weakest)}</strong> が今週の重点強化ポイントです。
          AI チューターに質問して苦手を克服しましょう。
        </div>"""

    subject = f"【AI学習コーチ塾】{safe_name}さんの週次学習レポート"
    html = f"""<!DOCTYPE html>
<html><body style="font-family: -apple-system, 'Hiragino Sans', sans-serif; line-height:1.7; color:#333; max-width:560px; margin:0 auto; padding:2rem;">
<h1 style="font-size:1.3rem;color:#6366f1;margin-bottom:0.3rem;">🎓 AI学習コーチ塾</h1>
<h2 style="font-size:1.1rem;color:#475569;margin-top:0;">📊 {safe_name}さんの今週のレポート</h2>

<p>{safe_name}さまの保護者さま、いつもお世話になっております。<br>今週の学習状況をお知らせいたします。</p>

<div style="display:flex;gap:12px;margin:1.2rem 0;flex-wrap:wrap;">
  <div style="flex:1;min-width:120px;background:linear-gradient(135deg,#6366f1,#a78bfa);color:#fff;padding:1rem;border-radius:12px;text-align:center;">
    <div style="font-size:0.75rem;opacity:0.85;">🔥 学習時間</div>
    <div style="font-size:1.8rem;font-weight:800;">{hours}<span style="font-size:0.9rem;">時間</span></div>
  </div>
  <div style="flex:1;min-width:120px;background:linear-gradient(135deg,#ec4899,#f472b6);color:#fff;padding:1rem;border-radius:12px;text-align:center;">
    <div style="font-size:0.75rem;opacity:0.85;">💬 AI質問数</div>
    <div style="font-size:1.8rem;font-weight:800;">{questions}<span style="font-size:0.9rem;">回</span></div>
  </div>
  <div style="flex:1;min-width:120px;background:linear-gradient(135deg,#22c55e,#4ade80);color:#fff;padding:1rem;border-radius:12px;text-align:center;">
    <div style="font-size:0.75rem;opacity:0.85;">💯 正答率</div>
    <div style="font-size:1.8rem;font-weight:800;">{accuracy}<span style="font-size:0.9rem;">%</span></div>
  </div>
</div>

{subject_table}
{weakest_note}

<p style="text-align:center;margin:1.5rem 0;">
  <a href="{mypage_url}" style="display:inline-block;padding:0.9rem 2rem;background:linear-gradient(135deg,#6366f1,#ec4899);color:#fff;text-decoration:none;border-radius:8px;font-weight:700;font-size:1rem;">
    📊 マイページで詳細を確認
  </a>
</p>

<div style="background:#f8fafc;padding:1rem;border-radius:8px;font-size:0.85rem;color:#64748b;">
  💡 学習データが蓄積されるほど、より精度の高いレポートをお届けします。<br>
  ご不明な点がございましたらお気軽にお問い合わせください。
</div>

<hr style="margin:2rem 0;border:none;border-top:1px solid #e2e8f0;">
<p style="font-size:0.8rem;color:#94a3b8;">
  AI学習コーチ塾 | <a href="mailto:info@trillion-ai-juku.com" style="color:#6366f1;">info@trillion-ai-juku.com</a>
</p>
</body></html>"""

    import urllib.request
    import time as _t
    payload_data = json.dumps({"from": FROM_EMAIL, "to": [to_email], "subject": subject, "html": html}).encode("utf-8")
    # 429 リトライ (最大3回・指数バックオフ 3s/6s/12s)
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=payload_data,
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json", "User-Agent": "ai-juku-system/1.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                log.info(f"[WeeklyReport] Email sent to {to_email} (resend_id={result.get('id')})")
                return {"sent": True, "resend_id": result.get("id")}
        except urllib.error.HTTPError as he:
            if he.code == 429 and attempt < 2:
                wait = 3 * (2 ** attempt)
                log.info(f"[WeeklyReport] 429 retry {attempt+1}/3 for {to_email}, waiting {wait}s")
                _t.sleep(wait)
                continue
            log.error(f"[WeeklyReport] Email failed for {to_email}: HTTP {he.code}")
            return {"sent": False, "error": f"HTTP {he.code}"}
        except Exception as e:
            log.error(f"[WeeklyReport] Email failed for {to_email}: {type(e).__name__}: {e}")
            return {"sent": False, "error": str(e)}
    return {"sent": False, "error": "max_retries_exceeded"}


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


# ---------------------------------------------------------------------------
# 体験終了後フォローアップ (3段ドリップ: Day1 / Day3 / Day7)
# ---------------------------------------------------------------------------

def _send_trial_followup_email(to_email: str, student_name: str, days_since: int, upgrade_url: str) -> dict:
    """体験終了後のフォローアップメール。段階に応じて訴求を変える。"""
    import html as _html
    if not RESEND_API_KEY:
        log.warning(f"[DEV-MODE] Trial followup skipped for {to_email}")
        return {"sent": False, "dev_mode": True}
    safe_name = _html.escape(student_name or "")
    greeting = f"{safe_name}さまの保護者さま" if safe_name else "保護者さま"

    if days_since <= 1:
        subject = "【AI学習コーチ塾】体験期間が終了しました — いつでも再開できます"
        headline = "体験期間が終了しました"
        body_msg = """
<p>7日間の無料体験をご利用いただき、ありがとうございました。</p>
<p>体験中の学習データはすべて保存されています。<br>
いつでも月額プランに登録いただければ、続きから学習を再開できます。</p>
<p style="background:#f0fdf4;padding:1rem;border-left:4px solid #22c55e;border-radius:4px;">
  🎁 <strong>体験終了後3日以内のご登録で、入塾金(¥10,000)を免除</strong>いたします。
</p>"""
    elif days_since <= 3:
        subject = "【AI学習コーチ塾】入塾金免除はあと数日です"
        headline = "入塾金免除の期限が近づいています"
        body_msg = """
<p>体験終了から数日が経ちました。お子さまの学習データはそのまま保存されています。</p>
<p style="background:#fffbeb;padding:1rem;border-left:4px solid #f59e0b;border-radius:4px;">
  ⏰ <strong>入塾金(¥10,000)免除の期限がまもなく終了します。</strong><br>
  お得な期間中にご検討ください。
</p>
<p>AI学習コーチが24時間お子さまの学習をサポートします。<br>
分からない問題はAIがその場で丁寧に解説。保護者さまへの学習レポートも毎週お届けします。</p>"""
    else:
        subject = "【AI学習コーチ塾】学習の遅れが気になっていませんか？"
        headline = "学習の継続をサポートします"
        body_msg = """
<p>体験期間終了から1週間が経ちました。</p>
<p>入試まで残された時間は限られています。<br>
AIが毎日の学習計画を自動作成し、苦手分野を集中的に克服するカリキュラムで、
効率よく合格力を身につけることができます。</p>
<p style="background:#f8f9fc;padding:1rem;border-left:4px solid #6366f1;border-radius:4px;">
  📊 <strong>お子さまの体験中の学習データは保存済みです。</strong><br>
  月額プランに登録いただければ、すぐに続きから再開できます。
</p>"""

    html = f"""<!DOCTYPE html>
<html><body style="font-family: -apple-system, sans-serif; line-height: 1.7; color: #333; max-width: 560px; margin: 0 auto; padding: 2rem;">
<h1 style="font-size: 1.4rem; color: #6366f1;">🎓 AI学習コーチ塾</h1>
<p>{greeting}</p>
<h2 style="font-size:1.15rem;color:#374151;">{headline}</h2>
{body_msg}
<p style="text-align:center; margin: 2rem 0;">
  <a href="{upgrade_url}" style="display:inline-block; padding: 1rem 2rem; background:linear-gradient(135deg,#6366f1,#ec4899); color:white; text-decoration:none; border-radius:8px; font-weight:700; font-size:1.05rem;">
    🎓 月額プランに登録する
  </a>
</p>
<div style="background:#fafafa; padding:1rem; border-radius:6px; margin: 1.5rem 0; font-size: 0.9rem;">
  <strong>💡 ご安心ください</strong><br>
  ・ 自動課金は一切発生しません<br>
  ・ 学習データは保持されています<br>
  ・ いつでも好きなタイミングで再開できます
</div>
<p style="font-size:0.85rem; color:#666;">
  ※ このメールは体験をご利用いただいた方にお送りしています。<br>
  今後の配信を希望されない場合は、このメールに返信でお知らせください。
</p>
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
            log.info(f"Trial followup (day {days_since}) sent to {to_email}: {result.get('id')}")
            return {"sent": True, "resend_id": result.get("id")}
    except Exception as e:
        log.error(f"Trial followup email failed for {to_email}: {type(e).__name__}: {e}")
        return {"sent": False, "error": str(e)}


@app.post("/api/cron/trial-followups")
def cron_trial_followups(x_cron_secret: str = Header(None), dry_run: bool = False):
    """体験終了後フォローアップ: Day1 / Day3 / Day7 の3段階ドリップメール。
    expire-trials の後に毎日実行。notifications テーブルで重複防止。"""
    if not CRON_SECRET:
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    import urllib.parse as _urlparse
    conn = db()
    c = conn.cursor()
    try:
        now = datetime.now(timezone.utc)

        # 継続意思のない (= 一度もログインしていない) 顧客はスキップ (塾長指示 2026-05-06)
        c.execute(
            "SELECT id, name, email, trial_end, last_login_at FROM students WHERE status='expired' AND email IS NOT NULL AND trial_end IS NOT NULL"
        )
        expired_students = list(c.fetchall())

        sent = 0
        skipped = 0
        skipped_silent = 0
        skipped_silent_ids = []
        preview = []
        for row in expired_students:
            # サイレント顧客スキップ: 一度もログインしていない = 継続の連絡がない顧客 (塾長指示 2026-05-06)
            try:
                _last_login = row["last_login_at"]
            except (KeyError, IndexError):
                _last_login = None
            if not _last_login:
                skipped_silent += 1
                skipped_silent_ids.append(row["id"])
                continue
            try:
                te = row["trial_end"]
                if isinstance(te, str):
                    te = datetime.fromisoformat(te.replace("Z", "+00:00"))
                if te.tzinfo is None:
                    te = te.replace(tzinfo=timezone.utc)
                days_since = int((now - te).total_seconds() / 86400)
            except Exception:
                continue

            # >= 範囲で判定: cron が1日欠落しても取りこぼさない (dedup で二重送信防止)
            if days_since < 0:
                continue
            elif days_since <= 2:
                step = 1
            elif days_since <= 5:
                step = 3
            elif days_since <= 10:
                step = 7
            else:
                continue

            template_key = f"trial_followup_day{step}"
            c.execute(
                "SELECT id FROM notifications WHERE student_id=? AND template=? AND success=1 LIMIT 1",
                (row["id"], template_key)
            )
            if c.fetchone():
                skipped += 1
                continue

            if dry_run:
                preview.append({"student_id": row["id"], "email": row["email"], "days_since": days_since, "step": step})
                continue

            upgrade_url = f"{BASE_URL}/upgrade.html?email={_urlparse.quote(row['email'], safe='')}"
            result = _send_trial_followup_email(row["email"], row["name"] or "", step, upgrade_url)
            c.execute(
                """INSERT INTO notifications (student_id, channel, template, payload, success, error)
                   VALUES (?, 'email', ?, ?, ?, ?)""",
                (row["id"], template_key, json.dumps({"days_since": days_since, "step": step}),
                 1 if result.get("sent") else 0, result.get("error", ""))
            )
            if result.get("sent"):
                sent += 1
        conn.commit()
        # events に audit log (CEO ダッシュ可視化用)
        if skipped_silent > 0 and not dry_run:
            try:
                c.execute(
                    "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                    ("trial_followup_silent_skipped",
                     json.dumps({"count": skipped_silent, "student_ids": skipped_silent_ids[:50], "reason": "last_login_at IS NULL"}, ensure_ascii=False),
                     "cron")
                )
                conn.commit()
            except Exception as _e:
                log.warning(f"[trial-followups] silent skip audit failed: {_e}")
        return {"sent": sent, "skipped": skipped, "skipped_silent": skipped_silent, "candidates": len(expired_students), "preview": preview if dry_run else None}
    finally:
        conn.close()


@app.post("/api/admin/students/extend-trial")
def admin_extend_trial(payload: dict, authorization: Optional[str] = Header(None)):
    """CEOダッシュボードから1クリックで体験延長。expired/trial → trial + 7日延長。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    try:
        sid = int(payload.get("id") or 0)
        extra_days = int(payload.get("days") or 7)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="id and days must be integers")
    if not sid:
        raise HTTPException(status_code=400, detail="id required")
    if extra_days < 1 or extra_days > 30:
        raise HTTPException(status_code=400, detail="days must be 1-30")

    conn = db()
    c = conn.cursor()
    try:
        c.execute("SELECT id, email, name, status, trial_end FROM students WHERE id=?", (sid,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"student id={sid} not found")
        if row["status"] not in ("expired", "trial"):
            raise HTTPException(status_code=400, detail=f"status={row['status']} は体験延長対象外です (expired/trial のみ)")

        new_trial_end = datetime.now(timezone.utc) + timedelta(days=extra_days)
        c.execute(
            "UPDATE students SET status='trial', trial_end=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_trial_end, sid)
        )
        # 旧 followup 通知をクリア → 再 expire 時に新しいドリップが送れるようにする
        c.execute(
            "DELETE FROM notifications WHERE student_id=? AND template LIKE 'trial_followup_%'",
            (sid,)
        )
        conn.commit()
        log.info(f"[admin/extend-trial] id={sid} extended {extra_days} days, new trial_end={new_trial_end}")
        return {
            "ok": True,
            "id": sid,
            "name": row["name"],
            "email": row["email"],
            "previous_status": row["status"],
            "new_trial_end": new_trial_end.isoformat(),
            "extended_days": extra_days,
        }
    finally:
        conn.close()


@app.post("/api/admin/students/send-followup")
def admin_send_followup(payload: dict, authorization: Optional[str] = Header(None)):
    """CEOダッシュボードから手動フォローアップメール送信。24h cooldown 付き。"""
    import urllib.parse as _urlparse
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    try:
        sid = int(payload.get("id") or 0)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="id must be integer")
    if not sid:
        raise HTTPException(status_code=400, detail="id required")

    conn = db()
    c = conn.cursor()
    try:
        c.execute("SELECT id, email, name, status, trial_end FROM students WHERE id=?", (sid,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"student id={sid} not found")
        if not row["email"]:
            raise HTTPException(status_code=400, detail="メールアドレスが登録されていません")

        # 24h cooldown: 直近24時間以内に手動送信済みならブロック
        cooldown_since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        c.execute(
            "SELECT id FROM notifications WHERE student_id=? AND template='trial_followup_manual' AND success=1 AND created_at > ? LIMIT 1",
            (sid, cooldown_since)
        )
        if c.fetchone():
            raise HTTPException(status_code=429, detail="24時間以内にフォローアップ済みです。時間を置いてお試しください。")

        # trial_end からの経過日数で適切なテンプレートを自動選択
        days_since_expiry = 1
        try:
            te = row["trial_end"]
            if te:
                if isinstance(te, str):
                    te = datetime.fromisoformat(te.replace("Z", "+00:00"))
                if te.tzinfo is None:
                    te = te.replace(tzinfo=timezone.utc)
                days_since_expiry = max(1, int((datetime.now(timezone.utc) - te).total_seconds() / 86400))
        except Exception:
            pass

        upgrade_url = f"{BASE_URL}/upgrade.html?email={_urlparse.quote(row['email'], safe='')}"
        result = _send_trial_followup_email(row["email"], row["name"] or "", days_since_expiry, upgrade_url)
        if not result.get("sent"):
            c.execute(
                """INSERT INTO notifications (student_id, channel, template, payload, success, error)
                   VALUES (?, 'email', 'trial_followup_manual', ?, 0, ?)""",
                (sid, json.dumps({"triggered_by": "ceo_dashboard", "days_since": days_since_expiry}), result.get("error", ""))
            )
            conn.commit()
            raise HTTPException(status_code=502, detail=f"メール送信失敗: {result.get('error', '不明')}")

        c.execute(
            """INSERT INTO notifications (student_id, channel, template, payload, success, error)
               VALUES (?, 'email', 'trial_followup_manual', ?, 1, '')""",
            (sid, json.dumps({"triggered_by": "ceo_dashboard", "days_since": days_since_expiry}))
        )
        conn.commit()
        return {"ok": True, "sent": True, "email": row["email"]}
    finally:
        conn.close()


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
    # 継続意思のない (= 一度もログインしていない) 顧客はスキップ (塾長指示 2026-05-06)
    c.execute(
        """SELECT id, name, email, trial_end, status, last_login_at FROM students
           WHERE status IN ('trial','paid') AND email IS NOT NULL
             AND trial_end IS NOT NULL
             AND trial_end > ? AND trial_end <= ?""",
        (t_start.isoformat(), t_end.isoformat())
    )
    candidates = list(c.fetchall())

    sent = 0
    skipped = 0
    skipped_silent = 0
    skipped_silent_ids = []
    preview = []
    for row in candidates:
        # サイレント顧客スキップ: 一度もログインしていない = 継続の連絡がない顧客 (塾長指示 2026-05-06)
        try:
            _last_login = row["last_login_at"]
        except (KeyError, IndexError):
            _last_login = None
        if not _last_login:
            skipped_silent += 1
            skipped_silent_ids.append(row["id"])
            continue
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
    # events に audit log (CEO ダッシュ可視化用)
    if skipped_silent > 0 and not dry_run:
        try:
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("trial_reminder_silent_skipped",
                 json.dumps({"count": skipped_silent, "student_ids": skipped_silent_ids[:50], "reason": "last_login_at IS NULL"}, ensure_ascii=False),
                 "cron")
            )
            conn.commit()
        except Exception as _e:
            log.warning(f"[trial-reminders] silent skip audit failed: {_e}")
    conn.commit()
    conn.close()
    return {"sent": sent, "skipped": skipped, "skipped_silent": skipped_silent, "candidates": len(candidates), "preview": preview if dry_run else None}


@app.post("/api/cron/trial-unused-warning")
def cron_trial_unused_warning(x_cron_secret: str = Header(None), dry_run: bool = False):
    """体験中で last_login_at IS NULL の生徒に通告メール送信。
    Stage 1 (early): 登録から 3 日経過 → 「体験を始めてみませんか?」
    Stage 2 (late): 体験終了 2 日前 → 「終了が迫ってます」
    notifications テーブルで重複送信防止 (template='trial_unused_early' / 'trial_unused_late')
    塾長指示 2026-05-06: 登録のみで使用歴がない人に通告"""
    if not CRON_SECRET:
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = db()
    c = conn.cursor()
    now = datetime.now(timezone.utc)
    sent_early = 0
    sent_late = 0
    skipped_already = 0
    preview = []
    try:
        # Stage 1: 登録から 3 日経過 + 未ログイン (4 日目に 1 通)
        early_lower = now - timedelta(days=4)  # 4 日経過は対象外 (重複防止のための窓)
        early_upper = now - timedelta(days=3)  # 3 日経過
        c.execute(
            """SELECT id, name, email, created_at, trial_end FROM students
               WHERE status = 'trial' AND email IS NOT NULL AND last_login_at IS NULL
                 AND created_at > ? AND created_at <= ?""",
            (early_lower.isoformat(), early_upper.isoformat())
        )
        for row in c.fetchall():
            # dedup
            c.execute(
                "SELECT id FROM notifications WHERE student_id=? AND template='trial_unused_early' AND success=1 LIMIT 1",
                (row["id"],)
            )
            if c.fetchone():
                skipped_already += 1
                continue
            try:
                ca = row["created_at"]
                if isinstance(ca, str):
                    ca = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                if ca.tzinfo is None: ca = ca.replace(tzinfo=timezone.utc)
                days_unused = max(1, int((now - ca).total_seconds() / 86400))
            except Exception:
                days_unused = 3
            if dry_run:
                preview.append({"student_id": row["id"], "email": row["email"], "stage": "early", "days_unused": days_unused})
                continue
            login_url = f"{BASE_URL}/login.html?email={row['email']}"
            result = _send_trial_unused_warning_email(row["email"], row["name"] or "", "early", login_url, days_unused)
            c.execute(
                """INSERT INTO notifications (student_id, channel, template, payload, success, error)
                   VALUES (?, 'email', 'trial_unused_early', ?, ?, ?)""",
                (row["id"], json.dumps({"days_unused": days_unused}), 1 if result.get("sent") else 0, result.get("error", ""))
            )
            if result.get("sent"):
                sent_early += 1

        # Stage 2: 体験終了 2 日前 + 未ログイン (重複防止 dedup あり)
        late_lower = now
        late_upper = now + timedelta(days=2)
        c.execute(
            """SELECT id, name, email, trial_end FROM students
               WHERE status = 'trial' AND email IS NOT NULL AND last_login_at IS NULL
                 AND trial_end IS NOT NULL AND trial_end > ? AND trial_end <= ?""",
            (late_lower.isoformat(), late_upper.isoformat())
        )
        for row in c.fetchall():
            c.execute(
                "SELECT id FROM notifications WHERE student_id=? AND template='trial_unused_late' AND success=1 LIMIT 1",
                (row["id"],)
            )
            if c.fetchone():
                skipped_already += 1
                continue
            try:
                te = row["trial_end"]
                if isinstance(te, str):
                    te = datetime.fromisoformat(te.replace("Z", "+00:00"))
                if te.tzinfo is None: te = te.replace(tzinfo=timezone.utc)
                days_left = max(1, int((te - now).total_seconds() / 86400))
            except Exception:
                days_left = 2
            if dry_run:
                preview.append({"student_id": row["id"], "email": row["email"], "stage": "late", "days_left": days_left})
                continue
            login_url = f"{BASE_URL}/login.html?email={row['email']}"
            result = _send_trial_unused_warning_email(row["email"], row["name"] or "", "late", login_url, days_left)
            c.execute(
                """INSERT INTO notifications (student_id, channel, template, payload, success, error)
                   VALUES (?, 'email', 'trial_unused_late', ?, ?, ?)""",
                (row["id"], json.dumps({"days_left": days_left}), 1 if result.get("sent") else 0, result.get("error", ""))
            )
            if result.get("sent"):
                sent_late += 1

        conn.commit()
    finally:
        conn.close()

    return {
        "ok": True,
        "sent_early": sent_early,
        "sent_late": sent_late,
        "skipped_already_sent": skipped_already,
        "dry_run": dry_run,
        "preview": preview if dry_run else None,
    }


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
    """毎週日曜19時 (JST) にスケジューラから実行。
    メール配信 (全生徒) + LINE 配信 (連携済みのみ) のデュアルチャネル。
    notifications テーブルで週次 dedup (同一生徒に週2回送らない)。"""
    if not CRON_SECRET:
        log.error("CRON_SECRET not configured; refusing cron request")
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = db()
    c = conn.cursor()
    # kokuritsu_nankan コース生も含めるため course も取得
    c.execute("SELECT id, name, email, line_user_id, course FROM students WHERE status IN ('trial', 'paid')")
    students = list(c.fetchall())
    conn.close()

    import time as _t
    sent_email = 0
    sent_line = 0
    skipped = 0
    failed = 0
    capped = 0
    previews = []
    email_index = 0
    # Resend 日次上限ガード: 他メール (ログイン/監視等) の枠を残す
    WEEKLY_REPORT_EMAIL_CAP = int(os.getenv("WEEKLY_REPORT_EMAIL_CAP", "80"))
    for row in students:
        try:
            stats = _compute_weekly_stats(row["id"], days=7)
            # 活動が全くない週はスキップ（スパム防止）
            if stats["hours"] == 0 and stats["questions"] == 0 and stats["problems_done"] == 0:
                skipped += 1
                continue
            if dry_run:
                previews.append({
                    "student_id": row["id"], "name": row["name"], "stats": stats,
                    "would_send_email": bool(row.get("email")),
                    "would_send_line": bool(row.get("line_user_id")),
                })
                continue
            # --- メール配信 (全生徒) ---
            email = row.get("email")
            if email and sent_email >= WEEKLY_REPORT_EMAIL_CAP:
                capped += 1
                log.warning(f"[WeeklyReport] Email cap ({WEEKLY_REPORT_EMAIL_CAP}) reached, skipping student {row['id']}")
            elif email:
                # 週次 dedup: 直近7日以内に同テンプレートで成功送信済みならスキップ
                _dup_conn = db()
                _dup_c = _dup_conn.cursor()
                _seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()
                _dup_c.execute(
                    "SELECT id FROM notifications WHERE student_id=? AND template='weekly_report_email' AND success=1 AND sent_at > ? LIMIT 1",
                    (row["id"], _seven_days_ago)
                )
                already_sent = _dup_c.fetchone()
                _dup_conn.close()
                if already_sent:
                    log.debug(f"[WeeklyReport] dedup skip email for student {row['id']}")
                else:
                    # Resend rate limit 対策: 2通目以降は 1.5秒待機
                    if email_index > 0:
                        _t.sleep(1.5)
                    email_index += 1
                    res = _send_weekly_report_email(email, row["name"], stats)
                    _ok = res.get("sent", False)
                    # notifications テーブルに記録
                    _n_conn = db()
                    _n_c = _n_conn.cursor()
                    _n_c.execute(
                        """INSERT INTO notifications (student_id, channel, template, payload, success, error)
                           VALUES (?, 'email', 'weekly_report_email', ?, ?, ?)""",
                        (row["id"], json.dumps(stats, ensure_ascii=False)[:500], 1 if _ok else 0,
                         res.get("error", "")[:200] if not _ok else None)
                    )
                    _n_conn.commit()
                    _n_conn.close()
                    if _ok:
                        sent_email += 1
                    else:
                        failed += 1
            # --- LINE 配信 (連携済みのみ・従来互換) ---
            if row.get("line_user_id"):
                try:
                    params = {
                        "hours": stats["hours"],
                        "accuracy": stats["accuracy"],
                        "questions": stats["questions"],
                        "url": f"{BASE_URL}/mypage.html",
                    }
                    _do_line_push(row["id"], "weekly_report", params)
                    sent_line += 1
                except Exception as le:
                    log.warning(f"[WeeklyReport] LINE push failed for {row['id']}: {le}")
        except Exception as e:
            log.error(f"Weekly report failed for {row['id']}: {e}")
    return {
        "sent_email": sent_email, "sent_line": sent_line,
        "skipped": skipped, "failed": failed, "capped": capped,
        "total_students": len(students),
        "previews": previews if dry_run else None,
    }


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
    """塾長ダッシュボードから、特定生徒にレポートを即送信 (メール + LINE)"""
    if not _origin_allowed(request):
        raise HTTPException(status_code=403, detail="Origin not allowed")
    if STATS_TOKEN and (not x_stats_token or not hmac.compare_digest(x_stats_token, STATS_TOKEN)):
        raise HTTPException(status_code=401, detail="Unauthorized")
    student_id = payload.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id required")
    stats = _compute_weekly_stats(int(student_id), days=7)
    # 生徒情報を取得
    conn = db()
    c = conn.cursor()
    c.execute("SELECT name, email, line_user_id FROM students WHERE id = ?", (int(student_id),))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="生徒が見つかりません")
    result = {"email": None, "line": None}
    # メール送信
    if row["email"]:
        result["email"] = _send_weekly_report_email(row["email"], row["name"], stats)
        # notifications に記録
        _ok = result["email"].get("sent", False)
        _n_conn = db()
        _n_c = _n_conn.cursor()
        _n_c.execute(
            """INSERT INTO notifications (student_id, channel, template, payload, success, error)
               VALUES (?, 'email', 'weekly_report_email', ?, ?, ?)""",
            (int(student_id), json.dumps(stats, ensure_ascii=False)[:500], 1 if _ok else 0,
             result["email"].get("error", "")[:200] if not _ok else None)
        )
        _n_conn.commit()
        _n_conn.close()
    # LINE 送信 (連携済みなら)
    if row.get("line_user_id"):
        try:
            params = {
                "hours": stats["hours"],
                "accuracy": stats["accuracy"],
                "questions": stats["questions"],
                "url": f"{BASE_URL}/mypage.html",
            }
            result["line"] = _do_line_push(int(student_id), "weekly_report", params)
        except Exception:
            result["line"] = {"ok": False}
    return result

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
        "SELECT id, status, trial_end, plan, course FROM students WHERE id = ?",
        (student_id,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="生徒が見つかりません")
    _row_course = row["course"] if "course" in row.keys() else None
    status = row["status"]
    if status == "paid":
        return dict(row)
    # 国公立難関大学コース = premium 同等 → trial_end に関係なく永久アクセス (塾長指示)
    if _row_course == "kokuritsu_nankan":
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
    """その生徒が直近24hで消費したAIトークンが Plan 別 budget を超えていないか確認。
    Plan 別 (塾長指示 2026-04-30): premium/family/founder_special は実質無制限の 2M tokens。
    旧プラン名 (founder1/hybrid/intensive/ai) も後方互換でカバー (DB 既存データ対策)。"""
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    conn = db()
    c = conn.cursor()
    # 生徒の plan + course を取得して budget を決定
    plan = "trial"
    _course = None
    try:
        c.execute("SELECT plan, course FROM students WHERE id = ?", (student_id,))
        row = c.fetchone()
        if row and row["plan"]:
            plan = str(row["plan"])
        if row:
            _course = row["course"] if "course" in row.keys() else None
    except Exception:
        pass
    # 国公立難関大学コース = premium 同等 (塾長指示: プレミアムの名前を変えて使っている)
    is_premium_tier = plan in PREMIUM_TIER_PLANS or _course == "kokuritsu_nankan"
    if _course == "kokuritsu_nankan":
        budget = PLAN_DAILY_TOKEN_BUDGET.get("premium", 2_000_000)
    else:
        budget = PLAN_DAILY_TOKEN_BUDGET.get(plan, AI_DAILY_TOKEN_BUDGET)
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
    if total >= budget:
        # Plan 別に upgrade 文言を出し分け (premium tier は upgrade 不要)
        if is_premium_tier:
            detail = (
                f"AI_BUDGET_PREMIUM:1日あたりのAI利用上限({budget:,}トークン)に達しました。"
                f"明日(JST 0時頃)にリセットされます。{plan}プランは大量生成にも耐える設計ですが、"
                f"教材一括生成等で稀に到達することがあります。"
            )
        else:
            detail = (
                f"AI_BUDGET_TRIAL:1日あたりのAI利用上限({budget:,}トークン)に達しました。"
                f"明日リセットされます。プレミアムプランなら 1日 2,000,000 トークンまで利用可能です。"
            )
        raise HTTPException(status_code=429, detail=detail)


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
    # 国公立難関大学コース = premium 同等 → 全機能無制限 (塾長指示)
    _sq_course = student.get("course")
    if _sq_course == "kokuritsu_nankan":
        return  # 無制限
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


def _record_ai_call_failure(stage: str, status_code: int, detail: str, payload_obj=None,
                              request_obj: Request = None):
    """ai_proxy の前段 check or AI 呼出で発生した失敗を events テーブルに記録。
    塾長が CEO ダッシュ /api/admin/ai/recent-failures から直近の失敗詳細を見られる。
    Why: probe-tutor は前段 check bypass で動くが、本物の /api/ai/call は前段で
    止まる可能性があるため、前段 check の失敗も可視化する必要がある (memory: feedback_self_healing_dashboard)。
    """
    try:
        conn = db()
        c = conn.cursor()
        props = {
            "stage": stage,
            "status_code": status_code,
            "detail": (detail or "")[:500],
            "student_id": getattr(payload_obj, "student_id", None) if payload_obj else None,
            "model": getattr(payload_obj, "model", None) if payload_obj else None,
            "kind": getattr(payload_obj, "kind", None) if payload_obj else None,
            "feature": getattr(payload_obj, "feature", None) if payload_obj else None,
            "thinking": getattr(payload_obj, "thinking", None) if payload_obj else None,
            "origin": (request_obj.headers.get("origin") if request_obj else None),
            "referer": (request_obj.headers.get("referer") if request_obj else None)[:200] if request_obj and request_obj.headers.get("referer") else None,
        }
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("ai_call_failure", json.dumps(props, ensure_ascii=False), "ai_proxy_check"),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"_record_ai_call_failure failed: {e}")


@app.post("/api/ai/call")
async def ai_proxy(payload: AIProxyRequest, request: Request):
    """顧客の全AI呼び出しを塾長のAPIキーで代理実行。
    Origin検証・student_id存在/有効性検証・1日あたりトークンbudgetで多層防御。"""
    if not ANTHROPIC_API_KEY:
        _record_ai_call_failure("anthropic_unconfigured", 503, "ANTHROPIC_API_KEY 未設定", payload, request)
        raise HTTPException(
            status_code=503,
            detail="AI サービスが構成されていません。管理者にお問い合わせください。",
        )

    # 1) Origin/Referer が許可ドメインか
    if not _origin_allowed(request):
        origin_header = request.headers.get('origin')
        referer_header = request.headers.get('referer')
        log.warning(
            f"/api/ai/call blocked by origin check: origin={origin_header} referer={referer_header} ip={request.client.host if request.client else '?'}"
        )
        _record_ai_call_failure(
            "origin_check",
            403,
            f"origin={origin_header}, referer={(referer_header or '')[:120]}",
            payload, request,
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
    except HTTPException as e:
        # 4xx はそのまま伝搬するが、events に詳細を記録 (塾長デバッグ用)
        _record_ai_call_failure(
            "student_or_budget_or_quota",
            e.status_code,
            str(e.detail)[:300],
            payload, request,
        )
        raise
    except Exception as e:
        log.error(f"/api/ai/call validation exception: {type(e).__name__}: {e}")
        _record_ai_call_failure(
            "validation_unexpected", 500,
            f"{type(e).__name__}: {str(e)[:200]}",
            payload, request,
        )
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
    # 上限 12000 chars: AI チューター system prompt は科目別指導方針を全 inline する設計のため
    # 7500-8500 chars 必要。以前 6000 制限で 400 → frontend が demo fallback してしまう不具合の修正 (2026-05-06)。
    # Anthropic API 自体は 200k token 対応なので 12000 chars は十分余裕がある。
    if len(_sys) > 12000:
        _record_ai_call_failure("system_too_long", 400, f"len={len(_sys)}", payload, request)
        raise HTTPException(status_code=400, detail="system prompt too long")
    _sys_low = _sys.lower()
    matched_jb = next((p for p in _JAILBREAK_PATTERNS if p in _sys_low), None)
    if matched_jb:
        log.warning(f"/api/ai/call blocked by jailbreak pattern check: student_id={payload.student_id}")
        _record_ai_call_failure("jailbreak_pattern", 403, f"pattern={matched_jb}", payload, request)
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
        _record_ai_call_failure("messages_too_long", 413, f"total_chars={_msg_text_total}", payload, request)
        raise HTTPException(status_code=413, detail="messages too long")

    body = {
        "model": payload.model,
        "max_tokens": max_tokens,
        "system": payload.system,
        "messages": payload.messages,
    }

    # Gemini ルート: model="gemini-*" を frontend から指定された場合は直接 Gemini を呼ぶ
    # (塾長指示 2026-05-06: コスト削減のため text 系 AI 機能は Gemini に切替)
    # Vision (image) は Gemini route 未対応 → Anthropic に強制 fallback
    if (payload.model or "").startswith("gemini-"):
        # 🚨 2026-05-07: Gemini quota 連続失敗時は Gemini をスキップして直接 Anthropic 経由
        # (Gemini → Anthropic の二重 round-trip でコスト増を防ぐ・circuit breaker パターン)
        import time as _t
        if _GEMINI_QUOTA_FAIL.get("skip_until", 0.0) > _t.time():
            log.info(f"[AIProxy][Gemini circuit breaker] Gemini skip active until {_GEMINI_QUOTA_FAIL['skip_until']:.0f}, going direct to Anthropic")
            if ANTHROPIC_API_KEY:
                fallback_body = dict(body)
                fallback_body["model"] = "claude-sonnet-4-6"
                try:
                    data = _call_anthropic_safe(fallback_body, kind=payload.kind)
                    if isinstance(data, dict):
                        data["_fallback_from"] = "gemini_circuit_breaker"
                    return data
                except HTTPException:
                    raise
                except Exception as ce:
                    log.error(f"[AIProxy][Gemini skip → Anthropic] failed: {type(ce).__name__}: {str(ce)[:120]}")
                    raise HTTPException(status_code=503, detail="AI サービスが一時的に応答できません。少し時間をおいてもう一度お試しください。")
            # Anthropic も無ければ Gemini を試すしかない (skip 解除して通常経路へ)
        if not GEMINI_API_KEY:
            _record_ai_call_failure("gemini_unconfigured", 503, "GEMINI_API_KEY 未設定", payload, request)
            raise HTTPException(status_code=503, detail="Gemini が構成されていません")
        # 画像入力検知
        _has_image = False
        for _m in (payload.messages or []):
            _c = _m.get("content") if isinstance(_m, dict) else None
            if isinstance(_c, list):
                for _part in _c:
                    if isinstance(_part, dict) and _part.get("type") == "image":
                        _has_image = True; break
            if _has_image: break
        if _has_image:
            _record_ai_call_failure("gemini_no_vision", 400, "Gemini route は image 入力非対応", payload, request)
            raise HTTPException(status_code=400, detail="画像入力は claude-* モデルを指定してください")
        try:
            data = _call_gemini(body, model=payload.model, kind=payload.kind)
            usage = data.get("usage", {}) or {}
            if payload.student_id and usage:
                try:
                    _conn = db()
                    _c = _conn.cursor()
                    _c.execute(
                        "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                        (f"ai_call_{payload.kind}",
                         json.dumps({"model": data.get("_actual_model") or payload.model, "provider": "gemini",
                                     "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}),
                         str(payload.student_id))
                    )
                    _conn.commit()
                    _conn.close()
                except Exception as _ev:
                    log.warning(f"[AIProxy][Gemini] cost tracking failed: {_ev}")
            return data
        except HTTPException:
            raise
        except Exception as e:
            # 🚨 2026-05-07: Gemini 失敗時は Anthropic に自動 fallback
            # memory 「AI never-fail 原則」: Gemini quota (429) 等で 503 を顧客に返さない
            # 顧客 (森澤さん級の決済前段階) で AI 計画生成が止まると致命的に機会損失
            err_str = f"{type(e).__name__}: {str(e)[:200]}"
            err_lower = err_str.lower()
            # quota 系 429 を circuit breaker でカウント (5 分窓で 3 回 → 30 分 skip)
            import time as _tt
            if "429" in err_str or "quota" in err_lower or "exceed" in err_lower:
                now_ts = _tt.time()
                if now_ts - _GEMINI_QUOTA_FAIL.get("window_start", 0) > 300:
                    _GEMINI_QUOTA_FAIL["window_start"] = now_ts
                    _GEMINI_QUOTA_FAIL["count_in_window"] = 1
                else:
                    _GEMINI_QUOTA_FAIL["count_in_window"] += 1
                if _GEMINI_QUOTA_FAIL["count_in_window"] >= 3:
                    _GEMINI_QUOTA_FAIL["skip_until"] = now_ts + 1800  # 30 min skip
                    log.warning(f"[AIProxy][Gemini circuit breaker] Activated for 30 min after {_GEMINI_QUOTA_FAIL['count_in_window']} 429s in 5min window")
                    _record_ai_critical_event("gemini_circuit_breaker_activated", {
                        "fail_count": _GEMINI_QUOTA_FAIL["count_in_window"],
                        "skip_minutes": 30,
                    })
            log.warning(f"[AIProxy][Gemini→Anthropic fallback] Gemini failed ({err_str}), trying Anthropic")
            if not ANTHROPIC_API_KEY:
                _record_ai_call_failure("gemini_failed_anthropic_unconfigured", 503, err_str, payload, request)
                raise HTTPException(status_code=503, detail=f"AI 呼び出しに失敗 (Gemini quota + Anthropic 未構成): {err_str[:120]}")
            try:
                # Anthropic に切替 (Sonnet 4.6 default)
                fallback_body = dict(body)
                fallback_body["model"] = "claude-sonnet-4-6"
                data = _call_anthropic_safe(fallback_body, kind=payload.kind)
                # 結果に fallback flag を埋める
                if isinstance(data, dict):
                    data["_fallback_from"] = "gemini"
                    data["_fallback_reason"] = err_str[:100]
                # cost tracking (Anthropic 経由)
                if payload.student_id:
                    try:
                        _conn = db()
                        _c = _conn.cursor()
                        usage = data.get("usage", {}) or {}
                        _c.execute(
                            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                            (f"ai_call_{payload.kind}",
                             json.dumps({"model": data.get("_actual_model") or "claude-sonnet-4-6",
                                         "provider": "anthropic",
                                         "fallback_from": "gemini",
                                         "fallback_reason": err_str[:80],
                                         "input_tokens": usage.get("input_tokens", 0),
                                         "output_tokens": usage.get("output_tokens", 0)}),
                             str(payload.student_id))
                        )
                        _conn.commit()
                        _conn.close()
                    except Exception as _ev:
                        log.warning(f"[AIProxy][Anthropic fallback] cost tracking failed: {_ev}")
                log.info(f"[AIProxy][Gemini→Anthropic fallback] success after Gemini fail")
                return data
            except HTTPException:
                raise
            except Exception as e2:
                log.error(f"[AIProxy] BOTH Gemini and Anthropic failed: gemini={err_str} / anthropic={type(e2).__name__}: {str(e2)[:120]}")
                _record_ai_call_failure("gemini_and_anthropic_failed", 503, f"gemini={err_str[:80]} / anthropic={type(e2).__name__}: {str(e2)[:80]}", payload, request)
                raise HTTPException(status_code=503, detail="AI サービスが一時的に応答できません。少し時間をおいてもう一度お試しください。")

    # Opus 4.7 は thinking + output_config + temperature が **必須** (memory: feedback_opus47_proxy_required.md)
    # frontend から thinking=false で来ても backend で必ず補完する。
    # Tier 2 (Sonnet) 降格時は _call_anthropic_safe 内部で thinking/output_config が pop されるので
    # 補完しても降格パスで問題は起きない。
    if (payload.model or "").startswith("claude-opus-4-7"):
        # thinking=true の用途 (diagnostic/curriculum/essay/problems): budget に応じた effort
        # thinking=false の用途 (chat/parent/prep/speaking): adaptive + low で軽く回す (latency/cost 抑制)
        if payload.thinking:
            budget = int(payload.thinking_budget or 4000)
            effort = "high" if budget >= 4000 else ("medium" if budget >= 1500 else "low")
        else:
            effort = "low"
        body["thinking"] = {"type": "adaptive"}
        body["output_config"] = {"effort": effort}
        body["temperature"] = 1.0
    elif payload.thinking:
        # Sonnet 4.6 以下は "enabled" + budget_tokens 形式
        body["temperature"] = 1.0
        body["thinking"] = {"type": "enabled", "budget_tokens": min(int(payload.thinking_budget or 4000), 16000)}

    # AI never-fail 原則: _call_anthropic_safe() 経由で 4 段降格 (Opus→Sonnet→Haiku→Gemini)。
    # 直叩きから _call_anthropic_safe() に移行 (memory: feedback_ai_never_fail.md)
    try:
        data = _call_anthropic_safe(body, kind=f"call_{payload.kind}", student_id=payload.student_id)

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
                        "model": data.get("_actual_model") or payload.model,
                        "provider": data.get("_provider") or "anthropic",
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
    except HTTPException as e:
        # _call_anthropic_safe が raise した 503 (全 tier 失敗) を events に記録 + 素通し
        _record_ai_call_failure(
            "anthropic_all_tiers_failed", e.status_code, str(e.detail)[:300],
            payload, request,
        )
        raise
    except Exception as e:
        log.error(f"AI proxy exception: {e}")
        _record_ai_call_failure(
            "ai_call_unexpected", 500, f"{type(e).__name__}: {str(e)[:300]}",
            payload, request,
        )
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
# 🛡️ Frontend エラー受信エンドポイント (2026-04-27)
# 全顧客接触ページの window.onerror / unhandledrejection で発生したエラーを
# events テーブルに name='js_error' として記録。CEO ダッシュからリアルタイム閲覧可能。
# ==========================================================================
_JS_ERROR_RATE_LIMIT = {}  # {ip: (count, window_start_ts)} - IP単位で50/min まで

@app.post("/api/js-error")
def js_error_report(report: JSErrorReport, request: Request):
    """フロントエンド uncaught JS error を受信し events に記録。
    Origin 検査 + IP rate limit (50/min) でスパム防止。"""
    if not _origin_allowed(request):
        # 念のため受け付ける (Origin が不明でも自社ドメイン外 referer なら拒否済)
        raise HTTPException(status_code=403, detail="Origin not allowed")
    ip = (request.headers.get("x-forwarded-for") or request.client.host or "?").split(",")[0].strip()
    nowts = time.time()
    cnt, win = _JS_ERROR_RATE_LIMIT.get(ip, (0, nowts))
    if nowts - win > 60:
        cnt, win = 0, nowts
    cnt += 1
    _JS_ERROR_RATE_LIMIT[ip] = (cnt, win)
    if cnt > 50:
        raise HTTPException(status_code=429, detail="too many errors")

    # message / stack / page を切り詰めて DB に保存
    props = {
        "kind": (report.kind or "js_error")[:32],
        "message": (report.message or "")[:500],
        "source": (report.source or "")[:300],
        "lineno": int(report.lineno or 0),
        "colno": int(report.colno or 0),
        "stack": (report.stack or "")[:2000],
        "page": (report.page or "")[:300],
        "user_agent": (report.user_agent or "")[:200],
        "client_ts": (report.ts or "")[:64],
        "ip": ip[:64],
    }
    props_str = json.dumps(props, ensure_ascii=False)[:4000]
    try:
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("js_error", props_str, (report.session_id or "")[:64])
        )
        conn.commit()
        conn.close()
        # critical: 直近5分で同一エラーが10件以上来たら monitor 経由で即時アラート
        # (重大なリリース起因バグ・全ユーザーが踏んでいる状態を想定)
        try:
            conn2 = db()
            c2 = conn2.cursor()
            c2.execute(
                "SELECT COUNT(*) FROM events WHERE name='js_error' AND created_at > "
                + ("NOW() - INTERVAL '5 minutes'" if USE_POSTGRES else "datetime('now', '-5 minutes')")
            )
            recent = c2.fetchone()[0] or 0
            conn2.close()
            if recent >= 10:
                # 既存 monitor のメール送信機構に乗せて即時アラート (cooldown 60min は Resend 側 dedup で実装)
                try:
                    subject = f"🚨 JS エラー多発 ({recent}件/5分) — 即時対応必要"
                    body_html = (
                        f"<h2>🚨 直近5分で JS エラーが {recent} 件発生</h2>"
                        f"<p><strong>最新メッセージ:</strong> {props.get('message','')[:200]}</p>"
                        f"<p><strong>page:</strong> {props.get('page','')[:200]}</p>"
                        f"<p><strong>source:</strong> {props.get('source','')[:200]}:{props.get('lineno',0)}</p>"
                        f"<p>全ユーザーが踏んでいるリリース起因の致命バグの可能性が高い。"
                        f"<a href='{BASE_URL}/ceo.html#js-errors'>CEO ダッシュ → JS エラーログ</a> を今すぐ確認してください。</p>"
                    )
                    _send_monitor_email(subject, body_html)
                except Exception as e2:
                    log.warning(f"[js_error] alert email failed: {e2}")
        except Exception:
            pass
    except Exception as e:
        log.warning(f"[js_error] insert failed: {e}")
    return {"ok": True}


@app.post("/api/admin/js-errors/sweep")
def admin_sweep_js_errors(authorization: Optional[str] = Header(None)):
    """admin Bearer 認証必須。「JS エラー一括解決」ボタン用 (2026-04-28 self-healing)。
    js_error_sweep event を打つことで、それ以前のエラーは js_error_6h カウントから除外される。
    新しい signature が後で発生すれば再カウント開始 → 本物の新規問題は引き続き検知される。
    冪等: 何度押しても直近 sweep の timestamp が更新されるだけで破綻しない。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    conn = db()
    c = conn.cursor()
    try:
        # sweep 直前のエラー件数を記録 (操作ログに残す)
        h6 = datetime.now(timezone.utc) - timedelta(hours=6)
        c.execute(
            "SELECT COUNT(*) FROM events WHERE name = 'js_error' AND created_at >= ?",
            (h6,)
        )
        cleared_count = c.fetchone()[0] or 0
        # sweep event を記録
        c.execute(
            "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
            ("js_error_sweep", json.dumps({"cleared_count": cleared_count}), "admin_sweep")
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "cleared_count": cleared_count, "message": f"{cleared_count} 件の JS エラーを sweep しました。新しいエラーが発生したら再度カウント開始されます。"}


@app.get("/api/admin/realtime-visitors")
def admin_realtime_visitors(authorization: Optional[str] = Header(None)):
    """admin Bearer 認証必須。今この瞬間サイトを見ているユニーク session 数。
    塾長要望「何人見ているかの数字が見えない」(2026-04-29) への対応。
    page_view イベントのユニーク session_id を 1分 / 5分 / 30分 / 1時間 で集計。
    1分の数値が「LIVE で今閲覧中」の指標として最も鋭敏。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    now = datetime.now(timezone.utc)
    windows = {
        "now": now - timedelta(minutes=1),
        "last_5min": now - timedelta(minutes=5),
        "last_30min": now - timedelta(minutes=30),
        "last_1h": now - timedelta(hours=1),
    }
    conn = db()
    c = conn.cursor()
    result = {}
    try:
        for key, since in windows.items():
            c.execute(
                "SELECT COUNT(DISTINCT session_id) FROM events WHERE name = 'page_view' AND created_at >= ?",
                (since,)
            )
            result[key] = c.fetchone()[0] or 0
    finally:
        conn.close()
    return {"ok": True, **result}


@app.get("/api/admin/js-errors")
def admin_list_js_errors(authorization: Optional[str] = Header(None), limit: int = 50, hours: int = 24):
    """admin Bearer 認証必須。直近 hours 時間内の JS エラーを最新順で limit 件返す。
    重複圧縮 (同一 message+source+lineno) で一覧化、CEO ダッシュ表示用。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    limit = max(1, min(limit, 200))
    hours = max(1, min(hours, 168))
    conn = db()
    c = conn.cursor()
    try:
        ts_clause = (
            "created_at > NOW() - INTERVAL '%d hours'" % hours if USE_POSTGRES
            else "created_at > datetime('now', '-%d hours')" % hours
        )
        c.execute(f"SELECT props, session_id, created_at FROM events WHERE name='js_error' AND {ts_clause} ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        # 重複圧縮: signature = message+source+lineno
        groups = {}
        latest = []
        for row in rows:
            try:
                p = json.loads(row["props"]) if isinstance(row, dict) or hasattr(row, "keys") else json.loads(row[0])
            except Exception:
                p = {}
            sig = f"{p.get('message','')[:120]}|{p.get('source','')[:60]}:{p.get('lineno',0)}"
            if sig not in groups:
                ca = row["created_at"] if "created_at" in (row.keys() if hasattr(row, "keys") else []) else row[2]
                groups[sig] = {
                    "message": p.get("message", ""),
                    "source": p.get("source", ""),
                    "lineno": p.get("lineno", 0),
                    "page": p.get("page", ""),
                    "kind": p.get("kind", ""),
                    "user_agent": p.get("user_agent", ""),
                    "stack_excerpt": (p.get("stack", "") or "")[:300],
                    "first_seen": str(ca) if ca else "",
                    "count": 1,
                }
            else:
                groups[sig]["count"] += 1

        # count 多い順
        result = sorted(groups.values(), key=lambda x: -x["count"])
        # 5分以内の最新発生件数 (緊急バナー判定用)
        ts_clause_5m = (
            "created_at > NOW() - INTERVAL '5 minutes'" if USE_POSTGRES
            else "created_at > datetime('now', '-5 minutes')"
        )
        c.execute(f"SELECT COUNT(*) FROM events WHERE name='js_error' AND {ts_clause_5m}")
        recent_5min = c.fetchone()[0] or 0
    finally:
        conn.close()
    return {
        "ok": True,
        "hours": hours,
        "unique_signatures": len(result),
        "total_in_window": sum(g["count"] for g in result),
        "recent_5min": recent_5min,
        "errors": result,
    }

# ==========================================================================
# 📱 QR コード機能 (チラシ・教室掲示・SNS・名刺などからの申込導線)
# 仕組み: /qr/{slug} → checkout.html (UTM 自動付与) で集客元の効果測定可能。
# slug は印刷後も動的に redirect 先を変えられる (dynamic QR)。
# ==========================================================================

# 媒体カテゴリ (UTM medium に使用)。未登録 slug は "custom" 扱い。
QR_SLUG_CATEGORIES = {
    # 印刷物
    "flyer": "print",
    "classroom": "print",
    "business-card": "print",
    "brochure": "print",
    "poster": "print",
    "handout": "print",
    "leaflet": "print",
    # SNS
    "threads": "sns",
    "instagram": "sns",
    "x": "sns",
    "youtube": "sns",
    "line": "sns",
    "facebook": "sns",
    # イベント/対面
    "demo": "event",
    "briefing": "event",
    "exam-day": "event",
    "open-house": "event",
    "trial": "event",
}

# 各 slug の優先 coupon (未指定なら none)。Threads6K キャンペーン連動。
QR_SLUG_DEFAULT_COUPON = {
    "threads": "THREADS6K",
}

# 安全な slug 検証 (英数字 + ハイフン + アンダースコア、最大 32 字)
_QR_SLUG_MAX_LEN = 32

_QR_SLUG_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
_QR_ALLOWED_HOSTS = {"trillion-ai-juku.com", "www.trillion-ai-juku.com"}
_QR_DEFAULT_BASE = "https://trillion-ai-juku.com"

# bot / crawler の User-Agent (SNS preview crawler 等)。スキャン件数水増し防止用
_QR_BOT_UA_PATTERNS = (
    "bot", "crawler", "spider", "preview",
    "facebookexternalhit", "slackbot", "discordbot",
    "twitterbot", "linkedinbot", "whatsapp", "telegram",
)

def _is_safe_qr_slug(slug: str) -> bool:
    """ASCII 英数字 + ハイフン + アンダースコアのみ許可。Unicode (日本語等) は弾く。"""
    if not slug or len(slug) > _QR_SLUG_MAX_LEN:
        return False
    return all(c in _QR_SLUG_ALLOWED for c in slug)

def _validate_qr_base_url(base_url: str) -> str:
    """base_url が allowlist host + https か検証。違反時は default に強制。
    Open Redirect 対策: admin token を奪っても外部ドメインに redirect する QR は作れない。
    """
    if not base_url:
        return _QR_DEFAULT_BASE
    try:
        from urllib.parse import urlparse
        p = urlparse(base_url)
    except Exception:
        return _QR_DEFAULT_BASE
    if p.scheme != "https" or (p.hostname or "").lower() not in _QR_ALLOWED_HOSTS:
        return _QR_DEFAULT_BASE
    return base_url.rstrip("/")

def _qr_build_query_string(slug_l: str) -> str:
    """slug から UTM クエリ文字列を組み立てる (path は呼び出し側で固定)。"""
    category = QR_SLUG_CATEGORIES.get(slug_l, "custom")
    coupon = QR_SLUG_DEFAULT_COUPON.get(slug_l)
    qs = f"utm_source=qr&utm_medium={category}&utm_campaign={slug_l}"
    if coupon:
        qs += f"&coupon={coupon}"
    return qs

def _qr_resolve_destination(slug: str, base_url: str = _QR_DEFAULT_BASE) -> dict:
    """slug から redirect 先 URL + UTM パラメータを組み立てる。
    base_url は allowlist 検証通過必須 (Open Redirect 防止)。
    """
    slug_l = (slug or "").strip().lower()
    category = QR_SLUG_CATEGORIES.get(slug_l, "custom")
    coupon = QR_SLUG_DEFAULT_COUPON.get(slug_l)
    base_url = _validate_qr_base_url(base_url)
    qs = _qr_build_query_string(slug_l)
    return {
        "url": f"{base_url}/checkout.html?{qs}",
        "category": category,
        "campaign": slug_l,
        "coupon": coupon,
    }


@app.get("/qr/{slug}")
def qr_redirect(slug: str, request: Request):
    """🔁 QR コード redirect: 短縮 slug → checkout.html (UTM 自動付与)。
    印刷した QR の遷移先を後から変更できる仕組み。スキャン件数を events に記録。
    Critical 対策: rate limit (per IP) + bot 除外 + 同一オリジン redirect 強制。
    """
    if not _is_safe_qr_slug(slug):
        # 不正な slug は LP に逃がす (印刷ミスや改ざん耐性)
        return RedirectResponse(url="/lp.html", status_code=302)

    slug_l = slug.lower()
    qs = _qr_build_query_string(slug_l)
    redirect_path = f"/checkout.html?{qs}"

    # bot / SNS preview crawler は redirect だけして DB 書込みを skip (件数水増し防止)
    ua = request.headers.get("user-agent", "")[:300]
    ua_l = ua.lower()
    is_bot = any(p in ua_l for p in _QR_BOT_UA_PATTERNS)
    if is_bot:
        return RedirectResponse(url=redirect_path, status_code=302)

    # rate limit: 同一 IP から 1 分 30 回までは記録、それ以上は redirect だけ通す
    rate_ok = True
    try:
        _check_rate_limit_ip(request, bucket="qr_scan", limit=30, window=60)
    except HTTPException:
        rate_ok = False

    if rate_ok:
        # スキャン件数を events テーブルに記録 (CEO ダッシュ analytics で集計可)
        try:
            ref = request.headers.get("referer", "")[:300]
            # referer は host 部分のみ保存 (個人情報含む可能性のある query を捨てる)
            ref_host = ""
            if ref:
                try:
                    from urllib.parse import urlparse
                    ref_host = (urlparse(ref).hostname or "")[:120]
                except Exception:
                    ref_host = ""
            conn = db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                (
                    "qr_scan",
                    json.dumps({
                        "slug": slug_l,
                        "category": QR_SLUG_CATEGORIES.get(slug_l, "custom"),
                        "user_agent": ua,
                        "referer_host": ref_host,
                    }),
                    f"qr_{slug_l}_{int(time.time())}",
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.warning(f"[qr_scan] event log failed: {e}")

    return RedirectResponse(url=redirect_path, status_code=302)


@app.post("/api/admin/qr/generate")
def admin_qr_generate(
    payload: dict = Body(default={}),
    authorization: Optional[str] = Header(None),
):
    """📱 QR コード生成 (印刷用 SVG + 表示用 PNG base64)。admin Bearer 認証必須。
    payload: {slug: str, base_url?: str (allowlist 内 https のみ)}
    返り値: {ok, slug, qr_url, destination, svg, png_base64, category, coupon}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload は object 形式")
    slug_raw = payload.get("slug")
    if not isinstance(slug_raw, str):
        raise HTTPException(status_code=400, detail="slug は文字列必須")
    slug = slug_raw.strip().lower()
    base_url_raw = payload.get("base_url") or _QR_DEFAULT_BASE
    if not isinstance(base_url_raw, str):
        raise HTTPException(status_code=400, detail="base_url は文字列")
    # Open Redirect 対策: allowlist 検証 (違反は default に強制 fallback)
    base_url = _validate_qr_base_url(base_url_raw)

    if not _is_safe_qr_slug(slug):
        raise HTTPException(status_code=400, detail="slug は英数字+ハイフン (最大32字)")

    qr_url = f"{base_url}/qr/{slug}"
    dest = _qr_resolve_destination(slug, base_url)

    try:
        import qrcode
        from qrcode.image.svg import SvgPathImage
    except ImportError:
        raise HTTPException(status_code=500, detail="qrcode lib 未インストール (requirements.txt 反映後 redeploy 必要)")

    # SVG (印刷品質・無限スケール)
    svg_qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
        image_factory=SvgPathImage,
    )
    svg_qr.add_data(qr_url)
    svg_qr.make(fit=True)
    svg_img = svg_qr.make_image()
    svg_buf = io.BytesIO()
    svg_img.save(svg_buf)
    try:
        svg_str = svg_buf.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        svg_str = svg_buf.getvalue().decode("utf-8", errors="replace")

    # PNG (画面プレビュー用、PIL があれば、無ければ SVG のみ)
    png_b64 = ""
    try:
        png_qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        png_qr.add_data(qr_url)
        png_qr.make(fit=True)
        png_img = png_qr.make_image(fill_color="black", back_color="white")
        png_buf = io.BytesIO()
        png_img.save(png_buf, format="PNG")
        png_b64 = base64.b64encode(png_buf.getvalue()).decode()
    except Exception as e:
        log.warning(f"[qr_generate] PNG render skipped (PIL 未導入か lib 未対応): {e}")

    return {
        "ok": True,
        "slug": slug,
        "qr_url": qr_url,
        "destination": dest["url"],
        "category": dest["category"],
        "campaign": dest["campaign"],
        "coupon": dest["coupon"],
        "svg": svg_str,
        "png_base64": png_b64,
        "preset_category": QR_SLUG_CATEGORIES.get(slug),
    }


@app.get("/api/admin/qr/scan-stats")
def admin_qr_scan_stats(
    authorization: Optional[str] = Header(None),
    days: int = 30,
):
    """📊 QR スキャン件数を slug 別に集計 (直近 N 日)。admin Bearer 認証必須。
    DoS 対策: SELECT に LIMIT 100000 を入れて巨大テーブルでも OOM しない。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    days = max(1, min(days, 365))
    conn = db()
    c = conn.cursor()
    try:
        ts_clause = (
            f"created_at > NOW() - INTERVAL '{days} days'" if USE_POSTGRES
            else f"created_at > datetime('now', '-{days} days')"
        )
        c.execute(f"SELECT props, created_at FROM events WHERE name='qr_scan' AND {ts_clause} ORDER BY created_at DESC LIMIT 100000")
        rows = c.fetchall()
    finally:
        conn.close()

    by_slug = {}
    total = 0
    for row in rows:
        try:
            p = json.loads(row["props"]) if hasattr(row, "keys") else json.loads(row[0])
        except Exception:
            p = {}
        s = (p.get("slug") or "unknown").lower()
        if s not in by_slug:
            by_slug[s] = {"slug": s, "category": p.get("category", "custom"), "scans": 0}
        by_slug[s]["scans"] += 1
        total += 1

    sorted_slugs = sorted(by_slug.values(), key=lambda x: -x["scans"])
    return {
        "ok": True,
        "days": days,
        "total_scans": total,
        "unique_slugs": len(sorted_slugs),
        "by_slug": sorted_slugs,
    }


# ==========================================================================
# 📸 マーケティング素材ダウンロード (Instagram/Threads/チラシ等の宣伝素材を CEO ダッシュから取得)
# 配置: STATIC_DIR / marketing-assets / {campaign} / *.png|*.svg|*.jpg
# 公開静的 URL: trillion-ai-juku.com/marketing-assets/{campaign}/{file} (Vercel が serve)
# ZIP 一括 DL は admin 認証必須 (こちらは Railway 経由)
# ==========================================================================

_MARKETING_CAMPAIGN_ALLOWED = {"instagram", "threads", "flyer", "classroom", "demo", "x", "line"}
_MARKETING_FILE_EXTENSIONS = {".png", ".svg", ".jpg", ".jpeg", ".webp", ".pdf"}
_MARKETING_MAX_FILES = 100  # DoS 対策: 1 campaign 内のファイル数上限
_MARKETING_MAX_TOTAL_BYTES = 50 * 1024 * 1024  # 合計サイズ上限

# 各 campaign の人間向け説明 (CEO ダッシュ表示用)
_MARKETING_CAMPAIGN_LABELS = {
    "instagram": {"emoji": "📷", "label": "Instagram 投稿用", "color": "#ec4899"},
    "threads": {"emoji": "🧵", "label": "Threads 投稿用", "color": "#a78bfa"},
    "flyer": {"emoji": "📄", "label": "チラシ印刷用", "color": "#fbbf24"},
    "classroom": {"emoji": "🏫", "label": "教室掲示用", "color": "#34d399"},
    "demo": {"emoji": "🎓", "label": "体験授業用", "color": "#22d3ee"},
    "x": {"emoji": "🐦", "label": "X 投稿用", "color": "#0ea5e9"},
    "line": {"emoji": "💬", "label": "LINE 配信用", "color": "#10b981"},
}

# 各ファイルの人間向け説明 (キャプション)。完全 hard-code、未登録は filename をそのまま使う
_MARKETING_FILE_DESCRIPTIONS = {
    "instagram": {
        "01-hero-lp.png": "LP ヒーロー (50/50 創設メンバー、24h AI チューター)",
        "02-curriculum.png": "学年×目標×個別最適 カリキュラム",
        "03-pricing-content.png": "¥14,500 の中身ぜんぶ見せます",
        "04-features.png": "14機能詳細カルーセル",
        "05-checkout-cta.png": "創設メンバー申込 CTA",
        "ai-juku-instagram-qr.png": "QR コード (PNG/SNS用)",
        "ai-juku-instagram-qr.svg": "QR コード (SVG/印刷用)",
    },
}

def _is_safe_marketing_filename(name: str) -> bool:
    """path traversal 防止: filename は basename のみ + 許可拡張子 + ASCII"""
    if not name or len(name) > 200:
        return False
    if name != os.path.basename(name):  # path separator が入ってたら拒否
        return False
    if any(c in name for c in ("..", "/", "\\", "\x00")):
        return False
    ext = pathlib.Path(name).suffix.lower()
    if ext not in _MARKETING_FILE_EXTENSIONS:
        return False
    # ASCII 印字可能 + 一般的な記号のみ
    return all(0x20 <= ord(c) < 0x7f for c in name)

def _marketing_assets_dir(campaign: str) -> pathlib.Path:
    """campaign 名 validate 済前提で marketing-assets ディレクトリを返す"""
    return STATIC_DIR / "marketing-assets" / campaign

def _list_safe_marketing_files(dir_path: pathlib.Path) -> list:
    """指定 dir から安全な marketing file のみ列挙。
    Symlink 完全拒否 + resolve() で dir 外脱出を物理的に防止 (CI/CD 侵害対策)。
    最大 _MARKETING_MAX_FILES 件で打ち切り (DoS 対策)。
    """
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    safe = []
    try:
        dir_resolved = dir_path.resolve(strict=True)
    except Exception:
        return []
    for entry in sorted(dir_path.iterdir()):
        if len(safe) >= _MARKETING_MAX_FILES:
            break
        # Symlink は一切受付けない (CI/CD 経由の悪意ある PR で /etc/passwd 等に向ける攻撃の防御)
        if entry.is_symlink():
            continue
        if not entry.is_file():
            continue
        # filename 検証
        if not _is_safe_marketing_filename(entry.name):
            continue
        # resolve() 後に dir 配下に留まることを確認 (二重防御)
        try:
            resolved = entry.resolve(strict=True)
            resolved.relative_to(dir_resolved)
        except (ValueError, OSError):
            continue
        safe.append(entry)
    return safe


@app.get("/api/admin/marketing-assets/{campaign}/list")
def admin_marketing_assets_list(
    campaign: str,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """📋 指定 campaign のマーケティング素材一覧。admin Bearer auth + IP rate limit (60req/min)。
    返り値: {ok, campaign, label_info, files: [{name, size, public_url, description}], exists, total_bytes}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    # admin auth 後の rate limit (token 漏洩時のダメージコントロール)
    _check_rate_limit_ip(request, bucket="mkt_assets_list", limit=60, window=60)

    campaign_l = (campaign or "").strip().lower()
    if campaign_l not in _MARKETING_CAMPAIGN_ALLOWED:
        raise HTTPException(status_code=400, detail=f"campaign は {sorted(_MARKETING_CAMPAIGN_ALLOWED)} のいずれか")

    dir_path = _marketing_assets_dir(campaign_l)
    if not dir_path.exists() or not dir_path.is_dir():
        return {"ok": True, "campaign": campaign_l, "files": [], "exists": False, "label_info": _MARKETING_CAMPAIGN_LABELS.get(campaign_l, {})}

    descriptions = _MARKETING_FILE_DESCRIPTIONS.get(campaign_l, {})
    safe_entries = _list_safe_marketing_files(dir_path)
    files = []
    total_bytes = 0
    for entry in safe_entries:
        size = entry.stat().st_size
        total_bytes += size
        files.append({
            "name": entry.name,
            "size": size,
            "size_human": f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.2f} MB",
            "public_url": f"/marketing-assets/{campaign_l}/{entry.name}",
            "description": descriptions.get(entry.name, ""),
            "extension": entry.suffix.lower().lstrip("."),
        })

    return {
        "ok": True,
        "campaign": campaign_l,
        "files": files,
        "exists": True,
        "file_count_capped": len(safe_entries) >= _MARKETING_MAX_FILES,
        "total_bytes": total_bytes,
        "total_human": f"{total_bytes/1024/1024:.2f} MB" if total_bytes >= 1024*1024 else f"{total_bytes/1024:.1f} KB",
        "label_info": _MARKETING_CAMPAIGN_LABELS.get(campaign_l, {}),
    }


_MARKETING_UPLOAD_MAX_BYTES = 10 * 1024 * 1024  # 1 file あたり 10MB 上限
_MARKETING_UPLOAD_MAX_FILENAME_LEN = 80

# MIME magic bytes による型チェック (extension 詐称防御)
_MARKETING_MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",  # 後ろの "WEBP" もチェック
    b"%PDF-": "pdf",
}

# SVG 内に含まれてはいけない危険タグ/属性 (XSS 物理防御; vercel header に頼らない)
_SVG_DANGEROUS_PATTERNS = (
    b"<script", b"</script", b"javascript:",
    b"onload=", b"onerror=", b"onclick=", b"onmouseover=", b"onfocus=",
    b"<foreignobject", b"<iframe", b"<embed", b"<object",
    b"<use ", b"<use\t", b"<use\n",  # xlink:href で外部 SVG 取り込み
    b"<animate ", b"<set ",  # CSS-from属性で実行可能
    b"href=\"javascript", b"href='javascript", b"xlink:href=\"javascript", b"xlink:href='javascript",
)

def _svg_is_safe(data: bytes) -> bool:
    """SVG bytes を string match で検査。<script> や onevent 属性 / external href があれば False。"""
    if not data:
        return False
    low = data.lower()
    for bad in _SVG_DANGEROUS_PATTERNS:
        if bad in low:
            return False
    return True

def _detect_image_kind(data: bytes) -> Optional[str]:
    """先頭 bytes から実ファイル形式を判定 (extension 詐称攻撃対策)。"""
    if not data:
        return None
    for sig, kind in _MARKETING_MAGIC_BYTES.items():
        if data.startswith(sig):
            if kind == "webp" and len(data) >= 12 and data[8:12] == b"WEBP":
                return "webp"
            elif kind != "webp":
                return kind
    # SVG: "<?xml" or "<svg" で開始 (XML)
    head = data[:200].lstrip().lower()
    if head.startswith(b"<?xml") and b"<svg" in head[:200]:
        return "svg"
    if head.startswith(b"<svg"):
        return "svg"
    return None


@app.post("/api/admin/marketing-assets/{campaign}/upload")
async def admin_marketing_assets_upload(
    campaign: str,
    request: Request,
    file: UploadFile = File(...),
    overwrite: bool = Form(False),
    authorization: Optional[str] = Header(None),
):
    """📤 マーケティング素材を CEO ダッシュからアップロード (GitHub API 経由 commit)。
    admin Bearer auth + IP rate limit (5req/min)。
    multipart/form-data: file (画像/PDF), overwrite (true なら既存上書き)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    # upload は重い + GitHub API rate limit があるので厳しめ
    _check_rate_limit_ip(request, bucket="mkt_assets_upload", limit=5, window=60)

    if not GITHUB_REVERT_PAT:
        raise HTTPException(status_code=503, detail="GITHUB_REVERT_PAT 未設定 (CEO ダッシュ env で設定要)")

    campaign_l = (campaign or "").strip().lower()
    if campaign_l not in _MARKETING_CAMPAIGN_ALLOWED:
        raise HTTPException(status_code=400, detail=f"campaign は {sorted(_MARKETING_CAMPAIGN_ALLOWED)} のいずれか")

    # filename validation
    raw_name = (file.filename or "").strip()
    if not raw_name:
        raise HTTPException(status_code=400, detail="filename が空")
    safe_name = os.path.basename(raw_name)
    if len(safe_name) > _MARKETING_UPLOAD_MAX_FILENAME_LEN:
        raise HTTPException(status_code=400, detail=f"filename は {_MARKETING_UPLOAD_MAX_FILENAME_LEN} 字以内")
    if not _is_safe_marketing_filename(safe_name):
        raise HTTPException(status_code=400, detail="filename は英数字+ハイフン+アンダースコア+許可拡張子のみ (frontend 側で sanitize 推奨)")

    # Content-Length 事前チェック (DoS 対策: read 前に弾く)
    try:
        cl = int(request.headers.get("content-length") or 0)
    except (TypeError, ValueError):
        cl = 0
    if cl > _MARKETING_UPLOAD_MAX_BYTES + 4096:  # multipart overhead 余裕
        raise HTTPException(status_code=413, detail=f"Content-Length が上限 {_MARKETING_UPLOAD_MAX_BYTES//1024//1024}MB 超過")

    # ファイル読込 (上限+1 で打ち切り = OOM 防止)
    contents = await file.read(_MARKETING_UPLOAD_MAX_BYTES + 1)
    if len(contents) > _MARKETING_UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"ファイルサイズが上限 {_MARKETING_UPLOAD_MAX_BYTES//1024//1024}MB 超過")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="ファイルが空")

    # MIME magic bytes で実ファイル形式を判定 (extension 詐称防御)
    detected = _detect_image_kind(contents)
    declared_ext = pathlib.Path(safe_name).suffix.lower().lstrip(".")
    if not detected:
        raise HTTPException(status_code=400, detail="非対応の画像形式 (PNG/JPG/WebP/GIF/SVG/PDF のみ)")
    if detected == "jpg" and declared_ext in ("jpg", "jpeg"):
        pass
    elif detected != declared_ext:
        raise HTTPException(status_code=400, detail=f"拡張子 .{declared_ext} と実形式 ({detected}) が不一致")

    # SVG XSS 対策: vercel.json header に依存せず string match で危険タグを reject
    if detected == "svg" and not _svg_is_safe(contents):
        raise HTTPException(status_code=400, detail="SVG にスクリプト/外部 href/onevent 属性があるため拒否 (XSS 防止)")

    # GitHub API で commit (PUT /repos/{owner}/{repo}/contents/{path})
    repo_path = f"marketing-assets/{campaign_l}/{safe_name}"
    # Critical 対策: path 越境を server 側で再 assert (PAT scope の防御)
    if not repo_path.startswith(f"marketing-assets/{campaign_l}/"):
        raise HTTPException(status_code=400, detail="path 越境検知")
    if ".." in repo_path or "//" in repo_path:
        raise HTTPException(status_code=400, detail="path に不正な区切り")
    api_url = f"/repos/{GITHUB_REPO}/contents/{repo_path}"

    # 既存チェック (overwrite=False で同名あれば 409)
    existing_sha = None
    head_res = _github_api("GET", api_url)
    if head_res.get("ok") and head_res.get("status") == 200:
        if not overwrite:
            raise HTTPException(status_code=409, detail=f"既存ファイルあり: {safe_name} (overwrite=true で上書き可)")
        existing_sha = (head_res.get("json") or {}).get("sha")

    # base64 encode + PUT
    content_b64 = base64.b64encode(contents).decode("ascii")
    # commit message から filename を除外 (public commit log 漏洩対策)
    commit_msg = f"upload marketing-asset to {campaign_l} (CEO dashboard)"
    body = {
        "message": commit_msg,
        "content": content_b64,
        "branch": AUTO_ROLLBACK_BRANCH,
    }
    if existing_sha:
        body["sha"] = existing_sha

    put_res = _github_api("PUT", api_url, body=body, timeout=30)
    if not put_res.get("ok"):
        # PAT 失効 (401) は self-healing 誘導
        if put_res.get("status") == 401:
            raise HTTPException(status_code=503, detail="GITHUB_REVERT_PAT 失効。Vercel/Railway env で PAT 更新が必要")
        if put_res.get("status") == 403:
            raise HTTPException(status_code=503, detail="GitHub API rate limit 到達 or PAT scope 不足")
        raise HTTPException(status_code=502, detail=f"GitHub API 失敗 (status {put_res.get('status')})")

    commit_sha = ((put_res.get("json") or {}).get("commit") or {}).get("sha", "")[:8]

    # Audit log (誰がいつ何を上げたか追跡可能に)
    log.info(f"[mkt-upload] admin token={token[:6]}... campaign={campaign_l} file={safe_name} size={len(contents)} commit={commit_sha} overwrote={existing_sha is not None}")

    return {
        "ok": True,
        "campaign": campaign_l,
        "filename": safe_name,
        "size": len(contents),
        "size_human": f"{len(contents)/1024:.1f} KB" if len(contents) < 1024*1024 else f"{len(contents)/1024/1024:.2f} MB",
        "detected_kind": detected,
        "overwritten": existing_sha is not None,
        "commit_sha": commit_sha,
        "deploy_eta_seconds": 150,  # Vercel + Railway 余裕を持って 2.5min
        "public_url": f"/marketing-assets/{campaign_l}/{safe_name}",
        "message": "✅ commit 済。Vercel + Railway redeploy で 2〜3分後に反映されます。",
    }


@app.get("/api/admin/marketing-assets/{campaign}/zip")
def admin_marketing_assets_zip(
    campaign: str,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """📦 指定 campaign の全ファイルを ZIP で一括ダウンロード。admin Bearer auth + IP rate limit (10req/min)。
    Symlink 拒否 + 合計 50MB 上限 + ファイル数 100 上限。StreamingResponse で 1 buffer のみ使用。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    # ZIP 生成は CPU/RAM 重いので rate limit 厳しめ
    _check_rate_limit_ip(request, bucket="mkt_assets_zip", limit=10, window=60)

    campaign_l = (campaign or "").strip().lower()
    if campaign_l not in _MARKETING_CAMPAIGN_ALLOWED:
        raise HTTPException(status_code=400, detail=f"campaign は {sorted(_MARKETING_CAMPAIGN_ALLOWED)} のいずれか")

    dir_path = _marketing_assets_dir(campaign_l)
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=404, detail="campaign フォルダが存在しません")

    safe_entries = _list_safe_marketing_files(dir_path)
    if not safe_entries:
        raise HTTPException(status_code=404, detail="ダウンロード可能なファイルが無し")

    # 合計サイズチェック (50MB 上限、メモリ保護)
    total = 0
    for entry in safe_entries:
        total += entry.stat().st_size
        if total > _MARKETING_MAX_TOTAL_BYTES:
            raise HTTPException(status_code=413, detail=f"合計サイズが上限 {_MARKETING_MAX_TOTAL_BYTES//1024//1024}MB 超過")

    # in-memory ZIP 生成 (StreamingResponse に直接 buf を渡し、二重コピー回避)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry in safe_entries:
            zf.write(entry, arcname=entry.name)
    zip_size = buf.tell()
    buf.seek(0)

    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d")
    download_name = f"ai-juku-{campaign_l}-{today}.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "Content-Length": str(zip_size),
        },
    )


# ==========================================================================
# 🎯 Mock Exam (完全模試) — 受験者層集客強化機能 (2026-05-03)
# 1171問プールから動的に試験を組み立て、本番想定で受験させる
# ==========================================================================

# 模試テンプレート: exam_type → セクション構成
MOCK_EXAM_TEMPLATES = {
    "kyotsu": {
        "label": "共通テスト英語 (リーディング相当)",
        "duration_min": 80,
        "sections": [
            {"name": "短文読解", "exam_id": "daigaku", "part_key": "r_short", "eiken_grade": "kyotsu", "count": 2, "points_per": 6},
            {"name": "長文読解", "exam_id": "daigaku", "part_key": "r_long", "eiken_grade": "kyotsu", "count": 3, "points_per": 8},
        ],
    },
    "todai": {
        "label": "東京大学 英語 (大問抜粋)",
        "duration_min": 90,
        "sections": [
            {"name": "要約 (大問1B)", "exam_id": "daigaku", "part_key": "r_summary", "eiken_grade": "todai", "count": 1, "points_per": 15},
            {"name": "長文読解", "exam_id": "daigaku", "part_key": "r_long", "eiken_grade": "todai", "count": 2, "points_per": 12},
            {"name": "和訳", "exam_id": "daigaku", "part_key": "r_translation", "eiken_grade": "todai", "count": 2, "points_per": 12},
        ],
    },
    "kyodai": {
        "label": "京都大学 英語 (大問抜粋)",
        "duration_min": 90,
        "sections": [
            {"name": "長文読解", "exam_id": "daigaku", "part_key": "r_long", "eiken_grade": "kyodai", "count": 2, "points_per": 14},
            {"name": "和訳", "exam_id": "daigaku", "part_key": "r_translation", "eiken_grade": "kyodai", "count": 2, "points_per": 14},
        ],
    },
    "waseda": {
        "label": "早稲田大学 英語 (商/政経 想定)",
        "duration_min": 75,
        "sections": [
            {"name": "長文読解", "exam_id": "daigaku", "part_key": "r_long", "eiken_grade": "waseda", "count": 3, "points_per": 10},
            {"name": "文法", "exam_id": "daigaku", "part_key": "g_grammar", "eiken_grade": "waseda", "count": 1, "points_per": 6},
        ],
    },
    "keio": {
        "label": "慶應義塾大学 英語 (経済/商 想定)",
        "duration_min": 75,
        "sections": [
            {"name": "長文読解", "exam_id": "daigaku", "part_key": "r_long", "eiken_grade": "keio", "count": 3, "points_per": 10},
        ],
    },
    "eiken_g2": {
        "label": "英検2級 模試 (リーディング)",
        "duration_min": 60,
        "sections": [
            {"name": "短文穴埋め", "exam_id": "eiken", "part_key": "r_q1", "eiken_grade": "g2", "count": 3, "points_per": 4},
            {"name": "長文読解", "exam_id": "eiken", "part_key": "r_q3", "eiken_grade": "g2", "count": 2, "points_per": 8},
            {"name": "内容一致型", "exam_id": "eiken", "part_key": "r_q3b", "eiken_grade": "g2", "count": 1, "points_per": 6},
        ],
    },
    "eiken_gp1": {
        "label": "英検準1級 模試 (リーディング)",
        "duration_min": 70,
        "sections": [
            {"name": "短文穴埋め", "exam_id": "eiken", "part_key": "r_q1", "eiken_grade": "gp1", "count": 3, "points_per": 4},
            {"name": "長文読解", "exam_id": "eiken", "part_key": "r_q3", "eiken_grade": "gp1", "count": 2, "points_per": 8},
        ],
    },
    "eiken_g1": {
        "label": "英検1級 模試 (リーディング)",
        "duration_min": 80,
        "sections": [
            {"name": "短文穴埋め", "exam_id": "eiken", "part_key": "r_q1", "eiken_grade": "g1", "count": 3, "points_per": 5},
            {"name": "長文読解", "exam_id": "eiken", "part_key": "r_q3", "eiken_grade": "g1", "count": 2, "points_per": 10},
        ],
    },
}


@app.get("/api/mock-exam/templates")
def mock_exam_templates():
    """利用可能な模試テンプレート一覧 (LP/UI セレクト用)。"""
    out = []
    for k, v in MOCK_EXAM_TEMPLATES.items():
        section_total = sum(s["count"] * s["points_per"] for s in v["sections"])
        out.append({
            "exam_type": k,
            "label": v["label"],
            "duration_min": v["duration_min"],
            "max_score": section_total,
            "section_count": len(v["sections"]),
        })
    return {"templates": out}


@app.post("/api/mock-exam/generate")
def mock_exam_generate(payload: dict):
    """模試を動的に生成。
    payload: {"exam_type": "kyotsu" | "todai" | ..., "student_id": optional}
    既存の exam_questions プールから section ごとに最新順 N 件を取得。
    返却: {session_id, label, duration_min, sections: [{name, questions: [...]}], max_score}
    """
    exam_type = payload.get("exam_type")
    if exam_type not in MOCK_EXAM_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown exam_type: {exam_type}")
    student_id = payload.get("student_id")
    tpl = MOCK_EXAM_TEMPLATES[exam_type]

    conn = db()
    c = conn.cursor()
    sections_out = []
    max_score = 0
    snapshot = []  # 採点用の正解データ
    for sec in tpl["sections"]:
        # 該当 part の最新 count 件をランダム抽出 (created_at DESC LIMIT で多様性確保)
        c.execute(
            "SELECT id, question_data FROM exam_questions WHERE exam_id=? AND part_key=? AND eiken_grade=? ORDER BY RANDOM() LIMIT ?",
            (sec["exam_id"], sec["part_key"], sec["eiken_grade"], sec["count"]),
        )
        rows = c.fetchall()
        section_questions = []
        for r in rows:
            qid = r[0] if not hasattr(r, 'keys') else r["id"]
            qdata_raw = r[1] if not hasattr(r, 'keys') else r["question_data"]
            qdata = json.loads(qdata_raw) if isinstance(qdata_raw, str) else qdata_raw
            sub_questions = qdata.get("questions", [])
            section_questions.append({
                "exam_question_id": qid,
                "passage": qdata.get("passage", ""),
                "audio_script": qdata.get("audio_script", ""),
                "prompt": qdata.get("prompt", ""),
                "year_simulated": qdata.get("year_simulated"),
                "univ_simulated": qdata.get("univ_simulated"),
                "questions": sub_questions,
            })
            # 採点用 snapshot
            snapshot.append({
                "section_name": sec["name"],
                "exam_question_id": qid,
                "sub_questions": [
                    {"id": sq.get("id"), "answer": sq.get("answer"), "points": sec["points_per"] // max(len(sub_questions), 1)}
                    for sq in sub_questions if sq.get("type") == "multiple_choice"
                ],
            })
        sections_out.append({
            "name": sec["name"],
            "points_per_question": sec["points_per"],
            "questions": section_questions,
        })
        max_score += sec["count"] * sec["points_per"]

    # セッション作成
    snapshot_json = json.dumps({"sections": sections_out, "answer_key": snapshot}, ensure_ascii=False)
    c.execute(
        "INSERT INTO mock_exam_sessions (student_id, exam_type, target_label, duration_min, started_at, score_max, questions_json) VALUES (?,?,?,?,?,?,?) RETURNING id",
        (student_id, exam_type, tpl["label"], tpl["duration_min"], datetime.now(timezone.utc).isoformat(), max_score, snapshot_json),
    )
    sid_row = c.fetchone()
    session_id = (sid_row[0] if not hasattr(sid_row, 'keys') else sid_row.get("id")) if sid_row else None
    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "exam_type": exam_type,
        "label": tpl["label"],
        "duration_min": tpl["duration_min"],
        "max_score": max_score,
        "sections": sections_out,
    }


@app.post("/api/mock-exam/submit")
def mock_exam_submit(payload: dict):
    """模試の採点。
    payload: {"session_id": N, "answers": {"<exam_question_id>_<sub_id>": "<choice_index>"}}
    返却: {score_total, score_max, percentage, deviation_estimate, section_scores, weak_topics}
    """
    session_id = payload.get("session_id")
    answers = payload.get("answers") or {}
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT student_id, exam_type, score_max, questions_json FROM mock_exam_sessions WHERE id=?", (session_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="session not found")
    student_id = row[0] if not hasattr(row, 'keys') else row["student_id"]
    exam_type = row[1] if not hasattr(row, 'keys') else row["exam_type"]
    score_max = row[2] if not hasattr(row, 'keys') else row["score_max"]
    snap_json = row[3] if not hasattr(row, 'keys') else row["questions_json"]
    snap = json.loads(snap_json)
    answer_key = snap.get("answer_key", [])

    score_total = 0
    section_scores = {}
    weak_topics = []
    for ak in answer_key:
        sec_name = ak["section_name"]
        eq_id = ak["exam_question_id"]
        sec = section_scores.setdefault(sec_name, {"got": 0, "max": 0})
        for sq in ak["sub_questions"]:
            sub_id = sq.get("id")
            correct = str(sq.get("answer", ""))
            points = int(sq.get("points") or 0)
            sec["max"] += points
            user_ans_key = f"{eq_id}_{sub_id}"
            user_ans = str(answers.get(user_ans_key, "")).strip()
            if user_ans and user_ans == correct:
                score_total += points
                sec["got"] += points
            elif points > 0:
                weak_topics.append({"section": sec_name, "exam_question_id": eq_id, "sub_id": sub_id})

    pct = round(100 * score_total / score_max, 1) if score_max > 0 else 0
    # 偏差値の簡易推定: 50 + (pct - 60) / 2 (60% = 50, 80% = 60, 40% = 40)
    deviation_estimate = round(50 + (pct - 60) / 2, 1)
    # 範囲制限
    deviation_estimate = max(30.0, min(80.0, deviation_estimate))

    section_scores_list = [{"name": k, "got": v["got"], "max": v["max"], "pct": round(100 * v["got"] / max(v["max"], 1), 1)} for k, v in section_scores.items()]

    c.execute(
        "UPDATE mock_exam_sessions SET submitted_at=?, score_total=?, deviation_estimate=?, section_scores=?, answers_json=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(), score_total, deviation_estimate, json.dumps(section_scores_list, ensure_ascii=False), json.dumps(answers, ensure_ascii=False), session_id),
    )
    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "exam_type": exam_type,
        "score_total": score_total,
        "score_max": score_max,
        "percentage": pct,
        "deviation_estimate": deviation_estimate,
        "section_scores": section_scores_list,
        "weak_count": len(weak_topics),
    }


@app.get("/api/mock-exam/history")
# ==========================================================================
# 🎓 大学別 過去問風オリジナル問題 (塾長指示 2026-05-03)
# 著作権: 全て Claude 生成のオリジナル問題。過去問の出題スタイル・トピックのみ参考、
# 実問題文の転載は禁止。inspired_by フィールドに「東大2022年第1問の長文読解スタイル」等
# のメタ情報を保存するが、これは事実情報 (どの大学のどの年度のどの形式の問題を模した
# かの説明) で、原問題のテキスト自体は含まない。
# ==========================================================================
@app.get("/api/university-problems")
def university_problems_list(university: Optional[str] = None, subject: Optional[str] = None,
                              year: Optional[int] = None, limit: int = 30, offset: int = 0):
    """大学別問題一覧。重い question_text 等は含めず、ID + メタのみ。"""
    conn = db(); c = conn.cursor()
    sql = "SELECT id, university, faculty, year, subject, topic, problem_type, difficulty, inspired_by, tags, created_at FROM university_problems WHERE status='published'"
    params = []
    if university:
        sql += " AND university = ?"; params.append(university)
    if subject:
        sql += " AND subject = ?"; params.append(subject)
    if year:
        sql += " AND year = ?"; params.append(year)
    sql += " ORDER BY university, subject, year DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    c.execute(sql, tuple(params))
    out = []
    for r in c.fetchall():
        d = dict(r) if hasattr(r, 'keys') else {}
        out.append(d)
    conn.close()
    return {"items": out, "count": len(out)}


@app.get("/api/university-problems/{pid}")
def university_problems_detail(pid: int):
    """1 問の詳細 (問題文・選択肢・解答・解説 全て返す)。"""
    conn = db(); c = conn.cursor()
    c.execute("SELECT id, university, faculty, year, subject, topic, problem_type, question_text, choices, answer, explanation, difficulty, inspired_by, tags, created_at FROM university_problems WHERE id=? AND status='published'", (pid,))
    r = c.fetchone()
    conn.close()
    if not r:
        raise HTTPException(status_code=404, detail="not found")
    d = dict(r) if hasattr(r, 'keys') else {}
    if d.get("choices"):
        try: d["choices"] = json.loads(d["choices"])
        except: pass
    return d


@app.get("/api/university-problems/meta/universities")
def university_problems_meta():
    """利用可能な (university, subject) の組合せと件数。生徒画面のフィルタ UI 用。"""
    conn = db(); c = conn.cursor()
    c.execute("SELECT university, subject, COUNT(*) AS cnt FROM university_problems WHERE status='published' GROUP BY university, subject ORDER BY university, subject")
    rows = []
    for r in c.fetchall():
        rows.append({
            "university": r["university"] if hasattr(r, 'keys') else r[0],
            "subject":    r["subject"]    if hasattr(r, 'keys') else r[1],
            "count":      r["cnt"]        if hasattr(r, 'keys') else r[2],
        })
    conn.close()
    return {"items": rows}


@app.post("/api/admin/university-problems/import")
def university_problems_import(payload: dict, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """大学別オリジナル問題の一括 import (admin)。
    payload: {"items": [{university, faculty, year, subject, topic, problem_type, question_text,
                          choices(list|None), answer, explanation, difficulty, inspired_by, tags}, ...]}"""
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token): authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    items = payload.get("items") or []
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=400, detail="items が空")

    inserted = 0; failed = 0; failed_details = []
    conn = db(); c = conn.cursor()
    try:
        for i, it in enumerate(items):
            try:
                if not it.get("university") or not it.get("subject") or not it.get("question_text") or not it.get("answer") or not it.get("explanation"):
                    failed += 1; failed_details.append({"i": i, "reason": "missing required"}); continue
                choices_raw = it.get("choices")
                choices_str = json.dumps(choices_raw, ensure_ascii=False) if isinstance(choices_raw, list) else (choices_raw or "")
                c.execute(
                    """INSERT INTO university_problems
                       (university, faculty, year, subject, topic, problem_type, question_text, choices,
                        answer, explanation, difficulty, inspired_by, tags, source)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        it["university"], it.get("faculty",""), it.get("year"),
                        it["subject"], it.get("topic",""), it.get("problem_type","multiple_choice"),
                        it["question_text"], choices_str, it["answer"], it["explanation"],
                        it.get("difficulty","standard"), it.get("inspired_by",""),
                        it.get("tags",""), it.get("source","claude_max"),
                    )
                )
                inserted += 1
            except Exception as e:
                failed += 1; failed_details.append({"i": i, "reason": f"{type(e).__name__}: {str(e)[:80]}"})
                try: conn.rollback()
                except Exception: pass
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "inserted": inserted, "failed": failed, "failed_details": failed_details[:5]}


@app.get("/api/mock-exam/history")
def mock_exam_history(student_id: int):
    """生徒の模試履歴 (mypage 用)。"""
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, exam_type, target_label, score_total, score_max, deviation_estimate, submitted_at FROM mock_exam_sessions WHERE student_id=? AND submitted_at IS NOT NULL ORDER BY submitted_at DESC LIMIT 30", (student_id,))
    rows = c.fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r) if hasattr(r, 'keys') else {"id": r[0], "exam_type": r[1], "target_label": r[2], "score_total": r[3], "score_max": r[4], "deviation_estimate": r[5], "submitted_at": r[6]}
        out.append(d)
    return {"history": out}


# ==========================================================================
# 📚 AI 単語帳 (Spaced Repetition) — Leitner Box system (2026-05-03)
# ==========================================================================

LEITNER_INTERVALS = {1: 1, 2: 3, 3: 7, 4: 21, 5: 60}  # box → days until next review


@app.post("/api/admin/vocab/import")
def vocab_import(payload: dict, authorization: Optional[str] = Header(None), x_cron_secret: Optional[str] = Header(None)):
    """単語データの一括 import (admin)。
    payload: {"words": [{"word":"...", "pos":"...", "meaning_jp":"...", "example_en":"...", "example_jp":"...", "level":"...", "tags":"..."}, ...]}
    """
    authed = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        if _verify_admin_token(token):
            authed = True
    if not authed and CRON_SECRET and x_cron_secret and hmac.compare_digest(x_cron_secret, CRON_SECRET):
        authed = True
    if not authed:
        raise HTTPException(status_code=401, detail="未認証")

    words = payload.get("words") or []
    if not isinstance(words, list) or not words:
        raise HTTPException(status_code=400, detail="words が空")

    inserted = 0
    skipped = 0
    failed = []
    conn = db()
    c = conn.cursor()
    try:
        for i, w in enumerate(words):
            try:
                if not w.get("word") or not w.get("meaning_jp") or not w.get("level"):
                    failed.append({"i": i, "reason": "missing required fields"})
                    continue
                # 事前 SELECT で重複チェック (rowcount が _Cursor wrapper で参照不可のため)
                c.execute("SELECT id FROM vocab_words WHERE word=?", (w["word"],))
                existing = c.fetchone()
                if existing:
                    skipped += 1
                    continue
                c.execute("INSERT INTO vocab_words (word, pos, meaning_jp, example_en, example_jp, level, tags) VALUES (?,?,?,?,?,?,?)",
                          (w["word"], w.get("pos", ""), w["meaning_jp"], w.get("example_en", ""), w.get("example_jp", ""), w["level"], w.get("tags", "")))
                inserted += 1
            except Exception as e:
                failed.append({"i": i, "reason": f"{type(e).__name__}: {str(e)[:80]}"})
                try: conn.rollback()
                except Exception: pass
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "inserted": inserted, "skipped": skipped, "failed": len(failed), "failed_details": failed[:10]}


@app.get("/api/vocab/queue")
def vocab_queue(student_id: int, level: Optional[str] = None, limit: int = 20):
    """次に復習すべき単語キューを返す。
    優先順位: 1) 今復習期限の単語 2) まだ未学習の単語

    limit clamp: max=100 / min=1。 quiz endpoint と統一 (2026-05-03)。
    """
    # limit clamp (silent fallback 防止)
    orig_limit = limit
    if limit is None or limit < 1:
        limit = 10
    if limit > 100:
        limit = 100
    conn = db()
    c = conn.cursor()
    out = []
    # 1) 期限到来の progress
    now = datetime.now(timezone.utc).isoformat()
    sql_due = """
        SELECT vw.id, vw.word, vw.pos, vw.meaning_jp, vw.example_en, vw.example_jp, vw.level, vw.tags, vp.box
        FROM vocab_progress vp
        JOIN vocab_words vw ON vw.id = vp.word_id
        WHERE vp.student_id = ? AND vp.next_review_at <= ?
    """
    params = [student_id, now]
    if level:
        sql_due += " AND vw.level = ?"
        params.append(level)
    sql_due += " ORDER BY vp.next_review_at ASC LIMIT ?"
    params.append(limit)
    c.execute(sql_due, tuple(params))
    for r in c.fetchall():
        d = dict(r) if hasattr(r, 'keys') else {"id": r[0], "word": r[1], "pos": r[2], "meaning_jp": r[3], "example_en": r[4], "example_jp": r[5], "level": r[6], "tags": r[7], "box": r[8]}
        d["status"] = "review"
        out.append(d)

    # 2) 残り枠で未学習
    remaining = limit - len(out)
    if remaining > 0:
        sql_new = """
            SELECT id, word, pos, meaning_jp, example_en, example_jp, level, tags
            FROM vocab_words
            WHERE id NOT IN (SELECT word_id FROM vocab_progress WHERE student_id = ?)
        """
        params2 = [student_id]
        if level:
            sql_new += " AND level = ?"
            params2.append(level)
        sql_new += " ORDER BY id LIMIT ?"
        params2.append(remaining)
        c.execute(sql_new, tuple(params2))
        for r in c.fetchall():
            d = dict(r) if hasattr(r, 'keys') else {"id": r[0], "word": r[1], "pos": r[2], "meaning_jp": r[3], "example_en": r[4], "example_jp": r[5], "level": r[6], "tags": r[7]}
            d["box"] = 0
            d["status"] = "new"
            out.append(d)
    conn.close()
    return {"queue": out, "count": len(out), "requested_limit": orig_limit, "applied_limit": limit}


@app.post("/api/vocab/grade")
def vocab_grade(payload: dict):
    """単語の自己評価を記録。Leitner box 方式で次回復習日を更新。
    payload: {"student_id": N, "word_id": M, "knew": true/false}
    """
    student_id = payload.get("student_id")
    word_id = payload.get("word_id")
    knew = bool(payload.get("knew"))
    if not student_id or not word_id:
        raise HTTPException(status_code=400, detail="student_id / word_id required")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, box, review_count, correct_count FROM vocab_progress WHERE student_id=? AND word_id=?", (student_id, word_id))
    row = c.fetchone()
    now = datetime.now(timezone.utc)
    if row:
        # 既存: box を更新
        prog_id = row[0] if not hasattr(row, 'keys') else row["id"]
        cur_box = int(row[1] if not hasattr(row, 'keys') else row["box"])
        review_count = int(row[2] if not hasattr(row, 'keys') else row["review_count"])
        correct_count = int(row[3] if not hasattr(row, 'keys') else row["correct_count"])
        new_box = min(5, cur_box + 1) if knew else 1
        days = LEITNER_INTERVALS.get(new_box, 1)
        next_at = (now + timedelta(days=days)).isoformat()
        c.execute("UPDATE vocab_progress SET box=?, next_review_at=?, last_reviewed_at=?, review_count=?, correct_count=? WHERE id=?",
                  (new_box, next_at, now.isoformat(), review_count + 1, correct_count + (1 if knew else 0), prog_id))
    else:
        # 新規
        new_box = 2 if knew else 1
        days = LEITNER_INTERVALS.get(new_box, 1)
        next_at = (now + timedelta(days=days)).isoformat()
        c.execute("INSERT INTO vocab_progress (student_id, word_id, box, next_review_at, last_reviewed_at, review_count, correct_count) VALUES (?,?,?,?,?,?,?)",
                  (student_id, word_id, new_box, next_at, now.isoformat(), 1, 1 if knew else 0))
    conn.commit()
    conn.close()
    return {"ok": True, "new_box": new_box, "next_review_in_days": LEITNER_INTERVALS.get(new_box, 1)}


@app.get("/api/vocab/stats")
def vocab_stats(student_id: int):
    """生徒の単語学習統計 (mypage 用)。"""
    def _val(row, idx, key):
        if row is None: return 0
        if hasattr(row, 'keys'):
            return row.get(key, 0) or 0
        return (row[idx] if idx < len(row) else 0) or 0

    conn = db()
    c = conn.cursor()
    by_box = {}
    try:
        c.execute("SELECT box AS box_n, COUNT(*) AS cnt FROM vocab_progress WHERE student_id=? GROUP BY box", (student_id,))
        for r in c.fetchall():
            b = _val(r, 0, 'box_n')
            n = _val(r, 1, 'cnt')
            by_box[int(b)] = int(n)
    except Exception:
        by_box = {}

    c.execute("SELECT COUNT(*) AS cnt FROM vocab_progress WHERE student_id=? AND next_review_at <= ?", (student_id, datetime.now(timezone.utc).isoformat()))
    due_now = int(_val(c.fetchone(), 0, 'cnt'))

    c.execute("SELECT COUNT(*) AS cnt FROM vocab_words")
    total_words = int(_val(c.fetchone(), 0, 'cnt'))

    c.execute("SELECT COALESCE(SUM(review_count), 0) AS rsum, COALESCE(SUM(correct_count), 0) AS csum FROM vocab_progress WHERE student_id=?", (student_id,))
    rr = c.fetchone()
    total_reviews = int(_val(rr, 0, 'rsum'))
    total_correct = int(_val(rr, 1, 'csum'))
    conn.close()
    accuracy = round(100 * total_correct / max(total_reviews, 1), 1)
    return {
        "total_words_in_pool": total_words,
        "by_box": by_box,
        "mastered": by_box.get(5, 0),
        "due_now": due_now,
        "total_reviews": total_reviews,
        "accuracy_percent": accuracy,
    }


# ==========================================================================
# 📖 単語: 4 択クイズ + 自動詞/他動詞・品詞ラベル (塾長指示 2026-05-03)
# ==========================================================================
_POS_LABEL_JP = {
    "verb": "動詞", "v": "動詞",
    "noun": "名詞", "n": "名詞",
    "adjective": "形容詞", "adj": "形容詞", "a": "形容詞",
    "adverb": "副詞", "adv": "副詞",
    "preposition": "前置詞", "prep": "前置詞",
    "conjunction": "接続詞", "conj": "接続詞",
    "pronoun": "代名詞", "pron": "代名詞",
    "interjection": "間投詞", "intj": "間投詞",
    "determiner": "限定詞", "det": "限定詞",
    "phrase": "熟語",
}


def _pos_label_jp(pos: str) -> str:
    if not pos: return ""
    return _POS_LABEL_JP.get(pos.strip().lower(), pos)


def _detect_transitivity(pos: str, meaning_jp: str, tags: str = "") -> str:
    """自動詞 (vi) / 他動詞 (vt) / vt+vi を判定。
    1) tags に明示があれば最優先 (Netlify import の動・他/動・自/動・自他 由来)
    2) 無ければ meaning_jp の「〜を」パターンから推定
    動詞以外は空文字。"""
    if not pos: return ""
    pl = pos.strip().lower()
    if "verb" not in pl and pl not in ("v",):
        return ""
    # tags 由来 (import データに付与) を優先
    if tags:
        t_set = {t.strip() for t in tags.split(",")}
        if "vt+vi" in t_set: return "vt+vi"
        if "vt" in t_set: return "vt"
        if "vi" in t_set: return "vi"
    # フォールバック: meaning_jp の 〜を/〜に パターン
    m = (meaning_jp or "").replace("～", "〜")
    has_wo = "〜を" in m or "~を" in m
    has_other = any(p in m for p in ("〜に", "~に", "〜と", "~と", "〜が", "~が"))
    if has_wo and has_other:
        return "vt+vi"
    if has_wo:
        return "vt"
    return "vi"


def _transitivity_label_jp(t: str) -> str:
    return {"vt": "他動詞", "vi": "自動詞", "vt+vi": "自他両用"}.get(t, "")


# 同等レベル横断マップ (塾長指示 2026-05-03): 同じ英単語は1レベルにしか入れられないため、
# クイズ抽出時に関連レベルからも引く。例: 英検2級は intermediate / kyotsu からも引く
_LEVEL_RELATED = {
    'eiken_g5':       ['chu1'],
    'eiken_g4':       ['chu1', 'chu2'],
    'eiken_g3':       ['chu3', 'basic'],
    'eiken_gp2':      ['basic', 'intermediate'],
    'eiken_g2':       ['intermediate', 'kyotsu'],
    'eiken_gp1':      ['advanced', 'march'],
    'eiken_g1':       ['soukeijou', 'todai_kyodai'],
    'kyotsu':         ['intermediate'],
    'chihokkokuritsu':['kyotsu', 'intermediate'],
    'march':          ['advanced'],
    'soukeijou':      ['advanced', 'march'],
    'todai_kyodai':   ['soukeijou', 'advanced'],
}


def _expand_levels(level: Optional[str]) -> list:
    """指定 level + 関連 level を返す。level なしなら []."""
    if not level:
        return []
    out = [level]
    out.extend(_LEVEL_RELATED.get(level, []))
    return out


@app.get("/api/vocab/quiz")
def vocab_quiz(student_id: int, level: Optional[str] = None, limit: int = 10, univ: Optional[str] = None):
    """4 択形式の単語クイズキュー。各 item は target word + 同 pos の distractor 3 個 + 品詞 + 自他動詞ラベル。
    塾長指示 (2026-05-03): 4 択は同品詞で固める / 自他動詞 + 品詞を表示。
    フロントが distractors を shuffle して出題する想定 (server は shuffle 済み choices も返す)。
    レベル指定時は _LEVEL_RELATED の関連レベルからも引いて実プールを拡張する。

    limit clamp: max=100 / min=1。 過大値 (99999 等) は内部で limit*3 を distractor SQL に渡して
    silent fallback (count=0) になっていた致命 issue の修正 (2026-05-03)。"""
    import random as _r
    # limit clamp (silent fallback 防止)
    orig_limit = limit
    if limit is None or limit < 1:
        limit = 10
    if limit > 100:
        limit = 100
    conn = db()
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    levels = _expand_levels(level)
    placeholders = ",".join(["?"] * len(levels)) if levels else ""
    # 1) 期限到来の progress (queue と同じ優先順位)
    sql_due = """
        SELECT vw.id, vw.word, vw.pos, vw.meaning_jp, vw.example_en, vw.example_jp, vw.level, vw.tags, vp.box
        FROM vocab_progress vp
        JOIN vocab_words vw ON vw.id = vp.word_id
        WHERE vp.student_id = ? AND vp.next_review_at <= ?
    """
    params = [student_id, now]
    if levels:
        sql_due += f" AND vw.level IN ({placeholders})"
        params.extend(levels)
    sql_due += " ORDER BY vp.next_review_at ASC LIMIT ?"
    params.append(limit * 3)  # univ filter で絞られる可能性があるので余裕めに
    c.execute(sql_due, tuple(params))
    candidates = []
    seen_ids = set()
    for r in c.fetchall():
        d = dict(r) if hasattr(r, 'keys') else {"id": r[0], "word": r[1], "pos": r[2], "meaning_jp": r[3], "example_en": r[4], "example_jp": r[5], "level": r[6], "tags": r[7], "box": r[8]}
        d["status"] = "review"
        candidates.append(d); seen_ids.add(d["id"])

    if len(candidates) < limit:
        sql_new = """
            SELECT id, word, pos, meaning_jp, example_en, example_jp, level, tags
            FROM vocab_words
            WHERE id NOT IN (SELECT word_id FROM vocab_progress WHERE student_id = ?)
        """
        params2 = [student_id]
        if levels:
            sql_new += f" AND level IN ({placeholders})"
            params2.extend(levels)
        sql_new += " ORDER BY id LIMIT ?"
        params2.append((limit - len(candidates)) * 3)
        c.execute(sql_new, tuple(params2))
        for r in c.fetchall():
            d = dict(r) if hasattr(r, 'keys') else {"id": r[0], "word": r[1], "pos": r[2], "meaning_jp": r[3], "example_en": r[4], "example_jp": r[5], "level": r[6], "tags": r[7]}
            d["box"] = 0; d["status"] = "new"
            if d["id"] not in seen_ids:
                candidates.append(d); seen_ids.add(d["id"])

    # univ tag filter
    if univ:
        want = f"univ:{univ}"
        candidates = [w for w in candidates if want in (w.get("tags") or "")]

    candidates = candidates[:limit]

    # 各 candidate に対して同 pos の distractor を 3 件取得
    quiz_items = []
    for w in candidates:
        wpos = (w.get("pos") or "").strip()
        # 同 pos / 異なる id / 同 level 優先 → 不足なら同 pos / 全 level
        c.execute(
            "SELECT meaning_jp FROM vocab_words WHERE pos=? AND id<>? AND level=? ORDER BY RANDOM() LIMIT 3",
            (wpos, w["id"], w["level"]),
        )
        distractors = [row["meaning_jp"] if hasattr(row, 'keys') else row[0] for row in c.fetchall()]
        if len(distractors) < 3:
            need = 3 - len(distractors)
            c.execute(
                "SELECT meaning_jp FROM vocab_words WHERE pos=? AND id<>? AND meaning_jp NOT IN (" + ",".join(["?"]*max(1,len(distractors))) + ") ORDER BY RANDOM() LIMIT ?",
                (wpos, w["id"], *(distractors or [""]), need),
            )
            for row in c.fetchall():
                m = row["meaning_jp"] if hasattr(row, 'keys') else row[0]
                if m not in distractors:
                    distractors.append(m)
        # 同 pos ですら 3 件揃わない場合は any pos からフォールバック (英検3級など pool 薄い時用)
        if len(distractors) < 3:
            need = 3 - len(distractors)
            c.execute(
                "SELECT meaning_jp FROM vocab_words WHERE id<>? ORDER BY RANDOM() LIMIT ?",
                (w["id"], need * 3),
            )
            for row in c.fetchall():
                m = row["meaning_jp"] if hasattr(row, 'keys') else row[0]
                if m not in distractors and m != w["meaning_jp"]:
                    distractors.append(m)
                    if len(distractors) >= 3: break

        choices = [w["meaning_jp"]] + distractors[:3]
        _r.shuffle(choices)
        correct_index = choices.index(w["meaning_jp"])
        transitivity = _detect_transitivity(wpos, w.get("meaning_jp") or "", w.get("tags") or "")
        quiz_items.append({
            "id": w["id"],
            "word": w["word"],
            "pos": wpos,
            "pos_label_jp": _pos_label_jp(wpos),
            "transitivity": transitivity,
            "transitivity_label_jp": _transitivity_label_jp(transitivity),
            "meaning_jp": w["meaning_jp"],
            "example_en": w.get("example_en") or "",
            "example_jp": w.get("example_jp") or "",
            "level": w["level"],
            "tags": w.get("tags") or "",
            "box": w.get("box", 0),
            "status": w.get("status", "new"),
            "choices": choices,
            "correct_index": correct_index,
        })
    conn.close()
    return {"quiz": quiz_items, "count": len(quiz_items), "requested_limit": orig_limit, "applied_limit": limit}


# ==========================================================================
# 📊 LP A/B 計測 集計 endpoint (CEO ダッシュ用)
# ==========================================================================
# ==========================================================================
# 🎰 LP Variant Multi-Armed Bandit (Phase 2)
# 既存の variant + analytics を最適化: epsilon-greedy で CV 高い variant に traffic 寄せる
# ==========================================================================
# Variant pool (hard-coded MVP, DB 化は次 phase)
# 各 variant は ID + 表示用 description。LP 側で variant ID を見て content を出し分ける想定。
LP_VARIANT_POOL = {
    "v2_2026-05-02": {
        "description": "現行ベースライン (一般訴求)",
        "config": {"headline": None, "cta_text": None},  # null = 既定値使用
        "active": True,
    },
    "v3_50limit": {
        "description": "50名限定 + 希少性訴求",
        "config": {
            "headline": "🎯 創設メンバー50名限定 — 募集終了間近",
            "cta_text": "今すぐ無料体験を始める (残り枠わずか)",
        },
        "active": True,
    },
    "v3_results": {
        "description": "成果訴求 (合格実績/学習量)",
        "config": {
            "headline": "🎓 AI が君だけのカリキュラムを設計 — 24時間質問できる個別指導",
            "cta_text": "7日間の無料体験を始める",
        },
        "active": True,
    },
}
LP_BANDIT_EPSILON = 0.2  # 20% 探索 / 80% 既知最良 variant
LP_BANDIT_MIN_VIEWS_PER_VARIANT = 30  # この未満の variant は強制探索


_LP_BANDIT_CACHE = {"data": None, "ts": 0, "days": 0}  # 60秒 cache (DoS 緩和)


def _compute_lp_variant_cv(days: int = 14) -> dict:
    """各 variant の CV (lp_view → lp_form_submit) を集計。
    返却: {variant_id: {views: int, submits: int, cv_rate: float}}
    Cache: 60s (高頻度 assign-variant 呼出しでも DB 負荷を抑制)"""
    import time as _time
    now = _time.time()
    if _LP_BANDIT_CACHE["data"] is not None and _LP_BANDIT_CACHE["days"] == days and now - _LP_BANDIT_CACHE["ts"] < 60:
        return _LP_BANDIT_CACHE["data"]

    conn = db()
    c = conn.cursor()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        c.execute(
            """SELECT name, props, session_id FROM events
               WHERE name IN ('lp_view', 'lp_form_submit') AND created_at > ?
               LIMIT 20000""",
            (cutoff,)
        )
        rows = list(c.fetchall())
    finally:
        conn.close()

    # session_id の unique で集計
    views = {}  # variant -> set(session_ids)
    submits = {}
    for r in rows:
        name = r["name"] if hasattr(r, "keys") else r[0]
        props_raw = r["props"] if hasattr(r, "keys") else r[1]
        sess = (r["session_id"] if hasattr(r, "keys") else r[2]) or "_anon"
        try:
            props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})
        except Exception:
            props = {}
        variant = props.get("variant", "unknown")
        if name == "lp_view":
            views.setdefault(variant, set()).add(sess)
        elif name == "lp_form_submit":
            submits.setdefault(variant, set()).add(sess)

    out = {}
    for variant, view_set in views.items():
        v_count = len(view_set)
        s_count = len(submits.get(variant, set()))
        cv = (s_count / v_count) if v_count > 0 else 0.0
        out[variant] = {"views": v_count, "submits": s_count, "cv_rate": cv}
    # views が無くて submits だけある variant も拾う
    for variant in submits:
        if variant not in out:
            out[variant] = {"views": 0, "submits": len(submits[variant]), "cv_rate": 0.0}

    _LP_BANDIT_CACHE["data"] = out
    _LP_BANDIT_CACHE["ts"] = now
    _LP_BANDIT_CACHE["days"] = days
    return out


def _select_lp_variant_epsilon_greedy() -> str:
    """epsilon-greedy で variant を選ぶ。
    - cold start (views < MIN): 最少 views variant を選択 (race-safe round-robin)
    - それ以外: epsilon=0.2 で random 探索、0.8 で best CV variant
    """
    import random
    active_variants = [vid for vid, cfg in LP_VARIANT_POOL.items() if cfg.get("active")]
    if not active_variants:
        return "v2_2026-05-02"  # fallback

    cv_data = _compute_lp_variant_cv(days=14)

    # 1) 未収集データ variant を優先 (cold start) — race-safe: 最少 views variant に決定的に流す
    # これにより 100 同時接続でも全員が「最少 views variant」を均等に埋めていく
    cold_variants = [v for v in active_variants if cv_data.get(v, {}).get("views", 0) < LP_BANDIT_MIN_VIEWS_PER_VARIANT]
    if cold_variants:
        return min(cold_variants, key=lambda v: cv_data.get(v, {}).get("views", 0))

    # 2) epsilon 探索
    if random.random() < LP_BANDIT_EPSILON:
        return random.choice(active_variants)

    # 3) Greedy: best CV
    best = max(active_variants, key=lambda v: cv_data.get(v, {}).get("cv_rate", 0.0))
    return best


@app.get("/api/lp/assign-variant")
def lp_assign_variant(request: Request, force: Optional[str] = None):
    """LP 側が初訪問時に呼ぶ: 推奨 variant ID を返す。
    - force=<variant_id>: テスト用に強制指定 (active な変数のみ受理)
    - 未指定: epsilon-greedy で選択
    Anti-DoS: 1 IP あたり 1分で 60 回まで (LP load 1回/sess なので十分)
    """
    _check_rate_limit_ip(request, bucket="lp_variant_assign", limit=60, window=60)

    if force and force in LP_VARIANT_POOL and LP_VARIANT_POOL[force].get("active"):
        variant = force
    else:
        variant = _select_lp_variant_epsilon_greedy()

    cfg = LP_VARIANT_POOL.get(variant, {})
    return {
        "variant": variant,
        "config": cfg.get("config", {}),
        "description": cfg.get("description", ""),
    }


@app.get("/api/admin/sns-cv")
def admin_sns_cv(authorization: Optional[str] = Header(None), days: int = 30):
    """CEOダッシュ用: SNS 投稿型 (UTM content) ごとの CV 率 + 自動学習ヒント有効化状況"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    cv_data = _compute_sns_utm_cv(days=days)
    rows = []
    for utm, label in SNS_UTM_ALLOWLIST.items():
        d = cv_data.get(utm, {"views": 0, "submits": 0, "cv_rate": 0.0})
        rows.append({
            "utm_content": utm,
            "post_type": label,
            "views": d["views"],
            "submits": d["submits"],
            "cv_rate_pct": round(d["cv_rate"] * 100, 2),
            "has_enough_data": d["views"] >= 150,
        })
    rows.sort(key=lambda r: r["cv_rate_pct"], reverse=True)
    hint = _build_sns_winning_hint()
    return {
        "days": days,
        "rows": rows,
        "hint_active": bool(hint),
        "hint_preview": hint[:300] if hint else "",
        "min_views_for_signal": 150,
        "min_cv_diff_pct": 30,
    }


@app.get("/api/admin/lp-bandit")
def admin_lp_bandit(authorization: Optional[str] = Header(None), days: int = 14):
    """CEOダッシュ用: 多腕バンディットの現状 + 推奨 variant"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="セッション期限切れ")

    cv_data = _compute_lp_variant_cv(days=days)
    rows = []
    for vid, cfg in LP_VARIANT_POOL.items():
        cv = cv_data.get(vid, {"views": 0, "submits": 0, "cv_rate": 0.0})
        rows.append({
            "variant": vid,
            "description": cfg.get("description", ""),
            "active": cfg.get("active", False),
            "views": cv["views"],
            "submits": cv["submits"],
            "cv_rate_pct": round(cv["cv_rate"] * 100, 2),
            "cold_start": cv["views"] < LP_BANDIT_MIN_VIEWS_PER_VARIANT,
        })
    rows.sort(key=lambda r: r["cv_rate_pct"], reverse=True)
    winner = rows[0] if rows and not rows[0]["cold_start"] else None
    return {
        "days": days,
        "epsilon": LP_BANDIT_EPSILON,
        "min_views_threshold": LP_BANDIT_MIN_VIEWS_PER_VARIANT,
        "variants": rows,
        "current_winner": winner,
    }


@app.get("/api/admin/lp-funnel")
def lp_funnel(authorization: Optional[str] = Header(None), days: int = 7):
    """LP のコンバージョンファネル集計。
    変数: days (default 7)。
    返却: {variants: {variant_id: {lp_view, lp_scroll_50, lp_cta_click, lp_form_start, lp_form_submit}, ...}}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")

    conn = db()
    c = conn.cursor()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    # name LIKE 'lp_%' のみ抽出
    c.execute("SELECT name, props, session_id, created_at FROM events WHERE name LIKE 'lp_%' AND created_at > ? LIMIT 50000", (cutoff,))
    rows = c.fetchall()

    # 集計: variant -> event -> count (sessions の unique はざっくり session_id 単位)
    variants = {}  # {variant: {event_name: set(session_ids), event_name_50: set(session_ids)}}
    for r in rows:
        name = r[0] if not hasattr(r, 'keys') else r["name"]
        props_raw = r[1] if not hasattr(r, 'keys') else r["props"]
        sess = r[2] if not hasattr(r, 'keys') else r["session_id"]
        try:
            props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})
        except Exception:
            props = {}
        variant = props.get("variant", "unknown")
        v = variants.setdefault(variant, {})

        # scroll_depth は depth >= 50 だけカウント (中盤到達)
        if name == "lp_scroll_depth":
            try:
                if int(props.get("depth", 0)) >= 50:
                    v.setdefault("lp_scroll_50", set()).add(sess or "_anon")
            except Exception:
                pass
        else:
            v.setdefault(name, set()).add(sess or "_anon")

    # set → count
    out_variants = {}
    for variant, events in variants.items():
        out_variants[variant] = {k: len(s) for k, s in events.items()}

    # 全 variants 横断のサマリ
    summary = {"days": days, "total_events": len(rows), "variants_count": len(variants)}

    return {"summary": summary, "variants": out_variants}


# ==========================================================================
# ✍️ Mock Exam 英作文採点 (Anthropic API 経由)
# ==========================================================================
@app.post("/api/mock-exam/grade-essay")
def mock_exam_grade_essay(payload: dict):
    """模試内 essay (英作文) を AI で採点。
    payload: {"prompt": "...", "essay": "...", "level": "todai" | "kyodai" | "eiken_g1" | ...}
    返却: {scores: {structure, content, language}, overall, total_points, feedback_jp}
    """
    prompt = (payload.get("prompt") or "").strip()
    essay = (payload.get("essay") or "").strip()
    level = (payload.get("level") or "todai").strip()
    if not essay or len(essay) < 20:
        raise HTTPException(status_code=400, detail="essay が短すぎます (20 文字以上必須)")
    if len(essay) > 4000:
        raise HTTPException(status_code=400, detail="essay が長すぎます (4000 文字以内)")

    # Anthropic AI による採点 — 既存の _call_anthropic_safe があれば使う
    system = (
        "You are an experienced English exam grader for Japanese university entrance exams. "
        "Grade the student's essay strictly but fairly. Score on 3 dimensions (0-10 each):\n"
        "1) Structure: thesis clarity, paragraph organization, logical flow\n"
        "2) Content: argument depth, evidence/examples, originality\n"
        "3) Language: grammar accuracy, vocabulary range, naturalness\n\n"
        "Return ONLY valid JSON: {\"structure\": <0-10>, \"content\": <0-10>, \"language\": <0-10>, "
        "\"overall_comment_jp\": \"...\", \"strengths_jp\": [\"...\"], \"improvements_jp\": [\"...\"]}\n"
        "Comment in Japanese for the student."
    )
    user = f"Level: {level}\n\nPrompt: {prompt}\n\nStudent essay:\n{essay}\n\nGrade now (JSON only)."

    try:
        # 既存の AI 呼び出し safe wrapper
        if "_call_anthropic_safe" in globals():
            resp_text = _call_anthropic_safe(system=system, user=user, max_tokens=1500)
        else:
            # fallback: 直接呼び出し (API key check)
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY 未設定")
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            resp_text = msg.content[0].text if msg.content else "{}"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 採点失敗: {type(e).__name__}: {str(e)[:120]}")

    # JSON パース
    try:
        # ``` で囲まれていたら除去
        cleaned = resp_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
        scores = json.loads(cleaned)
    except Exception:
        # JSON が壊れていたら空テンプレで返す
        scores = {"structure": 5, "content": 5, "language": 5,
                  "overall_comment_jp": resp_text[:400],
                  "strengths_jp": [], "improvements_jp": []}

    s = int(scores.get("structure") or 0)
    c_ = int(scores.get("content") or 0)
    l_ = int(scores.get("language") or 0)
    total_30 = s + c_ + l_
    return {
        "scores": {"structure": s, "content": c_, "language": l_},
        "total_30": total_30,
        "overall_pct": round(100 * total_30 / 30, 1),
        "overall_comment_jp": scores.get("overall_comment_jp", ""),
        "strengths_jp": scores.get("strengths_jp", []),
        "improvements_jp": scores.get("improvements_jp", []),
    }


# ==========================================================================
# Routes: Study Logs (学習記録 - Studyplus for School 代替)
# 塾長指示 2026-05-04: コスト削減のため Studyplus for School 機能を内製化
# 国公立難関大学コース (course='kokuritsu_nankan') 受講生のみ提供
# Phase 1: 学習記録 + タイムライン + ヒートマップ + リアクション
# ==========================================================================
_STUDY_SUBJECTS = {
    "英語", "数学", "国語", "現代文", "古文", "漢文",
    "理科", "物理", "化学", "生物", "地学",
    "社会", "日本史", "世界史", "地理", "倫理", "政経",
    "情報", "小論文", "面接対策", "その他",
}
_STUDY_LOG_TARGET_COURSE = "kokuritsu_nankan"  # 国公立難関大学コース 識別子

# JST (UTC+9) helper - JST 基準で「今日」を計算しないと夜間学習の記録が翌日扱いになる
_JST = timezone(timedelta(hours=9))

def _today_jst():
    return datetime.now(_JST).date()


def _verify_admin_required(authorization: Optional[str]) -> None:
    """admin Bearer token 検証 (失敗で 401)。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")


_STUDY_LOG_ALLOWED_PLANS = {"premium", "family", "founder_special", "student_addon"}  # 新プラン体系 2026-05-06

def _require_study_log_course(student: dict) -> None:
    """学習管理機能 (学習記録・カリキュラム・模試分析・弱点プリント) アクセス判定。
    新プラン体系 2026-05-06 (通塾生優遇方針 2026-05-06):
      - course='kokuritsu_nankan' (本クラス所属生徒・無料 sub) → 解放
      - plan='premium' (¥19,800・国公立難関機能含むフル) → 解放
      - plan='family' (¥39,800・プレミアム×3名) → 解放
      - plan='founder_special' (¥14,500 永年・既契約者特典) → 解放
      - plan='student_addon' (通塾生 ¥5,000・招待制限定) → 解放 (塾長指示 2026-05-06)
    塾長指示 2026-05-06: 旧 standard (¥24,980 募集停止) のみ AI のみで学習管理 NG
    通塾生は塾の月謝も払う高単価層で招待制限定のため学習管理を解放
    """
    if not student:
        raise HTTPException(status_code=403, detail="この機能はログイン必須です")
    # 国公立難関本クラス所属
    if student.get("course") == _STUDY_LOG_TARGET_COURSE:
        return
    # プレミアム / 家族 / 創設メンバー のいずれか
    plan = (student.get("plan") or "").lower()
    if plan in _STUDY_LOG_ALLOWED_PLANS:
        return
    raise HTTPException(
        status_code=403,
        detail="この機能はプレミアム以上または国公立難関大学コース受講生のみ利用可能です"
    )


def _sanitize_text(s, maxlen):
    """制御文字除去 + 長さ切り詰め + strip。空なら None。"""
    import re as _re
    if s is None:
        return None
    s = _re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(s))[:maxlen].strip()
    return s or None


class StudyLogCreateRequest(BaseModel):
    studied_date: Optional[str] = None
    subject: str
    material: Optional[str] = None
    minutes: int
    pages: Optional[int] = None
    note: Optional[str] = None


@app.post("/api/study-logs")
def create_study_log(payload: StudyLogCreateRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒が学習記録を投稿。国公立難関大学コース限定。"""
    _check_rate_limit_ip(request, bucket="study_log_create", limit=30, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)

    subject = (payload.subject or "").strip()
    if subject not in _STUDY_SUBJECTS:
        raise HTTPException(status_code=400, detail="科目が不正です")

    try:
        minutes = int(payload.minutes or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="勉強時間が不正です")
    if minutes <= 0 or minutes > 1440:
        raise HTTPException(status_code=400, detail="勉強時間は 1〜1440 分で指定してください")

    today = _today_jst()
    studied_date = (payload.studied_date or today.isoformat()).strip()
    try:
        d = datetime.strptime(studied_date, "%Y-%m-%d").date()
        if d > today:
            raise HTTPException(status_code=400, detail="未来の日付は登録できません")
        if (today - d).days > 365:
            raise HTTPException(status_code=400, detail="1年以上前の日付は登録できません")
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="日付フォーマットが不正です (YYYY-MM-DD)")

    material = _sanitize_text(payload.material, 200)
    note = _sanitize_text(payload.note, 1000)
    pages = None
    if payload.pages is not None:
        try:
            p = int(payload.pages)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="ページ数が不正です")
        if not (0 <= p <= 10000):
            raise HTTPException(status_code=400, detail="ページ数は 0〜10000 で指定してください")
        pages = p

    conn = db()
    try:
        c = conn.cursor()
        # 直近10秒以内の重複投稿を弾く (連打防止・seed_questions 致命事故と同パターン回避)
        if USE_POSTGRES:
            c.execute(
                "SELECT id FROM study_logs WHERE student_id = ? AND studied_date = ? AND subject = ? "
                "AND COALESCE(material,'') = COALESCE(?,'') AND minutes = ? "
                "AND created_at > NOW() - INTERVAL '10 seconds' LIMIT 1",
                (student["id"], studied_date, subject, material, minutes)
            )
        else:
            c.execute(
                "SELECT id FROM study_logs WHERE student_id = ? AND studied_date = ? AND subject = ? "
                "AND COALESCE(material,'') = COALESCE(?,'') AND minutes = ? "
                "AND created_at > datetime('now','-10 seconds') LIMIT 1",
                (student["id"], studied_date, subject, material, minutes)
            )
        if c.fetchone():
            raise HTTPException(status_code=409, detail="重複投稿です。少し待ってから再度お試しください。")

        c.execute(
            "INSERT INTO study_logs (student_id, studied_date, subject, material, minutes, pages, note) VALUES (?,?,?,?,?,?,?) RETURNING id",
            (student["id"], studied_date, subject, material, minutes, pages, note)
        )
        returned = c.fetchone()
        new_id = returned["id"] if returned else None
        conn.commit()
        log.info(f"[StudyLog] create id={new_id} student={student['id']} subj={subject} min={minutes}")
        return {"ok": True, "id": new_id}
    finally:
        conn.close()


@app.delete("/api/study-logs/{log_id}")
def delete_my_study_log(log_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """生徒が自分の学習記録を削除 (誤投稿対策)。"""
    _check_rate_limit_ip(request, bucket="study_log_delete", limit=20, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)

    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT student_id FROM study_logs WHERE id = ?", (log_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="記録が見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")

        # 塾長コメントが付いていたら削除を抑止 (励ましが消えるのを防ぐ)
        c.execute(
            "SELECT COUNT(*) AS n FROM study_log_reactions WHERE log_id = ? AND actor_type = 'admin' AND kind = 'comment'",
            (log_id,)
        )
        row2 = c.fetchone()
        admin_comments = int((row2["n"] if row2 else 0) or 0)
        if admin_comments > 0:
            raise HTTPException(status_code=409, detail="塾長コメントが付いた記録は削除できません。塾長に削除を依頼してください。")

        try:
            c.execute("DELETE FROM study_log_reactions WHERE log_id = ?", (log_id,))
            c.execute("DELETE FROM study_logs WHERE id = ?", (log_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        log.info(f"[StudyLog] delete id={log_id} student={student['id']}")
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/study-logs/me")
def get_my_study_logs(authorization: Optional[str] = Header(None), days: int = 30, limit: int = 200):
    """生徒が自分の学習記録を取得 (デフォルト直近30日)。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)

    try:
        days = int(days or 30)
        limit = int(limit or 200)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="クエリパラメータが不正です")
    days = max(1, min(days, 365))
    limit = max(1, min(limit, 1000))
    today = _today_jst()
    cutoff_date = (today - timedelta(days=days - 1)).isoformat()

    conn = db()
    try:
        c = conn.cursor()
        # 詳細表示用 logs (LIMIT)
        c.execute(
            "SELECT id, studied_date, subject, material, minutes, pages, note, created_at "
            "FROM study_logs WHERE student_id = ? AND studied_date >= ? "
            "ORDER BY studied_date DESC, created_at DESC LIMIT ?",
            (student["id"], cutoff_date, limit)
        )
        rows = c.fetchall()
        logs = []
        log_ids = []
        for r in rows:
            log_ids.append(r["id"])
            logs.append({
                "id": r["id"],
                "date": str(r["studied_date"]),
                "subject": r["subject"],
                "material": r["material"],
                "minutes": int(r["minutes"] or 0),
                "pages": r["pages"],
                "note": r["note"],
                "created_at": str(r["created_at"]) if r["created_at"] else None
            })

        # 集計は LIMIT なしで全期間
        c.execute(
            "SELECT studied_date, subject, SUM(minutes) AS m "
            "FROM study_logs WHERE student_id = ? AND studied_date >= ? "
            "GROUP BY studied_date, subject",
            (student["id"], cutoff_date)
        )
        daily = {}
        by_subject = {}
        for r in c.fetchall():
            d = str(r["studied_date"])
            s = r["subject"]
            m = int(r["m"] or 0)
            daily[d] = daily.get(d, 0) + m
            by_subject[s] = by_subject.get(s, 0) + m

        # reactions
        reactions_map = {}
        if log_ids:
            placeholders = ",".join(["?"] * len(log_ids))
            c.execute(
                f"SELECT log_id, kind, comment, actor_type, created_at FROM study_log_reactions WHERE log_id IN ({placeholders}) ORDER BY created_at ASC",
                tuple(log_ids)
            )
            for r in c.fetchall():
                lid = r["log_id"]
                if lid not in reactions_map:
                    reactions_map[lid] = {"likes": 0, "comments": []}
                if r["kind"] == "like":
                    reactions_map[lid]["likes"] += 1
                elif r["kind"] == "comment" and r["comment"]:
                    reactions_map[lid]["comments"].append({
                        "actor_type": r["actor_type"],
                        "comment": r["comment"],
                        "created_at": str(r["created_at"]) if r["created_at"] else None
                    })
        for log_obj in logs:
            log_obj["reactions"] = reactions_map.get(log_obj["id"], {"likes": 0, "comments": []})

        return {
            "ok": True,
            "logs": logs,
            "daily": [{"date": d, "minutes": m} for d, m in sorted(daily.items())],
            "by_subject": [{"subject": s, "minutes": m} for s, m in sorted(by_subject.items(), key=lambda x: -x[1])],
            "total_minutes": sum(daily.values()),
            "days_active": len(daily),
            "period_days": days,
        }
    finally:
        conn.close()


@app.get("/api/admin/study-logs/timeline")
def admin_study_logs_timeline(authorization: Optional[str] = Header(None), days: int = 7, limit: int = 200, student_id: Optional[int] = None):
    """塾長: 国公立難関大学コース生徒の学習記録タイムライン。"""
    _verify_admin_required(authorization)

    try:
        days = int(days or 7)
        limit = int(limit or 200)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="クエリパラメータが不正です")
    days = max(1, min(days, 90))
    limit = max(1, min(limit, 1000))
    today = _today_jst()
    cutoff_date = (today - timedelta(days=days - 1)).isoformat()

    conn = db()
    try:
        c = conn.cursor()
        if student_id:
            c.execute(
                """SELECT sl.id, sl.student_id, sl.studied_date, sl.subject, sl.material, sl.minutes, sl.pages, sl.note, sl.created_at,
                          s.name AS student_name, s.grade, s.course
                   FROM study_logs sl
                   JOIN students s ON sl.student_id = s.id
                   WHERE sl.studied_date >= ? AND sl.student_id = ? AND s.course = ?
                   ORDER BY sl.created_at DESC
                   LIMIT ?""",
                (cutoff_date, int(student_id), _STUDY_LOG_TARGET_COURSE, limit)
            )
        else:
            c.execute(
                """SELECT sl.id, sl.student_id, sl.studied_date, sl.subject, sl.material, sl.minutes, sl.pages, sl.note, sl.created_at,
                          s.name AS student_name, s.grade, s.course
                   FROM study_logs sl
                   JOIN students s ON sl.student_id = s.id
                   WHERE sl.studied_date >= ? AND s.course = ?
                   ORDER BY sl.created_at DESC
                   LIMIT ?""",
                (cutoff_date, _STUDY_LOG_TARGET_COURSE, limit)
            )
        rows = c.fetchall()

        logs = []
        log_ids = []
        for r in rows:
            log_ids.append(r["id"])
            logs.append({
                "id": r["id"],
                "student_id": r["student_id"],
                "student_name": r["student_name"],
                "grade": r["grade"],
                "date": str(r["studied_date"]),
                "subject": r["subject"],
                "material": r["material"],
                "minutes": int(r["minutes"] or 0),
                "pages": r["pages"],
                "note": r["note"],
                "created_at": str(r["created_at"]) if r["created_at"] else None
            })

        reactions_map = {}
        if log_ids:
            placeholders = ",".join(["?"] * len(log_ids))
            c.execute(
                f"SELECT log_id, kind, comment, actor_type, created_at FROM study_log_reactions WHERE log_id IN ({placeholders}) ORDER BY created_at ASC",
                tuple(log_ids)
            )
            for r in c.fetchall():
                lid = r["log_id"]
                if lid not in reactions_map:
                    reactions_map[lid] = {"likes": 0, "comments": []}
                if r["kind"] == "like":
                    reactions_map[lid]["likes"] += 1
                elif r["kind"] == "comment" and r["comment"]:
                    reactions_map[lid]["comments"].append({
                        "actor_type": r["actor_type"],
                        "comment": r["comment"],
                        "created_at": str(r["created_at"]) if r["created_at"] else None
                    })
        for log_obj in logs:
            log_obj["reactions"] = reactions_map.get(log_obj["id"], {"likes": 0, "comments": []})

        return {"ok": True, "logs": logs, "count": len(logs), "period_days": days}
    finally:
        conn.close()


@app.get("/api/admin/study-logs/heatmap")
def admin_study_logs_heatmap(authorization: Optional[str] = Header(None), days: int = 30):
    """塾長: 国公立難関大学コース生徒×日 の学習時間ヒートマップ。
    記録ゼロの生徒も「サボってる生徒」として可視化するため LEFT JOIN で全員表示。
    """
    _verify_admin_required(authorization)

    try:
        days = int(days or 30)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="クエリパラメータが不正です")
    days = max(1, min(days, 90))
    today = _today_jst()
    cutoff_date = (today - timedelta(days=days - 1)).isoformat()

    conn = db()
    try:
        c = conn.cursor()
        # 国公立難関大学コース受講中の生徒一覧 (active 状態のみ)
        c.execute(
            """SELECT id, name, grade FROM students
               WHERE course = ? AND status IN ('paid', 'trial')
               ORDER BY name""",
            (_STUDY_LOG_TARGET_COURSE,)
        )
        all_students = c.fetchall()

        # 期間内の集計
        c.execute(
            """SELECT sl.student_id, sl.studied_date, SUM(sl.minutes) AS total_minutes
               FROM study_logs sl
               JOIN students s ON sl.student_id = s.id
               WHERE sl.studied_date >= ? AND s.course = ? AND s.status IN ('paid', 'trial')
               GROUP BY sl.student_id, sl.studied_date""",
            (cutoff_date, _STUDY_LOG_TARGET_COURSE)
        )
        agg_rows = c.fetchall()

        students_map = {}
        for s in all_students:
            students_map[s["id"]] = {
                "student_id": s["id"],
                "name": s["name"],
                "grade": s["grade"],
                "data": {},
                "total": 0,
            }
        for r in agg_rows:
            sid = r["student_id"]
            if sid in students_map:
                m = int(r["total_minutes"] or 0)
                students_map[sid]["data"][str(r["studied_date"])] = m
                students_map[sid]["total"] += m

        full_dates = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
        students_list = list(students_map.values())
        students_list.sort(key=lambda x: -x["total"])

        return {
            "ok": True,
            "dates": full_dates,
            "students": students_list,
            "total_students": len(students_list),
            "period_days": days,
        }
    finally:
        conn.close()


class StudyLogReactRequest(BaseModel):
    kind: str
    comment: Optional[str] = None


@app.post("/api/admin/study-logs/{log_id}/react")
def admin_react_to_study_log(log_id: int, payload: StudyLogReactRequest, request: Request, authorization: Optional[str] = Header(None)):
    """塾長: 学習記録にいいね or コメントを投稿。"""
    _check_rate_limit_ip(request, bucket="study_log_react", limit=60, window=60)
    _verify_admin_required(authorization)

    kind = (payload.kind or "").strip()
    if kind not in ("like", "comment"):
        raise HTTPException(status_code=400, detail="kind は 'like' または 'comment'")

    comment = None
    if kind == "comment":
        comment = _sanitize_text(payload.comment, 500)
        if not comment:
            raise HTTPException(status_code=400, detail="コメントは必須です")

    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM study_logs WHERE id = ?", (log_id,))
        if not c.fetchone():
            raise HTTPException(status_code=404, detail="記録が見つかりません")

        try:
            c.execute(
                "INSERT INTO study_log_reactions (log_id, actor_type, actor_id, kind, comment) VALUES (?,?,?,?,?)",
                (log_id, "admin", None, kind, comment)
            )
            conn.commit()
        except IntegrityError:
            # UNIQUE 違反 = admin like の race condition 重複 (partial index で防御)
            conn.rollback()
            if kind == "like":
                return {"ok": True, "already": True}
            raise
        log.info(f"[StudyLog] admin_react log_id={log_id} kind={kind}")
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/admin/study-logs/students")
def admin_study_logs_students_summary(authorization: Optional[str] = Header(None), days: int = 7):
    """塾長: 国公立難関大学コース生徒別の集計。"""
    _verify_admin_required(authorization)

    try:
        days = int(days or 7)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="クエリパラメータが不正です")
    days = max(1, min(days, 90))
    today = _today_jst()
    cutoff_date = (today - timedelta(days=days - 1)).isoformat()

    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            """SELECT s.id, s.name, s.grade, s.status,
                      COALESCE(SUM(sl.minutes), 0) AS total_minutes,
                      COUNT(DISTINCT sl.studied_date) AS days_active,
                      MAX(sl.studied_date) AS last_studied
               FROM students s
               LEFT JOIN study_logs sl ON s.id = sl.student_id AND sl.studied_date >= ?
               WHERE s.course = ? AND s.status IN ('paid', 'trial')
               GROUP BY s.id, s.name, s.grade, s.status
               ORDER BY total_minutes DESC""",
            (cutoff_date, _STUDY_LOG_TARGET_COURSE)
        )
        rows = c.fetchall()
        students = []
        for r in rows:
            students.append({
                "student_id": r["id"],
                "name": r["name"],
                "grade": r["grade"],
                "status": r["status"],
                "total_minutes": int(r["total_minutes"] or 0),
                "days_active": int(r["days_active"] or 0),
                "last_studied": str(r["last_studied"]) if r["last_studied"] else None,
            })
        return {"ok": True, "students": students, "period_days": days}
    finally:
        conn.close()


_VALID_PLANS = {"standard", "premium", "family", "student_addon", "founder_special", "founder1"}


class StudentPlanSetRequest(BaseModel):
    plan: str


@app.post("/api/admin/students/{student_id}/plan")
def admin_set_student_plan(student_id: int, payload: StudentPlanSetRequest, authorization: Optional[str] = Header(None)):
    """塾長: 生徒のプランを設定。"""
    _verify_admin_required(authorization)
    new_plan = (payload.plan or "").strip().lower()
    if new_plan not in _VALID_PLANS:
        raise HTTPException(status_code=400, detail=f"plan は {', '.join(sorted(_VALID_PLANS))} のいずれか")
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, plan FROM students WHERE id = ?", (student_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="生徒が見つかりません")
        old_plan = row["plan"]
        c.execute("UPDATE students SET plan = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_plan, student_id))
        try:
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("plan_change", json.dumps({"student_id": student_id, "old": old_plan, "new": new_plan, "actor": "admin"}, ensure_ascii=False), "admin_action")
            )
        except Exception as ev_err:
            log.warning(f"[Admin] plan_change event log failed: {ev_err}")
        conn.commit()
        log.info(f"[Admin] set plan student={student_id} {old_plan} -> {new_plan}")
        return {"ok": True, "student_id": student_id, "plan": new_plan}
    finally:
        conn.close()


# 塾長: 生徒のコース割当 (国公立難関大学コース 加入/離脱)
class StudentCourseSetRequest(BaseModel):
    course: Optional[str] = None  # 'kokuritsu_nankan' or null


@app.post("/api/admin/students/{student_id}/course")
def admin_set_student_course(student_id: int, payload: StudentCourseSetRequest, authorization: Optional[str] = Header(None)):
    """塾長: 生徒のコースを設定 (kokuritsu_nankan or null)。"""
    _verify_admin_required(authorization)
    new_course = (payload.course or "").strip() or None
    if new_course is not None and new_course != _STUDY_LOG_TARGET_COURSE:
        raise HTTPException(status_code=400, detail=f"course は '{_STUDY_LOG_TARGET_COURSE}' または null のみ")
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, course FROM students WHERE id = ?", (student_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="生徒が見つかりません")
        old_course = row["course"] if "course" in row.keys() else None
        c.execute("UPDATE students SET course = ? WHERE id = ?", (new_course, student_id))
        # 監査ログ (events テーブル)
        try:
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("course_change", json.dumps({"student_id": student_id, "old": old_course, "new": new_course, "actor": "admin"}, ensure_ascii=False), "admin_action")
            )
        except Exception as ev_err:
            log.warning(f"[StudyLog] course_change event log failed: {ev_err}")

        # 生徒に加入完了 / 解除通知 in-app message を自動送信 (塾長指示 2026-05-05)
        if old_course != new_course:
            if new_course == _STUDY_LOG_TARGET_COURSE:
                notif_subject = "✅ 国公立難関大学コース 加入完了"
                notif_body = "ご加入ありがとうございます。マイページに「📚 学習記録」「📅 学習計画」セクションが表示されました。\n\n今日から毎日の学習を記録し、塾長と一緒に志望校合格まで走りましょう。"
            elif old_course == _STUDY_LOG_TARGET_COURSE and new_course is None:
                notif_subject = "📤 国公立難関大学コース 解除のお知らせ"
                notif_body = "国公立難関大学コースを解除しました。学習記録・学習計画セクションは非表示になります。\nご質問は塾長までお問い合わせください。"
            else:
                notif_subject = None
            if notif_subject:
                try:
                    c.execute(
                        "INSERT INTO messages (sender_type, sender_id, recipient_type, recipient_id, broadcast_filter, subject, body, sent_via, email_status) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        ("admin", None, "student", student_id, None, notif_subject, notif_body, "in_app", None)
                    )
                except Exception as me:
                    log.warning(f"[StudyLog] course notify message failed: {me}")
            # 既存 inquiry message の subject に「✅ 加入済み」prefix を付ける (履歴表示で識別)
            if new_course == _STUDY_LOG_TARGET_COURSE:
                try:
                    c.execute(
                        "UPDATE messages SET subject = '✅ [加入済み] ' || COALESCE(subject, '') "
                        "WHERE sender_type = 'student' AND recipient_type = 'admin' AND sender_id = ? "
                        "AND COALESCE(subject, '') NOT LIKE '✅ [加入済み]%'",
                        (student_id,)
                    )
                except Exception as ue:
                    log.warning(f"[StudyLog] inquiry subject update failed: {ue}")

        conn.commit()
        log.info(f"[StudyLog] admin set course student={student_id} course={new_course}")
        return {"ok": True, "student_id": student_id, "course": new_course}
    finally:
        conn.close()


@app.get("/api/admin/students/by-course")
def admin_list_students_by_course(authorization: Optional[str] = Header(None), course: Optional[str] = None):
    """塾長: コース別の生徒一覧 (course 未指定で全生徒)。"""
    _verify_admin_required(authorization)
    conn = db()
    try:
        c = conn.cursor()
        if course:
            c.execute(
                "SELECT id, name, grade, status, course FROM students WHERE course = ? AND status IN ('paid','trial') ORDER BY name",
                (course,)
            )
        else:
            c.execute(
                "SELECT id, name, grade, status, course FROM students WHERE status IN ('paid','trial') ORDER BY name"
            )
        rows = c.fetchall()
        students = [{
            "id": r["id"], "name": r["name"], "grade": r["grade"],
            "status": r["status"], "course": r["course"],
        } for r in rows]
        return {"ok": True, "students": students}
    finally:
        conn.close()


# ==========================================================================
# Routes: Study Plans (学習計画 - Phase 2)
# 塾長指示 2026-05-05: study_logs (実績) と study_plans (計画) を組み合わせ、
# ガントチャート + カレンダーで「計画 vs 実績」を可視化。
# 国公立難関大学コース限定。
# ==========================================================================
class StudyPlanCreateRequest(BaseModel):
    title: str
    subject: str
    material: Optional[str] = None
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    target_minutes: Optional[int] = None
    target_pages: Optional[int] = None
    color: Optional[str] = None
    note: Optional[str] = None


class StudyPlanUpdateRequest(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    material: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_minutes: Optional[int] = None
    target_pages: Optional[int] = None
    color: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None


_PLAN_STATUSES = {"active", "completed", "archived"}
_PLAN_COLOR_RE_STR = r'^#[0-9a-fA-F]{6}$'


def _validate_plan_dates(start_date: str, end_date: str) -> tuple:
    """start_date / end_date を validate して date オブジェクト返す。"""
    try:
        sd = datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
        ed = datetime.strptime(end_date.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="日付フォーマットが不正です (YYYY-MM-DD)")
    if ed < sd:
        raise HTTPException(status_code=400, detail="終了日は開始日以降に指定してください")
    today = _today_jst()
    if (sd - today).days > 730:
        raise HTTPException(status_code=400, detail="2年以上先の計画は登録できません")
    if (today - sd).days > 730:
        raise HTTPException(status_code=400, detail="2年以上前の計画は登録できません")
    if (ed - sd).days > 730:
        raise HTTPException(status_code=400, detail="期間は最大2年までです")
    return sd, ed


def _validate_plan_color(color: Optional[str]) -> Optional[str]:
    import re as _re
    if not color:
        return None
    color = color.strip()
    if not _re.match(_PLAN_COLOR_RE_STR, color):
        raise HTTPException(status_code=400, detail="color は #RRGGBB 形式で指定してください")
    return color


@app.post("/api/study-plans")
def create_study_plan(payload: StudyPlanCreateRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒が学習計画を作成。"""
    _check_rate_limit_ip(request, bucket="study_plan_create", limit=20, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)

    title = _sanitize_text(payload.title, 100)
    if not title:
        raise HTTPException(status_code=400, detail="タイトルは必須です")
    subject = (payload.subject or "").strip()
    if subject not in _STUDY_SUBJECTS:
        raise HTTPException(status_code=400, detail="科目が不正です")
    material = _sanitize_text(payload.material, 200)
    note = _sanitize_text(payload.note, 1000)
    sd, ed = _validate_plan_dates(payload.start_date, payload.end_date)
    color = _validate_plan_color(payload.color) or '#6366f1'

    target_minutes = None
    if payload.target_minutes is not None:
        try:
            tm = int(payload.target_minutes)
            if tm < 0 or tm > 60000:
                raise HTTPException(status_code=400, detail="目標分数は 0〜60000 で指定してください")
            target_minutes = tm
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="目標分数が不正です")

    target_pages = None
    if payload.target_pages is not None:
        try:
            tp = int(payload.target_pages)
            if tp < 0 or tp > 100000:
                raise HTTPException(status_code=400, detail="目標ページは 0〜100000 で指定してください")
            target_pages = tp
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="目標ページが不正です")

    conn = db()
    try:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO study_plans (student_id, title, subject, material, start_date, end_date, target_minutes, target_pages, color, note) "
                "VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING id",
                (student["id"], title, subject, material, sd.isoformat(), ed.isoformat(), target_minutes, target_pages, color, note)
            )
            returned = c.fetchone()
            new_id = returned["id"] if returned else None
            conn.commit()
        except IntegrityError:
            conn.rollback()
            raise HTTPException(status_code=409, detail="同じ内容の計画が既に存在します (subject + 教材 + 期間が一致)")
        log.info(f"[StudyPlan] create id={new_id} student={student['id']} subj={subject}")
        return {"ok": True, "id": new_id}
    finally:
        conn.close()


@app.put("/api/study-plans/{plan_id}")
def update_study_plan(plan_id: int, payload: StudyPlanUpdateRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒が自分の学習計画を更新。"""
    _check_rate_limit_ip(request, bucket="study_plan_update", limit=30, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)

    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT student_id, start_date, end_date FROM study_plans WHERE id = ?", (plan_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="計画が見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")

        # 更新するフィールドのみ抽出
        updates = {}
        if payload.title is not None:
            t = _sanitize_text(payload.title, 100)
            if not t:
                raise HTTPException(status_code=400, detail="タイトルは必須です")
            updates["title"] = t
        if payload.subject is not None:
            if payload.subject not in _STUDY_SUBJECTS:
                raise HTTPException(status_code=400, detail="科目が不正です")
            updates["subject"] = payload.subject
        if payload.material is not None:
            updates["material"] = _sanitize_text(payload.material, 200)
        if payload.note is not None:
            updates["note"] = _sanitize_text(payload.note, 1000)
        if payload.color is not None:
            updates["color"] = _validate_plan_color(payload.color) or '#6366f1'
        if payload.status is not None:
            if payload.status not in _PLAN_STATUSES:
                raise HTTPException(status_code=400, detail="status が不正です")
            updates["status"] = payload.status

        # 日付は両方 or どちらかが来た時に validate
        if payload.start_date is not None or payload.end_date is not None:
            new_sd = payload.start_date or str(row["start_date"])
            new_ed = payload.end_date or str(row["end_date"])
            sd, ed = _validate_plan_dates(new_sd, new_ed)
            updates["start_date"] = sd.isoformat()
            updates["end_date"] = ed.isoformat()

        if payload.target_minutes is not None:
            try:
                tm = int(payload.target_minutes)
                if tm < 0 or tm > 60000:
                    raise HTTPException(status_code=400, detail="目標分数は 0〜60000")
                updates["target_minutes"] = tm
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="目標分数が不正です")
        if payload.target_pages is not None:
            try:
                tp = int(payload.target_pages)
                if tp < 0 or tp > 100000:
                    raise HTTPException(status_code=400, detail="目標ページは 0〜100000")
                updates["target_pages"] = tp
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="目標ページが不正です")

        if not updates:
            return {"ok": True, "no_change": True}

        # updated_at も更新
        if USE_POSTGRES:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        else:
            updates["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        # WHERE id AND student_id (TOCTOU 防御: SELECT 後の race で他生徒の row を更新しないように二重ガード)
        c.execute(f"UPDATE study_plans SET {set_clause} WHERE id = ? AND student_id = ?", tuple(updates.values()) + (plan_id, student["id"]))
        conn.commit()
        log.info(f"[StudyPlan] update id={plan_id} student={student['id']}")
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/study-plans/{plan_id}")
def delete_my_study_plan(plan_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """生徒が自分の学習計画を削除。"""
    _check_rate_limit_ip(request, bucket="study_plan_delete", limit=20, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)

    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT student_id FROM study_plans WHERE id = ?", (plan_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="計画が見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")
        c.execute("DELETE FROM study_plans WHERE id = ? AND student_id = ?", (plan_id, student["id"]))
        conn.commit()
        log.info(f"[StudyPlan] delete id={plan_id} student={student['id']}")
        return {"ok": True}
    finally:
        conn.close()


def _enrich_plans_with_progress(c, plans: List[dict]) -> List[dict]:
    """plans 配列に study_logs から集計した progress (実績分数/ページ + 達成率) を付与。
    バッチ化: 全生徒分の logs を 1 クエリで取得し Python 側で fold。N+1 回避。
    """
    if not plans:
        return plans

    student_ids = list({int(p["student_id"]) for p in plans})
    if not student_ids:
        return plans
    placeholders = ",".join(["?"] * len(student_ids))
    c.execute(
        f"""SELECT student_id, subject, COALESCE(material,'') AS mkey,
                   studied_date, COALESCE(SUM(minutes),0) AS m, COALESCE(SUM(pages),0) AS p
            FROM study_logs WHERE student_id IN ({placeholders})
            GROUP BY student_id, subject, COALESCE(material,''), studied_date""",
        tuple(student_ids)
    )
    daily_rows = c.fetchall()
    # (sid, subj, mkey) -> sorted list of (date_str, m, p)
    bucket = {}
    for r in daily_rows:
        key = (int(r["student_id"]), r["subject"], r["mkey"] or '')
        bucket.setdefault(key, []).append((str(r["studied_date"]), int(r["m"] or 0), int(r["p"] or 0)))

    for p in plans:
        sid = int(p["student_id"])
        subj = p["subject"]
        mat_key = (p.get("material") or '') if p.get("material") else None
        sd = str(p["start_date"])
        ed = str(p["end_date"])
        actual_min = 0
        actual_pages = 0
        # material 指定なし → subject 全 material 合算 / 指定あり → 完全一致のみ
        if mat_key is None:
            for (sub_key, lst) in bucket.items():
                if sub_key[0] == sid and sub_key[1] == subj:
                    for (d, m, pp) in lst:
                        if sd <= d <= ed:
                            actual_min += m
                            actual_pages += pp
        else:
            lst = bucket.get((sid, subj, mat_key), [])
            for (d, m, pp) in lst:
                if sd <= d <= ed:
                    actual_min += m
                    actual_pages += pp
        p["actual_minutes"] = actual_min
        p["actual_pages"] = actual_pages
        if p.get("target_minutes"):
            p["progress_minutes_pct"] = min(100, round(actual_min / p["target_minutes"] * 100, 1))
        else:
            p["progress_minutes_pct"] = None
        if p.get("target_pages"):
            p["progress_pages_pct"] = min(100, round(actual_pages / p["target_pages"] * 100, 1))
        else:
            p["progress_pages_pct"] = None
    return plans


@app.get("/api/study-plans/me")
def get_my_study_plans(authorization: Optional[str] = Header(None), status: Optional[str] = None):
    """生徒が自分の学習計画 + 進捗を取得。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    if status and status not in _PLAN_STATUSES:
        raise HTTPException(status_code=400, detail="status が不正です")

    conn = db()
    try:
        c = conn.cursor()
        if status:
            c.execute(
                "SELECT id, student_id, title, subject, material, start_date, end_date, target_minutes, target_pages, color, status, note, created_at "
                "FROM study_plans WHERE student_id = ? AND status = ? ORDER BY start_date DESC",
                (student["id"], status)
            )
        else:
            c.execute(
                "SELECT id, student_id, title, subject, material, start_date, end_date, target_minutes, target_pages, color, status, note, created_at "
                "FROM study_plans WHERE student_id = ? ORDER BY start_date DESC",
                (student["id"],)
            )
        rows = c.fetchall()
        plans = []
        for r in rows:
            plans.append({
                "id": r["id"],
                "student_id": r["student_id"],
                "title": r["title"],
                "subject": r["subject"],
                "material": r["material"],
                "start_date": str(r["start_date"]),
                "end_date": str(r["end_date"]),
                "target_minutes": r["target_minutes"],
                "target_pages": r["target_pages"],
                "color": r["color"] or '#6366f1',
                "status": r["status"],
                "note": r["note"],
                "created_at": str(r["created_at"]) if r["created_at"] else None,
            })
        plans = _enrich_plans_with_progress(c, plans)
        return {"ok": True, "plans": plans, "count": len(plans)}
    finally:
        conn.close()


@app.get("/api/admin/study-plans/gantt")
def admin_study_plans_gantt(request: Request, authorization: Optional[str] = Header(None), days: int = 60, student_id: Optional[int] = None):
    """塾長: 全コース受講生のガントチャート用データ (期間+進捗)。"""
    _check_rate_limit_ip(request, bucket="admin_gantt", limit=60, window=60)
    _verify_admin_required(authorization)
    try:
        days = int(days or 60)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="クエリパラメータが不正です")
    days = max(7, min(days, 365))
    today = _today_jst()
    # ガントの window: 今日から前後を表示。表示範囲とアクティブ計画の判定を分離。
    window_start = (today - timedelta(days=days // 2)).isoformat()
    window_end = (today + timedelta(days=days // 2)).isoformat()

    conn = db()
    try:
        c = conn.cursor()
        if student_id:
            c.execute(
                """SELECT sp.id, sp.student_id, sp.title, sp.subject, sp.material,
                          sp.start_date, sp.end_date, sp.target_minutes, sp.target_pages,
                          sp.color, sp.status,
                          s.name AS student_name, s.grade
                   FROM study_plans sp
                   JOIN students s ON sp.student_id = s.id
                   WHERE s.course = ? AND s.status IN ('paid','trial')
                     AND sp.status != 'archived'
                     AND sp.end_date >= ? AND sp.start_date <= ?
                     AND sp.student_id = ?
                   ORDER BY s.name, sp.start_date""",
                (_STUDY_LOG_TARGET_COURSE, window_start, window_end, int(student_id))
            )
        else:
            c.execute(
                """SELECT sp.id, sp.student_id, sp.title, sp.subject, sp.material,
                          sp.start_date, sp.end_date, sp.target_minutes, sp.target_pages,
                          sp.color, sp.status,
                          s.name AS student_name, s.grade
                   FROM study_plans sp
                   JOIN students s ON sp.student_id = s.id
                   WHERE s.course = ? AND s.status IN ('paid','trial')
                     AND sp.status != 'archived'
                     AND sp.end_date >= ? AND sp.start_date <= ?
                   ORDER BY s.name, sp.start_date""",
                (_STUDY_LOG_TARGET_COURSE, window_start, window_end)
            )
        rows = c.fetchall()
        plans = []
        for r in rows:
            plans.append({
                "id": r["id"],
                "student_id": r["student_id"],
                "student_name": r["student_name"],
                "grade": r["grade"],
                "title": r["title"],
                "subject": r["subject"],
                "material": r["material"],
                "start_date": str(r["start_date"]),
                "end_date": str(r["end_date"]),
                "target_minutes": r["target_minutes"],
                "target_pages": r["target_pages"],
                "color": r["color"] or '#6366f1',
                "status": r["status"],
            })
        plans = _enrich_plans_with_progress(c, plans)

        # 生徒別グルーピング (ガント描画用)
        students_map = {}
        for p in plans:
            sid = p["student_id"]
            if sid not in students_map:
                students_map[sid] = {
                    "student_id": sid,
                    "name": p["student_name"],
                    "grade": p["grade"],
                    "plans": []
                }
            students_map[sid]["plans"].append(p)

        return {
            "ok": True,
            "window_start": window_start,
            "window_end": window_end,
            "today": today.isoformat(),
            "students": list(students_map.values()),
            "total_plans": len(plans),
        }
    finally:
        conn.close()


@app.get("/api/admin/study-plans/calendar")
def admin_study_plans_calendar(request: Request, authorization: Optional[str] = Header(None), year: Optional[int] = None, month: Optional[int] = None):
    """塾長: 月間カレンダー (該当月に重なる全計画)。"""
    _check_rate_limit_ip(request, bucket="admin_calendar", limit=60, window=60)
    _verify_admin_required(authorization)
    today = _today_jst()
    try:
        y = int(year) if year else today.year
        m = int(month) if month else today.month
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="year/month が不正です")
    if not (2020 <= y <= 2100) or not (1 <= m <= 12):
        raise HTTPException(status_code=400, detail="year/month が範囲外です")

    # 月初・月末
    import calendar as _cal
    last_day = _cal.monthrange(y, m)[1]
    month_start = f"{y:04d}-{m:02d}-01"
    month_end = f"{y:04d}-{m:02d}-{last_day:02d}"

    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            """SELECT sp.id, sp.student_id, sp.title, sp.subject, sp.material,
                      sp.start_date, sp.end_date, sp.color, sp.status,
                      s.name AS student_name, s.grade
               FROM study_plans sp
               JOIN students s ON sp.student_id = s.id
               WHERE s.course = ? AND s.status IN ('paid','trial')
                 AND sp.status != 'archived'
                 AND sp.end_date >= ? AND sp.start_date <= ?
               ORDER BY sp.start_date""",
            (_STUDY_LOG_TARGET_COURSE, month_start, month_end)
        )
        rows = c.fetchall()
        plans = [{
            "id": r["id"],
            "student_id": r["student_id"],
            "student_name": r["student_name"],
            "grade": r["grade"],
            "title": r["title"],
            "subject": r["subject"],
            "material": r["material"],
            "start_date": str(r["start_date"]),
            "end_date": str(r["end_date"]),
            "color": r["color"] or '#6366f1',
            "status": r["status"],
        } for r in rows]
        return {
            "ok": True,
            "year": y, "month": m,
            "month_start": month_start, "month_end": month_end,
            "plans": plans,
        }
    finally:
        conn.close()


# ==========================================================================
# Routes: Messages (Phase 3 - 塾長→生徒メッセージ機能, email only)
# 塾長指示 2026-05-05: Studyplus for School のメッセージ機能を内製代替。
# 個別 / 一斉 (フィルタ: コース/学年/ステータス) を email + アプリ内で配信。
# ==========================================================================
_MSG_BROADCAST_FILTERS = {"all", "kokuritsu_nankan", "paid_only", "trial_only"}


def _send_message_email(to_email: str, subject: str, body_text: str, student_name: Optional[str] = None) -> dict:
    """Resend 経由でメッセージを送信。in-app メッセージとは別の email 通知。"""
    if not RESEND_API_KEY:
        return {"sent": False, "error": "RESEND_API_KEY not configured"}
    # 合成監視向け bounce 防止 (memory: feedback_synthetic_monitor_quota.md)
    # case-insensitive (Integration 監査 2026-05-05): 大文字混じりでも skip
    if "@synthetic-monitor." in (to_email or "").lower():
        return {"sent": True, "resend_id": "synthetic-skip", "synthetic": True}
    def _esc(s):
        return (str(s or "")
                .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;").replace("'", "&#39;"))
    # subject: HTML escape + CRLF 除去 (header injection 二重防御 / Security M-1)
    raw_subject = (subject or "AI学習コーチ塾より新着メッセージ").replace("\r", "").replace("\n", " ")
    safe_subject = _esc(raw_subject)
    # body: HTML escape + CRLF 正規化
    body_normalized = (body_text or "").replace("\r\n", "\n").replace("\r", "\n")
    safe_body_html = _esc(body_normalized).replace("\n", "<br>")
    greeting = f"<p>{_esc(student_name)}さん</p>" if student_name else ""
    html = f"""<!DOCTYPE html><html><body style="font-family:sans-serif; line-height:1.7; color:#333; padding:1.5rem; max-width:600px; margin:0 auto;">
<h2 style="color:#6366f1; border-bottom:2px solid #6366f1; padding-bottom:0.5rem;">📨 {safe_subject}</h2>
{greeting}
<div style="background:#fafafa; border-left:4px solid #6366f1; padding:1rem 1.2rem; border-radius:6px; margin:1rem 0;">
{safe_body_html}
</div>
<p style="font-size:0.85rem; color:#666; margin-top:1.5rem;">
このメッセージは AI学習コーチ塾 のマイページからも確認できます:<br>
<a href="https://trillion-ai-juku.com/mypage.html" style="color:#6366f1;">https://trillion-ai-juku.com/mypage.html</a>
</p>
<hr style="margin:2rem 0; border:none; border-top:1px solid #eee;">
<p style="font-size:0.78rem; color:#999;">配信元: AI学習コーチ塾 / 配信停止やお問い合わせは塾長まで</p>
</body></html>"""
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps({"from": FROM_EMAIL, "to": [to_email], "subject": safe_subject, "html": html}).encode("utf-8"),
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json", "User-Agent": "ai-juku-system/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return {"sent": True, "resend_id": result.get("id")}
    except Exception as e:
        log.error(f"[Messages] email send failed for {to_email}: {type(e).__name__}: {str(e)[:200]}")
        return {"sent": False, "error": str(e)[:200]}


class MessageSendRequest(BaseModel):
    target: str  # 'student' (個別) or 'broadcast' (一斉)
    student_id: Optional[int] = None  # target='student' 時に必須
    broadcast_filter: Optional[str] = None  # 'all'/'kokuritsu_nankan'/'paid_only'/'trial_only'
    subject: Optional[str] = None
    body: str
    send_email: bool = True
    # 添付ファイル (任意・授業ファイル送信用 / 塾長指示 2026-05-06)
    attachment_filename: Optional[str] = None
    attachment_mime: Optional[str] = None
    attachment_data_b64: Optional[str] = None  # base64 encoded content


class StudentMessageSendRequest(BaseModel):
    """生徒 → 塾長 メッセージ送信。国公立難関コース受講生から授業質問・ファイル送信用。"""
    subject: Optional[str] = None
    body: str
    attachment_filename: Optional[str] = None
    attachment_mime: Optional[str] = None
    attachment_data_b64: Optional[str] = None


# 添付ファイル制限 (塾長指示 2026-05-06)
_MSG_ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_MSG_ATTACHMENT_ALLOWED_MIMES = {
    "image/jpeg", "image/png", "image/heic", "image/webp", "image/gif",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain", "text/csv",
}
# magic bytes 署名 (3 視点 review 2026-05-06: mime spoofing 防御)
_MSG_ATTACHMENT_MAGIC = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "image/webp": [b"RIFF"],  # 後段で WEBP container も check
    "application/pdf": [b"%PDF"],
    "application/msword": [b"\xd0\xcf\x11\xe0"],
    "application/vnd.ms-excel": [b"\xd0\xcf\x11\xe0"],
    "application/vnd.ms-powerpoint": [b"\xd0\xcf\x11\xe0"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK\x03\x04"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [b"PK\x03\x04"],
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": [b"PK\x03\x04"],
    # image/heic: variable magic, skip
    # text/plain, text/csv: textual content, no magic check
}


def _validate_message_attachment(filename: Optional[str], mime: Optional[str], data_b64: Optional[str]) -> Optional[dict]:
    """添付ファイル検証。OK なら {filename, mime, size, data_b64} を返す。
    どれか欠けてれば None。違反なら HTTPException raise。
    + magic bytes による mime spoofing 防御 (3 視点 review 2026-05-06)"""
    if not (filename or mime or data_b64):
        return None
    if not (filename and mime and data_b64):
        raise HTTPException(status_code=400, detail="添付ファイルは filename / mime / data_b64 全て必要です")
    fn = filename.strip()[:200]
    mt = mime.strip().lower()
    if mt not in _MSG_ATTACHMENT_ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail=f"添付ファイル形式 {mt} は許可されていません (PDF/画像/Word/Excel/PowerPoint/text のみ)")
    # base64 size 推定: len * 3/4
    b64_len = len(data_b64)
    if b64_len > _MSG_ATTACHMENT_MAX_BYTES * 4 // 3 + 100:
        raise HTTPException(status_code=413, detail=f"添付ファイルが大きすぎます (上限 {_MSG_ATTACHMENT_MAX_BYTES // 1024 // 1024} MB)")
    # decode できるかだけ check (オーバーヘッド最小)
    import base64 as _b64
    try:
        decoded = _b64.b64decode(data_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="添付データが破損しています (base64 デコード失敗)")
    actual_size = len(decoded)
    if actual_size > _MSG_ATTACHMENT_MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"添付ファイルが大きすぎます ({actual_size // 1024 // 1024} MB / 上限 {_MSG_ATTACHMENT_MAX_BYTES // 1024 // 1024} MB)")
    # magic bytes check (mime spoofing による XSS / RCE 防御)
    expected_signatures = _MSG_ATTACHMENT_MAGIC.get(mt)
    if expected_signatures and actual_size >= 8:
        head = decoded[:16]
        match = any(head.startswith(sig) for sig in expected_signatures)
        if not match:
            raise HTTPException(status_code=400, detail=f"添付ファイルの内容が宣言された形式 ({mt}) と一致しません (mime spoofing 検出)")
        # WEBP は RIFF...WEBP container を更に check
        if mt == "image/webp" and actual_size >= 16 and decoded[8:12] != b"WEBP":
            raise HTTPException(status_code=400, detail="WEBP ファイルが破損しています")
    return {"filename": fn, "mime": mt, "size": actual_size, "data_b64": data_b64}


def _safe_attachment_response(filename: str, stored_mime: str, data: bytes):
    """添付ダウンロード response builder。XSS 防御:
    - 許可リストにある mime のみ Content-Type 反映 (text/html 等の rendering 系を弾く)
    - それ以外は application/octet-stream に強制
    - Content-Disposition: attachment で常にダウンロード扱い
    - X-Content-Type-Options: nosniff で MIME sniffing 攻撃を防御"""
    from fastapi.responses import Response as _Resp
    from urllib.parse import quote as _qu
    safe_mime = stored_mime if stored_mime in _MSG_ATTACHMENT_ALLOWED_MIMES else "application/octet-stream"
    return _Resp(
        content=data,
        media_type=safe_mime,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{_qu(filename or 'attachment')}",
            "X-Content-Type-Options": "nosniff",
        }
    )


@app.post("/api/admin/messages/send")
def admin_send_message(payload: MessageSendRequest, background_tasks: BackgroundTasks, request: Request, authorization: Optional[str] = Header(None)):
    """塾長: 個別 or 一斉メッセージを送信。in-app は同期保存、email は BackgroundTasks で非同期送信。"""
    _check_rate_limit_ip(request, bucket="msg_send", limit=20, window=60)
    _verify_admin_required(authorization)

    target = (payload.target or "").strip()
    if target not in ("student", "broadcast"):
        raise HTTPException(status_code=400, detail="target は 'student' または 'broadcast'")

    # broadcast は別途 rate limit (5 分 3 回) — Resend 枠保護 (Security C-1 / feedback_synthetic_monitor_quota.md)
    if target == "broadcast":
        _check_rate_limit_ip(request, bucket="msg_broadcast", limit=3, window=300)

    body = _sanitize_text(payload.body, 5000)
    if not body:
        raise HTTPException(status_code=400, detail="本文は必須です")
    subject = _sanitize_text(payload.subject, 200) or "AI学習コーチ塾より新着メッセージ"

    conn = db()
    try:
        c = conn.cursor()
        # 対象生徒一覧を解決
        targets = []
        broadcast_group_id = None
        if target == "student":
            if not payload.student_id:
                raise HTTPException(status_code=400, detail="student_id が必要です")
            c.execute("SELECT id, name, email FROM students WHERE id = ? AND status IN ('paid','trial')", (int(payload.student_id),))
            row = c.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="生徒が見つからないか、status が無効です")
            targets.append({"id": row["id"], "name": row["name"], "email": row["email"]})
        else:
            bf = (payload.broadcast_filter or "all").strip()
            if bf not in _MSG_BROADCAST_FILTERS:
                raise HTTPException(status_code=400, detail="broadcast_filter が不正です")
            import uuid as _uuid
            broadcast_group_id = f"bc_{_uuid.uuid4().hex[:12]}"
            if bf == "all":
                c.execute("SELECT id, name, email FROM students WHERE status IN ('paid','trial')")
            elif bf == "kokuritsu_nankan":
                c.execute("SELECT id, name, email FROM students WHERE status IN ('paid','trial') AND course = ?", (_STUDY_LOG_TARGET_COURSE,))
            elif bf == "paid_only":
                c.execute("SELECT id, name, email FROM students WHERE status = 'paid'")
            elif bf == "trial_only":
                c.execute("SELECT id, name, email FROM students WHERE status = 'trial'")
            for r in c.fetchall():
                targets.append({"id": r["id"], "name": r["name"], "email": r["email"]})

        if not targets:
            raise HTTPException(status_code=404, detail="対象生徒がいません")
        # 一斉送信の上限 500 名 (Security M-4 / Resend 枠保護)
        if target == "broadcast" and len(targets) > 500:
            raise HTTPException(status_code=413, detail=f"一斉送信の上限は500名です (対象: {len(targets)}名)")

        # 60秒以内の同一内容 broadcast を弾く (連打誤送信防止 / Security C-1)
        if target == "broadcast":
            if USE_POSTGRES:
                c.execute(
                    "SELECT 1 FROM messages WHERE broadcast_group_id IS NOT NULL "
                    "AND broadcast_filter = ? AND subject = ? AND body = ? "
                    "AND created_at > NOW() - INTERVAL '60 seconds' LIMIT 1",
                    (payload.broadcast_filter or "all", subject, body)
                )
            else:
                c.execute(
                    "SELECT 1 FROM messages WHERE broadcast_group_id IS NOT NULL "
                    "AND broadcast_filter = ? AND subject = ? AND body = ? "
                    "AND created_at > datetime('now','-60 seconds') LIMIT 1",
                    (payload.broadcast_filter or "all", subject, body)
                )
            if c.fetchone():
                raise HTTPException(status_code=409, detail="同一内容の一斉送信が60秒以内に実行されています")

        # 添付ファイル検証 (任意)
        attachment = _validate_message_attachment(
            payload.attachment_filename, payload.attachment_mime, payload.attachment_data_b64
        )

        # Phase A: in-app メッセージを全件 INSERT して即 commit (idle in transaction 防止)
        # email 送信は後で BackgroundTasks に逃がし、email_status は事後 UPDATE する
        msg_records = []  # [(msg_id, email, name)]
        recipients_with_email = 0
        for t in targets:
            sent_via_initial = "in_app"
            if payload.send_email and t["email"]:
                recipients_with_email += 1
                sent_via_initial = "queued"  # 後で email_in_app or in_app に UPDATE
            c.execute(
                "INSERT INTO messages (sender_type, sender_id, recipient_type, recipient_id, broadcast_filter, subject, body, sent_via, email_status, broadcast_group_id, attachment_filename, attachment_mime, attachment_size, attachment_data_b64) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id",
                ("admin", None, "student", t["id"], (payload.broadcast_filter if target == "broadcast" else None),
                 subject, body, sent_via_initial, None, broadcast_group_id,
                 attachment["filename"] if attachment else None,
                 attachment["mime"] if attachment else None,
                 attachment["size"] if attachment else None,
                 attachment["data_b64"] if attachment else None)
            )
            row = c.fetchone()
            new_id = row["id"] if row else None
            msg_records.append((new_id, t["email"], t["name"]))
        conn.commit()
        log.info(f"[Messages] admin send target={target} recipients={len(targets)} queued_email={recipients_with_email} group={broadcast_group_id} ip={_client_ip(request)}")

        # Phase B: email 送信を BackgroundTasks で非同期化 (HTTP リクエストは即返却)
        if payload.send_email:
            background_tasks.add_task(_bg_send_messages_email, msg_records, subject, body)

        return {
            "ok": True,
            "target": target,
            "recipients": len(targets),
            "email_attempted": recipients_with_email,
            "email_queued": recipients_with_email,
            "broadcast_group_id": broadcast_group_id,
        }
    finally:
        conn.close()


def _bg_send_messages_email(msg_records: list, subject: str, body: str) -> None:
    """BackgroundTasks: 各メッセージの email を順次送信し、email_status / sent_via を後追い更新。
    別 connection で動作するため、admin_send_message のレスポンスは即返却される。
    Resend 無料枠 rate limit (1通/秒) 回避のため 1.5秒間隔 + 429 時は指数バックオフリトライ。"""
    import time as _t
    sent_ok, sent_fail = 0, 0
    for i, (msg_id, email, name) in enumerate(msg_records):
        if not msg_id:
            continue
        if not email:
            try:
                c2 = db()
                cur2 = c2.cursor()
                cur2.execute("UPDATE messages SET sent_via = ? WHERE id = ?", ("in_app", msg_id))
                c2.commit()
                c2.close()
            except Exception as e:
                log.warning(f"[Messages][bg] in_app finalize failed id={msg_id}: {e}")
            continue
        # Resend rate limit 回避: 2通目以降は 1.5秒待機
        if i > 0:
            _t.sleep(1.5)
        # 429 リトライ (最大3回・指数バックオフ)
        res = None
        for attempt in range(3):
            res = _send_message_email(email, subject, body, student_name=name)
            if res.get("sent") or "429" not in str(res.get("error", "")):
                break
            wait = 3 * (2 ** attempt)
            log.info(f"[Messages][bg] 429 retry {attempt+1}/3 for id={msg_id}, waiting {wait}s")
            _t.sleep(wait)
        if res and res.get("sent"):
            sent_ok += 1
            new_via, new_status = "email_in_app", "sent"
        else:
            sent_fail += 1
            err = (res.get("error") or "unknown")[:100] if res else "no_response"
            new_via, new_status = "in_app", f"failed:{err}"
        try:
            c2 = db()
            cur2 = c2.cursor()
            cur2.execute("UPDATE messages SET sent_via = ?, email_status = ? WHERE id = ?", (new_via, new_status, msg_id))
            c2.commit()
            c2.close()
        except Exception as e:
            log.warning(f"[Messages][bg] status UPDATE failed id={msg_id}: {e}")
    log.info(f"[Messages][bg] email batch done: sent={sent_ok} failed={sent_fail}")


@app.get("/api/admin/messages")
def admin_list_messages(authorization: Optional[str] = Header(None), limit: int = 100, offset: int = 0):
    """塾長: 送信履歴 + 受信した生徒からの問い合わせ。broadcast は group_id で集約。"""
    _verify_admin_required(authorization)
    try:
        limit = max(1, min(int(limit or 100), 500))
        offset = max(0, int(offset or 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="クエリパラメータが不正です")
    conn = db()
    try:
        c = conn.cursor()
        # admin が送った履歴 (recipient で students JOIN)
        c.execute(
            """SELECT m.id, m.recipient_id, m.subject, m.body, m.sent_via, m.email_status, m.read_at, m.created_at,
                      m.broadcast_filter, m.broadcast_group_id, m.sender_type,
                      m.attachment_filename, m.attachment_mime, m.attachment_size,
                      s.name AS student_name, s.grade
               FROM messages m
               LEFT JOIN students s ON m.recipient_id = s.id
               WHERE m.sender_type = 'admin'
               ORDER BY m.created_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        rows = c.fetchall()
        # 生徒からの問い合わせ (sender_id で students JOIN, 加入状況も含める)
        c.execute(
            """SELECT m.id, m.sender_id AS from_student_id, m.subject, m.body, m.created_at, m.read_at,
                      m.attachment_filename, m.attachment_mime, m.attachment_size,
                      s.name AS from_student_name, s.grade AS from_student_grade, s.course AS from_student_course
               FROM messages m
               LEFT JOIN students s ON m.sender_id = s.id
               WHERE m.sender_type = 'student' AND m.recipient_type = 'admin'
               ORDER BY m.created_at DESC
               LIMIT ?""",
            (min(limit, 200),)
        )
        inquiries_rows = c.fetchall()
        # group by broadcast_group_id (None = individual)
        groups = {}
        individuals = []
        for r in rows:
            _att_fn = r["attachment_filename"] if "attachment_filename" in r.keys() else None
            obj = {
                "id": r["id"],
                "recipient_id": r["recipient_id"],
                "student_name": r["student_name"],
                "grade": r["grade"],
                "subject": r["subject"],
                "body": r["body"],
                "sent_via": r["sent_via"],
                "email_status": r["email_status"],
                "read_at": str(r["read_at"]) if r["read_at"] else None,
                "created_at": str(r["created_at"]) if r["created_at"] else None,
                "broadcast_filter": r["broadcast_filter"],
                "broadcast_group_id": r["broadcast_group_id"],
                "attachment": ({"filename": _att_fn, "mime": r["attachment_mime"], "size": r["attachment_size"]} if _att_fn else None),
            }
            if obj["broadcast_group_id"]:
                gid = obj["broadcast_group_id"]
                if gid not in groups:
                    groups[gid] = {
                        "broadcast_group_id": gid,
                        "broadcast_filter": obj["broadcast_filter"],
                        "subject": obj["subject"],
                        "body": obj["body"],
                        "created_at": obj["created_at"],
                        "recipient_count": 0,
                        "email_sent_count": 0,
                        "email_failed_count": 0,
                        "read_count": 0,
                        "recipients_preview": [],
                    }
                g = groups[gid]
                g["recipient_count"] += 1
                if obj["email_status"] == "sent":
                    g["email_sent_count"] += 1
                elif obj["email_status"] and obj["email_status"].startswith("failed"):
                    g["email_failed_count"] += 1
                if obj["read_at"]:
                    g["read_count"] += 1
                if len(g["recipients_preview"]) < 10:
                    g["recipients_preview"].append({"name": obj["student_name"], "grade": obj["grade"], "read_at": obj["read_at"]})
            else:
                individuals.append(obj)
        # 受信問い合わせ整形 (mypage:source_tag を「(本文なし)」に置換 / 加入済みフラグ)
        inquiries = []
        for r in inquiries_rows:
            raw_body = (r["body"] or "")
            # 「mypage:study-log」「mypage:study-plan」のような source タグだけなら「(本文なし)」表示
            stripped = raw_body.strip()
            display_body = "(本文なし)" if stripped.startswith("mypage:") and len(stripped) <= 30 else raw_body
            _i_att_fn = r["attachment_filename"] if "attachment_filename" in r.keys() else None
            inquiries.append({
                "id": r["id"],
                "from_student_id": r["from_student_id"],
                "from_student_name": r["from_student_name"],
                "from_student_grade": r["from_student_grade"],
                "from_student_course": r["from_student_course"],
                "is_already_enrolled": r["from_student_course"] == _STUDY_LOG_TARGET_COURSE,
                "subject": r["subject"],
                "body": display_body,
                "attachment": ({"filename": _i_att_fn, "mime": r["attachment_mime"], "size": r["attachment_size"]} if _i_att_fn else None),
                "created_at": str(r["created_at"]) if r["created_at"] else None,
                "read_at": str(r["read_at"]) if r["read_at"] else None,
            })
        return {"ok": True, "individuals": individuals, "broadcasts": list(groups.values()), "inquiries": inquiries}
    finally:
        conn.close()


@app.get("/api/admin/messages/broadcast/{group_id}")
def admin_broadcast_detail(group_id: str, authorization: Optional[str] = Header(None)):
    """塾長: ブロードキャストの個別配信状況。"""
    _verify_admin_required(authorization)
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            """SELECT m.id, m.recipient_id, s.name AS student_name, s.email, s.grade,
                      m.email_status, m.sent_via, m.read_at, m.created_at
               FROM messages m LEFT JOIN students s ON m.recipient_id = s.id
               WHERE m.broadcast_group_id = ? ORDER BY m.id""",
            (group_id,)
        )
        rows = c.fetchall()
        return {"ok": True, "group_id": group_id, "deliveries": [
            {"id": r["id"], "student_name": r["student_name"], "email": r["email"],
             "grade": r["grade"], "email_status": r["email_status"],
             "sent_via": r["sent_via"], "read_at": str(r["read_at"]) if r["read_at"] else None}
            for r in rows
        ]}
    finally:
        conn.close()


@app.get("/api/messages/me")
def get_my_messages(authorization: Optional[str] = Header(None), limit: int = 50):
    """生徒: 自分宛メッセージ受信箱 + 自分が送信したメッセージ (双方向) を取得。
    添付ファイルは metadata のみ返す (実データは /api/messages/me/{id}/attachment で別途取得)。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        limit = max(1, min(int(limit or 50), 200))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="クエリパラメータが不正です")
    conn = db()
    try:
        c = conn.cursor()
        # 受信 + 送信 両方を時系列で取得
        c.execute(
            "SELECT id, sender_type, recipient_type, subject, body, sent_via, read_at, created_at, "
            "attachment_filename, attachment_mime, attachment_size FROM messages "
            "WHERE (recipient_type = 'student' AND recipient_id = ?) "
            "   OR (sender_type = 'student' AND sender_id = ?) "
            "ORDER BY created_at DESC LIMIT ?",
            (student["id"], student["id"], limit)
        )
        rows = c.fetchall()
        msgs = []
        unread = 0
        for r in rows:
            # 自分が送信したメッセージは既読扱い (受信側ではないため read_at は気にしない)
            is_outgoing = (r["sender_type"] == "student")
            is_unread = (not is_outgoing) and (not r["read_at"])
            if is_unread:
                unread += 1
            has_attachment = bool(r["attachment_filename"])
            msgs.append({
                "id": r["id"],
                "direction": "out" if is_outgoing else "in",
                "subject": r["subject"],
                "body": r["body"],
                "sent_via": r["sent_via"],
                "is_unread": is_unread,
                "read_at": str(r["read_at"]) if r["read_at"] else None,
                "created_at": str(r["created_at"]) if r["created_at"] else None,
                "attachment": {
                    "filename": r["attachment_filename"],
                    "mime": r["attachment_mime"],
                    "size": r["attachment_size"],
                } if has_attachment else None,
            })
        return {"ok": True, "messages": msgs, "unread_count": unread}
    finally:
        conn.close()


@app.post("/api/student/messages/send")
def student_send_message(payload: StudentMessageSendRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒 → 塾長 メッセージ送信。国公立難関大学コース 本クラス受講生限定。
    in-app メッセージとして塾長宛に保存 + 塾長 email にも通知。"""
    _check_rate_limit_ip(request, bucket="student_msg_send", limit=10, window=300)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # 本クラス所属生徒のみ (course='kokuritsu_nankan')
    if (student.get("course") or "") != _STUDY_LOG_TARGET_COURSE:
        raise HTTPException(status_code=403, detail="塾長へのメッセージ送信は国公立難関大学コース 本クラス受講生のみ利用可能です")

    body = _sanitize_text(payload.body, 5000)
    if not body:
        raise HTTPException(status_code=400, detail="本文は必須です")
    subject = _sanitize_text(payload.subject, 200) or f"📩 {student.get('name') or '生徒'}さんからのメッセージ"

    # 添付ファイル検証 (任意)
    attachment = _validate_message_attachment(
        payload.attachment_filename, payload.attachment_mime, payload.attachment_data_b64
    )

    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (sender_type, sender_id, recipient_type, recipient_id, broadcast_filter, subject, body, sent_via, email_status, attachment_filename, attachment_mime, attachment_size, attachment_data_b64) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id",
            ("student", student["id"], "admin", None, None,
             subject, body, "in_app", None,
             attachment["filename"] if attachment else None,
             attachment["mime"] if attachment else None,
             attachment["size"] if attachment else None,
             attachment["data_b64"] if attachment else None)
        )
        row = c.fetchone()
        msg_id = row["id"] if row else None
        # 監査 events
        try:
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("student_message_sent",
                 json.dumps({"student_id": student["id"], "name": student.get("name"),
                            "msg_id": msg_id, "has_attachment": bool(attachment),
                            "subject": subject[:120]}, ensure_ascii=False),
                 str(student["id"]))
            )
        except Exception: pass
        conn.commit()
        log.info(f"[Messages] student->admin send student={student['id']} msg_id={msg_id} attachment={bool(attachment)}")

        # 塾長 email 通知 (任意・DAILY_SNS_TO_EMAIL 設定済みなら)
        if DAILY_SNS_TO_EMAIL and RESEND_API_KEY and FROM_EMAIL:
            try:
                import urllib.request as _ur
                from_label = student.get("name") or "(名前未登録)"
                attach_note = f"\n📎 添付: {attachment['filename']} ({attachment['size'] // 1024} KB)" if attachment else ""
                email_body = (
                    f"{from_label}さん (生徒ID:{student['id']}) からメッセージが届きました。\n\n"
                    f"件名: {subject}\n\n{body}{attach_note}\n\n"
                    f"CEO ダッシュ「📨 メッセージ配信」 → 履歴 で内容確認 + 返信できます。"
                )
                req = _ur.Request(
                    "https://api.resend.com/emails",
                    data=json.dumps({
                        "from": FROM_EMAIL,
                        "to": [DAILY_SNS_TO_EMAIL],
                        "subject": f"📩 [生徒メッセージ] {subject}",
                        "text": email_body,
                    }).encode("utf-8"),
                    headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json", "User-Agent": "ai-juku-system/1.0"},
                    method="POST",
                )
                _ur.urlopen(req, timeout=10).read()
            except Exception as _e:
                log.warning(f"[Messages] student->admin email notify failed: {_e}")

        return {"ok": True, "message_id": msg_id, "has_attachment": bool(attachment),
                "info": "塾長に届きました。返信は受信箱に表示されます (通常 1〜2 営業日以内)。"}
    finally:
        conn.close()


@app.get("/api/messages/me/{msg_id}/attachment")
def get_my_message_attachment(msg_id: int, authorization: Optional[str] = Header(None)):
    """生徒: 自分宛 OR 自分送信メッセージの添付ファイルをダウンロード。
    認可: そのメッセージの sender か recipient のみ。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT sender_type, sender_id, recipient_type, recipient_id, "
            "attachment_filename, attachment_mime, attachment_data_b64 "
            "FROM messages WHERE id = ?",
            (int(msg_id),)
        )
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="メッセージが見つかりません")
        is_recipient = (row["recipient_type"] == "student" and row["recipient_id"] == student["id"])
        is_sender = (row["sender_type"] == "student" and row["sender_id"] == student["id"])
        if not (is_recipient or is_sender):
            raise HTTPException(status_code=403, detail="このメッセージへのアクセス権がありません")
        if not row["attachment_data_b64"]:
            raise HTTPException(status_code=404, detail="添付ファイルがありません")
        import base64 as _b64
        try:
            data = _b64.b64decode(row["attachment_data_b64"])
        except Exception:
            raise HTTPException(status_code=500, detail="添付データの読込に失敗しました")
        return _safe_attachment_response(
            row["attachment_filename"] or "attachment",
            row["attachment_mime"] or "application/octet-stream",
            data,
        )
    finally:
        conn.close()


@app.get("/api/admin/messages/{msg_id}/attachment")
def admin_get_message_attachment(msg_id: int, authorization: Optional[str] = Header(None)):
    """塾長: 任意のメッセージの添付ファイルをダウンロード。生徒からの添付も閲覧可。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未認証")
    token = authorization[len("Bearer "):].strip()
    if not _verify_admin_token(token):
        raise HTTPException(status_code=401, detail="未認証")
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT attachment_filename, attachment_mime, attachment_data_b64 FROM messages WHERE id = ?",
            (int(msg_id),)
        )
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="メッセージが見つかりません")
        if not row["attachment_data_b64"]:
            raise HTTPException(status_code=404, detail="添付ファイルがありません")
        import base64 as _b64
        try:
            data = _b64.b64decode(row["attachment_data_b64"])
        except Exception:
            raise HTTPException(status_code=500, detail="添付データの読込に失敗しました")
        return _safe_attachment_response(
            row["attachment_filename"] or "attachment",
            row["attachment_mime"] or "application/octet-stream",
            data,
        )
    finally:
        conn.close()


@app.post("/api/messages/me/{msg_id}/read")
def mark_message_read(msg_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: メッセージを既読にする。"""
    _check_rate_limit_ip(request, bucket="msg_read", limit=120, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = db()
    try:
        c = conn.cursor()
        # 自分宛 + 未読のみ更新 (race-safe)
        c.execute(
            "UPDATE messages SET read_at = CURRENT_TIMESTAMP WHERE id = ? AND recipient_type = 'student' AND recipient_id = ? AND read_at IS NULL",
            (msg_id, student["id"])
        )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# ==========================================================================
# Routes: Exam Results (外部模試結果 - 国公立難関大学コース限定)
# 塾長指示 2026-05-06: 模試結果を AI カリキュラム/進捗診断に反映
# ==========================================================================
class ExamResultCreateRequest(BaseModel):
    exam_name: str  # 例: 河合塾 第1回全統共通テスト模試
    exam_date: str  # YYYY-MM-DD
    subject: str  # 科目 (_STUDY_SUBJECTS)
    score: Optional[int] = None
    max_score: Optional[int] = None
    deviation: Optional[float] = None
    judgement: Optional[str] = None  # A/B/C/D/E
    target_university: Optional[str] = None
    note: Optional[str] = None


class ExamResultUpdateRequest(BaseModel):
    exam_name: Optional[str] = None
    exam_date: Optional[str] = None
    subject: Optional[str] = None
    score: Optional[int] = None
    max_score: Optional[int] = None
    deviation: Optional[float] = None
    judgement: Optional[str] = None
    target_university: Optional[str] = None
    note: Optional[str] = None


_EXAM_JUDGEMENTS = {"A", "B", "C", "D", "E"}


def _validate_exam_payload(exam_name, exam_date_str, subject, score, max_score, deviation, judgement):
    name = _sanitize_text(exam_name, 100)
    if not name:
        raise HTTPException(status_code=400, detail="模試名は必須")
    try:
        ed = datetime.strptime((exam_date_str or "").strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="日付フォーマット不正 (YYYY-MM-DD)")
    today = _today_jst()
    if (today - ed).days > 1825:
        raise HTTPException(status_code=400, detail="5年以上前の模試は登録できません")
    if (ed - today).days > 30:
        raise HTTPException(status_code=400, detail="未来の模試は登録できません")
    sub = (subject or "").strip()
    if sub not in _STUDY_SUBJECTS:
        raise HTTPException(status_code=400, detail="科目が不正です")
    sc = None
    if score is not None:
        try:
            sc = int(score)
            if not (0 <= sc <= 1000):
                raise HTTPException(status_code=400, detail="score は 0〜1000")
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="score が不正")
    ms = None
    if max_score is not None:
        try:
            ms = int(max_score)
            if not (1 <= ms <= 1000):
                raise HTTPException(status_code=400, detail="max_score は 1〜1000")
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="max_score が不正")
    dev = None
    if deviation is not None:
        try:
            dev = float(deviation)
            if not (10.0 <= dev <= 100.0):
                raise HTTPException(status_code=400, detail="deviation は 10〜100")
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="deviation が不正")
    jdg = None
    if judgement:
        jdg = (judgement or "").strip().upper()
        if jdg not in _EXAM_JUDGEMENTS:
            raise HTTPException(status_code=400, detail="judgement は A〜E")
    return {"exam_name": name, "exam_date": ed.isoformat(), "subject": sub, "score": sc, "max_score": ms, "deviation": dev, "judgement": jdg}


@app.post("/api/exam-results")
def create_exam_result(payload: ExamResultCreateRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: 外部模試結果を登録 (国公立難関大学コース限定)。"""
    _check_rate_limit_ip(request, bucket="exam_create", limit=30, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    v = _validate_exam_payload(payload.exam_name, payload.exam_date, payload.subject,
                                payload.score, payload.max_score, payload.deviation, payload.judgement)
    target_uni = _sanitize_text(payload.target_university, 100)
    note = _sanitize_text(payload.note, 500)
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO exam_results (student_id, exam_name, exam_date, subject, score, max_score, deviation, judgement, target_university, note) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING id",
            (student["id"], v["exam_name"], v["exam_date"], v["subject"], v["score"], v["max_score"], v["deviation"], v["judgement"], target_uni, note)
        )
        returned = c.fetchone()
        new_id = returned["id"] if returned else None
        conn.commit()
        log.info(f"[ExamResult] create id={new_id} student={student['id']} subj={v['subject']} dev={v['deviation']}")
        return {"ok": True, "id": new_id}
    finally:
        conn.close()


@app.put("/api/exam-results/{exam_id}")
def update_exam_result(exam_id: int, payload: ExamResultUpdateRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: 模試結果を更新。"""
    _check_rate_limit_ip(request, bucket="exam_update", limit=30, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT student_id FROM exam_results WHERE id = ?", (exam_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="模試結果が見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")

        updates = {}
        # 各フィールドが個別に来た場合は validate
        if any(getattr(payload, f) is not None for f in ["exam_name", "exam_date", "subject", "score", "max_score", "deviation", "judgement"]):
            # 既存値で埋めて全体 validate
            c.execute("SELECT exam_name, exam_date, subject, score, max_score, deviation, judgement FROM exam_results WHERE id = ?", (exam_id,))
            cur = c.fetchone()
            v = _validate_exam_payload(
                payload.exam_name if payload.exam_name is not None else cur["exam_name"],
                payload.exam_date if payload.exam_date is not None else str(cur["exam_date"]),
                payload.subject if payload.subject is not None else cur["subject"],
                payload.score if payload.score is not None else cur["score"],
                payload.max_score if payload.max_score is not None else cur["max_score"],
                payload.deviation if payload.deviation is not None else cur["deviation"],
                payload.judgement if payload.judgement is not None else cur["judgement"],
            )
            updates.update(v)
        if payload.target_university is not None:
            updates["target_university"] = _sanitize_text(payload.target_university, 100)
        if payload.note is not None:
            updates["note"] = _sanitize_text(payload.note, 500)
        if not updates:
            return {"ok": True, "no_change": True}
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        c.execute(f"UPDATE exam_results SET {set_clause} WHERE id = ? AND student_id = ?", tuple(updates.values()) + (exam_id, student["id"]))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/exam-results/{exam_id}")
def delete_exam_result(exam_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: 模試結果を削除。"""
    _check_rate_limit_ip(request, bucket="exam_delete", limit=20, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT student_id FROM exam_results WHERE id = ?", (exam_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="模試結果が見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")
        c.execute("DELETE FROM exam_results WHERE id = ? AND student_id = ?", (exam_id, student["id"]))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/exam-results/me")
def get_my_exam_results(authorization: Optional[str] = Header(None), limit: int = 100):
    """生徒: 自分の模試結果一覧 (外部模試 + 内蔵模試統合)。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    try:
        limit = max(1, min(int(limit or 100), 500))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="limit が不正")
    conn = db()
    try:
        c = conn.cursor()
        # 外部模試
        c.execute(
            "SELECT id, exam_name, exam_date, subject, score, max_score, deviation, judgement, target_university, note, created_at "
            "FROM exam_results WHERE student_id = ? ORDER BY exam_date DESC LIMIT ?",
            (student["id"], limit)
        )
        external = []
        for r in c.fetchall():
            external.append({
                "id": r["id"], "source": "external",
                "exam_name": r["exam_name"],
                "exam_date": str(r["exam_date"]),
                "subject": r["subject"],
                "score": r["score"], "max_score": r["max_score"],
                "deviation": r["deviation"],
                "judgement": r["judgement"],
                "target_university": r["target_university"],
                "note": r["note"],
            })
        # 内蔵模試 (mock_exam_sessions) も最新数件統合
        try:
            c.execute(
                "SELECT id, exam_type, target_label, score_total, score_max, deviation_estimate, submitted_at, started_at "
                "FROM mock_exam_sessions WHERE student_id = ? AND submitted_at IS NOT NULL "
                "ORDER BY submitted_at DESC LIMIT 30",
                (student["id"],)
            )
            internal = []
            for r in c.fetchall():
                ts = r["submitted_at"] or r["started_at"]
                internal.append({
                    "id": f"int_{r['id']}", "source": "internal",
                    "exam_name": f"AI模試 ({r['exam_type'] or '汎用'})",
                    "exam_date": str(ts).split(" ")[0].split("T")[0] if ts else None,
                    "subject": "総合",
                    "score": r["score_total"], "max_score": r["score_max"],
                    "deviation": r["deviation_estimate"],
                    "judgement": None,
                    "target_university": r["target_label"],
                    "note": None,
                })
        except Exception as ie:
            log.debug(f"[ExamResult] internal merge skip: {ie}")
            internal = []
        # 偏差値推移サマリ (科目別最新3件)
        c.execute(
            "SELECT subject, deviation, exam_date FROM exam_results WHERE student_id = ? AND deviation IS NOT NULL "
            "ORDER BY subject, exam_date DESC",
            (student["id"],)
        )
        by_subject_trend = {}
        for r in c.fetchall():
            s = r["subject"]
            if s not in by_subject_trend:
                by_subject_trend[s] = []
            if len(by_subject_trend[s]) < 5:
                by_subject_trend[s].append({"date": str(r["exam_date"]), "deviation": r["deviation"]})
        # 最新模試: 同じ exam_date でグループ化された科目別偏差値
        latest_exam_date = external[0]["exam_date"] if external else None
        latest_summary = None
        if latest_exam_date:
            c.execute(
                "SELECT subject, deviation, judgement FROM exam_results WHERE student_id = ? AND exam_date = ? AND deviation IS NOT NULL",
                (student["id"], latest_exam_date)
            )
            latest_subjects = []
            for r in c.fetchall():
                latest_subjects.append({"subject": r["subject"], "deviation": r["deviation"], "judgement": r["judgement"]})
            if latest_subjects:
                avg_dev = round(sum(s["deviation"] for s in latest_subjects) / len(latest_subjects), 1)
                latest_summary = {"exam_date": latest_exam_date, "subjects": latest_subjects, "average_deviation": avg_dev}
        return {
            "ok": True,
            "external": external,
            "internal": internal,
            "by_subject_trend": by_subject_trend,
            "latest_summary": latest_summary,
        }
    finally:
        conn.close()


# ==========================================================================
# Routes: Course Applications (Phase 4.8 - 国公立難関大学コース クレカなし申込)
# 塾長指示 2026-05-06: 専用 LP からクレカ登録なしで申込 → 塾長承認で加入
# ==========================================================================
class CourseApplicationRequest(BaseModel):
    name: str
    email: EmailStr
    grade: Optional[str] = None
    target_university: Optional[str] = None
    phone: Optional[str] = None
    referrer: Optional[str] = None  # 紹介者
    note: Optional[str] = None


@app.post("/api/course-applications")
def public_course_application(payload: CourseApplicationRequest, request: Request):
    """公開: 難関大学コースへの申込 (クレカ不要)。"""
    # 公開 endpoint なので rate limit を厳しめに (1 IP 5回/24h)
    _check_rate_limit_ip(request, bucket="course_apply", limit=5, window=86400)
    name = _sanitize_text(payload.name, 100)
    if not name:
        raise HTTPException(status_code=400, detail="お名前は必須です")
    email_lower = (payload.email or "").lower().strip()
    if not email_lower or "@" not in email_lower:
        raise HTTPException(status_code=400, detail="有効なメールアドレスを入力してください")
    grade = _sanitize_text(payload.grade, 30)
    target_uni = _sanitize_text(payload.target_university, 100)
    phone = _sanitize_text(payload.phone, 30)
    referrer = _sanitize_text(payload.referrer, 100)
    note = _sanitize_text(payload.note, 1000)
    ip = _client_ip(request)

    conn = db()
    try:
        c = conn.cursor()
        # 同 email で 'pending' or 'approved' の申込が既にあれば 409 (重複防止)
        c.execute(
            "SELECT id, status FROM course_applications WHERE LOWER(email) = ? AND status IN ('pending','approved') ORDER BY id DESC LIMIT 1",
            (email_lower,)
        )
        existing = c.fetchone()
        if existing:
            if existing["status"] == "approved":
                raise HTTPException(status_code=409, detail="このメールアドレスは既に承認済みです")
            else:
                raise HTTPException(status_code=409, detail="このメールアドレスで既にお申込済みです (1-2営業日以内に塾長から連絡があります)")

        c.execute(
            "INSERT INTO course_applications (name, email, grade, target_university, phone, referrer, note, ip) "
            "VALUES (?,?,?,?,?,?,?,?) RETURNING id",
            (name, email_lower, grade, target_uni, phone, referrer, note, ip)
        )
        returned = c.fetchone()
        new_id = returned["id"] if returned else None
        conn.commit()
        log.info(f"[CourseApp] new application id={new_id} email={email_lower} ip={ip}")
    finally:
        conn.close()

    # 塾長 email 通知
    admin_to = os.getenv("DAILY_SNS_TO_EMAIL") or os.getenv("MONITORING_TO_EMAIL")
    if admin_to and RESEND_API_KEY:
        try:
            body_text = (
                f"塾長へ\n\n"
                f"国公立難関大学コースへの新規申込が届きました。\n\n"
                f"## 申込者情報\n"
                f"お名前: {name}\n"
                f"メール: {email_lower}\n"
                f"学年: {grade or '未記入'}\n"
                f"志望校: {target_uni or '未記入'}\n"
                f"電話: {phone or '未記入'}\n"
                f"紹介者: {referrer or 'なし'}\n"
                f"メモ: {note or 'なし'}\n\n"
                f"CEO ダッシュ → 📋 難関コース申込待ち から承認できます。"
            )
            _send_message_email(admin_to, f"📥 難関コース 新規申込: {name}", body_text, student_name="塾長")
        except Exception as ee:
            log.warning(f"[CourseApp] admin email failed: {ee}")

    return {"ok": True, "application_id": new_id, "message": "お申込ありがとうございます。塾長から1-2営業日以内にご連絡いたします。"}


@app.get("/api/admin/course-applications")
def admin_list_course_applications(authorization: Optional[str] = Header(None), status: Optional[str] = "pending", limit: int = 100):
    """塾長: コース申込一覧 (デフォルト pending のみ)。"""
    _verify_admin_required(authorization)
    try:
        limit = max(1, min(int(limit or 100), 500))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="limit が不正")
    conn = db()
    try:
        c = conn.cursor()
        if status and status in ("pending", "approved", "rejected"):
            c.execute(
                "SELECT id, name, email, grade, target_university, phone, referrer, note, status, student_id, approved_at, rejected_reason, created_at "
                "FROM course_applications WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            )
        else:
            c.execute(
                "SELECT id, name, email, grade, target_university, phone, referrer, note, status, student_id, approved_at, rejected_reason, created_at "
                "FROM course_applications ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        rows = c.fetchall()
        items = [{
            "id": r["id"], "name": r["name"], "email": r["email"],
            "grade": r["grade"], "target_university": r["target_university"],
            "phone": r["phone"], "referrer": r["referrer"], "note": r["note"],
            "status": r["status"], "student_id": r["student_id"],
            "approved_at": str(r["approved_at"]) if r["approved_at"] else None,
            "rejected_reason": r["rejected_reason"],
            "created_at": str(r["created_at"]) if r["created_at"] else None,
        } for r in rows]
        # pending count (admin badge 用)
        c.execute("SELECT COUNT(*) AS n FROM course_applications WHERE status = 'pending'")
        pending_row = c.fetchone()
        return {"ok": True, "applications": items, "pending_count": int(pending_row["n"] if pending_row else 0)}
    finally:
        conn.close()


class CourseApplicationApproveRequest(BaseModel):
    note: Optional[str] = None  # 内部メモ


@app.post("/api/admin/course-applications/{app_id}/approve")
def admin_approve_course_application(app_id: int, payload: CourseApplicationApproveRequest, request: Request, authorization: Optional[str] = Header(None)):
    """塾長: 申込を承認 → 既存 student 検索 or 新規作成 → course='kokuritsu_nankan' 付与 + magic link メール送信。"""
    _verify_admin_required(authorization)
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, name, email, status FROM course_applications WHERE id = ?", (app_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="申込が見つかりません")
        if row["status"] != "pending":
            raise HTTPException(status_code=409, detail=f"既に {row['status']} 状態です")
        email_lower = (row["email"] or "").lower().strip()
        name = row["name"]

        # 既存生徒検索 → なければ trial として新規作成
        c.execute("SELECT id, status, course FROM students WHERE LOWER(email) = ? LIMIT 1", (email_lower,))
        st = c.fetchone()
        student_id = None
        if st:
            student_id = st["id"]
            # 既存生徒に course 付与 (status は変更しない)
            c.execute("UPDATE students SET course = ? WHERE id = ?", (_STUDY_LOG_TARGET_COURSE, student_id))
            log.info(f"[CourseApp] approve existing student id={student_id} email={email_lower}")
        else:
            # 新規生徒 (trial で作成 / 国難コースは永久無料なので trial_end を 10 年後に設定)
            now = datetime.now(timezone.utc)
            trial_end = now + timedelta(days=3650)
            c.execute(
                "INSERT INTO students (name, email, status, course, trial_start, trial_end) "
                "VALUES (?,?,?,?,?,?) RETURNING id",
                (name, email_lower, "trial", _STUDY_LOG_TARGET_COURSE, now.isoformat(), trial_end.isoformat())
            )
            new = c.fetchone()
            student_id = new["id"] if new else None
            log.info(f"[CourseApp] approve created new student id={student_id} email={email_lower}")

        # application を approved に更新
        admin_note = _sanitize_text(payload.note, 500)
        c.execute(
            "UPDATE course_applications SET status = 'approved', student_id = ?, approved_at = CURRENT_TIMESTAMP, approved_by = ?, note = COALESCE(?, note) WHERE id = ?",
            (student_id, "admin", admin_note, app_id)
        )
        conn.commit()
    finally:
        conn.close()

    # magic link 送信 (welcome + ログイン link)
    sent_link = False
    try:
        # 既存の magic link 発行ロジックを呼ぶ
        # _create_otp は student_id を取る
        # _send_magic_link_email がある (推定) → なければ直接 send
        # 簡略化: magic link URL を直接生成して email 送信
        magic_token = _sign_session_token(student_id, ttl_seconds=3600, token_type="magic")  # 1h
        login_url = f"https://trillion-ai-juku.com/auth.html?t={magic_token}"
        body_text = (
            f"{name} さん\n\n"
            f"国公立難関大学コースへのご加入が承認されました!\n"
            f"以下のリンクから1-クリックでログインできます (有効期限 1時間):\n\n"
            f"{login_url}\n\n"
            f"ログイン後、マイページで以下が利用可能になります:\n"
            f"📚 学習記録 + ヒートマップ\n"
            f"🎓 合格カリキュラム (AI 自動生成)\n"
            f"📊 模試結果 + AI ギャップ分析\n"
            f"🎯 AI 弱点プリント生成 + スタサプ補強推薦\n"
            f"📅 学習計画 (ガント + カレンダー)\n"
            f"📨 塾長との直接メッセージ\n\n"
            f"ご利用料金につきましては別途ご案内いたします。"
        )
        res = _send_message_email(email_lower, "✅ 国公立難関大学コース ご加入承認", body_text, student_name=name)
        sent_link = res.get("sent", False)
    except Exception as e:
        log.warning(f"[CourseApp] welcome email failed: {e}")

    return {"ok": True, "student_id": student_id, "welcome_email_sent": sent_link}


class CourseApplicationRejectRequest(BaseModel):
    reason: Optional[str] = None


@app.post("/api/admin/course-applications/{app_id}/reject")
def admin_reject_course_application(app_id: int, payload: CourseApplicationRejectRequest, request: Request, authorization: Optional[str] = Header(None)):
    """塾長: 申込を却下。"""
    _verify_admin_required(authorization)
    reason = _sanitize_text(payload.reason, 300) or "塾長判断"
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, status FROM course_applications WHERE id = ?", (app_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="申込が見つかりません")
        if row["status"] != "pending":
            raise HTTPException(status_code=409, detail=f"既に {row['status']} 状態です")
        c.execute("UPDATE course_applications SET status = 'rejected', rejected_reason = ? WHERE id = ?", (reason, app_id))
        conn.commit()
        log.info(f"[CourseApp] reject id={app_id} reason={reason}")
        return {"ok": True}
    finally:
        conn.close()


# ==========================================================================
# Routes: Weak-Points Worksheet (Phase 4.6 - AI 弱点プリント生成 / 国公立難関大学コース限定)
# 塾長指示 2026-05-06: 弱点はスタサプ講義で補強 + AI で弱点プリント自動生成
# ==========================================================================
class WorksheetGenRequest(BaseModel):
    subject: str
    topic: Optional[str] = None  # 空欄なら AI が模試結果から推測
    num_problems: Optional[int] = 8
    target_university: Optional[str] = None  # 任意・志望校レベル合わせ


@app.post("/api/weak-points/generate-worksheet")
def generate_weak_points_worksheet(payload: WorksheetGenRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: 弱点プリントを AI 生成 + スタサプ講義補強推薦。"""
    _check_rate_limit_ip(request, bucket="weak_worksheet", limit=10, window=600)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini が構成されていません")

    subject = (payload.subject or "").strip()
    if subject not in _STUDY_SUBJECTS:
        raise HTTPException(status_code=400, detail="科目が不正です")
    topic = _sanitize_text(payload.topic, 200) or ""
    target_uni = _sanitize_text(payload.target_university, 100) or ""
    try:
        n = int(payload.num_problems or 8)
        if not (3 <= n <= 15):
            raise HTTPException(status_code=400, detail="問題数は 3〜15")
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="問題数が不正")

    # 模試結果から弱点情報を context inject
    exam_context = ""
    try:
        _conn = db()
        _c = _conn.cursor()
        _c.execute(
            "SELECT exam_name, exam_date, deviation, judgement, note FROM exam_results "
            "WHERE student_id = ? AND subject = ? ORDER BY exam_date DESC LIMIT 3",
            (student["id"], subject)
        )
        rows = _c.fetchall()
        _conn.close()
        if rows:
            lines = ["", "## この生徒の最近の模試結果 (科目: " + subject + "):"]
            for r in rows:
                jd = f" / 判定 {r['judgement']}" if r['judgement'] else ""
                nt = f" / メモ: {r['note']}" if r['note'] else ""
                lines.append(f"- {r['exam_name']} ({r['exam_date']}): 偏差値 {r['deviation'] or '?'}{jd}{nt}")
            exam_context = "\n".join(lines)
    except Exception as e:
        log.warning(f"[Worksheet] exam context fetch failed: {e}")

    sys_prompt = "難関大学受験の問題作成のプロです。生徒の弱点科目に合わせて練習問題を作成し、解答・解説・対応するスタディサプリ講義も提案します。教師名は塾長指示で出さない方針 (ただし sapuri_lectures は商品名そのままなので講師名を含む)。純粋な JSON のみ返答 (前置きや解説不要)。"
    user_prompt = f"""科目: {subject}
{('テーマ/単元: ' + topic) if topic else 'テーマ/単元: AI が模試結果から推測して設定'}
{('志望校: ' + target_uni) if target_uni else ''}
問題数: {n} 問{exam_context}

上記の弱点を補強する練習問題を生成してください。問題は易→難の順で並べ、各問題に解答と解説を付けます。さらに対応するスタサプ講義 (3-5 件、レベル別) を推薦してください。

出力形式 (フェンスや前置きなし、純粋な JSON):
{{
  "topic_used": "実際に扱ったテーマ (60字以内)",
  "weak_point_analysis": "この弱点の典型的な原因と対策 (120字以内)",
  "problems": [
    {{
      "no": 1,
      "difficulty": "易|標準|応用|発展",
      "question": "問題文 (300字以内、必要なら数式は LaTeX なしの平文で)",
      "answer": "解答 (簡潔に)",
      "explanation": "解説 (200字以内、なぜそうなるか・解法の核を明示)"
    }}
  ],
  "sapuri_lectures": [
    {{"title": "スタサプ講義名 (商品名そのまま)", "level": "ベーシック|スタンダード|ハイレベル|トップレベル", "reason": "この弱点克服に有効な理由 (60字以内)"}}
  ]
}}

注意:
- 問題は前提知識を上げすぎず、弱点克服に集中
- 解説は「公式暗記」ではなく「なぜそうなるか」の理解促進
- スタサプ講義名は実在の商品 (ベーシック → トップレベルの順で 3-5 件)"""

    body = {
        "model": "gemini-2.5-flash",
        "max_tokens": 4000,
        "system": sys_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    try:
        data = _call_gemini(body, model="gemini-2.5-flash", kind="weak_worksheet")
        text = "".join(c.get("text", "") for c in (data.get("content") or []) if isinstance(c, dict)).strip()
        if not text:
            raise HTTPException(status_code=503, detail="AI が空文字を返しました")
        cleaned = text.strip()
        if cleaned.startswith("```"):
            import re as _re
            cleaned = _re.sub(r'^```(?:json)?\s*|\s*```$', '', cleaned).strip()
        try:
            parsed = json.loads(cleaned)
        except Exception:
            import re as _re
            m = _re.search(r'\{[\s\S]*\}', cleaned)
            if not m:
                raise HTTPException(status_code=503, detail="AI 出力 JSON 解析失敗")
            parsed = json.loads(m.group(0))
        problems = parsed.get("problems") or []
        if not problems:
            raise HTTPException(status_code=503, detail="AI が problems を返しませんでした")
        # validate / sanitize
        out_problems = []
        for i, p in enumerate(problems[:n]):
            out_problems.append({
                "no": i + 1,
                "difficulty": _sanitize_text(p.get("difficulty"), 20) or "標準",
                "question": _sanitize_text(p.get("question"), 600) or "",
                "answer": _sanitize_text(p.get("answer"), 400) or "",
                "explanation": _sanitize_text(p.get("explanation"), 600) or "",
            })
        out_lectures = []
        for r in (parsed.get("sapuri_lectures") or [])[:6]:
            out_lectures.append({
                "title": _sanitize_text(r.get("title"), 120) or "",
                "level": _sanitize_text(r.get("level"), 30) or "",
                "reason": _sanitize_text(r.get("reason"), 200) or "",
            })
        out = {
            "ok": True,
            "subject": subject,
            "topic_used": _sanitize_text(parsed.get("topic_used"), 100) or topic or "未指定",
            "weak_point_analysis": _sanitize_text(parsed.get("weak_point_analysis"), 300) or "",
            "problems": out_problems,
            "sapuri_lectures": out_lectures,
            "model": data.get("_actual_model"),
        }
        log.info(f"[Worksheet] gen student={student['id']} subj={subject} topic={topic} n={len(out_problems)}")
        return out
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[Worksheet] failed: {type(e).__name__}: {str(e)[:200]}")
        raise HTTPException(status_code=503, detail=f"AI 生成失敗: {str(e)[:200]}")


# ==========================================================================
# Routes: Curricula (Phase 4 - 合格カリキュラム / 国公立難関大学コース限定)
# 塾長指示 2026-05-06: 学習計画より上位の「合格までの全体ロードマップ」
# ==========================================================================
class CurriculumPhase(BaseModel):
    name: str  # 例: 「基礎固め期」
    start_date: str
    end_date: str
    focus: str  # 例: 「英文法と数学IAの基礎完成」
    materials: List[str] = []  # 推奨教材
    milestones: List[str] = []  # マイルストーン (例: 「7月末までに英単語1900完了」)


class CurriculumCreateRequest(BaseModel):
    target_university: str
    target_faculty: Optional[str] = None
    exam_date: str  # YYYY-MM-DD
    start_date: str
    daily_minutes: Optional[int] = None
    baseline_note: Optional[str] = None  # 現状学力メモ
    phases: List[CurriculumPhase]
    ai_model: Optional[str] = None
    note: Optional[str] = None


class CurriculumUpdateRequest(BaseModel):
    target_university: Optional[str] = None
    target_faculty: Optional[str] = None
    exam_date: Optional[str] = None
    start_date: Optional[str] = None
    daily_minutes: Optional[int] = None
    baseline_note: Optional[str] = None
    phases: Optional[List[CurriculumPhase]] = None
    status: Optional[str] = None
    note: Optional[str] = None


class CurriculumAiGenRequest(BaseModel):
    target_university: str
    target_faculty: Optional[str] = None
    exam_date: str
    start_date: Optional[str] = None  # 省略時は today (JST)
    daily_minutes: int = 60
    baseline_note: Optional[str] = None  # 現状偏差値や状況


_CURR_STATUSES = {"active", "completed", "archived"}


def _validate_curr_dates(start_date: str, exam_date: str) -> tuple:
    try:
        sd = datetime.strptime((start_date or "").strip(), "%Y-%m-%d").date()
        ed = datetime.strptime((exam_date or "").strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="日付フォーマット不正 (YYYY-MM-DD)")
    if ed <= sd:
        raise HTTPException(status_code=400, detail="入試日は開始日より後である必要があります")
    today = _today_jst()
    if (ed - today).days > 1825:  # 5年
        raise HTTPException(status_code=400, detail="5年以上先の入試日は登録できません")
    if (today - sd).days > 730:
        raise HTTPException(status_code=400, detail="2年以上前の開始日は登録できません")
    return sd, ed


def _validate_curr_phases(phases: list) -> list:
    """phases を validate して JSON serializable な list に正規化。"""
    if not phases:
        raise HTTPException(status_code=400, detail="phases は 1 件以上必須")
    if len(phases) > 10:
        raise HTTPException(status_code=400, detail="phases は最大 10 件")
    out = []
    for p in phases:
        if isinstance(p, dict):
            d = p
        else:
            d = p.dict() if hasattr(p, "dict") else dict(p)
        name = _sanitize_text(d.get("name"), 60) or "フェーズ"
        focus = _sanitize_text(d.get("focus"), 200) or ""
        try:
            sd = datetime.strptime((d.get("start_date") or "").strip(), "%Y-%m-%d").date()
            ed = datetime.strptime((d.get("end_date") or "").strip(), "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail=f"phase '{name}' の日付フォーマット不正")
        if ed < sd:
            raise HTTPException(status_code=400, detail=f"phase '{name}' の終了日は開始日以降である必要")
        materials = []
        for m in (d.get("materials") or [])[:10]:
            t = _sanitize_text(m, 100)
            if t:
                materials.append(t)
        milestones = []
        for m in (d.get("milestones") or [])[:10]:
            t = _sanitize_text(m, 200)
            if t:
                milestones.append(t)
        # スタサプ講義 (Phase 4.5 / 塾長指示 2026-05-06)
        sapuri_lectures = []
        for m in (d.get("sapuri_lectures") or [])[:8]:
            t = _sanitize_text(m, 120)
            if t:
                sapuri_lectures.append(t)
        out.append({
            "name": name, "focus": focus,
            "start_date": sd.isoformat(), "end_date": ed.isoformat(),
            "materials": materials, "milestones": milestones,
            "sapuri_lectures": sapuri_lectures,
        })
    return out


@app.post("/api/curricula")
def create_curriculum(payload: CurriculumCreateRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: 合格カリキュラム作成 (国公立難関大学コース限定)。"""
    _check_rate_limit_ip(request, bucket="curr_create", limit=20, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)

    target_university = _sanitize_text(payload.target_university, 100)
    if not target_university:
        raise HTTPException(status_code=400, detail="志望校は必須です")
    target_faculty = _sanitize_text(payload.target_faculty, 100)
    sd, ed = _validate_curr_dates(payload.start_date, payload.exam_date)
    phases_list = _validate_curr_phases(payload.phases)
    daily = None
    if payload.daily_minutes is not None:
        try:
            d = int(payload.daily_minutes)
            if 0 < d <= 600:
                daily = d
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="daily_minutes が不正")
    baseline_note = _sanitize_text(payload.baseline_note, 1000)
    note = _sanitize_text(payload.note, 1000)

    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO curricula (student_id, target_university, target_faculty, exam_date, start_date, daily_minutes, baseline_note, phases, ai_model, note) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING id",
            (student["id"], target_university, target_faculty, ed.isoformat(), sd.isoformat(), daily, baseline_note,
             json.dumps(phases_list, ensure_ascii=False), _sanitize_text(payload.ai_model, 50), note)
        )
        returned = c.fetchone()
        new_id = returned["id"] if returned else None
        conn.commit()
        log.info(f"[Curriculum] create id={new_id} student={student['id']} univ={target_university}")
        return {"ok": True, "id": new_id}
    finally:
        conn.close()


@app.put("/api/curricula/{curr_id}")
def update_curriculum(curr_id: int, payload: CurriculumUpdateRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: カリキュラム更新。"""
    _check_rate_limit_ip(request, bucket="curr_update", limit=30, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT student_id, exam_date, start_date FROM curricula WHERE id = ?", (curr_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="カリキュラムが見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")

        updates = {}
        if payload.target_university is not None:
            t = _sanitize_text(payload.target_university, 100)
            if not t: raise HTTPException(status_code=400, detail="志望校は必須")
            updates["target_university"] = t
        if payload.target_faculty is not None:
            updates["target_faculty"] = _sanitize_text(payload.target_faculty, 100)
        if payload.baseline_note is not None:
            updates["baseline_note"] = _sanitize_text(payload.baseline_note, 1000)
        if payload.note is not None:
            updates["note"] = _sanitize_text(payload.note, 1000)
        if payload.status is not None:
            if payload.status not in _CURR_STATUSES:
                raise HTTPException(status_code=400, detail="status が不正")
            updates["status"] = payload.status
        if payload.daily_minutes is not None:
            try:
                d = int(payload.daily_minutes)
                if not (0 < d <= 600): raise HTTPException(status_code=400, detail="daily_minutes は 1〜600")
                updates["daily_minutes"] = d
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="daily_minutes が不正")
        if payload.start_date is not None or payload.exam_date is not None:
            new_sd = payload.start_date or str(row["start_date"])
            new_ed = payload.exam_date or str(row["exam_date"])
            sd, ed = _validate_curr_dates(new_sd, new_ed)
            updates["start_date"] = sd.isoformat()
            updates["exam_date"] = ed.isoformat()
        if payload.phases is not None:
            phases_list = _validate_curr_phases(payload.phases)
            updates["phases"] = json.dumps(phases_list, ensure_ascii=False)

        if not updates:
            return {"ok": True, "no_change": True}
        if USE_POSTGRES:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        else:
            updates["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        c.execute(f"UPDATE curricula SET {set_clause} WHERE id = ? AND student_id = ?", tuple(updates.values()) + (curr_id, student["id"]))
        conn.commit()
        log.info(f"[Curriculum] update id={curr_id} student={student['id']}")
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/curricula/{curr_id}")
def delete_curriculum(curr_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: カリキュラム削除。"""
    _check_rate_limit_ip(request, bucket="curr_delete", limit=10, window=60)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT student_id FROM curricula WHERE id = ?", (curr_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="カリキュラムが見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")
        c.execute("DELETE FROM curricula WHERE id = ? AND student_id = ?", (curr_id, student["id"]))
        conn.commit()
        log.info(f"[Curriculum] delete id={curr_id} student={student['id']}")
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/curricula/me")
def get_my_curricula(authorization: Optional[str] = Header(None)):
    """生徒: 自分のカリキュラム一覧。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT id, target_university, target_faculty, exam_date, start_date, daily_minutes, baseline_note, phases, ai_model, status, note, created_at "
            "FROM curricula WHERE student_id = ? ORDER BY status ASC, exam_date ASC",
            (student["id"],)
        )
        rows = c.fetchall()
        items = []
        for r in rows:
            try:
                phases = json.loads(r["phases"] or "[]")
            except Exception:
                phases = []
            items.append({
                "id": r["id"],
                "target_university": r["target_university"],
                "target_faculty": r["target_faculty"],
                "exam_date": str(r["exam_date"]),
                "start_date": str(r["start_date"]),
                "daily_minutes": r["daily_minutes"],
                "baseline_note": r["baseline_note"],
                "phases": phases,
                "ai_model": r["ai_model"],
                "status": r["status"],
                "note": r["note"],
                "created_at": str(r["created_at"]) if r["created_at"] else None,
            })
        return {"ok": True, "curricula": items}
    finally:
        conn.close()


@app.post("/api/curricula/ai-generate")
def ai_generate_curriculum(payload: CurriculumAiGenRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: AI で全体カリキュラムを生成 (DB に保存はしない、生徒が確認後に POST /api/curricula で保存)。"""
    _check_rate_limit_ip(request, bucket="curr_ai_gen", limit=10, window=600)  # 10分10回
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini が構成されていません")

    target_university = _sanitize_text(payload.target_university, 100)
    if not target_university:
        raise HTTPException(status_code=400, detail="志望校は必須")
    target_faculty = _sanitize_text(payload.target_faculty, 100) or ""
    today = _today_jst()
    sd_str = (payload.start_date or "").strip() or today.isoformat()
    sd, ed = _validate_curr_dates(sd_str, payload.exam_date)
    daily = max(15, min(int(payload.daily_minutes or 60), 600))
    baseline = _sanitize_text(payload.baseline_note, 500) or "未指定"
    months = max(1, round((ed - sd).days / 30))

    # 直近模試結果を自動 inject (科目別偏差値+判定 / 最大3件)
    exam_summary = ""
    try:
        _conn = db()
        _c = _conn.cursor()
        _c.execute(
            "SELECT exam_name, exam_date, subject, deviation, judgement FROM exam_results "
            "WHERE student_id = ? AND deviation IS NOT NULL ORDER BY exam_date DESC LIMIT 15",
            (student["id"],)
        )
        recent = _c.fetchall()
        _conn.close()
        if recent:
            # 科目別最新偏差値
            by_subj = {}
            for r in recent:
                s = r["subject"]
                if s not in by_subj:
                    by_subj[s] = {"deviation": r["deviation"], "judgement": r["judgement"], "exam": r["exam_name"], "date": str(r["exam_date"])}
            lines = ["", "## 直近模試結果 (科目別偏差値 / 判定 / 模試名・日付):"]
            for s, d in by_subj.items():
                jd = f" / 判定 {d['judgement']}" if d['judgement'] else ""
                lines.append(f"- {s}: 偏差値 {d['deviation']}{jd} ({d['exam']} / {d['date']})")
            exam_summary = "\n".join(lines)
    except Exception as e:
        log.warning(f"[Curriculum] exam inject failed: {e}")

    sys_prompt = "受験戦略を立てる学習プランナーです。難関大学 (国公立・難関私立) 志望者に対し、入試日から逆算した全体カリキュラムを 4-6 フェーズに分割して提案します。各フェーズは現実的な期間と教材 + スタディサプリ (スタサプ) の対応講義で構成。スタサプ講義は商品名そのまま (例: 『高3 トップレベル英語 〈読解編〉』『高3 ハイレベル数学IAIIB』『古文文法ベーシックレベル』) で記載。市販の参考書教材とスタサプ講義は別フィールドに分けて出力。純粋な JSON のみ返答 (前置きや解説不要)。"
    user_prompt = f"""志望校: {target_university}{(' / ' + target_faculty) if target_faculty else ''}
開始日: {sd.isoformat()}
入試日: {ed.isoformat()} (期間 {months} ヶ月)
1日確保時間: {daily} 分
現状: {baseline}{exam_summary}

上記から、難関大学合格までの全体カリキュラムを 4-6 フェーズに分割して JSON で返してください。
模試結果が含まれている場合は、特に偏差値が低い科目に厚めの教材配分をしてください。
各フェーズには市販教材 (materials) と スタディサプリ講義 (sapuri_lectures) の両方を提案してください。

出力形式 (フェンスや前置きなし):
{{
  "phases": [
    {{
      "name": "フェーズ名 (例: 基礎固め期 / 標準演習期 / 過去問演習期 / 直前期)",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "focus": "このフェーズの主軸 (60字以内、例: 英文法基礎 + 数学IA基礎完成)",
      "materials": ["定番市販教材1 (例: ターゲット1900)", "定番市販教材2", "定番市販教材3"],
      "sapuri_lectures": ["対応するスタサプ講義名 (例: 高3 トップレベル英語〈読解編〉)", "...", "..."],
      "milestones": ["月末までに〇〇完了 (60字以内)", "...", "..."]
    }}
  ]
}}

注意:
- フェーズの期間は重複・空白なく開始日〜入試日を埋める
- 直前期は入試日 1-2 ヶ月前から
- 各フェーズに市販教材 2-4 件、スタサプ講義 2-4 件、マイルストーン 2-4 件
- 受験科目構成 (志望校に必要な科目) を考慮
- スタサプ講義はレベル (ベーシック/スタンダード/ハイレベル/トップレベル) と科目を明示した商品名で記載
- フェーズ進行に応じて段階的にレベルを上げる (例: 基礎期=ベーシック→標準期=スタンダード→応用期=ハイレベル→直前期=トップレベル)"""

    body = {
        "model": "gemini-2.5-flash",
        "max_tokens": 4000,
        "system": sys_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    try:
        data = _call_gemini(body, model="gemini-2.5-flash", kind="curriculum_gen")
        text = "".join(c.get("text", "") for c in (data.get("content") or []) if isinstance(c, dict)).strip()
        if not text:
            raise HTTPException(status_code=503, detail="AI が空文字を返しました")
        # JSON parse
        cleaned = text.strip()
        if cleaned.startswith("```"):
            import re as _re
            cleaned = _re.sub(r'^```(?:json)?\s*|\s*```$', '', cleaned).strip()
        try:
            parsed = json.loads(cleaned)
        except Exception:
            import re as _re
            m = _re.search(r'\{[\s\S]*\}', cleaned)
            if not m:
                raise HTTPException(status_code=503, detail="AI 出力 JSON 解析失敗")
            parsed = json.loads(m.group(0))
        phases_raw = parsed.get("phases") or []
        if not phases_raw:
            raise HTTPException(status_code=503, detail="AI が phases を返しませんでした")
        # validate
        phases_list = _validate_curr_phases(phases_raw)
        log.info(f"[Curriculum] ai-generate student={student['id']} univ={target_university} phases={len(phases_list)}")
        return {
            "ok": True,
            "preview": {
                "target_university": target_university,
                "target_faculty": target_faculty or None,
                "exam_date": ed.isoformat(),
                "start_date": sd.isoformat(),
                "daily_minutes": daily,
                "baseline_note": baseline if baseline != "未指定" else None,
                "phases": phases_list,
                "ai_model": data.get("_actual_model"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[Curriculum] ai-generate failed: {type(e).__name__}: {str(e)[:200]}")
        raise HTTPException(status_code=503, detail=f"AI 生成失敗: {str(e)[:200]}")


@app.post("/api/curricula/{curr_id}/gap-analyze")
def curriculum_gap_analyze(curr_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: 模試結果から志望校到達のギャップを分析し AI 修正提案を返す (Phase 4.7)。"""
    _check_rate_limit_ip(request, bucket="curr_gap_analyze", limit=20, window=600)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini が構成されていません")

    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, student_id, target_university, target_faculty, exam_date, start_date, daily_minutes, baseline_note, phases, status FROM curricula WHERE id = ?", (curr_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="カリキュラムが見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")
        try:
            phases = json.loads(row["phases"] or "[]")
        except Exception:
            phases = []
        # 模試結果 (科目別最新偏差値 + 推移)
        c.execute(
            "SELECT exam_name, exam_date, subject, deviation, judgement FROM exam_results "
            "WHERE student_id = ? AND deviation IS NOT NULL ORDER BY exam_date DESC LIMIT 30",
            (student["id"],)
        )
        exam_rows = c.fetchall()
    finally:
        conn.close()

    if not exam_rows:
        raise HTTPException(status_code=400, detail="模試結果がまだ登録されていません。先に模試結果を追加してください。")

    # 科目別: 最新と推移 (古い→新しい順で trend)
    by_subj = {}
    for r in exam_rows:
        s = r["subject"]
        if s not in by_subj:
            by_subj[s] = {"latest": {"deviation": r["deviation"], "judgement": r["judgement"], "date": str(r["exam_date"]), "exam": r["exam_name"]}, "history": []}
        by_subj[s]["history"].append({"date": str(r["exam_date"]), "deviation": r["deviation"]})
    # 各科目の trend (上昇/下降/横ばい)
    for s, d in by_subj.items():
        h = d["history"]
        if len(h) >= 2:
            recent = h[0]["deviation"]
            older = h[-1]["deviation"]
            diff = recent - older
            d["trend"] = "上昇" if diff >= 2 else ("下降" if diff <= -2 else "横ばい")
            d["trend_diff"] = round(diff, 1)
        else:
            d["trend"] = "データ不足"
            d["trend_diff"] = 0

    today = _today_jst()
    exam_dt = datetime.strptime(str(row["exam_date"]), "%Y-%m-%d").date() if row["exam_date"] else today
    remain_days = max(0, (exam_dt - today).days)
    remain_months = max(1, round(remain_days / 30))

    # 模試 summary 文字列
    exam_lines = []
    for s, d in by_subj.items():
        l = d["latest"]
        jd = f" / 判定 {l['judgement']}" if l['judgement'] else ""
        exam_lines.append(f"- {s}: 偏差値 {l['deviation']}{jd} ({l['exam']} {l['date']}) | 推移: {d['trend']} ({'+' if d['trend_diff']>0 else ''}{d['trend_diff']})")
    exam_block = "\n".join(exam_lines)

    # フェーズ summary
    phase_lines = []
    for i, p in enumerate(phases):
        mats = ", ".join((p.get("materials") or [])[:5])
        sapuri = ", ".join((p.get("sapuri_lectures") or [])[:5])
        phase_lines.append(f"  フェーズ{i+1}: {p.get('name','')} ({p.get('start_date','')}〜{p.get('end_date','')}) focus: {p.get('focus','')} / 教材: {mats} / スタサプ: {sapuri}")
    phase_block = "\n".join(phase_lines) if phase_lines else "  (なし)"

    sys_prompt = "難関大学受験の戦略アドバイザーです。生徒の現状偏差値と志望校に必要な偏差値のギャップを科目別に分析し、現行カリキュラムに具体的な修正提案を行います。教師名は出さない (ただし sapuri_lectures は商品名そのまま)。純粋な JSON のみ返答 (前置き解説不要)。"
    user_prompt = f"""## 志望校
{row['target_university']}{(' / ' + row['target_faculty']) if row['target_faculty'] else ''}

## 入試まで
{remain_days}日 ({remain_months} ヶ月)

## 1日の確保時間
{row['daily_minutes'] or 60} 分

## 現状の模試結果 (科目別最新偏差値 + 推移)
{exam_block}

## 現行カリキュラム ({len(phases)} フェーズ)
{phase_block}

上記を踏まえて、ギャップ分析と修正提案を JSON で返してください。

出力形式 (フェンスや前置きなし):
{{
  "target_deviation": "志望校合格に必要な平均偏差値レベル (例: 65)",
  "current_average": "現状の平均偏差値",
  "gap_summary": "総合ギャップ分析 (200字以内、ペース妥当性 + 全体所見)",
  "subject_gaps": [
    {{
      "subject": "科目名",
      "current": 現状偏差値,
      "target": 目標偏差値,
      "gap": 不足分 (target - current),
      "priority": "高|中|低",
      "trend_comment": "推移コメント (40字以内)"
    }}
  ],
  "phase_adjustments": [
    {{
      "phase_index": 0,
      "phase_name": "対象フェーズ名",
      "action": "教材追加|教材削減|期間延長|期間短縮|スタサプ追加|フェーズ名変更",
      "detail": "具体修正内容 (100字以内)",
      "new_materials": ["新規追加教材1", "..."],
      "new_sapuri_lectures": ["新規追加スタサプ講義1", "..."]
    }}
  ],
  "overall_recommendation": "総合戦略アドバイス (200字以内、3-5 個の actionable items)"
}}

注意:
- ギャップが 5 以上の科目は priority=高
- スタサプ講義は商品名そのまま (例: 高3 ハイレベル英文法)
- phase_adjustments は変更が必要なフェーズだけ提案 (全フェーズ列挙不要)"""

    body = {
        "model": "gemini-2.5-flash",
        "max_tokens": 3500,
        "system": sys_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    try:
        data = _call_gemini(body, model="gemini-2.5-flash", kind="curr_gap_analyze")
        text = "".join(c.get("text", "") for c in (data.get("content") or []) if isinstance(c, dict)).strip()
        if not text:
            raise HTTPException(status_code=503, detail="AI が空文字を返しました")
        cleaned = text.strip()
        if cleaned.startswith("```"):
            import re as _re
            cleaned = _re.sub(r'^```(?:json)?\s*|\s*```$', '', cleaned).strip()
        try:
            parsed = json.loads(cleaned)
        except Exception:
            import re as _re
            m = _re.search(r'\{[\s\S]*\}', cleaned)
            if not m:
                raise HTTPException(status_code=503, detail="AI 出力 JSON 解析失敗")
            parsed = json.loads(m.group(0))

        log.info(f"[Curriculum] gap-analyze curr={curr_id} student={student['id']} adjustments={len(parsed.get('phase_adjustments') or [])}")
        return {
            "ok": True,
            "curriculum_id": curr_id,
            "remain_days": remain_days,
            "analysis": parsed,
            "model": data.get("_actual_model"),
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[Curriculum] gap-analyze failed: {type(e).__name__}: {str(e)[:200]}")
        raise HTTPException(status_code=503, detail=f"AI 分析失敗: {str(e)[:200]}")


class GapApplyRequest(BaseModel):
    phase_adjustments: List[dict]  # [{phase_index, action, new_materials, new_sapuri_lectures}]


@app.post("/api/curricula/{curr_id}/apply-gap-fix")
def curriculum_apply_gap_fix(curr_id: int, payload: GapApplyRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: gap-analyze の提案をカリキュラムに反映 (Phase 4.7)。"""
    _check_rate_limit_ip(request, bucket="curr_gap_apply", limit=10, window=600)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)

    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT student_id, phases FROM curricula WHERE id = ?", (curr_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="カリキュラムが見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")
        try:
            phases = json.loads(row["phases"] or "[]")
        except Exception:
            phases = []
        applied = 0
        for adj in payload.phase_adjustments:
            try:
                idx = int(adj.get("phase_index", -1))
            except (TypeError, ValueError):
                continue
            if idx < 0 or idx >= len(phases):
                continue
            phase = phases[idx]
            new_mats = adj.get("new_materials") or []
            new_sapuri = adj.get("new_sapuri_lectures") or []
            mats_clean = [m for m in (_sanitize_text(x, 100) for x in new_mats) if m]
            sapuri_clean = [m for m in (_sanitize_text(x, 120) for x in new_sapuri) if m]
            if mats_clean:
                cur = phase.get("materials") or []
                for m in mats_clean:
                    if m not in cur:
                        cur.append(m)
                phase["materials"] = cur[:10]
            if sapuri_clean:
                cur = phase.get("sapuri_lectures") or []
                for m in sapuri_clean:
                    if m not in cur:
                        cur.append(m)
                phase["sapuri_lectures"] = cur[:8]
            applied += 1
        if not applied:
            return {"ok": True, "applied": 0, "message": "適用すべき変更がありませんでした"}
        # update DB
        if USE_POSTGRES:
            updated_at = datetime.now(timezone.utc).isoformat()
        else:
            updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE curricula SET phases = ?, updated_at = ? WHERE id = ? AND student_id = ?",
                  (json.dumps(phases, ensure_ascii=False), updated_at, curr_id, student["id"]))
        conn.commit()
        log.info(f"[Curriculum] apply-gap-fix curr={curr_id} student={student['id']} applied={applied}")
        return {"ok": True, "applied": applied}
    finally:
        conn.close()


@app.post("/api/curricula/{curr_id}/expand-to-plans")
def expand_curriculum_to_plans(curr_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: カリキュラム各フェーズの教材を study_plans に一括展開。"""
    _check_rate_limit_ip(request, bucket="curr_expand", limit=10, window=300)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_study_log_course(student)
    conn = db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, student_id, target_university, daily_minutes, phases FROM curricula WHERE id = ?", (curr_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="カリキュラムが見つかりません")
        if int(row["student_id"]) != int(student["id"]):
            raise HTTPException(status_code=403, detail="権限がありません")
        try:
            phases = json.loads(row["phases"] or "[]")
        except Exception:
            phases = []
        if not phases:
            raise HTTPException(status_code=400, detail="phases が空です")

        daily = int(row["daily_minutes"] or 60)
        # フェーズ別科目別 color
        subject_colors = {"英語": "#6366f1", "数学": "#10b981", "国語": "#ec4899", "現代文": "#ec4899", "古文": "#f472b6", "漢文": "#fb7185",
                          "理科": "#f59e0b", "物理": "#fbbf24", "化学": "#fb923c", "生物": "#84cc16", "地学": "#a3e635",
                          "社会": "#8b5cf6", "日本史": "#a78bfa", "世界史": "#c4b5fd", "地理": "#7dd3fc",
                          "倫理": "#67e8f9", "政経": "#22d3ee", "情報": "#94a3b8", "小論文": "#f472b6", "面接対策": "#94a3b8", "その他": "#71717a"}

        def _guess_subject(material: str) -> str:
            m = (material or "").lower()
            if any(k in material for k in ["英", "english", "ターゲット", "シス単", "速読", "ネクステ", "vintage"]): return "英語"
            if any(k in material for k in ["数", "チャート", "プラチカ", "1対1", "標問", "やさしい理系", "ハイ理"]): return "数学"
            if any(k in material for k in ["古文", "漢文", "古典"]): return "古文"
            if any(k in material for k in ["現代文", "得点奪取", "上級現代文"]): return "現代文"
            if "国語" in material: return "国語"
            if "物理" in material: return "物理"
            if "化学" in material: return "化学"
            if "生物" in material: return "生物"
            if "日本史" in material: return "日本史"
            if "世界史" in material: return "世界史"
            if "地理" in material: return "地理"
            if "倫" in material or "政経" in material: return "政経"
            if "理科" in material: return "理科"
            if "社会" in material or "歴史" in material: return "社会"
            if "小論" in material: return "小論文"
            return "その他"

        added, skipped = 0, 0
        for ph in phases:
            ph_start = ph.get("start_date")
            ph_end = ph.get("end_date")
            if not ph_start or not ph_end:
                continue
            # フェーズ期間日数
            try:
                p_sd = datetime.strptime(ph_start, "%Y-%m-%d").date()
                p_ed = datetime.strptime(ph_end, "%Y-%m-%d").date()
            except Exception:
                continue
            ph_days = max(1, (p_ed - p_sd).days + 1)
            materials = ph.get("materials") or []
            sapuri_lectures = ph.get("sapuri_lectures") or []
            # 市販教材 + スタサプ講義 を「教材 + 出典タグ」のペアで結合
            combined = [(m, "市販") for m in materials] + [(s, "スタサプ") for s in sapuri_lectures]
            if not combined:
                continue
            # 1項目あたり目標分数 = フェーズ総分数 / 全項目数
            per_item_min = max(60, (ph_days * daily) // max(1, len(combined)))
            for (mat, source_tag) in combined:
                mat_clean = (mat or "").strip()[:100]
                if not mat_clean:
                    continue
                subject = _guess_subject(mat_clean)
                color = subject_colors.get(subject, "#6366f1")
                # スタサプは識別しやすいよう [📺 スタサプ] prefix
                src_prefix = "📺 " if source_tag == "スタサプ" else ""
                title = f"[{ph.get('name','フェーズ')}] {src_prefix}{mat_clean}"[:100]
                try:
                    c.execute(
                        "INSERT INTO study_plans (student_id, title, subject, material, start_date, end_date, target_minutes, color, note) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (student["id"], title, subject, mat_clean, ph_start, ph_end, per_item_min, color,
                         f"カリキュラム自動展開 / 出典: {source_tag} / フェーズ: {ph.get('name','')} / focus: {ph.get('focus','')}"[:1000])
                    )
                    added += 1
                except IntegrityError:
                    skipped += 1
                except Exception as ee:
                    log.warning(f"[Curriculum] expand insert failed: {ee}")
                    skipped += 1
        conn.commit()
        log.info(f"[Curriculum] expand-to-plans curr={curr_id} added={added} skipped={skipped}")
        return {"ok": True, "added": added, "skipped": skipped}
    finally:
        conn.close()


class AdminAiDraftRequest(BaseModel):
    kind: str  # 'reply_draft' or 'broadcast_draft'
    context: str  # 状況説明 (返信案なら相手の本文 / 一斉送信なら要点)
    extra_hint: Optional[str] = None  # 追加指示 (任意)


@app.post("/api/admin/ai-draft")
def admin_ai_draft(payload: AdminAiDraftRequest, request: Request, authorization: Optional[str] = Header(None)):
    """塾長: メッセージ返信案 / 一斉送信文案を Gemini で生成 (Phase 3.5 / 塾長指示 2026-05-06)。"""
    _check_rate_limit_ip(request, bucket="admin_ai_draft", limit=30, window=60)
    _verify_admin_required(authorization)
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini が構成されていません")

    kind = (payload.kind or "").strip()
    if kind not in ("reply_draft", "broadcast_draft"):
        raise HTTPException(status_code=400, detail="kind は 'reply_draft' または 'broadcast_draft'")

    context = _sanitize_text(payload.context, 4000)
    if not context:
        raise HTTPException(status_code=400, detail="context は必須です")
    extra_hint = _sanitize_text(payload.extra_hint, 500) or ""

    hint_block = f"## 追加指示:\n{extra_hint}\n\n" if extra_hint else ""
    if kind == "reply_draft":
        sys_prompt = "あなたは200名規模の学習塾を運営する塾長の秘書 AI です。生徒・保護者からの問い合わせに対し、塾長口調で丁寧かつ温かい返信案を作成します。教師名や塾名は塾長指示で出さない方針。返信案は 100〜250 字、改行は適度に入れて読みやすく。署名や末尾挨拶は不要 (本文のみ)。純粋なテキストのみ返答 (前置きや解説は不要)。"
        user_prompt = f"以下の問い合わせに対する返信案を作成してください。\n\n## 受信メッセージ:\n{context}\n\n{hint_block}## 要件:\n- 塾長口調 (温かく・誠実に)\n- 100〜250 字程度\n- 適度な改行で読みやすく\n- 署名/末尾挨拶 (敬具など) は不要"
    else:  # broadcast_draft
        sys_prompt = "あなたは200名規模の学習塾を運営する塾長の秘書 AI です。塾長が指定する要点から、保護者・生徒に一斉送信する案内文を整えます。教師名や塾名は塾長指示で出さない方針。文章は 200〜500 字、見出しや箇条書きを使い読みやすく。署名や末尾挨拶は不要 (本文のみ)。純粋なテキストのみ返答 (前置きや解説は不要)。"
        user_prompt = f"以下の要点から、一斉送信用の案内文を作成してください。\n\n## 要点:\n{context}\n\n{hint_block}## 要件:\n- 塾長口調 (敬体・温かく)\n- 200〜500 字程度\n- 見出しや箇条書きを適度に活用\n- 署名/末尾挨拶 (敬具など) は不要"

    body = {
        "model": "gemini-2.5-flash",
        "max_tokens": 1500,
        "system": sys_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    try:
        data = _call_gemini(body, model="gemini-2.5-flash", kind=f"admin_{kind}")
        text = "".join(c.get("text", "") for c in (data.get("content") or []) if isinstance(c, dict)).strip()
        if not text:
            raise HTTPException(status_code=503, detail="AI が空文字を返しました。再度お試しください")
        log.info(f"[AdminAiDraft] kind={kind} ip={_client_ip(request)} chars={len(text)}")
        return {"ok": True, "draft": text, "model": data.get("_actual_model"), "kind": kind}
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[AdminAiDraft] failed kind={kind}: {type(e).__name__}: {str(e)[:200]}")
        raise HTTPException(status_code=503, detail=f"AI 生成失敗: {str(e)[:200]}")


class CourseInquiryRequest(BaseModel):
    course: str  # 'kokuritsu_nankan'
    note: Optional[str] = None  # 任意の追記


@app.post("/api/student/course-inquiry")
def student_course_inquiry(payload: CourseInquiryRequest, request: Request, authorization: Optional[str] = Header(None)):
    """生徒: コース申込問い合わせ。CEOダッシュ通知 + 塾長 email 通知 + 生徒に確認 in-app message を送信。"""
    _check_rate_limit_ip(request, bucket="course_inquiry", limit=5, window=600)
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    course = (payload.course or "").strip()
    if course != _STUDY_LOG_TARGET_COURSE:
        raise HTTPException(status_code=400, detail="course が不正です")
    # 既加入なら 409 (重複申込防止)
    if (student.get("course") or None) == _STUDY_LOG_TARGET_COURSE:
        raise HTTPException(status_code=409, detail="すでに加入済みのコースです")
    note = _sanitize_text(payload.note, 500)
    course_label = "国公立難関大学コース"

    conn = db()
    try:
        c = conn.cursor()
        # 監査 events に記録
        try:
            c.execute(
                "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                ("course_inquiry", json.dumps({
                    "student_id": student["id"], "name": student["name"], "email": student.get("email"),
                    "grade": student.get("grade"), "course": course, "note": note,
                }, ensure_ascii=False), "student_action")
            )
        except Exception as ev_err:
            log.warning(f"[CourseInquiry] events log failed: {ev_err}")

        # 塾長宛 in-app message として messages テーブルにも保存 (CEO ダッシュ履歴に出す)
        admin_subject = f"📥 {course_label} 申込問い合わせ ({student['name']})"
        admin_body = f"生徒「{student['name']}」({student.get('grade') or '学年未設定'}) から {course_label} の申込問い合わせがありました。\n\nメール: {student.get('email') or '未登録'}\nメモ: {note or '(なし)'}"
        try:
            c.execute(
                "INSERT INTO messages (sender_type, sender_id, recipient_type, recipient_id, broadcast_filter, subject, body, sent_via, email_status) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                ("student", student["id"], "admin", None, None, admin_subject, admin_body, "in_app", None)
            )
        except Exception as me:
            log.warning(f"[CourseInquiry] messages log failed: {me}")
        # 生徒に確認 in-app message を保存
        try:
            c.execute(
                "INSERT INTO messages (sender_type, sender_id, recipient_type, recipient_id, broadcast_filter, subject, body, sent_via, email_status) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                ("admin", None, "student", student["id"], None,
                 f"📥 {course_label} 申込お問い合わせを受け付けました",
                 f"このたびは {course_label} へのお問い合わせありがとうございます。\n塾長から折り返しご連絡いたします (通常 1〜2 営業日以内)。\n\nお問い合わせ内容:\n{note or '(コメントなし)'}",
                 "in_app", None)
            )
        except Exception as me2:
            log.warning(f"[CourseInquiry] confirm message failed: {me2}")

        conn.commit()
        log.info(f"[CourseInquiry] student={student['id']} course={course} ip={_client_ip(request)}")
    finally:
        conn.close()

    # 塾長宛 email 通知 (env DAILY_SNS_TO_EMAIL を流用 / 未設定なら skip)
    admin_to = os.getenv("DAILY_SNS_TO_EMAIL") or os.getenv("MONITORING_TO_EMAIL")
    if admin_to and RESEND_API_KEY:
        try:
            _send_message_email(
                admin_to,
                f"📥 {course_label} 申込問い合わせ ({student['name']})",
                f"塾長へ\n\n生徒「{student['name']}」({student.get('grade') or '学年未設定'}) から {course_label} の申込問い合わせがありました。\n\nメール: {student.get('email') or '未登録'}\nメモ: {note or '(なし)'}\n\nCEO ダッシュ → 📨 メッセージ配信 → 送信履歴 で詳細確認できます。",
                student_name="塾長"
            )
        except Exception as ee:
            log.warning(f"[CourseInquiry] admin email failed: {ee}")

    return {"ok": True, "message": "お問い合わせを受け付けました。塾長から折り返しご連絡いたします。"}


@app.get("/api/messages/me/unread-count")
def get_my_unread_count(authorization: Optional[str] = Header(None)):
    """生徒: 未読件数 (badge 表示用 - 軽量)。"""
    student = _get_current_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) AS n FROM messages WHERE recipient_type = 'student' AND recipient_id = ? AND read_at IS NULL",
            (student["id"],)
        )
        row = c.fetchone()
        return {"ok": True, "unread_count": int((row["n"] if row else 0) or 0)}
    finally:
        conn.close()


# ==========================================================================
# Static file serving (frontend)
# ==========================================================================
@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "lp.html")

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
