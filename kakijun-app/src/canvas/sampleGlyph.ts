/**
 * ★ お手本の字をどう描くか。ここが唯一の正典。
 *
 * 字形を測る/合わせ込むツールは、必ずこの条件と同じ描き方をすること。
 * 違う条件で描くと「子どもが見ている字とは別の字」に合わせ込むことになる。
 * 実際に refit-glyphs / dump-masks / glyph-mask が 0.88em・中央で描いており、
 * 忠実度 76% という数字自体が誤りだった (アプリ条件で測ると 49.3% だった。2026-08-17)。
 *
 * ツール側 (plain .mjs で動くもの) は tools/ref-font.mjs に写しを置いている。
 * 両者がずれていないことは src/canvas/__tests__/sampleGlyph.test.ts が機械で見る。
 */
export const SAMPLE_FONT_FAMILY = 'KakijunSample';
/** 字の大きさ = マス1辺に対する font-size の比 */
export const SAMPLE_FONT_RATIO = 0.86;
/** 字の縦位置 = マス1辺に対する基線 (textBaseline=middle) の比 */
export const SAMPLE_BASELINE_RATIO = 0.52;

/** お手本の字を描く (背景層)。色は呼び出し側が決める */
export function drawSampleGlyph(
  ctx: CanvasRenderingContext2D,
  char: string,
  size: number,
  color: string,
): void {
  ctx.save();
  ctx.fillStyle = color;
  ctx.font = `${size * SAMPLE_FONT_RATIO}px ${SAMPLE_FONT_FAMILY}, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(char, size / 2, size * SAMPLE_BASELINE_RATIO);
  ctx.restore();
}
