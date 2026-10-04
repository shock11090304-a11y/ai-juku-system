#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build/rows.json を exam_questions (exam_id=chugaku / eiken_grade=koukou) へ直 INSERT する。
★実行 (塾長の端末・承認つき): railway run -s Postgres python3 scripts/chugaku_dojo/expand_v3/insert.py [--commit]
   --commit を付けないと dry-run (何も書かない)。

なぜ直 INSERT か: 取込 API の自己完結ゲート Layer B (EXAM_IMPORT_VERIFY_AI) は本文の無い一問一答を
「解答不能」と非決定的に誤弾きした実績がある (2026-07 中学 理科/社会で 14 行)。検証済みデータは
既存の中学プールと同じく直 INSERT する。

冪等性: 既存行の全設問の (設問文, 選択肢) 集合と突き合わせ、既出の設問は行から除いて入れる
(1 問でも既出なら行ごと skip、だと futeishi で 25/30 問しか入らない事故があった)。全設問が既出の行は skip。
★question_data は json.dumps(ensure_ascii=False) の文字列で保存 (bank の日本語 LIKE が一致するため必須)。
rollback: DELETE FROM exam_questions WHERE model = 'chugaku-koukou-expand-v3';
安全装置: (1) 最初に check_expand_v3 (CI と同じゲート) を回し、NG なら DB につながない (build し忘れた古い rows.json を入れない)。
          (2) 接続に idle_in_transaction_session_timeout=60s・lock_timeout=5s を付ける (回線が切れても未 commit の
              トランザクションが表のロックを握り続けない。死んだ接続の idle in transaction で本番 API が止まった前例がある)。
          (3) pg_try_advisory_xact_lock で 2 つの端末からの同時実行を止める。
          (4) 単元名 LIKE の行数 (画面が bank から取る行数 = 読解 32 / それ以外 50) を dry-run では見込みで表示し、
              --commit では commit 前に同じトランザクションで数え、超えたら rollback して何も入れない。
"""
import json
import os
import sys

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v3lib as L  # noqa: E402

EXAM, GRADE = "chugaku", "koukou"
PART_OF = {"英語": "eng", "数学": "math", "国語": "kokugo", "理科": "rika", "社会": "shakai"}
COMMIT = "--commit" in sys.argv
LOCK_KEY = 2026100403   # pg_advisory_xact_lock の鍵 (この投入スクリプト専用の定数)

import check_expand_v3 as C  # noqa: E402
if C.main() != 0:
    print("❌ check_expand_v3 が NG なので DB にはつなぎません (build.py を回し直してください)"); sys.exit(1)
rows = json.load(open(os.path.join(L.HERE, "build", "rows.json"), encoding="utf-8"))
if not rows:
    print("rows.json が空"); sys.exit(1)

dsn = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
if not dsn:
    print("❌ DATABASE_PUBLIC_URL 未設定 (railway run -s Postgres … で実行してください)"); sys.exit(1)
conn = psycopg.connect(dsn, options="-c idle_in_transaction_session_timeout=60000 -c lock_timeout=5000")
cur = conn.cursor()
cur.execute("SELECT pg_try_advisory_xact_lock(%s)", (LOCK_KEY,))
if not cur.fetchone()[0]:
    conn.rollback(); conn.close()
    print("❌ 別の端末で insert.py が実行中です。終わってからやり直してください。"); sys.exit(1)

existing = {}   # part -> set(sig)
cur.execute("SELECT part_key, question_data FROM exam_questions WHERE exam_id=%s AND eiken_grade=%s", (EXAM, GRADE))
n_rows = 0
for part, qd in cur.fetchall():
    n_rows += 1
    try:
        obj = json.loads(qd) if isinstance(qd, str) else qd
        for q in obj.get("questions") or []:
            existing.setdefault(part, set()).add(L.sig(q.get("stem"), q.get("choices")))
    except Exception:
        pass
print(f"既存 {EXAM}/{GRADE}: {n_rows} 行 / 設問 " + " ".join(f"{p}={len(existing.get(p, ()))}" for p in L.PARTS))
cur.execute("SELECT COUNT(*) FROM exam_questions WHERE model=%s", (L.MODEL,))
print(f"この model ({L.MODEL}) の既存行: {cur.fetchone()[0]}")

plan, skipped_q, skipped_rows = [], 0, 0
for r in rows:
    part = PART_OF[r["subject"]]
    keep = [q for q in r["questions"] if L.sig(q["stem"], q["choices"]) not in existing.get(part, set())]
    skipped_q += len(r["questions"]) - len(keep)
    if not keep:
        skipped_rows += 1; continue
    if len(keep) != len(r["questions"]):
        r = dict(r); r["questions"] = [dict(q, id=f"q{i+1}") for i, q in enumerate(keep)]
    plan.append((part, r))
    existing.setdefault(part, set()).update(L.sig(q["stem"], q["choices"]) for q in keep)
n_q = sum(len(r["questions"]) for _, r in plan)
print(f"INSERT 予定: {len(plan)} 行 / {n_q} 小問   既出で除いた設問 {skipped_q} / 空になって skip した行 {skipped_rows}")
per = {}
for part, r in plan: per[part] = per.get(part, 0) + len(r["questions"])
print("  内訳:", per)

# 単元名 LIKE の行数 (bank は created_at DESC で画面が頼んだ行数しか返さない → 超えると古い行が配信されない)
CHECKS = [(u["part"], u["filter"], L.bank_limit(u["reading"])) for u in L.load_units()]
CHECKS += [("eng", f, L.BANK_LIMIT) for f in L.DOJO_ONLY_ENG]


def like_count(part, f):
    cur.execute("SELECT COUNT(*) FROM exam_questions WHERE exam_id=%s AND part_key=%s AND eiken_grade=%s AND question_data LIKE %s",
                (EXAM, part, GRADE, f"%{f}%"))
    return cur.fetchone()[0]


if not COMMIT:
    over = []
    for part, f, lim in CHECKS:
        n = like_count(part, f) + sum(1 for p, r in plan if p == part and f in json.dumps(r, ensure_ascii=False))
        if n > lim: over.append((part, f, n, lim))
    conn.rollback(); conn.close()
    if over:
        print("⚠️ 入れると単元名を含む行が上限を超える単元があります (--commit しても rollback されます):")
        for part, f, n, lim in over: print(f"   {part}/{f}: 見込み {n} 行 > {lim}")
    else:
        print("単元名 LIKE の見込み: すべて上限 (読解 32 / それ以外 50) 以内")
    print("\n🔎 dry-run。実際に入れるには --commit を付けて再実行してください。"); sys.exit(0)

for part, r in plan:
    payload = json.dumps(r, ensure_ascii=False)
    assert r["format_type"] in payload and "\\u" not in payload
    cur.execute("INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) VALUES (%s,%s,%s,%s,%s)",
                (EXAM, part, GRADE, payload, L.MODEL))
# ★commit の前に、同じトランザクションの中で数える (自分の未 commit 行も見える)。1 単元でも超えたら何も入れない。
over = []
for part, f, lim in CHECKS:
    n = like_count(part, f)
    if n > lim: over.append((part, f, n, lim))
if over:
    conn.rollback(); conn.close()
    print("❌ 単元名を含む行が上限を超える単元があるので rollback しました (何も入っていません):")
    for part, f, n, lim in over: print(f"   {part}/{f}: {n} 行 > {lim}")
    sys.exit(1)
conn.commit()
print(f"\n✅ INSERT 完了: {len(plan)} 行 / {n_q} 小問 (model={L.MODEL} / source={L.SOURCE})")
print("単元名 LIKE の上限 (読解 32 / それ以外 50) を超える単元: なし")
cur.execute("SELECT part_key, COUNT(*) FROM exam_questions WHERE model=%s GROUP BY part_key ORDER BY 1", (L.MODEL,))
print("この model の行数:", cur.fetchall())
conn.close()
