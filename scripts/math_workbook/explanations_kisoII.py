# -*- coding: utf-8 -*-
"""数学II 基礎徹底問題集の「この単元のキモ」オーバーレイ（POINTS のみ）。
問題ごとの詳細解説は content_kisoII.py の explanation を使う（EXPL は空）。"""

EXPL = {}

POINTS = {
    1: r"""▶ 三角関数はまず【弧度法】に慣れる。度数法のままでは微分・積分に進めない。
① $180^\circ=\pi$。度 $\to$ ラジアンは $\times\dfrac{\pi}{180}$、逆は $\times\dfrac{180}{\pi}$。
② 扇形は $\ell=r\theta$、$S=\dfrac12 r\ell=\dfrac12 r^2\theta$（$\theta$ はラジアン）。
　度数法のまま代入すると答えが合わない。
③ 値は【単位円】で読む。$\cos$ は $x$ 座標、$\sin$ は $y$ 座標。符号は象限で決まる。
★$90^\circ$ をこえたら「$\pi-\theta$」「$\pi+\theta$」「$2\pi-\theta$」のどれかに直す。
　$\sin$ は $y$、$\cos$ は $x$ の符号を見れば、公式を暗記しなくても符号が決まる。
★方程式は範囲内の解を【全部】書く。$0\leq\theta<2\pi$ なら普通は2つある。
★加法定理 $\sin(\alpha\pm\beta)=\sin\alpha\cos\beta\pm\cos\alpha\sin\beta$、
　$\cos(\alpha\pm\beta)=\cos\alpha\cos\beta\mp\sin\alpha\sin\beta$（$\cos$ は符号が逆になる）。
　2倍角は $\alpha=\beta$ とした特別な場合。別に覚えるものではない。""",

    2: r"""▶ 加法定理は「$\sin$ はそのまま、$\cos$ は符号が逆」。この2つだけ覚える。
① $\sin(\alpha\pm\beta)=\sin\alpha\cos\beta\pm\cos\alpha\sin\beta$
② $\cos(\alpha\pm\beta)=\cos\alpha\cos\beta\mp\sin\alpha\sin\beta$（複号が逆になる）
③ 2倍角は $\alpha=\beta$ とした特別な場合。$\sin2\theta=2\sin\theta\cos\theta$、
　$\cos2\theta=\cos^2\theta-\sin^2\theta=1-2\sin^2\theta=2\cos^2\theta-1$（3通りに書ける）。
★$15^\circ$ や $75^\circ$ は $45^\circ\pm30^\circ$ に分けると加法定理で値が出せる。
★★合成 $a\sin\theta+b\cos\theta=r\sin(\theta+\alpha)$、$r=\sqrt{a^2+b^2}$。
　$\cos\alpha=\dfrac{a}{r}$, $\sin\alpha=\dfrac{b}{r}$ から $\alpha$ を決める。
　合成する目的は「$\sin$ 1つにまとめて最大最小を読む」こと。最大は $r$、最小は $-r$。
★$y=a\sin(b\theta)$ は振幅 $|a|$、周期 $\dfrac{2\pi}{|b|}$。$a$ が縦、$b$ が横の伸縮。
★不等式は必ず単位円をかく。$\sin\theta>\dfrac12$ なら $y$ 座標が $\dfrac12$ より上の弧。""",

    3: r"""▶ 指数は「法則3つ」だけ。それ以外は全部この組み合わせ。
① $a^m a^n=a^{m+n}$（かけ算は指数を足す）
② $\dfrac{a^m}{a^n}=a^{m-n}$（わり算は引く）
③ $(a^m)^n=a^{mn}$（累乗の累乗はかける）
★拡張の定義：$a^0=1$、$a^{-n}=\dfrac{1}{a^n}$、$a^{\frac{m}{n}}=\sqrt[n]{a^m}$。
　累乗根が出たら【分数指数に直す】と、上の3法則がそのまま使える。
★大小比較は「底をそろえて指数を比べる」。$\sqrt2,\ \sqrt[3]4,\ \sqrt[6]{32}$ はすべて $2$ の累乗。
★指数方程式は両辺の底をそろえる。$4^x$ が出たら $(2^x)^2$ と見て $t=2^x$ と置く。
　置きかえたら【$t>0$】の条件を必ず書く。ここを落とすと余計な解を拾う。""",

    4: r"""▶ 対数は定義に毎回もどる。$\log_a M=p \iff a^p=M$（「$a$ を何乗すると $M$ か」）。
① $\log_a MN=\log_a M+\log_a N$（かけ算 $\to$ 足し算）
② $\log_a \dfrac{M}{N}=\log_a M-\log_a N$（わり算 $\to$ 引き算）
③ $\log_a M^k=k\log_a M$（累乗 $\to$ 前に出す）
★底の変換 $\log_a b=\dfrac{\log_c b}{\log_c a}$。底がそろっていないときは必ずこれでそろえる。
★$\log_a 1=0$、$\log_a a=1$。
　【底が $1$ より大きいとき】真数が $1$ より小さいと対数は負になる。
　底が $0<a<1$ なら逆に正になる（$\log_{1/2}\frac14=2$）。底の大きさで向きが変わる。
★★対数方程式・不等式は【真数条件】が命。$\log_2 x+\log_2(x-2)=3$ なら
　$x>0$ かつ $x-2>0$、つまり $x>2$。まとめてから解いて、最後に条件で【ふるい落とす】。
　この確認を飛ばすと、方程式としては正しいのに答えが間違う。""",

    5: r"""▶ 微分は「接線の傾き」。公式は $(x^n)'=nx^{n-1}$、定数は $0$、これだけ。
① $f'(a)$ ＝ $x=a$ における接線の傾き。定義は $\displaystyle\lim_{h\to0}\dfrac{f(a+h)-f(a)}{h}$。
② 点 $(a,\,f(a))$ における接線は $y-f(a)=f'(a)(x-a)$。
③ 増減は $f'$ の符号。$f'>0$ で増加、$f'<0$ で減少。
★極値は【増減表】をかいて求める。$f'(a)=0$ だけでは極値と言えない
　（$y=x^3$ は $f'(0)=0$ でも極値をもたない）。$f'$ の符号が【変わる】ことが条件。
★「極大値」と「最大値」は別物。定義域つきなら端の値と比べて最大を決める。""",

    6: r"""▶ 積分は微分の逆。$\displaystyle\int x^n dx=\dfrac{x^{n+1}}{n+1}+C$。
① 不定積分は【積分定数 $C$】を必ず書く。書き忘れは減点。
② 定積分は $\displaystyle\int_a^b f(x)dx=\Bigl[F(x)\Bigr]_a^b=F(b)-F(a)$。$C$ は消えるので不要。
③ 定積分は【符号つきの量】であって面積ではない。$x$ 軸より下では負になる。
★面積は必ず正。「（上の関数）−（下の関数）」を積分する。
　どちらが上かは、交点を求めてグラフを描いて決める。
★$x$ 軸より下にある部分の面積は $\displaystyle\int\{0-f(x)\}dx$（符号を反転させる）。
★偶関数は $\displaystyle\int_{-a}^{a}f=2\int_0^a f$、奇関数は $0$。計算量を大きく減らせる。""",
}
