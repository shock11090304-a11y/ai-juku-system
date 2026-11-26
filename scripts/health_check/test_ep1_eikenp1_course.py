#!/usr/bin/env python3
"""📗 英検準1級 4か月ステップアップ講座 (/api/ep1/checkout・本体 webhook の記録・人ごとの視聴期限・視聴ページ・お知らせ・返金) の回帰テスト。
in-process・一時 SQLite。Stripe は偽物、メールは記録器 (ネットワーク不要)。共通テスト過去問 (test_kt_kakomon_course.py) と同じ形。

  A. 料金と期限: 通常 29,800 円・質問つき 39,800 円・差額 10,000 円。期限 = 支払い日 + 5 か月 (月末は丸める)
  B. 決済の入口: 販売開始前は閉じる・フォーム送信 → Stripe へ 303 (明細・metadata・戻り先)・だめなときは日本語の HTML
  C. 記録: 1 行・案内メール・再送で増えない・テストモードは記録しない・質問つきは LINE の案内と塾長へのメール・記録失敗は False
  D. 視聴ページ: 講座だけの人もログインできる・期限を過ぎたら見られない・動画の登録とお知らせ
  E. 切りかえ: 通常の期間中に質問つき → 差額・期限はそのまま。同じコースは確認画面
  F. 返金・Stripe からの補い・管理 API (認証・期限の変更)
  G. 署名付き webhook (stripe 11.x の CI で実行)
  H. 画面と表記: 月謝アプリの取込で除外・視聴ページ・CEO の選択肢・特商法の金額
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import re
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
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="ep1_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "sk_test_dummy_for_ep1", "STRIPE_WEBHOOK_SECRET": "",
        "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "re_dummy", "BASE_URL": "https://example.invalid", "WINTER_SITE_URL": "https://site.example.invalid",
        "EP1_SALES_FROM": "",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_ep1", MAIN_PY)
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

            @staticmethod
            def list(**kw):
                return {"data": []}

        class _Checkout:
            Session = _Session
        self.checkout = _Checkout


def read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def main():
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    print("📗 英検準1級 4か月ステップアップ講座 回帰テスト")

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

    # ---- A. 料金と期限 ----
    check("A1. 通常 29,800 円・質問つき 39,800 円 (並び = 申込ページ)", list(mod.EP1_PRODUCTS) == ["ep1-std", "ep1-plus"]
          and mod.EP1_PRODUCTS["ep1-std"]["price"] == 29800 and mod.EP1_PRODUCTS["ep1-plus"]["price"] == 39800)
    am = mod._ep1_add_months
    check("A2. 期限 = +5 か月 (11/19→4/19・10/31→3/31・9/30→2/28・2027-09-30→2028-02-29 うるう年)",
          am("2026-11-19", 5) == "2027-04-19" and am("2026-10-31", 5) == "2027-03-31" and am("2026-09-30", 5) == "2027-02-28"
          and am("2027-09-30", 5) == "2028-02-29" and am("2027-08-31", 5) == "2028-01-31", [am("2026-09-30", 5), am("2027-09-30", 5)])
    check("A3. 講座キーは月額講座・冬期講習・過去問と重ならない", mod.EP1_COURSE_KEY not in mod.COURSE_KEYS and mod.EP1_COURSE_KEY not in mod.KT_COURSES
          and not mod._winter_is_video_key(mod.EP1_COURSE_KEY) and mod._course_key_name(mod.EP1_COURSE_KEY) == mod.EP1_COURSE_NAME)
    check("A4. 視聴は 5 か月", mod.EP1_VIEW_MONTHS == 5)

    # ---- B. 決済の入口 ----
    def post_form(fields):
        body = urllib.parse.urlencode(fields, doseq=True)
        return client.post("/api/ep1/checkout", content=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, follow_redirects=False)
    set_today("2027-01-10")
    rr = post_form({"course": "ep1-std", "email": "a@example.invalid"})
    check("B1. 販売開始前 (EP1_SALES_FROM が空) は 403・決済画面を作らない", rr.status_code == 403 and "まだお申し込みの受付を始めていません" in rr.text
          and not fake.created and "英検準1級 4か月ステップアップ講座" in rr.text and "冬期講習" not in rr.text, (rr.status_code, rr.text[:200]))
    mod.EP1_SALES_FROM = "2027-01-11"
    check("B2. 開始日の前日もまだ閉じている", post_form({"course": "ep1-std", "email": "a@example.invalid"}).status_code == 403 and not fake.created)
    mod.EP1_SALES_FROM = "2027-01-10"
    rv0 = post_form({"course": "ep1-std", "email": "a@example.invalid"})
    check("B2b. 公開中の動画が 1 本も無いときは売らない (503)", rv0.status_code == 503 and "準備中" in rv0.text and not fake.created, rv0.status_code)
    mod.EP1_SALES_FROM = "2027-1-9"
    check("B2c. EP1_SALES_FROM の形が違えば開かない", not mod._ep1_on_sale("2027-12-31"))
    mod.EP1_SALES_FROM = "2027-01-10"
    client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "ep1-step", "title": "第00週 はじめに", "youtube_url": "https://youtu.be/EEEEEEEEEE0",
                                                                "publish_date": "2027-01-01", "notify": False})
    t0 = int(time.time())
    r = post_form({"course": "ep1-std", "email": " Buyer@Example.invalid ", "app_id": "EP1-abc123"})
    kw = fake.created[-1] if fake.created else {}
    check("B3. 303 で Stripe の決済画面へ", r.status_code == 303 and r.headers.get("location", "").startswith("https://checkout.stripe.com/"), (r.status_code, r.text[:200]))
    li = (kw.get("line_items") or [{}])[0]
    check("B4. 明細 = 通常コース 29,800 円 1 つ", len(kw.get("line_items") or []) == 1 and li["price_data"]["unit_amount"] == 29800
          and li["price_data"]["product_data"]["name"].startswith("英検準1級 4か月ステップアップ講座 通常コース"), kw.get("line_items"))
    meta = kw.get("metadata") or {}
    check("B5. metadata (session と payment_intent の両方に system=juku-payment-eikenp1・plan・total・app_id)",
          meta.get("system") == "juku-payment-eikenp1" and meta.get("plan") == "ep1-std" and meta.get("total") == "29800"
          and meta.get("app_id") == "EP1-abc123" and (kw.get("payment_intent_data") or {}).get("metadata") == meta, kw)
    check("B6. メールは小文字・カードのみ・日本語・戻り先は eiken-p1 のページ・有効期限 23 時間",
          kw.get("customer_email") == "buyer@example.invalid" and kw.get("payment_method_types") == ["card"] and kw.get("locale") == "ja"
          and kw.get("mode") == "payment"
          and kw.get("success_url") == "https://site.example.invalid/eiken-p1-thanks.html?session_id={CHECKOUT_SESSION_ID}"
          and kw.get("cancel_url") == "https://site.example.invalid/eiken-p1.html?canceled=1" and kw.get("client_reference_id") == "ep1-EP1-abc123"
          and abs(kw.get("expires_at", 0) - (t0 + 23 * 3600)) < 60, kw)
    post_form({"course": "ep1-plus", "email": "plus@example.invalid"})
    check("B7. 質問つきは 39,800 円・plan=ep1-plus", fake.created[-1]["line_items"][0]["price_data"]["unit_amount"] == 39800
          and fake.created[-1]["metadata"]["plan"] == "ep1-plus")
    n_before = len(fake.created)
    for label, fields, code, text in [
        ("B8. メールの形が違う → 400", {"course": "ep1-std", "email": "not-an-email"}, 400, "メールアドレス"),
        ("B9. 知らないコース (ep1-upgrade を直接・過去問の sku も) → 400", {"course": "ep1-upgrade", "email": "a@example.invalid"}, 400, "コースが選ばれていません"),
        ("B10. コースなし → 400", {"course": "", "email": "a@example.invalid"}, 400, "コースが選ばれていません"),
    ]:
        rr = post_form(fields)
        check(label, rr.status_code == code and text in rr.text and "text/html" in rr.headers.get("content-type", "")
              and "https://site.example.invalid/eiken-p1.html" in rr.text, (rr.status_code, rr.text[:300]))
    check("B11. だめなときは決済画面を作らない", len(fake.created) == n_before)
    fake.fail = True
    rr = post_form({"course": "ep1-std", "email": "x@example.invalid"})
    check("B12. Stripe の失敗は 502 の HTML", rr.status_code == 502 and "お支払いの画面を用意できませんでした" in rr.text, rr.status_code)
    fake.fail = False
    os.environ["EP1_CHECKOUT_ENABLED"] = "0"
    check("B13. EP1_CHECKOUT_ENABLED=0 で止まる (503)", post_form({"course": "ep1-std", "email": "x@example.invalid"}).status_code == 503)
    os.environ["EP1_CHECKOUT_ENABLED"] = "1"

    # ---- C. 記録 ----
    conn = mod.db(); c = conn.cursor(); c.execute("SELECT COUNT(*) AS n FROM kt_purchases"); n_kt0 = c.fetchone()["n"]; conn.close()
    MAILS.clear()
    sess = {"id": "cs_live_e1", "object": "checkout.session", "payment_status": "paid", "livemode": True, "amount_total": 29800,
            "customer_details": {"email": "Buyer@Example.invalid", "name": "準一 太郎"},
            "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std", "total": "29800", "app_id": "EP1-abc123"}}
    r1 = mod._ep1_webhook_record(sess)
    r2 = mod._ep1_webhook_record(dict(sess))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT * FROM ep1_purchases"); rows = c.fetchall()
    c.execute("SELECT COUNT(*) AS n FROM kt_purchases"); n_kt = c.fetchone()["n"]
    conn.close()
    check("C1. 1 行だけ記録 (メールは小文字・plan・金額・期限 = 2027-01-10 + 5 か月)", r1 is True and r2 is True and len(rows) == 1
          and rows[0]["email"] == "buyer@example.invalid" and rows[0]["plan"] == "ep1-std" and rows[0]["amount"] == 29800
          and rows[0]["view_until"] == "2027-06-10" and rows[0]["status"] == "paid", [dict(x) for x in rows])
    welcome = [m for m in MAILS if m["to"] == "buyer@example.invalid"]
    check("C2. 案内メール 1 通 (ログインリンク・期限・通常コース・LINE の添削案内は無し)・塾長へは送らない", len(welcome) == 1 and "?t=" in welcome[0]["body"]
          and "2027年6月10日" in welcome[0]["body"] and "通常コース" in welcome[0]["body"] and "添削" not in welcome[0]["body"] and "テキストの PDF" in welcome[0]["body"]
          and "いまは 1 本を公開中" in welcome[0]["body"] and "全72本" in welcome[0]["body"]
          and not [m for m in MAILS if m["to"] == mod.COURSE_CONTACT_EMAIL], [m["subject"] for m in MAILS])
    welcome_link = [ln for ln in welcome[0]["body"].splitlines() if "?t=" in ln] if welcome else []
    check("C3. 過去問の表には混ざらない", n_kt == n_kt0)
    MAILS.clear()
    rp = mod._ep1_webhook_record({"id": "cs_live_p1", "payment_status": "paid", "livemode": True, "amount_total": 39800,
                                  "customer_details": {"email": "plus@example.invalid", "name": "質問 花子"},
                                  "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-plus"}})
    pw = [m for m in MAILS if m["to"] == "plus@example.invalid"]
    ow = [m for m in MAILS if m["to"] == mod.COURSE_CONTACT_EMAIL]
    check("C4. 質問つき: 案内に LINE の友だち追加・メールアドレスを送る・添削は3営業日・塾長に1通", rp is True and len(pw) == 1
          and mod.COURSE_LINE_URL in pw[0]["body"] and "メールアドレスを送って" in pw[0]["body"] and "3営業日" in pw[0]["body"] and "要約4回・意見論述4回" in pw[0]["body"] and "添削8回" in pw[0]["body"]
          and len(ow) == 1 and "質問つき" in ow[0]["subject"] and "plus@example.invalid" in ow[0]["body"], [m["subject"] for m in MAILS])
    MAILS.clear()
    rt = mod._ep1_webhook_record({"id": "cs_test_t1", "livemode": False, "payment_status": "paid", "customer_email": "testmode@example.invalid",
                                  "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}})
    check("C5. テストモードは記録しない・メールも送らない", rt is True and not mod._ep1_access("testmode@example.invalid")["until"] and not MAILS)
    MAILS.clear()
    ru = mod._ep1_webhook_record({"id": "cs_live_bad", "payment_status": "paid", "livemode": True, "customer_email": "bad@example.invalid",
                                  "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-zzz"}})
    check("C6. 知らない plan は記録せず塾長に知らせる", ru is True and not mod._ep1_access("bad@example.invalid")["until"]
          and len(MAILS) == 1 and MAILS[0]["to"] == mod.COURSE_CONTACT_EMAIL and "視聴を付けられない" in MAILS[0]["subject"], MAILS)
    conn = mod.db(); conn.cursor().execute("ALTER TABLE ep1_purchases RENAME TO ep1_purchases_tmp"); conn.commit(); conn.close()
    MAILS.clear()
    rf = mod._ep1_webhook_record({"id": "cs_live_fail", "payment_status": "paid", "livemode": True, "customer_email": "fail@example.invalid",
                                  "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}})
    conn = mod.db(); conn.cursor().execute("ALTER TABLE ep1_purchases_tmp RENAME TO ep1_purchases"); conn.commit(); conn.close()
    check("C7. 記録そのものに失敗したら False (webhook が 500 で再送させる)・メールは送らない", rf is False and not MAILS, rf)
    MAILS.clear()
    mod._course_upsert_member("monthly@example.invalid", ["bunpo"], "cus_m1", "月額 花子")
    rm = mod._ep1_webhook_record({"id": "cs_live_m1", "payment_status": "paid", "livemode": True, "amount_total": 29800,
                                  "customer_details": {"email": "monthly@example.invalid"}, "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}})
    mem = mod._course_member_by_email("monthly@example.invalid")
    check("C8. 月額講座の受講者が買っても月額講座はそのまま", rm is True and mem is not None and mem["status"] == "active" and mem["courses"] == ["bunpo"], mem)

    # ---- D. 視聴ページ ----
    tok = welcome_link[0].split("?t=", 1)[1].strip() if welcome_link else ""
    vr = client.post("/api/course/login/verify", json={"token": tok})
    check("D1. 案内メールのリンクで講座だけの人もログインできる", vr.status_code == 200 and [c["key"] for c in vr.json().get("courses", [])] == ["ep1-step"], vr.text[:300])
    H = {"Authorization": "Bearer " + (vr.json().get("token") or "")} if vr.status_code == 200 else {}
    def add(key, title, yid, pub, notify=True):
        return client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": key, "title": title, "youtube_url": "https://youtu.be/" + yid, "publish_date": pub, "notify": notify})
    MAILS.clear()
    ra = add("ep1-step", "第01週 ①講義", "EEEEEEEEEE1", "2027-01-10", notify=True)
    tos = sorted(m["to"] for m in MAILS)
    check("D2. 講座に動画を登録できる・登録と同時の通知は期間中の購入者だけ", ra.status_code == 200
          and tos == ["buyer@example.invalid", "monthly@example.invalid", "plus@example.invalid"], (ra.text[:200], tos))
    add("ep1-step", "第01週 ②演習A", "EEEEEEEEEE2", "2027-01-10", notify=False)
    add("ep1-step", "第02週 ①講義（先の公開日）", "EEEEEEEEEE3", "2027-02-01", notify=False)
    add("kt-r-2026", "英語R 2026", "KKKKKKKKKK1", "2027-01-10", notify=False)
    me = client.get("/api/course/me", headers=H)
    mj = me.json() if me.status_code == 200 else {}
    vids = sorted(v["title"] for v in mj.get("videos", []))
    check("D3. /me は講座の公開済み動画だけ (公開日前・過去問は出ない)", vids == ["第00週 はじめに", "第01週 ①講義", "第01週 ②演習A"], vids)
    check("D4. /me に講座と視聴期限 (準2級の講座は付かない)", mj.get("ep1") == [{"key": "ep1-step", "name": mod.EP1_COURSE_NAME}] and mj.get("ep1_view_until") == "2027-06-10"
          and not mj.get("kt") and not mj.get("winter") and not mj.get("ep2"), {k: mj.get(k) for k in ("ep1", "ep1_view_until", "ep2")})
    check("D4b. 準1級を買っても準2級は見られない・準2級の購入者の数にも入らない", not mod._ep2_keys_for_email("buyer@example.invalid")
          and "buyer@example.invalid" not in mod._ep2_buyers())
    set_today("2027-06-10")
    check("D5. 期限の日まではまだ見られる", mod._ep1_keys_for_email("buyer@example.invalid") == ["ep1-step"])
    set_today("2027-06-11")
    me_x = client.get("/api/course/me", headers=H)
    check("D6. 期限の翌日は見られない (/me は 401・購入者の数からも外れる)", me_x.status_code == 401 and not mod._ep1_keys_for_email("buyer@example.invalid")
          and "buyer@example.invalid" not in mod._ep1_buyers(), me_x.status_code)
    set_today("2027-01-12")
    MAILS.clear()
    nd = mod._ep1_notify_due(dry_run=False)
    check("D7. 朝のまとめ: 「知らせない」で登録した動画は飛ばす・公開日前は出さない・2 回目は 0",
          nd["sent"] == 0 and mod._ep1_notify_due(dry_run=False)["sent"] == 0, nd)
    set_today("2027-02-01")
    MAILS.clear()
    nd2 = mod._ep1_notify_due(dry_run=True)
    check("D8. 公開日に、「知らせない」の印のない動画だけ数える (印つきは 0)", nd2["videos"] == 0, nd2)
    add("ep1-step", "第03週 ①講義", "EEEEEEEEEE4", "2027-02-01", notify=False)
    conn = mod.db(); c = conn.cursor(); c.execute("DELETE FROM course_video_notices WHERE email = ?", (mod._WINTER_NOAUTO,)); conn.commit(); conn.close()
    MAILS.clear()
    nd3 = mod._ep1_notify_due(dry_run=False)
    bm = [m for m in MAILS if m["to"] == "buyer@example.invalid"]
    check("D9. 印を外すと 1 人 1 通にまとめて知らせる (期限入り)・2 回目は 0", nd3["recipients"] == 3 and len(bm) == 1 and "2027年6月10日" in bm[0]["body"]
          and "第03週 ①講義" in bm[0]["body"] and mod._ep1_notify_due(dry_run=False)["sent"] == 0, (nd3, [m["subject"] for m in bm]))

    # ---- E. 切りかえ・二重払い ----
    set_today("2027-02-01")
    n0 = len(fake.created)
    rd = post_form({"course": "ep1-std", "email": "buyer@example.invalid"})
    check("E1. 期間中に同じコース → 英検準1級用の確認画面 (期限が延びる旨・決済画面は作らない)", rd.status_code == 200 and "すでにお支払い済み" in rd.text and "2027年6月10日" in rd.text
          and "今日から5か月" in rd.text and "冬期講習" not in rd.text
          and len(fake.created) == n0, (rd.status_code, rd.text[:300]))
    rd2 = post_form({"course": "ep1-std", "email": "buyer@example.invalid", "confirm_dup": "1"})
    check("E2. 確認画面の「このまま進む」(confirm_dup=1) で決済画面へ", rd2.status_code == 303 and len(fake.created) == n0 + 1)
    ru = post_form({"course": "ep1-plus", "email": "buyer@example.invalid"})
    kwu = fake.created[-1]
    check("E3. 通常の期間中に質問つき → 差額 10,000 円・plan=ep1-upgrade", ru.status_code == 303 and kwu["line_items"][0]["price_data"]["unit_amount"] == 10000
          and kwu["metadata"]["plan"] == "ep1-upgrade" and kwu["metadata"].get("base_until") == "2027-06-10"
          and "差額" in kwu["line_items"][0]["price_data"]["product_data"]["name"], kwu.get("line_items"))
    MAILS.clear()
    mod._ep1_webhook_record({"id": "cs_live_up1", "payment_status": "paid", "livemode": True, "amount_total": 10000,
                             "customer_details": {"email": "buyer@example.invalid"}, "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-upgrade", "base_until": "2027-06-10"}})
    acc = mod._ep1_access("buyer@example.invalid")
    check("E4. 切りかえ後は質問つき・期限はそのまま (2027-06-10)・塾長に1通・LINE の案内", acc == {"until": "2027-06-10", "plus": True}
          and len([m for m in MAILS if m["to"] == mod.COURSE_CONTACT_EMAIL]) == 1
          and any(mod.COURSE_LINE_URL in m["body"] for m in MAILS if m["to"] == "buyer@example.invalid"), (acc, [m["subject"] for m in MAILS]))
    n1 = len(fake.created)
    rp2 = post_form({"course": "ep1-plus", "email": "plus@example.invalid"})
    check("E5. 質問つきの人が質問つき → 確認画面", rp2.status_code == 200 and "すでにお支払い済み" in rp2.text and len(fake.created) == n1)
    set_today("2027-07-01")
    re_ = post_form({"course": "ep1-std", "email": "buyer@example.invalid"})
    check("E6. 期限が切れた人は確認画面なしで買い直せる (29,800 円)", re_.status_code == 303 and fake.created[-1]["line_items"][0]["price_data"]["unit_amount"] == 29800)
    # 差額の画面を作った後に通常コースの期限が切れてから払った → 新しく 5 か月は付かない (画面を作ったときの期限のまま)
    set_today("2027-03-01")
    mod._ep1_webhook_record({"id": "cs_live_s2", "payment_status": "paid", "livemode": True, "amount_total": 29800,
                             "customer_details": {"email": "late@example.invalid"}, "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}})
    set_today("2027-08-02")
    MAILS.clear()
    mod._ep1_webhook_record({"id": "cs_live_up_late", "payment_status": "paid", "livemode": True, "amount_total": 10000,
                             "customer_details": {"email": "late@example.invalid"},
                             "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-upgrade", "base_until": "2027-08-01"}})
    check("E7. 期限切れの後に記録された差額は、もとの期限のまま (延びない)・塾長に二重払いの疑いとして知らせる",
          not mod._ep1_access("late@example.invalid")["until"]
          and any("二重払い" in m["subject"] for m in MAILS if m["to"] == mod.COURSE_CONTACT_EMAIL), [m["subject"] for m in MAILS])
    set_today("2027-03-02")
    MAILS.clear()
    mod._ep1_webhook_record({"id": "cs_live_s3", "payment_status": "paid", "livemode": True, "amount_total": 29800,
                             "customer_details": {"email": "twice@example.invalid"}, "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}})
    mod._ep1_webhook_record({"id": "cs_live_s4", "payment_status": "paid", "livemode": True, "amount_total": 29800,
                             "customer_details": {"email": "twice@example.invalid"}, "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}})
    dp = [m for m in MAILS if m["to"] == mod.COURSE_CONTACT_EMAIL and "二重払い" in m["subject"]]
    check("E8. 2 つのタブで両方払った → 2 本目で塾長に二重払いの疑い (1 通)", len(dp) == 1, [m["subject"] for m in MAILS])

    # ---- F. 返金・補い・管理 API ----
    set_today("2027-02-01")
    calls = {"pi": None}
    def _list(**kw):
        if "payment_intent" in kw:
            calls["pi"] = kw["payment_intent"]
            return {"data": [{"id": "cs_live_p1"}]} if kw["payment_intent"] == "pi_p1" else {"data": []}
        return {"data": []}
    fake.checkout.Session.list = staticmethod(_list)
    MAILS.clear()
    rp_part = mod._ep1_on_refund({"payment_intent": "pi_p1", "amount": 39800, "amount_refunded": 5000, "refunded": False})
    check("F1. 一部返金は視聴を止めずに塾長に知らせるだけ", rp_part.get("updated") is False and mod._ep1_access("plus@example.invalid")["until"]
          and len(MAILS) == 1 and "一部返金" in MAILS[0]["body"], (rp_part, MAILS))
    MAILS.clear()
    rfull = mod._ep1_on_refund({"payment_intent": "pi_p1", "amount": 39800, "amount_refunded": 39800, "refunded": True})
    check("F2. 全額返金で視聴を止める (refunded)・塾長に知らせる", rfull.get("updated") is True and not mod._ep1_access("plus@example.invalid")["until"]
          and len(MAILS) == 1 and "止めました" in MAILS[0]["body"], (rfull, MAILS))
    def _list_s1(**kw):
        return {"data": [{"id": "cs_live_e1"}]}
    fake.checkout.Session.list = staticmethod(_list_s1)
    MAILS.clear()
    r_std = mod._ep1_on_refund({"payment_intent": "pi_e1", "amount": 29800, "amount_refunded": 29800, "refunded": True})
    check("F2b. 通常コースを全額返金 → 上に乗せた差額の行も止まる・塾長に差額の返金を案内", r_std.get("updated") is True
          and not mod._ep1_access("buyer@example.invalid")["until"] and MAILS and "差額" in MAILS[0]["body"], (r_std, [m["body"][:200] for m in MAILS]))
    conn = mod.db(); c = conn.cursor(); c.execute("UPDATE ep1_purchases SET status = 'paid' WHERE email = ?", ("buyer@example.invalid",)); conn.commit(); conn.close()
    def _down(**kw):
        raise RuntimeError("stripe 503")
    fake.checkout.Session.list = staticmethod(_down)
    try:
        mod._ep1_on_refund({"payment_intent": "pi_x", "amount": 29800, "amount_refunded": 29800, "refunded": True})
        raised = False
    except Exception:
        raised = True
    check("F3. 返金の照会が失敗したら例外 (webhook が 500 で再送させる)", raised)
    class _It(list):
        def auto_paging_iter(self):
            return iter(self)
    def _list2(**kw):
        return _It([{"id": "cs_live_missed", "payment_status": "paid", "amount_total": 29800, "livemode": True, "payment_intent": "pi_missed",
                     "customer_details": {"email": "missed@example.invalid"}, "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}},
                    {"id": "cs_kt", "payment_status": "paid", "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026"}},
                    {"id": "cs_live_e1", "payment_status": "paid", "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}}])
    fake.checkout.Session.list = staticmethod(_list2)
    class _PI:
        @staticmethod
        def retrieve(pi, **kw):
            return {"id": pi, "latest_charge": {"amount": 29800, "amount_refunded": 0, "refunded": False, "disputed": False}}
    fake.PaymentIntent = _PI
    s1 = mod._ep1_sync_from_stripe(days=7, dry_run=True)
    s2 = mod._ep1_sync_from_stripe(days=7, dry_run=False)
    s3 = mod._ep1_sync_from_stripe(days=7, dry_run=False)
    check("F4. Stripe から取りこぼしを補う (dry_run は数えるだけ・過去問の決済は見ない・2 回目は 0)",
          s1["missing"] == 1 and s1["recorded"] == 0 and s2["recorded"] == 1 and s3["missing"] == 0
          and mod._ep1_access("missed@example.invalid")["until"] == "2027-07-01", (s1, s2, s3))
    check("F5. 管理 API は認証が要る", client.get("/api/admin/ep1/purchases").status_code == 401
          and client.post("/api/admin/ep1/purchases/1/status", json={"status": "refunded"}).status_code in (401, 403))
    pl = client.get("/api/admin/ep1/purchases", headers=ADMIN).json()
    row_m = [p for p in pl["purchases"] if p["email"] == "missed@example.invalid"][0]
    check("F6. 購入一覧 (コース名・期限・期間中か・販売中か)", pl["on_sale"] is True and row_m["active"] is True and row_m["view_until"] == "2027-07-01"
          and row_m["plan_name"].startswith("通常コース") and pl["view_months"] == 5, row_m)
    rv = client.post(f"/api/admin/ep1/purchases/{row_m['id']}/status", headers=ADMIN, json={"view_until": "2027-08-31"})
    bad = client.post(f"/api/admin/ep1/purchases/{row_m['id']}/status", headers=ADMIN, json={"view_until": "8/31"})
    check("F7. 期限を延ばせる・日付の形が違えば 400", rv.status_code == 200 and mod._ep1_access("missed@example.invalid")["until"] == "2027-08-31"
          and bad.status_code == 400, (rv.text[:200], bad.status_code))
    row_b = [p for p in pl["purchases"] if p["email"] == "buyer@example.invalid" and p["plan"] == "ep1-std"][0]
    client.post(f"/api/admin/ep1/purchases/{row_b['id']}/status", headers=ADMIN, json={"view_until": "2027-07-10"})
    set_today("2027-07-01")
    check("F7b. 通常コースの期限を変えると、同じ期限の差額の行もそろって動く (質問つきのまま)",
          mod._ep1_access("buyer@example.invalid") == {"until": "2027-07-10", "plus": True}, mod._ep1_access("buyer@example.invalid"))
    set_today("2027-02-01")
    client.post(f"/api/admin/ep1/purchases/{row_b['id']}/status", headers=ADMIN, json={"view_until": "2027-06-10"})
    rs = client.post(f"/api/admin/ep1/purchases/{row_m['id']}/status", headers=ADMIN, json={"status": "refunded"})
    check("F8. 手で refunded にすると見られない", rs.status_code == 200 and not mod._ep1_access("missed@example.invalid")["until"])
    cm = client.get("/api/admin/course/members", headers=ADMIN).json()["members"]
    bm_ = [m for m in cm if m["email"] == "buyer@example.invalid"]
    check("F9. CEO の受講者一覧に講座と期限が出る (準2級と同じ列 ep2_names)", bm_ and bm_[0].get("ep2_names") == [f"{mod.EP1_COURSE_NAME}（2027-06-10まで）"], bm_)
    cv = client.get("/api/admin/course/videos", headers=ADMIN).json()
    e1c = [x for x in (cv.get("ep2_courses") or []) if x["key"] == "ep1-step"]
    check("F10. CEO の動画登録の選択肢に講座 (準2級と同じ欄・期間中の人数)", e1c and e1c[0]["active_members"] == len(mod._ep1_buyers()) >= 2
          and [x["key"] for x in cv["ep2_courses"]] == ["ep2-step", "ep1-step"], cv.get("ep2_courses"))

    # ---- G. 署名付き webhook ----
    mod.get_stripe = _orig_get_stripe
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_ep1"
    mod.STRIPE_WEBHOOK_SECRET = "whsec_test_ep1"
    import stripe as _stripe_lib
    if int(str(getattr(_stripe_lib, "VERSION", "0")).split(".")[0] or 0) >= 14:
        print(f"  ⏭ G. 署名付き webhook: stripe {_stripe_lib.VERSION} ではスキップ (CI の 11.x で実行)")
    else:
        def _signed(pl_):
            ts2 = int(time.time())
            return {"Stripe-Signature": f"t={ts2},v1=" + hmac.new(b"whsec_test_ep1", f"{ts2}.".encode() + pl_, hashlib.sha256).hexdigest(), "Content-Type": "application/json"}
        payload = json.dumps({"id": "evt_ep1_1", "object": "event", "api_version": "2024-06-20", "created": int(time.time()), "livemode": True,
                              "type": "checkout.session.completed", "data": {"object": {"object": "checkout.session", "id": "cs_wh_e1",
                              "payment_status": "paid", "amount_total": 29800, "customer_details": {"email": "wh@example.invalid", "name": ""},
                              "metadata": {"system": "juku-payment-eikenp1", "plan": "ep1-std"}}}}).encode()
        wr = client.post("/api/stripe/webhook", content=payload, headers=_signed(payload))
        check("G1. 署名付き webhook → 記録し、応答は juku-payment skip", wr.status_code == 200 and wr.json().get("skipped_reason") == "juku-payment system tag"
              and mod._ep1_keys_for_email("wh@example.invalid") == ["ep1-step"], (wr.status_code, wr.text[:200]))
        payload2 = payload.replace(b"evt_ep1_1", b"evt_ep1_2").replace(b"cs_wh_e1", b"cs_wh_e2").replace(b"wh@example", b"wh2@example")
        conn = mod.db(); conn.cursor().execute("ALTER TABLE ep1_purchases RENAME TO ep1_purchases_tmp"); conn.commit(); conn.close()
        wf = client.post("/api/stripe/webhook", content=payload2, headers=_signed(payload2))
        conn = mod.db(); conn.cursor().execute("ALTER TABLE ep1_purchases_tmp RENAME TO ep1_purchases"); conn.commit(); conn.close()
        wr2 = client.post("/api/stripe/webhook", content=payload2, headers=_signed(payload2))
        check("G2. 記録に失敗したら 500 (Stripe が再送)・同じイベントの再送で記録できる", wf.status_code == 500 and wr2.status_code == 200
              and mod._ep1_keys_for_email("wh2@example.invalid") == ["ep1-step"], (wf.status_code, wr2.text[:200]))

    # ---- H. 画面と表記 ----
    app_js = read("payment/app.js")
    check("H1. 月謝アプリの Stripe 取込は juku-payment-eikenp1 を除外・?v= を上げた", "system === 'juku-payment-eikenp1')" in app_js
          and (re.search(r"app\.js\?v=(\d{8}[a-z]?)", read("payment/index.html")) or [None, ""])[1] >= "20261126")
    cvh = read("course-videos.html")
    check("H2. 視聴ページに講座の説明と期限", "id=\"ep1Note\"" in cvh and "me.ep1_view_until" in cvh and "英検準1級 4か月ステップアップ講座・英検準2級 ステップアップ講座をお申し込みの方" in cvh)
    ceo = read("ceo.html")
    check("H3. CEO の動画登録の選択肢・受講者一覧 (準2級と同じ欄)", "addEp2Options(d.ep2_courses" in ceo and "m.ep2_names" in ceo and "英検講座（準2級・準1級）" in ceo)
    legal = read("legal.html")
    sec = legal.split('id="tokusho-eikenp1"', 1)[1].split("</section>", 1)[0] if 'id="tokusho-eikenp1"' in legal else ""
    check("H4. 特商法の表記の金額・期間がサーバと同じ", "29,800円" in sec and "39,800円" in sec and "10,000円" in sec
          and "お支払いの日から5か月" in sec and "#tokusho-eikenp1" in legal
          and mod.EP1_PRICE_PLUS - mod.EP1_PRICE_STD == 10000, sec[:200])

    # ---- 決済を同じ画面で開く (2026-11-24)：GET の入口は日本語の案内・エラー画面は「ブラウザの戻る」の文 ----
    rg = client.get("/api/ep1/checkout")
    check("Z1. GET の決済入口は日本語の案内 (Not Found にしない)・戻り先は eiken-p1",
          rg.status_code == 400 and "申込ページでもう一度" in rg.text and "Not Found" not in rg.text and "eiken-p1" in rg.text, (rg.status_code, rg.text[:200]))
    eg = mod._ep1_error_page("テスト")
    check("Z2. 英検準1級のエラー画面は「ブラウザの「戻る」」の文 (「このタブを閉じて」は出さない)",
          "ブラウザの「戻る」" in eg.body.decode() and "このタブを閉じて" not in eg.body.decode())

    # ---- W. 本体 webhook の分岐・C3 の文字数 ----
    msrc = read("server/main.py")
    mw = re.search(r'if event\["type"\] == "checkout\.session\.completed":(.{0,2500})', msrc, re.S)
    check("W1. checkout.session.completed の分岐は準2級・準1級の両方を記録し、juku-payment skip が 2500 字以内に残る",
          bool(mw) and "EP1_SYSTEM_TAG: _ep1_webhook_record" in mw.group(1) and '_meta_system.startswith("juku-payment")' in mw.group(1))
    check("W2. 返金の分岐に準1級", "_ep1_on_refund(charge)" in msrc)

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}")
        sys.exit(1)
    print("✅ すべて合格")


if __name__ == "__main__":
    main()
