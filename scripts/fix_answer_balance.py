#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed-data の正解番号の偏りを、選択肢の並べ替えで均す。

実測 (scripts/seed_survey.py) で判明した状態:
  全 5,784 問の正解位置が ①42.5% / ②26.1% / ③17.3% / ④13.6%。
  「迷ったら①」で 4 割強が当たる。大問単位でも 457 大問に偏りがある。
  原因は出題側の癖 (正答を先頭に置いて書き、あとで混ぜていない)。

【やること】
正答の中身は変えず、**選択肢の並び順だけ**を変えて正解位置を散らす。
正答を今の位置から抜き、目標位置に差し込む (誤答の相対順は保つ)。

【触らないもの — 並べ替えると壊れるため】
1. 解説が「選択肢1は〜」「①は〜」と番号で選択肢を指している問題 (403 問)。
   並べ替えると解説の指示先がずれる。番号を書き換える手もあるが、①②③④は
   解説本文で別の用途にも使われるため機械置換は危険。手作業の対象として残す。
2. 選択肢が数値だけの問題 (661 問)。本番でも数値選択肢は昇順に並べるのが通例で、
   並べ替えると不自然になる。
3. seed-data/kyotsu_mogi2026_*.json。ビルダー出力であり CI が「再生成して差分ゼロ」を
   要求する。そもそも大問ごとの順列で配ってあり偏りは無い。

【並べ方】
大問単位で、(a) 大問内で同じ位置が偏らない (b) 同じ位置が 3 問続かない
(c) 全体の位置カウントが均等に近づく、の順で優先して貪欲に決める。
ファイル名・大問・小問の順で決定論的に処理するので、再実行しても同じ結果になる。

実行: python3 scripts/fix_answer_balance.py            # 変更内容の確認だけ
      python3 scripts/fix_answer_balance.py --apply    # 書き込み
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(ROOT, 'seed-data')

# 解説が選択肢を番号で指しているか (指していれば並べ替え禁止)
NUM_REF = re.compile(r'選択肢\s*[0-9１-４]|[①②③④⑤]|(?<![A-Za-z])[1-4]\s*番|\boption\s*[1-4]\b', re.I)
# 選択肢が数値だけか (数値選択肢は昇順のままにする)
NUM_ONLY = re.compile(r'^[\s$\\()a-zA-Z=]*-?[\d.,/]+\s*[^\s]{0,6}$')

SKIP_FILES = {'kyotsu_mogi2026_eng_manual.json',
              'kyotsu_mogi2026_math_manual.json',
              'kyotsu_mogi2026_math_exam_manual.json'}


def detect_format(raw, data):
    """元ファイルをバイト単位で再現できる json.dumps の引数を突き止める。

    seed-data の整形はファイルごとにばらばら (indent 0/1/2・末尾改行の有無・
    配列をインライン化した独自整形もある)。当てずっぽうで書き戻すと中身は
    1 問しか変えていないのに全行差分になってレビューできない。
    再現できなければそのファイルには触らない。
    """
    import itertools
    for ind, sep, tail in itertools.product([0, 1, 2, 3, 4, None],
                                            [None, (',', ': ')], ['', '\n']):
        try:
            if json.dumps(data, ensure_ascii=False, indent=ind, separators=sep) + tail == raw:
                return ind, sep, tail
        except TypeError:
            continue
    return None


def locked(q):
    """並べ替えてはいけない問題か。理由を返す (並べ替えてよければ None)。"""
    ch = q.get('choices')
    if not isinstance(ch, list) or len(ch) < 2:
        return 'choices なし'
    if not isinstance(q.get('answer'), int):
        return 'answer が int でない'
    if not (0 <= q['answer'] < len(ch)):
        return 'answer が範囲外'
    if NUM_REF.search(q.get('explanation') or ''):
        return '解説が選択肢を番号で参照'
    if all(NUM_ONLY.match(str(c) or '') for c in ch):
        return '選択肢が数値のみ'
    return None


def pick(n_choices, in_daimon, prev, prev2, globalc):
    """次の正解位置を選ぶ。大問内の偏り → 連続 → 全体の偏り の順に優先する。"""
    best, best_key = None, None
    for p in range(n_choices):
        run = 1 if (p == prev and p == prev2) else 0     # 3 連続になるか
        key = (run, in_daimon[p], globalc[p], p)
        if best_key is None or key < best_key:
            best, best_key = p, key
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    globalc = collections.Counter()
    unreproducible = []
    stats = collections.Counter()
    before = collections.Counter()
    after = collections.Counter()
    per_file = collections.Counter()

    for path in sorted(glob.glob(os.path.join(SEED_DIR, '*.json'))):
        name = os.path.basename(path)
        if name in SKIP_FILES:
            continue
        raw = open(path, encoding='utf-8').read()
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        qs = data.get('questions') if isinstance(data, dict) else (data if isinstance(data, list) else None)
        if not isinstance(qs, list):
            continue
        fmt = detect_format(raw, data)
        if fmt is None:
            unreproducible.append(name)
            continue

        # 大問 (question_data) と、フラットなドリル行 (ファイル全体で 1 束) に分ける
        groups = []
        flat = []
        for row in qs:
            if not isinstance(row, dict):
                continue
            if isinstance(row.get('question_data'), dict):
                sub = row['question_data'].get('questions')
                if isinstance(sub, list):
                    groups.append(sub)
            elif 'choices' in row:
                flat.append(row)
        if flat:
            groups.append(flat)

        changed = 0
        for sub in groups:
            in_daimon = collections.Counter()
            prev = prev2 = -1
            # 先に固定分を大問カウントへ入れておく (残りをそこへ寄せない)
            for q in sub:
                if isinstance(q, dict) and locked(q) and isinstance(q.get('answer'), int):
                    in_daimon[q['answer']] += 1
            for q in sub:
                if not isinstance(q, dict) or 'choices' not in q:
                    continue
                why = locked(q)
                if isinstance(q.get('answer'), int) and 0 <= q['answer'] < len(q.get('choices') or []):
                    before[q['answer']] += 1
                if why:
                    stats[why] += 1
                    if isinstance(q.get('answer'), int):
                        after[q['answer']] += 1
                        globalc[q['answer']] += 1
                        prev2, prev = prev, q['answer']
                    continue
                ch, a = list(q['choices']), q['answer']
                t = pick(len(ch), in_daimon, prev, prev2, globalc)
                if t != a:
                    correct = ch.pop(a)
                    ch.insert(t, correct)
                    q['choices'] = ch
                    q['answer'] = t
                    changed += 1
                in_daimon[t] += 1
                globalc[t] += 1
                after[t] += 1
                prev2, prev = prev, t
                stats['並べ替え対象'] += 1

        if changed:
            per_file[name] = changed
            if args.apply:
                ind, sep, tail = fmt
                out = json.dumps(data, ensure_ascii=False, indent=ind, separators=sep) + tail
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(out)

    def dist(c):
        n = sum(c.values()) or 1
        return ' '.join(f'{i + 1}:{100 * c[i] / n:5.1f}%' for i in range(4))

    print('[対象]')
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f'  {v:5d}  {k}')
    print(f'\n[正解位置の分布]  ({sum(before.values())} 問)')
    print(f'  変更前  {dist(before)}')
    print(f'  変更後  {dist(after)}')
    print(f'\n[並べ替えた問題]  計 {sum(per_file.values())} 問')
    for f, n in per_file.most_common():
        print(f'  {f:46s} {n}')
    if unreproducible:
        print('\n[触らなかったファイル] 独自整形で書き戻すと全行差分になるため')
        for f in unreproducible:
            print(f'  {f}')
    if not args.apply:
        print('\n(--apply を付けると書き込みます)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
