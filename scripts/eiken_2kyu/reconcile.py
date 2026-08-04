# -*- coding: utf-8 -*-
"""盲ソルバーの解答 solver_*.json を answer_key.json と決定的に照合する。
LLMは「解く」だけ、照合は Python が決定的に行う（grammar_workbook/reconcile.py 方針）。

使い方: python3 reconcile.py solver_A.json solver_B.json [...]
出力: 保存正解と食い違う問題（key-mismatch）と、ソルバー間で割れた問題を列挙。
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = ["①", "②", "③", "④"]

key = json.load(open(os.path.join(HERE, "answer_key.json"), encoding="utf-8"))
solvers = {}
for path in sys.argv[1:]:
    d = json.load(open(path, encoding="utf-8"))
    solvers[os.path.basename(path)] = d.get("answers", d)

def lab(v): return LAB[v] if isinstance(v, int) and 0 <= v <= 3 else "?"

mismatch, split = [], []
for k, correct in key.items():
    picks = {n: s.get(k) for n, s in solvers.items()}
    if any(v != correct for v in picks.values()):
        mismatch.append((k, correct, picks))
    if len(set(picks.values())) > 1:
        split.append(k)

n = len(key)
agree_all = sum(1 for k, c in key.items() if all(s.get(k) == c for s in solvers.values()))
print("=== 盲ソルバー照合 ===")
print("ソルバー:", ", ".join(solvers.keys()))
print("総問数 %d ／ 全ソルバーが保存正解と一致 %d (%.0f%%)" % (n, agree_all, 100*agree_all/n))
print("保存正解と食い違いあり: %d 問 ／ ソルバー間で割れ: %d 問" % (len(mismatch), len(split)))
if mismatch:
    print("\n--- 要精査（正解キーとソルバーが不一致） ---")
    for k, c, picks in mismatch:
        ps = "  ".join("%s=%s" % (n, lab(v)) for n, v in picks.items())
        print("  %-12s 保存正解=%s | %s" % (k, lab(c), ps))
sys.exit(0)
