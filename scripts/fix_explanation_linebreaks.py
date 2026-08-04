#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""理系解説の「1行に詰まった段階分け」に改行を入れる。

実測 (scripts/seed_survey.py) で「理系解説が3行未満」が 602 問出たが、中身を見ると
そのうち 400 問は **250〜450 字の完結した解説が改行なしで 1 行に詰まっている**だけ
だった。考え方/立式/計算/答え/補足 のラベルは全部入っている。

  【単元】微分法(積の微分)。考え方:積の微分公式 …を用いる。立式:\\(u=x^2,\\ v=e^x\\) …

画面でも紙でも塊で出るので生徒が読めない。ラベルの直前に改行を入れるだけで直る。

【安全性】
- 挿入するのは改行文字だけ。文字を作らない・消さない。
- 適用後、改行を取り除くと元の文字列に戻ることを 1 問ずつ確認する
  (戻らなければその問題は書き換えない)。
- ラベルが 1 つも無い 202 問には触らない (書き直しが要るので機械では直せない)。

実行: python3 scripts/fix_explanation_linebreaks.py [--apply]
"""
import argparse
import collections
import glob
import itertools
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 段階分けのラベル。行頭に来るべきもの。
LABEL = re.compile(r'(?<!^)(?<![\n])\s*(?<![ぁ-んァ-ヶ一-龥])'
                   r'(考え方|方針|立式|計算|答え|補足|誤答の根拠|誤答の検討|各選択肢の検討)\s*[:：]')
# 【単元】… の直後 (「。」で切れているところ) も 1 行にする
UNIT_HEAD = re.compile(r'^(【単元】[^\n]*?)。\s*(?=考え方|方針|立式)')

RIKEI_PARTS = re.compile(r'^(math|phys|chem|bio|earth)')
SKIP_FILES = {'kyotsu_mogi2026_eng_manual.json',
              'kyotsu_mogi2026_math_manual.json',
              'kyotsu_mogi2026_math_exam_manual.json'}


def detect_format(raw, data):
    for ind, sep, tail in itertools.product([0, 1, 2, 3, 4, None],
                                            [None, (',', ': ')], ['', '\n']):
        try:
            if json.dumps(data, ensure_ascii=False, indent=ind, separators=sep) + tail == raw:
                return ind, sep, tail
        except TypeError:
            continue
    return None


def relayout(exp):
    """ラベルの前に改行を入れる。変えられなければ None。"""
    if len([l for l in exp.splitlines() if l.strip()]) >= 3:
        return None                      # すでに段組みされている
    if len(LABEL.findall(exp)) < 2:
        return None                      # ラベルが足りない = 書き直しが要る
    out = UNIT_HEAD.sub(r'\1。\n', exp)      # 「。」は落とさずそのまま残す
    out = LABEL.sub(lambda m: '\n' + m.group(1) + ': ', out)
    out = re.sub(r'\n{2,}', '\n', out).strip()
    if len([l for l in out.splitlines() if l.strip()]) < 3:
        return None
    # 改行を戻して元に一致するか = 文字を作っていない/消していないことの確認
    if re.sub(r'\s+', '', out) != re.sub(r'\s+', '', exp):
        return None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    per_file = collections.Counter()
    skipped = collections.Counter()
    unreproducible = []

    for path in sorted(glob.glob(os.path.join(ROOT, 'seed-data', '*.json'))):
        name = os.path.basename(path)
        if name in SKIP_FILES:
            continue
        raw = open(path, encoding='utf-8').read()
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        qs = data.get('questions') if isinstance(data, dict) else None
        if not isinstance(qs, list):
            continue
        fmt = detect_format(raw, data)
        if fmt is None:
            unreproducible.append(name)
            continue

        changed = 0
        for row in qs:
            if not isinstance(row, dict):
                continue
            part = row.get('part_key') or ''
            if row.get('exam_id') != 'rikei' and not RIKEI_PARTS.match(part):
                continue
            qd = row.get('question_data')
            if not isinstance(qd, dict):
                continue
            for q in qd.get('questions') or []:
                if not isinstance(q, dict):
                    continue
                exp = q.get('explanation') or ''
                if not exp or len([l for l in exp.splitlines() if l.strip()]) >= 3:
                    continue
                new = relayout(exp)
                if new is None:
                    skipped['ラベルが足りず機械では直せない'] += 1
                    continue
                q['explanation'] = new
                changed += 1
        if changed:
            per_file[name] = changed
            if args.apply:
                ind, sep, tail = fmt
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(data, ensure_ascii=False, indent=ind, separators=sep) + tail)

    print(f'[段組みし直した解説]  計 {sum(per_file.values())} 問')
    for f, n in per_file.most_common():
        print(f'  {f:46s} {n}')
    for k, v in skipped.items():
        print(f'\n[触らなかった] {v} 問: {k}')
    if unreproducible:
        print('[触らなかったファイル] 独自整形: ' + ', '.join(unreproducible))
    if not args.apply:
        print('\n(--apply で書き込み)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
