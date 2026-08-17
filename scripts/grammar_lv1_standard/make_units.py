#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""content/*.py の素データから units/*.json を組み立てる。

★手で書くと必ず壊れる3か所を、人間に触らせずここで機械的に決める:

  1. answer_index / answer_text
     素データは正解を**文字列**でしか持たない。番号は choices から引き直すので、
     青学の教材を実際に壊した [MC MATCH](choices[answer_index] != answer_text)が
     構造的に起こりえない。

  2. 正解の位置
     素データの choices の並びは「教えやすい順」で書いてある(正解が先頭に来がち)。
     単元ごとに固定の配列 POSITIONS で 0-3 を配り直す。全体で均すのではなく
     **単元ごとに**均すのは、生徒が単元単位で解くから(CLAUDE.md の共通テスト模試と同じ理由)。

  3. 整序問題の tokens
     answer から機械的に切り出して並べ替える。手で書き写すと語の過不足が起きるし、
     既存の grammar_workbook では **4問が answer と同じ並びのまま**印字されていて
     答えがそのまま問題編に出ていた。ここでは shuffle 後に同一並びを禁止する。

使い方: python3 scripts/grammar_lv1_standard/make_units.py
        (--check を付けると書き込まずに既存 JSON との一致だけを見る)
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS_DIR = os.path.join(HERE, "units")
sys.path.insert(0, HERE)

from content import tenses, infinitive, gerund, subjunctive  # noqa: E402

MODULES = [
    ("01_tenses.json", tenses),
    ("02_infinitive.json", infinitive),
    ("03_gerund.json", gerund),
    ("04_subjunctive.json", subjunctive),
]

# 単元ごとの正解位置の配り方(mc 18問ぶん)。
# ★「全体で均等」ではなく単元内で 0-3 が 4-5 回ずつ、同じ位置が3連続しないよう手で組んだ。
#   乱数で作ると再現できず、差分が毎回暴れて査読できない。
POSITIONS = {
    "01_tenses.json":     [2, 0, 3, 1, 0, 2, 1, 3, 2, 0, 1, 3, 0, 2, 3, 1, 0, 2],
    "02_infinitive.json": [1, 3, 0, 2, 3, 1, 2, 0, 1, 3, 2, 0, 3, 1, 0, 2, 1, 3],
    "03_gerund.json":     [3, 1, 2, 0, 1, 3, 0, 2, 3, 1, 0, 2, 1, 3, 2, 0, 3, 1],
    "04_subjunctive.json": [0, 2, 1, 3, 2, 0, 3, 1, 0, 2, 3, 1, 2, 0, 1, 3, 2, 0],
}

# 整序の tokens をどう混ぜるか。answer の語数ごとに固定の置換を持つ。
# ★乱数を使わない(seed を変えると全問の tokens が入れ替わり、差分が読めなくなる)。
#   語数 n に対して「i 番目の語を (i*STEP+OFFSET) % n 番目に置く」形の巡回置換を使う。
#   n と STEP が互いに素なら全単射になるので語の過不足が起きない。
_SHUFFLE_STEP = 5
_SHUFFLE_OFFSET = 2


def shuffle_tokens(words):
    """語の集合を保ったまま並べ替える。決定的で、n によらず全単射。"""
    n = len(words)
    step = _SHUFFLE_STEP
    while _gcd(step, n) != 1:      # n が step の倍数だと巡回にならない
        step += 1
    out = [None] * n
    for i, w in enumerate(words):
        out[(i * step + _SHUFFLE_OFFSET) % n] = w
    return out


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def split_tokens(answer):
    """整序の選択肢に出す語の並びを answer から切り出す。

    文末の . ? ! だけ落とし、文中のコンマは語にくっつけたまま残す
    (既存 grammar_workbook の慣行に合わせる。コンマは切れ目のヒントとして生徒に見せる)。
    """
    words = answer.split()
    words[-1] = re.sub(r"[.?!]+$", "", words[-1])
    if not words[-1]:
        raise ValueError(f"最後の語が句読点だけになった: {answer!r}")
    return words


def build_unit(fname, mod):
    qs = list(mod.QUESTIONS)
    mcs = [q for q in qs if q["type"] == "mc"]
    pos = POSITIONS[fname]
    if len(pos) != len(mcs):
        raise ValueError(f"{fname}: POSITIONS {len(pos)} 個 != mc {len(mcs)} 問")

    out = []
    mc_i = 0
    for no, q in enumerate(qs, start=1):
        t = q["type"]
        rec = {"no": no, "type": t, "level": q["level"]}
        if t == "mc":
            choices = list(q["choices"])
            ans = q["answer"]
            if ans not in choices:
                raise ValueError(f"{fname}#{no}: answer {ans!r} が choices に無い")
            if len(choices) != 4:
                raise ValueError(f"{fname}#{no}: choices が {len(choices)} 個")
            # 正解を目標位置へ移し、残りは元の相対順を保つ
            want = pos[mc_i]
            mc_i += 1
            rest = [c for c in choices if c != ans]
            reordered = rest[:want] + [ans] + rest[want:]
            rec["stem"] = q["stem"]
            rec["choices"] = reordered
            rec["answer_index"] = reordered.index(ans)   # ★手で書かない
            rec["answer_text"] = reordered[rec["answer_index"]]
        elif t == "order":
            words = split_tokens(q["answer"])
            toks = shuffle_tokens(words)
            if toks == words:
                raise ValueError(f"{fname}#{no}: tokens が答えと同じ並びになった(答えの漏洩)")
            rec["prompt_ja"] = q["prompt_ja"]
            rec["tokens"] = toks
            rec["answer_text"] = q["answer"]
        elif t == "rewrite":
            rec["original"] = q["original"]
            rec["instruction"] = q["instruction"]
            rec["answer_text"] = q["answer"]
        else:
            raise ValueError(f"{fname}#{no}: 未知の type {t!r}")
        rec["explanation"] = q["explanation"]
        rec["point"] = q["point"]
        out.append(rec)

    return {"unit": mod.UNIT, "unit_slug": mod.UNIT_SLUG, "questions": out}


def build_all():
    return {fname: build_unit(fname, mod) for fname, mod in MODULES}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="書き込まず、既存 units/*.json と一致するかだけ見る")
    a = ap.parse_args()

    built = build_all()
    os.makedirs(UNITS_DIR, exist_ok=True)
    ng = 0
    for fname, data in built.items():
        path = os.path.join(UNITS_DIR, fname)
        text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        if a.check:
            if not os.path.exists(path):
                print(f"  ✗ {fname}: 出力が無い")
                ng += 1
                continue
            with open(path, encoding="utf-8") as f:
                cur = f.read()
            if cur != text:
                print(f"  ✗ {fname}: content/*.py から作り直した内容と一致しない"
                      "(JSON を直接編集した可能性がある。content/ 側を直して作り直すこと)")
                ng += 1
            else:
                print(f"  OK {fname}: 素データと一致")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            n = len(data["questions"])
            print(f"  書き出し {fname}: {data['unit']} {n} 問")
    if ng:
        sys.exit(1)


if __name__ == "__main__":
    main()
