/**
 * ごほうびスタンプ (§9.2)。
 * 1行（あ行、か行…= group）をすべて★1以上にするとスタンプが1個。
 */
import type { CharacterDef } from '../engine/types';
import type { CharProgress } from './progress';

/** group → スタンプの絵柄（動物・乗り物） */
export const STAMP_EMOJI: Record<string, string> = {
  // ひらがな: 動物
  'a-gyo': '🐶',
  'ka-gyo': '🐱',
  'sa-gyo': '🐰',
  'ta-gyo': '🐻',
  'na-gyo': '🦊',
  'ha-gyo': '🐼',
  'ma-gyo': '🐨',
  'ya-gyo': '🦁',
  'ra-gyo': '🐯',
  'wa-gyo': '🐘',
  dakuon: '🦒',
  handakuon: '🦉',
  youon: '🐧',
};

/** カタカナ・数字・運筆は type を前置して区別する */
export const STAMP_EMOJI_BY_TYPE: Record<string, Record<string, string>> = {
  katakana: {
    'a-gyo': '🚗',
    'ka-gyo': '🚕',
    'sa-gyo': '🚌',
    'ta-gyo': '🚒',
    'na-gyo': '🚑',
    'ha-gyo': '🚂',
    'ma-gyo': '✈️',
    'ya-gyo': '🚀',
    'ra-gyo': '🚁',
    'wa-gyo': '⛵',
    dakuon: '🚜',
    handakuon: '🛵',
    youon: '🚤',
  },
  number: { '0-5': '🍎', '6-10': '🍇' },
  unpitsu: { sen: '✏️', katachi: '🖍️' },
};

export type Stamp = {
  key: string; // 'hiragana:a-gyo'
  type: string;
  group: string;
  emoji: string;
  earned: boolean;
};

export function stampEmoji(type: string, group: string): string {
  if (type === 'hiragana') return STAMP_EMOJI[group] ?? '🌟';
  return STAMP_EMOJI_BY_TYPE[type]?.[group] ?? '🌟';
}

/** 収録データと進捗から、スタンプ一覧（獲得済みかどうか）を計算する（純関数） */
export function computeStamps(
  characters: CharacterDef[],
  progress: Record<string, CharProgress>,
): Stamp[] {
  const seen = new Map<string, { type: string; group: string; all: boolean }>();
  for (const c of characters) {
    const key = `${c.type}:${c.group}`;
    const entry = seen.get(key) ?? { type: c.type, group: c.group, all: true };
    if ((progress[c.id]?.bestStars ?? 0) < 1) entry.all = false;
    seen.set(key, entry);
  }
  return [...seen.entries()].map(([key, v]) => ({
    key,
    type: v.type,
    group: v.group,
    emoji: stampEmoji(v.type, v.group),
    earned: v.all,
  }));
}

export function earnedKeys(stamps: Stamp[]): Set<string> {
  return new Set(stamps.filter((s) => s.earned).map((s) => s.key));
}
