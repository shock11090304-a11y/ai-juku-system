#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高校英文法レベル1 標準演習 (偏差値55-60) を1冊のPDFに組版する。

    python3 scripts/grammar_lv1_standard/build_pdf.py

問題編 → 解答・解説編。構成は scripts/grammar_workbook/build_pdf.py を踏襲する
(同じクラスで2冊並べて使うので、見た目が違うと生徒が混乱する)。

★フォントの探し方だけ変えてある。grammar_workbook 側は macOS の
  /System/Library/Fonts/Supplemental/Arial Unicode.ttf を直書きしていて、
  Mac 以外では import した瞬間に落ちる。ここは候補を順に探し、
  **どれを使ったかを必ず印字する**(黙って別のフォントに落ちると、
  和文が豆腐になった紙が出てから気づくことになる)。
"""
import datetime
import json
import os
import re
import sys

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
OUT_PATH = os.path.join(HERE, "高校英文法レベル1_標準演習_仮定法不定詞動名詞時制_120問.pdf")

# ---- フォント登録 ----
# 和欧混植を1書体でまかなう。候補は「和文グリフを持つこと」が条件。
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",          # macOS (塾長の手元)
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",           # Debian/Ubuntu
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",            # IPA Pゴシック
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",             # IPAゴシック
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
FONT = "JP"


def register_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(FONT, path))
            pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT,
                                          italic=FONT, boldItalic=FONT)
            print(f"font: {path}")
            return path
    print("✗ 和文フォントが見つからない。候補:\n  " + "\n  ".join(FONT_CANDIDATES),
          file=sys.stderr)
    sys.exit(1)


# ---- 配色 (grammar_workbook と同じ) ----
NAVY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#c8492e")
BLUE = colors.HexColor("#2a6db0")
GRAY = colors.HexColor("#8a8a8a")
RULE = colors.HexColor("#c9d4e0")
GOLD = colors.HexColor("#c8a24e")


def hx(c):
    return "#" + c.hexval()[2:]


CIRCLED = ["①", "②", "③", "④", "⑤"]
TYPE_LABEL = {"mc": "4択", "order": "整序", "rewrite": "書換"}
LEVEL_LABEL = {"standard": "標準", "advanced": "発展"}

UNIT_ORDER = [
    ("01_tenses.json", "時制"),
    ("02_infinitive.json", "不定詞"),
    ("03_gerund.json", "動名詞"),
    ("04_subjunctive.json", "仮定法"),
]

BOOK_TITLE = "高校英文法レベル1 標準演習"

# ---- テキスト整形 (豆腐/不可視文字対策) ----
_TRANS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "―": "-", "…": "...",
    "　": " ", " ": " ", " ": " ",
}


def clean(s):
    if s is None:
        return ""
    s = str(s)
    for k, v in _TRANS.items():
        s = s.replace(k, v)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)


def esc(s):
    return clean(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def styles():
    base = dict(fontName=FONT, leading=15, textColor=colors.HexColor("#1a1a1a"))
    S = {}
    S["title"] = ParagraphStyle("title", fontName=FONT, fontSize=25, leading=33,
                                alignment=TA_CENTER, textColor=NAVY)
    S["subtitle"] = ParagraphStyle("subtitle", fontName=FONT, fontSize=13, leading=20,
                                   alignment=TA_CENTER, textColor=colors.HexColor("#444444"))
    S["cover_small"] = ParagraphStyle("cover_small", fontName=FONT, fontSize=10.5, leading=18,
                                      alignment=TA_CENTER, textColor=GRAY)
    S["sec_kicker"] = ParagraphStyle("sec_kicker", fontName=FONT, fontSize=10, leading=14,
                                     textColor=colors.white)
    S["sec_title"] = ParagraphStyle("sec_title", fontName=FONT, fontSize=17, leading=22,
                                    textColor=colors.white)
    S["part_title"] = ParagraphStyle("part_title", fontName=FONT, fontSize=22, leading=30,
                                     alignment=TA_CENTER, textColor=NAVY)
    S["toc"] = ParagraphStyle("toc", fontName=FONT, fontSize=11.5, leading=20,
                              textColor=colors.HexColor("#222222"))
    S["q"] = ParagraphStyle("q", **base, fontSize=10.5, spaceBefore=4, spaceAfter=2,
                            leftIndent=15, firstLineIndent=-15)
    S["sub"] = ParagraphStyle("sub", **base, fontSize=10.5, leftIndent=15, spaceAfter=2)
    S["a"] = ParagraphStyle("a", fontName=FONT, fontSize=10, leading=14.5, leftIndent=15,
                            firstLineIndent=-15, spaceBefore=3, spaceAfter=1,
                            textColor=colors.HexColor("#1a1a1a"))
    S["ab"] = ParagraphStyle("ab", fontName=FONT, fontSize=9.5, leading=14, leftIndent=22,
                             spaceAfter=6, textColor=colors.HexColor("#333333"))
    S["grp"] = ParagraphStyle("grp", fontName=FONT, fontSize=11, leading=16,
                              spaceBefore=4, spaceAfter=3)
    S["note"] = ParagraphStyle("note", fontName=FONT, fontSize=10, leading=16,
                               textColor=colors.HexColor("#333333"))
    return S


S = {}
PAGE_SECTIONS = {}


class SectionMarker(Flowable):
    """描画しない。afterFlowable でページ→セクション対応を採るためだけの目印。"""

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
    canvas.drawString(18 * mm, h - 12 * mm, BOOK_TITLE)
    right = f"{part} · {unit}" if unit else part
    if right:
        canvas.drawRightString(w - 18 * mm, h - 12 * mm, right)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, h - 14 * mm, w - 18 * mm, h - 14 * mm)
    canvas.setFont(FONT, 9)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(w / 2, 10 * mm, str(doc.page))
    canvas.restoreState()


def on_cover(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 70 * mm, w, 70 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 72 * mm, w, 2 * mm, fill=1, stroke=0)
    canvas.restoreState()


def section_band(no, unit, kicker):
    data = [[Paragraph(f"<font size=10>{esc(kicker)}</font>　<font size=11>{no:02d}</font>",
                       S["sec_kicker"])],
            [Paragraph(esc(unit), S["sec_title"])]]
    t = Table(data, colWidths=[174 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (0, 0), 8),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 10),
    ]))
    return t


def lvl_tag(level):
    c = "#3a7d44" if level == "standard" else "#b06a1f"
    return f'<font size=8 color="{c}">[{esc(LEVEL_LABEL.get(level, ""))}]</font>'


def type_tag(t):
    return f'<font size=8.5 color="{hx(ACCENT)}">〈{esc(TYPE_LABEL.get(t, t))}〉</font>'


def render_problem(q, flow):
    no = q["no"]
    t = q["type"]
    head = f'<font color="{hx(NAVY)}">{no}.</font> {type_tag(t)} {lvl_tag(q.get("level"))} '
    if t == "mc":
        flow.append(Paragraph(head + esc(q["stem"]), S["q"]))
        parts = [f'{CIRCLED[i]} {esc(ch)}' for i, ch in enumerate(q.get("choices", []))]
        flow.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "&nbsp;&nbsp;&nbsp;".join(parts),
                              S["sub"]))
    elif t == "order":
        flow.append(Paragraph(head + esc(q.get("prompt_ja", "")), S["q"]))
        toks = " / ".join(esc(tk) for tk in q.get("tokens", []))
        flow.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;[ {toks} ]', S["sub"]))
    elif t == "rewrite":
        flow.append(Paragraph(head + esc(q.get("original", "")), S["q"]))
        flow.append(Paragraph(
            f'&nbsp;&nbsp;&nbsp;&nbsp;<font color="{hx(GRAY)}">'
            f'（{esc(q.get("instruction", ""))}）</font>', S["sub"]))


def render_answer(q, flow):
    no = q["no"]
    if q["type"] == "mc":
        idx = q.get("answer_index", 0)
        ans = f'{CIRCLED[idx]} {esc(q.get("answer_text", ""))}'
    else:
        ans = esc(q.get("answer_text", ""))
    flow.append(Paragraph(
        f'<font color="{hx(NAVY)}">{no}.</font> <font color="{hx(ACCENT)}">{ans}</font>', S["a"]))
    body = f'<font size=9.5 color="#333333">{esc(q.get("explanation", ""))}</font>'
    point = esc(q.get("point", ""))
    if point:
        body += f'<br/><font size=9 color="{hx(BLUE)}">▶ {point}</font>'
    flow.append(Paragraph(body, S["ab"]))


GROUP_LABEL = {
    "mc": "■ 四択問題（空所に入る記号を選べ）",
    "order": "■ 整序英作文（[ ]内を並べ替えよ。文頭は大文字で示してある）",
    "rewrite": "■ 書き換え（指示に従って書き換えよ）",
}


def by_type_then_no(qs):
    return sorted(qs, key=lambda q: ({"mc": 0, "order": 1, "rewrite": 2}[q["type"]], q["no"]))


def build_flow(units, total_q):
    flow = []
    today = datetime.date.today().strftime("%Y年%m月")

    flow.append(Spacer(1, 62 * mm))
    flow.append(Paragraph("高校英文法 レベル1", S["title"]))
    flow.append(Paragraph("標準演習", S["title"]))
    flow.append(Spacer(1, 8 * mm))
    flow.append(Paragraph("偏差値55～60 を狙う4分野", S["subtitle"]))
    flow.append(Spacer(1, 3 * mm))
    flow.append(Paragraph("時制 ・ 不定詞 ・ 動名詞 ・ 仮定法", S["subtitle"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph(
        f"全{len(units)}分野 × 各30問（計{total_q}問）　·　四択／整序英作文／書き換え",
        S["subtitle"]))
    flow.append(Spacer(1, 26 * mm))
    flow.append(Paragraph(today, S["cover_small"]))
    flow.append(Paragraph("AI塾", S["cover_small"]))
    # ★これを忘れると2ページ目以降も "cover" テンプレートのままになり、
    #   全ページに紺帯が刷られてノンブルも柱も消える(初版で実際にそうなった)。
    flow.append(NextPageTemplate("normal"))
    flow.append(PageBreak())

    flow.append(SectionMarker("目次", ""))
    flow.append(Paragraph("目次", S["part_title"]))
    flow.append(Spacer(1, 6 * mm))
    rows = []
    for i, (unit, qs) in enumerate(units, 1):
        c = {"mc": 0, "order": 0, "rewrite": 0}
        lv = {"standard": 0, "advanced": 0}
        for q in qs:
            c[q["type"]] += 1
            lv[q["level"]] += 1
        rows.append([
            Paragraph(f"<font color='{hx(NAVY)}'>{i:02d}</font>", S["toc"]),
            Paragraph(esc(unit), S["toc"]),
            Paragraph(f"<font size=9 color='{hx(GRAY)}'>"
                      f"4択{c['mc']}・整序{c['order']}・書換{c['rewrite']}</font>", S["toc"]),
            Paragraph(f"<font size=9 color='{hx(GRAY)}'>"
                      f"標準{lv['standard']}・発展{lv['advanced']}</font>", S["toc"]),
            Paragraph(f"<font size=9 color='{hx(GRAY)}'>{len(qs)}問</font>", S["toc"]),
        ])
    tt = Table(rows, colWidths=[12 * mm, 60 * mm, 46 * mm, 40 * mm, 16 * mm])
    tt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (4, 0), (4, -1), "RIGHT"),
    ]))
    flow.append(tt)
    flow.append(Spacer(1, 10 * mm))
    a = hx(ACCENT)
    flow.append(Paragraph(
        "<font size=10 color='#444444'>【この問題集について】"
        "『高校英文法 基礎定着問題集（全20分野500問）』で基礎を終えた生徒が、"
        "入試の標準レベル（偏差値55～60）へ上がるための4分野を集めた演習です。"
        "各問に [標準] [発展] の目安を付けています。まず [標準] だけを通しで解き、"
        "8割を超えてから [発展] に進むと定着が速くなります。<br/><br/>"
        f"〈<font color='{a}'>4択</font>〉は空所に入る記号を選び、"
        f"〈<font color='{a}'>整序</font>〉は [ ] 内の語句を並べ替えて英文を完成させ、"
        f"〈<font color='{a}'>書換</font>〉は指示に従って英文を書き換えます。"
        "整序では文頭に来る語だけを大文字で示してあります。"
        "各問に解説と ▶ ポイントが付いています。</font>",
        S["note"]))

    flow.append(PageBreak())
    flow.append(SectionMarker("問題編", ""))
    flow.append(Spacer(1, 60 * mm))
    flow.append(Paragraph("問題編", S["part_title"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph(f"全{len(units)}分野　計{total_q}問", S["subtitle"]))
    for i, (unit, qs) in enumerate(units, 1):
        flow.append(PageBreak())
        flow.append(SectionMarker("問題編", unit))
        flow.append(section_band(i, unit, "問題"))
        flow.append(Spacer(1, 5 * mm))
        cur = None
        for q in by_type_then_no(qs):
            if q["type"] != cur:
                cur = q["type"]
                flow.append(Spacer(1, 2 * mm))
                flow.append(Paragraph(
                    f"<font size=11 color='{hx(NAVY)}'>{GROUP_LABEL[cur]}</font>", S["grp"]))
            render_problem(q, flow)

    flow.append(PageBreak())
    flow.append(SectionMarker("解答・解説編", ""))
    flow.append(Spacer(1, 60 * mm))
    flow.append(Paragraph("解答・解説編", S["part_title"]))
    for i, (unit, qs) in enumerate(units, 1):
        flow.append(PageBreak())
        flow.append(SectionMarker("解答・解説編", unit))
        flow.append(section_band(i, unit, "解答"))
        flow.append(Spacer(1, 5 * mm))
        for q in by_type_then_no(qs):
            render_answer(q, flow)
    return flow


def make_doc():
    doc = Doc(OUT_PATH, pagesize=A4,
              leftMargin=18 * mm, rightMargin=18 * mm, topMargin=20 * mm, bottomMargin=16 * mm,
              title=BOOK_TITLE, author="AI塾")
    fw = A4[0] - 36 * mm
    fh = A4[1] - 36 * mm
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[Frame(18 * mm, 16 * mm, fw, fh, id="cover")],
                     onPage=on_cover),
        PageTemplate(id="normal", frames=[Frame(18 * mm, 16 * mm, fw, fh, id="main",
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                     onPage=on_page),
    ])
    return doc


def main():
    global S
    register_font()
    S = styles()
    units = []
    for fname, unit in UNIT_ORDER:
        with open(os.path.join(UNITS_DIR, fname), encoding="utf-8") as f:
            d = json.load(f)
        if d["unit"] != unit:
            print(f"✗ {fname}: unit が {d['unit']!r} (期待 {unit!r})", file=sys.stderr)
            sys.exit(1)
        units.append((unit, d["questions"]))
    total_q = sum(len(qs) for _, qs in units)

    # 1パス目でページ→セクション対応を採り、2パス目で正しいヘッダを刷る
    doc1 = make_doc()
    doc1.build(build_flow(units, total_q))
    last = ("", "")
    PAGE_SECTIONS.clear()
    for p in range(1, doc1.page + 1):
        if p in doc1.section_map:
            last = doc1.section_map[p]
        PAGE_SECTIONS[p] = last

    doc2 = make_doc()
    doc2.build(build_flow(units, total_q))
    print(f"WROTE {OUT_PATH} | pages: {doc2.page} | questions: {total_q}")


if __name__ == "__main__":
    main()
