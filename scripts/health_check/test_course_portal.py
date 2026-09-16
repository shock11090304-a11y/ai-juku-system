#!/usr/bin/env python3
"""🎥 月額講座 視聴ページ (course-videos.html / /api/course/* / /api/admin/course/*) の回帰テスト (in-process・一時 SQLite)。
Stripe は _course_fetch_from_stripe を偽物に、メールは _course_send_email を記録器に差し替える (ネットワーク不要)。

  1. ログインリンク: 受講者でないメール → 同じ 200 応答でメールは送らない (列挙対策) / 受講者 → リンク付きメール 1 通
  2. リンクの token を交換 → 30 日セッション。塾生用 API (/api/auth/me) にはこの token で入れない・逆も同じ
  3. /api/course/me: 自分の講座の動画だけ・未来の公開日は出ない・非公開は出ない
  4. 塾長: 動画登録 (URL の各形式から ID 抽出)・登録と同時にその講座の受講者だけへ通知・重複登録は 409・不正 URL は 400
  5. 塾長: 一覧 (講座ごとの有効受講者数)・編集・再通知・削除・受講者一覧
  6. 解約: Stripe が講座なしを返す → 次のアクセスで 401、ログインリンクも送らない
  7. webhook 同期: checkout (course tag) で course_members が作られ students は増えない・視聴ページのログインリンクを自動送信 / subscription.deleted で解約に
  8. 管理 API は admin Bearer 無しで 401
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

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="courseportal_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "sk_test_dummy_for_course_portal", "STRIPE_WEBHOOK_SECRET": "",
        "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "re_dummy", "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_course_portal", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def main():
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    print("🎥 月額講座 視聴ページ 回帰テスト")

    # ---- 偽 Stripe / 偽メール ----
    STRIPE = {"parent@example.invalid": {"courses": ["bunpo", "kaishaku"], "customer_id": "cus_p1", "name": "テスト 花子"}}
    CALLS = []
    def fake_fetch(email, customer_id=""):
        CALLS.append(email)
        if email in STRIPE:
            return dict(STRIPE[email], found=True)
        return {"courses": [], "customer_id": "", "name": "", "found": False}
    mod._course_fetch_from_stripe = fake_fetch
    MAILS = []
    mod._course_send_email = lambda to, subject, body: (MAILS.append({"to": to, "subject": subject, "body": body}) or {"sent": True, "resend_id": "re_x"})
    mod._email_rate_limit = lambda *a, **k: None
    ADMIN = {"Authorization": "Bearer " + admin_token(mod)}

    # ---- 1. ログインリンク ----
    r1 = client.post("/api/course/login/request", json={"email": "nobody@example.invalid"})
    r2 = client.post("/api/course/login/request", json={"email": "Parent@Example.invalid "})
    check("1a. 受講者でないメールも 200 で同じ本文", r1.status_code == 200 and r1.json() == r2.json(), (r1.text, r2.text))
    check("1b. 受講者でないメールには送らない・受講者には 1 通", len(MAILS) == 1 and MAILS[0]["to"] == "parent@example.invalid", MAILS)
    link = [l for l in MAILS[0]["body"].splitlines() if l.startswith("https://example.invalid/course-videos.html?t=")]
    check("1c. 本文に視聴ページのリンク (token 付き)", len(link) == 1, MAILS[0]["body"])
    magic = link[0].split("?t=", 1)[1] if link else ""
    m = mod._course_member_by_email("parent@example.invalid")
    check("1d. course_members に active で登録 (講座はアルファベット順)", m and m["status"] == "active" and m["courses"] == ["bunpo", "kaishaku"] and m["name"] == "テスト 花子", m)
    check("1e. 未知のメールは course_members に行を作らない", mod._course_member_by_email("nobody@example.invalid") is None)
    n0 = CALLS.count("nobody@example.invalid")
    client.post("/api/course/login/request", json={"email": "nobody@example.invalid"})
    check("1f. 未知のメールの再入力は 10 分間 Stripe に聞き直さない (negative cache)", CALLS.count("nobody@example.invalid") == n0, CALLS)

    # ---- 2. token 交換 ----
    bad = client.post("/api/course/login/verify", json={"token": magic + "x"})
    ok = client.post("/api/course/login/verify", json={"token": magic})
    check("2a. 壊れた token は 401・正しい token は session", bad.status_code == 401 and ok.status_code == 200 and ok.json().get("token"), (bad.text, ok.text))
    sess = ok.json()["token"]
    H = {"Authorization": "Bearer " + sess}
    check("2b. 講座セッションで塾生 API には入れない", client.get("/api/auth/me", headers=H).status_code in (401, 403), client.get("/api/auth/me", headers=H).status_code)
    check("2c. ログインリンクの token を session として使えない", client.get("/api/course/me", headers={"Authorization": "Bearer " + magic}).status_code == 401)
    stud_tok = mod._sign_session_token(1)
    check("2d. 塾生セッションで講座 API には入れない", client.get("/api/course/me", headers={"Authorization": "Bearer " + stud_tok}).status_code == 401)
    check("2e. 講座セッションを verify に投げても 401・塾生 magic を verify に投げても 401",
          client.post("/api/course/login/verify", json={"token": sess}).status_code == 401 and client.post("/api/course/login/verify", json={"token": mod._sign_session_token(1, token_type="magic")}).status_code == 401)
    check("2f. coursemagic を塾生の /api/auth/verify に投げても入れない", client.get("/api/auth/verify?t=" + magic).status_code in (400, 401, 403, 404), client.get("/api/auth/verify?t=" + magic).status_code)

    # ---- 3/4. 動画登録と閲覧 ----
    check("8a. 管理 API は Bearer 無しで 401", client.post("/api/admin/course/videos", json={"course_key": "bunpo", "title": "x", "youtube_url": "https://youtu.be/AAAAAAAAAAA"}).status_code == 401)
    codes = [client.get("/api/admin/course/videos", headers=H).status_code, client.get("/api/admin/course/members", headers=H).status_code,
             client.post("/api/admin/course/members/sync", headers=H).status_code, client.delete("/api/admin/course/videos/1", headers=H).status_code,
             client.patch("/api/admin/course/videos/1", headers=H, json={"title": "x"}).status_code, client.post("/api/admin/course/videos/1/notify", headers=H).status_code]
    check("8b. 講座セッションで管理 API は全部 401", all(c == 401 for c in codes), codes)
    today = mod._course_today_jst()
    tomorrow = (datetime.date.fromisoformat(today) + datetime.timedelta(days=1)).isoformat()
    MAILS.clear()
    v1 = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "bunpo", "title": "第1回 時制", "youtube_url": "https://www.youtube.com/watch?v=AAAAAAAAAAA&t=5s", "note": "範囲: 第1章"})
    check("4a. watch?v= 形式から ID 抽出・登録", v1.status_code == 200 and v1.json()["youtube_id"] == "AAAAAAAAAAA", v1.text)
    check("4b. 登録と同時に bunpo 受講者へ通知 1 通 (視聴ページ URL あり・動画 URL なし・件名は【講座】新しい動画: タイトル)",
          v1.json()["notified"] == {"sent": 1, "failed": 0, "recipients": 1} and len(MAILS) == 1 and "course-videos.html" in MAILS[0]["body"] and "youtu" not in MAILS[0]["body"] and MAILS[0]["subject"] == "【英文法講座】新しい動画: 第1回 時制", (v1.json(), MAILS))
    v2 = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "kyotsu", "title": "共テ第1回", "youtube_url": "https://youtu.be/BBBBBBBBBBB?si=abc"})
    check("4c. youtu.be 形式・kyotsu は受講者 0 → 通知 0", v2.status_code == 200 and v2.json()["youtube_id"] == "BBBBBBBBBBB" and v2.json()["notified"]["recipients"] == 0, v2.text)
    v3 = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "kaishaku", "title": "未来の動画", "youtube_url": "CCCCCCCCCCC", "publish_date": tomorrow})
    check("4d. 生 ID・未来の公開日は登録できるが通知しない", v3.status_code == 200 and v3.json()["notified"] is None, v3.text)
    v4 = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "kaishaku", "title": "非公開予定", "youtube_url": "https://www.youtube.com/shorts/DDDDDDDDDDD", "notify": False})
    check("4e. shorts 形式・notify=false は送らない", v4.status_code == 200 and v4.json()["notified"] is None and len(MAILS) == 1, v4.text)
    dup = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "bunpo", "title": "重複", "youtube_url": "https://youtu.be/AAAAAAAAAAA"})
    badurl = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "bunpo", "title": "x", "youtube_url": "https://vimeo.com/123456"})
    badkey = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "math", "title": "x", "youtube_url": "https://youtu.be/AAAAAAAAAAA"})
    check("4f. 重複 409 / 非 YouTube 400 / 不正な講座 400", dup.status_code == 409 and badurl.status_code == 400 and badkey.status_code == 400, (dup.status_code, badurl.status_code, badkey.status_code))
    pid = v4.json()["id"]
    client.patch(f"/api/admin/course/videos/{pid}", headers=ADMIN, json={"is_published": False})

    me = client.get("/api/course/me", headers=H)
    ids = sorted(v["youtube_id"] for v in me.json()["videos"]) if me.status_code == 200 else None
    check("3a. /me は自分の講座 (bunpo, kaishaku) の公開済み・公開日到来分だけ", me.status_code == 200 and ids == ["AAAAAAAAAAA"], (me.status_code, me.text[:300]))
    check("3b. /me に講座名と連絡先", me.status_code == 200 and [c["key"] for c in me.json()["courses"]] == ["bunpo", "kaishaku"] and me.json()["contact"], me.text[:200])

    # ---- 5. 一覧・編集・再通知・削除・受講者一覧 ----
    lst = client.get("/api/admin/course/videos", headers=ADMIN)
    cnt = {c["key"]: c["active_members"] for c in lst.json()["courses"]} if lst.status_code == 200 else {}
    check("5a. 一覧 4 本・講座ごとの有効受講者数", lst.status_code == 200 and len(lst.json()["videos"]) == 4 and cnt == {"kaishaku": 1, "bunpo": 1, "kyotsu": 0}, (lst.status_code, cnt))
    MAILS.clear()
    rn = client.post(f"/api/admin/course/videos/{v1.json()['id']}/notify", headers=ADMIN)
    check("5b. 通知の押し直しは既に受け取った人には送らない (0 通)", rn.status_code == 200 and rn.json()["notified"]["recipients"] == 0 and len(MAILS) == 0, rn.text)
    rn2 = client.post(f"/api/admin/course/videos/{v1.json()['id']}/notify", headers=ADMIN, json={"resend_all": True})
    check("5b2. resend_all=true なら全員にもう一度・notified_count は累計 2", rn2.status_code == 200 and len(MAILS) == 1 and [v for v in client.get("/api/admin/course/videos", headers=ADMIN).json()["videos"] if v["id"] == v1.json()["id"]][0]["notified_count"] == 2, rn2.text)
    # あとから申し込んだ人には「通知」で届く
    mod._course_upsert_member("late@example.invalid", ["bunpo"], "cus_late", "あと 太郎")
    MAILS.clear()
    rn3 = client.post(f"/api/admin/course/videos/{v1.json()['id']}/notify", headers=ADMIN)
    check("5b3. あとから申し込んだ受講者にだけ届く", rn3.json()["notified"]["sent"] == 1 and len(MAILS) == 1 and MAILS[0]["to"] == "late@example.invalid", (rn3.text, MAILS))
    conn = mod.db(); c = conn.cursor(); c.execute("UPDATE course_members SET status = 'canceled', courses = '[]' WHERE email = ?", ("late@example.invalid",)); conn.commit(); conn.close()
    # 16 人以上はバックグラウンド送信
    for i in range(20):
        mod._course_upsert_member(f"bulk{i}@example.invalid", ["kyotsu"], f"cus_b{i}", "")
    MAILS.clear()
    vb = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "kyotsu", "title": "一斉配信テスト", "youtube_url": "https://youtu.be/GGGGGGGGGGG"})
    import time as _t
    for _ in range(50):
        if len(MAILS) >= 20: break
        _t.sleep(0.05)
    check("5b4. 宛先 16 名以上はバックグラウンドで送り queued を返す", vb.status_code == 200 and vb.json()["notified"].get("background") and vb.json()["notified"]["queued"] == 20 and len(MAILS) == 20, (vb.json(), len(MAILS)))
    conn = mod.db(); c = conn.cursor(); c.execute("UPDATE course_members SET status = 'canceled', courses = '[]' WHERE email LIKE 'bulk%'"); c.execute("DELETE FROM course_videos WHERE youtube_id = 'GGGGGGGGGGG'"); conn.commit(); conn.close()
    ed = client.patch(f"/api/admin/course/videos/{v3.json()['id']}", headers=ADMIN, json={"publish_date": today, "title": "第1回 構造"})
    me2 = client.get("/api/course/me", headers=H).json()
    check("5c. 公開日を今日に編集すると /me に出る", ed.status_code == 200 and sorted(v["youtube_id"] for v in me2["videos"]) == ["AAAAAAAAAAA", "CCCCCCCCCCC"], me2)
    de = client.delete(f"/api/admin/course/videos/{v2.json()['id']}", headers=ADMIN)
    check("5d. 削除", de.status_code == 200 and len(client.get("/api/admin/course/videos", headers=ADMIN).json()["videos"]) == 3)
    mem = client.get("/api/admin/course/members", headers=ADMIN)
    active = [m for m in mem.json()["members"] if m["status"] == "active"] if mem.status_code == 200 else []
    check("5e. 受講者一覧に講座名", mem.status_code == 200 and len(active) == 1 and active[0]["course_names"] == ["英文法講座", "英文解釈講座"], mem.text[:300])

    # ---- 7. webhook 同期 (関数を直接) ----
    MAILS.clear()
    mod._course_webhook_touch({"customer_details": {"email": "New@Example.invalid", "name": "新規 太郎"}, "customer": "cus_n1",
                               "metadata": {"system": "juku-payment-course", "combo": "kyotsu"}, "payment_status": "paid"}, "checkout")
    nm = mod._course_member_by_email("new@example.invalid")
    check("7a2. 決済完了で視聴ページのログインリンクを自動送信 (講座名・翌週の月曜・token 付きリンク)",
          len(MAILS) == 1 and MAILS[0]["to"] == "new@example.invalid" and "共通テスト対策講座" in MAILS[0]["body"] and "course-videos.html?t=" in MAILS[0]["body"] and "翌週の月曜" in MAILS[0]["body"], MAILS)
    _lnk = [l for l in MAILS[0]["body"].splitlines() if "course-videos.html?t=" in l][0] if MAILS else ""
    _tok = _lnk.split("?t=", 1)[1] if _lnk else ""
    _vr = client.post("/api/course/login/verify", json={"token": _tok})
    check("7a3. そのリンクの token で視聴ページにログインできる", _vr.status_code == 200 and _vr.json().get("courses") == [{"key": "kyotsu", "name": "共通テスト対策講座"}], _vr.text[:200])
    conn = mod.db(); c = conn.cursor(); c.execute("SELECT COUNT(*) AS n FROM students"); n_students = c.fetchone()["n"]; conn.close()
    check("7a. checkout で course_members に作成・students は増えない", nm and nm["courses"] == ["kyotsu"] and nm["status"] == "active" and n_students == 0, (nm, n_students))
    # 本物の Subscription には customer_email が無い → Customer.retrieve でメールを引く。Stripe が落ちていてもイベント自体で解約が効くこと
    class _FakeCustomers:
        @staticmethod
        def retrieve(cid): return {"id": cid, "email": "New@Example.invalid", "name": "新規 太郎"}
    class _FakeStripe:
        Customer = _FakeCustomers
    _orig_get_stripe = mod.get_stripe
    mod.get_stripe = lambda: _FakeStripe
    mod._course_fetch_from_stripe = lambda email, customer_id="": None   # Stripe 障害中
    sub = {"id": "sub_n1", "customer": "cus_n1", "status": "canceled", "metadata": {"system": "juku-payment-course", "combo": "kyotsu"},
           "items": {"data": [{"price": {"lookup_key": "course_kyotsu_monthly"}}]}}
    mod._course_webhook_touch(sub, "subscription.deleted")
    nm2 = mod._course_member_by_email("new@example.invalid")
    check("7b. subscription.deleted は Stripe が落ちていても canceled にする (Customer.retrieve でメールを引く)", nm2 and nm2["status"] == "canceled" and nm2["courses"] == [], nm2)
    mod._course_fetch_from_stripe = fake_fetch
    mod.get_stripe = _orig_get_stripe   # Webhook.construct_event は本物の stripe ライブラリで検証する
    # 署名付き webhook を通しても同じ経路に入る (juku-payment の skip より前に呼ばれる)
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_course"
    mod.STRIPE_WEBHOOK_SECRET = "whsec_test_course"
    import time as _tm
    payload = json.dumps({"id": "evt_course_1", "object": "event", "api_version": "2024-06-20", "created": int(_tm.time()), "livemode": False,
                          "type": "checkout.session.completed", "data": {"object": {"object": "checkout.session",
        "id": "cs_wh1", "payment_status": "paid", "customer": "cus_w1", "customer_details": {"email": "wh@example.invalid", "name": "ウェブ 太郎"},
        "metadata": {"system": "juku-payment-course", "combo": "bunpo"}}}}).encode()
    ts = int(_tm.time()); sig = hmac.new(b"whsec_test_course", f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    import stripe as _stripe_lib
    _stripe_major = int(str(getattr(_stripe_lib, "VERSION", "0")).split(".")[0] or 0)
    if _stripe_major >= 14:
        # ローカルの stripe 14+ は StripeObject が dict 互換でなく、本体 webhook 全体 (event.get) が動かない (CI は requirements の 11.1.0)
        print(f"  ⏭ 7c. 署名付き checkout webhook: stripe {_stripe_lib.VERSION} ではスキップ (CI の 11.x で実行)")
    else:
      try:
        wr = client.post("/api/stripe/webhook", data=payload, headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"})
        wm = mod._course_member_by_email("wh@example.invalid")
        check("7c. 署名付き checkout webhook → course_members に作成し、応答は juku-payment skip", wr.status_code == 200 and wr.json().get("skipped_reason") == "juku-payment system tag" and wm and wm["courses"] == ["bunpo"], (wr.status_code, wr.text[:200], wm))
        check("7c2. 署名付き checkout webhook でログインリンクのメールが 1 通", any(m["to"] == "wh@example.invalid" and "course-videos.html?t=" in m["body"] for m in MAILS), [m["to"] for m in MAILS])
      except Exception as e:
        check("7c. 署名付き checkout webhook", False, repr(e))

    # ---- 6. 解約後 ----
    STRIPE["parent@example.invalid"] = {"courses": [], "customer_id": "cus_p1", "name": "テスト 花子"}
    conn = mod.db(); c = conn.cursor(); c.execute("UPDATE course_members SET verified_at = ? WHERE email = ?", ("2020-01-01T00:00:00", "parent@example.invalid")); conn.commit(); conn.close()
    gone = client.get("/api/course/me", headers=H)
    MAILS.clear()
    client.post("/api/course/login/request", json={"email": "parent@example.invalid"})
    check("6. 解約後は /me が 401・ログインリンクも送らない", gone.status_code == 401 and len(MAILS) == 0, (gone.status_code, MAILS))
    # Stripe に顧客が見つからない (found=False) が DB に customer_id 付きの行がある → 据え置き (誤って解約にしない)
    STRIPE["parent@example.invalid"] = {"courses": ["bunpo"], "customer_id": "cus_p1", "name": "テスト 花子"}
    mod._course_upsert_member("parent@example.invalid", ["bunpo"], "cus_p1", "テスト 花子")
    mod._course_fetch_from_stripe = lambda email, customer_id="": {"courses": [], "customer_id": "", "name": "", "found": False}
    kept = mod._course_member_refresh("parent@example.invalid", force=True)
    check("6b. Stripe で一時的に見つからなくても customer_id 付きの有効行は据え置く", kept and kept["status"] == "active" and kept["courses"] == ["bunpo"], kept)
    mod._course_fetch_from_stripe = fake_fetch
    # 429: 同じ IP から 6 回目
    for _ in range(6):
        last = client.post("/api/course/login/request", json={"email": f"rl{_}@example.invalid"})
    check("6c. 同一 IP 6 回目のログイン要求は 429", last.status_code == 429, last.status_code)

    # ---- YouTube ID 抽出 ----
    f = mod._course_youtube_id
    check("id. 抽出パターン", f("https://www.youtube.com/embed/EEEEEEEEEEE?rel=0") == "EEEEEEEEEEE" and f("https://youtube.com/live/FFFFFFFFFFF") == "FFFFFFFFFFF" and f("not a url") is None and f("") is None and f("https://youtu.be/short") is None)

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}"); sys.exit(1)
    print("✅ 全件 OK")


if __name__ == "__main__":
    main()
