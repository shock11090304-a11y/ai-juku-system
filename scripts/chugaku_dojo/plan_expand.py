#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""各partの増量プラン(gi/current/add/gen/factcheck/reading)を計算し、part別 JSON を出力。
add2/_plan_<part>.json に {non_reading:[...], reading:[...]} を書く(workflow args 用)。
TARGET=24。gi は units.json のグローバル順(eng0.. math13.. kokugo28.. rika36.. shakai50..)。
factcheck: rika/shakai/kokugo(知識単元)=True, eng=False。reading 単元は factcheck=False(読解)。
"""
import os, json, math, collections

BASE = os.path.dirname(os.path.abspath(__file__))
TARGET = 24
units = json.load(open(os.path.join(BASE, "units.json"), encoding="utf-8"))

# グローバル gi 採番
gi = 0
GI = {}
READING = {}
SUBJ = {}
order = []
for s in units["subjects"]:
    for u in s["units"]:
        GI[(s["part"], u["filter"])] = gi
        READING[(s["part"], u["filter"])] = bool(u.get("reading"))
        SUBJ[s["part"]] = s["subj"]
        order.append((s["part"], u["filter"]))
        gi += 1

FACTCHECK_PART = {"rika": True, "shakai": True, "kokugo": True, "eng": False}

for part in ["eng", "kokugo", "rika", "shakai"]:
    stems = json.load(open(os.path.join(BASE, "add2", f"_stems_{part}.json"), encoding="utf-8"))
    non_reading = []
    reading = []
    for (p, filt) in order:
        if p != part:
            continue
        cur = len(stems.get(filt, []))
        add = max(0, TARGET - cur)
        if add == 0:
            continue
        gen = add + max(8, math.ceil(add * 0.7))  # 余裕込み(~1.6x)
        is_reading = READING[(part, filt)]
        fc = FACTCHECK_PART[part] and not is_reading  # 読解は factcheck 対象外
        item = {"part": part, "subject": SUBJ[part], "filter": filt, "gi": GI[(part, filt)],
                "current": cur, "add": add, "gen": gen, "factcheck": fc, "reading": is_reading}
        (reading if is_reading else non_reading).append(item)
    plan = {"part": part, "subject": SUBJ[part], "non_reading": non_reading, "reading": reading}
    json.dump(plan, open(os.path.join(BASE, "add2", f"_plan_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    nr = sum(x["add"] for x in non_reading)
    rd = sum(x["add"] for x in reading)
    print(f"=== {part} ({SUBJ[part]}) ===  非読解 {len(non_reading)}単元/+{nr}問  読解 {len(reading)}単元/+{rd}問")
    for x in non_reading + reading:
        tag = " [reading]" if x["reading"] else (" [fact]" if x["factcheck"] else "")
        print(f"   gi={x['gi']:2} {x['filter']:14} cur={x['current']:2} add={x['add']:2} gen={x['gen']:2}{tag}")
