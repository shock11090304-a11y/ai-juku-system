#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大学ミラー教材の「その肢を否定しているか」判定（青学・同志社・関学・明治で共有）。

★このモジュールが要る理由（2026-08-05 に実測で分かったこと）
  「正解バッジと同じカードで、その正解を誤答として解説している」を捕まえる判定を
  各ゲートが独自に書いた結果、次の2つを同時に踏んだ:

  1. **変異テストの語彙にだけ合わせて、実文体では捕まらない**
     関学に「〜は不可」という定型で変異を当てると 40/40 検出できたが、
     この教材の著者が実際に書く否定文（真逆／矛盾／と逆／文脈違い／ずれ …）に替えると
     **4/40 まで落ちた**。窓を「24文字」で切っていたため、「不可」が25文字目に来る
     実在の書き方にも届かなかった。
  2. **正当な対比言及を落とす**（「②は④と紛らわしいが本文にない」等）。
     肯定語の白リストが決め打ちで、列挙に無い自然な書き方はすべて誤検出になった（10/10）。

  → 窓を「N文字」でなく **その語を含む一文**にし、否定語は**実データから機械で拾った語彙**を使う。
    肯定的な対比（「④が正解に近い」「⑤が最適」）は否定ではないので除く。
"""
import re

# 実データ（青学・同志社・関学の explanations_seki.json）から出現数を数えて拾った否定語彙。
# 上位: ずれ16 / 合わない14 / と逆11 / ならない10 / 矛盾8 / 真逆7 / 不可7 / 誤り5 …
NEG_WORDS = ("不可", "誤り", "ならない", "なれない", "成り立たない", "使えない", "合わない",
             "できない", "不適", "は違う", "真逆", "矛盾", "と逆", "も逆", "主客が逆",
             "文脈違い", "意味不明", "持たない", "入らない", "続かない", "噛み合わない",
             "別熟語", "穴がない", "ずれ", "ズレ", "浮く", "崩れる", "消える", "×")

# 「その肢を正解として扱っている」言い回し。否定ではないので落とさない。
POS_WORDS = ("が正解", "（正解）", "(正解)", "＝正解", "が最適", "が最も", "で確定",
             "が正しい", "を選ぶ", "が答え", "に近い")

_SPLIT = re.compile(r"[。\n]")


def sentences(text):
    """。や改行で区切った一文の一覧。"""
    out, start = [], 0
    for m in _SPLIT.finditer(text):
        out.append(text[start:m.end()])
        start = m.end()
    if start < len(text):
        out.append(text[start:])
    return out


def negates(text, needle, word_boundary=False):
    """text の中で needle を **否定している一文があるか**。

    word_boundary=True は英単語を探すとき（`on` が `on the` の一部に当たるのを防ぐ）。
    肯定的な言及しか無いなら False（正当な対比を落とさない）。
    """
    pat = ((r"(?<![A-Za-z])" + re.escape(needle) + r"(?![A-Za-z])")
           if word_boundary else re.escape(needle))
    for sent in sentences(text):
        m = re.search(pat, sent)
        if not m:
            continue
        # ★「その一文が誰を否定しているか」は**文頭に置かれた肢**で決まる。
        #   位置を見ないと、別の肢を否定する説明の中の言及を拾う。実例:
        #   「when は It was ... that の強調構文の枠に入らない。」
        #   → 否定されているのは when で、that は説明の一部（実データで誤検出した）。
        head = sent.lstrip("、,。 　\n")
        if not re.match(r"^\W{0,3}" + pat, head):
            continue
        if any(p in sent for p in POS_WORDS):
            continue
        if any(n in sent for n in NEG_WORDS):
            return True
    return False
