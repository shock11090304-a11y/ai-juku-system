#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatGPT に書かせた JSON から冊子を作る経路の検査。

    python3 scripts/book_exam/check_llm_pipeline.py

引数なしで全シナリオを回す。run_all_gates.py が check* として自動で拾う。
Chrome も PDF ライブラリも要らない (純関数だけを叩く) ので CI でも同じものが走る。

■ 何を守るのか
  ・**LLM の出力を信用しない**。形が違う・でっち上げの項目・正解の取り違えを、
    冊子になる前に落とす
  ・指示文 (make_llm_prompt.py) が**正典とずれない**。解説の見出しや subject の
    集合が変わったのに指示文が古いままだと、LLM は落ちる JSON を作り続ける

■ 見るもの
  ・見本の spec (fixtures_llm/sample_math.json) が最後まで通ること
  ・壊した spec が**その理由で**落ちること (知らない項目 / 0 起算 / 見出しの欠け /
    解説の LaTeX / 正解の取り違え / 選択肢の同値 / check の細工)
  ・指示文に、実物の見出し・subject・規則が入っていること
"""
import copy
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "materials"))
import _book_build as B  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures_llm", "sample_math.json")

problems = []
N_CASE = 0


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BFS = _load("bfs", os.path.join(HERE, "materials", "build_from_spec.py"))
PROMPT = _load("mlp", os.path.join(HERE, "make_llm_prompt.py"))


def run_spec(spec):
    """spec を最後まで (PDF を作る手前まで) 通す。@returns エラー文の一覧。"""
    errs = []
    for k in sorted(set(spec) - {"book", "passages", "questions"}):
        errs.append(f"いちばん外側に知らない項目「{k}」があります")
    meta = BFS.to_meta(spec, errs)
    questions = BFS.to_questions(spec, errs)
    if errs:
        return errs
    return B.verify(meta, questions) + BFS.verify_checks(spec, questions)


def case(label, got, want):
    global N_CASE
    N_CASE += 1
    got = list(got)
    missing = [w for w in want if not any(w in g for g in got)]
    extra = [g for g in got if not any(w in g for w in want)]
    if missing or extra:
        problems.append(f"{label}\n      期待: {want}\n      実際: {got}")
        print(f"  [NG] {label}")
    else:
        print(f"  [ok] {label}")


def main():
    print("=== ChatGPT → 冊子 の経路の検査 ===")
    with open(FIXTURE, encoding="utf-8") as f:
        base = json.load(f)

    def broken(fn):
        s = copy.deepcopy(base)
        fn(s)
        return run_spec(s)

    # --- 見本はそのまま通る -------------------------------------------------
    case("見本の spec は最後まで通る", run_spec(copy.deepcopy(base)), [])

    # --- 形の検査 -----------------------------------------------------------
    case("知らない項目があれば落とす",
         broken(lambda s: s["questions"][0].update(difficulty="hard")),
         ["知らない項目「difficulty」"])
    case("いちばん外側の知らない項目も落とす",
         broken(lambda s: s.update(notes="よろしく")),
         ["いちばん外側に知らない項目「notes」"])
    case("必須の項目が無ければ落とす",
         broken(lambda s: s["questions"][0].pop("unit_tag")),
         ["「unit_tag」がありません"])
    case("book の必須が無ければ落とす",
         broken(lambda s: s["book"].pop("time_limit_min")),
         ["「time_limit_min」がありません"])

    # --- 中身の検査 ---------------------------------------------------------
    case("正解を 0 起算で書いたら落とす",
         broken(lambda s: s["questions"][0].update(answer=0)),
         ["正解番号が 1〜4 でない"])
    case("解説の見出しが欠けたら落とす",
         broken(lambda s: s["questions"][0].update(
             explanation=s["questions"][0]["explanation"].replace("【立式】", ""))),
         ["解説に「【立式】」が無い"])
    case("解説に LaTeX が混ざったら落とす",
         broken(lambda s: s["questions"][0].update(
             explanation=s["questions"][0]["explanation"]
             .replace("最小値 -4", "最小値 $-4$"))),
         ["解説に生の LaTeX がある"])
    case("誤答の説明が欠けたら落とす",
         broken(lambda s: s["questions"][0].update(
             explanation=s["questions"][0]["explanation"]
             .replace("3. 3 — 頂点の x 座標。聞かれているのは y の最小値。\n", ""))),
         ["誤答 3 の説明が無い"])
    case("正解を誤答の節に載せたら落とす",
         broken(lambda s: s["questions"][0].update(
             explanation=s["questions"][0]["explanation"]
             + "\n2. -4 — これも誤り。")),
         ["正解 2 が誤答の節に載っている"])
    case("unit_tag の形が崩れたら落とす",
         broken(lambda s: s["questions"][0].update(unit_tag="へいほう")),
         ["unit_tag の形が崩れている"])

    # --- ★ 正解を信用しない -------------------------------------------------
    case("正解の番号を取り違えたら sympy が落とす",
         broken(lambda s: s["questions"][0].update(answer=1)),
         ["check の計算", "正解 1 が誤答の節に載っている", "誤答 2 の説明が無い"])
    case("選択肢の値を書き換えたら sympy が落とす",
         broken(lambda s: s["questions"][0].update(
             choices_plain=["5", "-9", "3", "-3"])),
         ["check の計算"])
    case("選択肢に同値が混ざったら落とす",
         broken(lambda s: s["questions"][0].update(
             choices=["$5$", "$-4$", "$3$", "$-4$"],
             choices_plain=["5", "-4", "3", "-4"])),
         ["選択肢に同じものが混ざっている", "が同値です",
          "誤答 4 の説明が選択肢と合っていない"])
    case("check に式でないものを書いたら落とす",
         broken(lambda s: s["questions"][0].update(check="__import__('os')")),
         ["check に式以外の文字が入っています"])
    case("check に使えない名前を書いたら落とす",
         broken(lambda s: s["questions"][0].update(check="open(1)")),
         ["check の式を読めません"])
    case("記述に check を付けたら落とす",
         broken(lambda s: s["questions"][0].update(
             check="minimum(x**2 - 6*x + 5, x)", choices=None,
             answer="最小値は -4")),
         ["check は選択式の設問にだけ書けます",
          "choices_plain は選択式のときだけ使える"])

    # --- ★ 指示文が正典とずれていないか ------------------------------------
    print("--- 指示文 (make_llm_prompt.py) と正典の突き合わせ ---")
    for subject, heads in sorted(B.SUBJECT_HEADINGS.items()):
        text = PROMPT.build(subject, 10, False, "検査")
        miss = [h for h in heads if h not in text]
        case(f"指示文に {subject} の見出しが全部入っている",
             [f"入っていない: {miss}"] if miss else [], [])
    text = PROMPT.build("math", 10, False, "検査")
    for must, label in (
            ("1 から始まる番号", "1 起算の注意"),
            ("マーク欄", "マーク欄が作れないこと"),
            ("数字だけの答えは弾かれます", "記述の数字だけ禁止"),
            ("LaTeX を書かないでください", "解説の LaTeX 禁止"),
            ("page", "ページを書かないこと"),
            ("check", "sympy の再計算")):
        case(f"指示文に「{label}」が入っている",
             [] if must in text else [f"「{must}」が指示文に無い"], [])
    subs = {v for v, _ in PROMPT.subjects()}
    case("指示文の subject 一覧が実物と同じ",
         [] if subs and subs >= set(B.SUBJECT_HEADINGS) else
         [f"指示文の subject {sorted(subs)} が実物を含んでいない"], [])
    hon = PROMPT.build("math", 10, True, "検査")
    for must in ("誘導連鎖", "判断・考察", "転用", "単独でも解ける"):
        case(f"本番相当の指示文に「{must}」が入っている",
             [] if must in hon else [f"「{must}」が無い"], [])

    print(f"--- 見たもの: fixtures_llm/sample_math.json / build_from_spec の"
          f"形と中身の検査 / make_llm_prompt の全教科 — シナリオ {N_CASE} 件 ---")
    if problems:
        for p in problems:
            print(f"NG: {p}")
        print(f"違反 {len(problems)} 件")
        return 1
    print(f"=== ALL PASS (シナリオ {N_CASE}) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
