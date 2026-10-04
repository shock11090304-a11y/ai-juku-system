#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drafts/<part>__<gi>.json (作問の生出力) を機械検査し、盲検用の blind ビューと key を書く。
    python3 scripts/chugaku_dojo/expand_v3/lint_drafts.py [part ...]
出力 (blind/ は .gitignore 対象):
  blind/<part>__<gi>.blind.json  [{id, stem, passage, choices}]   … 正解・解説を伏せた盲検ビュー
  blind/<part>__<gi>.key.json    {id: {answer_text, answer_index, filter}}
  blind/lint_<part>.json         {gi: {kept:[ids], dropped:[[id, reason]], warn:[...]}}
除外 (drop): 形式不正・既存プール/同一ドラフト内と (stem, choices) または stem が同一・位置語。
警告 (warn): 正解が単独最長/最短の比率・部分最多で当たる (convergence)・他単元名の混入・形の偏り。
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
DR = os.path.join(L.HERE, "drafts")
units = L.load_units()
by_gi = {u["gi"]: u for u in units}
ex = L.existing_questions()
parts = [p for p in sys.argv[1:] if p in L.PARTS] or L.PARTS

TO_RE = re.compile(r"^[Tt]o [a-z]+")


def other_topics(part, filt):
    names = [f for f in L.filters_of(part, units) if f != filt]
    if part == "eng":
        names += [t for t in L.DOJO_ONLY_ENG if t != filt]
        if filt == "時制":
            names = [n for n in names if n not in ("過去形", "未来形")]
    # 自分の単元名を含む他単元名 (「不定詞・動名詞」⊃「不定詞」等) は除く
    return [n for n in names if n not in filt and filt not in n]


for part in parts:
    ex_sigs = {L.sig(q["stem"], q["choices"]) for q in ex[part]}
    ex_stems = {L.stem_key(q["stem"]) for q in ex[part]}
    ex_passages = {L.norm_ws(q.get("passage", "")) for q in ex[part] if q.get("passage")}
    report = {}
    for fp in sorted(glob.glob(os.path.join(DR, f"{part}__*.json"))):
        gi = int(os.path.basename(fp).split("__")[1].split(".")[0])
        u = by_gi.get(gi)
        if not u or u["part"] != part:
            print(f"❓ {os.path.basename(fp)}: gi {gi} は {part} の単元でない → skip"); continue
        try:
            data = json.load(open(fp, encoding="utf-8"))
        except Exception as e:
            print(f"⚠️ {os.path.basename(fp)}: JSON 読めない: {e}"); continue
        if isinstance(data, dict) and "questions" in data:
            data = data["questions"]
        if not isinstance(data, list):
            print(f"⚠️ {os.path.basename(fp)}: 配列でない"); continue
        kept, dropped, warn = [], [], []
        seen_sig, seen_stem = set(), set()
        blind, key = [], {}
        n_long = n_short = n_conv = n_to = 0
        forms = collections.Counter(); levels = collections.Counter(); ans = collections.Counter()
        others = other_topics(part, u["filter"])
        topic_hits = collections.Counter()
        for n, q in enumerate(data):
            qid = f"{part}{gi}-{n:02d}"
            errs = []
            if not isinstance(q, dict):
                dropped.append([qid, "オブジェクトでない"]); continue
            q.setdefault("filter", u["filter"]); q.setdefault("unit", q["filter"]); q.setdefault("passage", "")
            if q["filter"] != u["filter"]:
                dropped.append([qid, f"filter が単元と違う: {q['filter']!r}"]); continue
            if not L.validate_question(q, {u["filter"]}, errs, qid):
                dropped.append([qid, "; ".join(e for _, e in errs)]); continue
            if u["reading"] and not str(q.get("passage", "")).strip():
                dropped.append([qid, "読解なのに本文が空"]); continue
            if not u["reading"] and str(q.get("passage", "")).strip():
                dropped.append([qid, "非読解なのに本文あり"]); continue
            s = L.sig(q["stem"], q["choices"]); sk = L.stem_key(q["stem"])
            cs = L.content_stem(q["stem"]) and not u["reading"]
            if s in ex_sigs or (cs and sk in ex_stems):
                dropped.append([qid, "既存プールと同一 (stem/選択肢)"]); continue
            if s in seen_sig or (cs and sk in seen_stem):
                dropped.append([qid, "ドラフト内で同一"]); continue
            if u["reading"] and L.norm_ws(q["passage"]) in ex_passages:
                dropped.append([qid, "既存プールと同じ本文"]); continue
            seen_sig.add(s); seen_stem.add(sk)
            # 警告系
            if L.longest_tell(q): n_long += 1
            if L.shortest_tell(q): n_short += 1
            if L.converges(q["choices"], q["answer_index"]): n_conv += 1; warn.append([qid, "部分最多で当たる (2×2 に)"])
            if part == "eng" and TO_RE.match(q["choices"][q["answer_index"]]): n_to += 1
            blob = q["stem"] + " " + " ".join(q["choices"]) + " " + q["explanation"]
            for t in others:
                if t in blob: topic_hits[t] += 1
            forms[q.get("form", "?")] += 1; levels[q.get("level", "?")] += 1; ans[q["answer_index"]] += 1
            kept.append(qid)
            blind.append({"id": qid, "stem": q["stem"], "passage": q.get("passage", ""), "choices": q["choices"]})
            key[qid] = {"answer_text": q["choices"][q["answer_index"]], "answer_index": q["answer_index"], "filter": u["filter"]}
        nk = max(1, len(kept))
        if n_long / nk > 0.4: warn.append(["*", f"正解が単独最長 {n_long}/{len(kept)} (40%超)"])
        if n_short / nk > 0.4: warn.append(["*", f"正解が単独最短 {n_short}/{len(kept)}"])
        if part == "eng" and n_to / nk > 0.5: warn.append(["*", f"正解が to+原形 {n_to}/{len(kept)}"])
        for t, c in topic_hits.items():
            warn.append(["*", f"他単元名『{t}』が {c} 問に含まれる"])
        json.dump(blind, open(os.path.join(BL, f"{part}__{gi}.blind.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(key, open(os.path.join(BL, f"{part}__{gi}.key.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        report[gi] = {"filter": u["filter"], "kept": kept, "dropped": dropped, "warn": warn,
                      "stats": {"longest": n_long, "shortest": n_short, "converge": n_conv, "to_form": n_to,
                                "forms": dict(forms), "levels": dict(levels), "answer_dist": {str(k): v for k, v in sorted(ans.items())}}}
        flag = "" if not dropped else f"  drop {len(dropped)}"
        print(f"{part}__{gi:<2} {u['filter']:<10} 作問 {len(data):2} → 残 {len(kept):2}{flag} | 最長 {n_long} 最短 {n_short} 収束 {n_conv}"
              + (f" to形 {n_to}" if part == 'eng' else "") + f" | forms {len(forms)} | 他単元語 {dict(topic_hits) if topic_hits else '-'}")
        for d in dropped: print("     drop", d[0], d[1][:90])
        for w in warn:
            if w[0] == "*": print("     warn", w[1])
    json.dump(report, open(os.path.join(BL, f"lint_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
