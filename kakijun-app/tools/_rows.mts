/** 一時調査: 指定した字の墨の連結成分と、行ごとの x 区間を印字する */
import { chromium } from 'playwright';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from './ref-font.mjs';
const S = 512;
const CH = process.argv.slice(2).filter((a) => a !== '--')[0] ?? 'ふ';
const STEP = Number(process.argv.slice(2).filter((a) => a !== '--')[1] ?? '7');
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
await useRefFont(page, [CH]);
const mask: number[] = await page.evaluate(
  ({ S, ch, font, fr, br }) => {
    const g = (document.getElementById('c') as HTMLCanvasElement).getContext('2d')!;
    g.fillStyle = '#fff';
    g.fillRect(0, 0, S, S);
    g.fillStyle = '#000';
    g.font = `${S * fr}px "${font}"`;
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText(ch, S / 2, S * br);
    const d = g.getImageData(0, 0, S, S).data;
    const out: number[] = [];
    for (let i = 0; i < S * S; i++) out.push(d[i * 4] < 128 ? 1 : 0);
    return out;
  },
  { S, ch: CH, font: REF_FONT_FAMILY, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
);
await browser.close();
const comp = new Int32Array(S * S).fill(-1);
let nc = 0;
const sizes: number[] = [];
for (let i = 0; i < S * S; i++) {
  if (!mask[i] || comp[i] >= 0) continue;
  const q = [i];
  comp[i] = nc;
  let sz = 0;
  while (q.length) {
    const j = q.pop()!;
    sz++;
    const x = j % S;
    const y = (j / S) | 0;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
      const k = ny * S + nx;
      if (mask[k] && comp[k] < 0) {
        comp[k] = nc;
        q.push(k);
      }
    }
  }
  sizes.push(sz);
  nc++;
}
for (let cidx = 0; cidx < nc; cidx++) {
  if (sizes[cidx] < 40) continue;
  let x0 = S, x1 = 0, y0 = S, y1 = 0;
  for (let i = 0; i < S * S; i++)
    if (comp[i] === cidx) {
      const x = i % S;
      const y = (i / S) | 0;
      x0 = Math.min(x0, x);
      x1 = Math.max(x1, x);
      y0 = Math.min(y0, y);
      y1 = Math.max(y1, y);
    }
  console.log(
    `comp${cidx} size=${sizes[cidx]} x=${(x0 / S).toFixed(3)}..${(x1 / S).toFixed(3)} y=${(y0 / S).toFixed(3)}..${(y1 / S).toFixed(3)}`,
  );
  for (let y = y0; y <= y1; y += STEP) {
    const runs: string[] = [];
    let s = -1;
    for (let x = x0; x <= x1 + 1; x++) {
      const on = x <= x1 && comp[y * S + x] === cidx;
      if (on && s < 0) s = x;
      if (!on && s >= 0) {
        runs.push(`${(s / S).toFixed(3)}-${(x / S).toFixed(3)}`);
        s = -1;
      }
    }
    if (runs.length) console.log(`  y=${(y / S).toFixed(3)}: ${runs.join(' ')}`);
  }
}
