#!/usr/bin/env python3
"""📖 長文シードの盲検結果を照合する (ローカル専用・生出力はコミットしない)。
scripts/eiken_vocab/blind/reading/ の solver_{A,B,C}_chunk{1..4}.json と key_reading.json を突き合わせ、
  - 3 名一致 かつ 正解表と一致 → OK
  - 3 名一致 だが 正解表と違う → ★正解表が疑わしい (KEY?)
  - 3 名不一致 → 設問が曖昧かもしれない (SPLIT)
を設問ごとに出す。"""
import glob
import json
import os
import re
import sys

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blind", "reading")
key = json.load(open(os.path.join(D, "key_reading.json"), encoding="utf-8"))
blind = {p["pid"]: p for p in json.load(open(os.path.join(D, "blind_reading.json"), encoding="utf-8"))}
solvers = {}
for f in sorted(glob.glob(os.path.join(D, "solver_*_chunk*.json"))):
    name = re.search(r"solver_([A-Z])_chunk\d+", f).group(1)
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        print(f"⚠ {os.path.basename(f)} を読めない: {e}")
        continue
    solvers.setdefault(name, {}).update({k: int(v) for k, v in (d.get("answers") or {}).items()})
    for fl in d.get("flags") or []:
        solvers.setdefault("_flags", {}).setdefault(fl.get("qid"), []).append(f"{name}: {fl.get('note')}")
names = sorted(k for k in solvers if k != "_flags")
print("solvers:", {n: len(solvers[n]) for n in names})
ok = keyq = split = missing = 0
rows = []
for pid, meta in key.items():
    for j, ans in enumerate(meta["answers"], 1):
        qid = f"{pid}-{j}"
        votes = [solvers[n].get(qid) for n in names]
        if any(v is None for v in votes):
            missing += 1
        vs = [v for v in votes if v is not None]
        agree = len(vs) == len(names) and len(set(vs)) == 1
        if agree and vs[0] == ans:
            ok += 1
            continue
        q = blind[pid]["questions"][j - 1]
        if agree:
            keyq += 1
            tag = "KEY?"
        else:
            split += 1
            tag = "SPLIT"
        rows.append((tag, qid, meta["src"], ans, votes, q["stem"][:60], [c[:40] for c in q["choices"]], solvers.get("_flags", {}).get(qid)))
print(f"OK {ok} / KEY? {keyq} / SPLIT {split} / missing votes {missing} (全 {sum(len(m['answers']) for m in key.values())} 問)")
for r in sorted(rows, key=lambda r: (r[0] != "KEY?", r[1])):
    tag, qid, src, ans, votes, stem, ch, fl = r
    print(f"\n[{tag}] {qid} {src} key={ans} votes={votes}")
    print("   stem:", stem)
    for i, c in enumerate(ch):
        print(f"   {'*' if i == ans else ' '}{i}: {c}")
    if fl:
        print("   flags:", fl)
if "--json" in sys.argv:
    json.dump(rows, open(os.path.join(D, "reconcile.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
