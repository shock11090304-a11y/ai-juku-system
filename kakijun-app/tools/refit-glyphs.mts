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
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const args = process.argv.slice(2).filter((a) => a !== '--');
const APPLY = args.includes('--apply');
const only = args.filter((a) => !a.startsWith('--'));
/** --base-only で小書き字を除く (従来の挙動) */
const ONLY_BASE = args.includes('--base-only');
/** 弾かれた候補の書き出し先 (調査用): DUMP_REJECTED=/tmp/rej */
const DUMP_DIR = process.env.DUMP_REJECTED ?? '';
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
    // ★小書き字も対象にする。フォントには専用グリフがあるので合わせ込める。
    //   (gen-derived.mts の 0.62 倍縮小はフォントの小書きとは別物だった)
    if (ONLY_BASE && c.group === 'youon') continue;
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
    ({ ch, S, font, fr, br }: { ch: string; S: number; font: string; fr: number; br: number }) => {
      const c = document.getElementById('c') as HTMLCanvasElement;
      const g = c.getContext('2d')!;
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      // ★ アプリの renderBackground と同一条件で描く (src/canvas/sampleGlyph.ts)。
      //   ここが 0.88em・中央だった頃は、子どもが見ている字とは別の字に
      //   合わせ込んでいた (忠実度 76% という数字自体が誤りだった)
      g.font = `${S * fr}px "${font}"`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(ch, S / 2, S * br);
      const d = g.getImageData(0, 0, S, S).data;
      const out: number[] = [];
      for (let i = 0; i < S * S; i++) out.push(d[i * 4] < 128 ? 1 : 0);
      return out;
    },
    { ch, S, font: FONT, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
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

/** 墨の外側の各画素から墨までの距離 (px)。墨の上は 0 (check-start-dots と同じ物差し) */
function distToInkMap(mask: Uint8Array): Float32Array {
  const dt = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) dt[i] = mask[i] ? 0 : 1e6;
  for (let y = 0; y < S; y++)
    for (let x = 0; x < S; x++) {
      const i = y * S + x;
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
      let v = dt[i];
      if (y < S - 1) v = Math.min(v, dt[i + S] + 1);
      if (x < S - 1) v = Math.min(v, dt[i + 1] + 1);
      if (y < S - 1 && x < S - 1) v = Math.min(v, dt[i + S + 1] + 1.414);
      if (y < S - 1 && x > 0) v = Math.min(v, dt[i + S - 1] + 1.414);
      dt[i] = v;
    }
  return dt;
}

/** 書き出しの点が墨からどれだけ浮いているか (マス1辺比) */
function startGapOf(pts: Pt[], dToInk: Float32Array): number {
  const x = Math.max(0, Math.min(S - 1, Math.round(pts[0].x * S)));
  const y = Math.max(0, Math.min(S - 1, Math.round(pts[0].y * S)));
  return dToInk[y * S + x] / S;
}

/**
 * ★ 画の採否の物差し。忠実度だけでは足りない —
 *   す の2画目は忠実度 91% なのに書き出しだけが 9% 浮いており、
 *   「墨によく乗った案」が「書き出しの浮いた現状」に勝てなかった。
 *   書き出しは書き順を伝える唯一の手がかりなので、忠実度より重く数える。
 */
function strokeScore(pts: Pt[], mask: Uint8Array, dToInk: Float32Array): number {
  return fidelity(pts, mask) - 3 * Math.min(startGapOf(pts, dToInk), 0.3);
}

/**
 * 各画が「使っている」墨の画素 (線の太さぶんの帯)。
 * 別の画を直すとき、ここを避けて探すことで隣の画へ吸い寄せられるのを防ぐ。
 * ★連結成分では分けられない: き のように画どうしが交差する字では
 *   全部の墨が1つに繋がっている。画素の帯で分けるしかない。
 */
function strokeStamps(strokesPts: Pt[][], r: number): Uint8Array[] {
  return strokesPts.map((pts) => {
    const stamp = new Uint8Array(S * S);
    const R = Math.round(r * S);
    for (const p of splineSample(pts, 24)) {
      const cx = Math.round(p.x * S);
      const cy = Math.round(p.y * S);
      for (let dy = -R; dy <= R; dy++) {
        for (let dx = -R; dx <= R; dx++) {
          if (dx * dx + dy * dy > R * R) continue;
          const x = cx + dx;
          const y = cy + dy;
          if (x >= 0 && y >= 0 && x < S && y < S) stamp[y * S + x] = 1;
        }
      }
    }
    return stamp;
  });
}

/**
 * ★ 直した字形が判定エンジンを通るかを、単体テストと同じ3通りで確かめる:
 *   ① 理想軌跡 ② 手ぶれ ③ お手本ずらし
 * ★軌跡の作り方は src/engine/traceProfiles.ts をテストと共有する。
 *   ここを自前で書いていたら乱数の引き方がずれ、「ツールでは通ったのに
 *   単体テストが落ちる」字 (す) を通してしまった (2026-08-17)。
 */
function engineVerdict(raw: RawCharacterDef): string | null {
  const strokes = prepareStrokes(toCharacterDef(raw));
  const variants: [string, Pt[][]][] = [
    ['理想', idealPaths(strokes)],
    ['手ぶれ', shakyPaths(strokes, raw.id)],
    ['お手本ずらし', offsetPaths(strokes)],
  ];
  for (const [name, paths] of variants) {
    const m = new StrokeMatcher(strokes, resolveParams('normal', 1));
    for (let si = 0; si < strokes.length; si++) {
      const path = paths[si];
      const down = m.pointerDown(path[0]);
      if (down.type !== 'ok') {
        return `${name}: ${si + 1}画目の書き出しで ${down.type === 'feedback' ? down.feedback : down.type}`;
      }
      for (let i = 1; i < path.length; i++) {
        const r = m.pointerMove(path[i]);
        if (r.type !== 'ok') {
          const pct = Math.round((i / path.length) * 100);
          return `${name}: ${si + 1}画目の ${pct}% で ${r.type === 'feedback' ? r.feedback : r.type}`;
        }
      }
      const up = m.pointerUp();
      if (!/stroke-ok|char-complete/.test(up.type)) {
        return `${name}: ${si + 1}画目が完走にならない (${up.type === 'feedback' ? up.feedback : up.type})`;
      }
    }
  }
  return null;
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

/** 最小ヒープ (Dijkstra 用) */
class MinHeap {
  private a: { d: number; i: number }[] = [];
  push(d: number, i: number): void {
    const a = this.a;
    a.push({ d, i });
    let k = a.length - 1;
    while (k > 0) {
      const p = (k - 1) >> 1;
      if (a[p].d <= a[k].d) break;
      [a[p], a[k]] = [a[k], a[p]];
      k = p;
    }
  }
  pop(): { d: number; i: number } | undefined {
    const a = this.a;
    if (a.length === 0) return undefined;
    const top = a[0];
    const last = a.pop()!;
    if (a.length) {
      a[0] = last;
      let k = 0;
      for (;;) {
        const l = 2 * k + 1;
        const r = l + 1;
        let m = k;
        if (l < a.length && a[l].d < a[m].d) m = l;
        if (r < a.length && a[r].d < a[m].d) m = r;
        if (m === k) break;
        [a[m], a[k]] = [a[k], a[m]];
        k = m;
      }
    }
    return top;
  }
  get size(): number {
    return this.a.length;
  }
}

/**
 * いちばん近い墨の画素 (幅優先)。
 * avoid (他の画が使っている帯) を渡すと、そこを避けた墨を優先して探す。
 * ★これが無いと、き の1画目 (上の横画) を直すとき、既に2画目が使っている
 *   下の横画へ吸い寄せられる。避けた墨が見つからないときだけ何でも良い墨に落とす。
 */
function nearestInk(
  mask: Uint8Array,
  x0: number,
  y0: number,
  avoid: Uint8Array | null = null,
): [number, number] | null {
  const x = Math.max(0, Math.min(S - 1, x0));
  const y = Math.max(0, Math.min(S - 1, y0));
  const good = (j: number) => mask[j] === 1 && (!avoid || avoid[j] === 0);
  if (good(y * S + x)) return [x, y];
  const seen = new Uint8Array(S * S);
  const q: number[] = [y * S + x];
  seen[y * S + x] = 1;
  let anyInk: [number, number] | null = mask[y * S + x] ? [x, y] : null;
  for (let h = 0; h < q.length; h++) {
    const i = q[h];
    const cx = i % S;
    const cy = (i / S) | 0;
    for (const [dx, dy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ] as const) {
      const nx = cx + dx;
      const ny = cy + dy;
      if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
      const j = ny * S + nx;
      if (seen[j]) continue;
      if (good(j)) return [nx, ny];
      if (mask[j] && !anyInk) anyInk = [nx, ny];
      seen[j] = 1;
      q.push(j);
    }
  }
  return anyInk;
}

const DIRS: [number, number, number][] = [
  [1, 0, 1],
  [-1, 0, 1],
  [0, 1, 1],
  [0, -1, 1],
  [1, 1, 1.414],
  [1, -1, 1.414],
  [-1, 1, 1.414],
  [-1, -1, 1.414],
];

/** 墨の中だけを通り、中心線を優先する最短経路 */
function shortestInInk(
  mask: Uint8Array,
  dt: Float32Array,
  maxdt: number,
  a: [number, number],
  b: [number, number],
): [number, number][] | null {
  const src = a[1] * S + a[0];
  const dst = b[1] * S + b[0];
  if (src === dst) return [a];
  const dist = new Float64Array(S * S).fill(Infinity);
  const prev = new Int32Array(S * S).fill(-1);
  const pq = new MinHeap();
  dist[src] = 0;
  pq.push(0, src);
  while (pq.size) {
    const top = pq.pop()!;
    if (top.d > dist[top.i]) continue;
    if (top.i === dst) break;
    const x = top.i % S;
    const y = (top.i / S) | 0;
    for (const [dx, dy, w] of DIRS) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
      const j = ny * S + nx;
      if (!mask[j]) continue;
      // 墨の縁より中心を通らせる
      const pen = 1 + 8 * ((maxdt - dt[j]) / maxdt) ** 2;
      const nd = top.d + w * pen;
      if (nd < dist[j]) {
        dist[j] = nd;
        prev[j] = top.i;
        pq.push(nd, j);
      }
    }
  }
  if (!isFinite(dist[dst])) return null;
  const path: [number, number][] = [];
  for (let i = dst; i !== -1; i = prev[i]) {
    path.push([i % S, (i / S) | 0]);
    if (i === src) break;
  }
  path.reverse();
  return path;
}

/**
 * Ramer-Douglas-Peucker。
 * ★閉じた経路 (0 や ○ のように始点=終点) では使えない: 端点が同じだと
 *   全点の「弦からの距離」が 0 になり、経路が2点に潰れる。
 *   実際 num_0 の合わせ込みが長さ0の画になり、練習不能なデータが出かけた。
 *   閉じている場合は中央で2つに割ってから間引く。
 */
function rdpAny(pts: [number, number][], eps: number): [number, number][] {
  const a = pts[0];
  const b = pts[pts.length - 1];
  const closed = Math.hypot(b[0] - a[0], b[1] - a[1]) < 2; // 2px 以内なら閉じている
  if (!closed || pts.length < 6) return rdp(pts, eps);
  const mid = Math.floor(pts.length / 2);
  const head = rdp(pts.slice(0, mid + 1), eps);
  const tail = rdp(pts.slice(mid), eps);
  return head.concat(tail.slice(1));
}

/** Ramer-Douglas-Peucker */
function rdp(pts: [number, number][], eps: number): [number, number][] {
  if (pts.length < 3) return pts;
  const a = pts[0];
  const b = pts[pts.length - 1];
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const L = Math.hypot(dx, dy) || 1;
  let best = -1;
  let idx = 0;
  for (let k = 1; k < pts.length - 1; k++) {
    const d = Math.abs((pts[k][0] - a[0]) * dy - (pts[k][1] - a[1]) * dx) / L;
    if (d > best) {
      best = d;
      idx = k;
    }
  }
  if (best <= eps) return [a, b];
  return rdp(pts.slice(0, idx + 1), eps).slice(0, -1).concat(rdp(pts.slice(idx), eps));
}

/**
 * ★ 墨の中だけを通る経路で画を引き直す (強い合わせ込み)。
 *
 * refit() は直交にしか寄せられず、fitEndpoints() は端しか動かせない。
 * 「画の途中の形がそもそもお手本と違う」字 (そ・す・き・な・ぬ・と) は
 * これでないと直らない。現行の制御点を経由点として順に繋ぐので、
 * 画の順序・向き・輪の通り方 (topology) は保たれる。
 *
 * ★形が大きく変わるので、呼び出し側で必ず enginePasses() を通すこと。
 *   墨に乗っても「正しくなぞったのに逆走と言われる」データになりうる。
 */
function traceThroughInk(
  pts: Pt[],
  mask: Uint8Array,
  dt: Float32Array,
  label = '',
  avoid: Uint8Array | null = null,
): Pt[] | null {
  const dbg = (m: string) => {
    if (process.env.TRACE_FIT) console.log(`      [経路 ${label}] ${m}`);
  };
  let maxdt = 0;
  for (let i = 0; i < dt.length; i++) if (dt[i] > maxdt) maxdt = dt[i];
  if (maxdt <= 0) return null;
  const wps: [number, number][] = [];
  for (const p of pts) {
    // ★他の画の帯を避けて投影する。え の2画目は始点近くの経由点が
    //   1画目の点の墨に投影され、本体と繋がらず無言で失敗していた
    const w = nearestInk(mask, Math.round(p.x * S), Math.round(p.y * S), avoid);
    if (!w) return null;
    // 同じ画素に潰れた経由点は捨てる (経路が進まなくなる)
    if (wps.length === 0 || wps[wps.length - 1][0] !== w[0] || wps[wps.length - 1][1] !== w[1]) {
      wps.push(w);
    }
  }
  if (wps.length < 2) return null;
  let full: [number, number][] = [];
  for (let k = 0; k < wps.length - 1; k++) {
    const seg = shortestInInk(mask, dt, maxdt, wps[k], wps[k + 1]);
    if (!seg) return null;
    full = full.length === 0 ? seg : full.concat(seg.slice(1));
  }
  if (full.length < 2) return null;
  let simp = rdpAny(full, 4);
  // 制御点は元と同じ数に揃える (増やすと判定の解像度が変わる)
  const n = Math.max(2, Math.min(18, pts.length));
  if (simp.length > n) {
    simp = Array.from({ length: n }, (_, k) => simp[Math.round((k / (n - 1)) * (simp.length - 1))]);
  }
  const out = simp.map(([x, y]) => ({ x: Number((x / S).toFixed(3)), y: Number((y / S).toFixed(3)) }));
  const arcOf = (v: Pt[]): number => {
    const d = splineSample(v, 24);
    let L = 0;
    for (let i = 1; i < d.length; i++) L += Math.hypot(d[i].x - d[i - 1].x, d[i].y - d[i - 1].y);
    return L;
  };
  const arc = arcOf(out);
  // ★ 潰れた画は返さない。長さ 0 の画は判定エンジンを止める
  if (arc < 0.05) {
    dbg('潰れた (弧長 < 0.05)');
    return null;
  }
  // ★★ 墨の上を行ったり来たりした経路を返さない。
  //   経路探索は「墨の中だけ」を通るので、画が繋がっている字では
  //   隣の画へ回り込んでも忠実度は 100% のまま高得点になる。数値では見抜けない。
  //   実際 ぬ・の で弧長が +29% に伸び、自己交差だらけの線になった (目視で発見)。
  //   まっすぐ引き直したなら弧長はほぼ変わらないはずなので、伸びを上限で弾く。
  if (arc > arcOf(pts) * 1.15) {
    dbg(`回り道 (弧長 ${arcOf(pts).toFixed(2)} → ${arc.toFixed(2)})`);
    return null;
  }
  dbg(`忠実度 ${(fidelity(out, mask) * 100).toFixed(0)}% 弧長 ${arcOf(pts).toFixed(2)}→${arc.toFixed(2)}`);
  return out;
}

/**
 * ★ 墨からまるごと離れている画を、形を変えずに墨へ運ぶ (平行移動 + 回転)。
 *
 * 点画 (ツ・シ・ッ の点、と・や・な の短い画) は、既存の3つでは動かせない:
 *   refit()          … 直交にしか寄せない (探索半径 0.045)。8〜20% 離れていたら届かない
 *   fitEndpoints()   … 端点を画の向きにしか動かせない。点画の墨は横にあるので当たらない
 *   traceThroughInk()… 2点の点画は経由点が同じ画素に潰れて経路にならない
 * さらに採否が忠実度だけなので、まるごと外れた画は before も after も 0% になり
 * 「据え置き」で黙って残っていた。これが「お手本どおりに書いた子が
 * 『ぎゃくむきだよ』と叱られる」画の正体 (実測13画)。
 *
 * ★倍率は変えない。形はそのまま運ぶだけなので、別の字形に化けることはない。
 * ★他の画の上へ移っていないかを必ず確かめる (墨は繋がっているので、
 *   何も見ないと隣の画へ吸い寄せられる)。
 */
function fitDetached(
  pts: Pt[],
  mask: Uint8Array,
  others: Pt[][],
  label = '',
  avoid: Uint8Array | null = null,
): Pt[] | null {
  const dbg = (m: string) => {
    if (process.env.TRACE_FIT) console.log(`      [運ぶ ${label}] ${m}`);
  };
  const MIN_FID = 0.6; // これ以上乗っている画は触らない
  if (fidelity(pts, mask) >= MIN_FID) {
    dbg(`対象外 (忠実度 ${(fidelity(pts, mask) * 100).toFixed(0)}% >= 60%)`);
    return null;
  }
  const dense = splineSample(pts, 24);
  const cx = dense.reduce((a, p) => a + p.x, 0) / dense.length;
  const cy = dense.reduce((a, p) => a + p.y, 0) / dense.length;
  // ★採点: 空いている墨 = 1点 / 他の画が使っている墨 = 0.5点 / 墨の外 = 0点。
  //   全部を避けると、他の画と交差する画 (と の点は2画目を横切る) が
  //   交差ぶんの点をもらえず、空いている切れ端に合わせて縮んでしまう。
  //   ただし空いている墨に 35% は乗ること (まるごと他の画の上、を防ぐ)
  const hitKind = (x: number, y: number): number => {
    const xi = Math.round(x * S);
    const yi = Math.round(y * S);
    if (xi < 0 || yi < 0 || xi >= S || yi >= S) return 0;
    const j = yi * S + xi;
    if (mask[j] !== 1) return 0;
    return !avoid || avoid[j] === 0 ? 2 : 1; // 2=空き墨 1=占有墨
  };
  const xform = (p: Pt, dx: number, dy: number, th: number, sc: number): Pt => {
    const co = Math.cos(th);
    const si = Math.sin(th);
    return {
      x: cx + ((p.x - cx) * co - (p.y - cy) * si) * sc + dx,
      y: cy + ((p.x - cx) * si + (p.y - cy) * co) * sc + dy,
    };
  };
  const score = (dx: number, dy: number, th: number, sc: number): number => {
    let free = 0;
    let taken = 0;
    for (const p of dense) {
      const k = hitKind(xform(p, dx, dy, th, sc).x, xform(p, dx, dy, th, sc).y);
      if (k === 2) free++;
      else if (k === 1) taken++;
    }
    if (free / dense.length < 0.35) return 0;
    return (free + 0.5 * taken) / dense.length;
  };
  const apply = (dx: number, dy: number, th: number, sc: number): Pt[] =>
    pts.map((p) => {
      const q = xform(p, dx, dy, th, sc);
      return { x: Number(q.x.toFixed(3)), y: Number(q.y.toFixed(3)) };
    });
  const MAX_ROT = (30 * Math.PI) / 180;
  // 倍率はわずかだけ許す。大きく変えると別の字形になるので ±15% まで。
  // ★ただし2点の画 (まっすぐな点・短い画) は、縮めても伸ばしても
  //   「まっすぐな画」のままで形は変わらない。長さの正解はフォント側にしか
  //   無いので、と の点 (データ 0.187・フォントはもっと短い) のような
  //   長さ違いは広い幅で合わせる
  const straight = pts.length === 2;
  const SCALES = straight
    ? [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    : [0.85, 0.925, 1.0, 1.075, 1.15];
  // ★置き場所の種 = 「空いている墨のかたまり」の重心。
  //   元位置の周りだけを格子で探すと、遠くにある本来の置き場所
  //   (と の点は 0.30 先) に届かない。かたまりごとに種を置いて局所で詰める
  const freeComp = new Int32Array(S * S).fill(-1);
  const seeds: { dx: number; dy: number }[] = [{ dx: 0, dy: 0 }];
  {
    let comp = 0;
    for (let i0 = 0; i0 < S * S; i0++) {
      if (mask[i0] !== 1 || (avoid && avoid[i0] === 1) || freeComp[i0] >= 0) continue;
      const q = [i0];
      freeComp[i0] = comp;
      let n = 0;
      let sx = 0;
      let sy = 0;
      for (let h = 0; h < q.length; h++) {
        const i = q[h];
        const x = i % S;
        const y = (i / S) | 0;
        n++;
        sx += x;
        sy += y;
        for (const [ddx, ddy] of [
          [1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1],
        ] as const) {
          const nx = x + ddx;
          const ny = y + ddy;
          if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
          const j = ny * S + nx;
          if (mask[j] !== 1 || (avoid && avoid[j] === 1) || freeComp[j] >= 0) continue;
          freeComp[j] = comp;
          q.push(j);
        }
      }
      if (n >= 40) seeds.push({ dx: sx / n / S - cx, dy: sy / n / S - cy });
      comp++;
    }
  }
  let best = { s: -1, dx: 0, dy: 0, th: 0, sc: 1 };
  // 各種の周り ±0.06 を格子で探す → 細かく詰める
  for (const seed of seeds) {
    if (Math.hypot(seed.dx, seed.dy) > 0.45) continue; // 反対側の隅までは飛ばない
    for (const scv of SCALES) {
      for (let th = -MAX_ROT; th <= MAX_ROT + 1e-9; th += (3 * Math.PI) / 180) {
        for (let dx = seed.dx - 0.06; dx <= seed.dx + 0.06 + 1e-9; dx += 0.01) {
          for (let dy = seed.dy - 0.06; dy <= seed.dy + 0.06 + 1e-9; dy += 0.01) {
            const v = score(dx, dy, th, scv);
            // 同点なら動かす量が小さく倍率が 1 に近い方 (別の画へ飛ぶのを避ける)
            const better =
              v > best.s ||
              (v === best.s &&
                Math.hypot(dx, dy) + Math.abs(scv - 1) <
                  Math.hypot(best.dx, best.dy) + Math.abs(best.sc - 1));
            if (better) best = { s: v, dx, dy, th, sc: scv };
          }
        }
      }
    }
  }
  for (let scv = best.sc - 0.04; scv <= best.sc + 0.04 + 1e-9; scv += 0.02) {
    for (let th = best.th - 0.05; th <= best.th + 0.05; th += 0.01) {
      for (let dx = best.dx - 0.012; dx <= best.dx + 0.012; dx += 0.002) {
        for (let dy = best.dy - 0.012; dy <= best.dy + 0.012; dy += 0.002) {
          const v = score(dx, dy, th, scv);
          if (v > best.s) best = { s: v, dx, dy, th, sc: scv };
        }
      }
    }
  }
  // 墨に乗り切らないなら触らない。★ここを緩めすぎると「近いだけの別の場所」へ
  //   運んでしまう。0.75 は「線の太さぶんはみ出しても運ぶ」程度
  if (best.s < 0.75) {
    dbg(`乗り切らない (最良でも ${(best.s * 100).toFixed(0)}% 移動=${Math.hypot(best.dx, best.dy).toFixed(3)} 回転=${((best.th * 180) / Math.PI).toFixed(0)}度 倍率=${best.sc.toFixed(2)})`);
    return null;
  }
  const moved = apply(best.dx, best.dy, best.th, best.sc);
  // ★ 他の画の書き出しと重ならないこと。
  //   交差は普通にある (と・や は短い画が長い画を横切る) ので経路の近さでは弾かない。
  //   実害が出るのは「書き出しが別の画の書き出しと重なる」場合だけ:
  //   判定は先に来た画を優先するので、子どもが正しく触っても
  //   「じゅんばんが ちがうよ」になる。
  // ★判定は「いま書く画の書き出し」を先に見るので、多少近くても実害は出ない。
  //   と のようにフォント自身が2画の書き出しを近くに置く字がある。
  //   別の画の墨に乗る事故は avoid (帯の除外) が防ぐようになったので、
  //   ここは「ほぼ同一点」だけを弾き、実際の可否はエンジン検証に任せる
  const START_MIN = 0.02;
  for (const o of others) {
    if (Math.hypot(moved[0].x - o[0].x, moved[0].y - o[0].y) < START_MIN) {
      dbg(`書き出しが他の画の書き出しと重なる`);
      return null;
    }
  }
  dbg(`採用候補 乗り ${(best.s * 100).toFixed(0)}% 移動=${Math.hypot(best.dx, best.dy).toFixed(3)} 回転=${((best.th * 180) / Math.PI).toFixed(0)}度 倍率=${best.sc.toFixed(2)}`);
  return moved;
}

/**
 * ★ 書き出しの近辺だけをなだらかに墨へ寄せる (第4の手)。
 *
 * 画の胴体は墨に乗っているのに書き出しだけ浮いている画 (す2・の1・ぬ2 など) は、
 *   経路探索 … 引き直すと回り道して弧長ガードに当たる
 *   端合わせ … 画の向きに沿ってしか動けない (横に浮いた書き出しに届かない)
 * のどちらでも直らなかった。書き出しから弧長の 35% までを、
 * ズレのぶんだけ重み付き (先頭 1 → 35%地点 0) で平行移動する。
 * 胴体は動かさないので形は保たれる。
 */
function fitHead(
  pts: Pt[],
  mask: Uint8Array,
  dToInk: Float32Array,
  avoid: Uint8Array | null,
  label = '',
): Pt[] | null {
  const dbg = (m: string) => {
    if (process.env.TRACE_FIT) console.log(`      [書き出し ${label}] ${m}`);
  };
  const g0 = startGapOf(pts, dToInk);
  if (g0 < 0.02) {
    dbg('書き出しは乗っている');
    return null;
  }
  if (g0 > 0.16) {
    dbg(`遠すぎる (${(g0 * 100).toFixed(0)}%) — 運ぶ側の仕事`);
    return null;
  }
  const target = nearestInk(mask, Math.round(pts[0].x * S), Math.round(pts[0].y * S), avoid);
  if (!target) return null;
  // 墨の縁ぴったりだと丸めで外に出るので、2px ぶん内側へ入れる
  const v = { x: target[0] / S - pts[0].x, y: target[1] / S - pts[0].y };
  const vl = Math.hypot(v.x, v.y) || 1;
  v.x += (v.x / vl) * (2 / S);
  v.y += (v.y / vl) * (2 / S);
  // 制御点の弧長位置 (折れ線近似) で重みを決める
  const cum: number[] = [0];
  for (let i = 1; i < pts.length; i++) {
    cum.push(cum[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y));
  }
  const total = cum[cum.length - 1] || 1;
  const HEAD = 0.35;
  const out = pts.map((p, j) => {
    const w = Math.max(0, 1 - cum[j] / total / HEAD);
    return { x: Number((p.x + v.x * w).toFixed(3)), y: Number((p.y + v.y * w).toFixed(3)) };
  });
  dbg(`ズレ ${(g0 * 100).toFixed(0)}% → 寄せる (移動 ${vl.toFixed(3)})`);
  return out;
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
function fitEndpoints(pts: Pt[], mask: Uint8Array, dToInk: Float32Array): Pt[] {
  // これ以上動かさない (別の画に飛ぶのを防ぐ)。
  // ★0.22 では ル の1画目 (墨に入るまで 0.228 必要) に 0.008 届かなかった
  const MAX_MOVE = 0.26;
  const STEP = 0.002;
  // ★端点ごとの歩行上限は「その端点の実際のズレ」に比例させる。
  //   一律 0.26 のままだと、ほぼ乗っている端点 (こ の左端はズレ 2%) が
  //   墨の帯の少し上をかすめたまま 0.30 歩き、反対側の端に端点を置いて
  //   「行って戻る」ジグザグの画を作った (こ・ミ・モ・ユ で実際に発生)。
  const capFor = (p: Pt): number => {
    const x = Math.max(0, Math.min(S - 1, Math.round(p.x * S)));
    const y = Math.max(0, Math.min(S - 1, Math.round(p.y * S)));
    const gap = dToInk[y * S + x] / S;
    return Math.max(0.06, Math.min(3.5 * gap, MAX_MOVE));
  };
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
      // 墨の外: 内側へ進んで最初に墨に入る所を探す (歩行上限はズレに比例)
      const cap = capFor(p);
      for (let s = STEP; s <= cap; s += STEP) {
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

const report: { id: string; char: string; before: number; after: number; how: string }[] = [];
const rejected: string[] = [];

/**
 * 画ごとの案を作って、★点数 (忠実度 − 書き出しのズレ×3) が上がったものだけ
 * 採用した「文字の案」を返す。忠実度だけを見ていた頃は、す の2画目のように
 * 「墨には 91% 乗っているが書き出しだけ 9% 浮いている」現状に勝てなかった。
 */
function makeCandidate(
  original: [number, number][][],
  mask: Uint8Array,
  dToInk: Float32Array,
  fit: (pts: Pt[], index: number) => Pt[] | null,
): { strokes: [number, number][][]; fid: number; score: number } {
  const strokes: [number, number][][] = [];
  let fidSum = 0;
  let scoreSum = 0;
  original.forEach((op, i) => {
    const pts: Pt[] = op.map(([x, y]) => ({ x, y }));
    const beforeScore = strokeScore(pts, mask, dToInk);
    let cand = fit(pts, i);
    // ★弧長の激変はどの手のものでも弾く (全候補共通の歯止め)。
    //   経路探索には個別の弧長ガードがあるが、直交寄せ (端合わせ) には無く、
    //   「行って戻る」ジグザグ (こ で 166%) や大幅な縮み (も で 50%) が通っていた。
    //   まっすぐな2点の画だけは長さの正解がフォント側にあるので広めに許す
    if (cand) {
      const arcOf = (v: Pt[]): number => {
        const dd = splineSample(v, 24);
        let L = 0;
        for (let k = 1; k < dd.length; k++) L += Math.hypot(dd[k].x - dd[k - 1].x, dd[k].y - dd[k - 1].y);
        return L;
      };
      const ratio = arcOf(cand) / Math.max(arcOf(pts), 1e-6);
      const [lo, hi] = pts.length === 2 ? [0.45, 1.55] : [0.6, 1.3];
      if (ratio < lo || ratio > hi) cand = null;
    }
    const afterScore = cand ? strokeScore(cand, mask, dToInk) : -Infinity;
    if (cand && afterScore > beforeScore + 1e-6) {
      strokes.push(cand.map((p) => [p.x, p.y] as [number, number]));
      fidSum += fidelity(cand, mask);
      scoreSum += afterScore;
    } else {
      strokes.push(op.map((p) => [...p] as [number, number]));
      fidSum += fidelity(pts, mask);
      scoreSum += beforeScore;
    }
  });
  return { strokes, fid: fidSum / original.length, score: scoreSum / original.length };
}

for (const { c } of targets) {
  const mask = await maskOf(c.char);
  const dt = distanceTransform(mask);
  const dToInk = distToInkMap(mask);
  const original = c.strokes.map((st) => st.points.map((p) => [...p] as [number, number]));
  const originalPts = original.map((op) => op.map(([x, y]) => ({ x, y })));
  // 各画が使っている墨の帯。i 番の画を直すときは他の画の帯を避ける
  const stamps = strokeStamps(originalPts, 0.03);
  const avoidFor = (i: number): Uint8Array => {
    const out = new Uint8Array(S * S);
    stamps.forEach((st, k) => {
      if (k === i) return;
      for (let j = 0; j < out.length; j++) if (st[j]) out[j] = 1;
    });
    return out;
  };
  const before =
    originalPts.reduce((a, pts) => a + fidelity(pts, mask), 0) / original.length;
  const scoreBefore =
    originalPts.reduce((a, pts) => a + strokeScore(pts, mask, dToInk), 0) / original.length;

  // 4つの手を点数で競わせる。強い順ではなく「点数が上がった順」。
  const candidates: { how: string; strokes: [number, number][][]; fid: number; score: number }[] = [
    {
      how: '点画を運ぶ',
      ...makeCandidate(original, mask, dToInk, (pts, i) =>
        fitDetached(
          pts,
          mask,
          originalPts.filter((_, k) => k !== i),
          `${c.id} ${i + 1}画`,
          avoidFor(i),
        ),
      ),
    },
    {
      how: '経路探索',
      ...makeCandidate(original, mask, dToInk, (pts, i) =>
        traceThroughInk(pts, mask, dt, `${c.id} ${i + 1}画`, avoidFor(i)),
      ),
    },
    {
      how: '書き出し寄せ',
      ...makeCandidate(original, mask, dToInk, (pts, i) =>
        fitHead(pts, mask, dToInk, avoidFor(i), `${c.id} ${i + 1}画`),
      ),
    },
    {
      how: '直交寄せ',
      ...makeCandidate(original, mask, dToInk, (pts) =>
        refit(fitEndpoints(refit(pts, mask, dt), mask, dToInk), mask, dt),
      ),
    },
  ].sort((a, b) => b.score - a.score);

  let picked: { how: string; strokes: [number, number][][]; fid: number; score: number } | null =
    null;
  const why: string[] = [];
  for (const cand of candidates) {
    if (cand.score <= scoreBefore + 1e-6) continue;
    // ★ 墨に乗っても、判定エンジンが通らない形なら採用しない。
    //   「正しくなぞったのに逆走・逸脱」と言われるデータは改悪
    c.strokes.forEach((st, i) => (st.points = cand.strokes[i]));
    const verdict = engineVerdict(c);
    if (verdict === null) {
      picked = cand;
      break;
    }
    why.push(`${cand.how} (${(cand.fid * 100).toFixed(0)}%) → ${verdict}`);
  }
  if (!picked) {
    // 弾かれた候補を書き出せるようにする (なぜ通らないのかを調べるため)
    if (DUMP_DIR && candidates.some((cand) => cand.score > scoreBefore + 1e-6)) {
      fs.mkdirSync(DUMP_DIR, { recursive: true });
      fs.writeFileSync(
        path.join(DUMP_DIR, `${c.id}.json`),
        JSON.stringify({ id: c.id, char: c.char, candidates }, null, 2),
      );
    }
    c.strokes.forEach((st, i) => (st.points = original[i]));
    if (candidates.some((cand) => cand.score > scoreBefore + 1e-6)) {
      rejected.push(`${c.char} ${c.id}: ${why.join(' / ')}`);
    }
  } else if (!APPLY) {
    c.strokes.forEach((st, i) => (st.points = original[i]));
  }
  report.push({
    id: c.id,
    char: c.char,
    before,
    after: picked ? picked.fid : before,
    how: picked ? picked.how : '据え置き',
  });
}
await browser.close();

report.sort((a, b) => a.after - b.after);
console.log('忠実度 (線の中心が手本の墨に乗っている割合) 低い順:');
for (const r of report)
  console.log(
    `  ${r.char} ${r.id.padEnd(16)} ${(r.before * 100).toFixed(0).padStart(3)}% → ${(r.after * 100).toFixed(0).padStart(3)}%  ${r.how}`,
  );
if (rejected.length) {
  console.log(`★ 判定エンジンを通らなくなるため戻した ${rejected.length}字:`);
  for (const r of rejected) console.log(`    ${r}`);
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
