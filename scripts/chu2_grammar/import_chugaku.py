# -*- coding: utf-8 -*-
"""中2英文法45問を chugaku/eng バンク(exam_questions)へ直INSERT。
過去形→unit='過去形'(新)/未来形→unit='未来形'(新)/助動詞→unit='助動詞'(既存に追加)。
既存 chugaku/eng の1大問を top-level テンプレとして流用しスキーマ完全一致を保証。
answer は文字列index、explanation は「【単元】<unit>。正解は「<正答>」。<解説>」形式。
model='chu2-grammar-verified'・question_data.source='chu2_grammar_v1' でロールバック可能。
railway run -s Postgres python3 scripts/chu2_grammar/import_chugaku.py で実行。再実行は自model削除→再INSERTで冪等。"""
import os, json, psycopg
from psycopg.rows import dict_row

MODEL = "chu2-grammar-verified"
SRC = "chu2_grammar_v1"
GROUP2UNIT = {"past": "過去形", "future": "未来形", "aux": "助動詞"}
CHUNK = 5  # 1大問あたりの小問数(既存に合わせる)

base = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base, "..", "..", "seed-data", "chu2_grammar_v1.json"), encoding="utf-8") as f:
    rows = json.load(f)

conn = psycopg.connect(os.environ["DATABASE_PUBLIC_URL"], row_factory=dict_row)
c = conn.cursor()

# 既存chugaku/engの top-level テンプレを取得(passage/subject/univ_simulated/year_simulated/format_type)
c.execute("SELECT question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key='eng' AND model='chugaku-koukou-verified' LIMIT 1")
tmpl = json.loads(c.fetchone()["question_data"])
TOP = {k: tmpl.get(k) for k in ("passage", "subject", "univ_simulated", "year_simulated", "format_type")}
print("template top-level:", json.dumps(TOP, ensure_ascii=False))

# group ごとに subquestion を構築
by_group = {"past": [], "future": [], "aux": []}
for r in rows:
    g = r["group"]
    unit = GROUP2UNIT[g]
    ans_text = r["choices"][r["answer"]]
    expl = f"【単元】{unit}。正解は「{ans_text}」。{r['explanation']}"
    by_group[g].append({
        "type": "multiple_choice",
        "stem": r["stem"],
        "choices": r["choices"],
        "answer": str(r["answer"]),   # 文字列index(既存仕様)
        "unit": unit,
        "explanation": expl,
    })

# 冪等: 自model の既存行を削除
c.execute("DELETE FROM exam_questions WHERE exam_id='chugaku' AND part_key='eng' AND model=%s", (MODEL,))
deleted = c.rowcount
print("deleted old rows(self model):", deleted)

inserted_daimon = 0
inserted_subq = 0
for g, subs in by_group.items():
    unit = GROUP2UNIT[g]
    # CHUNK ごとに大問化
    for ci in range(0, len(subs), CHUNK):
        chunk = subs[ci:ci + CHUNK]
        # id を q1.. に振り直し
        for i, q in enumerate(chunk):
            q["id"] = f"q{i+1}"
        qd = dict(TOP)
        qd["source"] = SRC
        qd["questions"] = chunk
        c.execute(
            "INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) VALUES (%s,%s,%s,%s,%s)",
            ("chugaku", "eng", "koukou", json.dumps(qd, ensure_ascii=False), MODEL),
        )
        inserted_daimon += 1
        inserted_subq += len(chunk)

conn.commit()
print(f"inserted 大問={inserted_daimon} / 小問={inserted_subq}")

# 検証: 自model の unit 分布
c.execute("SELECT question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key='eng' AND model=%s", (MODEL,))
from collections import Counter
cnt = Counter()
for r in c.fetchall():
    for q in json.loads(r["question_data"]).get("questions", []):
        cnt[q.get("unit")] += 1
print("self-model unit分布:", dict(cnt))
# 全体(既存+自分) の 過去形/未来形/助動詞
c.execute("SELECT question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key='eng'")
cnt2 = Counter()
for r in c.fetchall():
    for q in json.loads(r["question_data"]).get("questions", []):
        u = q.get("unit")
        if u in ("過去形", "未来形", "助動詞", "時制"):
            cnt2[u] += 1
print("バンク全体の該当unit分布:", dict(cnt2))
conn.close()
print("DONE")
