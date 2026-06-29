#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""決定的な最終正規化:
(1) order問題: 先頭(文頭)に来るトークンを answer_text の先頭部分に合わせて大文字化(全order問で統一・一意性強化)。
(2) mc問題: 正解位置(answer_index)の偏りを是正するため選択肢を決定的にシャッフルし、
    answer_index 分布をほぼ一様(0/1/2/3)にする。解説は全問「値」参照なので安全。
両方とも answer_text(正解の値)は不変。
"""
import json, glob, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "units")

def fix_leading_caps(units):
    changed = 0
    warn = []
    for slug, d in units:
        for q in d["questions"]:
            if q["type"] != "order":
                continue
            ans = q["answer_text"]; toks = q.get("tokens", [])
            cands = [i for i, t in enumerate(toks) if ans.lower().startswith(t.lower())]
            if not cands:
                warn.append(f"{slug}#{q['no']}: no leading token matches answer start")
                continue
            i = max(cands, key=lambda k: len(toks[k]))
            newtok = ans[:len(toks[i])]
            if newtok != toks[i]:
                toks[i] = newtok
                changed += 1
            # 健全性: 先頭以外で文頭化し得る大文字トークン(固有名詞/Iを除く)が無いか軽くチェック
    return changed, warn

PROPER = {"I"}
def rebalance_mc(units):
    mc = []
    for slug, d in units:
        for q in d["questions"]:
            if q["type"] == "mc":
                mc.append((slug, q))
    # 決定的スクランブル順(stemのmd5)で並べ、rank%4 を target に
    mc.sort(key=lambda sq: hashlib.md5(sq[1]["stem"].encode("utf-8")).hexdigest())
    dist = [0, 0, 0, 0]
    for rank, (slug, q) in enumerate(mc):
        target = rank % 4
        ai = q["answer_index"]; ch = q["choices"]
        correct = ch[ai]
        distractors = [c for j, c in enumerate(ch) if j != ai]
        newch = distractors[:]
        newch.insert(target, correct)
        assert len(newch) == 4 and newch[target] == correct == q["answer_text"], f"rebalance fail {slug}#{q['no']}"
        q["choices"] = newch
        q["answer_index"] = target
        dist[target] += 1
    return dist

def main():
    units = []
    for f in sorted(glob.glob(os.path.join(SRC, "*.json"))):
        units.append((os.path.basename(f)[:-5], json.load(open(f, encoding="utf-8"))))
    changed, warn = fix_leading_caps(units)
    dist = rebalance_mc(units)
    for slug, d in units:
        json.dump(d, open(os.path.join(SRC, f"{slug}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    print("order leading-cap changed:", changed)
    if warn:
        print("WARN:", *warn, sep="\n  ")
    print("mc answer_index dist after rebalance [0,1,2,3]:", dist, "sum", sum(dist))

if __name__ == "__main__":
    main()
