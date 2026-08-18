/**
 * 手本グリフのマスクから距離変換を作り、現行ストロークの中心線を
 * 「墨の中心 (medial axis)」へスナップして忠実な制御点を出す。
 *
 *   node tools/glyph-mask.mjs お /tmp/mask-o.json
 *   npx vite-node tools/snap-to-glyph.mts -- hira_o /tmp/mask-o.json [画番号...]
 *
 * 出力: スナップ後の制御点 (JSON) と、各点の墨内外・中心からのズレの統計。
 * 近傍探索の半径を絞ってあるので、隣接する別画へ飛び移ることはない。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { splineSample } from '../src/engine/geometry';
import type { RawCharacterDef, Pt } from '../src/engine/types';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');

const [charId, maskPath, ...strokeArgs] = process.argv.slice(2).filter((a) => a !== '--');
const targetStrokes = strokeArgs.map(Number);

const files = ['hiragana.json', 'katakana.json', 'numbers.json', 'unpitsu.json'];
let def: RawCharacterDef | undefined;
let srcFile = '';
for (const f of files) {
  const p = path.join(dataDir, f);
  if (!fs.existsSync(p)) continue;
  const arr = JSON.parse(fs.readFileSync(p, 'utf8')) as RawCharacterDef[];
  const found = arr.find((c) => c.id === charId);
  if (found) {
    def = found;
    srcFile = f;
    break;
  }
}
if (!def) throw new Error(`not found: ${charId}`);

const { size: S, mask } = JSON.parse(fs.readFileSync(maskPath, 'utf8')) as {
  size: number;
  mask: number[];
};
const at = (x: number, y: number) =>
  x < 0 || y < 0 || x >= S || y >= S ? 0 : mask[y * S + x];

// 墨からの距離変換 (2パス chamfer)。墨の内側ほど値が大きい。
const dt = new Float32Array(S * S);
const BIG = 1e9;
for (let i = 0; i < S * S; i++) dt[i] = mask[i] ? BIG : 0;
for (let y = 0; y < S; y++) {
  for (let x = 0; x < S; x++) {
    const i = y * S + x;
    if (!mask[i]) continue;
    let v = dt[i];
    if (y > 0) v = Math.min(v, dt[i - S] + 1);
    if (x > 0) v = Math.min(v, dt[i - 1] + 1);
    if (y > 0 && x > 0) v = Math.min(v, dt[i - S - 1] + 1.414);
    if (y > 0 && x < S - 1) v = Math.min(v, dt[i - S + 1] + 1.414);
    dt[i] = v;
  }
}
for (let y = S - 1; y >= 0; y--) {
  for (let x = S - 1; x >= 0; x--) {
    const i = y * S + x;
    if (!mask[i]) continue;
    let v = dt[i];
    if (y < S - 1) v = Math.min(v, dt[i + S] + 1);
    if (x < S - 1) v = Math.min(v, dt[i + 1] + 1);
    if (y < S - 1 && x < S - 1) v = Math.min(v, dt[i + S + 1] + 1.414);
    if (y < S - 1 && x > 0) v = Math.min(v, dt[i + S - 1] + 1.414);
    dt[i] = v;
  }
}
const dtAt = (x: number, y: number) =>
  x < 0 || y < 0 || x >= S || y >= S ? 0 : dt[y * S + x];

/** 進行方向に直交する向きだけを探索して、局所的に最も太い位置 (中心) へ寄せる */
function snap(p: Pt, tangent: Pt, radiusPx: number): { pt: Pt; inside: boolean } {
  const px = p.x * S;
  const py = p.y * S;
  const len = Math.hypot(tangent.x, tangent.y) || 1;
  const nx = -tangent.y / len;
  const ny = tangent.x / len;
  let best = { d: dtAt(Math.round(px), Math.round(py)), x: px, y: py };
  for (let t = -radiusPx; t <= radiusPx; t += 0.5) {
    const x = px + nx * t;
    const y = py + ny * t;
    const d = dtAt(Math.round(x), Math.round(y));
    if (d > best.d) best = { d, x, y };
  }
  return {
    pt: { x: best.x / S, y: best.y / S },
    inside: at(Math.round(px), Math.round(py)) === 1,
  };
}

const RADIUS = Math.round(S * 0.035); // 隣接画へ飛ばない程度
const result: Record<number, number[][]> = {};
for (const st of def.strokes) {
  if (targetStrokes.length && !targetStrokes.includes(st.index)) continue;
  const pts: Pt[] = st.points.map(([x, y]) => ({ x, y }));
  const dense = splineSample(pts, 24);
  let insideCount = 0;
  const snapped: Pt[] = dense.map((p, i) => {
    const a = dense[Math.max(0, i - 1)];
    const b = dense[Math.min(dense.length - 1, i + 1)];
    const r = snap(p, { x: b.x - a.x, y: b.y - a.y }, RADIUS);
    if (r.inside) insideCount++;
    return r.pt;
  });
  // 制御点数を元と同じに間引く (エンジンの許容は制御点数に依存しないが素直な形を保つ)
  const n = pts.length;
  const out: number[][] = [];
  for (let k = 0; k < n; k++) {
    const idx = Math.round((k / (n - 1)) * (snapped.length - 1));
    out.push([
      Number(snapped[idx].x.toFixed(3)),
      Number(snapped[idx].y.toFixed(3)),
    ]);
  }
  result[st.index] = out;
  const pct = ((insideCount / dense.length) * 100).toFixed(0);
  console.log(`${charId} ${st.index}画目: 墨の中に乗っていた点 ${pct}%  → スナップ後の制御点:`);
  console.log('  ' + JSON.stringify(out));
}
fs.writeFileSync(
  `/tmp/snapped-${charId}.json`,
  JSON.stringify({ id: charId, file: srcFile, strokes: result }, null, 2),
);
