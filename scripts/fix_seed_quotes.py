#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed-data の英文本文にある LaTeX 流の引用符 `word' を "word" に直す。

`word' は TeX の書き方で、HTML でも PDF でも開き引用符にならない。
画面には「`smaller and faster'」と生のバッククォートが出る。

本文だけ直すと、その語句を引用している解説と食い違って
seed_survey の引用照合が落ちるので、**本文と解説を同時に**書き換える。

置換は **生の JSON テキスト上**で行う。json.load → json.dump で往復させると
インデントやキー順が変わって差分が全面書き換えになり、レビューできなくなる。

実行: python3 scripts/fix_seed_quotes.py [--apply]
      (--apply を付けない限り書き込まない)
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BQ = re.compile(r"`([^`'\n]{2,60})'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='実際に書き込む')
    args = ap.parse_args()

    total = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'seed-data', '*.json'))):
        raw = open(path, encoding='utf-8').read()
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(data, dict) or 'questions' not in data:
            continue
        # 本文に出てくる `X' を集める (解説の ` ` は語法メモにも使うので、
        # 本文に実在する語だけを置換対象にする)
        terms = []
        for row in data['questions']:
            qd = row.get('question_data')
            if isinstance(qd, dict):
                terms += [m.group(1) for m in BQ.finditer(qd.get('passage') or '')]
        if not terms:
            continue

        out = raw
        for t in sorted(set(terms), key=len, reverse=True):
            esc = t.replace('\\', '\\\\').replace('"', '\\"')
            for src in (f'`{t}\'', f'`{t}`'):
                out = out.replace(src, f'\\"{esc}\\"')
        if out == raw:
            continue
        json.loads(out)          # 壊していないことを確認してから書く
        total += len(terms)
        print(f'{os.path.basename(path)}: 本文 {len(terms)} 箇所 (+ 解説の同語)')
        if args.apply:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)
    print(f'計 {total} 箇所' + ('' if args.apply else ' (--apply で書き込み)'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
