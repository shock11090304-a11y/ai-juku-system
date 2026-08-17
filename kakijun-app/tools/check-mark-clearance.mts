/**
 * 濁点・半濁点が基字の画に食い込んでいないかの検査。
 * 中心線間の最小距離が線幅 (0.11) 未満 = 帯が重なる → NG。
 *   npx vite-node tools/check-mark-clearance.mts
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { splineSample } from '../src/engine/geometry';
import { toCharacterDef, resolveCharacter, toStroke, type MarkDef } from '../src/engine/loader';
import type { CharacterDef, RawCharacterDef, RawStroke, Pt } from '../src/engine/types';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const files = ['hiragana.json', 'katakana.json', 'numbers.json', 'unpitsu.json'];
const all: RawCharacterDef[] = files.flatMap((f) =>
  fs.existsSync(path.join(dataDir, f))
    ? (JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[])
    : [],
);
const marksRaw = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8'),
) as MarkDef[];

const registry = new Map<string, CharacterDef>(all.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(
  marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]),
);

const LW = 0.11;
function dist(a: Pt, b: Pt): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}
function minDist(aPts: Pt[], bPts: Pt[]): number {
  let m = Infinity;
  for (const a of aPts) for (const b of bPts) m = Math.min(m, dist(a, b));
  return m;
}

let bad = 0;
for (const c of registry.values()) {
  if (!c.composedFrom) continue;
  const r = resolveCharacter(c, registry, marks);
  const base = registry.get(c.composedFrom.base)!;
  const nBase = base.strokes.length;
  const dense = r.strokes.map((s) => splineSample(s.points, 48));
  for (let mi = nBase; mi < dense.length; mi++) {
    for (let bi = 0; bi < nBase; bi++) {
      const d = minDist(dense[mi], dense[bi]);
      if (d < LW) {
        console.log(
          `NG ${r.char} (${r.id}) mark${mi + 1} vs base${bi + 1}: ${d.toFixed(3)} < ${LW}`,
        );
        bad++;
      }
    }
  }
}
if (bad === 0) console.log('OK: 全合成字で 記号と基字の帯の重なりなし');
process.exit(bad ? 1 : 0);
