/*
 * 🆕 新しい宿題のお知らせ (2026-10-15 塾長決定「アプリを開けば分かる」)
 *   宿題・ドリルを配ったときのお知らせは LINE ではなくアプリの中で出す。数え方と「見た」の記録をこの 1 ファイルにまとめ、
 *   塾生アプリ (class.html: 画面上の帯・カードの 🆕 新着) とマイページ (mypage.js: 📌 要対応チップ・カードの 🆕 新着) が同じものを使う。
 *
 * - 未提出のドリル = status !== 'completed' ('open' と、デスクトップの予約タスクが書く 'assigned'。提出 API と同じ)。
 *   クラス宿題 (homework_assignments) の未提出 = status === 'open'。
 * - 「新しい」= 未提出で、生徒が自分で始めたもの (self_issued: 今日の1問・初回診断) ではなく、
 *   この端末で前に宿題を見たとき (markSeen) に無かったもの。記録の無い端末 (初めて・消えた) では届いて 72 時間以内のもの。
 * - 記録は localStorage 'aj_hw_seen_v1:<生徒ID>' に ID だけ (端末ごと。スマホで見ても PC では新着のまま = 塾長了承済みの割り切り)。
 *   読み書きはすべて try/catch。保存できない端末でも、ページ内の記録で「見たら帯が消える」は守る。
 *   取れた一覧だけを記録する (取得に失敗した一覧は前の記録を残す = 失敗で「新しい」を消したり作ったりしない)。
 * - 〆 (2026-10-18 塾長「②の残りも作っておいて」): クラス宿題の期限 (due_date) と、クラス自動宿題のドリルの題名の「〆M/D」
 *   (サーバが grammar-drills の due_date に 'YYYY-MM-DD' で入れる・JS で題名を読まない) を JST の今日と比べる (dueState)。
 *   〆を過ぎた = overdue・〆が今日 = dueToday (どちらも未提出だけ)。塾生アプリの帯 (banner) は新しい宿題があれば新着の帯に 〆 の数を添え、
 *   無ければ 〆を過ぎた / 〆今日 の未提出があるあいだ出し続ける (「見た」の記録に関係なく消えない)。カードのチップは dueChipText。
 *   帯・チップの文言はこのファイルの 1 か所 (scripts/health_check/test_item_open_due.py と test_hw_notice_js.py が動かして確かめる)。
 * - DOM には触らない (scripts/health_check/test_hw_notice_js.py が node / osascript で実際に動かして検査する)。
 * ★ES5 で書く (古い iOS Safari で読み込みに失敗すると帯もバッジも出ない)。
 * ★このファイルを変えたら class.html と mypage.html の hw-notice.js?v= を両方上げる (CI js_cache_bust.py)。
 */
(function (root) {
  'use strict';
  var KEY_PREFIX = 'aj_hw_seen_v1:';
  var FIRST_VISIT_WINDOW_MS = 72 * 3600 * 1000;   // 記録の無い端末では「届いて 72 時間以内」を新しいとみなす
  var MAX_IDS = 500;                              // 1 一覧あたりの記録の上限 (未提出の ID だけなので普通は数件)
  var JST_OFFSET_MS = 9 * 3600 * 1000;
  var mem = {};          // ページ内の記録 (生徒ID → {d, h})。localStorage が使えない端末の代わり
  var testStore;         // テスト用の差し替え (undefined = root.localStorage)
  var hasOwn = Object.prototype.hasOwnProperty;

  function isOpenDrill(d) { return !!d && d.status !== 'completed'; }
  function isOpenHw(h) { return !!h && h.status === 'open'; }

  // サーバの日時: naive UTC 'YYYY-MM-DD HH:MM:SS[.ffffff]' (str(datetime)) か、オフセット付きの ISO。ミリ秒を返す (読めなければ NaN)
  function parseServerTs(s) {
    if (s == null || s === '') return NaN;
    var t = String(s).replace(/^\s+|\s+$/g, '').replace(' ', 'T');
    t = t.replace(/(\.\d{3})\d+/, '$1');   // マイクロ秒は Date が読めない端末があるのでミリ秒に切る
    if (/^\d{4}-\d{2}-\d{2}$/.test(t)) t += 'T00:00:00';
    if (!/[Zz]$|[+-]\d{2}:?\d{2}$/.test(t)) t += 'Z';
    var ms = Date.parse(t);
    return isNaN(ms) ? NaN : ms;
  }
  // JST の今日 'YYYY-MM-DD' (期限切れの判定はサーバと同じ JST の日付で)
  function todayJst(now) {
    var ms = (typeof now === 'number' && !isNaN(now)) ? now : Date.now();
    return new Date(ms + JST_OFFSET_MS).toISOString().slice(0, 10);
  }
  // 〆の日付 'YYYY-MM-DD' (サーバの due_date。'YYYY-MM-DD HH:MM:SS' でも先頭の日付だけ)。形が違えば ''
  var YMD_RE = /^\d{4}-\d{2}-\d{2}$/;
  function dueYmd(v) {
    var s = (v == null) ? '' : String(v).replace(/^\s+/, '').slice(0, 10);
    return YMD_RE.test(s) ? s : '';
  }
  // 〆の状態: 'over' = 〆を過ぎた (〆の日 < JST の今日) / 'today' = 〆今日 / '' = 〆なし・まだ先・読めない。
  //   日付の文字列で比べる (サーバの _today_jst().isoformat() と同じ)。today を省くと JST の今日
  function dueState(due, today) {
    var d = dueYmd(due);
    if (!d) return '';
    var t = (typeof today === 'string' && YMD_RE.test(today)) ? today : todayJst();
    return d < t ? 'over' : (d === t ? 'today' : '');
  }
  // カードのチップの文言 (塾生アプリ・マイページ共通)
  function dueChipText(st) { return st === 'over' ? '〆を過ぎました' : (st === 'today' ? '〆今日' : ''); }

  function storage() {
    if (testStore !== undefined) return testStore;
    try { return root.localStorage || null; } catch (e) { return null; }
  }
  function storageKey(sid) {
    var s = (sid == null) ? '' : String(sid);
    return s ? KEY_PREFIX + s : '';   // 生徒が分からないときは保存しない (ページ内だけ)
  }
  function memKey(sid) { return (sid == null) ? '' : String(sid); }

  function idList(v) {
    if (v === null || v === undefined) return null;
    if (Object.prototype.toString.call(v) !== '[object Array]') return undefined;   // 形が違う = 壊れた記録
    var out = [];
    for (var i = 0; i < v.length && out.length < MAX_IDS; i++) {
      var x = v[i];
      if (typeof x === 'number' || (typeof x === 'string' && x !== '')) out.push(String(x));
    }
    return out;
  }
  function validRecord(o) {
    if (!o || typeof o !== 'object') return null;
    var d = idList(o.d), h = idList(o.h);
    if (d === undefined || h === undefined) return null;
    if (d === null && h === null) return null;
    return { d: d, h: h };
  }
  function union(a, b) {   // どちらかの記録で「見た」なら見た (記録は未提出の ID に絞ってあるので広がりすぎない)
    if (a === null) return b === null ? null : b.slice();
    if (b === null) return a.slice();
    var seen = {}, out = [], i;
    for (i = 0; i < a.length; i++) { if (!hasOwn.call(seen, a[i])) { seen[a[i]] = 1; out.push(a[i]); } }
    for (i = 0; i < b.length; i++) { if (!hasOwn.call(seen, b[i])) { seen[b[i]] = 1; out.push(b[i]); } }
    return out;
  }

  // この端末の記録 {d: [ドリルID] | null, h: [宿題ID] | null}。どちらも無ければ null。決して throw しない
  function loadSeen(sid) {
    var fromStore = null, fromMem = null;
    var key = storageKey(sid);
    if (key) {
      try {
        var st = storage();
        var raw = st ? st.getItem(key) : null;
        if (raw) fromStore = validRecord(JSON.parse(raw));
      } catch (e) { fromStore = null; }
    }
    try { fromMem = validRecord(mem[memKey(sid)]); } catch (e2) { fromMem = null; }
    if (!fromStore && !fromMem) return null;
    if (!fromStore) return { d: fromMem.d === null ? null : fromMem.d.slice(), h: fromMem.h === null ? null : fromMem.h.slice() };
    if (!fromMem) return fromStore;
    return { d: union(fromStore.d, fromMem.d), h: union(fromStore.h, fromMem.h) };
  }

  function openIds(list, isOpen, idOf) {
    var out = [], seen = {};
    for (var i = 0; i < list.length && out.length < MAX_IDS; i++) {
      var it = list[i];
      if (!isOpen(it)) continue;
      var id = idOf(it);
      if (id == null || id === '') continue;
      id = String(id);
      if (hasOwn.call(seen, id)) continue;
      seen[id] = 1; out.push(id);
    }
    return out;
  }
  function drillId(d) { return d.drill_id; }
  function hwId(h) { return h.id; }
  function isArray(v) { return Object.prototype.toString.call(v) === '[object Array]'; }

  // 宿題を見た: 取れた一覧 (配列) の未提出 ID をそのまま記録する。null の一覧 (取得失敗・対象外) は前の記録を残す。決して throw しない
  function markSeen(sid, drills, homework) {
    var prev = null;
    try { prev = loadSeen(sid); } catch (e) { prev = null; }
    var rec = {
      d: isArray(drills) ? openIds(drills, isOpenDrill, drillId) : (prev ? prev.d : null),
      h: isArray(homework) ? openIds(homework, isOpenHw, hwId) : (prev ? prev.h : null)
    };
    if (rec.d === null && rec.h === null) return null;
    try { mem[memKey(sid)] = { d: rec.d, h: rec.h }; } catch (e1) { /* noop */ }
    var key = storageKey(sid);
    if (key) {
      try {
        var st = storage();
        if (st) st.setItem(key, JSON.stringify({ v: 1, d: rec.d, h: rec.h, at: Date.now() }));
      } catch (e2) { /* 保存できない端末 (プライベートブラウズ・容量超過) はページ内の記録だけ */ }
    }
    return rec;
  }

  function toMap(ids) {
    var m = {};
    for (var i = 0; i < ids.length; i++) m[ids[i]] = true;
    return m;
  }
  function inList(list, id) {
    for (var i = 0; i < list.length; i++) if (list[i] === id) return true;
    return false;
  }
  function recentEnough(ts, now) {
    var ms = parseServerTs(ts);
    if (isNaN(ms)) return false;   // 日時が読めないものは「新しい」にしない (毎回出続けるのを防ぐ)
    return (now - ms) <= FIRST_VISIT_WINDOW_MS;
  }

  // opts = {drills: [..] | null, homework: [..] | null, seen: loadSeen() の値 | null, now: ms, today: 'YYYY-MM-DD' (JST)}
  // null の一覧 = 取れなかった (「新しい」にも未提出にも数えない)。DOM には触らない
  function compute(opts) {
    opts = opts || {};
    var drills = isArray(opts.drills) ? opts.drills : null;
    var homework = isArray(opts.homework) ? opts.homework : null;
    var seen = opts.seen || null;
    var now = (typeof opts.now === 'number' && !isNaN(opts.now)) ? opts.now : Date.now();
    var today = (typeof opts.today === 'string' && opts.today) ? opts.today : todayJst(now);
    var seenD = (seen && isArray(seen.d)) ? seen.d : null;
    var seenH = (seen && isArray(seen.h)) ? seen.h : null;
    var openDrills = [], openHw = [], newDrillIds = [], newHwIds = [], overdue = 0, i, id, ds;
    var overdueDrills = 0, overdueHw = 0, dueToday = 0;
    if (drills) {
      for (i = 0; i < drills.length; i++) {
        var d = drills[i];
        if (!isOpenDrill(d)) continue;
        openDrills.push(d);
        // 〆 (クラス自動宿題の題名の 〆M/D = サーバの due_date)。自分で始めたもの (〆なし) も数え方は同じ
        ds = dueState(d.due_date, today);
        if (ds === 'over') { overdue++; overdueDrills++; } else if (ds === 'today') dueToday++;
        if (d.self_issued === true || d.drill_id == null) continue;
        id = String(d.drill_id);
        if (inList(newDrillIds, id)) continue;
        if (seenD ? !inList(seenD, id) : recentEnough(d.assigned_at, now)) newDrillIds.push(id);
      }
    }
    if (homework) {
      for (i = 0; i < homework.length; i++) {
        var h = homework[i];
        if (!isOpenHw(h)) continue;
        openHw.push(h);
        ds = dueState(h.due_date, today);
        if (ds === 'over') { overdue++; overdueHw++; } else if (ds === 'today') dueToday++;
        if (h.id == null) continue;
        id = String(h.id);
        if (inList(newHwIds, id)) continue;
        if (seenH ? !inList(seenH, id) : recentEnough(h.created_at, now)) newHwIds.push(id);
      }
    }
    return {
      openDrills: openDrills,
      openHw: openHw,
      openCount: openDrills.length + openHw.length,
      newDrillIds: newDrillIds,
      newHwIds: newHwIds,
      newDrillMap: toMap(newDrillIds),
      newHwMap: toMap(newHwIds),
      newCount: newDrillIds.length + newHwIds.length,
      overdue: overdue,               // 〆を過ぎた未提出 (クラス宿題 + 〆のあるドリル)
      overdueHw: overdueHw,
      overdueDrills: overdueDrills,
      dueToday: dueToday              // 〆が今日の未提出
    };
  }

  // 表示の文言 (塾生アプリの帯・マイページの 📌 要対応チップ)
  function newLabel(n) { return '🆕 新しい宿題が ' + n + ' 件届いています'; }
  function overdueLabel(n) { return '⚠️ 〆を過ぎた宿題が ' + n + ' 件あります'; }
  function dueParts(overdueCount, dueTodayCount) {
    var p = [];
    if (overdueCount > 0) p.push('〆を過ぎた ' + overdueCount + ' 件');
    if (dueTodayCount > 0) p.push('〆今日 ' + dueTodayCount + ' 件');
    return p;
  }
  // 〆の帯の文言 (新しい宿題が無いとき): 〆を過ぎた (+ 〆今日) / 〆今日だけ
  function dueLabel(overdueCount, dueTodayCount) {
    overdueCount = overdueCount || 0; dueTodayCount = dueTodayCount || 0;
    if (overdueCount > 0) return overdueLabel(overdueCount) + (dueTodayCount > 0 ? '（〆今日 ' + dueTodayCount + ' 件）' : '');
    if (dueTodayCount > 0) return '⏰ 今日が〆の宿題が ' + dueTodayCount + ' 件あります';
    return '';
  }
  // 塾生アプリの帯 (宿題タブ以外の画面の上)。compute() の結果 → {kind, text} か null (帯なし)。
  //   kind 'new' = 新しい宿題 (〆を過ぎた / 〆今日 の数を添える) / 'over' = 〆を過ぎた未提出がある / 'today' = 〆今日の未提出がある。
  //   'over' / 'today' は「見た」の記録に関係なく、未提出が残っているあいだ出し続ける (提出すれば消える)
  function banner(n) {
    if (!n) return null;
    var nn = n.newCount || 0, ov = n.overdue || 0, td = n.dueToday || 0;
    if (nn > 0) {
      var p = dueParts(ov, td);
      return { kind: 'new', text: newLabel(nn) + (p.length ? '（' + p.join('・') + '）' : '') };
    }
    if (ov > 0) return { kind: 'over', text: dueLabel(ov, td) };
    if (td > 0) return { kind: 'today', text: dueLabel(0, td) };
    return null;
  }
  function todoLabel(newCount, openCount, overdueCount, dueTodayCount) {
    newCount = newCount || 0; openCount = openCount || 0; overdueCount = overdueCount || 0; dueTodayCount = dueTodayCount || 0;
    var parts = [];
    if (newCount > 0) {
      if (openCount > newCount) parts.push('未提出 ' + openCount + ' 件');
      if (overdueCount > 0) parts.push('うち〆を過ぎた ' + overdueCount + ' 件');
      if (dueTodayCount > 0) parts.push('〆今日 ' + dueTodayCount + ' 件');
      return '🆕 新しい宿題 ' + newCount + ' 件' + (parts.length ? '（' + parts.join('・') + '）' : '');
    }
    if (overdueCount > 0) parts.push('うち〆を過ぎた ' + overdueCount + ' 件');
    if (dueTodayCount > 0) parts.push('〆今日 ' + dueTodayCount + ' 件');
    return (overdueCount > 0 ? '⚠️ ' : (dueTodayCount > 0 ? '⏰ ' : '📝 ')) + '宿題 ' + openCount + ' 件'
      + (parts.length ? '（' + parts.join('・') + '）' : '');
  }

  root.AJHwNotice = {
    KEY_PREFIX: KEY_PREFIX,
    FIRST_VISIT_WINDOW_MS: FIRST_VISIT_WINDOW_MS,
    isOpenDrill: isOpenDrill,
    isOpenHw: isOpenHw,
    parseServerTs: parseServerTs,
    todayJst: todayJst,
    dueState: dueState,
    dueChipText: dueChipText,
    loadSeen: loadSeen,
    markSeen: markSeen,
    compute: compute,
    newLabel: newLabel,
    overdueLabel: overdueLabel,
    dueLabel: dueLabel,
    banner: banner,
    todoLabel: todoLabel,
    // テスト用 (scripts/health_check/test_hw_notice_js.py)。画面からは呼ばない
    _useStorage: function (s) { testStore = s; },
    _clearMemory: function () { mem = {}; }
  };
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
