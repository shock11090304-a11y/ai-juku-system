/**
 * 文字データのローダ。JSON（タプル座標）→ CharacterDef、
 * 濁音・半濁音の合成 (§4.3)、判定用リサンプリング (§6.1)。
 * fetch はしない（呼び出し側が import した JSON を渡す）。純関数のみ。
 */
import type {
  CharacterDef,
  Pt,
  RawCharacterDef,
  RawPt,
  RawStroke,
  ResampledStroke,
  Stroke,
} from './types';
import { resampleStroke } from './geometry';

export function toPt([x, y]: RawPt): Pt {
  return { x, y };
}

export function toStroke(raw: RawStroke): Stroke {
  return { ...raw, points: raw.points.map(toPt) };
}

export function toCharacterDef(raw: RawCharacterDef): CharacterDef {
  return { ...raw, strokes: raw.strokes.map(toStroke) };
}

export type MarkDef = { id: string; strokes: RawStroke[] };

/**
 * composedFrom を解決して strokes を組み立てる。
 * base の画 → marks の画の順に通し番号を振り直す (§4.3)。
 */
export function resolveCharacter(
  def: CharacterDef,
  registry: Map<string, CharacterDef>,
  marks: Map<string, Stroke[]>,
): CharacterDef {
  if (!def.composedFrom) return def;
  const base = registry.get(def.composedFrom.base);
  if (!base) throw new Error(`base not found: ${def.composedFrom.base}`);
  const baseResolved = resolveCharacter(base, registry, marks);
  const strokes: Stroke[] = baseResolved.strokes.map((s) => ({ ...s }));
  // 記号の位置は字ごとに違う (フォントの゛の打ち方に合わせる §types)
  const [dx, dy] = def.composedFrom.markOffset ?? [0, 0];
  for (const markId of def.composedFrom.marks) {
    const markStrokes = marks.get(markId);
    if (!markStrokes) throw new Error(`mark not found: ${markId}`);
    for (const ms of markStrokes) {
      strokes.push({
        ...ms,
        points: ms.points.map((p) => ({ x: p.x + dx, y: p.y + dy })),
      });
    }
  }
  strokes.forEach((s, i) => (s.index = i + 1));
  return { ...def, strokes };
}

/** 判定エンジンに渡す形へ前処理する */
export function prepareStrokes(def: CharacterDef): ResampledStroke[] {
  return def.strokes.map((s) => {
    const { pts, length } = resampleStroke(s.points);
    return { index: s.index, pts, length, hint: s.hint, ending: s.ending };
  });
}
