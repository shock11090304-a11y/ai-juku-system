# -*- coding: utf-8 -*-
"""math2bc_a.py: 2026共通テスト 数学ⅡBC そっくり類似問題 — 第1問・第2問(必答, 各配点15)

第1問 図形と方程式: 束 S±L=0 の2円と絶対値付き不等式の領域
  S(x,y) = x^2+y^2-3x-8y,  L(x,y) = 5x+2y-14
  C1: S+L=0 → x^2+y^2+2x-6y-14=0 → 中心(-1,3),  r1=2√6 (r1^2=24)
  C2: S-L=0 → x^2+y^2-8x-10y+14=0 → 中心(4,5),   r2=3√3 (r2^2=27)
  d = √29  (d^2 = 5^2+2^2 = 29)。|r1-r2|<d<r1+r2 → 2点で交わる。
  D:{L>=0}, E:{L<0}。  原点O∈E, C1中心∈E, C2中心∈D.
  ③: S+|L|<0  →  領域は 2円の共通部分(レンズ C1∩C2)          … セ = ⓪(lens)
  ⑤: S-|L|<0  →  領域は 2円の和集合 C1∪C2 (直感に反する結末)   … ソ = ④(union)
第2問 三角関数: 和積公式(sin版)の導出と応用
  ① sinA+sinB = 2 sin((A+B)/2) cos((A-B)/2)
  (2) f(x)=sin(x+7π/12)+sin(x+π/12)=2 sin(x+π/3) cos(π/4) → x=π/6 で最大値 √2
  (3) g(x)=sin(x+a)+sin(x+2a)+sin(x+3a)=(2cos a+1) sin(x+2a)
      両端の和 sin(x+a)+sin(x+3a)=2 sin(x+2a) cos a
      a=5π/6 → 係数 1-√3 <0 → x=(11/6)π で最大値 √3-1
検証: content/verify_math2bc_a.py (sympy 独立導出 + 9図の領域整合テスト)
"""
import math as _m

# =====================================================================
#  第1問: 幾何定数と領域9図(3×3)の系統生成
#  S = x^2+y^2-3x-8y,  L = 5x+2y-14
#  C1(=S+L): 中心(-1,3), r1=2√6 ;  C2(=S-L): 中心(4,5), r2=3√3
#  ℓ: 5x+2y-14=0 (2交点を通る直線)
# =====================================================================
_C1 = (-1.0, 3.0); _R1 = _m.sqrt(24.0)   # 2√6
_C2 = (4.0, 5.0);  _R2 = _m.sqrt(27.0)   # 3√3
_LA, _LB, _LC = 5.0, 2.0, -14.0          # ℓ: 5x+2y-14=0


# --- SVG 座標変換(縦横同スケールで真円に見せる。座標軸は省略=spec指定) ---
_W = 150
_XMIN, _XMAX = -7.0, 10.5
_YMIN, _YMAX = -3.5, 11.5
_KX = _W / (_XMAX - _XMIN)
_H = round(_KX * (_YMAX - _YMIN), 1)


def _sx(x): return (x - _XMIN) * _KX
def _sy(y): return _H - (y - _YMIN) * _KX
def _sr(r): return r * _KX


_cx1, _cy1, _rr1 = _sx(_C1[0]), _sy(_C1[1]), _sr(_R1)
_cx2, _cy2, _rr2 = _sx(_C2[0]), _sy(_C2[1]), _sr(_R2)


def _liney(x): return (-_LC - _LA * x) / _LB


_p_ln = [(_sx(_XMIN), _sy(_liney(_XMIN))), (_sx(_XMAX), _sy(_liney(_XMAX)))]


def _halfplane_poly(upper=True):
    """キャンバス矩形を ℓ で切った半平面ポリゴン(Sutherland-Hodgman)。
    upper=True は L>=0 側(=直線より上側 / y が大きい側)。"""
    rect = [(_XMIN, _YMIN), (_XMAX, _YMIN), (_XMAX, _YMAX), (_XMIN, _YMAX)]

    def side(x, y):
        v = _LA * x + _LB * y + _LC
        return v >= 0 if upper else v < 0

    def isect(p1, p2):
        x1, y1 = p1; x2, y2 = p2
        d1 = _LA * x1 + _LB * y1 + _LC
        d2 = _LA * x2 + _LB * y2 + _LC
        t = d1 / (d1 - d2)
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    poly = []
    n = len(rect)
    for i in range(n):
        cur = rect[i]; prv = rect[i - 1]
        if side(*cur):
            if not side(*prv):
                poly.append(isect(prv, cur))
            poly.append(cur)
        elif side(*prv):
            poly.append(isect(prv, cur))
    return " ".join(f"{_sx(x):.1f},{_sy(y):.1f}" for x, y in poly)


_GRAY = "#8f8f8f"
_OP = "0.42"


def _defs(i):
    return (f"<defs>"
            f"<clipPath id='c1_{i}'><circle cx='{_cx1:.2f}' cy='{_cy1:.2f}' r='{_rr1:.2f}'/></clipPath>"
            f"<clipPath id='c2_{i}'><circle cx='{_cx2:.2f}' cy='{_cy2:.2f}' r='{_rr2:.2f}'/></clipPath>"
            f"<clipPath id='up_{i}'><polygon points='{_halfplane_poly(True)}'/></clipPath>"
            f"<clipPath id='lo_{i}'><polygon points='{_halfplane_poly(False)}'/></clipPath>"
            f"</defs>")


def _outlines(withline=False):
    s = (f"<circle cx='{_cx1:.2f}' cy='{_cy1:.2f}' r='{_rr1:.2f}' fill='none' stroke='#333' stroke-width='1.1'/>"
         f"<circle cx='{_cx2:.2f}' cy='{_cy2:.2f}' r='{_rr2:.2f}' fill='none' stroke='#333' stroke-width='1.1'/>")
    if withline:
        s += (f"<line x1='{_p_ln[0][0]:.1f}' y1='{_p_ln[0][1]:.1f}' "
              f"x2='{_p_ln[1][0]:.1f}' y2='{_p_ln[1][1]:.1f}' stroke='#333' stroke-width='1.0'/>")
    return s


def _gfill():
    return f"<rect x='0' y='0' width='{_W}' height='{_H}' fill='{_GRAY}' fill-opacity='{_OP}'/>"


def _fig(i):
    """9図(⓪〜⑧)の系統生成。灰色部分だけが異なる。
    ⓪ レンズ C1∩C2 / ① C1全体 / ② C2全体 / ③ 対称差 / ④ 和集合
    ⑤ レンズ上側 / ⑥ レンズ下側 / ⑦ C1の下側の弓形 / ⑧ C2の上側の弓形  (⑤〜⑧は ℓ を描く)"""
    s = [f"<svg viewBox='0 0 {_W} {_H:.1f}' width='150' xmlns='http://www.w3.org/2000/svg'>", _defs(i)]
    if i == 0:      # レンズ
        s.append(f"<g clip-path='url(#c1_{i})'><g clip-path='url(#c2_{i})'>{_gfill()}</g></g>")
        s.append(_outlines(False))
    elif i == 1:    # C1全体
        s.append(f"<g clip-path='url(#c1_{i})'>{_gfill()}</g>")
        s.append(_outlines(False))
    elif i == 2:    # C2全体
        s.append(f"<g clip-path='url(#c2_{i})'>{_gfill()}</g>")
        s.append(_outlines(False))
    elif i == 3:    # 対称差(和集合−レンズ・一様濃度をmaskで)
        s.append(f"<mask id='sd_{i}'>"
                 f"<circle cx='{_cx1:.2f}' cy='{_cy1:.2f}' r='{_rr1:.2f}' fill='white'/>"
                 f"<circle cx='{_cx2:.2f}' cy='{_cy2:.2f}' r='{_rr2:.2f}' fill='white'/>"
                 f"<g clip-path='url(#c1_{i})'><circle cx='{_cx2:.2f}' cy='{_cy2:.2f}' r='{_rr2:.2f}' fill='black'/></g>"
                 f"</mask>")
        s.append(f"<g mask='url(#sd_{i})'>{_gfill()}</g>")
        s.append(_outlines(False))
    elif i == 4:    # 和集合(一様濃度)
        s.append(f"<mask id='un_{i}'>"
                 f"<circle cx='{_cx1:.2f}' cy='{_cy1:.2f}' r='{_rr1:.2f}' fill='white'/>"
                 f"<circle cx='{_cx2:.2f}' cy='{_cy2:.2f}' r='{_rr2:.2f}' fill='white'/></mask>")
        s.append(f"<g mask='url(#un_{i})'>{_gfill()}</g>")
        s.append(_outlines(False))
    elif i == 5:    # レンズ上側
        s.append(f"<g clip-path='url(#up_{i})'><g clip-path='url(#c1_{i})'><g clip-path='url(#c2_{i})'>{_gfill()}</g></g></g>")
        s.append(_outlines(True))
    elif i == 6:    # レンズ下側
        s.append(f"<g clip-path='url(#lo_{i})'><g clip-path='url(#c1_{i})'><g clip-path='url(#c2_{i})'>{_gfill()}</g></g></g>")
        s.append(_outlines(True))
    elif i == 7:    # C1の下側の弓形
        s.append(f"<g clip-path='url(#lo_{i})'><g clip-path='url(#c1_{i})'>{_gfill()}</g></g>")
        s.append(_outlines(True))
    elif i == 8:    # C2の上側の弓形
        s.append(f"<g clip-path='url(#up_{i})'><g clip-path='url(#c2_{i})'>{_gfill()}</g></g>")
        s.append(_outlines(True))
    s.append("</svg>")
    return "".join(s)


def _fig9_grid():
    circ = "⓪①②③④⑤⑥⑦⑧"
    cells = []
    for i in range(9):
        cells.append(
            "<div style='display:inline-block;width:160px;text-align:center;"
            "margin:2.5mm 3px;vertical-align:top'>"
            f"<div style='font-family:sans-serif;font-size:11.5pt;text-align:left;margin-left:10px'>{circ[i]}</div>"
            f"{_fig(i)}</div>")
    return "<div style='text-align:center;margin:2mm 0'>" + "".join(cells) + "</div>"


_FIG9_GRID = _fig9_grid()


# =====================================================================
#  第2問: グラフ描画ソフト画面(図1)の模式図 HTML
# =====================================================================
def _graph_curves_svg():
    """右側の座標平面: y=g(x)=sin(x+a)+sin(x+2a)+sin(x+3a) を a=0.5(実線)/1.0(点線)/1.5(破線)で。
    g=(2cos a+1)sin(x+2a) なので a が大きいほど振幅が縮む様子を描く。"""
    import math
    W, H = 250, 150
    xmin, xmax = 0.0, 2 * math.pi
    ymin, ymax = -3.2, 3.2

    def X(x): return (x - xmin) / (xmax - xmin) * (W - 24) + 16
    def Y(y): return H / 2 - y / (ymax - ymin) * (H - 16)

    def curve(a, dash):
        pts = []
        N = 240
        for k in range(N + 1):
            x = xmin + (xmax - xmin) * k / N
            y = math.sin(x + a) + math.sin(x + 2 * a) + math.sin(x + 3 * a)
            pts.append(f"{X(x):.1f},{Y(y):.1f}")
        da = f" stroke-dasharray='{dash}'" if dash else ""
        return f"<polyline points='{' '.join(pts)}' fill='none' stroke='#222' stroke-width='1.4'{da}/>"

    ox, oy = X(0.0), Y(0.0)
    s = [f"<svg viewBox='0 0 {W} {H}' width='250' xmlns='http://www.w3.org/2000/svg' style='background:#fff'>",
         "<g font-family='Times New Roman,serif' font-style='italic' font-size='10' fill='#333'>"]
    # 軸
    s.append(f"<line x1='6' y1='{oy:.1f}' x2='{W-4}' y2='{oy:.1f}' stroke='#555' stroke-width='0.8'/>")
    s.append(f"<line x1='{ox:.1f}' y1='{H-4}' x2='{ox:.1f}' y2='4' stroke='#555' stroke-width='0.8'/>")
    s.append(f"<text x='{W-8}' y='{oy-4:.1f}'>x</text>")
    s.append(f"<text x='{ox+4:.1f}' y='11'>y</text>")
    s.append(f"<text x='{ox-9:.1f}' y='{oy+11:.1f}'>O</text>")
    # 曲線
    s.append(curve(0.5, ""))       # 実線 a=0.5
    s.append(curve(1.0, "2 2"))    # 点線 a=1.0
    s.append(curve(1.5, "6 3"))    # 破線 a=1.5
    s.append("</g></svg>")
    return "".join(s)


_GRAPH_SVG = _graph_curves_svg()

_FIG1_HTML = f"""
<div style="border:1.4px solid #333;padding:3mm 3.5mm;margin:3mm auto;width:170mm;
  font-family:'Helvetica Neue',Arial,sans-serif;font-size:9pt;background:#fbfbfb;">
  <div style="display:flex;gap:4mm;align-items:stretch;">
    <div style="flex:0 0 46mm;border:1px solid #999;background:#f0f0f0;padding:2mm 2.5mm;">
      <div style="display:flex;gap:2mm;margin-bottom:2mm;">
        <span style="border:1px solid #888;background:#fff;padding:0.4mm 1.6mm;">&#9655;</span>
        <span style="border:1px solid #888;background:#fff;padding:0.4mm 1.6mm;">&bull;</span>
        <span style="border:1px solid #888;background:#fff;padding:0.4mm 1.6mm;">&#9651;</span>
        <span style="border:1px solid #888;background:#fff;padding:0.4mm 1.6mm;">&#9711;</span>
        <span style="border:1px solid #888;background:#fff;padding:0.4mm 1.6mm;font-style:italic;">a=</span>
        <span style="border:1px solid #888;background:#fff;padding:0.4mm 1.6mm;">&#10021;</span>
      </div>
      <div style="margin-bottom:2mm;">
        <span style="font-style:italic;">a</span> =
        <span style="display:inline-block;border:1px solid #888;background:#fff;width:22mm;padding:0.4mm 1mm;">0.5</span>
      </div>
      <div style="margin-bottom:2mm;display:flex;align-items:center;gap:1.5mm;">
        <span>&minus;</span>
        <span style="flex:1;height:2px;background:#bbb;position:relative;">
          <span style="position:absolute;left:22%;top:-3px;width:7px;height:7px;border-radius:50%;background:#222;"></span>
        </span>
        <span>&plus;</span>
      </div>
      <div style="display:flex;gap:1.4mm;margin-bottom:1.6mm;font-style:italic;">
        <span style="border:1px solid #999;background:#fff;padding:0.3mm 1.4mm;">x</span>
        <span style="border:1px solid #999;background:#fff;padding:0.3mm 1.4mm;">y</span>
        <span style="border:1px solid #999;background:#fff;padding:0.3mm 1.4mm;">a</span>
        <span style="border:1px solid #999;background:#fff;padding:0.3mm 1.4mm;font-style:normal;">&lt;</span>
        <span style="border:1px solid #999;background:#fff;padding:0.3mm 1.4mm;font-style:normal;">&gt;</span>
        <span style="border:1px solid #999;background:#fff;padding:0.3mm 1.4mm;font-style:normal;">&pi;</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.2mm;">
        {"".join(f'<span style="border:1px solid #999;background:#fff;text-align:center;padding:0.6mm 0;">{d}</span>' for d in ["7","8","9","4","5","6","1","2","3","0","+","&minus;"])}
      </div>
    </div>
    <div style="flex:1;border:1px solid #999;background:#fff;padding:1.5mm;position:relative;">
      <div style="position:absolute;top:1.5mm;right:2mm;border:1px solid #666;background:#fff;
        padding:0.4mm 2mm;font-style:italic;font-size:9.5pt;">y = g(x)</div>
      {_GRAPH_SVG}
      <div style="border:1px solid #aaa;background:#fafafa;font-size:8pt;padding:1mm 1.5mm;
        display:inline-block;margin-top:1mm;line-height:1.6;">
        <div><span style="display:inline-block;width:16px;border-top:1.4px solid #222;vertical-align:middle;"></span>
          <span style="font-style:italic;">a</span> = 0.5</div>
        <div><span style="display:inline-block;width:16px;border-top:1.4px dotted #222;vertical-align:middle;"></span>
          <span style="font-style:italic;">a</span> = 1.0</div>
        <div><span style="display:inline-block;width:16px;border-top:1.4px dashed #222;vertical-align:middle;"></span>
          <span style="font-style:italic;">a</span> = 1.5</div>
      </div>
    </div>
  </div>
  <div style="text-align:center;font-size:9pt;margin-top:1.5mm;font-family:'Hiragino Kaku Gothic ProN',sans-serif;">図　1</div>
</div>
"""


# ============================================================
# SECTIONS
# ============================================================

SECTIONS = [
    # ---------------- 第1問 図形と方程式(必答・15点) ----------------
    {"no": 1, "points": 15, "optional": "必答問題", "parts": [
        {"label": "", "blocks": [
            {"t": "boxnote", "lines": [
                r"（注）　この科目には，選択問題があります。（3ページ参照。）",
            ]},
            {"t": "p", "text": r"$\mathrm{O}$ を原点とする座標平面において，方程式"},
            {"t": "m", "tex": r"x^{2}+y^{2}-3x-8y+(5x+2y-14)=0 \qquad \cdots\cdots ①"},
            {"t": "p", "text": r"の表す円を $C_{1}$，方程式"},
            {"t": "m", "tex": r"x^{2}+y^{2}-3x-8y-(5x+2y-14)=0 \qquad \cdots\cdots ②"},
            {"t": "p", "text": r"の表す円を $C_{2}$ とする。"},

            {"t": "p", "text": r"<b>(1)</b>　①を変形すると，$C_{1}$ の中心の座標は "
                               r"$($〔アイ〕$,\ $〔ウ〕$)$ である。"},
            {"t": "p", "text": r"$C_{1}$ の半径を $r_{1}$，$C_{2}$ の半径を $r_{2}$，"
                               r"$C_{1}$ の中心と $C_{2}$ の中心との距離を $d$ とすると"},
            {"t": "m", "tex": r"r_{1}=エ\sqrt{オ},\qquad r_{2}=カ\sqrt{キ},\qquad d=\sqrt{クケ}"},
            {"t": "p", "text": r"である。$r_{1}$，$r_{2}$ と $d$ の関係"
                               r"$\bigl(\,|r_{1}-r_{2}|<d<r_{1}+r_{2}\,\bigr)$ から，"
                               r"$C_{1}$ と $C_{2}$ は<b>異なる2点で交わる</b>ことがわかる。"},

            {"t": "p", "text": r"<b>(2)</b>　不等式"},
            {"t": "m", "tex": r"x^{2}+y^{2}-3x-8y+\bigl|\,5x+2y-14\,\bigr|<0 \qquad \cdots\cdots ③"},
            {"t": "p", "text": r"の表す領域について考えよう。③の左辺は，$5x+2y-14\ge 0$ のとき①の左辺と一致し，"
                               r"$5x+2y-14<0$ のとき②の左辺と一致する。"},

            {"t": "p", "text": r"<b>(i)</b>　不等式 $5x+2y-14\ge 0$ の表す領域を $D$，"
                               r"不等式 $5x+2y-14<0$ の表す領域を $E$ とする。このとき，次のことがいえる。"},
            {"t": "p", "text": r"・原点 $\mathrm{O}$ は 〚コ〛 に含まれる。<br>"
                               r"・$C_{1}$ の中心は 〚サ〛 に含まれる。<br>"
                               r"・$C_{2}$ の中心は 〚シ〛 に含まれる。"},
            {"t": "choices", "for": r"〚コ〛〜〚シ〛の解答群（同じものを繰り返し選んでもよい。）",
             "cols": 2, "items": [r"$D$", r"$E$"]},

            {"t": "p", "text": r"<b>(ii)</b>　方程式 $5x+2y-14=0\ \ \cdots\cdots ④$ の表す直線を $\ell$ とする。"
                               r"実数 $x,\,y$ が①と②の両方を満たすとする。①と②の左辺どうし，右辺どうしの差をとると"},
            {"t": "m", "tex": r"2\,(5x+2y-14)=0"},
            {"t": "p", "text": r"となる。よって，このような実数 $x,\,y$ は④も満たす。"
                               r"したがって，次の 〚ス〛 が成り立つ。このことから，$\ell$ は "
                               r"$C_{1}$ と $C_{2}$ の二つの交点を通る直線であることがわかる。"},
            {"t": "choices", "for": "ス", "auto_intro": True, "cols": 1, "items": [
                r"点 $\mathrm{P}$ を $\ell$ 上の点とすると，$\mathrm{P}$ は $C_{1}$ 上にあり，かつ $C_{2}$ 上にもある",
                r"点 $\mathrm{P}$ を $\ell$ 上の点とすると，$\mathrm{P}$ は $C_{1}$ 上にあるか，または $C_{2}$ 上にある",
                r"点 $\mathrm{P}$ を $C_{1}$ 上にあり，かつ $C_{2}$ 上にもある点とすると，$\mathrm{P}$ は $\ell$ 上にある",
                r"点 $\mathrm{P}$ を $C_{1}$ 上にあるか，または $C_{2}$ 上にある点とすると，$\mathrm{P}$ は $\ell$ 上にある",
                r"点 $\mathrm{P}$ を $C_{1}$ 上の点，点 $\mathrm{Q}$ を $C_{2}$ 上の点とすると，直線 $\mathrm{PQ}$ は $\ell$ と一致する",
                r"点 $\mathrm{P}$ を $C_{1}$ 上の点，点 $\mathrm{Q}$ を $C_{2}$ 上の点とすると，直線 $\mathrm{PQ}$ は $\ell$ と交わる",
            ]},

            {"t": "p", "text": r"<b>(iii)</b>　不等式 $x^{2}+y^{2}-3x-8y+(5x+2y-14)<0$ の表す領域と，(i)の領域 $D$ との"
                               r"共通部分を $F$ とする。また，不等式 $x^{2}+y^{2}-3x-8y-(5x+2y-14)<0$ の表す領域と，"
                               r"(i)の領域 $E$ との共通部分を $G$ とする。"},
            {"t": "p", "text": r"③の表す領域は $F$ と $G$ の和集合である。これを図示すると 〚セ〛 の灰色部分となる。"
                               r"ただし，境界線を含まない。"},

            {"t": "p", "text": r"<b>(iv)</b>　③において $\bigl|\,5x+2y-14\,\bigr|$ の前の符号を $+$ から $-$ に変えた不等式"},
            {"t": "m", "tex": r"x^{2}+y^{2}-3x-8y-\bigl|\,5x+2y-14\,\bigr|<0 \qquad \cdots\cdots ⑤"},
            {"t": "p", "text": r"を考える。⑤の表す領域を図示すると 〚ソ〛 の灰色部分となる。"
                               r"ただし，境界線を含まない。"},
            {"t": "p", "text": r"〚セ〛，〚ソ〛については，最も適当なものを，次の <b>⓪</b>〜<b>⑧</b> のうちから一つずつ選べ。"
                               r"ただし，同じものを繰り返し選んでもよい。"
                               r"なお，<b>⓪</b>〜<b>⑧</b>では座標軸を省略している。"},
            {"t": "html", "html": _FIG9_GRID},
        ]},
    ]},

    # ---------------- 第2問 三角関数(必答・15点) ----------------
    {"no": 2, "points": 15, "optional": "必答問題", "parts": [
        {"label": "", "blocks": [
            {"t": "p", "text": r"<b>(1)</b>　二つの角 $A,\,B$ に対して"},
            {"t": "m", "tex": r"\sin A+\sin B=2\sin\dfrac{A+B}{2}\cos\dfrac{A-B}{2} \qquad \cdots\cdots ①"},
            {"t": "p", "text": r"が成り立つことを示そう。二つの角 $\alpha,\,\beta$ に対して，加法定理から"},
            {"t": "m", "tex": r"\sin(\alpha+\beta)=ア+\cos\alpha\sin\beta \qquad \cdots\cdots ②"},
            {"t": "m", "tex": r"\sin(\alpha-\beta)=ア-\cos\alpha\sin\beta \qquad \cdots\cdots ③"},
            {"t": "p", "text": r"が得られる。②と③の左辺どうし，右辺どうしを加えると "
                               r"$\sin(\alpha+\beta)+\sin(\alpha-\beta)=2\,ア$ となる。"
                               r"ここで $\alpha=$〚イ〛，$\beta=$〚ウ〛 とおくと，$\alpha+\beta=A$，$\alpha-\beta=B$ となり，①が得られる。"},
            {"t": "choices", "for": "ア", "auto_intro": True, "cols": 4, "items": [
                r"$\sin\alpha\sin\beta$", r"$\sin\alpha\cos\beta$", r"$\cos\alpha\sin\beta$", r"$\cos\alpha\cos\beta$",
                r"$\sin^{2}\alpha$", r"$\sin^{2}\beta$", r"$\cos^{2}\alpha$", r"$\cos^{2}\beta$",
            ]},
            {"t": "choices", "for": r"〚イ〛，〚ウ〛の解答群（同じものを繰り返し選んでもよい。）",
             "cols": 4, "items": [
                r"$A$", r"$B$", r"$A+B$", r"$A-B$",
                r"$\dfrac{A+B}{2}$", r"$\dfrac{A-B}{2}$", r"$\dfrac{A+B}{4}$", r"$\dfrac{A-B}{4}$",
             ]},

            {"t": "p", "text": r"<b>(2)</b>　関数 $f(x)=\sin\!\Bigl(x+\dfrac{7}{12}\pi\Bigr)+\sin\!\Bigl(x+\dfrac{1}{12}\pi\Bigr)$ について，"
                               r"$0\le x<2\pi$ の範囲で最大値を考えよう。①を用いると"},
            {"t": "m", "tex": r"f(x)=2\sin\!\bigl(x+エ\bigr)\cos オ=2\cos オ\,\sin\!\bigl(x+エ\bigr)"},
            {"t": "p", "text": r"と変形できる。$2\cos オ$ は正の定数であるから，$0\le x<2\pi$ の範囲において，"
                               r"$f(x)$ は $x=$〚カ〛 のとき最大値 〚キ〛 をとる。"},
            {"t": "choices", "for": r"〚エ〛，〚オ〛，〚カ〛の解答群（同じものを繰り返し選んでもよい。）",
             "cols": 4, "items": [
                r"$0$", r"$\dfrac{\pi}{12}$", r"$\dfrac{\pi}{6}$", r"$\dfrac{\pi}{4}$",
                r"$\dfrac{\pi}{3}$", r"$\dfrac{\pi}{2}$", r"$\dfrac{3}{4}\pi$", r"$\pi$",
             ]},
            {"t": "choices", "for": "キ", "auto_intro": True, "cols": 4, "items": [
                r"$\dfrac{1}{2}$", r"$1$", r"$2$", r"$\dfrac{\sqrt{2}}{2}$",
                r"$\dfrac{\sqrt{3}}{2}$", r"$\sqrt{2}$", r"$\sqrt{3}$", r"$2\sqrt{2}$",
             ]},

            {"t": "p", "text": r"<b>(3)</b>　$a$ を $0<a<\pi$ を満たす定数とし，"
                               r"$g(x)=\sin(x+a)+\sin(x+2a)+\sin(x+3a)$ とする。"
                               r"花子さんと太郎さんは，$y=g(x)$ のグラフを，コンピュータのグラフ描画ソフトを用いて"
                               r"$a$ の値をいくつか変えながら表示した（<b>図1</b>）。"},
            {"t": "html", "html": _FIG1_HTML},
            {"t": "convo", "turns": [
                {"sp": "花子", "text": r"どの $a$ でも，$g(x)$ は定数 $p,\,q$ を用いて $g(x)=p\sin(x+q)$ の形に"
                                       r"変形できそうだね。"},
                {"sp": "太郎", "text": r"三つの関数 $\sin(x+a)$，$\sin(x+2a)$，$\sin(x+3a)$ のうちの二つの関数の和に①を使うと，"
                                       r"残り一つの関数の定数倍にできるかな。"},
            ]},

            {"t": "p", "text": r"<b>(i)</b>　①を用いると，$\sin(x+a)$，$\sin(x+2a)$，$\sin(x+3a)$ のうちの二つの関数の和 〚ク〛 は，"
                               r"残りの関数 $\sin(x+$〚ケ〛$)$ の定数倍となる。したがって，$g(x)$ は"},
            {"t": "m", "tex": r"g(x)=コ\,\sin(x+ケ)"},
            {"t": "p", "text": r"と変形することができる。"},
            {"t": "choices", "for": "ク", "auto_intro": True, "cols": 1, "items": [
                r"$\sin(x+a)+\sin(x+2a)$",
                r"$\sin(x+a)+\sin(x+3a)$",
                r"$\sin(x+2a)+\sin(x+3a)$",
            ]},
            {"t": "choices", "for": "ケ", "auto_intro": True, "cols": 3, "items": [
                r"$a$", r"$2a$", r"$3a$",
            ]},
            {"t": "choices", "for": "コ", "auto_intro": True, "cols": 4, "items": [
                r"$2\cos a$", r"$-2\cos a$", r"$2\cos 2a$", r"$-2\cos 2a$",
                r"$2\cos a+1$", r"$-2\cos a+1$", r"$2\cos 2a+1$", r"$-2\cos 2a+1$",
             ]},

            {"t": "p", "text": r"<b>(ii)</b>　$a=\dfrac{5}{6}\pi$ のとき，$0\le x<2\pi$ の範囲において，"
                               r"$g(x)$ は $x=\dfrac{サシ}{ス}\pi$ で最大値 〚セ〛 をとる。"},
            {"t": "p", "text": r"（(2)では係数 $2\cos オ$ が正であったが，(ii)では 〚コ〛 の値の符号に注意して"
                               r"最大値を考えること。）"},
            {"t": "choices", "for": "セ", "auto_intro": True, "cols": 5, "items": [
                r"$0$", r"$1$", r"$2$", r"$-1$", r"$-2$",
                r"$\sqrt{3}$", r"$-\sqrt{3}$", r"$\sqrt{3}+1$", r"$\sqrt{3}-1$", r"$-\sqrt{3}+1$",
             ]},
        ]},
    ]},
]


# ============================================================
# ANS_SECTIONS
# ============================================================

ANS_SECTIONS = [
    # -------- 第1問 --------
    {"section": 1,
     "slots": {
         "ア": "−", "イ": "1", "ウ": "3",
         "エ": "2", "オ": "6", "カ": "3", "キ": "3",
         "ク": "2", "ケ": "9",
         "コ": "①", "サ": "①", "シ": "⓪",
         "ス": "②",
         "セ": "⓪", "ソ": "④",
     },
     "kai": [
         {"heading": "(1) 2円の標準形と位置関係 〔アイ〕〜〔クケ〕", "blocks": [
             {"t": "p", "text": r"$S=x^{2}+y^{2}-3x-8y$，$L=5x+2y-14$ とおく。①は $S+L=0$，②は $S-L=0$ である。"},
             {"t": "p", "text": r"$C_{1}\,(S+L=0)$：$x$，$y$ の項をまとめると"},
             {"t": "m", "tex": r"x^{2}+y^{2}+2x-6y-14=0\ \Longrightarrow\ (x+1)^{2}+(y-3)^{2}=24"},
             {"t": "p", "text": r"よって中心 $(-1,\,3)$，$r_{1}=\sqrt{24}=2\sqrt{6}$。"
                               r"<b>アイ$=-1$，ウ$=3$，$r_{1}=2\sqrt{6}$</b>（エ$=2$，オ$=6$）。"
                               r"（$\sqrt{24}$ は $\sqrt{4\cdot 6}=2\sqrt{6}$ と根号内を最小に。"
                               r"$2\sqrt{6}$ を $\sqrt{24}$ のまま書くのは規約違反。）"},
             {"t": "p", "text": r"$C_{2}\,(S-L=0)$：$-L$ を加えるので符号が反転して"},
             {"t": "m", "tex": r"x^{2}+y^{2}-8x-10y+14=0\ \Longrightarrow\ (x-4)^{2}+(y-5)^{2}=27"},
             {"t": "p", "text": r"よって中心 $(4,\,5)$，$r_{2}=\sqrt{27}=3\sqrt{3}$。<b>$r_{2}=3\sqrt{3}$</b>（カ$=3$，キ$=3$）。"},
             {"t": "m", "tex": r"d^{2}=(4-(-1))^{2}+(5-3)^{2}=25+4=29\ \Longrightarrow\ d=\sqrt{29}"},
             {"t": "p", "text": r"よって <b>クケ$=29$</b>。検算：$|r_{1}-r_{2}|=|2\sqrt6-3\sqrt3|\approx 0.30$，"
                               r"$r_{1}+r_{2}\approx 10.10$，$d\approx 5.39$ で "
                               r"$|r_{1}-r_{2}|<d<r_{1}+r_{2}$ が成り立ち，2円は異なる2点で交わる。"},
         ]},
         {"heading": "(2)(i) 半平面 D, E への帰属 〔コ〕〜〔シ〕", "blocks": [
             {"t": "p", "text": r"$L=5x+2y-14$ の符号で判定する。$L\ge 0$ が $D$，$L<0$ が $E$。"},
             {"t": "m", "tex": r"L(0,0)=-14<0,\qquad L(-1,3)=5\cdot(-1)+2\cdot 3-14=-13<0,"},
             {"t": "m", "tex": r"L(4,5)=5\cdot 4+2\cdot 5-14=16>0"},
             {"t": "p", "text": r"よって 原点 $\mathrm{O}$ は $L<0$ すなわち $E$ に，$C_{1}$ の中心 $(-1,3)$ も $E$ に，"
                               r"$C_{2}$ の中心 $(4,5)$ は $D$ に含まれる。"
                               r"<b>コ$=E=$①，サ$=E=$①，シ$=D=$⓪</b>。"
                               r"（$L$ に代入して符号を見るだけ。$C_{1}$ の中心が $E$ 側にあるのがこの後の急所。）"},
         ]},
         {"heading": "(2)(ii) 束から「2交点はℓ上」の含意 〔ス〕", "blocks": [
             {"t": "p", "text": r"①かつ②を満たす点は，差 $2L=0$ すなわち $L=0$（④）を満たす。"
                               r"言い換えると「$C_{1}$ 上にあり，かつ $C_{2}$ 上にもある点」は「$\ell$ 上にある」。"
                               r"含意の向きは<b>「$C_{1}$ かつ $C_{2}$」$\Rightarrow$「$\ell$ 上」</b>である。"},
             {"t": "p", "text": r"よって <b>ス$=$②</b>。"
                               r"⓪①は逆向き（$\ell$ 上$\Rightarrow C_{1},C_{2}$ 上）で誤り。"
                               r"実際 $\ell$ 上の点がすべて $C_{1}$ 上にあるわけではない。"
                               r"③は「または」に弱めた点で $\ell$ 上とは限らず誤り。"
                               r"④⑤は2点それぞれを結ぶ直線の話にすり替えており不適。"},
             {"t": "p", "text": r"なお，差をとった式 $2L=0$ が④そのものだから，「①かつ②」を満たす2交点は必ず $\ell$ 上にあり，"
                               r"$\ell$ が2交点を通る直線であることが確定する。"},
         ]},
         {"heading": "(2)(iii) ③の領域 〔セ〕", "blocks": [
             {"t": "p", "text": r"③ $S+|L|<0$ を場合分けする。"},
             {"t": "p", "text": r"・$D$（$L\ge 0$）では $|L|=L$ なので $S+L<0$，すなわち $C_{1}$ の<b>内部</b>。"
                               r"これと $D$ の共通部分が $F$。"},
             {"t": "p", "text": r"・$E$（$L<0$）では $|L|=-L$ なので $S-L<0$，すなわち $C_{2}$ の<b>内部</b>。"
                               r"これと $E$ の共通部分が $G$。"},
             {"t": "p", "text": r"ここで直線 $\ell$ は2交点を通るから，$D$ 側の交点付近では $C_{1}$ の内部と $C_{2}$ の内部が一致し，"
                               r"$E$ 側でも同様になる。実際に代表点で調べると，$F\cup G$ はちょうど"
                               r"<b>2円の共通部分（レンズ形 $C_{1}\cap C_{2}$）</b>に一致する。"},
             {"t": "p", "text": r"よって <b>セ$=$⓪</b>（レンズ）。"
                               r"検算：$F\cup G$ の点は常に $C_{1}$ の内部かつ $C_{2}$ の内部にあり，逆も成り立つ"
                               r"（章末の機械検証で全域一致を確認済み）。①②は片方の円だけ，③は対称差，④は和集合で誤り。"},
         ]},
         {"heading": "(2)(iv) 符号を反転した⑤の領域 〔ソ〕", "blocks": [
             {"t": "p", "text": r"⑤ $S-|L|<0$ を同様に場合分けする。"},
             {"t": "p", "text": r"・$D$（$L\ge 0$）では $-|L|=-L$ なので $S-L<0$，すなわち $C_{2}$ の<b>内部</b>。"},
             {"t": "p", "text": r"・$E$（$L<0$）では $-|L|=L$ なので $S+L<0$，すなわち $C_{1}$ の<b>内部</b>。"},
             {"t": "p", "text": r"$D$ 側では $C_{2}$ の内部，$E$ 側では $C_{1}$ の内部が塗られる。"
                               r"$\ell$ で分けた両側を合わせると，塗られる範囲は<b>2円の和集合 $C_{1}\cup C_{2}$ 全体</b>に広がる。"
                               r"符号を $-$ にしただけで領域が対称差ではなく和集合に化けるのがこの問題の急所である。"},
             {"t": "p", "text": r"よって <b>ソ$=$④</b>（和集合）。"
                               r"「対称差(③)」を選びたくなるが，$D$ 側で採用される円が $C_{1}$ から $C_{2}$ へ入れ替わるため，"
                               r"境界 $\ell$ で滑らかにつながって<b>和集合</b>になる。"
                               r"（機械検証で $S-|L|<0 \Leftrightarrow C_{1}\cup C_{2}$ を全域確認済み。）"},
         ]},
     ]},

    # -------- 第2問 --------
    {"section": 2,
     "slots": {
         "ア": "①", "イ": "④", "ウ": "⑤",
         "エ": "④", "オ": "③", "カ": "②", "キ": "⑤",
         "ク": "①", "ケ": "①", "コ": "④",
         "サ": "1", "シ": "1", "ス": "6", "セ": "⑧",
     },
     "kai": [
         {"heading": "(1) 和積公式の導出 〔ア〕〜〔ウ〕", "blocks": [
             {"t": "p", "text": r"加法定理 $\sin(\alpha\pm\beta)=\sin\alpha\cos\beta\pm\cos\alpha\sin\beta$ より，"
                               r"②の空欄は第1項 $\sin\alpha\cos\beta$。<b>ア$=$①</b>。"
                               r"（④〜⑦の $\sin^{2},\cos^{2}$ は加法定理に現れないので即座に切れる。⓪②③は項の組合せ違い。）"},
             {"t": "m", "tex": r"\sin(\alpha+\beta)+\sin(\alpha-\beta)=2\sin\alpha\cos\beta"},
             {"t": "p", "text": r"ここで $\alpha+\beta=A$，$\alpha-\beta=B$ となるように $\alpha,\beta$ を選ぶ。"
                               r"2式を辺々足す・引くと $\alpha=\dfrac{A+B}{2}$，$\beta=\dfrac{A-B}{2}$。"},
             {"t": "p", "text": r"よって <b>イ$=$④（$\tfrac{A+B}{2}$），ウ$=$⑤（$\tfrac{A-B}{2}$）</b>。"
                               r"これを代入すると $2\sin\alpha\cos\beta=2\sin\dfrac{A+B}{2}\cos\dfrac{A-B}{2}$ となり①が示せた。"},
         ]},
         {"heading": "(2) 同振幅2波の和の最大値 〔エ〕〜〔キ〕", "blocks": [
             {"t": "p", "text": r"①で $A=x+\dfrac{7}{12}\pi$，$B=x+\dfrac{1}{12}\pi$ とおく。"},
             {"t": "m", "tex": r"\frac{A+B}{2}=x+\frac{1}{2}\Bigl(\frac{7}{12}\pi+\frac{1}{12}\pi\Bigr)"
                               r"=x+\frac{1}{2}\cdot\frac{8}{12}\pi=x+\frac{\pi}{3}"},
             {"t": "m", "tex": r"\frac{A-B}{2}=\frac{1}{2}\Bigl(\frac{7}{12}\pi-\frac{1}{12}\pi\Bigr)"
                               r"=\frac{1}{2}\cdot\frac{6}{12}\pi=\frac{\pi}{4}"},
             {"t": "p", "text": r"よって $f(x)=2\sin\!\Bigl(x+\dfrac{\pi}{3}\Bigr)\cos\dfrac{\pi}{4}$。"
                               r"<b>エ$=$④（$\tfrac{\pi}{3}$），オ$=$③（$\tfrac{\pi}{4}$）</b>。"},
             {"t": "p", "text": r"$2\cos\dfrac{\pi}{4}=2\cdot\dfrac{\sqrt2}{2}=\sqrt2>0$ は正の定数だから，"
                               r"$f(x)$ が最大になるのは $\sin\!\Bigl(x+\dfrac{\pi}{3}\Bigr)=1$，"
                               r"すなわち $x+\dfrac{\pi}{3}=\dfrac{\pi}{2}$ のとき。"},
             {"t": "m", "tex": r"x=\frac{\pi}{2}-\frac{\pi}{3}=\frac{\pi}{6}\quad(0\le x<2\pi\ \text{に含まれる})"},
             {"t": "p", "text": r"このとき最大値は $\sqrt2\cdot 1=\sqrt2$。"
                               r"<b>カ$=$②（$\tfrac{\pi}{6}$），キ$=$⑤（$\sqrt2$）</b>。"
                               r"係数が正なので $\sin=1$ で最大、という素直なケース。(3)(ii)との対比が重要。"},
         ]},
         {"heading": "(3)(i) 3項和の構造 (2cos a+1)sin(x+2a) 〔ク〕〜〔コ〕", "blocks": [
             {"t": "p", "text": r"太郎さんの方針どおり，<b>両端の項</b> $\sin(x+a)$ と $\sin(x+3a)$ の和に①を使う。"
                               r"$A=x+3a$，$B=x+a$ とすると $\dfrac{A+B}{2}=x+2a$，$\dfrac{A-B}{2}=a$ だから"},
             {"t": "m", "tex": r"\sin(x+a)+\sin(x+3a)=2\sin(x+2a)\cos a"},
             {"t": "p", "text": r"となり，これは残りの関数 $\sin(x+2a)$ の定数倍（$2\cos a$ 倍）。"
                               r"よって <b>ク$=$①</b>（両端の和），<b>ケ$=$①（$2a$）</b>。"
                               r"（真ん中どうしを含む⓪②は，和が $\sin(x+2a)$ の定数倍にならず不適。）"},
             {"t": "p", "text": r"これに真ん中の項 $\sin(x+2a)$ を足すと"},
             {"t": "m", "tex": r"g(x)=2\cos a\,\sin(x+2a)+\sin(x+2a)=(2\cos a+1)\sin(x+2a)"},
             {"t": "p", "text": r"よって <b>コ$=$④（$2\cos a+1$）</b>。"
                               r"選択肢は「符号 $\pm$」×「角 $a$/$2a$」×「$+1$ の有無」の直積。"
                               r"角は $a$（$2a$ ではない）で $+1$ が付き符号は $+$、が正しい。"},
         ]},
         {"heading": "(3)(ii) 係数が負になる場合の最大値 〔サシ〕〜〔セ〕", "blocks": [
             {"t": "p", "text": r"$a=\dfrac{5}{6}\pi$ を代入する。係数は"},
             {"t": "m", "tex": r"2\cos a+1=2\cos\frac{5}{6}\pi+1=2\cdot\Bigl(-\frac{\sqrt3}{2}\Bigr)+1=1-\sqrt3<0"},
             {"t": "p", "text": r"$1-\sqrt3\approx -0.73$ で<b>負</b>。よって"},
             {"t": "m", "tex": r"g(x)=(1-\sqrt3)\,\sin\!\Bigl(x+\frac{5}{3}\pi\Bigr)\qquad\Bigl(2a=\frac{5}{3}\pi\Bigr)"},
             {"t": "p", "text": r"係数が負だから，$g(x)$ が<b>最大</b>になるのは $\sin$ が<b>最小 $=-1$</b> のとき。"
                               r"$\sin\!\Bigl(x+\dfrac{5}{3}\pi\Bigr)=-1$ すなわち "
                               r"$x+\dfrac{5}{3}\pi=\dfrac{3}{2}\pi$（$0\le x<2\pi$ での該当解）。"},
             {"t": "m", "tex": r"x=\frac{3}{2}\pi-\frac{5}{3}\pi=\frac{9\pi-10\pi}{6}=-\frac{\pi}{6}"
                               r"\ \equiv\ -\frac{\pi}{6}+2\pi=\frac{11}{6}\pi"},
             {"t": "p", "text": r"よって <b>サシ／ス$=\dfrac{11}{6}$</b>（サ$=1$，シ$=1$，ス$=6$）。最大値は"},
             {"t": "m", "tex": r"g_{\max}=(1-\sqrt3)\cdot(-1)=\sqrt3-1"},
             {"t": "p", "text": r"よって <b>セ$=$⑧（$\sqrt3-1$）</b>。"
                               r"係数の符号を見落とすと，$\sin=1$ で最大と誤り係数そのもの $1-\sqrt3=-\sqrt3+1$（⑨）を選んでしまう。"
                               r"⑨はこの誤答を検出する鏡像トラップ。符号が負のときは $\sin=-1$ で最大、が本質。"},
         ]},
     ]},
]
