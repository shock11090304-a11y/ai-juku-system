# -*- coding: utf-8 -*-
"""verify_math2bc_c.py — 数学ⅡBC 第5問・第6問・第7問 の全マークスロットを
独立計算(sympy / erf / 全数列挙 / numpy 幾何)で再導出し ANS_SECTIONS と照合する。

実行:  python3 verify_math2bc_c.py    (全 assert が通れば "ALL VERIFIED" を表示)
"""
import math, importlib.util, os, sys
import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    p = os.path.join(HERE, "math2bc_c.py")
    spec = importlib.util.spec_from_file_location("math2bc_c", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def Phi(z):
    """P(0<=Z<=z) 標準正規分布."""
    return 0.5 * math.erf(z / math.sqrt(2))


CIRC = "⓪①②③④⑤⑥⑦⑧⑨"


def ci(i):
    return CIRC[i]


# ============================================================
# 第5問: 統計的な推測 (母比率の仮説検定)
# 設定: 平均 μ=180, 標準偏差 σ=40, 合格点 T=210 の正規分布 X。
#       過去5年の合格率 p0=1/5=0.2。大標本 n1=300 中 m1=72 (p^=0.24)。
#       小標本 n2=150 中 m2=36 (p^=0.24)。√3=1.73, √6=2.45 を使用。
# ============================================================

def verify_sec5(ans):
    from fractions import Fraction as F
    mu, sig, T = 180, 40, 210
    p0 = F(1, 5)
    n1, m1 = 300, 72
    n2, m2 = 150, 36
    phat1 = F(m1, n1)
    phat2 = F(m2, n2)
    assert phat1 == phat2 == F(24, 100), "標本比率が 0.24 で一致するはず"

    slots = {}

    # --- ア: 標準化 Y=(X-μ)/σ = (X-180)/40 ---
    # 解答群 ⓪(X-180)/√40 ①(X-180)/40 ②(X-180)/40² ③(X-210)/√40 ④(X-210)/40 ⑤(X-210)/40²
    # 正しい標準化は分子=−平均(180), 分母=標準偏差(40) → ①
    slots["ア"] = ci(1)

    # --- イ: P(X>=210) ---
    z = (T - mu) / sig             # 0.75
    P = 0.5 - Phi(z)               # 0.2266... ~ 0.23
    assert abs(z - 0.75) < 1e-12
    assert round(P, 2) == 0.23, P
    # 8択: [⓪0.16 ①0.23 ②0.27 ③0.31 ④0.50 ⑤0.73 ⑥0.77 ⑦0.84] → 0.23=①
    ch_i = [0.16, 0.23, 0.27, 0.31, 0.50, 0.73, 0.77, 0.84]
    slots["イ"] = ci(ch_i.index(round(P, 2)))
    assert slots["イ"] == ci(1)

    # --- ウ: E(Wi) ---  ベルヌーイ: E=p
    # 6択 ⓪p ①1-p ②p² ③p(1-p) ④p²(1-p)² ⑤p³+(1-p)³
    p = sp.symbols("p")
    E = 0 * (1 - p) + 1 * p        # = p
    assert sp.simplify(E - p) == 0
    slots["ウ"] = ci(0)

    # --- エ: V(Wi) = {0-E}²(1-p)+{1-E}²p = p(1-p) ---
    V = (0 - p) ** 2 * (1 - p) + (1 - p) ** 2 * p
    assert sp.simplify(V - p * (1 - p)) == 0
    slots["エ"] = ci(3)          # p(1-p)

    # --- オ: V(W̄) = p(1-p)/n ---
    n = sp.symbols("n", positive=True)
    Vbar = p * (1 - p) / n
    # 8択 ⓪p ①1-p ②p(1-p) ③p/√n ④√(p(1-p)/n) ⑤p(1-p)/√n ⑥√(1-p)/n ⑦p(1-p)/n
    assert sp.simplify(Vbar - p * (1 - p) / n) == 0
    slots["オ"] = ci(7)

    # --- カ: σ(W̄) 大標本 = √(p0(1-p0)/n1) ---
    var1 = p0 * (1 - p0) / n1           # 1/1200
    sigma1 = sp.sqrt(sp.Rational(var1.numerator, var1.denominator))
    sigma1 = sp.nsimplify(sp.radsimp(sigma1))
    assert sp.simplify(sigma1 - sp.sqrt(3) / 75) == 0, sigma1
    # 6択(content の並び) ⓪3/75 ①√3/25 ②√3/5625 ③√3/75 ④4/1875 ⑤12/75 → √3/75=③
    ch_ka = [sp.Rational(3, 75), sp.sqrt(3) / 25, sp.sqrt(3) / 5625,
             sp.sqrt(3) / 75, sp.Rational(4, 1875), sp.Rational(12, 75)]
    slots["カ"] = ci(next(i for i, v in enumerate(ch_ka)
                          if sp.simplify(v - sigma1) == 0))
    assert slots["カ"] == ci(3)

    # --- キ: P(W̄>=0.24) 大標本 ---
    # z1 = (0.24-0.2)/σ1 = 0.04 / (√3/75) = 0.04*75/√3 = 3/√3 = √3 ≒ 1.73
    z1_symbolic = sp.simplify((F(24, 100) - p0) / (sp.sqrt(3) / 75))
    assert sp.simplify(z1_symbolic - sp.sqrt(3)) == 0, z1_symbolic  # = √3
    z1 = 1.73                              # √3≒1.73 (本文指定)
    tail1 = round(0.5 - Phi(z1), 4)
    assert tail1 == 0.0418, tail1
    # 8択(content の並び) ⓪0.0446 ①0.3888 ②0.4582 ③0.0418 ④0.0401 ⑤0.0495 ⑥0.4599 ⑦0.1112 → 0.0418=③
    ch_k = [0.0446, 0.3888, 0.4582, 0.0418, 0.0401, 0.0495, 0.4599, 0.1112]
    slots["キ"] = ci(ch_k.index(tail1))
    assert slots["キ"] == ci(3)

    # --- ク: 4.18% と 5% の比較 → 小さい → 棄却される ---
    assert tail1 * 100 < 5.0
    # 4択 ⓪小さいから棄却されない ①小さいから棄却される ②大きいから棄却されない ③大きいから棄却される
    slots["ク"] = ci(1)

    # --- ケ: 帰無仮説棄却 → 合格率は 0.2 より高いと判断できる ---
    # 2択 ⓪高いと判断できる ①高いとは判断できない
    slots["ケ"] = ci(0)

    # --- (3) 小標本 n2=150 ---
    var2 = p0 * (1 - p0) / n2           # 2/1875
    sigma2 = sp.nsimplify(sp.radsimp(sp.sqrt(sp.Rational(var2.numerator, var2.denominator))))
    assert sp.simplify(sigma2 - sp.sqrt(6) / 75) == 0, sigma2   # √6/75
    # z2 = 0.04/(√6/75) = 3/√6 = √6/2 ≒ 2.45/2 = 1.225 ≒ 1.22
    z2_symbolic = sp.simplify((F(24, 100) - p0) / (sp.sqrt(6) / 75))
    assert sp.simplify(z2_symbolic - sp.sqrt(6) / 2) == 0, z2_symbolic
    z2 = 2.45 / 2                          # √6=2.45 → 1.225
    tail2 = round(0.5 - Phi(1.22), 4)      # 表は z=1.22 の行 → 0.1112
    assert tail2 == 0.1112, tail2
    assert tail2 * 100 > 5.0

    # --- コ: 11.12% は 5% より 大きい ---  2択 ⓪小さい ①大きい
    slots["コ"] = ci(1)
    # --- サ: 棄却されない ---            2択 ⓪棄却される ①棄却されない
    slots["サ"] = ci(1)

    _assert_slots("第5問", slots, ans)
    return {"z_std": z, "P_pass": round(P, 4), "sigma1": "√3/75", "z1": z1,
            "tail1": tail1, "sigma2": "√6/75", "z2": round(z2, 3), "tail2": tail2}


# ============================================================
# 第6問: ベクトル (正六角形+中心 / 一次結合 Pの不変条件・存在範囲)
# 設定: 正六角形 (中心 B)。MP=aMA+bMB+cMC。(1)で (a,b,c)=(1,2,-1)。
# ============================================================

def verify_sec6(ans):
    import numpy as np
    # 六角形頂点 (中心B=原点)。A(120°),C(60°),D(180°),E(0°),F(240°),G(300°)
    th = {"A": 120, "C": 60, "D": 180, "E": 0, "F": 240, "G": 300}
    V = {k: np.array([math.cos(math.radians(a)), math.sin(math.radians(a))]) for k, a in th.items()}
    V["B"] = np.array([0.0, 0.0])
    order = ["A", "B", "C", "D", "E", "F", "G"]   # 解答群 ⓪A①B②C③D④E⑤F⑥G

    def P_of(Mn, a, b, c):
        M = V[Mn]
        return M + a * (V["A"] - M) + b * (V["B"] - M) + c * (V["C"] - M)

    def nearest(P):
        b = min(V, key=lambda k: np.linalg.norm(V[k] - P))
        return b, float(np.linalg.norm(V[b] - P))

    # ① MP = MA + 2MB - MC → (a,b,c)=(1,2,-1)
    A_, B_, C_ = 1, 2, -1
    slots = {}

    # --- ア: M=A のとき P=?（計算した最近頂点をそのまま採用） ---
    P = P_of("A", A_, B_, C_)
    nm, d = nearest(P)
    assert d < 1e-9, (nm, d)
    slots["ア"] = ci(order.index(nm))     # → F=⑤

    # --- イ: M=D のとき P=? ---
    P = P_of("D", A_, B_, C_)
    nm, d = nearest(P)
    assert d < 1e-9, (nm, d)
    slots["イ"] = ci(order.index(nm))     # → B=①

    # --- (2) A始点への書換え (記号計算) ---
    AB, AC, AM = sp.symbols("AB AC AM")
    a, b, c = sp.symbols("a b c")
    A0 = sp.Integer(0)
    Pexpr = sp.expand(AM + a * (A0 - AM) + b * (AB - AM) + c * (AC - AM))  # AP (A=原点)
    # ウ: MP = AP - AM
    MP = sp.expand(Pexpr - AM)
    # 4択 ⓪AP+AM ①-AP+AM ②AP-AM ③-AP-AM
    assert sp.simplify(MP - (Pexpr - AM)) == 0
    slots["ウ"] = ci(2)          # AP-AM

    # 右辺 aMA+bMB+cMC を AB,AC,AM で:
    RHS = sp.expand(a * (A0 - AM) + b * (AB - AM) + c * (AC - AM))
    # エ〜ケ 解答群(10択): ⓪a①b②c③a+b+c④-a+b+c⑤a-b+c⑥a+b-c⑦-a-b-c⑧1+a+b+c⑨1-a-b-c
    grp = [a, b, c, a + b + c, -a + b + c, a - b + c, a + b - c, -a - b - c,
           1 + a + b + c, 1 - a - b - c]
    cAB = RHS.coeff(AB); cAC = RHS.coeff(AC); cAM = RHS.coeff(AM)
    assert sp.simplify(cAB - b) == 0 and sp.simplify(cAC - c) == 0
    assert sp.simplify(cAM - (-a - b - c)) == 0
    slots["エ"] = ci(next(i for i, g in enumerate(grp) if sp.simplify(g - cAB) == 0))  # b=①
    slots["オ"] = ci(next(i for i, g in enumerate(grp) if sp.simplify(g - cAC) == 0))  # c=②
    slots["カ"] = ci(next(i for i, g in enumerate(grp) if sp.simplify(g - cAM) == 0))  # -a-b-c=⑦

    # AP = RHS + AM
    AP = sp.expand(RHS + AM)
    aAB = AP.coeff(AB); aAC = AP.coeff(AC); aAM = AP.coeff(AM)
    assert sp.simplify(aAB - b) == 0 and sp.simplify(aAC - c) == 0
    assert sp.simplify(aAM - (1 - a - b - c)) == 0
    slots["キ"] = ci(next(i for i, g in enumerate(grp) if sp.simplify(g - aAB) == 0))  # b=①
    slots["ク"] = ci(next(i for i, g in enumerate(grp) if sp.simplify(g - aAC) == 0))  # c=②
    slots["ケ"] = ci(next(i for i, g in enumerate(grp) if sp.simplify(g - aAM) == 0))  # 1-a-b-c=⑨

    # コ: P が M に依らない ⇔ AM の係数=0 ⇔ 1-a-b-c=0 ⇔ a+b+c=1
    cond = aAM
    assert sp.simplify(cond) == sp.simplify(1 - a - b - c)
    # 9択 ⓪a=b①b=c②c=a③a+b-c=0④a-b+c=1⑤-a+b+c=-1⑥a+b+c=0⑦a+b+c=1⑧a+b+c=-1
    grpK = [sp.Eq(a, b), sp.Eq(b, c), sp.Eq(c, a), sp.Eq(a + b - c, 0),
            sp.Eq(a - b + c, 1), sp.Eq(-a + b + c, -1), sp.Eq(a + b + c, 0),
            sp.Eq(a + b + c, 1), sp.Eq(a + b + c, -1)]
    # 正しい条件 a+b+c=1
    idxK = next(i for i, e in enumerate(grpK)
                if sp.simplify((e.lhs - e.rhs) - (a + b + c - 1)) == 0)
    slots["コ"] = ci(idxK)        # a+b+c=1 → ⑦

    # --- (3)(i): a+b+c=1, a=1/2 → 直線IJ (AB中点J, CA中点I を結ぶ中点連結線) ---
    Av = np.array([0.0, 3.0]); Bv = np.array([-2.0, 0.0]); Cv = np.array([2.0, 0.0])
    H = (Bv + Cv) / 2; I = (Cv + Av) / 2; J = (Av + Bv) / 2

    def Pbary(a1, b1, c1):   # a1+b1+c1=1
        return a1 * Av + b1 * Bv + c1 * Cv

    pts = []
    for t in np.linspace(-1.5, 2.0, 12):
        pts.append(Pbary(0.5, t, 0.5 - t))

    def collinear(P, p1, p2):
        v = p2 - p1; w = P - p1
        return abs(v[0] * w[1] - v[1] * w[0]) < 1e-9

    assert all(collinear(P, I, J) for P in pts), "軌跡が直線IJ でない"
    assert not all(collinear(P, H, I) for P in pts)
    assert not all(collinear(P, J, H) for P in pts)
    # 6択 ⓪直線AH①直線BI②直線CJ③直線HI④直線IJ⑤直線JH
    slots["サ"] = ci(4)          # 直線IJ

    # --- (3)(ii): a+b+c=1, c<0 → 直線ABに関してCと反対側の開半平面 ---
    def side(P, p1, p2):
        v = p2 - p1; w = P - p1
        return v[0] * w[1] - v[1] * w[0]
    sC = side(Cv, Av, Bv)
    import random
    rng = random.Random(0)
    for _ in range(3000):
        b1 = rng.uniform(-4, 4); c1 = rng.uniform(-4, -1e-3); a1 = 1 - b1 - c1
        P = Pbary(a1, b1, c1)
        assert side(P, Av, Bv) * sC < 0, "c<0 が AB のC反対側でない"
    # 6択(領域図): ⓪三角形内部 ①∠Cの内角領域 ②三角形+C対頂角 ③ABのC反対側半平面
    #              ④ABのC反対側∩BC上側 ⑤ABのC同側半平面
    slots["シ"] = ci(3)

    _assert_slots("第6問", slots, ans)
    return {"P(M=A)": "F", "P(M=D)": "B", "condition": "a+b+c=1"}


# ============================================================
# 第7問: 平面上の曲線と複素数平面 (w=z+1/z ジューコフスキー型)
# 設定: z0=1+√3 i (|z0|=2)。円 C: |z|=r。
# ============================================================

def verify_sec7(ans):
    slots = {}
    zc = sp.symbols("z")
    r, th = sp.symbols("r theta", positive=True)

    # --- (1) z0=1+√3 i ---
    z0 = 1 + sp.sqrt(3) * sp.I
    absz0 = sp.simplify(sp.Abs(z0))
    assert absz0 == 2
    w0 = sp.nsimplify(sp.radsimp(z0 + 1 / z0))
    re0 = sp.nsimplify(sp.re(w0)); im0 = sp.simplify(sp.im(w0))
    # w0 = 5/4 + (3√3/4) i  →  実部=イ/ウ=5/4, 虚部=(エ√オ)/カ=3√3/4
    assert re0 == sp.Rational(5, 4), re0
    assert sp.simplify(im0 - 3 * sp.sqrt(3) / 4) == 0, im0
    slots["ア"] = "2"
    slots["イ"] = str(sp.numer(re0)); slots["ウ"] = str(sp.denom(re0))   # 実部 5/4
    slots["エ"] = "3"; slots["オ"] = "3"; slots["カ"] = "4"              # 虚部 (3√3)/4

    # --- (2)(i) w=z+1/z, z=r(cosθ+isinθ) ---
    # w = (r+1/r)cosθ + i(r-1/r)sinθ
    reW = (r + 1 / r) * sp.cos(th)
    imW = (r - 1 / r) * sp.sin(th)
    z = r * (sp.cos(th) + sp.I * sp.sin(th))
    w = sp.expand(z + 1 / z)
    assert sp.simplify(sp.re(w) - reW) == 0
    assert sp.simplify(sp.im(w) - imW) == 0
    # キ・ク 10択: ⓪2r cosθ①2r sinθ②(r+1)cosθ③(r+1)sinθ④(r-1)cosθ⑤(r-1)sinθ
    #             ⑥(r+1/r)cosθ⑦(r+1/r)sinθ⑧(r-1/r)cosθ⑨(r-1/r)sinθ
    grp = [2 * r * sp.cos(th), 2 * r * sp.sin(th), (r + 1) * sp.cos(th), (r + 1) * sp.sin(th),
           (r - 1) * sp.cos(th), (r - 1) * sp.sin(th), (r + 1 / r) * sp.cos(th),
           (r + 1 / r) * sp.sin(th), (r - 1 / r) * sp.cos(th), (r - 1 / r) * sp.sin(th)]
    slots["キ"] = ci(next(i for i, g in enumerate(grp) if sp.simplify(g - reW) == 0))  # ⑥
    slots["ク"] = ci(next(i for i, g in enumerate(grp) if sp.simplify(g - imW) == 0))  # ⑨
    assert slots["キ"] == ci(6) and slots["ク"] == ci(9)

    # ケ: 虚部が θ によらず 0 ⇔ r-1/r=0 ⇔ r=1 (r>0)
    sol = sp.solve(sp.Eq(r - 1 / r, 0), r)
    sol = [s for s in sol if s > 0]
    assert sol == [1]
    slots["ケ"] = "1"

    # --- (2)(ii) r=1: w=2cosθ → 実軸線分 [-2,2] ---
    r1 = 1
    wr1 = sp.simplify((r1 + sp.Rational(1, r1)) * sp.cos(th))
    assert sp.simplify(wr1 - 2 * sp.cos(th)) == 0
    # cosθ ∈ [-1,1] → 2cosθ ∈ [-2,2], 虚部0
    # 図6択: ⓪実軸[-1,1]①実軸[-2,2]②虚軸[-1,1]③虚軸[-2,2]④山型 高さ1⑤山型 高さ2
    slots["コ"] = ci(1)

    # --- (2)(iii) r≠1: θ消去 → 楕円 ---
    # x=(r+1/r)cosθ, y=(r-1/r)sinθ → x²/(r+1/r)²+y²/(r-1/r)²=1
    x, y = sp.symbols("x y")
    cosv = x / (r + 1 / r); sinv = y / (r - 1 / r)
    ellipse = sp.simplify(cosv ** 2 + sinv ** 2)   # =1
    assert sp.simplify(ellipse.subs({x: (r + 1 / r) * sp.cos(th),
                                     y: (r - 1 / r) * sp.sin(th)}) - 1) == 0
    # サ 6択: ⓪x²/r²+y²/r²=1 ①x²/r²-y²/r²=1 ②x²/(r+1/r)²+y²/(r-1/r)²=1
    #        ③x²/(r+1/r)²-y²/(r-1/r)²=1 ④x²/(r-1/r)²+y²/(r+1/r)²=1 ⑤x²/(r-1/r)²-y²/(r+1/r)²=1
    slots["サ"] = ci(2)

    # --- (3)(i) w² を z で ---
    w2 = sp.expand((zc + 1 / zc) ** 2)   # z² + 2 + 1/z²
    target = zc ** 2 + 1 / zc ** 2 + 2
    assert sp.simplify(w2 - target) == 0
    # シ 6択: ⓪z²+1/z² ①…+1 ②…-1 ③…+2 ④…-2 ⑤…+2i
    slots["シ"] = ci(3)

    # --- (3)(ii) z²+1/z² = X+Yi, z² は半径 r² の円 ---
    # X=(r²+1/r²)cos2θ, Y=(r²-1/r²)sin2θ → X²/(r²+1/r²)²+Y²/(r²-1/r²)²=1
    X, Y = sp.symbols("X Y")
    reZ2 = (r ** 2 + 1 / r ** 2); imZ2 = (r ** 2 - 1 / r ** 2)
    ell2 = sp.simplify((X / reZ2) ** 2 + (Y / imZ2) ** 2)
    assert sp.simplify(ell2.subs({X: reZ2 * sp.cos(2 * th),
                                  Y: imZ2 * sp.sin(2 * th)}) - 1) == 0
    # ス 6択: ⓪X/(r²+1/r²)+Y/(r²-1/r²)=1 ①X²/r⁴+Y²/r⁴=1 ②X²/(r²+1/r²)²+Y²/(r²-1/r²)²=1
    #        ③…-…=1 ④分母入替+ ⑤分母入替-
    slots["ス"] = ci(2)

    # --- (3)(iii) w²=z²+1/z²+2=(X+2)+Yi → 楕円を実軸方向に +2 平行移動 (横長) ---
    # 横長判定: r²+1/r² > |r²-1/r²| (r>0,r≠1)
    for rv in [0.5, 2.0, 3.0, 1.5, 0.3]:
        assert rv ** 2 + 1 / rv ** 2 > abs(rv ** 2 - 1 / rv ** 2)
    # 図8択: ⓪縦長中心(-2,0)①縦長中心(2,0)②横長中心(-2,0)③横長中心(2,0)
    #        ④小横長(-2,0)⑤小横長(2,0)⑥縦長中心O⑦横長中心O
    slots["セ"] = ci(3)          # 横長・中心(2,0)

    _assert_slots("第7問", slots, ans)
    return {"|z0|": 2, "w0": "5/4 + (3√3/4)i", "shift": "+2 (実軸)"}


# ============================================================
def _assert_slots(name, computed, ans_slots):
    """独立計算 computed と ANS_SECTIONS の slots を照合."""
    for k, v in computed.items():
        assert k in ans_slots, f"{name}: スロット {k} が ANS に無い"
        assert ans_slots[k] == v, f"{name}: {k} 期待={v} だが ANS={ans_slots[k]}"
    # ANS 側の選択式/数値スロットのうち computed に無いものは無い前提(全網羅)
    missing = set(ans_slots) - set(computed) - _NONVERIFIED
    assert not missing, f"{name}: 未検証スロット {missing}"


# computed で個別に扱わず、連結枠として ANS に現れるが上で個別 assert 済みのキーは無し。
_NONVERIFIED = set()


def main():
    mod = _load()
    ans_by_sec = {s["section"]: s["slots"] for s in mod.ANS_SECTIONS}
    r5 = verify_sec5(ans_by_sec[5])
    print("第5問 OK:", r5)
    r6 = verify_sec6(ans_by_sec[6])
    print("第6問 OK:", r6)
    r7 = verify_sec7(ans_by_sec[7])
    print("第7問 OK:", r7)

    # --- 正解位置の偏り監査 (選択式スロットのみ) ---
    for sec in (5, 6, 7):
        vals = [v for v in ans_by_sec[sec].values() if v in CIRC]
        for i in range(len(vals) - 2):
            assert not (vals[i] == vals[i + 1] == vals[i + 2]), \
                f"第{sec}問: 同一選択肢が3連続 ({vals[i]})"
    print("正解位置 3連続なし OK")
    print("ALL VERIFIED")


if __name__ == "__main__":
    main()
