/** 一時調査: お手本の墨を細線化して「線の行き止まり (tip)」の座標を印字する。
 *  画の書き出し・終わりの候補はここにしか無い。
 *  npx vite-node tools/_tips.mts -- hira_ya hira_wa ...
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { prepareStrokes, toCharacterDef, resolveCharacter, toStroke, type MarkDef } from '../src/engine/loader';
import type { CharacterDef, RawCharacterDef, RawStroke } from '../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const only = process.argv.slice(2).filter((a) => a !== '--');
const S = 512;
const files = ['hiragana.json', 'katakana.json', 'numbers.json'];
const all: RawCharacterDef[] = files.flatMap(
  (f) => JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
);
const marksRaw = JSON.parse(fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8')) as MarkDef[];
const registry = new Map<string, CharacterDef>(all.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]));
const targets = [...registry.values()]
  .map((c) => resolveCharacter(c, registry, marks))
  .filter((c) => only.includes(c.id));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
await useRefFont(page, targets.map((t) => t.char));

function thin(src: Uint8Array): Uint8Array {
  const img = Uint8Array.from(src);
  const at = (x: number, y: number): number => (x < 0 || y < 0 || x >= S || y >= S ? 0 : img[y * S + x]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const step of [0, 1]) {
      const del: number[] = [];
      for (let y = 1; y < S - 1; y++)
        for (let x = 1; x < S - 1; x++) {
          if (!img[y * S + x]) continue;
          const p = [at(x, y - 1), at(x + 1, y - 1), at(x + 1, y), at(x + 1, y + 1),
            at(x, y + 1), at(x - 1, y + 1), at(x - 1, y), at(x - 1, y - 1)];
          const b = p.reduce((a, v) => a + v, 0);
          if (b < 2 || b > 6) continue;
          let a = 0;
          for (let i = 0; i < 8; i++) if (!p[i] && p[(i + 1) % 8]) a++;
          if (a !== 1) continue;
          if (step === 0) {
            if (p[0] * p[2] * p[4]) continue;
            if (p[2] * p[4] * p[6]) continue;
          } else {
            if (p[0] * p[2] * p[6]) continue;
            if (p[0] * p[4] * p[6]) continue;
          }
          del.push(y * S + x);
        }
      if (del.length) {
        changed = true;
        for (const i of del) img[i] = 0;
      }
    }
  }
  return img;
}

for (const c of targets) {
  const bits = await page.evaluate(
    ({ ch, S, font, fr, br }) => {
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
    { ch: c.char, S, font: REF_FONT_FAMILY, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
  );
  const sk = thin(Uint8Array.from(bits));
  const tips: [number, number][] = [];
  for (let y = 1; y < S - 1; y++)
    for (let x = 1; x < S - 1; x++) {
      if (!sk[y * S + x]) continue;
      let n = 0;
      for (let dy = -1; dy <= 1; dy++)
        for (let dx = -1; dx <= 1; dx++) {
          if (!dx && !dy) continue;
          if (sk[(y + dy) * S + (x + dx)]) n++;
        }
      if (n === 1) tips.push([x / S, y / S]);
    }
  const merged: [number, number][] = [];
  for (const t of tips) {
    if (!merged.some((m) => Math.hypot(m[0] - t[0], m[1] - t[1]) < 0.03)) merged.push(t);
  }
  console.log(`== ${c.char} ${c.id}`);
  console.log(
    '  墨の端: ' + merged.map(([x, y]) => `(${x.toFixed(3)},${y.toFixed(3)})`).join(' '),
  );
  prepareStrokes(c).forEach((s, i) => {
    console.log(
      `  ${i + 1}画: start=(${s.pts[0].x.toFixed(3)},${s.pts[0].y.toFixed(3)}) end=(${s.pts[63].x.toFixed(3)},${s.pts[63].y.toFixed(3)})`,
    );
  });
}
await browser.close();
