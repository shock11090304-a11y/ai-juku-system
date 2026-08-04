#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_expand.js の返り値から DROP index を add2/<part>__<gi>.json に適用し、各単元の不足(need→24)を SHORTS_JSON で出力。
usage: python3 apply_review2.py <review_output.json>
"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add2")
TARGET = 24


def extract(text):
    o = json.loads(text)
    if isinstance(o, dict):
        if "units" in o: return o
        if isinstance(o.get("result"), dict) and "units" in o["result"]: return o["result"]
    raise SystemExit("units 見つからず")


obj = extract(open(sys.argv[1], encoding="utf-8").read())
part = obj["part"]
inc = obj.get("incomplete") or []
if inc:
    print(f"❌ レビュー未完了(検証者失敗)単元あり → 適用中止・再実行が必要: {inc}")
    sys.exit(2)
plan = json.load(open(os.path.join(ADIR, f"_plan_{part}.json"), encoding="utf-8"))
meta = {x["gi"]: x for x in (plan["non_reading"] + plan["reading"])}

drop_by_gi = {u["gi"]: sorted(set(int(d["i"]) for d in (u.get("drop") or []))) for u in obj["units"]}

print(f"=== DROP適用 ({part}) ===")
shorts = []
grand = 0
for gi, m in sorted(meta.items()):
    filt = m["filter"]; target_add = m["add"]
    path = os.path.join(ADIR, f"{part}__{gi}.json")
    arr = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    drops = drop_by_gi.get(gi, [])
    if drops:
        arr = [q for k, q in enumerate(arr) if k not in set(drops)]
        json.dump(arr, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    grand += len(arr)
    need = max(0, target_add - len(arr))
    if need:
        shorts.append({"gi": gi, "filter": filt, "need": need, "factcheck": m["factcheck"], "reading": m["reading"]})
    flag = f"  ⚠️need={need}" if need else ""
    print(f"  gi={gi:2} {filt:14} drop={len(drops):2} 残 {len(arr):2}/{target_add}{flag}")
print(f"  合計追加確定: {grand}")
print("SHORTS_JSON=" + json.dumps({"part": part, "subject": plan["subject"], "units": shorts}, ensure_ascii=False))
