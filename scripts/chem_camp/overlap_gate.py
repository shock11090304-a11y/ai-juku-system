#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行またぎの文字の物理的な重なりを検出するゲート。

  python3 overlap_gate.py [pdf ...]

なぜ要るか: KaTeX の \\dfrac / 上付き下付きは vlist(height:0)で組まれるため、
数式の実際の高さが CSS の行ボックスに算入されない。行送りが足りないと、
上の行の分母と下の行の指数が**紙の上で物理的に重なる**。PDF は正常に生成され、
文字抽出でも普通に読めてしまうので、字形の矩形どうしを総当たりで見るしかない。
(実例: 解答13-3 の「0.20/2.0」の分母 2.0 が次行「0.80^2」の指数の上に乗り、指数が判読不能だった)
"""
import sys, os, collections
import fitz

XPAD = 0.4        # x方向の重なりがこれ以上(pt)
YPAD = 0.8        # y方向の重なりがこれ以上(pt)
LINE_GAP = 8.0    # y中心がこれ以上離れていれば「別の行」とみなす(pt)
# ★3.0 にすると $\mathrm{SO_4^{2-}}$ の下付き 4 と上付き 2- が同じ x に積まれている
#   (正しい組版)のを重なりと誤検出する。実測でこの積み重ねの y 中心差は最大 6.1pt、
#   一方の行送りは 25pt 前後なので、その中間の 8.0 を境目にする。


def chars(page):
    out = []
    for blk in page.get_text("rawdict")["blocks"]:
        for line in blk.get("lines", []):
            for span in line["spans"]:
                for ch in span["chars"]:
                    c = ch["c"]
                    if c.strip():
                        out.append((fitz.Rect(ch["bbox"]), c))
    return out


def overlaps(page):
    cs = chars(page)
    # x を 20pt 刻みでバケットに入れ、隣接バケットとだけ突き合わせる(総当たりの回避)
    buckets = collections.defaultdict(list)
    for r, c in cs:
        for b in range(int(r.x0 // 20), int(r.x1 // 20) + 1):
            buckets[b].append((r, c))
    hits, seen = [], set()
    for b, items in buckets.items():
        for i in range(len(items)):
            r1, c1 = items[i]
            for j in range(i + 1, len(items)):
                r2, c2 = items[j]
                if abs((r1.y0 + r1.y1) / 2 - (r2.y0 + r2.y1) / 2) < LINE_GAP:
                    continue                      # 同じ行(添字と本体など)は対象外
                ox = min(r1.x1, r2.x1) - max(r1.x0, r2.x0)
                oy = min(r1.y1, r2.y1) - max(r1.y0, r2.y0)
                if ox > XPAD and oy > YPAD:
                    key = (round(r1.x0, 1), round(r1.y0, 1), round(r2.x0, 1), round(r2.y0, 1))
                    if key not in seen:
                        seen.add(key)
                        hits.append((c1, c2, round(ox, 2), round(oy, 2), round(r1.y0, 1)))
    return hits


def main(paths):
    total = 0
    for p in paths:
        doc = fitz.open(p)
        n = 0
        for i, page in enumerate(doc, 1):
            h = overlaps(page)
            if h:
                n += len(h)
                print(f"  {os.path.basename(p)} p{i}: {len(h)}件  例 "
                      + ", ".join(f"'{a}'×'{b}'(x{ox}pt,y{oy}pt)" for a, b, ox, oy, _ in h[:3]))
        print(f"{os.path.basename(p)}: 重なり {n} 件 / {doc.page_count}ページ")
        total += n
        doc.close()
    print(f"\n合計 {total} 件")
    return 1 if total else 0


if __name__ == "__main__":
    args = sys.argv[1:] or ["kagaku_riron_soufukushu.pdf", "gasshuku_gakushu_keikaku.pdf",
                            "kagaku_jiko_saiten_sheet.pdf", "kagaku_shindan_key.pdf"]
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(main([a if os.path.isabs(a) else os.path.join(here, a) for a in args]))
