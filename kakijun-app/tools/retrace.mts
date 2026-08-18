/**
 * ★ 指定した「通過点」を順に結ぶ経路を、お手本の墨の中だけを通って引き直す。
 *   npx vite-node tools/retrace.mts -- [--apply] tools/_retrace_spec.json
 *
 * 画の切り分け (どの墨をどの画が書くか) が違っている字を直すための道具。
 * 人が指定するのは各画の**通過点だけ** (書き出し・要所・終わり) で、
 * 途中の形は墨の中心線を経路探索して求める。手で制御点を並べるより速く、
 * 「墨から浮いた線」も作らない。
 *
 * 通過点は tools/_tips.mts が印字する「墨の端」から選ぶ。
 * 直したら必ず tools/render/coverage-sheet.mts で目視すること
 * (経路探索は交差点で隣の画へ回り込むことがある)。
 *
 * spec の形:
 *   { "hira_ya": { "strokes": [ [[0.178,0.527],[0.46,0.40],[0.521,0.566]], null, ... ] } }
 *   null を置いた画はそのまま残す。
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
const specFile = args.find((a) => !a.startsWith('--'));
if (!specFile) throw new Error('spec の JSON を渡すこと');
const spec = JSON.parse(fs.readFileSync(specFile, 'utf8')) as Record<string, { strokes: ([number, number][] | null)[] }>;
// "_" で始まるキーは説明用のコメント
for (const k of Object.keys(spec)) if (k.startsWith('_')) delete spec[k];
const S = 512;

const FILES = ['hiragana.json', 'katakana.json', 'numbers.json'];
const bundles = FILES.map((f) => ({
  file: f,
  list: JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
}));
const find = (id: string): { b: (typeof bundles)[0]; c: RawCharacterDef } => {
  for (const b of bundles) {
    const c = b.list.find((x) => x.id === id);
    if (c) return { b, c };
  }
  throw new Error(`知らない字: ${id}`);
};

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
await useRefFont(
  page,
  Object.keys(spec).map((id) => find(id).c.char),
);

async function maskOf(ch: string): Promise<Uint8Array> {
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
    { ch, S, font: REF_FONT_FAMILY, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
  );
  return Uint8Array.from(bits);
}

/** 墨の中の各画素から縁までの距離 (中心線を通らせるため) */
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

function nearestInk(mask: Uint8Array, x0: number, y0: number): [number, number] {
  const x = Math.max(0, Math.min(S - 1, x0));
  const y = Math.max(0, Math.min(S - 1, y0));
  if (mask[y * S + x]) return [x, y];
  const seen = new Uint8Array(S * S);
  const q = [y * S + x];
  seen[y * S + x] = 1;
  for (let h = 0; h < q.length; h++) {
    const i = q[h];
    const cx = i % S;
    const cy = (i / S) | 0;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nx = cx + dx;
      const ny = cy + dy;
      if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
      const j = ny * S + nx;
      if (seen[j]) continue;
      if (mask[j]) return [nx, ny];
      seen[j] = 1;
      q.push(j);
    }
  }
  throw new Error('墨が見つからない');
}

class Heap {
  private a: { d: number; i: number }[] = [];
  get size(): number {
    return this.a.length;
  }
  push(d: number, i: number): void {
    this.a.push({ d, i });
    let k = this.a.length - 1;
    while (k > 0) {
      const p = (k - 1) >> 1;
      if (this.a[p].d <= this.a[k].d) break;
      [this.a[p], this.a[k]] = [this.a[k], this.a[p]];
      k = p;
    }
  }
  pop(): { d: number; i: number } | undefined {
    if (!this.a.length) return undefined;
    const top = this.a[0];
    const last = this.a.pop()!;
    if (this.a.length) {
      this.a[0] = last;
      let k = 0;
      for (;;) {
        const l = k * 2 + 1;
        const r = l + 1;
        let m = k;
        if (l < this.a.length && this.a[l].d < this.a[m].d) m = l;
        if (r < this.a.length && this.a[r].d < this.a[m].d) m = r;
        if (m === k) break;
        [this.a[m], this.a[k]] = [this.a[k], this.a[m]];
        k = m;
      }
    }
    return top;
  }
}

const DIRS: [number, number, number][] = [
  [1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1],
  [1, 1, 1.414], [1, -1, 1.414], [-1, 1, 1.414], [-1, -1, 1.414],
];

/** 墨の中だけを通り、中心線を優先する最短経路 */
function shortestInInk(
  mask: Uint8Array,
  dt: Float32Array,
  maxdt: number,
  a: [number, number],
  b: [number, number],
): [number, number][] {
  const src = a[1] * S + a[0];
  const dst = b[1] * S + b[0];
  if (src === dst) return [a];
  const dist = new Float64Array(S * S).fill(Infinity);
  const prev = new Int32Array(S * S).fill(-1);
  const pq = new Heap();
  dist[src] = 0;
  pq.push(0, src);
  while (pq.size) {
    const top = pq.pop()!;
    if (top.d > dist[top.i]) continue;
    if (top.i === dst) break;
    const x = top.i % S;
    const y = (top.i / S) | 0;
    for (const [dx, dy, w] of DIRS) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
      const j = ny * S + nx;
      if (!mask[j]) continue;
      const pen = 1 + 8 * ((maxdt - dt[j]) / maxdt) ** 2;
      const nd = top.d + w * pen;
      if (nd < dist[j]) {
        dist[j] = nd;
        prev[j] = top.i;
        pq.push(nd, j);
      }
    }
  }
  if (!isFinite(dist[dst])) throw new Error('墨の中で繋がらない (通過点を足すこと)');
  const path: [number, number][] = [];
  for (let i = dst; i !== -1; i = prev[i]) {
    path.push([i % S, (i / S) | 0]);
    if (i === src) break;
  }
  return path.reverse();
}

function rdp(pts: [number, number][], eps: number): [number, number][] {
  if (pts.length < 3) return pts;
  const a = pts[0];
  const b = pts[pts.length - 1];
  let worst = 0;
  let idx = 0;
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len = Math.hypot(dx, dy) || 1;
  for (let i = 1; i < pts.length - 1; i++) {
    const d = Math.abs((pts[i][0] - a[0]) * dy - (pts[i][1] - a[1]) * dx) / len;
    if (d > worst) {
      worst = d;
      idx = i;
    }
  }
  if (worst <= eps) return [a, b];
  return rdp(pts.slice(0, idx + 1), eps)
    .slice(0, -1)
    .concat(rdp(pts.slice(idx), eps));
}

const MAXPTS = 18;
for (const [id, s] of Object.entries(spec)) {
  const { c } = find(id);
  const mask = await maskOf(c.char);
  const dt = insideDistance(mask);
  let maxdt = 0;
  for (let i = 0; i < dt.length; i++) if (dt[i] > maxdt) maxdt = dt[i];
  s.strokes.forEach((wps, i) => {
    if (!wps) return;
    if (!c.strokes[i]) throw new Error(`${id}: ${i + 1}画目が無い`);
    const snapped = wps.map(([x, y]) => nearestInk(mask, Math.round(x * S), Math.round(y * S)));
    let full: [number, number][] = [];
    for (let k = 0; k < snapped.length - 1; k++) {
      const seg = shortestInInk(mask, dt, maxdt, snapped[k], snapped[k + 1]);
      full = full.length === 0 ? seg : full.concat(seg.slice(1));
    }
    let simp = rdp(full, 4);
    if (simp.length > MAXPTS) {
      simp = Array.from({ length: MAXPTS }, (_, k) =>
        simp[Math.round((k / (MAXPTS - 1)) * (simp.length - 1))],
      );
    }
    const pts = simp.map(([x, y]) => [
      Number((x / S).toFixed(3)),
      Number((y / S).toFixed(3)),
    ] as [number, number]);
    let L = 0;
    for (let k = 1; k < pts.length; k++) L += Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]);
    console.log(
      `${c.char} ${id} ${i + 1}画目: ${c.strokes[i].points.length}点 → ${pts.length}点  書き出し (${pts[0][0]},${pts[0][1]})  長さ ${L.toFixed(2)}`,
    );
    c.strokes[i].points = pts;
  });
}
await browser.close();

if (APPLY) {
  for (const b of bundles) {
    fs.writeFileSync(path.join(dataDir, b.file), JSON.stringify(b.list, null, 2) + '\n');
  }
  console.log('JSON を更新した');
} else {
  console.log('(測定のみ。書き換えるには --apply)');
}
