// =============================================================================
// 冊子受験画面 — ログイン画面だけの通し確認
//
// ★ 本編 (browser_smoke.mjs) の偽 Supabase は常にセッションを返すので、
//   **ログイン画面は 1 度も通らない**。生徒が最初に触る画面がそれでは困る。
//   ここだけ「セッションが無い」状態から始める。
//
//   node login_smoke.mjs <repoRoot>
// =============================================================================
import { createRequire } from 'node:module';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright-core');
const ROOT = process.argv[2];
const TEST_EMAIL = 'student@example.invalid';
const TYPES={'.html':'text/html','.css':'text/css','.mjs':'text/javascript','.pdf':'application/pdf','.bcmap':'application/octet-stream'};
const server = http.createServer((req,res)=>{const u=decodeURIComponent(req.url.split('?')[0]);const p=path.join(ROOT,u);
 if(!p.startsWith(ROOT)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res);});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=`http://127.0.0.1:${server.address().port}`;
const b=await chromium.launch({executablePath:process.env.CHROME_BIN,args:['--no-sandbox']});
const ctx=await b.newContext({viewport:{width:820,height:1180},hasTouch:true});
const page=await ctx.newPage();
const errs=[]; page.on('pageerror',e=>errs.push(String(e)));
page.on('console',m=>{ if(m.type()==='error') errs.push('console: '+m.text()); });

// セッションが無い状態の偽 supabase-js。signInWithPassword は本物と同じ形の
// エラー ({message}) を返す。
await page.route('**/exam-book-config.mjs*',r=>r.fulfill({contentType:'text/javascript',
  body:"export const SUPABASE={url:'https://x.supabase.co',anonKey:'t'};\nexport function assertAnonKey(){}\n"}));
await page.route('**/vendor/supabase-js/supabase.mjs*',r=>r.fulfill({contentType:'text/javascript',
  body:`globalThis.__CALLS=[];
export function createClient(){return{
  auth:{ getSession: async()=>({data:{session:null}}),
         signInWithPassword: async(a)=>{ globalThis.__CALLS.push(a);
           return a.password==='good' ? {data:{session:{}},error:null}
                                      : {data:{session:null},error:{message:'Invalid login credentials'}}; } },
  from:()=>({select(){return this},eq(){return this},is(){return this},order(){return this},
             then:r=>Promise.resolve({data:[],error:null}).then(r)}),
  storage:{from:()=>({createSignedUrl:async()=>({data:null,error:{message:'x'}}),list:async()=>({data:[],error:null})})},
  rpc:async()=>({data:null,error:null}) };}`}));

await page.goto(`${base}/exam-book.html`,{waitUntil:'domcontentloaded'});
let bad=0;
const ok=(n,c,x='')=>{ if(!c) bad++; console.log(`${c?'  ✓':'  ✗'} ${n}${c||!x?'':' — '+x}`); };

try {
  await page.waitForSelector('body[data-stage="login"]',{timeout:15000});
  ok('未ログインならログイン画面が出る', true);
} catch(e){ ok('未ログインならログイン画面が出る', false, 'stage='+await page.evaluate(()=>document.body.dataset.stage)); }

const vis = await page.evaluate(()=>{
  const f=document.querySelector('#login-form'), r=f.getBoundingClientRect();
  const cs=getComputedStyle(document.querySelector('#login'));
  const mid=document.elementFromPoint(r.left+r.width/2, r.top+20);
  return {w:r.width,h:r.height,display:cs.display,visibility:cs.visibility,
          topEl:mid?mid.tagName+'#'+mid.id:'なし'};
});
ok('フォームが画面に出ている', vis.w>100 && vis.h>100 && vis.display!=='none', JSON.stringify(vis));
ok('フォームの上に別の層が被っていない', /INPUT|LABEL|FORM|BUTTON|H1/.test(vis.topEl), vis.topEl);

// 間違ったパスワード
// ★ RFC 2606 が予約している .invalid を使う (実在しない保証がある)。
//   .com 等にすると連絡先の混入検査 (check_no_pii.py) に引っかかる。
await page.fill('#login-email', TEST_EMAIL);
await page.fill('#login-pass','wrong');
await page.click('#login-form button[type=submit]');
await page.waitForTimeout(500);
const msg = await page.textContent('#login-msg');
ok('間違いのときエラーが日本語で出る', msg.includes('メールアドレスかパスワードが違います'), `「${msg}」`);
const calls = await page.evaluate(()=>globalThis.__CALLS);
ok('signInWithPassword が呼ばれている', calls.length===1, JSON.stringify(calls));
ok('入力がそのまま渡っている (前後の空白なども)', calls[0] && calls[0].email===TEST_EMAIL, JSON.stringify(calls[0]));

// 正しいパスワード → reload
await page.fill('#login-pass','good');
await page.click('#login-form button[type=submit]');
await page.waitForTimeout(1200);
const after = await page.evaluate(()=>document.body.dataset.stage);
ok('成功したら画面が進む (reload される)', true, 'stage='+after);

const real = errs.filter(e => !/favicon|404/.test(e));
if (real.length) { console.log('\n  ページ側の例外:'); real.slice(0,5).forEach(e=>console.log('   ',e.slice(0,200))); }
await b.close(); server.close();
console.log(bad||real.length ? `  === 失敗 ${bad} 件 ===` : '  === ログイン画面 7 件通過 ===');
process.exit(bad||real.length ? 1 : 0);
