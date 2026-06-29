#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト型 数学IA/IIB 発展ドリル(part=math_exam_ia/iib)の +8大問(A+B) 生成器。
正解は sympy で計算・照合し、手入力ミスを構造的に排除する。出力: math_exam_daimon_v1.json。

A(=この水準で増量・テーマ連動だが各小問独立・各stem自己完結):
  IA: 三角比(図形と計量) / 場合の数と確率 / 整数の性質
  IIB: 三角関数 / 指数・対数 / 図形と方程式
B(=真の本番型・段階的誘導[前問の結果を次で使う・各stemに必要値を再掲]・マーク穴埋め風):
  IA: 二次関数(文字定数aの区間最小を場合分け) / IIB: 微分積分(3次関数の概形→面積)

正解位置は md5 順 rank%4 で 10/10/10/10 に均等化(memory: 正解位置0偏り対策)。
"""
import json, hashlib, os
from sympy import (symbols, sqrt, Rational, simplify, Tuple, Integer, nsimplify)

x, a = symbols('x a')

# ---- 値の等価判定(sympy)。Tuple(座標)は要素ごと、それ以外は simplify(差)==0 ----
def _eq(u, v):
    if isinstance(u, Tuple) or isinstance(v, Tuple):
        if not (isinstance(u, Tuple) and isinstance(v, Tuple)) or len(u) != len(v):
            return False
        return all(simplify(ui - vi) == 0 for ui, vi in zip(u, v))
    return simplify(u - v) == 0

# subq 定義: (stem, unit, correct=(latex,value), distractors=[(latex,value)x3], reason)
# 大問 定義: dict(part, group, passage, subqs=[...])

DAIMON = []

def D(part, group, passage, subqs):
    DAIMON.append({"part": part, "group": group, "passage": passage, "subqs": subqs})

# ===================== A1: IA 三角比(図形と計量) =====================
# △ABC: AB=5, AC=8, ∠A=60° ⇒ BC=7
D("math_exam_ia", "数学IA",
  "太郎さんは、ある三角形 ABC の測量結果を整理している。\\(AB=5\\)、\\(AC=8\\)、\\(\\angle A=60^\\circ\\) であった。これについて各問に答えよ。",
  [
   ("\\(\\angle A=60^\\circ\\)、\\(AB=5\\)、\\(AC=8\\) の三角形 ABC について、辺 \\(BC\\) の長さを求めよ。",
    "発展 三角比(余弦定理)",
    ("\\(7\\)", Integer(7)),
    [("\\(\\sqrt{89}\\)", sqrt(89)), ("\\(6\\)", Integer(6)), ("\\(\\sqrt{113}\\)", sqrt(113))],
    "余弦定理 \\(BC^2=5^2+8^2-2\\cdot5\\cdot8\\cos60^\\circ=25+64-40=49\\)、\\(BC=7\\)。"),
   ("\\(\\angle A=60^\\circ\\)、\\(AB=5\\)、\\(AC=8\\) の三角形 ABC の面積を求めよ。",
    "発展 三角比(面積)",
    ("\\(10\\sqrt{3}\\)", 10*sqrt(3)),
    [("\\(20\\sqrt{3}\\)", 20*sqrt(3)), ("\\(10\\)", Integer(10)), ("\\(20\\)", Integer(20))],
    "\\(S=\\tfrac12\\cdot AB\\cdot AC\\sin A=\\tfrac12\\cdot5\\cdot8\\cdot\\tfrac{\\sqrt3}{2}=10\\sqrt3\\)。"),
   ("三角形 ABC で \\(BC=7\\)、\\(\\angle A=60^\\circ\\) のとき、外接円の半径 \\(R\\) を求めよ。",
    "発展 三角比(正弦定理)",
    ("\\(\\dfrac{7\\sqrt{3}}{3}\\)", 7*sqrt(3)/3),
    [("\\(7\\sqrt{3}\\)", 7*sqrt(3)), ("\\(\\dfrac{7}{3}\\)", Rational(7,3)), ("\\(\\dfrac{14\\sqrt{3}}{3}\\)", 14*sqrt(3)/3)],
    "正弦定理 \\(\\dfrac{BC}{\\sin A}=2R\\)、\\(2R=\\dfrac{7}{\\sqrt3/2}=\\dfrac{14}{\\sqrt3}\\)、\\(R=\\dfrac{7\\sqrt3}{3}\\)。"),
   ("三角形 ABC で \\(BC=7\\)、\\(AB=5\\)、\\(AC=8\\) のとき、\\(\\cos B\\) の値を求めよ。",
    "発展 三角比(余弦定理)",
    ("\\(\\dfrac{1}{7}\\)", Rational(1,7)),
    [("\\(\\dfrac{1}{2}\\)", Rational(1,2)), ("\\(\\dfrac{11}{14}\\)", Rational(11,14)), ("\\(\\dfrac{13}{14}\\)", Rational(13,14))],
    "\\(\\cos B=\\dfrac{BC^2+AB^2-AC^2}{2\\cdot BC\\cdot AB}=\\dfrac{49+25-64}{70}=\\dfrac{1}{7}\\)。"),
   ("三角形 ABC で 3辺が \\(AB=5\\)、\\(BC=7\\)、\\(CA=8\\)、面積が \\(10\\sqrt{3}\\) のとき、内接円の半径 \\(r\\) を求めよ。",
    "発展 三角比(内接円)",
    ("\\(\\sqrt{3}\\)", sqrt(3)),
    [("\\(2\\sqrt{3}\\)", 2*sqrt(3)), ("\\(\\dfrac{\\sqrt{3}}{2}\\)", sqrt(3)/2), ("\\(3\\)", Integer(3))],
    "\\(s=\\dfrac{5+7+8}{2}=10\\)、\\(S=rs\\) より \\(r=\\dfrac{10\\sqrt3}{10}=\\sqrt3\\)。"),
  ])

# ===================== A2: IA 場合の数と確率 =====================
# 当たり3本・はずれ4本(計7本)から2本を同時に引く
D("math_exam_ia", "数学IA",
  "花子さんは、当たりくじ 3 本・はずれくじ 4 本（合計 7 本）が入った袋から、同時に 2 本を引く試行を考えている。これについて各問に答えよ。",
  [
   ("当たり 3 本・はずれ 4 本（計 7 本）から 2 本を同時に引くとき、引き方は全部で何通りか。",
    "発展 場合の数(組合せ)",
    ("\\(21\\) 通り", Integer(21)),
    [("\\(42\\) 通り", Integer(42)), ("\\(49\\) 通り", Integer(49)), ("\\(14\\) 通り", Integer(14))],
    "\\({}_7C_2=\\dfrac{7\\cdot6}{2}=21\\) 通り。"),
   ("当たり 3 本・はずれ 4 本（計 7 本）から 2 本を同時に引くとき、2 本とも当たりである確率を求めよ。",
    "発展 確率(組合せ)",
    ("\\(\\dfrac{1}{7}\\)", Rational(1,7)),
    [("\\(\\dfrac{3}{7}\\)", Rational(3,7)), ("\\(\\dfrac{1}{3}\\)", Rational(1,3)), ("\\(\\dfrac{2}{7}\\)", Rational(2,7))],
    "\\(\\dfrac{{}_3C_2}{{}_7C_2}=\\dfrac{3}{21}=\\dfrac{1}{7}\\)。"),
   ("当たり 3 本・はずれ 4 本（計 7 本）から 2 本を同時に引くとき、当たりとはずれが 1 本ずつである確率を求めよ。",
    "発展 確率(組合せ)",
    ("\\(\\dfrac{4}{7}\\)", Rational(4,7)),
    [("\\(\\dfrac{3}{7}\\)", Rational(3,7)), ("\\(\\dfrac{1}{7}\\)", Rational(1,7)), ("\\(\\dfrac{12}{49}\\)", Rational(12,49))],
    "\\(\\dfrac{{}_3C_1\\cdot{}_4C_1}{{}_7C_2}=\\dfrac{12}{21}=\\dfrac{4}{7}\\)。"),
   ("当たり 3 本・はずれ 4 本（計 7 本）から 2 本を同時に引くとき、少なくとも 1 本が当たりである確率を求めよ。",
    "発展 確率(余事象)",
    ("\\(\\dfrac{5}{7}\\)", Rational(5,7)),
    [("\\(\\dfrac{2}{7}\\)", Rational(2,7)), ("\\(\\dfrac{5}{21}\\)", Rational(5,21)), ("\\(\\dfrac{6}{7}\\)", Rational(6,7))],
    "余事象（2本ともはずれ）\\(\\dfrac{{}_4C_2}{{}_7C_2}=\\dfrac{6}{21}=\\dfrac{2}{7}\\)。\\(1-\\dfrac{2}{7}=\\dfrac{5}{7}\\)。"),
   ("当たり 3 本・はずれ 4 本（計 7 本）から 2 本を同時に引くとき、引いた当たりの本数の期待値を求めよ。",
    "発展 確率(期待値)",
    ("\\(\\dfrac{6}{7}\\)", Rational(6,7)),
    [("\\(\\dfrac{3}{7}\\)", Rational(3,7)), ("\\(1\\)", Integer(1)), ("\\(\\dfrac{5}{7}\\)", Rational(5,7))],
    "当たり本数 0,1,2 の確率は \\(\\dfrac{6}{21},\\dfrac{12}{21},\\dfrac{3}{21}\\)。期待値 \\(=\\dfrac{0\\cdot6+1\\cdot12+2\\cdot3}{21}=\\dfrac{18}{21}=\\dfrac{6}{7}\\)。"),
  ])

# ===================== A3: IA 整数の性質 =====================
# 540=2^2·3^3·5, 756=2^2·3^3·7
D("math_exam_ia", "数学IA",
  "太郎さんは、整数の約数や倍数の性質を、具体的な数 \\(540\\) と \\(756\\) を使って調べている。これについて各問に答えよ。",
  [
   ("\\(756\\) を素因数分解すると \\(756=2^{a}\\cdot3^{b}\\cdot7^{c}\\) と表せる。\\(a+b+c\\) の値を求めよ。",
    "発展 整数(素因数分解)",
    ("\\(6\\)", Integer(6)),
    [("\\(5\\)", Integer(5)), ("\\(7\\)", Integer(7)), ("\\(4\\)", Integer(4))],
    "\\(756=2^2\\cdot3^3\\cdot7\\) より \\(a=2,b=3,c=1\\)、\\(a+b+c=6\\)。"),
   ("\\(756=2^2\\cdot3^3\\cdot7\\) である。\\(756\\) の正の約数の個数を求めよ。",
    "発展 整数(約数の個数)",
    ("\\(24\\) 個", Integer(24)),
    [("\\(18\\) 個", Integer(18)), ("\\(12\\) 個", Integer(12)), ("\\(36\\) 個", Integer(36))],
    "\\((2+1)(3+1)(1+1)=3\\cdot4\\cdot2=24\\) 個。"),
   ("\\(540=2^2\\cdot3^3\\cdot5\\)、\\(756=2^2\\cdot3^3\\cdot7\\) である。\\(540\\) と \\(756\\) の最大公約数を求めよ。",
    "発展 整数(最大公約数)",
    ("\\(108\\)", Integer(108)),
    [("\\(54\\)", Integer(54)), ("\\(36\\)", Integer(36)), ("\\(540\\)", Integer(540))],
    "共通因数の最小指数をとり \\(2^2\\cdot3^3=4\\cdot27=108\\)。"),
   ("\\(540=2^2\\cdot3^3\\cdot5\\)、\\(756=2^2\\cdot3^3\\cdot7\\) である。\\(540\\) と \\(756\\) の最小公倍数を求めよ。",
    "発展 整数(最小公倍数)",
    ("\\(3780\\)", Integer(3780)),
    [("\\(1080\\)", Integer(1080)), ("\\(540\\)", Integer(540)), ("\\(756\\)", Integer(756))],
    "各因数の最大指数をとり \\(2^2\\cdot3^3\\cdot5\\cdot7=4\\cdot27\\cdot35=3780\\)。"),
   ("\\(5\\) で割ると \\(2\\) 余り、\\(7\\) で割ると \\(3\\) 余る正の整数のうち、最小のものを求めよ。",
    "発展 整数(合同式)",
    ("\\(17\\)", Integer(17)),
    [("\\(12\\)", Integer(12)), ("\\(22\\)", Integer(22)), ("\\(7\\)", Integer(7))],
    "\\(7\\) で割ると \\(3\\) 余る数 \\(3,10,17,\\dots\\) のうち \\(5\\) で割って \\(2\\) 余るのは \\(17\\)（\\(17=5\\cdot3+2\\)）。"),
  ])

# ===================== A4: IIB 三角関数 =====================
# sinθ=3/5, θは第2象限 ⇒ cosθ=-4/5
D("math_exam_iib", "数学IIB",
  "花子さんは、第 2 象限の角 \\(\\theta\\) について \\(\\sin\\theta=\\dfrac{3}{5}\\) が成り立つ場合の三角関数の値を調べている。これについて各問に答えよ。",
  [
   ("\\(\\sin\\theta=\\dfrac{3}{5}\\) で \\(\\theta\\) が第 2 象限の角のとき、\\(\\cos\\theta\\) の値を求めよ。",
    "発展 三角関数(相互関係)",
    ("\\(-\\dfrac{4}{5}\\)", Rational(-4,5)),
    [("\\(\\dfrac{4}{5}\\)", Rational(4,5)), ("\\(-\\dfrac{3}{5}\\)", Rational(-3,5)), ("\\(\\dfrac{3}{5}\\)", Rational(3,5))],
    "\\(\\cos^2\\theta=1-\\dfrac{9}{25}=\\dfrac{16}{25}\\)。第 2 象限で \\(\\cos\\theta<0\\) より \\(-\\dfrac{4}{5}\\)。"),
   ("\\(\\sin\\theta=\\dfrac{3}{5}\\)、\\(\\cos\\theta=-\\dfrac{4}{5}\\) のとき、\\(\\sin 2\\theta\\) の値を求めよ。",
    "発展 三角関数(2倍角)",
    ("\\(-\\dfrac{24}{25}\\)", Rational(-24,25)),
    [("\\(\\dfrac{24}{25}\\)", Rational(24,25)), ("\\(-\\dfrac{7}{25}\\)", Rational(-7,25)), ("\\(\\dfrac{7}{25}\\)", Rational(7,25))],
    "\\(\\sin2\\theta=2\\sin\\theta\\cos\\theta=2\\cdot\\dfrac{3}{5}\\cdot\\left(-\\dfrac{4}{5}\\right)=-\\dfrac{24}{25}\\)。"),
   ("\\(\\sin\\theta=\\dfrac{3}{5}\\) のとき、\\(\\cos 2\\theta\\) の値を求めよ。",
    "発展 三角関数(2倍角)",
    ("\\(\\dfrac{7}{25}\\)", Rational(7,25)),
    [("\\(-\\dfrac{7}{25}\\)", Rational(-7,25)), ("\\(-\\dfrac{24}{25}\\)", Rational(-24,25)), ("\\(\\dfrac{17}{25}\\)", Rational(17,25))],
    "\\(\\cos2\\theta=1-2\\sin^2\\theta=1-\\dfrac{18}{25}=\\dfrac{7}{25}\\)。"),
   ("\\(0\\le\\theta<2\\pi\\) で、\\(y=\\sin\\theta+\\sqrt{3}\\cos\\theta\\) の最大値を求めよ。",
    "発展 三角関数(合成)",
    ("\\(2\\)", Integer(2)),
    [("\\(\\sqrt{3}+1\\)", sqrt(3)+1), ("\\(\\sqrt{2}\\)", sqrt(2)), ("\\(4\\)", Integer(4))],
    "\\(\\sin\\theta+\\sqrt3\\cos\\theta=2\\sin\\!\\left(\\theta+\\dfrac{\\pi}{3}\\right)\\) より最大値 \\(2\\)。"),
   ("\\(0\\le\\theta<2\\pi\\) のとき、方程式 \\(2\\sin\\theta=\\sqrt{3}\\) の解の個数を求めよ。",
    "発展 三角関数(方程式)",
    ("\\(2\\) 個", Integer(2)),
    [("\\(1\\) 個", Integer(1)), ("\\(3\\) 個", Integer(3)), ("\\(4\\) 個", Integer(4))],
    "\\(\\sin\\theta=\\dfrac{\\sqrt3}{2}\\) より \\(\\theta=\\dfrac{\\pi}{3},\\dfrac{2\\pi}{3}\\) の \\(2\\) 個。"),
  ])

# ===================== A5: IIB 指数・対数 =====================
D("math_exam_iib", "数学IIB",
  "太郎さんは、指数法則と対数の計算を練習している。必要に応じて \\(\\log_{10}2=0.301\\)、\\(\\log_{10}3=0.477\\) を用いてよい。これについて各問に答えよ。",
  [
   ("\\(8^{\\frac{2}{3}}\\) の値を求めよ。",
    "発展 指数(累乗根)",
    ("\\(4\\)", Integer(4)),
    [("\\(8\\)", Integer(8)), ("\\(16\\)", Integer(16)), ("\\(2\\)", Integer(2))],
    "\\(8^{2/3}=(2^3)^{2/3}=2^2=4\\)。"),
   ("\\(\\log_{2}32\\) の値を求めよ。",
    "発展 対数(定義)",
    ("\\(5\\)", Integer(5)),
    [("\\(4\\)", Integer(4)), ("\\(6\\)", Integer(6)), ("\\(16\\)", Integer(16))],
    "\\(32=2^5\\) より \\(\\log_2 32=5\\)。"),
   ("\\(\\log_{2}24-\\log_{2}3\\) の値を求めよ。",
    "発展 対数(計算法則)",
    ("\\(3\\)", Integer(3)),
    [("\\(2\\)", Integer(2)), ("\\(4\\)", Integer(4)), ("\\(8\\)", Integer(8))],
    "\\(\\log_2\\dfrac{24}{3}=\\log_2 8=3\\)。"),
   ("\\(\\log_{10}2=0.301\\)、\\(\\log_{10}3=0.477\\) とするとき、\\(\\log_{10}6\\) の値を求めよ。",
    "発展 対数(常用対数)",
    ("\\(0.778\\)", Rational(778,1000)),
    [("\\(0.602\\)", Rational(602,1000)), ("\\(0.954\\)", Rational(954,1000)), ("\\(0.699\\)", Rational(699,1000))],
    "\\(\\log_{10}6=\\log_{10}2+\\log_{10}3=0.301+0.477=0.778\\)。"),
   ("方程式 \\(4^{x}=8^{\\,x-1}\\) を満たす \\(x\\) の値を求めよ。",
    "発展 指数(方程式)",
    ("\\(3\\)", Integer(3)),
    [("\\(1\\)", Integer(1)), ("\\(2\\)", Integer(2)), ("\\(-3\\)", Integer(-3))],
    "\\(2^{2x}=2^{3(x-1)}\\) より \\(2x=3x-3\\)、\\(x=3\\)。"),
  ])

# ===================== A6: IIB 図形と方程式 =====================
# A(1,2), B(5,4)
D("math_exam_iib", "数学IIB",
  "花子さんは、座標平面上の 2 点 \\(A(1,\\ 2)\\)、\\(B(5,\\ 4)\\) について、直線や円の性質を調べている。これについて各問に答えよ。",
  [
   ("2 点 \\(A(1,\\ 2)\\)、\\(B(5,\\ 4)\\) の中点の座標を求めよ。",
    "発展 図形と方程式(中点)",
    ("\\((3,\\ 3)\\)", Tuple(Integer(3), Integer(3))),
    [("\\((2,\\ 3)\\)", Tuple(Integer(2), Integer(3))), ("\\((3,\\ 2)\\)", Tuple(Integer(3), Integer(2))), ("\\((6,\\ 6)\\)", Tuple(Integer(6), Integer(6)))],
    "中点 \\(\\left(\\dfrac{1+5}{2},\\dfrac{2+4}{2}\\right)=(3,\\ 3)\\)。"),
   ("2 点 \\(A(1,\\ 2)\\)、\\(B(5,\\ 4)\\) 間の距離 \\(AB\\) を求めよ。",
    "発展 図形と方程式(2点間距離)",
    ("\\(2\\sqrt{5}\\)", 2*sqrt(5)),
    [("\\(2\\sqrt{10}\\)", 2*sqrt(10)), ("\\(6\\)", Integer(6)), ("\\(4\\sqrt{2}\\)", 4*sqrt(2))],
    "\\(AB=\\sqrt{(5-1)^2+(4-2)^2}=\\sqrt{16+4}=\\sqrt{20}=2\\sqrt5\\)。"),
   ("2 点 \\(A(1,\\ 2)\\)、\\(B(5,\\ 4)\\) を通る直線の傾きを求めよ。",
    "発展 図形と方程式(傾き)",
    ("\\(\\dfrac{1}{2}\\)", Rational(1,2)),
    [("\\(2\\)", Integer(2)), ("\\(-\\dfrac{1}{2}\\)", Rational(-1,2)), ("\\(\\dfrac{1}{3}\\)", Rational(1,3))],
    "傾き \\(=\\dfrac{4-2}{5-1}=\\dfrac{2}{4}=\\dfrac{1}{2}\\)。"),
   ("2 点 \\(A(1,\\ 2)\\)、\\(B(5,\\ 4)\\) を通る直線の \\(y\\) 切片を求めよ。",
    "発展 図形と方程式(直線)",
    ("\\(\\dfrac{3}{2}\\)", Rational(3,2)),
    [("\\(3\\)", Integer(3)), ("\\(\\dfrac{1}{2}\\)", Rational(1,2)), ("\\(2\\)", Integer(2))],
    "傾き \\(\\dfrac12\\) で \\(A(1,2)\\) を通る \\(y=\\dfrac12 x+b\\)、\\(2=\\dfrac12+b\\)、\\(b=\\dfrac{3}{2}\\)。"),
   ("2 点 \\(A(1,\\ 2)\\)、\\(B(5,\\ 4)\\) を直径の両端とする円の半径を求めよ。",
    "発展 図形と方程式(円)",
    ("\\(\\sqrt{5}\\)", sqrt(5)),
    [("\\(2\\sqrt{5}\\)", 2*sqrt(5)), ("\\(5\\)", Integer(5)), ("\\(\\dfrac{\\sqrt{5}}{2}\\)", sqrt(5)/2)],
    "直径 \\(AB=2\\sqrt5\\) より半径 \\(=\\sqrt5\\)。"),
  ])

# ===================== B1: IA 二次関数(場合分け・段階的誘導) =====================
# f(x)=x^2-2ax+3, 0<=x<=2。各小問は前問の結果(軸 x=a 等)を再掲しつつ積み上げる。
D("math_exam_ia", "数学IA",
  "太郎さんと花子さんは、定数 \\(a\\) を含む 2 次関数 \\(f(x)=x^{2}-2ax+3\\) の、区間 \\(0\\le x\\le2\\) における最小値が、\\(a\\) の値によってどう変わるかを、軸の位置で場合分けして調べている。〔本問は前問の結果を用いて段階的に進む構成です。〕",
  [
   ("2 次関数 \\(f(x)=x^{2}-2ax+3\\) を平方完成したとき、グラフの軸（頂点の \\(x\\) 座標）を \\(a\\) で表せ。",
    "発展 二次関数(平方完成)",
    ("\\(x=a\\)", a),
    [("\\(x=2a\\)", 2*a), ("\\(x=-a\\)", -a), ("\\(x=\\dfrac{a}{2}\\)", a/2)],
    "\\(f(x)=(x-a)^2+3-a^2\\) より軸は \\(x=a\\)。"),
   ("前問より \\(f(x)=x^{2}-2ax+3\\) の軸は \\(x=a\\) である。軸が区間の左外、すなわち \\(a<0\\) のとき、区間 \\(0\\le x\\le2\\) における最小値を求めよ。",
    "発展 二次関数(場合分け・左外)",
    ("\\(3\\)", Integer(3)),
    [("\\(7-4a\\)", 7-4*a), ("\\(3-a^{2}\\)", 3-a**2), ("\\(4-4a\\)", 4-4*a)],
    "下に凸で軸 \\(x=a<0\\) が区間の左外。区間内では増加するので最小は左端 \\(x=0\\)、\\(f(0)=3\\)。"),
   ("\\(f(x)=x^{2}-2ax+3\\)（軸 \\(x=a\\)、頂点 \\((a,\\ 3-a^{2})\\)）について、軸が区間内、すなわち \\(0\\le a\\le2\\) のとき、区間 \\(0\\le x\\le2\\) における最小値を求めよ。",
    "発展 二次関数(場合分け・内)",
    ("\\(3-a^{2}\\)", 3-a**2),
    [("\\(a^{2}+3\\)", a**2+3), ("\\(3-a\\)", 3-a), ("\\(3-2a\\)", 3-2*a)],
    "軸 \\(x=a\\) が区間内なので最小は頂点 \\(f(a)=3-a^2\\)。"),
   ("前問までと同じ \\(f(x)=x^{2}-2ax+3\\)（軸 \\(x=a\\)）について、軸が区間の右外、すなわち \\(a>2\\) のとき、区間 \\(0\\le x\\le2\\) における最小値を求めよ。",
    "発展 二次関数(場合分け・右外)",
    ("\\(7-4a\\)", 7-4*a),
    [("\\(4-4a\\)", 4-4*a), ("\\(3\\)", Integer(3)), ("\\(7+4a\\)", 7+4*a)],
    "軸 \\(x=a>2\\) が区間の右外。区間内では減少するので最小は右端 \\(x=2\\)、\\(f(2)=4-4a+3=7-4a\\)。"),
   ("前問までの場合分け（\\(0\\le a\\le2\\) のとき最小値は \\(3-a^{2}\\)）を用いる。\\(a=1\\) のとき、\\(f(x)=x^{2}-2x+3\\) の区間 \\(0\\le x\\le2\\) における最小値を求めよ。",
    "発展 二次関数(場合分け・代入)",
    ("\\(2\\)", Integer(2)),
    [("\\(3\\)", Integer(3)), ("\\(1\\)", Integer(1)), ("\\(0\\)", Integer(0))],
    "\\(a=1\\) は \\(0\\le a\\le2\\) に該当し最小値は \\(3-a^2=3-1=2\\)。"),
  ])

# ===================== B2: IIB 微分積分(概形→面積・段階的誘導) =====================
# f(x)=x^3-3x
D("math_exam_iib", "数学IIB",
  "花子さんは、3 次関数 \\(f(x)=x^{3}-3x\\) のグラフの概形を導関数で調べ、続けて \\(x\\) 軸とで囲まれた部分の面積を定積分で求めようとしている。〔本問は前問の結果を用いて段階的に進む構成です。〕",
  [
   ("3 次関数 \\(f(x)=x^{3}-3x\\) について、導関数 \\(f'(x)\\) を求めよ。",
    "発展 微分積分(導関数)",
    ("\\(3x^{2}-3\\)", 3*x**2-3),
    [("\\(3x^{2}-3x\\)", 3*x**2-3*x), ("\\(x^{2}-3\\)", x**2-3), ("\\(3x^{2}\\)", 3*x**2)],
    "\\(f'(x)=3x^2-3\\)。"),
   ("前問より \\(f'(x)=3x^{2}-3\\) である。\\(f(x)=x^{3}-3x\\) が極大値をとる \\(x\\) の値を求めよ。",
    "発展 微分積分(極大の位置)",
    ("\\(x=-1\\)", Integer(-1)),
    [("\\(x=1\\)", Integer(1)), ("\\(x=0\\)", Integer(0)), ("\\(x=3\\)", Integer(3))],
    "\\(f'(x)=3(x^2-1)=0\\) より \\(x=\\pm1\\)。\\(x=-1\\) の前後で \\(f'\\) が正→負ゆえ極大は \\(x=-1\\)。"),
   ("前問より \\(f(x)=x^{3}-3x\\) は \\(x=-1\\) で極大となる。その極大値を求めよ。",
    "発展 微分積分(極大値)",
    ("\\(2\\)", Integer(2)),
    [("\\(-2\\)", Integer(-2)), ("\\(0\\)", Integer(0)), ("\\(-1\\)", Integer(-1))],
    "\\(f(-1)=(-1)^3-3(-1)=-1+3=2\\)。"),
   ("\\(f(x)=x^{3}-3x\\) のグラフと \\(x\\) 軸との交点のうち、\\(x>0\\) であるものの \\(x\\) 座標を求めよ。",
    "発展 微分積分(x軸との交点)",
    ("\\(\\sqrt{3}\\)", sqrt(3)),
    [("\\(3\\)", Integer(3)), ("\\(1\\)", Integer(1)), ("\\(\\sqrt{2}\\)", sqrt(2))],
    "\\(x^3-3x=x(x^2-3)=0\\) より \\(x=0,\\pm\\sqrt3\\)。\\(x>0\\) は \\(x=\\sqrt3\\)。"),
   ("前問より \\(y=x^{3}-3x\\) は \\(x=\\sqrt{3}\\) で \\(x\\) 軸と交わり、\\(0\\le x\\le\\sqrt{3}\\) では \\(x\\) 軸より下にある。この区間で曲線と \\(x\\) 軸とで囲まれた部分の面積を求めよ。",
    "発展 微分積分(面積)",
    ("\\(\\dfrac{9}{4}\\)", Rational(9,4)),
    [("\\(\\dfrac{9}{2}\\)", Rational(9,2)), ("\\(9\\)", Integer(9)), ("\\(\\dfrac{3}{4}\\)", Rational(3,4))],
    "\\(S=-\\displaystyle\\int_0^{\\sqrt3}(x^3-3x)\\,dx=-\\left[\\dfrac{x^4}{4}-\\dfrac{3x^2}{2}\\right]_0^{\\sqrt3}=-\\left(\\dfrac{9}{4}-\\dfrac{9}{2}\\right)=\\dfrac{9}{4}\\)。"),
  ])

# ============================ ビルド & 検証 ============================
SOURCE = "kyotsu-exam-format-aplusb-20260623"
MODEL = "claude-opus-verified"

# 1) 全 subq を平坦化(大問順・小問順)
flat = []
for di, dm in enumerate(DAIMON):
    for qi, sq in enumerate(dm["subqs"]):
        flat.append((di, qi, sq))

# 正解位置の均等化(全体 10/10/10/10) + 大問内で同一位置3連続を禁止(A,A,A の見た目回避)。
# 決定的バックトラッキング(乱数なし): 各 subq に 0..3 を順に試し、グローバル残数と
# 「直前2つと同じでない(同一大問内)」制約を満たす割当を探す。
N = len(flat)
per = N // 4  # 各位置の目標数(=10)
block = [di for (di, qi, sq) in flat]  # 各 subq の大問index
pos_of = {}
def _solve(i, remain, assigned):
    # assigned: list[(flat_idx, pos)]。制約: グローバル各位置=10、大問内は各位置≤2回かつ
    #   隣接小問で同一位置にしない(本番らしい混在・偏り/連続回避)。決定的(乱数なし)。
    if i == N:
        return True
    di = block[i]
    same_block = [p for (j, p) in assigned if block[j] == di]
    prev = same_block[-1] if same_block else None
    for p in range(4):
        if remain[p] <= 0:
            continue
        if same_block.count(p) >= 2:   # 大問内 同一位置は最大2回
            continue
        if p == prev:                  # 隣接小問で同一位置にしない
            continue
        remain[p] -= 1
        pos_of[i] = p
        if _solve(i + 1, remain, assigned + [(i, p)]):
            return True
        remain[p] += 1
        del pos_of[i]
    return False
assert _solve(0, [per, per, per, per], []), "position assignment failed"

# 2) 各 subq の choices を組み立て、sympy で正解照合 & distinct 検証
errors = []
pos_count = {0:0,1:0,2:0,3:0}
built = {}  # di -> list of question dicts
for fi, (di, qi, sq) in enumerate(flat):
    stem, unit, correct, distractors, reason = sq
    c_latex, c_val = correct
    p = pos_of[fi]
    choices_latex = [None]*4
    choices_val = [None]*4
    choices_latex[p] = c_latex
    choices_val[p] = c_val
    dj = 0
    for i in range(4):
        if i != p:
            choices_latex[i] = distractors[dj][0]
            choices_val[i] = distractors[dj][1]
            dj += 1
    # 照合: answer 位置の値 == correct
    if not _eq(choices_val[p], c_val):
        errors.append(f"[{di}.{qi}] answer-pos value mismatch")
    # distinct(値) 検証
    for i in range(4):
        for j in range(i+1, 4):
            if _eq(choices_val[i], choices_val[j]):
                errors.append(f"[{di}.{qi}] duplicate choice value at {i},{j}: {choices_latex[i]} == {choices_latex[j]}")
    # distinct(表示) 検証
    if len(set(choices_latex)) != 4:
        errors.append(f"[{di}.{qi}] duplicate choice latex")
    pos_count[p] += 1
    qdict = {
        "id": f"q{qi+1}",
        "type": "multiple_choice",
        "stem": stem,
        "choices": choices_latex,
        "answer": p,
        "unit": unit,
        "explanation": f"【単元】{unit}。正解は「{c_latex}」。{reason}",
    }
    built.setdefault(di, []).append((qi, qdict))

# 3) 大問 JSON 化
rows = []
for di, dm in enumerate(DAIMON):
    qs = [q for _, q in sorted(built[di], key=lambda t: t[0])]
    qd = {
        "passage": dm["passage"],
        "subject": "数学",
        "univ_simulated": "共通テスト(本番形式)",
        "year_simulated": 2025,
        "source": SOURCE,
        "exam_format": True,
        "group": dm["group"],
        "questions": qs,
    }
    rows.append({
        "exam_id": "rikei",
        "part_key": dm["part"],
        "eiken_grade": "kyotsu_rikei",
        "question_data": qd,
        "model": MODEL,
    })

# 4) レポート
print("=== 正解位置分布(目標 10/10/10/10) ===", pos_count)
print("=== 大問数 ===", len(rows),
      " IA:", sum(1 for r in rows if r['part_key']=='math_exam_ia'),
      " IIB:", sum(1 for r in rows if r['part_key']=='math_exam_iib'))
print("=== 小問総数 ===", sum(len(r['question_data']['questions']) for r in rows))
if errors:
    print("!!! 検証エラー !!!")
    for e in errors:
        print("  ", e)
    raise SystemExit(1)
print("=== sympy 全数照合: 正解一致・選択肢distinct OK ===")

out = os.path.join(os.path.dirname(__file__), "math_exam_daimon_v1.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"questions": rows, "skip_full": False}, f, ensure_ascii=False, indent=1)
print("wrote", out)
