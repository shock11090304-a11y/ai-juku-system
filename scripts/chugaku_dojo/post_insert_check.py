#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投入後の最終検証(DBに実際に保存された行が対象)。
1) 決定的整合チェック: model=chugaku-koukou-expand-v1 の各設問について
   - explanation が 【単元】<ft>。正解は「<choices[answer]>」。 で始まる(シャッフル後も正答テキスト一致)
   - choices 4つが相異なる / answer が 0..3 / unit==format_type
   - 単元別 24 問
   - add ファイルの stem 集合と、保存された新規 stem 集合が一致(取りこぼし/破損なし)
2) 盲再解答用に blind/key ファイルを書き出す(add/_stored_blind.json, add/_stored_key.json)。
実行: railway run -s Postgres python3 scripts/chugaku_dojo/post_insert_check.py
"""
import os, sys, json, glob, collections
import psycopg

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add")
MODEL = "chugaku-koukou-expand-v1"
UNITS = json.load(open(os.path.join(BASE, "units.json"), encoding="utf-8"))
MATH_FILTERS = [u["filter"] for s in UNITS["subjects"] if s["part"] == "math" for u in s["units"]]

dsn = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
conn = psycopg.connect(dsn); cur = conn.cursor()
cur.execute("SELECT id, question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key='math' AND model=%s ORDER BY id", (MODEL,))
rows = cur.fetchall()

problems = []
per_unit = collections.Counter()
stored_stems = set()
blind = []   # {gid, unit, stem, choices}
key = {}     # gid -> answer_index
for rid, qd_txt in rows:
    qd = json.loads(qd_txt)
    ft = qd.get("format_type")
    for q in qd.get("questions", []):
        gid = f"{rid}:{q.get('id')}"
        ch = q.get("choices"); ans = q.get("answer"); unit = q.get("unit"); expl = q.get("explanation", "")
        stem = (q.get("stem") or "").strip()
        # 検証
        if not isinstance(ch, list) or len(ch) != 4 or len(set(str(c).strip() for c in ch)) != 4:
            problems.append(("choices", gid, ft)); continue
        try:
            ai = int(ans)
        except Exception:
            problems.append(("answer_type", gid, ft)); continue
        if not (0 <= ai < 4):
            problems.append(("answer_range", gid, ft)); continue
        if unit != ft:
            problems.append(("unit_ft", gid, f"{unit}!={ft}"))
        want_prefix = f"【単元】{ft}。正解は「{ch[ai]}」。"
        if not expl.startswith(want_prefix):
            problems.append(("expl_prefix", gid, f"{ft}: {expl[:40]}"))
        per_unit[ft] += 1
        stored_stems.add(stem)
        blind.append({"gid": gid, "unit": ft, "stem": q.get("stem"), "choices": ch})
        key[gid] = ai

# add ファイルの stem 集合と照合
add_stems = set()
for fp in glob.glob(os.path.join(ADIR, "math__*.json")):
    for q in json.load(open(fp, encoding="utf-8")):
        add_stems.add((q.get("stem") or "").strip())
missing_in_db = add_stems - stored_stems
extra_in_db = stored_stems - add_stems

print(f"=== 投入後 最終検証 (model={MODEL}) ===")
print(f"新規行: {len(rows)}  新規設問: {sum(per_unit.values())}")
print("単元別:")
allok = True
for f in MATH_FILTERS:
    n = per_unit.get(f, 0)
    flag = "" if n == 14 or (f == "円周角" and n == 15) else f"  ⚠️期待と不一致"
    if flag: allok = False
    print(f"  {n:3}  {f}{flag}")
print(f"整合エラー: {len(problems)} 件 (0であるべき)")
for p in problems[:20]:
    print("   ", p)
print(f"add stem数: {len(add_stems)}  DB新規stem数: {len(stored_stems)}")
print(f"  DBに無いadd stem: {len(missing_in_db)}  (0であるべき)")
for s in list(missing_in_db)[:5]:
    print("    missing:", s[:60])
print(f"  addに無いDB stem: {len(extra_in_db)}  (0であるべき)")
for s in list(extra_in_db)[:5]:
    print("    extra:", s[:60])

json.dump(blind, open(os.path.join(ADIR, "_stored_blind.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(key, open(os.path.join(ADIR, "_stored_key.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(f"\n盲再解答用に書き出し: add/_stored_blind.json ({len(blind)}問), add/_stored_key.json")

ok = (len(problems) == 0 and not missing_in_db and not extra_in_db and allok)
print("\n決定的整合チェック:", "✅ ALL CLEAN" if ok else "❌ 要確認")
cur.close(); conn.close()
sys.exit(0 if ok else 1)
