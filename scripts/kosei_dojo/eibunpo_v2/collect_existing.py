#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""既存プール (本番に入っている英文法の生成元) を集めて、作問者に渡す設問文の一覧と計画を blind/ に書く。
    python3 scripts/kosei_dojo/eibunpo_v2/collect_existing.py
出力 (blind/ は .gitignore 対象・再生成できる):
  blind/plan.json             カードごとの計画 {gi, part, filter, tag, name, add, gen, syllabus, existing_subtopics}
  blind/stems_<part>.json     {filter: [stem, ...]}  道場の既存設問文 (作問者の重複回避用)
  blind/drill_stems_<part>.json {filter: [stem, ...]} 単元ドリル (別機能) の設問文 (同じ文を出さないための参考)
  blind/existing_<part>.json  {filter: [{stem, choices}]} (lint の同一判定用)
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

OUT = os.path.join(L.HERE, "blind")
os.makedirs(OUT, exist_ok=True)

# カードの tag → 単元ドリル (grammar_questions) 側の unit 名
DRILL_UNITS = {"関係詞": ["関係詞"], "仮定法": ["仮定法"], "時制": ["時制"], "比較": ["比較"], "分詞": ["分詞", "分詞構文"],
               "助動詞": ["助動詞"], "受動態": ["受動態"], "不定詞": ["不定詞"], "動名詞": ["動名詞"], "接続詞": ["接続詞"],
               "前置詞": ["前置詞"], "語法": ["語法・イディオム"], "倒置・強調": ["否定・倒置", "強調・省略"]}

units = L.load_units()
plan = [{**u, "add": L.TARGET_ADD, "gen": L.GEN_PER_UNIT} for u in units]
json.dump(plan, open(os.path.join(OUT, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

ex = L.existing_questions(); drill = L.drill_stems()
tot = 0
for part in L.PARTS:
    stems = collections.OrderedDict(); full = collections.OrderedDict(); dr = collections.OrderedDict()
    for u in [u for u in units if u["part"] == part]:
        stems[u["filter"]] = [q["stem"] for q in ex[part] if q["filter"] == u["filter"]]
        full[u["filter"]] = [{"stem": q["stem"], "choices": q["choices"]} for q in ex[part] if q["filter"] == u["filter"]]
        dr[u["filter"]] = [s for du in DRILL_UNITS.get(u["tag"], []) for s in drill.get(du, [])]
    json.dump(stems, open(os.path.join(OUT, f"stems_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(dr, open(os.path.join(OUT, f"drill_stems_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(full, open(os.path.join(OUT, f"existing_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    n = sum(len(v) for v in stems.values()); tot += n
    unmatched = sum(1 for q in ex[part] if q["filter"] is None)
    print(f"{part:15} 既存 {n:4} 問 (カード外 {unmatched})  " + ", ".join(f"{k}={len(v)}" for k, v in stems.items())
          + "  | ドリル参考 " + ", ".join(f"{k}={len(v)}" for k, v in dr.items()))
print(f"合計 既存 {tot} 問 / 計画 {len(plan)} カード × +{L.TARGET_ADD} = {len(plan) * L.TARGET_ADD} 問 (作問 {L.GEN_PER_UNIT}/カード)")
