# -*- coding: utf-8 -*-
"""
高校日本史 演習プリントを PDF 化（~/Desktop へ 問題編・解答解説編の2冊）。

  python3 build.py

check.py が ALL PASS でなければビルドしない（内容を直してから再実行すること）。
"""
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_common import build_book  # noqa: E402


def run_check():
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py")],
                       cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr)
        sys.exit("check.py FAILED — 内容を直してからビルドすること")


def main():
    run_check()
    import content as m
    q, a = build_book(m.META, m.PART2)
    print("\n=== 完成 ===")
    print(" 問題編　　：", q)
    print(" 解答解説編：", a)


if __name__ == "__main__":
    main()
