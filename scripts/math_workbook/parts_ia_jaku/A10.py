# -*- coding: utf-8 -*-
"""A10 三角比の基本と相互関係（数学I 図形と計量）"""
import os, sys
import sympy as sp
from sympy import symbols, Rational as R, sqrt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from svgfig import Canvas   # noqa: E402  数学座標→SVG(y上向き)変換

S, C = symbols('S C', real=True)   # chk 用: S=sinθ, C=cosθ


def _fig_right_triangle():
    """∠B=90°, AB=5, BC=12 の直角三角形。stem に無い数値(AC の長さ)は書かない。"""
    c = Canvas(xr=(-1.5, 13.5), yr=(-1.5, 6.5), size=(215, 120), pad=14)
    A, B, Cp = (0, 5), (0, 0), (12, 0)
    c.poly([A, B, Cp])
    c.right_angle(0, 0, 0, 5, 12, 0, size=0.7)
    c.label(0, 5, "A", dx=-14, dy=-2)
    c.label(0, 0, "B", dx=-14, dy=13)
    c.label(12, 0, "C", dx=5, dy=13)
    c.label(0, 2.5, "5", dx=-13, dy=4)
    c.label(6, 0, "12", dx=-7, dy=15)
    return c.svg()


UNIT = {
 "name": "三角比の基本と相互関係",
 "tag": "定義・相互関係・符号の決め方",
 "problems": [

  {"group": "直角三角形と三角定規の角", "level": "basic",
   "skill": "TR1", "sub": [],
   "stem": "下の図のように、$\\angle\\mathrm{B}=90^\\circ$、$\\mathrm{AB}=5$、$\\mathrm{BC}=12$ "
           "である直角三角形 $\\mathrm{ABC}$ がある。"
           "$\\sin\\mathrm{A}$、$\\cos\\mathrm{A}$、$\\tan\\mathrm{A}$ の値をそれぞれ求めよ。",
   "answer": "$\\sin\\mathrm{A}=\\dfrac{12}{13}$、$\\cos\\mathrm{A}=\\dfrac{5}{13}$、"
             "$\\tan\\mathrm{A}=\\dfrac{12}{5}$",
   "figure": _fig_right_triangle(),
   "explanation": r"""▶ 三角比は<b>どの角から見るかで辺の役割が変わる</b>。
比を書く前に、$\angle\mathrm{A}$ から見た「斜辺・対辺・隣辺」の3つを言葉で確定させる。
① 直角は $\mathrm{B}$ にあるので、斜辺は直角の向かい側の $\mathrm{AC}$。
三平方の定理より $\mathrm{AC}=\sqrt{5^{2}+12^{2}}=\sqrt{169}=13$。
② $\angle\mathrm{A}$ の対辺（向かい合う辺）は $\mathrm{BC}=12$、隣辺（$\angle\mathrm{A}$ をはさむ辺）は $\mathrm{AB}=5$。
③ サイン＝対辺÷斜辺 だから $\sin\mathrm{A}=\frac{12}{13}$。
④ コサイン＝隣辺÷斜辺 だから $\cos\mathrm{A}=\frac{5}{13}$。
⑤ タンジェント＝対辺÷隣辺 だから $\tan\mathrm{A}=\frac{12}{5}$。
★ 事故の1位は<b>斜辺を「一番下の辺」「縦の辺」と思い込む</b>こと。斜辺は必ず
<b>直角の向かい側</b>で、図の向きとは無関係。角を見る位置が変われば対辺と隣辺は入れ替わる
（$\angle\mathrm{C}$ から見れば $\sin\mathrm{C}=\frac{5}{13}$ で、$\sin\mathrm{A}$ とは別物）。
検算は $\sin^{2}\mathrm{A}+\cos^{2}\mathrm{A}=\frac{144+25}{169}=1$ ✓ と
$\frac{\sin\mathrm{A}}{\cos\mathrm{A}}=\frac{12}{13}\times\frac{13}{5}=\frac{12}{5}=\tan\mathrm{A}$ ✓ の2本。""",
   "chk": lambda: (lambda t=sp.acos(sp.Matrix([0, -5]).dot(sp.Matrix([12, -5]))
                                    / (sp.Matrix([0, -5]).norm() * sp.Matrix([12, -5]).norm())):
                   sp.Matrix([0, -5]).norm() == 5 and sp.Matrix([12, 0]).norm() == 12
                   and sp.simplify(sp.sin(t) - R(12, 13)) == 0
                   and sp.simplify(sp.cos(t) - R(5, 13)) == 0
                   and sp.simplify(sp.tan(t) - R(12, 5)) == 0)()},

  {"group": "直角三角形と三角定規の角", "level": "basic",
   "skill": "TR1", "sub": [],
   "stem": "次の式の値をそれぞれ求めよ。<br>"
           "(1) $\\tan 30^\\circ\\tan 60^\\circ+\\sin 45^\\circ\\cos 45^\\circ-\\cos^{2}30^\\circ$<br>"
           "(2) $\\sin 120^\\circ\\cos 150^\\circ-\\tan 135^\\circ+\\cos^{2}120^\\circ$",
   "answer": "(1) $\\dfrac{3}{4}$、(2) $\\dfrac{1}{2}$",
   "explanation": r"""▶ $30^\circ,\ 45^\circ,\ 60^\circ$ の値は丸暗記しない。<b>2枚の三角定規</b>
（辺の比 $1:2:\sqrt{3}$ と $1:1:\sqrt{2}$）を隅に描いて、そこから読み取れば取り違えが起きない。
鈍角は $180^\circ-\theta$ の公式で<b>この2枚に戻してから符号を付ける</b>。
① $\tan 30^\circ=\frac{1}{\sqrt{3}}$、$\tan 60^\circ=\sqrt{3}$ なので
$\tan 30^\circ\tan 60^\circ=\frac{1}{\sqrt{3}}\times\sqrt{3}=1$。
② $\sin 45^\circ=\cos 45^\circ=\frac{1}{\sqrt{2}}$ なので
$\sin 45^\circ\cos 45^\circ=\frac{1}{\sqrt{2}}\times\frac{1}{\sqrt{2}}=\frac{1}{2}$。
③ $\cos 30^\circ=\frac{\sqrt{3}}{2}$ なので $\cos^{2}30^\circ=\left(\frac{\sqrt{3}}{2}\right)^{2}=\frac{3}{4}$。
④ (1) は $1+\frac{1}{2}-\frac{3}{4}=\frac{4+2-3}{4}=\frac{3}{4}$。
⑤ (2) は角を $180^\circ-\theta$ の形に読み替える。単位円で $y$ 軸に関して折り返すので
<b>$\sin$ はそのまま・$\cos$ と $\tan$ だけ符号が反転</b>する:
$\sin 120^\circ=\sin 60^\circ=\frac{\sqrt{3}}{2}$、$\cos 150^\circ=-\cos 30^\circ=-\frac{\sqrt{3}}{2}$、
$\tan 135^\circ=-\tan 45^\circ=-1$、$\cos 120^\circ=-\cos 60^\circ=-\frac{1}{2}$。
⑥ よって $\sin 120^\circ\cos 150^\circ=\frac{\sqrt{3}}{2}\times\left(-\frac{\sqrt{3}}{2}\right)=-\frac{3}{4}$、
$-\tan 135^\circ=+1$、$\cos^{2}120^\circ=\left(-\frac{1}{2}\right)^{2}=\frac{1}{4}$ となり、
(2) は $-\frac{3}{4}+1+\frac{1}{4}=\frac{1}{2}$。
★ 事故の1位は<b>$\sin 60^\circ$ と $\cos 60^\circ$ の取り違え</b>。
$0^\circ$ から $90^\circ$ へ角を大きくすると $\sin$ は増え $\cos$ は減る、と向きだけ覚えておけば
$\sin 60^\circ=\frac{\sqrt{3}}{2}\gt\sin 30^\circ=\frac{1}{2}$ で即その場で確かめられる。
鈍角では<b>負になれるのは $\cos$ と $\tan$ だけ</b>で $\sin$ は $0$ 以上。
ただし⑥のように<b>2乗すると負は消える</b>（$\cos 120^\circ\lt 0$ でも $\cos^{2}120^\circ\gt 0$）。
もう1つ、$\cos^{2}30^\circ$ は $(\cos 30^\circ)^{2}$ の意味。<b>2乗するのは角ではなく値</b>。""",
   "chk": lambda: (sp.simplify(sp.tan(sp.pi/6)*sp.tan(sp.pi/3)
                               + sp.sin(sp.pi/4)*sp.cos(sp.pi/4)
                               - sp.cos(sp.pi/6)**2 - R(3, 4)) == 0
                   and sp.simplify(sp.sin(2*sp.pi/3)*sp.cos(5*sp.pi/6)
                                   - sp.tan(3*sp.pi/4)
                                   + sp.cos(2*sp.pi/3)**2 - R(1, 2)) == 0)},

  {"group": "1つの値から残りの2つを求める", "level": "basic",
   "skill": "TR2", "sub": ["TR1"],
   "stem": "鋭角 $\\theta$ が $\\cos\\theta=\\dfrac{8}{17}$ を満たすとき、"
           "$\\sin\\theta$ と $\\tan\\theta$ の値をそれぞれ求めよ。",
   "answer": "$\\sin\\theta=\\dfrac{15}{17}$、$\\tan\\theta=\\dfrac{15}{8}$",
   "explanation": r"""▶ 3つの三角比は $\sin^{2}\theta+\cos^{2}\theta=1$ と
$\tan\theta=\frac{\sin\theta}{\cos\theta}$ で鎖のようにつながっている。<b>1つ分かれば残りは芋づる式</b>。
① $\sin^{2}\theta=1-\cos^{2}\theta=1-\left(\frac{8}{17}\right)^{2}=1-\frac{64}{289}=\frac{225}{289}$。
② ここで2乗を外すが、$\sin\theta=\pm\frac{15}{17}$ の<b>どちらかを決めるのは条件文</b>。
$\theta$ は鋭角なので $\sin\theta\gt 0$、よって $\sin\theta=\frac{15}{17}$。
③ $\tan\theta=\frac{\sin\theta}{\cos\theta}=\frac{15}{17}\div\frac{8}{17}=\frac{15}{17}\times\frac{17}{8}=\frac{15}{8}$。
分母がそろっているので、<b>③は分子どうしの比</b>になる。
★ この単元最大の失点は<b>ルートを外す瞬間に符号を決め忘れる</b>こと。
$\sin^{2}\theta$ が出た行のすぐ横に「鋭角だから＋」と書き込む習慣をつける。
検算は $8:15:17$ の直角三角形を実際に描くこと（$8^{2}+15^{2}=64+225=289=17^{2}$）。
鋭角の問題は必ず直角三角形が描けるので、<b>答えは図から読み直せる</b>——
隣辺 $8$、対辺 $15$、斜辺 $17$ の図の上で「対辺÷斜辺」「対辺÷隣辺」を読めば③まで一致する。""",
   "chk": lambda: (lambda s=[v for v in sp.solve(sp.Eq(S**2 + R(8, 17)**2, 1), S) if v > 0]:
                   len(s) == 1 and s[0] == R(15, 17)
                   and sp.simplify(s[0]/R(8, 17) - R(15, 8)) == 0
                   and 8**2 + 15**2 == 17**2)()},

  {"group": "1つの値から残りの2つを求める", "level": "standard",
   "skill": "TR2", "sub": [],
   "stem": "$0^\\circ\\leqq\\theta\\leqq 180^\\circ$ とする。$\\tan\\theta=-2$ のとき、"
           "$\\sin\\theta$ と $\\cos\\theta$ の値を求めよ。",
   "answer": "$\\sin\\theta=\\dfrac{2\\sqrt{5}}{5}$、$\\cos\\theta=-\\dfrac{\\sqrt{5}}{5}$",
   "explanation": r"""▶ 与えられたのが $\tan\theta$ だけのときは $1+\tan^{2}\theta=\frac{1}{\cos^{2}\theta}$ を使う。
$\sin$ と $\cos$ を同時に追わず、<b>先に $\cos\theta$ を確定させる</b>のが手数が最少。
① まず符号を決める。$0^\circ\leqq\theta\leqq 180^\circ$ の範囲では $\sin\theta\geqq 0$ が必ず成り立つ。
いま $\tan\theta=-2\lt 0$ だから $\cos\theta\lt 0$、つまり $\theta$ は鈍角（$90^\circ\lt\theta\lt 180^\circ$）。
② $1+\tan^{2}\theta=1+(-2)^{2}=5$ なので $\frac{1}{\cos^{2}\theta}=5$、すなわち $\cos^{2}\theta=\frac{1}{5}$。
③ ①より $\cos\theta\lt 0$ だから $\cos\theta=-\frac{1}{\sqrt{5}}=-\frac{\sqrt{5}}{5}$。
④ $\tan\theta=\frac{\sin\theta}{\cos\theta}$ を変形して
$\sin\theta=\tan\theta\times\cos\theta=(-2)\times\left(-\frac{\sqrt{5}}{5}\right)=\frac{2\sqrt{5}}{5}$。
★ 最頻出の事故は<b>符号の決め忘れ</b>で、$\cos\theta=+\frac{\sqrt{5}}{5}$ と書いてしまうもの。
$0^\circ\leqq\theta\leqq 180^\circ$ では<b>$\sin$ は常に $0$ 以上、負になれるのは $\cos$ と $\tan$ だけ</b>
—— これを計算を始める前に紙の端に書いておく。
検算は $\sin^{2}\theta+\cos^{2}\theta=\frac{4\times 5}{25}+\frac{5}{25}=\frac{20+5}{25}=1$ ✓、
さらに $\frac{\sin\theta}{\cos\theta}=\frac{2\sqrt{5}}{5}\times\left(-\frac{5}{\sqrt{5}}\right)=-2$ ✓ で
与えられた $\tan\theta$ に戻ることまで見る。""",
   "chk": lambda: (lambda z=[d for d in sp.solve([S**2 + C**2 - 1, S + 2*C], [S, C], dict=True)
                             if d[S] > 0]:
                   len(z) == 1
                   and sp.simplify(z[0][S] - 2*sqrt(5)/5) == 0
                   and sp.simplify(z[0][C] + sqrt(5)/5) == 0)()},

  {"group": "余角と補角の言いかえ", "level": "standard",
   "skill": "TR3", "sub": ["TR2"],
   "stem": "$\\sin^{2}20^\\circ+\\sin^{2}70^\\circ+\\cos 160^\\circ+\\cos 20^\\circ$ の値を求めよ。",
   "answer": "$1$",
   "explanation": r"""▶ $70^\circ$ も $160^\circ$ も単独では値が分からない。
<b>$90^\circ-\theta$ と $180^\circ-\theta$ の公式で角を $20^\circ$ にそろえる</b>のが方針。
そろえた結果 $\sin^{2}\theta+\cos^{2}\theta=1$ の形と、打ち消し合う組が現れる。
① $70^\circ=90^\circ-20^\circ$ なので $\sin 70^\circ=\sin(90^\circ-20^\circ)=\cos 20^\circ$。
② よって $\sin^{2}20^\circ+\sin^{2}70^\circ=\sin^{2}20^\circ+\cos^{2}20^\circ=1$。
③ $160^\circ=180^\circ-20^\circ$ なので $\cos 160^\circ=\cos(180^\circ-20^\circ)=-\cos 20^\circ$。
④ よって $\cos 160^\circ+\cos 20^\circ=-\cos 20^\circ+\cos 20^\circ=0$。
⑤ 全体は $1+0=1$。
★ 公式を4本（$\sin,\cos$ × 余角,補角）丸暗記すると<b>必ず符号を1つ落とす</b>。
覚えるのは単位円の動きだけでよい: $180^\circ-\theta$ は $y$ 軸に関する折り返しだから
$y$ 座標（$=\sin$）はそのまま・$x$ 座標（$=\cos$）だけ符号が反転する。
$90^\circ-\theta$ は直線 $y=x$ に関する折り返しだから $\sin$ と $\cos$ が入れ替わる。
その場でできる検算は<b>大きさの見当</b>: $\cos 160^\circ$ は鈍角なので負のはず、
$\sin 70^\circ$ は $1$ に近いはず —— 符号や大小が合わない答えはこの段階で弾ける。""",
   "chk": lambda: bool(abs(sp.N(sp.sin(sp.pi*20/180)**2 + sp.sin(sp.pi*70/180)**2
                                + sp.cos(sp.pi*160/180) + sp.cos(sp.pi*20/180) - 1, 50))
                       < sp.Rational(1, 10**30))},

  {"group": "式の値（相互関係を使う）", "level": "standard",
   "skill": "TR2", "sub": ["SK3"],
   "stem": "$0^\\circ\\leqq\\theta\\leqq 180^\\circ$ とする。"
           "$\\sin\\theta+\\cos\\theta=\\dfrac{1}{2}$ のとき、"
           "$\\sin\\theta\\cos\\theta$ と $\\sin^{3}\\theta+\\cos^{3}\\theta$ の値を求めよ。",
   "answer": "$\\sin\\theta\\cos\\theta=-\\dfrac{3}{8}$、$\\sin^{3}\\theta+\\cos^{3}\\theta=\\dfrac{11}{16}$",
   "explanation": r"""▶ $\sin\theta$ と $\cos\theta$ を<b>2つの数とみなすと、和と積の対称式</b>の問題になる。
$\sin^{2}\theta+\cos^{2}\theta=1$ が「2乗の和」を最初から与えてくれるので、<b>和を2乗すれば積が出る</b>。
$\theta$ の値そのものを求める必要は無い。
① $(\sin\theta+\cos\theta)^{2}=\sin^{2}\theta+2\sin\theta\cos\theta+\cos^{2}\theta=1+2\sin\theta\cos\theta$。
② 左辺は $\left(\frac{1}{2}\right)^{2}=\frac{1}{4}$ だから $1+2\sin\theta\cos\theta=\frac{1}{4}$。
③ よって $2\sin\theta\cos\theta=\frac{1}{4}-1=-\frac{3}{4}$、$\sin\theta\cos\theta=-\frac{3}{8}$。
④ 3乗の和は $a^{3}+b^{3}=(a+b)^{3}-3ab(a+b)$ を使う（展開して確かめられる）。
$\sin^{3}\theta+\cos^{3}\theta=\left(\frac{1}{2}\right)^{3}-3\times\left(-\frac{3}{8}\right)\times\frac{1}{2}$
$=\frac{1}{8}+\frac{9}{16}=\frac{2+9}{16}=\frac{11}{16}$。
★ ③で積が負になったのを計算ミスと思い、符号を直してしまう人が多い。
$\sin\theta\cos\theta\lt 0$ は<b>「$\theta$ が鈍角」という情報そのもの</b>で、正しい。
実際 $0^\circ\leqq\theta\leqq 180^\circ$ で $\sin\theta\geqq 0$ だから、積が負なら $\cos\theta\lt 0$ が確定する。
検算は逆向きに戻すこと: $1+2\times\left(-\frac{3}{8}\right)=1-\frac{3}{4}=\frac{1}{4}$ となり、
$\left(\frac{1}{2}\right)^{2}$ と一致する ✓ ——ここが合えば③まではまず間違いない。""",
   "chk": lambda: (lambda z=[d for d in sp.solve([S**2 + C**2 - 1, S + C - R(1, 2)], [S, C], dict=True)
                             if d[S] >= 0]:
                   len(z) == 1
                   and sp.simplify(z[0][S]*z[0][C] + R(3, 8)) == 0
                   and sp.simplify(z[0][S]**3 + z[0][C]**3 - R(11, 16)) == 0)()},

  {"group": "式の値（相互関係を使う）", "level": "advanced",
   "skill": "TR2", "sub": ["TR1"],
   "stem": "$0^\\circ\\leqq\\theta\\leqq 180^\\circ$ とする。$\\tan\\theta=3$ のとき、"
           "$\\dfrac{\\sin\\theta+2\\cos\\theta}{3\\sin\\theta-\\cos\\theta}$ と "
           "$\\sin^{2}\\theta-\\sin\\theta\\cos\\theta$ の値を求めよ。",
   "answer": "$\\dfrac{\\sin\\theta+2\\cos\\theta}{3\\sin\\theta-\\cos\\theta}=\\dfrac{5}{8}$、"
             "$\\sin^{2}\\theta-\\sin\\theta\\cos\\theta=\\dfrac{3}{5}$",
   "explanation": r"""▶ $\sin\theta$ と $\cos\theta$ について<b>各項の次数がそろっている式（同次式）</b>は、
$\cos\theta$ のべきで割ると $\tan\theta$ だけの式になる。
$\sin\theta,\ \cos\theta$ を個別に求めてから代入するより速く、根号も出ない。
① $\tan\theta=3\gt 0$ かつ $0^\circ\leqq\theta\leqq 180^\circ$ なので $\theta$ は鋭角。
とくに $\theta\neq 90^\circ$ だから $\cos\theta\neq 0$ で、$\cos\theta$ で割ってよい。
② 第1式は分子・分母とも1次の同次式。分母分子を $\cos\theta$ で割ると
$\frac{\tan\theta+2}{3\tan\theta-1}=\frac{3+2}{9-1}=\frac{5}{8}$。
③ 第2式は2次の同次式だが、このままでは割る相手がいない。そこで
<b>$1=\sin^{2}\theta+\cos^{2}\theta$ を分母に置いて分数にする</b>:
$\sin^{2}\theta-\sin\theta\cos\theta=\frac{\sin^{2}\theta-\sin\theta\cos\theta}{\sin^{2}\theta+\cos^{2}\theta}$。
④ 分母分子を $\cos^{2}\theta$ で割ると
$\frac{\tan^{2}\theta-\tan\theta}{\tan^{2}\theta+1}=\frac{9-3}{9+1}=\frac{6}{10}=\frac{3}{5}$。
★ ③の<b>「$1$ を $\sin^{2}\theta+\cos^{2}\theta$ に書き換えて次数をそろえる」</b>が
この型の急所で、ここが出てこないと手が止まる。
また②で割る前に①のように $\cos\theta\neq 0$ を確認すること（$\tan\theta$ の値が与えられている時点で
$\theta\neq 90^\circ$ は保証されるが、答案には書く）。
検算は実際の値を代入する: $\theta$ は鋭角で $\tan\theta=3$ だから $\sin\theta=\frac{3\sqrt{10}}{10}$、
$\cos\theta=\frac{\sqrt{10}}{10}$。これで $\sin^{2}\theta-\sin\theta\cos\theta=\frac{9}{10}-\frac{3}{10}=\frac{3}{5}$ ✓
—— 同次式の割り算を使わない<b>別ルート</b>で同じ値に着けば、②③の変形は正しい。""",
   "chk": lambda: (lambda z=[d for d in sp.solve([S**2 + C**2 - 1, S - 3*C], [S, C], dict=True)
                             if d[S] >= 0]:
                   len(z) == 1
                   and sp.simplify((z[0][S] + 2*z[0][C])/(3*z[0][S] - z[0][C]) - R(5, 8)) == 0
                   and sp.simplify(z[0][S]**2 - z[0][S]*z[0][C] - R(3, 5)) == 0)()},
 ]}
