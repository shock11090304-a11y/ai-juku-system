# -*- coding: utf-8 -*-
"""A02 実数・平方根・式の値（数学I 数と式）"""
import sympy as sp
from sympy import symbols, sqrt, Rational as R

x, y, a, b = symbols('x y a b', real=True)

UNIT = {
 "name": "実数・平方根・式の値",
 "tag": "有理化・二重根号・対称式・小数部分",
 "problems": [

  {"group": "根号のはずし方", "level": "basic",
   "skill": "SK4", "sub": ["SK6"],
   "stem": "$\\sqrt{(\\sqrt{3}-2)^{2}}+\\sqrt{(\\sqrt{3}+1)^{2}}$ を簡単にせよ。",
   "answer": "$3$",
   "explanation": r"""▶ $\sqrt{A^{2}}$ が $A$ に戻るとは限らない。根号の値は必ず $0$ 以上なので、
正しくは $\sqrt{A^{2}}=|A|$。だから<b>中身の符号を先に判定してから</b>外す。
① $\sqrt{3}=1.73\cdots$ で $\sqrt{3}\lt 2$ だから $\sqrt{3}-2$ は負。
よって $\sqrt{(\sqrt{3}-2)^{2}}=|\sqrt{3}-2|=2-\sqrt{3}$ と符号を反転させて外す。
② $\sqrt{3}+1$ は正。こちらはそのまま $\sqrt{(\sqrt{3}+1)^{2}}=\sqrt{3}+1$。
③ 足すと $(2-\sqrt{3})+(\sqrt{3}+1)=3$。$\sqrt{3}$ が消えて整数になった。
★ <b>2つの項で外し方が違う</b>のがこの問題の山。両方そのまま外すと
$(\sqrt{3}-2)+(\sqrt{3}+1)=2\sqrt{3}-1$ となって別物になる。
符号の判定は整数の $2$ 乗ではさめば足りる: $1^{2}\lt 3\lt 2^{2}$ より $1\lt\sqrt{3}\lt 2$。
検算は概算で: $2-\sqrt3\approx 0.27$、$\sqrt3+1\approx 2.73$、和はちょうど $3$ ✓
なお $0.333\cdots=\frac{1}{3}$ のように分数へ直せる数が有理数、$\sqrt{3}$ や $\pi$ のように
循環しない無限小数になる数が無理数で、実数はこの2つに分かれる。""",
   "chk": lambda: (lambda E=sp.sqrt((sp.sqrt(3) - 2)**2) + sp.sqrt((sp.sqrt(3) + 1)**2): bool(
        sp.simplify(E - 3) == 0 and
        abs(sp.N(E, 40) - 3) < sp.Rational(1, 10**30)))()},

  {"group": "根号のはずし方", "level": "basic",
   "skill": "SK4", "sub": ["SK6"],
   "stem": "$\\sqrt{(\\sqrt{5}-3)^{2}}+\\sqrt{(2-\\sqrt{5})^{2}}$ を簡単にせよ。",
   "answer": "$1$",
   "explanation": r"""▶ $\sqrt{A^{2}}=A$ <b>ではない</b>。正しくは $\sqrt{A^{2}}=|A|$。
根号は必ず $0$ 以上の値を返すので、中身が負なら符号を反転させて外す。だから<b>先に符号を判定する</b>。
① $\sqrt{5}=2.23\cdots$ だから $\sqrt{5}-3$ は負。よって $\sqrt{(\sqrt{5}-3)^{2}}=|\sqrt{5}-3|=3-\sqrt{5}$。
② $\sqrt{5}\gt 2$ だから $2-\sqrt{5}$ も負。よって $\sqrt{(2-\sqrt{5})^{2}}=|2-\sqrt{5}|=\sqrt{5}-2$。
③ 足すと $(3-\sqrt{5})+(\sqrt{5}-2)=1$。$\sqrt{5}$ がきれいに消えた。
★ 事故の1位は $\sqrt{(\sqrt{5}-3)^{2}}$ をそのまま $\sqrt{5}-3$ と書くこと。これは負の数なので、
$0$ 以上しか返さない根号の値になりえない。<b>「$\sqrt{\phantom{0}}$ を外したら答えが正か」を毎回見る</b>。
符号の判定は整数の $2$ 乗ではさめば十分: $2^{2}\lt 5\lt 3^{2}$ より $2\lt\sqrt{5}\lt 3$。
検算は概算で: $3-\sqrt5\approx 0.76$、$\sqrt5-2\approx 0.24$、和はほぼ $1$ ✓""",
   "chk": lambda: (lambda E=sp.sqrt((sp.sqrt(5) - 3)**2) + sp.sqrt((2 - sp.sqrt(5))**2): bool(
        sp.simplify(E - 1) == 0 and
        abs(sp.N(E, 40) - 1) < sp.Rational(1, 10**30)))()},

  {"group": "分母の有理化", "level": "basic",
   "skill": "SK4", "sub": ["SK1"],
   "stem": "$\\dfrac{4}{3+\\sqrt{5}}-\\dfrac{4}{3-\\sqrt{5}}$ を計算せよ。",
   "answer": "$-2\\sqrt{5}$",
   "explanation": r"""▶ 分母に根号があるままでは引き算の通分ができない。
<b>それぞれ有理化して分母を整数にしてから引く</b>のが最短。掛けるのは<b>符号だけ変えた式（共役）</b>で、
$(A+B)(A-B)=A^{2}-B^{2}$ が効いて根号が消えるからこれを選ぶ。
① 1つ目は分母・分子に $3-\sqrt{5}$ を掛ける。分母は $(3+\sqrt{5})(3-\sqrt{5})=9-5=4$。
よって $\frac{4(3-\sqrt{5})}{4}=3-\sqrt{5}$。
② 2つ目は分母・分子に $3+\sqrt{5}$ を掛ける。分母はやはり $9-5=4$ で $\frac{4(3+\sqrt{5})}{4}=3+\sqrt{5}$。
③ 引くと $(3-\sqrt{5})-(3+\sqrt{5})=3-\sqrt{5}-3-\sqrt{5}=-2\sqrt{5}$。
★ 事故は③で<b>かっこを外すときに後ろの項の符号を変え忘れる</b>こと（$-2\sqrt5$ が $0$ になる）。
引き算のかっこは「中身の符号を全部ひっくり返す」と声に出してから外す。
検算は $\sqrt{5}\approx 2.24$ を入れる: 元の式 $\approx\frac{4}{5.24}-\frac{4}{0.76}\approx 0.76-5.26=-4.5$、
答え $-2\sqrt5\approx-4.47$ ✓ 符号まで合う。""",
   "chk": lambda: (lambda E=4/(3 + sqrt(5)) - 4/(3 - sqrt(5)): bool(
        sp.simplify(sp.radsimp(E) + 2*sqrt(5)) == 0 and
        abs(sp.N(E + 2*sqrt(5), 40)) < sp.Rational(1, 10**30)))()},

  {"group": "分母の有理化", "level": "standard",
   "skill": "SK4", "sub": ["SK1"],
   "stem": "$\\dfrac{\\sqrt{7}-\\sqrt{3}}{\\sqrt{7}+\\sqrt{3}}$ を簡単にせよ。",
   "answer": "$\\dfrac{5-\\sqrt{21}}{2}$",
   "explanation": r"""▶ 分母が2項なので、共役 $\sqrt{7}-\sqrt{3}$ を分母・分子に掛ける。
分母は $(\sqrt{7})^{2}-(\sqrt{3})^{2}$ になって根号が消え、<b>分子は2乗の展開</b>になる。
① 分母: $(\sqrt{7}+\sqrt{3})(\sqrt{7}-\sqrt{3})=7-3=4$。
② 分子: $(\sqrt{7}-\sqrt{3})^{2}=(\sqrt{7})^{2}-2\sqrt{7}\sqrt{3}+(\sqrt{3})^{2}=7-2\sqrt{21}+3=10-2\sqrt{21}$。
③ よって $\frac{10-2\sqrt{21}}{4}$。分子・分母を $2$ で割って $\frac{5-\sqrt{21}}{2}$。
★ 事故の1位は②で $\sqrt{7}\times\sqrt{3}$ を $\sqrt{10}$ としてしまうこと。
<b>根号の中に入るのは掛け算だけ</b>で、$\sqrt{7}\sqrt{3}=\sqrt{21}$、足し算は中に入らない。
2位は③の約分忘れ（$\frac{10-2\sqrt{21}}{4}$ で止める）。<b>約分は全部の項にかかるか</b>を確認してから割る。
検算 ($\sqrt{7}\approx 2.65,\ \sqrt{3}\approx 1.73,\ \sqrt{21}\approx 4.58$):
元の式 $\approx\frac{0.92}{4.38}\approx 0.21$、答え $\approx\frac{5-4.58}{2}=0.21$ ✓""",
   "chk": lambda: (lambda E=(sqrt(7) - sqrt(3))/(sqrt(7) + sqrt(3)): bool(
        sp.simplify(sp.radsimp(E) - (5 - sqrt(21))/2) == 0 and
        abs(sp.N(E - (5 - sqrt(21))/2, 40)) < sp.Rational(1, 10**30)))()},

  {"group": "対称式で値を求める", "level": "standard",
   "skill": "SK3", "sub": ["SK4", "SK1"],
   "stem": "$x=\\dfrac{1}{\\sqrt{6}-\\sqrt{5}}$、$y=\\dfrac{1}{\\sqrt{6}+\\sqrt{5}}$ のとき、"
           "$x+y$、$xy$、$x^{2}+y^{2}$、$x^{3}+y^{3}$ の値を求めよ。",
   "answer": "$x+y=2\\sqrt{6}$、$xy=1$、$x^{2}+y^{2}=22$、$x^{3}+y^{3}=42\\sqrt{6}$",
   "explanation": r"""▶ $x$ や $y$ を直接3乗するのは手数が多すぎる。
$x^{2}+y^{2}$ も $x^{3}+y^{3}$ も $x$ と $y$ を入れ替えても変わらない式（対称式）なので、
<b>和 $x+y$ と積 $xy$ さえ出せば、あとは公式で組み立てられる</b>。まず有理化して形を整える。
① $x=\frac{\sqrt{6}+\sqrt{5}}{(\sqrt{6}-\sqrt{5})(\sqrt{6}+\sqrt{5})}=\frac{\sqrt{6}+\sqrt{5}}{6-5}=\sqrt{6}+\sqrt{5}$。
同様に $y=\sqrt{6}-\sqrt{5}$。
② $x+y=2\sqrt{6}$、$xy=(\sqrt{6})^{2}-(\sqrt{5})^{2}=6-5=1$。
③ $x^{2}+y^{2}=(x+y)^{2}-2xy=(2\sqrt{6})^{2}-2\cdot 1=24-2=22$。
④ $x^{3}+y^{3}=(x+y)^{3}-3xy(x+y)=(2\sqrt{6})^{3}-3\cdot 1\cdot 2\sqrt{6}=48\sqrt{6}-6\sqrt{6}=42\sqrt{6}$。
★ 暗記するのは2本だけ: $x^{2}+y^{2}=(x+y)^{2}-2xy$ と $x^{3}+y^{3}=(x+y)^{3}-3xy(x+y)$。
事故の1位は④で $(2\sqrt{6})^{3}$ を $2\cdot 6\sqrt{6}$ とすること。<b>係数も3乗する</b>ので
$2^{3}(\sqrt{6})^{3}=8\cdot 6\sqrt{6}=48\sqrt{6}$。
検算のコツは②で $xy=1$ に気づくこと。積が $1$ なら $y=\frac{1}{x}$ なので、
③④はそれぞれ $x^{2}+\frac{1}{x^{2}}$、$x^{3}+\frac{1}{x^{3}}$ の形になっている。
$x\approx 4.68$、$y\approx 0.21$ で
$x^{2}+y^{2}\approx 21.9+0.05\approx 22$ ✓""",
   "chk": lambda: (lambda X=1/(sqrt(6) - sqrt(5)), Y=1/(sqrt(6) + sqrt(5)): all(
        sp.simplify(sp.radsimp(e) - v) == 0
        for e, v in ((X + Y, 2*sqrt(6)), (X*Y, 1),
                     (X**2 + Y**2, 22), (X**3 + Y**3, 42*sqrt(6)))))()},

  {"group": "二重根号と整数部分・小数部分", "level": "standard",
   "skill": "SK5", "sub": ["SK4"],
   "stem": "$\\sqrt{9+4\\sqrt{5}}$ の二重根号をはずして簡単にせよ。",
   "answer": "$2+\\sqrt{5}$",
   "explanation": r"""▶ 二重根号は $(\sqrt{m}+\sqrt{n})^{2}=m+n+2\sqrt{mn}$ を逆にたどる。
だから公式 $\sqrt{p+2\sqrt{q}}=\sqrt{m}+\sqrt{n}$（$m+n=p$、$mn=q$）は
<b>内側が $2\sqrt{q}$ の形、つまり係数がちょうど $2$ のときだけ</b>使える。まずその形に直す。
① $4\sqrt{5}=2\times 2\sqrt{5}=2\sqrt{2^{2}\times 5}=2\sqrt{20}$。よって $\sqrt{9+2\sqrt{20}}$。
② 足して $9$、掛けて $20$ になる2数を探す。$20=1\times 20=2\times 10=4\times 5$ のうち、和が $9$ なのは $4$ と $5$。
③ よって $\sqrt{9+2\sqrt{20}}=\sqrt{5}+\sqrt{4}=\sqrt{5}+2$。
★ 最大の事故は①を飛ばして「足して $9$、掛けて $5$」を探し始めること。
<b>内側の係数を $2$ にそろえる</b>のが第一手で、係数 $k$ を根号の中に入れるときは $k^{2}$ を掛ける。
検算は<b>2乗して戻す</b>のが確実で、これだけで正誤が確定する:
$(2+\sqrt{5})^{2}=4+4\sqrt{5}+5=9+4\sqrt{5}$ ✓ 答えが $2-\sqrt5$ のように負にならないかも同時に見る。""",
   "chk": lambda: bool(sp.expand((2 + sqrt(5))**2) == sp.expand(9 + 4*sqrt(5))
                       and sp.N(2 + sqrt(5), 30) > 0
                       and abs(sp.N(sp.sqrt(9 + 4*sqrt(5)) - (2 + sqrt(5)), 40))
                           < sp.Rational(1, 10**30))},

  {"group": "二重根号と整数部分・小数部分", "level": "advanced",
   "skill": "SK5", "sub": ["SK4", "SK3"],
   "stem": "$x=\\sqrt{11+6\\sqrt{2}}$ とする。二重根号をはずして $x$ を簡単にし、"
           "さらに $x$ の整数部分を $a$、小数部分を $b$ とするとき、"
           "$a$、$b$、$b+\\dfrac{1}{b}$ の値を求めよ。",
   "answer": "$x=3+\\sqrt{2}$、$a=4$、$b=\\sqrt{2}-1$、$b+\\dfrac{1}{b}=2\\sqrt{2}$",
   "explanation": r"""▶ 小数部分は目分量では決まらない。<b>（小数部分）$=$（もとの数）$-$（整数部分）</b>という
定義から式で出す。そのために整数部分を、整数ではさみうちして確定させるのが手順の中心になる。
① まず二重根号。$6\sqrt{2}=2\times 3\sqrt{2}=2\sqrt{3^{2}\times 2}=2\sqrt{18}$ なので $x=\sqrt{11+2\sqrt{18}}$。
② 足して $11$、掛けて $18$ の2数は $9$ と $2$。よって $x=\sqrt{9}+\sqrt{2}=3+\sqrt{2}$。
③ はさみうち: $1^{2}\lt 2\lt 2^{2}$ より $1\lt\sqrt{2}\lt 2$。各辺に $3$ を足して $4\lt 3+\sqrt{2}\lt 5$。
よって整数部分は $a=4$。
④ 小数部分は $b=x-a=(3+\sqrt{2})-4=\sqrt{2}-1$。
⑤ $\frac{1}{b}=\frac{1}{\sqrt{2}-1}=\frac{\sqrt{2}+1}{(\sqrt{2}-1)(\sqrt{2}+1)}=\frac{\sqrt{2}+1}{2-1}=\sqrt{2}+1$。
⑥ $b+\frac{1}{b}=(\sqrt{2}-1)+(\sqrt{2}+1)=2\sqrt{2}$。$-1$ と $+1$ が消えるのが対称式の気持ちよさ。
★ 事故の1位は④で $b$ を $0.41$ と小数に丸めてしまうこと。
<b>小数部分は根号のままの式で持つ</b>。丸めると⑤の有理化ができず、答えが出せなくなる。
2位は③を飛ばして $a=3$（$x$ の前半だけ見た）とすること。$\sqrt{2}$ の分が繰り上がる。
検算は必ず $0\leqq b\lt 1$ を確認する: $b=\sqrt{2}-1\approx 0.41$ ✓
これが $1$ 以上や負になっていたら整数部分の取り違えで、③に戻る。""",
   "chk": lambda: (lambda X=sp.sqrt(11 + 6*sqrt(2)): bool(
        sp.simplify(X - (3 + sqrt(2))) == 0 and
        sp.floor(X) == 4 and
        sp.simplify((X - sp.floor(X)) - (sqrt(2) - 1)) == 0 and
        0 <= sp.N(X - sp.floor(X), 40) < 1 and
        sp.simplify(sp.radsimp((X - sp.floor(X)) + 1/(X - sp.floor(X))) - 2*sqrt(2)) == 0))()},
 ]}
