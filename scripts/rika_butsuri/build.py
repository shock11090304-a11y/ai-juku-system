# -*- coding: utf-8 -*-
"""
中学理科［物理分野］確認プリントを PDF 化（~/Desktop へ 問題編・解答解説編の2冊）。

  python3 build.py            # No.01

check.py が ALL PASS でなければビルドしない（内容を直してから再実行すること）。
★ゲートが落ちたときに PDF を書かないこと＝落ちたはずの内容が配布物に行くのを防ぐ。
"""
import sys, os, subprocess, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_common import build_book  # noqa: E402

MODMAP = {"no01": "content_no01"}


def run_check():
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py")],
                       cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr)
        sys.exit("check.py FAILED — 内容を直してからビルドすること")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "no01"
    run_check()
    m = importlib.import_module(MODMAP[which])
    q, a = build_book(m.META, m.POINTS, m.PART1, m.PART2, m.PART3)
    print("\n=== 完成 ===")
    print(" 問題編　　：", q)
    print(" 解答解説編：", a)


if __name__ == "__main__":
    main()
