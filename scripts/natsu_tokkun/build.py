# -*- coding: utf-8 -*-
"""
中学生 夏休み特訓プリント［5科総合］を PDF 化（~/Desktop へ 問題編・解答解説編の2冊）。

  python3 build.py

check.py が ALL PASS でなければビルドしない（＝落ちた内容が配布物に行かない）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def run_check():
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py")],
                       cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr)
        sys.exit("check.py FAILED — 内容を直してからビルドすること")


def verify_pages_per_day(pdf_path, expect):
    """★完成PDFを開いて「1日ぶり何ページか」を実測し、紙に刷った数と突き合わせる。

    初版は進め方の表に「1日1ページ」と刷っていたが、実物は1日3ページだった。
    紙に刷った数字が実物と食い違う事故は、機械QAでもゲートでも出ない
    （どちらも"作った本人の申告"を見ていないため）。ここだけが唯一の検出点。
    """
    import re
    import fitz
    d = fitz.open(pdf_path)
    heads = []
    for i, pg in enumerate(d):
        t = pg.get_text()
        if "目安 40分" in t:                      # DAY見出し帯にだけ出る文字列
            m = re.search(r"DAY\s*(\d+)", t)
            heads.append((i + 1, int(m.group(1)) if m else None))
    total = d.page_count
    d.close()
    if not heads:
        sys.exit("★DAY見出しが1つも見つからない（book.day_head の文言を変えたら"
                 "この検査のキーワードも直すこと）")
    spans = []
    for k, (p, n) in enumerate(heads):
        end = heads[k + 1][0] - 1 if k + 1 < len(heads) else total
        spans.append((n, end - p + 1))
    bad = [f"DAY{n}={s}ページ" for n, s in spans if s != expect]
    if bad:
        sys.exit(f"★紙に刷った「1日ぶん{expect}ページ」と実物が食い違う: " + "／".join(bad)
                 + f"\n  → book.PAGES_PER_DAY を実測値に直すか、組版を調整すること"
                 + f"（実測: {[s for _, s in spans]}）")
    print(f" 1日ぶりのページ数：全{len(spans)}日とも {expect}ページ（実測と一致）")


def main():
    run_check()
    import content as C
    from book import build_book, PAGES_PER_DAY
    q, a = build_book(C.META, C.DAYS, C.POINTS)
    verify_pages_per_day(q, PAGES_PER_DAY)
    print("\n=== 完成 ===")
    print(" 問題編　　：", q)
    print(" 解答解説編：", a)


if __name__ == "__main__":
    main()
