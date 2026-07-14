#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学 問題演習テキスト (数IA / 数IIB) を1冊のPDFに組版する。

  python3 build_math.py ia   → 数学IA
  python3 build_math.py iib  → 数学IIB

問題編 → 解答・解説編。和欧混植は Arial Unicode 単一フォント。
数式は content 側の軽量記法 (^{...} _{...}) を <super>/<sub> に変換して描画。
ヘッダのセクション名は SectionMarker + 2パスビルドでページ毎に正しく出す。
"""
import sys, os, re, datetime, importlib

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    Table, TableStyle, NextPageTemplate, Flowable, KeepTogether,
)

HERE = os.path.dirname(os.path.abspath(__file__))

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"
FONT = "AU"
pdfmetrics.registerFont(TTFont(FONT, FONT_PATH))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT, italic=FONT, boldItalic=FONT)

NAVY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#c8492e")
BLUE = colors.HexColor("#2a6db0")
GREEN = colors.HexColor("#3a7d44")
GRAY = colors.HexColor("#8a8a8a")
RULE = colors.HexColor("#c9d4e0")
GOLD = colors.HexColor("#c8a24e")

def hx(c):
    return "#" + c.hexval()[2:]

CIRCLED = ["①", "②", "③", "④", "⑤"]
LEVEL_LABEL = {"basic": "基礎", "standard": "標準", "advanced": "発展"}

# ---- テキスト整形 + 数式記法変換 ----
_TRANS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "―": "-", "…": "...",
    "　": " ",  # 全角スペース→半角(reportlabのCJK折返しで潰れないよう)
}

def _clean(s):
    if s is None:
        return ""
    s = str(s)
    for k, v in _TRANS.items():
        s = s.replace(k, v)
    # 制御文字除去 (NUL/豆腐対策)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    return s

def M(s):
    """数式軽量記法を reportlab マークアップへ。
    まず HTML特殊文字をエスケープ → ^{..}/_{..}/^x/_x を super/sub に変換。"""
    s = _clean(s)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # ^{...} , _{...}
    s = re.sub(r"\^\{([^{}]*)\}", r"<super>\1</super>", s)
    s = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", s)
    # ^x , _x  (1文字。英数字・+ - のみ対象)
    s = re.sub(r"\^([A-Za-z0-9+\-])", r"<super>\1</super>", s)
    s = re.sub(r"_([A-Za-z0-9+\-])", r"<sub>\1</sub>", s)
    return s

# ---- スタイル ----
def styles():
    base = dict(fontName=FONT, textColor=colors.HexColor("#1a1a1a"))
    S = {}
    S["title"] = ParagraphStyle("title", fontName=FONT, fontSize=26, leading=34, alignment=TA_CENTER, textColor=NAVY)
    S["subtitle"] = ParagraphStyle("subtitle", fontName=FONT, fontSize=13, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#444444"))
    S["cover_small"] = ParagraphStyle("cover_small", fontName=FONT, fontSize=10.5, leading=18, alignment=TA_CENTER, textColor=GRAY)
    S["sec_kicker"] = ParagraphStyle("sec_kicker", fontName=FONT, fontSize=10, leading=14, textColor=colors.white)
    S["sec_title"] = ParagraphStyle("sec_title", fontName=FONT, fontSize=16, leading=21, textColor=colors.white)
    S["part_title"] = ParagraphStyle("part_title", fontName=FONT, fontSize=22, leading=30, alignment=TA_CENTER, textColor=NAVY)
    S["toc"] = ParagraphStyle("toc", fontName=FONT, fontSize=11.5, leading=20, textColor=colors.HexColor("#222222"))
    S["q"] = ParagraphStyle("q", **base, fontSize=10.5, leading=16, spaceBefore=4, spaceAfter=2, leftIndent=16, firstLineIndent=-16, wordWrap="CJK")
    S["sub"] = ParagraphStyle("sub", **base, fontSize=10.5, leading=16, leftIndent=16, spaceAfter=2, wordWrap="CJK")
    S["a"] = ParagraphStyle("a", fontName=FONT, fontSize=10, leading=15, leftIndent=16, firstLineIndent=-16, spaceBefore=3, spaceAfter=1, textColor=colors.HexColor("#1a1a1a"), wordWrap="CJK")
    S["ab"] = ParagraphStyle("ab", fontName=FONT, fontSize=9.5, leading=14.5, leftIndent=16, spaceAfter=6, textColor=colors.HexColor("#333333"), wordWrap="CJK")
    S["grp"] = ParagraphStyle("grp", fontName=FONT, fontSize=11, leading=16, spaceBefore=6, spaceAfter=3)
    S["note"] = ParagraphStyle("note", fontName=FONT, fontSize=10.5, leading=16, textColor=colors.HexColor("#333333"), wordWrap="CJK")
    return S

S = {}
PAGE_SECTIONS = {}

class SectionMarker(Flowable):
    def __init__(self, part, unit):
        super().__init__()
        self.part, self.unit = part, unit
        self.width = self.height = 0
    def draw(self):
        pass

class Doc(BaseDocTemplate):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.section_map = {}
    def afterFlowable(self, flowable):
        if isinstance(flowable, SectionMarker):
            self.section_map[self.page] = (flowable.part, flowable.unit)

BOOK_TITLE = ""

def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    part, unit = PAGE_SECTIONS.get(doc.page, ("", ""))
    canvas.setFont(FONT, 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(18*mm, h-12*mm, BOOK_TITLE)
    right = f"{part} · {unit}" if unit else part
    if right:
        canvas.drawRightString(w-18*mm, h-12*mm, right)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(18*mm, h-14*mm, w-18*mm, h-14*mm)
    canvas.setFont(FONT, 9)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(w/2, 10*mm, str(doc.page))
    canvas.restoreState()

def on_cover(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h-70*mm, w, 70*mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h-72*mm, w, 2*mm, fill=1, stroke=0)
    canvas.restoreState()

def section_band(no, unit, kicker):
    data = [[Paragraph(f"<font size=10>{_clean(kicker)}</font>　<font size=11>{no:02d}</font>", S["sec_kicker"])],
            [Paragraph(_clean(unit), S["sec_title"])]]
    t = Table(data, colWidths=[174*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (0,0), 8),
        ("BOTTOMPADDING", (0,0), (0,0), 0),
        ("TOPPADDING", (0,1), (0,1), 0),
        ("BOTTOMPADDING", (0,1), (0,1), 10),
    ]))
    return t

def lvl_tag(level):
    color = {"basic": "#3a7d44", "standard": "#b06a1f", "advanced": "#a03030"}.get(level, "#3a7d44")
    lab = LEVEL_LABEL.get(level, "")
    return f'<font size=8 color="{color}">[{lab}]</font>' if lab else ""

def render_problem(q, flow):
    no = q["no"]
    head = f'<font color="{hx(NAVY)}">{no}.</font> {lvl_tag(q.get("level"))} '
    blk = [Paragraph(head + M(q["stem"]), S["q"])]
    if q.get("type", "short") == "mc":
        parts = [f'{CIRCLED[i]} {M(ch)}' for i, ch in enumerate(q.get("choices", []))]
        blk.append(Paragraph("&nbsp;&nbsp;&nbsp;" + "&nbsp;&nbsp;&nbsp;".join(parts), S["sub"]))
    flow.append(KeepTogether(blk))

def render_answer(q, flow):
    no = q["no"]
    if q.get("type", "short") == "mc":
        idx = q.get("answer_index", 0)
        ans = f'{CIRCLED[idx]}　{M(q.get("answer",""))}'
    else:
        ans = M(q.get("answer", ""))
    head = f'<font color="{hx(NAVY)}">{no}.</font> <font color="{hx(ACCENT)}">{ans}</font>'
    body_txt = M(q.get("explanation", ""))
    blk = [Paragraph(head, S["a"]),
           Paragraph(f'<font size=9.5 color="#333333">{body_txt}</font>', S["ab"])]
    flow.append(KeepTogether(blk))

def build_flow(cfg, units, total_q):
    flow = []
    today = datetime.date.today().strftime("%Y年%m月")

    # 表紙
    flow.append(Spacer(1, 60*mm))
    flow.append(Paragraph(cfg["title"], S["title"]))
    flow.append(Spacer(1, 4*mm))
    flow.append(Paragraph(cfg["subtitle"], S["title2"] if "title2" in S else S["subtitle"]))
    flow.append(Spacer(1, 8*mm))
    flow.append(Paragraph(cfg["tagline"], S["subtitle"]))
    flow.append(Spacer(1, 4*mm))
    flow.append(Paragraph(f"全{len(units)}分野　計{total_q}問　·　1問1答式（問題編／解答・解説編）", S["subtitle"]))
    flow.append(Spacer(1, 28*mm))
    flow.append(Paragraph(today, S["cover_small"]))
    flow.append(Paragraph("トリリオン AI塾", S["cover_small"]))
    flow.append(NextPageTemplate("normal"))
    flow.append(PageBreak())

    # 目次
    flow.append(SectionMarker("目次", ""))
    flow.append(Paragraph("目次", S["part_title"]))
    flow.append(Spacer(1, 6*mm))
    rows = []
    for i, u in enumerate(units, 1):
        rows.append([Paragraph(f"<font color='{hx(NAVY)}'>{i:02d}</font>", S["toc"]),
                     Paragraph(_clean(u["name"]), S["toc"]),
                     Paragraph(f"<font size=9 color='{hx(GRAY)}'>{_clean(u.get('tag',''))}</font>", S["toc"]),
                     Paragraph(f"<font size=9 color='{hx(GRAY)}'>{len(u['problems'])}問</font>", S["toc"])])
    tt = Table(rows, colWidths=[12*mm, 80*mm, 62*mm, 20*mm])
    tt.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), FONT),
        ("LINEBELOW", (0,0), (-1,-1), 0.4, RULE),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (3,0), (3,-1), "RIGHT"),
    ]))
    flow.append(tt)
    flow.append(Spacer(1, 8*mm))
    flow.append(Paragraph(cfg["howto"], S["note"]))

    # 問題編
    flow.append(PageBreak())
    flow.append(SectionMarker("問題編", ""))
    flow.append(Spacer(1, 60*mm))
    flow.append(Paragraph("問題編", S["part_title"]))
    flow.append(Spacer(1, 4*mm))
    flow.append(Paragraph(f"全{len(units)}分野　計{total_q}問", S["subtitle"]))
    for i, u in enumerate(units, 1):
        flow.append(PageBreak())
        flow.append(SectionMarker("問題編", u["name"]))
        flow.append(section_band(i, u["name"], "問題"))
        flow.append(Spacer(1, 4*mm))
        cur = None
        for q in u["problems"]:
            g = q.get("group", "")
            if g != cur:
                cur = g
                flow.append(Paragraph(f"<font size=11 color='{hx(NAVY)}'>■ {_clean(g)}</font>", S["grp"]))
            render_problem(q, flow)

    # 解答・解説編
    flow.append(PageBreak())
    flow.append(SectionMarker("解答・解説編", ""))
    flow.append(Spacer(1, 60*mm))
    flow.append(Paragraph("解答・解説編", S["part_title"]))
    for i, u in enumerate(units, 1):
        flow.append(PageBreak())
        flow.append(SectionMarker("解答・解説編", u["name"]))
        flow.append(section_band(i, u["name"], "解答"))
        flow.append(Spacer(1, 4*mm))
        cur = None
        for q in u["problems"]:
            g = q.get("group", "")
            if g != cur:
                cur = g
                flow.append(Paragraph(f"<font size=10.5 color='{hx(NAVY)}'>■ {_clean(g)}</font>", S["grp"]))
            render_answer(q, flow)
    return flow

def make_doc(out_path, title):
    doc = Doc(out_path, pagesize=A4,
              leftMargin=18*mm, rightMargin=18*mm, topMargin=20*mm, bottomMargin=16*mm,
              title=title, author="トリリオン AI塾")
    fw = A4[0] - 36*mm
    fh = A4[1] - 36*mm
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[Frame(18*mm, 16*mm, fw, fh, id="cover")], onPage=on_cover),
        PageTemplate(id="normal", frames=[Frame(18*mm, 16*mm, fw, fh, id="main",
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=on_page),
    ])
    return doc

CONFIGS = {
    "ia": dict(
        module="content_ia", title="数学 I · A", subtitle="問題演習テキスト",
        tagline="高校2年 / 苦手克服・基礎〜標準の総点検",
        out="数学IA_問題演習テキスト.pdf",
        howto=("<font size=10 color='#444444'>【使い方】この問題集は「問題編」と「解答・解説編」に分かれています。"
               "各分野の問題を解いたら、必ず解答・解説編で答え合わせをしてください。指数は x² のように、"
               "根号は √3 のように表記しています。まず全問を自力で解き、間違えた問題に印をつけて"
               "解き直すと、苦手が確実に埋まります。</font>"),
    ),
    "iib": dict(
        module="content_iib", title="数学 II · B", subtitle="問題演習テキスト",
        tagline="高校2年 / 苦手克服・基礎〜標準の総点検",
        out="数学IIB_問題演習テキスト.pdf",
        howto=("<font size=10 color='#444444'>【使い方】この問題集は「問題編」と「解答・解説編」に分かれています。"
               "各分野の問題を解いたら、必ず解答・解説編で答え合わせをしてください。指数は x² のように、"
               "根号は √3、対数は log_2 8 のように表記しています。ベクトルは a→, AB→ のように矢印を後置します。"
               "まず全問を自力で解き、間違えた問題を解き直すと苦手が埋まります。</font>"),
    ),
}

def main():
    global S, BOOK_TITLE
    which = sys.argv[1] if len(sys.argv) > 1 else "ia"
    cfg = CONFIGS[which]
    S = styles()
    mod = importlib.import_module(cfg["module"])
    units = mod.UNITS
    # 連番 no を全体通しで振り直し(ユニットごとに1始まり)
    for u in units:
        for j, q in enumerate(u["problems"], 1):
            q["no"] = j
    total_q = sum(len(u["problems"]) for u in units)
    BOOK_TITLE = f'{cfg["title"]}　問題演習テキスト'
    out_path = os.path.join(HERE, cfg["out"])

    doc1 = make_doc(out_path, cfg["title"])
    doc1.build(build_flow(cfg, units, total_q))
    last = ("", "")
    PAGE_SECTIONS.clear()
    for p in range(1, doc1.page + 1):
        if p in doc1.section_map:
            last = doc1.section_map[p]
        PAGE_SECTIONS[p] = last

    doc2 = make_doc(out_path, cfg["title"])
    doc2.build(build_flow(cfg, units, total_q))
    print("WROTE", out_path, "| pages:", doc2.page, "| units:", len(units), "| questions:", total_q)

if __name__ == "__main__":
    main()
