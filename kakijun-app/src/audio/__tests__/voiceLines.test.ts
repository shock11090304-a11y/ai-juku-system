/**
 * 音声文言の検査 (§8.1, §7.4, §14.6)。
 */
import { describe, expect, it } from 'vitest';
import {
  PRAISE,
  RETRY,
  feedbackLine,
  guideText,
  pickDifferent,
} from '../voiceLines';

describe('文言のルール (§7.4)', () => {
  it('「ちがう」「まちがい」「だめ」を一切使わない', () => {
    const all = [
      ...PRAISE.map(([, t]) => t),
      ...RETRY.map(([, t]) => t),
      guideText(1, true),
      guideText(2, false),
      ...(['start', 'order', 'offpath', 'reverse', 'short'] as const).map(
        (k) => feedbackLine(k, 2).text,
      ),
    ];
    for (const text of all) {
      expect(text).not.toMatch(/ちがう|まちがい|だめ/);
    }
  });

  it('称賛は8種以上・促しは6種以上 (§8.1)', () => {
    expect(PRAISE.length).toBeGreaterThanOrEqual(8);
    expect(RETRY.length).toBeGreaterThanOrEqual(6);
  });

  it('ファイル名が重複しない', () => {
    const files = [...PRAISE, ...RETRY].map(([f]) => f);
    expect(new Set(files).size).toBe(files.length);
  });
});

describe('指示文言', () => {
  it('1画目は「いっかくめ」、以降は「つぎは ◯かくめ」', () => {
    expect(guideText(1, true)).toBe('いっかくめ');
    expect(guideText(2, false)).toBe('つぎは にかくめ');
    expect(guideText(3, false)).toBe('つぎは さんかくめ');
  });

  it('書き順違いは正しい画番号を案内する', () => {
    expect(feedbackLine('order', 2).text).toBe('つぎは にかくめだよ');
    expect(feedbackLine('order', 2).file).toBe('guide/next_is_2');
  });
});

describe('直前重複の除外 (§8.1, §14.6)', () => {
  it('直前と同じインデックスは決して返さない', () => {
    // すべての乱数値で検査する（rand を格子でなめる）
    for (let exclude = 0; exclude < 9; exclude++) {
      for (let r = 0; r < 100; r++) {
        const idx = pickDifferent(9, exclude, () => r / 100);
        expect(idx).not.toBe(exclude);
        expect(idx).toBeGreaterThanOrEqual(0);
        expect(idx).toBeLessThan(9);
      }
    }
  });

  it('3回連続で同じ称賛にならない', () => {
    let last = -1;
    const seen: number[] = [];
    for (let i = 0; i < 50; i++) {
      const idx = pickDifferent(PRAISE.length, last);
      seen.push(idx);
      last = idx;
    }
    for (let i = 1; i < seen.length; i++) {
      expect(seen[i]).not.toBe(seen[i - 1]);
    }
  });

  it('候補が全て選ばれうる（除外以外に偏りがない）', () => {
    const counts = new Array(5).fill(0);
    for (let r = 0; r < 1000; r++) {
      counts[pickDifferent(5, 2, () => r / 1000)]++;
    }
    expect(counts[2]).toBe(0);
    for (const [i, c] of counts.entries()) {
      if (i !== 2) expect(c).toBeGreaterThan(0);
    }
  });
});
