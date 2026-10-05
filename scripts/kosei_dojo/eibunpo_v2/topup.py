#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""予備 (surplus) が尽きたカードの不足分を補う (top-up)。
    python3 scripts/kosei_dojo/eibunpo_v2/topup.py prep  <part> <gi>   # blind/topup_<part>__<gi>.json (作問の生出力) を検査し、盲検の束 batch_<part>_T<gi>.json と key を書く
    python3 scripts/kosei_dojo/eibunpo_v2/topup.py score <part> <gi>   # ans_<part>_{A,B,C}_T<gi>.json を採点し、合格を verified に不足ぶん足す (余りは surplus へ)。apply_log に replaced として記録
検査: 形式 (validate_question)・既存プール/単元ドリル/今の verified 全カード/予備/落とした問題 と同一でない・他カード名が設問文/選択肢に無い。
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

BL = os.path.join(L.HERE, "blind"); VD = os.path.join(L.HERE, "verified")
cmd, part, gi = sys.argv[1], sys.argv[2], int(sys.argv[3])
units = L.load_units(); u = next(x for x in units if x["gi"] == gi); assert u["part"] == part
TAG = f"T{gi}"


def load(p, default):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def all_known_keys():
    """重複判定に使う (sig, stem_key) の集合: 既存プール・単元ドリル・verified 全カード・予備・落とした問題。"""
    sigs, stems = set(), set()
    for q in L.existing_questions()[part]:
        sigs.add(L.sig(q["stem"], q["choices"])); stems.add(L.stem_key(q["stem"]))
    for v in load(os.path.join(BL, f"drill_stems_{part}.json"), {}).values():
        for s in v: stems.add(L.stem_key(s))
    for fp in glob.glob(os.path.join(VD, f"{part}__*.json")) + glob.glob(os.path.join(BL, f"surplus_{part}__*.json")):
        for q in load(fp, []):
            sigs.add(L.sig(q["stem"], q["choices"])); stems.add(L.stem_key(q["stem"]))
    for fp in L.own_part_files(glob.glob(os.path.join(BL, f"applied_review_{part}_*.json")), part, "review_"):
        for it in load(fp, []):
            if isinstance(it, dict) and it.get("action") == "drop" and it.get("stem"): stems.add(L.stem_key(it["stem"]))
    return sigs, stems


def other_names():
    names = set()
    for o in units:
        if o["part"] != part or o["gi"] == gi: continue
        names.update([o["filter"], o["tag"]])
    return sorted(n for n in names if n not in u["tag"] and u["tag"] not in n and n not in u["filter"] and u["filter"] not in n)


if cmd == "prep":
    items = load(os.path.join(BL, f"topup_{part}__{gi}.json"), [])
    if isinstance(items, dict): items = items.get("questions", [])
    sigs, stems = all_known_keys(); others = other_names()
    kept, key, dropped = [], {}, []
    seen = set()
    for n, q in enumerate(items):
        qid = f"{part}{gi}-{TAG}-{n:02d}"; errs = []
        if not isinstance(q, dict): dropped.append((qid, "オブジェクトでない")); continue
        q.setdefault("filter", u["filter"]); q.setdefault("passage", "")
        if not L.validate_question(q, u, errs, qid): dropped.append((qid, "; ".join(e for _, e in errs))); continue
        s = L.sig(q["stem"], q["choices"]); sk = L.stem_key(q["stem"])
        if s in sigs or sk in stems or s in seen: dropped.append((qid, "既存/ドリル/今のカード/落とした問題と同一")); continue
        hit = [t for t in others if t in q["stem"] or any(t in c for c in q["choices"])]
        if hit: dropped.append((qid, f"他カード名 {hit}")); continue
        seen.add(s)
        kept.append({"id": qid, "stem": q["stem"], "passage": "", "choices": q["choices"]})
        key[qid] = {"answer_text": q["choices"][q["answer_index"]], "answer_index": q["answer_index"], "filter": u["filter"], "q": q}
    json.dump(kept, open(os.path.join(BL, f"batch_{part}_{TAG}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(key, open(os.path.join(BL, f"topup_key_{part}__{gi}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{part}__{gi} {u['filter']}: 作問 {len(items)} → 盲検へ {len(kept)} / drop {len(dropped)}")
    for d in dropped: print("   drop", d[0], d[1][:100])

elif cmd == "score":
    key = load(os.path.join(BL, f"topup_key_{part}__{gi}.json"), {})
    ans = {l: {a["id"]: a for a in load(os.path.join(BL, f"ans_{part}_{l}_{TAG}.json"), [])} for l in "ABC"}
    vf = os.path.join(VD, f"{part}__{gi}.json"); cur = load(vf, [])
    sp = os.path.join(BL, f"surplus_{part}__{gi}.json"); sur = load(sp, [])
    accepted, rejected = [], []
    for qid, k in key.items():
        bad = []
        for l in "ABC":
            a = ans[l].get(qid)
            if not a: bad.append(f"{l}:未回答"); continue
            t = L.norm_ws(a.get("answer_text", ""))
            if t != L.norm_ws(k["answer_text"]): bad.append(f"{l}:別解({a.get('answer_text', '')[:16]})")
            elif not a.get("confident", True): bad.append(f"{l}:自信なし")
        (rejected if bad else accepted).append((qid, bad))
    KEEP = ("subject", "part", "filter", "unit", "stem", "passage", "choices", "answer_index", "explanation", "form", "level")
    need = max(0, L.TARGET_ADD - len(cur)); added = []
    for qid, _ in accepted:
        q = {kk: key[qid]["q"].get(kk, "") for kk in KEEP}; q["filter"] = u["filter"]; q["subject"] = u["subject"]; q["part"] = part; q["_id"] = qid
        if len(added) < need: cur.append(q); added.append(qid)
        else: sur.append(q)
    json.dump(cur, open(vf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(sur, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    lp = os.path.join(BL, f"apply_log_{part}.json"); log = load(lp, [])
    log += [{"action": "replaced", "file": os.path.basename(vf), "dropped": None, "added": qid, "reason": "top-up", "round": TAG} for qid in added]
    json.dump(log, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{part}__{gi} {u['filter']}: 合格 {len(accepted)} / 不合格 {len(rejected)} → verified に {len(added)} 問足して {len(cur)} 問、予備 {len(sur)} 問")
    for r in rejected: print("   ✗", r[0], "; ".join(r[1])[:100])
    if len(cur) < L.TARGET_ADD: print(f"   ⚠️ まだ {L.TARGET_ADD - len(cur)} 問不足")
else:
    print("usage: topup.py prep|score <part> <gi>"); sys.exit(2)
