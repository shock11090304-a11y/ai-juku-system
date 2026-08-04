#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ルール発見ドリル No.03(識別・省略編)の解答キー(ANNOT)を機械検査するゲート。

  python3 check.py

検査:
  A. 転記 — ANNOT の各 t が指定文 s に「そのまま」存在するか。
  B. 位置ごとの網羅 — 識別語(that/those/it/as/so/such/too/enough)と相関接続の
     **各出現位置**が、対応カテゴリの ANNOT スパン(または IGNORE)に包含されるか。
     一つでも未分類の that/it/as が残れば FAIL(識別ドリルの欠陥)。
     ※省略(ell)・plain な and/but/or の並列(par)は意味判断のため位置走査せず、A＋敵対検証で担保。
  C. IGNORE 実在チェック。
すべて PASS で exit 0。build.py はこのゲート通過を前提とする。
"""
import re, sys
import content as C


def sentences(pkey):
    p = next(p for p in C.PASSAGES if p["key"] == pkey)
    return {s["n"]: s["en"] for para in p["paras"] for s in para}


FAIL = []

# ---------- A. 転記チェック ----------
for pkey, cats in C.ANNOT.items():
    sen = sentences(pkey)
    for cat, items in cats.items():
        for it in items:
            if it["s"] not in sen:
                FAIL.append(f"[A] {pkey} {cat}: 文{it['s']} が存在しない")
            elif it["t"] not in sen[it["s"]]:
                FAIL.append(f"[A] {pkey} {cat} 文{it['s']}: 「{it['t'][:40]}…」が本文と不一致")

# ---------- B. 位置ごとの網羅走査 ----------
# (regex, 許容カテゴリ群, flags)
WORD_SCANS = [
    (r"\bthat\b",  ("tid", "deg"), re.I),   # that は識別 or 程度構文(so…that 等)
    (r"\bthose\b", ("tid",),       re.I),
    (r"\bit\b",    ("iid",),       re.I),
    (r"\bas\b",    ("aid",),       re.I),
    (r"\b(?:so|such|too|enough)\b", ("deg",), re.I),
    (r"\bnot only\b", ("par",),    re.I),
    (r"\bboth\b",     ("par",),    re.I),
    (r"\brather than\b", ("par",), re.I),
]


def covered_intervals(pkey, n, text, cats):
    ivs = []
    for cat in cats:
        for it in C.ANNOT[pkey].get(cat, []):
            if it["s"] == n:
                for m in re.finditer(re.escape(it["t"]), text):
                    ivs.append((m.start(), m.end()))
    for ig in C.IGNORE:
        if ig["p"] == pkey and ig["s"] == n:
            for m in re.finditer(re.escape(ig["t"]), text):
                ivs.append((m.start(), m.end()))
    return ivs


for pkey in ("p1", "p2"):
    sen = sentences(pkey)
    for n, text in sen.items():
        for pat, cats, flags in WORD_SCANS:
            for m in re.finditer(pat, text, flags):
                os_, oe = m.start(), m.end()
                ivs = covered_intervals(pkey, n, text, cats)
                if not any(s <= os_ and oe <= e for (s, e) in ivs):
                    FAIL.append(f"[B] {pkey} 文{n}: 「{m.group(0)}」(pos {os_})が{cats}に未分類 …{text[max(0,os_-12):oe+12]}…")

# ---------- C. IGNORE 実在チェック ----------
for ig in C.IGNORE:
    sen = sentences(ig["p"])
    if ig["s"] not in sen or ig["t"] not in sen[ig["s"]]:
        FAIL.append(f"[C] IGNORE 陳腐化: {ig['p']} 文{ig['s']} 「{ig['t']}」が本文に無い")

# ---------- 集計 ----------
uniq = sorted(set(FAIL))
counts = {p: {cat: len(items) for cat, items in cats.items()} for p, cats in C.ANNOT.items()}
words = {p["key"]: len(re.split(r"\s+", " ".join(s["en"] for para in p["paras"] for s in para).strip()))
         for p in C.PASSAGES}
print("instance counts:", counts)
print("totals:", {p: sum(v.values()) for p, v in counts.items()})
print("word counts:", words)
if uniq:
    print(f"\nFAIL ({len(uniq)}):")
    for f in uniq:
        print("  ✗", f)
    sys.exit(1)
print("\nALL PASS")
