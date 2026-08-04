# -*- coding: utf-8 -*-
"""math2bc_c.py: 2026共通テスト 数学ⅡBC そっくり類似問題
   — 第5問(統計的な推測)・第6問(ベクトル)・第7問(平面上の曲線と複素数平面)
   いずれも選択問題(第4問〜第7問から3問選択)・各配点16。

設計値(すべて content/verify_math2bc_c.py が独立計算で照合):
  ■第5問 資格試験の得点 X ~ N(180, 40²)、合格点 210。
    標準化 Y=(X-180)/40 (=①)。P(X≧210): z=0.75 → 0.23 (=①)。
    母比率検定: 過去5年の合格率 p0=1/5=0.2。「今年は 0.2 より高いか?」
      大標本 n1=300 中 m1=72 (p̂=0.24) → σ1=√3/75, z1=√3≒1.73, 裾0.0418 → 棄却。
      小標本 n2=150 中 m2=36 (p̂=0.24) → σ2=√6/75, z2=√6/2≒1.22, 裾0.1112 → 棄却されない。
    「同じ比率でも標本が小さいと棄却されない」構図。√3=1.73・√6=2.45 を本文指定。
  ■第6問 正六角形 DEFGCA(中心B)。MP=aMA+bMB+cMC。
    (1) (a,b,c)=(1,2,-1): P=A+2B-C-M。M=A→P=2B-C=F(⑤)、M=D→P=B(①)。
    (2) A始点書換 → AP=bAB+cAC+(1-a-b-c)AM。P が M に依らない ⇔ a+b+c=1。
    (3) a+b+c=1 のもとで a=1/2 → 直線IJ(中点連結)、c<0 → ABのC反対側の半平面。
  ■第7問 w=z+1/z(ジューコフスキー型)、円 C:|z|=r。
    (1) z=1+√3 i: |z|=2, w=(3√3)/4 + (5/4)i … ← 実部5/4・虚部3√3/4。
    (2) w=(r+1/r)cosθ + i(r-1/r)sinθ。θ非依存で虚部0 ⇔ r=1。r=1 → 実軸[-2,2]。
        r≠1 → θ消去で 楕円 x²/(r+1/r)²+y²/(r-1/r)²=1。
    (3) w²=z²+1/z²+2。z² は半径 r² の円 → 楕円 X²/(r²+1/r²)²+Y²/(r²-1/r²)²=1。
        +2 平行移動で「横長楕円・中心(2,0)」。
検証: python3 content/verify_math2bc_c.py  (全 assert 通過で ALL VERIFIED)
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _svg_math2bc_c import (normal_curve_fig, hexagon_fig, triangle_midpoints_fig,
                            region_figs_sec6, figs_sec7_ko, figs_sec7_se)

# 選択問題の各開始ページに毎回再掲する注意書き。
_SELECT_NOTE = {"t": "boxnote", "lines": [
    "第４問〜第７問は，いずれか３問を選択し，解答しなさい。"]}


# ---------------------------------------------------------------------------
# 図をラベル付きグリッドにまとめる小ヘルパ
# ---------------------------------------------------------------------------
_CIRC = "⓪①②③④⑤⑥⑦⑧⑨"


def _fig_grid(svgs, cols):
    cells = []
    for i, s in enumerate(svgs):
        cells.append(
            "<div style='padding:1.2mm 1mm 2mm;text-align:center;'>"
            "<div style='font-family:\"Hiragino Kaku Gothic ProN\",sans-serif;font-weight:700;"
            f"font-size:11pt;margin-bottom:.6mm'>{_CIRC[i]}</div>{s}</div>")
    return ("<div style='display:grid;grid-template-columns:repeat("
            f"{cols},1fr);gap:2.4mm;margin:3mm 0;break-inside:avoid;'>" + "".join(cells) + "</div>")


_REGION6_GRID = _fig_grid(region_figs_sec6(), 2)         # 第6問シ(2列×3段)
_KO6_GRID = _fig_grid(figs_sec7_ko(), 2)                 # 第7問コ(2列×3段)
_SE8_GRID = _fig_grid(figs_sec7_se(), 2)                 # 第7問セ(2列×4段)
_NORMAL_FIG = normal_curve_fig()
_HEX_FIG = hexagon_fig()
_TRI_FIG = triangle_midpoints_fig()


# ===========================================================================
#  SECTIONS
# ===========================================================================
SECTIONS = [

    # =======================================================================
    #  第5問 (選択問題) 配点16 — 統計的な推測
    # =======================================================================
    {"no": 5, "points": 16, "optional": "選択問題",
     "parts": [
         {"label": "", "blocks": [
             _SELECT_NOTE,
             {"t": "p", "text": r"以下の問題を解答するにあたっては，必要に応じて"
                                r"<b>この大問の末尾に掲げた正規分布表</b>を用いてもよい。"},
             {"t": "p", "text": r"ある自治体では，地域に関する知識を問う資格試験を実施している。"
                                r"この試験は $300$ 点満点で，$210$ 点以上を合格とする。"},

             # ------------------------------ (1) 標準化 ------------------------------
             {"t": "p", "text": r"<b>(1)</b>　今年の受験者全体の得点 $X$ は，平均 $180$ 点，"
                                 r"標準偏差 $40$ 点の正規分布 $N(180,\ 40^2)$ に従うものとする。"
                                 r"このとき"},
             {"t": "m", "tex": r"Y=〚ア〛"},
             {"t": "p", "text": r"とおくと，$Y$ は標準正規分布 $N(0,\ 1)$ に従う。"},
             {"t": "choices", "for": r"〚ア〛の解答群",
              "items": [r"$\dfrac{X-180}{\sqrt{40}}$", r"$\dfrac{X-180}{40}$",
                        r"$\dfrac{X-180}{40^2}$", r"$\dfrac{X-210}{\sqrt{40}}$",
                        r"$\dfrac{X-210}{40}$", r"$\dfrac{X-210}{40^2}$"], "cols": 3},
             {"t": "p", "text": r"また，今年の受験者全体のうち，$210$ 点以上である受験者の割合"
                                 r" $P(X\geqq 210)$ はおよそ 〚イ〛 である。"},
             {"t": "choices", "for": r"〚イ〛については，最も適当なものを，次の"
                                     r"<b>⓪</b>〜<b>⑦</b>のうちから一つ選べ。",
              "items": [r"$0.16$", r"$0.23$", r"$0.27$", r"$0.31$",
                        r"$0.50$", r"$0.73$", r"$0.77$", r"$0.84$"], "cols": 4},

             # ------------------------------ (2)(i) ベルヌーイ ------------------------
             {"t": "p", "text": r"<b>(2)</b>　この資格試験の合格率は，過去 $5$ 年間，毎年 $0.2$ であった。"
                                 r"今年の合格率が $0.2$ より高いと判断してよいかを，今年の受験者から"
                                 r"無作為に抽出した $n$ 人の標本をもとに考える。"},
             {"t": "p", "text": r"<b>(i)</b>　抽出した受験者のうち $i$ 番目の受験者が合格ならば $1$，"
                                 r"不合格ならば $0$ の値をとる確率変数を $W_i\ (i=1,\ 2,\ \cdots,\ n)$ とする。"
                                 r"母集団は十分大きく，合格率(母比率)を $p$ とすると，$W_i$ の確率分布は"
                                 r"次の表 $1$ のようになる。"},
             {"t": "table", "head": [r"$W_i$", r"$0$", r"$1$", r"計"],
              "rows": [[r"確率", r"$1-p$", r"$p$", r"$1$"]],
              "caption": r"表 1"},
             {"t": "p", "text": r"表 $1$ から，$W_i$ の平均(期待値)$E(W_i)$ は 〚ウ〛 となる。"
                                 r"また，$W_i$ の分散 $V(W_i)$ について"},
             {"t": "m", "tex": r"V(W_i)=\left\{0-E(W_i)\right\}^2(1-p)+\left\{1-E(W_i)\right\}^2\,p"},
             {"t": "p", "text": r"が成り立つことから，$V(W_i)$ は 〚エ〛 となる。"},
             {"t": "choices", "for": r"〚ウ〛，〚エ〛の解答群（同じものを繰り返し選んでもよい。）",
              "items": [r"$p$", r"$1-p$", r"$p^2$", r"$p(1-p)$",
                        r"$p^2(1-p)^2$", r"$p^3+(1-p)^3$"], "cols": 3},

             # ------------------------------ (2)(ii) 検定(大標本) --------------------
             {"t": "p", "text": r"<b>(ii)</b>　標本平均を $\overline{W}=\dfrac{W_1+W_2+\cdots+W_n}{n}$ とする。"
                                 r"$n$ が十分に大きいとき，$\overline{W}$ は近似的に正規分布"
                                 r" $N(p,\ 〚オ〛)$ に従う。"},
             {"t": "choices", "for": r"〚オ〛の解答群",
              "items": [r"$p$", r"$1-p$", r"$p(1-p)$", r"$\dfrac{p}{\sqrt{n}}$",
                        r"$\sqrt{\dfrac{p(1-p)}{n}}$", r"$\dfrac{p(1-p)}{\sqrt{n}}$",
                        r"$\dfrac{\sqrt{1-p}}{n}$", r"$\dfrac{p(1-p)}{n}$"], "cols": 4},
             {"t": "p", "text": r"ここで，統計的に検証したい仮説を<b>対立仮説</b>，"
                                 r"対立仮説に反する仮定として設けた仮説を<b>帰無仮説</b>という。"
                                 r"今年の合格率が $0.2$ より高いかどうかを，有意水準 $5\,\%$ で検定する。"
                                 r"すなわち，帰無仮説を「$p=0.2$」，対立仮説を「$p>0.2$」とする。"},
             {"t": "p", "text": r"いま，今年の受験者から無作為に $300$ 人を選んだところ，"
                                 r"そのうち $72$ 人が合格者であった。標本の大きさ $n=300$ は十分に大きいので，"
                                 r"帰無仮説が正しいと仮定すると，$\overline{W}$ は近似的に平均 $0.2$，"
                                 r"標準偏差 〚カ〛 の正規分布に従う。"},
             {"t": "choices", "for": r"〚カ〛の解答群",
              "items": [r"$\dfrac{3}{75}$", r"$\dfrac{\sqrt{3}}{25}$",
                        r"$\dfrac{\sqrt{3}}{5625}$", r"$\dfrac{\sqrt{3}}{75}$",
                        r"$\dfrac{4}{1875}$", r"$\dfrac{12}{75}$"], "cols": 3},
             {"t": "p", "text": r"$\sqrt{3}=1.73$ として用いると"},
             {"t": "m", "tex": r"P\!\left(\overline{W}\geqq \dfrac{72}{300}\right)"
                               r"=P\bigl(\overline{W}\geqq 0.24\bigr)"},
             {"t": "p", "text": r"の値は 〚キ〛 となる。よって，この値をパーセント表示した値は"
                                 r"有意水準 $5\,\%$ より 〚ク〛。したがって，有意水準 $5\,\%$ で，"
                                 r"今年のこの資格試験の合格率は $0.2$ より 〚ケ〛。"},
             {"t": "choices", "for": r"〚キ〛については，最も適当なものを，次の"
                                     r"<b>⓪</b>〜<b>⑦</b>のうちから一つ選べ。",
              "items": [r"$0.0446$", r"$0.3888$", r"$0.4582$", r"$0.0418$",
                        r"$0.0401$", r"$0.0495$", r"$0.4599$", r"$0.1112$"], "cols": 4},
             {"t": "choices", "for": r"〚ク〛の解答群",
              "items": [r"小さいから，帰無仮説は棄却されない",
                        r"小さいから，帰無仮説は棄却される",
                        r"大きいから，帰無仮説は棄却されない",
                        r"大きいから，帰無仮説は棄却される"], "cols": 1},
             {"t": "choices", "for": r"〚ケ〛の解答群",
              "items": [r"高いと判断できる", r"高いとは判断できない"], "cols": 2},

             {"t": "pagebreak"},

             # ------------------------------ (3) 小標本 ------------------------------
             {"t": "p", "text": r"<b>(3)</b>　太郎さんと花子さんは，(2)の(ii)の仮説検定の結果について"
                                 r"話している。"},
             {"t": "convo", "turns": [
                 {"sp": "太郎", "text": r"無作為に選んだ $100$ 人のうち $24$ 人が合格者でも，"
                                        r"比率は同じ $0.24$ になるから，仮説検定の結果は同じになるのかな。"},
                 {"sp": "花子", "text": r"試しに計算して調べてみようよ。"}]},
             {"t": "p", "text": r"今年のこの資格試験の受験者から無作為に選ばれた $150$ 人のうち，"
                                 r"$36$ 人が合格者である場合について考える。(2)の(ii)と同じ帰無仮説と対立仮説に対し，"
                                 r"有意水準 $5\,\%$ で帰無仮説が棄却されるかどうかを調べる。"},
             {"t": "p", "text": r"標本の大きさ $n=150$ は十分に大きいから，(2)の(ii)と同様に，"
                                 r"$\overline{W}$ は近似的に正規分布 $N(p,\ 〚オ〛)$ に従う。"
                                 r"帰無仮説が正しいと仮定する。このとき，$\sqrt{6}=2.45$ として用いると"},
             {"t": "m", "tex": r"P\!\left(\overline{W}\geqq \dfrac{36}{150}\right)"
                               r"=P\bigl(\overline{W}\geqq 0.24\bigr)"},
             {"t": "p", "text": r"の値をパーセント表示した値は有意水準 $5\,\%$ より 〚コ〛。"
                                 r"したがって，有意水準 $5\,\%$ で帰無仮説は 〚サ〛。"},
             {"t": "choices", "for": r"〚コ〛の解答群",
              "items": [r"小さい", r"大きい"], "cols": 2},
             {"t": "choices", "for": r"〚サ〛の解答群",
              "items": [r"棄却される", r"棄却されない"], "cols": 2},

             # ------------------------------ 正規分布表 ------------------------------
             {"t": "pagebreak"},
             {"t": "group", "blocks": [  # 表題・曲線図・表本体を1ページに保つ(改ページで割らない)
                 {"t": "html", "html": "<div style='text-align:center;font-family:\"Hiragino Kaku Gothic ProN\",sans-serif;"
                                       "font-size:13pt;font-weight:700;letter-spacing:.35em;margin:2mm 0 3mm'>"
                                       "正　規　分　布　表</div>"},
                 {"t": "fig", "svg": _NORMAL_FIG,
                  "caption": r"下の表は，上に示した標準正規分布の分布曲線において網かけ部分"
                             r"$P(0\leqq Z\leqq z_0)$ の面積の値をまとめたものである。"},
                 {"t": "table", "head": None, "rows": None,  # 実体は下で差し替える
                  "caption": r""},
             ]},
         ]},
     ]},

    # =======================================================================
    #  第6問 (選択問題) 配点16 — ベクトル
    # =======================================================================
    {"no": 6, "points": 16, "optional": "選択問題",
     "parts": [
         {"label": "", "blocks": [
             _SELECT_NOTE,
             {"t": "p", "text": r"平面上に，$\triangle \mathrm{ABC}$ と点 $\mathrm{M}$ がある。"},

             # ------------------------------ (1) ------------------------------
             {"t": "p", "text": r"<b>(1)</b>　次の等式を満たす点 $\mathrm{P}$ を考える。"},
             {"t": "m", "tex": r"\overrightarrow{\mathrm{MP}}"
                               r"=\overrightarrow{\mathrm{MA}}+2\overrightarrow{\mathrm{MB}}"
                               r"-\overrightarrow{\mathrm{MC}} \quad\cdots\cdots ①"},
             {"t": "p", "text": r"$3$ 点 $\mathrm{A},\ \mathrm{B},\ \mathrm{C}$ を図 $1$ の位置にとる。"
                                 r"ただし，図 $1$ における $\triangle \mathrm{ABC}$ は正三角形，"
                                 r"六角形 $\mathrm{DEFGCA}$ は正六角形であり，点 $\mathrm{B}$ は"
                                 r"正六角形の中心である。"},
             {"t": "fig", "svg": _HEX_FIG, "caption": r"図 1"},
             {"t": "p", "text": r"・$\mathrm{M}$ が $\mathrm{A}$ と一致するとき，$\mathrm{P}$ は 〚ア〛 と一致する。",
              "indent": True},
             {"t": "p", "text": r"・$\mathrm{M}$ が $\mathrm{D}$ と一致するとき，$\mathrm{P}$ は 〚イ〛 と一致する。",
              "indent": True},
             {"t": "choices", "for": r"〚ア〛，〚イ〛の解答群（同じものを繰り返し選んでもよい。）",
              "items": [r"$\mathrm{A}$", r"$\mathrm{B}$", r"$\mathrm{C}$", r"$\mathrm{D}$",
                        r"$\mathrm{E}$", r"$\mathrm{F}$", r"$\mathrm{G}$"], "cols": 7},

             {"t": "pagebreak"},

             # ------------------------------ (2) ------------------------------
             {"t": "p", "text": r"<b>(2)</b>　$a,\ b,\ c$ を実数とする。次の等式を満たす点 $\mathrm{P}$ を考える。"},
             {"t": "m", "tex": r"\overrightarrow{\mathrm{MP}}"
                               r"=a\overrightarrow{\mathrm{MA}}+b\overrightarrow{\mathrm{MB}}"
                               r"+c\overrightarrow{\mathrm{MC}} \quad\cdots\cdots ②"},
             {"t": "convo", "turns": [
                 {"sp": "花子", "text": r"①は $a=1,\ b=2,\ c=-1$ の場合だね。"
                                        r"(1)で考えた二つの場合では，$\mathrm{M}$ の位置によって"
                                        r"$\mathrm{P}$ の位置が異なるね。"},
                 {"sp": "太郎", "text": r"でも，$a=1,\ b=0,\ c=0$ の場合だと，②は"
                                        r" $\overrightarrow{\mathrm{MP}}=\overrightarrow{\mathrm{MA}}$ "
                                        r"となるから，$\mathrm{M}$ がどの位置にあっても，"
                                        r"$\mathrm{P}$ は $\mathrm{A}$ と一致するよ。"},
                 {"sp": "花子", "text": r"$\mathrm{P}$ の位置が変わらないのは，どのようなときかな。"}]},
             {"t": "p", "text": r"「$\mathrm{M}$ がどの位置にあっても，②を満たす $\mathrm{P}$ の位置が変わらない」"
                                 r"ための $a,\ b,\ c$ の条件を調べよう。",
              "cls": "center"},
             {"t": "p", "text": r"②の両辺を，$\mathrm{A}$ を始点とするベクトルを用いて表すと，左辺は"},
             {"t": "m", "tex": r"\overrightarrow{\mathrm{MP}}=〚ウ〛"},
             {"t": "p", "text": r"となり，右辺は"},
             {"t": "m", "tex": r"a\overrightarrow{\mathrm{MA}}+b\overrightarrow{\mathrm{MB}}"
                               r"+c\overrightarrow{\mathrm{MC}}"
                               r"=〚エ〛\,\overrightarrow{\mathrm{AB}}"
                               r"+〚オ〛\,\overrightarrow{\mathrm{AC}}"
                               r"+〚カ〛\,\overrightarrow{\mathrm{AM}}"},
             {"t": "p", "text": r"となる。したがって，②は"},
             {"t": "m", "tex": r"\overrightarrow{\mathrm{AP}}"
                               r"=〚キ〛\,\overrightarrow{\mathrm{AB}}"
                               r"+〚ク〛\,\overrightarrow{\mathrm{AC}}"
                               r"+〚ケ〛\,\overrightarrow{\mathrm{AM}}"},
             {"t": "p", "text": r"と変形できる。よって，$\mathrm{M}$ がどの位置にあっても②を満たす"
                                 r"$\mathrm{P}$ の位置が変わらないための<b>必要十分条件</b>は 〚コ〛 である。"},
             {"t": "choices", "for": r"〚ウ〛の解答群",
              "items": [r"$\overrightarrow{\mathrm{AP}}+\overrightarrow{\mathrm{AM}}$",
                        r"$-\overrightarrow{\mathrm{AP}}+\overrightarrow{\mathrm{AM}}$",
                        r"$\overrightarrow{\mathrm{AP}}-\overrightarrow{\mathrm{AM}}$",
                        r"$-\overrightarrow{\mathrm{AP}}-\overrightarrow{\mathrm{AM}}$"], "cols": 4},
             {"t": "choices", "for": r"〚エ〛〜〚ケ〛の解答群（同じものを繰り返し選んでもよい。）",
              "items": [r"$a$", r"$b$", r"$c$", r"$a+b+c$", r"$-a+b+c$",
                        r"$a-b+c$", r"$a+b-c$", r"$-a-b-c$",
                        r"$1+a+b+c$", r"$1-a-b-c$"], "cols": 5},
             {"t": "choices", "for": r"〚コ〛の解答群",
              "items": [r"$a=b$", r"$b=c$", r"$c=a$", r"$a+b-c=0$", r"$a-b+c=1$",
                        r"$-a+b+c=-1$", r"$a+b+c=0$", r"$a+b+c=1$", r"$a+b+c=-1$"], "cols": 3},

             {"t": "pagebreak"},

             # ------------------------------ (3) ------------------------------
             {"t": "p", "text": r"<b>(3)</b>　$a,\ b,\ c$ を，〚コ〛 を満たす実数とする。"
                                 r"様々な条件のもとで，②を満たす点 $\mathrm{P}$ が存在する範囲を調べよう。"},
             {"t": "p", "text": r"<b>(i)</b>　$a,\ b,\ c$ が，〚コ〛 と $a=\dfrac{1}{2}$ を満たすとき，"
                                 r"$\mathrm{P}$ が存在する範囲は 〚サ〛 である。ただし，$\triangle \mathrm{ABC}$ の"
                                 r"辺 $\mathrm{BC}$ の中点を $\mathrm{H}$，辺 $\mathrm{CA}$ の中点を $\mathrm{I}$，"
                                 r"辺 $\mathrm{AB}$ の中点を $\mathrm{J}$ とする。"},
             {"t": "fig", "svg": _TRI_FIG, "caption": r"参考図"},
             {"t": "choices", "for": r"〚サ〛の解答群",
              "items": [r"直線 $\mathrm{AH}$", r"直線 $\mathrm{BI}$", r"直線 $\mathrm{CJ}$",
                        r"直線 $\mathrm{HI}$", r"直線 $\mathrm{IJ}$", r"直線 $\mathrm{JH}$"], "cols": 3},

             {"t": "p", "text": r"<b>(ii)</b>　$a,\ b,\ c$ が，〚コ〛 と $c<0$ を満たすとき，"
                                 r"$\mathrm{P}$ が存在する範囲を図示すると，〚シ〛 の灰色部分となる。"
                                 r"ただし，<b>境界線を含まない</b>。"},
             {"t": "p", "text": r"〚シ〛については，最も適当なものを，次の<b>⓪</b>〜<b>⑤</b>のうちから一つ選べ。"
                                 r"なお，各図では直線 $\mathrm{AB}$，直線 $\mathrm{BC}$，直線 $\mathrm{CA}$ を"
                                 r"それぞれ両側に延長して示している。"},
             {"t": "html", "html": _REGION6_GRID},
         ]},
     ]},

    # =======================================================================
    #  第7問 (選択問題) 配点16 — 平面上の曲線と複素数平面
    # =======================================================================
    {"no": 7, "points": 16, "optional": "選択問題",
     "parts": [
         {"label": "", "blocks": [
             _SELECT_NOTE,
             {"t": "p", "text": r"$z$ を $0$ でない複素数とし，$w=z+\dfrac{1}{z}$ とする。また，$r$ を正の実数とし，"
                                 r"複素数平面上で，原点 $\mathrm{O}$ を中心とする半径 $r$ の円を $C$ とする。"},

             # ------------------------------ (1) ------------------------------
             {"t": "p", "text": r"<b>(1)</b>　$z=1+\sqrt{3}\,i$ のとき，$|z|=〔ア〕$ であり"},
             {"t": "m", "tex": r"w=\dfrac{イ}{ウ}+\dfrac{エ\sqrt{オ}}{カ}\,i"},
             {"t": "p", "text": r"である。"},

             # ------------------------------ (2) ------------------------------
             {"t": "p", "text": r"<b>(2)</b>　$z$ が $C$ 上を動くとき，$w$ が複素数平面上で描く図形を考える。"
                                 r"実数 $\theta$ を $z$ の偏角とし，極形式を用いて"
                                 r" $z=r(\cos\theta+i\sin\theta)$ と表す。"},
             {"t": "p", "text": r"<b>(i)</b>　$w=z+\dfrac{1}{z}$ を $r,\ \theta$ を用いて表すと"},
             {"t": "m", "tex": r"w=〚キ〛+i\,〚ク〛 \quad\cdots\cdots ①"},
             {"t": "p", "text": r"である。したがって，$\theta$ の値によらず 〚ク〛$=0$ となるような"
                                 r" $r$ の値は $〔ケ〕$ である。"},
             {"t": "choices", "for": r"〚キ〛，〚ク〛の解答群（同じものを繰り返し選んでもよい。）",
              "items": [r"$2r\cos\theta$", r"$2r\sin\theta$",
                        r"$(r+1)\cos\theta$", r"$(r+1)\sin\theta$",
                        r"$(r-1)\cos\theta$", r"$(r-1)\sin\theta$",
                        r"$\left(r+\dfrac{1}{r}\right)\cos\theta$",
                        r"$\left(r+\dfrac{1}{r}\right)\sin\theta$",
                        r"$\left(r-\dfrac{1}{r}\right)\cos\theta$",
                        r"$\left(r-\dfrac{1}{r}\right)\sin\theta$"], "cols": 2},

             {"t": "p", "text": r"<b>(ii)</b>　$r=〔ケ〕$ とする。$z$ が $C$ 上を動くとき，$w$ が描く図形は"
                                 r" 〚コ〛 である。"},
             {"t": "p", "text": r"〚コ〛については，最も適当なものを，次の<b>⓪</b>〜<b>⑤</b>のうちから一つ選べ。"},
             {"t": "html", "html": _KO6_GRID},

             {"t": "pagebreak"},

             {"t": "p", "text": r"<b>(iii)</b>　$r\neq 〔ケ〕$ とする。$x,\ y$ を実数として $w=x+yi$ とおくと，①から"},
             {"t": "m", "tex": r"x=〚キ〛,\qquad y=〚ク〛 \quad\cdots\cdots ②"},
             {"t": "p", "text": r"が成り立つ。②の二つの式から $\theta$ を消去すると，$x,\ y$ は 〚サ〛 を満たし，"
                                 r"$z$ が $C$ 上を動くとき，$w=x+yi$ は 〚サ〛 の表す図形を描く。"},
             {"t": "choices", "for": r"〚サ〛の解答群",
              "items": [r"$\dfrac{x^2}{r^2}+\dfrac{y^2}{r^2}=1$",
                        r"$\dfrac{x^2}{r^2}-\dfrac{y^2}{r^2}=1$",
                        r"$\dfrac{x^2}{\left(r+\frac{1}{r}\right)^2}+\dfrac{y^2}{\left(r-\frac{1}{r}\right)^2}=1$",
                        r"$\dfrac{x^2}{\left(r+\frac{1}{r}\right)^2}-\dfrac{y^2}{\left(r-\frac{1}{r}\right)^2}=1$",
                        r"$\dfrac{x^2}{\left(r-\frac{1}{r}\right)^2}+\dfrac{y^2}{\left(r+\frac{1}{r}\right)^2}=1$",
                        r"$\dfrac{x^2}{\left(r-\frac{1}{r}\right)^2}-\dfrac{y^2}{\left(r+\frac{1}{r}\right)^2}=1$"],
              "cols": 1},

             {"t": "pagebreak"},

             # ------------------------------ (3) ------------------------------
             {"t": "p", "text": r"<b>(3)</b>　$r\neq 〔ケ〕$ とする。$z$ が $C$ 上を動くとき，"
                                 r"$w^2$ が描く図形を考えよう。"},
             {"t": "p", "text": r"<b>(i)</b>　$w^2$ を $z$ を用いて表すと，$w^2=〚シ〛$ である。"},
             {"t": "choices", "for": r"〚シ〛の解答群",
              "items": [r"$z^2+\dfrac{1}{z^2}$", r"$z^2+\dfrac{1}{z^2}+1$",
                        r"$z^2+\dfrac{1}{z^2}-1$", r"$z^2+\dfrac{1}{z^2}+2$",
                        r"$z^2+\dfrac{1}{z^2}-2$", r"$z^2+\dfrac{1}{z^2}+2i$"], "cols": 3},
             {"t": "p", "text": r"<b>(ii)</b>　$z$ が $C$ 上を動くとき，$z^2+\dfrac{1}{z^2}$ が描く図形の方程式を考える。"
                                 r"このとき，$z^2$ は原点 $\mathrm{O}$ を中心とする半径 $r^2$ の円を描く。"
                                 r"このことから，$X,\ Y$ を実数として $z^2+\dfrac{1}{z^2}=X+Yi$ とおくと，"
                                 r"$X,\ Y$ は 〚ス〛 を満たす。"},
             {"t": "choices", "for": r"〚ス〛の解答群",
              "items": [r"$\dfrac{X}{r^2+\frac{1}{r^2}}+\dfrac{Y}{r^2-\frac{1}{r^2}}=1$",
                        r"$\dfrac{X^2}{r^4}+\dfrac{Y^2}{r^4}=1$",
                        r"$\dfrac{X^2}{\left(r^2+\frac{1}{r^2}\right)^2}+\dfrac{Y^2}{\left(r^2-\frac{1}{r^2}\right)^2}=1$",
                        r"$\dfrac{X^2}{\left(r^2+\frac{1}{r^2}\right)^2}-\dfrac{Y^2}{\left(r^2-\frac{1}{r^2}\right)^2}=1$",
                        r"$\dfrac{X^2}{\left(r^2-\frac{1}{r^2}\right)^2}+\dfrac{Y^2}{\left(r^2+\frac{1}{r^2}\right)^2}=1$",
                        r"$\dfrac{X^2}{\left(r^2-\frac{1}{r^2}\right)^2}-\dfrac{Y^2}{\left(r^2+\frac{1}{r^2}\right)^2}=1$"],
              "cols": 1},
             {"t": "p", "text": r"以上を踏まえると，$w^2$ が描く図形は 〚セ〛 であることがわかる。"},
             {"t": "p", "text": r"〚セ〛については，最も適当なものを，次の<b>⓪</b>〜<b>⑦</b>のうちから一つ選べ。"},
             {"t": "html", "html": _SE8_GRID},
         ]},
     ]},
]


# ---------------------------------------------------------------------------
#  正規分布表 (z=0.00〜3.59) を erf で生成し、第5問末尾の table ブロックへ差し込む
# ---------------------------------------------------------------------------
def _build_normal_table():
    import math

    def phi(z):
        return 0.5 * math.erf(z / math.sqrt(2))

    head = [r"$z_0$"] + [f"{c/100:.2f}" for c in range(10)]
    rows = []
    z = 0
    while z <= 35:                       # z0 = 0.0 .. 3.5
        z0 = z / 10
        cells = [f"<b>{z0:.1f}</b>"]
        for c in range(10):
            cells.append(f"{phi(z0 + c/100):.4f}")
        rows.append(cells)
        z += 1
    return {"t": "table", "head": head, "rows": rows, "cls": "normtbl",
            "caption": r"標準正規分布表　$P(0\leqq Z\leqq z_0)$"}


# 第5問末尾のプレースホルダ table を本物に差し替える(group内も走査)
def _fill_norm_table(blocks):
    for _i, _b in enumerate(blocks):
        if _b.get("t") == "table" and _b.get("head") is None:
            blocks[_i] = _build_normal_table()
            return True
        if _b.get("t") == "group" and _fill_norm_table(_b["blocks"]):
            return True
    return False


for _sec in SECTIONS:
    if _sec["no"] == 5:
        _fill_norm_table(_sec["parts"][0]["blocks"])


# ===========================================================================
#  ANS_SECTIONS
# ===========================================================================
ANS_SECTIONS = [

    # ---------------------------- 第5問 ----------------------------
    {"section": 5,
     "slots": {
         "ア": "①",                                   # Y=(X-180)/40
         "イ": "①",                                   # P(X>=210)=0.23
         "ウ": "⓪",                                   # E(Wi)=p
         "エ": "③",                                   # V(Wi)=p(1-p)
         "オ": "⑦",                                   # V(W̄)=p(1-p)/n
         "カ": "③",                                   # σ1=√3/75 (選択肢③に配置)
         "キ": "③",                                   # 裾 0.0418 (選択肢③に配置)
         "ク": "①",                                   # 小さいから棄却される
         "ケ": "⓪",                                   # 高いと判断できる
         "コ": "①",                                   # 11.12% は大きい
         "サ": "①",                                   # 棄却されない
     },
     "kai": [
         {"heading": "第5問　統計的な推測（母比率の仮説検定）", "blocks": [
             {"t": "p", "text": r"<b>(1)</b>　$X\sim N(180,\ 40^2)$ の標準化は，"
                                r"平均を引いて標準偏差で割る。標準偏差は $\sqrt{40^2}=40$ だから"},
             {"t": "m", "tex": r"Y=\dfrac{X-180}{40}\quad(\text{〚ア〛}=①)"},
             {"t": "p", "text": r"誤答の切り方：分母を $\sqrt{40}$ や $40^2$ にするのは，"
                                r"標準偏差を $40$ と正しく読めていない。分子を $X-210$ とするのは"
                                r"「合格点を引く」混同（引くのは<b>平均</b>）。"},
             {"t": "p", "text": r"$210$ 点に対応する $z$ の値は"},
             {"t": "m", "tex": r"z=\dfrac{210-180}{40}=\dfrac{30}{40}=0.75"},
             {"t": "p", "text": r"正規分布表より $P(0\leqq Z\leqq 0.75)=0.2734$。よって"},
             {"t": "m", "tex": r"P(X\geqq 210)=P(Z\geqq 0.75)=0.5-0.2734=0.2266\approx 0.23"},
             {"t": "p", "text": r"〚イ〛$=①$。$0.16$ は $z$ 値そのもの，$0.77$ は $1-0.23$ の誤り。"},

             {"t": "p", "text": r"<b>(2)(i)</b>　$W_i$ は $0,\ 1$ の二値（ベルヌーイ分布）。表 $1$ より"},
             {"t": "m", "tex": r"E(W_i)=0\cdot(1-p)+1\cdot p=p\quad(\text{〚ウ〛}=⓪)"},
             {"t": "p", "text": r"分散は与えられた定義式に $E(W_i)=p$ を代入して"},
             {"t": "m", "tex": r"V(W_i)=(0-p)^2(1-p)+(1-p)^2\,p=p^2(1-p)+p(1-p)^2"},
             {"t": "m", "tex": r"\qquad\ =p(1-p)\{p+(1-p)\}=p(1-p)\quad(\text{〚エ〛}=③)"},

             {"t": "p", "text": r"<b>(ii)</b>　$\overline{W}$ は独立な $W_i$ の平均だから"
                                r" $E(\overline{W})=p$，"},
             {"t": "m", "tex": r"V(\overline{W})=\dfrac{V(W_i)}{n}=\dfrac{p(1-p)}{n}\quad(\text{〚オ〛}=⑦)"},
             {"t": "p", "text": r"（$\sqrt{\ }$ が付くのは<b>標準偏差</b>で，分散にはならない。④⑤は $\sqrt{\ }$ の付け方の誤り。）"},
             {"t": "p", "text": r"帰無仮説 $p=0.2$ のもとで，$n=300$ のときの標準偏差は"},
             {"t": "m", "tex": r"\sqrt{\dfrac{0.2\times 0.8}{300}}=\sqrt{\dfrac{0.16}{300}}"
                               r"=\sqrt{\dfrac{16}{30000}}=\dfrac{4}{100\sqrt{3}}"
                               r"=\dfrac{4}{100\sqrt3}\cdot\dfrac{\sqrt3}{\sqrt3}=\dfrac{\sqrt3}{75}"},
             {"t": "p", "text": r"〚カ〛$=①$。標本比率は $\dfrac{72}{300}=0.24$ だから，"
                                r"帰無仮説のもとでの $z$ 値は"},
             {"t": "m", "tex": r"z_1=\dfrac{0.24-0.2}{\sqrt3/75}=\dfrac{0.04\times 75}{\sqrt3}"
                               r"=\dfrac{3}{\sqrt3}=\sqrt3\approx 1.73"},
             {"t": "p", "text": r"$\sqrt3=1.73$ を用いる。正規分布表より $P(0\leqq Z\leqq 1.73)=0.4582$ だから"},
             {"t": "m", "tex": r"P(\overline{W}\geqq 0.24)=0.5-0.4582=0.0418\quad(\text{〚キ〛}=①)"},
             {"t": "p", "text": r"これはパーセント表示で $4.18\,\%$。有意水準 $5\,\%$ より<b>小さい</b>ので，"
                                r"帰無仮説は<b>棄却される</b>（〚ク〛$=①$）。"
                                r"よって今年の合格率は $0.2$ より<b>高いと判断できる</b>（〚ケ〛$=⓪$）。"
                                r"（$0.4582$ は裾でなく表値そのもの，$0.3888$ は $z=1.22$ の表値で別問題の混同。）"},

             {"t": "p", "text": r"<b>(3)</b>　太郎さんの疑問「比率が同じ $0.24$ なら結果も同じか」を検証する。"
                                r"$n=150$ でも標本比率は $\dfrac{36}{150}=0.24$ で同じだが，標準偏差が変わる。"},
             {"t": "m", "tex": r"\sqrt{\dfrac{0.2\times 0.8}{150}}=\sqrt{\dfrac{0.16}{150}}"
                               r"=\dfrac{4}{100}\cdot\dfrac{1}{\sqrt{15}}\cdots"
                               r"=\dfrac{\sqrt6}{75}\quad\left(\because \dfrac{0.16}{150}=\dfrac{6}{5625}\right)"},
             {"t": "p", "text": r"帰無仮説のもとでの $z$ 値は"},
             {"t": "m", "tex": r"z_2=\dfrac{0.24-0.2}{\sqrt6/75}=\dfrac{0.04\times 75}{\sqrt6}"
                               r"=\dfrac{3}{\sqrt6}=\dfrac{\sqrt6}{2}=\dfrac{2.45}{2}\approx 1.22"},
             {"t": "p", "text": r"正規分布表より $P(0\leqq Z\leqq 1.22)=0.3888$ だから"},
             {"t": "m", "tex": r"P(\overline{W}\geqq 0.24)=0.5-0.3888=0.1112\ \Rightarrow\ 11.12\,\%"},
             {"t": "p", "text": r"$11.12\,\%$ は有意水準 $5\,\%$ より<b>大きい</b>（〚コ〛$=①$）ので，"
                                r"帰無仮説は<b>棄却されない</b>（〚サ〛$=①$）。"
                                r"標本比率が同じ $0.24$ でも，標本の大きさが小さいと標準偏差が大きくなり，"
                                r"$z$ 値が棄却域に届かない——これが本問の学びの核心。"},
         ]},
     ]},

    # ---------------------------- 第6問 ----------------------------
    {"section": 6,
     "slots": {
         "ア": "⑤",                                   # M=A → P=F (2B-C=Cの中心対称点)
         "イ": "①",                                   # M=D → P=B (=六角形の中心)
         "ウ": "②",                                   # MP = AP - AM
         "エ": "①", "オ": "②", "カ": "⑦",             # b, c, -a-b-c
         "キ": "①", "ク": "②", "ケ": "⑨",             # b, c, 1-a-b-c
         "コ": "⑦",                                   # a+b+c=1
         "サ": "④",                                   # 直線IJ
         "シ": "③",                                   # ABのC反対側の半平面
     },
     "kai": [
         {"heading": "第6問　ベクトル（一次結合とPの不変条件・存在範囲）", "blocks": [
             {"t": "p", "text": r"<b>(1)</b>　$(a,b,c)=(1,2,-1)$。始点を $\mathrm{M}$ にそろえて"
                                r"位置ベクトル $\vec p=\overrightarrow{\mathrm{OP}}$ 等で計算する。"
                                r"$\overrightarrow{\mathrm{MP}}=\overrightarrow{\mathrm{MA}}"
                                r"+2\overrightarrow{\mathrm{MB}}-\overrightarrow{\mathrm{MC}}$ より"},
             {"t": "m", "tex": r"\vec p=\vec a+2\vec b-\vec c\qquad"
                               r"(\vec a=\overrightarrow{\mathrm{OA}}\ \text{等})"},
             {"t": "p", "text": r"正六角形 $\mathrm{DEFGCA}$ の中心が $\mathrm{B}$ なので，"
                                r"$\mathrm{B}$ を原点にとると $\vec b=\vec 0$ で，各頂点は $\mathrm{B}$ からの"
                                r"単位ベクトルの整数結合で表せる。中心 $\mathrm{B}$ に関して "
                                r"$\mathrm{A}$ と $\mathrm{G}$，$\mathrm{C}$ と $\mathrm{F}$，"
                                r"$\mathrm{D}$ と $\mathrm{E}$ が対称。"},
             {"t": "p", "text": r"$\mathrm{M}=\mathrm{A}$ のとき "
                                r"$\overrightarrow{\mathrm{AP}}=\overrightarrow{\mathrm{AA}}"
                                r"+2\overrightarrow{\mathrm{AB}}-\overrightarrow{\mathrm{AC}}"
                                r"=2\overrightarrow{\mathrm{AB}}-\overrightarrow{\mathrm{AC}}$，すなわち"
                                r" $\mathrm{P}=2\mathrm{B}-\mathrm{C}$（$\mathrm{C}$ の中心 $\mathrm{B}$ に関する"
                                r"対称点）。$\mathrm{C}$ と $\mathrm{F}$ が対称だから $\mathrm{P}=\mathrm{F}$。"
                                r"よって 〚ア〛$=⑤$。"},
             {"t": "p", "text": r"$\mathrm{M}=\mathrm{D}$ のとき同様に "
                                r"$\mathrm{P}=\mathrm{A}+2\mathrm{B}-\mathrm{C}-\mathrm{D}$ を計算すると "
                                r"$\mathrm{P}=\mathrm{B}$（六角形の中心）。よって 〚イ〛$=①$。"
                                r"（$\mathrm{M}$ の位置で $\mathrm{P}$ が変わる＝(2)の伏線。）"},

             {"t": "p", "text": r"<b>(2)</b>　$\overrightarrow{\mathrm{MX}}"
                                r"=\overrightarrow{\mathrm{AX}}-\overrightarrow{\mathrm{AM}}$ を使う。左辺は"},
             {"t": "m", "tex": r"\overrightarrow{\mathrm{MP}}"
                               r"=\overrightarrow{\mathrm{AP}}-\overrightarrow{\mathrm{AM}}"
                               r"\quad(\text{〚ウ〛}=②)"},
             {"t": "p", "text": r"右辺は $\overrightarrow{\mathrm{MA}}=-\overrightarrow{\mathrm{AM}}$，"
                                r"$\overrightarrow{\mathrm{MB}}=\overrightarrow{\mathrm{AB}}"
                                r"-\overrightarrow{\mathrm{AM}}$，"
                                r"$\overrightarrow{\mathrm{MC}}=\overrightarrow{\mathrm{AC}}"
                                r"-\overrightarrow{\mathrm{AM}}$ を代入して整理すると"},
             {"t": "m", "tex": r"a\overrightarrow{\mathrm{MA}}+b\overrightarrow{\mathrm{MB}}"
                               r"+c\overrightarrow{\mathrm{MC}}"
                               r"=b\,\overrightarrow{\mathrm{AB}}+c\,\overrightarrow{\mathrm{AC}}"
                               r"+(-a-b-c)\overrightarrow{\mathrm{AM}}"},
             {"t": "p", "text": r"よって 〚エ〛$=①(b)$，〚オ〛$=②(c)$，〚カ〛$=⑦(-a-b-c)$。"
                                r"②の左辺 $=$ 右辺で 〚ウ〛 を移項すると"},
             {"t": "m", "tex": r"\overrightarrow{\mathrm{AP}}"
                               r"=b\,\overrightarrow{\mathrm{AB}}+c\,\overrightarrow{\mathrm{AC}}"
                               r"+(1-a-b-c)\overrightarrow{\mathrm{AM}}"},
             {"t": "p", "text": r"よって 〚キ〛$=①(b)$，〚ク〛$=②(c)$，〚ケ〛$=⑨(1-a-b-c)$。"},
             {"t": "p", "text": r"$\mathrm{P}$ の位置が $\mathrm{M}$ に依存しない"
                                r"$\iff \overrightarrow{\mathrm{AM}}$ の係数が $0$"
                                r"$\iff 1-a-b-c=0 \iff a+b+c=1$。よって 〚コ〛$=⑦$。"
                                r"（$a+b+c=0$⑥や向きの違う等式は係数を $0$ にできず不適。）"},

             {"t": "p", "text": r"<b>(3)(i)</b>　$a+b+c=1$ のとき $\overrightarrow{\mathrm{AP}}"
                                r"=b\,\overrightarrow{\mathrm{AB}}+c\,\overrightarrow{\mathrm{AC}}$"
                                r"（$\mathrm{M}$ に依らない＝重心座標 $(a,b,c)$ の点）。"
                                r"$a=\dfrac12$ 固定・$b+c=\dfrac12$ で $b$ を動かすと，$\mathrm{P}$ は"
                                r"$\mathrm{AB},\mathrm{AC}$ の中点 $\mathrm{J},\mathrm{I}$ を通る直線をなぞる。"},
             {"t": "m", "tex": r"a=\tfrac12,\ b=\tfrac12,\ c=0\ \Rightarrow\ \mathrm{P}=\mathrm{J};"
                               r"\quad a=\tfrac12,\ b=0,\ c=\tfrac12\ \Rightarrow\ \mathrm{P}=\mathrm{I}"},
             {"t": "p", "text": r"よって $\mathrm{P}$ の軌跡は<b>直線 $\mathrm{IJ}$</b>（〚サ〛$=④$）。"
                                r"中点連結線 $\mathrm{IJ}$ は $\mathrm{BC}$ に平行。"
                                r"頂点–対辺中点線（$\mathrm{AH}$ 等）や他の中点連結線は $2$ 点を通らず不適。"},
             {"t": "p", "text": r"<b>(ii)</b>　$a+b+c=1$（重心座標）で $c<0$ の点全体を考える。"
                                r"$c$ は頂点 $\mathrm{C}$ 側の重み。$c=0$ は直線 $\mathrm{AB}$ 上，$c>0$ が"
                                r"$\mathrm{C}$ 側，$c<0$ は<b>直線 $\mathrm{AB}$ に関して $\mathrm{C}$ と反対側</b>の"
                                r"開半平面。よって 〚シ〛$=③$。境界（$c=0$＝直線 $\mathrm{AB}$）は含まない。"},
             {"t": "p", "text": r"誤答の切り方：①②は $\angle\mathrm{C}$ の内角領域や対頂角で "
                                r"$c<0$ だけの条件より狭い／広い。④は上側にさらに制限をかけすぎ，"
                                r"⑤は $\mathrm{C}$ と<b>同じ</b>側で符号が逆。"},
         ]},
     ]},

    # ---------------------------- 第7問 ----------------------------
    {"section": 7,
     "slots": {
         "ア": "2",                                   # |z|=2
         "イ": "5", "ウ": "4",                        # 実部 5/4
         "エ": "3", "オ": "3", "カ": "4",             # 虚部 (3√3)/4
         "キ": "⑥", "ク": "⑨",                        # (r+1/r)cosθ, (r-1/r)sinθ
         "ケ": "1",                                   # r=1
         "コ": "①",                                   # 実軸[-2,2]
         "サ": "②",                                   # 楕円
         "シ": "③",                                   # z²+1/z²+2
         "ス": "②",                                   # X²/(r²+1/r²)²+Y²/(r²-1/r²)²=1
         "セ": "③",                                   # 横長楕円・中心(2,0)
     },
     "kai": [
         {"heading": "第7問　平面上の曲線と複素数平面（$w=z+1/z$ の像）", "blocks": [
             {"t": "p", "text": r"<b>(1)</b>　$z=1+\sqrt3\,i$ より"},
             {"t": "m", "tex": r"|z|=\sqrt{1^2+(\sqrt3)^2}=\sqrt4=2\quad(\text{ア}=2)"},
             {"t": "p", "text": r"$\dfrac1z=\dfrac{\overline z}{|z|^2}=\dfrac{1-\sqrt3\,i}{4}$ だから"},
             {"t": "m", "tex": r"w=z+\dfrac1z=(1+\sqrt3\,i)+\dfrac{1-\sqrt3\,i}{4}"
                               r"=\dfrac{4+\sqrt3\cdot4\,i+1-\sqrt3\,i}{4}"},
             {"t": "m", "tex": r"\ =\dfrac{5+3\sqrt3\,i}{4}=\dfrac{3\sqrt3}{4}\,i+\dfrac54"},
             {"t": "p", "text": r"よって実部 $\dfrac54$（イ$=5$，ウ$=4$），"
                                r"虚部 $\dfrac{3\sqrt3}{4}$（エ$=3$，オ$=3$，カ$=4$）。"},

             {"t": "p", "text": r"<b>(2)(i)</b>　$z=r(\cos\theta+i\sin\theta)$ のとき，"
                                r"$\dfrac1z=\dfrac1r(\cos\theta-i\sin\theta)$（$|z|=r$，偏角 $-\theta$）。"
                                r"よって"},
             {"t": "m", "tex": r"w=z+\dfrac1z=\left(r+\dfrac1r\right)\cos\theta"
                               r"+i\left(r-\dfrac1r\right)\sin\theta"},
             {"t": "p", "text": r"〚キ〛$=⑥$，〚ク〛$=⑨$。$\theta$ によらず虚部 $=0$ となるのは"
                                r"$r-\dfrac1r=0$，すなわち $r^2=1$。$r>0$ より $r=1$（ケ$=1$）。"},
             {"t": "p", "text": r"<b>(ii)</b>　$r=1$ のとき $w=\left(1+1\right)\cos\theta=2\cos\theta$。"
                                r"$\cos\theta\in[-1,1]$ より $w$ は実軸上の線分 $[-2,\ 2]$ を動く"
                                r"（虚部は常に $0$）。よって 〚コ〛$=①$。"
                                r"（⓪の $[-1,1]$ は係数 $2$ の見落とし，②③の虚軸は実部・虚部の取り違え，"
                                r"④⑤の山型は $r\neq1$ の楕円との混同。）"},

             {"t": "p", "text": r"<b>(iii)</b>　$r\neq1$ のとき "
                                r"$x=\left(r+\dfrac1r\right)\cos\theta,\ "
                                r"y=\left(r-\dfrac1r\right)\sin\theta$。"},
             {"t": "m", "tex": r"\cos\theta=\dfrac{x}{r+\frac1r},\quad "
                               r"\sin\theta=\dfrac{y}{r-\frac1r}"},
             {"t": "p", "text": r"$\cos^2\theta+\sin^2\theta=1$ に代入して $\theta$ を消去すると"},
             {"t": "m", "tex": r"\dfrac{x^2}{\left(r+\frac1r\right)^2}"
                               r"+\dfrac{y^2}{\left(r-\frac1r\right)^2}=1\quad(\text{〚サ〛}=②)"},
             {"t": "p", "text": r"これは楕円。$r+\dfrac1r>\left|r-\dfrac1r\right|$（相加相乗等）なので"
                                r"実軸方向に長い横長の楕円。①③⑤の $-$（双曲線型）や分母入替④は不適。"},

             {"t": "p", "text": r"<b>(3)(i)</b>　$w^2=\left(z+\dfrac1z\right)^2"
                                r"=z^2+2\cdot z\cdot\dfrac1z+\dfrac1{z^2}"
                                r"=z^2+\dfrac1{z^2}+2$。よって 〚シ〛$=③$。"
                                r"（中央項 $2z\cdot\dfrac1z=2$ を落とすと⓪，符号違いで④になる。）"},
             {"t": "p", "text": r"<b>(ii)</b>　$z^2$ は半径 $r^2$ の円を描く（偏角 $2\theta$）。"
                                r"$\dfrac1{z^2}$ は半径 $\dfrac1{r^2}$，偏角 $-2\theta$。よって"},
             {"t": "m", "tex": r"z^2+\dfrac1{z^2}=\left(r^2+\dfrac1{r^2}\right)\cos2\theta"
                               r"+i\left(r^2-\dfrac1{r^2}\right)\sin2\theta=X+Yi"},
             {"t": "p", "text": r"(iii)と同様に $2\theta$ を消去して"},
             {"t": "m", "tex": r"\dfrac{X^2}{\left(r^2+\frac1{r^2}\right)^2}"
                               r"+\dfrac{Y^2}{\left(r^2-\frac1{r^2}\right)^2}=1\quad(\text{〚ス〛}=②)"},
             {"t": "p", "text": r"⓪は $1$ 乗の直線型で不適，①は円（半径同じ）で不適。"},
             {"t": "p", "text": r"<b>最後に</b> $w^2=\left(z^2+\dfrac1{z^2}\right)+2=(X+2)+Yi$ だから，"
                                r"$w^2$ が描く図形は 〚ス〛 の楕円を<b>実軸方向に $+2$ 平行移動</b>したもの。"
                                r"中心 $(2,\ 0)$ の横長楕円になる。よって 〚セ〛$=③$。"},
             {"t": "p", "text": r"誤答の切り方：中心を $(-2,0)$ とする⓪②④は平行移動の向き違い，"
                                r"縦長⓪①⑥は長短軸の取り違え（$r^2+\frac1{r^2}>r^2-\frac1{r^2}$ で横長），"
                                r"⑥⑦は平行移動を忘れて中心 $\mathrm{O}$ のまま。"},
         ]},
     ]},
]
