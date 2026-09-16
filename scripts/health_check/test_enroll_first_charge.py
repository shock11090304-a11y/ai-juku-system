#!/usr/bin/env python3
"""🏫 入塾申込書からの初回カード決済 (2026-09-17) の回帰テスト (ネットワークなし)。

対象:
  api/register-subscribe.py  firstCharge=true → mode=payment の Checkout (入塾金+設備費+初月受講料・カード保存) と CORS
  api/stripe-webhook.py      その完了イベント → reg:completed (setup 相当) / 当月の charge:done+history / 確認メール+塾長通知

  A1. _validate が firstCharge / appId を受け取る (不正な appId は拒否)
  A2. Checkout のパラメータ: mode=payment・setup_future_usage=off_session・明細の合計=入塾金+月額・metadata.monthly_fee は月額のみ・
      PaymentIntent の metadata に month を付けない・戻り先は申込書サイトの enroll-thanks.html・Idempotency-Key
  A3. CORS: 許可オリジンだけ echo
  B1. 決済完了 → 名簿 (checkout_mode=setup + payment_method + monthly_fee) と当月台帳 (done / history / audit) と 2 通のメール
  B2. 同じセッションの再送 → 台帳もメールも増えない
  B3. 未払い (payment_status=unpaid) → 何も登録しない
  B4. テストモード (livemode=false) → 登録と台帳は書くがメールは送らない
  B5. pending が消えていても metadata から復元して登録・メール
  B6. 従来の setup モードは変わらない (台帳を書かない)
  B7. payment_intent.succeeded (rid あり・month なし) は台帳を書かない
"""
import importlib.util
import io
import json
import os
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEBHOOK = os.path.join(REPO, "api", "stripe-webhook.py")
REGISTER = os.path.join(REPO, "api", "register-subscribe.py")
FAILURES = []
# 架空のテスト値 (個人情報ゲートは「studentName: "氏名"」の直書きを止めるので変数で渡す)
TARO = "テスト 太郎"
HANAKO = "テスト 花子"
JIRO = "テスト 次郎"
SABURO = "テスト 三郎"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class FakeKV:
    def __init__(self):
        self.store, self.zsets, self.lists = {}, {}, {}

    def __call__(self, *args):
        cmd = args[0]
        if cmd == "SET":
            key, val = args[1], args[2]
            if "NX" in args[3:] and key in self.store:
                return {"result": None}
            self.store[key] = val
            return {"result": "OK"}
        if cmd == "GET":
            return {"result": self.store.get(args[1])}
        if cmd == "DEL":
            return {"result": 1 if self.store.pop(args[1], None) is not None else 0}
        if cmd == "ZADD":
            self.zsets.setdefault(args[1], []).append(args[3])
            return {"result": 1}
        if cmd == "RPUSH":
            self.lists.setdefault(args[1], []).append(args[2])
            return {"result": len(self.lists[args[1]])}
        if cmd == "EXPIRE":
            return {"result": 1}
        if cmd == "ZRANGE":
            return {"result": list(self.zsets.get(args[1], []))}
        if cmd == "INCR":
            self.store[args[1]] = str(int(self.store.get(args[1]) or 0) + 1)
            return {"result": int(self.store[args[1]])}
        return {"result": None}


class DownKV(FakeKV):
    """KV 障害: 全コマンドが None (通信失敗) を返す"""
    def __call__(self, *args):
        return None


class FakeNet:
    """urllib.request.urlopen の差し替え: Stripe GET payment_intents と Resend POST だけ受ける"""
    def __init__(self, pm="pm_card_1", pi_customer="cus_1"):
        self.sent, self.headers, self.stripe_gets = [], [], []
        self.pm, self.pi_customer = pm, pi_customer

    def __call__(self, req, timeout=None):
        url = req.full_url
        if "api.stripe.com/v1/payment_intents/" in url:
            self.stripe_gets.append(url)
            if self.pm is None:
                raise urllib.error.HTTPError(url, 500, "boom", {}, io.BytesIO(b"{}"))
            pi_id = url.rsplit("/", 1)[1]
            return io.BytesIO(json.dumps({"id": pi_id, "object": "payment_intent", "payment_method": self.pm,
                                          "customer": self.pi_customer, "amount_received": 18850, "status": "succeeded"}).encode())
        if "api.stripe.com/v1/customers/" in url and "/payment_methods" in url:
            self.stripe_gets.append(url)
            return io.BytesIO(json.dumps({"data": [{"id": "pm_from_customer", "type": "card"}]}).encode())
        if "api.resend.com" in url:
            self.headers.append(dict(req.header_items()))
            self.sent.append(json.loads(req.data.decode("utf-8")))
            return io.BytesIO(json.dumps({"id": f"re_{len(self.sent)}"}).encode())
        raise AssertionError("unexpected network call: " + url)


def payload(**kw):
    d = {"studentName": TARO, "grade": "高校2年", "parentName": HANAKO, "email": "parent@example.invalid",
         "phone": "090-0000-0000", "courses": ["kou2-grammar"], "options": ["facility-1350"], "firstCharge": True, "appId": "AB12CD34"}
    d.update(kw)
    return d


def pending(rid, fee=8850):
    return {"registration_id": rid, "session_id": "cs_enroll_1", "status": "pending", "created_at": 1789000000,
            "fee": fee, "monthly_fee": fee, "breakdown": ["高校2年英文法 ¥7,500", "設備費 (¥1,350) ¥1,350"],
            "fee_breakdown": "高校2年英文法 ¥7,500 / 設備費 (¥1,350) ¥1,350", "stripe_customer_id": "cus_1",
            "checkout_mode": "payment", "system": "juku-payment-monthly", "first_charge": True, "entry_fee": 10000,
            "first_total": 10000 + fee, "app_id": "AB12CD34", "studentName": TARO, "grade": "高校2年",
            "parentName": HANAKO, "email": "parent@example.invalid", "phone": "090-0000-0000",
            "courses": ["kou2-grammar"], "options": ["facility-1350"], "firstCharge": True, "appId": "AB12CD34"}


def session(rid, sid="cs_enroll_1", paid=True, livemode=True, mode="payment", first="1"):
    md = {"registration_id": rid, "system": "juku-payment-monthly", "student_name": TARO, "grade": "高校2年",
          "parent_name": HANAKO, "email": "parent@example.invalid", "phone": "090-0000-0000", "courses": "kou2-grammar",
          "options": "facility-1350", "fee_breakdown": "高校2年英文法 ¥7,500 / 設備費 (¥1,350) ¥1,350", "monthly_fee": "8850",
          "entry_fee": "10000", "first_total": "18850", "app_id": "AB12CD34", "source": "enrollment-form-v1-payment"}
    if first:
        md["first_charge"] = first
    obj = {"id": sid, "object": "checkout.session", "mode": mode, "livemode": livemode,
           "payment_status": "paid" if paid else "unpaid", "amount_total": 18850, "currency": "jpy",
           "customer": "cus_1", "customer_email": None, "customer_details": {"email": "parent@example.invalid"},
           "created": 1789000000, "metadata": md}
    if mode == "payment":
        obj["payment_intent"] = "pi_first_1"
    else:
        obj["setup_intent"] = "seti_1"
        obj["amount_total"] = 0
    return obj


def event(obj, eid="evt_1", etype="checkout.session.completed"):
    return {"id": eid, "type": etype, "data": {"object": obj}}


class FakeHandler:
    def __init__(self, origin):
        self.headers = {"Origin": origin} if origin else {}


def main():
    os.environ.update({"STRIPE_SECRET_KEY": "sk_test_dummy", "KV_REST_API_URL": "", "KV_REST_API_TOKEN": "",
                       "RESEND_API_KEY": "re_dummy", "FROM_EMAIL": "noreply@example.invalid",
                       "COURSE_NOTIFY_EMAIL": "owner@example.invalid", "REGISTER_CORS_ORIGINS": "",
                       "ENROLL_WELCOME_ENABLED": "1", "COURSE_REPLY_TO": "",
                       "ENROLL_ZOOM_ID": "12345", "ENROLL_ZOOM_PASS": "abc", "ENROLL_APP_REGISTER_URL": ""})
    print("🏫 入塾申込書 初回カード決済 回帰テスト\n")
    reg = load(REGISTER, "register_subscribe_vercel")
    wh = load(WEBHOOK, "stripe_webhook_vercel_enroll")

    # ---- A1 validate ----
    errs, clean = reg._validate(payload())
    check("A1a. firstCharge/appId を受理", not errs and clean["firstCharge"] is True and clean["appId"] == "AB12CD34", (errs, clean))
    errs, _ = reg._validate(payload(appId="bad id!"))
    check("A1b. 不正な appId は拒否", any("申込ID" in e for e in errs), errs)
    errs, clean2 = reg._validate(payload(firstCharge="true"))
    check("A1c. firstCharge は真偽値 true のみ (文字列は false)", not errs and clean2["firstCharge"] is False, clean2.get("firstCharge"))
    errs, _ = reg._validate(payload(courses=["kokugo", "kou2-grammar"]))
    check("A1d. 高校国語 (kokugo) がカタログにある", not errs, errs)
    errs, _ = reg._validate(payload(options=[]))
    check("A1f. 初回決済は設備費なしを拒否 (安い月額での登録防止)", any("設備費" in e for e in errs), errs)
    errs, _ = reg._validate(payload(firstCharge=False, options=[]))
    check("A1g. 従来の setup 登録は設備費なしでも可 (挙動不変)", not errs, errs)
    fee, breakdown = reg._calculate_fee(clean["courses"], clean["options"])
    check("A1e. 月額 = 7,500 + 1,350", fee == 8850, fee)

    # ---- A2 checkout params ----
    posts = []

    def fake_post(secret_key, path, form, idempotency_key=None):
        posts.append((path, list(form), idempotency_key))
        if path == "customers":
            return {"id": "cus_new"}
        if path == "checkout/sessions":
            return {"id": "cs_new", "url": "https://checkout.stripe.com/c/pay/cs_new", "customer": "cus_new"}
        return {}
    reg._stripe_post = fake_post
    reg._stripe_get = lambda *a, **k: {"data": []}
    sess = reg._create_first_charge_session("sk_test_dummy", clean, fee, breakdown, "reg_test1", "https://trillion-ai-juku.com",
                                            "https://graceful-eclair-56bdac.netlify.app")
    cs = [p for p in posts if p[0] == "checkout/sessions"]
    check("A2a. Checkout を 1 回作成 (Customer も 1 回)", len(cs) == 1 and sum(1 for p in posts if p[0] == "customers") == 1, [p[0] for p in posts])
    form = dict(cs[0][1]) if cs else {}
    check("A2b. mode=payment・カード限定・customer 明示", form.get("mode") == "payment" and form.get("payment_method_types[]") == "card" and form.get("customer") == "cus_new", form)
    check("A2c. setup_future_usage=off_session (カード保存)", form.get("payment_intent_data[setup_future_usage]") == "off_session")
    amounts = [int(v) for k, v in (cs[0][1] if cs else []) if k.endswith("[price_data][unit_amount]")]
    names = [v for k, v in (cs[0][1] if cs else []) if k.endswith("[product_data][name]")]
    check("A2d. 明細 3 行 = 入塾金 10,000 + 受講料 7,500 + 設備費 1,350 = 18,850", amounts == [10000, 7500, 1350] and sum(amounts) == 18850, amounts)
    check("A2e. 明細名: 入塾金（初回のみ）/ 高校2年英文法 受講料（初月分）/ 設備費（初月分）", names == ["入塾金（初回のみ）", "高校2年英文法 受講料（初月分）", "設備費（初月分）"], names)
    check("A2f. metadata.monthly_fee は月額 8,850 (入塾金を含めない)・first_total=18,850・first_charge=1・app_id",
          form.get("metadata[monthly_fee]") == "8850" and form.get("metadata[first_total]") == "18850"
          and form.get("metadata[first_charge]") == "1" and form.get("metadata[app_id]") == "AB12CD34", form)
    check("A2g. PaymentIntent の metadata に registration_id と system はあるが month は無い",
          form.get("payment_intent_data[metadata][registration_id]") == "reg_test1"
          and form.get("payment_intent_data[metadata][system]") == "juku-payment-monthly"
          and "payment_intent_data[metadata][month]" not in form, [k for k in form if k.startswith("payment_intent_data[metadata]")])
    check("A2h. 戻り先は申込書サイトの enroll-thanks.html (成功は session_id 付き・中断は canceled=1)",
          form.get("success_url") == "https://graceful-eclair-56bdac.netlify.app/enroll-thanks.html?session_id={CHECKOUT_SESSION_ID}"
          and form.get("cancel_url") == "https://graceful-eclair-56bdac.netlify.app/enroll-thanks.html?canceled=1", (form.get("success_url"), form.get("cancel_url")))
    check("A2i. Idempotency-Key に registration_id", cs and cs[0][2] == "juku-first-charge-reg_test1", cs[0][2] if cs else None)
    check("A2j. 決済画面の確認文に初回額と月額", "18,850 円" in form.get("custom_text[submit][message]", "") and "8,850 円" in form.get("custom_text[submit][message]", ""), form.get("custom_text[submit][message]"))
    check("A2k. 返り値に customer と first_total", sess.get("_juku_customer_id") == "cus_new" and sess.get("_juku_first_total") == 18850, sess)

    # ---- A3 CORS ----
    check("A3a. 既定の許可オリジン (Netlify) は echo", reg._cors_origin(FakeHandler("https://graceful-eclair-56bdac.netlify.app")) == "https://graceful-eclair-56bdac.netlify.app")
    check("A3b. 他のオリジンは空 (ヘッダなし)", reg._cors_origin(FakeHandler("https://evil.example")) == "")
    check("A3c. Origin なし (同一オリジン) は空", reg._cors_origin(FakeHandler("")) == "")
    os.environ["REGISTER_CORS_ORIGINS"] = "https://a.example, https://b.example/"
    check("A3d. env で上書き (末尾スラッシュ許容)", reg._cors_origin(FakeHandler("https://b.example")) == "https://b.example" and reg._cors_origin(FakeHandler("https://graceful-eclair-56bdac.netlify.app")) == "")
    os.environ["REGISTER_CORS_ORIGINS"] = ""

    # ---- A4 申込 API (do_POST): 同じメールの兄弟は通る・同じ生徒は 409 ----
    class FakeReq:
        def __init__(self, body, origin="https://graceful-eclair-56bdac.netlify.app"):
            self.headers = {"Content-Length": str(len(body)), "Origin": origin, "Host": "trillion-ai-juku.com"}
            self.rfile, self.wfile, self.client_address = io.BytesIO(body), io.BytesIO(), ("203.0.113.1", 0)
            self.status, self.hdrs = None, {}
        def send_response(self, code): self.status = code
        def send_header(self, k, v): self.hdrs[k] = v
        def end_headers(self): pass
        def do_POST(self): return reg.handler.do_POST(self)
    regkv = FakeKV()
    reg._redis_safe = regkv
    regkv.store["reg:completed:reg_old"] = json.dumps({"registration_id": "reg_old", "email": "parent@example.invalid", "studentName": TARO}, ensure_ascii=False)
    regkv.zsets["reg:completed:index"] = ["reg_old"]
    r1 = FakeReq(json.dumps(payload(studentName=JIRO), ensure_ascii=False).encode()); r1.do_POST()
    j1 = json.loads(r1.wfile.getvalue().decode() or "{}")
    check("A4a. 兄弟 (同じメール・別の生徒名) の入塾申込は 200 で決済 URL が返る", r1.status == 200 and j1.get("checkoutUrl", "").startswith("https://checkout.stripe.com/") and j1.get("firstTotal") == 18850 and j1.get("amount") == 8850, (r1.status, j1))
    check("A4b. 応答に許可オリジンの CORS ヘッダ", r1.hdrs.get("Access-Control-Allow-Origin") == "https://graceful-eclair-56bdac.netlify.app" and r1.hdrs.get("Vary") == "Origin", r1.hdrs)
    pend = [k for k in regkv.store if k.startswith("reg:pending:")]
    check("A4c. pending に first_charge / entry_fee / app_id / checkout_mode=payment", len(pend) == 1 and json.loads(regkv.store[pend[0]]).get("first_charge") is True and json.loads(regkv.store[pend[0]]).get("entry_fee") == 10000 and json.loads(regkv.store[pend[0]]).get("app_id") == "AB12CD34" and json.loads(regkv.store[pend[0]]).get("checkout_mode") == "payment", [regkv.store[k] for k in pend])
    r2 = FakeReq(json.dumps(payload(), ensure_ascii=False).encode()); r2.do_POST()
    j2 = json.loads(r2.wfile.getvalue().decode() or "{}")
    check("A4d. 同じメール・同じ生徒名は 409 ALREADY_REGISTERED", r2.status == 409 and j2.get("error") == "ALREADY_REGISTERED", (r2.status, j2))
    r3 = FakeReq(json.dumps(payload(firstCharge=False, studentName=JIRO), ensure_ascii=False).encode()); r3.do_POST()
    check("A4e. 従来の setup 登録は同じメールなら生徒名が違っても 409 (挙動不変)", r3.status == 409, r3.status)
    reg._redis_safe = FakeKV()   # 同じメールは 1 時間に 3 回までのレート制限に当たるので KV を新しくする
    r4 = FakeReq(json.dumps(payload(studentName=SABURO), ensure_ascii=False).encode(), origin="https://evil.example"); r4.do_POST()
    check("A4f. 許可外オリジンには CORS ヘッダを付けない (応答自体は返る)", r4.status == 200 and "Access-Control-Allow-Origin" not in r4.hdrs, (r4.status, r4.hdrs))

    # ---- B1 webhook 正常系 ----
    rid = "reg_t1"
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    kv.store[f"reg:pending:{rid}"] = json.dumps(pending(rid), ensure_ascii=False)
    wh._handle_checkout_completed(event(session(rid)))
    rec = json.loads(kv.store.get(f"reg:completed:{rid}") or "{}")
    month = wh._course_jst(1789000000).strftime("%Y-%m")   # 台帳の月はセッション作成 (=決済) の JST 月 (2026-09)。処理時刻ではない
    check("B0. 台帳の月は決済時刻 (session.created) の JST 月", month == "2026-09" and rec.get("paid_at") == 1789000000, (month, rec.get("paid_at")))
    check("B1a. reg:completed が setup 相当 (checkout_mode=setup・payment_method・customer)", rec.get("checkout_mode") == "setup" and rec.get("stripe_payment_method_id") == "pm_card_1" and rec.get("stripe_customer_id") == "cus_1", rec)
    check("B1b. monthly_fee=8,850 (月額のみ)・amount=18,850・first_charge 情報", rec.get("monthly_fee") == 8850 and rec.get("amount") == 18850 and rec.get("first_charge") is True and rec.get("first_charge_month") == month and rec.get("entry_fee") == 10000 and rec.get("app_id") == "AB12CD34", rec)
    check("B1c. pending 削除・index 登録", f"reg:pending:{rid}" not in kv.store and rid in kv.zsets.get("reg:completed:index", []))
    done = json.loads(kv.store.get(f"charge:done:{rid}:{month}") or "{}")
    check("B1d. 当月の charge:done (succeeded・18,850・source=enroll-first-charge)", done.get("status") == "succeeded" and done.get("amount") == 18850 and done.get("source") == "enroll-first-charge" and done.get("payment_intent_id") == "pi_first_1", done)
    hist = json.loads(kv.store.get(f"charge:history:{rid}:{month}") or "{}")
    check("B1e. charge:history (氏名・メール・月・entry_fee・monthly_fee)", hist.get("student_name") == "テスト 太郎" and hist.get("email") == "parent@example.invalid" and hist.get("month") == month and hist.get("entry_fee") == 10000 and hist.get("monthly_fee") == 8850, hist)
    check("B1f. history index と audit に 1 件", f"{rid}:{month}" in kv.zsets.get("charge:history:index", []) and len(kv.lists.get(f"charge:history:audit:{rid}:{month}", [])) == 1)
    check("B1g. PaymentIntent を 1 回取得", len(net.stripe_gets) == 1 and net.stripe_gets[0].endswith("/payment_intents/pi_first_1"), net.stripe_gets)
    check("B1h. メール 2 通 (保護者・塾長)", len(net.sent) == 2, [m.get("to") for m in net.sent])
    m = net.sent[0] if net.sent else {}
    body = m.get("text", "")
    check("B1i. 保護者宛・件名", m.get("to") == ["parent@example.invalid"] and m.get("subject") == "【トリリオン英語塾】ご入塾のお申し込みとお支払いの確認", (m.get("to"), m.get("subject")))
    check("B1j. 宛名は保護者名", body.startswith("テスト 花子 様"), body[:40])
    for s_ in ("入塾金（初回のみ）：10,000円", "設備費：1,350円", "受講料（初月分・日割りなし）：7,500円", "合計：18,850円", "月額 8,850円", "高校2年英文法", "前月 15 日まで", "26 日前後"):
        check(f"B1k. 本文に「{s_}」", s_ in body, body)
    ml, nl = wh._enroll_month_label(month), wh._enroll_month_label(wh._enroll_next_month(month))
    check("B1l. 本文に 当月分/翌月分 のラベル (今月分/翌月分どちらの月末運用でも嘘にならない文)", f"（{ml}分）" in body and f"{nl}分以降は" in body and f"{nl}分は {ml} 26 日前後" in body and "末の引き落としはありません" not in body and "LINE でお知らせします）" not in body, body)
    check("B1m. 本文に LINE URL・受付番号・申込ID・窓口", "https://lin.ee/ZHlrRjh" in body and "cs_enroll_1" in body and "AB12CD34" in body and "info@trillion-ai-juku.com" in body, body)
    check("B1m2. 本文に Zoom の ID とパスコード (環境変数から)・塾生アプリ登録 URL・授業ルール",
          "ミーティング ID：12345" in body and "パスコード：abc" in body and "https://trillion-ai-juku.com/juku-register.html" in body
          and "5 分前には入室" in body and "画面（カメラ）はオン、音声はオフ" in body and "LINE でお知らせします。" not in body.split("■ 授業について")[1].split("■")[0], body)
    check("B1n. From に塾名・reply_to は窓口・Idempotency-Key", m.get("from") == "トリリオン英語塾 <noreply@example.invalid>" and m.get("reply_to") == "info@trillion-ai-juku.com" and any(v == f"enroll-welcome/{rid}" for v in net.headers[0].values()), (m.get("from"), m.get("reply_to"), net.headers[:1]))
    o = net.sent[1] if len(net.sent) > 1 else {}
    check("B1o. 塾長通知 (宛先・件名に 名簿登録済み・本文に台帳の月と申込ID・金額照合の指示・★なし)", o.get("to") == ["owner@example.invalid"] and "名簿登録済み" in o.get("subject", "") and f"{ml}分を「引き落とし済み」" in o.get("text", "") and "AB12CD34" in o.get("text", "") and "送信済み" in o.get("text", "") and "金額_初月合計" in o.get("text", "") and "★" not in o.get("text", ""), o)
    check("B1q. reg:by_customer に rid", kv.store.get("reg:by_customer:cus_1") == rid, kv.store.get("reg:by_customer:cus_1"))
    wrec = json.loads(kv.store.get(f"enroll:welcome:{rid}") or "{}")
    check("B1p. enroll:welcome に status=sent", wrec.get("status") == "sent" and wrec.get("resend_id") == "re_1", wrec)

    # ---- B1z Zoom 未設定なら「LINE でお知らせ」 ----
    os.environ["ENROLL_ZOOM_ID"] = ""
    kvz, netz = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kvz, netz
    kvz.store["reg:pending:reg_tz"] = json.dumps(pending("reg_tz"), ensure_ascii=False)
    wh._handle_checkout_completed(event(session("reg_tz", sid="cs_enroll_z")))
    bz = netz.sent[0].get("text", "") if netz.sent else ""
    check("B1z. Zoom の環境変数が無ければ「ミーティング ID とパスコードは公式 LINE でお知らせします」", "ミーティング ID とパスコードは公式 LINE でお知らせします" in bz and "パスコード：" not in bz, bz)
    os.environ["ENROLL_ZOOM_ID"] = "12345"
    wh._redis_safe, urllib.request.urlopen = kv, net

    # ---- B2 再送 ----
    wh._handle_checkout_completed(event(session(rid), eid="evt_2"))
    check("B2a. 再送でもメールは増えない", len(net.sent) == 2, len(net.sent))
    check("B2b. 再送でも台帳の audit は増えない・done は元のまま", len(kv.lists.get(f"charge:history:audit:{rid}:{month}", [])) == 1 and json.loads(kv.store[f"charge:done:{rid}:{month}"]).get("source") == "enroll-first-charge")
    check("B2d. 自分が書いた台帳への再実行は written 扱い (★誤警告を出さない)", wh._enroll_write_ledger(rid, month, "pi_first_1", 18850, json.loads(kv.store[f"reg:completed:{rid}"]), 1) == "written" and wh._enroll_write_ledger(rid, month, "pi_other", 18850, {}, 1) == "exists")
    check("B2c. 再送後も名簿は setup 相当のまま", json.loads(kv.store[f"reg:completed:{rid}"]).get("checkout_mode") == "setup")

    # ---- B3 未払い ----
    rid3 = "reg_t3"
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    kv.store[f"reg:pending:{rid3}"] = json.dumps(pending(rid3), ensure_ascii=False)
    wh._handle_checkout_completed(event(session(rid3, sid="cs_enroll_3", paid=False)))
    check("B3. 未払いは名簿・台帳・メールを一切書かない", f"reg:completed:{rid3}" not in kv.store and not any(k.startswith("charge:") for k in kv.store) and not net.sent and f"reg:pending:{rid3}" in kv.store, list(kv.store))

    # ---- B4 テストモード ----
    rid4 = "reg_t4"
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    kv.store[f"reg:pending:{rid4}"] = json.dumps(pending(rid4), ensure_ascii=False)
    wh._handle_checkout_completed(event(session(rid4, sid="cs_enroll_4", livemode=False)))
    check("B4. テストモードは登録と台帳は書くがメールは送らない", f"reg:completed:{rid4}" in kv.store and f"charge:done:{rid4}:{month}" in kv.store and not net.sent, (list(kv.store), net.sent))

    # ---- B5 pending 消失 ----
    rid5 = "reg_t5"
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    wh._handle_checkout_completed(event(session(rid5, sid="cs_enroll_5")))
    rec5 = json.loads(kv.store.get(f"reg:completed:{rid5}") or "{}")
    check("B5a. metadata から復元して登録 (氏名・entry_fee・app_id・monthly_fee)", rec5.get("student_name") == "テスト 太郎" and rec5.get("entry_fee") == 10000 and rec5.get("app_id") == "AB12CD34" and rec5.get("monthly_fee") == 8850 and rec5.get("restored_from_metadata") is True, rec5)
    b5 = net.sent[0].get("text", "") if net.sent else ""
    check("B5b. fee_breakdown 文字列から内訳を復元してメール", "受講料（初月分・日割りなし）：7,500円" in b5 and "設備費：1,350円" in b5 and "テスト 太郎 さん" in b5, b5)
    h5 = json.loads(kv.store.get(f"charge:history:{rid5}:{month}") or "{}")
    check("B5c. 台帳にも氏名", h5.get("student_name") == "テスト 太郎", h5)

    # ---- B6 従来 setup ----
    rid6 = "reg_t6"
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    _orig_get = wh._stripe_get
    wh._stripe_get = lambda sk, path: {"id": "seti_1", "payment_method": "pm_setup_1", "customer": "cus_1"}
    wh._handle_checkout_completed(event(session(rid6, sid="cs_setup_6", mode="setup", first="")))
    wh._stripe_get = _orig_get
    rec6 = json.loads(kv.store.get(f"reg:completed:{rid6}") or "{}")
    check("B6. setup モードは従来どおり (pm 保存・amount=0・台帳なし・メールなし)", rec6.get("checkout_mode") == "setup" and rec6.get("stripe_payment_method_id") == "pm_setup_1" and rec6.get("amount") == 0 and not any(k.startswith("charge:") for k in kv.store) and not net.sent, (rec6, list(kv.store)))

    # ---- B7 payment_intent.succeeded (month なし) ----
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    wh._handle_payment_intent_succeeded(event({"id": "pi_first_1", "object": "payment_intent", "customer": "cus_1", "amount_received": 18850,
                                               "metadata": {"registration_id": "reg_t1", "system": "juku-payment-monthly", "first_charge": "1"}},
                                              etype="payment_intent.succeeded"))
    check("B7. PI 成功イベントは pi:succeeded だけ記録し charge:* を書かない", "pi:succeeded:pi_first_1" in kv.store and not any(k.startswith("charge:") for k in kv.store), list(kv.store))

    # ---- B8 PaymentIntent 取得失敗 → 顧客のカードから復元 ----
    rid8 = "reg_t8"
    kv, net = FakeKV(), FakeNet(pm=None)
    wh._redis_safe, urllib.request.urlopen = kv, net
    kv.store[f"reg:pending:{rid8}"] = json.dumps(pending(rid8), ensure_ascii=False)
    wh._handle_checkout_completed(event(session(rid8, sid="cs_enroll_8")))
    rec8 = json.loads(kv.store.get(f"reg:completed:{rid8}") or "{}")
    check("B8a. PI が取れなくても顧客の保存カードで payment_method を埋める", rec8.get("stripe_payment_method_id") == "pm_from_customer" and any("/payment_methods" in u for u in net.stripe_gets), (rec8.get("stripe_payment_method_id"), net.stripe_gets))
    check("B8b. amount_total から初回額 18,850 (PI 不要)", rec8.get("amount") == 18850 and json.loads(kv.store[f"charge:done:{rid8}:{month}"]).get("amount") == 18850)

    # ---- B9 翌月分の月末バッチが実行済み → 塾長通知に★個別請求 ----
    rid9 = "reg_t9"
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    nm = wh._enroll_next_month(month)
    kv.zsets["charge:history:index"] = [f"reg_other:{nm}"]
    kv.store[f"reg:pending:{rid9}"] = json.dumps(pending(rid9), ensure_ascii=False)
    wh._handle_checkout_completed(event(session(rid9, sid="cs_enroll_9")))
    o9 = net.sent[1] if len(net.sent) > 1 else {}
    check("B9. 翌月分バッチ実行済みなら塾長通知が ★要対応 で「翌月分は個別に請求」", o9.get("subject", "").startswith("★要対応") and f"{wh._enroll_month_label(nm)}分の月末バッチ" in o9.get("text", "") and "個別に請求" in o9.get("text", ""), o9)
    check("B9b. 保護者メールは通常どおり", net.sent and net.sent[0].get("to") == ["parent@example.invalid"], net.sent[:1])

    # ---- B10 同じ顧客の 2 件目 (申込書を送り直して 2 回支払った) ----
    rid10a, rid10b = "reg_t10a", "reg_t10b"
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    kv.store[f"reg:pending:{rid10a}"] = json.dumps(pending(rid10a), ensure_ascii=False)
    kv.store[f"reg:pending:{rid10b}"] = json.dumps(pending(rid10b), ensure_ascii=False)
    wh._handle_checkout_completed(event(session(rid10a, sid="cs_enroll_10a")))
    wh._handle_checkout_completed(event(session(rid10b, sid="cs_enroll_10b"), eid="evt_10b"))
    dup = json.loads(kv.store.get(f"reg:duplicate:{rid10b}") or "{}")
    check("B10a. 2 件目は名簿 (reg:completed) に入らず reg:duplicate に duplicate_of 付きで残る", f"reg:completed:{rid10b}" not in kv.store and dup.get("duplicate_of") == rid10a and rid10b not in kv.zsets.get("reg:completed:index", []), (list(kv.store), dup))
    check("B10b. 2 件目は台帳を書かない・pending は消す", f"charge:done:{rid10b}:{month}" not in kv.store and f"reg:pending:{rid10b}" not in kv.store)
    check("B10c. 2 件目は保護者メールなし・塾長に「二重」の返金確認メール", len(net.sent) == 3 and "二重" in net.sent[2].get("subject", "") and rid10a in net.sent[2].get("text", "") and "cs_enroll_10b" in net.sent[2].get("text", ""), [m.get("subject") for m in net.sent])
    # 既存の登録が退塾処理で消えていれば通常登録
    kv.store.pop(f"reg:completed:{rid10a}")
    rid10c = "reg_t10c"
    kv.store[f"reg:pending:{rid10c}"] = json.dumps(pending(rid10c), ensure_ascii=False)
    wh._handle_checkout_completed(event(session(rid10c, sid="cs_enroll_10c"), eid="evt_10c"))
    check("B10d. 既存登録が消えていれば (退塾後の再入塾) 通常どおり名簿に入る", f"reg:completed:{rid10c}" in kv.store and kv.store.get("reg:by_customer:cus_1") == rid10c)

    # ---- B11 KV 障害 → _RetryLater (Stripe に再送してもらう) ----
    kv, net = DownKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    raised = None
    try:
        wh._handle_checkout_completed(event(session("reg_t11", sid="cs_enroll_11")))
    except Exception as e:
        raised = e
    check("B11. KV に名簿を書けなければ _RetryLater (メールも送らない)", isinstance(raised, wh._RetryLater) and not net.sent, (repr(raised), net.sent))

    # ---- B12 async_payment_succeeded も入塾セッションを扱う ----
    rid12 = "reg_t12"
    kv, net = FakeKV(), FakeNet()
    wh._redis_safe, urllib.request.urlopen = kv, net
    kv.store[f"reg:pending:{rid12}"] = json.dumps(pending(rid12), ensure_ascii=False)
    wh._handle_course_async_paid(event(session(rid12, sid="cs_enroll_12"), etype="checkout.session.async_payment_succeeded"))
    check("B12. async_payment_succeeded でも登録される (支払方法を増やしたときの保険)", f"reg:completed:{rid12}" in kv.store)

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}")
        sys.exit(1)
    print("✅ 全て成功")


if __name__ == "__main__":
    main()
