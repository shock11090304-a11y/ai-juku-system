#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""final_resolve.js の返り値と add/_stored_key.json を突き合わせ、保存キーとの一致を検証。
usage: python3 compare_final.py <final_resolve_output.json>
判定: 各設問について 2ソルバーが保存キーと一致するか。
  - 両ソルバーとも保存キーに不一致 = 重大(真の誤りの可能性)→要調査で列挙
  - 片方だけ不一致 = ソルバー側の可能性(保存キー+他方が一致)→参考列挙
"""
import os, sys, json, collections

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add")
key = json.load(open(os.path.join(ADIR, "_stored_key.json"), encoding="utf-8"))
blind = {b["gid"]: b for b in json.load(open(os.path.join(ADIR, "_stored_blind.json"), encoding="utf-8"))}

def extract(text):
    obj = json.loads(text)
    if isinstance(obj, dict):
        if "units" in obj: return obj
        if isinstance(obj.get("result"), dict) and "units" in obj["result"]: return obj["result"]
    raise SystemExit("units 見つからず")

obj = extract(open(sys.argv[1], encoding="utf-8").read())
A = {}; B = {}
for u in obj["units"]:
    for a in u.get("solverA", []): A[a["gid"]] = a
    for b in u.get("solverB", []): B[b["gid"]] = b

both_disagree = []
one_disagree = []
missing = []
n_ok = 0
for gid, k in key.items():
    a = A.get(gid); b = B.get(gid)
    if a is None or b is None:
        missing.append(gid); continue
    ad = (a["choice_index"] == k); bd = (b["choice_index"] == k)
    if ad and bd:
        n_ok += 1
    elif not ad and not bd:
        both_disagree.append((gid, k, a["choice_index"], b["choice_index"]))
    else:
        one_disagree.append((gid, k, a["choice_index"], b["choice_index"]))

total = len(key)
print(f"=== 最終盲再解答 vs 保存キー ({total}問) ===")
print(f"両ソルバー一致(保存キー確認OK): {n_ok}")
print(f"片方のみ不一致(参考): {len(one_disagree)}")
print(f"両方不一致(★要調査): {len(both_disagree)}")
print(f"解答欠落: {len(missing)}")

def show(gid, k, ai, bi):
    q = blind.get(gid, {})
    print(f"   [{gid}] {q.get('unit')}  key={k} A={ai} B={bi}")
    print(f"     stem: {(q.get('stem') or '')[:70]}")
    print(f"     choices: {q.get('choices')}")

if both_disagree:
    print("\n--- ★両方不一致(真の誤り候補) ---")
    for t in both_disagree: show(*t)
if one_disagree:
    print("\n--- 片方のみ不一致(多くはソルバー側の誤り) ---")
    for t in one_disagree[:30]: show(*t)
if missing:
    print("\n--- 欠落 gid ---", missing[:20])

# 合格条件: 両方不一致=0 かつ 欠落=0
ok = (len(both_disagree) == 0 and len(missing) == 0)
print("\n最終判定:", "✅ 全問が保存キーを確認(両方不一致0)" if ok else "❌ 両方不一致/欠落あり=要調査")
sys.exit(0 if ok else 1)
