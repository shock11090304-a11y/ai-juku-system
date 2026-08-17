/**
 * 手本フォントのグリフを 512x512 の白黒マスクにして JSON で吐く。
 * 字形照合 (中心線スナップ・忠実度検査) の入力にする。
 *   node tools/glyph-mask.mjs お /tmp/mask-o.json ["Klee One"]
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const [ch, out, font = 'Klee One'] = process.argv.slice(2);
const S = 512;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0">
   <canvas id="c" width="${S}" height="${S}"></canvas>`,
);
await page.evaluate(async () => {
  // フォント読込を待つ (未読込だと代替フォントで測ってしまう)
  await document.fonts.ready;
});
const mask = await page.evaluate(
  ({ ch, S, font }) => {
    const c = document.getElementById('c');
    const g = c.getContext('2d');
    g.fillStyle = '#fff';
    g.fillRect(0, 0, S, S);
    g.fillStyle = '#000';
    g.font = `${S * 0.88}px "${font}"`;
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText(ch, S / 2, S / 2);
    const d = g.getImageData(0, 0, S, S).data;
    const bits = new Array(S * S);
    for (let i = 0; i < S * S; i++) bits[i] = d[i * 4] < 128 ? 1 : 0;
    return bits;
  },
  { ch, S, font },
);
await browser.close();

const ink = mask.reduce((a, b) => a + b, 0);
fs.writeFileSync(out, JSON.stringify({ char: ch, size: S, font, mask }));
console.log(`${ch} (${font}) → ${out}  ink=${((ink / (S * S)) * 100).toFixed(1)}%`);
