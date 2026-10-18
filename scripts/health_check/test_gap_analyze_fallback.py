#!/usr/bin/env python3
"""🩹 マイページ「AI ギャップ分析」「AI 弱点プリント」の降格 (2026-10-19 塾長「ギャップ分析を直して」「弱点プリントも直して」) の回帰テスト。

本番では 10-12〜10-18 に 5 回中 5 回 503 だった: gemini-2.5-flash を max_tokens 3500 で 1 回だけ呼び、
2.5 Flash は考える分も出力の枠から使うので finish_reason=MAX_TOKENS で切れ (_call_gemini が例外にする)、
降格が無いので生徒に「AI 分析失敗」が出ていた。さらに画面 (mypage.js) は既定の 30 秒で待つのをやめていた。

固定する性質 (実際のルートを TestClient で呼ぶ・外部通信なし・DB は一時 SQLite・生徒は架空):
  [1] Gemini で答えられたら Sonnet は呼ばない。Gemini には max_tokens 16000 以上・JSON 強制・temperature 0.3
  [2] Gemini が切れた (例外) → Sonnet 4.6 で 1 回だけやり直し 200。同じ system / user プロンプト・kind・student_id を渡す
  [3] Gemini が空 / JSON が読めない / dict でない → Sonnet でやり直す
  [4] Sonnet の ```json フェンス・前後の文も読める
  [5] 両方駄目 → 503 (生徒に内部のエラー文を出さない)・Sonnet も読めない → 503「JSON 解析失敗」
  [6] Sonnet の 429 (ライトの上限) はそのまま 429
  [7] Gemini が未構成なら Gemini を呼ばずに Sonnet・両方未構成なら 503
  [8] Sonnet の答えにも同じスタサプの検査 (対象外の生徒はスタサプの提案を捨てる・総合分析からスタサプの文を落とす)
  [9] 画面: mypage.js のギャップ分析 2 か所 (ボタン・模試保存後の自動) とカリキュラム生成は Railway に直接送り (longApi・
      ★Vercel の中継は 120 秒で切る)、待ち時間はサーバの 1 回分 (Gemini 75 秒の打ち切り + Sonnet 180 秒・カリキュラム生成は
      100 + 180) **以上**・★Railway の「5 分データが流れない要求は切る」より短い (≤ 295 秒)・読み込み中の文が「10-25秒」
      「15-40秒」のままでない・6 か所の表示がすべて seq を渡す・ボタンは分析中に押せない・カリキュラム生成のサーバも Gemini に cap 100
  [10] 弱点プリント (POST /api/weak-points/generate-worksheet・同じ gemini-2.5-flash 4000 で 1 回だけ・降格なしだった):
      Gemini は 16000・JSON 強制・temperature 0.7 (今までの既定 = 問題の幅を変えない)・切れ / 空 / 問題が無い / 問題が dict でない
      → Sonnet (12000・210 秒・student_id)・dict でない / 問題文が空の問題は捨てて番号を詰める・n 問まで・AI が書いたスタサプは使わない・
      両方駄目なら 503 (内部の文を出さない)・429 はそのまま・画面は Railway 直で 60 + 210 秒以上・295 秒以下待つ・「15-30秒」の表示を直す
  [11] Gemini の打ち切り: ギャップ分析 75・弱点プリント 60 の _timeout_cap_s → _gemini_request_options は timeout = cap・
      SDK の 600 秒の再試行を cap の中の短い再試行 (503 だけ・20 秒以内) に替える。cap の無い呼び出しは今までと同じ (timeout だけ)
  [12] 画面の slApiFetch を JS エンジンで動かす: longApi は Railway 直 / それ以外は今までどおり同じオリジン・timeoutMs と longApi は
      fetch に渡さない・送る前に Railway 直の GET /api/health で 1 回だけ到達確認 (ヘッダなし・失敗 / ok でない / 5 秒で返らない
      → このページの間は同じオリジン・確かめ直さない)・Railway 直がすぐ失敗 (10 秒以内の TypeError) したら同じオリジンで 1 回だけ
      やり直す・10 秒より後の失敗とタイムアウトはやり直さない (二重に作らない)
  [13] ギャップ分析のモーダル: 古い要求の答えは捨てる (新しい分析を上書きしない)・閉じた (× / 背景 / Esc) 後に届いた答えでは
      開き直さない・開いた直後 0.8 秒の背景クリックと中身のクリックでは閉じない・新しい要求の読み込み中は開く

実行:
    python3 scripts/health_check/test_gap_analyze_fallback.py
    # exit 0 = PASS / 1 = FAIL
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MYPAGE_JS = os.path.join(REPO, "mypage.js")
MYPAGE_HTML = os.path.join(REPO, "mypage.html")
sys.path.insert(0, HERE)
from test_sapuri_lessons import load_main, make_student, student_token, phase  # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


REPLY = {"target_deviation": "65", "current_average": "58", "gap_summary": "数学が課題。全体は順調。",
         "subject_gaps": [{"subject": "数学", "current": 58, "target": 65, "gap": 7, "priority": "高", "trend_comment": "横ばい"}],
         "phase_adjustments": [{"phase_index": 0, "phase_name": "基礎期", "action": "教材追加", "detail": "演習量を増やす",
                                "new_materials": ["1対1対応"]}],
         "overall_recommendation": "毎日続ける。"}


class FakeGemini:
    def __init__(self):
        self.calls = []
        self.mode = "ok"      # ok / truncated / empty / garbage / list
        self.reply = REPLY

    def __call__(self, body, model=None, kind="chat"):
        self.calls.append({"body": body, "model": model, "kind": kind})
        if self.mode == "truncated":
            raise RuntimeError("Gemini response truncated (finish_reason=MAX_TOKENS, max_tokens=16000)")
        text = {"ok": json.dumps(self.reply, ensure_ascii=False), "empty": "", "garbage": "分析します。まず数学は",
                "list": "[1, 2, 3]"}[self.mode]
        return {"content": [{"type": "text", "text": text}], "_actual_model": "fake-gemini"}


class FakeSonnet:
    def __init__(self):
        self.calls = []
        self.mode = "ok"      # ok / fenced / garbage / fail503 / fail429 / boom
        self.reply = REPLY

    def __call__(self, body, kind="chat", student_id=None, skip_light=False):
        self.calls.append({"body": body, "kind": kind, "student_id": student_id})
        if self.mode == "fail503":
            raise MOD.HTTPException(status_code=503, detail="ALL TIERS FAILED: secret-internal-detail")
        if self.mode == "fail429":
            raise MOD.HTTPException(status_code=429, detail="今月の AI の回数を使い切りました")
        if self.mode == "boom":
            raise ValueError("secret-internal-detail")
        js = json.dumps(self.reply, ensure_ascii=False)
        text = {"ok": js, "fenced": "以下が分析です。\n```json\n" + js + "\n```", "garbage": "I need to analyze this first..."}[self.mode]
        return {"content": [{"type": "text", "text": text}], "_actual_model": "fake-sonnet"}


MOD = None

_JS_OUT = ("var __s = 'RESULT ' + JSON.stringify(__o);\n"
           "if (typeof console !== 'undefined' && console.log) console.log(__s); else if (typeof print === 'function') print(__s);\n")

_JS_FETCH = r"""
var window = (typeof globalThis !== 'undefined') ? globalThis : this;
window.location = { hostname: 'trillion-ai-juku.com', port: '', origin: 'https://trillion-ai-juku.com' };
var SL_API_BASE = 'https://trillion-ai-juku.com';
function _slToken() { return 'tok'; }
function _slFormatErrDetail(d) { return d || ''; }
var __calls = [], __mode = 'ok', __now = 1000, __probe = 'ok', __probes = [];
Date.now = function () { return __now; };
var fetch = function (url, opts) {
  opts = opts || {};
  if (url.indexOf('/api/health') >= 0) {
    __probes.push({ url: url, headers: !!opts.headers, cache: opts.cache || '' });
    if (__probe === 'ok') return Promise.resolve({ ok: true, status: 200 });
    if (__probe === 'bad') return Promise.resolve({ ok: false, status: 503 });
    if (__probe === 'fail') return Promise.reject(new TypeError('Failed to fetch'));
    return new Promise(function (res, rej) {   // hang: 到達確認の 5 秒 (テストでは 30ms) で abort
      if (opts.signal) opts.signal.addEventListener('abort', function () { rej(new Error('AbortError')); });
    });
  }
  __calls.push({ url: url, timeoutMs: ('timeoutMs' in opts), longApi: ('longApi' in opts), auth: (opts.headers || {}).Authorization || '' });
  var direct = url.indexOf('ai-juku-api-production.up.railway.app') >= 0;
  if (__mode === 'early' && direct) return Promise.reject(new TypeError('Failed to fetch'));
  if (__mode === 'late' && direct) { __now += 20000; return Promise.reject(new TypeError('Failed to fetch')); }
  if (__mode === 'all') return Promise.reject(new TypeError('Failed to fetch'));
  if (__mode === 'hang') return new Promise(function (res, rej) {
    opts.signal.addEventListener('abort', function () { rej(new Error('AbortError')); });
  });
  return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ ok: true }); } });
};
%(block)s
(async function () {
  var __o = {};
  async function go(mode, path, opts, probe, keepProbe) {
    __mode = mode; __calls = []; __now = 1000; __probe = probe || 'ok'; __probes = [];
    if (!keepProbe) _slLongBaseProbe = null;
    var err = null;
    try { await slApiFetch(path, opts); } catch (e) { err = String(e && e.message || e); }
    return { urls: __calls.map(function (c) { return c.url; }), calls: __calls, err: err, probes: __probes };
  }
  __o.pOk = await go('ok', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true }, 'ok');
  __o.pCached = await go('ok', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true }, 'fail', true);
  __o.pFail = await go('ok', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true }, 'fail');
  __o.pBad = await go('ok', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true }, 'bad');
  __o.pHang = await go('ok', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true }, 'hang');
  __o.pAfterHang = await go('ok', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true }, 'ok', true);
  __o.pShort = await go('ok', '/api/curricula/me', { method: 'GET' }, 'ok');
  __o.long = await go('ok', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true });
  __o.short = await go('ok', '/api/curricula/me', { method: 'GET' });
  __o.early = await go('early', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true });
  __o.late = await go('late', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true });
  __o.all = await go('all', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 5000, longApi: true });
  __o.shortFail = await go('all', '/api/curricula/me', { method: 'GET' });
  __o.hang = await go('hang', '/api/curricula/1/gap-analyze', { method: 'POST', timeoutMs: 30, longApi: true });
  %(out)s
})();
"""

_JS_MODAL = r"""
var window = (typeof globalThis !== 'undefined') ? globalThis : this;
function _style() {
  // 本物のブラウザと同じく cssText を読み解く (作るときの 'display:flex' がそのまま style.display になる)
  var s = {};
  Object.defineProperty(s, 'cssText', {
    set: function (v) {
      String(v || '').split(';').forEach(function (d) {
        var i = d.indexOf(':');
        if (i < 0) return;
        var k = d.slice(0, i).trim().replace(/-([a-z])/g, function (_, c) { return c.toUpperCase(); });
        if (k) s[k] = d.slice(i + 1).trim();
      });
    },
    get: function () { return ''; }
  });
  return s;
}
function _el() {
  var e = { style: _style(), innerHTML: '', _l: {}, _kids: {},
    addEventListener: function (t, f) { this._l[t] = f; },
    querySelector: function (sel) { if (!this._kids[sel]) this._kids[sel] = _el(); return this._kids[sel]; } };
  return e;
}
var __byId = {};
var __docL = {};
var document = {
  getElementById: function (id) { return __byId[id] || null; },
  createElement: function () { return _el(); },
  body: { appendChild: function (e) { __byId[e.id] = e; } },
  addEventListener: function (t, f) { __docL[t] = f; }
};
function escapeHtml(s) { return String(s == null ? '' : s); }
var __now = 100000;
Date.now = function () { return __now; };
%(block)s
var __o = {};
var cur = { target_university: 'テスト大学' };
function st() { var m = __byId['gapAnalysisModal']; return m ? { display: m.style.display, body: m.querySelector('#gapModalBody').innerHTML } : null; }
// 0) ページで初めて開く (モーダルを作る) 直後の背景クリック = ダブルクリックの 2 回目 → 閉じない・答えは出る
var z = ++_gapSeq; showGapAnalysisModal('loading', { curriculum: cur, seq: z });
__o.firstCss = st();
__now += 200;
__byId['gapAnalysisModal']._l.click({ target: __byId['gapAnalysisModal'] });
showGapAnalysisModal('error', { curriculum: cur, error: 'FIRST-ANSWER', seq: z });
__o.firstBd = st();
__now += 5000;
// 1) 古い要求の答えは捨てる
var a = ++_gapSeq; showGapAnalysisModal('loading', { curriculum: cur, seq: a });
var b = ++_gapSeq; showGapAnalysisModal('loading', { curriculum: cur, seq: b });
showGapAnalysisModal('error', { curriculum: cur, error: 'OLD-ANSWER', seq: a });
__o.stale = st();
showGapAnalysisModal('error', { curriculum: cur, error: 'NEW-ANSWER', seq: b });
__o.fresh = st();
// 2) 閉じた後に届いた答えでは開き直さない
var c = ++_gapSeq; showGapAnalysisModal('loading', { curriculum: cur, seq: c });
__byId['gapAnalysisModal'].querySelector('#gapModalClose')._l.click();
__o.closed = st();
showGapAnalysisModal('error', { curriculum: cur, error: 'AFTER-CLOSE', seq: c });
__o.afterClose = st();
// 3) 新しい要求の読み込み中は開く・その答えも出す
var d = ++_gapSeq; showGapAnalysisModal('loading', { curriculum: cur, seq: d });
__o.reopen = st();
showGapAnalysisModal('error', { curriculum: cur, error: 'D-ANSWER', seq: d });
__o.dAnswer = st();
// 4) Esc でも閉じた扱い
var e2 = ++_gapSeq; showGapAnalysisModal('loading', { curriculum: cur, seq: e2 });
__docL.keydown({ key: 'Escape' });
showGapAnalysisModal('error', { curriculum: cur, error: 'AFTER-ESC', seq: e2 });
__o.afterEsc = st();
// 5) 背景クリック: 開いた直後 (0.8 秒以内 = 開いたボタンの二重押し) は閉じない・その後は閉じた扱い・中身のクリックは閉じない
var m = __byId['gapAnalysisModal'];
m.style.display = 'none';
__now += 5000;
var f = ++_gapSeq; showGapAnalysisModal('loading', { curriculum: cur, seq: f });
m._l.click({ target: m });
__o.bdEarly = st();
__now += 1000;
m._l.click({ target: {} });
__o.bdInner = st();
m._l.click({ target: m });
showGapAnalysisModal('error', { curriculum: cur, error: 'AFTER-BACKDROP', seq: f });
__o.bdLate = st();
// 6) 分析中にボタンを押し直す (閉じた後) = ボタン側の「開き直す」手順 → 新しく送らず、その分析の答えが出る
var g = ++_gapSeq; showGapAnalysisModal('loading', { curriculum: cur, seq: g });
__byId['gapAnalysisModal'].querySelector('#gapModalClose')._l.click();
_gapDismissedSeq = g - 1; showGapAnalysisModal('loading', { curriculum: cur, seq: g });   // mypage.js のボタンの手順と同じ
__o.reopenLoading = st();
showGapAnalysisModal('error', { curriculum: cur, error: 'REOPEN-ANSWER', seq: g });
__o.reopenAnswer = st();
// 7) seq なし (今までの呼び方) は今までどおり開く
__byId['gapAnalysisModal'].style.display = 'none';
showGapAnalysisModal('error', { curriculum: cur, error: 'NO-SEQ' });
__o.noSeq = st();
%(out)s
"""


def _block(js, start_pat, end_pat):
    i = js.find(start_pat)
    if i < 0:
        return None
    j = js.find(end_pat, i)
    if j < 0:
        return None
    return js[i:j + len(end_pat)]


def js_checks(js):
    print("\n[12] 画面の slApiFetch を JS エンジンで動かす (Railway 直・送る前の失敗だけ 1 回やり直す)")
    from test_grade_band_consistency import js_engine, run_js
    eng = js_engine()
    check("JS エンジンは node (setTimeout と AbortController が要る・CI は node)", bool(eng) and os.path.basename(eng[0]) == "node", eng)
    if not eng or os.path.basename(eng[0]) != "node":
        return
    blk = _block(js, "const SL_GAP_ANALYZE_TIMEOUT_MS", "\n  return res.json();\n}\n")
    check("slApiFetch と定数を切り出せる", bool(blk) and "async function slApiFetch" in blk
          and "const SL_LONG_API_PROBE_MS = 5000;" in blk)
    if not blk:
        return
    blk = blk.replace("const SL_LONG_API_PROBE_MS = 5000;", "const SL_LONG_API_PROBE_MS = 30;")   # 到達確認の 5 秒をテストでは 30ms
    out, err = run_js(eng, _JS_FETCH % {"block": blk, "out": _JS_OUT})
    check("JS が最後まで動く", out is not None, err)
    if out:
        D = "https://ai-juku-api-production.up.railway.app/api/curricula/1/gap-analyze"
        O = "https://trillion-ai-juku.com/api/curricula/1/gap-analyze"
        p = out["pOk"]
        check("到達確認: Railway 直の GET /api/health を 1 回 (ヘッダなし = preflight なし・cache no-store) → 届けば Railway 直",
              len(p["probes"]) == 1 and p["probes"][0]["url"] == "https://ai-juku-api-production.up.railway.app/api/health"
              and not p["probes"][0]["headers"] and p["probes"][0]["cache"] == "no-store" and p["urls"] == [D], p)
        check("到達確認はページの間 1 回だけ (2 回目は確かめない)", out["pCached"]["probes"] == [] and out["pCached"]["urls"] == [D], out["pCached"])
        for k, label in (("pFail", "失敗"), ("pBad", "ok でない (503)"), ("pHang", "5 秒で返らない (詰まる形)")):
            check(f"到達確認が{label} → 重い POST は Vercel 経由で 1 回 (Railway 直には送らない)",
                  out[k]["urls"] == [O] and out[k]["err"] is None, out[k])
        check("詰まった判定はページの間おぼえる (次も Vercel 経由・確かめ直さない)",
              out["pAfterHang"]["urls"] == [O] and out["pAfterHang"]["probes"] == [], out["pAfterHang"])
        check("longApi でない呼び出しは到達確認をしない", out["pShort"]["probes"] == [] and out["pShort"]["urls"] == ["https://trillion-ai-juku.com/api/curricula/me"],
              out["pShort"])
        lg, sh = out["long"], out["short"]
        check("longApi → Railway 直に 1 回 (Vercel を通さない)",
              lg["urls"] == ["https://ai-juku-api-production.up.railway.app/api/curricula/1/gap-analyze"] and lg["err"] is None, lg)
        check("longApi でない呼び出しは今までどおり同じオリジン", sh["urls"] == ["https://trillion-ai-juku.com/api/curricula/me"], sh)
        check("timeoutMs と longApi は fetch に渡さない・Authorization は付く",
              all(not c["timeoutMs"] and not c["longApi"] and c["auth"] == "Bearer tok" for c in lg["calls"] + sh["calls"]), lg["calls"])
        check("Railway 直が送る前に失敗 → 同じオリジンで 1 回だけやり直して成功",
              out["early"]["urls"] == ["https://ai-juku-api-production.up.railway.app/api/curricula/1/gap-analyze",
                                       "https://trillion-ai-juku.com/api/curricula/1/gap-analyze"] and out["early"]["err"] is None, out["early"])
        check("10 秒より後の失敗はやり直さない (二重に作らない)",
              len(out["late"]["urls"]) == 1 and out["late"]["err"], out["late"])
        check("やり直しも失敗 → エラー (2 回まで)", len(out["all"]["urls"]) == 2 and out["all"]["err"], out["all"])
        check("longApi でない呼び出しはやり直さない", len(out["shortFail"]["urls"]) == 1 and out["shortFail"]["err"], out["shortFail"])
        check("タイムアウトはやり直さず「タイムアウト」の文", len(out["hang"]["urls"]) == 1 and "タイムアウト" in (out["hang"]["err"] or ""), out["hang"])

    print("\n[13] ギャップ分析のモーダル (古い答えを捨てる・閉じた後に開き直さない)")
    i = js.find("let _gapSeq = 0;")
    k = js.find("function showGapAnalysisModal", i)
    j = js.find("\n}\n", k) if k >= 0 else -1
    mb = js[i:j + 3] if i >= 0 and j >= 0 else None
    check("モーダルのコードを切り出せる", bool(mb))
    if not mb:
        return
    out, err = run_js(eng, _JS_MODAL % {"block": mb, "out": _JS_OUT})
    check("JS が最後まで動く (モーダル)", out is not None, err)
    if out:
        check("古い要求の答えは捨てる (新しい読み込み中のまま)", "OLD-ANSWER" not in out["stale"]["body"] and "分析中" in out["stale"]["body"], out["stale"])
        check("新しい要求の答えは出す", "NEW-ANSWER" in out["fresh"]["body"] and out["fresh"]["display"] == "flex", out["fresh"])
        check("× で閉じる", out["closed"]["display"] == "none", out["closed"])
        check("閉じた後に届いた答えでは開き直さない", out["afterClose"]["display"] == "none" and "AFTER-CLOSE" not in out["afterClose"]["body"],
              out["afterClose"])
        check("新しい要求の読み込み中は開く", out["reopen"]["display"] == "flex" and "分析中" in out["reopen"]["body"], out["reopen"])
        check("その答えも出す", "D-ANSWER" in out["dAnswer"]["body"] and out["dAnswer"]["display"] == "flex", out["dAnswer"])
        check("Esc で閉じた後の答えでも開き直さない", out["afterEsc"]["display"] == "none" and "AFTER-ESC" not in out["afterEsc"]["body"], out["afterEsc"])
        check("模型も本物どおり: 作るときの cssText の display:flex で開いている", out["firstCss"]["display"] == "flex", out["firstCss"])
        check("ページで初めて開いた直後の背景クリック (ダブルクリックの 2 回目) でも閉じない・答えが出る",
              out["firstBd"]["display"] == "flex" and "FIRST-ANSWER" in out["firstBd"]["body"], out["firstBd"])
        check("閉じた後にボタンを押し直す → 読み込み中で開き直し、その分析の答えが出る",
              out["reopenLoading"]["display"] == "flex" and "分析中" in out["reopenLoading"]["body"]
              and out["reopenAnswer"]["display"] == "flex" and "REOPEN-ANSWER" in out["reopenAnswer"]["body"], (out["reopenLoading"], out["reopenAnswer"]))
        check("開いた直後 (0.8 秒以内) の背景クリックでは閉じない (二重押しの 2 回目)", out["bdEarly"]["display"] == "flex", out["bdEarly"])
        check("中身のクリックでは閉じない", out["bdInner"]["display"] == "flex", out["bdInner"])
        check("0.8 秒より後の背景クリックは閉じた扱い (後から届いた答えで開き直さない)",
              out["bdLate"]["display"] == "none" and "AFTER-BACKDROP" not in out["bdLate"]["body"], out["bdLate"])
        check("seq なしの呼び方は今までどおり開く", out["noSeq"]["display"] == "flex" and "NO-SEQ" in out["noSeq"]["body"], out["noSeq"])


def main():
    global MOD
    print("🩹 AI ギャップ分析の降格 回帰テスト\n")
    mod = load_main()
    MOD = mod
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    gem, son = FakeGemini(), FakeSonnet()
    mod._call_gemini = gem
    mod._call_anthropic_safe = son
    mod.GEMINI_API_KEY = "test-gemini"
    mod.ANTHROPIC_API_KEY = "test-anthropic"

    sid = make_student(mod, "ギャップ分析 A", "gap-a@example.org", labels=[])   # スタサプ対象外 (授業コースなし)
    tok = {"Authorization": "Bearer " + student_token(mod, sid)}
    today = mod._today_jst()
    sd, ed = today.isoformat(), (today + datetime.timedelta(days=200)).isoformat()
    r = client.post("/api/curricula", json={"target_university": "テスト大学", "exam_date": ed, "start_date": sd,
                                            "phases": [phase("基礎期", sd, ed, materials=["ポラリス1"])]}, headers=tok)
    assert r.status_code == 200, r.text
    cid = client.get("/api/curricula/me", headers=tok).json()["curricula"][0]["id"]
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid, "テスト模試", sd, "数学", 58.0))
    conn.commit(); conn.close()

    def run(gmode="ok", smode="ok", reply=None):
        mod._RATE_LIMIT_STORE.clear()
        gem.calls.clear(); son.calls.clear()
        gem.mode, son.mode = gmode, smode
        gem.reply = REPLY
        son.reply = reply or REPLY
        return client.post(f"/api/curricula/{cid}/gap-analyze", headers=tok)

    print("[1] Gemini で答えられたら Sonnet は呼ばない")
    r = run("ok")
    j = r.json() if r.status_code == 200 else {}
    check("200・分析が返る・model は Gemini", r.status_code == 200 and j.get("analysis", {}).get("target_deviation") == "65"
          and j.get("model") == "fake-gemini", r.text)
    check("Sonnet は呼ばない", son.calls == [], son.calls)
    gb = gem.calls[0]["body"] if gem.calls else {}
    check("Gemini は max_tokens 16000 以上 (3500 では考える分で切れる)", int(gb.get("max_tokens") or 0) >= 16000, gb.get("max_tokens"))
    check("Gemini は JSON 強制・temperature 0.3・kind=curr_gap_analyze",
          gb.get("response_format") == {"type": "json_object"} and gb.get("temperature") == 0.3
          and gem.calls[0]["kind"] == "curr_gap_analyze", gb)

    print("\n[2] Gemini が切れた → Sonnet で 1 回だけやり直す")
    r = run("truncated")
    j = r.json() if r.status_code == 200 else {}
    check("200・model は Sonnet", r.status_code == 200 and j.get("model") == "fake-sonnet"
          and j.get("analysis", {}).get("overall_recommendation") == "毎日続ける。", r.text)
    check("Sonnet は 1 回だけ", len(son.calls) == 1, son.calls)
    sc = son.calls[0] if son.calls else {"body": {}}
    check("Sonnet: claude-sonnet-4-6・kind=curr_gap_analyze_fallback・student_id を渡す (ライトの上限が効く)",
          sc["body"].get("model") == "claude-sonnet-4-6" and sc.get("kind") == "curr_gap_analyze_fallback"
          and sc.get("student_id") == sid, sc)
    check("Sonnet にも同じ system / user プロンプト",
          sc["body"].get("system") == gb.get("system") and sc["body"].get("messages") == gb.get("messages"), sc["body"].get("system"))
    check("Sonnet には response_format (Gemini 専用の鍵) を送らない", "response_format" not in sc["body"], sc["body"])

    print("\n[3] Gemini が空 / JSON が読めない / dict でない → Sonnet でやり直す")
    for gm in ("empty", "garbage", "list"):
        r = run(gm)
        check(f"Gemini={gm}: 200 で Sonnet の答え", r.status_code == 200 and r.json().get("model") == "fake-sonnet"
              and len(son.calls) == 1, r.text)

    print("\n[4] Sonnet の ```json フェンス・前後の文も読める")
    r = run("truncated", "fenced")
    check("フェンス付きでも 200", r.status_code == 200 and r.json().get("analysis", {}).get("target_deviation") == "65", r.text)

    print("\n[5] 両方駄目 → 503 (内部のエラー文を出さない)")
    for sm in ("fail503", "boom"):
        r = run("truncated", sm)
        check(f"Sonnet={sm}: 503・詳細に内部の文を出さない", r.status_code == 503 and "secret-internal-detail" not in r.text
              and "応答できませんでした" in r.text and "Gemini response truncated" not in r.text, r.text)
    r = run("garbage", "garbage")
    check("Sonnet も読めない: 503「JSON 解析失敗」", r.status_code == 503 and "JSON 解析失敗" in r.text, r.text)

    print("\n[6] Sonnet の 429 (ライトの上限) はそのまま")
    r = run("truncated", "fail429")
    check("429 で回数の文", r.status_code == 429 and "回数" in r.text, r.text)

    print("\n[7] 鍵の構成")
    mod.GEMINI_API_KEY = ""
    r = run("ok")
    check("Gemini 未構成: Gemini を呼ばずに Sonnet で 200", r.status_code == 200 and gem.calls == [] and len(son.calls) == 1
          and r.json().get("model") == "fake-sonnet", r.text)
    mod.ANTHROPIC_API_KEY = ""
    r = run("ok")
    check("両方未構成: 503・どちらも呼ばない", r.status_code == 503 and gem.calls == [] and son.calls == [], r.text)
    mod.GEMINI_API_KEY = "test-gemini"
    r = run("truncated")
    check("Anthropic 未構成で Gemini が切れた: 503 (Sonnet は呼ばない)", r.status_code == 503 and son.calls == [], r.text)
    mod.ANTHROPIC_API_KEY = "test-anthropic"

    print("\n[8] Sonnet の答えにも同じスタサプの検査")
    sap = dict(REPLY)
    sap["gap_summary"] = "数学が課題。スタサプで補強しよう。全体は順調。"
    sap["phase_adjustments"] = [
        {"phase_index": 0, "action": "スタサプ追加", "detail": "数学の演習量を増やす", "new_materials": ["1対1対応"],
         "new_sapuri": [{"course_code": "MKZ371000", "from_seq": 1, "to_seq": 5}]},
        {"phase_index": 0, "action": "教材追加", "detail": "スタディサプリの講座を見る", "new_materials": []},
    ]
    r = run("truncated", "ok", reply=sap)
    a = r.json().get("analysis", {}) if r.status_code == 200 else {}
    adj = a.get("phase_adjustments") or []
    check("対象外: スタサプの語を含む提案は捨て、残りは「教材追加」・スタサプは空",
          len(adj) == 1 and adj[0].get("action") == "教材追加" and adj[0].get("new_sapuri") == [], adj)
    check("対象外: 総合分析からスタサプの文を落とす",
          "スタサプ" not in a.get("gap_summary", "") and "全体は順調" in a.get("gap_summary", ""), a.get("gap_summary"))

    print("\n[9] 画面 (mypage.js) の待ち時間")
    js = open(MYPAGE_JS, encoding="utf-8").read()
    calls = re.findall(r"slApiFetch\(`/api/curricula/\$\{encodeURIComponent\([^)]*\)\}/gap-analyze`,\s*\{([^}]*)\}\)", js)
    check("ギャップ分析の呼び出しは 2 か所 (ボタン・模試保存後の自動)", len(calls) == 2, calls)
    check("2 か所とも timeoutMs: SL_GAP_ANALYZE_TIMEOUT_MS・longApi: true (Railway 直)",
          len(calls) == 2 and all("timeoutMs: SL_GAP_ANALYZE_TIMEOUT_MS" in x and "longApi: true" in x for x in calls), calls)
    m = re.search(r"slApiFetch\('/api/curricula/ai-generate',\s*\{([\s\S]*?)body:", js)
    check("カリキュラム生成も timeoutMs: SL_CURRICULUM_AI_TIMEOUT_MS・longApi: true",
          bool(m) and "timeoutMs: SL_CURRICULUM_AI_TIMEOUT_MS" in m.group(1) and "longApi: true" in m.group(1), m.group(1) if m else "")
    check("Railway 直の送り先 (SL_LONG_API_BASE) は本番の API・ローカルの確認画面は localhost:8000",
          "'https://ai-juku-api-production.up.railway.app'" in js and re.search(r"const SL_LONG_API_BASE = [^;]*'http://localhost:8000'", js) is not None)

    def const(name):
        mm = re.search(r"const\s+" + name + r"\s*=\s*(\d+)\s*;", js)
        return int(mm.group(1)) if mm else None
    g, cg = const("SL_GAP_ANALYZE_TIMEOUT_MS"), const("SL_CURRICULUM_AI_TIMEOUT_MS")
    # ★Railway の入口は「5 分データが流れない要求は切る」→ 画面の待ちは 295 秒以下 (先に日本語のタイムアウトを出す)
    check("ギャップ分析の待ち時間はサーバの 1 回分 (Gemini 75 秒 + Sonnet 180 秒 = 255 秒) 以上・Railway の 300 秒より短い (≤ 295 秒)",
          g is not None and 255000 <= g <= 295000, g)
    check("カリキュラム生成の待ち時間はサーバの 1 回分 (Gemini 100 秒 + Sonnet 180 秒 = 280 秒) 以上・≤ 295 秒",
          cg is not None and 280000 <= cg <= 295000, cg)
    calls_all = re.findall(r"showGapAnalysisModal\('(?:loading|result|error)',\s*\{[^}]*curriculum:\s*(?:curr|active)[^}]*\}\)", js)
    check("ボタンと自動の 7 か所 (ボタン 3 + 開き直し 1・自動 3) すべて seq を渡す (古い答えを捨てる・閉じた後に開き直さない)",
          len(calls_all) == 7 and all(re.search(r"\bseq\b", x) for x in calls_all), calls_all)
    check("ボタンと自動の両方で ++_gapSeq", js.count("const seq = ++_gapSeq;") == 2)
    hb = re.search(r"\.cu-gap-btn'\)\.forEach\(b => b\.addEventListener\('click', \(\) => \{([\s\S]*?)\n    \}\)\);", js)
    hbt = hb.group(1) if hb else ""
    check("ギャップ分析ボタン: 分析中にもう一度押したら新しく送らず開き直す (b._gapSeq・閉じた印を戻す・finally で外す)",
          "if (b._gapSeq && b._gapSeq === _gapSeq) {" in hbt and "_gapDismissedSeq = b._gapSeq - 1;" in hbt
          and "showGapAnalysisModal('loading', { curriculum: curr, seq: b._gapSeq });" in hbt and "b._gapSeq = seq;" in hbt
          and "if (b._gapSeq === seq) b._gapSeq = null;" in hbt
          and hbt.index("if (b._gapSeq && b._gapSeq === _gapSeq)") < hbt.index("slApiFetch("), hbt)
    check("ギャップ分析ボタンを disabled にしない (閉じた後に数分押しても何も起きなかった)", "b.disabled = true" not in hbt, hbt)
    check("モーダルの開いた時刻は「開く前に見えていたか」で付ける (作るときの cssText に display:flex が入る)",
          "const wasOpen = !!modal && modal.style.display === 'flex';" in js and "if (!wasOpen) modal._openedAt = Date.now();" in js
          and js.index("const wasOpen") < js.index("modal = document.createElement('div');\n    modal.id = 'gapAnalysisModal';"))
    mod._RATE_LIMIT_STORE.clear()
    gem.calls.clear()
    r = client.post("/api/curricula/ai-generate", json={"target_university": "テスト大学", "exam_date": ed, "start_date": sd,
                                                        "daily_minutes": 60}, headers=tok)
    agc = gem.calls[-1] if gem.calls else {"body": {}, "kind": None}
    check("カリキュラム生成のサーバ: Gemini に _timeout_cap_s 100 (180 秒 + 503 の再試行 600 秒まで粘らない)",
          agc["body"].get("_timeout_cap_s") == 100 and agc["kind"] == "curriculum_gen", (agc["body"].get("_timeout_cap_s"), agc["kind"], r.status_code))
    check("slApiFetch は options.timeoutMs を使う (既定 30 秒)", "options.timeoutMs" in js and ": 30000;" in js)
    check("読み込み中の文が「10-25秒」「15-40秒」のままでない",
          "ギャップを分析中... (10-25秒)" not in js and "AI 生成中... (15-40秒)" not in js)


    print("\n[10] 弱点プリント (同じ降格)")
    WS = {"topic_used": "関係詞", "weak_point_analysis": "先行詞を見落とす。",
          "problems": [{"no": 1, "difficulty": "易", "question": "Q1", "answer": "A1", "explanation": "E1"},
                       "壊れた要素",
                       {"no": 2, "difficulty": "標準", "question": "  ", "answer": "空の問題", "explanation": ""},
                       {"no": 3, "difficulty": "応用", "question": "Q3", "answer": "A3", "explanation": "E3"}],
          "sapuri_lectures": [{"title": "高3 架空講座 (AI が書いた名前)", "level": "x", "reason": "y"}]}
    NOPROB = {"topic_used": "関係詞", "weak_point_analysis": "x", "problems": []}
    BADPROB = {"topic_used": "関係詞", "weak_point_analysis": "x", "problems": ["文字列だけ", 3]}

    def ws(gmode="ok", smode="ok", greply=None, sreply=None, n=8):
        mod._RATE_LIMIT_STORE.clear()
        gem.calls.clear(); son.calls.clear()
        gem.mode, son.mode = gmode, smode
        gem.reply = greply or WS
        son.reply = sreply or WS
        return client.post("/api/weak-points/generate-worksheet",
                           json={"subject": "英語", "topic": "関係詞", "num_problems": n}, headers=tok)

    r = ws("ok")
    j = r.json() if r.status_code == 200 else {}
    gb = gem.calls[0]["body"] if gem.calls else {}
    check("Gemini で作れたら 200・Sonnet は呼ばない・model は Gemini", r.status_code == 200 and son.calls == []
          and j.get("model") == "fake-gemini", r.text)
    check("Gemini は max_tokens 16000 以上 (4000 では 15 問と考える分で切れる)・JSON 強制・temperature 0.7・kind=weak_worksheet",
          int(gb.get("max_tokens") or 0) >= 16000 and gb.get("response_format") == {"type": "json_object"}
          and gb.get("temperature") == 0.7 and gem.calls[0]["kind"] == "weak_worksheet", gb)
    probs = j.get("problems") or []
    check("dict でない / 問題文が空の問題は捨てて番号を詰める", [p.get("question") for p in probs] == ["Q1", "Q3"]
          and [p.get("no") for p in probs] == [1, 2], probs)
    check("AI が書いたスタサプは使わない (対象外の生徒は [])", j.get("sapuri_lectures") == [] and "AI が書いた" not in r.text, r.text)
    r = ws("ok", n=3, greply=dict(WS, problems=[{"question": f"Q{i}", "answer": "a", "explanation": "e"} for i in range(1, 8)]))
    check("n 問まで (3 問)", r.status_code == 200 and len(r.json().get("problems") or []) == 3, r.text)

    r = ws("truncated")
    j = r.json() if r.status_code == 200 else {}
    sc = son.calls[0] if son.calls else {"body": {}}
    check("Gemini が切れた → Sonnet で 200 (model は Sonnet・1 回だけ)", r.status_code == 200 and j.get("model") == "fake-sonnet"
          and len(son.calls) == 1, r.text)
    check("Sonnet: claude-sonnet-4-6・max_tokens 12000・_timeout_s 210 (1 回分 60 + 210 = 270 秒 < Railway の 300 秒)・"
          "kind=weak_worksheet_fallback・student_id",
          sc["body"].get("model") == "claude-sonnet-4-6" and sc["body"].get("max_tokens") == 12000
          and sc["body"].get("_timeout_s") == 210 and sc.get("kind") == "weak_worksheet_fallback" and sc.get("student_id") == sid, sc)
    check("Sonnet にも同じ system / user・response_format は送らない",
          sc["body"].get("system") == gb.get("system") and sc["body"].get("messages") == gb.get("messages")
          and "response_format" not in sc["body"], sc["body"])
    for label, gm, gr in (("空", "empty", None), ("JSON が読めない", "garbage", None), ("問題が 0 問", "ok", NOPROB),
                          ("問題が dict でない", "ok", BADPROB)):
        r = ws(gm, greply=gr)
        check(f"Gemini が{label} → Sonnet で 200", r.status_code == 200 and r.json().get("model") == "fake-sonnet"
              and len(son.calls) == 1, r.text)
    r = ws("truncated", "ok", sreply=NOPROB)
    check("Sonnet も問題が 0 問 → 503", r.status_code == 503 and "解析失敗" in r.text, r.text)
    for sm in ("fail503", "boom"):
        r = ws("truncated", sm)
        check(f"Sonnet={sm}: 503・内部の文を出さない", r.status_code == 503 and "secret-internal-detail" not in r.text
              and "Gemini response truncated" not in r.text, r.text)
    r = ws("truncated", "fail429")
    check("Sonnet の 429 はそのまま", r.status_code == 429 and "回数" in r.text, r.text)
    mod.GEMINI_API_KEY = ""
    r = ws("ok")
    check("Gemini 未構成: Sonnet だけで 200", r.status_code == 200 and gem.calls == [] and len(son.calls) == 1, r.text)
    mod.ANTHROPIC_API_KEY = ""
    r = ws("ok")
    check("両方未構成: 503・どちらも呼ばない", r.status_code == 503 and gem.calls == [] and son.calls == [], r.text)
    mod.GEMINI_API_KEY, mod.ANTHROPIC_API_KEY = "test-gemini", "test-anthropic"

    js = open(MYPAGE_JS, encoding="utf-8").read()
    html = open(MYPAGE_HTML, encoding="utf-8").read()
    m = re.search(r"slApiFetch\('/api/weak-points/generate-worksheet',\s*\{([\s\S]*?)body:", js)
    check("画面: 弱点プリントは timeoutMs: SL_WORKSHEET_AI_TIMEOUT_MS・longApi: true",
          bool(m) and "timeoutMs: SL_WORKSHEET_AI_TIMEOUT_MS" in m.group(1) and "longApi: true" in m.group(1), m.group(1) if m else "")
    mm = re.search(r"const\s+SL_WORKSHEET_AI_TIMEOUT_MS\s*=\s*(\d+)\s*;", js)
    w = int(mm.group(1)) if mm else None
    check("画面: 待ち時間はサーバの 1 回分 (Gemini 60 秒 + Sonnet 210 秒 = 270 秒) 以上・≤ 295 秒 (Railway の 300 秒より短い)",
          w is not None and 270000 <= w <= 295000, w)
    check("画面: ボタンの「15-30秒」を直した (mypage.js・mypage.html)",
          "弱点プリントを生成 (15-30秒)" not in js and "問題作成中... (15-30秒)" not in js and "弱点プリントを生成 (15-30秒)" not in html)

    print("\n[11] Gemini の打ち切り (降格する呼び出しだけ cap・SDK の 600 秒の再試行を cap の中の短い再試行に)")
    r = ws("ok")
    gb = gem.calls[0]["body"] if gem.calls else {}
    check("弱点プリント: Gemini に _timeout_cap_s 60", gb.get("_timeout_cap_s") == 60, gb.get("_timeout_cap_s"))
    r = run("ok")
    gb = gem.calls[0]["body"] if gem.calls else {}
    check("ギャップ分析: Gemini に _timeout_cap_s 75", gb.get("_timeout_cap_s") == 75, gb.get("_timeout_cap_s"))
    ro = mod._gemini_request_options
    base = mod._GEMINI_TIMEOUT_S

    try:
        from google.api_core import retry as _gr, exceptions as _gx
        has_core = True
    except Exception:
        has_core = False
    check("google.api_core がある (server/requirements.txt の google-generativeai が引く = CI でも本番でもある)", has_core)

    def _rt_ok(o, t):
        rq = (o or {}).get("request_options") or {}
        rt = rq.get("retry", "missing")
        if rq.get("timeout") != t or rt == "missing":
            return False
        if rt is None:              # None (1 回だけ) を許すのは google.api_core が無い環境だけ
            return not has_core
        if not has_core or not isinstance(rt, _gr.Retry):
            return False
        win = getattr(rt, "timeout", None) or getattr(rt, "_timeout", None)
        pred = getattr(rt, "_predicate", None)
        try:
            p_ok = bool(pred and pred(_gx.ServiceUnavailable("x")) and not pred(ValueError("x"))
                        and not pred(_gx.ResourceExhausted("x")) and not pred(_gx.DeadlineExceeded("x")))
        except Exception:
            p_ok = False
        return win is not None and 5 <= float(win) <= 20 and float(win) < t and p_ok
    check("cap 75 → timeout 75・再試行は 503 だけ・20 秒以内 (cap の中で終わる)", _rt_ok(ro({"_timeout_cap_s": 75}), 75),
          ro({"_timeout_cap_s": 75}))
    check("cap は _timeout_s (max) より強い (300 と cap 75 → 75)", _rt_ok(ro({"_timeout_s": 300, "_timeout_cap_s": 75}), 75))
    check("cap 60 → 再試行の窓は cap の 1/3 (20 秒)", _rt_ok(ro({"_timeout_cap_s": 60}), 60))
    check("cap が既定より長くても既定を超えない (cap 600 → 既定)",
          ro({"_timeout_cap_s": 600})["request_options"]["timeout"] == min(base, 600) if base else True, ro({"_timeout_cap_s": 600}))
    check("cap の下限は 30 秒", ro({"_timeout_cap_s": 5})["request_options"]["timeout"] == 30, ro({"_timeout_cap_s": 5}))
    check("cap の無い呼び出しは今までと同じ (timeout だけ・retry を付けない)",
          ro({}) == ({"request_options": {"timeout": max(30, min(900, base))}} if base else {})
          and ro({"_timeout_s": 300}) == {"request_options": {"timeout": max(base or 0, 300)}}
          and ro(default_s=600) == {"request_options": {"timeout": 600}} and "retry" not in str(ro({"_timeout_s": 300})), (ro({}), ro({"_timeout_s": 300})))
    check("壊れた cap は無視 (今までと同じ)", ro({"_timeout_cap_s": "x"}) == ro({}), ro({"_timeout_cap_s": "x"}))

    js_checks(js)
    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
