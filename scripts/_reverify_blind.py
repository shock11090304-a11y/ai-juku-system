# -*- coding: utf-8 -*-
"""盲検証のあとに設問を並べ替え／文言修正した冊子で、**盲解答がまだ有効か**を確かめる。

  python3 _reverify_blind.py <content.py> <blindの元ファイル> <解答A> <解答B> <解答C> [--days]

★なぜ id で照合しないか
  設問を1問でも別の群へ移すと通し番号が全部ずれ、id 一致では「全問不一致」に見える。
  設問文そのもので突き合わせれば、並べ替えても盲検証の結果を引き継げる。

★★1プロセスで1冊だけ扱うこと（複数冊をまとめて読み込まない）
  各冊の content_no01.py はどれも `from _p1 import PART1` と書いている。
  同じプロセスで2冊目を読むと `_p1` が sys.modules に残っていて、
  **2冊目が1冊目のデータを掴む**（実際にこれで「物理が全56問不一致」という誤報が出た）。
"""
import argparse
import json
import re
import sys

from _make_blind import load
from _reconcile import key_of, parse_ans


_MARK = [(re.compile(r"\[\[sqrt:([^\]]+)\]\]"), r"√\1"),
         (re.compile(r"\[\[frac:([^|\]]+)\|([^\]]+)\]\]"), r"\1/\2")]
# ★字種を変えただけで紐付けが切れないように、記号は1つの形に寄せてから比べる。
#   実例: 数学の ＝ を = に統一した（教科書の組み方に合わせた）だけで、
#   盲検証の照合が 26 問ぶん外れて「検証していない問題」になっていた。
_SYM = str.maketrans({"＝": "=", "＋": "+", "－": "-", "−": "-", "×": "*", "÷": "/",
                      "＞": ">", "＜": "<", "／": "/", "，": ",", "、": ",", "。": ""})


def core(q):
    """設問の「中身」だけを残す。**注記や字種を変えただけで紐付けが切れる**のを防ぐ。

    実例1: 整序7問に「（文の最初にくる語も小文字で示してある）」を足したところ、
    語群も正解も変えていないのに 7問が「設問が変わった」扱いになり、検証の網から外れた。
    実例2: 数学の記号を教科書式（全角＝ → 半角=）にそろえたら 26 問が同じく外れた。
    括弧内の注記・空白・記号の字種は落として比べる（中身が変われば当然一致しなくなる）。
    """
    s = str(q)
    for pat, rep in _MARK:
        s = pat.sub(rep, s)
    # ★括弧を落とすのは「日本語の注記」だけ。数式の括弧 (x+2) まで消すと、
    #   組分数にした設問が「別の設問」に見えて紐付けが切れる。
    s = re.sub(r"[（(](?=[^）)]*[ぁ-んァ-ヶ一-龥])[^）)]{0,40}[）)]", "", s)
    # ★丸括弧も落とす。組分数にすると教科書どおり分子の括弧が消えるので
    #   「(x+2)/3」と「x+2 の組分数」が別の設問に見えてしまう。
    #   英文の空所も （　）と ( ) で字種が割れるが、括弧を落とせば同じになる。
    s = re.sub(r"[（）()]", "", s)
    return re.sub(r"[\s　]+", "", s).translate(_SYM)


def current_ids(C, days):
    cur = {}
    if days:
        for D in C.DAYS:
            for sec in D["sections"]:
                for i, q in enumerate(sec["qs"], 1):
                    cur[f'D{D["day"]}-{sec["subj"]}-{i}'] = q["q"]
    else:
        n = 1
        for g in C.PART1:
            for it in g["items"]:
                cur[f"P1-{n}"] = it["q"]
                n += 1
        for b in C.PART2:
            for i, q in enumerate(b["qs"], 1):
                cur[f'{b["no"]}-{i}'] = q["q"]
    return cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("blind")
    ap.add_argument("solutions", nargs=3)
    ap.add_argument("--days", action="store_true")
    a = ap.parse_args()

    C = load(a.content)
    K = key_of(C, a.days)
    cur = current_ids(C, a.days)
    by_text = {v: k for k, v in cur.items()}
    by_core = {core(v): k for k, v in cur.items()}
    qtext = {it["id"]: it["question"] for it in json.load(open(a.blind, encoding="utf-8"))["items"]}
    sols = [{str(x["id"]): x.get("answer", "") for x in json.load(open(p, encoding="utf-8"))}
            for p in a.solutions]

    moved = gone = ok = bad = 0
    details = []
    for oid, txt in qtext.items():
        nid = by_text.get(txt) or by_core.get(core(txt))
        if nid is None:
            gone += 1
            details.append(f"設問が変わった/消えた: {oid}「{txt[:34]}…」")
            continue
        if nid != oid:
            moved += 1
        if nid not in K:
            continue
        t, want = K[nid]
        got = [parse_ans(t, s.get(oid, "")) for s in sols]
        if all(g in want for g in got):
            ok += 1
        else:
            bad += 1
            details.append(f"{oid}→{nid} 鍵=「{'|'.join(sorted(want))}」 盲={got}")
    print(f"照合 {len(qtext)}問／番号が動いた {moved}問／設問が変わった {gone}問"
          "（注記の追加だけなら同一とみなす）")
    print(f"  盲解答が現行の鍵と一致: {ok}   不一致: {bad}")
    for x in details[:20]:
        print("   ", x)
    sys.exit(1 if (bad or gone) else 0)


if __name__ == "__main__":
    main()
