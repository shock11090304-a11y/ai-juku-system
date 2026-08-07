# -*- coding: utf-8 -*-
"""A11 正弦定理・余弦定理（数学I 図形と計量）"""
import os, sys
import sympy as sp
from sympy import Rational as R, sqrt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from svgfig import Canvas   # noqa: E402  数学座標→SVG(y上向き)変換


# ---------------------------------------------------------------- chk 用の独立ルート
# ★ここに書く関数は「正弦定理・余弦定理を使わずに」三角形を実際に座標で作り、
#   距離・偏角・垂直二等分線の交点だけで答えを出し直す。
#   解説に書いた式をそのまま打ち直すと、式を間違えたときに検算も一緒に間違う。

def _dist2(P, Q):
    """2点間の距離の2乗(座標だけで出す)。"""
    d = P - Q
    return sp.expand(d.dot(d))


def _sas_pts(p, q, deg):
    """原点から x 軸方向に長さ p、角 deg の方向に長さ q を取った3点を返す。
    (2辺とその挟む角だけで三角形を実際に置く)"""
    th = sp.rad(deg)
    return (sp.Matrix([0, 0]), sp.Matrix([p, 0]),
            sp.Matrix([q*sp.cos(th), q*sp.sin(th)]))


def _asa_pts(Bdeg, Cdeg, b):
    """角B・角Cと辺 b(=CA) から3頂点 (A, B, C) を作る。
    B から角Bの向きに出た半直線と、C から角Cの向きに出た半直線の交点を
    連立1次方程式で求めるだけ(正弦定理は使わない)。"""
    B, C = sp.rad(Bdeg), sp.rad(Cdeg)
    s, t = sp.symbols('s t', positive=True)
    sol = sp.solve([s*sp.cos(B) + t*sp.cos(C) - 1,
                    s*sp.sin(B) - t*sp.sin(C)], [s, t], dict=True)[0]
    k = sp.simplify(b/sol[t])          # CA が b になるよう相似拡大する
    return (sp.simplify(sp.Matrix([sol[s]*sp.cos(B), sol[s]*sp.sin(B)])*k),
            sp.Matrix([0, 0]), sp.Matrix([k, 0]))


def _sss_pts(a, b, c):
    """3辺 a=BC, b=CA, c=AB から3頂点 (A, B, C) を作る(2円の交点)。"""
    x, y = sp.symbols('x y', real=True)
    sols = sp.solve([x**2 + y**2 - c**2, (x - a)**2 + y**2 - b**2], [x, y], dict=True)
    s = [q for q in sols if q[y] > 0][0]
    return sp.Matrix([s[x], s[y]]), sp.Matrix([0, 0]), sp.Matrix([a, 0])


def _circum_R(P, Q, S):
    """外接円の半径を「3頂点から等距離の点」を解いて出す(正弦定理を使わない)。"""
    u, v = sp.symbols('u v', real=True)
    O = sp.Matrix([u, v])
    sol = sp.solve([sp.expand((O - P).dot(O - P) - (O - Q).dot(O - Q)),
                    sp.expand((O - P).dot(O - P) - (O - S).dot(O - S))], [u, v], dict=True)[0]
    Oc = sp.Matrix([sol[u], sol[v]])
    return sp.sqrt(sp.simplify((Oc - P).dot(Oc - P)))


def _is_deg(P, Q, S, deg):
    """頂点 P の角が deg 度か。2方向の偏角(atan2)の差で測る(余弦定理を使わない)。"""
    u, w = Q - P, S - P
    ang = sp.deg(sp.Abs(sp.atan2(u[1], u[0]) - sp.atan2(w[1], w[0])))
    return bool(abs(sp.N(ang - deg, 50)) < R(1, 10**30))


def _heron(x, y, z):
    """3辺から面積(ヘロン)。角の検算を三角比と別ルートにするために使う。"""
    s = R(1, 2)*(x + y + z)
    return sp.sqrt(sp.simplify(s*(s - x)*(s - y)*(s - z)))


# ---------------------------------------------------------------- 図
def _fig_asa():
    """B=45°, C=30°, CA=8 の三角形。実点は _asa_pts と一致する A(4,4), B(0,0), C(4+4√3,0)。"""
    c = Canvas(xr=(-1.0, 12.0), yr=(-1.3, 5.2), size=(228, 118), pad=14)
    xc = 4 + 4*3**0.5
    c.poly([(4, 4), (0, 0), (xc, 0)])
    c.label(4, 4, "A", dx=-4, dy=-6)
    c.label(0, 0, "B", dx=-14, dy=13)
    c.label(xc, 0, "C", dx=5, dy=13)
    c.label(1.1, 0.0, "45°", dx=0, dy=-5, size=11)
    c.label(8.7, 0.0, "30°", dx=0, dy=-5, size=11)
    c.label((4 + xc)/2, 2.0, "8", dx=7, dy=-2)
    return c.svg()


def _fig_sas():
    """A=60°, AB=15, AC=7 の三角形。実点は A(0,0), B(15,0), C(7cos60°, 7sin60°)。"""
    import math
    c = Canvas(xr=(-1.0, 16.0), yr=(-1.4, 7.3), size=(226, 122), pad=14)
    cx, cy = 7*math.cos(math.radians(60)), 7*math.sin(math.radians(60))
    c.poly([(0, 0), (15, 0), (cx, cy)])
    c.label(0, 0, "A", dx=-14, dy=13)
    c.label(15, 0, "B", dx=5, dy=13)
    c.label(cx, cy, "C", dx=-3, dy=-6)
    c.label(1.6, 0.0, "60°", dx=0, dy=-5, size=11)
    c.label(7.5, 0, "15", dx=-7, dy=15)
    c.label(cx/2, cy/2, "7", dx=-13, dy=2)
    return c.svg()


def _fig_sss():
    """AB=6, BC=14, CA=10 の三角形。実点は B(0,0), C(14,0), A(33/7, 15√3/7)。
    ★角の大きさは答えなので図には書かない。"""
    import math
    c = Canvas(xr=(-1.0, 15.0), yr=(-1.4, 4.8), size=(224, 104), pad=14)
    ax, ay = 33/7, 15*math.sqrt(3)/7
    c.poly([(ax, ay), (0, 0), (14, 0)])
    c.label(ax, ay, "A", dx=-4, dy=-6)
    c.label(0, 0, "B", dx=-14, dy=13)
    c.label(14, 0, "C", dx=5, dy=13)
    c.label(ax/2, ay/2, "6", dx=-13, dy=3)
    c.label(7, 0, "14", dx=-7, dy=15)
    c.label((ax + 14)/2, ay/2, "10", dx=6, dy=0)
    return c.svg()


UNIT = {
 "name": "正弦定理・余弦定理",
 "tag": "辺と対角のペアで選ぶ・鈍角の符号",
 "problems": [

  {"group": "角と向かい合う辺が分かっているとき", "level": "basic",
   "skill": "TR4", "sub": ["TR1"],
   "stem": r"右の図の $\triangle\mathrm{ABC}$ で、$\angle\mathrm{B}=45^\circ$、"
           r"$\angle\mathrm{C}=30^\circ$、$\mathrm{CA}=8$ である。"
           r"辺 $\mathrm{AB}$ の長さを求めよ。",
   "answer": r"$\mathrm{AB}=4\sqrt{2}$",
   "figure": _fig_asa(),
   "explanation": r"""▶ 与えられたのが「角2つと辺1つ」。この形は<b>正弦定理</b>の出番。
正弦定理 $\frac{\mathrm{BC}}{\sin\mathrm{A}}=\frac{\mathrm{CA}}{\sin\mathrm{B}}=\frac{\mathrm{AB}}{\sin\mathrm{C}}=2R$ は、
<b>辺とその向かい合う角</b>をペアにして結ぶ式なので、
使う前に「どの辺とどの角がペアか」を図の上で確定させる。
① 求める $\mathrm{AB}$ の向かいは $\angle\mathrm{C}$、与えられた $\mathrm{CA}$ の向かいは $\angle\mathrm{B}$。
ペアが2組そろったので、<b>その2組だけ</b>を等号で結べばよい（$\angle\mathrm{A}$ は要らない）。
② $\frac{\mathrm{AB}}{\sin\mathrm{C}}=\frac{\mathrm{CA}}{\sin\mathrm{B}}$ より
$\mathrm{AB}=\mathrm{CA}\times\frac{\sin\mathrm{C}}{\sin\mathrm{B}}$。
③ 代入して $\mathrm{AB}=8\times\frac{\sin 30^\circ}{\sin 45^\circ}=8\times\frac{1}{2}\div\frac{\sqrt{2}}{2}$
$=8\times\frac{1}{2}\times\frac{2}{\sqrt{2}}=\frac{8}{\sqrt{2}}$。
④ 有理化して $\frac{8}{\sqrt{2}}=\frac{8\sqrt{2}}{2}=4\sqrt{2}$。
★ 事故の1位は<b>辺と角の対応を1つずらす</b>こと（$\frac{\mathrm{AB}}{\sin\mathrm{B}}$ と書いてしまう）。
辺 $\mathrm{AB}$ の向かいは $\mathrm{A}$ でも $\mathrm{B}$ でもなく<b>残った $\mathrm{C}$</b>。
図に「辺→向かいの角」の矢印を2本引いてから式を書く。
その場でできる検算は<b>大小の見当</b>: 三角形では小さい角の向かいほど辺が短い。
$\angle\mathrm{C}=30^\circ\lt\angle\mathrm{B}=45^\circ$ だから $\mathrm{AB}\lt\mathrm{CA}=8$ のはず。
$4\sqrt{2}\fallingdotseq 5.7\lt 8$ ✓ ——もし $8$ より大きい答えが出たら、ペアを取り違えている。""",
   "chk": lambda: (lambda P=_asa_pts(45, 30, 8):
                   sp.simplify(sp.sqrt(_dist2(P[0], P[2])) - 8) == 0
                   and sp.simplify(sp.sqrt(_dist2(P[0], P[1])) - 4*sqrt(2)) == 0)()},

  {"group": "角と向かい合う辺が分かっているとき", "level": "basic",
   "skill": "TR7", "sub": ["TR4", "TR3"],
   "stem": r"$\triangle\mathrm{ABC}$ で $\angle\mathrm{B}=135^\circ$、$\mathrm{CA}=7$ のとき、"
           r"$\triangle\mathrm{ABC}$ の外接円の半径 $R$ を求めよ。",
   "answer": r"$R=\dfrac{7\sqrt{2}}{2}$",
   "explanation": r"""▶ 外接円の半径は正弦定理の右端 $=2R$ の部分。
$\frac{\mathrm{CA}}{\sin\mathrm{B}}=2R$ なので、<b>辺と向かい合う角が1組わかれば $R$ は決まる</b>。
他の2辺も他の角も要らない、というのがこの式の強み。
① $\mathrm{CA}=7$ の向かいは $\angle\mathrm{B}=135^\circ$。ペアがそろっているので、この1組だけを使う。
② $2R=\frac{\mathrm{CA}}{\sin\mathrm{B}}=\frac{7}{\sin 135^\circ}$。
③ $135^\circ=180^\circ-45^\circ$ なので $\sin 135^\circ=\sin 45^\circ=\frac{\sqrt{2}}{2}$。
<b>鈍角の $\sin$ は補角に直す</b>（単位円で折り返しても $y$ 座標は変わらない）。
④ $2R=7\div\frac{\sqrt{2}}{2}=\frac{14}{\sqrt{2}}=7\sqrt{2}$。よって $R=\frac{7\sqrt{2}}{2}$。
★ 事故の1位は $\sin 135^\circ=-\frac{\sqrt{2}}{2}$ と符号をつけること。
$0^\circ\leqq\theta\leqq 180^\circ$ では<b>$\sin$ は常に $0$ 以上</b>で、負になれるのは $\cos$ と $\tan$ だけ。
$R$ が負に出たらまずここを疑う。
2位は $2R$ を求めたところで止めて、それを $R$ として答えること。
式の左辺が $2R$ である以上、<b>最後に $2$ で割る</b>。
検算: 三角形のどの辺も外接円の弦だから<b>直径 $2R$ より長くはなれない</b>。
$2R=7\sqrt{2}\fallingdotseq 9.9$ に対し $\mathrm{CA}=7$ で確かに短い ✓
さらに $\mathrm{CA}=2R\sin\mathrm{B}$ だから<b>辺は直径の $\sin$（向かいの角）倍</b>で、
$\sin 135^\circ\fallingdotseq 0.71$ より $9.9\times 0.71\fallingdotseq 7$ ✓
（<b>鈍角だから直径に近い、ではない</b>——$\sin$ は $90^\circ$ から離れるほど小さくなる）。""",
   "chk": lambda: all(sp.simplify(_circum_R(*_asa_pts(135, cd, 7)) - 7*sqrt(2)/2) == 0
                      for cd in (30, 15))},

  {"group": "2辺と挟む角から残りの辺", "level": "basic",
   "skill": "TR5", "sub": ["TR1"],
   "stem": r"右の図の $\triangle\mathrm{ABC}$ で、$\mathrm{AB}=15$、$\mathrm{AC}=7$、"
           r"$\angle\mathrm{A}=60^\circ$ である。辺 $\mathrm{BC}$ の長さを求めよ。",
   "answer": r"$\mathrm{BC}=13$",
   "figure": _fig_sas(),
   "explanation": r"""▶ 「2辺と<b>その2辺が挟む角</b>」がそろっているときは<b>余弦定理</b>。
$\mathrm{BC}^{2}=\mathrm{AB}^{2}+\mathrm{AC}^{2}-2\cdot\mathrm{AB}\cdot\mathrm{AC}\cos\mathrm{A}$ は
<b>三平方の定理に補正項 $-2\cdot\mathrm{AB}\cdot\mathrm{AC}\cos\mathrm{A}$ がついたもの</b>と見ると覚えやすい
（$\angle\mathrm{A}=90^\circ$ なら $\cos\mathrm{A}=0$ で補正項が消え、三平方の定理そのものに戻る）。
① 求める $\mathrm{BC}$ の向かいは $\angle\mathrm{A}$。その $\angle\mathrm{A}$ を挟む2辺 $\mathrm{AB},\ \mathrm{AC}$ が
与えられているので、余弦定理がそのまま使える形になっている。
② $\mathrm{BC}^{2}=15^{2}+7^{2}-2\times 15\times 7\times\cos 60^\circ$。
③ $\cos 60^\circ=\frac{1}{2}$ だから
$\mathrm{BC}^{2}=225+49-2\times 15\times 7\times\frac{1}{2}=274-105=169$。
④ $\mathrm{BC}\gt 0$ より $\mathrm{BC}=13$。
★ 事故が集中するのは③と④。③では $2\times 15\times 7=210$ まで出したところで<b>$\cos$ を掛け忘れて
$210$ を引く</b>ミス、④では<b>2乗を外し忘れて $169$ と答える</b>ミス。求めたのは長さであって長さの2乗ではない。
検算は角の大きさから: $\angle\mathrm{A}=60^\circ\lt 90^\circ$ なので、直角のとき
（$\sqrt{225+49}=\sqrt{274}\fallingdotseq 16.6$）より $\mathrm{BC}$ は<b>短い</b>はず。$13\lt 16.6$ ✓
挟む角が小さいほど向かいの辺は短い、を毎回この形で確かめる。""",
   "chk": lambda: (sp.simplify(sp.sqrt(_dist2(*_sas_pts(15, 7, 60)[1:])) - 13) == 0
                   and sp.simplify(_heron(7, 15, 13) - R(1, 2)*15*7*sp.sin(sp.rad(60))) == 0)},

  {"group": "2辺と挟む角から残りの辺", "level": "standard",
   "skill": "TR5", "sub": ["TR3"],
   "stem": r"$\triangle\mathrm{ABC}$ で $\mathrm{AB}=3$、$\mathrm{BC}=9$、$\angle\mathrm{B}=120^\circ$ "
           r"のとき、辺 $\mathrm{CA}$ の長さを求めよ。",
   "answer": r"$\mathrm{CA}=3\sqrt{13}$",
   "explanation": r"""▶ 挟む角が鈍角でも式はまったく同じ。ただし $\cos 120^\circ$ が<b>負</b>なので、
補正項の符号が反転して「三平方より長くなる」——ここが前問との唯一の違い。
① 求める $\mathrm{CA}$ の向かいは $\angle\mathrm{B}$。挟む2辺 $\mathrm{BA}=3,\ \mathrm{BC}=9$ がそろっている。
② $\mathrm{CA}^{2}=\mathrm{BA}^{2}+\mathrm{BC}^{2}-2\cdot\mathrm{BA}\cdot\mathrm{BC}\cos\mathrm{B}$
$=3^{2}+9^{2}-2\times 3\times 9\times\cos 120^\circ$。
③ $120^\circ=180^\circ-60^\circ$ なので $\cos 120^\circ=-\cos 60^\circ=-\frac{1}{2}$。
④ $-2\times 3\times 9\times\left(-\frac{1}{2}\right)=+27$ となり、<b>引くはずが足すことになる</b>。
$\mathrm{CA}^{2}=9+81+27=117$。
⑤ $\mathrm{CA}=\sqrt{117}=\sqrt{9\times 13}=3\sqrt{13}$。
★ 事故の1位は $\cos 120^\circ=+\frac{1}{2}$ として $\mathrm{CA}^{2}=90-27=63$ としてしまうこと。
<b>鈍角の $\cos$ は必ず負</b>（単位円で $x$ 座標が左側に来る）。
$90^\circ$ を超えた角を見たら、計算に入る前に式の横へ「$\cos\lt 0$」とメモしておく。
2位は⑤で $\sqrt{117}$ のまま答えること。<b>根号の中に平方数が残っていないか</b>を最後に必ず見る
（$117=9\times 13$ の $9$ に気づけるかどうか）。
検算: $\angle\mathrm{B}=120^\circ\gt 90^\circ$ だから、直角のとき $\sqrt{9+81}=\sqrt{90}\fallingdotseq 9.5$ より
$\mathrm{CA}$ は<b>長い</b>はず。$3\sqrt{13}\fallingdotseq 10.8\gt 9.5$ ✓""",
   "chk": lambda: (sp.simplify(sp.sqrt(_dist2(*_sas_pts(3, 9, 120)[1:])) - 3*sqrt(13)) == 0
                   and sp.simplify(_heron(3, 9, 3*sqrt(13))
                                   - R(1, 2)*3*9*sp.sin(sp.rad(120))) == 0)},

  {"group": "3辺がわかっているとき", "level": "standard",
   "skill": "TR5", "sub": ["TR1"],
   "stem": r"$\triangle\mathrm{ABC}$ で $\mathrm{BC}=5$、$\mathrm{CA}=8$、$\mathrm{AB}=7$ のとき、"
           r"$\angle\mathrm{C}$ の大きさを求めよ。",
   "answer": r"$\angle\mathrm{C}=60^\circ$",
   "explanation": r"""▶ 3辺が全部わかっているときは<b>余弦定理を角について解いた形</b>を使う。
$\cos\mathrm{C}=\frac{\mathrm{CB}^{2}+\mathrm{CA}^{2}-\mathrm{AB}^{2}}{2\cdot\mathrm{CB}\cdot\mathrm{CA}}$。
分子は「<b>角を挟む2辺の2乗の和</b> ひく <b>向かいの辺の2乗</b>」——この並びを口で言えるようにしておくと、
どの辺を引くのかで迷わなくなる。
① $\angle\mathrm{C}$ を挟む2辺は $\mathrm{CB}=5,\ \mathrm{CA}=8$、向かい合う辺は $\mathrm{AB}=7$。
② $\cos\mathrm{C}=\frac{5^{2}+8^{2}-7^{2}}{2\times 5\times 8}=\frac{25+64-49}{80}=\frac{40}{80}=\frac{1}{2}$。
③ $0^\circ\lt\mathrm{C}\lt 180^\circ$ でこの値をとるのは $\mathrm{C}=60^\circ$ だけ。よって $\angle\mathrm{C}=60^\circ$。
★ 覚えるべきは<b>分子の符号がそのまま角の種類</b>だということ。
正なら鋭角、$0$ ちょうどなら直角、負なら鈍角。ここが分かっていると、
分子が負に出たときに「計算ミスだ」と思って符号を書き直す事故が起きない（負は結論であって誤りではない）。
今回は分子 $+40$ なので鋭角、という予測が③の $60^\circ$ と合っている。
その場でできる検算は2つ。1つ目は<b>直角との比較</b>: $\angle\mathrm{C}$ が直角なら
$\mathrm{AB}=\sqrt{25+64}=\sqrt{89}\fallingdotseq 9.4$ のはずで、実際の $\mathrm{AB}=7$ はそれより短い。
よって $\angle\mathrm{C}\lt 90^\circ$ ✓
2つ目は<b>逆向きに戻す</b>こと: $25+64-2\times 5\times 8\times\frac{1}{2}=89-40=49=7^{2}$ となり、
$\mathrm{AB}=7$ に戻る ✓ ——分数の約分ミスはここで確実に見つかる。""",
   "chk": lambda: (lambda P=_sss_pts(5, 8, 7):
                   _dist2(P[1], P[2]) == 25 and _dist2(P[2], P[0]) == 64
                   and _dist2(P[0], P[1]) == 49
                   and _is_deg(P[2], P[0], P[1], 60)
                   and sp.simplify(2*_heron(5, 8, 7)/(5*8) - sp.sin(sp.rad(60))) == 0)()},

  {"group": "3辺がわかっているとき", "level": "standard",
   "skill": "TR7", "sub": ["TR5", "TR4"],
   "stem": r"右の図の $\triangle\mathrm{ABC}$ で、$\mathrm{AB}=6$、$\mathrm{BC}=14$、$\mathrm{CA}=10$ である。"
           r"$\angle\mathrm{A}$ の大きさと、$\triangle\mathrm{ABC}$ の外接円の半径 $R$ を求めよ。",
   "answer": r"$\angle\mathrm{A}=120^\circ$、$R=\dfrac{14\sqrt{3}}{3}$",
   "figure": _fig_sss(),
   "explanation": r"""▶ 2つの定理は<b>手持ちの情報で選ぶ</b>。
辺の情報しか無いときは余弦定理、<b>角とその向かいの辺がペアでそろっているとき</b>は正弦定理。
いまは辺が3つあるだけで角が1つも無いので、まず余弦定理で角を作り、ペアを手に入れてから正弦定理に渡す。
① $\angle\mathrm{A}$ を挟む2辺は $\mathrm{AB}=6,\ \mathrm{AC}=10$、向かい合う辺は $\mathrm{BC}=14$。
$\cos\mathrm{A}=\frac{6^{2}+10^{2}-14^{2}}{2\times 6\times 10}=\frac{36+100-196}{120}$
$=\frac{-60}{120}=-\frac{1}{2}$。
② 分子が負なので鈍角。$0^\circ\lt\mathrm{A}\lt 180^\circ$ より $\angle\mathrm{A}=120^\circ$。
③ これで「$\angle\mathrm{A}=120^\circ$ と、その向かいの辺 $\mathrm{BC}=14$」というペアができた。
正弦定理 $\frac{\mathrm{BC}}{\sin\mathrm{A}}=2R$ に入れる。$\sin 120^\circ=\sin 60^\circ=\frac{\sqrt{3}}{2}$ だから
$2R=14\div\frac{\sqrt{3}}{2}=\frac{28}{\sqrt{3}}=\frac{28\sqrt{3}}{3}$。
④ よって $R=\frac{14\sqrt{3}}{3}$。
★ この問題の骨は③。<b>正弦定理は「角と対辺のペア」が1組できるまで使えない</b>。
手が止まったら、まず<b>与えられた情報の中にペアがあるか</b>を確認し、無ければ余弦定理でペアを作りに行く
——この一手が定理の使い分けの正体で、覚える順番はこれだけでよい。
なお②で $\cos$ は負でも③で $\sin$ は正、という切り替えを落とさないこと。
仕上げの注意は $2R$ のまま答えないことと、分母に根号を残さないことの2つ。
検算: どの辺も直径 $2R=\frac{28\sqrt{3}}{3}\fallingdotseq 16.2$ を超えられない。最大辺は $\mathrm{BC}=14$ で
$14\lt 16.2$ ✓ しかも<b>最大角の向かいが最大辺</b>だから、最大角 $\angle\mathrm{A}=120^\circ$ の向かいの
$\mathrm{BC}$ が3辺 $6,\ 10,\ 14$ の中で最大、という形とも合う ✓""",
   "chk": lambda: (lambda P=_sss_pts(14, 10, 6):
                   _dist2(P[0], P[1]) == 36 and _dist2(P[1], P[2]) == 196
                   and _dist2(P[2], P[0]) == 100
                   and _is_deg(P[0], P[1], P[2], 120)
                   and sp.simplify(_circum_R(*P) - 14*sqrt(3)/3) == 0)()},

  {"group": "与えられた角が挟む角でないとき", "level": "advanced",
   "skill": "TR5", "sub": ["QF6"],
   "stem": r"$\triangle\mathrm{ABC}$ で $\angle\mathrm{A}=60^\circ$、$\mathrm{CA}=5$、"
           r"$\mathrm{BC}=\sqrt{21}$ のとき、辺 $\mathrm{AB}$ の長さを求めよ。",
   "answer": r"$\mathrm{AB}=1$ または $\mathrm{AB}=4$",
   "explanation": r"""▶ 与えられた $\angle\mathrm{A}$ は、$\mathrm{CA}$ と $\mathrm{BC}$ が<b>挟む角になっていない</b>
（$\mathrm{BC}$ は $\angle\mathrm{A}$ の向かい側にある）。この形では余弦定理を、そのまま計算する式としてではなく
<b>求める辺を文字において2次方程式を立てる道具</b>として使う。
① $\mathrm{AB}=x$ とおく。$\angle\mathrm{A}$ を挟む2辺は $\mathrm{AB}=x$ と $\mathrm{AC}=5$、向かいは $\mathrm{BC}=\sqrt{21}$。
余弦定理より $(\sqrt{21})^{2}=x^{2}+5^{2}-2\times x\times 5\times\cos 60^\circ$。
② $\cos 60^\circ=\frac{1}{2}$ を入れて $21=x^{2}+25-5x$、整理して $x^{2}-5x+4=0$。
③ 因数分解して $(x-1)(x-4)=0$ より $x=1,\ 4$。
④ <b>ここで片方を捨てない</b>。$x\gt 0$ はどちらも満たし、3辺
$(\sqrt{21},\ 5,\ 1)$ と $(\sqrt{21},\ 5,\ 4)$ はどちらも三角形の成立条件を満たす
（$1+\sqrt{21}\fallingdotseq 5.6\gt 5$）。よって $\mathrm{AB}=1,\ 4$ の<b>2つとも答え</b>。
★ この型の失点はほぼ全部④で起きる。「答えは1つのはず」という思い込みで小さいほうを不適にしてしまう。
捨ててよいのは<b>負の解</b>と<b>三角形が作れない解</b>だけで、判定は必ず三角形の成立条件で行う。
なぜ2つになるかは図を描けば見える: $\angle\mathrm{A}=60^\circ$ の一方の辺の上に、
$\mathrm{C}$ を中心とする半径 $\sqrt{21}$ の円をかくと<b>2点で交わる</b>。
交わる条件は $5\sin 60^\circ=\frac{5\sqrt{3}}{2}\fallingdotseq 4.33\lt\sqrt{21}\fallingdotseq 4.58\lt 5$
（半径が $\mathrm{C}$ から辺までの距離より大きく、$\mathrm{CA}$ より小さい）。
検算は<b>両方を元の式に戻す</b>こと: $x=1$ なら $1+25-5=21$ ✓、$x=4$ なら $16+25-20=21$ ✓。
2つとも $(\sqrt{21})^{2}$ に戻るので、どちらも本物の解だと確認できる。""",
   "chk": lambda: (lambda u=sp.Symbol('u', positive=True):
                   sorted(sp.solve(sp.Eq(_dist2(*_sas_pts(u, 5, 60)[1:]), 21), u)) == [1, 4])()},
 ]}
