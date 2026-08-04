# -*- coding: utf-8 -*-
"""数学I 基礎徹底問題集の図。svgfig.Canvas で数学座標から生成する。

★★図に「答えそのもの」を書かないこと（数Aの2円の図で同じ事故を起こし、
  ここでも二次不等式の解・四分位数・暗記三角形の辺の比で再発させた）。
  図は「形・位置関係」を示すもので、読み取れば答えが出る数値は問題編に書かない。

★figs_kisoA.py と同じ方針:
  図の座標は【本文の数値から計算して】作る。手で座標を置くと本文と食い違う
  （数Aで AB=6>AC=4 の問題に AB<AC の図を付けてしまった前科がある）。

図を入れる基準は「無いと解けない／誤読する」もの:
  ・三角比の定義（どの辺が対辺・隣辺か）
  ・正弦定理と外接円（R が何を指すか）
  ・余弦定理・面積（与えられた2辺と挟角の位置）
  ・二次関数の定義域つき最大最小（頂点が区間の内か外か）
  ・二次不等式（グラフが x 軸の上か下か）
  ・箱ひげ図（四分位数の位置）
"""
import math

from svgfig import Canvas, NAVY, RED, GRAY, FILL

SZ = (210, 150)


def _apex(ab, ac, bc):
    """B(0,0), C(bc,0) に対し AB=ab, AC=ac となる A を計算する（本文の値から作図）。"""
    x = (ab ** 2 - ac ** 2 + bc ** 2) / (2 * bc)
    y = math.sqrt(max(ab ** 2 - x ** 2, 0.01))
    return (x, y)


# ---------------------------------------------------------------- 三角比
def fig_right_triangle():
    """三角比の定義。θ の対辺・隣辺・斜辺がどれかを示す。"""
    c = Canvas((-0.7, 4.6), (-0.9, 3.4), SZ)
    A, B, C = (0, 0), (4, 0), (4, 3)      # ∠B が直角、θ=∠A
    c.poly([A, B, C])
    c.right_angle(4, 0, 0, 0, 4, 3, size=0.35)
    c.label(2, 0, "隣辺 b", dx=-14, dy=14, size=9, color=GRAY)
    c.label(4, 1.5, "対辺 a", dx=4, dy=3, size=9, color=GRAY)
    c.label(2, 1.5, "斜辺 c", dx=-24, dy=-4, size=9, color=RED)
    c.label(0, 0, "θ", dx=10, dy=-3, size=11, color=RED)
    for p, t, dx, dy in ((A, "A", -12, 4), (B, "B", -2, 14), (C, "C", 4, 0)):
        c.label(*p, t, dx=dx, dy=dy, size=11)
    return c.svg()


def fig_special_triangles():
    """暗記する2つの直角三角形（45°と30-60°）。
    ★ラベルは辺の外側に逃がす。斜辺の中点に置くと角度ラベルと重なって読めなくなる
      （初版で実際に重なった）。"""
    c = Canvas((-0.9, 8.0), (-1.1, 3.0), SZ)
    # 45-45-90（辺 1,1,√2）
    c.poly([(0, 0), (2, 0), (2, 2)])
    c.right_angle(2, 0, 0, 0, 2, 2, size=0.26)
    c.label(1, 0, "1", dx=-3, dy=15, size=9)
    c.label(2, 1, "1", dx=5, dy=4, size=9)
    c.label(1.05, 1.05, "√2", dx=-24, dy=-6, size=9, color=RED)   # 斜辺の外側へ
    c.label(0, 0, "45°", dx=13, dy=-5, size=9, color=RED)          # 頂点から離す
    # 30-60-90（辺 1,√3,2）
    ox = 4.6
    c.poly([(ox, 0), (ox + 2.6, 0), (ox + 2.6, 1.5)])
    c.right_angle(ox + 2.6, 0, ox, 0, ox + 2.6, 1.5, size=0.26)
    c.label(ox + 1.3, 0, "√3", dx=-6, dy=15, size=9)
    c.label(ox + 2.6, 0.75, "1", dx=5, dy=4, size=9)
    c.label(ox + 1.35, 0.8, "2", dx=-20, dy=-6, size=9, color=RED)
    c.label(ox, 0, "30°", dx=13, dy=-5, size=9, color=RED)
    return c.svg()


def fig_circumcircle(a=6, ang=30):
    """正弦定理。外接円の半径 R と、辺 a に対する円周角 A の関係。"""
    R = a / (2 * math.sin(math.radians(ang)))
    c = Canvas((-R * 1.25, R * 1.25), (-R * 1.2, R * 1.35), SZ)
    c.circle(0, 0, R, stroke=GRAY, w=1.2, dash="4 3")
    # 弦 BC の長さが a になるよう配置
    half = math.degrees(math.asin(min(a / (2 * R), 1)))
    B = (R * math.cos(math.radians(270 - half)), R * math.sin(math.radians(270 - half)))
    C = (R * math.cos(math.radians(270 + half)), R * math.sin(math.radians(270 + half)))
    A = (R * math.cos(math.radians(80)), R * math.sin(math.radians(80)))
    c.poly([A, B, C])
    c.seg(0, 0, *C, stroke=RED, w=1.3)
    c.dot(0, 0, RED)
    c.label(0, 0, "O", dx=-12, dy=-3, size=10, color=RED)
    c.label(C[0] / 2, C[1] / 2, "R", dx=4, dy=6, size=10, color=RED)
    c.label((B[0] + C[0]) / 2, B[1], "a", dx=-3, dy=14, size=10)
    for p, t, dx, dy in ((A, "A", 2, -4), (B, "B", -13, 12), (C, "C", 4, 12)):
        c.label(*p, t, dx=dx, dy=dy, size=11)
    return c.svg()


def fig_two_sides_angle(b=3, cc=5, ang=60):
    """余弦定理・面積。与えられた2辺 b, c とその間の角 A。"""
    A = (0, 0)
    B = (cc, 0)                                  # AB = c
    C = (b * math.cos(math.radians(ang)), b * math.sin(math.radians(ang)))   # AC = b
    c = Canvas((-0.8, cc + 0.8), (-0.9, max(C[1], 1) + 0.9), SZ)
    c.poly([A, B, C])
    c.label(cc / 2, 0, "c", dx=-3, dy=14, size=10)
    c.label(C[0] / 2, C[1] / 2, "b", dx=-13, dy=-2, size=10)
    c.label((B[0] + C[0]) / 2, (B[1] + C[1]) / 2, "a", dx=6, dy=-2, size=10, color=RED)
    c.label(0, 0, f"{ang}°", dx=10, dy=-4, size=9, color=RED)
    for p, t, dx, dy in ((A, "A", -12, 6), (B, "B", 4, 12), (C, "C", -4, -5)):
        c.label(*p, t, dx=dx, dy=dy, size=11)
    return c.svg()


# ---------------------------------------------------------------- 二次関数
def _parabola(c, f, xs, stroke=NAVY, w=1.7):
    pts = [(v, f(v)) for v in xs]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        c.seg(x1, y1, x2, y2, stroke=stroke, w=w)


def fig_quad_interval(lo=0, hi=3):
    """定義域つき最大最小。y=x^2-4x+1、頂点 x=2 が区間の内にあることを示す。"""
    f = lambda v: v ** 2 - 4 * v + 1
    c = Canvas((-1.2, 4.6), (-4.2, 2.6), SZ)
    c.axes(arrows=False)
    xs = [(-1.2 + 0.15 * i) for i in range(int(5.8 / 0.15) + 1)]
    _parabola(c, f, xs)
    # 定義域を強調
    # ★区間の端の座標を書くと「最大値は x=0 のとき」という答えのヒントになる。
    #   定義域が「どこからどこまでか」と、頂点が区間の内にあることだけを示す。
    c.seg(lo, 0, hi, 0, stroke=RED, w=2.6)
    for v in (lo, hi):
        c.dot(v, f(v), RED)
        c.seg(v, 0, v, f(v), stroke=GRAY, w=0.9, dash="3 2")
    c.label((lo + hi) / 2, 0, "定義域", dx=-14, dy=15, size=9, color=RED)
    c.dot(2, f(2), NAVY)
    c.label(2, f(2), "頂点", dx=5, dy=13, size=9)
    return c.svg()


def fig_quad_inequality():
    """二次不等式。y=x^2-x-6 が x 軸より下になる範囲（2解の間）。"""
    f = lambda v: v ** 2 - v - 6
    c = Canvas((-3.6, 4.6), (-7.2, 3.2), SZ)
    c.axes(arrows=False)
    xs = [(-3.4 + 0.15 * i) for i in range(int(7.8 / 0.15) + 1)]
    _parabola(c, f, xs)
    # ★答え($-2<x<3$)そのものになるので、交点の数値も「y<0」も書かない。
    #   グラフの形（下に凸で x 軸を2点で切る）だけを示す。
    for v in (-2, 3):
        c.dot(v, 0, NAVY)
    return c.svg()


# ---------------------------------------------------------------- データ
def fig_boxplot(data=(1, 3, 5, 7, 9, 11, 13)):
    """箱ひげ図。四分位数の位置を示す（本文のデータから計算する）。"""
    d = sorted(data)
    n = len(d)
    med = d[n // 2]
    q1 = sorted(d[:n // 2])[len(d[:n // 2]) // 2]
    q3 = sorted(d[n // 2 + 1:])[len(d[n // 2 + 1:]) // 2]
    lo, hi = d[0], d[-1]
    c = Canvas((lo - 1.5, hi + 1.5), (-1.6, 1.8), SZ)
    y = 0.4
    c.seg(lo, y, q1, y, stroke=NAVY, w=1.3)          # ひげ
    c.seg(q3, y, hi, y, stroke=NAVY, w=1.3)
    c.poly([(q1, y - 0.55), (q3, y - 0.55), (q3, y + 0.55), (q1, y + 0.55)],
           fill=FILL, stroke=NAVY, w=1.5)
    c.seg(med, y - 0.55, med, y + 0.55, stroke=RED, w=2.0)
    for v in (lo, hi):
        c.seg(v, y - 0.3, v, y + 0.3, stroke=NAVY, w=1.3)
    # ★Q₁ と Q₃ の値を書くと四分位範囲の答えが出てしまう。位置記号だけにする。
    for v, t, col in ((lo, "最小", GRAY), (q1, "Q₁", NAVY), (med, "Q₂", RED),
                      (q3, "Q₃", NAVY), (hi, "最大", GRAY)):
        c.label(v, y - 0.7, t, dx=-9, dy=12, size=8.5, color=col)
    return c.svg()


# ---------------------------------------------------------------- 割り当て
FIGS = {
    "$\\theta$ が鋭角で $\\sin\\theta=\\dfrac{3}{5}$": fig_right_triangle,
    "$\\triangle ABC$ で $a=6$, $A=30^\\circ$": lambda: fig_circumcircle(6, 30),
    "$\\triangle ABC$ で $b=3$, $c=5$, $A=60^\\circ$": lambda: fig_two_sides_angle(3, 5, 60),
    "$\\triangle ABC$ で $b=4$, $c=6$, $A=30^\\circ$": lambda: fig_two_sides_angle(4, 6, 30),
    "$0 \\leq x \\leq 3$ における": lambda: fig_quad_interval(0, 3),
    "$x^2-x-6<0$ を解け": fig_quad_inequality,
    "データ $1,\\ 3,\\ 5,\\ 7,\\ 9,\\ 11,\\ 13$": fig_boxplot,
}


def attach(parts):
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
