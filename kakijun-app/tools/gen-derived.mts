/**
 * 派生文字の一括生成（1回だけ実行して JSON にコミットする）。
 * - 濁音・半濁音: composedFrom 定義を追加 (§4.3 データはゼロから作らない)
 * - 拗音・促音（小さい字）: 清音を 0.62 倍に縮小して左下寄せで生成し、
 *   専用データとして保持する (§4.3 推奨に従い、あとから手で調整できる)
 * 実行: npx vite-node tools/gen-derived.mts
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { RawCharacterDef } from '../src/engine/types';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, '../src/data/characters');

// 濁音・半濁音の対応表: [合成先の字, base の字, マーク]
const DAKUON: [string, string, 'dakuten' | 'handakuten'][] = [
  ['が', 'か', 'dakuten'], ['ぎ', 'き', 'dakuten'], ['ぐ', 'く', 'dakuten'],
  ['げ', 'け', 'dakuten'], ['ご', 'こ', 'dakuten'],
  ['ざ', 'さ', 'dakuten'], ['じ', 'し', 'dakuten'], ['ず', 'す', 'dakuten'],
  ['ぜ', 'せ', 'dakuten'], ['ぞ', 'そ', 'dakuten'],
  ['だ', 'た', 'dakuten'], ['ぢ', 'ち', 'dakuten'], ['づ', 'つ', 'dakuten'],
  ['で', 'て', 'dakuten'], ['ど', 'と', 'dakuten'],
  ['ば', 'は', 'dakuten'], ['び', 'ひ', 'dakuten'], ['ぶ', 'ふ', 'dakuten'],
  ['べ', 'へ', 'dakuten'], ['ぼ', 'ほ', 'dakuten'],
  ['ぱ', 'は', 'handakuten'], ['ぴ', 'ひ', 'handakuten'], ['ぷ', 'ふ', 'handakuten'],
  ['ぺ', 'へ', 'handakuten'], ['ぽ', 'ほ', 'handakuten'],
];

const KATA_DAKUON: [string, string, 'dakuten' | 'handakuten'][] = [
  ['ガ', 'カ', 'dakuten'], ['ギ', 'キ', 'dakuten'], ['グ', 'ク', 'dakuten'],
  ['ゲ', 'ケ', 'dakuten'], ['ゴ', 'コ', 'dakuten'],
  ['ザ', 'サ', 'dakuten'], ['ジ', 'シ', 'dakuten'], ['ズ', 'ス', 'dakuten'],
  ['ゼ', 'セ', 'dakuten'], ['ゾ', 'ソ', 'dakuten'],
  ['ダ', 'タ', 'dakuten'], ['ヂ', 'チ', 'dakuten'], ['ヅ', 'ツ', 'dakuten'],
  ['デ', 'テ', 'dakuten'], ['ド', 'ト', 'dakuten'],
  ['バ', 'ハ', 'dakuten'], ['ビ', 'ヒ', 'dakuten'], ['ブ', 'フ', 'dakuten'],
  ['ベ', 'ヘ', 'dakuten'], ['ボ', 'ホ', 'dakuten'],
  ['パ', 'ハ', 'handakuten'], ['ピ', 'ヒ', 'handakuten'], ['プ', 'フ', 'handakuten'],
  ['ペ', 'ヘ', 'handakuten'], ['ポ', 'ホ', 'handakuten'],
];

// 小さい字: [小さい字, 清音]
const SMALL: [string, string][] = [
  ['ゃ', 'や'], ['ゅ', 'ゆ'], ['ょ', 'よ'], ['っ', 'つ'],
  ['ぁ', 'あ'], ['ぃ', 'い'], ['ぅ', 'う'], ['ぇ', 'え'], ['ぉ', 'お'],
];
const KATA_SMALL: [string, string][] = [
  ['ャ', 'ヤ'], ['ュ', 'ユ'], ['ョ', 'ヨ'], ['ッ', 'ツ'],
  ['ァ', 'ア'], ['ィ', 'イ'], ['ゥ', 'ウ'], ['ェ', 'エ'], ['ォ', 'オ'],
];

const SCALE = 0.62;
const OFFSET = { x: 0.07, y: 0.31 }; // 左下寄せ（横書きの小書き字の位置）

function processFile(
  file: string,
  dakuon: [string, string, 'dakuten' | 'handakuten'][],
  small: [string, string][],
): void {
  const p = path.join(dataDir, file);
  const defs = JSON.parse(fs.readFileSync(p, 'utf8')) as RawCharacterDef[];
  const byChar = new Map(defs.map((d) => [d.char, d]));
  let added = 0;

  for (const [chr, baseChar, mark] of dakuon) {
    if (byChar.has(chr)) continue;
    const base = byChar.get(baseChar);
    if (!base) throw new Error(`base not found: ${baseChar}`);
    const def: RawCharacterDef = {
      id: `${base.id}_${mark === 'dakuten' ? 'd' : 'h'}`.replace(
        base.id,
        base.id.replace(/^(hira|kata)_/, '$1_'),
      ),
      char: chr,
      reading: chr,
      type: base.type,
      group: mark === 'dakuten' ? 'dakuon' : 'handakuon',
      strokes: [],
      composedFrom: { base: base.id, marks: [`mark_${mark}`] },
    };
    // id は「hira_ga」の形式にする
    def.id = `${base.id.split('_')[0]}_${romajiOf(chr)}`;
    defs.push(def);
    byChar.set(chr, def);
    added++;
  }

  for (const [chr, baseChar] of small) {
    if (byChar.has(chr)) continue;
    const base = byChar.get(baseChar);
    if (!base) throw new Error(`base not found: ${baseChar}`);
    const def: RawCharacterDef = {
      id: `${base.id.split('_')[0]}_small_${romajiOf(baseChar)}`,
      char: chr,
      reading: `ちいさい ${baseChar}`,
      type: base.type,
      group: 'youon',
      strokes: base.strokes.map((s) => ({
        ...s,
        points: s.points.map(([x, y]) => [
          Math.round((x * SCALE + OFFSET.x) * 1000) / 1000,
          Math.round((y * SCALE + OFFSET.y) * 1000) / 1000,
        ]),
      })),
    };
    defs.push(def);
    byChar.set(chr, def);
    added++;
  }

  fs.writeFileSync(p, JSON.stringify(defs, null, 2) + '\n');
  console.log(`${file}: +${added} → ${defs.length} 文字`);
}

/** 濁音・小書き字の id 用ローマ字 */
function romajiOf(chr: string): string {
  const map: Record<string, string> = {
    が: 'ga', ぎ: 'gi', ぐ: 'gu', げ: 'ge', ご: 'go',
    ざ: 'za', じ: 'ji', ず: 'zu', ぜ: 'ze', ぞ: 'zo',
    だ: 'da', ぢ: 'dji', づ: 'dzu', で: 'de', ど: 'do',
    ば: 'ba', び: 'bi', ぶ: 'bu', べ: 'be', ぼ: 'bo',
    ぱ: 'pa', ぴ: 'pi', ぷ: 'pu', ぺ: 'pe', ぽ: 'po',
    ガ: 'ga', ギ: 'gi', グ: 'gu', ゲ: 'ge', ゴ: 'go',
    ザ: 'za', ジ: 'ji', ズ: 'zu', ゼ: 'ze', ゾ: 'zo',
    ダ: 'da', ヂ: 'dji', ヅ: 'dzu', デ: 'de', ド: 'do',
    バ: 'ba', ビ: 'bi', ブ: 'bu', ベ: 'be', ボ: 'bo',
    パ: 'pa', ピ: 'pi', プ: 'pu', ペ: 'pe', ポ: 'po',
    や: 'ya', ゆ: 'yu', よ: 'yo', つ: 'tsu',
    あ: 'a', い: 'i', う: 'u', え: 'e', お: 'o',
    ヤ: 'ya', ユ: 'yu', ヨ: 'yo', ツ: 'tsu',
    ア: 'a', イ: 'i', ウ: 'u', エ: 'e', オ: 'o',
  };
  const r = map[chr];
  if (!r) throw new Error(`no romaji for ${chr}`);
  return r;
}

processFile('hiragana.json', DAKUON, SMALL);
processFile('katakana.json', KATA_DAKUON, KATA_SMALL);
