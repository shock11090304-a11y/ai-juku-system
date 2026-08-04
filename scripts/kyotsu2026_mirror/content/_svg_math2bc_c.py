# -*- coding: utf-8 -*-
"""第5・6・7問で使う SVG 図の生成器(単一ソース)。
math2bc_c.py から import して使う。座標は world→pixel を各図で閉じて計算する。
"""
import math as _m


# ---------- 共通ヘルパ ----------
def _svg(w, h, body, wpx):
    return (f"<svg viewBox='0 0 {w:.0f} {h:.0f}' width='{wpx}' "
            f"xmlns='http://www.w3.org/2000/svg'>"
            f"<g font-family='Hiragino Mincho ProN,serif' font-size='11'>{body}</g></svg>")


# ============================================================
# 第5問: 正規分布表の右上に付く小図(0〜z0 灰色塗り)
# ============================================================
def normal_curve_fig():
    W, H = 150, 92
    ox, oy = 22, 70          # 原点
    sx = 34                  # x単位(σ)
    def curve_y(t):          # 標準正規密度 (相対高さ)
        return 46 * _m.exp(-t * t / 2)
    # z0 位置 (t=1.0 のところに z0)
    z0t = 1.0
    pts = [(ox + sx * (i / 20 * 3 - 0), oy - curve_y(i / 20 * 3 - 0))
           for i in range(-30, 31)]
    # 上の pts は t∈[-4.5,4.5]。作り直す:
    pts = []
    tt = -3.0
    while tt <= 3.0001:
        pts.append((ox + sx * tt, oy - curve_y(tt)))
        tt += 0.1
    poly = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    # 灰色部分 0..z0
    fill = [(ox, oy)]
    tt = 0.0
    while tt <= z0t + 1e-9:
        fill.append((ox + sx * tt, oy - curve_y(tt)))
        tt += 0.05
    fill.append((ox + sx * z0t, oy))
    fpath = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in fill) + " Z"
    body = [
        f"<path d='{fpath}' fill='#9a9a9a' fill-opacity='0.55' stroke='none'/>",
        f"<path d='{poly}' fill='none' stroke='#333' stroke-width='1.1'/>",
        f"<line x1='{ox-sx*3:.0f}' y1='{oy}' x2='{ox+sx*3:.0f}' y2='{oy}' stroke='#333' stroke-width='1'/>",
        f"<line x1='{ox}' y1='{oy+4}' x2='{ox}' y2='18' stroke='#333' stroke-width='1'/>",
        f"<text x='{ox-8}' y='{oy+13}' font-style='italic'>O</text>",
        f"<text x='{ox+sx*z0t-4:.0f}' y='{oy+13}' font-size='10'>z</text>",
        f"<text x='{ox+sx*z0t+4:.0f}' y='{oy+15}' font-size='7'>0</text>",
        f"<text x='{ox+sx*3-2:.0f}' y='{oy-5}' font-style='italic'>z</text>",
        f"<line x1='{ox+sx*z0t:.0f}' y1='{oy}' x2='{ox+sx*z0t:.0f}' y2='{oy-curve_y(z0t):.0f}' stroke='#333' stroke-width='0.8' stroke-dasharray='2 2'/>",
    ]
    return _svg(W, H, "".join(body), 150)


# ============================================================
# 第6問 図1: 正六角形 DEFGCA (中心B) + 3本の対角線
#   A(120°),C(60°),D(180°),E(0°),F(240°),G(300°), B=中心
# ============================================================
def hexagon_fig():
    R = 46.0
    cx, cy = 70.0, 62.0
    th = {"A": 120, "C": 60, "D": 180, "E": 0, "F": 240, "G": 300}
    pos = {k: (cx + R * _m.cos(_m.radians(a)), cy - R * _m.sin(_m.radians(a)))
           for k, a in th.items()}
    pos["B"] = (cx, cy)
    # 外周: A(120)->C(60)->E(0)->G(300)->F(240)->D(180)->A  (角度降順で正六角形の辺)
    ring = ["A", "C", "E", "G", "F", "D"]
    poly = "M" + " L".join(f"{pos[k][0]:.1f} {pos[k][1]:.1f}" for k in ring) + " Z"
    body = [f"<path d='{poly}' fill='none' stroke='#333' stroke-width='1.2'/>"]
    # 3本の対角線 (中心通る): A-G, C-F, D-E
    for u, v in [("A", "G"), ("C", "F"), ("D", "E")]:
        body.append(f"<line x1='{pos[u][0]:.1f}' y1='{pos[u][1]:.1f}' "
                    f"x2='{pos[v][0]:.1f}' y2='{pos[v][1]:.1f}' stroke='#333' stroke-width='0.9'/>")
    # ラベル位置微調整
    lab = {"A": (-4, -6), "C": (4, -6), "D": (-12, 2), "E": (6, 2),
           "F": (-10, 12), "G": (4, 12), "B": (5, -3)}
    for k, (x, y) in pos.items():
        body.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.3' fill='#333'/>")
        dx, dy = lab[k]
        body.append(f"<text x='{x+dx:.1f}' y='{y+dy:.1f}' font-size='12'>{k}</text>")
    return _svg(140, 128, "".join(body), 168)


# ============================================================
# 第6問 参考図: 三角形ABC + 辺の中点 H(BC),I(CA),J(AB)
# ============================================================
def triangle_midpoints_fig():
    A = (70.0, 16.0); B = (18.0, 104.0); C = (122.0, 104.0)
    H = ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2)
    I = ((C[0] + A[0]) / 2, (C[1] + A[1]) / 2)
    J = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
    body = [f"<path d='M{A[0]} {A[1]} L{B[0]} {B[1]} L{C[0]} {C[1]} Z' "
            f"fill='none' stroke='#333' stroke-width='1.2'/>"]
    for name, p, dx, dy in [("A", A, -3, -6), ("B", B, -12, 6), ("C", C, 6, 6),
                            ("H", H, -3, 14), ("I", I, 8, 0), ("J", J, -12, 0)]:
        body.append(f"<circle cx='{p[0]}' cy='{p[1]}' r='2.3' fill='#333'/>")
        body.append(f"<text x='{p[0]+dx}' y='{p[1]+dy}' font-size='12'>{name}</text>")
    return _svg(140, 122, "".join(body), 158)


# ============================================================
# 第6問 領域図6択(シ): 三角形ABC + 3直線(AB,AC,BC を両側延長)+塗り
#   ⓪三角形内部 ①∠Cの内角領域 ②三角形+C対頂角 ③ABのC反対側半平面
#   ④ABのC反対側∩BC上側 ⑤ABのC同側半平面
# ============================================================
def region_figs_sec6():
    # world 座標: A(0,3) B(-2,0) C(2,0)。pixel 変換。
    A = (0.0, 3.0); B = (-2.0, 0.0); C = (2.0, 0.0)
    XMIN, XMAX, YMIN, YMAX = -5.0, 5.0, -3.0, 5.0
    W, H = 128, 104
    K = min(W / (XMAX - XMIN), H / (YMAX - YMIN))
    ox = -XMIN * K; oy = YMAX * K

    def sx(x): return ox + x * K
    def sy(y): return oy - y * K

    # 直線を [XMIN,XMAX]×[YMIN,YMAX] でクリップする簡易描画: パラメータで両端を箱外まで延長
    def line_pts(p1, p2):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        t0, t1 = -20, 20
        return ((p1[0] + dx * t0, p1[1] + dy * t0), (p1[0] + dx * t1, p1[1] + dy * t1))

    def clipbox():
        return [(XMIN, YMIN), (XMAX, YMIN), (XMAX, YMAX), (XMIN, YMAX)]

    def side(P, p1, p2):
        return (p2[0] - p1[0]) * (P[1] - p1[1]) - (p2[1] - p1[1]) * (P[0] - p1[0])

    def clip_poly(poly, p1, p2, keep_sign):
        """半平面 side*keep_sign>0 でポリゴンをクリップ(Sutherland–Hodgman)。"""
        out = []
        n = len(poly)
        for i in range(n):
            cur = poly[i]; nxt = poly[(i + 1) % n]
            sc = side(cur, p1, p2) * keep_sign
            sn = side(nxt, p1, p2) * keep_sign
            if sc >= 0:
                out.append(cur)
            if (sc > 0) != (sn > 0):
                # 交点
                s1 = side(cur, p1, p2); s2 = side(nxt, p1, p2)
                t = s1 / (s1 - s2) if (s1 - s2) != 0 else 0
                out.append((cur[0] + (nxt[0] - cur[0]) * t,
                            cur[1] + (nxt[1] - cur[1]) * t))
        return out

    def poly_path(poly):
        if not poly:
            return ""
        return "M" + " L".join(f"{sx(x):.1f} {sy(y):.1f}" for x, y in poly) + " Z"

    sC_ab = side(C, A, B)   # C の AB に対する符号
    sC_bc = side(C, B, C)   # (=0) 使わない
    # 各図の塗りポリゴン群を返すクロージャ
    def region(idx):
        box = clipbox()
        if idx == 0:   # 三角形内部
            return [[A, B, C]]
        if idx == 1:   # ∠C の内角領域: BCの上側(Aと同側) ∩ CAのB側
            sA_bc = side(A, B, C)          # A の BC 側
            sB_ca = side(B, C, A)          # B の CA 側
            poly = box
            poly = clip_poly(poly, B, C, 1 if sA_bc > 0 else -1)
            poly = clip_poly(poly, C, A, 1 if sB_ca > 0 else -1)
            return [poly]
        if idx == 2:   # 三角形内部 ∪ C対頂角(BC下側∩CA反B側)
            sA_bc = side(A, B, C); sB_ca = side(B, C, A)
            tri = [A, B, C]
            opp = box
            opp = clip_poly(opp, B, C, -1 if sA_bc > 0 else 1)   # BC 下側
            opp = clip_poly(opp, C, A, -1 if sB_ca > 0 else 1)   # CA 反B側
            return [tri, opp]
        if idx == 3:   # AB の C反対側 半平面
            poly = clip_poly(box, A, B, -1 if sC_ab > 0 else 1)
            return [poly]
        if idx == 4:   # AB のC反対側 ∩ BC上側
            sA_bc = side(A, B, C)
            poly = clip_poly(box, A, B, -1 if sC_ab > 0 else 1)
            poly = clip_poly(poly, B, C, 1 if sA_bc > 0 else -1)
            return [poly]
        if idx == 5:   # AB の C同側 半平面
            poly = clip_poly(box, A, B, 1 if sC_ab > 0 else -1)
            return [poly]

    figs = []
    for idx in range(6):
        body = []
        for poly in region(idx):
            d = poly_path(poly)
            if d:
                body.append(f"<path d='{d}' fill='#8f8f8f' fill-opacity='0.42' stroke='none'/>")
        # 3直線 AB,AC,BC
        for p1, p2 in [(A, B), (A, C), (B, C)]:
            (q1, q2) = line_pts(p1, p2)
            body.append(f"<line x1='{sx(q1[0]):.1f}' y1='{sy(q1[1]):.1f}' "
                        f"x2='{sx(q2[0]):.1f}' y2='{sy(q2[1]):.1f}' stroke='#333' stroke-width='1.0'/>")
        # 頂点ラベル
        for name, p, dx, dy in [("A", A, -3, -5), ("B", B, -12, 4), ("C", C, 6, 4)]:
            body.append(f"<circle cx='{sx(p[0]):.1f}' cy='{sy(p[1]):.1f}' r='2.0' fill='#333'/>")
            body.append(f"<text x='{sx(p[0])+dx:.1f}' y='{sy(p[1])+dy:.1f}' font-size='11'>{name}</text>")
        figs.append(_svg(W, H, "".join(body), 132))
    return figs


# ============================================================
# 第7問 図6択(コ): x-y 軸 + 線分/山型
#   ⓪実軸[-1,1]①実軸[-2,2]②虚軸[-1,1]③虚軸[-2,2]④山型 高さ1⑤山型 高さ2
# ============================================================
def figs_sec7_ko():
    W, H = 118, 104
    cx, cy = W / 2, H / 2
    K = 20.0   # 1単位=20px

    def sx(x): return cx + x * K
    def sy(y): return cy - y * K

    def axes():
        return [
            f"<line x1='6' y1='{cy}' x2='{W-6}' y2='{cy}' stroke='#333' stroke-width='0.9'/>",
            f"<line x1='{cx}' y1='{H-6}' x2='{cx}' y2='6' stroke='#333' stroke-width='0.9'/>",
            f"<text x='{cx-9}' y='{cy+12}' font-style='italic' font-size='10'>O</text>",
            f"<text x='{W-6}' y='{cy-4}' font-style='italic' font-size='10'>x</text>",
            f"<text x='{cx+5}' y='12' font-style='italic' font-size='10'>y</text>",
        ]

    def seg_real(a):
        b = [f"<line x1='{sx(-a):.1f}' y1='{cy}' x2='{sx(a):.1f}' y2='{cy}' stroke='#333' stroke-width='2.6'/>"]
        b.append(f"<text x='{sx(a)-2:.1f}' y='{cy+13}' font-size='9'>{a}</text>")
        b.append(f"<text x='{sx(-a)-6:.1f}' y='{cy+13}' font-size='9'>-{a}</text>")
        return b

    def seg_imag(a):
        b = [f"<line x1='{cx}' y1='{sy(-a):.1f}' x2='{cx}' y2='{sy(a):.1f}' stroke='#333' stroke-width='2.6'/>"]
        b.append(f"<text x='{cx+4}' y='{sy(a)+3:.1f}' font-size='9'>{a}</text>")
        b.append(f"<text x='{cx+4}' y='{sy(-a)+3:.1f}' font-size='9'>-{a}</text>")
        return b

    def hump(hgt):
        # 山型: y = hgt*cos, 両裾 y=-hgt。ここでは概形 (パラメトリックな山型)
        pts = []
        n = 60
        for i in range(n + 1):
            t = -1 + 2 * i / n            # -1..1
            x = 2 * t                     # x∈[-2,2]
            y = hgt * (1 - 2 * t * t) if abs(t) <= 1 else -hgt  # 単純な山
            # より "山型 (上に凸→両裾下がる)" に: y = hgt*cos(pi*t) 風
            y = hgt * _m.cos(_m.pi * t / 1.0) if False else hgt - 2 * hgt * (t * t)
            pts.append((x, y))
        d = "M" + " L".join(f"{sx(x):.1f} {sy(y):.1f}" for x, y in pts)
        b = [f"<line x1='6' y1='{sy(-hgt):.1f}' x2='{W-6}' y2='{sy(-hgt):.1f}' stroke='#666' stroke-width='0.8' stroke-dasharray='3 2'/>",
             f"<path d='{d}' fill='none' stroke='#333' stroke-width='1.8'/>",
             f"<text x='{sx(0)+5:.1f}' y='{sy(hgt)+3:.1f}' font-size='9'>{hgt}</text>",
             f"<text x='{W-14}' y='{sy(-hgt)-3:.1f}' font-size='9'>-{hgt}</text>"]
        return b

    specs = [("real", 1), ("real", 2), ("imag", 1), ("imag", 2), ("hump", 1), ("hump", 2)]
    figs = []
    for kind, a in specs:
        body = axes()
        if kind == "real":
            body += seg_real(a)
        elif kind == "imag":
            body += seg_imag(a)
        else:
            body += hump(a)
        figs.append(_svg(W, H, "".join(body), 122))
    return figs


# ============================================================
# 第7問 図8択(セ): 楕円 (中心±2/O × 縦長/横長 × 大/小)
#   ⓪縦長中心(-2,0)①縦長中心(2,0)②横長中心(-2,0)③横長中心(2,0)
#   ④小横長(-2,0)⑤小横長(2,0)⑥縦長中心O⑦横長中心O(x±2,y±1目盛)
# ============================================================
def figs_sec7_se():
    W, H = 132, 108
    cx, cy = W / 2, H / 2 + 2
    K = 8.5    # 1単位=8.5px。中心±2 の楕円が枠内に収まるスケール

    def sx(x): return cx + x * K
    def sy(y): return cy - y * K

    def axes():
        return [
            f"<line x1='5' y1='{cy}' x2='{W-5}' y2='{cy}' stroke='#333' stroke-width='0.9'/>",
            f"<line x1='{cx}' y1='{H-5}' x2='{cx}' y2='5' stroke='#333' stroke-width='0.9'/>",
            f"<text x='{cx-9}' y='{cy+11}' font-style='italic' font-size='9'>O</text>",
            f"<text x='{W-5}' y='{cy-4}' font-style='italic' font-size='9'>x</text>",
            f"<text x='{cx+4}' y='11' font-style='italic' font-size='9'>y</text>",
        ]

    def ellipse(cxw, rx, ry, ticks=None):
        b = [f"<ellipse cx='{sx(cxw):.1f}' cy='{cy:.1f}' rx='{rx*K:.1f}' ry='{ry*K:.1f}' "
             f"fill='none' stroke='#333' stroke-width='1.4'/>"]
        if abs(cxw) > 1e-6:
            b.append(f"<line x1='{sx(cxw):.1f}' y1='{sy(ry)-3:.1f}' x2='{sx(cxw):.1f}' y2='{sy(-ry)+3:.1f}' "
                     f"stroke='#777' stroke-width='0.7' stroke-dasharray='2 2'/>")
            b.append(f"<circle cx='{sx(cxw):.1f}' cy='{cy:.1f}' r='1.5' fill='#333'/>")
            b.append(f"<text x='{sx(cxw)-2:.1f}' y='{cy+11}' font-size='8'>{cxw:g}</text>")
        if ticks:
            for (tx, ty, lab, anc) in ticks:
                b.append(f"<text x='{sx(tx)+anc[0]:.1f}' y='{sy(ty)+anc[1]:.1f}' font-size='8'>{lab}</text>")
        return b

    # 大横長=(4.25,3.75), 大縦長=(3.75,4.25), 小横長=(2.4,1.6) を 8.5px で描く
    LH = (4.25, 3.75); LV = (3.75, 4.25); SH = (2.4, 1.6)
    figs = []
    specs = [
        (-2, LV, None),   # ⓪縦長・中心(-2,0)
        (2, LV, None),    # ①縦長・中心(2,0)
        (-2, LH, None),   # ②横長・中心(-2,0)
        (2, LH, None),    # ③横長・中心(2,0)  ← 正解
        (-2, SH, None),   # ④小・横長・中心(-2,0)
        (2, SH, None),    # ⑤小・横長・中心(2,0)
        (0, (1.0, 2.0), [(1, 0, "1", (2, 10)), (-1, 0, "-1", (-8, 10)),
                         (0, 2, "2", (3, -1)), (0, -2, "-2", (3, 10))]),   # ⑥縦長・中心O
        (0, (2.0, 1.0), [(2, 0, "2", (1, 10)), (-2, 0, "-2", (-9, 10)),
                         (0, 1, "1", (3, -1)), (0, -1, "-1", (3, 10))]),   # ⑦横長・中心O
    ]
    for cxw, (rx, ry), ticks in specs:
        body = axes()
        body += ellipse(cxw, rx, ry, ticks=ticks)
        figs.append(_svg(W, H, "".join(body), 130))
    return figs


if __name__ == "__main__":
    # 単体プレビュー用 HTML を吐く
    import os
    HERE = os.path.dirname(os.path.abspath(__file__))
    parts = []
    parts.append("<h3>正規分布小図</h3>" + normal_curve_fig())
    parts.append("<h3>六角形図1</h3>" + hexagon_fig())
    parts.append("<h3>参考図</h3>" + triangle_midpoints_fig())
    parts.append("<h3>領域6択</h3>" + "".join(
        f"<div style='display:inline-block;margin:4px;text-align:center'>{i}<br>{s}</div>"
        for i, s in enumerate(region_figs_sec6())))
    parts.append("<h3>第7問コ 図6択</h3>" + "".join(
        f"<div style='display:inline-block;margin:4px;text-align:center'>{i}<br>{s}</div>"
        for i, s in enumerate(figs_sec7_ko())))
    parts.append("<h3>第7問セ 図8択</h3>" + "".join(
        f"<div style='display:inline-block;margin:4px;text-align:center'>{i}<br>{s}</div>"
        for i, s in enumerate(figs_sec7_se())))
    out = os.path.join(os.path.dirname(HERE), "build", "_svgprev_c.html")
    with open(out, "w") as f:
        f.write("<!doctype html><meta charset=utf-8><body style='font-family:sans-serif'>"
                + "".join(parts) + "</body>")
    print("wrote", out)
