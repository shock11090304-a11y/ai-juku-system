#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_expand.js / topup_expand.js の返り値から units[].kept を add2/<part>__<gi>.json へ書き出し(stem重複排除でマージ)。
usage: python3 extract2.py <output.json>
"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add2")
os.makedirs(ADIR, exist_ok=True)


def extract(text):
    try:
        o = json.loads(text)
        if isinstance(o, dict):
            if "units" in o: return o
            if isinstance(o.get("result"), dict) and "units" in o["result"]: return o["result"]
    except Exception:
        pass
    i = text.find('"units"')
    if i < 0: raise SystemExit("units 見つからず")
    i = text.rfind('{', 0, i)
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
                if depth == 0: return json.loads(text[i:j+1])
    raise SystemExit("JSON未閉")


obj = extract(open(sys.argv[1], encoding="utf-8").read())
part = obj.get("part")
if not part:
    raise SystemExit("part 不明(gen_expand の返り値には part が必要)")
REQ = ("subject", "part", "filter", "unit", "stem", "passage", "choices", "answer_index", "explanation")
print(f"=== add2/{part}__<gi>.json 書き出し ===")
total = 0
for u in obj["units"]:
    gi = u["gi"]; filt = u["filter"]; kept = u.get("kept", [])
    path = os.path.join(ADIR, f"{part}__{gi}.json")
    existing = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    seen = set((q.get("stem") or "").strip() for q in existing)
    merged = list(existing)
    for q in kept:
        if any(k not in q for k in REQ): continue
        s = (q.get("stem") or "").strip()
        if not s or s in seen: continue
        ch = q.get("choices")
        if not isinstance(ch, list) or len(ch) != 4 or len(set(str(c).strip() for c in ch)) != 4: continue
        ai = q.get("answer_index")
        if not isinstance(ai, int) or not (0 <= ai < 4): continue
        seen.add(s)
        merged.append({"subject": q["subject"], "part": part, "filter": filt, "unit": filt,
                       "stem": q["stem"], "passage": q.get("passage", ""), "choices": ch,
                       "answer_index": ai, "explanation": q["explanation"]})
    json.dump(merged, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total += len(merged)
    print(f"  gi={gi:2} {filt:14} add={len(merged)}")
print(f"  合計: {total}")
