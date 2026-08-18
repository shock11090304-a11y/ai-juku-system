/**
 * ★ 書き出しの点が「お手本の字の上」に乗っているかの全数検査。
 *   npx vite-node tools/check-start-dots.mts -- [--max 0.05] [id...]
 *
 * 経路表示をやめた (PR #39) ので、いま書き順を伝えているのは
 * 「番号 + 書き出しの点」だけ。その点がお手本の墨から浮いていると、
 * 子どもは何も無いところを指して「ここから書け」と言われることになる。
 * 見た目の破綻なのに、判定は許容幅が広いので自動テストは緑のまま通る。
 *
 * お手本 = 出荷している woff2 (画面に出ている字そのもの)。
 * 判定 = 線データ。両者は別物なので、ここでズレを数える。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { toCharacterDef, resolveCharacter, toStroke, type MarkDef } from '../src/engine/loader';
import type { CharacterDef, RawCharacterDef, RawStroke } from '../src/engine/types';
// @ts-expect-error 型定義のない開発用ヘルパ
import { useRefFont, REF_FONT_FAMILY, SAMPLE_FONT_RATIO, SAMPLE_BASELINE_RATIO } from './ref-font.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');
const args = process.argv.slice(2).filter((a) => a !== '--');
const maxArg = args.indexOf('--max');
/** 許容ズレ (マス1辺に対する比)。お手本の線の太さの半分 ≒ 0.05 */
const MAX = maxArg >= 0 ? Number(args[maxArg + 1]) : 0.05;
const only = args.filter((a, i) => !a.startsWith('--') && args[i - 1] !== '--max');
const S = 512;

const files = ['hiragana.json', 'katakana.json', 'numbers.json'];
const all: RawCharacterDef[] = files.flatMap(
  (f) => JSON.parse(fs.readFileSync(path.join(dataDir, f), 'utf8')) as RawCharacterDef[],
);
const marksRaw = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'marks.json'), 'utf8'),
) as MarkDef[];
const registry = new Map<string, CharacterDef>(all.map((c) => [c.id, toCharacterDef(c)]));
const marks = new Map(marksRaw.map((m) => [m.id, m.strokes.map((s: RawStroke) => toStroke(s))]));
// 運筆はお手本を線データから描くので (フォントに字形が無い) 検査対象外
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

/** 墨までの距離マップ (px)。墨の中は 0 */
async function inkDistance(ch: string): Promise<Float32Array> {
  const mask = await page.evaluate(
    ({ ch, S, font, fr, br }) => {
      const g = (document.getElementById('c') as HTMLCanvasElement).getContext('2d')!;
      g.fillStyle = '#fff';
      g.fillRect(0, 0, S, S);
      g.fillStyle = '#000';
      // ★ アプリの renderBackground と同じ配置 (0.86em・中央・y=0.52)
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

type Bad = { id: string; char: string; stroke: number; gap: number };
const bad: Bad[] = [];
let worstOk = 0;
/**
 * ★書き出しどうしの重なり検査 (2026-08-18 追加)。
 * 判定が「書き出しの位置と順番」だけになったので、別の画の書き出しが同じ点に
 * 置かれていると、後の画の番号バッジが前の画の頭に重なって表示され、
 * 子どもは「同じ場所から2回書け」と言われることになる。
 * 実際 ち で1画目(横棒)の書き出しが合わせ込み事故で縦画の頭 (=2画目の書き出し)
 * に置かれ、縦を先に書いても1画目として通っていた。
 * 近い書き出し (例: ふ の1画目と2画目) は実際の字形がそうなので許し、
 * 「視覚上同じ点」(距離 SAME 以下) だけをデータ事故として落とす。
 */
const SAME = 0.045;
/** 本当に同じ角から書き始める字 (ロ・ク・タ の角、5 の縦と横)。字形の事実であって事故ではない */
const CORNER_OK = new Set([
  'kata_ro 1-2',
  'kata_ku 1-2',
  'kata_ta 1-2',
  'kata_gu 1-2',
  'kata_da 1-2',
  'num_5 1-2',
]);
const overlap: string[] = [];
for (const c of targets) {
  const dt = await inkDistance(c.char);
  for (const s of c.strokes) {
    const p = s.points[0];
    const x = Math.round(p.x * S);
    const y = Math.round(p.y * S);
    const px = Math.max(0, Math.min(S - 1, x));
    const py = Math.max(0, Math.min(S - 1, y));
    const gap = dt[py * S + px] / S; // マス1辺に対する比
    if (gap > MAX) bad.push({ id: c.id, char: c.char, stroke: s.index, gap });
    else worstOk = Math.max(worstOk, gap);
  }
  for (let i = 0; i < c.strokes.length; i++) {
    for (let j = i + 1; j < c.strokes.length; j++) {
      const d = Math.hypot(
        c.strokes[j].points[0].x - c.strokes[i].points[0].x,
        c.strokes[j].points[0].y - c.strokes[i].points[0].y,
      );
      if (d <= SAME && !CORNER_OK.has(`${c.id} ${i + 1}-${j + 1}`)) {
        overlap.push(
          `${c.char} ${c.id}: ${i + 1}画目と${j + 1}画目の書き出しが同じ点にある (距離 ${(d * 100).toFixed(1)}%)`,
        );
      }
    }
  }
}
await browser.close();

if (overlap.length) {
  console.log(`★ 書き出しが同じ点に重なる字 ${overlap.length}件 (番号バッジが同じ場所に2つ出る):`);
  for (const o of overlap) console.log(`  NG ${o}`);
}

/**
 * 既知のズレは baseline に記録し、落とすのは「新しく入ったもの」と
 * 「悪化したもの」だけにする (scripts/_pii_baseline.txt と同じ考え方)。
 * ★ 直したら baseline から消すこと。消し忘れも検出する。
 * ★ 数字を書き換えて黙らせないこと。ここに載っている字は
 *   「書き出しの点がお手本の上に無い = 直っていない」という意味。
 */
const baselineFile = path.join(here, '_start_dots_baseline.txt');
const baseline = new Map<string, number>();
if (fs.existsSync(baselineFile)) {
  for (const line of fs.readFileSync(baselineFile, 'utf8').split('\n')) {
    const t = line.trim();
    if (!t || t.startsWith('#')) continue;
    const [id, stroke, gap] = t.split(/\s+/);
    baseline.set(`${id} ${stroke}`, Number(gap));
  }
}
const WORSE = 0.01; // 1% を超えて悪化したら落とす

console.log(
  `書き出しの点がお手本の墨から離れていないか: ${targets.length}字 / 許容 ${(MAX * 100).toFixed(1)}%`,
);
bad.sort((a, b) => b.gap - a.gap);
const fresh: Bad[] = [];
const worse: Bad[] = [];
for (const b of bad) {
  const known = baseline.get(`${b.id} ${b.stroke}`);
  if (known === undefined) fresh.push(b);
  else if (b.gap > known + WORSE) worse.push(b);
}
// ★ 今回測った画に属する行だけを見る。id を指定して絞って回したときに
//   「測っていない行」まで直ったことにすると、一覧から消えて追跡できなくなる
const measured = new Set(
  targets.flatMap((c) => c.strokes.map((s) => `${c.id} ${s.index}`)),
);
const fixed = [...baseline.keys()].filter(
  (k) => measured.has(k) && !bad.some((b) => `${b.id} ${b.stroke}` === k),
);

if (bad.length) {
  console.log(`  既知のズレ ${bad.length - fresh.length}画 (baseline に記録済み・未修正):`);
  for (const b of bad.slice(0, 8)) {
    console.log(`    ${b.char} ${b.id.padEnd(16)} ${b.stroke}画目  ${(b.gap * 100).toFixed(1)}%`);
  }
  if (bad.length > 8) console.log(`    … 他 ${bad.length - 8}画 (全部見るなら --max 1 で)`);
}
for (const b of fresh) {
  console.log(`NG 新しく浮いた: ${b.char} ${b.id} ${b.stroke}画目 ${(b.gap * 100).toFixed(1)}%`);
}
for (const b of worse) {
  console.log(
    `NG 悪化: ${b.char} ${b.id} ${b.stroke}画目 ${((baseline.get(`${b.id} ${b.stroke}`) ?? 0) * 100).toFixed(1)}% → ${(b.gap * 100).toFixed(1)}%`,
  );
}
if (fixed.length) {
  console.log(`★ 直ったのに baseline に残っている ${fixed.length}件: ${fixed.join(' / ')}`);
  console.log('  → tools/_start_dots_baseline.txt から消すこと');
}
if (fresh.length || worse.length || fixed.length || overlap.length) {
  process.exit(1); // ★ 検査は必ず落とす。印字だけして exit 0 にしない
}
console.log(
  bad.length === 0
    ? `OK: 全画が許容内 (最大 ${(worstOk * 100).toFixed(1)}%)`
    : `OK: 新しいズレ・悪化なし (既知の未修正 ${bad.length}画)`,
);
