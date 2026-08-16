/**
 * 合成軌跡でエンジンを叩くテストヘルパ (§6.7)。
 */
import type { Pt, ResampledStroke } from '../types';
import { toCharacterDef, prepareStrokes } from '../loader';
import { fixture } from './fixtures';
import {
  StrokeMatcher,
  resolveParams,
  type MatcherResult,
} from '../strokeMatcher';
import type { MatchParams } from '../types';

export function loadStrokes(id: string): ResampledStroke[] {
  return prepareStrokes(toCharacterDef(fixture(id)));
}

export function newMatcher(
  id: string,
  params: MatchParams = resolveParams('normal', 1),
): StrokeMatcher {
  return new StrokeMatcher(loadStrokes(id), params);
}

/** down → move… → up を一気に流し、返ってきたイベントを全部集める */
export function feedStroke(m: StrokeMatcher, path: Pt[]): MatcherResult[] {
  const out: MatcherResult[] = [];
  const down = m.pointerDown(path[0]);
  out.push(down);
  if (down.type !== 'ok') return out; // 始点で弾かれたら描かない
  for (let i = 1; i < path.length; i++) {
    const r = m.pointerMove(path[i]);
    out.push(r);
    if (r.type === 'feedback') return out; // 途中で失敗したらペンを離す扱い
  }
  out.push(m.pointerUp());
  return out;
}

/** 全画を理想軌跡（変換つき）でなぞる */
export function traceChar(
  m: StrokeMatcher,
  strokes: ResampledStroke[],
  transform: (pts: Pt[], strokeIdx: number) => Pt[] = (pts) => pts,
): MatcherResult[] {
  const out: MatcherResult[] = [];
  for (let i = 0; i < strokes.length; i++) {
    out.push(...feedStroke(m, transform(strokes[i].pts, i)));
  }
  return out;
}

export function lastEvent(events: MatcherResult[]): MatcherResult {
  return events[events.length - 1];
}

export function feedbackKinds(events: MatcherResult[]): string[] {
  return events
    .filter((e) => e.type === 'feedback')
    .map((e) => (e.type === 'feedback' ? e.feedback : ''));
}

/** 決定的な乱数 (mulberry32) */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** ±amp にクリップした正規ノイズを全点に乗せる */
export function withNoise(pts: Pt[], amp: number, seed: number): Pt[] {
  const rand = rng(seed);
  const gauss = () => {
    // Box-Muller
    const u = Math.max(rand(), 1e-9);
    const v = rand();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  };
  const clip = (x: number) => Math.max(-amp, Math.min(amp, x));
  return pts.map((p) => ({
    x: p.x + clip(gauss() * (amp / 3)),
    y: p.y + clip(gauss() * (amp / 3)),
  }));
}

/** 速書きの再現: 点を大きく間引く（最初と最後は残す） */
export function decimate(pts: Pt[], keepEvery: number): Pt[] {
  const out = pts.filter((_, i) => i % keepEvery === 0);
  if (out[out.length - 1] !== pts[pts.length - 1]) out.push(pts[pts.length - 1]);
  return out;
}
