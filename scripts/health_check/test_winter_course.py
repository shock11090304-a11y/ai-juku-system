#!/usr/bin/env python3
"""❄️ 冬期講習2026 (/api/winter/checkout・本体 webhook の記録・視聴ページの講習対応・配信のお知らせ) の回帰テスト。
in-process・一時 SQLite。Stripe (Checkout の作成・顧客の検索) は偽物、メールは記録器 (ネットワーク不要)。

  A. 料金: 高3の講座は「いちばん安いセット＋バラ」(申込ページの h3Plan と同じ)。全組み合わせを総当たりと照合。締切 (JST の日付)
  B. 決済の入口: フォーム送信 → Stripe Checkout へ 303。金額・metadata (session と payment_intent)・有効期限。だめなときは日本語の HTML
  C. 支払い完了の記録: winter_purchases に 1 行・ログインリンクのメール 1 通・再送で 2 行目もメールも作らない・月額講座の受講者を変えない
  D. 視聴ページ: 講習だけの人もログインできる・自分の講座の動画だけ・配信日前は出ない
  E. お知らせ: 動画の登録 (notify) は買った人だけ・配信日の朝のまとめは 1 人 1 通で、同じ動画は 2 回知らせない
  F. 返金 (refunded)・視聴期間の終わりで入れなくなる / 管理 API は認証必須
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import itertools
import json
import os
import sys
import tempfile
import time
import urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="winter_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "sk_test_dummy_for_winter", "STRIPE_WEBHOOK_SECRET": "",
        "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "re_dummy", "BASE_URL": "https://example.invalid", "WINTER_SITE_URL": "https://winter.example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_winter", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


class FakeStripe:
    """get_stripe() の代わり。checkout.Session.create の引数を記録して URL を返す。"""
    def __init__(self):
        self.created = []
        self.fail = False
        outer = self

        class _Session:
            @staticmethod
            def create(**kw):
                if outer.fail:
                    raise RuntimeError("stripe down")
                outer.created.append(kw)
                return {"id": f"cs_test_{len(outer.created)}", "url": f"https://checkout.stripe.com/c/pay/cs_test_{len(outer.created)}"}

        class _Checkout:
            Session = _Session
        self.checkout = _Checkout


def main():
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    print("❄️ 冬期講習2026 回帰テスト")

    # ---- 偽 Stripe / 偽メール ----
    STRIPE = {"monthly@example.invalid": {"courses": ["bunpo"], "customer_id": "cus_m1", "name": "月額 花子"}}
    def fake_fetch(email, customer_id=""):
        if email in STRIPE:
            return dict(STRIPE[email], found=True)
        return {"courses": [], "customer_id": "", "name": "", "found": False}
    mod._course_fetch_from_stripe = fake_fetch
    MAILS = []
    mod._course_send_email = lambda to, subject, body: (MAILS.append({"to": to, "subject": subject, "body": body}) or {"sent": True, "resend_id": "re_x"})
    mod._email_rate_limit = lambda *a, **k: None
    fake = FakeStripe()
    _orig_get_stripe = mod.get_stripe
    mod.get_stripe = lambda: fake
    ADMIN = {"Authorization": "Bearer " + admin_token(mod)}
    REAL_TODAY = mod._winter_today
    def set_today(d):
        mod._winter_today = (lambda: d) if d else REAL_TODAY
        mod._course_today_jst = (lambda: d) if d else (lambda: datetime.datetime.now(mod.JST).strftime("%Y-%m-%d"))

    # ---- A. 料金 ----
    P = lambda skus, today="2026-11-20": mod._winter_plan(skus, today)
    a1 = P(["h3-k", "h3-r", "h3-l"])
    check("A1. R＋L＋古文漢文 → 英語セット＋古文漢文 = 21,300円", a1["parts"] == ["h3-set-ei", "h3-k"] and a1["total"] == 21300, a1)
    a2 = P(["h3-r", "h3-l", "h3-k", "h3-m", "h3-b"])
    check("A2. 5 講座 → 全5講座セット 29,800円", a2["parts"] == ["h3-set-all5"] and a2["total"] == 29800, a2)
    a3 = P(["h3-r", "h3-k", "h3-m", "h3-b"])
    check("A3. セットを含まない 4 講座はバラ 30,000円 (切り替えはページの提案)", a3["parts"] == ["h3-r", "h3-k", "h3-m", "h3-b"] and a3["total"] == 30000, a3)
    a4 = P(["u-kansai", "h3-r", "h3-l", "pack-c3", "u-kansai"])
    check("A4. 重複は 1 つに・高3セット＋パックは並び順どおり", a4["parts"] == ["h3-set-ei", "pack-c3", "u-kansai"] and a4["total"] == 13800 + 15000 + 14500, a4)
    check("A5. 知らない sku は unknown", P(["h3-r", "zzz"])["unknown"] == ["zzz"])
    # 総当たり: 高3 の 31 通りすべてで「重ならないセットの組＋バラ」の最安と一致
    h3 = ["h3-r", "h3-l", "h3-k", "h3-m", "h3-b"]
    bad = []
    for n in range(1, 6):
        for sel in itertools.combinations(h3, n):
            best = sum(mod.WINTER_ITEMS[k]["price"] for k in sel)
            for m in range(1, 4):
                for bs in itertools.combinations(mod.WINTER_BUNDLES.values(), m):
                    used = [k for b in bs for k in b["items"]]
                    if len(used) != len(set(used)) or not set(used) <= set(sel):
                        continue
                    best = min(best, sum(b["price"] for b in bs) + sum(mod.WINTER_ITEMS[k]["price"] for k in sel if k not in used))
            got = P(list(sel))
            if got["total"] != best or sum(mod._winter_part_price(p) for p in got["parts"]) != got["total"]:
                bad.append((sel, got["total"], best))
    check("A6. 高3の 31 通りすべて最安・明細の合計 = total", not bad, bad)
    check("A7. 1/12 は共通テストの講座もセットも買える", not P(["h3-r", "h3-l"], "2027-01-12")["closed"] and P(["h3-r", "h3-l"], "2027-01-12")["parts"] == ["h3-set-ei"])
    a8 = P(["h3-r", "h3-b"], "2027-01-13")
    check("A8. 1/13 は共通テストの講座が締切・私大文法は買える", a8["closed"] == ["h3-r"], a8)
    check("A9. 大学別の締切 (関西大 1/25 まで・1/26 から締切)", not P(["u-kansai"], "2027-01-25")["closed"] and P(["u-kansai"], "2027-01-26")["closed"] == ["u-kansai"])
    check("A10. 18 大学・高3 5・パック 3 = 26 講座", len(mod.WINTER_ITEMS) == 26 and sum(1 for k in mod.WINTER_ITEMS if k.startswith("u-")) == 18)
    # 有効期限: 23 時間を上限に、締切の 23:59:59 JST を越えない・最低 31 分
    now = int(datetime.datetime(2027, 1, 12, 23, 50, tzinfo=mod.JST).timestamp())
    check("A11. 締切 10 分前の決済画面は 31 分 (Stripe の下限)", mod._winter_expires_at(["h3-set-ei"], now) == now + 31 * 60)
    now2 = int(datetime.datetime(2027, 1, 12, 12, 0, tzinfo=mod.JST).timestamp())
    check("A12. 締切当日の昼は 23:59:59 JST まで", mod._winter_expires_at(["h3-r"], now2) == int(datetime.datetime(2027, 1, 12, 23, 59, 59, tzinfo=mod.JST).timestamp()))
    now3 = int(datetime.datetime(2026, 11, 20, 12, 0, tzinfo=mod.JST).timestamp())
    check("A13. 締切が先なら 23 時間", mod._winter_expires_at(["h3-r", "u-keio-kei"], now3) == now3 + 23 * 3600)

    # ---- B. 決済の入口 ----
    def post_form(fields, **kw):
        body = urllib.parse.urlencode(fields, doseq=True)
        return client.post("/api/winter/checkout", content=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, follow_redirects=False, **kw)
    set_today("2026-11-20")
    r = post_form({"items": ["h3-r,h3-l", "u-kansai"], "email": " Buyer@Example.invalid ", "app_id": "W26-abc123", "page": "winter"})
    kw = fake.created[-1] if fake.created else {}
    check("B1. 303 で Stripe の決済画面へ", r.status_code == 303 and r.headers.get("location", "").startswith("https://checkout.stripe.com/"), (r.status_code, r.text[:200]))
    amts = [li["price_data"]["unit_amount"] for li in kw.get("line_items", [])]
    names = [li["price_data"]["product_data"]["name"] for li in kw.get("line_items", [])]
    check("B2. 明細 = 英語セット 13,800＋関西大 14,500 (円・1 個ずつ)", amts == [13800, 14500] and all(li["quantity"] == 1 and li["price_data"]["currency"] == "jpy" for li in kw.get("line_items", [])), (amts, names))
    meta = kw.get("metadata") or {}
    check("B3. metadata (session と payment_intent の両方に system=juku-payment-winter・items・plan・total・app_id)",
          meta.get("system") == "juku-payment-winter" and meta.get("items") == "h3-r,h3-l,u-kansai" and meta.get("plan") == "h3-set-ei,u-kansai"
          and meta.get("total") == "28300" and meta.get("app_id") == "W26-abc123" and (kw.get("payment_intent_data") or {}).get("metadata") == meta, kw)
    check("B4. メールは小文字・カードのみ・日本語・戻り先は Netlify のページ",
          kw.get("customer_email") == "buyer@example.invalid" and kw.get("payment_method_types") == ["card"] and kw.get("locale") == "ja"
          and kw.get("mode") == "payment"
          and kw.get("success_url") == "https://winter.example.invalid/winter-thanks.html?session_id={CHECKOUT_SESSION_ID}"
          and kw.get("cancel_url") == "https://winter.example.invalid/winter.html?canceled=1" and kw.get("client_reference_id") == "winter-W26-abc123", kw)
    n_before = len(fake.created)
    bads = [
        ("B5. メールの形が違う → 400", {"items": "h3-r", "email": "not-an-email", "page": "winter"}, 400, "メールアドレス"),
        ("B6. 知らない講座 → 400", {"items": "h3-r,evil", "email": "a@example.invalid"}, 400, "講座の指定"),
        ("B7. 講座なし → 400", {"items": "", "email": "a@example.invalid", "page": "winter-chugaku"}, 400, "講座が選ばれていません"),
    ]
    for label, fields, code, text in bads:
        rr = post_form(fields)
        check(label, rr.status_code == code and text in rr.text and "text/html" in rr.headers.get("content-type", ""), (rr.status_code, rr.text[:300]))
    check("B7b. 中学版から来たら戻り先も中学版", "winter-chugaku.html" in post_form({"items": "", "email": "a@example.invalid", "page": "winter-chugaku"}).text)
    set_today("2027-01-13")
    rr = post_form({"items": "h3-r,h3-b", "email": "late@example.invalid"})
    check("B8. 締切を過ぎた講座を含むと 400 (講座名つき)・決済画面は作らない", rr.status_code == 400 and "締切" in rr.text and "共通テスト英語リーディング" in rr.text and len(fake.created) == n_before, rr.text[:300])
    rr = post_form({"items": "h3-b", "email": "late@example.invalid"})
    check("B9. 1/13 でも私大文法だけなら作れる (7,500円)", rr.status_code == 303 and [li["price_data"]["unit_amount"] for li in fake.created[-1]["line_items"]] == [7500])
    set_today("2026-11-20")
    fake.fail = True
    rr = post_form({"items": "h3-r", "email": "x@example.invalid"})
    check("B10. Stripe の失敗は 502 の HTML", rr.status_code == 502 and "お支払いの画面を用意できませんでした" in rr.text, rr.status_code)
    fake.fail = False
    os.environ["WINTER_CHECKOUT_ENABLED"] = "0"
    rr = post_form({"items": "h3-r", "email": "x@example.invalid"})
    check("B11. WINTER_CHECKOUT_ENABLED=0 で止まる (503)", rr.status_code == 503, rr.status_code)
    os.environ["WINTER_CHECKOUT_ENABLED"] = "1"
    codes = [post_form({"items": "h3-r", "email": "spam@example.invalid"}).status_code for _ in range(11)]
    check("B12. 同じメールは 10 分に 10 回まで (11 回目は 429 の HTML)", codes[:10] == [303] * 10 and codes[10] == 429, codes)

    # ---- C. 支払い完了の記録 ----
    MAILS.clear()
    sess = {"id": "cs_live_w1", "object": "checkout.session", "payment_status": "paid", "livemode": True, "amount_total": 28300,
            "customer_details": {"email": "Buyer@Example.invalid", "name": "冬期 太郎"},
            "metadata": {"system": "juku-payment-winter", "items": "h3-r,h3-l,u-kansai", "plan": "h3-set-ei,u-kansai", "total": "28300", "app_id": "W26-abc123"}}
    mod._winter_webhook_record(sess)
    mod._winter_webhook_record(dict(sess))   # Stripe の再送・別イベント
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT * FROM winter_purchases"); rows = c.fetchall()
    c.execute("SELECT COUNT(*) AS n FROM students"); n_students = c.fetchone()["n"]
    conn.close()
    check("C1. 1 行だけ記録 (メールは小文字・講座・明細・金額)", len(rows) == 1 and rows[0]["email"] == "buyer@example.invalid"
          and json.loads(rows[0]["item_keys"]) == ["h3-r", "h3-l", "u-kansai"] and json.loads(rows[0]["plan"]) == ["h3-set-ei", "u-kansai"]
          and rows[0]["amount"] == 28300 and rows[0]["status"] == "paid", [dict(r) for r in rows])
    check("C2. students は増えない", n_students == 0, n_students)
    bm = mod._course_member_by_email("buyer@example.invalid")
    check("C3. course_members に講習だけの行 (status=canceled・courses=[])", bm and bm["status"] == "canceled" and bm["courses"] == [] and bm["name"] == "冬期 太郎", bm)
    check("C4. 案内メールは 1 通 (講座名・配信日・合計・ログインリンク)", len(MAILS) == 1 and MAILS[0]["to"] == "buyer@example.invalid"
          and "28,300円" in MAILS[0]["body"] and "大学別パック 関西大学" in MAILS[0]["body"] and "12月12日（土）" in MAILS[0]["body"]
          and "course-videos.html?t=" in MAILS[0]["body"] and "3月31日（水）" in MAILS[0]["body"], MAILS)
    welcome_link = [l for l in MAILS[0]["body"].splitlines() if "course-videos.html?t=" in l] if MAILS else []
    # 月額講座の受講者が講習も買う → 月額講座はそのまま
    mod._course_upsert_member("monthly@example.invalid", ["bunpo"], "cus_m1", "月額 花子")
    mod._winter_webhook_record({"id": "cs_live_w2", "payment_status": "paid", "amount_total": 7500, "customer_email": "monthly@example.invalid",
                                "metadata": {"system": "juku-payment-winter", "items": "h3-b", "plan": "h3-b"}})
    mm = mod._course_member_by_email("monthly@example.invalid")
    check("C5. 月額講座の受講者が講習を買っても月額講座は有効のまま", mm["status"] == "active" and mm["courses"] == ["bunpo"], mm)
    MAILS.clear()
    mod._winter_webhook_record({"id": "cs_bad", "payment_status": "paid", "customer_email": "x@example.invalid", "metadata": {"system": "juku-payment-winter", "items": "evil"}})
    check("C6. 講座の無い metadata は記録しない・送らない", not MAILS and not mod._winter_keys_for_email("x@example.invalid"))

    MAILS.clear()
    r_test = mod._winter_webhook_record({"id": "cs_test_t1", "livemode": False, "payment_status": "paid", "customer_email": "testmode@example.invalid",
                                         "metadata": {"system": "juku-payment-winter", "items": "h3-r", "plan": "h3-r"}})
    check("C7. テストモードの決済は記録しない (True で再送させない)", r_test is True and not mod._winter_keys_for_email("testmode@example.invalid") and not MAILS)
    conn = mod.db(); conn.cursor().execute("ALTER TABLE winter_purchases RENAME TO winter_purchases_tmp"); conn.commit(); conn.close()
    r_fail = mod._winter_webhook_record({"id": "cs_live_fail", "payment_status": "paid", "customer_email": "fail@example.invalid",
                                         "metadata": {"system": "juku-payment-winter", "items": "h3-r", "plan": "h3-r"}})
    conn = mod.db(); conn.cursor().execute("ALTER TABLE winter_purchases_tmp RENAME TO winter_purchases"); conn.commit(); conn.close()
    check("C8. 記録そのものに失敗したら False (webhook が 500 で Stripe に再送させる)・メールは送らない", r_fail is False and not MAILS, r_fail)
    # 取りこぼしの補い (Stripe の Checkout Session 一覧から)
    class _L(list):
        def auto_paging_iter(self):
            return iter(self)
    LIST_ARGS = []
    def _list(**kw):
        LIST_ARGS.append(kw)
        return _L([{"id": "cs_live_w1", "payment_status": "paid", "metadata": {"system": "juku-payment-winter", "items": "h3-r"}},
                   {"id": "cs_live_missed", "payment_status": "paid", "amount_total": 7500, "livemode": True, "customer_details": {"email": "missed@example.invalid", "name": ""},
                    "metadata": {"system": "juku-payment-winter", "items": "h3-k", "plan": "h3-k"}},
                   {"id": "cs_live_unpaid", "payment_status": "unpaid", "metadata": {"system": "juku-payment-winter", "items": "h3-m"}},
                   {"id": "cs_other", "payment_status": "paid", "metadata": {"system": "juku-payment-course"}}])
    fake.checkout.Session.list = staticmethod(_list)
    s1 = mod._winter_sync_from_stripe(days=7, dry_run=True)
    s2 = mod._winter_sync_from_stripe(days=7, dry_run=False)
    s3 = mod._winter_sync_from_stripe(days=7, dry_run=False)
    check("C9. Stripe から取りこぼしを補う (dry_run は数えるだけ・2 回目は 0)", s1["missing"] == 1 and s1["recorded"] == 0 and s2["recorded"] == 1 and s3["missing"] == 0
          and mod._winter_keys_for_email("missed@example.invalid") == ["w26-h3-k"] and "gte" in LIST_ARGS[0].get("created", {}), (s1, s2, s3))
    sy = client.post("/api/admin/winter/sync", json={"dry_run": True})
    check("C10. 補いの API は認証必須", sy.status_code == 401, sy.status_code)

    # ---- D. 視聴ページ ----
    tok = welcome_link[0].split("?t=", 1)[1].strip() if welcome_link else ""
    vr = client.post("/api/course/login/verify", json={"token": tok})
    check("D1. 案内メールのリンクで講習だけの人もログインできる", vr.status_code == 200 and [c["key"] for c in vr.json().get("courses", [])] == ["w26-h3-r", "w26-h3-l", "w26-u-kansai"], vr.text[:300])
    H = {"Authorization": "Bearer " + (vr.json().get("token") or "")} if vr.status_code == 200 else {}
    # 動画: 高3R (公開済み)・関西大 (12/19 配信)・月額 bunpo・買っていない高3数学
    def add(key, title, yid, pub, notify=True):
        return client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": key, "title": title, "youtube_url": "https://youtu.be/" + yid, "publish_date": pub, "notify": notify})
    MAILS.clear()
    ra = add("w26-h3-r", "共テR 第1回", "RRRRRRRRRR1", "2026-11-20", notify=True)
    check("E1. 講習の講座に動画を登録できる・登録と同時の通知は買った人だけ (1 通)", ra.status_code == 200 and ra.json()["notified"]["sent"] == 1
          and [m["to"] for m in MAILS] == ["buyer@example.invalid"] and "共通テスト英語リーディング" in MAILS[0]["subject"], (ra.text[:200], [m["to"] for m in MAILS]))
    add("w26-u-kansai", "関西大 第1回", "KKKKKKKKKK1", "2026-12-19")
    add("w26-u-kansai", "関西大 第2回", "KKKKKKKKKK2", "2026-12-19")
    add("w26-h3-m", "共テ数学 第1回", "MMMMMMMMMM1", "2026-11-20")
    add("bunpo", "英文法 第1回", "BBBBBBBBBB1", "2026-11-20")
    check("D2. 不正な講座キーは 400", add("w26-nope", "x", "XXXXXXXXXX1", "2026-11-20").status_code == 400)
    me = client.get("/api/course/me", headers=H)
    vids = [v["title"] for v in me.json().get("videos", [])] if me.status_code == 200 else []
    check("D3. /me は自分の講習の公開済み動画だけ (配信日前・買っていない講座・月額講座は出ない)", me.status_code == 200 and vids == ["共テR 第1回"], (me.status_code, vids))
    wi = me.json().get("winter") if me.status_code == 200 else None
    check("D4. /me に講習の講座と配信日・視聴期限", wi and [(w["key"], w["delivery"]) for w in wi] == [("w26-h3-r", "2026-12-12"), ("w26-h3-l", "2026-12-12"), ("w26-u-kansai", "2026-12-19")]
          and me.json().get("winter_view_until") == "2027-03-31", me.text[:300])
    MAILS.clear()
    lr = client.post("/api/course/login/request", json={"email": "buyer@example.invalid"})
    check("D5. ログインリンクの再送も講習だけの人に届く", lr.status_code == 200 and len(MAILS) == 1 and "course-videos.html?t=" in MAILS[0]["body"], MAILS)
    # 月額講座の受講者は月額講座＋講習の両方
    MAILS.clear()
    client.post("/api/course/login/request", json={"email": "monthly@example.invalid"})
    mlink = [l for l in MAILS[0]["body"].splitlines() if "course-videos.html?t=" in l] if MAILS else []
    mv = client.post("/api/course/login/verify", json={"token": mlink[0].split("?t=", 1)[1].strip() if mlink else ""})
    check("D6. 月額講座＋講習の人は両方の講座", mv.status_code == 200 and [c["key"] for c in mv.json()["courses"]] == ["bunpo", "w26-h3-b"], mv.text[:300])
    adm = client.get("/api/admin/course/videos", headers=ADMIN).json()
    wc = {c["key"]: c["active_members"] for c in adm.get("winter_courses", [])}
    check("D7. CEO の一覧に講習の講座と購入者数 (月額講座の欄は変えない)", wc.get("w26-h3-r") == 1 and wc.get("w26-h3-b") == 1 and wc.get("w26-h3-m") == 0
          and [c["key"] for c in adm["courses"]] == list(mod.COURSE_KEYS), wc)
    vnames = {v["title"]: v["course_name"] for v in adm["videos"]}
    check("D8. 動画の講座名は講習の講座名", vnames.get("関西大 第1回") == "大学別パック 関西大学（全学部）", vnames)
    am = {m["email"]: m for m in client.get("/api/admin/course/members", headers=ADMIN).json()["members"]}
    check("D9. 受講者一覧に講習の講座名", am["buyer@example.invalid"]["winter_names"][0] == "共通テスト英語リーディング 本番形式演習", am.get("buyer@example.invalid"))

    # 教材 (PDF) の URL: 動画ごと・視聴ページ (/me) だけに出す
    vid_r = [v["id"] for v in adm["videos"] if v["title"] == "共テR 第1回"][0]
    bad = client.patch(f"/api/admin/course/videos/{vid_r}", headers=ADMIN, json={"material_url": "javascript:alert(1)"})
    bad2 = client.patch(f"/api/admin/course/videos/{vid_r}", headers=ADMIN, json={"material_url": "http://example.invalid/a.pdf"})
    check("D10. 教材の URL は https:// だけ (javascript:・http:// は 400)", bad.status_code == 400 and bad2.status_code == 400, (bad.status_code, bad2.status_code))
    pdf = "https://drive.google.com/file/d/abcDEF123/view?usp=sharing"
    ok = client.patch(f"/api/admin/course/videos/{vid_r}", headers=ADMIN, json={"material_url": pdf})
    mev = {v["title"]: v for v in client.get("/api/course/me", headers=H).json()["videos"]}
    check("D11. 教材の URL を付けると /me の動画に material_url が出る", ok.status_code == 200 and mev["共テR 第1回"].get("material_url") == pdf, mev)
    adm2 = {v["title"]: v for v in client.get("/api/admin/course/videos", headers=ADMIN).json()["videos"]}
    check("D12. CEO の一覧にも material_url (付けていない動画は空)", adm2["共テR 第1回"]["material_url"] == pdf and adm2["関西大 第1回"]["material_url"] == "", adm2.get("関西大 第1回"))
    rc = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "w26-h3-l", "title": "共テL 第1回", "youtube_url": "https://youtu.be/LLLLLLLLLL1",
                                                                      "publish_date": "2026-12-12", "notify": False, "material_url": "  https://example.invalid/l1.pdf  "})
    rcb = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "w26-h3-l", "title": "共テL 第2回", "youtube_url": "https://youtu.be/LLLLLLLLLL2",
                                                                       "publish_date": "2026-12-12", "notify": False, "material_url": "ftp://x/y.pdf"})
    adm3 = {v["title"]: v for v in client.get("/api/admin/course/videos", headers=ADMIN).json()["videos"]}
    check("D13. 登録と同時に教材の URL (前後の空白は落とす)・不正な URL は登録しない", rc.status_code == 200 and adm3["共テL 第1回"]["material_url"] == "https://example.invalid/l1.pdf"
          and rcb.status_code == 400 and "共テL 第2回" not in adm3, (rc.text[:200], rcb.status_code))
    clr = client.patch(f"/api/admin/course/videos/{vid_r}", headers=ADMIN, json={"material_url": ""})
    mev2 = {v["title"]: v for v in client.get("/api/course/me", headers=H).json()["videos"]}
    check("D14. 空で送ると教材を外せる", clr.status_code == 200 and mev2["共テR 第1回"].get("material_url") == "", mev2)
    client.patch(f"/api/admin/course/videos/{vid_r}", headers=ADMIN, json={"material_url": pdf})

    # 二重払いの確認画面
    n0 = len(fake.created)
    dupr = post_form({"items": "h3-r,h3-m", "email": "buyer@example.invalid", "page": "winter"})
    check("B13. 支払い済みの講座を含むと確認画面 (決済画面は作らない・講座名と「このまま支払いへ進む」)", dupr.status_code == 200 and "すでにお支払い済み" in dupr.text
          and "共通テスト英語リーディング" in dupr.text and 'name="confirm_dup" value="1"' in dupr.text and len(fake.created) == n0, dupr.text[:300])
    dupok = post_form({"items": "h3-r,h3-m", "email": "buyer@example.invalid", "page": "winter", "confirm_dup": "1"})
    check("B14. 「このまま支払いへ進む」(confirm_dup=1) なら作る", dupok.status_code == 303 and len(fake.created) == n0 + 1)
    # 「知らせる」を外して登録した講習の動画は朝のまとめでも送らない
    add("w26-u-kansai", "関西大 おまけ（知らせない）", "KKKKKKKKKK9", "2026-12-19", notify=False)

    # ---- E. 配信日の朝のまとめ ----
    set_today("2026-12-19")
    dry = mod._winter_notify_due(dry_run=True)
    check("E2. dry_run は送らずに数だけ (関西大 2 本 → 1 人)", dry["recipients"] == 1 and dry["videos"] == 2 and not MAILS[1:], dry)
    MAILS.clear()
    res = mod._winter_notify_due()
    check("E3. 1 人 1 通にまとめる (R 第1回は登録時に知らせ済みなので入らない)", res["sent"] == 1 and len(MAILS) == 1 and "関西大 第1回" in MAILS[0]["body"]
          and "関西大 第2回" in MAILS[0]["body"] and "共テR 第1回" not in MAILS[0]["body"] and "（2本）" in MAILS[0]["subject"]
          and "おまけ" not in MAILS[0]["body"], (res, MAILS))
    dl = [l for l in MAILS[0]["body"].splitlines() if "course-videos.html?t=" in l] if MAILS else []
    check("E3b. まとめのメールにログインリンク (そのまま入れる)", len(dl) == 1 and client.post("/api/course/login/verify", json={"token": dl[0].split("?t=", 1)[1].strip()}).status_code == 200, dl)
    MAILS.clear()
    check("E4. 2 回目は送らない", mod._winter_notify_due()["sent"] == 0 and not MAILS)
    me2 = client.get("/api/course/me", headers=H)
    check("E5. 配信日になると /me に並ぶ (知らせない印の動画も視聴はできる)", sorted(v["title"] for v in me2.json().get("videos", [])) == ["共テL 第1回", "共テR 第1回", "関西大 おまけ（知らせない）", "関西大 第1回", "関西大 第2回"], me2.text[:300])
    # 配信後に買った人: 案内メールで公開済みの動画を知らせ、朝のまとめでは送らない
    MAILS.clear()
    mod._winter_webhook_record({"id": "cs_live_w3", "payment_status": "paid", "amount_total": 14500, "customer_details": {"email": "late@example.invalid", "name": ""},
                                "metadata": {"system": "juku-payment-winter", "items": "u-kansai", "plan": "u-kansai"}})
    check("E6. 配信後の購入は案内メールに「すでに配信している動画（3本）」", len(MAILS) == 1 and "すでに配信している動画（3本）" in MAILS[0]["body"], MAILS)
    MAILS.clear()
    check("E7. その人に朝のまとめで同じ動画を送らない", mod._winter_notify_due()["sent"] == 0 and not MAILS)

    # Stripe 照会の全体枠を使い切っても、講習の購入者にはログインリンクが届く
    for _ in range(31):
        try:
            mod._check_rate_limit_value("*", bucket="course_login_stripe", limit=30, window=60)
        except Exception:
            pass
    conn = mod.db(); c = conn.cursor(); c.execute("UPDATE course_members SET verified_at = ? WHERE email = ?", ("2020-01-01T00:00:00", "late@example.invalid")); conn.commit(); conn.close()
    MAILS.clear()
    client.post("/api/course/login/request", json={"email": "late@example.invalid"})
    check("E8. Stripe 照会の枠が尽きても講習の購入者にはリンクを送る", len(MAILS) == 1 and MAILS[0]["to"] == "late@example.invalid", MAILS)

    # ---- F. 返金・視聴期間・認証 ----
    pid = [p for p in client.get("/api/admin/winter/purchases", headers=ADMIN).json()["purchases"] if p["email"] == "buyer@example.invalid"][0]["id"]
    st = client.post(f"/api/admin/winter/purchases/{pid}/status", headers=ADMIN, json={"status": "refunded"})
    check("F1. refunded にすると講習だけの人は /me が 401", st.status_code == 200 and client.get("/api/course/me", headers=H).status_code == 401, st.text[:200])
    client.post(f"/api/admin/winter/purchases/{pid}/status", headers=ADMIN, json={"status": "paid"})
    check("F2. paid に戻すと入れる", client.get("/api/course/me", headers=H).status_code == 200)
    set_today("2027-04-01")
    check("F3. 視聴期間 (3/31) を過ぎると講習だけの人は 401・月額講座の人は月額講座だけ",
          client.get("/api/course/me", headers=H).status_code == 401
          and [c["key"] for c in client.get("/api/course/me", headers={"Authorization": "Bearer " + mv.json().get("token", "")}).json().get("courses", [])] == ["bunpo"])
    set_today("2026-12-19")
    pl = client.get("/api/admin/winter/purchases", headers=ADMIN).json()
    check("F4. 購入一覧 (合計・講座ごとの人数)", pl["paid_total"] == 28300 + 7500 + 14500 + 7500 and {i["sku"]: i["buyers"] for i in pl["items"]}["u-kansai"] == 2, pl.get("paid_total"))
    codes = [client.get("/api/admin/winter/purchases").status_code, client.post("/api/admin/winter/notify-due", json={"dry_run": False}).status_code,
             client.post(f"/api/admin/winter/purchases/{pid}/status", json={"status": "refunded"}).status_code,
             client.get("/api/admin/winter/purchases", headers=H).status_code]
    check("F5. 管理 API は認証なし・受講者の token では 401", all(c == 401 for c in codes), codes)
    rr1 = client.post(f"/api/admin/winter/purchases/{pid}/status", headers=ADMIN, json={"remove_items": ["u-kansai"]})
    keys_after = mod._winter_keys_for_email("buyer@example.invalid")
    check("F7. 講座ごとの返金: 関西大だけ外れる (残りは見られる)", rr1.status_code == 200 and rr1.json()["status"] == "paid" and keys_after == ["w26-h3-r", "w26-h3-l"], (rr1.text[:200], keys_after))
    rr2 = client.post(f"/api/admin/winter/purchases/{pid}/status", headers=ADMIN, json={"remove_items": ["u-kansai"]})
    rr3 = client.post(f"/api/admin/winter/purchases/{pid}/status", headers=ADMIN, json={"remove_items": ["h3-r", "h3-l"]})
    check("F8. 含まれない講座は 400・全部外すと refunded", rr2.status_code == 400 and rr3.json().get("status") == "refunded" and not mod._winter_keys_for_email("buyer@example.invalid"), (rr2.status_code, rr3.text[:200]))
    check("F6. 不正な status は 400", client.post(f"/api/admin/winter/purchases/{pid}/status", headers=ADMIN, json={"status": "deleted"}).status_code == 400)

    # ---- G. 署名付き webhook (本体 /api/stripe/webhook) ----
    mod.get_stripe = _orig_get_stripe
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_winter"
    mod.STRIPE_WEBHOOK_SECRET = "whsec_test_winter"
    import stripe as _stripe_lib
    if int(str(getattr(_stripe_lib, "VERSION", "0")).split(".")[0] or 0) >= 14:
        print(f"  ⏭ G. 署名付き webhook: stripe {_stripe_lib.VERSION} ではスキップ (CI の 11.x で実行)")
    else:
        payload = json.dumps({"id": "evt_winter_1", "object": "event", "api_version": "2024-06-20", "created": int(time.time()), "livemode": True,
                              "type": "checkout.session.completed", "data": {"object": {"object": "checkout.session", "id": "cs_wh_w1",
                              "payment_status": "paid", "amount_total": 7500, "customer_details": {"email": "wh@example.invalid", "name": ""},
                              "metadata": {"system": "juku-payment-winter", "items": "h3-m", "plan": "h3-m"}}}}).encode()
        ts = int(time.time()); sig = hmac.new(b"whsec_test_winter", f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
        wr = client.post("/api/stripe/webhook", content=payload, headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"})
        check("G1. 署名付き webhook → 記録し、応答は juku-payment skip", wr.status_code == 200 and wr.json().get("skipped_reason") == "juku-payment system tag"
              and mod._winter_keys_for_email("wh@example.invalid") == ["w26-h3-m"], (wr.status_code, wr.text[:200]))
        payload2 = payload.replace(b"evt_winter_1", b"evt_winter_2").replace(b"cs_wh_w1", b"cs_wh_w2").replace(b"wh@example", b"wh2@example")
        def _signed(pl):
            ts2 = int(time.time()); return {"Stripe-Signature": f"t={ts2},v1=" + hmac.new(b"whsec_test_winter", f"{ts2}.".encode() + pl, hashlib.sha256).hexdigest(), "Content-Type": "application/json"}
        conn = mod.db(); conn.cursor().execute("ALTER TABLE winter_purchases RENAME TO winter_purchases_tmp"); conn.commit(); conn.close()
        wf = client.post("/api/stripe/webhook", content=payload2, headers=_signed(payload2))
        conn = mod.db(); conn.cursor().execute("ALTER TABLE winter_purchases_tmp RENAME TO winter_purchases"); conn.commit(); conn.close()
        wr2 = client.post("/api/stripe/webhook", content=payload2, headers=_signed(payload2))
        check("G2. 記録に失敗したら 500 (Stripe が再送)・同じイベントの再送で記録できる", wf.status_code == 500 and wr2.status_code == 200
              and wr2.json().get("duplicate") is not True and mod._winter_keys_for_email("wh2@example.invalid") == ["w26-h3-m"], (wf.status_code, wr2.text[:200]))

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}"); sys.exit(1)
    print("✅ 全件 OK")


if __name__ == "__main__":
    main()
