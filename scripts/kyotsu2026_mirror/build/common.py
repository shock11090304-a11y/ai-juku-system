#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト2026 そっくり類似問題PDF — 共通ビルド基盤。

方式: コンテンツJSON → HTML組版 → Chrome --print-to-pdf。
数式は LaTeX → MathML (latex2mathml) 変換で Chrome の MathML Core が描画する
(プロトタイプ proto_math.py で分数/√/Σ/∫/ベクトル/カタカナ解答欄ボックス全て検証済み)。

コンテンツJSONの block 型:
  {"t":"p","text":...}         地の文。$...$=LaTeX、〔ア〕=解答欄ボックス、<b><u><br><ruby>可
  {"t":"m","tex":...}          別行立て数式(インデント)
  {"t":"choices","for":"ア","items":[...],"cols":N}  ⓪①②…の解答群(itemsは$..$可)
  {"t":"q","no":3,"points":4,"stem":...,"choices":[...],"multi":false}
                               設問(マーク番号ボックス+①②③④選択肢)
  {"t":"fig","svg":...,"caption":...}   図(inline SVG)
  {"t":"table","head":[...],"rows":[[...]],"caption":...}
  {"t":"convo","turns":[{"sp":"太郎","text":...}]}   会話文
  {"t":"boxnote","title":...,"lines":[...]}          枠囲みメモ
  {"t":"html","html":...}      自由HTML(ポスター等・定義済みクラス使用)
  {"t":"pagebreak"}            強制改ページ
"""
import os, re, html as _html, subprocess

import latex2mathml.converter as l2m

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONTENT = os.path.join(ROOT, "content")
OUTDIR = os.path.expanduser("~/Desktop/共通テスト2026類似問題")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

KATAKANA = set("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヰヱヲン")
BOX_STYLE = "border:1.1px solid #222;padding:0.05em 0.3em;margin:0 0.07em;border-radius:1px;"
CIRCLED = "⓪①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"

_MI = re.compile(r"<mi>([^<]+)</mi>")
_TEX = re.compile(r"\$([^$]+)\$")
_SLOT = re.compile(r"〔([ア-ヲンa-zA-Z]+)〕")
_SLOT2 = re.compile(r"〚([ア-ヲンa-zA-Z]+)〛")  # 二重枠=選択式スロット

ALLOWED_TAGS = re.compile(r"&lt;(/?)(b|u|i|br|em|ruby|rt|rp|sub|sup|wbr|span class=\"[a-z0-9\- ]+\"|/span|span)&gt;")


def esc(s: str) -> str:
    return _html.escape(str(s), quote=False)


def esc_keep_tags(s: str) -> str:
    """エスケープしつつ許可タグ(b/u/i/br/ruby等)だけ復元する。"""
    e = _html.escape(str(s), quote=False)
    e = ALLOWED_TAGS.sub(lambda m: "<%s%s>" % (m.group(1), m.group(2)), e)
    return e


def box_slots_mathml(mathml: str) -> str:
    """MathML中のカタカナ<mi>を解答欄ボックス化(複数文字は1文字ずつ)。"""
    def rep(m):
        t = m.group(1)
        if t and all(ch in KATAKANA for ch in t):
            return "".join(
                f'<mi mathvariant="normal" style="{BOX_STYLE}">{ch}</mi>' for ch in t)
        return m.group(0)
    return _MI.sub(rep, mathml)


_SLOTBRK = str.maketrans("", "", "〔〕〚〛")


def tex2mathml(tex: str, display=False) -> str:
    # tex内の解答欄マーカー括弧 〔〕〚〛 はカタカナだけ残して除去する。
    # (latex2mathml は括弧をリテラル演算子として通すため、除去しないと箱+括弧の
    #  二重描画になる。カタカナは box_slots_mathml が枠囲みするので括弧は不要。)
    tex = tex.translate(_SLOTBRK)
    mm = l2m.convert(tex, display="block" if display else "inline")
    return box_slots_mathml(mm)


def slot_span(name: str, double=False) -> str:
    cls = "slot slot2" if double else "slot"
    return "".join(f'<span class="{cls}">{c}</span>' for c in name)


def rich(s: str) -> str:
    """地の文: エスケープ→許可タグ復元→$..$をMathML→〔ア〕をボックス化。"""
    s = str(s)
    parts = _TEX.split(s)  # odd indexes = tex
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            out.append(tex2mathml(p))
        else:
            e = esc_keep_tags(p)
            e = _SLOT.sub(lambda m: slot_span(m.group(1)), e)
            e = _SLOT2.sub(lambda m: slot_span(m.group(1), double=True), e)
            out.append(e)
    # スロット化されずに残った解答欄括弧(例 〔①〕 のように中身が非カタカナ)は
    # 括弧記号だけ除去して中身を残す(生の 〔〕〚〛 を紙面に出さない安全網)。
    return "".join(out).translate(_SLOTBRK_STRIP)


_SLOTBRK_STRIP = str.maketrans("", "", "〔〕〚〛")


def rich_or_svg(s: str) -> str:
    """選択肢や表セル: SVG/HTML片(<で始まる)はそのまま、他はrich()処理。"""
    t = str(s).lstrip()
    if t.startswith("<svg") or t.startswith("<div") or t.startswith("<img"):
        return s
    return rich(s)


def qbox(no) -> str:
    """設問のマーク番号ボックス(英語/国語形式: 解答番号は□囲みの数字)"""
    return f'<span class="qslot">{no}</span>'


# ---------------- block renderers (横書き共通) ----------------

def r_p(b):
    cls = b.get("cls", "")
    ind = ' style="text-indent:1em"' if b.get("indent") else ""
    return f'<p class="bp {cls}"{ind}>{rich(b["text"])}</p>'


def r_m(b):
    return f'<div class="dm">{tex2mathml(b["tex"], display=True)}</div>'


def r_choices(b):
    items = b["items"]
    cols = b.get("cols") or (4 if len(items) <= 4 else 3)
    lab = b.get("labels") or [CIRCLED[i] for i in range(len(items))]
    cells = "".join(
        f'<div class="chc"><span class="chlab">{lab[i]}</span><span class="chbody">{rich_or_svg(x)}</span></div>'
        for i, x in enumerate(items))
    intro = ""
    if b.get("for"):
        intro = (f'<div class="chintro">{slot_span(b["for"]) if all(c in KATAKANA for c in b["for"]) else rich(b["for"])}'
                 f'については，最も適当なものを，次の<b>⓪</b>〜<b>{CIRCLED[len(items)-1]}</b>のうちから一つ選べ。</div>'
                 if b.get("auto_intro") else f'<div class="chintro">{rich(b["for"])}</div>')
    # 実物準拠: テキスト解答群は罫線の長方形枠で囲む(見出し「○○の解答群」は枠の外・上)。
    # 列は等幅(minmax(0,1fr))で、長い選択肢は枠内で折り返す(auto だと枠からはみ出す)。
    return (f'{intro}<div class="ansgroup"><div class="choices" '
            f'style="grid-template-columns:repeat({cols},minmax(0,1fr))">{cells}</div></div>')


def r_q(b):
    pts = f'<span class="qpts">(各{b["points"]}点)' if b.get("points_each") else (
        f'<span class="qpts">({b["points"]}点)</span>' if b.get("points") else "")
    multi = b.get("multi")
    stem = rich(b["stem"])
    if "{Q}" in b["stem"]:
        stem = stem.replace("{Q}", qbox(b["no"]))
    else:
        stem += "　" + qbox(b["no"])
    ch = ""
    if b.get("choices"):
        lab = b.get("labels") or [CIRCLED[i + 1] for i in range(len(b["choices"]))]
        cols = b.get("cols", 1)
        ch = f'<div class="qchoices" style="grid-template-columns:repeat({cols},minmax(0,1fr))">' + "".join(
            f'<div class="qc"><span class="qclab">{lab[i]}</span><div class="qcbody">{rich_or_svg(c)}</div></div>'
            for i, c in enumerate(b["choices"])) + "</div>"
    # 実物準拠: 「問 N」を設問文と同じ行から続けて流す(見出しを別行に切り出さない)。
    qno = f'<span class="qno">問 {b["qlabel"]}</span>　' if b.get("qlabel") else ""
    return f'<div class="q"><div class="qstem">{qno}{stem}{pts}</div>{ch}</div>'


def r_fig(b):
    cap = f'<div class="figcap">{rich(b["caption"])}</div>' if b.get("caption") else ""
    w = f' style="width:{b["width_mm"]}mm"' if b.get("width_mm") else ""
    return f'<div class="fig"{w}>{b["svg"]}{cap}</div>'


def r_table(b):
    th = "".join(f"<th>{rich(h)}</th>" for h in b["head"]) if b.get("head") else ""
    thead = f"<thead><tr>{th}</tr></thead>" if th else ""
    rows = "".join("<tr>" + "".join(f"<td>{rich_or_svg(c)}</td>" for c in r) + "</tr>" for r in b["rows"])
    # 実物準拠: 表番号・表題(表N …)は表の【上】中央に置く(図は下)。
    cap = f'<div class="tblcap">{rich(b["caption"])}</div>' if b.get("caption") else ""
    cls = b.get("cls", "")
    return f'<div class="tblw {cls}">{cap}<table class="tbl">{thead}<tbody>{rows}</tbody></table></div>'


def r_convo(b):
    turns = "".join(
        f'<div class="turn"><span class="sp">{esc(t["sp"])}</span><span class="tx">{rich(t["text"])}</span></div>'
        for t in b["turns"])
    return f'<div class="convo">{turns}</div>'


def r_boxnote(b):
    title = f'<div class="bn-t">{rich(b["title"])}</div>' if b.get("title") else ""
    body = "".join(f'<p>{rich(x)}</p>' for x in b.get("lines", []))
    inner = body + "".join(render_block(x) for x in b.get("blocks", []))
    return f'<div class="boxnote">{title}{inner}</div>'


def r_html(b):
    return b["html"]


def r_group(b):
    """子ブロックを1つの keep-together 単位にまとめる(改ページで割らない)。"""
    return f'<div class="keepgroup">{render_blocks(b["blocks"])}</div>'


RENDERERS = {
    "p": r_p, "m": r_m, "choices": r_choices, "q": r_q, "fig": r_fig,
    "table": r_table, "convo": r_convo, "boxnote": r_boxnote, "html": r_html,
    "group": r_group,
    "pagebreak": lambda b: '<div class="pb"></div>',
    "vspace": lambda b: f'<div style="height:{b.get("mm",4)}mm"></div>',
}


def render_block(b):
    return RENDERERS[b["t"]](b)


def render_blocks(blocks):
    return "".join(render_block(b) for b in blocks)


# ---------------- ページ骨格 ----------------

BASE_CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; background:#fff; }
body { font-family:"Hiragino Mincho ProN","YuMincho",serif; color:#111;
       -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.pagewrap { width:210mm; padding:20mm 22mm 22mm; margin:0 auto; }
@media screen { body{background:#e9edf2;} .pagewrap{background:#fff; box-shadow:0 2px 12px rgba(0,0,0,.15); margin:12px auto;} }
math { font-size:1.06em; }
.dm math { math-style: normal; }
.gothic, .qno, .qpts, .sp, .bn-t, .chintro, .sec-h, .part-lab, .figcap, .slot, .qslot
 { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
.slot { display:inline-block; border:1.1px solid #222; padding:0 .32em; margin:0 .07em;
        font-size:.92em; border-radius:1px; line-height:1.5; }
.slot2 { border:3px double #222; }
.qslot { display:inline-block; border:1.2px solid #222; min-width:2.1em; text-align:center;
         padding:.02em .3em; margin:0 .15em; font-size:.95em; }
.sec-h { font-size:12.5pt; font-weight:700; margin:2mm 0 4mm; }
.sec-h .pts { font-weight:600; font-size:10.5pt; margin-left:.5em; }
.sec-h .pts + .pts { margin-left:0; }
.sec-wrap { break-before: page; }
.sec-wrap:first-child { break-before: auto; }
.part-lab { font-weight:700; margin:4mm 0 2mm; font-size:11pt; }
.bp { font-size:10.5pt; line-height:1.95; margin:1.6mm 0; }
.dm { margin:2.5mm 0 2.5mm 8mm; font-size:11pt; }
.choices { display:grid; gap:1.2mm 8mm; margin:2mm 0 3mm 6mm; font-size:10.5pt; justify-content:start; }
.chc { display:flex; gap:.55em; align-items:baseline; min-width:0; }
.chc .chbody { min-width:0; overflow-wrap:anywhere; }
.chlab { font-family:"Hiragino Kaku Gothic ProN",sans-serif; flex:0 0 auto; }
.chintro { font-size:10.2pt; margin:2.5mm 0 1mm; }
.ansgroup { border:1px solid #333; padding:1.8mm 3mm; margin:1.2mm 0 3mm; break-inside:avoid; }
.ansgroup .choices { margin:0; }
.q { margin:3.2mm 0; break-inside: avoid; }
.qno { font-weight:700; margin-right:.8em; }
.qstem { display:inline; font-size:10.5pt; line-height:1.95; }
.q > .qstem { display:block; }
.qchoices { display:grid; gap:1.1mm 7mm; margin:1.8mm 0 0 7mm; font-size:10.4pt; }
.qc { display:flex; gap:.5em; align-items:baseline; break-inside:avoid; }
.qclab { font-family:"Hiragino Kaku Gothic ProN",sans-serif; flex:0 0 auto; }
.qcbody { line-height:1.8; }
.fig { margin:3mm auto; text-align:center; break-inside:avoid; }
.fig svg { max-width:100%; }
.figcap { font-size:9pt; color:#333; margin-top:1mm; text-align:center; }
.tblcap { font-size:9pt; color:#333; margin-bottom:1.2mm; text-align:center;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.tblw { margin:3mm auto; break-inside:avoid; text-align:center; }
table.tbl { border-collapse:collapse; margin:0 auto; font-size:9.8pt; }
table.tbl th, table.tbl td { border:1px solid #333; padding:1.2mm 3mm; text-align:center; }
table.tbl th { background:#f2f2f2; font-weight:600;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.convo { margin:2.5mm 0 2.5mm 2mm; }
.turn { display:flex; gap:1em; margin:1mm 0; font-size:10.4pt; line-height:1.9; }
.sp { flex:0 0 3.5em; font-weight:600; }
.boxnote { border:1.3px solid #222; padding:3mm 4mm; margin:3mm 2mm; break-inside:avoid; font-size:10.2pt; line-height:1.9; }
.boxnote p { margin:.6mm 0; }
.bn-t { font-weight:700; margin-bottom:1.5mm; }
.pb { break-after: page; }
.keepgroup { break-inside: avoid; }
.pageno { text-align:center; font-size:9pt; color:#555; margin-top:6mm;
  font-family:sans-serif; }
"""


def chrome_pdf(html_path: str, pdf_path: str, budget=8000):
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", f"--virtual-time-budget={budget}",
           f"--print-to-pdf={pdf_path}", "file://" + html_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(pdf_path):
        raise SystemExit(f"PDF生成失敗: {pdf_path}\n{r.stdout}\n{r.stderr}")
    print("WROTE", pdf_path, os.path.getsize(pdf_path), "bytes")


def wrap_doc(title: str, body: str, extra_css: str = "") -> str:
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{esc(title)}</title><style>{BASE_CSS}{extra_css}</style></head>'
            f'<body><div class="pagewrap">{body}</div></body></html>')


def ensure_outdir():
    os.makedirs(OUTDIR, exist_ok=True)
    return OUTDIR
