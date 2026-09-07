// 🏦 塾月謝アプリ 銀行明細取込の純粋関数テスト (jsc / node で実行。DOM 不要)。
//   payment/app.js から NOISE_PATTERNS〜matchPayer と parseEnrollmentApp を抜き出して実行する。
//   実行: jsc scripts/health_check/payment_import_logic.test.js  (または node)
const fs = (typeof require === 'function') ? require('fs') : null;
const src = fs ? fs.readFileSync(__dirname + '/../../payment/app.js', 'utf8') : readFile('payment/app.js');
function fn(name) {
  const m = src.match(new RegExp('\\n(?:async )?function ' + name + '\\('));
  if (!m) throw new Error('function not found: ' + name);
  const s = m.index + 1; const e = src.indexOf('\n}\n', s) + 3;
  return src.slice(s, e);
}
function block(startMarker, endMarker) { return src.slice(src.indexOf(startMarker), src.indexOf(endMarker)); }
const core = block('const NOISE_PATTERNS = [', 'function parseCSVText(');
let pre = '';
for (const c of ['HW_KANA_MAP', 'DAKUTEN', 'HANDAKUTEN', 'KANJI_VARIANTS']) {
  if (core.indexOf('const ' + c + ' =') >= 0) continue;   // 抜き出した範囲に含まれていれば二重定義しない
  const i = src.indexOf('const ' + c + ' ='); const j = src.indexOf('\n};', i) + 3;
  pre += src.slice(i, j) + '\n';
}
const stubs = `
const STATE = { currentMonth: '2026-09', overrides: { payerNames: { 5: 'ヤマダ ハナコ' }, payments: {} }, data: { students: [
  { id: 5, name: '山田 花子', status: '通塾', fee: 7500 }, { id: 6, name: '佐藤 太郎', status: '通塾', fee: 13500 }, { id: 7, name: '退塾 生', status: '退塾', fee: 9000 } ] } };
function activeStudents() { return STATE.data.students.filter(s => s.status === '通塾'); }
const document = { getElementById: () => null };
`;
const tests = `
const R = [];
const ok = (label, cond, detail) => { R.push((cond ? '✅ ' : '❌ ') + label + (cond ? '' : ' — ' + JSON.stringify(detail))); };
ok('Stripe 入金 (全角) はノイズ', isNoise('TRILLION ストライプジャパン（カ') === true);
ok('Stripe 入金 (半角カナ) もノイズ', isNoise('TRILLION ｽﾄﾗｲﾌﾟｼﾞｬﾊﾟﾝ(ｶ') === true);
ok('普通の振込人はノイズでない', isNoise('ヤマダ ハナコ') === false && isNoise('センダ ヒサコ 塾') === false);
ok('末尾の「塾」を無視して正規化', normalizeName('ヤマダ ハナコ 塾') === normalizeName('ヤマダハナコ'));
const m1 = matchPayer('ヤマダ ハナコ 塾', 8850);
ok('学習済の振込人名 + 末尾「塾」でも learned 100', m1.length && m1[0].confidence === 'learned' && m1[0].studentId === 5, m1);
const note = '■きっかけ: Instagram\\n■申込日: 2026-09-05\\n■保護者: 山田 花子(ヤマダ ハナコ) 続柄:母\\n■金額: 受講料 8500円 / 毎月 9850円 / 初月 19850円\\n';
const p1 = parseEnrollmentApp({ note });
ok('申込書: 保護者フリガナ (括弧内) を振込人名に', p1.payerName === 'ヤマダ ハナコ', p1);
ok('申込書: 受講料/毎月/初月 を読む', p1.fee === 8500 && p1.monthlyTotal === 9850 && p1.firstMonthFee === 19850, p1);
const p2 = parseEnrollmentApp({ note: note.replace('山田 花子(ヤマダ ハナコ)', 'ヤマダハナコ(山田花子)') });
ok('申込書: 氏名とフリガナが逆でもカナ側を採用', p2.payerName === 'ヤマダハナコ', p2);
const p3 = parseEnrollmentApp({ note: note.replace('山田 花子(ヤマダ ハナコ)', '山田 花子(山田花子)') });
ok('申込書: どちらもカナでなければ空', p3.payerName === '', p3);
ok('初月らしい金額 (18,850 = 7,500 + 11,350)', looksLikeFirstMonth(18850) === true);
ok('毎月合計 (8,850 = 名簿 7,500 + 1,350) は初月扱いしない', looksLikeFirstMonth(8850) === false);
ok('端数の金額 (21,092) は初月扱いしない', looksLikeFirstMonth(21092) === false);
ok('candidateMonth: 既定は翌月分、当月分を選ぶと入金月', candidateMonth({ month: '2026-10', calMonth: '2026-09', monthMode: 'next' }) === '2026-10' && candidateMonth({ month: '2026-10', calMonth: '2026-09', monthMode: 'current' }) === '2026-09');
const out = R.join('\\n');
if (typeof console !== 'undefined' && console.log) console.log(out); else print(out);
if (R.some(x => x.startsWith('❌'))) { if (typeof process !== 'undefined') process.exit(1); throw new Error('FAIL'); }
`;
const program = pre + stubs + core + '\n' + fn('parseEnrollmentApp') + '\n' + tests;
(0, eval)(program);
