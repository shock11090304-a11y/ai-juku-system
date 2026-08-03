#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dojo_eng_kyotsu2026_manual.json の解説を 4 セクション形式に揃える。

apply_graph.py と同じ手順を r_short プール (38 大問 / 140 小問) に適用する。
既存の解説は本文を逐語で引き正答の根拠も述べているが、🎯コアイメージ と
🔬文構造分析 が無い。塾の看板である「コアイメージ × 文構造分析」の二段構えが
抜けた状態なので、書き直しではなく **追記** として 4 セクションに組み直す。

- 解説本体は kaisetsu_manual.py に (大問番号, 問番号) をキーとして持たせる。
- 誤答 NG 理由の見出しは choices から機械的に作る (手で書き写すと表記ゆれで
  検証器の 1 対 1 対応が崩れるため)。理由だけを choices 順 (正答を除く) で与える。
- 書き戻し後に scripts/eng_4section/validate.py と同じ検査を通す。

実行: python3 scripts/eng_4section/apply_manual.py            # 確認のみ
      python3 scripts/eng_4section/apply_manual.py --apply    # 書き込み
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
SEED = os.path.join(ROOT, 'seed-data', 'dojo_eng_kyotsu2026_manual.json')

sys.path.insert(0, HERE)
from apply_graph import SECTIONS, detect_format   # noqa: E402  (整形検出は共通)
from kaisetsu_manual import K                     # noqa: E402
import validate as V                              # noqa: E402


def compose(key, q, errors):
    k = K.get(key)
    if not k:
        errors.append(f'{key}: kaisetsu_manual.py に解説が無い')
        return None
    for f in ('core', 'kouzou', 'konkyo', 'ng'):
        if not k.get(f):
            errors.append(f'{key}: 解説の {f} が空')
            return None
    choices = q['choices']
    ans = int(q['answer'])
    distractors = [c for i, c in enumerate(choices) if i != ans]
    if len(k['ng']) != len(distractors):
        errors.append(f'{key}: 誤答 NG 理由が {len(k["ng"])} 件 (誤答は {len(distractors)} 件)')
        return None
    ng_lines = '\n'.join(f'- 「{d}」… {why}' for d, why in zip(distractors, k['ng']))
    return (f'正解は「{choices[ans]}」。\n\n'
            f'{SECTIONS[0]}\n{k["core"]}\n\n'
            f'{SECTIONS[1]}\n{k["kouzou"]}\n\n'
            f'{SECTIONS[2]}\n{k["konkyo"]}\n\n'
            f'{SECTIONS[3]}\n{ng_lines}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    raw = open(SEED, encoding='utf-8').read()
    data = json.loads(raw)
    fmt = detect_format(raw, data)
    if fmt is None:
        print('❌ 元ファイルの整形を再現できない (書き戻すと全行差分になる)')
        return 1

    errors, done, missing = [], 0, 0
    for gi, row in enumerate(data['questions'], start=1):
        qd = row['question_data']
        for qi, q in enumerate(qd['questions'], start=1):
            if (gi, qi) not in K:
                missing += 1
                continue
            exp = compose((gi, qi), q, errors)
            if exp is None:
                continue
            q['explanation'] = exp
            done += 1

    if errors:
        print(f'❌ 組み立てで {len(errors)} 件:')
        for e in errors[:20]:
            print('   -', e)
        return 1

    # 書き戻す前に検証器と同じ検査を通す。まだ書けていない問は 4 セクションが
    # 無いので必ず落ちる → 未着手ぶんは除いて、書いた問だけを検証する。
    vres = []
    for gi, row in enumerate(data['questions'], start=1):
        qd = row['question_data']
        label = qd.get('format_type') or f'大問{gi}'
        for qi, q in enumerate(qd['questions'], start=1):
            if (gi, qi) not in K:
                continue
            V.check_question(f'大問{gi}({label}) 問{qi}', q, qd.get('passage') or '', vres,
                             qd.get('figure_svg') or '')
    if vres:
        print(f'❌ 検証で {len(vres)} 件:')
        for e in vres[:25]:
            print('   -', e)
        return 1

    print(f'✅ {done} 問を 4 セクション形式に組み直した (検証 OK)')
    if missing:
        print(f'   ⚠️ 未着手 {missing} 問 (kaisetsu_manual.py に解説が無い)')
    if args.apply:
        ind, sep, tail = fmt
        with open(SEED, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=ind, separators=sep) + tail)
        print(f'   → {os.path.relpath(SEED, ROOT)}')
    else:
        print('   (--apply で書き込み)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
