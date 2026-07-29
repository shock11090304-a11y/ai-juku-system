#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build/rows.json を exam_questions (chugaku/eng/koukou) へ直INSERT。

★実行: `railway run -s Postgres python3 scripts/chugaku_dojo/futeishi/insert.py [--commit]`
   --commit を付けないと dry-run (何も書かない)。

なぜ直INSERT か: 本番の EXAM_IMPORT_VERIFY_AI (Layer B ゲート) は passage の無い一問一答を
「本文が無い→解答不能」と非決定的に誤弾きする実績があるため (中学 理科/社会で14行が落ちた)。
検証済みデータは既存 chugaku プールと同様に直INSERT する。

★必須: question_data は json.dumps(ensure_ascii=False) の文字列で保存する。
   ensure_ascii=True だと \\uXXXX 化され、bank の `question_data LIKE '%不定詞の用法%'`
   (日本語リテラル) が一致せず、ドリルが「単元で絞れない」状態になる。

冪等性: 既存 chugaku/eng 行の (stem, 選択肢) 集合と突き合わせ、1問でも既出の設問を含む行はスキップ。
   ★stem だけで判定しない: 「次の中から、英文として正しいものを選びなさい。」のように指示文だけが
     stem になる形式は複数問で正当に重複するため、stem 単独だと別問題を誤って弾いてしまう
     (実際に1行25問しか入らない事故を起こした)。content hash だけだと逆に、解説を直して
     再実行したとき同じ設問が二重に入る。

rollback: model='chugaku-koukou-futeishi-v1' の行だけを消せば完全に元へ戻る。
   DELETE FROM exam_questions WHERE model='chugaku-koukou-futeishi-v1';
"""
import json
import os
import sys

import psycopg

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from build import MODEL, SOURCE, UNIT  # noqa: E402

EXAM, PART, GRADE = "chugaku", "eng", "koukou"
COMMIT = "--commit" in sys.argv

rows = json.load(open(os.path.join(BASE, "build", "rows.json"), encoding="utf-8"))

dsn = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
if not dsn:
    print("❌ DATABASE_PUBLIC_URL 未設定 (railway run -s Postgres … で実行してください)")
    sys.exit(1)

conn = psycopg.connect(dsn)
cur = conn.cursor()

# ── 既存 stem 集合 (同一 exam/part/grade) ──
cur.execute(
    "SELECT question_data FROM exam_questions WHERE exam_id=%s AND part_key=%s AND eiken_grade=%s",
    (EXAM, PART, GRADE),
)
def sig(q):
    """設問の同一判定キー = 設問文 + 選択肢の組 (stem 単独では足りない)。"""
    return (" ".join(str(q.get("stem", "")).split()),
            tuple(sorted(str(c) for c in (q.get("choices") or []))))


existing_sigs = set()
existing_rows = 0
for (qd,) in cur.fetchall():
    existing_rows += 1
    try:
        obj = json.loads(qd) if isinstance(qd, str) else qd
        for q in obj.get("questions") or []:
            existing_sigs.add(sig(q))
    except Exception:
        pass
print(f"既存 {EXAM}/{PART}/{GRADE}: {existing_rows}行 / 設問 {len(existing_sigs)}件")

to_insert, skipped = [], []
for r in rows:
    sigs = [sig(q) for q in r.get("questions") or []]
    dup = [x for x in sigs if x in existing_sigs]
    if dup:
        skipped.append((len(r["questions"]), dup[0][0][:40]))
        continue
    to_insert.append(r)
    existing_sigs.update(sigs)  # rows.json 内の重複も防ぐ

n_sub = sum(len(r["questions"]) for r in to_insert)
print(f"INSERT 予定: {len(to_insert)}行 / {n_sub}小問   SKIP(設問既出): {len(skipped)}行")
for n, s in skipped:
    print(f"  skip: {n}小問 (既出: {s}…)")

if not COMMIT:
    print("\n🔎 dry-run。実際に入れるには --commit を付けて再実行してください。")
    sys.exit(0)

for r in to_insert:
    payload = json.dumps(r, ensure_ascii=False)   # ★ensure_ascii=False 必須
    assert UNIT in payload, "日本語リテラルが payload に無い (LIKE が一致しなくなる)"
    cur.execute(
        "INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) "
        "VALUES (%s,%s,%s,%s,%s)",
        (EXAM, PART, GRADE, payload, MODEL),
    )
conn.commit()
print(f"\n✅ INSERT 完了: {len(to_insert)}行 / {n_sub}小問  (model={MODEL} / source={SOURCE})")

# ── 事後確認 ──
cur.execute(
    "SELECT COUNT(*) FROM exam_questions WHERE exam_id=%s AND part_key=%s AND eiken_grade=%s AND model=%s",
    (EXAM, PART, GRADE, MODEL),
)
print("この model の行数:", cur.fetchone()[0])
cur.execute(
    "SELECT COUNT(*) FROM exam_questions WHERE exam_id=%s AND part_key=%s AND eiken_grade=%s "
    "AND question_data LIKE %s",
    (EXAM, PART, GRADE, f"%{UNIT}%"),
)
print(f"LIKE '%{UNIT}%' で拾える行数:", cur.fetchone()[0])
conn.close()
