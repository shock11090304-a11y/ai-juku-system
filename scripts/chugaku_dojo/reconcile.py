#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_lean.js の結果(_verify_results.json= {units:[...]})と verified/ の保存キーを突き合わせ、
独立検証者(solver / fact)が保存キーと食い違う設問を「要確認(suspect)」として洗い出す。
使い方: python3 reconcile.py   (先に _verify_results.json を用意)
"""
import json, os, sys
BASE = os.path.dirname(os.path.abspath(__file__)); VDIR = f"{BASE}/verified"
res = json.load(open(f"{BASE}/_verify_results.json", encoding="utf-8"))
units = res.get("units", res if isinstance(res, list) else [])

suspects = []
checked_q = 0
for u in units:
    part, gi = u["part"], u["gi"]
    fp = f"{VDIR}/{part}__{gi}.json"
    d = json.load(open(fp, encoding="utf-8"))
    stored = {i: q["answer_index"] for i, q in enumerate(d)}
    smap = {a["i"]: a for a in u.get("solver_answers", [])}
    fmap = {a["i"]: a for a in u.get("fact_answers", [])}
    for i, ans in stored.items():
        checked_q += 1
        votes = []
        if i in smap and smap[i].get("confident", True):
            votes.append(("solver", smap[i]["choice_index"]))
        if i in fmap and fmap[i].get("confident", True):
            votes.append(("fact", fmap[i]["choice_index"]))
        disagree = [v for v in votes if v[1] != ans]
        if disagree:
            q = d[i]
            suspects.append({
                "part": part, "gi": gi, "filter": u["filter"], "subject": u["subject"], "i": i,
                "stored": ans, "stored_text": q["choices"][ans],
                "disagree": {who: q["choices"][ci] if 0 <= ci < 4 else ci for who, ci in disagree},
                "stem": q["stem"][:100], "choices": q["choices"],
            })
print(f"検証済 {checked_q} 問 / suspects {len(suspects)}")
for s in suspects:
    print(f"\n[{s['part']}#{s['gi']} {s['filter']} Q{s['i']}] stored={s['stored']}«{s['stored_text']}»")
    print(f"   stem: {s['stem']}")
    print(f"   choices: {s['choices']}")
    print(f"   独立検証の相違: {s['disagree']}")
json.dump(suspects, open(f"{BASE}/_suspects.json", "w"), ensure_ascii=False, indent=1)
