/**
 * 保護者設定 (§10.3)。
 */
import type { CharType, Strictness } from '../engine/types';
import { getDB } from './db';

export type Settings = {
  /** 判定のきびしさ */
  strictness: Strictness;
  /** 1回のれんしゅう時間の上限（分）。null = なし */
  sessionLimitMin: number | null;
  /** 1日の合計上限（分）。null = なし */
  dailyLimitMin: number | null;
  voiceEnabled: boolean;
  sfxEnabled: boolean;
  /** 学習範囲の表示切替 */
  showTypes: Record<CharType, boolean>;
};

export const DEFAULT_SETTINGS: Settings = {
  strictness: 'normal',
  sessionLimitMin: 15,
  dailyLimitMin: 30,
  voiceEnabled: true,
  sfxEnabled: true,
  showTypes: { hiragana: true, katakana: true, number: true, unpitsu: true },
};

export async function loadSettings(): Promise<Settings> {
  const db = await getDB();
  const saved = await db.get('settings', 'settings');
  return { ...DEFAULT_SETTINGS, ...saved };
}

export async function saveSettings(s: Settings): Promise<void> {
  const db = await getDB();
  await db.put('settings', s, 'settings');
}
