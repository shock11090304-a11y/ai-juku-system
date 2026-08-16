/**
 * 星の判定 (§9.1)。
 *   ★1: 全画を最後まで完走した
 *   ★2: ★1 + 書き順のミス (MISTAKE_ORDER) が 0 回
 *   ★3: ★2 + やり直しが1度も発生しなかった（逸脱・逆走・途中終了すべて0）
 */
import type { AttemptSummary, GuideLevel, Stars } from './types';

export function computeStars(summary: AttemptSummary): Stars {
  const c = summary.counts;
  const star2 = c.order === 0;
  const star3 =
    star2 &&
    c.offpath === 0 &&
    c.reverse === 0 &&
    c.reverse_start === 0 &&
    c.short === 0;
  if (star3) return 3;
  if (star2) return 2;
  return 1;
}

/** ガイド Lv3 で★3 → マスターバッジ (§9.1) */
export function isMasterAttempt(stars: Stars, guideLevel: GuideLevel): boolean {
  return stars === 3 && guideLevel === 3;
}
