#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""final_resolve2.js の返り値 vs add2/_stored_key_<part>.json 照合。
usage: python3 compare_final2.py <final_output.json>
両ソルバー不一致=0 かつ 欠落=0 なら合格。
"""
import os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__)); ADIR = os.path.join(BASE, "add2")


def extract(text):
    o = json.loads(text)
    if isinstance(o, dict):
        if "units" in o: return o
        if isinstance(o.get("result"), dict) and "units" in o["result"]: return o["result"]
    raise SystemExit("units 見つからず")


obj = extract(open(sys.argv[1], encoding="utf-8").read())
part = obj["part"]
key = json.load(open(os.path.join(ADIR, f"_stored_key_{part}.json"), encoding="utf-8"))
blind = {b["gid"]: b for b in json.load(open(os.path.join(ADIR, f"_stored_blind_{part}.json"), encoding="utf-8"))}
A = {}; B = {}
for u in obj["units"]:
    for a in u.get("solverA", []): A[a["gid"]] = a
    for b in u.get("solverB", []): B[b["gid"]] = b

both = []; one = []; missing = []; ok = 0
for gid, k in key.items():
    a = A.get(gid); b = B.get(gid)
    if a is None or b is None: missing.append(gid); continue
    ad = a["choice_index"] == k; bd = b["choice_index"] == k
    if ad and bd: ok += 1
    elif not ad and not bd: both.append((gid, k, a["choice_index"], b["choice_index"]))
    else: one.append((gid, k, a["choice_index"], b["choice_index"]))

print(f"=== 最終盲再解答 vs 保存キー ({part}, {len(key)}問) ===")
print(f"両ソルバー一致: {ok} / 片方のみ不一致: {len(one)} / ★両方不一致: {len(both)} / 欠落: {len(missing)}")

def show(t):
    gid, k, ai, bi = t; q = blind.get(gid, {})
    print(f"   [{gid}] {q.get('unit')} key={k} A={ai} B={bi}\n     {(q.get('stem') or '')[:70]}\n     {q.get('choices')}")

if both:
    print("\n--- ★両方不一致(真の誤り候補) ---"); [show(t) for t in both]
if one:
    print("\n--- 片方のみ不一致(参考・多くはソルバー側) ---"); [show(t) for t in one[:40]]
if missing: print("\n欠落:", missing[:20])
res = (len(both) == 0 and len(missing) == 0)
print("\n最終判定:", "✅ 両方不一致0・欠落0" if res else "❌ 要調査")
sys.exit(0 if res else 1)
