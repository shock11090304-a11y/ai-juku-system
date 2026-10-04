#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verified/*.json → exam_questions の行 (question_data JSON) を組み立て、ゲートをかけて build/ に書く。
    python3 scripts/chugaku_dojo/expand_v3/build.py
出力:
  build/rows.json   … exam_questions に入れる行 (非読解 5小問/行・読解は本文ごと1行)
  build/flat.json   … 全小問 (正解つき・検証と post_check の照合用)
  build/blind.json  … 全小問 (正解・解説なし)
  build/report.json … 件数・正解位置・tell の集計
正解位置: 単元ごとに stem の md5 順で 0,1,2,3 を振る (均等・決定的・保存順に周期を作らない)。
解説は正解テキスト参照 (【単元】F。正解は「…」。) なので、選択肢を入れ替えても壊れない。
★ゲート NG のときは build/ を書き換えない (落ちた rows.json がそのまま本番へ入るのを防ぐ)。
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v3lib as L  # noqa: E402

VD = os.path.join(L.HERE, "verified"); OUT = os.path.join(L.HERE, "build")
SUBJ = {"eng": "英語", "math": "数学", "kokugo": "国語", "rika": "理科", "shakai": "社会"}


def load_verified():
    units = L.load_units(); by_gi = {u["gi"]: u for u in units}
    qs = []
    for fp in sorted(glob.glob(os.path.join(VD, "*.json"))):
        part, gi = os.path.basename(fp).split("__")[0], int(os.path.basename(fp).split("__")[1].split(".")[0])
        u = by_gi.get(gi)
        data = json.load(open(fp, encoding="utf-8"))
        for q in data:
            q = dict(q); q["_gi"] = gi; q["_file"] = os.path.basename(fp); q["_unit"] = u
            q["_part"] = part
            qs.append(q)
    return units, qs


def assign_positions(qs):
    """単元ごとに md5(stem) 順で 0..3 を振り、選択肢を入れ替える。"""
    by_gi = collections.defaultdict(list)
    for q in qs: by_gi[q["_gi"]].append(q)
    for gi, group in by_gi.items():
        ranked = sorted(group, key=lambda q: L.md5(q["stem"] + "|" + q.get("passage", "")))
        for rank, q in enumerate(ranked):
            want = rank % 4; cur = q["answer_index"]
            if cur != want:
                ch = list(q["choices"]); ch[cur], ch[want] = ch[want], ch[cur]
                q["choices"] = ch; q["answer_index"] = want


def gates(units, qs, strict=True, partial=False):
    """partial=True: まだ問題の無い単元を『0 件』エラーにしない (途中の点検用)"""
    errs, warns = [], []
    by_gi = {u["gi"]: u for u in units}
    ex = L.existing_questions()
    for part in L.PARTS:
        ex_sigs = {L.sig(q["stem"], q["choices"]) for q in ex[part]}
        ex_stems = {L.stem_key(q["stem"]) for q in ex[part]}
        mine = [q for q in qs if q["_part"] == part]
        seen_sig, seen_stem = {}, {}
        for q in mine:
            u = by_gi.get(q["_gi"]); where = f"{q['_file']}:{q['stem'][:30]!r}"
            if not u or u["part"] != part:
                errs.append((where, "ファイル名の gi が単元と合わない")); continue
            L.validate_question(q, {u["filter"]}, errs, where)
            # 解説の接頭辞: 作り直しても変わらないこと + 正解の後ろ半分が頭に残っていないこと (2026-10-04 の重複事故)
            c_ok = q["choices"][q["answer_index"]] if 0 <= q.get("answer_index", -1) < len(q["choices"]) else ""
            if c_ok and L.rebuild_expl(u["filter"], c_ok, q["explanation"]) != q["explanation"]:
                errs.append((where, "解説の接頭辞を作り直すと変わる (strip_prefix の取りこぼし)"))
            if "」" in c_ok:
                h = L.expl_head(u["filter"], c_ok)
                if q["explanation"].startswith(h) and q["explanation"][len(h):].startswith(c_ok[c_ok.index("」") + 1:] + "」"):
                    errs.append((where, "解説の頭に正解の後ろ半分が重複している"))
            if u["reading"] and not str(q.get("passage", "")).strip(): errs.append((where, "読解なのに本文が空"))
            if not u["reading"] and str(q.get("passage", "")).strip(): errs.append((where, "非読解なのに本文あり"))
            s = L.sig(q["stem"], q["choices"]); sk = L.stem_key(q["stem"])
            cs = L.content_stem(q["stem"]) and not u["reading"]
            if s in ex_sigs: errs.append((where, "既存プールと同一の設問 (stem+選択肢)"))
            elif cs and sk in ex_stems: errs.append((where, "既存プールと同一の設問文"))
            if s in seen_sig: errs.append((where, f"v3 内で同一の設問: {seen_sig[s]}"))
            elif cs and sk in seen_stem: errs.append((where, f"v3 内で同一の設問文: {seen_stem[sk]}"))
            seen_sig[s] = q["_file"]; seen_stem[sk] = q["_file"]
            if q["explanation"].count("正解は「") != 1: errs.append((where, "解説の「正解は「」が 1 回でない"))
        # 単元ごとの件数・正解位置・tell
        for u in [u for u in units if u["part"] == part]:
            g = [q for q in mine if q["_gi"] == u["gi"]]
            if not g:
                if not partial: errs.append((f"{part}__{u['gi']}", f"単元『{u['filter']}』の問題が 0 件"))
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
            conv = [q for q in g if L.converges(q["choices"], q["answer_index"])]
            for q in conv: warns.append((f"{part}__{u['gi']}", f"部分最多で当たる: {q['stem'][:40]!r} / " + " | ".join(q["choices"])))
        # bank の LIKE 予算: 単元名を含む行が既存+新規で 50 行を超えると、古い行が配信から押し出される
        new_rows = rows_for(part, mine, by_gi)
        old_rows = L.existing_rows_text(part)
        names = L.filters_of(part, units) + (L.DOJO_ONLY_ENG if part == "eng" else [])
        reading_of = {u["filter"]: u["reading"] for u in units if u["part"] == part}
        for f in names:
            lim = L.bank_limit(reading_of.get(f, False))
            n_old = sum(1 for r in old_rows if f in r); n_new = sum(1 for r in new_rows if f in json.dumps(r, ensure_ascii=False))
            own_old = sum(1 for r in old_rows if f'"format_type": "{f}"' in r); own_new = sum(1 for r in new_rows if r["format_type"] == f)
            if n_old + n_new > lim:
                errs.append((f"{part}/{f}", f"単元名を含む行が {n_old}+{n_new}={n_old+n_new} > {lim} (画面が bank から取る行数) → 古い行が配信されなくなる"))
            elif n_new - own_new > 0:
                warns.append((f"{part}/{f}", f"他単元の新規行 {n_new - own_new} 行に『{f}』が含まれる (LIKE 予算 {n_old+n_new}/{lim})"))
    return errs, warns


def rows_for(part, mine, by_gi):
    rows = []
    for u in sorted({q["_gi"] for q in mine}):
        unit = by_gi[u]; g = [q for q in mine if q["_gi"] == u]
        def row(qlist, passage):
            return {"passage": passage or "", "subject": SUBJ[part], "univ_simulated": "公立高校入試(標準)",
                    "year_simulated": None, "source": L.SOURCE, "format_type": unit["filter"],
                    "questions": [{"id": f"q{i+1}", "type": "multiple_choice", "stem": q["stem"], "choices": q["choices"],
                                   "answer": str(q["answer_index"]), "unit": unit["filter"], "explanation": q["explanation"]}
                                  for i, q in enumerate(qlist)]}
        if unit["reading"]:
            groups = collections.OrderedDict()
            for q in g: groups.setdefault(q["passage"], []).append(q)
            for pg, qq in groups.items(): rows.append(row(qq, pg))
        else:
            for i in range(0, len(g), L.CHUNK): rows.append(row(g[i:i + L.CHUNK], ""))
    return rows


def main():
    partial = "--partial" in sys.argv   # 途中点検: 無い単元を 0 件エラーにしない・build/ も verified/ も書かない
    units, qs = load_verified()
    if not qs:
        print("verified/ が空です"); sys.exit(1)
    assign_positions(qs)
    for q in qs:
        q["explanation"] = L.rebuild_expl(q["filter"], q["choices"][q["answer_index"]], q["explanation"])
    errs, warns = gates(units, qs, partial=partial)
    by_gi = {u["gi"]: u for u in units}
    rows = []
    for part in L.PARTS: rows += rows_for(part, [q for q in qs if q["_part"] == part], by_gi)
    flat, blind = [], []
    for ri, r in enumerate(rows):
        for q in r["questions"]:
            gid = f"r{ri:03d}:{q['id']}"
            flat.append({"gid": gid, "part": [p for p in L.PARTS if SUBJ[p] == r["subject"]][0], "unit": r["format_type"],
                         "passage": r["passage"], "stem": q["stem"], "choices": q["choices"], "answer": q["answer"], "explanation": q["explanation"]})
            blind.append({"gid": gid, "unit": r["format_type"], "passage": r["passage"], "stem": q["stem"], "choices": q["choices"]})
    per_part = collections.Counter(f["part"] for f in flat); dist = collections.Counter(f["answer"] for f in flat)
    print(f"小問 {len(flat)} / 行 {len(rows)}  " + " ".join(f"{p}={per_part[p]}" for p in L.PARTS))
    print(f"正解位置分布: " + " ".join(f"{k}:{dist[k]}" for k in "0123"))
    for w in warns: print("  warn", w[0], w[1][:110])
    if errs:
        print(f"\n[GATE] NG {len(errs)} 件 (build/ は更新していません)")
        for e in errs[:60]: print("  NG:", e[0], e[1][:120])
        sys.exit(1)
    if partial:
        print("\n(途中点検 --partial: build/ と verified/ は書き換えていません)"); return
    os.makedirs(OUT, exist_ok=True)
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(flat, open(os.path.join(OUT, "flat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(blind, open(os.path.join(OUT, "blind.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"questions": len(flat), "rows": len(rows), "per_part": dict(per_part), "answer_dist": dict(dist),
               "warnings": [f"{a} {b}" for a, b in warns]}, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # verified/ 側も位置の入れ替え・解説の接頭辞を書き戻す (正典をそろえる)
    by_file = collections.defaultdict(list)
    for q in qs: by_file[q["_file"]].append({k: v for k, v in q.items() if not k.startswith("_")})
    for fn, lst in by_file.items():
        json.dump(lst, open(os.path.join(VD, fn), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n✅ 全ゲート PASS (warn {len(warns)}) → build/ を更新しました")


if __name__ == "__main__":
    main()
