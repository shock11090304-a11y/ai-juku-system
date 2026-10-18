/*
 * 💾 単元ドリルの解答の途中保存 (2026-10-18 塾長「②の残りも作っておいて」= 成績を上げる提案 ②「解答を途中で保存できるようにします。
 *   保存は端末の中だけです」)。塾生アプリ (class.html の gdOpen) とマイページ (mypage.js の openDrill) が同じものを使う。
 *
 * - 単元ドリル (クラス自動宿題・3日ドリル・塾長のドリル・今日の1問) は全問に答えないと提出できず、選んだ答えは画面の中にしか無かった
 *   (スマホで LINE を見に行ってタブが読み直されると全部消え、未提出のまま次の配信も止まる)。選ぶたびにこの端末に保存し、
 *   開き直したら戻す。提出できたら (二重提出の 409 でも) 消す。通信に失敗したときは残す。
 * - 保存先は localStorage 'aj_gd_draft_v1:<生徒ID>:<ドリルID>' (端末ごと・読み書きは全部 try/catch。使えない端末はページ内だけ)。
 *   中身は {v: 1, t: 問題数, n: 答えた数, a: {問題ID: [選んだ番号 (0 始まり), 問題の指紋]}, u: [自信なしの問題ID], at: 保存した時刻 (ms)}
 *   = 選んだ番号だけ (正解は提出までサーバから届かないので、保存しても答えは漏れない)。名前・メール・トークンは入れない。
 * - 戻すのは、今の問題に同じ問題 ID があり、問題文と選択肢の指紋が同じで、番号が選択肢の数より小さい答えだけ
 *   (塾長が問題を直したら、その問は戻さない)。60 日より古い下書きは使わず、保存したときに消す (端末に溜めない)。
 * - 一覧のカードの「途中 4/10」は progress / progressLabel (問題を読まずに、保存した数だけで出す)。
 * - 生徒 ID が分からないときは localStorage を使わない (同じ端末の別の生徒に戻さない)。
 * ★ES5 で書く (古い iOS Safari で読み込みに失敗すると途中保存が無くなるだけで、ドリルは今までどおり解ける)。
 * ★このファイルを変えたら class.html と mypage.html の gd-draft.js?v= を両方上げる (CI js_cache_bust.py)。
 * 回帰テスト: scripts/health_check/test_drill_draft.py (node / osascript / jsc で実際に動かす)。
 */
(function (root) {
  'use strict';
  var PREFIX = 'aj_gd_draft_v1:';
  var MAX_AGE_MS = 60 * 24 * 3600 * 1000;   // 60 日
  var mem = {};          // ページ内の下書き (localStorage が使えない端末の代わり)
  var testStore;         // テスト用の差し替え (undefined = root.localStorage)
  var hasOwn = Object.prototype.hasOwnProperty;

  function isArray(v) { return Object.prototype.toString.call(v) === '[object Array]'; }
  function toInt(v) {
    if (typeof v === 'number') return (isFinite(v) && Math.floor(v) === v) ? v : NaN;
    if (typeof v === 'string' && /^\d{1,3}$/.test(v)) return parseInt(v, 10);
    return NaN;
  }
  function nowMs() { return Date.now(); }
  function storage() {
    if (testStore !== undefined) return testStore;
    try { return root.localStorage || null; } catch (e) { return null; }
  }
  function key(sid, drillId) {
    var s = (sid == null) ? '' : String(sid), d = (drillId == null) ? '' : String(drillId);
    return (s && d) ? PREFIX + s + ':' + d : '';
  }
  function memKey(sid, drillId) { return String(sid == null ? '' : sid) + ':' + String(drillId == null ? '' : drillId); }

  // 問題の指紋 (問題文と選択肢の簡単なハッシュ + 選択肢の数)。塾長が問題を直したら一致しなくなる
  function fp(q) {
    var parts = [(q && q.stem != null) ? String(q.stem) : ''];
    var ch = (q && isArray(q.choices)) ? q.choices : [];
    for (var i = 0; i < ch.length; i++) parts.push(String(ch[i] == null ? '' : ch[i]));
    var s = parts.join('\u0001'), h = 5381;
    for (var j = 0; j < s.length; j++) h = ((h << 5) + h + s.charCodeAt(j)) | 0;
    return (h >>> 0).toString(36) + '.' + ch.length;
  }
  // 問題の配列 → {問題ID: {fp, n (選択肢の数)}}
  function qmap(qs) {
    var m = {};
    for (var i = 0; qs && i < qs.length; i++) {
      var q = qs[i];
      if (!q || q.question_id == null) continue;
      m[String(q.question_id)] = { fp: fp(q), n: isArray(q.choices) ? q.choices.length : 0 };
    }
    return m;
  }
  function fresh(rec) {
    if (!rec || typeof rec !== 'object' || rec.v !== 1 || !rec.a || typeof rec.a !== 'object' || isArray(rec.a)) return null;
    var at = Number(rec.at);
    if (!isFinite(at) || nowMs() - at > MAX_AGE_MS) return null;
    return rec;
  }
  // 保存してある下書き (検査前の生の値) か null。決して throw しない
  function readRaw(sid, drillId) {
    var k = key(sid, drillId), got = null;
    if (k) {
      try {
        var st = storage();
        var raw = st ? st.getItem(k) : null;
        if (raw) got = fresh(JSON.parse(raw));
      } catch (e) { got = null; }
    }
    if (!got) {
      try { got = fresh(mem[memKey(sid, drillId)]); } catch (e2) { got = null; }
    }
    return got;
  }

  // 今の問題に戻せる答え: {answers: {問題ID: 番号}, unsure: {問題ID: 1}, n: 戻せた答えの数, t: 問題数} か null
  function load(sid, drillId, qs) {
    var rec = readRaw(sid, drillId);
    if (!rec) return null;
    var m = qmap(qs), answers = {}, unsure = {}, n = 0, nu = 0, qid;
    for (qid in rec.a) {
      if (!hasOwn.call(rec.a, qid) || !hasOwn.call(m, qid)) continue;
      var e = rec.a[qid];
      if (!isArray(e)) continue;
      var idx = toInt(e[0]);
      if (!(idx >= 0 && idx < m[qid].n) || e[1] !== m[qid].fp) continue;
      answers[qid] = idx; n++;
    }
    if (isArray(rec.u)) {
      for (var i = 0; i < rec.u.length; i++) {
        var u = String(rec.u[i]);
        if (hasOwn.call(m, u) && !hasOwn.call(unsure, u)) { unsure[u] = 1; nu++; }
      }
    }
    if (!n && !nu) return null;
    return { answers: answers, unsure: unsure, n: n, t: (qs && qs.length) || 0 };
  }

  // 下書きを保存する。answers = {問題ID: 番号}・unsure = [問題ID] か {問題ID: true}。
  // 戻り値: 'stored' (この端末に保存) / 'memory' (このページの中だけ) / 'empty' (何も答えていない = 消した)。決して throw しない
  function save(sid, drillId, qs, answers, unsure) {
    var m = qmap(qs), a = {}, u = [], n = 0, qid;
    if (answers && typeof answers === 'object') {
      for (qid in answers) {
        if (!hasOwn.call(answers, qid) || !hasOwn.call(m, String(qid))) continue;
        var idx = toInt(answers[qid]);
        if (idx >= 0 && idx < m[String(qid)].n) { a[String(qid)] = [idx, m[String(qid)].fp]; n++; }
      }
    }
    if (isArray(unsure)) {
      for (var i = 0; i < unsure.length; i++) if (hasOwn.call(m, String(unsure[i]))) u.push(String(unsure[i]));
    } else if (unsure && typeof unsure === 'object') {
      for (qid in unsure) if (hasOwn.call(unsure, qid) && unsure[qid] && hasOwn.call(m, String(qid))) u.push(String(qid));
    }
    if (!n && !u.length) { clear(sid, drillId); return 'empty'; }
    var rec = { v: 1, t: (qs && qs.length) || 0, n: n, a: a, u: u, at: nowMs() };
    try { mem[memKey(sid, drillId)] = rec; } catch (e0) { /* noop */ }
    var k = key(sid, drillId);
    if (!k) return 'memory';
    try {
      var st = storage();
      if (st) {
        st.setItem(k, JSON.stringify(rec));
        prune(st, k);
        return 'stored';
      }
    } catch (e) { /* 保存できない端末 (容量・プライベート) はページ内だけ */ }
    return 'memory';
  }
  function clear(sid, drillId) {
    try { delete mem[memKey(sid, drillId)]; } catch (e0) { /* noop */ }
    var k = key(sid, drillId);
    if (!k) return;
    try { var st = storage(); if (st) st.removeItem(k); } catch (e) { /* noop */ }
  }
  // 60 日より古い (または壊れた) 下書きを消す。保存したとき 1 ページ 1 回だけ (端末に溜めない)
  var pruned = false;
  function prune(st, keep) {
    if (pruned) return;
    pruned = true;
    try {
      if (typeof st.key !== 'function' || typeof st.length !== 'number') return;
      var drop = [];
      for (var i = 0; i < st.length; i++) {
        var k = st.key(i);
        if (!k || k.indexOf(PREFIX) !== 0 || k === keep) continue;
        var rec = null;
        try { rec = fresh(JSON.parse(st.getItem(k))); } catch (e1) { rec = null; }
        if (!rec) drop.push(k);
      }
      for (var j = 0; j < drop.length; j++) { try { st.removeItem(drop[j]); } catch (e2) { /* noop */ } }
    } catch (e) { /* noop */ }
  }

  // 一覧のカード用: {n: 答えた数, t: 問題数} か null (問題を読まずに、保存した数だけで出す)
  function progress(sid, drillId) {
    var rec = readRaw(sid, drillId);
    if (!rec) return null;
    var n = 0, qid;
    for (qid in rec.a) if (hasOwn.call(rec.a, qid) && isArray(rec.a[qid])) n++;
    if (!n) return null;
    var t = toInt(rec.t);
    return { n: n, t: (t > 0 && t >= n) ? t : 0 };
  }
  function progressLabel(p) {
    if (!p || !(p.n > 0)) return '';
    return '途中 ' + p.n + (p.t ? ('/' + p.t) : ' 問');
  }
  // この端末に保存できるか (生徒 ID があり、localStorage に書いて消せる)。決して throw しない
  function canPersist(sid) {
    if (!key(sid, 'x')) return false;
    try {
      var st = storage();
      if (!st) return false;
      var pk = PREFIX + '__probe';
      st.setItem(pk, '1');
      st.removeItem(pk);
      return true;
    } catch (e) { return false; }
  }

  root.AJGdDraft = {
    PREFIX: PREFIX,
    MAX_AGE_MS: MAX_AGE_MS,
    fingerprint: fp,
    load: load,
    save: save,
    clear: clear,
    progress: progress,
    progressLabel: progressLabel,
    canPersist: canPersist,
    // テスト用 (scripts/health_check/test_drill_draft.py)。画面からは呼ばない
    _useStorage: function (s) { testStore = s; pruned = false; },
    _clearMemory: function () { mem = {}; pruned = false; }
  };
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
