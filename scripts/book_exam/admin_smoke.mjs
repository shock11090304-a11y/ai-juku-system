// =============================================================================
// 先生用の冊子登録画面 — 実ブラウザでの通し確認
//
//   node admin_smoke.mjs <repoRoot> <fixtureDir>
//
// ★ 受験画面と同じ作法: 差し替えるのは **接続設定と supabase-js の 2 本だけ**。
//   exam-book-admin*.mjs / pdf.js / CSS / HTML は配信するものそのものを読ませる。
//
// ★ ここで守りたいのは「壊れた冊子を作れないこと」。
//   ・生徒が全員 0 点になる正解 (0 起算・全角・範囲外) を保存させない
//   ・設問 0 問 / PDF 無しの冊子を公開させない
//   ・講師でないアカウントに開かせない
// =============================================================================
import { createRequire } from 'node:module';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright-core');

const ROOT = process.argv[2], FIX = process.argv[3];
const TYPES = { '.html':'text/html','.css':'text/css','.mjs':'text/javascript',
  '.pdf':'application/pdf','.bcmap':'application/octet-stream' };
const server = http.createServer((req,res)=>{
  const u=decodeURIComponent(req.url.split('?')[0]); const p=path.join(ROOT,u);
  if(!p.startsWith(ROOT)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream'});
  fs.createReadStream(p).pipe(res);
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=`http://127.0.0.1:${server.address().port}`;

const b=await chromium.launch({executablePath:process.env.CHROME_BIN,args:['--no-sandbox']});
const page=await (await b.newContext({viewport:{width:1400,height:1000}})).newPage();
page.setDefaultTimeout(20000);
const watchdog = setTimeout(()=>{ console.log('  ✗ 制限時間を超えた'); process.exit(1); }, 150000);
const errs=[]; const isFav=u=>String(u||'').endsWith('/favicon.ico');
page.on('pageerror',e=>errs.push(String(e)));
page.on('console',m=>{const l=m.location&&m.location(); if(m.type()==='error'&&!isFav(l&&l.url)) errs.push('console: '+m.text());});

let bad=0;
const ok=(n,c,x='')=>{ if(!c) bad++; console.log(`${c?'  ✓':'  ✗'} ${n}${c||!x?'':' — '+x}`); };
const st=()=>page.evaluate(()=>globalThis.__DB);

await page.route('**/exam-book-config.mjs*',r=>r.fulfill({contentType:'text/javascript',
  body:"export const SUPABASE={url:'https://x.supabase.co',anonKey:'t'};\nexport function assertAnonKey(){}\n"}));
await page.route('**/vendor/supabase-js/supabase.mjs*',r=>r.fulfill({contentType:'text/javascript',
  body:fs.readFileSync(path.join(FIX,'mock_supabase.mjs'),'utf8')}));

// --- 講師でないと開けない -----------------------------------------------------
await page.goto(`${base}/exam-book-admin.html`,{waitUntil:'domcontentloaded'});
await page.evaluate(()=>localStorage.setItem('__smoke_role','student'));
await page.reload({waitUntil:'domcontentloaded'});
await page.waitForSelector('body[data-stage="fatal"]',{timeout:20000}).catch(()=>{});
ok('生徒アカウントでは開けない',
   await page.evaluate(()=>document.body.dataset.stage)==='fatal',
   `stage=${await page.evaluate(()=>document.body.dataset.stage)}`);
ok('理由が画面に出る', /講師/.test(await page.textContent('#fatal-title').catch(()=>'')),
   await page.textContent('#fatal-title').catch(()=>''));

// --- 講師で開く ---------------------------------------------------------------
await page.evaluate(()=>localStorage.setItem('__smoke_role','teacher'));
await page.reload({waitUntil:'domcontentloaded'});
await page.waitForSelector('body[data-stage="ready"]',{timeout:20000}).catch(()=>{});
ok('講師なら開ける', await page.evaluate(()=>document.body.dataset.stage)==='ready',
   `stage=${await page.evaluate(()=>document.body.dataset.stage)}`);
ok('冊子が一覧に出る', (await page.$$('#books .bookrow')).length>=1,
   `${(await page.$$('#books .bookrow')).length} 件`);

// --- PDF をまとめて調べる -----------------------------------------------------
// ★ 先生の PC のファイルには作業環境から触れないが、ブラウザなら触れる。
//   選んでもらった PDF をこの画面の中だけで開いて判定する (どこにも送らない)。
{
  const pdf = fs.readFileSync(path.join(FIX,'book.pdf'));
  await page.setInputFiles('#scan-files', [
    { name: '共通テスト英語R_問題.pdf', mimeType: 'application/pdf', buffer: pdf },
    { name: '共通テスト英語R_解説.pdf', mimeType: 'application/pdf', buffer: pdf },
    { name: 'こわれたもの.pdf', mimeType: 'application/pdf', buffer: Buffer.from('not a pdf') },
  ]);
  await page.waitForTimeout(4000);
  const txt = await page.textContent('#scan-result');
  ok('まとめて調べた結果が出る', /3 件中 2 件が使えます/.test(txt), txt.slice(0,100));
  ok('ページ数を出す', /2 ページ/.test(txt), '');
  ok('開けない PDF を使えないと言う', /1 件は使えません/.test(txt), '');
  ok('問題と解説の対を見つける', /対がそろっています/.test(txt), '');
  ok('解説から読み取った文字を見せる',
     (await page.inputValue('#scan-text')).includes('Page One'),
     (await page.inputValue('#scan-text')).slice(0,60));
}

// --- 設問 0 問の冊子は公開できない -------------------------------------------
// ★ 公開してしまうと、生徒の画面には「この冊子は現在公開停止です」と出て何も解けない。
//   偽 DB の b2 が「設問 0・未公開」。
await page.click('.bookrow[data-id="b2"] .pub');
await page.waitForTimeout(400);
ok('設問が 0 問の冊子は公開できない',
   /公開できません/.test(await page.textContent('#banner')),
   await page.textContent('#banner'));
ok('公開されていない', (await st()).books.find(x=>x.id==='b2').is_published===false);

// --- 設問の編集 ---------------------------------------------------------------
await page.click('.bookrow[data-id="b1"] button:last-child');
await page.waitForSelector('#editor:not([hidden])');
const rows = await page.$$('#q-rows .qrow');
ok('既存の設問が表に出る', rows.length>=1, `${rows.length} 行`);

// ★ 全員 0 点になる正解を入れて保存を試みる
const setCell = async (i,k,v)=>{
  const sel = `.qrow[data-i="${i}"] [data-k="${k}"]`;
  await page.fill(sel, String(v)).catch(async()=>{ await page.selectOption(sel, String(v)); });
};
await setCell(0,'correct_answer','0');
await page.click('#q-save');
await page.waitForTimeout(500);
ok('0 起算の正解では保存させない',
   /おかしいところ/.test(await page.textContent('#banner')), await page.textContent('#banner'));
ok('どの欄が悪いか印を付ける',
   await page.evaluate(()=>!!document.querySelector('.qrow[data-i="0"] [data-k="correct_answer"].bad')));
ok('DB に書かれていない',
   (await st()).questions.find(q=>q.book_id==='b1').correct_answer!=='0');

await setCell(0,'correct_answer','３');       // 全角
await page.click('#q-save');
await page.waitForTimeout(500);
ok('全角数字でも保存させない',
   /おかしいところ/.test(await page.textContent('#banner')), await page.textContent('#banner'));

// 正しい値なら保存できる
await setCell(0,'correct_answer','2');
await page.click('#q-save');
await page.waitForTimeout(800);
ok('正しい値なら保存できる', /保存しました/.test(await page.textContent('#banner')),
   await page.textContent('#banner'));
ok('DB に届いている', (await st()).questions.find(q=>q.book_id==='b1').correct_answer==='2',
   (await st()).questions.find(q=>q.book_id==='b1').correct_answer);

// --- 設問を足す ---------------------------------------------------------------
const before = (await page.$$('#q-rows .qrow')).length;
await page.click('#q-add');
await page.waitForTimeout(200);
ok('設問を足せる', (await page.$$('#q-rows .qrow')).length===before+1);
const n = before;   // 足した行の index
ok('番号が自動で振られる',
   (await page.inputValue(`.qrow[data-i="${n}"] [data-k="number"]`))!=='',
   await page.inputValue(`.qrow[data-i="${n}"] [data-k="number"]`));

await setCell(n,'page','1');
await setCell(n,'correct_answer','1');
await page.click('#q-save');
await page.waitForTimeout(800);
ok('足した設問が DB に入る',
   (await st()).questions.filter(q=>q.book_id==='b1').length===before+1,
   `${(await st()).questions.filter(q=>q.book_id==='b1').length} 問`);

// --- JSON の一括読み込み -------------------------------------------------------
// ★ 既に保存された設問がある冊子には入れない (番号がぶつかって、生徒の答案が
//   参照している行を壊しかねない)。b1 は保存済みなので断られるのが正しい。
const BUNDLE = JSON.stringify({
  book: { title: '取り込みの見本', subject: 'japanese' },
  preview: [{ number: 1, stem: '木の葉、庭に＿落ち＿て。', correct_answer: '3',
              correct_text: '上二段活用' }],
  questions: [
    { number: 1, page: 1, answer_type: 'choice', choice_count: 4, correct_answer: '3',
      points: 1, explanation: '上二段活用と決まる' },
    { number: 2, page: null, answer_type: 'short', correct_answer: 'けり',
      accepted_answers: ['ケリ'], points: 2, explanation: '詠嘆' },
  ],
});
const upload = async (name, body) => {
  await page.setInputFiles('#q-import', { name, mimeType: 'application/json',
                                          buffer: Buffer.from(body, 'utf8') });
  await page.waitForTimeout(500);
};
await upload('bundle.json', BUNDLE);
ok('保存済みの冊子には一括読み込みできない',
   /既に保存された設問/.test(await page.textContent('#banner')),
   await page.textContent('#banner'));

// 設問が 0 問の冊子 (b2) には入れられる
await page.click('.bookrow[data-id="b2"] button:last-child');
await page.waitForSelector('#editor:not([hidden])');

await upload('broken.json', '{ questions: ');
ok('壊れた JSON は断る', /読み込めません/.test(await page.textContent('#banner')),
   await page.textContent('#banner'));

await upload('bundle.json', BUNDLE);
ok('空の冊子には読み込める', (await page.$$('#q-rows .qrow')).length===2,
   `${(await page.$$('#q-rows .qrow')).length} 行`);
ok('起算の確認を画面に出す',
   /1 問だけ実物と照合|正解 3 番|3 番 =/.test(await page.textContent('#q-import-note')),
   await page.textContent('#q-import-note'));
ok('読み込んだだけでは DB に書かない',
   (await st()).questions.filter(q=>q.book_id==='b2').length===0,
   `${(await st()).questions.filter(q=>q.book_id==='b2').length} 問`);
await page.click('#q-save');
await page.waitForTimeout(800);
ok('保存を押すと DB に入る',
   (await st()).questions.filter(q=>q.book_id==='b2').length===2,
   `${(await st()).questions.filter(q=>q.book_id==='b2').length} 問`);

// --- 正解をまとめて流し込む ---------------------------------------------------
// ★ マーク式の冊子は「正解一覧が紙にある」。1 問ずつ欄を移動するのが手入力の重さなので、
//   そのまま打てるようにする。★ 記述の行には入れない (数字で埋めると採点が全部外れる)。
{
  // b2 は 1 問目=選択式(4択) / 2 問目=記述 で取り込んである
  await page.fill('#q-key', '2 9');
  await page.click('#q-key-apply');
  await page.waitForTimeout(400);
  ok('選択式の数を超える数は流し込めない',
     /2 個ありますが、設問は 1 問です|おかしいところ/.test(await page.textContent('#banner')),
     await page.textContent('#banner'));

  await page.fill('#q-key', '4');
  await page.click('#q-key-apply');
  await page.waitForTimeout(400);
  ok('選択式の行に入る',
     (await page.inputValue('.qrow[data-i="0"] [data-k="correct_answer"]'))==='4',
     await page.inputValue('.qrow[data-i="0"] [data-k="correct_answer"]'));
  ok('★記述の行には入らない',
     (await page.inputValue('.qrow[data-i="1"] [data-k="correct_answer"]'))==='けり',
     await page.inputValue('.qrow[data-i="1"] [data-k="correct_answer"]'));

  await page.fill('#q-key', '9');
  await page.click('#q-key-apply');
  await page.waitForTimeout(400);
  ok('選択肢の数を超える正解はその場で赤くする',
     await page.evaluate(()=>!!document.querySelector('.qrow[data-i="0"] [data-k="correct_answer"].bad')));
}

// --- 削除ボタンを置いていない -------------------------------------------------
// ★ 消すと生徒の答案・手書きが cascade で巻き添えになる。出さないことが仕様。
ok('冊子と設問に削除ボタンが無い',
   await page.evaluate(()=>[...document.querySelectorAll('button')]
     .every(b=>!/削除|消す|delete/i.test(b.textContent))),
   await page.evaluate(()=>[...document.querySelectorAll('button')]
     .map(b=>b.textContent.trim()).join(' / ')));

const real = errs.filter(e=>!/favicon|404/.test(e));
if (real.length){ console.log('\n  ページ側の例外:'); real.slice(0,6).forEach(e=>console.log('   ',e.slice(0,200))); }
clearTimeout(watchdog);
await b.close(); server.close();
console.log(bad||real.length ? `\n  === 失敗 ${bad} 件 ===` : `\n  === 登録画面 通過 ===`);
process.exit(bad||real.length ? 1 : 0);
