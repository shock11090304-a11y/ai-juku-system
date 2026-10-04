#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_drafts.py が書いた blind/<part>__<gi>.blind.json を、解答エージェント 1 回ぶんの束 (batch) にまとめる。
    python3 scripts/chugaku_dojo/expand_v3/make_batches.py <part> [max_per_batch]
出力: blind/batch_<part>_<n>.json  (非読解 ≤ 90 問・読解 ≤ 40 問。単元の途中では切らない)
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v3lib as L  # noqa: E402

BL = os.path.join(L.HERE, "blind")
part = sys.argv[1]
MAXN = int(sys.argv[2]) if len(sys.argv) > 2 else 90
by_gi = {u["gi"]: u for u in L.load_units()}
for fp in glob.glob(os.path.join(BL, f"batch_{part}_*.json")): os.remove(fp)
files = sorted(glob.glob(os.path.join(BL, f"{part}__*.blind.json")), key=lambda p: int(os.path.basename(p).split("__")[1].split(".")[0]))
batches, cur, cur_reading = [], [], None
for fp in files:
    gi = int(os.path.basename(fp).split("__")[1].split(".")[0]); reading = by_gi[gi]["reading"]
    items = json.load(open(fp, encoding="utf-8"))
    limit = 40 if reading else MAXN
    if cur and (len(cur) + len(items) > limit or cur_reading != reading):
        batches.append(cur); cur = []
    cur += items; cur_reading = reading
if cur: batches.append(cur)
for n, b in enumerate(batches):
    json.dump(b, open(os.path.join(BL, f"batch_{part}_{n}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    units = sorted({x["id"].split("-")[0] for x in b})
    print(f"batch_{part}_{n}.json: {len(b)} 問  単元 {units}")
print(f"{len(batches)} batches")
