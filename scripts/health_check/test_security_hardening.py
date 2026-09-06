#!/usr/bin/env python3
"""🔐 セキュリティ強化 (2026-09-07) の回帰テスト (in-process・一時 SQLite・本番に触れない)。

システム点検 (3視点レビュー) で確定した「外から攻められる穴」を塞いだ。壊すと元の穴に戻るので契約を固定する。

  1. Stored XSS: 生徒が /api/textbooks/request-generation に入れた topic 等は長さが切られ、
     CEO 画面 (ceo.html) は表示時に escapeHtml を通す (ソース検査)。
  2. X-Forwarded-For: 攻撃者が先頭に任意の値を詰めても、信頼するプロキシが最後に付けた実 IP を採る。
  3. 塾長ログイン: IP を変えながら総当たりしても、IP 非依存の上限 (1 時間) で 429 になる。
     成功したらカウンタは戻る (keychain の連続失敗の救済は従来どおり)。
  4. 管理者トークンの失効: ADMIN_TOKEN_VERSION を変えると既存トークンが全部無効になる。
  5. 週次レポートの preview / send-one は、管理者 Bearer か STATS_TOKEN のどちらかが無ければ通らない
     (STATS_TOKEN 未設定でも Origin ヘッダだけでは通らない = fail-closed)。
  6. 本番 (Postgres) で MAGIC_LINK_SECRET が開発用の既定値なら起動を拒否する (ソース検査)。
  7. /api/news/generate-question に IP レート制限がある (docstring の約束どおり)。

使い方: python3 scripts/health_check/test_security_hardening.py   (CI: server-tests.yml)
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import os
import re
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
CEO_HTML = os.path.join(REPO, "ceo.html")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []
ADMIN_PW = "test-admin-password-please-change"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="sec_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        "DATABASE_URL": "",          # ★空にしないと本番 Postgres に書く
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "ADMIN_PASSWORD": ADMIN_PW,
        "STATS_TOKEN": "",           # 未設定でも fail-closed であることを見る
        "ADMIN_TOKEN_VERSION": "",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_sec", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    payload = mod._admin_token_payload(str(exp))
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def student_token(mod, sid, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def make_student(mod, name, email):
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat()
    c.execute("INSERT INTO students (name, email, status, plan, trial_end, course, grade) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (name, email, "paid", "founder_special", far, "kokuritsu_nankan", "高校3年"))
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


class _Req:
    """_client_ip 用の最小 request スタブ。"""
    def __init__(self, headers, host="10.0.0.1"):
        self.headers = headers
        self.client = type("C", (), {"host": host})()


def main():
    print("🔐 セキュリティ強化 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    src = open(MAIN_PY, encoding="utf-8").read()
    ceo = open(CEO_HTML, encoding="utf-8").read()
    sid = make_student(mod, "Student S", "student-s@example.org")
    tok_s = {"Authorization": "Bearer " + student_token(mod, sid)}
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    mod._RATE_LIMIT_STORE.clear()

    # ------------------------------------------------ 1. Stored XSS
    print("1) 教材リクエストの topic: 長さ制限 + CEO 画面のエスケープ")
    evil = "<img src=x onerror=alert(1)>" + "A" * 400
    r = client.post("/api/textbooks/request-generation", json={"subject": "english", "topic": evil, "level": "x" * 300, "type": "t" * 300}, headers=tok_s)
    check("生徒がリクエストを投稿できる (200)", r.status_code == 200, r.text)
    d = client.get("/api/admin/textbooks/missing-requests?hours=1", headers=adm).json()
    items = d.get("items") or []
    check("塾長一覧に載る", len(items) == 1, d)
    if items:
        check("topic は 100 文字で切られる", len(items[0]["topic"]) <= 100, len(items[0]["topic"]))
        check("level/type は 40 文字で切られる", len(items[0]["level"]) <= 40 and len(items[0]["type"]) <= 40, (len(items[0]["level"]), len(items[0]["type"])))
    fn = ceo[ceo.index("function loadTextbookMissingRequests"):]
    fn = fn[:fn.index("\n    }\n")]
    for v in ("item.subject", "item.topic", "item.level", "item.type"):
        check(f"ceo.html は {v} を escapeHtml で囲む", f"escapeHtml({v})" in fn and not re.search(r"\$\{" + re.escape(v) + r"\}", fn), v)

    # ------------------------------------------------ 2. X-Forwarded-For
    print("2) X-Forwarded-For の解釈 (信頼するプロキシが最後に付けた IP)")
    check("XFF 'spoofed, real' → real", mod._client_ip(_Req({"x-forwarded-for": "9.9.9.9, 203.0.113.5"})) == "203.0.113.5")
    check("XFF 'a, b, real' → real", mod._client_ip(_Req({"x-forwarded-for": "9.9.9.9, 8.8.8.8, 203.0.113.5"})) == "203.0.113.5")
    check("XFF 単独 → その値", mod._client_ip(_Req({"x-forwarded-for": "203.0.113.5"})) == "203.0.113.5")
    check("XFF 無し → 接続元", mod._client_ip(_Req({}, host="198.51.100.7")) == "198.51.100.7")
    check("64 文字で切る", len(mod._client_ip(_Req({"x-forwarded-for": "x" * 500}))) <= 64)
    check("重複していた独自パーサが残っていない", src.count('xff.split(",")[0]') == 0 and 'or "?").split(",")[0]' not in src)

    # ------------------------------------------------ 3. 塾長ログインの総当たり
    print("3) 塾長ログイン: IP を変えても IP 非依存の上限で止まる")
    mod._RATE_LIMIT_STORE.clear()
    codes = []
    for i in range(45):
        r = client.post("/api/admin/login", json={"password": "wrong"}, headers={"x-forwarded-for": f"9.9.{i // 250}.{i % 250}, 203.0.113.{i % 200}"})
        codes.append(r.status_code)
    check("最初は 401 (パスワード不一致)", codes[0] == 401, codes[:3])
    check("IP を変え続けても 45 回以内に 429 になる", 429 in codes, codes)
    first_429 = codes.index(429) if 429 in codes else None
    check("上限は 40 回前後 (keychain の誤入力を救える緩さ)", first_429 is not None and 35 <= first_429 <= 41, first_429)
    # 🔐 2026-09-07 DB 基準の全体上限: in-memory をクリア (= 再起動/デプロイ相当) しても 1 時間は止まったまま
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/login", json={"password": ADMIN_PW}, headers={"x-forwarded-for": "9.9.9.9, 203.0.113.250"})
    check("再起動相当 (メモリのカウンタ消去) 後も、直近 1 時間の失敗 40 回で 429", r.status_code == 429, f"{r.status_code} {r.text[:120]}")
    conn = mod.db(); c = conn.cursor(); c.execute("DELETE FROM events WHERE name = 'admin_login_failed'"); conn.commit(); conn.close()
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/login", json={"password": ADMIN_PW})
    check("正しいパスワードで 200 + token", r.status_code == 200 and r.json().get("token"), r.text)
    tok = r.json().get("token")
    check("発行トークンで /api/admin/verify が通る", client.get("/api/admin/verify", headers={"Authorization": "Bearer " + tok}).status_code == 200)

    # ------------------------------------------------ 4. トークン失効 (ADMIN_TOKEN_VERSION)
    print("4) ADMIN_TOKEN_VERSION による一括失効")
    old = mod.ADMIN_TOKEN_VERSION
    try:
        mod.ADMIN_TOKEN_VERSION = "2"
        check("version を変えると既存トークンは無効", client.get("/api/admin/verify", headers={"Authorization": "Bearer " + tok}).status_code == 401)
        r = client.post("/api/admin/login", json={"password": ADMIN_PW})
        tok2 = r.json().get("token")
        check("再ログインした新トークンは有効", tok2 and client.get("/api/admin/verify", headers={"Authorization": "Bearer " + tok2}).status_code == 200)
        check("新トークンも 3 パート形式のまま (ceo.html の exp 解析互換)", len(base64.urlsafe_b64decode(tok2 + "=" * (-len(tok2) % 4)).decode().split(".")) == 3)
    finally:
        mod.ADMIN_TOKEN_VERSION = old

    # ------------------------------------------------ 5. 週次レポート preview / send-one
    print("5) 週次レポート preview / send-one は管理者 Bearer か STATS_TOKEN が必須 (fail-closed)")
    mod._RATE_LIMIT_STORE.clear()
    origin = {"Origin": "https://trillion-ai-juku.com"}
    for path in ("/api/weekly-reports/preview", "/api/weekly-reports/send-one"):
        r = client.post(path, json={"student_id": sid}, headers=origin)
        check(f"{path}: Origin だけでは通らない", r.status_code in (401, 403), f"{r.status_code} {r.text[:100]}")
        r = client.post(path, json={"student_id": sid}, headers={**origin, "x-stats-token": "anything"})
        check(f"{path}: STATS_TOKEN 未設定時はトークン付きでも通らない", r.status_code in (401, 403), f"{r.status_code}")
        # send-one は実際にメール/LINE を送る経路なので、存在しない生徒 ID で「認証は通って 404」を見る
        target = sid if path.endswith("/preview") else 999999
        r = client.post(path, json={"student_id": target}, headers={**origin, **adm})
        check(f"{path}: 管理者 Bearer なら認証は通る", r.status_code not in (401, 403), f"{r.status_code} {r.text[:120]}")
    old_st = mod.STATS_TOKEN
    try:
        mod.STATS_TOKEN = "stats-secret-for-test"
        r = client.post("/api/weekly-reports/preview", json={"student_id": sid}, headers={**origin, "x-stats-token": "stats-secret-for-test"})
        check("STATS_TOKEN 設定時は一致するトークンで通る", r.status_code not in (401, 403), r.status_code)
        r = client.post("/api/weekly-reports/preview", json={"student_id": sid}, headers={**origin, "x-stats-token": "wrong"})
        check("不一致のトークンは通らない", r.status_code in (401, 403), r.status_code)
    finally:
        mod.STATS_TOKEN = old_st

    # ------------------------------------------------ 6. 開発用既定鍵で本番起動しない (ソース検査)
    print("6) 本番で開発用の既定鍵なら起動を拒否する")
    blk = src[src.index('if MAGIC_LINK_SECRET == "dev-secret-DO-NOT-USE-IN-PROD":'):][:900]
    check("dev 鍵の分岐に SystemExit がある", "raise SystemExit" in blk, blk[:200])
    check("この検査は USE_POSTGRES 配下 (テスト/SQLite では起動する)", "if USE_POSTGRES:" in src[src.index('if MAGIC_LINK_SECRET == "dev-secret-DO-NOT-USE-IN-PROD":') - 400:src.index('if MAGIC_LINK_SECRET == "dev-secret-DO-NOT-USE-IN-PROD":')])

    # ------------------------------------------------ 7. news の IP レート制限
    print("7) /api/news/generate-question の IP レート制限")
    mod._RATE_LIMIT_STORE.clear()
    key = ("testclient", "news_generate")
    mod._RATE_LIMIT_STORE[key] = [time.time()] * 10
    r = client.post("/api/news/generate-question", json={"feed": "cnn"})
    check("上限到達後は 429 (AI を呼ばない)", r.status_code == 429, f"{r.status_code} {r.text[:100]}")

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
