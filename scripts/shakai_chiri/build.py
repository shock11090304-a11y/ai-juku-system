# -*- coding: utf-8 -*-
"""
中学社会 地理演習を PDF 化（~/Desktop へ 問題編・解答解説編の2冊）。

  python3 build.py            # No.01
  python3 build.py no01

check.py が ALL PASS でなければビルドしない（内容を直してから再実行すること）。
"""
import sys, os, subprocess, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_common import build_book  # noqa: E402

# 号ごとに「content モジュール」と「その号を検査する check スクリプト」を組で持つ。
# ★check.py を全号で使い回さないこと（No.01 の check は雨温図の月別値を No.01 の定数で
#   検算しているので、No.02 に当てると通ってしまう＝検査したつもりになる）。
MODMAP = {"no01": ("content_no01", "check.py"),
          "no02": ("content_no02", "check_no02.py")}


def run_check(script="check.py"):
    r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                       cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr)
        sys.exit("check.py FAILED — 内容を直してからビルドすること")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "no01"
    mod, chk = MODMAP[which]
    run_check(chk)
    m = importlib.import_module(mod)
    q, a = build_book(m.META, m.POINTS, m.PART1, m.PART2, m.PART3)
    print("\n=== 完成 ===")
    print(" 問題編　　：", q)
    print(" 解答解説編：", a)


if __name__ == "__main__":
    main()
