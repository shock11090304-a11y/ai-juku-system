#!/usr/bin/env python3
"""🔁 生徒ログインの自動延長と LINE「やること」の返信リンク (2026-10-18 塾長「②の残りも作っておいて」) の回帰テスト。

背景 (成績を上げる提案 ②「入口の壁を取る」): 生徒のトークンはログインから 30 日で必ず切れ、延長が無かった
  (管理者だけ /api/admin/verify が延長する)。「やろう」と思って開いた日にログイン画面が出ると、その日の宿題は出ない。
  そこで全ページのガード auth-guard.js が叩く GET /api/auth/me で、残りが 15 日を切った**在籍中の生徒**にだけ、
  ログインと同じ形の新しいトークンを renewed = {token, expires_at} で返し、auth-guard がログインと同じキーに保存する。
  あわせて LINE「やること」の返信のリンクを、リッチメニュー A「宿題を開く」と同じ宿題欄の URL にした (返信だけ・push なし)。

固定する性質:
  [1] 在籍中 (paid) の生徒・残り 10 日 → renewed あり。新しいトークンはログインと同じ形 (session.{id}.{exp}.{sig})・同じ生徒・
      期限はいまから 30 日・応答は private, no-store・新しいトークンで入れて、もう延長しない
  [2] 残り 15 日の境目 (15 日 + 1 分は延長しない / 15 日 − 1 分は延長する)・ログイン直後 (30 日) は延長しない
  [3] 親のアドレスでも子のアドレス (確認済みの子供メール) でもトークンは生徒 id と期限だけ = 延長しても同じ生徒・同じ形。
      延長で students の email / student_email / 確認済みフラグは変わらない
  [4] AIなし (塾生アプリのみ枠・trial + 国公立難関大コース + ai_disabled=1)・猶予中の past_due・体験中の trial → 延長する
  [5] canceled / 体験切れ → entitled=false で延長しない。国公立難関大コースで canceled / expired / 猶予切れの past_due
      (_get_current_student は通す) も在籍ではないので延長しない
  [6] 合成監視 (@synthetic-monitor.)・テスト系の名前 → 延長しない (応答は今までどおり 200)
  [7] 管理者のなりすまし (impersonation) は延長しない・magic / dl トークンは今までどおり 401・旧 3 パートの session は新しい形に延長
  [8] 管理者の経路は変わらない: /api/admin/verify の延長・管理者トークンで /api/auth/me は 401・生徒トークンで /api/admin/verify は 401
  [9] 延長の SELECT が失敗しても 200 で延長なし・ログにトークンを出さない
  [10] LINE「やること」: 返信の本文に {BASE_URL}/mypage.html?focus=homework&openExternalBrowser=1 (AIあり・AIなしとも)・
       LINE API は reply だけ (push 0)・未連携は案内だけ・リッチメニュー A の URL と同じ
  [11] auth-guard.js を JS エンジンで動かす: renewed をログインと同じキー・形で保存・問い合わせたトークンが替わっていたら触らない・
       期限が過去 / 今より短い / 形が違うものは保存しない・localStorage が throw しても止まらず login へ飛ばさない・
       entitled=false では保存しない・401 は今までどおり login へ・トークンを console に出さない
  [12] ソース検査: auth-guard.js を読む HTML は全部同じ ?v= (新しい版)・CI 登録

★JS エンジンが無ければ FAIL (飛ばさない)。CI (ubuntu) は node、塾長の Mac は osascript -l JavaScript。
  外部通信なし (LINE API は偽物)・DB は一時 SQLite・生徒名とメールは架空 (公開リポジトリ)。

実行:
    python3 scripts/health_check/test_student_session_renew.py
    # exit 0 = PASS / 1 = FAIL
"""
import base64
import datetime
import glob
import hashlib
import hmac
import importlib.util
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
GUARD_JS = os.path.join(REPO, "auth-guard.js")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc"
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []
DAY = 86400
RICH_MENU_A = "https://trillion-ai-juku.com/mypage.html?focus=homework&openExternalBrowser=1"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="renew_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと本番 Postgres に書き込む
        "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_renew", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def utc_str(dt):
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def mk(mod, name, email, *, status="paid", course=None, ai_disabled=0, trial_days=365, student_email=None,
       verified=0, past_due_days=None, goal=None):
    now = datetime.datetime.now(datetime.timezone.utc)
    conn = mod.db(); c = conn.cursor()
    c.execute(
        "INSERT INTO students (name, email, status, plan, trial_end, course, grade, goal, student_email, student_email_verified, "
        "ai_disabled, past_due_since) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (name, email, status, "founder_special", (now + datetime.timedelta(days=trial_days)).isoformat(), course, "高校2年",
         goal, student_email, verified, ai_disabled,
         utc_str(now - datetime.timedelta(days=past_due_days)) if past_due_days is not None else None),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE email = ?", (email,))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


def tok(mod, sid, left_seconds, ttype="session"):
    return mod._sign_session_token(sid, ttl_seconds=int(left_seconds), token_type=ttype)


def legacy_tok(mod, sid, left_seconds):
    exp = int(time.time()) + int(left_seconds)
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"{sid}.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{sid}.{exp}.{sig}".encode()).decode().rstrip("=")


def admin_tok(mod, left_seconds):
    return mod._sign_admin_token(ttl=int(left_seconds))["token"]


def parts(token):
    raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)).decode()
    return raw.split(".")


def me(client, token):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer " + token})
    try:
        j = r.json()
    except Exception:
        j = {}
    return r, j


# ---------------------------------------------------------------------------------------------------------------
# [11] auth-guard.js を JS エンジンで動かす
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


# 結果の書き出し (node は console.log = stdout、osascript は console.log = stderr、jsc は print)。OK / NG / DONE の行だけを読む
JS_PRELUDE = r"""
var __out = [];
function __j(v) { try { return JSON.stringify(v); } catch (e) { return String(v); } }
function eq(label, got, want) { var ok = __j(got) === __j(want); __out.push((ok ? 'OK  ' : 'NG  ') + label + (ok ? '' : ' => ' + __j(got) + ' (want ' + __j(want) + ')')); }
function ok(label, cond, detail) { __out.push((cond ? 'OK  ' : 'NG  ') + label + (cond || detail === undefined ? '' : ' => ' + __j(detail))); }
function __emit() {
  var s = __out.join('\n') + '\nDONE ' + __out.length;
  if (typeof process !== 'undefined' && typeof console !== 'undefined' && console.log) console.log(s);
  else if (typeof print === 'function') print(s);
  else if (typeof console !== 'undefined' && console.log) console.log(s);
}
async function flush(n) { for (var i = 0; i < (n || 400); i++) await Promise.resolve(); }
// 最小の URLSearchParams (osascript / jsc には無い。node は本物を使う。auth-guard の redirectToLogin が使う)
(function (g) {
  if (typeof g.URLSearchParams !== 'undefined') return;
  var URLSearchParams = function (s) {
    this._p = [];
    s = String(s || '').replace(/^\?/, '');
    if (s) {
      var ps = s.split('&');
      for (var i = 0; i < ps.length; i++) {
        if (!ps[i]) continue;
        var kv = ps[i].split('=');
        this._p.push([decodeURIComponent(kv[0]), decodeURIComponent(kv.slice(1).join('=') || '')]);
      }
    }
  };
  URLSearchParams.prototype.get = function (k) { for (var i = 0; i < this._p.length; i++) if (this._p[i][0] === k) return this._p[i][1]; return null; };
  URLSearchParams.prototype.set = function (k, v) { this._p = this._p.filter(function (p) { return p[0] !== k; }); this._p.push([k, String(v)]); };
  URLSearchParams.prototype.toString = function () { return this._p.map(function (p) { return encodeURIComponent(p[0]) + '=' + encodeURIComponent(p[1]); }).join('&'); };
  g.URLSearchParams = URLSearchParams;
})(typeof globalThis !== 'undefined' ? globalThis : this);
// localStorage の偽物。throwKeys に入れたキーの setItem は throw する (保存できない端末)
function memStore(init, throwKeys) {
  var m = {}, k;
  for (k in (init || {})) m[k] = String(init[k]);
  return {
    getItem: function (k) { return Object.prototype.hasOwnProperty.call(m, k) ? m[k] : null; },
    setItem: function (k, v) { if (throwKeys && throwKeys.indexOf(k) >= 0) throw new Error('QuotaExceededError'); m[k] = String(v); },
    removeItem: function (k) { delete m[k]; },
    _m: m
  };
}
var NOW = Math.floor(Date.now() / 1000);
var STUDENT = { id: 7, name: '生徒 甲', email: 'p1@example.org', entitled: true };
// auth-guard.js を 1 ページ分読み込む。localStorage / sessionStorage / fetch / window / console は引数で差し替える
async function boot(o) {
  var store = memStore(o.storage, o.throwKeys), sess = memStore({});
  var calls = [], warns = [], replaced = [];
  var win = { location: { origin: 'https://example.invalid', pathname: o.path || '/mypage.html', search: '', href: '',
                          replace: function (u) { replaced.push(String(u)); } } };
  var fakeFetch = function (url, init) {
    calls.push({ url: String(url), auth: (init && init.headers && init.headers['Authorization']) || null });
    if (o.onFetch) o.onFetch(store);
    var r = o.response;
    return Promise.resolve({ ok: r.status >= 200 && r.status < 300, status: r.status,
                             json: function () { return Promise.resolve(JSON.parse(JSON.stringify(r.body))); } });
  };
  var con = { log: function () {}, error: function () {},
              warn: function () { var a = []; for (var i = 0; i < arguments.length; i++) a.push(String(arguments[i])); warns.push(a.join(' ')); } };
  __loadGuard(store, sess, fakeFetch, win, con);
  await flush();
  return { m: store._m, calls: calls, warns: warns, replaced: replaced, guard: win.AuthGuard };
}
"""

JS_CASES = r"""
(async function () {
  try {
    var base = { ai_juku_session_token: 'OLD-TOKEN', ai_juku_session_expires: String(NOW + 5 * 86400) };
    var NEWEXP = NOW + 30 * 86400;

    // (1) サーバが renewed を返した → ログインと同じキー・同じ形で置き換わる
    var r = await boot({ storage: base, response: { status: 200, body: { ok: true, student: STUDENT, renewed: { token: 'NEW-TOKEN', expires_at: NEWEXP } } } });
    eq('(1) /api/auth/me を今のトークンで 1 回だけ問い合わせる', r.calls.map(function (c) { return c.auth; }), ['Bearer OLD-TOKEN']);
    eq('(1) トークンが新しいものに置き換わる', r.m.ai_juku_session_token, 'NEW-TOKEN');
    eq('(1) 期限はログインと同じ epoch 秒の文字列', r.m.ai_juku_session_expires, String(NEWEXP));
    eq('(1) AuthGuard.getToken も新しいトークン', r.guard.getToken(), 'NEW-TOKEN');
    eq('(1) 本人の表示ポインタは今までどおり', JSON.parse(r.m.ai_juku_session_student).id, 7);
    eq('(1) ログインへ飛ばない・警告なし', [r.replaced, r.warns], [[], []]);

    // (2) renewed が無い (残りが 15 日以上・在籍でない) → 何も変えない
    r = await boot({ storage: base, response: { status: 200, body: { ok: true, student: STUDENT } } });
    eq('(2) renewed なし: トークンと期限はそのまま', [r.m.ai_juku_session_token, r.m.ai_juku_session_expires], ['OLD-TOKEN', base.ai_juku_session_expires]);

    // (3) 応答待ちの間にログアウト → 別の生徒でログインしていた: 触らない
    r = await boot({ storage: base, onFetch: function (s) { s.setItem('ai_juku_session_token', 'OTHER-STUDENT'); s.setItem('ai_juku_session_expires', String(NOW + 29 * 86400)); },
                     response: { status: 200, body: { ok: true, student: STUDENT, renewed: { token: 'NEW-TOKEN', expires_at: NEWEXP } } } });
    eq('(3) 問い合わせたトークンが替わっていたら上書きしない', [r.m.ai_juku_session_token, r.m.ai_juku_session_expires], ['OTHER-STUDENT', String(NOW + 29 * 86400)]);

    // (4) 形の違う renewed は保存しない
    var bad = [
      ['期限が過去', { token: 'NEW-TOKEN', expires_at: NOW - 10 }],
      ['期限が 0', { token: 'NEW-TOKEN', expires_at: 0 }],
      ['期限が数字でない', { token: 'NEW-TOKEN', expires_at: 'abc' }],
      ['今の期限より短い', { token: 'NEW-TOKEN', expires_at: NOW + 4 * 86400 }],
      ['今の期限と同じ', { token: 'NEW-TOKEN', expires_at: NOW + 5 * 86400 }],
      ['トークンが空', { token: '', expires_at: NEWEXP }],
      ['トークンが文字列でない', { token: 12345, expires_at: NEWEXP }],
      ['renewed が文字列', 'NEW-TOKEN']
    ];
    for (var i = 0; i < bad.length; i++) {
      r = await boot({ storage: base, response: { status: 200, body: { ok: true, student: STUDENT, renewed: bad[i][1] } } });
      eq('(4) ' + bad[i][0] + ' → 保存しない', [r.m.ai_juku_session_token, r.m.ai_juku_session_expires], ['OLD-TOKEN', base.ai_juku_session_expires]);
    }

    // (5) localStorage に保存できない端末: 止まらず、ログインへ飛ばさず、今のトークンのまま
    r = await boot({ storage: base, throwKeys: ['ai_juku_session_token', 'ai_juku_session_expires'],
                     response: { status: 200, body: { ok: true, student: STUDENT, renewed: { token: 'NEW-TOKEN', expires_at: NEWEXP } } } });
    eq('(5) setItem が throw しても今のトークンのまま・ログインへ飛ばない・警告なし', [r.m.ai_juku_session_token, r.replaced, r.warns], ['OLD-TOKEN', [], []]);

    // (6) entitled=false (体験切れ・解約) では renewed が来ても保存しない (サーバも返さない)
    r = await boot({ storage: base, response: { status: 200, body: { ok: true, student: { id: 7, entitled: false }, renewed: { token: 'NEW-TOKEN', expires_at: NEWEXP } } } });
    eq('(6) entitled=false: 保存しない・継続登録へ', [r.m.ai_juku_session_token, r.replaced], ['OLD-TOKEN', ['upgrade.html?reason=resubscribe']]);

    // (7) 401 は今までどおりセッションを消して login へ
    r = await boot({ storage: base, response: { status: 401, body: { detail: 'Unauthorized' } } });
    eq('(7) 401: トークンを消して login へ', [r.m.ai_juku_session_token || null, r.replaced.length === 1 && r.replaced[0].indexOf('login.html') === 0], [null, true]);

    // (8) 5xx はローカルのまま (延長もしない)
    r = await boot({ storage: base, response: { status: 503, body: { renewed: { token: 'NEW-TOKEN', expires_at: NEWEXP } } } });
    eq('(8) 503: 今のトークンのまま・ログインへ飛ばない', [r.m.ai_juku_session_token, r.replaced], ['OLD-TOKEN', []]);

    // (9) 期限切れの端末は問い合わせずに login へ (今までどおり・延長で復活させない)
    r = await boot({ storage: { ai_juku_session_token: 'OLD-TOKEN', ai_juku_session_expires: String(NOW - 60) },
                     response: { status: 200, body: { ok: true, student: STUDENT, renewed: { token: 'NEW-TOKEN', expires_at: NEWEXP } } } });
    eq('(9) 端末の期限切れ: 問い合わせない・login へ', [r.calls.length, r.replaced.length === 1 && r.replaced[0].indexOf('login.html') === 0, r.m.ai_juku_session_token], [0, true, 'OLD-TOKEN']);
  } catch (e) {
    ok('JS の例外なし', false, String(e && e.stack || e));
  }
  __emit();
})();
"""


def run_js(engine, program, label):
    with tempfile.TemporaryDirectory(prefix="renew_js_") as td:
        path = os.path.join(td, "case.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(program)
        try:
            r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=180)
        except Exception as e:  # noqa: BLE001
            check(f"{label}: JS を実行できた", False, f"{type(e).__name__}: {e}")
            return
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    lines = [l for l in text.split("\n") if l.startswith(("OK  ", "NG  ", "DONE "))]
    done = [l for l in lines if l.startswith("DONE ")]
    if r.returncode != 0 or not done:
        check(f"{label}: JS が最後まで走った (exit {r.returncode})", False, text[-1500:])
        return
    for l in lines:
        if l.startswith("OK  "):
            check(l[4:], True)
        elif l.startswith("NG  "):
            check(l[4:], False, l[4:])
    n = int(done[-1].split()[1])
    check(f"{label}: {n} 件の検査を実行", n > 0)


def main():
    print("🔁 生徒ログインの自動延長・LINE「やること」の返信リンク (2026-10-18) 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    TTL = mod.SESSION_TTL_SECONDS
    WIN = mod.STUDENT_SESSION_RENEW_WINDOW_SECONDS
    check("延長の窓は 15 日 (30 日の半分)", WIN == 15 * DAY and TTL == 30 * DAY, (WIN, TTL))

    P = mk(mod, "生徒 甲", "p1@example.org", student_email="c1@example.org", verified=1)
    AIN = mk(mod, "生徒 乙", "p2@example.org", status="trial", course="kokuritsu_nankan", ai_disabled=1, trial_days=3650)
    PD_OK = mk(mod, "生徒 丙", "p3@example.org", status="past_due", past_due_days=3)
    TR = mk(mod, "生徒 丁", "p4@example.org", status="trial", trial_days=5)
    CAN = mk(mod, "生徒 戊", "p5@example.org", status="canceled")
    TR_END = mk(mod, "生徒 己", "p6@example.org", status="trial", trial_days=-1)
    K_CAN = mk(mod, "生徒 庚", "p7@example.org", status="canceled", course="kokuritsu_nankan")
    K_EXP = mk(mod, "生徒 辛", "p8@example.org", status="expired", course="kokuritsu_nankan")
    K_PD_OLD = mk(mod, "生徒 壬", "p9@example.org", status="past_due", course="kokuritsu_nankan", past_due_days=40)
    SYN = mk(mod, "生徒 癸", "synth-1@synthetic-monitor.local")
    TESTN = mk(mod, "テスト 生徒", "p10@example.org")

    # ---------------------------------------------------------------- [1]
    print("[1] 在籍中の生徒・残り 10 日 → 延長")
    t_old = tok(mod, P, 10 * DAY)
    r, j = me(client, t_old)
    rn = j.get("renewed") or {}
    check("200 で本人", r.status_code == 200 and (j.get("student") or {}).get("id") == P, (r.status_code, j))
    check("renewed = {token, expires_at}", isinstance(rn, dict) and set(rn) == {"token", "expires_at"}, rn)
    new = rn.get("token") or ""
    if new:
        p = parts(new)
        claims = mod._verify_session_token(new)
        check("ログインと同じ形: session.{id}.{exp}.{sig} の 4 つ", len(p) == 4 and p[0] == "session" and p[1] == str(P), p[:3])
        check("同じ生徒・種別 session", claims and claims["student_id"] == P and claims["token_type"] == "session", claims)
        check("期限はいまから 30 日 (expires_at と一致)",
              claims and abs(claims["exp"] - (int(time.time()) + TTL)) <= 5 and claims["exp"] == rn.get("expires_at"),
              (claims, rn.get("expires_at")))
        check("前のトークンとは別の文字列", new != t_old)
        check("応答は private, no-store", "no-store" in (r.headers.get("cache-control") or ""), r.headers.get("cache-control"))
        r2, j2 = me(client, new)
        check("新しいトークンで入れて、もう延長しない", r2.status_code == 200 and (j2.get("student") or {}).get("id") == P and "renewed" not in j2, j2)
        check("student の中身は延長のない応答と同じキー", set((j.get("student") or {}).keys()) == set((j2.get("student") or {}).keys()),
              set((j.get("student") or {}).keys()) ^ set((j2.get("student") or {}).keys()))
        check("延長のない応答は今までどおり (ok と student だけ)", set(j2.keys()) == {"ok", "student"}, j2.keys())
    check("古いトークンも期限までは使える (失効させない)", me(client, t_old)[0].status_code == 200)

    # ---------------------------------------------------------------- [2]
    print("\n[2] 15 日の境目")
    check("残り 15 日 + 1 分 → 延長しない", "renewed" not in me(client, tok(mod, P, WIN + 60))[1])
    check("残り 15 日 − 1 分 → 延長する", "renewed" in me(client, tok(mod, P, WIN - 60))[1])
    check("残り 20 日 → 延長しない", "renewed" not in me(client, tok(mod, P, 20 * DAY))[1])
    check("ログイン直後 (30 日) → 延長しない", "renewed" not in me(client, mod._sign_session_token(P))[1])
    check("残り 1 分 → 延長する", "renewed" in me(client, tok(mod, P, 60))[1])

    # ---------------------------------------------------------------- [3]
    print("\n[3] 親のアドレス・子のアドレスでのログインと延長")
    def otp_login(email):
        mod._RATE_LIMIT_STORE.clear()
        code = mod._create_otp(P)
        return client.post("/api/auth/verify-code", json={"email": email, "code": code})
    rp = otp_login("p1@example.org")
    rc = otp_login("c1@example.org")
    check("親のアドレス + コードでログインできる", rp.status_code == 200, rp.text[:200])
    check("子のアドレス + コードでログインできる (同じ生徒)", rc.status_code == 200 and rc.json()["student"]["id"] == P, rc.text[:200])
    if rp.status_code == 200 and rc.status_code == 200:
        tp, tc = rp.json()["token"], rc.json()["token"]
        cp, cc = mod._verify_session_token(tp), mod._verify_session_token(tc)
        check("どちらのトークンも生徒 id・期限・種別だけ (どのアドレスで入ったかは持たない)",
              set(cp) == {"student_id", "exp", "token_type"} and set(cc) == set(cp) and cp["student_id"] == cc["student_id"] == P, (cp, cc))
        check("ログインのトークンと延長のトークンは同じ形", [len(parts(tp)), parts(tp)[0]] == [len(parts(new)), parts(new)[0]] if new else False)
        for label, t in (("親", tp), ("子", tc)):
            # そのログインから 16 日たった状態のトークン (残り 14 日) を同じ生徒で作って延長する
            near = tok(mod, P, 14 * DAY)
            rr, jj = me(client, near)
            nc = mod._verify_session_token((jj.get("renewed") or {}).get("token") or "")
            check(f"{label}のアドレスで入った生徒も延長され、同じ生徒のまま", bool(nc) and nc["student_id"] == P and nc["token_type"] == "session", jj.get("renewed"))
            check(f"{label}のログインのトークン (残り 30 日) は延長しない", "renewed" not in me(client, t)[1])
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT email, student_email, student_email_verified FROM students WHERE id = ?", (P,))
    row = c.fetchone(); conn.close()
    check("延長しても email / student_email / 確認済みは変わらない",
          (row["email"], row["student_email"], int(row["student_email_verified"])) == ("p1@example.org", "c1@example.org", 1), dict(row))

    # ---------------------------------------------------------------- [4] [5] [6]
    print("\n[4][5][6] 在籍の決め方")
    cases = [
        ("AIなし (塾生アプリのみ枠: trial + 国公立難関大コース + ai_disabled)", AIN, True, True),
        ("猶予中の past_due (3 日前に決済失敗)", PD_OK, True, True),
        ("体験中の trial", TR, True, True),
        ("canceled", CAN, False, False),
        ("体験切れの trial", TR_END, False, False),
        ("国公立難関大コースで canceled (_get_current_student は通す)", K_CAN, True, False),
        ("国公立難関大コースで expired", K_EXP, True, False),
        ("国公立難関大コースで猶予切れの past_due (40 日前)", K_PD_OLD, True, False),
        ("合成監視 (@synthetic-monitor.)", SYN, True, False),
        ("テスト系の名前", TESTN, True, False),
    ]
    for label, sid, entitled, renew in cases:
        r, j = me(client, tok(mod, sid, 10 * DAY))
        st = j.get("student") or {}
        check(f"{label}: 200・entitled={entitled}", r.status_code == 200 and st.get("id") == sid and st.get("entitled") is entitled, (r.status_code, st.get("entitled")))
        check(f"{label}: {'延長する' if renew else '延長しない'}", ("renewed" in j) is renew, j.get("renewed"))

    # ---------------------------------------------------------------- [7]
    print("\n[7] トークンの種別")
    r, j = me(client, tok(mod, K_CAN, 10 * DAY, "impersonation"))
    check("管理者のなりすまし: 入れるが延長しない", r.status_code == 200 and "renewed" not in j, (r.status_code, j.get("renewed")))
    r, j = me(client, tok(mod, P, 10 * DAY, "impersonation"))
    check("在籍中の生徒へのなりすましでも延長しない", r.status_code == 200 and "renewed" not in j, (r.status_code, j.get("renewed")))
    check("magic トークンは今までどおり 401", me(client, tok(mod, P, 10 * DAY, "magic"))[0].status_code == 401)
    check("dl トークンは今までどおり 401", me(client, tok(mod, P, 10 * 60, "dl"))[0].status_code == 401)
    r, j = me(client, legacy_tok(mod, P, 10 * DAY))
    lp = parts((j.get("renewed") or {}).get("token") or "e30")
    check("旧 3 パートの session は新しい 4 パートの形に延長", r.status_code == 200 and len(lp) == 4 and lp[0] == "session" and lp[1] == str(P), lp[:2])
    check("署名の違うトークンは 401", me(client, tok(mod, P, 10 * DAY)[:-3] + "AAA")[0].status_code == 401)

    # ---------------------------------------------------------------- [8]
    print("\n[8] 管理者の経路は変わらない")
    a_near = admin_tok(mod, 10 * DAY)
    r = client.get("/api/admin/verify", headers={"Authorization": "Bearer " + a_near})
    aj = r.json() if r.status_code == 200 else {}
    arn = (aj.get("renewed") or {}).get("token") or ""
    check("管理者トークン (残り 10 日) は /api/admin/verify が今までどおり延長", r.status_code == 200 and arn and parts(arn)[0] == "admin" and len(parts(arn)) == 3, aj)
    r = client.get("/api/admin/verify", headers={"Authorization": "Bearer " + admin_tok(mod, 29 * DAY)})
    check("管理者トークン (残り 29 日) は延長しない", r.status_code == 200 and "renewed" not in r.json(), r.text[:200])
    check("管理者トークンで /api/auth/me は 401", me(client, a_near)[0].status_code == 401)
    r = client.get("/api/admin/verify", headers={"Authorization": "Bearer " + tok(mod, P, 10 * DAY)})
    check("生徒のトークンで /api/admin/verify は 401", r.status_code == 401, r.status_code)

    # ---------------------------------------------------------------- [9]
    print("\n[9] 失敗しても確認は成功・トークンをログに出さない")
    records = []

    class _H(logging.Handler):
        def emit(self, rec):
            records.append(rec.getMessage())
    h = _H(); mod.log.addHandler(h)
    old_level = mod.log.level
    mod.log.setLevel(logging.DEBUG)
    try:
        t9 = tok(mod, P, 10 * DAY)
        r, j = me(client, t9)
        new9 = (j.get("renewed") or {}).get("token") or ""
        check("延長できた (ログの検査の前提)", bool(new9))
        check("ログに古いトークンも新しいトークンも出ない", new9 and not any((t9 in m) or (new9 in m) for m in records), [m[:120] for m in records])
        check("延長のログは生徒 id だけ", any("session renewed: student_id=" in m for m in records), records)
        orig = mod._enrolled_sql
        mod._enrolled_sql = lambda alias="": "(no_such_column = 1)"
        try:
            r, j = me(client, tok(mod, P, 10 * DAY))
            check("延長の SELECT が失敗しても 200・延長なし", r.status_code == 200 and (j.get("student") or {}).get("id") == P and "renewed" not in j, (r.status_code, j.get("renewed")))
        finally:
            mod._enrolled_sql = orig
        orig_sign = mod._sign_session_token

        def _boom(*a, **k):
            if k.get("token_type", "session") == "session" and k.get("ttl_seconds") is None and len(a) == 1:
                raise RuntimeError("sign failed")
            return orig_sign(*a, **k)
        mod._sign_session_token = _boom
        try:
            r, j = me(client, orig_sign(P, ttl_seconds=10 * DAY))
            check("新しいトークンを作れなくても 200・延長なし", r.status_code == 200 and "renewed" not in j, (r.status_code, j.get("renewed")))
        finally:
            mod._sign_session_token = orig_sign
    finally:
        mod.log.removeHandler(h)
        mod.log.setLevel(old_level)

    # ---------------------------------------------------------------- [10]
    print("\n[10] LINE「やること」の返信リンク")
    want_link = f"{mod.BASE_URL}/mypage.html?focus=homework&openExternalBrowser=1"
    check("リンクはリッチメニュー A「宿題を開く」と同じ URL", "https://trillion-ai-juku.com" + mod._LINE_TODO_LINK_PATH == RICH_MENU_A, mod._LINE_TODO_LINK_PATH)
    calls = []
    orig_api = mod._line_api_call
    mod._line_api_call = lambda endpoint, body: (calls.append((endpoint, body)) or True)
    try:
        conn = mod.db(); c = conn.cursor()
        c.execute("UPDATE students SET line_user_id = ? WHERE id = ?", ("U_test_line_aiari_000000000000000", P))
        c.execute("UPDATE students SET line_user_id = ? WHERE id = ?", ("U_test_line_ainashi_00000000000000", AIN))
        conn.commit(); conn.close()
        for label, uid in (("AIあり", "U_test_line_aiari_000000000000000"), ("AIなし", "U_test_line_ainashi_00000000000000")):
            calls.clear()
            mod._handle_line_event({"type": "message", "replyToken": "rt-" + label, "webhookEventId": "ev-" + label,
                                    "source": {"type": "user", "userId": uid}, "message": {"type": "text", "text": "やること"}})
            ends = [e for e, _ in calls]
            text = calls[0][1]["messages"][0]["text"] if calls else ""
            check(f"{label}: LINE API は reply 1 回だけ (push なし)", ends == ["message/reply"], ends)
            check(f"{label}: 返信の最後が宿題欄のリンク", text.rstrip().endswith(want_link) and "▶ 宿題を開く" in text, text[-160:])
            check(f"{label}: マイページだけのリンク・class.html は出さない (AIなしは mypage が宿題タブへ送る)",
                  f"{mod.BASE_URL}/mypage.html\n" not in text + "\n" and "class.html" not in text, text[-160:])
        calls.clear()
        mod._handle_line_event({"type": "message", "replyToken": "rt-x", "webhookEventId": "ev-x",
                                "source": {"type": "user", "userId": "U_not_linked_000000000000000000"}, "message": {"type": "text", "text": "今日のやること"}})
        check("未連携: 連携の案内を reply で 1 回だけ", [e for e, _ in calls] == ["message/reply"] and calls[0][1]["messages"][0]["text"] == mod._LINE_NOT_LINKED_GUIDE, calls)
    finally:
        mod._line_api_call = orig_api
    src = read(MAIN_PY)
    fn = src[src.index("def _line_build_todo_text"):src.index("def _line_handle_question")]
    check("「やること」の本文を作る関数は LINE に送らない (返信は呼び出し側の reply だけ)", "_line_push" not in fn and "_line_api_call" not in fn and "_do_line_push" not in fn)
    mp = read(os.path.join(REPO, "mypage.html"))
    check("mypage は AIなし枠を ?focus=homework から class.html?tab=homework へ送る (前提)",
          "get('focus') === 'homework') _q = '?tab=homework'" in mp and "window.location.replace('class.html' + _q)" in mp)

    # ---------------------------------------------------------------- [11]
    print("\n[11] auth-guard.js (JS エンジンで動かす)")
    guard = read(GUARD_JS)
    eng = js_engine()
    print(f"  JS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng), "node も osascript も jsc も見つからない")
    if eng:
        loader = "function __loadGuard(localStorage, sessionStorage, fetch, window, console) {\n" + guard + "\n}\n"
        run_js(eng, JS_PRELUDE + loader + JS_CASES, "[11]")
    a = guard.find("function storeRenewedSession")
    body = guard[a:guard.find("async function authFetch", a)] if a >= 0 else ""
    check("storeRenewedSession がある", bool(body))
    check("storeRenewedSession は console に何も出さない (トークンをログに出さない)", "console." not in body, body[:200])
    check("ログインと同じキーに保存する", "localStorage.setItem(SESSION_TOKEN_KEY, renewed.token)" in body and "localStorage.setItem(SESSION_EXPIRES_KEY, String(exp))" in body)
    check("保存は try/catch の中", re.search(r"try \{[\s\S]*setItem\(SESSION_TOKEN_KEY[\s\S]*\} catch", body) is not None)
    check("enforceAuth が問い合わせたトークンで呼ぶ", "storeRenewedSession(token, data.renewed)" in guard)

    # ---------------------------------------------------------------- [12]
    print("\n[12] ソース検査 (?v= と CI)")
    vs = {}
    for h in sorted(glob.glob(os.path.join(REPO, "**", "*.html"), recursive=True)):
        if os.sep + ".git" + os.sep in h or os.sep + "node_modules" + os.sep in h:
            continue
        for m in re.finditer(r'<script[^>]+src="((?:\.\./)*auth-guard\.js)(?:\?v=([^"]*))?"', read(h)):
            vs[os.path.relpath(h, REPO)] = m.group(2)
    check("auth-guard.js を読む HTML が見つかる (16 本以上)", len(vs) >= 16, len(vs))
    check("どの HTML も ?v= 付き", all(vs.values()), [k for k, v in vs.items() if not v])
    check("どの HTML も同じ ?v= (1 本の JS なので 1 つにそろえる)", len(set(vs.values())) == 1, sorted(set(vs.values())))
    vv = next(iter(vs.values()), "") or ""
    check("?v= は自動延長の版 (2026-10-18 以降)", vv[:8].isdigit() and vv[:8] >= "20261018", vv)
    ci = read(CI_YML)
    check("CI (server-tests.yml) がこのテストを回す", "scripts/health_check/test_student_session_renew.py" in ci)
    check("CI は auth-guard.js だけ直した push でも走る", re.search(r"^\s*- 'auth-guard\.js'", ci, re.M) is not None)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print("   -", f)
        return 1
    print("✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
