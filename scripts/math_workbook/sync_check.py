#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ソースを直したのに PDF を再ビルドし忘れる事故を検出する。

  python3 sync_check.py suuA

実際に「content を直したが PDF は古いまま」で納品しかけた（レビューで発覚）。
KaTeX で組んだ PDF は数式部分がテキスト抽出で改行になるため、素朴な文字列比較は
偽陰性を出す（これも実際に踏んだ）。日本語部分だけを取り出して突き合わせる。
"""
import importlib
import os
import re
import sys

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_kiso as BK  # noqa: E402

JP = re.compile(r"[ぁ-んァ-ヶ一-龥、。（）「」]{4,}")


def jp_chunks(s):
    """日本語の連続部分だけを取り出す（数式は KaTeX 描画で消えるため比較対象にしない）。"""
    return {m.group(0) for m in JP.finditer(re.sub(r"\s+", "", s))}


def main():
    vol = sys.argv[1] if len(sys.argv) > 1 else "kiso"
    V = BK.VOLUMES[vol]
    C = importlib.import_module(V["content"])
    pdf = os.path.join(HERE, V["out"])
    if not os.path.exists(pdf):
        sys.exit(f"PDF が無い: {pdf}")

    src_txt = []
    for p in C.PARTS:
        src_txt.append(p.get("sub", ""))
        for u in p["units"]:
            for q in u["problems"]:
                src_txt += [q.get("stem", ""), q.get("answer", ""), q.get("explanation", "")]
    want = set()
    for s in src_txt:
        want |= jp_chunks(s)

    # ★集合の完全一致で照合すると、PDF側は数式のところで分断されて別チャンクになり
    #   ほぼ全件が「無い」と誤検出される（実際そうなった）。空白を除いた本文に対する
    #   部分文字列検索で照合する。
    got = re.sub(r"\s+", "", " ".join(pg.get_text() for pg in fitz.open(pdf)))
    missing = sorted(w for w in want if w not in got)

    print(f"=== ソース↔PDF 同期チェック（{V['out']}）===")
    print(f"  日本語チャンク: ソース{len(want)}個 ／ PDFに存在 {len(want)-len(missing)}個")
    if missing:
        print(f"\n  ★PDFに無い（＝再ビルドし忘れ）: {len(missing)}件")
        for m in missing[:12]:
            print("   ×", m[:60])
        sys.exit(1)
    print("  ✓ ソースの本文はすべてPDFに反映されている")


if __name__ == "__main__":
    main()
