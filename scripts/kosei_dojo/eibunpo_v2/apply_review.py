#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立レビューの指摘を verified/ に適用する。指し示しは stem (本文) の完全一致。添字は使わない。
    python3 scripts/kosei_dojo/eibunpo_v2/apply_review.py <part>
入力: blind/review_<part>_*.json … [{stem, action: "drop" | "fix_expl" | "fix_choice" | "fix_stem" | "fix_unit" | "note", reason, explanation?, choices?, answer_text?, stem_new?, unit_new?}]
  drop       その問題を外し、余り (blind/surplus_<part>__<gi>.json・盲検合格済) から同じ単元に 1 問補充
  fix_expl   解説だけ差し替える (正解の本文を含むこと・盲検は有効のまま)
  fix_choice 選択肢を差し替える (正解の本文は不変。新しい選択肢は choices か choices_new。stem が同一の正誤問題は old_choices か _id で絞る)
             (★盲検をやり直す必要がある → 既定では適用せず警告のみ。--allow-choice で適用)
  fix_stem   設問文を書きかえる {stem_new, explanation?, choices?, answer_text?}。正解の本文は変えない
             (★盲検をやり直した版だけ。--allow-choice で適用)
  fix_unit   unit の細目だけ書きかえる {unit_new} (tag は不変)
  note       表示するだけ (適用しない)
  stem が重複するときは passage / choices / _id で絞る。
一致する stem が 0 件・2 件以上なら assert で止める。
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

BL = os.path.join(L.HERE, "blind"); VD = os.path.join(L.HERE, "verified")
part = sys.argv[1]
allow_choice = "--allow-choice" in sys.argv
items = []
review_files = L.own_part_files(sorted(glob.glob(os.path.join(BL, f"review_{part}_*.json"))), part, "review_")   # applied_ 済みと別 part (r_grammar_unit) は対象外
for fp in review_files:
    d = json.load(open(fp, encoding="utf-8"))
    if isinstance(d, dict): d = d.get("items") or d.get("findings") or []
    items += [x for x in d if isinstance(x, dict) and x.get("stem")]
print(f"指摘 {len(items)} 件 ({len(review_files)} ファイル)")

files = {}
for fp in sorted(glob.glob(os.path.join(VD, f"{part}__*.json"))):
    files[fp] = json.load(open(fp, encoding="utf-8"))


def find(stem):
    k = L.stem_key(stem); hits = []
    for fp, qs in files.items():
        for i, q in enumerate(qs):
            if L.stem_key(q["stem"]) == k: hits.append((fp, i))
    return hits


n_drop = n_fix = n_skip = 0
dropped_keys = set()
LOG = []   # このラウンドで入れ替え・書き換えた問題の _id (後で再レビューに回す)
notes = [it for it in items if it.get("action") == "note"]
items = [it for it in items if it.get("action") != "note"]
for it in items:
    hits = find(it["stem"])
    if len(hits) > 1 and it.get("passage"):
        pk = L.norm_ws(it["passage"]); hits = [(fp, i) for fp, i in hits if L.norm_ws(files[fp][i].get("passage", "")) == pk]
    # 絞り込みに使う選択肢: fix_choice は choices が「新しい選択肢」なので old_choices を使う (正誤問題は stem が同一のため)
    dis = it.get("old_choices") or (it.get("choices") if it.get("action") != "fix_choice" else None)
    if len(hits) > 1 and dis:
        ck = sorted(L.norm_ws(c) for c in dis); hits = [(fp, i) for fp, i in hits if sorted(L.norm_ws(c) for c in files[fp][i]["choices"]) == ck]
    if len(hits) > 1 and it.get("_id"):
        hits = [(fp, i) for fp, i in hits if files[fp][i].get("_id") == it["_id"]]
    if not hits and L.stem_key(it["stem"]) in dropped_keys:
        print(f"  (既に drop 済) {it['stem'][:40]!r}"); continue
    assert len(hits) == 1, f"stem の一致が {len(hits)} 件: {it['stem'][:60]!r}"
    fp, i = hits[0]; q = files[fp][i]; act = it.get("action")
    if act == "drop":
        dropped_keys.add(L.stem_key(q["stem"])); files[fp].pop(i); n_drop += 1
        gi = os.path.basename(fp).split("__")[1].split(".")[0]
        sp = os.path.join(BL, f"surplus_{part}__{gi}.json")
        sur = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else []
        if sur:
            add = sur.pop(0); files[fp].append(add); json.dump(sur, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            LOG.append({"action": "replaced", "file": os.path.basename(fp), "dropped": q.get("_id"), "added": add.get("_id"), "reason": it.get("reason", "")})
            print(f"  drop+補充 {os.path.basename(fp)}: {it['stem'][:40]!r} ← {it.get('reason','')[:60]}")
        else:
            print(f"  drop (補充なし・不足) {os.path.basename(fp)}: {it['stem'][:40]!r} ← {it.get('reason','')[:60]}")
    elif act == "fix_expl":
        new = str(it.get("explanation", "")).strip()
        correct = q["choices"][q["answer_index"]]
        assert new and correct in new, f"新しい解説に正解本文が無い: {it['stem'][:40]!r}"
        assert not L.POSITIONAL.search(new), f"新しい解説に位置語: {it['stem'][:40]!r}"
        q["explanation"] = L.rebuild_expl(q["unit"], correct, new); n_fix += 1
        LOG.append({"action": "fix_expl", "file": os.path.basename(fp), "id": q.get("_id")})
        print(f"  fix_expl {os.path.basename(fp)}: {it['stem'][:40]!r}")
    elif act == "fix_stem":
        # 設問文 (と必要なら選択肢) を書きかえる。正解の本文は変えない。★盲検をやり直した版だけを渡すこと
        if not allow_choice:
            n_skip += 1; print(f"  ⚠️ fix_stem は盲検やり直しが要るので未適用: {it['stem'][:40]!r}"); continue
        new_stem = str(it.get("stem_new", "")).strip(); assert new_stem, it
        ch = it.get("choices_new") or it.get("choices") or q["choices"]; at = L.norm_ws(it.get("answer_text") or q["choices"][q["answer_index"]])
        assert len(ch) == 4 and len({L.norm_ws(c) for c in ch}) == 4
        assert at == L.norm_ws(q["choices"][q["answer_index"]]), "fix_stem で正解の本文が変わっている"
        q["stem"] = new_stem; q["choices"] = ch; q["answer_index"] = [L.norm_ws(c) for c in ch].index(at)
        if it.get("explanation"): q["explanation"] = L.rebuild_expl(q["unit"], ch[q["answer_index"]], it["explanation"])
        n_fix += 1
        LOG.append({"action": "fix_stem", "file": os.path.basename(fp), "id": q.get("_id")})
        print(f"  fix_stem {os.path.basename(fp)}: {it['stem'][:40]!r}")
    elif act == "fix_unit":
        new_unit = str(it.get("unit_new", "")).strip(); up = L.unit_parts(new_unit)
        assert up and up[0] == L.unit_parts(q["unit"])[0], f"fix_unit は細目だけ (tag は不変): {new_unit!r}"
        q["unit"] = new_unit; q["explanation"] = L.rebuild_expl(new_unit, q["choices"][q["answer_index"]], q["explanation"]); n_fix += 1
        LOG.append({"action": "fix_unit", "file": os.path.basename(fp), "id": q.get("_id")})
        print(f"  fix_unit {os.path.basename(fp)}: {it['stem'][:40]!r} → {new_unit}")
    elif act == "fix_choice":
        if not allow_choice:
            n_skip += 1; print(f"  ⚠️ fix_choice は盲検やり直しが要るので未適用: {it['stem'][:40]!r} ← {it.get('reason','')[:60]}"); continue
        ch = it.get("choices_new") or it.get("choices"); at = L.norm_ws(it.get("answer_text", ""))
        assert isinstance(ch, list) and len(ch) == 4 and len({L.norm_ws(c) for c in ch}) == 4
        assert at == L.norm_ws(q["choices"][q["answer_index"]]), "fix_choice で正解の本文が変わっている"
        idx = [L.norm_ws(c) for c in ch].index(at)
        q["choices"] = ch; q["answer_index"] = idx
        q["explanation"] = L.rebuild_expl(q["unit"], ch[idx], it.get("explanation") or q["explanation"]); n_fix += 1
        LOG.append({"action": "fix_choice", "file": os.path.basename(fp), "id": q.get("_id")})
        print(f"  fix_choice {os.path.basename(fp)}: {it['stem'][:40]!r}")
    else:
        n_skip += 1; print(f"  ? action 不明 {act!r}: {it['stem'][:40]!r}")
for fp, qs in files.items():
    json.dump(qs, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import time
if LOG:
    lp = os.path.join(BL, f"apply_log_{part}.json")
    prev = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else []
    json.dump(prev + [dict(x, round=len(review_files) and os.path.basename(review_files[0])) for x in LOG], open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 二重適用を防ぐ: 処理したレビューファイルは applied_ に改名 (drop 済の stem が見つからず assert で止まるため)
for fp in review_files:
    os.rename(fp, os.path.join(BL, "applied_" + os.path.basename(fp)))
print(f"適用: drop {n_drop} / fix {n_fix} / 未適用 {n_skip}")
for n in notes: print(f"  note: {n.get('stem','')[:40]!r} ← {n.get('reason','')[:100]}")
for fp, qs in files.items():
    if len(qs) != L.TARGET_ADD: print(f"  ⚠️ {os.path.basename(fp)} は {len(qs)} 問 ({L.TARGET_ADD} でない)")
