/**
 * 書き順判定エンジンの必須テスト (§6.7 の8ケース + §14.1)。
 */
import { describe, expect, it } from 'vitest';
import { StrokeMatcher, resolveParams, startTol } from '../strokeMatcher';
import { computeStars } from '../scoring';
import { prepareStrokes, toCharacterDef } from '../loader';
import { shakyPaths } from '../traceProfiles';
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
    // 25番目まで正しく進み、そこから引き返す
    // (向きの評価は移動距離で量子化されるため、確定には数サンプルぶんの逆走が要る)
    const path = [...pts.slice(0, 26), ...pts.slice(2, 25).reverse()];
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

describe('実機で起きる端点（総点検で確定した不具合の回帰テスト）', () => {
  it('cancelStroke は途中中断をミス扱いにしない (pointercancel)', () => {
    const strokes = loadStrokes('hira_shi');
    const m = newMatcher('hira_shi');
    m.pointerDown(strokes[0].pts[0]);
    for (let i = 1; i < 30; i++) m.pointerMove(strokes[0].pts[i]);
    m.cancelStroke();
    expect(m.state.drawing).toBe(false);
    expect(m.state.attempts).toBe(0);
    expect(m.summary().mistakes).toHaveLength(0);
    expect(m.consecutiveFailures).toBe(0);
    // 中断後は最初からやり直して普通に完走できる
    const events = feedStroke(m, strokes[0].pts);
    expect(lastEvent(events).type).toBe('char-complete');
  });

  it('drawing のまま次の pointerDown が来ても仕切り直す (cancel 取りこぼし)', () => {
    const strokes = loadStrokes('hira_shi');
    const m = newMatcher('hira_shi');
    m.pointerDown(strokes[0].pts[0]);
    for (let i = 1; i < 20; i++) m.pointerMove(strokes[0].pts[i]);
    // pointerup を挟まず新しいタッチ
    const r = m.pointerDown(strokes[0].pts[0]);
    expect(r.type).toBe('ok');
    for (let i = 1; i < 64; i++) m.pointerMove(strokes[0].pts[i]);
    expect(m.pointerUp().type).toBe('char-complete');
    expect(m.summary().mistakes).toHaveLength(0);
  });

  it('濁点サイズの画でも始点ターゲットは指サイズ (0.045) 以上ある', () => {
    // 弧長 0.12 程度の短い画 (tol は 0.03 に張り付く)
    const short = prepareTiny([
      { x: 0.8, y: 0.1 },
      { x: 0.87, y: 0.2 },
    ]);
    const m = new StrokeMatcher(short, resolveParams('normal', 1));
    // 始点から 0.04 ずれたタップ (旧実装では弾かれていた)
    const r = m.pointerDown({ x: 0.8 - 0.028, y: 0.1 - 0.028 });
    expect(r.type).toBe('ok');
  });

  it('短い画では「始点許容内なのに終点寄り」を逆書きにしない', () => {
    const short = prepareTiny([
      { x: 0.4, y: 0.4 },
      { x: 0.48, y: 0.4 },
    ]);
    const m = new StrokeMatcher(short, resolveParams('normal', 1));
    // 中央やや終点寄り: dStart=0.042 ≤ T(0.045), dEnd=0.038 < dStart
    const r = m.pointerDown({ x: 0.442, y: 0.4 });
    expect(r.type).toBe('ok');
  });

  it('終点まで到達した後のはみ出し (終筆の勢い) は逸脱・逆走にしない', () => {
    const strokes = loadStrokes('hira_shi');
    const m = newMatcher('hira_shi');
    const pts = strokes[0].pts;
    const path = [...pts];
    // 終点の先へ接線方向に大きく滑る
    const end = pts[63];
    const prev = pts[60];
    const tx = end.x - prev.x;
    const ty = end.y - prev.y;
    const l = Math.hypot(tx, ty) || 1;
    for (let k = 1; k <= 10; k++) {
      path.push({ x: end.x + (tx / l) * 0.02 * k, y: end.y + (ty / l) * 0.02 * k });
    }
    const events = feedStroke(m, path);
    expect(lastEvent(events).type).toBe('char-complete');
    expect(m.summary().counts.offpath).toBe(0);
    expect(m.summary().counts.reverse).toBe(0);
  });

  it('始点外れタップは連続失敗カウント (自動レベルダウン) に数えない', () => {
    const m = newMatcher('hira_shi');
    for (let i = 0; i < 5; i++) {
      const r = m.pointerDown({ x: 0.95, y: 0.95 });
      expect(r).toMatchObject({ type: 'feedback', feedback: 'start' });
    }
    expect(m.consecutiveFailures).toBe(0);
    expect(m.summary().counts.start).toBe(5); // 記録には残る
  });
});

function prepareTiny(control: { x: number; y: number }[]) {
  // テスト用: 制御点から直接 ResampledStroke を作る
  return prepareStrokes(
    toCharacterDef({
      id: 'test_tiny',
      char: '゛',
      reading: 'てん',
      type: 'hiragana',
      group: 'test',
      strokes: [
        {
          index: 1,
          hint: 'naname',
          ending: 'tome',
          points: control.map((p) => [p.x, p.y] as [number, number]),
        },
      ],
    }),
  );
}

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

describe('★曲率のきつい画: 正しくなぞった手ぶれを逆走と誤判定しない (2026-08-17)', () => {
  // 字形をお手本に合わせ込むほど輪が忠実になり、す・そ・カ・る で
  // 「手ぶれ入力が逆走扱い」になってデータを入れられなかった。
  // 原因は尺度の不一致: 手の動きは距離 0.045 以上の弦で測るのに、
  // 経路側は隣り合う2点の接線と比べていた。曲率のきつい所では
  // 正しく前進していても大きな角度差が出る。
  // ここでは輪を持つ画を合成し、手ぶれを乗せても完走できることを見る。
  function loopStroke(radius: number): { x: number; y: number }[] {
    // 上から入って一周し、右下へ抜ける「結び」の形
    const pts: { x: number; y: number }[] = [{ x: 0.5 - radius, y: 0.2 }];
    for (let k = 0; k <= 8; k++) {
      const a = -Math.PI / 2 + (k / 8) * Math.PI * 2;
      pts.push({ x: 0.5 + Math.cos(a) * radius, y: 0.5 + Math.sin(a) * radius });
    }
    pts.push({ x: 0.5 + radius * 1.6, y: 0.8 });
    return pts;
  }

  for (const radius of [0.05, 0.06, 0.07, 0.08, 0.11, 0.15]) {
    it(`半径 ${radius} の輪を手ぶれ付きでなぞって完走する`, () => {
      const strokes = prepareTiny(loopStroke(radius));
      const m = new StrokeMatcher(strokes, resolveParams('normal', 1));
      const paths = shakyPaths(strokes, `loop_${radius}`);
      const events = feedStroke(m, paths[0]);
      expect(feedbackKinds(events), `半径 ${radius}`).not.toContain('reverse');
      expect(lastEvent(events).type).toBe('char-complete');
    });
  }

  /**
   * ★ これが実際に起きた形。合成した円では再現しない。
   * す の2画目を手本フォントの墨から引き直したもの (忠実度 24%→94%)。
   * 「結び」で経路が鋭く折り返す所で、旧エンジンは手ぶれを逆走と誤判定し、
   * この字形を入れられなかった。★数値はここに固定で持つ (JSON を直しても
   * この回帰テストは生き続ける)。
   */
  const SU_STROKES: [number, number][][] = [
    [[0.242, 0.373], [0.721, 0.316]],
    [
      [0.539, 0.189], [0.561, 0.357], [0.48, 0.467], [0.43, 0.584], [0.5, 0.641],
      [0.578, 0.559], [0.543, 0.439], [0.578, 0.605], [0.531, 0.73], [0.424, 0.859],
    ],
  ];

  it('す の結び (お手本から引き直した実データ) を手ぶれ付きでなぞって完走する', () => {
    // ★手ぶれの乱数は1字で1本。1画目を通したあとの揺れでないと再現しない
    const def = toCharacterDef({
      id: 'hira_su',
      char: 'す',
      reading: 'す',
      type: 'hiragana',
      group: 'sa-gyo',
      strokes: SU_STROKES.map((points, i) => ({
        index: i + 1,
        hint: 'magari' as const,
        ending: 'tome' as const,
        points,
      })),
    });
    const strokes = prepareStrokes(def);
    const m = new StrokeMatcher(strokes, resolveParams('normal', 1));
    const paths = shakyPaths(strokes, 'hira_su');
    const events = [...feedStroke(m, paths[0]), ...feedStroke(m, paths[1])];
    expect(feedbackKinds(events)).not.toContain('reverse');
    expect(lastEvent(events).type).toBe('char-complete');
  });

  it('本当に引き返したときは輪の中でも逆走を出す', () => {
    const strokes = prepareTiny(loopStroke(0.11));
    const m = new StrokeMatcher(strokes, resolveParams('normal', 1));
    const pts = strokes[0].pts;
    // 30番まで進んでから、来た道を戻る
    const path = [...pts.slice(0, 31), ...pts.slice(4, 30).reverse()];
    const events = feedStroke(m, path);
    expect(feedbackKinds(events)).toContain('reverse');
  });
});

describe('★開始のみモード pathJudge:false (アプリの既定。2026-08-18 塾長指示)', () => {
  // 経路は画面に見せていないのに「せんのうえをなぞってね」「ぎゃくむきだよ」と
  // 叱られるのは子どもには意味が分からない。アプリの判定は
  // 「書き出しの位置」と「画の順番」だけにする。
  const startOnly = { ...resolveParams('normal', 1), pathJudge: false };

  it('正しい書き出しから、経路と無関係にぐちゃぐちゃ描いても完走する', () => {
    const strokes = loadStrokes('hira_shi');
    const m = new StrokeMatcher(strokes, startOnly);
    const start = strokes[0].pts[0];
    // 従来判定なら即 offpath/reverse になるジグザグ
    const path = [start];
    for (let i = 1; i <= 20; i++) {
      path.push({
        x: start.x + (i % 2 ? 0.3 : 0.05),
        y: start.y + i * 0.02,
      });
    }
    const events = feedStroke(m, path);
    expect(feedbackKinds(events)).toEqual([]);
    expect(lastEvent(events).type).toBe('char-complete');
  });

  it('タップだけでは画が進まない (short で書き出しへ誘導)', () => {
    const strokes = loadStrokes('hira_shi');
    const m = new StrokeMatcher(strokes, startOnly);
    const start = strokes[0].pts[0];
    const events = feedStroke(m, [start, { x: start.x + 0.005, y: start.y }]);
    expect(lastEvent(events)).toMatchObject({ type: 'feedback', feedback: 'short' });
    // やり直して普通に描けば通る
    const path = [start];
    for (let i = 1; i <= 20; i++) {
      path.push({ x: start.x + i * 0.02, y: start.y + i * 0.025 });
    }
    expect(lastEvent(feedStroke(m, path)).type).toBe('char-complete');
  });

  it('書き出しの位置と順番の判定は生きている', () => {
    const strokes = loadStrokes('hira_i');
    const m = new StrokeMatcher(strokes, startOnly);
    // 2画目から書こうとする → order
    expect(m.pointerDown(strokes[1].pts[0])).toMatchObject({
      type: 'feedback',
      feedback: 'order',
    });
    // 何もない所 → start
    expect(m.pointerDown({ x: 0.95, y: 0.95 })).toMatchObject({
      type: 'feedback',
      feedback: 'start',
    });
    // 逆側 (現在の画の終点) から → reverse
    const shi = new StrokeMatcher(loadStrokes('hira_shi'), startOnly);
    expect(shi.pointerDown(loadStrokes('hira_shi')[0].pts[63])).toMatchObject({
      type: 'feedback',
      feedback: 'reverse',
    });
  });

  it('書き出しの受付半径は 0.13 で頭打ちになる (経路を見ないぶん狭める)', () => {
    // 長い画では tol が TOL_MAX=0.28 (マス1/3) まで膨らむ。経路判定があった頃は
    // 書き出しが甘くても経路で正されたが、開始のみ判定では書き出しが全てなので、
    // マスの別の場所から書いても通ってしまう
    expect(startTol(2.0, resolveParams('normal', 1))).toBeCloseTo(0.28);
    expect(startTol(2.0, startOnly)).toBeCloseTo(0.13);
    // 短い画の下限 (指のタップ精度) はそのまま
    expect(startTol(0.05, startOnly)).toBeCloseTo(0.075);
  });

  it('複数画の字も、順に書き出せば自由な線で完走する', () => {
    const strokes = loadStrokes('hira_i');
    const m = new StrokeMatcher(strokes, startOnly);
    for (const s of strokes) {
      const start = s.pts[0];
      const path = [start];
      for (let i = 1; i <= 16; i++) {
        path.push({
          x: Math.min(0.98, start.x + (i % 2 ? 0.22 : 0.06)),
          y: Math.min(0.98, start.y + i * 0.02),
        });
      }
      const events = feedStroke(m, path);
      expect(feedbackKinds(events)).toEqual([]);
    }
    expect(m.state.completed).toBe(true);
  });
});
