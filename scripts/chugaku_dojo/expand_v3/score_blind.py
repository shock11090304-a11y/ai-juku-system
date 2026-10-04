#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲検 (正解を伏せた独立解答) の結果を key と突き合わせ、全員一致かつ confident の問題だけを合格にする。
    python3 scripts/chugaku_dojo/expand_v3/score_blind.py <part>
入力: blind/<part>__<gi>.key.json (lint_drafts.py が書く)
      blind/ans_<part>_<lens>_<n>.json  … 解答者の出力 [{id, answer_text, answer_index?, confident}]
         lens は A (自力で解く) / B (全選択肢を点検) / C (別解・計算 or 事実照合)。3 レンズそろって初めて判定。
出力: blind/accept_<part>.json {gi: {accepted:[id], rejected:[[id, reason]], missing:[id]}}
★解答は「選択肢の本文」で受け取り、本文の完全一致 (空白正規化) で照合する。添字は本文が照合できないときの保険。
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v3lib as L  # noqa: E402

BL = os.path.join(L.HERE, "blind")
part = sys.argv[1]
LENSES = ["A", "B", "C"]

answers = {lens: {} for lens in LENSES}
for lens in LENSES:
    for fp in sorted(glob.glob(os.path.join(BL, f"ans_{part}_{lens}_*.json"))):
        try:
            data = json.load(open(fp, encoding="utf-8"))
        except Exception as e:
            print(f"⚠️ {os.path.basename(fp)} 読めない: {e}"); continue
        if isinstance(data, dict):
            data = data.get("answers") or data.get("items") or []
        for a in data:
            if isinstance(a, dict) and a.get("id"):
                answers[lens][str(a["id"]).strip()] = a
print(f"解答ファイル: " + ", ".join(f"{l}={len(answers[l])}" for l in LENSES))

blind_by_id = {}
for fp in glob.glob(os.path.join(BL, f"{part}__*.blind.json")):
    for b in json.load(open(fp, encoding="utf-8")):
        blind_by_id[b["id"]] = b


def resolve(a, choices):
    """解答 → 選択肢 index (本文一致を優先・無ければ添字)。None なら照合不能。"""
    t = L.norm_ws(a.get("answer_text", ""))
    if t:
        for i, c in enumerate(choices):
            if L.norm_ws(c) == t:
                return i, "text"
        # 末尾の句点・引用符の違いだけなら許す
        tt = re.sub(r"[「」『』\"'。.\s]+$", "", t)
        for i, c in enumerate(choices):
            if re.sub(r"[「」『』\"'。.\s]+$", "", L.norm_ws(c)) == tt:
                return i, "text~"
    ai = a.get("answer_index")
    if isinstance(ai, int) and 0 <= ai < 4:
        return ai, "index"
    return None, "unmatched"


report = {}
tot_acc = tot_rej = tot_missing = 0
for fp in sorted(glob.glob(os.path.join(BL, f"{part}__*.key.json")), key=lambda p: int(os.path.basename(p).split("__")[1].split(".")[0])):
    gi = int(os.path.basename(fp).split("__")[1].split(".")[0])
    key = json.load(open(fp, encoding="utf-8"))
    acc, rej, missing = [], [], []
    why = collections.Counter()
    for qid, k in key.items():
        ch = blind_by_id[qid]["choices"]
        picks = []
        for lens in LENSES:
            a = answers[lens].get(qid)
            if a is None:
                picks.append((lens, None, "missing", None)); continue
            idx, how = resolve(a, ch)
            picks.append((lens, idx, how, bool(a.get("confident", True))))
        if any(p[1] is None and p[2] == "missing" for p in picks):
            missing.append(qid); continue
        bad = []
        for lens, idx, how, conf in picks:
            if idx is None:
                bad.append(f"{lens}:照合不能")
            elif idx != k["answer_index"]:
                bad.append(f"{lens}:別解({ch[idx][:20]})")
            elif not conf:
                bad.append(f"{lens}:自信なし")
        if bad:
            rej.append([qid, "; ".join(bad)]); why[bad[0].split(":")[1][:4]] += 1
        else:
            acc.append(qid)
    report[gi] = {"filter": next(iter(key.values()))["filter"] if key else "?", "accepted": acc, "rejected": rej, "missing": missing}
    tot_acc += len(acc); tot_rej += len(rej); tot_missing += len(missing)
    print(f"{part}__{gi:<2} {report[gi]['filter']:<10} 合格 {len(acc):2} / 不合格 {len(rej):2} / 未回答 {len(missing):2}  {dict(why) if why else ''}")
    for r in rej:
        print("     ✗", r[0], r[1][:100])
json.dump(report, open(os.path.join(BL, f"accept_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"合計 合格 {tot_acc} / 不合格 {tot_rej} / 未回答 {tot_missing}")
