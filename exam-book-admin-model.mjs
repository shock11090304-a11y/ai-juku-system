// =============================================================================
// 先生用の冊子登録 — 入力の検証 (純関数だけ)
//
// ★ このファイルは DOM も Supabase も触らない。node からそのまま import できるので
//   ゲート (scripts/book_exam/) が **実物を** 検査する。
//
// ★ ここが崩れると **その冊子を解いた生徒が全員 0 点になる**。しかもそれを
//   落とす仕組みは他に無い:
//     ・採点 RPC は correct_answer と突き合わせるだけで、値の妥当性を見ない
//     ・DB の CHECK は形は見るが「1 起算か」までは分からない
//       (choice_count=4 で correct_answer='0' は CHECK を通らないが、
//        '1' と '4' のどちらが正しいかは DB には判断できない)
//   だから **入力の時点で弾く** しかない。
//
// ★ DB の CHECK (question_answer_is_valid) より **こちらを厳しく**しておく。
//   壊れたものを送らないのがクライアントの責任。
// =============================================================================

// ★ DB 側の CHECK (supabase/migrations/…_books_subject_widen.sql) と必ず揃える。
//   片方だけ足すと、画面では選べるのに保存で 23514 になる。
export const SUBJECTS = Object.freeze([
  { value: 'grammar',  label: '英文法' },
  { value: 'reading',  label: '長文読解' },
  { value: 'eiken',    label: '英検' },
  { value: 'mock',     label: '模試' },
  { value: 'math',     label: '数学' },
  { value: 'japanese', label: '国語 (現代文・古文・漢文)' },
  { value: 'science',  label: '理科' },
  { value: 'social',   label: '社会' },
  { value: 'other',    label: 'その他' },
]);

export const ANSWER_TYPES = Object.freeze([
  { value: 'choice', label: '選択式' },
  { value: 'short',  label: '記述' },
]);

/** バケットの上限 (supabase/migrations/…_storage.sql と揃える) */
export const MAX_PDF_BYTES = 52428800;      // 50MB
export const MIN_CHOICES = 2;
export const MAX_CHOICES = 10;

const isInt = (v) => Number.isInteger(v);
const trim = (v) => (v == null ? '' : String(v).trim());

/** "a, b ,, c" → ['a','b','c'] (空要素は落とす。DB が NULL 要素を禁止しているため) */
export function parseAccepted(text) {
  return trim(text).split(',').map((x) => x.trim()).filter((x) => x !== '');
}

/** 入力欄の文字列を DB に入れる形へ。★数値は必ずここで数値にする。 */
export function normalizeQuestion(row) {
  const type = trim(row.answer_type) === 'short' ? 'short' : 'choice';
  const num = trim(row.number);
  const page = trim(row.page);
  const cc = trim(row.choice_count);
  const pts = trim(row.points);
  return {
    id: row.id || null,
    number: num === '' ? null : Number(num),
    page: page === '' ? null : Number(page),
    answer_type: type,
    choice_count: type === 'choice' ? (cc === '' ? null : Number(cc)) : null,
    correct_answer: trim(row.correct_answer),
    accepted_answers: type === 'short' ? parseAccepted(row.accepted_answers) : [],
    points: pts === '' ? 1 : Number(pts),
    unit_tag: trim(row.unit_tag) || null,
    explanation: row.explanation == null ? null : (String(row.explanation).trim() || null),
  };
}

/**
 * 設問の検証。**保存の直前に必ず通す。**
 * @param {Array} rows normalizeQuestion を通したもの
 * @param {{pageCount:number|null}} opt PDF の実ページ数 (分かっていれば範囲を見る)
 * @returns {{ok:boolean, errors:Array<{i:number, field:string, msg:string}>}}
 */
export function validateQuestions(rows, opt = {}) {
  const errors = [];
  const bad = (i, field, msg) => errors.push({ i, field, msg });
  if (!Array.isArray(rows) || rows.length === 0) {
    return { ok: false, errors: [{ i: -1, field: '', msg: '設問が 1 問もありません' }] };
  }
  const pageCount = Number.isFinite(opt.pageCount) ? opt.pageCount : null;
  const seen = new Map();

  rows.forEach((q, i) => {
    // --- 番号 ---------------------------------------------------------------
    if (q.number == null || !isInt(q.number) || q.number < 1) {
      bad(i, 'number', '番号は 1 以上の整数にしてください');
    } else if (seen.has(q.number)) {
      bad(i, 'number', `番号 ${q.number} が ${seen.get(q.number) + 1} 行目と重複しています`);
    } else {
      seen.set(q.number, i);
    }

    // --- ページ -------------------------------------------------------------
    if (q.page != null) {
      if (!isInt(q.page) || q.page < 1) {
        bad(i, 'page', 'ページは 1 以上の整数か、空にしてください');
      } else if (pageCount != null && q.page > pageCount) {
        bad(i, 'page', `この冊子は ${pageCount} ページまでです`);
      }
    }

    // --- 配点 ---------------------------------------------------------------
    if (!isInt(q.points) || q.points < 1) {
      bad(i, 'points', '配点は 1 以上の整数にしてください');
    }

    // --- 正解 ---------------------------------------------------------------
    if (q.correct_answer === '') {
      bad(i, 'correct_answer', '正解を入れてください');
    }

    if (q.answer_type === 'choice') {
      if (!isInt(q.choice_count) || q.choice_count < MIN_CHOICES || q.choice_count > MAX_CHOICES) {
        bad(i, 'choice_count', `選択肢の数は ${MIN_CHOICES}〜${MAX_CHOICES} にしてください`);
      }
      // ★ ここが「全員 0 点」を止める最後の砦。
      //   受験画面は選択肢を 1 起算の数字文字列で保存する (choiceValue)。
      //   0 起算や 'A' や '①' を入れると、生徒が正しく選んでも一致しない。
      if (q.correct_answer !== '') {
        if (!/^[1-9][0-9]?$/.test(q.correct_answer)) {
          bad(i, 'correct_answer',
              '選択式の正解は「1」「2」… の数字で入れてください (0 起算や A・① は不可)');
        } else if (isInt(q.choice_count)) {
          const n = Number(q.correct_answer);
          if (n < 1 || n > q.choice_count) {
            bad(i, 'correct_answer', `1〜${q.choice_count} の範囲で入れてください`);
          }
        }
      }
      if (q.accepted_answers && q.accepted_answers.length) {
        bad(i, 'accepted_answers', '別解は記述のときだけ使えます');
      }
    } else {
      if (q.choice_count != null) {
        bad(i, 'choice_count', '記述では選択肢の数を空にしてください');
      }
      // ★ 記述の正解に数字だけを入れると、選択式と取り違えている可能性が高い。
      //   採点は文字列一致なので「3」と答えないと当たらない。念のため知らせる。
      if (/^[0-9]+$/.test(q.correct_answer)) {
        bad(i, 'correct_answer',
            '記述の正解が数字だけです。選択式にするつもりではありませんか');
      }
      for (const a of q.accepted_answers || []) {
        if (a.trim() === '') bad(i, 'accepted_answers', '別解に空のものが混ざっています');
      }
    }
  });

  return { ok: errors.length === 0, errors };
}

/** DB に送る列だけを組み立てる。★行オブジェクトをそのまま渡さない。 */
export function questionPayload(q, bookId) {
  return {
    book_id: bookId,
    number: q.number,
    page: q.page,
    answer_type: q.answer_type,
    choice_count: q.choice_count,
    correct_answer: q.correct_answer,
    accepted_answers: (q.answer_type === 'short' && q.accepted_answers.length)
      ? q.accepted_answers : null,
    points: q.points,
    unit_tag: q.unit_tag,
    explanation: q.explanation,
  };
}

/**
 * 冊子そのものの検証。
 * @returns {{ok:boolean, errors:string[]}}
 */
export function validateBook(book) {
  const errors = [];
  if (trim(book.title) === '') errors.push('タイトルを入れてください');
  if (!SUBJECTS.some((s) => s.value === book.subject)) errors.push('科目を選んでください');
  if (book.time_limit_sec != null) {
    if (!isInt(book.time_limit_sec) || book.time_limit_sec < 1) {
      errors.push('制限時間は 1 分以上か、空 (無制限) にしてください');
    }
  }
  return { ok: errors.length === 0, errors };
}

/**
 * アップロードする PDF の検査。**送る前に落とす。**
 * @param {{name:string, size:number, type:string}} file
 * @returns {{ok:boolean, reason:string|null}}
 */
export function checkPdfFile(file) {
  if (!file) return { ok: false, reason: 'ファイルが選ばれていません' };
  if (file.size > MAX_PDF_BYTES) {
    return { ok: false,
             reason: `${(file.size / 1048576).toFixed(1)}MB あります。`
                   + `上限は ${MAX_PDF_BYTES / 1048576}MB です` };
  }
  if (file.size === 0) return { ok: false, reason: '中身が空です' };
  const okType = file.type === 'application/pdf' || /\.pdf$/i.test(file.name || '');
  if (!okType) return { ok: false, reason: 'PDF ではありません' };
  return { ok: true, reason: null };
}

/**
 * Storage に置くパス。
 * ★ 元のファイル名をそのまま使わない。日本語・空白・記号が入ると署名付き URL の
 *   組み立てで壊れる経路があるうえ、**ファイル名から中身が推測できる**
 *   (未公開の模試名が一覧 API で見えてしまう)。id ベースの機械的な名前にする。
 */
export function pdfPath(bookId) {
  return `books/${bookId}.pdf`;
}


// =============================================================================
// 一括取り込み (scripts/book_exam/convert_workbook.py が吐く JSON)
// =============================================================================
/**
 * 取り込む JSON を画面の行の形へ。**検証はしない** (呼び出し側が
 * normalizeQuestion → validateQuestions を通す。検証器を 2 つ持たない)。
 * @returns {{ok:boolean, rows:Array, book:object|null, preview:Array, reason:string|null}}
 */
export function parseImport(text) {
  let data;
  try {
    data = JSON.parse(text);
  } catch (e) {
    return { ok: false, rows: [], book: null, preview: [], reason: 'JSON として読めません' };
  }
  const list = Array.isArray(data) ? data
    : (Array.isArray(data.questions) ? data.questions : null);
  if (!list) {
    return { ok: false, rows: [], book: null, preview: [],
             reason: 'questions の配列が見つかりません' };
  }
  if (!list.length) {
    return { ok: false, rows: [], book: null, preview: [], reason: '設問が 0 件です' };
  }

  const rows = list.map((q, i) => ({
    id: null,                                   // ★ 取り込みは必ず新規 (既存を書き換えない)
    number: String(q.number != null ? q.number : i + 1),
    page: q.page == null ? '' : String(q.page),
    answer_type: q.answer_type === 'short' ? 'short' : 'choice',
    choice_count: q.choice_count == null ? '' : String(q.choice_count),
    correct_answer: q.correct_answer == null ? '' : String(q.correct_answer),
    accepted_answers: Array.isArray(q.accepted_answers) ? q.accepted_answers.join(', ')
                                                        : String(q.accepted_answers || ''),
    points: String(q.points == null ? 1 : q.points),
    unit_tag: q.unit_tag == null ? '' : String(q.unit_tag),
    explanation: q.explanation == null ? '' : String(q.explanation),
  }));

  return {
    ok: true, rows,
    book: (data && typeof data.book === 'object') ? data.book : null,
    // ★ 起算の確認用。機械では証明しきれないので、人が 1 件だけ実物と照合する。
    preview: Array.isArray(data && data.preview) ? data.preview.slice(0, 3) : [],
    reason: null,
  };
}
