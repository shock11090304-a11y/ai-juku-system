import { describe, expect, it } from 'vitest';
import {
  dist,
  interpolateSegment,
  polylineLength,
  resampleStroke,
  splineSample,
} from '../geometry';
import { toCharacterDef, prepareStrokes, resolveCharacter } from '../loader';
import type { CharacterDef, Stroke } from '../types';
import { fixture } from './fixtures';

describe('リサンプリング (§6.1)', () => {
  it('64点・等間隔・端点保持', () => {
    const control = fixture('hira_shi').strokes[0].points.map(([x, y]) => ({
      x,
      y,
    }));
    const { pts, length } = resampleStroke(control);
    expect(pts).toHaveLength(64);
    // 端点は制御点の始点・終点に一致
    expect(dist(pts[0], control[0])).toBeLessThan(1e-9);
    expect(dist(pts[63], control[control.length - 1])).toBeLessThan(1e-9);
    // 等間隔（±5% 以内）
    const step = length / 63;
    for (let i = 1; i < 64; i++) {
      expect(dist(pts[i - 1], pts[i])).toBeGreaterThan(step * 0.95);
      expect(dist(pts[i - 1], pts[i])).toBeLessThan(step * 1.05);
    }
  });

  it('制御点2点は直線になる', () => {
    const { pts } = resampleStroke([
      { x: 0.1, y: 0.1 },
      { x: 0.9, y: 0.9 },
    ]);
    for (const p of pts) {
      expect(Math.abs(p.x - p.y)).toBeLessThan(1e-6);
    }
  });

  it('スプラインは制御点を通る', () => {
    const control = [
      { x: 0.2, y: 0.2 },
      { x: 0.5, y: 0.8 },
      { x: 0.8, y: 0.3 },
    ];
    const dense = splineSample(control, 32);
    for (const c of control) {
      const min = Math.min(...dense.map((p) => dist(p, c)));
      expect(min).toBeLessThan(0.02);
    }
  });
});

describe('入力補間 (§6.4)', () => {
  it('h 以下の間隔に分割される', () => {
    const a = { x: 0, y: 0 };
    const b = { x: 0.1, y: 0 };
    const out = interpolateSegment(a, b, 0.03);
    expect(out[out.length - 1]).toEqual(b);
    let prev = a;
    for (const p of out) {
      expect(dist(prev, p)).toBeLessThanOrEqual(0.03 + 1e-9);
      prev = p;
    }
  });

  it('近い点はそのまま返す', () => {
    const out = interpolateSegment({ x: 0, y: 0 }, { x: 0.01, y: 0 }, 0.03);
    expect(out).toHaveLength(1);
  });
});

describe('濁音・半濁音の合成 (§4.3)', () => {
  const dakutenStrokes: Stroke[] = [
    {
      index: 1,
      hint: 'naname',
      points: [
        { x: 0.8, y: 0.08 },
        { x: 0.86, y: 0.18 },
      ],
    },
    {
      index: 2,
      hint: 'naname',
      points: [
        { x: 0.9, y: 0.06 },
        { x: 0.96, y: 0.16 },
      ],
    },
  ];

  it('base の画 → marks の画の順で通し番号が振り直される', () => {
    const base = toCharacterDef(fixture('hira_shi'));
    const composed: CharacterDef = {
      id: 'hira_ji',
      char: 'じ',
      reading: 'じ',
      type: 'hiragana',
      group: 'dakuon',
      strokes: [],
      composedFrom: { base: 'hira_shi', marks: ['mark_dakuten'] },
    };
    const registry = new Map([[base.id, base]]);
    const marks = new Map([['mark_dakuten', dakutenStrokes]]);
    const resolved = resolveCharacter(composed, registry, marks);
    expect(resolved.strokes).toHaveLength(3); // base 1 + 濁点 2
    expect(resolved.strokes.map((s) => s.index)).toEqual([1, 2, 3]);
    // 濁点は右上 (x: 0.78〜0.98, y: 0.05〜0.30)
    for (const s of resolved.strokes.slice(1)) {
      for (const p of s.points) {
        expect(p.x).toBeGreaterThanOrEqual(0.78);
        expect(p.x).toBeLessThanOrEqual(0.98);
        expect(p.y).toBeGreaterThanOrEqual(0.05);
        expect(p.y).toBeLessThanOrEqual(0.3);
      }
    }
    // 元データは破壊されない
    expect(base.strokes[0].index).toBe(1);
  });

  it('prepareStrokes で弧長が入る', () => {
    const def = toCharacterDef(fixture('hira_a'));
    const prepared = prepareStrokes(def);
    expect(prepared).toHaveLength(3);
    for (const s of prepared) {
      expect(s.length).toBeGreaterThan(0.1);
      expect(polylineLength(s.pts)).toBeCloseTo(s.length, 10);
    }
  });
});
