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
# DB_PATH は Railway Volume にマウントされたディレクトリを env で指定する。
# 未設定時はローカル開発用に server/data.db を使用（Railway の ephemeral FS では
# 再起動で消えるため本番では必ず DB_PATH=/app/data/data.db 等を設定すること）。
DB_PATH = pathlib.Path(os.getenv("DB_PATH", str(ROOT / "data.db")))
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
# Database Setup (SQLite)
# ==========================================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        stripe_payment_intent TEXT,
        amount INTEGER,
        status TEXT,
        paid_at TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    );
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        channel TEXT,
        template TEXT,
        payload TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        success INTEGER DEFAULT 0,
        error TEXT
    );
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
    """)
    conn.commit()
    conn.close()
init_db()

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row) if row else None

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
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM students WHERE status='paid'")
    paid = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM students WHERE status='trial'")
    trial = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM payments WHERE status='paid' AND paid_at > datetime('now', '-30 days')")
    mrr = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM notifications WHERE sent_at > datetime('now', '-7 days')")
    notifs = c.fetchone()[0]
    conn.close()
    return {"paid_students": paid, "trial_students": trial, "mrr_yen": mrr, "notifications_7d": notifs}

# ==========================================================================
# Routes: Trial Signup (called from LP form)
# ==========================================================================
@app.post("/api/trial/signup")
def trial_signup(payload: TrialSignup):
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=3)  # 3日間の無料体験
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            """INSERT INTO students (name, email, grade, goal, plan, status, trial_start, trial_end)
               VALUES (?, ?, ?, ?, ?, 'trial', ?, ?)""",
            (payload.name, payload.email, payload.grade, payload.goal,
             payload.plan or "hybrid", now.isoformat(), trial_end.isoformat())
        )
        student_id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
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

    # 通常プラン: 3日間トライアル（¥1,980）+ 月額サブスク（入塾金はトライアル後に追加）
    # トライアル開始時は ¥1,980 のみ即時請求
    line_items = [
        {"price": price_id, "quantity": 1},
        {
            "price_data": {
                "currency": "jpy",
                "product_data": {"name": "3日間トライアル料金（創業記念価格）"},
                "unit_amount": FOUNDER_TRIAL_PRICE,
            },
            "quantity": 1,
        },
    ]

    # 入塾金はWebhook (checkout.session.completed) で InvoiceItem として
    # 顧客に作成 → トライアル終了後の初回請求書に自動的に乗る。
    # （Stripe Checkout の subscription_data は add_invoice_items 非対応）
    needs_enrollment_fee = payload.plan not in ENROLLMENT_FEE_EXEMPT
    subscription_data = {
        "trial_period_days": 3,
        "trial_settings": {"end_behavior": {"missing_payment_method": "cancel"}},
        "metadata": {
            "plan": payload.plan,
            "student_id": str(payload.student_id or ""),
            "max_students": str(max_students),
            "founder": "1",
            "needs_enrollment_fee": "1" if needs_enrollment_fee else "0",
        }
    }

    session_kwargs = {
        "mode": "subscription",
        "payment_method_types": ["card"],
        "line_items": line_items,
        "customer_email": payload.email,
        "success_url": f"{BASE_URL}/checkout-success.html?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{BASE_URL}/checkout-cancel.html",
        "subscription_data": subscription_data,
        "metadata": {
            "plan": payload.plan,
            "plan_name": plan_name,
            "student_id": str(payload.student_id or ""),
            "max_students": str(max_students),
            "founder_trial": "true",
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
    """第1期生の残り枠をカウント"""
    conn = db()
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM students WHERE plan IN ('ai', 'hybrid', 'intensive') AND status='paid'")
        paid = c.fetchone()[0]
    except Exception:
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
        except sqlite3.IntegrityError:
            conn.close()
            log.info(f"Stripe webhook duplicate ignored: id={event_id}, type={event.get('type')}")
            return {"received": True, "duplicate": True}
        conn.close()

    log.info(f"Stripe webhook: {event['type']} id={event_id}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {}) or {}
        plan = meta.get("plan")
        student_id = meta.get("student_id")
        max_students = meta.get("max_students", "1")
        conn = db()
        c = conn.cursor()
        # 生徒が既に存在する場合は更新、なければ新規作成
        if student_id and student_id != "":
            c.execute(
                """UPDATE students SET status='paid', stripe_customer_id=?, stripe_subscription_id=?,
                       paid_since=CURRENT_TIMESTAMP, plan=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (session.get("customer"), session.get("subscription"), plan, student_id)
            )
        else:
            # 匿名チェックアウトの場合は email で紐付け
            email = session.get("customer_details", {}).get("email") or session.get("customer_email")
            if email:
                c.execute("SELECT id FROM students WHERE email=?", (email,))
                row = c.fetchone()
                if row:
                    c.execute(
                        """UPDATE students SET status='paid', stripe_customer_id=?, stripe_subscription_id=?,
                               paid_since=CURRENT_TIMESTAMP, plan=?, updated_at=CURRENT_TIMESTAMP
                           WHERE id=?""",
                        (session.get("customer"), session.get("subscription"), plan, row[0])
                    )
                else:
                    c.execute(
                        """INSERT INTO students (name, email, plan, status, stripe_customer_id, stripe_subscription_id, paid_since)
                           VALUES (?, ?, ?, 'paid', ?, ?, CURRENT_TIMESTAMP)""",
                        ("（新規）", email, plan, session.get("customer"), session.get("subscription"))
                    )
        conn.commit()
        conn.close()
        log.info(f"✅ Checkout completed: plan={plan}, customer={session.get('customer')}, max_students={max_students}")

        # 入塾金 (¥10,000) を顧客に InvoiceItem として作成。
        # トライアル終了後の初回月額請求書に自動的に追加される。
        # トライアル中に解約された場合は orphan のまま残り、課金されない (= 解約時無料)。
        if meta.get("needs_enrollment_fee") == "1" and session.get("customer"):
            try:
                s.InvoiceItem.create(
                    customer=session.get("customer"),
                    amount=ENROLLMENT_FEE,
                    currency="jpy",
                    description="入塾金（システム登録費用・初回のみ）",
                    metadata={"plan": plan, "type": "enrollment_fee"},
                )
                log.info(f"✅ Enrollment fee InvoiceItem created: customer={session.get('customer')}, amount={ENROLLMENT_FEE}")
            except Exception as e:
                log.error(f"Failed to create enrollment fee InvoiceItem for customer={session.get('customer')}: {type(e).__name__}: {e}")

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

@app.post("/api/line/push")
def line_push(payload: LinePushRequest):
    if not LINE_CHANNEL_ACCESS_TOKEN:
        log.warning("LINE push called but not configured")
        return {"ok": False, "mock": True, "message": "LINE_CHANNEL_ACCESS_TOKEN未設定"}

    conn = db()
    c = conn.cursor()
    c.execute("SELECT line_user_id, name FROM students WHERE id = ?", (payload.student_id,))
    row = c.fetchone()
    if not row or not row["line_user_id"]:
        raise HTTPException(status_code=404, detail="Student or LINE user ID not found")

    tmpl_fn = LINE_TEMPLATES.get(payload.template)
    if not tmpl_fn:
        raise HTTPException(status_code=400, detail=f"Unknown template: {payload.template}")

    params = {**(payload.params or {}), "name": row["name"]}
    message = tmpl_fn(params)

    import urllib.request
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        },
        data=json.dumps({"to": row["line_user_id"], "messages": [message]}).encode("utf-8")
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            success = resp.status == 200
    except Exception as e:
        log.error(f"LINE push failed: {e}")
        success = False

    c.execute(
        """INSERT INTO notifications (student_id, channel, template, payload, success)
           VALUES (?, 'line', ?, ?, ?)""",
        (payload.student_id, payload.template, json.dumps(params, ensure_ascii=False), 1 if success else 0)
    )
    conn.commit()
    conn.close()
    return {"ok": success}

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
@app.post("/api/cron/weekly-reports")
def cron_weekly_reports(x_cron_secret: str = Header(None)):
    """毎週日曜20時に外部cronから呼び出し"""
    if not CRON_SECRET:
        log.error("CRON_SECRET not configured; refusing cron request")
        raise HTTPException(status_code=503, detail="Cron not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, line_user_id FROM students WHERE status IN ('trial', 'paid') AND line_user_id IS NOT NULL")
    sent = 0
    for row in c.fetchall():
        try:
            line_push(LinePushRequest(
                student_id=row["id"],
                template="weekly_report",
                params={"hours": 12.5, "accuracy": 78, "questions": 47, "url": f"{BASE_URL}/mypage.html"}
            ))
            sent += 1
        except Exception as e:
            log.error(f"Weekly report failed for {row['id']}: {e}")
    conn.close()
    return {"sent": sent}

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
        # トライアル期限切れチェック
        trial_end_str = row["trial_end"]
        if trial_end_str:
            try:
                te = datetime.fromisoformat(trial_end_str.replace("Z", "+00:00"))
                if te.tzinfo is None:
                    te = te.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > te:
                    raise HTTPException(status_code=403, detail="トライアル期間が終了しています。契約を継続してください。")
            except ValueError:
                pass
        return dict(row)
    raise HTTPException(status_code=403, detail=f"契約状態が無効です (status={status})")


def _check_ai_budget(student_id: int) -> None:
    """その生徒が直近24hで消費したAIトークンが AI_DAILY_TOKEN_BUDGET を超えていないか確認。"""
    conn = db()
    c = conn.cursor()
    c.execute(
        """SELECT props FROM events
           WHERE session_id = ?
             AND name LIKE 'ai_call_%'
             AND datetime(created_at) > datetime('now', '-1 day')""",
        (str(student_id),),
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

    # 2) student_id 必須・DBで有効性確認
    _verify_student_active(payload.student_id)

    # 3) 1日あたりトークン予算チェック
    _check_ai_budget(payload.student_id)

    # 4) モデルとトークン数の上限ガード（異常値を弾く）
    max_tokens = max(1, min(int(payload.max_tokens or 2000), 8000))

    import urllib.request

    body = {
        "model": payload.model,
        "max_tokens": max_tokens,
        "system": payload.system,
        "messages": payload.messages,
    }
    if payload.thinking:
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
def log_activity(payload: dict):
    """生徒の活動を記録（ログイン、質問、クエスト完了等）"""
    student_id = payload.get("student_id")
    activity_type = payload.get("type", "unknown")
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id required")
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

    conn = db()
    c = conn.cursor()
    # Find students inactive for N days
    c.execute(
        """SELECT id, name, line_user_id, status,
                  (julianday('now') - julianday(updated_at)) as days_inactive
           FROM students
           WHERE status IN ('trial', 'paid')
             AND julianday('now') - julianday(updated_at) >= ?""",
        (payload.threshold_days,)
    )
    inactive = c.fetchall()
    conn.close()

    sent_count = 0
    for row in inactive:
        days = int(row["days_inactive"])
        level = 3 if days >= 7 else 2 if days >= 5 else 1
        try:
            if row["line_user_id"]:
                template = "streak_reminder" if level == 1 else "trial_ending"
                line_push(LinePushRequest(
                    student_id=row["id"],
                    template=template,
                    params={"days_inactive": days, "streak": 0}
                ))
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
def save_problem(payload: dict):
    """生成した問題をDBに保存（後で再利用可能）"""
    conn = db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
           VALUES (?, ?, ?, ?, ?, ?)""",
        (payload.get("subject"), payload.get("topic"), payload.get("difficulty"),
         payload.get("format"), payload.get("content"), payload.get("student_id"))
    )
    conn.commit()
    new_id = c.lastrowid
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
def track_event(event: EventTrack):
    conn = db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
        (event.name, json.dumps(event.props, ensure_ascii=False), event.session_id)
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
