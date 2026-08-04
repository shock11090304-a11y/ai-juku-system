# -*- coding: utf-8 -*-
"""数学の図(SVG)を「数学座標」から正しく生成するヘルパ。
SVG は y 下向きなので、数学 y 正 = 上 になるよう変換する(生成AIが上下逆に描く事故を防ぐ)。
色: 主図形=NAVY, 強調/求める要素=RED。"""
import math

NAVY = "#1f3a5f"
RED = "#c8492e"
FILL = "#eef2f7"
GRAY = "#8a8a8a"

class Canvas:
    def __init__(self, xr, yr, size=(180, 150), pad=16):
        (xmin, xmax), (ymin, ymax) = xr, yr
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        W, H = size
        self.W, self.H = W, H
        sx = (W - 2 * pad) / (xmax - xmin)
        sy = (H - 2 * pad) / (ymax - ymin)
        self.s = min(sx, sy)
        # 中央寄せ
        self.ox = (W - self.s * (xmax + xmin)) / 2
        self.oy = (H + self.s * (ymax + ymin)) / 2
        self.parts = []

    def X(self, x): return round(self.ox + self.s * x, 1)
    def Y(self, y): return round(self.oy - self.s * y, 1)

    def axes(self, arrows=True, olabel=True):
        x0, x1 = self.X(self.xmin), self.X(self.xmax)
        y0 = self.Y(0)
        self.parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{NAVY}" stroke-width="1.1"/>')
        yt, yb = self.Y(self.ymax), self.Y(self.ymin)
        xv = self.X(0)
        self.parts.append(f'<line x1="{xv}" y1="{yb}" x2="{xv}" y2="{yt}" stroke="{NAVY}" stroke-width="1.1"/>')
        if arrows:
            self.parts.append(f'<polygon points="{x1},{y0} {x1-8},{y0-3.5} {x1-8},{y0+3.5}" fill="{NAVY}"/>')
            self.parts.append(f'<polygon points="{xv},{yt} {xv-3.5},{yt+8} {xv+3.5},{yt+8}" fill="{NAVY}"/>')
            self.parts.append(f'<text x="{x1-2}" y="{y0-5}" font-size="10">x</text>')
            self.parts.append(f'<text x="{xv+4}" y="{yt+9}" font-size="10">y</text>')
        if olabel:
            self.parts.append(f'<text x="{xv-11}" y="{y0+12}" font-size="10">O</text>')

    def poly(self, pts, fill=FILL, stroke=NAVY, w=1.6):
        p = " ".join(f"{self.X(x)},{self.Y(y)}" for x, y in pts)
        self.parts.append(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')

    def circle(self, cx, cy, r, fill="none", stroke=NAVY, w=1.6, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<circle cx="{self.X(cx)}" cy="{self.Y(cy)}" r="{round(self.s*r,1)}" '
                          f'fill="{fill}" stroke="{stroke}" stroke-width="{w}"{d}/>')

    def seg(self, x1, y1, x2, y2, stroke=NAVY, w=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{self.X(x1)}" y1="{self.Y(y1)}" x2="{self.X(x2)}" y2="{self.Y(y2)}" '
                          f'stroke="{stroke}" stroke-width="{w}"{d}/>')

    def line_abc(self, a, b, c, stroke=NAVY, w=1.4, dash=None):
        """ax+by+c=0 を描画枠でクリップして描く。"""
        pts = []
        for x in (self.xmin, self.xmax):
            if b != 0:
                y = -(a * x + c) / b
                if self.ymin - 1e-9 <= y <= self.ymax + 1e-9: pts.append((x, y))
        for y in (self.ymin, self.ymax):
            if a != 0:
                x = -(b * y + c) / a
                if self.xmin - 1e-9 <= x <= self.xmax + 1e-9: pts.append((x, y))
        # 重複除去
        uniq = []
        for p in pts:
            if not any(abs(p[0]-q[0]) < 1e-6 and abs(p[1]-q[1]) < 1e-6 for q in uniq): uniq.append(p)
        if len(uniq) >= 2:
            (x1, y1), (x2, y2) = uniq[0], uniq[1]
            self.seg(x1, y1, x2, y2, stroke, w, dash)

    def vec(self, x1, y1, x2, y2, stroke=RED, w=1.8):
        sx1, sy1, sx2, sy2 = self.X(x1), self.Y(y1), self.X(x2), self.Y(y2)
        self.parts.append(f'<line x1="{sx1}" y1="{sy1}" x2="{sx2}" y2="{sy2}" stroke="{stroke}" stroke-width="{w}"/>')
        ang = math.atan2(sy2 - sy1, sx2 - sx1)
        L, spread = 9, 0.42
        for da in (spread, -spread):
            bx = sx2 - L * math.cos(ang - da); by = sy2 - L * math.sin(ang - da)
            self.parts.append(f'<line x1="{sx2}" y1="{sy2}" x2="{round(bx,1)}" y2="{round(by,1)}" stroke="{stroke}" stroke-width="{w}"/>')

    def dot(self, x, y, color=NAVY, r=2.5):
        self.parts.append(f'<circle cx="{self.X(x)}" cy="{self.Y(y)}" r="{r}" fill="{color}"/>')

    def label(self, x, y, s, dx=0, dy=0, size=12, color="#1a1a1a"):
        self.parts.append(f'<text x="{round(self.X(x)+dx,1)}" y="{round(self.Y(y)+dy,1)}" '
                          f'font-size="{size}" fill="{color}">{s}</text>')

    def right_angle(self, vx, vy, ux, uy, wx, wy, size=0.5):
        """頂点(vx,vy)、そこから(ux,uy)方向と(wx,wy)方向への直角マーク。"""
        def norm(ax, ay):
            L = math.hypot(ax, ay); return (ax / L, ay / L)
        u = norm(ux - vx, uy - vy); w = norm(wx - vx, wy - vy)
        p1 = (vx + u[0] * size, vy + u[1] * size)
        p3 = (vx + w[0] * size, vy + w[1] * size)
        p2 = (vx + (u[0] + w[0]) * size, vy + (u[1] + w[1]) * size)
        pts = " ".join(f"{self.X(px)},{self.Y(py)}" for px, py in [p1, p2, p3])
        self.parts.append(f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="1.1"/>')

    def svg(self):
        body = "".join(self.parts)
        return (f'<svg viewBox="0 0 {self.W} {self.H}" xmlns="http://www.w3.org/2000/svg">'
                f'{body}</svg>')
