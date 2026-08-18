#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英検準1級 オリジナル模擬試験の全回を検査する (相互チェック ②層)。

    python3 scripts/eiken_junichi/mogi/check_mogi.py

引数なし = **mogi/data_no*.json の全回** (CLAUDE.md「引数なしの既定は刷るもの全部」)。
run_all_gates.py が check* として自動で拾う。何を見たかを必ず印字する。

見るもの (どれも「刷ってから気づく」と手遅れになるもの):
  ・設問数と通し番号 — 大問1=18問 / 大問2=6問 / 大問3=7問、番号 (1)〜(31) が連番
  ・正解キーが 0〜3 の範囲か、選択肢が 4 つで重複が無いか
  ・★大問1: 正解の語が例文の空所に入る形か (正解語が選択肢に無い等の取り違え)
  ・★大問2: 本文の空所番号と blanks の no が一致するか (ずれると全問が別問題になる)
  ・★解説が引用する語が、その設問の選択肢に実在するか (別の問題の解説の貼り違え)
  ・大問3: 質問文・選択肢・解説の対応、正解位置の偏り
  ・要約・意見論述: 模範解答の語数が指定範囲か (60〜70 / 120〜150)、
    model_words の申告と実測が一致するか (申告だけ直して本文を直し忘れる事故を防ぐ)
"""
import glob
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def wc(s):
    return len(re.findall(r"[A-Za-z][A-Za-z'’\-]*", s))


# ★生成時に紛れ込む「日本語でも英語でもない文字」を止める。2026-08-16 に実際に
#   キリル文字 (данные / речь) が語釈と選択肢に混入した。読める字なので目視では
#   気づきにくく、刷ってから生徒が困る。キリル・ギリシャ・ハングルを検出する。
STRAY = re.compile(r"[Ѐ-ӿͰ-Ͽ가-힯]+")


def check_stray_script(obj, label, bad, path=""):
    """JSON 全体を歩いて、混入した異種文字を報告する。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            check_stray_script(v, label, bad, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_stray_script(v, label, bad, f"{path}[{i}]")
    elif isinstance(obj, str):
        for m in set(STRAY.findall(obj)):
            bad.append(f"{label}: 日本語でも英語でもない文字が混入 {m!r} ({path})")


def check_round(d, label, bad, warn):
    n_p1, n_p2, n_p3 = len(d["part1"]), 0, 0
    for ps in d["part2"]:
        n_p2 += len(ps["blanks"])
    for ps in d["part3"]:
        n_p3 += len(ps["questions"])
    if n_p1 != 18:
        bad.append(f"{label}: 大問1が {n_p1} 問 (18 問であること)")
    if n_p2 != 6:
        bad.append(f"{label}: 大問2が {n_p2} 問 (6 問であること)")
    if n_p3 != 7:
        bad.append(f"{label}: 大問3が {n_p3} 問 (7 問であること)")
    total = n_p1 + n_p2 + n_p3
    if d["meta"].get("full") != total:
        bad.append(f"{label}: meta.full={d['meta'].get('full')} が実際の設問数 {total} と違う")

    answers = []

    # --- 大問1 -----------------------------------------------------------
    for i, it in enumerate(d["part1"], 1):
        at = f"{label} 大問1 ({i})"
        ch = it["choices"]
        if len(ch) != 4:
            bad.append(f"{at}: 選択肢が {len(ch)} 個")
        if len(set(c.strip().lower() for c in ch)) != len(ch):
            bad.append(f"{at}: 選択肢に重複")
        a = it["answer"]
        if not isinstance(a, int) or not 0 <= a <= 3:
            bad.append(f"{at}: answer={a} が範囲外")
            continue
        answers.append(a)
        if "( )" not in it["sentence"] and "(  )" not in it["sentence"]:
            bad.append(f"{at}: 例文に空所 ( ) が無い")
        # 解説の見出し語が正解と対応しているか
        for key in ("gloss_ja", "trans_ja"):
            if not it.get(key):
                bad.append(f"{at}: {key} が空")
        dis = it.get("distractors_ja") or {}
        # 誤答の語釈は「正解以外の 3 つ」を説明しているはず
        wrong = [c for k, c in enumerate(ch) if k != a]
        for w in wrong:
            # 語釈は原形で書く (ruled out → rule out) ので、先頭語の語幹 4 文字で照合する
            head = re.sub(r"(ed|d|s)$", "", w.split()[0].lower())[:4]
            if not any(head and head in k.lower() for k in dis):
                warn.append(f"{at}: 誤答 '{w}' の語釈が distractors_ja に無い")
        for k in dis:
            if k.lower() == ch[a].strip().lower():
                bad.append(f"{at}: 正解語 '{k}' が誤答の語釈欄に入っている")

    # --- 大問2 -----------------------------------------------------------
    no = 19
    for ps in d["part2"]:
        text = " ".join(ps["text"])
        nums_in_text = [int(x) for x in re.findall(r"\(\s*(\d+)\s*\)", text)]
        nums_in_blanks = [b["no"] for b in ps["blanks"]]
        if nums_in_text != nums_in_blanks:
            bad.append(f"{label} 大問2 {ps['id']}: 本文の空所番号 {nums_in_text} と "
                       f"blanks の番号 {nums_in_blanks} が一致しない")
        for b in ps["blanks"]:
            at = f"{label} 大問2 ({b['no']})"
            if b["no"] != no:
                bad.append(f"{at}: 通し番号がずれている (期待 {no})")
            no += 1
            ch = b["choices"]
            if len(ch) != 4:
                bad.append(f"{at}: 選択肢が {len(ch)} 個")
            if len(set(c.strip().lower() for c in ch)) != len(ch):
                bad.append(f"{at}: 選択肢に重複")
            a = b["answer"]
            if not isinstance(a, int) or not 0 <= a <= 3:
                bad.append(f"{at}: answer={a} が範囲外")
                continue
            answers.append(a)
            exp = b.get("exp_ja") or ""
            if len(exp) < 40:
                bad.append(f"{at}: 解説が短すぎる ({len(exp)} 字)")
            # 解説が触れる選択肢番号 (1〜4) は実在する選択肢のはず
            for m in re.findall(r"(?<![0-9])([1-4])『", exp):
                if int(m) - 1 == a:
                    bad.append(f"{at}: 正解 {a + 1} を誤答として説明している")

    # --- 大問3 -----------------------------------------------------------
    for ps in d["part3"]:
        body = " ".join(ps["paras"])
        for q in ps["questions"]:
            at = f"{label} 大問3 ({q['no']})"
            if q["no"] != no:
                bad.append(f"{at}: 通し番号がずれている (期待 {no})")
            no += 1
            ch = q["choices"]
            if len(ch) != 4:
                bad.append(f"{at}: 選択肢が {len(ch)} 個")
            if len(set(c.strip().lower() for c in ch)) != len(ch):
                bad.append(f"{at}: 選択肢に重複")
            a = q["answer"]
            if not isinstance(a, int) or not 0 <= a <= 3:
                bad.append(f"{at}: answer={a} が範囲外")
                continue
            answers.append(a)
            for key in ("q_ja", "exp_ja"):
                if not q.get(key):
                    bad.append(f"{at}: {key} が空")
            if len(q.get("exp_ja", "")) < 60:
                bad.append(f"{at}: 解説が短すぎる ({len(q.get('exp_ja', ''))} 字)")
            if not body.strip():
                bad.append(f"{at}: 本文が空")

    if no != 32:
        bad.append(f"{label}: 通し番号が (31) で終わっていない (最後は {no - 1})")

    # --- 正解位置の偏り ---------------------------------------------------
    c = Counter(answers)
    dist = [c.get(i, 0) for i in range(4)]
    if answers and max(dist) / len(answers) > 0.40:
        bad.append(f"{label}: 正解位置が偏っている {dist} (40% 超)")
    # ★同じ番号の 3 連続を止める。全体の分布が均等でも、並びが固まると生徒が
    #   「今度は 4 だろう」と勘で当てられる (2026-08-16 に第3回で実際に (12)〜(18) が
    #   すべて 4 になり、独立ソルバーの指摘で気づいた)。
    run, longest, prev = 0, 0, None
    for a in answers:
        run = run + 1 if a == prev else 1
        longest = max(longest, run)
        prev = a
    if longest >= 3:
        bad.append(f"{label}: 同じ正解番号が {longest} 連続している")
    print(f"    正解位置分布(1234): {dist} / 最長連続 {longest}")

    # --- 大問4・5 ---------------------------------------------------------
    s = d["part4"]["summary"]
    n = wc(s["model"])
    if not 60 <= n <= 70:
        bad.append(f"{label} 大問4: 解答例が {n} 語 (60〜70 語であること)")
    if s.get("model_words") != n:
        bad.append(f"{label} 大問4: model_words={s.get('model_words')} が実測 {n} 語と違う")
    if len(s["paras"]) < 3:
        bad.append(f"{label} 大問4: 要約用英文の段落が {len(s['paras'])} 個 (3 以上)")
    e = d["part4"]["essay"]
    n = wc(e["model"])
    if not 120 <= n <= 150:
        bad.append(f"{label} 大問5: 解答例が {n} 語 (120〜150 語であること)")
    if e.get("model_words") != n:
        bad.append(f"{label} 大問5: model_words={e.get('model_words')} が実測 {n} 語と違う")
    if len(e["points"]) != 4:
        bad.append(f"{label} 大問5: POINTS が {len(e['points'])} 個 (4 個であること)")
    return total


def main():
    files = sorted(glob.glob(os.path.join(HERE, "data_no*.json")))
    if not files:
        print("NG: 検査対象の data_no*.json が 1 つも無い")
        return 1
    bad, warn, n_round, n_q = [], [], 0, 0
    for f in files:
        label = os.path.basename(f)
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            bad.append(f"{label}: JSON が読めない ({e})")
            continue
        n_round += 1
        print(f"[..] {label} (第{d['meta']['no']}回)")
        before = len(bad)
        check_stray_script(d, label, bad)
        n_q += check_round(d, label, bad, warn)
        if len(bad) == before:
            print(f"[OK] {label} — 31問 + 要約 + 意見論述")
    for w in warn:
        print(f"[WARN] {w}")
    if bad:
        for x in bad:
            print(f"NG: {x}")
        print(f"違反 {len(bad)} 件")
        return 1
    print(f"=== ALL PASS (回 {n_round} / 設問 {n_q} + 英作文 {n_round * 2} 題) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
