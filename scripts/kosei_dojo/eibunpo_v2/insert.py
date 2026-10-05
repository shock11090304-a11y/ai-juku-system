#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build/rows.json を exam_questions (exam_id=daigaku / eiken_grade=teiki / part_key は行ごと) へ直 INSERT する。
★実行 (塾長の端末・承認つき): railway run -s Postgres python3 scripts/kosei_dojo/eibunpo_v2/insert.py [--commit]
   --commit を付けないと dry-run (何も書かない)。

なぜ直 INSERT か: 中学プール v3 と同じ (検証済みデータを、取込 API の自己完結ゲートに左右されずに入れる)。
冪等性: 既存行の全設問の (設問文, 選択肢) 集合と突き合わせ、既出の設問は行から除いて入れる。全設問が既出の行は skip。
★question_data は json.dumps(ensure_ascii=False) の文字列で保存 (bank の日本語 LIKE が一致するため必須)。
rollback: DELETE FROM exam_questions WHERE model = 'kosei-eibunpo-expand-v2';
安全装置: (1) 最初に check_eibunpo_v2 (CI と同じゲート) を回し、NG なら DB につながない。
          (2) 接続に idle_in_transaction_session_timeout=60s・lock_timeout=5s。
          (3) pg_try_advisory_xact_lock で同時実行を止める。
          (4) カード名 LIKE の行数 (画面が bank から取る 50 行・created_at DESC) を数え、上限を超えるときは「押し出される行」を特定する。
              押し出されるのが AI の自動生成行 (model が 'claude-sonnet-4-6' のような素のモデル名) だけなら警告して進め、
              それ以外 (manual/manual2・*verified*・*team-review*・claude-max-plan・model NULL・自分の過去の行 = 手作り/取込) が
              含まれるなら rollback して何も入れない。★AI の行も univ_simulated ('teiki' など) を持つので、question_data では見分けない。
              (2026-10-05 の基準取りで、助動詞カードは AI の古い行で窓がすでに満杯 (50/50)・受動態 49・前置詞 48 と分かった。)
              --allow-pushout (全カード) か --allow-pushout=r_grammar/助動詞,r_grammar/前置詞 (カード指定) で、手作りの押し出しも了承して進める。
              dry-run は押し出される行ごとに id・model・created_at・出どころを表示する (塾長が判断できるように)。
"""
import json
import os
import sys

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

import re  # noqa: E402

COMMIT = "--commit" in sys.argv
ALLOW_ALL = "--allow-pushout" in sys.argv
ALLOW_CARDS = set()
for a in sys.argv:
    if a.startswith("--allow-pushout="):
        ALLOW_CARDS.update(x.strip() for x in a.split("=", 1)[1].split(",") if x.strip())
AI_MODEL_RE = re.compile(r"^claude-(sonnet|opus|haiku)-[0-9][0-9a-z.-]*$")   # scheduler の自動生成 (例 claude-sonnet-4-6)。verified/team-review/max-plan は含まない
LOCK_KEY = 2026100502   # pg_advisory_xact_lock の鍵 (この投入スクリプト専用の定数)

import check_eibunpo_v2 as C  # noqa: E402
if C.main() != 0:
    print("❌ check_eibunpo_v2 が NG なので DB にはつなぎません (build.py を回し直してください)"); sys.exit(1)
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
cur.execute("SELECT part_key, question_data FROM exam_questions WHERE exam_id=%s AND eiken_grade=%s AND part_key = ANY(%s)", (L.EXAM, L.GRADE, L.PARTS))
n_rows = 0
for part, qd in cur.fetchall():
    n_rows += 1
    try:
        obj = json.loads(qd) if isinstance(qd, str) else qd
        for q in obj.get("questions") or []:
            existing.setdefault(part, set()).add(L.sig(q.get("stem"), q.get("choices")))
    except Exception:
        pass
print(f"既存 {L.EXAM}/{L.GRADE}: {n_rows} 行 / 設問 " + " ".join(f"{p}={len(existing.get(p, ()))}" for p in L.PARTS))
cur.execute("SELECT COUNT(*) FROM exam_questions WHERE model=%s", (L.MODEL,))
print(f"この model ({L.MODEL}) の既存行: {cur.fetchone()[0]}")

plan, skipped_q, skipped_rows = [], 0, 0
for r in rows:
    part = r["part_key"]; qd = r["question_data"]
    keep = [q for q in qd["questions"] if L.sig(q["stem"], q["choices"]) not in existing.get(part, set())]
    skipped_q += len(qd["questions"]) - len(keep)
    if not keep:
        skipped_rows += 1; continue
    if len(keep) != len(qd["questions"]):
        qd = dict(qd); qd["questions"] = [dict(q, id=f"q{i+1}") for i, q in enumerate(keep)]
    plan.append((part, qd))
    existing.setdefault(part, set()).update(L.sig(q["stem"], q["choices"]) for q in keep)
n_q = sum(len(qd["questions"]) for _, qd in plan)
print(f"INSERT 予定: {len(plan)} 行 / {n_q} 小問   既出で除いた設問 {skipped_q} / 空になって skip した行 {skipped_rows}")
per = {}
for part, qd in plan: per[part] = per.get(part, 0) + len(qd["questions"])
print("  内訳:", per)

CHECKS = [(u["part"], u["filter"], L.bank_limit()) for u in L.load_units()]


def is_ai_row(model):
    """scheduler が自動生成した行か。素のモデル名 (claude-sonnet-4-6 など) だけを AI とみなし、迷うものは手作り扱い (止める側)。"""
    return bool(AI_MODEL_RE.match(str(model or "").strip()))


def origin(qd_text):
    try:
        qd = json.loads(qd_text) if isinstance(qd_text, str) else (qd_text or {})
    except Exception:
        return "?"
    return str(qd.get("source") or qd.get("univ_simulated") or "?")[:24]


def pushout_report(part, f, lim, n_new):
    """投入後の窓 (新しい順 lim 行) から押し出される既存行を返す: [(id, model, created_at, origin, ai?)]。
    今回入れる行は created_at が最新なので全部窓に入る → 既存行は上位 (lim - n_new) 行だけ残る。
    ★既存行は model で絞らない (bank のクエリに model 条件は無い。前回の自分の行も NULL の行も窓を使う)。
    境界の行と created_at が同じ行は順序が不定なので、全部「押し出されうる」として評価する。"""
    if n_new <= 0: return [], 0
    cur.execute("SELECT COUNT(*) FROM exam_questions WHERE exam_id=%s AND part_key=%s AND eiken_grade=%s AND question_data LIKE %s",
                (L.EXAM, part, L.GRADE, f"%{f}%"))
    n_old = cur.fetchone()[0]
    keep = max(0, lim - n_new)
    if n_old <= keep: return [], n_old
    cur.execute("SELECT id, model, created_at, question_data FROM exam_questions WHERE exam_id=%s AND part_key=%s AND eiken_grade=%s AND question_data LIKE %s "
                "ORDER BY created_at DESC, id DESC", (L.EXAM, part, L.GRADE, f"%{f}%"))
    rows_sorted = cur.fetchall()
    boundary_ts = rows_sorted[keep][2] if keep < len(rows_sorted) else None
    pushed = [r for i, r in enumerate(rows_sorted) if i >= keep or (boundary_ts is not None and r[2] == boundary_ts)]
    return [(rid, model, created, origin(qd), is_ai_row(model)) for rid, model, created, qd in pushed], n_old


def budget_check():
    """全カードの押し出しを評価して表示。手作り/取込の行が押し出されるカードの一覧を返す。"""
    blocked = []
    for part, f, lim in CHECKS:
        n_new = sum(1 for p, qd in plan if p == part and f in json.dumps(qd, ensure_ascii=False))
        pushed, n_old = pushout_report(part, f, lim, n_new)
        total = n_old + n_new
        if not pushed:
            print(f"   {part}/{f}: 既存 {n_old} + 新規 {n_new} = {total} / {lim}")
            continue
        n_keep = sum(1 for r in pushed if not r[4])
        kind = f"手作り/取込 {n_keep} 行を含む" if n_keep else "AI の自動生成行のみ"
        print(f"   {part}/{f}: 既存 {n_old} + 新規 {n_new} = {total} / {lim} → 窓から {len(pushed)} 行が押し出される ({kind})")
        for rid, model, created, org, ai in pushed[:12]:
            print(f"        id={rid} model={model!r} created={str(created)[:19]} 出どころ={org} → {'AI' if ai else '★手作り/取込'}")
        if len(pushed) > 12: print(f"        … ほか {len(pushed) - 12} 行")
        if n_keep and not (ALLOW_ALL or f"{part}/{f}" in ALLOW_CARDS):
            blocked.append((part, f, n_keep, len(pushed)))
    return blocked


print(f"\n単元名 LIKE の窓 (画面が取る {L.bank_limit()} 行) の評価:")
blocked = budget_check()
if blocked:
    conn.rollback(); conn.close()
    print("\n❌ 手作り/取込の行が窓から押し出されるカードがあるので止めました (何も入っていません):")
    for part, f, nm, npush in blocked: print(f"   {part}/{f}: 押し出し {npush} 行のうち手作り/取込 {nm} 行")
    print("   塾長が了承する場合だけ、--allow-pushout=" + ",".join(f"{p}/{f}" for p, f, _, _ in blocked) + " (カード指定) か --allow-pushout (全カード) を付けて再実行してください。"); sys.exit(1)
if ALLOW_ALL or ALLOW_CARDS:
    print(f"\n⚠️ 押し出しの了承: {'全カード' if ALLOW_ALL else sorted(ALLOW_CARDS)}")
if not COMMIT:
    conn.rollback(); conn.close()
    print("\n🔎 dry-run。実際に入れるには --commit を付けて再実行してください。"); sys.exit(0)

for part, qd in plan:
    payload = json.dumps(qd, ensure_ascii=False)
    assert "\\u" not in payload and qd.get("source") == L.SOURCE
    cur.execute("INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) VALUES (%s,%s,%s,%s,%s)",
                (L.EXAM, part, L.GRADE, payload, L.MODEL))
conn.commit()
print(f"\n✅ INSERT 完了: {len(plan)} 行 / {n_q} 小問 (model={L.MODEL} / source={L.SOURCE})")
cur.execute("SELECT part_key, COUNT(*) FROM exam_questions WHERE model=%s GROUP BY part_key ORDER BY 1", (L.MODEL,))
print("この model の行数:", cur.fetchall())
conn.close()
