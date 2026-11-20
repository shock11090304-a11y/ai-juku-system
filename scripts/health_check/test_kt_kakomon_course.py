#!/usr/bin/env python3
"""📝 共通テスト過去問 解説動画 (/api/kt/checkout・本体 webhook の記録・視聴ページ・配信のお知らせ・返金) の回帰テスト。
in-process・一時 SQLite。Stripe は偽物、メールは記録器 (ネットワーク不要)。冬期講習 (test_winter_course.py) と同じ形。

  A. 料金: 1 年分 1,980 円・直前セット 8,800 円 (6 年度)。同じ科目のセットを選んだら 1 年分は外す。講座 12 (2 科目 × 6 年度)
  B. 決済の入口: フォーム送信 → Stripe Checkout へ 303。明細・metadata (system=juku-payment-kakomon)・戻り先・有効期限。だめなときは日本語の HTML
     (題は「共通テスト過去問」・戻り先は kakomon.html。冬期講習の画面の文面は変わらない)
  C. 記録: kt_purchases に 1 行 (セットは 6 年度に展開)・案内メール 1 通・再送で増えない・テストモードは記録しない・記録失敗は False・
     月額講座の受講者を変えない・冬期講習の表と先着特典の数に混ざらない・Stripe からの補い・返金
  D. 視聴ページ: 過去問だけの人もログインできる・自分の年度の公開済み動画だけ・配信日前は出ない・月額講座／冬期講習との組み合わせ
  E. お知らせ: 登録と同時の通知は買った人だけ・朝のまとめは 1 人 1 通で 2 回知らせない・「知らせない」で登録した動画は飛ばす
  F. 二重払いの確認画面・返金/視聴期間の終わりで入れない・管理 API は認証必須・年度ごとの取り消し
  G. 署名付き webhook (stripe 11.x の CI で実行)
  H. 画面と表記: 月謝アプリの取込で除外・視聴ページ・CEO の選択肢・特商法の表記の金額
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import re
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
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="kt_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "sk_test_dummy_for_kt", "STRIPE_WEBHOOK_SECRET": "",
        "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "re_dummy", "BASE_URL": "https://example.invalid", "WINTER_SITE_URL": "https://site.example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_kt", MAIN_PY)
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
    print("📝 共通テスト過去問 解説動画 回帰テスト")

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
    P = mod._kt_plan
    check("A1. 売るもの 6 (国語・英語R の 2026・2025 の 1 年分 4 と直前セット 2)・講座 12",
          list(mod.KT_PRODUCTS) == ["kt-kokugo-2026", "kt-kokugo-2025", "kt-kokugo-set6", "kt-r-2026", "kt-r-2025", "kt-r-set6"]
          and len(mod.KT_COURSES) == 12, list(mod.KT_PRODUCTS))
    check("A2. 1 年分は 1,980 円・直前セットは 8,800 円",
          all(v["price"] == 1980 for k, v in mod.KT_PRODUCTS.items() if not k.endswith("set6"))
          and all(v["price"] == 8800 for k, v in mod.KT_PRODUCTS.items() if k.endswith("set6")))
    check("A3. 直前セットは 2026〜2021 の 6 年度", mod.KT_PRODUCTS["kt-r-set6"]["keys"] == [f"kt-r-{y}" for y in (2026, 2025, 2024, 2023, 2022, 2021)])
    a4 = P(["kt-r-2025", "kt-kokugo-2026", "kt-r-2025"])
    check("A4. 重複は 1 つ・並びは表の順・合計 3,960 円", a4["parts"] == ["kt-kokugo-2026", "kt-r-2025"] and a4["total"] == 3960
          and a4["keys"] == ["kt-kokugo-2026", "kt-r-2025"], a4)
    a5 = P(["kt-r-2026", "kt-r-set6", "kt-kokugo-2025"])
    check("A5. 同じ科目のセットを選んだら 1 年分は外す (英語セット 8,800＋国語 2025 1,980)", a5["parts"] == ["kt-kokugo-2025", "kt-r-set6"]
          and a5["total"] == 10780 and len(a5["keys"]) == 7, a5)
    check("A6. 知らない sku は unknown・2024 の 1 年分はまだ売らない", P(["kt-r-2024", "zzz"])["unknown"] == ["kt-r-2024", "zzz"])
    check("A7. 配信日: 2026・2025 は第1弾・2024〜2021 は第2弾",
          mod.KT_COURSES["kt-r-2025"]["delivery"] == mod.KT_DELIVERY_1 and mod.KT_COURSES["kt-kokugo-2021"]["delivery"] == mod.KT_DELIVERY_2
          and mod.KT_DELIVERY_1 < mod.KT_DELIVERY_2)
    check("A8. 講座のキーは冬期講習・月額講座と重ならない",
          not (set(mod.KT_COURSES) & set(mod.COURSE_KEYS)) and not any(mod._winter_is_video_key(k) for k in mod.KT_COURSES))

    # ---- B. 決済の入口 ----
    def post_form(fields, **kw):
        body = urllib.parse.urlencode(fields, doseq=True)
        return client.post("/api/kt/checkout", content=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, follow_redirects=False, **kw)
    set_today("2026-11-25")
    t0 = int(time.time())
    r = post_form({"items": ["kt-r-set6,kt-r-2026", "kt-kokugo-2026"], "email": " Buyer@Example.invalid ", "app_id": "KT-abc123"})
    kw = fake.created[-1] if fake.created else {}
    check("B1. 303 で Stripe の決済画面へ", r.status_code == 303 and r.headers.get("location", "").startswith("https://checkout.stripe.com/"), (r.status_code, r.text[:200]))
    amts = [li["price_data"]["unit_amount"] for li in kw.get("line_items", [])]
    names = [li["price_data"]["product_data"]["name"] for li in kw.get("line_items", [])]
    check("B2. 明細 = 国語 2026 1,980＋英語セット 8,800 (英語 2026 はセットに含む)", amts == [1980, 8800]
          and all(li["quantity"] == 1 and li["price_data"]["currency"] == "jpy" for li in kw.get("line_items", []))
          and names[1].startswith("共通テスト過去問 解説動画 英語リーディング 直前セット"), (amts, names))
    meta = kw.get("metadata") or {}
    check("B3. metadata (session と payment_intent の両方に system=juku-payment-kakomon・items・total・app_id)",
          meta.get("system") == "juku-payment-kakomon" and meta.get("items") == "kt-kokugo-2026,kt-r-set6" and meta.get("total") == "10780"
          and meta.get("app_id") == "KT-abc123" and (kw.get("payment_intent_data") or {}).get("metadata") == meta, kw)
    check("B4. メールは小文字・カードのみ・日本語・戻り先は kakomon のページ・有効期限 23 時間",
          kw.get("customer_email") == "buyer@example.invalid" and kw.get("payment_method_types") == ["card"] and kw.get("locale") == "ja"
          and kw.get("mode") == "payment"
          and kw.get("success_url") == "https://site.example.invalid/kakomon-thanks.html?session_id={CHECKOUT_SESSION_ID}"
          and kw.get("cancel_url") == "https://site.example.invalid/kakomon.html?canceled=1" and kw.get("client_reference_id") == "kt-KT-abc123"
          and abs(kw.get("expires_at", 0) - (t0 + 23 * 3600)) < 60, kw)
    n_before = len(fake.created)
    for label, fields, code, text in [
        ("B5. メールの形が違う → 400", {"items": "kt-r-2026", "email": "not-an-email"}, 400, "メールアドレス"),
        ("B6. 知らない講座 (冬期講習の sku も) → 400", {"items": "kt-r-2026,h3-r", "email": "a@example.invalid"}, 400, "講座の指定"),
        ("B7. 講座なし → 400", {"items": "", "email": "a@example.invalid"}, 400, "講座が選ばれていません"),
    ]:
        rr = post_form(fields)
        check(label, rr.status_code == code and text in rr.text and "text/html" in rr.headers.get("content-type", "")
              and "共通テスト過去問 解説動画" in rr.text and "https://site.example.invalid/kakomon.html" in rr.text and "冬期講習" not in rr.text,
              (rr.status_code, rr.text[:300]))
    check("B8. だめなときは決済画面を作らない", len(fake.created) == n_before)
    w_err = mod._winter_error_page("x")
    wt = w_err.body.decode()
    check("B9. 冬期講習のエラー画面の文面は変わらない (題・帯・戻り先)", "お手続きを続けられませんでした | 冬期講習2026" in wt
          and "トリリオン英語塾　冬期講習2026" in wt and "https://site.example.invalid/winter.html" in wt, wt[:300])
    fake.fail = True
    rr = post_form({"items": "kt-r-2026", "email": "x@example.invalid"})
    check("B10. Stripe の失敗は 502 の HTML", rr.status_code == 502 and "お支払いの画面を用意できませんでした" in rr.text, rr.status_code)
    fake.fail = False
    os.environ["KT_CHECKOUT_ENABLED"] = "0"
    rr = post_form({"items": "kt-r-2026", "email": "x@example.invalid"})
    check("B11. KT_CHECKOUT_ENABLED=0 で止まる (503)・冬期講習の入口は止まらない", rr.status_code == 503
          and post_form.__call__ and client.post("/api/winter/checkout", content="items=h3-r&email=x%40example.invalid",
                                                 headers={"Content-Type": "application/x-www-form-urlencoded"}, follow_redirects=False).status_code == 303, rr.status_code)
    os.environ["KT_CHECKOUT_ENABLED"] = "1"
    codes = [post_form({"items": "kt-r-2026", "email": "spam@example.invalid"}).status_code for _ in range(11)]
    check("B12. 同じメールは 10 分に 10 回まで (11 回目は 429)", codes[:10] == [303] * 10 and codes[10] == 429, codes)

    # ---- C. 記録 ----
    conn = mod.db(); c = conn.cursor(); c.execute("SELECT COUNT(*) AS n FROM winter_purchases"); n_winter0 = c.fetchone()["n"]; conn.close()
    bonus0 = mod._winter_bonus_left()
    MAILS.clear()
    sess = {"id": "cs_live_k1", "object": "checkout.session", "payment_status": "paid", "livemode": True, "amount_total": 10780,
            "customer_details": {"email": "Buyer@Example.invalid", "name": "過去問 太郎"},
            "metadata": {"system": "juku-payment-kakomon", "items": "kt-kokugo-2026,kt-r-set6", "total": "10780", "app_id": "KT-abc123"}}
    r1 = mod._kt_webhook_record(sess)
    r2 = mod._kt_webhook_record(dict(sess))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT * FROM kt_purchases"); rows = c.fetchall()
    c.execute("SELECT COUNT(*) AS n FROM winter_purchases"); n_winter = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM students"); n_students = c.fetchone()["n"]
    conn.close()
    exp_keys = ["kt-kokugo-2026"] + [f"kt-r-{y}" for y in (2026, 2025, 2024, 2023, 2022, 2021)]
    check("C1. 1 行だけ記録 (メールは小文字・講座はセットを 6 年度に展開・明細・金額)", r1 is True and r2 is True and len(rows) == 1
          and rows[0]["email"] == "buyer@example.invalid" and json.loads(rows[0]["item_keys"]) == exp_keys
          and json.loads(rows[0]["plan"]) == ["kt-kokugo-2026", "kt-r-set6"] and rows[0]["amount"] == 10780 and rows[0]["status"] == "paid",
          [dict(x) for x in rows])
    check("C2. students・冬期講習の購入・冬期講習の先着特典の残りは変わらない", n_students == 0 and n_winter == n_winter0 and mod._winter_bonus_left() == bonus0,
          (n_students, n_winter, n_winter0))
    bm = mod._course_member_by_email("buyer@example.invalid")
    check("C3. course_members に過去問だけの行 (status=canceled・courses=[])", bm and bm["status"] == "canceled" and bm["courses"] == [] and bm["name"] == "過去問 太郎", bm)
    body0 = MAILS[0]["body"] if MAILS else ""
    check("C4. 案内メールは 1 通 (件名・年度ごとの講座名と配信日・合計・ログインリンク・視聴期限)", len(MAILS) == 1 and MAILS[0]["to"] == "buyer@example.invalid"
          and "共通テスト過去問 解説動画" in MAILS[0]["subject"] and "10,780円" in body0
          and "共通テスト過去問 英語リーディング 2021年度 本試験（第1日程）（配信 12月26日（土）〜）" in body0
          and "共通テスト過去問 国語 2026年度 本試験（配信 12月5日（土）〜）" in body0
          and "course-videos.html?t=" in body0 and "2028年3月31日（金）" in body0 and "冬期講習" not in body0, MAILS)
    welcome_link = [l for l in body0.splitlines() if "course-videos.html?t=" in l]
    mod._course_upsert_member("monthly@example.invalid", ["bunpo"], "cus_m1", "月額 花子")
    mod._kt_webhook_record({"id": "cs_live_k2", "payment_status": "paid", "amount_total": 1980, "customer_email": "monthly@example.invalid",
                            "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2025"}})
    mm = mod._course_member_by_email("monthly@example.invalid")
    check("C5. 月額講座の受講者が過去問を買っても月額講座は有効のまま", mm["status"] == "active" and mm["courses"] == ["bunpo"], mm)
    MAILS.clear()
    r_test = mod._kt_webhook_record({"id": "cs_test_t1", "livemode": False, "payment_status": "paid", "customer_email": "testmode@example.invalid",
                                     "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026"}})
    check("C6. テストモードの決済は記録しない (True で再送させない)", r_test is True and not mod._kt_keys_for_email("testmode@example.invalid") and not MAILS)
    os.environ["KT_RECORD_TEST"] = "1"
    r_test2 = mod._kt_webhook_record({"id": "cs_test_t2", "livemode": False, "payment_status": "paid", "customer_email": "testmode@example.invalid",
                                      "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026"}})
    os.environ["KT_RECORD_TEST"] = "0"
    check("C6b. KT_RECORD_TEST=1 ならテストモードも記録する (livemode=0)", r_test2 is True and mod._kt_keys_for_email("testmode@example.invalid") == ["kt-r-2026"])
    conn = mod.db(); conn.cursor().execute("DELETE FROM kt_purchases WHERE session_id = 'cs_test_t2'"); conn.commit(); conn.close()
    MAILS.clear()
    conn = mod.db(); conn.cursor().execute("ALTER TABLE kt_purchases RENAME TO kt_purchases_tmp"); conn.commit(); conn.close()
    r_fail = mod._kt_webhook_record({"id": "cs_live_fail", "payment_status": "paid", "customer_email": "fail@example.invalid",
                                     "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026"}})
    conn = mod.db(); conn.cursor().execute("ALTER TABLE kt_purchases_tmp RENAME TO kt_purchases"); conn.commit(); conn.close()
    check("C7. 記録そのものに失敗したら False (webhook が 500 で再送させる)・メールは送らない", r_fail is False and not MAILS, r_fail)
    check("C8. 中身の無い決済 (知らない商品だけ) は記録しない (True)",
          mod._kt_webhook_record({"id": "cs_live_bad", "payment_status": "paid", "customer_email": "bad@example.invalid",
                                  "metadata": {"system": "juku-payment-kakomon", "items": "h3-r"}}) is True and not mod._kt_keys_for_email("bad@example.invalid"))
    _orig_link = mod._course_send_login_link
    mod._course_send_login_link = lambda member, intro="", subject="": {"sent": False, "error": "recipient cap"}
    MAILS.clear()
    r_nm = mod._kt_webhook_record({"id": "cs_live_nomail", "payment_status": "paid", "amount_total": 1980, "customer_email": "nomail@example.invalid",
                                   "metadata": {"system": "juku-payment-kakomon", "items": "kt-kokugo-2025"}})
    mod._course_send_login_link = _orig_link
    check("C9. 案内メールが送れなかったら塾長に知らせる (記録はできている)", r_nm is True and mod._kt_keys_for_email("nomail@example.invalid") == ["kt-kokugo-2025"]
          and len(MAILS) == 1 and MAILS[0]["to"] == mod.COURSE_CONTACT_EMAIL and "送れませんでした" in MAILS[0]["subject"], MAILS)
    conn = mod.db(); conn.cursor().execute("DELETE FROM kt_purchases WHERE session_id = 'cs_live_nomail'"); conn.commit(); conn.close()
    # 取りこぼしの補い
    class _L(list):
        def auto_paging_iter(self):
            return iter(self)
    def _list(**kw):
        if kw.get("payment_intent"):
            return {"data": [{"id": {"pi_missed": "cs_live_missed", "pi_k1": "cs_live_k1"}.get(kw["payment_intent"], "cs_unknown")}]}
        return _L([{"id": "cs_live_k1", "payment_status": "paid", "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026"}},
                   {"id": "cs_live_missed", "payment_status": "paid", "amount_total": 1980, "livemode": True, "payment_intent": "pi_missed",
                    "customer_details": {"email": "missed@example.invalid", "name": ""}, "metadata": {"system": "juku-payment-kakomon", "items": "kt-kokugo-2026"}},
                   {"id": "cs_live_refd", "payment_status": "paid", "amount_total": 1980, "livemode": True, "payment_intent": "pi_refunded",
                    "customer_details": {"email": "refd@example.invalid"}, "metadata": {"system": "juku-payment-kakomon", "items": "kt-kokugo-2026"}},
                   {"id": "cs_live_unpaid", "payment_status": "unpaid", "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2025"}},
                   {"id": "cs_winter", "payment_status": "paid", "metadata": {"system": "juku-payment-winter", "items": "h3-r"}}])
    fake.checkout.Session.list = staticmethod(_list)
    class _PI:
        @staticmethod
        def retrieve(pi, **kw):
            return {"id": pi, "latest_charge": {"amount": 1980, "amount_refunded": 1980 if pi == "pi_refunded" else 0, "refunded": pi == "pi_refunded", "disputed": False}}
    fake.PaymentIntent = _PI
    s1 = mod._kt_sync_from_stripe(days=7, dry_run=True)
    s2 = mod._kt_sync_from_stripe(days=7, dry_run=False)
    s3 = mod._kt_sync_from_stripe(days=7, dry_run=False)
    check("C10. Stripe から取りこぼしを補う (dry_run は数えるだけ・返金済みは補わない・冬期講習の決済は見ない・2 回目は 0)",
          s1["missing"] == 1 and s1["recorded"] == 0 and s1["skipped_refunded"] == 1 and s2["recorded"] == 1 and s3["missing"] == 0
          and mod._kt_keys_for_email("missed@example.invalid") == ["kt-kokugo-2026"] and not mod._kt_keys_for_email("refd@example.invalid"), (s1, s2, s3))
    MAILS.clear()
    rf = mod._kt_on_refund({"payment_intent": "pi_missed", "amount": 1980, "amount_refunded": 1980, "refunded": True, "metadata": {"system": "juku-payment-kakomon"}})
    check("C11. 全額返金で視聴を止める (refunded)・塾長に知らせる", rf.get("updated") is True and not mod._kt_keys_for_email("missed@example.invalid")
          and len(MAILS) == 1 and MAILS[0]["to"] == mod.COURSE_CONTACT_EMAIL and "止めました" in MAILS[0]["body"], (rf, MAILS))
    MAILS.clear()
    rp = mod._kt_on_refund({"payment_intent": "pi_k1", "amount": 10780, "amount_refunded": 1980, "refunded": False, "metadata": {"system": "juku-payment-kakomon"}})
    check("C12. 一部返金は視聴を止めずに塾長に知らせるだけ", rp.get("updated") is False and len(mod._kt_keys_for_email("buyer@example.invalid")) == 7
          and len(MAILS) == 1 and "一部返金" in MAILS[0]["body"], (rp, MAILS))
    # 返金のときに Stripe への照会が失敗 → 例外を上げる (webhook が 500 で再送させる)。握りつぶして「記録が無い」と知らせない
    _orig_list = fake.checkout.Session.list
    def _list_down(**kw):
        raise RuntimeError("stripe 503")
    fake.checkout.Session.list = staticmethod(_list_down)
    MAILS.clear()
    try:
        mod._kt_on_refund({"payment_intent": "pi_k1", "amount": 10780, "amount_refunded": 10780, "refunded": True, "metadata": {"system": "juku-payment-kakomon"}})
        raised = False
    except Exception:
        raised = True
    fake.checkout.Session.list = _orig_list
    check("C13. 返金の照会が失敗したら例外 (再送させる)・塾長に誤った知らせを送らない・視聴はまだ付いたまま",
          raised and not MAILS and len(mod._kt_keys_for_email("buyer@example.invalid")) == 7, (raised, MAILS))
    # 記録より先に返金が済んでいた (再送待ちの間に返金) → refunded で記録し、視聴も案内メールも付けない
    MAILS.clear()
    r_rf = mod._kt_webhook_record({"id": "cs_live_late", "payment_status": "paid", "amount_total": 1980, "livemode": True, "payment_intent": "pi_refunded",
                                   "customer_details": {"email": "late@example.invalid"}, "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2025"}})
    conn = mod.db(); c_ = conn.cursor(); c_.execute("SELECT status FROM kt_purchases WHERE session_id = 'cs_live_late'"); st_late = c_.fetchone(); conn.close()
    check("C14. 記録より先に全額返金されていたら refunded で記録 (視聴なし・案内メールなし)",
          r_rf is True and st_late and st_late["status"] == "refunded" and not mod._kt_keys_for_email("late@example.invalid") and not MAILS, (st_late and dict(st_late), MAILS))
    # 決済の後に売り方を変えた等で、知らない商品が混ざっている → 分かる分は記録し、塾長に知らせる
    MAILS.clear()
    r_mx = mod._kt_webhook_record({"id": "cs_live_mixed", "payment_status": "paid", "amount_total": 3960, "livemode": True,
                                   "customer_details": {"email": "mixed@example.invalid"}, "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026,kt-r-2020"}})
    check("C15. 知らない商品が混ざった決済は、分かる分を記録して塾長に知らせる",
          r_mx is True and mod._kt_keys_for_email("mixed@example.invalid") == ["kt-r-2026"]
          and any(m["to"] == mod.COURSE_CONTACT_EMAIL and "kt-r-2020" in m["body"] for m in MAILS), MAILS)
    _orig_pi = fake.PaymentIntent
    class _PIpart:
        @staticmethod
        def retrieve(pi, **kw):
            return {"id": pi, "latest_charge": {"amount": 10780, "amount_refunded": 1980, "refunded": False, "disputed": False}}
    fake.PaymentIntent = _PIpart
    r_pt = mod._kt_webhook_record({"id": "cs_live_part", "payment_status": "paid", "amount_total": 10780, "livemode": True, "payment_intent": "pi_part",
                                   "customer_details": {"email": "part@example.invalid"}, "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026"}})
    fake.PaymentIntent = _orig_pi
    check("C16. 記録より先に一部返金だけなら paid で記録 (どの年度を止めるかは塾長が決める)",
          r_pt is True and mod._kt_keys_for_email("part@example.invalid") == ["kt-r-2026"], mod._kt_keys_for_email("part@example.invalid"))
    conn = mod.db(); conn.cursor().execute("DELETE FROM kt_purchases WHERE session_id IN ('cs_live_mixed', 'cs_live_late', 'cs_live_part')"); conn.commit(); conn.close()

    # ---- D. 視聴ページ ----
    tok = welcome_link[0].split("?t=", 1)[1].strip() if welcome_link else ""
    vr = client.post("/api/course/login/verify", json={"token": tok})
    check("D1. 案内メールのリンクで過去問だけの人もログインできる (講座 7)", vr.status_code == 200 and [c["key"] for c in vr.json().get("courses", [])] == exp_keys, vr.text[:300])
    H = {"Authorization": "Bearer " + (vr.json().get("token") or "")} if vr.status_code == 200 else {}
    def add(key, title, yid, pub, notify=True):
        return client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": key, "title": title, "youtube_url": "https://youtu.be/" + yid, "publish_date": pub, "notify": notify})
    MAILS.clear()
    ra = add("kt-r-2026", "英語R 2026 第1〜4問", "RRRRRRRRRR1", "2026-11-25", notify=True)
    check("E1. 過去問の講座に動画を登録できる・登録と同時の通知は買った人だけ (1 通)", ra.status_code == 200 and (ra.json().get("notified") or {}).get("sent") == 1
          and [m["to"] for m in MAILS] == ["buyer@example.invalid"] and "英語リーディング 2026年度" in MAILS[0]["subject"], (ra.text[:200], [m["to"] for m in MAILS]))
    add("kt-r-2026", "英語R 2026 第5〜8問", "RRRRRRRRRR2", "2026-11-25", notify=False)
    add("kt-r-2024", "英語R 2024 第1〜4問", "RRRRRRRRRR3", "2026-12-26")
    add("kt-kokugo-2025", "国語 2025 第1問", "KKKKKKKKKK1", "2026-11-25")   # 買っていない年度
    add("w26-h3-r", "共テR 冬期 第1回", "WWWWWWWWWW1", "2026-11-25")
    check("D2. 知らない講座キー (kt-r-2020・kt-r-set6) は 400", add("kt-r-2020", "x", "XXXXXXXXXX1", "2026-11-25").status_code == 400
          and add("kt-r-set6", "x", "XXXXXXXXXX2", "2026-11-25").status_code == 400)
    me = client.get("/api/course/me", headers=H)
    vids = [v["title"] for v in me.json().get("videos", [])] if me.status_code == 200 else []
    check("D3. /me は自分の年度の公開済み動画だけ (配信日前・買っていない年度・冬期講習は出ない)", me.status_code == 200
          and sorted(vids) == ["英語R 2026 第1〜4問", "英語R 2026 第5〜8問"], (me.status_code, vids))
    kt = me.json().get("kt") if me.status_code == 200 else None
    check("D4. /me に過去問の講座と配信日・視聴期限 (冬期講習の欄は空)", kt and [(w["key"], w["delivery"]) for w in kt][:3] == [("kt-kokugo-2026", "2026-12-05"), ("kt-r-2026", "2026-12-05"), ("kt-r-2025", "2026-12-05")]
          and kt[-1] == {"key": "kt-r-2021", "name": "共通テスト過去問 英語リーディング 2021年度 本試験（第1日程）", "delivery": "2026-12-26"}
          and me.json().get("kt_view_until") == "2028-03-31" and me.json().get("winter") == [] and me.json().get("winter_view_until") is None, me.text[:400])
    set_today("2026-12-26")
    me2 = client.get("/api/course/me", headers=H)
    check("D5. 第2弾の配信日になると 2024 の動画も出る", "英語R 2024 第1〜4問" in [v["title"] for v in me2.json().get("videos", [])], me2.text[:300])
    set_today("2026-11-25")
    MAILS.clear()
    lr = client.post("/api/course/login/request", json={"email": "buyer@example.invalid"})
    check("D6. ログインリンクの再送も過去問だけの人に届く", lr.status_code == 200 and len(MAILS) == 1 and "course-videos.html?t=" in MAILS[0]["body"], MAILS)
    # 行が無いのに購入はある (記録の途中で落ちた等) → ログインの依頼で行を作って送る
    conn = mod.db(); conn.cursor().execute("DELETE FROM course_members WHERE email = 'missed2@example.invalid'"); conn.commit(); conn.close()
    conn = mod.db(); conn.cursor().execute("INSERT INTO kt_purchases (session_id, email, name, plan, item_keys, amount, status, livemode, paid_at) VALUES ('cs_x2','missed2@example.invalid','','[\"kt-r-2025\"]','[\"kt-r-2025\"]',1980,'paid',1,'2026-11-20T00:00:00')"); conn.commit(); conn.close()
    MAILS.clear()
    client.post("/api/course/login/request", json={"email": "missed2@example.invalid"})
    check("D7. 購入はあるのに受講者の行が無い人にもログインリンクが届く", len(MAILS) == 1 and MAILS[0]["to"] == "missed2@example.invalid"
          and (mod._course_member_by_email("missed2@example.invalid") or {}).get("status") == "canceled", MAILS)
    # 月額講座＋過去問・冬期講習＋過去問
    MAILS.clear()
    client.post("/api/course/login/request", json={"email": "monthly@example.invalid"})
    mlink = [l for l in MAILS[0]["body"].splitlines() if "course-videos.html?t=" in l] if MAILS else []
    mv = client.post("/api/course/login/verify", json={"token": mlink[0].split("?t=", 1)[1].strip() if mlink else ""})
    check("D8. 月額講座＋過去問の人は両方の講座", mv.status_code == 200 and [c["key"] for c in mv.json()["courses"]] == ["bunpo", "kt-r-2025"], mv.text[:300])
    mod._winter_webhook_record({"id": "cs_live_w9", "payment_status": "paid", "amount_total": 7500, "customer_email": "buyer@example.invalid",
                                "metadata": {"system": "juku-payment-winter", "items": "h3-r", "plan": "h3-r"}})
    me3 = client.get("/api/course/me", headers=H).json()
    check("D9. 冬期講習＋過去問の人は両方 (冬期講習の動画も出る・欄は別)", "共テR 冬期 第1回" in [v["title"] for v in me3.get("videos", [])]
          and [w["key"] for w in me3.get("winter", [])] == ["w26-h3-r"] and len(me3.get("kt", [])) == 7, me3.get("courses"))
    adm = client.get("/api/admin/course/videos", headers=ADMIN).json()
    kc = {c["key"]: c["active_members"] for c in adm.get("kt_courses", [])}
    check("D10. CEO の一覧に過去問の講座と購入者数 (月額講座・冬期講習の欄は変えない)", kc.get("kt-r-2026") == 1 and kc.get("kt-r-2025") == 3
          and kc.get("kt-kokugo-2025") == 0 and len(kc) == 12 and [c["key"] for c in adm["courses"]] == list(mod.COURSE_KEYS)
          and len(adm.get("winter_courses", [])) == len(mod.WINTER_ITEMS), kc)
    vnames = {v["title"]: v["course_name"] for v in adm["videos"]}
    check("D11. 動画の講座名は過去問の講座名", vnames.get("国語 2025 第1問") == "共通テスト過去問 国語 2025年度 本試験", vnames)
    am = {m["email"]: m for m in client.get("/api/admin/course/members", headers=ADMIN).json()["members"]}
    check("D12. 受講者一覧に過去問の講座名", am["buyer@example.invalid"]["kt_names"][0] == "共通テスト過去問 国語 2026年度 本試験"
          and am["monthly@example.invalid"]["kt_names"] == ["共通テスト過去問 英語リーディング 2025年度 本試験"], am.get("buyer@example.invalid"))

    # ---- E. お知らせ ----
    add("kt-r-2025", "英語R 2025 第1〜4問", "RRRRRRRRRR4", "2026-11-26")   # 公開日が明日 → 登録の時は知らせない
    set_today("2026-11-26")
    MAILS.clear()
    d1 = mod._kt_notify_due(dry_run=True)
    check("E2. 朝のまとめ dry_run は送らない", not MAILS and d1.get("dry_run") is True, d1)
    n1 = mod._kt_notify_due()
    sent_to = sorted(m["to"] for m in MAILS)
    body_b = "".join(m["body"] for m in MAILS if m["to"] == "buyer@example.invalid")
    check("E3. 朝のまとめ: 公開日が来た動画を買った人へ 1 人 1 通 (「知らせない」の動画・登録時に知らせた動画は入れない)",
          n1.get("sent") == 3 and sent_to == ["buyer@example.invalid", "missed2@example.invalid", "monthly@example.invalid"]
          and "英語R 2025 第1〜4問" in body_b and "英語R 2026" not in body_b and "course-videos.html?t=" in body_b, (n1, sent_to, body_b[:300]))
    MAILS.clear()
    n2 = mod._kt_notify_due()
    check("E4. 2 回目は 0 通", n2.get("sent") == 0 and not MAILS, n2)
    set_today("2026-12-26")
    MAILS.clear()
    n3 = mod._kt_notify_due()
    check("E5. 第2弾の配信日の朝に 2024 の動画を買った人へ (セットの人だけ)", n3.get("sent") == 1 and [m["to"] for m in MAILS] == ["buyer@example.invalid"]
          and "英語R 2024 第1〜4問" in MAILS[0]["body"] and "共通テスト過去問 解説動画" in MAILS[0]["subject"]
          and "視聴は 2028年3月31日（金） までです" in MAILS[0]["body"], (n3, MAILS))
    set_today("2026-11-25")
    check("E6. 冬期講習の朝のまとめに過去問の動画は混ざらない",
          all(v["course_key"].startswith("w26-") for v in mod._winter_published_videos({"w26-h3-r", "kt-r-2026"})))

    # ---- F. 二重払い・返金・期限・管理 API ----
    n_before = len(fake.created)
    rd = post_form({"items": "kt-kokugo-2026", "email": "buyer@example.invalid"})
    check("F1. 払い済みの年度をもう一度 → 確認画面 (決済画面は作らない・題は過去問)", rd.status_code == 200 and "すでにお支払い済み" in rd.text
          and "国語 2026年度（1年分）" in rd.text and "共通テスト過去問 解説動画" in rd.text and 'name="confirm_dup"' in rd.text
          and len(fake.created) == n_before, rd.text[:300])
    rd2 = post_form({"items": "kt-kokugo-2026", "email": "buyer@example.invalid", "confirm_dup": "1"})
    check("F2. 「それでも進む」(confirm_dup=1) なら決済画面へ", rd2.status_code == 303 and len(fake.created) == n_before + 1)
    rd3 = post_form({"items": "kt-kokugo-set6", "email": "buyer@example.invalid"})
    li3 = fake.created[-1]["line_items"] if fake.created else []
    check("F3. 1 年分 (国語 2026) を持っている人がセットを買うと、確認なしでその分 1,980 円を引く (8,800→6,820)",
          rd3.status_code == 303 and len(li3) == 1 and li3[0]["price_data"]["unit_amount"] == 6820
          and "購入済みの2026年度分を差し引き" in li3[0]["price_data"]["product_data"]["name"] and fake.created[-1]["metadata"]["total"] == "6820", li3)
    p3 = mod._kt_priced_parts(["kt-r-set6"], {"kt-r-2026", "kt-r-2025", "kt-r-2024", "kt-r-2023", "kt-r-2022"})
    check("F3b. 引いても下限は 1 年分の料金 (5 年度持っていても 1,980 円)", p3[0]["price"] == 1980, p3)
    check("F4. 管理 API は認証必須", client.get("/api/admin/kt/purchases").status_code == 401
          and client.post("/api/admin/kt/sync", json={"dry_run": True}).status_code == 401
          and client.post("/api/admin/kt/notify-due", json={"dry_run": True}).status_code == 401
          and client.post("/api/admin/kt/purchases/1/status", json={"status": "refunded"}).status_code in (401, 403))
    pl = client.get("/api/admin/kt/purchases", headers=ADMIN).json()
    pid = [p["id"] for p in pl["purchases"] if p["session_id"] == "cs_live_k1"][0]
    check("F5. 購入一覧 (合計・講座ごとの人数・商品)", pl["view_until"] == "2028-03-31" and {c["key"]: c["buyers"] for c in pl["courses"]}["kt-r-2021"] == 1
          and [p["sku"] for p in pl["products"]] == list(mod.KT_PRODUCTS), pl.get("paid_total"))
    rr = client.post(f"/api/admin/kt/purchases/{pid}/status", headers=ADMIN, json={"remove_items": ["kt-r-2021"]})
    check("F6. 年度ごとの取り消し (remove_items)", rr.status_code == 200 and "kt-r-2021" not in mod._kt_keys_for_email("buyer@example.invalid")
          and len(mod._kt_keys_for_email("buyer@example.invalid")) == 6, rr.text[:200])
    check("F7. 知らない講座・含まれない講座は 400", client.post(f"/api/admin/kt/purchases/{pid}/status", headers=ADMIN, json={"remove_items": ["h3-r"]}).status_code == 400
          and client.post(f"/api/admin/kt/purchases/{pid}/status", headers=ADMIN, json={"remove_items": ["kt-kokugo-2025"]}).status_code == 400)
    client.post(f"/api/admin/kt/purchases/{pid}/status", headers=ADMIN, json={"status": "refunded"})
    me4 = client.get("/api/course/me", headers=H).json()
    check("F8. refunded にすると過去問の講座は視聴ページから消える (冬期講習は残る)", me4.get("kt") == [] and [w["key"] for w in me4.get("winter", [])] == ["w26-h3-r"], me4.get("courses"))
    client.post(f"/api/admin/kt/purchases/{pid}/status", headers=ADMIN, json={"status": "paid"})
    set_today("2028-04-01")
    check("F9. 視聴期間 (2028-03-31) を過ぎたら過去問のキーは無い", mod._kt_keys_for_email("buyer@example.invalid") == [] and mod._kt_buyers() == {})
    set_today("2026-11-25")
    pv = client.post("/api/winter/pv", content=json.dumps({"page": "kakomon", "src": "threads"}), headers={"Content-Type": "text/plain"})
    check("F10. 申込ページの閲覧数 (page=kakomon) を受ける", pv.status_code == 200, pv.text[:200])
    pvs = client.get("/api/admin/winter/pageviews", headers=ADMIN).json()
    check("F11. 冬期講習の閲覧数の合計 (total) に過去問のページは混ぜない (kt_total は別)",
          pvs.get("kt_total", 0) >= 1 and pvs["total"] == sum(r["n"] for r in pvs["rows"] if r["page"] != "kakomon"), pvs)
    set_today("2028-02-01")
    n_before = len(fake.created)
    rc = post_form({"items": "kt-r-2026", "email": "late-buyer@example.invalid"})
    set_today("2026-11-25")
    check("F12. 申込の締切 (KT_SALES_UNTIL 2028-01-31) を過ぎたら決済画面を作らない (410)",
          rc.status_code == 410 and "受付は終了" in rc.text and len(fake.created) == n_before, rc.status_code)

    # ---- H. 画面と表記 ----
    app_js = read("payment/app.js")
    check("H1. 月謝アプリの Stripe 取込は過去問の決済を除外", "system === 'juku-payment-kakomon'" in app_js
          and re.search(r"charges = charges\.filter\(c => !\(\(c\.metadata \|\| \{\}\)\.system === 'juku-payment-kakomon'\)\)", app_js))
    cv = read("course-videos.html")
    check("H2. 視聴ページは me.kt を配信日の欄に入れ、案内文を出す", "(me.kt || []).forEach(function (w) { winter[w.key] = w; });" in cv and 'id="ktNote"' in cv)
    ceo = read("ceo.html")
    check("H3. CEO の講座の選択肢に過去問 (kt_courses)", "addKtOptions(d.kt_courses || [])" in ceo and "m.kt_names" in ceo)
    legal = read("legal.html")
    sec = legal.split('id="tokusho-kakomon"', 1)[1].split("</section>", 1)[0] if 'id="tokusho-kakomon"' in legal else ""
    check("H4. 特商法の表記の金額・視聴期限・配信日がサーバと同じ", sec and f"{mod.KT_PRICE_YEAR:,}円" in sec and f"{mod.KT_PRICE_SET6:,}円" in sec
          and "2028年3月31日" in sec and "2026年12月5日" in sec and "2026年12月26日" in sec and mod.KT_VIEW_UNTIL == "2028-03-31"
          and mod.KT_DELIVERY_1 == "2026-12-05" and mod.KT_DELIVERY_2 == "2026-12-26" and 'href="#tokusho-kakomon"' in legal)

    # ---- G. 署名付き webhook (本体 /api/stripe/webhook) ----
    mod.get_stripe = _orig_get_stripe
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_kt"
    mod.STRIPE_WEBHOOK_SECRET = "whsec_test_kt"
    import stripe as _stripe_lib
    if int(str(getattr(_stripe_lib, "VERSION", "0")).split(".")[0] or 0) >= 14:
        print(f"  ⏭ G. 署名付き webhook: stripe {_stripe_lib.VERSION} ではスキップ (CI の 11.x で実行)")
    else:
        def _signed(pl):
            ts2 = int(time.time())
            return {"Stripe-Signature": f"t={ts2},v1=" + hmac.new(b"whsec_test_kt", f"{ts2}.".encode() + pl, hashlib.sha256).hexdigest(), "Content-Type": "application/json"}
        payload = json.dumps({"id": "evt_kt_1", "object": "event", "api_version": "2024-06-20", "created": int(time.time()), "livemode": True,
                              "type": "checkout.session.completed", "data": {"object": {"object": "checkout.session", "id": "cs_wh_k1",
                              "payment_status": "paid", "amount_total": 1980, "customer_details": {"email": "wh@example.invalid", "name": ""},
                              "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026"}}}}).encode()
        wr = client.post("/api/stripe/webhook", content=payload, headers=_signed(payload))
        check("G1. 署名付き webhook → 記録し、応答は juku-payment skip", wr.status_code == 200 and wr.json().get("skipped_reason") == "juku-payment system tag"
              and mod._kt_keys_for_email("wh@example.invalid") == ["kt-r-2026"], (wr.status_code, wr.text[:200]))
        payload2 = payload.replace(b"evt_kt_1", b"evt_kt_2").replace(b"cs_wh_k1", b"cs_wh_k2").replace(b"wh@example", b"wh2@example")
        conn = mod.db(); conn.cursor().execute("ALTER TABLE kt_purchases RENAME TO kt_purchases_tmp"); conn.commit(); conn.close()
        wf = client.post("/api/stripe/webhook", content=payload2, headers=_signed(payload2))
        conn = mod.db(); conn.cursor().execute("ALTER TABLE kt_purchases_tmp RENAME TO kt_purchases"); conn.commit(); conn.close()
        wr2 = client.post("/api/stripe/webhook", content=payload2, headers=_signed(payload2))
        check("G2. 記録に失敗したら 500 (Stripe が再送)・同じイベントの再送で記録できる", wf.status_code == 500 and wr2.status_code == 200
              and mod._kt_keys_for_email("wh2@example.invalid") == ["kt-r-2026"], (wf.status_code, wr2.text[:200]))
        # 返金の webhook: Stripe への照会が落ちたら 500 (再送で視聴を止められる)
        _orig_sl = _stripe_lib.checkout.Session.list
        _down = {"on": True}
        def _sl(**kw):
            if _down["on"]:
                raise RuntimeError("stripe 503")
            return {"data": [{"id": "cs_wh_k1"}]}
        _stripe_lib.checkout.Session.list = _sl
        rpl = json.dumps({"id": "evt_kt_r1", "object": "event", "api_version": "2024-06-20", "created": int(time.time()), "livemode": True,
                          "type": "charge.refunded", "data": {"object": {"object": "charge", "id": "ch_wh_k1", "payment_intent": "pi_wh_k1",
                          "amount": 1980, "amount_refunded": 1980, "refunded": True, "metadata": {"system": "juku-payment-kakomon"}}}}).encode()
        MAILS.clear()
        try:
            rf1 = client.post("/api/stripe/webhook", content=rpl, headers=_signed(rpl))
            alert_mails = [m for m in MAILS if m["to"] == mod.COURSE_CONTACT_EMAIL and "反映できませんでした" in m["subject"]]
            still = mod._kt_keys_for_email("wh@example.invalid")
            _down["on"] = False
            rf2 = client.post("/api/stripe/webhook", content=rpl, headers=_signed(rpl))
        finally:
            _stripe_lib.checkout.Session.list = _orig_sl
        check("G3. 返金の照会が落ちたら 500・塾長に1通知らせる・同じイベントの再送で視聴が止まる", rf1.status_code == 500 and len(alert_mails) == 1 and still == ["kt-r-2026"]
              and rf2.status_code == 200 and mod._kt_keys_for_email("wh@example.invalid") == [], (rf1.status_code, rf2.status_code, rf2.text[:200]))

    # ---- 決済を同じ画面で開く (2026-11-20)：GET の入口は日本語の案内・エラー画面は「ブラウザの戻る」の文 ----
    rg = client.get("/api/kt/checkout")
    check("Z1. GET の決済入口は日本語の案内 (Not Found にしない)・戻り先は kakomon",
          rg.status_code == 400 and "申込ページでもう一度" in rg.text and "Not Found" not in rg.text and "kakomon" in rg.text, (rg.status_code, rg.text[:200]))
    eg = mod._kt_error_page("テスト")
    check("Z2. 共通テスト過去問のエラー画面は「ブラウザの「戻る」」の文 (「このタブを閉じて」は出さない)",
          "ブラウザの「戻る」" in eg.body.decode() and "このタブを閉じて" not in eg.body.decode())
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}"); sys.exit(1)
    print("✅ 全件 OK")


if __name__ == "__main__":
    main()
