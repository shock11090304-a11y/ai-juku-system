#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rewrite_workflow の出力(rewrite_out.json)を、検証済みの plain バックアップに適用して
教科書LaTeX版の content_ia.py / content_iib.py を再生成する。

方針:
- 既存問題は chk(sympy検算)を AST で byte-faithful に温存し、表示4フィールドのみ LaTeX に差し替える。
- 新規問題は dict ノードを組み立てて追加(chk は文字列を式ノードにパース)。
- 共通ヘッダを差し替え、旧新どちらの chk も解決できる記号/ヘルパを供給。
- 忠実性レポート(既存 answer の LaTeX を素に戻して元と比較)を出力。
"""
import ast, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

HEADER = '''# -*- coding: utf-8 -*-
"""%s 問題演習テキストの内容(単一ソース・教科書LaTeX組版用)。
数式は $...$ の LaTeX。各問の chk は sympy で答えを独立再計算して True を返す(verify.py が実行)。
自動生成: apply_rewrite.py が plain 版 + rewrite_out.json から生成。
"""
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

def const(v):
    if isinstance(v, list):
        return ast.List([const(x) for x in v], ast.Load())
    return ast.Constant(v)

def get_units_node(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "UNITS":
                    return node.value
    raise RuntimeError("UNITS not found")

def dict_get(dnode, key):
    for kk, vv in zip(dnode.keys, dnode.values):
        if isinstance(kk, ast.Constant) and kk.value == key:
            return vv
    return None

def dict_set(dnode, key, valuenode):
    for i, kk in enumerate(dnode.keys):
        if isinstance(kk, ast.Constant) and kk.value == key:
            dnode.values[i] = valuenode
            return
    dnode.keys.append(ast.Constant(key))
    dnode.values.append(valuenode)

def build_new_problem(p):
    keys, vals = [], []
    def add(k, v):
        keys.append(ast.Constant(k)); vals.append(v)
    add("group", const(p["group"]))
    add("level", const(p["level"]))
    if p.get("type", "short") != "short":
        add("type", const(p["type"]))
    add("stem", const(p["stem"]))
    if p.get("type") == "mc":
        add("choices", const(p.get("choices") or []))
        add("answer_index", const(p.get("answer_index") or 0))
    add("answer", const(p["answer"]))
    add("explanation", const(p["explanation"]))
    chk_expr = ast.parse(p["chk"].strip(), mode="eval").body
    add("chk", chk_expr)
    return ast.Dict(keys, vals)

# --- 忠実性チェック: LaTeX を素の記法に戻して比較 ---
def delatex(s):
    s = s or ""
    s = re.sub(r"\\dfrac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√\1", s)
    s = re.sub(r"\\sqrt(\w)", r"√\1", s)
    s = re.sub(r"\\overrightarrow\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\vec\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\overline\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\{\}_\{?(\w+)\}?\\mathrm\{([PC])\}_\{?(\w+)\}?", r"\1\2\3", s)
    for a_, b_ in [("\\displaystyle",""),("\\left",""),("\\right",""),("\\dfrac","/"),
                   ("\\cdot","·"),("\\times","×"),("\\pm","±"),("\\leqq","≦"),("\\geqq","≧"),
                   ("\\theta","θ"),("\\pi","π"),("\\alpha","α"),("\\beta","β"),
                   ("\\circ","°"),("\\,",""),("\\ ",""),("\\Big",""),("$",""),
                   ("\\int","∫"),("\\sum","Σ"),("\\cup","∪"),("\\cap","∩"),
                   ("\\subset","⊂"),("\\in","∈"),("\\Rightarrow","⇒"),("\\iff","⇔"),
                   ("{","("),("}",")"),(" ",""),("^","^"),("_","_")]:
        s = s.replace(a_, b_)
    return s

def norm(s):
    return re.sub(r"[\s()（）]", "", delatex(s))

def main():
    data = json.load(open(os.path.join(HERE, "rewrite_out.json"), encoding="utf-8"))
    by_book = {"ia": {}, "iib": {}}
    for u in data:
        by_book[u["book"]][u["unitIndex"]] = u

    faithfulness = []
    for book, title in [("ia", "数学I・A"), ("iib", "数学II・B")]:
        src = open(os.path.join(HERE, f"content_{book}_plain.py.bak"), encoding="utf-8").read()
        tree = ast.parse(src)
        units_node = get_units_node(tree)
        plain = __import__(f"content_{book}_plain_mod_{book}") if False else None
        # 元の answer(plain) を取得するため plain バックアップを実行して読む
        ns = {}
        exec(compile(ast.parse(src), f"<{book}>", "exec"), ns)
        plain_units = ns["UNITS"]

        for ui, unit_node in enumerate(units_node.elts):
            if ui not in by_book[book]:
                continue
            r = by_book[book][ui]
            probs_node = dict_get(unit_node, "problems")
            rmap = {x["idx"]: x for x in r.get("rewritten", [])}
            for pi, prob_node in enumerate(probs_node.elts):
                if pi in rmap:
                    rw = rmap[pi]
                    dict_set(prob_node, "stem", const(rw["stem"]))
                    dict_set(prob_node, "answer", const(rw["answer"]))
                    dict_set(prob_node, "explanation", const(rw["explanation"]))
                    if rw.get("choices"):
                        dict_set(prob_node, "choices", const(rw["choices"]))
                    # 忠実性: 元 answer と LaTeX戻し answer を比較
                    old_ans = plain_units[ui]["problems"][pi].get("answer", "")
                    if norm(old_ans) != norm(rw["answer"]):
                        faithfulness.append((book, r["unitName"], pi,
                                             old_ans, rw["answer"], norm(old_ans), norm(rw["answer"])))
            # 新規問題を追加
            for p in r.get("new_problems", []):
                probs_node.elts.append(build_new_problem(p))

        new_src = HEADER % title + "UNITS = " + ast.unparse(units_node) + "\n"
        out = os.path.join(HERE, f"content_{book}.py")
        open(out, "w", encoding="utf-8").write(new_src)
        nnew = sum(len(by_book[book][ui].get("new_problems", [])) for ui in by_book[book])
        print(f"WROTE {out} | 新規追加 {nnew}問")

    print("\n=== 忠実性レビュー(要目視: 元answer vs LaTeX戻し) ===")
    if not faithfulness:
        print("  差分なし ✓ (既存問題の値は保存されている)")
    for book, un, pi, oa, na, no, nn in faithfulness:
        print(f"  ? {book}/{un}#{pi+1}: 元『{oa}』 → 新『{na}』  (norm: {no} vs {nn})")

if __name__ == "__main__":
    main()
