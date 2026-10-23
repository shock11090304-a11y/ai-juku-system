#!/usr/bin/env python3
"""🔒 LINE 連携の付け替え防止と、管理者が連携を外す道 (2026-10-23) の回帰テスト。

背景: 連携コードは期限なしで、入塾承認のメール (保護者宛) にも書いてある。生徒がすでに LINE 連携しているところへ、
  別の LINE (保護者が子どものマイページで発行したコードや承認メールのコード) から有効なコードが届くと、
  _bind_line_user が子どもの line_user_id を黙って上書きしていた。以後ログインコードやお知らせは保護者の LINE に届き、
  子どもには届かない。2026-10-23 にリッチメニューを 9 ボタンにして、保護者が連携を試す場面が増えた。

固定する性質:
  [1] 再現: 子どもが連携済み → 保護者の LINE から有効なコード → 子どもの連携はそのまま・保護者には「別のLINEが連携済み・
      お子さまのLINEならそのまま・名前を添えて塾に連絡」を reply で 1 回だけ (push なし)・コードは消費しない・
      断った記録 events.line_bind_refused (生徒 id だけ・userId なし・session_id は生徒 ID にしない)
  [2] 同じ LINE からの送り直しは今までどおり連携完了 (冪等)・未連携の生徒は最初に送った LINE で連携できる
  [3] 1 つの LINE は 1 人の生徒だけ (taken) は今までどおり
  [4] _bind_line_user: 事前判定のあとに別の LINE が先に連携しても上書きしない (UPDATE の WHERE)・空文字は未連携扱い・
      生徒が無ければ missing。webhook の race 経路でも同じ返事
  [5] 管理 API POST /api/admin/students/{id}/line-unlink: 認証 (admin Bearer / X-Cron-Secret)・404・連携を外す・
      この生徒の未使用コードだけ全部無効 (使用済み・他の生徒のコードは触らない)・記録に LINE の userId を残さない・
      記録の at = 無効にしたコードの used_at (診断の reason=used と見分ける)・2 回目は was_linked=false
  [6] 外したあと: 古いコード (保護者の承認メールのコード) は無効・新しいコードを新しい LINE から送ると連携できる (機種変更の救済)
  [7] issue-line-link: 連携済みならコードを出さず (行も作らない) already_linked_note で「先に外す」を案内・未連携ならコードと None
  [8] 連携済みの LINE が使用済みのコードを送り直したときの「すでに連携済み」の返事は今までどおり
  [9] CEO 画面: 「🔌 連携を外す」ボタンの配線を JS エンジンで動かす (確認で止められる・POST 先・成功で行を未連携に書き換え・
      ② に出ていたコードを「無効」に差し替え・発行済みの印を消す・ほかの結果 (OTP など) は消さない・失敗でボタンを戻す)・
      連携済みのコード発行は案内だけ・入塾承認は連携済みの生徒にコードを出さず、メールに「1つだけ」・マイページの案内・CI 登録

★外部通信なし (LINE API は偽物)・DB は一時 SQLite・生徒名とメールは架空 (公開リポジトリ)。
★JS エンジン (node / osascript / jsc) が無ければ FAIL (飛ばさない)。

実行:
    python3 scripts/health_check/test_line_bind_guard.py
    # exit 0 = PASS / 1 = FAIL
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
CEO_HTML = os.path.join(REPO, "ceo.html")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc"
sys.path.insert(0, os.path.join(REPO, "server"))
CRON = "test-cron-secret-line-bind"
FAILURES = []

CHILD = "U" + "c" * 32       # 子どもの LINE (架空)
PARENT = "U" + "p" * 32      # 保護者の LINE (架空)
CHILD_NEW = "U" + "n" * 32   # 機種変更後の子どもの LINE (架空)
SIBLING = "U" + "s" * 32     # 別の生徒の LINE (架空)
PARENT_B = "U" + "q" * 32    # 生徒B の保護者の LINE (架空・PARENT とは別の人)


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="line_bind_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        "DATABASE_URL": "",   # ★空にしないと本番 Postgres を見る
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "CRON_SECRET": CRON,
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_line_bind", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def mk(mod, name, email, line_user_id=None):
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO students (name, email, status, line_user_id) VALUES (?,?,?,?)", (name, email, "paid", line_user_id))
    conn.commit()
    c.execute("SELECT id FROM students WHERE email = ?", (email,))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


def line_of(mod, sid):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT line_user_id FROM students WHERE id = ?", (sid,))
    r = c.fetchone()
    conn.close()
    return r["line_user_id"] if r else "<no row>"


def set_line(mod, sid, uid):
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET line_user_id = ? WHERE id = ?", (uid, sid))
    conn.commit(); conn.close()


def used_at(mod, code):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT used_at FROM line_link_tokens WHERE token = ?", (code,))
    r = c.fetchone()
    conn.close()
    return r["used_at"] if r else "<no row>"


class FakeLine:
    """_line_api_call の偽物。送った先 (reply / push) と本文を覚える。"""
    def __init__(self):
        self.calls = []

    def __call__(self, endpoint, body):
        self.calls.append((endpoint, body))
        return True

    def texts(self):
        return [m.get("text") for _, b in self.calls for m in (b.get("messages") or [])]

    def endpoints(self):
        return [e for e, _ in self.calls]


_EV = [0]


def send(mod, fake, uid, text):
    fake.calls.clear()
    _EV[0] += 1
    mod._handle_line_event({"type": "message", "replyToken": f"rt-{_EV[0]}", "webhookEventId": f"ev-{_EV[0]}",
                            "source": {"type": "user", "userId": uid}, "message": {"type": "text", "text": text}})
    return fake.texts()


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
async function flush(n) { for (var i = 0; i < (n || 200); i++) await Promise.resolve(); }
"""

# ceo.html の「🔌 連携を外す」の配線 (本物のブロック) を偽の DOM で動かす。BLOCK は Python が差し込む。
JS_UNLINK = r"""
function makeEnv(opts) {
  var env = { alerts: [], confirms: [], fetches: [], applied: [], cellHtml: null };
  var cell = { set innerHTML(v) { env.cellHtml = v; }, get innerHTML() { return env.cellHtml; } };
  var listeners = {};
  env.issueBtn = { dataset: opts.issued ? { issued: '1' } : {} };
  env.helpBox = { style: { display: opts.helpShown ? 'block' : 'none' }, innerHTML: opts.helpHtml || '',
                  querySelector: function (sel) { return sel === '.sd-line-copy' && /sd-line-copy/.test(env.helpBox.innerHTML) ? {} : null; } };
  var btn = { dataset: { studentId: String(opts.sid) }, style: {}, disabled: false,
              addEventListener: function (t, f) { listeners[t] = f; },
              closest: function (sel) { return sel === '.sd-line-state' ? cell : null; } };
  env.btn = btn; env.click = function () { return listeners.click(); };
  env.infoPane = { querySelectorAll: function (sel) { return sel === '.sd-line-unlink-btn' ? [btn] : []; },
                   querySelector: function (sel) { return sel === '.sd-issue-linelink-btn' ? env.issueBtn : sel === '.sd-login-help-result' ? env.helpBox : null; } };
  env.st = { id: opts.sid, name: 'テスト生徒', has_line: true };
  env.confirm = function (m) { env.confirms.push(m); return opts.confirm; };
  env.alert = function (m) { env.alerts.push(String(m)); };
  env.AdminAuth = { fetch: function (url, init) {
    env.fetches.push({ url: url, method: init && init.method });
    if (opts.throwFetch) return Promise.reject(new Error('network down'));
    return Promise.resolve({ ok: opts.status === 200, status: opts.status, json: function () { return Promise.resolve(opts.body); } });
  } };
  env._applySavedToStudent = function (sid, st, patch) { env.applied.push([sid, patch]); Object.assign(st, patch); };
  return env;
}
function wire(env) {
  (new Function('infoPane', 'st', 'confirm', 'alert', 'AdminAuth', '_applySavedToStudent', BLOCK))(
    env.infoPane, env.st, env.confirm, env.alert, env.AdminAuth, env._applySavedToStudent);
}
(async function () {
  // 確認で「キャンセル」→ 何も送らない
  var e0 = makeEnv({ sid: 42, confirm: false, status: 200, body: {} });
  wire(e0); await e0.click(); await flush();
  eq('キャンセルなら POST しない', e0.fetches.length, 0);
  ok('確認の文言に生徒名と「未使用の連携コードはすべて無効」がある', /テスト生徒/.test(e0.confirms[0] || '') && /未使用の連携コードはすべて無効/.test(e0.confirms[0] || ''), e0.confirms);

  // 成功 → POST /api/admin/students/42/line-unlink・行を未連携に・has_line=false
  var e1 = makeEnv({ sid: 42, confirm: true, status: 200,
                     body: { ok: true, was_linked: true, student: { id: 42, name: 'テスト生徒' }, message: 'LINE 連携を外しました。' } });
  wire(e1); await e1.click(); await flush();
  eq('POST 先', e1.fetches, [{ url: '/api/admin/students/42/line-unlink', method: 'POST' }]);
  eq('名簿の has_line を false に', e1.applied, [[42, { has_line: false }]]);
  ok('行を「未連携」に書き換え、② 連携コードを発行 へ案内', /未連携/.test(e1.cellHtml || '') && /連携コードを発行/.test(e1.cellHtml || ''), e1.cellHtml);
  ok('サーバの message を alert で出す', e1.alerts.length === 1 && /外しました/.test(e1.alerts[0]), e1.alerts);
  ok('確認の文言に「保護者も受け取りたい」では外さない・誤って外したときの戻し方', /保護者も受け取りたい/.test(e1.confirms[0] || '') && /元の LINE から送って/.test(e1.confirms[0] || ''), e1.confirms);

  // ② にコードが出ていた → 外したら「無効」に差し替え・発行済みの印を消す
  var e5 = makeEnv({ sid: 42, confirm: true, status: 200, issued: true, helpShown: true,
                     helpHtml: '<div>XXXXCODE</div><button class="sd-line-copy">📋</button>',
                     body: { ok: true, was_linked: true, student: { id: 42 }, message: 'ok' } });
  wire(e5); await e5.click(); await flush();
  ok('② に出ていたコードを消し「無効」と出す', !/XXXXCODE/.test(e5.helpBox.innerHTML) && /無効/.test(e5.helpBox.innerHTML), e5.helpBox.innerHTML);
  ok('② の「発行済み」の印を消す (押し直しで「前のコードを使って」と出さない)', !('issued' in e5.issueBtn.dataset), e5.issueBtn.dataset);
  // 結果欄に出ていたのが OTP などコード以外なら消さない
  var e6 = makeEnv({ sid: 42, confirm: true, status: 200, helpShown: true, helpHtml: '<div>OTP 123456</div>',
                     body: { ok: true, was_linked: true, student: { id: 42 }, message: 'ok' } });
  wire(e6); await e6.click(); await flush();
  eq('結果欄が LINE のコード以外なら触らない', e6.helpBox.innerHTML, '<div>OTP 123456</div>');

  // 失敗 (401) → 行は変えない・ボタンを戻す
  var e2 = makeEnv({ sid: 42, confirm: true, status: 401, body: { detail: '未認証' } });
  wire(e2); await e2.click(); await flush();
  eq('失敗では行を書き換えない', e2.cellHtml, null);
  eq('失敗では has_line を変えない', e2.applied, []);
  ok('失敗でボタンを押せる状態に戻す', e2.btn.disabled === false, e2.btn.disabled);
  ok('失敗の理由 (detail) を出す', e2.alerts.length === 1 && /未認証/.test(e2.alerts[0]), e2.alerts);

  // 通信エラー → ボタンを戻す
  var e3 = makeEnv({ sid: 42, confirm: true, throwFetch: true, status: 0, body: {} });
  wire(e3); await e3.click(); await flush();
  ok('通信エラーでボタンを戻す', e3.btn.disabled === false && e3.cellHtml === null, [e3.btn.disabled, e3.cellHtml]);

  // サーバが別の生徒を返した → 行を書き換えない
  var e4 = makeEnv({ sid: 42, confirm: true, status: 200, body: { ok: true, student: { id: 7 } } });
  wire(e4); await e4.click(); await flush();
  ok('生徒が食い違えば行を書き換えない', e4.cellHtml === null && e4.applied.length === 0, [e4.cellHtml, e4.applied]);
  __emit();
})().catch(function (e) { ok('JS が例外なく走った', false, String(e && e.stack || e)); __emit(); });
"""


def run_js(engine, program, label):
    with tempfile.TemporaryDirectory(prefix="line_bind_js_") as td:
        path = os.path.join(td, "case.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(program)
        try:
            r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=120)
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
    print("🔒 LINE 連携の付け替え防止・管理者が連携を外す (2026-10-23) 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    fake = FakeLine()
    mod._line_api_call = fake
    LINKED_OTHER = mod._LINE_STUDENT_LINKED_OTHER

    print("[1] 再現: 子どもが連携済みのところへ保護者の LINE からコード")
    A = mk(mod, "テスト生徒A", "parent-a@example.invalid")
    code_child = mod._create_line_link_token(A)
    texts = send(mod, fake, CHILD, code_child)
    check("子どもが先に連携できる", line_of(mod, A) == CHILD and any("連携が完了" in t for t in texts), texts)
    code_parent = mod._create_line_link_token(A)   # 承認メールやマイページで保護者が手にするコード
    texts = send(mod, fake, PARENT, code_parent)
    check("子どもの連携は保護者の LINE に書き換わらない", line_of(mod, A) == CHILD, line_of(mod, A))
    check("保護者には「別の LINE と連携済み・塾に連絡」を返す", texts == [LINKED_OTHER], texts)
    check("返事は reply 1 回だけ (push なし)", fake.endpoints() == ["message/reply"], fake.endpoints())
    check("保護者のコードは消費しない (taken と同じ)", used_at(mod, code_parent) is None, used_at(mod, code_parent))
    check("文言: 1つだけ・お子さまのLINEならそのまま・名前を添えて塾に連絡", "塾にご連絡" in LINKED_OTHER and "1つだけ" in LINKED_OTHER
          and "別のLINE" in LINKED_OTHER and "お子さまのLINE" in LINKED_OTHER and "お名前" in LINKED_OTHER, LINKED_OTHER)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT props, session_id FROM events WHERE name = 'line_bind_refused' ORDER BY id")
    refused = [dict(r) for r in c.fetchall()]; conn.close()
    check("断った記録 events.line_bind_refused が 1 行 (生徒 id・経路 pre)", len(refused) == 1
          and json.loads(refused[0]["props"]) == {"student_id": A, "stage": "pre"}, refused)
    check("断った記録に LINE の userId を残さない・session_id は生徒 ID にしない", bool(refused) and PARENT not in refused[0]["props"]
          and PARENT[-6:] not in refused[0]["props"] and refused[0]["session_id"] == "line_webhook", refused)
    # 同じコードをもう一度送っても同じ (繰り返しで付け替わらない)
    texts = send(mod, fake, PARENT, code_parent)
    check("保護者がもう一度送っても付け替わらない", line_of(mod, A) == CHILD and texts == [LINKED_OTHER], texts)

    print("\n[2] 同じ LINE からの送り直し・未連携の生徒")
    code_again = mod._create_line_link_token(A)
    texts = send(mod, fake, CHILD, code_again)
    check("連携済みの LINE が新しいコードを送ると連携完了 (冪等)", line_of(mod, A) == CHILD and any("連携が完了" in t for t in texts), texts)
    check("そのコードは消費される", used_at(mod, code_again) is not None)
    B = mk(mod, "テスト生徒B", "parent-b@example.invalid")
    texts = send(mod, fake, PARENT_B, mod._create_line_link_token(B))
    check("未連携の生徒は最初に送った LINE で連携できる (保護者でも)", line_of(mod, B) == PARENT_B and any("連携が完了" in t for t in texts), texts)
    E = mk(mod, "テスト生徒E", "parent-e@example.invalid", line_user_id="")
    texts = send(mod, fake, SIBLING, mod._create_line_link_token(E))
    check("line_user_id が空文字の生徒も未連携として連携できる", line_of(mod, E) == SIBLING, line_of(mod, E))

    print("\n[3] 1 つの LINE は 1 人の生徒だけ (taken)")
    C = mk(mod, "テスト生徒C", "parent-c@example.invalid")
    code_c = mod._create_line_link_token(C)
    texts = send(mod, fake, CHILD, code_c)   # 生徒A の LINE が 生徒C のコードを送る
    check("別の生徒に連携済みの LINE は使えない", line_of(mod, C) is None and texts and "既に別の生徒アカウント" in texts[0], texts)
    check("taken でもコードは消費しない", used_at(mod, code_c) is None)

    print("\n[4] _bind_line_user の直接呼び出し・race")
    check("連携済みの生徒に別の LINE → linked_other", mod._bind_line_user(A, PARENT) == "linked_other")
    check("…そして上書きしない", line_of(mod, A) == CHILD, line_of(mod, A))
    check("同じ LINE → ok", mod._bind_line_user(A, CHILD) == "ok" and line_of(mod, A) == CHILD)
    check("別の生徒に連携済みの LINE → taken", mod._bind_line_user(C, CHILD) == "taken" and line_of(mod, C) is None)
    check("生徒が無い → missing", mod._bind_line_user(999999, "U" + "z" * 32) == "missing")
    # webhook の事前判定を通ったあとに別の LINE が先に連携した (race) を、事前判定だけ素通りさせて再現する
    D = mk(mod, "テスト生徒D", "parent-d@example.invalid", line_user_id=CHILD_NEW)
    code_d = mod._create_line_link_token(D)
    orig_pre = mod._line_student_linked_other
    mod._line_student_linked_other = lambda sid, uid: False
    try:
        texts = send(mod, fake, PARENT + "x", code_d)
    finally:
        mod._line_student_linked_other = orig_pre
    check("race: 事前判定を抜けても UPDATE が上書きしない", line_of(mod, D) == CHILD_NEW, line_of(mod, D))
    check("race: 返事は同じ「別の LINE と連携済み」", texts == [LINKED_OTHER], texts)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT props FROM events WHERE name = 'line_bind_refused' ORDER BY id DESC LIMIT 1")
    r_last = c.fetchone(); conn.close()
    check("race: 断った記録 (経路 race)", bool(r_last) and json.loads(r_last["props"]) == {"student_id": D, "stage": "race"}, r_last and r_last["props"])

    print("\n[5] 管理 API POST /api/admin/students/{id}/line-unlink")
    url = f"/api/admin/students/{A}/line-unlink"
    r = client.post(url)
    check("認証なしは 401", r.status_code == 401, r.status_code)
    r = client.post(url, headers={"Authorization": "Bearer not-a-token"})
    check("偽のトークンは 401", r.status_code == 401, r.status_code)
    r = client.post(url, headers={"X-Cron-Secret": "wrong"})
    check("違う X-Cron-Secret は 401", r.status_code == 401, r.status_code)
    check("401 のあいだは外れていない", line_of(mod, A) == CHILD)
    admin = mod._sign_admin_token()["token"]
    r = client.post("/api/admin/students/999999/line-unlink", headers={"Authorization": "Bearer " + admin})
    check("生徒が無ければ 404", r.status_code == 404, r.status_code)
    # A の未使用コード: code_parent (保護者)・下で 1 つ足す。使用済み: code_child, code_again。C のコード (code_c) は他の生徒
    extra = mod._create_line_link_token(A)
    r = client.post(url, headers={"Authorization": "Bearer " + admin})
    j = r.json() if r.status_code == 200 else {}
    check("admin Bearer で外せる", r.status_code == 200 and j.get("ok") is True and j.get("was_linked") is True, (r.status_code, j))
    check("連携が外れる (NULL)", line_of(mod, A) is None, line_of(mod, A))
    check("この生徒の未使用コードを全部無効 (2 件)", j.get("invalidated_codes") == 2 and used_at(mod, code_parent) is not None
          and used_at(mod, extra) is not None, j)
    check("他の生徒の未使用コードは触らない", used_at(mod, code_c) is None)
    check("応答に生徒 id と名前", (j.get("student") or {}).get("id") == A)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT props, session_id FROM events WHERE name = 'line_unlinked' ORDER BY id DESC LIMIT 1")
    ev = c.fetchone(); conn.close()
    props = json.loads(ev["props"]) if ev else {}
    check("記録 events.line_unlinked (admin_action・生徒 id・件数)", bool(ev) and ev["session_id"] == "admin_action"
          and props.get("student_id") == A and props.get("invalidated_codes") == 2, props)
    check("記録に LINE の userId を残さない", bool(ev) and CHILD not in ev["props"] and CHILD[-6:] not in ev["props"], ev and ev["props"])
    _at = mod._parse_db_dt(props.get("at")) if props.get("at") else None
    check("記録の at は無効にしたコードの used_at と同じ時刻 (診断の reason=used と見分ける・時刻として比べる)", _at is not None
          and _at == mod._parse_db_dt(used_at(mod, code_parent)) == mod._parse_db_dt(used_at(mod, extra))
          and _at == mod._parse_db_dt(str(used_at(mod, code_parent)).replace("T", " ")), (props.get("at"), used_at(mod, code_parent)))
    check("診断 API は無効にしたコードを used と返す", mod._line_link_token_status(code_parent).get("reason") == "used")
    r = client.post(url, headers={"X-Cron-Secret": CRON})
    j2 = r.json() if r.status_code == 200 else {}
    check("X-Cron-Secret でも呼べる・2 回目は was_linked=false", r.status_code == 200 and j2.get("was_linked") is False
          and j2.get("invalidated_codes") == 0, (r.status_code, j2))

    print("\n[6] 外したあと (機種変更の救済)")
    texts = send(mod, fake, PARENT, code_parent)
    check("保護者の古いコードは無効 (先取りできない)", line_of(mod, A) is None and texts and "無効" in texts[0], texts)
    new_code = mod._create_line_link_token(A)
    texts = send(mod, fake, CHILD_NEW + "a", new_code)
    check("新しいコードを新しい LINE から送ると連携できる", line_of(mod, A) == CHILD_NEW + "a" and any("連携が完了" in t for t in texts), texts)

    print("\n[7] issue-line-link の案内")
    def n_tokens(sid):
        conn = mod.db(); c = conn.cursor()
        c.execute("SELECT COUNT(*) AS n FROM line_link_tokens WHERE student_id = ?", (sid,))
        n = c.fetchone()["n"]; conn.close()
        return n
    before = n_tokens(A)
    r = client.post("/api/admin/students/issue-line-link", json={"student_id": A}, headers={"Authorization": "Bearer " + admin})
    j = r.json() if r.status_code == 200 else {}
    check("連携済みなら already_linked と「先に外す」の案内", j.get("already_linked") is True and "連携を外す" in (j.get("already_linked_note") or ""), j)
    check("連携済みならコードを出さない (行も作らない)", j.get("code") is None and n_tokens(A) == before, (j.get("code"), n_tokens(A), before))
    r = client.post("/api/admin/students/issue-line-link", json={"student_id": C}, headers={"Authorization": "Bearer " + admin})
    j = r.json() if r.status_code == 200 else {}
    check("未連携ならコードを出し、already_linked_note は None", j.get("already_linked") is False and j.get("already_linked_note") is None
          and bool(j.get("code")) and mod._peek_line_link_token(j.get("code")) == C, j)

    print("\n[8] 連携済みの LINE が使用済みのコードを送り直す")
    texts = send(mod, fake, CHILD, code_child)   # code_child は使用済み・CHILD は今は誰にも連携していない
    check("どこにも連携していない LINE の使用済みコード → 無効の案内", texts and "無効" in texts[0], texts)
    texts = send(mod, fake, CHILD_NEW + "a", new_code)
    check("連携済みの LINE の使用済みコード → 「すでに連携済み」", texts and "すでに連携済み" in texts[0], texts)

    print("\n[9] CEO 画面とソース")
    ceo = read(CEO_HTML)
    m = re.search(r"\n(\s*// 🔌 2026-10-23: LINE 連携を外す.*?)\n\s*// 🎯 2026-05-26 audit fix: 学年/志望校", ceo, re.S)
    check("ceo.html に「🔌 連携を外す」の配線ブロックがある", bool(m))
    check("連携済みの行に sd-line-unlink-btn ボタン (sd-line-state の中)", 'class="sd-line-unlink-btn"' in ceo and 'class="sd-line-state"' in ceo)
    check("コード発行: 連携済み (コードなし) は案内だけ出して戻る", "if (d.already_linked && !d.code) {" in ceo and "d.already_linked_note" in ceo)
    mp = read(os.path.join(REPO, "mypage.html"))
    check("マイページの LINE 連携の案内に「1つだけ」", "連携できる LINE は1つだけです" in mp)
    eng = js_engine()
    print(f"  JS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng))
    if m and eng:
        run_js(eng, JS_PRELUDE + "var BLOCK = " + json.dumps(m.group(1)) + ";\n" + JS_UNLINK, "CEO 連携を外す")
    src = read(MAIN_PY)
    fn = src[src.index("def _bind_line_user"):src.index("_LINE_BG_TASKS: set")]
    check("_bind_line_user の UPDATE は未連携か同じ LINE のときだけ (WHERE)", "line_user_id IS NULL OR line_user_id = '' OR line_user_id = ?" in fn)
    ap = src[src.index("# 📲 [LINE受信案内 2026-06-26]"):src.index("# magic link 送信 (welcome + ログイン link)")]
    check("入塾承認: 連携済みの生徒にはコードを出さない (line_user_id を見てから発行)", "SELECT line_user_id FROM students WHERE id = ?" in ap
          and ap.index("SELECT line_user_id") < ap.index("_create_line_link_token("), ap[:200])
    mail = src[src.index("# 📲 LINEで受け取る案内 (メールが届きにくい方向け・両コース共通)"):][:900]
    check("入塾承認メール: 連携できる LINE は1つだけ・お子さまに渡す", "連携できる LINE は1つだけ" in mail and "お子さま" in mail)
    ci = read(CI_YML)
    check("CI (server-tests.yml) に登録", "scripts/health_check/test_line_bind_guard.py" in ci)

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
