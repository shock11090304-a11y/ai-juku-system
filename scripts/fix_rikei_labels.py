#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""理系解説のうち「段階ラベルが無く 1 行に詰まった 202 問」に段階ラベルを付ける。

scripts/fix_explanation_linebreaks.py は「ラベルはあるが改行が無い」問を直した。
残ったのがこの 202 問で、ラベルそのものが無いため改行位置を決められず、当時は
手を付けなかった。

【なぜ直してよいと判断したか】
5 プールで signature を実測したところ、「単元のみ」= ラベル無しの件数と
「3 行未満」の件数が完全に一致した:

    math_unit    ラベル無し 104 / 3行未満 104   (プール 302 問・他 198 問はラベル有り)
    phys_basic   ラベル無し  40 / 3行未満  40   (プール 251 問)
    math_1a      ラベル無し  19 / 3行未満  19   (プール 201 問)
    math_2b      ラベル無し  20 / 3行未満  20   (プール 246 問)
    math3c_unit  ラベル無し  19 / 3行未満  19   (プール 149 問)

つまりこれは「別の流儀」ではなく、同じプールの多数派から取りこぼされた群。
CLAUDE.md の「迷ったら同じプールの既存 seed に合わせる」に照らして、
ラベルを付ける方向が正しい。

【安全性: 数式に触れない】
挿入するのは **改行とラベル文字列だけ**。本文の文字は 1 つも作らない・消さない。
適用後、挿入したラベルと空白を取り除くと元の文字列に戻ることを 1 問ずつ確認し、
戻らなければその問題は書き換えない (fix_explanation_linebreaks.py と同じ方式)。

【段階の切り方: 手掛かり語がある所だけ】
実測した手掛かり語の出現数 (母数 202):
    【単元】202 / よって 121 / 誤答 59 / 立式すると 22 / 求める 11 / 検算 7 …
確信を持って言える境界だけで切る。手掛かりが無い文は直前の段階に残す
(無理に 立式 と 計算 を分けると、当てずっぽうのラベルが付く)。
phys_basic の既存ラベル付き解説も「考え方」行に複数文を置いており、
この置き方はプールの慣行に沿う。

ラベルの書式 (コロン後の空白数) はプールごとに違うので、
**そのプールの既存ラベル付き解説から実測**して合わせる。

実行: python3 scripts/fix_rikei_labels.py [--apply]
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
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from seed_survey import family                      # noqa: E402

# 段階の手掛かり語。文頭に来たときだけ境界とみなす。
ANSWER_CUE = re.compile(r'^(よって|したがって|ゆえに|以上より|求める答えは|答えは)')
KEISAN_CUE = re.compile(r'^(計算すると|計算して|整理すると|通分して|代入すると)')
RITSU_CUE = re.compile(r'^(立式すると|立式は|式を立てると)')
NOTE_CUE = re.compile(r'^(誤答|誤選択肢|選択肢|検算|注意|なお|参考)')
# 文頭に手掛かりが無く、文中で「…で正解は2番。」と答えを述べる書き方が 12 問ある。
# 文頭の手掛かりが見つからなかったときの予備として使う。
ANSWER_INLINE = re.compile(r'正解は')
# 手掛かり語をまったく持たず「240は…の誤り。160は…との混同。」と
# 誤答の解説だけが末尾に並ぶ書き方が 29 問ある。誤答の解説は必ず文末側に
# かたまるので、「末尾から連続してこの語を含む文」を誤答ブロックとみなす。
# 途中の 1 文だけを拾うと本文の途中で切ってしまうので、必ず**末尾から連続**で判定する。
# 「誤り/誤った/誤解/誤読」など活用形が揺れるので「誤」1 字で拾う。
# 単独の文を拾うのではなく末尾からの連続で判定するため、本文側を誤って
# 巻き込む危険は小さい (途中に非該当文が 1 つでもあればそこで止まる)。
WRONG_MARK = re.compile(r'(誤|ミス|混同|取り違え|勘違い|早合点|見落と)')

LABELS = ('考え方', '立式', '計算', '答え', '誤答の根拠', '補足')


def detect_format(raw, data):
    for ind, sep, tail in itertools.product([0, 1, 2, 3, 4, None],
                                            [None, (',', ': ')], ['', '\n']):
        try:
            if json.dumps(data, ensure_ascii=False, indent=ind, separators=sep) + tail == raw:
                return ind, sep, tail
        except TypeError:
            continue
    return None


def split_sentences(text):
    """「。」で切って句点を残す。LaTeX 中の「。」は無いので単純分割でよい。"""
    out, buf = [], ''
    for ch in text:
        buf += ch
        if ch == '。':
            out.append(buf)
            buf = ''
    if buf.strip():
        out.append(buf)
    return out


def pool_gap(rows_by_pool, pkey):
    """そのプールの既存ラベル付き解説から、コロン後の空白数を実測する。"""
    gaps = collections.Counter()
    for exp in rows_by_pool.get(pkey, ()):
        for m in re.finditer(r'(?:%s)\s*[:：]( *)' % '|'.join(LABELS), exp):
            gaps[len(m.group(1))] += 1
    return gaps.most_common(1)[0][0] if gaps else 1


def relabel(exp, gap):
    """段階ラベルを挿入する。切れなければ None。"""
    if len([l for l in exp.splitlines() if l.strip()]) >= 3:
        return None                       # すでに段組みされている
    if re.search(r'(?:%s)\s*[:：]' % '|'.join(LABELS), exp):
        return None                       # ラベルがある = 別のスクリプトの担当
    # 単元見出しは 2 通りある (実測: 「。」で終わる 156 問 / 「)」で終わる 46 問)。
    #   【単元】整数(約数と倍数)。素因数分解して…
    #   【単元】集合と命題(集合と要素) まず \(A\cup B…
    # 括弧閉じまでを見出しとし、直後の「。」があれば含める。
    m = re.match(r'(【単元】[^\n。]*?[)）]。?)', exp)
    if not m:
        return None                       # 【単元】で始まらないものは触らない
    head, rest = m.group(1), exp[m.end():]
    sents = split_sentences(rest)
    if len(sents) < 2:
        return None

    sep = ':' + ' ' * gap
    # 文頭に答えの手掛かりが無いときだけ、「…で正解は2番。」の文を答えとみなす。
    inline_answer = None
    if not any(ANSWER_CUE.match(x.lstrip()) for x in sents):
        for x in sents:
            if ANSWER_INLINE.search(x):
                inline_answer = x
                break

    # 明示の手掛かりが無い場合の予備: 末尾から連続する「誤答の解説」文を切り出す。
    tail_from = len(sents)
    if not any(NOTE_CUE.match(x.lstrip()) for x in sents):
        i = len(sents)
        while i > 1 and WRONG_MARK.search(sents[i - 1]):
            i -= 1
        if i < len(sents):
            tail_from = i

    # 手掛かり語のある文だけを境界にする。無い文は直前の段階に付ける。
    blocks, cur_label, cur = [], '考え方', []
    for si, s in enumerate(sents):
        t = s.lstrip()
        nxt = None
        if si == tail_from:
            nxt = '誤答の根拠'
        elif RITSU_CUE.match(t):
            nxt = '立式'
        elif KEISAN_CUE.match(t):
            nxt = '計算'
        elif ANSWER_CUE.match(t):
            nxt = '答え'
        elif s is inline_answer:
            nxt = '答え'
        elif NOTE_CUE.match(t):
            nxt = '誤答の根拠' if t.startswith(('誤答', '誤選択肢', '選択肢')) else '補足'
        # 同じラベルが 2 度出るときは切らない (「よって」が計算途中に出る等)
        if nxt and nxt != cur_label and not any(b[0] == nxt for b in blocks):
            if cur:
                blocks.append((cur_label, cur))
            cur_label, cur = nxt, [s]
        else:
            cur.append(s)
    if cur:
        blocks.append((cur_label, cur))

    if len(blocks) < 2:
        return None                       # 段階が 1 つしか立たない = 切る根拠が無い
    out = head + '\n' + '\n'.join(
        f'{lab}{sep}{"".join(ss).strip()}' for lab, ss in blocks)

    # ★ 検証: 挿入したラベルと空白を取り除くと元に戻るか
    back = out
    for lab in LABELS:
        back = back.replace(f'\n{lab}{sep}', '')
    if re.sub(r'\s+', '', back) != re.sub(r'\s+', '', exp):
        return None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    # 先に各プールの既存ラベル付き解説を集める (書式の実測用)
    labeled = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(ROOT, 'seed-data', '*.json'))):
        try:
            data = json.loads(open(path, encoding='utf-8').read())
        except Exception:
            continue
        rows = data.get('questions') if isinstance(data, dict) else None
        if not isinstance(rows, list):
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            qd = r.get('question_data') or {}
            if isinstance(qd, str):
                try:
                    qd = json.loads(qd)
                except Exception:
                    continue
            for q in qd.get('questions') or []:
                e = q.get('explanation') or ''
                if re.search(r'(?:%s)\s*[:：]' % '|'.join(LABELS), e):
                    labeled[r.get('part_key')].append(e)

    total, changed, skipped = 0, 0, collections.Counter()
    per_file = collections.Counter()
    for path in sorted(glob.glob(os.path.join(ROOT, 'seed-data', '*.json'))):
        try:
            raw = open(path, encoding='utf-8').read()
            data = json.loads(raw)
        except Exception:
            continue
        rows = data.get('questions') if isinstance(data, dict) else None
        if not isinstance(rows, list):
            continue
        fmt = detect_format(raw, data)
        touched = False
        for r in rows:
            if not isinstance(r, dict):
                continue
            if family(r.get('exam_id'), r.get('part_key')) != 'rikei':
                continue
            qd = r.get('question_data')
            if isinstance(qd, str):
                continue                  # 文字列の question_data は対象外
            if not isinstance(qd, dict):
                continue
            gap = pool_gap(labeled, r.get('part_key'))
            for q in qd.get('questions') or []:
                e = q.get('explanation') or ''
                if not e.strip() or len([l for l in e.splitlines() if l.strip()]) >= 3:
                    continue
                total += 1
                out = relabel(e, gap)
                if out is None:
                    skipped[os.path.basename(path)] += 1
                    continue
                q['explanation'] = out
                changed += 1
                per_file[os.path.basename(path)] += 1
                touched = True
        if touched and args.apply:
            if fmt is None:
                print(f'❌ {os.path.basename(path)}: 整形を再現できないので書き込まない')
                continue
            ind, sepj, tail = fmt
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=ind,
                                   separators=sepj) + tail)

    print(f'対象 (理系・3行未満): {total} 問')
    print(f'ラベルを付けた       : {changed} 問')
    for fn, n in per_file.most_common():
        print(f'    {n:4d}  {fn}')
    if skipped:
        print(f'触らなかった         : {sum(skipped.values())} 問 (切る根拠が無い/復元できない)')
        for fn, n in skipped.most_common():
            print(f'    {n:4d}  {fn}')
    print('   (--apply で書き込み)' if not args.apply else '   → 書き込み済み')
    return 0


if __name__ == '__main__':
    sys.exit(main())
