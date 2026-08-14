// =============================================================================
// 先生用の冊子登録
//
// ★ ターミナルを使わずにブラウザだけで完結させる。PDF を選ぶ → 中身を検査 →
//   アップロード → 冊子を作る → 設問を入れる → 公開、までを 1 画面で。
//
// ★ 危ないので **出していない操作** が 2 つある:
//   ・冊子の削除 … answers / attempts / annotations が cascade で消える。
//     生徒の答案と手書きが巻き添えになるので、非公開にするだけにする。
//   ・設問の削除 … 同上 (answers.question_id が参照している)。
//   どちらも必要になったら SQL Editor で、影響範囲を見てから行うこと。
//
// ★ 既に提出された答案がある冊子の **正解を変えると、過去の採点と食い違う**。
//   採点は提出時に確定して answers.is_correct に入っており、後から再計算されない。
//   変える前に必ず警告を出す。
// =============================================================================
import { sb } from '/exam-book-sb.mjs?v=1';
import { Book } from '/exam-book-pdf.mjs?v=1';
import {
  SUBJECTS, ANSWER_TYPES, MAX_PDF_BYTES,
  normalizeQuestion, validateQuestions, questionPayload, validateBook,
  checkPdfFile, pdfPath, parseImport,
} from '/exam-book-admin-model.mjs?v=1';

const $ = (s) => document.querySelector(s);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};

const app = { books: [], current: null, rows: [], pdfFile: null, pdfPages: null };

function setStage(n) { document.body.dataset.stage = n; }
function say(msg, tone = '') {
  const b = $('#banner');
  b.textContent = msg || '';
  b.dataset.tone = tone;
  b.hidden = !msg;
}

// =============================================================================
// 起動
// =============================================================================
async function boot() {
  setStage('boot');
  const { data: sess } = await sb().auth.getSession();
  if (!sess || !sess.session) { showLogin(); return; }

  const me = await sb().from('profiles').select('id, role, display_name')
    .eq('id', sess.session.user.id).maybeSingle();
  if (me.error) { fatal('プロフィールを読めませんでした', me.error.message); return; }
  if (!me.data || me.data.role !== 'teacher') {
    fatal('この画面は講師だけが使えます',
          `今のアカウントは ${me.data ? me.data.role : '不明'} です。`
        + 'SQL Editor で profiles.role を teacher にしてください。');
    return;
  }
  $('#who').textContent = `${me.data.display_name || ''} (講師)`;

  wire();
  await loadBooks();
  setStage('ready');
}

function fatal(title, detail) {
  setStage('fatal');
  $('#fatal-title').textContent = title;
  $('#fatal-detail').textContent = detail || '';
}

function showLogin() {
  setStage('login');
  const form = $('#login-form');
  const btn = form.querySelector('button[type="submit"]');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    btn.disabled = true;
    $('#login-msg').textContent = 'ログインしています…';
    const { error } = await sb().auth.signInWithPassword({
      email: $('#login-email').value.trim(),
      password: $('#login-pass').value,
    });
    if (error) {
      $('#login-msg').textContent = /invalid login credentials/i.test(error.message)
        ? 'メールアドレスかパスワードが違います' : `ログインできません (${error.message})`;
      btn.disabled = false;
      return;
    }
    location.reload();
  });
}

// =============================================================================
// 冊子一覧
// =============================================================================
async function loadBooks() {
  const r = await sb().from('books')
    .select('id, title, subject, level, pdf_path, page_count, time_limit_sec, is_published, created_at')
    .order('created_at', { ascending: false });
  if (r.error) { say(`冊子を読めませんでした: ${r.error.message}`, 'bad'); return; }
  app.books = r.data || [];

  // 設問数と受験数を 1 回ずつでまとめて数える
  const counts = await sb().from('questions').select('book_id, id');
  const qn = new Map();
  for (const q of (counts.data || [])) qn.set(q.book_id, (qn.get(q.book_id) || 0) + 1);
  const at = await sb().from('attempts').select('book_id, submitted_at');
  const an = new Map();
  for (const a of (at.data || [])) {
    if (a.submitted_at) an.set(a.book_id, (an.get(a.book_id) || 0) + 1);
  }

  const host = $('#books');
  host.innerHTML = '';
  if (!app.books.length) { host.appendChild(el('p', 'muted', 'まだ冊子がありません')); return; }

  for (const b of app.books) {
    const row = el('div', 'bookrow');
    row.dataset.id = b.id;
    const main = el('div', 'bookrow-main');
    main.appendChild(el('div', 'bookrow-title', b.title));
    const sub = SUBJECTS.find((s) => s.value === b.subject);
    main.appendChild(el('div', 'bookrow-meta',
      `${sub ? sub.label : b.subject}`
      + `${b.level ? ' / ' + b.level : ''}`
      + ` ・ ${b.page_count || '?'} ページ`
      + ` ・ 設問 ${qn.get(b.id) || 0}`
      + ` ・ 提出 ${an.get(b.id) || 0}`
      + `${b.pdf_path ? '' : ' ・ ★PDF なし'}`));
    row.appendChild(main);

    const pub = el('button', 'pub' + (b.is_published ? ' on' : ''),
                   b.is_published ? '公開中' : '非公開');
    pub.type = 'button';
    pub.addEventListener('click', () => togglePublish(b, qn.get(b.id) || 0));
    row.appendChild(pub);

    const open = el('button', '', '設問を編集');
    open.type = 'button';
    open.addEventListener('click', () => openBook(b));
    row.appendChild(open);

    host.appendChild(row);
  }
}

async function togglePublish(book, questionCount) {
  // ★ 設問が 0 の本を公開すると、生徒には「この冊子は現在公開停止です」と出て
  //   何も解けない。公開の前にここで止める。
  if (!book.is_published && questionCount === 0) {
    say('設問が 1 問も無い冊子は公開できません (生徒の画面で何も出ません)', 'warn');
    return;
  }
  if (!book.is_published && !book.pdf_path) {
    say('PDF が無い冊子は公開できません', 'warn');
    return;
  }
  const r = await sb().from('books').update({ is_published: !book.is_published })
    .eq('id', book.id).select('id, is_published');
  if (r.error) { say(`切り替えられませんでした: ${r.error.message}`, 'bad'); return; }
  if (!r.data || !r.data.length) { say('切り替えられませんでした (権限がありません)', 'bad'); return; }
  say(`「${book.title}」を${r.data[0].is_published ? '公開' : '非公開に'}しました`, 'ok');
  await loadBooks();
}

// =============================================================================
// 新しい冊子
// =============================================================================
function wire() {
  $('#logout').addEventListener('click', async () => {
    await sb().auth.signOut();
    location.reload();
  });

  const sel = $('#nb-subject');
  for (const s of SUBJECTS) {
    const o = document.createElement('option');
    o.value = s.value; o.textContent = s.label;
    sel.appendChild(o);
  }

  $('#nb-file').addEventListener('change', (e) => inspectPdf(e.target.files[0]));
  $('#nb-create').addEventListener('click', createBook);
  $('#q-import').addEventListener('change', (e) => importJson(e.target.files[0]));
  $('#q-add').addEventListener('click', () => { addRow(); renderRows(); });
  $('#q-save').addEventListener('click', saveQuestions);
  $('#q-close').addEventListener('click', () => {
    app.current = null; app.rows = [];
    $('#editor').hidden = true;
  });
  $('#fatal-reload').addEventListener('click', () => location.reload());
}

/** 選ばれた PDF を **送る前に** ブラウザで開いて確かめる。 */
async function inspectPdf(file) {
  app.pdfFile = null; app.pdfPages = null;
  const box = $('#nb-pdfinfo');
  box.textContent = '';
  box.dataset.tone = '';
  if (!file) return;

  const basic = checkPdfFile(file);
  if (!basic.ok) { box.textContent = `✗ ${basic.reason}`; box.dataset.tone = 'bad'; return; }

  box.textContent = '開いて確かめています…';
  try {
    const buf = new Uint8Array(await file.arrayBuffer());
    const doc = new Book();
    // ★ 実際に pdf.js で開く。壊れている / パスワード付き はここで分かる。
    //   上げてから気づくと、生徒の画面で「冊子を開けませんでした」になる。
    const url = URL.createObjectURL(new Blob([buf], { type: 'application/pdf' }));
    const pages = await doc.open(url);
    URL.revokeObjectURL(url);
    app.pdfFile = file;
    app.pdfPages = pages;
    box.textContent = `✓ ${pages} ページ / ${(file.size / 1048576).toFixed(1)}MB — 使えます`;
    box.dataset.tone = 'ok';
    if (!$('#nb-title').value.trim()) {
      $('#nb-title').value = (file.name || '').replace(/\.pdf$/i, '');
    }
  } catch (e) {
    box.textContent = `✗ この PDF は開けません (${(e && e.message) || e})。`
                    + 'パスワードが掛かっているか、壊れている可能性があります';
    box.dataset.tone = 'bad';
  }
}

async function createBook() {
  const btn = $('#nb-create');
  const minutes = $('#nb-limit').value.trim();
  const book = {
    title: $('#nb-title').value.trim(),
    subject: $('#nb-subject').value,
    level: $('#nb-level').value.trim() || null,
    time_limit_sec: minutes === '' ? null : Number(minutes),
  };
  const v = validateBook({ ...book, time_limit_sec: minutes === '' ? null : Number(minutes) });
  if (!v.ok) { say(v.errors.join(' / '), 'warn'); return; }
  if (!app.pdfFile) { say('PDF を選んでください', 'warn'); return; }

  btn.disabled = true;
  say('冊子を作っています…');
  try {
    // 1. 先に行を作る (id が要る。pdf_path は id から決まる)
    const ins = await sb().from('books').insert({
      title: book.title, subject: book.subject, level: book.level,
      page_count: app.pdfPages,
      time_limit_sec: book.time_limit_sec == null ? null : book.time_limit_sec * 60,
      is_published: false,          // ★ 設問を入れるまで公開しない
    }).select('id, title').single();
    if (ins.error) throw new Error(ins.error.message);

    // 2. PDF を上げる
    const path = pdfPath(ins.data.id);
    const up = await sb().storage.from('book-pdfs')
      .upload(path, app.pdfFile, { contentType: 'application/pdf', upsert: true });
    if (up.error) {
      // ★ 行だけ残ると「PDF なし」の冊子になる。消さずに知らせる (消すと cascade が怖い)。
      throw new Error(`PDF を上げられませんでした: ${up.error.message}`
                    + '（冊子の行は作られています。もう一度 PDF を選んで作り直すか、'
                    + '先に一覧から確認してください）');
    }

    // 3. pdf_path を書く
    const upd = await sb().from('books').update({ pdf_path: path })
      .eq('id', ins.data.id).select('id');
    if (upd.error || !upd.data.length) throw new Error('PDF の場所を記録できませんでした');

    say(`「${ins.data.title}」を作りました。続けて設問を入れてください`, 'ok');
    $('#nb-title').value = ''; $('#nb-level').value = ''; $('#nb-limit').value = '';
    $('#nb-file').value = ''; $('#nb-pdfinfo').textContent = '';
    app.pdfFile = null; app.pdfPages = null;
    await loadBooks();
    const made = app.books.find((b) => b.id === ins.data.id);
    if (made) openBook(made);
  } catch (e) {
    say((e && e.message) || String(e), 'bad');
  } finally {
    btn.disabled = false;
  }
}

/**
 * 変換した JSON をまとめて読み込む。
 * ★ **既に保存された設問がある冊子には入れない**。番号がぶつかって
 *   どちらが正か分からなくなり、生徒の答案が参照している行を壊しかねない。
 * ★ 読み込んだだけでは保存しない。必ず人が見てから「保存する」を押す。
 */
async function importJson(file) {
  const note = $('#q-import-note');
  note.hidden = true;
  $('#q-import').value = '';
  if (!file || !app.current) return;

  if (app.rows.some((r) => r.id)) {
    say('この冊子には既に保存された設問があります。'
      + '一括読み込みは、設問がまだ 1 問も無い冊子にだけ使えます', 'warn');
    return;
  }

  let text;
  try {
    text = await file.text();
  } catch (e) {
    say('ファイルを読めませんでした', 'bad');
    return;
  }
  const r = parseImport(text);
  if (!r.ok) { say(`読み込めません: ${r.reason}`, 'bad'); return; }

  // 送る前にアプリと同じ検証器を通す (壊れたものを表に入れない)
  const v = validateQuestions(r.rows.map(normalizeQuestion), { pageCount: app.current.page_count });

  app.rows = r.rows;
  renderRows();
  markDirty();
  if (!v.ok) showErrors(v.errors);

  // ★ 起算の確認。機械では証明しきれないので、人が 1 件だけ実物と照合する。
  if (r.preview && r.preview.length) {
    const p = r.preview[0];
    note.hidden = false;
    note.textContent =
      `${r.rows.length} 問を読み込みました。★ 選択肢の番号がずれていないか、`
      + `1 問だけ実物と照合してください — 問${p.number}「${p.stem}」の正解は `
      + `${p.correct_answer} 番 =「${p.correct_text}」です。`
      + 'ここが違っていたら、その冊子は全問ずれています。';
  }
  say(v.ok ? `${r.rows.length} 問を読み込みました。中身を確認してから保存してください`
           : `${r.rows.length} 問を読み込みましたが ${v.errors.length} 件おかしいところがあります`,
      v.ok ? 'ok' : 'warn');
}

// =============================================================================
// 設問の編集
// =============================================================================
async function openBook(book) {
  app.current = book;
  $('#editor').hidden = false;
  $('#ed-title').textContent = book.title;
  $('#ed-meta').textContent = `${book.page_count || '?'} ページ`
    + `${book.is_published ? ' ・ 公開中' : ' ・ 非公開'}`;

  const r = await sb().from('questions').select('*').eq('book_id', book.id).order('number');
  if (r.error) { say(`設問を読めませんでした: ${r.error.message}`, 'bad'); return; }
  app.rows = (r.data || []).map((q) => ({
    id: q.id,
    number: String(q.number),
    page: q.page == null ? '' : String(q.page),
    answer_type: q.answer_type,
    choice_count: q.choice_count == null ? '' : String(q.choice_count),
    correct_answer: q.correct_answer || '',
    accepted_answers: (q.accepted_answers || []).join(', '),
    points: String(q.points),
    unit_tag: q.unit_tag || '',
    explanation: q.explanation || '',
  }));
  if (!app.rows.length) addRow();

  // 既に提出された答案があるか (正解を変えると過去の採点と食い違う)
  const at = await sb().from('attempts').select('id, submitted_at').eq('book_id', book.id);
  app.submitted = (at.data || []).filter((a) => a.submitted_at).length;
  $('#ed-warn').hidden = app.submitted === 0;
  if (app.submitted) {
    $('#ed-warn').textContent =
      `この冊子は既に ${app.submitted} 件提出されています。正解を変えても`
      + '**過去の採点はやり直されません**（提出時に確定して保存されているため）。'
      + '直すなら、先生の方で該当の生徒に伝えてください。';
  }
  renderRows();
  $('#editor').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function addRow() {
  const max = app.rows.reduce((m, r) => Math.max(m, Number(r.number) || 0), 0);
  app.rows.push({
    id: null, number: String(max + 1), page: '', answer_type: 'choice',
    choice_count: '4', correct_answer: '', accepted_answers: '',
    points: '1', unit_tag: '', explanation: '',
  });
}

const FIELDS = [
  { k: 'number', label: '番号', w: '4.5em', type: 'number' },
  { k: 'page', label: 'ページ', w: '5em', type: 'number' },
  { k: 'answer_type', label: '形式', w: '7em', type: 'select', options: ANSWER_TYPES },
  { k: 'choice_count', label: '選択肢', w: '5em', type: 'number' },
  { k: 'correct_answer', label: '正解', w: '9em', type: 'text' },
  { k: 'accepted_answers', label: '別解 (,区切り)', w: '11em', type: 'text' },
  { k: 'points', label: '配点', w: '4.5em', type: 'number' },
  { k: 'unit_tag', label: '単元', w: '7em', type: 'text' },
];

function renderRows() {
  const host = $('#q-rows');
  host.innerHTML = '';

  const head = el('div', 'qhead');
  for (const f of FIELDS) {
    const c = el('div', 'qcell', f.label);
    c.style.width = f.w;
    head.appendChild(c);
  }
  head.appendChild(el('div', 'qcell grow', '解説'));
  host.appendChild(head);

  app.rows.forEach((row, i) => {
    const line = el('div', 'qrow');
    line.dataset.i = String(i);
    for (const f of FIELDS) {
      const cell = el('div', 'qcell');
      cell.style.width = f.w;
      let input;
      if (f.type === 'select') {
        input = document.createElement('select');
        for (const o of f.options) {
          const op = document.createElement('option');
          op.value = o.value; op.textContent = o.label;
          input.appendChild(op);
        }
        input.value = row[f.k];
      } else {
        input = document.createElement('input');
        input.type = f.type === 'number' ? 'text' : 'text';   // iOS の数字化けを避ける
        input.inputMode = f.type === 'number' ? 'numeric' : 'text';
        input.value = row[f.k];
        input.autocapitalize = 'off';
        input.setAttribute('autocorrect', 'off');
        input.spellcheck = false;
      }
      input.dataset.k = f.k;
      input.addEventListener('input', () => { row[f.k] = input.value; markDirty(); });
      input.addEventListener('change', () => {
        row[f.k] = input.value;
        if (f.k === 'answer_type') renderRows();     // 形式で使う欄が変わる
        markDirty();
      });
      // 記述では選択肢の数を使わない / 選択式では別解を使わない
      if (f.k === 'choice_count' && row.answer_type === 'short') input.disabled = true;
      if (f.k === 'accepted_answers' && row.answer_type === 'choice') input.disabled = true;
      cell.appendChild(input);
      line.appendChild(cell);
    }
    const ex = el('div', 'qcell grow');
    const ta = document.createElement('textarea');
    ta.rows = 1;
    ta.value = row.explanation;
    ta.placeholder = '解説 (任意)';
    ta.addEventListener('input', () => { row.explanation = ta.value; markDirty(); });
    ex.appendChild(ta);
    line.appendChild(ex);

    const err = el('div', 'qerr');
    line.appendChild(err);
    host.appendChild(line);
  });

  $('#q-count').textContent = `${app.rows.length} 問 / 合計 `
    + `${app.rows.reduce((s, r) => s + (Number(r.points) || 0), 0)} 点`;
}

let dirty = false;
function markDirty() { dirty = true; $('#q-save').classList.add('todo'); }

function showErrors(errors) {
  for (const e of document.querySelectorAll('.qerr')) { e.textContent = ''; e.hidden = true; }
  for (const inp of document.querySelectorAll('.qrow [data-k]')) inp.classList.remove('bad');
  const byRow = new Map();
  for (const er of errors) {
    if (er.i < 0) { say(er.msg, 'bad'); continue; }
    if (!byRow.has(er.i)) byRow.set(er.i, []);
    byRow.get(er.i).push(er.msg);
    const inp = document.querySelector(`.qrow[data-i="${er.i}"] [data-k="${er.field}"]`);
    if (inp) inp.classList.add('bad');
  }
  for (const [i, msgs] of byRow) {
    const box = document.querySelector(`.qrow[data-i="${i}"] .qerr`);
    if (box) { box.textContent = `${i + 1} 行目: ${msgs.join(' / ')}`; box.hidden = false; }
  }
}

async function saveQuestions() {
  if (!app.current) return;
  const btn = $('#q-save');
  const norm = app.rows.map(normalizeQuestion);
  const v = validateQuestions(norm, { pageCount: app.current.page_count });
  showErrors(v.errors);
  if (!v.ok) {
    say(`${v.errors.length} 件おかしいところがあります。赤い欄を直してください`, 'bad');
    return;
  }

  btn.disabled = true;
  say('保存しています…');
  let created = 0, updated = 0;
  try {
    for (const q of norm) {
      const payload = questionPayload(q, app.current.id);
      if (q.id) {
        const r = await sb().from('questions').update(payload).eq('id', q.id).select('id');
        if (r.error) throw new Error(`問 ${q.number}: ${r.error.message}`);
        if (!r.data.length) throw new Error(`問 ${q.number}: 更新できませんでした (権限がありません)`);
        updated++;
      } else {
        const r = await sb().from('questions').insert(payload).select('id');
        if (r.error) throw new Error(`問 ${q.number}: ${r.error.message}`);
        if (!r.data.length) throw new Error(`問 ${q.number}: 追加できませんでした`);
        q.id = r.data[0].id;
        created++;
      }
    }
    // 画面の行に id を戻す (次の保存で二重登録しないように)
    norm.forEach((q, i) => { app.rows[i].id = q.id; });
    dirty = false;
    btn.classList.remove('todo');
    say(`保存しました (追加 ${created} / 更新 ${updated})`, 'ok');
    await loadBooks();
  } catch (e) {
    say(`保存できませんでした — ${(e && e.message) || e}`, 'bad');
  } finally {
    btn.disabled = false;
  }
}

window.addEventListener('beforeunload', (e) => {
  if (dirty) { e.preventDefault(); e.returnValue = ''; }
});

// =============================================================================
boot().catch((e) => fatal('起動できませんでした', (e && e.message) || String(e)));
