#!/usr/bin/env python3
"""🏛 国公立大学 過去問 解説動画 (/api/kk/checkout・共通テスト過去問と同じ表 kt_purchases・視聴ページ) の回帰テスト (2026-11-28)。
in-process・一時 SQLite。Stripe は偽物、メールは記録器 (ネットワーク不要)。共通テスト過去問 (test_kt_kakomon_course.py) と同じ形。

  A. 料金: 3 年そろった組は 3 年セット 4,800 円だけ・1 年分しかない組は 1 年分 1,980 円・確認待ちの組 (KK_HOLD) は売らない
  B. 決済の入口: KK_SALES_FROM までは閉じている・開いたら Stripe へ 303 (明細・metadata・戻り先 kokkoritsu)・共通テストの商品は買えない
     (逆に /api/kt/checkout で国公立の商品も買えない)・エラー画面の題は「国公立大学 過去問 解説動画」
  C. 記録: kt_purchases に 1 行 (セットは 3 年度に展開)・案内メールは国公立の名前・配信日の文は出さない・すぐ見られる本数
  D. 視聴ページ: /me の kk 欄 (配信日なし・視聴期限)・kt 欄には入らない・自分の組の動画だけ・1 年分を持つ人のセットは差し引き
  E. 表記: 特商法の金額がサーバと同じ・視聴ページの案内文・CEO の選択肢・申込ページの閲覧数の欄
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import tempfile
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
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="kk_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "sk_test_dummy_for_kk", "STRIPE_WEBHOOK_SECRET": "",
        "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "re_dummy", "BASE_URL": "https://example.invalid", "WINTER_SITE_URL": "https://site.example.invalid",
        "KK_SALES_FROM": "",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_kk", MAIN_PY)
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
        outer = self

        class _Session:
            @staticmethod
            def create(**kw):
                outer.created.append(kw)
                return {"id": f"cs_test_{len(outer.created)}", "url": f"https://checkout.stripe.com/c/pay/cs_test_{len(outer.created)}"}

            @staticmethod
            def list(**kw):
                return {"data": []}

        class _Checkout:
            Session = _Session
        self.checkout = _Checkout

        class _PI:
            @staticmethod
            def retrieve(pi, **kw):
                return {"id": pi, "latest_charge": {"amount": 0, "amount_refunded": 0, "refunded": False, "disputed": False}}
        self.PaymentIntent = _PI


def read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def main():
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    print("🏛 国公立大学 過去問 解説動画 回帰テスト")
    mod._course_fetch_from_stripe = lambda email, customer_id="": {"courses": [], "customer_id": "", "name": "", "found": False}
    MAILS = []
    mod._course_send_email = lambda to, subject, body: (MAILS.append({"to": to, "subject": subject, "body": body}) or {"sent": True, "resend_id": "re_x"})
    mod._email_rate_limit = lambda *a, **k: None
    fake = FakeStripe()
    mod.get_stripe = lambda: fake
    ADMIN = {"Authorization": "Bearer " + admin_token(mod)}
    REAL_TODAY = mod._winter_today
    def set_today(d):
        mod._winter_today = (lambda: d) if d else REAL_TODAY
        mod._course_today_jst = (lambda: d) if d else (lambda: datetime.datetime.now(mod.JST).strftime("%Y-%m-%d"))

    # ---- A. 料金 ----
    KP = {k: v for k, v in mod.KT_PRODUCTS.items() if k.startswith("kk-")}
    KC = {k: v for k, v in mod.KT_COURSES.items() if k.startswith("kk-")}
    sets = [k for k in KP if k.endswith("-set3")]
    singles = [k for k in KP if not k.endswith("-set3") and KP[k].get("on_sale", True)]
    check("A1. 3 年セットは理系数学の 5 組 (東大・京大・阪大・九大・東北大)・各 4,800 円・中身は 2026〜2024",
          sets == ["kk-todai-suri-set3", "kk-kyodai-suri-set3", "kk-handai-suri-set3", "kk-kyudai-suri-set3", "kk-tohoku-suri-set3"]
          and all(KP[k]["price"] == 4800 and KP[k]["keys"] == [k[:-5] + f"-{y}" for y in (2026, 2025, 2024)] for k in sets), sets)
    check("A2. 1 年分は 2026 年度だけの 8 組 (国語は確認待ちで売らない)・各 1,980 円",
          singles == ["kk-meidai-suri-2026", "kk-kyodai-subun-2026", "kk-handai-subun-2026", "kk-tohoku-subun-2026",
                      "kk-kyodai-butsuri-2026", "kk-kyodai-kagaku-2026", "kk-kyodai-nihonshi-2026", "kk-kyodai-sekaishi-2026"]
          and all(KP[k]["price"] == 1980 for k in singles), singles)
    check("A3. 3 年セットの組は 1 年分をバラで売らない (表には on_sale=False で残す・入口では unknown)",
          KP["kk-kyodai-suri-2026"].get("on_sale") is False and KP["kk-todai-suri-2024"].get("on_sale") is False
          and mod._kt_plan(["kk-kyodai-suri-2026"], family="kk")["unknown"] == ["kk-kyodai-suri-2026"])
    check("A4. 国語は講座 (動画の登録先) はあるが売らない (on_sale=False)", "kk-kyodai-kokugo-2026" in KC
          and KP["kk-kyodai-kokugo-2026"].get("on_sale") is False and mod._kt_plan(["kk-kyodai-kokugo-2026"], family="kk")["unknown"])
    check("A5. 講座 24 (理系数学 5 組×3 年 15＋2026 年度だけの 9 組 9)・配信日なし・名前", len(KC) == 15 + 9 and all(v["delivery"] is None for v in KC.values())
          and KC["kk-todai-suri-2025"]["name"] == "国公立大学 過去問 東京大学 数学（理科） 2025年度"
          and KC["kk-kyodai-subun-2026"]["name"] == "国公立大学 過去問 京都大学 数学（文系） 2026年度", len(KC))
    check("A6. 講座キーは共通テスト・冬期講習・月額講座と重ならない", not (set(KC) & set(mod.COURSE_KEYS)) and not any(mod._winter_is_video_key(k) for k in KC)
          and not any(k.startswith("kt-") for k in KC))
    pl = mod._kt_plan(["kk-kyodai-suri-set3", "kk-kyodai-subun-2026", "kk-kyodai-suri-set3"], family="kk")
    check("A7. 重複は 1 つ・合計 6,780 円・講座 4", pl["parts"] == ["kk-kyodai-suri-set3", "kk-kyodai-subun-2026"] and pl["total"] == 6780
          and pl["keys"] == ["kk-kyodai-suri-2026", "kk-kyodai-suri-2025", "kk-kyodai-suri-2024", "kk-kyodai-subun-2026"], pl)
    check("A8. 入口ごとに売るものを分ける (kk の入口で kt の商品・kt の入口で kk の商品は unknown)",
          mod._kt_plan(["kt-r-2026"], family="kk")["unknown"] == ["kt-r-2026"] and mod._kt_plan(["kk-handai-subun-2026"], family="kt")["unknown"] == ["kk-handai-subun-2026"])
    pp = mod._kt_priced_parts(["kk-kyodai-suri-set3"], {"kk-kyodai-suri-2026"})
    check("A9. 1 年分を持つ人の 3 年セットは 1,980 円を差し引き (2,820 円)", pp[0]["price"] == 2820 and "2026年度分を差し引き" in pp[0]["name"], pp)
    pp2 = mod._kt_priced_parts(["kk-kyodai-suri-set3"], {"kk-kyodai-suri-2026", "kk-kyodai-suri-2025"})
    check("A10. 2 年分を持つ人の 3 年セットは 840 円 (1 年分につき 1,980 円・下限で上げない)", pp2[0]["price"] == 840, pp2)
    pp3 = mod._kt_priced_parts(["kt-r-set6"], {f"kt-r-{y}" for y in (2026, 2025, 2024, 2023, 2022)})
    check("A11. 共通テストの直前セットの下限 (1,980 円) は今までどおり", pp3[0]["price"] == 1980, pp3)
    os.environ["KK_SALES_FROM"] = ""
    mod.KK_SALES_FROM = "2026-12-1"
    check("A12. KK_SALES_FROM の形が違えば閉じたまま", mod._kk_sales_open("2027-01-01") is False)
    mod.KK_SALES_FROM = ""

    # ---- B. 決済の入口 ----
    def post(fields, path="/api/kk/checkout"):
        return client.post(path, content=urllib.parse.urlencode(fields, doseq=True),
                           headers={"Content-Type": "application/x-www-form-urlencoded"}, follow_redirects=False)
    set_today("2026-12-01")
    r0 = post({"items": "kk-kyodai-suri-set3", "email": "a@example.invalid"})
    check("B1. KK_SALES_FROM が空なら閉じている (503・決済画面を作らない)", r0.status_code == 503 and "まだ始まっていません" in r0.text
          and "国公立大学 過去問 解説動画" in r0.text and not fake.created, (r0.status_code, r0.text[:200]))
    mod.KK_SALES_FROM = "2026-12-02"
    r0b = post({"items": "kk-kyodai-suri-set3", "email": "a@example.invalid"})
    check("B2. 受付の前日も閉じている", r0b.status_code == 503 and not fake.created, r0b.status_code)
    set_today("2026-12-02")
    r = post({"items": ["kk-kyodai-suri-set3,kk-kyodai-subun-2026"], "email": " Buyer@Example.invalid ", "app_id": "KK-abc123"})
    kw = fake.created[-1] if fake.created else {}
    names = [li["price_data"]["product_data"]["name"] for li in kw.get("line_items", [])]
    amts = [li["price_data"]["unit_amount"] for li in kw.get("line_items", [])]
    meta = kw.get("metadata") or {}
    check("B3. 受付の日から 303 で Stripe へ・明細 4,800＋1,980・商品名は国公立", r.status_code == 303 and amts == [4800, 1980]
          and names == ["国公立大学 過去問 解説動画 京都大学 数学（理系） 3年セット（2024〜2026年度）", "国公立大学 過去問 解説動画 京都大学 数学（文系） 2026年度（1年分）"],
          (r.status_code, names, amts))
    check("B4. metadata は共通テストと同じタグ・page=kokkoritsu・戻り先は kokkoritsu のページ",
          meta.get("system") == "juku-payment-kakomon" and meta.get("items") == "kk-kyodai-suri-set3,kk-kyodai-subun-2026" and meta.get("total") == "6780"
          and meta.get("page") == "kokkoritsu" and (kw.get("payment_intent_data") or {}).get("description") == "国公立大学 過去問 解説動画"
          and kw.get("success_url") == "https://site.example.invalid/kokkoritsu-thanks.html?session_id={CHECKOUT_SESSION_ID}"
          and kw.get("cancel_url") == "https://site.example.invalid/kokkoritsu.html?canceled=1" and kw.get("client_reference_id") == "kk-KK-abc123", kw)
    n0 = len(fake.created)
    rb = post({"items": "kt-r-2026", "email": "a@example.invalid"})
    check("B5. 国公立の入口で共通テストの商品は 400 (題・戻り先は国公立)", rb.status_code == 400 and "講座の指定" in rb.text
          and "国公立大学 過去問 解説動画" in rb.text and "kokkoritsu.html" in rb.text and "共通テスト" not in rb.text, rb.text[:300])
    rk = post({"items": "kk-kyodai-kokugo-2026", "email": "a@example.invalid"})
    check("B6. 確認待ちの国語は買えない (400)", rk.status_code == 400 and "講座の指定" in rk.text)
    rt = post({"items": "kk-kyodai-subun-2026", "email": "a@example.invalid"}, path="/api/kt/checkout")
    check("B7. 共通テストの入口で国公立の商品は 400 (共通テストの題のまま)", rt.status_code == 400 and "共通テスト過去問 解説動画" in rt.text and "kakomon.html" in rt.text, rt.text[:300])
    check("B8. だめなときは決済画面を作らない", len(fake.created) == n0)
    rg = client.get("/api/kk/checkout")
    check("B9. GET の入口は日本語の案内・戻り先は kokkoritsu", rg.status_code == 400 and "申込ページでもう一度" in rg.text and "kokkoritsu.html" in rg.text, rg.text[:200])
    ok_kt = post({"items": "kt-r-2026", "email": "kt@example.invalid"}, path="/api/kt/checkout")
    check("B10. 共通テストの入口は今までどおり (KK_SALES_FROM に関係なく 303・戻り先 kakomon)", ok_kt.status_code == 303
          and fake.created[-1]["success_url"].endswith("/kakomon-thanks.html?session_id={CHECKOUT_SESSION_ID}")
          and fake.created[-1]["line_items"][0]["price_data"]["product_data"]["name"].startswith("共通テスト過去問 解説動画"), ok_kt.status_code)

    # ---- C. 記録 ----
    MAILS.clear()
    def add(key, title, yid, pub="2026-12-02", notify=False):
        return client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": key, "title": title, "youtube_url": "https://youtu.be/" + yid,
                                                                           "publish_date": pub, "notify": notify})
    rv = [add("kk-kyodai-suri-2024", f"京大 理系 2024 第{i}問", f"AAAAAAAAA{i:02d}"[-11:]) for i in (1, 2)]
    rv += [add("kk-kyodai-suri-2026", "京大 理系 2026 第1問", "BBBBBBBBB01"), add("kk-kyodai-subun-2026", "京大 文系 2026 第1問", "CCCCCCCCC01"),
           add("kk-handai-subun-2026", "阪大 文系 2026 第1問", "DDDDDDDDD01"), add("kk-kyodai-kokugo-2026", "京大 国語 2026 第1問", "EEEEEEEEE01")]
    check("C0. 国公立の講座 (売っていない国語も) に動画を登録できる・セットのキー (set3) は 400", all(x.status_code == 200 for x in rv)
          and add("kk-kyodai-suri-set3", "x", "XXXXXXXXX01").status_code == 400, [x.status_code for x in rv])
    sess = {"id": "cs_live_kk1", "object": "checkout.session", "payment_status": "paid", "livemode": True, "amount_total": 6780,
            "customer_details": {"email": "Buyer@Example.invalid", "name": "国公立 太郎"},
            "metadata": {"system": "juku-payment-kakomon", "items": "kk-kyodai-suri-set3,kk-kyodai-subun-2026", "total": "6780", "page": "kokkoritsu"}}
    r1 = mod._kt_webhook_record(sess)
    r2 = mod._kt_webhook_record(dict(sess))
    conn = mod.db(); c = conn.cursor(); c.execute("SELECT * FROM kt_purchases"); rows = c.fetchall(); conn.close()
    exp_keys = ["kk-kyodai-suri-2026", "kk-kyodai-suri-2025", "kk-kyodai-suri-2024", "kk-kyodai-subun-2026"]
    check("C1. kt_purchases に 1 行 (セットを 3 年度に展開・再送で増えない)", r1 is True and r2 is True and len(rows) == 1
          and json.loads(rows[0]["item_keys"]) == exp_keys and rows[0]["amount"] == 6780 and rows[0]["status"] == "paid", [dict(x) for x in rows])
    body0 = MAILS[0]["body"] if MAILS else ""
    check("C2. 案内メール 1 通: 件名・本文は国公立の名前・配信日の文なし・すぐ見られる本数 (4 本)・視聴期限",
          len(MAILS) == 1 and "国公立大学 過去問 解説動画" in MAILS[0]["subject"] and "共通テスト" not in MAILS[0]["subject"] + body0
          and "・国公立大学 過去問 京都大学 数学（理系） 2024年度\n" in body0 and "配信 " not in body0 and "配信日" not in body0
          and "動画（4本）は、下のリンクから" in body0 and "2028年3月31日（金）" in body0 and "course-videos.html?t=" in body0, MAILS)
    welcome = [l for l in body0.splitlines() if "course-videos.html?t=" in l]

    MAILS.clear()
    r_off = mod._kt_webhook_record({"id": "cs_live_off", "payment_status": "paid", "amount_total": 1980, "livemode": True,
                                    "customer_email": "off@example.invalid", "metadata": {"system": "juku-payment-kakomon", "items": "kk-kyodai-suri-2026"}})
    check("C3. 売るのをやめた 1 年分 (切りかえの前に開いた決済画面) で払われても記録して視聴を付ける・塾長への「付けられない」は出ない",
          r_off is True and mod._kt_keys_for_email("off@example.invalid") == ["kk-kyodai-suri-2026"]
          and not any("付けられない" in m["subject"] for m in MAILS), MAILS)

    # ---- D. 視聴ページ ----
    vr = client.post("/api/course/login/verify", json={"token": welcome[0].split("?t=", 1)[1].strip() if welcome else ""})
    H = {"Authorization": "Bearer " + (vr.json().get("token") or "")} if vr.status_code == 200 else {}
    me = client.get("/api/course/me", headers=H).json() if H else {}
    vids = sorted(v["title"] for v in me.get("videos", []))
    check("D1. 国公立だけの人もログインでき、自分の組の動画だけ見られる (阪大・国語は出ない)",
          vr.status_code == 200 and vids == sorted(["京大 理系 2024 第1問", "京大 理系 2024 第2問", "京大 理系 2026 第1問", "京大 文系 2026 第1問"]), (vr.status_code, vids))
    check("D2. /me の kk 欄 (配信日なし・視聴期限)・kt 欄は空", [w["key"] for w in me.get("kk", [])] == exp_keys and all(w["delivery"] is None for w in me.get("kk", []))
          and me.get("kk_view_until") == "2028-03-31" and me.get("kt") == [] and me.get("kt_view_until") is None, json.dumps(me, ensure_ascii=False)[:400])
    # 共通テストも買った人は欄が分かれる
    mod._kt_webhook_record({"id": "cs_live_kk2", "payment_status": "paid", "amount_total": 1980, "livemode": True, "customer_email": "buyer@example.invalid",
                            "metadata": {"system": "juku-payment-kakomon", "items": "kt-r-2026"}})
    me2 = client.get("/api/course/me", headers=H).json()
    check("D3. 共通テストも買った人は kt と kk の欄が分かれる", [w["key"] for w in me2.get("kt", [])] == ["kt-r-2026"] and len(me2.get("kk", [])) == 4
          and me2.get("kt_view_until") == "2028-03-31", json.dumps(me2, ensure_ascii=False)[:300])
    # 二重払いの確認画面
    rd = post({"items": "kk-kyodai-suri-set3", "email": "buyer@example.invalid"})
    check("D4. 買った組をもう一度選ぶと確認画面 (題は国公立・戻り先 kokkoritsu)", rd.status_code == 200 and "すでにお支払い済み" in rd.text
          and "国公立大学 過去問 解説動画" in rd.text and "kokkoritsu.html" in rd.text, rd.text[:300])
    # 1 年分を持つ人のセット (将来 3 年そろった組) の差し引き: 決済画面の金額で確かめる
    mod._kt_webhook_record({"id": "cs_live_kk3", "payment_status": "paid", "amount_total": 1980, "livemode": True, "customer_email": "one@example.invalid",
                            "metadata": {"system": "juku-payment-kakomon", "items": "kk-kyodai-subun-2026"}})
    mod.KT_PRODUCTS["kk-kyodai-subun-set3"] = {"name": "京都大学 数学（文系） 3年セット（2024〜2026年度）", "price": 4800,
                                              "keys": ["kk-kyodai-subun-2026", "kk-kyodai-subun-2025", "kk-kyodai-subun-2024"], "subject": "kk-kyodai-subun"}
    for y in (2025, 2024):
        mod.KT_COURSES[f"kk-kyodai-subun-{y}"] = {"name": f"国公立大学 過去問 京都大学 数学（文系） {y}年度", "subject": "kk-kyodai-subun", "year": y, "delivery": None}
    r_up = post({"items": "kk-kyodai-subun-set3", "email": "one@example.invalid"})
    check("D5. 1 年分を持つ人が 3 年セットを買うと 2,820 円 (購入済みの年度を差し引き)", r_up.status_code == 303
          and fake.created[-1]["line_items"][0]["price_data"]["unit_amount"] == 2820, r_up.status_code)
    del mod.KT_PRODUCTS["kk-kyodai-subun-set3"]
    set_today("2028-02-01")
    rc = post({"items": "kk-handai-subun-2026", "email": "late@example.invalid"})
    check("D6. 申込の締切 (2028-01-31) を過ぎたら 410", rc.status_code == 410 and "受付は終了" in rc.text and "国公立大学" in rc.text, rc.text[:200])
    set_today("2028-04-01")
    check("D7. 視聴期限 (2028-03-31) を過ぎたら見られない", mod._kt_keys_for_email("buyer@example.invalid") == [])
    set_today("2026-12-02")

    # ---- E. 表記・画面 ----
    legal = read("legal.html")
    check("E1. 特商法に国公立の節 (3 年セット 4,800円・1 年分 1,980円 = サーバと同じ・視聴期限・目次)",
          'id="tokusho-kokkoritsu"' in legal and 'href="#tokusho-kokkoritsu"' in legal
          and f"{mod.KK_PRICE_SET3:,}円" in legal and f"{mod.KK_PRICE_YEAR:,}円" in legal and "2028年3月31日まで" in legal)
    cv = read("course-videos.html")
    check("E2. 視聴ページに国公立の案内文 (me.kk)", 'id="kkNote"' in cv and "me.kk" in cv and "国公立大学の過去問" in cv)
    ceo = read("ceo.html")
    check("E3. CEO の講座の選択肢に「国公立大学 過去問」の組", "国公立大学 過去問" in ceo and "/^kk-/.test(c.key)" in ceo)
    adm = client.get("/api/admin/course/videos", headers=ADMIN).json()
    kc = {c["key"]: c["active_members"] for c in adm.get("kt_courses", [])}
    check("E4. CEO の一覧に国公立の講座と購入者数", kc.get("kk-kyodai-suri-2025") == 1 and kc.get("kk-handai-subun-2026") == 0, kc)
    check("E5. 申込ページの閲覧数に kokkoritsu (冬期講習の合計には入れない)", "kokkoritsu" in mod._WINTER_PV_PAGES)
    pay = read("payment/app.js")
    check("E6. 月謝アプリの取込は同じタグ (juku-payment-kakomon) で除外済み", "juku-payment-kakomon" in pay)
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}"); sys.exit(1)
    print("✅ 全件 OK")


if __name__ == "__main__":
    main()
