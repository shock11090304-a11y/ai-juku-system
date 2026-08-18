/**
 * 開発検証: フィードバック演出と「3回連続失敗でガイドが易しくなる」(§7.4 ★)。
 * あ を完走して Lv2 に上げ、Lv2 で3回わざと失敗 → Lv1 に自動で戻ることを確認。
 */
import { chromium } from '@playwright/test';
import { getChar } from '../src/data';
import { prepareStrokes } from '../src/engine/loader';

const outdir = process.argv[2] ?? '/tmp';
const def = getChar('hira_a');
const strokes = prepareStrokes(def);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1180, height: 820 } });
let pageErrors = 0;
page.on('pageerror', (err) => {
  pageErrors++;
  console.error('[pageerror]', err.message);
});
await page.goto('http://localhost:5199/');
await page.click('[data-testid=tile-hiragana]');
await page.click('[data-testid=char-hira_a]');
await page.waitForSelector('[data-testid=practice-canvas] canvas');
await page.waitForTimeout(1500);

const box = (await page.locator('[data-testid=practice-canvas]').boundingBox())!;
const toScreen = (p: { x: number; y: number }) => ({
  x: box.x + p.x * box.width,
  y: box.y + p.y * box.height,
});

async function trace(sIdx: number, opts: { reverse?: boolean; stopAt?: number } = {}) {
  let pts = strokes[sIdx].pts;
  if (opts.reverse) pts = pts.slice().reverse();
  const end = opts.stopAt ?? 64;
  const start = toScreen(pts[0]);
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  for (let i = 1; i < end; i += 2) {
    const p = toScreen(pts[i]);
    await page.mouse.move(p.x, p.y);
  }
  await page.mouse.up();
  await page.waitForTimeout(300);
}

// ① まちがった始点（中央をタップ）→ 始点パルス
await page.mouse.click(box.x + box.width * 0.55, box.y + box.height * 0.45);
await page.waitForTimeout(150);
await page.screenshot({ path: `${outdir}/fb-start.png` });

// ② 2画目から書こうとする → 番号ズーム
const s2 = toScreen(strokes[1].pts[0]);
await page.mouse.click(s2.x, s2.y);
await page.waitForTimeout(150);
await page.screenshot({ path: `${outdir}/fb-order.png` });

// ③ 完走して Lv2 へ
for (let i = 0; i < 3; i++) await trace(i);
await page.waitForSelector('[data-testid=celebration]');
await page.click('[data-testid=btn-again]');
await page.waitForTimeout(600);

// ④ Lv2 で3回失敗（途中でやめる×3）→ Lv1 に自動で戻る
for (let i = 0; i < 3; i++) await trace(0, { stopAt: 20 });
await page.waitForTimeout(400);
await page.screenshot({ path: `${outdir}/fb-leveldown.png` });

console.log('pageErrors:', pageErrors);
if (pageErrors > 0) process.exitCode = 1;
await browser.close();
