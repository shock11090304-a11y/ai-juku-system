/**
 * ★ お手本の描き方が「見せる側」と「測る側」でずれていないかの検査。
 *
 * 2026-08-17 の事故: 字形ツールが 0.88em・中央でお手本を描いてお手本扱いしていたが、
 * アプリは 0.86em・y=0.52 で描いていた。別の字に合わせ込んでいたので、
 * 「忠実度 76%」という数字自体が誤りだった (アプリ条件では 49.3%)。
 * 写しを持つ以上、ずれたら機械で気づけるようにしておく。
 */
import { describe, expect, it } from 'vitest';
import { SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from '../sampleGlyph';
// @ts-expect-error 型定義のない開発用ヘルパ (plain .mjs)
import { SAMPLE_FONT_RATIO as TOOL_FONT, SAMPLE_BASELINE_RATIO as TOOL_BASE } from '../../../tools/ref-font.mjs';

describe('お手本の描き方は1か所で決める', () => {
  it('アプリ (src/canvas/sampleGlyph.ts) と字形ツール (tools/ref-font.mjs) で一致する', () => {
    expect(TOOL_FONT, '字の大きさ').toBe(SAMPLE_FONT_RATIO);
    expect(TOOL_BASE, '字の縦位置').toBe(SAMPLE_BASELINE_RATIO);
  });
});
