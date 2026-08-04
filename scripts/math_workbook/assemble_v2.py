#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_v2_workflow の出力(v2_out.json)から content_ia_v2.py / content_iib_v2.py を生成する。
全問が新規なので AST 温存は不要。JSON→Python ソースを直接組む(chk は生コード、他は json.dumps)。"""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))

HEADER = '''# -*- coding: utf-8 -*-
"""%s 問題演習テキスト 第2集(図形強化) の内容(単一ソース)。
数式は $...$ の LaTeX、図は figure に SVG。各問の chk を verify.py が実行して答えを独立再計算する。
自動生成: assemble_v2.py が v2_out.json から生成。"""
import sympy as sp
from sympy import (symbols, expand, factor, simplify, sqrt, Rational as R, apart,
    solveset, solve, S, Interval, FiniteSet, Union, Abs, Eq, oo, pi, I,
    sin, cos, tan, atan, acos, asin, log, diff, integrate, binomial, factorial,
    gcd, divisors, Matrix, N, And, Or, Not, nsimplify)
x, y, z, a, b, c, d, m, n, k, t, r, s, theta, alpha, beta = symbols(
    'x y z a b c d m n k t r s theta alpha beta', real=True)
def EQ(u, v): return simplify(sp.expand(u) - sp.expand(v)) == 0
def NUM(u, v, tol=1e-9): return abs(complex(N(u) - N(v))) < tol
def SOLR(expr, var=x): return solveset(expr, var, domain=S.Reals)
SOL = SOLR
def SOLC(expr, var=x): return solveset(expr, var, domain=S.Complexes)
def P(nn, rr): return factorial(nn) // factorial(nn - rr)
def C(nn, rr): return int(binomial(nn, rr))

'''

TAGS = {
    "数と式": "式変形・根号・不等式", "集合と命題": "ベン図・必要十分・対偶",
    "二次関数": "グラフ・最大最小・解の配置", "図形と計量": "三角比・正弦余弦・面積(図)",
    "データの分析": "代表値・箱ひげ図・相関", "場合の数": "順列組合せ・経路(図)",
    "確率": "余事象・反復・条件付き", "図形の性質": "五心・円・方べき(図)",
    "整数の性質": "約数・互除法・不定方程式",
    "式と証明": "二項定理・除法・不等式", "複素数と方程式": "複素数・解と係数・高次",
    "図形と方程式": "直線・円・軌跡・領域(図)", "三角関数": "加法定理・合成・グラフ(図)",
    "指数関数・対数関数": "計算・方程式・桁数", "微分法": "接線・極値・実数解(図)",
    "積分法": "定積分・面積(図)", "数列": "等差等比・Σ・漸化式",
    "ベクトル": "内積・分点・空間(図)", "統計的な推測": "二項/正規分布・推定・検定",
}

def unesc(o):
    if isinstance(o, str): return html.unescape(o)
    if isinstance(o, list): return [unesc(v) for v in o]
    if isinstance(o, dict): return {k: unesc(v) for k, v in o.items()}
    return o

def J(v): return json.dumps(v, ensure_ascii=False)

def emit_problem(p):
    parts = []
    for key in ["group", "level", "type", "stem", "answer", "explanation"]:
        parts.append(f'{J(key)}: {J(p.get(key, ""))}')
    if p.get("type") == "mc":
        parts.append(f'"choices": {J(p.get("choices") or [])}')
        parts.append(f'"answer_index": {int(p.get("answer_index") or 0)}')
    if p.get("figure"):
        parts.append(f'"figure": {J(p["figure"])}')
    parts.append(f'"chk": {p["chk"].strip()}')
    return "{" + ", ".join(parts) + "}"

def main():
    data = unesc(json.load(open(os.path.join(HERE, "v2_out.json"), encoding="utf-8")))
    for book, title in [("ia", "数学I・A"), ("iib", "数学II・B")]:
        units = sorted([u for u in data if u["book"] == book], key=lambda u: u["unitIndex"])
        lines = ["UNITS = ["]
        nfig = ntot = 0
        for u in units:
            probs = u.get("problems", [])
            ntot += len(probs)
            nfig += sum(1 for p in probs if p.get("figure"))
            tag = TAGS.get(u["unitName"], u.get("tag", ""))
            lines.append(f'  {{"name": {J(u["unitName"])}, "tag": {J(tag)}, "problems": [')
            for p in probs:
                lines.append("    " + emit_problem(p) + ",")
            lines.append("  ]},")
        lines.append("]")
        src = HEADER % title + "\n".join(lines) + "\n"
        out = os.path.join(HERE, f"content_{book}_v2.py")
        open(out, "w", encoding="utf-8").write(src)
        print(f"WROTE {out} | units={len(units)} problems={ntot} figures={nfig}")

if __name__ == "__main__":
    main()
