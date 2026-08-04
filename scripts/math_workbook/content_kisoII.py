# -*- coding: utf-8 -*-
"""数学II「三角関数」「指数関数・対数関数」「微分法」「積分法」基礎徹底問題集の単一ソース。

content_kisoA.py / content_kisoI.py と同じ構造・同じ検証方式。
  ・各問は "av"（答えの値）と "chk"（av を受け取って独立再計算する関数）を持つ
  ・証明問題は "proof": True を立てて av を省く

■ 位置づけ
  高2以降で脱落が集中する4分野。数Iの二次関数と因数分解ができている前提で組んである。
  三角関数は弧度法、対数は定義（$a^p=M \\iff p=\\log_a M$）でつまずくので、そこを厚くした。
"""
import sympy as sp
from sympy import Rational as R, sqrt, symbols, solve, S, Interval, oo, log, exp, pi

x, t = symbols("x t", real=True)


def _eq(p, q):
    return sp.simplify(sp.nsimplify(p) - sp.nsimplify(q)) == 0


def _same_expr(p, q):
    return sp.simplify(sp.expand(p) - sp.expand(q)) == 0


def _sset(vals):
    return sorted(sp.nsimplify(v) for v in vals)


def _same_trig(f, g):
    """2つの三角式が恒等的に等しいか（合成の検証用）。"""
    return sp.simplify(sp.expand_trig(f - g)) == 0


def _extremum(f, kind):
    """f の極大値／極小値を、臨界点を解いて2階微分の符号で判定して返す。
    ★「答えの x を chk に書き写す」と、極大と極小を取り違えても通ってしまう。
      どちらであるかの判定こそが検証の核心なので、ここで判定する。"""
    d1, d2 = sp.diff(f, x), sp.diff(f, x, 2)
    vals = []
    for c in sp.solve(d1, x):
        if not c.is_real:
            continue
        s2 = d2.subs(x, c)
        if (kind == "max" and s2 < 0) or (kind == "min" and s2 > 0):
            vals.append(sp.nsimplify(f.subs(x, c)))
    return vals[0] if len(vals) == 1 else None


def _area_between(f, g):
    """曲線 f と g で囲まれた面積。交点を自分で求め、|f-g| を積分する。
    ★積分区間と上下関係を答えから写すと、上下を逆にした誤答でも通る。"""
    pts = sorted(s for s in sp.solve(sp.Eq(f, g), x) if s.is_real)
    if len(pts) != 2:
        return None
    return sp.nsimplify(sp.integrate(sp.Abs(f - g), (x, pts[0], pts[1])))


# ================================================================ 三角関数
U_KODO = {
    "name": "弧度法と三角関数の値",
    "tag": "弧度法・単位円・周期",
    "problems": [
        {"group": "弧度法", "level": "basic",
         "stem": r"$120^\circ$ を弧度法で表せ。",
         "answer": r"$\dfrac{2}{3}\pi$",
         "explanation": r"$180^\circ=\pi$ なので $1^\circ=\dfrac{\pi}{180}$。"
                        r"$120\times\dfrac{\pi}{180}=\dfrac{2}{3}\pi$。",
         "av": 2 * pi / 3, "chk": lambda av: _eq(sp.rad(120), av)},
        {"group": "弧度法", "level": "basic",
         "stem": r"$\dfrac{5}{6}\pi$ を度数法で表せ。",
         "answer": r"$150^\circ$",
         "explanation": r"$\pi=180^\circ$ なので $\dfrac{5}{6}\times180=150$。よって $150^\circ$。",
         "av": 150, "chk": lambda av: _eq(sp.deg(5 * pi / 6), av)},
        {"group": "三角関数の値", "level": "basic",
         "stem": r"$\cos\dfrac{\pi}{3}$ の値を求めよ。",
         "answer": r"$\dfrac{1}{2}$",
         "explanation": r"$\dfrac{\pi}{3}=60^\circ$。$1:2:\sqrt3$ の直角三角形より "
                        r"$\cos60^\circ=\dfrac12$。",
         "av": R(1, 2), "chk": lambda av: _eq(sp.cos(pi / 3), av)},
        {"group": "弧度法", "level": "standard",
         "stem": r"半径 $6$、中心角 $\dfrac{\pi}{3}$ の扇形の弧の長さと面積を求めよ。",
         "answer": r"弧の長さ $2\pi$、面積 $6\pi$",
         "explanation": r"弧の長さ $\ell=r\theta=6\cdot\dfrac{\pi}{3}=2\pi$。"
                        r"面積 $S=\dfrac12 r\ell=\dfrac12\cdot6\cdot2\pi=6\pi$"
                        r"（$S=\dfrac12 r^2\theta$ でも同じ）。",
         "av": [2 * pi, 6 * pi],
         "chk": lambda av: (_eq(6 * pi / 3, av[0])
                            and _eq(R(1, 2) * 6 ** 2 * pi / 3, av[1]))},
        {"group": "三角関数の値", "level": "basic",
         "stem": r"$\sin\dfrac{3}{4}\pi$ の値を求めよ。",
         "answer": r"$\dfrac{\sqrt2}{2}$",
         "explanation": r"$\dfrac34\pi=135^\circ$。$\sin(\pi-\theta)=\sin\theta$ より "
                        r"$\sin\dfrac34\pi=\sin\dfrac{\pi}{4}=\dfrac{\sqrt2}{2}$。",
         "av": sqrt(2) / 2, "chk": lambda av: _eq(sp.sin(3 * pi / 4), av)},
        {"group": "三角関数の値", "level": "standard",
         "stem": r"$\cos\dfrac{7}{6}\pi$ の値を求めよ。",
         "answer": r"$-\dfrac{\sqrt3}{2}$",
         "explanation": r"$\dfrac76\pi=210^\circ$ で第3象限。第3象限では $\cos<0$。"
                        r"$\cos\dfrac76\pi=-\cos\dfrac{\pi}{6}=-\dfrac{\sqrt3}{2}$。",
         "av": -sqrt(3) / 2, "chk": lambda av: _eq(sp.cos(7 * pi / 6), av)},
        {"group": "方程式・不等式", "level": "standard",
         "stem": r"$0 \leq \theta < 2\pi$ のとき、$\sin\theta=\dfrac{1}{2}$ を解け。",
         "answer": r"$\theta=\dfrac{\pi}{6},\ \dfrac{5}{6}\pi$",
         "explanation": r"単位円で $y$ 座標が $\dfrac12$ になる点は第1象限と第2象限に1つずつ。"
                        r"$\theta=\dfrac{\pi}{6}$ と $\pi-\dfrac{\pi}{6}=\dfrac56\pi$。"
                        r"★範囲内の解を【全部】書く。1つで止めない。",
         "av": [pi / 6, 5 * pi / 6],
         "chk": lambda av: _sset(sp.solveset(sp.Eq(sp.sin(x), R(1, 2)), x,
                                             Interval.Ropen(0, 2 * pi))) == _sset(av)},
    ],
}

U_KAHO = {
    "name": "加法定理・2倍角・三角関数の合成",
    "tag": "加法定理・2倍角・合成・グラフ",
    "problems": [
        {"group": "加法定理", "level": "basic",
         "stem": r"$\sin(\alpha+\beta)$ を加法定理を用いて $\alpha$, $\beta$ の三角関数で表せ。",
         "answer": r"$\sin\alpha\cos\beta+\cos\alpha\sin\beta$",
         "explanation": r"$\sin$ の加法定理は「サイン・コス・コス・サイン」と唱えて覚える。"
                        r"符号は $\pm$ がそのまま移る（$\sin(\alpha-\beta)$ なら $-$）。",
         "proof": True,
         "chk": lambda av=None: sp.simplify(
             sp.expand_trig(sp.sin(sp.Symbol("A") + sp.Symbol("B")))
             - (sp.sin(sp.Symbol("A")) * sp.cos(sp.Symbol("B"))
                + sp.cos(sp.Symbol("A")) * sp.sin(sp.Symbol("B")))) == 0},
        {"group": "加法定理", "level": "standard",
         "stem": r"加法定理を用いて $\sin75^\circ$ の値を求めよ。",
         "answer": r"$\dfrac{\sqrt6+\sqrt2}{4}$",
         "explanation": r"$75^\circ=45^\circ+30^\circ$。"
                        r"$\sin(\alpha+\beta)=\sin\alpha\cos\beta+\cos\alpha\sin\beta$ より "
                        r"$\dfrac{\sqrt2}{2}\cdot\dfrac{\sqrt3}{2}"
                        r"+\dfrac{\sqrt2}{2}\cdot\dfrac12=\dfrac{\sqrt6+\sqrt2}{4}$。",
         "av": (sqrt(6) + sqrt(2)) / 4,
         "chk": lambda av: _eq(sp.sin(sp.rad(75)), av)},
        {"group": "加法定理", "level": "advanced",
         "stem": r"2倍角の公式を用いて、$\sin\theta=\dfrac{3}{5}$（$\theta$ は鋭角）のとき "
                 r"$\sin2\theta$ を求めよ。",
         "answer": r"$\dfrac{24}{25}$",
         "explanation": r"鋭角なので $\cos\theta=\sqrt{1-\dfrac{9}{25}}=\dfrac45$。"
                        r"$\sin2\theta=2\sin\theta\cos\theta"
                        r"=2\cdot\dfrac35\cdot\dfrac45=\dfrac{24}{25}$。",
         "av": R(24, 25),
         "chk": lambda av: _eq(sp.sin(2 * sp.asin(R(3, 5))), av)},
        {"group": "加法定理", "level": "standard",
         "stem": r"$\cos75^\circ$ の値を求めよ。",
         "answer": r"$\dfrac{\sqrt6-\sqrt2}{4}$",
         "explanation": r"$\cos(\alpha+\beta)=\cos\alpha\cos\beta-\sin\alpha\sin\beta$。"
                        r"$\dfrac{\sqrt2}{2}\cdot\dfrac{\sqrt3}{2}"
                        r"-\dfrac{\sqrt2}{2}\cdot\dfrac12=\dfrac{\sqrt6-\sqrt2}{4}$。"
                        r"★$\cos$ の加法定理は符号が【逆】になる。$\sin$ と混同しない。",
         "av": (sqrt(6) - sqrt(2)) / 4,
         "chk": lambda av: _eq(sp.cos(sp.rad(75)), av)},
        {"group": "三角関数の合成", "level": "standard",
         "stem": r"$\sin\theta+\sqrt{3}\cos\theta$ を $r\sin(\theta+\alpha)$ の形に変形せよ"
                 r"（$r>0$、$-\pi<\alpha\leq\pi$）。",
         "answer": r"$2\sin\left(\theta+\dfrac{\pi}{3}\right)$",
         "explanation": r"$a\sin\theta+b\cos\theta=r\sin(\theta+\alpha)$、"
                        r"$r=\sqrt{a^2+b^2}$、$\cos\alpha=\dfrac{a}{r}$, "
                        r"$\sin\alpha=\dfrac{b}{r}$。"
                        r"$r=\sqrt{1+3}=2$、$\cos\alpha=\dfrac12$, "
                        r"$\sin\alpha=\dfrac{\sqrt3}{2}$ より $\alpha=\dfrac{\pi}{3}$。",
         "av": [2, pi / 3],
         "chk": lambda av: _same_trig(sp.sin(x) + sqrt(3) * sp.cos(x),
                                      av[0] * sp.sin(x + av[1]))},
        {"group": "三角関数の合成", "level": "advanced",
         "stem": r"$0\leq\theta<2\pi$ のとき、$y=\sin\theta+\sqrt{3}\cos\theta$ の"
                 r"最大値を求めよ。",
         "answer": r"最大値 $2$",
         "explanation": r"合成して $y=2\sin\left(\theta+\dfrac{\pi}{3}\right)$。"
                        r"$\sin$ の最大は $1$ なので最大値は $2$。"
                        r"★合成する目的は「$\sin$ 1つにまとめて最大最小を読む」こと。",
         "av": 2,
         "chk": lambda av: _eq(sp.maximum(sp.sin(x) + sqrt(3) * sp.cos(x), x,
                                          Interval(0, 2 * pi)), av)},
        {"group": "グラフ", "level": "standard",
         "stem": r"$y=2\sin\theta$ の周期と最大値を求めよ。",
         "answer": r"周期 $2\pi$、最大値 $2$",
         "explanation": r"$y=a\sin(b\theta)$ の周期は $\dfrac{2\pi}{|b|}$。"
                        r"ここは $b=1$ なので周期 $2\pi$。振幅 $|a|=2$ が最大値。"
                        r"★$y=\sin2\theta$ なら周期は $\pi$（横に縮む）。$a$ と $b$ の役割を"
                        r"取り違えない。",
         "av": [2 * pi, 2],
         "chk": lambda av: (_eq(sp.periodicity(2 * sp.sin(x), x), av[0])
                            and _eq(sp.maximum(2 * sp.sin(x), x, Interval(0, 2 * pi)), av[1]))},
        {"group": "三角不等式", "level": "advanced",
         "stem": r"$0\leq\theta<2\pi$ のとき、$\sin\theta>\dfrac{1}{2}$ を解け。",
         "answer": r"$\dfrac{\pi}{6}<\theta<\dfrac{5}{6}\pi$",
         "explanation": r"まず $\sin\theta=\dfrac12$ の解 $\dfrac{\pi}{6},\ \dfrac56\pi$ を求める。"
                        r"単位円で $y>\dfrac12$ になるのはこの2点の【間】。"
                        r"よって $\dfrac{\pi}{6}<\theta<\dfrac56\pi$。"
                        r"★不等式は必ず単位円をかいて、どちら側かを目で確かめる。",
         "av": [pi / 6, 5 * pi / 6],
         "chk": lambda av: sp.solveset(sp.sin(x) > R(1, 2), x,
                                       Interval.Ropen(0, 2 * pi))
                           == Interval.open(av[0], av[1])},
    ],
}

# ================================================================ 指数・対数
U_SISU = {
    "name": "指数の拡張と指数関数",
    "tag": "指数法則・累乗根・指数方程式",
    "problems": [
        {"group": "指数法則", "level": "basic",
         "stem": r"$2^{-3}$ の値を求めよ。",
         "answer": r"$\dfrac{1}{8}$",
         "explanation": r"$a^{-n}=\dfrac{1}{a^n}$。よって $2^{-3}=\dfrac{1}{2^3}=\dfrac18$。",
         "av": R(1, 8), "chk": lambda av: _eq(2 ** -3, av)},
        {"group": "指数法則", "level": "basic",
         "stem": r"$8^{\frac{2}{3}}$ の値を求めよ。",
         "answer": r"$4$",
         "explanation": r"$a^{\frac{m}{n}}=\sqrt[n]{a^m}$。"
                        r"$8^{\frac23}=(\sqrt[3]{8})^2=2^2=4$。"
                        r"★$8=2^3$ と直してから $2^{3\cdot\frac23}=2^2$ としてもよい。",
         "av": 4, "chk": lambda av: _eq(8 ** R(2, 3), av)},
        {"group": "指数法則", "level": "standard",
         "stem": r"$\dfrac{3^5 \times 3^{-2}}{3^{4}}$ を簡単にせよ。",
         "answer": r"$\dfrac{1}{3}$",
         "explanation": r"指数は「かけ算は足す・わり算は引く」。"
                        r"$3^{5+(-2)-4}=3^{-1}=\dfrac13$。",
         "av": R(1, 3),
         "chk": lambda av: _eq(3 ** 5 * 3 ** -2 / 3 ** 4, av)},
        {"group": "指数法則", "level": "standard",
         "stem": r"$\sqrt[3]{16}$ を $2^p$ の形で表せ。",
         "answer": r"$2^{\frac{4}{3}}$",
         "explanation": r"$16=2^4$ なので $\sqrt[3]{16}=(2^4)^{\frac13}=2^{\frac43}$。"
                        r"★累乗根は分数指数に直すと指数法則がそのまま使える。",
         "av": R(4, 3),
         "chk": lambda av: _eq(16 ** R(1, 3), 2 ** av)},
        {"group": "指数関数のグラフ", "level": "standard",
         "stem": r"$y=2^x$ と $y=\left(\dfrac12\right)^x$ のグラフについて正しいものを選べ。"
                 r"　(ア) どちらも増加　(イ) どちらも減少　"
                 r"(ウ) 前者は増加、後者は減少　(エ) 前者は減少、後者は増加",
         "answer": r"(ウ) 前者は増加、後者は減少",
         "explanation": r"$y=a^x$ は $a>1$ で増加、$0<a<1$ で減少。"
                        r"どちらも点 $(0,\,1)$ を通り、$x$ 軸が漸近線。"
                        r"$\left(\dfrac12\right)^x=2^{-x}$ なので $y=2^x$ を $y$ 軸で折り返した形。",
         "chk": None},
        {"group": "指数の大小", "level": "standard",
         "stem": r"$\sqrt{2}$, $\sqrt[3]{4}$, $\sqrt[6]{32}$ を小さい順に並べよ。",
         "answer": r"$\sqrt{2}<\sqrt[3]{4}<\sqrt[6]{32}$",
         "explanation": r"すべて $2$ の累乗に直して指数を比べる。"
                        r"$\sqrt2=2^{\frac12}=2^{\frac{3}{6}}$、"
                        r"$\sqrt[3]4=2^{\frac23}=2^{\frac46}$、"
                        r"$\sqrt[6]{32}=2^{\frac56}$。"
                        r"底 $2>1$ なので指数が大きいほど大きい。",
         # av は「小さい順に並べた3つの値」そのもの。答えの並び順を入れかえると chk が落ちる。
         "av": [sqrt(2), 4 ** R(1, 3), 32 ** R(1, 6)],
         "chk": lambda av: ([float(v) for v in av] == sorted(float(v) for v in av)
                            and _eq(av[0], 2 ** R(1, 2))
                            and _eq(av[1], 2 ** R(2, 3))
                            and _eq(av[2], 2 ** R(5, 6)))},
        {"group": "指数方程式", "level": "standard",
         "stem": r"$2^{x}=32$ を解け。",
         "answer": r"$x=5$",
         "explanation": r"$32=2^5$ なので $2^x=2^5$。底がそろえば指数が等しく $x=5$。",
         "av": 5, "chk": lambda av: solve(sp.Eq(2 ** x, 32), x) == [av]},
        {"group": "指数方程式", "level": "advanced",
         "stem": r"$4^{x}-3\cdot2^{x}+2=0$ を解け。",
         "answer": r"$x=0,\ 1$",
         "explanation": r"$4^x=(2^x)^2$ なので $t=2^x$（$t>0$）と置くと $t^2-3t+2=0$。"
                        r"$(t-1)(t-2)=0$ より $t=1,\,2$。"
                        r"$2^x=1$ より $x=0$、$2^x=2$ より $x=1$。"
                        r"★置きかえたら【$t>0$ の条件】を忘れない。",
         "av": [0, 1],
         "chk": lambda av: _sset(solve(sp.Eq(4 ** x - 3 * 2 ** x + 2, 0), x)) == _sset(av)},
    ],
}

U_TAISU = {
    "name": "対数とその性質",
    "tag": "対数の定義・底の変換・対数方程式",
    "problems": [
        {"group": "対数の定義", "level": "basic",
         "stem": r"$\log_2 8$ の値を求めよ。",
         "answer": r"$3$",
         "explanation": r"$\log_a M$ は「$a$ を何乗すると $M$ になるか」。"
                        r"$2^3=8$ なので $\log_2 8=3$。",
         "av": 3, "chk": lambda av: _eq(log(8, 2), av)},
        {"group": "対数の定義", "level": "basic",
         "stem": r"$\log_3 \dfrac{1}{9}$ の値を求めよ。",
         "answer": r"$-2$",
         "explanation": r"$\dfrac19=3^{-2}$ なので $\log_3\dfrac19=-2$。"
                        r"★底が $1$ より大きいとき、真数が $1$ より小さいと対数は負になる"
                        r"（底が $0<a<1$ なら逆に正）。",
         "av": -2, "chk": lambda av: _eq(log(R(1, 9), 3), av)},
        {"group": "対数の定義", "level": "basic",
         "stem": r"$\log_5 25$ の値を求めよ。",
         "answer": r"$2$",
         "explanation": r"$5^2=25$ なので $\log_5 25=2$。",
         "av": 2, "chk": lambda av: _eq(log(25, 5), av)},
        {"group": "対数の定義", "level": "basic",
         "stem": r"$\log_7 1$ の値を求めよ。",
         "answer": r"$0$",
         "explanation": r"$7^0=1$ なので $\log_7 1=0$。"
                        r"★どんな底でも $\log_a 1=0$、$\log_a a=1$。",
         "av": 0, "chk": lambda av: _eq(log(1, 7), av)},
        {"group": "対数の性質", "level": "standard",
         "stem": r"$\log_{10}2+\log_{10}5$ の値を求めよ。",
         "answer": r"$1$",
         "explanation": r"$\log_a M+\log_a N=\log_a MN$。"
                        r"$\log_{10}(2\times5)=\log_{10}10=1$。",
         "av": 1, "chk": lambda av: _eq(log(2, 10) + log(5, 10), av)},
        {"group": "対数の性質", "level": "standard",
         "stem": r"$\log_2 48-\log_2 3$ の値を求めよ。",
         "answer": r"$4$",
         "explanation": r"$\log_a M-\log_a N=\log_a\dfrac{M}{N}$。"
                        r"$\log_2\dfrac{48}{3}=\log_2 16=4$。",
         "av": 4, "chk": lambda av: _eq(log(48, 2) - log(3, 2), av)},
        {"group": "底の変換", "level": "standard",
         "stem": r"$\log_4 8$ の値を求めよ。",
         "answer": r"$\dfrac{3}{2}$",
         "explanation": r"底の変換公式 $\log_a b=\dfrac{\log_c b}{\log_c a}$ で底を $2$ に。"
                        r"$\dfrac{\log_2 8}{\log_2 4}=\dfrac{3}{2}$。",
         "av": R(3, 2), "chk": lambda av: _eq(log(8, 4), av)},
        {"group": "対数方程式", "level": "advanced",
         "stem": r"$\log_2 x+\log_2(x-2)=3$ を解け。",
         "answer": r"$x=4$",
         "explanation": r"左辺をまとめて $\log_2 x(x-2)=3$、すなわち $x(x-2)=2^3=8$。"
                        r"$x^2-2x-8=0$ より $(x-4)(x+2)=0$、$x=4,\,-2$。"
                        r"★【真数条件】$x>0$ かつ $x-2>0$、つまり $x>2$。"
                        r"よって $x=-2$ は不適で、答えは $x=4$ だけ。",
         "av": 4,
         # ★変形後の式から始めず、元の対数式に代入して成り立つことを確認する
         "chk": lambda av: (_eq(log(av, 2) + log(av - 2, 2), 3) and av > 2)},
    ],
}

# ================================================================ 微分・積分
U_BIBUN = {
    "name": "微分係数と導関数",
    "tag": "導関数・接線・増減と極値",
    "problems": [
        {"group": "導関数", "level": "basic",
         "stem": r"$f(x)=x^3-3x^2+2$ を微分せよ。",
         "answer": r"$f'(x)=3x^2-6x$",
         "explanation": r"$(x^n)'=nx^{n-1}$、定数の微分は $0$。"
                        r"$3x^2-3\cdot2x+0=3x^2-6x$。",
         "av": 3 * x ** 2 - 6 * x,
         "chk": lambda av: _same_expr(sp.diff(x ** 3 - 3 * x ** 2 + 2, x), av)},
        {"group": "導関数", "level": "basic",
         "stem": r"$f(x)=2x^3+5x-1$ のとき、$f'(1)$ の値を求めよ。",
         "answer": r"$11$",
         "explanation": r"$f'(x)=6x^2+5$。$f'(1)=6+5=11$。",
         "av": 11,
         "chk": lambda av: _eq(sp.diff(2 * x ** 3 + 5 * x - 1, x).subs(x, 1), av)},
        {"group": "導関数", "level": "basic",
         "stem": r"$f(x)=4x^2-7x+1$ を微分せよ。",
         "answer": r"$f'(x)=8x-7$",
         "explanation": r"$(x^n)'=nx^{n-1}$、定数は $0$。$4\cdot2x-7=8x-7$。",
         "av": 8 * x - 7,
         "chk": lambda av: _same_expr(sp.diff(4 * x ** 2 - 7 * x + 1, x), av)},
        {"group": "接線", "level": "standard",
         "stem": r"曲線 $y=x^2$ 上の点 $(2,\,4)$ における接線の方程式を求めよ。",
         "answer": r"$y=4x-4$",
         "explanation": r"$y'=2x$ より、$x=2$ での傾きは $4$。"
                        r"点 $(2,4)$ を通る傾き $4$ の直線は $y-4=4(x-2)$、"
                        r"すなわち $y=4x-4$。",
         "av": 4 * x - 4,
         "chk": lambda av: _same_expr(
             sp.diff(x ** 2, x).subs(x, 2) * (x - 2) + 4, av)},
        {"group": "微分係数", "level": "basic",
         "stem": r"$f(x)=x^2$ のとき、$x=3$ における微分係数 $f'(3)$ を、"
                 r"定義 $\displaystyle\lim_{h\to0}\dfrac{f(3+h)-f(3)}{h}$ から求めよ。",
         "answer": r"$f'(3)=6$",
         "explanation": r"$\dfrac{(3+h)^2-9}{h}=\dfrac{6h+h^2}{h}=6+h$。"
                        r"$h\to0$ で $6$。"
                        r"★微分係数は「その点での接線の傾き」。公式 $f'(x)=2x$ に $x=3$ でも同じ。",
         "av": 6,
         "chk": lambda av: _eq(sp.limit(((3 + sp.Symbol("h")) ** 2 - 9) / sp.Symbol("h"),
                                        sp.Symbol("h"), 0), av)},
        {"group": "接線", "level": "standard",
         "stem": r"曲線 $y=x^3-2x$ 上の点 $(1,\,-1)$ における接線の方程式を求めよ。",
         "answer": r"$y=x-2$",
         "explanation": r"$y'=3x^2-2$ より $x=1$ での傾きは $1$。"
                        r"$y-(-1)=1\cdot(x-1)$ すなわち $y=x-2$。",
         "av": x - 2,
         "chk": lambda av: _same_expr(
             sp.diff(x ** 3 - 2 * x, x).subs(x, 1) * (x - 1) - 1, av)},
        {"group": "増減と極値", "level": "standard",
         "stem": r"$f(x)=x^3-3x$ の極大値を求めよ。",
         "answer": r"極大値 $2$（$x=-1$ のとき）",
         "explanation": r"$f'(x)=3x^2-3=3(x+1)(x-1)$。"
                        r"$f'$ の符号は $x<-1$ で正、$-1<x<1$ で負、$x>1$ で正。"
                        r"よって $x=-1$ で極大、$f(-1)=-1+3=2$。",
         # ★答えの x を書き写すのは検証ではない。臨界点を解き、2階微分の符号で
         #   「極大かどうか」まで判定してから値を照合する。
         "av": 2,
         "chk": lambda av: _extremum(x ** 3 - 3 * x, "max") == sp.nsimplify(av)},
        {"group": "増減と極値", "level": "advanced",
         "stem": r"$f(x)=x^3-3x$ の極小値を求めよ。",
         "answer": r"極小値 $-2$（$x=1$ のとき）",
         "explanation": r"$f'(x)=3(x+1)(x-1)$ が $x=1$ の前後で負から正に変わるので極小。"
                        r"$f(1)=1-3=-2$。"
                        r"★増減表を必ずかく。$f'=0$ だけで極値と決めつけない"
                        r"（$y=x^3$ は $f'(0)=0$ でも極値をもたない）。",
         "av": -2,
         "chk": lambda av: _extremum(x ** 3 - 3 * x, "min") == sp.nsimplify(av)},
    ],
}

U_SEKIBUN = {
    "name": "不定積分・定積分と面積",
    "tag": "積分の計算・定積分・面積",
    "problems": [
        {"group": "不定積分", "level": "basic",
         "stem": r"$\displaystyle\int (3x^2-2x)\,dx$ を求めよ（$C$ は積分定数）。",
         "answer": r"$x^3-x^2+C$",
         "explanation": r"$\displaystyle\int x^n dx=\dfrac{x^{n+1}}{n+1}+C$。"
                        r"$3\cdot\dfrac{x^3}{3}-2\cdot\dfrac{x^2}{2}=x^3-x^2$。"
                        r"★積分定数 $C$ を書き忘れない。",
         "av": x ** 3 - x ** 2,
         "chk": lambda av: _same_expr(sp.integrate(3 * x ** 2 - 2 * x, x), av)},
        {"group": "定積分", "level": "basic",
         "stem": r"$\displaystyle\int_0^2 (3x^2)\,dx$ を求めよ。",
         "answer": r"$8$",
         "explanation": r"$\left[x^3\right]_0^2=2^3-0^3=8$。",
         "av": 8,
         "chk": lambda av: _eq(sp.integrate(3 * x ** 2, (x, 0, 2)), av)},
        {"group": "定積分", "level": "standard",
         "stem": r"$\displaystyle\int_{-1}^{1} (x^2+1)\,dx$ を求めよ。",
         "answer": r"$\dfrac{8}{3}$",
         "explanation": r"$\left[\dfrac{x^3}{3}+x\right]_{-1}^{1}"
                        r"=\left(\dfrac13+1\right)-\left(-\dfrac13-1\right)=\dfrac83$。"
                        r"★偶関数なので $2\displaystyle\int_0^1$ としても速い。",
         "av": R(8, 3),
         "chk": lambda av: _eq(sp.integrate(x ** 2 + 1, (x, -1, 1)), av)},
        {"group": "不定積分", "level": "basic",
         "stem": r"$\displaystyle\int (2x+1)\,dx$ を求めよ（$C$ は積分定数）。",
         "answer": r"$x^2+x+C$",
         "explanation": r"$2\cdot\dfrac{x^2}{2}+x=x^2+x$。積分定数 $C$ を必ず書く。",
         "av": x ** 2 + x,
         "chk": lambda av: _same_expr(sp.integrate(2 * x + 1, x), av)},
        {"group": "定積分", "level": "standard",
         "stem": r"$\displaystyle\int_1^3 (2x-4)\,dx$ を求めよ。",
         "answer": r"$0$",
         "explanation": r"$\left[x^2-4x\right]_1^3=(9-12)-(1-4)=-3+3=0$。"
                        r"★定積分は面積ではなく符号つきの量。$x$ 軸の上と下が打ち消し合うと $0$ になる。",
         "av": 0,
         "chk": lambda av: _eq(sp.integrate(2 * x - 4, (x, 1, 3)), av)},
        {"group": "定積分", "level": "standard",
         "stem": r"$\displaystyle\int_0^1 (x^2-x)\,dx$ を求めよ。",
         "answer": r"$-\dfrac{1}{6}$",
         "explanation": r"$\left[\dfrac{x^3}{3}-\dfrac{x^2}{2}\right]_0^1"
                        r"=\dfrac13-\dfrac12=-\dfrac16$。"
                        r"区間内で被積分関数が負なので値も負になる。",
         "av": R(-1, 6),
         "chk": lambda av: _eq(sp.integrate(x ** 2 - x, (x, 0, 1)), av)},
        {"group": "面積", "level": "standard",
         "stem": r"放物線 $y=x^2$ と直線 $y=x$ で囲まれた部分の面積を求めよ。",
         "answer": r"$\dfrac{1}{6}$",
         "explanation": r"交点は $x^2=x$ より $x=0,\,1$。"
                        r"区間 $0<x<1$ では直線が上なので "
                        r"$S=\displaystyle\int_0^1 (x-x^2)dx"
                        r"=\left[\dfrac{x^2}{2}-\dfrac{x^3}{3}\right]_0^1=\dfrac16$。"
                        r"★（上の関数）−（下の関数）を積分する。順序を逆にすると符号が逆になる。",
         # ★交点と上下関係を答えから丸写しせず、交点を解いて |差| を積分する
         "av": R(1, 6),
         "chk": lambda av: _area_between(x ** 2, x) == sp.nsimplify(av)},
        {"group": "面積", "level": "advanced",
         "stem": r"放物線 $y=x^2-4$ と $x$ 軸で囲まれた部分の面積を求めよ。",
         "answer": r"$\dfrac{32}{3}$",
         "explanation": r"$x^2-4=0$ より $x=\pm2$。区間 $-2<x<2$ では放物線が $x$ 軸より下"
                        r"なので、$S=\displaystyle\int_{-2}^{2}\{0-(x^2-4)\}dx"
                        r"=\displaystyle\int_{-2}^{2}(4-x^2)dx=\dfrac{32}{3}$。"
                        r"★面積は必ず正。下にあるときは符号を反転させてから積分する。",
         "av": R(32, 3),
         "chk": lambda av: _area_between(x ** 2 - 4, sp.Integer(0)) == sp.nsimplify(av)},
    ],
}

PARTS = [
    {"area": "第1編　三角関数",
     "sub": "数学II ／ 弧度法と単位円が土台。度数法のままでは先に進めない",
     "units": [U_KODO, U_KAHO]},
    {"area": "第2編　指数関数・対数関数",
     "sub": "数学II ／ 対数は「$a$ を何乗すると $M$ か」という定義に毎回もどる",
     "units": [U_SISU, U_TAISU]},
    {"area": "第3編　微分法・積分法",
     "sub": "数学II ／ 微分は接線の傾き、積分は面積。増減表と上下関係が要",
     "units": [U_BIBUN, U_SEKIBUN]},
]
