/**
 * ★ 書き出しの点が「お手本の字の上」に乗っているかの全数検査。
 *   npx vite-node tools/check-start-dots.mts -- [--max 0.05] [id...]
 *
 * 経路表示をやめた (PR #39) ので、いま書き順を伝えているのは
 * 「番号 + 書き出しの点」だけ。その点がお手本の墨から浮いていると、
 * 子どもは何も無いところを指して「ここから書け」と言われることになる。
 * 見た目の破綻なのに、判定は許容幅が広いので自動テストは緑のまま通る。
 *
 * お手本 = 出荷している woff2 (画面に出ている字そのもの)。
 * 判定 = 線データ。両者は別物なので、ここでズレを数える。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { toCharacterDef, resolveCharacter, toStroke, type MarkDef } from '../src/engine/loader';
import type { CharacterDef, RawCharacterDef, RawStroke } from '../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const args = process.argv.slice(2).filter((a) => a !== '--');
const maxArg = args.indexOf('--max');
/** 許容ズレ (マス1辺に対する比)。お手本の線の太さの半分 ≒ 0.05 */
const MAX = maxArg >= 0 ? Number(args[maxArg + 1]) : 0.05;
const only = args.filter((a, i) => !a.startsWith('--') && args[i - 1] !== '--max');
const S = 512;

const files = ['hiragana.json', 'katakana.json', 'numbers.json'];
const all: RawCharacterDef[] = files.flatMap(
  (f) => JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
);
const marksRaw = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8'),
) as MarkDef[];
const registry = new Map<string, CharacterDef>(all.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]));
// 運筆はお手本を線データから描くので (フォントに字形が無い) 検査対象外
const targets = [...registry.values()]
  .map((c) => resolveCharacter(c, registry, marks))
  .filter((c) => only.length === 0 || only.includes(c.id));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
await useRefFont(
  page,
  targets.map((t) => t.char),
);

/** 墨までの距離マップ (px)。墨の中は 0 */
async function inkDistance(ch: string): Promise<Float32Array> {
  const mask = await page.evaluate(
    ({ ch, S, font }) => {
      const g = (document.getElementById('c') as HTMLCanvasElement).getContext('2d')!;
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      // ★ アプリの renderBackground と同じ配置 (0.86em・中央・y=0.52)
      g.font = `${S * 0.86}px "${font}"`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(ch, S / 2, S * 0.52);
      const d = g.getImageData(0, 0, S, S).data;
      const out: number[] = [];
      for (let i = 0; i < S * S; i++) out.push(d[i * 4] < 128 ? 1 : 0);
      return out;
    },
    { ch, S, font: REF_FONT_FAMILY },
  );
  const dt = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) dt[i] = mask[i] ? 0 : 1e6;
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
  return dt;
}

type Bad = { id: string; char: string; stroke: number; gap: number };
const bad: Bad[] = [];
let worstOk = 0;
for (const c of targets) {
  const dt = await inkDistance(c.char);
  for (const s of c.strokes) {
    const p = s.points[0];
    const x = Math.round(p.x * S);
    const y = Math.round(p.y * S);
    const px = Math.max(0, Math.min(S - 1, x));
    const py = Math.max(0, Math.min(S - 1, y));
    const gap = dt[py * S + px] / S; // マス1辺に対する比
    if (gap > MAX) bad.push({ id: c.id, char: c.char, stroke: s.index, gap });
    else worstOk = Math.max(worstOk, gap);
  }
}
await browser.close();

console.log(
  `書き出しの点がお手本の墨から離れていないか: ${targets.length}字 / 許容 ${(MAX * 100).toFixed(1)}%`,
);
if (bad.length === 0) {
  console.log(`OK: 全画が許容内 (最大 ${(worstOk * 100).toFixed(1)}%)`);
} else {
  bad.sort((a, b) => b.gap - a.gap);
  console.log(`★ ${bad.length}画が浮いている (悪い順):`);
  for (const b of bad) {
    console.log(`  ${b.char} ${b.id.padEnd(16)} ${b.stroke}画目  ${(b.gap * 100).toFixed(1)}%`);
  }
  process.exit(1); // ★ 検査は必ず落とす。印字だけして exit 0 にしない
}
