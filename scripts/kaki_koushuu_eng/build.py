# -*- coding: utf-8 -*-
"""
トリリオン夏期講習 英語テキストを PDF 化（~/Desktop へ）。

  python3 build.py chu     # 中学生版（問題編・解答解説編）
  python3 build.py kou     # 高校生版
  python3 build.py both    # 両方（既定）

事前に check.py が ALL PASS であること（build 側でも自動実行し、FAIL なら中止）。
"""
import sys, subprocess, importlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
from build_common import build_book  # noqa: E402

MODMAP = {"chu": "content_chu", "kou": "content_kou"}


def run_check(which):
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py"), which],
                       cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(f"check.py FAILED for {which} — 内容を直してからビルドすること")


def build_one(which):
    run_check(which)
    m = importlib.import_module(MODMAP[which])
    importlib.reload(m)
    q, a = build_book(m.META, m.GRAMMAR, m.READING)
    print(f"[{which}] 問題編: {q}")
    print(f"[{which}] 解答解説編: {a}")
    return q, a


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    targets = ["chu", "kou"] if which == "both" else [which]
    outs = []
    for t in targets:
        outs.extend(build_one(t))
    print("\n=== 完成 ===")
    for o in outs:
        print(" •", o)


if __name__ == "__main__":
    main()
