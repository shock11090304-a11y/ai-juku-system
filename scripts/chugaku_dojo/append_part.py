#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中学ドリル(英/国/理/社)の追加問題を part 指定で append-only 投入。既存行は不変・新規行のみ追記。
非読解=5問/行に束ね。読解(passage有)=passage毎に1行。model=chugaku-<part>-expand-v1(rollback purge用)。
usage: railway run -s Postgres python3 scripts/chugaku_dojo/append_part.py <part> [--commit]
"""
import os, sys, json, glob, re, hashlib, collections

BASE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(BASE, "add2")
UNITS = json.load(open(os.path.join(BASE, "units.json"), encoding="utf-8"))
PART = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
COMMIT = "--commit" in sys.argv
if PART not in {s["part"] for s in UNITS["subjects"]}:
    print("part を指定してください (eng/kokugo/rika/shakai)"); sys.exit(1)
SUBJ = {s["part"]: s["subj"] for s in UNITS["subjects"]}[PART]
FILTERS = [u["filter"] for s in UNITS["subjects"] if s["part"] == PART for u in s["units"]]
READING = {u["filter"] for s in UNITS["subjects"] if s["part"] == PART for u in s["units"] if u.get("reading")}
MODEL = f"chugaku-{PART}-expand-v1"

PREFIX_RE = re.compile(r"^\s*【単元】[^。]*。\s*正解は「.*?」。\s*")
POS_TOKENS = [r"[①-⑳]", r"選択肢\s*[アイウエオABCDａ-ｄ1-4１-４]",
              r"[上下]から\s*[0-9一二三四五六０-９]+\s*(?:番目|つ目)",
              r"[0-9１-４]\s*番目\s*の\s*(?:選択肢|答え|もの)", r"正解は\s*[アイウエ]\b"]
POS_RE = re.compile("|".join(POS_TOKENS))


def rebuild_expl(filt, ans_text, expl):
    body = PREFIX_RE.sub("", expl).strip()
    body = PREFIX_RE.sub("", body).strip()
    return f"【単元】{filt}。正解は「{ans_text}」。" + (body if body else "")


def main():
    import psycopg
    dsn = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_PUBLIC_URL 未設定"); sys.exit(1)
    conn = psycopg.connect(dsn); cur = conn.cursor()
    cur.execute("SELECT question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key=%s", (PART,))
    existing_stems, existing_hashes, existing_count = set(), set(), collections.Counter()
    for (t,) in cur.fetchall():
        try: qd = json.loads(t)
        except Exception: continue
        existing_hashes.add(hashlib.md5(json.dumps(qd, ensure_ascii=False, sort_keys=True).encode()).hexdigest())
        for q in qd.get("questions", []):
            existing_stems.add((q.get("stem") or "").strip()); existing_count[q.get("unit") or qd.get("format_type")] += 1
    print(f"既存 chugaku/{PART} 単元別:", dict(sorted(existing_count.items())))

    rows = []
    for fp in sorted(glob.glob(os.path.join(ADIR, f"{PART}__*.json"))):
        for q in json.load(open(fp, encoding="utf-8")):
            q["_src"] = os.path.basename(fp); rows.append(q)
    print(f"追加候補: {len(rows)} 問")

    # 文字化けガード: 日本語/英語教材にハングル等の混入は不正
    HANGUL = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")

    problems = []
    good = []
    for q in rows:
        filt = q.get("filter")
        ch = q.get("choices"); ai = q.get("answer_index")
        blob = (q.get("stem") or "") + (q.get("explanation") or "") + " ".join(q.get("choices") or []) + (q.get("passage") or "")
        if HANGUL.search(blob):
            problems.append(("hangul_corruption", q.get("_src"), filt)); continue
        if q.get("part") != PART or filt not in FILTERS:
            problems.append(("bad_unit", q.get("_src"), filt)); continue
        if not isinstance(ch, list) or len(ch) != 4 or len(set(str(c).strip() for c in ch)) != 4:
            problems.append(("bad_choices", q.get("_src"), filt)); continue
        if not isinstance(ai, int) or not (0 <= ai < 4):
            problems.append(("bad_ai", q.get("_src"), filt)); continue
        if not (q.get("stem") or "").strip() or not (q.get("explanation") or "").strip():
            problems.append(("empty", q.get("_src"), filt)); continue
        good.append(q)
    print(f"バリデーションOK: {len(good)}/{len(rows)}")

    seen = set(); fresh = []
    de = dw = 0
    for q in good:
        s = q["stem"].strip()
        if s in existing_stems: de += 1; continue
        if s in seen: dw += 1; continue
        seen.add(s); fresh.append(q)
    print(f"重複スキップ: 既存{de}/追加内{dw} → 新規 {len(fresh)}")

    for q in fresh:
        # 位置トークンを含む解説だけシャッフル除外(読解も値参照解説ならシャッフル可=位置均等化)
        q["_no_shuffle"] = bool(POS_RE.search(PREFIX_RE.sub("", q["explanation"])))

    by_filt = collections.defaultdict(list)
    for q in fresh: by_filt[q["filter"]].append(q)
    # 正解位置ラウンドロビン(全体通し・reading/位置トークン問は据え置き)
    tgt = 0
    for filt in FILTERS:
        for q in by_filt.get(filt, []):
            if q["_no_shuffle"]: continue
            want = tgt % 4; cur_i = q["answer_index"]
            if cur_i != want:
                c = q["choices"]; c[cur_i], c[want] = c[want], c[cur_i]; q["answer_index"] = want
            tgt += 1
    for q in fresh:
        q["explanation"] = rebuild_expl(q["filter"], q["choices"][q["answer_index"]], q["explanation"])

    def make_qd(filt, passage, qs):
        return {"passage": passage or "", "subject": SUBJ, "univ_simulated": "公立高校入試(標準)",
                "year_simulated": None, "source": "chugaku_koukou_v1", "format_type": filt,
                "questions": [{"id": f"q{j+1}", "type": "multiple_choice", "stem": q["stem"],
                               "choices": q["choices"], "answer": str(q["answer_index"]),
                               "unit": q["filter"], "explanation": q["explanation"]} for j, q in enumerate(qs)]}

    new_rows = []
    for filt in FILTERS:
        qs = by_filt.get(filt, [])
        if not qs: continue
        if filt in READING:
            groups = collections.OrderedDict()
            for q in qs:
                groups.setdefault((q.get("passage") or "").strip() or "(none)", []).append(q)
            for pas, gq in groups.items():
                new_rows.append(make_qd(filt, "" if pas == "(none)" else pas, gq))
        else:
            for i in range(0, len(qs), 5):
                new_rows.append(make_qd(filt, "", qs[i:i+5]))

    ans = collections.Counter(); mism = 0; per_new = collections.Counter()
    for qd in new_rows:
        for q in qd["questions"]:
            ans[q["answer"]] += 1; per_new[q["unit"]] += 1
            if not q["explanation"].startswith(f"【単元】{qd['format_type']}。正解は「{q['choices'][int(q['answer'])]}」。"): mism += 1
    print(f"新規行 {len(new_rows)} / 問 {sum(len(r['questions']) for r in new_rows)}")
    print("正解位置分布:", " ".join(f"{k}:{ans[k]}" for k in ['0', '1', '2', '3']))
    print("解説接頭辞不一致:", mism, "(0であるべき)")
    print("単元別増分:", {f: per_new.get(f, 0) for f in FILTERS})
    if problems:
        print("除外:", problems[:15])

    if not COMMIT:
        print("[dry-run] DB無変更。"); cur.close(); conn.close(); return
    if mism:
        print("接頭辞不一致で中断"); sys.exit(1)

    ins = 0
    for qd in new_rows:
        h = hashlib.md5(json.dumps(qd, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if h in existing_hashes: continue
        cur.execute("INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model) VALUES (%s,%s,%s,%s,%s)",
                    ("chugaku", PART, "koukou", json.dumps(qd, ensure_ascii=False), MODEL))
        ins += 1
    conn.commit()
    print(f"INSERT 完了: {ins} 行 (model={MODEL})")
    cur.execute("SELECT question_data FROM exam_questions WHERE exam_id='chugaku' AND part_key=%s", (PART,))
    after = collections.Counter()
    for (t,) in cur.fetchall():
        qd = json.loads(t)
        for q in qd.get("questions", []): after[q.get("unit") or qd.get("format_type")] += 1
    print(f"=== 取込後 chugaku/{PART} 単元別 ===")
    for f in FILTERS: print(f"  {after.get(f,0):3}  {f}")
    print("  total:", sum(after.values()))
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
