/**
 * 開発検証: 実ブラウザで ホーム → 文字えらび → 練習(あ) を通しで操作し、
 * 実データの理想軌跡をマウスでなぞって完走できることを確かめる。
 *   npx vite-node tools/drive-practice.mts -- <outdir> [charId] [reverseFirst]
 */
import { chromium } from '@playwright/test';
import { getChar } from '../src/data';
import { prepareStrokes } from '../src/engine/loader';

const outdir = process.argv[2] ?? '/tmp';
const charId = process.argv[3] ?? 'hira_a';
const def = getChar(charId);
const strokes = prepareStrokes(def);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1180, height: 820 } });
page.on('pageerror', (err) => {
  console.error('[pageerror]', err.message);
  process.exitCode = 1;
});
await page.goto('http://localhost:5199/');
await page.click(`[data-testid=tile-${def.type}]`);
await page.screenshot({ path: `${outdir}/p3-select.png` });
await page.click(`[data-testid=char-${charId}]`);
await page.waitForSelector('[data-testid=practice-canvas] canvas');
await page.waitForTimeout(1600); // お手本アニメを見送る
await page.screenshot({ path: `${outdir}/p3-practice-lv1.png` });

const box = (await page.locator('[data-testid=practice-canvas]').boundingBox())!;
const toScreen = (p: { x: number; y: number }) => ({
  x: box.x + p.x * box.width,
  y: box.y + p.y * box.height,
});

for (const s of strokes) {
  const pts = s.pts;
  const start = toScreen(pts[0]);
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  for (let i = 1; i < 64; i += 2) {
    const p = toScreen(pts[i]);
    await page.mouse.move(p.x, p.y);
  }
  await page.mouse.up();
  await page.waitForTimeout(250);
}

await page.screenshot({ path: `${outdir}/p3-after-strokes.png` });
const celebration = await page.locator('[data-testid=celebration]').isVisible();
console.log('celebration visible:', celebration);
if (!celebration) process.exitCode = 1;
await page.click('[data-testid=btn-next]');
await page.waitForTimeout(400);
await page.screenshot({ path: `${outdir}/p3-next-char.png` });
await browser.close();
