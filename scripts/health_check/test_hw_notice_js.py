#!/usr/bin/env python3
"""🆕 新しい宿題のお知らせ (hw-notice.js・塾生アプリ class.html・マイページ mypage) を実際の JS エンジンで動かして確かめる。

背景 (2026-10-15 塾長決定「アプリを開けば分かる」): 宿題・ドリルを配ったときのお知らせは LINE を使わず、アプリを開いたときに出す。
  数え方と「見た」の記録は hw-notice.js の 1 か所。class.html は画面の上の帯 (宿題タブ以外)・カードの 🆕 新着、
  mypage はコーチカード下の 📌 要対応チップ「🆕 新しい宿題 N 件」とカードの 🆕 新着。
  あわせて、デスクトップの予約タスクが書く status='assigned' のドリルを class.html が「完了」と表示していたのを直した。

固定する性質:
  [1] hw-notice.js の関数: 'assigned' も未提出・新しい = 未提出 − この端末で見たもの − 自分で始めたもの (今日の1問・診断)・
      記録が無ければ届いて 72 時間以内 (naive UTC のマイクロ秒つき / オフセット付き ISO)・取れなかった一覧は記録を変えない・
      宿題の記録は今の未提出に絞る・localStorage が throw しても止まらずページ内の記録で帯が消える・文言
  [2] mypage.js の宿題欄 (initHomeworkSection を偽の DOM で実行): hw-notice.js が無い端末は今までどおり / あれば 🆕 新着と
      「🆕 新しい宿題 N 件」・宿題欄が 1.5 秒見えたら・ドリルを開いたら「見た」・?focus=homework で宿題欄へスクロール
  [3] class.html の inline script を丸ごと偽の DOM と偽の API で実行: 帯 (宿題タブ以外)・'assigned' は未提出・バッジ・
      宿題タブで「見た」と記録・?tab=homework と #homework で宿題タブに着地して URL から消す・401 のログインに redirect=・
      宿題 API が 403 でもドリルは出す・期限切れだけの帯・hw-notice.js が読めない端末でも動く
  [4] 構文 (new Function): hw-notice.js・mypage.js・class.html と mypage.html の inline script
  [5] ソース検査: 読み込み順・?v= が両ページでそろう・hw-notice.js は ES5・class.html にドリルの status === 'open' が残っていない・
      mypage の送り返しが ?tab=homework を引き継ぐ・mypage.js の AJHwNotice は _hwNotice() 経由・CI 登録

★JS エンジンが無ければ FAIL (飛ばさない)。CI (ubuntu) は node、塾長の Mac は osascript -l JavaScript (node は無い)。
  AJ_JS_ENGINE=node|osascript|jsc で選べる。生徒名・メールは架空 (公開リポジトリ)。

実行:
    python3 scripts/health_check/test_hw_notice_js.py
    # exit 0 = PASS / 1 = FAIL
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
HW_JS = os.path.join(REPO, "hw-notice.js")
CLASS_HTML = os.path.join(REPO, "class.html")
MYPAGE_HTML = os.path.join(REPO, "mypage.html")
MYPAGE_JS = os.path.join(REPO, "mypage.js")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc"

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


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


def inline_scripts(html):
    out = []
    for m in re.finditer(r"<script(\s[^>]*)?>(.*?)</script>", html, re.S):
        attrs = m.group(1) or ""
        if "src=" in attrs:
            continue
        if "type=" in attrs and "javascript" not in attrs:
            continue
        out.append(m.group(2))
    return out


# 結果の書き出し (node は console.log = stdout、osascript は console.log = stderr、jsc は print)。OK / NG / DONE の行だけを読む
PRELUDE = r"""
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
var window = (typeof globalThis !== 'undefined') ? globalThis : this;
// 画面のコードが使う console.warn / console.error (osascript には log しか無い・jsc には console が無い)。結果は __emit が書く
if (typeof console === 'undefined') window.console = { log: function () {}, warn: function () {}, error: function () {} };
if (!console.warn) console.warn = function () {};
if (!console.error) console.error = function () {};
function memStore() {
  var m = {}, log = [];
  return {
    getItem: function (k) { log.push('get ' + k); return Object.prototype.hasOwnProperty.call(m, k) ? m[k] : null; },
    setItem: function (k, v) { log.push('set ' + k); m[k] = String(v); },
    removeItem: function (k) { delete m[k]; },
    _m: m, _log: log
  };
}
var __storageNote = '';
// window.localStorage を差し替える (node 25 以降は既定で localStorage があるので defineProperty で上書き)
function setWindowStorage(desc) {
  try { Object.defineProperty(window, 'localStorage', desc); return true; }
  catch (e) { __storageNote = String(e); return false; }
}
async function flush(n) { for (var i = 0; i < (n || 600); i++) await Promise.resolve(); }
function utcNaive(msAgo) { return new Date(Date.now() - msAgo).toISOString().replace('T', ' ').replace('Z', ''); }
var HOUR = 3600 * 1000, DAY = 24 * HOUR;
"""

# 最小の URLSearchParams (osascript / jsc には無い。node は本物を使う)
POLYFILL = r"""
if (typeof URLSearchParams === 'undefined') {
  window.URLSearchParams = function (s) {
    this._p = [];
    s = String(s || '').replace(/^\?/, '');
    if (s) {
      var parts = s.split('&');
      for (var i = 0; i < parts.length; i++) {
        if (!parts[i]) continue;
        var kv = parts[i].split('=');
        this._p.push([decodeURIComponent(kv[0].replace(/\+/g, ' ')), decodeURIComponent((kv.slice(1).join('=') || '').replace(/\+/g, ' '))]);
      }
    }
  };
  URLSearchParams.prototype.get = function (k) { for (var i = 0; i < this._p.length; i++) if (this._p[i][0] === k) return this._p[i][1]; return null; };
  URLSearchParams.prototype.has = function (k) { return this.get(k) !== null; };
  URLSearchParams.prototype['delete'] = function (k) { this._p = this._p.filter(function (p) { return p[0] !== k; }); };
  URLSearchParams.prototype.toString = function () { return this._p.map(function (p) { return encodeURIComponent(p[0]) + '=' + encodeURIComponent(p[1]); }).join('&'); };
}
"""

# 偽の DOM (class.html / mypage.js が使う範囲だけ)。innerHTML を書くと子要素の控えは捨てる
FAKE_DOM = r"""
function FakeEl(id) {
  this.id = id || ''; this.hidden = false; this.textContent = ''; this.className = ''; this.value = '';
  this.style = {}; this.attrs = {}; this.listeners = {}; this.children = []; this._qs = {}; this._html = ''; this.scrolled = 0;
  var cls = {};
  this.classList = {
    add: function (c) { cls[c] = 1; }, remove: function (c) { delete cls[c]; },
    toggle: function (c, on) { if (on === undefined) on = !cls[c]; if (on) cls[c] = 1; else delete cls[c]; return on; },
    contains: function (c) { return !!cls[c]; }
  };
}
Object.defineProperty(FakeEl.prototype, 'innerHTML', {
  get: function () { return this._html; },
  set: function (v) { this._html = String(v); this._qs = {}; }
});
FakeEl.prototype.addEventListener = function (t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); };
FakeEl.prototype.removeEventListener = function () {};
FakeEl.prototype.dispatch = function (t, ev) {
  var self = this;
  (this.listeners[t] || []).slice().forEach(function (fn) { fn(ev || { preventDefault: function () {}, target: self }); });
};
FakeEl.prototype.querySelector = function (sel) { return this._qs[sel] || (this._qs[sel] = new FakeEl()); };
FakeEl.prototype.querySelectorAll = function () { return []; };
FakeEl.prototype.setAttribute = function (k, v) { this.attrs[k] = String(v); };
FakeEl.prototype.getAttribute = function (k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; };
FakeEl.prototype.appendChild = function (c) { this.children.push(c); return c; };
FakeEl.prototype.insertBefore = function (c) { this.children.push(c); return c; };
FakeEl.prototype.closest = function () { return null; };
FakeEl.prototype.scrollIntoView = function () { this.scrolled++; };
FakeEl.prototype.remove = function () {};
FakeEl.prototype.focus = function () {};
function count(hay, needle) { return String(hay).split(needle).length - 1; }
"""

# ---------------------------------------------------------------------------------------------------------------
# [1] hw-notice.js の関数
JS_PURE = r"""
__loadHwNotice();
var N = window.AJHwNotice;
ok('window.AJHwNotice が公開される', !!N && typeof N.compute === 'function');
eq('未提出: open / assigned は未提出・completed と null は違う',
   [N.isOpenDrill({ status: 'open' }), N.isOpenDrill({ status: 'assigned' }), N.isOpenDrill({ status: 'completed' }), N.isOpenDrill(null)],
   [true, true, false, false]);
eq('クラス宿題: open だけ未提出', [N.isOpenHw({ status: 'open' }), N.isOpenHw({ status: 'completed' }), N.isOpenHw(null)], [true, false, false]);
eq('naive UTC (マイクロ秒つき) を読む', N.parseServerTs('2026-10-15 05:30:00.123456'), Date.UTC(2026, 9, 15, 5, 30, 0, 123));
eq('naive UTC (秒まで)', N.parseServerTs('2026-10-15 05:30:00'), Date.UTC(2026, 9, 15, 5, 30, 0));
eq('オフセット付き ISO (+09:00)', N.parseServerTs('2026-10-15T14:30:00+09:00'), Date.UTC(2026, 9, 15, 5, 30, 0));
eq('str(datetime) の +00:00', N.parseServerTs('2026-10-15 05:30:00.5+00:00'), Date.UTC(2026, 9, 15, 5, 30, 0, 500));
eq('Z 付き', N.parseServerTs('2026-10-15T05:30:00Z'), Date.UTC(2026, 9, 15, 5, 30, 0));
eq('読めない値は NaN', [isNaN(N.parseServerTs('bad')), isNaN(N.parseServerTs('')), isNaN(N.parseServerTs(null))], [true, true, true]);
eq('JST の今日 (UTC 15:00 = JST 翌日 0:00)', [N.todayJst(Date.UTC(2026, 9, 14, 15, 0, 0)), N.todayJst(Date.UTC(2026, 9, 14, 14, 59, 59))], ['2026-10-15', '2026-10-14']);

var NOW = Date.UTC(2026, 9, 15, 6, 0, 0);   // 2026-10-15 15:00 JST
var drills = [
  { drill_id: 1, status: 'open', assigned_at: '2026-10-15 05:30:00.123456' },            // 30 分前
  { drill_id: 2, status: 'assigned', assigned_at: '2026-10-13 07:00:00' },               // 47 時間前 (予約タスクの 'assigned')
  { drill_id: 3, status: 'open', assigned_at: '2026-10-11 05:00:00' },                   // 4 日前
  { drill_id: 4, status: 'open', assigned_at: '2026-10-15T14:00:00+09:00', self_issued: true },  // 今日の1問 (自分で始めた)
  { drill_id: 5, status: 'completed', assigned_at: '2026-10-15 05:00:00' },
  { drill_id: 6, status: 'open', assigned_at: '2026-10-12T15:00:00+09:00' },             // ちょうど 72 時間前
  { drill_id: 7, status: 'open', assigned_at: 'bad' },                                   // 日時が読めない
  { drill_id: 1, status: 'open', assigned_at: '2026-10-15 05:30:00' }                    // 同じ ID の重複
];
var hw = [
  { id: 11, status: 'open', created_at: '2026-10-15 01:00:00', due_date: '2026-10-14' },  // 新しい・期限切れ
  { id: 12, status: 'open', created_at: '2026-10-01 01:00:00', due_date: '2026-10-15' },  // 古い・今日が期限 (期限切れではない)
  { id: 13, status: 'completed', created_at: '2026-10-15 01:00:00', due_date: '2026-10-01' }
];
var r = N.compute({ drills: drills, homework: hw, seen: null, now: NOW });
eq('記録なし: 72 時間以内の未提出ドリルが新しい (assigned も・自分で始めたもの・完了・読めない日時は除く)', r.newDrillIds, ['1', '2', '6']);
eq('記録なし: 72 時間以内の未提出の宿題が新しい', r.newHwIds, ['11']);
eq('新しい件数', r.newCount, 4);
eq('未提出の件数 (ドリル 7 行 = 重複込み 6 + 宿題 2)', r.openCount, 9);
eq('期限切れは JST の今日で数える', r.overdue, 1);
eq('newDrillMap / newHwMap', [r.newDrillMap['2'] === true, r.newHwMap['11'] === true, r.newDrillMap['3'] === undefined], [true, true, true]);
var r2 = N.compute({ drills: drills, homework: hw, seen: { d: ['1', '3'], h: [] }, now: NOW });
eq('記録あり: 見ていない未提出ドリルが新しい (日時は見ない・自分で始めたものは除く)', r2.newDrillIds, ['2', '6', '7']);
eq('記録あり: 宿題も記録と比べる', r2.newHwIds, ['11', '12']);
var r3 = N.compute({ drills: drills, homework: hw, seen: { d: null, h: ['11'] }, now: NOW });
eq('ドリルの記録が無ければドリルだけ 72 時間で数える', [r3.newDrillIds, r3.newHwIds], [['1', '2', '6'], ['12']]);
var r4 = N.compute({ drills: null, homework: null, seen: null, now: NOW });
eq('取れなかった一覧は数えない', [r4.newCount, r4.openCount, r4.overdue], [0, 0, 0]);
eq('today を渡せばその日で期限切れを数える', N.compute({ homework: hw, today: '2026-10-16', now: NOW }).overdue, 2);

// 記録 (localStorage) の読み書き
var st = memStore(); N._useStorage(st); N._clearMemory();
eq('記録の無い端末は null', N.loadSeen('7'), null);
N.markSeen('7', drills, hw);
eq('キーは aj_hw_seen_v1:<生徒ID>', Object.keys(st._m), ['aj_hw_seen_v1:7']);
N._clearMemory();   // 次のページ
var s1 = N.loadSeen('7');
eq('未提出のドリル ID だけを保存 (重複なし)', s1.d, ['1', '2', '3', '4', '6', '7']);
eq('未提出の宿題 ID だけを保存', s1.h, ['11', '12']);
eq('見た後は新しい 0', N.compute({ drills: drills, homework: hw, seen: s1, now: NOW }).newCount, 0);
var hw2 = [{ id: 12, status: 'completed' }, { id: 14, status: 'open', created_at: '2026-10-15 05:00:00' }];
N.markSeen('7', null, hw2);
N._clearMemory();
var s2 = N.loadSeen('7');
eq('ドリルが取れなかったときは前のドリル ID を残す', s2.d, ['1', '2', '3', '4', '6', '7']);
eq('宿題 ID は今の未提出に絞る', s2.h, ['14']);
var st2 = memStore(); N._useStorage(st2); N._clearMemory();
N.markSeen('8', null, []);
var s3 = N.loadSeen('8');
eq('初めての記録でドリルが取れなかったらドリルは「記録なし」のまま', [s3.d, s3.h], [null, []]);
eq('その場合ドリルは 72 時間で数える', N.compute({ drills: drills, homework: [], seen: s3, now: NOW }).newDrillIds, ['1', '2', '6']);
eq('両方 null の記録は作らない', [N.markSeen('9', null, null), Object.keys(st2._m).indexOf('aj_hw_seen_v1:9')], [null, -1]);
var st3 = memStore(); N._useStorage(st3); N._clearMemory();
N.markSeen('', drills, hw);
eq('生徒が分からないときは localStorage に触らない', st3._log.length, 0);
eq('…ページ内の記録は効く', N.compute({ drills: drills, homework: hw, seen: N.loadSeen(''), now: NOW }).newCount, 0);
var st4 = memStore(); N._useStorage(st4); N._clearMemory();
st4._m['aj_hw_seen_v1:9'] = '{not json';
eq('壊れた記録は null (throw しない)', N.loadSeen('9'), null);
st4._m['aj_hw_seen_v1:9'] = JSON.stringify({ d: 'x', h: [] });
eq('形の違う記録は null', N.loadSeen('9'), null);
st4._m['aj_hw_seen_v1:9'] = JSON.stringify({ d: [1, '2', { x: 1 }, '', null], h: null });
eq('ID は数か空でない文字列だけ読む', N.loadSeen('9'), { d: ['1', '2'], h: null });
var st5 = memStore(); N._useStorage(st5); N._clearMemory();
N.markSeen('7', [{ drill_id: 1, status: 'open' }], null);
st5._m['aj_hw_seen_v1:7'] = JSON.stringify({ v: 1, d: ['5'], h: null });   // 別のタブが書いた
eq('別のタブの記録とページ内の記録はどちらも「見た」', N.loadSeen('7').d.slice().sort(), ['1', '5']);
var many = []; for (var i = 0; i < 620; i++) many.push({ drill_id: i + 1, status: 'open' });
N._useStorage(memStore()); N._clearMemory();
eq('1 一覧の記録は 500 件まで', N.markSeen('7', many, []).d.length, 500);

// localStorage が使えない端末 (プライベートブラウズ・容量超過・保存を禁止)
var bad = { getItem: function () { throw new Error('SecurityError'); }, setItem: function () { throw new Error('QuotaExceededError'); } };
N._useStorage(bad); N._clearMemory();
eq('保存できない端末: loadSeen は null', N.loadSeen('7'), null);
var threw = false; try { N.markSeen('7', drills, hw); } catch (e) { threw = String(e); }
eq('保存できない端末: markSeen は throw しない', threw, false);
eq('保存できない端末: ページ内の記録で 2 回目は新しい 0 (帯が消える)', N.compute({ drills: drills, homework: hw, seen: N.loadSeen('7'), now: NOW }).newCount, 0);
N._useStorage(undefined); N._clearMemory();
if (setWindowStorage({ configurable: true, get: function () { throw new Error('SecurityError'); } })) {
  var t2 = false; var ls = 'x';
  try { ls = N.loadSeen('7'); N.markSeen('7', drills, hw); } catch (e) { t2 = String(e); }
  eq('window.localStorage を読むだけで throw する端末でも止まらない', [t2, ls], [false, null]);
  eq('…ページ内の記録は効く', N.compute({ drills: drills, homework: hw, seen: N.loadSeen('7'), now: NOW }).newCount, 0);
  var st6 = memStore();
  setWindowStorage({ configurable: true, writable: true, value: st6 }); N._clearMemory();
  N.markSeen('7', drills, hw);
  eq('差し替えなしでは window.localStorage に保存する', Object.keys(st6._m), ['aj_hw_seen_v1:7']);
} else {
  // node の版によっては window.localStorage を差し替えられない。上の _useStorage(bad) の検査で同じ性質を見ている
  ok('(この JS エンジンでは window.localStorage を差し替えられないので _useStorage の検査で代用: ' + __storageNote + ')', true);
}

// 文言
eq('帯: 新しい宿題', N.newLabel(3), '🆕 新しい宿題が 3 件届いています');
eq('帯: 〆を過ぎた (2026-10-18 から 〆 の言い方)', N.overdueLabel(2), '⚠️ 〆を過ぎた宿題が 2 件あります');
eq('チップ: 新しい + 未提出 + 〆を過ぎた', N.todoLabel(2, 5, 1), '🆕 新しい宿題 2 件（未提出 5 件・うち〆を過ぎた 1 件）');
eq('チップ: 新しいものだけ', N.todoLabel(2, 2, 0), '🆕 新しい宿題 2 件');
eq('チップ: 新しいものが無いとき', [N.todoLabel(0, 3, 0), N.todoLabel(0, 3, 1)], ['📝 宿題 3 件', '⚠️ 宿題 3 件（うち〆を過ぎた 1 件）']);
eq('記録なしの窓は 72 時間', N.FIRST_VISIT_WINDOW_MS, 72 * 3600 * 1000);
__emit();
"""

# ---------------------------------------------------------------------------------------------------------------
# [2] mypage.js の宿題欄 (initHomeworkSection) を偽の DOM で動かす
JS_MYPAGE_SETUP = r"""
var location = { search: '?focus=homework', pathname: '/mypage.html', hash: '' }; window.location = location;
window.innerHeight = 800;
var TODO = {};
var AJ_TODO = { set: function (k, v) { TODO[k] = v; } }; window.AJ_TODO = AJ_TODO;
var TIMERS = [];
function setTimeout(fn, ms) { TIMERS.push({ fn: fn, ms: ms }); return TIMERS.length; }
function clearTimeout(id) { if (TIMERS[id - 1]) TIMERS[id - 1].fn = null; }
var IO_LIST = [];
function IntersectionObserver(cb, opts) { this.cb = cb; this.opts = opts; this.els = []; IO_LIST.push(this); }
IntersectionObserver.prototype.observe = function (el) { this.el = el; if (this.els.indexOf(el) < 0) this.els.push(el); };
IntersectionObserver.prototype.unobserve = function (el) { this.els = this.els.filter(function (x) { return x !== el; }); };
IntersectionObserver.prototype.disconnect = function () { this.els = []; };
function sectionObservers() { return IO_LIST.filter(function (o) { return o.el === SECTION; }); }   // 宿題欄の監視 (🆕 の「見た」)
window.IntersectionObserver = IntersectionObserver;   // 画面は 'IntersectionObserver' in window で見る
function confirm() { return true; }
function alert() {}
function getCurrentStudent() { return { id: 7, name: 'テスト生徒A' }; }   // 架空
function _canUseStudyMgmt() { return true; }
function _gdRich(s) { return String(s == null ? '' : s); }
var API = {};
function slApiFetch(path) {
  var d = API[String(path).split('?')[0]];
  if (d instanceof Error) return Promise.reject(d);
  return Promise.resolve(JSON.parse(JSON.stringify(d || {})));
}
var SECTION, ELS;
function newSection() {
  SECTION = new FakeEl('homeworkSection');
  ELS = {};
  ['#homeworkList', '#homeworkBadge', '#homeworkCompletedToggle', '#homeworkShowCompleted', '#homeworkTitleText', '#homeworkIntro'].forEach(function (s) { ELS[s] = new FakeEl(s.slice(1)); });
  SECTION.querySelector = function (sel) { return ELS[sel] || null; };
}
var document = {
  querySelector: function (sel) { return sel === '.homework-section' ? SECTION : null; },
  getElementById: function (id) { return id === 'homeworkSection' ? SECTION : null; }
};
var OPENED = [];
window._gdOpenDrill = function (id) { OPENED.push(id); };
function setApi(drills, hw, overdue) {
  API['/api/student/grammar-drills'] = drills instanceof Error ? drills : { ok: true, items: drills };
  API['/api/student/homework'] = { ok: true, items: hw, summary: { overdue: overdue || 0 } };
}
var D_NEW = { drill_id: 101, title: '時制ドリル', unit: '時制', subject: 'english', status: 'open', assigned_at: utcNaive(2 * HOUR) };
var D_OLD = { drill_id: 102, title: '関係詞ドリル', unit: '関係詞', subject: 'english', status: 'assigned', assigned_at: utcNaive(10 * DAY) };
var D_SELF = { drill_id: 103, title: '今日の1問', unit: '今日の1問', subject: 'english', status: 'open', assigned_at: utcNaive(HOUR), self_issued: true };
var D_DONE = { drill_id: 104, title: '比較ドリル', unit: '比較', subject: 'english', status: 'completed', score_correct: 8, score_total: 10, assigned_at: utcNaive(3 * DAY) };
var H_NEW = { id: 201, title: '音読の宿題', subject: 'english', status: 'open', created_at: utcNaive(HOUR), due_date: '2999-12-31' };
var H_OVER = { id: 202, title: '単語テストの準備', subject: 'english', status: 'open', created_at: utcNaive(5 * DAY), due_date: '2000-01-01' };
var H_DONE = { id: 203, title: '前の宿題', subject: 'english', status: 'completed', created_at: utcNaive(9 * DAY), completed_at: utcNaive(8 * DAY) };
function clickDrill(id) {
  var btn = new FakeEl(); btn.setAttribute('data-hw-drill-open', String(id));
  ELS['#homeworkList'].dispatch('click', { target: { closest: function (sel) { return sel === '[data-hw-drill-open]' ? btn : null; } } });
}
"""

JS_MYPAGE_CASES = r"""
(async function () {
  try {
    // (a) hw-notice.js が読めなかった端末: 今までどおり
    newSection(); setApi([D_NEW, D_OLD, D_SELF, D_DONE], [H_NEW, H_OVER, H_DONE], 1);
    await initHomeworkSection(); await flush();
    eq('hw-notice.js なし: チップは今までの文言 (assigned も未提出に数える)', TODO.homework && TODO.homework.label, '⚠️ 宿題 5 件（うち期限切れ 1 件）');
    eq('hw-notice.js なし: 🆕 新着は付かない', count(ELS['#homeworkList'].innerHTML, '🆕 新着'), 0);
    eq('hw-notice.js なし: 宿題欄の見えたかの監視は作らない', sectionObservers().length, 0);
    eq('hw-notice.js なし: ?focus=homework でも宿題欄へスクロール', SECTION.scrolled, 1);

    // (b) hw-notice.js あり・記録の無い端末
    __loadHwNotice();
    var st = memStore(); window.AJHwNotice._useStorage(st); window.AJHwNotice._clearMemory();
    newSection(); setApi([D_NEW, D_OLD, D_SELF, D_DONE], [H_NEW, H_OVER, H_DONE], 1);
    await initHomeworkSection(); await flush();
    var html = ELS['#homeworkList'].innerHTML;
    eq('チップ「🆕 新しい宿題 N 件」(届いて 72 時間以内のドリル 1 + 宿題 1)', TODO.homework && TODO.homework.label, '🆕 新しい宿題 2 件（未提出 5 件・うち〆を過ぎた 1 件）');
    eq('新しいときはチップを目立たせる (urgent)', TODO.homework && TODO.homework.urgent, true);
    eq('🆕 新着はドリル 1 枚 + 宿題 1 枚', count(html, '🆕 新着'), 2);
    ok('🆕 新着は新しいドリルのカードに付く', /🆕 新着<\/span>[^]*?data-hw-drill-open="101"/.test(html) && !/🆕 新着<\/span><span[^>]*>📝 英文法ドリル<\/span><span[^>]*>関係詞/.test(html));
    eq('assigned のドリルも「▶ 解いて提出する」(未提出の 3 枚)', count(html, '▶ 解いて提出する'), 3);
    eq('?focus=homework で宿題欄へスクロール (1 回)', SECTION.scrolled, 1);
    eq('宿題欄の見えたかの監視を 1 つ作る', sectionObservers().length, 1);
    eq('描いただけでは「見た」にしない', Object.keys(st._m).length, 0);
    var io = sectionObservers()[0];
    io.cb([{ isIntersecting: true, intersectionRatio: 0.4, intersectionRect: { height: 200 } }]);
    eq('宿題欄が見えたら 1.5 秒待つ', TIMERS.length && TIMERS[TIMERS.length - 1].ms, 1500);
    io.cb([{ isIntersecting: false, intersectionRatio: 0, intersectionRect: { height: 0 } }]);
    eq('1.5 秒たつ前に見えなくなったら記録しない', TIMERS[TIMERS.length - 1].fn, null);
    io.cb([{ isIntersecting: true, intersectionRatio: 0.12, intersectionRect: { height: 500 } }]);   // 縦長の欄が画面の半分以上
    var t = TIMERS[TIMERS.length - 1]; ok('縦に長い欄は画面の半分以上見えたら数える', !!(t && t.fn));
    t.fn();
    eq('見たら localStorage に記録', Object.keys(st._m), ['aj_hw_seen_v1:7']);
    eq('見たらチップは「📝/⚠️ 宿題 N 件」に戻る', TODO.homework && TODO.homework.label, '⚠️ 宿題 5 件（うち〆を過ぎた 1 件）');
    eq('見ている最中はカードの 🆕 を消さない', count(ELS['#homeworkList'].innerHTML, '🆕 新着'), 2);
    await window._hwRefreshDrills(); await flush();
    eq('読み直したら 🆕 は消える', count(ELS['#homeworkList'].innerHTML, '🆕 新着'), 0);
    eq('?focus=homework のスクロールは最初の 1 回だけ', SECTION.scrolled, 1);

    // 新しいドリルが届いた → ドリルを開いたら「見た」
    var D_NEXT = { drill_id: 105, title: '仮定法ドリル', unit: '仮定法', subject: 'english', status: 'open', assigned_at: utcNaive(5 * 60 * 1000) };
    setApi([D_NEXT, D_NEW, D_OLD, D_SELF, D_DONE], [H_NEW, H_OVER, H_DONE], 1);
    await window._hwRefreshDrills(); await flush();
    eq('次に届いたドリルだけが新しい', [TODO.homework && TODO.homework.label, count(ELS['#homeworkList'].innerHTML, '🆕 新着')], ['🆕 新しい宿題 1 件（未提出 6 件・うち〆を過ぎた 1 件）', 1]);
    clickDrill(105);
    eq('ドリルを開く (_gdOpenDrill)', OPENED, ['105']);
    eq('開いたら「見た」でチップが戻る', TODO.homework && TODO.homework.label, '⚠️ 宿題 6 件（うち〆を過ぎた 1 件）');
    eq('記録に新しいドリルが入る', JSON.parse(st._m['aj_hw_seen_v1:7']).d, ['105', '101', '102', '103']);

    // ドリルの取得に失敗 → ドリルの記録は変えない
    setApi(new Error('HTTP 500'), [H_NEW, H_OVER, H_DONE], 1);
    await window._hwRefreshDrills(); await flush();
    io.cb([{ isIntersecting: true, intersectionRatio: 0.5, intersectionRect: { height: 300 } }]);
    TIMERS[TIMERS.length - 1].fn();
    eq('ドリルが取れなかったときはドリルの記録を残す', JSON.parse(st._m['aj_hw_seen_v1:7']).d, ['105', '101', '102', '103']);
    ok('ドリルの取得失敗は赤い案内のまま', ELS['#homeworkList'].innerHTML.indexOf('ドリルの取得に失敗しました') >= 0);
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""

# ---------------------------------------------------------------------------------------------------------------
# [3] class.html の inline script を丸ごと動かす
JS_CLASS_SETUP = r"""
var location, HIST = [], TOASTS = [];
function setLoc(path, search, hash) {
  location = { protocol: 'https:', hostname: 'example.invalid', port: '', origin: 'https://example.invalid',
               pathname: path, search: search || '', hash: hash || '', href: 'https://example.invalid' + path + (search || '') + (hash || ''),
               reload: function () {} };
  window.location = location;
}
var history = { replaceState: function (s, t, url) { HIST.push(url); } }; window.history = history;
window.scrollTo = function () {};
window.innerHeight = 800;
var TIMERS = [];
function setTimeout(fn, ms) { TIMERS.push({ fn: fn, ms: ms }); return TIMERS.length; }
function clearTimeout() {}
function confirm() { return true; }
function alert() {}
window.AuthGuard = { getToken: function () { return 'test-token'; }, getStudent: function () { return { id: 7, name: 'テスト生徒A' }; } };
var ELS = {}, TAB_BTNS = [];
var document = {
  getElementById: function (id) { return ELS[id] || (ELS[id] = new FakeEl(id)); },
  querySelectorAll: function (sel) { return sel === '#tabbar button' ? TAB_BTNS : []; },
  querySelector: function () { return null; },
  createElement: function () { return new FakeEl(); },
  head: new FakeEl('head'), body: new FakeEl('body'),
  addEventListener: function () {}
};
var API = {}, FETCHES = [];
function fetch(url, opts) {
  var path = String(url).replace(/^https?:\/\/[^\/]+/, '');
  FETCHES.push(path);
  var key = path.split('?')[0];
  var r = Object.prototype.hasOwnProperty.call(API, key) ? API[key] : { status: 200, body: {} };
  return Promise.resolve({ ok: r.status >= 200 && r.status < 300, status: r.status,
                           json: function () { return Promise.resolve(JSON.parse(JSON.stringify(r.body))); } });
}
window.fetch = fetch;
function setApi(o) {
  API = {
    '/api/student/class/feed': { status: 200, body: { ai_home_available: false, sessions: [], recordings: [] } },
    '/api/student/homework': { status: 200, body: { ok: true, items: [], summary: { open: 0, overdue: 0 } } },
    '/api/student/grammar-drills': { status: 200, body: { ok: true, items: [], summary: { open: 0 } } }
  };
  for (var k in o) API[k] = o[k];
}
function hwBody(items) {
  var open = items.filter(function (x) { return x.status === 'open'; }).length;
  return { status: 200, body: { ok: true, items: items, summary: { open: open, overdue: 0 } } };
}
function drillBody(items) { return { status: 200, body: { ok: true, items: items } }; }
// 新しいページを開く (偽の DOM を作り直して inline script を実行する)
async function bootPage(path, search, hash) {
  ELS = {}; TAB_BTNS = ['schedule', 'homework', 'videos', 'messages'].map(function (t) { var b = new FakeEl(); b.setAttribute('data-tab', t); return b; });
  HIST = []; FETCHES = []; TIMERS = [];
  setLoc(path || '/class.html', search, hash);
  if (window.AJHwNotice) window.AJHwNotice._clearMemory();
  __bootClass();
  await flush();
}
function tab(name) { TAB_BTNS.filter(function (b) { return b.getAttribute('data-tab') === name; })[0].dispatch('click'); }
function visibleTab() { var v = ['schedule', 'homework', 'videos', 'messages'].filter(function (t) { return ELS['view-' + t] && ELS['view-' + t].hidden === false; }); return v.join(','); }
function banner() { var b = ELS.hwNotice; return (b && !b.hidden) ? b.innerHTML : ''; }
var D1 = { drill_id: 301, title: '時制ドリル（10問）', unit: '時制', subject: 'english', status: 'assigned', score_total: 10, assigned_at: utcNaive(HOUR) };
var D2 = { drill_id: 302, title: '関係詞ドリル', unit: '関係詞', subject: 'english', status: 'open', score_total: 10, assigned_at: utcNaive(10 * DAY) };
var D3 = { drill_id: 303, title: '比較ドリル', unit: '比較', subject: 'english', status: 'completed', score_correct: 7, score_total: 10, assigned_at: utcNaive(5 * DAY), completed_at: utcNaive(4 * DAY) };
var D4 = { drill_id: 304, title: '今日の1問', unit: '今日の1問', subject: 'english', status: 'open', score_total: 1, assigned_at: utcNaive(HOUR), self_issued: true };
var H1 = { id: 401, title: '音読の宿題', subject: 'english', topic: '', status: 'open', created_at: utcNaive(2 * HOUR), due_date: '2999-12-31' };
var H2 = { id: 402, title: '前の宿題', subject: 'english', topic: '', status: 'completed', created_at: utcNaive(9 * DAY), completed_at: utcNaive(8 * DAY) };
"""

JS_CLASS_CASES = r"""
(async function () {
  try {
    // (E1) hw-notice.js が読めなかった端末 (帯は出ないが、'assigned' は未提出のまま数える)
    setApi({ '/api/student/homework': hwBody([H1, H2]), '/api/student/grammar-drills': drillBody([D1, D2, D3, D4]) });
    await bootPage('/class.html', '', '');
    eq('hw-notice.js なし: 予定タブで開く', visibleTab(), 'schedule');
    eq('hw-notice.js なし: 帯は出ない', banner(), '');
    eq('hw-notice.js なし: バッジは宿題 1 + 未提出ドリル 3 (assigned も)', ELS.hwBadge && ELS.hwBadge.textContent, 4);
    tab('homework'); await flush();
    var h0 = ELS.homeworkBody.innerHTML;
    eq('hw-notice.js なし: assigned のドリルも「未提出」で「▶ 解いて提出する」', count(h0, '▶ 解いて提出する'), 3);
    eq('hw-notice.js なし: 🆕 新着は付かない', count(h0, '🆕 新着'), 0);

    // (A) hw-notice.js あり・記録の無い端末
    __loadHwNotice();
    var st = memStore();
    if (!setWindowStorage({ configurable: true, writable: true, value: st })) window.AJHwNotice._useStorage(st);
    await bootPage('/class.html', '', '');
    eq('予定タブで開く', visibleTab(), 'schedule');
    ok('帯「🆕 新しい宿題が 2 件届いています」(届いて 72 時間以内のドリル + 宿題。自分で始めた今日の1問は数えない)',
       banner().indexOf('🆕 新しい宿題が 2 件届いています') >= 0 && banner().indexOf('class="hw-notice"') >= 0, banner());
    eq('バッジは宿題 1 + 未提出ドリル 3', ELS.hwBadge.textContent, 4);
    ELS.hwNotice.querySelector('button').dispatch('click');
    await flush();
    eq('帯を押すと宿題タブ', visibleTab(), 'homework');
    eq('宿題タブでは帯を隠す', banner(), '');
    var h1 = ELS.homeworkBody.innerHTML;
    eq('🆕 新着はドリル 1 枚 + 宿題 1 枚', count(h1, '🆕 新着'), 2);
    ok('🆕 新着は新しいドリル (assigned) のカードに付く', /chip-open">未提出<\/span> <span class="chip chip-new">🆕 新着<\/span>[^]*?data-id="301"/.test(h1), h1.slice(0, 600));
    eq('assigned のドリルは「完了」ではなく未提出 (▶ 3 枚・🔁 1 枚)', [count(h1, '▶ 解いて提出する'), count(h1, '🔁 解説を見る')], [3, 1]);
    ok('カードの 2 行目 (gdMetaText) は今までと同じ', h1.indexOf('その場で自動採点 ・ いつでもOK') >= 0 && h1.indexOf('スコア 7 / 10') >= 0);
    var rec = JSON.parse(st._m['aj_hw_seen_v1:7'] || 'null');
    eq('宿題タブを開いたら「見た」と記録 (未提出の ID)', rec && [rec.d, rec.h], [['301', '302', '304'], ['401']]);
    tab('schedule');
    eq('見た後は帯が消える', banner(), '');

    // (B) 次のページ: ?tab=homework (お知らせメールのリンク) で宿題タブに着地。新しく届いたドリルだけ 🆕
    var D5 = { drill_id: 305, title: '仮定法ドリル', unit: '仮定法', subject: 'english', status: 'open', score_total: 10, assigned_at: utcNaive(10 * 60 * 1000) };
    setApi({ '/api/student/homework': hwBody([H1, H2]), '/api/student/grammar-drills': drillBody([D5, D1, D2, D3, D4]) });
    await bootPage('/class.html', '?tab=homework', '');
    eq('?tab=homework で宿題タブに着地', visibleTab(), 'homework');
    eq('?tab=homework は URL から消す', HIST, ['/class.html']);
    eq('新しく届いたドリルだけ 🆕', count(ELS.homeworkBody.innerHTML, '🆕 新着'), 1);
    eq('宿題タブにいる間は帯を出さない', banner(), '');
    tab('schedule');
    eq('見た後は予定タブでも帯なし', banner(), '');

    // (C) dojo-drill から #homework で戻る (ほかのクエリは残す)
    await bootPage('/class.html', '?ref=x', '#homework');
    eq('#homework で宿題タブに着地', visibleTab(), 'homework');
    eq('#homework だけ消してクエリは残す', HIST, ['/class.html?ref=x']);
    await bootPage('/class.html', '?tab=schedule&ref=x', '#top');
    eq('?tab=homework 以外は予定タブ・tab だけ消す (# は残す)', [visibleTab(), HIST], ['schedule', ['/class.html?ref=x#top']]);

    // (D) 401 → ログインのリンクに redirect= (ログイン後に宿題タブへ戻る)
    setApi({ '/api/student/class/feed': { status: 401, body: { detail: 'Unauthorized' } } });
    await bootPage('/class.html', '?tab=homework', '');
    ok('401: login.html?redirect=%2Fclass.html%3Ftab%3Dhomework', ELS.gate.innerHTML.indexOf('href="login.html?redirect=%2Fclass.html%3Ftab%3Dhomework"') >= 0, ELS.gate.innerHTML);

    // (F) 宿題 API が 403 (通塾生コース外) でも、配られたドリルは出す
    var D6 = { drill_id: 306, title: '分詞ドリル', unit: '分詞', subject: 'english', status: 'open', score_total: 10, assigned_at: utcNaive(HOUR) };
    setApi({ '/api/student/homework': { status: 403, body: { detail: 'forbidden' } }, '/api/student/grammar-drills': drillBody([D6]) });
    await bootPage('/class.html', '', '');
    ok('宿題 403 でもドリルは帯に数える', banner().indexOf('🆕 新しい宿題が 1 件届いています') >= 0, banner());
    eq('宿題 403 でもバッジはドリルを数える', ELS.hwBadge.textContent, 1);
    tab('homework'); await flush();
    var h3 = ELS.homeworkBody.innerHTML;
    ok('宿題 403: 行き止まりの文ではなくドリルを出す', h3.indexOf('data-id="306"') >= 0 && h3.indexOf('通塾生のみ') < 0, h3.slice(0, 300));
    setApi({ '/api/student/homework': { status: 403, body: { detail: 'forbidden' } }, '/api/student/grammar-drills': drillBody([]) });
    await bootPage('/class.html', '', '');
    tab('homework'); await flush();
    ok('宿題 403 でドリルも無ければ今までの案内', ELS.homeworkBody.innerHTML.indexOf('通塾生のみ') >= 0);

    // (G) 新しいものは無いが〆を過ぎた宿題がある → 〆を過ぎた帯 (2026-10-18 から 〆 の言い方)
    var H3 = { id: 403, title: '単語テストの準備', subject: 'english', topic: '', status: 'open', created_at: utcNaive(20 * DAY), due_date: '2000-01-01' };
    var stG = memStore();
    if (!setWindowStorage({ configurable: true, writable: true, value: stG })) window.AJHwNotice._useStorage(stG);
    stG._m['aj_hw_seen_v1:7'] = JSON.stringify({ v: 1, d: [], h: ['403'] });   // 前に見た宿題
    setApi({ '/api/student/homework': hwBody([H3]), '/api/student/grammar-drills': drillBody([]) });
    await bootPage('/class.html', '', '');
    ok('〆を過ぎただけなら「⚠️ 〆を過ぎた宿題が 1 件あります」(赤い帯)', banner().indexOf('⚠️ 〆を過ぎた宿題が 1 件あります') >= 0 && banner().indexOf('hw-notice warn') >= 0, banner());

    // (H) ドリルの取得に失敗: 帯は取れた宿題だけで数え、ドリルの記録は変えない
    var st2 = memStore();
    if (!setWindowStorage({ configurable: true, writable: true, value: st2 })) window.AJHwNotice._useStorage(st2);
    st2._m['aj_hw_seen_v1:7'] = JSON.stringify({ v: 1, d: ['301'], h: [] });
    setApi({ '/api/student/homework': hwBody([H1]), '/api/student/grammar-drills': { status: 500, body: { detail: 'Internal Server Error' } } });
    await bootPage('/class.html', '', '');
    ok('ドリルが取れなくても宿題の新着は帯に出る', banner().indexOf('🆕 新しい宿題が 1 件届いています') >= 0, banner());
    eq('片方が取れなければバッジは出さない (今までどおり)', ELS.hwBadge ? ELS.hwBadge.textContent : '', '');
    tab('homework'); await flush();
    eq('ドリルが取れなかったときはドリルの記録を残す', JSON.parse(st2._m['aj_hw_seen_v1:7']).d, ['301']);

    // (E2) localStorage が throw する端末: 帯は出て、宿題タブを見たらページ内で消える
    //   (window.localStorage を差し替えられない JS エンジンでは、throw する偽物を hw-notice.js に直接渡して同じことを確かめる)
    var THROWING = { getItem: function () { throw new Error('SecurityError'); }, setItem: function () { throw new Error('SecurityError'); } };
    if (setWindowStorage({ configurable: true, get: function () { throw new Error('SecurityError'); } })) window.AJHwNotice._useStorage(undefined);
    else window.AJHwNotice._useStorage(THROWING);
    setApi({ '/api/student/homework': hwBody([H1]), '/api/student/grammar-drills': drillBody([D1]) });
    await bootPage('/class.html', '', '');
    ok('保存できない端末でも帯は出る', banner().indexOf('🆕 新しい宿題が 2 件届いています') >= 0, banner());
    tab('homework'); await flush();
    tab('schedule');
    eq('保存できない端末でも見たら帯が消える', banner(), '');
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


def run_js(engine, program, label):
    with tempfile.TemporaryDirectory(prefix="hw_notice_js_") as td:
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


def mypage_homework_slice(js):
    a = js.index("function _hwEscape(s) {")
    b = js.index("// 📝 単元別ドリル (英文法 4 択ドリル")
    return js[a:b]


def main():
    hw_src = read(HW_JS)
    class_html = read(CLASS_HTML)
    mypage_html = read(MYPAGE_HTML)
    mypage_js = read(MYPAGE_JS)
    class_inline = inline_scripts(class_html)
    load_hw = "function __loadHwNotice() {\n" + hw_src + "\n}\n"

    eng = js_engine()
    print(f"JS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng),
          "node も osascript も jsc も見つからない (AJ_JS_ENGINE の指定も確認)")

    if eng:
        print("\n[1] hw-notice.js の関数")
        run_js(eng, PRELUDE + load_hw + JS_PURE, "[1]")

        print("\n[2] mypage.js の宿題欄 (initHomeworkSection を偽の DOM で実行)")
        try:
            sl = mypage_homework_slice(mypage_js)
        except ValueError:
            sl = None
            check("mypage.js の宿題欄の範囲 (function _hwEscape 〜 「📝 単元別ドリル (英文法 4 択ドリル」) が見つかる", False)
        if sl:
            run_js(eng, PRELUDE + POLYFILL + FAKE_DOM + load_hw + JS_MYPAGE_SETUP + sl + "\n" + JS_MYPAGE_CASES, "[2]")

        print("\n[3] class.html の inline script を偽の DOM と偽の API で実行")
        if len(class_inline) != 1:
            check("class.html の inline script は 1 つ", False, len(class_inline))
        else:
            boot = "function __bootClass() {\n" + class_inline[0] + "\n}\n"
            run_js(eng, PRELUDE + POLYFILL + FAKE_DOM + load_hw + JS_CLASS_SETUP + boot + JS_CLASS_CASES, "[3]")

        print("\n[4] 構文 (new Function)")
        srcs = {"hw-notice.js": hw_src, "mypage.js": mypage_js}
        for i, b in enumerate(class_inline):
            srcs[f"class.html inline #{i}"] = b
        for i, b in enumerate(inline_scripts(mypage_html)):
            srcs[f"mypage.html inline #{i}"] = b
        run_js(eng, PRELUDE + "var SRC = " + json.dumps(srcs, ensure_ascii=True) + ";\n" + JS_SYNTAX, "[4]")

    print("\n[5] ソース検査")
    v_class = re.search(r'<script src="hw-notice\.js\?v=([^"]+)"></script>', class_html)
    v_my = re.search(r'<script src="hw-notice\.js\?v=([^"]+)"></script>', mypage_html)
    check("class.html が hw-notice.js?v= を読む", bool(v_class))
    check("mypage.html が hw-notice.js?v= を読む", bool(v_my))
    check("hw-notice.js の ?v= が 2 ページでそろう (変えたら両方上げる)", bool(v_class and v_my and v_class.group(1) == v_my.group(1)),
          (v_class and v_class.group(1), v_my and v_my.group(1)))
    i_guard = class_html.find('src="auth-guard.js')
    i_hw = class_html.find('src="hw-notice.js')
    i_inline = class_html.find("<script>", i_hw if i_hw >= 0 else 0)
    check("class.html: auth-guard.js → hw-notice.js → inline script の順", 0 <= i_guard < i_hw < i_inline, (i_guard, i_hw, i_inline))
    i_my_hw = mypage_html.find('src="hw-notice.js')
    i_my_js = mypage_html.find('src="mypage.js?v=')
    check("mypage.html: hw-notice.js を mypage.js より前に読む", 0 <= i_my_hw < i_my_js, (i_my_hw, i_my_js))
    check('class.html に <div id="hwNotice" hidden> がある', '<div id="hwNotice" hidden></div>' in class_html)
    check("class.html は ?tab= と #homework の両方で宿題タブに着地", ".get('tab')" in class_html and "location.hash === '#homework'" in class_html)
    check("class.html の 401 のログインに redirect=", "'login.html?redirect=' + encodeURIComponent(location.pathname + location.search)" in class_html)
    script = class_inline[0] if class_inline else ""
    left = re.findall(r"\.status\s*[!=]==?\s*'open'", script)
    check("class.html: ドリルの status === 'open' / !== 'open' が残っていない (gdIsOpen = completed 以外)", not left, left)
    check("class.html: gdIsOpen はバッジ・一覧・カード・先読みで使う",
          "gdDrills.filter(gdIsOpen)" in script and "var done = !gdIsOpen(it);" in script and "drills.filter(gdIsOpen)" in script)
    check("class.html: カードの 2 行目は gdMetaText(it) の 1 か所", "function gdMetaText(it)" in script and "var meta = gdMetaText(it);" in script)
    check("mypage.html: AIなし枠の送り返しで focus=homework を ?tab=homework に引き継ぐ",
          re.search(r"get\('focus'\)\s*===\s*'homework'\)\s*_q\s*=\s*'\?tab=homework'", mypage_html) is not None
          and "window.location.replace('class.html' + _q)" in mypage_html)
    my_code = re.sub(r"(^|\s)//.*$", r"\1", re.sub(r"/\*.*?\*/", "", mypage_js, flags=re.S), flags=re.M)   # コメントは除く
    bare = re.findall(r"(?<!window\.)\bAJHwNotice\b", my_code)
    refs = re.findall(r"window\.AJHwNotice", my_code)
    check("mypage.js の AJHwNotice は _hwNotice() 経由だけ (無ければ null = 今までどおり)", not bare and len(refs) == 2
          and "function _hwNotice() { return (typeof window !== 'undefined' && window.AJHwNotice) ? window.AJHwNotice : null; }" in mypage_js,
          (bare, len(refs)))
    code = re.sub(r"/\*.*?\*/", "", hw_src, flags=re.S)
    code = re.sub(r"(^|\s)//.*$", r"\1", code, flags=re.M)
    es6 = [p for p in (r"=>", r"\blet\s", r"\bconst\s", r"`", r"\bclass\s", r"\.\.\.") if re.search(p, code)]
    check("hw-notice.js は ES5 (=> / let / const / ` / class / ... を使わない)", not es6, es6)
    check("hw-notice.js は DOM に触らない (document を使わない)", "document." not in code)
    check("hw-notice.js の記録のキーは aj_hw_seen_v1:", "var KEY_PREFIX = 'aj_hw_seen_v1:';" in hw_src)
    ci = read(CI_YML)
    check("CI (server-tests.yml) にこのテストの step がある", "python3 scripts/health_check/test_hw_notice_js.py" in ci)
    paths_block = ci.split("pull_request:")[0]
    for p in ("'class.html'", "'mypage.html'", "'mypage.js'", "'hw-notice.js'"):
        check(f"CI の paths に {p} (画面だけの push でも走らせる)", p in paths_block)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES[:20]))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
