# -*- coding: utf-8 -*-
"""盲ソルバーの解答と鍵を Python で決定的に照合する（LLM に一致判定をさせない）。

  python3 reconcile.py solver_A.json solver_B.json ...

★全員が鍵と違う qid（key-mismatch）が、本物の鍵誤りの最強シグナル。
★1人だけ外した qid は「難しいが正しい」ことが多いので、意味を人が見て判断する。
"""
import os, sys, json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
key = json.load(open(os.path.join(HERE, "answer_key.json"), encoding="utf-8"))

solvers = {}
for path in sys.argv[1:]:
    name = os.path.basename(path).replace(".json", "")
    raw = json.load(open(path, encoding="utf-8"))
    ans = raw.get("answers", raw)
    solvers[name] = {k: int(v) for k, v in ans.items() if str(v).strip().isdigit()}

print("鍵 %d問 / ソルバー %s" % (len(key), ", ".join(
    "%s=%d問" % (n, len(a)) for n, a in solvers.items())))

mismatch = defaultdict(list)
for qid, k in key.items():
    for name, a in solvers.items():
        if qid not in a:
            mismatch[qid].append("%s=未回答" % name)
        elif a[qid] != k:
            mismatch[qid].append("%s=%d" % (name, a[qid]))

allmiss = [q for q, v in mismatch.items() if len(v) == len(solvers)]
somemiss = [q for q, v in mismatch.items() if 0 < len(v) < len(solvers)]

for name, a in solvers.items():
    hit = sum(1 for q, k in key.items() if a.get(q) == k)
    print("  %s : %d/%d 一致 (%.1f%%)" % (name, hit, len(key), 100.0 * hit / len(key)))

print("\n★全員不一致 (鍵誤りの疑い) %d件" % len(allmiss))
for q in sorted(allmiss):
    print("   %s  鍵=%d  %s" % (q, key[q], " ".join(mismatch[q])))
print("\n一部不一致 %d件" % len(somemiss))
for q in sorted(somemiss):
    print("   %s  鍵=%d  %s" % (q, key[q], " ".join(mismatch[q])))

sys.exit(1 if allmiss else 0)
