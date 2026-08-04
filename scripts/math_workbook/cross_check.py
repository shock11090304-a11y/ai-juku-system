#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第1集と第2集の「実質重複」を機械検出する。

  python3 cross_check.py

verify.py の DUP 検出は同一ファイル内の stem 完全一致しか見ないため、
「文言を変えただけで、測る力も答えも同じ問題」が第1集↔第2集をまたいで
すり抜ける。ここでは診断マップ(スキル)と答えを突き合わせて洗い出す。

判定: (測定スキルが同じ) かつ (答えの表記が一致) → 要目視(数値替えが不十分の疑い)
"""
import re, sys
import diagnosis_kiso as D1
import diagnosis_kiso2 as D2
import content_kiso as C1
import content_kiso2 as C2
import build_kiso as K


def numbered(mod, offset):
    units = [u for p in mod.PARTS for u in p["units"]]
    K.reorder(units)
    return {f"{ui}-{q['no']}": q
            for ui, u in enumerate(units, 1 + offset) for q in u["problems"]}


def norm(s):
    """答えの表記ゆれ(空白・\, \ など)だけを吸収した正規化文字列。
    ★数字だけを抜き出す方式は n^{2}+1 と 2^{n}-1 を同一視してしまう(偽陽性)ので採らない。"""
    s = re.sub(r"\\[,;: ]", "", s or "")
    return re.sub(r"\s+", "", s)


def main():
    p1, p2 = numbered(C1, 0), numbered(C2, 12)
    hits = []
    for k2, q2 in p2.items():
        s2 = D2.MAP[k2]["skill"]
        a2 = norm(q2.get("answer", ""))
        if not a2:
            continue
        for k1, q1 in p1.items():
            if D1.MAP[k1]["skill"] != s2:
                continue
            if norm(q1.get("answer", "")) == a2:
                hits.append((k2, q2["stem"][:34], k1, q1["stem"][:34],
                             D1.SKILLS[s2], q2.get("answer", "")[:20]))
    print(f"第1集 {len(p1)}問 / 第2集 {len(p2)}問")
    if not hits:
        print("\n★ 同スキル×同答えのペアなし(数値替えは十分)")
        return 0
    print(f"\n-- 要目視: 同じスキルで答えの数値も一致 ({len(hits)}件) --")
    for k2, s2t, k1, s1t, sk, ans in hits:
        print(f"  第2集 {k2:>6} 「{s2t}…」")
        print(f"  第1集 {k1:>6} 「{s1t}…」")
        print(f"          スキル={sk} / 答え={ans}\n")
    print("※ 答えが同じでも設定が本質的に違えば問題なし(頻出値の偶然一致)。")
    print("※ 「名詞を差し替えただけ」なら数値を変えること。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
