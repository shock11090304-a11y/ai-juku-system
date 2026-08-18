/**
 * 濁点・半濁点が「お手本フォントが描いている記号の上」に乗っているかの検査。
 *   npx vite-node tools/check-mark-clearance.mts
 *
 * ★2026-08-17 に見るものを変えた。
 *   以前は「記号の中心線が基字の中心線から 0.11 以上離れているか」を見ていた。
 *   これは記号をマスの右上の隅に固定で置いていた時代の決まりで、
 *   フォントが゛を打つ位置とは無関係だった (実測で見えている゛と最大 34% ずれ、
 *   子どもは何も無いところを指して「ここから書け」と言われていた)。
 *   いまは tools/fit-marks.mts がフォントから実測した位置に記号を置く。
 *   そこで検査も「フォントの記号の墨に乗っているか」に変える。
 *
 * ★fit-marks とは独立の経路で確かめる (相互チェック):
 *   fit-marks は「差分の墨の外接箱の中心」を使う。こちらは
 *   「記号の全サンプル点が差分の墨の上にあるか」を距離で見る。
 *   markOffset の値は読まない (合成後の座標だけを見る)。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { splineSample } from '../src/engine/geometry';
import { toCharacterDef, resolveCharacter, toStroke, type MarkDef } from '../src/engine/loader';
import type { CharacterDef, RawCharacterDef, RawStroke } from '../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const files = ['hiragana.json', 'katakana.json', 'numbers.json'];
const all: RawCharacterDef[] = files.flatMap(
  (f) => JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
);
const marksRaw = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8'),
) as MarkDef[];
const registry = new Map<string, CharacterDef>(all.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]));

const S = 512;
const FRINGE = 3; // 輪郭の平滑化による 1〜2px の差は記号ではない
/** 記号の中心線が記号の墨から離れてよい上限 (マス1辺に対する比) */
const MAX_GAP = 0.05;

const composed = [...registry.values()].filter((c) => c.composedFrom);
const chars = new Set<string>();
for (const c of composed) {
  chars.add(c.char);
  chars.add(registry.get(c.composedFrom!.base)!.char);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
await useRefFont(page, [...chars]);
await page.evaluate(
  ({ S, font, fr, br }) => {
    const g = (document.getElementById('c') as HTMLCanvasElement).getContext('2d')!;
    (window as unknown as { maskOf: (ch: string) => Uint8Array }).maskOf = (ch: string) => {
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      g.font = `${S * fr}px "${font}"`; // アプリと同じ (sampleGlyph.ts)
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(ch, S / 2, S * br);
      const d = g.getImageData(0, 0, S, S).data;
      const m = new Uint8Array(S * S);
      for (let i = 0; i < S * S; i++) m[i] = d[i * 4] < 128 ? 1 : 0;
      return m;
    };
  },
  { S, font: REF_FONT_FAMILY, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
);

/** 記号の墨 (濁音グリフにだけある墨) までの距離マップ */
async function markInkDistance(baseCh: string, compCh: string): Promise<number[]> {
  return page.evaluate(
    ({ baseCh, compCh, S, FRINGE }) => {
      const maskOf = (window as unknown as { maskOf: (ch: string) => Uint8Array }).maskOf;
      const B = maskOf(baseCh);
      const C = maskOf(compCh);
      const near = new Uint8Array(S * S);
      for (let y = 0; y < S; y++)
        for (let x = 0; x < S; x++) {
          if (!B[y * S + x]) continue;
          for (let dy = -FRINGE; dy <= FRINGE; dy++)
            for (let dx = -FRINGE; dx <= FRINGE; dx++) {
              const yy = y + dy;
              const xx = x + dx;
              if (yy >= 0 && xx >= 0 && yy < S && xx < S) near[yy * S + xx] = 1;
            }
        }
      const dt = new Float32Array(S * S);
      for (let i = 0; i < S * S; i++) dt[i] = C[i] && !near[i] ? 0 : 1e6;
      for (let y = 0; y < S; y++)
        for (let x = 0; x < S; x++) {
          const i = y * S + x;
          let v = dt[i];
          if (y > 0) v = Math.min(v, dt[i - S] + 1);
          if (x > 0) v = Math.min(v, dt[i - 1] + 1);
          if (y > 0 && x > 0) v = Math.min(v, dt[i - S - 1] + 1.414);
          if (y > 0 && x < S - 1) v = Math.min(v, dt[i - S + 1] + 1.414);
          dt[i] = v;
        }
      for (let y = S - 1; y >= 0; y--)
        for (let x = S - 1; x >= 0; x--) {
          const i = y * S + x;
          let v = dt[i];
          if (y < S - 1) v = Math.min(v, dt[i + S] + 1);
          if (x < S - 1) v = Math.min(v, dt[i + 1] + 1);
          if (y < S - 1 && x < S - 1) v = Math.min(v, dt[i + S + 1] + 1.414);
          if (y < S - 1 && x > 0) v = Math.min(v, dt[i + S - 1] + 1.414);
          dt[i] = v;
        }
      return Array.from(dt);
    },
    { baseCh, compCh, S, FRINGE },
  );
}

let bad = 0;
let worst = 0;
for (const c of composed) {
  const base = registry.get(c.composedFrom!.base)!;
  const resolved = resolveCharacter(c, registry, marks);
  const dt = await markInkDistance(base.char, c.char);
  const markStrokes = resolved.strokes.slice(base.strokes.length);
  for (const s of markStrokes) {
    let maxGap = 0;
    for (const p of splineSample(s.points, 16)) {
      const x = Math.max(0, Math.min(S - 1, Math.round(p.x * S)));
      const y = Math.max(0, Math.min(S - 1, Math.round(p.y * S)));
      maxGap = Math.max(maxGap, dt[y * S + x] / S);
    }
    if (maxGap > MAX_GAP) {
      console.log(
        `NG ${c.char} (${c.id}) ${s.index}画目: 記号の墨から最大 ${(maxGap * 100).toFixed(1)}% 離れている`,
      );
      bad++;
    } else {
      worst = Math.max(worst, maxGap);
    }
  }
}
await browser.close();

if (bad === 0) {
  console.log(
    `OK: 全 ${composed.length} 合成字の濁点・半濁点がお手本の記号に乗っている (最大 ${(worst * 100).toFixed(1)}%)`,
  );
} else {
  console.log(`★ ${bad}画がお手本の記号から外れている`);
  process.exit(1);
}
