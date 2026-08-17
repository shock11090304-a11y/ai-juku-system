/**
 * 文字ごとの進捗 (§9.3)。最高記録を保持する（下がらない）。
 */
import type {
  AttemptSummary,
  GuideLevel,
  MistakeKind,
  Stars,
} from '../engine/types';
import { emptyMistakeCounts } from '../engine/types';
import { isMasterAttempt } from '../engine/scoring';
import { getDB } from './db';

export type CharProgress = {
  charId: string;
  bestStars: Stars;
  mastered: boolean;
  attempts: number;
  lastPlayedAt: number;
  /** 次に練習するガイドレベル (§5.4 Lv1→Lv2→Lv3 と進む) */
  guideLevel: GuideLevel;
  /** 保護者ダッシュボード用: ミスの内訳を累計 (§10.2) */
  mistakeCounts: Record<MistakeKind, number>;
};

export function emptyProgress(charId: string): CharProgress {
  return {
    charId,
    bestStars: 0,
    mastered: false,
    attempts: 0,
    lastPlayedAt: 0,
    guideLevel: 1,
    mistakeCounts: emptyMistakeCounts(),
  };
}

/** 1回の練習結果を進捗へ反映する（純関数） */
export function applyAttempt(
  prev: CharProgress,
  stars: Stars,
  summary: AttemptSummary,
  guideLevel: GuideLevel,
  now: number,
): CharProgress {
  const counts = { ...prev.mistakeCounts };
  for (const k of Object.keys(summary.counts) as MistakeKind[]) {
    counts[k] += summary.counts[k];
  }
  return {
    ...prev,
    bestStars: Math.max(prev.bestStars, stars) as Stars,
    mastered: prev.mastered || isMasterAttempt(stars, guideLevel),
    attempts: prev.attempts + 1,
    lastPlayedAt: now,
    // 完走したら次はひとつ上のレベルへ (§5.4)
    guideLevel: Math.min(3, Math.max(prev.guideLevel, guideLevel + 1)) as GuideLevel,
    mistakeCounts: counts,
  };
}

export async function loadAllProgress(): Promise<Record<string, CharProgress>> {
  const db = await getDB();
  const all = await db.getAll('progress');
  return Object.fromEntries(all.map((p) => [p.charId, p]));
}

export async function saveProgress(p: CharProgress): Promise<void> {
  const db = await getDB();
  await db.put('progress', p);
}

export async function clearAllProgress(): Promise<void> {
  const db = await getDB();
  await db.clear('progress');
  await db.clear('sessions');
}
