# -*- coding: utf-8 -*-
"""準1級の語彙リスト (塾の既存教材から集める) と、語形のゆるい照合。

check.py (外部ライブラリなし・CI で回る) と gloss_scan.py (手元で語注の候補を洗い出す) が共有する。

■ 準1級の語 = 次の2つの和集合 (2026-09-30 時点で 644 語・句)
  - scripts/eiken_tango_test/content.py の TESTS (準1級 単語テスト 400 語)
  - seed-data/eiken_vocab_pool_v1.json の unit に「準1級」を含む問題の正解語 (270 問)
  ★ここに載っている語は「準1級で覚える語」として扱い、語注を付けない (本番の英検も級の範囲内の語には注を付けない)。
"""
import importlib.util
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TANGO = os.path.join(HERE, "..", "..", "eiken_tango_test", "content.py")
POOL = os.path.join(HERE, "..", "..", "..", "seed-data", "eiken_vocab_pool_v1.json")

TOK = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")


def load_pre1():
    words = set()
    spec = importlib.util.spec_from_file_location("tango_content", TANGO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for t in mod.TESTS:
        for it in t["items"]:
            words.add(it[0].lower().strip())
    pool = json.load(open(POOL, encoding="utf-8"))
    for q in pool["questions"]:
        if "準1級" in q.get("unit", ""):
            a = q["choices"][q["answer"]] if isinstance(q["answer"], int) else q["answer"]
            words.add(str(a).lower().strip())
    return words


def forms(w):
    """語形の候補 (外部ライブラリなしの簡易版: 複数形・過去形・進行形・比較・派生の一部)。"""
    w = w.lower()
    c = {w}
    for suf, rep in (("ies", "y"), ("es", ""), ("s", ""), ("ied", "y"), ("ed", ""), ("ed", "e"),
                     ("d", ""), ("ing", ""), ("ing", "e"), ("ly", ""), ("ion", "e"), ("ion", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            c.add(w[: -len(suf)] + rep)
    return c


def _phrase_re(p):
    first, rest = p.split(" ", 1)
    stem = first[:-1] if first.endswith("e") else first
    return re.compile(r"\b" + re.escape(stem) + r"[a-z]*\s+" + re.escape(rest).replace(r"\ ", r"\s+") + r"\b", re.I)


def pre1_in(text, pre1):
    """text に出てくる準1級の語・句 (見出しの形で返す)。"""
    single = {w for w in pre1 if " " not in w}
    found = set()
    for t in TOK.findall(text):
        found |= forms(t) & single
    for p in (w for w in pre1 if " " in w):
        if _phrase_re(p).search(text):
            found.add(p)
    return sorted(found)
