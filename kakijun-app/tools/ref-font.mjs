/**
 * ★ 手本フォントの供給元を1本にする。
 *
 * 字形の計測 (忠実度・中心線抽出・比較シート) は「アプリが実際に表示している字」に
 * 対して行わないと意味がない。以前は各ツールが system にインストールされた
 * "Klee One" を名前で参照していたが、コンテナを作り直すとフォントが消え、
 * ★エラーにならずに代替フォント (IPAGothic 等) を測ってしまう。
 * その状態で refit-glyphs --apply を回すと、全文字の線データがゴシック体に
 * 合わせて作り直され、静かに壊れる。
 *
 * そこで計測は出荷している public/fonts/KleeOne-subset.woff2 を直接読む。
 * これはアプリが画面に描いているファイルそのもの。ネットワークもフォント
 * インストールも要らず、コンテナを作り直しても結果が変わらない。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
export const REF_FONT_FAMILY = 'KakijunSample';
export const REF_FONT_FILE = path.join(here, '../public/fonts/KleeOne-subset.woff2');

/** @font-face 宣言 (data URL 埋め込み。外部参照なしで完結する) */
export function refFontFaceCss() {
  const b64 = fs.readFileSync(REF_FONT_FILE).toString('base64');
  return `@font-face{font-family:'${REF_FONT_FAMILY}';src:url(data:font/woff2;base64,${b64}) format('woff2');font-display:block}`;
}

/**
 * ページに手本フォントを読み込ませる。
 * ★読み込めなかった場合・グリフが無い場合は落とす。黙って代替フォントで
 *   測り続けるのが一番たちが悪いため。
 */
export async function useRefFont(page, sampleChars = ['あ']) {
  await page.addStyleTag({ content: refFontFaceCss() });
  await page.evaluate(
    async (family) => {
      await document.fonts.load(`100px ${family}`);
      await document.fonts.ready;
    },
    REF_FONT_FAMILY,
  );
  const bad = await page.evaluate(
    ({ family, chars }) => {
      const c = document.createElement('canvas');
      c.width = 128;
      c.height = 128;
      const g = c.getContext('2d');
      const draw = (ch, font) => {
        g.clearRect(0, 0, 128, 128);
        g.fillStyle = '#000';
        g.font = font;
        g.textAlign = 'center';
        g.textBaseline = 'middle';
        g.fillText(ch, 64, 64);
        const d = g.getImageData(0, 0, 128, 128).data;
        let h = 0;
        let ink = 0;
        for (let i = 3; i < d.length; i += 4) {
          const v = d[i] > 32 ? 1 : 0;
          ink += v;
          h = (h * 31 + v) >>> 0;
        }
        return { h, ink };
      };
      return chars.filter((ch) => {
        const withFont = draw(ch, `100px ${family}, monospace`);
        const fallback = draw(ch, '100px monospace');
        return withFont.ink === 0 || withFont.h === fallback.h;
      });
    },
    { family: REF_FONT_FAMILY, chars: sampleChars },
  );
  if (bad.length) {
    throw new Error(
      `手本フォント (${path.basename(REF_FONT_FILE)}) が効いていないか、` +
        `グリフが無い: ${bad.join(' ')}\n` +
        `代替フォントで計測すると別の字形を測ることになるので中止する。`,
    );
  }
}
