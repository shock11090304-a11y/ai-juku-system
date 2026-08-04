#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英語ネイティブ観点のレビュー指摘を単一ソースへ反映する(冪等・全件 assert つき)。

  python3 apply_en_fixes.py

★形式ラベルを直すワークフローと同じ JSON を触るので、必ずそちらの完了後に実行すること。
"""
import os, re, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
applied, skipped = [], []


def load(no, kind="passages"):
    p = os.path.join(HERE, kind, f"p{no:02d}.json")
    return p, (json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None)


def sub_all(d, old, new, fields=("passage", "title", "translation_ja")):
    """本文系フィールド＋全設問の文字列フィールドを一括置換。置換件数を返す。"""
    n = 0
    for f in fields:
        if isinstance(d.get(f), str) and old in d[f]:
            n += d[f].count(old)
            d[f] = d[f].replace(old, new)
    for q in d.get("questions", []):
        for k in ("q", "evidence", "explanation_ja", "distractor_ja"):
            if isinstance(q.get(k), str) and old in q[k]:
                n += q[k].count(old)
                q[k] = q[k].replace(old, new)
        if "options" in q:
            for i, o in enumerate(q["options"]):
                if old in o:
                    n += o.count(old)
                    q["options"][i] = o.replace(old, new)
    for g in d.get("glossary", []):
        for k in ("word", "ja"):
            if old in (g.get(k) or ""):
                n += g[k].count(old)
                g[k] = g[k].replace(old, new)
    return n


# (題, 置換前, 置換後, 必須か) — 必須は1件も当たらなければ落とす
EDITS = [
    # ── 明らかな誤り ─────────────────────────────────────────────
    (2,  "bookstores are the perfect partner for", "bookstores are the perfect partners for", True),
    (4,  "neighbours", "neighbors", True),
    (4,  "litres", "liters", True),
    (4,  "litre", "liter", True),
    (10, "上着の値段で人を判断されることはない", "上着の値段で人が判断されることはない", True),
    (4,  "彼女と姉妹は", "彼女と妹は", True),
    (6,  "枝を刈り込ま(剪定し)なければならないし", "枝を刈り込む(剪定する)必要があるし", False),
    # ★私の Day 振り直しの取り残し(本文は Day 10 なのに解説だけ Day 9)
    (3,  "Day 9", "Day 10", False),
    (3,  "9日目", "10日目", False),
    (3,  "9 日目", "10 日目", False),
    # ── 正解肢に共テ超えの語(fetch は B2・英用法) ──────────────
    (4,  "Fetching water took up time", "Carrying water took up time", True),
    # ── 金額は数字が原則(本文も 600 yen a month) ────────────────
    (8,  "six hundred yen every month", "600 yen a month", True),
    # ── ネイティブが書かない言い回し ─────────────────────────
    (3,  "I sat in a history lesson", "I sat in on a history lesson", True),
    (3,  "waiting until my English is perfect before I open my mouth",
         "waiting for my English to be perfect before I open my mouth", True),
    (8,  "even then the machine sometimes accepts", "even then it sometimes accepts", True),
    (6,  "reports that they change how a city works",
         "reports that these green spaces change how a city works", True),
    (6,  "are not only decoration", "are not just decoration", True),
    (1,  "There is now a bright reading room", "There are now a bright reading room", True),
    (4,  "After finishing school she studied", "After finishing school, she studied", True),
    (8,  "for building vocabulary and it fits easily", "for building vocabulary, and it fits easily", True),
    (1,  "every item may be renewed one time", "every item may be renewed once", True),
    (5,  "than that of first-year students", "than that for first-year students", True),
    (3,  "for one final farewell lesson", "for one last lesson", True),
    (6,  "with each passing year", "every year", True),
    (1,  "university student volunteers", "student volunteers from a local university", True),
    (9,  "information about the kind of danger coming",
         "information about the kind of danger that was coming", True),
    (10, "because heavy wool in June is a real problem",
         "because a heavy wool jacket in June is a real problem", True),
    (10, "and satisfaction rose sharply", "and student satisfaction rose sharply", True),
    # ── 根拠のない節(本文は「昨年の春」開始で、in April が今年なら "soon after" は出ない) ──
    (2,  "He began taking part in the project in April, soon after it started.",
         "He began taking part in the project in April.", True),
]

# 語注の追加(正誤の鍵になるのに無注だった B2 語)と削除(共テレベルの過剰注)
GLOSS_ADD = {6: [("housing", "住宅")], 10: [("wardrobe", "手持ちの服(ひとそろい)")],
             8: [("complaint", "不満・苦情")], 4: [("cupful", "コップ1杯分")],
             7: [("wheat", "小麦")]}
GLOSS_DEL = {6: ["concrete"], 1: ["fee"]}


def main():
    for no in range(1, 11):
        p, d = load(no)
        sp, sd = load(no, "stems")
        before = json.dumps(d, ensure_ascii=False, sort_keys=True)

        for tno, old, new, must in EDITS:
            if tno != no:
                continue
            n = sub_all(d, old, new)
            if sd:
                sub_all(sd, old, new)
            (applied if n else skipped).append(f"p{no:02d}: {old[:42]!r} → {new[:42]!r} ({n}件)")
            if must and not n:
                sys.exit(f"★置換対象が見つからない(仕様変更の疑い): p{no:02d} {old!r}")

        gl = d.setdefault("glossary", [])
        for w, ja in GLOSS_ADD.get(no, []):
            if w in d["passage"] and not any(g["word"] == w for g in gl):
                gl.append({"word": w, "ja": ja})
                applied.append(f"p{no:02d}: 語注に「{w}」を追加")
        for w in GLOSS_DEL.get(no, []):
            if any(g["word"] == w for g in gl):
                d["glossary"] = [g for g in gl if g["word"] != w]
                applied.append(f"p{no:02d}: 語注から「{w}」を削除(共テ範囲内)")
        if sd is not None:
            sd["glossary"] = d["glossary"]

        # word_count を実測に合わせる
        wc = len([w for w in re.split(r"[^A-Za-z'’\-]+", re.sub(r"</?u>", "", d["passage"])) if w])
        if d.get("word_count") != wc:
            applied.append(f"p{no:02d}: word_count {d.get('word_count')} → {wc}")
            d["word_count"] = wc
        if not (240 <= wc <= 260):
            sys.exit(f"★p{no:02d} の語数が {wc} 語になった(240〜260を外れた)")

        if json.dumps(d, ensure_ascii=False, sort_keys=True) != before:
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if sd is not None:
            json.dump(sd, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # p06 の evidence: 離れた2文を連結していたので " / " を入れる
    p, d = load(6)
    for q in d["questions"]:
        ev = q.get("evidence", "")
        m = re.search(r"(how a city works\.) (However)", ev)
        if m:
            q["evidence"] = ev.replace(m.group(0), f"{m.group(1)} / {m.group(2)}")
            applied.append("p06: evidence の離れた2文に ' / ' を挿入")
        m2 = re.search(r"(air conditioning\.) (In many cities)", ev)
        if m2:
            q["evidence"] = q["evidence"].replace(m2.group(0), f"{m2.group(1)} / {m2.group(2)}")
            applied.append("p06: evidence の離れた2文に ' / ' を挿入")
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"適用 {len(applied)} 件 / 対象なし {len(skipped)} 件\n")
    for s in applied:
        print("  ✓ " + s)
    if skipped:
        print()
        for s in skipped:
            print("  - " + s)


if __name__ == "__main__":
    main()
