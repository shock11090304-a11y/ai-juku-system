// =============================================================================
// 先生用の登録画面が作る設問データを、意地の悪い入力から **実際に生成** して出す。
// check_book_exam.py が使い捨て Postgres の question_answer_is_valid() に食わせ、
//     「画面が通すもの ⊆ DB が受け取るもの」
// を確かめる。崩れると「登録できたのに保存で弾かれる」か、もっと悪い
// 「保存できたのに全員 0 点」になる。
//
// ★ 写経しない。**実物の exam-book-admin-model.mjs** を import する。
// =============================================================================
import { normalizeQuestion, validateQuestions, questionPayload }
  from '../../exam-book-admin-model.mjs';

const PAGES = 4;   // 検査用の冊子は 4 ページという想定

// [名前, 入力欄に打たれた文字列]
const CASES = [
  ['まっとうな 4 択', { number: '1', page: '1', answer_type: 'choice', choice_count: '4',
                       correct_answer: '3', points: '1' }],
  ['まっとうな記述', { number: '2', page: '2', answer_type: 'short', choice_count: '',
                      correct_answer: 'could', accepted_answers: 'could speak, was able to',
                      points: '2' }],
  ['ページ空 (指定なし)', { number: '3', page: '', answer_type: 'choice', choice_count: '2',
                           correct_answer: '2', points: '1' }],
  ['選択肢 10 個の上限', { number: '4', page: '4', answer_type: 'choice', choice_count: '10',
                          correct_answer: '10', points: '3' }],
  ['前後に空白', { number: ' 5 ', page: ' 1 ', answer_type: 'choice', choice_count: ' 4 ',
                  correct_answer: ' 2 ', points: ' 1 ' }],
  ['解説つき', { number: '6', page: '1', answer_type: 'choice', choice_count: '4',
                correct_answer: '1', points: '1', explanation: '## 🎯 コアイメージ\n本文どおり' }],
  ['別解に空が混ざる', { number: '7', page: '2', answer_type: 'short', correct_answer: 'rain',
                        accepted_answers: 'rains, , raining, ', points: '1' }],
  ['単元タグつき', { number: '8', page: '3', answer_type: 'short', correct_answer: 'went',
                    points: '1', unit_tag: 'SUBJ-01' }],

  // --- ここから弾かれるべきもの -------------------------------------------
  ['★0 起算の正解', { number: '9', page: '1', answer_type: 'choice', choice_count: '4',
                     correct_answer: '0', points: '1' }],
  ['★アルファベットの正解', { number: '10', page: '1', answer_type: 'choice', choice_count: '4',
                             correct_answer: 'C', points: '1' }],
  ['★丸数字の正解', { number: '11', page: '1', answer_type: 'choice', choice_count: '4',
                     correct_answer: '③', points: '1' }],
  ['★全角数字の正解', { number: '12', page: '1', answer_type: 'choice', choice_count: '4',
                       correct_answer: '３', points: '1' }],
  // ★ 先頭ゼロ。範囲チェック (Number('03')=3) は通ってしまうので、
  //   形の検査 (^[1-9][0-9]?$) だけが止められる。DB 側も同じ形で弾く。
  ['★先頭ゼロの正解', { number: '25', page: '1', answer_type: 'choice', choice_count: '4',
                       correct_answer: '03', points: '1' }],
  ['★選択肢の数を超える正解', { number: '13', page: '1', answer_type: 'choice',
                               choice_count: '4', correct_answer: '5', points: '1' }],
  ['★選択肢が 1 個', { number: '14', page: '1', answer_type: 'choice', choice_count: '1',
                      correct_answer: '1', points: '1' }],
  ['★選択肢が 11 個', { number: '15', page: '1', answer_type: 'choice', choice_count: '11',
                       correct_answer: '11', points: '1' }],
  ['★正解が空', { number: '16', page: '1', answer_type: 'choice', choice_count: '4',
                 correct_answer: '', points: '1' }],
  ['★正解が空白だけ', { number: '17', page: '1', answer_type: 'short',
                       correct_answer: '   ', points: '1' }],
  // ↓ 通るのが正解。normalizeQuestion が DB の形 (記述なら choice_count は NULL) に揃える
  ['記述に切り替えたら選択肢の数は捨てられる', { number: '18', page: '1', answer_type: 'short',
                                              choice_count: '4', correct_answer: 'apple', points: '1' }],
  ['★記述の正解が数字だけ (取り違え)', { number: '19', page: '1', answer_type: 'short',
                                       correct_answer: '3', points: '1' }],
  // ↓ 同上。選択式に切り替えたら別解は捨てられる (DB は choice に別解を持たせない)
  ['選択式に切り替えたら別解は捨てられる', { number: '20', page: '1', answer_type: 'choice',
                                          choice_count: '4', correct_answer: '2',
                                          accepted_answers: 'x', points: '1' }],
  ['★配点 0', { number: '21', page: '1', answer_type: 'choice', choice_count: '4',
               correct_answer: '2', points: '0' }],
  ['★配点が小数', { number: '22', page: '1', answer_type: 'choice', choice_count: '4',
                   correct_answer: '2', points: '1.5' }],
  ['★番号 0', { number: '0', page: '1', answer_type: 'choice', choice_count: '4',
               correct_answer: '2', points: '1' }],
  ['★番号が小数', { number: '1.5', page: '1', answer_type: 'choice', choice_count: '4',
                   correct_answer: '2', points: '1' }],
  ['★番号が空', { number: '', page: '1', answer_type: 'choice', choice_count: '4',
                 correct_answer: '2', points: '1' }],
  ['★ページが冊子より後ろ', { number: '23', page: '99', answer_type: 'choice',
                             choice_count: '4', correct_answer: '2', points: '1' }],
  ['★ページ 0', { number: '24', page: '0', answer_type: 'choice', choice_count: '4',
                 correct_answer: '2', points: '1' }],
  ['★番号が数字でない', { number: 'あ', page: '1', answer_type: 'choice', choice_count: '4',
                         correct_answer: '2', points: '1' }],
];

const out = [];
for (const [name, raw] of CASES) {
  const q = normalizeQuestion(raw);
  // 1 件ずつ検査する (重複判定を混ぜないため)
  const v = validateQuestions([q], { pageCount: PAGES });
  out.push({
    kind: 'question', name, accepted: v.ok,
    reasons: v.errors.map((e) => `${e.field}:${e.msg}`),
    payload: v.ok ? questionPayload(q, 'deadbeef-cafe-4bad-8fed-0123456789ab') : null,
  });
}

// 番号の重複は 2 件そろって初めて分かるので別に見る
{
  const rows = [
    normalizeQuestion({ number: '1', page: '1', answer_type: 'choice', choice_count: '4',
                        correct_answer: '1', points: '1' }),
    normalizeQuestion({ number: '1', page: '2', answer_type: 'choice', choice_count: '4',
                        correct_answer: '2', points: '1' }),
  ];
  const v = validateQuestions(rows, { pageCount: PAGES });
  out.push({ kind: 'question', name: '★番号の重複', accepted: v.ok,
             reasons: v.errors.map((e) => `${e.field}:${e.msg}`), payload: null });
}
// ★ normalizeQuestion を通さず validateQuestions に直接渡す。
//   上の 2 件は normalize が形を揃えてしまうので、検証側の分岐がそこでは通らない。
//   一括取込など normalize を経ない経路のために、分岐が生きていることをここで確かめる。
{
  const direct = [
    ['★(直接) 記述なのに choice_count がある',
     { id: null, number: 1, page: 1, answer_type: 'short', choice_count: 4,
       correct_answer: 'apple', accepted_answers: [], points: 1, unit_tag: null,
       explanation: null }],
    ['★(直接) 選択式なのに別解がある',
     { id: null, number: 1, page: 1, answer_type: 'choice', choice_count: 4,
       correct_answer: '2', accepted_answers: ['x'], points: 1, unit_tag: null,
       explanation: null }],
    ['★(直接) 別解に空文字が残っている',
     { id: null, number: 1, page: 1, answer_type: 'short', choice_count: null,
       correct_answer: 'rain', accepted_answers: ['rains', '  '], points: 1,
       unit_tag: null, explanation: null }],
  ];
  for (const [name, q] of direct) {
    const v = validateQuestions([q], { pageCount: PAGES });
    out.push({ kind: 'question', name, accepted: v.ok,
               reasons: v.errors.map((e) => `${e.field}:${e.msg}`), payload: null });
  }
}

// 設問が 0 件
{
  const v = validateQuestions([], { pageCount: PAGES });
  out.push({ kind: 'question', name: '★設問が 0 件', accepted: v.ok,
             reasons: v.errors.map((e) => e.msg), payload: null });
}

for (const r of out) console.log(JSON.stringify(r));
