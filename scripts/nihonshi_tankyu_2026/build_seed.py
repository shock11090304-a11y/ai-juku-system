#!/usr/bin/env python3
"""日本史探究: 検証済みrowをスキーマ検証してseed JSONを組み立てる(リバランスなし)。
使い方: build_seed.py <rows.json> [--out=PATH]
- 組合せ/正誤/整序の選択肢は位置に意味があるためシャッフルしない(英語と異なる)。
- explanation は「【単元】<時代>。正解は「<choices[answer]>」。」を含むこと。
"""
import json, re, sys, os

TANGEN = re.compile(r'^【単元】')


def cited_ok(ex, choice):
    """解説が「正解は「<choice>」で始まる正答テキストを述べているか(前方一致・末尾句点許容)。"""
    i = ex.find('正解は「')
    if i < 0:
        return False
    rest = ex[i + len('正解は「'):]
    key = str(choice).strip()
    return rest.startswith(key) or rest.startswith(key.rstrip('。．.'))
FIG_HINTS = ['下の図', '右の図', '左の図', '上の図', '次の図', 'の写真', 'のグラフ', 'の地図', 'パネル', '図版', '絵画資料', '屏風']
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'seed-data', 'dojo_nihonshi_tankyu_manual.json')


def main():
    args = sys.argv[1:]
    out = OUT
    paths = []
    for a in args:
        if a.startswith('--out='):
            out = a[6:]
        else:
            paths.append(a)
    rows = []
    for p in paths:
        rows.extend(json.load(open(p)))
    errs, warns = [], []
    for i, r in enumerate(rows):
        for k in ('exam_id', 'part_key', 'eiken_grade', 'model', 'question_data'):
            if k not in r:
                errs.append(f'row{i}: missing {k}')
        if r.get('exam_id') != 'daigaku':
            errs.append(f"row{i}: exam_id={r.get('exam_id')}")
        if r.get('part_key') != 'nihonshi':
            errs.append(f"row{i}: part_key={r.get('part_key')}")
        if r.get('eiken_grade') != 'kyotsu':
            errs.append(f"row{i}: eiken_grade={r.get('eiken_grade')}")
        qd = r.get('question_data') or {}
        if not qd.get('passage'):
            errs.append(f'row{i}: empty passage')
        if qd.get('subject') != '社会':
            warns.append(f"row{i}: subject={qd.get('subject')}")
        qs = qd.get('questions') or []
        if not qs:
            errs.append(f'row{i}: no questions')
        blob = qd.get('passage', '')
        for j, q in enumerate(qs):
            for k in ('id', 'type', 'stem', 'choices', 'answer', 'unit', 'explanation'):
                if k not in q:
                    errs.append(f'row{i}.q{j}: missing {k}')
            ch = q.get('choices') or []
            a = q.get('answer')
            if not isinstance(ch, list) or len(ch) < 4:
                errs.append(f'row{i}.q{j}: choices<4'); continue
            if not isinstance(a, int) or a < 0 or a >= len(ch):
                errs.append(f'row{i}.q{j}: answer {a} out of range'); continue
            ex = q.get('explanation') or ''
            if not TANGEN.match(ex):
                errs.append(f'row{i}.q{j}: 解説が【単元】で始まらない: {ex[:30]}')
            # 「正解は「<選択肢テキスト>」を前方一致で照合(選択肢が末尾。や入れ子「」を含んでも安全)
            if '正解は「' not in ex:
                errs.append(f'row{i}.q{j}: 解説に 正解は「… が無い')
            elif not cited_ok(ex, ch[a]):
                errs.append(f'row{i}.q{j}: 解説の正解テキストが choices[answer] と不一致\n      key={ch[a]!r}\n      ex={ex[:90]!r}')
            blob += ' ' + q['stem'] + ' ' + ex + ' ' + ' '.join(map(str, ch))
        for h in FIG_HINTS:
            if h in blob:
                warns.append(f'row{i}: 図依存ヒント "{h}" を検出(要確認)')

    print(f'rows: {len(rows)} | errors: {len(errs)} | warnings: {len(warns)}')
    for e in errs[:40]:
        print('  ERR', e)
    for w in warns[:20]:
        print('  warn', w)
    if errs:
        print('!! エラーのため書き出さず'); sys.exit(2)

    def dist_of(rs):
        dd = {}
        nn = 0
        for r in rs:
            for q in r['question_data']['questions']:
                dd[q['answer']] = dd.get(q['answer'], 0) + 1
                nn += 1
        return dd, nn

    before, _ = dist_of(rows)

    # ── 全四択問題を round-robin で正答位置に分散(知識四択・正誤組合せ・正誤判定・整序すべて)。
    #   解説は「正解は「<選択肢テキスト>」とテキスト参照ゆえ選択肢を入れ替えても整合(cited_okで再検証)。
    #   ただし解説に位置語(1つ目/選択肢N/①等)がある問は除外(シャッフルで陳腐化するため)。
    POS_REF = re.compile(r'[1-4１-４一二三四]つ目|最初の選択肢|最後の選択肢|選択肢[1-4１-４]|[①②③④]|[1-4]番目')

    def shuffleable(q):
        if POS_REF.search(q.get('explanation', '')):
            return False
        return len(q['choices']) == 4

    target = 0
    moved = 0
    for r in rows:
        for q in r['question_data']['questions']:
            if not shuffleable(q):
                continue
            a = q['answer']
            t = target % 4
            target += 1
            if a != t:
                ch = q['choices']
                ch[a], ch[t] = ch[t], ch[a]
                q['answer'] = t
                moved += 1
    # shuffle後の解説↔正答 整合を再検証(正解は「text」がテキスト参照なので安全だが念のため)
    post_err = 0
    for r in rows:
        for q in r['question_data']['questions']:
            if not cited_ok(q['explanation'] or '', q['choices'][q['answer']]):
                post_err += 1
    if post_err:
        print(f'!! shuffle後に解説↔正答 不整合 {post_err} 件'); sys.exit(3)
    after, n = dist_of(rows)
    print(f'=== 正答位置: 知識四択{moved}問を移動 | before {dict(sorted(before.items()))} -> after {dict(sorted(after.items()))} ===')
    dist = after
    by_era = {}
    for r in rows:
        e = r['question_data']['questions'][0]['unit']
        by_era[e] = by_era.get(e, 0) + 1
    json.dump({'questions': rows}, open(out, 'w'), ensure_ascii=False, indent=1)
    print(f'=== wrote {os.path.relpath(out)} ===')
    print(f'大問 {len(rows)} (時代別 {by_era}) | 小問 {n} | answer位置 {dict(sorted(dist.items()))}')


if __name__ == '__main__':
    main()
