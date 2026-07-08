#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中学数学ドリルの追加問題を『append-only』で本番 exam_questions に投入する。

なぜ専用スクリプトか:
  package.py は verified/*.json 全体を 5問/行に束ね直し + part単位の正解位置ラウンドロビンをやる。
  既存問題を含めて再パッケージすると『既存行の content hash が変わり』→ direct_insert が
  重複 INSERT してしまう(既存行は残ったまま新バンドルが増える=二重出題)。
  よって追加分は「新規ファイルのみ」を読み、既存を一切触らず新しい行だけを追記する。

入力:  scripts/chugaku_dojo/add/math__*.json
        [{subject, part='math', filter, unit, stem, passage='', choices[4], answer_index, explanation}, ...]
処理:
  - 厳密バリデーション(4択・重複なし・index範囲・unit=filter・stem/expl 非空)
  - 既存DB(chugaku/math)の stem 集合と照合し、stem 完全一致は重複としてスキップ(冪等)
  - 追加分の中でも stem 重複を除去
  - answer_index を 0..3 ラウンドロビンで均等化(全体通し・単元境界でリセットしない=0/1偏り回避。choices入替で正解を移動)
  - explanation を最終正答テキストで再構成(【単元】<filter>。正解は「<正答>」。 + 本文)
  - filter ごとに 5問/行に束ねて新規行を作成
  - DATABASE_PUBLIC_URL へ直接 INSERT(exam_id=chugaku, part_key=math, eiken_grade=koukou,
    model=MODEL(=chugaku-koukou-expand-v1 固有・rollback purge/検証用), question_data=json.dumps(ensure_ascii=False))

実行: railway run -s Postgres python3 scripts/chugaku_dojo/append_math.py [--commit]
       (--commit 無しは dry-run: 検証と件数のみ表示・DB無変更)
"""
import os, sys, json, glob, re, hashlib, collections

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add")
UNITS = json.load(open(os.path.join(BASE, "units.json"), encoding="utf-8"))
MATH_FILTERS = [u["filter"] for s in UNITS["subjects"] if s["part"] == "math" for u in s["units"]]
COMMIT = "--commit" in sys.argv
# 新規行だけを識別できる固有 model(post-insert検証 & ロールバック purge 用)
MODEL = "chugaku-koukou-expand-v1"

PREFIX_RE = re.compile(r"^\s*【単元】[^。]*。\s*正解は「.*?」。\s*")
POS_TOKENS = [r"[①-⑳]", r"選択肢\s*[アイウエオABCDａ-ｄ1-4１-４]",
              r"[上下]から\s*[0-9一二三四五六０-９]+\s*(?:番目|つ目)",
              r"[0-9１-４]\s*番目\s*の\s*(?:選択肢|答え|もの)", r"正解は\s*[アイウエ]\b"]
POS_RE = re.compile("|".join(POS_TOKENS))


def load_new():
    rows = []
    for fp in sorted(glob.glob(os.path.join(ADIR, "math__*.json"))):
        data = json.load(open(fp, encoding="utf-8"))
        if not isinstance(data, list):
            print(f"  ⚠️ not-a-list skip: {os.path.basename(fp)}"); continue
        for q in data:
            q["_src"] = os.path.basename(fp)
            rows.append(q)
    return rows


def validate(q, problems):
    filt = q.get("filter")
    if q.get("part") != "math":
        problems.append(("bad_part", q.get("_src"), q.get("part"))); return False
    if filt not in MATH_FILTERS:
        problems.append(("bad_filter", q.get("_src"), filt)); return False
    ch = q.get("choices")
    if not isinstance(ch, list) or len(ch) != 4 or any((not isinstance(c, str) or not c.strip()) for c in ch):
        problems.append(("bad_choices", q.get("_src"), f"{filt}: {ch}")); return False
    if len(set(c.strip() for c in ch)) != 4:
        problems.append(("dup_choices", q.get("_src"), f"{filt}: {ch}")); return False
    ai = q.get("answer_index")
    if not isinstance(ai, int) or not (0 <= ai < 4):
        problems.append(("bad_answer_index", q.get("_src"), filt)); return False
    if not isinstance(q.get("stem"), str) or not q["stem"].strip():
        problems.append(("bad_stem", q.get("_src"), filt)); return False
    if not isinstance(q.get("explanation"), str) or not q["explanation"].strip():
        problems.append(("bad_expl", q.get("_src"), filt)); return False
    return True


def rebuild_expl(filt, answer_text, expl):
    body = PREFIX_RE.sub("", expl).strip()
    body = PREFIX_RE.sub("", body).strip()
    return f"【単元】{filt}。正解は「{answer_text}」。" + (body if body else "")


def main():
    import psycopg
    dsn = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_PUBLIC_URL 未設定 (railway run -s Postgres で実行)"); sys.exit(1)
    conn = psycopg.connect(dsn)
    cur = conn.cursor()

    # 既存 chugaku/math の stem 集合(冪等キー) + content hash 集合(行重複ガード)
    cur.execute("SELECT question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key='math'")
    existing_stems = set()
    existing_hashes = set()
    existing_count = collections.Counter()
    for (qd_txt,) in cur.fetchall():
        try:
            qd = json.loads(qd_txt)
        except Exception:
            continue
        existing_hashes.add(hashlib.md5(json.dumps(qd, ensure_ascii=False, sort_keys=True).encode()).hexdigest())
        for q in qd.get("questions", []):
            existing_stems.add((q.get("stem") or "").strip())
            existing_count[q.get("unit") or qd.get("format_type")] += 1
    print("既存 chugaku/math 単元別:", dict(sorted(existing_count.items())))

    rows = load_new()
    print(f"\n追加候補: {len(rows)} 問 ({len(glob.glob(os.path.join(ADIR,'math__*.json')))} files)")
    problems = []
    good = [q for q in rows if validate(q, problems)]
    print(f"バリデーションOK: {len(good)} / {len(rows)}")

    # 重複除去: 既存stem一致 or 追加内stem重複
    seen_stems = set()
    fresh = []
    dup_existing = dup_within = 0
    for q in good:
        s = q["stem"].strip()
        if s in existing_stems:
            dup_existing += 1; continue
        if s in seen_stems:
            dup_within += 1; continue
        seen_stems.add(s); fresh.append(q)
    print(f"重複スキップ: 既存一致 {dup_existing} / 追加内重複 {dup_within}  → 新規 {len(fresh)} 問")

    # 位置トークン lint(シャッフル不可問はそのまま)
    for q in fresh:
        q["_no_shuffle"] = bool(POS_RE.search(PREFIX_RE.sub("", q["explanation"])))

    # 正解位置ラウンドロビン(全体で通し・単元境界でリセットしない=0/1偏りを防ぐ)
    by_filt = collections.defaultdict(list)
    for q in fresh:
        by_filt[q["filter"]].append(q)
    tgt = 0
    for filt in MATH_FILTERS:
        for q in by_filt.get(filt, []):
            if q["_no_shuffle"]:
                continue
            cur_i = q["answer_index"]; want = tgt % 4
            if cur_i != want:
                ch = q["choices"]; ch[cur_i], ch[want] = ch[want], ch[cur_i]
                q["answer_index"] = want
            tgt += 1

    # explanation 再構成
    for q in fresh:
        q["explanation"] = rebuild_expl(q["filter"], q["choices"][q["answer_index"]], q["explanation"])

    # 5問/行に束ねて新規行を作成
    new_rows = []
    for filt in MATH_FILTERS:
        qs = by_filt.get(filt, [])
        for i in range(0, len(qs), 5):
            chunk = qs[i:i+5]
            qd = {
                "passage": "", "subject": "数学", "univ_simulated": "公立高校入試(標準)",
                "year_simulated": None, "source": "chugaku_koukou_v1", "format_type": filt,
                "questions": [
                    {"id": f"q{j+1}", "type": "multiple_choice", "stem": q["stem"],
                     "choices": q["choices"], "answer": str(q["answer_index"]),
                     "unit": q["filter"], "explanation": q["explanation"]}
                    for j, q in enumerate(chunk)
                ],
            }
            h = hashlib.md5(json.dumps(qd, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            if h in existing_hashes:
                continue  # 万一の行重複ガード
            new_rows.append(qd)

    # 整合チェック
    ans_dist = collections.Counter()
    mism = 0
    for qd in new_rows:
        for q in qd["questions"]:
            ans_dist[q["answer"]] += 1
            want_prefix = f"【単元】{qd['format_type']}。正解は「{q['choices'][int(q['answer'])]}」。"
            if not q["explanation"].startswith(want_prefix):
                mism += 1
    print(f"\n新規行: {len(new_rows)} 行 / {sum(len(r['questions']) for r in new_rows)} 問")
    print(f"正解位置分布(新規): " + " ".join(f"{k}:{ans_dist[k]}" for k in ['0','1','2','3']))
    print(f"解説接頭辞不一致: {mism} (0であるべき)")
    per_filt_new = collections.Counter()
    for qd in new_rows:
        for q in qd["questions"]:
            per_filt_new[q["unit"]] += 1
    print("追加後 単元別 増分:", {f: per_filt_new.get(f, 0) for f in MATH_FILTERS})

    if problems:
        print("\n除外詳細(先頭20):")
        for p in problems[:20]:
            print("  ", p)

    if not COMMIT:
        print("\n[dry-run] --commit 無しのため DB 無変更。")
        cur.close(); conn.close(); return

    if mism:
        print("接頭辞不一致があるため中断。"); cur.close(); conn.close(); sys.exit(1)

    ins = 0
    for qd in new_rows:
        cur.execute(
            "INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) VALUES (%s,%s,%s,%s,%s)",
            ("chugaku", "math", "koukou", json.dumps(qd, ensure_ascii=False), MODEL),
        )
        ins += 1
    conn.commit()
    print(f"\nINSERT 完了: {ins} 行")

    cur.execute("SELECT question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key='math'")
    after = collections.Counter()
    for (qd_txt,) in cur.fetchall():
        try:
            qd = json.loads(qd_txt)
        except Exception:
            continue
        for q in qd.get("questions", []):
            after[q.get("unit") or qd.get("format_type")] += 1
    print("=== 取込後 chugaku/math 単元別 ===")
    for f in MATH_FILTERS:
        print(f"  {after.get(f,0):4}  {f}")
    print("  total:", sum(after.values()))
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
