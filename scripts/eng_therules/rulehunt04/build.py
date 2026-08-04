#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英語長文 ルール発見トレーニング No.04「読解の運用編」 — 問題編/解答解説編 を PDF 化。

  python3 build.py            (事前に python3 check.py が ALL PASS であること)

No.01〜03 の視覚アイデンティティを踏襲(No.04 はクリムゾン系)。6ターゲット=語彙推測・指示語・
言い換え・抽象具体・主張評価・マーカー予測。巻頭に「全24ルール地図」(4列)。各長文に「設問の解き方」。
HTML → Chrome --headless --print-to-pdf → fitz でノンブル刻印。apply_annot は入れ子対応。
"""
import os, re, sys, subprocess, html
from collections import defaultdict
import fitz
import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
OUT_Q = os.path.join(HERE, "ルール発見トレーニングNo04_読解運用編_問題編.pdf")
OUT_A = os.path.join(HERE, "ルール発見トレーニングNo04_読解運用編_解答解説編.pdf")

esc = lambda s: html.escape(str(s), quote=False)
TKEY = {t["key"]: t for t in C.TARGETS}

BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 13mm 13mm 16mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.3pt; line-height:1.62; margin:0; }
.gothic, h1,h2,h3,.band,.qno,.secttl,.tgname,.legend,.chip { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
.en { font-family: Georgia,"Times New Roman",serif; }

.band { background: linear-gradient(90deg,#0f172a,#be123c); color:#fff; padding:9px 14px; border-radius:8px;
  display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:14.5pt; font-weight:700; }
.band .l small { font-weight:600; font-size:9pt; opacity:.92; margin-left:8px; }
.band .l .ed { background:#f59e0b; color:#3b1d00; border-radius:5px; padding:1px 7px; font-size:9pt; margin-left:8px; }
.band .r { text-align:right; font-size:8.5pt; line-height:1.4; }

.instr { font-size:9.4pt; background:#fff1f2; border-left:4px solid #be123c; padding:7px 10px; border-radius:4px; margin:8px 0; line-height:1.7; }
.instr b { color:#9f1239; }

table.tg { width:100%; border-collapse:collapse; font-size:9pt; margin:6px 0 2px; }
table.tg th, table.tg td { border:1px solid #cbd5e1; padding:6px 9px; vertical-align:top; line-height:1.55; }
table.tg th { background:#ffe4e6; white-space:nowrap; font-family:"Hiragino Kaku Gothic ProN",sans-serif; padding:5px 9px; }
table.tg td.nm { white-space:nowrap; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
table.tg td.mk2 { white-space:nowrap; }
table.tg.targets { table-layout:fixed; }
table.tg.targets td.nm { white-space:normal; vertical-align:middle; }
table.tg.targets td.mk2 { white-space:normal; vertical-align:middle; color:#334155; }

.secttl { font-size:12.5pt; font-weight:700; color:#0f172a; border-left:6px solid #be123c;
  padding:2px 0 2px 10px; margin:18px 0 9px; page-break-after:avoid; }
.secttl .en2 { font-size:8.5pt; color:#64748b; margin-left:8px; }
.pb { page-break-before: always; }

/* rule map (巻頭・4列・縦積みブロック) */
.mapwrap { display:flex; gap:8px; margin:8px 0 6px; align-items:flex-start; }
.mapcol { flex:1; min-width:0; border:1.2px solid #cbd5e1; border-radius:9px; overflow:hidden; }
.mapcol .mh { padding:7px 10px; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:9pt; color:#fff; }
.mapcol.A .mh { background:#1e3a8a; }
.mapcol.B .mh { background:#6d28d9; }
.mapcol.C .mh { background:#0e7490; }
.mapcol.D .mh { background:#be123c; }
.mapcol .mh small { font-weight:600; font-size:7.4pt; opacity:.92; display:block; margin-top:2px; }
.mrow { display:flex; gap:5px; padding:6px 10px; border-top:1px solid #eef2f7; }
.mrow:first-of-type { border-top:none; }
.mg { flex:none; width:1.3em; color:#94a3b8; font-weight:700; font-size:8.4pt; }
.mbody { flex:1; min-width:0; }
.mtop { display:flex; justify-content:space-between; align-items:baseline; gap:4px; }
.mname { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:8.3pt; color:#0f172a; line-height:1.3; }
.mchip { flex:none; white-space:nowrap; color:#64748b; font-size:6.8pt; background:#f1f5f9; border:1px solid #e2e8f0; border-radius:3px; padding:0 4px; }
.mpt { color:#475569; font-size:7.5pt; line-height:1.4; margin-top:2px; }

/* passage */
.ptitle { text-align:center; font-size:12pt; font-weight:700; margin:8px 0 2px; font-family:Georgia,serif; }
.pjtitle { text-align:center; font-size:8.5pt; color:#64748b; margin-bottom:6px; }
.passage { border:1.2px solid #94a3b8; border-radius:8px; padding:10px 14px; }
.passage p { margin:0 0 7px; }
.passage .en { line-height:2.2; text-align:justify; }
.passage sup.sn { color:#be123c; font-weight:700; font-size:7.5pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:1px; }
.wcount { text-align:right; color:#64748b; font-size:8.5pt; margin-top:2px; }

/* questions (marking) */
.q { margin:0 0 10px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:8px; margin-bottom:2px; }
.qno { color:#fff; border-radius:5px; padding:1px 9px; font-size:9.3pt; font-weight:700; }
.q .stem { font-size:9.8pt; }
table.fill { width:100%; border-collapse:collapse; font-size:9.2pt; margin-top:4px; }
table.fill th, table.fill td { border:1px solid #94a3b8; padding:3px 7px; }
table.fill th { background:#f8fafc; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:600; white-space:nowrap; }
table.fill td { height:30px; }
.smallnote { font-size:8.6pt; color:#475569; margin-top:2px; }

/* 設問の解き方 */
.qq { border:1px solid #cbd5e1; border-radius:6px; padding:7px 10px; margin:0 0 8px; font-size:9.7pt; page-break-inside:avoid; }
.qqno { background:#be123c; color:#fff; border-radius:4px; padding:1px 8px; font-weight:700; font-size:9pt; margin-right:6px; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.qtag { color:#64748b; font-size:8.3pt; margin-right:4px; }
.ansline { border-bottom:1px dotted #94a3b8; height:21px; margin-top:7px; }
.qa { border:1px solid #cbd5e1; border-left:4px solid #be123c; border-radius:6px; padding:7px 10px; margin:0 0 8px; font-size:9.4pt; page-break-inside:avoid; }
.qa .qah { font-weight:600; margin-bottom:3px; }
.qa .qaans { margin:2px 0; }
.qa .qahow { color:#334155; background:#fff1f2; border-radius:4px; padding:4px 8px; margin-top:4px; font-size:9.2pt; }
.qa .qahow b, .qa .qaans b { color:#9f1239; }

/* annotations (解答編) — 6ターゲット */
.vcb { background:#fef3c7; color:#92400e; border:1px solid #fde68a; border-radius:3px; padding:0 2px; font-weight:700; }
.ref { border:1.4px solid #1d4ed8; border-radius:4px; padding:0 2px; color:#1d4ed8; font-weight:600; }
.par { border-bottom:2.4px solid #0f766e; color:#0f766e; font-weight:600; }
.abc { background:#ede9fe; color:#6d28d9; border:1px solid #ddd6fe; border-radius:3px; padding:0 2px; font-weight:700; }
.clm { background:#fee2e2; color:#b91c1c; border:1px solid #fecaca; border-radius:3px; padding:0 2px; font-weight:700; }
.mkr { border:1.4px solid #1e3a8a; border-radius:4px; padding:0 2px; color:#1e3a8a; font-weight:700; }
.legend { font-size:8.6pt; margin:4px 0 8px; color:#334155; line-height:1.9; }
.legend span.item { margin-right:10px; white-space:nowrap; }

/* answer tables */
table.ans { width:100%; border-collapse:collapse; font-size:9.1pt; margin:3px 0 10px; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:4px 7px; vertical-align:top; }
table.ans th { background:#ffe4e6; font-family:"Hiragino Kaku Gothic ProN",sans-serif; white-space:nowrap; }
table.ans td.s { white-space:nowrap; font-weight:700; color:#9f1239; }
table.ans td.t { font-family:Georgia,serif; }
.tgname { font-weight:700; font-size:10.5pt; margin:10px 0 3px; page-break-after:avoid; }
.tgname .cnt { color:#64748b; font-size:8.8pt; font-weight:600; margin-left:6px; }
.tgname .gn { color:#94a3b8; font-size:8.5pt; font-weight:600; margin-left:4px; }
.invblk { page-break-inside:avoid; break-inside:avoid; }
td.nw { white-space:nowrap; }
.think { background:#fff1f2; border:1px solid #fda4af; border-radius:6px; padding:6px 10px;
  font-size:9.3pt; margin:-4px 0 10px; page-break-inside:avoid; }
.think b { color:#9f1239; }

.lecture { border:1px solid #cbd5e1; border-left:5px solid #be123c; border-radius:6px; padding:8px 11px; margin:0 0 9px; page-break-inside:avoid; font-size:9.5pt; }
.lecture .lh { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:10.3pt; margin-bottom:2px; }
.lecture .slogan { color:#b91c1c; font-weight:700; }
.trap { background:#fff7ed; border:1px solid #fdba74; border-radius:6px; padding:7px 10px; margin:0 0 8px; font-size:9.3pt; page-break-inside:avoid; }
.trap b { color:#9a3412; }

.trbox { font-size:9.4pt; }
.trbox .tr1 { margin:0 0 5px; }
.trbox .sn2 { color:#be123c; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.3pt; }
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
    marks = {"vcb": "〇＋根拠", "ref": "〇→", "par": "＝線", "abc": "〇＋下線", "clm": "◎", "mkr": "□→"}
    items = [f'<span class="item"><span class="{t["cls"]}">{esc(t["name"])}</span>（{esc(marks[t["key"]])}）</span>'
             for t in C.TARGETS]
    return f'<div class="legend">凡例: {"".join(items)}</div>'


def rulemap_html():
    cols = []
    for key in ("A", "B", "C", "D"):
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
                    f'<div class="smallnote" style="color:#94a3b8;white-space:nowrap">全24ルール中の{t["gno"]}</div></td>'
                    f'<td>{esc(t["what"])}<div class="smallnote">目印: {esc(t["sign"])}</div></td>'
                    f'<td class="mk2">{esc(t["mark"])}</td></tr>')
    return ('<table class="tg targets">'
            '<colgroup><col style="width:20%"><col style="width:48%"><col style="width:32%"></colgroup>'
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
 "vcb": ("知らない語・多義語に〇をつけ、意味を教えてくれる<b>根拠</b>(言い換え／対比／具体例／語源)に下線を引き、種類を書け。",
         ["文番号", "語", "意味のヒント(根拠)", "推測した意味"]),
 "ref": ("<b>指示語</b>(this / these / such / it 等)に〇、指す先へ矢印を引き、指す中身を本文の語で書け。",
         ["文番号", "指示語", "指す中身(本文の語で)"]),
 "par": ("同じ内容の<b>言い換えペア</b>を線で結び、間に「＝」を書け。",
         ["文番号", "言い換えの箇所", "何の言い換えか"]),
 "abc": ("<b>抽象語</b>(problem / cost / rule など)に〇、その<b>具体的な中身</b>に下線を引け。",
         ["文番号", "抽象語", "具体の中身(文番号や語)"]),
 "clm": ("筆者の<b>主張・評価</b>の語(should / 評価語 / 逆接の後ろ)に◎をつけよ。",
         ["文番号", "主張・評価の箇所", "主張 / 評価"]),
 "mkr": ("<b>マーカー</b>に□、直後に来る内容(主張／例／結論／対比／言い換え)を<b>予測</b>して書け。",
         ["文番号", "マーカー", "予測(次に来る内容)"]),
}
QNO = {"vcb": "問 1-1", "ref": "問 1-2", "par": "問 1-3", "abc": "問 1-4", "clm": "問 1-5", "mkr": "問 1-6"}

THINK_Q = ('<div class="smallnote">考える1問: 文(4) a hidden cost の“具体的な中身”は本文のどこに書かれているか、'
           '文番号で答えよ → 記入欄。</div>')
THINK_ANS = ('<div class="think"><b>問1-4「考える1問」の答え:</b> <b>文(5)</b>。For example の後ろに、'
             '「脳が最初の作業を読み込み直すのに一瞬を要する」という具体で示される。'
             '抽象語(cost)の中身は、直後の具体例に置かれる(㉒ 抽象→具体)。</div>')


def qset_questions(pkey):
    """問題編: 設問（記入欄つき）"""
    out = ['<div class="secttl">設問の解き方（実戦演習）</div>',
           '<div class="smallnote" style="margin:0 2px 6px">マークした手がかりを使って、実際の設問を解いてみよう。</div>']
    for i, q in enumerate(C.QSET[pkey], 1):
        out.append(f'<div class="qq"><span class="qqno">設問{i}</span>'
                   f'<span class="qtag">{esc(q["tag"])}</span>{esc(q["q"])}'
                   f'<div class="ansline"></div><div class="ansline"></div></div>')
    return "\n".join(out)


def qset_answers(pkey):
    """解答編: 設問の答え＋解き方"""
    out = ['<div class="secttl">設問の解き方（解答）</div>']
    for i, q in enumerate(C.QSET[pkey], 1):
        out.append(f'<div class="qa"><div class="qah"><span class="qqno">設問{i}</span>'
                   f'<span class="qtag">{esc(q["tag"])}</span>{esc(q["q"])}</div>'
                   f'<div class="qaans"><b>答え:</b> {esc(q["ans"])}</div>'
                   f'<div class="qahow"><b>解き方:</b> {esc(q["how"])}</div></div>')
    return "\n".join(out)


def build_q():
    h = [header("問題編")]
    h.append('<div class="instr"><b>これは「読解問題」ではありません(前半は)。</b>まず本文から<b>読解の手がかりを探して印をつけ</b>、'
             'その後で<b>実際の設問</b>を、印を使って解きます。No.01〜03(流れ・構造・識別)の総仕上げ=<b>読み方の「運用」</b>です。<br>'
             '<b>使い方</b>: 1周目=手がかりを全部マーク→設問を解く→答え合わせ → 2周目=同じ本文を13分で再現。')
    h.append('<div class="secttl">英文読解ルール 全24の地図<span class="en2">No.01流れ＋No.02構造＋No.03識別＋No.04運用</span></div>')
    h.append('<div class="smallnote" style="margin:0 2px 4px">流れ→構造→識別→運用。関正生『The Rules』式の英文の読み方を、この24個で完全網羅します(番号・文言は当塾独自)。</div>')
    h.append(rulemap_html())
    h.append('<div class="secttl">今回の6ターゲット（⑲〜㉔）</div>')
    h.append(targets_table())

    for p in C.PASSAGES:
        ann = C.ANNOT[p["key"]]
        h.append(f'<div class="pb"></div><div class="secttl">{esc(p["label"])}'
                 f'<span class="en2">{esc(p["title"])}</span></div>')
        h.append(passage_html(p))
        if p["hint"]:
            h.append('<div class="instr">ターゲットごとに<b>個数を明かした状態</b>で手がかりを探す練習。本文に印をつけてから、表を埋めよう。</div>')
            counts = {k: len(v) for k, v in ann.items()}
            for key in ("vcb", "ref", "par", "abc", "clm", "mkr"):
                t = TKEY[key]
                stem, headers = QDEF[key]
                fill = fill_table(headers, counts[key])
                if key == "abc":
                    stem = stem + THINK_Q
                    fill = fill + ('<table class="fill"><tr><th style="width:9em">考える1問の答え</th>'
                                   '<td style="height:26px"></td></tr></table>')
                h.append(q_block(QNO[key], t["color"],
                                 f'{t["no"]} {t["name"]}（全 {counts[key]} 箇所）', stem, fill))
        else:
            total = sum(len(v) for v in ann.values())
            h.append(f'<div class="instr"><b>仕上げ: 個数ヒントなしの一括ハント。</b>6つの手がかりを自力で探し、'
                     f'本文に印(〇＋根拠・〇→・＝線・〇＋下線・◎・□→)をつけてから、下の集計表に「見つけた個数」を書け。'
                     f'<b>合計 {total} 箇所</b>ある。全部見つけるまで帰るな。</div>')
            rows = "".join(
                f'<tr><td class="nm" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}</td>'
                f'<td style="width:5.5em"></td><td></td></tr>'
                for t in C.TARGETS)
            h.append('<table class="fill"><tr><th>ターゲット</th><th>見つけた個数</th>'
                     '<th>文番号のメモ</th></tr>' + rows + "</table>")
        h.append(qset_questions(p["key"]))
    h.append(f'<div class="footnote">{esc(C.META["note"])}</div>')
    return "\n".join(h)


# ------------------------------------------------------------------ 解答解説編
CAT_COLS = {
    "vcb": (["文", "語", "意味のヒント（根拠・種類）", "推測した意味", "ひとこと"],
            lambda it: [it["t"], f'{it["clue"]}（{it["kind"]}）', it["guess"], it["note"]], {1}),
    "ref": (["文", "指示語", "指す中身", "ひとこと"],
            lambda it: [it["t"], it["refers"], it["note"]], {1}),
    "par": (["文", "言い換えの箇所", "＝ 何の言い換え", "ひとこと"],
            lambda it: [it["t"], it["equals"], it["note"]], set()),
    "abc": (["文", "抽象語", "具体の中身", "ひとこと"],
            lambda it: [it["t"], it["concrete"], it["note"]], {1}),
    "clm": (["文", "主張・評価の箇所", "型", "ひとこと"],
            lambda it: [it["t"], it["kind"], it["note"]], {1}),
    "mkr": (["文", "マーカー", "予測（次に来る内容）", "ひとこと"],
            lambda it: [it["t"], it["predict"], it["note"]], {1}),
}


def inv_tables(pkey):
    out = []
    for t in C.TARGETS:
        items = C.ANNOT[pkey][t["key"]]
        heads, rowf, nowrap = CAT_COLS[t["key"]]
        blk = [f'<div class="tgname" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}'
               f'<span class="cnt">全 {len(items)} 箇所</span>'
               f'<span class="gn">(全24ルール中の{t["gno"]})</span></div>']
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
        if pkey == "p1" and t["key"] == "abc":
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
        h.append(qset_answers(p["key"]))

    h.append('<div class="pb"></div><div class="secttl">ひっかけ注意報 — 「それっぽいのに違う」</div>')
    for tr in C.TRAPS:
        tname = TKEY[tr["target"]]["name"]
        h.append(f'<div class="trap"><b>【{esc(tname)}の運用】 {esc(tr["t"])}</b><br>{esc(tr["note"])}</div>')

    h.append('<div class="secttl">ミニ講義 — 6ターゲットの「使い方」総まとめ</div>')
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
