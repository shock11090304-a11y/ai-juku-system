#!/usr/bin/env python3
"""📱 塾長メッセージ (個別) の LINE 併送 (2026-11-18 塾長「LINE連携済みの子にLINEでも」= AI 担任のアドバイス)。

背景: AI 担任のアドバイスはアプリ内のお知らせだけで、2 日で 68 通のうち 8 通しか読まれなかった。
  LINE 連携済みの子には同じ文面を LINE でも送る。ただし 2026-10-12〜 月の上限で LINE push が全部 429 になったので、
  月の残りが LINE_ADVICE_QUOTA_RESERVE (既定 50) 以下なら LINE は送らない (ログインコードなどのために残す)。

固定する性質 (一時 SQLite・外部通信なし・LINE API は偽物・生徒名とメールは架空 = 公開リポジトリ):
  [1] send_line を付けない (既定) → LINE 0 通・line=None (今までどおり)
  [2] send_line=true・連携済み・残りに余裕 → LINE 1 通 (件名と本文とアプリのリンク)・line='sent'・アプリ内の行は in_app・
      notifications に channel='line' template='admin_message' success=1・send_email=false ならメール 0
  [3] 連携していない → 'not_linked' (LINE 0 通・アプリ内は残る)
  [4] 月の残り ≤ 予備 (50) → 'quota_low' (LINE 0 通)・予備は env で変えられる・上限なしのプランは送る
  [5] LINE が失敗 → 'failed'・アプリ内の行は残る・notifications に success=0
  [6] LINE 未設定 → 'not_configured'
  [7] 一斉送信 (broadcast) に send_line → 400・行を 1 つも作らない
  [8] _line_quota_status: limited 200 / 使用 150 → 残り 50・type none → 残り None・失敗 → None・10 分キャッシュ・
      送れたら キャッシュの残りを 1 減らす
  [9] GET /api/admin/line/quota は管理者だけ (401)・形 {configured, ok, quota, reserve}
  [10] CI (server-tests.yml) に登録

実行:
    python3 scripts/health_check/test_admin_message_line.py
    # exit 0 = PASS / 1 = FAIL
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import io
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="admin_msg_line_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        "DATABASE_URL": "",   # ★空にしないと本番 Postgres を見る
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    os.environ.pop("LINE_ADVICE_QUOTA_RESERVE", None)
    spec = importlib.util.spec_from_file_location("aijuku_main_admin_msg_line", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


_N = [0]


def mk(mod, line_user_id=None):
    _N[0] += 1
    n = _N[0]
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO students (name, email, status, line_user_id) VALUES (?,?,?,?) RETURNING id",
              (f"架空 生徒{n:02d}", f"msg-line-{n:02d}@example.invalid", "paid", line_user_id))
    sid = c.fetchone()["id"]
    conn.commit(); conn.close()
    return sid


def rows(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    r = [dict(x) for x in c.fetchall()]
    conn.close()
    return r


class FakeLine:
    def __init__(self, ok=True):
        self.calls, self.ok = [], ok

    def __call__(self, endpoint, body):
        self.calls.append((endpoint, body))
        return self.ok

    def texts(self):
        return [m.get("text") for _, b in self.calls for m in (b.get("messages") or [])]


def main():
    print("== 塾長メッセージの LINE 併送 ==")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    H = {"Authorization": f"Bearer {admin_token(mod)}"}
    fake = FakeLine()
    mod._line_api_call = fake
    mod.LINE_CHANNEL_ACCESS_TOKEN = "test-token"
    quota = {"val": {"type": "limited", "limit": 5000, "used": 10, "remaining": 4990}}
    mod._line_quota_status = lambda force=False: (dict(quota["val"]) if quota["val"] is not None else None)

    def send(sid, **extra):
        mod._RATE_LIMIT_STORE.clear()
        fake.calls.clear()
        body = {"target": "student", "student_id": sid, "subject": "📘 学習アドバイス",
                "body": "時制の10問を出しました。", "send_email": False, **extra}
        r = client.post("/api/admin/messages/send", json=body, headers=H)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)

    linked = mk(mod, "U" + "a" * 32)
    plain = mk(mod)

    print("[1] 既定は LINE を送らない")
    code, d = send(linked)
    check("send_line なし → 200・LINE 0 通・line=None", code == 200 and not fake.calls and d.get("line") is None, (code, d))

    print("[2] 連携済み・残りに余裕 → LINE でも送る")
    code, d = send(linked, send_line=True)
    t = fake.texts()
    check("line='sent'・LINE 1 通 (push)", code == 200 and d.get("line") == "sent" and len(fake.calls) == 1
          and fake.calls[0][0] == "message/push", (code, d, fake.calls))
    check("LINE の本文に件名・本文・アプリのリンク", t and "📘 学習アドバイス" in t[0] and "時制の10問を出しました。" in t[0]
          and "https://example.invalid/mypage.html" in t[0], t)
    check("send_email=false ならメール 0", d.get("email_attempted") == 0, d)
    m = rows(mod, "SELECT sent_via, email_status FROM messages WHERE recipient_id = ? ORDER BY id DESC LIMIT 1", (linked,))
    check("アプリ内の行は in_app・email_status なし", m and m[0]["sent_via"] == "in_app" and m[0]["email_status"] is None, m)
    nrow = rows(mod, "SELECT channel, template, success FROM notifications WHERE student_id = ? ORDER BY id DESC LIMIT 1", (linked,))
    check("notifications に line / admin_message / success=1", nrow and nrow[0]["channel"] == "line"
          and nrow[0]["template"] == "admin_message" and int(nrow[0]["success"]) == 1, nrow)

    print("[3] 連携していない")
    code, d = send(plain, send_line=True)
    n_msg = rows(mod, "SELECT COUNT(*) AS n FROM messages WHERE recipient_id = ?", (plain,))[0]["n"]
    check("not_linked・LINE 0 通・アプリ内は 1 通", code == 200 and d.get("line") == "not_linked" and not fake.calls and n_msg == 1,
          (code, d, n_msg))

    print("[4] 月の残りが少ない")
    quota["val"] = {"type": "limited", "limit": 200, "used": 150, "remaining": 50}
    code, d = send(linked, send_line=True)
    check("残り 50 (= 予備 50) → quota_low・LINE 0 通", d.get("line") == "quota_low" and not fake.calls, d)
    quota["val"] = {"type": "limited", "limit": 200, "used": 149, "remaining": 51}
    code, d = send(linked, send_line=True)
    check("残り 51 → sent", d.get("line") == "sent" and len(fake.calls) == 1, d)
    os.environ["LINE_ADVICE_QUOTA_RESERVE"] = "60"
    code, d = send(linked, send_line=True)
    check("LINE_ADVICE_QUOTA_RESERVE=60 なら残り 51 でも quota_low", d.get("line") == "quota_low" and not fake.calls, d)
    os.environ["LINE_ADVICE_QUOTA_RESERVE"] = "abc"
    check("読めない値は 50", mod._line_advice_quota_reserve() == 50)
    os.environ.pop("LINE_ADVICE_QUOTA_RESERVE", None)
    quota["val"] = {"type": "none", "limit": None, "used": 9999, "remaining": None}
    code, d = send(linked, send_line=True)
    check("上限なしのプラン → sent", d.get("line") == "sent" and len(fake.calls) == 1, d)
    quota["val"] = None
    code, d = send(linked, send_line=True)
    check("通数が読めない (None) → 送る (sent)", d.get("line") == "sent", d)

    print("[5] LINE が失敗")
    fake.ok = False
    before = rows(mod, "SELECT COUNT(*) AS n FROM messages WHERE recipient_id = ?", (linked,))[0]["n"]
    code, d = send(linked, send_line=True)
    after = rows(mod, "SELECT COUNT(*) AS n FROM messages WHERE recipient_id = ?", (linked,))[0]["n"]
    nrow = rows(mod, "SELECT success FROM notifications WHERE student_id = ? ORDER BY id DESC LIMIT 1", (linked,))
    check("failed・アプリ内は残る・notifications success=0", code == 200 and d.get("line") == "failed" and after == before + 1
          and nrow and int(nrow[0]["success"]) == 0, (code, d, before, after, nrow))
    fake.ok = True

    print("[6] LINE 未設定")
    mod.LINE_CHANNEL_ACCESS_TOKEN = ""
    code, d = send(linked, send_line=True)
    check("not_configured・LINE 0 通", d.get("line") == "not_configured" and not fake.calls, d)
    mod.LINE_CHANNEL_ACCESS_TOKEN = "test-token"

    print("[7] 一斉送信には使えない")
    mod._RATE_LIMIT_STORE.clear()
    n0 = rows(mod, "SELECT COUNT(*) AS n FROM messages")[0]["n"]
    r = client.post("/api/admin/messages/send", json={"target": "broadcast", "broadcast_filter": "all", "body": "x",
                                                      "send_email": False, "send_line": True}, headers=H)
    n1 = rows(mod, "SELECT COUNT(*) AS n FROM messages")[0]["n"]
    check("broadcast + send_line → 400・行を作らない", r.status_code == 400 and n1 == n0, (r.status_code, r.text[:200], n0, n1))

    print("[8] _line_quota_status (偽の LINE API)")
    mod2 = load_main()
    mod2.LINE_CHANNEL_ACCESS_TOKEN = "test-token"
    import urllib.request as _u
    hits = []
    answers = {"message/quota": {"type": "limited", "value": 200}, "message/quota/consumption": {"totalUsage": 150}}

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_open(req, timeout=None):
        ep = req.full_url.split("/v2/bot/", 1)[1]
        hits.append(ep)
        if answers.get("_fail"):
            raise OSError("boom")
        return _Resp(json.dumps(answers[ep]).encode())

    orig = _u.urlopen
    _u.urlopen = fake_open
    try:
        q = mod2._line_quota_status(force=True)
        check("limited 200・使用 150 → 残り 50", q == {"type": "limited", "limit": 200, "used": 150, "remaining": 50}, q)
        n = len(hits)
        mod2._line_quota_status()
        check("10 分以内はキャッシュ (LINE に聞かない)", len(hits) == n, hits)
        answers["message/quota"] = {"type": "none"}
        q = mod2._line_quota_status(force=True)
        check("type none → limit/remaining None", q and q["limit"] is None and q["remaining"] is None, q)
        answers["_fail"] = True
        check("取得失敗 → None", mod2._line_quota_status(force=True) is None)
        answers.pop("_fail")
        answers["message/quota"] = {"type": "limited", "value": 200}
        mod2._line_quota_status(force=True)
        sid = mk(mod2, "U" + "b" * 32)
        mod2._line_api_call = FakeLine()
        st = mod2._admin_message_line_push(sid, "件名", "本文")
        check("送れたらキャッシュの残りを 1 減らす (50 は予備なので quota_low・減らさない)",
              st == "quota_low" and mod2._LINE_QUOTA_CACHE["val"]["remaining"] == 50, (st, mod2._LINE_QUOTA_CACHE))
        answers["message/quota/consumption"] = {"totalUsage": 100}
        mod2._line_quota_status(force=True)
        st = mod2._admin_message_line_push(sid, "件名", "本文")
        check("残り 100 → sent・キャッシュは 99", st == "sent" and mod2._LINE_QUOTA_CACHE["val"]["remaining"] == 99
              and mod2._LINE_QUOTA_CACHE["val"]["used"] == 101, (st, mod2._LINE_QUOTA_CACHE))
    finally:
        _u.urlopen = orig

    print("[9] GET /api/admin/line/quota")
    r = client.get("/api/admin/line/quota")
    check("トークンなし → 401", r.status_code == 401, r.status_code)
    quota["val"] = {"type": "limited", "limit": 200, "used": 20, "remaining": 180}
    r = client.get("/api/admin/line/quota", headers=H)
    j = r.json() if r.status_code == 200 else {}
    check("管理者 → {configured, ok, quota, reserve}", r.status_code == 200 and j.get("configured") is True and j.get("ok") is True
          and j.get("quota", {}).get("remaining") == 180 and j.get("reserve") == 50, (r.status_code, j))

    print("[10] CI に登録")
    yml = open(CI_YML, encoding="utf-8").read()
    check("server-tests.yml で実行する", any(ln.strip() == "python3 scripts/health_check/test_admin_message_line.py"
                                              for ln in yml.splitlines()))

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        return 1
    print("✅ PASS (塾長メッセージの LINE 併送: 個別だけ・連携済みだけ・月の残りを守る)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
