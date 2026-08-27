#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診断: 文型の宣言が主節の V を全部拾えているか（★ゲートではない・手で回す）

  python3 scripts/eng_svoc_kaisetsu/diag_pattern_count.py

「第3文型（SVO）×2」と書いたのに主節の V が 3 つある、といった<b>数え落とし</b>を洗い出す。
2026-08-27 にこれで実際に 3 件見つけた（慶應 ¶1-1 / 東大 ¶14-2 / 東大 ¶21-3）。

★なぜ check.py のゲートに入れないか
  正当な不一致が構造的に出るため。ゲートにすると例外表を持つことになり、
  「例外に足して黙らせる」運用になって検査が死ぬ。
    - 強調構文（It is 〜 that …）は主節の V が 2 つ見えるが、元の文は 1 つ。
    - 引用文が前に出た形（"…," she said）は引用文の V も主節の高さにある。
    - 従属節の文型を添えた宣言（「〜節の中は第2文型」）はその V が主節に無い。
  よって<b>出力を人が読んで判断する道具</b>として置く。ファイル名が check*/verify* に
  当たらないので run_all_gates.py は拾わない（＝ゲートを自称しない）。
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core

# 「〜節の中は」「〜節は」で始まる区切りは従属節の話なので主節の勘定から外す
SUB = re.compile(r"節の中は|節は")
PAT = re.compile(r"第[1-5]文型（[^）]*）\s*(?:×\s*(\d+))?")


def main():
    bad = 0
    for key, name in (("content_keio2018", "慶應"), ("content_todai2018", "東大")):
        mod = __import__(key)
        for para in mod.PARAS:
            for j, s in enumerate(para["sents"], 1):
                declared = 0
                for seg in s["pat"].split("／"):
                    if SUB.search(seg):
                        continue
                    for m in PAT.finditer(seg):
                        declared += int(m.group(1) or 1)
                if declared == 0:
                    continue
                node = core.parse(s["dsl"])
                topv = sum(1 for k in node.kids if k.label == "V")
                if topv != declared:
                    bad += 1
                    print(f"  {name} ¶{para['no']}-{j}: 主節の V が {topv} 個 / 宣言は {declared} 個")
                    print(f"      {s['pat']}")
                    print(f"      {core.plain_text(node)[:96]}")
    print(f"\n要確認 {bad} 件（0 でなくてよい。上の『正当な不一致』に当たるかを目で見て判断する）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
