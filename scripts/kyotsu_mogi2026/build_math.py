#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト模試 2026 (数学I・A / 数学II・B・C) の seed JSON 生成器。

対象プール (EXAM_QUESTION_ROTATION と一致必須):
  ("rikei", "math_unit", "kyotsu_rikei")  … 数学 共テ 単元別 (道場ドリル用)

★ これは「単元別ドリル」であって模試ではない。各小問が独立し、公式を 1 つ当てはめれば終わる。
  本番形式 (会話文 + 誘導連鎖) は build_math_exam.py が math_1a/math_2b に作る。
  模試テンプレ MOCK_EXAM_TEMPLATES["kyotsu_math"] が引くのは math_1a/math_2b なので、
  この単元別セットを math_unit に置くことで模試の抽選には混ざらない
  (塾長指摘 2026-08-02「実際の共通模試のレベル・形式になってない」への対応)。

【解説フォーマット (server/main.py の理系生成プロンプト準拠・絶対遵守)】
  「解説は日本語で『考え方→立式→計算→答え→補足』を必ず段階分け (3行以上)」
  同一プールの既存 seed (rikei_kyotsu_math_manual.json 148問) と完全に同じ次の 5 行構成にする:

      方針: 〔どの定理・公式をなぜ選ぶか〕
      立式: 〔その公式に問題の値を当てはめた式〕
      計算: 〔途中式と数値〕
      答え: 〔正答。選択肢のテキストと一致すること〕
      補足: 〔典型的な誤答がどのミスから出るか・検算方法〕

  ★ build 時に 5 セクションの存在と、「答え:」に正答の選択肢テキストが含まれることを機械検査する。
    欠けていれば JSON を書かずに落ちるので、フォーマット違反が本番に流れない。

【正解の作り方 (build_daimon.py と同じ「正解を手入力しない」原則)】
  各小問は correct / distractors を「LaTeX と sympy 値」の組で持ち、さらに verify() で
  独立に再計算した値と照合する。手入力ミスは import 前にここで落ちる。
  - verify() の結果 != correct の値 → AssertionError
  - distractor が correct と同値 (別表記の同一値) → AssertionError
  - 正解位置は md5 順の round-robin で 0..3 に完全均等配分

出力: seed-data/kyotsu_mogi2026_math_manual.json
実行: python3 scripts/kyotsu_mogi2026/build_math.py
"""
import json
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import answer_positions   # noqa: E402  正解位置の配置

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

# 解説の必須セクション (順序どおりに並んでいること)
SECTIONS = ('方針', '立式', '計算', '答え', '補足')

DAIMON = []


def D(part_key, group, passage, subqs):
    DAIMON.append({"part_key": part_key, "group": group, "passage": passage, "subqs": subqs})


def Q(stem, unit, correct, distractors, verify, hoshin, rishiki, keisan, kotae, hosoku):
    """小問 1 つ。解説は 5 セクションを個別のフィールドで持たせ、組み立て時に検査する。"""
    return dict(stem=stem, unit=unit, correct=correct, distractors=distractors, verify=verify,
                hoshin=hoshin, rishiki=rishiki, keisan=keisan, kotae=kotae, hosoku=hosoku)


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


def _menelaus_af_fc():
    """座標で直接計算して AF:FC を出す (メネラウスの検算)。"""
    ax, ay = Rational(0), Rational(0)
    bx, by = Rational(1), Rational(0)
    cx, cy = Rational(0), Rational(1)
    dx, dy = ax + Rational(2, 3) * (bx - ax), ay + Rational(2, 3) * (by - ay)   # AD:DB = 2:1
    ex, ey = bx + Rational(3, 5) * (cx - bx), by + Rational(3, 5) * (cy - by)   # BE:EC = 3:2
    s = (ax - dx) / (ex - dx)                                                   # 直線 DE と AC (x=0) の交点
    fy = dy + s * (ey - dy)
    return Tuple(simplify(Abs(fy - ay) / Abs(fy - cy)), Integer(1))


def _recurrence_general():
    """a_1=3, a_{n+1}=3a_n-4 を数値展開して 3^{n-1}+2 と一致するか確認する。"""
    vals = [Integer(3)]
    for _ in range(9):
        vals.append(3 * vals[-1] - 4)
    cand = 3 ** (n - 1) + 2
    assert all(cand.subs(n, i + 1) == v for i, v in enumerate(vals)), "漸化式の一般項が数値列と不一致"
    return cand


# =====================================================================
# 数学I・A  (part_key = math_1a)
# =====================================================================

# ---- 第1問 数と式・集合と命題 ---------------------------------------
D("math_unit", "数学I・A 第1問",
  "太郎さんは、式の計算と論証の復習をしている。次の問い(問1〜問5)に答えよ。"
  "各小問は独立しており、それぞれ単独で解答できる。文字はすべて実数を表すものとする。",
  [
    Q("式 \\((3x-2y)^2-(3x+2y)(3x-2y)\\) を展開して整理したものとして正しいものはどれか。",
      "数と式",
      ("\\(-12xy+8y^2\\)", expand((3 * x - 2 * y) ** 2 - (3 * x + 2 * y) * (3 * x - 2 * y))),
      [("\\(12xy+8y^2\\)", 12 * x * y + 8 * y ** 2),
       ("\\(-12xy\\)", -12 * x * y),
       ("\\(18x^2-12xy+8y^2\\)", 18 * x ** 2 - 12 * x * y + 8 * y ** 2)],
      lambda: expand((9 * x ** 2 - 12 * x * y + 4 * y ** 2) - (9 * x ** 2 - 4 * y ** 2)),
      hoshin="\\((a-b)^2\\) の展開公式と \\((a+b)(a-b)=a^2-b^2\\) を別々に使い、最後に差をとる。",
      rishiki="\\((3x-2y)^2=9x^2-12xy+4y^2\\)、\\((3x+2y)(3x-2y)=9x^2-4y^2\\)。",
      keisan="\\((9x^2-12xy+4y^2)-(9x^2-4y^2)=9x^2-12xy+4y^2-9x^2+4y^2=-12xy+8y^2\\)。",
      kotae="\\(-12xy+8y^2\\)。",
      hosoku="後ろのカッコを引くとき \\(-4y^2\\) の符号を反転し忘れると \\(4y^2-4y^2=0\\) となり "
             "\\(-12xy\\) と誤る。カッコの前がマイナスなら中身の全項の符号を変える。"),
    Q("二次式 \\(6x^2+x-12\\) を因数分解したものとして正しいものはどれか。",
      "数と式",
      ("\\((2x+3)(3x-4)\\)", expand((2 * x + 3) * (3 * x - 4))),
      [("\\((2x-3)(3x+4)\\)", expand((2 * x - 3) * (3 * x + 4))),
       ("\\((6x-3)(x+4)\\)", expand((6 * x - 3) * (x + 4))),
       ("\\((3x+2)(2x-6)\\)", expand((3 * x + 2) * (2 * x - 6)))],
      lambda: expand(factor(6 * x ** 2 + x - 12)),
      hoshin="\\(ax^2+bx+c\\) のたすき掛け。\\(6=2\\times3\\)、定数項 \\(-12\\) の組合せで中央項 \\(+x\\) を作る。",
      rishiki="\\((2x+m)(3x+n)\\) とおくと \\(mn=-12\\)、\\(2n+3m=1\\)。",
      keisan="\\(m=3,\\ n=-4\\) とすると \\(mn=-12\\)、\\(2(-4)+3(3)=-8+9=1\\) で条件に一致する。",
      kotae="\\((2x+3)(3x-4)\\)。",
      hosoku="展開して \\(6x^2-8x+9x-12=6x^2+x-12\\) と検算できる。"
             "符号を入れ替えた \\((2x-3)(3x+4)\\) は \\(6x^2-x-12\\) となり中央項の符号が逆になる。"),
    Q("実数 \\(a,\\ b\\) が \\(a+b=4\\)、\\(ab=2\\) を満たすとき、\\(a^3+b^3\\) の値はいくらか。",
      "数と式",
      ("\\(40\\)", Integer(40)),
      [("\\(64\\)", Integer(64)), ("\\(56\\)", Integer(56)), ("\\(52\\)", Integer(52))],
      lambda: Integer(4) ** 3 - 3 * Integer(2) * Integer(4),
      hoshin="基本対称式 \\(a+b,\\ ab\\) だけで表せる形に変形する。\\(a^3+b^3=(a+b)^3-3ab(a+b)\\)。",
      rishiki="\\((a+b)^3-3ab(a+b)\\) に \\(a+b=4,\\ ab=2\\) を代入する。",
      keisan="\\(4^3-3\\cdot2\\cdot4=64-24=40\\)。",
      kotae="\\(40\\)。",
      hosoku="\\(3ab(a+b)\\) を引き忘れると \\(64\\)、\\(ab\\) だけ引くと \\(56\\)。"
             "\\(a^3+b^3=(a+b)(a^2-ab+b^2)\\) からでも \\(a^2+b^2=16-4=12\\) より "
             "\\(4\\times(12-2)=40\\) と確認できる。"),
    Q("不等式 \\(|2x-5|<3\\) を満たす整数 \\(x\\) は何個あるか。",
      "数と式",
      ("\\(2\\) 個", Integer(2)),
      [("\\(3\\) 個", Integer(3)), ("\\(4\\) 個", Integer(4)), ("\\(1\\) 個", Integer(1))],
      lambda: Integer(len([i for i in range(-20, 21) if abs(2 * i - 5) < 3])),
      hoshin="\\(|A|<k\\ (k>0)\\) は \\(-k<A<k\\) と、絶対値を外した 1 つの連立不等式に書き直す。",
      rishiki="\\(-3<2x-5<3\\)。",
      keisan="各辺に \\(5\\) を足して \\(2<2x<8\\)、\\(2\\) で割って \\(1<x<4\\)。"
             "この範囲の整数は \\(x=2,\\ 3\\)。",
      kotae="\\(2\\) 個。",
      hosoku="等号を含まないので端点 \\(x=1,\\ 4\\) は入らない。含めると \\(4\\) 個と誤る。"),
    Q("実数 \\(x\\) について、条件「\\(x^2=9\\)」は条件「\\(x=3\\)」であるための何条件か。",
      "集合と命題",
      ("必要条件であるが十分条件でない", "必要"),
      [("十分条件であるが必要条件でない", "十分"),
       ("必要十分条件", "同値"),
       ("必要条件でも十分条件でもない", "無関係")],
      lambda: _condition_label(solveset(Eq(x ** 2, 9), x, S.Reals),
                              solveset(Eq(x, 3), x, S.Reals)),
      hoshin="命題「\\(p\\Rightarrow q\\)」と逆「\\(q\\Rightarrow p\\)」の真偽を別々に調べる。",
      rishiki="\\(p\\) は \\(x^2=9\\) すなわち \\(x=3\\) または \\(x=-3\\)、\\(q\\) は \\(x=3\\)。",
      keisan="\\(p\\Rightarrow q\\) は反例 \\(x=-3\\) があり偽。"
             "逆 \\(q\\Rightarrow p\\) は \\(x=3\\) なら \\(x^2=9\\) となり真。",
      kotae="逆だけが真なので \\(p\\) は「必要条件であるが十分条件でない」。",
      hosoku="解集合で見ると \\(\\{-3,3\\}\\supset\\{3\\}\\) で \\(p\\) の集合の方が広い。"
             "範囲の広い側が必要条件になる、と覚えるとよい。"),
  ])


# ---- 第2問 図形と計量 -----------------------------------------------
# 三角形 ABC: AB=6, AC=10, ∠A=120° ⇒ BC=14, S=15√3, R=14√3/3, r=√3, cosB=11/14
_c, _b, _cosA = Integer(6), Integer(10), Rational(-1, 2)
_a = sqrt(_b ** 2 + _c ** 2 - 2 * _b * _c * _cosA)
_S = Rational(1, 2) * _b * _c * sqrt(1 - _cosA ** 2)

D("math_unit", "数学I・A 第2問",
  "花子さんは、校庭にある三角形の花壇 ABC を測量した。測量の結果、"
  "\\(AB=6\\ \\mathrm{m}\\)、\\(AC=10\\ \\mathrm{m}\\)、\\(\\angle A=120^\\circ\\) であることが分かった。"
  "この花壇について次の問い(問1〜問5)に答えよ。"
  "各小問に必要な値は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    Q("\\(AB=6\\)、\\(AC=10\\)、\\(\\angle A=120^\\circ\\) の三角形 ABC について、辺 \\(BC\\) の長さを求めよ。",
      "図形と計量",
      ("\\(14\\)", Integer(14)),
      [("\\(2\\sqrt{19}\\)", 2 * sqrt(19)), ("\\(4\\sqrt{6}\\)", 4 * sqrt(6)), ("\\(16\\)", Integer(16))],
      lambda: simplify(_a),
      hoshin="2 辺とその間の角が分かっているので、余弦定理で残りの 1 辺を求める。",
      rishiki="\\(BC^2=AB^2+AC^2-2\\cdot AB\\cdot AC\\cos A=6^2+10^2-2\\cdot6\\cdot10\\cos120^\\circ\\)。",
      keisan="\\(\\cos120^\\circ=-\\dfrac12\\) だから \\(BC^2=36+100+60=196\\)、\\(BC=14\\)。",
      kotae="\\(14\\)。",
      hosoku="\\(\\cos120^\\circ\\) を \\(+\\dfrac12\\) とすると \\(BC^2=76\\)、\\(BC=2\\sqrt{19}\\) になる。"
             "鈍角の余弦は負であることを必ず確認する。"),
    Q("\\(AB=6\\)、\\(AC=10\\)、\\(\\angle A=120^\\circ\\) の三角形 ABC の面積を求めよ。",
      "図形と計量",
      ("\\(15\\sqrt{3}\\)", 15 * sqrt(3)),
      [("\\(30\\sqrt{3}\\)", 30 * sqrt(3)), ("\\(15\\)", Integer(15)), ("\\(30\\)", Integer(30))],
      lambda: simplify(_S),
      hoshin="2 辺とその間の角が分かっているので、面積公式 \\(S=\\dfrac12ab\\sin C\\) を使う。",
      rishiki="\\(S=\\dfrac12\\cdot AB\\cdot AC\\sin A=\\dfrac12\\cdot6\\cdot10\\sin120^\\circ\\)。",
      keisan="\\(\\sin120^\\circ=\\dfrac{\\sqrt3}{2}\\) だから "
             "\\(S=\\dfrac12\\cdot6\\cdot10\\cdot\\dfrac{\\sqrt3}{2}=15\\sqrt3\\)。",
      kotae="\\(15\\sqrt{3}\\)。",
      hosoku="\\(\\dfrac12\\) を掛け忘れると \\(30\\sqrt3\\)。"
             "\\(\\sin120^\\circ=\\sin60^\\circ\\) であり、鈍角でも正弦は正である点に注意。"),
    Q("三角形 ABC において \\(BC=14\\)、\\(\\angle A=120^\\circ\\) であるとき、外接円の半径 \\(R\\) を求めよ。",
      "図形と計量",
      ("\\(\\dfrac{14\\sqrt{3}}{3}\\)", Rational(14, 3) * sqrt(3)),
      [("\\(\\dfrac{28\\sqrt{3}}{3}\\)", Rational(28, 3) * sqrt(3)),
       ("\\(\\dfrac{7\\sqrt{3}}{3}\\)", Rational(7, 3) * sqrt(3)),
       ("\\(7\\sqrt{3}\\)", 7 * sqrt(3))],
      lambda: simplify(Integer(14) / (2 * sqrt(3) / 2)),
      hoshin="1 辺とその対角が分かっているので、正弦定理 \\(\\dfrac{a}{\\sin A}=2R\\) を使う。",
      rishiki="\\(\\dfrac{BC}{\\sin A}=2R\\)、すなわち \\(\\dfrac{14}{\\sin120^\\circ}=2R\\)。",
      keisan="\\(\\sin120^\\circ=\\dfrac{\\sqrt3}{2}\\) より \\(2R=\\dfrac{14}{\\sqrt3/2}=\\dfrac{28}{\\sqrt3}\\)、"
             "\\(R=\\dfrac{14}{\\sqrt3}=\\dfrac{14\\sqrt3}{3}\\)。",
      kotae="\\(\\dfrac{14\\sqrt{3}}{3}\\)。",
      hosoku="\\(2R\\) をそのまま答えると \\(\\dfrac{28\\sqrt3}{3}\\)。"
             "分母に根号を残さず有理化してから選択肢と照合する。"),
    Q("三角形 ABC において \\(AB=6\\)、\\(BC=14\\)、\\(CA=10\\)、面積が \\(15\\sqrt{3}\\) であるとき、"
      "内接円の半径 \\(r\\) を求めよ。",
      "図形と計量",
      ("\\(\\sqrt{3}\\)", sqrt(3)),
      [("\\(\\dfrac{\\sqrt{3}}{2}\\)", sqrt(3) / 2),
       ("\\(2\\sqrt{3}\\)", 2 * sqrt(3)),
       ("\\(\\dfrac{15\\sqrt{3}}{14}\\)", Rational(15, 14) * sqrt(3))],
      lambda: simplify(_S / (Rational(1, 2) * (14 + 6 + 10))),
      hoshin="面積と周の長さを結ぶ公式 \\(S=rs\\) (\\(s\\) は周の半分) を使う。",
      rishiki="\\(s=\\dfrac{AB+BC+CA}{2}=\\dfrac{6+14+10}{2}\\)、\\(r=\\dfrac{S}{s}\\)。",
      keisan="\\(s=15\\)、\\(S=15\\sqrt3\\) だから \\(r=\\dfrac{15\\sqrt3}{15}=\\sqrt3\\)。",
      kotae="\\(\\sqrt{3}\\)。",
      hosoku="\\(s\\) を周の長さ \\(30\\) のまま使うと \\(\\dfrac{\\sqrt3}{2}\\) と半分になる。"
             "\\(s\\) は必ず「周の半分」。"),
    Q("三角形 ABC において \\(AB=6\\)、\\(BC=14\\)、\\(CA=10\\) であるとき、\\(\\cos B\\) の値を求めよ。",
      "図形と計量",
      ("\\(\\dfrac{11}{14}\\)", Rational(11, 14)),
      [("\\(\\dfrac{13}{14}\\)", Rational(13, 14)),
       ("\\(\\dfrac{11}{12}\\)", Rational(11, 12)),
       ("\\(-\\dfrac{1}{2}\\)", Rational(-1, 2))],
      lambda: simplify((Integer(14) ** 2 + Integer(6) ** 2 - Integer(10) ** 2) / (2 * 14 * 6)),
      hoshin="3 辺が分かっているので、余弦定理を角 \\(B\\) について解いた形で使う。",
      rishiki="\\(\\cos B=\\dfrac{BC^2+AB^2-CA^2}{2\\cdot BC\\cdot AB}\\)。"
              "角 \\(B\\) をはさむ辺は \\(BC=14,\\ AB=6\\)、向かい合う辺は \\(CA=10\\)。",
      keisan="\\(\\cos B=\\dfrac{196+36-100}{2\\cdot14\\cdot6}=\\dfrac{132}{168}=\\dfrac{11}{14}\\)。",
      kotae="\\(\\dfrac{11}{14}\\)。",
      hosoku="向かい合う辺を取り違えて \\(6^2\\) を引くと \\(\\dfrac{13}{14}\\)。"
             "「引くのは対辺の 2 乗」と固定して覚える。"),
  ])


# ---- 第3問 二次関数 --------------------------------------------------
_f2 = 2 * x ** 2 - 8 * x + 5

D("math_unit", "数学I・A 第3問",
  "太郎さんは二次関数 \\(y=2x^2-8x+5\\) のグラフとその応用について調べている。"
  "次の問い(問1〜問5)に答えよ。各小問に必要な式や条件は問題文中に再掲してあるので、"
  "それぞれ単独で解答できる。",
  [
    Q("二次関数 \\(y=2x^2-8x+5\\) のグラフの頂点の座標を求めよ。",
      "二次関数",
      ("\\((2,\\ -3)\\)", Tuple(Integer(2), Integer(-3))),
      [("\\((2,\\ 3)\\)", Tuple(Integer(2), Integer(3))),
       ("\\((-2,\\ -3)\\)", Tuple(Integer(-2), Integer(-3))),
       ("\\((4,\\ -3)\\)", Tuple(Integer(4), Integer(-3)))],
      lambda: Tuple(Integer(2), _f2.subs(x, 2)),
      hoshin="平方完成して \\(y=a(x-p)^2+q\\) の形にすれば、頂点はそのまま \\((p,\\ q)\\)。",
      rishiki="\\(y=2x^2-8x+5=2(x^2-4x)+5\\)。",
      keisan="\\(x^2-4x=(x-2)^2-4\\) だから "
             "\\(y=2\\{(x-2)^2-4\\}+5=2(x-2)^2-8+5=2(x-2)^2-3\\)。",
      kotae="\\((2,\\ -3)\\)。",
      hosoku="\\(2\\) でくくった分 \\(2\\times(-4)=-8\\) を戻し忘れると \\(y\\) 座標を \\(3\\) や \\(1\\) と誤る。"),
    Q("二次関数 \\(y=2x^2-8x+5\\) の \\(0\\le x\\le 3\\) における最小値を求めよ。",
      "二次関数",
      ("\\(-3\\)", Integer(-3)),
      [("\\(-1\\)", Integer(-1)), ("\\(5\\)", Integer(5)), ("\\(0\\)", Integer(0))],
      lambda: min(_f2.subs(x, Rational(i, 20)) for i in range(0, 61)),
      hoshin="下に凸の放物線では、頂点が区間の内部にあるかどうかで最小値の場所が決まる。まず頂点を出す。",
      rishiki="平方完成すると \\(y=2(x-2)^2-3\\) で頂点は \\((2,\\ -3)\\)。"
              "区間は \\(0\\le x\\le3\\) で、\\(x=2\\) はその内部にある。",
      keisan="頂点が区間内なので最小値は頂点の \\(y\\) 座標 \\(-3\\)。"
             "参考に端点は \\(f(0)=5\\)、\\(f(3)=18-24+5=-1\\)。",
      kotae="\\(-3\\)。",
      hosoku="端点だけを比べると \\(-1\\) を選んでしまう。"
             "頂点が区間に入るかどうかを必ず先に確認する。"),
    Q("二次方程式 \\(x^2-2(k+1)x+k^2+3=0\\) が異なる \\(2\\) つの実数解をもつような定数 \\(k\\) の値の範囲を求めよ。",
      "二次関数",
      ("\\(k>1\\)", Interval.open(1, oo)),
      [("\\(k<1\\)", Interval.open(-oo, 1)),
       ("\\(k\\ge 1\\)", Interval(1, oo)),
       ("\\(k>-1\\)", Interval.open(-1, oo))],
      lambda: solveset((k + 1) ** 2 - (k ** 2 + 3) > 0, k, S.Reals),
      hoshin="異なる 2 実数解の条件は判別式 \\(D>0\\)。\\(x\\) の係数が偶数なので \\(D/4\\) を使う。",
      rishiki="\\(D/4=(k+1)^2-1\\cdot(k^2+3)\\)。",
      keisan="\\((k^2+2k+1)-(k^2+3)=2k-2\\)。\\(2k-2>0\\) より \\(k>1\\)。",
      kotae="\\(k>1\\)。",
      hosoku="\\(D/4\\ge0\\) は重解を含むので不適。等号を入れると \\(k\\ge1\\) と誤る。"),
    Q("二次不等式 \\(x^2-5x+6>0\\) を解け。",
      "二次関数",
      ("\\(x<2\\) または \\(x>3\\)", Union(Interval.open(-oo, 2), Interval.open(3, oo))),
      [("\\(2<x<3\\)", Interval.open(2, 3)),
       ("\\(x\\le 2\\) または \\(x\\ge 3\\)", Union(Interval(-oo, 2), Interval(3, oo))),
       ("すべての実数", S.Reals)],
      lambda: solveset(x ** 2 - 5 * x + 6 > 0, x, S.Reals),
      hoshin="因数分解し、下に凸の放物線が \\(x\\) 軸のどちら側にあるかで判断する。",
      rishiki="\\(x^2-5x+6=(x-2)(x-3)>0\\)。",
      keisan="\\(x\\) 軸との交点は \\(x=2,\\ 3\\)。下に凸なので、値が正になるのは 2 解の外側。",
      kotae="\\(x<2\\) または \\(x>3\\)。",
      hosoku="\\(>0\\) は外側、\\(<0\\) は内側。不等号の向きを取り違えると \\(2<x<3\\) になる。"),
    Q("二次関数 \\(y=2x^2-8x+5\\) のグラフを、\\(x\\) 軸方向に \\(-1\\)、\\(y\\) 軸方向に \\(4\\) だけ"
      "平行移動して得られるグラフの頂点の座標を求めよ。",
      "二次関数",
      ("\\((1,\\ 1)\\)", Tuple(Integer(1), Integer(1))),
      [("\\((3,\\ 1)\\)", Tuple(Integer(3), Integer(1))),
       ("\\((1,\\ -7)\\)", Tuple(Integer(1), Integer(-7))),
       ("\\((3,\\ -7)\\)", Tuple(Integer(3), Integer(-7)))],
      lambda: Tuple(Integer(2) + Integer(-1), _f2.subs(x, 2) + Integer(4)),
      hoshin="平行移動はグラフ全体の移動なので、頂点 1 点の移動として捉えると速い。",
      rishiki="もとの頂点は \\((2,\\ -3)\\)。これを \\(x\\) 方向に \\(-1\\)、\\(y\\) 方向に \\(+4\\) 動かす。",
      keisan="\\((2+(-1),\\ -3+4)=(1,\\ 1)\\)。",
      kotae="\\((1,\\ 1)\\)。",
      hosoku="移動量はそのまま足す。\\(x\\) 方向の符号を逆にすると \\((3,\\ 1)\\) になる。"
             "式で \\(y=2(x+1)^2-8(x+1)+5+4\\) を平方完成しても同じ結果になる。"),
  ])


# ---- 第4問 データの分析 ----------------------------------------------
_scores = [4, 6, 7, 9, 9]
_mean = Rational(sum(_scores), len(_scores))
_var = Rational(sum((Integer(s) - _mean) ** 2 for s in _scores), len(_scores))

D("math_unit", "数学I・A 第4問",
  "あるクラスで 10 点満点の小テストを行い、生徒 5 人の得点を小さい順に並べたところ、"
  "次のようになった。\n\n"
  "  得点: 4, 6, 7, 9, 9 (単位は点)\n\n"
  "このデータについて次の問い(問1〜問5)に答えよ。"
  "各小問に必要なデータや値は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    Q("得点が 4, 6, 7, 9, 9 の 5 個のデータについて、平均値を求めよ。",
      "データの分析",
      ("\\(7\\) 点", Integer(7)),
      [("\\(6.8\\) 点", Rational(34, 5)), ("\\(7.5\\) 点", Rational(15, 2)), ("\\(6\\) 点", Integer(6))],
      lambda: Rational(sum(_scores), 5),
      hoshin="平均値は総和をデータの個数で割る。",
      rishiki="\\(\\bar{x}=\\dfrac{4+6+7+9+9}{5}\\)。",
      keisan="\\(\\dfrac{35}{5}=7\\)。",
      kotae="\\(7\\) 点。",
      hosoku="最頻値 \\(9\\) 点や中央値と混同しないこと。平均は「ならした値」で、"
             "データの中に存在しない値になることもある。"),
    Q("得点が 4, 6, 7, 9, 9 の 5 個のデータについて、分散を求めよ。ただし平均値は \\(7\\) 点である。",
      "データの分析",
      ("\\(3.6\\)", Rational(18, 5)),
      [("\\(4.5\\)", Rational(9, 2)), ("\\(3.2\\)", Rational(16, 5)), ("\\(2.6\\)", Rational(13, 5))],
      lambda: Rational(sum((s - 7) ** 2 for s in _scores), 5),
      hoshin="分散は偏差 (各データ − 平均) の 2 乗の平均。",
      rishiki="\\(s^2=\\dfrac{(4-7)^2+(6-7)^2+(7-7)^2+(9-7)^2+(9-7)^2}{5}\\)。",
      keisan="偏差は \\(-3,\\ -1,\\ 0,\\ 2,\\ 2\\)。2 乗の和は \\(9+1+0+4+4=18\\)、"
             "\\(\\dfrac{18}{5}=3.6\\)。",
      kotae="\\(3.6\\)。",
      hosoku="\\(n-1=4\\) で割ると \\(4.5\\) になる。共通テストの分散はデータの個数 \\(n\\) で割る。"),
    Q("得点が 4, 6, 7, 9, 9 の 5 個のデータについて、中央値 (メジアン) を求めよ。",
      "データの分析",
      ("\\(7\\) 点", Integer(7)),
      [("\\(6\\) 点", Integer(6)), ("\\(7.5\\) 点", Rational(15, 2)), ("\\(9\\) 点", Integer(9))],
      lambda: Integer(sorted(_scores)[len(_scores) // 2]),
      hoshin="中央値は小さい順に並べたときの真ん中の値。個数が奇数なら中央のちょうど 1 個。",
      rishiki="データは 4, 6, 7, 9, 9 と既に昇順で、個数は 5 個 (奇数)。",
      keisan="真ん中は 3 番目の値なので \\(7\\)。",
      kotae="\\(7\\) 点。",
      hosoku="最頻値は \\(9\\) 点で別物。個数が偶数のときは中央 2 個の平均をとる。"),
    Q("平均値 \\(7\\)、分散 \\(3.6\\) のデータ \\(x\\) に対し、\\(u=2x+3\\) で新しい変量 \\(u\\) をつくる。"
      "このとき \\(u\\) の平均値と分散の組として正しいものはどれか。",
      "データの分析",
      ("平均 \\(17\\)、分散 \\(14.4\\)", Tuple(Integer(17), Rational(72, 5))),
      [("平均 \\(17\\)、分散 \\(7.2\\)", Tuple(Integer(17), Rational(36, 5))),
       ("平均 \\(14\\)、分散 \\(14.4\\)", Tuple(Integer(14), Rational(72, 5))),
       ("平均 \\(17\\)、分散 \\(3.6\\)", Tuple(Integer(17), Rational(18, 5)))],
      lambda: (lambda us, m: Tuple(m, Rational(sum((Integer(u) - m) ** 2 for u in us), len(us))))(
          [2 * s + 3 for s in _scores], Rational(sum(2 * s + 3 for s in _scores), len(_scores))),
      hoshin="\\(u=ax+b\\) のとき、平均は \\(a\\bar{x}+b\\)、分散は \\(a^2\\) 倍になる。",
      rishiki="\\(a=2,\\ b=3\\)、\\(\\bar{x}=7\\)、\\(s_x^2=3.6\\) を代入する。",
      keisan="平均は \\(2\\times7+3=17\\)、分散は \\(2^2\\times3.6=14.4\\)。",
      kotae="平均 \\(17\\)、分散 \\(14.4\\)。",
      hosoku="\\(+3\\) は分散に影響しない (平行移動ではばらつきは変わらない)。"
             "\\(a\\) を 2 乗し忘れると \\(7.2\\) になる。"),
    Q("2 つの変量 \\(x,\\ y\\) について、共分散が \\(-4.2\\)、\\(x\\) の標準偏差が \\(3\\)、"
      "\\(y\\) の標準偏差が \\(2\\) であるとき、相関係数を求めよ。",
      "データの分析",
      ("\\(-0.7\\)", Rational(-7, 10)),
      [("\\(-0.35\\)", Rational(-7, 20)), ("\\(0.7\\)", Rational(7, 10)), ("\\(-2.1\\)", Rational(-21, 10))],
      lambda: Rational(-42, 10) / (Integer(3) * Integer(2)),
      hoshin="相関係数は共分散を 2 つの標準偏差の積で割って、単位に依存しない値に直したもの。",
      rishiki="\\(r=\\dfrac{s_{xy}}{s_xs_y}=\\dfrac{-4.2}{3\\times2}\\)。",
      keisan="\\(\\dfrac{-4.2}{6}=-0.7\\)。",
      kotae="\\(-0.7\\)。",
      hosoku="相関係数は必ず \\(-1\\le r\\le1\\) に収まるので、それ自体が検算になる。"
             "割り忘れると \\(-4.2\\) となり範囲外で明らかにおかしいと気づける。"),
  ])


# ---- 第5問 場合の数と確率 --------------------------------------------
_C = binomial

D("math_unit", "数学I・A 第5問",
  "赤玉 4 個、白玉 5 個の合計 9 個が入った袋がある。玉は色以外に区別がつかないものとし、"
  "袋の中はよくかき混ぜてあるものとする。次の問い(問1〜問5)に答えよ。"
  "各小問に必要な設定は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    Q("赤玉 4 個、白玉 5 個の計 9 個から同時に 3 個を取り出すとき、取り出し方は何通りあるか。",
      "場合の数・確率",
      ("\\(84\\) 通り", _C(9, 3)),
      [("\\(504\\) 通り", Integer(504)), ("\\(126\\) 通り", Integer(126)), ("\\(729\\) 通り", Integer(729))],
      lambda: _C(9, 3),
      hoshin="「同時に取り出す」ので順序は区別しない。順列ではなく組合せを使う。",
      rishiki="\\({}_9\\mathrm{C}_3\\)。",
      keisan="\\(\\dfrac{9\\cdot8\\cdot7}{3\\cdot2\\cdot1}=84\\)。",
      kotae="\\(84\\) 通り。",
      hosoku="順序を区別すると \\({}_9\\mathrm{P}_3=504\\) 通りで 6 倍になる。"
             "「同時に」「取り出す組合せ」は \\(\\mathrm{C}\\) の合図。"),
    Q("赤玉 4 個、白玉 5 個の計 9 個から同時に 3 個を取り出すとき、3 個とも赤玉である確率を求めよ。",
      "場合の数・確率",
      ("\\(\\dfrac{1}{21}\\)", Rational(1, 21)),
      [("\\(\\dfrac{1}{84}\\)", Rational(1, 84)),
       ("\\(\\dfrac{4}{21}\\)", Rational(4, 21)),
       ("\\(\\dfrac{1}{14}\\)", Rational(1, 14))],
      lambda: Rational(_C(4, 3), _C(9, 3)),
      hoshin="(赤 3 個を選ぶ場合の数) ÷ (全事象の場合の数) で求める。",
      rishiki="\\(\\dfrac{{}_4\\mathrm{C}_3}{{}_9\\mathrm{C}_3}\\)。",
      keisan="\\({}_4\\mathrm{C}_3=4\\)、\\({}_9\\mathrm{C}_3=84\\) より \\(\\dfrac{4}{84}=\\dfrac{1}{21}\\)。",
      kotae="\\(\\dfrac{1}{21}\\)。",
      hosoku="同色でも 1 個ずつ区別して数えるのが確率の原則。"
             "分子を「赤 3 個で 1 通り」と数えると \\(\\dfrac{1}{84}\\) と誤る。"),
    Q("赤玉 4 個、白玉 5 個の計 9 個から同時に 3 個を取り出すとき、"
      "赤玉 2 個・白玉 1 個である確率を求めよ。",
      "場合の数・確率",
      ("\\(\\dfrac{5}{14}\\)", Rational(5, 14)),
      [("\\(\\dfrac{10}{21}\\)", Rational(10, 21)),
       ("\\(\\dfrac{15}{28}\\)", Rational(15, 28)),
       ("\\(\\dfrac{5}{28}\\)", Rational(5, 28))],
      lambda: Rational(_C(4, 2) * _C(5, 1), _C(9, 3)),
      hoshin="色ごとに選び方を数え、積の法則でつなぐ。",
      rishiki="\\(\\dfrac{{}_4\\mathrm{C}_2\\times{}_5\\mathrm{C}_1}{{}_9\\mathrm{C}_3}\\)。",
      keisan="\\({}_4\\mathrm{C}_2=6\\)、\\({}_5\\mathrm{C}_1=5\\) なので "
             "\\(\\dfrac{6\\times5}{84}=\\dfrac{30}{84}=\\dfrac{5}{14}\\)。",
      kotae="\\(\\dfrac{5}{14}\\)。",
      hosoku="色ごとの選び方は「かけ算」でつなぐ。足すと別の事象を数えたことになる。"),
    Q("赤玉 4 個、白玉 5 個の計 9 個から 1 個ずつ続けて 2 回取り出す。取り出した玉は袋に戻さない。"
      "1 回目が赤玉であったとき、2 回目も赤玉である条件付き確率を求めよ。",
      "場合の数・確率",
      ("\\(\\dfrac{3}{8}\\)", Rational(3, 8)),
      [("\\(\\dfrac{4}{9}\\)", Rational(4, 9)),
       ("\\(\\dfrac{1}{2}\\)", Rational(1, 2)),
       ("\\(\\dfrac{1}{6}\\)", Rational(1, 6))],
      lambda: Rational(4 - 1, 9 - 1),
      hoshin="条件付き確率は「条件が起きた後の世界」で数え直す。袋の中身を更新してから考える。",
      rishiki="1 回目に赤玉を取り出した後、袋の中は赤玉 \\(3\\) 個・白玉 \\(5\\) 個の計 \\(8\\) 個。",
      keisan="その \\(8\\) 個から赤玉を引く確率だから \\(\\dfrac{3}{8}\\)。",
      kotae="\\(\\dfrac{3}{8}\\)。",
      hosoku="戻さないので分子も分母も 1 ずつ減る。この更新を見落とすと \\(\\dfrac{4}{9}\\) と誤る。"),
    Q("赤玉 4 個、白玉 5 個の計 9 個から同時に 3 個を取り出すとき、"
      "取り出した赤玉の個数の期待値を求めよ。",
      "場合の数・確率",
      ("\\(\\dfrac{4}{3}\\)", Rational(4, 3)),
      [("\\(1\\)", Integer(1)), ("\\(\\dfrac{3}{2}\\)", Rational(3, 2)), ("\\(\\dfrac{2}{3}\\)", Rational(2, 3))],
      lambda: sum(Integer(i) * Rational(_C(4, i) * _C(5, 3 - i), _C(9, 3)) for i in range(0, 4)),
      hoshin="赤玉の個数 \\(X\\) の確率分布を作り、\\(E(X)=\\sum xP(x)\\) で求める。",
      rishiki="\\(P(X=i)=\\dfrac{{}_4\\mathrm{C}_i\\cdot{}_5\\mathrm{C}_{3-i}}{{}_9\\mathrm{C}_3}\\ (i=0,1,2,3)\\)。",
      keisan="\\(P(0)=\\dfrac{10}{84},\\ P(1)=\\dfrac{40}{84},\\ P(2)=\\dfrac{30}{84},\\ P(3)=\\dfrac{4}{84}\\)。"
             "\\(E(X)=\\dfrac{0+40+60+12}{84}=\\dfrac{112}{84}=\\dfrac43\\)。",
      kotae="\\(\\dfrac{4}{3}\\)。",
      hosoku="期待値の線形性から「1 個あたり赤の割合 \\(\\dfrac49\\) を 3 倍する」と考えても "
             "\\(3\\times\\dfrac49=\\dfrac43\\) で一致する。分布を作らずに検算できる。"),
  ])


# ---- 第6問 図形の性質 ------------------------------------------------
D("math_unit", "数学I・A 第6問",
  "花子さんは円と三角形の性質について復習している。次の問い(問1〜問5)に答えよ。"
  "各小問に必要な設定はすべて問題文中に書かれており、それぞれ単独で解答できる。",
  [
    Q("円 O の外部の点 P を通る直線が円 O と 2 点 A, B で交わっており、\\(PA=3\\)、\\(AB=5\\) である"
      "(A は P に近い方の交点)。また、点 P から円 O に引いた接線の接点を T とする。"
      "このとき線分 \\(PT\\) の長さを求めよ。",
      "図形の性質",
      ("\\(2\\sqrt{6}\\)", 2 * sqrt(6)),
      [("\\(\\sqrt{15}\\)", sqrt(15)), ("\\(4\\)", Integer(4)), ("\\(2\\sqrt{3}\\)", 2 * sqrt(3))],
      lambda: sqrt(Integer(3) * (Integer(3) + Integer(5))),
      hoshin="接線と割線が 1 点で交わる形なので、方べきの定理 \\(PT^2=PA\\cdot PB\\) を使う。",
      rishiki="\\(PB=PA+AB=3+5=8\\) なので \\(PT^2=3\\times8\\)。",
      keisan="\\(PT^2=24\\)、\\(PT=\\sqrt{24}=2\\sqrt6\\)。",
      kotae="\\(2\\sqrt{6}\\)。",
      hosoku="\\(PB\\) は P から遠い方の交点までの長さ。\\(AB=5\\) と取り違えると "
             "\\(PT=\\sqrt{15}\\) になる。図で P・A・B の並びを確認してから代入する。"),
    Q("三角形 ABC において、辺 AB を \\(2:1\\) に内分する点を D、辺 BC を \\(3:2\\) に内分する点を E とする。"
      "直線 DE と直線 AC の交点を F とするとき、\\(AF:FC\\) を求めよ。",
      "図形の性質",
      ("\\(3:1\\)", Tuple(Integer(3), Integer(1))),
      [("\\(1:3\\)", Tuple(Integer(1), Integer(3))),
       ("\\(3:2\\)", Tuple(Integer(3), Integer(2))),
       ("\\(2:1\\)", Tuple(Integer(2), Integer(1)))],
      lambda: _menelaus_af_fc(),
      hoshin="三角形を 1 本の直線が横切る形なので、三角形 ABC と直線 DEF にメネラウスの定理を使う。",
      rishiki="\\(\\dfrac{AD}{DB}\\cdot\\dfrac{BE}{EC}\\cdot\\dfrac{CF}{FA}=1\\)。"
              "\\(\\dfrac{AD}{DB}=\\dfrac21\\)、\\(\\dfrac{BE}{EC}=\\dfrac32\\)。",
      keisan="\\(\\dfrac21\\cdot\\dfrac32\\cdot\\dfrac{CF}{FA}=1\\) より "
             "\\(3\\cdot\\dfrac{CF}{FA}=1\\)、\\(\\dfrac{CF}{FA}=\\dfrac13\\)。",
      kotae="\\(3:1\\)。",
      hosoku="F は辺 AC を C の側に延長した上にある。"
             "\\(A(0,0),\\ B(1,0),\\ C(0,1)\\) と座標をとって直線 DE と \\(x=0\\) の交点 "
             "\\(\\left(0,\\ \\dfrac32\\right)\\) を求めても "
             "\\(AF:FC=\\dfrac32:\\dfrac12=3:1\\) と確認できる。"),
    Q("円に内接する四角形 ABCD において \\(\\angle A=105^\\circ\\) であるとき、\\(\\angle C\\) の大きさを求めよ。",
      "図形の性質",
      ("\\(75^\\circ\\)", Integer(75)),
      [("\\(105^\\circ\\)", Integer(105)), ("\\(85^\\circ\\)", Integer(85)), ("\\(90^\\circ\\)", Integer(90))],
      lambda: Integer(180) - Integer(105),
      hoshin="円に内接する四角形では、向かい合う内角の和が \\(180^\\circ\\) になる。",
      rishiki="\\(\\angle A+\\angle C=180^\\circ\\)。",
      keisan="\\(\\angle C=180^\\circ-105^\\circ=75^\\circ\\)。",
      kotae="\\(75^\\circ\\)。",
      hosoku="「向かい合う角は等しい」と覚え違えると \\(105^\\circ\\) と誤る。"
             "平行四辺形の性質との混同に注意。同じ性質は「外角は内対角に等しい」とも言い換えられる。"),
    Q("三角形 ABC において \\(AB=8\\)、\\(AC=6\\) である。\\(\\angle A\\) の二等分線と辺 BC の交点を D とするとき、"
      "\\(BD:DC\\) を求めよ。",
      "図形の性質",
      ("\\(4:3\\)", Tuple(Integer(4), Integer(3))),
      [("\\(3:4\\)", Tuple(Integer(3), Integer(4))),
       ("\\(16:9\\)", Tuple(Integer(16), Integer(9))),
       ("\\(2:1\\)", Tuple(Integer(2), Integer(1)))],
      lambda: (lambda g: Tuple(Integer(8) / g, Integer(6) / g))(Integer(2)),
      hoshin="角の二等分線は、対辺を「その角をはさむ 2 辺の比」に内分する。",
      rishiki="\\(BD:DC=AB:AC=8:6\\)。",
      keisan="\\(8:6\\) を約分して \\(4:3\\)。",
      kotae="\\(4:3\\)。",
      hosoku="比の向きを逆にすると \\(3:4\\)。辺の 2 乗の比と混同すると \\(16:9\\) になる。"
             "\\(B\\) の側に \\(AB\\)、\\(C\\) の側に \\(AC\\) が対応すると押さえる。"),
    Q("座標平面上の 3 点 \\(A(1,\\ 2)\\)、\\(B(5,\\ -2)\\)、\\(C(3,\\ 6)\\) を頂点とする三角形 ABC の"
      "重心の座標を求めよ。",
      "図形の性質",
      ("\\((3,\\ 2)\\)", Tuple(Integer(3), Integer(2))),
      [("\\((3,\\ 3)\\)", Tuple(Integer(3), Integer(3))),
       ("\\((9,\\ 6)\\)", Tuple(Integer(9), Integer(6))),
       ("\\((2,\\ 2)\\)", Tuple(Integer(2), Integer(2)))],
      lambda: Tuple(Rational(1 + 5 + 3, 3), Rational(2 - 2 + 6, 3)),
      hoshin="重心の座標は 3 頂点の座標の平均。",
      rishiki="\\(G\\left(\\dfrac{1+5+3}{3},\\ \\dfrac{2+(-2)+6}{3}\\right)\\)。",
      keisan="\\(\\left(\\dfrac93,\\ \\dfrac63\\right)=(3,\\ 2)\\)。",
      kotae="\\((3,\\ 2)\\)。",
      hosoku="3 で割り忘れると \\((9,\\ 6)\\)。重心は各中線を頂点から \\(2:1\\) に内分する点でもある。"),
  ])


# =====================================================================
# 数学II・B・C  (part_key = math_2b)
# =====================================================================

th = symbols('theta')

# ---- 第1問 三角関数 --------------------------------------------------
D("math_unit", "数学II・B・C 第1問",
  "太郎さんは三角関数の性質を復習している。次の問い(問1〜問5)に答えよ。"
  "角の大きさは、断りのない限り弧度法で表す。"
  "各小問に必要な条件は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    Q("\\(0<\\theta<\\dfrac{\\pi}{2}\\) で \\(\\sin\\theta=\\dfrac{3}{5}\\) であるとき、"
      "\\(\\sin 2\\theta\\) の値を求めよ。",
      "三角関数",
      ("\\(\\dfrac{24}{25}\\)", Rational(24, 25)),
      [("\\(\\dfrac{12}{25}\\)", Rational(12, 25)),
       ("\\(\\dfrac{7}{25}\\)", Rational(7, 25)),
       ("\\(\\dfrac{6}{5}\\)", Rational(6, 5))],
      lambda: simplify(2 * Rational(3, 5) * sqrt(1 - Rational(3, 5) ** 2)),
      hoshin="2 倍角の公式 \\(\\sin2\\theta=2\\sin\\theta\\cos\\theta\\) を使うため、まず \\(\\cos\\theta\\) を出す。",
      rishiki="\\(0<\\theta<\\dfrac{\\pi}{2}\\) では \\(\\cos\\theta>0\\) なので "
              "\\(\\cos\\theta=\\sqrt{1-\\sin^2\\theta}=\\sqrt{1-\\left(\\dfrac35\\right)^2}\\)。",
      keisan="\\(\\cos\\theta=\\dfrac45\\)。よって "
             "\\(\\sin2\\theta=2\\cdot\\dfrac35\\cdot\\dfrac45=\\dfrac{24}{25}\\)。",
      kotae="\\(\\dfrac{24}{25}\\)。",
      hosoku="\\(2\\) を掛け忘れると \\(\\dfrac{12}{25}\\)。"
             "\\(\\cos2\\theta=1-2\\sin^2\\theta=\\dfrac{7}{25}\\) と取り違えないこと。"
             "角の範囲から \\(\\cos\\theta\\) の符号を決める手順を必ず書く。"),
    Q("\\(\\sin\\theta+\\sqrt{3}\\cos\\theta\\) を \\(r\\sin(\\theta+\\alpha)\\) "
      "(\\(r>0,\\ -\\pi<\\alpha\\le\\pi\\)) の形に変形したときの \\(r\\) と \\(\\alpha\\) の組はどれか。",
      "三角関数",
      ("\\(r=2,\\ \\alpha=\\dfrac{\\pi}{3}\\)", Tuple(Integer(2), pi / 3)),
      [("\\(r=2,\\ \\alpha=\\dfrac{\\pi}{6}\\)", Tuple(Integer(2), pi / 6)),
       ("\\(r=4,\\ \\alpha=\\dfrac{\\pi}{3}\\)", Tuple(Integer(4), pi / 3)),
       ("\\(r=\\sqrt{3}+1,\\ \\alpha=\\dfrac{\\pi}{4}\\)", Tuple(sqrt(3) + 1, pi / 4))],
      lambda: Tuple(sqrt(Integer(1) ** 2 + sqrt(3) ** 2),
                    [a for a in (pi / 6, pi / 3, pi / 4)
                     if simplify(2 * cos(a) - 1) == 0 and simplify(2 * sin(a) - sqrt(3)) == 0][0]),
      hoshin="三角関数の合成。\\(a\\sin\\theta+b\\cos\\theta=r\\sin(\\theta+\\alpha)\\) では "
             "\\(r=\\sqrt{a^2+b^2}\\)、\\(\\cos\\alpha=\\dfrac ar\\)、\\(\\sin\\alpha=\\dfrac br\\)。",
      rishiki="\\(a=1,\\ b=\\sqrt3\\) なので \\(r=\\sqrt{1^2+(\\sqrt3)^2}\\)、"
              "\\(\\cos\\alpha=\\dfrac1r\\)、\\(\\sin\\alpha=\\dfrac{\\sqrt3}{r}\\)。",
      keisan="\\(r=\\sqrt{1+3}=2\\)。\\(\\cos\\alpha=\\dfrac12,\\ \\sin\\alpha=\\dfrac{\\sqrt3}{2}\\) "
             "を同時に満たす \\(\\alpha\\) は \\(\\dfrac{\\pi}{3}\\)。",
      kotae="\\(r=2,\\ \\alpha=\\dfrac{\\pi}{3}\\)。",
      hosoku="\\(\\sin\\) と \\(\\cos\\) の役割を逆にすると \\(\\alpha=\\dfrac{\\pi}{6}\\) と誤る。"
             "\\(\\cos\\alpha\\) の分子が \\(\\sin\\theta\\) の係数、と対応を固定して覚える。"),
    Q("\\(0\\le\\theta<2\\pi\\) のとき、方程式 \\(\\sin\\theta+\\sqrt{3}\\cos\\theta=1\\) の解をすべて求めよ。",
      "三角関数",
      ("\\(\\theta=\\dfrac{\\pi}{2},\\ \\dfrac{11\\pi}{6}\\)", FiniteSet(pi / 2, 11 * pi / 6)),
      [("\\(\\theta=\\dfrac{\\pi}{6},\\ \\dfrac{5\\pi}{6}\\)", FiniteSet(pi / 6, 5 * pi / 6)),
       ("\\(\\theta=\\dfrac{\\pi}{3},\\ \\dfrac{5\\pi}{3}\\)", FiniteSet(pi / 3, 5 * pi / 3)),
       ("\\(\\theta=\\dfrac{\\pi}{2}\\) のみ", FiniteSet(pi / 2))],
      lambda: FiniteSet(*[m * pi / 12 for m in range(24)
                          if simplify(sin(m * pi / 12) + sqrt(3) * cos(m * pi / 12) - 1) == 0]),
      hoshin="左辺を合成して \\(\\sin\\) 1 つの方程式にし、角の範囲も同じだけ平行移動してから解く。",
      rishiki="\\(2\\sin\\left(\\theta+\\dfrac{\\pi}{3}\\right)=1\\)、すなわち "
              "\\(\\sin\\left(\\theta+\\dfrac{\\pi}{3}\\right)=\\dfrac12\\)。"
              "\\(0\\le\\theta<2\\pi\\) より \\(\\dfrac{\\pi}{3}\\le\\theta+\\dfrac{\\pi}{3}<\\dfrac{7\\pi}{3}\\)。",
      keisan="この範囲で \\(\\sin=\\dfrac12\\) となるのは "
             "\\(\\theta+\\dfrac{\\pi}{3}=\\dfrac{5\\pi}{6},\\ \\dfrac{13\\pi}{6}\\)。"
             "それぞれ \\(\\dfrac{\\pi}{3}\\) を引いて "
             "\\(\\theta=\\dfrac{\\pi}{2},\\ \\dfrac{11\\pi}{6}\\)。",
      kotae="\\(\\theta=\\dfrac{\\pi}{2},\\ \\dfrac{11\\pi}{6}\\)。",
      hosoku="最後に \\(\\dfrac{\\pi}{3}\\) を引き忘れると \\(\\dfrac{5\\pi}{6}\\) 等をそのまま答えてしまう。"
             "角の範囲も \\(\\dfrac{\\pi}{3}\\) ずらすのを忘れない。"),
    Q("\\(\\cos 75^\\circ\\) の値を求めよ。",
      "三角関数",
      ("\\(\\dfrac{\\sqrt{6}-\\sqrt{2}}{4}\\)", (sqrt(6) - sqrt(2)) / 4),
      [("\\(\\dfrac{\\sqrt{6}+\\sqrt{2}}{4}\\)", (sqrt(6) + sqrt(2)) / 4),
       ("\\(\\dfrac{\\sqrt{2}-\\sqrt{6}}{4}\\)", (sqrt(2) - sqrt(6)) / 4),
       ("\\(\\dfrac{\\sqrt{3}-1}{4}\\)", (sqrt(3) - 1) / 4)],
      lambda: simplify(cos(75 * pi / 180)),
      hoshin="\\(75^\\circ\\) を既知の角の和 \\(45^\\circ+30^\\circ\\) に分け、余弦の加法定理を使う。",
      rishiki="\\(\\cos(\\alpha+\\beta)=\\cos\\alpha\\cos\\beta-\\sin\\alpha\\sin\\beta\\) より "
              "\\(\\cos45^\\circ\\cos30^\\circ-\\sin45^\\circ\\sin30^\\circ\\)。",
      keisan="\\(\\dfrac{\\sqrt2}{2}\\cdot\\dfrac{\\sqrt3}{2}-\\dfrac{\\sqrt2}{2}\\cdot\\dfrac12"
             "=\\dfrac{\\sqrt6}{4}-\\dfrac{\\sqrt2}{4}=\\dfrac{\\sqrt6-\\sqrt2}{4}\\)。",
      kotae="\\(\\dfrac{\\sqrt{6}-\\sqrt{2}}{4}\\)。",
      hosoku="余弦の加法定理は符号が反転する (「コスコス マイナス サインサイン」)。"
             "\\(+\\) にすると \\(\\sin75^\\circ\\) の値になってしまう。"
             "\\(75^\\circ\\) は鋭角なので値が正になることでも検算できる。"),
    Q("\\(0\\le\\theta\\le\\pi\\) における関数 \\(y=\\sin\\theta+\\sqrt{3}\\cos\\theta\\) の"
      "最大値と最小値の組として正しいものはどれか。",
      "三角関数",
      ("最大値 \\(2\\)、最小値 \\(-\\sqrt{3}\\)", Tuple(Integer(2), -sqrt(3))),
      [("最大値 \\(2\\)、最小値 \\(-2\\)", Tuple(Integer(2), Integer(-2))),
       ("最大値 \\(2\\)、最小値 \\(\\sqrt{3}\\)", Tuple(Integer(2), sqrt(3))),
       ("最大値 \\(1+\\sqrt{3}\\)、最小値 \\(-\\sqrt{3}\\)", Tuple(1 + sqrt(3), -sqrt(3)))],
      lambda: _extrema_on_interval(sin(th) + sqrt(3) * cos(th), th, Integer(0), pi),
      hoshin="合成してから、動く角の範囲で \\(\\sin\\) が実際にどこまで動くかを調べる。",
      rishiki="\\(y=2\\sin\\left(\\theta+\\dfrac{\\pi}{3}\\right)\\)。"
              "\\(0\\le\\theta\\le\\pi\\) より \\(\\dfrac{\\pi}{3}\\le\\theta+\\dfrac{\\pi}{3}\\le\\dfrac{4\\pi}{3}\\)。",
      keisan="この区間で \\(\\sin\\) は \\(\\dfrac{\\pi}{2}\\) のとき最大 \\(1\\)、"
             "右端 \\(\\dfrac{4\\pi}{3}\\) のとき最小 \\(-\\dfrac{\\sqrt3}{2}\\)。"
             "よって \\(y\\) の最大値は \\(2\\times1=2\\)、最小値は \\(2\\times\\left(-\\dfrac{\\sqrt3}{2}\\right)=-\\sqrt3\\)。",
      kotae="最大値 \\(2\\)、最小値 \\(-\\sqrt{3}\\)。",
      hosoku="\\(\\theta\\) の範囲を無視して振幅だけから \\(\\pm2\\) とするのが典型ミス。"
             "\\(-1\\) に達するのは \\(\\theta+\\dfrac{\\pi}{3}=\\dfrac{3\\pi}{2}\\) のときで、"
             "これは範囲外である。合成後の角の範囲を必ず書き出す。"),
  ])


# ---- 第2問 指数関数・対数関数 ----------------------------------------
D("math_unit", "数学II・B・C 第2問",
  "花子さんは指数関数と対数関数の計算を復習している。次の問い(問1〜問5)に答えよ。"
  "対数の底はすべて正で 1 と異なるものとし、真数は正とする。"
  "各小問に必要な条件は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    Q("\\(\\left(\\dfrac{1}{8}\\right)^{-\\frac{2}{3}}\\) の値を求めよ。",
      "指数関数・対数関数",
      ("\\(4\\)", Integer(4)),
      [("\\(\\dfrac{1}{4}\\)", Rational(1, 4)), ("\\(2\\)", Integer(2)), ("\\(16\\)", Integer(16))],
      lambda: simplify(Rational(1, 8) ** Rational(-2, 3)),
      hoshin="負の指数は逆数、分数の指数は累乗根。底を素因数に直してから指数法則を使う。",
      rishiki="\\(\\left(\\dfrac18\\right)^{-\\frac23}=8^{\\frac23}=(2^3)^{\\frac23}\\)。",
      keisan="\\((a^m)^n=a^{mn}\\) より \\(2^{3\\times\\frac23}=2^2=4\\)。",
      kotae="\\(4\\)。",
      hosoku="負号を落として \\(8^{-\\frac23}\\) のまま計算すると \\(\\dfrac14\\) になる。"
             "「マイナス指数 = 逆数」を最初に処理してしまうと迷わない。"),
    Q("\\(\\log_2 24-\\log_2 3\\) の値を求めよ。",
      "指数関数・対数関数",
      ("\\(3\\)", Integer(3)),
      [("\\(2\\)", Integer(2)), ("\\(8\\)", Integer(8)), ("\\(\\log_2 21\\)", sympify('log(21)/log(2)'))],
      lambda: simplify(sympify('log(24)/log(2) - log(3)/log(2)')),
      hoshin="同じ底の対数の差は、真数の商にまとめられる。",
      rishiki="\\(\\log_2 24-\\log_2 3=\\log_2\\dfrac{24}{3}\\)。",
      keisan="\\(\\log_2 8=\\log_2 2^3=3\\)。",
      kotae="\\(3\\)。",
      hosoku="真数どうしを引いて \\(\\log_2 21\\) とするのは公式の誤用。"
             "「和は積、差は商」と対応づけて覚える。答えの \\(3\\) は \\(2^3=8\\) からも確認できる。"),
    Q("方程式 \\(4^x-3\\cdot 2^x-4=0\\) を解け。",
      "指数関数・対数関数",
      ("\\(x=2\\)", FiniteSet(Integer(2))),
      [("\\(x=-1,\\ 2\\)", FiniteSet(Integer(-1), Integer(2))),
       ("\\(x=1\\)", FiniteSet(Integer(1))),
       ("\\(x=4\\)", FiniteSet(Integer(4)))],
      lambda: solveset(Eq(4 ** x - 3 * 2 ** x - 4, 0), x, S.Reals),
      hoshin="\\(2^x\\) をひとかたまりと見て 2 次方程式に帰着させる。置換した文字の変域を必ず添える。",
      rishiki="\\(t=2^x\\ (t>0)\\) とおくと \\(4^x=(2^x)^2=t^2\\) なので \\(t^2-3t-4=0\\)。",
      keisan="\\((t-4)(t+1)=0\\) より \\(t=4,\\ -1\\)。"
             "\\(t=2^x>0\\) だから \\(t=-1\\) は不適。\\(t=4=2^2\\) より \\(x=2\\)。",
      kotae="\\(x=2\\)。",
      hosoku="\\(t>0\\) の条件を落とすと \\(t=-1\\) から余分な解を作ってしまう。"
             "指数関数の値は常に正、という基本性質が効く場面。"),
    Q("不等式 \\(\\log_3(x-1)+\\log_3(x+1)<1\\) を解け。",
      "指数関数・対数関数",
      ("\\(1<x<2\\)", Interval.open(1, 2)),
      [("\\(x<2\\)", Interval.open(-oo, 2)),
       ("\\(-2<x<2\\)", Interval.open(-2, 2)),
       ("\\(1<x<4\\)", Interval.open(1, 4))],
      lambda: solveset((x - 1) * (x + 1) < 3, x, S.Reals).intersect(Interval.open(1, oo)),
      hoshin="対数の不等式は「真数条件を先に書く」→「底が 1 より大きいので不等号の向きはそのまま」の順で処理する。",
      rishiki="真数条件は \\(x-1>0\\) かつ \\(x+1>0\\) より \\(x>1\\)。"
              "左辺をまとめると \\(\\log_3(x-1)(x+1)<1=\\log_3 3\\)。",
      keisan="底 \\(3>1\\) なので \\((x-1)(x+1)<3\\)、すなわち \\(x^2<4\\) より \\(-2<x<2\\)。"
             "真数条件 \\(x>1\\) と合わせて \\(1<x<2\\)。",
      kotae="\\(1<x<2\\)。",
      hosoku="真数条件を忘れると \\(-2<x<2\\) と誤る。"
             "対数の問題は必ず真数条件から書き始めると、この失点は起きない。"),
    Q("\\(\\log_{10}2=0.3010\\)、\\(\\log_{10}3=0.4771\\) とするとき、\\(6^{20}\\) は何桁の整数か。",
      "指数関数・対数関数",
      ("\\(16\\) 桁", Integer(16)),
      [("\\(15\\) 桁", Integer(15)), ("\\(17\\) 桁", Integer(17)), ("\\(20\\) 桁", Integer(20))],
      lambda: Integer(len(str(6 ** 20))),
      hoshin="常用対数をとり、\\(10^{n}\\le N<10^{n+1}\\) の \\(n\\) を求める。桁数は \\(n+1\\)。",
      rishiki="\\(\\log_{10}6^{20}=20\\log_{10}6=20(\\log_{10}2+\\log_{10}3)\\)。",
      keisan="\\(20(0.3010+0.4771)=20\\times0.7781=15.562\\)。"
             "\\(15<15.562<16\\) より \\(10^{15}<6^{20}<10^{16}\\)。",
      kotae="\\(16\\) 桁。",
      hosoku="整数部分が \\(15\\) なので桁数は \\(15+1=16\\)。"
             "この \\(+1\\) を忘れて \\(15\\) 桁と答えるミスが最も多い。"
             "\\(10^1=10\\) が 2 桁であることを思い出すと \\(+1\\) を納得できる。"),
  ])


# ---- 第3問 微分・積分 ------------------------------------------------
_f3 = x ** 3 - 3 * x ** 2 - 9 * x + 5

D("math_unit", "数学II・B・C 第3問",
  "太郎さんは 3 次関数 \\(f(x)=x^3-3x^2-9x+5\\) とそのグラフについて調べている。"
  "次の問い(問1〜問5)に答えよ。"
  "各小問に必要な式は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    Q("関数 \\(f(x)=x^3-3x^2-9x+5\\) の極大値を求めよ。",
      "微分・積分",
      ("\\(10\\)", Integer(10)),
      [("\\(-22\\)", Integer(-22)), ("\\(5\\)", Integer(5)), ("\\(-1\\)", Integer(-1))],
      lambda: _local_max_value(_f3, x),
      hoshin="導関数の符号変化を調べ、正から負に変わる点で極大になる。増減表を作る。",
      rishiki="\\(f'(x)=3x^2-6x-9=3(x-3)(x+1)\\)。\\(f'(x)=0\\) となるのは \\(x=-1,\\ 3\\)。",
      keisan="\\(f'\\) は \\(x<-1\\) で正、\\(-1<x<3\\) で負、\\(x>3\\) で正。"
             "よって \\(x=-1\\) で極大。\\(f(-1)=-1-3+9+5=10\\)。",
      kotae="\\(10\\)。",
      hosoku="\\(x=3\\) は極小で \\(f(3)=27-27-27+5=-22\\)。"
             "増減表を書かずに \\(f'(x)=0\\) の解を代入しただけだと、極大と極小を取り違える。"),
    Q("曲線 \\(y=x^3-3x^2-9x+5\\) 上の点 \\((1,\\ -6)\\) における接線の方程式を求めよ。",
      "微分・積分",
      ("\\(y=-12x+6\\)", -12 * x + 6),
      [("\\(y=-12x-6\\)", -12 * x - 6),
       ("\\(y=12x-18\\)", 12 * x - 18),
       ("\\(y=-9x+3\\)", -9 * x + 3)],
      lambda: expand(diff(_f3, x).subs(x, 1) * (x - 1) + _f3.subs(x, 1)),
      hoshin="接線の傾きは接点での微分係数。傾きと通る点から直線の式を作る。",
      rishiki="\\(f'(x)=3x^2-6x-9\\) より傾きは \\(f'(1)\\)。接点は \\((1,\\ -6)\\) なので "
              "\\(y-(-6)=f'(1)(x-1)\\)。",
      keisan="\\(f'(1)=3-6-9=-12\\)。\\(y+6=-12(x-1)=-12x+12\\)、"
             "よって \\(y=-12x+6\\)。",
      kotae="\\(y=-12x+6\\)。",
      hosoku="\\(-12(x-1)=-12x+12\\) の展開で符号を誤ると \\(y=-12x-6\\) になる。"
             "接点が曲線上にあること (\\(f(1)=1-3-9+5=-6\\)) も先に確認しておく。"),
    Q("定積分 \\(\\displaystyle\\int_{0}^{2}(3x^2-4x+1)\\,dx\\) の値を求めよ。",
      "微分・積分",
      ("\\(2\\)", Integer(2)),
      [("\\(6\\)", Integer(6)), ("\\(4\\)", Integer(4)), ("\\(0\\)", Integer(0))],
      lambda: integrate(3 * x ** 2 - 4 * x + 1, (x, 0, 2)),
      hoshin="各項の原始関数を求め、上端と下端を代入して差をとる。",
      rishiki="\\(\\displaystyle\\int(3x^2-4x+1)dx=x^3-2x^2+x\\)。",
      keisan="\\(\\left[x^3-2x^2+x\\right]_0^2=(8-8+2)-0=2\\)。",
      kotae="\\(2\\)。",
      hosoku="\\(-4x\\) の積分は \\(-2x^2\\)。"
             "\\(\\div2\\) を忘れて \\(-4x^2\\) とすると答えが大きくずれる。"
             "積分したら微分して戻るか確かめると安全。"),
    Q("放物線 \\(y=x^2-2x\\) と \\(x\\) 軸で囲まれた部分の面積を求めよ。",
      "微分・積分",
      ("\\(\\dfrac{4}{3}\\)", Rational(4, 3)),
      [("\\(\\dfrac{8}{3}\\)", Rational(8, 3)), ("\\(\\dfrac{2}{3}\\)", Rational(2, 3)), ("\\(4\\)", Integer(4))],
      lambda: integrate(0 - (x ** 2 - 2 * x), (x, 0, 2)),
      hoshin="囲まれた面積は (上にある式) − (下にある式) を交点の間で積分する。まず交点と上下関係を確認する。",
      rishiki="\\(x^2-2x=x(x-2)\\) より交点は \\(x=0,\\ 2\\)。"
              "この区間で放物線は \\(x\\) 軸より下にあるので "
              "\\(\\displaystyle\\int_0^2\\{0-(x^2-2x)\\}dx\\)。",
      keisan="\\(\\left[x^2-\\dfrac{x^3}{3}\\right]_0^2=4-\\dfrac83=\\dfrac43\\)。",
      kotae="\\(\\dfrac{4}{3}\\)。",
      hosoku="上下を逆にすると符号が負になる。面積は必ず正。"
             "公式 \\(\\dfrac{|a|}{6}(\\beta-\\alpha)^3=\\dfrac16\\cdot2^3=\\dfrac43\\) でも検算できる。"),
    Q("放物線 \\(y=x^2\\) と直線 \\(y=x+2\\) で囲まれた部分の面積を求めよ。",
      "微分・積分",
      ("\\(\\dfrac{9}{2}\\)", Rational(9, 2)),
      [("\\(\\dfrac{9}{4}\\)", Rational(9, 4)), ("\\(\\dfrac{27}{2}\\)", Rational(27, 2)), ("\\(\\dfrac{3}{2}\\)", Rational(3, 2))],
      lambda: integrate((x + 2) - x ** 2, (x, -1, 2)),
      hoshin="2 曲線の交点を求め、(上の式) − (下の式) をその区間で積分する。",
      rishiki="\\(x^2=x+2\\) より \\(x^2-x-2=(x-2)(x+1)=0\\)、交点は \\(x=-1,\\ 2\\)。"
              "この区間では直線が上なので \\(\\displaystyle\\int_{-1}^{2}\\{(x+2)-x^2\\}dx\\)。",
      keisan="\\(\\left[\\dfrac{x^2}{2}+2x-\\dfrac{x^3}{3}\\right]_{-1}^{2}"
             "=\\left(2+4-\\dfrac83\\right)-\\left(\\dfrac12-2+\\dfrac13\\right)"
             "=\\dfrac{10}{3}+\\dfrac76=\\dfrac92\\)。",
      kotae="\\(\\dfrac{9}{2}\\)。",
      hosoku="\\(\\dfrac16\\) 公式 \\(\\dfrac16(\\beta-\\alpha)^3=\\dfrac16\\cdot3^3=\\dfrac{27}{6}=\\dfrac92\\) "
             "で一致を確認できる。交点の差 \\(\\beta-\\alpha=3\\) を使うだけなので検算が速い。"),
  ])


# ---- 第4問 数列 ------------------------------------------------------
D("math_unit", "数学II・B・C 第4問",
  "花子さんは数列の一般項と和について復習している。次の問い(問1〜問5)に答えよ。"
  "各小問に必要な条件は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    Q("等差数列 \\(\\{a_n\\}\\) が \\(a_3=11\\)、\\(a_7=27\\) を満たすとき、一般項 \\(a_n\\) を求めよ。",
      "数列",
      ("\\(a_n=4n-1\\)", 4 * n - 1),
      [("\\(a_n=4n+3\\)", 4 * n + 3),
       ("\\(a_n=4n-5\\)", 4 * n - 5),
       ("\\(a_n=3n+2\\)", 3 * n + 2)],
      lambda: (lambda d, a1: expand(a1 + (n - 1) * d))(
          Rational(27 - 11, 7 - 3), Integer(11) - 2 * Rational(27 - 11, 7 - 3)),
      hoshin="等差数列は 2 項の差から公差を出し、そこから初項を逆算する。",
      rishiki="\\(a_7-a_3=(7-3)d=4d\\)、また \\(a_3=a_1+2d\\)。",
      keisan="\\(4d=27-11=16\\) より \\(d=4\\)。\\(a_1=11-2\\cdot4=3\\)。"
             "よって \\(a_n=3+(n-1)\\cdot4=4n-1\\)。",
      kotae="\\(a_n=4n-1\\)。",
      hosoku="\\(a_3=4\\cdot3-1=11\\)、\\(a_7=4\\cdot7-1=27\\) と代入して検算する。"
             "\\(a_1\\) を \\(11\\) のまま使うと \\(a_n=4n+7\\) のようにずれる。"),
    Q("初項 \\(3\\)、公差 \\(4\\) の等差数列について、初項から第 20 項までの和を求めよ。",
      "数列",
      ("\\(820\\)", Integer(820)),
      [("\\(800\\)", Integer(800)), ("\\(840\\)", Integer(840)), ("\\(1580\\)", Integer(1580))],
      lambda: summation(3 + (n - 1) * 4, (n, 1, 20)),
      hoshin="等差数列の和の公式 \\(S_n=\\dfrac n2\\{2a_1+(n-1)d\\}\\) を使う。",
      rishiki="\\(S_{20}=\\dfrac{20}{2}\\{2\\cdot3+19\\cdot4\\}\\)。",
      keisan="\\(10(6+76)=10\\times82=820\\)。",
      kotae="\\(820\\)。",
      hosoku="末項 \\(a_{20}=3+19\\cdot4=79\\) を使い "
             "\\(S_{20}=\\dfrac{20(3+79)}{2}=820\\) と別式でも検算できる。"
             "\\((n-1)d\\) を \\(nd\\) とすると \\(840\\) になる。"),
    Q("初項 \\(3\\)、公比 \\(2\\) の等比数列について、初項から第 8 項までの和を求めよ。",
      "数列",
      ("\\(765\\)", Integer(765)),
      [("\\(768\\)", Integer(768)), ("\\(381\\)", Integer(381)), ("\\(1533\\)", Integer(1533))],
      lambda: summation(3 * 2 ** (n - 1), (n, 1, 8)),
      hoshin="等比数列の和の公式 \\(S_n=\\dfrac{a_1(r^n-1)}{r-1}\\) を使う (\\(r\\ne1\\))。",
      rishiki="\\(S_8=\\dfrac{3(2^8-1)}{2-1}\\)。",
      keisan="\\(2^8=256\\) なので \\(3(256-1)=3\\times255=765\\)。",
      kotae="\\(765\\)。",
      hosoku="\\(2^8\\) から \\(1\\) を引き忘れると \\(768\\)。"
             "第 8 項 \\(a_8=3\\cdot2^7=384\\) は「和」ではないので混同しない。"),
    Q("\\(\\displaystyle\\sum_{k=1}^{n}k(k+2)\\) を \\(n\\) の式で表せ。",
      "数列",
      ("\\(\\dfrac{n(n+1)(2n+7)}{6}\\)", n * (n + 1) * (2 * n + 7) / 6),
      [("\\(\\dfrac{n(n+1)(2n+1)}{6}\\)", n * (n + 1) * (2 * n + 1) / 6),
       ("\\(\\dfrac{n(n+1)(n+2)}{3}\\)", n * (n + 1) * (n + 2) / 3),
       ("\\(\\dfrac{n(n+1)(2n+7)}{3}\\)", n * (n + 1) * (2 * n + 7) / 3)],
      lambda: simplify(summation(k * (k + 2), (k, 1, n))),
      hoshin="まず展開して、\\(\\sum k^2\\) と \\(\\sum k\\) の公式が使える形に分ける。",
      rishiki="\\(\\displaystyle\\sum_{k=1}^{n}(k^2+2k)"
              "=\\dfrac{n(n+1)(2n+1)}{6}+2\\cdot\\dfrac{n(n+1)}{2}\\)。",
      keisan="\\(n(n+1)\\) でくくると "
             "\\(n(n+1)\\left\\{\\dfrac{2n+1}{6}+1\\right\\}=n(n+1)\\cdot\\dfrac{2n+7}{6}\\)。",
      kotae="\\(\\dfrac{n(n+1)(2n+7)}{6}\\)。",
      hosoku="\\(n=1\\) を入れると左辺は \\(1\\cdot3=3\\)、右辺も \\(\\dfrac{1\\cdot2\\cdot9}{6}=3\\) で一致する。"
             "\\(2\\sum k\\) の項を足し忘れると \\(\\dfrac{n(n+1)(2n+1)}{6}\\) のままになる。"),
    Q("\\(a_1=3\\)、\\(a_{n+1}=3a_n-4\\) (\\(n=1,2,3,\\dots\\)) で定まる数列 \\(\\{a_n\\}\\) の一般項を求めよ。",
      "数列",
      ("\\(a_n=3^{n-1}+2\\)", 3 ** (n - 1) + 2),
      [("\\(a_n=3^{n}+2\\)", 3 ** n + 2),
       ("\\(a_n=3^{n-1}-2\\)", 3 ** (n - 1) - 2),
       ("\\(a_n=3^{n-1}+3\\)", 3 ** (n - 1) + 3)],
      lambda: _recurrence_general(),
      hoshin="\\(a_{n+1}=pa_n+q\\) 型は特性方程式 \\(\\alpha=p\\alpha+q\\) を解き、"
             "\\(\\{a_n-\\alpha\\}\\) を等比数列に直す。",
      rishiki="\\(\\alpha=3\\alpha-4\\) より \\(\\alpha=2\\)。"
              "漸化式との差をとると \\(a_{n+1}-2=3(a_n-2)\\)。",
      keisan="\\(\\{a_n-2\\}\\) は初項 \\(a_1-2=1\\)、公比 \\(3\\) の等比数列だから "
             "\\(a_n-2=1\\cdot3^{n-1}\\)。よって \\(a_n=3^{n-1}+2\\)。",
      kotae="\\(a_n=3^{n-1}+2\\)。",
      hosoku="\\(a_1=3^0+2=3\\)、\\(a_2=3^1+2=5\\) で、"
             "漸化式 \\(a_2=3\\cdot3-4=5\\) と一致する。"
             "指数を \\(n\\) にすると \\(a_1=5\\) となり初項が合わなくなる。"),
  ])


# ---- 第5問 統計的な推測 ----------------------------------------------
D("math_unit", "数学II・B・C 第5問",
  "太郎さんは統計的な推測について復習している。必要に応じて、"
  "標準正規分布に従う確率変数 \\(Z\\) について \\(P(0\\le Z\\le 1)=0.3413\\)、"
  "\\(P(0\\le Z\\le 1.96)=0.4750\\) を用いてよい。次の問い(問1〜問5)に答えよ。"
  "各小問に必要な条件は問題文中に再掲してあるので、それぞれ単独で解答できる。",
  [
    Q("確率変数 \\(X\\) が二項分布 \\(B\\left(180,\\ \\dfrac{1}{3}\\right)\\) に従うとき、"
      "\\(X\\) の平均 (期待値) を求めよ。",
      "統計的な推測",
      ("\\(60\\)", Integer(60)),
      [("\\(45\\)", Integer(45)), ("\\(120\\)", Integer(120)), ("\\(30\\)", Integer(30))],
      lambda: Integer(180) * Rational(1, 3),
      hoshin="二項分布 \\(B(n,p)\\) の平均は \\(np\\)。",
      rishiki="\\(E(X)=np=180\\times\\dfrac13\\)。",
      keisan="\\(180\\times\\dfrac13=60\\)。",
      kotae="\\(60\\)。",
      hosoku="\\(1-p=\\dfrac23\\) を掛けると \\(120\\) になる。"
             "\\(p\\) は「1 回の試行で目的の事象が起こる確率」であることを確認して代入する。"),
    Q("確率変数 \\(X\\) が二項分布 \\(B\\left(180,\\ \\dfrac{1}{3}\\right)\\) に従うとき、"
      "\\(X\\) の標準偏差を求めよ。",
      "統計的な推測",
      ("\\(2\\sqrt{10}\\)", 2 * sqrt(10)),
      [("\\(40\\)", Integer(40)), ("\\(\\sqrt{60}\\)", sqrt(60)), ("\\(4\\sqrt{10}\\)", 4 * sqrt(10))],
      lambda: simplify(sqrt(Integer(180) * Rational(1, 3) * Rational(2, 3))),
      hoshin="二項分布の分散は \\(np(1-p)\\)。標準偏差はその正の平方根。",
      rishiki="\\(V(X)=180\\times\\dfrac13\\times\\dfrac23\\)、\\(\\sigma=\\sqrt{V(X)}\\)。",
      keisan="\\(V(X)=40\\)、\\(\\sigma=\\sqrt{40}=2\\sqrt{10}\\)。",
      kotae="\\(2\\sqrt{10}\\)。",
      hosoku="分散のまま答えると \\(40\\)、\\((1-p)\\) を掛け忘れると \\(\\sqrt{60}\\)。"
             "「分散か標準偏差か」を問題文で必ず確認する。"),
    Q("母標準偏差が \\(15\\) である母集団から大きさ \\(25\\) の標本を無作為に抽出するとき、"
      "標本平均 \\(\\overline{X}\\) の標準偏差を求めよ。",
      "統計的な推測",
      ("\\(3\\)", Integer(3)),
      [("\\(15\\)", Integer(15)), ("\\(0.6\\)", Rational(3, 5)), ("\\(5\\)", Integer(5))],
      lambda: simplify(Integer(15) / sqrt(Integer(25))),
      hoshin="標本平均の標準偏差 (標準誤差) は \\(\\dfrac{\\sigma}{\\sqrt n}\\)。",
      rishiki="\\(\\dfrac{\\sigma}{\\sqrt n}=\\dfrac{15}{\\sqrt{25}}\\)。",
      keisan="\\(\\sqrt{25}=5\\) より \\(\\dfrac{15}{5}=3\\)。",
      kotae="\\(3\\)。",
      hosoku="\\(n\\) の平方根を取らずに \\(\\dfrac{15}{25}\\) とすると \\(0.6\\) になる。"
             "標本サイズを 4 倍にすると標準誤差は半分になる、という関係も押さえておく。"),
    Q("母標準偏差が \\(15\\) の母集団から大きさ \\(25\\) の標本を無作為抽出したところ、"
      "標本平均が \\(52\\) であった。母平均 \\(m\\) に対する信頼度 95% の信頼区間として"
      "正しいものはどれか。必要なら \\(P(0\\le Z\\le 1.96)=0.4750\\) を用いよ。",
      "統計的な推測",
      ("\\(46.12\\le m\\le 57.88\\)", Tuple(Rational(1153, 25), Rational(1447, 25))),
      [("\\(49.00\\le m\\le 55.00\\)", Tuple(Integer(49), Integer(55))),
       ("\\(22.60\\le m\\le 81.40\\)", Tuple(Rational(113, 5), Rational(407, 5))),
       ("\\(50.04\\le m\\le 53.96\\)", Tuple(Rational(1251, 25), Rational(1349, 25)))],
      lambda: (lambda se: Tuple(Integer(52) - Rational(196, 100) * se,
                                Integer(52) + Rational(196, 100) * se))(Integer(15) / sqrt(Integer(25))),
      hoshin="信頼度 95% の信頼区間は "
             "\\(\\overline{X}-1.96\\dfrac{\\sigma}{\\sqrt n}\\le m\\le\\overline{X}+1.96\\dfrac{\\sigma}{\\sqrt n}\\)。"
             "先に標準誤差を出す。",
      rishiki="\\(\\dfrac{\\sigma}{\\sqrt n}=\\dfrac{15}{\\sqrt{25}}=3\\)、幅は \\(1.96\\times3\\)。",
      keisan="\\(1.96\\times3=5.88\\)。\\(52-5.88=46.12\\)、\\(52+5.88=57.88\\)。",
      kotae="\\(46.12\\le m\\le 57.88\\)。",
      hosoku="\\(\\sqrt n\\) で割り忘れると \\(52\\pm29.4\\) と極端に広い区間になる。"
             "区間は標本平均を中心に左右対称になることでも検算できる。"),
    Q("確率変数 \\(X\\) が正規分布 \\(N(50,\\ 10^2)\\) に従うとき、\\(P(40\\le X\\le 60)\\) を求めよ。"
      "ただし \\(P(0\\le Z\\le 1)=0.3413\\) とする。",
      "統計的な推測",
      ("\\(0.6826\\)", Rational(6826, 10000)),
      [("\\(0.3413\\)", Rational(3413, 10000)),
       ("\\(0.8413\\)", Rational(8413, 10000)),
       ("\\(0.9544\\)", Rational(9544, 10000))],
      lambda: 2 * Rational(3413, 10000),
      hoshin="\\(Z=\\dfrac{X-m}{\\sigma}\\) で標準化し、標準正規分布表の値に対応させる。",
      rishiki="\\(Z=\\dfrac{X-50}{10}\\)。\\(X=40\\) は \\(Z=-1\\)、\\(X=60\\) は \\(Z=1\\) に対応する。",
      keisan="標準正規分布は \\(Z=0\\) について左右対称なので "
             "\\(P(-1\\le Z\\le1)=2P(0\\le Z\\le1)=2\\times0.3413=0.6826\\)。",
      kotae="\\(0.6826\\)。",
      hosoku="片側だけで止めると \\(0.3413\\)、"
             "\\(P(Z\\le1)=0.5+0.3413=0.8413\\) と混同しやすい。"
             "求める範囲が平均をまたぐかどうかで、2 倍するか足すかが決まる。"),
  ])


# ---- 第6問 ベクトル --------------------------------------------------
# ★ 自己完結ゲート Layer A 対策: ベクトル記号を使う小問は成分を必ず stem に書く
#    (成分が解説にしかないと「解けない問題」として import 時に弾かれる)
D("math_unit", "数学II・B・C 第6問",
  "花子さんはベクトルの計算を復習している。次の問い(問1〜問5)に答えよ。"
  "各小問で扱うベクトルの成分はすべて問題文中に明示してあるので、それぞれ単独で解答できる。",
  [
    Q("平面上のベクトル \\(\\vec{a}=(2,\\ -1)\\)、\\(\\vec{b}=(3,\\ 4)\\) について、"
      "内積 \\(\\vec{a}\\cdot\\vec{b}\\) を求めよ。",
      "ベクトル",
      ("\\(2\\)", Integer(2)),
      [("\\(10\\)", Integer(10)), ("\\(-2\\)", Integer(-2)), ("\\(6\\)", Integer(6))],
      lambda: Integer(2 * 3 + (-1) * 4),
      hoshin="成分表示の内積は、対応する成分どうしの積の和 \\(a_1b_1+a_2b_2\\)。",
      rishiki="\\(\\vec{a}\\cdot\\vec{b}=2\\times3+(-1)\\times4\\)。",
      keisan="\\(6-4=2\\)。",
      kotae="\\(2\\)。",
      hosoku="第 2 成分の符号を落とすと \\(6+4=10\\) になる。"
             "内積の結果はベクトルではなく実数 (スカラー) である点も確認する。"),
    Q("平面上のベクトル \\(\\vec{a}=(2,\\ -1)\\)、\\(\\vec{b}=(3,\\ 4)\\) のなす角を \\(\\theta\\) とするとき、"
      "\\(\\cos\\theta\\) の値を求めよ。",
      "ベクトル",
      ("\\(\\dfrac{2\\sqrt{5}}{25}\\)", 2 * sqrt(5) / 25),
      [("\\(\\dfrac{\\sqrt{5}}{25}\\)", sqrt(5) / 25),
       ("\\(\\dfrac{2}{25}\\)", Rational(2, 25)),
       ("\\(\\dfrac{2\\sqrt{5}}{5}\\)", 2 * sqrt(5) / 5)],
      lambda: simplify(Integer(2) / (sqrt(Integer(2) ** 2 + Integer(1) ** 2)
                                     * sqrt(Integer(3) ** 2 + Integer(4) ** 2))),
      hoshin="\\(\\cos\\theta=\\dfrac{\\vec{a}\\cdot\\vec{b}}{|\\vec{a}||\\vec{b}|}\\)。"
             "内積と 2 つの大きさを別々に出してから代入する。",
      rishiki="\\(\\vec{a}\\cdot\\vec{b}=2\\times3+(-1)\\times4=2\\)、"
              "\\(|\\vec{a}|=\\sqrt{2^2+(-1)^2}=\\sqrt5\\)、\\(|\\vec{b}|=\\sqrt{3^2+4^2}=5\\)。",
      keisan="\\(\\cos\\theta=\\dfrac{2}{\\sqrt5\\times5}=\\dfrac{2}{5\\sqrt5}"
             "=\\dfrac{2\\sqrt5}{25}\\)。",
      kotae="\\(\\dfrac{2\\sqrt{5}}{25}\\)。",
      hosoku="分母に根号を残さず有理化してから選択肢と照合する。"
             "\\(|\\vec{b}|=\\sqrt{25}=5\\) を \\(\\sqrt5\\) と取り違えないこと。"),
    Q("平面上のベクトル \\(\\vec{a}=(2,\\ -1)\\)、\\(\\vec{b}=(3,\\ 4)\\) について、"
      "\\(|\\vec{a}+2\\vec{b}|\\) を求めよ。",
      "ベクトル",
      ("\\(\\sqrt{113}\\)", sqrt(113)),
      [("\\(\\sqrt{85}\\)", sqrt(85)), ("\\(15\\)", Integer(15)), ("\\(\\sqrt{145}\\)", sqrt(145))],
      lambda: simplify(sqrt((2 + 2 * 3) ** 2 + (-1 + 2 * 4) ** 2)),
      hoshin="先にベクトルの成分を計算し、そのあとで大きさを求める。",
      rishiki="\\(\\vec{a}+2\\vec{b}=(2+2\\cdot3,\\ -1+2\\cdot4)=(8,\\ 7)\\)。",
      keisan="\\(|\\vec{a}+2\\vec{b}|=\\sqrt{8^2+7^2}=\\sqrt{64+49}=\\sqrt{113}\\)。",
      kotae="\\(\\sqrt{113}\\)。",
      hosoku="\\(|\\vec{a}|+2|\\vec{b}|=\\sqrt5+10\\) のように"
             "「大きさを先に取ってから足す」のは誤り。大きさの計算は必ず成分をまとめた後。"),
    Q("平面上のベクトル \\(\\vec{a}=(x,\\ 3)\\)、\\(\\vec{b}=(4,\\ -2)\\) が垂直であるとき、"
      "\\(x\\) の値を求めよ。",
      "ベクトル",
      ("\\(\\dfrac{3}{2}\\)", Rational(3, 2)),
      [("\\(-\\dfrac{3}{2}\\)", Rational(-3, 2)), ("\\(6\\)", Integer(6)), ("\\(-6\\)", Integer(-6))],
      lambda: list(solveset(Eq(4 * x + 3 * (-2), 0), x, S.Reals))[0],
      hoshin="2 つのベクトルが垂直であることと、内積が \\(0\\) であることは同値。",
      rishiki="\\(\\vec{a}\\cdot\\vec{b}=x\\times4+3\\times(-2)=4x-6=0\\)。",
      keisan="\\(4x=6\\) より \\(x=\\dfrac32\\)。",
      kotae="\\(\\dfrac{3}{2}\\)。",
      hosoku="平行条件 \\(a_1b_2-a_2b_1=0\\) と取り違えると "
             "\\(-2x-12=0\\) から \\(x=-6\\) になってしまう。"
             "垂直は内積、平行は成分の比 (たすき掛けの差) と区別する。"),
    Q("空間内の 2 点 \\(A(1,\\ 2,\\ 3)\\)、\\(B(3,\\ -1,\\ 4)\\) について、"
      "\\(\\left|\\overrightarrow{AB}\\right|\\) を求めよ。",
      "ベクトル",
      ("\\(\\sqrt{14}\\)", sqrt(14)),
      [("\\(\\sqrt{26}\\)", sqrt(26)), ("\\(\\sqrt{6}\\)", sqrt(6)), ("\\(14\\)", Integer(14))],
      lambda: simplify(sqrt((3 - 1) ** 2 + (-1 - 2) ** 2 + (4 - 3) ** 2)),
      hoshin="\\(\\overrightarrow{AB}=\\) (終点 B の座標) \\(-\\) (始点 A の座標) を成分で出してから大きさを求める。",
      rishiki="\\(\\overrightarrow{AB}=(3-1,\\ -1-2,\\ 4-3)=(2,\\ -3,\\ 1)\\)。",
      keisan="\\(\\left|\\overrightarrow{AB}\\right|=\\sqrt{2^2+(-3)^2+1^2}"
             "=\\sqrt{4+9+1}=\\sqrt{14}\\)。",
      kotae="\\(\\sqrt{14}\\)。",
      hosoku="引く向きを逆にしても大きさは変わらない。"
             "座標を足して \\((4,\\ 1,\\ 7)\\) としてしまうと \\(\\sqrt{66}\\) と全く別の値になる。"),
  ])


# =====================================================================
# 検証 → JSON 組み立て
# =====================================================================

def _answer_positions():
    """正解位置を大問ごとに決める (answer_positions.assign)。

    大問ごとに 0..3 の順列を選び perm[j%4] で配るので、
    隣り合う小問が同じ番号になることが構造的に起きず (最大連続 1)、
    1 大問内の各番号の出現も ⌊n/4⌋〜⌈n/4⌉ に収まる。
    順列は全体の分布が最も平らになるものを貪欲に選ぶので、全体の均等も保たれる。"""
    sizes = [(dm["group"], len(dm["subqs"])) for dm in DAIMON]
    per_daimon, total = answer_positions.assign(sizes, SOURCE)
    return {(g, i): p for g, seq in per_daimon.items() for i, p in enumerate(seq)}, total


def build():
    rows = []
    errors = []
    total_sub = 0
    positions, pos_total = _answer_positions()

    for dm in DAIMON:
        subs = []
        for qi, sq in enumerate(dm["subqs"]):
            tag = f'{dm["group"]} 問{qi + 1}'
            c_latex, c_val = sq["correct"]

            # (1) 独立計算との一致 (正解を手入力しない原則)
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

            # (3) 解説フォーマット「方針→立式→計算→答え→補足」(server/main.py 理系プロンプト準拠)
            body = {"方針": sq["hoshin"], "立式": sq["rishiki"], "計算": sq["keisan"],
                    "答え": sq["kotae"], "補足": sq["hosoku"]}
            for name in SECTIONS:
                if not (body[name] or "").strip():
                    errors.append(f'{tag}: 解説の「{name}」が空 (5 セクション必須)')
            # 「答え:」に正答の選択肢テキストが入っていること = 解説と選択肢の食い違い検出
            if c_latex not in body["答え"]:
                errors.append(f'{tag}: 「答え:」に正答「{c_latex}」が含まれていない')
            explanation = "\n".join(f'{name}: {body[name]}' for name in SECTIONS)
            if len(explanation.splitlines()) < 3:
                errors.append(f'{tag}: 解説が 3 行未満')

            # (4) 正解位置を md5 順の round-robin で 0..3 に均等配分
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
                "explanation": explanation,
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

    dist = {0: 0, 1: 0, 2: 0, 3: 0}
    for r in rows:
        for q in r["question_data"]["questions"]:
            dist[q["answer"]] += 1

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"questions": rows, "skip_full": False}, f, ensure_ascii=False, indent=1)

    print(f"✅ 検証 OK: {len(rows)} 大問 / {total_sub} 小問")
    for pk in ("math_unit",):
        cnt = sum(1 for r in rows if r["part_key"] == pk)
        sub = sum(len(r["question_data"]["questions"]) for r in rows if r["part_key"] == pk)
        print(f"   {pk}: {cnt} 大問 / {sub} 小問")
    print(f"   解説: 全 {total_sub} 問が「方針→立式→計算→答え→補足」の 5 セクション")
    print(f"   正解位置の分布: {dist}")
    print(f"   → {os.path.relpath(OUT)}")


if __name__ == "__main__":
    build()
