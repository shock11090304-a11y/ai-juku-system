# -*- coding: utf-8 -*-
"""古文［ルールで解く］完全版 — 解答解説編 ビルダー

問題編(WeasyPrint製)と同じ意匠(ネイビー#16243F・金#9A7C2E・Noto Sans/Serif JP)で
A4のHTMLを生成し、Chrome --headless --print-to-pdf でPDF化する。
ページ番号フッタは Chrome が CSS Paged Media のマージンボックスを解さないため、
生成後に PyMuPDF で全ページに刻印する(stamp.py)。

usage: python3 build.py <outdir>
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_ch1 import CH1
from content_ch2 import CH2
from content_ch3 import CH3
from content_ch4 import CH4

CHAPTERS = [CH1, CH2, CH3, CH4]

BOOK_TITLE = "古文［ルールで解く］完全版　—　解答解説編"
FOOTER = "Trillion English Academy　—　古文［ルールで解く］完全版 解答解説編"

# ---------------------------------------------------------------- inline 記法
# <b> 太字 / <u> 下線 / <k> 古文(明朝) / <r> 赤系の強調 / <n> ネイビー強調
_TAGS = {
    "b": ("<b>", "</b>"),
    "u": ("<u>", "</u>"),
    "k": ('<span class="k">', "</span>"),
    "r": ('<span class="hl">', "</span>"),
    "n": ('<span class="nv">', "</span>"),
}
_TAG_RE = re.compile(r"</?([bukrn])>")


def fmt(s):
    """許可タグだけ残して他をエスケープ。Markdownの ** は事故なので検出して落とす。"""
    if s is None:
        return ""
    s = str(s)
    if "**" in s:
        raise SystemExit("FATAL: Markdown '**' が本文に混入: " + s[:80])
    holes = []

    def _stash(m):
        holes.append(_TAGS[m.group(1)][0 if m.group(0)[1] != "/" else 1])
        return "\x00%d\x00" % (len(holes) - 1)

    s = _TAG_RE.sub(_stash, s)
    s = html.escape(s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: holes[int(m.group(1))], s)
    return s.replace("\n", "<br/>")


# ---------------------------------------------------------------- パーツ
def marks(ans):
    """'③' -> 丸数字バッジ"""
    return '<span class="ansbadge">%s</span>' % html.escape(ans)


def render_steps(steps):
    if not steps:
        return ""
    out = ['<div class="steps">']
    for i, (head, body) in enumerate(steps, 1):
        out.append(
            '<div class="step"><span class="stepno">%d</span>'
            '<span class="stephead">%s</span>'
            '<span class="stepbody">%s</span></div>' % (i, fmt(head), fmt(body))
        )
    out.append("</div>")
    return "".join(out)


def render_cut(cut):
    """選択肢を1つずつ潰す表。(番号, 正誤, 理由)"""
    if not cut:
        return ""
    rows = []
    for no, ok, why in cut:
        cls = "ok" if ok else "ng"
        sym = "○" if ok else "×"
        rows.append(
            '<tr class="%s"><td class="cno">%s</td><td class="csym">%s</td>'
            '<td class="cwhy">%s</td></tr>' % (cls, fmt(no), sym, fmt(why))
        )
    return (
        '<div class="cutwrap"><div class="cuthd">選択肢を一つずつ切る</div>'
        '<table class="cut">%s</table></div>' % "".join(rows)
    )


def render_q(q, kind="jissen"):
    """1設問ぶんのカード"""
    o = ['<div class="qcard %s">' % kind]
    o.append(
        '<div class="qhd"><span class="qno">%s</span>'
        '<span class="qtitle">%s</span>%s</div>'
        % (fmt(q["no"]), fmt(q.get("title", "")), marks(q["ans"]))
    )
    if q.get("stem"):
        o.append('<div class="stem">%s</div>' % fmt(q["stem"]))
    if q.get("eye"):
        o.append(
            '<div class="eye"><span class="eyelab">着眼</span>%s</div>' % fmt(q["eye"])
        )
    o.append(render_steps(q.get("steps")))
    if q.get("cut"):
        o.append(render_cut(q["cut"]))
    for lab, key, cls in (
        ("もう一歩", "plus", "plus"),
        ("ここに注意", "warn", "warn"),
        ("覚え方", "memo", "memo"),
    ):
        if q.get(key):
            o.append(
                '<div class="note %s"><span class="notelab">%s</span>'
                "<span>%s</span></div>" % (cls, lab, fmt(q[key]))
            )
    o.append("</div>")
    return "".join(o)


def render_kiso_block(b):
    # 見出し＋問題文＋最初の設問を一かたまりにして、見出しだけがページ末に取り残されるのを防ぐ
    o = ['<div class="kisoblock">', '<div class="kisolead">']
    o.append(
        '<div class="kisohd"><span class="kisono">%s</span>'
        '<span class="kisotitle">%s</span></div>' % (fmt(b["no"]), fmt(b["title"]))
    )
    o.append('<div class="kisoq"><span class="qlab">問題</span>%s</div>' % fmt(b["q"]))
    if b.get("src"):
        o.append('<div class="src">出典：%s</div>' % fmt(b["src"]))
    o.append("</div>")  # kisolead（見出し＋問題文）を閉じる
    for it in b["items"]:
        o.append(render_q(it, kind="kiso"))
    if b.get("wrap"):
        o.append(
            '<div class="note wrap"><span class="notelab">まとめ</span>'
            "<span>%s</span></div>" % fmt(b["wrap"])
        )
    o.append("</div>")
    return "".join(o)


def render_bunkai(rows):
    """品詞分解表。rows = [(語, 品詞・活用形, はたらき・意味)] / ('#', 見出し) で小見出し"""
    # thead にしておくと、表がページ境界で割れたときに Chrome が見出し行を刷り直す
    out = ['<table class="bunkai"><thead>']
    out.append(
        '<tr class="bhd"><th class="bw">語　句</th><th class="bp">品詞・活用形</th>'
        '<th class="bm">はたらき・意味</th></tr>'
    )
    out.append("</thead><tbody>")
    for r in rows:
        if r[0] == "#":
            out.append('<tr class="bsep"><td colspan="3">%s</td></tr>' % fmt(r[1]))
            continue
        w, p, m = r
        star = " starred" if w.startswith("★") else ""
        out.append(
            '<tr class="brow%s"><td class="bw k">%s</td><td class="bp">%s</td>'
            '<td class="bm">%s</td></tr>' % (star, fmt(w.lstrip("★")), fmt(p), fmt(m))
        )
    out.append("</tbody></table>")
    return "".join(out)


def render_passage(p):
    o = ['<div class="passage">']
    o.append(
        '<div class="pbar">実戦演習の本文を、まるごと品詞分解する　'
        '<span class="psrc">%s</span></div>' % fmt(p["src"])
    )
    if p.get("scene"):
        o.append(
            '<div class="scene"><span class="scenelab">場面</span>%s</div>'
            % fmt(p["scene"])
        )
    for sec in p["sections"]:
        o.append('<div class="psec">')
        o.append(
            '<div class="pline"><span class="plno">%s</span>'
            '<span class="ptext k">%s</span></div>' % (fmt(sec["no"]), fmt(sec["text"]))
        )
        o.append(render_bunkai(sec["rows"]))
        o.append(
            '<div class="yaku"><span class="yakulab">訳</span>%s</div>'
            % fmt(sec["yaku"])
        )
        if sec.get("point"):
            o.append(
                '<div class="note plus"><span class="notelab">ポイント</span>'
                "<span>%s</span></div>" % fmt(sec["point"])
            )
        o.append("</div>")
    if p.get("goi"):
        rows = "".join(
            '<tr><td class="gw k">%s</td><td class="gp">%s</td><td class="gm">%s</td></tr>'
            % (fmt(a), fmt(b), fmt(c))
            for a, b, c in p["goi"]
        )
        o.append(
            '<div class="goiwrap"><div class="goihd">この文章で押さえる重要古語</div>'
            '<table class="goi"><thead><tr class="bhd"><th>古　語</th><th>品詞</th>'
            "<th>意味（入試で問われる訳）</th></tr></thead><tbody>%s</tbody></table></div>" % rows
        )
    if p.get("zenyaku"):
        o.append(
            '<div class="zenyaku"><div class="zyhd">全文通釈</div><div class="zybody">%s</div></div>'
            % fmt(p["zenyaku"])
        )
    o.append("</div>")
    return "".join(o)


def render_anslist(ch):
    def cell(no, a):
        return '<td><span class="aln">%s</span><span class="ala">%s</span></td>' % (
            fmt(no),
            html.escape(a),
        )

    o = ['<div class="answrap">']
    for lab, pairs in (("STEP 2　基礎演習", ch["ans_kiso"]), ("STEP 3　実戦演習", ch["ans_jissen"])):
        if not pairs:
            continue
        o.append('<div class="anshd">%s</div>' % fmt(lab))
        o.append('<table class="anslist"><tr>')
        for i, (no, a) in enumerate(pairs):
            if i and i % 10 == 0:
                o.append("</tr><tr>")
            o.append(cell(no, a))
        o.append("</tr></table>")
    o.append("</div>")
    return "".join(o)


def render_chapter(ch):
    o = ['<section class="chapter">']
    o.append(
        '<div class="chhead"><div class="chno">第%d章</div>'
        '<div class="chtitle">%s</div><div class="chsub">%s</div></div>'
        % (ch["no"], fmt(ch["title"]), fmt(ch["sub"]))
    )
    o.append('<div class="chlead">%s</div>' % fmt(ch["lead"]))
    o.append(render_anslist(ch))
    if ch.get("kiso"):
        o.append('<div class="stepbar">STEP 2　基礎演習　—　一問ずつ、手順で解き直す</div>')
        for b in ch["kiso"]:
            o.append(render_kiso_block(b))
    if ch.get("passage"):
        o.append('<div class="stepbar">STEP 3　実戦演習　—　まず本文を完全に読む</div>')
        o.append(render_passage(ch["passage"]))
    if ch.get("jissen"):
        o.append('<div class="stepbar alt">STEP 3　実戦演習　—　設問の解説</div>')
        for q in ch["jissen"]:
            o.append(render_q(q, kind="jissen"))
    if ch.get("closing"):
        o.append(
            '<div class="closing"><div class="clhd">第%d章のまとめ</div>%s</div>'
            % (ch["no"], fmt(ch["closing"]))
        )
    o.append("</section>")
    return "".join(o)


# ---------------------------------------------------------------- 表紙・巻頭
def render_cover():
    rows = []
    for ch in CHAPTERS:
        rows.append(
            '<div class="tocrow"><span class="tocno">第%d章</span>'
            '<span class="toct">%s</span><span class="tocs">%s</span></div>'
            % (ch["no"], fmt(ch["title"]), fmt(ch["sub"]))
        )
    return """
<section class="cover">
  <div class="cvbrand">T r i l l i o n　E n g l i s h　A c a d e m y　<span>基礎核シリーズ</span></div>
  <div class="cvband">
    <div class="cvtitle">古文［ルールで解く］完全版</div>
    <div class="cvsub">解答解説編</div>
    <div class="cvtag">F O U N D A T I O N　→　R E A L</div>
  </div>
  <div class="cvlead">この冊子は「答え合わせ」のためのものではありません。<br/>
  <b>解けた問題も、解説を読んで“手順”を確認する</b>ところまでが一問です。<br/>
  すべての設問を、<n>①どこに目をつけるか　②どのルールを当てるか　③どう意味で確認するか</n>
  の三段階に分解して示しました。実戦演習の本文は<b>全文を品詞分解</b>し、訳と重要古語まで載せています。</div>
  <div class="cvhow">
    <div class="cvhowhd">この冊子の使い方</div>
    <div class="cvhowgrid">
      <div><span class="cvn">1</span><b>まず答え合わせ</b><br/>各章の冒頭に解答一覧があります。○×だけつけて、まだ解説は読まない。</div>
      <div><span class="cvn">2</span><b>間違えた問題は「手順」から</b><br/>答えを覚えるのではなく、<u>着眼→手順→選択肢を切る</u>の流れをなぞる。</div>
      <div><span class="cvn">3</span><b>正解した問題も「切り方」を確認</b><br/>他の四つを<u>なぜ切れるか</u>言えて初めて、その問題は自分のものです。</div>
      <div><span class="cvn">4</span><b>最後に本文をもう一度音読</b><br/>品詞分解を見ながら、本文を頭から訳せるようになるまで。ここで差がつきます。</div>
    </div>
  </div>
  <div class="cvtoc"><div class="cvtochd">目次</div>%s</div>
</section>
""" % "".join(rows)


CSS = """
@font-face{font-family:NSJP;src:url('NotoSansJP.ttf');font-weight:100 900;font-style:normal;}
@font-face{font-family:NMJP;src:url('NotoSerifJP.ttf');font-weight:100 900;font-style:normal;}
:root{
  --navy:#16243F; --navy2:#24365C; --gold:#9A7C2E; --goldl:#C2A14D;
  --ink:#20242C; --mute:#6C7382; --tan:#D9D3C4; --cream:#FBF9F3;
  --gray:#EEF0F4; --line:#D8DCE4; --red:#8E2F2F; --green:#2C5F46;
}
@page{ size:A4; margin:13mm 11mm 15mm 11mm; }
*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{font-family:NSJP,sans-serif; font-weight:400; color:var(--ink);
  font-size:8.5pt; line-height:1.62; -webkit-font-smoothing:antialiased;}
.k{font-family:NMJP,serif;}
b{font-weight:700;}
u{text-decoration:none; border-bottom:1.6px solid var(--goldl); padding-bottom:.5px;}
.nv{color:var(--navy); font-weight:700;}
.hl{color:var(--red); font-weight:700;}

/* ---------------- 表紙 ---------------- */
.cover{ page-break-after:always; }
.cvbrand{ font-size:7.6pt; font-weight:700; color:var(--navy); letter-spacing:.06em; }
.cvbrand span{ color:var(--gold); }
.cvband{ margin-top:7mm; background:var(--navy); color:#fff; padding:13mm 10mm 11mm; border-radius:2px;
  border-bottom:3.5px solid var(--goldl); }
.cvtitle{ font-size:23pt; font-weight:900; letter-spacing:.03em; }
.cvsub{ font-size:13pt; font-weight:900; color:var(--goldl); margin-top:3mm; letter-spacing:.28em; }
.cvtag{ font-size:7.4pt; font-weight:700; color:#CDD3DF; margin-top:6mm; letter-spacing:.12em; }
.cvlead{ margin-top:8mm; font-size:9pt; line-height:1.95; }
.cvhow{ margin-top:8mm; border:1px solid var(--tan); background:var(--cream); border-radius:2px; padding:5mm 6mm 6mm; }
.cvhowhd{ font-size:9.5pt; font-weight:900; color:var(--navy); margin-bottom:3mm;
  border-left:3.5px solid var(--goldl); padding-left:3mm; }
.cvhowgrid{ display:grid; grid-template-columns:1fr 1fr; gap:4mm 6mm; font-size:8.3pt; line-height:1.7; }
.cvn{ display:inline-block; width:5.2mm; height:5.2mm; line-height:5.2mm; text-align:center;
  background:var(--navy); color:#fff; font-weight:900; border-radius:50%; font-size:7pt; margin-right:2mm; }
.cvtoc{ margin-top:8mm; }
.cvtochd{ font-size:9.5pt; font-weight:900; color:var(--navy); border-bottom:2px solid var(--navy);
  padding-bottom:1.5mm; margin-bottom:3mm; }
.tocrow{ display:flex; align-items:baseline; gap:3mm; padding:2.2mm 1mm; border-bottom:1px dotted var(--line); }
.tocno{ font-weight:900; color:var(--gold); font-size:8.4pt; min-width:13mm; }
.toct{ font-weight:700; font-size:9pt; color:var(--navy); }
.tocs{ font-size:7.8pt; color:var(--mute); }

/* ---------------- 章 ---------------- */
.chapter{ page-break-before:always; }
.chhead{ background:var(--navy); color:#fff; padding:4.5mm 6mm; border-left:4px solid var(--goldl); }
.chno{ font-size:7.4pt; font-weight:900; color:var(--goldl); letter-spacing:.16em; }
.chtitle{ font-size:15pt; font-weight:900; margin-top:.6mm; letter-spacing:.02em; }
.chsub{ font-size:8pt; color:#CDD3DF; margin-top:1mm; }
.chlead{ font-size:8.4pt; line-height:1.8; margin:3.5mm 1mm 4mm; }

/* 解答一覧 */
.answrap{ border:1px solid var(--tan); background:var(--cream); border-radius:2px; padding:3.5mm 4mm 4mm; margin-bottom:5mm; }
.anshd{ font-size:8.2pt; font-weight:900; color:var(--navy); margin:1mm 0 2mm; }
table.anslist{ border-collapse:separate; border-spacing:1.4mm 1.2mm; width:100%; }
table.anslist td{ background:#fff; border:1px solid var(--line); border-radius:2px; text-align:center;
  padding:1.4mm .5mm; width:10%; }
.aln{ display:block; font-size:6.6pt; color:var(--mute); font-weight:700; line-height:1.2; }
.ala{ display:block; font-size:11pt; font-weight:900; color:var(--navy); line-height:1.25; }

.stepbar{ background:var(--navy2); color:#fff; font-size:8.6pt; font-weight:900; padding:2.4mm 4mm;
  margin:5mm 0 4mm; letter-spacing:.03em; border-radius:2px;
  break-after:avoid; page-break-after:avoid; }
.stepbar.alt{ background:var(--gold); }

/* ---------------- 基礎ブロック ---------------- */
/* overflow:hidden はページ分割時に中身を切り落とすので使わない */
.kisoblock{ margin-bottom:5mm; border:1px solid var(--line); border-radius:2px; }
.kisolead{ break-inside:avoid; page-break-inside:avoid; break-after:avoid; page-break-after:avoid; }
.kisohd{ background:var(--gray); padding:2mm 4mm; border-bottom:1px solid var(--line); }
.kisono{ font-weight:900; color:#fff; background:var(--navy); font-size:7.2pt; padding:.7mm 2.4mm;
  border-radius:2px; margin-right:2.5mm; }
.kisotitle{ font-weight:900; font-size:9pt; color:var(--navy); }
.kisoq{ padding:2.6mm 4mm; font-family:NMJP,serif; font-size:9.4pt; line-height:1.85; background:#fff; }
.qlab{ font-family:NSJP,sans-serif; font-size:6.8pt; font-weight:900; color:#fff; background:var(--gold);
  padding:.6mm 2mm; border-radius:2px; margin-right:2.5mm; vertical-align:.6mm; }
.src{ padding:0 4mm 2.4mm; font-size:7.2pt; color:var(--mute); text-align:right; }

/* ---------------- 設問カード ---------------- */
/* カードは 300〜450pt あるので atomic にすると1ページに1枚しか載らず紙が半分死ぬ。
   カード自体は分割を許し、内部の小さな単位(手順1行・選択肢1行・注記)だけを atomic にする。 */
.qcard{ padding:3mm 4mm 3.4mm; border-top:1px solid var(--line); }
.qcard.jissen{ border:1px solid var(--line); border-left:3.5px solid var(--navy); border-radius:2px;
  margin-bottom:4mm; background:#fff; }
.qhd{ display:flex; align-items:center; gap:2.5mm; margin-bottom:2mm;
  break-after:avoid; page-break-after:avoid; break-inside:avoid; page-break-inside:avoid; }
.qno{ font-weight:900; font-size:9.2pt; color:var(--navy); }
.qtitle{ font-weight:700; font-size:8.4pt; color:var(--gold); flex:1; }
.ansbadge{ font-weight:900; font-size:11pt; color:#fff; background:var(--navy);
  padding:.4mm 3mm; border-radius:2px; letter-spacing:.02em; white-space:nowrap; }
.stem{ font-family:NMJP,serif; font-size:9pt; background:var(--cream); border:1px solid var(--tan);
  border-radius:2px; padding:2mm 3mm; margin-bottom:2.2mm; line-height:1.8;
  break-inside:avoid; page-break-inside:avoid; break-after:avoid; page-break-after:avoid; }
.eye{ font-size:8.3pt; line-height:1.72; margin-bottom:2.2mm;
  break-inside:avoid; page-break-inside:avoid; }
.eyelab{ font-size:6.8pt; font-weight:900; color:#fff; background:var(--gold); padding:.6mm 2mm;
  border-radius:2px; margin-right:2.5mm; vertical-align:.5mm; }

.steps{ margin:0 0 2.4mm; }
.step{ display:flex; align-items:flex-start; gap:2.2mm; padding:1.5mm 2.6mm; background:var(--cream);
  border-left:2.5px solid var(--goldl); margin-bottom:1.2mm; font-size:8.2pt; line-height:1.68;
  break-inside:avoid; page-break-inside:avoid; }
.stepno{ flex:0 0 auto; width:4.4mm; height:4.4mm; line-height:4.4mm; text-align:center; border-radius:50%;
  background:var(--navy); color:#fff; font-weight:900; font-size:6.4pt; margin-top:.7mm; }
.stephead{ flex:0 0 auto; font-weight:900; color:var(--navy); margin-right:1mm; }
.stepbody{ flex:1; }

.cutwrap{ margin:2.4mm 0; }
.cuthd{ font-size:7.4pt; font-weight:900; color:var(--navy); margin-bottom:1.2mm; letter-spacing:.04em;
  break-after:avoid; page-break-after:avoid; }
table.cut{ width:100%; border-collapse:collapse; font-size:8pt; }
table.cut tr{ break-inside:avoid; page-break-inside:avoid; }
table.cut td{ border-top:1px solid var(--line); padding:1.5mm 2mm; vertical-align:top; line-height:1.62; }
table.cut tr:first-child td{ border-top:1px solid var(--tan); }
td.cno{ width:7mm; font-weight:900; color:var(--navy); text-align:center; }
td.csym{ width:6mm; text-align:center; font-weight:900; }
tr.ok td.csym{ color:#1F6B3B; }
tr.ng td.csym{ color:var(--red); }
tr.ok{ background:#F2F8F3; }

.note{ display:flex; gap:2.5mm; align-items:flex-start; font-size:8pt; line-height:1.68;
  padding:1.8mm 2.6mm; border-radius:2px; margin-top:1.8mm;
  break-inside:avoid; page-break-inside:avoid; }
.note.plus{ background:#F3F6FB; border-left:2.5px solid var(--navy2); }
.note.warn{ background:#FCF4F2; border-left:2.5px solid var(--red); }
.note.memo{ background:#FBF7E9; border-left:2.5px solid var(--goldl); }
.note.wrap{ background:var(--gray); border-left:2.5px solid var(--navy); margin:0 4mm 3mm; }
.notelab{ flex:0 0 auto; font-size:6.8pt; font-weight:900; color:#fff; background:var(--navy);
  padding:.6mm 2mm; border-radius:2px; margin-top:.5mm; white-space:nowrap; }
.note.warn .notelab{ background:var(--red); }
.note.memo .notelab{ background:var(--gold); }

/* ---------------- 本文・品詞分解 ---------------- */
.pbar{ background:var(--cream); border:1px solid var(--tan); border-left:3.5px solid var(--gold);
  padding:2.2mm 4mm; font-size:8.4pt; font-weight:900; color:var(--navy); border-radius:2px;
  break-after:avoid; page-break-after:avoid; overflow:hidden; }
.psrc{ float:right; font-size:7.6pt; color:var(--gold); font-weight:700; }
.scene{ font-size:8.2pt; line-height:1.72; margin:2.5mm 1mm 3.5mm; }
.scenelab{ font-size:6.8pt; font-weight:900; color:#fff; background:var(--navy2); padding:.6mm 2mm;
  border-radius:2px; margin-right:2.5mm; vertical-align:.5mm; }
/* 品詞分解も1セクション 200〜400pt あるので atomic にしない。
   行(tr)は割らず、文頭の帯と訳だけを離さない。 */
.psec{ margin-bottom:3.2mm; }
.pline{ display:flex; gap:2.5mm; align-items:baseline; background:var(--navy); color:#fff;
  padding:1.4mm 3mm; border-radius:2px 2px 0 0;
  break-inside:avoid; page-break-inside:avoid; break-after:avoid; page-break-after:avoid; }
.plno{ flex:0 0 auto; font-size:7pt; font-weight:900; color:var(--goldl); }
.ptext{ font-size:8.9pt; line-height:1.65; font-weight:600; }
table.bunkai{ width:100%; border-collapse:collapse; font-size:7.5pt; }
table.bunkai tr{ break-inside:avoid; page-break-inside:avoid; }
table.bunkai th{ background:var(--gray); color:var(--navy); font-size:6.6pt; font-weight:900;
  padding:.8mm 2mm; text-align:left; border:1px solid var(--line); }
table.bunkai td{ border:1px solid var(--line); padding:.85mm 2mm; vertical-align:top; line-height:1.42; }
td.bw{ width:21%; font-size:8.4pt; }
td.bp{ width:24%; font-size:7.2pt; color:var(--navy); font-weight:700; }
td.bm{ font-size:7.4pt; }
tr.brow.starred td{ background:#FBF7E9; }
tr.brow.starred td.bw{ font-weight:700; }
tr.bsep td{ background:var(--navy2); color:#fff; font-size:7.2pt; font-weight:900; padding:1.1mm 2mm; }
.yaku{ background:var(--cream); border:1px solid var(--tan); border-top:none; padding:1.6mm 3mm;
  font-size:8.2pt; line-height:1.7; border-radius:0 0 2px 2px;
  break-inside:avoid; page-break-inside:avoid; }
.yakulab{ font-size:6.8pt; font-weight:900; color:#fff; background:var(--gold); padding:.6mm 2.2mm;
  border-radius:2px; margin-right:2.5mm; vertical-align:.5mm; }

.goiwrap{ margin:4mm 0; }
.goihd{ font-size:8.6pt; font-weight:900; color:var(--navy); border-left:3.5px solid var(--goldl);
  padding-left:3mm; margin-bottom:2mm; break-after:avoid; page-break-after:avoid; }
table.goi{ width:100%; border-collapse:collapse; font-size:8pt; }
table.goi tr{ break-inside:avoid; page-break-inside:avoid; }
table.goi th{ background:var(--gray); color:var(--navy); font-size:6.9pt; font-weight:900;
  padding:1.1mm 2mm; text-align:left; border:1px solid var(--line); }
table.goi td{ border:1px solid var(--line); padding:1.25mm 2mm; vertical-align:top; line-height:1.55; }
td.gw{ width:18%; font-size:8.8pt; font-weight:600; }
td.gp{ width:14%; font-size:7.4pt; color:var(--navy); font-weight:700; }

.zenyaku{ margin:4mm 0 5mm; border:1px solid var(--navy); border-radius:2px; }
.zyhd{ background:var(--navy); color:#fff; font-size:8.4pt; font-weight:900; padding:2mm 4mm;
  break-after:avoid; page-break-after:avoid; }
.zybody{ padding:3mm 4mm; font-size:8.6pt; line-height:1.95; }

.closing{ margin-top:5mm; border:1px solid var(--tan); background:var(--cream); border-radius:2px;
  padding:3.5mm 4.5mm; font-size:8.3pt; line-height:1.78; page-break-inside:avoid; }
.clhd{ font-size:9pt; font-weight:900; color:var(--navy); margin-bottom:2mm;
  border-left:3.5px solid var(--goldl); padding-left:3mm; }
"""

# CSS の宣言部に非ASCII が紛れ込むと Chrome が黙って宣言を捨てるので機械で弾く
# (/* */ の中の日本語コメントは無害なので除外してから見る)
_bad = [c for c in re.sub(r"/\*.*?\*/", "", CSS, flags=re.S) if ord(c) > 0x7F]
if _bad:
    raise SystemExit("FATAL: CSS に非ASCII文字: %r" % sorted(set(_bad)))


def build_html():
    body = [render_cover()]
    for ch in CHAPTERS:
        body.append(render_chapter(ch))
    return (
        "<!doctype html><html lang='ja'><head><meta charset='utf-8'>"
        "<title>%s</title><style>%s</style></head><body>%s</body></html>"
        % (html.escape(BOOK_TITLE), CSS, "".join(body))
    )


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "kaisetsu.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_html())
    print("HTML:", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
