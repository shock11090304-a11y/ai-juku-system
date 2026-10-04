#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""既存プール (本番に入っている問題の生成元) を集めて、作問者に渡す stem 一覧と計画を blind/ に書く。
    python3 scripts/chugaku_dojo/expand_v3/collect_existing.py
出力 (blind/ は .gitignore 対象・再生成できる):
  blind/plan.json            単元ごとの計画 {gi, part, subject, filter, name, reading, add, gen}
  blind/stems_<part>.json    {filter: [stem, ...]}  既存の問題文 (作問者の重複回避用)
  blind/existing_<part>.json {filter: [{stem, choices}]} (lint の同一判定用)
"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v3lib as L  # noqa: E402

OUT = os.path.join(L.HERE, "blind")
os.makedirs(OUT, exist_ok=True)

units = L.load_units()
plan = []
for u in units:
    plan.append({**u, "add": L.TARGET_ADD,
                 "gen": (L.READING_PASSAGES if u["reading"] else L.GEN_PER_UNIT)})
json.dump(plan, open(os.path.join(OUT, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

ex = L.existing_questions()
tot = 0
for part in L.PARTS:
    stems = collections.OrderedDict()
    full = collections.OrderedDict()
    for q in ex[part]:
        stems.setdefault(q["filter"], []).append(q["stem"])
        full.setdefault(q["filter"], []).append({"stem": q["stem"], "choices": q["choices"]})
    json.dump(stems, open(os.path.join(OUT, f"stems_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(full, open(os.path.join(OUT, f"existing_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    n = sum(len(v) for v in stems.values()); tot += n
    print(f"{part:7} 既存 {n:4} 問  単元 {len(stems)}: " + ", ".join(f"{k}={len(v)}" for k, v in stems.items()))
print(f"合計 既存 {tot} 問 / 計画 {len(plan)} 単元 × +{L.TARGET_ADD} = {len(plan) * L.TARGET_ADD} 問")
