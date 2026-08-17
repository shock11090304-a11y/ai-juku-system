/**
 * 開発検証: 同じ文字を3回続けて完走し、ガイドが Lv1→Lv2→Lv3 と進むこと、
 * Lv3 で★3 を取るとマスターバッジが付くことを確かめる。
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
await page.click(`[data-testid=char-${charId}]`);
await page.waitForSelector('[data-testid=practice-canvas] canvas');

for (let round = 1; round <= 3; round++) {
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${outdir}/lv${round}-guide.png` });
  const box = (await page.locator('[data-testid=practice-canvas]').boundingBox())!;
  const toScreen = (p: { x: number; y: number }) => ({
    x: box.x + p.x * box.width,
    y: box.y + p.y * box.height,
  });
  for (const s of strokes) {
    const start = toScreen(s.pts[0]);
    await page.mouse.move(start.x, start.y);
    await page.mouse.down();
    for (let i = 1; i < 64; i += 2) {
      const p = toScreen(s.pts[i]);
      await page.mouse.move(p.x, p.y);
    }
    await page.mouse.up();
    await page.waitForTimeout(200);
  }
  await page.waitForSelector('[data-testid=celebration]');
  if (round < 3) {
    await page.click('[data-testid=btn-again]');
  }
}
// Lv3 完走 → マスター。celebration を閉じてから文字えらびに戻って王冠を確認
await page.click('[data-testid=btn-next]');
await page.waitForTimeout(300);
await page.click('[data-testid=btn-back]');
await page.waitForTimeout(300);
await page.screenshot({ path: `${outdir}/lv-select-after.png` });
const crown = await page
  .locator(`[data-testid=char-${charId}] [aria-label=ますたー]`)
  .isVisible()
  .catch(() => false);
console.log('master crown visible:', crown);
await browser.close();
