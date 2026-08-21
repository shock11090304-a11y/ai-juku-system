#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatGPT などに書かせた**データ**から神テストの冊子を作る。

    python3 scripts/book_exam/materials/build_from_spec.py 〈spec.json〉
    python3 scripts/book_exam/materials/build_from_spec.py 〈spec.yaml〉 --out 〈置き場〉

指示文 (ChatGPT に渡すプロンプト) は
    python3 scripts/book_exam/make_llm_prompt.py math
で作る。正典から生成しているので、規則が変わればプロンプトも変わる。

■ ★ 設計 — LLM には**コードを書かせない**
    LLM に build_*.py (Python) を書かせると、実行するまで何が起きるか分からず、
    構文エラーも混ざる。ここでは **JSON / YAML のデータだけ**を受け取り、
    ・知らないキーがあれば落とす (でっち上げの項目をそのまま通さない)
    ・_book_build.verify() の全項目を通す
    ・数学は `check` の式を sympy で**独立に計算**して正解と突き合わせる
    という順で、通ったものだけを冊子にする。**LLM の出力を信用しない**のが要点。

■ ★ 落ちたときは「貼り戻し文」を出す
    違反の一覧を、そのまま ChatGPT に貼って直させられる形で印字する。
    直った JSON をもう一度食わせれば済む。

■ 使い方の流れ
    1. make_llm_prompt.py で指示文を作り、ChatGPT に渡す
    2. 返ってきた JSON を spec.json として保存
    3. このスクリプトに食わせる → 通れば 〈stem〉.json と 〈stem〉_問題.pdf ができる
    4. 中身を**人が全問読む** (正解の一意性は機械に見えない)
    5. git add → commit → push → import_books.py で取り込む
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _book_build as B  # noqa: E402

BOOK_KEYS = {"stem", "title", "subject", "subject_name", "level",
             "time_limit_min", "intro"}
BOOK_REQUIRED = {"stem", "title", "subject", "subject_name", "level",
                 "time_limit_min"}
PASSAGE_KEYS = {"title", "html", "source", "break_before", "page"}
QUESTION_KEYS = {"number", "page", "points", "unit_tag", "stem", "choices",
                 "choices_plain", "answer", "accepted", "figure",
                 "figure_ticks", "check", "explanation"}
QUESTION_REQUIRED = {"number", "points", "unit_tag", "stem", "answer",
                     "explanation"}

# `check` に書いてよい文字。式以外のものを持ち込ませない。
CHECK_OK = re.compile(r"^[0-9A-Za-z_+\-*/(),.\s^=<>\[\]]+$")
# 使ってよい名前 (sympy のごく一部)。ここに無い名前は parse で落ちる。
import sympy as _sp                                        # noqa: E402
CHECK_NAMES = {
    "x": _sp.Symbol("x"), "y": _sp.Symbol("y"), "a": _sp.Symbol("a"),
    "b": _sp.Symbol("b"), "c": _sp.Symbol("c"), "k": _sp.Symbol("k"),
    "n": _sp.Symbol("n"), "t": _sp.Symbol("t"),
    "minimum": _sp.minimum, "maximum": _sp.maximum, "solve": _sp.solve,
    "diff": _sp.diff, "expand": _sp.expand, "factor": _sp.factor,
    "simplify": _sp.simplify, "sqrt": _sp.sqrt, "Rational": _sp.Rational,
    "discriminant": _sp.discriminant, "Abs": _sp.Abs, "pi": _sp.pi,
}
# ★ 名前空間はここで閉じる。sympy の全名前を開けない (組み込みも渡さない)。
#   数値リテラルの変換に要る Integer / Float / Symbol / Rational だけ足す。
CHECK_GLOBALS = {"__builtins__": {}, "Integer": _sp.Integer,
                 "Float": _sp.Float, "Symbol": _sp.Symbol,
                 "Rational": _sp.Rational}


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # ★ ChatGPT は JSON をコードブロックで返すことがある。剥がしてから読む。
    text = re.sub(r"^\s*```[a-zA-Z]*\s*|\s*```\s*$", "", text.strip())
    if path.lower().endswith((".yaml", ".yml")):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def check_keys(obj, allowed, required, where, errs):
    if not isinstance(obj, dict):
        errs.append(f"{where}: 辞書ではありません")
        return
    for k in sorted(set(obj) - allowed):
        errs.append(f"{where}: 知らない項目「{k}」があります "
                    f"(使えるのは {sorted(allowed)})")
    for k in sorted(required - set(obj)):
        errs.append(f"{where}: 「{k}」がありません")


def to_meta(spec, errs):
    book = spec.get("book")
    check_keys(book, BOOK_KEYS, BOOK_REQUIRED, "book", errs)
    if not isinstance(book, dict):
        return None
    meta = {k: book.get(k) for k in BOOK_KEYS if k in book}
    passages = spec.get("passages") or []
    if not isinstance(passages, list):
        errs.append("passages: 並びではありません")
        passages = []
    for i, p in enumerate(passages):
        check_keys(p, PASSAGE_KEYS, {"title", "html"}, f"passages[{i}]", errs)
    if passages:
        meta["passages"] = passages
    return meta


def to_questions(spec, errs):
    rows = spec.get("questions")
    if not isinstance(rows, list) or not rows:
        errs.append("questions: 1 問もありません")
        return []
    out = []
    for i, r in enumerate(rows):
        where = f"questions[{i}] (第{r.get('number') if isinstance(r, dict) else '?'}問)"
        check_keys(r, QUESTION_KEYS, QUESTION_REQUIRED, where, errs)
        if not isinstance(r, dict):
            continue
        q = {k: r[k] for k in QUESTION_KEYS if k in r and k != "check"}
        q.setdefault("page", None)
        out.append(q)
    return out


def parse_math(text, where, errs):
    """`check` の式を sympy で読む。読めなければ None。"""
    s = str(text).strip()
    if not CHECK_OK.fullmatch(s):
        errs.append(f"{where}: check に式以外の文字が入っています ({s[:40]!r})")
        return None
    try:
        from sympy.parsing.sympy_parser import parse_expr
        return parse_expr(s, local_dict=CHECK_NAMES,
                          global_dict=CHECK_GLOBALS, evaluate=True)
    except Exception as e:                                   # noqa: BLE001
        errs.append(f"{where}: check の式を読めません ({e})")
        return None


def verify_checks(spec, questions):
    """★ 数学の正解を手入力で信じない。check の式を独立に計算して照合する。"""
    errs = []
    rows = spec.get("questions") or []
    for r, q in zip(rows, questions):
        if not isinstance(r, dict) or "check" not in r:
            continue
        no = q.get("number")
        where = f"第{no}問"
        got = parse_math(r["check"], where, errs)
        if got is None:
            continue
        choices = q.get("choices")
        ans = q.get("answer")
        if not isinstance(choices, list):
            errs.append(f"{where}: check は選択式の設問にだけ書けます")
            continue
        if not (isinstance(ans, int) and 1 <= ans <= len(choices)):
            continue        # 正解番号の異常は verify() が言うので二重に言わない
        plain = q.get("choices_plain") or [B.strip_math(str(c)) for c in choices]
        vals, unread = [], []
        for j, p in enumerate(plain):
            v = None
            if CHECK_OK.fullmatch(str(p).strip()):
                try:
                    from sympy.parsing.sympy_parser import parse_expr
                    v = parse_expr(str(p).strip(),
                                   local_dict=CHECK_NAMES,
                                   global_dict=CHECK_GLOBALS, evaluate=True)
                except Exception:                            # noqa: BLE001
                    v = None
            if v is None:
                unread.append(j + 1)
            vals.append(v)
        want = vals[ans - 1]
        if want is None:
            errs.append(f"{where}: 正解の選択肢を式として読めません "
                        f"({plain[ans - 1]!r})。choices_plain に "
                        f"「-2*x**2 + 40*x」のような形で書いてください")
            continue
        if _sp.simplify(want - got) != 0:
            errs.append(f"{where}: check の計算 ({got}) と正解の選択肢 "
                        f"({want}) が合いません")
        for j in range(len(vals)):
            for k in range(j + 1, len(vals)):
                if vals[j] is not None and vals[k] is not None \
                        and _sp.simplify(vals[j] - vals[k]) == 0:
                    errs.append(f"{where}: 選択肢 {j + 1} と {k + 1} が同値です "
                                f"({vals[j]})。正解が 2 つになります")
        if unread:
            print(f"!    {where}: 選択肢 {unread} は式として読めないので"
                  f"同値かどうかを確かめていません")
    return errs


def paste_back(errs, path):
    print()
    print("=" * 66)
    print("--- ここから下をそのまま ChatGPT に貼って直させてください ---")
    print()
    print("さきほどの JSON に次の問題があります。**同じ JSON 形式のまま**"
          "直して、コードブロックで全文を出し直してください。")
    print()
    for e in errs:
        print(f"- {e}")
    print()
    print("=" * 66)
    print(f"(直した JSON を {os.path.basename(path)} に上書きして、"
          f"同じコマンドをもう一度回してください)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", help="ChatGPT が書いた JSON / YAML")
    ap.add_argument("--out", help="冊子の置き場 (既定 materials/〈stem〉/)")
    a = ap.parse_args()

    try:
        spec = load_spec(a.spec)
    except Exception as e:                                   # noqa: BLE001
        print(f"✗ {a.spec} を読めません ({e})")
        print("  ChatGPT の返答から JSON のコードブロックだけを"
              "保存し直してください")
        return 1
    if not isinstance(spec, dict):
        print("✗ いちばん外側が辞書ではありません "
              "({\"book\": …, \"questions\": […]} の形にしてください)")
        return 1

    errs = []
    for k in sorted(set(spec) - {"book", "passages", "questions"}):
        errs.append(f"いちばん外側に知らない項目「{k}」があります "
                    f"(使えるのは book / passages / questions)")
    meta = to_meta(spec, errs)
    questions = to_questions(spec, errs)
    if errs:
        for e in errs:
            print(f"✗ {e}")
        paste_back(errs, a.spec)
        return 1

    errs = B.verify(meta, questions) + verify_checks(spec, questions)
    if errs:
        for e in errs:
            print(f"✗ {e}")
        paste_back(errs, a.spec)
        return 1
    print(f"[ok] 形と中身の検査を通りました ({len(questions)} 問)")

    out = a.out or os.path.join(HERE, meta["stem"])
    os.makedirs(out, exist_ok=True)
    rc = B.run(out, meta, questions)
    if rc:
        return rc
    print()
    print("=== 次にやること ===")
    print("  1. 刷り上がりの PDF を**自分の目で読む**")
    print("  2. 全問を敵対的に読み直す (正解の一意性は機械に見えない)")
    print(f"  3. git add {os.path.relpath(out)} && git commit && git push")
    print(f"  4. python3 scripts/book_exam/import_books.py {os.path.relpath(out)} \\")
    print(f"       --pdf-dir {os.path.relpath(out)} --dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
