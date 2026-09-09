# -*- coding: utf-8 -*-
"""時制 / 接続詞 / 疑問詞・間接疑問 の英文法ドリル 90 問を組み立てて seed JSON にする。

    python3 scripts/eng_drill_jisei_setsuzoku_gimon/build.py

入力  scripts/eng_drill_jisei_setsuzoku_gimon/content.py   … 正典 (正解は文字列で持つ)
出力  seed-data/grammar_drill_pool_v2_jisei_setsuzoku_gimon.json  … /api/admin/grammar/import 用
      scripts/eng_drill_jisei_setsuzoku_gimon/blind_view.json     … 盲解き用 (正解・解説なし)

★正解の位置は (単元, レベル) ごとに 0→1→2→3 のラウンドロビンで割り当てる。
  手で番号を振ると必ず偏る (2026-08-02 の指摘)。番号を書かない = 偏りようがない、にする。
★このファイルの出力は check.py が再生成して1バイト単位で照合する。JSON を手で直さない。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _rules   # noqa: E402
import content  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
SEED_PATH = os.path.join(BASE, "..", "..", "seed-data", "grammar_drill_pool_v2_jisei_setsuzoku_gimon.json")
BLIND_PATH = os.path.join(BASE, "blind_view.json")

BLANK = _rules.BLANK


def build():
    """content.Q から (seed 用の dict のリスト, 盲解き用のリスト) を作る。

    ★ここでは「組み立てられるか」だけを見る。良し悪しの判定は _rules.validate() の一本道に通す
      (build と check で判定が二重になると、片方だけ直されてずれる)。
    """
    out, blind = [], []
    pos = {}
    for i, (ukey, level, stem, choices, ans_text, expl) in enumerate(content.Q):
        unit = content.UNIT_MAP.get(ukey, ukey)
        if ans_text not in choices:            # 正解の位置を決められない = 組み立て不能
            raise ValueError(f"answer_text が choices に無い: {stem} / {ans_text}")

        # (単元, レベル) ごとのラウンドロビンで正解位置を決める
        key = (unit, level)
        target = pos.get(key, 0) % 4
        pos[key] = pos.get(key, 0) + 1
        distractors = [c for c in choices if c != ans_text]   # 元の相対順を保つ
        new_choices, di = [], 0
        for p in range(len(choices)):
            if p == target:
                new_choices.append(ans_text)
            elif di < len(distractors):
                new_choices.append(distractors[di])
                di += 1

        out.append({
            "unit": unit,
            "level": level,
            "stem": stem,
            "choices": new_choices,
            "answer": target,                 # 0 始まりの index
            "explanation": expl,
            "source": content.SOURCE,
            "subject": content.SUBJECT,
        })
        blind.append({"n": i, "unit": unit, "level": level, "stem": stem, "choices": new_choices})
    return out, blind


def seed_document(rows):
    return {
        "_meta": {
            "source": content.SOURCE,
            "note": "英文法ドリル補充 v2: 時制/接続詞/疑問詞・間接疑問 の3単元 x 基礎30/標準36/やや難30。"
                    "正典は scripts/eng_drill_jisei_setsuzoku_gimon/content.py。"
                    "正解位置は (単元,レベル) ごとのラウンドロビン。解説は値参照 (位置トークンを書かない)。"
                    "投入先は /api/admin/grammar/import (grammar_questions)。",
            "count": len(rows),
        },
        "questions": rows,
    }


def answers():
    """正典 (content.py) が持つ正解の文字列。JSON の answer(index) と突き合わせるのに使う。"""
    return [q[4] for q in content.Q]


def main():
    rows, blind = build()
    ng = _rules.validate(rows, answers(), os.path.normpath(os.path.join(BASE, "..", "..")))
    if ng:
        print(f"違反 {len(ng)} 件 — JSON は書き出さない")
        for m in ng:
            print(" ", m)
        sys.exit(1)
    with open(SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(seed_document(rows), f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(BLIND_PATH, "w", encoding="utf-8") as f:
        json.dump(blind, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"生成 {len(rows)} 問")
    report = _rules.position_report(rows)
    for k in sorted(report):
        print(f"  {k[0]:<12s} {k[1]:<9s} 正解位置 {report[k]}")
    print("出力:", os.path.relpath(SEED_PATH, os.path.join(BASE, "..", "..")))
    print("出力:", os.path.relpath(BLIND_PATH, os.path.join(BASE, "..", "..")))


if __name__ == "__main__":
    main()
