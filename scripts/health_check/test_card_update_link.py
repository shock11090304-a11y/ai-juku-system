#!/usr/bin/env python3
"""🪪 月謝のカード変更リンク (2026-10-20) の回帰テスト (ネットワークなし・KV / Stripe / Resend は偽物)。

対象:
  api/admin-card-update.py   塾長が「🪪 カード変更」でリンク (Checkout mode=setup・その登録の Stripe 顧客) を作る / 状態を聞く
  api/stripe-webhook.py      その完了 → 同じ reg:completed:{rid} の stripe_payment_method_id だけを差し替える
  api/admin-registration-cancel.py  月額の保存 (update_fee) も「読んだときのままなら書く」・退塾処理でリンクと前のカードを片付ける
  api/admin-charge-reconcile.py     回収済みの月の「未課金にする」「再請求」を止める (📜 失敗の行の 🔁 から二重取りしていた)
  api/registered-customers.py / api/admin-charge-readonly.py  画面の「🪪 VISA 末尾 4242（10/20 に変更）」・失敗の行の「回収済み」

なぜ: 月末一斉・個別・再請求は KV のカード (stripe_payment_method_id) を名指しで使うので、Stripe の画面でカードを替えても
効かない。それまでの回り道 (退塾処理→再登録→紐付け直し) は rid が変わり、rid 単位の台帳 (charge:done / history) が
引き継がれずに二重取りの穴になった。ここで守るのは「rid・月額・台帳・名簿の紐付けを変えずにカードだけ替わる」こと。

  A. リンク作成 API: 認証 / 断る登録 / Checkout の中身 (system=juku-payment-card-update + card_update_rid・★registration_id なし) /
     前のリンクを失効 / 作れなかったら前のリンクは生きたまま / 登録・台帳には書かない / status (いまのカード・送ったリンク)
  B. webhook: 差し替え・前のカードを外す・メール / 再送・取りこぼした後始末 / 登録が無い・顧客が違う・古いリンク /
     処理中・3DS 待ちは前のカードを外さない / 読んでから書くまでに他が書いた・消えた (CAS) / _RetryLater / 申込の再送で上書きしない
  C. 配線 (Railway は skip・rewrite・画面・完了ページ)
  D. 月額の保存 (update_fee) の CAS・退塾処理の後始末
  E. 回収済みの月の mark_unpaid / retry を止める
  F. 📜 失敗の行の「その後に回収済み」
"""
import importlib.util
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(REPO, "api")
FAILURES = []
# 架空のテスト値 (個人情報ゲートは「studentName: "氏名"」の直書きを止めるので変数で渡す)
TARO = "テスト 太郎"
HANAKO = "テスト 花子"
PW = "test-admin-pw"
CU_TAG = "juku-payment-card-update"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load(name, alias):
    spec = importlib.util.spec_from_file_location(alias, os.path.join(API, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


class FakeKV:
    """Upstash REST の最小限の真似。writes に書き込みの (命令, キー) を残す。
    EVAL は「読んだときのままなら書く」スクリプト (_KV_CAS_SCRIPT) だけを解釈する。before_eval で「読んでから書くまでの間の他の書き込み」を起こせる"""
    def __init__(self):
        self.store, self.zsets, self.lists, self.writes = {}, {}, {}, []
        self.before_eval = None   # 読んでから書くまでの間の他の書き込み
        self.after_eval = None    # 書いた直後 (確認の読み直しの前) の他の書き込み
        self.eval_supported = True

    def eval_api(self, *args):
        """_kv_eval の差し替え: (state, reply)。EVAL を断る KV は Upstash と同じく 4xx = rejected"""
        if args[0] != "EVAL":
            return "ok", self(*args)
        if not self.eval_supported:
            return "rejected", None
        return "ok", self(*args)

    def __call__(self, *args):
        cmd = args[0]
        if cmd == "EVAL":
            assert "redis.call('GET', KEYS[1])" in args[1] and args[2] == "1", args[:3]
            key, expected, new = args[3], args[4], args[5]
            if self.before_eval:
                hook, self.before_eval = self.before_eval, None
                hook(self)
            cur = self.store.get(key)
            if cur is None:
                return {"result": -1}
            if cur != expected:
                return {"result": 0}
            self.store[key] = new
            self.writes.append(("SET", key))
            if self.after_eval:
                hook, self.after_eval = self.after_eval, None
                hook(self)
            return {"result": 1}
        if cmd == "SET":
            key, val = args[1], args[2]
            if "NX" in args[3:] and key in self.store:
                return {"result": None}
            self.store[key] = val
            self.writes.append(("SET", key))
            return {"result": "OK"}
        if cmd == "GET":
            return {"result": self.store.get(args[1])}
        if cmd == "DEL":
            self.writes.append(("DEL", args[1]))
            return {"result": 1 if self.store.pop(args[1], None) is not None else 0}
        if cmd == "ZADD":
            opts = [a for a in args[2:-2] if a in ("NX", "XX", "GT", "LT", "CH")]
            member = args[-1]
            z = self.zsets.setdefault(args[1], [])
            if member not in z and "XX" not in opts:
                z.append(member)
            self.writes.append(("ZADD", args[1]) if not opts else ("ZADD " + " ".join(opts), args[1]))
            return {"result": 1}
        if cmd == "ZREM":
            z = self.zsets.setdefault(args[1], [])
            if args[2] in z:
                z.remove(args[2])
            self.writes.append(("ZREM", args[1]))
            return {"result": 1}
        if cmd == "ZSCORE":
            return {"result": "1780000000" if args[2] in self.zsets.get(args[1], []) else None}
        if cmd == "ZRANGE":
            return {"result": list(reversed(self.zsets.get(args[1], [])))}
        if cmd == "RPUSH":
            self.lists.setdefault(args[1], []).append(args[2])
            return {"result": len(self.lists[args[1]])}
        if cmd == "MGET":
            return {"result": [self.store.get(k) for k in args[1:]]}
        if cmd in ("INCR", "EXPIRE"):
            return {"result": 1}
        return {"result": None}


class DownKV(FakeKV):
    def __call__(self, *args):
        return None

    def eval_api(self, *args):
        return "down", None


class SetFailKV(FakeKV):
    """読めるが reg:completed への書き込み (EVAL / SET) だけ応答が無い"""
    def __call__(self, *args):
        if args[0] == "EVAL" or (args[0] == "SET" and str(args[1]).startswith("reg:completed:")):
            return None
        return super().__call__(*args)

    def eval_api(self, *args):
        return "down", None


def card(pm_id, customer, brand, last4, mm, yy):
    return {"id": pm_id, "object": "payment_method", "customer": customer,
            "card": {"brand": brand, "last4": last4, "exp_month": mm, "exp_year": yy}}


class FakeNet:
    """urllib.request.urlopen の差し替え: Stripe (SetupIntent / PaymentMethod / detach / PaymentIntent 一覧) と Resend だけ受ける"""
    def __init__(self, si_status="succeeded", si_pm="pm_new", si_customer="cus_1", si_fail=False, detach_fail=None, resend_fail=False, pis=None, pis_fail=False):
        self.calls, self.sent, self.headers, self.detached = [], [], [], []
        self.si_status, self.si_pm, self.si_customer, self.si_fail = si_status, si_pm, si_customer, si_fail
        self.detach_fail, self.resend_fail = detach_fail, resend_fail
        self.pis, self.pis_fail = list(pis or []), pis_fail
        self.pms = {"pm_new": card("pm_new", "cus_1", "visa", "4242", 8, 2030),
                    "pm_new2": card("pm_new2", "cus_1", "jcb", "0005", 3, 2031),
                    "pm_old": card("pm_old", "cus_1", "mastercard", "4444", 1, 2027)}

    def __call__(self, req, timeout=None):
        url, method = req.full_url, req.get_method()
        self.calls.append((method, url))
        if url.startswith("https://api.stripe.com/v1/setup_intents/"):
            if self.si_fail:
                raise urllib.error.HTTPError(url, 500, "boom", {}, io.BytesIO(b"{}"))
            return io.BytesIO(json.dumps({"id": url.rsplit("/", 1)[1], "object": "setup_intent", "status": self.si_status,
                                          "payment_method": self.si_pm, "customer": self.si_customer}).encode())
        if url.startswith("https://api.stripe.com/v1/payment_intents?"):
            if self.pis_fail:
                raise urllib.error.HTTPError(url, 500, "boom", {}, io.BytesIO(b"{}"))
            return io.BytesIO(json.dumps({"object": "list", "data": self.pis}).encode())
        if url.startswith("https://api.stripe.com/v1/payment_methods/") and url.endswith("/detach"):
            pm = url.split("/v1/payment_methods/")[1].split("/")[0]
            if self.detach_fail:
                raise urllib.error.HTTPError(url, 400, "bad", {}, io.BytesIO(self.detach_fail))
            self.detached.append(pm)
            if pm in self.pms:
                self.pms[pm]["customer"] = None
            return io.BytesIO(json.dumps({"id": pm, "customer": None}).encode())
        if url.startswith("https://api.stripe.com/v1/payment_methods/"):
            pm = url.rsplit("/", 1)[1]
            if pm not in self.pms:
                raise urllib.error.HTTPError(url, 404, "nf", {}, io.BytesIO(b'{"error":{"code":"resource_missing"}}'))
            return io.BytesIO(json.dumps(self.pms[pm]).encode())
        if "api.resend.com" in url:
            if self.resend_fail:
                raise urllib.error.HTTPError(url, 500, "boom", {}, io.BytesIO(b"{}"))
            self.headers.append(dict(req.header_items()))
            self.sent.append(json.loads(req.data.decode("utf-8")))
            return io.BytesIO(json.dumps({"id": f"re_{len(self.sent)}"}).encode())
        raise AssertionError("unexpected network call: " + url)


def reg_record(rid, customer="cus_1", pm="pm_old", **kw):
    r = {"registration_id": rid, "session_id": "cs_orig", "stripe_customer_id": customer, "stripe_subscription_id": "",
         "stripe_payment_method_id": pm, "stripe_setup_intent_id": "", "checkout_mode": "setup", "status": "completed",
         "completed_at": 1780000000, "amount": 18850, "monthly_fee": 8850, "email": "parent@example.invalid",
         "system": "juku-payment-monthly", "studentName": TARO, "grade": "高校2年", "parentName": HANAKO,
         "first_charge": True, "first_charge_month": "2026-09", "start_month": "2026-09",
         "fee_breakdown": "高2 英文法 ¥7,500 / 設備費 (¥1,350) ¥1,350", "source": "enrollment-form-v1-payment"}
    r.update(kw)
    return r


def cu_session(rid, sid="cs_cu_1", customer="cus_1", seti="seti_cu_1", livemode=True, created=1790000000, system=CU_TAG, md_extra=None):
    md = {"system": system, "purpose": "card_update", "card_update_rid": rid, "student_name": TARO, "source": "admin-card-update"}
    if system is None:
        md.pop("system")
    md.update(md_extra or {})
    return {"id": sid, "object": "checkout.session", "mode": "setup", "status": "complete", "livemode": livemode,
            "payment_status": "no_payment_required", "customer": customer, "setup_intent": seti, "created": created,
            "amount_total": None, "metadata": md}


def event(obj, eid="evt_cu_1"):
    return {"id": eid, "type": "checkout.session.completed", "data": {"object": obj}}


def seeded_kv(rid, **kw):
    kv = FakeKV()
    kv.store[f"reg:completed:{rid}"] = json.dumps(reg_record(rid, **kw), ensure_ascii=False)
    kv.zsets["reg:completed:index"] = [rid]
    kv.store[f"charge:done:{rid}:2026-10"] = json.dumps({"status": "succeeded", "payment_intent_id": "pi_oct"})
    kv.store[f"charge:history:{rid}:2026-10"] = json.dumps({"status": "succeeded", "amount": 8850})
    return kv


class FakeReq:
    def __init__(self, mod, body, pw=PW, path="/api/x"):
        raw = json.dumps(body, ensure_ascii=False).encode() if not isinstance(body, bytes) else body
        self.headers = {"Content-Length": str(len(raw)), "x-real-ip": "203.0.113.7"}
        if pw is not None:
            self.headers["X-Admin-Password"] = pw
        self.rfile, self.wfile = io.BytesIO(raw), io.BytesIO()
        self.status, self.hdrs, self._mod, self.path = None, {}, mod, path

    def send_response(self, code): self.status = code
    def send_header(self, k, v): self.hdrs[k] = v
    def end_headers(self): pass

    def run(self):
        self._mod.handler.do_POST(self)
        return self.status, json.loads(self.wfile.getvalue().decode() or "{}")

    def run_get(self):
        self._mod.handler.do_GET(self)
        return self.status, json.loads(self.wfile.getvalue().decode() or "{}")


# ───────────────────────── A. リンク作成 API ─────────────────────────
def test_admin_api():
    print("[A] リンク作成 API (api/admin-card-update.py)")
    os.environ.update({"CHAT_ADMIN_PASSWORD": PW, "STRIPE_SECRET_KEY": "sk_test_dummy", "KV_REST_API_URL": "", "KV_REST_API_TOKEN": "",
                       "PUBLIC_BASE_URL": ""})
    mod = load("admin-card-update", "vercel_admin_card_update")
    mod._admin_kv = lambda *a: None   # 総当たり対策のカウンタは test_vercel_admin_guard.py が見る
    posts = []
    state = {"fail_create": None, "fail_expire": None, "n": 0}

    def fake_post(secret_key, path, form, idempotency_key=None):
        posts.append((path, list(form)))
        if path == "checkout/sessions":
            if state["fail_create"]:
                raise urllib.error.HTTPError("https://api.stripe.com/v1/checkout/sessions", 400, "bad", {}, io.BytesIO(state["fail_create"]))
            state["n"] += 1
            return {"id": f"cs_link_{state['n']}", "url": f"https://checkout.stripe.com/c/pay/cs_link_{state['n']}", "expires_at": int(time.time()) + 86400}
        if path.endswith("/expire"):
            if state["fail_expire"]:
                raise urllib.error.HTTPError("https://api.stripe.com/v1/" + path, 400, "bad", {}, io.BytesIO(b'{"error":{"message":"already complete"}}'))
            return {"id": path.split("/")[1], "status": "expired"}
        raise AssertionError("unexpected Stripe POST " + path)
    mod._stripe_post = fake_post
    rid = "reg_cu_a"

    kv = seeded_kv(rid)
    mod._redis = kv
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid}, pw=None).run()
    check("A1a. パスワード無しは 401 (Stripe も呼ばない)", st == 401 and not posts, (st, body, posts))
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid}, pw="wrong").run()
    check("A1b. 間違ったパスワードは 401 (入れ直しの案内つき)", st == 401 and "入れ直して" in body.get("message", ""), (st, body))
    st, body = FakeReq(mod, {"action": "cancel", "registrationId": rid}).run()
    check("A1c. action は create_link / status だけ (退塾などの別操作に落ちない)", st == 400 and body.get("error") == "UNKNOWN_ACTION", (st, body))
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": "reg bad'"}).run()
    check("A1d. 登録 ID の形が不正なら 400", st == 400 and body.get("error") == "MISSING_REG_ID", (st, body))
    st, body = FakeReq(mod, b"not json").run()
    check("A1e. 壊れた本文は 400 (日本語の案内つき)", st == 400 and body.get("error") == "INVALID_JSON" and body.get("message"), (st, body))

    st, body = FakeReq(mod, {"action": "create_link", "registrationId": "reg_nothing"}).run()
    check("A2a. 登録が無ければ 404 (日本語の案内)", st == 404 and "カード登録が見つかりません" in body.get("message", ""), (st, body))
    kv.store["reg:completed:reg_sub"] = json.dumps(reg_record("reg_sub", checkout_mode="subscription"), ensure_ascii=False)
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": "reg_sub"}).run()
    check("A2b. 旧方式 (subscription) は 409 NOT_SETUP_MODE", st == 409 and body.get("error") == "NOT_SETUP_MODE", (st, body))
    kv.store["reg:completed:reg_nocus"] = json.dumps(reg_record("reg_nocus", customer=""), ensure_ascii=False)
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": "reg_nocus"}).run()
    check("A2c. Stripe 顧客の無い登録は 409 NO_CUSTOMER (やり直しの手順つき)", st == 409 and body.get("error") == "NO_CUSTOMER"
          and "register.html" in body.get("message", "") and "✓確定" in body.get("message", ""), (st, body))
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid, "expectCustomerId": "cus_other"}).run()
    check("A2d. 名簿の紐付けの顧客と違えば 409 CUSTOMER_MISMATCH", st == 409 and body.get("error") == "CUSTOMER_MISMATCH", (st, body))
    kv.store["reg:completed:reg_zombie"] = json.dumps(reg_record("reg_zombie"), ensure_ascii=False)
    kv.store["reg:zombie:reg_zombie"] = json.dumps({"reason": "Stripe customer/PM not found"})
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": "reg_zombie"}).run()
    check("A2e. 一覧から外れた登録 (reg:zombie) は 409", st == 409 and body.get("error") == "ZOMBIE_REGISTRATION", (st, body))
    check("A2f. 断った場合は Stripe を一度も呼んでいない", not posts, posts)
    mod._redis = DownKV()
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid}).run()
    check("A2g. KV が応答しなければ 503 (作らない)", st == 503 and not posts, (st, body))
    mod._redis = kv

    st, body = FakeReq(mod, {"action": "status", "registrationId": rid}).run()
    check("A6a. status: まだ何も無ければ card / link とも null", st == 200 and body.get("ok") and body.get("card") is None and body.get("link") is None
          and body.get("studentName") == TARO, (st, body))
    before = dict(kv.store)
    kv.writes.clear()
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid, "expectCustomerId": "cus_1"}).run()
    check("A3a. 作成できたら 200・URL・期限・生徒名", st == 200 and body.get("ok") and body.get("url", "").startswith("https://checkout.stripe.com/")
          and body.get("expiresAt", 0) > time.time() and body.get("studentName") == TARO and body.get("expiredPrevious") is False, (st, body))
    cs = [p for p in posts if p[0] == "checkout/sessions"]
    form = dict(cs[0][1]) if cs else {}
    keys = [k for k, _ in (cs[0][1] if cs else [])]
    check("A3b. Checkout は mode=setup・カード・その登録の顧客・日本語", form.get("mode") == "setup" and form.get("payment_method_types[]") == "card"
          and form.get("customer") == "cus_1" and form.get("locale") == "ja", form)
    check("A3c. 戻り先は payment/card-update-complete.html (中断は ?canceled=1・apex)",
          form.get("success_url") == "https://trillion-ai-juku.com/payment/card-update-complete.html"
          and form.get("cancel_url") == "https://trillion-ai-juku.com/payment/card-update-complete.html?canceled=1", (form.get("success_url"), form.get("cancel_url")))
    check("A3d. metadata: system=juku-payment-card-update・card_update_rid (Session と SetupIntent の両方)",
          form.get("metadata[system]") == CU_TAG and form.get("metadata[card_update_rid]") == rid
          and form.get("setup_intent_data[metadata][system]") == CU_TAG and form.get("setup_intent_data[metadata][card_update_rid]") == rid, form)
    check("A3e. ★registration_id は付けない (従来の webhook が新規登録と取り違えて上書きするため)",
          not any("registration_id" in k for k in keys), [k for k in keys if "registration" in k])
    msg = form.get("custom_text[submit][message]", "")
    check("A3f. 決済画面の確認文: 生徒名・「入力しただけでは料金はかかりません」(★「本日の課金はありません」とは言わない)",
          f"{TARO}さんの" in msg and "入力しただけでは料金はかかりません" in msg and "本日の課金" not in msg, msg)
    link = json.loads(kv.store.get(f"card_update:link:{rid}") or "{}")
    check("A3g. KV card_update:link:{rid} に最新のリンク (session_id・url・期限)", link.get("session_id") == "cs_link_1"
          and link.get("url") == "https://checkout.stripe.com/c/pay/cs_link_1" and link.get("expires_at", 0) > time.time(), link)
    check("A3h. ★登録・台帳・index には一切書かない (書いたのは card_update:link だけ)",
          kv.writes == [("SET", f"card_update:link:{rid}")] and all(kv.store.get(k) == v for k, v in before.items()), kv.writes)
    st, body = FakeReq(mod, {"action": "status", "registrationId": rid}).run()
    check("A6b. status: 送ったリンクがまだ使えるなら、その URL と期限 (作り直さずにもう一度送れる)", st == 200
          and (body.get("link") or {}).get("url") == "https://checkout.stripe.com/c/pay/cs_link_1", (st, body))
    os.environ["STRIPE_SECRET_KEY"] = ""
    st, body = FakeReq(mod, {"action": "status", "registrationId": rid}).run()
    check("A6c. status は Stripe を使わない (キー未設定でも答える)", st == 200 and body.get("ok"), (st, body))
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy"
    rec_c = json.loads(kv.store[f"reg:completed:{rid}"])
    rec_c.update(card_brand="VISA", card_last4="4242", card_exp="08/30", card_updated_at=1790000000)
    kv.store[f"reg:completed:{rid}"] = json.dumps(rec_c, ensure_ascii=False)
    st, body = FakeReq(mod, {"action": "status", "registrationId": rid}).run()
    check("A6d. status: カード変更で差し替えたカードの種類・末尾・日時", st == 200 and body.get("card") == {"brand": "VISA", "last4": "4242", "exp": "08/30", "updatedAt": 1790000000}, body)
    lk = json.loads(kv.store[f"card_update:link:{rid}"])
    lk["expires_at"] = int(time.time()) - 10
    kv.store[f"card_update:link:{rid}"] = json.dumps(lk)
    st, body = FakeReq(mod, {"action": "status", "registrationId": rid}).run()
    check("A6e. status: 期限の切れたリンクは出さない", st == 200 and body.get("link") is None, body)
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid}).run()
    check("A4z. 期限の切れたリンクは失効させに行かない", st == 200 and not [p for p in posts if p[0].endswith("/expire")], [p[0] for p in posts])

    n_cs = len([p for p in posts if p[0] == "checkout/sessions"])
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid}).run()
    check("A8. まだ使えるリンクがあるのに replace 無しで作ろうとすると 409 LINK_ACTIVE (今のリンクを返し、作らない・失効させない)", st == 409
          and body.get("error") == "LINK_ACTIVE" and (body.get("link") or {}).get("url") == "https://checkout.stripe.com/c/pay/cs_link_2"
          and len([p for p in posts if p[0] == "checkout/sessions"]) == n_cs and not [p for p in posts if p[0].endswith("/expire")], (st, body))
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid, "replace": True}).run()
    expires = [p[0] for p in posts if p[0].endswith("/expire")]
    order = [p[0] for p in posts]
    check("A4a. 作り直す (replace: true) と前のリンク (cs_link_2) を失効させ、expiredPrevious=true", st == 200 and expires == ["checkout/sessions/cs_link_2/expire"]
          and body.get("expiredPrevious") is True, (st, body, expires))
    check("A4b. 失効は新しいリンクを作れてから (作成 → 失効の順)", order[-2:] == ["checkout/sessions", "checkout/sessions/cs_link_2/expire"], order[-3:])
    check("A4c. 最新のリンクが記録される (cs_link_3)", json.loads(kv.store[f"card_update:link:{rid}"]).get("session_id") == "cs_link_3")
    state["fail_expire"] = True
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid, "replace": True}).run()
    check("A4d. 前のリンクが既に完了・失効でも (Stripe 400) 新しいリンクは作れる", st == 200 and body.get("expiredPrevious") is False and body.get("sessionId") == "cs_link_4", (st, body))
    state["fail_expire"] = None
    n_expire = len([p for p in posts if p[0].endswith("/expire")])
    state["fail_create"] = b'{"error":{"code":"resource_missing","message":"No such customer: cus_1"}}'
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid, "replace": True}).run()
    check("A5a. 顧客が Stripe に無ければ 502 CUSTOMER_MISSING (登録し直しの案内)", st == 502 and body.get("error") == "CUSTOMER_MISSING", (st, body))
    check("A5b. 作れなかったときは前のリンクを失効させない (前のリンクが生きたまま)",
          len([p for p in posts if p[0].endswith("/expire")]) == n_expire and json.loads(kv.store[f"card_update:link:{rid}"]).get("session_id") == "cs_link_4")
    state["fail_create"] = b'{"error":{"message":"Invalid request"}}'
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid, "replace": True}).run()
    check("A5c. ほかの Stripe エラーは 502 STRIPE_ERROR", st == 502 and body.get("error") == "STRIPE_ERROR", (st, body))
    state["fail_create"] = None
    os.environ["STRIPE_SECRET_KEY"] = ""
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid}).run()
    check("A5d. STRIPE_SECRET_KEY 未設定は 503", st == 503 and body.get("error") == "STRIPE_NOT_CONFIGURED", (st, body))
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy"

    class LinkReadFailKV(FakeKV):
        def __call__(self, *args):
            if args[0] == "GET" and str(args[1]).startswith("card_update:link:"):
                return None
            return super().__call__(*args)
    kv7 = LinkReadFailKV()
    kv7.store.update(seeded_kv(rid).store)
    mod._redis = kv7
    n_posts = len(posts)
    st, body = FakeReq(mod, {"action": "create_link", "registrationId": rid}).run()
    check("A7. 前のリンクの記録を読めなければ作らない (503・2 本同時に使える状態を作らない)", st == 503 and len(posts) == n_posts, (st, body))


# ───────────────────────── B. webhook ─────────────────────────
def run_wh(wh, kv, net, obj, eid="evt_cu_1"):
    wh._redis_safe, urllib.request.urlopen = kv, net
    wh._kv_eval = kv.eval_api
    raised = None
    try:
        wh._handle_checkout_completed(event(obj, eid=eid))
    except Exception as e:
        raised = e
    return raised


def rec_of(kv, rid):
    return json.loads(kv.store.get(f"reg:completed:{rid}") or "{}")


def owner_mails(net):
    return [m for m in net.sent if m.get("to") == ["owner@example.invalid"]]


def parent_mails(net):
    return [m for m in net.sent if m.get("to") == ["parent@example.invalid"]]


def test_webhook():
    print("\n[B] webhook (api/stripe-webhook.py _handle_card_update_checkout)")
    os.environ.update({"STRIPE_SECRET_KEY": "sk_test_dummy", "KV_REST_API_URL": "", "KV_REST_API_TOKEN": "",
                       "RESEND_API_KEY": "re_dummy", "FROM_EMAIL": "noreply@example.invalid", "COURSE_REPLY_TO": "",
                       "ENROLL_NOTIFY_EMAIL": "", "COURSE_NOTIFY_EMAIL": "owner@example.invalid", "CARD_UPDATE_MAIL_ENABLED": "1",
                       "ENROLL_WELCOME_ENABLED": "1", "ENROLL_COURSEAPP_ENABLED": "0"})
    wh = load("stripe-webhook", "stripe_webhook_vercel_card_update")
    rid = "reg_cu_b"
    orig_urlopen = urllib.request.urlopen

    # ---- B1 差し替え ----
    kv, net = seeded_kv(rid), FakeNet()
    before = rec_of(kv, rid)
    ledger_before = {k: v for k, v in kv.store.items() if k.startswith("charge:")}
    raised = run_wh(wh, kv, net, cu_session(rid))
    rec = rec_of(kv, rid)
    check("B1a. 例外なし", raised is None, repr(raised))
    check("B1b. stripe_payment_method_id が新しいカード (pm_new) に", rec.get("stripe_payment_method_id") == "pm_new", rec.get("stripe_payment_method_id"))
    keep = ["registration_id", "stripe_customer_id", "monthly_fee", "checkout_mode", "first_charge_month", "start_month", "completed_at",
            "email", "studentName", "fee_breakdown", "source", "session_id"]
    check("B1c. ほかの項目 (月額・顧客・初回決済の月・受講開始月・登録日時など) はそのまま", all(rec.get(k) == before.get(k) for k in keep),
          {k: (before.get(k), rec.get(k)) for k in keep if rec.get(k) != before.get(k)})
    check("B1d. 画面用にカードの種類・末尾・期限・変更日時と前のカードを記録", rec.get("card_brand") == "VISA" and rec.get("card_last4") == "4242"
          and rec.get("card_exp") == "08/30" and rec.get("card_updated_at", 0) > 0 and rec.get("card_prev_payment_method_id") == "pm_old"
          and rec.get("card_update_session_id") == "cs_cu_1" and rec.get("card_update_count") == 1, rec)
    check("B1e. ★台帳 (charge:done / history) は不変・新しい登録を作らない・index も増えない",
          {k: v for k, v in kv.store.items() if k.startswith("charge:")} == ledger_before
          and [k for k in kv.store if k.startswith("reg:completed:")] == [f"reg:completed:{rid}"]
          and kv.zsets.get("reg:completed:index") == [rid], [k for k in kv.store if k.startswith("reg:")])
    check("B1f. 前のカード (pm_old) を顧客から外した (新しいカードは外さない)", net.detached == ["pm_old"], net.detached)
    pm1 = parent_mails(net)
    check("B1g. 保護者へ「変更を承りました」(新しいカードの種類と末尾・宛名は保護者名・「これからの月謝」)", len(pm1) == 1
          and "お支払いカードの変更を承りました" in pm1[0]["subject"] and "VISA 末尾 4242" in pm1[0]["text"]
          and pm1[0]["text"].startswith(f"{HANAKO} 様") and "これからの月謝の引き落としには" in pm1[0]["text"], pm1)
    o1 = owner_mails(net)
    check("B1h. 塾長へ通知 (★なし・前のカードは「外しました」・取り直しは 📜 の 🔁 再請求)", len(o1) == 1 and o1[0]["subject"].startswith("【カード変更】")
          and "★" not in o1[0]["subject"] and "Mastercard 末尾 4444（有効期限 01/27）（外しました）" in o1[0]["text"]
          and "VISA 末尾 4242" in o1[0]["subject"] and "🔁 再請求" in o1[0]["text"], [m.get("subject") for m in o1])
    idem = [h.get("Idempotency-key") or h.get("Idempotency-Key") for h in net.headers]
    check("B1i. メールの Idempotency-Key は session ごと (二重送信しない)", sorted(idem) == ["card-update/cs_cu_1/owner", "card-update/cs_cu_1/parent"], idem)
    audit = json.loads(kv.store.get("card_update:session:cs_cu_1") or "{}")
    check("B1j. 調査用の記録 card_update:session:{session} (applied・前のカード・detach の結果)",
          audit.get("status") == "applied" and audit.get("prev_payment_method_id") == "pm_old" and audit.get("detach_prev") == "detached"
          and audit.get("parent_mail") == "sent", audit)
    check("B1k. Stripe で前のカードの未完了の請求を確かめてから外した", any("/v1/payment_intents?customer=cus_1" in u for _, u in net.calls), net.calls)

    # ---- B2 再送 (別イベント・同じセッション) → 何もしない ----
    net2 = FakeNet()
    writes_before = list(kv.writes)
    raised = run_wh(wh, kv, net2, cu_session(rid), eid="evt_cu_1b")
    check("B2. 同じセッションの再送は何もしない (書き込み・detach・メールなし)", raised is None and kv.writes == writes_before and not net2.detached and not net2.sent,
          (raised, kv.writes[len(writes_before):], net2.detached, net2.sent))

    # ---- B3 2 回目のカード変更 (新しいリンク・新しいカード) ----
    net3 = FakeNet(si_pm="pm_new2")
    raised = run_wh(wh, kv, net3, cu_session(rid, sid="cs_cu_2", seti="seti_cu_2", created=1790100000), eid="evt_cu_2")
    rec = rec_of(kv, rid)
    check("B3. 2 回目も差し替わり、1 回目のカード (pm_new) を外す・回数 2", raised is None and rec.get("stripe_payment_method_id") == "pm_new2"
          and rec.get("card_update_count") == 2 and net3.detached == ["pm_new"] and rec.get("card_last4") == "0005", (raised, rec, net3.detached))

    # ---- B4 古いリンクの完了が後から届いた → 新しい方を残し、塾長に知らせる ----
    net4 = FakeNet(si_pm="pm_new")
    net4.pms["pm_new"]["customer"] = "cus_1"
    raised = run_wh(wh, kv, net4, cu_session(rid, sid="cs_cu_old", seti="seti_cu_old", created=1790050000), eid="evt_cu_old")
    rec = rec_of(kv, rid)
    o4 = owner_mails(net4)
    check("B4. 古いリンク (作成が前) の完了は差し替えず、そのカードを外し、塾長に ★ (保護者には送らない)", raised is None and rec.get("stripe_payment_method_id") == "pm_new2"
          and net4.detached == ["pm_new"] and not parent_mails(net4) and len(o4) == 1 and o4[0]["subject"].startswith("★要対応")
          and json.loads(kv.store.get("card_update:session:cs_cu_old") or "{}").get("status") == "stale_session", (raised, rec.get("stripe_payment_method_id"), net4.detached, o4))

    # ---- B5 登録が無い (リンクの後に退塾処理) ----
    kv5, net5 = FakeKV(), FakeNet()
    raised = run_wh(wh, kv5, net5, cu_session("reg_gone", sid="cs_cu_5"), eid="evt_cu_5")
    check("B5a. 登録が無ければ作らない (reg:completed を書かない)", raised is None and not [k for k in kv5.store if k.startswith("reg:")], list(kv5.store))
    check("B5b. 入力されたカード (使われない) は外す", net5.detached == ["pm_new"], net5.detached)
    o5 = owner_mails(net5)
    check("B5c. 塾長に ★要対応 (保護者には完了画面が出ているので連絡を・保護者には送らない)", len(o5) == 1 and o5[0]["subject"].startswith("★要対応【カード変更】")
          and "連絡してください" in o5[0]["text"] and not parent_mails(net5), [m.get("subject") for m in net5.sent])

    # ---- B6 顧客が違う ----
    kv6, net6 = seeded_kv("reg_cu_6", customer="cus_9"), FakeNet()
    raised = run_wh(wh, kv6, net6, cu_session("reg_cu_6", sid="cs_cu_6"), eid="evt_cu_6")
    check("B6. 登録の顧客と違えば差し替えない・何も外さない・塾長に ★", raised is None and rec_of(kv6, "reg_cu_6").get("stripe_payment_method_id") == "pm_old"
          and not net6.detached and any(m["subject"].startswith("★要対応") for m in net6.sent), (raised, net6.detached, [m["subject"] for m in net6.sent]))
    kv6b, net6b = seeded_kv("reg_cu_6b"), FakeNet(si_customer="cus_9")
    raised = run_wh(wh, kv6b, net6b, cu_session("reg_cu_6b", sid="cs_cu_6b"), eid="evt_cu_6b")
    check("B6b. リンクの顧客と SetupIntent の顧客が違えば差し替えない", raised is None and rec_of(kv6b, "reg_cu_6b").get("stripe_payment_method_id") == "pm_old" and not net6b.detached)

    # ---- B7 前のカードを外さない場面 (処理中・3DS 待ち・確かめられない) ----
    this_m = wh._course_jst().strftime("%Y-%m")
    kv7, net7 = seeded_kv("reg_cu_7"), FakeNet()
    kv7.store[f"charge:done:reg_cu_7:{wh._enroll_next_month(this_m)}"] = "pending"
    raised = run_wh(wh, kv7, net7, cu_session("reg_cu_7", sid="cs_cu_7"), eid="evt_cu_7")
    o7 = owner_mails(net7)
    check("B7a. 翌月分が処理中 (pending) なら差し替えるが前のカードは外さず、塾長に ★", raised is None
          and rec_of(kv7, "reg_cu_7").get("stripe_payment_method_id") == "pm_new" and not net7.detached
          and len(o7) == 1 and o7[0]["subject"].startswith("★要対応") and "前のカードは外していません" in o7[0]["text"], (raised, net7.detached, o7))
    kv7b, net7b = seeded_kv("reg_cu_7b"), FakeNet()
    m3 = wh._enroll_prev_month(wh._enroll_prev_month(wh._enroll_prev_month(this_m)))
    kv7b.store[f"charge:done:reg_cu_7b:{m3}"] = "pending"   # 3 か月前の滞納分をまとめて請求中
    raised = run_wh(wh, kv7b, net7b, cu_session("reg_cu_7b", sid="cs_cu_7b"), eid="evt_cu_7b")
    check("B7b. 3 か月前の滞納分の請求が処理中でも前のカードは外さない", raised is None and not net7b.detached
          and rec_of(kv7b, "reg_cu_7b").get("stripe_payment_method_id") == "pm_new", (raised, net7b.detached))
    kv7c, net7c = seeded_kv("reg_cu_7c"), FakeNet()
    kv7c.store[f"charge:done:reg_cu_7c:{this_m}"] = json.dumps({"status": "succeeded"})   # 済んだ請求は処理中ではない
    raised = run_wh(wh, kv7c, net7c, cu_session("reg_cu_7c", sid="cs_cu_7c"), eid="evt_cu_7c")
    check("B7c. 済んだ請求 (succeeded) は処理中に数えない (前のカードを外す)", raised is None and net7c.detached == ["pm_old"], net7c.detached)
    pi_ra = {"id": "pi_ra", "object": "payment_intent", "status": "requires_action", "payment_method": "pm_old", "metadata": {"month": this_m}}
    kv7d, net7d = seeded_kv("reg_cu_7d"), FakeNet(pis=[pi_ra])
    raised = run_wh(wh, kv7d, net7d, cu_session("reg_cu_7d", sid="cs_cu_7d"), eid="evt_cu_7d")
    o7d = owner_mails(net7d)
    check("B7d. 前のカードで本人認証 (3DS) 待ちの請求が Stripe にあれば外さない (保護者が認証できなくなる)・塾長に ★", raised is None
          and not net7d.detached and rec_of(kv7d, "reg_cu_7d").get("stripe_payment_method_id") == "pm_new"
          and len(o7d) == 1 and "本人認証 (3DS) 待ち" in o7d[0]["text"], (raised, net7d.detached, o7d))
    pi_other = {"id": "pi_x", "status": "requires_action", "payment_method": "pm_someone", "metadata": {}}
    pi_done = {"id": "pi_y", "status": "succeeded", "payment_method": "pm_old", "metadata": {}}
    kv7e, net7e = seeded_kv("reg_cu_7e"), FakeNet(pis=[pi_other, pi_done])
    raised = run_wh(wh, kv7e, net7e, cu_session("reg_cu_7e", sid="cs_cu_7e"), eid="evt_cu_7e")
    check("B7e. 別のカードの 3DS 待ち・前のカードの済んだ請求は妨げにならない (外す)", raised is None and net7e.detached == ["pm_old"], net7e.detached)
    kv7f, net7f = seeded_kv("reg_cu_7f"), FakeNet(pis_fail=True)
    raised = run_wh(wh, kv7f, net7f, cu_session("reg_cu_7f", sid="cs_cu_7f"), eid="evt_cu_7f")
    check("B7f. Stripe で請求の状況を確かめられなければ外さない (外したカードは戻せない)", raised is None and not net7f.detached
          and rec_of(kv7f, "reg_cu_7f").get("stripe_payment_method_id") == "pm_new", net7f.detached)

    # ---- B8 KV / Stripe に聞けない → _RetryLater (外部には何もしない) ----
    raised = run_wh(wh, DownKV(), FakeNet(), cu_session("reg_cu_8", sid="cs_cu_8"), eid="evt_cu_8")
    check("B8a. KV が読めなければ _RetryLater", isinstance(raised, wh._RetryLater), repr(raised))
    kv8, net8 = seeded_kv("reg_cu_8b"), FakeNet(si_fail=True)
    raised = run_wh(wh, kv8, net8, cu_session("reg_cu_8b", sid="cs_cu_8b"), eid="evt_cu_8b")
    check("B8b. SetupIntent を取れなければ _RetryLater (登録は前のカードのまま)", isinstance(raised, wh._RetryLater)
          and rec_of(kv8, "reg_cu_8b").get("stripe_payment_method_id") == "pm_old" and not net8.sent, repr(raised))
    kv8c = SetFailKV()
    kv8c.store["reg:completed:reg_cu_8c"] = json.dumps(reg_record("reg_cu_8c"), ensure_ascii=False)
    net8c = FakeNet()
    raised = run_wh(wh, kv8c, net8c, cu_session("reg_cu_8c", sid="cs_cu_8c"), eid="evt_cu_8c")
    check("B8c. 登録を書けなければ _RetryLater (前のカードを外さない・メールなし)", isinstance(raised, wh._RetryLater) and not net8c.detached and not net8c.sent,
          (repr(raised), net8c.detached, net8c.sent))
    os.environ["STRIPE_SECRET_KEY"] = ""
    raised = run_wh(wh, seeded_kv("reg_cu_8d"), FakeNet(), cu_session("reg_cu_8d", sid="cs_cu_8d"), eid="evt_cu_8d")
    check("B8d. STRIPE_SECRET_KEY 未設定は _RetryLater (設定後の再送で反映される)", isinstance(raised, wh._RetryLater), repr(raised))
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy"

    # ---- B9 カード登録が完了していない SetupIntent ----
    kv9, net9 = seeded_kv("reg_cu_9"), FakeNet(si_status="requires_action")
    raised = run_wh(wh, kv9, net9, cu_session("reg_cu_9", sid="cs_cu_9"), eid="evt_cu_9")
    check("B9. SetupIntent が succeeded でなければ差し替えない (塾長に ★・リンクを作り直す案内)", raised is None and rec_of(kv9, "reg_cu_9").get("stripe_payment_method_id") == "pm_old"
          and not net9.detached and any(m["subject"].startswith("★要対応") and "作り直して" in m["text"] for m in net9.sent), (raised, [m["subject"] for m in net9.sent]))

    # ---- B10 テストモード → 差し替えるがメールなし ----
    kv10, net10 = seeded_kv("reg_cu_10"), FakeNet()
    raised = run_wh(wh, kv10, net10, cu_session("reg_cu_10", sid="cs_cu_10", livemode=False), eid="evt_cu_10")
    check("B10. テストモードは差し替えるがメールは送らない", raised is None and rec_of(kv10, "reg_cu_10").get("stripe_payment_method_id") == "pm_new" and not net10.sent,
          (raised, net10.sent))

    # ---- B11 保護者メールの停止スイッチ・メール失敗・宛名 ----
    os.environ["CARD_UPDATE_MAIL_ENABLED"] = "0"
    kv11, net11 = seeded_kv("reg_cu_11"), FakeNet()
    raised = run_wh(wh, kv11, net11, cu_session("reg_cu_11", sid="cs_cu_11"), eid="evt_cu_11")
    check("B11a. CARD_UPDATE_MAIL_ENABLED=0 → 保護者には送らず、塾長通知に「停止中」", raised is None
          and [m.get("to") for m in net11.sent] == [["owner@example.invalid"]] and "停止中" in net11.sent[0]["text"]
          and "★" not in net11.sent[0]["subject"], [m.get("subject") for m in net11.sent])
    os.environ["CARD_UPDATE_MAIL_ENABLED"] = "1"
    kv11b, net11b = seeded_kv("reg_cu_11b"), FakeNet(resend_fail=True)
    raised = run_wh(wh, kv11b, net11b, cu_session("reg_cu_11b", sid="cs_cu_11b"), eid="evt_cu_11b")
    check("B11b. メールが送れなくても差し替えは済む (例外を外に出さない)", raised is None and rec_of(kv11b, "reg_cu_11b").get("stripe_payment_method_id") == "pm_new"
          and json.loads(kv11b.store.get("card_update:session:cs_cu_11b") or "{}").get("parent_mail") == "failed", repr(raised))
    kv11c, net11c = seeded_kv("reg_cu_11c", parentName=""), FakeNet()
    raised = run_wh(wh, kv11c, net11c, cu_session("reg_cu_11c", sid="cs_cu_11c"), eid="evt_cu_11c")
    p11 = parent_mails(net11c)
    check("B11c. 保護者名が無ければ「保護者 様」(塾長通知の「-」を宛名にしない)", raised is None and bool(p11) and p11[0]["text"].startswith("保護者 様"),
          p11[0]["text"][:40] if p11 else None)

    # ---- B12 前のカードを外せない / 既に外れている ----
    kv12, net12 = seeded_kv("reg_cu_12"), FakeNet(detach_fail=b'{"error":{"message":"Something went wrong"}}')
    raised = run_wh(wh, kv12, net12, cu_session("reg_cu_12", sid="cs_cu_12"), eid="evt_cu_12")
    o12 = owner_mails(net12)
    check("B12a. 前のカードを外せなければ塾長に ★ (差し替えは済んでいる)", raised is None and rec_of(kv12, "reg_cu_12").get("stripe_payment_method_id") == "pm_new"
          and len(o12) == 1 and o12[0]["subject"].startswith("★要対応") and "外せませんでした" in o12[0]["text"], o12)
    kv12b, net12b = seeded_kv("reg_cu_12b"), FakeNet(detach_fail=b'{"error":{"message":"The payment method you provided is not attached to a customer so detachment is impossible."}}')
    raised = run_wh(wh, kv12b, net12b, cu_session("reg_cu_12b", sid="cs_cu_12b"), eid="evt_cu_12b")
    o12b = owner_mails(net12b)
    check("B12b. 既に外れていた (not attached) は失敗扱いにしない", raised is None and len(o12b) == 1 and "★" not in o12b[0]["subject"], [m["subject"] for m in o12b])
    kv12c, net12c = seeded_kv("reg_cu_12c"), FakeNet()
    net12c.pms["pm_old"]["customer"] = None
    raised = run_wh(wh, kv12c, net12c, cu_session("reg_cu_12c", sid="cs_cu_12c"), eid="evt_cu_12c")
    check("B12c. 前のカードが既に顧客から外れていれば detach を呼ばない", raised is None and not net12c.detached
          and json.loads(kv12c.store.get("card_update:session:cs_cu_12c") or "{}").get("detach_prev") == "already", net12c.detached)

    # ---- B13 従来の道を壊していない・取り違えない ----
    kv13, net13 = seeded_kv("reg_cu_13"), FakeNet()
    s13 = cu_session("reg_cu_13", sid="cs_cu_13", system=None)   # system タグが無い (= 本来ありえない) ときは従来の分岐へ → registration_id が無いので skip
    raised = run_wh(wh, kv13, net13, s13, eid="evt_cu_13")
    check("B13a. system タグの無い card_update_rid だけのセッションは何も書かない (従来の分岐が skip)", raised is None
          and rec_of(kv13, "reg_cu_13").get("stripe_payment_method_id") == "pm_old" and not net13.calls and not kv13.writes, (raised, kv13.writes, net13.calls))
    kv13b, net13b = FakeKV(), FakeNet(si_customer="cus_2")
    legacy = {"id": "cs_reg_new", "object": "checkout.session", "mode": "setup", "status": "complete", "livemode": True,
              "customer": "cus_2", "setup_intent": "seti_reg_new", "created": 1790000000, "customer_details": {"email": "parent@example.invalid"},
              "metadata": {"registration_id": "reg_new_setup", "system": "juku-payment-monthly", "monthly_fee": "8850", "student_name": TARO}}
    raised = run_wh(wh, kv13b, net13b, legacy, eid="evt_reg_new")
    check("B13b. 従来のカード登録 (juku-payment-monthly・registration_id) は今までどおり新しい登録になる",
          raised is None and rec_of(kv13b, "reg_new_setup").get("stripe_payment_method_id") == "pm_new"
          and rec_of(kv13b, "reg_new_setup").get("monthly_fee") == 8850 and not net13b.detached, (raised, rec_of(kv13b, "reg_new_setup")))
    # 申込 (setup) の完了イベントが 24 時間後に再送された (webhook:seen は消えている) → カード変更・月額の編集を上書きしない
    r13 = rec_of(kv13b, "reg_new_setup")
    r13.update(stripe_payment_method_id="pm_new2", card_last4="0005", monthly_fee=12000, monthly_fee_edited_at=1790000500)
    kv13b.store["reg:completed:reg_new_setup"] = json.dumps(r13, ensure_ascii=False)
    raised = run_wh(wh, kv13b, FakeNet(si_customer="cus_2"), legacy, eid="evt_reg_new_resend")
    r13b = rec_of(kv13b, "reg_new_setup")
    check("B13c. ★申込の完了の再送は登録を書き直さない (カード変更・月額の編集が残る)", raised is None and r13b.get("stripe_payment_method_id") == "pm_new2"
          and r13b.get("monthly_fee") == 12000 and r13b.get("card_last4") == "0005", r13b)
    kv13c = FakeKV()
    kv13c.store["reg:completed:reg_new_setup"] = json.dumps({**r13, "stripe_payment_method_id": ""}, ensure_ascii=False)
    raised = run_wh(wh, kv13c, FakeNet(si_customer="cus_2"), legacy, eid="evt_reg_repair")
    check("B13d. カードの無い登録 (前回カードを取れなかった) は再送で直せる (従来どおり)", raised is None
          and rec_of(kv13c, "reg_new_setup").get("stripe_payment_method_id") == "pm_new", rec_of(kv13c, "reg_new_setup"))

    class RegGetFailKV(FakeKV):
        def __call__(self, *args):
            if args[0] == "GET" and str(args[1]).startswith("reg:completed:"):
                return None
            return super().__call__(*args)
    kv13e = RegGetFailKV()
    kv13e.store.update(kv13b.store)
    raised = run_wh(wh, kv13e, FakeNet(si_customer="cus_2"), legacy, eid="evt_reg_new_kvfail")
    check("B13e. 再送かどうかを KV で確かめられなければ _RetryLater (確かめずに書き直してカード変更を巻き戻さない)",
          isinstance(raised, wh._RetryLater) and json.loads(kv13e.store["reg:completed:reg_new_setup"]).get("stripe_payment_method_id") == "pm_new2", repr(raised))
    kv13f = FakeKV()
    kv13f.store["reg:completed:reg_new_setup"] = kv13b.store["reg:completed:reg_new_setup"]
    raised = run_wh(wh, kv13f, FakeNet(si_customer="cus_2"), legacy, eid="evt_reg_new_reindex")
    check("B13f. 再送のとき一覧 (index) から抜けていれば戻す (ZADD NX・登録は書き直さない)", raised is None
          and kv13f.zsets.get("reg:completed:index") == ["reg_new_setup"] and ("ZADD NX", "reg:completed:index") in kv13f.writes
          and rec_of(kv13f, "reg_new_setup").get("stripe_payment_method_id") == "pm_new2", (raised, kv13f.writes))
    kv13g = FakeKV()
    kv13g.store["reg:completed:reg_new_setup"] = kv13b.store["reg:completed:reg_new_setup"]
    kv13g.store["reg:zombie:reg_new_setup"] = json.dumps({"reason": "Stripe customer/PM not found"})
    raised = run_wh(wh, kv13g, FakeNet(si_customer="cus_2"), legacy, eid="evt_reg_new_zombie")
    check("B13g. Stripe で顧客/カードが見つからず外した登録 (zombie) は、再送でも一覧に戻さない", raised is None
          and not kv13g.zsets.get("reg:completed:index"), kv13g.zsets)

    # ---- B14 読んでから書くまでに、月額の保存が先に入った (CAS) → 読み直して両方残す ----
    kv14, net14 = seeded_kv("reg_cu_14"), FakeNet()

    def fee_edit(k):
        r = json.loads(k.store["reg:completed:reg_cu_14"])
        r.update(monthly_fee=12000, monthly_fee_prev=8850, monthly_fee_edited_at=1790000100)
        k.store["reg:completed:reg_cu_14"] = json.dumps(r, ensure_ascii=False)
    kv14.before_eval = fee_edit
    raised = run_wh(wh, kv14, net14, cu_session("reg_cu_14", sid="cs_cu_14"), eid="evt_cu_14")
    r14 = rec_of(kv14, "reg_cu_14")
    check("B14. 月額の保存と重なっても、読み直して載せ直す (新しいカード・新しい月額の両方が残る)", raised is None
          and r14.get("stripe_payment_method_id") == "pm_new" and r14.get("monthly_fee") == 12000 and net14.detached == ["pm_old"], (raised, r14))

    # ---- B15 読んでから書くまでに退塾処理で消えた → 生き返らせない ----
    kv15, net15 = seeded_kv("reg_cu_15"), FakeNet()

    def cancel_now(k):
        k.store.pop("reg:completed:reg_cu_15", None)
        k.zsets["reg:completed:index"] = []
    kv15.before_eval = cancel_now
    raised = run_wh(wh, kv15, net15, cu_session("reg_cu_15", sid="cs_cu_15"), eid="evt_cu_15")
    check("B15. 退塾処理と重なったら登録を生き返らせない (入力されたカードは外し、塾長に ★)", raised is None
          and "reg:completed:reg_cu_15" not in kv15.store and net15.detached == ["pm_new"]
          and any(m["subject"].startswith("★要対応") for m in net15.sent) and not parent_mails(net15), (raised, list(kv15.store), net15.detached))

    # ---- B16 EVAL が使えない KV → 従来どおり SET で書く (カード変更を止めない) ----
    kv16, net16 = seeded_kv("reg_cu_16"), FakeNet()
    kv16.eval_supported = False
    raised = run_wh(wh, kv16, net16, cu_session("reg_cu_16", sid="cs_cu_16"), eid="evt_cu_16")
    check("B16a. EVAL を断られる KV (HTTP 4xx) でも差し替えはできる (読み直して比べてから SET)", raised is None
          and rec_of(kv16, "reg_cu_16").get("stripe_payment_method_id") == "pm_new" and net16.detached == ["pm_old"], raised)
    kv16b, net16b = seeded_kv("reg_cu_16b"), FakeNet()
    kv16b.eval_supported = False

    class GoneBeforeSetKV(FakeKV):
        """EVAL を断る KV で、比べるための読み直しの時点では登録が消えている (退塾処理と重なった)"""
        n_get = 0

        def __call__(self, *args):
            if args[0] == "GET" and args[1] == "reg:completed:reg_cu_16b":
                GoneBeforeSetKV.n_get += 1
                if GoneBeforeSetKV.n_get == 2:
                    self.store.pop("reg:completed:reg_cu_16b", None)
            return super().__call__(*args)
    kv16c = GoneBeforeSetKV()
    kv16c.store.update(kv16b.store)
    kv16c.zsets.update(kv16b.zsets)
    kv16c.eval_supported = False
    raised = run_wh(wh, kv16c, net16b, cu_session("reg_cu_16b", sid="cs_cu_16b"), eid="evt_cu_16b")
    check("B16b. EVAL を断られる KV でも、消えた登録は書き戻さない (比べる読み直しで missing)", raised is None
          and "reg:completed:reg_cu_16b" not in kv16c.store and net16b.detached == ["pm_new"], (raised, list(kv16c.store), net16b.detached))
    raised = run_wh(wh, seeded_kv("reg_cu_16d"), FakeNet(), cu_session("reg_cu_16d", sid="cs_cu_16d"), eid="evt_cu_16d")
    kv16e = seeded_kv("reg_cu_16e")
    wh._redis_safe, urllib.request.urlopen = kv16e, FakeNet()
    wh._kv_eval = DownKV().eval_api
    raised = None
    try:
        wh._handle_checkout_completed(event(cu_session("reg_cu_16e", sid="cs_cu_16e"), eid="evt_cu_16e"))
    except Exception as e:
        raised = e
    check("B16c. EVAL に応答が無ければ _RetryLater (書いたことにしない)", isinstance(raised, wh._RetryLater)
          and rec_of(kv16e, "reg_cu_16e").get("stripe_payment_method_id") == "pm_old", repr(raised))

    # ---- B17 書けたが応答が届かず再送された → 後始末 (前のカード・メール・記録) をやり直す ----
    kv17, net17 = seeded_kv("reg_cu_17"), FakeNet()
    r17 = rec_of(kv17, "reg_cu_17")
    r17.update(stripe_payment_method_id="pm_new", card_update_session_id="cs_cu_17", card_prev_payment_method_id="pm_old",
               card_update_session_created=1790000000, card_last4="4242", card_brand="VISA")
    kv17.store["reg:completed:reg_cu_17"] = json.dumps(r17, ensure_ascii=False)
    raised = run_wh(wh, kv17, net17, cu_session("reg_cu_17", sid="cs_cu_17"), eid="evt_cu_17")
    check("B17. 差し替えだけ済んで後始末が無い再送 → 前のカードを外し、メールと記録を出す", raised is None and net17.detached == ["pm_old"]
          and len(parent_mails(net17)) == 1 and len(owner_mails(net17)) == 1
          and json.loads(kv17.store.get("card_update:session:cs_cu_17") or "{}").get("status") == "applied", (raised, net17.detached))

    # ---- B18 一覧 (index) から外れた登録 → 差し替えるが ★ で知らせる ----
    kv18, net18 = seeded_kv("reg_cu_18"), FakeNet()
    kv18.zsets["reg:completed:index"] = []
    raised = run_wh(wh, kv18, net18, cu_session("reg_cu_18", sid="cs_cu_18"), eid="evt_cu_18")
    o18 = owner_mails(net18)
    check("B18. 月末の一覧から外れた登録は、差し替えても ★ で知らせる (引き落とされないため)", raised is None
          and len(o18) == 1 and o18[0]["subject"].startswith("★要対応") and "一覧から外れています" in o18[0]["text"], o18)

    # ---- B19 入塾の初回決済の完了が後から再送された → 登録 (カード変更後) を上書きしない ----
    kv19 = FakeKV()
    r19 = reg_record("reg_cu_19", pm="pm_new2", card_last4="0005", first_charge_session_id="cs_first_19", session_id="cs_first_19")
    kv19.store["reg:completed:reg_cu_19"] = json.dumps(r19, ensure_ascii=False)
    kv19.zsets["reg:completed:index"] = ["reg_cu_19"]
    first = {"id": "cs_first_19", "object": "checkout.session", "mode": "payment", "livemode": True, "payment_status": "paid",
             "amount_total": 18850, "currency": "jpy", "customer": "cus_1", "customer_details": {"email": "parent@example.invalid"},
             "created": 1789000000, "payment_intent": "pi_first_19",
             "metadata": {"registration_id": "reg_cu_19", "system": "juku-payment-monthly", "first_charge": "1", "monthly_fee": "8850",
                          "student_name": TARO, "first_total": "18850", "entry_fee": "10000", "source": "enrollment-form-v1-payment"}}

    class FirstNet(FakeNet):
        def __call__(self, req, timeout=None):
            if "api.stripe.com/v1/payment_intents/pi_first_19" in req.full_url:
                return io.BytesIO(json.dumps({"id": "pi_first_19", "payment_method": "pm_old", "customer": "cus_1",
                                              "amount_received": 18850, "status": "succeeded"}).encode())
            return super().__call__(req, timeout)
    raised = run_wh(wh, kv19, FirstNet(), first, eid="evt_first_19_resend")
    check("B19a. ★入塾の初回決済の再送は登録を書き直さない (カード変更後のカードが残る)", raised is None
          and rec_of(kv19, "reg_cu_19").get("stripe_payment_method_id") == "pm_new2", (raised, rec_of(kv19, "reg_cu_19").get("stripe_payment_method_id")))
    kv19b = FakeKV()
    kv19b.store["reg:completed:reg_cu_19"] = kv19.store["reg:completed:reg_cu_19"]   # 前回 SET は通ったが応答が届かず、一覧に入っていない
    raised = run_wh(wh, kv19b, FirstNet(), first, eid="evt_first_19_lostack")
    check("B19b. 初回決済の再送で一覧 (index) から抜けていれば戻す (戻さないと毎月の引き落としから漏れる)", raised is None
          and kv19b.zsets.get("reg:completed:index") == ["reg_cu_19"], (raised, kv19b.zsets))
    # ---- B20 同じセッションの再送 (24 時間後の Dashboard 再送など) は、その後の状態にかかわらず何もしない ----
    kv20, net20 = seeded_kv("reg_cu_20"), FakeNet()
    raised = run_wh(wh, kv20, net20, cu_session("reg_cu_20", sid="cs_cu_20"), eid="evt_cu_20")
    r20 = rec_of(kv20, "reg_cu_20")
    r20.update(stripe_payment_method_id="pm_new2", card_update_session_created=1790200000)   # その後に別のリンクで差し替え済み
    kv20.store["reg:completed:reg_cu_20"] = json.dumps(r20, ensure_ascii=False)
    net20b = FakeNet()
    w0 = list(kv20.writes)
    raised = run_wh(wh, kv20, net20b, cu_session("reg_cu_20", sid="cs_cu_20"), eid="evt_cu_20_resend")
    check("B20. 処理済みのセッションの再送は何もしない (古いリンク扱いでカードを外したり、記録を書き換えたりしない)", raised is None
          and not net20b.detached and not net20b.sent and kv20.writes == w0
          and json.loads(kv20.store["card_update:session:cs_cu_20"]).get("status") == "applied", (raised, net20b.detached, kv20.writes[len(w0):]))

    class AuditGetFailKV(FakeKV):
        def __call__(self, *args):
            if args[0] == "GET" and str(args[1]).startswith("card_update:session:"):
                return None
            return super().__call__(*args)
    kv21 = AuditGetFailKV()
    kv21.store.update(seeded_kv("reg_cu_21").store)
    raised = run_wh(wh, kv21, FakeNet(), cu_session("reg_cu_21", sid="cs_cu_21"), eid="evt_cu_21")
    check("B21. 処理済みかどうかを KV で確かめられなければ _RetryLater (何もしない)", isinstance(raised, wh._RetryLater)
          and rec_of(kv21, "reg_cu_21").get("stripe_payment_method_id") == "pm_old", repr(raised))

    kv22, net22 = seeded_kv("reg_cu_22"), FakeNet(si_status="requires_action")
    kv22.store["card_update:link:reg_cu_22"] = json.dumps({"session_id": "cs_cu_22", "url": "u", "expires_at": int(time.time()) + 3600})
    raised = run_wh(wh, kv22, net22, cu_session("reg_cu_22", sid="cs_cu_22"), eid="evt_cu_22")
    check("B22. 差し替えなかった場合も使い終わったリンクの記録は消す (画面に「まだ使えます」と出さない)", raised is None
          and "card_update:link:reg_cu_22" not in kv22.store, list(kv22.store))

    kv23, net23 = seeded_kv("reg_cu_23"), FakeNet()

    def cancel_right_after(k):
        k.store.pop("reg:completed:reg_cu_23", None)
        k.zsets["reg:completed:index"] = []
    kv23.after_eval = cancel_right_after
    raised = run_wh(wh, kv23, net23, cu_session("reg_cu_23", sid="cs_cu_23"), eid="evt_cu_23")
    check("B23. 書いた直後に退塾処理で消えたら、差し替え扱いにしない (入力されたカードを外す・保護者に「承りました」を送らない・塾長に ★)", raised is None
          and net23.detached == ["pm_new"] and not parent_mails(net23) and any(m["subject"].startswith("★要対応") for m in owner_mails(net23))
          and json.loads(kv23.store.get("card_update:session:cs_cu_23") or "{}").get("status") == "missing_after_apply", (raised, net23.detached))
    kv24, net24 = seeded_kv("reg_cu_24"), FakeNet()

    def newer_change(k):
        r = json.loads(k.store["reg:completed:reg_cu_24"])
        r["stripe_payment_method_id"] = "pm_newest"
        k.store["reg:completed:reg_cu_24"] = json.dumps(r, ensure_ascii=False)
    kv24.after_eval = newer_change
    raised = run_wh(wh, kv24, net24, cu_session("reg_cu_24", sid="cs_cu_24"), eid="evt_cu_24")
    check("B24. 書いた直後に別のカードに変わっていたら、差し替え扱いにしない (前のカードを外さない・保護者メールなし・★)", raised is None
          and not net24.detached and not parent_mails(net24) and any(m["subject"].startswith("★要対応") for m in owner_mails(net24))
          and json.loads(kv24.store.get("card_update:session:cs_cu_24") or "{}").get("status") == "superseded", (raised, net24.detached))
    kv25, net25 = seeded_kv("reg_cu_25", email=""), FakeNet()
    raised = run_wh(wh, kv25, net25, cu_session("reg_cu_25", sid="cs_cu_25"), eid="evt_cu_25")
    o25 = owner_mails(net25)
    check("B25. 登録に保護者のメールが無ければ確認メールは送れない → 塾長に ★ (LINE で伝える)", raised is None and len(o25) == 1
          and o25[0]["subject"].startswith("★要対応") and "LINE で「変更できました」" in o25[0]["text"], [m["subject"] for m in o25])
    urllib.request.urlopen = orig_urlopen


# ───────────────────────── C. 画面の項目・配線 ─────────────────────────
def test_wiring():
    print("\n[C] 画面の項目・配線")
    os.environ.update({"CHAT_ADMIN_PASSWORD": PW, "KV_REST_API_URL": "", "KV_REST_API_TOKEN": ""})
    rc = load("registered-customers", "vercel_registered_customers_cu")
    rc._admin_kv = lambda *a: None
    kv = FakeKV()
    kv.store["reg:completed:reg_c1"] = json.dumps(reg_record("reg_c1", card_brand="VISA", card_last4="4242", card_updated_at=1790000000), ensure_ascii=False)
    kv.zsets["reg:completed:index"] = ["reg_c1"]
    rc._redis = kv
    st, body = FakeReq(rc, b"").run_get()
    c0 = (body.get("customers") or [{}])[0]
    check("C1. 登録一覧に cardBrand / cardLast4 / cardUpdatedAt / checkoutMode", st == 200 and c0.get("cardBrand") == "VISA" and c0.get("cardLast4") == "4242"
          and c0.get("cardUpdatedAt") == 1790000000 and c0.get("checkoutMode") == "setup", (st, c0))
    ro = open(os.path.join(API, "admin-charge-readonly.py"), encoding="utf-8").read()
    check("C2. 月末プレビューも cardBrand / cardLast4 / cardUpdatedAt を返す", all(f'"{k}": ' in ro for k in ("cardBrand", "cardLast4", "cardUpdatedAt")))

    main_src = open(os.path.join(REPO, "server", "main.py"), encoding="utf-8").read()
    m = re.search(r'if event\["type"\] == "checkout\.session\.completed":(.{0,2500})', main_src, re.S)
    check("C3. 本体 (Railway) の webhook は checkout.session.completed の system が juku-payment で始まれば skip (= juku-payment-card-update も触らない)",
          bool(m) and '_meta_system.startswith("juku-payment")' in m.group(1) and CU_TAG.startswith("juku-payment"))
    vj = json.load(open(os.path.join(REPO, "vercel.json"), encoding="utf-8"))
    rw = vj.get("rewrites", [])
    idx = [i for i, r in enumerate(rw) if r.get("source") == "/payment/api/admin-card-update" and r.get("destination") == "/api/admin-card-update"]
    catch_all = [i for i, r in enumerate(rw) if r.get("source") == "/api/:path*"]
    check("C4. vercel.json の rewrite /payment/api/admin-card-update が /api/:path* (Railway 行き) より前", bool(idx) and bool(catch_all) and idx[0] < catch_all[0], (idx, catch_all))
    js = open(os.path.join(REPO, "payment", "app.js"), encoding="utf-8").read()
    calls = [js[i:i + 400] for i in [mm.start() for mm in re.finditer(re.escape("fetch('/payment/api/admin-card-update'"), js)]]
    check("C5. 画面はパスワード付きで create_link と status を呼ぶ", len(calls) == 2 and all("X-Admin-Password" in c for c in calls)
          and any("create_link" in c for c in calls) and any("'status'" in c for c in calls), len(calls))
    check("C6. 月末タブ・全生徒・実行結果の 3 か所から開ける", "openCardUpdateModal('${rid}')" in js and "openCardUpdateModal('${rid}', '', { failedMonth:" in js
          and "data-action=\"card-update\"" in js and "a === 'card-update'" in js)
    check("C6b. 作り直しは確認つき・リンクを作った後は「閉じる」が主ボタン", "前に作ったリンクは使えなくなります" in js and "setCardUpdateButtons(true)" in js)
    check("C6c. LINE の文面は「本日の課金はありません」と言わない (失敗した月をすぐ取り直すことがある)", "本日の課金はありません" not in js[js.find("function cardUpdateLineText"):js.find("async function submitCardUpdateLink")])
    check("C6d. 📜 失敗の行は、その後に回収済み・請求書を発行済みなら 🔁 再請求を出さず、まだなら 🔁 と 🪪 を出す", "r.collected" in js and "その後に回収済み" in js
          and "r.invoiced" in js and "請求書を発行済み" in js and "failedMonth: '${escapeHtmlME(data.month)}'" in js)
    check("C6e. 作り直しは replace: true・409 LINK_ACTIVE なら今のリンクを出す・状態を確かめている間は押せない", "replace: !!CARD_UPDATE_STATE.issued" in js
          and "data.error === 'LINK_ACTIVE'" in js and "loadCardUpdateStatus(rid, expectCustomerId || '', pw, seq).finally(" in js)
    check("C6f. 🔁 再請求が断られたら (ALREADY_COLLECTED)「再請求はしませんでした」と出して一覧を取り直す・名簿で入金済みなら確認で知らせる",
          "d1.error === 'ALREADY_COLLECTED'" in js and "再請求はしませんでした" in js and "rosterPaidNote" in js and "unlock 失敗" not in js)
    check("C6g. Stripe 案内メールは保存済みの古い文でも顧客ポータルのカード変更を案内しない", "withoutPortalCardChange(SETTINGS.stripeInviteBody" in js
          and "(24時間いつでも可能)\\n{{customerPortal}}" in js)
    html = open(os.path.join(REPO, "payment", "index.html"), encoding="utf-8").read()
    check("C7. index.html にカード変更のダイアログ (role=dialog・閉じるボタン・入力欄)",
          all(f'id="{k}"' in html for k in ("cardUpdateModal", "cardUpdateRid", "cardUpdatePw", "cardUpdateUrl", "cardUpdateLineText",
                                            "cardUpdateSubmitBtn", "cardUpdateCloseBtn", "cardUpdateTitle"))
          and 'role="dialog"' in html[html.find('id="cardUpdateModal"') - 80:html.find('id="cardUpdateModal"') + 120])
    page = os.path.join(REPO, "payment", "card-update-complete.html")
    src_api = open(os.path.join(API, "admin-card-update.py"), encoding="utf-8").read()
    ptxt = re.sub(r"<!--.*?-->", "", open(page, encoding="utf-8").read(), flags=re.S) if os.path.exists(page) else ""   # 注記のコメントは除く
    check("C8. 戻り先の完了ページがあり、中断 (?canceled=1) の表示も持つ・「本日の課金はありません」と言わない", bool(ptxt) and "/payment/card-update-complete.html" in src_api
          and "canceled" in ptxt and "本日の課金" not in ptxt)
    wh_src = open(os.path.join(API, "stripe-webhook.py"), encoding="utf-8").read()
    check("C9. webhook と API のタグが同じ値", f'CARD_UPDATE_SYSTEM_TAG = "{CU_TAG}"' in wh_src and f'CARD_UPDATE_SYSTEM_TAG = "{CU_TAG}"' in src_api)
    j = wh_src.find("if system_tag == CARD_UPDATE_SYSTEM_TAG:")
    k = wh_src.find('if not reg_id and system_tag != "juku-payment-monthly":')
    check("C10. webhook はカード変更を従来の新規登録の分岐より前に分ける", 0 < j < k, (j, k))
    cancel_src = open(os.path.join(API, "admin-registration-cancel.py"), encoding="utf-8").read()
    check("C11. CAS の Lua は webhook と月額の保存で同じ", wh_src.count("_KV_CAS_SCRIPT = (") == 1 and cancel_src.count("_KV_CAS_SCRIPT = (") == 1
          and wh_src[wh_src.find("_KV_CAS_SCRIPT = ("):wh_src.find("def _kv_eval")].strip()
          == cancel_src[cancel_src.find("_KV_CAS_SCRIPT = ("):cancel_src.find("def _kv_eval")].strip())


# ───────────────────────── D. 月額の保存 (update_fee) と退塾処理 ─────────────────────────
def test_cancel_module():
    print("\n[D] 月額の保存 (update_fee) の CAS・退塾処理の後始末 (api/admin-registration-cancel.py)")
    os.environ.update({"CHAT_ADMIN_PASSWORD": PW, "STRIPE_SECRET_KEY": "sk_test_dummy", "KV_REST_API_URL": "", "KV_REST_API_TOKEN": ""})
    mod = load("admin-registration-cancel", "vercel_admin_registration_cancel_cu")
    mod._admin_kv = lambda *a: None
    posts = []

    def fake_post(secret_key, path, form, idempotency_key=None):
        posts.append(path)
        return {"id": "x"}
    mod._stripe_post = fake_post

    kv = seeded_kv("reg_d1")

    def card_change(k):
        r = json.loads(k.store["reg:completed:reg_d1"])
        r.update(stripe_payment_method_id="pm_new", card_last4="4242", card_updated_at=1790000200)
        k.store["reg:completed:reg_d1"] = json.dumps(r, ensure_ascii=False)
    kv.before_eval = card_change
    mod._redis, mod._kv_eval = kv, kv.eval_api
    st, body = FakeReq(mod, {"action": "update_fee", "registrationId": "reg_d1", "monthly_fee": 12000}).run()
    r = rec_of(kv, "reg_d1")
    check("D1. 月額の保存とカード変更が重なっても、読み直して載せ直す (新しいカードを消さない・新しい月額)", st == 200
          and r.get("monthly_fee") == 12000 and r.get("stripe_payment_method_id") == "pm_new" and r.get("monthly_fee_prev") == 8850, (st, body, r))
    kv2 = seeded_kv("reg_d2")
    kv2.eval_supported = False
    mod._redis, mod._kv_eval = kv2, kv2.eval_api
    st, body = FakeReq(mod, {"action": "update_fee", "registrationId": "reg_d2", "monthly_fee": 9000}).run()
    check("D2a. EVAL を断られる KV (HTTP 4xx) でも月額は保存できる (読み直して比べてから SET)", st == 200 and rec_of(kv2, "reg_d2").get("monthly_fee") == 9000, (st, body))
    kv2b = seeded_kv("reg_d2b")
    mod._redis, mod._kv_eval = kv2b, DownKV().eval_api
    st, body = FakeReq(mod, {"action": "update_fee", "registrationId": "reg_d2b", "monthly_fee": 9000}).run()
    check("D2b. KV の応答が無ければ 502 (保存したことにしない)", st == 502 and rec_of(kv2b, "reg_d2b").get("monthly_fee") == 8850, (st, body))
    kv3 = seeded_kv("reg_d3")
    kv3.before_eval = lambda k: k.store.pop("reg:completed:reg_d3", None)
    mod._redis, mod._kv_eval = kv3, kv3.eval_api
    st, body = FakeReq(mod, {"action": "update_fee", "registrationId": "reg_d3", "monthly_fee": 9000}).run()
    check("D3. 保存の途中で登録が消えたら 404 (生き返らせない)", st == 404 and "reg:completed:reg_d3" not in kv3.store, (st, body))

    kv4 = seeded_kv("reg_d4", card_prev_payment_method_id="pm_prev_kept")
    kv4.store["card_update:link:reg_d4"] = json.dumps({"session_id": "cs_open_d4", "url": "https://checkout.stripe.com/c/pay/cs_open_d4",
                                                       "expires_at": int(time.time()) + 3600})
    mod._redis, mod._kv_eval = kv4, kv4.eval_api
    mod._stripe_get_json = lambda *a, **k: {"data": []}
    posts.clear()
    st, body = FakeReq(mod, {"registrationId": "reg_d4", "confirmStudentName": TARO, "reason": "退塾"}).run()
    check("D4a. 退塾処理は従来どおり (今のカードを外し、登録を canceled へ)", st == 200 and "payment_methods/pm_old/detach" in posts
          and "reg:completed:reg_d4" not in kv4.store and "reg:canceled:reg_d4" in kv4.store, (st, body, posts))
    check("D4b. 開いているカード変更リンクを失効させ、記録を消す", "checkout/sessions/cs_open_d4/expire" in posts and "card_update:link:reg_d4" not in kv4.store, posts)
    check("D4c. カード変更で残していた前のカードも外す", "payment_methods/pm_prev_kept/detach" in posts, posts)
    kv5 = seeded_kv("reg_d5", card_prev_payment_method_id="pm_prev_busy")
    mod._redis, mod._kv_eval = kv5, kv5.eval_api
    mod._stripe_get_json = lambda *a, **k: {"data": [{"id": "pi_ra", "status": "requires_action", "payment_method": "pm_prev_busy"}]}
    posts.clear()
    st, body = FakeReq(mod, {"registrationId": "reg_d5", "confirmStudentName": TARO, "reason": "退塾"}).run()
    check("D5a. 前のカードで本人認証待ちの請求が残っていれば、退塾処理でも前のカードは外さない (今のカードは従来どおり外す)", st == 200
          and "payment_methods/pm_prev_busy/detach" not in posts and "payment_methods/pm_old/detach" in posts, posts)
    kv5b = seeded_kv("reg_d5b", card_prev_payment_method_id="pm_prev_x")
    mod._redis, mod._kv_eval = kv5b, kv5b.eval_api
    mod._stripe_get_json = lambda *a, **k: None
    posts.clear()
    st, body = FakeReq(mod, {"registrationId": "reg_d5b", "confirmStudentName": TARO, "reason": "退塾"}).run()
    check("D5b. Stripe で確かめられなければ前のカードは外さない (退塾処理は完了)", st == 200 and "payment_methods/pm_prev_x/detach" not in posts
          and "reg:canceled:reg_d5b" in kv5b.store, (st, posts))


# ───────────────────────── E. 回収済みの月の「未課金にする」「再請求」を止める ─────────────────────────
def test_reconcile_guard():
    print("\n[E] 回収済みの月の mark_unpaid / retry を止める (api/admin-charge-reconcile.py)")
    os.environ.update({"CHAT_ADMIN_PASSWORD": PW, "STRIPE_SECRET_KEY": "sk_test_dummy", "KV_REST_API_URL": "", "KV_REST_API_TOKEN": ""})
    mod = load("admin-charge-reconcile", "vercel_admin_charge_reconcile_cu")
    mod._admin_kv = lambda *a: None
    stripe_calls = []
    mod._stripe_post = lambda *a, **k: stripe_calls.append(a[1]) or {"id": "pi_new", "status": "succeeded"}
    mod._stripe_get = lambda *a, **k: stripe_calls.append(a[1]) or {}

    kv = seeded_kv("reg_e1")   # 2026-10 は charge:done=succeeded・charge:history あり (回収済み)
    kv.store["charge:failed:reg_e1:2026-10"] = json.dumps({"error_code": "expired_card"})   # 失敗の記録は回収後も残る
    mod._redis = kv
    st, body = FakeReq(mod, {"action": "mark_unpaid", "registrationId": "reg_e1", "month": "2026-10"}).run()
    check("E1a. 回収済みの月の mark_unpaid は 409 ALREADY_COLLECTED (done を消さない)", st == 409 and body.get("error") == "ALREADY_COLLECTED"
          and "charge:done:reg_e1:2026-10" in kv.store, (st, body))
    st, body = FakeReq(mod, {"action": "retry", "registrationId": "reg_e1", "month": "2026-10"}).run()
    check("E1b. 回収済みの月の retry も 409 (Stripe を呼ばない)", st == 409 and body.get("error") == "ALREADY_COLLECTED" and not stripe_calls, (st, body, stripe_calls))
    kv.store.pop("charge:history:reg_e1:2026-10")
    st, body = FakeReq(mod, {"action": "mark_unpaid", "registrationId": "reg_e1", "month": "2026-10"}).run()
    check("E1c. 台帳が無くても done が succeeded なら止める", st == 409, (st, body))
    kv.store.pop("charge:done:reg_e1:2026-10")
    kv.store["charge:history:reg_e1:2026-10"] = json.dumps({"status": "succeeded"})
    st, body = FakeReq(mod, {"action": "retry", "registrationId": "reg_e1", "month": "2026-10"}).run()
    check("E1d. done が消えていても (60 日) 台帳に成功があれば retry を止める", st == 409 and not stripe_calls, (st, body))
    st, body = FakeReq(mod, {"action": "mark_unpaid", "registrationId": "reg_e1", "month": "2026-09"}).run()
    check("E1e. 入塾時の初回決済の月も止める", st == 409 and "初回決済" in body.get("message", ""), (st, body))

    kv2 = seeded_kv("reg_e2")
    kv2.store["charge:done:reg_e2:2026-11"] = "pending"   # 途中で止まった (要確認) 月は従来どおり未課金にできる
    mod._redis = kv2
    st, body = FakeReq(mod, {"action": "mark_unpaid", "registrationId": "reg_e2", "month": "2026-11"}).run()
    check("E2a. 回収していない月 (done=pending) の mark_unpaid は従来どおり通る", st == 200 and "charge:done:reg_e2:2026-11" not in kv2.store, (st, body))
    kv2.store["charge:done:reg_e2:2026-12"] = json.dumps({"status": "uncertain"})
    st, body = FakeReq(mod, {"action": "mark_unpaid", "registrationId": "reg_e2", "month": "2026-12"}).run()
    check("E2b. 要確認 (uncertain) の月も従来どおり通る", st == 200, (st, body))
    st, body = FakeReq(mod, {"action": "retry", "registrationId": "reg_e2", "month": "2026-11"}).run()
    check("E2c. 回収していない月の retry は従来どおり新しいカードで請求する", st == 200 and "payment_intents" in stripe_calls, (st, body, stripe_calls))


# ───────────────────────── F. 📜 失敗の行の「その後に回収済み」 ─────────────────────────
def test_readonly_failed_flag():
    print("\n[F] 📜 失敗の行の「その後に回収済み」(api/admin-charge-readonly.py)")
    os.environ.update({"CHAT_ADMIN_PASSWORD": PW, "KV_REST_API_URL": "", "KV_REST_API_TOKEN": ""})
    mod = load("admin-charge-readonly", "vercel_admin_charge_readonly_cu")
    kv = FakeKV()
    kv.zsets["charge:failed:index"] = ["reg_f1:2026-10", "reg_f2:2026-10"]
    kv.store["charge:failed:reg_f1:2026-10"] = json.dumps({"student_name": TARO, "amount": 8850, "error_code": "expired_card"}, ensure_ascii=False)
    kv.store["charge:failed:reg_f2:2026-10"] = json.dumps({"student_name": HANAKO, "amount": 7500, "error_code": "expired_card"}, ensure_ascii=False)
    kv.store["charge:history:reg_f1:2026-10"] = json.dumps({"status": "succeeded", "amount": 8850})
    mod._redis = kv
    req = FakeReq(mod, b"")
    mod._handle_history(req, {"month": ["2026-10"], "type": ["failed"]})
    body = json.loads(req.wfile.getvalue().decode() or "{}")
    flags = {f.get("registrationId"): f.get("collected") for f in body.get("failed", [])}
    check("F1. 失敗の後に回収済みの行は collected=true・まだの行は false", flags == {"reg_f1": True, "reg_f2": False}, flags)


def main():
    print("🪪 月謝のカード変更リンク 回帰テスト\n")
    test_admin_api()
    test_webhook()
    test_wiring()
    test_cancel_module()
    test_reconcile_guard()
    test_readonly_failed_flag()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}")
        sys.exit(1)
    print("✅ 全て成功")


if __name__ == "__main__":
    main()
