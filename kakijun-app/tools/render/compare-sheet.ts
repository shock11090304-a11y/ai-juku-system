/**
 * 手本フォント (REF_FONT, 既定 "Klee One") と現行ストロークの並置比較シート。
 *   REF_FONT="Klee One" COMPARE_OUT=... npx vite-node tools/render/compare-sheet.ts -- [絞り込み...]
 * 左 = 手本フォント / 右 = 現行データ描画 (単独表示)。重ね合わせはしない (甘くなるため)。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { charSvg } from './charSvg';
import type { RawCharacterDef, RawStroke } from '../../src/engine/types';
import { toCharacterDef, resolveCharacter, toStroke, type MarkDef } from '../../src/engine/loader';
import type { CharacterDef } from '../../src/engine/types';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../../src/data/characters');
const files = ['hiragana.json', 'katakana.json', 'numbers.json', 'unpitsu.json'];
const all: RawCharacterDef[] = files.flatMap((f) =>
  fs.existsSync(path.join(dataDir, f))
    ? (JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[])
    : [],
);
const marksRaw = fs.existsSync(path.join(dataDir, 'marks.json'))
  ? (JSON.parse(fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8')) as MarkDef[])
  : [];
const registry = new Map<string, CharacterDef>(all.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]));

const filters = process.argv.slice(2).filter((a) => a !== '--');
const selected = [...registry.values()]
  .map((c) => resolveCharacter(c, registry, marks))
  .filter(
    (c) =>
      filters.length === 0 ||
      filters.includes(c.type) ||
      filters.includes(c.group) ||
      filters.includes(c.id),
  );

const S = Number(process.env.CELL ?? 250);
const FONT = process.env.REF_FONT ?? 'Klee One';

function refCell(ch: string): string {
  return (
    `<svg width="${S}" height="${S}" xmlns="http://www.w3.org/2000/svg">` +
    `<rect width="${S}" height="${S}" fill="#fff" stroke="#ccc"/>` +
    `<path d="M${S / 2},0 V${S} M0,${S / 2} H${S}" stroke="#eee" fill="none"/>` +
    `<text x="${S / 2}" y="${S / 2}" font-family="${FONT}" font-size="${S * 0.88}" fill="#333" text-anchor="middle" dominant-baseline="central">${ch}</text>` +
    `</svg>`
  );
}

const cells = selected
  .map((c) => {
    const raw: RawCharacterDef = {
      ...c,
      strokes: c.strokes.map((s) => ({
        ...s,
        points: s.points.map((p) => [p.x, p.y] as [number, number]),
      })),
    };
    return `<div class="pair"><div class="label">${c.char} <small>${c.id}</small></div>${refCell(
      c.char,
    )}${charSvg(raw, { size: S, refGlyph: false, showControlPoints: false })}</div>`;
  })
  .join('\n');

const html = `<!doctype html><meta charset="utf-8"><style>
body{font-family:sans-serif;background:#f5f5f5;margin:8px}
.grid{display:flex;flex-wrap:wrap;gap:10px}
.pair{background:#fff;padding:4px;border-radius:4px}
.label{font-size:14px;text-align:center}
small{color:#888}
</style><div class="grid">${cells}</div>`;

const out = process.env.COMPARE_OUT ?? '/tmp/compare-sheet.html';
fs.writeFileSync(out, html);
console.log(`${selected.length} 字 → ${out}`);
