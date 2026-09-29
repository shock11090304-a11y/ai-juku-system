# -*- coding: utf-8 -*-
"""中学ドリルのシードから「各部分でいちばん多く出る値を拾うと正解になる」選択肢を探す (読むだけ・ゲートではない)。

誤答がどれも正解の一部だけを入れ替えたもの (例: 正解「20 N の力で 1.0 m 引く」に対して「20 N の力で 0.5 m 引く」
「40 N の力で 1.0 m 引く」「20 N の力で 0.25 m 引く」) だと、力は 20 N・距離は 1.0 m が多数派なので本文を読まずに当たる。
正解を基準に誤答との差分 (数と英単語はひとまとまり・ほかは1文字ずつ) を取り、差分の場所が2つ以上あって、
どの場所でも正解の値が単独でいちばん多いものを出す。直し方は 2×2 (各要素の値がちょうど2回ずつ出る組み合わせ)。
比較のため、誤答を仮の正解にしたときに同じ形になる数も出す (偶然の水準。正解側がこれより多ければ手がかりになっている)。

★拾いすぎるもの (直さなくてよい): 同じ語が2か所に出る 2×2 (「ア 尊敬語　イ 謙譲語」「Xは誤り・Yは正しい」など)・
  確率などの分数1つの答え (分子と分母を別々に数えてしまう)。拾い漏らすもの: 言い回しの違う文 (差分が細かく割れる)。
使い方: python3 scripts/scan_choice_convergence.py [シードの JSON ...]   (引数なしは中学ドリル5教科)
"""
import collections
import difflib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = ["chugaku_drill_pool_v1.json", "chugaku_math_pool_v1.json", "chugaku_rika_pool_v1.json",
           "chugaku_shakai_pool_v1.json", "chugaku_kokugo_pool_v1.json"]
TOK = re.compile(r"[0-9０-９]+(?:[.．][0-9０-９]+)?|[A-Za-z]+|.", re.S)


def _diff_places(key, others):
    """正解の語の並びの上で、誤答との差分の場所をまとめる (重なる・接する差分は1つの場所)"""
    spans, ops = [], []
    for d in others:
        o = difflib.SequenceMatcher(None, key, d, autojunk=False).get_opcodes()
        ops.append(o)
        spans += [(i1, i2) for tag, i1, i2, _, _ in o if tag != "equal"]
    places = []
    for a, b in sorted(spans):
        if places and a <= places[-1][1]:
            places[-1][1] = max(places[-1][1], b)
        else:
            places.append([a, b])
    return places, ops


def _value_at(ops, d, c1, c2):
    """誤答 d のうち、正解の [c1, c2) にあたる部分"""
    got = []
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            lo, hi = max(i1, c1), min(i2, c2)
            if lo < hi:
                got += d[j1 + lo - i1: j1 + hi - i1]
        elif (i1 < c2 and c1 < i2) or (i1 == i2 and c1 <= i1 <= c2) or (c1 == c2 and i1 <= c1 <= i2):
            got += d[j1:j2]
    return tuple(got)


def converges(choices, c):
    """choices[c] を正解としたとき、差分の場所が2つ以上あり、どの場所でも正解の値が単独の最多か"""
    toks = [TOK.findall(x) for x in choices]
    key = toks[c]
    others = [t for i, t in enumerate(toks) if i != c]
    places, ops = _diff_places(key, others)
    if len(places) < 2:
        return False
    for c1, c2 in places:
        vals = [tuple(key[c1:c2])] + [_value_at(o, d, c1, c2) for o, d in zip(ops, others)]
        top = collections.Counter(vals).most_common()
        if top[0][0] != vals[0] or (len(top) > 1 and top[1][1] == top[0][1]):
            return False
    return True


def main():
    paths = sys.argv[1:] or [os.path.join(ROOT, "seed-data", f) for f in DEFAULT]
    for p in paths:
        qs = json.load(open(p, encoding="utf-8"))["questions"]
        hits, chance = [], 0
        for i, q in enumerate(qs):
            ch = q["choices"]
            if len(set(ch)) < 4:
                continue
            if converges(ch, q["answer"]):
                hits.append(i)
            chance += sum(converges(ch, j) for j in range(len(ch)) if j != q["answer"])
        print(f"{os.path.basename(p)}: {len(qs)}問  正解が中心 {len(hits)}問 / 偶然の水準 {chance / 3:.1f}問")
        for i in hits:
            q = qs[i]
            print(f"   #{i} [{q['unit']}] " + " / ".join(("★" if k == q["answer"] else "") + c for k, c in enumerate(q["choices"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
