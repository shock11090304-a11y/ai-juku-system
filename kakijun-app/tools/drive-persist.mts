/**
 * 開発検証 (Phase 5): 完走 → ページ再読込 → 星が残っていること (IndexedDB 永続化)。
 * あ行5文字を完走してスタンプ獲得も確認する。
 */
import { chromium } from '@playwright/test';
import { listByType } from '../src/data';
import { prepareStrokes } from '../src/engine/loader';

const outdir = process.argv[2] ?? '/tmp';
const aGyo = listByType('hiragana').filter((c) => c.group === 'a-gyo');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1180, height: 820 } });
page.on('pageerror', (err) => {
  console.error('[pageerror]', err.message);
  process.exitCode = 1;
});
await page.goto('http://localhost:5199/');

let sawStamp = false;
for (const def of aGyo) {
  await page.click('[data-testid=tile-hiragana]');
  await page.click(`[data-testid=char-${def.id}]`);
  await page.waitForSelector('[data-testid=practice-canvas] canvas');
  await page.waitForTimeout(1500);
  const box = (await page.locator('[data-testid=practice-canvas]').boundingBox())!;
  const toScreen = (p: { x: number; y: number }) => ({
    x: box.x + p.x * box.width,
    y: box.y + p.y * box.height,
  });
  for (const s of prepareStrokes(def)) {
    const start = toScreen(s.pts[0]);
    await page.mouse.move(start.x, start.y);
    await page.mouse.down();
    for (let i = 1; i < 64; i += 2) {
      const p = toScreen(s.pts[i]);
      await page.mouse.move(p.x, p.y);
    }
    await page.mouse.up();
    await page.waitForTimeout(150);
  }
  await page.waitForSelector('[data-testid=celebration]');
  if (await page.locator('[data-testid=new-stamp]').isVisible()) {
    sawStamp = true;
    await page.screenshot({ path: `${outdir}/p5-stamp-get.png` });
  }
  await page.click('[data-testid=btn-back]').catch(() => {});
  // celebration の上から back は押せないので next → back
  if (await page.locator('[data-testid=celebration]').isVisible()) {
    await page.click('[data-testid=btn-next]');
    await page.waitForTimeout(300);
    await page.click('[data-testid=btn-back]');
  }
  await page.waitForTimeout(200);
  await page.click('[data-testid=btn-back]').catch(() => {});
  await page.waitForTimeout(200);
}

// ページを完全に再読込 → 星が残っているか
await page.reload();
await page.waitForTimeout(800);
await page.click('[data-testid=tile-hiragana]');
await page.waitForTimeout(300);
await page.screenshot({ path: `${outdir}/p5-after-reload.png` });
console.log('stamp seen:', sawStamp);

// スタンプ帳
await page.click('[data-testid=btn-reward]');
await page.waitForTimeout(300);
await page.screenshot({ path: `${outdir}/p5-reward.png` });
const stampEarned = await page
  .locator('[data-testid="stamp-hiragana:a-gyo"]')
  .textContent();
console.log('a-gyo stamp after reload:', stampEarned);
if (stampEarned === '❔') process.exitCode = 1;
await browser.close();
