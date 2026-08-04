# -*- coding: utf-8 -*-
"""複素数平面（数C）／確率分布と統計的な推測（数B）／極限（数III）の基礎徹底問題集。

content_kisoA / kisoI / kisoII と同じ構造・同じ検証方式（av + chk）。

■ ★課程上の位置づけ（作る前に確認した。学年で入れ替わるので毎回確認すること）
  ・複素数平面 …… 数学C「平面上の曲線と複素数平面」。
    2025年度からの共通テスト「数学II・B・C」では、第4〜7問の4題から3題を選ぶ
    【選択問題】として出題される（2025年度は第7問が複素数平面だけの出題だった）。
  ・確率分布と統計的な推測 …… 数学B。旧課程の「確率分布と統計的な推測」が
    「統計的な推測」として拡充され、共通テストでも同じく【選択問題】。
    2025年度本試では仮説検定が出題された。
  ・極限 …… 数学III。**共通テストの出題範囲外**（数IIIは共テに出ない）。
    国公立2次・私大の理系個別試験で必須なので本書に収録する。
    → この事情は各編の扉に明記する（生徒が「共テに出る」と誤解しないため）。
"""
import sympy as sp
from sympy import Rational as R, sqrt, symbols, I, pi, oo, Symbol

x, n = symbols("x n", real=True)
k = Symbol("k", integer=True, positive=True)


def _eq(p, q):
    return sp.simplify(sp.nsimplify(p) - sp.nsimplify(q)) == 0


def _sset(vals):
    return sorted(sp.nsimplify(v) for v in vals)


# ---- 独立検証用ヘルパ（公式を書き直すのではなく、定義から計算する）
def _same(p, q):
    """式として同一か（微分・積分の結果は形が違っても同値でありうる）。"""
    return sp.simplify(sp.expand(p - q)) == 0


def _area_under(f, a, b, npts=200):
    """曲線 f と x 軸で囲まれた面積を、区間を刻んで符号を判定しながら求める。
    ★sympy の integrate(Abs(cos x), ...) は 0 を返すことがある（実測）ので
      Abs に頼らず、符号が一定の小区間に分けて絶対値をとって足す。"""
    a, b = sp.nsimplify(a), sp.nsimplify(b)
    total = sp.Integer(0)
    edges = [a + (b - a) * sp.Rational(i, npts) for i in range(npts + 1)]
    for lo, hi in zip(edges, edges[1:]):
        total += sp.Abs(sp.integrate(f, (x, lo, hi)))
    return sp.simplify(total)


def _same_upto_const(p, q):
    """不定積分の比較。★積分定数の分だけ定数がズレるのは正しい答え。
    差が x を含まない定数なら一致とみなす（微分して確かめるのと同じこと）。"""
    d = sp.simplify(sp.expand(p - q))
    return d.is_number or sp.simplify(sp.diff(d, x)) == 0


def _extremum3(f, kind, dom=None):
    """f の極大値／極小値を、臨界点を解いて2階微分の符号で判定して返す。
    ★答えの x を chk に書き写すと、極大と極小を取り違えても通ってしまう。"""
    d1, d2 = sp.diff(f, x), sp.diff(f, x, 2)
    vals = []
    for cpt in sp.solve(d1, x):
        if not cpt.is_real:
            continue
        if dom and not (dom[0] <= float(cpt) <= dom[1]):
            continue
        sgn = d2.subs(x, cpt)
        if (kind == "max" and sgn < 0) or (kind == "min" and sgn > 0):
            vals.append(sp.nsimplify(sp.simplify(f.subs(x, cpt))))
    return vals[0] if len(vals) == 1 else None


def _inflection(f):
    """変曲点の x 座標。y''=0 かつ前後で符号が変わるものだけを返す。"""
    d2 = sp.diff(f, x, 2)
    out = []
    for cpt in sp.solve(d2, x):
        if not cpt.is_real:
            continue
        a = d2.subs(x, cpt - sp.Rational(1, 100))
        b = d2.subs(x, cpt + sp.Rational(1, 100))
        if a * b < 0:
            out.append(sp.nsimplify(cpt))
    return sorted(out)


def _E(dist, f=lambda v: v):
    """dist=[(値, 確率), ...] から E[f(X)] を定義どおり計算する。"""
    return sum(f(v) * p for v, p in dist)


def _V(dist, f=lambda v: v):
    """V[f(X)] = E[f^2] - (E[f])^2 を定義どおり計算する。"""
    m = _E(dist, f)
    return sp.simplify(_E(dist, lambda v: f(v) ** 2) - m ** 2)


def _binom_E(nn, p):
    """二項分布の期待値を、確率関数の総和から直接計算する（np を使わない）。"""
    return sp.simplify(sum(i * sp.binomial(nn, i) * p ** i * (1 - p) ** (nn - i)
                           for i in range(nn + 1)))


def _binom_V(nn, p):
    e1 = _binom_E(nn, p)
    e2 = sp.simplify(sum(i ** 2 * sp.binomial(nn, i) * p ** i * (1 - p) ** (nn - i)
                         for i in range(nn + 1)))
    return sp.simplify(e2 - e1 ** 2)


def _upper_pct(alpha):
    """標準正規分布の上側 alpha 点を、誤差関数から求める（1.96 等を再計算する）。"""
    return sp.sqrt(2) * sp.erfinv(1 - 2 * sp.Rational(alpha))


# ================================================================ 複素数平面
U_FUKUSO1 = {
    "name": "複素数平面の基本",
    "tag": "絶対値・共役・極形式",
    "problems": [
        {"group": "絶対値と共役", "level": "basic",
         "stem": r"複素数 $z=3+4i$ について、$|z|$ を求めよ。",
         "answer": r"$5$",
         "explanation": r"$|a+bi|=\sqrt{a^2+b^2}$。$\sqrt{9+16}=\sqrt{25}=5$。"
                        r"★複素数平面では $|z|$ は原点からの距離。",
         "av": 5, "chk": lambda av: _eq(abs(3 + 4 * I), av)},
        {"group": "絶対値と共役", "level": "basic",
         "stem": r"$z=2-5i$ の共役複素数 $\bar{z}$ を求めよ。",
         "answer": r"$\bar{z}=2+5i$",
         "explanation": r"共役複素数は虚部の符号を変える。複素数平面では"
                        r"【実軸に関して対称】な点。",
         "av": 2 + 5 * I, "chk": lambda av: _eq(sp.conjugate(2 - 5 * I), av)},
        {"group": "四則", "level": "basic",
         "stem": r"$(2+3i)+(1-5i)$ を計算せよ。",
         "answer": r"$3-2i$",
         "explanation": r"実部どうし・虚部どうしを足す。$(2+1)+(3-5)i=3-2i$。",
         "av": 3 - 2 * I, "chk": lambda av: _eq((2 + 3 * I) + (1 - 5 * I), av)},
        {"group": "四則", "level": "basic",
         "stem": r"$(1+i)^2$ を計算せよ。",
         "answer": r"$2i$",
         "explanation": r"$1+2i+i^2$。$i^2=-1$ なので $1+2i-1=2i$。"
                        r"★$i^2=-1$ の置きかえを忘れないこと。",
         "av": 2 * I, "chk": lambda av: _eq(sp.expand((1 + I) ** 2), av)},
        {"group": "絶対値と共役", "level": "standard",
         "stem": r"$z=1+2i$ のとき、$z\bar{z}$ の値を求めよ。",
         "answer": r"$5$",
         "explanation": r"$z\bar z=|z|^2$。$|z|^2=1^2+2^2=5$。"
                        r"★$z\bar z$ は必ず実数（0以上）になる。実際に展開しても "
                        r"$(1+2i)(1-2i)=1-4i^2=5$。",
         "av": 5,
         "chk": lambda av: _eq(sp.expand((1 + 2 * I) * sp.conjugate(1 + 2 * I)), av)},
        {"group": "極形式", "level": "standard",
         "stem": r"$z=1+\sqrt{3}i$ を極形式 $r(\cos\theta+i\sin\theta)$ で表せ"
                 r"（$0\leq\theta<2\pi$）。",
         "answer": r"$2\left(\cos\dfrac{\pi}{3}+i\sin\dfrac{\pi}{3}\right)$",
         "explanation": r"$r=|z|=\sqrt{1+3}=2$。"
                        r"$\cos\theta=\dfrac12,\ \sin\theta=\dfrac{\sqrt3}{2}$ より "
                        r"$\theta=\dfrac{\pi}{3}$。",
         "av": [2, pi / 3],
         "chk": lambda av: _eq(av[0] * (sp.cos(av[1]) + I * sp.sin(av[1])),
                               1 + sqrt(3) * I)},
        {"group": "極形式", "level": "standard",
         "stem": r"$z=2\left(\cos\dfrac{\pi}{6}+i\sin\dfrac{\pi}{6}\right)$、"
                 r"$w=3\left(\cos\dfrac{\pi}{3}+i\sin\dfrac{\pi}{3}\right)$ のとき、"
                 r"$zw$ の絶対値と偏角を求めよ（偏角は $0\leq\theta<2\pi$）。",
         "answer": r"絶対値 $6$、偏角 $\dfrac{\pi}{2}$",
         "explanation": r"極形式のかけ算は【絶対値はかけ算、偏角は足し算】。"
                        r"$2\times3=6$、$\dfrac{\pi}{6}+\dfrac{\pi}{3}=\dfrac{\pi}{2}$。",
         "av": [6, pi / 2],
         "chk": lambda av: (_eq(abs(2 * sp.exp(I * pi / 6) * 3 * sp.exp(I * pi / 3)), av[0])
                            and _eq(sp.arg(2 * sp.exp(I * pi / 6) * 3 * sp.exp(I * pi / 3)),
                                    av[1]))},
        {"group": "ド・モアブル", "level": "advanced",
         "stem": r"$\left(\cos\dfrac{\pi}{6}+i\sin\dfrac{\pi}{6}\right)^{6}$ の値を求めよ。",
         "answer": r"$-1$",
         "explanation": r"ド・モアブルの定理 $(\cos\theta+i\sin\theta)^n"
                        r"=\cos n\theta+i\sin n\theta$。"
                        r"$n\theta=6\times\dfrac{\pi}{6}=\pi$ なので "
                        r"$\cos\pi+i\sin\pi=-1$。",
         "av": -1,
         "chk": lambda av: _eq(sp.expand((sp.cos(pi / 6) + I * sp.sin(pi / 6)) ** 6), av)},
    ],
}

U_FUKUSO2 = {
    "name": "複素数平面と図形",
    "tag": "点の移動・回転・軌跡",
    "problems": [
        {"group": "回転", "level": "standard",
         "stem": r"点 $z=2+i$ を原点のまわりに $\dfrac{\pi}{2}$ だけ回転した点を表す"
                 r"複素数を求めよ。",
         "answer": r"$-1+2i$",
         "explanation": r"原点のまわりの $\theta$ 回転は "
                        r"$(\cos\theta+i\sin\theta)$ をかける。"
                        r"$\dfrac{\pi}{2}$ 回転は $i$ をかけることと同じ。"
                        r"$i(2+i)=2i+i^2=-1+2i$。",
         "av": -1 + 2 * I,
         "chk": lambda av: _eq(sp.expand(I * (2 + I)), av)},
        {"group": "回転", "level": "advanced",
         "stem": r"点 $\alpha=1+i$ を中心として、点 $z=3+i$ を $\dfrac{\pi}{2}$ だけ"
                 r"回転した点を表す複素数を求めよ。",
         "answer": r"$1+3i$",
         "explanation": r"中心を原点に移す → 回転 → もどす、の3手順。"
                        r"$w=\alpha+i(z-\alpha)$。"
                        r"$z-\alpha=2$、$i\times2=2i$、$\alpha+2i=1+3i$。"
                        r"★中心が原点でないときは【引いて・回して・足す】。",
         "av": 1 + 3 * I,
         "chk": lambda av: _eq(sp.expand((1 + I) + I * ((3 + I) - (1 + I))), av)},
        {"group": "2点間の距離", "level": "basic",
         "stem": r"複素数平面上の2点 $\alpha=1+2i$, $\beta=4+6i$ の間の距離を求めよ。",
         "answer": r"$5$",
         "explanation": r"2点間の距離は $|\beta-\alpha|$。"
                        r"$\beta-\alpha=3+4i$、$|3+4i|=5$。",
         "av": 5, "chk": lambda av: _eq(abs((4 + 6 * I) - (1 + 2 * I)), av)},
        {"group": "軌跡", "level": "standard",
         "stem": r"$|z-2|=3$ を満たす点 $z$ 全体はどのような図形か答えよ。",
         "answer": r"点 $2$ を中心とする半径 $3$ の円",
         "explanation": r"$|z-\alpha|=r$ は「$\alpha$ からの距離が $r$ の点の集まり」"
                        r"＝中心 $\alpha$、半径 $r$ の円。"
                        r"★$|z-\alpha|=|z-\beta|$ なら2点から等距離＝【垂直二等分線】。",
         "chk": None},
    ],
}

# ================================================================ 確率分布・統計的な推測
U_KAKURITSU = {
    "name": "確率変数と確率分布",
    "tag": "期待値・分散・二項分布",
    "problems": [
        {"group": "期待値", "level": "basic",
         "stem": r"1個のさいころを1回投げるとき、出る目 $X$ の期待値 $E(X)$ を求めよ。",
         "answer": r"$\dfrac{7}{2}$",
         "explanation": r"$E(X)=\sum x_i p_i"
                        r"=\dfrac{1+2+3+4+5+6}{6}=\dfrac{21}{6}=\dfrac72$。",
         "av": R(7, 2),
         "chk": lambda av: _eq(R(sum(range(1, 7)), 6), av)},
        {"group": "期待値", "level": "basic",
         "stem": r"当たりが出る確率が $\dfrac{1}{5}$ のくじを1回引くとき、"
                 r"当たれば $100$ 円、はずれれば $0$ 円もらえる。もらえる金額の期待値を求めよ。",
         "answer": r"$20$ 円",
         "explanation": r"$E(X)=100\times\dfrac15+0\times\dfrac45=20$。"
                        r"★期待値は「1回あたり平均していくら」を表す。",
         "av": 20,
         "chk": lambda av: _eq(100 * R(1, 5) + 0 * R(4, 5), av)},
        {"group": "期待値", "level": "standard",
         "stem": r"確率変数 $X$ の期待値が $E(X)=4$ のとき、$E(3X+2)$ を求めよ。",
         "answer": r"$14$",
         "explanation": r"$E(aX+b)=aE(X)+b$。$3\times4+2=14$。"
                        r"★期待値は「そのまま線形に動く」。分散はちがう（下の問）。",
         # ★公式を書き直すだけでは検証にならない。E(X)=4 となる具体分布から直接計算する。
         "av": 14, "chk": lambda av: _eq(_E([(2, R(1, 2)), (6, R(1, 2))], lambda v: 3 * v + 2), av)},
        {"group": "分散", "level": "standard",
         "stem": r"1個のさいころを1回投げるとき、出る目 $X$ の分散 $V(X)$ を求めよ。",
         "answer": r"$\dfrac{35}{12}$",
         "explanation": r"$V(X)=E(X^2)-\{E(X)\}^2$。"
                        r"$E(X^2)=\dfrac{1+4+9+16+25+36}{6}=\dfrac{91}{6}$。"
                        r"$V(X)=\dfrac{91}{6}-\left(\dfrac72\right)^2=\dfrac{35}{12}$。",
         "av": R(35, 12),
         "chk": lambda av: _eq(R(sum(v ** 2 for v in range(1, 7)), 6) - R(7, 2) ** 2, av)},
        {"group": "分散", "level": "standard",
         "stem": r"確率変数 $X$ の分散が $V(X)=5$ のとき、$V(3X+2)$ を求めよ。",
         "answer": r"$45$",
         "explanation": r"$V(aX+b)=a^2V(X)$。定数 $b$ は散らばりに影響しないので消え、"
                        r"$a$ は【2乗】でかかる。$3^2\times5=45$。"
                        r"★ここが期待値との最大のちがい。",
         # ★V(X)=5 となる具体分布(3と7が半々→V=4)…ではなく V=5 になる分布を作って直接計算
         "av": 45,
         "chk": lambda av: _eq(_V([(0, R(1, 2)), (2 * sqrt(5), R(1, 2))],
                                  lambda v: 3 * v + 2), av)},
        {"group": "二項分布", "level": "standard",
         "stem": r"1個のさいころを $180$ 回投げるとき、$1$ の目が出る回数 $X$ の"
                 r"期待値と分散を求めよ。",
         "answer": r"$E(X)=30$、$V(X)=25$",
         "explanation": r"$X$ は二項分布 $B(n,\,p)$、$n=180$, $p=\dfrac16$。"
                        r"$E(X)=np=180\times\dfrac16=30$。"
                        r"$V(X)=np(1-p)=180\times\dfrac16\times\dfrac56=25$。",
         # ★np, np(1-p) を書き直すのでなく、二項分布の確率関数から直接 E と V を出す
         "av": [30, 25],
         "chk": lambda av: (_eq(_binom_E(180, R(1, 6)), av[0])
                            and _eq(_binom_V(180, R(1, 6)), av[1]))},
        {"group": "正規分布", "level": "advanced",
         "stem": r"確率変数 $X$ が正規分布 $N(50,\,10^2)$ に従うとき、"
                 r"$Z=\dfrac{X-50}{10}$ の期待値と標準偏差を求めよ。",
         "answer": r"$E(Z)=0$、標準偏差 $1$",
         "explanation": r"標準化 $Z=\dfrac{X-m}{\sigma}$ をすると、どんな $X$ でも "
                        r"$E(Z)=0$、標準偏差 $1$ になる。"
                        r"さらに $X$ が正規分布に従うときに限り、$Z$ は標準正規分布 "
                        r"$N(0,\,1^2)$ に従う。"
                        r"$E(Z)=\dfrac{E(X)-50}{10}=0$、"
                        r"標準偏差は $\dfrac{10}{10}=1$。",
         "av": [0, 1],
         "chk": lambda av: (_eq(R(50 - 50, 10), av[0]) and _eq(R(10, 10), av[1]))},
    ],
}

U_SUITEI = {
    "name": "統計的な推測",
    "tag": "標本平均・信頼区間・仮説検定",
    "problems": [
        {"group": "母集団と標本", "level": "basic",
         "stem": r"母集団全体を調べる調査を何というか。また、一部を取り出して調べる調査を"
                 r"何というか。",
         "answer": r"全数調査、標本調査",
         "explanation": r"国勢調査のように全部を調べるのが全数調査、"
                        r"視聴率調査のように一部から推測するのが標本調査。"
                        r"標本調査では【無作為に】取り出すことが前提になる。",
         "chk": None},
        {"group": "標本平均", "level": "standard",
         "stem": r"母平均 $m=60$、母標準偏差 $\sigma=12$ の母集団から大きさ $36$ の"
                 r"標本を無作為に取り出すとき、標本平均 $\bar{X}$ の期待値と標準偏差を求めよ。",
         "answer": r"$E(\bar{X})=60$、標準偏差 $2$",
         "explanation": r"$E(\bar X)=m=60$（母平均と同じ）。"
                        r"標準偏差は $\dfrac{\sigma}{\sqrt n}=\dfrac{12}{\sqrt{36}}"
                        r"=\dfrac{12}{6}=2$。"
                        r"★標本を大きくすると標準偏差は $\sqrt n$ に反比例して小さくなる"
                        r"＝推定が正確になる。",
         "av": [60, 2],
         "chk": lambda av: (_eq(60, av[0]) and _eq(12 / sqrt(36), av[1]))},
        {"group": "信頼区間", "level": "advanced",
         "stem": r"母標準偏差 $\sigma=10$ の母集団から大きさ $100$ の標本を取り出したところ、"
                 r"標本平均が $50$ であった。母平均 $m$ に対する信頼度 $95\%$ の信頼区間を"
                 r"求めよ（$1.96$ を用いよ）。",
         "answer": r"$48.04 \leq m \leq 51.96$",
         "explanation": r"信頼区間は $\bar X \pm 1.96\dfrac{\sigma}{\sqrt n}$。"
                        r"$\dfrac{10}{\sqrt{100}}=1$ なので $50\pm1.96$。"
                        r"よって $48.04\leq m\leq51.96$。"
                        r"★信頼度を上げる（99%）と区間は【広く】なる。",
         # ★答えを小数で印字するなら av も小数にする（分数のままだと照合できない）
         "av": [sp.Float("48.04"), sp.Float("51.96")],
         "chk": lambda av: (_eq(50 - sp.Float("1.96") * 10 / sqrt(100), av[0])
                            and _eq(50 + sp.Float("1.96") * 10 / sqrt(100), av[1]))},
        {"group": "仮説検定", "level": "standard",
         "stem": r"仮説検定で、主張したいことの否定として立てる仮説を何というか。"
                 r"また、それに対して主張したい側の仮説を何というか。",
         "answer": r"帰無仮説、対立仮説",
         "explanation": r"「差がない・効果がない」という否定側が帰無仮説 $H_0$、"
                        r"主張したい側が対立仮説 $H_1$。"
                        r"$H_0$ を仮定したときに観測結果が起こる確率が有意水準より小さければ "
                        r"$H_0$ を棄却する（＝$H_1$ を採用）。",
         "chk": None},
        {"group": "仮説検定", "level": "advanced",
         "stem": r"有意水準 $5\%$ の両側検定を行う。標準正規分布で上側 $2.5\%$ 点が "
                 r"$1.96$ であることを用いて、棄却域を $Z$ の不等式で表せ。",
         "answer": r"$|Z| \geq 1.96$（$Z\leq-1.96$ または $Z\geq1.96$）",
         "explanation": r"両側検定なので $5\%$ を左右に $2.5\%$ ずつ分ける。"
                        r"標準正規分布で上側 $2.5\%$ 点が $1.96$。"
                        r"よって $Z\leq-1.96$ または $Z\geq1.96$ が棄却域。"
                        r"★片側検定なら $5\%$ を片方に寄せるので境界は $1.64$ になる。",
         # ★av を av と比べる恒真chkだった。標準正規分布から上側2.5%点を
         #   実際に求めて照合する（公式を書き写すのではなく再計算する）。
         "av": sp.Float("1.96"),
         "chk": lambda av: abs(float(_upper_pct(sp.Rational(25, 1000)) - av)) < 5e-4},
    ],
}

# ================================================================ 極限（数III）
U_KYOKUGEN = {
    "name": "数列の極限",
    "tag": "収束・発散・無限等比数列",
    "problems": [
        {"group": "数列の極限", "level": "basic",
         "stem": r"$\displaystyle\lim_{n\to\infty}\dfrac{1}{n}$ を求めよ。",
         "answer": r"$0$",
         "explanation": r"分母が限りなく大きくなるので、全体は $0$ に近づく。"
                        r"$\dfrac{1}{n}\to0$ は極限のいちばん基本。",
         "av": 0, "chk": lambda av: _eq(sp.limit(1 / n, n, oo), av)},
        {"group": "数列の極限", "level": "basic",
         "stem": r"$\displaystyle\lim_{n\to\infty}\left(2+\dfrac{3}{n}\right)$ を求めよ。",
         "answer": r"$2$",
         "explanation": r"$\dfrac3n\to0$ なので全体は $2$ に近づく。",
         "av": 2, "chk": lambda av: _eq(sp.limit(2 + 3 / n, n, oo), av)},
        {"group": "数列の極限", "level": "standard",
         "stem": r"$\displaystyle\lim_{n\to\infty}\dfrac{3n^2-n}{2n^2+5}$ を求めよ。",
         "answer": r"$\dfrac{3}{2}$",
         "explanation": r"分母の最高次 $n^2$ で分子・分母を割る。"
                        r"$\dfrac{3-\frac1n}{2+\frac{5}{n^2}}\to\dfrac{3}{2}$。"
                        r"★$\dfrac{\infty}{\infty}$ の形は【最高次で割る】が定石。",
         "av": R(3, 2),
         "chk": lambda av: _eq(sp.limit((3 * n ** 2 - n) / (2 * n ** 2 + 5), n, oo), av)},
        {"group": "無限等比数列", "level": "standard",
         "stem": r"$\displaystyle\lim_{n\to\infty}\left(\dfrac{2}{3}\right)^n$ を求めよ。",
         "answer": r"$0$",
         "explanation": r"$|r|<1$ のとき $r^n\to0$。$\left|\dfrac23\right|<1$ なので $0$。"
                        r"★$r^n$ の極限は $|r|<1$ で $0$、$r=1$ で $1$、"
                        r"それ以外（$r>1$ や $r\leq-1$）は発散。",
         "av": 0, "chk": lambda av: _eq(sp.limit(R(2, 3) ** n, n, oo), av)},
        {"group": "無限級数", "level": "advanced",
         "stem": r"無限等比級数 $1+\dfrac{1}{2}+\dfrac{1}{4}+\dfrac{1}{8}+\cdots$ の和を"
                 r"求めよ。",
         "answer": r"$2$",
         "explanation": r"初項 $a=1$、公比 $r=\dfrac12$。$|r|<1$ なので収束し、"
                        r"和は $\dfrac{a}{1-r}=\dfrac{1}{1-\frac12}=2$。"
                        r"★$|r|\geq1$ なら発散して和は存在しない。収束条件の確認が先。",
         "av": 2,
         "chk": lambda av: _eq(sp.summation(R(1, 2) ** k, (k, 0, oo)), av)},
    ],
}

U_KANSU_KYOKUGEN = {
    "name": "関数の極限と連続性",
    "tag": "不定形の処理・連続・微分係数",
    "problems": [
        {"group": "関数の極限", "level": "basic",
         "stem": r"$\displaystyle\lim_{x\to2}(x^2+3x)$ を求めよ。",
         "answer": r"$10$",
         "explanation": r"多項式は連続なので、そのまま $x=2$ を代入して "
                        r"$4+6=10$。",
         "av": 10, "chk": lambda av: _eq(sp.limit(x ** 2 + 3 * x, x, 2), av)},
        {"group": "関数の極限", "level": "basic",
         "stem": r"$\displaystyle\lim_{x\to3}\dfrac{x+1}{x-1}$ を求めよ。",
         "answer": r"$2$",
         "explanation": r"分母が $0$ にならないので、そのまま代入して "
                        r"$\dfrac{4}{2}=2$。",
         "av": 2,
         "chk": lambda av: _eq(sp.limit((x + 1) / (x - 1), x, 3), av)},
        {"group": "不定形", "level": "standard",
         "stem": r"$\displaystyle\lim_{x\to1}\dfrac{x^2-1}{x-1}$ を求めよ。",
         "answer": r"$2$",
         "explanation": r"そのまま代入すると $\dfrac00$ の不定形。"
                        r"分子を因数分解して $\dfrac{(x+1)(x-1)}{x-1}=x+1$。"
                        r"$x\to1$ で $2$。"
                        r"★$\dfrac00$ が出たら【約分できる形にする】。",
         "av": 2,
         "chk": lambda av: _eq(sp.limit((x ** 2 - 1) / (x - 1), x, 1), av)},
        {"group": "不定形", "level": "advanced",
         "stem": r"$\displaystyle\lim_{x\to0}\dfrac{\sin x}{x}$ を求めよ。",
         "answer": r"$1$",
         "explanation": r"三角関数の極限の基本公式。$\dfrac00$ の不定形だが、"
                        r"$x$ が【弧度法】のとき $1$ に収束する。"
                        r"★度数法では成り立たない。極限・微分では必ず弧度法を使う理由がこれ。",
         "av": 1,
         "chk": lambda av: _eq(sp.limit(sp.sin(x) / x, x, 0), av)},
        {"group": "微分係数と極限", "level": "standard",
         "stem": r"$f(x)=x^3$ のとき、$\displaystyle\lim_{h\to0}\dfrac{f(1+h)-f(1)}{h}$ を"
                 r"求めよ。",
         "answer": r"$3$",
         "explanation": r"これは微分係数 $f'(1)$ の定義そのもの。"
                        r"$f'(x)=3x^2$ より $f'(1)=3$。"
                        r"★極限の式を見たら「微分係数の定義ではないか」を疑う。",
         "av": 3,
         "chk": lambda av: _eq(sp.limit(((1 + Symbol("h")) ** 3 - 1) / Symbol("h"),
                                        Symbol("h"), 0), av)},
    ],
}


# ================================================================ 微分法（数III）
U_BIBUN3 = {
    "name": "微分の計算（数III）",
    "tag": "積・商・合成関数／三角・指数・対数の微分",
    "problems": [
        {"group": "基本の導関数", "level": "basic",
         "stem": r"$y=\sin x$ を微分せよ。",
         "answer": r"$y'=\cos x$",
         "explanation": r"$(\sin x)'=\cos x$。$(\cos x)'=-\sin x$（符号に注意）、"
                        r"$(\tan x)'=\dfrac{1}{\cos^2 x}$ もセットで覚える。",
         "av": sp.cos(x), "chk": lambda av: _same(sp.diff(sp.sin(x), x), av)},
        {"group": "基本の導関数", "level": "basic",
         "stem": r"$y=e^{x}$ と $y=\log x$（$x>0$）をそれぞれ微分せよ。",
         "answer": r"$(e^x)'=e^x$、$(\log x)'=\dfrac{1}{x}$",
         "explanation": r"$e^x$ は微分しても変わらない唯一の関数。"
                        r"$\log x$（自然対数）の微分は $\dfrac1x$。"
                        r"★数IIIの $\log$ は底が $e$ の自然対数。底を省略して書く。",
         "av": [sp.exp(x), 1 / x],
         "chk": lambda av: (_same(sp.diff(sp.exp(x), x), av[0])
                            and _same(sp.diff(sp.log(x), x), av[1]))},
        {"group": "基本の導関数", "level": "basic",
         "stem": r"$y=\cos x$ を微分せよ。",
         "answer": r"$y'=-\sin x$",
         "explanation": r"$(\cos x)'=-\sin x$。★$\sin$ の微分と違って【マイナスが付く】。"
                        r"ここの符号落としが最頻出のミス。",
         "av": -sp.sin(x), "chk": lambda av: _same(sp.diff(sp.cos(x), x), av)},
        {"group": "基本の導関数", "level": "basic",
         "stem": r"$y=x^{3}+2x$ を微分せよ。",
         "answer": r"$y'=3x^{2}+2$",
         "explanation": r"$(x^n)'=nx^{n-1}$。数IIまでと同じ計算。"
                        r"数IIIではここに三角・指数・対数が加わるだけ。",
         "av": 3 * x ** 2 + 2,
         "chk": lambda av: _same(sp.diff(x ** 3 + 2 * x, x), av)},
        {"group": "積の微分", "level": "standard",
         "stem": r"$y=x^2 e^{x}$ を微分せよ。",
         "answer": r"$y'=(x^2+2x)e^{x}$",
         "explanation": r"積の微分 $(fg)'=f'g+fg'$。"
                        r"$f=x^2,\ g=e^x$ として $2xe^x+x^2e^x=(x^2+2x)e^x$。",
         "av": (x ** 2 + 2 * x) * sp.exp(x),
         "chk": lambda av: _same(sp.diff(x ** 2 * sp.exp(x), x), av)},
        {"group": "商の微分", "level": "standard",
         "stem": r"$y=\dfrac{x}{x+1}$ を微分せよ。",
         "answer": r"$y'=\dfrac{1}{(x+1)^2}$",
         "explanation": r"商の微分 $\left(\dfrac fg\right)'=\dfrac{f'g-fg'}{g^2}$。"
                        r"$\dfrac{1\cdot(x+1)-x\cdot1}{(x+1)^2}=\dfrac{1}{(x+1)^2}$。"
                        r"★分子は【引き算】。順序を逆にすると符号が変わる。",
         "av": 1 / (x + 1) ** 2,
         "chk": lambda av: _same(sp.diff(x / (x + 1), x), av)},
        {"group": "合成関数の微分", "level": "standard",
         "stem": r"$y=(2x+1)^{5}$ を微分せよ。",
         "answer": r"$y'=10(2x+1)^{4}$",
         "explanation": r"合成関数の微分（連鎖律）は「外側を微分 × 内側を微分」。"
                        r"$5(2x+1)^4 \times 2=10(2x+1)^4$。",
         "av": 10 * (2 * x + 1) ** 4,
         "chk": lambda av: _same(sp.diff((2 * x + 1) ** 5, x), av)},
        {"group": "合成関数の微分", "level": "standard",
         "stem": r"$y=e^{3x}$ を微分せよ。",
         "answer": r"$y'=3e^{3x}$",
         "explanation": r"外側 $e^{\square}$ の微分は $e^{\square}$、内側 $3x$ の微分は $3$。"
                        r"かけて $3e^{3x}$。",
         "av": 3 * sp.exp(3 * x),
         "chk": lambda av: _same(sp.diff(sp.exp(3 * x), x), av)},
        {"group": "合成関数の微分", "level": "advanced",
         "stem": r"$y=\log(x^2+1)$ を微分せよ。",
         "answer": r"$y'=\dfrac{2x}{x^2+1}$",
         "explanation": r"$(\log u)'=\dfrac{u'}{u}$。$u=x^2+1$、$u'=2x$ より "
                        r"$\dfrac{2x}{x^2+1}$。"
                        r"★$\dfrac{u'}{u}$ の形は「対数微分」として頻出。",
         "av": 2 * x / (x ** 2 + 1),
         "chk": lambda av: _same(sp.diff(sp.log(x ** 2 + 1), x), av)},
        {"group": "合成関数の微分", "level": "advanced",
         "stem": r"$y=\sin^{2}x$ を微分せよ。",
         "answer": r"$y'=2\sin x\cos x$（$=\sin 2x$）",
         "explanation": r"$(\sin x)^2$ とみて、外側 $\square^2$ の微分 $2\square$ に"
                        r"内側 $\sin x$ の微分 $\cos x$ をかける。"
                        r"$2\sin x\cos x$。2倍角より $\sin2x$ とも書ける。",
         "av": 2 * sp.sin(x) * sp.cos(x),
         "chk": lambda av: _same(sp.diff(sp.sin(x) ** 2, x), av)},
    ],
}

U_BIBUN3_APP = {
    "name": "微分の応用（数III）",
    "tag": "接線・増減と凹凸・最大最小",
    "problems": [
        {"group": "微分係数", "level": "basic",
         "stem": r"$f(x)=e^{x}$ のとき、$f'(0)$ の値を求めよ。",
         "answer": r"$1$",
         "explanation": r"$f'(x)=e^x$ なので $f'(0)=e^0=1$。"
                        r"★$y=e^x$ は原点近くで傾き $1$。これが $e$ を底に選ぶ理由。",
         "av": 1,
         "chk": lambda av: _eq(sp.diff(sp.exp(x), x).subs(x, 0), av)},
        {"group": "接線", "level": "standard",
         "stem": r"曲線 $y=e^{x}$ 上の点 $(0,\,1)$ における接線の方程式を求めよ。",
         "answer": r"$y=x+1$",
         "explanation": r"$y'=e^x$ より $x=0$ での傾きは $e^0=1$。"
                        r"$y-1=1\cdot(x-0)$ すなわち $y=x+1$。",
         "av": x + 1,
         "chk": lambda av: _same(sp.diff(sp.exp(x), x).subs(x, 0) * (x - 0) + 1, av)},
        {"group": "接線", "level": "advanced",
         "stem": r"曲線 $y=\log x$ 上の点 $(1,\,0)$ における接線の方程式を求めよ。",
         "answer": r"$y=x-1$",
         "explanation": r"$y'=\dfrac1x$ より $x=1$ での傾きは $1$。"
                        r"$y-0=1\cdot(x-1)$ すなわち $y=x-1$。",
         "av": x - 1,
         "chk": lambda av: _same(sp.diff(sp.log(x), x).subs(x, 1) * (x - 1) + 0, av)},
        {"group": "増減と極値", "level": "standard",
         "stem": r"$f(x)=xe^{-x}$ の極大値を求めよ。",
         "answer": r"極大値 $\dfrac{1}{e}$（$x=1$ のとき）",
         "explanation": r"$f'(x)=e^{-x}-xe^{-x}=(1-x)e^{-x}$。"
                        r"$e^{-x}>0$ なので符号は $1-x$ で決まり、$x<1$ で正、$x>1$ で負。"
                        r"よって $x=1$ で極大、$f(1)=\dfrac1e$。",
         "av": sp.exp(-1),
         "chk": lambda av: _extremum3(x * sp.exp(-x), "max") == sp.nsimplify(av)},
        {"group": "増減と極値", "level": "advanced",
         "stem": r"$f(x)=x-\log x$（$x>0$）の極小値を求めよ。",
         "answer": r"極小値 $1$（$x=1$ のとき）",
         "explanation": r"$f'(x)=1-\dfrac1x=\dfrac{x-1}{x}$。"
                        r"$x>0$ では分母は正なので符号は $x-1$ で決まる。"
                        r"$x<1$ で負、$x>1$ で正なので $x=1$ で極小、$f(1)=1-0=1$。",
         "av": 1,
         "chk": lambda av: _extremum3(x - sp.log(x), "min", dom=(0.01, 20))
                           == sp.nsimplify(av)},
        {"group": "最大最小", "level": "advanced",
         "stem": r"$0\leq x\leq 2\pi$ における $f(x)=x+2\cos x$ の最大値を求めよ。",
         "answer": r"最大値 $2\pi+2$（$x=2\pi$ のとき）",
         "explanation": r"★極大値と最大値は別物。閉区間では【極値と両端】を比べる。"
                        r"極大は $x=\dfrac{\pi}{6}$ で $\dfrac{\pi}{6}+\sqrt3\fallingdotseq2.3$、"
                        r"極小は $x=\dfrac56\pi$。"
                        r"端は $f(0)=2$、$f(2\pi)=2\pi+2\fallingdotseq8.3$。"
                        r"いちばん大きいのは $x=2\pi$ のときで $2\pi+2$。",
         "av": 2 * pi + 2,
         "chk": lambda av: _eq(sp.maximum(x + 2 * sp.cos(x), x, sp.Interval(0, 2 * pi)), av)},
        {"group": "凹凸と変曲点", "level": "advanced",
         "stem": r"曲線 $y=x^3-3x^2$ の変曲点の $x$ 座標を求めよ。",
         "answer": r"$x=1$",
         "explanation": r"$y''=6x-6$。$y''=0$ となるのは $x=1$ で、"
                        r"その前後で $y''$ の符号が負から正に【変わる】ので変曲点。"
                        r"★$y''=0$ だけでは変曲点と言えない。符号が変わることが条件。",
         "av": 1,
         "chk": lambda av: _inflection(x ** 3 - 3 * x ** 2) == [sp.nsimplify(av)]},
        {"group": "増減と極値", "level": "advanced",
         "stem": r"$0\leq x\leq 2\pi$ における $f(x)=x+2\cos x$ の極大値を求めよ。",
         "answer": r"極大値 $\dfrac{\pi}{6}+\sqrt{3}$（$x=\dfrac{\pi}{6}$ のとき）",
         "explanation": r"$f'(x)=1-2\sin x$。$f'=0$ より $\sin x=\dfrac12$、"
                        r"$x=\dfrac{\pi}{6},\ \dfrac{5}{6}\pi$。"
                        r"$f'$ は $x<\dfrac{\pi}{6}$ で正、$\dfrac{\pi}{6}<x<\dfrac56\pi$ で負"
                        r"なので $x=\dfrac{\pi}{6}$ で極大。"
                        r"$f\left(\dfrac{\pi}{6}\right)=\dfrac{\pi}{6}+2\cos\dfrac{\pi}{6}"
                        r"=\dfrac{\pi}{6}+\sqrt3$。",
         "av": pi / 6 + sqrt(3),
         # ★sympy の比較は Boolean オブジェクトを返すので bool() で包む
         #   （包まないとゲートの「True を返すか」判定に落ちる）
         "chk": lambda av: bool(
             _eq((x + 2 * sp.cos(x)).subs(x, pi / 6), av)
             and _eq(sp.diff(x + 2 * sp.cos(x), x).subs(x, pi / 6), 0)
             and sp.diff(x + 2 * sp.cos(x), x, 2).subs(x, pi / 6) < 0)},
    ],
}

# ================================================================ 積分法（数III）
U_SEKIBUN3 = {
    "name": "積分の計算（数III）",
    "tag": "基本の不定積分・置換積分・部分積分",
    "problems": [
        {"group": "基本の不定積分", "level": "basic",
         "stem": r"$\displaystyle\int \cos x\,dx$ を求めよ（$C$ は積分定数）。",
         "answer": r"$\sin x+C$",
         "explanation": r"微分の逆。$(\sin x)'=\cos x$ なので "
                        r"$\displaystyle\int\cos x\,dx=\sin x+C$。",
         "av": sp.sin(x),
         "chk": lambda av: _same_upto_const(sp.integrate(sp.cos(x), x), av)},
        {"group": "基本の不定積分", "level": "basic",
         "stem": r"$\displaystyle\int \dfrac{1}{x}\,dx$ を求めよ（$x>0$、$C$ は積分定数）。",
         "answer": r"$\log x+C$",
         "explanation": r"$(\log x)'=\dfrac1x$ の逆。"
                        r"★$x<0$ も含めるときは $\log|x|+C$ と絶対値をつける。",
         "av": sp.log(x),
         "chk": lambda av: _same_upto_const(sp.integrate(1 / x, x), av)},
        {"group": "基本の不定積分", "level": "basic",
         "stem": r"$\displaystyle\int e^{x}\,dx$ を求めよ（$C$ は積分定数）。",
         "answer": r"$e^{x}+C$",
         "explanation": r"$(e^x)'=e^x$ の逆。微分しても積分しても変わらない。",
         "av": sp.exp(x),
         "chk": lambda av: _same_upto_const(sp.integrate(sp.exp(x), x), av)},
        {"group": "基本の不定積分", "level": "basic",
         "stem": r"$\displaystyle\int \sin x\,dx$ を求めよ（$C$ は積分定数）。",
         "answer": r"$-\cos x+C$",
         "explanation": r"$(-\cos x)'=\sin x$。★積分でも符号に注意。"
                        r"$\displaystyle\int\cos x\,dx=\sin x+C$ とは符号が逆になる。",
         "av": -sp.cos(x),
         "chk": lambda av: _same_upto_const(sp.integrate(sp.sin(x), x), av)},
        {"group": "置換積分", "level": "standard",
         "stem": r"$\displaystyle\int (2x+1)^{4}\,dx$ を求めよ（$C$ は積分定数）。",
         "answer": r"$\dfrac{(2x+1)^{5}}{10}+C$",
         "explanation": r"$u=2x+1$ と置くと $du=2\,dx$、つまり $dx=\dfrac{du}{2}$。"
                        r"$\displaystyle\int u^4\dfrac{du}{2}=\dfrac{u^5}{10}$。"
                        r"もどして $\dfrac{(2x+1)^5}{10}$。",
         "av": (2 * x + 1) ** 5 / 10,
         "chk": lambda av: _same_upto_const(sp.integrate((2 * x + 1) ** 4, x), av)},
        {"group": "置換積分", "level": "advanced",
         "stem": r"$\displaystyle\int \dfrac{2x}{x^2+1}\,dx$ を求めよ（$C$ は積分定数）。",
         "answer": r"$\log(x^2+1)+C$",
         "explanation": r"分子が分母の微分になっている（$\dfrac{u'}{u}$ の形）。"
                        r"このとき積分は $\log|u|+C$。"
                        r"$x^2+1>0$ なので絶対値は不要で $\log(x^2+1)+C$。",
         "av": sp.log(x ** 2 + 1),
         "chk": lambda av: _same_upto_const(sp.integrate(2 * x / (x ** 2 + 1), x), av)},
        {"group": "部分積分", "level": "advanced",
         "stem": r"$\displaystyle\int x e^{x}\,dx$ を求めよ（$C$ は積分定数）。",
         "answer": r"$(x-1)e^{x}+C$",
         "explanation": r"部分積分 $\displaystyle\int fg'=fg-\int f'g$。"
                        r"$f=x,\ g'=e^x$ とすると "
                        r"$xe^x-\displaystyle\int e^x dx=xe^x-e^x=(x-1)e^x$。"
                        r"★多項式は【微分する側】に置くと次数が下がって終わる。",
         "av": (x - 1) * sp.exp(x),
         "chk": lambda av: _same_upto_const(sp.integrate(x * sp.exp(x), x), av)},
        {"group": "部分積分", "level": "advanced",
         "stem": r"$\displaystyle\int \log x\,dx$ を求めよ（$x>0$、$C$ は積分定数）。",
         "answer": r"$x\log x-x+C$",
         "explanation": r"$\log x=1\times\log x$ とみて、$f=\log x,\ g'=1$ で部分積分。"
                        r"$x\log x-\displaystyle\int \dfrac1x\cdot x\,dx=x\log x-x$。"
                        r"★$\log$ 単独の積分はこの手が定石。",
         "av": x * sp.log(x) - x,
         "chk": lambda av: _same_upto_const(sp.integrate(sp.log(x), x), av)},
    ],
}

U_SEKIBUN3_APP = {
    "name": "定積分の応用（数III）",
    "tag": "定積分・面積・回転体の体積",
    "problems": [
        {"group": "定積分", "level": "basic",
         "stem": r"$\displaystyle\int_0^{\pi} \sin x\,dx$ を求めよ。",
         "answer": r"$2$",
         "explanation": r"$\left[-\cos x\right]_0^{\pi}=-\cos\pi-(-\cos0)=1+1=2$。",
         "av": 2,
         "chk": lambda av: _eq(sp.integrate(sp.sin(x), (x, 0, pi)), av)},
        {"group": "定積分", "level": "basic",
         "stem": r"$\displaystyle\int_0^{\frac{\pi}{2}} \cos x\,dx$ を求めよ。",
         "answer": r"$1$",
         "explanation": r"$\left[\sin x\right]_0^{\frac{\pi}{2}}"
                        r"=\sin\dfrac{\pi}{2}-\sin0=1-0=1$。",
         "av": 1,
         "chk": lambda av: _eq(sp.integrate(sp.cos(x), (x, 0, pi / 2)), av)},
        {"group": "定積分", "level": "standard",
         "stem": r"$\displaystyle\int_0^{1} e^{x}\,dx$ を求めよ。",
         "answer": r"$e-1$",
         "explanation": r"$\left[e^x\right]_0^1=e^1-e^0=e-1$。",
         "av": sp.E - 1,
         "chk": lambda av: _eq(sp.integrate(sp.exp(x), (x, 0, 1)), av)},
        {"group": "面積", "level": "standard",
         "stem": r"曲線 $y=\cos x$（$-\dfrac{\pi}{2}\leq x\leq\dfrac{\pi}{2}$）と "
                 r"$x$ 軸で囲まれた部分の面積を求めよ。",
         "answer": r"$2$",
         "explanation": r"この区間で $\cos x\geq0$ なので、面積はそのまま "
                        r"$\displaystyle\int_{-\frac{\pi}{2}}^{\frac{\pi}{2}}\cos x\,dx"
                        r"=\left[\sin x\right]_{-\frac{\pi}{2}}^{\frac{\pi}{2}}=1-(-1)=2$。"
                        r"★偶関数なので $2\displaystyle\int_0^{\frac{\pi}{2}}\cos x\,dx$ でもよい。",
         "av": 2,
         "chk": lambda av: _eq(_area_under(sp.cos(x), -pi / 2, pi / 2), av)},
        {"group": "面積", "level": "advanced",
         "stem": r"曲線 $y=\log x$、$x$ 軸、直線 $x=e$ で囲まれた部分の面積を求めよ。",
         "answer": r"$1$",
         "explanation": r"$\log x=0$ となるのは $x=1$。区間 $1\leq x\leq e$ で "
                        r"$\log x\geq0$ なので、"
                        r"$\displaystyle\int_1^{e}\log x\,dx"
                        r"=\left[x\log x-x\right]_1^{e}=(e-e)-(0-1)=1$。",
         "av": 1,
         "chk": lambda av: _eq(sp.integrate(sp.log(x), (x, 1, sp.E)), av)},
        {"group": "回転体の体積", "level": "advanced",
         "stem": r"曲線 $y=\sqrt{x}$、$x$ 軸、直線 $x=4$ で囲まれた部分を $x$ 軸のまわりに"
                 r"1回転してできる立体の体積を求めよ。",
         "answer": r"$8\pi$",
         "explanation": r"$V=\pi\displaystyle\int_a^b y^2\,dx"
                        r"=\pi\displaystyle\int_0^4 x\,dx"
                        r"=\pi\left[\dfrac{x^2}{2}\right]_0^4=8\pi$。"
                        r"★$y$ ではなく【$y^2$】を積分する。2乗を忘れるミスが最多。",
         "av": 8 * pi,
         "chk": lambda av: _eq(pi * sp.integrate((sqrt(x)) ** 2, (x, 0, 4)), av)},
        {"group": "回転体の体積", "level": "advanced",
         "stem": r"曲線 $y=\sin x$（$0\leq x\leq\pi$）と $x$ 軸で囲まれた部分を "
                 r"$x$ 軸のまわりに1回転してできる立体の体積を求めよ。",
         "answer": r"$\dfrac{\pi^2}{2}$",
         "explanation": r"$V=\pi\displaystyle\int_0^{\pi}\sin^2x\,dx$。"
                        r"半角の公式 $\sin^2x=\dfrac{1-\cos2x}{2}$ を使うと "
                        r"$\pi\cdot\dfrac{\pi}{2}=\dfrac{\pi^2}{2}$。"
                        r"★$\sin^2$ や $\cos^2$ の積分は【半角で次数を下げる】。",
         "av": pi ** 2 / 2,
         "chk": lambda av: _eq(pi * sp.integrate(sp.sin(x) ** 2, (x, 0, pi)), av)},
    ],
}

PARTS = [
    {"area": "第1編　複素数平面",
     "sub": "数学C ／ 共通テスト数学II・B・Cでは第4〜7問の選択問題として出題される",
     "units": [U_FUKUSO1, U_FUKUSO2]},
    {"area": "第2編　確率分布と統計的な推測",
     "sub": "数学B ／ 共通テスト数学II・B・Cでは選択問題。2025年度は仮説検定が出た",
     "units": [U_KAKURITSU, U_SUITEI]},
    {"area": "第3編　極限",
     "sub": "数学III ／ 共通テストの出題範囲外だが、国公立2次・私大の理系個別試験では必須",
     "units": [U_KYOKUGEN, U_KANSU_KYOKUGEN]},
    {"area": "第4編　微分法",
     "sub": "数学III ／ 積・商・合成関数の微分ができれば、あとは増減表を書くだけ",
     "units": [U_BIBUN3, U_BIBUN3_APP]},
    {"area": "第5編　積分法",
     "sub": "数学III ／ 置換積分と部分積分の2本柱。面積・体積はその応用",
     "units": [U_SEKIBUN3, U_SEKIBUN3_APP]},
]
