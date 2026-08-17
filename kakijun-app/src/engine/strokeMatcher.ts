/**
 * ★ 書き順判定エンジン本体 (§6)。
 * Canvas・DOM・React に一切依存しない。座標はすべて正規化座標 (0〜1)。
 */
import type {
  AttemptSummary,
  GuideLevel,
  MatchParams,
  MistakeKind,
  MistakeLog,
  Pt,
  ResampledStroke,
  Strictness,
} from './types';
import { emptyMistakeCounts } from './types';
import { clamp, dist, dot, interpolateSegment, normalize, sub, vlen } from './geometry';

const N = 64; // 1画あたりのサンプル数 (§6.1)
const LAST = N - 1;

/** 難易度によらない共通パラメータ (§6.3) */
const COMMON = {
  LOOKAHEAD: 10,
  REVERSE_DOT: -0.3,
  REVERSE_RUN: 3,
} as const;

/** 難易度3段階 (§6.5) */
const PRESETS: Record<Strictness, Omit<MatchParams, keyof typeof COMMON>> = {
  easy: {
    TOL_RATIO: 0.35,
    TOL_MIN: 0.045,
    TOL_MAX: 0.22,
    OFF_DIST: 0.1,
    DONE_RATE: 0.75,
    reverseEnabled: false,
  },
  normal: {
    TOL_RATIO: 0.25,
    TOL_MIN: 0.03,
    TOL_MAX: 0.16,
    OFF_DIST: 0.06,
    DONE_RATE: 0.88,
    reverseEnabled: true,
  },
  strict: {
    TOL_RATIO: 0.18,
    TOL_MIN: 0.022,
    TOL_MAX: 0.11,
    OFF_DIST: 0.04,
    DONE_RATE: 0.95,
    reverseEnabled: true,
  },
};

const ORDER: Strictness[] = ['easy', 'normal', 'strict'];

/**
 * きびしさ + ガイドレベルから実際のパラメータを決める。
 * Lv3（お手本なし）では自動的に1段階緩める (§5.4, §6.5)。
 */
export function resolveParams(
  strictness: Strictness,
  guideLevel: GuideLevel,
): MatchParams {
  let s = strictness;
  if (guideLevel === 3) {
    s = ORDER[Math.max(0, ORDER.indexOf(strictness) - 1)];
  }
  return { ...PRESETS[s], ...COMMON };
}

/** 許容半径。画の弧長 L に対する相対値 (§6.3 ★ 固定値にしない) */
export function tol(L: number, p: MatchParams): number {
  return clamp(L * p.TOL_RATIO, p.TOL_MIN, p.TOL_MAX);
}

/**
 * 書き始め (pointerDown) 専用の許容半径。
 * 濁点や小書き字では tol が 0.03 (600px 画面で約18px) まで縮み、
 * 幼児の指では狙えない「始点弾かれループ」になるため、
 * 始点判定に限り指のタップサイズ相当の下限を敷く。
 */
const START_TOL_FLOOR = 0.045;
export function startTol(L: number, p: MatchParams): number {
  return Math.max(tol(L, p), START_TOL_FLOOR);
}

/** 入力補間の刻み (§6.3 ★ 固定値にしない) */
export function step(L: number): number {
  return (L / LAST) * 0.5;
}

export type Feedback = 'start' | 'order' | 'reverse' | 'offpath' | 'short';

export type MatcherResult =
  | { type: 'ok' }
  | { type: 'ignored' }
  | { type: 'feedback'; feedback: Feedback; strokeIdx: number }
  | { type: 'stroke-ok'; committedIdx: number; nextIdx: number }
  | { type: 'char-complete'; summary: AttemptSummary };

/** 判定の状態 (§6.2) */
type MatchState = {
  strokeIdx: number; // いま書くべき画（0始まり）
  progress: number; // 現在の画の到達インデックス（0〜63）
  offDist: number; // 経路から外れたまま進んだ累積移動距離
  reverseRun: number; // 進行方向が逆を向いた連続回数
  pPrev: Pt | null; // 直前の判定点
  /** 逆走の向き判定の基準点。ここから一定距離動くたびに向きを1回評価する */
  dirAnchor: Pt | null;
  attempts: number; // 現在の画のやり直し回数
  mistakes: MistakeLog[]; // 文字全体のミス記録（採点用）
  drawing: boolean;
  completed: boolean;
};

export class StrokeMatcher {
  private readonly strokes: ResampledStroke[];
  private params: MatchParams;
  private st: MatchState;
  /** 連続失敗回数。3回でガイドを1段階易しくする (§7.4)。画の成功でリセット */
  consecutiveFailures = 0;

  constructor(strokes: ResampledStroke[], params: MatchParams) {
    if (strokes.length === 0) throw new Error('strokes must not be empty');
    this.strokes = strokes;
    this.params = params;
    this.st = {
      strokeIdx: 0,
      progress: 0,
      offDist: 0,
      reverseRun: 0,
      pPrev: null,
      dirAnchor: null,
      attempts: 0,
      mistakes: [],
      drawing: false,
      completed: false,
    };
  }

  /** ガイドレベル自動変更時などに、書きかけの状態を保ったまま許容量だけ変える */
  setParams(params: MatchParams): void {
    this.params = params;
  }

  get state(): Readonly<MatchState> {
    return this.st;
  }

  get currentStroke(): ResampledStroke {
    return this.strokes[Math.min(this.st.strokeIdx, this.strokes.length - 1)];
  }

  private log(kind: MistakeKind): void {
    this.st.mistakes.push({ kind, strokeIdx: this.st.strokeIdx });
  }

  /**
   * 現在の画の筆跡だけを消してやり直し。確定済みの画は残す (§6.4 ★)。
   */
  private resetCurrentStroke(): void {
    this.st.progress = 0;
    this.st.offDist = 0;
    this.st.reverseRun = 0;
    this.st.pPrev = null;
    this.st.dirAnchor = null;
    this.st.drawing = false;
    this.st.attempts++;
    this.consecutiveFailures++;
  }

  /**
   * pointercancel (エッジスワイプ・通知バナー等) 用の中断。
   * ミスとして記録せず、やり直し回数も進めない。
   * これを呼ばないと drawing=true のまま残り、次のタッチが
   * 前の画の続きとして誤判定される。
   */
  cancelStroke(): void {
    this.st.progress = 0;
    this.st.offDist = 0;
    this.st.reverseRun = 0;
    this.st.pPrev = null;
    this.st.dirAnchor = null;
    this.st.drawing = false;
  }

  private fail(feedback: Feedback): MatcherResult {
    return { type: 'feedback', feedback, strokeIdx: this.st.strokeIdx };
  }

  /** ── ペンを置いたとき (§6.4) ─────────────────────────── */
  pointerDown(p: Pt): MatcherResult {
    if (this.st.completed) return { type: 'ignored' };
    // pointercancel を取りこぼした後などに drawing のまま来たら黙って仕切り直す
    if (this.st.drawing) this.cancelStroke();
    const s = this.strokes[this.st.strokeIdx];
    const T = startTol(s.length, this.params);
    const dStart = dist(p, s.pts[0]);
    const dEnd = dist(p, s.pts[LAST]);

    // ① まず「この画を逆から書こうとしている」を見る（順序チェックより先に）。
    //    ただし始点と終点がほぼ同じ閉じた画（運筆の円など）では区別できないので除外する。
    //    ★dStart > T も条件に入れる: 短い画では始点・終点の許容円が重なり、
    //      正しい始点タッチが「わずかに終点寄り」なだけで逆書き扱いになるため
    const closed = dist(s.pts[0], s.pts[LAST]) <= T;
    if (!closed && dEnd <= T && dEnd < dStart && dStart > T) {
      this.log('reverse_start');
      this.consecutiveFailures++;
      return this.fail('reverse'); // 「こっちから かいてみよう」
    }

    // ② 正しい始点
    if (dStart <= T) {
      this.st.drawing = true;
      this.st.progress = 0;
      this.st.offDist = 0;
      this.st.reverseRun = 0;
      this.st.pPrev = p;
      this.st.dirAnchor = p;
      return { type: 'ok' };
    }

    // ③ これから書く画の始点に近い → 書き順の飛ばし。
    //    ★ strokeIdx より前（確定済み）の画は対象にしない
    for (let i = this.st.strokeIdx + 1; i < this.strokes.length; i++) {
      const t = this.strokes[i];
      if (dist(p, t.pts[0]) <= startTol(t.length, this.params)) {
        this.log('order');
        this.consecutiveFailures++;
        return this.fail('order'); // 「つぎは ◯かくめだよ」
      }
    }

    // 始点外れは記録するが、連続失敗カウント (自動レベルダウン) には数えない。
    // 手のひらの接地など「書く意思のないタッチ」で3回に達して
    // 勝手に易しくなるのを防ぐ。書きはじめた後の失敗だけを数える
    this.log('start');
    return this.fail('start'); // 始点の丸を大きく点滅
  }

  /** ── ペンを動かしたとき (§6.4) ───────────────────────── */
  pointerMove(pRaw: Pt): MatcherResult {
    if (!this.st.drawing || this.st.completed) return { type: 'ignored' };
    const s = this.strokes[this.st.strokeIdx];
    const h = step(s.length);
    const pEventStart = this.st.pPrev ?? pRaw;

    // ★ 生のイベント点だけで判定しない。前回の判定点との間を h 刻みで線形補間する。
    //   （速く書くとイベントが飛び、経路をショートカットしたと誤判定するため）
    const pts = interpolateSegment(pEventStart, pRaw, h);
    let lastOnPathJ = -1;
    for (const p of pts) {
      const r = this.judgePoint(p, s, (j) => (lastOnPathJ = j));
      if (r) return r;
    }

    // --- 逆走: 「位置」ではなく「進む向き」で判定する (★★ §6.4) ---
    //   ★イベント単位でも補間点単位でも数えない。高頻度入力 (Apple Pencil は
    //     240Hz) では1イベントの移動が手ぶれより小さく、向きがノイズになる。
    //     「基準点から一定距離 (指の揺れより大きい) 動くごとに1回」向きを評価し、
    //     それが REVERSE_RUN 回連続で逆だったら逆走と確定する。
    //   ★終点近くまで到達した後 (progress ≥ DONE_RATE) は数えない:
    //     はらいの勢い余りが逆走扱いになるのを防ぐ (pointerUp で完走になる)
    const doneZone = this.st.progress >= LAST * this.params.DONE_RATE;
    if (this.params.reverseEnabled && !doneZone && this.st.dirAnchor) {
      // このイベントに経路上の点が無くても (すでに外れている最中でも)、
      // 到達済みの progress 位置の接線で向きを見続ける。
      // ここで止めると逆走中に reverseRun が伸びず、常に offpath 扱いになる
      const jDir = lastOnPathJ >= 0 ? lastOnPathJ : this.st.progress;
      const D = Math.max(3 * h, 0.045); // 向き1評価あたりの移動距離
      const motion = sub(pRaw, this.st.dirAnchor);
      if (vlen(motion) >= D) {
        const tangent = normalize(
          sub(s.pts[Math.min(jDir + 1, LAST)], s.pts[Math.max(jDir - 1, 0)]),
        );
        // ループ (す・ぬ・結び) では吸着点 j が実際の筆先より遅れ、遅れた j の
        // 接線と実運筆方向が見かけ上反転する。「この先の経路へ近づいているか」も
        // 見て、前進中の揺れを逆走に数えない
        const ahead = s.pts[Math.min(jDir + 3, LAST)];
        const toAhead = sub(ahead, this.st.dirAnchor);
        const approaching =
          vlen(toAhead) === 0 ||
          dot(normalize(motion), normalize(toAhead)) > 0;
        if (
          !approaching &&
          dot(normalize(motion), tangent) < this.params.REVERSE_DOT
        ) {
          this.st.reverseRun++;
          if (this.st.reverseRun >= this.params.REVERSE_RUN) {
            this.log('reverse');
            this.resetCurrentStroke();
            return this.fail('reverse'); // 「ぎゃくむきだよ」
          }
        } else {
          this.st.reverseRun = 0;
        }
        this.st.dirAnchor = pRaw;
      }
    }
    return { type: 'ok' };
  }

  private judgePoint(
    p: Pt,
    s: ResampledStroke,
    onPathMatched: (j: number) => void,
  ): MatcherResult | null {
    const T = tol(s.length, this.params);
    const st = this.st;

    // --- 前方一致 ---
    const kMax = Math.min(st.progress + this.params.LOOKAHEAD, LAST);
    let j = st.progress;
    let d = dist(p, s.pts[j]);
    for (let k = st.progress + 1; k <= kMax; k++) {
      const dk = dist(p, s.pts[k]);
      if (dk < d) {
        d = dk;
        j = k;
      }
    }

    // --- 経路逸脱: 「累積移動距離」で測る (★ サンプル数で測らない §6.6) ---
    if (d > T) {
      // 終点近くまで到達済みなら、はみ出しは「終筆の勢い」なので数えない
      // (濁点のはらいが数十px はみ出しただけで全消しになるのを防ぐ。
      //  完走判定は pointerUp の DONE_RATE がそのまま行う)
      if (st.progress >= LAST * this.params.DONE_RATE) {
        st.pPrev = p;
        return null;
      }
      if (st.pPrev) st.offDist += dist(p, st.pPrev);
      st.pPrev = p;
      if (st.offDist > this.params.OFF_DIST) {
        this.log('offpath');
        this.resetCurrentStroke();
        return this.fail('offpath'); // 「せんの うえを なぞってね」
      }
      return null;
    }
    st.offDist = 0;
    onPathMatched(j);
    st.progress = Math.max(st.progress, j);
    st.pPrev = p;
    return null;
  }

  /** ── ペンを離したとき (§6.4) ─────────────────────────── */
  pointerUp(): MatcherResult {
    if (!this.st.drawing || this.st.completed) return { type: 'ignored' };
    const st = this.st;
    if (st.progress >= LAST * this.params.DONE_RATE) {
      const committedIdx = st.strokeIdx;
      st.strokeIdx++;
      st.progress = 0;
      st.offDist = 0;
      st.reverseRun = 0;
      st.pPrev = null;
      st.dirAnchor = null;
      st.attempts = 0;
      st.drawing = false;
      this.consecutiveFailures = 0;
      if (st.strokeIdx >= this.strokes.length) {
        st.completed = true;
        return { type: 'char-complete', summary: this.summary() };
      }
      return { type: 'stroke-ok', committedIdx, nextIdx: st.strokeIdx }; // 「じょうず！」
    }
    this.log('short');
    this.resetCurrentStroke();
    return this.fail('short'); // 「さいごまで なぞろうね」
  }

  summary(): AttemptSummary {
    const counts = emptyMistakeCounts();
    for (const m of this.st.mistakes) counts[m.kind]++;
    return { mistakes: this.st.mistakes.slice(), counts };
  }
}
