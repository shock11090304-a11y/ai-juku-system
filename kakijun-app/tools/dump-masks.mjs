/**
 * 対象文字ぶんの手本グリフマスクをまとめて出力する (Chromium 1回起動)。
 *   node tools/dump-masks.mjs /tmp/masks
 * 対象: hiragana/katakana/numbers の合成でない字 (小書き・濁音は基字から派生)。
 */
import { chromium } from 'playwright';
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from './ref-font.mjs';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const [outDir] = process.argv.slice(2);
// ★ 出荷している woff2 を測る (tools/ref-font.mjs)。system フォント名で引かない
const font = REF_FONT_FAMILY;
fs.mkdirSync(outDir, { recursive: true });
const S = 512;

const chars = [];
for (const f of ['hiragana.json', 'katakana.json', 'numbers.json']) {
  const list = JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8'));
  for (const c of list) {
    if (c.composedFrom || c.group === 'youon') continue;
    chars.push({ id: c.id, char: c.char });
  }
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
await useRefFont(page, chars.map((c) => c.char));

for (const { id, char } of chars) {
  const bits = await page.evaluate(
    ({ ch, S, font, fr, br }) => {
      const g = document.getElementById('c').getContext('2d');
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      // ★ アプリの renderBackground と同一条件 (src/canvas/sampleGlyph.ts)
      g.font = `${S * fr}px "${font}"`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(ch, S / 2, S * br);
      const d = g.getImageData(0, 0, S, S).data;
      // 行ごとの ink 区間 (x開始,x終了) に圧縮して軽くする
      const runs = [];
      for (let y = 0; y < S; y++) {
        let x = 0;
        while (x < S) {
          if (d[(y * S + x) * 4] < 128) {
            const s = x;
            while (x < S && d[(y * S + x) * 4] < 128) x++;
            runs.push([y, s, x - 1]);
          } else x++;
        }
      }
      return runs;
    },
    { ch: char, S, font, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
  );
  fs.writeFileSync(path.join(outDir, `${id}.json`), JSON.stringify({ id, char, size: S, runs: bits }));
}
await browser.close();
console.log(`${chars.length} 字のマスクを ${outDir} へ`);
