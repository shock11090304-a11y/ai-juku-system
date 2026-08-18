/**
 * ★ 「人がなぞった軌跡」の合成。単体テストと字形ツールが**同じものを使う**ための共有実装。
 *
 * ここを共有していなかったせいで事故った (2026-08-17):
 * tools/refit-glyphs.mts が独自に手ぶれ軌跡を作っていたが、乱数を画ごとに
 * 引き直していたため単体テストとは別の揺れになり、「ツールでは通ったのに
 * 単体テストが落ちる」字 (す) を出してしまった。
 * ★手ぶれの乱数は1字につき1本。画をまたいで引き継ぐ (テストがそうなっている)。
 */
import type { Pt, ResampledStroke } from './types';

/** 決定的な乱数 (mulberry32) */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 文字 id から決まる種 (同じ字なら毎回同じ揺れ) */
export function seedOf(id: string): number {
  return id.split('').reduce((a, ch) => a + ch.charCodeAt(0), 7);
}

/** ① 理想軌跡: データそのまま */
export function idealPaths(strokes: ResampledStroke[]): Pt[][] {
  return strokes.map((s) => s.pts.slice());
}

/**
 * ② 手ぶれ: 経路の法線方向に ±0.02 の揺れ + 4倍に細分した密なイベント列
 * (Apple Pencil 240Hz 相当)。★乱数は1字で1本。
 */
export function shakyPaths(strokes: ResampledStroke[], id: string): Pt[][] {
  const rand = rng(seedOf(id));
  return strokes.map((s) => {
    const path: Pt[] = [];
    for (let i = 0; i < 63; i++) {
      const a = s.pts[i];
      const b = s.pts[i + 1];
      const tx = b.x - a.x;
      const ty = b.y - a.y;
      const l = Math.hypot(tx, ty) || 1;
      for (let k = 0; k < 4; k++) {
        const t = k / 4;
        const j = (rand() * 2 - 1) * 0.02;
        path.push({
          x: a.x + tx * t + (-ty / l) * j,
          y: a.y + ty * t + (tx / l) * j,
        });
      }
    }
    path.push(s.pts[63]);
    return path;
  });
}

/**
 * ③ お手本ずらし: 見本 (フォント) と判定 (線データ) のズレぶん横にずらしてなぞる。
 * 折れ角では寄せ幅を絞る (等距離オフセットは角で自己交差して
 * 「人がなぞった軌跡」ではなくなるため)。
 */
export function offsetPaths(strokes: ResampledStroke[], offset = 0.035): Pt[][] {
  return strokes.map((s) =>
    s.pts.map((p, i) => {
      const a = s.pts[Math.max(0, i - 1)];
      const b = s.pts[Math.min(63, i + 1)];
      const tx = b.x - a.x;
      const ty = b.y - a.y;
      const l = Math.hypot(tx, ty) || 1;
      const c = s.pts[Math.max(0, i - 2)];
      const d = s.pts[Math.min(63, i + 2)];
      const u = Math.hypot(p.x - c.x, p.y - c.y) || 1;
      const v = Math.hypot(d.x - p.x, d.y - p.y) || 1;
      const cos = ((p.x - c.x) * (d.x - p.x) + (p.y - c.y) * (d.y - p.y)) / (u * v);
      const k = Math.max(0, Math.min(1, (cos + 0.2) / 1.2));
      return { x: p.x + (-ty / l) * offset * k, y: p.y + (tx / l) * offset * k };
    }),
  );
}
