/**
 * 字形修正用の精密シート: 1字を 520px で、0.1 グリッド + 参照フォント +
 * 現在のストローク (細線・制御点付き) を重ねて表示する。
 *   FIX_OUT=... npx vite-node tools/render/fix-sheet.ts -- hira_su hira_ma ...
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { splineSample } from '../../src/engine/geometry';
import type { RawCharacterDef } from '../../src/engine/types';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../../src/data/characters');
const files = ['hiragana.json', 'katakana.json', 'numbers.json', 'unpitsu.json'];
const all: RawCharacterDef[] = files.flatMap((f) =>
  fs.existsSync(path.join(dataDir, f))
    ? (JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[])
    : [],
);

const ids = process.argv.slice(2).filter((a) => a !== '--');
const S = 520;
const COLORS = ['#e05d5d', '#3b82f6', '#22a559', '#e08a1e', '#8b5cf6'];

function cell(def: RawCharacterDef): string {
  const parts: string[] = [];
  parts.push(`<svg width="${S}" height="${S}" xmlns="http://www.w3.org/2000/svg">`);
  parts.push(`<rect width="${S}" height="${S}" fill="#fff" stroke="#999"/>`);
  // 0.1 グリッド + 座標ラベル
  for (let i = 1; i < 10; i++) {
    const v = (i / 10) * S;
    parts.push(`<line x1="${v}" y1="0" x2="${v}" y2="${S}" stroke="#ddd"/>`);
    parts.push(`<line x1="0" y1="${v}" x2="${S}" y2="${v}" stroke="#ddd"/>`);
    parts.push(`<text x="${v + 2}" y="12" font-size="11" fill="#999">${(i / 10).toFixed(1)}</text>`);
    parts.push(`<text x="2" y="${v - 2}" font-size="11" fill="#999">${(i / 10).toFixed(1)}</text>`);
  }
  // 参照フォント
  parts.push(
    `<text x="${S / 2}" y="${S / 2}" font-family="IPAGothic" font-size="${S * 0.9}" fill="#000" opacity="0.18" text-anchor="middle" dominant-baseline="central">${def.char}</text>`,
  );
  // 現在のストローク (実太さの半透明 + 中心線 + 制御点)
  def.strokes.forEach((st, i) => {
    const c = COLORS[i % COLORS.length];
    const pts = st.points.map(([x, y]) => ({ x, y }));
    const dense = splineSample(pts, 32);
    const d = dense.map((p, k) => `${k === 0 ? 'M' : 'L'}${(p.x * S).toFixed(1)},${(p.y * S).toFixed(1)}`).join(' ');
    parts.push(`<path d="${d}" stroke="${c}" stroke-width="${S * 0.11}" opacity="0.25" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`);
    parts.push(`<path d="${d}" stroke="${c}" stroke-width="2.5" fill="none"/>`);
    pts.forEach((p, k) => {
      parts.push(`<circle cx="${p.x * S}" cy="${p.y * S}" r="4" fill="#fff" stroke="${c}" stroke-width="2"/>`);
      parts.push(`<text x="${p.x * S + 6}" y="${p.y * S - 6}" font-size="11" fill="${c}">${k}</text>`);
    });
  });
  parts.push('</svg>');
  return `<div style="display:inline-block;margin:4px"><div style="font-family:sans-serif">${def.char} ${def.id}</div>${parts.join('')}</div>`;
}

const out = process.env.FIX_OUT ?? '/tmp/fix-sheet.html';
const cells = ids
  .map((id) => {
    const def = all.find((c) => c.id === id);
    if (!def) throw new Error(`not found: ${id}`);
    return cell(def);
  })
  .join('\n');
fs.writeFileSync(out, `<!doctype html><meta charset="utf-8">${cells}`);
console.log(`${ids.length} 字 → ${out}`);
