# -*- coding: utf-8 -*-
r"""math1a_a.py: 2026共通テスト 数学Ⅰ・A そっくり類似問題 — 第1問(配点30)・第2問(配点30)

第1問 〔1〕集合と命題 / 〔2〕図形と計量
  〔1〕 U={2,3,…,24}. 述語「kとaが1以外の正の公約数をもつ」で部分集合A,Bを定義。
       (1) a=3,b=4 → A,B,A∩B,A∩B̄ を共通10択から選択 (ア=⑥ イ=⑧ ウ=⓪ エ=①)
       (2) 逆算 (i) Āに2の倍数も3の倍数もない → a=6(オ)
                 (ii) A∩B̄={7} → a=7(カ), b=6(キ)  ※全探索で一意
  〔2〕 一般四角形ABCDの面積公式 S=(1/2)(AB·AD+BC·CD)sinA …① を導出(ク〜サ)し、
       半径5の円Oに接する△PQRの2つの四角形PMOK・QLOMに①を適用。
       (i) PK=15,QL=3 → PMOK面積75(シス)/sinP=3/5(セソ)/sinQ=15/17(タチツテ)/
           PR:QR=25:17(トナ:ニヌ)/RL=45/2(ネノ/ハ)
       (ii) PK=5√2,QL=2√2 反対側 → RL=35√2(ヒフ√ヘ)

第2問 〔1〕2次関数 / 〔2〕データの分析
  〔1〕 (1) y=2x²−4x−1, 0≦x≦3 → 最大x=3で5, 最小x=1で−3 (ア,イ,ウ,エオ)
       (2)(i) 条件1 → 頂点(−2,5)(カ=③), f(x)=−x²−4x+1 (キク=−1, ケ=4, コ=1)
          (ii) 条件2 → 下に凸(サ=⓪), g(x)=x²−8x+12 (シ=⑥)
       (3) 条件3 → h(x)非一意だがx軸との共有点は x=3, x=7 (ス,セ 順不同)
  〔2〕 男子1500m自由形28人のタイム分析(オリジナル・T前/T後/T前後=平均)。
       (1) 散布図2枚 → (a)真(b)真 → ソ=⓪
       (2) 相関係数 r=0.90 → タ=⑤
       (3)(i) 1位の選手の四分位範囲 0.15秒 (チツ=15) ※外れ値境界差=4×IQR
          (ii) 28人の箱ひげ図(分散昇順) → (a)偽(b)真 → テ=②
          (iii) 2×2分割表 n=6(ト) / 割合 P=6/8>Q=8/20 → ナ=②

検証: content/verify_math1a_a.py (sympy/全数列挙で全スロット独立導出)
"""
from math import gcd, hypot

# =========================================================================
#  第2問〔2〕 データの分析: データ定義とSVG生成
# =========================================================================

# --- 散布図データ(28選手): T前, T後. T前後=(T前+T後)/2 ---
_TMAE = [444, 447, 449, 451, 453, 455, 458, 460, 462, 464,
         471, 473, 475, 477, 479, 481, 483, 485, 487, 489,
         446, 452, 457, 459, 463, 465, 470, 472]
_TATO = [458, 455, 453, 457, 457, 459, 470, 468, 468, 472,
         483, 483, 479, 489, 491, 487, 487, 495, 493, 495,
         454, 458, 471, 473, 475, 479, 482, 480]
_TZEN = [(_TMAE[i] + _TATO[i]) // 2 for i in range(28)]   # T前後(平均・整数)
_A_IDX = 23   # 選手A (T前=459, T後=473, T前後=466)


def _scatter_svg(ykind):
    """散布図SVG。ykind='ato'→図1(T前×T後), 'zen'→図2(T前×T前後)。"""
    ys = _TATO if ykind == "ato" else _TZEN
    # 描画領域: 横軸T前 440..490, 縦軸 440..500
    XW, YW = 300, 300
    ML, MT = 46, 14      # 左・上マージン
    x0, x1 = 440, 490
    y0, y1 = 440, 500
    W = ML + XW + 16
    H = MT + YW + 34

    def sx(v):
        return ML + (v - x0) / (x1 - x0) * XW

    def sy(v):
        return MT + (y1 - v) / (y1 - y0) * YW

    s = [f"<svg viewBox='0 0 {W} {H}' width='250' xmlns='http://www.w3.org/2000/svg'>",
         "<g font-family='Helvetica Neue,Arial,sans-serif' font-size='10' fill='#333'>"]
    # 点線グリッド(10刻み)
    for gx in range(x0, x1 + 1, 10):
        s.append(f"<line x1='{sx(gx):.1f}' y1='{sy(y0):.1f}' x2='{sx(gx):.1f}' y2='{sy(y1):.1f}' "
                 f"stroke='#ccc' stroke-width='0.6' stroke-dasharray='2 2'/>")
    for gy in range(y0, y1 + 1, 10):
        s.append(f"<line x1='{sx(x0):.1f}' y1='{sy(gy):.1f}' x2='{sx(x1):.1f}' y2='{sy(gy):.1f}' "
                 f"stroke='#ccc' stroke-width='0.6' stroke-dasharray='2 2'/>")
    # 軸
    s.append(f"<line x1='{sx(x0):.1f}' y1='{sy(y0):.1f}' x2='{sx(x1):.1f}' y2='{sy(y0):.1f}' stroke='#333' stroke-width='1.1'/>")
    s.append(f"<line x1='{sx(x0):.1f}' y1='{sy(y0):.1f}' x2='{sx(x0):.1f}' y2='{sy(y1):.1f}' stroke='#333' stroke-width='1.1'/>")
    # 目盛数値
    for gx in range(x0, x1 + 1, 10):
        s.append(f"<text x='{sx(gx):.1f}' y='{sy(y0) + 13:.1f}' text-anchor='middle'>{gx}</text>")
    for gy in range(y0, y1 + 1, 10):
        s.append(f"<text x='{sx(x0) - 5:.1f}' y='{sy(gy) + 3.5:.1f}' text-anchor='end'>{gy}</text>")
    # 軸ラベル(秒): 横軸は末尾目盛(490)と重ならないよう一段下・右へ / 縦軸は左上
    s.append(f"<text x='{sx(x1) + 4:.1f}' y='{sy(y0) + 25:.1f}' text-anchor='middle'>(秒)</text>")
    s.append(f"<text x='{sx(x0) - 30:.1f}' y='{sy(y1) - 4:.1f}'>(秒)</text>")
    # 点
    for i in range(28):
        cx, cy = sx(_TMAE[i]), sy(ys[i])
        s.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='2.7' fill='none' stroke='#333' stroke-width='1'/>")
        if i == _A_IDX:
            s.append(f"<text x='{cx + 5:.1f}' y='{cy - 4:.1f}' font-size='11' font-weight='700'>A</text>")
    s.append("</g></svg>")
    return "".join(s)


_FIG1_SVG = _scatter_svg("ato")   # T前×T後
_FIG2_SVG = _scatter_svg("zen")   # T前×T前後


# --- (3)(i) 1位の選手の30ラップ(50m毎) → 四分位範囲0.15 ---
_LAP1 = [28.98, 29.07, 29.28, 29.33, 29.36, 29.38, 29.39, 29.40, 29.42, 29.43,
         29.45, 29.46, 29.47, 29.49, 29.50, 29.51, 29.52, 29.53, 29.54, 29.545,
         29.55, 29.55, 29.55, 29.58, 29.62, 29.66, 29.70, 29.74, 29.82, 29.60]


def _boxplot_ref_svg():
    """(3)(i)参考図: 外れ値付き箱ひげ図の凡例(境界2本+外れ値)。"""
    W, H = 300, 96
    x0, x1 = 28.8, 30.0
    ML = 14

    def sx(v):
        return ML + (v - x0) / (x1 - x0) * (W - 2 * ML)

    yb = 40   # 箱の中心y
    s = [f"<svg viewBox='0 0 {W} {H}' width='330' xmlns='http://www.w3.org/2000/svg'>",
         "<g font-family='Helvetica Neue,Arial,sans-serif' font-size='9.5' fill='#333'>"]
    # 数直線
    s.append(f"<line x1='{sx(x0):.1f}' y1='72' x2='{sx(x1):.1f}' y2='72' stroke='#333' stroke-width='1'/>")
    for gv in [28.8, 29.0, 29.2, 29.4, 29.6, 29.8, 30.0]:
        s.append(f"<line x1='{sx(gv):.1f}' y1='69' x2='{sx(gv):.1f}' y2='72' stroke='#333' stroke-width='0.8'/>")
        s.append(f"<text x='{sx(gv):.1f}' y='84' text-anchor='middle'>{gv:g}</text>")
    # 箱ひげ (Q1=29.40, med=29.505, Q3=29.55, whisker 29.28..29.74)
    q1, med, q3, wl, wr = 29.40, 29.505, 29.55, 29.28, 29.74
    s.append(f"<rect x='{sx(q1):.1f}' y='{yb - 9}' width='{sx(q3) - sx(q1):.1f}' height='18' fill='none' stroke='#333' stroke-width='1.1'/>")
    s.append(f"<line x1='{sx(med):.1f}' y1='{yb - 9}' x2='{sx(med):.1f}' y2='{yb + 9}' stroke='#333' stroke-width='1.1'/>")
    s.append(f"<line x1='{sx(wl):.1f}' y1='{yb}' x2='{sx(q1):.1f}' y2='{yb}' stroke='#333' stroke-width='1'/>")
    s.append(f"<line x1='{sx(q3):.1f}' y1='{yb}' x2='{sx(wr):.1f}' y2='{yb}' stroke='#333' stroke-width='1'/>")
    for wv in (wl, wr):
        s.append(f"<line x1='{sx(wv):.1f}' y1='{yb - 6}' x2='{sx(wv):.1f}' y2='{yb + 6}' stroke='#333' stroke-width='1'/>")
    # 外れ値の白丸(下側2個・上側1個)
    for ov in (28.98, 29.07, 29.82):
        s.append(f"<circle cx='{sx(ov):.1f}' cy='{yb}' r='2.6' fill='none' stroke='#333' stroke-width='1'/>")
    # 境界線2本(29.175 / 29.775)と外れ値ラベル
    for bv in (29.175, 29.775):
        s.append(f"<line x1='{sx(bv):.1f}' y1='16' x2='{sx(bv):.1f}' y2='72' stroke='#333' stroke-width='0.9' stroke-dasharray='3 2'/>")
        s.append(f"<text x='{sx(bv):.1f}' y='12' text-anchor='middle' font-size='8.5'>{bv:g}</text>")
    s.append(f"<text x='{sx(28.98):.1f}' y='{yb - 9}' text-anchor='middle' font-size='8'>外れ値</text>")
    s.append(f"<text x='{sx(29.82):.1f}' y='{yb - 9}' text-anchor='middle' font-size='8'>外れ値</text>")
    s.append("</g></svg>")
    return "".join(s)


_BOXREF_SVG = _boxplot_ref_svg()


# --- (3)(ii) 28人の箱ひげ図(分散昇順・上から) ---
# 各行 (min, Q1, med, Q3, max, [外れ値]).  分散小→大の順に上から並ぶ。
_BOX28 = [
    (29.20, 29.40, 29.50, 29.55, 29.72, [28.98, 29.07, 29.82]),
    (29.16, 29.36, 29.51, 29.60, 29.80, [29.90]),
    (29.10, 29.34, 29.50, 29.62, 29.86, []),
    (29.05, 29.32, 29.50, 29.64, 29.92, [28.90]),
    (28.98, 29.30, 29.49, 29.66, 29.98, []),
    (29.02, 29.28, 29.51, 29.70, 30.04, [28.82]),
    (28.90, 29.26, 29.50, 29.72, 30.10, []),
    (28.84, 29.24, 29.48, 29.75, 30.18, []),
    (28.78, 29.22, 29.50, 29.78, 30.25, [28.60]),
    (28.72, 29.18, 29.49, 29.80, 30.32, []),
    (28.66, 29.15, 29.51, 29.84, 30.40, [28.48]),
    (28.60, 29.12, 29.50, 29.88, 30.48, []),
    (28.54, 29.08, 29.50, 29.92, 30.56, []),
    (28.48, 29.05, 29.48, 29.96, 30.66, [28.30]),
    (28.42, 29.00, 29.52, 30.02, 30.76, []),
    (28.36, 28.96, 29.50, 30.06, 30.86, [28.18]),
    (28.30, 28.92, 29.49, 30.12, 30.98, []),
    (28.20, 29.32, 29.55, 29.68, 31.20, []),      # 分散大なのに箱が細い行
    (28.18, 28.85, 29.51, 30.22, 31.28, [27.98]),
    (28.10, 28.80, 29.50, 30.28, 31.40, []),
    (28.05, 28.90, 29.52, 30.30, 31.55, []),
    (27.95, 28.72, 29.49, 30.38, 31.66, [27.72]),
    (27.86, 28.68, 29.51, 30.44, 31.78, []),
    (28.00, 28.64, 29.50, 30.50, 31.98, []),
    (27.70, 28.58, 29.52, 30.56, 32.10, [27.48]),
    (27.60, 28.52, 29.50, 30.62, 32.24, []),
    (27.50, 28.46, 29.51, 30.70, 32.40, [27.30]),
    (27.30, 28.40, 29.50, 30.78, 32.56, []),
]
# 上から分散小→大の順に並ぶ「順位」(=実際の着順)。variance-rank i 行目の選手着順。
_RANK_ORDER = [1, 6, 12, 3, 2, 18, 5, 21, 15, 24, 4, 19, 11, 26,
               8, 7, 10, 13, 9, 25, 14, 16, 23, 17, 20, 27, 22, 28]


def _box28_svg():
    """図3: 28人分の箱ひげ図(横軸26〜34秒・上から分散小順)。"""
    x0, x1 = 26, 34
    ML = 40           # 左(順位ラベル用)
    PW = 430          # プロット幅
    rowh = 15.5
    W = ML + PW + 30  # 右端の単位ラベル(秒)の逃げ幅
    H = 24 + 28 * rowh + 8

    def sx(v):
        return ML + (v - x0) / (x1 - x0) * PW

    s = [f"<svg viewBox='0 0 {W:.0f} {H:.0f}' width='500' xmlns='http://www.w3.org/2000/svg'>",
         "<g font-family='Helvetica Neue,Arial,sans-serif' font-size='9' fill='#333'>"]
    top = 20
    bottom = top + 28 * rowh
    # 縦の点線グリッド(1秒刻み)+目盛数値
    for gv in range(x0, x1 + 1):
        s.append(f"<line x1='{sx(gv):.1f}' y1='{top - 3}' x2='{sx(gv):.1f}' y2='{bottom}' "
                 f"stroke='#ccc' stroke-width='0.6' stroke-dasharray='2 2'/>")
        s.append(f"<text x='{sx(gv):.1f}' y='{top - 6}' text-anchor='middle'>{gv}</text>")
    s.append(f"<text x='{sx(x1) + 13:.1f}' y='{top - 6}'>(秒)</text>")
    for r in range(28):
        yc = top + r * rowh + rowh / 2
        mn, q1, med, q3, mx, outs = _BOX28[r]
        rank = _RANK_ORDER[r]
        # 順位ラベル
        s.append(f"<text x='{ML - 6}' y='{yc + 3:.1f}' text-anchor='end'>{rank}位</text>")
        # 行区切り(点線)
        s.append(f"<line x1='{ML}' y1='{top + r * rowh:.1f}' x2='{ML + PW}' y2='{top + r * rowh:.1f}' "
                 f"stroke='#e2e2e2' stroke-width='0.5' stroke-dasharray='1 2'/>")
        # ひげ
        s.append(f"<line x1='{sx(mn):.1f}' y1='{yc:.1f}' x2='{sx(q1):.1f}' y2='{yc:.1f}' stroke='#333' stroke-width='0.9'/>")
        s.append(f"<line x1='{sx(q3):.1f}' y1='{yc:.1f}' x2='{sx(mx):.1f}' y2='{yc:.1f}' stroke='#333' stroke-width='0.9'/>")
        for wv in (mn, mx):
            s.append(f"<line x1='{sx(wv):.1f}' y1='{yc - 3:.1f}' x2='{sx(wv):.1f}' y2='{yc + 3:.1f}' stroke='#333' stroke-width='0.9'/>")
        # 箱
        s.append(f"<rect x='{sx(q1):.1f}' y='{yc - 4:.1f}' width='{sx(q3) - sx(q1):.1f}' height='8' fill='none' stroke='#333' stroke-width='0.9'/>")
        s.append(f"<line x1='{sx(med):.1f}' y1='{yc - 4:.1f}' x2='{sx(med):.1f}' y2='{yc + 4:.1f}' stroke='#333' stroke-width='0.9'/>")
        # 外れ値(白丸)
        for ov in outs:
            s.append(f"<circle cx='{sx(ov):.1f}' cy='{yc:.1f}' r='2.1' fill='none' stroke='#333' stroke-width='0.8'/>")
    s.append("</g></svg>")
    return "".join(s)


_BOX28_SVG = _box28_svg()


# --- 〔2〕(2)(i) 参考図: 円Oに三辺で接する△PQR(内接円) ---
def _pqr_ref_svg():
    import math as _mm
    W, H = 280, 210
    # 三角形の頂点(概念図。M が Q 寄りになるよう非対称)
    P = (34.0, 178.0); Q = (256.0, 178.0); R = (176.0, 34.0)

    def _d(A, B):
        return _mm.hypot(A[0] - B[0], A[1] - B[1])

    # 内心 I = (a·P + b·Q + c·R)/(a+b+c),  a=|QR|,b=|RP|,c=|PQ|
    a, b, c = _d(Q, R), _d(R, P), _d(P, Q)
    s_ = a + b + c
    O = ((a * P[0] + b * Q[0] + c * R[0]) / s_,
         (a * P[1] + b * Q[1] + c * R[1]) / s_)
    # 内接円半径 = 面積/半周長
    area = abs((Q[0]-P[0])*(R[1]-P[1]) - (R[0]-P[0])*(Q[1]-P[1])) / 2
    r = area / (s_ / 2)

    def _foot(A, B):
        """線分ABへ O から下ろした垂線の足(=接点)。"""
        ax, ay = A; bx, by = B
        t = ((O[0]-ax)*(bx-ax) + (O[1]-ay)*(by-ay)) / ((bx-ax)**2 + (by-ay)**2)
        return (ax + t*(bx-ax), ay + t*(by-ay))

    M = _foot(P, Q)   # PQ上の接点
    K = _foot(P, R)   # PR上の接点
    L = _foot(Q, R)   # QR上の接点

    s = [f"<svg viewBox='0 0 {W} {H}' width='240' xmlns='http://www.w3.org/2000/svg'>",
         "<g font-family='Helvetica Neue,Arial,sans-serif' font-size='11' fill='#333'>"]
    s.append(f"<path d='M{P[0]:.1f} {P[1]:.1f} L{Q[0]:.1f} {Q[1]:.1f} L{R[0]:.1f} {R[1]:.1f} Z' "
             f"fill='none' stroke='#333' stroke-width='1.2'/>")
    s.append(f"<circle cx='{O[0]:.1f}' cy='{O[1]:.1f}' r='{r:.1f}' fill='none' stroke='#333' stroke-width='1.1'/>")
    s.append(f"<circle cx='{O[0]:.1f}' cy='{O[1]:.1f}' r='1.6' fill='#333'/>")
    for (pt, lab, dx, dy) in [(P, "P", -12, 6), (Q, "Q", 7, 6), (R, "R", -2, -6),
                              (O, "O", 7, 4), (M, "M", -3, 15), (K, "K", -14, 2), (L, "L", 7, 2)]:
        if lab not in ("R", "O"):
            s.append(f"<circle cx='{pt[0]:.1f}' cy='{pt[1]:.1f}' r='1.6' fill='#333'/>")
        s.append(f"<text x='{pt[0] + dx:.1f}' y='{pt[1] + dy:.1f}'>{lab}</text>")
    s.append("</g></svg>")
    return "".join(s)


_PQR_REF_SVG = _pqr_ref_svg()


# =========================================================================
#  SECTIONS
# =========================================================================

_KUKE_CHOICES = [r"$\mathrm{AD}\cdot\mathrm{CD}$", r"$\mathrm{AB}\cdot\mathrm{AD}$",
                 r"$\mathrm{AB}\cdot\mathrm{BC}$", r"$\mathrm{AB}\cdot\mathrm{CD}$",
                 r"$\mathrm{BC}\cdot\mathrm{CD}$", r"$\mathrm{AD}\cdot\mathrm{BC}$",
                 r"$\mathrm{BD}\cdot\mathrm{CD}$", r"$\mathrm{AB}\cdot\mathrm{BD}$",
                 r"$\mathrm{AC}\cdot\mathrm{BD}$"]
_KO_CHOICES = [r"$90^\circ$", r"$120^\circ$", r"$135^\circ$", r"$150^\circ$",
               r"$180^\circ$", r"$240^\circ$", r"$270^\circ$", r"$360^\circ$"]  # 昇順
_SA1_CHOICES = [r"$\mathrm{AB}\cdot\mathrm{AD}-\mathrm{BC}\cdot\mathrm{CD}$",
                r"$\mathrm{AB}\cdot\mathrm{BD}+\mathrm{BC}\cdot\mathrm{BD}$",
                r"$\mathrm{AB}\cdot\mathrm{AD}+\mathrm{BC}\cdot\mathrm{CD}$",
                r"$\mathrm{AB}\cdot\mathrm{BD}-\mathrm{BC}\cdot\mathrm{BD}$",
                r"$\mathrm{AD}\cdot\mathrm{BD}+\mathrm{BD}\cdot\mathrm{CD}$",
                r"$\mathrm{AD}\cdot\mathrm{BD}-\mathrm{BD}\cdot\mathrm{CD}$",
                r"$\mathrm{AB}\cdot\mathrm{CD}+\mathrm{AD}\cdot\mathrm{BC}$",
                r"$\mathrm{AB}\cdot\mathrm{CD}-\mathrm{AD}\cdot\mathrm{BC}$",
                r"$\mathrm{AC}\cdot\mathrm{BD}$"]

_SET_CHOICES = [
    r"$\{6,\,12,\,18,\,24\}$",
    r"$\{3,\,9,\,15,\,21\}$",
    r"$\{2,\,3,\,4,\,6,\,8\}$",
    r"$\{4,\,8,\,12,\,16,\,20,\,24\}$",
    r"$\{5,\,7,\,11,\,13,\,17,\,19,\,23\}$",
    r"$\{3,\,6,\,9,\,12,\,15,\,18,\,21\}$",
    r"$\{3,\,6,\,9,\,12,\,15,\,18,\,21,\,24\}$",
    r"$\{2,\,4,\,8,\,10,\,14,\,16,\,20,\,22\}$",
    r"$\{2,\,4,\,6,\,8,\,10,\,12,\,14,\,16,\,18,\,20,\,22,\,24\}$",
    r"$\{2,\,3,\,4,\,6,\,8,\,9,\,10,\,12,\,14,\,15,\,16,\,18,\,20,\,21,\,22,\,24\}$",
]

_KAKU_CHOICES = [  # 第2問〔1〕(2)(i) 頂点座標
    r"$(0,\ 5)$", r"$(1,\ 5)$", r"$(2,\ 5)$", r"$(-2,\ 5)$", r"$(-5,\ 5)$",
    r"$(0,\ -4)$", r"$(-2,\ -4)$", r"$(-5,\ -4)$", r"$(2,\ -4)$", r"$(5,\ -4)$",
]
_SI_CHOICES = [   # 第2問〔1〕(2)(ii) 2次式
    r"$-x^2+8x-12$", r"$x^2-8$", r"$-x^2+8$", r"$x^2-4x+3$",
    r"$2x^2-16x+24$", r"$-2x^2+16x-24$", r"$x^2-8x+12$", r"$-x^2+4x-3$",
    r"$2x^2-9x+7$", r"$-2x^2+9x-7$",
]
_TA_CHOICES = ["0.02", "0.24", "0.47", "0.62", "0.75", "0.90", "0.83", "1.12", "3.64", "4.14"]


SECTIONS = [
    # ================= 第1問 =================
    {"no": 1, "points": 30, "parts": [
        # ---------- 〔1〕 集合と命題 ----------
        {"label": "〔1〕", "blocks": [
            {"t": "p", "text": r"2以上24以下の自然数全体の集合を $U$ とする。すなわち"},
            {"t": "m", "tex": r"U=\{2,\ 3,\ 4,\ \cdots,\ 24\}"},
            {"t": "p", "text": r"である。2以上9以下の自然数 $a$ に対して，$U$ の要素 $k$ で「$k$ と $a$ が1以外の正の公約数をもつ」もの全体の集合を $A$ とする。同様に，2以上9以下の自然数 $b$ に対して，$U$ の要素 $k$ で「$k$ と $b$ が1以外の正の公約数をもつ」もの全体の集合を $B$ とする。"},
            {"t": "p", "text": r"たとえば $a=5$ のとき $A=\{5,\,10,\,15,\,20\}$ であり，$a=8$ のとき $A=\{2,\,4,\,6,\,8,\,10,\,12,\,14,\,16,\,18,\,20,\,22,\,24\}$ である。"},
            {"t": "p", "text": r"<b>(1)</b> $a=3$，$b=4$ とする。このとき $A=〚ア〛$，$B=〚イ〛$ である。また，$B$ の補集合を $\overline{B}$ で表すと"},
            {"t": "m", "tex": r"A\cap B=〚ウ〛,\qquad A\cap\overline{B}=〚エ〛"},
            {"t": "p", "text": r"である。"},
            {"t": "choices", "for": r"〚ア〛〜〚エ〛の解答群（同じものを繰り返し選んでもよい。）",
             "items": _SET_CHOICES, "cols": 1},   # 長い集合(⑨は16要素)がMathMLで折返せないため1列で全幅に
            {"t": "p", "text": r"<b>(2)</b> $a$，$b$ が2以上9以下の自然数であることに注意して，次の問いに答えよ。"},
            {"t": "p", "text": r"　(i) $\overline{A}$ の要素に，2の倍数も3の倍数もないとき $a=〔オ〕$ である。", "indent": False},
            {"t": "p", "text": r"　(ii) $A\cap\overline{B}=\{7\}$ であるとき $a=〔カ〕$，$b=〔キ〕$ である。", "indent": False},
        ]},
        # ---------- 〔2〕 図形と計量 ----------
        {"label": "〔2〕", "blocks": [
            {"t": "p", "text": r"以下の問題において，比を解答する場合は，最も簡単な整数の比で答えよ。"},
            {"t": "p", "text": r"<b>(1)</b> 四角形 ABCD において，四つの内角 $\angle\mathrm{A}$，$\angle\mathrm{B}$，$\angle\mathrm{C}$，$\angle\mathrm{D}$ の大きさをそれぞれ $A$，$B$，$C$，$D$ で表す（いずれも $180^\circ$ より小さいとする）。対角線 BD によって四角形 ABCD を $\triangle$ABD と $\triangle$BCD に分けると，それぞれの面積 $S_1$，$S_2$ は"},
            {"t": "m", "tex": r"S_1=\frac{1}{2}\,〚ク〛\,\sin A,\qquad S_2=\frac{1}{2}\,〚ケ〛\,\sin C"},
            {"t": "p", "text": r"と表される。"},
            {"t": "choices", "for": r"〚ク〛，〚ケ〛の解答群（同じものを繰り返し選んでもよい。）",
             "items": _KUKE_CHOICES, "cols": 3},
            {"t": "p", "text": r"いま，四つの内角が $A+C=B+D$ を満たすとする。四角形の内角の和が $360^\circ$ であることから"},
            {"t": "m", "tex": r"A+C=〚コ〛"},
            {"t": "p", "text": r"となる。"},
            {"t": "choices", "for": r"〚コ〛", "auto_intro": True, "items": _KO_CHOICES, "cols": 4},
            {"t": "p", "text": r"このとき $\sin C$ を $\sin A$ を用いて表せることに注意すると，四角形 ABCD の面積 $S=S_1+S_2$ は"},
            {"t": "m", "tex": r"S=S_1+S_2=\frac{1}{2}\,〚サ〛\,\sin A\qquad\cdots\cdots\ \text{①}"},
            {"t": "p", "text": r"と表される。"},
            {"t": "choices", "for": r"〚サ〛", "auto_intro": True, "items": _SA1_CHOICES, "cols": 2},
            {"t": "p", "text": r"<b>(2)</b> 半径5の円 O が，線分 PQ 上の点 M（P，Q とは異なる）で接している。P，Q のそれぞれから，円 O へ直線 PQ とは異なる接線を引き，その接点を K，L とする。2直線 PK，QL が交わる場合を考え，その交点を R とする。"},
            {"t": "p", "text": r"　(i) $\mathrm{PK}=15$，$\mathrm{QL}=3$ とし，$\angle\mathrm{KPM}=P$，$\angle\mathrm{LQM}=Q$ とおく。このとき，交点 R は直線 PQ に関して点 O と<b>同じ側</b>にある。", "indent": False},
            {"t": "fig", "svg": _PQR_REF_SVG, "caption": "参考図"},
            {"t": "p", "text": r"接線の性質から $\mathrm{PM}=\mathrm{PK}$，$\mathrm{OM}=\mathrm{OK}$ であり，$\angle\mathrm{PMO}=\angle\mathrm{PKO}=90^\circ$ である。四角形 PMOK が $\triangle$PMO と $\triangle$PKO に分けられることに注意すると，四角形 PMOK の面積は $〔シ〕〔ス〕$ である。"},
            {"t": "p", "text": r"一方，四角形 PMOK に①を適用すると，$\angle\mathrm{PMO}=\angle\mathrm{PKO}=90^\circ$ より $P+\angle\mathrm{MOK}=180^\circ$ が成り立つので，上で求めた面積とあわせて"},
            {"t": "m", "tex": r"\sin P=\frac{〔セ〕}{〔ソ〕}"},
            {"t": "p", "text": r"が得られる。四角形 QLOM についても同様に考えると"},
            {"t": "m", "tex": r"\sin Q=\frac{〔タ〕〔チ〕}{〔ツ〕〔テ〕}"},
            {"t": "p", "text": r"である。よって，正弦定理により"},
            {"t": "m", "tex": r"\mathrm{PR}:\mathrm{QR}=〔ト〕〔ナ〕:〔ニ〕〔ヌ〕"},
            {"t": "p", "text": r"となり，これにより"},
            {"t": "m", "tex": r"\mathrm{RL}=\frac{〔ネ〕〔ノ〕}{〔ハ〕}"},
            {"t": "p", "text": r"と求められるので，$\triangle$PQR の3辺の長さを求めることができる。"},
            {"t": "p", "text": r"　(ii) $\mathrm{PK}=5\sqrt{2}$，$\mathrm{QL}=2\sqrt{2}$ とする。このとき，交点 R は直線 PQ に関して点 O と<b>反対側</b>にある。このことに注意すると", "indent": False},
            {"t": "m", "tex": r"\mathrm{RL}=〔ヒ〕〔フ〕\sqrt{〔ヘ〕}"},
            {"t": "p", "text": r"である。"},
        ]},
    ]},

    # ================= 第2問 =================
    {"no": 2, "points": 30, "parts": [
        # ---------- 〔1〕 2次関数 ----------
        {"label": "〔1〕", "blocks": [
            {"t": "p", "text": r"<b>(1)</b> 2次関数"},
            {"t": "m", "tex": r"y=2x^2-4x-1"},
            {"t": "p", "text": r"は $0\le x\le 3$ において，$x=〔ア〕$ で最大値 $〔イ〕$ をとり，$x=〔ウ〕$ で最小値 $〔エ〕〔オ〕$ をとる。"},
            {"t": "p", "text": r"<b>(2)</b> 次に，$x$ の値の範囲とそのときの最大値・最小値に関する条件が与えられているとき，その条件を満たす2次関数を求めることを考える。"},
            {"t": "convo", "turns": [
                {"sp": "太郎", "text": r"(1)では，2次関数と $x$ のとり得る値の範囲が与えられていて，最大値と最小値を求めることができたね。"},
                {"sp": "花子", "text": r"じゃあ，逆に，$x$ の範囲とそのときの最大値・最小値に関する条件から，条件を満たす2次関数を求めることはできるのかな。具体的な例で考えてみよう。"},
            ]},
            {"t": "p", "text": r"　(i) 2次関数 $y=f(x)$ は次の<b>条件1</b>を満たすとする。", "indent": False},
            {"t": "boxnote", "title": "条件1", "lines": [
                r"$y=f(x)$ は $-5\le x\le 0$ において",
                r"　・$x=-2$ で最大値 $5$ をとる。",
                r"　・$x=-5$ で最小値 $-4$ をとる。",
            ]},
            {"t": "p", "text": r"このとき，$y=f(x)$ のグラフの頂点の座標は $〚カ〛$ であり"},
            {"t": "m", "tex": r"f(x)=〔キ〕〔ク〕x^2-〔ケ〕x+〔コ〕"},
            {"t": "p", "text": r"である。"},
            {"t": "choices", "for": r"〚カ〛", "auto_intro": True, "items": _KAKU_CHOICES, "cols": 3},
            {"t": "p", "text": r"　(ii) 2次関数 $y=g(x)$ は次の<b>条件2</b>を満たすとする。", "indent": False},
            {"t": "boxnote", "title": "条件2", "lines": [
                r"$a$ を正の定数とし，$y=g(x)$ の $0\le x\le a$ における最大値を $M$，最小値を $m$ とすると",
                r"　・$0<a<4$ ならば，$m>-4$",
                r"　・$a\ge 4$ ならば，$m=-4$",
                r"　・$0<a\le 8$ ならば，$M=12$",
                r"　・$a>8$ ならば，$M>12$",
            ]},
            {"t": "p", "text": r"このとき，$y=g(x)$ のグラフは $〚サ〛$ の放物線であり"},
            {"t": "m", "tex": r"g(x)=〚シ〛"},
            {"t": "p", "text": r"である。"},
            {"t": "choices", "for": r"〚サ〛", "auto_intro": True,
             "items": [r"下に凸", r"上に凸"], "cols": 2},
            {"t": "choices", "for": r"〚シ〛", "auto_intro": True, "items": _SI_CHOICES, "cols": 2},
            {"t": "p", "text": r"<b>(3)</b> 2次関数 $y=h(x)$ は次の<b>条件3</b>を満たすとする。"},
            {"t": "boxnote", "title": "条件3", "lines": [
                r"$b$ を定数とし，$y=h(x)$ の $b-1\le x\le b+1$ における最大値を $M$ とすると",
                r"　・$2\le b\le 8$ ならば，$M\ge 0$",
                r"　・$b<2$ または $8<b$ ならば，$M<0$",
            ]},
            {"t": "convo", "turns": [
                {"sp": "太郎", "text": r"(2)の条件1や条件2からは2次関数が一つに決まったけど，条件3だけでは，$h(x)$ が一つに決まりそうにないね。"},
                {"sp": "花子", "text": r"でも，$y=h(x)$ のグラフと $x$ 軸の共有点の座標はわかりそうだね。"},
            ]},
            {"t": "p", "text": r"2次関数 $y=h(x)$ のグラフと $x$ 軸の共有点の $x$ 座標は $〔ス〕$ および $〔セ〕$ である。ただし，$〔ス〕$，$〔セ〕$ の解答の順序は問わない。"},
        ]},
        # ---------- 〔2〕 データの分析 ----------
        {"label": "〔2〕", "blocks": [
            {"t": "p", "text": r"以下では，値の集まりについて，次のように定めた基準で<b>外れ値</b>を定義する。"},
            {"t": "boxnote", "title": None, "lines": [
                r"　（第1四分位数）$-\,1.5\times$（四分位範囲）　以下の値",
                r"　（第3四分位数）$+\,1.5\times$（四分位範囲）　以上の値",
            ]},
            {"t": "p", "text": r"水泳部の太郎さんは，ペース配分を検討するため，ある年の男子1500m自由形の予選に出場した28人の選手の記録を分析することにした。ここで，自由形とは，どのような泳ぎ方で泳いでもよい競技である。"},
            {"t": "p", "text": r"タイムは秒を単位とし，たとえば15分23秒46は $60\times15+23.46=923.46$（秒）と換算する。順位はタイムが小さいほど上位である。スタートから750m地点までのタイムを <b>T前</b>，750m地点からゴールまでのタイムを <b>T後</b>，T前とT後の平均値を <b>T前後</b> とする。なお，以下の図や表については，架空の大会記録をもとに作成しているものとする。"},
            {"t": "p", "text": r"<b>(1)</b> 図1は横軸に T前，縦軸に T後 をとった散布図，図2は横軸に T前，縦軸に T前後 をとった散布図である（いずれも完全に重なっている点はない）。図中の A は，両図で同一の選手を表す。"},
            {"t": "html", "html": (
                "<div style='display:flex;gap:6mm;justify-content:center;flex-wrap:wrap;align-items:flex-start;'>"
                "<div style='text-align:center;'>" + _FIG1_SVG +
                "<div style='font-size:9pt;margin-top:1mm;'>図1&emsp;T前 と T後 の散布図</div></div>"
                "<div style='text-align:center;'>" + _FIG2_SVG +
                "<div style='font-size:9pt;margin-top:1mm;'>図2&emsp;T前 と T前後 の散布図</div></div>"
                "</div>")},
            {"t": "p", "text": r"次の(a)，(b)について考える。"},
            {"t": "p", "text": r"　(a) T前 が 467.5 秒未満の選手について，T後 が 461.5 秒以上である人数と，T前後 が 461.5 秒以上である人数は等しい。", "indent": False},
            {"t": "p", "text": r"　(b) 選手 A について，T前 の値は T前後 の値より小さく，かつ T後 の値は T前後 の値より大きい。", "indent": False},
            {"t": "p", "text": r"(a)，(b)の正誤の組合せとして正しいものは $〚ソ〛$ である。"},
            {"t": "table", "head": ["", "⓪", "①", "②", "③"],
             "rows": [["(a)", "正", "正", "誤", "誤"], ["(b)", "正", "誤", "正", "誤"]],
             "caption": r"〚ソ〛の解答群"},
            {"t": "p", "text": r"<b>(2)</b> 太郎さんは，T前 と T前後 の相関係数を求めるために，表1のように平均値，標準偏差および共分散を計算した。"},
            {"t": "table", "head": ["", "平均値", "標準偏差", "共分散"],
             "rows": [["T前", "466.0", "8.5", "59.4"], ["T前後", "470.0", "7.8", ""]],
             "caption": r"表1　T前 と T前後 の平均値・標準偏差・共分散",
             "cls": "cov-merge"},
            {"t": "p", "text": r"（共分散の値 59.4 は T前 と T前後 についてのものである。）表1を用いると，T前 と T前後 の相関係数は $〚タ〛$ である。"},
            {"t": "choices", "for": r"〚タ〛", "auto_intro": True, "items": _TA_CHOICES, "cols": 5},
            {"t": "p", "text": r"<b>(3)</b> 太郎さんは，順位とペース配分の関係を調べるため，各選手のタイムを，ゴールまで50mごとの30個のタイムに分けて分析することにした。"},
            {"t": "p", "text": r"　(i) 1位の選手の30個のタイムについて，外れ値かどうかを判断する二つの値 29.175 と 29.775 が算出され，29.175 以下の2個のタイムと 29.775 以上の1個のタイムが外れ値と判断された。このとき，1位の選手の30個のタイムの四分位範囲は $0.〔チ〕〔ツ〕$ 秒である。", "indent": False},
            {"t": "fig", "svg": _BOXREF_SVG, "caption": "参考図"},
            {"t": "p", "text": r"　(ii) 太郎さんは28人の選手それぞれについて，30個のタイムを用いて選手ごとの箱ひげ図を作成し，分散を計算した。図3は，上から分散が小さい順になるように28人の箱ひげ図を並べたものであり，30個のタイムにおける外れ値は白丸で示されている。なお，分散が等しい選手はいなかった。", "indent": False},
            {"t": "fig", "svg": _BOX28_SVG,
             "caption": r"図3　28人の選手の順位と30個のタイムの箱ひげ図（上から分散の小さい順）"},
            {"t": "p", "text": r"図3から読み取れることについて，次の(a)，(b)を考える。"},
            {"t": "p", "text": r"　(a) 28人の選手において，29秒より速いタイムはすべて外れ値である。", "indent": False},
            {"t": "p", "text": r"　(b) 28人の選手から2人を選んだとき，分散の大きい選手の四分位範囲が，分散の小さい選手の四分位範囲より小さいことがある。", "indent": False},
            {"t": "p", "text": r"(a)，(b)の正誤の組合せとして正しいものは $〚テ〛$ である。"},
            {"t": "table", "head": ["", "⓪", "①", "②", "③"],
             "rows": [["(a)", "正", "正", "誤", "誤"], ["(b)", "正", "誤", "正", "誤"]],
             "caption": r"〚テ〛の解答群"},
            {"t": "p", "text": r"　(iii) 1〜8位を<b>決勝進出グループ</b>，9〜28位を<b>予選敗退グループ</b>とよぶことにする。決勝進出グループであり，かつ30個のタイムの分散が小さい方から14番目までである選手の人数を $n$ 人とすると，表2のようになる。", "indent": False},
            {"t": "table",
             "head": ["", "分散1〜14番", "分散15〜28番", "計"],
             "rows": [
                 ["決勝進出グループ", r"$n$", r"$8-n$", "8"],
                 ["予選敗退グループ", r"$14-n$", r"$6+n$", "20"],
                 ["計", "14", "14", "28"],
             ],
             "caption": r"表2　順位と分散の表（単位は人）"},
            {"t": "p", "text": r"図3から $n=〔ト〕$ であることがわかる。"},
            {"t": "p", "text": r"さらに，決勝進出グループにおいて分散が小さい方から14番目までの選手が占める割合を $P$，予選敗退グループにおいて分散が小さい方から14番目までの選手が占める割合を $Q$ とすると，$P\ 〚ナ〛\ Q$ であることがわかる。"},
            {"t": "choices", "for": r"〚ナ〛", "auto_intro": True,
             "items": [r"$<$", r"$=$", r"$>$"], "cols": 3},
        ]},
    ]},
]


# =========================================================================
#  ANS_SECTIONS
# =========================================================================

ANS_SECTIONS = [
    {"section": 1,
     "slots": {
         # 〔1〕(1) 選択
         "ア": "⑥", "イ": "⑧", "ウ": "⓪", "エ": "①",
         # 〔1〕(2) 数値
         "オ": "6", "カ": "7", "キ": "6",
         # 〔2〕(1) 選択
         "ク": "①", "ケ": "④", "コ": "④", "サ": "②",   # コ=180°(昇順で④)
         # 〔2〕(2)(i)
         "シ": "7", "ス": "5",          # 75
         "セ": "3", "ソ": "5",          # 3/5
         "タ": "1", "チ": "5", "ツ": "1", "テ": "7",   # 15/17
         "ト": "2", "ナ": "5", "ニ": "1", "ヌ": "7",   # 25:17
         "ネ": "4", "ノ": "5", "ハ": "2",             # 45/2
         # 〔2〕(2)(ii)
         "ヒ": "3", "フ": "5", "ヘ": "2",             # 35√2
     },
     "kai": [
         {"heading": "〔1〕 集合と命題", "blocks": [
             {"t": "p", "text": r"$U=\{2,3,\cdots,24\}$。$a=3$ のとき $A$ は「3と1以外の公約数をもつ数」＝3の倍数。$b=4$ のとき $B$ は「4と1以外の公約数をもつ数」＝偶数（2を約数にもつ数）である。"},
             {"t": "p", "text": r"<b>(1)</b> $A=\{3,6,9,12,15,18,21,24\}$（3の倍数・要素数8）＝<b>⑥</b>（ア）。$B=\{2,4,\cdots,24\}$（偶数・要素数12）＝<b>⑧</b>（イ）。"},
             {"t": "p", "text": r"$A\cap B$ は「3の倍数かつ偶数」＝6の倍数 $\{6,12,18,24\}$＝<b>⓪</b>（ウ）。$A\cap\overline{B}$ は「3の倍数だが偶数でない」＝奇数の3の倍数 $\{3,9,15,21\}$＝<b>①</b>（エ）。誤答は $\cup$・補集合との取り違えや要素数の混同を拾う。"},
             {"t": "p", "text": r"<b>(2)(i)</b> $\overline{A}$（$a$ と互いに素寄りの数の集合）に2の倍数も3の倍数も含まれないためには，$A$ が2の倍数と3の倍数をすべて吸収する必要がある。$a=6$ のとき $A=\{2\text{の倍数}\}\cup\{3\text{の倍数}\}$ となり，$\overline{A}=\{5,7,11,13,17,19,23\}$ で条件を満たす。$2\le a\le 9$ で調べると $a=6$ のみ。よって $a=\boxed{6}$（オ）。"},
             {"t": "p", "text": r"<b>(ii)</b> $A\cap\overline{B}=\{7\}$。$7$ が $A$ に入るには $a$ が7と1以外の公約数をもつ数を作る必要があり，$A$ が7を含むのは $a=7$。このとき $A=\{7,14,21\}$。$14=2\cdot7$，$21=3\cdot7$ が $B$ に入り $7$ だけ残るには，$B$ が2の倍数と3の倍数をともに含む，すなわち $b=6$。$2\le a,b\le9$ の全探索で $(a,b)=(7,6)$ が一意。よって $a=\boxed{7}$（カ），$b=\boxed{6}$（キ）。"},
         ]},
         {"heading": "〔2〕 図形と計量", "blocks": [
             {"t": "p", "text": r"<b>(1)</b> $\triangle$ABD の面積は2辺 AB，AD とはさむ角 $A$ から $S_1=\dfrac12\,\mathrm{AB}\cdot\mathrm{AD}\sin A$（ク＝<b>①</b>）。$\triangle$BCD は $S_2=\dfrac12\,\mathrm{BC}\cdot\mathrm{CD}\sin C$（ケ＝<b>④</b>）。"},
             {"t": "p", "text": r"内角の和 $A+B+C+D=360^\circ$ と $A+C=B+D$ より $2(A+C)=360^\circ$，$A+C=180^\circ$（コ＝<b>④</b>）。よって $C=180^\circ-A$ で $\sin C=\sin A$ だから"},
             {"t": "m", "tex": r"S=\tfrac12(\mathrm{AB}\cdot\mathrm{AD}+\mathrm{BC}\cdot\mathrm{CD})\sin A\quad(\text{サ}=②)\ \cdots\text{①}"},
             {"t": "p", "text": r"<b>(2)(i)</b> 接線の長さは等しく $\mathrm{PM}=\mathrm{PK}=15$，$\mathrm{OM}=\mathrm{OK}=5$。四角形 PMOK は直角三角形 PMO，PKO に分かれ，面積は $2\times\dfrac12\cdot15\cdot5=\boxed{75}$（シス）。"},
             {"t": "p", "text": r"①を四角形 PMOK に適用すると，面積は $\dfrac12(\mathrm{PM}\cdot\mathrm{PK}+\mathrm{OM}\cdot\mathrm{OK})\sin P=\dfrac12(15^2+5^2)\sin P=125\sin P$。これが $75$ に等しいから"},
             {"t": "m", "tex": r"\sin P=\frac{75}{125}=\frac{3}{5}\quad(\text{セソ})"},
             {"t": "p", "text": r"同様に四角形 QLOM で $\mathrm{QM}=\mathrm{QL}=3$，半径5より $\dfrac12(3^2+5^2)\sin Q=3\cdot5=15$，$\sin Q=\dfrac{30}{34}=\dfrac{15}{17}$（タチ／ツテ）。$\cos P=\dfrac45$。$\angle Q$ は鈍角（$\tan\frac{Q}{2}=\frac53>1$）だから $\cos Q=-\dfrac{8}{17}$。"},
             {"t": "p", "text": r"$\triangle$PQR で $\mathrm{PR}$ は $\angle Q$ の対辺，$\mathrm{QR}$ は $\angle P$ の対辺。正弦定理より $\mathrm{PR}:\mathrm{QR}=\sin Q:\sin P=\dfrac{15}{17}:\dfrac35=25:17$（トナ：ニヌ）。"},
             {"t": "p", "text": r"$\sin R=\sin(P+Q)=\dfrac35\cdot\left(-\dfrac{8}{17}\right)+\dfrac45\cdot\dfrac{15}{17}=\dfrac{-24+60}{85}=\dfrac{36}{85}$。$\mathrm{PQ}=\mathrm{PM}+\mathrm{QM}=15+3=18$。正弦定理より $\dfrac{\mathrm{PQ}}{\sin R}=\dfrac{18}{36/85}=\dfrac{85}{2}$ とおくと $\mathrm{QR}=\dfrac{85}{2}\sin P=\dfrac{85}{2}\cdot\dfrac35=\dfrac{51}{2}$。接線長は $\mathrm{RL}=\mathrm{RK}=\mathrm{QR}-\mathrm{QL}=\dfrac{51}{2}-3=\dfrac{45}{2}$（ネノ／ハ）。"},
             {"t": "p", "text": r"<b>(ii)</b> $\mathrm{PK}=5\sqrt2$，$\mathrm{QL}=2\sqrt2$ で R が O と反対側にあるときは，同様の計算（配置が補角になる）を行うと $\mathrm{RL}=35\sqrt2$（ヒフ√ヘ）。座標計算でも M を原点，PQ を $x$ 軸，$\mathrm{O}=(0,5)$ とし，P，Q からの第二接線の交点 R を求めると $\mathrm{RO}^2-5^2$ の平方根が $35\sqrt2$ となり一致する。"},
         ]},
     ]},
    {"section": 2,
     "slots": {
         # 〔1〕(1)
         "ア": "3", "イ": "5", "ウ": "1", "エ": "−", "オ": "3",
         # 〔1〕(2)(i)
         "カ": "③", "キ": "−", "ク": "1", "ケ": "4", "コ": "1",
         # 〔1〕(2)(ii)
         "サ": "⓪", "シ": "⑥",
         # 〔1〕(3) 順不同
         "ス": "3", "セ": "7",
         # 〔2〕(1)
         "ソ": "⓪",
         # 〔2〕(2)
         "タ": "⑤",
         # 〔2〕(3)(i) IQR = 0.15
         "チ": "1", "ツ": "5",
         # 〔2〕(3)(ii) 箱ひげ正誤
         "テ": "②",
         # 〔2〕(3)(iii)
         "ト": "6", "ナ": "②",
     },
     "kai": [
         {"heading": "〔1〕 2次関数", "blocks": [
             {"t": "p", "text": r"<b>(1)</b> $y=2x^2-4x-1=2(x-1)^2-3$。頂点 $(1,-3)$。$0\le x\le 3$ で $f(0)=-1$，$f(1)=-3$，$f(3)=5$。よって最大は $x=3$ で $5$（ア＝3，イ＝5），最小は $x=1$ で $-3$（ウ＝1，エオ＝$-3$）。"},
             {"t": "p", "text": r"<b>(2)(i)</b> 条件1より最大を区間内部 $x=-2$ でとるから上に凸で頂点 $(-2,5)$（カ＝<b>③</b>）。$f(x)=a(x+2)^2+5$ とおき，$x=-5$ で最小 $-4$：$f(-5)=9a+5=-4$ より $a=-1$。よって $f(x)=-(x+2)^2+5=-x^2-4x+1$。印字形 $[キク]x^2-[ケ]x+[コ]$ に合わせ キク＝$-1$，ケ＝4，コ＝1。"},
             {"t": "p", "text": r"<b>(ii)</b> 「$a\ge4$ で最小が一定値 $-4$」＝頂点の $x$ 座標が4・最小値 $-4$。「$0<a\le8$ で最大が $g(0)=12$，$a>8$ で増加」＝軸 $x=4$ に関し $g(8)=g(0)=12$。よって下に凸（サ＝<b>⓪</b>）で $g(x)=(x-4)^2-4=x^2-8x+12$（シ＝<b>⑥</b>）。符号反転肢①や凸性違いを消去する。"},
             {"t": "p", "text": r"<b>(3)</b> 条件3は「幅2の窓 $[b-1,b+1]$ での最大 $M\ge0$ となるのは $2\le b\le8$ のときだけ」。上に凸の放物線では $h\ge0$ となる区間が根の間 $[\alpha,\beta]$。窓がこの区間と共有点をもつ条件が $b+1\ge\alpha$ かつ $b-1\le\beta$，すなわち $\alpha-1\le b\le\beta+1$。これが $2\le b\le8$ に一致するので $\alpha=3$，$\beta=7$。$a$（先頭係数）は定まらず $h$ は一つに決まらないが，$x$ 軸との共有点の $x$ 座標は $\boxed{3}$ と $\boxed{7}$（ス，セ・順不同）。"},
         ]},
         {"heading": "〔2〕 データの分析", "blocks": [
             {"t": "p", "text": r"<b>(1)</b> (a) T前 $<467.5$ の16人で，T後 $\ge461.5$ は8人，T前後 $\ge461.5$ も8人で<b>等しい</b>→(a)は正。(b) A は T前 $=459$，T後 $=473$，T前後 $=466$ で $459<466<473$，すなわち T前 $<$ T前後 $<$ T後→(b)も正。組合せ（正，正）で $〚ソ〛=$<b>⓪</b>。（T前後は T前 と T後 の平均だから，T前 $<$ T前後 $<$ T後 は T前 $<$ T後 と同値である点がポイント。）"},
             {"t": "p", "text": r"<b>(2)</b> 相関係数 $r=\dfrac{\text{共分散}}{\text{（標準偏差の積）}}=\dfrac{59.4}{8.5\times7.8}=\dfrac{59.4}{66.3}=0.896\cdots\approx0.90$（タ＝<b>⑤</b>）。誤答は，和で割った $\dfrac{59.4}{8.5+7.8}=3.64$（⑧），逆数 $\dfrac{66.3}{59.4}=1.12$（⑦），共分散を用いない $\dfrac1{8.5\times7.8}=0.02$（⓪）など。$|r|\le1$ より1を超える⑦⑧⑨は直ちに除外できる。"},
             {"t": "p", "text": r"<b>(3)(i)</b> 外れ値の境界は $Q_1-1.5\,\mathrm{IQR}=29.175$，$Q_3+1.5\,\mathrm{IQR}=29.775$。差をとると $(Q_3-Q_1)+3\,\mathrm{IQR}=4\,\mathrm{IQR}=29.775-29.175=0.60$。よって $\mathrm{IQR}=0.15$，四分位範囲は $0.15$ 秒（チツ＝15）。"},
             {"t": "p", "text": r"<b>(ii)</b> (a) 図3の下位（分散大）の行には，外れ値でないタイムが29秒より速い所まで届く行がある（ひげの左端が29秒未満で白丸でない）。よって「29秒より速いタイムはすべて外れ値」は<b>誤</b>。(b) 分散は大きいが箱（四分位範囲）が細い行があり，それより上（分散小）で箱の広い行より四分位範囲が小さい。よって(b)は<b>正</b>（分散の大小とIQRの大小は一致しない）。組合せ（誤，正）で $〚テ〛=$<b>②</b>。"},
             {"t": "p", "text": r"<b>(iii)</b> 図3の上から14行の順位は $\{1,6,12,3,2,18,5,21,15,24,4,19,11,26\}$。このうち順位が8以下（決勝進出）は $\{1,6,3,2,5,4\}$ の6人だから $n=\boxed{6}$（ト）。"},
             {"t": "p", "text": r"割合は $P=\dfrac{n}{8}=\dfrac68=\dfrac34$，$Q=\dfrac{14-n}{20}=\dfrac{8}{20}=\dfrac25$。$\dfrac34>\dfrac25$ なので $P>Q$，$〚ナ〛=$<b>②</b>。"},
         ]},
     ]},
]
