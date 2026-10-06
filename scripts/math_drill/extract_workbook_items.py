#!/usr/bin/env python3
"""📐 高校数学ドリル 第2弾の素材を取り出す: scripts/math_workbook の問題集 8 冊 (基礎徹底 数I・数II・数A・数III系 / 問題演習テキスト IA・IIB・IA第2集・IIB第2集)
の全問を 1 つの JSON にそろえる (誤答づくりと盲検の入力・build_math_workbook_seed.py の土台)。

入れないもの (2026-10-06 調査):
  - 基礎徹底「数列・確率・ベクトル」と 数学IA 弱点発見トレーニング … 自己採点シート＋診断キー (部外秘) と組で弱点診断に使う冊子。
    同じ問題をドリルで先に見せると診断が効かなくなる。
  - 証明問題 (proof フラグ・「証明せよ」「示せ」) … 4 択にならない。
  - 図が無いと解けない問題 … FIGURE_DROP に列挙 (箱ひげ図の読み取り・碁盤目の道)。図を指す言い回しだけのものは FIGURE_REWRITE で文を直す。

出力 (1 問 1 行): id (冊子:単元番号:問番号)・book・src_unit・unit (入試道場の topic)・level・stem・answer・explanation・av (sympy の答えの値の repr)・
  mc_choices / mc_answer (元から選択式のもの)・figure_attached (第2集で図が付いていたもの。図は出さない)。数式は $…$ → \\( \\) に直す。
使い方: python3 scripts/math_drill/extract_workbook_items.py --out PATH
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WB = os.path.join(REPO, "scripts", "math_workbook")

BOOKS = [  # (モジュール, 冊子の短い名前, source の接頭辞)
    ("content_kisoI", "基礎徹底 数I", "kI"), ("content_kisoII", "基礎徹底 数II", "kII"),
    ("content_kisoA", "基礎徹底 数A", "kA"), ("content_kisoIII", "基礎徹底 数III系", "kIII"),
    ("content_ia", "問題演習 IA", "ia"), ("content_iib", "問題演習 IIB", "iib"),
    ("content_ia_v2", "問題演習 IA 第2集", "ia2"), ("content_iib_v2", "問題演習 IIB 第2集", "iib2"),
]
UNIT_MAP = {
    # 基礎徹底
    "式の展開と因数分解": "数学I 数と式", "実数・絶対値・1次不等式": "数学I 数と式", "集合と命題": "数学I 集合と命題",
    "二次関数のグラフ": "基礎数学 二次関数", "二次方程式と二次不等式": "基礎数学 二次関数",
    "三角比の基本": "基礎数学 図形と計量", "正弦定理・余弦定理と面積": "基礎数学 図形と計量", "データの分析": "基礎数学 データ",
    "弧度法と三角関数の値": "基礎数学 三角関数", "加法定理・2倍角・三角関数の合成": "基礎数学 三角関数",
    "指数の拡張と指数関数": "基礎数学 指数対数", "対数とその性質": "基礎数学 指数対数",
    "微分係数と導関数": "基礎数学 微積", "不定積分・定積分と面積": "基礎数学 微積",
    "三角形と線分の比": "数学A 図形の性質", "三角形の五心とチェバ・メネラウス": "数学A 図形の性質",
    "円の性質（円周角・内接四角形）": "数学A 図形の性質", "方べきの定理と2つの円": "数学A 図形の性質", "作図と空間図形": "数学A 図形の性質",
    "約数と倍数": "基礎数学 整数", "ユークリッドの互除法と不定方程式": "基礎数学 整数", "整数の割り算と余り": "基礎数学 整数", "n進法": "基礎数学 整数",
    "複素数平面の基本": "数学C 複素数平面", "複素数平面と図形": "数学C 複素数平面",
    "確率変数と確率分布": "数学B 統計的な推測", "統計的な推測": "数学B 統計的な推測",
    "数列の極限": "数学III 極限", "関数の極限と連続性": "数学III 極限",
    "微分の計算（数III）": "数学III 微分法", "微分の応用（数III）": "数学III 微分法",
    "積分の計算（数III）": "数学III 積分法", "定積分の応用（数III）": "数学III 積分法",
    # 問題演習テキスト (IA・IIB・第2集とも同じ単元名)
    "数と式": "数学I 数と式", "二次関数": "基礎数学 二次関数", "図形と計量": "基礎数学 図形と計量",
    "場合の数": "基礎数学 確率", "確率": "基礎数学 確率", "図形の性質": "数学A 図形の性質", "整数の性質": "基礎数学 整数",
    "式と証明": "数学II 式と証明", "複素数と方程式": "数学II 複素数と方程式", "図形と方程式": "数学II 図形と方程式",
    "三角関数": "基礎数学 三角関数", "指数関数・対数関数": "基礎数学 指数対数", "微分法": "基礎数学 微積", "積分法": "基礎数学 微積",
    "数列": "基礎数学 数列", "ベクトル": "基礎数学 ベクトル",
}
PROOF = re.compile(r"証明せよ|示せ|証明しなさい")
FIGURE_REF = re.compile(r"図(?:のように|は|に示|の(?:よう|ような|中|三角形|点))|下の図|右の図|左の図|次の箱ひげ図|図のような")
# 図が無いと条件が足りない → 入れない
FIGURE_DROP_PATTERNS = [r"次の箱ひげ図は", r"図のような碁盤目状の道"]   # 「右に3区画、上に2区画進む碁盤目状の道」は文で条件がそろうので入れる
# 図を指す言い回しだけ → 文を直す (条件は本文にそろっている)
FIGURE_REWRITE = [
    (r"^右の図の直角三角形 ABC", "直角三角形 ABC"),
    (r"^図は指数関数 (\$y=a\^\{x\}\$)\((\$a>0,\\ a \\neq 1\$)\)のグラフで、点 (\$\(2,\\ 9\)\$) を通っている。", r"指数関数 \1(\2)のグラフが点 \3 を通っている。"),
    (r"^図のように、", ""),
    (r"^下の図で、", ""),
]


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(WB, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    cwd = os.getcwd()
    try:
        os.chdir(WB)
        sys.path.insert(0, WB)
        spec.loader.exec_module(m)
    finally:
        os.chdir(cwd)
        sys.path.remove(WB)
    return m


def dollars_to_paren(s):
    """$…$ を \\( … \\) に。$ の数が奇数なら落とす (変換できない = 呼び出し側で problems に積む)。"""
    s = str(s or "")
    if s.count("$") % 2:
        return None
    out, inside = [], False
    for part in re.split(r"(\$)", s):
        if part == "$":
            out.append(r"\)" if inside else r"\(")
            inside = not inside
        else:
            out.append(part)
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    items, dropped, problems = [], [], []
    seen_stem = {}
    for mod, book, pre in BOOKS:
        m = load(mod)
        units = [u for p in m.PARTS for u in p["units"]] if hasattr(m, "PARTS") else m.UNITS
        for ui, u in enumerate(units, 1):
            unit = UNIT_MAP.get(u["name"])
            if not unit:
                problems.append(f"{book} {u['name']}: 単元の対応が無い")
                continue
            for pi, q in enumerate(u["problems"], 1):
                pid = f"{pre}:{ui}:{pi}"
                stem_raw = q["stem"]
                if q.get("proof") or PROOF.search(stem_raw):
                    dropped.append({"id": pid, "why": "証明問題", "stem": stem_raw[:60]}); continue
                if any(re.search(p, stem_raw) for p in FIGURE_DROP_PATTERNS):
                    dropped.append({"id": pid, "why": "図が無いと解けない", "stem": stem_raw[:60]}); continue
                for pat, rep in FIGURE_REWRITE:
                    stem_raw = re.sub(pat, rep, stem_raw)
                if FIGURE_REF.search(stem_raw):
                    problems.append(f"{pid}: 図への言及が残る: {stem_raw[:80]}")
                stem, ans, expl = dollars_to_paren(stem_raw), dollars_to_paren(q["answer"]), dollars_to_paren(q.get("explanation", ""))
                if None in (stem, ans, expl):
                    problems.append(f"{pid}: $ の数が奇数"); continue
                key = re.sub(r"\s+", "", stem)
                if key in seen_stem:
                    dropped.append({"id": pid, "why": f"{seen_stem[key]} と同じ問題文", "stem": stem_raw[:60]}); continue
                seen_stem[key] = pid
                it = {"id": pid, "book": book, "src_unit": u["name"], "unit": unit, "level": q.get("level", "standard"),
                      "stem": stem, "answer": ans, "explanation": expl,
                      "av": repr(q["av"]) if "av" in q else None,
                      "figure_attached": bool(q.get("figure")),
                      "stem_hash": hashlib.sha1(q["stem"].encode()).hexdigest()[:10]}
                if q.get("choices"):
                    it["mc_choices"] = [dollars_to_paren(c) for c in q["choices"]]
                    it["mc_answer"] = int(q["answer_index"])
                items.append(it)
    if problems:
        print("❌", len(problems)); [print(" -", p) for p in problems[:40]]; sys.exit(1)
    json.dump({"items": items, "dropped": dropped}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by = {}
    for it in items:
        by[it["unit"]] = by.get(it["unit"], 0) + 1
    print(f"items {len(items)} / dropped {len(dropped)}")
    for u, n in sorted(by.items()):
        print(f"  {u}: {n}")
    for d in dropped:
        print("  drop", d["id"], d["why"], d["stem"])


if __name__ == "__main__":
    main()
