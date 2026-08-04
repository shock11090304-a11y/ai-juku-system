#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""part別 投入後の決定的整合チェック + 盲再解答用ファイル書き出し。
usage: railway run -s Postgres python3 scripts/chugaku_dojo/post_insert_check2.py <part>
"""
import os, sys, json, glob, collections
import psycopg

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add2")
PART = sys.argv[1]
MODEL = f"chugaku-{PART}-expand-v1"
UNITS = json.load(open(os.path.join(BASE, "units.json"), encoding="utf-8"))
FILTERS = [u["filter"] for s in UNITS["subjects"] if s["part"] == PART for u in s["units"]]
plan = json.load(open(os.path.join(ADIR, f"_plan_{PART}.json"), encoding="utf-8"))
TADD = {x["gi"]: x for x in (plan["non_reading"] + plan["reading"])}
FILT_TADD = {x["filter"]: x["add"] for x in (plan["non_reading"] + plan["reading"])}

conn = psycopg.connect(os.environ.get("DATABASE_PUBLIC_URL") or os.environ["DATABASE_URL"]); cur = conn.cursor()
cur.execute("SELECT id, question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key=%s AND model=%s ORDER BY id", (PART, MODEL))
rows = cur.fetchall()

problems = []; per_unit = collections.Counter(); stored_stems = set(); blind = []; key = {}
for rid, t in rows:
    qd = json.loads(t); ft = qd.get("format_type"); passage = qd.get("passage", "")
    for q in qd.get("questions", []):
        gid = f"{rid}:{q.get('id')}"; ch = q.get("choices"); ans = q.get("answer"); unit = q.get("unit"); expl = q.get("explanation", "")
        if not isinstance(ch, list) or len(ch) != 4 or len(set(str(c).strip() for c in ch)) != 4:
            problems.append(("choices", gid, ft)); continue
        try: ai = int(ans)
        except Exception: problems.append(("ans", gid, ft)); continue
        if not (0 <= ai < 4): problems.append(("range", gid, ft)); continue
        if unit != ft: problems.append(("unit", gid, f"{unit}!={ft}"))
        if not expl.startswith(f"【単元】{ft}。正解は「{ch[ai]}」。"): problems.append(("prefix", gid, ft))
        per_unit[ft] += 1; stored_stems.add((q.get("stem") or "").strip())
        blind.append({"gid": gid, "unit": ft, "passage": passage, "stem": q.get("stem"), "choices": ch}); key[gid] = ai

add_stems = set()
present_gi = set()
for fp in glob.glob(os.path.join(ADIR, f"{PART}__*.json")):
    present_gi.add(int(os.path.basename(fp).split("__")[1].split(".")[0]))
    for q in json.load(open(fp, encoding="utf-8")): add_stems.add((q.get("stem") or "").strip())
missing = add_stems - stored_stems; extra = stored_stems - add_stems
# 生成済(add2ファイルが存在する)単元のみ件数を検査。未生成(読解等)はスキップ。
EXPECT = {TADD[gi]["filter"]: TADD[gi]["add"] for gi in present_gi if gi in TADD}

print(f"=== 投入後 最終検証 ({MODEL}) ===")
print(f"新規行 {len(rows)} / 新規設問 {sum(per_unit.values())}")
allok = True
for f in FILTERS:
    if f not in EXPECT: continue
    n = per_unit.get(f, 0); exp = EXPECT[f]
    flag = "" if n == exp else "  ⚠️不一致"
    if flag: allok = False
    print(f"  {n:3}/{exp:2}  {f}{flag}")
print(f"整合エラー: {len(problems)}"); [print("  ", p) for p in problems[:15]]
print(f"add stem {len(add_stems)} / DB新規stem {len(stored_stems)} / DB欠落 {len(missing)} / 余剰 {len(extra)}")
[print("  missing:", s[:50]) for s in list(missing)[:5]]
[print("  extra:", s[:50]) for s in list(extra)[:5]]

json.dump(blind, open(os.path.join(ADIR, f"_stored_blind_{PART}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(key, open(os.path.join(ADIR, f"_stored_key_{PART}.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(f"盲再解答用: add2/_stored_blind_{PART}.json ({len(blind)}) / _stored_key_{PART}.json")
ok = (len(problems) == 0 and not missing and not extra and allok)
print("決定的整合チェック:", "✅ ALL CLEAN" if ok else "❌ 要確認")
cur.close(); conn.close(); sys.exit(0 if ok else 1)
