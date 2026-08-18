/**
 * ★ お手本の墨のうち「どの画も通っていない」場所を赤で見せる目視用シート。
 *   npx vite-node tools/render/coverage-sheet.mts -- [--min 900] [--dump FILE] [id...]
 *
 * check-start-dots は「書き出しの点が墨の上にあるか」しか見ない。
 * ところが**別の画の墨の上**でも合格してしまうので、
 *   ・や = 長い斜め画が2本に割れ、右上の点には画が1本も無い
 *   ・わ = 2画目の書き出しが1画目 (縦) の頭に吸着し、横棒の左半分が誰にも書かれない
 *   ・を = 2画目が1画目の墨をなぞり、本来の縦カーブが残る
 * といった「画の切り分けそのものが違う」事故が全部すり抜けていた
 * (2026-08-18 塾長が実練習で や・を・わ を発見)。
 *
 * 判定は「書き出しの位置と順番」だけになったので、画の切り分けが違う =
 * 子どもが「そこには何も無い場所」から書かされる、そのものになる。
 *
 * 覆われていない墨のかたまり (連結成分) が MIN 画素以上あれば違反。
 * 運筆はお手本をフォントで描かないので対象外。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { prepareStrokes, toCharacterDef, resolveCharacter, toStroke, type MarkDef } from '../../src/engine/loader';
import type { CharacterDef, RawCharacterDef, RawStroke } from '../../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from '../ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../../src/data/characters');
const args = process.argv.slice(2).filter((a) => a !== '--');
const opt = (n: string, d: string): string => {
  const i = args.indexOf(`--${n}`);
  return i >= 0 ? args[i + 1] : d;
};
/**
 * 見逃す大きさの上限 (画素)。お手本の線の太さは 0.04 マス ≒ 20px なので、
 * 900px ≒ 長さ 0.09 マスぶんの線。これ以上の墨が放置されていたら
 * 「画が1本足りない/ずれている」と見てよい。
 */
const MIN = Number(opt('min', '900'));
const DUMP = opt('dump', '');
/** 未踏の墨を赤で塗った検証シートの書き出し先 (目視用) */
const RENDER = opt('render', '');
/** 画の帯の半径。線の太さの半分 (0.021) + 合わせ込みのずれ ぶん */
const BAND = Number(opt('band', '0.035'));
const only = args.filter((a, i) => !a.startsWith('--') && !args[i - 1]?.startsWith('--'));
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

async function maskOf(ch: string): Promise<Uint8Array> {
  const bits = await page.evaluate(
    ({ ch, S, font, fr, br }) => {
      const g = (document.getElementById('c') as HTMLCanvasElement).getContext('2d')!;
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      // ★ アプリの renderBackground と同一条件 (0.86em・中央・y=0.52)
      g.font = `${S * fr}px "${font}"`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(ch, S / 2, S * br);
      const d = g.getImageData(0, 0, S, S).data;
      const out: number[] = [];
      for (let i = 0; i < S * S; i++) out.push(d[i * 4] < 128 ? 1 : 0);
      return out;
    },
    { ch, S, font: REF_FONT_FAMILY, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
  );
  return Uint8Array.from(bits);
}

/** 墨の中の各画素から「墨の外」までの距離 (= その場所の線の太さの半分) */
function insideDistance(mask: Uint8Array): Float32Array {
  const dt = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) dt[i] = mask[i] ? 1e6 : 0;
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

type Hole = { size: number; x0: number; x1: number; y0: number; y1: number };
type Row = { id: string; char: string; holes: Hole[]; inkPx: number };

const rows: Row[] = [];
/** --render 用: 未踏の墨の座標 (間引き済み) と判定線 */
const shots: { id: string; char: string; pts: number[][]; strokes: number[][][] }[] = [];
for (const c of targets) {
  const mask = await maskOf(c.char);
  // ★帯の太さは墨の実測幅に合わせる。固定幅にすると起筆・角の「太い墨」が
  //   覆いきれず、切り分けは正しいのに違反として出てしまう
  const inside = insideDistance(mask);
  const covered = new Uint8Array(S * S);
  const RMIN = Math.round(BAND * S);
  const RMAX = Math.round(0.075 * S);
  for (const s of prepareStrokes(c)) {
    for (const p of s.pts) {
      const cx = Math.round(p.x * S);
      const cy = Math.round(p.y * S);
      const local =
        cx >= 0 && cy >= 0 && cx < S && cy < S ? inside[cy * S + cx] * 1.6 : 0;
      const R = Math.max(RMIN, Math.min(RMAX, Math.round(local)));
      for (let dy = -R; dy <= R; dy++) {
        for (let dx = -R; dx <= R; dx++) {
          if (dx * dx + dy * dy > R * R) continue;
          const x = cx + dx;
          const y = cy + dy;
          if (x >= 0 && y >= 0 && x < S && y < S) covered[y * S + x] = 1;
        }
      }
    }
  }
  // 覆われていない墨の連結成分
  const seen = new Uint8Array(S * S);
  const holes: Hole[] = [];
  let inkPx = 0;
  for (let i = 0; i < S * S; i++) if (mask[i]) inkPx++;
  for (let i = 0; i < S * S; i++) {
    if (!mask[i] || covered[i] || seen[i]) continue;
    const q = [i];
    seen[i] = 1;
    let size = 0;
    let x0 = S;
    let x1 = 0;
    let y0 = S;
    let y1 = 0;
    while (q.length) {
      const j = q.pop()!;
      size++;
      const x = j % S;
      const y = (j / S) | 0;
      if (x < x0) x0 = x;
      if (x > x1) x1 = x;
      if (y < y0) y0 = y;
      if (y > y1) y1 = y;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
        const k = ny * S + nx;
        if (mask[k] && !covered[k] && !seen[k]) {
          seen[k] = 1;
          q.push(k);
        }
      }
    }
    if (size >= MIN) holes.push({ size, x0, x1, y0, y1 });
  }
  holes.sort((a, b) => b.size - a.size);
  rows.push({ id: c.id, char: c.char, holes, inkPx });
  if (RENDER && holes.length) {
    const pts: number[][] = [];
    for (let y = 0; y < S; y += 2)
      for (let x = 0; x < S; x += 2) {
        const i = y * S + x;
        if (mask[i] && !covered[i]) pts.push([x / S, y / S]);
      }
    shots.push({
      id: c.id,
      char: c.char,
      pts,
      strokes: prepareStrokes(c).map((s) => s.pts.map((p) => [p.x, p.y])),
    });
  }
}

// ★ 目で確かめるための検証シート: お手本=灰・未踏の墨=赤・判定線=青
if (RENDER && shots.length) {
  const CELL = Number(opt('cell', '220'));
  const COLS = Number(opt('cols', '9'));
  const page2 = await browser.newPage({
    viewport: { width: COLS * (CELL + 8) + 16, height: 900 },
  });
  // @ts-expect-error 型定義のない開発用ヘルパ
  const { refFontFaceCss } = await import('../ref-font.mjs');
  await page2.setContent(
    `<!doctype html><meta charset="utf-8"><style>${refFontFaceCss()}
     body{margin:0;background:#fafafa;font-family:sans-serif}
     .g{display:grid;grid-template-columns:repeat(${COLS},${CELL}px);gap:6px;padding:6px}
     figure{margin:0;background:#fff;border:1px solid #ddd;border-radius:4px}
     figcaption{font-size:10px;text-align:center;color:#666}</style><div class="g" id="g"></div>`,
  );
  await page2.evaluate(async (family) => {
    await document.fonts.load(`100px ${family}`);
    await document.fonts.ready;
  }, REF_FONT_FAMILY);
  await page2.evaluate(
    ({ shots, CELL, font, fr, br }) => {
      const g = document.getElementById('g')!;
      for (const s of shots) {
        const fig = document.createElement('figure');
        const cv = document.createElement('canvas');
        cv.width = CELL;
        cv.height = CELL;
        cv.style.display = 'block';
        const ctx = cv.getContext('2d')!;
        ctx.fillStyle = '#fff';
        ctx.fillRect(0, 0, CELL, CELL);
        ctx.fillStyle = '#cfd8dc';
        ctx.font = `${CELL * fr}px ${font}`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(s.char, CELL / 2, CELL * br);
        ctx.fillStyle = 'rgba(229,57,53,0.85)'; // 未踏の墨
        for (const [x, y] of s.pts) ctx.fillRect(x * CELL, y * CELL, 1.4, 1.4);
        ctx.strokeStyle = '#1e88e5';
        ctx.lineWidth = 1.6;
        for (const pts of s.strokes) {
          ctx.beginPath();
          pts.forEach(([x, y], i) =>
            i ? ctx.lineTo(x * CELL, y * CELL) : ctx.moveTo(x * CELL, y * CELL),
          );
          ctx.stroke();
        }
        ctx.fillStyle = '#fb8c00';
        s.strokes.forEach((pts, i) => {
          const [x, y] = pts[0];
          ctx.beginPath();
          ctx.arc(x * CELL, y * CELL, CELL * 0.028, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = '#fff';
          ctx.font = `bold ${CELL * 0.035}px sans-serif`;
          ctx.fillText(String(i + 1), x * CELL, y * CELL);
          ctx.fillStyle = '#fb8c00';
        });
        fig.appendChild(cv);
        const cap = document.createElement('figcaption');
        cap.textContent = `${s.char} ${s.id}`;
        fig.appendChild(cap);
        g.appendChild(fig);
      }
    },
    { shots, CELL, font: REF_FONT_FAMILY, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
  );
  await page2.waitForTimeout(300);
  await page2.locator('.g').screenshot({ path: RENDER });
  console.log(`検証シート (未踏の墨を赤で表示): ${RENDER}`);
}
await browser.close();

const bad = rows.filter((r) => r.holes.length);
console.log(
  `お手本の墨に「どの画も通っていない場所」が無いか: ${targets.length}字 / 見逃す上限 ${MIN}px・帯半径 ${(BAND * 100).toFixed(1)}%`,
);
for (const r of bad) {
  const total = r.holes.reduce((a, h) => a + h.size, 0);
  console.log(
    `NG ${r.char} ${r.id.padEnd(16)} 未踏の墨 ${r.holes.length}か所 計${total}px (墨全体の${((total / r.inkPx) * 100).toFixed(1)}%)`,
  );
  for (const h of r.holes) {
    console.log(
      `     ${String(h.size).padStart(5)}px  x=${(h.x0 / S).toFixed(3)}..${(h.x1 / S).toFixed(3)} y=${(h.y0 / S).toFixed(3)}..${(h.y1 / S).toFixed(3)}`,
    );
  }
}
if (DUMP) {
  fs.writeFileSync(DUMP, JSON.stringify(rows, null, 2) + '\n');
  console.log(`(全結果を ${DUMP} に書き出した)`);
}
// ★これは目視用の診断ツール (落とさない)。輪の内側を線がショートカットしている
//   だけの字も赤くなるため、これ単体では合否を決められない。
//   機械で落とすのは tools/check-stroke-segmentation.mts の2規則。
console.log(
  bad.length
    ? `${bad.length}字に未踏の墨がある。赤が「書き出しの手前」に続いていたら書き順の案内が壊れている`
    : '全字の墨がいずれかの画に覆われている',
);
