#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中学生(公立高校入試 標準) 弱点克服ドリル: verified/*.json → 検証・正解位置ラウンドロビン・行束ね・取込チャンク生成。

入力: scripts/chugaku_dojo/verified/<part>__<idx>.json
        [{subject, part, filter, unit, stem, passage, choices[4], answer_index, explanation}, ...]
出力:
  batches/all_rows.json            全 import 行 (exam_id/part_key/eiken_grade/question_data/model)
  batches/chunks/<part>_<k>.json   4行/ファイル (import API 用チャンク)
  report を stdout に。
規約:
  - explanation は 【単元】<filter>。正解は「<正答テキスト>」。 を先頭に強制再構成(値参照=シャッフル安全)。
  - answer は 0始まり index の文字列。type=multiple_choice。
  - source=chugaku_koukou_v1 / model=chugaku-koukou-verified (rollback 用)。
"""
import json, os, re, glob, hashlib, collections

BASE = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(BASE, "verified")
BATCH = os.path.join(BASE, "batches")
CHUNK = os.path.join(BATCH, "chunks")
os.makedirs(CHUNK, exist_ok=True)

UNITS = json.load(open(os.path.join(BASE, "units.json"), encoding="utf-8"))
VALID = {}   # part -> set(filters)
SUBJ_OF_PART = {}
READING = set()  # (part, filter)
for s in UNITS["subjects"]:
    VALID[s["part"]] = set(u["filter"] for u in s["units"])
    SUBJ_OF_PART[s["part"]] = s["subj"]
    for u in s["units"]:
        if u.get("reading"):
            READING.add((s["part"], u["filter"]))

# 「選択肢の位置」を指す表現だけを検出 (シャッフルで陳腐化する解説を弾く)。
#   ★計算順の「左から順に」等は誤検出しないよう、方向語は「番目/つ目」を伴う場合のみ。
CHOICE_POS_TOKENS = [
    r"[①-⑳]",                                          # 丸数字ラベル
    r"選択肢\s*[アイウエオABCDａ-ｄ1-4１-４]",             # 「選択肢ア/A/1」
    r"[上下]から\s*[0-9一二三四五六０-９]+\s*(?:番目|つ目)",  # 「上から2番目」
    r"[0-9１-４]\s*番目\s*の\s*(?:選択肢|答え|もの)",       # 「2番目の選択肢/答え」
    r"正解は\s*[アイウエ]\b",                             # 「正解はア」(ラベル指し)
]
POS_RE = re.compile("|".join(CHOICE_POS_TOKENS))

# 先頭の 【単元】…。正解は「…」。 を1つ剥がす(緩め)
PREFIX_RE = re.compile(r"^\s*【単元】[^。]*。\s*正解は「.*?」。\s*")

def load_all():
    rows = []
    for fp in sorted(glob.glob(os.path.join(VDIR, "*.json"))):
        try:
            data = json.load(open(fp, encoding="utf-8"))
        except Exception as e:
            print(f"  ⚠️ JSON parse失敗 skip: {os.path.basename(fp)}: {e}")
            continue
        if not isinstance(data, list):
            print(f"  ⚠️ not-a-list skip: {os.path.basename(fp)}")
            continue
        for q in data:
            q["_src"] = os.path.basename(fp)
            rows.append(q)
    return rows

def valid_question(q, problems):
    part = q.get("part"); filt = q.get("filter")
    if part not in VALID:
        problems.append(("bad_part", q.get("_src"), part)); return False
    if filt not in VALID[part]:
        problems.append(("bad_filter", q.get("_src"), f"{part}/{filt}")); return False
    ch = q.get("choices")
    if not isinstance(ch, list) or len(ch) != 4 or any((not isinstance(c, str) or not c.strip()) for c in ch):
        problems.append(("bad_choices", q.get("_src"), f"{part}/{filt}")); return False
    if len(set(c.strip() for c in ch)) != 4:
        problems.append(("dup_choices", q.get("_src"), f"{part}/{filt}: {ch}")); return False
    ai = q.get("answer_index")
    if not isinstance(ai, int) or not (0 <= ai < 4):
        problems.append(("bad_answer_index", q.get("_src"), f"{part}/{filt}")); return False
    if not isinstance(q.get("stem"), str) or not q["stem"].strip():
        problems.append(("bad_stem", q.get("_src"), f"{part}/{filt}")); return False
    if not isinstance(q.get("explanation"), str) or not q["explanation"].strip():
        problems.append(("bad_expl", q.get("_src"), f"{part}/{filt}")); return False
    return True

def rebuild_expl(filt, answer_text, expl):
    body = PREFIX_RE.sub("", expl).strip()
    body = PREFIX_RE.sub("", body).strip()  # まれに二重
    return f"【単元】{filt}。正解は「{answer_text}」。" + (body if body else "")

def main():
    rows = load_all()
    print(f"読み込み: {len(rows)} 問 (verified/*.json {len(glob.glob(os.path.join(VDIR,'*.json')))} files)")
    problems = []
    good = [q for q in rows if valid_question(q, problems)]
    print(f"検証OK: {len(good)} / {len(rows)}  (除外 {len(rows)-len(good)})")

    # unit 正規化 + explanation 位置トークン lint
    pos_flagged = 0
    for q in good:
        q["unit"] = q["filter"]  # unit は filter に固定 (unitExact/bank LIKE 一致)
        if POS_RE.search(PREFIX_RE.sub("", q["explanation"])):
            q["_no_shuffle"] = True; pos_flagged += 1
        else:
            q["_no_shuffle"] = False
    print(f"位置トークンで shuffle 除外: {pos_flagged} 問 (該当問は作問時の位置を保持)")

    # 正解位置ラウンドロビン (part 単位で 0..3 巡回・shuffle 可能な問のみ)
    by_part = collections.defaultdict(list)
    for q in good:
        by_part[q["part"]].append(q)
    for part, qs in by_part.items():
        tgt = 0
        for q in qs:
            if q["_no_shuffle"]:
                continue
            cur = q["answer_index"]
            want = tgt % 4
            if cur != want:
                ch = q["choices"]
                ch[cur], ch[want] = ch[want], ch[cur]
                q["answer_index"] = want
            tgt += 1

    # explanation を最終正解テキストで再構成 (シャッフル後の値で確定)
    for q in good:
        q["explanation"] = rebuild_expl(q["filter"], q["choices"][q["answer_index"]], q["explanation"])

    # 行束ね: reading は passage ごと1行 / 非reading は unit ごと最大5問/行
    rows_out = []
    def make_row(part, filt, passage, qlist):
        subj = SUBJ_OF_PART[part]
        qd = {
            "passage": passage or "",
            "subject": subj,
            "univ_simulated": "公立高校入試(標準)",
            "year_simulated": None,
            "source": "chugaku_koukou_v1",
            "format_type": filt,
            "questions": [
                {
                    "id": f"q{i+1}",
                    "type": "multiple_choice",
                    "stem": q["stem"],
                    "choices": q["choices"],
                    "answer": str(q["answer_index"]),
                    "unit": q["filter"],
                    "explanation": q["explanation"],
                } for i, q in enumerate(qlist)
            ],
        }
        return {"exam_id": "chugaku", "part_key": part, "eiken_grade": "koukou",
                "question_data": qd, "model": "chugaku-koukou-verified"}

    for part in ["eng", "math", "kokugo", "rika", "shakai"]:
        for filt in [u["filter"] for s in UNITS["subjects"] if s["part"] == part for u in s["units"]]:
            qs = [q for q in by_part.get(part, []) if q["filter"] == filt]
            if not qs:
                continue
            if (part, filt) in READING:
                groups = collections.OrderedDict()
                for q in qs:
                    groups.setdefault(q.get("passage", "") or "(no-passage)", []).append(q)
                for passage, gq in groups.items():
                    rows_out.append(make_row(part, filt, (passage if passage != "(no-passage)" else ""), gq))
            else:
                for i in range(0, len(qs), 5):
                    rows_out.append(make_row(part, filt, "", qs[i:i+5]))

    # dedup guard (content md5) — 念のため
    seen = set(); uniq = []
    for r in rows_out:
        h = hashlib.md5(json.dumps(r["question_data"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h); uniq.append(r)
    rows_out = uniq

    json.dump(rows_out, open(os.path.join(BATCH, "all_rows.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # チャンク (4行/ファイル・part 混在しないように part ごとに割る)
    nchunk = 0
    for part in ["eng", "math", "kokugo", "rika", "shakai"]:
        pr = [r for r in rows_out if r["part_key"] == part]
        for k in range(0, len(pr), 4):
            fn = os.path.join(CHUNK, f"{part}_{k//4:02d}.json")
            json.dump({"questions": pr[k:k+4], "skip_full": False}, open(fn, "w", encoding="utf-8"), ensure_ascii=False)
            nchunk += 1

    # レポート
    print("\n=== レポート ===")
    per_part_q = collections.Counter()
    per_part_rows = collections.Counter()
    ans_dist = collections.Counter()
    for r in rows_out:
        per_part_rows[r["part_key"]] += 1
        for q in r["question_data"]["questions"]:
            per_part_q[r["part_key"]] += 1
            ans_dist[q["answer"]] += 1
    for part in ["eng", "math", "kokugo", "rika", "shakai"]:
        nunits = len(set(q["filter"] for q in by_part.get(part, [])))
        print(f"  {SUBJ_OF_PART[part]:3}({part:6}): 単元{nunits:2}  問{per_part_q[part]:3}  行{per_part_rows[part]:3}")
    total_q = sum(per_part_q.values())
    print(f"  合計: 問 {total_q}  行 {len(rows_out)}  チャンク {nchunk}")
    print(f"  正解位置分布: " + " ".join(f"{k}:{ans_dist[k]}" for k in ['0','1','2','3']))

    # 整合チェック: 再構成した接頭辞 (【単元】<filt>。正解は「<正答>」。) が先頭にあるか。
    #   ★正答テキスト自体が「」を含む(文学読解の引用等)ケースがあるため regex 抽出でなく exact prefix 照合。
    mism = 0
    for r in rows_out:
        filt = r["question_data"]["format_type"]
        for q in r["question_data"]["questions"]:
            ans_txt = q["choices"][int(q["answer"])]
            want_prefix = f"【単元】{filt}。正解は「{ans_txt}」。"
            if not q["explanation"].startswith(want_prefix):
                mism += 1
    print(f"  解説の正答接頭辞不一致: {mism} 問 (0であるべき)")
    # 【単元】接頭辞チェック
    noprefix = sum(1 for r in rows_out for q in r["question_data"]["questions"] if not q["explanation"].startswith("【単元】"))
    print(f"  【単元】接頭辞なし: {noprefix} 問 (0であるべき)")

    if problems:
        print("\n=== 除外詳細 (先頭20) ===")
        for p in problems[:20]:
            print("  ", p)

if __name__ == "__main__":
    main()
