/**
 * 音声の文言とファイル名 (§8.1)。純データ・純関数（テスト対象）。
 * 「ちがう」「まちがい」「だめ」は音声・表示ともに一切使わない (§7.4)。
 */

export const PRAISE: [string, string][] = [
  ['praise_01', 'じょうず！'],
  ['praise_02', 'できたね！'],
  ['praise_03', 'すごい！'],
  ['praise_04', 'かっこいい！'],
  ['praise_05', 'きれいに かけたね！'],
  ['praise_06', 'そのちょうし！'],
  ['praise_07', 'ばっちり！'],
  ['praise_08', 'はなまる！'],
  ['praise_09', 'めきめき じょうずに なってるよ！'],
];

export const RETRY: [string, string][] = [
  ['retry_01', 'もういちど やってみよう'],
  ['retry_02', 'ゆっくりで いいよ'],
  ['retry_03', 'だいじょうぶ、できるよ'],
  ['retry_04', 'おしい！'],
  ['retry_05', 'すこしずつで いいよ'],
  ['retry_06', 'いっしょに がんばろう'],
];

/** 数の読み（指示音声「◯かくめ」用） */
export const KAKU: string[] = [
  '',
  'いっかくめ',
  'にかくめ',
  'さんかくめ',
  'よんかくめ',
  'ごかくめ',
  'ろっかくめ',
];

export function kakuText(strokeNumber: number): string {
  return KAKU[strokeNumber] ?? `${strokeNumber}かくめ`;
}

export function guideText(strokeNumber: number, isFirst: boolean): string {
  const kaku = kakuText(strokeNumber);
  return isFirst ? kaku : `つぎは ${kaku}`;
}

export type FeedbackVoiceKind = 'start' | 'order' | 'offpath' | 'reverse' | 'short';

export function feedbackLine(
  kind: FeedbackVoiceKind,
  strokeNumber: number,
): { file: string; text: string } {
  switch (kind) {
    case 'start':
      return { file: 'guide/start_here', text: 'ここから はじめてね' };
    case 'order':
      return {
        file: `guide/next_is_${strokeNumber}`,
        text: `つぎは ${kakuText(strokeNumber)}だよ`,
      };
    case 'offpath':
      return { file: 'guide/on_line', text: 'せんの うえを なぞろうね' };
    case 'reverse':
      return { file: 'guide/this_way', text: 'こっちむきだよ' };
    case 'short':
      return { file: 'guide/to_end', text: 'さいごまで なぞろうね' };
  }
}

/**
 * 直前に再生したものを除外してランダム選択 (§8.1)。
 * rand は [0,1) の乱数源（テストでは固定できる）。
 */
export function pickDifferent(
  n: number,
  exclude: number,
  rand: () => number = Math.random,
): number {
  if (n <= 1) return 0;
  if (exclude < 0 || exclude >= n) return Math.floor(rand() * n);
  let idx = Math.floor(rand() * (n - 1));
  if (idx >= exclude) idx++;
  return idx;
}
