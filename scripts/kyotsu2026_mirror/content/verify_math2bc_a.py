# -*- coding: utf-8 -*-
"""verify_math2bc_a.py: math2bc_a.py の全マークスロットを sympy / 全数列挙 / 領域サンプリングで
独立に導出して assert する。

- 第1問(図形と方程式): 円の標準形・半径・距離を sympy で導出。半平面帰属は L に代入。
  ③⑤の領域は 26万点サンプリングで「レンズ/和集合」と一致することを厳密確認。
  9図の各インデックスの領域も同サンプリングで一意特定し、セ/ソ を機械決定。
- 第2問(三角関数): 加法定理・和積・最大値を sympy で導出。全選択肢を数式一致で照合。

実行: python3 verify_math2bc_a.py  → 全pass なら 'ALL VERIFY PASS'。
"""
import os
import sys
import math
import random
import importlib.util
import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
CIRC = "⓪①②③④⑤⑥⑦⑧⑨"


def load():
    p = os.path.join(HERE, "math2bc_a.py")
    spec = importlib.util.spec_from_file_location("m2a", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def slots_of(mod, sec):
    for s in mod.ANS_SECTIONS:
        if s["section"] == sec:
            return s["slots"]
    raise KeyError(sec)


def ci(i):
    return CIRC[i]


def main():
    mod = load()
    fails = []

    def ck(name, got, exp):
        if str(got) != str(exp):
            fails.append(f"[{name}] answer_key={exp!r} but computed={got!r}")
        else:
            print(f"  OK {name} = {got}")

    x, y = sp.symbols('x y', real=True)

    # =========================================================
    # 第1問 図形と方程式
    # =========================================================
    print("== 第1問 ==")
    S1 = slots_of(mod, 1)

    S = x**2 + y**2 - 3*x - 8*y
    L = 5*x + 2*y - 14
    eq1 = sp.expand(S + L)   # C1
    eq2 = sp.expand(S - L)   # C2

    def circle(expr):
        p = sp.Poly(expr, x, y)
        A = p.coeff_monomial(x)
        B = p.coeff_monomial(y)
        Cc = p.coeff_monomial(1)
        cx = sp.Rational(-A, 2)
        cy = sp.Rational(-B, 2)
        r2 = cx**2 + cy**2 - Cc
        return cx, cy, r2

    cx1, cy1, r1sq = circle(eq1)
    cx2, cy2, r2sq = circle(eq2)

    # アイ, ウ: C1 中心 (-1,3)
    ck("アイ", ("−" + str(abs(cx1))) if cx1 < 0 else str(cx1), S1["ア"] + S1["イ"])
    ck("ウ", cy1, S1["ウ"])
    assert (cx1, cy1) == (-1, 3), (cx1, cy1)
    assert (cx2, cy2) == (4, 5), (cx2, cy2)

    # エ√オ = r1 = 2√6 ; カ√キ = r2 = 3√3
    def ksqrt(r2):
        r2 = int(r2)
        k = 1
        m = r2
        d = 2
        while d * d <= m:
            while m % (d * d) == 0:
                m //= d * d
                k *= d
            d += 1
        return k, m

    k1, m1 = ksqrt(r1sq)   # 2,6
    k2, m2 = ksqrt(r2sq)   # 3,3
    assert r1sq == 24 and r2sq == 27, (r1sq, r2sq)
    ck("エ", k1, S1["エ"]); ck("オ", m1, S1["オ"])
    ck("カ", k2, S1["カ"]); ck("キ", m2, S1["キ"])

    # √クケ = d , d^2 = 29
    d2 = (cx1 - cx2)**2 + (cy1 - cy2)**2
    assert d2 == 29, d2
    ck("クケ", str(d2), S1["ク"] + S1["ケ"])

    # 2点で交わる条件確認
    r1 = math.sqrt(float(r1sq)); r2 = math.sqrt(float(r2sq)); d = math.sqrt(float(d2))
    assert abs(r1 - r2) < d < r1 + r2, (abs(r1 - r2), d, r1 + r2)

    # コ,サ,シ: 半平面帰属。D:{L>=0}=index0, E:{L<0}=index1 (解答群 [D, E])
    def side_index(px, py):
        v = float(L.subs({x: px, y: py}))
        return 0 if v >= 0 else 1   # 0->D, 1->E
    ck("コ", ci(side_index(0, 0)), S1["コ"])         # O -> E -> ①
    ck("サ", ci(side_index(cx1, cy1)), S1["サ"])      # C1中心 -> E -> ①
    ck("シ", ci(side_index(cx2, cy2)), S1["シ"])      # C2中心 -> D -> ⓪
    # 値の直接確認
    assert float(L.subs({x: 0, y: 0})) == -14
    assert float(L.subs({x: -1, y: 3})) == -13
    assert float(L.subs({x: 4, y: 5})) == 16

    # ス: 論理選択(6択)。正しい含意は「C1かつC2 ⇒ ℓ上」= index2。
    inter = sp.solve([eq1, eq2], [x, y], dict=True)
    assert len(inter) == 2, inter
    for pt in inter:
        assert sp.simplify(L.subs(pt)) == 0, ("2交点がℓ上でない", pt)
    # 逆向き(⓪①)が偽であることの反例: ℓ上の点でC1にもC2にも乗らないものが存在
    xt = sp.Rational(0)
    yt = sp.Rational(14, 2)  # (0,7) on ℓ
    assert sp.simplify(L.subs({x: xt, y: yt})) == 0
    on_c1 = sp.simplify(eq1.subs({x: xt, y: yt})) == 0
    on_c2 = sp.simplify(eq2.subs({x: xt, y: yt})) == 0
    assert not (on_c1 or on_c2), "ℓ上の(0,7)はC1にもC2にも乗らない(⓪①は偽)"
    ck("ス", ci(2), S1["ス"])

    # セ, ソ: 9図から領域を機械決定。
    C1c = (-1.0, 3.0)
    C2c = (4.0, 5.0)

    def inC1(px, py): return (px - C1c[0])**2 + (py - C1c[1])**2 < 24.0
    def inC2(px, py): return (px - C2c[0])**2 + (py - C2c[1])**2 < 27.0
    def Lf(px, py): return 5.0 * px + 2.0 * py - 14.0
    def above(px, py): return Lf(px, py) > 0.0  # L>0 => 上側(D側)

    def region_of_index(idx):
        if idx == 0: return lambda px, py: inC1(px, py) and inC2(px, py)            # lens
        if idx == 1: return lambda px, py: inC1(px, py)                             # C1
        if idx == 2: return lambda px, py: inC2(px, py)                             # C2
        if idx == 3: return lambda px, py: (inC1(px, py) or inC2(px, py)) and not (inC1(px, py) and inC2(px, py))  # symdiff
        if idx == 4: return lambda px, py: inC1(px, py) or inC2(px, py)             # union
        if idx == 5: return lambda px, py: inC1(px, py) and inC2(px, py) and above(px, py)        # lens upper
        if idx == 6: return lambda px, py: inC1(px, py) and inC2(px, py) and (not above(px, py))  # lens lower
        if idx == 7: return lambda px, py: inC1(px, py) and (not above(px, py))     # C1 lower cap
        if idx == 8: return lambda px, py: inC2(px, py) and above(px, py)           # C2 upper cap
        raise ValueError(idx)

    def region3(px, py):
        Sv = px**2 + py**2 - 3.0 * px - 8.0 * py
        return Sv + abs(Lf(px, py)) < 0.0

    def region5(px, py):
        Sv = px**2 + py**2 - 3.0 * px - 8.0 * py
        return Sv - abs(Lf(px, py)) < 0.0

    random.seed(20260707)
    N = 260000
    pts = [(random.uniform(-7.0, 10.5), random.uniform(-3.5, 11.5)) for _ in range(N)]
    sig3 = set(i for i, (px, py) in enumerate(pts) if region3(px, py))
    sig5 = set(i for i, (px, py) in enumerate(pts) if region5(px, py))

    sigs = []
    for idx in range(9):
        fn = region_of_index(idx)
        sigs.append(set(i for i, (px, py) in enumerate(pts) if fn(px, py)))

    def best_match(sig):
        best = None
        for idx in range(9):
            s = sigs[idx]
            inter_ = len(sig & s)
            uni_ = len(sig | s) or 1
            jac = inter_ / uni_
            if best is None or jac > best[1]:
                best = (idx, jac)
        return best

    idx3, jac3 = best_match(sig3)
    idx5, jac5 = best_match(sig5)
    assert jac3 > 0.995, ("③ 図一致が不十分", idx3, jac3)
    assert jac5 > 0.995, ("⑤ 図一致が不十分", idx5, jac5)
    print(f"  (③ ≈ 図{idx3} jaccard={jac3:.4f} ; ⑤ ≈ 図{idx5} jaccard={jac5:.4f})")
    ck("セ", ci(idx3), S1["セ"])
    ck("ソ", ci(idx5), S1["ソ"])

    # 9図が相互に異なる(=答が一意)ことも確認
    for i in range(9):
        for j in range(i + 1, 9):
            uni_ = len(sigs[i] | sigs[j]) or 1
            jac = len(sigs[i] & sigs[j]) / uni_
            assert jac < 0.98, ("9図に重複", i, j, jac)

    # =========================================================
    # 第2問 三角関数
    # =========================================================
    print("== 第2問 ==")
    S2 = slots_of(mod, 2)
    a, A, B, al, be = sp.symbols('a A B alpha beta', real=True)

    # (1) ア: sin(α+β)=sinαcosβ+cosαsinβ の空欄 = sinαcosβ
    a_items = [
        sp.sin(al) * sp.sin(be), sp.sin(al) * sp.cos(be), sp.cos(al) * sp.sin(be), sp.cos(al) * sp.cos(be),
        sp.sin(al)**2, sp.sin(be)**2, sp.cos(al)**2, sp.cos(be)**2,
    ]
    target = sp.expand_trig(sp.sin(al + be)) - sp.cos(al) * sp.sin(be)  # = sinαcosβ
    ia = [i for i, it in enumerate(a_items) if sp.simplify(it - target) == 0]
    assert len(ia) == 1, ia
    ck("ア", ci(ia[0]), S2["ア"])

    # イ,ウ: α=(A+B)/2, β=(A-B)/2  s.t. α+β=A, α-β=B
    iw_items = [A, B, A + B, A - B, (A + B) / 2, (A - B) / 2, (A + B) / 4, (A - B) / 4]
    alpha_sol = (A + B) / 2
    beta_sol = (A - B) / 2
    assert sp.simplify((alpha_sol + beta_sol) - A) == 0
    assert sp.simplify((alpha_sol - beta_sol) - B) == 0
    ii = [i for i, it in enumerate(iw_items) if sp.simplify(it - alpha_sol) == 0]
    iu = [i for i, it in enumerate(iw_items) if sp.simplify(it - beta_sol) == 0]
    ck("イ", ci(ii[0]), S2["イ"])
    ck("ウ", ci(iu[0]), S2["ウ"])

    # (2) f(x)=sin(x+7π/12)+sin(x+π/12)
    th1 = sp.Rational(7, 12) * sp.pi
    th2 = sp.Rational(1, 12) * sp.pi
    f = sp.sin(x + th1) + sp.sin(x + th2)
    avg = (th1 + th2) / 2   # π/3
    half = (th1 - th2) / 2  # π/4
    assert sp.simplify(f - 2 * sp.sin(x + avg) * sp.cos(half)) == 0
    ang_items = [sp.Integer(0), sp.pi / 12, sp.pi / 6, sp.pi / 4, sp.pi / 3, sp.pi / 2, 3 * sp.pi / 4, sp.pi]
    ie = [i for i, it in enumerate(ang_items) if sp.simplify(it - avg) == 0]
    io = [i for i, it in enumerate(ang_items) if sp.simplify(it - half) == 0]
    ck("エ", ci(ie[0]), S2["エ"])   # π/3
    ck("オ", ci(io[0]), S2["オ"])   # π/4
    # カ: xmax = π/2 - avg ; キ: max = 2cos(half)
    xmax = sp.pi / 2 - avg          # π/6
    assert 0 <= float(xmax) < 2 * math.pi
    icx = [i for i, it in enumerate(ang_items) if sp.simplify(it - xmax) == 0]
    ck("カ", ci(icx[0]), S2["カ"])
    fmax = sp.simplify(2 * sp.cos(half))
    max_items = [sp.Rational(1, 2), sp.Integer(1), sp.Integer(2), sp.sqrt(2) / 2, sp.sqrt(3) / 2, sp.sqrt(2), sp.sqrt(3), 2 * sp.sqrt(2)]
    ik = [i for i, it in enumerate(max_items) if sp.simplify(it - fmax) == 0]
    ck("キ", ci(ik[0]), S2["キ"])
    # 数値で最大点・最大値を裏取り
    xs = [2 * math.pi * t / 400000 for t in range(400000)]
    fv = [math.sin(t + float(th1)) + math.sin(t + float(th2)) for t in xs]
    imax = max(range(len(xs)), key=lambda t: fv[t])
    assert abs(xs[imax] - float(xmax)) < 1e-3, (xs[imax], float(xmax))
    assert abs(fv[imax] - float(fmax)) < 1e-4, (fv[imax], float(fmax))

    # (3)(i) g(x)=sin(x+a)+sin(x+2a)+sin(x+3a)
    g = sp.sin(x + a) + sp.sin(x + 2 * a) + sp.sin(x + 3 * a)
    pairs = [sp.sin(x + a) + sp.sin(x + 2 * a),
             sp.sin(x + a) + sp.sin(x + 3 * a),
             sp.sin(x + 2 * a) + sp.sin(x + 3 * a)]
    good = []
    for i, pr in enumerate(pairs):
        if sp.simplify(pr - 2 * sp.sin(x + 2 * a) * sp.cos(a)) == 0:
            good.append(i)
    assert good == [1], good
    ck("ク", ci(1), S2["ク"])
    ke_items = [a, 2 * a, 3 * a]
    ike = [i for i, it in enumerate(ke_items) if sp.simplify(it - 2 * a) == 0]
    ck("ケ", ci(ike[0]), S2["ケ"])
    assert sp.simplify(g - (2 * sp.cos(a) + 1) * sp.sin(x + 2 * a)) == 0
    co_items = [2 * sp.cos(a), -2 * sp.cos(a), 2 * sp.cos(2 * a), -2 * sp.cos(2 * a),
                2 * sp.cos(a) + 1, -2 * sp.cos(a) + 1, 2 * sp.cos(2 * a) + 1, -2 * sp.cos(2 * a) + 1]
    coeff = 2 * sp.cos(a) + 1
    ico = [i for i, it in enumerate(co_items) if sp.simplify(it - coeff) == 0]
    ck("コ", ci(ico[0]), S2["コ"])

    # (3)(ii) a=5π/6
    av = sp.Rational(5, 6) * sp.pi
    coeff_v = sp.simplify(coeff.subs(a, av))   # 1-√3 <0
    assert coeff_v == 1 - sp.sqrt(3)
    assert float(coeff_v) < 0
    # 最大点・最大値を数値で確定
    xs2 = [2 * math.pi * t / 600000 for t in range(600000)]
    gvals = [math.sin(t + float(av)) + math.sin(t + 2 * float(av)) + math.sin(t + 3 * float(av)) for t in xs2]
    imax2 = max(range(len(xs2)), key=lambda t: gvals[t])
    xmax2 = xs2[imax2]
    gmax2 = gvals[imax2]
    exp_x = float(sp.Rational(11, 6) * sp.pi)
    exp_max = float(sp.sqrt(3) - 1)
    assert abs(xmax2 - exp_x) < 1e-3, (xmax2, exp_x)
    assert abs(gmax2 - exp_max) < 1e-4, (gmax2, exp_max)
    # サシ/ス = 11/6
    frac = sp.Rational(11, 6)
    num, den = frac.p, frac.q
    ck("サ", str(num)[0], S2["サ"])
    ck("シ", str(num)[1], S2["シ"])
    ck("ス", str(den), S2["ス"])
    # セ: √3-1 (10択, index8)
    se_items = [sp.Integer(0), sp.Integer(1), sp.Integer(2), sp.Integer(-1), sp.Integer(-2),
                sp.sqrt(3), -sp.sqrt(3), sp.sqrt(3) + 1, sp.sqrt(3) - 1, -sp.sqrt(3) + 1]
    ise = [i for i, it in enumerate(se_items) if sp.simplify(it - (sp.sqrt(3) - 1)) == 0]
    ck("セ", ci(ise[0]), S2["セ"])
    # 符号解析の裏取り: 係数<0なので最大は sin=-1 のとき、値=coeff*(-1)=√3-1
    assert sp.simplify(coeff_v * (-1) - (sp.sqrt(3) - 1)) == 0

    # =========================================================
    print()
    if fails:
        print("FAILURES:")
        for f_ in fails:
            print("  ", f_)
        sys.exit(1)
    print("ALL VERIFY PASS")


if __name__ == "__main__":
    main()
