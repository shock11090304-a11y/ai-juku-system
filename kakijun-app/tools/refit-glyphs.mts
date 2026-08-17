/**
 * 全文字の字形を手本フォントの墨に合わせ込む一括処理。
 *   npx vite-node tools/refit-glyphs.mts -- [--apply] [id...]
 *
 * 各字について:
 *   1. 手本グリフを 512px マスク化 (Chromium 1回起動で全字ぶん)
 *   2. 距離変換で墨の中心線を作る
 *   3. 現行ストロークを進行方向と直交する向きにだけ寄せる (隣の画へ飛ばない)
 *   4. 平滑化 → 元と同じ制御点数へ間引き
 *   5. 「線の中心が墨の中に乗っている割合」= 忠実度を before/after で出す
 *
 * --apply を付けたときだけ JSON を書き換える。付けなければ測定のみ。
 * 合成字 (濁音・半濁音) と小書き、運筆は対象外 (基字から派生させるため)。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { splineSample } from '../src/engine/geometry';
import { prepareStrokes, toCharacterDef } from '../src/engine/loader';
import { StrokeMatcher, resolveParams } from '../src/engine/strokeMatcher';
import { idealPaths, shakyPaths, offsetPaths } from '../src/engine/traceProfiles';
import type { RawCharacterDef, Pt } from '../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const args = process.argv.slice(2).filter((a) => a !== '--');
const APPLY = args.includes('--apply');
const only = args.filter((a) => !a.startsWith('--'));
// ★ system にインストールされたフォントを名前で引かない (tools/ref-font.mjs 参照)。
//   出荷している woff2 = 画面に出ている字そのものを測る。
const FONT = REF_FONT_FAMILY;
const S = 512;
const PASSES = 3;

const FILES = ['hiragana.json', 'katakana.json', 'numbers.json'];
type Bundle = { file: string; list: RawCharacterDef[] };
const bundles: Bundle[] = FILES.map((f) => ({
  file: f,
  list: JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
}));

const targets: { b: Bundle; c: RawCharacterDef }[] = [];
for (const b of bundles)
  for (const c of b.list) {
    if (c.composedFrom) continue; // 濁音等は基字から合成
    if (c.group === 'youon') continue; // 小書きは基字から生成
    if (only.length && !only.includes(c.id)) continue;
    targets.push({ b, c });
  }

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
// 手本フォントが本当に効いているかを、測る字そのもので確かめる
await useRefFont(
  page,
  targets.map((t) => t.c.char),
);

async function maskOf(ch: string): Promise<Uint8Array> {
  const bits = await page.evaluate(
    ({ ch, S, font }) => {
      const c = document.getElementById('c') as HTMLCanvasElement;
      const g = c.getContext('2d')!;
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      // ★ アプリの renderBackground と同一条件で描く。
      //   ここが 0.88em・中央だった頃は、子どもが見ている字 (0.86em・y=0.52) とは
      //   別の字に合わせ込んでいた (縦に約2%ずれる)
      g.font = `${S * 0.86}px "${font}"`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(ch, S / 2, S * 0.52);
      const d = g.getImageData(0, 0, S, S).data;
      const out: number[] = [];
      for (let i = 0; i < S * S; i++) out.push(d[i * 4] < 128 ? 1 : 0);
      return out;
    },
    { ch, S, font: FONT },
  );
  return Uint8Array.from(bits);
}

function distanceTransform(mask: Uint8Array): Float32Array {
  const dt = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) dt[i] = mask[i] ? 1e6 : 0;
  for (let y = 0; y < S; y++)
    for (let x = 0; x < S; x++) {
      const i = y * S + x;
      if (!mask[i]) continue;
      let v = dt[i];
      if (y > 0) v = Math.min(v, dt[i - S] + 1);
      if (x > 0) v = Math.min(v, dt[i - 1] + 1);
      if (y > 0 && x > 0) v = Math.min(v, dt[i - S - 1] + 1.414);
      if (y > 0 && x < S - 1) v = Math.min(v, dt[i - S + 1] + 1.414);
      dt[i] = v;
    }
  for (let y = S - 1; y >= 0; y--)
    for (let x = S - 1; x >= 0; x--) {
      const i = y * S + x;
      if (!mask[i]) continue;
      let v = dt[i];
      if (y < S - 1) v = Math.min(v, dt[i + S] + 1);
      if (x < S - 1) v = Math.min(v, dt[i + 1] + 1);
      if (y < S - 1 && x < S - 1) v = Math.min(v, dt[i + S + 1] + 1.414);
      if (y < S - 1 && x > 0) v = Math.min(v, dt[i + S - 1] + 1.414);
      dt[i] = v;
    }
  return dt;
}

/**
 * ★ 直した字形が判定エンジンを通るかを、単体テストと同じ3通りで確かめる:
 *   ① 理想軌跡 ② 手ぶれ ③ お手本ずらし
 * ★軌跡の作り方は src/engine/traceProfiles.ts をテストと共有する。
 *   ここを自前で書いていたら乱数の引き方がずれ、「ツールでは通ったのに
 *   単体テストが落ちる」字 (す) を通してしまった (2026-08-17)。
 */
function enginePasses(raw: RawCharacterDef): boolean {
  const strokes = prepareStrokes(toCharacterDef(raw));
  const variants = [
    idealPaths(strokes),
    shakyPaths(strokes, raw.id),
    offsetPaths(strokes),
  ];
  for (const paths of variants) {
    const m = new StrokeMatcher(strokes, resolveParams('normal', 1));
    for (let si = 0; si < strokes.length; si++) {
      const path = paths[si];
      if (m.pointerDown(path[0]).type !== 'ok') return false;
      for (let i = 1; i < path.length; i++) {
        if (m.pointerMove(path[i]).type !== 'ok') return false;
      }
      if (!/stroke-ok|char-complete/.test(m.pointerUp().type)) return false;
    }
  }
  return true;
}

/** 墨に乗っている割合 (忠実度) */
function fidelity(pts: Pt[], mask: Uint8Array): number {
  const dense = splineSample(pts, 24);
  let inside = 0;
  for (const p of dense) {
    const x = Math.round(p.x * S);
    const y = Math.round(p.y * S);
    if (x >= 0 && y >= 0 && x < S && y < S && mask[y * S + x]) inside++;
  }
  return inside / dense.length;
}

/**
 * ★ 画の「端」をお手本の墨の端に合わせる。
 *
 * refit() は進行方向と直交にしか寄せないので、書き出しが墨の外にある画
 * (か の3画目など) はどれだけ回しても動かない。書き出しの点はいま書き順を
 * 伝える唯一の手がかりなので、そこが白いところに浮くと「どの画のことか
 * 分からない」になる (2026-08-17 塾長指摘)。
 *
 * やり方: 端点から画の向きに沿って前後へ探り、いちばん近い「墨の区間」を見つけ、
 * その端を新しい端点にする。向きに沿って探るので隣の画へ飛び移りにくい。
 */
function fitEndpoints(pts: Pt[], mask: Uint8Array): Pt[] {
  const MAX_MOVE = 0.22; // これ以上動かさない (別の画に飛ぶのを防ぐ)
  const STEP = 0.002;
  const inside = (x: number, y: number): boolean => {
    const xi = Math.round(x * S);
    const yi = Math.round(y * S);
    return xi >= 0 && yi >= 0 && xi < S && yi < S && mask[yi * S + xi] === 1;
  };
  const dense = splineSample(pts, 24);
  const out = pts.map((p) => ({ ...p }));

  /** 端点 p から向き d に沿って探り、墨の区間の「外側の端」を返す */
  const findInkEdge = (p: Pt, d: Pt): Pt | null => {
    // s>0 = 画の内側へ進む向き。s<0 = 画を伸ばす向き
    let entry: number | null = null;
    if (inside(p.x, p.y)) {
      // すでに墨の上: 墨が続く限り外へ伸ばして端を探す
      let s = 0;
      while (s > -MAX_MOVE && inside(p.x + d.x * (s - STEP), p.y + d.y * (s - STEP))) {
        s -= STEP;
      }
      entry = s;
    } else {
      // 墨の外: 内側へ進んで最初に墨に入る所を探す
      for (let s = STEP; s <= MAX_MOVE; s += STEP) {
        if (inside(p.x + d.x * s, p.y + d.y * s)) {
          entry = s;
          break;
        }
      }
    }
    if (entry === null) return null;
    return { x: p.x + d.x * entry, y: p.y + d.y * entry };
  };

  const dir = (a: Pt, b: Pt): Pt => {
    const l = Math.hypot(b.x - a.x, b.y - a.y) || 1;
    return { x: (b.x - a.x) / l, y: (b.y - a.y) / l };
  };
  const head = findInkEdge(dense[0], dir(dense[0], dense[Math.min(6, dense.length - 1)]));
  const tail = findInkEdge(
    dense[dense.length - 1],
    dir(dense[dense.length - 1], dense[Math.max(0, dense.length - 7)]),
  );
  const cand = out.map((p) => ({ ...p }));
  if (head) cand[0] = { x: Number(head.x.toFixed(3)), y: Number(head.y.toFixed(3)) };
  if (tail) cand[cand.length - 1] = { x: Number(tail.x.toFixed(3)), y: Number(tail.y.toFixed(3)) };
  // ★ 潰れた画を作らない。短い画 (ウ の1画目の点など) では墨の区間が短く出て
  //   両端が寄り、長さ 0.026 まで縮んだ。長さ 0.03 以下の画は判定エンジンを止める
  //   ので、その倍を下限にする。★「元より短くするな」ではない —
  //   書き出しが墨の外にある画 (か の3画目) は正しく詰める必要がある
  const MIN_ARC = 0.06;
  const arc = (v: Pt[]) => {
    const d = splineSample(v, 24);
    let L = 0;
    for (let i = 1; i < d.length; i++) L += Math.hypot(d[i].x - d[i - 1].x, d[i].y - d[i - 1].y);
    return L;
  };
  if (arc(cand) < MIN_ARC) return out;
  return cand;
}

function refit(pts: Pt[], _mask: Uint8Array, dt: Float32Array): Pt[] {
  const n = pts.length;
  let cur = pts;
  for (let pass = 0; pass < PASSES; pass++) {
    const dense = splineSample(cur, 24);
    const R = Math.round(S * (pass === 0 ? 0.045 : 0.02));
    const snapped: Pt[] = dense.map((p, i) => {
      const a = dense[Math.max(0, i - 1)];
      const b = dense[Math.min(dense.length - 1, i + 1)];
      const tx = b.x - a.x;
      const ty = b.y - a.y;
      const len = Math.hypot(tx, ty) || 1;
      const nx = -ty / len;
      const ny = tx / len;
      const px = p.x * S;
      const py = p.y * S;
      const idx = (x: number, y: number) => {
        const xi = Math.round(x);
        const yi = Math.round(y);
        return xi < 0 || yi < 0 || xi >= S || yi >= S ? 0 : dt[yi * S + xi];
      };
      let best = { d: idx(px, py), x: px, y: py };
      for (let t = -R; t <= R; t += 0.5) {
        const x = px + nx * t;
        const y = py + ny * t;
        const d = idx(x, y);
        if (d > best.d) best = { d, x, y };
      }
      return { x: best.x / S, y: best.y / S };
    });
    // 平滑化 (スナップのギザつきを均す。端点は動かさない)
    const sm: Pt[] = snapped.map((p, i) => {
      if (i === 0 || i === snapped.length - 1) return p;
      const a = snapped[i - 1];
      const b = snapped[i + 1];
      return { x: (a.x + 2 * p.x + b.x) / 4, y: (a.y + 2 * p.y + b.y) / 4 };
    });
    // 元と同じ制御点数へ
    cur = Array.from({ length: n }, (_, k) => sm[Math.round((k / (n - 1)) * (sm.length - 1))]);
  }
  return cur.map((p) => ({ x: Number(p.x.toFixed(3)), y: Number(p.y.toFixed(3)) }));
}

const report: { id: string; char: string; before: number; after: number }[] = [];
const rejected: string[] = [];
for (const { c } of targets) {
  const mask = await maskOf(c.char);
  const dt = distanceTransform(mask);
  let beforeSum = 0;
  let afterSum = 0;
  const original = c.strokes.map((st) => st.points.map((p) => [...p] as [number, number]));
  const fittedAll: ([number, number][] | null)[] = [];
  for (const st of c.strokes) {
    const pts: Pt[] = st.points.map(([x, y]) => ({ x, y }));
    const before = fidelity(pts, mask);
    // ★ 直交に寄せる → 端を墨の端に合わせる → もう一度直交に寄せる。
    //   端を動かすと途中も少しずれるので、最後にもう一度ならす
    const fitted = refit(fitEndpoints(refit(pts, mask, dt), mask), mask, dt);
    const after = fidelity(fitted, mask);
    beforeSum += before;
    // 悪化する画は触らない (元の形のほうが墨に乗っている場合)
    if (after > before) {
      afterSum += after;
      fittedAll.push(fitted.map((p) => [p.x, p.y] as [number, number]));
    } else {
      afterSum += before;
      fittedAll.push(null);
    }
  }
  // ★ 墨に寄せた結果、判定エンジンが通らない形になっていないかを必ず確かめる。
  //   墨への一致度が上がっても、折り返しが鋭くなって「正しくなぞったのに
  //   逆走・逸脱」と言われるデータになったら、それは改悪。忠実度の数字だけを
  //   見て入れ替えると、そ・ぞ・え・カ で実際にそうなった (2026-08-17)。
  for (let i = 0; i < c.strokes.length; i++) {
    if (fittedAll[i]) c.strokes[i].points = fittedAll[i]!;
  }
  const ok = enginePasses(c);
  if (!ok) {
    for (let i = 0; i < c.strokes.length; i++) c.strokes[i].points = original[i];
    rejected.push(`${c.char} ${c.id}`);
    afterSum = beforeSum;
  } else if (!APPLY) {
    for (let i = 0; i < c.strokes.length; i++) c.strokes[i].points = original[i];
  }
  report.push({
    id: c.id,
    char: c.char,
    before: beforeSum / c.strokes.length,
    after: afterSum / c.strokes.length,
  });
}
await browser.close();

report.sort((a, b) => a.after - b.after);
console.log('忠実度 (線の中心が手本の墨に乗っている割合) 低い順:');
for (const r of report)
  console.log(
    `  ${r.char} ${r.id.padEnd(16)} ${(r.before * 100).toFixed(0).padStart(3)}% → ${(r.after * 100).toFixed(0).padStart(3)}%`,
  );
if (rejected.length) {
  console.log(`★ 判定エンジンを通らなくなるため戻した ${rejected.length}字: ${rejected.join(' / ')}`);
}
const avgB = report.reduce((s, r) => s + r.before, 0) / report.length;
const avgA = report.reduce((s, r) => s + r.after, 0) / report.length;
console.log(`平均: ${(avgB * 100).toFixed(1)}% → ${(avgA * 100).toFixed(1)}%  (${report.length}字)`);

if (APPLY) {
  for (const b of bundles) {
    fs.writeFileSync(path.join(dataDir, b.file), JSON.stringify(b.list, null, 2) + '\n');
  }
  console.log('JSON を更新した');
} else {
  console.log('(測定のみ。書き換えるには --apply)');
}
