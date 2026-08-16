/**
 * 開発検証 (Phase 6): 保護者ゲート（正解で入れる・3回誤答でホームへ戻る）、
 * ダッシュボード表示、設定変更、エクスポート。
 */
import { chromium } from '@playwright/test';

const outdir = process.argv[2] ?? '/tmp';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1180, height: 820 } });
page.on('pageerror', (err) => {
  console.error('[pageerror]', err.message);
  process.exitCode = 1;
});
await page.goto('http://localhost:5199/');

// ① 3回誤答 → ホームへ戻される
await page.click('[data-testid=btn-gear]');
for (let i = 0; i < 3; i++) {
  await page.click('[data-testid=key-1]'); // 1 は常に不正解（積は 12 以上）
  await page.click('[data-testid=key-OK]');
  await page.waitForTimeout(150);
}
const backHome = await page.locator('[data-testid=tile-hiragana]').isVisible();
console.log('3誤答でホームへ:', backHome);
if (!backHome) process.exitCode = 1;

// ② 正解して入る
await page.click('[data-testid=btn-gear]');
const qText = await page.locator('text=/\\d+ × \\d+/').textContent();
const m = qText!.match(/(\d+) × (\d+)/)!;
const answer = String(Number(m[1]) * Number(m[2]));
for (const d of answer) await page.click(`[data-testid=key-${d}]`);
await page.click('[data-testid=key-OK]');
await page.waitForSelector('text=保護者メニュー');
await page.screenshot({ path: `${outdir}/p6-dashboard.png` });

// ③ 設定変更（きびしい）→ IndexedDB 保存
await page.click('text=きびしい');
await page.waitForTimeout(300);

// ④ エクスポート
await page.click('[data-testid=btn-export]');
await page.waitForTimeout(300);
const io = await page.inputValue('[data-testid=io-text]');
const data = JSON.parse(io);
console.log('export ok:', data.app === 'kakijun', 'settings:', data.settings.strictness);
if (data.settings.strictness !== 'strict') process.exitCode = 1;

// ⑤ 再読込しても設定が残る
await page.reload();
await page.waitForTimeout(600);
await page.click('[data-testid=btn-gear]');
const qText2 = await page.locator('text=/\\d+ × \\d+/').textContent();
const m2 = qText2!.match(/(\d+) × (\d+)/)!;
for (const d of String(Number(m2[1]) * Number(m2[2]))) {
  await page.click(`[data-testid=key-${d}]`);
}
await page.click('[data-testid=key-OK]');
await page.waitForSelector('text=保護者メニュー');
const strictActive = await page
  .locator('button', { hasText: 'きびしい' })
  .evaluate((el) => getComputedStyle(el).fontWeight);
console.log('きびしい fontWeight (700=選択中):', strictActive);
if (strictActive !== '700') process.exitCode = 1;
await browser.close();
