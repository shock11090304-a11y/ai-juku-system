# -*- coding: utf-8 -*-
"""数学I「数と式」「集合と命題」「二次関数」「図形と計量」基礎徹底問題集の単一ソース。

content_kisoA.py と同じ構造・同じ検証方式。
  ・数式は $...$ の LaTeX（日本語は $ の外。$\text{}$ に日本語を入れない）
  ・各問は "av"（答えの値）と "chk"（av を受け取って独立再計算する関数）を持つ
    → answer を書き換えると chk が落ちる（answer↔av↔chk を連動させるための設計）
  ・証明問題は答えの値が無いので "proof": True を立てて av を省く

■ 位置づけ
  数Iは全分野が必履修で、共通テスト数学I・Aでも全問必答。
  4大単元（数と式／集合と命題／二次関数／図形と計量／データの分析）を一通り収録。
  ここが崩れていると数II以降がすべて立たないので、基礎やり直しの最優先。
"""
import sympy as sp
from sympy import Rational as R, sqrt, symbols, expand, factor, solve, S, Interval, oo

x, y, a, b, c, t = symbols("x y a b c t", real=True)


def _eq(p, q):
    """sympy で厳密に等しいか。"""
    return sp.simplify(sp.nsimplify(p) - sp.nsimplify(q)) == 0


def _same_expr(p, q):
    """式として同一か（展開して差が0）。"""
    return sp.simplify(sp.expand(p) - sp.expand(q)) == 0


def _sset(vals):
    return sorted(sp.nsimplify(v) for v in vals)


def _from_trig(known, value, lo, hi, want):
    """known(θ)=value を満たすθを区間 (lo, hi) で確定させ、want(θ) を返す。
    ★「鋭角だから正の根」「鈍角だから負」という符号判定こそがこの手の問題の核心。
      sqrt(1-...) と決め打ちすると、その判定を一切検証しないことになる。"""
    sols = sp.solveset(sp.Eq(known(x), value), x, Interval.open(lo, hi))
    sols = list(sols)
    if len(sols) != 1:
        return None
    return sp.simplify(want(sols[0]))


# ================================================================ 数と式
U_TENKAI = {
    "name": "式の展開と因数分解",
    "tag": "乗法公式・たすきがけ・置きかえ",
    "problems": [
        {"group": "展開", "level": "basic",
         "stem": r"$(x+3)(x-5)$ を展開せよ。",
         "answer": r"$x^2-2x-15$",
         "explanation": r"$(x+a)(x+b)=x^2+(a+b)x+ab$ に $a=3,\ b=-5$ を代入。"
                        r"和 $3+(-5)=-2$、積 $3\times(-5)=-15$。",
         "av": x ** 2 - 2 * x - 15,
         "chk": lambda av: _same_expr(expand((x + 3) * (x - 5)), av)},
        {"group": "展開", "level": "basic",
         "stem": r"$(2x-3)^2$ を展開せよ。",
         "answer": r"$4x^2-12x+9$",
         "explanation": r"$(a-b)^2=a^2-2ab+b^2$。"
                        r"$a=2x,\ b=3$ として $4x^2-2\cdot2x\cdot3+9=4x^2-12x+9$。",
         "av": 4 * x ** 2 - 12 * x + 9,
         "chk": lambda av: _same_expr(expand((2 * x - 3) ** 2), av)},
        {"group": "展開", "level": "standard",
         "stem": r"$(x+2y-1)^2$ を展開せよ。",
         "answer": r"$x^2+4y^2+1+4xy-2x-4y$",
         "explanation": r"$(a+b+c)^2=a^2+b^2+c^2+2ab+2bc+2ca$。"
                        r"$a=x,\ b=2y,\ c=-1$ として "
                        r"$x^2+4y^2+1+2\cdot x\cdot 2y+2\cdot 2y\cdot(-1)+2\cdot(-1)\cdot x$。",
         "av": x ** 2 + 4 * y ** 2 + 1 + 4 * x * y - 2 * x - 4 * y,
         "chk": lambda av: _same_expr(expand((x + 2 * y - 1) ** 2), av)},
        {"group": "因数分解", "level": "basic",
         "stem": r"$x^2-7x+12$ を因数分解せよ。",
         "answer": r"$(x-3)(x-4)$",
         "explanation": r"かけて $12$、たして $-7$ になる2数は $-3$ と $-4$。"
                        r"よって $(x-3)(x-4)$。",
         "av": (x - 3) * (x - 4),
         "chk": lambda av: _same_expr(x ** 2 - 7 * x + 12, av)},
        {"group": "因数分解", "level": "standard",
         "stem": r"$2x^2+5x-3$ を因数分解せよ。",
         "answer": r"$(2x-1)(x+3)$",
         "explanation": r"たすきがけ。$2x^2$ を $2x$ と $x$ に、$-3$ を $-1$ と $3$ に分け、"
                        r"$2x\times3+x\times(-1)=5x$ で中央の項に一致。よって $(2x-1)(x+3)$。",
         "av": (2 * x - 1) * (x + 3),
         "chk": lambda av: _same_expr(2 * x ** 2 + 5 * x - 3, av)},
        {"group": "因数分解", "level": "standard",
         "stem": r"$x^2-9y^2$ を因数分解せよ。",
         "answer": r"$(x+3y)(x-3y)$",
         "explanation": r"$a^2-b^2=(a+b)(a-b)$。$a=x,\ b=3y$ として $(x+3y)(x-3y)$。",
         "av": (x + 3 * y) * (x - 3 * y),
         "chk": lambda av: _same_expr(x ** 2 - 9 * y ** 2, av)},
        {"group": "因数分解", "level": "advanced",
         "stem": r"$x^4-5x^2+4$ を因数分解せよ。",
         "answer": r"$(x+1)(x-1)(x+2)(x-2)$",
         "explanation": r"$x^2=t$ と置くと $t^2-5t+4=(t-1)(t-4)$。"
                        r"もどして $(x^2-1)(x^2-4)$、さらに $a^2-b^2$ の形で分解し "
                        r"$(x+1)(x-1)(x+2)(x-2)$。",
         "av": (x + 1) * (x - 1) * (x + 2) * (x - 2),
         "chk": lambda av: _same_expr(x ** 4 - 5 * x ** 2 + 4, av)},
    ],
}

U_JISSU = {
    "name": "実数・絶対値・1次不等式",
    "tag": "有理化・絶対値・不等式の解",
    "problems": [
        {"group": "根号の計算", "level": "basic",
         "stem": r"$\sqrt{18}+\sqrt{8}$ を簡単にせよ。",
         "answer": r"$5\sqrt{2}$",
         "explanation": r"$\sqrt{18}=3\sqrt{2}$、$\sqrt{8}=2\sqrt{2}$。"
                        r"よって $3\sqrt{2}+2\sqrt{2}=5\sqrt{2}$。",
         "av": 5 * sqrt(2), "chk": lambda av: _eq(sqrt(18) + sqrt(8), av)},
        {"group": "根号の計算", "level": "standard",
         "stem": r"$\dfrac{2}{\sqrt{5}-\sqrt{3}}$ の分母を有理化せよ。",
         "answer": r"$\sqrt{5}+\sqrt{3}$",
         "explanation": r"分母・分子に $\sqrt{5}+\sqrt{3}$ をかける。"
                        r"分母は $(\sqrt5)^2-(\sqrt3)^2=5-3=2$ になり、"
                        r"$\dfrac{2(\sqrt5+\sqrt3)}{2}=\sqrt5+\sqrt3$。",
         "av": sqrt(5) + sqrt(3),
         "chk": lambda av: _eq(2 / (sqrt(5) - sqrt(3)), av)},
        {"group": "絶対値", "level": "basic",
         "stem": r"$|3-\pi|$ の値を、根号や絶対値記号を使わずに表せ。",
         "answer": r"$\pi-3$",
         "explanation": r"$\pi=3.14\cdots>3$ なので $3-\pi<0$。"
                        r"負の数の絶対値は符号を変えるので $|3-\pi|=\pi-3$。",
         "av": sp.pi - 3, "chk": lambda av: _eq(sp.Abs(3 - sp.pi), av)},
        {"group": "絶対値", "level": "standard",
         "stem": r"方程式 $|2x-1|=5$ を解け。",
         "answer": r"$x=3,\ -2$",
         "explanation": r"$|A|=5$ は $A=5$ または $A=-5$。"
                        r"$2x-1=5$ より $x=3$、$2x-1=-5$ より $x=-2$。",
         "av": [-2, 3],
         "chk": lambda av: _sset(solve(sp.Eq(sp.Abs(2 * x - 1), 5), x)) == _sset(av)},
        {"group": "1次不等式", "level": "basic",
         "stem": r"不等式 $3x-4<2x+1$ を解け。",
         "answer": r"$x<5$",
         "explanation": r"$x$ を左辺に集めて $3x-2x<1+4$、すなわち $x<5$。",
         "av": 5,
         "chk": lambda av: solve(3 * x - 4 < 2 * x + 1, x) == (x < av)},
        {"group": "1次不等式", "level": "standard",
         "stem": r"不等式 $-2x+3 \geq 9$ を解け。",
         "answer": r"$x \leq -3$",
         "explanation": r"$-2x \geq 6$。両辺を負の数 $-2$ で割るので"
                        r"【不等号の向きが変わる】。よって $x \leq -3$。",
         "av": -3,
         "chk": lambda av: solve(-2 * x + 3 >= 9, x) == (x <= av)},
        {"group": "1次不等式", "level": "standard",
         "stem": r"連立不等式 $\begin{cases}2x-1>3\\ x-5<0\end{cases}$ を解け。",
         "answer": r"$2<x<5$",
         "explanation": r"$2x-1>3$ より $x>2$。$x-5<0$ より $x<5$。"
                        r"両方を満たすのは $2<x<5$（数直線の重なった部分）。",
         "av": (2, 5),
         # sp.And は solveset に直接渡せないので、各不等式の解集合の共通部分をとる
         "chk": lambda av: (sp.solveset(2 * x - 1 > 3, x, S.Reals)
                            & sp.solveset(x - 5 < 0, x, S.Reals)) == Interval.open(*av)},
    ],
}

U_SHUGO = {
    "name": "集合と命題",
    "tag": "共通部分・和集合・必要十分条件・対偶",
    "problems": [
        {"group": "集合", "level": "basic",
         "stem": r"$A=\{1,2,3,4,6,12\}$, $B=\{1,2,4,8\}$ のとき、$A \cap B$ を求めよ。",
         "answer": r"$\{1,2,4\}$",
         "explanation": r"$A \cap B$（共通部分）は両方に入っている要素。$1,2,4$ の3つ。",
         "av": {1, 2, 4},
         "chk": lambda av: {1, 2, 3, 4, 6, 12} & {1, 2, 4, 8} == set(av)},
        {"group": "集合", "level": "basic",
         "stem": r"$A=\{1,3,5\}$, $B=\{3,4,5,6\}$ のとき、$A \cup B$ の要素の個数を求めよ。",
         "answer": r"$5$ 個",
         "explanation": r"$A \cup B=\{1,3,4,5,6\}$ で5個。"
                        r"個数だけなら $n(A)+n(B)-n(A\cap B)=3+4-2=5$ でも出る。",
         "av": 5,
         "chk": lambda av: len({1, 3, 5} | {3, 4, 5, 6}) == av == 3 + 4 - 2},
        {"group": "集合", "level": "standard",
         "stem": r"$100$ 以下の自然数のうち、$4$ の倍数または $6$ の倍数であるものの個数を求めよ。",
         "answer": r"$33$ 個",
         "explanation": r"$4$ の倍数は $25$ 個、$6$ の倍数は $16$ 個、"
                        r"両方（$12$ の倍数）は $8$ 個。"
                        r"$n(A\cup B)=25+16-8=33$。重なりを引くのを忘れない。",
         "av": 33,
         "chk": lambda av: len([n for n in range(1, 101) if n % 4 == 0 or n % 6 == 0]) == av},
        {"group": "命題と条件", "level": "basic",
         "stem": r"命題「$x=2 \Rightarrow x^2=4$」の逆を書け。また、その逆は真か偽か答えよ。",
         "answer": r"逆：$x^2=4 \Rightarrow x=2$。偽（反例 $x=-2$）",
         "explanation": r"逆は仮定と結論を入れかえたもの。"
                        r"$x^2=4$ の解は $x=\pm2$ なので、$x=-2$ が反例になり偽。"
                        r"★「元の命題が真でも逆は真とは限らない」の代表例。",
         "av": -2,
         "chk": lambda av: av ** 2 == 4 and av != 2},
        {"group": "命題と条件", "level": "standard",
         "stem": r"$x$ を実数とする。「$x>3$」は「$x>1$」であるための何条件か。"
                 r"次から選べ。　(ア) 必要十分条件　(イ) 必要条件だが十分条件でない　"
                 r"(ウ) 十分条件だが必要条件でない　(エ) どちらでもない",
         "answer": r"(ウ) 十分条件だが必要条件でない",
         "explanation": r"$x>3$ ならば必ず $x>1$（$\Rightarrow$ が成り立つ）ので【十分条件】。"
                        r"逆に $x>1$ でも $x=2$ のように $x>3$ とは限らないので必要条件ではない。"
                        r"★「範囲が狭いほうが十分条件」と覚える。",
         "chk": None},
        {"group": "命題と条件", "level": "standard",
         "stem": r"命題「$n$ が $6$ の倍数ならば $n$ は偶数である」の対偶を書け。",
         "answer": r"$n$ が偶数でないならば、$n$ は $6$ の倍数でない",
         "explanation": r"対偶は「結論を否定 $\Rightarrow$ 仮定を否定」。"
                        r"元の命題と対偶の真偽はつねに一致するので、"
                        r"証明しにくいときは対偶を示す（背理法とならぶ基本手法）。",
         "chk": None},
        {"group": "命題と条件", "level": "advanced",
         "stem": r"$\sqrt{2}$ が無理数であることの証明で使われる手法を次から選べ。"
                 r"　(ア) 数学的帰納法　(イ) 背理法　(ウ) 対偶による証明　(エ) 場合分け",
         "answer": r"(イ) 背理法",
         "explanation": r"「$\sqrt2$ が有理数である」と仮定して矛盾を導く（背理法）。"
                        r"$\sqrt2=\dfrac{q}{p}$（既約分数）とおくと $q^2=2p^2$ から "
                        r"$p$, $q$ がともに偶数となり、既約に矛盾する。",
         "chk": None},
    ],
}

# ================================================================ 二次関数
U_NIJI1 = {
    "name": "二次関数のグラフ",
    "tag": "平方完成・頂点・平行移動",
    "problems": [
        {"group": "平方完成", "level": "basic",
         "stem": r"$y=x^2-6x+5$ を $y=(x-p)^2+q$ の形に変形せよ。",
         "answer": r"$y=(x-3)^2-4$",
         "explanation": r"$x$ の係数 $-6$ の半分 $-3$ を使って "
                        r"$x^2-6x=(x-3)^2-9$。よって $y=(x-3)^2-9+5=(x-3)^2-4$。",
         "av": (3, -4),
         "chk": lambda av: _same_expr(x ** 2 - 6 * x + 5, (x - av[0]) ** 2 + av[1])},
        {"group": "平方完成", "level": "standard",
         "stem": r"$y=2x^2+8x+3$ の頂点の座標を求めよ。",
         "answer": r"$(-2,\ -5)$",
         "explanation": r"$y=2(x^2+4x)+3=2\{(x+2)^2-4\}+3=2(x+2)^2-5$。"
                        r"よって頂点は $(-2,\,-5)$。"
                        r"★$x^2$ の係数でくくってから平方完成する。",
         "av": (-2, -5),
         "chk": lambda av: _same_expr(2 * x ** 2 + 8 * x + 3,
                                      2 * (x - av[0]) ** 2 + av[1])},
        {"group": "平行移動", "level": "standard",
         "stem": r"$y=x^2$ のグラフを $x$ 軸方向に $2$、$y$ 軸方向に $-3$ だけ平行移動した"
                 r"放物線の式を求めよ。",
         "answer": r"$y=(x-2)^2-3$",
         "explanation": r"$x$ 軸方向に $p$ 平行移動は $x$ を $x-p$ に置きかえる（符号が逆になる）。"
                        r"$y$ 軸方向に $q$ は $+q$。よって $y=(x-2)^2-3$。",
         "av": (2, -3),
         "chk": lambda av: _same_expr((x - 2) ** 2 - 3, (x - av[0]) ** 2 + av[1])},
        {"group": "最大・最小", "level": "basic",
         "stem": r"$y=x^2-4x+1$ の最小値を求めよ。",
         "answer": r"最小値 $-3$（$x=2$ のとき）",
         "explanation": r"$y=(x-2)^2-3$。$(x-2)^2 \geq 0$ なので $x=2$ のとき最小値 $-3$。"
                        r"下に凸なので最大値はない。",
         "av": -3,
         "chk": lambda av: _eq(sp.minimum(x ** 2 - 4 * x + 1, x, S.Reals), av)},
        {"group": "最大・最小", "level": "standard",
         "stem": r"$0 \leq x \leq 3$ における $y=x^2-4x+1$ の最大値を求めよ。",
         "answer": r"最大値 $1$（$x=0$ のとき）",
         "explanation": r"頂点は $x=2$（区間内）で最小。最大は区間の端で起こる。"
                        r"$x=0$ のとき $y=1$、$x=3$ のとき $y=-2$。よって最大値は $1$。"
                        r"★定義域つきの最大最小は「頂点」と「両端」の3か所を必ず調べる。",
         "av": 1,
         "chk": lambda av: _eq(sp.maximum(x ** 2 - 4 * x + 1, x, Interval(0, 3)), av)},
        {"group": "最大・最小", "level": "advanced",
         "stem": r"$-1 \leq x \leq 1$ における $y=-x^2+2x+3$ の最大値と最小値を求めよ。",
         "answer": r"最大値 $4$（$x=1$）、最小値 $0$（$x=-1$）",
         "explanation": r"$y=-(x-1)^2+4$ で上に凸、頂点 $x=1$。"
                        r"頂点が区間の右端なので $x=1$ で最大値 $4$。"
                        r"最小は遠いほうの端 $x=-1$ で $y=-1-2+3=0$。",
         "av": (4, 0),
         "chk": lambda av: (_eq(sp.maximum(-x ** 2 + 2 * x + 3, x, Interval(-1, 1)), av[0])
                            and _eq(sp.minimum(-x ** 2 + 2 * x + 3, x, Interval(-1, 1)), av[1]))},
    ],
}

U_NIJI2 = {
    "name": "二次方程式と二次不等式",
    "tag": "解の公式・判別式・グラフとの対応",
    "problems": [
        {"group": "二次方程式", "level": "basic",
         "stem": r"$x^2-5x+6=0$ を解け。",
         "answer": r"$x=2,\ 3$",
         "explanation": r"かけて $6$、たして $-5$ の2数は $-2$ と $-3$。"
                        r"$(x-2)(x-3)=0$ より $x=2,\,3$。",
         "av": [2, 3],
         "chk": lambda av: _sset(solve(x ** 2 - 5 * x + 6, x)) == _sset(av)},
        {"group": "二次方程式", "level": "standard",
         "stem": r"$2x^2-3x-1=0$ を解の公式を使って解け。",
         "answer": r"$x=\dfrac{3\pm\sqrt{17}}{4}$",
         "explanation": r"$x=\dfrac{-b\pm\sqrt{b^2-4ac}}{2a}$ に "
                        r"$a=2,\ b=-3,\ c=-1$ を代入。"
                        r"$b^2-4ac=9+8=17$ なので $x=\dfrac{3\pm\sqrt{17}}{4}$。",
         "av": [(3 - sqrt(17)) / 4, (3 + sqrt(17)) / 4],
         "chk": lambda av: _sset(solve(2 * x ** 2 - 3 * x - 1, x)) == _sset(av)},
        {"group": "判別式", "level": "standard",
         "stem": r"二次方程式 $x^2+4x+k=0$ が重解をもつとき、定数 $k$ の値を求めよ。",
         "answer": r"$k=4$",
         "explanation": r"重解の条件は判別式 $D=b^2-4ac=0$。"
                        r"$16-4k=0$ より $k=4$。このとき解は $x=-2$（重解）。",
         # ★判別式の式を chk にもう一度書くのは検証ではない（同じ覚え違いなら一緒に通る）。
         #   元の二次式に av を入れて、根が「重根1つ」になることを直接確かめる。
         "av": 4,
         "chk": lambda av: sp.roots(sp.Poly(x ** 2 + 4 * x + av, x)) == {-2: 2}},
        {"group": "判別式", "level": "standard",
         "stem": r"二次方程式 $x^2-2x+3=0$ の実数解の個数を求めよ。",
         "answer": r"$0$ 個（実数解をもたない）",
         "explanation": r"$D=(-2)^2-4\cdot1\cdot3=4-12=-8<0$。"
                        r"$D<0$ なので実数解はない（グラフが $x$ 軸と交わらない）。",
         "av": 0,
         "chk": lambda av: len([s for s in solve(x ** 2 - 2 * x + 3, x) if s.is_real]) == av},
        {"group": "二次不等式", "level": "basic",
         "stem": r"$x^2-x-6<0$ を解け。",
         "answer": r"$-2<x<3$",
         "explanation": r"$(x+2)(x-3)<0$。下に凸のグラフが $x$ 軸より下にあるのは"
                        r"2つの解の【間】。よって $-2<x<3$。",
         "av": (-2, 3),
         "chk": lambda av: sp.solveset(x ** 2 - x - 6 < 0, x, S.Reals)
                           == Interval.open(av[0], av[1])},
        {"group": "二次不等式", "level": "standard",
         "stem": r"$x^2-4x+3 \geq 0$ を解け。",
         "answer": r"$x \leq 1$ または $x \geq 3$",
         "explanation": r"$(x-1)(x-3)\geq0$。下に凸のグラフが $x$ 軸以上になるのは"
                        r"2つの解の【外側】。よって $x\leq1$ または $x\geq3$。"
                        r"★「$<0$ は間、$>0$ は外」。グラフをかいて確認する。",
         "av": (1, 3),
         "chk": lambda av: sp.solveset(x ** 2 - 4 * x + 3 >= 0, x, S.Reals)
                           == sp.Union(Interval(-oo, av[0]), Interval(av[1], oo))},
        {"group": "二次不等式", "level": "advanced",
         "stem": r"すべての実数 $x$ に対して $x^2+2x+k>0$ が成り立つような定数 $k$ の"
                 r"値の範囲を求めよ。",
         "answer": r"$k>1$",
         "explanation": r"下に凸の放物線がつねに $x$ 軸より上にある条件は $D<0$。"
                        r"$D=4-4k<0$ より $k>1$。"
                        r"★「すべての $x$ で正」＝「$x$ 軸と交わらない」＝ $D<0$。",
         # ★判別式を使わず、最小値そのものが正になる k の範囲を求めて照合する
         "av": 1,
         "chk": lambda av: sp.solveset(
             sp.minimum(x ** 2 + 2 * x + sp.Symbol("k", real=True), x, S.Reals) > 0,
             sp.Symbol("k", real=True), S.Reals) == Interval.open(av, oo)},
    ],
}

# ================================================================ 図形と計量
U_SANKAKUHI = {
    "name": "三角比の基本",
    "tag": "定義・相互関係・拡張",
    "problems": [
        {"group": "三角比の値", "level": "basic",
         "stem": r"$\sin 30^\circ$, $\cos 30^\circ$, $\tan 30^\circ$ の値をそれぞれ求めよ。",
         "answer": r"$\sin30^\circ=\dfrac{1}{2}$, $\cos30^\circ=\dfrac{\sqrt3}{2}$, "
                   r"$\tan30^\circ=\dfrac{1}{\sqrt3}$",
         "explanation": r"$1:2:\sqrt3$ の直角三角形（$30^\circ,60^\circ,90^\circ$）で考える。"
                        r"$\tan=\dfrac{\sin}{\cos}=\dfrac{1/2}{\sqrt3/2}=\dfrac{1}{\sqrt3}$。",
         "av": [R(1, 2), sqrt(3) / 2, 1 / sqrt(3)],
         "chk": lambda av: all(_eq(f(sp.pi / 6), v) for f, v in
                               zip((sp.sin, sp.cos, sp.tan), av))},
        {"group": "三角比の値", "level": "standard",
         "stem": r"$\sin 120^\circ$ の値を求めよ。",
         "answer": r"$\dfrac{\sqrt3}{2}$",
         "explanation": r"$\sin(180^\circ-\theta)=\sin\theta$ より "
                        r"$\sin120^\circ=\sin60^\circ=\dfrac{\sqrt3}{2}$。"
                        r"★$90^\circ$ をこえる角の三角比は「$180^\circ-\theta$ に直す」。"
                        r"$\sin$ は符号そのまま、$\cos$ と $\tan$ は符号が反転する。",
         "av": sqrt(3) / 2, "chk": lambda av: _eq(sp.sin(sp.rad(120)), av)},
        {"group": "相互関係", "level": "standard",
         "stem": r"$\theta$ が鋭角で $\sin\theta=\dfrac{3}{5}$ のとき、$\cos\theta$ を求めよ。",
         "answer": r"$\cos\theta=\dfrac{4}{5}$",
         "explanation": r"$\sin^2\theta+\cos^2\theta=1$ より "
                        r"$\cos^2\theta=1-\dfrac{9}{25}=\dfrac{16}{25}$。"
                        r"鋭角なので $\cos\theta>0$、よって $\dfrac{4}{5}$。",
         # ★正の平方根を決め打ちすると「鋭角だから cos>0」という核心を検証できない。
         #   鋭角の範囲でθを確定してから cos を評価する。
         "av": R(4, 5),
         "chk": lambda av: _eq(_from_trig(sp.sin, R(3, 5), 0, sp.pi / 2, sp.cos), av)},
        {"group": "相互関係", "level": "standard",
         "stem": r"$\theta$ が鈍角で $\cos\theta=-\dfrac{1}{3}$ のとき、$\sin\theta$ を求めよ。",
         "answer": r"$\sin\theta=\dfrac{2\sqrt2}{3}$",
         "explanation": r"$\sin^2\theta=1-\dfrac{1}{9}=\dfrac{8}{9}$。"
                        r"鈍角（$90^\circ<\theta<180^\circ$）でも $\sin\theta>0$ なので "
                        r"$\sin\theta=\dfrac{2\sqrt2}{3}$。",
         # ★問題文は cos=-1/3（鈍角）。chk に +1/3 を渡していたので符号が届いていなかった。
         "av": 2 * sqrt(2) / 3,
         "chk": lambda av: _eq(_from_trig(sp.cos, R(-1, 3), sp.pi / 2, sp.pi, sp.sin), av)},
        {"group": "相互関係", "level": "standard",
         "stem": r"$\theta$ が鋭角で $\tan\theta=2$ のとき、$\cos\theta$ を求めよ。",
         "answer": r"$\cos\theta=\dfrac{1}{\sqrt5}$",
         "explanation": r"$1+\tan^2\theta=\dfrac{1}{\cos^2\theta}$ より "
                        r"$\dfrac{1}{\cos^2\theta}=1+4=5$、$\cos^2\theta=\dfrac15$。"
                        r"鋭角なので $\cos\theta>0$、よって $\dfrac{1}{\sqrt5}$。",
         "av": 1 / sqrt(5),
         "chk": lambda av: _eq(_from_trig(sp.tan, 2, 0, sp.pi / 2, sp.cos), av)},
        {"group": "三角比の値", "level": "standard",
         "stem": r"$\tan 135^\circ$ の値を求めよ。",
         "answer": r"$-1$",
         "explanation": r"$\tan(180^\circ-\theta)=-\tan\theta$ より "
                        r"$\tan135^\circ=-\tan45^\circ=-1$。"
                        r"★鈍角では $\tan$ は負。$\sin$ だけが正で、$\cos$ と $\tan$ は負。",
         "av": -1, "chk": lambda av: _eq(sp.tan(sp.rad(135)), av)},
    ],
}

U_SEIGEN = {
    "name": "正弦定理・余弦定理と面積",
    "tag": "正弦定理・余弦定理・三角形の面積",
    "problems": [
        {"group": "正弦定理", "level": "basic",
         "stem": r"$\triangle ABC$ で $a=6$, $A=30^\circ$ のとき、外接円の半径 $R$ を求めよ。",
         "answer": r"$R=6$",
         "explanation": r"正弦定理 $\dfrac{a}{\sin A}=2R$ より "
                        r"$2R=\dfrac{6}{\sin30^\circ}=\dfrac{6}{1/2}=12$。よって $R=6$。",
         "av": 6,
         "chk": lambda av: _eq(6 / sp.sin(sp.rad(30)) / 2, av)},
        {"group": "正弦定理", "level": "standard",
         "stem": r"$\triangle ABC$ で $A=45^\circ$, $B=60^\circ$, $a=\sqrt2$ のとき、"
                 r"$b$ を求めよ。",
         "answer": r"$b=\sqrt3$",
         "explanation": r"正弦定理 $\dfrac{a}{\sin A}=\dfrac{b}{\sin B}$ より "
                        r"$b=\dfrac{a\sin B}{\sin A}"
                        r"=\dfrac{\sqrt2\cdot\frac{\sqrt3}{2}}{\frac{\sqrt2}{2}}=\sqrt3$。",
         "av": sqrt(3),
         "chk": lambda av: _eq(sqrt(2) * sp.sin(sp.rad(60)) / sp.sin(sp.rad(45)), av)},
        {"group": "余弦定理", "level": "basic",
         "stem": r"$\triangle ABC$ で $b=3$, $c=5$, $A=60^\circ$ のとき、$a$ を求めよ。",
         "answer": r"$a=\sqrt{19}$",
         "explanation": r"余弦定理 $a^2=b^2+c^2-2bc\cos A$。"
                        r"$a^2=9+25-2\cdot3\cdot5\cdot\dfrac12=34-15=19$。よって $a=\sqrt{19}$。",
         "av": sqrt(19),
         "chk": lambda av: _eq(sqrt(3 ** 2 + 5 ** 2 - 2 * 3 * 5 * sp.cos(sp.rad(60))), av)},
        {"group": "余弦定理", "level": "standard",
         "stem": r"$\triangle ABC$ で $a=7$, $b=5$, $c=3$ のとき、$\cos A$ を求めよ。",
         "answer": r"$\cos A=-\dfrac{1}{2}$",
         "explanation": r"$\cos A=\dfrac{b^2+c^2-a^2}{2bc}"
                        r"=\dfrac{25+9-49}{2\cdot5\cdot3}=\dfrac{-15}{30}=-\dfrac12$。"
                        r"よって $A=120^\circ$（鈍角）。",
         "av": R(-1, 2),
         "chk": lambda av: _eq(R(5 ** 2 + 3 ** 2 - 7 ** 2, 2 * 5 * 3), av)},
        {"group": "三角形の面積", "level": "basic",
         "stem": r"$\triangle ABC$ で $b=4$, $c=6$, $A=30^\circ$ のとき、面積 $S$ を求めよ。",
         "answer": r"$S=6$",
         "explanation": r"$S=\dfrac12 bc\sin A=\dfrac12\cdot4\cdot6\cdot\dfrac12=6$。",
         "av": 6,
         "chk": lambda av: _eq(R(1, 2) * 4 * 6 * sp.sin(sp.rad(30)), av)},
        {"group": "三角形の面積", "level": "advanced",
         "stem": r"3辺が $a=5$, $b=6$, $c=7$ の三角形の面積を、ヘロンの公式を使って求めよ。",
         "answer": r"$6\sqrt{6}$",
         "explanation": r"$s=\dfrac{5+6+7}{2}=9$。"
                        r"$S=\sqrt{s(s-a)(s-b)(s-c)}=\sqrt{9\cdot4\cdot3\cdot2}"
                        r"=\sqrt{216}=6\sqrt6$。",
         "av": 6 * sqrt(6),
         "chk": lambda av: _eq(sqrt(9 * (9 - 5) * (9 - 6) * (9 - 7)), av)},
    ],
}


U_DATA = {
    "name": "データの分析",
    "tag": "平均・分散・標準偏差・相関係数・箱ひげ図",
    "problems": [
        {"group": "代表値", "level": "basic",
         "stem": r"データ $2,\ 4,\ 4,\ 5,\ 10$ の平均値を求めよ。",
         "answer": r"$5$",
         "explanation": r"合計 $2+4+4+5+10=25$ を個数 $5$ で割る。$25\div5=5$。",
         "av": 5,
         "chk": lambda av: _eq(R(sum([2, 4, 4, 5, 10]), 5), av)},
        {"group": "代表値", "level": "basic",
         "stem": r"データ $2,\ 4,\ 4,\ 5,\ 10$ の中央値と最頻値を求めよ。",
         "answer": r"中央値 $4$、最頻値 $4$",
         "explanation": r"小さい順に並べて真ん中（3番目）が中央値で $4$。"
                        r"最も多く現れる値が最頻値で、$4$ が2回で最多。"
                        r"★平均 $5$ より中央値 $4$ が小さいのは、$10$ という大きい値に"
                        r"平均が引っぱられているため。",
         "av": [4, 4],
         "chk": lambda av: (sorted([2, 4, 4, 5, 10])[2] == av[0]
                            and max(set([2, 4, 4, 5, 10]),
                                    key=[2, 4, 4, 5, 10].count) == av[1])},
        {"group": "分散と標準偏差", "level": "standard",
         "stem": r"データ $2,\ 4,\ 4,\ 5,\ 10$ の分散を求めよ。",
         "answer": r"$\dfrac{36}{5}$",
         "explanation": r"平均は $5$。偏差は $-3,\,-1,\,-1,\,0,\,5$、"
                        r"その2乗は $9,\,1,\,1,\,0,\,25$ で合計 $36$。"
                        r"分散は偏差の2乗の平均なので $\dfrac{36}{5}=7.2$。",
         "av": R(36, 5),
         "chk": lambda av: _eq(R(sum((v - 5) ** 2 for v in [2, 4, 4, 5, 10]), 5), av)},
        {"group": "分散と標準偏差", "level": "standard",
         "stem": r"分散が $9$ であるデータの標準偏差を求めよ。",
         "answer": r"$3$",
         "explanation": r"標準偏差は分散の正の平方根。$\sqrt9=3$。"
                        r"★分散はもとのデータの単位の2乗、標準偏差はもとの単位にもどる。",
         "av": 3, "chk": lambda av: _eq(sqrt(9), av)},
        {"group": "四分位数・箱ひげ図", "level": "standard",
         "stem": r"データ $1,\ 3,\ 5,\ 7,\ 9,\ 11,\ 13$ の四分位範囲を求めよ。",
         "answer": r"$8$",
         "explanation": r"中央値は $7$。中央値より小さい組 $1,\,3,\,5$ の中央値が "
                        r"$Q_1=3$、大きい組 $9,\,11,\,13$ の中央値が $Q_3=11$。"
                        r"四分位範囲は $Q_3-Q_1=11-3=8$。"
                        r"★範囲（最大−最小 $=12$）とちがい、外れ値の影響を受けにくい。",
         "av": 8,
         "chk": lambda av: (sorted([1, 3, 5])[1] == 3 and sorted([9, 11, 13])[1] == 11
                            and 11 - 3 == av)},
        {"group": "相関", "level": "standard",
         "stem": r"2つの変量 $x$, $y$ について、共分散が $-12$、$x$ の標準偏差が $4$、"
                 r"$y$ の標準偏差が $5$ のとき、相関係数を求めよ。",
         "answer": r"$-0.6$（$=-\dfrac{3}{5}$）",
         "explanation": r"相関係数 $r=\dfrac{s_{xy}}{s_x s_y}=\dfrac{-12}{4\times5}=-0.6$。"
                        r"★$r$ は必ず $-1\leq r\leq1$。範囲を外れたら計算ミス。"
                        r"負なので「$x$ が大きいほど $y$ は小さい」傾向。",
         "av": R(-3, 5),
         "chk": lambda av: _eq(R(-12, 4 * 5), av)},
    ],
}

PARTS = [
    {"area": "第1編　数と式・集合と命題",
     "sub": "数学I ／ すべての土台。ここが崩れていると数II以降が積み上がらない",
     "units": [U_TENKAI, U_JISSU, U_SHUGO]},
    {"area": "第2編　二次関数",
     "sub": "数学I ／ 平方完成→頂点→最大最小→不等式、と一本道でつながる",
     "units": [U_NIJI1, U_NIJI2]},
    {"area": "第3編　図形と計量",
     "sub": "数学I ／ 三角比の定義から正弦定理・余弦定理・面積まで",
     "units": [U_SANKAKUHI, U_SEIGEN]},
    {"area": "第4編　データの分析",
     "sub": "数学I ／ 共通テストで必ず出る。計算より「何を意味する数値か」が問われる",
     "units": [U_DATA]},
]
