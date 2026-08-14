// =============================================================================
// 冊子受験画面 — 本編では通らない 2 経路
//
//   node edge_smoke.mjs <repoRoot> <fixtureDir>
//
// ★ browser_smoke.mjs は「1 台で最後まで解いて出す」筋だけを通す。だが消失が
//   いちばん怖いのは **別端末が同じページを触ったとき** で、そこは 1 台では作れない。
//   偽 Supabase の行を直接書き換えて「他所で更新された」状況を作り、
//   CAS が **上書きする前に** 気づくこと・「両方を残す」で双方が残ることを見る。
//
// ★ 時間切れの自動提出も本編では通らない (制限時間 NULL のため)。確認ダイアログを
//   挟まずに提出される経路で、**保存が済む前に打ち切られる**ので取りこぼしやすい。
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
const page=await (await b.newContext({viewport:{width:1280,height:900},hasTouch:true})).newPage();
page.setDefaultTimeout(20000);
const errs=[]; const isFav=u=>String(u||'').endsWith('/favicon.ico');
page.on('pageerror',e=>errs.push(String(e)));
page.on('console',m=>{const l=m.location&&m.location(); if(m.type()==='error'&&!isFav(l&&l.url)) errs.push('console: '+m.text());});

await page.route('**/exam-book-config.mjs*',r=>r.fulfill({contentType:'text/javascript',
  body:"export const SUPABASE={url:'https://x.supabase.co',anonKey:'t'};\nexport function assertAnonKey(){}\n"}));
await page.route('**/vendor/supabase-js/supabase.mjs*',r=>r.fulfill({contentType:'text/javascript',
  body:fs.readFileSync(path.join(FIX,'mock_supabase.mjs'),'utf8')}));
await page.route('**/__pdf/**',r=>r.fulfill({contentType:'application/pdf',
  body:fs.readFileSync(path.join(FIX,'book.pdf'))}));

let bad=0;
const ok=(n,c,x='')=>{ if(!c) bad++; console.log(`${c?'  ✓':'  ✗'} ${n}${c||!x?'':' — '+x}`); };
const st=()=>page.evaluate(()=>globalThis.__DB);
const strokes=async()=>{const d=await st(); const a=d.annotations[0];
  return a&&a.strokes&&a.strokes.strokes?a.strokes.strokes:[];};
async function draw(box,x0,y0,dx,dy,n=8){
  await page.mouse.move(box.x+box.width*x0, box.y+box.height*y0);
  await page.mouse.down();
  for(let i=1;i<=n;i++) await page.mouse.move(box.x+box.width*(x0+dx*i/n), box.y+box.height*(y0+dy*i/n));
  await page.mouse.up();
}

// =============================================================================
console.log('--- 別端末が同じページを書き換えたとき (CAS の競合) ---');
// =============================================================================
await page.goto(`${base}/exam-book.html`,{waitUntil:'domcontentloaded'});
await page.evaluate(()=>localStorage.clear());
await page.reload({waitUntil:'domcontentloaded'});
await page.waitForSelector('body[data-stage="ready"]');
await page.waitForTimeout(1200);
await page.click('[data-mode="write"]');
const box = await (await page.$('#viewer .page')).boundingBox();

await draw(box, 0.10, 0.20, 0.25, 0.10);
await page.waitForTimeout(2200);
ok('自分の 1 本目が保存される', (await strokes()).length===1, `${(await strokes()).length} 本`);

// ★ 別端末が同じページを書き換えた状況を作る (updated_at が進む = こちらの版が古くなる)
await page.evaluate(()=>{
  const r = globalThis.__DB.annotations[0];
  r.strokes = { v:1, strokes:[{ c:'#d02a2a', w:0.003, p:[[0.80,0.10],[0.90,0.20]] }] };
  r.updated_at = new Date(Date.now()+60000).toISOString();
});

await draw(box, 0.10, 0.50, 0.25, 0.10);          // 2 本目 → CAS が 0 行になるはず
await page.waitForSelector('#dialog[open]',{timeout:15000}).catch(()=>{});
const openNow = await page.evaluate(()=>document.querySelector('#dialog').open);
ok('上書きする前に競合を検出してダイアログを出す', openNow===true);
const title = await page.textContent('#dialog-title').catch(()=>'');
ok('どのページで起きたか出ている', /別の端末/.test(title), `「${title}」`);
const btns = await page.$$eval('#dialog-buttons button', bs=>bs.map(b=>b.textContent));
ok('消しゴム未使用なら「両方を残す」が選べる', btns.includes('両方を残す'), JSON.stringify(btns));

await page.click(`#dialog-buttons button:nth-child(${btns.indexOf('両方を残す')+1})`);
await page.waitForTimeout(2500);
const after = await strokes();
ok('自分の 2 本が残っている', after.length>=3, `${after.length} 本`);
ok('別端末の 1 本も消えていない', after.some(s=>s.c==='#d02a2a'),
   JSON.stringify(after.map(s=>s.c)));
ok('保存が通っている (未保存 0)', (await page.textContent('#saveState')).includes('保存済み'),
   await page.textContent('#saveState'));

// =============================================================================
console.log('--- 時間切れの自動提出 ---');
// =============================================================================
await page.evaluate(()=>{ localStorage.clear(); localStorage.setItem('__smoke_time_limit','8'); });
await page.reload({waitUntil:'domcontentloaded'});
await page.waitForSelector('body[data-stage="ready"]');
await page.waitForTimeout(800);
const clock = await page.textContent('#clock');
ok('残り時間が出る', /残り \d+:\d\d/.test(clock), `「${clock}」`);

await page.click('[data-mode="write"]');
const box2 = await (await page.$('#viewer .page')).boundingBox();
await draw(box2, 0.15, 0.30, 0.30, 0.15);        // ★ 保存前に時間切れを迎えさせる
await page.click('.q[data-number="1"] .choice:nth-of-type(2)');

// 時間切れ → 自動提出 (確認ダイアログは出ない)
await page.waitForSelector('#result:not([hidden])',{timeout:40000}).catch(()=>{});
const shown = await page.evaluate(()=>!document.querySelector('#result').hidden);
ok('0 秒で自動提出され、結果が出る', shown===true,
   `stage=${await page.evaluate(()=>document.body.dataset.stage)} clock=${await page.textContent('#clock')}`);
const db2 = await st();
ok('自動提出でも RPC は 1 回だけ', db2.rpcCalls.length===1, String(db2.rpcCalls.length));
ok('自動提出でも解答が保存されている',
   (db2.answers.find(a=>a.question_id==='q1')||{}).user_answer==='2',
   JSON.stringify(db2.answers.map(a=>a.user_answer)));
ok('自動提出でも直前の手書きが届いている',
   db2.annotations.length===1 && db2.annotations[0].strokes.strokes.length===1,
   `${db2.annotations.length} ページ / ${db2.annotations[0]?db2.annotations[0].strokes.strokes.length:0} 本`);
ok('提出後は書けない (読むモード)',
   await page.evaluate(()=>document.querySelector('#viewer').dataset.mode)==='read');

// =============================================================================
console.log('--- 開始時刻が読めないとき ---');
// =============================================================================
// ★ ここを素通しにすると残り時間が NaN になり、表示が「残り NaN:NaN」になるうえ
//   `left <= 0` が永久に false なので **自動提出も走らない**。どちらも黙って壊れる。
//   時間を数えられないときに打ち切るのは生徒に不利なので、自動提出はしないのが正。
await page.evaluate(()=>{ localStorage.clear();
  localStorage.setItem('__smoke_time_limit','5');
  localStorage.setItem('__smoke_no_started_at','1'); });
await page.reload({waitUntil:'domcontentloaded'});
await page.waitForSelector('body[data-stage="ready"]');
await page.waitForTimeout(1000);
const clock3 = await page.textContent('#clock');
ok('NaN を表示しない', !/NaN/.test(clock3), `「${clock3}」`);
ok('計算できないことを画面に出す', /計算できません/.test(clock3), `「${clock3}」`);
ok('帯でも知らせる', /残り時間/.test(await page.textContent('#banner')),
   await page.textContent('#banner'));
await page.waitForTimeout(9000);                  // 制限時間 5 秒を十分に超える
ok('数えられないときは勝手に提出しない',
   await page.evaluate(()=>document.querySelector('#result').hidden)===true,
   `rpc=${(await st()).rpcCalls.length} 回`);
await page.evaluate(()=>localStorage.clear());

const real = errs.filter(e=>!/favicon|404/.test(e));
if (real.length){ console.log('\n  ページ側の例外:'); real.slice(0,6).forEach(e=>console.log('   ',e.slice(0,200))); }
await b.close(); server.close();
console.log(bad||real.length ? `\n  === 失敗 ${bad} 件 ===` : `\n  === 追加 3 経路 通過 ===`);
process.exit(bad||real.length ? 1 : 0);
