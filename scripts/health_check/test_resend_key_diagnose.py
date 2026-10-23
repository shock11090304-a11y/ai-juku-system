#!/usr/bin/env python3
"""📨 メール診断が Resend の送信専用キーを「無効」と出さないことの回帰テスト (2026-10-23)。

背景: 2026-10-23 に RESEND_API_KEY を送信専用キー (Sending access) に入れ替えたあと、CEO 画面の「🩺 メール診断」が
「❌ 無効 — HTTP 401: API key が revoke 済みまたは無効」と出し、「📨 テスト送信 (自分宛)」ボタンも消えた (実送信は正常)。
コードは 403 = 送信専用・401 = 無効と見ていたが、Resend の実際の応答は逆 (公式の errors 一覧と偽キーで実測):
  送信専用キー                 = 401 restricted_api_key「This API key is restricted to only send emails.」
  存在しない・削除済みのキー   = 400 validation_error「API key is invalid」
  有効でないキー               = 403 restricted_api_key「API key is not active」  ← 名前が同じでも送信専用ではない
  停止中のキー                 = 403 suspended_api_key (対処は Resend サポートへの問い合わせ)
  キー以外の失敗               = 429 rate_limit_exceeded (チーム共有の毎秒上限)・5xx・タイムアウト → 判定できず (無効とは言わない)
ここで固定するのは「キーの状態は応答本文の name と status の組で決める」「決められないときは決めない」こと。

  A. _resend_key_http_error の判定
  B. POST /api/admin/email/diagnose: api_key_valid (true/false/null) / api_key_scope / api_key_note / api_key_error / domain_status。
     /domains と /api-keys の 2 本の答えが食い違う (片方だけ 429) ときも矛盾した結果にしない
  C. GET /api/email/diagnose-public: 同じ判定 (公開側も同じ誤りがあった)
  D. ceo.html: B の本物の応答を画面のハンドラ (本物のコード) に通して描く。送信専用キー・判定できないときもテスト送信ボタンを出す・
     ドメインを読めなかっただけで DNS の手順を出さない・ログイン切れを「無効」と描かない・直近エラーの student_id をエスケープする

実行:
    python3 scripts/health_check/test_resend_key_diagnose.py
    # exit 0 = PASS / 1 = FAIL。★JS エンジン (node / osascript / jsc) が無ければ FAIL (飛ばさない)。AJ_JS_ENGINE で選べる

外部通信は一切しない (urllib.request.urlopen を差し替える)。DB は一時 SQLite。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc"

FAILURES = []
FROM_DOMAIN = "example.com"   # RFC 2606 の文書用ドメイン

# Resend の応答 (公式の errors 一覧の status / name / message そのまま)
SEND_ONLY = (401, {"statusCode": 401, "name": "restricted_api_key", "message": "This API key is restricted to only send emails."})
INVALID = (400, {"statusCode": 400, "name": "validation_error", "message": "API key is invalid"})
NOT_ACTIVE = (403, {"statusCode": 403, "name": "restricted_api_key", "message": "API key is not active"})
SUSPENDED = (403, {"statusCode": 403, "name": "suspended_api_key", "message": "This API key is suspended"})
RATE = (429, {"statusCode": 429, "name": "rate_limit_exceeded", "message": "Too many requests."})
BAD_GATEWAY = (502, None)   # 本文が JSON でない
TIMEOUT = ("timeout", None)
DOMAINS_OK = (200, {"data": [{"name": FROM_DOMAIN, "status": "verified", "created_at": "2026-01-01"}]})
DOMAINS_FAILED = (200, {"data": [{"name": FROM_DOMAIN, "status": "failed", "created_at": "2026-01-01"}]})
KEYS_OK = (200, {"data": []})
XSS = '<img src=x onerror=alert(1)>'


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def http_error(url, status, body):
    raw = json.dumps(body).encode() if body is not None else b"<html>Bad Gateway</html>"
    return urllib.error.HTTPError(url, status, "err", {}, io.BytesIO(raw))


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="resenddiag_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_resenddiag", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


class FakeResp:
    def __init__(self, body):
        self._b = json.dumps(body).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeResend:
    """urllib.request.urlopen の差し替え。/domains・/api-keys ごとに (status, body) を返す。呼ばれた URL を残す"""
    def __init__(self):
        self.answers, self.calls = {}, []

    def set(self, domains, api_keys):
        self.answers = {"/domains": domains, "/api-keys": api_keys}
        self.calls = []

    def __call__(self, req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        self.calls.append((getattr(req, "method", None) or "GET", url))
        for suffix, ans in self.answers.items():
            if url.endswith(suffix):
                status, body = ans
                if status == 200:
                    return FakeResp(body)
                if status == "timeout":
                    raise urllib.error.URLError("timed out")
                raise http_error(url, status, body)
        raise AssertionError(f"想定外の外部通信: {url}")


def js_engine():
    want = os.environ.get("AJ_JS_ENGINE", "").strip()
    cands = {
        "node": ["node"] if shutil.which("node") else None,
        "osascript": ["osascript", "-l", "JavaScript"] if shutil.which("osascript") else None,
        "jsc": [JSC] if os.path.exists(JSC) else None,
    }
    if want:
        return cands.get(want)
    for k in ("node", "osascript", "jsc"):
        if cands[k]:
            return cands[k]
    return None


def diag_handler_body(html):
    """ceo.html の「🩺 メール診断」ハンドラの、応答を受け取ってから描き終えるまで (本物のコード)"""
    i = html.index("🩺 「メール診断」ボタン")
    a = html.index("const d = await r.json();", i) + len("const d = await r.json();")
    b = html.index("resultDiv.innerHTML = html;", a)
    return html[a:b]


def run_render(engine, body, cases):
    """cases = [(名前, 応答 JSON, r.ok)] を本物の描画コードに通し、{名前: html または "THROW:..."} を返す"""
    prog = r"""
function lineEsc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]; }); }
var document = { getElementById: function () { return null; } };
var setTimeout = function () {};
function render(d, r) {
""" + body + r"""
  return html;
}
var CASES = """ + json.dumps(cases, ensure_ascii=False) + r""";
var out = {};
for (var i = 0; i < CASES.length; i++) {
  try { out[CASES[i][0]] = render(CASES[i][1], { ok: CASES[i][2], status: CASES[i][2] ? 200 : 401 }); }
  catch (e) { out[CASES[i][0]] = 'THROW:' + e.message; }
}
var s = 'RESULT ' + JSON.stringify(out);
if (typeof console !== 'undefined' && console.log) console.log(s); else print(s);
"""
    with tempfile.TemporaryDirectory(prefix="resenddiag_js_") as td:
        path = os.path.join(td, "render.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(prog)
        r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=120)
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    line = [l for l in text.split("\n") if l.startswith("RESULT ")]
    if r.returncode != 0 or not line:
        check(f"画面のコードが最後まで走った (exit {r.returncode})", False, text[-1500:])
        return {}
    return json.loads(line[-1][len("RESULT "):])


def main():
    print("📨 Resend 送信専用キーの診断 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    mod.RESEND_API_KEY = "re_test_dummy_not_a_real_key"
    mod.FROM_EMAIL = f"AIコーチング <noreply@{FROM_DOMAIN}>"
    fake = FakeResend()
    urllib.request.urlopen = fake
    hdr = {"Authorization": f"Bearer {admin_token(mod)}"}
    responses = {}

    def admin_diag(name=None):
        r = client.post("/api/admin/email/diagnose", headers=hdr)
        assert r.status_code == 200, r.text
        d = r.json()
        if name:
            responses[name] = d
        return d

    def public_diag():
        mod._RATE_LIMIT_STORE.clear()   # 公開側は 1 分 5 回まで
        r = client.get("/api/email/diagnose-public")
        assert r.status_code == 200, r.text
        return r.json()

    # ---------------------------------------------------------------- A
    print("A. _resend_key_http_error の判定")
    f = mod._resend_key_http_error
    k = f(http_error("u", *SEND_ONLY))
    check("401 restricted_api_key = 送信専用 (有効)", k["scope"] == "send_only" and k["valid"] is True, k)
    k = f(http_error("u", 403, {"name": "restricted_api_key", "message": "This API key is restricted to only send emails."}))
    check("status が 403 に変わっても「only send」なら送信専用", k["scope"] == "send_only" and k["valid"] is True, k)
    k = f(http_error("u", *INVALID))
    check("400 validation_error「API key is invalid」= 無効", k["scope"] == "invalid" and k["valid"] is False, k)
    k = f(http_error("u", 401, INVALID[1]))
    check("401 validation_error (送信の経路の形) = 無効", k["scope"] == "invalid" and k["valid"] is False, k)
    k = f(http_error("u", *NOT_ACTIVE))
    check("★403 restricted_api_key「not active」は送信専用ではなく無効", k["scope"] == "invalid" and k["valid"] is False, k)
    k = f(http_error("u", 401, NOT_ACTIVE[1]))
    check("401 でも「not active」なら無効 (送信専用と決めない)", k["scope"] == "invalid" and k["valid"] is False, k)
    k = f(http_error("u", *SUSPENDED))
    check("403 suspended_api_key = 無効", k["scope"] == "invalid" and k["valid"] is False, k)
    k = f(http_error("u", 403, {"name": "invalid_api_key", "message": "Invalid API key"}))
    check("403 invalid_api_key (SDK の型にある名前) = 無効", k["scope"] == "invalid" and k["valid"] is False, k)
    k = f(http_error("u", 401, {"statusCode": 401, "name": "missing_api_key", "message": "Missing API Key"}))
    check("401 missing_api_key = 無効", k["scope"] == "invalid" and k["valid"] is False, k)
    k = f(http_error("u", *RATE))
    check("★429 はキーの状態を決めない (scope も valid も None)", k["scope"] is None and k["valid"] is None and k["code"] == 429, k)
    check("429 の label = 「HTTP 429 rate_limit_exceeded」", k["label"] == "HTTP 429 rate_limit_exceeded", k["label"])
    k = f(http_error("u", *BAD_GATEWAY))
    check("本文が JSON でない 502 も決めない・本文を message に残す・label に余分な空白なし",
          k["scope"] is None and k["valid"] is None and "Bad Gateway" in k["message"] and k["label"] == "HTTP 502", k)
    k = f(http_error("u", 401, None))
    check("★本文が name を持たない 401 を送信専用とも無効とも決めない", k["scope"] is None, k)
    k = f(urllib.error.HTTPError("u", 401, "err", {}, None))
    check("本文を読めない HTTPError (fp なし) でも落ちずに決めない", k["scope"] is None and k["message"] == "", k)

    # ---------------------------------------------------------------- B
    print("\nB. POST /api/admin/email/diagnose")
    fake.set(domains=SEND_ONLY, api_keys=SEND_ONLY)
    d = admin_diag("send_only")
    check("送信専用キー: api_key_valid = true", d.get("api_key_valid") is True, d)
    check("送信専用キー: api_key_scope = send_only", d.get("api_key_scope") == "send_only", d)
    check("送信専用キー: api_key_error を出さない (エラーではない)", not d.get("api_key_error"), d.get("api_key_error"))
    check("送信専用キー: api_key_note でテスト送信を案内", "テスト送信" in (d.get("api_key_note") or ""), d.get("api_key_note"))
    check("送信専用キー: domain_status は send_only_key で始まる (CEO 画面がこれで灰色にする)",
          str(d.get("domain_status") or "").startswith("send_only_key"), d.get("domain_status"))
    check("送信専用キー: 修復案で Full access を勧めない", "Full access に上げる" not in (d.get("domain_status_remediation") or ""),
          d.get("domain_status_remediation"))
    check("診断は Resend の読み取り 2 本だけ (送信しない)",
          [u.rsplit("/", 1)[-1] for _, u in fake.calls] == ["domains", "api-keys"] and all(m == "GET" for m, _ in fake.calls), fake.calls)

    for label, ans in (("削除済み (400 validation_error)", INVALID), ("有効でない (403 restricted_api_key)", NOT_ACTIVE),
                       ("停止中 (403 suspended_api_key)", SUSPENDED)):
        fake.set(domains=ans, api_keys=ans)
        d = admin_diag("invalid" if ans is INVALID else None)
        check(f"{label}: api_key_valid = false・scope = invalid", d.get("api_key_valid") is False and d.get("api_key_scope") == "invalid", d)
        check(f"{label}: api_key_error に name が出る", ans[1]["name"] in (d.get("api_key_error") or ""), d.get("api_key_error"))
        check(f"{label}: domain_status は unauthorized", str(d.get("domain_status") or "").startswith("unauthorized"), d.get("domain_status"))
    check("停止中: 対処は Resend サポートへの問い合わせ", "サポート" in (d.get("api_key_error") or "") and "サポート" in (d.get("domain_status_remediation") or ""),
          (d.get("api_key_error"), d.get("domain_status_remediation")))

    for label, ans, key in (("429 (毎秒上限)", RATE, "unknown"), ("502 (本文なし)", BAD_GATEWAY, None), ("タイムアウト", TIMEOUT, None)):
        fake.set(domains=ans, api_keys=ans)
        d = admin_diag(key)
        check(f"★{label}: api_key_valid は null (無効とは言わない)", "api_key_valid" in d and d["api_key_valid"] is None, d.get("api_key_valid"))
        check(f"{label}: api_key_scope = unknown", d.get("api_key_scope") == "unknown", d.get("api_key_scope"))
        check(f"{label}: api_key_error は「判定できず」", "判定できず" in (d.get("api_key_error") or ""), d.get("api_key_error"))
        check(f"{label}: domain_status は api_error", str(d.get("domain_status") or "").startswith("api_error"), d.get("domain_status"))
    check("429: api_key_error に HTTP 429 と name", "HTTP 429 rate_limit_exceeded" in (responses["unknown"].get("api_key_error") or ""),
          responses["unknown"].get("api_key_error"))

    # 2 本の答えが食い違う (片方だけ 429)。決まった方の答えを使い、矛盾した結果にしない
    fake.set(domains=SEND_ONLY, api_keys=RATE)
    d = admin_diag("mixed_domains_send_only")
    check("★/domains = 送信専用・/api-keys = 429 → 送信専用 (有効)", d.get("api_key_valid") is True and d.get("api_key_scope") == "send_only", d)
    check("  同: api_key_error を出さない", not d.get("api_key_error"), d.get("api_key_error"))
    fake.set(domains=RATE, api_keys=SEND_ONLY)
    d = admin_diag("mixed_keys_send_only")
    check("/domains = 429・/api-keys = 送信専用 → 送信専用 (有効)・domain_status は api_error",
          d.get("api_key_scope") == "send_only" and d.get("api_key_valid") is True and str(d.get("domain_status")).startswith("api_error"), d)
    fake.set(domains=INVALID, api_keys=RATE)
    d = admin_diag()
    check("/domains = 無効・/api-keys = 429 → 無効", d.get("api_key_valid") is False and d.get("api_key_scope") == "invalid", d)
    fake.set(domains=DOMAINS_OK, api_keys=RATE)
    d = admin_diag()
    check("/domains = 200・/api-keys = 429 → Full access (有効)", d.get("api_key_valid") is True and d.get("api_key_scope") == "full_access", d)

    fake.set(domains=DOMAINS_OK, api_keys=KEYS_OK)
    d = admin_diag("full")
    check("Full access キー: api_key_valid = true・scope = full_access", d.get("api_key_valid") is True and d.get("api_key_scope") == "full_access", d)
    check("Full access キー: domain_status = verified", d.get("domain_status") == "verified", d.get("domain_status"))
    fake.set(domains=DOMAINS_FAILED, api_keys=KEYS_OK)
    admin_diag("full_unverified")

    mod.RESEND_API_KEY = ""
    fake.set(domains=SEND_ONLY, api_keys=SEND_ONLY)
    d = admin_diag("unset")
    check("キー未設定: Resend を呼ばない・resend_api_key_set = false", d.get("resend_api_key_set") is False and not fake.calls, (d, fake.calls))
    mod.RESEND_API_KEY = "re_test_dummy_not_a_real_key"

    # 直近エラーの student_id: events の props はだれでも /api/track で書ける (画面でエスケープしないと CEO 画面で動く)
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
              ("magic_link_email_status", json.dumps({"email_sent": False, "error": "x", "student_id": XSS}), "t"))
    conn.commit(); conn.close()
    fake.set(domains=SEND_ONLY, api_keys=SEND_ONLY)
    admin_diag("xss_student_id")

    # ---------------------------------------------------------------- C
    print("\nC. GET /api/email/diagnose-public")
    fake.set(domains=SEND_ONLY, api_keys=SEND_ONLY)
    p = public_diag()
    check("送信専用キー: api_key_valid = true・scope = send_only",
          p.get("api_key_valid") is True and p.get("api_key_scope") == "send_only", p)
    check("送信専用キー: domain_status = unverifiable_via_send_only_key", p.get("domain_status") == "unverifiable_via_send_only_key", p)
    check("送信専用キー: last_error_class を立てない", not p.get("last_error_class"), p.get("last_error_class"))
    for label, ans in (("削除済み", INVALID), ("有効でない (403)", NOT_ACTIVE), ("停止中", SUSPENDED)):
        fake.set(domains=ans, api_keys=ans)
        p = public_diag()
        check(f"{label}: api_key_valid = false・scope = invalid", p.get("api_key_valid") is False and p.get("api_key_scope") == "invalid", p)
        check(f"{label}: last_error_class = HTTPError_{ans[0]}", p.get("last_error_class") == f"HTTPError_{ans[0]}", p.get("last_error_class"))
    fake.set(domains=RATE, api_keys=RATE)
    p = public_diag()
    check("429: api_key_valid = null・scope を決めない・last_error_short に 429",
          p.get("api_key_valid") is None and p.get("api_key_scope") is None and "429" in (p.get("last_error_short") or ""), p)
    fake.set(domains=TIMEOUT, api_keys=TIMEOUT)
    p = public_diag()
    check("タイムアウト: api_key_valid = null", p.get("api_key_valid") is None and p.get("last_error_class") == "URLError", p)
    check("公開側はキー本体を出さない", mod.RESEND_API_KEY not in json.dumps(p, ensure_ascii=False), "")

    # ---------------------------------------------------------------- D
    print("\nD. ceo.html のメール診断の表示 (B の本物の応答を本物の描画コードに通す)")
    engine = js_engine()
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(engine), "AJ_JS_ENGINE の指定も確認")
    if engine:
        body = diag_handler_body(open(os.path.join(REPO, "ceo.html"), encoding="utf-8").read())
        cases = [[name, resp, True] for name, resp in responses.items()]
        cases.append(["not_ok", {"detail": "未認証"}, False])
        out = run_render(engine, body, cases)
        BTN, REPAIR = "emailTestSendBtn", "🔧 修復手順"

        def has(name, s):
            return s in out.get(name, "")

        h = "send_only"
        check("送信専用キー: 「✅ 有効（送信専用キー）」", has(h, "✅ 有効（送信専用キー）"), out.get(h))
        check("★送信専用キー: 📨 テスト送信ボタンを出す", has(h, BTN), "")
        check("送信専用キー: 修復手順を出さない・「無効」と描かない", not has(h, REPAIR) and not has(h, "❌ 無効"), out.get(h))
        check("送信専用キー: ドメインは灰色で「読めません」", has(h, "color:#a3a3a3;font-weight:700;\">送信専用キーのため読めません"), out.get(h))
        h = "unknown"
        check("★429: 「⚠️ 判定できず」・「無効」と描かない", has(h, "⚠️ 判定できず") and not has(h, "❌ 無効"), out.get(h))
        check("429: テスト送信ボタンを出す・修復手順 (鍵の再生成・DNS) を出さない", has(h, BTN) and not has(h, REPAIR), out.get(h))
        for h in ("mixed_domains_send_only", "mixed_keys_send_only"):
            check(f"{h}: 有効（送信専用キー）・ボタンあり・修復手順なし",
                  has(h, "✅ 有効（送信専用キー）") and has(h, BTN) and not has(h, REPAIR), out.get(h))
        h = "invalid"
        check("無効なキー: 「❌ 無効」・ボタンなし", has(h, "❌ 無効") and not has(h, BTN), out.get(h))
        check("無効なキー: 修復手順は 1. 再生成 2. Railway と Vercel の RESEND_API_KEY", has(h, "<div>1. ") and has(h, "再生成")
              and has(h, "<div>2. Railway (API サーバ) と Vercel"), out.get(h))
        check("無効なキー: ドメインを読めなかっただけなので DNS の手順を出さない", not has(h, "DNS レコード"), out.get(h))
        h = "unset"
        check("未設定: 「❌ 未設定」・ボタンなし・手順は「発行」", has(h, "❌ 未設定") and not has(h, BTN) and has(h, "発行"), out.get(h))
        h = "full"
        check("Full access・verified: 有効・ボタンあり・修復手順なし", has(h, "✅ 有効</span>") and has(h, BTN) and not has(h, REPAIR), out.get(h))
        h = "full_unverified"
        check("Full access・ドメイン未検証: DNS の手順が 1. から", has(h, "<div>1. <a href=\"https://resend.com/domains\"") and has(h, BTN), out.get(h))
        check("ログイン切れ (401): 描かずに「未認証」で止める", out.get("not_ok") == "THROW:未認証", out.get("not_ok"))
        h = "xss_student_id"
        check("★直近エラーの student_id をエスケープする (タグとして描かない)", "&lt;img src=x" in out.get(h, "") and "<img" not in out.get(h, ""),
              out.get(h, "")[-400:])

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for x in FAILURES:
            print(f"   - {x}")
        return 1
    print("✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
