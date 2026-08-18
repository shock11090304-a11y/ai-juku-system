#!/usr/bin/env python3
"""
手本グリフの墨の上だけを通る経路 (中心線寄り) を引き直して制御点を作る。

  python3 tools/trace_all.py /tmp/masks [--apply] [id ...]

各画について、現行の制御点を「経由点」として使い、墨の中だけを通る最短経路を
順に繋ぐ。コストは距離変換 (墨の中心ほど小さい) で重み付けするので、線の縁では
なく中心を通る。経路は必ず墨の中なので、忠実度は構造的に高くなる。

--apply で JSON を書き換える。指定が無ければ測定のみ。
"""
import json
import math
import os
import sys
import heapq
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '../src/data/characters')
FILES = ['hiragana.json', 'katakana.json', 'numbers.json']


def load_mask(path):
    d = json.load(open(path))
    S = d['size']
    ink = bytearray(S * S)
    for y, x0, x1 in d['runs']:
        for x in range(x0, x1 + 1):
            ink[y * S + x] = 1
    return S, ink


def distance_transform(S, ink):
    """墨の内側ほど大きい距離場 (2パス chamfer)"""
    INF = 10 ** 6
    dt = [0.0] * (S * S)
    for i in range(S * S):
        dt[i] = INF if ink[i] else 0.0
    for y in range(S):
        base = y * S
        for x in range(S):
            i = base + x
            if not ink[i]:
                continue
            v = dt[i]
            if y:
                v = min(v, dt[i - S] + 1)
                if x:
                    v = min(v, dt[i - S - 1] + 1.414)
                if x < S - 1:
                    v = min(v, dt[i - S + 1] + 1.414)
            if x:
                v = min(v, dt[i - 1] + 1)
            dt[i] = v
    for y in range(S - 1, -1, -1):
        base = y * S
        for x in range(S - 1, -1, -1):
            i = base + x
            if not ink[i]:
                continue
            v = dt[i]
            if y < S - 1:
                v = min(v, dt[i + S] + 1)
                if x < S - 1:
                    v = min(v, dt[i + S + 1] + 1.414)
                if x:
                    v = min(v, dt[i + S - 1] + 1.414)
            if x < S - 1:
                v = min(v, dt[i + 1] + 1)
            dt[i] = v
    return dt


def nearest_ink(S, ink, x, y):
    if 0 <= x < S and 0 <= y < S and ink[y * S + x]:
        return x, y
    seen = {(x, y)}
    q = deque([(x, y)])
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < S and 0 <= ny < S) or (nx, ny) in seen:
                continue
            if ink[ny * S + nx]:
                return nx, ny
            seen.add((nx, ny))
            q.append((nx, ny))
    raise RuntimeError('墨が無い')


DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]


def shortest(S, ink, dt, maxdt, a, b):
    """墨の中だけを通り、中心を優先する経路"""
    src = a[1] * S + a[0]
    dst = b[1] * S + b[0]
    if src == dst:
        return [a]
    dist = {src: 0.0}
    prev = {}
    pq = [(0.0, src)]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist.get(i, 1e18):
            continue
        if i == dst:
            break
        x = i % S
        y = i // S
        for dx, dy, w in DIRS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < S and 0 <= ny < S):
                continue
            j = ny * S + nx
            if not ink[j]:
                continue
            pen = 1.0 + 8.0 * ((maxdt - dt[j]) / maxdt) ** 2
            nd = d + w * pen
            if nd < dist.get(j, 1e18):
                dist[j] = nd
                prev[j] = i
                heapq.heappush(pq, (nd, j))
    if dst not in dist:
        return None
    path = []
    i = dst
    while i != src:
        path.append((i % S, i // S))
        i = prev[i]
    path.append((src % S, src // S))
    path.reverse()
    return path


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    best, idx = -1.0, 0
    for k in range(1, len(pts) - 1):
        d = abs((pts[k][0] - a[0]) * dy - (pts[k][1] - a[1]) * dx) / L
        if d > best:
            best, idx = d, k
    if best <= eps:
        return [a, b]
    return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)


def catmull(pts, per=24):
    """engine/geometry と同じ Catmull-Rom で密にサンプルする"""
    if len(pts) < 2:
        return pts
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def fidelity(pts, S, ink):
    dense = catmull(pts)
    hit = 0
    for x, y in dense:
        xi, yi = int(round(x * S)), int(round(y * S))
        if 0 <= xi < S and 0 <= yi < S and ink[yi * S + xi]:
            hit += 1
    return hit / len(dense)


def main():
    args = [a for a in sys.argv[1:]]
    mask_dir = args[0]
    apply_ = '--apply' in args
    only = [a for a in args[1:] if not a.startswith('--')]

    bundles = [(f, json.load(open(os.path.join(DATA, f)))) for f in FILES]
    report = []
    for fname, lst in bundles:
        for c in lst:
            if c.get('composedFrom') or c.get('group') == 'youon':
                continue
            if only and c['id'] not in only:
                continue
            mp = os.path.join(mask_dir, c['id'] + '.json')
            if not os.path.exists(mp):
                continue
            S, ink = load_mask(mp)
            dt = distance_transform(S, ink)
            maxdt = max(dt) or 1.0
            before_all, after_all = [], []
            for st in c['strokes']:
                pts = [(p[0], p[1]) for p in st['points']]
                before = fidelity(pts, S, ink)
                wps = [nearest_ink(S, ink, int(round(x * S)), int(round(y * S))) for x, y in pts]
                full = []
                ok = True
                for k in range(len(wps) - 1):
                    seg = shortest(S, ink, dt, maxdt, wps[k], wps[k + 1])
                    if seg is None:
                        ok = False
                        break
                    full = seg if not full else full + seg[1:]
                if not ok or len(full) < 2:
                    before_all.append(before)
                    after_all.append(before)
                    continue
                simp = rdp(full, 4.0)
                # 制御点が増えすぎないよう上限を設ける
                if len(simp) > 18:
                    simp = [simp[round(i * (len(simp) - 1) / 17)] for i in range(18)]
                new = [(round(x / S, 3), round(y / S, 3)) for x, y in simp]
                after = fidelity(new, S, ink)
                before_all.append(before)
                if after > before:
                    after_all.append(after)
                    if apply_:
                        st['points'] = [[x, y] for x, y in new]
                else:
                    after_all.append(before)
            report.append((c['id'], c['char'],
                           sum(before_all) / len(before_all),
                           sum(after_all) / len(after_all)))
    report.sort(key=lambda r: r[3])
    for cid, ch, b, a in report:
        print(f'  {ch} {cid:16s} {b*100:3.0f}% → {a*100:3.0f}%')
    print(f'平均: {sum(r[2] for r in report)/len(report)*100:.1f}% → '
          f'{sum(r[3] for r in report)/len(report)*100:.1f}%  ({len(report)}字)')
    if apply_:
        for fname, lst in bundles:
            with open(os.path.join(DATA, fname), 'w') as f:
                json.dump(lst, f, ensure_ascii=False, indent=2)
                f.write('\n')
        print('JSON を更新した')


if __name__ == '__main__':
    main()
