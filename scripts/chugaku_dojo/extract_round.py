#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Workflow の返り値(output file の JSON)から units[].kept を取り出し、
add/math__<gi>.json に書き出す。既存 add ファイルとマージ(stem重複排除)。
usage: python3 extract_round.py <output_file.json>
"""
import json, os, sys, re, collections

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add")
os.makedirs(ADIR, exist_ok=True)

src = sys.argv[1]
raw = open(src, encoding="utf-8").read()

# output file が純JSONでない場合に備え、最初の {"units" から末尾までを抽出して括弧整合で切り出す
def extract_json(text):
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            if "units" in obj:
                return obj
            if isinstance(obj.get("result"), dict) and "units" in obj["result"]:
                return obj["result"]
    except Exception:
        pass
    i = text.find('{"units"')
    if i < 0:
        i = text.find('"units"')
        if i >= 0:
            i = text.rfind('{', 0, i)
    if i < 0:
        raise SystemExit("units JSON が見つかりません")
    depth = 0; instr = False; esc = False
    for j in range(i, len(text)):
        ch = text[j]
        if instr:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return json.loads(text[i:j+1])
    raise SystemExit("JSON の括弧が閉じていません")

obj = extract_json(raw)
units = obj["units"]

REQ = ("subject", "part", "filter", "unit", "stem", "passage", "choices", "answer_index", "explanation")
total = 0
summary = []
for u in units:
    gi = u["gi"]; filt = u["filter"]; add_target = u.get("add")
    kept = u.get("kept", [])
    path = os.path.join(ADIR, f"math__{gi}.json")
    # 既存 add ファイルとマージ(stem重複排除)
    existing = []
    if os.path.exists(path):
        try:
            existing = json.load(open(path, encoding="utf-8"))
        except Exception:
            existing = []
    seen = set((q.get("stem") or "").strip() for q in existing)
    merged = list(existing)
    for q in kept:
        # 整形/検証
        if any(k not in q for k in REQ):
            continue
        s = (q.get("stem") or "").strip()
        if not s or s in seen:
            continue
        ch = q.get("choices")
        if not isinstance(ch, list) or len(ch) != 4 or len(set(str(c).strip() for c in ch)) != 4:
            continue
        ai = q.get("answer_index")
        if not isinstance(ai, int) or not (0 <= ai < 4):
            continue
        seen.add(s)
        merged.append({
            "subject": "数学", "part": "math", "filter": filt, "unit": filt,
            "stem": q["stem"], "passage": "", "choices": q["choices"],
            "answer_index": ai, "explanation": q["explanation"],
        })
    json.dump(merged, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total += len(merged)
    summary.append((filt, gi, len(merged), add_target))

print("=== add/math__<gi>.json 書き出し ===")
for filt, gi, n, tgt in summary:
    flag = "" if (tgt is None or n >= tgt) else f"  ⚠️不足({n}/{tgt})"
    print(f"  gi={gi:2}  {filt:8}  add={n:3}{flag}")
print(f"  合計 追加候補: {total}")
