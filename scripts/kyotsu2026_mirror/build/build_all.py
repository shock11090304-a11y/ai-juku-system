#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4科目一括ビルド: 問題編+解答編を ~/Desktop/共通テスト2026類似問題/ へ。"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(args):
    print("==>", " ".join(args))
    r = subprocess.run([PY] + args, cwd=HERE, capture_output=True, text=True)
    print(r.stdout[-2000:])
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(f"FAILED: {args}")


def main():
    subjects = sys.argv[1:] or ["math1a", "math2bc", "english", "kokugo"]
    for s in subjects:
        if s == "kokugo":
            run([os.path.join(HERE, "build_kokugo.py"), "kokugo"])
            run([os.path.join(HERE, "build_exam.py"), "kokugo", "--answers-only"])
        else:
            run([os.path.join(HERE, "build_exam.py"), s])
    print("ALL DONE")


if __name__ == "__main__":
    main()
