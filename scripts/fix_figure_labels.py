#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed-data の figure_svg のラベル重なり・はみ出しを実測して直す。

2026-08-03: Web 受験で図が出るようになって初めて見えた不具合。
グラフの横軸ラベルが隣とぶつかって「ownSpavimg travel time」のように重なっていた。
図が描画されていなかった間は誰も気づけなかった。

【方針: 目測しない】
文字幅はフォント・字種で変わるので係数で見積もると外す。実ブラウザで
getBBox() を取って**実測**し、重なりとviewBoxはみ出しを検出してから直す。

直し方は 2 通り。どちらも情報は落とさない:
  1. 横軸の項目ラベル … 語の切れ目で 2 行に折る (<tspan> で dy を付ける)
  2. タイトル         … viewBox に収まるまで font-size を下げる

実行: python3 scripts/fix_figure_labels.py            # 実測して報告のみ
      python3 scripts/fix_figure_labels.py --apply    # 直して書き戻す
"""
import argparse
import asyncio
import glob
import itertools
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(ROOT, 'seed-data')
PAD = 2.0          # この隙間より近ければ「重なり」とみなす
MIN_TITLE_SIZE = 8.5


def chromium_path():
    for pat in ('/opt/pw-browsers/chromium-*/chrome-linux/chrome',
                '/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell'):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


def detect_format(raw, data):
    for ind, sep, tail in itertools.product([0, 1, 2, 3, 4, None],
                                            [None, (',', ': ')], ['', '\n']):
        try:
            if json.dumps(data, ensure_ascii=False, indent=ind, separators=sep) + tail == raw:
                return ind, sep, tail
        except TypeError:
            continue
    return None


def collect(only=None):
    """(file, gi, label, svg) を集める。"""
    out = []
    for path in sorted(glob.glob(os.path.join(SEED_DIR, '*.json'))):
        name = os.path.basename(path)
        if only and name not in only:
            continue
        try:
            data = json.loads(open(path, encoding='utf-8').read())
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for gi, row in enumerate(data.get('questions') or []):
            if not isinstance(row, dict):
                continue
            qd = row.get('question_data') or {}
            svg = qd.get('figure_svg')
            if svg:
                out.append((name, gi, qd.get('format_type') or qd.get('group') or f'大問{gi + 1}', svg))
    return out


MEASURE_JS = r'''(svgs) => {
  const host = document.createElement('div');
  host.style.cssText = 'position:absolute;left:-9999px;top:0;font-family:Helvetica,Arial,sans-serif';
  document.body.appendChild(host);
  const out = [];
  for (const svg of svgs) {
    host.innerHTML = svg;
    const el = host.querySelector('svg');
    const vb = (el.getAttribute('viewBox') || '0 0 0 0').split(/\s+/).map(Number);
    const texts = [];
    el.querySelectorAll('text').forEach((t, i) => {
      const b = t.getBBox();
      texts.push({ i, x: b.x, y: b.y, w: b.width, h: b.height,
                   s: (t.textContent || '').trim(),
                   size: parseFloat(t.getAttribute('font-size') || '0') });
    });
    out.push({ vbW: vb[2], vbH: vb[3], texts });
  }
  host.remove();
  return out;
}'''


async def measure(svgs):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=chromium_path())
        pg = await b.new_page()
        await pg.set_content('<body></body>')
        res = await pg.evaluate(MEASURE_JS, svgs)
        await b.close()
    return res


def problems(m):
    """重なり (同じ y 帯で x 範囲が交わる) と、viewBox からのはみ出しを拾う。"""
    issues = []
    ts = m['texts']
    for a, b in itertools.combinations(ts, 2):
        if abs(a['y'] - b['y']) > max(a['h'], b['h']) * 0.6:
            continue                      # 別の行なので比較しない
        lo, hi = (a, b) if a['x'] <= b['x'] else (b, a)
        if lo['x'] + lo['w'] + PAD > hi['x']:
            issues.append(('overlap', lo['s'], hi['s'],
                           round(lo['x'] + lo['w'] - hi['x'], 1)))
    for t in ts:
        if t['x'] < -PAD or t['x'] + t['w'] > m['vbW'] + PAD:
            issues.append(('overflow', t['s'], '',
                           round(max(-t['x'], t['x'] + t['w'] - m['vbW']), 1)))
    return issues


def wrap_label(svg, text, max_w, cur_w):
    """横軸ラベルを語の切れ目で 2 行に折る。1 行目を <tspan>、2 行目を dy 付き <tspan> に。"""
    words = text.split()
    if len(words) < 2:
        return None
    # 幅がだいたい半々になる切れ目を選ぶ
    best, bestdiff = None, None
    for k in range(1, len(words)):
        a, b = ' '.join(words[:k]), ' '.join(words[k:])
        diff = abs(len(a) - len(b))
        if bestdiff is None or diff < bestdiff:
            best, bestdiff = (a, b), diff
    a, b = best
    esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    old = f'>{esc(text)}</text>'
    if old not in svg:
        return None
    new = (f'><tspan x="{{X}}" dy="0">{esc(a)}</tspan>'
           f'<tspan x="{{X}}" dy="1.15em">{esc(b)}</tspan></text>')
    # その <text> の x を拾って tspan に引き継ぐ
    m = re.search(r'<text([^>]*)>' + re.escape(esc(text)) + r'</text>', svg)
    if not m:
        return None
    xm = re.search(r'\bx="([-\d.]+)"', m.group(1))
    if not xm:
        return None
    return svg.replace(old, new.replace('{X}', xm.group(1)), 1)


def shrink_title(svg, text, over, cur_size):
    """タイトルが viewBox からはみ出すぶんだけ font-size を下げる。"""
    if not cur_size:
        return None
    esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    m = re.search(r'<text([^>]*)>' + re.escape(esc(text)) + r'</text>', svg)
    if not m:
        return None
    attrs = m.group(1)
    # はみ出し量に比例して縮める (少し余裕を持たせる)
    new_size = max(MIN_TITLE_SIZE, round(cur_size * 0.94, 1))
    new_attrs = re.sub(r'font-size="[\d.]+"', f'font-size="{new_size}"', attrs)
    return svg.replace(m.group(0), f'<text{new_attrs}>{esc(text)}</text>', 1)


async def main_async(args):
    items = collect(set(args.only) if args.only else None)
    if not items:
        print('figure_svg を持つ大問が無い')
        return 0
    svgs = [s for _, _, _, s in items]
    meas = await measure(svgs)

    fixed = {}
    report = []
    for (name, gi, label, svg), m in zip(items, meas):
        issues = problems(m)
        if not issues:
            continue
        cur = svg
        # 重なり → ラベルを折る (幅の広いほうを折る)
        for kind, s1, s2, amt in issues:
            if kind != 'overlap':
                continue
            t1 = next((t for t in m['texts'] if t['s'] == s1), None)
            t2 = next((t for t in m['texts'] if t['s'] == s2), None)
            target = s1 if (t1 and t2 and t1['w'] >= t2['w']) else s2
            w = wrap_label(cur, target, 0, 0)
            if w:
                cur = w
        # はみ出し → タイトルを縮める
        for kind, s1, _s2, amt in issues:
            if kind != 'overflow':
                continue
            t = next((t for t in m['texts'] if t['s'] == s1), None)
            sh = shrink_title(cur, s1, amt, t['size'] if t else 0)
            if sh:
                cur = sh
        report.append((name, gi, label, issues, cur != svg))
        if cur != svg:
            fixed[(name, gi)] = cur

    print(f'図版 {len(items)} 枚を実測')
    if not report:
        print('✅ 重なり・はみ出しなし')
        return 0
    for name, gi, label, issues, changed in report:
        print(f'\n{name} 大問{gi + 1} ({label})  {"→ 修正" if changed else "→ 手当てできず"}')
        for kind, s1, s2, amt in issues:
            if kind == 'overlap':
                print(f'    重なり {amt}px: "{s1[:34]}" ↔ "{s2[:34]}"')
            else:
                print(f'    はみ出し {amt}px: "{s1[:50]}"')

    if args.apply and fixed:
        by_file = {}
        for (name, gi), svg in fixed.items():
            by_file.setdefault(name, {})[gi] = svg
        for name, gis in by_file.items():
            path = os.path.join(SEED_DIR, name)
            raw = open(path, encoding='utf-8').read()
            data = json.loads(raw)
            fmt = detect_format(raw, data)
            if fmt is None:
                print(f'  ⚠ {name}: 整形を再現できないので触らない')
                continue
            for gi, svg in gis.items():
                data['questions'][gi]['question_data']['figure_svg'] = svg
            ind, sep, tail = fmt
            open(path, 'w', encoding='utf-8').write(
                json.dumps(data, ensure_ascii=False, indent=ind, separators=sep) + tail)
            print(f'  書き込み: {name} ({len(gis)} 枚)')
    elif not args.apply:
        print('\n(--apply で書き込み)')
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args()
    return asyncio.run(main_async(args))


if __name__ == '__main__':
    sys.exit(main())
