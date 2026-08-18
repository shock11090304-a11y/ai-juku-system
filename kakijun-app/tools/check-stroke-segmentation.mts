/**
 * ★ 画の切り分けがお手本と合っているかの全数検査。
 *   npx vite-node tools/check-stroke-segmentation.mts -- [id...]
 *
 * 判定が「書き出しの位置と順番」だけになった今 (2026-08-18)、
 * 画の切り分けの誤りは、そのまま**子どもへの嘘の案内**になる。
 * 実際 塾長が実練習で見つけた事故:
 *   ち … 1画目 (横棒) の書き出しが縦画の頭に置かれ、縦を先に書いても通った
 *   や … 右上の点を書く画が無く、長い払いが2本に割れていた
 *   わ … 2画目の書き出しが1画目 (縦) の途中にあり、横棒の左半分は誰も書かない
 *   を … 同上
 * どれも「書き出しは墨の上にある」ので check-start-dots は通ってしまう。
 *
 * ここで落とすのは、人が字を書く上で**あり得ない形**の2つだけ:
 *   ① 書き出しの手前に、その画の向きのまま墨が続いている
 *      = 画の途中から書かせている (人は画の端か交差点からしか書き始めない)
 *   ② どの画も通っていない墨の部品がある
 *      = お手本に見えているのに、書かせる画が1本も無い
 * 「輪の内側を線がショートカットしている」類の粗は落とさない (子どもには見えない)。
 * 赤で可視化して目で見るのは tools/render/coverage-sheet.mts。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { prepareStrokes, toCharacterDef, resolveCharacter, toStroke, type MarkDef } from '../src/engine/loader';
import type { CharacterDef, RawCharacterDef, RawStroke } from '../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const args = process.argv.slice(2).filter((a) => a !== '--');
const opt = (n: string, d: string): string => {
  const i = args.indexOf(`--${n}`);
  return i >= 0 ? args[i + 1] : d;
};
/** ①で「墨が続いている」と見なす後退距離 (マス1辺比)。線の太さ 0.04 より広く取る */
const BACK_FROM = Number(opt('back-from', '0.035'));
const BACK_TO = Number(opt('back-to', '0.085'));
/** ②で見る部品の最小の大きさ (画素)。濁点1個で約 1400px */
const MIN_PART = Number(opt('min-part', '700'));
const only = args.filter((a, i) => !a.startsWith('--') && !args[i - 1]?.startsWith('--'));
const S = 512;

const files = ['hiragana.json', 'katakana.json', 'numbers.json'];
const all: RawCharacterDef[] = files.flatMap(
  (f) => JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
);
const marksRaw = JSON.parse(fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8')) as MarkDef[];
const registry = new Map<string, CharacterDef>(all.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]));
const targets = [...registry.values()]
  .map((c) => resolveCharacter(c, registry, marks))
  .filter((c) => only.length === 0 || only.includes(c.id));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent(
  `<!doctype html><meta charset="utf-8"><body style="margin:0"><canvas id="c" width="${S}" height="${S}"></canvas>`,
);
await useRefFont(
  page,
  targets.map((t) => t.char),
);

async function maskOf(ch: string): Promise<Uint8Array> {
  const bits = await page.evaluate(
    ({ ch, S, font, fr, br }) => {
      const g = (document.getElementById('c') as HTMLCanvasElement).getContext('2d')!;
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      // ★ アプリの renderBackground と同一条件 (0.86em・中央・y=0.52)
      g.font = `${S * fr}px "${font}"`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(ch, S / 2, S * br);
      const d = g.getImageData(0, 0, S, S).data;
      const out: number[] = [];
      for (let i = 0; i < S * S; i++) out.push(d[i * 4] < 128 ? 1 : 0);
      return out;
    },
    { ch, S, font: REF_FONT_FAMILY, fr: SAMPLE_FONT_RATIO, br: SAMPLE_BASELINE_RATIO },
  );
  return Uint8Array.from(bits);
}

const ink = (m: Uint8Array, x: number, y: number): boolean => {
  const px = Math.round(x * S);
  const py = Math.round(y * S);
  return px >= 0 && py >= 0 && px < S && py < S && m[py * S + px] === 1;
};

const midStart: string[] = [];
const orphan: string[] = [];
for (const c of targets) {
  const mask = await maskOf(c.char);
  const prepared = prepareStrokes(c);

  // ① 書き出しの手前に、その画の向きのまま「誰も書かない墨」が続いていないか。
  //   ★他の画が書く墨なら違反ではない: ま の縦画が横棒から始まる、
  //     ア の2画目が1画目の横棒から始まる、のように「交差点から始める画」は正しい。
  //     見たいのは「その画自身の墨が、書き出しより手前にまだ残っている」場合だけ。
  const claimed = (i: number): Uint8Array => {
    const out = new Uint8Array(S * S);
    const R = Math.round(0.045 * S);
    prepared.forEach((s, k) => {
      if (k === i) return;
      for (const p of s.pts) {
        const cx = Math.round(p.x * S);
        const cy = Math.round(p.y * S);
        for (let dy = -R; dy <= R; dy++)
          for (let dx = -R; dx <= R; dx++) {
            if (dx * dx + dy * dy > R * R) continue;
            const x = cx + dx;
            const y = cy + dy;
            if (x >= 0 && y >= 0 && x < S && y < S) out[y * S + x] = 1;
          }
      }
    });
    return out;
  };
  prepared.forEach((s, i) => {
    const p0 = s.pts[0];
    const p1 = s.pts[8]; // 弧長の 1/8 先 (細かい凹凸に引きずられない向き)
    const dx = p1.x - p0.x;
    const dy = p1.y - p0.y;
    const len = Math.hypot(dx, dy);
    if (len < 1e-6) return;
    const ux = dx / len;
    const uy = dy / len;
    const other = claimed(i);
    let all = true;
    for (let t = BACK_FROM; t <= BACK_TO + 1e-9; t += 0.01) {
      const x = p0.x - ux * t;
      const y = p0.y - uy * t;
      const px = Math.max(0, Math.min(S - 1, Math.round(x * S)));
      const py = Math.max(0, Math.min(S - 1, Math.round(y * S)));
      if (!ink(mask, x, y) || other[py * S + px]) {
        all = false;
        break;
      }
    }
    if (all) {
      midStart.push(
        `${c.char} ${c.id}: ${i + 1}画目が墨の途中から始まっている (書き出しの手前 ${(BACK_TO * 100).toFixed(0)}% まで、誰も書かない墨が続く)`,
      );
    }
  });

  // ② どの画も通っていない墨の部品が無いか
  const comp = new Int32Array(S * S).fill(-1);
  const sizes: number[] = [];
  let nc = 0;
  for (let i = 0; i < S * S; i++) {
    if (!mask[i] || comp[i] >= 0) continue;
    const q = [i];
    comp[i] = nc;
    let sz = 0;
    while (q.length) {
      const j = q.pop()!;
      sz++;
      const x = j % S;
      const y = (j / S) | 0;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= S || ny >= S) continue;
        const k = ny * S + nx;
        if (mask[k] && comp[k] < 0) {
          comp[k] = nc;
          q.push(k);
        }
      }
    }
    sizes.push(sz);
    nc++;
  }
  const touched = new Set<number>();
  for (const s of prepared) {
    for (const p of s.pts) {
      const px = Math.round(p.x * S);
      const py = Math.round(p.y * S);
      // 線が墨から少しはみ出していても拾えるよう、近傍も見る
      for (let dy = -6; dy <= 6; dy += 3)
        for (let dx = -6; dx <= 6; dx += 3) {
          const x = px + dx;
          const y = py + dy;
          if (x < 0 || y < 0 || x >= S || y >= S) continue;
          const k = comp[y * S + x];
          if (k >= 0) touched.add(k);
        }
    }
  }
  for (let k = 0; k < nc; k++) {
    if (sizes[k] < MIN_PART || touched.has(k)) continue;
    let x0 = 1;
    let y0 = 1;
    for (let i = 0; i < S * S; i++)
      if (comp[i] === k) {
        x0 = (i % S) / S;
        y0 = ((i / S) | 0) / S;
        break;
      }
    orphan.push(
      `${c.char} ${c.id}: どの画も通らない部品がある (${sizes[k]}px・${(x0 * 100).toFixed(0)}%,${(y0 * 100).toFixed(0)}% 付近)`,
    );
  }
}
await browser.close();

console.log(`画の切り分けがお手本と合っているか: ${targets.length}字`);
for (const m of midStart) console.log(`NG ${m}`);
for (const o of orphan) console.log(`NG ${o}`);
if (midStart.length || orphan.length) {
  const ids = new Set(
    [...midStart, ...orphan].map((s) => s.split(' ')[1].replace(':', '')),
  );
  console.log(
    `★ 途中から書かせている ${midStart.length}画 / 書く画が無い部品 ${orphan.length}か所 (計 ${ids.size}字)`,
  );
  process.exit(1); // ★ 検査は必ず落とす
}
console.log('OK: 全字が「画の端から書き始め」「全部品に書く画がある」');
