# -*- coding: utf-8 -*-
"""
2026年 共通テスト 英語(リーディング) 詳細解答・解説 PDF ビルダー
- 本文（全文）を抜き出して掲載 + 設問別に 正解 / 解説 / 本文該当箇所
- 和欧混植は Arial Unicode 単一フォントで対応
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content as C

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, KeepTogether, FrameBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("AU", FONT_PATH))
pdfmetrics.registerFontFamily("AU", normal="AU", bold="AU", italic="AU", boldItalic="AU")

# ---------- カラーパレット ----------
NAVY    = colors.HexColor("#1f3a5f")
ACCENT  = colors.HexColor("#c0392b")   # 正解・赤系
TEAL    = colors.HexColor("#0e6b66")   # 英文該当箇所
GRAY    = colors.HexColor("#555555")
LIGHT   = colors.HexColor("#f4f6f9")   # 本文ボックス背景
LIGHTQ  = colors.HexColor("#eef3ee")   # 該当箇所背景
HEADBG  = colors.HexColor("#1f3a5f")
ANSBG   = colors.HexColor("#fdecea")
RULE    = colors.HexColor("#d4dae2")

# ---------- スタイル ----------
def S(name, **kw):
    base = dict(fontName="AU", fontSize=9.3, leading=14, textColor=colors.black,
                alignment=TA_LEFT, spaceBefore=0, spaceAfter=0)
    base.update(kw)
    return ParagraphStyle(name, **base)

st_theme   = S("theme",  fontSize=10.5, leading=15, textColor=colors.white)
st_sit     = S("sit",    fontSize=9.0, leading=13.5, textColor=GRAY)
st_ptitle  = S("ptitle", fontSize=9.3, leading=13, textColor=NAVY)
st_pbody   = S("pbody",  fontSize=8.8, leading=13.2, textColor=colors.HexColor("#1a1a1a"))
st_spk     = S("spk",    fontSize=8.8, leading=12.5, textColor=NAVY)
st_qlabel  = S("qlabel", fontSize=10, leading=14, textColor=ACCENT)
st_qtext   = S("qtext",  fontSize=9.2, leading=13.5, textColor=colors.black)
st_choice  = S("choice", fontSize=8.8, leading=12.8, textColor=colors.HexColor("#222222"), leftIndent=10)
st_ans     = S("ans",    fontSize=10.5, leading=15, textColor=ACCENT)
st_exp     = S("exp",    fontSize=9.2, leading=14.2, textColor=colors.HexColor("#141414"))
st_evlabel = S("evlabel",fontSize=8.6, leading=12, textColor=TEAL)
st_even    = S("even",   fontSize=8.6, leading=12.4, textColor=TEAL)
st_evja    = S("evja",   fontSize=8.4, leading=12, textColor=GRAY)
st_small   = S("small",  fontSize=8.2, leading=11.5, textColor=GRAY)

def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

# ---------- ドキュメント枠 ----------
PW, PH = A4
LM = RM = 16*mm
TM = 16*mm
BM = 15*mm

def header_footer(canvas, doc):
    canvas.saveState()
    # ヘッダ細線
    canvas.setStrokeColor(RULE); canvas.setLineWidth(0.6)
    canvas.line(LM, PH-TM+6, PW-RM, PH-TM+6)
    canvas.setFont("AU", 7.5); canvas.setFillColor(GRAY)
    canvas.drawString(LM, PH-TM+9, "2026年 大学入学共通テスト　英語（リーディング）　詳細解答・解説")
    canvas.drawRightString(PW-RM, PH-TM+9, "トリリオンAI塾")
    # フッタ
    canvas.setStrokeColor(RULE)
    canvas.line(LM, BM-4, PW-RM, BM-4)
    canvas.setFont("AU", 8); canvas.setFillColor(GRAY)
    canvas.drawCentredString(PW/2, BM-12, f"- {doc.page} -")
    canvas.restoreState()

def build():
    out = "/Users/adachishouhei/Desktop/共通テスト2026英語_解答解説.pdf"
    doc = BaseDocTemplate(out, pagesize=A4, leftMargin=LM, rightMargin=RM,
                          topMargin=TM, bottomMargin=BM, title="共通テスト2026英語 詳細解答解説")
    frame = Frame(LM, BM, PW-LM-RM, PH-TM-BM, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=header_footer)])

    story = []
    story += cover()
    story += answer_table()
    for sec in C.SECTIONS:
        story += section_block(sec)
    doc.build(story)
    print("WROTE", out)

# ---------- 表紙 ----------
def cover():
    el = []
    el.append(Spacer(1, 26*mm))
    t = Table([[Paragraph("2026年 大学入学共通テスト", S("c1", fontSize=15, leading=22, textColor=NAVY, alignment=TA_CENTER))],
               [Paragraph("英語（リーディング）", S("c2", fontSize=22, leading=30, textColor=ACCENT, alignment=TA_CENTER))],
               [Paragraph("詳細 解答・解説　＋　本文該当箇所", S("c3", fontSize=13, leading=20, textColor=NAVY, alignment=TA_CENTER))]],
              colWidths=[PW-LM-RM])
    t.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    el.append(t)
    el.append(Spacer(1, 8*mm))
    el.append(Paragraph("満点 100点／試験時間 80分／全8大問・解答番号 1〜44", S("c4", fontSize=10.5, leading=16, textColor=GRAY, alignment=TA_CENTER)))
    el.append(Spacer(1, 12*mm))
    note = ("本資料は、各設問の<b>正解</b>・<b>詳しい解説（日本語）</b>に加え、解答の根拠となる"
            "<b>本文の該当箇所（英文＋和訳）</b>を抜き出して掲載しています。各大問の冒頭には"
            "読解の対象となる<b>本文（全文）</b>を再録しています。")
    box = Table([[Paragraph(note, S("c5", fontSize=9.5, leading=15.5, textColor=colors.HexColor("#222")))]],
                colWidths=[PW-LM-RM-20*mm])
    box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),LIGHT),("BOX",(0,0),(-1,-1),0.6,RULE),
                             ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
                             ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))
    wrap = Table([[box]], colWidths=[PW-LM-RM]); wrap.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER")]))
    el.append(wrap)
    el.append(FrameBreak())
    return el

# ---------- 解答一覧 ----------
def answer_table():
    el = []
    el.append(bar("解答一覧", "Answer Key"))
    el.append(Spacer(1, 4))
    # 4列に分けて並べる（番号/正解）
    rows = C.ANSWER_KEY
    header = ["大問", "問", "番号", "正解", "配点"]
    data = [header]
    for sec, q, num, ans, pt in rows:
        data.append([sec, q, num, ans, str(pt)])
    tbl = Table(data, colWidths=[20*mm, 16*mm, 16*mm, 22*mm, 14*mm]*1, repeatRows=1, hAlign="LEFT")
    style = [("FONT",(0,0),(-1,-1),"AU",8.6),
             ("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),colors.white),
             ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
             ("TEXTCOLOR",(3,1),(3,-1),ACCENT),("FONTSIZE",(3,1),(3,-1),9.6),
             ("GRID",(0,0),(-1,-1),0.4,RULE),
             ("TOPPADDING",(0,0),(-1,-1),3.2),("BOTTOMPADDING",(0,0),(-1,-1),3.2)]
    for i in range(1,len(data)):
        if i%2==0: style.append(("BACKGROUND",(0,i),(-1,i),colors.HexColor("#f7f9fc")))
    tbl.setStyle(TableStyle(style))
    el.append(tbl)
    el.append(Spacer(1,6))
    el.append(Paragraph("※「順不同」と注記した設問（22・23／24・25／33・34／40・41）は2つの解答の順序を問わない。"
                        "問2の整序（9〜12／26〜29）と第8問問3〔42〕・問5〔44〕は完答で得点。",
                        st_small))
    el.append(FrameBreak())
    return el

# ---------- 共通: 見出しバー ----------
def bar(title_jp, sub=""):
    p = Paragraph(f'<font size=12>{esc(title_jp)}</font>'
                  + (f'   <font size=8.5 color="#c9d6e5">{esc(sub)}</font>' if sub else ""),
                  st_theme)
    t = Table([[p]], colWidths=[PW-LM-RM])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),HEADBG),
                           ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),8),
                           ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    return t

# ---------- 本文ボックス ----------
def passage_box(p):
    inner = [Paragraph("▍" + esc(p["title"]), st_ptitle), Spacer(1,3)]
    if p["kind"] == "dialogue":
        for spk, txt in p["items"]:
            inner.append(Paragraph(f'<font color="#1f3a5f">●{esc(spk)}：</font>{esc(txt)}', st_pbody))
            inner.append(Spacer(1,2.5))
    else:
        for para in p["items"]:
            inner.append(Paragraph(esc(para), st_pbody))
            inner.append(Spacer(1,3))
    box = Table([[inner]], colWidths=[PW-LM-RM])
    box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),LIGHT),("BOX",(0,0),(-1,-1),0.5,RULE),
                             ("LINEBEFORE",(0,0),(0,-1),2.2,NAVY),
                             ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
                             ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    return box

# ---------- 設問ブロック ----------
def question_block(q):
    el = []
    el.append(Paragraph("■ " + esc(q["label"]), st_qlabel))
    el.append(Spacer(1,1.5))
    el.append(Paragraph(esc(q["qtext"]), st_qtext))
    el.append(Spacer(1,2.5))
    for mark, txt in q["choices"]:
        el.append(Paragraph(f'<font color="#1f3a5f">{esc(mark)}</font> {esc(txt)}', st_choice))
    el.append(Spacer(1,4))
    # 正解バンド
    ans = Table([[Paragraph(f'正解：<font size=12>{esc(q["answer"])}</font>', st_ans)]], colWidths=[PW-LM-RM])
    ans.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),ANSBG),("LINEBEFORE",(0,0),(0,-1),2.4,ACCENT),
                             ("LEFTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    el.append(ans)
    el.append(Spacer(1,3))
    el.append(Paragraph("〔解説〕 " + esc(q["explain"]), st_exp))
    el.append(Spacer(1,3))
    # 該当箇所
    ev_inner = [Paragraph("【本文該当箇所】", st_evlabel)]
    for en, ja in q["evidence"]:
        ev_inner.append(Spacer(1,1.5))
        ev_inner.append(Paragraph("“" + esc(en) + "”", st_even))
        ev_inner.append(Paragraph("　— " + esc(ja), st_evja))
    evbox = Table([[ev_inner]], colWidths=[PW-LM-RM])
    evbox.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),LIGHTQ),("LINEBEFORE",(0,0),(0,-1),2.2,TEAL),
                               ("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),
                               ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    el.append(evbox)
    el.append(Spacer(1,8))
    return el

# ---------- 大問ブロック ----------
def section_block(sec):
    el = []
    el.append(bar(f'{sec["num"]}　（配点 {sec["points"]}）', sec["theme"]))
    el.append(Spacer(1,4))
    el.append(Paragraph("◆ 設定：" + esc(sec["situation"]), st_sit))
    el.append(Spacer(1,5))
    el.append(Paragraph("〈本文（全文）〉", S("ph", fontSize=9.5, textColor=NAVY)))
    el.append(Spacer(1,3))
    for p in sec["passages"]:
        el.append(passage_box(p))
        el.append(Spacer(1,5))
    el.append(Spacer(1,2))
    el.append(Paragraph("〈設問の解答・解説〉", S("ph2", fontSize=9.5, textColor=NAVY)))
    el.append(Spacer(1,4))
    for q in sec["questions"]:
        el += [KeepTogether(question_block(q))]
    el.append(FrameBreak())
    return el

if __name__ == "__main__":
    build()
