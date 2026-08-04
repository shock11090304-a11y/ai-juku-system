# -*- coding: utf-8 -*-
"""数学A「図形の性質」「整数の性質」基礎徹底問題集の内容（単一ソース・教科書LaTeX組版用）。

既存の content_kiso.py（確率・数列・ベクトル）と同じ構造。これで数Aの残り2分野が埋まる。
数式は $...$ の LaTeX（日本語は $ の外）。各問の chk は sympy 等で答えを独立再計算して True を返す
（verify_kisoA.py が全問実行する）。

■ ★新課程での位置づけ（作る前に確認した。学年で入れ替わるので毎回確認すること）
  ・「図形の性質」…… 数Aの単元として現行課程にも存在。2025年度以降の共通テストでは
    「場合の数と確率」とともに【必答】になった（旧課程の選択問題は廃止）。
  ・「整数の性質」…… 現行課程では数Aの単元名として存在せず、内容は
    数A「数学と人間の活動」と数I「数と式」に分散した。
    そのため 2025年度以降の共通テストでは出題範囲外。
    ただし国公立2次・私大の個別試験では整数問題は頻出のままなので本書に収録する。
    → この事情は冊子の整数編の扉に明記する（生徒が「共テに出る」と誤解しないため）。
"""
import sympy as sp
from sympy import Rational as R, sqrt, gcd, lcm, divisors, factorint, igcd

# ---------------------------------------------------------------- 検算用ヘルパ
def _eq(a, b):
    """sympy で厳密に等しいか（数値誤差に頼らない）。"""
    return sp.simplify(sp.nsimplify(a) - sp.nsimplify(b)) == 0


def _tri_area(ax, ay, bx, by, cx, cy):
    return sp.Abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2


def _dist(p, q):
    return sp.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)


# ---- 図形問題は「定理に代入して確かめる」だけだと、そもそも図が成立しない設定を見逃す。
#      （初版で、直線DEと直線ACが平行になり交点が存在しないメネラウス問題を出してしまった）
#      実際に座標をとって交点を求め、比を実測するヘルパを用意する。
P = sp.Point


def _div(a, b, m, n):
    """線分 ab を m:n に内分する点。"""
    return a + (b - a) * R(m, m + n)


def _bisector_ratio(a, b, c):
    """∠a の二等分線と辺 bc の交点 d を作図し、bd:dc を実測して返す。
    二等分線は「ab方向の単位ベクトル + ac方向の単位ベクトル」の向き（＝ひし形の対角線）。
    角の二等分線の定理を使わないので、定理の検算として独立している。"""
    ub = sp.Matrix([b[0] - a[0], b[1] - a[1]]) / a.distance(b)
    uc = sp.Matrix([c[0] - a[0], c[1] - a[1]]) / a.distance(c)
    dirv = sp.simplify(ub + uc)
    d = sp.Line(a, a + sp.Point(dirv[0], dirv[1])).intersection(sp.Segment(b, c))[0]
    return sp.simplify(b.distance(d) / d.distance(c))


def _ext_bisector_ratio(a, b, c):
    """∠a の外角の二等分線と直線 bc の交点 e を作図し、be:ec を実測して返す。
    外角の二等分線の向きは「ab方向の単位ベクトル − ac方向の単位ベクトル」。"""
    ub = sp.Matrix([b[0] - a[0], b[1] - a[1]]) / a.distance(b)
    uc = sp.Matrix([c[0] - a[0], c[1] - a[1]]) / a.distance(c)
    dirv = sp.simplify(ub - uc)
    e = sp.Line(a, a + sp.Point(dirv[0], dirv[1])).intersection(sp.Line(b, c))[0]
    return sp.simplify(b.distance(e) / e.distance(c))


def _area_ratio_ap_ab(a, b, c, m, n):
    """辺 ab を m:n に内分する点 p をとり、△apc と △abc の面積比を実測して返す。"""
    p = _div(a, b, m, n)
    return sp.simplify(sp.Triangle(a, p, c).area / sp.Triangle(a, b, c).area)


def _circle_relation(d, r1, r2):
    """中心間距離 d と半径から2円の位置関係を判定して日本語で返す（答えそのものを計算する）。"""
    if d > r1 + r2:
        return "離れている"
    if d == r1 + r2:
        return "外接する"
    if d > abs(r1 - r2):
        return "2点で交わる"
    if d == abs(r1 - r2):
        return "内接する"
    return "一方が他方の内部にある"


def _to_base(n, b):
    """10進数 n を b 進法の文字列にする（答えそのものを計算する）。"""
    if n == 0:
        return "0"
    out = ""
    while n:
        n, r = divmod(n, b)
        out = str(r) + out
    return out


def _cross_ratio(line_p, line_q, on):
    """直線 line_p line_q と、直線 on（2点タプル）の交点を求め、on の2点からの距離比を返す。
    交点が存在しなければ None（＝問題として成立していない合図）。"""
    hits = sp.Line(line_p, line_q).intersection(sp.Line(*on))
    if not hits or not isinstance(hits[0], sp.Point2D):
        return None
    f = hits[0]
    return on[0].distance(f) / f.distance(on[1])


# ================================================================ 図形の性質
U_HIRITSU = {
    "name": "三角形と線分の比",
    "tag": "角の二等分線・中点連結・平行線と比",
    "problems": [
        {"group": "平行線と線分の比", "level": "basic",
         "stem": r"$\triangle ABC$ で、辺 $AB$ 上に点 $D$、辺 $AC$ 上に点 $E$ があり "
                 r"$DE \parallel BC$ である。$AD=3$, $DB=2$, $AE=4$ のとき、$EC$ の長さを求めよ。",
         "answer": r"$EC=\dfrac{8}{3}$",
         "explanation": r"$DE \parallel BC$ より $AD:DB=AE:EC$。"
                        r"$3:2=4:EC$ だから $3\,EC=8$、よって $EC=\dfrac{8}{3}$。",
         "av": R(8, 3), "chk": lambda av: _eq(R(2 * 4, 3), av)},
        {"group": "平行線と線分の比", "level": "basic",
         "stem": r"$\triangle ABC$ の辺 $AB$ 上に点 $D$、辺 $AC$ 上に点 $E$ があり "
                 r"$DE \parallel BC$ である。$AD=4$, $AB=6$, $BC=9$ のとき、"
                 r"$DE$ の長さを求めよ。",
         "answer": r"$DE=6$",
         "explanation": r"$\triangle ADE \sim \triangle ABC$（2角が等しい）で相似比は "
                        r"$AD:AB=4:6=2:3$。よって $DE=9\times\dfrac{2}{3}=6$。",
         "av": 6, "chk": lambda av: _eq(9 * R(4, 6), av)},
        {"group": "中点連結定理", "level": "basic",
         "stem": r"$\triangle ABC$ で、辺 $AB$, $AC$ の中点をそれぞれ $M$, $N$ とする。"
                 r"$BC=10$ のとき $MN$ の長さを求めよ。",
         "answer": r"$MN=5$",
         "explanation": r"中点連結定理より $MN \parallel BC$ かつ $MN=\dfrac{1}{2}BC$。"
                        r"よって $MN=5$。",
         "av": 5, "chk": lambda av: _eq(R(10, 2), av)},
        {"group": "角の二等分線と比", "level": "basic",
         "stem": r"$\triangle ABC$ で $AB=6$, $AC=4$ とする。$\angle A$ の二等分線と辺 $BC$ の"
                 r"交点を $D$ とするとき、$BD:DC$ を最も簡単な整数比で求めよ。",
         "answer": r"$BD:DC=3:2$",
         "explanation": r"内角の二等分線の定理より $BD:DC=AB:AC=6:4=3:2$。",
         # ★定理を代入し直すのは検算ではない（同じ式をもう一度書くだけ）。
         #   単位ベクトルの和で二等分線を「作図」し、BC との交点を実際に求めて比を実測する。
         "av": R(3, 2), "chk": lambda av: _eq(_bisector_ratio(P(0, 0), P(6, 0), P(0, 4)), av)},
        {"group": "角の二等分線と比", "level": "standard",
         "stem": r"$\triangle ABC$ で $AB=8$, $AC=6$, $BC=7$ とする。$\angle A$ の二等分線と"
                 r"辺 $BC$ の交点を $D$ とするとき、$BD$ の長さを求めよ。",
         "answer": r"$BD=4$",
         "explanation": r"$BD:DC=AB:AC=8:6=4:3$ で $BD+DC=7$。"
                        r"よって $BD=7\times\dfrac{4}{4+3}=4$。",
         "av": 4, "chk": lambda av: _eq(7 * R(4, 7), av)},
        {"group": "角の二等分線と比", "level": "standard",
         "stem": r"$\triangle ABC$ で $AB=5$, $AC=3$ とする。$\angle A$ の外角の二等分線と"
                 r"直線 $BC$ の交点を $E$ とするとき、$BE:EC$ を最も簡単な整数比で求めよ。",
         "answer": r"$BE:EC=5:3$",
         "explanation": r"外角の二等分線の定理より $BE:EC=AB:AC=5:3$。"
                        r"（点 $E$ は辺 $BC$ の外側、$C$ 側の延長上にある。）",
         # ★恒真だった(_eq(R(5,3), R(5,3)))。外角の二等分線を作図して交点を実測する。
         "av": R(5, 3), "chk": lambda av: _eq(_ext_bisector_ratio(P(0, 0), P(5, 0),
                                                                  P(0, 3)), av)},
        {"group": "重心", "level": "basic",
         "stem": r"$\triangle ABC$ の重心を $G$、辺 $BC$ の中点を $M$ とする。"
                 r"$AM=9$ のとき $AG$ の長さを求めよ。",
         "answer": r"$AG=6$",
         "explanation": r"重心は中線を頂点から $2:1$ に内分する。よって "
                        r"$AG=9\times\dfrac{2}{3}=6$（$GM=3$）。",
         "av": 6, "chk": lambda av: _eq(9 * R(2, 3), av)},
        {"group": "重心", "level": "standard",
         "stem": r"$A(0,\,0)$, $B(6,\,0)$, $C(3,\,6)$ とする。$\triangle ABC$ の重心 $G$ の"
                 r"座標を求めよ。",
         "answer": r"$G(3,\,2)$",
         "explanation": r"重心の座標は3頂点の平均。"
                        r"$\left(\dfrac{0+6+3}{3},\ \dfrac{0+0+6}{3}\right)=(3,\,2)$。",
         "av": 3, "chk": lambda av: (_eq(R(0 + 6 + 3, 3), av) and _eq(R(0 + 0 + 6, 3), 2))},
        {"group": "証明の型", "level": "advanced",
         "stem": r"$\triangle ABC$ の辺 $AB$, $AC$ の中点をそれぞれ $M$, $N$ とするとき、"
                 r"$MN \parallel BC$ かつ $MN=\dfrac{1}{2}BC$ となることを、相似を用いて証明せよ。",
         "answer": r"$\triangle AMN$ と $\triangle ABC$ で $AM:AB=AN:AC=1:2$、"
                   r"$\angle A$ が共通だから2辺の比とその間の角が等しく相似（相似比 $1:2$）。"
                   r"よって $\angle AMN=\angle ABC$ より $MN \parallel BC$、"
                   r"また $MN:BC=1:2$ より $MN=\dfrac{1}{2}BC$。",
         "explanation": r"▶ 中点連結定理の証明。相似の「2辺の比とその間の角」を使う。"
                        r"①$M$, $N$ は中点なので $AM:AB=1:2$, $AN:AC=1:2$。"
                        r"②$\angle A$ は共通。よって $\triangle AMN \sim \triangle ABC$（相似比 $1:2$）。"
                        r"③相似だから $\angle AMN=\angle ABC$。同位角が等しいので $MN \parallel BC$。"
                        r"④相似比より $MN:BC=1:2$、すなわち $MN=\dfrac{1}{2}BC$。"
                        r"★「平行」と「長さ半分」の2つを両方示す必要がある。片方だけで終わらない。",
         "chk": None},
        {"group": "面積比", "level": "standard",
         "stem": r"$\triangle ABC$ で、辺 $AB$ を $2:1$ に内分する点を $P$ とする。"
                 r"$\triangle APC$ と $\triangle ABC$ の面積比を最も簡単な整数比で求めよ。",
         "answer": r"$\triangle APC:\triangle ABC=2:3$",
         "explanation": r"$AP:AB=2:3$ で、頂点 $C$ から $AB$ までの高さは共通。"
                        r"底辺の比がそのまま面積比になるので $2:3$。",
         # ★恒真だった(_eq(R(2,3), R(2,3)))。座標で2つの三角形の面積を実測して比を出す。
         "av": R(2, 3), "chk": lambda av: _eq(_area_ratio_ap_ab(P(0, 0), P(9, 1),
                                                                P(2, 7), 2, 1), av)},
        {"group": "面積比", "level": "advanced",
         "stem": r"$\triangle ABC$ で、辺 $AB$ を $1:2$ に内分する点を $D$、辺 $AC$ を "
                 r"$3:1$ に内分する点を $E$ とする。$\triangle ADE$ と $\triangle ABC$ の"
                 r"面積比を最も簡単な整数比で求めよ。",
         "answer": r"$\triangle ADE:\triangle ABC=1:4$",
         "explanation": r"$\angle A$ を共有する2つの三角形の面積比は "
                        r"$\dfrac{AD}{AB}\cdot\dfrac{AE}{AC}$。"
                        r"$\dfrac{1}{3}\times\dfrac{3}{4}=\dfrac{1}{4}$ より $1:4$。",
         "av": R(1, 4), "chk": lambda av: _eq(R(1, 3) * R(3, 4), av)},
    ],
}

U_GOSHIN = {
    "name": "三角形の五心とチェバ・メネラウス",
    "tag": "外心・内心・重心・垂心・傍心／チェバ・メネラウスの定理",
    "problems": [
        {"group": "外心", "level": "basic",
         "stem": r"$\triangle ABC$ の外心を $O$ とする。$O$ はどのような線の交点か。"
                 r"次から選べ。　(ア) 3辺の垂直二等分線　(イ) 3つの内角の二等分線　"
                 r"(ウ) 3本の中線　(エ) 3本の垂線",
         "answer": r"(ア) 3辺の垂直二等分線",
         "explanation": r"外心は3辺の垂直二等分線の交点で、3頂点から等距離"
                        r"（$OA=OB=OC$＝外接円の半径）。"
                        r"(イ)は内心、(ウ)は重心、(エ)は垂心。",
         "chk": None},
        {"group": "外心", "level": "standard",
         "stem": r"鋭角三角形 $ABC$ の外心を $O$ とする。$\angle OBC=25^\circ$, "
                 r"$\angle OCA=35^\circ$ のとき、$\angle OAB$ の大きさを求めよ。",
         "answer": r"$\angle OAB=30^\circ$",
         "explanation": r"$OA=OB=OC$ より $\triangle OBC$, $\triangle OCA$, $\triangle OAB$ は"
                        r"すべて二等辺三角形。$\angle OBC=\angle OCB=25^\circ$、"
                        r"$\angle OCA=\angle OAC=35^\circ$、$\angle OAB=\angle OBA=x$ とおくと、"
                        r"三角形の内角の和より $2(25+35+x)=180$。よって $x=30^\circ$。"
                        r"（この式は $O$ が三角形の内部にある＝鋭角三角形のときに成り立つ。"
                        r"鈍角三角形だと $O$ が外に出て $80^\circ$ になるので、"
                        r"問題文の「鋭角三角形」が効いている。）",
         "av": 30, "chk": lambda av: _eq(sp.solve(sp.Eq(2 * (25 + 35 + sp.Symbol('x')), 180))[0], av)},
        {"group": "内心", "level": "standard",
         "stem": r"$\triangle ABC$ の内心を $I$ とする。$\angle A=70^\circ$ のとき、"
                 r"$\angle BIC$ の大きさを求めよ。",
         "answer": r"$\angle BIC=125^\circ$",
         "explanation": r"$\angle BIC=90^\circ+\dfrac{\angle A}{2}$。"
                        r"$90+\dfrac{70}{2}=125^\circ$。"
                        r"（$\angle IBC+\angle ICB=\dfrac{B+C}{2}=\dfrac{180-70}{2}=55^\circ$ から"
                        r"$180-55=125^\circ$ と導いてもよい。）",
         "av": 125, "chk": lambda av: _eq(90 + R(70, 2), av)},
        {"group": "内心", "level": "standard",
         "stem": r"$\triangle ABC$ で $AB=5$, $BC=6$, $CA=7$、内接円の半径を $r$ とする。"
                 r"$\triangle ABC$ の面積が $6\sqrt{6}$ のとき、$r$ を求めよ。",
         "answer": r"$r=\dfrac{2\sqrt{6}}{3}$",
         "explanation": r"$S=\dfrac{1}{2}r(a+b+c)$ より "
                        r"$6\sqrt{6}=\dfrac{1}{2}r(5+6+7)=9r$。"
                        r"よって $r=\dfrac{6\sqrt{6}}{9}=\dfrac{2\sqrt{6}}{3}$。",
         "av": 2 * sqrt(6) / 3, "chk": lambda av: _eq(6 * sqrt(6) / R(5 + 6 + 7, 2), av)},
        {"group": "チェバの定理", "level": "basic",
         "stem": r"$\triangle ABC$ の内部の点 $O$ について、直線 $AO$, $BO$, $CO$ が"
                 r"辺 $BC$, $CA$, $AB$ と交わる点を $P$, $Q$, $R$ とする。"
                 r"$BP:PC=2:3$, $CQ:QA=3:1$ のとき、$AR:RB$ を最も簡単な整数比で求めよ。",
         "answer": r"$AR:RB=1:2$",
         "explanation": r"チェバの定理 "
                        r"$\dfrac{BP}{PC}\cdot\dfrac{CQ}{QA}\cdot\dfrac{AR}{RB}=1$ より "
                        r"$\dfrac{2}{3}\cdot\dfrac{3}{1}\cdot\dfrac{AR}{RB}=1$。"
                        r"よって $\dfrac{AR}{RB}=\dfrac{1}{2}$。",
         "av": R(1, 2), "chk": lambda av: _eq(1 / (R(2, 3) * R(3, 1)), av)},
        {"group": "チェバの定理", "level": "standard",
         "stem": r"$\triangle ABC$ の内部の点 $O$ について、直線 $AO$, $BO$, $CO$ が"
                 r"辺 $BC$, $CA$, $AB$ と交わる点をそれぞれ $P$, $Q$, $R$ とする。"
                 r"$BP:PC=1:2$, $AR:RB=3:2$ のとき、$CQ:QA$ を最も簡単な整数比で求めよ。",
         "answer": r"$CQ:QA=4:3$",
         "explanation": r"$\dfrac{1}{2}\cdot\dfrac{CQ}{QA}\cdot\dfrac{3}{2}=1$ より "
                        r"$\dfrac{CQ}{QA}=\dfrac{4}{3}$。",
         "av": R(4, 3), "chk": lambda av: _eq(1 / (R(1, 2) * R(3, 2)), av)},
        {"group": "メネラウスの定理", "level": "standard",
         "stem": r"$\triangle ABC$ で、辺 $AB$ を $2:1$ に内分する点を $D$、"
                 r"辺 $BC$ を $2:1$ に内分する点を $E$ とする。直線 $DE$ と直線 $AC$ の交点を "
                 r"$F$ とするとき、$AF:FC$ を最も簡単な整数比で求めよ。",
         "answer": r"$AF:FC=4:1$",
         "explanation": r"$\triangle ABC$ と直線 $DEF$ にメネラウスの定理を使う。"
                        r"$\dfrac{AD}{DB}\cdot\dfrac{BE}{EC}\cdot\dfrac{CF}{FA}=1$ より "
                        r"$\dfrac{2}{1}\cdot\dfrac{2}{1}\cdot\dfrac{CF}{FA}=1$、"
                        r"すなわち $\dfrac{CF}{FA}=\dfrac{1}{4}$。"
                        r"点 $F$ は辺 $AC$ を $C$ の側に延長した位置にあり、$AF:FC=4:1$。"
                        r"（$A(0,0)$, $B(3,0)$, $C(0,3)$ とおくと $D(2,0)$, $E(1,2)$、"
                        r"直線 $DE$ と $y$ 軸の交点は $F(0,4)$ で、たしかに $AF=4$, $FC=1$。）",
         # ★座標で交点を実際に求めて比を実測する。
         #   初版は BE:EC=1:2 としており、DE と AC が平行になって交点が存在しない
         #   （＝解けない問題）だった。図形問題こそ座標で機械検算する。
         "av": 4, "chk": lambda av: _eq(_cross_ratio(
             _div(P(0, 0), P(3, 0), 2, 1),      # D: AB を 2:1
             _div(P(3, 0), P(0, 3), 2, 1),      # E: BC を 2:1
             (P(0, 0), P(0, 3))), av)},          # 直線AC 上での AF:FC
        {"group": "メネラウスの定理", "level": "standard",
         "stem": r"$\triangle ABC$ で、辺 $AB$ の中点を $M$、辺 $AC$ を $2:1$ に内分する点を "
                 r"$N$ とする。直線 $MN$ と直線 $BC$ の交点を $P$ とするとき、"
                 r"$BP:PC$ を最も簡単な整数比で求めよ。",
         "answer": r"$BP:PC=2:1$",
         "explanation": r"メネラウスの定理を $\triangle ABC$ と直線 $MNP$ に使うと "
                        r"$\dfrac{AM}{MB}\cdot\dfrac{BP}{PC}\cdot\dfrac{CN}{NA}=1$。"
                        r"$\dfrac{AM}{MB}=1$、$\dfrac{CN}{NA}=\dfrac{1}{2}$ だから "
                        r"$\dfrac{BP}{PC}=2$。よって $BP:PC=2:1$。"
                        r"（$M$, $N$ がともに辺の内部にあるので、点 $P$ は線分 $BC$ 上ではなく、"
                        r"$C$ の側の延長上にある。図をかくときに注意。）",
         # 定理の計算に加え、座標で交点Pを実際に求めて比を実測する
         "av": 2, "chk": lambda av: _eq(_cross_ratio(
             P(2, 0),                            # M: AB の中点
             _div(P(0, 0), P(0, 3), 2, 1),       # N: AC を 2:1
             (P(4, 0), P(0, 3))), av)},           # 直線BC 上での BP:PC
        {"group": "五心のあと2つ", "level": "basic",
         "stem": r"$\triangle ABC$ の各頂点から対辺（またはその延長）に下ろした3本の垂線は"
                 r"1点で交わる。この点を何というか。",
         "answer": r"垂心",
         "explanation": r"三角形の五心は 外心・内心・重心・垂心・傍心。"
                        r"垂心は鋭角三角形では内部、直角三角形では直角の頂点、"
                        r"鈍角三角形では外部にある。",
         "chk": None},
        {"group": "五心のあと2つ", "level": "standard",
         "stem": r"$\triangle ABC$ で $\angle B=90^\circ$ のとき、垂心はどの点か。"
                 r"次から選べ。　(ア) 点 $A$　(イ) 点 $B$　(ウ) 辺 $AC$ の中点　"
                 r"(エ) $\triangle ABC$ の外部の点",
         "answer": r"(イ) 点 $B$",
         "explanation": r"$A$ からの垂線は辺 $BC$ 上、$C$ からの垂線は辺 $AB$ 上を通り、"
                        r"どちらも直角の頂点 $B$ を通る。よって垂心は $B$。"
                        r"（このとき外心は斜辺 $AC$ の中点。）",
         "chk": None},
        {"group": "五心のあと2つ", "level": "standard",
         "stem": r"1つの内角の二等分線と、他の2つの外角の二等分線が交わる点を何というか。"
                 r"また、その点は1つの三角形にいくつあるか。",
         "answer": r"傍心。1つの三角形に3つある",
         "explanation": r"傍心は三角形の外側にあり、1辺と他の2辺の延長に接する円"
                        r"（傍接円）の中心。頂点 $A$, $B$, $C$ に対応して3つある。",
         "chk": None},
        {"group": "五心の判別", "level": "basic",
         "stem": r"次の点のうち、必ず三角形の内部にあるとは限らないものをすべて選べ。"
                 r"　(ア) 重心　(イ) 内心　(ウ) 外心　(エ) 垂心",
         "answer": r"(ウ) 外心、(エ) 垂心",
         "explanation": r"重心と内心はつねに内部にある。外心と垂心は、鈍角三角形では外部に、"
                        r"直角三角形では外心が斜辺の中点・垂心が直角の頂点に来る。",
         "chk": None},
        {"group": "五心の判別", "level": "standard",
         "stem": r"直角三角形 $ABC$（$\angle A=90^\circ$, $AB=3$, $AC=4$）の外接円の"
                 r"半径を求めよ。",
         "answer": r"$\dfrac{5}{2}$",
         "explanation": r"直角三角形の外心は斜辺 $BC$ の中点なので、外接円の半径は "
                        r"$\dfrac{BC}{2}$。$BC=\sqrt{3^2+4^2}=5$ より $\dfrac{5}{2}$。",
         "av": R(5, 2), "chk": lambda av: _eq(sqrt(3 ** 2 + 4 ** 2) / 2, av)},
    ],
}

U_EN1 = {
    "name": "円の性質（円周角・内接四角形）",
    "tag": "円周角の定理・内接四角形・接弦定理",
    "problems": [
        {"group": "円周角の定理", "level": "basic",
         "stem": r"円$O$ の周上に3点 $A$, $B$, $C$ がある。中心角 $\angle AOB=100^\circ$ のとき、"
                 r"円周角 $\angle ACB$ の大きさを求めよ（$C$ は優弧 $AB$ 上）。",
         "answer": r"$\angle ACB=50^\circ$",
         "explanation": r"円周角は中心角の半分。$\dfrac{100}{2}=50^\circ$。",
         "av": 50, "chk": lambda av: _eq(R(100, 2), av)},
        {"group": "円周角の定理", "level": "basic",
         "stem": r"線分 $AB$ を直径とする円周上に点 $C$ をとる（$C \ne A,\,B$）。"
                 r"$\angle ACB$ の大きさを求めよ。",
         "answer": r"$\angle ACB=90^\circ$",
         "explanation": r"直径に対する円周角は $90^\circ$（中心角 $180^\circ$ の半分）。"
                        r"これはタレスの定理とよばれる。",
         "av": 90, "chk": lambda av: _eq(R(180, 2), av)},
        {"group": "内接四角形", "level": "basic",
         "stem": r"円に内接する四角形 $ABCD$ で $\angle A=95^\circ$ のとき、"
                 r"$\angle C$ の大きさを求めよ。",
         "answer": r"$\angle C=85^\circ$",
         "explanation": r"円に内接する四角形の向かい合う内角の和は $180^\circ$。"
                        r"$180-95=85^\circ$。",
         "av": 85, "chk": lambda av: _eq(180 - 95, av)},
        {"group": "内接四角形", "level": "standard",
         "stem": r"円に内接する四角形 $ABCD$ で、$\angle B=110^\circ$ のとき、"
                 r"$\angle D$ の外角（頂点 $D$ における外角）の大きさを求めよ。",
         "answer": r"$110^\circ$",
         "explanation": r"$\angle D=180-110=70^\circ$ なので、その外角は $180-70=110^\circ$。"
                        r"「内接四角形の外角は、それととなり合わない内角に等しい」"
                        r"（$\angle B$ にそのまま等しい）と覚えてもよい。",
         "av": 110, "chk": lambda av: _eq(180 - (180 - 110), av)},
        {"group": "接弦定理", "level": "standard",
         "stem": r"円$O$ の周上の点 $A$ における接線を $AT$ とし、円周上に点 $B$ をとる。"
                 r"接線と弦のなす角 $\angle TAB=55^\circ$ のとき、"
                 r"弦 $AB$ に関して $\angle TAB$ と反対側にある弧 $AB$ 上に点 $C$ をとるとき、"
                 r"$\angle ACB$ の大きさを求めよ。",
         "answer": r"$\angle ACB=55^\circ$",
         "explanation": r"接弦定理より、接線と弦のなす角は、その弦に対する円周角に等しい。"
                        r"よって $55^\circ$。",
         "chk": None},
        {"group": "円と角度", "level": "standard",
         "stem": r"円に内接する四角形 $ABCD$ で $\angle A=80^\circ$, $\angle B=70^\circ$ の"
                 r"とき、$\angle C$ と $\angle D$ の大きさをそれぞれ求めよ。",
         "answer": r"$\angle C=100^\circ$, $\angle D=110^\circ$",
         "explanation": r"向かい合う内角の和が $180^\circ$ なので "
                        r"$\angle C=180-80=100^\circ$、$\angle D=180-70=110^\circ$。"
                        r"（4つの内角の和 $80+70+100+110=360^\circ$ で検算できる。）",
         "av": 100, "chk": lambda av: (_eq(180 - 80, av) and _eq(180 - 70, 110)
                         and _eq(80 + 70 + 100 + 110, 360))},
        {"group": "円と角度", "level": "advanced",
         "stem": r"円$O$ の2つの弦 $AB$, $CD$ が円の内部の点 $P$ で交わっている。"
                 r"弧 $AC$ に対する円周角が $30^\circ$、弧 $BD$ に対する円周角が $40^\circ$ の"
                 r"とき、$\angle APC$ の大きさを求めよ。",
         "answer": r"$\angle APC=70^\circ$",
         "explanation": r"$\triangle PBC$ の外角を考えると "
                        r"$\angle APC=\angle PBC+\angle PCB$。"
                        r"$\angle PBC$ は弧 $AC$ に対する円周角、$\angle PCB$ は弧 $BD$ に対する"
                        r"円周角なので、2つの弦が作る角は「向かい合う2つの弧に対する円周角の和」"
                        r"に等しい。"
                        r"$30+40=70^\circ$。",
         "av": 70, "chk": lambda av: _eq(30 + 40, av)},
        {"group": "証明の型", "level": "standard",
         "stem": r"円に内接する四角形 $ABCD$ において、$\angle A+\angle C=180^\circ$ となることを、"
                 r"円周角の定理を用いて証明せよ。",
         "answer": r"$\angle A$ は弧 $BCD$ に対する円周角、$\angle C$ は弧 $BAD$ に対する円周角。"
                   r"2つの弧を合わせると円1周（中心角 $360^\circ$）だから、"
                   r"円周角の和は $360^\circ\div2=180^\circ$。",
         "explanation": r"▶ 「向かい合う角の和が $180^\circ$」は、"
                        r"中心角の合計が $360^\circ$ であることに帰着させる。"
                        r"①$\angle A$ が見ている弧は $B\to C\to D$ 側の弧、"
                        r"$\angle C$ が見ている弧は $D\to A\to B$ 側の弧。"
                        r"②この2つの弧を合わせるとちょうど円1周なので、中心角の和は $360^\circ$。"
                        r"③円周角は中心角の半分だから、$\angle A+\angle C=\dfrac{360^\circ}{2}=180^\circ$。"
                        r"★「どちらの弧を見ているか」を必ず図に書き込むこと。ここを取り違えると"
                        r"証明が崩れる。",
         "chk": None},
        {"group": "4点が同一円周上", "level": "standard",
         "stem": r"四角形 $ABCD$ において、4点 $A$, $B$, $C$, $D$ が同一円周上にあるための"
                 r"条件として正しいものを次から選べ。"
                 r"　(ア) $\angle A+\angle B=180^\circ$　(イ) $\angle A+\angle C=180^\circ$　"
                 r"(ウ) $\angle A=\angle C$　(エ) 4辺の長さが等しい",
         "answer": r"(イ) $\angle A+\angle C=180^\circ$",
         "explanation": r"向かい合う内角の和が $180^\circ$ であることが、"
                        r"円に内接する（4点が同一円周上にある）ための必要十分条件。"
                        r"(ア)はとなり合う角なので不適。",
         "chk": None},
    ],
}

U_EN2 = {
    "name": "方べきの定理と2つの円",
    "tag": "方べきの定理・接線の長さ・2円の位置関係・多面体",
    "problems": [
        {"group": "方べきの定理（交わる）", "level": "basic",
         "stem": r"円の2つの弦 $AB$, $CD$ が円の内部の点 $P$ で交わっている。"
                 r"$PA=3$, $PB=8$, $PC=4$ のとき、$PD$ の長さを求めよ。",
         "answer": r"$PD=6$",
         "explanation": r"方べきの定理より $PA\cdot PB=PC\cdot PD$。"
                        r"$3\times 8=4\times PD$ から $PD=6$。",
         "av": 6, "chk": lambda av: _eq(R(3 * 8, 4), av)},
        {"group": "方べきの定理（外部）", "level": "standard",
         "stem": r"円の外部の点 $P$ から引いた直線が円と2点 $A$, $B$ で交わっている"
                 r"（$PA<PB$）。$PA=2$, $AB=6$ のとき、$P$ から円に引いた接線の"
                 r"接点を $T$ とするとき $PT$ の長さを求めよ。",
         "answer": r"$PT=4$",
         "explanation": r"$PB=PA+AB=2+6=8$。方べきの定理より $PT^2=PA\cdot PB=2\times 8=16$。"
                        r"よって $PT=4$。",
         "av": 4, "chk": lambda av: _eq(sqrt(2 * (2 + 6)), av)},
        {"group": "方べきの定理（外部）", "level": "standard",
         "stem": r"円の外部の点 $P$ から2本の直線を引き、一方は円と $A$, $B$ で"
                 r"（$PA=3$, $PB=12$）、もう一方は円と $C$, $D$ で交わっている"
                 r"（$PC<PD$）。$PC=4$ のとき、$PD$ の長さを求めよ。",
         "answer": r"$PD=9$",
         "explanation": r"$PA\cdot PB=PC\cdot PD$ より $3\times 12=4\times PD$。"
                        r"よって $PD=9$。",
         "av": 9, "chk": lambda av: _eq(R(3 * 12, 4), av)},
        {"group": "接線の長さ", "level": "basic",
         "stem": r"中心 $O$、半径 $5$ の円がある。$OP=13$ である点 $P$ から円に接線を引き、"
                 r"接点を $T$ とするとき、$PT$ の長さを求めよ。",
         "answer": r"$PT=12$",
         "explanation": r"接点では $OT \perp PT$ なので、$\triangle OTP$ は直角三角形。"
                        r"$PT=\sqrt{13^2-5^2}=\sqrt{144}=12$。",
         "av": 12, "chk": lambda av: _eq(sqrt(13 ** 2 - 5 ** 2), av)},
        {"group": "2円の位置関係", "level": "standard",
         "stem": r"半径がそれぞれ $7$, $3$ の2つの円がある。中心間の距離が $10$ のとき、"
                 r"2円の位置関係を次から選べ。"
                 r"　(ア) 離れている　(イ) 外接する　(ウ) 2点で交わる　(エ) 内接する",
         "answer": r"(イ) 外接する",
         "explanation": r"中心間の距離 $d=10$、半径の和は $7+3=10$。"
                        r"$d=r_1+r_2$ のとき2円は外接する。",
         "av": "外接する", "chk": lambda av: _circle_relation(10, 7, 3) == av},
        {"group": "2円の位置関係", "level": "standard",
         "stem": r"半径がそれぞれ $6$, $2$ の2つの円がある。中心間の距離が $4$ のとき、"
                 r"2円の位置関係を次から選べ。"
                 r"　(ア) 離れている　(イ) 外接する　(ウ) 2点で交わる　(エ) 内接する",
         "answer": r"(エ) 内接する",
         "explanation": r"$d=4$、半径の差は $6-2=4$。$d=|r_1-r_2|$ のとき内接する"
                        r"（小さい円が大きい円の内側に接している）。",
         "av": "内接する", "chk": lambda av: _circle_relation(4, 6, 2) == av},
        {"group": "多面体", "level": "standard",
         "stem": r"正十二面体の頂点の数を、オイラーの多面体定理 $v-e+f=2$ を使って求めよ。"
                 r"ただし正十二面体は正五角形12枚でできている。",
         "answer": r"$v=20$",
         "explanation": r"面は $f=12$。辺は、正五角形12枚の辺の総数 $5\times 12=60$ を"
                        r"2枚ずつで共有するので $e=\dfrac{60}{2}=30$。"
                        r"$v-30+12=2$ より $v=20$。",
         "av": 20, "chk": lambda av: _eq(2 + R(5 * 12, 2) - 12, av)},
        {"group": "多面体", "level": "basic",
         "stem": r"すべての面が正三角形で、頂点の数が $6$、辺の数が $12$ である多面体の"
                 r"面の数を、オイラーの多面体定理を使って求めよ。",
         "answer": r"$f=8$（正八面体）",
         "explanation": r"$v-e+f=2$ に $v=6$, $e=12$ を代入して $6-12+f=2$。"
                        r"よって $f=8$ で、これは正八面体。",
         "av": 8, "chk": lambda av: _eq(2 - 6 + 12, av)},
    ],
}


U_SAKUZU = {
    "name": "作図と空間図形",
    "tag": "基本の作図・直線と平面の位置関係・多面体",
    "problems": [
        {"group": "基本の作図", "level": "basic",
         "stem": r"線分 $AB$ の垂直二等分線を作図するとき、コンパスの針をどこに置くか。"
                 r"次から選べ。　(ア) 点 $A$ と点 $B$ の2か所　(イ) 線分 $AB$ の中点だけ　"
                 r"(ウ) 点 $A$ だけ　(エ) 線分 $AB$ の外の任意の点",
         "answer": r"(ア) 点 $A$ と点 $B$ の2か所",
         "explanation": r"$A$, $B$ をそれぞれ中心として同じ半径の円をかき、"
                        r"2つの交点を結べば垂直二等分線になる。"
                        r"この直線上の点は $A$ からの距離と $B$ からの距離が等しい。",
         "chk": None},
        {"group": "基本の作図", "level": "basic",
         "stem": r"$\angle XOY$ の二等分線を作図する手順として正しい順に並べよ。"
                 r"　(ア) 2つの交点を中心に同じ半径の円をかき、その交点を $P$ とする"
                 r"　(イ) 点 $O$ を中心とする円をかき、$OX$, $OY$ との交点をとる"
                 r"　(ウ) 半直線 $OP$ をひく",
         "answer": r"(イ) → (ア) → (ウ)",
         "explanation": r"①$O$ 中心の円で2辺上に等距離の2点をとる（イ）。"
                        r"②その2点から同じ半径の円をかいて交点 $P$ を作る（ア）。"
                        r"③$OP$ が二等分線（ウ）。ひし形の対角線が角を二等分することが根拠。",
         "chk": None},
        {"group": "基本の作図", "level": "standard",
         "stem": r"長さ $1$ の線分が与えられているとき、コンパスと定規だけで作図できない長さを"
                 r"次から選べ。　(ア) $\sqrt{2}$　(イ) $\dfrac{3}{5}$　(ウ) $\sqrt[3]{2}$　"
                 r"(エ) $\sqrt{5}$",
         "answer": r"(ウ) $\sqrt[3]{2}$",
         "explanation": r"定規とコンパスで作図できるのは、四則演算と平方根で表せる長さだけ。"
                        r"$\sqrt{2}$ は正方形の対角線、$\dfrac{3}{5}$ は平行線を使った等分、"
                        r"$\sqrt{5}$ は直角をはさむ辺が $1$ と $2$ の直角三角形の斜辺として作れる。"
                        r"立方根 $\sqrt[3]{2}$（立方体倍積問題）は作図不可能であることが"
                        r"証明されている。",
         "chk": None},
        {"group": "直線と平面", "level": "basic",
         "stem": r"空間内の2直線が、平行でなく、交わりもしない位置関係にあるとき、"
                 r"この2直線の関係を何というか。",
         "answer": r"ねじれの位置",
         "explanation": r"空間内の2直線の位置関係は「交わる」「平行」「ねじれの位置」の3通り。"
                        r"ねじれの位置にある2直線は同じ平面上にない。",
         "chk": None},
        {"group": "直線と平面", "level": "standard",
         "stem": r"立方体 $ABCD\text{-}EFGH$ において、辺 $AB$ とねじれの位置にある辺は"
                 r"全部で何本あるか。",
         "answer": r"$4$ 本",
         "explanation": r"立方体の辺は12本。$AB$ 自身を除く11本のうち、"
                        r"$AB$ と交わるのは $AD$, $AE$, $BC$, $BF$ の4本、"
                        r"$AB$ と平行なのは $DC$, $EF$, $HG$ の3本。"
                        r"残る $CG$, $DH$, $FG$, $EH$ の4本がねじれの位置。"
                        r"（$11-4-3=4$ と数えてもよい。）",
         "av": 4, "chk": lambda av: 11 - 4 - 3 == av},
        {"group": "直線と平面", "level": "standard",
         "stem": r"平面 $\alpha$ 上にない点 $P$ から $\alpha$ に垂線 $PH$ を下ろす。"
                 r"$\alpha$ 上の直線 $\ell$ が点 $H$ を通らないとき、"
                 r"$\ell$ と直線 $PH$ の位置関係を答えよ。",
         "answer": r"ねじれの位置",
         "explanation": r"▶ 空間の2直線は「交わる・平行・ねじれの位置」の3通り。順に消していく。"
                        r"①$\ell$ は $H$ を通らないので $PH$ とは交わらない"
                        r"（$PH$ が $\alpha$ と共有する点は $H$ だけ）。"
                        r"②$PH \perp \alpha$ なので $PH$ は $\alpha$ 上になく、$\ell$ と平行でもない。"
                        r"③よって残るのは「ねじれの位置」。"
                        r"★$PH \perp \alpha$ ならば $PH$ は $\alpha$ 上の【$H$ を通る】"
                        r"すべての直線と垂直（三垂線の定理の土台）。",
         "chk": None},
        {"group": "多面体", "level": "basic",
         "stem": r"正四面体の面・辺・頂点の数をそれぞれ答え、オイラーの多面体定理 "
                 r"$v-e+f=2$ が成り立つことを確かめよ。",
         "answer": r"面 $4$、辺 $6$、頂点 $4$。$4-6+4=2$ で成り立つ",
         "explanation": r"正四面体は正三角形4枚。辺は $3\times4\div2=6$、頂点は4。"
                        r"$v-e+f=4-6+4=2$ でオイラーの多面体定理を満たす。",
         "av": 2, "chk": lambda av: 4 - 6 + 4 == av},
    ],
}

# ================================================================ 整数の性質
U_YAKUSU = {
    "name": "約数と倍数",
    "tag": "素因数分解・約数の個数と総和・最大公約数と最小公倍数",
    "problems": [
        {"group": "素因数分解", "level": "basic",
         "stem": r"$360$ を素因数分解せよ。",
         "answer": r"$360=2^3\times 3^2\times 5$",
         "explanation": r"小さい素数から順に割る。"
                        r"$360=2\times180=2^2\times90=2^3\times45=2^3\times3^2\times5$。",
         "av": {2: 3, 3: 2, 5: 1}, "chk": lambda av: factorint(360) == av},
        {"group": "約数の個数", "level": "basic",
         "stem": r"$360$ の正の約数の個数を求めよ。",
         "answer": r"$24$ 個",
         "explanation": r"$360=2^3\times3^2\times5^1$ なので、"
                        r"約数の個数は $(3+1)(2+1)(1+1)=24$ 個。"
                        r"（各素因数を何個使うかを独立に選ぶ、と考える。）",
         "av": 24, "chk": lambda av: len(divisors(360)) == av},
        {"group": "約数の総和", "level": "standard",
         "stem": r"$360$ の正の約数の総和を求めよ。",
         "answer": r"$1170$",
         "explanation": r"$(1+2+4+8)(1+3+9)(1+5)=15\times13\times6=1170$。",
         "av": 1170, "chk": lambda av: sum(divisors(360)) == 15 * 13 * 6 == av},
        {"group": "最大公約数・最小公倍数", "level": "basic",
         "stem": r"$84$ と $126$ の最大公約数を求めよ。",
         "answer": r"$42$",
         "explanation": r"$84=2^2\times3\times7$, $126=2\times3^2\times7$。"
                        r"共通の素因数を、指数の小さいほうでとると "
                        r"$2\times3\times7=42$。",
         "av": 42, "chk": lambda av: igcd(84, 126) == av},
        {"group": "最大公約数・最小公倍数", "level": "basic",
         "stem": r"$84$ と $126$ の最小公倍数を求めよ。",
         "answer": r"$252$",
         "explanation": r"指数の大きいほうをとって $2^2\times3^2\times7=252$。"
                        r"（「最大公約数×最小公倍数＝2数の積」でも確かめられる。"
                        r"$42\times252=10584=84\times126$。）",
         "av": 252, "chk": lambda av: (lcm(84, 126) == av and 42 * 252 == 84 * 126)},
        {"group": "最大公約数・最小公倍数", "level": "standard",
         "stem": r"2つの正の整数がある。最大公約数が $6$、最小公倍数が $180$、"
                 r"一方の数が $30$ のとき、もう一方の数を求めよ。",
         "answer": r"$36$",
         "explanation": r"（最大公約数）$\times$（最小公倍数）$=$（2数の積）より "
                        r"$6\times180=30\times x$。よって $x=36$。"
                        r"検算: $\gcd(30,36)=6$, $\mathrm{lcm}(30,36)=180$。",
         "av": 36, "chk": lambda av: (R(6 * 180, 30) == av and igcd(30, 36) == 6 and lcm(30, 36) == 180)},
        {"group": "倍数の判定", "level": "standard",
         "stem": r"$1$ から $200$ までの整数のうち、$3$ の倍数でも $5$ の倍数でもないものは"
                 r"何個あるか。",
         "answer": r"$107$ 個",
         "explanation": r"$3$ の倍数は $66$ 個、$5$ の倍数は $40$ 個、"
                        r"$15$ の倍数は $13$ 個。"
                        r"少なくとも一方の倍数は $66+40-13=93$ 個。"
                        r"よって $200-93=107$ 個。",
         "av": 107, "chk": lambda av: len([n for n in range(1, 201) if n % 3 and n % 5]) == av},
        {"group": "末尾の0の個数", "level": "advanced",
         "stem": r"$50!$ を計算したとき、末尾に連続して並ぶ $0$ の個数を求めよ。",
         "answer": r"$12$ 個",
         "explanation": r"末尾の $0$ の個数は、$50!$ に因数 $10=2\times5$ が何個あるかで決まり、"
                        r"$2$ より $5$ のほうが少ないので $5$ の個数を数えればよい。"
                        r"$\left[\dfrac{50}{5}\right]+\left[\dfrac{50}{25}\right]=10+2=12$。",
         "av": 12, "chk": lambda av: (50 // 5 + 50 // 25 == av
                         and str(sp.factorial(50)).endswith("0" * 12)
                         and not str(sp.factorial(50)).endswith("0" * 13))},
    ],
}

U_GOJOHO = {
    "name": "ユークリッドの互除法と不定方程式",
    "tag": "互除法・1次不定方程式の整数解",
    "problems": [
        {"group": "互除法", "level": "basic",
         "stem": r"ユークリッドの互除法を用いて、$319$ と $209$ の最大公約数を求めよ。",
         "answer": r"$11$",
         "explanation": r"$319=209\times1+110$、$209=110\times1+99$、"
                        r"$110=99\times1+11$、$99=11\times9+0$。"
                        r"最後に割り切れたときの割る数 $11$ が最大公約数。",
         "av": 11, "chk": lambda av: igcd(319, 209) == av},
        {"group": "互除法", "level": "basic",
         "stem": r"ユークリッドの互除法を用いて、$1189$ と $899$ の最大公約数を求めよ。",
         "answer": r"$29$",
         "explanation": r"$1189=899\times1+290$、$899=290\times3+29$、"
                        r"$290=29\times10+0$。よって $29$。",
         "av": 29, "chk": lambda av: igcd(1189, 899) == av},
        {"group": "1次不定方程式", "level": "standard",
         "stem": r"$3x+5y=1$ を満たす整数 $x$, $y$ の組を1つ求めよ。",
         "answer": r"$(x,\,y)=(2,\,-1)$ など",
         "explanation": r"$3\times2+5\times(-1)=6-5=1$。"
                        r"見つけにくいときは互除法を逆にたどる。",
         "av": (2, -1), "chk": lambda av: 3 * av[0] + 5 * av[1] == 1},
        {"group": "1次不定方程式", "level": "standard",
         "stem": r"$3x+5y=1$ の整数解をすべて求めよ（$k$ を整数とする）。",
         "answer": r"$x=5k+2,\ y=-3k-1$（$k$ は整数）",
         "explanation": r"1つの解 $(2,\,-1)$ との差をとると $3(x-2)+5(y+1)=0$、"
                        r"すなわち $3(x-2)=-5(y+1)$。"
                        r"$3$ と $5$ は互いに素なので $x-2$ は $5$ の倍数。"
                        r"$x-2=5k$ とおくと $x=5k+2$、$y=-3k-1$。",
         # av=(x の係数, x の定数, y の係数, y の定数)。answer の一般解そのもの。
         "av": (5, 2, -3, -1),
         "chk": lambda av: all(3 * (av[0] * k + av[1]) + 5 * (av[2] * k + av[3]) == 1
                               for k in range(-6, 7))},
        {"group": "1次不定方程式", "level": "standard",
         "stem": r"$7x+11y=1$ を満たす整数 $x$, $y$ の組を1つ求めよ。",
         "answer": r"$(x,\,y)=(-3,\,2)$ など",
         "explanation": r"互除法を逆にたどる。$11=7\times1+4$、$7=4\times1+3$、$4=3\times1+1$ より "
                        r"$1=4-3=4-(7-4)=2\times4-7=2(11-7)-7=2\times11-3\times7$。"
                        r"よって $7\times(-3)+11\times2=1$。",
         "av": (-3, 2), "chk": lambda av: 7 * av[0] + 11 * av[1] == 1},
        {"group": "1次不定方程式", "level": "standard",
         "stem": r"$3x+5y=7$ の整数解をすべて求めよ（$k$ を整数とする）。",
         "answer": r"$x=5k+4,\ y=-3k-1$（$k$ は整数）",
         "explanation": r"まず $3x+5y=1$ の解 $(2,\,-1)$ を7倍して "
                        r"$3\times14+5\times(-7)=7$。つまり $(14,\,-7)$ は解の1つ。"
                        r"差をとると $3(x-14)=-5(y+7)$ で、$3$ と $5$ は互いに素だから "
                        r"$x-14=5m$。よって $x=5m+14,\ y=-3m-7$。"
                        r"$m=k-2$ と置きなおすと $x=5k+4,\ y=-3k-1$。"
                        r"（$k=0$ で $(4,\,-1)$、$3\times4+5\times(-1)=7$ で確かめられる。）",
         "av": (5, 4, -3, -1),
         "chk": lambda av: all(3 * (av[0] * k + av[1]) + 5 * (av[2] * k + av[3]) == 7
                               for k in range(-6, 7))},
        {"group": "1次不定方程式", "level": "standard",
         "stem": r"$7x-4y=3$ の整数解をすべて求めよ（$k$ を整数とする）。",
         "answer": r"$x=4k+1,\ y=7k+1$（$k$ は整数）",
         "explanation": r"$x=1,\ y=1$ が解の1つ（$7-4=3$）。"
                        r"差をとると $7(x-1)=4(y-1)$。$7$ と $4$ は互いに素なので "
                        r"$x-1=4k$、このとき $y-1=7k$。"
                        r"よって $x=4k+1,\ y=7k+1$。",
         "av": (4, 1, 7, 1),
         "chk": lambda av: all(7 * (av[0] * k + av[1]) - 4 * (av[2] * k + av[3]) == 3
                               for k in range(-6, 7))},
        {"group": "1次不定方程式", "level": "advanced",
         "stem": r"$5x+3y=100$ を満たす正の整数 $x$, $y$ の組は何組あるか。",
         "answer": r"$6$ 組",
         "explanation": r"$3y=100-5x=5(20-x)$ より $y$ は $5$ の倍数。"
                        r"$y=5m$ とおくと $5x+15m=100$、すなわち $x=20-3m$。"
                        r"$x>0$ かつ $y>0$ より $1\le m\le 6$。よって $6$ 組。",
         "av": 6, "chk": lambda av: len([(x, y) for x in range(1, 100) for y in range(1, 100)
                             if 5 * x + 3 * y == 100]) == av},
        {"group": "公約数の性質", "level": "standard",
         "stem": r"$n$ を整数とする。$n$ と $n+1$ の最大公約数を求めよ。",
         "answer": r"$1$（連続する2整数はつねに互いに素）",
         "explanation": r"$n$ と $n+1$ の公約数を $d$ とすると、$d$ は差 $(n+1)-n=1$ も割り切る。"
                        r"よって $d=1$。",
         "av": 1, "chk": lambda av: all(igcd(n, n + 1) == av for n in range(-20, 21) if n != 0)},
    ],
}

U_AMARI = {
    "name": "整数の割り算と余り",
    "tag": "余りによる分類・倍数の証明",
    "problems": [
        {"group": "余りによる分類", "level": "basic",
         "stem": r"整数 $n$ を $3$ で割った余りで分類するとき、$n$ はどのように表せるか。"
                 r"$k$ を整数として3つの形をすべて書け。",
         "answer": r"$n=3k,\ 3k+1,\ 3k+2$",
         "explanation": r"$3$ で割った余りは $0,\,1,\,2$ のいずれか。"
                        r"整数問題では、この3通りに分けて調べる方法（余りによる分類）が基本。",
         "av": [0, 1, 2], "chk": lambda av: sorted({n % 3 for n in range(-30, 31)}) == av},
        {"group": "余りによる分類", "level": "standard",
         "stem": r"$n$ を整数とする。$n^2$ を $3$ で割った余りとしてありえる値をすべて求めよ。",
         "answer": r"$0$ と $1$",
         "explanation": r"$n=3k$ のとき $n^2=9k^2$ で余り $0$。"
                        r"$n=3k\pm1$ のとき $n^2=9k^2\pm6k+1$ で余り $1$。"
                        r"よって余りは $0$ か $1$ で、$2$ にはならない。",
         "av": [0, 1], "chk": lambda av: sorted({(n ** 2) % 3 for n in range(-50, 51)}) == av},
        {"group": "余りによる分類", "level": "standard",
         "stem": r"$n$ を整数とする。$n^2$ を $4$ で割った余りとしてありえる値をすべて求めよ。",
         "answer": r"$0$ と $1$",
         "explanation": r"$n$ が偶数 $n=2k$ なら $n^2=4k^2$ で余り $0$。"
                        r"$n$ が奇数 $n=2k+1$ なら $n^2=4(k^2+k)+1$ で余り $1$。",
         "av": [0, 1], "chk": lambda av: sorted({(n ** 2) % 4 for n in range(-50, 51)}) == av},
        {"group": "倍数の証明", "level": "standard",
         "stem": r"連続する $2$ つの整数の積は、必ずある整数の倍数になる。"
                 r"その整数のうち最大のものを求めよ。",
         "answer": r"$2$",
         "explanation": r"連続する2整数 $n,\ n+1$ のどちらか一方は必ず偶数なので、積は $2$ の倍数。"
                        r"$1\times2=2$ より、これ以上大きい数の倍数とは限らない。"
                        r"（$3$ つ連続なら $6$ の倍数になる。次の問と見比べること。）",
         "av": 2,
         "chk": lambda av: (all((n * (n + 1)) % av == 0 for n in range(-40, 41))
                            and igcd(*[n * (n + 1) for n in range(1, 14)]) == av)},
        {"group": "倍数の証明", "level": "advanced",
         "stem": r"$n$ を整数とするとき、$n^3-n$ は必ずある整数の倍数になる。"
                 r"その整数のうち最大のものを求めよ。",
         "answer": r"$6$",
         "explanation": r"$n^3-n=n(n^2-1)=(n-1)n(n+1)$ と因数分解できる。"
                        r"これは連続する3整数の積なので $6$ の倍数。",
         "av": 6,
         "chk": lambda av: (all((n ** 3 - n) % av == 0 for n in range(-30, 31))
                            and igcd(*[n ** 3 - n for n in range(2, 14)]) == av)},
        {"group": "証明の型", "level": "standard",
         "stem": r"$n$ を整数とするとき、$n^2+n$ は偶数であることを証明せよ。",
         "answer": r"$n^2+n=n(n+1)$ は連続する2整数の積で、"
                   r"一方が必ず偶数だから $n^2+n$ は偶数。",
         "explanation": r"▶ 「偶数であることを示せ」＝「2×（整数）の形に書けることを言う」。"
                        r"①因数分解する： $n^2+n=n(n+1)$。"
                        r"②$n$ と $n+1$ は連続する2整数なので、どちらか一方は必ず偶数。"
                        r"③偶数を含む積は偶数だから $n(n+1)$ は偶数。"
                        r"★別解（余りによる分類）：$n=2k$ なら $n^2+n=4k^2+2k=2(2k^2+k)$、"
                        r"$n=2k+1$ なら $n^2+n=4k^2+6k+2=2(2k^2+3k+1)$。どちらも偶数。",
         # 証明問題は「答えの値」が無いので av を使わず、命題を全数検証する
         "proof": True,
         "chk": lambda av=None: all((n ** 2 + n) % 2 == 0 for n in range(-200, 201))},
        {"group": "証明の型", "level": "standard",
         "stem": r"$n$ を整数とするとき、$n^2$ を $3$ で割った余りは $2$ にならないことを"
                 r"証明せよ。",
         "answer": r"$n=3k,\,3k\pm1$ で場合分けすると余りは $0$ か $1$ のみで、$2$ にならない。",
         "explanation": r"▶ 「〜にならない」＝ありうる場合を全部調べて、そこに現れないことを示す。"
                        r"①整数 $n$ は $3k,\ 3k+1,\ 3k+2$ のいずれかで書ける"
                        r"（$3k+2$ は $3k-1$ と書くと計算が楽）。"
                        r"②$n=3k$ のとき $n^2=9k^2=3(3k^2)$ で余り $0$。"
                        r"③$n=3k\pm1$ のとき $n^2=9k^2\pm6k+1=3(3k^2\pm2k)+1$ で余り $1$。"
                        r"★よって余りは $0$ か $1$ だけ。「余りで分類する」は整数の証明の最重要の型。",
         "proof": True,
         "chk": lambda av=None: 2 not in {(n ** 2) % 3 for n in range(-500, 501)}},
        {"group": "証明の型", "level": "advanced",
         "stem": r"$a$, $b$ を整数とする。$a+b$ が偶数ならば $a-b$ も偶数であることを証明せよ。",
         "answer": r"$(a+b)-(a-b)=2b$ より $a-b=(a+b)-2b$。"
                   r"偶数から偶数をひいた数は偶数だから $a-b$ は偶数。",
         "explanation": r"▶ 「$P$ ならば $Q$」は、$P$ の式から $Q$ の式を作り出せばよい。"
                        r"①$a-b=(a+b)-2b$ と変形する。"
                        r"②仮定より $a+b$ は偶数、また $2b$ はつねに偶数。"
                        r"③偶数 $-$ 偶数 $=$ 偶数だから $a-b$ は偶数。"
                        r"★「差をとる／和をとる」で仮定の式に持ち込むのが定石。"
                        r"$a+b$ と $a-b$ は偶奇が必ず一致する、と覚えておくとよい。",
         "proof": True,
         "chk": lambda av=None: all((a - b) % 2 == 0
                                    for a in range(-30, 31) for b in range(-30, 31)
                                    if (a + b) % 2 == 0)},
        {"group": "余りの計算", "level": "standard",
         "stem": r"$7^{100}$ を $5$ で割った余りを求めよ。",
         "answer": r"$1$",
         "explanation": r"$7$ を $5$ で割った余りは $2$ なので、$7^{100}$ を $5$ で割った余りは "
                        r"$2^{100}$ の余りと同じ。$2^1,\,2^2,\,2^3,\,2^4$ を $5$ で割った余りは"
                        r"順に $2,\,4,\,3,\,1$ で、$4$ 個ごとにくり返す。"
                        r"$100=4\times25$ なので周期のちょうど終わりにあたり、余りは $1$。",
         "av": 1, "chk": lambda av: pow(7, 100, 5) == av},
        {"group": "余りの計算", "level": "advanced",
         "stem": r"$3^{2026}$ の一の位の数字を求めよ。",
         "answer": r"$9$",
         "explanation": r"$3$ の累乗の一の位は $3,\,9,\,7,\,1$ の周期 $4$ でくり返す。"
                        r"$2026=4\times506+2$ なので、周期の $2$ 番目にあたり $9$。",
         "av": 9, "chk": lambda av: pow(3, 2026, 10) == av},
    ],
}

U_NSHINHO = {
    "name": "n進法",
    "tag": "位取り記数法・10進法との変換",
    "problems": [
        {"group": "n進法→10進法", "level": "basic",
         "stem": r"$2$ 進法で表された $1011_{(2)}$ を $10$ 進法で表せ。",
         "answer": r"$11$",
         "explanation": r"$1\times2^3+0\times2^2+1\times2^1+1\times2^0=8+0+2+1=11$。",
         "av": 11, "chk": lambda av: int("1011", 2) == av},
        {"group": "n進法→10進法", "level": "basic",
         "stem": r"$3$ 進法で表された $2101_{(3)}$ を $10$ 進法で表せ。",
         "answer": r"$64$",
         "explanation": r"$2\times27+1\times9+0\times3+1\times1=54+9+0+1=64$。",
         "av": 64, "chk": lambda av: int("2101", 3) == av},
        {"group": "10進法→n進法", "level": "basic",
         "stem": r"$10$ 進法の $45$ を $2$ 進法で表せ。",
         "answer": r"$101101_{(2)}$",
         "explanation": r"$45$ を $2$ で割り続けて余りを下から読む。"
                        r"$45\div2=22\cdots1$, $22\div2=11\cdots0$, $11\div2=5\cdots1$, "
                        r"$5\div2=2\cdots1$, $2\div2=1\cdots0$, $1\div2=0\cdots1$。"
                        r"よって $101101_{(2)}$。",
         "av": "101101", "chk": lambda av: bin(45)[2:] == av},
        {"group": "10進法→n進法", "level": "standard",
         "stem": r"$10$ 進法の $100$ を $5$ 進法で表せ。",
         "answer": r"$400_{(5)}$",
         "explanation": r"$100=4\times25+0\times5+0=4\times5^2$。よって $400_{(5)}$。",
         "av": "400", "chk": lambda av: _to_base(100, 5) == av},
        {"group": "n進法の応用", "level": "standard",
         "stem": r"$2$ 進法で $101_{(2)}+110_{(2)}$ を計算し、$2$ 進法で答えよ。",
         "answer": r"$1011_{(2)}$",
         "explanation": r"$10$ 進法に直すと $5+6=11$。$11$ を $2$ 進法にすると $1011_{(2)}$。"
                        r"（$2$ 進法のまま筆算してもよい。$1+1$ は繰り上がって $10$。）",
         "av": "1011", "chk": lambda av: bin(int("101", 2) + int("110", 2))[2:] == av},
        {"group": "n進法の応用", "level": "advanced",
         "stem": r"$n$ 進法で $3$ 桁の数のうち、最大のものを $10$ 進法で表すと $124$ である。"
                 r"$n$ の値を求めよ。",
         "answer": r"$n=5$",
         "explanation": r"$n$ 進法の $3$ 桁の最大数は $(n-1)(n-1)(n-1)_{(n)}=n^3-1$。"
                        r"$n^3-1=124$ より $n^3=125$、よって $n=5$。",
         "av": 5, "chk": lambda av: sp.solve(sp.Eq(sp.Symbol('n', positive=True) ** 3 - 1, 124))[0] == av},
    ],
}

# ---------------------------------------------------------------- 編の構成
PARTS = [
    {"area": "第1編　図形の性質",
     "sub": "数学A ／ 2025年度から共通テスト数学I・Aは選択問題が廃止され全問必答。"
            "数Aからは「図形の性質」と「場合の数と確率」が出題される",
     "units": [U_HIRITSU, U_GOSHIN, U_EN1, U_EN2, U_SAKUZU]},
    {"area": "第2編　整数の性質",
     "sub": "現行課程では数A「数学と人間の活動」で扱う内容。"
            "共通テスト数学I・Aは数Aから「図形の性質」「場合の数と確率」のみ出題するため"
            "本編は共通テストには出ないが、国公立2次・私大の個別試験では頻出",
     "units": [U_YAKUSU, U_GOJOHO, U_AMARI, U_NSHINHO]},
]
