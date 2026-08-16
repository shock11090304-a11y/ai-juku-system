/**
 * 文字データの機械検査 (§14.4 の自動化できる部分)。
 * Phase 7 で全 183 項目が入っても、このテストがそのまま全数検査になる。
 */
import { describe, expect, it } from 'vitest';
import { characters, getChar, listByType } from '../index';
import { prepareStrokes } from '../../engine/loader';
import { StrokeMatcher, resolveParams } from '../../engine/strokeMatcher';

describe('文字データの整合性', () => {
  it('id が重複していない', () => {
    const ids = characters.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('ゐ ゑ ヰ ヱ は収録しない (§14.4)', () => {
    for (const c of characters) {
      expect(['ゐ', 'ゑ', 'ヰ', 'ヱ']).not.toContain(c.char);
    }
  });

  it('全文字: 画が1つ以上・制御点2点以上・座標が 0〜1', () => {
    for (const c of characters) {
      expect(c.strokes.length, c.id).toBeGreaterThan(0);
      c.strokes.forEach((s, i) => {
        expect(s.index, `${c.id} 画番号`).toBe(i + 1);
        expect(s.points.length, `${c.id} ${i + 1}画目`).toBeGreaterThanOrEqual(2);
        for (const p of s.points) {
          expect(p.x, c.id).toBeGreaterThanOrEqual(0);
          expect(p.x, c.id).toBeLessThanOrEqual(1);
          expect(p.y, c.id).toBeGreaterThanOrEqual(0);
          expect(p.y, c.id).toBeLessThanOrEqual(1);
        }
      });
    }
  });

  it('全画がリサンプリング可能で、弧長が退化していない', () => {
    for (const c of characters) {
      for (const s of prepareStrokes(c)) {
        expect(s.pts, c.id).toHaveLength(64);
        expect(s.length, `${c.id} ${s.index}画目の弧長`).toBeGreaterThan(0.05);
      }
    }
  });

  it('読みと group が入っている', () => {
    for (const c of characters) {
      expect(c.reading.length, c.id).toBeGreaterThan(0);
      expect(c.group.length, c.id).toBeGreaterThan(0);
    }
  });
});

describe('全文字: 理想軌跡が判定エンジンを通る（自己整合性）', () => {
  // データに鋭すぎる折り返しや退化があると、正しくなぞっても
  // 逆走・逸脱と誤判定されて練習不能になる。全文字を実際になぞって検査する
  for (const c of characters) {
    it(`${c.id} (${c.char})`, () => {
      const strokes = prepareStrokes(c);
      const m = new StrokeMatcher(strokes, resolveParams('normal', 1));
      for (const s of strokes) {
        const down = m.pointerDown(s.pts[0]);
        expect(down.type, `${c.id} ${s.index}画目の始点`).toBe('ok');
        for (let i = 1; i < 64; i++) {
          const r = m.pointerMove(s.pts[i]);
          expect(r.type, `${c.id} ${s.index}画目 ${i}/63`).toBe('ok');
        }
        const up = m.pointerUp();
        expect(up.type, `${c.id} ${s.index}画目の完走`).toMatch(
          /stroke-ok|char-complete/,
        );
      }
      expect(m.state.completed, c.id).toBe(true);
      expect(m.summary().mistakes, c.id).toHaveLength(0);
    });
  }
});

describe('画数の重点確認 (§14.4)', () => {
  // 「現行の国語教科書（教科書体）で一般に通用している筆順」を基準とする
  const EXPECTED: Record<string, number> = {
    // ひらがな
    hira_a: 3, hira_i: 2, hira_u: 2, hira_e: 2, hira_o: 3,
    hira_na: 4, hira_ma: 3, hira_ho: 4, hira_yo: 2, hira_ya: 3,
    hira_se: 3, hira_yu: 2, hira_ki: 4, hira_sa: 3, hira_ri: 2,
    hira_fu: 4, hira_mo: 3,
    // カタカナ
    kata_wo: 3, kata_sa: 3, kata_ne: 4, kata_so: 2, kata_n: 2,
    kata_shi: 3, kata_tsu: 3, kata_fu: 1,
    // 数字 (「4」「5」は2画 §14.4)
    num_0: 1, num_1: 1, num_2: 1, num_3: 1, num_4: 2, num_5: 2,
  };

  for (const [id, count] of Object.entries(EXPECTED)) {
    it(`${id} は ${count}画`, () => {
      const c = characters.find((x) => x.id === id);
      if (!c) return; // まだ投入していない文字はスキップ (Phase 7 で全部入る)
      expect(c.strokes.length).toBe(count);
    });
  }
});

describe('濁音・半濁音の合成 (§14.4)', () => {
  it('濁音は base+2画・半濁音は base+1画で、濁点が右上にある', () => {
    for (const c of characters) {
      if (!c.composedFrom) continue;
      const base = getChar(c.composedFrom.base);
      const extra = c.composedFrom.marks.reduce(
        (n, m) => n + (m === 'mark_dakuten' ? 2 : 1),
        0,
      );
      expect(c.strokes.length, c.id).toBe(base.strokes.length + extra);
      // 合成された marks の座標はマスの右上 (x 0.72〜1.0, y 0〜0.32)
      for (const s of c.strokes.slice(base.strokes.length)) {
        for (const p of s.points) {
          expect(p.x, c.id).toBeGreaterThanOrEqual(0.72);
          expect(p.y, c.id).toBeLessThanOrEqual(0.32);
        }
      }
    }
  });
});

describe('種類ごとの収録数 (Phase 7 完了時の全量チェック)', () => {
  it('現時点の収録数を下回らない', () => {
    // Phase 7 完了時: ひらがな80 / カタカナ80 / 数字11 / 運筆12 = 183
    expect(listByType('hiragana').length).toBeGreaterThanOrEqual(5);
    expect(listByType('number').length).toBeGreaterThanOrEqual(6);
  });
});
