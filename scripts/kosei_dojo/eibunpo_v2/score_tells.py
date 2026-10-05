#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""設問文の手がかりを取り除いた書きかえ (blind/tellfix_<part>.json) を採点し、適用用のレビューファイルを書く。
    python3 scripts/kosei_dojo/eibunpo_v2/score_tells.py <part> [--write]
合格条件: 盲検 3 レンズ (ans_tell_<part>_{A,B,C}.json) が全員、元の正解の本文を confident で選ぶ & 独立チェック (tellcheck) が ok。
--write で blind/review_<part>_T.json を書く: 合格 → fix_stem / 不合格 → drop (元の問題には手がかりが残っているので予備と入れ替える)。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

BL = os.path.join(L.HERE, "blind")
part = sys.argv[1]
WRITE = "--write" in sys.argv
R = "2" if "--round2" in sys.argv else ""   # 2 回目の書きかえ (tellfix2_ / ans_tell2_ / tellcheck2_)


def load(name, default):
    p = os.path.join(BL, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


fixes = load(f"tellfix{R}_{part}.json", [])
ans = {l: {a["id"]: a for a in load(f"ans_tell{R}_{part}_{l}.json", [])} for l in "ABC"}
chk = {c["_id"]: c for c in load(f"tellcheck{R}_{part}.json", [])}
out, ok_n, ng_n = [], 0, 0
for f in fixes:
    i = f["_id"]; at = L.norm_ws(f["answer_text"])
    bad = []
    for l in "ABC":
        a = ans[l].get(i)
        if not a: bad.append(f"{l}:未回答")
        elif L.norm_ws(a.get("answer_text", "")) != at: bad.append(f"{l}:別解({a.get('answer_text', '')[:16]})")
        elif not a.get("confident", True): bad.append(f"{l}:自信なし")
    c = chk.get(i)
    if not c: bad.append("check:なし")
    elif not c.get("ok"): bad.append("check:NG " + c.get("reason", "")[:80])
    if bad:
        ng_n += 1
        print(f"  ✗ {i} {'; '.join(bad)}")
        out.append({"stem": f["stem"], "_id": i, "action": "drop", "reason": "設問文に正解の語が入っている手がかりを書きかえで消せなかった (" + "; ".join(bad) + ")"})
    else:
        ok_n += 1
        item = {"stem": f["stem"], "_id": i, "action": "fix_stem", "stem_new": f["stem_new"], "answer_text": f["answer_text"], "reason": f.get("reason", "")}
        if f.get("choices"): item["choices"] = f["choices"]
        if f.get("explanation"): item["explanation"] = f["explanation"]
        out.append(item)
print(f"{part}: 書きかえ {len(fixes)} 件 → 合格 {ok_n} / 不合格 {ng_n}")
if WRITE and out:
    json.dump(out, open(os.path.join(BL, f"review_{part}_T{R}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  → blind/review_{part}_T{R}.json に {len(out)} 件")
