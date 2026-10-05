#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drafts/<part>__<gi>.json (作問の生出力) を機械検査し、盲検用の blind ビューと key を書く。
    python3 scripts/kosei_dojo/eibunpo_v2/lint_drafts.py [part ...]
出力 (blind/ は .gitignore 対象):
  blind/<part>__<gi>.blind.json  [{id, stem, passage, choices}]   … 正解・解説を伏せた盲検ビュー
  blind/<part>__<gi>.key.json    {id: {answer_text, answer_index, filter}}
  blind/lint_<part>.json         {gi: {kept:[ids], dropped:[[id, reason]], warn:[...]}}
除外 (drop): 形式不正 (unit の形・空所 1 か所・位置語)・既存プール/単元ドリル/同一ドラフト内と同じ設問・他カード名が設問文/選択肢に。
警告 (warn): 正解が単独最長/最短・部分最多で当たる・解説に他カード名・正解の語が設問文にも出る・形式の偏り。
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

BL = os.path.join(L.HERE, "blind")
DR = os.path.join(L.HERE, "drafts")
units = L.load_units()
by_gi = {u["gi"]: u for u in units}
ex = L.existing_questions()
parts = [p for p in sys.argv[1:] if p in L.PARTS] or L.PARTS

TO_RE = re.compile(r"^[Tt]o [a-z]+")
WORD = re.compile(r"[A-Za-z']+")


def other_names(part, u):
    """同じ part の他カードの filter と tag (bank の LIKE 予算を食う語)。自分の名前を含む/含まれる語は除く。"""
    names = set()
    for o in units:
        if o["part"] != part or o["gi"] == u["gi"]: continue
        names.update([o["filter"], o["tag"]])
    return sorted(n for n in names if n not in u["tag"] and u["tag"] not in n and n not in u["filter"] and u["filter"] not in n)


def answer_in_stem(q):
    """正解の語が設問文 (空所の外) にそのまま出ていて、誤答の語は出ていない → 読まずに当たる手がかり。"""
    stem_words = {w.lower() for w in WORD.findall(q["stem"])}
    def words(c): return {w.lower() for w in WORD.findall(c)} - {"to", "a", "an", "the", "of", "in", "be", "is", "are", "was", "were", "been", "being", "not", "it", "that"}
    cw = words(q["choices"][q["answer_index"]])
    if not cw or not cw <= stem_words: return False
    return not any(words(c) <= stem_words for i, c in enumerate(q["choices"]) if i != q["answer_index"] and words(c))


for part in parts:
    ex_sigs = {L.sig(q["stem"], q["choices"]) for q in ex[part]}
    ex_stems = {L.stem_key(q["stem"]) for q in ex[part]}
    drill_fp = os.path.join(BL, f"drill_stems_{part}.json")
    drill = json.load(open(drill_fp, encoding="utf-8")) if os.path.exists(drill_fp) else {}
    drill_stems = {L.stem_key(s) for v in drill.values() for s in v}
    report = {}
    for fp in sorted(glob.glob(os.path.join(DR, f"{part}__*.json")), key=lambda p: int(os.path.basename(p).split("__")[1].split(".")[0])):
        gi = int(os.path.basename(fp).split("__")[1].split(".")[0])
        u = by_gi.get(gi)
        if not u or u["part"] != part:
            print(f"❓ {os.path.basename(fp)}: gi {gi} は {part} のカードでない → skip"); continue
        try:
            data = json.load(open(fp, encoding="utf-8"))
        except Exception as e:
            print(f"⚠️ {os.path.basename(fp)}: JSON 読めない: {e}"); continue
        if isinstance(data, dict) and "questions" in data: data = data["questions"]
        if not isinstance(data, list):
            print(f"⚠️ {os.path.basename(fp)}: 配列でない"); continue
        kept, dropped, warn = [], [], []
        seen_sig, seen_stem = set(), set()
        blind, key = [], {}
        n_long = n_short = n_conv = n_to = n_ais = 0
        forms = collections.Counter(); levels = collections.Counter(); ans = collections.Counter(); subs = collections.Counter()
        others = other_names(part, u)
        topic_hits = collections.Counter()
        for n, q in enumerate(data):
            qid = f"{part}{gi}-{n:02d}"
            errs = []
            if not isinstance(q, dict):
                dropped.append([qid, "オブジェクトでない"]); continue
            q.setdefault("filter", u["filter"]); q.setdefault("passage", "")
            if not L.validate_question(q, u, errs, qid):
                dropped.append([qid, "; ".join(e for _, e in errs)]); continue
            s = L.sig(q["stem"], q["choices"]); sk = L.stem_key(q["stem"])
            cs = L.content_stem(q["stem"])
            if s in ex_sigs or (cs and sk in ex_stems):
                dropped.append([qid, "既存プールと同一 (stem/選択肢)"]); continue
            if cs and sk in drill_stems:
                dropped.append([qid, "単元ドリルと同じ設問文"]); continue
            if s in seen_sig or (cs and sk in seen_stem):
                dropped.append([qid, "ドラフト内で同一"]); continue
            hit_stem = [t for t in others if t in q["stem"] or any(t in c for c in q["choices"])]
            if hit_stem:
                dropped.append([qid, f"設問文/選択肢に他カード名 {hit_stem}"]); continue
            seen_sig.add(s); seen_stem.add(sk)
            # 警告系
            if L.longest_tell(q): n_long += 1
            if L.shortest_tell(q): n_short += 1
            if L.converges(q["choices"], q["answer_index"]): n_conv += 1; warn.append([qid, "部分最多で当たる (2×2 に)"])
            if TO_RE.match(q["choices"][q["answer_index"]]): n_to += 1
            if answer_in_stem(q): n_ais += 1; warn.append([qid, "正解の語が設問文にもある (誤答の語は無い)"])
            for t in others:
                if t in q["explanation"]: topic_hits[t] += 1
            forms[q.get("form", "?")] += 1; levels[q.get("level", "?")] += 1; ans[q["answer_index"]] += 1
            subs[L.unit_parts(q["unit"])[1]] += 1
            kept.append(qid)
            blind.append({"id": qid, "stem": q["stem"], "passage": "", "choices": q["choices"]})
            key[qid] = {"answer_text": q["choices"][q["answer_index"]], "answer_index": q["answer_index"], "filter": u["filter"]}
        nk = max(1, len(kept))
        if n_long / nk > 0.4: warn.append(["*", f"正解が単独最長 {n_long}/{len(kept)} (40%超)"])
        if n_short / nk > 0.4: warn.append(["*", f"正解が単独最短 {n_short}/{len(kept)}"])
        if n_to / nk > 0.5: warn.append(["*", f"正解が to+原形 {n_to}/{len(kept)}"])
        dup_sub = {k: v for k, v in subs.items() if v > 3}
        if dup_sub: warn.append(["*", f"同じ細目が 4 問以上: {dup_sub}"])
        for t, c in topic_hits.items():
            warn.append(["*", f"解説に他カード名『{t}』が {c} 問 (LIKE 予算を食う)"])
        json.dump(blind, open(os.path.join(BL, f"{part}__{gi}.blind.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(key, open(os.path.join(BL, f"{part}__{gi}.key.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        report[gi] = {"filter": u["filter"], "kept": kept, "dropped": dropped, "warn": warn,
                      "stats": {"longest": n_long, "shortest": n_short, "converge": n_conv, "to_form": n_to, "answer_in_stem": n_ais,
                                "forms": dict(forms), "levels": dict(levels), "subtopics": len(subs), "answer_dist": {str(k): v for k, v in sorted(ans.items())}}}
        flag = "" if not dropped else f"  drop {len(dropped)}"
        print(f"{part}__{gi:<2} {u['filter']:<6} 作問 {len(data):2} → 残 {len(kept):2}{flag} | 最長 {n_long} 最短 {n_short} 収束 {n_conv} to形 {n_to} 語漏れ {n_ais} | forms {len(forms)} 細目 {len(subs)} | 他カード語 {dict(topic_hits) if topic_hits else '-'}")
        for d in dropped: print("     drop", d[0], d[1][:100])
        for w in warn:
            if w[0] == "*": print("     warn", w[1])
    json.dump(report, open(os.path.join(BL, f"lint_{part}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
