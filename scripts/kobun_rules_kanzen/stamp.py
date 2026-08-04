# -*- coding: utf-8 -*-
"""Chrome print-to-pdf の出力に、問題編と同じ体裁のフッタを全ページ刻印する。

Chrome は CSS Paged Media のマージンボックス(@bottom-center)を解さないので、
「n / N」を含むフッタは HTML 側では書けない。生成後に PyMuPDF で入れる。

usage: python3 stamp.py <in.pdf> <out.pdf> <NotoSansJP.ttf>
"""
import sys

import fitz

FOOTER = "Trillion English Academy　—　古文［ルールで解く］完全版 解答解説編　—　%d / %d"
NAVY = (0x16 / 255, 0x24 / 255, 0x3F / 255)
GOLD = (0xC2 / 255, 0xA1 / 255, 0x4D / 255)


def main():
    src, dst, ttf = sys.argv[1], sys.argv[2], sys.argv[3]
    doc = fitz.open(src)
    font = fitz.Font(fontfile=ttf)  # 幅計測と描画で同じフォント実体を使う
    n = doc.page_count
    size = 6.4
    for i, page in enumerate(doc, 1):
        w, h = page.rect.width, page.rect.height
        y = h - 26
        # 金の細罫（本文は下マージン15mm=42.5pt を確保してある）
        page.draw_line(fitz.Point(31, y), fitz.Point(w - 31, y), color=GOLD, width=0.6)
        txt = FOOTER % (i, n)
        tl = font.text_length(txt, fontsize=size)
        writer = fitz.TextWriter(page.rect, color=NAVY)
        writer.append(fitz.Point(w - 31 - tl, y + 9.5), txt, font=font, fontsize=size)
        writer.write_text(page)
    doc.subset_fonts()
    doc.save(dst, garbage=4, deflate=True)
    print("stamped %d pages -> %s" % (n, dst))


if __name__ == "__main__":
    main()
