/*
 * 📝 記号の解答用紙 (マーク) — 生徒の画面 (2026-10-18 塾長「◎のとおりでお願いします。ただし、記述式は採点が難しいので
 *   しばらくは記号問題がいい」の第1段)。塾生アプリ (class.html) とマイページ (mypage.js) が同じものを使う。
 *
 * - 塾長が CEO の「📚 宿題」/ 📤 一括割当で「記号の解答用紙」付きの宿題を出すと、宿題一覧の item に answer_sheet が付く
 *   (問題数・択数・記号の種類・提出済みか・点数・問ごとの ○×・reveal_on・correct)。一覧の answer_sheet_ready が true のときだけ使う。
 * - 生徒は問ごとに記号のボタン (大きいタップ領域) を押してマークし、1 回だけ提出する
 *   (POST /api/student/homework/{id}/sheet {answers:[番号 (1 始まり) | null]})。採点はサーバだけ (画面は点数を送らない)。
 * - 提出したらすぐ点数と問ごとの ○×。正解の記号はサーバが見せてよいと言ったとき (reveal: 期限の翌日 (JST) から・期限なしは提出直後) だけ。
 * - 答えの下書きは localStorage 'aj_hw_sheet_v1:<生徒ID>:<宿題ID>' (端末ごと・読み書きは全部 try/catch。使えない端末はページ内だけ)。
 *   提出できたら消す。問題数・択数・やり直しの回数が変わった下書きは使わない。
 * - 二度目の提出は 409 → 一覧を読み直して提出済みの結果を出す。読み直せない・まだ未提出に見えるときもボタンを「⏳ 採点中…」のまま
 *   残さない (提出済みなら「✅ 提出済み」と一覧で開き直す案内・それ以外はサーバの理由を出してボタンを戻す)。
 *   422 は理由・503 / 未デプロイの 404 は「準備中」・通信失敗は下書きを残す。
 * - 返事を待つ間も「← 宿題一覧に戻る」で戻れる (通信が止まった端末で閉じ込めない)。返事は裏で受け取り、トーストと
 *   opts.onSubmitted(res, {left: true}) で知らせる (一覧の読み直しは画面の側)。離れた後は画面を描き替えない。
 * - マイページの重ね (openOverlay) は 1 枚だけ。開いている間にもう一度呼ばれたら (二度押し) 今の重ねを返す。
 * - 解答用紙の宿題に「✓完了」は出さない (完了 = 提出。サーバも /complete を 400 で止める)。
 * - 値は全部 escape して描く。AI は呼ばない。
 * ★ES5 で書く (古い iOS Safari で読み込みに失敗すると解答用紙が出ない)。
 * ★このファイルを変えたら class.html と mypage.html の hw-sheet.js?v= を両方上げる (CI js_cache_bust.py)。
 * 回帰テスト: scripts/health_check/test_homework_sheet_front.py (node / osascript / jsc で実際に動かす)。
 */
(function (root) {
  'use strict';
  var DRAFT_PREFIX = 'aj_hw_sheet_v1:';
  var STYLE_LABELS = { circled: '①②③④⑤⑥⑦⑧', katakana: 'アイウエオカキク', upper: 'ABCDEFGH', lower: 'abcdefgh', seigo: '正誤' };
  var CIRCLED_ALL = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳';
  var NET_MSG = '通信できませんでした。電波のよいところでもう一度押してね（答えはこの端末に残っています）';
  var mem = {};          // ページ内の下書き (localStorage が使えない端末の代わり)
  var testStore;         // テスト用の差し替え (undefined = root.localStorage)
  var hasOwn = Object.prototype.hasOwnProperty;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }
  function isArray(v) { return Object.prototype.toString.call(v) === '[object Array]'; }
  function toInt(v) {
    if (typeof v === 'number') return (isFinite(v) && Math.floor(v) === v) ? v : NaN;
    if (typeof v === 'string' && /^\s*\d+\s*$/.test(v)) return parseInt(v, 10);
    return NaN;
  }
  function chars(s) {   // 記号の文字 (丸数字・カナ・英字はどれも 1 文字 = BMP)
    var out = [];
    for (var i = 0; i < s.length; i++) out.push(s.charAt(i));
    return out;
  }

  // ---------------------------------------------------------------- 表示の部品 (DOM に触らない)
  function numQuestions(sheet) { var n = toInt(sheet && sheet.num_questions); return (n >= 1 && n <= 100) ? n : 0; }
  function numChoices(sheet) { var n = toInt(sheet && sheet.num_choices); return (n >= 2 && n <= 8) ? n : 0; }
  // 紙の記号の並び (サーバの labels を優先・無ければ記号の種類と択数から)
  function labels(sheet) {
    var nc = numChoices(sheet), out = [], i;
    if (sheet && isArray(sheet.labels) && sheet.labels.length >= 2) {
      for (i = 0; i < sheet.labels.length && i < 8; i++) out.push(String(sheet.labels[i]));
      return out;
    }
    var s = STYLE_LABELS[(sheet && sheet.label_style) || 'circled'] || STYLE_LABELS.circled;
    return chars(s).slice(0, nc || 4);
  }
  // 1 始まりの番号 → 記号 (配列 = どれでも正解・0 = 全員正解)
  function labelOf(v, sheet) {
    if (isArray(v)) {
      var parts = [];
      for (var i = 0; i < v.length; i++) parts.push(labelOf(v[i], sheet));
      return parts.join('/');
    }
    var n = toInt(v);
    if (n === 0) return '全員正解';
    if (!(n >= 1)) return '—';
    var L = labels(sheet);
    if (n <= L.length) return L[n - 1];
    if ((sheet && sheet.label_style) === 'circled' && n <= CIRCLED_ALL.length) return CIRCLED_ALL.charAt(n - 1);
    return String(n);
  }
  // 'none' = 解答用紙なし (今までどおり) / 'open' = これから答える / 'submitted' = 提出済み /
  // 'unavailable' = 正解表が無い (塾長に知らせる) / 'unsupported' = この画面では答えられない答え方
  function state(it, ready) {
    if (!it || !it.answer_sheet || typeof it.answer_sheet !== 'object' || ready !== true) return 'none';
    var sh = it.answer_sheet;
    if (sh.mode !== 'choice') return 'unsupported';
    if (sh.submitted === true) return 'submitted';
    if (sh.available !== true || !numQuestions(sh) || !numChoices(sh)) return 'unavailable';
    return 'open';
  }
  function answerButtonLabel(sheet) { return '✏️ 解答用紙に答える（全' + numQuestions(sheet) + '問）'; }
  function scoreText(sheet) {
    if (!sheet || sheet.score_correct == null || sheet.score_total == null) return '';
    return '📝 ' + sheet.score_correct + '/' + sheet.score_total;
  }
  function styleRangeText(sheet) {
    var L = labels(sheet);
    if (!L.length) return '';
    return (sheet && sheet.label_style === 'seigo') ? '正・誤' : (L[0] + '〜' + L[L.length - 1]);
  }
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  // サーバの日時 (naive UTC 'YYYY-MM-DD HH:MM:SS[.ffffff]' / オフセット付き ISO) → JST 'YYYY-MM-DD HH:MM'。端末のタイムゾーンに依らない
  function fmtJst(s) {
    if (s == null || s === '') return '';
    var t = String(s).replace(/^\s+|\s+$/g, '').replace(' ', 'T').replace(/(\.\d{3})\d+/, '$1');
    if (/^\d{4}-\d{2}-\d{2}$/.test(t)) t += 'T00:00:00';
    if (!/[Zz]$|[+-]\d{2}:?\d{2}$/.test(t)) t += 'Z';
    var ms = Date.parse(t);
    if (isNaN(ms)) return String(s).slice(0, 16);
    var j = new Date(ms + 9 * 3600 * 1000);
    return j.getUTCFullYear() + '-' + pad2(j.getUTCMonth() + 1) + '-' + pad2(j.getUTCDate()) + ' ' + pad2(j.getUTCHours()) + ':' + pad2(j.getUTCMinutes());
  }
  function md(dateStr) {   // 'YYYY-MM-DD' (JST の日付) → 'M/D'
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(dateStr == null ? '' : dateStr));
    return m ? (Number(m[2]) + '/' + Number(m[3])) : '';
  }
  function revealNote(sheet) {
    if (!sheet || sheet.reveal === true) return '';
    var d = md(sheet.reveal_on);
    return d ? ('正解の記号は ' + d + '（期限の翌日）から見られます') : '正解の記号は、あとで見られるようになります';
  }

  // ---------------------------------------------------------------- 下書き (端末ごと・全部 try/catch)
  function storage() {
    if (testStore !== undefined) return testStore;
    try { return root.localStorage || null; } catch (e) { return null; }
  }
  function draftKey(sid, hwId) {
    var s = (sid == null) ? '' : String(sid), h = (hwId == null) ? '' : String(hwId);
    return (s && h) ? DRAFT_PREFIX + s + ':' + h : '';
  }
  function memKey(sid, hwId) { return String(sid == null ? '' : sid) + ':' + String(hwId == null ? '' : hwId); }
  function cleanAnswers(arr, n, nc) {
    var out = [];
    for (var i = 0; i < n; i++) {
      var v = (arr && i < arr.length) ? toInt(arr[i]) : NaN;
      out.push((v >= 1 && v <= nc) ? v : null);
    }
    return out;
  }
  function emptyAnswers(n) { var out = []; for (var i = 0; i < n; i++) out.push(null); return out; }
  function validDraft(o, sheet) {
    var n = numQuestions(sheet), nc = numChoices(sheet);
    if (!o || typeof o !== 'object' || !isArray(o.a) || o.n !== n || o.c !== nc) return null;
    if ((o.r || 0) !== (toInt(sheet.reset_count) || 0)) return null;   // 塾長の「やり直し」より前の下書きは使わない
    return cleanAnswers(o.a, n, nc);
  }
  // この端末の下書き (問題数ぶんの配列) か null。決して throw しない
  function loadDraft(sid, hwId, sheet) {
    var key = draftKey(sid, hwId), got = null;
    if (key) {
      try {
        var st = storage();
        var raw = st ? st.getItem(key) : null;
        if (raw) got = validDraft(JSON.parse(raw), sheet);
      } catch (e) { got = null; }
    }
    if (!got) {
      try { got = validDraft(mem[memKey(sid, hwId)], sheet); } catch (e2) { got = null; }
    }
    return got;
  }
  function saveDraft(sid, hwId, sheet, answers) {
    var rec = { v: 1, n: numQuestions(sheet), c: numChoices(sheet), r: toInt(sheet && sheet.reset_count) || 0, a: answers, at: Date.now() };
    try { mem[memKey(sid, hwId)] = rec; } catch (e0) { /* noop */ }
    var key = draftKey(sid, hwId);
    if (!key) return;
    try { var st = storage(); if (st) st.setItem(key, JSON.stringify(rec)); } catch (e) { /* 保存できない端末はページ内だけ */ }
  }
  function clearDraft(sid, hwId) {
    try { delete mem[memKey(sid, hwId)]; } catch (e0) { /* noop */ }
    var key = draftKey(sid, hwId);
    if (!key) return;
    try { var st = storage(); if (st) st.removeItem(key); } catch (e) { /* noop */ }
  }

  // ---------------------------------------------------------------- 提出まわり
  function blanks(answers) {
    var out = [];
    for (var i = 0; i < answers.length; i++) if (answers[i] == null) out.push(i);
    return out;
  }
  function blankNos(bl, max) {
    var parts = [];
    for (var i = 0; i < bl.length && i < (max || 3); i++) parts.push('問' + (bl[i] + 1));
    return parts.join('・') + (bl.length > (max || 3) ? ' ほか' : '');
  }
  function confirmText(answers) {
    var bl = blanks(answers);
    if (bl.length) {
      return blankNos(bl, 3) + ' がまだです（空欄 ' + bl.length + ' 問）。\n空欄のまま提出しますか？\n空欄は × になります。提出は 1 回だけです。';
    }
    return 'この答えで提出しますか？\n提出は 1 回だけです（出し直しは塾長に頼みます）。';
  }
  function errText(e) {
    var st = e && e.status, m = (e && e.message) || '';
    if (st === 404 && (m === 'Not Found' || !m)) return '準備中です。少し待ってからもう一度押してね';   // 新しいサーバがまだ出ていない
    if (st === 503) return '準備中です。少し待ってからもう一度押してね';
    if (st === 401) return 'ログインし直してからもう一度押してね（答えはこの端末に残っています）';
    if (st === 403) return 'いまは提出できませんでした。少し待ってから、もう一度おためしください';
    if (st === 429) return '少し時間をおいてから、もう一度押してね';
    if (!st || st >= 500 || /failed to fetch|networkerror|load failed/i.test(m)) return NET_MSG;
    return m || '提出できませんでした';
  }

  // ---------------------------------------------------------------- HTML
  function btn(cls, attrs, text) { return '<button type="button" class="hs-btn ' + cls + '"' + attrs + '>' + text + '</button>'; }
  function backHtml(label) { return '<div class="hs-back-row">' + btn('hs-btn-ghost', ' data-hs-act="back"', esc(label || '← 宿題一覧に戻る')) + '</div>'; }
  function printBtnHtml(hw, canPrint) {
    if (!canPrint || !hw || !hw.attachment_print || hw.attachment_print.id == null) return '';
    return '<div class="hs-print-row">' + btn('hs-btn-ghost', ' data-hs-act="print" data-id="' + esc(String(hw.id)) + '" data-print-id="'
      + esc(String(hw.attachment_print.id)) + '"', '📄 プリントを開く') + '</div>';
  }
  function rowInnerHtml(i, sheet, answers) {
    var L = labels(sheet), out = '<span class="hs-no">問' + (i + 1) + '</span><span class="hs-cs">';
    for (var v = 1; v <= L.length; v++) {
      var on = answers[i] === v;
      out += '<button type="button" class="hs-c' + (on ? ' hs-sel' : '') + '" data-hs-q="' + i + '" data-hs-v="' + v + '" aria-pressed="'
        + (on ? 'true' : 'false') + '" aria-label="問' + (i + 1) + ' ' + esc(L[v - 1]) + '">' + esc(L[v - 1]) + '</button>';
    }
    return out + '</span>';
  }
  function progressText(answers) {
    var left = blanks(answers).length;
    return left > 0 ? ('あと ' + left + ' 問（全 ' + answers.length + ' 問）') : ('全 ' + answers.length + ' 問 答えました');
  }
  function formHtml(hw, sheet, answers, o) {
    o = o || {};
    var title = String((hw && hw.title) || '宿題');
    var rows = '';
    for (var i = 0; i < answers.length; i++) rows += '<div class="hs-q" data-hs-row="' + i + '">' + rowInnerHtml(i, sheet, answers) + '</div>';
    var due = hw && hw.due_date ? ('📅 期限: ' + esc(hw.due_date) + ' ・ ') : '';
    return '<div class="hs-wrap" data-hs-view="form">' + backHtml(o.backLabel)
      + '<div class="hs-title">✏️ ' + esc(title) + '</div>'
      + '<div class="hs-meta">' + due + '全 ' + answers.length + ' 問 ・ 記号 ' + esc(styleRangeText(sheet)) + ' ・ 提出は 1 回だけ</div>'
      + printBtnHtml(hw, o.canPrint)
      + '<div class="hs-meta hs-howto">紙のプリントを解いたら、問題ごとに答えの記号を押してね。もう一度押すと消せます。'
      + '答えはこの端末に自動で保存されます。</div>'
      + rows
      + '<div class="hs-progress" data-hs-progress>' + esc(progressText(answers)) + '</div>'
      + '<div class="hs-msg" data-hs-msg></div>'
      + btn('hs-btn-primary hs-submit', ' data-hs-act="submit"', '📤 提出する（1 回だけ）')
      + '</div>';
  }
  function resultHtml(hw, sheet, o) {
    o = o || {};
    var title = String((hw && hw.title) || '宿題');
    var n = numQuestions(sheet) || (isArray(sheet && sheet.answers) ? sheet.answers.length : 0);
    var answers = isArray(sheet && sheet.answers) ? sheet.answers : [];
    var results = isArray(sheet && sheet.results) ? sheet.results : null;
    var reveal = sheet && sheet.reveal === true && isArray(sheet.correct);
    var scored = sheet && sheet.score_correct != null && sheet.score_total != null;
    var head = '<div class="hs-score">' + (o.justSubmitted ? '提出しました' : '採点結果')
      + (scored ? ('<span class="hs-n">' + esc(String(sheet.score_correct)) + ' / ' + esc(String(sheet.score_total)) + '</span>')
        : '<span class="hs-n hs-n-small">採点を準備中です</span>')
      + '<div class="hs-meta">' + (sheet && sheet.submitted_at ? ('提出: ' + esc(fmtJst(sheet.submitted_at))) : '')
      + (sheet && sheet.late ? ' <span class="hs-chip hs-chip-late">期限後</span>' : '') + '</div></div>';
    var note = reveal ? '○ は正解・× はまちがい。正解の記号も出しています。' : ('○ は正解・× はまちがいです。' + revealNote(sheet));
    var rows = '';
    for (var i = 0; i < n; i++) {
      var ok = results ? results[i] === true : null;
      var mine = (i < answers.length && answers[i] != null) ? labelOf(answers[i], sheet) : '（空欄）';
      rows += '<div class="hs-r' + (ok === true ? ' hs-ok' : (ok === false ? ' hs-ng' : '')) + '">'
        + '<span class="hs-no">問' + (i + 1) + '</span>'
        + '<span class="hs-mk">' + (ok === true ? '○' : (ok === false ? '×' : '—')) + '</span>'
        + '<span class="hs-mine">あなた: ' + esc(mine) + '</span>'
        + (reveal && i < sheet.correct.length ? ('<span class="hs-ans">正解: ' + esc(labelOf(sheet.correct[i], sheet)) + '</span>') : '')
        + '</div>';
    }
    var cheer = '';
    if (scored && sheet.score_total > 0) {
      cheer = sheet.score_correct === sheet.score_total ? '🎉 全問正解！'
        : (sheet.score_correct * 100 >= sheet.score_total * 80 ? '👍 よくできました！ × の問題を見直そう' : '📖 × の問題をプリントで解き直してみよう');
    }
    return '<div class="hs-wrap" data-hs-view="result">' + backHtml(o.backLabel)
      + '<div class="hs-title">📝 ' + esc(title) + '</div>' + head
      + (cheer ? '<div class="hs-meta hs-cheer">' + esc(cheer) + '</div>' : '')
      + '<div class="hs-meta">' + esc(note) + '</div>'
      + printBtnHtml(hw, o.canPrint)
      + rows
      + '<div class="hs-meta" style="margin-top:0.6rem;">提出は 1 回だけです。出し直したいときは塾長に「やり直し」を頼んでね。</div>'
      + backHtml(o.backLabel) + '</div>';
  }

  // ---------------------------------------------------------------- 見た目 (1 回だけ <style> を入れる)
  var CSS = ''
    + '.hs-wrap{color:#e4e4e7;}'
    + '.hs-back-row{margin:0 0 0.8rem;}'
    + '.hs-title{font-size:1.08rem;font-weight:800;margin:0.2rem 0 0.35rem;line-height:1.5;word-break:break-word;}'
    + '.hs-meta{color:#a1a1aa;font-size:0.82rem;line-height:1.6;margin:0.15rem 0 0.45rem;word-break:break-word;}'
    + '.hs-howto{color:#cbd5e1;}'
    + '.hs-print-row{margin:0.3rem 0 0.6rem;}'
    + '.hs-btn{display:inline-block;min-height:44px;padding:0.55rem 1rem;border-radius:10px;font-weight:800;font-size:0.9rem;cursor:pointer;font-family:inherit;touch-action:manipulation;}'
    + '.hs-btn-ghost{background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.2);color:#e4e4e7;}'
    + '.hs-btn-primary{background:linear-gradient(135deg,#10b981,#059669);border:0;color:#fff;}'
    + '.hs-btn:disabled{opacity:0.55;cursor:default;}'
    + '.hs-q{display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.6rem;margin:0.4rem 0;background:rgba(255,255,255,0.035);border:1px solid rgba(255,255,255,0.12);border-radius:12px;}'
    + '.hs-q.hs-blank{border-color:rgba(251,191,36,0.7);box-shadow:0 0 0 1px rgba(251,191,36,0.35);}'
    + '.hs-no{flex:0 0 3.1em;font-weight:800;color:#a5b4fc;font-size:0.88rem;}'
    + '.hs-cs{display:flex;flex-wrap:wrap;gap:0.45rem;flex:1 1 auto;min-width:0;}'
    + '.hs-c{min-width:50px;min-height:50px;padding:0 0.55rem;border-radius:12px;border:1.5px solid rgba(255,255,255,0.25);background:rgba(0,0,0,0.28);color:#e4e4e7;font-size:1.2rem;font-weight:800;font-family:inherit;cursor:pointer;touch-action:manipulation;-webkit-tap-highlight-color:transparent;}'
    + '.hs-c.hs-sel{background:#6366f1;border-color:#c7d2fe;color:#fff;box-shadow:0 0 0 2px rgba(129,140,248,0.45);}'
    + '.hs-progress{text-align:center;color:#c7d2fe;font-weight:800;font-size:0.9rem;margin:0.8rem 0 0.3rem;}'
    + '.hs-msg{text-align:center;color:#fca5a5;font-size:0.86rem;font-weight:700;min-height:1.2em;margin:0.3rem 0 0.6rem;white-space:pre-wrap;}'
    + '.hs-submit{display:block;width:100%;min-height:52px;font-size:1rem;}'
    + '.hs-score{text-align:center;padding:0.9rem;margin:0.5rem 0 0.7rem;background:linear-gradient(135deg,rgba(129,140,248,0.18),rgba(167,139,250,0.10));border:1px solid rgba(129,140,248,0.42);border-radius:14px;font-weight:700;}'
    + '.hs-n{display:block;font-size:2rem;font-weight:800;color:#c7d2fe;line-height:1.25;}'
    + '.hs-n-small{font-size:1rem;}'
    + '.hs-chip{display:inline-block;padding:0.1rem 0.5rem;border-radius:999px;font-size:0.74rem;font-weight:800;}'
    + '.hs-chip-late{background:rgba(251,191,36,0.18);border:1px solid rgba(251,191,36,0.45);color:#fde68a;}'
    + '.hs-r{display:flex;flex-wrap:wrap;align-items:center;gap:0.3rem 0.7rem;padding:0.5rem 0.7rem;margin:0.3rem 0;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);font-size:0.92rem;}'
    + '.hs-r.hs-ok{background:rgba(16,185,129,0.12);border-color:rgba(16,185,129,0.45);}'
    + '.hs-r.hs-ng{background:rgba(239,68,68,0.10);border-color:rgba(239,68,68,0.45);}'
    + '.hs-mk{font-weight:800;font-size:1.15rem;min-width:1.2em;text-align:center;}'
    + '.hs-r.hs-ok .hs-mk{color:#6ee7b7;}.hs-r.hs-ng .hs-mk{color:#fca5a5;}'
    + '.hs-ans{color:#6ee7b7;font-weight:800;}'
    + '.hs-overlay{position:fixed;left:0;top:0;right:0;bottom:0;z-index:9000;background:rgba(12,12,26,0.98);overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;}'
    + '.hs-overlay-inner{max-width:760px;margin:0 auto;padding:1rem 1rem 5rem;box-sizing:border-box;}'
    + '.hs-toast{position:fixed;left:50%;bottom:90px;transform:translateX(-50%);z-index:9100;max-width:90%;padding:0.7rem 1.1rem;border-radius:10px;background:rgba(20,20,40,0.97);border:1px solid rgba(129,140,248,0.5);color:#e4e4e7;font-size:0.9rem;font-weight:700;box-shadow:0 6px 24px rgba(0,0,0,0.5);}'
    + '.hs-toast.hs-err{border-color:rgba(239,68,68,0.6);color:#fca5a5;}';
  function injectCss(doc) {
    try {
      doc = doc || root.document;
      if (!doc || !doc.createElement || !doc.head) return;
      if (doc.getElementById && doc.getElementById('aj-hw-sheet-css')) return;
      var st = doc.createElement('style');
      st.id = 'aj-hw-sheet-css';
      st.textContent = CSS;
      doc.head.appendChild(st);
    } catch (e) { /* 見た目が付かなくても答えられる */ }
  }
  var _toastTimer = null;
  function defaultToast(msg, isErr) {
    try {
      var doc = root.document;
      if (!doc || !doc.body) return;
      var t = doc.getElementById ? doc.getElementById('aj-hw-sheet-toast') : null;
      if (!t) { t = doc.createElement('div'); t.id = 'aj-hw-sheet-toast'; doc.body.appendChild(t); }
      t.className = 'hs-toast' + (isErr ? ' hs-err' : '');
      t.textContent = String(msg);
      t.style.display = 'block';
      if (_toastTimer) clearTimeout(_toastTimer);
      _toastTimer = setTimeout(function () { t.style.display = 'none'; }, 2800);
    } catch (e) { /* noop */ }
  }

  // ---------------------------------------------------------------- 画面 (el の中に解答用紙 / 結果を描く)
  // opts = { hw: 宿題一覧の item (answer_sheet 付き), sid: 生徒ID, api: function (path, {method, body}) → Promise<JSON>
  //          (失敗は Error に status と message), toast(msg, isErr), confirm(msg) → bool, onBack(changed), onSubmitted(res),
  //          onOpenPrint(buttonEl) (無ければプリントのボタンは出さない), backLabel, scrollTop() }
  function mount(el, opts) {
    opts = opts || {};
    var hw = opts.hw || {};
    var sheet = hw.answer_sheet || {};
    var hwId = hw.id;
    var sid = opts.sid;
    var n = numQuestions(sheet), nc = numChoices(sheet);
    var answers = loadDraft(sid, hwId, sheet) || emptyAnswers(n);
    var busy = false, changed = false, view = '';
    var left = false;   // 提出の返事を待つ間に「← 宿題一覧に戻る」で離れた (返事は裏で受け取る)
    var toast = typeof opts.toast === 'function' ? opts.toast : defaultToast;
    var ask = typeof opts.confirm === 'function' ? opts.confirm : function (m) { try { return root.confirm(m); } catch (e) { return true; } };
    var o = { backLabel: opts.backLabel, canPrint: typeof opts.onOpenPrint === 'function' };
    var backText = opts.backLabel || '← 宿題一覧に戻る';
    var SUBMIT_TEXT = '📤 提出する（1 回だけ）';
    injectCss();
    // この画面がもう出ていない (戻った・同じ el に一覧や別の画面が描かれた) = 返事が来ても描き替えない
    function gone() { return left || el.__hsCtl !== ctl; }
    function setSubmitBtn(b, text, disabled) {
      if (!b) return;
      b.disabled = !!disabled;
      b.textContent = text || SUBMIT_TEXT;
    }

    function scrollTop() {
      try { if (typeof opts.scrollTop === 'function') { opts.scrollTop(); return; } } catch (e0) { /* noop */ }
      try { root.scrollTo(0, 0); } catch (e) { /* noop */ }
    }
    function q(sel) { try { return el.querySelector(sel); } catch (e) { return null; } }
    function renderForm() {
      view = 'form';
      el.innerHTML = formHtml(hw, sheet, answers, o);
    }
    function renderResult(justSubmitted) {
      view = 'result';
      el.innerHTML = resultHtml(hw, sheet, { backLabel: o.backLabel, canPrint: o.canPrint, justSubmitted: !!justSubmitted });
      scrollTop();
    }
    function setMsg(t) { var m = q('[data-hs-msg]'); if (m) m.textContent = t || ''; }
    function updateRow(i) {
      var row = q('[data-hs-row="' + i + '"]');
      if (row) {
        row.innerHTML = rowInnerHtml(i, sheet, answers);
        try { row.classList.remove('hs-blank'); } catch (e) { /* noop */ }
      }
      var p = q('[data-hs-progress]');
      if (p) p.textContent = progressText(answers);
    }
    function choose(i, v) {
      if (view !== 'form' || busy) return;
      if (!(i >= 0 && i < n) || !(v >= 1 && v <= nc)) return;
      answers[i] = (answers[i] === v) ? null : v;   // もう一度押すと消せる
      saveDraft(sid, hwId, sheet, answers);
      updateRow(i);
      var m = q('[data-hs-msg]');
      if (m && m.textContent) {
        var bl = blanks(answers);
        m.textContent = bl.length ? ('⚠ ' + blankNos(bl, 3) + ' がまだです（あと ' + bl.length + ' 問）') : '';
      }
    }
    function markBlanks() {
      var bl = blanks(answers), first = null;
      for (var k = 0; k < bl.length; k++) {
        var row = q('[data-hs-row="' + bl[k] + '"]');
        if (row) { try { row.classList.add('hs-blank'); } catch (e) { /* noop */ } if (!first) first = row; }
      }
      return first;
    }
    function showSubmitted(res, just) {
      hw.status = 'completed';
      if (res && res.answer_sheet && typeof res.answer_sheet === 'object') sheet = res.answer_sheet;
      else { sheet.submitted = true; sheet.answers = cleanAnswers(answers, n, nc); sheet.results = null; sheet.score_correct = null; }
      hw.answer_sheet = sheet;
      changed = true;
      clearDraft(sid, hwId);
      renderResult(just);
    }
    // 409 = 二度目の提出 (別の端末で先に出した・二度押し) は失敗ではない。一覧を読み直して提出済みの結果を出す。
    //   ★サーバの 409 は「もう提出済み」と「正解表が見つかりません」の 2 つ。どちらでもボタンを「⏳ 採点中…」のまま残さない:
    //   - 一覧で提出済み → 結果の画面
    //   - 一覧ではまだ未提出 (正解表が無い・その間に塾長がやり直しにした) → サーバの理由を出してボタンを戻す
    //   - 一覧を読めない / 一覧に無い → 「もう提出済み」なら ✅ 提出済み (押せない) と一覧で開き直す案内、それ以外は理由とボタンを戻す
    function after409(b, e) {
      changed = true;
      var srv = (e && e.message) || '';
      var dup = !srv || srv.indexOf('提出済み') >= 0;
      if (dup) toast('この解答用紙はもう提出済みです');
      else toast('❌ ' + srv, true);
      function stillOpen() {
        setMsg('❌ 提出できませんでした。' + (srv || errText(e)));
        setSubmitBtn(b);
      }
      function unknown() {
        if (gone()) return;
        if (dup) {
          setMsg('この解答用紙はもう提出済みです。「' + backText + '」で一覧に戻って開き直すと、結果が見られます');
          setSubmitBtn(b, '✅ 提出済み', true);
        } else {
          stillOpen();
        }
      }
      return opts.api('/api/student/homework').then(function (d) {
        var items = (d && d.items) || [], it = null;
        for (var k = 0; k < items.length; k++) if (items[k] && String(items[k].id) === String(hwId)) it = items[k];
        if (it && it.answer_sheet && it.answer_sheet.submitted === true) {
          clearDraft(sid, hwId);
          if (gone()) return;
          hw = it;
          showSubmitted({ answer_sheet: it.answer_sheet }, false);
          return;
        }
        if (it && it.answer_sheet && typeof it.answer_sheet === 'object') {
          if (!gone()) stillOpen();
          return;
        }
        unknown();
      }, unknown);
    }
    function submit(b) {
      if (view !== 'form' || busy) return;
      var bl = blanks(answers);
      var first = bl.length ? markBlanks() : null;
      if (bl.length) setMsg('⚠ ' + blankNos(bl, 3) + ' がまだです（あと ' + bl.length + ' 問）');
      if (!ask(confirmText(answers))) {
        if (first) { try { first.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (e) { try { first.scrollIntoView(); } catch (e2) { /* noop */ } } }
        return;
      }
      busy = true;
      setSubmitBtn(b, '⏳ 採点中…', true);
      setMsg('');
      var payload = cleanAnswers(answers, n, nc);
      return opts.api('/api/student/homework/' + encodeURIComponent(String(hwId)) + '/sheet',
        { method: 'POST', body: JSON.stringify({ answers: payload }) }).then(function (res) {
        busy = false;
        var wasGone = gone();
        if (wasGone) {
          // 返事を待つ間に一覧へ戻った: 画面は描き替えず、下書きを消して結果をトーストで知らせる (一覧の読み直しは onSubmitted で画面の側)
          hw.status = 'completed';
          if (res && res.answer_sheet && typeof res.answer_sheet === 'object') { sheet = res.answer_sheet; hw.answer_sheet = sheet; }
          changed = true;
          clearDraft(sid, hwId);
        } else {
          showSubmitted(res, true);
        }
        var s = (res && res.answer_sheet && typeof res.answer_sheet === 'object') ? res.answer_sheet : sheet;
        toast((s.score_correct != null && s.score_total != null) ? ('提出しました！ ' + s.score_correct + ' / ' + s.score_total + ' 正解') : '提出しました！');
        if (typeof opts.onSubmitted === 'function') { try { opts.onSubmitted(res, { left: wasGone }); } catch (e3) { /* noop */ } }
      }, function (e) {
        busy = false;
        if (e && e.status === 409) return after409(b, e);
        if (gone()) { toast('❌ 提出できませんでした。' + errText(e), true); return; }   // 下書きは残っている
        setMsg('❌ 提出できませんでした。' + errText(e));
        setSubmitBtn(b);
      });
    }
    function back() {
      if (busy && !left) {
        // 返事を待つ間も戻れる (通信が止まった端末で閉じ込めない)。返事は裏で受け取ってトーストで知らせる
        left = true;
        toast('⏳ 提出を送っています。結果は宿題一覧に出ます');
      }
      if (typeof opts.onBack === 'function') opts.onBack(changed);
    }
    function onClick(ev) {
      if (el.__hsCtl !== ctl) return;   // この el に新しい画面 (一覧など) が描かれた後は何もしない
      var t = ev && ev.target;
      if (!t || typeof t.closest !== 'function') return;
      var c = t.closest('[data-hs-v]');
      if (c) {
        if (ev.preventDefault) ev.preventDefault();
        choose(toInt(c.getAttribute('data-hs-q')), toInt(c.getAttribute('data-hs-v')));
        return;
      }
      var a = t.closest('[data-hs-act]');
      if (!a) return;
      var act = a.getAttribute('data-hs-act');
      if (ev.preventDefault) ev.preventDefault();
      if (act === 'back') back();
      else if (act === 'submit') submit(a);
      else if (act === 'print' && typeof opts.onOpenPrint === 'function') opts.onOpenPrint(a);
    }
    var ctl = {
      choose: choose,
      submit: function () { return submit(q('[data-hs-act="submit"]')); },
      back: back,
      answers: function () { return answers.slice(); },
      view: function () { return view; },
      sheet: function () { return sheet; },
      changed: function () { return changed; },
      detach: function () { if (el.__hsCtl === ctl) el.__hsCtl = null; }
    };
    el.__hsCtl = ctl;
    if (!el.__hsBound) {
      el.__hsBound = true;
      el.addEventListener('click', function (ev) { var c = el.__hsCtl; if (c && c._onClick) c._onClick(ev); });
    }
    ctl._onClick = onClick;
    if (sheet.submitted === true) { clearDraft(sid, hwId); renderResult(false); }
    else { renderForm(); scrollTop(); }
    return ctl;
  }

  // マイページ用: 画面いっぱいの重ね (閉じたら opts.onClose(changed))。塾生アプリは宿題タブの中に mount する
  // ★重ねは 1 枚だけ: 開いている間にもう一度呼ばれたら (「✏️ 解答用紙に答える」の二度押し) 新しい重ねを作らずに今のを返す
  var activeOverlay = null;
  function openOverlay(opts) {
    opts = opts || {};
    var doc = root.document;
    if (activeOverlay && activeOverlay.overlay && activeOverlay.overlay.parentNode) return activeOverlay;
    activeOverlay = null;
    injectCss(doc);
    var ov = doc.createElement('div');
    ov.className = 'hs-overlay';
    ov.setAttribute('role', 'dialog');
    ov.setAttribute('aria-modal', 'true');
    var inner = doc.createElement('div');
    inner.className = 'hs-overlay-inner';
    ov.appendChild(inner);
    doc.body.appendChild(ov);
    var prev = '';
    try { prev = doc.body.style.overflow || ''; doc.body.style.overflow = 'hidden'; } catch (e) { /* noop */ }
    var o = {}, k;
    for (k in opts) if (hasOwn.call(opts, k)) o[k] = opts[k];
    o.backLabel = opts.backLabel || '× 閉じる';
    o.scrollTop = function () { try { ov.scrollTop = 0; } catch (e) { /* noop */ } };
    o.onBack = function (changed) {
      if (ctl) ctl.detach();
      if (activeOverlay === ctl) activeOverlay = null;
      try { if (ov.parentNode) ov.parentNode.removeChild(ov); } catch (e) { /* noop */ }
      try { doc.body.style.overflow = prev; } catch (e2) { /* noop */ }
      if (typeof opts.onClose === 'function') opts.onClose(changed);
    };
    var ctl = mount(inner, o);
    ctl.overlay = ov;
    activeOverlay = ctl;
    return ctl;
  }

  root.AJHwSheet = {
    DRAFT_PREFIX: DRAFT_PREFIX,
    state: state,
    labels: labels,
    labelOf: labelOf,
    numQuestions: numQuestions,
    answerButtonLabel: answerButtonLabel,
    scoreText: scoreText,
    fmtJst: fmtJst,
    revealNote: revealNote,
    loadDraft: loadDraft,
    saveDraft: saveDraft,
    clearDraft: clearDraft,
    confirmText: confirmText,
    errText: errText,
    formHtml: formHtml,
    resultHtml: resultHtml,
    mount: mount,
    openOverlay: openOverlay,
    toast: defaultToast,
    // テスト用 (scripts/health_check/test_homework_sheet_front.py)。画面からは呼ばない
    _useStorage: function (s) { testStore = s; },
    _clearMemory: function () { mem = {}; }
  };
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
