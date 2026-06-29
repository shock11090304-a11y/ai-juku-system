#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高校英文法 基礎定着問題集 (全20分野×25問) を1冊のPDFに組版する。

問題編 → 解答・解説編 の順。和欧混植は Arial Unicode 単一フォント。
ヘッダのセクション名は SectionMarker + 2パスビルドでページ毎に正しく出す。
"""
import json, os, glob, re, datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    Table, TableStyle, NextPageTemplate, Flowable,
)

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS_DIR = os.path.join(HERE, "units")
OUT_PATH = os.path.join(HERE, "高校英文法_基礎定着問題集_全20分野500問.pdf")

# ---- フォント登録 (Arial Unicode 単一、family登録でHelvetica落ち=豆腐を防止) ----
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FONT = "AU"
pdfmetrics.registerFont(TTFont(FONT, FONT_PATH))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT, italic=FONT, boldItalic=FONT)

# ---- 配色 ----
NAVY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#c8492e")
BLUE = colors.HexColor("#2a6db0")
GRAY = colors.HexColor("#8a8a8a")
RULE = colors.HexColor("#c9d4e0")
GOLD = colors.HexColor("#c8a24e")

def hx(c):
    return "#" + c.hexval()[2:]

CIRCLED = ["①", "②", "③", "④", "⑤"]
TYPE_LABEL = {"mc": "4択", "order": "整序", "rewrite": "書き換え"}
LEVEL_LABEL = {"basic": "基礎", "standard": "標準"}

UNIT_ORDER = [
    ("01_sentence-patterns.json", "文型"),
    ("02_tenses.json", "時制"),
    ("03_perfect.json", "完了形"),
    ("04_modals.json", "助動詞"),
    ("05_passive.json", "受動態"),
    ("06_infinitive.json", "不定詞"),
    ("07_gerund.json", "動名詞"),
    ("08_participle.json", "分詞"),
    ("09_participial-construction.json", "分詞構文"),
    ("10_comparison.json", "比較"),
    ("11_relatives.json", "関係詞"),
    ("12_subjunctive.json", "仮定法"),
    ("13_conjunctions.json", "接続詞"),
    ("14_prepositions.json", "前置詞"),
    ("15_nouns-articles.json", "名詞・冠詞"),
    ("16_pronouns.json", "代名詞"),
    ("17_adjectives-adverbs.json", "形容詞・副詞"),
    ("18_interrogatives.json", "疑問文"),
    ("19_negation-inversion.json", "否定・倒置・強調・省略"),
    ("20_reported-speech.json", "話法"),
]

# ---- テキスト整形 (豆腐/不可視文字対策) ----
_TRANS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "―": "-", "…": "...",
    "　": " ",
}
def clean(s):
    if s is None:
        return ""
    s = str(s)
    for k, v in _TRANS.items():
        s = s.replace(k, v)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    return s

def esc(s):
    s = clean(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---- スタイル ----
def styles():
    base = dict(fontName=FONT, leading=15, textColor=colors.HexColor("#1a1a1a"))
    S = {}
    S["title"] = ParagraphStyle("title", fontName=FONT, fontSize=26, leading=34, alignment=TA_CENTER, textColor=NAVY)
    S["subtitle"] = ParagraphStyle("subtitle", fontName=FONT, fontSize=13, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#444444"))
    S["cover_small"] = ParagraphStyle("cover_small", fontName=FONT, fontSize=10.5, leading=18, alignment=TA_CENTER, textColor=GRAY)
    S["sec_kicker"] = ParagraphStyle("sec_kicker", fontName=FONT, fontSize=10, leading=14, textColor=colors.white)
    S["sec_title"] = ParagraphStyle("sec_title", fontName=FONT, fontSize=17, leading=22, textColor=colors.white)
    S["part_title"] = ParagraphStyle("part_title", fontName=FONT, fontSize=22, leading=30, alignment=TA_CENTER, textColor=NAVY)
    S["toc"] = ParagraphStyle("toc", fontName=FONT, fontSize=11.5, leading=20, textColor=colors.HexColor("#222222"))
    S["q"] = ParagraphStyle("q", **base, fontSize=10.5, spaceBefore=4, spaceAfter=2, leftIndent=15, firstLineIndent=-15)
    S["sub"] = ParagraphStyle("sub", **base, fontSize=10.5, leftIndent=15, spaceAfter=2)
    S["a"] = ParagraphStyle("a", fontName=FONT, fontSize=10, leading=14.5, leftIndent=15, firstLineIndent=-15, spaceBefore=3, spaceAfter=1, textColor=colors.HexColor("#1a1a1a"))
    S["ab"] = ParagraphStyle("ab", fontName=FONT, fontSize=9.5, leading=14, leftIndent=22, spaceAfter=6, textColor=colors.HexColor("#333333"))
    S["grp"] = ParagraphStyle("grp", fontName=FONT, fontSize=11, leading=16, spaceBefore=4, spaceAfter=3)
    S["note"] = ParagraphStyle("note", fontName=FONT, fontSize=10.5, leading=16, textColor=colors.HexColor("#333333"))
    return S

S = {}

# ---- セクション追跡 (ページ毎の見出し) ----
PAGE_SECTIONS = {}   # page_no -> (part, unit)  ※2パス目のヘッダ描画で使用

class SectionMarker(Flowable):
    """描画はしないが、afterFlowable でページ→セクション対応を記録するためのマーカー。"""
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

def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    part, unit = PAGE_SECTIONS.get(doc.page, ("", ""))
    canvas.setFont(FONT, 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(18*mm, h-12*mm, "高校英文法 基礎定着問題集")
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

# ---- セクション見出し(帯) ----
def section_band(no, unit, kicker):
    data = [[Paragraph(f"<font size=10>{esc(kicker)}</font>　<font size=11>{no:02d}</font>", S["sec_kicker"])],
            [Paragraph(esc(unit), S["sec_title"])]]
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
    c = "#3a7d44" if level == "basic" else "#b06a1f"
    return f'<font size=8 color="{c}">[{esc(LEVEL_LABEL.get(level,""))}]</font>'

def type_tag(t):
    return f'<font size=8.5 color="{hx(ACCENT)}">〈{esc(TYPE_LABEL.get(t,t))}〉</font>'

def render_problem(q, flow):
    no = q["no"]; t = q["type"]
    head = f'<font color="{hx(NAVY)}">{no}.</font> {type_tag(t)} {lvl_tag(q.get("level"))} '
    if t == "mc":
        flow.append(Paragraph(head + esc(q["stem"]), S["q"]))
        parts = [f'{CIRCLED[i]} {esc(ch)}' for i, ch in enumerate(q.get("choices", []))]
        flow.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "&nbsp;&nbsp;&nbsp;".join(parts), S["sub"]))
    elif t == "order":
        flow.append(Paragraph(head + esc(q.get("prompt_ja","")), S["q"]))
        toks = " / ".join(esc(tk) for tk in q.get("tokens", []))
        flow.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;[ {toks} ]', S["sub"]))
    elif t == "rewrite":
        flow.append(Paragraph(head + esc(q.get("original","")), S["q"]))
        flow.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<font color="{hx(GRAY)}">（{esc(q.get("instruction",""))}）</font>', S["sub"]))

def render_answer(q, flow):
    no = q["no"]; t = q["type"]
    if t == "mc":
        idx = q.get("answer_index", 0)
        ans = f'{CIRCLED[idx]} {esc(q.get("answer_text",""))}'
    else:
        ans = esc(q.get("answer_text",""))
    head = f'<font color="{hx(NAVY)}">{no}.</font> <font color="{hx(ACCENT)}">{ans}</font>'
    flow.append(Paragraph(head, S["a"]))
    body = f'<font size=9.5 color="#333333">{esc(q.get("explanation",""))}</font>'
    point = esc(q.get("point",""))
    if point:
        body += f'<br/><font size=9 color="{hx(BLUE)}">▶ {point}</font>'
    flow.append(Paragraph(body, S["ab"]))

GROUP_LABEL = {
    "mc": "■ 四択問題（空所に入る記号を選べ）",
    "order": "■ 整序英作文（[ ]内を並べ替えよ）",
    "rewrite": "■ 書き換え（指示に従って書き換えよ）",
}

def by_type_then_no(qs):
    return sorted(qs, key=lambda q: ({"mc":0,"order":1,"rewrite":2}[q["type"]], q["no"]))

# ---- フロー構築 (2回呼べるよう毎回新規生成) ----
def build_flow(units, total_q):
    flow = []
    today = datetime.date.today().strftime("%Y年%m月")

    # 表紙 (タイトルは紺帯=上端72mmより下に出す)
    flow.append(Spacer(1, 64*mm))
    flow.append(Paragraph("高校英文法", S["title"]))
    flow.append(Paragraph("基礎定着問題集", S["title"]))
    flow.append(Spacer(1, 8*mm))
    flow.append(Paragraph("高校1年生～基礎を固めたい高校2年生向け", S["subtitle"]))
    flow.append(Spacer(1, 4*mm))
    flow.append(Paragraph(f"全{len(units)}分野 × 各25問（計{total_q}問）　·　四択／整序英作文／書き換え", S["subtitle"]))
    flow.append(Spacer(1, 30*mm))
    flow.append(Paragraph(today, S["cover_small"]))
    flow.append(Paragraph("AI塾", S["cover_small"]))
    flow.append(NextPageTemplate("normal"))
    flow.append(PageBreak())

    # 目次
    flow.append(SectionMarker("目次", ""))
    flow.append(Paragraph("目次", S["part_title"]))
    flow.append(Spacer(1, 6*mm))
    rows = []
    for i, (unit, qs) in enumerate(units, 1):
        c = {"mc":0,"order":0,"rewrite":0}
        for q in qs:
            c[q["type"]] += 1
        breakdown = f"4択{c['mc']}・整序{c['order']}・書換{c['rewrite']}"
        rows.append([Paragraph(f"<font color='{hx(NAVY)}'>{i:02d}</font>", S["toc"]),
                     Paragraph(esc(unit), S["toc"]),
                     Paragraph(f"<font size=9 color='{hx(GRAY)}'>{breakdown}</font>", S["toc"]),
                     Paragraph(f"<font size=9 color='{hx(GRAY)}'>{len(qs)}問</font>", S["toc"])])
    tt = Table(rows, colWidths=[12*mm, 92*mm, 50*mm, 20*mm])
    tt.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), FONT),
        ("LINEBELOW", (0,0), (-1,-1), 0.4, RULE),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (3,0), (3,-1), "RIGHT"),
    ]))
    flow.append(tt)
    flow.append(Spacer(1, 10*mm))
    a = hx(ACCENT)
    flow.append(Paragraph(
        "<font size=10 color='#444444'>【使い方】この問題集は「問題編」と「解答・解説編」に分かれています。"
        f"〈<font color='{a}'>4択</font>〉は空所に入る記号を選び、〈<font color='{a}'>整序</font>〉は [ ] 内の語句を並べ替えて英文を完成させ、"
        f"〈<font color='{a}'>書き換え</font>〉は指示に従って英文を書き換えます。各問に解説と ▶ ポイントがついています。</font>",
        S["note"]))

    # 問題編
    flow.append(PageBreak())
    flow.append(SectionMarker("問題編", ""))
    flow.append(Spacer(1, 60*mm))
    flow.append(Paragraph("問題編", S["part_title"]))
    flow.append(Spacer(1, 4*mm))
    flow.append(Paragraph(f"全{len(units)}分野　計{total_q}問", S["subtitle"]))
    for i, (unit, qs) in enumerate(units, 1):
        flow.append(PageBreak())
        flow.append(SectionMarker("問題編", unit))
        flow.append(section_band(i, unit, "問題"))
        flow.append(Spacer(1, 5*mm))
        cur = None
        for q in by_type_then_no(qs):
            if q["type"] != cur:
                cur = q["type"]
                flow.append(Spacer(1, 2*mm))
                flow.append(Paragraph(f"<font size=11 color='{hx(NAVY)}'>{GROUP_LABEL[cur]}</font>", S["grp"]))
            render_problem(q, flow)

    # 解答・解説編
    flow.append(PageBreak())
    flow.append(SectionMarker("解答・解説編", ""))
    flow.append(Spacer(1, 60*mm))
    flow.append(Paragraph("解答・解説編", S["part_title"]))
    for i, (unit, qs) in enumerate(units, 1):
        flow.append(PageBreak())
        flow.append(SectionMarker("解答・解説編", unit))
        flow.append(section_band(i, unit, "解答"))
        flow.append(Spacer(1, 5*mm))
        for q in by_type_then_no(qs):
            render_answer(q, flow)
    return flow

def make_doc():
    doc = Doc(OUT_PATH, pagesize=A4,
              leftMargin=18*mm, rightMargin=18*mm, topMargin=20*mm, bottomMargin=16*mm,
              title="高校英文法 基礎定着問題集", author="AI塾")
    fw = A4[0] - 36*mm
    fh = A4[1] - 36*mm
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[Frame(18*mm, 16*mm, fw, fh, id="cover")], onPage=on_cover),
        PageTemplate(id="normal", frames=[Frame(18*mm, 16*mm, fw, fh, id="main",
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=on_page),
    ])
    return doc

def main():
    global S
    S = styles()
    units = []
    for fname, unit in UNIT_ORDER:
        with open(os.path.join(UNITS_DIR, fname), encoding="utf-8") as f:
            d = json.load(f)
        units.append((unit, d["questions"]))
    total_q = sum(len(qs) for _, qs in units)

    # 1パス目: ページ→セクション対応を採取
    doc1 = make_doc()
    doc1.build(build_flow(units, total_q))
    last = ("", "")
    PAGE_SECTIONS.clear()
    for p in range(1, doc1.page + 1):
        if p in doc1.section_map:
            last = doc1.section_map[p]
        PAGE_SECTIONS[p] = last

    # 2パス目: 正しいヘッダで出力
    doc2 = make_doc()
    doc2.build(build_flow(units, total_q))
    print("WROTE", OUT_PATH, "| pages:", doc2.page, "| questions:", total_q)

if __name__ == "__main__":
    main()
