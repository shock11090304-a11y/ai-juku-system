#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""workflow 用 args JSON を plan から生成。
usage: python3 emit_args.py <part> <gen|review|final> [reading]
  gen    : gen_expand.js 用 {part,subject,units:[{filter,gi,add,gen,factcheck}]}
  review : review_expand.js 用 {part,subject,units:[{filter,gi,factcheck}]}
  final  : final_resolve2.js 用 {part,subject,units:[{filter,factcheck}]}
3rd引数 reading を付けると読解単元、無ければ非読解単元。
"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
part, mode = sys.argv[1], sys.argv[2]
want_reading = len(sys.argv) > 3 and sys.argv[3] == "reading"
plan = json.load(open(os.path.join(BASE, "add2", f"_plan_{part}.json"), encoding="utf-8"))
items = plan["reading"] if want_reading else plan["non_reading"]
subject = plan["subject"]

if mode == "gen":
    units = [{"filter": x["filter"], "gi": x["gi"], "add": x["add"], "gen": x["gen"], "factcheck": x["factcheck"]} for x in items]
elif mode == "review":
    units = [{"filter": x["filter"], "gi": x["gi"], "factcheck": x["factcheck"]} for x in items]
elif mode == "final":
    units = [{"filter": x["filter"], "factcheck": x["factcheck"]} for x in items]
else:
    raise SystemExit("mode は gen|review|final")
print(json.dumps({"part": part, "subject": subject, "units": units}, ensure_ascii=False))
