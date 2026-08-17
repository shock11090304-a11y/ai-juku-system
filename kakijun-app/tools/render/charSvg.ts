/**
 * ストロークデータ → SVG。エディタのプレビューと目視QA用コンタクトシートで共用。
 * 実アプリの Canvas 描画と同じスプライン (engine/geometry) を使う (§4.4)。
 */
import { splineSample } from '../../src/engine/geometry';
import type { Pt, RawCharacterDef, RawStroke } from '../../src/engine/types';

const COLORS = ['#e05d5d', '#3b82f6', '#22a559', '#e08a1e', '#8b5cf6', '#0ea5b0'];

function toPts(stroke: RawStroke): Pt[] {
  return stroke.points.map(([x, y]) => ({ x, y }));
}

function pathD(pts: Pt[], size: number): string {
  return pts
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${(p.x * size).toFixed(1)},${(p.y * size).toFixed(1)}`)
    .join(' ');
}

export type CharSvgOpts = {
  size?: number;
  /** 参照用に文字をうすく背後に出す（IPAGothic 等のシステムフォント。あくまで下敷き） */
  refGlyph?: boolean;
  /** 制御点も表示する */
  showControlPoints?: boolean;
};

export function charSvg(def: RawCharacterDef, opts: CharSvgOpts = {}): string {
  const size = opts.size ?? 220;
  const lw = size * 0.11; // 筆の太さ (§4.2)
  const parts: string[] = [];
  parts.push(
    `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">`,
  );
  parts.push(`<rect width="${size}" height="${size}" fill="#fffdf7" stroke="#ddd"/>`);
  // 十字の点線マス
  parts.push(
    `<path d="M${size / 2},0 V${size} M0,${size / 2} H${size}" stroke="#cfd8dc" stroke-dasharray="6 6" fill="none"/>`,
  );
  if (opts.refGlyph) {
    parts.push(
      `<text x="${size / 2}" y="${size / 2}" font-family="IPAGothic, sans-serif" font-size="${
        size * 0.9
      }" fill="#000" opacity="0.22" text-anchor="middle" dominant-baseline="central">${def.char}</text>`,
    );
  }
  def.strokes.forEach((stroke, i) => {
    const color = COLORS[i % COLORS.length];
    const pts = toPts(stroke);
    const dense = splineSample(pts, 32);
    parts.push(
      `<path d="${pathD(dense, size)}" stroke="${color}" stroke-width="${lw}" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="0.55"/>`,
    );
    // 方向: 30% 地点に矢印
    const a = dense[Math.floor(dense.length * 0.28)];
    const b = dense[Math.floor(dense.length * 0.32)];
    const ang = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
    parts.push(
      `<g transform="translate(${b.x * size},${b.y * size}) rotate(${ang})"><path d="M-7,-6 L7,0 L-7,6" fill="none" stroke="#333" stroke-width="2.5"/></g>`,
    );
    if (opts.showControlPoints) {
      for (const p of pts) {
        parts.push(
          `<circle cx="${p.x * size}" cy="${p.y * size}" r="3" fill="none" stroke="${color}" stroke-width="1.5"/>`,
        );
      }
    }
    // 始点の丸 + 画数
    const s0 = pts[0];
    parts.push(
      `<circle cx="${s0.x * size}" cy="${s0.y * size}" r="${size * 0.035}" fill="${color}"/>`,
    );
    parts.push(
      `<text x="${s0.x * size + size * 0.05}" y="${s0.y * size - size * 0.02}" font-size="${
        size * 0.09
      }" font-weight="bold" fill="${color}">${stroke.index}</text>`,
    );
  });
  parts.push('</svg>');
  return parts.join('');
}
