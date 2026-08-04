#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""刷るフォントの cmap を `_print_font_cmap.txt` に書き出す（macOS で実行）。

★何の cmap なのか（取り違えると誤検出になる）
  これは build_common.py の FONT_PATH（Arial Unicode）＝**ノンブル/柱の刻印に使うフォント**の
  cmap。本文は CSS の Hiragino 明朝/角ゴ・Georgia で出るので、ここに無い字でも紙には出る
  （実測: ㉑ U+3251 / ㊿ U+32BF は AU に無くヒラギノにある）。
  だから check.py 側はこの照合を **警告**として扱う。絵文字だけは確実に壊れるので別枠で落とす。

★なぜファイルに固定するのか
  CI (ubuntu) に macOS のフォントは無い。その場にあるフォントで照合すると環境ごとに判定が
  変わり、「手元では通るのに CI では落ちる（逆も）」という再現しない検査になる。

    python3 scripts/kaki_koushuu_eng/gen_font_cmap.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_print_font_cmap.txt")
# build_common.py が実際に PDF へ埋めるフォント（そこを変えたらここも変える）
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"


def main():
    if not os.path.exists(FONT):
        sys.exit(f"刷るフォントが無い: {FONT}\n（このスクリプトは macOS で回す）")
    from fontTools.ttLib import TTFont
    cps = sorted(TTFont(FONT, fontNumber=0).getBestCmap().keys())
    rng, start, prev = [], cps[0], cps[0]
    for c in cps[1:]:
        if c == prev + 1:
            prev = c
            continue
        rng.append((start, prev))
        start = prev = c
    rng.append((start, prev))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# ノンブル/柱の刻印に使うフォント（build_common.py の FONT_PATH）の cmap。\n")
        f.write(f"# font: {FONT}\n")
        f.write(f"# count: {len(cps)}\n")
        f.write("# ★本文はCSSのヒラギノ/Georgiaで出るので、ここに無い字でも紙には出る。\n")
        f.write("#   check.py はこの照合を警告として扱う（err にすると正しい原稿を落とす）。\n")
        f.write("# 再生成: python3 scripts/kaki_koushuu_eng/gen_font_cmap.py （macOS）\n")
        f.write("# 形式: 16進のコードポイント。範囲は start-end\n")
        for a, b in rng:
            f.write(f"{a:04X}-{b:04X}\n" if a != b else f"{a:04X}\n")
    print(f"{OUT}\n  コードポイント {len(cps)} 個 → {len(rng)} 範囲")


if __name__ == "__main__":
    main()
