# -*- coding: utf-8 -*-
"""A17 図形の性質（数学A 第7編）

chk の方針: 図形の定理は「公式に代入し直すだけ」だと検算にならない。
すべて座標をとって、二等分線・中線・チェバ線・円との交点を **実際に作図（計算）** し、
出てきた長さ・角度・比を答えと照合する（定理そのものは一度も使わない）。
"""
import math
import os
import sys

import sympy as sp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from svgfig import Canvas, NAVY, RED, FILL, GRAY  # noqa: E402


# ---------------------------------------------------------------- 検算用（座標幾何）
def _dist(p, q):
    return sp.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)


def _mid(p, q):
    return ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)


def _centroid(p, q, r):
    return ((p[0] + q[0] + r[0]) / 3, (p[1] + q[1] + r[1]) / 3)


def _area(p, q, r):
    return sp.Abs((q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1])) / 2


def _unit(p, q):
    d = _dist(p, q)
    return ((q[0] - p[0]) / d, (q[1] - p[1]) / d)


def _add(u, v):
    return (u[0] + v[0], u[1] + v[1])


def _sub(u, v):
    return (u[0] - v[0], u[1] - v[1])


def _foot_on_x(p, v):
    """点 p を通り方向ベクトル v の直線が x 軸(y=0)と交わる点の x 座標。"""
    t = -p[1] / v[1]
    return sp.simplify(p[0] + t * v[0])


def _inter(p1, p2, q1, q2):
    """直線 p1p2 と直線 q1q2 の交点（sympy で厳密に）。"""
    s, u = sp.symbols('_s _u')
    sol = sp.solve([sp.Eq(p1[0] + s * (p2[0] - p1[0]), q1[0] + u * (q2[0] - q1[0])),
                    sp.Eq(p1[1] + s * (p2[1] - p1[1]), q1[1] + u * (q2[1] - q1[1]))],
                   [s, u], dict=True)[0]
    t = sol[s]
    return (sp.simplify(p1[0] + t * (p2[0] - p1[0])),
            sp.simplify(p1[1] + t * (p2[1] - p1[1])))


def _ratio_pt(p, q, m, n):
    """線分 pq を m:n に内分する点。"""
    return (sp.Rational(1, 1) * (n * p[0] + m * q[0]) / (m + n),
            sp.Rational(1, 1) * (n * p[1] + m * q[1]) / (m + n))


def _ang(v, p, q):
    """∠pvq を「度」で返す（float）。内積から出すので定理を使わない。"""
    a, b = _sub(p, v), _sub(q, v)
    c = ((a[0] * b[0] + a[1] * b[1])
         / (sp.sqrt(a[0] ** 2 + a[1] ** 2) * sp.sqrt(b[0] ** 2 + b[1] ** 2)))
    return float(sp.N(sp.acos(c) * 180 / sp.pi))


def _circumcenter(p, q, r):
    """3辺の垂直二等分線を実際に連立して外心を出す。"""
    X, Y = sp.symbols('_cx _cy')
    e1 = sp.Eq(2 * (q[0] - p[0]) * X + 2 * (q[1] - p[1]) * Y,
               q[0] ** 2 + q[1] ** 2 - p[0] ** 2 - p[1] ** 2)
    e2 = sp.Eq(2 * (r[0] - p[0]) * X + 2 * (r[1] - p[1]) * Y,
               r[0] ** 2 + r[1] ** 2 - p[0] ** 2 - p[1] ** 2)
    sol = sp.solve([e1, e2], [X, Y], dict=True)[0]
    return (sol[X], sol[Y])


def _incenter(p, q, r):
    """内角の二等分線を2本実際に引いて交わらせる（重み付き平均の公式は使わない）。"""
    dp = _add(_unit(p, q), _unit(p, r))
    dq = _add(_unit(q, p), _unit(q, r))
    return _inter(p, (p[0] + dp[0], p[1] + dp[1]), q, (q[0] + dq[0], q[1] + dq[1]))


def _p7_solve():
    """stem の与件 (OP=10, PA=4, AB=5, PA<PB) *だけ* から、割線のもう1つの交点までの距離 PB・
    半径 r・接線の長さ PT を解き直す。方べきの定理は使わないし、解説①の PB=PA+AB も借りない
    (借りると『解説の途中結果を入力にした検算』になり、①の取り違えを検出できない)。"""
    r, c, t2 = sp.symbols('_r _c _t2', positive=True)
    # P=(10,0) を通る単位方向 (-c, -sqrt(1-c^2)) の直線上、P から距離 t の点が円周上にある条件は
    #   t^2 - 20*c*t + (100 - r^2) = 0。 この2解が PA と PB。
    sol = sp.solve([sp.Eq(4 ** 2 - 20 * c * 4 + 100 - r ** 2, 0),        # 1つ目の交点 PA=4
                    sp.Eq(t2 ** 2 - 20 * c * t2 + 100 - r ** 2, 0),      # 2つ目の交点 PB=t2
                    sp.Eq(t2 - 4, 5)], [r, c, t2], dict=True)            # AB = PB - PA = 5
    if len(sol) != 1:                       # 解が一意でなければ検算にならない
        return None
    rr, cc, pb = (sp.simplify(sol[0][r]), sp.simplify(sol[0][c]), sp.simplify(sol[0][t2]))
    if cc > 1:                              # 単位ベクトルにならない = そんな図は存在しない
        return None
    # 出てきた r と向きで A, B を実際に置き直し、与件がそのまま出るか確かめる
    ss = sp.sqrt(1 - cc ** 2)
    P, O = (sp.Integer(10), sp.Integer(0)), (sp.Integer(0), sp.Integer(0))
    A, B = (10 - 4 * cc, -4 * ss), (10 - pb * cc, -pb * ss)
    if not (sp.simplify(_dist(P, A) - 4) == 0 and sp.simplify(_dist(A, B) - 5) == 0
            and sp.simplify(_dist(O, A) - rr) == 0 and sp.simplify(_dist(O, B) - rr) == 0):
        return None
    tx, ty = sp.symbols('_tx _ty', real=True)
    # 接点 T は「円周上」かつ「OT と PT が垂直」
    tsol = sp.solve([sp.Eq(tx ** 2 + ty ** 2, rr ** 2),
                     sp.Eq(tx * (tx - 10) + ty * ty, 0)], [tx, ty], dict=True)
    lens = {sp.simplify(sp.sqrt((s[tx] - 10) ** 2 + s[ty] ** 2)) for s in tsol}
    return rr, (lens.pop() if len(lens) == 1 else None), pb


def _cevian_ratios(A, B, C):
    """与えられた3頂点で D(BD:DC=1:2) と E(CE:EA=4:1) を実際に置き、線分 AD と BE を
    本当に交わらせて交点 P を出し、AP:PD と BP:PE を長さから実測する。
    メネラウスの式は一度も書かない(書いたら解説の打ち直しになって検算にならない)。"""
    D = _ratio_pt(B, C, 1, 2)
    E = _ratio_pt(C, A, 4, 1)
    if not (sp.simplify(2 * _dist(B, D) - _dist(D, C)) == 0
            and sp.simplify(_dist(C, E) - 4 * _dist(E, A)) == 0):
        return None                          # 与件どおりの点になっていなければ検算にならない
    P = _inter(A, D, B, E)
    return (sp.simplify(_dist(A, P) / _dist(P, D)),
            sp.simplify(_dist(B, P) / _dist(P, E)))


def _tangent_secant(rv):
    """半径 rv の円(中心は原点)に対し、stem の与件 (PT=12, PA=8) *だけ* から
    点 P の位置 OP と割線の向きを決め直し、遠いほうの交点までの距離 PB を出す。
    方べきの定理も OP^2=r^2+PT^2 も使わない。接線は『円と重解で交わる直線』として素で書き、
    割線は『同じ直線上で円周に乗る2つの距離』として解く。"""
    rv = sp.Integer(rv)
    t = sp.Symbol('_t', real=True)
    wx, wy, d = sp.symbols('_wx _wy _d', real=True)
    g = (d + t * wx) ** 2 + (t * wy) ** 2 - rv ** 2       # P+t*w が円周上にある条件
    sol = sp.solve([sp.Eq(wx ** 2 + wy ** 2, 1),
                    sp.Eq(g.subs(t, 12), 0),                   # t=12 で円に接触
                    sp.Eq(sp.diff(g, t).subs(t, 12), 0)],      # しかも重解 = 接する(交点が1つ)
                   [wx, wy, d], dict=True)
    ds = {sp.simplify(s[d]) for s in sol if sp.simplify(s[d]).is_positive}
    if len(ds) != 1:                          # OP が一意に決まらなければ検算にならない
        return None
    dv = ds.pop()
    ux, uy, pb = sp.symbols('_ux _uy _pb', real=True)
    s2 = sp.solve([sp.Eq(ux ** 2 + uy ** 2, 1),
                   sp.Eq((dv + 8 * ux) ** 2 + (8 * uy) ** 2, rv ** 2),    # 近い交点 PA=8
                   sp.Eq((dv + pb * ux) ** 2 + (pb * uy) ** 2, rv ** 2)], # 遠い交点 PB=pb
                  [ux, uy, pb], dict=True)
    far = {sp.simplify(s[pb]) for s in s2 if sp.simplify(s[pb] - 8).is_positive}
    if len(far) != 1:
        return None
    pbv = far.pop()
    s0 = next(s for s in s2 if sp.simplify(s[pb] - pbv) == 0)
    # 出てきた向きで A・B を実際に置き直し、与件がそのまま出るか確かめる
    O, P = (sp.Integer(0), sp.Integer(0)), (dv, sp.Integer(0))
    A = (dv + 8 * s0[ux], 8 * s0[uy])
    B = (dv + pbv * s0[ux], pbv * s0[uy])
    if not (sp.simplify(_dist(O, A) - rv) == 0 and sp.simplify(_dist(O, B) - rv) == 0
            and sp.simplify(_dist(P, A) - 8) == 0 and sp.simplify(_dist(P, B) - pbv) == 0):
        return None
    return dv, pbv


# ---------------------------------------------------------------- 図（実点を計算して描く）
def _fx(p1, p2, q1, q2):
    """作図用の直線交点（float）。"""
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p1, p2, q1, q2
    d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def _fig_bisector():
    """AB=10, AC=6, BC=12 の三角形と ∠A の二等分線 AD。"""
    B, C = (0.0, 0.0), (12.0, 0.0)
    A = (26.0 / 3.0, 4.0 * math.sqrt(14.0) / 3.0)
    D = (7.5, 0.0)
    c = Canvas(xr=(-1.4, 13.4), yr=(-2.4, 6.4), size=(205, 135))
    c.poly([A, B, C], fill=FILL)
    c.seg(A[0], A[1], D[0], D[1], stroke=RED, w=1.7)
    for p in (A, B, C):
        c.dot(p[0], p[1])
    c.dot(D[0], D[1], color=RED)
    c.label(A[0], A[1], "A", dx=-4, dy=-6)
    c.label(B[0], B[1], "B", dx=-13, dy=13)
    c.label(C[0], C[1], "C", dx=5, dy=13)
    c.label(D[0], D[1], "D", dx=-8, dy=14, color=RED)   # 辺 BC の下へ。旧 (4,-5) は線分 AD に重なっていた
    c.label((A[0] + B[0]) / 2, (A[1] + B[1]) / 2, "10", dx=-19, dy=-1, size=11)
    c.label((A[0] + C[0]) / 2, (A[1] + C[1]) / 2, "6", dx=6, dy=-1, size=11)
    return c.svg()


def _incircle_float(A, B, C):
    """内心 I と内接円の半径 r を **別々の道筋で** 出す。
    - I: 頂点 A, B から出る内角の二等分線(単位ベクトルの和の向き)を実際に交わらせる。
    - r: ヘロンではなく r = S/s（S=面積、s=半周長）。
    2つは独立なので「I から各辺への距離 == r」が成り立てば両方の裏取りになる。
    """
    def unit(p, q):
        d = math.dist(p, q)
        return ((q[0] - p[0]) / d, (q[1] - p[1]) / d)
    dA = _add(unit(A, B), unit(A, C))
    dB = _add(unit(B, A), unit(B, C))
    I = _fx(A, (A[0] + dA[0], A[1] + dA[1]), B, (B[0] + dB[0], B[1] + dB[1]))
    a, b, cc = math.dist(B, C), math.dist(C, A), math.dist(A, B)
    s = (a + b + cc) / 2.0                                    # 半周長
    S = abs((B[0] - A[0]) * (C[1] - A[1]) - (C[0] - A[0]) * (B[1] - A[1])) / 2.0
    return I, S / s


def _d_line(P, U, V):
    """点 P と直線 UV の距離。"""
    return (abs((V[0] - U[0]) * (U[1] - P[1]) - (U[0] - P[0]) * (V[1] - U[1]))
            / math.dist(U, V))


def _fig_gosin():
    """∠A が鋭角の三角形と、外心 O（外接円）・内心 I（内接円）。

    ★内接円は r=S/s（S=面積、s=半周長）で出す。中心は二等分線の交点として別に作図するので、
      「I から3辺への距離 == r」が独立な検算になる（_incircle_audit が import 時に毎回回す）。
      実測値（外接円の半径を 1 とした数学座標）:
          r = 0.44633748550772323
          中心→辺AB 0.44633748550772323 / 辺BC 0.4463374855077232 / 辺CA 0.4463374855077233
          r/距離 = 1.0 / 1.0000000000000002 / 0.9999999999999999   (最大相対誤差 1.2e-16)
      刷った PDF から図形を読み直しても、中心→各辺 = 20.156 / 20.133 / 20.102pt に対し
      r = 20.133pt（r/距離 = 0.9989 / 1.0000 / 1.0016。ずれは Canvas が 0.1 単位に丸めるぶんだけ）。
      → 3辺すべてに正しく内接している。紙で「突き抜けて見えた」のは半径ではなく
        **描き順**が原因だった（赤い円を三角形の後に描いていたので、接点付近の
        約40°ぶんの弧が辺の線の上に乗って、線を跨いだように見えていた）。
        いまは三角形の3辺を内接円の**後**に描き直しているので、接点付近では
        紺の辺が赤い弧を隠す＝「内側で触れている」と読める。
    """
    # ∠A=64° を保ったまま(弧 BC=128°)、外心 O と内心 I が離れる配置にする。
    # 中心角 = 円周角の2倍なので 弧BC=2·64、弧CA=2·76、弧AB=2·40 → ∠A,∠B,∠C = 64°,76°,40°（すべて鋭角）
    A, B, C = [(math.cos(math.radians(t)), math.sin(math.radians(t)))
               for t in (126.0, 206.0, 334.0)]
    I, r = _incircle_float(A, B, C)
    c = Canvas(xr=(-1.22, 1.22), yr=(-1.22, 1.22), size=(158, 158), pad=14)
    c.poly([A, B, C], fill=FILL, w=1.2)
    c.circle(0, 0, 1.0, stroke=NAVY, w=1.0)
    c.seg(0, 0, B[0], B[1], stroke=NAVY, w=1.0, dash="3 2")
    c.seg(0, 0, C[0], C[1], stroke=NAVY, w=1.0, dash="3 2")
    c.seg(I[0], I[1], B[0], B[1], stroke=RED, w=1.0, dash="3 2")
    c.seg(I[0], I[1], C[0], C[1], stroke=RED, w=1.0, dash="3 2")
    c.circle(I[0], I[1], r, stroke=RED, w=1.1)
    # ★3辺を内接円の「後」に引き直す。接点付近で辺が円の上に来るので、
    #   円は辺の内側で止まって見える（＝接している）。順番を戻すと突き抜けて見える。
    for U, V in ((A, B), (B, C), (C, A)):
        c.seg(U[0], U[1], V[0], V[1], stroke=NAVY, w=1.2)
    c.dot(0, 0)
    c.dot(I[0], I[1], color=RED)
    for p in (A, B, C):
        c.dot(p[0], p[1])
    c.label(A[0], A[1], "A", dx=-4, dy=-7)
    c.label(B[0], B[1], "B", dx=-14, dy=4)
    c.label(C[0], C[1], "C", dx=6, dy=4)
    # O と I は近い(|OI|=0.33R)ので、両方とも「左上」へ同じ向きに逃がして文字どうしを離す。
    # 実測クリアランス(最近接インクまで、viewBox 単位): O 3.78 / I 3.69、文字間 12.2
    # → w_mm=52 なので紙の上では O 1.24mm / I 1.21mm 空く。旧版は O が -0.5 で破線に食い込んでいた。
    c.label(0, 0, "O", dx=-11, dy=-5)
    c.label(I[0], I[1], "I", dx=-13, dy=-6, color=RED)
    return c.svg(w_mm=52.0)


def _fig_ceva():
    """3本のチェバ線 AP, BQ, CR が 1 点 O で交わる図。

    ★**答えになる比は、わざと正確に描かない**。
      設問は CQ:QA(=10:3) と AO:OP(=7:10) を聞いている。与件 BP:PC=3:4、AR:RB=2:5 の
      とおりに作図すると、チェバの定理を使わなくても定規で測るだけで答えが読めてしまう
      (図が本文の外にある根拠になる)。図の役目は「P は辺 BC 上、Q は辺 CA 上、R は辺 AB 上、
      3本が1点 O で交わる」という**位置関係を示すこと**だけなので、分点は
      BP:PC=87:100、AR:RB=47:100 に置く。これはチェバの条件を満たす本物の配置なので
      3本はきちんと1点で交わる(図として嘘はない)が、測って出る比は答えとは別物になる。
      実測(下の _fig_ratio_audit が毎回検算する):
          CQ:QA  描画 2.446 : 真 3.333 → 26.6% ずれ
          AO:OP  描画 0.879 : 真 0.700 → 25.6% ずれ
      定規の読み取り精度(40mm の辺で ±0.5mm ≒ ±3%)より一桁大きいので、測っても答えは作れない。
      いっぽう与件そのものの見た目は保つ: P は BC の 46.5%(真 42.9%)、R は AB の 32.0%(真 28.6%)。
      大小の向き(CQ>QA、AO<OP)も真の答えと同じ。図中に長さの数値は一切書かない。
      ★分点をずらすと交点 O が辺や他の分点に寄って図が潰れるので、
        「O から3辺・P・Q・R までの最短距離 / 三角形の直径」を 0.174 まで上げる形で
        頂点 C も (2.5,6.0)→(3.5,6.4) に動かしてある（元の配置は 0.130 で Q・O・R が団子になった）。
    """
    A, B, C = (0.0, 0.0), (8.0, 0.0), (3.5, 6.4)
    u, v = 0.87, 0.47                      # 描画用の BP/PC と AR/RB（答えが読めない値）
    P = (B[0] + u / (1 + u) * (C[0] - B[0]), B[1] + u / (1 + u) * (C[1] - B[1]))
    R = (A[0] + v / (1 + v) * (B[0] - A[0]), A[1] + v / (1 + v) * (B[1] - A[1]))
    O = _fx(A, P, C, R)
    Q = _fx(B, O, C, A)
    c = Canvas(xr=(-0.9, 8.9), yr=(-1.2, 6.9), size=(190, 155))
    c.poly([A, B, C], fill=FILL)
    for p in (P, Q, R):
        c.seg(*( {P: A, Q: B, R: C}[p] ), *p, stroke=RED, w=1.3)
    c.dot(O[0], O[1], color=RED, r=3.0)
    for p in (A, B, C):
        c.dot(p[0], p[1])
    for p in (P, Q, R):
        c.dot(p[0], p[1], color=RED)
    c.label(A[0], A[1], "A", dx=-13, dy=12)
    c.label(B[0], B[1], "B", dx=5, dy=12)
    c.label(C[0], C[1], "C", dx=-4, dy=-6)
    c.label(P[0], P[1], "P", dx=2, dy=-5)
    c.label(Q[0], Q[1], "Q", dx=-14, dy=-2)
    c.label(R[0], R[1], "R", dx=-4, dy=14)
    c.label(O[0], O[1], "O", dx=3, dy=15, color=RED)   # 旧 (4,-5) は線分 AP に重なっていた
    return c.svg(w_mm=52.0)


def _fig_enshukaku():
    """中心 O と円周上の 3 点 A, B, C。半径 OA, OB を引いた二等辺三角形が見えるように。"""
    A = (math.cos(math.radians(212)), math.sin(math.radians(212)))
    B = (math.cos(math.radians(328)), math.sin(math.radians(328)))
    C = (0.0, 1.0)
    c = Canvas(xr=(-1.32, 1.32), yr=(-1.32, 1.32), size=(155, 155))
    c.circle(0, 0, 1.0, stroke=NAVY, w=1.3)
    c.seg(0, 0, A[0], A[1], stroke=NAVY, w=1.2)
    c.seg(0, 0, B[0], B[1], stroke=NAVY, w=1.2)
    c.seg(A[0], A[1], B[0], B[1], stroke=NAVY, w=1.2)
    c.seg(C[0], C[1], A[0], A[1], stroke=RED, w=1.4)
    c.seg(C[0], C[1], B[0], B[1], stroke=RED, w=1.4)
    c.dot(0, 0)
    for p in (A, B):
        c.dot(p[0], p[1])
    c.dot(C[0], C[1], color=RED)
    c.label(0, 0, "O", dx=-4, dy=-6)
    c.label(A[0], A[1], "A", dx=-14, dy=6)
    c.label(B[0], B[1], "B", dx=6, dy=6)
    c.label(C[0], C[1], "C", dx=-4, dy=-6, color=RED)
    return c.svg()


def _fig_houbeki():
    """外部の点 P からの割線 PAB と接線 PT（問8）。作図は _CIRC_FIG["houbeki"]。"""
    return _circle_fig_svg("houbeki")


def _fig_2cevian():
    """辺 BC 上の D、辺 CA 上の E をとり、線分 AD と BE だけを引いて交点 P を作った図。
    チェバの図(3本が1点)と見分けさせたいので、3本目はわざと引かない。

    ★_fig_ceva と同じ理由で、**答えになる比はわざと正確に描かない**。
      設問は AP:PD(=3:4) と BP:PE(=5:2)。与件 BD:DC=1:2、CE:EA=4:1 のとおりに描くと
      交点 P の位置がぴたり決まり、定規で測るだけで両方の答えが読めてしまう。
      描画用は BD:DC=17:25、CE:EA=11:2。実測:
          AP:PD  描画 0.449 : 真 0.750 → 40.1% ずれ
          BP:PE  描画 4.420 : 真 2.500 → 76.8% ずれ
      大小の向き(AP<PD、BP>PE)は真の答えと同じに保ってあるので、図を見て
      「どちらが長いか」で検算する子を騙すことはない。
      与件の見た目も保つ: D は BC の 40.5%(真 33.3%)、E は CA の 84.6%(真 80.0%)。
      交点 P の余裕(P から3辺・D・E までの最短距離/直径)は 0.115（真の配置は 0.130）。
    """
    A, B, C = (2.5, 6.5), (0.0, 0.0), (9.0, 0.0)
    a, b = 0.68, 5.5                       # 描画用の BD/DC と CE/EA（答えが読めない値）
    D = (B[0] + a / (1 + a) * (C[0] - B[0]), B[1] + a / (1 + a) * (C[1] - B[1]))
    E = (C[0] + b / (1 + b) * (A[0] - C[0]), C[1] + b / (1 + b) * (A[1] - C[1]))
    P = _fx(A, D, B, E)
    c = Canvas(xr=(-1.0, 10.2), yr=(-1.4, 7.6), size=(200, 165))
    c.poly([A, B, C], fill=FILL)
    c.seg(A[0], A[1], D[0], D[1], stroke=RED, w=1.4)
    c.seg(B[0], B[1], E[0], E[1], stroke=RED, w=1.4)
    for p in (A, B, C):
        c.dot(p[0], p[1])
    for p in (D, E):
        c.dot(p[0], p[1], color=RED)
    c.dot(P[0], P[1], color=RED, r=3.0)
    c.label(A[0], A[1], "A", dx=-4, dy=-6)
    c.label(B[0], B[1], "B", dx=-13, dy=13)
    c.label(C[0], C[1], "C", dx=5, dy=13)
    c.label(D[0], D[1], "D", dx=-3, dy=17, color=RED)   # 辺 BC と線分 AD の両方から離す
    c.label(E[0], E[1], "E", dx=6, dy=-2, color=RED)
    c.label(P[0], P[1], "P", dx=7, dy=11, color=RED)
    return c.svg(w_mm=52.0)


def _fig_sessen():
    """外部の点 P からの接線 PT と割線 PAB（問9・接線のほうが先に分かっている型）。
    作図は _CIRC_FIG["sessen"]。"""
    return _circle_fig_svg("sessen")


# ------------------------------------------------ 円と割線・接線の図（問8・問9）の作図
# ★この2図は **答えそのものが図の中の長さ** になっている。
#   問8 は (1) PT (2) 半径 r、問9 は (1) AB (2) OP が答え。与件どおりに作図すると、
#   出荷版で実測したとおり PT=6.000 / r=7.996 / OP=15.007 / AB=10.009 と
#   誤差 0.1% で読めてしまい、定規1本で解ける（＝図が答えを配っている）。
#   → _fig_ceva / _fig_2cevian と同じ方針で **答えになる量をわざとずらして描く**。
#     位置関係（P は円の外・P,A,B の順に並ぶ・A,B は円周上・T は接点で OT⊥PT）は
#     すべて厳密に正しく、図に長さの数値は一切書かない。ずらすのは寸法の比だけ。
#
# ★ここで「与件どおりの比」を保てない理由（元に戻したくなったとき用）:
#   方べきの定理そのものが PA·PB = PT² を強制するので、与件の PA:AB を絵の上で
#   正しく描いた瞬間に PT が PA の 1.5 倍に固定される＝答えが決まってしまう。
#   同様に OP:PA まで正しいと r も決まる。つまり「与件を正しく描く」と
#   「答えを隠す」は数学的に両立しない。ずらすのは与件の比のほうにするしかない。
#
# ★寸法の選び方（総当たりで最適化した。値を動かすときは同じ計算をやり直すこと）:
#   与件のどれを物差しにしても答えが読めないこと、を目的関数にした。
#   すなわち「(与件の描画長):(答えの描画長)」から逆算した答えの読み取り値が、
#   真の答えから何%ずれるかの **最小値** を最大化する。到達した最小ずれは
#     方べき 24.2%（律速: PB=9 を物差しに PT を読む → 4.55、真 6）
#     接線   26.8%（律速: r=9 を物差しに OP を読む → 10.98、真 15）
#   定規の読み取り精度（40mm の辺で ±0.5mm ≒ ±3%）の 8 倍以上ある。
#   ★方べきは 25% に届かない。PA<AB（与件の大小）を保ち、割線が直径にならない
#     範囲での上限がちょうど 24.2% で、25% は「割線＝直径」の1点でしか取れない。
#     → 下限は 20% にしてある（_FIG_RATIO_SPEC）。ceva/2cevian の 25% は下げていない。
#   ★どちらの図でも「接線 PT と半径 r の長短」だけは真と逆になる（図では PT < r or PT > r）。
#     これも数学的に強制される: 問8 で r を OP の 0.8 倍（真の比）付近に描くと
#     OP を物差しに r がそのまま読めるので r/OP ≦ 0.6 にせざるを得ず、そのとき必ず PT > r。
#     問9 は逆に、PT を物差しに OP が読めないためには r/OP ≧ 0.77 が要り、そのとき必ず PT < r。
#     残せる大小（問8: PA<AB・r<OP／問9: PA<AB・AB<OP）は _fig_ratio_audit が assert する。
#     「PT と r のどちらが長いか」は設問でも答えでもないので、ここは切り捨てた。
_CIRC_FS = 12.0                      # ラベルの font-size(user unit)
_CHROME_PRINT_SCALE = 0.90685        # Chrome の print-to-pdf が文書全体にかける縮小
_CIRC_FIG = {
    # R,h は「OP=10 としたときの半径」と「中心 O から割線までの距離」。
    # labels は SVG 座標でのラベルのずらし幅(dx,dy)。総当たりで
    # 「円の外向き・線からのクリアランス最大」を満たす点を選んである。
    "houbeki": dict(R=6.05, h=1.50, size=(200, 160), pad=14, w_mm=70.0,
                    xr=(-7.1, 11.2), yr=(-7.1, 7.1), ra=0.85,
                    labels={"O": (-11, -11), "P": (8, 0), "T": (6, -6),
                            "A": (7, 17), "B": (-19, 6)}),
    "sessen": dict(R=8.20, h=7.55, size=(205, 185), pad=14, w_mm=72.0,
                   xr=(-9.2, 11.3), yr=(-9.2, 9.2), ra=0.90,
                   labels={"O": (-8, -11), "P": (8, 0), "T": (6, -6),
                           "A": (12, 8), "B": (7, 15)}),
}


def _secant_tangent(R, h, d=10.0):
    """中心 O(原点)・半径 R の円と、距離 d の外部の点 P=(d,0) の図を **座標で解く**。
    接点 T は「OT⊥PT かつ |OT|=R」から、割線の交点 A,B は「O からの距離が h の直線と
    円の交点」から出す（方べきの定理も接線長の公式も使わない ＝ 図と検算が別ルート）。
    戻り値: 点(O,P,T,A,B) と長さ(r,OP,PT,PA,PB,AB) の dict。"""
    t = math.sqrt(d * d - R * R)             # OT⊥PT の直角三角形 OTP から
    T = (R * R / d, R * t / d)               # 上側の接点
    uy = -h / d                              # 割線の向き(下向き)。O との距離が h になる
    ux = -math.sqrt(1 - uy * uy)
    m = -d * ux                              # P から弦の中点までの距離
    half = math.sqrt(R * R - h * h)          # 半弦
    pa, pb = m - half, m + half
    A = (d + pa * ux, pa * uy)
    B = (d + pb * ux, pb * uy)
    return dict(O=(0.0, 0.0), P=(d, 0.0), T=T, A=A, B=B,
                r=R, OP=d, PT=t, PA=pa, PB=pb, AB=pb - pa)


def _circle_fig_parts(name):
    """作図と検査で同じものを見るための共通部品。
    戻り値: (spec, 点の dict, Canvas, SVG座標の点, 線分[(名前,始点,終点)], 1user unit の pt)"""
    sp_ = _CIRC_FIG[name]
    g = _secant_tangent(sp_["R"], sp_["h"])
    c = Canvas(xr=sp_["xr"], yr=sp_["yr"], size=sp_["size"], pad=sp_["pad"])
    S = {k: (c.X(v[0]), c.Y(v[1])) for k, v in g.items() if isinstance(v, tuple)}
    segs = [("PB", S["P"], S["B"]), ("PT", S["P"], S["T"]),
            ("OT", S["O"], S["T"]), ("OP", S["O"], S["P"])]
    pt = (sp_["w_mm"] / 25.4 * 72) / sp_["size"][0] * _CHROME_PRINT_SCALE
    return sp_, g, c, S, segs, pt


def _circle_fig_svg(name):
    sp_, g, c, S, _segs, _pt = _circle_fig_parts(name)
    O, P, T, A, B = (g[k] for k in ("O", "P", "T", "A", "B"))
    c.circle(0, 0, sp_["R"], stroke=NAVY, w=1.4)
    c.seg(P[0], P[1], B[0], B[1], stroke=RED, w=1.5)      # 割線 P→A→B
    c.seg(P[0], P[1], T[0], T[1], stroke=RED, w=1.5)      # 接線 PT
    c.seg(0, 0, T[0], T[1], stroke=GRAY, w=1.0, dash="3 2")
    c.seg(0, 0, P[0], P[1], stroke=GRAY, w=1.0, dash="3 2")
    c.right_angle(T[0], T[1], 0, 0, P[0], P[1], size=sp_["ra"])
    c.dot(0, 0)
    c.dot(P[0], P[1])
    c.dot(T[0], T[1], color=RED)
    for p in (A, B):
        c.dot(p[0], p[1])
    for nm in ("O", "P", "T", "A", "B"):
        dx, dy = sp_["labels"][nm]
        c.label(g[nm][0], g[nm][1], nm, dx=dx, dy=dy, size=_CIRC_FS,
                color=(RED if nm == "T" else "#1a1a1a"))
    return c.svg(w_mm=sp_["w_mm"])


# 図ごとの検査の強さ: (ずれの下限, 「1:1 に見えない」と「長短の向き」も見るか)
#   ceva / 2cevian … 答えが「1本の線分を分ける比」そのもの。生徒は図の上で
#       2つの部分を見比べるので、向きが真と逆だと正しい答えを疑わせる → 3つとも課す。
#   houbeki / sessen … 答えは長さ1つで、読み取りは「与件のどれかを物差しにする」形。
#       比べる相手が毎回違うので「1:1 か」「どちらが長いか」は意味を持たない。
#       下限が 0.20 なのは、方べきの図では 0.25 が幾何学的に取れないため
#       (上の _CIRC_FIG の★を参照。実際の達成値は 24.2% / 26.8%)。
_FIG_RATIO_SPEC = {"ceva": (0.25, True), "2cevian": (0.25, True),
                   "houbeki": (0.20, False), "sessen": (0.20, False)}


def _fig_ratio_audit():
    """図から定規で答えが読めないことを機械で確かめる。

    ★このファイルの図は「位置関係だけ正しく、答えになる比はわざとずらす」方針で描いてある。
      うっかり分点や半径を与件どおりに戻すと**図が答えを配ってしまう**ので、
      import 時に毎回検算する（戻すと即 AssertionError）。
      比は公式ではなく、線分を実際に交わらせた交点と距離から出す(別ルートでの裏取り)。
    戻り値: {図の名前: [(比の名前, 描画値, 真の値, ずれ), ...]}
    """
    def d(p, q):
        return math.hypot(q[0] - p[0], q[1] - p[1])

    out = {}

    # --- 問5 チェバ: 3本が本当に1点で交わっているか + CQ:QA, AO:OP が答えから離れているか
    A, B, C = (0.0, 0.0), (8.0, 0.0), (3.5, 6.4)
    u, v = 0.87, 0.47
    P = (B[0] + u / (1 + u) * (C[0] - B[0]), B[1] + u / (1 + u) * (C[1] - B[1]))
    R = (A[0] + v / (1 + v) * (B[0] - A[0]), A[1] + v / (1 + v) * (B[1] - A[1]))
    O = _fx(A, P, C, R)
    Q = _fx(B, O, C, A)
    # B, O, Q が一直線 = 3本目 BQ もちゃんと O を通る（図として嘘がない）
    cross = ((O[0] - B[0]) * (Q[1] - B[1]) - (Q[0] - B[0]) * (O[1] - B[1]))
    assert abs(cross) < 1e-9, f"チェバの図の3本が1点で交わっていない: {cross}"
    out["ceva"] = [("CQ:QA", d(C, Q) / d(Q, A), 10 / 3), ("AO:OP", d(A, O) / d(O, P), 0.7)]

    # --- 問6 2本のチェバ線: AP:PD, BP:PE
    A2, B2, C2 = (2.5, 6.5), (0.0, 0.0), (9.0, 0.0)
    a, b = 0.68, 5.5
    D = (B2[0] + a / (1 + a) * (C2[0] - B2[0]), B2[1] + a / (1 + a) * (C2[1] - B2[1]))
    E = (C2[0] + b / (1 + b) * (A2[0] - C2[0]), C2[1] + b / (1 + b) * (A2[1] - C2[1]))
    P2 = _fx(A2, D, B2, E)
    out["2cevian"] = [("AP:PD", d(A2, P2) / d(P2, D), 0.75),
                      ("BP:PE", d(B2, P2) / d(P2, E), 2.5)]

    # --- 問8 方べき(割線)・問9 接線: 与件のどれを物差しにしても答えが読めないこと
    #     ★測るのは _circle_fig_svg が実際に描くのと同じ dict(_circle_fig_parts 経由)。
    #       検査用に座標を書き写すと、片方だけ直したときに検査が通ってしまう。
    for name, refs, answers, compare in (
            # (与件の名前, 本文での値) …物差し / (答えの名前, 真の答え) /
            # compare = 生徒が図の上で実際に見比べる組。ここだけは大小を真と揃える
            ("houbeki", (("OP", 10.0), ("PA", 4.0), ("AB", 5.0), ("PB", 9.0)),
                        (("PT", 6.0), ("r", 8.0)),
                        # PA と AB は1本の赤い直線の隣り合う2区間なので必ず見比べられる。
                        # r<OP は「P が円の外」そのもの。
                        (("PA", "AB", 4.0, 5.0), ("r", "OP", 8.0, 10.0))),
            ("sessen",  (("PT", 12.0), ("PA", 8.0), ("r", 9.0)),
                        (("AB", 10.0), ("OP", 15.0)),
                        # AB と OP は**答えどうし**。ここが逆だと正しい答えを疑わせる。
                        (("PA", "AB", 8.0, 10.0), ("AB", "OP", 10.0, 15.0),
                         ("r", "OP", 9.0, 15.0)))):
        _sp, g, _c, _S, _sg, _pt = _circle_fig_parts(name)
        O_, P_, T_, A_, B_ = (g[k] for k in ("O", "P", "T", "A", "B"))
        # (i) 図として嘘が無いこと ―― A,B は本当に円周上、T は本当に接点、P,A,B の順
        for nm, X in (("A", A_), ("B", B_), ("T", T_)):
            assert abs(d(O_, X) - g["r"]) < 1e-9, f"{name}: {nm} が円周上にない"
        assert abs((T_[0] - O_[0]) * (T_[0] - P_[0])
                   + (T_[1] - O_[1]) * (T_[1] - P_[1])) < 1e-9, f"{name}: OT⊥PT でない"
        assert g["r"] < g["OP"], f"{name}: P が円の外にない"
        assert 0 < g["PA"] < g["PB"], f"{name}: P,A,B の並びが壊れている"
        assert abs(d(P_, A_) - g["PA"]) < 1e-9 and abs(d(P_, B_) - g["PB"]) < 1e-9
        assert abs(g["PA"] * g["PB"] - g["PT"] ** 2) < 1e-9, f"{name}: 方べきが成り立たない"
        # (ii) 生徒が見比べる組の大小は本文と同じ
        #     ★全部の組は揃えられない(上の★参照)。揃える組をここに明記して機械で見張る。
        for n1, n2, v1, v2 in compare:
            assert (g[n1] < g[n2]) == (v1 < v2), (
                f"{name}: 描画の {n1}({g[n1]:.3f}) と {n2}({g[n2]:.3f}) の大小が"
                f"本文({n1}={v1:g}, {n2}={v2:g})と逆")
        # (iii) 物差し × 答え の総当たり
        out[name] = [(f"{rn}を物差しに{an}", g[an] / g[rn], av / rv)
                     for rn, rv in refs for an, av in answers]

    res = {}
    for name, rows in out.items():
        bar, strict = _FIG_RATIO_SPEC[name]
        res[name] = []
        for label, drawn, true in rows:
            dev = abs(drawn - true) / true
            # 1) 定規で測っても答えに届かない
            assert dev >= bar, (f"{name} {label}: 描画 {drawn:.4f} が真の値 {true:.4f} に"
                                f"近すぎる（{dev:.1%} < {bar:.0%}）")
            if strict:
                # 2) 一目で読める 1:1 に化けていない
                assert abs(drawn - 1) >= 0.08, f"{name} {label}: 描画 {drawn:.4f} が 1:1 に見える"
                # 3) どちらが長いかの向きは真の答えと同じ（図で検算する子を騙さない）
                assert (drawn > 1) == (true > 1), f"{name} {label}: 長短が真の答えと逆"
            res[name].append((label, round(drawn, 4), round(true, 4), round(dev, 4)))
    return res


def _incircle_audit():
    """内接円が本当に3辺すべてに接しているか（中心と半径は別ルートで出してある）。
    戻り値: (r, [辺ごとの中心からの距離], 最大相対誤差)"""
    A, B, C = [(math.cos(math.radians(t)), math.sin(math.radians(t)))
               for t in (126.0, 206.0, 334.0)]
    I, r = _incircle_float(A, B, C)
    ds = [_d_line(I, U, V) for U, V in ((A, B), (B, C), (C, A))]
    err = max(abs(x - r) / r for x in ds)
    assert err < 1e-12, f"内接円が3辺に接していない: 最大相対誤差 {err}"
    return r, ds, err


# ------------------------------------------------ 円の2図のラベル配置を見張る検査
# ★ラベルを 6.4pt → 9.8pt に大きくすると、置き場所が同じままでは線に乗る。
#   「大きくしたら重なった」は紙を見ても気づきにくい(前は小さすぎて重なりが見えなかった)。
#   紙の pt に直した実距離で機械が測る。
_INK_CAP = (0.00, 0.75, -0.80, 0.03)   # 英大文字のインクの広がり(A12 が刷った PDF から較正)
_CIRC_MIN_CLEAR_PT = 3.5
_CIRC_FS_RANGE = (9.0, 11.5)           # 同じ本の他の図は 8.4〜11.3pt、本文は 9.7pt


def _seg_box_dist(p, q, box):
    """線分 p-q と矩形 box=(x0,y0,x1,y1) の最短距離(交われば 0)。"""
    def pt_seg(P, U, V):
        dx, dy = V[0] - U[0], V[1] - U[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((P[0]-U[0])*dx + (P[1]-U[1])*dy) / L2))
        return math.hypot(P[0] - (U[0] + t*dx), P[1] - (U[1] + t*dy))

    def cross(o, u, v):
        return (u[0]-o[0])*(v[1]-o[1]) - (u[1]-o[1])*(v[0]-o[0])

    def seg_seg(a, b, c, e):
        d1, d2, d3, d4 = cross(c, e, a), cross(c, e, b), cross(a, b, c), cross(a, b, e)
        if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
            return 0.0
        return min(pt_seg(a, c, e), pt_seg(b, c, e), pt_seg(c, a, b), pt_seg(e, a, b))

    x0, y0, x1, y1 = box
    for P in (p, q):
        if x0 <= P[0] <= x1 and y0 <= P[1] <= y1:
            return 0.0
    co = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return min(seg_seg(p, q, co[i], co[(i + 1) % 4]) for i in range(4))


def _circle_fig_clearances(report=False):
    """円の2図(問8・問9)のラベルが、線・円弧・他のラベル・図の枠にぶつかっていないか。
    返り値: 違反メッセージの list(空なら合格)。unit_check_ia_jaku.py が FIG_CHECKS 経由で回す。"""
    errs = []
    for name in ("houbeki", "sessen"):
        sp_, g, c, S, segs, pt = _circle_fig_parts(name)
        W, H = sp_["size"]
        # 円は折れ線にして線分と同じ扱いにする
        cx, cy, rr = c.X(0), c.Y(0), c.s * sp_["R"]
        N = 240
        ring = [(cx + rr*math.cos(2*math.pi*i/N), cy + rr*math.sin(2*math.pi*i/N))
                for i in range(N + 1)]
        prim = list(segs) + [("円", ring[i], ring[i+1]) for i in range(N)]
        # 直角マークの2辺も線として数える
        ra = sp_["ra"]
        T_, O_, P_ = g["T"], g["O"], g["P"]
        uu = [(O_[i] - T_[i]) / math.dist(O_, T_) for i in (0, 1)]
        vv = [(P_[i] - T_[i]) / math.dist(P_, T_) for i in (0, 1)]
        m1 = (T_[0] + uu[0]*ra, T_[1] + uu[1]*ra)
        m2 = (T_[0] + (uu[0]+vv[0])*ra, T_[1] + (uu[1]+vv[1])*ra)
        m3 = (T_[0] + vv[0]*ra, T_[1] + vv[1]*ra)
        M = [(c.X(p[0]), c.Y(p[1])) for p in (m1, m2, m3)]
        prim += [("直角マーク", M[0], M[1]), ("直角マーク", M[1], M[2])]

        def ink(nm):
            dx, dy = sp_["labels"][nm]
            x, y = S[nm][0] + dx, S[nm][1] + dy
            L, R_, T2, B2 = _INK_CAP
            return (x + L*_CIRC_FS, y + T2*_CIRC_FS, x + R_*_CIRC_FS*len(nm), y + B2*_CIRC_FS)

        boxes = {nm: ink(nm) for nm in ("O", "P", "T", "A", "B")}
        rows = []
        for nm, bx in boxes.items():
            ds = sorted((_seg_box_dist(p, q, bx)*pt, n) for n, p, q in prim)
            rows.append((nm, ds[0]))
            if ds[0][0] < _CIRC_MIN_CLEAR_PT:
                errs.append(f"{name} の図: ラベル『{nm}』が {ds[0][1]} に {ds[0][0]:.2f}pt まで"
                            f"接近(下限 {_CIRC_MIN_CLEAR_PT}pt)")
            if bx[0] < 0 or bx[1] < 0 or bx[2] > W or bx[3] > H:
                errs.append(f"{name} の図: ラベル『{nm}』が viewBox({W}x{H})からはみ出す {bx}")
        ns = list(boxes)
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                b1, b2 = boxes[ns[i]], boxes[ns[j]]
                if min(b1[2], b2[2]) - max(b1[0], b2[0]) > 0 and \
                   min(b1[3], b2[3]) - max(b1[1], b2[1]) > 0:
                    errs.append(f"{name} の図: ラベル『{ns[i]}』と『{ns[j]}』が重なっている")
        fs_pt = _CIRC_FS * pt
        if not _CIRC_FS_RANGE[0] <= fs_pt <= _CIRC_FS_RANGE[1]:
            errs.append(f"{name} の図: ラベルが紙で {fs_pt:.2f}pt "
                        f"(許容 {_CIRC_FS_RANGE[0]}〜{_CIRC_FS_RANGE[1]}pt、本文 9.7pt)。"
                        f"size か w_mm を直すこと")
        if report:
            print(f"  {name}: 紙 {sp_['w_mm']:.1f}mm x {sp_['w_mm']*H/W:.1f}mm / "
                  f"ラベル {fs_pt:.2f}pt")
            for nm, (dmin, who) in rows:
                print(f"    『{nm}』最短 {dmin:5.2f}pt ({who})")
    return errs


# unit_check_ia_jaku.py が拾って実際に回す(書いただけで呼ばれない検査を作らない)
FIG_CHECKS = [_circle_fig_clearances]

_FIG_RATIO_AUDIT = _fig_ratio_audit()      # import のたびに検算する（戻すと即 AssertionError）
_INCIRCLE_AUDIT = _incircle_audit()


UNIT = {
 "name": "図形の性質",
 "tag": "角の二等分線・五心・チェバ／メネラウス・円と方べき",
 "problems": [

  {"group": "角の二等分線と線分の比", "level": "basic",
   "skill": "GE1", "sub": [],
   "stem": "$\\triangle\\mathrm{ABC}$ で $\\mathrm{AB}=10$、$\\mathrm{AC}=6$ とする。"
           "$\\angle\\mathrm{A}$ の二等分線が辺 $\\mathrm{BC}$ と交わる点を $\\mathrm{D}$ とし、"
           "$\\mathrm{BD}-\\mathrm{DC}=3$ であるという。$\\mathrm{BD}$ と $\\mathrm{BC}$ の長さを求めよ。",
   "answer": "$\\mathrm{BD}=\\dfrac{15}{2}$、$\\mathrm{BC}=12$",
   "figure": _fig_bisector(),
   "explanation": r"""▶ なぜ「はさむ2辺の比」で切れるのか。$\mathrm{D}$ は $\angle\mathrm{A}$ の二等分線上にあるので、
$\mathrm{D}$ から辺 $\mathrm{AB}$、$\mathrm{AC}$ に下ろした垂線の長さは等しい（これが二等分線の正体）。
その共通の長さを $h$ とすると
$\triangle\mathrm{ABD}:\triangle\mathrm{ACD}=\frac{1}{2}\mathrm{AB}\cdot h:\frac{1}{2}\mathrm{AC}\cdot h=\mathrm{AB}:\mathrm{AC}$。
同じ2つの三角形を $\mathrm{BC}$ 側から見ると高さが共通なので面積比は $\mathrm{BD}:\mathrm{DC}$。
だから $\mathrm{BD}:\mathrm{DC}=\mathrm{AB}:\mathrm{AC}$ になる。
① $\mathrm{BD}:\mathrm{DC}=10:6=5:3$。<b>まず約分する</b>と後がラク。
② 比が分かったら<b>比の1つ分を $k$ とおく</b>のが定石。$\mathrm{BD}=5k$、$\mathrm{DC}=3k$。
③ 与えられた条件 $\mathrm{BD}-\mathrm{DC}=3$ に入れると $5k-3k=2k=3$、よって $k=\frac{3}{2}$。
④ $\mathrm{BD}=5k=\frac{15}{2}$、$\mathrm{DC}=3k=\frac{9}{2}$、$\mathrm{BC}=8k=12$。
★ 事故の1位は比を裏返して $\mathrm{BD}:\mathrm{DC}=6:10$ としてしまうこと。
合言葉は<b>「$\mathrm{B}$ 側には $\mathrm{B}$ が入っている辺 $\mathrm{AB}$ が対応」</b>。
図の $\mathrm{AB}$ と $\mathrm{BD}$ に同じ印を書き込んでおくと二度と間違えない。
検算は $\mathrm{BD}+\mathrm{DC}=\frac{15}{2}+\frac{9}{2}=12=\mathrm{BC}$ に戻るか、
そして $\frac{15}{2}:\frac{9}{2}=15:9=5:3$ に戻るか —— どちらも5秒で済む。""",
   "chk": lambda: (lambda A=(sp.Rational(26, 3), 4 * sp.sqrt(14) / 3),
                          B=(sp.Integer(0), sp.Integer(0)),
                          C=(sp.Integer(12), sp.Integer(0)): (
        # 与えられた2辺をもつ三角形を実際に置き、二等分線を「単位ベクトルの和」で作って交点 D を実測する
        lambda D=(_foot_on_x(A, _add(_unit(A, B), _unit(A, C))), sp.Integer(0)): (
            sp.simplify(_dist(A, B) - 10) == 0 and sp.simplify(_dist(A, C) - 6) == 0
            and sp.simplify(_dist(B, D) - _dist(D, C) - 3) == 0
            and sp.simplify(_dist(B, D) - sp.Rational(15, 2)) == 0
            and sp.simplify(_dist(B, C) - 12) == 0))())()},

  {"group": "角の二等分線と線分の比", "level": "standard",
   "skill": "GE1", "sub": [],
   "stem": "$\\triangle\\mathrm{ABC}$ において $\\mathrm{AB}=9$、$\\mathrm{AC}=6$、$\\mathrm{BC}=5$ である。"
           "頂点 $\\mathrm{A}$ における<b>外角</b>の二等分線をひき、それが直線 $\\mathrm{BC}$ と"
           "交わる点を $\\mathrm{E}$ とする。線分 $\\mathrm{CE}$ の長さを求めよ。",
   "answer": "$\\mathrm{CE}=10$",
   "explanation": r"""▶ 外角の二等分線でも、$\mathrm{E}$ から2辺（の延長）までの距離が等しいという事情は内角のときと同じ。
だから比はやはり $\mathrm{AB}:\mathrm{AC}$ になる。<b>違うのは内分ではなく外分になること</b>だけ。
① $\mathrm{BE}:\mathrm{EC}=\mathrm{AB}:\mathrm{AC}=9:6=3:2$。
② $\mathrm{AB}$ のほうが長いので、$\mathrm{E}$ は<b>短い辺 $\mathrm{AC}$ の側、つまり $\mathrm{C}$ を越えた延長上</b>にある。
③ すると $\mathrm{B}\to\mathrm{C}\to\mathrm{E}$ の順に並ぶので $\mathrm{BE}-\mathrm{EC}=\mathrm{BC}=5$。
④ $\mathrm{BE}=3k$、$\mathrm{EC}=2k$ とおくと $3k-2k=k=5$。よって $\mathrm{CE}=2k=10$（このとき $\mathrm{BE}=15$）。
★ 内分と同じ $3:2$ なのに、<b>足して $\mathrm{BC}$ ではなく引いて $\mathrm{BC}$</b> になる —— ここを取り違えるのが最頻出。
図をかいて $\mathrm{E}$ がどちら側かを先に決めること。
なお $\mathrm{AB}=\mathrm{AC}$ のときは外角の二等分線が $\mathrm{BC}$ と平行になり<b>交点が存在しない</b>。
検算は $\mathrm{BE}:\mathrm{EC}=15:10=3:2$ かつ $15-10=5=\mathrm{BC}$ の2本立てで。""",
   "chk": lambda: (lambda A=(sp.Integer(7), 4 * sp.sqrt(2)),
                          B=(sp.Integer(0), sp.Integer(0)),
                          C=(sp.Integer(5), sp.Integer(0)): (
        lambda E=_foot_on_x(A, _sub(_unit(A, B), _unit(A, C))): (
            # 外角の二等分線 = 単位ベクトルの「差」の向き。交点 E を直接求めて長さを実測する
            sp.simplify(_dist(A, B) - 9) == 0 and sp.simplify(_dist(A, C) - 6) == 0
            and sp.simplify(_dist(B, C) - 5) == 0
            and sp.simplify(E - C[0] - 10) == 0 and sp.simplify(E - B[0] - 15) == 0))())()},

  {"group": "三角形の五心（重心・外心・内心）", "level": "basic",
   "skill": "GE2", "sub": [],
   "stem": "$\\triangle\\mathrm{ABC}$ の重心を $\\mathrm{G}$ とし、直線 $\\mathrm{AG}$ と辺 $\\mathrm{BC}$ の交点を "
           "$\\mathrm{M}$ とする。$\\mathrm{AG}=6$、$\\triangle\\mathrm{ABC}$ の面積が $45$ のとき、"
           "線分 $\\mathrm{GM}$ の長さと $\\triangle\\mathrm{GBC}$ の面積を求めよ。",
   "answer": "$\\mathrm{GM}=3$、$\\triangle\\mathrm{GBC}$ の面積は $15$",
   "explanation": r"""▶ 重心は3本の中線の交点で、<b>各中線を頂点の側から $2:1$ に内分する</b>。
だから直線 $\mathrm{AG}$ は中線であり、$\mathrm{M}$ は辺 $\mathrm{BC}$ の中点。長さも面積もこの $2:1$ から出る。
① $\mathrm{AG}:\mathrm{GM}=2:1$ なので $\mathrm{GM}=\frac{1}{2}\mathrm{AG}=3$。中線全体は $\mathrm{AM}=6+3=9$。
② 面積は「底辺 $\mathrm{BC}$ が共通」で比べる。$\triangle\mathrm{GBC}$ の高さは $\mathrm{G}$ から $\mathrm{BC}$ までの距離、
$\triangle\mathrm{ABC}$ の高さは $\mathrm{A}$ から $\mathrm{BC}$ までの距離で、その比は $\mathrm{GM}:\mathrm{AM}=3:9=1:3$。
③ よって $\triangle\mathrm{GBC}=\frac{1}{3}\times 45=15$。
★ ここで覚えるのは<b>「重心は三角形を面積の等しい3つに割る」</b>こと。
実際 $\triangle\mathrm{GBC}=\triangle\mathrm{GCA}=\triangle\mathrm{GAB}=15$ で、合計 $45$ に戻る（これが検算）。
$2:1$ を $1:2$ と逆に取ると $\mathrm{GM}=12$ になってしまう。<b>「頂点から数えて2」</b>と口で言ってから書くこと。""",
   "chk": lambda: (lambda A=(sp.Integer(5), sp.Integer(9)),
                          B=(sp.Integer(0), sp.Integer(0)),
                          C=(sp.Integer(10), sp.Integer(0)): (
        lambda G=_centroid(A, B, C), M=_mid(B, C): (
            # 重心を「3頂点の平均」として置き直し、与件(AG=6・面積45)が成立することを確かめてから
            # 答え(GM と △GBC の面積)を座標から実測する
            sp.simplify(_area(A, B, C) - 45) == 0
            and sp.simplify(_dist(A, G) - 6) == 0
            and sp.simplify(_dist(G, M) - 3) == 0
            and sp.simplify(_area(G, B, C) - 15) == 0))())()},

  {"group": "三角形の五心（重心・外心・内心）", "level": "standard",
   "skill": "GE2", "sub": ["GE4"],
   "stem": "鋭角三角形 $\\mathrm{ABC}$ の外心を $\\mathrm{O}$、内心を $\\mathrm{I}$ とする。"
           "$\\angle\\mathrm{A}=64^\\circ$ のとき、$\\angle\\mathrm{BOC}$ と $\\angle\\mathrm{BIC}$ を"
           "それぞれ求めよ。",
   "answer": "$\\angle\\mathrm{BOC}=128^\\circ$、$\\angle\\mathrm{BIC}=122^\\circ$",
   "figure": _fig_gosin(),
   "explanation": r"""▶ 同じ $\angle\mathrm{A}$ から出発するのに答えが違うのは、<b>外心と内心で使う道具が別物</b>だから。
外心は「外接円の中心」＝円周角の話、内心は「内角の二等分線の交点」＝角の和の話。混ぜないことがすべて。
① 外心 $\mathrm{O}$ は外接円の中心なので、$\angle\mathrm{BOC}$ は弧 $\mathrm{BC}$ に対する<b>中心角</b>、
$\angle\mathrm{A}$ は同じ弧に対する<b>円周角</b>。中心角は円周角の2倍だから
$\angle\mathrm{BOC}=2\times 64^\circ=128^\circ$。
② 内心 $\mathrm{I}$ は内角の二等分線の交点なので、$\triangle\mathrm{IBC}$ で
$\angle\mathrm{IBC}=\frac{\mathrm{B}}{2}$、$\angle\mathrm{ICB}=\frac{\mathrm{C}}{2}$。
③ $\mathrm{B}+\mathrm{C}=180^\circ-64^\circ=116^\circ$ なので $\frac{\mathrm{B}}{2}+\frac{\mathrm{C}}{2}=58^\circ$。
④ $\triangle\mathrm{IBC}$ の内角の和より $\angle\mathrm{BIC}=180^\circ-58^\circ=122^\circ$。
公式にすると $\angle\mathrm{BIC}=90^\circ+\frac{\mathrm{A}}{2}$。
★ 合言葉は<b>「外心は2倍、内心は $90^\circ$ ＋半分」</b>。逆に当てはめるのがこの単元最多の事故。
検算は<b>公式の形そのもの</b>でやる。$\angle\mathrm{BIC}=90^\circ+\frac{\mathrm{A}}{2}$ で $\mathrm{A}\gt 0$ だから、
内心のほうは<b>どんな三角形でも必ず $90^\circ$ より大きい</b>。
いっぽう $\angle\mathrm{BOC}=2\angle\mathrm{A}$ のほうは $\mathrm{A}\lt 45^\circ$ なら $90^\circ$ より小さくなる。
「内部にある点だから大きな角」ではない —— 大小を決めているのは位置ではなく式のほう。
なお $\angle\mathrm{BOC}=2\angle\mathrm{A}$ に効いているのは<b>$\angle\mathrm{A}$ が鋭角</b>ということだけで、
$\mathrm{B}$ や $\mathrm{C}$ が鈍角でも成り立つ（$\mathrm{A}=64^\circ$、$\mathrm{B}=100^\circ$ でも $\angle\mathrm{BOC}=128^\circ$）。
$\angle\mathrm{A}$ が鈍角のときだけ $2\angle\mathrm{A}$ が $180^\circ$ を超え、
中心角は反対まわりの $360^\circ-2\angle\mathrm{A}$ になる。
この問題は $\angle\mathrm{A}=64^\circ$ と鋭角だと最初から与えられているので、
「鋭角三角形」という条件は<b>図の形を決めているだけ</b>（外心 $\mathrm{O}$ が三角形の内部に来る）で、
答えを出すのには使っていない。""",
   "chk": lambda: (lambda A=(sp.Float(0), sp.Float(0)), B=(sp.Float(5), sp.Float(0)): (
        # 垂直二等分線の連立で外心、二等分線2本の交点で内心を作図し、内積で角度を実測する。
        # t=3 は鋭角三角形、t=20 は ∠B が鈍角の三角形(★で「B や C が鈍角でも成り立つ」と
        # 書いた主張そのものを検算する)。∠A=64° さえ保てば答えは同じになるはず。
        all((lambda C=(sp.N(t * sp.cos(sp.rad(64))), sp.N(t * sp.sin(sp.rad(64)))): (
                lambda O=_circumcenter(A, B, C), I=_incenter(A, B, C): (
                    abs(_ang(A, B, C) - 64) < 1e-7
                    and abs(_ang(O, B, C) - 128) < 1e-7
                    and abs(_ang(I, B, C) - 122) < 1e-7))())()
            for t in (3, 20))
        and abs(_ang(B, A, (sp.N(20 * sp.cos(sp.rad(64))), sp.N(20 * sp.sin(sp.rad(64)))))) > 90))()},

  {"group": "チェバとメネラウスの使い分け", "level": "advanced",
   "skill": "GE3", "sub": [],
   "stem": "$\\triangle\\mathrm{ABC}$ の辺 $\\mathrm{BC}$ 上に点 $\\mathrm{P}$、辺 $\\mathrm{CA}$ 上に点 $\\mathrm{Q}$、"
           "辺 $\\mathrm{AB}$ 上に点 $\\mathrm{R}$ があり、3直線 $\\mathrm{AP}$、$\\mathrm{BQ}$、$\\mathrm{CR}$ は"
           "1点 $\\mathrm{O}$ で交わっている。$\\mathrm{BP}:\\mathrm{PC}=3:4$、"
           "$\\mathrm{AR}:\\mathrm{RB}=2:5$ のとき、次を最も簡単な整数比で求めよ。<br>"
           "(1) $\\mathrm{CQ}:\\mathrm{QA}$　(2) $\\mathrm{AO}:\\mathrm{OP}$",
   "answer": "(1) $\\mathrm{CQ}:\\mathrm{QA}=10:3$　(2) $\\mathrm{AO}:\\mathrm{OP}=7:10$",
   "figure": _fig_ceva(),
   "explanation": r"""▶ 使い分けは図の形で決まる。<b>3本が1点に集まっている＝チェバ、1本の直線が三角形を切っている＝メネラウス</b>。
(1) は3本が集まっている話なのでチェバ、(2) は $\mathrm{AP}$ 上の点の位置を聞かれているのでメネラウスに持ち込む。
① チェバの定理を $\triangle\mathrm{ABC}$ に使う:
$\frac{\mathrm{BP}}{\mathrm{PC}}\cdot\frac{\mathrm{CQ}}{\mathrm{QA}}\cdot\frac{\mathrm{AR}}{\mathrm{RB}}=1$。
分子分母は<b>$\mathrm{B}\to\mathrm{P}\to\mathrm{C}\to\mathrm{Q}\to\mathrm{A}\to\mathrm{R}\to\mathrm{B}$ と一周する順</b>に書けば必ず作れる。
② 代入して $\frac{3}{4}\cdot\frac{\mathrm{CQ}}{\mathrm{QA}}\cdot\frac{2}{5}=1$。
よって $\frac{\mathrm{CQ}}{\mathrm{QA}}=\frac{20}{6}=\frac{10}{3}$、すなわち $\mathrm{CQ}:\mathrm{QA}=10:3$。
③ (2) は<b>「求めたい $\mathrm{AO}$ と $\mathrm{OP}$ が辺の上に乗る三角形」を先に探す</b>。$\triangle\mathrm{ABP}$ を選び、
これを直線 $\mathrm{CR}$（$\mathrm{C}$、$\mathrm{O}$、$\mathrm{R}$ が一直線）で切ると見る。
④ メネラウスの定理:
$\frac{\mathrm{AR}}{\mathrm{RB}}\cdot\frac{\mathrm{BC}}{\mathrm{CP}}\cdot\frac{\mathrm{PO}}{\mathrm{OA}}=1$。
⑤ $\mathrm{BP}:\mathrm{PC}=3:4$ より $\mathrm{BC}=3+4=7$、$\mathrm{CP}=4$ なので $\frac{\mathrm{BC}}{\mathrm{CP}}=\frac{7}{4}$。
ここは $\frac{3}{4}$ ではない —— <b>$\mathrm{BC}$ は $\mathrm{BP}$ ではなく全体</b>。
⑥ $\frac{2}{5}\cdot\frac{7}{4}\cdot\frac{\mathrm{PO}}{\mathrm{OA}}=1$ より $\frac{\mathrm{PO}}{\mathrm{OA}}=\frac{10}{7}$。
よって $\mathrm{AO}:\mathrm{OP}=7:10$。
★ メネラウスで落ちる人の9割は⑤の<b>「線分の取り違え」</b>。定理を書く前に、
たどる道（$\mathrm{A}\to\mathrm{R}\to\mathrm{B}\to\mathrm{C}\to\mathrm{P}\to\mathrm{O}\to\mathrm{A}$）を図に指でなぞって、
通過点で切った6本の線分を書き出すこと。
検算は「$\mathrm{O}$ は三角形の内部だから $\mathrm{AO}$ も $\mathrm{OP}$ も正、しかも $\mathrm{AO}+\mathrm{OP}=\mathrm{AP}$」で符号と大小を確認する。""",
   "chk": lambda: (lambda A=(sp.Integer(0), sp.Integer(0)), B=(sp.Integer(7), sp.Integer(0)),
                          C=(sp.Integer(0), sp.Integer(7)): (
        lambda P=_ratio_pt(B, C, 3, 4), R=_ratio_pt(A, B, 2, 5): (
            lambda O=_inter(A, P, C, R): (
                lambda Q=_inter(B, O, C, A): (
                    # 定理を使わず、AP と CR を実際に交わらせて O を出し、
                    # 直線 BO と CA の交点 Q も出してから比を実測する
                    sp.simplify(_dist(C, Q) / _dist(Q, A) - sp.Rational(10, 3)) == 0
                    and sp.simplify(_dist(A, O) / _dist(O, P) - sp.Rational(7, 10)) == 0))())())())()},

  {"group": "チェバとメネラウスの使い分け", "level": "advanced",
   "skill": "GE3", "sub": [],
   "stem": "$\\triangle\\mathrm{ABC}$ の辺 $\\mathrm{BC}$ 上に $\\mathrm{BD}:\\mathrm{DC}=1:2$ となる点 "
           "$\\mathrm{D}$、辺 $\\mathrm{CA}$ 上に $\\mathrm{CE}:\\mathrm{EA}=4:1$ となる点 $\\mathrm{E}$ をとる。"
           "線分 $\\mathrm{AD}$ と線分 $\\mathrm{BE}$ の交点を $\\mathrm{P}$ とするとき、"
           "次を最も簡単な整数比で求めよ。<br>"
           "(1) $\\mathrm{AP}:\\mathrm{PD}$　(2) $\\mathrm{BP}:\\mathrm{PE}$",
   "answer": "(1) $\\mathrm{AP}:\\mathrm{PD}=3:4$　(2) $\\mathrm{BP}:\\mathrm{PE}=5:2$",
   "figure": _fig_2cevian(),
   "explanation": r"""▶ まず<b>どちらの定理かを仕分ける</b>。チェバは「3本が1点で交わる」ときの式で、3本そろわないと作れない。
この図に引いてある線は $\mathrm{AD}$ と $\mathrm{BE}$ の<b>2本だけ</b>なので、チェバは使えない。
2本の交点が線分をどこで切るかを知りたいときはメネラウス —— コツは
<b>「求めたい2つの線分が辺の上に乗る三角形」を先に選び、もう1本をそれを切る直線と見る</b>こと。
① (1) の $\mathrm{AP}$ と $\mathrm{PD}$ はどちらも線分 $\mathrm{AD}$ の上にある。
そこで $\mathrm{AD}$ を辺にもつ $\triangle\mathrm{ADC}$ を選び、これを直線 $\mathrm{BE}$ で切ると見る
（$\mathrm{B}$、$\mathrm{P}$、$\mathrm{E}$ は一直線）。
② 一周する道は $\mathrm{A}\to\mathrm{P}\to\mathrm{D}\to\mathrm{B}\to\mathrm{C}\to\mathrm{E}\to\mathrm{A}$。
切れた6本の線分を順に並べて
$\frac{\mathrm{AP}}{\mathrm{PD}}\cdot\frac{\mathrm{DB}}{\mathrm{BC}}\cdot\frac{\mathrm{CE}}{\mathrm{EA}}=1$。
③ $\mathrm{BD}:\mathrm{DC}=1:2$ から $\mathrm{DB}=1$、$\mathrm{BC}=1+2=3$ なので $\frac{\mathrm{DB}}{\mathrm{BC}}=\frac{1}{3}$。
ここを $\frac{1}{2}$ としないこと —— <b>$\mathrm{BC}$ は $\mathrm{DC}$ ではなく辺の全体</b>。
④ 代入して $\frac{\mathrm{AP}}{\mathrm{PD}}\cdot\frac{1}{3}\cdot\frac{4}{1}=1$、よって
$\frac{\mathrm{AP}}{\mathrm{PD}}=\frac{3}{4}$、すなわち $\mathrm{AP}:\mathrm{PD}=3:4$。
⑤ (2) の $\mathrm{BP}$ と $\mathrm{PE}$ は線分 $\mathrm{BE}$ の上にあるので、
今度は $\mathrm{BE}$ を辺にもつ $\triangle\mathrm{BEC}$ を選び、直線 $\mathrm{AD}$ で切ると見る
（$\mathrm{A}$、$\mathrm{P}$、$\mathrm{D}$ は一直線）。
⑥ 道は $\mathrm{B}\to\mathrm{P}\to\mathrm{E}\to\mathrm{A}\to\mathrm{C}\to\mathrm{D}\to\mathrm{B}$ で
$\frac{\mathrm{BP}}{\mathrm{PE}}\cdot\frac{\mathrm{EA}}{\mathrm{AC}}\cdot\frac{\mathrm{CD}}{\mathrm{DB}}=1$。
⑦ $\mathrm{EA}=1$、$\mathrm{AC}=4+1=5$、$\mathrm{CD}=2$、$\mathrm{DB}=1$ だから
$\frac{\mathrm{BP}}{\mathrm{PE}}\cdot\frac{1}{5}\cdot\frac{2}{1}=1$、よって $\mathrm{BP}:\mathrm{PE}=5:2$。
★ 合言葉は<b>「1点に集まる＝チェバ、1本で切る＝メネラウス」</b>。
そのうえでメネラウスは<b>三角形の選び方がすべて</b>で、選び方は「欲しい比が辺の上に乗るように」で自動的に決まる。
(1) と (2) で違う三角形を使ったのはそのためで、同じ $\triangle\mathrm{ADC}$ のままでは $\mathrm{BP}:\mathrm{PE}$ は出てこない。
検算は座標が速い。$\mathrm{B}(0,\ 0)$、$\mathrm{C}(3,\ 0)$、$\mathrm{A}(0,\ 5)$ とおくと
$\mathrm{D}(1,\ 0)$、$\mathrm{E}\left(\frac{3}{5},\ 4\right)$ で、
直線 $\mathrm{AD}$ は $y=5-5x$、直線 $\mathrm{BE}$ は $y=\frac{20}{3}x$。
交点は $\mathrm{P}\left(\frac{3}{7},\ \frac{20}{7}\right)$ なので、$x$ 座標だけ見れば
$\mathrm{AP}:\mathrm{PD}=\frac{3}{7}:\frac{4}{7}=3:4$、$\mathrm{BP}:\mathrm{PE}=\frac{3}{7}:\frac{6}{35}=5:2$ に戻る。""",
   "chk": lambda: all(
        # 定理を使わず、形の違う三角形3つで D・E を置き AD と BE を実際に交わらせて比を実測する。
        # 1つの三角形だけだと「その配置でたまたま合う値」を検出できない。
        _cevian_ratios(*tri) == (sp.Rational(3, 4), sp.Rational(5, 2))
        for tri in (((sp.Integer(1), sp.Integer(5)), (sp.Integer(0), sp.Integer(0)),
                     (sp.Integer(6), sp.Integer(0))),
                    ((sp.Integer(0), sp.Integer(0)), (sp.Integer(9), sp.Integer(0)),
                     (sp.Integer(2), sp.Integer(7))),
                    ((sp.Integer(-3), sp.Integer(4)), (sp.Integer(1), sp.Integer(-2)),
                     (sp.Integer(8), sp.Integer(5)))))},

  {"group": "円周角・方べきの定理", "level": "basic",
   "skill": "GE4", "sub": ["GE2"],
   "stem": "円 $\\mathrm{O}$ の周上に3点 $\\mathrm{A}$、$\\mathrm{B}$、$\\mathrm{C}$ がある。"
           "$\\angle\\mathrm{OAB}=32^\\circ$ で、点 $\\mathrm{C}$ は直線 $\\mathrm{AB}$ に関して "
           "中心 $\\mathrm{O}$ と同じ側の弧上にあるとき、$\\angle\\mathrm{ACB}$ の大きさを求めよ。",
   "answer": "$\\angle\\mathrm{ACB}=58^\\circ$",
   "figure": _fig_enshukaku(),
   "explanation": r"""▶ いきなり円周角には入れない。中心角 $\angle\mathrm{AOB}$ が分かっていないからだ。
そこで<b>「中心と円周上の点を結んだら、必ず半径どうしで二等辺三角形」</b>という合図を使う。
① $\mathrm{OA}=\mathrm{OB}$（どちらも半径）だから $\triangle\mathrm{OAB}$ は二等辺三角形。
底角は等しいので $\angle\mathrm{OBA}=\angle\mathrm{OAB}=32^\circ$。
② 内角の和より $\angle\mathrm{AOB}=180^\circ-32^\circ\times 2=180^\circ-64^\circ=116^\circ$。
③ $\angle\mathrm{AOB}$ は $\mathrm{C}$ を含まない側の弧 $\mathrm{AB}$ に対する中心角、$\angle\mathrm{ACB}$ は同じ弧に対する円周角。
円周角は中心角の半分なので $\angle\mathrm{ACB}=\frac{116^\circ}{2}=58^\circ$。
★ この単元の最大の事故は<b>「円周角と中心角が同じ弧を見ているか」を確かめないこと</b>。
もし $\mathrm{C}$ が反対側（$\mathrm{A}$ と $\mathrm{B}$ の間の短いほうの弧上）にあれば、
見る弧が入れかわって $\angle\mathrm{ACB}=\frac{360^\circ-116^\circ}{2}=122^\circ$ になる。
答えが2通りありうるので、問題文の「どちら側か」を必ず図に書き込むこと。
検算は $\triangle\mathrm{OAB}$ の内角の和 $32^\circ+32^\circ+116^\circ=180^\circ$ と、
$58^\circ+122^\circ=180^\circ$（円に内接する四角形の向かい合う角の和）の2本で。""",
   "chk": lambda: (lambda O=(sp.Float(0), sp.Float(0)),
                          A=(sp.N(sp.cos(sp.rad(212))), sp.N(sp.sin(sp.rad(212)))),
                          B=(sp.N(sp.cos(sp.rad(328))), sp.N(sp.sin(sp.rad(328)))): (
        # 半径1の円に A, B を置いて ∠OAB=32° が本当に成り立つことを確認したうえで、
        # 反対側の弧上の C を何通りか動かし、そのつど ∠ACB を内積で実測する（円周角の定理は使わない）
        abs(_ang(A, O, B) - 32) < 1e-7
        and abs(_dist(O, A) - 1) < 1e-9 and abs(_dist(O, B) - 1) < 1e-9
        and all(abs(_ang((sp.N(sp.cos(sp.rad(d))), sp.N(sp.sin(sp.rad(d)))), A, B) - 58) < 1e-7
                for d in (90, 60, 150, 340))
        and all(abs(_ang((sp.N(sp.cos(sp.rad(d))), sp.N(sp.sin(sp.rad(d)))), A, B) - 122) < 1e-7
                for d in (250, 270, 300))))()},

  {"group": "円周角・方べきの定理", "level": "standard",
   "skill": "GE5", "sub": [],
   "stem": "中心 $\\mathrm{O}$ の円の外部に点 $\\mathrm{P}$ があり、$\\mathrm{OP}=10$ とする。"
           "$\\mathrm{P}$ を通る直線が円と2点 $\\mathrm{A}$、$\\mathrm{B}$ で交わり "
           "($\\mathrm{PA}\\lt\\mathrm{PB}$)、$\\mathrm{PA}=4$、$\\mathrm{AB}=5$ である。"
           "また $\\mathrm{P}$ から円に引いた接線の接点を $\\mathrm{T}$ とする。<br>"
           "(1) 線分 $\\mathrm{PT}$ の長さ　(2) 円の半径 $r$　を求めよ。",
   "answer": "(1) $\\mathrm{PT}=6$　(2) $r=8$",
   "figure": _fig_houbeki(),
   "explanation": r"""▶ 円の外の1点 $\mathrm{P}$ から直線を引くと、向きをどう変えても
「$\mathrm{P}$ から2つの交点までの距離の積」が同じ値になる。これが方べき。
接線は<b>2つの交点が重なった場合</b>と見るので、積は $\mathrm{PT}\times\mathrm{PT}=\mathrm{PT}^{2}$ になる。
① まず $\mathrm{PB}$ を作る。$\mathrm{P}$、$\mathrm{A}$、$\mathrm{B}$ の順に並ぶので
$\mathrm{PB}=\mathrm{PA}+\mathrm{AB}=4+5=9$。
② 方べきの定理より $\mathrm{PT}^{2}=\mathrm{PA}\cdot\mathrm{PB}=4\times 9=36$。
$\mathrm{PT}$ は長さなので正をとって $\mathrm{PT}=6$。
③ (2) は接線のもう一つの性質を使う。<b>接点を通る半径は接線と垂直</b>なので $\mathrm{OT}\perp\mathrm{PT}$、
つまり $\triangle\mathrm{OTP}$ は $\mathrm{T}$ が直角の直角三角形。
④ 三平方の定理より $r^{2}=\mathrm{OT}^{2}=\mathrm{OP}^{2}-\mathrm{PT}^{2}=10^{2}-6^{2}=100-36=64$。
よって $r=8$。
★ 事故の1位は①をとばして $\mathrm{PB}=5$ としてしまうこと。<b>$\mathrm{AB}=5$ は $\mathrm{A}$ から $\mathrm{B}$ までで、
$\mathrm{P}$ からではない</b>。図に $\mathrm{P}$、$\mathrm{A}$、$\mathrm{B}$ の並び順を書き込み、
$\mathrm{PB}=\mathrm{PA}+\mathrm{AB}$ を必ず一度手で書くこと。
検算には<b>方べきの値を2通りで出す</b>とよい。割線からは $\mathrm{PA}\cdot\mathrm{PB}=36$、
中心からは $\mathrm{OP}^{2}-r^{2}=100-64=36$。ここが一致すれば $\mathrm{PT}$ と $r$ が同時に正しい。""",
   "chk": lambda: (lambda z=_p7_solve(): (
        # 与件(OP=10, PA=4, AB=5)だけを条件に、直線と円の交点の方程式・接線の垂直条件から
        # PB・r・PT を解き直す。解説①(PB=PA+AB=9)も検算の対象に入れる
        z is not None and sp.simplify(z[0] - 8) == 0 and sp.simplify(z[1] - 6) == 0
        and sp.simplify(z[2] - 9) == 0))()},

  {"group": "円周角・方べきの定理", "level": "standard",
   "skill": "GE5", "sub": [],
   "stem": "円 $\\mathrm{O}$ の外部の点 $\\mathrm{P}$ から円に接線をひき、接点を $\\mathrm{T}$ とすると "
           "$\\mathrm{PT}=12$ であった。また $\\mathrm{P}$ を通る別の直線が円と2点 $\\mathrm{A}$、"
           "$\\mathrm{B}$ で交わり ($\\mathrm{PA}\\lt\\mathrm{PB}$)、$\\mathrm{PA}=8$ である。<br>"
           "(1) 線分 $\\mathrm{AB}$ の長さ　(2) 円の半径が $9$ であるときの $\\mathrm{OP}$ の長さ"
           "　を求めよ。",
   "answer": "(1) $\\mathrm{AB}=10$　(2) $\\mathrm{OP}=15$",
   "figure": _fig_sessen(),
   "explanation": r"""▶ 円の外の1点 $\mathrm{P}$ から引いた直線について、$\mathrm{P}$ から2つの交点までの距離の積は
向きを変えても一定で、接線はその2点が重なった場合だから積は $\mathrm{PT}^{2}$ になる。
<b>今回は先に分かっているのが「積のほう」</b>なので、割線の側を逆にたどる。
① 接線から積を作る: $\mathrm{PA}\cdot\mathrm{PB}=\mathrm{PT}^{2}=12^{2}=144$。
② $\mathrm{PA}=8$ を入れて $8\times\mathrm{PB}=144$、よって $\mathrm{PB}=18$。
③ 聞かれているのは $\mathrm{AB}$。$\mathrm{P}$、$\mathrm{A}$、$\mathrm{B}$ の順に並ぶので
$\mathrm{AB}=\mathrm{PB}-\mathrm{PA}=18-8=10$。
④ (2) は接線のもう一つの性質。<b>接点を通る半径は接線と垂直</b>なので $\mathrm{OT}\perp\mathrm{PT}$、
つまり $\triangle\mathrm{OTP}$ は $\mathrm{T}$ が直角の直角三角形。
⑤ 三平方の定理より $\mathrm{OP}^{2}=r^{2}+\mathrm{PT}^{2}=9^{2}+12^{2}=81+144=225$、よって $\mathrm{OP}=15$。
★ 事故の1位は③、<b>$\mathrm{PB}=18$ を出したところで丸をつけてしまう</b>こと。
$\mathrm{PB}$ は $\mathrm{P}$ からの長さ、聞かれている $\mathrm{AB}$ は $\mathrm{A}$ からの長さで別物。
$\mathrm{PB}=\mathrm{PA}+\mathrm{AB}$ を図の上に書き込んでから引き算すること。
検算は2本立てで。まず<b>方べきの値を2通りで出す</b>: 割線からは $\mathrm{PA}\cdot\mathrm{PB}=8\times 18=144$、
中心からは $\mathrm{OP}^{2}-r^{2}=225-81=144$。一致すれば (1)(2) が同時に正しい。
もう1本は<b>大きさの筋</b>。$\mathrm{P}$ から円周までは最短が $\mathrm{OP}-r=15-9=6$、最長が $\mathrm{OP}+r=15+9=24$ で、
$\mathrm{PA}=8$ も $\mathrm{PB}=18$ もこの間に収まっている。ここから外れた答えが出たら図が描けていない。""",
   "chk": lambda: (lambda z9=_tangent_secant(9), z6=_tangent_secant(6), z20=_tangent_secant(20): (
        # 与件(PT=12, PA=8)だけを条件に、接線=重解・割線=円周上の2距離として PB を解き直す。
        # 半径を 3 通り変えても AB=PB-PA が動かないこと(=(1)は半径によらない)まで確かめる。
        all(z is not None and sp.simplify(z[1] - 8 - 10) == 0 for z in (z9, z6, z20))
        and sp.simplify(z9[0] - 15) == 0))()},
 ]}
