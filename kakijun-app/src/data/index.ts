/**
 * 文字データの入口。JSON を静的 import してレジストリ化する
 * （バンドルに含まれるので、オフラインでも fetch 不要で全データが使える）。
 */
import hiraganaJson from './characters/hiragana.json';
import katakanaJson from './characters/katakana.json';
import numbersJson from './characters/numbers.json';
import unpitsuJson from './characters/unpitsu.json';
import marksJson from './characters/marks.json';
import type { CharacterDef, CharType, RawCharacterDef } from '../engine/types';
import {
  resolveCharacter,
  toCharacterDef,
  toStroke,
  type MarkDef,
} from '../engine/loader';

const rawAll: RawCharacterDef[] = [
  ...(hiraganaJson as unknown as RawCharacterDef[]),
  ...(katakanaJson as unknown as RawCharacterDef[]),
  ...(numbersJson as unknown as RawCharacterDef[]),
  ...(unpitsuJson as unknown as RawCharacterDef[]),
];

const registry = new Map(rawAll.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(
  (marksJson as unknown as MarkDef[]).map((m) => [
    m.id,
    m.strokes.map(toStroke),
  ]),
);

/** 合成（濁音・半濁音）解決済みの全文字。ファイル内の並び順を保持する */
export const characters: CharacterDef[] = [...registry.values()].map((c) =>
  resolveCharacter(c, registry, marks),
);

const byId = new Map(characters.map((c) => [c.id, c]));

export function getChar(id: string): CharacterDef {
  const c = byId.get(id);
  if (!c) throw new Error(`character not found: ${id}`);
  return c;
}

export function listByType(type: CharType): CharacterDef[] {
  return characters.filter((c) => c.type === type);
}

/** 出現順を保った group 一覧（文字えらび画面の行見出しに使う） */
export function groupsOf(type: CharType): string[] {
  const seen: string[] = [];
  for (const c of listByType(type)) {
    if (!seen.includes(c.group)) seen.push(c.group);
  }
  return seen;
}
