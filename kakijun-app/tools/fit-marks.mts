/**
 * ★ 濁点・半濁点を「お手本フォントが実際に描いている位置」へ合わせる。
 *   npx vite-node tools/fit-marks.mts -- [--apply]
 *
 * 濁音の合成は marks.json の固定座標 (右上の隅) を全字で使い回していたが、
 * フォントが゛を打つ位置は字ごとに違う。結果、書き出しの点だけが右上の隅に
 * 浮き、見えている゛とは無関係な場所を指していた (実測で最大 34%)。
 * 経路表示をやめた今、書き出しの点は書き順を伝える唯一の手がかりなので、
 * ここがズレていると「何も無いところから書け」と言っていることになる。
 *
 * 測り方: 基字グリフと濁音グリフの墨を比べ、濁音側にだけある墨 (= ゛ / ゜) の
 * 位置を取る。輪郭の平滑化による1〜2px の差は距離で落とす。
 * 得られた移動量を composedFrom.markOffset に書き、loader が適用する。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import type { RawCharacterDef } from '../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const args = process.argv.slice(2).filter((a) => a !== '--');
const APPLY = args.includes('--apply');
const S = 512;
const FRINGE = 3; // 輪郭の平滑化差を無視する距離 (px)

const FILES = ['hiragana.json', 'katakana.json'];
type Bundle = { file: string; list: RawCharacterDef[] };
const bundles: Bundle[] = FILES.map((f) => ({
  file: f,
  list: JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
}));
const byId = new Map<string, RawCharacterDef>();
for (const b of bundles) for (const c of b.list) byId.set(c.id, c);

const marksRaw = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8'),
) as { id: string; strokes: { points: [number, number][] }[] }[];
/** マーク定義そのものの中心 (制御点の外接箱の中心) */
const markCenter = new Map<string, { x: number; y: number }>(
  marksRaw.map((m) => {
    const pts = m.strokes.flatMap((s) => s.points);
    const xs = pts.map((p) => p[0]);
    const ys = pts.map((p) => p[1]);
    return [
      m.id,
      { x: (Math.min(...xs) + Math.max(...xs)) / 2, y: (Math.min(...ys) + Math.max(...ys)) / 2 },
    ];
  }),
);

const targets = [...byId.values()].filter((c) => c.composedFrom);
const chars = new Set<string>();
for (const c of targets) {
  chars.add(c.char);
  chars.add(byId.get(c.composedFrom!.base)!.char);
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
      // アプリの renderBackground と同じ配置
      g.font = `${S * fr}px "${font}"`;
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

/** 濁音側にだけある墨の外接箱の中心 (正規化座標) */
async function markInkCenter(baseCh: string, compCh: string) {
  return page.evaluate(
    ({ baseCh, compCh, S, FRINGE }) => {
      const maskOf = (window as unknown as { maskOf: (ch: string) => Uint8Array }).maskOf;
      const B = maskOf(baseCh);
      const C = maskOf(compCh);
      // 基字の墨からの距離 (チェビシェフ距離で十分)
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
      let minX = 1e9;
      let minY = 1e9;
      let maxX = -1;
      let maxY = -1;
      let n = 0;
      for (let i = 0; i < S * S; i++) {
        if (!C[i] || near[i]) continue;
        const x = i % S;
        const y = (i / S) | 0;
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
        n++;
      }
      return { n, cx: (minX + maxX) / 2 / S, cy: (minY + maxY) / 2 / S, w: (maxX - minX) / S, h: (maxY - minY) / S };
    },
    { baseCh, compCh, S, FRINGE },
  );
}

const rows: string[] = [];
let failed = 0;
for (const c of targets) {
  const base = byId.get(c.composedFrom!.base)!;
  const markId = c.composedFrom!.marks[0];
  const mc = markCenter.get(markId)!;
  const ink = await markInkCenter(base.char, c.char);
  // 濁点は 2 画・半濁点は輪。どちらもマス1辺の 1〜2 割に収まる小さな塊。
  // それより大きい/小さい塊が出たら、基字が動いた等で差分が濁点になっていない
  if (ink.n < 60 || ink.w > 0.3 || ink.h > 0.3) {
    console.log(`  ★ ${c.char} (${c.id}): 差分が ${markId} らしくない (px=${ink.n} w=${ink.w.toFixed(2)} h=${ink.h.toFixed(2)}) → 触らない`);
    failed++;
    continue;
  }
  const dx = Number((ink.cx - mc.x).toFixed(3));
  const dy = Number((ink.cy - mc.y).toFixed(3));
  rows.push(`  ${c.char} ${c.id.padEnd(15)} ${markId.replace('mark_', '').padEnd(11)} → [${dx.toFixed(3)}, ${dy.toFixed(3)}]`);
  if (APPLY) c.composedFrom!.markOffset = [dx, dy];
}
await browser.close();

console.log(`濁点・半濁点をフォントの位置へ合わせる (${targets.length}字):`);
for (const r of rows) console.log(r);
if (failed) console.log(`★ ${failed}字は測れなかった`);

if (APPLY) {
  for (const b of bundles) {
    fs.writeFileSync(path.join(dataDir, b.file), JSON.stringify(b.list, null, 2) + '\n');
  }
  console.log('JSON を更新した');
} else {
  console.log('(測定のみ。書き換えるには --apply)');
}
