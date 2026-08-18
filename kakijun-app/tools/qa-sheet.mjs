/**
 * ★ 目視QA用: 実アプリの練習画面を1字ずつ撮って、一覧シートに貼る。
 *
 *   npx vite build && npx vite preview --port 4173 &
 *   node tools/qa-sheet.mjs [--out DIR] [--url URL] [--cols N] [type...]
 *
 * 「検査が緑でも見た目が壊れていることがある」(HANDOFF §7-1) ので、
 * 出荷前にこのシートを人の目で見る。コンタクトシート (線データだけ) と違い、
 * ★お手本フォント・番号・書き出しの点まで含めた「子どもが実際に見る画面」を撮る。
 *
 * type を省略すると全種別。出力:
 *   DIR/<charId>.png       1字ずつ
 *   DIR/sheet-<type>-N.png 一覧シート (これを人が見る)
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from '@playwright/test';

const argv = process.argv.slice(2).filter((a) => a !== '--');
function opt(name, fallback) {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 ? argv[i + 1] : fallback;
}
const OUT = opt('out', '/tmp/kakijun-qa');
const URL = opt('url', 'http://localhost:4173/');
const COLS = Number(opt('cols', 6));
const PER_SHEET = Number(opt('per-sheet', 24));
const TYPES = argv.filter((a, i) => !a.startsWith('--') && !argv[i - 1]?.startsWith('--'));
const ALL_TYPES = ['hiragana', 'katakana', 'number', 'unpitsu'];
const types = TYPES.length ? TYPES : ALL_TYPES;

fs.mkdirSync(OUT, { recursive: true });

async function launch() {
  try {
    return await chromium.launch();
  } catch {
    return chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  }
}

const browser = await launch();
const page = await browser.newPage({ viewport: { width: 1180, height: 820 } });
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('console', (m) => {
  if (m.type() === 'error') errors.push(m.text());
});

const shots = [];
for (const type of types) {
  await page.goto(URL, { waitUntil: 'networkidle' });
  const tile = page.locator(`[data-testid=tile-${type}]`);
  if (!(await tile.count())) {
    console.error(`  tile-${type} が無い`);
    continue;
  }
  await tile.click();
  await page.waitForTimeout(300);
  // かな は 五十音/濁音/拗音 のタブに分かれているので全タブ回る
  const tabs = await page.locator('header button').allInnerTexts();
  const tabNames = tabs.filter((t) => /^[ぁ-んァ-ヶ]/.test(t.trim()));
  const rounds = tabNames.length ? tabNames : [null];
  for (const tab of rounds) {
    if (tab) {
      const b = page.locator('header button', { hasText: tab }).first();
      if (await b.count()) await b.click();
      await page.waitForTimeout(200);
    }
    const ids = await page.$$eval('[data-testid^=char-]', (els) =>
      els.map((e) => e.getAttribute('data-testid').replace(/^char-/, '')),
    );
    for (const id of ids) {
      if (shots.some((s) => s.id === id)) continue;
      await page.click(`[data-testid=char-${id}]`);
      await page.waitForSelector('[data-testid=practice-canvas] canvas');
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(260);
      const file = path.join(OUT, `${id}.png`);
      await page.locator('[data-testid=practice-canvas]').screenshot({ path: file });
      const char = await page.locator('header span').first().innerText();
      shots.push({ id, char, type, file });
      // 戻る (練習 → 文字えらび)。タブ選択は保持されない実装なので選び直す
      await page.locator('header button').first().click();
      await page.waitForTimeout(160);
      if (tab) {
        const b = page.locator('header button', { hasText: tab }).first();
        if (await b.count()) await b.click();
        await page.waitForTimeout(120);
      }
    }
  }
}

// ── 一覧シートに貼る ────────────────────────────────────
const sheetPage = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
const sheets = [];
for (const type of types) {
  const list = shots.filter((s) => s.type === type);
  for (let i = 0, n = 0; i < list.length; i += PER_SHEET, n++) {
    const chunk = list.slice(i, i + PER_SHEET);
    const cells = chunk
      .map((s) => {
        const b64 = fs.readFileSync(s.file).toString('base64');
        return `<figure><img src="data:image/png;base64,${b64}"><figcaption>${s.char} <small>${s.id}</small></figcaption></figure>`;
      })
      .join('');
    const html = `<!doctype html><meta charset="utf-8"><style>
      body{margin:0;background:#fafafa;font-family:sans-serif}
      .grid{display:grid;grid-template-columns:repeat(${COLS},1fr);gap:6px;padding:8px}
      figure{margin:0;background:#fff;border:1px solid #ddd;border-radius:6px;overflow:hidden}
      img{width:100%;display:block}
      figcaption{font-size:13px;text-align:center;padding:2px}
      small{color:#888;font-size:10px}
    </style><div class="grid">${cells}</div>`;
    await sheetPage.setContent(html);
    await sheetPage.waitForTimeout(120);
    const out = path.join(OUT, `sheet-${type}-${n + 1}.png`);
    await sheetPage.locator('.grid').screenshot({ path: out });
    sheets.push(out);
  }
}

await browser.close();
console.log(`撮影 ${shots.length} 字 → ${OUT}`);
for (const s of sheets) console.log(`  シート: ${s}`);
if (errors.length) {
  console.error(`★ ブラウザのエラー ${errors.length} 件:`);
  for (const e of [...new Set(errors)].slice(0, 10)) console.error(`  ${e}`);
  process.exit(1);
}
