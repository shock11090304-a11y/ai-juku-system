# -*- coding: utf-8 -*-
"""出口式 現代文読解ロジック演習 問題編/解答解説編 PDFビルダー(2026-07-12改訂版)"""
import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether, Flowable,
)

import deguchi_content as C

# ---------------- fonts ----------------
def register_fonts():
    tries = [
        ("JPN", "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", 0),
        ("JPN-B", "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc", 0),
    ]
    ok = True
    for name, path, idx in tries:
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=idx))
        except Exception as e:
            print(f"font fail {name}: {e}")
            ok = False
    if not ok:
        au = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
        pdfmetrics.registerFont(TTFont("JPN", au))
        pdfmetrics.registerFont(TTFont("JPN-B", au))
    registerFontFamily("JPN", normal="JPN", bold="JPN-B", italic="JPN", boldItalic="JPN-B")


register_fonts()

# ---------------- palette ----------------
NAVY = colors.HexColor("#1e2a52")
NAVY2 = colors.HexColor("#2c3e6b")
BODY = colors.HexColor("#1a1a2e")
GRAY = colors.HexColor("#5a5a68")
GOLD = colors.HexColor("#B8860B")
BAND_BG = colors.HexColor("#e9edf6")
CREAM_BG = colors.HexColor("#faf3e2")
ZEBRA = colors.HexColor("#edf0f8")
BOX_BG = colors.HexColor("#f0f3fa")
BOX_EDGE = colors.HexColor("#c9d2e8")
RULE = colors.HexColor("#c8ccd8")
TBL_EDGE = colors.HexColor("#b7c0d8")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 57, 57, 50, 62
CW = PAGE_W - ML - MR  # content width

# ---------------- styles ----------------
def S(name, **kw):
    base = dict(fontName="JPN", fontSize=10.3, leading=16.5, textColor=BODY, wordWrap="CJK")
    base.update(kw)
    return ParagraphStyle(name, **base)


st_body = S("body", spaceBefore=4, spaceAfter=4)
st_gray = S("gray", fontSize=9.4, leading=14.5, textColor=GRAY, spaceBefore=2, spaceAfter=2)
st_gray_sm = S("graysm", fontSize=8.6, leading=12.5, textColor=GRAY)
st_h1 = S("h1", fontName="JPN-B", fontSize=13, leading=17, textColor=NAVY, spaceBefore=13, spaceAfter=5)
st_band_t = S("bandt", fontName="JPN-B", fontSize=12.5, leading=16, textColor=NAVY)
st_band_n = S("bandn", fontSize=8.8, leading=11.5, textColor=GRAY)
st_pass = S("pass", leading=19.5, spaceBefore=2, spaceAfter=2, firstLineIndent=10.5)
st_qtext = S("qtext", leading=16.5)
st_qlabel = S("qlabel", fontName="JPN-B", fontSize=10.5, leading=16.5, textColor=NAVY)
st_choice = S("choice", leading=16, leftIndent=12, firstLineIndent=-12, spaceBefore=1.5, spaceAfter=1.5)
st_choice_g = S("choiceg", leading=16, leftIndent=12, firstLineIndent=-12, spaceBefore=1.5, spaceAfter=1.5, textColor=GOLD)
st_ansbox = S("ansbox", fontSize=9.4, textColor=GRAY, spaceBefore=5)
st_item = S("item", leading=16.5, spaceBefore=3, spaceAfter=0)
st_drill_label = S("dlabel", leading=16.5, spaceBefore=12, spaceAfter=3)
st_ans = S("ans", leading=16, spaceBefore=2, spaceAfter=0)
st_kai = S("kai", fontSize=9.7, leading=15, textColor=colors.HexColor("#33334a"), spaceBefore=1, spaceAfter=2)
st_logic = S("logic", fontSize=9.4, leading=13, textColor=GOLD, spaceBefore=3, spaceAfter=1)
st_check = S("check", leading=18, spaceBefore=3, spaceAfter=3, leftIndent=14, firstLineIndent=-14)
st_tbl = S("tbl", fontSize=9.2, leading=13.5)
st_tbl_h = S("tblh", fontName="JPN-B", fontSize=9.4, leading=12, textColor=colors.white)


# ---------------- flowables ----------------
class HLine(Flowable):
    def __init__(self, width, color=RULE, thickness=0.6, offset_x=0):
        super().__init__()
        self.w, self.c, self.t, self.ox = width, color, thickness, offset_x
        self.width, self.height = width, thickness

    def draw(self):
        self.canv.setStrokeColor(self.c)
        self.canv.setLineWidth(self.t)
        self.canv.line(self.ox, 0, self.ox + self.w, 0)


def rule_lines(n=3, width=CW, gap=13):
    out = [Spacer(1, 7)]
    for i in range(n):
        out.append(HLine(width))
        if i < n - 1:
            out.append(Spacer(1, gap))
    out.append(Spacer(1, 8))
    return out


def answer_rule():
    # ドリル小問用の短い記入線 (中央右寄り)
    return [Spacer(1, 6), HLine(CW * 0.42, offset_x=CW * 0.29), Spacer(1, 6)]


def band(title, note=None, bg=BAND_BG):
    rows = [[Paragraph(title, st_band_t)]]
    if note:
        rows.append([Paragraph(note, st_band_n)])
    t = Table(rows, colWidths=[CW - 4])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (0, 0), 7),
        ("BOTTOMPADDING", (0, -1), (0, -1), 7),
        ("TOPPADDING", (0, 1), (0, 1), 0) if note else ("TOPPADDING", (0, 0), (0, 0), 7),
        ("LINEBEFORE", (0, 0), (0, -1), 4, NAVY),
    ]))
    return [Spacer(1, 6), t, Spacer(1, 8)]


def passage_box(paras, style=st_pass):
    inner = [Paragraph(p, style) for p in paras]
    t = Table([[inner]], colWidths=[CW - 6])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BOX_BG),
        ("BOX", (0, 0), (-1, -1), 0.7, BOX_EDGE),
        ("LINEBEFORE", (0, 0), (0, -1), 3, NAVY2),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return [Spacer(1, 4), t, Spacer(1, 8)]


def qblock(label, text):
    """問N ラベル(金バー付き) + 設問文"""
    t = Table(
        [[Paragraph(label, st_qlabel), Paragraph(text, st_qtext)]],
        colWidths=[34, CW - 34 - 3],
    )
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("LEFTPADDING", (1, 0), (1, 0), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEBEFORE", (0, 0), (0, 0), 3, GOLD),
    ]))
    return [Spacer(1, 10), t, Spacer(1, 2)]


def grid_table(header, rows, widths, header_bg=NAVY, zebra=True, span_title=None, keep=False):
    data = []
    style = [
        ("GRID", (0, 0), (-1, -1), 0.6, TBL_EDGE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    r0 = 0
    if span_title:
        data.append([Paragraph(span_title, st_tbl_h)] + [""] * (len(widths) - 1))
        style += [
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY2),
        ]
        r0 = 1
    if header:
        data.append([Paragraph(h, st_tbl_h) for h in header])
        style.append(("BACKGROUND", (0, r0), (-1, r0), NAVY))
        r0 += 1
    for i, row in enumerate(rows):
        data.append([Paragraph(c, st_tbl) for c in row])
        if zebra and i % 2 == 1:
            style.append(("BACKGROUND", (0, r0 + i), (-1, r0 + i), ZEBRA))
    t = Table(data, colWidths=widths, repeatRows=r0)
    t.setStyle(TableStyle(style))
    out = [Spacer(1, 5), t, Spacer(1, 7)]
    return [KeepTogether(out)] if keep else out


def title_header(badge):
    st_title = S("t", fontName="JPN-B", fontSize=21, leading=27, textColor=colors.white)
    st_sub = S("ts", fontSize=11.5, leading=15, textColor=colors.HexColor("#dfe4f2"))
    st_badge = S("tb", fontName="JPN-B", fontSize=13, leading=16, textColor=colors.white, alignment=1)
    t = Table(
        [[Paragraph("出口式で読む 現代文 読解ロジック演習", st_title)],
         [HLine(CW - 36, color=GOLD, thickness=2)],
         [Paragraph("論理で読む・論理で解く ― 大学受験の基本ステップ", st_sub)]],
        colWidths=[CW],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (0, 0), 14),
        ("BOTTOMPADDING", (0, 0), (0, 0), 6),
        ("TOPPADDING", (0, 1), (0, 1), 2),
        ("BOTTOMPADDING", (0, 1), (0, 1), 2),
        ("TOPPADDING", (0, 2), (0, 2), 4),
        ("BOTTOMPADDING", (0, 2), (0, 2), 12),
    ]))
    b = Table([[Paragraph(badge, st_badge)]], colWidths=[CW])
    b.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [t, Spacer(1, 8), b, Spacer(1, 8)]


def name_score_row():
    st_lab = S("nlab", fontSize=10.8, textColor=NAVY)
    t = Table(
        [[Paragraph("氏名", st_lab), "", Paragraph("得点", st_lab), ""]],
        colWidths=[34, CW * 0.62, 40, CW - 74 - CW * 0.62],
    )
    t.setStyle(TableStyle([
        ("LINEBELOW", (1, 0), (1, 0), 0.7, GRAY),
        ("LINEBELOW", (3, 0), (3, 0), 0.7, GRAY),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [Spacer(1, 6), t, Spacer(1, 10)]


# ---------------- doc scaffolding ----------------
def make_doc(path, book_label):
    def on_page(canv, doc):
        canv.saveState()
        canv.setStrokeColor(colors.HexColor("#d8dbe4"))
        canv.setLineWidth(0.5)
        canv.line(ML, 46, PAGE_W - MR, 46)
        canv.setFont("JPN", 8)
        canv.setFillColor(GRAY)
        canv.drawCentredString(
            PAGE_W / 2, 34,
            f"トリリオンAI塾　出口式で読む 現代文 読解ロジック演習　―　{book_label}　―　{canv.getPageNumber()}",
        )
        canv.restoreState()

    doc = BaseDocTemplate(
        path, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
        title=f"出口式で読む 現代文 読解ロジック演習 {book_label}",
        author="トリリオンAI塾",
    )
    frame = Frame(ML, MB, CW, PAGE_H - MT - MB, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="pt", frames=[frame], onPage=on_page)])
    return doc


def mc_choices_plain(key):
    out = []
    for mark, text in C.CHOICES[key]["items"]:
        out.append(Paragraph(f"{mark} {text}", st_choice))
    out.append(Paragraph("解答欄 ( )", st_ansbox))
    return out


def mc_choices_answer(key):
    out = []
    d = C.CHOICES[key]
    for mark, text in d["items"]:
        if mark == d["correct"]:
            out.append(Paragraph(f"★ {mark} {text}", st_choice_g))
        else:
            out.append(Paragraph(f"　{mark} {text}", st_choice))
    out.append(Paragraph(f"<b>正解</b>　{d['correct']}", S("seikai", fontName="JPN-B", fontSize=10.8, textColor=NAVY, spaceBefore=6)))
    return out


def drill_item(text, ans, kai, rule=True):
    parts = [Paragraph(text, st_item)]
    if rule:
        parts += answer_rule()
    return parts


def kaito_item(text_paras, ans, kai):
    parts = [Paragraph(t, st_item) for t in text_paras]
    parts.append(Paragraph(f"<b>答</b>　{ans}", st_ans))
    parts.append(Paragraph(f"<b>解説</b>　{kai}", st_kai))
    parts.append(Spacer(1, 4))
    return [KeepTogether(parts)]


# ============================================================
# 問題編
# ============================================================
def build_mondai(path):
    doc = make_doc(path, "問題編")
    E = []
    E += title_header("問題編")
    E.append(Paragraph("現代文が苦手でも大丈夫。答えは必ず本文の中にある。接続語を◯で囲み、指示語の指す先を確かめながら、論理の流れを追ってみよう。", st_gray))
    E += name_score_row()
    E += band("読解ロジックの要点", "＊ここを読んでから演習に進もう(解くときの武器になる)")

    E.append(Paragraph("1. 現代文は「論理」で読む", st_h1))
    E.append(Paragraph("現代文は、才能やセンスで読むものではない。「論理」で読むものである。", st_body))
    E.append(Paragraph("ここでいう論理とは、難しい理屈のことではない。「言葉と言葉のつながり方」のことだ。筆者は、自分の主張を読者に正確に伝えるために、言葉を一定のルールでつないで文章を組み立てている。そのつながり方(＝論理)を客観的にたどれば、誰が読んでも同じ結論にたどり着く。", st_body))
    E.append(Paragraph("「なんとなく」「感覚で」読むのをやめ、本文に書かれた論理を根拠に読み、根拠に基づいて解く。これが出口式の出発点である。答えは君の頭の中ではなく、いつも本文の中にある。", st_body))

    E.append(Paragraph("2. すべての土台 ― 三つの論理関係", st_h1))
    E.append(Paragraph("文章の中で言葉と言葉をつなぐ関係は、突きつめると次の三つしかない。この三つを見抜けることが、現代文読解のすべての土台になる。(このほかに、情報を対等に並べ足す「並列(添加)」を、三つの関係を補う整理用のラベルとして使うことがある。)", st_body))
    E += grid_table(
        ["関係", "はたらき", "目印になる言葉(接続語)"],
        [
            ["① イコールの関係(＝)", "言い換え・具体と抽象・比喩。同じ内容を別の言葉で繰り返す。筆者の主張は必ず言い換えられて何度も現れる。", "つまり・すなわち・要するに／たとえば(具体例)"],
            ["② 対立関係(⇔)", "二つのものを対比する。一方を際立たせるために、もう一方を持ち出す。", "しかし・だが・ところが・一方・～に対して・むしろ"],
            ["③ 因果関係(→)", "原因と結果、理由と主張をつなぐ。「AだからB」「なぜならA」。", "だから・したがって・それゆえ・なぜなら・～ので・～ため"],
        ],
        [CW * 0.27, CW * 0.42, CW * 0.31],
    )

    E.append(Paragraph("3. イコールを深める ― 「具体と抽象」で筆者の主張を見つける", st_h1))
    E.append(Paragraph("イコールの関係でいちばん大切なのが「具体と抽象」だ。抽象とは、いくつかの具体例から共通点を取り出してまとめたもの。具体とは、その抽象を分かりやすく示した個々の例のことである。", st_body))
    E.append(Paragraph("評論では、筆者の主張はいつも抽象的な形で述べられ、それが具体例で説明される。だから、具体例(たとえば…)に出会ったら「これはどの主張の例か」を考える。逆に、具体例が続いたら「要するに何が言いたいのか(抽象)」を一言でまとめる。", st_body))
    E.append(Paragraph("さらに大事なのは、筆者の主張は一度では終わらないということ。大事なことほど、言葉を変えて何度も繰り返される(＝イコールで言い換えられる)。同じ内容が別の表現で出てきたら、そこが主張だと考えてよい。", st_body))
    E += grid_table(
        ["具体(個々の例)", "抽象(まとめ)"],
        [
            ["犬・猫・馬・すずめ", "動物"],
            ["手紙を書く・電話をかける・会って話す", "人とコミュニケーションをとる"],
            ["スマホで調べる・電子レンジで温める", "便利な道具を使う"],
        ],
        [CW * 0.52, CW * 0.48],
    )

    E.append(Paragraph("4. 対立を深める ― 評論の「二項対立」をつかむ", st_h1))
    E.append(Paragraph("評論の多くは、二つのものを対立させて論じる。片方(A)を退け、もう片方(B)を主張するために対比するのだ。だから対立関係が見えれば、筆者がどちらの側に立っているかも見えてくる。", st_body))
    E.append(Paragraph("「Aに対してB」「Aではなく、むしろB」「一方はA、他方はB」――こうした形が出たら、A列とB列に分けて整理する(対比表を作る)と、頭の中がすっきりする。", st_body))
    E.append(Paragraph("下は評論に出てきやすい対立の型。ただしどちらが良い・悪いは文章によって決まるので、型を覚えて決めつけず、その文章で筆者がどちらを主張しているかを必ず本文で確かめること。", st_body))
    E += grid_table(
        ["よくある一方", "⇔", "もう一方"],
        [
            ["近代・現代", "⇔", "前近代・伝統"],
            ["西洋", "⇔", "東洋・日本"],
            ["人工・文明", "⇔", "自然"],
            ["個人", "⇔", "社会・共同体"],
            ["効率・便利", "⇔", "ゆとり・手間"],
        ],
        [CW * 0.42, CW * 0.16, CW * 0.42],
    )

    E.append(Paragraph("5. 因果を深める ― 「なぜ？」に答える", st_h1))
    E.append(Paragraph("因果関係は「原因→結果」「理由→主張」のつながりだ。設問で「なぜか」「理由を答えよ」と問われたら、答えは必ず本文の中にある。頭の中で理由をつくり出してはいけない。", st_body))
    E.append(Paragraph("探す目印は因果の接続語。「だから・したがって・それゆえ」は前が原因・後が結果。「なぜなら・というのは・～から・～ので・～ため」は、その部分が理由を表す。傍線部の前後を見て、これらの語をたどれば理由が見つかる。", st_body))
    E.append(Paragraph("答え方は、「～から。」「～ため。」と、理由を表す文末で結ぶこと。", st_body))

    E.append(Paragraph("6. 論理をたどる三つの目印 ― 主語述語・指示語・接続語", st_h1))
    E.append(Paragraph("主語・述語:「何が」「どうする/どうだ」。これが一文の骨組み。まずここを押さえれば、その一文が結局なにを言っているのかがつかめる。", st_body))
    E.append(Paragraph("指示語(これ・それ・この・その…):指示語には必ず前に指す内容がある。指示語が出てきたら、立ち止まって「何を指すか」を確認する。ここを飛ばすと文がつながらなくなる。", st_body))
    E.append(Paragraph("接続語:文と文の論理関係を教えてくれる標識。読むときは◯で囲む習慣を。とくに「しかし」の後には筆者の主張が来やすい。下の一覧で、接続語とその論理関係を頭に入れよう。", st_body))
    E += grid_table(
        ["はたらき", "論理関係", "おもな接続語"],
        [
            ["言い換え・要約", "イコール", "つまり・すなわち・要するに・言いかえれば"],
            ["例示", "イコール(具体)", "たとえば(例えば)"],
            ["逆接・対比", "対立", "しかし・だが・ところが・一方・むしろ・～に対して"],
            ["順接・結果", "因果", "だから・したがって・それゆえ・そこで"],
            ["理由", "因果", "なぜなら・というのは・～から・～ので"],
            ["添加(付け足し)", "並列", "また・さらに・そのうえ・しかも"],
        ],
        [CW * 0.24, CW * 0.2, CW * 0.56],
    )

    E.append(Paragraph("7. 譲歩と逆接 ― 筆者の主張はこの直後に来る", st_h1))
    E.append(Paragraph("「確かに～。しかし～。」「もちろん～だが～。」という形を譲歩(じょうほ)という。まず反対意見や一般論をいったん認めておき(＝譲歩)、そのうえで「しかし」と自分の主張を述べる型だ。", st_body))
    E.append(Paragraph("この型では、「確かに・もちろん」の後ろは筆者が本当に言いたいことではない(いったん認めているだけ)。本当の主張は必ず「しかし・だが」の後に来る。だから「確かに/もちろん」を見たら、「この後に『しかし』『だが』などの逆接が来て、そこに主張がある」と身構えよう。", st_body))
    E.append(Paragraph("選択肢問題では、譲歩部分(いったん認めただけの内容)を筆者の主張のように書いた選択肢が、よくあるひっかけである。", st_body))

    E.append(Paragraph("8. 読解の基本ステップ(この順で読む)", st_h1))
    for s in [
        "① 一文ごとに主語・述語をつかむ。",
        "② 指示語の指す内容を確かめ、接続語に印をつけて論理関係を意識する。",
        "③ イコールで筆者の主張を追い、対立で主張を際立たせ、因果で理由をつかむ。「確かに/もちろん…しかし」の譲歩の後ろに主張が来ることも意識する。",
        "④ 段落ごとの要点をつなぎ、文章全体で「筆者が最も言いたいこと(主題)」を一つにしぼる。",
    ]:
        E.append(Paragraph(s, st_body))

    E.append(Paragraph("9. 設問を解くときも「ロジック」で ― 選択肢の消し方", st_h1))
    E.append(Paragraph("傍線部の問題:傍線部を含む一文の主語・述語をつかみ、指示語・接続語を手がかりに、その言い換え(イコール)を本文中に探す。答えは自分でひねり出すのではなく、本文から拾う。", st_body))
    E.append(Paragraph("選択肢の問題:選択肢は本文の論理と照合して選ぶ・消す。感覚ではなく、本文の一文を指さして正解・不正解を説明できるようにする。下の五つの型で消していこう。", st_body))
    E += grid_table(
        ["消し方の型", "見分け方"],
        [
            ["① 言い過ぎ", "「すべて」「最も」「必ず」など、本文より強く言い切っている。"],
            ["② 本文にない", "本文に書かれていない語・話がまぎれこんでいる。"],
            ["③ 因果が逆", "原因と結果が入れかわっている／本文と逆のことを言っている。"],
            ["④ 対比のズレ", "対立するAとBを取り違えている。"],
            ["⑤ 主語のズレ", "誰の考えか・何についてかが、すりかわっている。"],
        ],
        [CW * 0.28, CW * 0.72],
    )
    # FIX-343: ③/④の優先規則
    E.append(Paragraph("＊③と④の両方に当てはまりそうなときは、対立するAとBの取り違えなら④を優先する(③は、因果の逆転など、それ以外の「逆」に使う)。", st_gray_sm))

    E.append(Paragraph("10. 記述問題の作法", st_h1))
    E.append(Paragraph("記述は「自分の感想」を書く欄ではない。本文の言葉を使って、設問が求める要素をそろえて書く。", st_body))
    E.append(Paragraph("手順:① 設問の問い方を確かめる(「どういうことか」＝言い換え / 「なぜか」＝理由)。② 傍線部を含む一文の主語述語をつかむ。③ 指示語・言い換えを本文にたどり、必要な要素を拾う。④ 要素をつないで、設問に対応する文末(「～こと。」「～から。」)で結ぶ。", st_body))
    E.append(Paragraph("字数は、短い問いなら一文、字数指定や「くわしく」なら要素を数えて増やす。迷ったら本文の言葉を優先し、思いつきの言葉は入れない。", st_body))

    E.append(Paragraph("11. 小説の読み方 ― 心情は「出来事・心情・行動」でたどる", st_h1))
    E.append(Paragraph("小説でも、感覚で読むのではなく論理でたどる。人物の心情は、① きっかけとなる出来事 → ② 心情 → ③ 行動・表情・情景、という流れで動いていく。", st_body))
    E.append(Paragraph("心情そのものが「うれしい」「悲しい」と書かれていないことも多い。そのときは、人物の行動・表情・言葉づかい・情景描写から心情を読み取る。「答案を手で隠した」→(見られたくない)、「胸の底が温かくなる」→(満たされている)というように。", st_body))
    E.append(Paragraph("とりわけ情景描写(風景・光・天気)は、人物の心情を映す鏡になっていることが多い。明るい光は明るい心、雨や夕闇は沈んだ心――というように、情景と心情を重ねて読もう。", st_body))

    # ---------- 演習1 ----------
    E.append(PageBreak())
    E += band("演習1　基礎トレーニング", "論理の型を12本のミニドリルで身につける")
    E.append(Paragraph("短い文で論理の「目印」をくり返し練習して、型を体にしみこませよう。基礎が固まれば、長い文章は必ず読めるようになる。全部で12本のミニドリル。", st_body))

    E.append(Paragraph(f"<b>問A</b> {C.QA_HEAD}", st_drill_label))
    E.append(Paragraph(f"　{C.QA_CHOICES}", st_body))
    for it in C.Q_A_ITEMS:
        E.append(Paragraph(it, st_item)); E += answer_rule()

    E.append(Paragraph(f"<b>問B</b> {C.QB_HEAD}", st_drill_label))
    for it in C.Q_B_ITEMS:
        E.append(Paragraph(it, st_item)); E += answer_rule()

    E.append(Paragraph(f"<b>問C</b> {C.QC_HEAD}", st_drill_label))
    for it in C.Q_C_ITEMS:
        E.append(Paragraph(it, st_item)); E += answer_rule()

    E.append(Paragraph(f"<b>問D</b> {C.QD_HEAD}", st_drill_label))
    E += passage_box(C.QD_PASSAGE)
    E.append(Paragraph("(1) 抽象的な主張を述べた一文", st_item)); E += rule_lines(2, gap=12)
    E.append(Paragraph("(2) その具体的な説明", st_item)); E += rule_lines(2, gap=12)

    E.append(Paragraph(f"<b>問E</b> {C.QE_HEAD}", st_drill_label))
    E += passage_box(C.QE_PASSAGE)
    E += grid_table(
        ["観点", "都会", "田舎"],
        [["便利さ", "( )", "( )"], ["時間の流れ", "( )", "( )"], ["人とのつながり", "( )", "( )"]],
        [CW * 0.34, CW * 0.33, CW * 0.33],
        keep=True,
    )

    E.append(Paragraph(f"<b>問F</b> {C.QF_HEAD}", st_drill_label))
    for it in C.Q_F_ITEMS:
        E.append(Paragraph(it, st_item)); E.append(Spacer(1, 8))

    E.append(Paragraph(f"<b>問G</b> {C.QG_HEAD}", st_drill_label))
    E.append(Paragraph(f"　{C.QG_CHOICES}", st_body))
    for it in C.QG_ITEMS:
        E.append(Paragraph(it, st_item)); E += answer_rule()

    E.append(Paragraph(f"<b>問H</b> {C.QH_HEAD}", st_drill_label))
    E += passage_box(C.QH_PASSAGE)
    E += grid_table(
        ["観点", "手書きのノート", "パソコンでの記録"],
        [["書く速さ", "( )", "( )"], ["記憶への残りやすさ", "( )", "( )"]],
        [CW * 0.34, CW * 0.33, CW * 0.33],
        keep=True,
    )

    E.append(Paragraph(f"<b>問I</b> {C.QI_HEAD}", st_drill_label))
    for it in C.QI_ITEMS:
        E.append(Paragraph(it, st_item)); E += rule_lines(1)

    E.append(Paragraph(f"<b>問J</b> {C.QJ_HEAD}", st_drill_label))
    for body, q in C.QJ_ITEMS:
        E.append(Paragraph(body, st_item))
        E.append(Paragraph(q, st_item))
        E += rule_lines(1)

    E.append(Paragraph(f"<b>問K</b> {C.QK_HEAD}", st_drill_label))
    for body, sel in C.Q_K_ITEMS:
        E.append(Paragraph(body, st_item))
        E.append(Paragraph("　" + sel, st_item))
        E += answer_rule()

    l_block = [Paragraph(f"<b>問L</b> {C.QL_HEAD}", st_drill_label),
               Paragraph(f"　{C.QL_CHOICES}", st_body),
               Paragraph(C.Q_L_ITEMS[0], st_item)] + answer_rule()
    E.append(KeepTogether(l_block))
    for it in C.Q_L_ITEMS[1:]:
        E.append(Paragraph(it, st_item)); E += answer_rule()

    # ---------- 演習2〜5 (大問) ----------
    daimon_specs = [
        ("演習2　短い評論で読む(言葉と思考)", "傍線部を『本文の言い換え』から解く", "第一問", C.PASSAGE_1,
         [("問1", "1-1", "desc3"), ("問2", "1-2", "desc3"), ("問3", "1-3", "mc")]),
        ("演習3　評論で総合演習(便利さ)", "対比・因果・譲歩・主張を最後まで追う", "第二問", C.PASSAGE_2,
         [("問1", "2-1", "desc3"), ("問2", "2-2", "desc3"), ("問3", "2-3", "mc"), ("問4", "2-4", "mc"), ("問5", "2-5", "mc")]),
        ("演習4　やや難しい評論(情報と知識)", "二項対立と譲歩逆接を見抜く", "第三問", C.PASSAGE_3,
         [("問1", "3-1", "mc"), ("問2", "3-2", "desc3"), ("問3", "3-3", "desc3"), ("問4", "3-4", "mc"), ("問5", "3-5", "mc")]),
        ("演習5　小説で心情把握", "出来事→心情→行動・情景でたどる", "第四問", C.PASSAGE_4,
         [("問1", "4-1", "desc3"), ("問2", "4-2", "mc"), ("問3", "4-3", "desc3"), ("問4", "4-4", "mc"), ("問5", "4-5", "mc")]),
    ]
    for ban, sub, daimon, passage, qs in daimon_specs:
        E.append(PageBreak())
        E += band(ban, sub)
        E.append(Paragraph(f"{daimon} 次の文章を読んで、あとの問いに答えよ。", st_h1))
        E += passage_box(passage)
        for label, key, kind in qs:
            block = qblock(label, C.Q_TEXTS[key])
            if kind == "mc":
                block += mc_choices_plain(key)
                E.append(KeepTogether(block))
            else:
                E.append(KeepTogether(block))
                E += rule_lines(3, gap=12)

    # ---------- チェックリスト ----------
    E.append(PageBreak())
    E += band("解き終えたら ― 出口式・見直しのチェックリスト", None)
    for c in [
        "接続語を◯で囲めたか。とくに「しかし」の後の筆者の主張を見逃さなかったか。",
        "「確かに/もちろん…しかし」の譲歩を見つけ、「しかし」の後を主張として拾えたか。",
        "指示語(これ・それ…)の指す内容を、いちいち前に戻って確かめたか。",
        "評論では二項対立(A⇔B)を整理し、筆者がどちら側かをつかめたか。",
        "傍線部の答えを、頭でひねり出すのではなく、本文の言い換え(イコール)から拾えたか。",
        "小説では「出来事→心情→行動・情景」で心情をたどれたか。情景描写と心情を重ねられたか。",
        "選択肢を消すとき、五つの型(言い過ぎ/本文にない/因果が逆/対比のズレ/主語のズレ)を根拠にできたか。",
        "最後に、筆者が最も言いたいこと(主題)を一文で言えるか。",
    ]:
        E.append(Paragraph(f'<font color="{C.GOLD}">▲</font> {c}', st_check))

    doc.build(E)
    print(f"built {path}")


# ============================================================
# 解答解説編
# ============================================================
def build_kaito(path):
    doc = make_doc(path, "解答・解説編")
    E = []
    E += title_header("解答・解説編")
    E.append(Paragraph("＊ただ答え合わせをするのではなく、『どの論理(イコール/対立/因果)で解けるか』を確かめよう。ここが伸びる人の見直し方。", st_gray))
    E += band("正解一覧", None, bg=CREAM_BG)
    E += grid_table(
        ["設問", "正解", "使う論理"],
        [
            ["一・問1", "記述(下記参照)", "主語述語 ＋ 指示語 ＋ 対立関係"],
            ["一・問2", "記述(下記参照)", "イコールの関係(具体と抽象)"],
            ["一・問3", "ア", "イコールの関係(主張の言い換え) ＋ 文章全体の論理構造"],
            ["二・問1", "記述(下記参照)", "イコールの関係(定義・言い換え)"],
            ["二・問2", "記述(下記参照)", "因果関係"],
            ["二・問3", "ウ", "対立関係(対比) ＋ 具体と抽象"],
            ["二・問4", "イ", "イコールの関係(言い換え) ＋ 因果関係"],
            ["二・問5", "エ", "文章全体の論理構造 ＋ 譲歩逆接から主張を見極める"],
            ["三・問1", "イ", "イコールの関係(言い換えの接続語)"],
            ["三・問2", "記述(下記参照)", "対立関係(対比) ＋ 定義(イコール)"],
            ["三・問3", "記述(下記参照)", "具体と抽象(イコール) ＋ 対立"],
            ["三・問4", "ウ", "因果関係 ＋ イコール(本文の言い換え)"],
            ["三・問5", "ア", "文章全体の論理構造 ＋ 譲歩逆接から主張を見極める"],
            ["四・問1", "記述(下記参照)", "心情把握(出来事→心情) ＋ 因果"],
            ["四・問2", "イ", "心情把握(行動の理由) ＋ 対比"],
            ["四・問3", "記述(下記参照)", "心情把握 ＋ 対立(うれしい⇔それとは違う)"],
            ["四・問4", "エ", "心情把握(情景描写＝心情の投影)"],
            ["四・問5", "ウ", "心情把握(心情の変化) ＋ 対比(隠す⇔表にする)"],
        ],
        [CW * 0.18, CW * 0.28, CW * 0.54],
    )

    # ---------- 演習1 解答と解説 ----------
    E.append(PageBreak())
    E += band("演習1　解答と解説", None)

    E.append(Paragraph(f"<b>問A</b> {C.QA_HEAD}", st_drill_label))
    E.append(Paragraph(f"　{C.QA_CHOICES}", st_body))
    a_ans = [
        ("ウ / 因果", "努力(原因)→優勝(結果)。原因と結果をつなぐので因果関係。目印は「だから」。"),
        ("イ / 対立", "前(自信がある)と後(出せなかった)が食い違う。逆の内容をぶつける対立関係。目印は「しかし」。"),
        ("ア / イコール", "「三か国語」を「日本語・英語・中国語」と言い換えて具体化している。イコールの関係で、目印は「つまり」。"),
        ("エ / イコール", "「蒸し暑い」という抽象的な内容を、具体例で示している。具体と抽象もイコールの関係で、目印は「たとえば」。"),
        ("オ / 並列", "「暗くなった」に「雷の音」を付け足している。情報を並べて足す並列(添加)。目印は「また」。"),
        ("ア / イコール", "「本番に強い」を、後の文が別の言葉で言い直して説明している(具体例ではなく言い換え)。イコールの関係。目印は「つまり」。"),
        ("ウ / 因果", "熱があった(原因)→出場をあきらめた(結果)。原因と結果をつなぐ因果関係。目印は「だから」。"),
        ("イ / 対立", "評判(よく効く)と自分の場合(まったく効かない)という逆の内容をぶつけている。対立関係。目印は「しかし」。"),
        ("エ / イコール", "「観光名所が多い」という内容を、具体例(城跡・古い街並み)で示している。具体と抽象＝イコールの関係。目印は「たとえば」。＊(3)との違いに注意:(3)は三か国語の中身を全部言い換えたので「つまり」。ここは多くの名所の中から例を挙げているので「たとえば」。"),
        ("オ / 並列", "ピアノに加えてギターを付け足している。情報を並べ足す並列(添加)。目印は「また」。"),
    ]
    for it, (ans, kai) in zip(C.Q_A_ITEMS, a_ans):
        E += kaito_item([it], ans, kai)

    E.append(Paragraph(f"<b>問B</b> {C.QB_HEAD}", st_drill_label))
    b_ans = [
        ("失敗", "指示語「それ」は前の内容を指す。恐れる対象＝直前の「失敗」。指示語には必ず前に指す内容がある。"),
        ("都会の便利さと、田舎の豊かな自然", "「この二つ」は直前の二つの内容をまとめて指す。前の一文から二つの要素を正確に拾う。"),
        ("自然を征服しようとする(考え方)", "「その考え方」は前の一文の内容を指す。直前の「自然を征服しようとしてきた」を指示語に当てはめて確かめる。"),
        ("毎朝三十分歩くこと", "「これ」に直前の内容を当てはめて、「毎朝三十分歩くことを始めてから」と読めれば正解。指示語は、指す内容に置きかえて文が通るかで確かめる。"),
        ("図書館", "「そこ」は場所を指す指示語。直前の「図書館」に置きかえて確かめる。"),
        ("「急がば回れ」という言葉", "「その＋名詞(意味)」の形。何の意味かと問えば、直前の「『急がば回れ』という言葉」に戻れる。"),
    ]
    for it, (ans, kai) in zip(C.Q_B_ITEMS, b_ans):
        E += kaito_item([it], ans, kai)

    E.append(Paragraph(f"<b>問C</b> {C.QC_HEAD}", st_drill_label))
    c_ans = [
        ("イコール", "後の文は前の文の言い換え(同じ内容を別の言葉で表す)。イコールの関係。"),
        ("対立", "外向的⇔内向的を対比している。二つを比べて違いを示す対立関係。"),
        ("因果", "大雨(原因)→増水・氾濫(結果)。原因と結果をつなぐ因果関係。"),
        ("イコール", "具体的な行動(約束を守る・うそをつかない)を、後の文が「誠実」と抽象的にまとめている。具体と抽象もイコールの関係。＊「だから」を挟んでも読めそうだが、後の文は新しい出来事や結果を述べたのではなく、前の内容を別の言葉でまとめ直しただけ。内容が同じなら言い換え(イコール)。"),
        ("因果", "動画を研究した(原因)→弱点を突けた(結果)。接続語が無くても、原因→結果のつながりなら因果関係。"),
        ("対立", "昔⇔今という時間の対比。「一回きり」⇔「何枚でも撮り直せる」を比べて違いを示す対立関係。"),
        ("因果", "直前まで画面を見た(原因)→寝つけなかった(結果)。因果関係。"),
        ("イコール", "ことわざ(比喩)を、後の文がその意味に言い換えている。比喩とその説明もイコールの関係。"),
    ]
    for it, (ans, kai) in zip(C.Q_C_ITEMS, c_ans):
        E += kaito_item([it], ans, kai)

    E.append(Paragraph(f"<b>問D</b> {C.QD_HEAD}", st_drill_label))
    E += passage_box(C.QD_PASSAGE)
    E += kaito_item(
        ["(1) 抽象的な主張を述べた一文"],
        "つまり、ふだん使う言葉が、その人の心のありようをつくっていくのである。",
        "「つまり」はまとめ(抽象)の目印。前の二つの具体例に共通する内容を、一般化してまとめている。具体例が続いたら、「要するに何が言いたいのか」をまとめた一文を探す。",
    )
    E += kaito_item(
        ["(2) その具体的な説明"],
        "「ありがとう」と口にすると、自分の気持ちまで明るくなる。反対に、とげとげしい言葉を使えば、心もとげとげしくなっていく。",
        "「ありがとう」と「とげとげしい言葉」という二つの具体例が、抽象的な主張を支えている。具体と抽象＝イコールの関係。",
    )

    E.append(Paragraph(f"<b>問E</b> {C.QE_HEAD}", st_drill_label))
    E += passage_box(C.QE_PASSAGE)
    E += grid_table(
        ["観点", "都会", "田舎"],
        [["便利さ", "便利", "不便"], ["時間の流れ", "慌ただしい", "ゆったり"], ["人とのつながり", "薄い", "濃い(近所づきあいも濃い)"]],
        [CW * 0.34, CW * 0.33, CW * 0.33],
    )
    E.append(Paragraph("<b>解説</b>　「一方」「〜だが」は対立の目印。都会と田舎を三つの観点で対比している。対立表に整理すると、筆者が何と何を比べているかが一目で分かる。", st_kai))

    E.append(Paragraph(f"<b>問F</b> {C.QF_HEAD}", st_drill_label))
    f_ans = [
        ("主語＝(白い)犬が　述語＝走り回っている", "述語「走り回っている」を先に見つけ、「走り回っているのは何か」→「犬が」。「芝生を」は述語を説明する修飾語(何を)であって主語ではない。"),
        ("主語＝(私の)姉は　述語＝通う", "「通うのは誰か」→「姉は」。「私の」は姉を説明する修飾語。"),
        ("主語＝母は　述語＝読んだ", "文頭の「手紙を」に引きずられない。「読んだのは誰か」→「母は」。「〜を」は動作の対象(目的語)で、主語は「〜が/〜は」。語順が入れかわっても述語から戻れば間違えない。"),
        ("主語＝老人が　述語＝すわっていた", "「すわっていたのは誰か」→「老人が」。場所(ベンチに)や様子(静かに)は、述語をくわしくする修飾語。"),
        ("主語＝(昨日買ったばかりの)傘が　述語＝壊れてしまった", "長い修飾語(昨日買ったばかりの)にまどわされない。「壊れたのは何か」→「傘が」。"),
    ]
    for it, (ans, kai) in zip(C.Q_F_ITEMS, f_ans):
        E += kaito_item([it], ans, kai)

    E.append(Paragraph(f"<b>問G</b> {C.QG_HEAD}", st_drill_label))
    E.append(Paragraph(f"　{C.QG_CHOICES}", st_body))
    g_ans = [
        ("イ(自然災害)", "三つに共通する性質(自然が引き起こす災い)を取り出してまとめた言葉が「自然災害」。共通点を取り出してまとめる＝抽象化。"),
        ("ウ(交通機関)", "人や物を運ぶ乗り物、という共通点でまとめると「交通機関」。"),
        ("ア(感情)", "心の動き、という共通点でまとめると「感情」。"),
        ("(解答例)野球・サッカー・バレーボール(テニス・バスケットボールなども可)", "抽象→具体の方向。評論を読むときは「具体例が出たらまとめ(抽象)を探す」「抽象的な主張が出たら具体例で確かめる」と、両方向を行き来できることが大切。"),
    ]
    for it, (ans, kai) in zip(C.QG_ITEMS, g_ans):
        E += kaito_item([it], ans, kai)

    E.append(Paragraph(f"<b>問H</b> {C.QH_HEAD}", st_drill_label))
    E += passage_box(C.QH_PASSAGE)
    E += grid_table(
        ["観点", "手書きのノート", "パソコンでの記録"],
        [["書く速さ", "時間がかかる", "速く大量に書き留められる"], ["記憶への残りやすさ", "内容が頭に残りやすい", "記憶に残りにくい"]],
        [CW * 0.34, CW * 0.33, CW * 0.33],
    )
    E.append(Paragraph("<b>解説</b>　「一方」は対立の目印。二つの記録方法を「速さ」と「記憶」の二つの観点で対比している。対立表に整理すれば、どちらの長所・短所かを取り違えない(選択肢の「対比のズレ」対策にもなる)。", st_kai))

    E.append(Paragraph(f"<b>問I</b> {C.QI_HEAD}", st_drill_label))
    i_ans = [
        ("しかし、睡眠時間を削ってまで行うのなら、かえって健康を損なってしまう。", "「確かに〜」は譲歩＝いったん認めただけで、筆者が本当に言いたいことではない。主張は「しかし」の後に来る。"),
        ("だが、本当に大切なのは、計画を立てたあとに、実際に動き出すことである。", "「もちろん…だが…」の譲歩逆接。筆者の言いたいことは「だが」の後ろ。"),
        ("しかし、失敗こそが、人を最も成長させてくれる教師なのである。", "「多くの人は考えている」＝一般論(通念)。「確かに」が無くても、一般論→「しかし」→筆者の主張、という型は同じ。評論の最頻出パターン。"),
    ]
    for it, (ans, kai) in zip(C.QI_ITEMS, i_ans):
        E += kaito_item([it], ans, kai)

    E.append(Paragraph(f"<b>問J</b> {C.QJ_HEAD}", st_drill_label))
    j_ans = [
        ("毎晩、英単語を十個ずつ覚え続けた(その積み重ねが実を結んだ)から。", "「その積み重ね」という指示語が原因を指している。指示語を前にたどれば理由が見つかる。理由の答えは文末を「〜から。」で結ぶ。"),
        ("森の木々が、夏の強い日ざしをさえぎってくれるから。", "「だから」の前＝原因、後＝結果。問われているのは結果の理由なので、「だから」の前を答える。"),
        ("焼きたてしか店頭に並ばないから。(毎朝その日に売る分だけ焼かれ、焼きたてしか店頭に並ばないから、とすればより十分)", "「〜ので」が理由の目印。中心となる理由は「〜ので」の直前(焼きたてしか並ばない)。その背景である前の一文(その日の分だけ焼く)まで含めると、より十分な答えになる。"),
    ]
    for (body, q), (ans, kai) in zip(C.QJ_ITEMS, j_ans):
        E += kaito_item([body, q], ans, kai)

    E.append(Paragraph(f"<b>問K</b> {C.QK_HEAD}", st_drill_label))
    k_ans = [
        ("① 言い過ぎ", "本文は「よい影響を与えることがある」と控えめに述べているのに、選択肢は「必ずすべて解決」と強めすぎ。「すべて・必ず・〜しさえすれば」は言い過ぎのサイン。"),
        # FIX-343
        ("④ 対比のズレ", "「便利」は都会側の内容。対比のA(都会＝便利)とB(田舎＝自然)を取り違えている。＊「本文と逆」(③)にも見えるが、③と④の両方に当てはまりそうなときは、対立するAとBを取り違えているなら④を優先する。③は、因果の逆転など、対比の取り違え以外の「逆」に使う。"),
        ("③ 因果が逆", "本文は「睡眠(原因)→集中力(結果)」。選択肢は「集中力(原因)→睡眠(結果)」と、原因と結果が入れかわっている。"),
        ("⑤ 主語のズレ", "なつかしんでいるのは筆者であって祖母ではない。「誰が」がすりかわっている。"),
        ("② 本文にない", "映画化も世界中の人気も、本文にはひと言も書かれていない。もっともらしくても、本文に無ければ切る。"),
    ]
    for (body, sel), (ans, kai) in zip(C.Q_K_ITEMS, k_ans):
        E += kaito_item([body, "　" + sel], ans, kai)

    E.append(Paragraph(f"<b>問L</b> {C.QL_HEAD}", st_drill_label))
    E.append(Paragraph(f"　{C.QL_CHOICES}", st_body))
    l_ans = [
        ("イ", "丸める・底に押しこむ＝結果を視界から消したい行動。悔しさ・見たくない気持ちの表れ。心情が直接書かれていなくても、行動から読み取れる。"),
        ("ウ", "「何度も何度も見比べる」＝にわかには信じられず、確かめずにはいられない気持ちの表れ。"),
        ("ア", "立ちつくす(行動)に、「冷たい風」という情景が重なる。情景描写は心情を映す鏡。別れの寂しさ・心細さを表している。"),
    ]
    for it, (ans, kai) in zip(C.Q_L_ITEMS, l_ans):
        E += kaito_item([it], ans, kai)

    # ---------- 大問 解答と解説 ----------
    def sekkei(rows):
        return grid_table(["段落", "内容の要点", "論理の働き"], rows,
                          [CW * 0.12, CW * 0.56, CW * 0.32],
                          span_title="本文の設計図 ― 段落ごとの論理の働き")

    def desc_q(label, key, ans, logic, kai):
        block = qblock(label, C.Q_TEXTS[key])
        block.append(Paragraph(f"<b>解答例</b>　{ans}", st_ans))
        block.append(Paragraph(f"★ 使う論理　{logic}", st_logic))
        block.append(Paragraph(f"<b>解説</b>　{kai}", st_kai))
        block.append(Spacer(1, 6))
        return [KeepTogether(block)]

    def mc_q(label, key, logic, kai):
        block = qblock(label, C.Q_TEXTS[key])
        block += mc_choices_answer(key)
        block.append(Paragraph(f"★ 使う論理　{logic}", st_logic))
        block.append(Paragraph(f"<b>解説</b>　{kai}", st_kai))
        block.append(Spacer(1, 6))
        return [KeepTogether(block)]

    # 第一問
    E.append(PageBreak())
    E += band("第一問　解答と解説", None)
    E += sekkei([
        ["第一", "「思い→言葉」という通念を示し、「しかし」で退けて逆の主張を立てる", "対立(通念⇔主張)"],
        ["第二", "虹の色の例。色を区切っているのは言葉だと具体で示す", "具体例(イコール)"],
        ["第三", "「つまり」で主張をまとめる。言葉が考える枠組みを与える", "主張のまとめ(イコール)"],
    ])
    E += desc_q("問1", "1-1",
        "頭の中にまず思いがあって、それを言葉に置きかえて話しているという考え。",
        "主語述語 ＋ 指示語 ＋ 対立関係",
        "傍線部①は「しかし」の直後にある。対立関係では、「しかし」の前に否定される内容が置かれる。直前の一文の主語述語をつかむと「私たちは…考えている」＝一般に信じられている考え。筆者はこれを「単純」だと退け、直後で反対の主張(むしろ言葉があるから考えられる)を述べている。")
    E += desc_q("問2", "1-2",
        "境目のない連続した世界に、言葉が境界線を引いて区切っている(＝言葉が世界を区切り、考える枠組みを与えている)という考え。",
        "イコールの関係(具体と抽象)",
        "「たとえば」は具体例の目印。具体例は、抽象的な主張を分かりやすく示すために置かれる(具体と抽象＝イコールの関係)。虹の段落の後半で「境界線を引き、いくつかの色として区切っているのは…言葉なのだ」と抽象化されている。この具体例が示している抽象的な主張を答える。")
    E += mc_q("問3", "1-3",
        "イコールの関係(主張の言い換え) ＋ 文章全体の論理構造",
        "筆者の主張は言い換えられて繰り返される。最終段落「つまり…」以降が主張のまとめで、傍線部③「言葉こそが…考えるための枠組みそのものを与えている」がそれ。アがこの言い換えになっている。イ＝本文が退けた「乗り物(道具)」説。ウ＝「考える力が劣っている」は本文にない話(型②)。エ＝本文は虹を「境目のない連続」だと述べ、色名の少ない言語では二・三色に区切るとも言うので、「どの言語でも本来は七色」は本文と正反対(型③)。")

    # 第二問
    E.append(PageBreak())
    E += band("第二問　解答と解説", None)
    E += sekkei([
        ["第一", "便利さを定義し、それを疑いようのない善だとする通念を示す", "定義(イコール)＋通念"],
        ["第二", "「しかし」で通念を退ける。手紙とメッセージの対比で、便利さが失うものを示す", "対立＋具体例"],
        ["第三", "「もちろん…ではない/そうではなく…べきだ」の譲歩で主張を述べる", "譲歩逆接(主張)"],
        ["第四", "本当に問うべき問いを示して結ぶ", "主張のまとめ(因果)"],
    ])
    E += desc_q("問1", "2-1",
        "ある目的にたどり着くまでの手間や時間を減らすこと。",
        "イコールの関係(定義・言い換え)",
        "「便利さとは、～ことだ」という形は、語をイコールで定義する言い方。傍線部①そのものが定義になっているので、その部分を過不足なく抜き出す。定義は「AとはBだ」の形(イコールの関係)で示されることが多い。＊この問いは、出口式の基本「答えは本文にある。拾ってくる」を体で覚えるためのもの。")
    E += desc_q("問2", "2-2",
        "手間が省かれることで、その手間の中にあったはずの経験もまた失われてしまうから。",
        "因果関係",
        "傍線部②の直後に「～だからだ」とあり、これは理由を示す因果の目印。「なぜか」と問われたら、因果の目印(だから・なぜなら・ので・ため)を本文で探す。直後の一文がそのまま理由になっている。文末は「～から。」で結ぶ。")
    E += mc_q("問3", "2-3",
        "対立関係(対比) ＋ 具体と抽象",
        "手紙⇔メッセージは対比(対立関係)。対比は、片方を際立たせて筆者の主張を示すために使われる。「ところが」「だが」を境に、メッセージは速い(長所)が「間」を消す(短所)と述べられ、段落の結び「手間の中で育っていた何か」を失うという抽象的主張につながる。ウがこれと一致。ア・エは本文にない話(型②本文にない)。イは「あらゆる面で」と本文より強く言い切り、メッセージの短所(「間」を消す)を無視している(型①言い過ぎ)。")
    E += mc_q("問4", "2-4",
        "イコールの関係(言い換え) ＋ 因果関係",
        "傍線部③は直前の一文「便利になればなるほど、人は自分の力では何もできなくなっていく」の言い換え(イコール)。「道具が有能に」＝便利になる、「人間が無能に」＝自分では何もできなくなる、を「表と裏」と表現している。イがこの言い換え。ウは「道具が高性能になるほど人間も有能になる」と述べており、本文(便利になるほど人は自分の力で何もできなくなる)と正反対(型③因果が逆)。ア・エは本文にない話。")
    E += mc_q("問5", "2-5",
        "文章全体の論理構造 ＋ 譲歩逆接から主張を見極める",
        "第三段落の「そうではなく、～もっと自覚的であるべきだ」、第四段落の「本当に問うべきは…『何を手放すのか』である」が筆者の主張。エがその言い換え。ア＝筆者は第三段落冒頭で「昔に帰れと言いたいのではない」と明確に否定している(型③本文と逆)。イ＝本文が退けた通念。ウ＝本文にない話(型②)。主張は、譲歩(もちろん…ない)の後の「そうではなく…べきだ」に現れることが多い。")

    # 第三問
    E.append(PageBreak())
    E += band("第三問　解答と解説", None)
    E += sekkei([
        ["第一", "「調べれば十分・暗記は無駄」という通念。「確かに…かもしれない」と一度認める", "譲歩"],
        ["第二", "「しかし」で反転。情報⇔知識を定義して対比する", "対立＋定義(イコール)"],
        ["第三", "年号の例。情報を知識に変えるのは「考える手間」だと示す", "具体例(イコール)"],
        ["第四", "「調べれば分かる」の落とし穴＝情報を知識と錯覚すること", "因果(主張の展開)"],
        ["第五", "知識は集める量でなく深くつなげて育つ、とまとめる", "主張のまとめ(対立＋イコール)"],
    ])
    # FIX-3Q1
    E += mc_q("問1", "3-1",
        "イコールの関係(言い換えの接続語)",
        "空欄の前は「情報＝外にある事実の断片」「知識＝内側で結びついたまとまり」という定義。空欄の後「情報は外から与えられ、知識は内側で作り上げる」は、その定義を言い換えて整理し直したもの。同じ内容を別の言葉で言い直すのはイコールの関係だから「言いかえれば」。「ところが」(対立)・「たとえば」(具体例)では前後がつながらない。「だから」(因果)も文としては通らなくはないが、空欄の後ろは新しい結果を導いているのではなく前の内容の言い直しなので、「最も適当」なのは言い換えのイ。")
    E += desc_q("問2", "3-2",
        "情報＝外にある事実の断片で、検索すれば手に入る(外から与えられる)もの。知識＝その断片が自分の中で結びつき、意味のあるまとまりとなった(内側で作り上げる)もの。",
        "対立関係(対比) ＋ 定義(イコール)",
        "情報と知識は第二段落で対比され、それぞれ「～とは、…である」と定義されている(定義＝イコール)。対比の問いは、A列とB列に分けて、両方を本文の言葉でそろえて書くのがコツ。「外から与えられる/内側で作り上げる」という対の表現も入れると、対比がはっきりする。")
    E += desc_q("問3", "3-3",
        "出来事の年号を覚えるだけでは情報を持っているにすぎず、その出来事がなぜ起こり後の時代に何をもたらしたのかを自分の言葉で語れるように考えて、はじめて知識になるということ。",
        "具体と抽象(イコール) ＋ 対立",
        "傍線部①は抽象的な主張。「どういうことか」と問われたら、直前の具体例(歴史の年号)に戻して言い換える。「覚える手間」＝年号を覚えること(＝情報)、「考える手間」＝なぜ起こり何をもたらしたかを自分の言葉で語ること(＝知識)。具体例と対応づけて説明する。")
    E += mc_q("問4", "3-4",
        "因果関係 ＋ イコール(本文の言い換え)",
        "傍線部②の直後が理由。「調べて画面に出てきたものは、まだ情報でしかない」「組み立て直さないかぎり、知識には育たない」「情報を手に入れたことで、知識を得たと錯覚しやすくなる」――この三点をまとめたウが正解。ア(思考力がなくなる)・イ(情報が誤り)・エ(調べる力が身につかない)は、いずれも本文が述べていない別の理由(型②本文にない)。")
    # FIX-3Q5
    E += mc_q("問5", "3-5",
        "文章全体の論理構造 ＋ 譲歩逆接から主張を見極める",
        "第一段落「確かに…かもしれない」は譲歩(いったん認めただけ)。主張は「しかし」以降にあり、最終段落「知識は、多く抱えこむことではなく、深くつなげることによって育つ」「どれだけ自分のものにできたか」がまとめ。アがその言い換え。イ＝譲歩部分(認めただけの内容)を主張と取り違えたひっかけ。ウ＝情報と知識を「同じ」とするが、本文は両者を対比している(型④対比のズレ。AとBの取り違えだけでなく、本文の対比を無いことにするのも対比のズレ)。「どちらもできるだけ多く」も、知識は量ではなく深さで育つという本文の主張と逆。エ＝本文にない話(型②)。")

    # 第四問
    E.append(PageBreak())
    E += band("第四問　解答と解説", None)
    E += grid_table(
        ["きっかけ(出来事)", "心情", "行動・表情・情景"],
        [
            ["苦手な数学の答案が返ってくる", "結果を見るのがこわい・不安", "答案を手に取れない／めくる手が重い"],
            ["百点の由衣に点数を聞かれる", "見られたくない・引け目", "答案を手で隠す／声が硬くなる"],
            ["放課後、七十二点・図形に赤い丸", "努力が報われた静かな満足", "赤い丸を指でなぞる／胸の底が温かい"],
            ["(結末)", "引け目を乗り越え前向きに", "答案を表にしてしまう／明日点数を言おうと思う"],
        ],
        [CW * 0.34, CW * 0.28, CW * 0.38],
        span_title="心情の流れ ― 出来事 → 心情 → 行動・情景",
    )
    E += desc_q("問1", "4-1",
        "昨夜遅くまで苦手な問題を解いて努力したのに、それでも駄目だったらと思うと、答案の結果を見るのがこわく、不安だという心情。",
        "心情把握(出来事→心情) ＋ 因果",
        "心情は「出来事→心情→行動」でたどる。出来事＝苦手な数学の答案が返ってきた／昨夜がんばった。「もし…駄目だったら」という思いから、結果を見るのがこわい・不安という心情が読み取れ、それが「めくる手が重い」という行動に表れている。「努力したのに」という前提も入れると心情が深く書ける。")
    # FIX-42E
    E += mc_q("問2", "4-2",
        "心情把握(行動の理由) ＋ 対比",
        "直前で由衣の答案に「百点」とあり、真希は自分の点数をまだ見てすらいない。百点の由衣と自分を思わず比べ、見られたくないという引け目から、とっさに隠すという行動に出た。イが正解。ア(言いふらす)・ウ(いたずら)は本文にない(型②)。エ「うらやましい・くやしい」という心情は本文のどこにも書かれておらず(型②)、くやしさをおさえるためにとっさに自分の答案を隠す、というつながりも不自然。")
    E += desc_q("問3", "4-3",
        "決して高い点ではないが、いつも半分も取れなかった自分が努力の成果を出せたことへの、単純な喜びとは違う、努力が報われたという静かな満足の気持ち。",
        "心情把握 ＋ 対立(うれしい⇔それとは違う)",
        "「うれしい、というのとは少し違った」は、単純な喜びを打ち消す表現(対立)。直後の「昨夜の自分がむだではなかった」「静かに胸の底が温かくなる」が、その心情の中身。「努力が報われた・満たされた」という静かな実感を、本文の言葉を使って書く。")
    E += mc_q("問4", "4-4",
        "心情把握(情景描写＝心情の投影)",
        "情景描写は人物の心情を映す鏡になっていることが多い。直前の「静かに胸の底が温かくなる」という満たされた心情に、「オレンジ色の光」というあたたかく穏やかな情景が重ねられている。エが正解。ア(寂しさ・後悔)・イ(不満・焦り)・ウ(心細さ・孤独)は、いずれも温かな光の情景とも、直前の『温かくなる』という心情とも合わず、心情の根拠が本文にない(型②。ウは「誰もいない教室」という舞台こそ本文にあるが、心細さ・孤独という心情には根拠がない)。＊夕暮れ＝さびしい、と型どおりに決めつけず、直前の心情に情景を重ねるのがコツ。")
    E += mc_q("問5", "4-5",
        "心情把握(心情の変化) ＋ 対比(隠す⇔表にする)",
        "場面の最初では答案を「手のひらで隠した」のに、最後は「表を上にして」しまい、隠していた点数を由衣に「明日は…言おう」と思う。この行動の対比(隠す⇔表にする)が、由衣への引け目を乗り越えて努力の結果を受け入れ、前向きになった心情の変化を表す。ウが正解。ア＝自分を責め厳しく反省する心情は、直前の「静かに胸の底が温かくなる」という穏やかで満たされた流れと合わない(型②本文にない)。イ(対抗心・百点を取る)・エ(開き直り・意欲を失う)も本文に根拠がない(型②)。")

    doc.build(E)
    print(f"built {path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    build_mondai(os.path.join(out, "出口式_現代文読解ロジック演習_問題編.pdf"))
    build_kaito(os.path.join(out, "出口式_現代文読解ロジック演習_解答解説編.pdf"))
