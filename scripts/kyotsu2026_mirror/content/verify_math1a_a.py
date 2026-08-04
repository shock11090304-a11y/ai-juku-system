# -*- coding: utf-8 -*-
r"""verify_math1a_a.py — math1a_a.py の全マークスロットを独立計算で検証する。

方針: SECTIONS/ANS_SECTIONS の値を「使わずに」ゼロから再計算し、
      ANS_SECTIONS の slots と一致することを assert する。
      さらにデータ分析部の (a)(b) 真偽・散布図の境界余白・箱ひげ図特徴も検証。

実行: python3 content/verify_math1a_a.py   → 全 assert 通過で "ALL VERIFY PASS"
"""
import importlib.util
import os
from math import gcd, isqrt, hypot
from fractions import Fraction

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    spec = importlib.util.spec_from_file_location("m1a", os.path.join(HERE, "math1a_a.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


MOD = load()
ANS = {s["section"]: s["slots"] for s in MOD.ANS_SECTIONS}
CIRC = "⓪①②③④⑤⑥⑦⑧⑨"


def circ(i):
    return CIRC[i]


def eq(name, got, exp):
    assert str(got) == str(exp), f"[{name}] got={got!r} expected={exp!r}"


# =====================================================================
#  第1問〔1〕 集合と命題
# =====================================================================
def verify_q1_sets():
    U = set(range(2, 25))

    def A(a):
        return set(k for k in U if gcd(k, a) > 1)

    # 具体例(問題文の足場)を独立検証
    eq("例a=5", A(5), {5, 10, 15, 20})
    eq("例a=8", A(8), {2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24})

    # (1) a=3,b=4
    Aset = A(3)
    Bset = A(4)
    inter = Aset & Bset
    adiff = Aset - Bset

    # 解答群(math1a_a と同じ内容を独立に定義)
    SET_CH = [
        {6, 12, 18, 24},
        {3, 9, 15, 21},
        {2, 3, 4, 6, 8},
        {4, 8, 12, 16, 20, 24},
        {5, 7, 11, 13, 17, 19, 23},
        {3, 6, 9, 12, 15, 18, 21},
        {3, 6, 9, 12, 15, 18, 21, 24},
        {2, 4, 8, 10, 14, 16, 20, 22},
        {2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24},
        {2, 3, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24},
    ]
    # 選択肢の要素数が昇順であること(実物の癖)
    cards = [len(s) for s in SET_CH]
    assert cards == sorted(cards), f"choices not sorted by card: {cards}"

    eq("ア(A)", circ(SET_CH.index(Aset)), ANS[1]["ア"])
    eq("イ(B)", circ(SET_CH.index(Bset)), ANS[1]["イ"])
    eq("ウ(A∩B)", circ(SET_CH.index(inter)), ANS[1]["ウ"])
    eq("エ(A∩B̄)", circ(SET_CH.index(adiff)), ANS[1]["エ"])

    # (2)(i): Ā に 2の倍数も3の倍数もない a を全探索(2..9で一意)
    sol_i = [a for a in range(2, 10)
             if not any((k % 2 == 0 or k % 3 == 0) for k in (U - A(a)))]
    assert sol_i == [6], f"(2)(i) not unique: {sol_i}"
    eq("オ", sol_i[0], ANS[1]["オ"])

    # (2)(ii): A∩B̄={7} となる (a,b) を全探索(一意)
    sol_ii = [(a, b) for a in range(2, 10) for b in range(2, 10)
              if (A(a) - A(b)) == {7}]
    assert sol_ii == [(7, 6)], f"(2)(ii) not unique: {sol_ii}"
    eq("カ", sol_ii[0][0], ANS[1]["カ"])
    eq("キ", sol_ii[0][1], ANS[1]["キ"])


# =====================================================================
#  第1問〔2〕 図形と計量
# =====================================================================
def verify_q1_geometry():
    # (1) 選択スロット: 解答群を独立に定義し index を照合
    KUKE = ["AD·CD", "AB·AD", "AB·BC", "AB·CD", "BC·CD",
            "AD·BC", "BD·CD", "AB·BD", "AC·BD"]
    eq("ク", circ(KUKE.index("AB·AD")), ANS[1]["ク"])   # S1=1/2·AB·AD·sinA
    eq("ケ", circ(KUKE.index("BC·CD")), ANS[1]["ケ"])   # S2=1/2·BC·CD·sinC
    KO = ["90", "120", "135", "150", "180", "240", "270", "360"]  # 昇順
    # A+C=B+D かつ A+B+C+D=360 → A+C=180
    eq("コ", circ(KO.index("180")), ANS[1]["コ"])
    SA1 = ["AB·AD-BC·CD", "AB·BD+BC·BD", "AB·AD+BC·CD", "AB·BD-BC·BD",
           "AD·BD+BD·CD", "AD·BD-BD·CD", "AB·CD+AD·BC", "AB·CD-AD·BC", "AC·BD"]
    eq("サ", circ(SA1.index("AB·AD+BC·CD")), ANS[1]["サ"])

    # (2) 円と接線. r=5, PK=p=15, QL=q=3.
    r, p, q = 5, 15, 3
    # 四角形PMOKの面積 = 2*(1/2 * p * r) = p*r
    area = p * r
    eq("シス(面積)", area, int(ANS[1]["シ"] + ANS[1]["ス"]))

    # ①適用: area = 1/2(p^2+r^2) sinP → sinP=2pr/(p^2+r^2)
    sinP = Fraction(2 * p * r, p * p + r * r)
    # 独立チェック: 2つの導出が一致
    assert Fraction(1, 2) * (p * p + r * r) * sinP == area
    eq("セ", sinP.numerator, ANS[1]["セ"])
    eq("ソ", sinP.denominator, ANS[1]["ソ"])
    assert gcd(sinP.numerator, sinP.denominator) == 1, "sinP not reduced"

    sinQ = Fraction(2 * q * r, q * q + r * r)
    ts = str(sinQ.numerator).zfill(2)
    ns = str(sinQ.denominator).zfill(2)
    eq("タチ", ts, ANS[1]["タ"] + ANS[1]["チ"])
    eq("ツテ", ns, ANS[1]["ツ"] + ANS[1]["テ"])
    assert gcd(sinQ.numerator, sinQ.denominator) == 1

    # PR:QR = sinQ:sinP (正弦定理)。最簡整数比
    ratio = sinQ / sinP  # = PR/QR
    a_r, b_r = ratio.numerator, ratio.denominator
    eq("トナ:ニヌ", f"{a_r}:{b_r}", f"{ANS[1]['ト']}{ANS[1]['ナ']}:{ANS[1]['ニ']}{ANS[1]['ヌ']}")

    # RL = QR - QL. QR を正弦定理で厳密に。
    cosP = Fraction(p * p - r * r, p * p + r * r)
    cosQ = Fraction(q * q - r * r, q * q + r * r)
    sinR = sinP * cosQ + cosP * sinQ
    k = Fraction(p + q, 1) / sinR
    QR = k * sinP
    RL = QR - q
    eq("ネノ/ハ", f"{RL.numerator}/{RL.denominator}",
       f"{ANS[1]['ネ']}{ANS[1]['ノ']}/{ANS[1]['ハ']}")
    assert gcd(RL.numerator, RL.denominator) == 1

    # (ii) 反対側(円が△の傍接円): 座標計算で厳密に RL を出す
    import numpy as np

    def RL_opposite(p_, q_, r_):
        P = np.array([-p_, 0.0]); Q = np.array([q_, 0.0]); O = np.array([0.0, r_])

        def other_dir(Pt):
            v_po = O - Pt; v_m = -Pt
            u = v_po / np.linalg.norm(v_po)
            return 2 * np.dot(v_m, u) * u - v_m

        dP = other_dir(P); dQ = other_dir(Q)
        Amat = np.array([[dP[0], -dQ[0]], [dP[1], -dQ[1]]]); bvec = Q - P
        tsol = np.linalg.solve(Amat, bvec)
        R = P + tsol[0] * dP
        assert R[1] < 0, "R should be opposite side of O"
        RO = np.linalg.norm(R - O)
        return (RO * RO - r_ * r_) ** 0.5

    import math
    val = RL_opposite(5 * math.sqrt(2), 2 * math.sqrt(2), 5.0)
    # 期待 = ヒフ√ヘ
    coef = int(ANS[1]["ヒ"] + ANS[1]["フ"]); rad = int(ANS[1]["ヘ"])
    assert abs(val - coef * math.sqrt(rad)) < 1e-6, f"RL(ii)={val} vs {coef}√{rad}"
    # √ヘ が平方因子をもたない
    assert all(rad % (d * d) != 0 for d in range(2, isqrt(rad) + 1)), "ヘ has square factor"


# =====================================================================
#  第2問〔1〕 2次関数
# =====================================================================
def verify_q2_quadratic():
    x = sp.Symbol("x")
    # (1) y=2x^2-4x-1 on [0,3]
    f = 2 * x**2 - 4 * x - 1
    vals = {t: int(f.subs(x, t)) for t in range(0, 4)}
    mx = max(vals.values()); mn = min(vals.values())
    xmax = [t for t in vals if vals[t] == mx]
    xmin = [t for t in vals if vals[t] == mn]
    assert len(xmax) == 1 and len(xmin) == 1, f"tie: {vals}"
    eq("ア", xmax[0], ANS[2]["ア"])
    eq("イ", mx, ANS[2]["イ"])
    eq("ウ", xmin[0], ANS[2]["ウ"])
    eq("エオ", str(mn).replace("-", "−"), ANS[2]["エ"] + ANS[2]["オ"])   # 例: −3

    # (2)(i) 条件1: 頂点(-2,5) 上に凸, f(-5)=-4
    a = sp.Symbol("a")
    fx = a * (x + 2)**2 + 5
    a_sol = sp.solve(sp.Eq(fx.subs(x, -5), -4), a)
    assert a_sol == [-1], a_sol
    fexp = sp.expand(fx.subs(a, -1))    # -x^2-4x+1
    assert fexp == -x**2 - 4 * x + 1, fexp
    # 頂点座標選択
    KAKU = [(0, 5), (1, 5), (2, 5), (-2, 5), (-5, 5),
            (0, -4), (-2, -4), (-5, -4), (2, -4), (5, -4)]
    eq("カ", circ(KAKU.index((-2, 5))), ANS[2]["カ"])
    # f(x)=[キク]x^2-[ケ]x+[コ]  → 係数 -1, +（-4）, +1。印字 -[ケ]x なので ケ=4
    lead = sp.Poly(fexp, x).coeff_monomial(x**2)   # -1
    lin = sp.Poly(fexp, x).coeff_monomial(x)       # -4
    const = sp.Poly(fexp, x).coeff_monomial(1)     # 1
    eq("キク", str(lead).replace("-", "−"), ANS[2]["キ"] + ANS[2]["ク"])   # −1
    eq("ケ", -lin, ANS[2]["ケ"])                          # 4
    eq("コ", const, ANS[2]["コ"])                         # 1
    # 定義域内で最大は x=-2, 最小は x=-5 を確認
    dom = [sp.Rational(t, 2) for t in range(-10, 1)]
    fv = [(t, fexp.subs(x, t)) for t in dom]
    assert max(fv, key=lambda z: z[1])[0] == -2
    assert fexp.subs(x, -5) == -4 and min(fv, key=lambda z: z[1])[1] == -4

    # (2)(ii) 条件2: 下に凸, 頂点 x=4, 最小-4, g(0)=12, g(8)=12
    g = (x - 4)**2 - 4
    gexp = sp.expand(g)   # x^2-8x+12
    assert gexp == x**2 - 8 * x + 12
    assert g.subs(x, 0) == 12 and g.subs(x, 8) == 12 and g.subs(x, 4) == -4
    # 条件の整合を数値検証: 0<a<4→m>-4; a>=4→m=-4; 0<a<=8→M=12; a>8→M>12
    def Mm(A):
        # [0,A] 上の g の最大最小(頂点4内部か端で)
        xs = [sp.Rational(i, 4) for i in range(0, int(A * 4) + 1)]
        gv = [g.subs(x, t) for t in xs]
        return max(gv), min(gv)
    for A in [1, 2, 3]:
        M, m = Mm(A); assert m > -4 and M == 12, (A, M, m)
    for A in [4, 5, 6, 7, 8]:
        M, m = Mm(A); assert m == -4 and M == 12, (A, M, m)
    for A in [9, 10]:
        M, m = Mm(A); assert m == -4 and M > 12, (A, M, m)
    # サ(凸性): 下に凸 = index 0
    eq("サ(凸性)", circ(0), ANS[2]["サ"])
    SI = ["-x^2+8x-12", "x^2-8", "-x^2+8", "x^2-4x+3", "2x^2-16x+24",
          "-2x^2+16x-24", "x^2-8x+12", "-x^2+4x-3", "2x^2-9x+7", "-2x^2+9x-7"]
    eq("シ", circ(SI.index("x^2-8x+12")), ANS[2]["シ"])

    # (3) 条件3: 上に凸, 根 α<β. 窓[b-1,b+1] の最大M>=0 ⇔ 窓∩[α,β]≠∅ ⇔ α-1<=b<=β+1
    #     これが 2<=b<=8 に一致 → α=3, β=7. h は係数未定で非一意。
    alpha, beta = sp.symbols("alpha beta")
    sol = sp.solve([sp.Eq(alpha - 1, 2), sp.Eq(beta + 1, 8)], [alpha, beta])
    assert sol[alpha] == 3 and sol[beta] == 7
    roots = sorted([3, 7])
    got = sorted([int(ANS[2]["ス"]), int(ANS[2]["セ"])])
    eq("スセ(根・順不同)", got, roots)
    # 非一意性: a を変えても根が3,7で同条件を満たすことを確認(a=-1,-2)
    for aa in (-1, -2, -3):
        h = aa * (x - 3) * (x - 7)
        # 窓最大>=0 の b 範囲を数値で
        def Mwin(b):
            xs = [sp.Rational(b) + sp.Rational(i, 10) for i in range(-10, 11)]
            return max(h.subs(x, t) for t in xs)
        for b in [2, 3, 5, 7, 8]:
            assert Mwin(b) >= 0
        for b in [0, 1, 9, 10]:
            assert Mwin(b) < 0


# =====================================================================
#  第2問〔2〕 データの分析
# =====================================================================
def verify_q2_data():
    Tmae = MOD._TMAE
    Tato = MOD._TATO
    Tzen = MOD._TZEN
    A = MOD._A_IDX
    assert len(Tmae) == len(Tato) == 28
    assert all((Tmae[i] + Tato[i]) % 2 == 0 for i in range(28)), "T前後 not integer"
    assert Tzen == [(Tmae[i] + Tato[i]) // 2 for i in range(28)]

    SEL, CNT = 467.5, 461.5
    # (a): T前<467.5 の中で #(T後>=461.5)==#(T前後>=461.5) → 真
    sel = [i for i in range(28) if Tmae[i] < SEL]
    c1 = sum(1 for i in sel if Tato[i] >= CNT)
    c2 = sum(1 for i in sel if Tzen[i] >= CNT)
    a_true = (c1 == c2)
    # (b): 選手A で T前<T前後<T後 → 真
    b_true = (Tmae[A] < Tzen[A] < Tato[A])
    combo = [(True, True), (True, False), (False, True), (False, False)]
    idx = combo.index((a_true, b_true))
    eq("ソ(散布正誤)", circ(idx), ANS[2]["ソ"])
    # 図の読み取り頑健性: 全点が閾値から2以上離れている
    assert min(abs(v - SEL) for v in Tmae) >= 2.0
    assert min(abs(v - CNT) for v in Tato) >= 2.0
    assert min(abs(v - CNT) for v in Tzen) >= 2.0
    # 重なり点なし(両図)
    assert len(set(zip(Tmae, Tato))) == 28
    assert len(set(zip(Tmae, Tzen))) == 28

    # (2) 相関係数: r = cov/(sd1*sd2) = 59.4/(8.5*7.8)
    cov, sd1, sd2 = 59.4, 8.5, 7.8
    r = cov / (sd1 * sd2)
    TA = [0.02, 0.24, 0.47, 0.62, 0.75, 0.90, 0.83, 1.12, 3.64, 4.14]
    best = min(range(len(TA)), key=lambda i: abs(TA[i] - r))
    eq("タ(相関)", circ(best), ANS[2]["タ"])
    assert abs(r - 0.90) < 0.01, r
    # |r|<=1 を破る肢が本当に>1 であること(消去法の妥当性)
    assert TA[7] > 1 and TA[8] > 1 and TA[9] > 1

    # (3)(i) 1位30ラップ → IQR (共テ流の四分位数)
    lap = sorted(MOD._LAP1)
    assert len(lap) == 30
    low = lap[:15]; up = lap[15:]
    Q1 = low[7]; Q3 = up[7]          # 15個の中央値=8番目
    IQR = round(Q3 - Q1, 10)
    lo = Q1 - 1.5 * IQR
    hi = Q3 + 1.5 * IQR
    # 境界が問題文の 29.175 / 29.775 と一致
    assert abs(lo - 29.175) < 1e-9, lo
    assert abs(hi - 29.775) < 1e-9, hi
    # 外れ値個数(下2・上1)
    below = [v for v in lap if v <= lo]
    above = [v for v in lap if v >= hi]
    assert len(below) == 2 and len(above) == 1, (below, above)
    # IQR=0.15 → チツ=15
    iqr2 = round(IQR, 2)
    assert abs(iqr2 - 0.15) < 1e-9, iqr2
    eq("チツ(IQR)", "15", ANS[2]["チ"] + ANS[2]["ツ"])

    # (3)(ii) 箱ひげ図28本: (a)偽 (b)真
    box = MOD._BOX28
    assert len(box) == 28
    # 各外れ値はひげの外
    for (mn, q1, med, q3, mx, outs) in box:
        assert q1 <= med <= q3 and mn <= q1 and q3 <= mx
        for ov in outs:
            assert ov < mn or ov > mx
    # (a) 「29秒より速いタイムはすべて外れ値」→ 非外れ値の下ひげ端<29 が存在 ⇒ 偽
    a_all_outlier = not any(box[i][0] < 29.0 for i in range(28))
    # (b) 分散大(下の行=index大)で四分位範囲が分散小(上の行)より小さい例が存在 ⇒ 真
    iqrs = [round(q3 - q1, 6) for (mn, q1, med, q3, mx, o) in box]
    b_exists = any(iqrs[j] < iqrs[i] for i in range(28) for j in range(i + 1, 28))
    combo2 = [(True, True), (True, False), (False, True), (False, False)]
    idx2 = combo2.index((a_all_outlier, b_exists))
    eq("テ(箱ひげ正誤)", circ(idx2), ANS[2]["テ"])
    assert a_all_outlier is False and b_exists is True
    # 分散順の妥当性(全域幅が概ね増加)
    ranges = [mx - mn for (mn, q1, med, q3, mx, o) in box]
    assert all(ranges[i] <= ranges[i + 1] + 1e-9 for i in range(27)), "range not increasing"

    # (3)(iii) 2×2分割表 n と割合
    order = MOD._RANK_ORDER
    assert sorted(order) == list(range(1, 29)), "not a permutation of 1..28"
    top14 = order[:14]
    n = sum(1 for rk in top14 if rk <= 8)   # 決勝進出(順位<=8) かつ 分散小さい14番以内
    eq("ト(n)", n, ANS[2]["ト"])
    # 表2の整合(周辺和)
    assert (8 - n) >= 0 and (14 - n) >= 0 and (6 + n) <= 20
    assert n + (14 - n) == 14 and (8 - n) + (6 + n) == 14
    assert n + (8 - n) == 8 and (14 - n) + (6 + n) == 20
    # 割合 P,Q
    P = Fraction(n, 8); Q = Fraction(14 - n, 20)
    rel = "<" if P < Q else ("=" if P == Q else ">")
    NA = ["<", "=", ">"]
    eq("ナ(割合)", circ(NA.index(rel)), ANS[2]["ナ"])


# =====================================================================
#  正解位置の分布(選択スロットが偏りすぎない)
# =====================================================================
def verify_distribution():
    circles = "⓪①②③④⑤⑥⑦⑧⑨"
    picks = []
    for sec in (1, 2):
        for k, v in ANS[sec].items():
            if v in circles:
                picks.append((sec, k, circles.index(v)))
    # 同一大問内で同じ番号が3連続していないか(登場順)
    for sec in (1, 2):
        seq = [i for (s, k, i) in picks if s == sec]
        run = 1
        for j in range(1, len(seq)):
            run = run + 1 if seq[j] == seq[j - 1] else 1
            assert run < 3, f"section{sec} 3連続 index at pos {j}"
    # 全体分布: どの番号も過半数を占めない
    from collections import Counter
    cnt = Counter(i for (_, _, i) in picks)
    total = sum(cnt.values())
    assert max(cnt.values()) <= total * 0.4 + 0.5, f"偏り: {cnt} / {total}"
    print(f"  選択スロット分布: {dict(sorted(cnt.items()))} (計{total})")


def main():
    verify_q1_sets(); print("第1問〔1〕集合 OK")
    verify_q1_geometry(); print("第1問〔2〕図形と計量 OK")
    verify_q2_quadratic(); print("第2問〔1〕2次関数 OK")
    verify_q2_data(); print("第2問〔2〕データの分析 OK")
    verify_distribution(); print("正解分布 OK")
    print("ALL VERIFY PASS")


if __name__ == "__main__":
    main()
