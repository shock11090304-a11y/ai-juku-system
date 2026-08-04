# -*- coding: utf-8 -*-
"""英検準1級 問題集 構造検証ゲート（grammar_workbook/validate.py + analyze_pos.py 相当）

LLM作問データを決定的に点検する。正解キーの健全性・選択肢重複・空所整合・
正解位置分布・英作文語数を機械チェック。build 前に必ず通す。
"""
import json, os, re, sys
from collections import Counter

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
errors, warns = [], []
def err(m): errors.append(m)
def warn(m): warns.append(m)
def load(n):
    p = os.path.join(DATA, n)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
def wc(s): return len(re.findall(r"[A-Za-z][A-Za-z'’\-]*", s))
BAD = "‘’“”—–…"  # スマートクオート等（en()で正規化されるが作問段階で検知）

def check_choices(tag, choices, ans):
    if len(choices) != 4:
        err(f"{tag} choices数={len(choices)} (期待4)")
    if not isinstance(ans, int) or not (0 <= ans <= 3):
        err(f"{tag} answer={ans} 範囲外")
    if len(set(c.strip().lower() for c in choices)) != len(choices):
        err(f"{tag} 選択肢に重複")

def dist_report(label, answers):
    d = Counter(answers)
    print(f"  {label} 正解位置分布(①②③④):", [d.get(i, 0) for i in range(4)])
    if answers and max(d.values()) / len(answers) > 0.40:
        warn(f"{label} 正解位置が偏り >40% ({dict(sorted(d.items()))})")

# ---------- 大問1 ----------
p1 = load("part1_vocab.json")
if p1:
    items = p1["items"]
    print(f"[大問1] {len(items)}問")
    if len(items) < 30: warn(f"大問1 問題数={len(items)} が少ない")
    ids = set()
    for it in items:
        tag = it.get("id", "?")
        for k in ("id", "sentence", "choices", "answer", "target_word", "gloss_ja"):
            if k not in it: err(f"{tag} キー欠落: {k}")
        check_choices(tag, it["choices"], it["answer"])
        if not re.search(r"_{3,}", it["sentence"]): err(f"{tag} 本文に空所(___)なし")
        tw = (it.get("target_word") or "").strip().lower()
        if tw and it["choices"][it["answer"]].strip().lower() != tw:
            warn(f"{tag} target_word≠choices[answer]: '{it['choices'][it['answer']]}' vs '{it['target_word']}'")
        if tag in ids: err(f"id重複: {tag}")
        ids.add(tag)
    dist_report("大問1", [it["answer"] for it in items])

# ---------- 大問2 ----------
p2 = load("part2_cloze.json")
if p2:
    ps = p2["passages"]
    print(f"[大問2] {len(ps)}パッセージ / {sum(len(x['blanks']) for x in ps)}空所")
    ans2 = []
    for pa in ps:
        tag = pa.get("id", "?")
        for k in ("id", "title", "text", "blanks"):
            if k not in pa: err(f"{tag} キー欠落: {k}")
        real = wc(pa["text"])
        if not (240 <= real <= 380): warn(f"{tag} 本文語数={real} が想定外(240-380)")
        for b in pa["blanks"]:
            btag = f"{tag}#{b.get('n')}"
            check_choices(btag, b["choices"], b["answer"])
            if not re.search(r"\(\s*%s\s*\)" % b["n"], pa["text"]):
                err(f"{btag} 本文に空所 ( {b['n']} ) が見つからない")
            if "rationale" not in b: warn(f"{btag} rationale欠落")
            ans2.append(b["answer"])
    dist_report("大問2", ans2)

# ---------- 大問3 ----------
p3 = load("part3_reading.json")
if p3:
    ps = p3["passages"]
    tot_q = sum(len(x["questions"]) for x in ps)
    print(f"[大問3] {len(ps)}パッセージ / {tot_q}問")
    ans3 = []
    for pa in ps:
        tag = pa.get("id", "?")
        for k in ("id", "title", "paragraphs", "questions"):
            if k not in pa: err(f"{tag} キー欠落: {k}")
        if not pa.get("paragraphs"): err(f"{tag} paragraphs空")
        real = wc(" ".join(pa.get("paragraphs", [])))
        if not (320 <= real <= 520): warn(f"{tag} 本文語数={real} が想定外(320-520)")
        for i, q in enumerate(pa["questions"], 1):
            qtag = f"{tag}Q{i}"
            check_choices(qtag, q["choices"], q["answer"])
            if not q.get("evidence"): warn(f"{qtag} evidence欠落")
            ans3.append(q["answer"])
    dist_report("大問3", ans3)

# ---------- 大問4 ----------
p4 = load("part4_writing.json")
if p4:
    print(f"[大問4] 要約{len(p4['summary_tasks'])}題 / 意見{len(p4['essay_tasks'])}題")
    for t in p4["summary_tasks"]:
        n = wc(t["model_summary"])
        s = wc(t["source_text"])
        print(f"  {t['id']}: source={s}語, summary={n}語")
        if not (60 <= n <= 70): err(f"要約 {t['id']} model_summary={n}語 (60-70外)")
        if not (180 <= s <= 250): warn(f"要約 {t['id']} source={s}語 (200前後想定)")
    for t in p4["essay_tasks"]:
        n = wc(t["model_essay"])
        print(f"  {t['id']}: essay={n}語, points={len(t['points'])}")
        if not (120 <= n <= 150): err(f"意見 {t['id']} model_essay={n}語 (120-150外)")
        if len(t["points"]) != 4: warn(f"意見 {t['id']} points={len(t['points'])} (4想定)")

# ---------- 結果 ----------
print("\n=== 検証結果 ===")
for w in warns: print("  [WARN]", w)
for e in errors: print("  [ERR ]", e)
print(f"\nERROR={len(errors)}  WARN={len(warns)}")
sys.exit(1 if errors else 0)
