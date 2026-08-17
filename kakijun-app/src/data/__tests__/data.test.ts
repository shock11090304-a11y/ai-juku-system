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
        expect(s.length, `${c.id} ${s.index}画目の弧長`).toBeGreaterThan(0.03);
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

describe('全文字: 手ぶれ入力でも完走できる（実機の指書き相当）', () => {
  // 経路の法線方向に ±0.02 の揺れ + 密なイベント列 (240Hz 相当) を合成。
  // ループのある す・ず 等で吸着遅れによる逆走誤発火が起きないことの回帰テスト
  function rng(seed: number): () => number {
    let a = seed >>> 0;
    return () => {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  for (const c of characters) {
    it(`${c.id} (${c.char})`, () => {
      const strokes = prepareStrokes(c);
      const m = new StrokeMatcher(strokes, resolveParams('normal', 1));
      const rand = rng(c.id.split('').reduce((a, ch) => a + ch.charCodeAt(0), 7));
      for (const s of strokes) {
        // 4倍に細分し法線ジッタを加えた密な軌跡
        const path: { x: number; y: number }[] = [];
        for (let i = 0; i < 63; i++) {
          const a = s.pts[i];
          const b = s.pts[i + 1];
          const tx = b.x - a.x;
          const ty = b.y - a.y;
          const l = Math.hypot(tx, ty) || 1;
          for (let k = 0; k < 4; k++) {
            const t = k / 4;
            const j = (rand() * 2 - 1) * 0.02;
            path.push({
              x: a.x + tx * t + (-ty / l) * j,
              y: a.y + ty * t + (tx / l) * j,
            });
          }
        }
        path.push(s.pts[63]);
        const down = m.pointerDown(path[0]);
        expect(down.type, `${c.id} ${s.index}画目の始点`).toBe('ok');
        for (let i = 1; i < path.length; i++) {
          const r = m.pointerMove(path[i]);
          expect(r.type, `${c.id} ${s.index}画目 点${i}`).toBe('ok');
        }
        const up = m.pointerUp();
        expect(up.type, `${c.id} ${s.index}画目の完走`).toMatch(
          /stroke-ok|char-complete/,
        );
      }
    });
  }
});

describe('退化した画が無い (長さ0の画は判定エンジンを止める)', () => {
  for (const c of characters) {
    it(`${c.id} (${c.char})`, () => {
      for (const s of prepareStrokes(c)) {
        expect(s.length, `${c.id} ${s.index}画目の長さ`).toBeGreaterThan(0.03);
      }
    });
  }
});

describe('お手本 (フォント) の通りになぞっても弾かれない', () => {
  // 見本はフォント、判定は線データなので両者にズレがある。
  // 実測のズレ幅ぶん横にずらしてなぞっても通ること。
  // 0.035 = 線の太さ 0.11 の半分より少し小さい。これ以上ずらすと、
  // そ・ぬ・め のような小さい輪では内側にずらした線が反転してしまい、
  // 「人がなぞった軌跡」とは言えない形になるため検査の意味がなくなる。
  const OFFSET = 0.035;
  for (const c of characters) {
    it(`${c.id} (${c.char})`, () => {
      const strokes = prepareStrokes(c);
      const m = new StrokeMatcher(strokes, resolveParams('normal', 1));
      for (const s of strokes) {
        const path = s.pts.map((p, i) => {
          const a = s.pts[Math.max(0, i - 1)];
          const b = s.pts[Math.min(63, i + 1)];
          const tx = b.x - a.x;
          const ty = b.y - a.y;
          const l = Math.hypot(tx, ty) || 1;
          // 折れ角では寄せ幅を絞る。等距離オフセットは角で自己交差して
          // 「人がなぞった軌跡」ではなくなるため (て・ぬ 等で偽陽性になる)。
          const c = s.pts[Math.max(0, i - 2)];
          const d = s.pts[Math.min(63, i + 2)];
          const u = Math.hypot(p.x - c.x, p.y - c.y) || 1;
          const v = Math.hypot(d.x - p.x, d.y - p.y) || 1;
          const cos =
            ((p.x - c.x) * (d.x - p.x) + (p.y - c.y) * (d.y - p.y)) / (u * v);
          const k = Math.max(0, Math.min(1, (cos + 0.2) / 1.2));
          return {
            x: p.x + (-ty / l) * OFFSET * k,
            y: p.y + (tx / l) * OFFSET * k,
          };
        });
        expect(m.pointerDown(path[0]).type, `${c.id} ${s.index}画目の始点`).toBe('ok');
        for (let i = 1; i < path.length; i++) {
          expect(m.pointerMove(path[i]).type, `${c.id} ${s.index}画目 点${i}`).toBe('ok');
        }
        expect(m.pointerUp().type, `${c.id} ${s.index}画目の完走`).toMatch(
          /stroke-ok|char-complete/,
        );
      }
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
  it('濁音は base+2画・半濁音は base+1画', () => {
    for (const c of characters) {
      if (!c.composedFrom) continue;
      const base = getChar(c.composedFrom.base);
      const extra = c.composedFrom.marks.reduce(
        (n, m) => n + (m === 'mark_dakuten' ? 2 : 1),
        0,
      );
      expect(c.strokes.length, c.id).toBe(base.strokes.length + extra);
    }
  });

  it('濁点・半濁点は字の右上側にあり、マスからはみ出さない', () => {
    // ★ 以前は「x≥0.72 かつ y≤0.32 の固定枠に入っていること」を見ていたが、
    //   フォントが゛を打つ位置は字ごとに違い、固定枠のほうが誤りだった
    //   (見えている゛と書き出しの点が最大 34% ずれていた)。
    //   位置の正解はフォントしか知らないので、ここでは「常識の範囲」だけを見て、
    //   実際の一致は tools/check-start-dots.mts (お手本の墨と照合) で担保する。
    for (const c of characters) {
      if (!c.composedFrom) continue;
      const base = getChar(c.composedFrom.base);
      const markPts = c.strokes.slice(base.strokes.length).flatMap((s) => s.points);
      const basePts = base.strokes.flatMap((s) => s.points);
      const avg = (v: number[]) => v.reduce((a, b) => a + b, 0) / v.length;
      for (const p of markPts) {
        expect(p.x, `${c.id} 記号がマス外`).toBeGreaterThanOrEqual(0.05);
        expect(p.x, `${c.id} 記号がマス外`).toBeLessThanOrEqual(0.95);
        expect(p.y, `${c.id} 記号がマス外`).toBeGreaterThanOrEqual(0.05);
        expect(p.y, `${c.id} 記号がマス外`).toBeLessThanOrEqual(0.95);
      }
      // 基字より右かつ上 (濁点は右上に打つ)
      expect(avg(markPts.map((p) => p.x)), `${c.id} 記号が基字より右`).toBeGreaterThan(
        avg(basePts.map((p) => p.x)),
      );
      expect(avg(markPts.map((p) => p.y)), `${c.id} 記号が基字より上`).toBeLessThan(
        avg(basePts.map((p) => p.y)),
      );
    }
  });
});

describe('種類ごとの収録数 (§13 Phase 7: 全183項目)', () => {
  it('ひらがな80 / カタカナ80 / 数字11 / 運筆12 = 183', () => {
    expect(listByType('hiragana').length).toBe(80);
    expect(listByType('katakana').length).toBe(80);
    expect(listByType('number').length).toBe(11);
    expect(listByType('unpitsu').length).toBe(12);
    expect(characters.length).toBe(183);
  });
});
