#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲検合格の問題からカードごとに 30 問を選んで verified/<part>__<gi>.json に書く。余りは blind/surplus_<part>__<gi>.json へ。
    python3 scripts/kosei_dojo/eibunpo_v2/select_verified.py <part>
選び方: 「読まずに当たる」兆候 (部分最多・単独最長・単独最短) のある問題を後回しにし、form (出題形式) を
ラウンドロビンで散らして 30 問。合格が 30 未満なら全部採用して不足を表示 (top-up の対象)。
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

BL = os.path.join(L.HERE, "blind"); DR = os.path.join(L.HERE, "drafts"); VD = os.path.join(L.HERE, "verified")
part = sys.argv[1]
ONLY = None
if "--only" in sys.argv:   # 指定した gi だけ選び直す (他の単元の verified/ ＝レビュー適用済みを上書きしないため)
    ONLY = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
units = {u["gi"]: u for u in L.load_units() if u["part"] == part}
accept = json.load(open(os.path.join(BL, f"accept_{part}.json"), encoding="utf-8"))
lint = json.load(open(os.path.join(BL, f"lint_{part}.json"), encoding="utf-8"))
KEEP = ("subject", "part", "filter", "unit", "stem", "passage", "choices", "answer_index", "explanation", "form", "level")

short = []
for gi_s, rep in sorted(accept.items(), key=lambda kv: int(kv[0])):
    gi = int(gi_s); u = units[gi]
    if ONLY is not None and gi not in ONLY: continue
    data = json.load(open(os.path.join(DR, f"{part}__{gi}.json"), encoding="utf-8"))
    if isinstance(data, dict): data = data.get("questions", [])
    acc = set(rep["accepted"])
    warn_ids = {w[0] for w in lint[gi_s]["warn"] if w[0] != "*"}
    cands = []
    for n, q in enumerate(data):
        qid = f"{part}{gi}-{n:02d}"
        if qid not in acc: continue
        q = {k: q.get(k, "") for k in KEEP}
        q["filter"] = u["filter"]; q["subject"] = u["subject"]; q["part"] = part   # unit は draft の「<tag>(細目)」をそのまま残す
        q["_id"] = qid
        penalty = (3 if qid in warn_ids else 0) + (1 if L.longest_tell(q) else 0) + (1 if L.shortest_tell(q) else 0)
        cands.append((penalty, n, q))
    cands.sort(key=lambda t: (t[0], t[1]))
    by_form = collections.OrderedDict()
    for c in cands: by_form.setdefault(c[2].get("form") or "?", []).append(c)
    chosen, rest = [], []
    while len(chosen) < L.TARGET_ADD and any(by_form.values()):
        for f in list(by_form):
            if by_form[f] and len(chosen) < L.TARGET_ADD: chosen.append(by_form[f].pop(0))
    for f in by_form: rest += by_form[f]
    chosen.sort(key=lambda t: t[1])
    out = [{k: v for k, v in q.items()} for _, _, q in chosen]
    sur = [{k: v for k, v in q.items()} for _, _, q in rest]
    json.dump(out, open(os.path.join(VD, f"{part}__{gi}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(sur, open(os.path.join(BL, f"surplus_{part}__{gi}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    forms = collections.Counter(q.get("form") for q in out)
    flag = "" if len(out) >= L.TARGET_ADD else f"  ⚠️不足 {L.TARGET_ADD - len(out)}"
    if len(out) < L.TARGET_ADD: short.append((gi, u["filter"], L.TARGET_ADD - len(out)))
    print(f"{part}__{gi:<2} {u['filter']:<10} 合格 {len(cands):2} → 採用 {len(out):2} 余り {len(sur):2}{flag}  forms={len(forms)}")
if short: print("不足:", short)
else: print(f"全カード {L.TARGET_ADD} 問そろいました")
