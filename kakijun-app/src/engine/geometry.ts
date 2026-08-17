/**
 * 点・距離・スプライン・リサンプリング (§6.1)。純関数のみ。
 */
import type { Pt } from './types';

export const clamp = (v: number, min: number, max: number): number =>
  v < min ? min : v > max ? max : v;

export const dist = (a: Pt, b: Pt): number => Math.hypot(a.x - b.x, a.y - b.y);

export const sub = (a: Pt, b: Pt): Pt => ({ x: a.x - b.x, y: a.y - b.y });

export const lerp = (a: Pt, b: Pt, t: number): Pt => ({
  x: a.x + (b.x - a.x) * t,
  y: a.y + (b.y - a.y) * t,
});

export const vlen = (v: Pt): number => Math.hypot(v.x, v.y);

export const dot = (a: Pt, b: Pt): number => a.x * b.x + a.y * b.y;

/** ゼロベクトルは {0,0} のまま返す（呼び出し側で |v|>0 を確認すること） */
export const normalize = (v: Pt): Pt => {
  const l = vlen(v);
  return l > 0 ? { x: v.x / l, y: v.y / l } : { x: 0, y: 0 };
};

/** uniform Catmull-Rom の1セグメント */
function catmullRom(p0: Pt, p1: Pt, p2: Pt, p3: Pt, t: number): Pt {
  const t2 = t * t;
  const t3 = t2 * t;
  return {
    x:
      0.5 *
      (2 * p1.x +
        (-p0.x + p2.x) * t +
        (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 +
        (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3),
    y:
      0.5 *
      (2 * p1.y +
        (-p0.y + p2.y) * t +
        (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 +
        (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3),
  };
}

/**
 * 制御点列を Catmull-Rom スプラインで補間して密な点列にする。
 * 端点は複製して端まで通す。制御点2点なら実質直線になる。
 */
export function splineSample(control: Pt[], perSegment = 32): Pt[] {
  if (control.length < 2) return control.slice();
  const ext = [control[0], ...control, control[control.length - 1]];
  const out: Pt[] = [];
  for (let i = 0; i < control.length - 1; i++) {
    const p0 = ext[i];
    const p1 = ext[i + 1];
    const p2 = ext[i + 2];
    const p3 = ext[i + 3];
    for (let s = 0; s < perSegment; s++) {
      out.push(catmullRom(p0, p1, p2, p3, s / perSegment));
    }
  }
  out.push(control[control.length - 1]);
  return out;
}

export function polylineLength(pts: Pt[]): number {
  let l = 0;
  for (let i = 1; i < pts.length; i++) l += dist(pts[i - 1], pts[i]);
  return l;
}

/** 弧長に沿って等間隔な n 点にリサンプリングする */
export function resampleUniform(pts: Pt[], n: number): Pt[] {
  if (pts.length === 0) return [];
  if (pts.length === 1) return new Array<Pt>(n).fill(pts[0]);
  const total = polylineLength(pts);
  if (total === 0) return new Array<Pt>(n).fill(pts[0]);
  const step = total / (n - 1);
  const out: Pt[] = [pts[0]];
  let segIdx = 0;
  let segStart = pts[0];
  let segEnd = pts[1];
  let segLen = dist(segStart, segEnd);
  let acc = 0; // segStart からの消化済み距離
  for (let i = 1; i < n - 1; i++) {
    let need = step;
    while (acc + need > segLen) {
      need -= segLen - acc;
      acc = 0;
      segIdx++;
      if (segIdx >= pts.length - 1) break;
      segStart = pts[segIdx];
      segEnd = pts[segIdx + 1];
      segLen = dist(segStart, segEnd);
    }
    if (segIdx >= pts.length - 1) {
      out.push(pts[pts.length - 1]);
      continue;
    }
    acc += need;
    out.push(lerp(segStart, segEnd, segLen > 0 ? acc / segLen : 0));
  }
  out.push(pts[pts.length - 1]);
  return out;
}

/**
 * 制御点列 → 判定基準の 64 点列 (§6.1)。
 * 返り値の length はリサンプリング後の弧長 L（許容量の基準）。
 */
export function resampleStroke(
  control: Pt[],
  n = 64,
): { pts: Pt[]; length: number } {
  const dense = splineSample(control, 32);
  const pts = resampleUniform(dense, n);
  return { pts, length: polylineLength(pts) };
}

/**
 * a→b を間隔 h 以下で線形補間した点列（a を含まず b を含む）(§6.4)。
 * 速書きでイベントが飛んだときに中間点も判定列に含めるための主経路。
 */
export function interpolateSegment(a: Pt, b: Pt, h: number): Pt[] {
  const d = dist(a, b);
  if (h <= 0 || d <= h) return [b];
  const k = Math.ceil(d / h);
  const out: Pt[] = [];
  for (let i = 1; i <= k; i++) out.push(lerp(a, b, i / k));
  return out;
}
