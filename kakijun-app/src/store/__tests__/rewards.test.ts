import { describe, expect, it } from 'vitest';
import { computeStamps, earnedKeys } from '../rewards';
import { emptyProgress, applyAttempt, type CharProgress } from '../progress';
import { characters } from '../../data';
import { emptyMistakeCounts } from '../../engine/types';

function progressWithStars(ids: string[], stars: 1 | 2 | 3): Record<string, CharProgress> {
  return Object.fromEntries(
    ids.map((id) => [id, { ...emptyProgress(id), bestStars: stars }]),
  );
}

describe('スタンプ (§9.2)', () => {
  const aGyo = characters
    .filter((c) => c.type === 'hiragana' && c.group === 'a-gyo')
    .map((c) => c.id);

  it('行の全文字が★1以上でスタンプ獲得', () => {
    const stamps = computeStamps(characters, progressWithStars(aGyo, 1));
    const target = stamps.find((s) => s.key === 'hiragana:a-gyo');
    expect(target?.earned).toBe(true);
  });

  it('1文字でも★0ならまだ獲得できない', () => {
    const partial = progressWithStars(aGyo.slice(1), 3); // あ だけ未達成
    const stamps = computeStamps(characters, partial);
    expect(stamps.find((s) => s.key === 'hiragana:a-gyo')?.earned).toBe(false);
  });

  it('全スタンプに絵柄がある', () => {
    const stamps = computeStamps(characters, {});
    for (const s of stamps) {
      expect(s.emoji.length).toBeGreaterThan(0);
    }
  });

  it('earnedKeys が獲得済みだけを返す', () => {
    const stamps = computeStamps(characters, progressWithStars(aGyo, 1));
    const keys = earnedKeys(stamps);
    expect(keys.has('hiragana:a-gyo')).toBe(true);
    expect(keys.has('number:0-5')).toBe(false);
  });
});

describe('進捗の反映 (§9.3)', () => {
  it('最高記録は下がらない', () => {
    let p = emptyProgress('hira_a');
    const summary = { mistakes: [], counts: emptyMistakeCounts() };
    p = applyAttempt(p, 3, summary, 1, 1000);
    expect(p.bestStars).toBe(3);
    p = applyAttempt(p, 1, summary, 2, 2000);
    expect(p.bestStars).toBe(3); // 下がらない
    expect(p.attempts).toBe(2);
  });

  it('Lv3で★3を取るとマスター (§9.1)', () => {
    let p = emptyProgress('hira_a');
    const summary = { mistakes: [], counts: emptyMistakeCounts() };
    p = applyAttempt(p, 3, summary, 1, 1000);
    expect(p.mastered).toBe(false);
    p = applyAttempt(p, 3, summary, 3, 2000);
    expect(p.mastered).toBe(true);
  });

  it('完走でガイドレベルが上がる (Lv1→2→3, 上限3)', () => {
    let p = emptyProgress('hira_a');
    const summary = { mistakes: [], counts: emptyMistakeCounts() };
    p = applyAttempt(p, 1, summary, 1, 1000);
    expect(p.guideLevel).toBe(2);
    p = applyAttempt(p, 1, summary, 2, 2000);
    expect(p.guideLevel).toBe(3);
    p = applyAttempt(p, 1, summary, 3, 3000);
    expect(p.guideLevel).toBe(3);
  });

  it('ミス内訳が累計される (§10.2)', () => {
    let p = emptyProgress('hira_a');
    const counts = { ...emptyMistakeCounts(), order: 2, offpath: 1 };
    p = applyAttempt(p, 1, { mistakes: [], counts }, 1, 1000);
    p = applyAttempt(p, 1, { mistakes: [], counts }, 1, 2000);
    expect(p.mistakeCounts.order).toBe(4);
    expect(p.mistakeCounts.offpath).toBe(2);
  });
});
