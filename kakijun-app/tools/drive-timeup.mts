/**
 * 開発検証 (Phase 6): 時間制限の発動 (§10.4)。
 * インポートで極小の制限を入れ、文字を1つ完走した後に
 * 「きょうは ここまで！」画面へ切り替わることを確認する。
 * （書いている途中では止めない、という仕様どおり完走後に発動する）
 */
import { chromium } from '@playwright/test';
import { getChar } from '../src/data';
import { prepareStrokes } from '../src/engine/loader';

const outdir = process.argv[2] ?? '/tmp';
const def = getChar('hira_i');
const strokes = prepareStrokes(def);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1180, height: 820 } });
page.on('pageerror', (err) => console.error('[pageerror]', err.message));
await page.goto('http://localhost:5199/');

// ゲートを解いて設定をインポート（1回の上限 ≈ 2秒）
await page.click('[data-testid=btn-gear]');
const qText = await page.locator('text=/\\d+ × \\d+/').textContent();
const m = qText!.match(/(\d+) × (\d+)/)!;
for (const d of String(Number(m[1]) * Number(m[2]))) {
  await page.click(`[data-testid=key-${d}]`);
}
await page.click('[data-testid=key-OK]');
await page.waitForSelector('text=保護者メニュー');
const payload = {
  app: 'kakijun',
  version: 1,
  progress: [],
  sessions: [],
  settings: {
    strictness: 'normal',
    sessionLimitMin: 0.03, // ≈2秒
    dailyLimitMin: null,
    voiceEnabled: false,
    sfxEnabled: false,
    showTypes: { hiragana: true, katakana: true, number: true, unpitsu: true },
  },
};
await page.fill('[data-testid=io-text]', JSON.stringify(payload));
await page.click('[data-testid=btn-import]');
await page.waitForTimeout(400);
await page.click('[data-testid=btn-back]');

// 練習して完走（2秒は超える）
await page.click('[data-testid=tile-hiragana]');
await page.click('[data-testid=char-hira_i]');
await page.waitForSelector('[data-testid=practice-canvas] canvas');
await page.waitForTimeout(2500);
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
// 完走が認められた上で、閉じたら時間切れ画面へ
await page.click('[data-testid=btn-next]');
await page.waitForSelector('text=きょうは ここまで！');
await page.screenshot({ path: `${outdir}/p6-timeup.png` });
console.log('time-up screen: OK');
await browser.close();
