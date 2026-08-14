// =============================================================================
// 冊子受験画面 — 実ブラウザでの通し確認 (check_exam_book_browser.py から呼ばれる)
//
//   node browser_smoke.mjs <repoRoot> <fixtureDir>
//
// ★ 差し替えるのは **接続設定と supabase-js の 2 本だけ**。
//   exam-book*.mjs / pdf.js / CSS / HTML は **配信するものそのもの**を読ませる。
//   ここを写経したりモックに寄せたりすると、本物が壊れても緑になる。
//
// ★ 偽 Supabase は updated_at の CAS と提出後の 42501 を本物と同じ意味で返す。
//   「保存が通ったつもりで 0 行」「提出後に書けてしまう」をここで捕まえるため。
// =============================================================================
import { createRequire } from 'node:module';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

// ★ ESM の import は NODE_PATH を見ない。playwright-core はリポジトリの依存ではなく
//   「あれば回す」ものなので、CJS の解決 (NODE_PATH を見る) で拾う。
const { chromium } = createRequire(import.meta.url)('playwright-core');

const ROOT = process.argv[2];
const FIX = process.argv[3];
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.mjs': 'text/javascript',
  '.js': 'text/javascript', '.json': 'application/json', '.pdf': 'application/pdf',
  '.bcmap': 'application/octet-stream' };

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const p = path.join(ROOT, u);
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) {
    res.writeHead(404); res.end('nf'); return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;

const results = [];
const ok = (n, c, extra = '') => {
  results.push({ n, c: !!c, extra });
  console.log(`${c ? '  ✓' : '  ✗'} ${n}${c || !extra ? '' : ` — ${extra}`}`);
};

const browser = await chromium.launch({ executablePath: process.env.CHROME_BIN, args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
page.setDefaultTimeout(15000);
// ★ 何があっても止まらない。ハングは「検査していない」と同じ。
const watchdog = setTimeout(() => {
  console.log('  ✗ 制限時間 (200 秒) を超えた — どこかで止まっている');
  process.exit(1);
}, 200000);

const errors = [];
const isFavicon = (u) => String(u || '').endsWith('/favicon.ico');
page.on('pageerror', (e) => errors.push(String(e)));
page.on('console', (m) => {
  const loc = m.location && m.location();
  if (m.type() === 'error' && !isFavicon(loc && loc.url)) errors.push('console: ' + m.text());
});
page.on('requestfailed', (r) => { if (!isFavicon(r.url())) errors.push('reqfail: ' + r.url()); });
page.on('response', (r) => {
  if (r.status() >= 400 && !isFavicon(r.url())) errors.push(`http ${r.status()}: ${r.url()}`);
});

// 差し替えるのは 2 本だけ。それ以外は **本物のファイル**を読ませる。
await page.route('**/exam-book-config.mjs*', (r) => r.fulfill({
  contentType: 'text/javascript',
  body: "export const SUPABASE = { url: 'https://x.supabase.co', anonKey: 'test' };\n"
      + 'export function assertAnonKey() {}\n',
}));
await page.route('**/vendor/supabase-js/supabase.mjs*', (r) => r.fulfill({
  contentType: 'text/javascript',
  body: fs.readFileSync(path.join(FIX, 'mock_supabase.mjs'), 'utf8'),
}));
await page.route('**/__pdf/**', (r) => r.fulfill({
  contentType: 'application/pdf', body: fs.readFileSync(path.join(FIX, 'book.pdf')),
}));

await page.goto(`${base}/exam-book.html`, { waitUntil: 'domcontentloaded' });
try {

// --- 起動 ---------------------------------------------------------------------
try {
  await page.waitForSelector('body[data-stage="ready"]', { timeout: 25000 });
  ok('起動して受験できる状態になる', true);
} catch (e) {
  const t = await page.textContent('#fatal-title').catch(() => '');
  const d = await page.textContent('#fatal-detail').catch(() => '');
  ok('起動して受験できる状態になる', false, `${t} / ${d}`);
}

const st = () => page.evaluate(() => globalThis.__DB);

// --- ページ枠 -----------------------------------------------------------------
const pages = await page.$$('#viewer .page');
ok('ページ枠が 2 枚できる', pages.length === 2, `実際 ${pages.length}`);
const ar = await page.evaluate(() =>
  [...document.querySelectorAll('#viewer .page')].map((e) => e.style.aspectRatio));
// ★ 「数字 / 数字 の形か」だけ見ると、仮寸 (1 / 1.414) でも通ってしまう。
//   検査用 PDF の実寸 595x842 と一致するかまで見る。
const WANT = 595 / 842;
// ★ 許容差は 1e-4。よくある仮寸 1/1.414 は 595/842 と 5.6e-4 しか違わないので、
//   1e-3 だと仮寸のまま通ってしまう (実際に見逃した)。
ok('aspect-ratio が PDF の実寸と一致する (仮寸で作っていない)',
  ar.length === 2 && ar.every((a) => {
    const m = /^([\d.]+)\s*\/\s*([\d.]+)$/.exec(a);
    return m && Math.abs(Number(m[1]) / Number(m[2]) - WANT) < 1e-4;
  }), JSON.stringify(ar));

const painted = await page.evaluate(async () => {
  await new Promise((r) => setTimeout(r, 1200));
  const cv = document.querySelector('#viewer .page canvas.pdf');
  const c = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
  let nonWhite = 0;
  for (let i = 0; i < c.length; i += 4 * 97) if (c[i] < 240) nonWhite++;
  return { w: cv.width, h: cv.height, nonWhite };
});
ok('PDF が実際に描かれている (白紙でない)', painted.nonWhite > 0, JSON.stringify(painted));

// --- attempt ------------------------------------------------------------------
let db = await st();
ok('attempt は PDF を読み終えた後に 1 件だけ作られる', db.attempts.length === 1,
  `実際 ${db.attempts.length}`);
ok('answers 行が設問数ぶん先に作られる', db.answers.length === 3, `実際 ${db.answers.length}`);
const order = db.log.map((l) => `${l.t}:${l.op}`);
ok('attempts の insert より前に books の select がある',
  order.indexOf('attempts:insert') > order.indexOf('books:select'), order.join(' '));

// --- 答案 ---------------------------------------------------------------------
ok('page=NULL の設問が先頭グループに出る',
  await page.evaluate(() =>
    document.querySelector('.qgroup').dataset.page === 'none'
    && document.querySelector('.qgroup .q').dataset.number === '3'));

// ★ data-value で押すと「値が何であれ同じ値が保存される」ので必ず通ってしまう。
//   **何番目のピルか**で押して、保存されたのが 1 起算の番号かを見る。
await page.click('.q[data-number="1"] .choice:nth-of-type(2)');
await page.fill('.q[data-number="2"] input.short', 'apple');
await page.click('.q[data-number="3"] .choice:nth-of-type(1)');
await page.waitForTimeout(1200);
db = await st();
const byNum = (n) => db.answers.find((a) => a.question_id === `q${n}`);
ok('2 番目のピルが "2" として保存される (1 起算)', byNum(1).user_answer === '2',
  `実際 ${byNum(1).user_answer}`);
ok('1 番目のピルが "1" として保存される', byNum(3).user_answer === '1',
  `実際 ${byNum(3).user_answer}`);
ok('記述は入力どおり保存される', byNum(2).user_answer === 'apple', byNum(2).user_answer);
const upd = db.log.filter((l) => l.t === 'answers' && l.op === 'update');
ok('answers の update は 2 列だけ',
  upd.every((l) => Object.keys(l.payload).join() === 'user_answer,time_spent_sec'),
  JSON.stringify(upd[0] && upd[0].payload));
ok('進捗は自前で数えている',
  (await page.textContent('.ans-count')).includes('3 / 3'), await page.textContent('.ans-count'));

// --- 通信断のときに答案の再送が暴走しないか -----------------------------------
// ★ 失敗するたびに want へ戻すので、再帰に上限が無いと **バックオフ無しで叩き続け**、
//   提出手順の FLUSH_ANSWERS の await が永久に返らなくなる。回数で見る。
{
  const before = (await st()).log.filter((l) => l.t === 'answers' && l.op === 'update').length;
  await page.evaluate(() => { globalThis.__DB.offlineAnswers = true; });
  await page.fill('.q[data-number="2"] input.short', 'apple pie');
  await page.waitForTimeout(3000);
  const after = (await st()).log.filter((l) => l.t === 'answers' && l.op === 'update').length;
  ok('通信断でも答案の再送が暴走しない', after - before <= 4, `3 秒で ${after - before} 回`);
  ok('通信断のときは「未保存」を出し続ける',
    (await page.textContent('#saveState')).includes('未保存')
    || (await page.textContent('#banner')).includes('保存'),
    `${await page.textContent('#saveState')} / ${await page.textContent('#banner')}`);
  await page.evaluate(() => { globalThis.__DB.offlineAnswers = false; });
  await page.fill('.q[data-number="2"] input.short', 'apple');
  await page.click('.q[data-number="1"] .choice:nth-of-type(2)');   // blur させて確定
  await page.click('.q[data-number="1"] .choice:nth-of-type(2)');   // 押し直して元に戻す
  await page.waitForTimeout(1500);
  ok('復帰したら答案が保存される',
    (await st()).answers.find((a) => a.question_id === 'q2').user_answer === 'apple',
    (await st()).answers.find((a) => a.question_id === 'q2').user_answer);
}

// --- 手書き -------------------------------------------------------------------
await page.click('[data-mode="write"]');
ok('書くモードで touch-action が none になる',
  await page.evaluate(() => getComputedStyle(document.querySelector('#viewer')).touchAction) === 'none');

const box = await (await page.$('#viewer .page')).boundingBox();
// ★ 1 本指の touch は何も起こさない (手のひらで紙を押さえられること)
await page.evaluate((b) => {
  const v = document.querySelector('#viewer');
  const mk = (type, x, y) => new PointerEvent(type, { pointerId: 9, pointerType: 'touch',
    clientX: x, clientY: y, bubbles: true, cancelable: true });
  const el = document.elementFromPoint(b.x + 40, b.y + 40);
  el.dispatchEvent(mk('pointerdown', b.x + 40, b.y + 40));
  v.dispatchEvent(mk('pointermove', b.x + 120, b.y + 120));
  v.dispatchEvent(mk('pointerup', b.x + 120, b.y + 120));
}, box);
// ★ 300ms で見るとデバウンス (1.2 秒) の内側なので、線が引かれていても 0 件に見える。
//   保存まで待ってから数える。
await page.waitForTimeout(2200);
ok('1 本指タッチでは線を引かない (手のひら先着)', (await st()).annotations.length === 0,
  `実際 ${(await st()).annotations.length} 件`);

// ペンで書く
await page.mouse.move(box.x + 60, box.y + 60);
await page.mouse.down();
for (let i = 1; i <= 12; i++) await page.mouse.move(box.x + 60 + i * 14, box.y + 60 + i * 9);
await page.mouse.up();
await page.waitForTimeout(2200);

db = await st();
ok('手書きが 1 ページ分だけ保存される', db.annotations.length === 1,
  `実際 ${db.annotations.length}`);
const strokes = db.annotations[0] && db.annotations[0].strokes;
ok('保存形式が §5 ({v:1,strokes:[{c,w,p}]})',
  strokes && strokes.v === 1 && Array.isArray(strokes.strokes) && strokes.strokes.length === 1
  && ['c', 'w', 'p'].every((k) => k in strokes.strokes[0]), JSON.stringify(strokes).slice(0, 120));
const pts = strokes && strokes.strokes[0].p;
ok('座標が 0〜1 に正規化されている',
  pts && pts.every((q) => q[0] >= 0 && q[0] <= 1 && q[1] >= 0 && q[1] <= 1),
  JSON.stringify(pts && pts.slice(0, 3)));
ok('ローカル写しがサーバ保存後に消える',
  await page.evaluate(() => !Object.keys(localStorage).some((k) => /^ink:.*:\d+$/.test(k))),
  await page.evaluate(() => Object.keys(localStorage).join(',')));

// 2 本目を書いたら CAS で update になる
await page.mouse.move(box.x + 200, box.y + 300);
await page.mouse.down();
for (let i = 1; i <= 8; i++) await page.mouse.move(box.x + 200 + i * 10, box.y + 300 - i * 6);
await page.mouse.up();
await page.waitForTimeout(2200);
db = await st();
const annUpd = db.log.filter((l) => l.t === 'annotations' && l.op === 'update');
ok('2 回目は CAS つき update になる',
  annUpd.length >= 1 && annUpd[0].f.some(([c]) => c === 'updated_at'),
  JSON.stringify(annUpd[0] && annUpd[0].f));
ok('2 本目も同じページに積まれる', db.annotations[0].strokes.strokes.length === 2,
  String(db.annotations[0].strokes.strokes.length));

// 消しゴム + undo
await page.click('[data-tool="eraser"]');
await page.mouse.move(box.x + 60 + 6 * 14, box.y + 60 + 6 * 9);
await page.mouse.down();
await page.mouse.move(box.x + 60 + 6 * 14 + 2, box.y + 60 + 6 * 9 + 2);
await page.mouse.up();
await page.waitForTimeout(2200);
db = await st();
ok('消しゴムでストロークが 1 本減る', db.annotations[0].strokes.strokes.length === 1,
  String(db.annotations[0].strokes.strokes.length));
await page.click('[data-tool="undo"]');
await page.waitForTimeout(2200);
db = await st();
ok('戻すで復活する', db.annotations[0].strokes.strokes.length === 2,
  String(db.annotations[0].strokes.strokes.length));

// --- 提出 ---------------------------------------------------------------------
// ★ **保存が済む前に**提出する。DRAIN が予約を取り消すので、FLUSH_INK が無いと
//   この 1 本は永久に届かない。待ってから提出すると、その穴は必ず見逃す。
// ★ **通信断のまま**書いて、そのまま提出する (設計 §13-5 の「機内モードで書く」)。
//   保存が済んでから提出すると、FLUSH_INK が無くても通ってしまい穴を見逃す。
await page.evaluate(() => { globalThis.__DB.offline = true; });
await page.click('[data-pen="red"]');            // 消しゴムのままだと線が増えない
await page.mouse.move(box.x + 120, box.y + 420);
await page.mouse.down();
for (let i = 1; i <= 6; i++) await page.mouse.move(box.x + 120 + i * 12, box.y + 420 + i * 4);
await page.mouse.up();
await page.waitForTimeout(2500);                 // 送信に失敗してバックオフに入るまで待つ
db = await st();
ok('通信断の間はサーバに届かない (検査の前提)',
  db.annotations[0].strokes.strokes.length === 2,
  `実際 ${db.annotations[0].strokes.strokes.length} 本`);
ok('通信断のときは端末に控えが残る',
  await page.evaluate(() => Object.keys(localStorage).some((k) => /^ink:.*:1$/.test(k))),
  await page.evaluate(() => Object.keys(localStorage).join(',')));
ok('未保存が画面に出続ける',
  (await page.textContent('#saveState')).includes('未保存'),
  await page.textContent('#saveState'));
await page.evaluate(() => { globalThis.__DB.offline = false; });   // 復帰

page.on('dialog', (d) => d.accept());
await page.click('#submit');
await page.waitForSelector('#dialog[open]', { timeout: 5000 });
await page.click('#dialog-buttons button:last-child');
await page.waitForSelector('#result:not([hidden])', { timeout: 20000 });

db = await st();
ok('submit_attempt が 1 回だけ呼ばれる', db.rpcCalls.length === 1, String(db.rpcCalls.length));
ok('提出直前に書いた 1 本も届いている (FLUSH_INK)',
  db.annotations[0].strokes.strokes.length === 3,
  `実際 ${db.annotations[0].strokes.strokes.length} 本`);
ok('全問正解なら満点になる (選択肢のずれが無い)',
  db.attempts[0].total_score === 4 && db.attempts[0].max_score === 4,
  `${db.attempts[0].total_score} / ${db.attempts[0].max_score}`);
ok('採点結果が出る', (await page.textContent('#result-score')).includes('/'),
  await page.textContent('#result-score'));

// ★ F14: 提出 (RPC) より後に届いた再送は 42501 で黙って消える。
//   「RPC の後に書き込みを 1 本も投げていない」ことを順序で見る。
await page.waitForTimeout(2500);          // バックオフが生き残っていれば この間に飛ぶ
db = await st();
const rpcAt = db.log.findIndex((l) => l.t === 'rpc');
const after = db.log.slice(rpcAt + 1)
  .filter((l) => l.op === 'insert' || l.op === 'update');
ok('提出より後に書き込みを投げていない (F14)', rpcAt >= 0 && after.length === 0,
  `${after.length} 件: ${after.map((l) => `${l.t}:${l.op}`).join(', ')}`);
ok('正解と解説が出る',
  (await page.textContent('.q[data-number="1"] .q-res')).includes('解説 1'),
  await page.textContent('.q[data-number="1"] .q-res'));
ok('提出後は答案が読み取り専用',
  await page.evaluate(() => document.querySelector('.q .choice').disabled));
ok('提出後は読むモードに戻る',
  await page.evaluate(() => document.querySelector('#viewer').dataset.mode) === 'read');

// ★ 横画面では結果は答案の **下**。ペインの中で縦に積めていないと右隣に並ぶ
//   (見た目だけの崩れなので、値の検査では 1 件も落ちない)。
const geo = await page.evaluate(() => {
  const a = document.querySelector('#answers').getBoundingClientRect();
  const r = document.querySelector('#result').getBoundingClientRect();
  return { aB: a.bottom, aR: a.right, rT: r.top, rL: r.left, rW: r.width };
});
ok('結果は答案の下に積まれる (右隣に並んでいない)',
  geo.rT >= geo.aB - 1 && geo.rL < geo.aR, JSON.stringify(geo));

// 提出後に書こうとしても 42501 を赤く出さない (静かに止まる)
const before = errors.length;
await page.mouse.move(box.x + 300, box.y + 500);
await page.mouse.down(); await page.mouse.move(box.x + 320, box.y + 520); await page.mouse.up();
await page.waitForTimeout(1800);
ok('提出後の書き込みが例外を出さない', errors.length === before,
  errors.slice(before).join(' | ').slice(0, 200));

} catch (e) { ok('通し実行が最後まで届く', false, String(e).slice(0, 300)); }

// --- F6: 書き込みの取得に失敗したら受験を始めさせない -------------------------
// ★ 「取得失敗」と「白紙」を取り違えると、失敗したページに 1 本書いた瞬間に
//   ページ丸ごと上書きされて既存の書き込みが全消しになる。
try {
  await page.evaluate(() => { localStorage.setItem('__smoke_fail_ann', '1'); });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('body[data-stage="fatal"]', { timeout: 25000 });
  const t = await page.textContent('#fatal-title');
  ok('書き込みを取得できないときは受験を始めさせない (F6)',
    t.includes('書き込みを読み込めませんでした'), t);
} catch (e) {
  const stage = await page.evaluate(() => document.body.dataset.stage).catch(() => '?');
  ok('書き込みを取得できないときは受験を始めさせない (F6)', false,
    `stage=${stage} — 白紙として受験を始めてしまっている`);
}

clearTimeout(watchdog);
await browser.close();
server.close();

let bad = 0;
for (const r of results) if (!r.c) bad++;
if (errors.length) {
  console.log(`\n  ページ側の例外 ${errors.length} 件:`);
  for (const e of errors.slice(0, 8)) console.log(`    ${e.slice(0, 220)}`);
}
console.log(`\n${bad ? `=== 失敗 ${bad} / ${results.length} ===` : `=== 全 ${results.length} 件通過 ===`}`);
process.exit(bad || errors.length ? 1 : 0);
