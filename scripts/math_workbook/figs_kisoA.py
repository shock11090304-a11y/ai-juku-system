# -*- coding: utf-8 -*-
"""数学A 基礎徹底問題集（図形の性質）の図。svgfig.Canvas で数学座標から生成する。

★図が必要な理由（レビューで指摘され、実際に問題が起きていた箇所）
  ・外分点（外角の二等分線・メネラウスの交点）は、文章だけだと生徒が内分点として作図し、
    誤った図のまま比だけ暗記してしまう。
  ・2円の位置関係は d と r1+r2, |r1-r2| の大小を図で理解させるのが定番で、
    図が無いと丸暗記になる。
  ・外心の問題は O が内部にある（＝鋭角三角形）ことが図で一目で分かる。

座標はすべて content_kisoA.py の設定と一致させること（図と数値がズレると最悪の事故）。
"""
import math

from svgfig import Canvas, NAVY, RED, GRAY

SZ = (200, 150)


def _tri(c, A, B, C, la="A", lb="B", lc="C"):
    c.poly([A, B, C])
    for (x, y), t, dx, dy in ((A, la, -12, -4), (B, lb, 4, 14), (C, lc, 4, -4)):
        c.label(x, y, t, dx=dx, dy=dy, size=11)


# ---------------------------------------------------------------- 三角形と線分の比
def fig_parallel(t=0.6):
    """DE∥BC（D は AB 上、E は AC 上）。t = AD:AB の比。
    ★本文の比に合わせて D, E を置く（2問で同じ図を使い回すと数値と合わなくなる）。"""
    c = Canvas((-0.6, 6.6), (-0.8, 5.4), SZ)
    A, B, C = (0, 5), (-0.2, 0), (6, 0)
    _tri(c, A, B, C)
    D = (A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t)
    E = (A[0] + (C[0] - A[0]) * t, A[1] + (C[1] - A[1]) * t)
    c.seg(*D, *E, stroke=RED, w=1.8)
    c.dot(*D, RED); c.dot(*E, RED)
    c.label(*D, "D", dx=-13, dy=2, size=11, color=RED)
    c.label(*E, "E", dx=5, dy=2, size=11, color=RED)
    return c.svg()


def _apex(ab, ac, bc):
    """B(0,0), C(bc,0) に対し AB=ab, AC=ac となる頂点 A を計算する。
    ★本文の辺の長さから座標を作ることで、図と本文が食い違わないようにする
      （手で座標を置いた初版は AB<AC に描かれ、本文の AB>AC と逆になっていた）。"""
    x = (ab ** 2 - ac ** 2 + bc ** 2) / (2 * bc)
    y = math.sqrt(max(ab ** 2 - x ** 2, 0.01))
    return (x, y)


def fig_bisector_in(ab=6, ac=4, bc=6.5):
    """∠A の二等分線と辺 BC の交点 D（内分）。BD:DC=AB:AC になる位置に D を置く。"""
    A = _apex(ab, ac, bc)
    B, C = (0, 0), (bc, 0)
    c = Canvas((-0.6, bc + 0.8), (-0.8, A[1] + 0.6), SZ)
    _tri(c, A, B, C)
    D = (bc * ab / (ab + ac), 0)
    c.seg(*A, *D, stroke=RED, w=1.8)
    c.dot(*D, RED)
    c.label(*D, "D", dx=-4, dy=14, size=11, color=RED)
    c.label(1.5, 3.9, "×", dx=-14, dy=0, size=10, color=RED)
    c.label(1.9, 3.9, "×", dx=2, dy=0, size=10, color=RED)
    return c.svg()


def fig_bisector_ex(ab=5, ac=3, bc=4.4):
    """∠A の外角の二等分線と直線 BC の交点 E（★C の側の外分点）。
    BE:EC=AB:AC（外分）なので E は bc*ab/(ab-ac) の位置。AB>AC が前提。"""
    assert ab > ac, "外分点が C 側に来るには AB>AC が必要"
    A = _apex(ab, ac, bc)
    B, C = (0, 0), (bc, 0)
    ex = bc * ab / (ab - ac)
    c = Canvas((-0.8, ex + 1.0), (-0.9, A[1] + 0.8), SZ)
    _tri(c, A, B, C)
    E = (ex, 0)
    c.seg(*C, *E, stroke=GRAY, w=1.1, dash="4 3")     # BC の延長
    c.seg(*A, *E, stroke=RED, w=1.8)                   # 外角の二等分線
    c.seg(A[0], A[1], A[0] + 1.7, A[1] + 1.2, stroke=GRAY, w=1.1, dash="3 2")  # 外角側
    c.dot(*E, RED)
    c.label(*E, "E", dx=2, dy=14, size=11, color=RED)
    c.label((bc + ex) / 2, 0, "外分点", dx=-16, dy=-6, size=9, color=RED)
    return c.svg()


# ---------------------------------------------------------------- 五心・メネラウス
def fig_circumcenter():
    """鋭角三角形の外心 O（内部にある）と外接円。"""
    c = Canvas((-2.6, 2.6), (-2.4, 2.8), SZ)
    r = 2.0
    pts = [(r * math.cos(math.radians(t)), r * math.sin(math.radians(t)))
           for t in (72, 200, 340)]
    c.circle(0, 0, r, stroke=GRAY, w=1.2, dash="4 3")
    _tri(c, *pts)
    c.dot(0, 0, RED)
    c.label(0, 0, "O", dx=4, dy=-4, size=11, color=RED)
    for p in pts:
        c.seg(0, 0, *p, stroke=RED, w=1.0, dash="3 2")
    return c.svg()


def fig_menelaus():
    """メネラウス: D(AB上) E(BC上) を通る直線が、直線 AC を C の側の外側で切る。"""
    c = Canvas((-0.8, 4.4), (-0.8, 6.4), SZ)
    A, B, C = (0, 0), (3, 0), (0, 3)
    D = (2, 0)                       # AB を 2:1
    E = (1, 2)                       # BC を 2:1
    F = (0, 4)                       # 直線DE と 直線AC の交点（★C の外側）
    _tri(c, A, B, C)
    c.seg(0, 3, 0, 4.2, stroke=GRAY, w=1.1, dash="4 3")   # AC の延長
    c.seg(D[0], D[1], F[0], F[1], stroke=RED, w=1.6)
    for p, t, dx, dy in ((D, "D", -3, 14), (E, "E", 6, 0), (F, "F", -13, 2)):
        c.dot(*p, RED); c.label(*p, t, dx=dx, dy=dy, size=11, color=RED)
    return c.svg()


# ---------------------------------------------------------------- 円
def fig_tangent_chord():
    """接弦定理: 接線AT と 弦AB のなす角＝弦ABに関して反対側の弧上の円周角。"""
    c = Canvas((-2.7, 2.7), (-2.7, 2.7), SZ)
    r = 2.0
    A = (r * math.cos(math.radians(215)), r * math.sin(math.radians(215)))
    B = (r * math.cos(math.radians(325)), r * math.sin(math.radians(325)))
    C = (r * math.cos(math.radians(75)), r * math.sin(math.radians(75)))
    c.circle(0, 0, r, stroke=NAVY, w=1.5)
    # A における接線（半径OAに垂直）
    ux, uy = -A[1] / r, A[0] / r
    c.seg(A[0] - ux * 1.9, A[1] - uy * 1.9, A[0] + ux * 1.9, A[1] + uy * 1.9,
          stroke=GRAY, w=1.3)
    c.seg(*A, *B, stroke=RED, w=1.6)          # 弦 AB
    c.seg(*A, *C, stroke=NAVY, w=1.2)
    c.seg(*B, *C, stroke=NAVY, w=1.2)
    for p, t, dx, dy in ((A, "A", -12, 8), (B, "B", 4, 10), (C, "C", 2, -4)):
        c.dot(*p, NAVY); c.label(*p, t, dx=dx, dy=dy, size=11)
    c.label(A[0] + ux * 1.7, A[1] + uy * 1.7, "T", dx=4, dy=4, size=11, color=GRAY)
    return c.svg()


def fig_two_chords():
    """円内で2弦 AB, CD が P で交わる。"""
    c = Canvas((-2.6, 2.6), (-2.6, 2.6), SZ)
    r = 2.0
    ang = {"A": 150, "B": 340, "C": 60, "D": 250}
    pt = {k: (r * math.cos(math.radians(v)), r * math.sin(math.radians(v)))
          for k, v in ang.items()}
    c.circle(0, 0, r, stroke=NAVY, w=1.5)
    c.seg(*pt["A"], *pt["B"], stroke=NAVY, w=1.4)
    c.seg(*pt["C"], *pt["D"], stroke=NAVY, w=1.4)
    # 交点P
    (x1, y1), (x2, y2) = pt["A"], pt["B"]
    (x3, y3), (x4, y4) = pt["C"], pt["D"]
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / d
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / d
    c.dot(px, py, RED)
    c.label(px, py, "P", dx=4, dy=-4, size=11, color=RED)
    for k, p in pt.items():
        c.dot(*p, NAVY)
        c.label(*p, k, dx=6 if p[0] > 0 else -13, dy=-3 if p[1] > 0 else 12, size=11)
    return c.svg()


def fig_power_out():
    """円外の点Pから割線と接線。方べきの定理 PA·PB=PT²。"""
    c = Canvas((-4.6, 2.8), (-2.4, 2.4), SZ)
    r = 1.8
    c.circle(0, 0, r, stroke=NAVY, w=1.5)
    Pp = (-4.0, 0.0)
    c.seg(Pp[0], Pp[1], 2.4, 0, stroke=NAVY, w=1.3)    # 割線（中心を通る）
    c.dot(-r, 0, NAVY); c.dot(r, 0, NAVY)
    c.label(-r, 0, "A", dx=-4, dy=-6, size=11)
    c.label(r, 0, "B", dx=0, dy=-6, size=11)
    # 接点T（PからのTは OT⊥PT）
    d = math.hypot(*Pp)
    a = math.acos(r / d)
    base = math.atan2(Pp[1], Pp[0])
    T = (r * math.cos(base + a), r * math.sin(base + a))
    c.seg(*Pp, *T, stroke=RED, w=1.6)
    c.dot(*T, RED)
    c.label(*T, "T", dx=-2, dy=-6, size=11, color=RED)
    c.dot(*Pp, NAVY)
    c.label(*Pp, "P", dx=-13, dy=4, size=11)
    return c.svg()


def fig_two_circles(kind):
    """2円の位置関係。kind='外接'|'内接'"""
    # ★図に「d = r₁+r₂」等と書くと答えそのものになる（ブラインド解答で
    #   「問題を読まずに正解できた」と指摘された）。ラベルは d だけにする。
    if kind == "外接":
        r1, r2, d = 1.6, 0.7, 2.3            # d = r1+r2
    else:
        r1, r2, d = 1.8, 0.6, 1.2            # d = r1-r2
    lab = "d"
    c = Canvas((-2.4, 3.4), (-2.2, 2.4), SZ)
    c.circle(0, 0, r1, stroke=NAVY, w=1.5)
    c.circle(d, 0, r2, stroke=RED, w=1.5)
    c.seg(0, 0, d, 0, stroke=GRAY, w=1.1, dash="3 2")
    c.dot(0, 0, NAVY); c.dot(d, 0, RED)
    c.label(0, 0, "O₁", dx=-16, dy=-3, size=10)
    c.label(d, 0, "O₂", dx=3, dy=-4, size=10, color=RED)
    c.label(d / 2, 0, lab, dx=-22, dy=16, size=9, color=GRAY)
    return c.svg()


# ---------------------------------------------------------------- 割り当て
# キーは content_kisoA.py の stem の先頭で照合する（問題番号は並べ替えで動くため）
FIGS = {
    # AD:DB=3:2 → AD:AB=3/5
    "$\\triangle ABC$ で、辺 $AB$ 上に点 $D$、辺 $AC$ 上に点 $E$": lambda: fig_parallel(3 / 5),
    # AD:AB=4:6=2/3
    "$\\triangle ABC$ の辺 $AB$ 上に点 $D$、辺 $AC$ 上に点 $E$": lambda: fig_parallel(2 / 3),
    "$\\triangle ABC$ で $AB=6$, $AC=4$": fig_bisector_in,
    "$\\triangle ABC$ で $AB=5$, $AC=3$": fig_bisector_ex,
    "鋭角三角形 $ABC$ の外心": fig_circumcenter,
    "$\\triangle ABC$ で、辺 $AB$ を $2:1$ に内分する点を $D$、辺 $BC$ を $2:1$": fig_menelaus,
    "円$O$ の周上の点 $A$ における接線": fig_tangent_chord,
    "円$O$ の2つの弦": fig_two_chords,
    "円の外部の点 $P$ から引いた直線": fig_power_out,
    "半径がそれぞれ $7$, $3$": lambda: fig_two_circles("外接"),
    "半径がそれぞれ $6$, $2$": lambda: fig_two_circles("内接"),
}


def attach(parts):
    """PARTS の各問に figure を差し込む。付いた数を返す。"""
    n = 0
    for p in parts:
        for u in p["units"]:
            for q in u["problems"]:
                for key, fn in FIGS.items():
                    if q["stem"].startswith(key):
                        q["figure"] = fn()
                        n += 1
                        break
    return n
