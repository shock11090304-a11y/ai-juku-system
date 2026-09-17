"""Vercel Function: Stripe Webhook 受信

Endpoint: POST /payment/api/stripe-webhook
  (vercel.json の rewrites で /api/stripe-webhook に流れる)

Stripe Dashboard 設定:
  Developers → Webhooks → Add endpoint
    URL:    https://www.trillion-ai-juku.com/payment/api/stripe-webhook
    Events: checkout.session.completed
            invoice.payment_failed
            invoice.payment_succeeded
            customer.subscription.deleted
            checkout.session.async_payment_succeeded (🆕 2026-09-16 月額講座・カード以外の入金確定。購読は任意)
            payment_intent.succeeded   (🆕 v2 月末バッチ請求用)
            payment_intent.payment_failed   (🆕 v2 バッチ請求失敗時)
            payment_intent.canceled    (🆕 2026-07-02 塾長が Dashboard で要確認 PI を
                                        キャンセルした時の掃除用。★Dashboard の webhook
                                        endpoint にこのイベントの購読追加が必要。
                                        ★順序: デプロイ反映確認 → 購読追加 の順を厳守
                                        — 先に購読すると旧コードが webhook:seen に 24h
                                        焼き付け、Resend も duplicate 扱いになる)

Env:
  STRIPE_WEBHOOK_SECRET   Stripe webhook signing secret (whsec_...)
  KV_REST_API_URL         Upstash Redis REST URL (Vercel KV 自動付与)
  KV_REST_API_TOKEN       Upstash Redis REST token

機能:
  1. checkout.session.completed → KV pending → completed に更新、registrations index に追加
  2. invoice.payment_failed → KV failures index に追加 (塾長ダッシュで一覧表示用)
  3. customer.subscription.deleted → KV cancellations index に追加
  4. その他のイベントは ack のみして無視 (安全)
  5. 🆕 2026-09-16 月額講座 (英文解釈/英文法/共通テスト対策・Stripe 支払いリンク・metadata.system=juku-payment-course)
     の checkout.session.completed → 受講案内メールを Resend で自動送信 (KV course:welcome:* に送信記録)
     Env (追加): RESEND_API_KEY / FROM_EMAIL (mail-send.py と共通) / COURSE_REPLY_TO (任意・既定 info@…)
                 COURSE_NOTIFY_EMAIL (塾長への申込通知。案内メール失敗に気づける唯一の経路なので実質必須)
                 COURSE_WELCOME_ENABLED=0 で講座の案内メールだけ止められる (月謝の一斉メールには影響しない)
     講座の invoice / subscription イベント (毎月の更新・失敗・解約) は月謝の台帳に混ぜず skip する

依存: 標準ライブラリのみ
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import sys
import time
import hmac
import hashlib
import urllib.request
import urllib.error


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


def _redis_safe(*args):
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


def _verify_signature(raw_payload: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
    """Stripe-Signature ヘッダ: t=1234,v1=hex,v1=hex,...
    timing-safe HMAC-SHA256 検証 + timestamp tolerance (default 5min)
    """
    if not sig_header or not secret:
        return False
    try:
        items = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
    except Exception:
        return False
    timestamp = items.get("t")
    if not timestamp:
        return False
    # v1 が複数ある場合は最初の v1
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


def _stripe_get(secret_key, path):
    """Stripe GET API helper (SetupIntent 取得用)"""
    if not secret_key:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.stripe.com/v1/{path}",
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Stripe-Version": "2024-06-20",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"stripe GET {path} error: {e}")
        return None


# ===== 🆕 2026-09-16 月額講座 (Stripe 支払いリンク・定期) の受講案内メール =====
# 申込書 (入塾書類/course.html) → Stripe 支払いリンク (metadata.system=juku-payment-course, metadata.combo=
# "bunpo+kaishaku" のように講座コードを "+" で連結) → 決済完了でここに届く。本体 (server/main.py) の webhook は
# juku-payment 前方一致で skip するので、講座の決済を扱うのはこの関数だけ。
# ★件名・本文は塾長が書き換えてよい。使える差し込み:
#   {student_name} {courses} {amount} {payment_line} {first_monday} {first_note} {receipt_no} {contact} {portal} {line_url}
#   ({ } を文中に書くと format が失敗して status=failed になる。波括弧は差し込み以外に使わない)
# ★講座変更 (一部解約・追加) を Stripe ダッシュボードで行うときは「日割りしない」を選ぶこと。本文で「日割りなし」と約束している。
RESEND_USER_AGENT = "ai-juku/1.0 (+https://trillion-ai-juku.com)"
COURSE_SYSTEM_TAG = "juku-payment-course"
COURSE_NAMES = {"kaishaku": "英文解釈講座", "bunpo": "英文法講座", "kyotsu": "共通テスト対策講座"}
COURSE_CONTACT_DEFAULT = "info@trillion-ai-juku.com"   # 公開済み (legal.html) の窓口。COURSE_REPLY_TO で上書き可
COURSE_PORTAL_URL_DEFAULT = "https://trillion-ai-juku.com/course-videos.html"   # 受講者専用の視聴ページ (本体リポジトリ course-videos.html)
COURSE_LINE_URL_DEFAULT = "https://lin.ee/ZHlrRjh"   # 公式 LINE の友だち追加 URL (env COURSE_LINE_URL で上書き可)
COURSE_DELIVERY_START_DEFAULT = "2026-10-05"   # 配信開始日 (月曜)。これより前の決済は初回配信がこの日になる (塾長 2026-09-16「10月から配信開始」)。env COURSE_DELIVERY_START で上書き可
COURSE_RECORD_TTL = 365 * 86400   # 受付番号として保護者に案内するので 1 年残す (pi:* / charge:history と同じ)
COURSE_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
COURSE_WELCOME_SUBJECT = "【トリリオン英語塾】受講のご案内（{courses}）"
COURSE_WELCOME_BODY = """{student_name} さん・保護者様

トリリオン英語塾です。
「{courses}」のお申し込みとお支払いを確認いたしました。
これをもって受講確定となります。ありがとうございます。

■ 動画の配信について
・各講座とも 毎週月曜に 2 本ずつ動画を追加します（月 8 本）。
・動画は専用の視聴ページでご覧いただけます。
　{portal}
　（このメールとは別に「視聴ページのログインリンク」のメールも届きます。そのリンクをタップすればそのまま開けます。届かないときは、視聴ページでお支払い時のメールアドレスを入力するとリンクを再送できます。一度ログインすると、同じブラウザでは 30 日間そのまま開けます。ホーム画面に追加しておくと便利です）
・初回の配信は {first_monday} の予定です{first_note}。
・新しい動画を追加したときは、このアドレスあてにお知らせメールが届きます。迷惑メールに入らないよう、このメールの差出人と {contact} を受信許可に設定してください。
・視聴ページは生徒さんご本人が開いていただいて構いません（視聴ページでメールアドレスを入力すると届く「ログインリンク」のメールを、生徒さんに転送してください）。

■ ご質問・ご連絡
・分からない箇所のご質問やご連絡は、公式 LINE でお願いします。
　友だち追加: {line_url}
　生徒さんご本人からのご質問も歓迎です。

■ お支払いについて
・{payment_line}
　（29〜31日にお手続きの場合、その日が無い月は月末日）
・領収書は、決済のたびに Stripe から別のメールで届きます（このメールは領収書ではありません）。
・解約や講座の変更は、次回の決済日の前日までに公式 LINE（またはメール {contact}）へご連絡ください。
　次回分から反映します（日割りの返金はありません）。

■ 受付番号
{receipt_no}
（お問い合わせの際にお知らせいただくと確認が早くなります）

ご不明な点は、公式 LINE またはこのメールへの返信（返信先は {contact}）でご連絡ください。
このメールに心当たりがない場合も、お手数ですが {contact} までご連絡ください。

トリリオン英語塾（Trillion English Academy）
{contact}
"""
COURSE_PAYMENT_LINE_NORMAL = "月額合計 {amount}円（税込）を、毎月同じ日にご登録のカードから自動で決済します。"
COURSE_PAYMENT_LINE_DISCOUNT = "今回のお支払いは {amount}円（税込）です。以降は毎月同じ日に、お選びいただいた講座の月額合計（英文解釈 1,000円、英文法・共通テスト対策 各 1,500円・税込）をご登録のカードから自動で決済します。"
COURSE_NOTIFY_SUBJECT = "[月額講座] 新規申込: {courses} / {student_name}"
COURSE_NOTIFY_SUBJECT_FAILED = "[月額講座] ★案内メール未送信: {courses} / {student_name}"
COURSE_NOTIFY_BODY = """月額講座の決済が完了しました。

講座: {courses}
生徒氏名（決済画面の入力）: {student_name_raw}
お申込者: {purchaser_name}
メール: {email}
月額合計: {amount}円
決済日時 (JST): {paid_at_jst} → 以後 毎月 {billing_day}日 に決済（29〜31日はその日が無い月は月末。解約期限はその前日）
初回配信（保護者に案内済み）: {first_monday}
受付番号 (Checkout Session): {receipt_no}
申込ID（Netlify 通知メールの「申込ID」と一致）: {app_id}
Stripe 顧客: {customer}
Stripe サブスクリプション: {subscription}
案内メール: {welcome_status}
"""


def _resend_send_text(api_key, from_email, to_email, reply_to, subject, text, idempotency_key=""):
    """Resend API で 1 通送る (mail-send.py の _resend_send と同じ形。Vercel の関数は共有モジュールを持てないので複製)。
    idempotency_key を渡すと Resend 側で重複送信を弾く (KV が落ちていて再送が通っても 2 通にならない)。
    timeout は 8 秒: Vercel 関数の既定上限 (10 秒) より短くして、Resend が固まっても KV に失敗を残せるようにする"""
    payload = {"from": from_email, "to": [to_email], "subject": subject, "text": text}
    if reply_to:
        payload["reply_to"] = reply_to
    # User-Agent 必須: Resend 前段の Cloudflare が Python-urllib の既定 UA を 403 (error code 1010) で弾く (2026-09-17 発覚)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": RESEND_USER_AGENT}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key[:256]
    req = urllib.request.Request("https://api.resend.com/emails",
                                 data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _course_jst(ts=None):
    import datetime as _dt
    return _dt.datetime.fromtimestamp(ts if ts is not None else time.time(), _dt.timezone(_dt.timedelta(hours=9)))


def _course_first_monday_date(now_ts=None):
    """初回配信日 (JST の date)。「次の月曜 (当日が月曜でも翌週)」と「配信開始日」の遅い方。"""
    import datetime as _dt
    now = _course_jst(now_ts)
    days = (7 - now.weekday()) % 7 or 7
    d = (now + _dt.timedelta(days=days)).date()
    start_s = (os.environ.get("COURSE_DELIVERY_START", "").strip() or COURSE_DELIVERY_START_DEFAULT)
    try:
        start = _dt.date.fromisoformat(start_s)
        if d < start:
            d = start
    except Exception:
        pass
    return d


def _course_first_monday_jst(now_ts=None):
    """初回配信日を「M月D日（月）」で返す (配信開始日より前の決済は配信開始日)。"""
    d = _course_first_monday_date(now_ts)
    return f"{d.month}月{d.day}日（{'月火水木金土日'[d.weekday()]}）"


def _course_first_note(now_ts=None):
    """初回配信日の補足: 配信開始日で切り上げたなら「10月からの配信開始のため」、そうでなければ「翌週の月曜から」"""
    import datetime as _dt
    now = _course_jst(now_ts)
    days = (7 - now.weekday()) % 7 or 7
    nxt = (now + _dt.timedelta(days=days)).date()
    d = _course_first_monday_date(now_ts)
    if d > nxt:
        return f"（{d.month}月からの配信開始のため。以降は毎週月曜に追加します）"
    return "（お支払いの翌週の月曜から始まります）"


def _course_keys_from_session(obj, secret_key):
    """講座コードの一覧 (アルファベット順)。metadata.combo が正。無ければ明細の price.lookup_key (course_<key>_monthly) から復元"""
    combo = ((obj.get("metadata") or {}).get("combo") or "").strip().replace(" ", "+")
    keys = [k for k in combo.split("+") if k in COURSE_NAMES]
    if keys:
        return sorted(set(keys))
    session_id = obj.get("id", "")
    items = _stripe_get(secret_key, f"checkout/sessions/{session_id}/line_items?limit=20") if (secret_key and session_id) else None
    for li in ((items or {}).get("data") or []):
        lk = ((li.get("price") or {}).get("lookup_key") or "")
        if lk.startswith("course_") and lk.endswith("_monthly"):
            k = lk[len("course_"):-len("_monthly")]
            if k in COURSE_NAMES:
                keys.append(k)
    return sorted(set(keys))


def _course_save(session_id, record):
    _redis_safe("SET", f"course:welcome:{session_id}", json.dumps(record, ensure_ascii=False), "EX", str(COURSE_RECORD_TTL))


def _handle_course_checkout(obj):
    """月額講座の決済完了 → 受講案内メール。例外は握って KV に記録する (Stripe には呼び出し側が 200 を返す)。
    二重送信ガード: course:welcome:<session_id> を SET NX (Stripe の再送・同一セッションの別イベントでも 1 通)。
    ただし前回が "sending" のまま 10 分以上経っている (Resend が固まって関数が時間切れになった) ときはやり直す。
    KV に記録できないときは送信を優先する (Resend の Idempotency-Key が 2 通目を弾く)。"""
    session_id = obj.get("id", "")
    if obj.get("livemode") is False:
        _log(f"webhook course: test-mode session {session_id} — no mail")
        return
    details = obj.get("customer_details") or {}
    email = (obj.get("customer_email") or details.get("email") or "").strip()
    purchaser_name = (details.get("name") or "").strip()
    student_name_raw = ""
    for cf in (obj.get("custom_fields") or []):
        if cf.get("key") == "student_name":
            student_name_raw = ((cf.get("text") or {}).get("value") or "").strip()
    amount = obj.get("amount_total") or 0  # JPY は最小単位=円
    client_ref = obj.get("client_reference_id") or ""
    customer = obj.get("customer") or ""
    now = int(time.time())
    # 決済日 (次回決済日の案内・初回配信日の起点): Stripe の再送が数時間〜数日遅れても狂わないよう、サブスクの請求起点
    # (billing_cycle_anchor = 実際の決済時刻) を最優先、取れなければ session.created、最後に処理時刻
    paid_ts = now
    try:
        _sk = os.environ.get("STRIPE_SECRET_KEY", "").strip()
        _sub = _stripe_get(_sk, f"subscriptions/{obj.get('subscription')}") if (_sk and obj.get("subscription")) else None
        _anchor = int((_sub or {}).get("billing_cycle_anchor") or 0)
        if _anchor:
            paid_ts = _anchor
        elif int(obj.get("created") or 0):
            paid_ts = int(obj.get("created"))
    except Exception:
        paid_ts = now

    if obj.get("payment_status") not in ("paid", "no_payment_required"):   # 100% クーポン等は no_payment_required
        # カード以外 (コンビニ等) は unpaid で届き、後から checkout.session.async_payment_succeeded が来る (HANDLERS に登録済み)
        _log(f"webhook course: session {session_id} not paid yet (payment_status={obj.get('payment_status')}) — no mail")
        return

    # 同一セッションの二重送信ガード
    guard_key = f"course:welcome:{session_id}"
    guard = _redis_safe("SET", guard_key, json.dumps({"status": "sending", "email": email, "at": now}), "NX", "EX", str(COURSE_RECORD_TTL))
    if guard and isinstance(guard, dict) and guard.get("result") != "OK":
        prev = {}
        try:
            got = _redis_safe("GET", guard_key)
            prev = json.loads((got or {}).get("result") or "{}")
        except Exception:
            prev = {}
        if prev.get("status") == "sending" and int(prev.get("at") or 0) < now - 600:
            _log(f"webhook course: session {session_id} stuck in 'sending' since {prev.get('at')} — retrying")
        else:
            _log(f"webhook course: welcome mail already handled for session {session_id} (status={prev.get('status')}) — skip")
            return
    # 先に index へ載せる = 途中で時間切れになっても「sending のまま」が一覧で見える
    _redis_safe("ZADD", "course:welcome:index", str(now), session_id)

    secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    keys = _course_keys_from_session(obj, secret_key)
    courses = "・".join(COURSE_NAMES[k] for k in keys) if keys else "月額講座"
    contact = os.environ.get("COURSE_REPLY_TO", "").strip()
    if not COURSE_EMAIL_RE.match(contact):
        contact = COURSE_CONTACT_DEFAULT
    discount = 0
    try:
        discount = int(((obj.get("total_details") or {}).get("amount_discount")) or 0)
    except Exception:
        discount = 0
    amount_txt = f"{int(amount):,}"
    payment_line = (COURSE_PAYMENT_LINE_DISCOUNT if (int(amount) == 0 or discount > 0) else COURSE_PAYMENT_LINE_NORMAL).format(amount=amount_txt)
    paid_jst = _course_jst(paid_ts)
    app_id = client_ref.rsplit("-sub-", 1)[1] if "-sub-" in client_ref else ""
    vars_ = {
        "student_name": student_name_raw or purchaser_name or "お申込者",
        "student_name_raw": student_name_raw or "(未入力)",
        "purchaser_name": purchaser_name or "-",
        "courses": courses,
        "amount": amount_txt,
        "payment_line": payment_line,
        "first_monday": _course_first_monday_jst(paid_ts),
        "first_note": _course_first_note(paid_ts),
        "receipt_no": session_id,
        "contact": contact,
        "portal": os.environ.get("COURSE_PORTAL_URL", "").strip() or COURSE_PORTAL_URL_DEFAULT,
        "line_url": os.environ.get("COURSE_LINE_URL", "").strip() or COURSE_LINE_URL_DEFAULT,
        "email": email,
        "client_ref": client_ref or "-",
        "app_id": app_id or "★突合キーなし → 氏名・メールで照合",
        "customer": customer or "-",
        "subscription": obj.get("subscription") or "-",
        "paid_at_jst": paid_jst.strftime("%Y-%m-%d %H:%M"),
        "billing_day": str(paid_jst.day),
    }
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    from_raw = os.environ.get("FROM_EMAIL", "noreply@trillion-ai-juku.com").strip() or "noreply@trillion-ai-juku.com"
    from_email = from_raw if "<" in from_raw else f"トリリオン英語塾 <{from_raw}>"   # 受信箱に塾名を出す (mail-send.py と同じ形)
    record = {"status": "", "email": email, "student_name": student_name_raw, "courses": keys, "amount": amount,
              "client_reference_id": client_ref, "customer": customer, "subscription": obj.get("subscription") or "",
              "session_created": obj.get("created") or 0, "paid_at": paid_ts, "at": now, "resend_id": "", "error": ""}
    enabled = os.environ.get("COURSE_WELCOME_ENABLED", "1").strip().lower() not in ("0", "false", "off")
    if not enabled:
        record["status"] = "disabled"
        _log(f"webhook course: welcome mail DISABLED by env COURSE_WELCOME_ENABLED (session={session_id})")
    elif not email:
        record["status"] = "no_email"
        _log(f"webhook course CRITICAL: session {session_id} has no email — welcome mail NOT sent")
    elif not api_key:
        record["status"] = "no_api_key"
        _log(f"webhook course CRITICAL: RESEND_API_KEY missing — welcome mail NOT sent (session={session_id})")
    else:
        try:
            res = _resend_send_text(api_key, from_email, email, contact,
                                    COURSE_WELCOME_SUBJECT.format(**vars_), COURSE_WELCOME_BODY.format(**vars_),
                                    idempotency_key=f"course-welcome/{session_id}")
            record["status"] = "sent"
            record["resend_id"] = (res or {}).get("id", "")
            _log(f"webhook course: welcome mail sent session={session_id} courses={keys} resend_id={record['resend_id']}")
        except Exception as e:
            record["status"] = "failed"
            record["error"] = repr(e)[:300]
            _log(f"webhook course CRITICAL: welcome mail FAILED session={session_id}: {e!r}")
    _course_save(session_id, record)

    # 塾長への通知 (任意・env があるときだけ)。案内メールの成否も載せる = 失敗時は手で送り直せる
    notify_to = os.environ.get("COURSE_NOTIFY_EMAIL", "").strip()
    if notify_to and api_key and COURSE_EMAIL_RE.match(notify_to):
        try:
            ok = record["status"] == "sent"
            vars_["welcome_status"] = "送信済み" if ok else f"★送信失敗 ({record['status']}) — 手動で送ってください"
            subj = (COURSE_NOTIFY_SUBJECT if ok else COURSE_NOTIFY_SUBJECT_FAILED).format(**vars_)
            _resend_send_text(api_key, from_email, notify_to, "", subj, COURSE_NOTIFY_BODY.format(**vars_),
                              idempotency_key=f"course-notify/{session_id}/{record['status']}")
        except Exception as e:
            _log(f"webhook course: owner notify failed: {e!r}")


def _handle_course_async_paid(event):
    """checkout.session.async_payment_succeeded: カード以外 (コンビニ・銀行振込) の入金確定。講座のセッションだけ扱う。
    ★Stripe ダッシュボードの webhook でこのイベントを購読していないと届かない (現状は支払いリンクをカード限定にしているので予備)"""
    obj = event.get("data", {}).get("object", {})
    md = obj.get("metadata") or {}
    if (md.get("system") or "") == COURSE_SYSTEM_TAG:
        _handle_course_checkout(obj)
    elif md.get("first_charge") == "1" and md.get("registration_id"):
        # 入塾の初回決済 (現状カード限定なので届かないはずだが、支払方法を増やしたときの保険)
        _handle_checkout_completed(event)
    else:
        _log("webhook: async_payment_succeeded ignored (not a course / enroll session)")


# ===== 🆕 2026-09-17 入塾申込書からの初回決済 (register-subscribe.py firstCharge=true / mode=payment) =====
# 申込書 (入塾書類/index.html) → Checkout (入塾金+設備費+初月受講料をその場で決済・カード保存) → ここ。
# やること: ① reg:completed を setup 相当 (checkout_mode=setup + payment_method) で書く = 月謝アプリの名簿に載る
#           ② 決済した月の charge:done / charge:history を書く = 月末バッチがその月を skip (二重請求防止)
#           ③ 保護者へ確認メール・塾長へ通知 (Resend)。文面は塾長が書き換えてよい。
# 使える差し込み: {student_name} {parent_name} {grade} {courses} {entry_fee} {facility} {course_fee} {first_total} {monthly_fee}
#   {month_label} {next_month_label} {receipt_no} {app_id} {contact} {line_url} {email} {paid_at_jst} {registration_id} {welcome_status}
#   {zoom_block} (Zoom の ID とパスコード。env ENROLL_ZOOM_ID / ENROLL_ZOOM_PASS から。★リポジトリは公開なので値はコードに書かない。
#                未設定なら「LINE でお知らせします」になる) {app_register_url} (塾生アプリの登録 URL。env ENROLL_APP_REGISTER_URL)
ENROLL_APP_REGISTER_URL_DEFAULT = "https://trillion-ai-juku.com/juku-register.html"
ENROLL_ZOOM_BLOCK = """　ミーティング ID：{zoom_id}
　パスコード：{zoom_pass}"""
ENROLL_ZOOM_BLOCK_UNSET = "　ミーティング ID とパスコードは公式 LINE でお知らせします。"
ENROLL_WELCOME_SUBJECT = "【トリリオン英語塾】ご入塾のお申し込みとお支払いの確認"
ENROLL_WELCOME_BODY = """{parent_name} 様

このたびはトリリオン英語塾へのご入塾をお申し込みいただき、誠にありがとうございます。
{student_name} さんの初回分のお支払いを確認いたしました。

■ 今回お支払いいただいた内容（{month_label}分）
　入塾金（初回のみ）：{entry_fee}円
　設備費：{facility}円
　受講料（初月分・日割りなし）：{course_fee}円
　　{courses}
　合計：{first_total}円（税込）
　※ Stripe からの領収メールも別途届きます。

■ 翌月以降のお支払い
　今回のお支払いに {month_label}分の受講料と設備費は含まれています。
　{next_month_label}分以降は、月額 {monthly_fee}円（設備費＋受講料・税込）を毎月 26 日前後に今回ご登録のカードから自動で引き落とします（翌月分の前払い）。
　※ {next_month_label}分は {month_label} 26 日前後のお引き落としです（この日を過ぎてのご入塾の場合は、塾長より別途ご案内します）。

■ 今後の流れ
　1. 塾生アプリにご登録ください（1 分ほどで終わります）
　　　{app_register_url}
　　　塾休日・授業のアーカイブ・配布プリントのご案内など、授業に関する連絡はすべて塾生アプリで行います。
　2. 公式 LINE を友だち追加してください（急ぎのご連絡用です）
　　　{line_url}
　3. 塾長より、初回授業の日時をご連絡します。

■ 授業について（Zoom）
{zoom_block}
　・授業の 5 分前には入室してください。
　・画面（カメラ）はオン、音声はオフ（ミュート）でご参加ください。

■ カードの変更・コースの変更・退塾
　公式 LINE またはメール（{contact}）へご連絡ください。
　退塾・コース変更は、停止したい月の前月 15 日までにご連絡ください（翌月分から反映・日割りの返金はありません）。

受付番号：{receipt_no}
申込ID：{app_id}

このメールは自動送信です。ご不明な点は {contact} または公式 LINE までお気軽にお問い合わせください。

トリリオン英語塾
"""
ENROLL_NOTIFY_SUBJECT = "【入塾・初回決済】{student_name}（{grade}）{first_total}円 — 名簿登録済み"
ENROLL_NOTIFY_SUBJECT_FAILED = "★要対応【入塾・初回決済】{student_name} — {fail_reason}"
ENROLL_DUPLICATE_SUBJECT = "★要対応【入塾・初回決済 二重】{student_name} — 同じ顧客の 2 件目の決済 ({first_total}円)。返金の確認を"
ENROLL_DUPLICATE_BODY = """同じ Stripe 顧客 ({customer}) に既に名簿登録 ({duplicate_of}) があるのに、入塾申込書から 2 件目の初回決済が完了しました。
申込書を送り直して 2 回支払った可能性が高いです。名簿には追加していません (月額の二重引き落としは起きません)。

生徒: {student_name}（{grade}）／保護者: {parent_name}／メール: {email}
今回の決済額: {first_total}円／受付番号: {receipt_no}／申込ID: {app_id}／決済日時 (JST): {paid_at_jst}

やること: Stripe ダッシュボードで受付番号の決済を確認し、二重なら返金する。既存の登録 ({duplicate_of}) のコース・月額が最新の申込内容と合っているか名簿で確認する。
"""
ENROLL_NOTIFY_BODY = """入塾申込書からの初回カード決済が完了し、月謝アプリの名簿に自動登録しました。

生徒: {student_name}（{grade}）
保護者: {parent_name}
メール: {email}
コース: {courses}
初回決済額: {first_total}円（入塾金 {entry_fee} + 設備費 {facility} + 受講料 {course_fee}）
翌月以降の月額: {monthly_fee}円
決済日時 (JST): {paid_at_jst}
台帳: {month_label}分を「引き落とし済み」として記録 → 月末バッチは {month_label}分を請求しません（{next_month_label}分から請求）
登録ID: {registration_id}
受付番号 (Stripe Checkout): {receipt_no}
申込ID (Netlify 通知メールの「申込ID」と一致): {app_id}
保護者への確認メール: {welcome_status}
{warnings}
確認すること: Netlify の申込通知メールの「金額_初月合計」「コース」がこの決済額・コースと一致しているか（金額はサーバ側のカタログで計算・申込書の入力とは独立）。
次にやること: 初回授業の日時を連絡する（Zoom の ID・パスコードと授業ルールは確認メールに記載済み）。
"""
ENROLL_RECORD_TTL = 365 * 86400


class _RetryLater(Exception):
    """KV に名簿を書けなかった (KV 障害)。Stripe に 500 を返して再送してもらう (最長 3 日)。
    通常の handler 例外は 200 で握るが、入塾の初回決済だけは「決済されたのに名簿に無い」が最悪なので再送に賭ける"""


def _enroll_month_label(ym):
    try:
        return f"{int(ym[:4])}年{int(ym[5:7])}月"
    except Exception:
        return ym


def _enroll_next_month(ym):
    try:
        y, m = int(ym[:4]), int(ym[5:7])
        return f"{y + 1}-01" if m == 12 else f"{y}-{m + 1:02d}"
    except Exception:
        return ym


def _enroll_write_ledger(rid, month, pi_id, first_total, existing, now_ts):
    """決済した月の charge:done (SET NX・60 日) と charge:history (1 年・台帳の恒久記録) を書く。
    done が既にある (Stripe の再送・月末バッチが先に走った) ときは何も書かない。戻り値: 書いたかどうか"""
    done_key = f"charge:done:{rid}:{month}"
    done_val = json.dumps({"payment_intent_id": pi_id, "status": "succeeded", "amount": first_total,
                           "charged_at": now_ts, "source": "enroll-first-charge"}, ensure_ascii=False)
    nx = _redis_safe("SET", done_key, done_val, "NX", "EX", "5184000")
    if nx is None:
        _log(f"webhook enroll CRITICAL: KV error writing charge:done rid={rid} month={month} — ledger NOT written")
        return "error"
    if not (isinstance(nx, dict) and nx.get("result") == "OK"):
        # 自分が前回書いたもの (Stripe の再送・メール前に落ちた再実行) なら異常ではない
        try:
            prev = json.loads(((_redis_safe("GET", done_key) or {}).get("result")) or "{}")
            if prev.get("source") == "enroll-first-charge" and prev.get("payment_intent_id") == pi_id:
                return "written"
        except Exception:
            pass
        _log(f"webhook enroll: charge:done already exists rid={rid} month={month} — ledger untouched")
        return "exists"
    hist = {
        "payment_intent_id": pi_id,
        "registration_id": rid,
        "month": month,
        "amount": first_total,
        "student_name": existing.get("studentName") or existing.get("student_name") or "",
        "email": existing.get("email", ""),
        "phone": existing.get("phone", ""),
        "charged_at": now_ts,
        "status": "succeeded",
        "source": "enroll-first-charge",
        "note": "入塾時の初回決済（入塾金＋設備費＋初月受講料）。入塾金を含むため月額より大きい",
        "entry_fee": int(existing.get("entry_fee") or 0),
        "monthly_fee": int(existing.get("monthly_fee") or 0),
    }
    hj = json.dumps(hist, ensure_ascii=False)
    _redis_safe("ZADD", "charge:history:index", str(now_ts), f"{rid}:{month}")
    _redis_safe("SET", f"charge:history:{rid}:{month}", hj, "EX", "31536000")
    _redis_safe("RPUSH", f"charge:history:audit:{rid}:{month}", hj)
    _redis_safe("EXPIRE", f"charge:history:audit:{rid}:{month}", "31536000")
    return "written"


def _enroll_next_month_batch_ran(next_month):
    """翌月分の月末バッチ (前倒し請求) が既に実行済みか = charge:history:index に「:翌月」のエントリがあるか。
    実行済みなら、この生徒の翌月分は誰も請求しない (当月は初回決済で済み・翌月分のバッチはもう終わっている) ので塾長に個別請求を促す"""
    try:
        # score は書込時刻。直近 45 日に絞る (index は月ごとに全生徒分が増える無限 ZSET)
        since = str(int(time.time()) - 45 * 86400)
        zr = _redis_safe("ZRANGE", "charge:history:index", since, "+inf", "BYSCORE")
        members = [m for m in ((zr or {}).get("result") or []) if isinstance(m, str) and m.endswith(f":{next_month}")]
        if not members:
            return False
        # 翌月のエントリが「月末バッチ」由来かを確認する (個別請求 1 件・手動記帳では「実行済み」にしない)
        keys = [f"charge:history:{m}" for m in members[:300]]
        mg = _redis_safe("MGET", *keys)
        for raw in ((mg or {}).get("result") or []):
            try:
                rec = json.loads(raw) if isinstance(raw, str) else None
            except Exception:
                rec = None
            if isinstance(rec, dict) and str(rec.get("source") or "").startswith("month-end-batch"):
                return True
        return False
    except Exception:
        return False


def _enroll_send_mails(obj, record, month, ledger_state, warnings=None):
    """保護者への確認メールと塾長通知。二重送信ガード: enroll:welcome:<rid> を SET NX (再送イベントでも 1 通)。
    テストモードの決済 (livemode=false) はメールを送らない (course と同じ)"""
    rid = record.get("registration_id", "")
    session_id = obj.get("id", "")
    if obj.get("livemode") is False:
        _log(f"webhook enroll: test-mode session {session_id} — no mail")
        return
    # KV が落ちていて NX の結果が取れないときは送る側に倒す (Resend の Idempotency-Key が 2 通目を弾く)
    nx = _redis_safe("SET", f"enroll:welcome:{rid}", json.dumps({"status": "sending", "at": int(time.time())}), "NX", "EX", str(ENROLL_RECORD_TTL))
    if nx is not None and not (isinstance(nx, dict) and nx.get("result") == "OK"):
        _log(f"webhook enroll: mail already handled rid={rid} — skip")
        return
    courses = record.get("courses") or []
    names = []
    course_fee = 0
    facility = 0
    parts = record.get("breakdown") or [x.strip() for x in str(record.get("fee_breakdown") or "").split(" / ") if x.strip()]
    for part in parts:
        # breakdown は register-subscribe が作る "名前 ¥7,500" の配列 (pending が消えていたら metadata の fee_breakdown 文字列)。設備費とコースを分ける
        if "設備費" in part:
            try:
                facility += int(part.rsplit("¥", 1)[1].replace(",", ""))
            except Exception:
                pass
        else:
            names.append(part)
            try:
                course_fee += int(part.rsplit("¥", 1)[1].replace(",", ""))
            except Exception:
                pass
    if not names:
        names = [c for c in courses]
    monthly_fee = int(record.get("monthly_fee") or 0)
    entry_fee = int(record.get("entry_fee") or 0)
    first_total = int(record.get("first_charge_amount") or 0)
    if not facility and monthly_fee and course_fee:
        facility = max(monthly_fee - course_fee, 0)
    if not course_fee and monthly_fee:
        course_fee = max(monthly_fee - facility, 0)
    contact = os.environ.get("COURSE_REPLY_TO", "").strip() or COURSE_CONTACT_DEFAULT
    if not COURSE_EMAIL_RE.match(contact):
        contact = COURSE_CONTACT_DEFAULT
    paid_jst = _course_jst(record.get("paid_at") or record.get("completed_at") or None)
    vars_ = {
        "student_name": record.get("studentName") or record.get("student_name") or "",
        "parent_name": record.get("parentName") or record.get("parent_name") or "保護者",
        "grade": record.get("grade", ""),
        "courses": "／".join(names) if names else "-",
        "entry_fee": f"{entry_fee:,}",
        "facility": f"{facility:,}",
        "course_fee": f"{course_fee:,}",
        "first_total": f"{first_total:,}",
        "monthly_fee": f"{monthly_fee:,}",
        "month_label": _enroll_month_label(month),
        "next_month_label": _enroll_month_label(_enroll_next_month(month)),
        "receipt_no": session_id,
        "app_id": record.get("app_id") or "★申込IDなし → 氏名・メールで照合",
        "contact": contact,
        "line_url": os.environ.get("COURSE_LINE_URL", "").strip() or COURSE_LINE_URL_DEFAULT,
        "email": record.get("email", ""),
        "paid_at_jst": paid_jst.strftime("%Y-%m-%d %H:%M"),
        "registration_id": rid,
        "welcome_status": "",
        "warnings": "",
        "fail_reason": "",
        "app_register_url": os.environ.get("ENROLL_APP_REGISTER_URL", "").strip() or ENROLL_APP_REGISTER_URL_DEFAULT,
        "zoom_block": (ENROLL_ZOOM_BLOCK.format(zoom_id=os.environ.get("ENROLL_ZOOM_ID", "").strip(),
                                               zoom_pass=os.environ.get("ENROLL_ZOOM_PASS", "").strip())
                       if (os.environ.get("ENROLL_ZOOM_ID", "").strip() and os.environ.get("ENROLL_ZOOM_PASS", "").strip())
                       else ENROLL_ZOOM_BLOCK_UNSET),
    }
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    from_raw = os.environ.get("FROM_EMAIL", "noreply@trillion-ai-juku.com").strip() or "noreply@trillion-ai-juku.com"
    from_email = from_raw if "<" in from_raw else f"トリリオン英語塾 <{from_raw}>"
    to_email = (record.get("email") or "").strip()
    status, err, resend_id = "", "", ""
    enabled = os.environ.get("ENROLL_WELCOME_ENABLED", "1").strip().lower() not in ("0", "false", "off")
    if not enabled:
        status = "disabled"
    elif not to_email or not COURSE_EMAIL_RE.match(to_email):
        status = "no_email"
        _log(f"webhook enroll CRITICAL: rid={rid} has no valid email — confirmation NOT sent")
    elif not api_key:
        status = "no_api_key"
        _log(f"webhook enroll CRITICAL: RESEND_API_KEY missing — confirmation NOT sent (rid={rid})")
    else:
        try:
            res = _resend_send_text(api_key, from_email, to_email, contact,
                                    ENROLL_WELCOME_SUBJECT.format(**vars_), ENROLL_WELCOME_BODY.format(**vars_),
                                    idempotency_key=f"enroll-welcome/{rid}")
            status = "sent"
            resend_id = (res or {}).get("id", "")
            _log(f"webhook enroll: confirmation sent rid={rid} resend_id={resend_id}")
        except Exception as e:
            status, err = "failed", repr(e)[:300]
            _log(f"webhook enroll CRITICAL: confirmation FAILED rid={rid}: {e!r}")
    _redis_safe("SET", f"enroll:welcome:{rid}", json.dumps({"status": status, "error": err, "resend_id": resend_id, "email": to_email,
                                                            "session_id": session_id, "month": month, "at": int(time.time())}, ensure_ascii=False),
                "EX", str(ENROLL_RECORD_TTL))
    _enroll_notify_owner(record, vars_, status, ledger_state, list(warnings or []))


def _enroll_notify_owner(record, vars_, mail_status, ledger_state, warnings):
    """塾長通知。★が 1 つでもあれば件名を「★要対応」にする (確認メール失敗・台帳未記録・カード未取得・翌月分の個別請求)"""
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    notify_to = os.environ.get("ENROLL_NOTIFY_EMAIL", "").strip() or os.environ.get("COURSE_NOTIFY_EMAIL", "").strip()
    if not (notify_to and api_key and COURSE_EMAIL_RE.match(notify_to)):
        return
    from_raw = os.environ.get("FROM_EMAIL", "noreply@trillion-ai-juku.com").strip() or "noreply@trillion-ai-juku.com"
    from_email = from_raw if "<" in from_raw else f"トリリオン英語塾 <{from_raw}>"
    rid = record.get("registration_id", "")
    try:
        ok = mail_status == "sent"
        vars_["welcome_status"] = "送信済み" if ok else f"★送信失敗 ({mail_status}) — 手動で送ってください"
        if ledger_state == "error":
            warnings.append("★台帳 (charge:done / charge:history) を KV に書けませんでした → 月末タブでこの生徒の当月が「引き落とし済み」になっているか確認。なっていなければ「✅ 支払い済みにする」で手動記録 (二重請求防止)")
        elif ledger_state == "exists":
            warnings.append("★台帳に当月の記録が既にあったため上書きしていません (再送または手動記録済み)。月末タブで確認")
        if not record.get("stripe_payment_method_id"):
            warnings.append("★カード (payment_method) を Stripe から取得できませんでした → 名簿で「再登録要」と出ます。Stripe で顧客にカードが付いていれば reconcile で復元")
        reasons = []
        if not ok:
            reasons.append("確認メール未送信")
        if any(w.startswith("★") for w in warnings):
            reasons.append("要確認あり")
        vars_["fail_reason"] = "・".join(reasons) or "要確認"
        vars_["warnings"] = ("\n".join(warnings) + "\n") if warnings else ""
        subj = (ENROLL_NOTIFY_SUBJECT if not reasons else ENROLL_NOTIFY_SUBJECT_FAILED).format(**vars_)
        _resend_send_text(api_key, from_email, notify_to, "", subj, ENROLL_NOTIFY_BODY.format(**vars_),
                          idempotency_key=f"enroll-notify/{rid}/{mail_status}")
    except Exception as e:
        _log(f"webhook enroll: owner notify failed: {e!r}")


def _handle_enroll_first_charge(obj, reg_id, metadata, existing):
    """mode=payment (first_charge=1) の完了。PaymentIntent から保存カードを取り、setup 相当の reg:completed を書く"""
    session_id = obj.get("id", "")
    pi_id = obj.get("payment_intent", "") or ""
    if obj.get("payment_status") not in ("paid", "no_payment_required"):
        _log(f"webhook enroll CRITICAL: session {session_id} payment_status={obj.get('payment_status')} — not registered")
        return
    secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not secret_key:
        _log(f"webhook CRITICAL: STRIPE_SECRET_KEY missing (rid={reg_id}) - payment_method will be empty")
    pi = _stripe_get(secret_key, f"payment_intents/{pi_id}") if (secret_key and pi_id) else None
    payment_method = ""
    pi_customer = ""
    amount_received = 0
    if pi and isinstance(pi, dict):
        pm = pi.get("payment_method")
        payment_method = pm.get("id", "") if isinstance(pm, dict) else (pm or "")
        pi_customer = pi.get("customer") or ""
        amount_received = int(pi.get("amount_received") or 0)
    customer = obj.get("customer", "") or pi_customer
    if not payment_method and secret_key and customer:
        # PaymentIntent が取れなかったときの予備: 顧客に保存されたカードを直接引く (setup_future_usage で attach 済み)
        pms = _stripe_get(secret_key, f"customers/{customer}/payment_methods?type=card&limit=1")
        for pm_obj in ((pms or {}).get("data") or []):
            payment_method = pm_obj.get("id") or ""
            if payment_method:
                _log(f"webhook enroll: payment_method recovered from customer {customer}")
                break
    email = obj.get("customer_email") or (obj.get("customer_details") or {}).get("email", "")
    try:
        monthly_fee = int(metadata.get("monthly_fee", "0"))
    except Exception:
        monthly_fee = 0
    try:
        entry_fee = int(metadata.get("entry_fee") or existing.get("entry_fee") or 0)
    except Exception:
        entry_fee = 0
    first_total = int(obj.get("amount_total") or 0) or amount_received
    if not first_total:
        try:
            first_total = int(metadata.get("first_total") or existing.get("first_total") or 0)
        except Exception:
            first_total = 0
    now_ts = int(time.time())
    # 台帳の月は「決済した月」= セッション作成 (支払いは作成から 24 時間以内) の JST 月。処理時刻を使うと、KV 障害で
    # Stripe の再送 (最長 3 日) が月をまたいだとき翌月に印が付き、決済した月が未請求のまま翌月が skip される
    paid_ts = int(obj.get("created") or 0) or now_ts
    month = _course_jst(paid_ts).strftime("%Y-%m")
    record = {
        **existing,
        "registration_id": reg_id,
        "session_id": session_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": "",
        "stripe_payment_method_id": payment_method,
        "stripe_setup_intent_id": "",
        "checkout_mode": "setup",            # 月末バッチ / 名簿 / スポット請求は setup だけを対象にする → 同じ扱いにする
        "status": "completed",
        "completed_at": now_ts,
        "paid_at": paid_ts,
        "amount": first_total,
        "monthly_fee": monthly_fee or int(existing.get("monthly_fee") or 0),
        "email": email or existing.get("email", ""),
        "system": "juku-payment-monthly",
        "first_charge": True,
        "first_charge_session_id": session_id,
        "first_charge_payment_intent_id": pi_id,
        "first_charge_amount": first_total,
        "first_charge_month": month,
        "entry_fee": entry_fee,
        "app_id": metadata.get("app_id") or existing.get("app_id") or "",
        "source": "enrollment-form-v1-payment",
    }
    # 同じ Stripe 顧客で既に名簿登録があれば (申込書を送り直して 2 回支払った)、名簿には足さず塾長に返金確認を促す。
    # 既存の登録が退塾処理で消えていれば通常どおり登録する
    if customer:
        by = _redis_safe("GET", f"reg:by_customer:{customer}")
        other = ((by or {}).get("result") or "") if isinstance(by, dict) else ""
        if other and other != reg_id:
            still = _redis_safe("GET", f"reg:completed:{other}")
            if isinstance(still, dict) and still.get("result"):
                record["status"] = "duplicate"
                record["duplicate_of"] = other
                _redis_safe("SET", f"reg:duplicate:{reg_id}", json.dumps(record, ensure_ascii=False), "EX", str(ENROLL_RECORD_TTL))
                _redis_safe("DEL", f"reg:pending:{reg_id}")
                _log(f"webhook enroll CRITICAL: duplicate first charge rid={reg_id} customer={customer} existing={other} amount={first_total} — NOT added to roster")
                if obj.get("livemode") is not False:
                    _enroll_notify_duplicate(record, other)
                return
    res = _redis_safe("SET", f"reg:completed:{reg_id}", json.dumps(record, ensure_ascii=False))
    if not (isinstance(res, dict) and res.get("result") == "OK"):
        _log(f"webhook enroll CRITICAL: KV error writing reg:completed rid={reg_id} — asking Stripe to retry")
        raise _RetryLater(f"reg:completed write failed rid={reg_id}")
    _redis_safe("DEL", f"reg:pending:{reg_id}")
    _redis_safe("ZADD", "reg:completed:index", str(now_ts), reg_id)
    if customer:
        _redis_safe("SET", f"reg:by_customer:{customer}", reg_id)
    ledger_state = _enroll_write_ledger(reg_id, month, pi_id, first_total, record, now_ts)
    warnings = []
    nxt = _enroll_next_month(month)
    if _enroll_next_month_batch_ran(nxt):
        warnings.append(f"★{_enroll_month_label(nxt)}分の月末バッチ (前倒し請求) は実行済みです → この生徒の {_enroll_month_label(nxt)}分 (月額 {record['monthly_fee']:,}円) は月末タブで {nxt} を選んで個別に請求してください (自動では請求されません)")
    _log(f"webhook enroll: completed reg={reg_id} customer={customer} pm={payment_method} first_total={first_total} monthly_fee={record['monthly_fee']} month={month} ledger={ledger_state}")
    try:
        _enroll_send_mails(obj, record, month, ledger_state, warnings)
    except Exception as e:
        _log(f"webhook enroll: mail step crashed rid={reg_id}: {e!r}")


def _enroll_notify_duplicate(record, duplicate_of):
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    notify_to = os.environ.get("ENROLL_NOTIFY_EMAIL", "").strip() or os.environ.get("COURSE_NOTIFY_EMAIL", "").strip()
    if not (notify_to and api_key and COURSE_EMAIL_RE.match(notify_to)):
        return
    from_raw = os.environ.get("FROM_EMAIL", "noreply@trillion-ai-juku.com").strip() or "noreply@trillion-ai-juku.com"
    from_email = from_raw if "<" in from_raw else f"トリリオン英語塾 <{from_raw}>"
    v = {"student_name": record.get("studentName") or record.get("student_name") or "", "grade": record.get("grade", ""),
         "parent_name": record.get("parentName") or record.get("parent_name") or "", "email": record.get("email", ""),
         "first_total": f"{int(record.get('first_charge_amount') or 0):,}", "receipt_no": record.get("session_id", ""),
         "app_id": record.get("app_id") or "-", "paid_at_jst": _course_jst(record.get("completed_at") or None).strftime("%Y-%m-%d %H:%M"),
         "customer": record.get("stripe_customer_id", ""), "duplicate_of": duplicate_of}
    try:
        _resend_send_text(api_key, from_email, notify_to, "", ENROLL_DUPLICATE_SUBJECT.format(**v), ENROLL_DUPLICATE_BODY.format(**v),
                          idempotency_key=f"enroll-duplicate/{record.get('registration_id', '')}")
    except Exception as e:
        _log(f"webhook enroll: duplicate notify failed: {e!r}")


def _handle_checkout_completed(event):
    """🆕 v2 (2026-05-13): mode=setup 対応。
    旧 mode=subscription も後方互換のため一応動くようにしておく。
    """
    obj = event.get("data", {}).get("object", {})
    session_id = obj.get("id", "")
    metadata = obj.get("metadata", {}) or {}
    reg_id = metadata.get("registration_id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")  # mode=subscription 時のみ存在
    setup_intent_id = obj.get("setup_intent", "")  # mode=setup 時のみ存在
    mode = obj.get("mode", "")
    amount = obj.get("amount_total", 0)
    email = obj.get("customer_email") or obj.get("customer_details", {}).get("email", "")

    # 🚨 AIコーチングとの完全分離: system metadata で識別
    # juku-payment 系 (system=juku-payment-monthly or reg_id 有り) 以外は skip
    system_tag = metadata.get("system", "")
    # 🆕 2026-09-16 月額講座 (支払いリンク) は registration_id を持たない別系統 → 受講案内メールだけ送って終わり
    if system_tag == COURSE_SYSTEM_TAG:
        _handle_course_checkout(obj)
        return
    if not reg_id and system_tag != "juku-payment-monthly":
        _log(f"webhook: not juku-payment event (mode={mode} system={system_tag}) — skip")
        return

    if not reg_id:
        _log(f"webhook: missing registration_id (mode={mode}) — skip")
        return

    # 🆕 mode=setup: SetupIntent から payment_method を取得
    # 🚨 2nd review fix: STRIPE_SECRET_KEY 未設定時の warning + customer 取得 fallback
    payment_method = ""
    monthly_fee = 0
    setup_intent_customer = ""  # SetupIntent.customer (Customer 取得 fallback)
    if mode == "setup" and setup_intent_id:
        secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
        if not secret_key:
            _log(f"webhook CRITICAL: STRIPE_SECRET_KEY missing in webhook env (rid={reg_id}) - payment_method will be empty")
        si = _stripe_get(secret_key, f"setup_intents/{setup_intent_id}") if secret_key else None
        if si and isinstance(si, dict):
            payment_method = si.get("payment_method") or ""
            setup_intent_customer = si.get("customer") or ""
        # metadata.monthly_fee は register-subscribe.py で必ず設定される
        try:
            monthly_fee = int(metadata.get("monthly_fee", "0"))
        except Exception:
            monthly_fee = 0

    # 🚨 fallback: session.customer が空でも SetupIntent.customer から復元
    if not customer and setup_intent_customer:
        customer = setup_intent_customer
        _log(f"webhook: customer fallback from SetupIntent rid={reg_id} customer={customer}")

    # pending → completed (KV 失敗時は metadata から最低限復元)
    existing_raw = _redis_safe("GET", f"reg:pending:{reg_id}")
    existing = {}
    if existing_raw and isinstance(existing_raw, dict):
        r = existing_raw.get("result")
        if r:
            try: existing = json.loads(r)
            except Exception: pass
    # KV pending が消失していても Stripe metadata から最低限の情報を復元
    if not existing:
        existing = {
            "registration_id": reg_id,
            "student_name": metadata.get("student_name", ""),
            "grade": metadata.get("grade", ""),
            "parent_name": metadata.get("parent_name", ""),
            "phone": metadata.get("phone", ""),
            "courses": [c for c in metadata.get("courses", "").split(",") if c],
            "options": [o for o in metadata.get("options", "").split(",") if o],
            "fee_breakdown": metadata.get("fee_breakdown", ""),
            "restored_from_metadata": True,
        }
    # 🆕 2026-09-17 入塾申込書からの初回決済 (mode=payment) は専用処理へ (setup 相当の名簿 + 当月の台帳 + メール)
    if mode == "payment" and (metadata.get("first_charge") == "1" or existing.get("first_charge") is True):
        _handle_enroll_first_charge(obj, reg_id, metadata, existing)
        return

    # 🆕 mode によって record の意味が異なる:
    #   mode=setup       : amount=0 / payment_method 必須 / monthly_fee で月額保存
    #   mode=subscription: amount=初回課金額 / subscription_id 必須 (legacy)
    record = {
        **existing,
        "registration_id": reg_id,
        "session_id": session_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,  # setup 時は空
        "stripe_payment_method_id": payment_method,  # 🆕 setup 時のみ
        "stripe_setup_intent_id": setup_intent_id,  # 🆕 setup 時のみ
        "checkout_mode": mode,  # "setup" or "subscription"
        "status": "completed",
        "completed_at": int(time.time()),
        "amount": amount,  # setup 時は 0
        "monthly_fee": monthly_fee or existing.get("monthly_fee", 0),  # 🆕 月額 (バッチ請求用)
        "email": email or existing.get("email", ""),
        "system": "juku-payment-monthly",
    }
    _redis_safe("SET", f"reg:completed:{reg_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("DEL", f"reg:pending:{reg_id}")
    _redis_safe("ZADD", "reg:completed:index", str(record["completed_at"]), reg_id)
    _log(f"webhook: completed reg={reg_id} mode={mode} customer={customer} pm={payment_method} monthly_fee={monthly_fee}")


def _handle_payment_failed(event):
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング invoice event の混入防止)
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    sub_meta = (obj.get("subscription_details") or {}).get("metadata", {}) or {}
    sys_tag = (meta.get("system") or sub_meta.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: invoice.payment_failed skipped (system={sys_tag} - not juku-payment)")
        return
    if sys_tag == COURSE_SYSTEM_TAG:   # 🆕 月額講座は月謝の台帳 (pay:failed) に混ぜない。失敗は Stripe の通知メールで塾長が知る
        _log("webhook: invoice.payment_failed skipped (course subscription)")
        return
    invoice_id = obj.get("id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")
    amount_due = obj.get("amount_due", 0)
    next_attempt = obj.get("next_payment_attempt")
    email = obj.get("customer_email", "")
    failure_msg = (obj.get("last_finalization_error") or {}).get("message", "") or ""

    record = {
        "invoice_id": invoice_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,
        "amount_due": amount_due,
        "next_attempt": next_attempt,
        "email": email,
        "failure_message": failure_msg[:300],
        "failed_at": int(time.time()),
    }
    _redis_safe("SET", f"pay:failed:{invoice_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "pay:failed:index", str(record["failed_at"]), invoice_id)
    _log(f"webhook: payment_failed invoice={invoice_id} amount={amount_due}")


def _handle_subscription_deleted(event):
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング subscription event の混入防止)
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    sys_tag = (meta.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: subscription_deleted skipped (system={sys_tag} - not juku-payment)")
        return
    if sys_tag == COURSE_SYSTEM_TAG:   # 🆕 月額講座の解約は月謝の台帳 (sub:canceled) に混ぜない
        _log("webhook: subscription_deleted skipped (course subscription)")
        return
    sub_id = obj.get("id", "")
    customer = obj.get("customer", "")
    canceled_at = obj.get("canceled_at") or int(time.time())
    record = {
        "stripe_subscription_id": sub_id,
        "stripe_customer_id": customer,
        "canceled_at": canceled_at,
        "metadata": meta,
    }
    _redis_safe("SET", f"sub:canceled:{sub_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "sub:canceled:index", str(canceled_at), sub_id)
    _log(f"webhook: subscription_deleted sub={sub_id}")


def _handle_payment_succeeded(event):
    """invoice.payment_succeeded — 月次サブスク or 過去未納分の請求書が支払われた時"""
    obj = event.get("data", {}).get("object", {})
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング invoice 混入防止)
    # 🆕 2026-08-16: subscription_details.metadata も見る (_handle_payment_failed と対称)。
    #   invoice 自体の metadata は空が普通で、神テスト (kamitest-subscription) のサブスク
    #   請求書がここを素通りして月謝の pay:succeeded 台帳に混ざっていた。
    metadata = obj.get("metadata", {}) or {}
    sub_meta = (obj.get("subscription_details") or {}).get("metadata", {}) or {}
    sys_tag = (metadata.get("system") or sub_meta.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: invoice.payment_succeeded skipped (system={sys_tag} - not juku-payment)")
        return
    if sys_tag == COURSE_SYSTEM_TAG:   # 🆕 月額講座の毎月の更新は月謝の台帳 (pay:succeeded) に混ぜない
        _log("webhook: invoice.payment_succeeded skipped (course subscription)")
        return
    invoice_id = obj.get("id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")
    amount_paid = obj.get("amount_paid", 0)
    source = metadata.get("source", "")
    student_name = metadata.get("student_name", "")
    month = metadata.get("month", "")

    record = {
        "invoice_id": invoice_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,
        "amount_paid": amount_paid,
        "metadata": metadata,
        "paid_at": int(time.time()),
        "source": source,
    }
    _redis_safe("SET", f"pay:succeeded:{invoice_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "pay:succeeded:index", str(record["paid_at"]), invoice_id)

    # past-due 由来なら専用 index にも記録 (塾長ダッシュ用)
    if source == "past-due-invoice-v1":
        _redis_safe("SET", f"pastdue:paid:{invoice_id}", json.dumps(record, ensure_ascii=False))
        _redis_safe("ZADD", "pastdue:paid:index", str(record["paid_at"]), invoice_id)
        _log(f"webhook: past-due paid invoice={invoice_id} student={student_name} month={month} amount={amount_paid}")
    else:
        _log(f"webhook: payment_succeeded invoice={invoice_id} amount={amount_paid}")


def _clear_charge_source_state(source_state, rid, month):
    """月次 auto-reconcile 完了時の中間 state 掃除 (record DEL + index ZREM)。
    mark_paid / mark_unpaid (admin-charge-reconcile.py) も uncertain / requires_action の
    両 namespace をこれと同じ規約で掃除する (2026-07-02 fix: 従来 reconcile は uncertain
    のみで、mark_paid で決着させた RA record が TTL 1年残る残課題があった → 解消済み)。
    🚨 2026-07-02 fix: uncertain 側も index から ZREM する (従来は record DEL のみで
    index にゴミが残り、台帳の MGET 枠 (GET_CAP) を無駄に食っていた)。"""
    if source_state == "uncertain":
        _redis_safe("DEL", f"charge:uncertain:{rid}:{month}")
        _redis_safe("ZREM", "charge:uncertain:index", f"{rid}:{month}")
    elif source_state == "requires_action":
        _redis_safe("DEL", f"charge:requires_action:{rid}:{month}")
        _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")


def _update_spot_history(meta, pi_id, new_status, source_event):
    """🆕 2026-07-02: 講習など単発スポット課金 (admin-charge-spot.py) の record を
    Stripe event で確定更新する。spot:history は同期 response 時の書き切りで、
    requires_action (3DS) → 顧客の認証完了後に succeeded へ更新する経路が無く、
    台帳 (admin-charge-ledger) で「🎓⚠️要確認」のまま永久に残っていた。
    record key は PI metadata の registration_id + idem_token から再構成する
    (idem_token は admin-charge-spot.py が metadata に焼き込む。無い旧 PI は skip)。"""
    rid = (meta.get("registration_id") or "").strip()
    token = (meta.get("idem_token") or "").strip()
    if not rid or not token:
        _log(f"webhook: spot PI missing registration_id/idem_token metadata pi={pi_id} - skip spot reconcile")
        return
    key = f"spot:history:{rid}:{token}"
    got = _redis_safe("GET", key)
    rec = None
    if got and isinstance(got, dict) and got.get("result"):
        try:
            parsed = json.loads(got["result"])
            if isinstance(parsed, dict):
                rec = parsed
        except Exception:
            pass
    if not rec:
        # 同期 response がまだ record を書いていない (即時成功時は webhook が先着し得る)
        # or TTL 切れ → 同期側の書込を正とする / 触らない
        _log(f"webhook: spot record not found key={key} pi={pi_id} - skip")
        return
    cur = (rec.get("status") or "").strip()
    if cur == new_status:
        return  # 冪等 (Stripe event 再送)
    if cur == "succeeded":
        # out-of-order な failed event で確定成功を降格させない。
        # ★processing は非終端 status (Stripe は processing → payment_failed に正規遷移し得る)
        # なのでここでは守らない = processing → failed は正当な前進遷移として通す (2026-07-02 review)
        _log(f"webhook: spot skip downgrade key={key} {cur} -x-> {new_status} pi={pi_id}")
        return
    if new_status == "failed" and cur not in ("requires_action", "uncertain", "processing"):
        # 同期側で確定済みの failed の再書込は不要・想定外 status からの failed 化はしない
        _log(f"webhook: spot skip failed-transition key={key} cur={cur} pi={pi_id}")
        return
    rec_pi = (rec.get("payment_intent_id") or "").strip()
    if rec_pi and pi_id and rec_pi != pi_id:
        # 同一 idem_token で別 PI は Idempotency-Key 上ありえない → 触らず要調査ログのみ
        _log(f"webhook: spot PI mismatch key={key} rec_pi={rec_pi} event_pi={pi_id} - skip")
        return
    rec["status"] = new_status
    if pi_id and not rec_pi:
        rec["payment_intent_id"] = pi_id
    rec["status_updated_at"] = int(time.time())
    rec["source_event"] = source_event
    # "at" は変更しない (台帳の月割り当ては at 由来。3DS 完了が月を跨いでも請求起票月に留める)
    rec_json = json.dumps(rec, ensure_ascii=False)
    _redis_safe("SET", key, rec_json, "EX", "31536000")  # 1y (spot.py の _record と同じ)
    # index 自己修復: 書込時に ZADD だけ落ちた個体を台帳に復帰させる
    # (score = record の at = 元の起票時刻なので、既存 entry は score 不変 = 順序も不変・冪等)
    try:
        _at_score = int(rec.get("at") or 0) or int(time.time())
    except Exception:
        _at_score = int(time.time())
    _redis_safe("ZADD", "spot:history:index", str(_at_score), f"{rid}:{token}")
    _redis_safe("RPUSH", f"spot:history:audit:{rid}", rec_json)
    _redis_safe("EXPIRE", f"spot:history:audit:{rid}", "31536000")
    _log(f"webhook: spot {cur} -> {new_status} rid={rid} token={token} pi={pi_id}")


def _handle_payment_intent_succeeded(event):
    """🆕 v2 (2026-05-13): 月末バッチ請求の PaymentIntent 成功 event を非同期 reconcile 用に記録。
    execute.py が同期 response で既に charge:history を書いているが、SCA 後の銀行 async 承認 etc で
    後から成功になる case を捕捉するための補完。
    """
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    # 🚨 Round 5 fix (C2): 既存 3 handler と統一して startswith 判定 (空文字 = 既存挙動維持)
    # 将来 juku-payment-yearly 等の派生 system を追加した時にも自動的に処理対象になる
    _pi_sys = (meta.get("system") or "").strip()
    if _pi_sys and not _pi_sys.startswith("juku-payment"):
        _log(f"webhook: PaymentIntent skipped (system={_pi_sys} - not juku-payment)")
        return
    pi_id = obj.get("id", "")
    customer = obj.get("customer", "")
    amount = obj.get("amount_received", 0) or obj.get("amount", 0)
    rid = meta.get("registration_id", "")
    month = meta.get("month", "")
    record = {
        "payment_intent_id": pi_id,
        "stripe_customer_id": customer,
        "registration_id": rid,
        "month": month,
        "amount": amount,
        "metadata": meta,
        "status": "succeeded",
        "succeeded_at": int(time.time()),
        "source_event": "payment_intent.succeeded",
    }
    _redis_safe("SET", f"pi:succeeded:{pi_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "pi:succeeded:index", str(record["succeeded_at"]), pi_id)
    # 🆕 2026-07-02: 単発スポット課金 (admin-charge-spot.py) は月次 reconcile 対象外。
    # spot:history の status を succeeded に確定して終了 (3DS 完了・async 承認の反映)。
    if _pi_sys == "juku-payment-spot":
        _update_spot_history(meta, pi_id, "succeeded", "payment_intent.succeeded")
        _log(f"webhook: payment_intent.succeeded (spot) rid={rid} pi={pi_id} amount={amount}")
        return
    # 🚨 2nd/3rd/4th review fix: 自動 reconcile (uncertain + requires_action 両方の case を処理)
    # done_key が既に他の status (succeeded/manually_reconciled/retry) で確定済なら override しない
    # tombstone (unpaid マーク済) があれば auto-reconcile を完全に skip (幽霊復活防止)
    if rid and month:
        uncertain_key = f"charge:uncertain:{rid}:{month}"
        requires_action_key = f"charge:requires_action:{rid}:{month}"
        done_key = f"charge:done:{rid}:{month}"
        tombstone_key = f"charge:unpaid-tombstone:{rid}:{month}"
        tombstone_check = _redis_safe("GET", tombstone_key)
        tombstone_active = bool(tombstone_check and isinstance(tombstone_check, dict) and tombstone_check.get("result"))
        if tombstone_active:
            # 🚨 2026-07-02 fix (df439e6 3並列review 残穴②): PI 非照合の無差別ミュートをやめる。
            # mark_unpaid → 💳個別請求/retry → 新 PI が再び requires_action → 顧客が 3DS 完了、
            # の succeeded が握り潰され、回収済みなのに台帳が 🔐 のまま最大 30 日 (tombstone TTL)
            # 止まっていた (execute/retry は成功分岐でしか tombstone を DEL しない)。判定は2段:
            # ① RA record の payment_intent_id と event PI の完全一致 → 通す。
            #    mark_unpaid は RA record を必ず DEL するため、tombstone と併存する RA record は
            #    tombstone より「後」の新試行 (execute/retry の RA 分岐) が書いたもの = その PI は
            #    幽霊ではあり得ない。時刻比較では区別できない同一秒 (UI の mark_unpaid→retry 自動
            #    連鎖で常態的に起きる)・clock skew・Idempotency replay で created が古い正当回収も
            #    これで救う (2026-07-03 3並列review P1)。
            # ② fallback: tombstone の marked_at と PI の created の時刻比較 (canceled handler
            #    ガード3 の canceled_at vs noted_at と同型)。RA record に PI が無い uncertain 起点
            #    向け。created >= marked_at なら新試行 = 通す (「未課金」と確定判断した旧 PI が
            #    判断と同一秒に作成されることは物理的にないため >= が安全)。
            #    marked_at / created が取れない場合は安全側 = ミュート維持。
            ra_probe_pi = ""
            _ra_probe = _redis_safe("GET", requires_action_key)
            if _ra_probe and isinstance(_ra_probe, dict) and _ra_probe.get("result"):
                try:
                    _ra_probe_rec = json.loads(_ra_probe["result"])
                    if isinstance(_ra_probe_rec, dict):
                        ra_probe_pi = (_ra_probe_rec.get("payment_intent_id") or "").strip()
                except Exception:
                    ra_probe_pi = ""
            if pi_id and ra_probe_pi and ra_probe_pi == pi_id:
                tombstone_active = False
                _log(f"webhook: tombstone bypassed (event PI matches live RA record) rid={rid} month={month} pi={pi_id}")
            else:
                marked_at_ts = 0
                try:
                    _tomb = json.loads(tombstone_check["result"])
                    if isinstance(_tomb, dict):
                        marked_at_ts = int(_tomb.get("marked_at") or 0)
                except Exception:
                    marked_at_ts = 0
                try:
                    pi_created_ts = int(obj.get("created") or 0)
                except Exception:
                    pi_created_ts = 0
                if marked_at_ts and pi_created_ts and pi_created_ts >= marked_at_ts:
                    tombstone_active = False
                    _log(f"webhook: tombstone predates PI (marked_at={marked_at_ts} <= created={pi_created_ts}) - allowing auto-reconcile rid={rid} month={month} pi={pi_id}")
        if tombstone_active:
            _log(f"webhook: tombstone found, skipping auto-reconcile rid={rid} month={month} pi={pi_id}")
        else:
            existing_uncertain = _redis_safe("GET", uncertain_key)
            existing_requires_action = _redis_safe("GET", requires_action_key)
            should_auto_reconcile = False
            source_state = None
            if existing_uncertain and isinstance(existing_uncertain, dict) and existing_uncertain.get("result"):
                should_auto_reconcile = True
                source_state = "uncertain"
            # 🚨 Round 4 fix (C-BUG-1): requires_action → succeeded の遷移を捕捉
            # SCA 認証完了後の async PI.succeeded で正常に charge:history を書く
            elif existing_requires_action and isinstance(existing_requires_action, dict) and existing_requires_action.get("result"):
                should_auto_reconcile = True
                source_state = "requires_action"

            if should_auto_reconcile:
                # done_key の既存状態を check
                existing_done_raw = _redis_safe("GET", done_key)
                existing_done = None
                if existing_done_raw and isinstance(existing_done_raw, dict):
                    ed_s = existing_done_raw.get("result")
                    if ed_s:
                        try:
                            _ed = json.loads(ed_s)
                            if isinstance(_ed, dict):
                                existing_done = _ed
                        except Exception: pass
                # 既存 done が succeeded/manually_reconciled なら、上書きせず source state だけ削除
                # 🚨 Round 5 fix (H3): manually_reconciled も skip 条件に追加 (mark_paid との race 防御)
                if existing_done and (
                    existing_done.get("status") in ("succeeded", "processing") or
                    existing_done.get("manually_reconciled") is True
                ):
                    _clear_charge_source_state(source_state, rid, month)
                    _log(f"webhook: {source_state} cleared (done already finalized) rid={rid} month={month} pi={pi_id}")
                else:
                    now_ts = int(time.time())
                    done_payload = json.dumps({
                        "payment_intent_id": pi_id, "status": "succeeded",
                        "amount": amount, "charged_at": now_ts,
                        "auto_reconciled_from": source_state,
                    }, ensure_ascii=False)
                    # 🚨 2026-07-02 fix: execute は uncertain/requires_action 時に done_key を
                    # 中間 status のまま保持する (二重請求防止ロック) ため、常時 SET NX だと
                    # 通常フローで必ず失敗し「race 扱い → history 未記録のまま return」になっていた
                    # (= 3DS 完了/uncertain 自動確定の回収済みが台帳・売上集計から漏れる)。
                    # 既存 done が中間 status (uncertain/requires_action) なら succeeded へ確定上書き。
                    # done_key 不在時のみ SET NX (手動 mark_paid との同時書込 race 防御は従来通り)。
                    if existing_done is not None:
                        set_result = _redis_safe("SET", done_key, done_payload, "EX", "5184000")
                        if not (set_result and isinstance(set_result, dict) and set_result.get("result") == "OK"):
                            # plain SET は race では失敗しない (失敗 = KV エラーのみ)。真実の記録は
                            # history 側なので続行するが、done が中間 status のまま残る事実はログに残す
                            _log(f"webhook: WARN done overwrite kv-error rid={rid} month={month} - proceeding with history write")
                        wrote_done = True
                    else:
                        nx_result = _redis_safe("SET", done_key, done_payload, "NX", "EX", "5184000")
                        wrote_done = bool(nx_result and isinstance(nx_result, dict) and nx_result.get("result") == "OK")
                    if not wrote_done:
                        # 手動 mark_paid が先に書いた → source state だけ削除して終了 (history は mark_paid 側が書く)
                        _clear_charge_source_state(source_state, rid, month)
                        _log(f"webhook: race detected (manual mark_paid won) {source_state} cleared rid={rid} month={month}")
                        return
                    # 🚨 Round 4 fix + 2026-07-02 fix: requires_action だけでなく uncertain 起点の
                    # 自動確定も charge:history に記録する (書かないと台帳 (admin-charge-ledger) の
                    # マスが空欄・月合計/履歴の売上集計から漏れる。charge:done は TTL 60日で消えるため
                    # history が唯一の恒久記録)
                    student_name = meta.get("student_name", "")
                    email = meta.get("email", "")
                    _history_rec = {
                        "payment_intent_id": pi_id,
                        "registration_id": rid,
                        "month": month,
                        "amount": amount,
                        "student_name": student_name,
                        "email": email,
                        "charged_at": now_ts,
                        "status": "succeeded",
                        "auto_reconciled_from": source_state,
                        "source": "sca-async-completion" if source_state == "requires_action" else "uncertain-async-completion",
                    }
                    _redis_safe("ZADD", "charge:history:index", str(now_ts), f"{rid}:{month}")
                    _redis_safe("SET", f"charge:history:{rid}:{month}", json.dumps(_history_rec, ensure_ascii=False), "EX", "31536000")
                    _redis_safe("RPUSH", f"charge:history:audit:{rid}:{month}", json.dumps(_history_rec, ensure_ascii=False))
                    _redis_safe("EXPIRE", f"charge:history:audit:{rid}:{month}", "31536000")
                    _clear_charge_source_state(source_state, rid, month)
                    # 月が succeeded で決着したので tombstone も解除 (execute/retry の成功分岐・
                    # mark_paid と同じ「決着時に消す」規約。残しても done=succeeded ガードで
                    # 実害は無いが、30日間 旧 PI 由来 event のログ文言が紛らわしくなるだけ)
                    _redis_safe("DEL", tombstone_key)
                    _log(f"webhook: auto-reconciled {source_state} → succeeded rid={rid} month={month} pi={pi_id} amount={amount}")
    _log(f"webhook: payment_intent.succeeded rid={rid} month={month} pi={pi_id} amount={amount}")


def _handle_payment_intent_failed(event):
    """🆕 v2 (2026-05-13): 月末バッチ請求の PaymentIntent 失敗 event を記録。
    execute.py が同期 HTTPError で既に charge:failed を書いているが、SCA 後の銀行 async 拒否で
    後から失敗になる case を捕捉するための補完。
    """
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    # 🚨 Round 5 fix (C2): 既存 3 handler と統一して startswith 判定 (空文字 = 既存挙動維持)
    # 将来 juku-payment-yearly 等の派生 system を追加した時にも自動的に処理対象になる
    _pi_sys = (meta.get("system") or "").strip()
    if _pi_sys and not _pi_sys.startswith("juku-payment"):
        _log(f"webhook: PaymentIntent skipped (system={_pi_sys} - not juku-payment)")
        return
    pi_id = obj.get("id", "")
    rid = meta.get("registration_id", "")
    month = meta.get("month", "")
    last_error = obj.get("last_payment_error", {}) or {}
    error_code = last_error.get("code", "")
    decline_code = last_error.get("decline_code", "")
    error_msg = last_error.get("message", "")[:300]
    record = {
        "payment_intent_id": pi_id,
        "registration_id": rid,
        "month": month,
        "amount": obj.get("amount", 0),
        "metadata": meta,
        "error_code": error_code,
        "decline_code": decline_code,
        "error_message": error_msg,
        "failed_at": int(time.time()),
        "source_event": "payment_intent.payment_failed",
    }
    _redis_safe("SET", f"pi:failed:{pi_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "pi:failed:index", str(record["failed_at"]), pi_id)
    # 🆕 2026-07-02: 単発スポット課金の 3DS 拒否/失敗も record に反映する
    # (succeeded 側と対で、requires_action の「🎓⚠️要確認」が永久に残らないようにする。
    #  _update_spot_history 内で succeeded/processing からの降格は拒否 = out-of-order event 安全)
    if _pi_sys == "juku-payment-spot":
        _update_spot_history(meta, pi_id, "failed", "payment_intent.payment_failed")
    _log(f"webhook: payment_intent.payment_failed rid={rid} month={month} pi={pi_id} code={error_code} decline={decline_code}")


def _kv_get_state(key):
    """KV GET → (exists, parsed_dict|None)。値はあるが JSON dict でない
    (execute の SET NX 初期値 "pending" 等) は (True, None) を返す。"""
    got = _redis_safe("GET", key)
    if not (got and isinstance(got, dict) and got.get("result")):
        return False, None
    try:
        parsed = json.loads(got["result"])
    except Exception:
        return True, None
    return True, parsed if isinstance(parsed, dict) else None


def _handle_payment_intent_canceled(event):
    """🆕 2026-07-02: payment_intent.canceled — 主に塾長が Stripe Dashboard で
    要確認 (uncertain / requires_action) の PI を手動キャンセルした時の掃除。
    従来はハンドラが無く、キャンセルしても charge:uncertain / charge:requires_action /
    spot:history の record が TTL 1年残り、台帳・詳細履歴に ⚠️/🔐 が出続けていた。

    月次: failed 相当の掃除 = 中間 record (uncertain/RA) + 中間 done ロックを解除し、
          charge:failed を書く (台帳 ❌ = execute 同期失敗と同じ「ロック解除済・再請求可能」規約。
          failed_at は再請求時の Idempotency salt 供給源のため掃除より先に書く)。
    spot: _update_spot_history で failed 確定 (succeeded からの降格は同関数が拒否。
          processing→failed は正規の前進遷移として通す = 同関数 L364 の規約どおり)。

    ★安全ガード (succeeded 済みを canceled で降格させない):
      - done or charge:history が succeeded/processing/manually_reconciled → 月の状態は不変
        (同一 PI の残骸 RA record の掃除のみ行う)
      - RA record / 中間 done の payment_intent_id が event と別 PI → 一切触らない
        (retry 等で別 PI が生きている月を旧 PI のキャンセルで誤って unlock しない)
      - PI id を持たない uncertain の record/done ロックは canceled_at vs noted_at の
        前後比較で守る (遅延再送された旧 PI の canceled が新試行のロックを外さない)
      - done が中間 status の JSON dict でない ("pending" = execute 実行中の NX ロック) → done 温存
    ※ Stripe Dashboard の webhook endpoint に payment_intent.canceled の購読追加が必要。
      ★順序厳守: 本コードのデプロイ反映を確認してから購読追加すること。先に購読すると
      旧コードが event id を webhook:seen に焼き付け (TTL 24h)、デプロイ後に Dashboard から
      Resend しても duplicate 扱いで飲まれる (24h 待つか mark_unpaid での手動復旧になる)。"""
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    _pi_sys = (meta.get("system") or "").strip()
    if _pi_sys and not _pi_sys.startswith("juku-payment"):
        _log(f"webhook: PaymentIntent skipped (system={_pi_sys} - not juku-payment)")
        return
    pi_id = obj.get("id", "")
    rid = meta.get("registration_id", "")
    month = meta.get("month", "")
    reason = obj.get("cancellation_reason") or ""
    record = {
        "payment_intent_id": pi_id,
        "registration_id": rid,
        "month": month,
        "amount": obj.get("amount", 0),
        "metadata": meta,
        "cancellation_reason": reason,
        "canceled_at": int(time.time()),
        "source_event": "payment_intent.canceled",
    }
    _redis_safe("SET", f"pi:canceled:{pi_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "pi:canceled:index", str(record["canceled_at"]), pi_id)
    if _pi_sys == "juku-payment-spot":
        _update_spot_history(meta, pi_id, "failed", "payment_intent.canceled")
        _log(f"webhook: payment_intent.canceled (spot) rid={rid} pi={pi_id} reason={reason}")
        return
    if not rid or not month:
        _log(f"webhook: payment_intent.canceled without rid/month pi={pi_id} - audit only")
        return

    ra_key = f"charge:requires_action:{rid}:{month}"
    unc_key = f"charge:uncertain:{rid}:{month}"
    done_key = f"charge:done:{rid}:{month}"
    ra_exists, ra_rec = _kv_get_state(ra_key)
    unc_exists, unc_rec = _kv_get_state(unc_key)
    done_exists, done_rec = _kv_get_state(done_key)
    _hist_exists, hist_rec = _kv_get_state(f"charge:history:{rid}:{month}")

    # --- ガード1: 月が succeeded で確定済みなら絶対に降格させない ---
    done_final = bool(done_rec and (
        done_rec.get("status") in ("succeeded", "processing") or
        done_rec.get("manually_reconciled") is True))
    hist_final = bool(hist_rec and hist_rec.get("status") in ("succeeded", "processing"))
    if done_final or hist_final:
        # 決着済みの月に残った「同一 PI の」RA 残骸だけは掃除 (旧 mark_paid が RA を
        # 掃除しなかった時代のデータの自己修復。PI 一致 = その record は確実に死んでいる)
        if ra_rec and (ra_rec.get("payment_intent_id") or "") == pi_id:
            _redis_safe("DEL", ra_key)
            _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")
            _log(f"webhook: canceled PI swept stale RA record (month settled) rid={rid} month={month} pi={pi_id}")
        else:
            _log(f"webhook: payment_intent.canceled ignored (month settled) rid={rid} month={month} pi={pi_id}")
        return

    # --- ガード2: 別 PI がこの月を保持している場合は触らない ---
    ra_pi = (ra_rec.get("payment_intent_id") or "") if ra_rec else ""
    if ra_pi and ra_pi != pi_id:
        _log(f"webhook: canceled PI mismatch (RA holds {ra_pi}) rid={rid} month={month} pi={pi_id} - skip")
        return
    done_intermediate = bool(done_rec and done_rec.get("status") in ("uncertain", "requires_action"))
    done_pi = (done_rec.get("payment_intent_id") or "") if done_rec else ""
    if done_intermediate and done_pi and done_pi != pi_id:
        _log(f"webhook: canceled PI mismatch (done lock holds {done_pi}) rid={rid} month={month} pi={pi_id} - skip")
        return

    # --- ガード3: 遅延/再送 event の stale 判定 (2026-07-02 3並列review P1) ---
    # uncertain の record / done ロックは PI id を持たない (timeout 起因で PI 不明) ため
    # ガード2 で守れない。Stripe は配送失敗時 最大3日 retry / 手動 Resend も可能で、
    # webhook:seen の dedup は 24h しか効かない。PI の canceled_at より「後に」生まれた
    # uncertain 中間 state は別 (より新しい) 試行のもの → 旧 PI の canceled で解除しない
    # (解除すると新試行が実は成功していた場合に ❌ 表示 → 再請求 = 二重請求の入口になる)。
    try:
        canceled_at_ts = int(obj.get("canceled_at") or 0)
    except Exception:
        canceled_at_ts = 0

    def _newer_than_cancel(rec):
        if not canceled_at_ts or not rec:
            return False
        try:
            return int(rec.get("noted_at") or 0) > canceled_at_ts
        except Exception:
            return False

    will_clean = []
    if ra_exists:
        # RA はガード2 で PI 照合済み (同一 PI or 照合不能 record のみここに来る)
        will_clean.append("requires_action")
    if unc_exists:
        if _newer_than_cancel(unc_rec):
            _log(f"webhook: canceled PI stale (uncertain noted_at > canceled_at) rid={rid} month={month} pi={pi_id} - keep uncertain")
        else:
            will_clean.append("uncertain")
    release_done = False
    if done_exists:
        if not done_intermediate:
            # "pending" (execute 実行中の NX ロック) / 想定外形式 → in-flight 二重請求防御を壊さない
            _log(f"webhook: canceled PI keeps non-intermediate done rid={rid} month={month} pi={pi_id}")
        elif not done_pi and _newer_than_cancel(done_rec):
            # PI 無し (uncertain) の done ロックがキャンセルより新しい = 別試行のロック → 温存
            _log(f"webhook: canceled PI stale (done noted_at > canceled_at) rid={rid} month={month} pi={pi_id} - keep done lock")
        else:
            release_done = True
            will_clean.append("done-lock")
    if not will_clean:
        _log(f"webhook: payment_intent.canceled no state to clean rid={rid} month={month} pi={pi_id}")
        return

    # 台帳・詳細履歴に「この月は未回収 (キャンセル)」を残す = execute 同期失敗と同じ charge:failed 規約。
    # ★掃除 (DEL) より先に書く: この record の failed_at は再請求時の Idempotency salt
    # (execute の failed_salts) の供給源なので、途中クラッシュで「掃除済みなのに ❌ が無い
    # (= salt 無しの決定的キーで Stripe replay を踏む)」窓を作らない (2026-07-02 review P2)。
    src_rec = ra_rec or unc_rec or {}
    try:
        amount = int(src_rec.get("amount") or 0) or int(obj.get("amount") or 0)
    except Exception:
        amount = 0
    failed_rec = {
        "registration_id": rid,
        "month": month,
        "amount": amount,
        "student_name": src_rec.get("student_name") or meta.get("student_name", ""),
        "email": src_rec.get("email") or meta.get("email", ""),
        "phone": src_rec.get("phone", ""),
        "payment_intent_id": pi_id,
        "error_code": "payment_intent_canceled",
        "decline_code": reason,
        "error_detail": f"PaymentIntent がキャンセルされました (reason={reason or 'unknown'}・Stripe Dashboard 等での手動キャンセル)",
        "failed_at": int(time.time()),
        "source_event": "payment_intent.canceled",
    }
    _redis_safe("SET", f"charge:failed:{rid}:{month}", json.dumps(failed_rec, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "charge:failed:index", str(failed_rec["failed_at"]), f"{rid}:{month}")

    # 掃除 (❌ マーカー確定後)
    if "requires_action" in will_clean:
        _redis_safe("DEL", ra_key)
        _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")
    if "uncertain" in will_clean:
        _redis_safe("DEL", unc_key)
        _redis_safe("ZREM", "charge:uncertain:index", f"{rid}:{month}")
    if release_done:
        # 中間ロック解除 → 台帳 ❌ + 個別請求で再請求可能に (execute の同期失敗と同じ扱い)
        _redis_safe("DEL", done_key)
    _log(f"webhook: payment_intent.canceled cleaned {'+'.join(will_clean)} rid={rid} month={month} pi={pi_id} reason={reason}")


HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "checkout.session.async_payment_succeeded": _handle_course_async_paid,  # 🆕 月額講座のみ (カード以外の入金確定)
    "invoice.payment_failed": _handle_payment_failed,
    "invoice.payment_succeeded": _handle_payment_succeeded,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "payment_intent.succeeded": _handle_payment_intent_succeeded,
    "payment_intent.payment_failed": _handle_payment_intent_failed,
    "payment_intent.canceled": _handle_payment_intent_canceled,
}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            sig_header = self.headers.get("Stripe-Signature", "")
            secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()

            # 署名検証 (env 未設定なら 503)
            if not secret:
                _log("webhook: STRIPE_WEBHOOK_SECRET not set")
                _json(self, 503, {"error": "WEBHOOK_SECRET_NOT_SET"})
                return

            if not _verify_signature(raw, sig_header, secret):
                _log("webhook: signature verification failed")
                _json(self, 401, {"error": "INVALID_SIGNATURE"})
                return

            try:
                event = json.loads(raw.decode("utf-8"))
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return

            event_type = event.get("type", "")
            event_id = event.get("id", "")

            # idempotency: SET NX EX で原子的に重複検知 (race condition 対策)
            # Stripe が並行リトライしても最初の1件だけが処理される
            seen_key = f"webhook:seen:{event_id}"
            seen = _redis_safe("SET", seen_key, "1", "NX", "EX", "86400")
            # Upstash REST: SET NX で既存キーがある場合 result=null、新規なら "OK"
            if seen and isinstance(seen, dict) and seen.get("result") != "OK":
                _log(f"webhook: duplicate event {event_id} ({event_type}) ignored")
                _json(self, 200, {"received": True, "duplicate": True})
                return

            handler_fn = HANDLERS.get(event_type)
            if handler_fn:
                try:
                    handler_fn(event)
                except _RetryLater as e:
                    # 入塾の初回決済で名簿を KV に書けなかった → 500 を返して Stripe に再送してもらう (seen キーも書けていないので再送は弾かれない)
                    _log(f"webhook handler retry-later ({event_type}): {e!r}")
                    _redis_safe("DEL", f"webhook:seen:{event_id}")
                    _json(self, 500, {"error": "RETRY_LATER", "type": event_type})
                    return
                except Exception as e:
                    _log(f"webhook handler error ({event_type}): {e!r}")
                    # Stripe には 200 を返す (本体は KV best-effort なので失敗してもリトライ要らない)
            else:
                _log(f"webhook: ignored event type {event_type}")

            _json(self, 200, {"received": True, "type": event_type})
        except Exception as e:
            _log(f"webhook internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR"})
