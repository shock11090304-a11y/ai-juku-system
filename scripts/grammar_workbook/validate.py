#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全20分野のJSONを検証する。構造・件数・mc整合・order語句一致・禁止文字を点検。"""
import json, os, glob, re, unicodedata

UNITS_DIR = os.path.join(os.path.dirname(__file__), "units")

EXPECT_ORDER = [
    ("01_sentence-patterns.json", "文型"),
    ("02_tenses.json", "時制"),
    ("03_perfect.json", "完了形"),
    ("04_modals.json", "助動詞"),
    ("05_passive.json", "受動態"),
    ("06_infinitive.json", "不定詞"),
    ("07_gerund.json", "動名詞"),
    ("08_participle.json", "分詞"),
    ("09_participial-construction.json", "分詞構文"),
    ("10_comparison.json", "比較"),
    ("11_relatives.json", "関係詞"),
    ("12_subjunctive.json", "仮定法"),
    ("13_conjunctions.json", "接続詞"),
    ("14_prepositions.json", "前置詞"),
    ("15_nouns-articles.json", "名詞・冠詞"),
    ("16_pronouns.json", "代名詞"),
    ("17_adjectives-adverbs.json", "形容詞・副詞"),
    ("18_interrogatives.json", "疑問文"),
    ("19_negation-inversion.json", "否定・倒置・強調・省略"),
    ("20_reported-speech.json", "話法"),
]

# 禁止文字: スマートクオート/各種ダッシュ/絵文字/制御文字
SMART = "‘’“”–—… 　"
def find_bad_chars(s):
    bad = []
    for ch in s:
        o = ord(ch)
        if ch in SMART:
            bad.append(("smart/space", repr(ch)))
        elif o < 0x20 and ch not in "\n\t":
            bad.append(("ctrl", hex(o)))
        elif o >= 0x1F000 or (0x2600 <= o <= 0x27BF) or (0x1F300 <= o <= 0x1FAFF):
            bad.append(("emoji", hex(o)))
    return bad

def norm_words(s):
    # 句読点を空白化して語の多重集合を取る(整序の語句一致確認用)
    s = s.lower()
    s = re.sub(r"[.,?!;:\"]", " ", s)
    return sorted([w for w in s.split() if w])

def main():
    total = 0
    type_counts = {"mc":0,"order":0,"rewrite":0}
    problems = []
    all_bad_chars = []
    for fname, unit in EXPECT_ORDER:
        path = os.path.join(UNITS_DIR, fname)
        if not os.path.exists(path):
            problems.append(f"[MISSING] {fname}")
            continue
        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                problems.append(f"[JSON ERROR] {fname}: {e}")
                continue
        if data.get("unit") != unit:
            problems.append(f"[UNIT NAME] {fname}: got {data.get('unit')!r} expected {unit!r}")
        qs = data.get("questions", [])
        if len(qs) != 25:
            problems.append(f"[COUNT] {fname}: {len(qs)} questions (expected 25)")
        nos = [q.get("no") for q in qs]
        if sorted(nos) != list(range(1,26)):
            problems.append(f"[NO SEQ] {fname}: {nos}")
        for q in qs:
            total += 1
            t = q.get("type")
            tag = f"{unit}#{q.get('no')}"
            if t not in type_counts:
                problems.append(f"[TYPE] {tag}: unknown type {t!r}")
                continue
            type_counts[t] += 1
            if q.get("level") not in ("basic","standard"):
                problems.append(f"[LEVEL] {tag}: {q.get('level')!r}")
            # 禁止文字チェック(全英語フィールド)
            for fld in ("stem","answer_text","original","instruction","prompt_ja","point","explanation"):
                v = q.get(fld)
                if isinstance(v, str):
                    for kind, info in find_bad_chars(v):
                        # prompt_ja/point/explanation は和文なので全角スペースのみ許容外チェックは弱める
                        if kind == "smart/space" and info in ("'\\u3000'",) and fld in ("prompt_ja","point","explanation"):
                            continue
                        all_bad_chars.append((tag, fld, kind, info, v[:40]))
            for ch in (q.get("choices") or []):
                for kind, info in find_bad_chars(ch):
                    all_bad_chars.append((tag, "choices", kind, info, ch))
            # 解説の有無
            if not (q.get("explanation") or "").strip():
                problems.append(f"[NO EXPL] {tag}")
            if not (q.get("point") or "").strip():
                problems.append(f"[NO POINT] {tag}")
            # type別
            if t == "mc":
                ch = q.get("choices") or []
                if len(ch) != 4:
                    problems.append(f"[MC CHOICES] {tag}: {len(ch)} choices")
                ai = q.get("answer_index")
                if not isinstance(ai, int) or not (0 <= ai < len(ch)):
                    problems.append(f"[MC IDX] {tag}: answer_index={ai}")
                elif ch[ai] != q.get("answer_text"):
                    problems.append(f"[MC MATCH] {tag}: choices[{ai}]={ch[ai]!r} != answer_text={q.get('answer_text')!r}")
                if len(set(ch)) != len(ch):
                    problems.append(f"[MC DUP] {tag}: duplicate choices {ch}")
                if "( )" not in (q.get("stem") or "") and "()" not in (q.get("stem") or ""):
                    problems.append(f"[MC BLANK] {tag}: no '( )' in stem: {q.get('stem')!r}")
            elif t == "order":
                toks = q.get("tokens") or []
                ans = q.get("answer_text") or ""
                if len(toks) < 3:
                    problems.append(f"[ORDER TOK#] {tag}: {len(toks)} tokens")
                # 語の多重集合一致
                from_tokens = norm_words(" ".join(toks))
                from_ans = norm_words(ans)
                if from_tokens != from_ans:
                    problems.append(f"[ORDER MATCH] {tag}: tokens words {from_tokens} != answer words {from_ans} | ans={ans!r} toks={toks}")
                if not ans or ans[0].islower():
                    problems.append(f"[ORDER CAP] {tag}: answer not capitalized: {ans!r}")
                if ans and ans[-1] not in ".?!":
                    problems.append(f"[ORDER END] {tag}: answer not terminated: {ans!r}")
            elif t == "rewrite":
                if not (q.get("original") or "").strip():
                    problems.append(f"[RW ORIG] {tag}")
                if not (q.get("instruction") or "").strip():
                    problems.append(f"[RW INSTR] {tag}")
                if not (q.get("answer_text") or "").strip():
                    problems.append(f"[RW ANS] {tag}")

    print(f"=== 集計 ===")
    print(f"総問題数: {total}")
    print(f"type別: {type_counts}")
    print()
    print(f"=== 禁止文字 (件数 {len(all_bad_chars)}) ===")
    for tag, fld, kind, info, ctx in all_bad_chars[:60]:
        print(f"  {tag} [{fld}] {kind} {info}: {ctx}")
    print()
    print(f"=== 問題点 (件数 {len(problems)}) ===")
    for p in problems:
        print("  " + p)
    if not problems and not all_bad_chars:
        print("  （問題なし）")

if __name__ == "__main__":
    main()
