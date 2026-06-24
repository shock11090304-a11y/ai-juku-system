#!/usr/bin/env python3
"""共テ英語2026 類似問題: ワークフロー出力を検証→seed JSON を組み立てる。

使い方:
  python3 validate_and_build.py <b1_rows.json> <rest_output_file> [...more output files]

- b1_rows.json   : rows の配列 (パイロット出力を保存したもの)
- rest_output_file: ワークフローの task .output ファイル (wrapper {result:...})
両形式を自動判別して rows を吸い上げる。

検証:
  - 行スキーマ (exam_id/part_key/eiken_grade/model/question_data)
  - question_data (passage/subject/questions[])
  - 小問 (id/type/stem/choices>=4/answer 範囲内/unit/explanation)
  - explanation が「正解は「<choices[answer]>」。」で始まり、正答テキストと完全一致
  - HTMLエンティティ(&lt; 等)の残存
  - 図依存ヒューリスティック (graph/figure/picture 等の参照を警告)
  - 正答位置の偏り (plain 4択のみ round-robin で均し・解説はテキスト参照ゆえ shuffle安全)
  - content hash dedup
出力: seed-data/dojo_eng_kyotsu2026_manual.json  ({"questions":[...rows]})
"""
import json, re, sys, hashlib, html, os

CORRECT_RE = re.compile(r'^正解は「(.*?)」。', re.S)
# 鉤括弧欠落の良性スリップ用フォールバック (正解は X 。 の X が正答テキストと完全一致する時だけ補正)
LOOSE_RE = re.compile(r'^正解は\s*(.+?)\s*。(.*)$', re.S)
ENTITY_RE = re.compile(r'&(lt|gt|amp|quot|#\d+);')
FIGURE_HINTS = ['the graph above', 'the graph below', 'the picture', 'the figure', 'the diagram',
                'as shown in the image', 'see the chart', '下のグラフ', '右の図', '左の図', '上の図', 'の写真を見']

SEED_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'seed-data', 'dojo_eng_kyotsu2026_manual.json')


def extract_rows(path):
    raw = open(path).read()
    try:
        obj = json.loads(raw)
    except Exception as e:
        print(f'  ! {path}: not JSON ({e})'); return []
    # case A: already a list of rows
    if isinstance(obj, list):
        return obj
    # case B: wrapper {result: "<json str>"} or {rows:[...]}
    if isinstance(obj, dict):
        if 'rows' in obj and isinstance(obj['rows'], list):
            return obj['rows']
        res = obj.get('result')
        if isinstance(res, str):
            d = json.loads(res)
            if isinstance(d, str):
                d = json.loads(d)
            if isinstance(d, dict):
                return d.get('rows', [])
            if isinstance(d, list):
                return d
        if isinstance(res, dict):
            return res.get('rows', [])
    return []


def content_hash(qd):
    s = json.dumps(qd, ensure_ascii=False)
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def validate_row(row, errs, warns, ridx):
    ok = True
    for k in ('exam_id', 'part_key', 'eiken_grade', 'model', 'question_data'):
        if k not in row:
            errs.append(f'row{ridx}: missing {k}'); ok = False
    if not ok:
        return False
    if row['exam_id'] != 'daigaku':
        errs.append(f"row{ridx}: exam_id={row['exam_id']}"); ok = False
    if row['part_key'] not in ('r_short', 'r_long'):
        errs.append(f"row{ridx}: part_key={row['part_key']}"); ok = False
    if row['eiken_grade'] != 'kyotsu':
        errs.append(f"row{ridx}: eiken_grade={row['eiken_grade']}"); ok = False
    qd = row['question_data']
    if not isinstance(qd, dict):
        errs.append(f'row{ridx}: question_data not dict'); return False
    if not qd.get('passage'):
        errs.append(f'row{ridx}: empty passage'); ok = False
    if qd.get('subject') != '英語':
        warns.append(f"row{ridx}: subject={qd.get('subject')}")
    qs = qd.get('questions')
    if not isinstance(qs, list) or not qs:
        errs.append(f'row{ridx}: no questions'); return False
    blob = qd.get('passage', '')
    for j, q in enumerate(qs):
        for k in ('id', 'type', 'stem', 'choices', 'answer', 'unit', 'explanation'):
            if k not in q:
                errs.append(f'row{ridx}.q{j}: missing {k}'); ok = False
        if not ok:
            continue
        ch = q['choices']
        if not isinstance(ch, list) or len(ch) < 4:
            errs.append(f'row{ridx}.q{j}: choices<4'); ok = False; continue
        a = q['answer']
        if not isinstance(a, int) or a < 0 or a >= len(ch):
            errs.append(f'row{ridx}.q{j}: answer {a} out of range(0..{len(ch)-1})'); ok = False; continue
        expl = q['explanation'] or ''
        m = CORRECT_RE.match(expl)
        if not m:
            # 鉤括弧欠落の良性スリップを安全に補正 (X が正答テキストと完全一致する時だけ)
            lm = LOOSE_RE.match(expl)
            if lm and lm.group(1).strip() == str(ch[a]).strip():
                expl = f'正解は「{ch[a]}」。' + lm.group(2).lstrip()
                q['explanation'] = expl
                m = CORRECT_RE.match(expl)
                warns.append(f'row{ridx}.q{j}: 解説の鉤括弧を自動補正')
        if not m:
            errs.append(f'row{ridx}.q{j}: explanation 規約違反 (正解は「…」。で始まらない): {expl[:40]}'); ok = False
        else:
            cited = m.group(1).strip()
            if cited != str(ch[a]).strip():
                errs.append(f'row{ridx}.q{j}: 解説の正解テキスト != choices[answer]\n      cited={cited!r}\n      key  ={ch[a]!r}'); ok = False
        # entity scan
        scan = ' '.join([q['stem'], expl] + [str(c) for c in ch])
        if ENTITY_RE.search(scan):
            warns.append(f'row{ridx}.q{j}: HTMLエンティティ残存')
        blob += ' ' + scan
    if not qd.get('figure_svg'):  # 図(figure_svg)を持つ大問は図ヒントが出て当然なので警告しない
        low = blob.lower()
        for h in FIGURE_HINTS:
            if h.lower() in low:
                warns.append(f'row{ridx}: 図依存ヒント "{h}" を検出 (自己完結を要確認)')
    return ok


def is_plain4(q):
    """正答位置を均すために shuffle してよい "素直な4択" か。
    ラベル(<A>)/順序(→)/組合せ(と/and)選択肢は順序に意味があるので除外。"""
    ch = q['choices']
    if len(ch) != 4:
        return False
    for c in ch:
        s = str(c).strip()
        if re.match(r'^<[A-D]>$', s):
            return False
        if '→' in s or '➡' in s:
            return False
        if re.match(r'^(①|②|③|④|⑤|⑥|[A-D])\s*(と|and)\s*', s):
            return False
        if re.match(r'^[A-D]\s+and\s+[A-D]$', s):
            return False
        if len(s) < 6:  # 単独ラベル/短すぎる選択肢
            return False
    return True


def rebalance(rows):
    """plain4 の小問について、正答位置を 0,1,2,3 へ round-robin で均す。
    解説は正答テキストを引用(位置非参照)ゆえ choices を入れ替えても整合維持。"""
    target = 0
    moved = 0
    for row in rows:
        for q in row['question_data']['questions']:
            if not is_plain4(q):
                continue
            a = q['answer']
            t = target % 4
            target += 1
            if a != t:
                ch = q['choices']
                ch[a], ch[t] = ch[t], ch[a]
                q['answer'] = t
                moved += 1
    return moved


def dist(rows, part):
    d = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    n = 0
    for row in rows:
        if row['part_key'] != part:
            continue
        for q in row['question_data']['questions']:
            d[q['answer']] = d.get(q['answer'], 0) + 1
            n += 1
    return d, n


def main():
    args = sys.argv[1:]
    out_path = SEED_PATH
    paths = []
    for a in args:
        if a.startswith('--out='):
            out_path = a[len('--out='):]
        else:
            paths.append(a)
    if not paths:
        print('usage: validate_and_build.py [--out=PATH] <file> [file...]'); sys.exit(1)
    rows = []
    for p in paths:
        r = extract_rows(p)
        print(f'  loaded {len(r)} rows from {os.path.basename(p)}')
        rows.extend(r)
    print(f'total raw rows: {len(rows)}')

    errs, warns = [], []
    valid = []
    seen = set()
    for i, row in enumerate(rows):
        if validate_row(row, errs, warns, i):
            h = content_hash(row['question_data'])
            if h in seen:
                warns.append(f'row{i}: 重複(content hash) skip')
                continue
            seen.add(h)
            valid.append(row)

    print(f'\n=== validation ===')
    print(f'valid rows: {len(valid)} / {len(rows)}')
    print(f'errors: {len(errs)}')
    for e in errs[:60]:
        print('  ERR', e)
    print(f'warnings: {len(warns)}')
    for w in warns[:40]:
        print('  warn', w)

    if errs:
        print('\n!! エラーがあるため seed を書き出しません。修正後に再実行してください。')
        sys.exit(2)

    # rebalance answer positions
    before = {}
    for part in ('r_short', 'r_long'):
        before[part] = dist(valid, part)
    moved = rebalance(valid)
    print(f'\n=== answer 位置リバランス: {moved} 問を移動 (plain4のみ) ===')
    for part in ('r_short', 'r_long'):
        d0, n0 = before[part]
        d1, n1 = dist(valid, part)
        print(f'  {part}: before {dict((k,v) for k,v in d0.items() if v)} -> after {dict((k,v) for k,v in d1.items() if v)} (n={n1})')

    # re-validate explanation<->answer after shuffle (safety)
    errs2 = []
    for i, row in enumerate(valid):
        for j, q in enumerate(row['question_data']['questions']):
            m = CORRECT_RE.match(q['explanation'])
            if m and m.group(1).strip() != str(q['choices'][q['answer']]).strip():
                errs2.append(f'row{i}.q{j}: post-shuffle mismatch')
    if errs2:
        print('!! shuffle後に不整合', errs2[:10]); sys.exit(3)
    print('  shuffle後の解説<->正答 整合: OK')

    total_subq = sum(len(r['question_data']['questions']) for r in valid)
    by_part = {}
    by_fmt = {}
    for r in valid:
        by_part[r['part_key']] = by_part.get(r['part_key'], 0) + 1
        f = r['question_data'].get('format_type', '?')
        by_fmt[f] = by_fmt.get(f, 0) + 1

    out = {'questions': valid}
    with open(out_path, 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f'\n=== wrote {os.path.relpath(out_path)} ===')
    print(f'大問: {len(valid)} (by part {by_part}) (by format {by_fmt})')
    print(f'小問: {total_subq}')


if __name__ == '__main__':
    main()
