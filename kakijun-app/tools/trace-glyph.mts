/**
 * 手本グリフの墨の上を「中心線をたどって」経路探索し、制御点を機械抽出する。
 * 経由点 (waypoint) を与えると、その順に墨の中だけを通る最短経路を引く。
 * コストは距離変換の逆数寄りにしてあるので、線の縁ではなく中心を通る。
 *
 *   node tools/glyph-mask.mjs お /tmp/mask-o.json
 *   npx vite-node tools/trace-glyph.mts -- /tmp/mask-o.json 0.37,0.18 0.37,0.5 ...
 *
 * 出力: 制御点 JSON (0-1 正規化)。RDP で間引いてある。
 */
import fs from 'node:fs';

const [maskPath, ...wpArgs] = process.argv.slice(2).filter((a) => a !== '--');
const { size: S, mask } = JSON.parse(fs.readFileSync(maskPath, 'utf8')) as {
  size: number;
  mask: number[];
};
const waypoints = wpArgs.map((s) => {
  const [x, y] = s.split(',').map(Number);
  return { x: Math.round(x * S), y: Math.round(y * S) };
});
if (waypoints.length < 2) throw new Error('経由点は2つ以上必要');

// 距離変換 (墨の内側ほど大きい)
const dt = new Float32Array(S * S);
for (let i = 0; i < S * S; i++) dt[i] = mask[i] ? 1e9 : 0;
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
let maxDT = 0;
for (let i = 0; i < S * S; i++) maxDT = Math.max(maxDT, dt[i]);

/** 墨の外なら最寄りの墨へ寄せる */
function toInk(p: { x: number; y: number }) {
  if (mask[p.y * S + p.x]) return p;
  for (let r = 1; r < 40; r++)
    for (let dy = -r; dy <= r; dy++)
      for (let dx = -r; dx <= r; dx++) {
        const x = p.x + dx;
        const y = p.y + dy;
        if (x < 0 || y < 0 || x >= S || y >= S) continue;
        if (mask[y * S + x]) return { x, y };
      }
  throw new Error('墨が見つからない');
}

const DIRS = [
  [1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1],
  [1, 1, 1.414], [1, -1, 1.414], [-1, 1, 1.414], [-1, -1, 1.414],
];

/** 墨の中だけを通り、中心 (距離変換が大きい所) を優先する最短経路 */
function dijkstra(a: { x: number; y: number }, b: { x: number; y: number }) {
  const dist = new Float32Array(S * S).fill(Infinity);
  const prev = new Int32Array(S * S).fill(-1);
  const si = a.y * S + a.x;
  dist[si] = 0;
  // 単純な bucket queue (コストが小さい整数域なので十分速い)
  const heap: [number, number][] = [[0, si]];
  const push = (d: number, i: number) => {
    heap.push([d, i]);
    let c = heap.length - 1;
    while (c > 0) {
      const p = (c - 1) >> 1;
      if (heap[p][0] <= heap[c][0]) break;
      [heap[p], heap[c]] = [heap[c], heap[p]];
      c = p;
    }
  };
  const pop = () => {
    const top = heap[0];
    const last = heap.pop()!;
    if (heap.length) {
      heap[0] = last;
      let c = 0;
      for (;;) {
        const l = c * 2 + 1;
        const r = l + 1;
        let m = c;
        if (l < heap.length && heap[l][0] < heap[m][0]) m = l;
        if (r < heap.length && heap[r][0] < heap[m][0]) m = r;
        if (m === c) break;
        [heap[m], heap[c]] = [heap[c], heap[m]];
        c = m;
      }
    }
    return top;
  };
  const goal = b.y * S + b.x;
  while (heap.length) {
    const [d, i] = pop();
    if (d > dist[i]) continue;
    if (i === goal) break;
    const x = i % S;
    const y = (i / S) | 0;
    for (const [dx, dy, w] of DIRS) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
      const j = ny * S + nx;
      if (!mask[j]) continue;
      // 中心 (dt 最大) から離れるほど高コスト → 稜線を通る
      const penalty = 1 + 6 * ((maxDT - dt[j]) / maxDT) ** 2;
      const nd = d + w * penalty;
      if (nd < dist[j]) {
        dist[j] = nd;
        prev[j] = i;
        push(nd, j);
      }
    }
  }
  const path: { x: number; y: number }[] = [];
  for (let i = goal; i !== -1; i = prev[i]) path.push({ x: i % S, y: (i / S) | 0 });
  if (path[path.length - 1].x !== a.x || path[path.length - 1].y !== a.y)
    throw new Error('経路が繋がらない (墨が切れている)');
  return path.reverse();
}

let full: { x: number; y: number }[] = [];
for (let k = 0; k + 1 < waypoints.length; k++) {
  const seg = dijkstra(toInk(waypoints[k]), toInk(waypoints[k + 1]));
  full = full.length ? full.concat(seg.slice(1)) : seg;
}

/** Ramer-Douglas-Peucker で制御点へ間引く */
function rdp(pts: { x: number; y: number }[], eps: number): { x: number; y: number }[] {
  if (pts.length < 3) return pts;
  const a = pts[0];
  const b = pts[pts.length - 1];
  let maxD = -1;
  let idx = 0;
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const len = Math.hypot(dx, dy) || 1;
  for (let i = 1; i < pts.length - 1; i++) {
    const d = Math.abs((pts[i].x - a.x) * dy - (pts[i].y - a.y) * dx) / len;
    if (d > maxD) {
      maxD = d;
      idx = i;
    }
  }
  if (maxD <= eps) return [a, b];
  return rdp(pts.slice(0, idx + 1), eps)
    .slice(0, -1)
    .concat(rdp(pts.slice(idx), eps));
}

const eps = Number(process.env.RDP_EPS ?? 5);
const simplified = rdp(full, eps);
const out = simplified.map((p) => [
  Number((p.x / S).toFixed(3)),
  Number((p.y / S).toFixed(3)),
]);
console.log(`経路 ${full.length}px → 制御点 ${out.length}個`);
console.log(JSON.stringify(out));
