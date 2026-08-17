/**
 * 開発用スクリーンショットツール。
 *   node tools/shot.mjs <url> <out.png> [width] [height]
 * iPad 横向き相当 (1180x820) が既定。
 */
import fs from 'node:fs';
import { chromium } from '@playwright/test';

const [url, out, w = '1180', h = '820'] = process.argv.slice(2);
if (!url || !out) {
  console.error('usage: node tools/shot.mjs <url> <out.png> [w] [h]');
  process.exit(1);
}

async function launch() {
  try {
    return await chromium.launch();
  } catch {
    // 環境のプリインストール Chromium にフォールバック
    const exe = '/opt/pw-browsers/chromium';
    if (fs.existsSync(exe)) return chromium.launch({ executablePath: exe });
    throw new Error('no chromium available');
  }
}

const browser = await launch();
const page = await browser.newPage({
  viewport: { width: Number(w), height: Number(h) },
});
page.on('console', (msg) => {
  if (msg.type() === 'error') console.error('[console.error]', msg.text());
});
page.on('pageerror', (err) => console.error('[pageerror]', err.message));
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(500);
await page.screenshot({ path: out });
await browser.close();
console.log('saved:', out);
