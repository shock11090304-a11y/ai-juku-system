#!/usr/bin/env python3
"""💾 単元ドリルの解答の途中保存 (2026-10-18 塾長「②の残りも作っておいて」= 成績を上げる提案 ②「解答を途中で保存できるようにします。
保存は端末の中だけです」) の回帰テスト。共通部品 gd-draft.js・塾生アプリ (class.html の gdOpen / gdSubmit)・マイページ (mypage.js の openDrill)。

背景: 単元ドリル (クラス自動宿題・3日ドリル・塾長のドリル) は全問に答えないと提出できず、選んだ答えは画面の中にしか無かった
  (class.html の旧コメント「解答中に戻ると選んだ答えは消える (下書き保存は無い)」)。スマホで LINE を見に行ってタブが読み直されると全部消え、
  未提出のまま次の配信も止まる。記号の解答用紙 (hw-sheet.js) の下書きは塾長の宿題だけで、ドリルには効いていなかった。

★サーバとの約束を本物で確かめる: 一時 SQLite の本物のサーバでドリルを配り、GET の本物の応答 (question_id・stem・choices) を画面のテストに入れる。
  画面が下書きから戻した答えで送った提出の本文は、本物のサーバに送り直して 200・選んだとおりに採点されるかを見る。
  二重提出は本物の 409 の応答を入れる。

固定する性質:
  [1] gd-draft.js: 保存 / 戻す / 消す・キーは 'aj_gd_draft_v1:<生徒ID>:<ドリルID>' (中身は選んだ番号と指紋だけ = 名前・正解なし)・
      問題文 / 選択肢を直した問・選択肢の数を超える番号・今の問題に無い ID は戻さない・60 日より古い下書きは使わず保存のときに消す・
      生徒 ID が無ければ localStorage を使わない・throw する端末はページ内だけ ('memory')・何も答えていなければ消す ('empty')・
      壊れた値・progress / progressLabel (途中 2/3)・canPersist・自信なしの問題 ID・ES5
  [2] 塾生アプリ (class.html の inline script を偽の DOM と本物のサーバの応答で): 選ぶたびに保存・「💾 答えはこの端末に自動で保存されます」・
      「← 宿題一覧に戻る」は確認せずに戻ってトースト・カードに「💾 途中 2/3」と「▶ 続きから解く」・読み直したページで開き直すと戻る (選んだ印も)・
      直された問だけ戻さない・通信に失敗した提出は残す・提出できたら消す・送る本文はサーバが受け付ける (選んだとおりに採点)・
      409 (提出ずみ) は消して提出ずみの画面・提出ずみのドリルを開いたら消す・別の生徒には出さない・保存できない端末はページ内だけ
      (案内を出さず、戻るトーストも「このページを閉じるまで」)・gd-draft.js が読めない端末は今までどおり (戻るときに確認)
  [3] マイページ (mypage.js の解答エリア・宿題欄): 選ぶたび (自信なしも) に保存・開き直すと戻る (「💾 前に答えた N 問を戻しました」)・
      提出できたら消す・通信失敗は残す・409 は消して提出ずみの画面・カードに「💾 途中 2/10」と「▶ 続きから解く」
  [4] ソース検査: gd-draft.js の ?v= が 2 ページでそろう・読み込み順・CI 登録と paths

★JS エンジンが無ければ FAIL (飛ばさない)。CI (ubuntu) は node、塾長の Mac は osascript -l JavaScript。AJ_JS_ENGINE で選べる。
  生徒名・メールは架空 (公開リポジトリ)。外部通信は一切しない。DB は一時 SQLite。

実行:
    python3 scripts/health_check/test_drill_draft.py
    # exit 0 = PASS / 1 = FAIL
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")
GD_JS = os.path.join(REPO, "gd-draft.js")
HW_JS = os.path.join(REPO, "hw-notice.js")
CLASS_HTML = os.path.join(REPO, "class.html")
MYPAGE_HTML = os.path.join(REPO, "mypage.html")
MYPAGE_JS = os.path.join(REPO, "mypage.js")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
HW_NOTICE_TEST = os.path.join(HERE, "test_hw_notice_js.py")

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:500]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------------------------------------------
# 本物のサーバ (一時 SQLite) でドリルを配り、画面に渡す応答を作る
def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="drill_draft_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "", "ANTHROPIC_API_KEY": "", "BASE_URL": "https://example.invalid",
    })
    mod = load_module("aijuku_main_drill_draft", MAIN_PY)
    mod.init_db()
    return mod


def ex(mod, sql, params=()):
    conn = mod.db()
    c = conn.cursor()
    c.execute(sql, params)
    rid = None
    try:
        r = c.fetchone()
        rid = r[0] if r is not None else None
    except Exception:
        rid = None
    conn.commit()
    conn.close()
    return rid


class Server:
    def __init__(self):
        self.mod = load_main()
        from fastapi.testclient import TestClient
        self.client = TestClient(self.mod.app)
        mod = self.mod
        self.sid = ex(mod, "INSERT INTO students (name, email, status, grade, ai_disabled, plan, last_login_at) "
                           "VALUES (?, ?, 'paid', '高2', 1, 'student_addon', '2026-10-18 01:00:00') RETURNING id",
                      ("架空 途中保存", "drill-draft-a@example.org"))
        mod._AI_DISABLED_CACHE.pop(self.sid, None)
        self.tok = {"Authorization": "Bearer " + mod._sign_session_token(self.sid)}
        # 3 問 (正解は 1・2・0)。choices は 4 択
        self.answers = {}
        self.qids = []
        for i, (stem, ans) in enumerate([("架空 時制 ( ) 1", 1), ("架空 時制 ( ) 2", 2), ("架空 時制 ( ) 3", 0)]):
            qid = ex(mod, "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                          "VALUES ('english', '時制', 'standard', ?, ?, ?, '架空の解説', 'manual-drill-v1') RETURNING id",
                     (stem, json.dumps([f"選択肢{i}-a", f"選択肢{i}-b", f"選択肢{i}-c", f"選択肢{i}-d"], ensure_ascii=False), ans))
            self.qids.append(qid)
            self.answers[str(qid)] = ans
        self.d_open = self.drill("【月曜2限 英文法 Lv.1】宿題 時制（3問・〆10/20）", "class_hw_auto:kosei:月曜2限 英文法 Lv.1")
        self.d_done = self.drill("塾長のドリル 済み", "admin")
        ex(mod, "INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at, score_total) VALUES (?, ?, 'open', '2026-10-17 21:00:05', 3)",
           (self.d_open, self.sid))
        ex(mod, "INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at, score_total, score_correct, answers_json, completed_at) "
                "VALUES (?, ?, 'completed', '2026-10-16 21:00:05', 3, 2, ?, '2026-10-17 01:00:00')",
           (self.d_done, self.sid, json.dumps({str(self.qids[0]): 1, str(self.qids[1]): 2, str(self.qids[2]): 3})))

    def drill(self, title, created_by):
        return ex(self.mod, "INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) "
                            "VALUES ('english', ?, '時制', 'standard', ?, ?) RETURNING id",
                  (title, json.dumps(self.qids), created_by))

    def fixtures(self):
        print("[0] 本物のサーバ (一時 SQLite) でドリルを配り、画面に渡す応答を作る")
        c = self.client
        g_open = c.get(f"/api/student/grammar-drill/{self.d_open}", headers=self.tok)
        g_done = c.get(f"/api/student/grammar-drill/{self.d_done}", headers=self.tok)
        lst = c.get("/api/student/grammar-drills", headers=self.tok)
        dup = c.post(f"/api/student/grammar-drill/{self.d_done}/submit", headers=self.tok,
                     json={"answers": {str(q): 0 for q in self.qids}})
        check("GET (未提出) は 200・3 問・question_id / stem / choices がある (正解は届かない)",
              g_open.status_code == 200 and len(g_open.json().get("questions") or []) == 3
              and all({"question_id", "stem", "choices"} <= set(q) and "answer" not in q for q in g_open.json()["questions"]),
              (g_open.status_code, g_open.text[:300]))
        check("GET (提出ずみ) は 200・status completed", g_done.status_code == 200 and g_done.json().get("status") == "completed", g_done.text[:200])
        check("一覧は 200", lst.status_code == 200, lst.text[:200])
        check("提出ずみに出し直すと本物の 409", dup.status_code == 409, (dup.status_code, dup.text[:200]))
        return {
            "sid": self.sid, "d_open": self.d_open, "d_done": self.d_done,
            "get_open": g_open.json(), "get_done": g_done.json(),
            "list": lst.json(),
            "dup": {"status": dup.status_code, "body": dup.json()},
            "qids": [str(q) for q in self.qids],
        }

    def submit(self, body):
        return self.client.post(f"/api/student/grammar-drill/{self.d_open}/submit", headers=self.tok, json=body)


# ---------------------------------------------------------------------------------------------------------------
def load_harness():
    spec = importlib.util.spec_from_file_location("hw_notice_js_harness_drill_draft", HW_NOTICE_TEST)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run_js(engine, program, label):
    """OK / NG / DONE の行を判定に、DATA <json> の行を返す (画面が送った本文をサーバに送り直すため)"""
    with tempfile.TemporaryDirectory(prefix="drill_draft_js_") as td:
        path = os.path.join(td, "case.js")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(program)
        env = dict(os.environ)
        env["TZ"] = "America/Los_Angeles"
        try:
            r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=180, env=env)
        except Exception as e:  # noqa: BLE001
            check(f"{label}: JS を実行できた", False, f"{type(e).__name__}: {e}")
            return []
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    lines = [ln for ln in text.split("\n") if ln.startswith(("OK  ", "NG  ", "DONE ", "DATA "))]
    done = [ln for ln in lines if ln.startswith("DONE ")]
    if r.returncode != 0 or not done:
        check(f"{label}: JS が最後まで走った (exit {r.returncode})", False, text[-1500:])
        return []
    data = []
    for ln in lines:
        if ln.startswith("OK  "):
            check(ln[4:], True)
        elif ln.startswith("NG  "):
            check(ln[4:], False, ln[4:])
        elif ln.startswith("DATA "):
            try:
                data.append(json.loads(ln[5:]))
            except Exception:  # noqa: BLE001
                check(f"{label}: DATA の行を読めた", False, ln[:200])
    check(f"{label}: {int(done[-1].split()[1])} 件の検査を実行", int(done[-1].split()[1]) > 0)
    return data


# DATA の行を出す (__emit の前に __out へ入れる)
JS_DATA = r"""
function __data(o) { __out.push('DATA ' + JSON.stringify(o)); }
"""

# ---------------------------------------------------------------------------------------------------------------
# [1] gd-draft.js の部品
JS_PURE = r"""
__loadGdDraft();
var G = window.AJGdDraft;
var st = memStore(); G._useStorage(st); G._clearMemory();
var Q = SRV.get_open.questions, D = String(SRV.d_open), K = 'aj_gd_draft_v1:7:' + D;
var q0 = String(Q[0].question_id), q1 = String(Q[1].question_id), q2 = String(Q[2].question_id);
var a = {}; a[q0] = 1; a[q1] = 3;
eq('保存: この端末に (stored)', G.save('7', D, Q, a, [q1]), 'stored');
var rec = JSON.parse(st._m[K] || 'null');
ok('キーは aj_gd_draft_v1:<生徒ID>:<ドリルID>', !!rec, Object.keys(st._m));
eq('中身は問題数・答えた数・選んだ番号 (と指紋)・自信なし・時刻だけ', rec && Object.keys(rec).sort(), ['a', 'at', 'n', 't', 'u', 'v']);
ok('名前・正解・問題文は入れない', String(st._m[K]).indexOf('架空') < 0 && String(st._m[K]).indexOf('選択肢') < 0 && String(st._m[K]).indexOf('answer') < 0, st._m[K]);
var L = G.load('7', D, Q);
eq('戻す: 答え 2 問・自信なし 1 問・問題数 3', L && [L.answers, L.unsure, L.n, L.t], [a, (function () { var u = {}; u[q1] = 1; return u; })(), 2, 3]);
eq('progress / progressLabel: 途中 2/3', [G.progress('7', D), G.progressLabel(G.progress('7', D))], [{ n: 2, t: 3 }, '途中 2/3']);
eq('progressLabel: 問題数が分からなければ「途中 N 問」・無ければ空', [G.progressLabel({ n: 4, t: 0 }), G.progressLabel(null), G.progressLabel({ n: 0, t: 3 })], ['途中 4 問', '', '']);
eq('別の生徒・別のドリルには出さない', [G.load('8', D, Q), G.progress('8', D), G.load('7', '999999', Q)], [null, null, null]);
// 問題を直した (問題文) → その問だけ戻さない
var Q2 = JSON.parse(JSON.stringify(Q)); Q2[1].stem = Q2[1].stem + '（直した）';
var L2 = G.load('7', D, Q2);
eq('問題文を直した問は戻さない (ほかの問は戻す)', L2 && L2.answers, (function () { var o = {}; o[q0] = 1; return o; })());
var Q3 = JSON.parse(JSON.stringify(Q)); Q3[0].choices[2] = '直した選択肢';
eq('選択肢を直した問も戻さない', (G.load('7', D, Q3) || {}).answers, (function () { var o = {}; o[q1] = 3; return o; })());
var Q4 = JSON.parse(JSON.stringify(Q)); Q4[1].choices = Q4[1].choices.slice(0, 3);
eq('選択肢が減って番号がはみ出す問は戻さない', (G.load('7', D, Q4) || {}).answers, (function () { var o = {}; o[q0] = 1; return o; })());
eq('今の問題に無い ID は戻さない (全部無ければ null)', G.load('7', D, [{ question_id: 1, stem: 'x', choices: ['a', 'b'] }]), null);
var bad = {}; bad[q0] = 9; bad[q2] = 'x'; bad['nope'] = 0;
eq('保存でも範囲外・数でない・知らない ID は捨てる (全部捨てたら消す = empty)', [G.save('7', 'D2', Q, bad, []), st._m['aj_gd_draft_v1:7:D2']], ['empty', undefined]);
eq('何も答えていない保存は消す', [G.save('7', D, Q, {}, []), st._m[K], G.progress('7', D)], ['empty', undefined, null]);
G.save('7', D, Q, a, []);
G.clear('7', D);
eq('clear で消える (ページ内の控えも)', [st._m[K], G.load('7', D, Q)], [undefined, null]);
// 壊れた値
st._m[K] = '{not json'; eq('壊れた値は使わない', [G.load('7', D, Q), G.progress('7', D)], [null, null]);
st._m[K] = JSON.stringify({ v: 2, a: {}, at: Date.now() }); eq('版が違う値は使わない', G.load('7', D, Q), null);
// 60 日
var __now = Date.now;
var T0 = Date.UTC(2026, 9, 18, 1, 0, 0);
Date.now = function () { return T0; };
G._clearMemory(); st = memStore(); G._useStorage(st);
G.save('7', D, Q, a, []);
Date.now = function () { return T0 + 61 * 24 * 3600 * 1000; };
G._clearMemory();
eq('60 日より古い下書きは使わない', [G.load('7', D, Q), G.progress('7', D)], [null, null]);
var st2 = memStore();
st2._m['aj_gd_draft_v1:7:old'] = JSON.stringify({ v: 1, t: 3, n: 1, a: { '1': [0, 'x'] }, u: [], at: T0 });
st2._m['aj_gd_draft_v1:7:broken'] = '{';
st2._m['aj_hw_sheet_v1:7:5'] = 'other';
st2.length = 3; st2.key = function (i) { return Object.keys(st2._m)[i] || null; };
G._useStorage(st2);
G.save('7', D, Q, a, []);
st2.length = Object.keys(st2._m).length;
ok('保存したときに古い・壊れた下書きを消す (ほかのキーは触らない)', !st2._m['aj_gd_draft_v1:7:old'] && !st2._m['aj_gd_draft_v1:7:broken']
   && st2._m['aj_hw_sheet_v1:7:5'] === 'other' && !!st2._m[K], Object.keys(st2._m));
Date.now = __now;
// 生徒 ID が無い・throw する端末
G._clearMemory(); st = memStore(); G._useStorage(st);
eq('生徒 ID が無ければ localStorage を使わない (memory)', [G.save('', D, Q, a, []), Object.keys(st._m).length, G.canPersist('')], ['memory', 0, false]);
ok('…このページの中では戻せる', !!G.load('', D, Q));
var thrower = { getItem: function () { throw new Error('denied'); }, setItem: function () { throw new Error('quota'); }, removeItem: function () { throw new Error('denied'); } };
G._clearMemory(); G._useStorage(thrower);
eq('throw する端末: 保存は memory・canPersist は false・例外を出さない', [G.save('7', D, Q, a, []), G.canPersist('7')], ['memory', false]);
eq('…このページの中では戻せる・progress も出る', [(G.load('7', D, Q) || {}).n, G.progress('7', D)], [2, { n: 2, t: 3 }]);
var r1 = 'ok'; try { G.clear('7', D); } catch (e) { r1 = String(e); }
eq('…clear も例外を出さない', [r1, G.load('7', D, Q)], ['ok', null]);
G._useStorage(null); G._clearMemory();
eq('localStorage が無い端末も memory', G.save('7', D, Q, a, []), 'memory');
G._useStorage(memStore());
eq('canPersist: 書けて消せる端末は true', G.canPersist('7'), true);
eq('自信なしは {ID: true} でも受ける・自信なしだけでも保存', (function () { var u = {}; u[q2] = true; G.save('7', 'D3', Q, {}, u); return G.load('7', 'D3', Q); })(),
   { answers: {}, unsure: (function () { var u = {}; u[q2] = 1; return u; })(), n: 0, t: 3 });
eq('指紋は問題文と選択肢で変わる', [G.fingerprint(Q[0]) === G.fingerprint(JSON.parse(JSON.stringify(Q[0]))), G.fingerprint(Q[0]) === G.fingerprint(Q3[0])], [true, false]);
__emit();
"""

# ---------------------------------------------------------------------------------------------------------------
# [2] class.html (偽の DOM)
JS_CLASS_SETUP2 = r"""
var CONFIRMS = [], CALLSD = [], NETFAIL = {};
window.confirm = function (m) { CONFIRMS.push(String(m)); return true; };
var __baseFetchD = fetch;
fetch = function (url, opts) {
  var path = String(url).replace(/^https?:\/\/[^\/]+/, '');
  CALLSD.push({ path: path, method: (opts && opts.method) || 'GET', body: opts && opts.body });
  if (NETFAIL[path]) return Promise.reject(new TypeError('Failed to fetch'));
  return __baseFetchD(url, opts);
};
window.fetch = fetch;
var FORM = null;
function makeClassForm(html) {
  var f = new FakeEl('gdForm'); f._src = html; f.radios = [];
  var re = /<input type="radio" name="([^"]+)" data-qid="([^"]+)" value="(\d+)">/g, m, blocks = {};
  while ((m = re.exec(html))) {
    var inp = new FakeEl(); inp.type = 'radio'; inp.name = m[1]; inp.value = m[3]; inp.checked = false;
    inp.setAttribute('data-qid', m[2]); inp._label = new FakeEl(); inp._q = blocks[m[2]] || (blocks[m[2]] = new FakeEl());
    inp.closest = function (sel) { return sel === '.gd-choice' ? this._label : (sel === '.gd-q' ? this._q : null); };
    f.radios.push(inp);
  }
  f.querySelectorAll = function (sel) {
    if (sel === 'input[type="radio"]:checked') return f.radios.filter(function (r) { return r.checked; });
    if (sel === 'input[type="radio"]') return f.radios.slice();
    var mm = /^input\[name="([^"]+)"\]$/.exec(sel);
    if (mm) return f.radios.filter(function (r) { return r.name === mm[1]; });
    return [];
  };
  return f;
}
var __baseGet = document.getElementById;
document.getElementById = function (id) {
  if (id === 'gdForm') {
    var hb = ELS.homeworkBody, html = hb ? hb._html : '';
    if (html.indexOf('<div id="gdForm">') < 0) return null;
    if (!FORM || FORM._src !== html) FORM = makeClassForm(html);
    return FORM;
  }
  return __baseGet(id);
};
function wireBody() {
  var hb = new FakeEl('homeworkBody'); ELS.homeworkBody = hb; hb._btns = {};
  hb.querySelectorAll = function (sel) {
    var cls = { '.gd-open': 'gd-open', '.gd-back': 'gd-back' }[sel];
    if (!cls) return [];
    var out = [], re = new RegExp('class="btn btn-[a-z]+ ' + cls + '"(?: data-id="([^"]*)")?', 'g'), m;
    while ((m = re.exec(hb._html))) { var b = new FakeEl(); if (m[1] != null) b.setAttribute('data-id', m[1]); out.push(b); }
    hb._btns[cls] = out;
    return out;
  };
}
function gdBtn(cls, id) { var b = (ELS.homeworkBody._btns[cls] || []); return id == null ? b[0] : b.filter(function (x) { return x.getAttribute('data-id') === String(id); })[0]; }
async function bootD() {
  ELS = {}; TAB_BTNS = ['schedule', 'homework', 'videos', 'messages'].map(function (t) { var b = new FakeEl(); b.setAttribute('data-tab', t); return b; });
  HIST = []; FETCHES = []; TIMERS = []; CALLSD = []; CONFIRMS = []; FORM = null;
  setLoc('/class.html', '?tab=homework', '');
  location.assign = function () {};
  wireBody();
  __bootClass();
  await flush();
}
function pick(qid, idx) {
  var f = document.getElementById('gdForm');
  var t = null;
  f.radios.forEach(function (r) { if (r.getAttribute('data-qid') === String(qid)) { r.checked = (r.value === String(idx)); if (r.checked) t = r; } });
  f.dispatch('change', { target: t });
}
function checkedMap() {
  var f = document.getElementById('gdForm'), o = {};
  if (!f) return null;
  f.radios.forEach(function (r) { if (r.checked) o[r.getAttribute('data-qid')] = Number(r.value); });
  return o;
}
function card(id) { var parts = String(ELS.homeworkBody.innerHTML).split('<div class="card">'); for (var i = 1; i < parts.length; i++) if (parts[i].indexOf('data-id="' + id + '"') >= 0) return parts[i]; return ''; }
function toastText() { return (ELS.toast && ELS.toast.textContent) || ''; }
var LIST_ITEMS = SRV.list.items;
var Q = SRV.get_open.questions, D = String(SRV.d_open), DD = String(SRV.d_done), K = 'aj_gd_draft_v1:7:' + D;
var q0 = String(Q[0].question_id), q1 = String(Q[1].question_id), q2 = String(Q[2].question_id);
function api0() {
  var o = {};
  o['/api/student/homework'] = hwBody([]);
  o['/api/student/grammar-drills'] = { status: 200, body: SRV.list };
  o['/api/student/grammar-drill/' + D] = { status: 200, body: SRV.get_open };
  o['/api/student/grammar-drill/' + DD] = { status: 200, body: SRV.get_done };
  o['/api/student/grammar-drill/' + D + '/submit'] = { status: 200, body: { ok: true, score_correct: 3, score_total: 3, percentage: 100, results: [] } };
  o['/api/student/grammar-drill/' + DD + '/submit'] = SRV.dup;
  return o;
}
"""

JS_CLASS_CASES2 = r"""
(async function () {
  try {
    __loadGdDraft();
    var G = window.AJGdDraft;
    var st = memStore(); G._useStorage(st); G._clearMemory();
    setApi(api0());
    await bootD();
    ok('未提出のドリルのカード: 「▶ 解いて提出する」・途中のチップなし', card(D).indexOf('▶ 解いて提出する') >= 0 && card(D).indexOf('chip-draft') < 0, card(D));
    gdBtn('gd-open', D).dispatch('click'); await flush();
    ok('ドリルを開いた (解答フォーム)', !!document.getElementById('gdForm'));
    ok('「💾 答えはこの端末に自動で保存されます」の案内', String(ELS.homeworkBody.innerHTML).indexOf('💾 答えはこの端末に自動で保存されます（途中でやめても続きから解けます）') >= 0);
    pick(q0, 1);
    var rec = JSON.parse(st._m[K] || 'null');
    ok('選んだらすぐこの端末に保存 (1 問)', !!rec && rec.n === 1 && rec.a[q0][0] === 1, st._m[K]);
    pick(q1, 2);
    eq('2 問目も保存', JSON.parse(st._m[K] || '{}').n, 2);
    ok('選んだ肢に印 (sel)', document.getElementById('gdForm').radios.filter(function (r) { return r.checked; }).every(function (r) { return r._label.classList.contains('sel'); }));
    // 戻る: 確認しない・トースト
    gdBtn('gd-back').dispatch('click'); await flush();
    eq('「← 宿題一覧に戻る」は確認しない (答えは残っている)', CONFIRMS, []);
    ok('…トースト「💾 答えはこの端末に保存しました。続きから解けます」', toastText().indexOf('💾 答えはこの端末に保存しました。続きから解けます') >= 0, toastText());
    ok('一覧のカードに「💾 途中 2/3」と「▶ 続きから解く」', card(D).indexOf('<span class="chip chip-draft">💾 途中 2/3</span>') >= 0 && card(D).indexOf('▶ 続きから解く') >= 0, card(D));
    // ページを読み直す (iOS がタブを捨てた) → 戻る
    G._clearMemory();
    await bootD();
    ok('読み直したページでもカードに「💾 途中 2/3」', card(D).indexOf('💾 途中 2/3') >= 0, card(D));
    gdBtn('gd-open', D).dispatch('click'); await flush();
    var exp = {}; exp[q0] = 1; exp[q1] = 2;
    eq('開き直すと選んだ答えが戻る', checkedMap(), exp);
    ok('…戻した肢にも印 (sel)', document.getElementById('gdForm').radios.filter(function (r) { return r.checked; }).every(function (r) { return r._label.classList.contains('sel'); }));
    ok('…トースト「💾 前に答えた 2 問を戻しました（あと 1 問）」', toastText() === '💾 前に答えた 2 問を戻しました（あと 1 問）', toastText());
    // 通信に失敗した提出は残す
    pick(q2, 0);
    NETFAIL['/api/student/grammar-drill/' + D + '/submit'] = true;
    ELS.gdSubmitBtn.dispatch('click'); await flush();
    ok('通信に失敗した提出は下書きを残す (3 問)', JSON.parse(st._m[K] || '{}').n === 3, st._m[K]);
    ok('…フォームの答えもそのまま', JSON.stringify(checkedMap()) === JSON.stringify((function () { var o = {}; o[q0] = 1; o[q1] = 2; o[q2] = 0; return o; })()));
    NETFAIL = {};
    ELS.gdSubmitBtn.disabled = false;
    ELS.gdSubmitBtn.dispatch('click'); await flush();
    var sub = CALLSD.filter(function (c) { return c.method === 'POST' && c.path === '/api/student/grammar-drill/' + D + '/submit'; });
    eq('提出は 2 回 (失敗 + 成功)', sub.length, 2);
    __data({ kind: 'class_submit', body: JSON.parse(sub[sub.length - 1].body) });
    eq('提出できたら下書きを消す', [st._m[K], G.progress('7', D)], [undefined, null]);
    // 直された問は戻さない
    var D_EDIT = JSON.parse(JSON.stringify(SRV.get_open));
    D_EDIT.questions[1].stem = D_EDIT.questions[1].stem + '（直した）';
    var a2 = {}; a2[q0] = 3; a2[q1] = 1;
    G.save('7', D, Q, a2, null);
    var o2 = api0(); o2['/api/student/grammar-drill/' + D] = { status: 200, body: D_EDIT }; setApi(o2);
    await bootD();
    gdBtn('gd-open', D).dispatch('click'); await flush();
    var exp2 = {}; exp2[q0] = 3;
    eq('塾長が直した問だけ戻さない', checkedMap(), exp2);
    ok('…トースト「前に答えた 1 問を戻しました（あと 2 問）」', toastText() === '💾 前に答えた 1 問を戻しました（あと 2 問）', toastText());
    // 409 (別の端末で提出ずみ) → 消して提出ずみの画面。一覧と GET は開いた時点ではまだ未提出に見える
    var KD = 'aj_gd_draft_v1:7:' + DD;
    var o3 = api0();
    var lst = JSON.parse(JSON.stringify(SRV.list));
    lst.items.forEach(function (x) { if (String(x.drill_id) === DD) x.status = 'open'; });
    o3['/api/student/grammar-drills'] = { status: 200, body: lst };
    o3['/api/student/grammar-drill/' + DD] = { status: 200, body: SRV.get_open };
    setApi(o3);
    await bootD();
    gdBtn('gd-open', DD).dispatch('click'); await flush();
    pick(q0, 2);
    ok('提出ずみのドリル (開いた時点では未提出) にも下書き', !!st._m[KD]);
    o3['/api/student/grammar-drill/' + DD] = { status: 200, body: SRV.get_done }; setApi(o3);
    pick(q1, 1); pick(q2, 1);
    ELS.gdSubmitBtn.dispatch('click'); await flush();
    eq('409 (本物の応答) → 下書きを消す', st._m[KD], undefined);
    ok('…トースト「このドリルは提出ずみです」・提出ずみの画面 (フォームなし)', toastText() === 'このドリルは提出ずみです' && !document.getElementById('gdForm'), toastText());
    // 提出ずみのドリルを開いたら (別の端末で出した) 下書きを消す
    G.save('7', DD, Q, a2, null);
    setApi(api0());
    await bootD();
    ok('提出ずみのカードには途中のチップを出さない', card(DD).indexOf('chip-draft') < 0 && card(DD).indexOf('🔁 解説を見る') >= 0, card(DD));
    gdBtn('gd-open', DD).dispatch('click'); await flush();
    eq('提出ずみのドリルを開いたら下書きを消す', st._m[KD], undefined);
    // 別の生徒 (同じ端末) には出さない
    G.save('7', D, Q, a2, null);
    var __gs = window.AuthGuard.getStudent;
    window.AuthGuard.getStudent = function () { return { id: 8, name: 'テスト生徒B' }; };
    G._clearMemory();
    await bootD();
    ok('別の生徒のカードには途中のチップを出さない', card(D).indexOf('chip-draft') < 0 && card(D).indexOf('▶ 解いて提出する') >= 0, card(D));
    gdBtn('gd-open', D).dispatch('click'); await flush();
    eq('…開いても戻さない', checkedMap(), {});
    window.AuthGuard.getStudent = __gs;
    // 保存できない端末 (throw) はページ内だけ
    var thrower = { getItem: function () { throw new Error('denied'); }, setItem: function () { throw new Error('quota'); }, removeItem: function () { throw new Error('denied'); } };
    G._useStorage(thrower); G._clearMemory();
    await bootD();
    gdBtn('gd-open', D).dispatch('click'); await flush();
    ok('保存できない端末では「この端末に自動で保存」と書かない', String(ELS.homeworkBody.innerHTML).indexOf('この端末に自動で保存') < 0);
    pick(q0, 2);
    gdBtn('gd-back').dispatch('click'); await flush();
    ok('…戻るトーストは「このページを閉じるまで残ります」・確認しない', toastText().indexOf('💾 答えはこのページを閉じるまで残ります') >= 0 && CONFIRMS.length === 0, [toastText(), CONFIRMS]);
    gdBtn('gd-open', D).dispatch('click'); await flush();
    var exp3 = {}; exp3[q0] = 2;
    eq('…同じページで開き直すと戻る', checkedMap(), exp3);
    // gd-draft.js が読めない端末は今までどおり
    var __G = window.AJGdDraft; window.AJGdDraft = undefined;
    await bootD();
    ok('gd-draft.js なし: カードは「▶ 解いて提出する」', card(D).indexOf('▶ 解いて提出する') >= 0 && card(D).indexOf('chip-draft') < 0, card(D));
    gdBtn('gd-open', D).dispatch('click'); await flush();
    ok('gd-draft.js なし: 案内は出さない', String(ELS.homeworkBody.innerHTML).indexOf('💾') < 0);
    pick(q0, 1);
    gdBtn('gd-back').dispatch('click'); await flush();
    eq('gd-draft.js なし: 戻るときは今までどおり確認する', CONFIRMS, ['まだ提出していません。ここでやめると、答えたぶんが消えます。やめますか？']);
    window.AJGdDraft = __G;
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""

# ---------------------------------------------------------------------------------------------------------------
# [3] マイページ (mypage.js の解答エリア = initGrammarDrillSection)
JS_MY_SETUP = r"""
function escapeHtml(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
var CSS = { escape: function (s) { return String(s); } };
function setInterval() { return 0; }
function clearInterval() {}
function setTimeout(fn) { return 0; }
function clearTimeout() {}
var SID = '7';
function _hwSid() { return SID; }
function _gdLevelJa(lv) { return String(lv || ''); }
var API = {}, CALLS = [], REFRESHED = 0;
function slApiFetch(path, opts) {
  var p = String(path).split('?')[0];
  CALLS.push({ path: p, method: (opts && opts.method) || 'GET', body: opts && opts.body });
  var r = API[p];
  if (r && r.netfail) return Promise.reject(new TypeError('Failed to fetch'));
  if (r && r.status && r.status !== 200) { var e = new Error((r.body && r.body.detail) || ('HTTP ' + r.status)); e.status = r.status; e.detail = r.body && r.body.detail; return Promise.reject(e); }
  return Promise.resolve(JSON.parse(JSON.stringify(r ? r.body : {})));
}
window._hwRefreshDrills = function () { REFRESHED++; return Promise.resolve(); };
function makeMyForm(html) {
  var f = new FakeEl(); f.radios = []; f.unsure = [];
  var re = /<input type="radio" name="([^"]+)" value="(\d+)" data-gd-qid="([^"]+)"/g, m;
  while ((m = re.exec(html))) {
    var inp = new FakeEl(); inp.type = 'radio'; inp.name = m[1]; inp.value = m[2]; inp.checked = false; inp.setAttribute('data-gd-qid', m[3]);
    f.radios.push(inp);
  }
  var re2 = /<input type="checkbox" data-gd-unsure data-gd-unsure-qid="([^"]+)"/g;
  while ((m = re2.exec(html))) {
    var cb = new FakeEl(); cb.type = 'checkbox'; cb.checked = false; cb.setAttribute('data-gd-unsure-qid', m[1]);
    f.unsure.push(cb);
  }
  f.querySelectorAll = function (sel) {
    if (sel === 'input[type="radio"]:checked') return f.radios.filter(function (r) { return r.checked; });
    if (sel === 'input[type="radio"]') return f.radios.slice();
    if (sel === 'input[data-gd-unsure]:checked') return f.unsure.filter(function (r) { return r.checked; });
    if (sel === 'input[data-gd-unsure]') return f.unsure.slice();
    return [];
  };
  return f;
}
var SECTION, LIST;
function newDrillSection() {
  SECTION = new FakeEl('grammarDrillSection');
  LIST = new FakeEl('grammarDrillList');
  var BADGE = new FakeEl('grammarDrillBadge');
  SECTION.querySelector = function (sel) { return sel === '#grammarDrillList' ? LIST : (sel === '#grammarDrillBadge' ? BADGE : null); };
  LIST.querySelector = function (sel) {
    if (sel.indexOf('[data-gd-form') === 0) {
      if (LIST._html.indexOf('data-gd-form=') < 0) return null;
      return LIST._qs.__form || (LIST._qs.__form = makeMyForm(LIST._html));
    }
    if (sel === '[data-gd-submit-msg]' || sel === '[data-gd-draft-note]') {
      if (LIST._html.indexOf(sel.slice(1, -1)) < 0) return null;
      return LIST._qs[sel] || (LIST._qs[sel] = new FakeEl());
    }
    return null;
  };
}
var document = { getElementById: function (id) { return id === 'grammarDrillSection' ? SECTION : null; } };
function myForm() { return LIST.querySelector('[data-gd-form]'); }
function myPick(qid, idx) {
  var f = myForm(), t = null;
  f.radios.forEach(function (r) { if (r.getAttribute('data-gd-qid') === String(qid)) { r.checked = (r.value === String(idx)); if (r.checked) t = r; } });
  LIST.dispatch('change', { target: t });
}
function myUnsure(qid) {
  var f = myForm(), t = f.unsure.filter(function (c) { return c.getAttribute('data-gd-unsure-qid') === String(qid); })[0];
  t.checked = true; LIST.dispatch('change', { target: t });
}
function myChecked() { var f = myForm(), o = {}; if (!f) return null; f.radios.forEach(function (r) { if (r.checked) o[r.getAttribute('data-gd-qid')] = Number(r.value); }); return o; }
function myUnsureChecked() { var f = myForm(); return f ? f.unsure.filter(function (c) { return c.checked; }).map(function (c) { return c.getAttribute('data-gd-unsure-qid'); }) : null; }
function myClick(attrs) {
  var btn = new FakeEl(); for (var k in attrs) btn.setAttribute(k, attrs[k]);
  LIST.dispatch('click', { target: { closest: function (sel) { var a = sel.slice(1, -1); return Object.prototype.hasOwnProperty.call(attrs, a) ? btn : null; } } });
  return btn;
}
var Q = SRV.get_open.questions, D = String(SRV.d_open), DD = String(SRV.d_done), K = 'aj_gd_draft_v1:7:' + D;
var q0 = String(Q[0].question_id), q1 = String(Q[1].question_id), q2 = String(Q[2].question_id);
function myApi0() {
  API = {};
  API['/api/student/grammar-drill/' + D] = { status: 200, body: SRV.get_open };
  API['/api/student/grammar-drill/' + DD] = { status: 200, body: SRV.get_done };
  API['/api/student/grammar-drill/' + D + '/submit'] = { status: 200, body: { ok: true, score_correct: 3, score_total: 3, percentage: 100, results: [] } };
}
"""

JS_MY_CASES = r"""
(async function () {
  try {
    __loadGdDraft();
    var G = window.AJGdDraft;
    var st = memStore(); G._useStorage(st); G._clearMemory();
    myApi0(); newDrillSection();
    await initGrammarDrillSection();
    await window._gdOpenDrill(D); await flush();
    ok('解答エリアに「💾 答えはこの端末に自動で保存されます」', String(LIST.innerHTML).indexOf('💾 答えはこの端末に自動で保存されます（途中でやめても続きから解けます）') >= 0);
    myPick(q0, 1); myPick(q1, 3); myUnsure(q1);
    var rec = JSON.parse(st._m[K] || 'null');
    ok('選ぶたび (自信なしも) この端末に保存', !!rec && rec.n === 2 && rec.a[q1][0] === 3 && rec.u.length === 1 && rec.u[0] === q1, st._m[K]);
    myClick({ 'data-gd-back': '1' }); await flush();
    ok('「← 一覧に戻る」で一覧を読み直す (確認なし)', REFRESHED >= 1);
    // ページを読み直す
    G._clearMemory(); newDrillSection();
    await initGrammarDrillSection();
    await window._gdOpenDrill(D); await flush();
    var exp = {}; exp[q0] = 1; exp[q1] = 3;
    eq('開き直すと答えが戻る', myChecked(), exp);
    eq('…自信なしも戻る', myUnsureChecked(), [q1]);
    eq('…「💾 前に答えた 2 問を戻しました（あと 1 問）」', LIST.querySelector('[data-gd-draft-note]').textContent, '💾 前に答えた 2 問を戻しました（あと 1 問）');
    // 通信失敗は残す
    myPick(q2, 0);
    API['/api/student/grammar-drill/' + D + '/submit'] = { netfail: true };
    myClick({ 'data-gd-submit': D, 'data-gd-total': '3' }); await flush();
    ok('通信に失敗した提出は下書きを残す', JSON.parse(st._m[K] || '{}').n === 3, st._m[K]);
    ok('…「答えは消えていません」', String(LIST.querySelector('[data-gd-submit-msg]').textContent).indexOf('答えは消えていません') >= 0, LIST.querySelector('[data-gd-submit-msg]').textContent);
    API['/api/student/grammar-drill/' + D + '/submit'] = { status: 200, body: { ok: true, score_correct: 3, score_total: 3, percentage: 100, results: [] } };
    myClick({ 'data-gd-submit': D, 'data-gd-total': '3' }); await flush();
    var sub = CALLS.filter(function (c) { return c.method === 'POST' && c.path === '/api/student/grammar-drill/' + D + '/submit'; });
    __data({ kind: 'mypage_submit', body: JSON.parse(sub[sub.length - 1].body) });
    eq('提出できたら下書きを消す', [st._m[K], G.progress('7', D)], [undefined, null]);
    ok('…採点結果の画面', String(LIST.innerHTML).indexOf('採点結果') >= 0);
    // 409 → 消して提出ずみの画面
    var KD = 'aj_gd_draft_v1:7:' + DD;
    API['/api/student/grammar-drill/' + DD] = { status: 200, body: SRV.get_open };   // 開いた時点ではまだ未提出に見える
    API['/api/student/grammar-drill/' + DD + '/submit'] = SRV.dup;
    newDrillSection(); await initGrammarDrillSection();
    await window._gdOpenDrill(DD); await flush();
    myPick(q0, 0); myPick(q1, 0); myPick(q2, 0);
    ok('下書きがある', !!st._m[KD]);
    API['/api/student/grammar-drill/' + DD] = { status: 200, body: SRV.get_done };
    myClick({ 'data-gd-submit': DD, 'data-gd-total': '3' }); await flush();
    eq('409 (本物の応答) → 下書きを消す', st._m[KD], undefined);
    ok('…提出ずみの画面を開き直す (「✅ 完了済み」・フォームなし)', String(LIST.innerHTML).indexOf('✅ 完了済み') >= 0 && !myForm(), String(LIST.innerHTML).slice(0, 300));
    // 提出ずみを開いたら消す
    var a2 = {}; a2[q0] = 2;
    G.save('7', DD, Q, a2, null);
    await window._gdOpenDrill(DD); await flush();
    eq('提出ずみのドリルを開いたら下書きを消す', st._m[KD], undefined);
    // gd-draft.js なし
    var __G = window.AJGdDraft; window.AJGdDraft = undefined;
    newDrillSection(); await initGrammarDrillSection();
    await window._gdOpenDrill(D); await flush();
    ok('gd-draft.js なし: 案内を出さない・選んでも例外なし', String(LIST.innerHTML).indexOf('💾 答えはこの端末') < 0);
    myPick(q0, 1);
    eq('gd-draft.js なし: 何も保存しない', Object.keys(st._m).filter(function (k) { return k.indexOf('aj_gd_draft') === 0; }), []);
    window.AJGdDraft = __G;
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""

# [3b] マイページの宿題欄のカード
JS_MY_CARD = r"""
(async function () {
  try {
    __loadHwNotice(); __loadGdDraft();
    var G = window.AJGdDraft;
    var st = memStore(); G._useStorage(st); G._clearMemory();
    var Qx = [{ question_id: 1, stem: 'a', choices: ['1', '2', '3', '4'] }, { question_id: 2, stem: 'b', choices: ['1', '2', '3', '4'] }];
    for (var i = 3; i <= 10; i++) Qx.push({ question_id: i, stem: 's' + i, choices: ['1', '2'] });
    G.save('7', '101', Qx, { '1': 0, '2': 3 }, []);
    G.save('7', '104', Qx, { '1': 0 }, []);   // 提出ずみのドリルには出さない
    newSection(); setApi([D_NEW, D_OLD, D_DONE], [H_NEW], 0);
    await initHomeworkSection(); await flush();
    var html = ELS['#homeworkList'].innerHTML;
    function cardM(key) { var parts = String(html).split('<div class="hw-item'); for (var j = 1; j < parts.length; j++) if (parts[j].indexOf(key) >= 0) return parts[j]; return ''; }
    ok('途中のドリルのカード: 「💾 途中 2/10」と「▶ 続きから解く」', cardM('data-hw-drill-open="101"').indexOf('💾 途中 2/10') >= 0 && cardM('data-hw-drill-open="101"').indexOf('▶ 続きから解く') >= 0,
       cardM('data-hw-drill-open="101"'));
    ok('ほかのドリルは今までどおり「▶ 解いて提出する」', cardM('data-hw-drill-open="102"').indexOf('▶ 解いて提出する') >= 0 && cardM('data-hw-drill-open="102"').indexOf('💾') < 0);
    ok('提出ずみのドリルには途中を出さない', cardM('data-hw-drill-open="104"').indexOf('💾') < 0, cardM('data-hw-drill-open="104"'));
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""

JS_SYNTAX = r"""
for (var k in SRC) {
  try { new Function(SRC[k]); ok('構文 OK: ' + k, true); }
  catch (e) { ok('構文 OK: ' + k, false, String(e)); }
}
__emit();
"""


def mypage_drill_slice(js):
    a = js.index("// 📝 単元別ドリル (英文法 4 択ドリル")
    b = js.index("// 🧭 コーチの今日の一手")
    return js[a:b]


def check_screens(srv_fx):
    H = load_harness()
    eng = H.js_engine()
    print(f"\n  JS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng), "node も osascript も jsc も見つからない")
    if not eng:
        return []
    gd_src = read(GD_JS)
    load_gd = "function __loadGdDraft() {\n" + gd_src + "\n}\n"
    load_hw = "function __loadHwNotice() {\n" + read(HW_JS) + "\n}\n"
    srv = "var SRV = " + json.dumps(srv_fx, ensure_ascii=False) + ";\n"
    out = []

    print("\n[1] gd-draft.js の部品")
    out += run_js(eng, H.PRELUDE + JS_DATA + load_gd + srv + JS_PURE, "[1]")

    print("\n[2] class.html (偽の DOM・本物のサーバの応答)")
    inline = H.inline_scripts(read(CLASS_HTML))
    check("class.html の inline script は 1 つ", len(inline) == 1, len(inline))
    if len(inline) == 1:
        boot = "function __bootClass() {\n" + inline[0] + "\n}\n"
        out += run_js(eng, H.PRELUDE + JS_DATA + H.POLYFILL + H.FAKE_DOM + load_gd + srv + H.JS_CLASS_SETUP + JS_CLASS_SETUP2 + boot + JS_CLASS_CASES2, "[2]")

    print("\n[3] mypage.js の解答エリア (initGrammarDrillSection を偽の DOM で)")
    my_js = read(MYPAGE_JS)
    try:
        sl = mypage_drill_slice(my_js)
    except ValueError:
        sl = None
        check("mypage.js の単元ドリルの範囲が見つかる", False)
    if sl:
        out += run_js(eng, H.PRELUDE + JS_DATA + H.POLYFILL + H.FAKE_DOM + load_gd + srv + JS_MY_SETUP + sl + "\n" + JS_MY_CASES, "[3]")

    print("\n[3b] mypage.js の宿題欄のカード (initHomeworkSection を偽の DOM で)")
    try:
        hs = H.mypage_homework_slice(my_js)
    except ValueError:
        hs = None
        check("mypage.js の宿題欄の範囲が見つかる", False)
    if hs:
        run_js(eng, H.PRELUDE + H.POLYFILL + H.FAKE_DOM + load_hw + load_gd + H.JS_MYPAGE_SETUP + hs + "\n" + JS_MY_CARD, "[3b]")

    print("\n[3c] 構文 (new Function)")
    srcs = {"gd-draft.js": gd_src, "mypage.js": my_js}
    for i, b in enumerate(inline):
        srcs[f"class.html inline #{i}"] = b
    run_js(eng, H.PRELUDE + "var SRC = " + json.dumps(srcs, ensure_ascii=True) + ";\n" + JS_SYNTAX, "[3c]")
    return out


def check_resubmit(server, data):
    print("\n[2+3] 画面が送った提出の本文を本物のサーバに送り直す")
    by = {d.get("kind"): d.get("body") for d in data}
    q = server.qids
    want = {str(q[0]): 1, str(q[1]): 2, str(q[2]): 0}   # 画面で選んだ (下書きから戻した 2 問 + 最後の 1 問)
    cb = by.get("class_submit") or {}
    check("塾生アプリ: 送った答え = 下書きから戻した答え + 最後に選んだ答え (問題 ID の文字列 → 0 始まりの番号)", cb.get("answers") == want, cb)
    r = server.submit(cb)
    check("…本物のサーバが 200 で受け付ける", r.status_code == 200, (r.status_code, r.text[:300]))
    if r.status_code == 200:
        j = r.json()
        exp = sum(1 for k, v in want.items() if server.answers[k] == v)
        check(f"…選んだとおりに採点 ({exp}/3)", j.get("score_correct") == exp and j.get("score_total") == 3, j.get("score_correct"))
    mb = by.get("mypage_submit") or {}
    want_my = {str(q[0]): 1, str(q[1]): 3, str(q[2]): 0}
    check("マイページ: 送った答え = 下書きから戻した答え + 最後に選んだ答え・🤔 自信なしも戻ったぶん", mb.get("answers") == want_my and mb.get("unsure") == [str(q[1])], mb)
    r2 = server.submit(mb)
    check("…同じドリルに 2 回目は本物の 409 (= 画面は下書きを消して提出ずみの画面を出す)", r2.status_code == 409, (r2.status_code, r2.text[:200]))


def check_sources():
    print("\n[4] ソース検査")
    class_html, mypage_html, gd_src, my_js = read(CLASS_HTML), read(MYPAGE_HTML), read(GD_JS), read(MYPAGE_JS)
    v1 = re.search(r'<script src="gd-draft\.js\?v=([^"]+)"></script>', class_html)
    v2 = re.search(r'<script src="gd-draft\.js\?v=([^"]+)"></script>', mypage_html)
    check("class.html と mypage.html が gd-draft.js?v= を読む・?v= がそろう", bool(v1 and v2 and v1.group(1) == v2.group(1)), (v1 and v1.group(1), v2 and v2.group(1)))
    i_gd = class_html.find('src="gd-draft.js')
    i_inline = class_html.find("<script>", i_gd if i_gd >= 0 else 0)
    check("class.html: gd-draft.js を inline script より前に読む", 0 <= i_gd < i_inline, (i_gd, i_inline))
    check("mypage.html: gd-draft.js を mypage.js より前に読む", 0 <= mypage_html.find('src="gd-draft.js') < mypage_html.find('src="mypage.js?v='))
    body = re.sub(r"/\*.*?\*/", "", gd_src, flags=re.S)
    body = "\n".join(re.sub(r"(^|\s)//.*$", "", ln) for ln in body.split("\n"))
    check("gd-draft.js は ES5 (=>・let・const・テンプレート文字列なし)", not re.search(r"=>|\blet\s|\bconst\s|`", body))
    check("class.html の旧コメント「下書き保存は無い」は消えた", "下書き保存は無い" not in class_html)
    check("gd-draft.js は名前・トークンを保存しない (保存する値は選んだ番号・指紋・自信なし・時刻)",
          "var rec = { v: 1, t: (qs && qs.length) || 0, n: n, a: a, u: u, at: nowMs() };" in gd_src)
    check("mypage.js: 提出できたら / 409 で下書きを消す", "draftClear(drillId);   // 💾 出したので途中保存は消す" in my_js
          and "if (e && e.status === 409) { draftClear(drillId); openDrill(drillId); return; }" in my_js)
    ci = read(CI_YML)
    check("CI (server-tests.yml) にこのテストの step がある", "python3 scripts/health_check/test_drill_draft.py" in ci)
    paths_block = ci.split("pull_request:")[0]
    for p in ("'gd-draft.js'", "'class.html'", "'mypage.js'", "'mypage.html'", "'server/**'"):
        check(f"CI の paths に {p}", p in paths_block)


def main():
    sys.path.insert(0, HERE)
    server = Server()
    fx = server.fixtures()
    data = check_screens(fx)
    check_resubmit(server, data)
    check_sources()
    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for x in FAILURES:
            print("   -", x)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
