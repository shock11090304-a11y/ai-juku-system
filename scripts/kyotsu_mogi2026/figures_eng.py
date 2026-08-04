#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト模試 2026 英語リーディング — 大問ごとの図版 (figure_svg)。

本番の共通テスト リーディングは大問のほぼ全てに視覚資料が付く
(カレンダー / ポスター / 比較表 / 円・棒グラフ / イラスト / 時系列 / 図解)。
本文だけ載せると「読解問題」にはなっても「共通テスト形式」にはならない。

【この図版群の絶対条件】
1. **図に載せる情報は必ず passage に書かれている事実だけ**。
   図にしか無い数値を作らない (作ると設問の根拠が本文外に出て audit が破綻する)。
   図は「本文の情報を本番と同じ見せ方で提示し直したもの」に徹する。
2. **明背景 (PDF の白紙) と暗背景 (Web アプリ) の両方で読めること**。
   線と文字は `currentColor` を使って地の文の色を継承する。塗りは中間色
   (#3b82f6 / #ef4444 / #22c55e / #f59e0b) のみ — 白でも黒でも沈まない。
3. `<script>` と `on*` 属性は禁止 (server 側 sanitizer / XSS 対策)。
4. チェック・バツ等の記号は **フォント依存の文字を使わず線で描く**。
   ✓/✗ を文字で置くと PDF の日本語フォントで豆腐になる。

出力は build_eng.py が question_data.figure_svg に載せる。
"""

# 明暗どちらの地色でも沈まないアクセント色
BLUE, RED, GREEN, AMBER = '#3b82f6', '#ef4444', '#22c55e', '#f59e0b'
FG = 'currentColor'


def _esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _t(x, y, s, size=11, anchor='start', weight='normal', fill=FG, opacity=1):
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" fill="{fill}" fill-opacity="{opacity}">{_esc(s)}</text>')


def _rect(x, y, w, h, fill='none', stroke=FG, sw=1, rx=0, op=1, sop=1):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'fill-opacity="{op}" stroke="{stroke}" stroke-opacity="{sop}" stroke-width="{sw}"/>')


def _line(x1, y1, x2, y2, stroke=FG, sw=1, op=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-opacity="{op}" stroke-width="{sw}"{d}/>')


def _path(d, stroke=FG, sw=1.4, fill='none', op=1):
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-opacity="{op}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')


def _check(cx, cy, c=GREEN, s=5):
    """チェック印を線で描く (フォント非依存)。"""
    return _path(f'M{cx - s},{cy} L{cx - s / 3},{cy + s * 0.8} L{cx + s},{cy - s * 0.9}',
                 stroke=c, sw=2)


def _cross(cx, cy, c=RED, s=4.5):
    """バツ印を線で描く (フォント非依存)。"""
    return (_path(f'M{cx - s},{cy - s} L{cx + s},{cy + s}', stroke=c, sw=2)
            + _path(f'M{cx + s},{cy - s} L{cx - s},{cy + s}', stroke=c, sw=2))


def _wrap(text, width):
    """図中のラベルを width 文字で折り返す (はみ出し・重なりの防止)。"""
    lines, line = [], ''
    for w in text.split():
        if line and len(line) + 1 + len(w) > width:
            lines.append(line)
            line = w
        else:
            line = (line + ' ' + w).strip()
    if line:
        lines.append(line)
    return lines


def _svg(w, h, body, title):
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Helvetica, Arial, sans-serif" role="img" '
            f'aria-label="{_esc(title)}">{body}</svg>')


# =====================================================================
# 第1問A — 9月のカレンダー
#   本文の事実: 5 September 到着 / Monday the 8th に学校 / 書道部は水 or 木 (未確定)
#   → 8 が月曜なので 1 も月曜。5 は金曜。カレンダーはこの整合で組む。
# =====================================================================
def fig_1a():
    b = [_rect(6, 6, 448, 258, rx=8, sop=.35)]
    b.append(_t(230, 28, 'SEPTEMBER', 15, 'middle', 'bold'))
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    x0, y0, cw, ch = 24, 40, 59, 32
    # 水・木の列は「書道部が水曜か木曜か分からない」という論点なので薄く敷く
    for ci in (2, 3):
        b.append(_rect(x0 + ci * cw, y0, cw, ch * 5 + 20, fill=AMBER, op=.13, stroke='none'))
    for ci, d in enumerate(days):
        b.append(_t(x0 + ci * cw + cw / 2, y0 + 14, d, 10, 'middle', 'bold', opacity=.75))
    b.append(_line(x0, y0 + 20, x0 + 7 * cw, y0 + 20, op=.4))
    for n in range(1, 31):
        ci, ri = (n - 1) % 7, (n - 1) // 7
        cx, cy = x0 + ci * cw, y0 + 20 + ri * ch
        if n == 5:
            b.append(f'<circle cx="{cx + cw / 2}" cy="{cy + 15}" r="13" fill="{BLUE}" fill-opacity=".9"/>')
            b.append(_t(cx + cw / 2, cy + 19, n, 12, 'middle', 'bold', fill='#ffffff'))
        elif n == 8:
            b.append(f'<circle cx="{cx + cw / 2}" cy="{cy + 15}" r="13" fill="{GREEN}" fill-opacity=".9"/>')
            b.append(_t(cx + cw / 2, cy + 19, n, 12, 'middle', 'bold', fill='#ffffff'))
        else:
            b.append(_t(cx + cw / 2, cy + 19, n, 11, 'middle', opacity=.85))
    ly = y0 + 20 + 5 * ch + 12
    b.append(f'<circle cx="34" cy="{ly - 4}" r="6" fill="{BLUE}" fill-opacity=".9"/>')
    b.append(_t(46, ly, 'Emma arrives in Osaka', 10.5))
    b.append(f'<circle cx="212" cy="{ly - 4}" r="6" fill="{GREEN}" fill-opacity=".9"/>')
    b.append(_t(224, ly, 'meets you at school', 10.5))
    b.append(_rect(340, ly - 11, 12, 12, fill=AMBER, op=.3, sop=.4))
    b.append(_t(357, ly, 'calligraphy club: ?', 10.5))
    return _svg(460, 270, ''.join(b), 'September calendar')


# =====================================================================
# 第1問B — 図書館のポスター (レベル別バッジ + 期間バー)
# =====================================================================
def fig_1b():
    b = [_rect(6, 6, 448, 302, rx=8, sop=.35)]
    b.append(_rect(6, 6, 448, 44, fill=BLUE, op=.16, stroke='none', rx=8))
    b.append(_t(230, 26, 'SUMMER READING CHALLENGE 2026', 14, 'middle', 'bold'))
    b.append(_t(230, 41, 'Minami High School Library', 10.5, 'middle', opacity=.8))

    levels = [('BRONZE', '3', AMBER, ['bookmark']),
              ('SILVER', '6', BLUE, ['bookmark', '+ drink ticket']),
              ('GOLD', '10', GREEN, ['bookmark, drink ticket', '+ review printed'])]
    for i, (name, n, col, prizes) in enumerate(levels):
        x = 26 + i * 143
        b.append(_rect(x, 62, 128, 96, rx=6, sop=.3))
        b.append(f'<circle cx="{x + 64}" cy="88" r="18" fill="{col}" fill-opacity=".9"/>')
        b.append(_t(x + 64, 93, n, 15, 'middle', 'bold', fill='#ffffff'))
        b.append(_t(x + 64, 120, f'{name} ({n} books)', 10, 'middle', 'bold'))
        for j, p in enumerate(prizes):
            b.append(_t(x + 64, 136 + j * 12, p, 8.5, 'middle', opacity=.85))

    # 期間バー: 7/21-8/25 が挑戦期間・8/11-15 は閉館・8/28 がカード提出期限
    bx, by, bw = 30, 190, 400
    b.append(_t(30, 180, 'OPEN PERIOD', 9.5, 'start', 'bold', opacity=.75))

    def dx(day):        # day: 7/21 からの経過日数 (0=7/21, 35=8/25, 38=8/28)
        return bx + bw * day / 38.0
    b.append(_rect(bx, by, dx(35) - bx, 16, fill=BLUE, op=.28, stroke='none', rx=3))
    b.append(_rect(dx(21), by, dx(26) - dx(21), 16, fill=RED, op=.35, stroke='none'))
    for day in (0, 21, 26, 35):
        b.append(_line(dx(day), by, dx(day), by + 16, op=.5))
    b.append(_line(dx(38), by - 8, dx(38), by + 24, stroke=GREEN, sw=2))
    b.append(_t(bx, by + 30, '21 Jul', 9.5))
    b.append(_t(dx(23.5), by + 30, '11-15 Aug closed', 9, 'middle', fill=RED))
    b.append(_t(dx(35), by + 30, '25 Aug', 9.5, 'middle'))
    b.append(_t(436, by + 44, 'cards due 28 Aug', 9.5, 'end', 'bold', fill=GREEN))

    b.append(_line(24, 252, 436, 252, op=.25))
    facts = ['Open Mon-Fri 9:00-16:00, closed at weekends',
             'Borrow 5 books at a time (usually 2)',
             'Reading room: 2nd floor, 30 seats, silent']
    for i, f in enumerate(facts):
        b.append(f'<circle cx="32" cy="{266 + i * 14 - 3.5}" r="2.5" fill="{FG}" fill-opacity=".55"/>')
        b.append(_t(42, 266 + i * 14, f, 9.5, opacity=.9))
    return _svg(460, 316, ''.join(b), 'Summer reading challenge poster')


# =====================================================================
# 第2問A — アプリ比較表 (○×は線画)
# =====================================================================
def fig_2a():
    b = [_rect(6, 6, 448, 268, rx=8, sop=.35)]
    b.append(_t(230, 26, 'WHICH VOCABULARY APP IS RIGHT FOR YOU?', 12.5, 'middle', 'bold'))
    apps = ['WordStep', 'QuizLeaf', 'MemoRise']
    cols = [200, 288, 376]
    b.append(_line(24, 38, 436, 38, op=.4))
    for i, a in enumerate(apps):
        b.append(_rect(cols[i] - 40, 44, 80, 20, rx=4, fill=[BLUE, RED, GREEN][i], op=.18, sop=.35))
        b.append(_t(cols[i], 58, a, 10.5, 'middle', 'bold'))
    rows = [
        ('Monthly cost', ['Free', '500 yen', '300 yen']),
        ('Words in database', ['3,000', '12,000', '8,000']),
        ('Works offline', [True, False, True]),
        ('Speaking practice', [False, True, True]),
        ('Daily reminder', [True, True, False]),
        ('Progress report', ['Weekly', 'Daily', 'Monthly']),
    ]
    y = 84
    for ri, (label, vals) in enumerate(rows):
        if ri % 2 == 0:
            b.append(_rect(24, y - 14, 412, 24, fill=FG, op=.05, stroke='none'))
        b.append(_t(32, y, label, 10.5, opacity=.9))
        for i, v in enumerate(vals):
            if v is True:
                b.append(_check(cols[i], y - 4))
            elif v is False:
                b.append(_cross(cols[i], y - 4))
            else:
                b.append(_t(cols[i], y, v, 10.5, 'middle'))
        y += 24
    b.append(_line(24, y - 12, 436, y - 12, op=.4))
    b.append(_t(32, y + 4, 'Tested by three student reporters, eight weeks each.', 9.5, opacity=.75))
    b.append(_t(32, y + 18, 'The table lists only what the reporters could check themselves;', 9.5, opacity=.75))
    b.append(_t(32, y + 32, 'app-store ratings are not included.', 9.5, opacity=.75))
    return _svg(460, 280, ''.join(b), 'Vocabulary app comparison table')


# =====================================================================
# 第2問B — アンケート結果 (本文の数値のみ)
# =====================================================================
def fig_2b():
    b = [_rect(6, 6, 448, 252, rx=8, sop=.35)]
    b.append(_t(230, 26, 'STUDENT LIFE COMMITTEE SURVEY', 12.5, 'middle', 'bold'))
    b.append(_t(230, 40, '612 students asked, 478 answered', 9.5, 'middle', opacity=.75))

    b.append(_t(28, 62, 'What students said now', 10.5, 'start', 'bold', opacity=.85))
    for i, (lab, pct, col) in enumerate([('sleep under 6 hours on school nights', 61, RED),
                                         ('feel sleepy during first period', 74, RED)]):
        y = 76 + i * 26
        b.append(_rect(28, y, 300, 16, fill=FG, op=.07, stroke='none', rx=3))
        b.append(_rect(28, y, 300 * pct / 100, 16, fill=col, op=.55, stroke='none', rx=3))
        b.append(_t(336, y + 13, f'{pct}%', 11, 'start', 'bold'))
        b.append(_t(32, y + 12.5, lab, 9.5, fill=FG))

    b.append(_line(24, 134, 436, 134, op=.25))
    b.append(_t(28, 152, 'If you had 30 more minutes in the morning', 10.5, 'start', 'bold', opacity=.85))
    data = [('sleep', 58, BLUE), ('breakfast', 21, GREEN), ('study', 11, AMBER),
            ('club activities', 4, FG)]
    for i, (lab, pct, col) in enumerate(data):
        y = 166 + i * 21
        b.append(_t(112, y + 12, lab, 9.5, 'end', opacity=.9))
        b.append(_rect(120, y, 240, 14, fill=FG, op=.07, stroke='none', rx=3))
        b.append(_rect(120, y, 240 * pct / 58, 14, fill=col, op=.5 if col != FG else .3,
                       stroke='none', rx=3))
        b.append(_t(368, y + 11.5, f'{pct}%', 10, 'start', 'bold'))
    return _svg(460, 260, ''.join(b), 'School start time survey results')


# =====================================================================
# 第3問A — 田植えのイラスト
# =====================================================================
def _seedling(x, y, h=13, op=1):
    """苗 1 株。葉は「立ち上がってから外へ反る」弧を描く。
    直線を 3 本 V 字に置くと下向きの矢印にしか見えないので必ず曲線で。"""
    return _path(f'M{x},{y} C{x - 1},{y - h * .7} {x - 4},{y - h} {x - 9},{y - h * .82} '
                 f'M{x},{y} C{x + 1},{y - h * .6} {x + 2},{y - h} {x + 1},{y - h * 1.22} '
                 f'M{x},{y} C{x + 1},{y - h * .7} {x + 5},{y - h} {x + 10},{y - h * .76}',
                 stroke=GREEN, sw=1.3, op=op)


def _planter(x, y, flip=1):
    """前かがみで苗を植える人 (笠・曲げた背中・水に入った脚)。"""
    f = flip
    hx, hy = x + 20 * f, y - 34            # 頭
    return (
        # 笠
        _path(f'M{hx - 13 * f},{hy + 2} Q{hx},{hy - 15} {hx + 13 * f},{hy + 2} Z',
              fill=AMBER, sw=1.3, op=.95)
        # 頭
        + f'<circle cx="{hx}" cy="{hy + 6}" r="5" fill="none" stroke="{FG}" stroke-width="1.5"/>'
        # 曲げた背中 (腰 → 肩)
        + _path(f'M{x},{y - 10} Q{x + 9 * f},{y - 30} {hx - 5 * f},{hy + 9}', sw=2.6)
        # 腕 (肩 → 水面の手) と、手に持った苗
        + _path(f'M{hx - 6 * f},{hy + 11} Q{hx - 2 * f},{hy + 26} {x + 24 * f},{y + 1}', sw=2)
        + _seedling(x + 24 * f, y + 1, h=9)
        # 脚 (腰 → 水中)
        + _path(f'M{x},{y - 10} L{x - 5 * f},{y + 10} M{x},{y - 10} L{x + 6 * f},{y + 10}', sw=2.4)
        # 足元の波紋
        + f'<ellipse cx="{x - 5 * f}" cy="{y + 10}" rx="7" ry="2.4" fill="none" '
          f'stroke="{BLUE}" stroke-width="1" stroke-opacity=".7"/>'
        + f'<ellipse cx="{x + 6 * f}" cy="{y + 10}" rx="7" ry="2.4" fill="none" '
          f'stroke="{BLUE}" stroke-width="1" stroke-opacity=".7"/>')


def fig_3a():
    b = [_rect(6, 6, 448, 250, rx=8, sop=.35)]
    b.append(_t(230, 26, 'RICE FIELDS AND WET SOCKS', 12.5, 'middle', 'bold'))
    b.append(_t(230, 40, 'Kawakami village - about an hour north of the city', 9.5, 'middle', opacity=.7))
    # 遠景の山 (斜面をわずかに凹ませて山らしく)
    for x1, px, py, x2 in ((20, 62, 60, 106), (86, 148, 52, 210),
                           (190, 250, 66, 310), (288, 356, 54, 424), (404, 428, 74, 440)):
        # Z で閉じない (閉じると稜線の下に横棒が出て三角形の羅列に見える)
        b.append(_path(f'M{x1},98 Q{(x1 + px) / 2},{(98 + py) / 2 + 7} {px},{py} '
                       f'Q{(px + x2) / 2},{(py + 98) / 2 + 7} {x2},98', op=.33, sw=1.2))
    b.append(_line(20, 98, 440, 98, op=.5))
    # 水を張った田 (映り込みの線は控えめに・苗と人に重ねない)
    b.append(_rect(20, 98, 420, 128, fill=BLUE, op=.10, stroke='none'))
    for x1, x2, y in ((34, 150, 110), (196, 300, 106), (330, 428, 112),
                      (40, 120, 172), (300, 420, 168), (150, 250, 208)):
        b.append(_line(x1, y, x2, y, stroke=BLUE, sw=1, op=.3))
    # 目印の縄と杭 — 人の頭より上に張る (「keep to the line marked by the rope」)
    b.append(_line(32, 124, 428, 116, stroke=AMBER, sw=1.6, op=.95, dash='8 5'))
    for x, y in ((32, 124), (230, 120), (428, 116)):
        b.append(_line(x, y - 10, x, y + 12, stroke=AMBER, sw=2, op=.95))
        b.append(f'<circle cx="{x}" cy="{y - 11}" r="2" fill="{AMBER}"/>')
    # 苗の列 3 本
    for i in range(15):
        b.append(_seedling(40 + i * 27, 156 - i * 0.5))
    for i in range(14):
        b.append(_seedling(54 + i * 28, 190, op=.8))
    for i in range(13):
        b.append(_seedling(38 + i * 30, 220, h=15, op=.6))
    # 植えている 2 人 (笠・前かがみ) と、離れて見ている Mr Ito
    b.append(_planter(108, 186))
    b.append(_planter(278, 196, -1))
    b.append(_path('M366,150 Q379,135 392,150 Z', fill=AMBER, sw=1.3, op=.95))
    b.append(f'<circle cx="379" cy="155" r="5" fill="none" stroke="{FG}" stroke-width="1.5"/>')
    b.append(_path('M379,160 L379,186 M379,166 L368,176 M379,166 Q392,170 399,164 '
                   'M379,186 L372,206 M379,186 L387,206', sw=2.4))
    b.append(_t(414, 176, 'Mr Ito', 9, 'start', opacity=.85))
    b.append(_t(30, 240, 'keep to the line marked by the rope - no deeper than the roots', 9.5, opacity=.8))
    return _svg(460, 262, ''.join(b), 'Rice planting illustration')


# =====================================================================
# 第3問B — 科学キャンプの時系列
# =====================================================================
def fig_3b():
    b = [_rect(6, 6, 448, 248, rx=8, sop=.35)]
    b.append(_t(230, 26, 'MY WEEK AT THE PACIFIC SCIENCE CAMP', 12.5, 'middle', 'bold'))
    # 準備期間
    b.append(_rect(24, 42, 176, 52, rx=6, sop=.3, fill=AMBER, op=.08))
    b.append(_t(32, 58, 'BEFORE THE CAMP', 9.5, 'start', 'bold', opacity=.8))
    b.append(_t(32, 73, 'April: application form', 9.5, opacity=.9))
    b.append(_t(32, 87, 'May-June: list of 200 science words', 9.5, opacity=.9))
    b.append(_rect(216, 42, 220, 52, rx=6, sop=.3, fill=BLUE, op=.08))
    b.append(_t(224, 58, 'AT THE CAMP', 9.5, 'start', 'bold', opacity=.8))
    b.append(_t(224, 73, '40 students from 11 countries', 9.5, opacity=.9))
    b.append(_t(224, 87, 'teams of 5 - Chile, Kenya, Thailand, Australia', 9.5, opacity=.9))
    # 5 日間の矢印
    y = 128
    b.append(_line(30, y, 424, y, op=.45, sw=1.5))
    b.append(_path(f'M424,{y} L416,{y - 4} M424,{y} L416,{y + 4}', sw=1.5, op=.45))
    days = [('Day 1', 'teams formed; said almost nothing'),
            ('Day 2', 'sorted beach plastic; first idea dropped'),
            ('Day 3', 'stopped translating in my head'),
            ('Day 4', 'model failed twice; my idea to do both'),
            ('Day 5', 'presented; did not win')]
    for i, (d, txt) in enumerate(days):
        x = 46 + i * 84
        col = [BLUE, BLUE, GREEN, GREEN, AMBER][i]
        b.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{col}" fill-opacity=".85"/>')
        b.append(_t(x, y + 3.5, str(i + 1), 10, 'middle', 'bold', fill='#ffffff'))
        b.append(_t(x, y - 18, d, 9.5, 'middle', 'bold'))
        words, line, lines = txt.split(), '', []
        for w in words:
            if len(line + ' ' + w) > 16:
                lines.append(line)
                line = w
            else:
                line = (line + ' ' + w).strip()
        lines.append(line)
        for j, ln in enumerate(lines[:3]):
            b.append(_t(x, y + 26 + j * 11, ln, 8.5, 'middle', opacity=.85))
    b.append(_line(24, 200, 436, 200, op=.25))
    b.append(_t(230, 218, 'the judge: "your team changed its mind more often than any other"', 9.5,
                'middle', opacity=.85))
    b.append(_t(230, 234, 'the 200-word list came home mostly unused', 9.5, 'middle', opacity=.7))
    return _svg(460, 256, ''.join(b), 'Science camp timeline')


# =====================================================================
# 第4問 — 通学手段の調査 (人数の棒 + 評価の点)
# =====================================================================
def fig_4():
    b = [_rect(6, 6, 448, 282, rx=8, sop=.35)]
    b.append(_t(230, 24, 'REPORT A: HOW 1,200 STUDENTS TRAVEL TO SCHOOL', 12, 'middle', 'bold'))
    b.append(_t(230, 38, 'Higashi City, June', 9.5, 'middle', opacity=.7))
    rows = [('Train', 468, 42, 2.9), ('Bicycle', 372, 24, 3.8),
            ('Bus', 204, 35, 2.6), ('Walking', 156, 18, 4.1)]
    ax, ay, aw, ah = 74, 56, 300, 152     # 棒グラフの領域
    b.append(_line(ax, ay, ax, ay + ah, op=.45))
    b.append(_line(ax, ay + ah, ax + aw, ay + ah, op=.45))
    for v in (0, 100, 200, 300, 400, 500):
        yy = ay + ah - ah * v / 500
        b.append(_line(ax - 4, yy, ax + aw, yy, op=.16 if v else .45))
        b.append(_t(ax - 8, yy + 3.5, v, 8.5, 'end', opacity=.7))
    b.append(_t(ax - 8, ay - 6, 'students', 9, 'end', 'bold', opacity=.8))
    b.append(_t(ax + aw + 8, ay - 6, 'rating', 9, 'start', 'bold', opacity=.8, fill=RED))
    for v in (1, 2, 3, 4, 5):
        yy = ay + ah - ah * v / 5.0
        b.append(_t(ax + aw + 8, yy + 3.5, v, 8.5, 'start', opacity=.7, fill=RED))
    bw, gap = 46, 75
    pts = []
    for i, (lab, n, mins, rate) in enumerate(rows):
        cx = ax + 18 + i * gap
        h = ah * n / 500
        b.append(_rect(cx, ay + ah - h, bw, h, fill=BLUE, op=.45, stroke=BLUE, sop=.7, rx=2))
        # 人数は棒の内側に置く。棒の上は評価の折れ線が通るので譲る。
        b.append(_t(cx + bw / 2, ay + ah - h + 14, n, 10, 'middle', 'bold'))
        b.append(_t(cx + bw / 2, ay + ah + 14, lab, 10, 'middle'))
        b.append(_t(cx + bw / 2, ay + ah + 26, f'{mins} min', 8.5, 'middle', opacity=.7))
        pts.append((cx + bw / 2, ay + ah - ah * rate / 5.0, rate))
    b.append(_path('M' + ' L'.join(f'{x},{y}' for x, y, _ in pts), stroke=RED, sw=1.4, op=.55))
    for x, y, rate in pts:
        b.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{RED}" fill-opacity=".95"/>')
        b.append(_t(x, y - 10, rate, 9, 'middle', 'bold', fill=RED))
    b.append(_line(24, 244, 436, 244, op=.25))
    b.append(_t(30, 260, 'Reported times ran 7 min short of recorded times (train users: 11 min).', 9.5, opacity=.85))
    b.append(_t(30, 274, 'Ratings compare people, not methods: each student rated only their own journey.', 9.5, opacity=.85))
    return _svg(460, 290, ''.join(b), 'Travel to school survey chart')


# =====================================================================
# 第5問 — 発表用ノート (年表)
# =====================================================================
def fig_5():
    b = [_rect(6, 6, 448, 224, rx=8, sop=.35)]
    b.append(_t(230, 26, 'PRESENTATION NOTES: INES BERTRAND', 12.5, 'middle', 'bold'))
    y = 86
    b.append(_line(38, y, 424, y, op=.45, sw=1.5))
    b.append(_path(f'M424,{y} L416,{y - 4} M424,{y} L416,{y + 4}', sw=1.5, op=.45))
    marks = [('1901', 'born in the south of France, the fourth of six children', BLUE),
             # 本文は「at sixteen」としか書いていない。1917 と年号に直すのは
             # 本文に無い事実の持ち込みになるので、年齢のまま置く。
             ('at 16', 'paints numbers on clock faces in her father\'s workshop', AMBER),
             ('1922', 'Dr Meyer sees her margin drawings in the order book', AMBER),
             ('1923', 'technical assistant in Meyer\'s laboratory, Lyon', GREEN),
             ('+11 yrs', 'over 4,000 illustrations, none of them signed', GREEN)]
    for i, (yr, txt, col) in enumerate(marks):
        x = 52 + i * 89
        b.append(_line(x, y - 7, x, y + 7, op=.55, sw=1.2))
        b.append(f'<circle cx="{x}" cy="{y}" r="6.5" fill="{col}" fill-opacity=".9"/>')
        b.append(_t(x, y - 16, yr, 10.5, 'middle', 'bold'))
        for j, ln in enumerate(_wrap(txt, 17)[:4]):
            b.append(_t(x, y + 24 + j * 10.5, ln, 8, 'middle', opacity=.9))
    b.append(_line(24, 152, 436, 152, op=.25))
    b.append(_t(30, 170, 'Why a drawing, not a photograph?', 10, 'start', 'bold', opacity=.9))
    b.append(_t(30, 186, 'Photography of microscopic samples flattened everything into grey.', 9.5, opacity=.85))
    b.append(_t(30, 200, 'An illustrator could decide which parts mattered and show them clearly.', 9.5, opacity=.85))
    b.append(_t(30, 214, 'One plate could take three weeks: microscope, draft, correction, redraw.', 9.5, opacity=.85))
    return _svg(460, 232, ''.join(b), 'Biography presentation notes')


# =====================================================================
# 第6問A — 都市の樹木 (冷却は局所的・被覆率の格差)
# =====================================================================
def fig_6a():
    b = [_rect(6, 6, 448, 244, rx=8, sop=.35)]
    b.append(_t(230, 26, 'WHERE THE TREES ARE, AND WHERE THE HEAT IS', 12.5, 'middle', 'bold'))
    gy = 150
    b.append(_line(24, gy, 436, gy, op=.5))
    # 郊外の公園 (木は多い・気温は低い)
    b.append(_rect(24, 44, 132, gy - 44, fill=GREEN, op=.08, stroke='none'))
    b.append(_t(90, 60, 'park on the edge', 10, 'middle', 'bold', opacity=.9))
    for i in range(9):
        x, ty = 34 + (i % 5) * 28, 96 + (i // 5) * 26
        b.append(_line(x, ty, x, ty + 16, sw=1.6, op=.85))
        b.append(f'<circle cx="{x}" cy="{ty - 4}" r="8" fill="{GREEN}" fill-opacity=".55" stroke="none"/>')
    # 中心部 (建物が密・木が少ない・気温が高い)
    b.append(_rect(176, 44, 260, gy - 44, fill=RED, op=.08, stroke='none'))
    b.append(_t(306, 60, 'crowded central district', 10, 'middle', 'bold', opacity=.9))
    for i, (bx, bh) in enumerate([(186, 62), (216, 84), (246, 50), (276, 76), (306, 92),
                                  (336, 58), (366, 80), (396, 66)]):
        b.append(_rect(bx, gy - bh, 24, bh, sop=.45, fill=FG, op=.07))
    b.append(_line(258, 130, 258, gy, sw=1.6, op=.85))
    b.append(f'<circle cx="258" cy="126" r="8" fill="{GREEN}" fill-opacity=".55" stroke="none"/>')
    b.append(_line(390, 130, 390, gy, sw=1.6, op=.85))
    b.append(f'<circle cx="390" cy="126" r="8" fill="{GREEN}" fill-opacity=".55" stroke="none"/>')
    # 冷却は数メートルの局所効果
    b.append(f'<ellipse cx="258" cy="{gy}" rx="26" ry="7" fill="{BLUE}" fill-opacity=".35"/>')
    b.append(_t(258, gy + 20, 'shade + water vapour', 8.5, 'middle', fill=BLUE))
    b.append(_t(258, gy + 31, 'cools only a few metres', 8.5, 'middle', fill=BLUE))
    b.append(_t(90, gy + 20, '1,000 trees here do very little', 8.5, 'middle', opacity=.8))
    b.append(_t(90, gy + 31, 'for the district that is hottest', 8.5, 'middle', opacity=.8))
    # 被覆率の格差
    b.append(_line(24, 194, 436, 194, op=.25))
    b.append(_t(30, 212, 'Tree cover, 37 cities surveyed', 10, 'start', 'bold', opacity=.9))
    b.append(_t(196, 227, 'wealthier districts', 9, 'end', opacity=.85))
    b.append(_rect(204, 216, 180, 13, fill=GREEN, op=.45, stroke='none', rx=2))
    b.append(_t(196, 242, 'lower-income districts', 9, 'end', opacity=.85))
    b.append(_rect(204, 231, 180 * .76, 13, fill=AMBER, op=.5, stroke='none', rx=2))
    b.append(_t(392, 242, '24% less', 9, 'start', 'bold', fill=AMBER))
    return _svg(460, 252, ''.join(b), 'Urban trees and heat diagram')


# =====================================================================
# 第6問B — 食品ロスの発生位置 (ポスター用の図解)
# =====================================================================
def fig_6b():
    b = [_rect(6, 6, 448, 252, rx=8, sop=.35)]
    b.append(_t(230, 26, 'WHERE FOOD IS LOST ALONG THE CHAIN', 12.5, 'middle', 'bold'))
    stages = ['Field', 'Storage', 'Transport', 'Shop', 'Home']
    x0, sw_, gap = 28, 74, 10
    for i, s in enumerate(stages):
        x = x0 + i * (sw_ + gap)
        b.append(_rect(x, 44, sw_, 30, rx=5, sop=.4))
        b.append(_t(x + sw_ / 2, 63, s, 10, 'middle', 'bold'))
        if i < len(stages) - 1:
            b.append(_path(f'M{x + sw_ + 1},59 L{x + sw_ + gap - 1},59 '
                           f'M{x + sw_ + gap - 5},55.5 L{x + sw_ + gap - 1},59 '
                           f'M{x + sw_ + gap - 5},62.5 L{x + sw_ + gap - 1},59', sw=1.3, op=.6))
    # 低所得国: 損失は前半に集中
    b.append(_t(28, 100, 'Lower-income countries', 10, 'start', 'bold', opacity=.9))
    b.append(_rect(28, 108, 412, 20, fill=FG, op=.05, stroke='none', rx=3))
    b.append(_rect(28, 108, 3 * sw_ + 2 * gap, 20, fill=AMBER, op=.45, stroke='none', rx=3))
    b.append(_t(154, 122, 'most losses: field to market', 9.5, 'middle'))
    b.append(_t(28, 144, 'insects in storage, no refrigeration, no buyer before the crop rots', 9, opacity=.8))
    b.append(_t(28, 157, 'households throw away very little', 9, opacity=.8))
    # 高所得国: 損失は後半に集中
    b.append(_t(28, 182, 'Higher-income countries', 10, 'start', 'bold', opacity=.9))
    b.append(_rect(28, 190, 412, 20, fill=FG, op=.05, stroke='none', rx=3))
    b.append(_rect(28 + 3 * (sw_ + gap), 190, 2 * sw_ + gap, 20, fill=RED, op=.45, stroke='none', rx=3))
    b.append(_t(374, 204, 'shops, restaurants, homes', 9.5, 'middle'))
    b.append(_t(28, 226, 'households alone: 45-55% of all food wasted in the country', 9.5,
                'start', 'bold', fill=RED))
    b.append(_t(28, 240, '- more than farms, factories, shops and restaurants combined', 9, opacity=.8))
    return _svg(460, 260, ''.join(b), 'Food loss along the supply chain')


# =====================================================================
FIGURES = {
    '第1問A メッセージ読解': fig_1a,
    '第1問B 告知の読み取り': fig_1b,
    '第2問A 比較とレビュー': fig_2a,
    '第2問B 記事(事実と意見)': fig_2b,
    '第3問A 体験記事': fig_3a,
    '第3問B 体験ブログ(時系列)': fig_3b,
    '第4問 複数資料の統合': fig_4,
    '第5問 伝記とノート作成': fig_5,
    '第6問A 論説文の要旨': fig_6a,
    '第6問B 説明文の整理': fig_6b,
}


# 図中に出てくるが「本文に書かれたデータ」ではない数値 = 軸の目盛り・カレンダーの日付。
# build_eng.py の check_figure がこれ以外の数値を本文と照合する
# (図が本文に無い事実を持ち込まないための歯止め)。
AXIS_TICKS = {
    # カレンダーの日付 1..30 (本文にあるのは 5 と 8 だけ)
    '第1問A メッセージ読解': {str(n) for n in range(1, 31)},
    # 期間バーの目盛りラベルは本文の日付そのもの。追加の目盛りは無い
    '第1問B 告知の読み取り': set(),
    '第2問A 比較とレビュー': set(),
    '第2問B 記事(事実と意見)': set(),
    '第3問A 体験記事': set(),
    '第3問B 体験ブログ(時系列)': {'1', '2', '3', '4', '5'},   # Day 番号の丸数字
    # 左軸 0-500 (100 刻み) と右軸 1-5
    '第4問 複数資料の統合': {'0', '100', '200', '300', '400', '500', '1', '2', '3', '4', '5'},
    '第5問 伝記とノート作成': set(),
    '第6問A 論説文の要旨': set(),
    '第6問B 説明文の整理': set(),
}


def get(group):
    fn = FIGURES.get(group)
    return fn() if fn else ''
