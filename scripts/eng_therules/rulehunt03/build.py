#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英語長文 ルール発見トレーニング No.03「識別・省略編」 — 問題編/解答解説編 を PDF 化。

  python3 build.py            (事前に python3 check.py が ALL PASS であること)

No.01/No.02 の視覚アイデンティティを踏襲(No.03 はティール系)。6ターゲット=
that/it/as の識別・省略・共通関係・程度構文。巻頭に「全18ルール地図」(3列)。
HTML → Chrome --headless --print-to-pdf → fitz でノンブル刻印。apply_annot は入れ子対応。
"""
import os, re, sys, subprocess, html
from collections import defaultdict
import fitz
import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
OUT_Q = os.path.join(HERE, "ルール発見トレーニングNo03_識別省略編_問題編.pdf")
OUT_A = os.path.join(HERE, "ルール発見トレーニングNo03_識別省略編_解答解説編.pdf")

esc = lambda s: html.escape(str(s), quote=False)
TKEY = {t["key"]: t for t in C.TARGETS}

BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 13mm 13mm 16mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.3pt; line-height:1.62; margin:0; }
.gothic, h1,h2,h3,.band,.qno,.secttl,.tgname,.legend,.chip { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
.en { font-family: Georgia,"Times New Roman",serif; }

.band { background: linear-gradient(90deg,#0f172a,#0e7490); color:#fff; padding:9px 14px; border-radius:8px;
  display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:14.5pt; font-weight:700; }
.band .l small { font-weight:600; font-size:9pt; opacity:.92; margin-left:8px; }
.band .l .ed { background:#f59e0b; color:#3b1d00; border-radius:5px; padding:1px 7px; font-size:9pt; margin-left:8px; }
.band .r { text-align:right; font-size:8.5pt; line-height:1.4; }

.instr { font-size:9.4pt; background:#ecfeff; border-left:4px solid #0e7490; padding:7px 10px; border-radius:4px; margin:8px 0; line-height:1.7; }
.instr b { color:#155e75; }

table.tg { width:100%; border-collapse:collapse; font-size:9pt; margin:6px 0 2px; }
table.tg th, table.tg td { border:1px solid #cbd5e1; padding:6px 9px; vertical-align:top; line-height:1.55; }
table.tg th { background:#cffafe; white-space:nowrap; font-family:"Hiragino Kaku Gothic ProN",sans-serif; padding:5px 9px; }
table.tg td.nm { white-space:nowrap; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
table.tg td.mk2 { white-space:nowrap; }
table.tg.targets { table-layout:fixed; }
table.tg.targets td.nm { white-space:normal; vertical-align:middle; }
table.tg.targets td.mk2 { white-space:normal; vertical-align:middle; color:#334155; }

.secttl { font-size:12.5pt; font-weight:700; color:#0f172a; border-left:6px solid #0e7490;
  padding:2px 0 2px 10px; margin:18px 0 9px; page-break-after:avoid; }
.secttl .en2 { font-size:8.5pt; color:#64748b; margin-left:8px; }
.pb { page-break-before: always; }

/* rule map (巻頭・3列・縦積みブロック) */
.mapwrap { display:flex; gap:11px; margin:8px 0 6px; align-items:flex-start; }
.mapcol { flex:1; min-width:0; border:1.3px solid #cbd5e1; border-radius:10px; overflow:hidden; }
.mapcol .mh { padding:8px 12px; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:9.8pt; color:#fff; }
.mapcol.A .mh { background:#1e3a8a; }
.mapcol.B .mh { background:#6d28d9; }
.mapcol.C .mh { background:#0e7490; }
.mapcol .mh small { font-weight:600; font-size:8pt; opacity:.92; display:block; margin-top:2px; }
.mrow { display:flex; gap:7px; padding:8px 12px; border-top:1px solid #eef2f7; }
.mrow:first-of-type { border-top:none; }
.mg { flex:none; width:1.4em; color:#94a3b8; font-weight:700; font-size:9pt; }
.mbody { flex:1; min-width:0; }
.mtop { display:flex; justify-content:space-between; align-items:baseline; gap:6px; }
.mname { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:9pt; color:#0f172a; }
.mchip { flex:none; white-space:nowrap; color:#475569; font-size:7.4pt; background:#f1f5f9; border:1px solid #e2e8f0; border-radius:4px; padding:1px 5px; }
.mpt { color:#334155; font-size:8.2pt; line-height:1.45; margin-top:3px; }

/* passage */
.ptitle { text-align:center; font-size:12pt; font-weight:700; margin:8px 0 2px; font-family:Georgia,serif; }
.pjtitle { text-align:center; font-size:8.5pt; color:#64748b; margin-bottom:6px; }
.passage { border:1.2px solid #94a3b8; border-radius:8px; padding:10px 14px; }
.passage p { margin:0 0 7px; }
.passage .en { line-height:2.2; text-align:justify; }
.passage sup.sn { color:#0e7490; font-weight:700; font-size:7.5pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:1px; }
.wcount { text-align:right; color:#64748b; font-size:8.5pt; margin-top:2px; }

/* questions */
.q { margin:0 0 10px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:8px; margin-bottom:2px; }
.qno { color:#fff; border-radius:5px; padding:1px 9px; font-size:9.3pt; font-weight:700; }
.q .stem { font-size:9.8pt; }
table.fill { width:100%; border-collapse:collapse; font-size:9.2pt; margin-top:4px; }
table.fill th, table.fill td { border:1px solid #94a3b8; padding:3px 7px; }
table.fill th { background:#f8fafc; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:600; white-space:nowrap; }
table.fill td { height:30px; }
.smallnote { font-size:8.6pt; color:#475569; margin-top:2px; }

/* annotations (解答編) — 6ターゲット */
.tid { background:#e0e7ff; color:#3730a3; border:1px solid #c7d2fe; border-radius:3px; padding:0 2px; font-weight:700; }
.iid { background:#cffafe; color:#155e75; border:1px solid #a5f3fc; border-radius:3px; padding:0 2px; font-weight:700; }
.aid { background:#fae8ff; color:#86198f; border:1px solid #f5d0fe; border-radius:3px; padding:0 2px; font-weight:700; }
.ell { border-bottom:2px dashed #c2410c; color:#9a3412; font-weight:600; }
.par { border-bottom:2.4px solid #15803d; color:#166534; font-weight:600; }
.deg { border:1.4px solid #dc2626; border-radius:4px; padding:0 2px; color:#b91c1c; font-weight:600; }
.legend { font-size:8.6pt; margin:4px 0 8px; color:#334155; line-height:1.9; }
.legend span.item { margin-right:10px; white-space:nowrap; }

/* answer tables */
table.ans { width:100%; border-collapse:collapse; font-size:9.1pt; margin:3px 0 10px; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:4px 7px; vertical-align:top; }
table.ans th { background:#cffafe; font-family:"Hiragino Kaku Gothic ProN",sans-serif; white-space:nowrap; }
table.ans td.s { white-space:nowrap; font-weight:700; color:#155e75; }
table.ans td.t { font-family:Georgia,serif; }
.tgname { font-weight:700; font-size:10.5pt; margin:10px 0 3px; page-break-after:avoid; }
.tgname .cnt { color:#64748b; font-size:8.8pt; font-weight:600; margin-left:6px; }
.tgname .gn { color:#94a3b8; font-size:8.5pt; font-weight:600; margin-left:4px; }
.invblk { page-break-inside:avoid; break-inside:avoid; }
td.nw { white-space:nowrap; }
.think { background:#ecfeff; border:1px solid #67e8f9; border-radius:6px; padding:6px 10px;
  font-size:9.3pt; margin:-4px 0 10px; page-break-inside:avoid; }
.think b { color:#155e75; }

.lecture { border:1px solid #cbd5e1; border-left:5px solid #0e7490; border-radius:6px; padding:8px 11px; margin:0 0 9px; page-break-inside:avoid; font-size:9.5pt; }
.lecture .lh { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:10.3pt; margin-bottom:2px; }
.lecture .slogan { color:#b91c1c; font-weight:700; }
.trap { background:#fff7ed; border:1px solid #fdba74; border-radius:6px; padding:7px 10px; margin:0 0 8px; font-size:9.3pt; page-break-inside:avoid; }
.trap b { color:#9a3412; }

.trbox { font-size:9.4pt; }
.trbox .tr1 { margin:0 0 5px; }
.trbox .sn2 { color:#0e7490; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.3pt; }
.footnote { margin-top:12px; color:#64748b; font-size:8.2pt; border-top:1px solid #cbd5e1; padding-top:5px; }
"""


def header(kind):
    m = C.META
    return (f'<div class="band"><div class="l">{esc(m["series"])} {esc(m["no"])}'
            f'<span class="ed">{esc(m["edition"])}</span>'
            f'<small>{esc(kind)}</small></div>'
            f'<div class="r">{esc(m["subtitle"])}<br>対象: {esc(m["level"])} ｜ {esc(m["time"])}</div></div>')


def sup(n):
    return f'<sup class="sn">({n})</sup>'


def apply_annot(pkey, n, raw):
    """文 n の全 ANNOT を入れ子対応でスパン化。同一 t は class 結合。部分重複は検出して落とす。"""
    items = {}
    for cat, lst in C.ANNOT[pkey].items():
        cls = TKEY[cat]["cls"]
        for it in lst:
            if it["s"] == n:
                items.setdefault(it["t"], set()).add(cls)
    if not items:
        return esc(raw)
    spans = []
    for t, clss in items.items():
        start = raw.find(t)
        if start < 0:
            sys.exit(f"annotate fail: {pkey} 文{n} 「{t[:30]}」not found")
        spans.append((start, start + len(t), " ".join(sorted(clss))))
    spans.sort(key=lambda x: (x[0], -x[1]))
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            (s1, e1, _), (s2, e2, _) = spans[i], spans[j]
            if s2 < e1 and e2 > e1:
                sys.exit(f"annotate overlap: {pkey} 文{n}: 部分重複スパン {spans[i]} / {spans[j]}")
    opens = defaultdict(list)
    for s, e, c in spans:
        opens[s].append((e, c))
    for s in opens:
        opens[s].sort(key=lambda x: -x[0])
    out, stack = [], []
    for pos in range(len(raw) + 1):
        while stack and stack[-1] == pos:
            out.append("</span>")
            stack.pop()
        for e, c in opens.get(pos, []):
            out.append(f'<span class="{c}">')
            stack.append(e)
        if pos < len(raw):
            out.append(esc(raw[pos]))
    return "".join(out)


def passage_html(p, annotate=False):
    parts = [f'<div class="ptitle">{esc(p["title"])}</div>',
             f'<div class="pjtitle">{esc(p["jtitle"])}</div>', '<div class="passage">']
    for para in p["paras"]:
        buf = []
        for s in para:
            text = apply_annot(p["key"], s["n"], s["en"]) if annotate else esc(s["en"])
            buf.append(sup(s["n"]) + text)
        parts.append('<p class="en">' + " ".join(buf) + "</p>")
    words = len(re.split(r"\s+", " ".join(s["en"] for para in p["paras"] for s in para).strip()))
    parts.append("</div>")
    parts.append(f'<div class="wcount">({words} words)</div>')
    return "\n".join(parts)


def legend():
    marks = {"tid": "〇＋役割", "iid": "〇＋役割", "aid": "〇＋役割", "ell": "∧＋補い", "par": "[ ] △", "deg": "□→that/to"}
    items = [f'<span class="item"><span class="{t["cls"]}">{esc(t["name"])}</span>（{esc(marks[t["key"]])}）</span>'
             for t in C.TARGETS]
    return f'<div class="legend">凡例: {"".join(items)}</div>'


def rulemap_html():
    cols = []
    for key in ("A", "B", "C"):
        g = C.RULEMAP[key]
        rows = "".join(
            f'<div class="mrow"><div class="mg">{esc(no)}</div><div class="mbody">'
            f'<div class="mtop"><span class="mname">{esc(name)}</span>'
            f'<span class="mchip">{esc(mk)}</span></div>'
            f'<div class="mpt">{esc(pt)}</div></div></div>'
            for (no, name, mk, pt) in g["rows"])
        cols.append(f'<div class="mapcol {key}"><div class="mh">{esc(g["title"])}'
                    f'<small>{esc(g["sub"])}</small></div>{rows}</div>')
    return '<div class="mapwrap">' + "".join(cols) + "</div>"


def targets_table():
    rows = []
    for t in C.TARGETS:
        rows.append(f'<tr><td class="nm" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}'
                    f'<div class="smallnote" style="color:#94a3b8;white-space:nowrap">全18ルール中の{t["gno"]}</div></td>'
                    f'<td>{esc(t["what"])}<div class="smallnote">目印: {esc(t["sign"])}</div></td>'
                    f'<td class="mk2">{esc(t["mark"])}</td></tr>')
    return ('<table class="tg targets">'
            '<colgroup><col style="width:19%"><col style="width:49%"><col style="width:32%"></colgroup>'
            '<tr><th>ターゲット</th><th>何を探すか</th><th>付ける印</th></tr>'
            + "".join(rows) + "</table>")


def q_block(no, color, title, stem, fill_html=""):
    return (f'<div class="q"><div class="h"><span class="qno" style="background:{color}">{no}</span>'
            f'<b class="gothic">{esc(title)}</b></div>'
            f'<div class="stem">{stem}</div>{fill_html}</div>')


def fill_table(headers, nrows):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join("<td></td>" for _ in headers) + "</tr>" for _ in range(nrows))
    return f'<table class="fill"><tr>{th}</tr>{trs}</table>'


QDEF = {
 "tid": ("すべての <b>that / those</b> に〇をつけ、上に役割を書け"
         "（<b>接</b>=接続詞／<b>関</b>=関係代名詞／<b>同</b>=同格／<b>指</b>=指示／<b>強</b>=強調構文）。"
         '<div class="smallnote">見分け: that の直後が完全文→接続詞・同格、欠けた不完全文→関係代名詞。</div>',
         ["文番号", "that / those の箇所", "役割（接/関/同/指/強）"]),
 "iid": ("すべての <b>it</b> に〇をつけ、上に役割を書け"
         "（<b>仮主</b>=仮主語／<b>仮目</b>=仮目的語／<b>代</b>=代名詞／<b>強</b>=強調／<b>状</b>=状況）。",
         ["文番号", "it の箇所", "役割（仮主/仮目/代/強/状）"]),
 "aid": ("すべての <b>as</b> に〇をつけ、上に役割を書け"
         "（<b>様</b>=様態／<b>理</b>=理由／<b>時</b>=時・比例／<b>前</b>=前置詞「として」／<b>比</b>=as…as）。",
         ["文番号", "as の箇所", "役割（様/理/時/前/比）"]),
 "ell": ("<b>省略</b>のある箇所に「∧」を書き、補う語を（　）で入れよ。",
         ["文番号", "省略のある箇所", "補う語"]),
 "par": ("<b>並列</b>の要素を [　] でくくり、接続詞（and / but / or / not only … など）に△をつけ、"
         "「何と何が並ぶか」を書け。",
         ["文番号", "並列の箇所", "何と何が並ぶか"]),
 "deg": ("<b>so / such / too / enough</b> に□をつけ、結びつく <b>that・to</b> まで矢印を引け。",
         ["文番号", "該当箇所", "型（so~that / such~that / too~to / enough to）"]),
}
QNO = {"tid": "問 1-1", "iid": "問 1-2", "aid": "問 1-3", "ell": "問 1-4", "par": "問 1-5", "deg": "問 1-6"}

THINK_Q = ('<div class="smallnote">考える1問: 文(1) It is clear that … と 文(10) it is curiosity that … は'
           'どちらも「It is … that」の形。片方は<b>仮主語</b>、片方は<b>強調構文</b>。どちらがどちらか、理由も書け → 記入欄。</div>')
THINK_ANS = ('<div class="think"><b>問1-2「考える1問」の答え:</b> 文(1)=<b>仮主語</b>（that 以下 “curiosity … is what …” は完全文で、'
             'It の中身そのもの。名詞1つを抜き出せない）。文(10)=<b>強調構文</b>（curiosity という名詞を強調。'
             'It is と that を外すと “Curiosity … decides how far a mind will travel.” に戻る）。'
             '「It is と that を外して元の文に戻せるか」が決定打。</div>')


def build_q():
    h = [header("問題編")]
    h.append('<div class="instr"><b>これは「読解問題」ではありません。</b>設問はすべて「本文から<b>探して、印をつける</b>」だけ。'
             'No.01(流れ)・No.02(構造)に続き、今回は<b>迷いやすい形の「見分け」と、省略の「補い」</b>を反射化する筋トレです。<br>'
             '<b>使い方</b>: 1周目=時間無制限で全部見分ける → 答え合わせ(解答編の色マーク本文と突き合わせ) → '
             '数日後の2周目=同じ本文を12分で再判定。')
    h.append('<div class="secttl">英文読解ルール 全18の地図<span class="en2">No.01(流れ)＋No.02(構造)＋No.03(識別)</span></div>')
    h.append('<div class="smallnote" style="margin:0 2px 4px">No.01で「流れ」、No.02で「構造」、この No.03 で「識別・省略」を——'
             '関正生『The Rules』式の英文の読み方を、この18個で完全網羅します(番号・文言は当塾独自)。</div>')
    h.append(rulemap_html())
    h.append('<div class="secttl">今回の6ターゲット（⑬〜⑱）</div>')
    h.append(targets_table())

    for p in C.PASSAGES:
        ann = C.ANNOT[p["key"]]
        h.append(f'<div class="pb"></div><div class="secttl">{esc(p["label"])}'
                 f'<span class="en2">{esc(p["title"])}</span></div>')
        h.append(passage_html(p))
        if p["hint"]:
            h.append('<div class="instr">ターゲットごとに<b>個数を明かした状態</b>で見分ける練習。本文に印をつけてから、表を埋めよう。</div>')
            counts = {k: len(v) for k, v in ann.items()}
            for key in ("tid", "iid", "aid", "ell", "par", "deg"):
                t = TKEY[key]
                stem, headers = QDEF[key]
                fill = fill_table(headers, counts[key])
                if key == "iid":
                    stem = stem + THINK_Q
                    fill = fill + ('<table class="fill"><tr><th style="width:9em">考える1問の答え</th>'
                                   '<td style="height:26px"></td></tr></table>')
                h.append(q_block(QNO[key], t["color"],
                                 f'{t["no"]} {t["name"]}（全 {counts[key]} 箇所）', stem, fill))
        else:
            total = sum(len(v) for v in ann.values())
            h.append(f'<div class="instr"><b>仕上げ: 個数ヒントなしの一括判定。</b>6ターゲットすべてを自力で見分け、'
                     f'本文に印(〇＋役割・∧・[ ]△・□→)をつけてから、下の集計表に「見つけた個数」を書け。'
                     f'<b>合計 {total} 箇所</b>ある。全部見分けるまで帰るな。</div>')
            rows = "".join(
                f'<tr><td class="nm" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}</td>'
                f'<td style="width:5.5em"></td><td></td></tr>'
                for t in C.TARGETS)
            h.append('<table class="fill"><tr><th>ターゲット</th><th>見つけた個数</th>'
                     '<th>文番号のメモ</th></tr>' + rows + "</table>")
    h.append(f'<div class="footnote">{esc(C.META["note"])}</div>')
    return "\n".join(h)


# ------------------------------------------------------------------ 解答解説編
CAT_COLS = {
    "tid": (["文", "that / those", "役割", "ひとこと"],
            lambda it: [it["t"], it["role"], it["note"]], {1}),
    "iid": (["文", "it", "役割", "ひとこと"],
            lambda it: [it["t"], it["role"], it["note"]], {1}),
    "aid": (["文", "as", "役割", "ひとこと"],
            lambda it: [it["t"], it["role"], it["note"]], {1}),
    "ell": (["文", "省略のある箇所", "補う語", "ひとこと"],
            lambda it: [it["t"], it["supply"], it["note"]], {1}),
    "par": (["文", "並列の箇所", "型", "結ぶもの", "ひとこと"],
            lambda it: [it["t"], it["kind"], it["joins"], it["note"]], {1}),
    "deg": (["文", "該当箇所", "型", "ひとこと"],
            lambda it: [it["t"], it["kind"], it["note"]], {1}),
}


def inv_tables(pkey):
    out = []
    for t in C.TARGETS:
        items = C.ANNOT[pkey][t["key"]]
        heads, rowf, nowrap = CAT_COLS[t["key"]]
        blk = [f'<div class="tgname" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}'
               f'<span class="cnt">全 {len(items)} 箇所</span>'
               f'<span class="gn">(全18ルール中の{t["gno"]})</span></div>']
        th = "".join(f"<th>{esc(x)}</th>" for x in heads)
        trs = []
        for it in items:
            cells = rowf(it)
            tds = f'<td class="s">({it["s"]})</td>'
            tds += f'<td class="t">{esc(cells[0])}</td>'
            for ci, c in enumerate(cells[1:], 1):
                cls = ' class="nw"' if ci in nowrap else ""
                tds += f"<td{cls}>{esc(c)}</td>"
            trs.append(f"<tr>{tds}</tr>")
        blk.append(f'<table class="ans"><tr>{th}</tr>{"".join(trs)}</table>')
        out.append(f'<div class="invblk">{"".join(blk)}</div>')
        if pkey == "p1" and t["key"] == "iid":
            out.append(THINK_ANS)
    return "\n".join(out)


def build_a():
    h = [header("解答・解説編")]
    h.append('<div class="secttl">解答一覧（個数）と★合言葉</div>')
    rows = []
    for t in C.TARGETS:
        c1 = len(C.ANNOT["p1"][t["key"]])
        c2 = len(C.ANNOT["p2"][t["key"]])
        rows.append(f'<tr><td class="nm" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}'
                    f'<span class="gn" style="color:#94a3b8;font-size:8pt"> {t["gno"]}</span></td>'
                    f'<td style="text-align:center">{c1}</td><td style="text-align:center">{c2}</td>'
                    f'<td>{esc(t["slogan"])}</td></tr>')
    h.append('<table class="tg"><tr><th>ターゲット</th><th>訓練1</th><th>訓練2</th><th>★合言葉</th></tr>'
             + "".join(rows) + "</table>")

    for p in C.PASSAGES:
        h.append(f'<div class="pb"></div><div class="secttl">{esc(p["label"])}　解答'
                 f'<span class="en2">{esc(p["title"])}</span></div>')
        h.append(legend())
        h.append(passage_html(p, annotate=True))
        h.append('<div style="height:6px"></div>')
        h.append(inv_tables(p["key"]))

    h.append('<div class="pb"></div><div class="secttl">ひっかけ注意報 — 「それっぽいのに違う」</div>')
    for tr in C.TRAPS:
        tname = TKEY[tr["target"]]["name"]
        h.append(f'<div class="trap"><b>【{esc(tname)}の見分け】 {esc(tr["t"])}</b><br>{esc(tr["note"])}</div>')

    h.append('<div class="secttl">ミニ講義 — 6ターゲットの「見分け方」総まとめ</div>')
    for t in C.TARGETS:
        h.append(f'<div class="lecture"><div class="lh" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}'
                 f'　<span style="font-size:8.5pt;color:#64748b">{esc(t["series"])}</span></div>'
                 f'<div class="slogan">★ {esc(t["slogan"])}</div>'
                 f'<div>{esc(C.LECTURES[t["key"]])}</div></div>')

    for p in C.PASSAGES:
        h.append(f'<div class="pb"></div><div class="secttl">{esc(p["label"])}　全訳</div><div class="trbox">')
        for para in p["paras"]:
            buf = [f'<span class="sn2">({s["n"]})</span> {esc(C.TRANS[p["key"]][s["n"]])}' for s in para]
            h.append('<div class="tr1">' + "　".join(buf) + "</div>")
        h.append("</div>")
    h.append(f'<div class="footnote">{esc(C.META["note"])}</div>')
    return "\n".join(h)


def render(body, out_path):
    doc = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
           f'<style>{BASE_CSS}</style></head><body>{body}</body></html>')
    tmp = os.path.join(HERE, "_" + os.path.basename(out_path).replace(".pdf", ".html"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(doc)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=12000", f"--print-to-pdf={out_path}",
                    "file://" + tmp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = fitz.open(out_path)
    for i, page in enumerate(d):
        n = str(i + 1)
        tw = fitz.Font(fontfile=FONT_PATH).text_length(n, fontsize=9)
        page.insert_text((page.rect.width / 2 - tw / 2, page.rect.height - 20), n,
                         fontfile=FONT_PATH, fontname="AU", fontsize=9, color=(0.45, 0.45, 0.45))
    d.subset_fonts()
    tmp2 = out_path + ".tmp"
    d.save(tmp2, garbage=4, deflate=True, clean=True)
    d.close()
    os.replace(tmp2, out_path)
    d = fitz.open(out_path)
    print(f"WROTE {out_path} | pages: {d.page_count}")
    d.close()


def main():
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py")],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        print(r.stdout + r.stderr)
        sys.exit("check.py FAILED — 解答キーを直してからビルドすること")
    print(r.stdout.strip())
    render(build_q(), OUT_Q)
    render(build_a(), OUT_A)


if __name__ == "__main__":
    main()
