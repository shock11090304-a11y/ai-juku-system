// =============================================================================
// 冊子受験画面 — エントリ
//
// 起動状態機械 (§9.1) と提出状態機械 (§10)。
//
// ★ 順序に意味がある箇所が 2 つある。どちらも入れ替えると静かに壊れる。
//   1. **attempt の insert は PDF を落として寸法を取り終えた後**。
//      先に作ると、数十秒のダウンロードが試験時間から引かれる。
//   2. 提出は FREEZE → DRAIN → FLUSH_ANSWERS → RECONCILE → FLUSH_INK → RPC。
//      DRAIN を飛ばすと、RPC の後に届いた再送が 42501 で黙って消える。
//      RECONCILE を飛ばすと、行の無い設問が「無得点 + 復習キュー不参加 + 解説が
//      永久に出ない」の三重障害になる。
// =============================================================================
import { sb, serverNow, haveServerClock } from '/exam-book-sb.mjs?v=1';
import { Book, signedUrl, ZOOM_STEPS } from '/exam-book-pdf.mjs?v=1';
import { Ink, MODE } from '/exam-book-ink.mjs?v=1';
import { PENS, parseStrokes, mergeAppend } from '/exam-book-model.mjs?v=1';
import { InkQueue, AnswerQueue, LocalCopy, TabLock, submitAttempt } from '/exam-book-sync.mjs?v=1';
import { AnswerPane } from '/exam-book-answers.mjs?v=1';

const $ = (sel) => document.querySelector(sel);
const app = {
  book: null, attempt: null, questions: [], doc: null, ink: null,
  queue: null, answers: null, pane: null, local: null, lock: null,
  pageEls: [], zoom: 0, timer: null, submitting: false, finished: false,
  resultRows: null,           // ★ メモリに保持する (再受験で消える値を再取得しない)
};

// =============================================================================
// 画面の小道具
// =============================================================================
function setStage(name) { document.body.dataset.stage = name; }

function say(msg, tone = '') {
  const b = $('#banner');
  b.textContent = msg || '';
  b.dataset.tone = tone;
  b.hidden = !msg;
}

function fatal(title, detail) {
  setStage('fatal');
  $('#fatal-title').textContent = title;
  $('#fatal-detail').textContent = detail || '';
  $('#fatal-reload').onclick = () => location.reload();
}

function progress(pct, label) {
  $('#boot-bar-fill').style.width = `${Math.round(pct * 100)}%`;
  if (label) $('#boot-label').textContent = label;
}

/**
 * 確認ダイアログ。★戻り値は押されたボタンの key。
 * @param {{title:string, body:Node|string, buttons:Array<{key:string,label:string,tone?:string}>}} o
 */
function ask(o) {
  return new Promise((resolve) => {
    const dlg = $('#dialog');
    $('#dialog-title').textContent = o.title;
    const body = $('#dialog-body');
    body.innerHTML = '';
    if (typeof o.body === 'string') body.textContent = o.body;
    else if (o.body) body.appendChild(o.body);
    const bar = $('#dialog-buttons');
    bar.innerHTML = '';
    for (const b of o.buttons) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = b.label;
      if (b.tone) btn.dataset.tone = b.tone;
      btn.addEventListener('click', () => { dlg.close(); resolve(b.key); }, { once: true });
      bar.appendChild(btn);
    }
    dlg.showModal();
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// =============================================================================
// 起動
// =============================================================================
async function boot() {
  setStage('boot');
  progress(0.02, '接続を確認しています');

  // --- 認証 -----------------------------------------------------------------
  const { data: sess } = await sb().auth.getSession();
  if (!sess || !sess.session) { showLogin(); return; }
  const uid = sess.session.user.id;

  // --- ブック ---------------------------------------------------------------
  progress(0.06, '冊子を探しています');
  const book = await pickBook();
  if (!book) return;
  app.book = book;
  $('#book-title').textContent = book.title;

  if (!book.pdf_path) {
    fatal('この本には冊子 PDF がありません',
          '先生に連絡してください (books.pdf_path が空です)。');
    return;
  }

  // --- PDF ------------------------------------------------------------------
  // ★ ここで attempt をまだ作らない。作ると download の数十秒が試験時間から引かれる。
  const doc = new Book();
  let opened = false;
  for (let tryNo = 0; tryNo < 3 && !opened; tryNo++) {
    try {
      progress(0.1, tryNo ? `冊子を取得しています (再試行 ${tryNo})` : '冊子を取得しています');
      const url = await signedUrl(sb(), book.pdf_path);     // 毎回取り直す (署名切れ対策)
      await doc.open(url, (frac) => progress(0.1 + frac * 0.6, '冊子を取得しています'));
      opened = true;
    } catch (e) {
      if (tryNo === 2) {
        fatal('冊子を開けませんでした',
              `${e.message}\n通信を確認して再読み込みしてください。答案はまだ作られていません。`);
        return;
      }
      await sleep(800 * (tryNo + 1));
    }
  }
  app.doc = doc;

  // --- ページ枠 (sized) ------------------------------------------------------
  progress(0.72, 'ページを準備しています');
  app.pageEls = doc.buildPageElements($('#viewer'));
  setZoom(0);

  // --- 冊子の差し替え検知 ----------------------------------------------------
  const replaced = await pdfReplaced(book);

  // --- attempt --------------------------------------------------------------
  progress(0.78, '答案を用意しています');
  const at = await resolveAttempt(book.id, uid);
  if (!at) return;
  app.attempt = at.attempt;

  app.local = new LocalCopy(app.attempt.id, (m) => say(m, 'warn'));
  app.lock = new TabLock(app.attempt.id, () => {
    app.queue && app.queue.stopAll();
    setReadonlyAll('このタブは読み取り専用です (同じ答案を別のタブで開いています)');
  });

  // --- 設問 -----------------------------------------------------------------
  progress(0.84, '設問を読み込んでいます');
  const qs = await sb().from('student_questions')
    .select('*').eq('book_id', book.id).order('number');
  if (qs.error) { fatal('設問を読み込めませんでした', qs.error.message); return; }
  if (!qs.data.length) {
    fatal('この冊子は現在公開停止です', '先生に連絡してください。');
    return;
  }
  app.questions = qs.data;

  // --- 答案ペイン ------------------------------------------------------------
  app.pane = new AnswerPane($('#answers'), {
    onChange: (qid, v, sec) => app.answers.set(qid, v, sec),
    onJump: (page) => jumpToPage(page),
  });
  app.pane.build(app.questions);

  // --- answers --------------------------------------------------------------
  progress(0.88, '解答欄を用意しています');
  app.answers = new AnswerQueue({
    attemptId: app.attempt.id,
    on: {
      frozen: (m) => onFrozen(m),
      error: (m) => say(m, 'warn'),
      saved: () => { if (!app.answers.pending()) say(''); },
      pending: () => renderStatus(),
    },
  });
  const seeded = await app.answers.seed(app.questions.map((q) => q.id));
  if (!seeded.ok) {
    fatal('解答欄を用意できませんでした',
          `${seeded.error && seeded.error.message}\nこのまま受験すると採点されません。`);
    return;
  }
  const have = await sb().from('answers')
    .select('question_id, user_answer, time_spent_sec').eq('attempt_id', app.attempt.id);
  if (!have.error) {
    for (const r of have.data) app.pane.setValue(r.question_id, r.user_answer, r.time_spent_sec);
  }

  // --- 手書き ---------------------------------------------------------------
  progress(0.94, '書き込みを読み込んでいます');
  app.ink = new Ink(
    $('#viewer'),
    (page) => app.queue.touch(page),
    (page) => say(`${page} ページはこれ以上書き込めません (1 ページの上限に達しました)`, 'bad'),
  );
  app.queue = new InkQueue({
    attemptId: app.attempt.id,
    getStrokes: (page) => app.ink.model(page).strokes,
    local: app.local,
    on: {
      pending: () => renderStatus(),
      frozen: (m) => onFrozen(m),
      invalid: (page, m) => say(`${page} ページの書き込みを保存できませんでした: ${m}`, 'bad'),
      conflict: (page) => onConflict(page),
      saved: () => renderStatus(),
    },
  });

  const loaded = await loadAnnotations();
  if (!loaded) return;

  if (replaced) {
    app.ink.setMode(MODE.READ);
    app.queue.stopAll();
    setReadonlyAll('冊子が差し替えられています。この答案には書き込めません。先生に連絡してください');
  }

  // --- 準備完了 --------------------------------------------------------------
  wireUi();
  startTimer();
  setStage('ready');
  progress(1, '');
  renderStatus();
}

// --- ブック選択 ---------------------------------------------------------------
async function pickBook() {
  const want = new URLSearchParams(location.search).get('book');
  let q = sb().from('books')
    .select('id, title, pdf_path, time_limit_sec, page_count').eq('is_published', true);
  if (want) q = q.eq('id', want);
  const { data, error } = await q.order('created_at', { ascending: false });
  if (error) { fatal('冊子の一覧を取得できませんでした', error.message); return null; }
  if (!data.length) {
    fatal(want ? 'その冊子は見つかりません' : '公開されている冊子がありません',
          '先生に連絡してください。');
    return null;
  }
  if (data.length === 1) return data[0];

  const list = document.createElement('div');
  list.className = 'booklist';
  const chosen = await new Promise((resolve) => {
    for (const b of data) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = b.title;
      btn.addEventListener('click', () => { $('#dialog').close(); resolve(b); }, { once: true });
      list.appendChild(btn);
    }
    ask({ title: '受験する冊子を選んでください', body: list, buttons: [] });
  });
  return chosen;
}

// --- 冊子の差し替え検知 -------------------------------------------------------
// books に版の列が無いので Storage 側のメタが唯一の手がかり。
async function pdfReplaced(book) {
  try {
    const i = book.pdf_path.lastIndexOf('/');
    const dir = i < 0 ? '' : book.pdf_path.slice(0, i);
    const name = i < 0 ? book.pdf_path : book.pdf_path.slice(i + 1);
    const { data } = await sb().storage.from('book-pdfs').list(dir, { search: name });
    const hit = (data || []).find((o) => o.name === name);
    if (!hit) return false;
    const stamp = hit.updated_at || hit.created_at || '';
    const key = `pdfver:${book.id}`;
    const seen = localStorage.getItem(key);
    if (seen && stamp && seen !== stamp) return true;
    if (stamp) localStorage.setItem(key, stamp);
    return false;
  } catch (_) {
    return false;          // 判定できないときは止めない (受験できない方が困る)
  }
}

// --- attempt の確定 -----------------------------------------------------------
async function resolveAttempt(bookId, userId) {
  const open = await sb().from('attempts')
    .select('id, started_at, submitted_at')
    .eq('book_id', bookId).eq('user_id', userId).is('submitted_at', null)
    .order('started_at', { ascending: false });
  if (open.error) { fatal('答案を取得できませんでした', open.error.message); return null; }

  if (open.data.length >= 1) {
    if (open.data.length > 1) {
      // ★ 削除ボタンは出さない。cascade で手書きごと消える。
      say(`受験中の答案が他に ${open.data.length - 1} 件あります。`
        + 'この本の正解と解説は、それを全部提出するまで表示されません', 'warn');
    }
    return { attempt: open.data[0], created: false };
  }

  const ins = await sb().from('attempts')
    .insert({ book_id: bookId, user_id: userId })
    .select('id, started_at, submitted_at').single();
  if (ins.error) { fatal('答案を作成できませんでした', ins.error.message); return null; }
  return { attempt: ins.data, created: true };
}

// --- annotations --------------------------------------------------------------
// ★ 「取得失敗」と「白紙」を絶対に区別する。区別しないと、失敗したページに 1 本書いた
//   瞬間にページ丸ごと上書きされて既存の書き込みが全消しになる。
async function loadAnnotations() {
  for (let tryNo = 0; tryNo < 3; tryNo++) {
    const r = await sb().from('annotations')
      .select('page, strokes, updated_at').eq('attempt_id', app.attempt.id).order('page');
    if (!r.error) {
      const rows = new Map((r.data || []).map((x) => [x.page, x]));
      for (const p of app.doc.pages) {
        const row = rows.get(p.n);
        const parsed = row ? parseStrokes(row.strokes) : { ok: true, strokes: [] };
        if (row && !parsed.ok) {
          say(`${p.n} ページに古い形式の書き込みがあります (表示できません)`, 'warn');
        }
        const rec = app.local.recover(p.n, parsed.strokes);
        app.ink.loadPage(p.n, rec.strokes);
        app.queue.markLoaded(p.n, row ? row.updated_at : null);
        if (rec.hasLocal) app.queue.touch(p.n);   // 端末に残っていた分を送り直す
      }
      return true;
    }
    await sleep(600 * (tryNo + 1));
  }
  fatal('書き込みを読み込めませんでした',
        'このまま始めると、これまでの書き込みが消えるおそれがあります。通信を確認して再読み込みしてください。');
  return false;
}

// =============================================================================
// UI の配線
// =============================================================================
function wireUi() {
  // --- モード ---------------------------------------------------------------
  for (const b of document.querySelectorAll('[data-mode]')) {
    b.addEventListener('click', () => {
      const m = b.dataset.mode === 'write' ? MODE.WRITE : MODE.READ;
      app.ink.setMode(m);
      for (const x of document.querySelectorAll('[data-mode]')) x.classList.toggle('on', x === b);
      flushVisible();
      $('#tools').hidden = m !== MODE.WRITE;
    });
  }
  document.querySelector('[data-mode="read"]').classList.add('on');
  $('#tools').hidden = true;

  // --- ペン -----------------------------------------------------------------
  for (const b of document.querySelectorAll('[data-pen]')) {
    b.addEventListener('click', () => {
      app.ink.setPen(PENS[b.dataset.pen]);
      for (const x of document.querySelectorAll('[data-pen],[data-tool="eraser"]')) {
        x.classList.toggle('on', x === b);
      }
    });
  }
  document.querySelector('[data-pen="normal"]').classList.add('on');

  $('[data-tool="eraser"]').addEventListener('click', (e) => {
    app.ink.setEraser(true);
    for (const x of document.querySelectorAll('[data-pen],[data-tool="eraser"]')) {
      x.classList.toggle('on', x === e.currentTarget);
    }
  });
  $('[data-tool="undo"]').addEventListener('click', () => app.ink.undo(currentPage()));
  $('[data-tool="redo"]').addEventListener('click', () => app.ink.redo(currentPage()));

  // --- ズーム ---------------------------------------------------------------
  $('[data-zoom="in"]').addEventListener('click', () => setZoom(app.zoom + 1));
  $('[data-zoom="out"]').addEventListener('click', () => setZoom(app.zoom - 1));

  // --- 提出 -----------------------------------------------------------------
  $('#submit').addEventListener('click', () => submitFlow({ auto: false }));

  wireGrip();

  // --- ページ描画 (可視分だけ) ----------------------------------------------
  // ★ 冊子を一度も動かしていないうちは答案ペインを追従させない。
  //   起動直後に IntersectionObserver が 1 回発火するので、追従させると
  //   「ページ指定なし」の設問が画面の外へ流れて **最初から見えない**。
  //   (縦画面のボトムシートだと特に気づけない)
  let viewerMoved = false;
  $('#viewer').addEventListener('scroll', () => { viewerMoved = true; }, { passive: true });

  const io = new IntersectionObserver((entries) => {
    for (const en of entries) {
      if (en.isIntersecting) app.doc.render(en.target).catch(() => {});
      else queueFlushPage(Number(en.target.dataset.page));
    }
    if (!viewerMoved) return;
    const first = entries.find((e) => e.isIntersecting);
    if (first) app.pane.followPage(Number(first.target.dataset.page));
  }, { root: $('#viewer'), rootMargin: '150% 0px' });

  // ★ 回転 / Split View / ボトムシート開閉 — window の resize も scroll も起きない
  //   変化を全部これで拾う。拾い損ねると線の途中からずれる。
  const ro = new ResizeObserver((entries) => {
    for (const en of entries) {
      const page = Number(en.target.dataset.page);
      app.ink.invalidateRect(page);
      app.ink.redraw(page);
      clearTimeout(en.target._rt);
      en.target._rt = setTimeout(() => app.doc.render(en.target).catch(() => {}), 120);
    }
  });
  for (const el of app.pageEls) { io.observe(el); ro.observe(el); }

  // DPR の変化は ResizeObserver では発火しない
  const dpr = window.devicePixelRatio || 1;
  try {
    matchMedia(`(resolution: ${dpr}dppx)`).addEventListener('change', () => {
      for (const el of app.pageEls) {
        app.ink.redraw(Number(el.dataset.page));
        app.doc.render(el).catch(() => {});
      }
    });
  } catch (_) { /* 古い Safari */ }

  // --- 離脱 -----------------------------------------------------------------
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState !== 'hidden') { startTimer(); return; }
    app.pane.pauseTiming();
    app.answers.flush().catch(() => {});
    app.queue.flushAll(5000).catch(() => {});
  });
  // ★ pagehide は「最後の砦」に数えない (sendBeacon はヘッダ不可 / keepalive は 64KB)。
  //   保険はローカル写しの側にある。ここはベストエフォート。
  window.addEventListener('pagehide', () => {
    app.answers.flush().catch(() => {});
    app.queue.flushAll(1500).catch(() => {});
  });
  window.addEventListener('beforeunload', (e) => {
    if (app.finished) return;
    if (app.queue.pending() || app.answers.pending()) { e.preventDefault(); e.returnValue = ''; }
  });
}

// --- 仕切り / ボトムシートの取っ手 ------------------------------------------
// ★ 横画面では冊子の比率、縦画面ではシートの高さ。どちらも localStorage に覚える。
function wireGrip() {
  const grip = $('#grip');
  const wide = () => matchMedia('(min-width: 1000px)').matches;
  const KEY = 'exambook:layout';

  const saved = (() => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (_) { return {}; } })();
  const apply = (o) => {
    if (o.split != null) {
      document.documentElement.style.setProperty('--split', String(o.split));
    }
    if (o.sheet != null) {
      document.documentElement.style.setProperty('--sheet', `${o.sheet}px`);
    }
  };
  apply(saved);

  let from = null;
  grip.addEventListener('pointerdown', (e) => {
    grip.setPointerCapture(e.pointerId);
    const st = $('#stage').getBoundingClientRect();
    from = { x: e.clientX, y: e.clientY, rect: st,
             sheet: $('#pane').getBoundingClientRect().height };
    e.preventDefault();
  });
  grip.addEventListener('pointermove', (e) => {
    if (!from) return;
    if (wide()) {
      const r = (e.clientX - from.rect.left) / from.rect.width;
      saved.split = Math.max(0.25, Math.min(0.8, r));
    } else {
      const h = from.sheet - (e.clientY - from.y);
      saved.sheet = Math.max(80, Math.min(from.rect.height - 120, h));
    }
    apply(saved);
    for (const el of app.pageEls) app.ink.invalidateRect(Number(el.dataset.page));
    e.preventDefault();
  });
  for (const t of ['pointerup', 'pointercancel', 'lostpointercapture']) {
    grip.addEventListener(t, () => {
      if (!from) return;
      from = null;
      try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (_) {}
    });
  }
}

function setZoom(step) {
  app.zoom = Math.max(0, Math.min(ZOOM_STEPS.length - 1, step));
  $('#viewer').style.setProperty('--page-zoom', String(ZOOM_STEPS[app.zoom]));
  $('#zoom-label').textContent = `${Math.round(ZOOM_STEPS[app.zoom] * 100)}%`;
  if (app.ink) {
    for (const el of app.pageEls) app.ink.invalidateRect(Number(el.dataset.page));
    flushVisible();
  }
}

function currentPage() {
  const v = $('#viewer');
  const mid = v.scrollTop + v.clientHeight / 2;
  let best = 1;
  for (const el of app.pageEls) {
    if (el.offsetTop <= mid) best = Number(el.dataset.page);
  }
  return best;
}

function jumpToPage(page) {
  const el = app.pageEls[page - 1];
  if (!el) return;
  $('#viewer').scrollTo({ top: el.offsetTop - 8, behavior: 'smooth' });
  el.classList.add('hl');
  setTimeout(() => el.classList.remove('hl'), 1200);
}

function queueFlushPage(page) { if (app.queue) app.queue.flush(page); }
function flushVisible() { if (app.queue) for (const el of app.pageEls) app.queue.flush(Number(el.dataset.page)); }

// =============================================================================
// 状態表示
// =============================================================================
function renderStatus() {
  if (!app.queue) return;
  const ink = app.queue.pending();
  const ans = app.answers ? app.answers.pending() : 0;
  const s = $('#saveState');
  if (ink || ans) {
    s.textContent = `未保存 ${ink ? `${ink} ページ` : ''}${ink && ans ? ' / ' : ''}${ans ? `${ans} 問` : ''}`;
    s.dataset.tone = 'warn';
  } else {
    s.textContent = '保存済み';
    s.dataset.tone = 'ok';
  }
}

function setReadonlyAll(msg) {
  app.ink && app.ink.setMode(MODE.READ);
  app.pane && app.pane.setReadonly(true);
  document.body.classList.add('frozen');
  if (msg) say(msg, 'bad');
}

function onFrozen(msg) {
  if (app.submitting || app.finished) return;   // 提出中の 42501 は手順側で扱う
  app.queue.stopAll();
  setReadonlyAll(`${msg}。この端末の書き込みは残してあります`);
}

// --- 競合 (別端末が同じページを触った) ---------------------------------------
async function onConflict(page) {
  const erased = app.ink.model(page).undo.some((op) => op.type === 'erase');
  const buttons = [];
  if (!erased) buttons.push({ key: 'both', label: '両方を残す' });
  buttons.push({ key: 'mine', label: 'この端末の書き込みで上書き', tone: 'warn' });
  buttons.push({ key: 'theirs', label: '別の端末の内容を読み直す' });

  const key = await ask({
    title: `${page} ページが別の端末でも書き換えられています`,
    body: erased
      ? 'このページでは消しゴムを使っているため、自動で合流させると消したはずの線が戻ります。どちらを残すか選んでください。'
      : '手書きは追記なので、両方を残すことができます。',
    buttons,
  });

  const cur = app.ink.model(page).strokes.slice();
  const got = await app.queue.refetch(page);
  if (!got.ok) { say('別の端末の内容を読み直せませんでした', 'bad'); return; }

  if (key === 'theirs') {
    app.local.write(page, cur);            // 破棄する前に控えへ退避
    app.ink.loadPage(page, got.strokes);
    return;
  }
  if (key === 'both') {
    app.ink.loadPage(page, mergeAppend(cur, got.strokes));
  } else {
    app.ink.loadPage(page, cur);
  }
  app.queue.touch(page);
}

// =============================================================================
// タイマー
// =============================================================================
function startTimer() {
  if (app.timer) clearInterval(app.timer);
  const limit = app.book.time_limit_sec;
  const box = $('#clock');
  if (!limit) { box.textContent = '時間無制限'; return; }   // NULL なら自動提出しない
  const started = Date.parse(app.attempt.started_at);
  const tick = () => {
    if (app.finished) { clearInterval(app.timer); return; }
    const left = Math.max(0, Math.round(limit - (serverNow().getTime() - started) / 1000));
    const m = Math.floor(left / 60), s = left % 60;
    box.textContent = `${haveServerClock() ? '' : 'およそ '}残り ${m}:${String(s).padStart(2, '0')}`;
    box.dataset.tone = left <= 300 ? 'warn' : '';
    if (left <= 0 && !app.submitting) { clearInterval(app.timer); submitFlow({ auto: true }); }
  };
  tick();
  app.timer = setInterval(tick, 1000);
}

// =============================================================================
// 提出 (§10)
// =============================================================================
async function submitFlow({ auto }) {
  if (app.submitting || app.finished) return;

  // --- CONFIRM --------------------------------------------------------------
  if (!auto) {
    const miss = app.pane.unanswered();
    const body = document.createElement('div');
    if (miss.length) {
      body.appendChild(Object.assign(document.createElement('p'),
        { textContent: `未解答が ${miss.length} 問あります:` }));
      const ul = document.createElement('div');
      ul.className = 'misslist';
      for (const m of miss) {
        const b = document.createElement('button');
        b.type = 'button';
        b.textContent = `問 ${m.number}${m.page ? ` (p.${m.page})` : ''}`;
        b.addEventListener('click', () => {
          $('#dialog').close();
          app.pane.focusQuestion(m.id);
          if (m.page) jumpToPage(m.page);
        });
        ul.appendChild(b);
      }
      body.appendChild(ul);
    }
    const unsaved = app.queue.pending() + app.answers.pending();
    if (unsaved) {
      body.appendChild(Object.assign(document.createElement('p'),
        { textContent: `未保存が ${unsaved} 件あります。提出前に保存を試みます。` }));
    }
    body.appendChild(Object.assign(document.createElement('p'),
      { textContent: '提出すると、解答も書き込みも変更できません。' }));
    const yes = await ask({
      title: '提出しますか', body,
      buttons: [{ key: 'no', label: 'まだ解く' }, { key: 'yes', label: '提出する', tone: 'warn' }],
    });
    if (yes !== 'yes') return;
  }

  app.submitting = true;

  // --- FREEZE ---------------------------------------------------------------
  $('#submit').disabled = true;
  app.pane.setReadonly(true);
  app.ink.setMode(MODE.READ);
  document.body.classList.add('submitting');
  say(auto ? '時間になりました。提出しています' : '提出しています');

  const unfreeze = () => {
    app.submitting = false;
    $('#submit').disabled = false;
    document.body.classList.remove('submitting');
    if (!app.finished) { app.pane.setReadonly(false); app.queue.resume(); }
  };

  // --- DRAIN ----------------------------------------------------------------
  // ★ 予約済みの再送を全部取り消してから待つ。取り消さないと RPC の後に届いて 42501。
  await app.queue.drain();

  // --- FLUSH_ANSWERS (必須) --------------------------------------------------
  await app.answers.flush();
  if (app.answers.pending()) {
    await app.answers.flush();
    if (app.answers.pending()) {
      unfreeze();
      say('解答が保存できていません。通信を確認して、もう一度提出してください', 'bad');
      return;
    }
  }

  // --- RECONCILE (必須) ------------------------------------------------------
  const rec = await app.answers.reconcile(app.questions.map((q) => q.id));
  if (!rec.ok) {
    unfreeze();
    say(`解答欄を確認できませんでした: ${rec.error && rec.error.message}`, 'bad');
    return;
  }

  // --- FLUSH_INK (ベストエフォート) -----------------------------------------
  app.queue.resume();
  const left = await app.queue.flushAll(auto ? 20000 : 45000);
  app.queue.stopAll();
  if (left.length) {
    const go = await ask({
      title: '手書きの一部が保存できていません',
      body: `${left.length} ページ (${left.join(', ')}) の書き込みがサーバに届いていません。`
          + '提出すると、この書き込みは二度と保存できません。提出しますか。',
      buttons: [{ key: 'no', label: '提出しない' }, { key: 'yes', label: '提出する', tone: 'warn' }],
    });
    if (go !== 'yes') { unfreeze(); say('提出を取りやめました', 'warn'); return; }
  }

  // --- SUBMITTING -----------------------------------------------------------
  app.queue.submitted = true;
  let res = await submitAttempt(app.attempt.id);
  if (res.state === 'retry') {
    await sleep(1500);
    res = await submitAttempt(app.attempt.id);      // 未提出のときしか通らない = 二重採点なし
  }
  if (res.state !== 'ok') {
    app.queue.submitted = false;
    unfreeze();
    say(res.message || '提出できませんでした', 'bad');
    return;
  }

  app.finished = true;
  await showResult(left);
}

// =============================================================================
// 結果 (復習モード)
// =============================================================================
async function showResult(inkLeft) {
  say('');
  setReadonlyAll('');
  document.body.classList.remove('submitting');
  document.body.classList.add('reviewing');
  if (app.timer) clearInterval(app.timer);

  const [at, qs, ans] = await Promise.all([
    sb().from('attempts').select('total_score, max_score, elapsed_sec, submitted_at')
      .eq('id', app.attempt.id).maybeSingle(),
    sb().from('student_questions').select('*').eq('book_id', app.book.id).order('number'),
    sb().from('answers').select('question_id, user_answer, is_correct')
      .eq('attempt_id', app.attempt.id),
  ]);

  // ★ ここで取った行を **メモリに保持**する。「もう一度受験する」を押すと
  //   student_questions.revealed がブック単位で false に落ちるので、再取得すると
  //   ○× だけ残って解説が空になる。
  app.resultRows = (qs.data && qs.data.length) ? qs.data : app.questions;
  const amap = new Map((ans.data || []).map((r) => [r.question_id, r]));

  const revealed = app.pane.showResult(app.resultRows, amap);

  const s = at.data || {};
  const panel = $('#result');
  panel.hidden = false;
  $('#result-score').textContent =
    (s.total_score == null) ? '採点結果を取得できませんでした'
                            : `${s.total_score} / ${s.max_score} 点`;
  const wrong = (ans.data || []).filter((r) => r.is_correct !== true).length;
  $('#result-detail').textContent =
    `誤答 ${wrong} 問は復習キューに入りました`
    + (s.elapsed_sec != null ? ` ・ 所要 ${Math.floor(s.elapsed_sec / 60)} 分` : '')
    + (revealed ? '' : ' ・ 正解と解説は、この本の受験中の答案をすべて提出すると表示されます');

  // ★ 送り切れなかった書き込みのローカル写しは消さない。黙って捨てない。
  const leftover = app.local.leftovers();
  if (inkLeft.length || leftover.length) {
    $('#result-warn').hidden = false;
    $('#result-warn').textContent =
      `この端末に、保存できなかった書き込みが残っています (${
        (inkLeft.length ? inkLeft : leftover).join(', ')} ページ)。`
      + '同じ端末・同じブラウザで開けば復元できます。先生に連絡してください。';
  }

  $('#retake').addEventListener('click', async () => {
    const go = await ask({
      title: 'もう一度受験しますか',
      body: '開始すると、この本の正解と解説は新しい答案を提出するまで見えなくなります。'
          + '今表示している結果はこの画面に残ります。',
      buttons: [{ key: 'no', label: 'やめる' }, { key: 'yes', label: '始める', tone: 'warn' }],
    });
    if (go === 'yes') location.href = `/exam-book.html?book=${app.book.id}&new=1`;
  }, { once: true });

  app.lock && app.lock.close();
}

// =============================================================================
// ログイン (この画面は Supabase Auth のセッションだけを見る)
// =============================================================================
/** Supabase のエラー文は英語で、生徒には読めない。よく出るものだけ日本語にする。 */
function loginMessage(error) {
  const m = String((error && error.message) || '');
  if (/invalid login credentials/i.test(m)) {
    return 'メールアドレスかパスワードが違います';
  }
  if (/email not confirmed/i.test(m)) {
    return 'このアカウントはまだ有効になっていません。先生に連絡してください';
  }
  if (/email logins are disabled|signups not allowed/i.test(m)) {
    return 'この方法でのログインが止められています。先生に連絡してください';
  }
  if (/rate limit|too many/i.test(m)) {
    return '試行回数が多すぎます。少し待ってからやり直してください';
  }
  if (/failed to fetch|networkerror|load failed/i.test(m)) {
    return '通信できませんでした。電波を確認してやり直してください';
  }
  return `ログインできません (${m})`;   // 想定外はそのまま出す (黙って隠さない)
}

function showLogin() {
  setStage('login');
  const form = $('#login-form');
  const btn = form.querySelector('button[type="submit"]');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    btn.disabled = true;                       // 二重送信でロック扱いにされないように
    $('#login-msg').textContent = 'ログインしています…';
    let res;
    try {
      res = await sb().auth.signInWithPassword({
        // ★ iPad で貼り付けると前後に空白が付くことがある。メールは trim する。
        //   パスワードは trim しない (末尾の空白も本人が決めた文字の一部)。
        email: $('#login-email').value.trim(),
        password: $('#login-pass').value,
      });
    } catch (err) {
      res = { error: err };
    }
    if (res.error) {
      $('#login-msg').textContent = loginMessage(res.error);
      btn.disabled = false;
      return;
    }
    location.reload();
  });
}

// =============================================================================
boot().catch((e) => fatal('起動できませんでした', (e && e.message) || String(e)));
