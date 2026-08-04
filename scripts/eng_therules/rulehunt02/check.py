#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ルール発見ドリル No.02(文構造編)の解答キー(ANNOT)を機械検査するゲート。

  python3 check.py

検査:
  A. ANNOT の各 t が指定文 s に「そのまま」存在するか(転記ミス検出)。
  B. 網羅性 — 機械判定できる構文パターン(比較/強調/倒置/関係詞/同格)を全文走査し、
     ANNOT にも IGNORE にも載っていない候補が残っていたら FAIL(取りこぼし=教材の欠陥)。
     ※無生物主語(isu)と関係副詞・場所倒置は意味判断のため機械走査せず、
       A(転記)のみ+解説編の敵対検証で担保する。
  C. IGNORE の各エントリが実在するか(陳腐化検出)。
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

# ---------- B. 網羅性走査 ----------
# 各候補は (category, regex) で拾い、covered() で ANNOT(該当カテゴリ群)/IGNORE を確認。
SUPERLATIVE = r"\b(most|least|best|worst|greatest|largest|smallest|highest|lowest|deepest|richest|finest)\b"
APP_NOUNS = (r"the (?:\w+ )?(?:fact|idea|belief|news|claim|hope|possibility|conclusion|"
             r"sense|feeling|assumption|reason|myth|thought|fear|discovery|realization) that\b")
INV_INIT = r"^(Never|Rarely|Seldom|Little|Hardly|Scarcely|Nowhere|Not only|Not until|No sooner|Only)\b"
NEG_AUX = (r"\b(never|rarely|seldom|little|hardly|scarcely|nowhere)\s+"
           r"(has|have|had|do|does|did|is|are|was|were|will|can|could|would|should|may|might|must)\b")

# (name, pattern, ok_cats) — ok_cats はその候補を吸収できる ANNOT カテゴリ群
SCANS = [
    ("than",       r"\bthan\b",                     ("cmp",)),
    ("as..as",     r"\bas\b",                       ("cmp",)),           # as は必ず比較(as..as)で回収する前提
    ("the-er",     r"\b[Tt]he (?:more|less|\w+er)\b(?=.*,\s*the (?:more|less|\w+er)\b)", ("cmp",)),
    ("no other",   r"\bno other\b",                 ("cmp",)),
    ("superlative", SUPERLATIVE,                    ("cmp",)),
    ("it-cleft",   r"\bit (?:is|was)\b",            ("clf",)),           # It is/was … → 強調構文 or IGNORE(形式主語)
    ("what-cleft", r"^What\b",                       ("clf", "rel")),     # 文頭 What … is(擬似分裂) or 関係詞
    ("emph-do",    r"\b(?:do|does|did)\b",           ("clf", "inv")),     # do/does/did → 強調 or 倒置 or IGNORE
    ("inv-init",   INV_INIT,                         ("inv",)),
    ("neg-aux",    NEG_AUX,                          ("inv",)),
    ("rel-which",  r",\s*which\b",                    ("rel",)),
    ("rel-who",    r",\s*who\b",                      ("rel",)),
    ("rel-what",   r"\bwhat\b",                       ("rel", "clf")),
    ("rel-ever",   r"\b(?:whatever|whoever|whomever|whichever|wherever|whenever|however)\b", ("rel",)),
    ("app-colon",  r":",                              ("app",)),
    ("app-dash",   r"—",                              ("app",)),
    ("app-that",   APP_NOUNS,                         ("app",)),
]


def covered(pkey, n, frag, cats_to_check):
    frag = frag.strip().lstrip(",").strip().lower()
    for cat in cats_to_check:
        for it in C.ANNOT[pkey].get(cat, []):
            if it["s"] == n and (frag in it["t"].lower() or it["t"].lower() in frag):
                return True
    for ig in C.IGNORE:
        if ig["p"] == pkey and ig["s"] == n and (frag in ig["t"].lower() or ig["t"].lower() in frag):
            return True
    return False


for pkey in ("p1", "p2"):
    sen = sentences(pkey)
    for n, text in sen.items():
        for name, pat, ok_cats in SCANS:
            for match in re.finditer(pat, text, flags=re.M):
                frag = match.group(0)
                if not covered(pkey, n, frag, ok_cats):
                    FAIL.append(f"[B] {pkey} 文{n}: {name}候補「{frag}」が解答キー未収載")

# ---------- C. IGNORE 実在チェック ----------
for ig in C.IGNORE:
    sen = sentences(ig["p"])
    if ig["s"] not in sen or ig["t"].lower() not in sen[ig["s"]].lower():
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
