#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サブスク申込まわり (exam-app/api/{checkout,stripe-webhook,portal}.py) のゲート。

    python3 scripts/book_exam/check_signup.py      # 引数なし = 全部検査

偽の Stripe / 偽の Supabase を 127.0.0.1 に立て、**本物のハンドラを本物の HTTP で**
叩いて往復を検査する (check_import_books.py と同じ流儀)。見るのは:

  - 申込 (checkout): ban 付きアカウント作成 / 体験の有無 / 既契約の拒否 /
    ★他人のメールを入れてもパスワードを乗っ取れないこと / Host 制限 / 入力検査
  - webhook: 署名検証 (不正署名で副作用ゼロ) / ban⇄解除 / 行の upsert /
    AI塾のイベントの素通り / 解約後の遅延再送で復活しないこと / 失敗時 500 (再送要求)
  - portal: トークンの本人確認 / 無契約 404
  - 静的整合: signup.html の学年 = checkout.py の GRADE_OPTIONS / 価格・体験日数の
    表示が signup.html と legal.html で一致 / 秘密鍵がリポジトリに無いこと

★ 落ちたら sys.exit(1)。違反を印字して 0 で終わる状態 (INCONSISTENT) を作らない。
"""
import hashlib
import hmac
import importlib.util
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API_DIR = os.path.join(ROOT, "exam-app", "api")

SERVICE_KEY = "service_gate_key"
STRIPE_KEY = "sk_test_gate"
WEBHOOK_SECRET = "whsec_gate"
PRICE_ID = "price_gate_1250"

failures = []
checked = 0


def ok(label):
    global checked
    checked += 1
    print(f"  [ok] {label}")


def bad(label, detail=""):
    global checked
    checked += 1
    failures.append(label)
    print(f"  [NG] {label}" + (f" — {detail}" if detail else ""))


def expect(cond, label, detail=""):
    if cond:
        ok(label)
    else:
        bad(label, detail)


# =============================================================================
# 偽サーバ
# =============================================================================
class FakeState:
    def __init__(self):
        self.users = {}          # id -> {id,email,password,banned_until,user_metadata}
        self.rows = {}           # user_id -> subscriptions 行
        self.stripe_calls = []   # (path, form dict)
        self.sb_calls = []       # (method, path, body)
        self.fail_next_upsert = False
        self.seq = 0

    def new_id(self):
        # ★数字だけの区切りにすると check_no_pii.py の電話番号検出に誤爆するので hex 文字にする
        self.seq += 1
        return f"deadbeef-cafe-4abc-8def-{self.seq:012d}"


STATE = FakeState()


class FakeStripe(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        if self.headers.get("Authorization") != f"Bearer {STRIPE_KEY}":
            self._send(401, {"error": {"message": "bad key"}})
            return
        length = int(self.headers.get("Content-Length") or 0)
        form = dict(urllib.parse.parse_qsl(self.rfile.read(length).decode()))
        path = self.path
        STATE.stripe_calls.append((path, form))
        if path == "/v1/checkout/sessions":
            self._send(200, {"id": "cs_gate_1", "url": "https://checkout.stripe.test/cs_gate_1"})
        elif path == "/v1/billing_portal/sessions":
            self._send(200, {"id": "bps_gate_1", "url": "https://billing.stripe.test/bps_gate_1"})
        else:
            self._send(404, {"error": {"message": f"unknown {path}"}})

    def _send(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FakeSupabase(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # --- 小道具 ---------------------------------------------------------------
    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw.decode()) if raw else None
        except Exception:
            return None

    def _send(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _service_ok(self):
        return self.headers.get("apikey") == SERVICE_KEY

    def _user_json(self, u):
        out = {k: v for k, v in u.items() if k != "password"}
        return out

    # --- ルーティング ----------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = dict(urllib.parse.parse_qsl(parsed.query))
        STATE.sb_calls.append(("GET", self.path, None))
        if not self._service_ok():
            self._send(401, {"message": "no apikey"})
            return
        if parsed.path == "/auth/v1/admin/users":
            users = [self._user_json(u) for u in STATE.users.values()]
            page = int(qs.get("page", 1))
            per = int(qs.get("per_page", 50))
            self._send(200, {"users": users[(page - 1) * per: page * per]})
        elif parsed.path == "/auth/v1/user":
            token = (self.headers.get("Authorization") or "")[len("Bearer "):]
            hit = [u for u in STATE.users.values() if u.get("token") == token]
            if hit:
                self._send(200, self._user_json(hit[0]))
            else:
                self._send(401, {"message": "invalid token"})
        elif parsed.path == "/rest/v1/subscriptions":
            m = re.match(r"eq\.(.+)", qs.get("user_id", ""))
            uid = m.group(1) if m else ""
            row = STATE.rows.get(uid)
            self._send(200, [row] if row else [])
        else:
            self._send(404, {"message": f"unknown GET {parsed.path}"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        body = self._body()
        STATE.sb_calls.append(("POST", self.path, body))
        if not self._service_ok():
            self._send(401, {"message": "no apikey"})
            return
        if parsed.path == "/auth/v1/admin/users":
            email = (body or {}).get("email", "")
            if any(u["email"] == email for u in STATE.users.values()):
                self._send(422, {"message": "email exists"})
                return
            uid = STATE.new_id()
            STATE.users[uid] = {
                "id": uid, "email": email,
                "password": (body or {}).get("password", ""),
                "banned_until": ("2100-01-01T00:00:00Z"
                                 if (body or {}).get("ban_duration") else ""),
                "ban_duration_given": (body or {}).get("ban_duration", ""),
                "email_confirm_given": bool((body or {}).get("email_confirm")),
                "user_metadata": (body or {}).get("user_metadata", {}),
            }
            self._send(200, self._user_json(STATE.users[uid]))
        elif parsed.path == "/auth/v1/token":
            email = (body or {}).get("email", "")
            password = (body or {}).get("password", "")
            hit = [u for u in STATE.users.values()
                   if u["email"] == email and u["password"] == password]
            if hit:
                self._send(200, {"access_token": "tok_ok"})
            else:
                self._send(400, {"error": "invalid_grant"})
        elif parsed.path == "/rest/v1/subscriptions":
            if STATE.fail_next_upsert:
                STATE.fail_next_upsert = False
                self._send(500, {"message": "boom (gate-injected)"})
                return
            rows = body if isinstance(body, list) else [body]
            fields = rows[0]
            # ★ 本物の Postgres と同じ厳しさ: upsert の INSERT 側は既存行の更新でも
            #   NOT NULL (default 無し) の email を要求する。省くと 400。
            #   (これを緩くしていたせいで production の 400 を見逃した 2026-08-16)
            if "email" not in fields:
                self._send(400, {"code": "23502",
                                 "message": "null value in column \"email\" violates not-null constraint"})
                return
            uid = fields.get("user_id", "")
            merged = dict(STATE.rows.get(uid) or {})
            merged.update(fields)
            STATE.rows[uid] = merged
            self._send(201, [merged])
        else:
            self._send(404, {"message": f"unknown POST {parsed.path}"})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        body = self._body()
        STATE.sb_calls.append(("PUT", self.path, body))
        if not self._service_ok():
            self._send(401, {"message": "no apikey"})
            return
        m = re.match(r"/auth/v1/admin/users/(.+)$", parsed.path)
        if m and m.group(1) in STATE.users:
            u = STATE.users[m.group(1)]
            if "password" in (body or {}):
                u["password"] = body["password"]
            if "user_metadata" in (body or {}):
                u["user_metadata"] = body["user_metadata"]
            if "ban_duration" in (body or {}):
                u["banned_until"] = ("" if body["ban_duration"] == "none"
                                     else "2100-01-01T00:00:00Z")
            self._send(200, self._user_json(u))
        else:
            self._send(404, {"message": "no such user"})


# =============================================================================
# 本物のハンドラを立てる
# =============================================================================
def load_module(fname, alias):
    path = os.path.join(API_DIR, fname)
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.handler.log_message = lambda self, *a: None
    return mod


def serve(handler_cls):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def post(port, path, payload=None, headers=None, raw=None):
    data = raw if raw is not None else (json.dumps(payload).encode() if payload is not None else b"")
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data,
                                 headers=headers or {"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}


def sign(payload: bytes, secret=WEBHOOK_SECRET, ts=None):
    t = int(ts if ts is not None else time.time())
    mac = hmac.new(secret.encode(), f"{t}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={t},v1={mac}"


def stripe_count():
    return len(STATE.stripe_calls)


def sb_write_count():
    return len([c for c in STATE.sb_calls if c[0] in ("POST", "PUT")])


VALID = {"email": "shin@example.test", "password": "himitsu-8moji", "name": "新規 太郎",
         "grade": "高校3年", "school": "テスト高校"}


# =============================================================================
def run_checkout_tests(port):
    print("--- 申込 (checkout) ---")
    # S1: 新規申込 → ban 付き作成 + 体験つきセッション
    st, body = post(port, "/api/checkout", dict(VALID))
    expect(st == 200 and body.get("checkoutUrl", "").startswith("https://checkout.stripe.test/"),
           "S1 新規申込で決済URLが返る", f"HTTP {st} {body}")
    made = [u for u in STATE.users.values() if u["email"] == VALID["email"]]
    expect(len(made) == 1 and made[0]["ban_duration_given"] == "87600h"
           and made[0]["email_confirm_given"] is True,
           "S1 アカウントが ban 付き (87600h)・確認済みで作られた",
           f"{made!r}"[:200])
    expect(made and made[0]["user_metadata"].get("school") == "テスト高校",
           "S1 学校名がアカウントに記録された")
    sess = [f for p, f in STATE.stripe_calls if p == "/v1/checkout/sessions"]
    f = sess[-1] if sess else {}
    expect(f.get("mode") == "subscription" and f.get("line_items[0][price]") == PRICE_ID,
           "S1 セッションが subscription モード + 正しい Price")
    expect(f.get("subscription_data[trial_period_days]") == "3",
           "S1 初回は 3 日間の無料体験つき")
    expect(f.get("metadata[system]") == "kamitest-subscription"
           and f.get("subscription_data[metadata][supabase_user_id]") == (made[0]["id"] if made else ""),
           "S1 metadata に system と supabase_user_id が入る")
    expect(f.get("customer_email") == VALID["email"] and "customer" not in f,
           "S1 新規は customer_email で作る")
    uid_s1 = made[0]["id"] if made else ""

    # S2: 解約済み (ban 中 + 行あり) の再申込 → 体験なし・Customer 再利用・パスワード再設定
    STATE.rows[uid_s1] = {"user_id": uid_s1, "status": "canceled",
                          "stripe_customer_id": "cus_gate_9", "stripe_subscription_id": "sub_old"}
    st, body = post(port, "/api/checkout", {**VALID, "password": "atarashii-pass9"})
    sess = [f for p, f in STATE.stripe_calls if p == "/v1/checkout/sessions"]
    f = sess[-1] if sess else {}
    expect(st == 200 and "subscription_data[trial_period_days]" not in f,
           "S2 再申込には無料体験が付かない", f"HTTP {st} form={f}")
    expect(f.get("customer") == "cus_gate_9" and "customer_email" not in f,
           "S2 前回の Stripe Customer を再利用する")
    expect(STATE.users[uid_s1]["password"] == "atarashii-pass9",
           "S2 ban 中の再申込は新しいパスワードに置き換わる")

    # S3: 有効な契約がある → 409 で断り、Stripe を呼ばない
    STATE.rows[uid_s1]["status"] = "active"
    before = stripe_count()
    st, body = post(port, "/api/checkout", dict(VALID))
    expect(st == 409 and body.get("error") == "ALREADY_SUBSCRIBED",
           "S3 契約中の再申込は 409 で断る", f"HTTP {st} {body}")
    expect(stripe_count() == before, "S3 そのとき Stripe は呼ばれない")
    del STATE.rows[uid_s1]

    # S4: 生きたアカウント (先生発行) のメールで申込 → パスワードが合わないと進めない
    manual_id = STATE.new_id()
    STATE.users[manual_id] = {"id": manual_id, "email": "jukusei@example.test",
                              "password": "sensei-hakko-1", "banned_until": "",
                              "ban_duration_given": "", "email_confirm_given": True,
                              "user_metadata": {}}
    st, body = post(port, "/api/checkout",
                    {**VALID, "email": "jukusei@example.test", "password": "nusumitori-8"})
    expect(st == 401 and body.get("error") == "PASSWORD_MISMATCH",
           "S4 他人のメール + 違うパスワードでは乗っ取れない (401)", f"HTTP {st} {body}")
    expect(STATE.users[manual_id]["password"] == "sensei-hakko-1",
           "S4 そのときパスワードは書き換わっていない")
    st, body = post(port, "/api/checkout",
                    {**VALID, "email": "jukusei@example.test", "password": "sensei-hakko-1"})
    expect(st == 200, "S4 本人 (パスワード一致) なら申込に進める", f"HTTP {st} {body}")

    # S5: 入力検査 → 400 で、外部を一切呼ばない
    before_s, before_w = stripe_count(), sb_write_count()
    for broken, why in [({**VALID, "password": "mijikai"}, "短いパスワード"),
                        ({**VALID, "grade": "大学4年"}, "無い学年"),
                        ({**VALID, "school": ""}, "学校名なし"),
                        ({**VALID, "email": "kowareta"}, "壊れたメール")]:
        st, body = post(port, "/api/checkout", broken)
        expect(st == 400, f"S5 {why} は 400", f"HTTP {st}")
    expect(stripe_count() == before_s and sb_write_count() == before_w,
           "S5 400 のとき外部への書き込みはゼロ")

    # S6: 許可していない Host からの申込は 403
    os.environ["EXAM_SIGNUP_HOSTS"] = "only.example.com"
    st, body = post(port, "/api/checkout", dict(VALID))
    expect(st == 403 and body.get("error") == "HOST_NOT_ALLOWED",
           "S6 許可していないドメインからは申し込めない (403)", f"HTTP {st}")
    os.environ["EXAM_SIGNUP_HOSTS"] = "127.0.0.1"

    # S7: 鍵の env が無ければ 503 (準備中) で、アカウントを作らない
    saved = os.environ.pop("STRIPE_SECRET_KEY")
    before_users = len(STATE.users)
    st, body = post(port, "/api/checkout", {**VALID, "email": "mada@example.test"})
    expect(st == 503 and body.get("error") == "NOT_CONFIGURED",
           "S7 env 未設定なら 503 (準備中)", f"HTTP {st}")
    expect(len(STATE.users) == before_users, "S7 そのときアカウントは作られない")
    os.environ["STRIPE_SECRET_KEY"] = saved


def run_webhook_tests(port):
    print("--- webhook ---")
    uid = STATE.new_id()
    STATE.users[uid] = {"id": uid, "email": "kounyu@example.test", "password": "x" * 8,
                        "banned_until": "2100-01-01T00:00:00Z", "ban_duration_given": "87600h",
                        "email_confirm_given": True, "user_metadata": {}}
    meta = {"system": "kamitest-subscription", "supabase_user_id": uid,
            "email": "kounyu@example.test", "student_name": "gate-w-student",
            "grade": "高校2年", "school": "ゲート高校"}

    # W1: checkout.session.completed → 行が出来て ban が解除される
    ev = {"id": "evt_1", "type": "checkout.session.completed",
          "data": {"object": {"id": "cs_1", "customer": "cus_w1", "subscription": "sub_w1",
                              "customer_details": {"email": "kounyu@example.test"},
                              "metadata": meta}}}
    raw = json.dumps(ev).encode()
    st, body = post(port, "/api/stripe-webhook", raw=raw,
                    headers={"Content-Type": "application/json", "Stripe-Signature": sign(raw)})
    row = STATE.rows.get(uid) or {}
    expect(st == 200 and row.get("stripe_subscription_id") == "sub_w1"
           and row.get("school") == "ゲート高校",
           "W1 支払い完了で契約行が出来る", f"HTTP {st} row={row}")
    expect(STATE.users[uid]["banned_until"] == "", "W1 支払い完了で ban が解除される")

    # W2: subscription.updated (期末が items の中にある新しい形) → status と期末が入る
    ev = {"id": "evt_2", "type": "customer.subscription.updated",
          "data": {"object": {"id": "sub_w1", "status": "trialing", "customer": "cus_w1",
                              "metadata": meta,
                              "items": {"data": [{"current_period_end": 1790000000}]}}}}
    raw = json.dumps(ev).encode()
    st, _ = post(port, "/api/stripe-webhook", raw=raw,
                 headers={"Content-Type": "application/json", "Stripe-Signature": sign(raw)})
    row = STATE.rows.get(uid) or {}
    expect(st == 200 and row.get("status") == "trialing"
           and str(row.get("current_period_end", "")).startswith("20"),
           "W2 状態と期末が行に入る (items の中の期末も読める)", f"row={row}")

    # W3: subscription.deleted → canceled + ban
    ev = {"id": "evt_3", "type": "customer.subscription.deleted",
          "data": {"object": {"id": "sub_w1", "status": "canceled", "customer": "cus_w1",
                              "metadata": meta, "current_period_end": 1790000000}}}
    raw = json.dumps(ev).encode()
    st, _ = post(port, "/api/stripe-webhook", raw=raw,
                 headers={"Content-Type": "application/json", "Stripe-Signature": sign(raw)})
    row = STATE.rows.get(uid) or {}
    expect(st == 200 and row.get("status") == "canceled",
           "W3 解約イベントで行が canceled になる", f"row={row}")
    expect(STATE.users[uid]["banned_until"] != "", "W3 解約でログインできなくなる (ban)")

    # W4: 解約後に古い active イベントが再送されても復活しない
    ev = {"id": "evt_2b", "type": "customer.subscription.updated",
          "data": {"object": {"id": "sub_w1", "status": "active", "customer": "cus_w1",
                              "metadata": meta, "current_period_end": 1790000000}}}
    raw = json.dumps(ev).encode()
    st, _ = post(port, "/api/stripe-webhook", raw=raw,
                 headers={"Content-Type": "application/json", "Stripe-Signature": sign(raw)})
    row = STATE.rows.get(uid) or {}
    expect(st == 200 and row.get("status") == "canceled" and STATE.users[uid]["banned_until"] != "",
           "W4 解約済み契約は遅延再送イベントで復活しない", f"row={row}")

    # W5: 署名が壊れていたら 401 で副作用ゼロ
    before_w = sb_write_count()
    raw = json.dumps({"id": "evt_x", "type": "checkout.session.completed",
                      "data": {"object": {"metadata": meta}}}).encode()
    st, _ = post(port, "/api/stripe-webhook", raw=raw,
                 headers={"Content-Type": "application/json",
                          "Stripe-Signature": sign(raw, secret="whsec_nise")})
    expect(st == 401, "W5 不正署名は 401", f"HTTP {st}")
    expect(sb_write_count() == before_w, "W5 不正署名で副作用ゼロ")

    # W6: AI塾 (月謝) のイベントは素通り
    before_w = sb_write_count()
    ev = {"id": "evt_juku", "type": "customer.subscription.deleted",
          "data": {"object": {"id": "sub_juku", "metadata": {"system": "juku-payment-monthly"}}}}
    raw = json.dumps(ev).encode()
    st, _ = post(port, "/api/stripe-webhook", raw=raw,
                 headers={"Content-Type": "application/json", "Stripe-Signature": sign(raw)})
    expect(st == 200 and sb_write_count() == before_w,
           "W6 AI塾のイベントは処理せず 200 で流す")

    # W7: 途中で Supabase が落ちたら 500 (Stripe に再送させる)
    uid2 = STATE.new_id()
    STATE.users[uid2] = {"id": uid2, "email": "w7@example.test", "password": "x" * 8,
                         "banned_until": "2100-01-01T00:00:00Z", "ban_duration_given": "87600h",
                         "email_confirm_given": True, "user_metadata": {}}
    STATE.fail_next_upsert = True
    ev = {"id": "evt_7", "type": "checkout.session.completed",
          "data": {"object": {"id": "cs_7", "customer": "cus_7", "subscription": "sub_7",
                              "metadata": {**meta, "supabase_user_id": uid2}}}}
    raw = json.dumps(ev).encode()
    st, _ = post(port, "/api/stripe-webhook", raw=raw,
                 headers={"Content-Type": "application/json", "Stripe-Signature": sign(raw)})
    expect(st == 500, "W7 保存に失敗したら 500 (握り潰さず Stripe に再送させる)", f"HTTP {st}")


def run_portal_tests(port):
    print("--- 契約管理 (portal) ---")
    uid = STATE.new_id()
    STATE.users[uid] = {"id": uid, "email": "p1@example.test", "password": "x" * 8,
                        "banned_until": "", "ban_duration_given": "",
                        "email_confirm_given": True, "user_metadata": {}, "token": "tok_p1"}
    STATE.rows[uid] = {"user_id": uid, "status": "active", "stripe_customer_id": "cus_p1"}

    st, body = post(port, "/api/portal", raw=b"",
                    headers={"Authorization": "Bearer tok_p1"})
    expect(st == 200 and body.get("portalUrl", "").startswith("https://billing.stripe.test/"),
           "P1 契約者はポータルURLをもらえる", f"HTTP {st} {body}")
    calls = [f for p, f in STATE.stripe_calls if p == "/v1/billing_portal/sessions"]
    expect(calls and calls[-1].get("customer") == "cus_p1",
           "P1 自分の Stripe Customer でポータルを開く")

    st, body = post(port, "/api/portal", raw=b"",
                    headers={"Authorization": "Bearer tok_nise"})
    expect(st == 401, "P2 偽トークンは 401", f"HTTP {st}")

    uid2 = STATE.new_id()
    STATE.users[uid2] = {"id": uid2, "email": "free@example.test", "password": "x" * 8,
                         "banned_until": "", "ban_duration_given": "",
                         "email_confirm_given": True, "user_metadata": {}, "token": "tok_free"}
    st, body = post(port, "/api/portal", raw=b"",
                    headers={"Authorization": "Bearer tok_free"})
    expect(st == 404 and body.get("error") == "NO_SUBSCRIPTION",
           "P3 無料アカウント (行なし) は 404", f"HTTP {st}")


def run_static_tests(checkout_mod):
    print("--- 静的整合 ---")
    signup = open(os.path.join(ROOT, "exam-app", "signup.html"), encoding="utf-8").read()
    legal = open(os.path.join(ROOT, "exam-app", "legal.html"), encoding="utf-8").read()

    # 学年の選択肢が checkout.py と一致するか
    opts = re.findall(r"<option>([^<]+)</option>", signup)
    expect(tuple(opts) == tuple(checkout_mod.GRADE_OPTIONS),
           "学年の選択肢が signup.html と checkout.py で一致",
           f"html={opts} py={list(checkout_mod.GRADE_OPTIONS)}")

    # 価格と体験日数の表示が両ページにあるか (Stripe 側の Price は §22 の手順で人が確認)
    for name, page in (("signup.html", signup), ("legal.html", legal)):
        expect("1,250円" in page, f"{name} に月額 1,250円 の表示がある")
        expect("3日間" in page, f"{name} に 3日間無料体験 の表示がある")
    expect(checkout_mod.TRIAL_DAYS == 3, "checkout.py の体験日数も 3 日")

    # 秘密鍵がリポジトリに書かれていないか (env でしか持たない約束)
    secret_re = re.compile(r"sk_live_[A-Za-z0-9]{8,}|sk_test_[A-Za-z0-9]{8,}"
                           r"|whsec_[A-Za-z0-9]{8,}|sb_secret_[A-Za-z0-9]{8,}")
    dirty = []
    scan = []
    for base, _dirs, files in os.walk(os.path.join(ROOT, "exam-app")):
        if "vendor" in base:
            continue
        for fn in files:
            if fn.endswith((".py", ".mjs", ".html", ".json")):
                scan.append(os.path.join(base, fn))
    for path in scan:
        text = open(path, encoding="utf-8", errors="replace").read()
        if secret_re.search(text):
            dirty.append(os.path.relpath(path, ROOT))
    expect(not dirty, f"exam-app に Stripe/Supabase の秘密鍵が書かれていない ({len(scan)} ファイル走査)",
           f"{dirty}")

    # ログイン画面の申込リンクが「自塾のみ」でガードされているか
    ebh = open(os.path.join(ROOT, "exam-app", "exam-book.html"), encoding="utf-8").read()
    ebm = open(os.path.join(ROOT, "exam-app", "exam-book.mjs"), encoding="utf-8").read()
    expect('id="signup-links" hidden' in ebh,
           "申込リンクは既定で hidden (他塾ドメインに出さない)")
    expect("SUPABASE.name === 'trillion'" in ebm and "#signup-links" in ebm,
           "exam-book.mjs が trillion のときだけ申込リンクを出す")

    # account.html: hidden 属性が display:flex の作者スタイルに負けない保険があるか
    # (実測 2026-08-16: ログインフォームと契約カードが両方表示された)
    account = open(os.path.join(ROOT, "exam-app", "account.html"), encoding="utf-8").read()
    expect("[hidden]" in account and "!important" in account,
           "account.html に [hidden] を必ず効かせる CSS がある")

    # AI塾側 (api/stripe-webhook.py) が神テストの請求書を月謝の台帳に混ぜないか。
    # invoice の metadata は空が普通なので subscription_details 側も見る必要がある。
    # payment_failed だけ見て succeeded を見ない「片対称」に戻ったら赤 (2026-08-16 の穴)。
    juku_wh = open(os.path.join(ROOT, "api", "stripe-webhook.py"), encoding="utf-8").read()
    for fn in ("_handle_payment_failed", "_handle_payment_succeeded"):
        m = re.search(rf"def {fn}\(.*?(?=\ndef )", juku_wh, re.S)
        body = m.group(0) if m else ""
        expect("subscription_details" in body,
               f"AI塾 webhook {fn} が subscription 側 metadata でも見分ける (混入防止)")


# =============================================================================
def main():
    print("=== サブスク申込ゲート (checkout / webhook / portal) ===")
    for req in ("checkout.py", "stripe-webhook.py", "portal.py"):
        if not os.path.exists(os.path.join(API_DIR, req)):
            print(f"✗ exam-app/api/{req} が無い")
            return 1

    stripe_srv, stripe_port = serve(FakeStripe)
    sb_srv, sb_port = serve(FakeSupabase)

    os.environ.update({
        "STRIPE_SECRET_KEY": STRIPE_KEY,
        "STRIPE_PRICE_ID": PRICE_ID,
        "STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET,
        "STRIPE_API_BASE": f"http://127.0.0.1:{stripe_port}",
        "SUPABASE_URL": f"http://127.0.0.1:{sb_port}",
        "SUPABASE_SERVICE_ROLE_KEY": SERVICE_KEY,
        "EXAM_SIGNUP_HOSTS": "127.0.0.1",
        "PUBLIC_BASE_URL": "https://exam.trillion-ai-juku.com",
    })

    checkout = load_module("checkout.py", "gate_checkout")
    webhook = load_module("stripe-webhook.py", "gate_webhook")
    portal = load_module("portal.py", "gate_portal")
    co_srv, co_port = serve(checkout.handler)
    wh_srv, wh_port = serve(webhook.handler)
    po_srv, po_port = serve(portal.handler)

    try:
        run_checkout_tests(co_port)
        run_webhook_tests(wh_port)
        run_portal_tests(po_port)
        run_static_tests(checkout)
    finally:
        for srv in (stripe_srv, sb_srv, co_srv, wh_srv, po_srv):
            srv.shutdown()

    print()
    if failures:
        print(f"=== FAIL ({len(failures)} / {checked} 件) ===")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print(f"=== ALL PASS ({checked} 件) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
