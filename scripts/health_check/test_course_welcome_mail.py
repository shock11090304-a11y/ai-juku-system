#!/usr/bin/env python3
"""📧 月額講座 (Stripe 支払いリンク・metadata.system=juku-payment-course) の決済完了 → 受講案内メール自動送信
(api/stripe-webhook.py::_handle_course_checkout, 2026-09-16) の回帰テスト。ネットワーク不要・KV と Resend は偽物。

  1. 決済済み (paid) の講座セッション → Resend に 1 通。宛先=決済メール、件名に講座名、本文に 生徒氏名/月額合計/受付番号/次の月曜
     → KV course:welcome:<session> が status=sent、index に載る
  2. 同じセッションが再度届く (Stripe 再送・別 event.id) → 2 通目は送らない (SET NX ガード)
  3. payment_status=unpaid → 送らない・KV にも書かない
  4. system が juku-payment-course でない (空 / juku-payment-monthly) → 講座の処理に入らない
  5. RESEND_API_KEY 未設定 → 例外にせず KV に status=no_api_key
  6. metadata.combo が無い → 明細の price.lookup_key から講座を復元
  7. COURSE_NOTIFY_EMAIL 設定時 → 塾長にも 1 通 (合計 2 通)、案内メール失敗時は件名に「未送信」・本文に「送信失敗」
  8. 次の月曜の計算 (JST): 月曜当日は翌週、日曜は翌日 (UTC で計算すると別の日になる時刻で検査)
  9. KV が落ちている (_redis_safe → None) → それでも送る (Resend の Idempotency-Key 付き)
 10. 前回が "sending" のまま 10 分以上 → やり直す / 10 分未満 → 送らない
 11. livemode=false (テストモードの決済) → 送らない
 12. checkout.session.async_payment_succeeded (カード以外の入金確定) → 講座のセッションなら同じ処理
 13. combo が "bunpo kaishaku" (旧版の URL エンコード漏れ) でも講座名を復元
 14. クーポン適用 (total_details.amount_discount>0) → 本文が「今回のお支払いは」に切り替わる
 15. テンプレートに壊れた波括弧があっても例外にせず status=failed
 16. COURSE_WELCOME_ENABLED=0 → 講座の案内メールだけ止まる (塾長通知は「未送信」で届く)
 17. payment_status=no_payment_required (100% クーポン) → 送る
 18. 講座の毎月の更新・失敗・解約イベントは月謝の台帳 (pay:*/sub:canceled) に書かない
"""
import importlib.util
import io
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEBHOOK = os.path.join(REPO, "api", "stripe-webhook.py")
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load():
    os.environ.update({"KV_REST_API_URL": "", "KV_REST_API_TOKEN": "", "STRIPE_SECRET_KEY": "sk_test_dummy",
                       "RESEND_API_KEY": "re_test", "FROM_EMAIL": "noreply@example.invalid",
                       "COURSE_DELIVERY_START": "2026-09-01"})   # 8a/8b は「翌週の月曜」の計算だけを見る (配信開始日の切り上げは 8c で見る)
    os.environ.pop("COURSE_NOTIFY_EMAIL", None)
    spec = importlib.util.spec_from_file_location("stripe_webhook_vercel", WEBHOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeKV:
    """Upstash REST の SET (NX/EX) / GET / ZADD を最小限に真似る"""
    def __init__(self):
        self.store, self.zsets = {}, {}

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
        if cmd == "ZADD":
            self.zsets.setdefault(args[1], []).append(args[3])
            return {"result": 1}
        return {"result": None}


class FakeResend:
    """urllib.request.urlopen を差し替えて Resend への POST を記録する。fail_first=True で 1 通目だけ HTTP エラー"""
    def __init__(self, fail_first=False):
        self.sent, self.fail_first, self.calls, self.headers = [], fail_first, 0, []

    def __call__(self, req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "api.resend.com" not in url:
            raise AssertionError("unexpected network call: " + url)
        self.calls += 1
        self.headers.append(dict(req.header_items()))
        if self.fail_first and self.calls == 1:
            raise urllib.error.HTTPError(url, 500, "boom", {}, io.BytesIO(b"{}"))
        self.sent.append(json.loads(req.data.decode("utf-8")))
        return io.BytesIO(json.dumps({"id": f"re_{len(self.sent)}"}).encode())


def session(sid="cs_test_abc123", paid=True, combo="bunpo+kaishaku", system="juku-payment-course", email="parent@example.invalid"):
    md = {"system": system} if system else {}
    if combo is not None:
        md["combo"] = combo
    return {
        "id": sid, "object": "checkout.session", "mode": "subscription",
        "payment_status": "paid" if paid else "unpaid", "amount_total": 3000, "currency": "jpy",
        "customer": "cus_test1", "subscription": "sub_test1", "customer_email": None,
        "customer_details": {"email": email, "name": "テスト 花子"},
        "custom_fields": [{"key": "student_name", "type": "text", "label": {"type": "custom", "custom": "生徒氏名"}, "text": {"value": "テスト 太郎"}}],
        "client_reference_id": "course-bunpo_kaishaku-sub-ABC123",
        "created": 1789000000,  # 2026-09-10 (木) 09:26 JST
        "metadata": md,
    }


def event(obj, eid="evt_1"):
    return {"id": eid, "type": "checkout.session.completed", "data": {"object": obj}}


def main():
    mod = load()
    print("📧 月額講座 受講案内メール 回帰テスト")

    # ---- 1. 正常系 ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._handle_checkout_completed(event(session()))
    check("1a. Resend に 1 通", len(rs.sent) == 1, rs.sent)
    m = rs.sent[0] if rs.sent else {}
    check("1b. 宛先=決済メール", m.get("to") == ["parent@example.invalid"], m.get("to"))
    check("1c. 件名は「受講のご案内（講座名）」(アルファベット順で 英文法・英文解釈)", m.get("subject", "") == "【トリリオン英語塾】受講のご案内（英文法講座・英文解釈講座）", m.get("subject"))
    body = m.get("text", "")
    check("1d. 宛名は「生徒 さん・保護者様」", body.startswith("テスト 太郎 さん・保護者様"), body[:60])
    check("1d2. From に塾名", m.get("from") == "トリリオン英語塾 <noreply@example.invalid>", m.get("from"))
    check("1e. 本文に月額合計 3,000円 (通常文)", "月額合計 3,000円（税込）を、毎月同じ日に" in body)
    check("1e2. 本文に受講確定", "受講確定" in body)
    check("1f. 本文に受付番号", "cs_test_abc123" in body)
    _exp = mod._course_first_monday_jst()
    check("1g. 初回配信は処理時刻 (=決済直後) の次の月曜", ("初回の配信は %s の予定" % _exp) in body, body[:400])
    check("1g2. Resend に Idempotency-Key", any(v == "course-welcome/cs_test_abc123" for v in rs.headers[0].values()) if rs.headers else False, rs.headers)
    check("1h. reply_to は窓口メール", m.get("reply_to") == "info@trillion-ai-juku.com", m.get("reply_to"))
    check("1h2. Resend への送信に User-Agent (Cloudflare 1010 対策・2026-09-17)", any(k.lower() == "user-agent" and v.startswith("ai-juku/") for k, v in (rs.headers[0] if rs.headers else {}).items()), rs.headers[:1])
    rec = json.loads(kv.store.get("course:welcome:cs_test_abc123") or "{}")
    check("1i. KV に status=sent と講座コード・セッション作成時刻", rec.get("status") == "sent" and rec.get("courses") == ["bunpo", "kaishaku"] and rec.get("session_created") == 1789000000, rec)
    check("1j. index に session が載る", "cs_test_abc123" in kv.zsets.get("course:welcome:index", []))

    # ---- 2. 再送 (別 event.id・同じ session) ----
    mod._handle_checkout_completed(event(session(), eid="evt_2"))
    check("2. 同じセッションの再送では 2 通目を送らない", len(rs.sent) == 1, len(rs.sent))

    # ---- 3. unpaid ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._handle_checkout_completed(event(session(sid="cs_unpaid", paid=False)))
    check("3. unpaid は送らない・KV にも書かない", len(rs.sent) == 0 and not kv.store, (rs.sent, kv.store))

    # ---- 4. 講座以外 ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._handle_checkout_completed(event(session(sid="cs_other", system="")))
    mod._handle_checkout_completed(event(session(sid="cs_ai", system="ai-juku")))
    check("4a. system 空 / 他システムは講座の処理に入らない", len(rs.sent) == 0 and not kv.store, (rs.sent, kv.store))
    calls = []
    orig_get = mod._stripe_get
    mod._stripe_get = lambda *a, **k: calls.append(a) or None
    mod._handle_checkout_completed(event({**session(sid="cs_monthly", system="juku-payment-monthly", combo=None), "mode": "setup", "setup_intent": "seti_1", "metadata": {"system": "juku-payment-monthly", "registration_id": "reg_1"}}))
    mod._stripe_get = orig_get
    check("4b. juku-payment-monthly は従来どおり月謝の処理 (メールなし・SetupIntent 取得)", len(rs.sent) == 0 and any("setup_intents/seti_1" in str(c) for c in calls), (rs.sent, calls))

    # ---- 5. RESEND_API_KEY なし ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    os.environ["RESEND_API_KEY"] = ""
    mod._handle_checkout_completed(event(session(sid="cs_nokey")))
    rec = json.loads(kv.store.get("course:welcome:cs_nokey") or "{}")
    check("5. API キー無しは例外にせず status=no_api_key", len(rs.sent) == 0 and rec.get("status") == "no_api_key", rec)
    os.environ["RESEND_API_KEY"] = "re_test"

    # ---- 6. combo 無し → 明細から復元 ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._stripe_get = lambda key, path: {"data": [{"price": {"lookup_key": "course_kyotsu_monthly"}}, {"price": {"lookup_key": "course_kaishaku_monthly"}}]} if "line_items" in path else None
    mod._handle_checkout_completed(event(session(sid="cs_nocombo", combo=None)))
    mod._stripe_get = orig_get
    check("6. combo 無しでも明細 (lookup_key) から講座名を復元", rs.sent and "英文解釈講座・共通テスト対策講座" in rs.sent[0]["subject"], rs.sent and rs.sent[0]["subject"])

    # ---- 7. 塾長通知 ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    os.environ["COURSE_NOTIFY_EMAIL"] = "owner@example.invalid"
    mod._handle_checkout_completed(event(session(sid="cs_notify")))
    check("7a. 通知先設定時は 2 通 (受講生 + 塾長)", len(rs.sent) == 2 and rs.sent[1]["to"] == ["owner@example.invalid"], [x.get("to") for x in rs.sent])
    n = rs.sent[1]["text"] if len(rs.sent) == 2 else ""
    check("7b. 塾長通知に生徒名・講座・受付番号・申込ID・決済日・サブスク・送信済み",
          all(x in n for x in ["テスト 太郎", "英文法講座", "cs_notify", "申込ID", "ABC123", "毎月 %d日" % mod._course_jst().day, "sub_test1", mod._course_first_monday_jst(), "送信済み"]), n)
    kv, rs = FakeKV(), FakeResend(fail_first=True)
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._handle_checkout_completed(event(session(sid="cs_fail")))
    rec = json.loads(kv.store.get("course:welcome:cs_fail") or "{}")
    check("7c. Resend 失敗は例外にせず KV に status=failed", rec.get("status") == "failed" and rec.get("error"), rec)
    check("7d. 失敗時の塾長通知は件名に「未送信」・本文に「送信失敗」", len(rs.sent) == 1 and "未送信" in rs.sent[0]["subject"] and "送信失敗" in rs.sent[0]["text"], rs.sent)
    check("7e. 「sending」のまま index に載る (途中で時間切れでも一覧で見える)", "cs_fail" in kv.zsets.get("course:welcome:index", []))
    os.environ.pop("COURSE_NOTIFY_EMAIL", None)

    # ---- 8. 次の月曜 (JST) ----
    import datetime as dt
    jst = dt.timezone(dt.timedelta(hours=9))
    mon = dt.datetime(2026, 9, 14, 8, 0, tzinfo=jst)   # 月曜 08:00 JST = 日曜 23:00 UTC (UTC で計算すると 9/14 になる)
    check("8a. 月曜 08:00 JST → 翌週の月曜 (UTC で計算すると当日になってしまう時刻)", mod._course_first_monday_jst(mon.timestamp()) == "9月21日（月）", mod._course_first_monday_jst(mon.timestamp()))
    sun = dt.datetime(2026, 9, 20, 8, 0, tzinfo=jst)   # 日曜 08:00 JST = 土曜 23:00 UTC
    check("8b. 日曜 08:00 JST → 翌日の月曜", mod._course_first_monday_jst(sun.timestamp()) == "9月21日（月）", mod._course_first_monday_jst(sun.timestamp()))
    os.environ["COURSE_DELIVERY_START"] = "2026-10-05"
    check("8c. 配信開始日 (10/5) より前の決済は初回配信が 10月5日（月）・補足は「10月からの配信開始のため」",
          mod._course_first_monday_jst(mon.timestamp()) == "10月5日（月）" and "10月からの配信開始のため" in mod._course_first_note(mon.timestamp()), (mod._course_first_monday_jst(mon.timestamp()), mod._course_first_note(mon.timestamp())))
    oct = dt.datetime(2026, 10, 7, 10, 0, tzinfo=jst)   # 水曜
    check("8d. 配信開始後の決済は翌週の月曜 (10/12)・補足は「翌週の月曜から」", mod._course_first_monday_jst(oct.timestamp()) == "10月12日（月）" and "翌週の月曜" in mod._course_first_note(oct.timestamp()), (mod._course_first_monday_jst(oct.timestamp()), mod._course_first_note(oct.timestamp())))
    os.environ["COURSE_DELIVERY_START"] = "2026-09-01"

    # ---- 9. KV 停止中でも送る ----
    rs = FakeResend()
    mod._redis_safe, urllib.request.urlopen = (lambda *a: None), rs
    mod._handle_checkout_completed(event(session(sid="cs_kvdown")))
    check("9. KV が落ちていても送る (Idempotency-Key 付き)", len(rs.sent) == 1 and any("course-welcome/cs_kvdown" in str(h) for h in rs.headers), (rs.sent, rs.headers))

    # ---- 10. sending のまま放置 ----
    import time as _t
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    kv.store["course:welcome:cs_stale"] = json.dumps({"status": "sending", "at": int(_t.time()) - 900})
    mod._handle_checkout_completed(event(session(sid="cs_stale")))
    check("10a. 10 分以上 sending のまま → やり直して送る", len(rs.sent) == 1 and json.loads(kv.store["course:welcome:cs_stale"]).get("status") == "sent", (rs.sent, kv.store))
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    kv.store["course:welcome:cs_fresh"] = json.dumps({"status": "sending", "at": int(_t.time()) - 30})
    mod._handle_checkout_completed(event(session(sid="cs_fresh")))
    check("10b. 送信中 (30 秒前) の再送は送らない", len(rs.sent) == 0, rs.sent)

    # ---- 11. テストモード ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._handle_checkout_completed(event({**session(sid="cs_testmode"), "livemode": False}))
    check("11. livemode=false は送らない", len(rs.sent) == 0 and not kv.store, (rs.sent, kv.store))

    # ---- 12. async_payment_succeeded ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    ev = {"id": "evt_async", "type": "checkout.session.async_payment_succeeded", "data": {"object": session(sid="cs_async")}}
    mod.HANDLERS["checkout.session.async_payment_succeeded"](ev)
    ev2 = {"id": "evt_async2", "type": "checkout.session.async_payment_succeeded", "data": {"object": session(sid="cs_async_other", system="juku-payment-monthly")}}
    mod.HANDLERS["checkout.session.async_payment_succeeded"](ev2)
    check("12. async_payment_succeeded は講座のセッションだけ送る", len(rs.sent) == 1 and rs.sent[0]["text"].find("cs_async") > 0, rs.sent)

    # ---- 13. combo に空白 ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._handle_checkout_completed(event(session(sid="cs_space", combo="bunpo kaishaku")))
    check("13. combo の空白は + とみなす", rs.sent and "英文法講座・英文解釈講座" in rs.sent[0]["subject"], rs.sent and rs.sent[0]["subject"])

    # ---- 14. クーポン ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._handle_checkout_completed(event({**session(sid="cs_coupon"), "amount_total": 1500, "total_details": {"amount_discount": 1500}}))
    check("14. 割引ありは「今回のお支払いは」の文", rs.sent and "今回のお支払いは 1,500円" in rs.sent[0]["text"] and "月額合計 1,500円（税込）を、毎月" not in rs.sent[0]["text"], rs.sent and rs.sent[0]["text"][:600])

    # ---- 16. 講座だけ止める切替 ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    os.environ["COURSE_WELCOME_ENABLED"] = "0"; os.environ["COURSE_NOTIFY_EMAIL"] = "owner@example.invalid"
    mod._handle_checkout_completed(event(session(sid="cs_disabled")))
    rec = json.loads(kv.store.get("course:welcome:cs_disabled") or "{}")
    check("16. COURSE_WELCOME_ENABLED=0 は案内メールを送らず status=disabled、塾長通知は「未送信」で届く",
          rec.get("status") == "disabled" and len(rs.sent) == 1 and rs.sent[0]["to"] == ["owner@example.invalid"] and "未送信" in rs.sent[0]["subject"], (rec, rs.sent))
    os.environ.pop("COURSE_WELCOME_ENABLED", None); os.environ.pop("COURSE_NOTIFY_EMAIL", None)

    # ---- 17. no_payment_required (100% クーポン) は送る ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    mod._handle_checkout_completed(event({**session(sid="cs_free"), "payment_status": "no_payment_required", "amount_total": 0}))
    check("17. no_payment_required は送る (今回のお支払いは 0円 の文)", len(rs.sent) == 1 and "今回のお支払いは 0円" in rs.sent[0]["text"], rs.sent)

    # ---- 18. 毎月の更新・失敗・解約は月謝の台帳に書かない ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    inv = {"id": "in_1", "customer": "cus_test1", "subscription": "sub_test1", "amount_paid": 1500, "amount_due": 1500,
           "metadata": {}, "subscription_details": {"metadata": {"system": "juku-payment-course"}}}
    mod._handle_payment_succeeded({"id": "e1", "type": "invoice.payment_succeeded", "data": {"object": inv}})
    mod._handle_payment_failed({"id": "e2", "type": "invoice.payment_failed", "data": {"object": inv}})
    mod._handle_subscription_deleted({"id": "e3", "type": "customer.subscription.deleted", "data": {"object": {"id": "sub_test1", "customer": "cus_test1", "metadata": {"system": "juku-payment-course"}}}})
    check("18. 講座の invoice/subscription イベントは KV に何も書かない", not kv.store and not kv.zsets, (kv.store, kv.zsets))

    # ---- 15. テンプレート破損 ----
    kv, rs = FakeKV(), FakeResend()
    mod._redis_safe, urllib.request.urlopen = kv, rs
    orig_body = mod.COURSE_WELCOME_BODY
    mod.COURSE_WELCOME_BODY = orig_body + "\n{typo}"
    try:
        mod._handle_checkout_completed(event(session(sid="cs_typo")))
    finally:
        mod.COURSE_WELCOME_BODY = orig_body
    rec = json.loads(kv.store.get("course:welcome:cs_typo") or "{}")
    check("15. 壊れた差し込みは例外にせず status=failed (KeyError)", len(rs.sent) == 0 and rec.get("status") == "failed" and "KeyError" in rec.get("error", ""), rec)

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}"); sys.exit(1)
    print("✅ 全件 OK")


if __name__ == "__main__":
    main()
