#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""b2/d0..d5.json (ワークフロー作問+多段検証済のB型6大問) を本番取込形に組版。
- group を part から正規化(数学IA/IIB)
- 正解位置を均等化(全体できるだけ均等[8,8,7,7]・大問内 各位置≤2・隣接重複なし)
- explanation を "【単元】unit。正解は「latex」。reason" で生成
- 最終ガード: sympy で choices_value[new_answer]==truth・選択肢distinct を全数再照合
出力: math_exam_b2.json
"""
import json, os, sys, glob
from sympy import sympify, simplify, Tuple

HERE = os.path.dirname(__file__)
SUBDIR = sys.argv[1] if len(sys.argv) > 1 else "b2"
SOURCE = sys.argv[2] if len(sys.argv) > 2 else "kyotsu-exam-format-b2-20260623"
OUTNAME = sys.argv[3] if len(sys.argv) > 3 else "math_exam_b2.json"
MODEL = "claude-opus-verified"
GROUP_OF = {"math_exam_ia": "数学IA", "math_exam_iib": "数学IIB",
            "chem_exam": "化学", "phys_exam": "物理"}

def sval(s):
    return sympify(s)
def eq(u, v):
    try:
        if getattr(u, "func", None) == Tuple or getattr(v, "func", None) == Tuple:
            return len(u) == len(v) and all(simplify(a-b) == 0 for a, b in zip(u, v))
    except Exception:
        pass
    if simplify(u - v) == 0:
        return True
    # 数値許容(理科: Float/sqrt 混在時の保険。exact が第一)
    try:
        return abs(float(u) - float(v)) < 1e-9
    except Exception:
        return False

# 1) 大問を読み、平坦化
daimon = []
files = sorted(glob.glob(os.path.join(HERE, SUBDIR, "d*.json")))
files = [f for f in files if not f.endswith("_blind.json")]
for f in files:
    daimon.append(json.load(open(f, encoding="utf-8")))
flat = []  # (di, qi, subq)
for di, d in enumerate(daimon):
    for qi, q in enumerate(d["subqs"]):
        flat.append((di, qi, q))
N = len(flat)  # 30

# 2) 正解位置の均等化(全体できるだけ均等・大問内≤2・隣接重複なし)。決定的バックトラッキング。
_q, _r = divmod(N, 4)
target = [_q + (1 if i < _r else 0) for i in range(4)]
assert sum(target) == N
block = [di for (di, qi, q) in flat]
pos_of = {}
def solve(idx, remain, assigned):
    if idx == N:
        return True
    di = block[idx]
    same = [p for (j, p) in assigned if block[j] == di]
    prev = same[-1] if same else None
    # 試行順を「残数の多い位置から」(同数は番号昇順)に。全体均等を保ちつつ
    #   前方への偏り(0優先)で起きる終端デッドロックを避け、バックトラッキングを激減させる。
    cands = [p for p in range(4) if remain[p] > 0 and same.count(p) < 2 and p != prev]
    cands.sort(key=lambda p: (-remain[p], p))
    for p in cands:
        remain[p] -= 1; pos_of[idx] = p
        if solve(idx+1, remain, assigned+[(idx, p)]): return True
        remain[p] += 1; del pos_of[idx]
    return False
assert solve(0, target[:], []), "position balancing failed"

# 3) 各 subq を再配置 + 最終 sympy ガード + question_data 構築
errors = []
posc = {0:0,1:0,2:0,3:0}
out_questions = {di: [] for di in range(len(daimon))}
for fi, (di, qi, q) in enumerate(flat):
    cl = list(q["choices_latex"]); cv = list(q["choices_value"])
    old = q["answer_index"]; tv = q["truth_value"]
    # 取込前の自己整合(元の並び)を再確認
    if not eq(sval(cv[old]), sval(tv)):
        errors.append(f"d{di}.q{qi+1}: 元 answer!=truth")
    # 新位置へ正解を移動・残りを順序保持で詰める
    newp = pos_of[fi]
    correct_l, correct_v = cl[old], cv[old]
    rest_l = [cl[k] for k in range(4) if k != old]
    rest_v = [cv[k] for k in range(4) if k != old]
    nl = [None]*4; nv = [None]*4
    nl[newp] = correct_l; nv[newp] = correct_v
    j = 0
    for k in range(4):
        if k != newp:
            nl[k] = rest_l[j]; nv[k] = rest_v[j]; j += 1
    # 再配置後ガード
    if not eq(sval(nv[newp]), sval(tv)):
        errors.append(f"d{di}.q{qi+1}: 再配置後 answer!=truth")
    vals = [sval(x) for x in nv]
    for a in range(4):
        for b in range(a+1, 4):
            if eq(vals[a], vals[b]):
                errors.append(f"d{di}.q{qi+1}: dup choice {a},{b}")
    if len(set(nl)) != 4:
        errors.append(f"d{di}.q{qi+1}: dup latex")
    posc[newp] += 1
    unit = q["unit"]
    out_questions[di].append((qi, {
        "id": f"q{qi+1}",
        "type": "multiple_choice",
        "stem": q["stem"],
        "choices": nl,
        "answer": newp,
        "unit": unit,
        "explanation": f"【単元】{unit}。正解は「{correct_l}」。{q.get('reason','')}".strip(),
    }))

# 4) 大問 JSON 化
rows = []
for di, d in enumerate(daimon):
    qs = [q for _, q in sorted(out_questions[di], key=lambda t: t[0])]
    rows.append({
        "exam_id": "rikei",
        "part_key": d["part"],
        "eiken_grade": "kyotsu_rikei",
        "question_data": {
            "passage": d["passage"],
            "subject": "数学",
            "univ_simulated": "共通テスト(本番形式)",
            "year_simulated": 2025,
            "source": SOURCE,
            "exam_format": True,
            "group": GROUP_OF[d["part"]],
            "questions": qs,
        },
        "model": MODEL,
    })

print("=== 正解位置分布(目標 8/8/7/7) ===", posc)
for di, d in enumerate(daimon):
    pos = [q["answer"] for _, q in sorted(out_questions[di], key=lambda t: t[0])]
    print(f"  d{di} {d['part']:14} {GROUP_OF[d['part']]} {d.get('unit_theme','')[:20]:20} pos={pos}")
print("=== 大問数 ===", len(rows), " 小問総数 ===", sum(len(r['question_data']['questions']) for r in rows))
if errors:
    print("!!! sympy ガード エラー !!!")
    for e in errors: print("  ", e)
    raise SystemExit(1)
print("=== sympy 最終ガード: 再配置後も answer==truth・distinct OK ===")

out = os.path.join(HERE, OUTNAME)
json.dump({"questions": rows, "skip_full": False}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out)
