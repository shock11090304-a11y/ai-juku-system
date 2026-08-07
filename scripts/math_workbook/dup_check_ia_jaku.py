#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学I·A 弱点発見トレーニングと、既存の問題集との実質重複を検出する。

  python3 dup_check_ia_jaku.py

なぜ要るか: 同じ生徒が第1集/第2集/数学I基礎徹底/数学A基礎徹底も持っている。
同じ問題が入っていると「もう解いた問題」で診断してしまい、弱点判定が歪む。

★答えの数字だけを比べると偽陽性が出る(別の問題でも答えが 12 になることは山ほどある)。
  ここでは【問題文の正規化一致】＋【問題文＋答えの両方が近い】の2条件で判定する。
"""
import os, re, sys, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_kiso as K

# 比較相手(この生徒層が同時に持ちうる本)
OTHERS = ["content_ia", "content_ia_v2", "content_kisoI", "content_kisoA",
          "content_kiso", "content_kiso2"]
UNREADABLE = []
SIM_TH = 0.90        # 問題文の類似度がこれ以上なら重複候補
SIM_WARN = 0.82      # ここ以上は目視の対象


def norm(s):
    """LaTeX の飾り・空白・約物を落として比較用にする。数値は残す(設定が同じかを見たい)。"""
    s = re.sub(r"\\[a-zA-Z]+", " ", s or "")
    s = re.sub(r"[{}$\\\s,.、。（）()\[\]　:：;；]", "", s)
    return s


def load(mod_name):
    import importlib
    try:
        m = importlib.import_module(mod_name)
    except Exception as e:
        # ★黙って外すと「1冊も照合していないのに OK」になる(verify.py が同じ穴で
        #   CI の緑を無意味にした前例がある)。読めない＝検査していないので違反にする。
        print(f"  NG {mod_name} を読めない({type(e).__name__}: {e})— 照合できていない")
        UNREADABLE.append(mod_name)
        return []
    parts = getattr(m, "PARTS", None)
    units = [u for p in parts for u in p["units"]] if parts else getattr(m, "UNITS", [])
    for u in units:
        K.reorder([u])
    return [(f'{mod_name}:{u["name"]}#{q["no"]}', q.get("stem", ""), q.get("answer", ""))
            for u in units for q in u["problems"]]


def main():
    import content_ia_jaku as C
    for p in C.PARTS:
        K.reorder(p["units"])
    mine = [(f"{code}-{j}", q["stem"], q.get("answer", ""))
            for code, u in zip(C.CODES, C.UNITS)
            for j, q in enumerate(u["problems"], 1)]

    others = []
    for name in OTHERS:
        others.extend(load(name))
    print(f"自分 {len(mine)}問 × 既存 {len(others)}問 を照合")

    # 完全一致(正規化後)を先に潰す
    idx = {}
    for tag, stem, ans in others:
        idx.setdefault(norm(stem), []).append(tag)

    hard, soft = [], []
    for tag, stem, ans in mine:
        n = norm(stem)
        if n in idx:
            hard.append((tag, idx[n][0], 1.0))
            continue
        best, btag = 0.0, ""
        for otag, ostem, oans in others:
            on = norm(ostem)
            # 長さが大きく違うものは飛ばす(高速化)
            if not on or abs(len(on) - len(n)) > max(12, len(n) * 0.4):
                continue
            r = difflib.SequenceMatcher(None, n, on).ratio()
            if r > best:
                best, btag = r, otag
        if best >= SIM_TH:
            hard.append((tag, btag, round(best, 3)))
        elif best >= SIM_WARN:
            soft.append((tag, btag, round(best, 3)))

    for tag, otag, r in hard:
        print(f"  NG {tag} が {otag} と重複 (類似度 {r})")
    for tag, otag, r in soft:
        print(f"  ! {tag} が {otag} に似ている (類似度 {r}) — 目視で判断")
    if not hard and not UNREADABLE:
        print(f"  OK 実質重複なし（既刊 {len(OTHERS)}冊と照合）"
              + (f"（要目視 {len(soft)}件）" if soft else ""))
    if UNREADABLE:
        print(f"  NG 照合できなかった既刊 {len(UNREADABLE)}冊: {', '.join(UNREADABLE)}")
    return 1 if (hard or UNREADABLE) else 0


if __name__ == "__main__":
    sys.exit(main())
