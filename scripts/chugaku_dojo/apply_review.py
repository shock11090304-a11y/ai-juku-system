#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_math.js の返り値(output file)から DROP index を読み、add/math__<gi>.json から
該当設問を削除する。結果の単元別件数と、目標(24)に対する不足(need)を JSON で出力。
usage: python3 apply_review.py <review_output.json>
出力末尾に SHORTS_JSON=<json> 行(topup用 [{gi,filter,need}])。
"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add")

# gi -> (filter, target_add)  target=24 到達に必要な追加数
TARGET = {
    13: ("正負の数", 14), 14: ("式の計算", 14), 15: ("一次方程式", 14), 16: ("連立方程式", 14),
    17: ("平方根", 14), 18: ("二次方程式", 14), 19: ("比例・反比例", 14), 20: ("一次関数", 14),
    21: ("二乗に比例", 14), 22: ("合同と証明", 14), 23: ("相似", 14), 24: ("円周角", 15),
    25: ("三平方の定理", 14), 26: ("確率", 14), 27: ("データの活用", 14),
}


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
    raise SystemExit("JSON 未閉")


obj = extract_json(open(sys.argv[1], encoding="utf-8").read())
drop_by_gi = {}
for u in obj["units"]:
    gi = u["gi"]
    drop_by_gi[gi] = sorted(set(int(d["i"]) for d in (u.get("drop") or [])))

print("=== DROP適用 ===")
shorts = []
grand = 0
for gi in sorted(TARGET):
    filt, tgt = TARGET[gi]
    path = os.path.join(ADIR, f"math__{gi}.json")
    arr = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    drops = drop_by_gi.get(gi, [])
    if drops:
        keep = [q for k, q in enumerate(arr) if k not in set(drops)]
        json.dump(keep, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    else:
        keep = arr
    grand += len(keep)
    need = max(0, tgt - len(keep))
    if need:
        shorts.append({"gi": gi, "filter": filt, "need": need})
    flag = f"  ⚠️不足 need={need}" if need else ""
    print(f"  gi={gi:2} {filt:8} drop={len(drops):2} → 残 {len(keep):2}/{tgt}{flag}")
print(f"  合計 追加確定: {grand}")
print("SHORTS_JSON=" + json.dumps(shorts, ensure_ascii=False))
