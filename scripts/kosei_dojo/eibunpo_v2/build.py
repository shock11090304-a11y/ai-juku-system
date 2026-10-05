#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verified/*.json → exam_questions の行 (question_data JSON) を組み立て、ゲートをかけて build/ に書く。
    python3 scripts/kosei_dojo/eibunpo_v2/build.py [--partial]
出力:
  build/rows.json   … [{part_key, question_data}] (6 小問/行。question_data は既存の英文法プールと同じ形 + source)
  build/flat.json   … 全小問 (正解つき・検証と post_check の照合用)
  build/blind.json  … 全小問 (正解・解説なし)
  build/report.json … 件数・正解位置・tell の集計
正解位置: カードごとに stem の md5 順で 0,1,2,3 を振る (均等・決定的・保存順に周期を作らない)。
解説は正解テキスト参照 (【単元】<unit>。正解は「…」。) なので、選択肢を入れ替えても壊れない。
★ゲート NG のときは build/ を書き換えない (落ちた rows.json がそのまま本番へ入るのを防ぐ)。
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

VD = os.path.join(L.HERE, "verified"); OUT = os.path.join(L.HERE, "build"); BL = os.path.join(L.HERE, "blind")


def load_verified():
    units = L.load_units(); by_gi = {u["gi"]: u for u in units}
    qs = []
    for fp in sorted(glob.glob(os.path.join(VD, "*.json"))):
        part, gi = os.path.basename(fp).split("__")[0], int(os.path.basename(fp).split("__")[1].split(".")[0])
        for q in json.load(open(fp, encoding="utf-8")):
            q = dict(q); q["_gi"] = gi; q["_file"] = os.path.basename(fp); q["_unit"] = by_gi.get(gi); q["_part"] = part
            qs.append(q)
    return units, qs


def assign_positions(qs):
    by_gi = collections.defaultdict(list)
    for q in qs: by_gi[q["_gi"]].append(q)
    for gi, group in by_gi.items():
        ranked = sorted(group, key=lambda q: L.md5(q["stem"]))
        for rank, q in enumerate(ranked):
            want = rank % 4; cur = q["answer_index"]
            if cur != want:
                ch = list(q["choices"]); ch[cur], ch[want] = ch[want], ch[cur]
                q["choices"] = ch; q["answer_index"] = want


def drill_stem_keys(part):
    """単元ドリル (grammar_questions) の設問文。blind/ のキャッシュは .gitignore なので、CI でも効くように seed-data からも集める。"""
    keys = {L.stem_key(s) for v in L.drill_stems().values() for s in v}
    fp = os.path.join(BL, f"drill_stems_{part}.json")
    if os.path.exists(fp):
        keys |= {L.stem_key(s) for v in json.load(open(fp, encoding="utf-8")).values() for s in v}
    return keys


def gates(units, qs, strict=True, partial=False):
    errs, warns = [], []
    by_gi = {u["gi"]: u for u in units}
    ex = L.existing_questions(); base = L.baseline_rows()
    for part in L.PARTS:
        ex_sigs = {L.sig(q["stem"], q["choices"]) for q in ex[part]}
        ex_stems = {L.stem_key(q["stem"]) for q in ex[part]}
        dr_stems = drill_stem_keys(part)
        mine = [q for q in qs if q["_part"] == part]
        seen_sig, seen_stem = {}, {}
        for q in mine:
            u = by_gi.get(q["_gi"]); where = f"{q['_file']}:{q['stem'][:30]!r}"
            if not u or u["part"] != part:
                errs.append((where, "ファイル名の gi がカードと合わない")); continue
            L.validate_question(q, u, errs, where)
            c_ok = q["choices"][q["answer_index"]] if 0 <= q.get("answer_index", -1) < len(q["choices"]) else ""
            if c_ok and L.rebuild_expl(q["unit"], c_ok, q["explanation"]) != q["explanation"]:
                errs.append((where, "解説の接頭辞を作り直すと変わる (strip_prefix の取りこぼし)"))
            if "」" in c_ok:
                h = L.expl_head(q["unit"], c_ok)
                if q["explanation"].startswith(h) and q["explanation"][len(h):].startswith(c_ok[c_ok.index("」") + 1:] + "」"):
                    errs.append((where, "解説の頭に正解の後ろ半分が重複している"))
            s = L.sig(q["stem"], q["choices"]); sk = L.stem_key(q["stem"]); cs = L.content_stem(q["stem"])
            if s in ex_sigs: errs.append((where, "既存プールと同一の設問 (stem+選択肢)"))
            elif cs and sk in ex_stems: errs.append((where, "既存プールと同一の設問文"))
            elif cs and sk in dr_stems: errs.append((where, "単元ドリルと同一の設問文"))
            if s in seen_sig: errs.append((where, f"v2 内で同一の設問: {seen_sig[s]}"))
            elif cs and sk in seen_stem: errs.append((where, f"v2 内で同一の設問文: {seen_stem[sk]}"))
            seen_sig[s] = q["_file"]; seen_stem[sk] = q["_file"]
            if q["explanation"].count("正解は「") != 1: errs.append((where, "解説の「正解は「」が 1 回でない"))
        for u in [u for u in units if u["part"] == part]:
            g = [q for q in mine if q["_gi"] == u["gi"]]
            if not g:
                if not partial: errs.append((f"{part}__{u['gi']}", f"カード『{u['filter']}』の問題が 0 件"))
                continue
            if len(g) != L.TARGET_ADD: warns.append((f"{part}__{u['gi']}", f"{u['filter']}: {len(g)} 問 (目標 {L.TARGET_ADD})"))
            dist = collections.Counter(q["answer_index"] for q in g)
            if max(dist.values()) - min([dist.get(i, 0) for i in range(4)]) > 1:
                errs.append((f"{part}__{u['gi']}", f"正解位置が不均等 {dict(dist)}"))
            seq = [q["answer_index"] for q in g]
            if len(seq) >= 8 and seq == [i % 4 for i in range(len(seq))]:
                errs.append((f"{part}__{u['gi']}", "正解位置が保存順に完全周期"))
            n_long = sum(L.longest_tell(q) for q in g); n_short = sum(L.shortest_tell(q) for q in g)
            if n_long > len(g) * 0.5: warns.append((f"{part}__{u['gi']}", f"{u['filter']}: 正解が単独最長 {n_long}/{len(g)}"))
            if n_short > len(g) * 0.5: warns.append((f"{part}__{u['gi']}", f"{u['filter']}: 正解が単独最短 {n_short}/{len(g)}"))
            for q in g:
                if L.converges(q["choices"], q["answer_index"]):
                    warns.append((f"{part}__{u['gi']}", f"部分最多で当たる: {q['stem'][:40]!r} / " + " | ".join(q["choices"])))
            subs = collections.Counter(L.unit_parts(q["unit"])[1] for q in g if L.unit_parts(q["unit"]))
            if subs and subs.most_common(1)[0][1] > 3: warns.append((f"{part}__{u['gi']}", f"同じ細目が 4 問以上: {subs.most_common(2)}"))
        # bank の LIKE 予算: カード名 (filter) を含む行が 既存+新規 で 50 行を超えると、古い行が配信から押し出される。
        #   既存の行数は seed-data の近似。塾長の端末で取った本番の基準 (kosei_baseline) があれば大きい方を使う。
        new_rows = rows_for(part, mine, by_gi)
        old_rows = L.existing_rows_text(part)
        for u in [u for u in units if u["part"] == part]:
            f = u["filter"]; lim = L.bank_limit()
            n_old = sum(1 for r in old_rows if f in r)
            n_new = sum(1 for r in new_rows if f in json.dumps(r["question_data"], ensure_ascii=False))
            own_new = sum(1 for r in new_rows if r["_filter"] == f)
            if n_old + n_new > lim:   # seed-data の近似で超える = 自分たちの行だけで窓を埋める → NG
                errs.append((f"{part}/{f}", f"カード名を含む行が {n_old}+{n_new}={n_old+n_new} > {lim} (画面が bank から取る行数) → 古い行が配信されなくなる"))
            elif n_new - own_new > 0:
                warns.append((f"{part}/{f}", f"他カードの新規行 {n_new - own_new} 行に『{f}』が含まれる (LIKE 予算 {n_old+n_new}/{lim})"))
            if (part, f) in base and base[(part, f)] + n_new > lim:
                # 本番は seed より行が多い (AI の古い行 + 2026-08-18 のタグ付け)。超えるぶんは insert.py が
                # 「押し出されるのが手作りの行か AI の行か」を本番で判定して止める/進めるので、ここは警告にとどめる。
                warns.append((f"{part}/{f}", f"[本番基準] {base[(part, f)]} 行 + 新規 {n_new} 行 = {base[(part, f)] + n_new} > {lim} → insert.py が押し出される行を確認する"))
        if not base: warns.append((part, "本番の基準 (~/Desktop/kosei_baseline_*.json) が無いので LIKE 予算は seed-data の近似で判定"))
    return errs, warns


def rows_for(part, mine, by_gi):
    """[{part_key, _filter, question_data}]。question_data は既存プールと同じキー + source。"""
    rows = []
    for gi in sorted({q["_gi"] for q in mine}):
        u = by_gi[gi]; g = [q for q in mine if q["_gi"] == gi]
        for i in range(0, len(g), L.CHUNK):
            chunk = g[i:i + L.CHUNK]
            qd = {"passage": "", "subject": L.SUBJECT, "univ_simulated": L.UNIV_SIMULATED, "year_simulated": L.YEAR_SIMULATED, "source": L.SOURCE,
                  "questions": [{"id": f"q{k+1}", "type": "multiple_choice", "stem": q["stem"], "choices": q["choices"],
                                 "answer": int(q["answer_index"]), "unit": q["unit"], "explanation": q["explanation"]} for k, q in enumerate(chunk)]}
            rows.append({"part_key": part, "_filter": u["filter"], "question_data": qd})
    return rows


def main():
    partial = "--partial" in sys.argv
    units, qs = load_verified()
    if not qs:
        print("verified/ が空です"); sys.exit(1)
    assign_positions(qs)
    for q in qs:
        q["explanation"] = L.rebuild_expl(q["unit"], q["choices"][q["answer_index"]], q["explanation"])
    errs, warns = gates(units, qs, partial=partial)
    by_gi = {u["gi"]: u for u in units}
    rows = []
    for part in L.PARTS: rows += rows_for(part, [q for q in qs if q["_part"] == part], by_gi)
    flat, blind = [], []
    for ri, r in enumerate(rows):
        for q in r["question_data"]["questions"]:
            gid = f"r{ri:03d}:{q['id']}"
            flat.append({"gid": gid, "part": r["part_key"], "filter": r["_filter"], "unit": q["unit"], "stem": q["stem"], "choices": q["choices"],
                         "answer": q["answer"], "explanation": q["explanation"]})
            blind.append({"gid": gid, "part": r["part_key"], "filter": r["_filter"], "stem": q["stem"], "choices": q["choices"]})
    per_part = collections.Counter(f["part"] for f in flat); dist = collections.Counter(str(f["answer"]) for f in flat)
    print(f"小問 {len(flat)} / 行 {len(rows)}  " + " ".join(f"{p}={per_part[p]}" for p in L.PARTS))
    print("正解位置分布: " + " ".join(f"{k}:{dist[k]}" for k in "0123"))
    for w in warns: print("  warn", w[0], w[1][:120])
    if errs:
        print(f"\n[GATE] NG {len(errs)} 件 (build/ は更新していません)")
        for e in errs[:60]: print("  NG:", e[0], e[1][:120])
        sys.exit(1)
    if partial:
        print("\n(途中点検 --partial: build/ と verified/ は書き換えていません)"); return
    os.makedirs(OUT, exist_ok=True)
    out_rows = [{"part_key": r["part_key"], "question_data": r["question_data"]} for r in rows]   # _filter は書かない (本番の形のまま)
    json.dump(out_rows, open(os.path.join(OUT, "rows.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(flat, open(os.path.join(OUT, "flat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(blind, open(os.path.join(OUT, "blind.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # report.json には端末によって変わる warn (本番基準・基準ファイル無し) を入れない (どの端末で build しても同一にする)
    stable = [f"{a} {b}" for a, b in warns if "[本番基準]" not in b and "本番の基準" not in b]
    json.dump({"questions": len(flat), "rows": len(rows), "per_part": dict(per_part), "answer_dist": dict(dist),
               "warnings": stable}, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by_file = collections.defaultdict(list)
    for q in qs: by_file[q["_file"]].append({k: v for k, v in q.items() if not k.startswith("_")})
    for fn, lst in by_file.items():
        json.dump(lst, open(os.path.join(VD, fn), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n✅ 全ゲート PASS (warn {len(warns)}) → build/ を更新しました")


if __name__ == "__main__":
    main()
