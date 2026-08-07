# -*- coding: utf-8 -*-
"""A12 三角形の面積と空間図形（数学I 図形と計量）"""
import os, sys, math, itertools
import sympy as sp
from sympy import Rational as R, sqrt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from svgfig import Canvas, RED, GRAY   # noqa: E402  数学座標→SVG(y上向き)変換


# ---------------------------------------------------------------- chk 用の道具
# ★どれも「面積公式・ヘロン・S=rs・正弦定理」を一切使わない。
#   座標を連立方程式で置き直してから測る = 解説とは別ルートで答えに到達させる。

def _circle_int(P, r1, Q, r2):
    """2円(中心 P・半径 r1)と(中心 Q・半径 r2)の交点を厳密に解いて返す。"""
    px, py = sp.symbols('px py', real=True)
    sols = sp.solve([(px - P[0])**2 + (py - P[1])**2 - r1**2,
                     (px - Q[0])**2 + (py - Q[1])**2 - r2**2], [px, py])
    return [(sp.radsimp(sp.simplify(sx)), sp.radsimp(sp.simplify(sy))) for sx, sy in sols]


def _apex(a, b, c):
    """3辺 a=BC, b=CA, c=AB の三角形を B=(0,0), C=(a,0) と置いたときの頂点 A の座標。
    2円の交点として解くので、面積公式もヘロンも通っていない。"""
    for s in _circle_int((0, 0), c, (a, 0), b):
        if sp.N(s[1]) > 0:
            return s
    raise ValueError("3辺 %s から三角形が作れない" % ((a, b, c),))


def _circumcenter(A, B, C):
    """3点から等距離という条件だけで外心を解く(外接円の公式は使わない)。"""
    ox, oy = sp.symbols('ox oy', real=True)
    d = lambda P: (ox - P[0])**2 + (oy - P[1])**2
    s = sp.solve([sp.Eq(d(A), d(B)), sp.Eq(d(B), d(C))], [ox, oy], dict=True)[0]
    return (sp.simplify(s[ox]), sp.simplify(s[oy]))


def _tetra_vertices(a):
    """1辺 a の正四面体の4頂点を「6辺すべてが a」という条件だけから解く。
    B を原点・C を x 軸上に置き、D は z=0 の面内、A は z>0 側を選ぶ。
    正四面体の高さ $\\sqrt{2/3}\\,a$ や重心の公式といった暗記事項は一切通していない
    (通すと、その公式が間違っていたときに chk も一緒に間違える)。"""
    dx, dy, ax, ay, az = sp.symbols('dx dy ax ay az', real=True)
    a = sp.Integer(a)
    B, C = sp.Matrix([0, 0, 0]), sp.Matrix([a, 0, 0])
    sd = sp.solve([dx**2 + dy**2 - a**2, (dx - a)**2 + dy**2 - a**2], [dx, dy], dict=True)
    D = next(sp.Matrix([s[dx], s[dy], 0]) for s in sd if sp.N(s[dy]) > 0)
    sa = sp.solve([ax**2 + ay**2 + az**2 - a**2,
                   (ax - C[0])**2 + (ay - C[1])**2 + az**2 - a**2,
                   (ax - D[0])**2 + (ay - D[1])**2 + az**2 - a**2], [ax, ay, az], dict=True)
    A = next(sp.Matrix([s[ax], s[ay], s[az]]) for s in sa if sp.N(s[az]) > 0)
    return A, B, C, D


def _quad_vertices():
    """四角形 ABCD (AB=8, AD=3, ∠A=60°, BC=5, CD=3) の4頂点を厳密に求める。
    A を原点・AB を x 軸の正の向きに置き、C は 2円の交点として解く。
    対角線で2つの三角形に分ける解法は一切使っていない。"""
    A = (sp.Integer(0), sp.Integer(0))
    B = (sp.Integer(8), sp.Integer(0))
    D = (3*sp.cos(sp.pi/3), 3*sp.sin(sp.pi/3))
    cands = [p for p in _circle_int(B, 5, D, 3) if sp.N(p[1]) > R(1, 100)]
    return (A, B, cands[0], D)


# ---------------------------------------------------------------- 図
def _fig_quad():
    """四角形 ABCD。頂点 C は連立方程式の解をそのまま投影する(手打ちしない)。
    stem に無い数値(対角線 BD・面積)は書かない。"""
    A, B, C, D = [(float(p[0]), float(p[1])) for p in _quad_vertices()]
    c = Canvas(xr=(-0.7, 8.7), yr=(-0.9, 4.3), size=(215, 125), pad=14)
    c.poly([A, B, C, D])
    # ∠A の弧(60°)を小さな折れ線で描く
    arc = [(0.8*math.cos(math.radians(t)), 0.8*math.sin(math.radians(t)))
           for t in range(0, 61, 10)]
    for (x1, y1), (x2, y2) in zip(arc, arc[1:]):
        c.seg(x1, y1, x2, y2, w=1.0)
    c.label(A[0], A[1], "A", dx=-15, dy=14)
    c.label(B[0], B[1], "B", dx=4, dy=15)
    c.label(C[0], C[1], "C", dx=6, dy=-2)
    c.label(D[0], D[1], "D", dx=-15, dy=-2)
    c.label((A[0] + B[0])/2, (A[1] + B[1])/2, "8", dx=-4, dy=16)
    c.label((B[0] + C[0])/2, (B[1] + C[1])/2, "5", dx=8, dy=4)
    c.label((C[0] + D[0])/2, (C[1] + D[1])/2, "3", dx=-3, dy=-6)
    c.label((D[0] + A[0])/2, (D[1] + A[1])/2, "3", dx=-15, dy=4)
    c.label(1.0, 0.58, "60°", dx=0, dy=4, size=10)
    return c.svg()


# --- 直方体の図: 幾何とラベル配置は _box_geometry() が唯一の出どころ。
#     図(_fig_box)と検査(_fig_box_clearances)が同じ数を読む。片方に座標を手で写すと、
#     ラベルを動かしたときに検査だけ古い座標を見つづけて「通ったのに紙は壊れている」になる。
_BOX_K, _BOX_TH = 0.7, math.radians(45)   # 奥行きの縮率と振り角
_BOX_SIZE = (131, 188)
# ★作図と字の大きさの比。font-size を 12/g、紙幅を 46mm×g にすると、
#   紙に出る字は 10.83pt のまま作図だけが g 倍になる(user unit の意味が g 倍に薄まるため)。
#   g=1 では、『2』が入る唯一の隙間である三角形 ABD が紙の上で高さ 19.7pt しかなく、
#   高さ 8.5pt の『2』を破線 AB・赤い BD・実線 AD の3本から等距離に置くと
#   どの辺のラベルか決まらない(総当たりの上限が クリア 2.76pt・帰属の余裕 0.84pt)。
#   g=1.20 で クリア 4.50pt まで開く。図の高さは 66.0→79.2mm(p20 の余白は 43mm)。
#   ★丸めるのは SVG 属性に 55.199999999999996 のような浮動小数の桁が出るのを避けるため。
_BOX_G = 1.20
_BOX_FS = round(12.0 / _BOX_G, 3)         # ラベルの font-size(user unit)
_BOX_W_MM = round(46.0 * _BOX_G, 2)       # 紙に出す幅
# Chrome の print-to-pdf は文書全体を縮めて刷る。実測(p20 の A-D が 59.65pt、
# font-size 12 が 10.83pt)から逆算した係数。紙の pt に直すときに必ず掛ける。
_CHROME_PRINT_SCALE = 0.90685


def _box_geometry():
    """直方体の投影・引く線分・ラベル配置をまとめて返す。
    返り値: (Canvas, 頂点の math 座標 dict, 線分の list, ラベルの list)
      線分  = (端点名1, 端点名2, 種別)   種別: solid/hidden/diag/red
      ラベル = (文字, アンカーの math 座標, dx, dy, ラベルが指す辺 or None)
    """
    k, th = _BOX_K, _BOX_TH

    def P(u, v, w):
        """u = AD 方向(横)、v = AB 方向(奥行き)、w = AE 方向(上)。"""
        return (u + k*v*math.cos(th), w + k*v*math.sin(th))

    V = {"A": P(0, 0, 0), "B": P(0, 2, 0), "C": P(3, 2, 0), "D": P(3, 0, 0),
         "E": P(0, 0, 6), "F": P(0, 2, 6), "G": P(3, 2, 6), "H": P(3, 0, 6)}
    segs = ([(u, v, "solid") for u, v in
             [("A", "D"), ("D", "H"), ("H", "E"), ("E", "A"),   # 手前の面 ADHE
              ("E", "F"), ("F", "G"), ("G", "H"),               # 上の面
              ("D", "C"), ("C", "G")]]                          # 右の面
            + [(u, v, "hidden") for u, v in
               [("A", "B"), ("B", "C"), ("B", "F")]]            # 見えない辺(奥の頂点 B)
            + [("A", "G", "diag")]                              # 対角線 AG
            + [(u, v, "red") for u, v in
               [("B", "D"), ("D", "E"), ("E", "B")]])           # 三角形 BDE
    mid = lambda u, v: ((V[u][0] + V[v][0])/2, (V[u][1] + V[v][1])/2)
    # ラベルのずらし幅 dx,dy は **g=1 の座標系**で書く(_BOX_G で割って使う)。
    # こうすると g を変えても紙の上のラベル位置は動かず、作図だけが g 倍になる
    # ＝『2』の隙間を広げるために g を上げても、他のラベルを置き直さなくて済む。
    # ★B と H は「頂点のすぐ左下」に置くと灰色の対角線 AG に串刺しにされる
    #   (旧配置は実測 0.00pt = 接触)。B は BC・BF・AG に囲まれた右上の空きへ、
    #   H は AG の反対側(手前の面の中)へ逃がす。
    raw = [("A", V["A"], -14, 14, None), ("B", V["B"], 7, -6.5, None),
           ("C", V["C"], 5, 11, None), ("D", V["D"], 2, 15, None),
           ("E", V["E"], -14, 5, None), ("F", V["F"], -13, -3, None),
           ("G", V["G"], 5, 2, None), ("H", V["H"], -16, 15, None),
           # ★『2』が入る隙間は三角形 ABD だけ。dx,dy は 0.1 刻みの総当たりで
           #   「インクの中心から最も近い線分が AB(2位との差 0.8pt 以上)」を満たす中で
           #   最小クリアランスが最大になる点。旧 (8.5,5.5) は赤い BD のほうが
           #   0.10pt 近く、『2』が BD(=√13、stem に無い値)のラベルに見えうる位置だった。
           ("2", mid("A", "B"), 10.56, 5.76, ("A", "B")),
           ("6", mid("A", "E"), -14, 4, ("A", "E")),
           ("3", mid("A", "D"), -4, 16, ("A", "D"))]
    labels = [(s, a, dx/_BOX_G, dy/_BOX_G, e) for s, a, dx, dy, e in raw]
    # 余白は「いちばん外側のラベルが収まる分」だけ取る(旧 yr/pad は 25% を捨てていた)。
    c = Canvas(xr=(-0.70, 4.70), yr=(-0.62, 7.37), size=_BOX_SIZE, pad=6)
    return c, V, segs, labels


def _fig_box():
    """直方体 ABCD-EFGH (AB=2, AD=3, AE=6) の斜投影。3次元座標を実際に投影して
    2次元の点を計算する。stem に無い数値(AG や各面の対角線の長さ)は書かない。
    ★縦(AE=6)と横(AD=3)は実寸で描く。図に「6」「3」と印字する以上、絵の上でも
      6 が 3 の2倍でなければ数値と絵が食い違う。奥行き(AB=2)だけ 0.7 倍に縮める
      =見取り図の標準(奥行きだけの短縮は読み手が織り込んでいる)。
      以前は高さを 0.55 倍に潰していたため、AE の描画長が AB の 1.65 倍(真値 3.0)
      しかなく、ほぼ立方体に見えていた。
    ★横に取るのは AD(=3)、奥行きに取るのは AB(=2) のほう。逆(AB を横)にすると
      視線が平面 BDE にほぼ含まれ、赤い三角形の頂点 E の投影角が 1.3° まで潰れて
      1本の線に見える。この向きなら 15.4° 開く。
      なお実測では奥行きの向き(角度)をどう振っても投影角は 20° 程度が上限で、
      効くのは「どの辺を奥行きに取るか」。真の ∠BED=31.95° より小さく見えるので、
      図から角を読ませる設問は置いていない(★でも図を信じるなと書いてある)。
    ★紙の寸法は svg(w_mm=...) で決める。既定のままだと CSS の
      `.fig svg{max-height:44mm}` が効き、縦長のこの図は実効スケールが 44mm/215 まで
      落ちて、ラベルが 6.3pt・作図が 16×29mm しかなかった(同じページの四角形の図は
      10.9pt・本文は 9.5pt)。w_mm を渡せばスケールは w_mm/W で決まり、
      ラベルは Chrome の文書縮小(_CHROME_PRINT_SCALE)込みで 10.83pt = 四角形の図と揃う。
    ★ラベルは「大きくすれば済む」ものではない。字を 6.3→10.83pt にすると、今度は
      『2』が入る唯一の隙間である三角形 ABD(破線 AB・赤い BD・実線 AD で囲まれる)に
      収まらなくなる。作図が w_mm=46 のままだとこの三角形は紙の上で高さ 19.7pt しかなく、
      高さ 8.5pt の『2』をどこに置いても3辺からほぼ等距離になり、
      **どの辺の長さを表しているのか決まらない**(総当たりの上限がクリア 2.76pt・
      帰属の余裕 0.84pt。実際、赤い BD のほうが近い配置になっていて、
      『2』が BD=√13 のラベルに見えうる状態だった)。
      → 直し方は「字を動かす」ではなく **作図と字の比を変える**(_BOX_G)。
      配置は _fig_box_clearances() が全ラベル×全線分の距離を紙の pt で測って見張る
      (この検査は unit_check_ia_jaku.py が FIG_CHECKS 経由で実際に回す)。
      現物(p20)の実測: ラベル 10.83pt・最小クリアランス 5.17pt・
      『2』は AB 5.96pt < BD 6.39pt < AD 6.61pt で AB が最近。"""
    c, V, segs, labels = _box_geometry()
    style = {"solid": dict(),
             "hidden": dict(dash="4 3"),
             "diag": dict(stroke=GRAY, w=1.1, dash="3 3"),
             "red": dict(stroke=RED, w=1.5)}
    for u, v, kind in segs:
        p, q = V[u], V[v]
        c.seg(p[0], p[1], q[0], q[1], **style[kind])
    for s, (ax, ay), dx, dy, _edge in labels:
        c.label(ax, ay, s, dx=dx, dy=dy, size=_BOX_FS)
    return c.svg(w_mm=_BOX_W_MM)


# ------------------------------------------------ 直方体の図のラベル配置を見張る検査
# ★『字を大きくしたら線に重なった』は目で見ても気づけない(6.3pt のときは重なりが
#   小さすぎて見えず、実際に灰色の AG がラベル B・H を串刺しにしていた)。
#   紙の pt に直した実距離で機械が測る。

# 字の“インク”の広がり(アンカーからの em オフセット L/R/T/B)。
# 字面(span の bbox)は上に 0.90em の余白を含むので、それで測ると空いている所を
# 「詰まっている」と誤判定する。刷った PDF の Type3 グリフのパスを実測して較正した
# (数字 .045/.602/-.783/.008、英大文字 .013/.735/-.784/.007)。少し外側に丸めてある。
_INK_DIGIT = (0.03, 0.62, -0.80, 0.03)
_INK_CAP = (0.00, 0.75, -0.80, 0.03)
_MIN_CLEAR_PT = 3.5      # ラベルのインクと線分の最小距離
_OWNER_MARGIN_PT = 0.8   # 長さラベルは「指す辺」が2番目より確実に近いこと


def _seg_box_dist(p, q, box):
    """線分 p-q と矩形 box=(x0,y0,x1,y1) の最短距離(交われば 0)。"""
    def pt_seg(P, A, B):
        dx, dy = B[0] - A[0], B[1] - A[1]
        L2 = dx*dx + dy*dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((P[0]-A[0])*dx + (P[1]-A[1])*dy)/L2))
        return math.hypot(P[0] - (A[0] + t*dx), P[1] - (A[1] + t*dy))

    def cross(o, u, v):
        return (u[0]-o[0])*(v[1]-o[1]) - (u[1]-o[1])*(v[0]-o[0])

    def seg_seg(a, b, cc, e):
        d1, d2, d3, d4 = cross(cc, e, a), cross(cc, e, b), cross(a, b, cc), cross(a, b, e)
        if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
            return 0.0
        return min(pt_seg(a, cc, e), pt_seg(b, cc, e), pt_seg(cc, a, b), pt_seg(e, a, b))

    x0, y0, x1, y1 = box
    for P in (p, q):
        if x0 <= P[0] <= x1 and y0 <= P[1] <= y1:
            return 0.0
    co = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return min(seg_seg(p, q, co[i], co[(i + 1) % 4]) for i in range(4))


def _fig_box_clearances(report=False):
    """直方体の図の「全ラベル × 全線分」の距離を紙の pt で測る。
    返り値: 違反メッセージの list(空なら合格)。report=True なら実測値も印字する。

    見るのは3つ。
      (1) どのラベルも、どの線分からも _MIN_CLEAR_PT 以上離れていること(インク箱で測る)。
      (2) 長さのラベル(2/3/6)は、指すべき辺が「いちばん近い辺」であること。
          ★これが要る理由: 三角形 ABD の中では、破線 AB と赤い BD と実線 AD が
            『2』を三方から挟む。AB 以外が近いと『2』は BD(=√13)や AD(=3)の
            ラベルに見え、図が stem に無い値を主張することになる。
          ★帰属は**インクの中心**で測る。箱の角で測ると、『2』のように左上が丸い字は
            角に印字が無いぶん実際より近く出て、紙の順位と入れ替わる
            (実測: 箱の角では AB が最近、紙の実インクでは AD が最近だった)。
            中心なら丸めの影響を受けず、較正誤差は 0.03pt に収まる。
      (3) ラベル同士が重ならないこと。
    """
    c, V, segs, labels = _box_geometry()
    # user unit → 紙の pt(w_mm で幅を固定しているので viewBox 幅で割れば出る)
    pt = (_BOX_W_MM / 25.4 * 72) / _BOX_SIZE[0] * _CHROME_PRINT_SCALE
    S = {n: (c.X(p[0]), c.Y(p[1])) for n, p in V.items()}

    def ink(anchor, dx, dy, s):
        x, y = c.X(anchor[0]) + dx, c.Y(anchor[1]) + dy
        L, R, T, B = _INK_DIGIT if s.isdigit() else _INK_CAP
        return (x + L*_BOX_FS, y + T*_BOX_FS, x + R*_BOX_FS*len(s), y + B*_BOX_FS)

    def pt_seg(P, A, B):
        dx, dy = B[0]-A[0], B[1]-A[1]
        L2 = dx*dx + dy*dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((P[0]-A[0])*dx + (P[1]-A[1])*dy)/L2))
        return math.hypot(P[0]-(A[0]+t*dx), P[1]-(A[1]+t*dy))

    # ★辺の名前は端点名を並べ替えて正規化する。segs は ("E","A") の向きで持っているのに
    #   ラベル側は ("A","E") と書くので、素朴に u+v で引くと KeyError で検査が落ちる
    #   ("検査が壊れている" は "検査が通った" ではない)。
    key = lambda u, v: "".join(sorted((u, v)))
    boxes = [(s, ink(a, dx, dy, s), edge) for s, a, dx, dy, edge in labels]
    errs, rows = [], []
    for s, bx, edge in boxes:
        ds = sorted(((_seg_box_dist(S[u], S[v], bx)*pt, key(u, v)) for u, v, _k in segs))
        cen = ((bx[0]+bx[2])/2, (bx[1]+bx[3])/2)
        cd = sorted(((pt_seg(cen, S[u], S[v])*pt, key(u, v)) for u, v, _k in segs))
        rows.append((s, ds, cd, edge))
        if ds[0][0] < _MIN_CLEAR_PT:
            errs.append(f"直方体の図: ラベル『{s}』が線分 {ds[0][1]} に {ds[0][0]:.2f}pt まで"
                        f"接近(下限 {_MIN_CLEAR_PT}pt)")
        if edge:
            want = key(*edge)
            near, dnear = cd[0][1], cd[0][0]
            if near != want:
                errs.append(f"直方体の図: 長さラベル『{s}』はインクの中心が {near}({dnear:.2f}pt)"
                            f"に最も近く、指すべき {want}"
                            f"({dict((n, d) for d, n in cd)[want]:.2f}pt) ではない"
                            f" → 読み手は『{s}』を {near} の長さだと読む")
            elif cd[1][0] - dnear < _OWNER_MARGIN_PT:
                errs.append(f"直方体の図: 長さラベル『{s}』は {want}={dnear:.2f}pt と "
                            f"{cd[1][1]}={cd[1][0]:.2f}pt がほぼ等距離"
                            f"(差 {cd[1][0]-dnear:.2f}pt < {_OWNER_MARGIN_PT}pt) → どちらの辺の"
                            f"長さか決まらない")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (s1, b1, _), (s2, b2, _) = boxes[i], boxes[j]
            ox = min(b1[2], b2[2]) - max(b1[0], b2[0])
            oy = min(b1[3], b2[3]) - max(b1[1], b2[1])
            if ox > 0 and oy > 0:
                errs.append(f"直方体の図: ラベル『{s1}』と『{s2}』が重なっている")
    # 紙に出る字の大きさ(同じページの四角形の図と揃っていること)
    fs_pt = _BOX_FS * pt
    if not 9.5 <= fs_pt <= 11.5:
        errs.append(f"直方体の図: ラベルが {fs_pt:.2f}pt(同ページの四角形の図は 10.85pt、"
                    f"本文 9.5pt)。size か w_mm を直すこと")
    # 図に出る数値が stem にあるものだけか(図が本文に無い値を主張しない)
    stem_nums = {"2", "3", "6"}
    for s, _a, _dx, _dy, _e in labels:
        if s.isdigit() and s not in stem_nums:
            errs.append(f"直方体の図: stem に無い数値『{s}』を書いている")
    # 図と数値の一致: AE=6 は AD=3 の2倍に「描かれて」いること。
    # ★測るのは math 座標ではなく SVG に実際に書き出す座標。Canvas.X/Y は小数第1位で
    #   丸めるので厳密な 2.000 にはならない(実測 1.998)。許容は 1% ——
    #   丸め(理論上 0.2% 未満)は通し、縦を潰す事故(かつての 0.55 倍 = 比 1.65)は落ちる。
    ad = math.dist(S["A"], S["D"])
    ae = math.dist(S["A"], S["E"])
    if abs(ae/ad - 2.0) > 0.01:
        errs.append(f"直方体の図: AE の描画長が AD の {ae/ad:.3f} 倍。"
                    f"図に 6 と 3 と書く以上ほぼ 2 倍でなければ絵と数値が食い違う")
    if report:
        print(f"  図の幅 {_BOX_W_MM:.1f}mm × 高さ {_BOX_W_MM*_BOX_SIZE[1]/_BOX_SIZE[0]:.1f}mm / "
              f"1 user unit = {pt:.5f}pt / ラベル {fs_pt:.2f}pt / "
              f"AD {ad*pt:.2f}pt・AE {ae*pt:.2f}pt(比 {ae/ad:.3f})")
        for s, ds, cd, edge in sorted(rows, key=lambda z: z[1][0][0]):
            top = "  ".join(f"{n}={d:.2f}" for d, n in ds[:3])
            own = (f"／指す辺 {key(*edge)}: 中心帰属 {cd[0][1]} 余裕 {cd[1][0]-cd[0][0]:+.2f}pt"
                   if edge else "")
            print(f"  『{s}』最短 {ds[0][0]:5.2f}pt (最近辺 {ds[0][1]}){own}   [{top}]")
    return errs


# unit_check_ia_jaku.py が拾って実際に回す(書いただけで呼ばれない検査を作らない)
FIG_CHECKS = [_fig_box_clearances]


def _fig_tetra():
    """正四面体 ABCD と辺 BC 上の点 P。4頂点は _tetra_vertices が距離条件から解いた
    3次元座標をそのまま正射影する(手打ちしない)。
    ★視線(方位角 208°・仰角 32°)は全方位を 2° 刻みで走査して選んだ。判定に使った量は
      (i) 赤い三角形 APD の投影後の最小角 (ii) 6辺の投影長の最大/最小比
      (iii) 各頂点と、その頂点を含まない辺との距離 (iv) P と B・C の距離。
      正四面体は対称性が高く、教科書でよくある「底面を手前に寝かせた向き」
      (方位角 260°〜270° 付近)にすると A・P・D がほぼ一直線に並び、
      赤い三角形の開きが 7° まで潰れて1本の線に見える —— 実測して捨てた。
      採用した向きでは APD の最小角 55°、辺長比 1.51。
    ★破線にするのは CD の1本だけ。4頂点の奥行き(視線方向の成分)を実際に比べ、
      いちばん奥の2頂点を結ぶ辺として機械的に決めている(見た目で決めない)。
    ★AD は正四面体の辺であると同時に △APD の1辺なので、赤で1本だけ引く。
    stem に無い数値(AP・PC・高さ)は書かない。"""
    A3, B3, C3, D3 = _tetra_vertices(6)
    P3 = B3 + (C3 - B3)*R(2, 6)          # BP=2, BC=6 → BC を 1:2 に内分
    ph, el = math.radians(208), math.radians(32)
    sph, cph, sel, cel = math.sin(ph), math.cos(ph), math.sin(el), math.cos(el)

    def PR(v):
        x, y, z = (float(t) for t in v)
        return (-x*sph + y*cph, -(x*cph + y*sph)*sel + z*cel)

    A, B, C, D, P = [PR(v) for v in (A3, B3, C3, D3, P3)]
    c = Canvas(xr=(-3.9, 3.6), yr=(-0.8, 6.7), size=(180, 186), pad=14)
    for p, q in [(A, B), (A, C), (B, C), (B, D)]:            # 見えている辺
        c.seg(p[0], p[1], q[0], q[1])
    c.seg(C[0], C[1], D[0], D[1], stroke=GRAY, w=1.1, dash="4 3")   # 奥に隠れる辺
    for p, q in [(A, P), (P, D), (D, A)]:                    # 三角形 APD
        c.seg(p[0], p[1], q[0], q[1], stroke=RED, w=1.5)
    c.dot(P[0], P[1], color=RED, r=2.4)
    # ★P と BP の「2」は投影後わずか 13px しか離れていない(BP は BC の 1/3)。
    #   同じ向きにずらすと紙で「2 P」と1語に読める(実際に描いて確認した)ので、
    #   P は辺 BC に沿って C 寄りへ、2 は辺の外側へと別々の向きに逃がす。
    for pt, s, dx, dy in [(A, "A", -4, -7), (B, "B", -5, 16), (C, "C", 7, 5),
                          (D, "D", -16, 3), (P, "P", 15, 5)]:
        c.label(pt[0], pt[1], s, dx=dx, dy=dy)
    c.label((A[0] + C[0])/2, (A[1] + C[1])/2, "6", dx=7, dy=-1)
    c.label((B[0] + P[0])/2, (B[1] + P[1])/2, "2", dx=9, dy=11)
    # ★直方体の図と同じ罠。w_mm を渡さないと CSS の .fig svg{max-height:44mm} が
    #   寸法を決め、viewBox が縦 186 と大きいこの図は実効スケールが 44/186 まで落ちて
    #   ラベルが 7.29pt しかなかった(同じ単元の四角形の図は 10.85pt、直方体は 10.83pt)。
    #   作図・ラベル位置はそのまま、紙の幅だけ固定して 9.85pt に揃える。
    return c.svg(w_mm=57.5)


UNIT = {
 "name": "三角形の面積と空間図形",
 "tag": "面積公式・ヘロン・内接円と外接円・空間への持ち込み",
 "problems": [

  {"group": "2辺とはさむ角で面積をとらえる", "level": "basic",
   "skill": "TR6", "sub": ["TR3"],
   "stem": "$\\triangle\\mathrm{ABC}$ において $\\mathrm{AB}=7$、$\\mathrm{AC}=5$、"
           "$\\angle\\mathrm{A}=120^\\circ$ である。$\\triangle\\mathrm{ABC}$ の面積 $S$ を求めよ。",
   "answer": "$S=\\dfrac{35\\sqrt{3}}{4}$",
   "explanation": r"""▶ 面積公式 $S=\frac{1}{2}bc\sin\mathrm{A}$ が使えるのは<b>「2辺と、その2辺にはさまれた角」</b>
がそろったときだけ。高さを別に求める必要は無い —— $c\sin\mathrm{A}$ がそのまま高さの役をしている。
① 与えられた2辺は $\mathrm{AB}=7$ と $\mathrm{AC}=5$ で、$\angle\mathrm{A}$ はちょうどこの2辺にはさまれた角。
条件がそろっているので、そのまま公式に入れてよい。
② $120^\circ$ は鈍角なので $180^\circ-\theta$ の公式で直す:
$\sin 120^\circ=\sin(180^\circ-60^\circ)=\sin 60^\circ=\frac{\sqrt{3}}{2}$。
③ $S=\frac{1}{2}\times 7\times 5\times\frac{\sqrt{3}}{2}=\frac{35}{2}\times\frac{\sqrt{3}}{2}=\frac{35\sqrt{3}}{4}$。
★ この単元の事故1位は<b>鈍角の $\sin$ を負にしてしまう</b>こと。$0^\circ\lt\theta\lt 180^\circ$ では
$\sin\theta$ は<b>常に正</b>で、負になれるのは $\cos$ と $\tan$ だけ。
面積が負になったら、まちがいなくここを間違えている。
その場でできる検算は<b>上限との比較</b>: $\sin\mathrm{A}\leqq 1$ なので
$S\leqq\frac{1}{2}\times 7\times 5=\frac{35}{2}=17.5$。
いま $\frac{35\sqrt{3}}{4}\approx 15.2$ でちゃんと下回っている ✓
（等号が成り立つのは $\angle\mathrm{A}=90^\circ$ のときで、$120^\circ$ はそれより少しつぶれた形だから
やや小さくなる、という向きも合っている）。""",
   "chk": lambda: (lambda B=(sp.Integer(7), sp.Integer(0)),
                    C=(5*sp.cos(2*sp.pi/3), 5*sp.sin(2*sp.pi/3)):
                   sp.simplify(R(1, 2)*sp.Abs(B[0]*C[1] - C[0]*B[1]) - 35*sqrt(3)/4) == 0)()},

  {"group": "2辺とはさむ角で面積をとらえる", "level": "standard",
   "skill": "TR6", "sub": ["TR3"],
   "stem": "$\\triangle\\mathrm{ABC}$ において $\\mathrm{AB}=8$、$\\mathrm{AC}=5$ であり、"
           "面積は $10\\sqrt{2}$ である。$\\angle\\mathrm{A}$ が鈍角であるとき、"
           "$\\angle\\mathrm{A}$ の大きさを求めよ。",
   "answer": "$\\angle\\mathrm{A}=135^\\circ$",
   "explanation": r"""▶ 同じ面積公式を<b>「角を求める向き」</b>に使う問題。式の形は同じでも、
$\sin$ の値から角を逆にたどるところで<b>候補が2つ出る</b>のがこの向きの急所。
① 面積公式に代入する: $10\sqrt{2}=\frac{1}{2}\times 8\times 5\times\sin\mathrm{A}=20\sin\mathrm{A}$。
② よって $\sin\mathrm{A}=\frac{10\sqrt{2}}{20}=\frac{\sqrt{2}}{2}$。
③ $0^\circ\lt\mathrm{A}\lt 180^\circ$ で $\sin\mathrm{A}=\frac{\sqrt{2}}{2}$ となる角は
$\mathrm{A}=45^\circ$ と $\mathrm{A}=135^\circ$ の<b>2つ</b>。
$\sin 135^\circ=\sin(180^\circ-45^\circ)=\sin 45^\circ$ だから、この2つは同じ面積を与える。
④ 条件に「$\angle\mathrm{A}$ は鈍角」とあるので $\mathrm{A}=135^\circ$。
★ ③で $45^\circ$ だけ書いて終わるのが最頻出の失点。
<b>$\sin$ の値から角を求めると必ず $\theta$ と $180^\circ-\theta$ の2つが候補になる</b>
（$\cos$ の値からなら1つに決まる）。
だから面積から角を聞かれた問題には、どこかに「鋭角」「鈍角」「$\mathrm{AB}$ が最大辺」などの
絞り込みの条件が必ず書いてある。見当たらなければ<b>両方が答え</b>である。
検算は答えを式に戻すこと: $\frac{1}{2}\times 8\times 5\times\sin 135^\circ$
$=20\times\frac{\sqrt{2}}{2}=10\sqrt{2}$ ✓ と与えられた面積に戻る。""",
   # ★ stem の AB=8・AC=5・面積 10√2 を直接使い、面積は座標の外積(たすきがけ)で測る。
   #   解説①の中間結果 20(=½·8·5) を打ち直すと stem の取り違えを検出できなくなる。
   #   実測: AC を 6 に変えても AB を 7 に変えても面積を 10√3 に変えても False になる。
   "chk": lambda: (lambda B=sp.Matrix([8, 0]),
                    C=(lambda t: sp.Matrix([5*sp.cos(t), 5*sp.sin(t)])),
                    S=(lambda P, Q: R(1, 2)*sp.Abs(P[0]*Q[1] - Q[0]*P[1])):
                   (lambda cands=[d for d in range(1, 180)
                                  if abs(float(S(B, C(sp.rad(d)))) - float(10*sqrt(2))) < 1e-9]:
                    cands == [45, 135] and [d for d in cands if d > 90] == [135]
                    and sp.simplify(S(B, C(sp.rad(135))) - 10*sqrt(2)) == 0)())()},

  {"group": "3辺だけが分かっているとき", "level": "basic",
   "skill": "TR6", "sub": ["TR5"],
   "stem": "3辺の長さが $4$、$13$、$15$ である三角形の面積 $S$ を求めよ。",
   "answer": "$S=24$",
   "explanation": r"""▶ 分かっているのが3辺だけのときは<b>ヘロンの公式</b>
$S=\sqrt{s(s-a)(s-b)(s-c)}$、$s=\frac{a+b+c}{2}$ が最短。
余弦定理で $\cos$ を出し、$\sin$ に直してから面積公式、という2手でも必ず出せるが、
3辺が整数ならヘロンのほうが計算が軽い。
① $s=\frac{4+13+15}{2}=\frac{32}{2}=16$。<b>$s$ は周の長さそのものではなく、その半分</b>。
② $s-a=16-4=12$、$s-b=16-13=3$、$s-c=16-15=1$。
③ $S=\sqrt{16\times 12\times 3\times 1}=\sqrt{576}=24$。
$\sqrt{\ }$ の中はかけ算のまま素因数で見ると速い: $16\times 12\times 3=16\times 36=576=24^{2}$。
★ 事故1位は<b>$s$ に周の長さ $32$ をそのまま入れる</b>こと。「$s$ は semi（半分）の $s$」と唱えて入れる。
2位は $s-a,\ s-b,\ s-c$ の引き算ミス。これは<b>3つの和が $s$ に戻るか</b>で一瞬で見つかる:
$12+3+1=16=s$ ✓（$(s-a)+(s-b)+(s-c)=3s-2s=s$ なので、これは必ず成り立つ）。
最後に高さで確かめる: 底辺を $15$ とみると高さは $\frac{2S}{15}=\frac{48}{15}=3.2$。
残りの辺 $4$ と $13$ のどちらよりも短く、三角形の形として矛盾しない ✓""",
   "chk": lambda: (lambda P=_apex(15, 13, 4): R(1, 2)*15*P[1] == 24)()},

  {"group": "3辺だけが分かっているとき", "level": "standard",
   "skill": "TR7", "sub": ["TR6", "TR4"],
   "stem": "3辺の長さが $\\mathrm{BC}=14$、$\\mathrm{CA}=13$、$\\mathrm{AB}=15$ である "
           "$\\triangle\\mathrm{ABC}$ について、面積 $S$、内接円の半径 $r$、"
           "外接円の半径 $R$ をそれぞれ求めよ。",
   "answer": "$S=84$、$r=4$、$R=\\dfrac{65}{8}$",
   "explanation": r"""▶ 内接円と外接円は、出どころがまったく違う。
<b>内接円は面積の分け方から</b>: 内心 $\mathrm{I}$ と3頂点を結ぶと三角形が3つに分かれ、
どれも高さが $r$ なので $S=\frac{1}{2}ar+\frac{1}{2}br+\frac{1}{2}cr=rs$。
<b>外接円は正弦定理から</b>: $\frac{a}{\sin\mathrm{A}}=2R$。
どちらも<b>先に面積 $S$ を出しておく</b>と一直線に進む。
① ヘロンで面積: $s=\frac{14+13+15}{2}=21$ なので
$S=\sqrt{21\times(21-14)\times(21-13)\times(21-15)}=\sqrt{21\times 7\times 8\times 6}=\sqrt{7056}=84$。
② 内接円: $S=rs$ より $r=\frac{S}{s}=\frac{84}{21}=4$。
③ 外接円: 正弦定理を使うには $\sin$ が1つ要る。面積公式
$S=\frac{1}{2}\times\mathrm{CA}\times\mathrm{CB}\times\sin\mathrm{C}$ を逆に読んで
$\sin\mathrm{C}=\frac{2S}{13\times 14}=\frac{168}{182}=\frac{12}{13}$。
④ $\angle\mathrm{C}$ の向かい側の辺は $\mathrm{AB}=15$ だから
$2R=\frac{15}{\sin\mathrm{C}}=15\times\frac{13}{12}=\frac{65}{4}$、よって $R=\frac{65}{8}$。
★ 混乱の元は $r$ と $R$ の取り違え。<b>$r$ は面積を割って作る（$r=\frac{S}{s}$）、
$R$ は辺を $\sin$ で割って作る（$2R=\frac{a}{\sin\mathrm{A}}$）</b>と、材料が違うことで区別する。
$r=\frac{S}{s}$ の $s$ もヘロンと同じ「周の半分」で、周そのものではない。
検算は<b>大小の見当</b>が効く。外接円は三角形を丸ごと含むので、$R$ は最大辺の半分
$\frac{15}{2}=7.5$ 以上でなければならない: $\frac{65}{8}=8.125$ ✓
内接円は三角形に収まるので $2r$ は最小の高さ以下: 最小の高さは $\frac{2S}{15}=11.2$ で $2r=8$ ✓
どちらかが破れていたら、①の $S$ から疑うこと。""",
   "chk": lambda: (lambda P=_apex(14, 13, 15): (
                   R(1, 2)*14*P[1] == 84
                   and (lambda I=tuple((14*u + 13*v + 15*w)/sp.Integer(14 + 13 + 15)
                                       for u, v, w in zip(P, (0, 0), (14, 0))): I[1] == 4)()
                   and sp.simplify(sp.sqrt(sum((u - v)**2 for u, v in
                                   zip(_circumcenter(P, (0, 0), (14, 0)), P))) - R(65, 8)) == 0))()},

  {"group": "三角形に切り分けて考える（四角形・空間）", "level": "standard",
   "skill": "TR6", "sub": ["TR5"],
   "stem": "右の図の四角形 $\\mathrm{ABCD}$ において、$\\mathrm{AB}=8$、$\\mathrm{BC}=5$、"
           "$\\mathrm{CD}=3$、$\\mathrm{DA}=3$、$\\angle\\mathrm{A}=60^\\circ$ である。"
           "四角形 $\\mathrm{ABCD}$ の面積 $S$ を求めよ。",
   "answer": "$S=\\dfrac{39\\sqrt{3}}{4}$",
   "figure": _fig_quad(),
   "explanation": r"""▶ 四角形の面積には公式が無い。<b>対角線を1本引いて三角形2つに切り分ける</b>のが定石。
どちらの対角線を引くかは自由ではなく、<b>与えられた角がまるごと1つの三角形に入るほう</b>を選ぶ。
① $\angle\mathrm{A}=60^\circ$ と、それをはさむ2辺 $\mathrm{AB}=8$、$\mathrm{AD}=3$ がそろっているので、
対角線 $\mathrm{BD}$ を引く。$\triangle\mathrm{ABD}$ は「2辺とはさむ角」の形:
$S_{1}=\frac{1}{2}\times 8\times 3\times\sin 60^\circ=12\times\frac{\sqrt{3}}{2}=6\sqrt{3}$。
② 同じ $\triangle\mathrm{ABD}$ に余弦定理を使って、切り口 $\mathrm{BD}$ の長さも取っておく:
$\mathrm{BD}^{2}=8^{2}+3^{2}-2\times 8\times 3\times\cos 60^\circ=64+9-48\times\frac{1}{2}=49$、$\mathrm{BD}=7$。
③ これで $\triangle\mathrm{BCD}$ は3辺 $\mathrm{BC}=5$、$\mathrm{CD}=3$、$\mathrm{BD}=7$ が分かった。
余弦定理を角を求める向きに使う:
$\cos\mathrm{C}=\frac{5^{2}+3^{2}-7^{2}}{2\times 5\times 3}=\frac{25+9-49}{30}=-\frac{1}{2}$
より $\angle\mathrm{C}=120^\circ$、$\sin\mathrm{C}=\frac{\sqrt{3}}{2}$。
④ $S_{2}=\frac{1}{2}\times 5\times 3\times\frac{\sqrt{3}}{2}=\frac{15\sqrt{3}}{4}$。
⑤ $S=S_{1}+S_{2}=6\sqrt{3}+\frac{15\sqrt{3}}{4}=\frac{24\sqrt{3}+15\sqrt{3}}{4}=\frac{39\sqrt{3}}{4}$。
★ ①で対角線 $\mathrm{AC}$ のほうを引くと、$\triangle\mathrm{ABC}$ も $\triangle\mathrm{ACD}$ も
「2辺とはさむ角」がそろわず、そこで手が止まる。<b>切る前に与えられた角を見る</b>のが順序。
また②を飛ばして③に進もうとすると、$\triangle\mathrm{BCD}$ の材料が2辺しか無くて動けない。
<b>切り口の長さは必ず余弦定理で先に取る</b>。
検算は2本ある。(1) ②で出た $\mathrm{BD}=7$ が $\triangle\mathrm{BCD}$ の辺として成り立つか:
$5+3=8\gt 7$ ✓（もし $\mathrm{BD}\geqq 8$ になったら②の符号ミス）。
(2) 面積の上限: 三角形の面積は「2辺の積の半分」を超えないので
$S\leqq 12+\frac{15}{2}=19.5$。$\frac{39\sqrt{3}}{4}\approx 16.9$ で収まっている ✓
（なお $\angle\mathrm{A}+\angle\mathrm{C}=60^\circ+120^\circ=180^\circ$ となったので、
この四角形はたまたま円に内接する形をしている。）""",
   "chk": lambda: (lambda V=_quad_vertices(): sp.simplify(
                   R(1, 2)*sum(V[i][0]*V[(i + 1) % 4][1] - V[(i + 1) % 4][0]*V[i][1]
                               for i in range(4)) - 39*sqrt(3)/4) == 0)()},

  {"group": "三角形に切り分けて考える（四角形・空間）", "level": "advanced",
   "skill": "TR8", "sub": ["TR5", "TR6"],
   "stem": "右の図の直方体 $\\mathrm{ABCD}$-$\\mathrm{EFGH}$ において、$\\mathrm{AB}=2$、"
           "$\\mathrm{AD}=3$、$\\mathrm{AE}=6$ である。次を求めよ。<br>"
           "(1) 対角線 $\\mathrm{AG}$ の長さ　(2) $\\cos\\angle\\mathrm{BED}$　"
           "(3) $\\triangle\\mathrm{BDE}$ の面積",
   "answer": "$\\mathrm{AG}=7$、$\\cos\\angle\\mathrm{BED}=\\dfrac{3\\sqrt{2}}{5}$、"
             "$\\triangle\\mathrm{BDE}$ の面積は $3\\sqrt{14}$",
   "figure": _fig_box(),
   "explanation": r"""▶ 空間図形は、空間のまま考えようとすると必ず崩れる。
<b>使う三角形を1つだけ抜き出して、平面に描き直す</b>のが手順のすべて。
抜き出す前に、その三角形の3辺を三平方の定理で全部そろえてしまえば、あとは数学I の三角比そのままになる。
① 対角線 $\mathrm{AG}$。まず底面で $\triangle\mathrm{ABC}$ は $\angle\mathrm{B}=90^\circ$ だから
$\mathrm{AC}^{2}=2^{2}+3^{2}=13$。次に $\mathrm{CG}$ は底面に垂直で $\mathrm{CG}=\mathrm{AE}=6$ なので
$\triangle\mathrm{ACG}$ は $\angle\mathrm{C}=90^\circ$。
$\mathrm{AG}^{2}=\mathrm{AC}^{2}+\mathrm{CG}^{2}=13+36=49$、$\mathrm{AG}=7$。
（直方体の対角線は毎回「たて・よこ・高さの2乗をぜんぶ足して平方根」になる。
ここでは $\sqrt{2^{2}+3^{2}+6^{2}}=\sqrt{49}=7$ と一気に書いてよい。）
② $\triangle\mathrm{BDE}$ の3辺を出す。3辺とも直方体の<b>面の対角線</b>で、それぞれ直角三角形の斜辺:
$\mathrm{BD}^{2}=2^{2}+3^{2}=13$、$\mathrm{DE}^{2}=3^{2}+6^{2}=45$、$\mathrm{EB}^{2}=6^{2}+2^{2}=40$。
すなわち $\mathrm{BD}=\sqrt{13}$、$\mathrm{DE}=3\sqrt{5}$、$\mathrm{EB}=2\sqrt{10}$。
③ ここから先は平面の問題。3辺が分かっているので、角 $\angle\mathrm{BED}$ は余弦定理:
$\cos\angle\mathrm{BED}=\frac{\mathrm{EB}^{2}+\mathrm{ED}^{2}-\mathrm{BD}^{2}}{2\times\mathrm{EB}\times\mathrm{ED}}$
$=\frac{40+45-13}{2\times 2\sqrt{10}\times 3\sqrt{5}}=\frac{72}{12\sqrt{50}}=\frac{6}{5\sqrt{2}}=\frac{3\sqrt{2}}{5}$。
④ $\angle\mathrm{BED}$ は三角形の内角なので $\sin\angle\mathrm{BED}\gt 0$:
$\sin\angle\mathrm{BED}=\sqrt{1-\frac{18}{25}}=\frac{\sqrt{7}}{5}$。
⑤ 面積は $\frac{1}{2}\times 2\sqrt{10}\times 3\sqrt{5}\times\frac{\sqrt{7}}{5}$
$=3\sqrt{50}\times\frac{\sqrt{7}}{5}=15\sqrt{2}\times\frac{\sqrt{7}}{5}=3\sqrt{14}$。
★ 空間の事故1位は<b>長さを出す前に、図の見た目で角を決めつける</b>こと
（$\angle\mathrm{BED}$ を $90^\circ$ だと思い込む、$\triangle\mathrm{BDE}$ を二等辺だと思い込む等）。
斜めから描いた図は必ず歪むので、<b>信じてよいのは計算した長さだけ</b>。
実際 $\cos\angle\mathrm{BED}=\frac{3\sqrt{2}}{5}\approx 0.85$ で、$\angle\mathrm{BED}$ は約 $32^\circ$ の鋭い角である。
手順は毎回同じ3段:<b>(i) 使う三角形を決める →(ii) 3辺を三平方で出す →(iii) 平面の余弦定理と面積公式</b>。
検算も2本。(ii) の3辺が三角形になるか: $\sqrt{13}\approx 3.6$、$2\sqrt{10}\approx 6.3$、$3\sqrt{5}\approx 6.7$ で
$3.6+6.3=9.9\gt 6.7$ ✓。もう1本は $|\cos|\leqq 1$ の確認 —— ③で $1$ を超えたら②か③の計算違い。""",
   "chk": lambda: (lambda A=sp.Matrix([0, 0, 0]), B=sp.Matrix([2, 0, 0]),
                    D=sp.Matrix([0, 3, 0]), E=sp.Matrix([0, 0, 6]), G=sp.Matrix([2, 3, 6]): (
                   (G - A).norm() == 7
                   and sp.simplify((B - E).dot(D - E)
                                   / ((B - E).norm()*(D - E).norm()) - 3*sqrt(2)/5) == 0
                   and sp.simplify((B - E).cross(D - E).norm()/2 - 3*sqrt(14)) == 0))()},

  {"group": "三角形に切り分けて考える（四角形・空間）", "level": "advanced",
   "skill": "TR8", "sub": ["TR5", "TR6"],
   "stem": "右の図のように、1辺の長さが $6$ の正四面体 $\\mathrm{ABCD}$ の辺 $\\mathrm{BC}$ 上に、"
           "$\\mathrm{BP}=2$ となる点 $\\mathrm{P}$ をとる。次を求めよ。<br>"
           "(1) 線分 $\\mathrm{AP}$ の長さ　(2) $\\cos\\angle\\mathrm{APD}$　"
           "(3) $\\triangle\\mathrm{APD}$ の面積 $S$",
   "answer": "$\\mathrm{AP}=2\\sqrt{7}$、$\\cos\\angle\\mathrm{APD}=\\dfrac{5}{14}$、"
             "$S=3\\sqrt{19}$",
   "figure": _fig_tetra(),
   "explanation": r"""▶ 手順は前問とまったく同じ3段:<b>(i) 使う三角形を1つ決める →(ii) その3辺を出す
→(iii) 平面の余弦定理と面積公式</b>。変わるのは (ii) の道具だけである。
前問の直方体は面が長方形だったので (ii) は三平方の定理で足りたが、
正四面体は<b>面が正三角形＝どこにも直角が無い</b>。直角の無い面で長さを作るのは余弦定理の仕事。
ここを取り違えて三平方を当てはめようとすると、最初の一歩で止まる。
① $\mathrm{AP}$ を出す。$\mathrm{P}$ は面 $\mathrm{ABC}$ の上にあるので、<b>この面だけを平面に描き直す</b>。
$\triangle\mathrm{ABP}$ は $\mathrm{AB}=6$、$\mathrm{BP}=2$、$\angle\mathrm{ABP}=60^\circ$
（$\mathrm{P}$ が辺 $\mathrm{BC}$ 上にあるので $\angle\mathrm{ABP}$ は正三角形の内角 $\angle\mathrm{ABC}$ そのもの）。
2辺とはさむ角がそろったので余弦定理:
$\mathrm{AP}^{2}=6^{2}+2^{2}-2\times 6\times 2\times\cos 60^\circ=36+4-24\times\frac{1}{2}=28$。
よって $\mathrm{AP}=2\sqrt{7}$。
② $\mathrm{DP}$ も同じ形で出る。辺 $\mathrm{BC}$ は面 $\mathrm{ABC}$ と面 $\mathrm{BCD}$ の<b>両方</b>に属しているので、
$\mathrm{P}$ は面 $\mathrm{BCD}$ の上にもある。$\triangle\mathrm{DBP}$ は $\mathrm{DB}=6$、$\mathrm{BP}=2$、
$\angle\mathrm{DBP}=60^\circ$ で①と数値までそっくり同じ。したがって $\mathrm{DP}^{2}=28$、$\mathrm{DP}=2\sqrt{7}$。
③ これで $\triangle\mathrm{APD}$ の3辺 $\mathrm{PA}=\mathrm{PD}=2\sqrt{7}$、$\mathrm{AD}=6$ がそろった。
ここから先は空間ではなく平面の問題。3辺が分かっているので余弦定理を角を求める向きに使う:
$\cos\angle\mathrm{APD}=\frac{\mathrm{PA}^{2}+\mathrm{PD}^{2}-\mathrm{AD}^{2}}{2\times\mathrm{PA}\times\mathrm{PD}}$
$=\frac{28+28-36}{2\times 2\sqrt{7}\times 2\sqrt{7}}=\frac{20}{56}=\frac{5}{14}$。
④ $\angle\mathrm{APD}$ は三角形の内角なので $\sin\angle\mathrm{APD}\gt 0$:
$\sin\angle\mathrm{APD}=\sqrt{1-\left(\frac{5}{14}\right)^{2}}=\sqrt{\frac{196-25}{196}}=\frac{\sqrt{171}}{14}=\frac{3\sqrt{19}}{14}$。
$171=9\times 19$ と素因数に割って根号の外へ出す。
⑤ $S=\frac{1}{2}\times\mathrm{PA}\times\mathrm{PD}\times\sin\angle\mathrm{APD}$
$=\frac{1}{2}\times 28\times\frac{3\sqrt{19}}{14}=3\sqrt{19}$。
★ 合言葉は<b>「面が長方形なら三平方、面が正三角形なら余弦定理」</b>。
空間で詰まる人の多くは、三角形の選び方ではなく<b>辺の長さを作る道具の選択</b>で止まっている。
事故は2つ。1つめは<b>図の見た目で $\mathrm{P}$ を $\mathrm{BC}$ の中点だと思い込む</b>こと
（$\mathrm{BP}=2$、$\mathrm{PC}=4$ なので中点ではない。斜めから描いた図の比は信じない）。
2つめは<b>$\triangle\mathrm{APD}$ を正三角形だと思い込む</b>こと
（$2\sqrt{7}\approx 5.29$ と $6$ で、二等辺ではあるが正三角形ではない）。
検算は2本。(1) $|\cos\angle\mathrm{APD}|\leqq 1$ を確認する:
$\frac{5}{14}\approx 0.36$ で $\angle\mathrm{APD}$ は約 $69^\circ$。
$60^\circ$ より少し大きい —— 正三角形だと思い込んだ人の答えとはっきり食い違う。
(2) 面積を別ルートで出す。①②から $\mathrm{PA}=\mathrm{PD}$ なので $\triangle\mathrm{APD}$ は
$\mathrm{AD}$ を底辺とする二等辺三角形で、$\mathrm{P}$ から下ろした垂線の足は $\mathrm{AD}$ の中点。
高さは $\sqrt{(2\sqrt{7})^{2}-3^{2}}=\sqrt{28-9}=\sqrt{19}$ だから
$S=\frac{1}{2}\times 6\times\sqrt{19}=3\sqrt{19}$ ✓ ⑤と一致する。
<b>二等辺に気づいたら高さで検算</b>は、余弦定理の計算ミスを一発で暴くので必ずやること。""",
   # ★解説とは別ルート。余弦定理も面積公式も通さず、正四面体を「6辺すべてが 6」という
   #   距離条件だけから連立で解き直し、内分点 P をとって内積(cos)と外積(面積)で測る。
   #   実測: 1辺を 6→7 に変えても BP を 2→3 に変えても、答えのどれか1つでも
   #   ずらしても False になる。所要 3 秒。
   "chk": lambda: (lambda T=_tetra_vertices(6): (lambda A=T[0], B=T[1], C=T[2], D=T[3]: (
                   lambda P=B + (C - B)*R(2, 6): (
                   all(sp.simplify((U - V).norm() - 6) == 0
                       for U, V in itertools.combinations((A, B, C, D), 2))   # 正四面体か
                   and (P - B).norm() == 2 and (C - P).norm() == 4            # P の位置
                   and sp.simplify((A - P).norm() - 2*sqrt(7)) == 0
                   and sp.simplify((A - P).dot(D - P)
                                   / ((A - P).norm()*(D - P).norm()) - R(5, 14)) == 0
                   and sp.simplify((A - P).cross(D - P).norm()/2 - 3*sqrt(19)) == 0))())())()},
 ]}
