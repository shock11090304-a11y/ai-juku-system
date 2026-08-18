#!/usr/bin/env python3
"""daigaku/r_grammar 未タグ小問への【単元】タグ付与 + 「関係」→「関係詞」正規化。
- 変更前 question_data を exam_questions_archive に退避 (batch_id で一括 rollback 可)
- 既定 dry-run。--apply で書き込み。
- 冪等: 既にタグ/unit がある小問はスキップ (再実行で二重付与しない)。
使い方: railway run -s Postgres python3 apply_unit_tags.py final_labels.json [--apply]
"""
import os, json, re, sys
import psycopg

LABELS = json.load(open(sys.argv[1]))
APPLY = "--apply" in sys.argv
BATCH_ID = "r_grammar_unit_tags_20260818"
REASON = "週次弱点プリント単元一致: 未タグ小問に【単元】タグ+unit付与 / 【単元】関係→関係詞 正規化"
TAG_RE = re.compile(r"【単元】\s*([^】\n(（]+)")
VOCAB = {"時制","助動詞","受動態","不定詞","動名詞","分詞","分詞構文","比較","関係詞","仮定法",
         "接続詞","前置詞","倒置","否定","疑問詞","話法","強調","名詞・代名詞","冠詞","形容詞・副詞","語法"}
assert all(v in VOCAB for v in LABELS.values()), "語彙外ラベルあり"

conn = psycopg.connect(os.environ["DATABASE_PUBLIC_URL"])
c = conn.cursor()
c.execute("SELECT id, exam_id, part_key, eiken_grade, question_data, model, created_at "
          "FROM exam_questions WHERE exam_id='daigaku' AND part_key='r_grammar' ORDER BY id")
rows = c.fetchall()

n_tagged_subs = 0
n_norm_subs = 0
rows_to_update = []   # (rid, new_json, row_meta)
errors = []
samples = []

for (rid, exam_id, part_key, eiken_grade, qd_raw, model, created_at) in rows:
    qd = json.loads(qd_raw) if isinstance(qd_raw, str) else (qd_raw or {})
    qs = [q for q in (qd.get("questions") or []) if isinstance(q, dict)]
    changed = False
    for i, q in enumerate(qs):
        u = str(q.get("unit") or "").strip()
        expl = str(q.get("explanation") or "")
        text = expl + "\n" + str(q.get("stem") or "")
        m = TAG_RE.search(text)
        if u or m:
            # 正規化: 【単元】関係 ( → 【単元】関係詞 ( — タグは explanation 末尾/stem 末尾の両方にある
            if m and m.group(1).strip() == "関係":
                norm = False
                new_expl = re.sub(r"【単元】関係(?=\s*[(（])", "【単元】関係詞", expl)
                if new_expl != expl:
                    q["explanation"] = new_expl
                    norm = True
                stem = str(q.get("stem") or "")
                new_stem = re.sub(r"【単元】関係(?=\s*[(（])", "【単元】関係詞", stem)
                if new_stem != stem:
                    q["stem"] = new_stem
                    norm = True
                if norm:
                    n_norm_subs += 1
                    changed = True
            continue
        key = f"{rid}#{i}"
        label = LABELS.get(key)
        if not label:
            errors.append(f"ラベル欠落: {key}")
            continue
        q["unit"] = label
        q["explanation"] = f"【単元】{label}" + ("\n" + expl if expl else "")
        n_tagged_subs += 1
        changed = True
        if len(samples) < 3:
            samples.append((key, label, q["explanation"][:120]))
    if changed:
        new_json = json.dumps(qd, ensure_ascii=False)
        json.loads(new_json)  # round-trip 検証
        assert "【単元】" in new_json
        rows_to_update.append((rid, new_json, (exam_id, part_key, eiken_grade, qd_raw, model, created_at)))

print(f"対象行={len(rows_to_update)} タグ付与小問={n_tagged_subs} 関係→関係詞 正規化小問={n_norm_subs}")
if errors:
    print("ERRORS:", errors[:10])
    sys.exit(1)
for s in samples:
    print("  sample:", s)

if not APPLY:
    print("(dry-run: --apply で書き込み)")
    sys.exit(0)

for (rid, new_json, (exam_id, part_key, eiken_grade, qd_raw, model, created_at)) in rows_to_update:
    c.execute(
        "INSERT INTO exam_questions_archive "
        "(original_id, exam_id, part_key, eiken_grade, question_data, original_model, original_created_at, replacement_batch_id, replacement_reason) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (rid, exam_id, part_key, eiken_grade, qd_raw, model, created_at, BATCH_ID, REASON)
    )
    c.execute("UPDATE exam_questions SET question_data = %s WHERE id = %s", (new_json, rid))
conn.commit()
print(f"APPLIED: {len(rows_to_update)} 行を更新・退避 batch_id={BATCH_ID}")
conn.close()
