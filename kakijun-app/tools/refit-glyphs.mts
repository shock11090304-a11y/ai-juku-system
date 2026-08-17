/**
 * 全文字の字形を手本フォントの墨に合わせ込む一括処理。
 *   npx vite-node tools/refit-glyphs.mts -- [--apply] [id...]
 *
 * 各字について:
 *   1. 手本グリフを 512px マスク化 (Chromium 1回起動で全字ぶん)
 *   2. 距離変換で墨の中心線を作る
 *   3. 現行ストロークを進行方向と直交する向きにだけ寄せる (隣の画へ飛ばない)
 *   4. 平滑化 → 元と同じ制御点数へ間引き
 *   5. 「線の中心が墨の中に乗っている割合」= 忠実度を before/after で出す
 *
 * --apply を付けたときだけ JSON を書き換える。付けなければ測定のみ。
 * 合成字 (濁音・半濁音) と小書き、運筆は対象外 (基字から派生させるため)。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { splineSample } from '../src/engine/geometry';
import type { RawCharacterDef, Pt } from '../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const args = process.argv.slice(2).filter((a) => a !== '--');
const APPLY = args.includes('--apply');
const only = args.filter((a) => !a.startsWith('--'));
// ★ system にインストールされたフォントを名前で引かない (tools/ref-font.mjs 参照)。
//   出荷している woff2 = 画面に出ている字そのものを測る。
const FONT = REF_FONT_FAMILY;
const S = 512;
const PASSES = 3;

const FILES = ['hiragana.json', 'katakana.json', 'numbers.json'];
type Bundle = { file: string; list: RawCharacterDef[] };
const bundles: Bundle[] = FILES.map((f) => ({
  file: f,
  list: JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
}));

const targets: { b: Bundle; c: RawCharacterDef }[] = [];
for (const b of bundles)
  for (const c of b.list) {
    if (c.composedFrom) continue; // 濁音等は基字から合成
    if (c.group === 'youon') continue; // 小書きは基字から生成
    if (only.length && !only.includes(c.id)) continue;
    targets.push({ b, c });
  }

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
// 手本フォントが本当に効いているかを、測る字そのもので確かめる
await useRefFont(
  page,
  targets.map((t) => t.c.char),
);

async function maskOf(ch: string): Promise<Uint8Array> {
  const bits = await page.evaluate(
    ({ ch, S, font }) => {
      const c = document.getElementById('c') as HTMLCanvasElement;
      const g = c.getContext('2d')!;
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      g.font = `${S * 0.88}px "${font}"`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(ch, S / 2, S / 2);
      const d = g.getImageData(0, 0, S, S).data;
      const out: number[] = [];
      for (let i = 0; i < S * S; i++) out.push(d[i * 4] < 128 ? 1 : 0);
      return out;
    },
    { ch, S, font: FONT },
  );
  return Uint8Array.from(bits);
}

function distanceTransform(mask: Uint8Array): Float32Array {
  const dt = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) dt[i] = mask[i] ? 1e6 : 0;
  for (let y = 0; y < S; y++)
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
  for (let y = S - 1; y >= 0; y--)
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
  return dt;
}

/** 墨に乗っている割合 (忠実度) */
function fidelity(pts: Pt[], mask: Uint8Array): number {
  const dense = splineSample(pts, 24);
  let inside = 0;
  for (const p of dense) {
    const x = Math.round(p.x * S);
    const y = Math.round(p.y * S);
    if (x >= 0 && y >= 0 && x < S && y < S && mask[y * S + x]) inside++;
  }
  return inside / dense.length;
}

function refit(pts: Pt[], _mask: Uint8Array, dt: Float32Array): Pt[] {
  const n = pts.length;
  let cur = pts;
  for (let pass = 0; pass < PASSES; pass++) {
    const dense = splineSample(cur, 24);
    const R = Math.round(S * (pass === 0 ? 0.045 : 0.02));
    const snapped: Pt[] = dense.map((p, i) => {
      const a = dense[Math.max(0, i - 1)];
      const b = dense[Math.min(dense.length - 1, i + 1)];
      const tx = b.x - a.x;
      const ty = b.y - a.y;
      const len = Math.hypot(tx, ty) || 1;
      const nx = -ty / len;
      const ny = tx / len;
      const px = p.x * S;
      const py = p.y * S;
      const idx = (x: number, y: number) => {
        const xi = Math.round(x);
        const yi = Math.round(y);
        return xi < 0 || yi < 0 || xi >= S || yi >= S ? 0 : dt[yi * S + xi];
      };
      let best = { d: idx(px, py), x: px, y: py };
      for (let t = -R; t <= R; t += 0.5) {
        const x = px + nx * t;
        const y = py + ny * t;
        const d = idx(x, y);
        if (d > best.d) best = { d, x, y };
      }
      return { x: best.x / S, y: best.y / S };
    });
    // 平滑化 (スナップのギザつきを均す。端点は動かさない)
    const sm: Pt[] = snapped.map((p, i) => {
      if (i === 0 || i === snapped.length - 1) return p;
      const a = snapped[i - 1];
      const b = snapped[i + 1];
      return { x: (a.x + 2 * p.x + b.x) / 4, y: (a.y + 2 * p.y + b.y) / 4 };
    });
    // 元と同じ制御点数へ
    cur = Array.from({ length: n }, (_, k) => sm[Math.round((k / (n - 1)) * (sm.length - 1))]);
  }
  return cur.map((p) => ({ x: Number(p.x.toFixed(3)), y: Number(p.y.toFixed(3)) }));
}

const report: { id: string; char: string; before: number; after: number }[] = [];
for (const { c } of targets) {
  const mask = await maskOf(c.char);
  const dt = distanceTransform(mask);
  let beforeSum = 0;
  let afterSum = 0;
  for (const st of c.strokes) {
    const pts: Pt[] = st.points.map(([x, y]) => ({ x, y }));
    const before = fidelity(pts, mask);
    const fitted = refit(pts, mask, dt);
    const after = fidelity(fitted, mask);
    beforeSum += before;
    // 悪化する画は触らない (元の形のほうが墨に乗っている場合)
    if (after > before) {
      afterSum += after;
      if (APPLY) st.points = fitted.map((p) => [p.x, p.y] as [number, number]);
    } else {
      afterSum += before;
    }
  }
  report.push({
    id: c.id,
    char: c.char,
    before: beforeSum / c.strokes.length,
    after: afterSum / c.strokes.length,
  });
}
await browser.close();

report.sort((a, b) => a.after - b.after);
console.log('忠実度 (線の中心が手本の墨に乗っている割合) 低い順:');
for (const r of report)
  console.log(
    `  ${r.char} ${r.id.padEnd(16)} ${(r.before * 100).toFixed(0).padStart(3)}% → ${(r.after * 100).toFixed(0).padStart(3)}%`,
  );
const avgB = report.reduce((s, r) => s + r.before, 0) / report.length;
const avgA = report.reduce((s, r) => s + r.after, 0) / report.length;
console.log(`平均: ${(avgB * 100).toFixed(1)}% → ${(avgA * 100).toFixed(1)}%  (${report.length}字)`);

if (APPLY) {
  for (const b of bundles) {
    fs.writeFileSync(path.join(dataDir, b.file), JSON.stringify(b.list, null, 2) + '\n');
  }
  console.log('JSON を更新した');
} else {
  console.log('(測定のみ。書き換えるには --apply)');
}
