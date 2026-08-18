/**
 * 型定義 (§4.1)。
 * engine/ 以下は UI・DOM・Canvas に一切依存しない純粋ロジック (§2.1)。
 */

/** 正規化座標。文字の外接マス（正方形）を 0.0〜1.0 とする。原点は左上。 */
export type Pt = { x: number; y: number };

/** JSON データ内の座標表現（コンパクトさのためタプル） */
export type RawPt = [number, number];

export type StrokeHint =
  | 'tate'
  | 'yoko'
  | 'naname'
  | 'magari'
  | 'maru'
  | 'haneru'
  | 'harau';

export type StrokeEnding = 'tome' | 'hane' | 'harai';

export type Stroke = {
  /** 1画目から順の通し番号（1始まり） */
  index: number;
  /** 画の中心線を表す制御点列。始点→終点の順。最低2点。 */
  points: Pt[];
  /** 幼児向けのひとこと指示（音声ファイル名の決定にも使う） */
  hint: StrokeHint;
  /** 終筆の処理。見本アニメと採点表示に使う */
  ending?: StrokeEnding;
};

/** JSON ファイル上のストローク（points がタプル配列） */
export type RawStroke = Omit<Stroke, 'points'> & { points: RawPt[] };

export type CharType = 'hiragana' | 'katakana' | 'number' | 'unpitsu';

export type CharacterDef = {
  id: string; // 'hira_a', 'kata_a', 'num_3', 'unpitsu_zigzag'
  char: string; // 'あ'
  reading: string; // 'あ'（読み上げ用）
  type: CharType;
  /** 学習順のグループ。CharSelectScreen の並び順に使う */
  group: string; // 'a-gyo', 'ka-gyo', 'dakuon', '0-5', ...
  strokes: Stroke[];
  /**
   * 濁音・半濁音のための合成定義 (§4.3)。
   * markOffset = 記号を動かす量。フォントが゛を打つ位置は字ごとに違うので、
   * 共有の marks.json をそのまま置くと見えている記号と書き出しの点がずれる。
   * tools/fit-marks.mts が実測して入れる。
   */
  composedFrom?: { base: string; marks: string[]; markOffset?: [number, number] };
  /** 絵カード（例: あ → あり） */
  sample?: { word: string; image: string; audio: string };
};

export type RawCharacterDef = Omit<CharacterDef, 'strokes'> & {
  strokes: RawStroke[];
};

/** 判定用に前処理（スプライン補間 + 等間隔 64 点リサンプリング）済みの画 (§6.1) */
export type ResampledStroke = {
  index: number;
  /** 弧長に沿って等間隔な 64 点。pts[0] が始点、pts[63] が終点 */
  pts: Pt[];
  /** 弧長 L。許容量はすべてこの値に対する相対値 (§6.3) */
  length: number;
  hint: StrokeHint;
  ending?: StrokeEnding;
};

/** ミスの種類。採点 (§9.1) と保護者ダッシュボードのつまずき分析 (§10.2) に使う */
export type MistakeKind =
  | 'start' // 始点が違う
  | 'order' // 書き順の飛ばし (MISTAKE_ORDER)
  | 'reverse_start' // 画を終点側から書き始めた
  | 'reverse' // 途中で逆走した
  | 'offpath' // 経路から外れた
  | 'short'; // 最後まで書かずに離した

export type MistakeLog = { kind: MistakeKind; strokeIdx: number };

/** 判定パラメータ (§6.3, §6.5)。許容量は画の弧長 L に対する相対値 */
export type MatchParams = {
  TOL_RATIO: number;
  TOL_MIN: number;
  TOL_MAX: number;
  LOOKAHEAD: number;
  REVERSE_DOT: number;
  REVERSE_RUN: number;
  OFF_DIST: number;
  DONE_RATE: number;
  /** 「やさしい」では逆走判定を無効にする (§6.5) */
  reverseEnabled: boolean;
  /**
   * ★なぞり判定 (経路逸脱・逆走・到達率) を行うか。
   * アプリは false で使う (2026-08-18 塾長指示: 判定は書き出しの位置と順番だけ。
   * 経路は画面に見せていないのに「せんのうえをなぞってね」と叱られるのは
   * 子どもには意味が分からない)。true は単体テストと教材データの品質検査用
   * (理想軌跡が通ることをデータの健全性の基準として使い続ける)。
   */
  pathJudge: boolean;
};

/** 判定のきびしさ（保護者設定） */
export type Strictness = 'easy' | 'normal' | 'strict';

/** ガイドの3段階 (§5.4): 1=なぞる 2=うすいお手本 3=じぶんで */
export type GuideLevel = 1 | 2 | 3;

export type Stars = 0 | 1 | 2 | 3;

/** 1回の練習の結果まとめ（採点の入力） */
export type AttemptSummary = {
  mistakes: MistakeLog[];
  counts: Record<MistakeKind, number>;
};

export const MISTAKE_KINDS: MistakeKind[] = [
  'start',
  'order',
  'reverse_start',
  'reverse',
  'offpath',
  'short',
];

export function emptyMistakeCounts(): Record<MistakeKind, number> {
  return {
    start: 0,
    order: 0,
    reverse_start: 0,
    reverse: 0,
    offpath: 0,
    short: 0,
  };
}
