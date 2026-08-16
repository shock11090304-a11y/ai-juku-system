/**
 * 書き順判定エンジンの必須テスト (§6.7 の8ケース + §14.1)。
 */
import { describe, expect, it } from 'vitest';
import { StrokeMatcher, resolveParams } from '../strokeMatcher';
import { computeStars } from '../scoring';
import {
  decimate,
  feedStroke,
  feedbackKinds,
  lastEvent,
  loadStrokes,
  newMatcher,
  traceChar,
  withNoise,
} from './helpers';

const ALL_IDS = ['hira_shi', 'hira_ku', 'hira_i', 'hira_a'];

describe('ケース1: 理想的な軌跡 → 全画クリア・ミス0', () => {
  for (const id of ALL_IDS) {
    it(id, () => {
      const strokes = loadStrokes(id);
      const m = newMatcher(id);
      const events = traceChar(m, strokes);
      const last = lastEvent(events);
      expect(last.type).toBe('char-complete');
      if (last.type === 'char-complete') {
        expect(last.summary.mistakes).toHaveLength(0);
        expect(computeStars(last.summary)).toBe(3);
      }
    });
  }
});

describe('ケース2: ±0.03 のガウスノイズ → クリアする', () => {
  for (const id of ALL_IDS) {
    it(id, () => {
      const strokes = loadStrokes(id);
      const m = newMatcher(id);
      const events = traceChar(m, strokes, (pts, i) =>
        withNoise(pts, 0.03, 1000 + i),
      );
      expect(lastEvent(events).type).toBe('char-complete');
    });
  }
});

describe('ケース3: ±0.25 の大きなズレ → FEEDBACK_OFFPATH', () => {
  it('い の1画目を途中から大きく外れる', () => {
    const strokes = loadStrokes('hira_i');
    const m = newMatcher('hira_i');
    // 正しく書き始めてから、2点目以降を +0.25 横にずらした経路へ移る
    const shifted = strokes[0].pts.map((p, i) =>
      i === 0 ? p : { x: p.x + 0.25, y: p.y },
    );
    const events = feedStroke(m, shifted);
    expect(feedbackKinds(events)).toContain('offpath');
    // 確定済みの画はないので strokeIdx は 0 のまま
    expect(m.state.strokeIdx).toBe(0);
  });
});

describe('ケース4: 画の順番を入れ替え → FEEDBACK_ORDER', () => {
  it('い: 2画目から書こうとする', () => {
    const strokes = loadStrokes('hira_i');
    const m = newMatcher('hira_i');
    const r = m.pointerDown(strokes[1].pts[0]);
    expect(r).toMatchObject({ type: 'feedback', feedback: 'order' });
    expect(m.summary().counts.order).toBe(1);
  });

  it('あ: 2画目と3画目を入れ替えると FEEDBACK_ORDER (§14.1)', () => {
    const strokes = loadStrokes('hira_a');
    const m = newMatcher('hira_a');
    feedStroke(m, strokes[0].pts); // 1画目は正しく
    const r = m.pointerDown(strokes[2].pts[0]); // 3画目の始点に置く
    expect(r).toMatchObject({ type: 'feedback', feedback: 'order' });
  });

  it('確定済みの画の始点に触れても ORDER にはしない (§6.4 ③)', () => {
    const strokes = loadStrokes('hira_a');
    const m = newMatcher('hira_a');
    feedStroke(m, strokes[0].pts); // 1画目を確定
    const r = m.pointerDown(strokes[0].pts[0]); // 書き終えた1画目の始点
    // 2画目の始点でも後続の画の始点でもない → start 扱い（order ではない）
    expect(r).toMatchObject({ type: 'feedback', feedback: 'start' });
  });
});

describe('ケース5: 終点から始点へ描く → FEEDBACK_REVERSE', () => {
  it('し を逆からなぞる（始点が終点側）', () => {
    const strokes = loadStrokes('hira_shi');
    const m = newMatcher('hira_shi');
    const reversed = strokes[0].pts.slice().reverse();
    const events = feedStroke(m, reversed);
    expect(events[0]).toMatchObject({ type: 'feedback', feedback: 'reverse' });
    expect(m.summary().counts.reverse_start).toBe(1);
  });

  it('途中から逆走する → FEEDBACK_REVERSE', () => {
    const strokes = loadStrokes('hira_shi');
    const m = newMatcher('hira_shi');
    const pts = strokes[0].pts;
    // 20番目まで正しく進み、そこから引き返す
    const path = [...pts.slice(0, 21), ...pts.slice(8, 20).reverse()];
    const events = feedStroke(m, path);
    expect(feedbackKinds(events)).toContain('reverse');
    expect(m.summary().counts.reverse).toBe(1);
  });

  it('逆走判定より書き始めの向きを優先する（順序チェックより先 §6.4 ①）', () => {
    const strokes = loadStrokes('hira_a');
    const m = newMatcher('hira_a');
    feedStroke(m, strokes[0].pts); // 1画目を確定
    // 2画目の「終点」から書こうとする → order ではなく reverse
    const r = m.pointerDown(strokes[1].pts[63]);
    expect(r).toMatchObject({ type: 'feedback', feedback: 'reverse' });
  });
});

describe('ケース6: 画の60%で止める → FEEDBACK_SHORT', () => {
  it('し を 60% でペンを離す', () => {
    const strokes = loadStrokes('hira_shi');
    const m = newMatcher('hira_shi');
    const partial = strokes[0].pts.slice(0, 38); // 38/64 ≈ 60%
    const events = feedStroke(m, partial);
    expect(lastEvent(events)).toMatchObject({
      type: 'feedback',
      feedback: 'short',
    });
    expect(m.summary().counts.short).toBe(1);
  });
});

describe('ケース7: 点を大きく間引いた軌跡（速書き）→ 補間が効いてクリアする ★', () => {
  // 間引き幅は「1イベントの移動が文字マスの2割程度」という速書きの上限を再現する。
  // 弧長の長い画（あ の3画目）で 16 点間引きにすると1イベント 0.38 移動という
  // 非現実的な軌跡になるので、そこは 8 点間引きにする
  const FACTORS: Record<string, number> = {
    hira_shi: 16,
    hira_ku: 16,
    hira_i: 16,
    hira_a: 8,
  };
  for (const id of ALL_IDS) {
    it(id, () => {
      const strokes = loadStrokes(id);
      const m = newMatcher(id);
      const events = traceChar(m, strokes, (pts) => decimate(pts, FACTORS[id]));
      expect(lastEvent(events).type).toBe('char-complete');
    });
  }
});

describe('ケース8: 交差・ループのある文字で逆走・逸脱が誤発火しない ★', () => {
  for (const id of ['hira_a', 'hira_nu']) {
    it(`${id} を理想軌跡でなぞる`, () => {
      const strokes = loadStrokes(id);
      const m = newMatcher(id);
      const events = traceChar(m, strokes);
      const last = lastEvent(events);
      expect(last.type).toBe('char-complete');
      if (last.type === 'char-complete') {
        expect(last.summary.counts.reverse).toBe(0);
        expect(last.summary.counts.offpath).toBe(0);
      }
    });
  }

  it('ぬ のループを速書き（間引き）でも誤発火しない (§14.1)', () => {
    const strokes = loadStrokes('hira_nu');
    const m = newMatcher('hira_nu');
    const events = traceChar(m, strokes, (pts) => decimate(pts, 8));
    expect(lastEvent(events).type).toBe('char-complete');
  });
});

describe('§14.1: 難易度によって同じ軌跡の合否が変わる', () => {
  it('80% で止めた軌跡: やさしい→合格 / きびしい→FEEDBACK_SHORT', () => {
    const strokes = loadStrokes('hira_shi');
    const partial = strokes[0].pts.slice(0, 51); // 51/64 ≈ 80%

    const easy = new StrokeMatcher(strokes, resolveParams('easy', 1));
    expect(lastEvent(feedStroke(easy, partial)).type).toBe('char-complete');

    const strict = new StrokeMatcher(strokes, resolveParams('strict', 1));
    expect(lastEvent(feedStroke(strict, partial))).toMatchObject({
      type: 'feedback',
      feedback: 'short',
    });
  });

  it('Lv3（お手本なし）では1段階緩くなる (§6.5)', () => {
    expect(resolveParams('normal', 3)).toEqual(resolveParams('easy', 1));
    expect(resolveParams('strict', 3)).toEqual(resolveParams('normal', 1));
    expect(resolveParams('easy', 3)).toEqual(resolveParams('easy', 1));
  });

  it('やさしいでは逆走判定が無効 (§6.5)', () => {
    const strokes = loadStrokes('hira_shi');
    const m = new StrokeMatcher(strokes, resolveParams('easy', 1));
    const pts = strokes[0].pts;
    // 途中で引き返しても reverse は出ない（ただし完走はしないので short になる）
    const path = [...pts.slice(0, 21), ...pts.slice(8, 20).reverse()];
    const events = feedStroke(m, path);
    expect(feedbackKinds(events)).not.toContain('reverse');
  });
});

describe('やり直しの挙動 (§6.4 resetCurrentStroke)', () => {
  it('失敗しても確定済みの画は残り、同じ画からやり直せる', () => {
    const strokes = loadStrokes('hira_i');
    const m = newMatcher('hira_i');
    feedStroke(m, strokes[0].pts); // 1画目確定
    expect(m.state.strokeIdx).toBe(1);

    // 2画目を途中でやめる → short → strokeIdx は 1 のまま
    feedStroke(m, strokes[1].pts.slice(0, 20));
    expect(m.state.strokeIdx).toBe(1);
    expect(m.state.attempts).toBe(1);

    // やり直して完走 → 文字完成。short 1回なので ★2
    const events = feedStroke(m, strokes[1].pts);
    const last = lastEvent(events);
    expect(last.type).toBe('char-complete');
    if (last.type === 'char-complete') {
      expect(computeStars(last.summary)).toBe(2);
    }
  });

  it('書き順ミスがあると ★1 (§9.1)', () => {
    const strokes = loadStrokes('hira_i');
    const m = newMatcher('hira_i');
    m.pointerDown(strokes[1].pts[0]); // order ミス
    traceChar(m, strokes);
    const s = m.summary();
    expect(computeStars(s)).toBe(1);
  });

  it('3回連続失敗で consecutiveFailures が 3 になる (§7.4)', () => {
    const strokes = loadStrokes('hira_shi');
    const m = newMatcher('hira_shi');
    for (let i = 0; i < 3; i++) {
      feedStroke(m, strokes[0].pts.slice(0, 15)); // short ×3
    }
    expect(m.consecutiveFailures).toBe(3);
    // 成功でリセット
    feedStroke(m, strokes[0].pts);
    expect(m.consecutiveFailures).toBe(0);
  });

  it('describing 前の move / up は無視される', () => {
    const m = newMatcher('hira_shi');
    expect(m.pointerMove({ x: 0.5, y: 0.5 }).type).toBe('ignored');
    expect(m.pointerUp().type).toBe('ignored');
  });
});
