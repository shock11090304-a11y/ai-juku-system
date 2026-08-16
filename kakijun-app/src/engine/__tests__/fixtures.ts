/**
 * Phase 1 テスト用の最小データ（付録A そのまま + ループ検証用の「ぬ」）。
 * 本番データ (Phase 7) が変わってもテストが揺れないよう、ここに固定で持つ。
 */
import type { RawCharacterDef } from '../types';

export const FIXTURES: RawCharacterDef[] = [
  {
    id: 'hira_shi',
    char: 'し',
    reading: 'し',
    type: 'hiragana',
    group: 'sa-gyo',
    strokes: [
      {
        index: 1,
        hint: 'tate',
        ending: 'hane',
        points: [
          [0.38, 0.15],
          [0.36, 0.45],
          [0.4, 0.68],
          [0.55, 0.8],
          [0.72, 0.72],
          [0.78, 0.58],
        ],
      },
    ],
  },
  {
    id: 'hira_ku',
    char: 'く',
    reading: 'く',
    type: 'hiragana',
    group: 'ka-gyo',
    strokes: [
      {
        index: 1,
        hint: 'magari',
        ending: 'tome',
        points: [
          [0.62, 0.2],
          [0.4, 0.42],
          [0.34, 0.5],
          [0.42, 0.6],
          [0.64, 0.8],
        ],
      },
    ],
  },
  {
    id: 'hira_i',
    char: 'い',
    reading: 'い',
    type: 'hiragana',
    group: 'a-gyo',
    strokes: [
      {
        index: 1,
        hint: 'tate',
        ending: 'hane',
        points: [
          [0.3, 0.22],
          [0.26, 0.5],
          [0.3, 0.68],
          [0.44, 0.72],
        ],
      },
      {
        index: 2,
        hint: 'tate',
        ending: 'tome',
        points: [
          [0.68, 0.26],
          [0.76, 0.44],
          [0.85, 0.62],
        ],
      },
    ],
  },
  {
    id: 'hira_a',
    char: 'あ',
    reading: 'あ',
    type: 'hiragana',
    group: 'a-gyo',
    strokes: [
      {
        index: 1,
        hint: 'yoko',
        ending: 'tome',
        points: [
          [0.2, 0.3],
          [0.48, 0.28],
          [0.76, 0.29],
        ],
      },
      {
        index: 2,
        hint: 'tate',
        ending: 'tome',
        points: [
          [0.48, 0.14],
          [0.44, 0.45],
          [0.4, 0.72],
          [0.36, 0.88],
        ],
      },
      {
        // ★ 3画目は時計回り・自己交差あり。逆走誤判定 (§6.7 ケース8) の検証に使う
        index: 3,
        hint: 'maru',
        ending: 'harai',
        points: [
          [0.56, 0.43],
          [0.45, 0.71],
          [0.2, 0.82],
          [0.18, 0.67],
          [0.33, 0.54],
          [0.46, 0.5],
          [0.63, 0.49],
          [0.82, 0.59],
          [0.83, 0.75],
          [0.5, 0.9],
        ],
      },
    ],
  },
  {
    // 結び（小さなループ＋自己交差）を持つ「ぬ」。§14.1 のループ誤発火検証用
    id: 'hira_nu',
    char: 'ぬ',
    reading: 'ぬ',
    type: 'hiragana',
    group: 'na-gyo',
    strokes: [
      {
        index: 1,
        hint: 'naname',
        ending: 'tome',
        points: [
          [0.4, 0.14],
          [0.28, 0.45],
          [0.14, 0.78],
        ],
      },
      {
        index: 2,
        hint: 'maru',
        ending: 'harai',
        points: [
          [0.6, 0.12],
          [0.38, 0.35],
          [0.3, 0.62],
          [0.42, 0.82],
          [0.62, 0.78],
          [0.72, 0.55],
          [0.62, 0.38],
          [0.5, 0.55],
          [0.55, 0.72],
          [0.72, 0.8],
          [0.85, 0.7],
        ],
      },
    ],
  },
];

export function fixture(id: string): RawCharacterDef {
  const def = FIXTURES.find((c) => c.id === id);
  if (!def) throw new Error(`fixture not found: ${id}`);
  return def;
}
