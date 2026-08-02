#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト模試 2026 (数学I・A / 数学II・B・C) の seed JSON 生成器。

対象プール (EXAM_QUESTION_ROTATION と一致必須):
  ("rikei", "math_1a", "kyotsu_rikei")  … MOCK_EXAM_TEMPLATES["kyotsu_math"] 第1セクション
  ("rikei", "math_2b", "kyotsu_rikei")  … 同 第2セクション

方針 (build_daimon.py と同じ「正解を手入力しない」原則):
  各小問は correct / distractors を「LaTeX と sympy 値」の組で持ち、さらに verify() で
  独立に再計算した値と照合する。手入力ミスは import 前にここで落ちる。

  - verify() の結果 != correct の値 → AssertionError
  - distractor が correct と同値 (別表記の同一値) → AssertionError
  - 正解位置は md5 順で 0..3 に均等配分 (正解が 0 番に偏る事故の対策)

出力: seed-data/kyotsu_mogi2026_math_manual.json
実行: python3 scripts/kyotsu_mogi2026/build_math.py
"""
import json
import hashlib
import os

from sympy import (
    Integer, Rational, symbols, sqrt, pi, oo, expand, factor, simplify, summation,
    Tuple, FiniteSet, Interval, Union, S, solveset, Eq, integrate, diff, binomial,
    sin, cos, Abs, sympify,
)

x, y, k, n, t = symbols('x y k n t')

OUT = os.path.join(os.path.dirname(__file__), '..', '..',
                   'seed-data', 'kyotsu_mogi2026_math_manual.json')
SOURCE = 'kyotsu-mogi2026-20260802'
MODEL = 'claude-kyotsu-mogi2026-verified'

DAIMON = []


def D(part_key, group, passage, subqs):
    DAIMON.append({"part_key": part_key, "group": group, "passage": passage, "subqs": subqs})


def _eq(u, v):
    """sympy 値の等価判定。Tuple(組) は要素ごと、Set/文字列は ==、数式は simplify(差)==0。"""
    if isinstance(u, str) or isinstance(v, str):
        return u == v
    if isinstance(u, Tuple) or isinstance(v, Tuple):
        if not (isinstance(u, Tuple) and isinstance(v, Tuple)) or len(u) != len(v):
            return False
        return all(_eq(ui, vi) for ui, vi in zip(u, v))
    if isinstance(u, (FiniteSet, Interval, Union)) or isinstance(v, (FiniteSet, Interval, Union)):
        return u == v
    try:
        return simplify(u - v) == 0
    except TypeError:
        return u == v


# =====================================================================
# 数学I・A  (part_key = math_1a)
# =====================================================================

# ---- 第1問 数と式・集合と命題 ---------------------------------------
D("math_1a", "数学I・A 第1問",
  "太郎さんは、式の計算と論証の復習をしている。次の問い(問1〜問5)に答えよ。"
  "各小問は独立しており、それぞれ単独で解答できる。文字はすべて実数を表すものとする。",
  [
    dict(
        stem="式 \\((3x-2y)^2-(3x+2y)(3x-2y)\\) を展開して整理したものとして正しいものはどれか。",
        unit="数と式",
        correct=("\\(-12xy+8y^2\\)", expand((3 * x - 2 * y) ** 2 - (3 * x + 2 * y) * (3 * x - 2 * y))),
        distractors=[("\\(12xy+8y^2\\)", 12 * x * y + 8 * y ** 2),
                     ("\\(-12xy\\)", -12 * x * y),
                     ("\\(18x^2-12xy+8y^2\\)", 18 * x ** 2 - 12 * x * y + 8 * y ** 2)],
        verify=lambda: expand((9 * x ** 2 - 12 * x * y + 4 * y ** 2) - (9 * x ** 2 - 4 * y ** 2)),
        reason="\\((3x-2y)^2=9x^2-12xy+4y^2\\)、\\((3x+2y)(3x-2y)=9x^2-4y^2\\)。"
               "差をとると \\((9x^2-12xy+4y^2)-(9x^2-4y^2)=-12xy+8y^2\\)。"
               "後ろのカッコの \\(-4y^2\\) にマイナスを配り忘れると \\(-12xy\\) になってしまうので注意。",
    ),
    dict(
        stem="二次式 \\(6x^2+x-12\\) を因数分解したものとして正しいものはどれか。",
        unit="数と式",
        correct=("\\((2x+3)(3x-4)\\)", expand((2 * x + 3) * (3 * x - 4))),
        distractors=[("\\((2x-3)(3x+4)\\)", expand((2 * x - 3) * (3 * x + 4))),
                     ("\\((6x-3)(x+4)\\)", expand((6 * x - 3) * (x + 4))),
                     ("\\((3x+2)(2x-6)\\)", expand((3 * x + 2) * (2 * x - 6)))],
        verify=lambda: expand(factor(6 * x ** 2 + x - 12)),
        reason="たすき掛けで \\((2x+m)(3x+n)\\) とおくと \\(mn=-12\\)、\\(2n+3m=1\\)。"
               "\\(m=3,\\ n=-4\\) が \\(2(-4)+3(3)=1\\) を満たすので \\((2x+3)(3x-4)\\)。"
               "展開して \\(6x^2-8x+9x-12=6x^2+x-12\\) と検算できる。"
               "符号を入れ替えた \\((2x-3)(3x+4)\\) は \\(6x^2-x-12\\) となり中央項の符号が逆。",
    ),
    dict(
        stem="実数 \\(a,\\ b\\) が \\(a+b=4\\)、\\(ab=2\\) を満たすとき、\\(a^3+b^3\\) の値はいくらか。",
        unit="数と式",
        correct=("\\(40\\)", Integer(40)),
        distractors=[("\\(64\\)", Integer(64)), ("\\(56\\)", Integer(56)), ("\\(52\\)", Integer(52))],
        verify=lambda: Integer(4) ** 3 - 3 * Integer(2) * Integer(4),
        reason="対称式の変形 \\(a^3+b^3=(a+b)^3-3ab(a+b)\\) を使う。"
               "\\(4^3-3\\cdot 2\\cdot 4=64-24=40\\)。"
               "\\(3ab(a+b)\\) を引き忘れると \\(64\\)、\\(ab\\) だけ引くと \\(64-8=56\\) となる典型ミス。",
    ),
    dict(
        stem="不等式 \\(|2x-5|<3\\) を満たす整数 \\(x\\) は何個あるか。",
        unit="数と式",
        correct=("\\(2\\) 個", Integer(2)),
        distractors=[("\\(3\\) 個", Integer(3)), ("\\(4\\) 個", Integer(4)), ("\\(1\\) 個", Integer(1))],
        verify=lambda: Integer(len([i for i in range(-20, 21) if abs(2 * i - 5) < 3])),
        reason="\\(|2x-5|<3\\) は \\(-3<2x-5<3\\)、すなわち \\(2<2x<8\\) より \\(1<x<4\\)。"
               "この範囲の整数は \\(x=2,\\ 3\\) の \\(2\\) 個。"
               "端点 \\(x=1,\\ 4\\) は等号を含まないので入らない (含めると \\(4\\) 個と誤る)。",
    ),
    dict(
        stem="実数 \\(x\\) について、条件「\\(x^2=9\\)」は条件「\\(x=3\\)」であるための何条件か。",
        unit="集合と命題",
        correct=("必要条件であるが十分条件でない", "必要"),
        distractors=[("十分条件であるが必要条件でない", "十分"),
                     ("必要十分条件", "同値"),
                     ("必要条件でも十分条件でもない", "無関係")],
        verify=lambda: _condition_label(solveset(Eq(x ** 2, 9), x, S.Reals),
                                        solveset(Eq(x, 3), x, S.Reals)),
        reason="\\(x=3\\) ならば \\(x^2=9\\) は常に成り立つので「\\(x^2=9\\)」は必要条件。"
               "逆に \\(x^2=9\\) からは \\(x=-3\\) の可能性が残り「\\(x=3\\)」は導けないので十分条件ではない。"
               "解集合で見ると \\(\\{-3,3\\}\\supsetneq\\{3\\}\\)、範囲の広い方が必要条件と覚えるとよい。",
    ),
  ])


def _extrema_on_interval(expr, var, lo, hi):
    """閉区間 [lo, hi] における最大値・最小値を、停留点と端点の厳密値から求めて Tuple(最大, 最小) を返す。"""
    cands = [lo, hi]
    for r in solveset(Eq(diff(expr, var), 0), var, Interval(lo, hi)):
        cands.append(r)
    vals = [simplify(expr.subs(var, c)) for c in cands]
    vals.sort(key=lambda v: float(v.evalf()))
    return Tuple(vals[-1], vals[0])


def _local_max_value(expr, var):
    """f''<0 となる停留点での値 (= 極大値) を返す。"""
    d1, d2 = diff(expr, var), diff(expr, var, 2)
    for r in solveset(Eq(d1, 0), var, S.Reals):
        if d2.subs(var, r) < 0:
            return simplify(expr.subs(var, r))
    raise ValueError("極大値が見つからない")


def _condition_label(set_p, set_q):
    """条件 p が条件 q であるための何条件か (解集合の包含関係から判定)。"""
    p_sup_q = set_q.is_subset(set_p)
    q_sup_p = set_p.is_subset(set_q)
    if p_sup_q and q_sup_p:
        return "同値"
    if p_sup_q:
        return "必要"
    if q_sup_p:
        return "十分"
    return "無関係"


# ---- 第2問 図形と計量 -----------------------------------------------
# 三角形 ABC: AB=6, AC=10, ∠A=120° ⇒ BC=14, S=15√3, R=14√3/3, r=√3, cosB=11/14
_c, _b, _cosA = Integer(6), Integer(10), Rational(-1, 2)
_a = sqrt(_b ** 2 + _c ** 2 - 2 * _b * _c * _cosA)
_S = Rational(1, 2) * _b * _c * sqrt(1 - _cosA ** 2)

D("math_1a", "数学I・A 第2問",
  "花子さんは、校庭にある三角形の花壇 ABC を測量した。測量の結果、"
  "\\(AB=6\\ \\mathrm{m}\\)、\\(AC=10\\ \\mathrm{m}\\)、\\(\\angle A=120^\\circ\\) であることが分かった。"
  "この花壇について次の問い(問1〜問5)に答えよ。"
  "各小問に必要な値は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="\\(AB=6\\)、\\(AC=10\\)、\\(\\angle A=120^\\circ\\) の三角形 ABC について、辺 \\(BC\\) の長さを求めよ。",
        unit="図形と計量",
        correct=("\\(14\\)", Integer(14)),
        distractors=[("\\(2\\sqrt{19}\\)", 2 * sqrt(19)), ("\\(4\\sqrt{6}\\)", 4 * sqrt(6)), ("\\(16\\)", Integer(16))],
        verify=lambda: simplify(_a),
        reason="余弦定理より \\(BC^2=6^2+10^2-2\\cdot 6\\cdot 10\\cos 120^\\circ\\)。"
               "\\(\\cos 120^\\circ=-\\dfrac12\\) だから \\(BC^2=36+100+60=196\\)、よって \\(BC=14\\)。"
               "\\(\\cos 120^\\circ\\) の符号を \\(+\\dfrac12\\) と誤ると \\(BC^2=76\\)、\\(BC=2\\sqrt{19}\\) になる。",
    ),
    dict(
        stem="\\(AB=6\\)、\\(AC=10\\)、\\(\\angle A=120^\\circ\\) の三角形 ABC の面積を求めよ。",
        unit="図形と計量",
        correct=("\\(15\\sqrt{3}\\)", 15 * sqrt(3)),
        distractors=[("\\(30\\sqrt{3}\\)", 30 * sqrt(3)), ("\\(15\\)", Integer(15)), ("\\(30\\)", Integer(30))],
        verify=lambda: simplify(_S),
        reason="\\(S=\\dfrac12\\cdot AB\\cdot AC\\sin A\\) に代入する。"
               "\\(\\sin 120^\\circ=\\dfrac{\\sqrt3}{2}\\) なので "
               "\\(S=\\dfrac12\\cdot 6\\cdot 10\\cdot\\dfrac{\\sqrt3}{2}=15\\sqrt3\\)。"
               "\\(\\dfrac12\\) を掛け忘れると \\(30\\sqrt3\\) となる。",
    ),
    dict(
        stem="三角形 ABC において \\(BC=14\\)、\\(\\angle A=120^\\circ\\) であるとき、外接円の半径 \\(R\\) を求めよ。",
        unit="図形と計量",
        correct=("\\(\\dfrac{14\\sqrt{3}}{3}\\)", Rational(14, 3) * sqrt(3)),
        distractors=[("\\(\\dfrac{28\\sqrt{3}}{3}\\)", Rational(28, 3) * sqrt(3)),
                     ("\\(\\dfrac{7\\sqrt{3}}{3}\\)", Rational(7, 3) * sqrt(3)),
                     ("\\(7\\sqrt{3}\\)", 7 * sqrt(3))],
        verify=lambda: simplify(Integer(14) / (2 * sqrt(3) / 2)),
        reason="正弦定理 \\(\\dfrac{BC}{\\sin A}=2R\\) を使う。"
               "\\(\\sin 120^\\circ=\\dfrac{\\sqrt3}{2}\\) だから "
               "\\(2R=\\dfrac{14}{\\sqrt3/2}=\\dfrac{28}{\\sqrt3}\\)、"
               "よって \\(R=\\dfrac{14}{\\sqrt3}=\\dfrac{14\\sqrt3}{3}\\)。"
               "\\(2R\\) をそのまま答えると \\(\\dfrac{28\\sqrt3}{3}\\) になる。",
    ),
    dict(
        stem="三角形 ABC において \\(AB=6\\)、\\(BC=14\\)、\\(CA=10\\)、面積が \\(15\\sqrt{3}\\) であるとき、"
             "内接円の半径 \\(r\\) を求めよ。",
        unit="図形と計量",
        correct=("\\(\\sqrt{3}\\)", sqrt(3)),
        distractors=[("\\(\\dfrac{\\sqrt{3}}{2}\\)", sqrt(3) / 2),
                     ("\\(2\\sqrt{3}\\)", 2 * sqrt(3)),
                     ("\\(\\dfrac{15\\sqrt{3}}{14}\\)", Rational(15, 14) * sqrt(3))],
        verify=lambda: simplify(_S / (Rational(1, 2) * (14 + 6 + 10))),
        reason="\\(S=rs\\) (\\(s\\) は周の半分) を使う。"
               "\\(s=\\dfrac{6+14+10}{2}=15\\) だから \\(r=\\dfrac{S}{s}=\\dfrac{15\\sqrt3}{15}=\\sqrt3\\)。"
               "\\(s\\) を周の長さ \\(30\\) のまま使うと \\(\\dfrac{\\sqrt3}{2}\\) と半分になってしまう。",
    ),
    dict(
        stem="三角形 ABC において \\(AB=6\\)、\\(BC=14\\)、\\(CA=10\\) であるとき、\\(\\cos B\\) の値を求めよ。",
        unit="図形と計量",
        correct=("\\(\\dfrac{11}{14}\\)", Rational(11, 14)),
        distractors=[("\\(\\dfrac{13}{14}\\)", Rational(13, 14)),
                     ("\\(\\dfrac{11}{12}\\)", Rational(11, 12)),
                     ("\\(-\\dfrac{1}{2}\\)", Rational(-1, 2))],
        verify=lambda: simplify((Integer(14) ** 2 + Integer(6) ** 2 - Integer(10) ** 2) / (2 * 14 * 6)),
        reason="角 B をはさむ辺は \\(BA=6\\) と \\(BC=14\\)、向かい合う辺は \\(CA=10\\)。"
               "余弦定理より \\(\\cos B=\\dfrac{14^2+6^2-10^2}{2\\cdot 14\\cdot 6}"
               "=\\dfrac{196+36-100}{168}=\\dfrac{132}{168}=\\dfrac{11}{14}\\)。"
               "向かい合う辺を取り違えて \\(6^2\\) を引くと \\(\\dfrac{13}{14}\\) になる。",
    ),
  ])


# ---- 第3問 二次関数 --------------------------------------------------
_f2 = 2 * x ** 2 - 8 * x + 5

D("math_1a", "数学I・A 第3問",
  "太郎さんは二次関数 \\(y=2x^2-8x+5\\) のグラフとその応用について調べている。"
  "次の問い(問1〜問5)に答えよ。各小問に必要な式や条件は問題文中に再掲してあるので、"
  "それぞれ単独で解答できる。",
  [
    dict(
        stem="二次関数 \\(y=2x^2-8x+5\\) のグラフの頂点の座標を求めよ。",
        unit="二次関数",
        correct=("\\((2,\\ -3)\\)", Tuple(Integer(2), Integer(-3))),
        distractors=[("\\((2,\\ 3)\\)", Tuple(Integer(2), Integer(3))),
                     ("\\((-2,\\ -3)\\)", Tuple(Integer(-2), Integer(-3))),
                     ("\\((4,\\ -3)\\)", Tuple(Integer(4), Integer(-3)))],
        verify=lambda: Tuple(Integer(2), _f2.subs(x, 2)),
        reason="平方完成する。\\(y=2(x^2-4x)+5=2(x-2)^2-8+5=2(x-2)^2-3\\)。"
               "よって頂点は \\((2,\\ -3)\\)。"
               "\\(2\\) でくくった分 \\(2\\times(-2)^2=8\\) を引くのを忘れると \\(y\\) 座標を \\(3\\) と誤る。",
    ),
    dict(
        stem="二次関数 \\(y=2x^2-8x+5\\) の \\(0\\le x\\le 3\\) における最小値を求めよ。",
        unit="二次関数",
        correct=("\\(-3\\)", Integer(-3)),
        distractors=[("\\(-1\\)", Integer(-1)), ("\\(5\\)", Integer(5)), ("\\(0\\)", Integer(0))],
        verify=lambda: min(_f2.subs(x, Rational(i, 20)) for i in range(0, 61)),
        reason="頂点は \\((2,\\ -3)\\) で、\\(x=2\\) は区間 \\(0\\le x\\le 3\\) の内部にある。"
               "下に凸だから最小値は頂点の \\(y\\) 座標そのもので \\(-3\\)。"
               "端点だけを比べると \\(f(0)=5\\)、\\(f(3)=-1\\) なので \\(-1\\) と誤りやすいが、"
               "頂点が区間に入るかどうかを必ず先に確認する。",
    ),
    dict(
        stem="二次方程式 \\(x^2-2(k+1)x+k^2+3=0\\) が異なる \\(2\\) つの実数解をもつような定数 \\(k\\) の値の範囲を求めよ。",
        unit="二次関数",
        correct=("\\(k>1\\)", Interval.open(1, oo)),
        distractors=[("\\(k<1\\)", Interval.open(-oo, 1)),
                     ("\\(k\\ge 1\\)", Interval(1, oo)),
                     ("\\(k>-1\\)", Interval.open(-1, oo))],
        verify=lambda: solveset((k + 1) ** 2 - (k ** 2 + 3) > 0, k, S.Reals),
        reason="判別式を \\(4\\) で割った \\(D/4=(k+1)^2-(k^2+3)\\) を使う。"
               "展開すると \\(k^2+2k+1-k^2-3=2k-2\\)。"
               "異なる \\(2\\) 実数解の条件は \\(D/4>0\\)、すなわち \\(2k-2>0\\) より \\(k>1\\)。"
               "\\(D/4\\ge 0\\) は重解を含むので不適 (等号を入れると \\(k\\ge 1\\) と誤る)。",
    ),
    dict(
        stem="二次不等式 \\(x^2-5x+6>0\\) を解け。",
        unit="二次関数",
        correct=("\\(x<2\\) または \\(x>3\\)", Union(Interval.open(-oo, 2), Interval.open(3, oo))),
        distractors=[("\\(2<x<3\\)", Interval.open(2, 3)),
                     ("\\(x\\le 2\\) または \\(x\\ge 3\\)", Union(Interval(-oo, 2), Interval(3, oo))),
                     ("すべての実数", S.Reals)],
        verify=lambda: solveset(x ** 2 - 5 * x + 6 > 0, x, S.Reals),
        reason="左辺を因数分解すると \\((x-2)(x-3)>0\\)。"
               "下に凸の放物線が \\(x\\) 軸と交わるのは \\(x=2,\\ 3\\) で、"
               "正になるのは \\(2\\) 解の外側だから \\(x<2\\) または \\(x>3\\)。"
               "不等号の向きを取り違えると \\(2<x<3\\) (2 解の間) になる。",
    ),
    dict(
        stem="二次関数 \\(y=2x^2-8x+5\\) のグラフを、\\(x\\) 軸方向に \\(-1\\)、\\(y\\) 軸方向に \\(4\\) だけ"
             "平行移動して得られるグラフの頂点の座標を求めよ。",
        unit="二次関数",
        correct=("\\((1,\\ 1)\\)", Tuple(Integer(1), Integer(1))),
        distractors=[("\\((3,\\ 1)\\)", Tuple(Integer(3), Integer(1))),
                     ("\\((1,\\ -7)\\)", Tuple(Integer(1), Integer(-7))),
                     ("\\((3,\\ -7)\\)", Tuple(Integer(3), Integer(-7)))],
        verify=lambda: Tuple(Integer(2) + Integer(-1), _f2.subs(x, 2) + Integer(4)),
        reason="平行移動は頂点の移動として捉えるのが速い。"
               "もとの頂点 \\((2,\\ -3)\\) を \\(x\\) 方向に \\(-1\\)、\\(y\\) 方向に \\(+4\\) 動かすと "
               "\\((2-1,\\ -3+4)=(1,\\ 1)\\)。"
               "\\(x\\) 方向の符号を逆にすると \\((3,\\ 1)\\) になるので、移動量の符号をそのまま足すことを徹底する。",
    ),
  ])


# ---- 第4問 データの分析 ----------------------------------------------
_scores = [4, 6, 7, 9, 9]
_mean = Rational(sum(_scores), len(_scores))
_var = Rational(sum((Integer(s) - _mean) ** 2 for s in _scores), len(_scores))

D("math_1a", "数学I・A 第4問",
  "あるクラスで 10 点満点の小テストを行い、生徒 5 人の得点を小さい順に並べたところ、"
  "次のようになった。\n\n"
  "  得点: 4, 6, 7, 9, 9 (単位は点)\n\n"
  "このデータについて次の問い(問1〜問5)に答えよ。"
  "各小問に必要なデータや値は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="得点が 4, 6, 7, 9, 9 の 5 個のデータについて、平均値を求めよ。",
        unit="データの分析",
        correct=("\\(7\\) 点", Integer(7)),
        distractors=[("\\(6.8\\) 点", Rational(34, 5)), ("\\(7.5\\) 点", Rational(15, 2)), ("\\(6\\) 点", Integer(6))],
        verify=lambda: Rational(sum(_scores), 5),
        reason="平均値は総和をデータの個数で割る。"
               "\\(4+6+7+9+9=35\\)、\\(35\\div 5=7\\) より \\(7\\) 点。",
    ),
    dict(
        stem="得点が 4, 6, 7, 9, 9 の 5 個のデータについて、分散を求めよ。ただし平均値は \\(7\\) 点である。",
        unit="データの分析",
        correct=("\\(3.6\\)", Rational(18, 5)),
        distractors=[("\\(4.5\\)", Rational(9, 2)), ("\\(3.2\\)", Rational(16, 5)), ("\\(2.6\\)", Rational(13, 5))],
        verify=lambda: Rational(sum((s - 7) ** 2 for s in _scores), 5),
        reason="分散は偏差の 2 乗の平均。偏差は \\(-3,\\ -1,\\ 0,\\ 2,\\ 2\\)。"
               "2 乗して和をとると \\(9+1+0+4+4=18\\)、"
               "データの個数 \\(5\\) で割って \\(\\dfrac{18}{5}=3.6\\)。"
               "\\(n-1=4\\) で割ると \\(4.5\\) になるが、共通テストの分散は \\(n\\) で割る。",
    ),
    dict(
        stem="得点が 4, 6, 7, 9, 9 の 5 個のデータについて、中央値 (メジアン) を求めよ。",
        unit="データの分析",
        correct=("\\(7\\) 点", Integer(7)),
        distractors=[("\\(6\\) 点", Integer(6)), ("\\(7.5\\) 点", Rational(15, 2)), ("\\(9\\) 点", Integer(9))],
        verify=lambda: Integer(sorted(_scores)[len(_scores) // 2]),
        reason="データは既に小さい順に並んでいて個数は \\(5\\) 個 (奇数) なので、"
               "中央値はちょうど真ん中の 3 番目の値、すなわち \\(7\\) 点。"
               "最頻値 (最も多く現れる値) は \\(9\\) 点で、中央値とは別物である点に注意。",
    ),
    dict(
        stem="平均値 \\(7\\)、分散 \\(3.6\\) のデータ \\(x\\) に対し、\\(u=2x+3\\) で新しい変量 \\(u\\) をつくる。"
             "このとき \\(u\\) の平均値と分散の組として正しいものはどれか。",
        unit="データの分析",
        correct=("平均 \\(17\\)、分散 \\(14.4\\)", Tuple(Integer(17), Rational(72, 5))),
        distractors=[("平均 \\(17\\)、分散 \\(7.2\\)", Tuple(Integer(17), Rational(36, 5))),
                     ("平均 \\(14\\)、分散 \\(14.4\\)", Tuple(Integer(14), Rational(72, 5))),
                     ("平均 \\(17\\)、分散 \\(3.6\\)", Tuple(Integer(17), Rational(18, 5)))],
        verify=lambda: (lambda us, m: Tuple(m, Rational(sum((Integer(u) - m) ** 2 for u in us), len(us))))(
            [2 * s + 3 for s in _scores], Rational(sum(2 * s + 3 for s in _scores), len(_scores))),
        reason="\\(u=ax+b\\) のとき平均は \\(a\\bar{x}+b\\)、分散は \\(a^2\\) 倍になる。"
               "平均は \\(2\\times 7+3=17\\)、分散は \\(2^2\\times 3.6=14.4\\)。"
               "分散に \\(+3\\) は影響しない (平行移動ではばらつきは変わらない)。"
               "\\(a\\) を 2 乗し忘れると \\(7.2\\) と誤る。",
    ),
    dict(
        stem="2 つの変量 \\(x,\\ y\\) について、共分散が \\(-4.2\\)、\\(x\\) の標準偏差が \\(3\\)、"
             "\\(y\\) の標準偏差が \\(2\\) であるとき、相関係数を求めよ。",
        unit="データの分析",
        correct=("\\(-0.7\\)", Rational(-7, 10)),
        distractors=[("\\(-0.35\\)", Rational(-7, 20)), ("\\(0.7\\)", Rational(7, 10)), ("\\(-2.1\\)", Rational(-21, 10))],
        verify=lambda: Rational(-42, 10) / (Integer(3) * Integer(2)),
        reason="相関係数は \\(r=\\dfrac{s_{xy}}{s_x s_y}\\)。"
               "\\(r=\\dfrac{-4.2}{3\\times 2}=\\dfrac{-4.2}{6}=-0.7\\)。"
               "分母を片方の標準偏差だけにすると \\(-1.4\\)、"
               "割らずに答えると \\(-4.2\\) となる。相関係数は必ず \\(-1\\le r\\le 1\\) に収まることで検算できる。",
    ),
  ])


# ---- 第5問 場合の数と確率 --------------------------------------------
_C = binomial

D("math_1a", "数学I・A 第5問",
  "赤玉 4 個、白玉 5 個の合計 9 個が入った袋がある。玉は色以外に区別がつかないものとし、"
  "袋の中はよくかき混ぜてあるものとする。次の問い(問1〜問5)に答えよ。"
  "各小問に必要な設定は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="赤玉 4 個、白玉 5 個の計 9 個から同時に 3 個を取り出すとき、取り出し方は何通りあるか。",
        unit="場合の数・確率",
        correct=("\\(84\\) 通り", _C(9, 3)),
        distractors=[("\\(504\\) 通り", Integer(504)), ("\\(126\\) 通り", Integer(126)), ("\\(729\\) 通り", Integer(729))],
        verify=lambda: _C(9, 3),
        reason="同時に取り出すので順序は区別しない。組合せ "
               "\\({}_9\\mathrm{C}_3=\\dfrac{9\\cdot 8\\cdot 7}{3\\cdot 2\\cdot 1}=84\\) 通り。"
               "順序を区別してしまうと \\({}_9\\mathrm{P}_3=504\\) 通りと 6 倍になる。",
    ),
    dict(
        stem="赤玉 4 個、白玉 5 個の計 9 個から同時に 3 個を取り出すとき、3 個とも赤玉である確率を求めよ。",
        unit="場合の数・確率",
        correct=("\\(\\dfrac{1}{21}\\)", Rational(1, 21)),
        distractors=[("\\(\\dfrac{1}{84}\\)", Rational(1, 84)),
                     ("\\(\\dfrac{4}{21}\\)", Rational(4, 21)),
                     ("\\(\\dfrac{1}{14}\\)", Rational(1, 14))],
        verify=lambda: Rational(_C(4, 3), _C(9, 3)),
        reason="全事象は \\({}_9\\mathrm{C}_3=84\\) 通り。"
               "赤玉 4 個から 3 個を選ぶのは \\({}_4\\mathrm{C}_3=4\\) 通り。"
               "よって確率は \\(\\dfrac{4}{84}=\\dfrac{1}{21}\\)。"
               "分子を 1 通りと数えると \\(\\dfrac{1}{84}\\) になる (赤玉も 1 個ずつ区別して数える)。",
    ),
    dict(
        stem="赤玉 4 個、白玉 5 個の計 9 個から同時に 3 個を取り出すとき、"
             "赤玉 2 個・白玉 1 個である確率を求めよ。",
        unit="場合の数・確率",
        correct=("\\(\\dfrac{5}{14}\\)", Rational(5, 14)),
        distractors=[("\\(\\dfrac{10}{21}\\)", Rational(10, 21)),
                     ("\\(\\dfrac{15}{28}\\)", Rational(15, 28)),
                     ("\\(\\dfrac{5}{28}\\)", Rational(5, 28))],
        verify=lambda: Rational(_C(4, 2) * _C(5, 1), _C(9, 3)),
        reason="赤 2 個の選び方は \\({}_4\\mathrm{C}_2=6\\) 通り、白 1 個の選び方は "
               "\\({}_5\\mathrm{C}_1=5\\) 通りで、積は \\(30\\) 通り。"
               "全事象 \\(84\\) 通りで割って \\(\\dfrac{30}{84}=\\dfrac{5}{14}\\)。"
               "色ごとの選び方は「かけ算」でつなぐ (足すと誤り)。",
    ),
    dict(
        stem="赤玉 4 個、白玉 5 個の計 9 個から 1 個ずつ続けて 2 回取り出す。取り出した玉は袋に戻さない。"
             "1 回目が赤玉であったとき、2 回目も赤玉である条件付き確率を求めよ。",
        unit="場合の数・確率",
        correct=("\\(\\dfrac{3}{8}\\)", Rational(3, 8)),
        distractors=[("\\(\\dfrac{4}{9}\\)", Rational(4, 9)),
                     ("\\(\\dfrac{1}{2}\\)", Rational(1, 2)),
                     ("\\(\\dfrac{1}{6}\\)", Rational(1, 6))],
        verify=lambda: Rational(4 - 1, 9 - 1),
        reason="1 回目に赤玉を取り出した後、袋の中は赤玉 \\(3\\) 個・白玉 \\(5\\) 個の計 \\(8\\) 個。"
               "その中から赤玉を引く確率だから \\(\\dfrac{3}{8}\\)。"
               "戻さないことを見落として \\(\\dfrac{4}{9}\\) とするのが典型ミス。",
    ),
    dict(
        stem="赤玉 4 個、白玉 5 個の計 9 個から同時に 3 個を取り出すとき、"
             "取り出した赤玉の個数の期待値を求めよ。",
        unit="場合の数・確率",
        correct=("\\(\\dfrac{4}{3}\\)", Rational(4, 3)),
        distractors=[("\\(1\\)", Integer(1)), ("\\(\\dfrac{3}{2}\\)", Rational(3, 2)), ("\\(\\dfrac{2}{3}\\)", Rational(2, 3))],
        verify=lambda: sum(Integer(i) * Rational(_C(4, i) * _C(5, 3 - i), _C(9, 3)) for i in range(0, 4)),
        reason="赤玉の個数 \\(X\\) は \\(0,1,2,3\\) の値をとり、"
               "\\(P(X=i)=\\dfrac{{}_4\\mathrm{C}_i\\cdot{}_5\\mathrm{C}_{3-i}}{{}_9\\mathrm{C}_3}\\)。"
               "\\(P(0)=\\dfrac{10}{84}\\)、\\(P(1)=\\dfrac{40}{84}\\)、\\(P(2)=\\dfrac{30}{84}\\)、"
               "\\(P(3)=\\dfrac{4}{84}\\) で、\\(E(X)=\\dfrac{0+40+60+12}{84}=\\dfrac{112}{84}=\\dfrac43\\)。"
               "「1 個あたり赤の割合 \\(\\dfrac49\\) を 3 倍する」と考えても "
               "\\(3\\times\\dfrac49=\\dfrac43\\) と一致する。",
    ),
  ])


# ---- 第6問 図形の性質 ------------------------------------------------
D("math_1a", "数学I・A 第6問",
  "花子さんは円と三角形の性質について復習している。次の問い(問1〜問5)に答えよ。"
  "各小問に必要な設定はすべて問題文中に書かれており、それぞれ単独で解答できる。",
  [
    dict(
        stem="円 O の外部の点 P を通る直線が円 O と 2 点 A, B で交わっており、\\(PA=3\\)、\\(AB=5\\) である"
             "(A は P に近い方の交点)。また、点 P から円 O に引いた接線の接点を T とする。"
             "このとき線分 \\(PT\\) の長さを求めよ。",
        unit="図形の性質",
        correct=("\\(2\\sqrt{6}\\)", 2 * sqrt(6)),
        distractors=[("\\(\\sqrt{15}\\)", sqrt(15)), ("\\(4\\)", Integer(4)), ("\\(2\\sqrt{3}\\)", 2 * sqrt(3))],
        verify=lambda: sqrt(Integer(3) * (Integer(3) + Integer(5))),
        reason="方べきの定理 (接線の場合) より \\(PT^2=PA\\cdot PB\\)。"
               "\\(PB=PA+AB=3+5=8\\) だから \\(PT^2=3\\times 8=24\\)、\\(PT=2\\sqrt6\\)。"
               "\\(PB\\) を \\(AB=5\\) と取り違えると \\(PT=\\sqrt{15}\\) になるので、"
               "\\(PB\\) は P から遠い方の交点までの長さであることに注意。",
    ),
    dict(
        stem="三角形 ABC において、辺 AB を \\(2:1\\) に内分する点を D、辺 BC を \\(3:2\\) に内分する点を E とする。"
             "直線 DE と直線 AC の交点を F とするとき、\\(AF:FC\\) を求めよ。",
        unit="図形の性質",
        correct=("\\(3:1\\)", Tuple(Integer(3), Integer(1))),
        distractors=[("\\(1:3\\)", Tuple(Integer(1), Integer(3))),
                     ("\\(3:2\\)", Tuple(Integer(3), Integer(2))),
                     ("\\(2:1\\)", Tuple(Integer(2), Integer(1)))],
        verify=lambda: _menelaus_af_fc(),
        reason="三角形 ABC と直線 DEF にメネラウスの定理を使う。"
               "\\(\\dfrac{AD}{DB}\\cdot\\dfrac{BE}{EC}\\cdot\\dfrac{CF}{FA}=1\\) に "
               "\\(\\dfrac{AD}{DB}=\\dfrac21\\)、\\(\\dfrac{BE}{EC}=\\dfrac32\\) を代入すると "
               "\\(3\\cdot\\dfrac{CF}{FA}=1\\)、よって \\(\\dfrac{CF}{FA}=\\dfrac13\\)。"
               "すなわち \\(AF:FC=3:1\\) (F は辺 AC を C の側に延長した上にある)。",
    ),
    dict(
        stem="円に内接する四角形 ABCD において \\(\\angle A=105^\\circ\\) であるとき、\\(\\angle C\\) の大きさを求めよ。",
        unit="図形の性質",
        correct=("\\(75^\\circ\\)", Integer(75)),
        distractors=[("\\(105^\\circ\\)", Integer(105)), ("\\(85^\\circ\\)", Integer(85)), ("\\(90^\\circ\\)", Integer(90))],
        verify=lambda: Integer(180) - Integer(105),
        reason="円に内接する四角形では向かい合う内角の和が \\(180^\\circ\\) になる。"
               "\\(\\angle A+\\angle C=180^\\circ\\) より \\(\\angle C=180^\\circ-105^\\circ=75^\\circ\\)。"
               "「等しくなる」と覚え違えると \\(105^\\circ\\) と誤答する。",
    ),
    dict(
        stem="三角形 ABC において \\(AB=8\\)、\\(AC=6\\) である。\\(\\angle A\\) の二等分線と辺 BC の交点を D とするとき、"
             "\\(BD:DC\\) を求めよ。",
        unit="図形の性質",
        correct=("\\(4:3\\)", Tuple(Integer(4), Integer(3))),
        distractors=[("\\(3:4\\)", Tuple(Integer(3), Integer(4))),
                     ("\\(16:9\\)", Tuple(Integer(16), Integer(9))),
                     ("\\(2:1\\)", Tuple(Integer(2), Integer(1)))],
        verify=lambda: (lambda g: Tuple(Integer(8) / g, Integer(6) / g))(Integer(2)),
        reason="角の二等分線の性質より \\(BD:DC=AB:AC\\)。"
               "\\(AB:AC=8:6=4:3\\) だから \\(BD:DC=4:3\\)。"
               "比の向きを逆にすると \\(3:4\\)、辺の 2 乗の比と混同すると \\(16:9\\) になる。",
    ),
    dict(
        stem="座標平面上の 3 点 \\(A(1,\\ 2)\\)、\\(B(5,\\ -2)\\)、\\(C(3,\\ 6)\\) を頂点とする三角形 ABC の"
             "重心の座標を求めよ。",
        unit="図形の性質",
        correct=("\\((3,\\ 2)\\)", Tuple(Integer(3), Integer(2))),
        distractors=[("\\((3,\\ 3)\\)", Tuple(Integer(3), Integer(3))),
                     ("\\((9,\\ 6)\\)", Tuple(Integer(9), Integer(6))),
                     ("\\((2,\\ 2)\\)", Tuple(Integer(2), Integer(2)))],
        verify=lambda: Tuple(Rational(1 + 5 + 3, 3), Rational(2 - 2 + 6, 3)),
        reason="重心の座標は 3 頂点の座標の平均。"
               "\\(x\\) 座標は \\(\\dfrac{1+5+3}{3}=3\\)、\\(y\\) 座標は \\(\\dfrac{2+(-2)+6}{3}=2\\)。"
               "よって \\((3,\\ 2)\\)。3 で割り忘れると \\((9,\\ 6)\\) になる。",
    ),
  ])


def _menelaus_af_fc():
    """座標で直接計算して AF:FC を出す (メネラウスの検算)。"""
    ax, ay = Rational(0), Rational(0)
    bx, by = Rational(1), Rational(0)
    cx, cy = Rational(0), Rational(1)
    dx, dy = ax + Rational(2, 3) * (bx - ax), ay + Rational(2, 3) * (by - ay)   # AD:DB = 2:1
    ex, ey = bx + Rational(3, 5) * (cx - bx), by + Rational(3, 5) * (cy - by)   # BE:EC = 3:2
    # 直線 DE と直線 AC (x=0) の交点
    s = (ax - dx) / (ex - dx)
    fy = dy + s * (ey - dy)
    af = Abs(fy - ay)
    fc = Abs(fy - cy)
    g = simplify(af / fc)
    return Tuple(simplify(g), Integer(1))


# =====================================================================
# 数学II・B・C  (part_key = math_2b)
# =====================================================================

# ---- 第1問 三角関数 --------------------------------------------------
th = symbols('theta')

D("math_2b", "数学II・B・C 第1問",
  "太郎さんは三角関数の性質を復習している。次の問い(問1〜問5)に答えよ。"
  "角の大きさは、断りのない限り弧度法で表す。"
  "各小問に必要な条件は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="\\(0<\\theta<\\dfrac{\\pi}{2}\\) で \\(\\sin\\theta=\\dfrac{3}{5}\\) であるとき、"
             "\\(\\sin 2\\theta\\) の値を求めよ。",
        unit="三角関数",
        correct=("\\(\\dfrac{24}{25}\\)", Rational(24, 25)),
        distractors=[("\\(\\dfrac{12}{25}\\)", Rational(12, 25)),
                     ("\\(\\dfrac{7}{25}\\)", Rational(7, 25)),
                     ("\\(\\dfrac{6}{5}\\)", Rational(6, 5))],
        verify=lambda: simplify(2 * Rational(3, 5) * sqrt(1 - Rational(3, 5) ** 2)),
        reason="\\(0<\\theta<\\dfrac{\\pi}{2}\\) では \\(\\cos\\theta>0\\) なので "
               "\\(\\cos\\theta=\\sqrt{1-\\left(\\dfrac35\\right)^2}=\\dfrac45\\)。"
               "2 倍角の公式 \\(\\sin 2\\theta=2\\sin\\theta\\cos\\theta\\) より "
               "\\(2\\cdot\\dfrac35\\cdot\\dfrac45=\\dfrac{24}{25}\\)。"
               "\\(2\\) を掛け忘れると \\(\\dfrac{12}{25}\\)、"
               "\\(\\cos 2\\theta\\) と取り違えると \\(\\dfrac{7}{25}\\) になる。",
    ),
    dict(
        stem="\\(\\sin\\theta+\\sqrt{3}\\cos\\theta\\) を \\(r\\sin(\\theta+\\alpha)\\) "
             "(\\(r>0,\\ -\\pi<\\alpha\\le\\pi\\)) の形に変形したときの \\(r\\) と \\(\\alpha\\) の組はどれか。",
        unit="三角関数",
        correct=("\\(r=2,\\ \\alpha=\\dfrac{\\pi}{3}\\)", Tuple(Integer(2), pi / 3)),
        distractors=[("\\(r=2,\\ \\alpha=\\dfrac{\\pi}{6}\\)", Tuple(Integer(2), pi / 6)),
                     ("\\(r=4,\\ \\alpha=\\dfrac{\\pi}{3}\\)", Tuple(Integer(4), pi / 3)),
                     ("\\(r=\\sqrt{3}+1,\\ \\alpha=\\dfrac{\\pi}{4}\\)", Tuple(sqrt(3) + 1, pi / 4))],
        verify=lambda: Tuple(sqrt(Integer(1) ** 2 + sqrt(3) ** 2),
                             [a for a in (pi / 6, pi / 3, pi / 4)
                              if simplify(2 * cos(a) - 1) == 0 and simplify(2 * sin(a) - sqrt(3)) == 0][0]),
        reason="\\(a\\sin\\theta+b\\cos\\theta=r\\sin(\\theta+\\alpha)\\) では "
               "\\(r=\\sqrt{a^2+b^2}\\)、\\(\\cos\\alpha=\\dfrac{a}{r}\\)、\\(\\sin\\alpha=\\dfrac{b}{r}\\)。"
               "\\(r=\\sqrt{1^2+(\\sqrt3)^2}=2\\)、"
               "\\(\\cos\\alpha=\\dfrac12,\\ \\sin\\alpha=\\dfrac{\\sqrt3}{2}\\) より \\(\\alpha=\\dfrac{\\pi}{3}\\)。"
               "\\(\\sin\\) と \\(\\cos\\) の役割を逆にすると \\(\\alpha=\\dfrac{\\pi}{6}\\) と誤る。",
    ),
    dict(
        stem="\\(0\\le\\theta<2\\pi\\) のとき、方程式 \\(\\sin\\theta+\\sqrt{3}\\cos\\theta=1\\) の解をすべて求めよ。",
        unit="三角関数",
        correct=("\\(\\theta=\\dfrac{\\pi}{2},\\ \\dfrac{11\\pi}{6}\\)", FiniteSet(pi / 2, 11 * pi / 6)),
        distractors=[("\\(\\theta=\\dfrac{\\pi}{6},\\ \\dfrac{5\\pi}{6}\\)", FiniteSet(pi / 6, 5 * pi / 6)),
                     ("\\(\\theta=\\dfrac{\\pi}{3},\\ \\dfrac{5\\pi}{3}\\)", FiniteSet(pi / 3, 5 * pi / 3)),
                     ("\\(\\theta=\\dfrac{\\pi}{2}\\) のみ", FiniteSet(pi / 2))],
        verify=lambda: FiniteSet(*[m * pi / 12 for m in range(24)
                                   if simplify(sin(m * pi / 12) + sqrt(3) * cos(m * pi / 12) - 1) == 0]),
        reason="左辺を合成すると \\(2\\sin\\left(\\theta+\\dfrac{\\pi}{3}\\right)=1\\)、"
               "すなわち \\(\\sin\\left(\\theta+\\dfrac{\\pi}{3}\\right)=\\dfrac12\\)。"
               "\\(0\\le\\theta<2\\pi\\) では \\(\\dfrac{\\pi}{3}\\le\\theta+\\dfrac{\\pi}{3}<\\dfrac{7\\pi}{3}\\) なので、"
               "\\(\\theta+\\dfrac{\\pi}{3}=\\dfrac{5\\pi}{6},\\ \\dfrac{13\\pi}{6}\\)。"
               "よって \\(\\theta=\\dfrac{\\pi}{2},\\ \\dfrac{11\\pi}{6}\\)。"
               "\\(\\dfrac{\\pi}{3}\\) を引き忘れると \\(\\dfrac{5\\pi}{6}\\) 等をそのまま答えてしまう。",
    ),
    dict(
        stem="\\(\\cos 75^\\circ\\) の値を求めよ。",
        unit="三角関数",
        correct=("\\(\\dfrac{\\sqrt{6}-\\sqrt{2}}{4}\\)", (sqrt(6) - sqrt(2)) / 4),
        distractors=[("\\(\\dfrac{\\sqrt{6}+\\sqrt{2}}{4}\\)", (sqrt(6) + sqrt(2)) / 4),
                     ("\\(\\dfrac{\\sqrt{2}-\\sqrt{6}}{4}\\)", (sqrt(2) - sqrt(6)) / 4),
                     ("\\(\\dfrac{\\sqrt{3}-1}{4}\\)", (sqrt(3) - 1) / 4)],
        verify=lambda: simplify(cos(75 * pi / 180)),
        reason="\\(75^\\circ=45^\\circ+30^\\circ\\) と分けて加法定理 "
               "\\(\\cos(\\alpha+\\beta)=\\cos\\alpha\\cos\\beta-\\sin\\alpha\\sin\\beta\\) を使う。"
               "\\(\\dfrac{\\sqrt2}{2}\\cdot\\dfrac{\\sqrt3}{2}-\\dfrac{\\sqrt2}{2}\\cdot\\dfrac12"
               "=\\dfrac{\\sqrt6-\\sqrt2}{4}\\)。"
               "符号を \\(+\\) にすると \\(\\sin 75^\\circ\\) の値になってしまう。",
    ),
    dict(
        stem="\\(0\\le\\theta\\le\\pi\\) における関数 \\(y=\\sin\\theta+\\sqrt{3}\\cos\\theta\\) の"
             "最大値と最小値の組として正しいものはどれか。",
        unit="三角関数",
        correct=("最大値 \\(2\\)、最小値 \\(-\\sqrt{3}\\)", Tuple(Integer(2), -sqrt(3))),
        distractors=[("最大値 \\(2\\)、最小値 \\(-2\\)", Tuple(Integer(2), Integer(-2))),
                     ("最大値 \\(2\\)、最小値 \\(\\sqrt{3}\\)", Tuple(Integer(2), sqrt(3))),
                     ("最大値 \\(1+\\sqrt{3}\\)、最小値 \\(-\\sqrt{3}\\)", Tuple(1 + sqrt(3), -sqrt(3)))],
        verify=lambda: _extrema_on_interval(sin(th) + sqrt(3) * cos(th), th, Integer(0), pi),
        reason="合成すると \\(y=2\\sin\\left(\\theta+\\dfrac{\\pi}{3}\\right)\\)。"
               "\\(0\\le\\theta\\le\\pi\\) では \\(\\dfrac{\\pi}{3}\\le\\theta+\\dfrac{\\pi}{3}\\le\\dfrac{4\\pi}{3}\\)。"
               "この区間で \\(\\sin\\) は \\(\\dfrac{\\pi}{2}\\) で最大値 \\(1\\)、"
               "端の \\(\\dfrac{4\\pi}{3}\\) で最小値 \\(-\\dfrac{\\sqrt3}{2}\\) をとる。"
               "よって最大値 \\(2\\)、最小値 \\(-\\sqrt3\\)。"
               "\\(\\theta\\) の範囲を無視して振幅から \\(\\pm 2\\) と答えるのが典型ミス。",
    ),
  ])


# ---- 第2問 指数関数・対数関数 ----------------------------------------
D("math_2b", "数学II・B・C 第2問",
  "花子さんは指数関数と対数関数の計算を復習している。次の問い(問1〜問5)に答えよ。"
  "対数の底はすべて正で 1 と異なるものとし、真数は正とする。"
  "各小問に必要な条件は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="\\(\\left(\\dfrac{1}{8}\\right)^{-\\frac{2}{3}}\\) の値を求めよ。",
        unit="指数関数・対数関数",
        correct=("\\(4\\)", Integer(4)),
        distractors=[("\\(\\dfrac{1}{4}\\)", Rational(1, 4)), ("\\(2\\)", Integer(2)), ("\\(16\\)", Integer(16))],
        verify=lambda: simplify(Rational(1, 8) ** Rational(-2, 3)),
        reason="\\(\\left(\\dfrac18\\right)^{-\\frac23}=8^{\\frac23}=\\left(2^3\\right)^{\\frac23}=2^2=4\\)。"
               "指数の負号は逆数を意味する。"
               "負号を落とすと \\(8^{-\\frac23}=\\dfrac14\\) になる。",
    ),
    dict(
        stem="\\(\\log_2 24-\\log_2 3\\) の値を求めよ。",
        unit="指数関数・対数関数",
        correct=("\\(3\\)", Integer(3)),
        distractors=[("\\(2\\)", Integer(2)), ("\\(8\\)", Integer(8)), ("\\(\\log_2 21\\)", sympify('log(21)/log(2)'))],
        verify=lambda: simplify(sympify('log(24)/log(2) - log(3)/log(2)')),
        reason="対数の差は商に直せる。"
               "\\(\\log_2 24-\\log_2 3=\\log_2\\dfrac{24}{3}=\\log_2 8=3\\)。"
               "真数どうしを引いて \\(\\log_2 21\\) としてしまうのは公式の誤用。",
    ),
    dict(
        stem="方程式 \\(4^x-3\\cdot 2^x-4=0\\) を解け。",
        unit="指数関数・対数関数",
        correct=("\\(x=2\\)", FiniteSet(Integer(2))),
        distractors=[("\\(x=-1,\\ 2\\)", FiniteSet(Integer(-1), Integer(2))),
                     ("\\(x=1\\)", FiniteSet(Integer(1))),
                     ("\\(x=4\\)", FiniteSet(Integer(4)))],
        verify=lambda: solveset(Eq(4 ** x - 3 * 2 ** x - 4, 0), x, S.Reals),
        reason="\\(t=2^x\\ (t>0)\\) とおくと \\(4^x=(2^x)^2=t^2\\) なので \\(t^2-3t-4=0\\)。"
               "因数分解して \\((t-4)(t+1)=0\\) より \\(t=4,\\ -1\\)。"
               "\\(t=2^x>0\\) だから \\(t=-1\\) は不適で、\\(t=4=2^2\\) より \\(x=2\\)。"
               "\\(t>0\\) の条件を落とすと \\(x=-1\\) を余分に答えてしまう。",
    ),
    dict(
        stem="不等式 \\(\\log_3(x-1)+\\log_3(x+1)<1\\) を解け。",
        unit="指数関数・対数関数",
        correct=("\\(1<x<2\\)", Interval.open(1, 2)),
        distractors=[("\\(x<2\\)", Interval.open(-oo, 2)),
                     ("\\(-2<x<2\\)", Interval.open(-2, 2)),
                     ("\\(1<x<4\\)", Interval.open(1, 4))],
        verify=lambda: solveset((x - 1) * (x + 1) < 3, x, S.Reals).intersect(Interval.open(1, oo)),
        reason="まず真数条件 \\(x-1>0\\) かつ \\(x+1>0\\) から \\(x>1\\)。"
               "左辺をまとめると \\(\\log_3(x-1)(x+1)<1=\\log_3 3\\)、"
               "底 \\(3>1\\) なので \\((x-1)(x+1)<3\\)、すなわち \\(x^2<4\\) より \\(-2<x<2\\)。"
               "真数条件と合わせて \\(1<x<2\\)。"
               "真数条件を忘れると \\(-2<x<2\\) と誤る。",
    ),
    dict(
        stem="\\(\\log_{10}2=0.3010\\)、\\(\\log_{10}3=0.4771\\) とするとき、\\(6^{20}\\) は何桁の整数か。",
        unit="指数関数・対数関数",
        correct=("\\(16\\) 桁", Integer(16)),
        distractors=[("\\(15\\) 桁", Integer(15)), ("\\(17\\) 桁", Integer(17)), ("\\(20\\) 桁", Integer(20))],
        verify=lambda: Integer(len(str(6 ** 20))),
        reason="\\(\\log_{10}6^{20}=20(\\log_{10}2+\\log_{10}3)=20(0.3010+0.4771)=20\\times 0.7781=15.562\\)。"
               "\\(15<15.562<16\\) より \\(10^{15}<6^{20}<10^{16}\\) なので桁数は \\(15+1=16\\) 桁。"
               "\\(+1\\) を忘れて \\(15\\) 桁と答えるミスが多い。",
    ),
  ])


# ---- 第3問 微分・積分 ------------------------------------------------
_f3 = x ** 3 - 3 * x ** 2 - 9 * x + 5

D("math_2b", "数学II・B・C 第3問",
  "太郎さんは 3 次関数 \\(f(x)=x^3-3x^2-9x+5\\) とそのグラフについて調べている。"
  "次の問い(問1〜問5)に答えよ。"
  "各小問に必要な式は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="関数 \\(f(x)=x^3-3x^2-9x+5\\) の極大値を求めよ。",
        unit="微分・積分",
        correct=("\\(10\\)", Integer(10)),
        distractors=[("\\(-22\\)", Integer(-22)), ("\\(5\\)", Integer(5)), ("\\(-1\\)", Integer(-1))],
        verify=lambda: _local_max_value(_f3, x),
        reason="\\(f'(x)=3x^2-6x-9=3(x-3)(x+1)\\)。"
               "\\(f'\\) の符号は \\(x<-1\\) で正、\\(-1<x<3\\) で負、\\(x>3\\) で正だから "
               "\\(x=-1\\) で極大、\\(x=3\\) で極小。"
               "極大値は \\(f(-1)=-1-3+9+5=10\\)。"
               "極小値 \\(f(3)=27-27-27+5=-22\\) と取り違えないこと。",
    ),
    dict(
        stem="曲線 \\(y=x^3-3x^2-9x+5\\) 上の点 \\((1,\\ -6)\\) における接線の方程式を求めよ。",
        unit="微分・積分",
        correct=("\\(y=-12x+6\\)", -12 * x + 6),
        distractors=[("\\(y=-12x-6\\)", -12 * x - 6),
                     ("\\(y=12x-18\\)", 12 * x - 18),
                     ("\\(y=-9x+3\\)", -9 * x + 3)],
        verify=lambda: expand(diff(_f3, x).subs(x, 1) * (x - 1) + _f3.subs(x, 1)),
        reason="\\(f'(x)=3x^2-6x-9\\) より接線の傾きは \\(f'(1)=3-6-9=-12\\)。"
               "点 \\((1,\\ -6)\\) を通るので \\(y-(-6)=-12(x-1)\\)、"
               "整理して \\(y=-12x+6\\)。"
               "\\(-12(x-1)=-12x+12\\) の符号を誤ると \\(y=-12x-6\\) になる。",
    ),
    dict(
        stem="定積分 \\(\\displaystyle\\int_{0}^{2}(3x^2-4x+1)\\,dx\\) の値を求めよ。",
        unit="微分・積分",
        correct=("\\(2\\)", Integer(2)),
        distractors=[("\\(6\\)", Integer(6)), ("\\(4\\)", Integer(4)), ("\\(0\\)", Integer(0))],
        verify=lambda: integrate(3 * x ** 2 - 4 * x + 1, (x, 0, 2)),
        reason="原始関数は \\(x^3-2x^2+x\\)。"
               "\\(\\left[x^3-2x^2+x\\right]_0^2=(8-8+2)-0=2\\)。"
               "\\(-4x\\) の積分を \\(-4x^2\\) (\\(\\div 2\\) を忘れる) とすると \\(-6\\) ずれて誤答になる。",
    ),
    dict(
        stem="放物線 \\(y=x^2-2x\\) と \\(x\\) 軸で囲まれた部分の面積を求めよ。",
        unit="微分・積分",
        correct=("\\(\\dfrac{4}{3}\\)", Rational(4, 3)),
        distractors=[("\\(\\dfrac{8}{3}\\)", Rational(8, 3)), ("\\(\\dfrac{2}{3}\\)", Rational(2, 3)), ("\\(4\\)", Integer(4))],
        verify=lambda: integrate(0 - (x ** 2 - 2 * x), (x, 0, 2)),
        reason="\\(x^2-2x=x(x-2)\\) より \\(x\\) 軸との交点は \\(x=0,\\ 2\\)。"
               "この区間で放物線は \\(x\\) 軸より下にあるので、面積は "
               "\\(\\displaystyle\\int_0^2\\{0-(x^2-2x)\\}dx=\\left[x^2-\\dfrac{x^3}{3}\\right]_0^2"
               "=4-\\dfrac83=\\dfrac43\\)。"
               "上下を逆にすると符号が負になり、絶対値を取らないと誤答になる。"
               "公式 \\(\\dfrac{|a|}{6}(\\beta-\\alpha)^3=\\dfrac16\\cdot 2^3=\\dfrac43\\) でも確認できる。",
    ),
    dict(
        stem="放物線 \\(y=x^2\\) と直線 \\(y=x+2\\) で囲まれた部分の面積を求めよ。",
        unit="微分・積分",
        correct=("\\(\\dfrac{9}{2}\\)", Rational(9, 2)),
        distractors=[("\\(\\dfrac{9}{4}\\)", Rational(9, 4)), ("\\(\\dfrac{27}{2}\\)", Rational(27, 2)), ("\\(\\dfrac{3}{2}\\)", Rational(3, 2))],
        verify=lambda: integrate((x + 2) - x ** 2, (x, -1, 2)),
        reason="交点は \\(x^2=x+2\\)、すなわち \\(x^2-x-2=(x-2)(x+1)=0\\) より \\(x=-1,\\ 2\\)。"
               "この区間では直線が上なので面積は "
               "\\(\\displaystyle\\int_{-1}^{2}\\{(x+2)-x^2\\}dx=\\dfrac92\\)。"
               "公式 \\(\\dfrac{1}{6}(\\beta-\\alpha)^3=\\dfrac16\\cdot 3^3=\\dfrac{27}{6}=\\dfrac92\\) でも一致する。",
    ),
  ])


# ---- 第4問 数列 ------------------------------------------------------
D("math_2b", "数学II・B・C 第4問",
  "花子さんは数列の一般項と和について復習している。次の問い(問1〜問5)に答えよ。"
  "各小問に必要な条件は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="等差数列 \\(\\{a_n\\}\\) が \\(a_3=11\\)、\\(a_7=27\\) を満たすとき、一般項 \\(a_n\\) を求めよ。",
        unit="数列",
        correct=("\\(a_n=4n-1\\)", 4 * n - 1),
        distractors=[("\\(a_n=4n+3\\)", 4 * n + 3),
                     ("\\(a_n=4n-5\\)", 4 * n - 5),
                     ("\\(a_n=3n+2\\)", 3 * n + 2)],
        verify=lambda: (lambda d, a1: expand(a1 + (n - 1) * d))(
            Rational(27 - 11, 7 - 3), Integer(11) - 2 * Rational(27 - 11, 7 - 3)),
        reason="公差を \\(d\\) とすると \\(a_7-a_3=4d=27-11=16\\) より \\(d=4\\)。"
               "\\(a_3=a_1+2d=11\\) から \\(a_1=11-8=3\\)。"
               "よって \\(a_n=3+(n-1)\\cdot 4=4n-1\\)。"
               "検算: \\(a_3=11\\)、\\(a_7=27\\) を満たす。"
               "\\(a_1\\) を \\(11\\) のまま使うと \\(a_n=4n+7\\) のようにずれる。",
    ),
    dict(
        stem="初項 \\(3\\)、公差 \\(4\\) の等差数列について、初項から第 20 項までの和を求めよ。",
        unit="数列",
        correct=("\\(820\\)", Integer(820)),
        distractors=[("\\(800\\)", Integer(800)), ("\\(840\\)", Integer(840)), ("\\(1580\\)", Integer(1580))],
        verify=lambda: summation(3 + (n - 1) * 4, (n, 1, 20)),
        reason="等差数列の和は \\(S_n=\\dfrac{n}{2}\\{2a_1+(n-1)d\\}\\)。"
               "\\(S_{20}=\\dfrac{20}{2}\\{2\\cdot 3+19\\cdot 4\\}=10(6+76)=820\\)。"
               "末項 \\(a_{20}=3+19\\cdot 4=79\\) を使って "
               "\\(S_{20}=\\dfrac{20(3+79)}{2}=820\\) と確認してもよい。"
               "\\((n-1)d\\) を \\(nd\\) とすると \\(840\\) になる。",
    ),
    dict(
        stem="初項 \\(3\\)、公比 \\(2\\) の等比数列について、初項から第 8 項までの和を求めよ。",
        unit="数列",
        correct=("\\(765\\)", Integer(765)),
        distractors=[("\\(768\\)", Integer(768)), ("\\(381\\)", Integer(381)), ("\\(1533\\)", Integer(1533))],
        verify=lambda: summation(3 * 2 ** (n - 1), (n, 1, 8)),
        reason="等比数列の和は \\(S_n=\\dfrac{a_1(r^n-1)}{r-1}\\)。"
               "\\(S_8=\\dfrac{3(2^8-1)}{2-1}=3(256-1)=3\\times 255=765\\)。"
               "第 8 項 \\(a_8=3\\cdot 2^7=384\\) と混同したり、"
               "\\(2^8\\) から \\(1\\) を引き忘れて \\(768\\) とするミスに注意。",
    ),
    dict(
        stem="\\(\\displaystyle\\sum_{k=1}^{n}k(k+2)\\) を \\(n\\) の式で表せ。",
        unit="数列",
        correct=("\\(\\dfrac{n(n+1)(2n+7)}{6}\\)", n * (n + 1) * (2 * n + 7) / 6),
        distractors=[("\\(\\dfrac{n(n+1)(2n+1)}{6}\\)", n * (n + 1) * (2 * n + 1) / 6),
                     ("\\(\\dfrac{n(n+1)(n+2)}{3}\\)", n * (n + 1) * (n + 2) / 3),
                     ("\\(\\dfrac{n(n+1)(2n+7)}{3}\\)", n * (n + 1) * (2 * n + 7) / 3)],
        verify=lambda: simplify(summation(k * (k + 2), (k, 1, n))),
        reason="展開して \\(\\displaystyle\\sum_{k=1}^{n}(k^2+2k)"
               "=\\dfrac{n(n+1)(2n+1)}{6}+2\\cdot\\dfrac{n(n+1)}{2}\\)。"
               "\\(n(n+1)\\) でくくると "
               "\\(n(n+1)\\left\\{\\dfrac{2n+1}{6}+1\\right\\}=\\dfrac{n(n+1)(2n+7)}{6}\\)。"
               "検算: \\(n=1\\) のとき左辺は \\(1\\cdot 3=3\\)、"
               "右辺も \\(\\dfrac{1\\cdot 2\\cdot 9}{6}=3\\) で一致する。"
               "\\(2\\sum k\\) の項を足し忘れると \\(\\dfrac{n(n+1)(2n+1)}{6}\\) のままになる。",
    ),
    dict(
        stem="\\(a_1=3\\)、\\(a_{n+1}=3a_n-4\\) (\\(n=1,2,3,\\dots\\)) で定まる数列 \\(\\{a_n\\}\\) の一般項を求めよ。",
        unit="数列",
        correct=("\\(a_n=3^{n-1}+2\\)", 3 ** (n - 1) + 2),
        distractors=[("\\(a_n=3^{n}+2\\)", 3 ** n + 2),
                     ("\\(a_n=3^{n-1}-2\\)", 3 ** (n - 1) - 2),
                     ("\\(a_n=3^{n-1}+3\\)", 3 ** (n - 1) + 3)],
        verify=lambda: _recurrence_general(),
        reason="特性方程式 \\(\\alpha=3\\alpha-4\\) を解くと \\(\\alpha=2\\)。"
               "漸化式から \\(a_{n+1}-2=3(a_n-2)\\) なので、"
               "\\(\\{a_n-2\\}\\) は初項 \\(a_1-2=1\\)、公比 \\(3\\) の等比数列。"
               "よって \\(a_n-2=3^{n-1}\\)、すなわち \\(a_n=3^{n-1}+2\\)。"
               "検算: \\(a_1=1+2=3\\)、\\(a_2=3+2=5=3\\cdot 3-4\\) で一致する。"
               "指数を \\(n\\) にすると初項が合わなくなる。",
    ),
  ])


def _recurrence_general():
    """a_1=3, a_{n+1}=3a_n-4 を数値展開して 3^{n-1}+2 と一致するか確認するための式を返す。"""
    vals = [Integer(3)]
    for _ in range(9):
        vals.append(3 * vals[-1] - 4)
    cand = 3 ** (n - 1) + 2
    assert all(cand.subs(n, i + 1) == v for i, v in enumerate(vals)), "漸化式の一般項が数値列と不一致"
    return cand


# ---- 第5問 統計的な推測 ----------------------------------------------
D("math_2b", "数学II・B・C 第5問",
  "太郎さんは統計的な推測について復習している。必要に応じて、"
  "標準正規分布に従う確率変数 \\(Z\\) について \\(P(0\\le Z\\le 1)=0.3413\\)、"
  "\\(P(0\\le Z\\le 1.96)=0.4750\\) を用いてよい。次の問い(問1〜問5)に答えよ。"
  "各小問に必要な条件は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="確率変数 \\(X\\) が二項分布 \\(B\\left(180,\\ \\dfrac{1}{3}\\right)\\) に従うとき、"
             "\\(X\\) の平均 (期待値) を求めよ。",
        unit="統計的な推測",
        correct=("\\(60\\)", Integer(60)),
        distractors=[("\\(45\\)", Integer(45)), ("\\(120\\)", Integer(120)), ("\\(30\\)", Integer(30))],
        verify=lambda: Integer(180) * Rational(1, 3),
        reason="二項分布 \\(B(n,p)\\) の平均は \\(np\\)。"
               "\\(180\\times\\dfrac13=60\\)。"
               "\\(1-p=\\dfrac23\\) を掛けると \\(120\\) になるので、どちらを使うか注意する。",
    ),
    dict(
        stem="確率変数 \\(X\\) が二項分布 \\(B\\left(180,\\ \\dfrac{1}{3}\\right)\\) に従うとき、"
             "\\(X\\) の標準偏差を求めよ。",
        unit="統計的な推測",
        correct=("\\(2\\sqrt{10}\\)", 2 * sqrt(10)),
        distractors=[("\\(40\\)", Integer(40)), ("\\(\\sqrt{60}\\)", sqrt(60)), ("\\(4\\sqrt{10}\\)", 4 * sqrt(10))],
        verify=lambda: simplify(sqrt(Integer(180) * Rational(1, 3) * Rational(2, 3))),
        reason="二項分布の分散は \\(np(1-p)=180\\times\\dfrac13\\times\\dfrac23=40\\)。"
               "標準偏差はその平方根で \\(\\sqrt{40}=2\\sqrt{10}\\)。"
               "分散のまま答えると \\(40\\)、\\((1-p)\\) を掛け忘れると \\(\\sqrt{60}\\) になる。",
    ),
    dict(
        stem="母標準偏差が \\(15\\) である母集団から大きさ \\(25\\) の標本を無作為に抽出するとき、"
             "標本平均 \\(\\overline{X}\\) の標準偏差を求めよ。",
        unit="統計的な推測",
        correct=("\\(3\\)", Integer(3)),
        distractors=[("\\(15\\)", Integer(15)), ("\\(0.6\\)", Rational(3, 5)), ("\\(5\\)", Integer(5))],
        verify=lambda: simplify(Integer(15) / sqrt(Integer(25))),
        reason="標本平均の標準偏差 (標準誤差) は \\(\\dfrac{\\sigma}{\\sqrt{n}}\\)。"
               "\\(\\dfrac{15}{\\sqrt{25}}=\\dfrac{15}{5}=3\\)。"
               "\\(n\\) の平方根を取らずに割ると \\(0.6\\) になる。"
               "標本サイズを 4 倍にすると標準誤差は半分になる、という関係も押さえておく。",
    ),
    dict(
        stem="母標準偏差が \\(15\\) の母集団から大きさ \\(25\\) の標本を無作為抽出したところ、"
             "標本平均が \\(52\\) であった。母平均 \\(m\\) に対する信頼度 95% の信頼区間として"
             "正しいものはどれか。必要なら \\(P(0\\le Z\\le 1.96)=0.4750\\) を用いよ。",
        unit="統計的な推測",
        correct=("\\(46.12\\le m\\le 57.88\\)", Tuple(Rational(1153, 25), Rational(1447, 25))),
        distractors=[("\\(49.00\\le m\\le 55.00\\)", Tuple(Integer(49), Integer(55))),
                     ("\\(22.60\\le m\\le 81.40\\)", Tuple(Rational(113, 5), Rational(407, 5))),
                     ("\\(50.04\\le m\\le 53.96\\)", Tuple(Rational(1251, 25), Rational(1349, 25)))],
        verify=lambda: (lambda se: Tuple(Integer(52) - Rational(196, 100) * se,
                                         Integer(52) + Rational(196, 100) * se))(Integer(15) / sqrt(Integer(25))),
        reason="信頼度 95% の信頼区間は "
               "\\(\\overline{X}-1.96\\dfrac{\\sigma}{\\sqrt n}\\le m\\le\\overline{X}+1.96\\dfrac{\\sigma}{\\sqrt n}\\)。"
               "標準誤差は \\(\\dfrac{15}{\\sqrt{25}}=3\\) なので幅は \\(1.96\\times 3=5.88\\)。"
               "よって \\(52\\pm 5.88\\)、すなわち \\(46.12\\le m\\le 57.88\\)。"
               "\\(\\sqrt{n}\\) で割り忘れると \\(52\\pm 29.4\\) と極端に広い区間になる。",
    ),
    dict(
        stem="確率変数 \\(X\\) が正規分布 \\(N(50,\\ 10^2)\\) に従うとき、\\(P(40\\le X\\le 60)\\) を求めよ。"
             "ただし \\(P(0\\le Z\\le 1)=0.3413\\) とする。",
        unit="統計的な推測",
        correct=("\\(0.6826\\)", Rational(6826, 10000)),
        distractors=[("\\(0.3413\\)", Rational(3413, 10000)),
                     ("\\(0.8413\\)", Rational(8413, 10000)),
                     ("\\(0.9544\\)", Rational(9544, 10000))],
        verify=lambda: 2 * Rational(3413, 10000),
        reason="\\(Z=\\dfrac{X-50}{10}\\) と標準化すると、"
               "\\(X=40\\) は \\(Z=-1\\)、\\(X=60\\) は \\(Z=1\\) に対応する。"
               "\\(P(-1\\le Z\\le 1)=2P(0\\le Z\\le 1)=2\\times 0.3413=0.6826\\)。"
               "片側だけの \\(0.3413\\) で止めたり、"
               "\\(P(Z\\le 1)=0.5+0.3413=0.8413\\) と混同しないこと。",
    ),
  ])


# ---- 第6問 ベクトル --------------------------------------------------
D("math_2b", "数学II・B・C 第6問",
  "花子さんはベクトルの計算を復習している。次の問い(問1〜問5)に答えよ。"
  "各小問で扱うベクトルの成分はすべて問題文中に明示してあるので、それぞれ単独で解答できる。",
  [
    dict(
        stem="平面上のベクトル \\(\\vec{a}=(2,\\ -1)\\)、\\(\\vec{b}=(3,\\ 4)\\) について、"
             "内積 \\(\\vec{a}\\cdot\\vec{b}\\) を求めよ。",
        unit="ベクトル",
        correct=("\\(2\\)", Integer(2)),
        distractors=[("\\(10\\)", Integer(10)), ("\\(-2\\)", Integer(-2)), ("\\(6\\)", Integer(6))],
        verify=lambda: Integer(2 * 3 + (-1) * 4),
        reason="成分表示の内積は \\(\\vec{a}\\cdot\\vec{b}=a_1b_1+a_2b_2\\)。"
               "\\(2\\times 3+(-1)\\times 4=6-4=2\\)。"
               "第 2 成分の符号を落とすと \\(6+4=10\\) になる。",
    ),
    dict(
        stem="平面上のベクトル \\(\\vec{a}=(2,\\ -1)\\)、\\(\\vec{b}=(3,\\ 4)\\) のなす角を \\(\\theta\\) とするとき、"
             "\\(\\cos\\theta\\) の値を求めよ。",
        unit="ベクトル",
        correct=("\\(\\dfrac{2\\sqrt{5}}{25}\\)", 2 * sqrt(5) / 25),
        distractors=[("\\(\\dfrac{\\sqrt{5}}{25}\\)", sqrt(5) / 25),
                     ("\\(\\dfrac{2}{25}\\)", Rational(2, 25)),
                     ("\\(\\dfrac{2\\sqrt{5}}{5}\\)", 2 * sqrt(5) / 5)],
        verify=lambda: simplify(Integer(2) / (sqrt(Integer(2) ** 2 + Integer(1) ** 2)
                                              * sqrt(Integer(3) ** 2 + Integer(4) ** 2))),
        reason="\\(\\cos\\theta=\\dfrac{\\vec{a}\\cdot\\vec{b}}{|\\vec{a}||\\vec{b}|}\\)。"
               "\\(\\vec{a}\\cdot\\vec{b}=2\\)、\\(|\\vec{a}|=\\sqrt{4+1}=\\sqrt5\\)、"
               "\\(|\\vec{b}|=\\sqrt{9+16}=5\\) なので "
               "\\(\\cos\\theta=\\dfrac{2}{5\\sqrt5}=\\dfrac{2\\sqrt5}{25}\\)。"
               "分母の有理化を忘れると形が合わず、"
               "\\(|\\vec{b}|\\) を \\(\\sqrt5\\) と取り違えると \\(\\dfrac{2}{5}\\) 系の値になる。",
    ),
    dict(
        stem="平面上のベクトル \\(\\vec{a}=(2,\\ -1)\\)、\\(\\vec{b}=(3,\\ 4)\\) について、"
             "\\(|\\vec{a}+2\\vec{b}|\\) を求めよ。",
        unit="ベクトル",
        correct=("\\(\\sqrt{113}\\)", sqrt(113)),
        distractors=[("\\(\\sqrt{85}\\)", sqrt(85)), ("\\(15\\)", Integer(15)), ("\\(\\sqrt{145}\\)", sqrt(145))],
        verify=lambda: simplify(sqrt((2 + 2 * 3) ** 2 + (-1 + 2 * 4) ** 2)),
        reason="まず成分を計算すると "
               "\\(\\vec{a}+2\\vec{b}=(2+6,\\ -1+8)=(8,\\ 7)\\)。"
               "大きさは \\(\\sqrt{8^2+7^2}=\\sqrt{64+49}=\\sqrt{113}\\)。"
               "\\(|\\vec{a}|+2|\\vec{b}|=\\sqrt5+10\\) のように"
               "「大きさを先に取ってから足す」のは誤り。",
    ),
    dict(
        stem="平面上のベクトル \\(\\vec{a}=(x,\\ 3)\\)、\\(\\vec{b}=(4,\\ -2)\\) が垂直であるとき、"
             "\\(x\\) の値を求めよ。",
        unit="ベクトル",
        correct=("\\(\\dfrac{3}{2}\\)", Rational(3, 2)),
        distractors=[("\\(-\\dfrac{3}{2}\\)", Rational(-3, 2)), ("\\(6\\)", Integer(6)), ("\\(-6\\)", Integer(-6))],
        verify=lambda: list(solveset(Eq(4 * x + 3 * (-2), 0), x, S.Reals))[0],
        reason="2 つのベクトルが垂直 \\(\\iff\\) 内積が \\(0\\)。"
               "\\(\\vec{a}\\cdot\\vec{b}=4x+3\\times(-2)=4x-6=0\\) より \\(x=\\dfrac32\\)。"
               "平行条件 \\(a_1b_2-a_2b_1=0\\) と取り違えると "
               "\\(-2x-12=0\\) から \\(x=-6\\) になってしまう。",
    ),
    dict(
        stem="空間内の 2 点 \\(A(1,\\ 2,\\ 3)\\)、\\(B(3,\\ -1,\\ 4)\\) について、"
             "\\(\\left|\\overrightarrow{AB}\\right|\\) を求めよ。",
        unit="ベクトル",
        correct=("\\(\\sqrt{14}\\)", sqrt(14)),
        distractors=[("\\(\\sqrt{26}\\)", sqrt(26)), ("\\(\\sqrt{6}\\)", sqrt(6)), ("\\(14\\)", Integer(14))],
        verify=lambda: simplify(sqrt((3 - 1) ** 2 + (-1 - 2) ** 2 + (4 - 3) ** 2)),
        reason="\\(\\overrightarrow{AB}=(3-1,\\ -1-2,\\ 4-3)=(2,\\ -3,\\ 1)\\)。"
               "大きさは \\(\\sqrt{2^2+(-3)^2+1^2}=\\sqrt{4+9+1}=\\sqrt{14}\\)。"
               "引く向きを逆にしても大きさは変わらないが、"
               "成分を足し算 \\((4,\\ 1,\\ 7)\\) にすると \\(\\sqrt{66}\\) と全く別の値になる。",
    ),
  ])


# =====================================================================
# 検証 → JSON 組み立て
# =====================================================================

def _answer_positions():
    """全小問の正解位置を md5 順の round-robin で 0..3 に完全均等配分して返す。

    ハッシュ剰余だけだと 11/19/15/15 のように偏る (実測)。順位で割り当てれば必ず等分になり、
    「正解はだいたい 1 番」のような当てずっぽうが効かなくなる。"""
    keys = [(dm["group"], qi)
            for dm in DAIMON for qi in range(len(dm["subqs"]))]
    ranked = sorted(keys, key=lambda kk: hashlib.md5(f'{SOURCE}:{kk[0]}:{kk[1]}'.encode()).hexdigest())
    return {kk: i % 4 for i, kk in enumerate(ranked)}


def build():
    rows = []
    errors = []
    total_sub = 0
    positions = _answer_positions()
    for di, dm in enumerate(DAIMON):
        subs = []
        for qi, sq in enumerate(dm["subqs"]):
            tag = f'{dm["group"]} 問{qi + 1}'
            c_latex, c_val = sq["correct"]

            # (1) 独立計算との一致
            try:
                got = sq["verify"]()
            except Exception as e:  # noqa: BLE001
                errors.append(f'{tag}: verify() が例外 {type(e).__name__}: {e}')
                continue
            if not _eq(got, c_val):
                errors.append(f'{tag}: verify()={got} ≠ correct={c_val}')

            # (2) 誤答が正解と同値でないこと・誤答どうしも重複しないこと
            seen = [c_val]
            for d_latex, d_val in sq["distractors"]:
                if any(_eq(d_val, s) for s in seen):
                    errors.append(f'{tag}: 誤答「{d_latex}」が他の選択肢と同値')
                seen.append(d_val)
            if len(sq["distractors"]) != 3:
                errors.append(f'{tag}: 誤答は 3 個必要 (実際 {len(sq["distractors"])} 個)')

            # (3) 正解位置を md5 順の round-robin で 0..3 に均等配分
            pos = positions[(dm["group"], qi)]
            choices = [d[0] for d in sq["distractors"]]
            choices.insert(pos, c_latex)
            if choices[pos] != c_latex:
                errors.append(f'{tag}: 正解位置の挿入に失敗')

            subs.append({
                "id": f"q{qi + 1}",
                "type": "multiple_choice",
                "stem": sq["stem"],
                "choices": choices,
                "answer": pos,
                "unit": sq["unit"],
                "explanation": f'【単元】{sq["unit"]}。正解は「{c_latex}」。{sq["reason"]}',
            })
            total_sub += 1

        rows.append({
            "exam_id": "rikei",
            "part_key": dm["part_key"],
            "eiken_grade": "kyotsu_rikei",
            "model": MODEL,
            "question_data": {
                "passage": dm["passage"],
                "subject": "数学",
                "univ_simulated": "共通テスト模試",
                "year_simulated": 2026,
                "source": SOURCE,
                "exam_format": True,
                "group": dm["group"],
                "questions": subs,
            },
        })

    if errors:
        print("❌ 検証エラー:")
        for e in errors:
            print("   -", e)
        raise SystemExit(1)

    # 正解位置の分布を確認 (0 番偏り事故の再発防止)
    dist = {0: 0, 1: 0, 2: 0, 3: 0}
    for r in rows:
        for q in r["question_data"]["questions"]:
            dist[q["answer"]] += 1

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"questions": rows, "skip_full": False}, f, ensure_ascii=False, indent=1)

    print(f"✅ 検証 OK: {len(rows)} 大問 / {total_sub} 小問")
    for pk in ("math_1a", "math_2b"):
        cnt = sum(1 for r in rows if r["part_key"] == pk)
        sub = sum(len(r["question_data"]["questions"]) for r in rows if r["part_key"] == pk)
        print(f"   {pk}: {cnt} 大問 / {sub} 小問")
    print(f"   正解位置の分布: {dist}")
    print(f"   → {os.path.relpath(OUT)}")


if __name__ == "__main__":
    build()
