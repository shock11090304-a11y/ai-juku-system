#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ルール発見ドリル No.04(読解の運用編)の解答キー(ANNOT)を機械検査するゲート。

  python3 check.py

検査:
  A. 転記 — ANNOT の各 t が指定文 s に存在するか。QSET の設問参照文が存在するか。
  B. 位置ごとの網羅(機械判定できる指標のみ):
     - 指示語 this/these/those/such の各出現 → ref か IGNORE。
     - should/must の各出現 → clm か IGNORE。
     - 論理マーカー(However/For example/Therefore/Yet/In other words/So 等) → mkr か IGNORE。
     ※語彙推測(vcb)・言い換え(par)・抽象具体(abc)は意味判断のため位置走査せず、A＋敵対検証で担保。
  C. IGNORE 実在チェック。
すべて PASS で exit 0。
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
MARKERS = (r"\bhowever\b|\bfor example\b|\bfor instance\b|\btherefore\b|\bthus\b|\bmoreover\b|"
           r"\bfurthermore\b|\bnevertheless\b|\bon the other hand\b|\bin contrast\b|"
           r"\bin other words\b|\bthat is\b|\bas a result\b|\byet\b|\binstead\b|\bmeanwhile\b|^so\b")
WORD_SCANS = [
    (r"\b(?:this|these|those|such)\b", ("ref",)),
    (r"\b(?:should|must)\b",           ("clm",)),
    (MARKERS,                          ("mkr",)),
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
        for pat, cats in WORD_SCANS:
            for m in re.finditer(pat, text, re.I | re.M):
                os_, oe = m.start(), m.end()
                ivs = covered_intervals(pkey, n, text, cats)
                if not any(s <= os_ and oe <= e for (s, e) in ivs):
                    FAIL.append(f"[B] {pkey} 文{n}: 「{m.group(0)}」(pos {os_})が{cats}に未分類 …{text[max(0,os_-12):oe+12]}…")

# ---------- A2. QSET 参照文の存在 ----------
for pkey, qs in C.QSET.items():
    sen = sentences(pkey)
    for q in qs:
        for mnum in re.findall(r"文\((\d+)\)", q["q"]):
            if int(mnum) not in sen:
                FAIL.append(f"[A] QSET {pkey}: 設問が参照する文({mnum})が存在しない")

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
