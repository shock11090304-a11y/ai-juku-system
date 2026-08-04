#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ルール発見ドリルの解答キー(ANNOT)を機械検査する誤答・取りこぼしゲート。

  python3 check.py

検査:
  A. ANNOT の各 t が指定文 s に「そのまま」存在するか(転記ミス検出)。
  B. 網羅性 — 候補語彙・パターンで全文を走査し、ANNOT にも IGNORE にも
     載っていない候補が残っていたら FAIL(解答キーの取りこぼし=教材の欠陥)。
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
MARKERS = ["however", "for example", "for instance", "in other words", "as a result",
           "moreover", "in contrast", "on the other hand", "therefore", "in fact",
           "indeed", "in short", "instead", "furthermore", "nevertheless",
           "yet", "but", "also", "though", "although", "while", "meanwhile"]
CAUSAL = [r"\bcauses?d?\b", r"\bcaused\b", r"\blead(s|ing)? to\b", r"\bled to\b",
          r"\bresult(s|ed)? (in|from)\b", r"\bdue to\b", r"\bbecause( of)?\b",
          r"\bthanks to\b", r"\bbrings? about\b", r"\bbrought about\b",
          r"\bcontributes?d? to\b", r"\bcontributed to\b", r"\bso\b",
          r"\bcomes? from\b", r"\bcame from\b", r"\bstems? from\b"]
SUBJ = [r"\bwould\b", r"\bcould\b", r"\bmight\b", r"\bif\b", r"\bwithout\b",
        r"\botherwise\b", r"^had\b", r"\bwere\b", r"\bhad\b", r"\bwish\b", r"\bunless\b"]
PP = (r"(\w+ed|\w+en|known|shown|given|taken|made|kept|found|held|left|built|written|"
      r"thrown|stored|shared|released|forced|formed|filled|caused|treated|typed|removed|helped|done|said|seen|paid)")
PASSIVE = [rf"\b(is|are|was|were|be|been|being)\b(\s+\w+){{0,2}}\s+{PP}\b"]
PART = [r"^(\w+ing)\b", r", (\w+ing)\b"]
WILL = [r"\bwill\b"]

LEX = {"marker": None, "causal": CAUSAL, "subj": SUBJ, "passive": PASSIVE,
       "part": PART, "will": WILL}

def covered(pkey, n, frag, cats_to_check):
    """候補 frag が ANNOT(該当カテゴリ群) か IGNORE でカバーされているか。"""
    frag = frag.strip().lstrip(",").strip()  # 「, linking」→「linking」正規化
    for cat in cats_to_check:
        for it in C.ANNOT[pkey].get(cat, []):
            if it["s"] == n and (frag.lower() in it["t"].lower() or it["t"].lower() in frag.lower()):
                return True
    for ig in C.IGNORE:
        if ig["p"] == pkey and ig["s"] == n and (frag.lower() in ig["t"].lower() or ig["t"].lower() in frag.lower()):
            return True
    return False

for pkey in ("p1", "p2"):
    sen = sentences(pkey)
    for n, text in sen.items():
        low = text.lower()
        # マーカー(語リスト・大小無視・単語境界)
        for m in MARKERS:
            for match in re.finditer(rf"(?<![a-z]){re.escape(m)}(?![a-z])", low):
                frag = text[match.start():match.end()]
                # マーカー候補は marker/causal(so,because等の重複回避) どちらかでカバーされていればOK
                if not covered(pkey, n, frag, ("marker", "causal")):
                    FAIL.append(f"[B] {pkey} 文{n}: マーカー候補「{frag}」が解答キー未収載")
        for name, pats in LEX.items():
            if not pats:
                continue
            for pat in pats:
                for match in re.finditer(pat, text, flags=re.I | re.M):
                    frag = match.group(0)
                    ok_cats = {"causal": ("causal", "marker"),
                               "subj": ("subj",),
                               "passive": ("passive", "subj"),
                               "part": ("part",),
                               "will": ("will",)}[name]
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
print("word counts:", words)
if uniq:
    print(f"\nFAIL ({len(uniq)}):")
    for f in uniq:
        print("  ✗", f)
    sys.exit(1)
print("\nALL PASS")
