/**
 * 全文字データを1枚の HTML に並べる目視QA用コンタクトシート (§14.4)。
 *   npx vite-node tools/render/contact-sheet.ts -- [type または group の絞り込み...]
 * 出力: CONTACT_SHEET_OUT (既定 /tmp/contact-sheet.html)
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { charSvg } from './charSvg';
import type { RawCharacterDef } from '../../src/engine/types';
import { toCharacterDef, resolveCharacter, type MarkDef, toStroke } from '../../src/engine/loader';
import type { CharacterDef, RawStroke } from '../../src/engine/types';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../../src/data/characters');

function readJson<T>(file: string): T {
  return JSON.parse(fs.readFileSync(path.join(dataDir, file), 'utf8')) as T;
}

const files = ['hiragana.json', 'katakana.json', 'numbers.json', 'unpitsu.json'];
const all: RawCharacterDef[] = [];
for (const f of files) {
  if (fs.existsSync(path.join(dataDir, f))) {
    all.push(...readJson<RawCharacterDef[]>(f));
  }
}
const marksRaw = fs.existsSync(path.join(dataDir, 'marks.json'))
  ? readJson<MarkDef[]>('marks.json')
  : [];

// 合成 (濁音等) を解決してから描く
const registry = new Map<string, CharacterDef>(
  all.map((c) => [c.id, toCharacterDef(c)]),
);
const marks = new Map(
  marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]),
);

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

const cells = selected
  .map((c) => {
    const raw: RawCharacterDef = {
      ...c,
      strokes: c.strokes.map((s) => ({
        ...s,
        points: s.points.map((p) => [p.x, p.y] as [number, number]),
      })),
    };
    return `<div class="cell"><div class="label">${c.char} <small>${c.id} / ${c.strokes.length}画</small></div>${charSvg(
      raw,
      { size: 300, refGlyph: true, showControlPoints: false },
    )}</div>`;
  })
  .join('\n');

const html = `<!doctype html><meta charset="utf-8"><style>
body{font-family:IPAGothic,sans-serif;background:#f5f5f5;margin:8px}
.grid{display:flex;flex-wrap:wrap;gap:8px}
.cell{background:#fff;padding:4px;border-radius:4px}
.label{font-size:14px;text-align:center}
small{color:#888}
</style><div class="grid">${cells}</div>`;

const out = process.env.CONTACT_SHEET_OUT ?? '/tmp/contact-sheet.html';
fs.writeFileSync(out, html);
console.log(`${selected.length} 文字 → ${out}`);
