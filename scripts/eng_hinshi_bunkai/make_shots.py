# -*- coding: utf-8 -*-
"""Threads 投稿用の切り出し画像を ~/Desktop/品詞分解_Threads用/ に書き出す。

PDF の一部を高 DPI でクリップし、スマホでも読める幅に整える。
座標は A4（595×842pt）基準。上下左右に少し余白を残して切る。
"""
import os, fitz

DESK = os.path.expanduser("~/Desktop")
OUT = os.path.join(DESK, "品詞分解_Threads用")
DPI = 220
PDF = {"Q": os.path.join(DESK, "英語_品詞分解トレーニング_問題編.pdf"),
       "A": os.path.join(DESK, "英語_品詞分解トレーニング_解答解説編.pdf")}

# (出力名, PDF, ページ番号(1始まり), クリップ矩形 x0,y0,x1,y1)
# 本文の左端は x≈36.8pt から始まるので、クリップは x0=28 まで引いて字を切らない
SHOTS = [
    ("1_分解図.png",      "A", 2,  (28, 146, 566, 620)),   # 長文1 (1)(2) 色分け分解＋骨組み＋解説
    ("2_記号ルール.png",   "Q", 1,  (28, 282, 566, 690)),   # ( ) [ ] < > の定義4枚＋分解の手順
    ("3_倒置.png",        "A", 15, (28, 566, 566, 778)),   # Only when … does … の倒置
    ("4_問題編.png",      "Q", 4,  (28, 157, 566, 410)),   # 書き込み用の英文が並ぶ面
    ("5_本文.png",        "Q", 3,  (28, 155, 566, 425)),   # 下線と番号の入った長文本文
]


def main():
    os.makedirs(OUT, exist_ok=True)
    docs = {k: fitz.open(v) for k, v in PDF.items()}
    for name, tag, pno, rect in SHOTS:
        page = docs[tag][pno - 1]
        pix = page.get_pixmap(dpi=DPI, clip=fitz.Rect(*rect))
        path = os.path.join(OUT, name)
        pix.save(path)
        print(f"{name:<18} {pix.width}x{pix.height}px  ({tag} p{pno})")
    for d in docs.values():
        d.close()
    print("->", OUT)


if __name__ == "__main__":
    main()
