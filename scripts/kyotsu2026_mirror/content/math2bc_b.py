# -*- coding: utf-8 -*-
"""math2bc_b.py: 2026共通テスト 数学ⅡBC そっくり類似問題 — 第3問(必答, 配点22)・第4問(選択, 配点16)

第3問 微分積分:  f(x) = (5/3)x^3 - 10x^2 + 15x + k  (k は実数)
  f'(x) = 5x^2 - 20x + 15 = 5(x-1)(x-3)            … ア=②
  x=1 で極大 f = 20/3 + k                            … イ=1, ウ=⑨(20/3+k)
  x=3 で極小 f = k                                    … エ=3, オ=⑤(k)
  (ii) k=0 → 極小が x軸に接する正係数図(②)         … カ=②
       k>0 → 両極値とも x軸より上の正係数図(⓪)      … キ=⓪
  (iii) f(0)=k<0<f(1)=20/3+k → -20/3<k<0            … ク=⑦(-20/3), ケ=⓪(0)
        面積等分 ⇔ ∫_0^1 f dx = 0                     … コ=①
        → k = -55/12                                  … サシス=-55, セソ=12
  (2) g(x) 3次: 条件(a)(b)(c) で 8図を 3→2→1 に絞る
       (a) g(0)=0 ∧ g'(0)>0     → {①,②,④}           … タチツ(順不同)
       (b) g' の軸が x=0 (原点対称) → {①,④}          … テト(順不同)
       (c) g' が下に凸 (正係数)  → {④}                … ナ=④

第4問 数列 (階差数列):
  (1) b_n = 6n-3, a_1 = 4
      b_1=3, a_2=7, b_2=9, a_3=16                     … ア=3,イ=7,ウ=9,エオ=16
      a_n = a_1 + Σ_{k=1}^{n-1} b_k = 3n^2 - 6n + 7    … カ=⓪(n-1), キ=3,ク=6,ケ=7
  (2) 太郎: d_n=(3n-1)·2^n を c_n=(pn+q)·2^n で解く
      c_{n+1}-c_n = {p·n + (2p+q)}·2^n                … コ=⓪(p), サ=⑤(2p+q)
      p=3, q=-7                                        … シ=3, スセ=-7
      Σ_{k=1}^n d_k = (3n-4)·2^{n+1} + 8              … ソ=①(3n-4), タ=8
  (3) 花子: d_n=(n^2-2n-2)·2^n を c_n=(n^2-6n+8)·2^n で解く
      Σ_{k=1}^n d_k = (n^2-4n+3)·2^{n+1} - 6          … チ=④(n^2-4n+3), ツ=6

検証: content/verify_math2bc_b.py (sympy 独立導出 + 8図/6図の条件整合テスト + 数列和の全数照合)
"""

# =====================================================================
#  Q3 (ii): 3次関数グラフ概形 6図 の系統生成
#  すべて座標軸+O のみ, 目盛りなし. 正/負係数 × {極小接地(k=0型) / 両極値上方(k>0型) / 極大接地(k<0型)}
# =====================================================================
_W3 = 150.0   # svg 論理幅
_H3 = 108.0   # svg 論理高
_OX3 = 74.0   # 原点 x (px)
_OY3 = 56.0   # 原点 y (px)
_SX3 = 20.0   # x スケール
_SY3 = 7.6    # y スケール (縦は圧縮)


def _poly3(coef, xr, n=120):
    """3次曲線 coef=(a,b,c,d): a x^3+b x^2+c x+d を xr=(x0,x1) でサンプルしてSVGパス点列に。"""
    a, b, c, d = coef
    x0, x1 = xr
    pts = []
    for i in range(n + 1):
        xw = x0 + (x1 - x0) * i / n
        yw = a * xw ** 3 + b * xw ** 2 + c * xw + d
        px = _OX3 + _SX3 * xw
        py = _OY3 - _SY3 * yw
        py = max(6.0, min(_H3 - 6.0, py))
        pts.append(f"{px:.1f} {py:.1f}")
    return "M" + " L".join(pts)


def _fig3_svg(coef, xr, width=140):
    """概形1枚。座標軸(矢印つき)+O のみ。"""
    s = [f"<svg viewBox='0 0 {_W3:.0f} {_H3:.0f}' width='{width}' xmlns='http://www.w3.org/2000/svg'>"]
    # 軸
    s.append(f"<line x1='6' y1='{_OY3}' x2='{_W3-4:.0f}' y2='{_OY3}' stroke='#333' stroke-width='0.9'/>")
    s.append(f"<path d='M{_W3-4:.0f} {_OY3} L{_W3-10:.0f} {_OY3-2.6} L{_W3-10:.0f} {_OY3+2.6} Z' fill='#333'/>")
    s.append(f"<line x1='{_OX3}' y1='{_H3-4:.0f}' x2='{_OX3}' y2='4' stroke='#333' stroke-width='0.9'/>")
    s.append(f"<path d='M{_OX3} 4 L{_OX3-2.6} 10 L{_OX3+2.6} 10 Z' fill='#333'/>")
    s.append(f"<text x='{_OX3-9:.0f}' y='{_OY3+11:.0f}' font-size='9' font-style='italic' "
             f"font-family='Times New Roman,serif'>O</text>")
    s.append(f"<text x='{_W3-6:.0f}' y='{_OY3-4:.0f}' font-size='9' font-style='italic' "
             f"font-family='Times New Roman,serif'>x</text>")
    s.append(f"<text x='{_OX3+4:.0f}' y='12' font-size='9' font-style='italic' "
             f"font-family='Times New Roman,serif'>y</text>")
    # 曲線
    s.append(f"<path d='{_poly3(coef, xr)}' fill='none' stroke='#333' stroke-width='1.3'/>")
    s.append("</svg>")
    return "".join(s)


# 6図カタログ (⓪..⑤).
# base(x)=A(x^3-6x^2+9x)  → 極大 @x=1 値 4A, 極小 @x=3 値 0 (原点も通る)。vshift で全体を上下に。
_A6 = 1.0 / 3.0
def _base_pos(vshift):
    # A(x^3-6x^2+9x)+vshift  極大@x=1 値 4A+vshift, 極小@x=3 値 vshift
    return (_A6, -6 * _A6, 9 * _A6, vshift)
def _base_neg(vshift):
    # 鏡像: -A(x^3-6x^2+9x)+vshift  極小@x=1 値 -4A+vshift, 極大@x=3 値 vshift
    return (-_A6, 6 * _A6, -9 * _A6, vshift)

_XR6 = (-0.55, 4.15)
_MAX_CONST = 4 * _A6   # 極大の生値 = 4A
# 設計:
#  ⓪ 正係数・両極値とも x軸より上 (極小>0)              ← キ (k>0) の正解
#  ① 負係数・⓪の鏡像
#  ② 正係数・極小が x軸に接する (原点通過, 極小=0)        ← カ (k=0) の正解
#  ③ 負係数・②の鏡像 (極大が x軸に接する)
#  ④ 正係数・極大が x軸に接する (極小は x軸下)            (k<0 型)
#  ⑤ 負係数・④の鏡像
_FIG6_COEF = [
    _base_pos(1.15),                # ⓪ 極小を +1.15 上げ → 両極値とも明確に x軸より上
    _base_neg(-1.15),               # ① ⓪の鏡像
    _base_pos(0.0),                 # ② 極小=0 で接地
    _base_neg(0.0),                 # ③ 極大=0 で接地(鏡像)
    _base_pos(-_MAX_CONST),         # ④ 極大を 0 まで下げ接地 → 極小 <0
    _base_neg(_MAX_CONST),          # ⑤ ④の鏡像
]
_FIG6_XR = [_XR6] * 6


def _fig6_grid_html():
    circled = "⓪①②③④⑤"
    cells = []
    for i in range(6):
        cells.append(
            "<div style='padding:1.2mm 1mm 1mm;text-align:center;'>"
            f"<div style='font-family:\"Hiragino Kaku Gothic ProN\",sans-serif;font-weight:700;"
            f"font-size:11pt;margin-bottom:0.5mm'>{circled[i]}</div>"
            f"{_fig3_svg(_FIG6_COEF[i], _FIG6_XR[i])}</div>")
    return ("<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:2.5mm;"
            "margin:3mm 0;'>" + "".join(cells) + "</div>")


_FIG6_GRID = _fig6_grid_html()


# =====================================================================
#  Q3 (2): 3次関数グラフ概形 8図 (⓪..⑦)
#  条件 (a) g(0)=0 ∧ g'(0)>0 / (b) g' の軸 x=0 (原点対称) / (c) g' 下に凸(正係数)
#  正解: (a)={①,②,④}, (a)&(b)={①,④}, (a)&(b)&(c)={④}
# =====================================================================
_W8 = 132.0
_H8 = 104.0
_OX8 = 66.0
_OY8 = 52.0
_SX8 = 18.0
_SY8 = 4.6


def _poly8(coef, xr, n=140):
    a, b, c, d = coef
    x0, x1 = xr
    pts = []
    for i in range(n + 1):
        xw = x0 + (x1 - x0) * i / n
        yw = a * xw ** 3 + b * xw ** 2 + c * xw + d
        px = _OX8 + _SX8 * xw
        py = _OY8 - _SY8 * yw
        py = max(6.0, min(_H8 - 6.0, py))   # 縦にはみ出す枝を枠内に抑える
        pts.append(f"{px:.1f} {py:.1f}")
    return "M" + " L".join(pts)


def _fig8_svg(coef, xr, width=124):
    s = [f"<svg viewBox='0 0 {_W8:.0f} {_H8:.0f}' width='{width}' xmlns='http://www.w3.org/2000/svg'>"]
    s.append(f"<line x1='6' y1='{_OY8}' x2='{_W8-4:.0f}' y2='{_OY8}' stroke='#333' stroke-width='0.9'/>")
    s.append(f"<path d='M{_W8-4:.0f} {_OY8} L{_W8-10:.0f} {_OY8-2.6} L{_W8-10:.0f} {_OY8+2.6} Z' fill='#333'/>")
    s.append(f"<line x1='{_OX8}' y1='{_H8-4:.0f}' x2='{_OX8}' y2='4' stroke='#333' stroke-width='0.9'/>")
    s.append(f"<path d='M{_OX8} 4 L{_OX8-2.6} 10 L{_OX8+2.6} 10 Z' fill='#333'/>")
    s.append(f"<text x='{_OX8-9:.0f}' y='{_OY8+11:.0f}' font-size='8.5' font-style='italic' "
             f"font-family='Times New Roman,serif'>O</text>")
    s.append(f"<text x='{_W8-6:.0f}' y='{_OY8-4:.0f}' font-size='8.5' font-style='italic' "
             f"font-family='Times New Roman,serif'>x</text>")
    s.append(f"<text x='{_OX8+4:.0f}' y='12' font-size='8.5' font-style='italic' "
             f"font-family='Times New Roman,serif'>y</text>")
    s.append(f"<path d='{_poly8(coef, xr)}' fill='none' stroke='#333' stroke-width='1.25'/>")
    s.append("</svg>")
    return "".join(s)


# 8つの具体 3次 (a,b,c,d):
#  ⓪ x^3-3x        原点対称・原点で減少 (g'(0)=-3<0)               → (a)不成立
#  ① -x^3+3x       ⓪の鏡像・原点で増加 (g'(0)=3>0), 軸x=0, 負係数  → (a),(b)成立,(c)不成立
#  ② x^3+3x^2+3x   g'=3(x+1)^2, g'(0)=3>0, b≠0 (非対称)            → (a)成立,(b)不成立
#  ③ -x^3+3x^2-3x  ②の鏡像 g'(0)=-3<0                             → (a)不成立
#  ④ x^3+3x        単調増加(極値なし) g'(0)=3>0, 軸x=0, 正係数     → (a)(b)(c)すべて成立 (ナ)
#  ⑤ -x^3-3x       単調減少 g'(0)=-3<0                            → (a)不成立
#  ⑥ x^3+3x^2+3x+2 g(0)=2≠0 (原点不通過)                         → (a)不成立
#  ⑦ -x^3-3x^2-3x+2 g(0)=2≠0                                     → (a)不成立
_FIG8_COEF = [
    (1, 0, -3, 0),      # ⓪
    (-1, 0, 3, 0),      # ①  ← (a)(b)
    (1, 3, 3, 0),       # ②  ← (a)
    (-1, 3, -3, 0),     # ③
    (1, 0, 3, 0),       # ④  ← (a)(b)(c) ナ
    (-1, 0, -3, 0),     # ⑤
    (1, 3, 3, 2),       # ⑥
    (-1, -3, -3, 2),    # ⑦
]
# 各図の x 表示範囲 (枝が枠に収まるよう個別調整)
_FIG8_XR = [
    (-2.15, 2.15), (-2.15, 2.15),
    (-2.9, 1.0), (-1.0, 2.9),
    (-1.75, 1.75), (-1.75, 1.75),
    (-2.9, 1.0), (-2.7, 1.15),
]


def _fig8_grid_html():
    circled = "⓪①②③④⑤⑥⑦"
    cells = []
    for i in range(8):
        cells.append(
            "<div style='padding:1.2mm 1mm 1mm;text-align:center;'>"
            f"<div style='font-family:\"Hiragino Kaku Gothic ProN\",sans-serif;font-weight:700;"
            f"font-size:11pt;margin-bottom:0.5mm'>{circled[i]}</div>"
            f"{_fig8_svg(_FIG8_COEF[i], _FIG8_XR[i])}</div>")
    return ("<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:2.5mm;"
            "margin:3mm 0;'>" + "".join(cells) + "</div>")


_FIG8_GRID = _fig8_grid_html()


# =====================================================================
#  Q4: 「発想」ボックス (角丸罫囲み・見出し「発想」を枠線上に重ねる)
# =====================================================================
_HASSOU_HTML = (
    "<div style='border:1.3px solid #222;border-radius:3mm;padding:3.5mm 5mm 3mm;"
    "margin:3mm 4mm;position:relative;font-size:10.3pt;line-height:1.9;'>"
    "<div style='position:absolute;top:-2.6mm;left:6mm;background:#fff;padding:0 2mm;"
    "font-family:\"Hiragino Kaku Gothic ProN\",sans-serif;font-weight:700;font-size:10.5pt;'>発想</div>"
    "ある数列 {<i>d<sub>n</sub></i>} の和を求めたいときは，数列 {<i>c<sub>n</sub></i>} で，"
    "{<i>c<sub>n</sub></i>} の階差数列が {<i>d<sub>n</sub></i>} となるもの，すなわち "
    "<i>c<sub>n+1</sub></i> &minus; <i>c<sub>n</sub></i> = <i>d<sub>n</sub></i> "
    "を満たすものを見つければよい。</div>"
)


# =====================================================================
#  SECTIONS
# =====================================================================
SECTIONS = [
    # ---------------------------------------------------------------
    #  第3問 (必答) 配点22 — 微分法・積分法
    # ---------------------------------------------------------------
    {"no": 3, "points": 22, "optional": "必答問題",
     "parts": [
         {"label": "", "blocks": [
             {"t": "p", "text": r"$k$ を実数とし，$3$ 次関数"},
             {"t": "m", "tex": r"f(x)=\dfrac{5}{3}x^3-10x^2+15x+k"},
             {"t": "p", "text": r"について考える。"},

             {"t": "p", "text": r"<b>(1)　(i)</b>　$f(x)$ を微分すると"},
             {"t": "m", "tex": r"f'(x)=〚ア〛"},
             {"t": "p", "text": r"である。よって，$f(x)$ は $x=〔イ〕$ のとき極大値 〚ウ〛 をとり，"
                                 r"$x=〔エ〕$ のとき極小値 〚オ〛 をとる。"},
             {"t": "choices", "for": "ア", "auto_intro": True,
              "items": [r"$\dfrac{5}{3}x^2-10x+15+k$", r"$\dfrac{5}{3}x^2-10x+15$",
                        r"$5x^2-20x+15$", r"$5x^2-20x+15+k$",
                        r"$\dfrac{5}{12}x^4-\dfrac{10}{3}x^3+\dfrac{15}{2}x^2+kx$",
                        r"$\dfrac{5}{3}x^4-10x^3+15x^2+kx$"], "cols": 2},
             {"t": "choices", "for": r"〚ウ〛，〚オ〛の解答群（同じものを繰り返し選んでもよい。）",
              "items": [r"$0$", r"$1$", r"$2$", r"$\dfrac{5}{3}$", r"$\dfrac{20}{3}$",
                        r"$k$", r"$-\dfrac{20}{3}+k$", r"$-\dfrac{5}{3}+k$",
                        r"$\dfrac{5}{3}+k$", r"$\dfrac{20}{3}+k$"], "cols": 5},

             {"t": "p", "text": r"<b>(ii)</b>　$y=f(x)$ のグラフの概形は，$k=0$ のとき 〚カ〛 であり，$k>0$ のとき 〚キ〛 である。"},
             {"t": "p", "text": r"〚カ〛，〚キ〛については，最も適当なものを，次の<b>⓪</b>〜<b>⑤</b>のうちから"
                                 r"一つずつ選べ。ただし，同じものを繰り返し選んでもよい。なお，"
                                 r"<b>⓪</b>〜<b>⑤</b>では座標軸と原点 $\mathrm{O}$ のみを示している。"},
             {"t": "html", "html": _FIG6_GRID},

             {"t": "p", "text": r"<b>(iii)</b>　(i) で求めた極大・極小を与える $x$ の値のうち，小さい方を $\alpha$ とする。"
                                 r"以下では，$f(0)<0<f(\alpha)$ が成り立つように $k$ の値を定めることを考える。"
                                 r"この条件は"},
             {"t": "m", "tex": r"〚ク〛<k<〚ケ〛"},
             {"t": "p", "text": r"と同値である。以下，$k$ はこの範囲にあるとする。このとき，$0\leqq x\leqq\alpha$ の範囲に"
                                 r"$f(x)=0$ を満たす $x$ がただ一つ存在するので，それを $\beta$ とおく。"},
             {"t": "choices", "for": r"〚ク〛，〚ケ〛の解答群（同じものを繰り返し選んでもよい。）",
              "items": [r"$0$", r"$\dfrac{5}{3}$", r"$\dfrac{10}{3}$", r"$\dfrac{20}{3}$", r"$\dfrac{5}{2}$",
                        r"$-\dfrac{5}{3}$", r"$-\dfrac{10}{3}$", r"$-\dfrac{20}{3}$", r"$-\dfrac{5}{2}$", r"$-\dfrac{25}{3}$"],
              "cols": 5},

             {"t": "p", "text": r"いま，次の二つの面積が等しくなるように $k$ の値を定めたい。"},
             {"t": "p", "text": r"・$0\leqq x\leqq\beta$ において，曲線 $y=f(x)$，$x$ 軸および $y$ 軸で囲まれた部分の面積 $S_1$",
              "indent": True},
             {"t": "p", "text": r"・$\beta\leqq x\leqq\alpha$ において，曲線 $y=f(x)$，$x$ 軸および直線 $x=\alpha$ で囲まれた部分の面積 $S_2$",
              "indent": True},
             {"t": "p", "text": r"$0\leqq x\leqq\beta$ では $f(x)\leqq0$，$\beta\leqq x\leqq\alpha$ では $f(x)\geqq0$ である"
                                 r"ことに注意すると，$S_1=S_2$ となるための条件は 〚コ〛 が成り立つことである。"},
             {"t": "choices", "for": "コ", "auto_intro": True,
              "items": [r"$\displaystyle\int_0^{\beta}f(x)\,dx=\int_{\beta}^{\alpha}f(x)\,dx$",
                        r"$\displaystyle\int_0^{\alpha}f(x)\,dx=0$",
                        r"$\displaystyle\int_0^{\beta}f(x)\,dx=0$",
                        r"$\displaystyle\int_{\beta}^{\alpha}f(x)\,dx=0$"], "cols": 1},
             {"t": "p", "text": r"これを解くと"},
             {"t": "m", "tex": r"k=\dfrac{サシス}{セソ}"},
             {"t": "p", "text": r"である。"},

             {"t": "p", "text": r"<b>(2)</b>　$3$ 次関数 $g(x)$ に対して，与えられた条件のもとで $y=g(x)$ のグラフの概形を考えよう。"},
             {"t": "boxnote", "title": "条件(a)", "lines": [
                 r"$g(0)=0$ かつ $g'(0)>0$ である。"]},
             {"t": "p", "text": r"後の<b>⓪</b>〜<b>⑦</b>のうち，条件(a)を満たす $y=g(x)$ のグラフの概形は "
                                 r"〚タ〛，〚チ〛，〚ツ〛 の三つであり，残りの五つは条件(a)を満たさない。"
                                 r"ただし，〚タ〛，〚チ〛，〚ツ〛 の解答の順序は問わない。"},
             {"t": "boxnote", "title": "条件(b)", "lines": [
                 r"条件(a)に加えて，$y=g'(x)$ のグラフは直線 $x=0$ を軸とする放物線である。"]},
             {"t": "p", "text": r"条件(a)，(b)をともに満たす $y=g(x)$ のグラフの概形は 〚テ〛，〚ト〛 の二つであり，"
                                 r"残りの六つは条件(a)，(b)の少なくとも一方を満たさない。"
                                 r"ただし，〚テ〛，〚ト〛 の解答の順序は問わない。"},
             {"t": "boxnote", "title": "条件(c)", "lines": [
                 r"条件(a)，(b)に加えて，$y=g'(x)$ のグラフは下に凸の放物線である。"]},
             {"t": "p", "text": r"条件(a)，(b)，(c)をすべて満たす $y=g(x)$ のグラフの概形は 〚ナ〛 の一つだけである。"},
             {"t": "p", "text": r"〚タ〛〜〚ナ〛については，最も適当なものを，次の<b>⓪</b>〜<b>⑦</b>のうちから"
                                 r"一つずつ選べ。ただし，同じものを繰り返し選んでもよい。なお，"
                                 r"<b>⓪</b>〜<b>⑦</b>では座標軸と原点 $\mathrm{O}$ のみを示している。"},
             {"t": "html", "html": _FIG8_GRID},
         ]},
     ]},

    # ---------------------------------------------------------------
    #  第4問 (選択) 配点16 — 数列(階差数列)
    # ---------------------------------------------------------------
    {"no": 4, "points": 16, "optional": "選択問題",
     "parts": [
         {"label": "", "blocks": [
             {"t": "boxnote", "lines": [
                 r"第4問〜第7問は，いずれか3問を選択し，解答しなさい。"]},
             {"t": "p", "text": r"数列 $\{a_n\}$ に対して"},
             {"t": "m", "tex": r"b_n=a_{n+1}-a_n \quad(n=1,\,2,\,3,\,\cdots)"},
             {"t": "p", "text": r"で定められる数列 $\{b_n\}$ を，$\{a_n\}$ の<b>階差数列</b>という。"},

             {"t": "p", "text": r"<b>(1)</b>　数列 $\{a_n\}$ の階差数列 $\{b_n\}$ が"},
             {"t": "m", "tex": r"b_n=6n-3 \quad(n=1,\,2,\,3,\,\cdots)"},
             {"t": "p", "text": r"であり，$a_1=4$ であるとする。"},
             {"t": "p", "text": r"<b>(i)</b>　$b_1=〔ア〕$ であるから，$a_2=〔イ〕$ となる。さらに，"
                                 r"$b_2=〔ウ〕$ であるから，$a_3=〔エオ〕$ となる。"},
             {"t": "p", "text": r"<b>(ii)</b>　$n$ を $2$ 以上の自然数とする。このとき"},
             {"t": "m", "tex": r"a_n=a_1+\sum_{k=1}^{〚カ〛}b_k \quad\cdots\cdots ①"},
             {"t": "p", "text": r"が成り立つ。これより，$a_1=4$ の場合も含めて，すべての自然数 $n$ について"},
             {"t": "m", "tex": r"a_n=〔キ〕n^2-〔ク〕n+〔ケ〕"},
             {"t": "p", "text": r"であることがわかる。"},
             {"t": "choices", "for": "カ", "auto_intro": True,
              "items": [r"$n-1$", r"$n$", r"$n+1$", r"$n+2$"], "cols": 4},

             {"t": "p", "text": r"<b>(2)</b>　太郎さんは，数列 $\{d_n\}$ が"},
             {"t": "m", "tex": r"d_n=(3n-1)\cdot 2^n \quad(n=1,\,2,\,3,\,\cdots)"},
             {"t": "p", "text": r"で定められるとき，初項から第 $n$ 項までの和 $\displaystyle\sum_{k=1}^{n}d_k$ を"
                                 r"求める方法を考えた。①を変形すると，$n$ を $2$ 以上の自然数として "
                                 r"$\displaystyle\sum_{k=1}^{n-1}b_k=a_n-a_1$ となることに着目して，太郎さんは次のように考えた。"},
             {"t": "html", "html": _HASSOU_HTML},
             {"t": "convo", "turns": [
                 {"sp": "太郎", "text": r"$\{c_n\}$ の一般項を $c_n=(pn+q)\cdot 2^n$（$p,\ q$ は定数）と"
                                        r"推測して，$c_{n+1}-c_n=d_n$ となる $p,\ q$ を求めればよさそうだね。"}]},
             {"t": "p", "text": r"$c_n=(pn+q)\cdot 2^n$ とおくと"},
             {"t": "m", "tex": r"c_{n+1}-c_n=\left\{〚コ〛\,n+〚サ〛\right\}\cdot 2^n \quad\cdots\cdots ②"},
             {"t": "p", "text": r"となる。②の右辺が $d_n=(3n-1)\cdot 2^n$ と一致するのは"},
             {"t": "m", "tex": r"p=〔シ〕,\qquad q=〔スセ〕"},
             {"t": "p", "text": r"のときである。"},
             {"t": "choices", "for": r"〚コ〛，〚サ〛の解答群（同じものを繰り返し選んでもよい。）",
              "items": [r"$p$", r"$q$", r"$2p$", r"$2q$", r"$p+q$",
                        r"$2p+q$", r"$p+2q$", r"$2(p+q)$"], "cols": 4},

             {"t": "p", "text": r"このとき $c_{n+1}-c_n=d_n$ が成り立つから，$\{d_n\}$ の初項から第 $n$ 項までの和は，"
                                 r"$c_1$ を用いて $\displaystyle\sum_{k=1}^{n}d_k=c_{n+1}-c_1$ と表せる。したがって"},
             {"t": "m", "tex": r"\sum_{k=1}^{n}d_k=\bigl(〚ソ〛\bigr)\cdot 2^{\,n+1}+〔タ〕"},
             {"t": "p", "text": r"となることがわかる。"},
             {"t": "choices", "for": "ソ", "auto_intro": True,
              "items": [r"$3n-2$", r"$3n-4$", r"$2n-3$", r"$2n-1$", r"$n-1$", r"$n+1$"], "cols": 3},

             {"t": "p", "text": r"<b>(3)</b>　花子さんは，(2)の<b>発想</b>に基づいて，数列 $\{d_n\}$ が"},
             {"t": "m", "tex": r"d_n=(n^2-2n-2)\cdot 2^n \quad(n=1,\,2,\,3,\,\cdots)"},
             {"t": "p", "text": r"で定められるときの和を考えた。今度は $\{c_n\}$ の一般項を $2$ 次式を用いて "
                                 r"$c_n=(rn^2+sn+t)\cdot 2^n$（$r,\ s,\ t$ は定数）と推測し，$c_{n+1}-c_n=d_n$ となる"
                                 r"$r,\ s,\ t$ を定めると"},
             {"t": "m", "tex": r"\sum_{k=1}^{n}d_k=\bigl(〚チ〛\bigr)\cdot 2^{\,n+1}-〔ツ〕"},
             {"t": "p", "text": r"となることがわかる。"},
             {"t": "choices", "for": "チ", "auto_intro": True,
              "items": [r"$3n-3$", r"$3n+3$", r"$2n-3$", r"$2n+3$",
                        r"$n^2-4n+3$", r"$n^2-6n+8$", r"$n^2+2n-2$", r"$n^2-2n-2$",
                        r"$n^2+4n+1$", r"$n^2-4n-1$"], "cols": 5},
         ]},
     ]},
]


# =====================================================================
#  ANS_SECTIONS
# =====================================================================
ANS_SECTIONS = [
    # ---------------- 第3問 ----------------
    {"section": 3,
     "slots": {
         "ア": "②",                                    # f'(x)=5x^2-20x+15
         "イ": "1", "ウ": "⑨",                          # 極大 x=1, 値 20/3+k
         "エ": "3", "オ": "⑤",                          # 極小 x=3, 値 k
         "カ": "②", "キ": "⓪",                          # k=0図②, k>0図⓪
         "ク": "⑦", "ケ": "⓪",                          # -20/3 < k < 0
         "コ": "①",                                    # ∫_0^α f dx = 0
         "サ": "−", "シ": "5", "ス": "5",                # k = -55/12 (numerator -55)
         "セ": "1", "ソ": "2",                          # denominator 12
         "タ": "①", "チ": "②", "ツ": "④",                # (a): {①,②,④} 順不同
         "テ": "①", "ト": "④",                          # (b): {①,④} 順不同
         "ナ": "④",                                    # (c): {④}
     },
     "kai": [
         {"heading": "第3問　微分法・積分法", "blocks": [
             {"t": "p", "text": r"<b>(1)(i)</b>　各項を微分する。定数項 $k$ は微分すると $0$ になることに注意すると"},
             {"t": "m", "tex": r"f'(x)=\dfrac{5}{3}\cdot 3x^2-10\cdot 2x+15=5x^2-20x+15=5(x-1)(x-3)"},
             {"t": "p", "text": r"よって 〚ア〛=<b>②</b>。$\dfrac53$ のまま微分し忘れた①，$k$ を残した③④，"
                                 r"積分してしまった④⑤は誤り。"},
             {"t": "p", "text": r"$f'(x)=0$ より $x=1,\ 3$。$x=1$ の前後で $f'$ は正→負に変わるので極大，"
                                 r"$x=3$ の前後で負→正に変わるので極小。極値は"},
             {"t": "m", "tex": r"f(1)=\dfrac53-10+15+k=\dfrac{20}{3}+k,\qquad f(3)=45-90+45+k=k"},
             {"t": "p", "text": r"よって $x=1$（〔イ〕）で極大値 $\dfrac{20}{3}+k$（〚ウ〛=<b>⑨</b>），"
                                 r"$x=3$（〔エ〕）で極小値 $k$（〚オ〛=<b>⑤</b>）。"
                                 r"極値が $k$ を含む式になるので選択式。$k$ を含まない ⓪〜④ は誤り。"},

             {"t": "p", "text": r"<b>(ii)</b>　$y$ 切片は $f(0)=k$，極小値も $f(3)=k$，極大値は $f(1)=\dfrac{20}{3}+k>f(3)$。"
                                 r"$x^3$ の係数は正なので右上がりで，極大が左（$x=1$）・極小が右（$x=3$）にある。"},
             {"t": "p", "text": r"$k=0$ のとき極小値 $f(3)=0$ となり，グラフは極小で $x$ 軸に接する（原点も通る）。"
                                 r"これは 〚カ〛=<b>②</b>。$k>0$ のとき極小値 $f(3)=k>0$ となり，両極値とも $x$ 軸より上。"
                                 r"これは 〚キ〛=<b>⓪</b>。負係数の①③⑤や，極大が接する④は不適。"},

             {"t": "p", "text": r"<b>(iii)</b>　極大・極小を与える $x$ は $1,\ 3$ で，小さい方は $\alpha=1$。"},
             {"t": "m", "tex": r"f(0)=k,\qquad f(1)=\dfrac{20}{3}+k"},
             {"t": "p", "text": r"$f(0)<0<f(\alpha)$ すなわち $k<0$ かつ $\dfrac{20}{3}+k>0$ より"},
             {"t": "m", "tex": r"-\dfrac{20}{3}<k<0"},
             {"t": "p", "text": r"よって 〚ク〛=<b>⑦</b>（$-\dfrac{20}{3}$），〚ケ〛=<b>⓪</b>（$0$）。"},
             {"t": "p", "text": r"次に面積の条件。$0\leqq x\leqq\beta$ では $f(x)\leqq0$ なので "
                                 r"$S_1=-\displaystyle\int_0^{\beta}f(x)\,dx$，$\beta\leqq x\leqq\alpha$ では $f(x)\geqq0$ なので "
                                 r"$S_2=\displaystyle\int_{\beta}^{\alpha}f(x)\,dx$。$S_1=S_2$ は次と同値。"},
             {"t": "m", "tex": r"-\int_0^{\beta}\!\!f\,dx=\int_{\beta}^{\alpha}\!\!f\,dx \iff \int_0^{\beta}\!\!f\,dx+\int_{\beta}^{\alpha}\!\!f\,dx=0 \iff \int_0^{\alpha}\!\!f(x)\,dx=0"},
             {"t": "p", "text": r"すなわち「全区間 $0\leqq x\leqq\alpha$ での定積分が $0$」。よって 〚コ〛=<b>①</b>。"
                                 r"「面積が等しい ⇔ 符号付き面積の和が $0$」という同値変形が要点。⓪は符号を無視した式，"
                                 r"②③は片方だけ $0$ とする誤り。"},
             {"t": "p", "text": r"$\alpha=1$ として計算する。"},
             {"t": "m", "tex": r"\int_0^{1}\!\Bigl(\dfrac53x^3-10x^2+15x+k\Bigr)dx=\Bigl[\dfrac{5}{12}x^4-\dfrac{10}{3}x^3+\dfrac{15}{2}x^2+kx\Bigr]_0^1=\dfrac{5}{12}-\dfrac{10}{3}+\dfrac{15}{2}+k"},
             {"t": "m", "tex": r"=\dfrac{5-40+90}{12}+k=\dfrac{55}{12}+k=0 \ \Rightarrow\ k=-\dfrac{55}{12}"},
             {"t": "p", "text": r"よって $k=\dfrac{-55}{12}$（サシス$=-55$，セソ$=12$）。この $k$ は $-\dfrac{20}{3}<k<0$ を"
                                 r"満たしており，$\beta$ が $0<\beta<1$ に存在することとも整合する。"},

             {"t": "p", "text": r"<b>(2)</b>　三つの条件を順にグラフの性質へ読み替える。"},
             {"t": "p", "text": r"・条件(a)：$g(0)=0$ は「原点を通る」，$g'(0)>0$ は「原点での接線の傾きが正"
                                 r"（原点で増加）」。⓪〜⑦のうち原点を通り，かつ原点で増加しているのは "
                                 r"<b>①</b>，<b>②</b>，<b>④</b>。よって $\{$〚タ〛，〚チ〛，〚ツ〛$\}=\{①,②,④\}$（順不同）。"
                                 r"⑥⑦は原点を通らず（$g(0)\neq0$），⓪③⑤は原点で減少しているので不適。"},
             {"t": "p", "text": r"・条件(b)：$y=g'(x)$ が直線 $x=0$ を軸とする放物線 $\iff$ $g'(x)$ に $1$ 次の項がない "
                                 r"$\iff$ $g(x)$ に $2$ 次の項がない $\iff$ グラフが原点に関して対称。"
                                 r"(a)を満たす①②④のうち，原点対称なのは <b>①</b> と <b>④</b>。②は $2$ 次の項をもち"
                                 r"非対称なので外れる。よって $\{$〚テ〛，〚ト〛$\}=\{①,④\}$（順不同）。"},
             {"t": "p", "text": r"・条件(c)：$y=g'(x)$ が下に凸 $\iff$ $g'(x)$ の $x^2$ の係数が正 $\iff$ $g(x)$ の"
                                 r"$x^3$ の係数が正（正係数の $3$ 次関数）。①は負係数，④は正係数だから，残るのは "
                                 r"<b>④</b> のみ。よって 〚ナ〛=<b>④</b>。"},
             {"t": "p", "text": r"（④は $g(x)=x^3+3x$ 型で極値をもたず単調増加。$g'(x)=3x^2+3$ は下に凸で軸が $x=0$，"
                                 r"$g'(0)=3>0$，$g(0)=0$ とすべての条件を満たす。）"},
         ]},
     ]},

    # ---------------- 第4問 ----------------
    {"section": 4,
     "slots": {
         "ア": "3", "イ": "7", "ウ": "9", "エ": "1", "オ": "6",   # b1=3,a2=7,b2=9,a3=16
         "カ": "⓪",                                              # Σ上限 n-1
         "キ": "3", "ク": "6", "ケ": "7",                         # a_n=3n^2-6n+7
         "コ": "⓪", "サ": "⑤",                                   # p, 2p+q
         "シ": "3", "ス": "−", "セ": "7",                         # p=3, q=-7
         "ソ": "①", "タ": "8",                                   # (3n-4)·2^{n+1}+8
         "チ": "④", "ツ": "6",                                   # (n^2-4n+3)·2^{n+1}-6
     },
     "kai": [
         {"heading": "第4問　数列（階差数列）", "blocks": [
             {"t": "p", "text": r"<b>(1)(i)</b>　$b_n=6n-3$ より"},
             {"t": "m", "tex": r"b_1=6\cdot1-3=3,\qquad a_2=a_1+b_1=4+3=7"},
             {"t": "m", "tex": r"b_2=6\cdot2-3=9,\qquad a_3=a_2+b_2=7+9=16"},
             {"t": "p", "text": r"よって $b_1=3$（〔ア〕），$a_2=7$（〔イ〕），$b_2=9$（〔ウ〕），$a_3=16$（〔エオ〕）。"},
             {"t": "p", "text": r"<b>(ii)</b>　階差数列の一般項の公式より，$n\geqq2$ のとき"},
             {"t": "m", "tex": r"a_n=a_1+\sum_{k=1}^{n-1}b_k"},
             {"t": "p", "text": r"であるから，$\Sigma$ の上限は $n-1$。よって 〚カ〛=<b>⓪</b>。"
                                 r"（①〜③のように上限を $n,\ n+1,\ n+2$ とすると項数が合わない。）"},
             {"t": "m", "tex": r"\sum_{k=1}^{n-1}(6k-3)=6\cdot\dfrac{(n-1)n}{2}-3(n-1)=3n^2-3n-3n+3=3n^2-6n+3"},
             {"t": "m", "tex": r"a_n=4+(3n^2-6n+3)=3n^2-6n+7"},
             {"t": "p", "text": r"$n=1$ を代入すると $3-6+7=4=a_1$ となり，$n=1$ でも成り立つ。"
                                 r"よって $a_n=3n^2-6n+7$（〔キ〕$=3$，〔ク〕$=6$，〔ケ〕$=7$）。"},

             {"t": "p", "text": r"<b>(2)</b>　①より $\displaystyle\sum_{k=1}^{n-1}b_k=a_n-a_1$。同じ発想で，"
                                 r"$\{d_n\}$ の和を求めるには「階差が $d_n$ になる数列 $\{c_n\}$」を見つければよい。"},
             {"t": "p", "text": r"$c_n=(pn+q)\cdot2^n$ とおくと"},
             {"t": "m", "tex": r"c_{n+1}-c_n=\left\{p(n+1)+q\right\}\cdot2^{n+1}-(pn+q)\cdot2^n"},
             {"t": "m", "tex": r"=2^n\bigl[\,2\{p(n+1)+q\}-(pn+q)\,\bigr]=2^n\bigl[\,pn+(2p+q)\,\bigr]"},
             {"t": "p", "text": r"よって $\{$〚コ〛$\,n+$〚サ〛$\}$ の 〚コ〛$=p$（<b>⓪</b>），〚サ〛$=2p+q$（<b>⑤</b>）。"},
             {"t": "p", "text": r"これが $d_n=(3n-1)\cdot2^n$ の $3n-1$ と一致する条件は，係数比較により"},
             {"t": "m", "tex": r"p=3,\qquad 2p+q=-1 \ \Rightarrow\ q=-1-2\cdot3=-7"},
             {"t": "p", "text": r"よって $p=3$（〔シ〕），$q=-7$（〔スセ〕，符号 $-$ を含めて $-7$）。すなわち "
                                 r"$c_n=(3n-7)\cdot2^n$。"},
             {"t": "p", "text": r"和は $c_{n+1}-c_1$ で求まる。"},
             {"t": "m", "tex": r"c_{n+1}=\{3(n+1)-7\}\cdot2^{n+1}=(3n-4)\cdot2^{n+1},\qquad c_1=(3-7)\cdot2=-8"},
             {"t": "m", "tex": r"\sum_{k=1}^{n}d_k=c_{n+1}-c_1=(3n-4)\cdot2^{n+1}-(-8)=(3n-4)\cdot2^{n+1}+8"},
             {"t": "p", "text": r"よって 〚ソ〛=<b>①</b>（$3n-4$），〔タ〕$=8$。"
                                 r"（検算：$n=1$ で右辺 $=(-1)\cdot4+8=4=d_1$。）"},

             {"t": "p", "text": r"<b>(3)</b>　同じ発想を $2$ 次に上げる。$c_n=(rn^2+sn+t)\cdot2^n$ とおくと"},
             {"t": "m", "tex": r"c_{n+1}-c_n=2^n\bigl[\,rn^2+(4r+s)n+(2r+2s+t)\,\bigr]"},
             {"t": "p", "text": r"これが $d_n=(n^2-2n-2)\cdot2^n$ と一致する条件は，係数比較により"},
             {"t": "m", "tex": r"r=1,\quad 4r+s=-2\Rightarrow s=-6,\quad 2r+2s+t=-2\Rightarrow t=8"},
             {"t": "p", "text": r"すなわち $c_n=(n^2-6n+8)\cdot2^n$。よって"},
             {"t": "m", "tex": r"c_{n+1}=\{(n+1)^2-6(n+1)+8\}\cdot2^{n+1}=(n^2-4n+3)\cdot2^{n+1}"},
             {"t": "m", "tex": r"c_1=(1-6+8)\cdot2=6"},
             {"t": "m", "tex": r"\sum_{k=1}^{n}d_k=c_{n+1}-c_1=(n^2-4n+3)\cdot2^{n+1}-6"},
             {"t": "p", "text": r"よって 〚チ〛=<b>④</b>（$n^2-4n+3$），〔ツ〕$=6$。"
                                 r"選択肢⑤ $n^2-6n+8$ は $c_n$ の係数そのもの（$c_{n+1}$ ではない）で，"
                                 r"取り違えを誘う誤答。$2^{n+1}$ の係数は $c_{n+1}$ 側の $n^2-4n+3$ である点に注意。"
                                 r"（検算：$n=1$ で右辺 $=(1-4+3)\cdot4-6=0-6=-6=d_1$。）"},
         ]},
     ]},
]
