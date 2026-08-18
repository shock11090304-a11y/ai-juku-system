/**
 * ★ お手本 (フォント) と判定線 (データ) の重ね合わせシート。
 *   npx vite-node tools/render/overlay-sheet.mts -- [--out FILE] [--cols N] [id|type|group...]
 *
 * compare-sheet.ts は左右に並べる (甘くならないように)。こちらは「同じマスに重ねる」。
 * 判定が見本からどれだけ浮いているかは、重ねないと分からないため。
 *
 * ★描画はアプリと同じ条件で行う: canvas・0.86em・textBaseline=middle・y=0.52。
 *   ここを SVG の text で代用すると基線がずれ、ありもしないズレを「発見」してしまう。
 * 判定線もアプリと同じ 64 点リサンプリング後の経路を描く (制御点の折れ線ではない)。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { toCharacterDef, resolveCharacter, toStroke, prepareStrokes, type MarkDef } from '../../src/engine/loader';
import type { CharacterDef, RawCharacterDef, RawStroke } from '../../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { refFontFaceCss, REF_FONT_FAMILY } from '../ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../../src/data/characters');
const argv = process.argv.slice(2).filter((a) => a !== '--');
const opt = (n: string, d: string) => {
  const i = argv.indexOf(`--${n}`);
  return i >= 0 ? argv[i + 1] : d;
};
const OUT = opt('out', '/tmp/overlay-sheet.png');
const COLS = Number(opt('cols', '8'));
const CELL = Number(opt('cell', '200'));
const filters = argv.filter((a, i) => !a.startsWith('--') && !argv[i - 1]?.startsWith('--'));

const files = ['hiragana.json', 'katakana.json', 'numbers.json', 'unpitsu.json'];
const all: RawCharacterDef[] = files.flatMap((f) =>
  fs.existsSync(path.join(dataDir, f))
    ? (JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[])
    : [],
);
const marksRaw = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8'),
) as MarkDef[];
const registry = new Map<string, CharacterDef>(all.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]));
const selected = [...registry.values()]
  .map((c) => resolveCharacter(c, registry, marks))
  .filter(
    (c) =>
      filters.length === 0 ||
      filters.includes(c.type) ||
      filters.includes(c.group) ||
      filters.includes(c.id),
  );

const cells = selected.map((c) => ({
  id: c.id,
  char: c.char,
  // 運筆はお手本フォントを使わない (線データがお手本)
  useFont: c.type !== 'unpitsu',
  strokes: prepareStrokes(c).map((s) => s.pts.map((p) => [p.x, p.y] as [number, number])),
}));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: COLS * (CELL + 8) + 16, height: 800 } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><style>${refFontFaceCss()}
   body{margin:0;background:#fafafa;font-family:sans-serif}
   .g{display:grid;grid-template-columns:repeat(${COLS},${CELL}px);gap:6px;padding:6px}
   figure{margin:0;background:#fff;border:1px solid #ddd;border-radius:4px}
   figcaption{font-size:11px;text-align:center;color:#666;padding:1px}
   </style><div class="g" id="g"></div>`,
);
await page.evaluate(async (family) => {
  await document.fonts.load(`100px ${family}`);
  await document.fonts.ready;
}, REF_FONT_FAMILY);

await page.evaluate(
  ({ cells, CELL, font }) => {
    const g = document.getElementById('g')!;
    for (const c of cells) {
      const fig = document.createElement('figure');
      const cv = document.createElement('canvas');
      cv.width = CELL;
      cv.height = CELL;
      cv.style.display = 'block';
      const ctx = cv.getContext('2d')!;
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, CELL, CELL);
      // マス目
      ctx.strokeStyle = '#eee';
      ctx.beginPath();
      ctx.moveTo(CELL / 2, 0);
      ctx.lineTo(CELL / 2, CELL);
      ctx.moveTo(0, CELL / 2);
      ctx.lineTo(CELL, CELL / 2);
      ctx.stroke();
      // ★ お手本: アプリの renderBackground と同一条件
      if (c.useFont) {
        ctx.fillStyle = '#cfd8dc';
        ctx.font = `${CELL * 0.86}px ${font}`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(c.char, CELL / 2, CELL * 0.52);
      }
      // 判定線 (リサンプリング後の実経路)
      ctx.strokeStyle = '#1e88e5';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.globalAlpha = 0.8;
      for (const pts of c.strokes) {
        ctx.beginPath();
        pts.forEach(([x, y], i) =>
          i ? ctx.lineTo(x * CELL, y * CELL) : ctx.moveTo(x * CELL, y * CELL),
        );
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
      // 書き出しの点
      ctx.fillStyle = '#fb8c00';
      c.strokes.forEach((pts, i) => {
        const [x, y] = pts[0];
        ctx.beginPath();
        ctx.arc(x * CELL, y * CELL, CELL * 0.03, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.font = `bold ${CELL * 0.035}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(i + 1), x * CELL, y * CELL);
        ctx.fillStyle = '#fb8c00';
      });
      fig.appendChild(cv);
      const cap = document.createElement('figcaption');
      cap.textContent = `${c.char} ${c.id}`;
      fig.appendChild(cap);
      g.appendChild(fig);
    }
  },
  { cells, CELL, font: REF_FONT_FAMILY },
);
await page.waitForTimeout(200);
await page.locator('.g').screenshot({ path: OUT });
await browser.close();
console.log(`${selected.length} 字 → ${OUT}`);
