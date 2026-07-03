#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gemini自己完結ゲート(Layer B)が誤弾きした理科/社会の知識問題を直接DB INSERT でゲート迂回。
★必ず `railway run -s Postgres python3 scripts/chugaku_dojo/direct_insert_gated.py` で実行(DATABASE_PUBLIC_URL 取得)。
冪等: batches/all_rows.json の全 chugaku 行のうち、DB に未存在(question_data content 一致無し)の行のみ INSERT。
question_data は import と同じ json.dumps(ensure_ascii=False) の文字列で保存(bank の topic LIKE が日本語literalで一致するため必須)。
"""
import os, sys, json, hashlib
import psycopg

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, "batches", "all_rows.json"), encoding="utf-8"))

def canon(qd_obj):
    # 順序非依存の同一判定 (DB既存TEXTと自分の行を同じ規則でhash)
    return hashlib.md5(json.dumps(qd_obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

dsn = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
if not dsn:
    print("DATABASE_PUBLIC_URL 未設定 (railway run -s Postgres で実行してください)"); sys.exit(1)

conn = psycopg.connect(dsn)
cur = conn.cursor()

# 既存 chugaku 行の question_data を取得し canonical hash 集合を作る
cur.execute("SELECT part_key, question_data FROM exam_questions WHERE exam_id='chugaku'")
existing = {}  # part -> set(hash)
for part_key, qd_text in cur.fetchall():
    try:
        obj = json.loads(qd_text) if isinstance(qd_text, str) else qd_text
        existing.setdefault(part_key, set()).add(canon(obj))
    except Exception:
        pass
print("既存 chugaku 行:", {k: len(v) for k, v in existing.items()})

ins = {}
skip = {}
for r in rows:
    part = r["part_key"]; qd = r["question_data"]
    h = canon(qd)
    if h in existing.get(part, set()):
        skip[part] = skip.get(part, 0) + 1
        continue
    cur.execute(
        "INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) VALUES (%s,%s,%s,%s,%s)",
        ("chugaku", part, "koukou", json.dumps(qd, ensure_ascii=False), "chugaku-koukou-verified"),
    )
    existing.setdefault(part, set()).add(h)
    ins[part] = ins.get(part, 0) + 1

conn.commit()
print("INSERT:", ins if ins else "(なし)")
print("SKIP(既存):", skip)

# 事後確認
cur.execute("SELECT part_key, COUNT(*) FROM exam_questions WHERE exam_id='chugaku' GROUP BY part_key ORDER BY part_key")
print("=== 取込後の chugaku 行数 ===")
tot = 0
for part_key, n in cur.fetchall():
    tot += n; print(f"  {part_key:8} {n}")
print("  total rows:", tot, "(期待 125)")
cur.close(); conn.close()
