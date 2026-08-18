#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""難関国公立大 英文法 実戦問題集 — PDF 組版（問題編／解答解説編の2冊）。

  python3 scripts/eng_kokkoritsu_nankan/build.py

★冒頭で check.py の全ゲートを回し、FAIL があれば1バイトも書かずに落ちる。
  （build と insert を「;」でつないだとき、落ちたはずのデータが成果物に行くのを防ぐ）
★出力は一度英数字名で書いてから日本語名へ mv する
  （日本語ファイル名は NFD/NFC 不一致で FileNotFound を起こすため）。
"""
import os
import re
import subprocess
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, HRFlowable, KeepTogether, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

HERE = os.path.dirname(os.path.abspath(__file__))
# ★機械（ゲート・組版・盲検証）は共有し、中身だけ差し替える。
#   WORKBOOK_DIR=<別冊のディレクトリ> を付けて実行すると、そちらの content.py を読む。
BOOK_DIR = os.path.abspath(os.environ.get("WORKBOOK_DIR") or HERE)
sys.path.insert(0, BOOK_DIR)
sys.path.insert(0, os.path.dirname(HERE))

import check as gates                                  # noqa: E402
from content import BOOK, ELEMENT_KINDS                # noqa: E402

DESKTOP = os.path.expanduser("~/Desktop")
TMP_Q = os.path.join(BOOK_DIR, "_out_q.pdf")
TMP_A = os.path.join(BOOK_DIR, "_out_a.pdf")
FINAL_Q = os.path.join(DESKTOP, f'{BOOK["file"]}_問題編.pdf')
FINAL_A = os.path.join(DESKTOP, f'{BOOK["file"]}_解答解説編.pdf')

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FONT = "AU"
pdfmetrics.registerFont(TTFont(FONT, FONT_PATH))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT, italic=FONT, boldItalic=FONT)

NAVY = colors.HexColor("#16324f")
ACCENT = colors.HexColor("#b3402a")
BLUE = colors.HexColor("#2a6db0")
GRAY = colors.HexColor("#8a8a8a")
RULE = colors.HexColor("#c9d4e0")
GOLD = colors.HexColor("#c19b4a")
INK = colors.HexColor("#1a1a1a")

MARGIN = 18 * mm
BODY_W = A4[0] - 2 * MARGIN


def hx(c):
    return "#" + c.hexval()[2:]


_TRANS = {"‘": "'", "’": "'", "“": '"', "”": '"',
          "–": "-", "—": "-", "…": "...", "　": " ",
          # ★同じ「〜」でも U+FF5E と U+301C が混ざると、紙面で字形がはっきり変わる
          #   （実測: 2ページだけ細い ~ になっていた）。片方に寄せる。
          "～": "〜"}


def clean(s):
    s = "" if s is None else str(s)
    for k, v in _TRANS.items():
        s = s.replace(k, v)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)


# ★中黒「・」(U+30FB) はカタカナ範囲の中にあるが、和欧の空白を入れる対象から外す。
#   入れると「GMARCH ・地方国公立」と中黒の前が空いて不格好になる（実測）。
_CJK = r"\u3041-\u309f\u30a1-\u30fa\u30fc-\u30ff\u4e00-\u9fff\u3005"
_PUNC = r"、。「」『』（）・…！？"


def wa_ei(s):
    """和文と欧文の境目に半角スペースを入れる。無いと「用いてIt is」と詰まって読めない。
    ★数字は対象外。日本語では「100点」「2つ」「高1」を空けないうえ、空けると
      そこが改行位置になって「各部は 100 / 点満点で」と助数詞だけ次行に落ちる。"""
    s = re.sub(rf"([{_CJK}])([A-Za-z])", r"\1 \2", s)
    return re.sub(rf"([A-Za-z])([{_CJK}])", r"\1 \2", s)


# 和欧の境目に空白を入れると、そこが改行位置になる。1語として読ませたい
# 組み合わせだけは分割を禁止する（「be／動詞」「-ing／形」で割れて別項目に見えた）。
# ★角括弧は「[」だけが行末に残りやすい。空所そのものごと1かたまりで動かす。
_GLUE = ("be 動詞", "-ing 形", "to 不定詞", "-ed 形", "[  ] 内", "] 内")


def esc(s):
    s = wa_ei(clean(s))
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for g in _GLUE:
        s = s.replace(g, g.replace(" ", "&nbsp;"))
    return s


JA = BOOK.get("lang") == "ja"


def ul(s):
    """古文教材の傍線。stem 中の ＿…＿ を下線に変える（esc の後に呼ぶ）。"""
    return re.sub(r"＿(.+?)＿", r"<u>\1</u>", s)


def nb(n):
    """★reportlab の Paragraph は連続空白を1つに畳む。記入欄の空所はすべて
    &nbsp; で作らないと「( )」まで縮んで書き込めない冊子になる。"""
    return "&nbsp;" * n


def frame_html(it):
    """整序の [    ] を、実際に書き込める幅の空所に置き換える。"""
    return re.sub(r"\[\s*\]", "[" + nb(38) + "]", esc(it["frame"]))


def fill_html(it):
    """空所補充の (    ) / (  i  ) を書き込める幅にする。頭文字ヒントは残す。
    古文教材では ＿…＿ を傍線に変え、全角括弧の空所にも対応する。"""
    def rep(m):
        letter = m.group(1) or ""
        return "（" + (nb(2) + letter if letter else "") + nb(26) + "）"
    return re.sub(r"[（(]\s*([A-Za-z]?)\s*[）)]", rep, ul(esc(it["stem"])))


# ------------------------------------------------------------------ スタイル
def styles():
    S = {}
    S["title"] = ParagraphStyle("t", fontName=FONT, fontSize=25, leading=34,
                                alignment=TA_CENTER, textColor=NAVY)
    S["sub"] = ParagraphStyle("s", fontName=FONT, fontSize=12.5, leading=20,
                              alignment=TA_CENTER, textColor=colors.HexColor("#444"))
    S["cov"] = ParagraphStyle("c", fontName=FONT, fontSize=10.5, leading=18,
                              alignment=TA_CENTER, textColor=GRAY)
    S["part"] = ParagraphStyle("p", fontName=FONT, fontSize=21, leading=30,
                               alignment=TA_CENTER, textColor=NAVY)
    S["partsub"] = ParagraphStyle("ps", fontName=FONT, fontSize=11.5, leading=19,
                                  alignment=TA_CENTER, textColor=colors.HexColor("#444"))
    S["kick"] = ParagraphStyle("k", fontName=FONT, fontSize=9.5, leading=13,
                               textColor=colors.white)
    S["band"] = ParagraphStyle("b", fontName=FONT, fontSize=15, leading=20,
                               textColor=colors.white)
    S["inst"] = ParagraphStyle("i", fontName=FONT, fontSize=10, leading=15.5,
                               textColor=colors.HexColor("#333"), leftIndent=4,
                               spaceBefore=5, spaceAfter=6)
    S["q"] = ParagraphStyle("q", fontName=FONT, fontSize=10.5, leading=17, textColor=INK,
                            leftIndent=17, firstLineIndent=-17, spaceBefore=6, spaceAfter=1)
    S["qs"] = ParagraphStyle("qs", fontName=FONT, fontSize=10.5, leading=17, textColor=INK,
                             leftIndent=17, spaceAfter=1)
    S["tok"] = ParagraphStyle("tk", fontName=FONT, fontSize=10.5, leading=17,
                              textColor=colors.HexColor("#22303c"), leftIndent=17,
                              spaceBefore=1, spaceAfter=2)
    S["a"] = ParagraphStyle("a", fontName=FONT, fontSize=10.5, leading=16, textColor=INK,
                            leftIndent=17, firstLineIndent=-17, spaceBefore=7, spaceAfter=1)
    S["exp"] = ParagraphStyle("e", fontName=FONT, fontSize=9.5, leading=14.5,
                              textColor=colors.HexColor("#333"), leftIndent=17, spaceAfter=1)
    S["pt"] = ParagraphStyle("pt", fontName=FONT, fontSize=9.5, leading=14.5,
                             textColor=BLUE, leftIndent=17, spaceAfter=4)
    S["note"] = ParagraphStyle("n", fontName=FONT, fontSize=10.5, leading=17.5,
                               textColor=colors.HexColor("#333"))
    # 前書き・部扉の地の文は、英語の冊子でも中身が日本語の散文なので禁則を効かせる。
    # ★note そのものに効かせてはいけない。note は表のセルにも使われ、
    #   中学英語の本の活用表のように英単語が入るセルで単語が途中から割れる。
    S["intro"] = ParagraphStyle("in", parent=S["note"], wordWrap="CJK")
    S["h2"] = ParagraphStyle("h2", fontName=FONT, fontSize=12.5, leading=19, textColor=NAVY,
                             spaceBefore=9, spaceAfter=2)
    return S


S = styles()

# ★日本語の冊子だけ CJK 折り返しにする。reportlab は既定だと長い CJK 語を
#   文字単位で機械的に割るだけで禁則を見ないので、行頭に「。」「、」「）」が来る
#   （実測: 古文の解答解説編で 2000行中 43行）。wordWrap="CJK" にすると
#   reportlab 内蔵の ALL_CANNOT_START が効いて行頭禁則が守られる。
#   英語の冊子に効かせると単語の途中で割れるので、lang で切り分ける。
if BOOK.get("lang") == "ja":
    for _k in ("q", "qs", "tok", "a", "exp", "pt", "note", "inst", "kick", "partsub"):
        if _k in S:
            S[_k].wordWrap = "CJK"
# ★部扉の説明文（p["aim"]）だけは、英語の冊子でも中身が純日本語の長文なので禁則を効かせる。
#   効かせないと行頭に「。」が落ちる（実測1行／全659行）。
#   ★partsub そのものに効かせてはいけない。partsub は解答編の部見出し
#   （「〜レベル　／　100点満点」）にも使われ、CJK 折り返しだと「100点／満点」で割れる
#   （実測: 中堅編の解答編 p2 が退行した）。
S["aim"] = ParagraphStyle("aim", parent=S["partsub"], wordWrap="CJK")

PAGE_SEC = {}
# ★表紙や前書きに「N問」と手で書かない。実データから出す（初版は112問と刷って実際は103問だった）
TOTAL_Q = sum(len(s["items"]) for p in BOOK["parts"] for s in p["sections"])
# ★大きな区切りの単位語。既定は「部」。模試形式の本は content.py で "回" にする。
#   持たせないと、データが「第1回 標準レベル」なのに機械が「第1部」と刷って
#   紙面が「第1部 第1回 標準レベル」と二重表記になる。
UNIT = BOOK.get("unit", "部")
# 採点要素で採る設問（英文和訳・和文英訳）の実数。0 なら解答編の表紙から
# 「採点のポイントつき」を落とす（中身に無いものを表紙が名乗らないように）。
N_ELEMENT = sum(len(s["items"]) for p in BOOK["parts"] for s in p["sections"]
                if s["kind"] in ELEMENT_KINDS)


class Marker(Flowable):
    def __init__(self, label):
        super().__init__()
        self.label, self.width, self.height = label, 0, 0

    def draw(self):
        pass


class Doc(BaseDocTemplate):
    """★ヘッダの大問名は first と last の両方を持たないと必ずズレる。
    ・そのページに大問が始まる → そのページの「最初の」大問（last だと、次の大問の帯が
      ページ末に少しかかっただけでページ全体が次の大問扱いになる）
    ・大問が始まらない続きのページ → 直前ページの「最後の」大問（first を引き継ぐと、
      1ページに大問4と5が同居した次のページが大問4のままになる）"""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.first_on_page, self.last_on_page = {}, {}

    def afterFlowable(self, f):
        if isinstance(f, Marker):
            self.first_on_page.setdefault(self.page, f.label)
            self.last_on_page[self.page] = f.label


def make_on_page(book_label):
    def on_page(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFont(FONT, 8)
        canvas.setFillColor(GRAY)
        canvas.drawString(MARGIN, h - 12 * mm, book_label)
        right = PAGE_SEC.get(doc.page, "")
        if right:
            canvas.drawRightString(w - MARGIN, h - 12 * mm, right)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, h - 14 * mm, w - MARGIN, h - 14 * mm)
        canvas.setFont(FONT, 9)
        canvas.drawCentredString(w / 2, 10 * mm, str(doc.page))
        canvas.restoreState()
    return on_page


def on_cover(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 74 * mm, w, 74 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 76 * mm, w, 2 * mm, fill=1, stroke=0)
    canvas.restoreState()


# ------------------------------------------------------------------ 部品
def band(kicker, title):
    t = Table([[Paragraph(esc(kicker), S["kick"])], [Paragraph(esc(title), S["band"])]],
              colWidths=[BODY_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (0, 0), 7), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (0, 1), 9),
    ]))
    return t


def conj_table(t):
    """助動詞の活用表。★単一セルTableに全体を包むとページ超過で分割できず LayoutError に
    なるので、行ごとに分割できる複数行 Table にする（古文ルールブックで踏んだ罠）。"""
    head = [Paragraph(f'<font size=8.5>{esc(h)}</font>', S["note"]) for h in t["headers"]]
    body = [[Paragraph(f'<font size=8.5>{esc(c)}</font>', S["note"]) for c in row]
            for row in t["rows"]]
    # ★列幅は表ごとに持たせる。9列の助動詞表の幅を8列の用言表や4列の音便表に
    #   使い回すと、セルが縦に潰れて「シク活/用 補助/活用」のように折れる。
    n = len(t["headers"])
    w = t.get("widths") or [212 // n] * n           # 合計 212pt ≒ 174mm
    if len(w) != n:
        raise SystemExit(f'表「{t["title"]}」の widths が列数({n})と合わない: {w}')
    tb = Table([head] + body, colWidths=[x * 0.82 * mm * 1.0 for x in w], repeatRows=1)
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tb


def rule(w_ratio=1.0, space=7):
    return HRFlowable(width=f"{int(w_ratio*100)}%", thickness=0.6, color=RULE,
                      spaceBefore=space, spaceAfter=space, hAlign="LEFT")


def answer_lines(n=2, indent=17):
    """記述解答欄。★行間は手書きの英文が収まる 9mm 前後にする。
    reportlab 既定の詰め方だと3本が1cmに収まって書き込めない欄になる。"""
    out = [Spacer(1, 2)]
    for _ in range(n):
        out.append(HRFlowable(width=BODY_W - indent, thickness=0.5,
                              color=colors.HexColor("#bfc9d4"),
                              spaceBefore=25, spaceAfter=0, hAlign="RIGHT"))
    out.append(Spacer(1, 6))
    return out


CIRCLED = ["①", "②", "③", "④", "⑤"]


def mc_stem_html(it):
    """四択の空所を、選択肢を書き込める幅にする。古文なら傍線も引く。"""
    s = ul(esc(it["stem"]))
    return re.sub(r"[（(]\s*[）)]", "（" + nb(12) + "）", s)


def error_stem_html(it):
    s = esc(it["stem"])
    for i, ch in enumerate("abcd"):
        s = s.replace("{%s}" % ch,
                      f'<font color="{hx(ACCENT)}">({ch})</font><u>{esc(it["parts"][i])}</u>')
    return s


def completed_sentence(it):
    """整序の frame の [ ] に解答を差し込んだ完成文。

    ★問題編は「文頭に来るべき語も小文字で示す」約束なので ans は小文字始まりだが、
      解答編に載せる完成文は模範解答なので文頭を大文字に戻す。戻さないと
      「no matter what happens, we will not …」と誤った英語を模範解答として刷る。
    """
    s = re.sub(r"\[\s*\]", esc(it["ans"]), esc(it["frame"]))
    return re.sub(r"^([a-z])", lambda m: m.group(1).upper(), s.lstrip())


def fill_note(it):
    """★注記の中で折り返すと「（n」だけが行末に残り、「で始まる語）」が次行に落ちる。
    注記はひとかたまりで動かす（空白は全部 &nbsp; にする）。"""
    def one(s):
        return f'<font size=9 color="{hx(GRAY)}">{s}</font>'
    if it.get("given"):
        return one("（" + esc(it["given"]).replace(" ", "&nbsp;") + "）")
    if it.get("hint"):
        return one(f'（{esc(it["hint"])}&nbsp;で始まる語句）')
    return ""


def _cover_pts():
    """表紙の満点表記。★「各部100点満点」と決め打ちすると、部ごとに満点が違う本で
    表紙だけが嘘になる（表紙の数字はデータから出す。過去に問数で同じ事故を出した）。"""
    tots = sorted({p["total"] for p in BOOK["parts"]})
    return f"各{UNIT}{tots[0]}点満点" if len(tots) == 1 \
        else f"計{sum(p['total'] for p in BOOK['parts'])}点"


# ------------------------------------------------------------------ 問題編
def flow_questions():
    f = [Spacer(1, 66 * mm),
         Paragraph(esc(BOOK["title"]), S["title"]),
         Spacer(1, 7 * mm),
         Paragraph("問 題 編", S["sub"]),
         Spacer(1, 3 * mm),
         Paragraph(esc(BOOK["sub"]), S["sub"]),
         Spacer(1, 3 * mm),
         Paragraph(f"全{len(BOOK['parts'])}{UNIT}・{TOTAL_Q}問／{_cover_pts()}", S["sub"]),
         Spacer(1, 34 * mm),
         Paragraph(esc(BOOK["series"]), S["cov"]),
         NextPageTemplate("normal"), PageBreak()]

    f.append(Marker("本書の使い方"))
    f.append(Paragraph("本書の使い方", S["part"]))
    f.append(Spacer(1, 6 * mm))
    for h, b in BOOK["intro"]:
        # ★本文に改行があれば1行ずつ組む。1段落に流すと「② 」「③ 」だけが
        #   行末に取り残されて、箇条書きに見えない（番号を付けても意味がない）。
        # ★見出しと本文1行目は KeepTogether で括る（見出しだけがページ末に残るのを防ぐ）。
        body = [Paragraph(esc(_line), S["intro"]) for _line in str(b).split("\n")]
        f.append(KeepTogether([Paragraph(esc(h), S["h2"])] + body[:1]))
        f.extend(body[1:])
    f.append(rule())
    # ★見出し・導入文はここで append しない。下の KeepTogether が同じ2行を持っており、
    #   両方あると 2ページにわたって二度刷られる（実際に p2 末尾と p3 冒頭に出た）。
    # 講義対応の本では「対応講義」列を出す（p["ref"] があるときだけ）
    ref = any(p.get("ref") for p in BOOK["parts"])
    rows = [[UNIT, "レベル"] + (["対応講義"] if ref else []) + ["問数", "満点", "目安時間"]]
    for p in BOOK["parts"]:
        n = sum(len(s["items"]) for s in p["sections"])
        rows.append([f'第{p["no"]}{UNIT}', p["level"]] + ([p.get("ref", "")] if ref else [])
                    + [f"{n}問", f'{p["total"]}点', f'{p["time"]}分'])
    cw = ([16 * mm, 52 * mm, 26 * mm, 16 * mm, 16 * mm, 20 * mm] if ref
          else [18 * mm, 46 * mm, 20 * mm, 20 * mm, 24 * mm])
    t = Table([[Paragraph(f'<font size=9.5>{esc(c)}</font>', S["note"]) for c in r]
               for r in rows], colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    # ★見出し＋表を KeepTogether で括る。括らないと、前書きが長い本で表が改ページ位置に
    #   かかり、1行目だけ前ページに残って次ページが「見出し行＋残り2行」の白紙同然になる
    #   （実測: 前書きを1節足しただけで 91字のページが1枚生まれた）。
    f.append(KeepTogether([Paragraph(f'全{len(BOOK["parts"])}{UNIT}の構成と目安時間', S["h2"]),
                           Paragraph("上から順に解いてください。"
                                     f'前の{UNIT}で8割取れてから次の{UNIT}へ進みます。', S["intro"]),
                           Spacer(1, 2 * mm), t]))
    # 前書きが長い本では、この表だけが1ページに独立して大半が白紙になる。
    # 表のあとに置きたい案内があれば続けて組む（無い本は今までどおり）。
    # ★見出しと本文を KeepTogether で括る。括らないと見出しだけがページ末に取り残される
    #   （実測: 「この問題集で扱う範囲」が p2 の最終行で、本文は p3 頭から始まっていた）。
    for h, b in BOOK.get("after_table", []):
        f.append(KeepTogether([Paragraph(esc(h), S["h2"])]
                              + [Paragraph(esc(_line), S["intro"])
                                 for _line in str(b).split("\n")]))
    f.append(PageBreak())

    for p in BOOK["parts"]:
        f.append(Marker(f'第{p["no"]}{UNIT} {p["level"]}'))
        f.append(Spacer(1, 52 * mm))
        f.append(Paragraph(f'第 {p["no"]} {UNIT}', S["partsub"]))
        f.append(Paragraph(esc(p["level"]), S["part"]))
        f.append(Spacer(1, 5 * mm))
        f.append(Paragraph(esc(p["univ"]), S["partsub"]))
        f.append(Spacer(1, 8 * mm))
        f.append(Paragraph(esc(p["aim"]), S["aim"]))
        f.append(Spacer(1, 14 * mm))
        sc = Table([[Paragraph('<font size=10>目安時間</font>', S["note"]),
                     Paragraph(f'<font size=10>{p["time"]}分</font>', S["note"]),
                     Paragraph('<font size=10>得点</font>', S["note"]),
                     Paragraph(f'<font size=10>{nb(10)}／{p["total"]}点</font>', S["note"])]],
                   colWidths=[26 * mm, 22 * mm, 20 * mm, 40 * mm], hAlign="CENTER")
        # 部扉に「この部の解き方」を三手順で置く（手順だけなので答えは割れない）
        if p.get("steps"):
            f.append(Spacer(1, 6 * mm))
            f.append(Paragraph(f'<font color="{hx(NAVY)}">この{UNIT}の解き方</font>', S["h2"]))
            for i, st in enumerate(p["steps"], 1):
                f.append(Paragraph(f'<font color="{hx(NAVY)}">{i}.</font> {esc(st)}', S["q"]))
            f.append(Spacer(1, 8 * mm))
        sc.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, RULE),
                                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#eef2f7")),
                                ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#eef2f7")),
                                ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        f += [sc, PageBreak()]

        for s in p["sections"]:
            pts = len(s["items"]) * s["pt"]
            # ★見出し＋指示文だけを1かたまりにすると、ページ末尾に見出しだけが
            #   ぶら下がって小問は次ページ、という紙面が出る（実測2か所）。
            #   第1問まで含めて1かたまりにする。
            head = [band(f'第{p["no"]}{UNIT} {p["level"]}',
                         f'大問 {s["no"]}　{s["title"]}　（各{s["pt"]}点・計{pts}点）'),
                    Paragraph(esc(s["inst"]), S["inst"])]
            for i, it in enumerate(s["items"], 1):
                # ★番号のうしろを半角スペースにすると、そこが改行位置になって
                #   「2.」だけが行に取り残される（日本語の設問文で実際に出た）。
                no = f'<font color="{hx(NAVY)}">{i}.</font>&nbsp;'
                blk = []
                if s["kind"] == "mc":
                    blk.append(Paragraph(no + mc_stem_html(it), S["q"]))
                    # ★選択肢の中の空白で折り返すと、丸数字だけが行末に残ったり
                    #   選択肢が途中で割れて境目が読めなくなる。1つの選択肢は折らない。
                    blk.append(Paragraph(nb(4) + nb(3).join(
                        f'{CIRCLED[i]}&nbsp;' + esc(ch).replace(" ", "&nbsp;")
                        for i, ch in enumerate(it["choices"])), S["qs"]))
                elif s["kind"] == "error":
                    blk.append(Paragraph(no + error_stem_html(it), S["q"]))
                    # ★「正しい形」は語順ごと直す設問だと30字前後になる。行内の
                    #   かっこでは物理的に書けないので、記号だけかっこにして罫線を1本置く。
                    blk.append(Paragraph(
                        f'<font size=9.5 color="{hx(GRAY)}">記号（{nb(4)}）{nb(4)}'
                        f'正しい形</font>', S["qs"]))
                    blk += answer_lines(1)
                elif s["kind"] == "order":
                    blk.append(Paragraph(no + esc(it["ja"]), S["q"]))
                    blk.append(Paragraph(frame_html(it), S["qs"]))
                    blk.append(Paragraph(
                        "[ " + " / ".join(esc(t) for t in sorted(it["tokens"], key=str.lower))
                        + " ]", S["tok"]))
                    # ★[ ] の内寸では解答が入りきらない（最長37字に対し約3.9cm）。
                    #   実際に紙で書かせるので記入用の罫線を1本置く。
                    blk += answer_lines(1)
                elif s["kind"] == "ident":
                    blk.append(Paragraph(no + ul(esc(it["stem"])), S["q"]))
                    blk += answer_lines(1)
                elif s["kind"] == "fill":
                    blk.append(Paragraph(no + fill_html(it) + " " + fill_note(it), S["q"]))
                elif s["kind"] == "rewrite":
                    blk.append(Paragraph(no + esc(it["src"]), S["q"]))
                    blk.append(Paragraph(
                        f'<font size=9.5 color="{hx(GRAY)}">（{esc(it["inst"])}）</font>',
                        S["qs"]))
                    blk += answer_lines(2)
                elif s["kind"] == "jtrans":
                    blk.append(Paragraph(
                        no + f'<font color="{hx(GRAY)}">{esc(it["context"])}</font> '
                        + f'<u>{ul(esc(it["src"]))}</u>', S["q"]))
                    blk += answer_lines(4)
                elif s["kind"] == "trans":
                    blk.append(Paragraph(no + esc(it["ja"]), S["q"]))
                    blk += answer_lines(3)
                # ★1問は必ず同一ページに。日本語文だけ前ページに残って英文が次ページ、
                #   という分断が実際に出た（p4末→p5頭）。
                f.append(KeepTogether(head + blk if i == 1 else blk))
            f.append(Spacer(1, 4 * mm))
        f.append(PageBreak())
    return f


# ------------------------------------------------------------------ 解答編
def flow_answers():
    f = [Spacer(1, 66 * mm),
         Paragraph(esc(BOOK["title"]), S["title"]),
         Spacer(1, 7 * mm),
         Paragraph("解 答 ・ 解 説 編", S["sub"]),
         Spacer(1, 3 * mm),
         # ★「採点のポイント」は英文和訳・和文英訳の採点要素のこと。その形式を持たない本で
         #   刷ると、表紙が中身に無いものを名乗る（実測: 四択・整序・誤り指摘だけの本で出ていた）。
         # ★ELEMENT_KINDS の宣言ではなく実際の設問数で判定する。宣言はどの本も
         #   ("trans","jtrans") と書いてあるだけで、その設問が入っている保証にならない。
         Paragraph("採点のポイントつき" if N_ELEMENT else "全問くわしい解説つき", S["sub"]),
         Spacer(1, 38 * mm),
         Paragraph(esc(BOOK["series"]), S["cov"]),
         NextPageTemplate("normal"), PageBreak()]

    # ★解答解説編の巻頭に「基本の確認」＝一覧表・活用表・覚え方・識別フロー。
    #   問題編に置くと接続を問う設問が表を写すだけで解けるので、必ずこちら側に置く。
    if BOOK.get("tables") or BOOK.get("flows"):
        f.append(Marker("基本の確認"))
        f.append(Paragraph("基本の確認", S["part"]))
        f.append(Paragraph("接続・活用・意味の一覧と、覚え方、識別のフローチャート",
                           S["partsub"]))
        f.append(Spacer(1, 5 * mm))
        for t in BOOK.get("tables", []):
            f.append(Paragraph(esc(t["title"]), S["h2"]))
            f.append(Paragraph(esc(t["lead"]), S["exp"]))
            f.append(Spacer(1, 2 * mm))
            f.append(conj_table(t))
            if t.get("note"):
                f.append(Paragraph(f'<font size=9>{esc(t["note"])}</font>', S["pt"]))
        for fl in BOOK.get("flows", []):
            f.append(Paragraph(esc(fl["title"]), S["h2"]))
            for i, st in enumerate(fl["steps"], 1):
                # ★例文を本文に流し込むと行途中で割れて、どこまでが例文か読めない。
                #   改行があれば1行ずつ組む（無い本は今までどおり1段落）。
                for j, _line in enumerate(str(st).split("\n")):
                    _h = (f'<font color="{hx(NAVY)}">{i}.</font>&nbsp;' if j == 0 else nb(4))
                    f.append(Paragraph(_h + esc(_line), S["exp"]))
            if fl.get("warn"):
                f.append(Paragraph(f'<font size=9>{esc(fl["warn"])}</font>', S["pt"]))
        f.append(PageBreak())

    for p in BOOK["parts"]:
        f.append(Marker(f'第{p["no"]}{UNIT} {p["level"]}'))
        f.append(Paragraph(f'第{p["no"]}{UNIT}　{p["level"]}', S["part"]))
        f.append(Paragraph(f'{p["univ"]}　／　{p["total"]}点満点', S["partsub"]))
        f.append(Spacer(1, 5 * mm))

        for s in p["sections"]:
            # ★見出しバンドは第1問と同じかたまりにする。バンドだけがページ末に残り、
            #   問1が次ページ頭から始まる紙面が実際に出た（解答解説編 p20）。
            bandhead = [band(f'第{p["no"]}{UNIT} 解答・解説',
                             f'大問 {s["no"]}　{s["title"]}　'
                             f'（各{s["pt"]}点）')]
            for i, it in enumerate(s["items"], 1):
                no = f'<font color="{hx(NAVY)}">{i}.</font>&nbsp;'
                blk = []
                if s["kind"] == "mc":
                    blk.append(Paragraph(
                        f'{no}<font color="{hx(ACCENT)}">{CIRCLED[it["ans"]]} '
                        f'{esc(it["choices"][it["ans"]])}</font>', S["a"]))
                elif s["kind"] == "error":
                    blk.append(Paragraph(
                        f'{no}<font color="{hx(ACCENT)}">'
                        f'（{"abcd"[it["ans"]]}）{esc(it["fix"])}</font>', S["a"]))
                elif s["kind"] == "order":
                    # ★空所が文頭に来る問は ans が小文字始まりなので、解答行も大文字に戻す。
                    #   戻さないと、同じ設問で解答行「no matter what happens」と
                    #   完成文「No matter what happens, …」が食い違って刷られる。
                    _a = it["ans"]
                    if it["frame"].lstrip().startswith("[") and _a[:1].islower():
                        _a = _a[0].upper() + _a[1:]
                    blk.append(Paragraph(
                        f'{no}<font color="{hx(ACCENT)}">{esc(_a)}</font>', S["a"]))
                    blk.append(Paragraph(
                        f'<font size=9.5 color="#555">完成文: {completed_sentence(it)}</font>',
                        S["exp"]))
                elif s["kind"] in ("fill", "ident"):
                    alt = it.get("accept") or []
                    tail = (f'　<font size=9 color="{hx(GRAY)}">［可: '
                            + " / ".join(esc(a) for a in alt) + "］</font>") if alt else ""
                    blk.append(Paragraph(
                        f'{no}<font color="{hx(ACCENT)}">{esc(it["ans"])}</font>{tail}', S["a"]))
                elif s["kind"] == "rewrite":
                    blk.append(Paragraph(
                        f'{no}<font color="{hx(ACCENT)}">{esc(it["ans"])}</font>', S["a"]))
                    for a in (it.get("accept") or []):
                        blk.append(Paragraph(
                            f'<font size=9.5 color="#555">別解: {esc(a)}</font>', S["exp"]))
                elif s["kind"] in ("trans", "jtrans"):
                    q = it["ja"] if s["kind"] == "trans" else it["src"]
                    blk.append(Paragraph(f'{no}<font color="{hx(GRAY)}">{esc(q)}</font>',
                                         S["a"]))
                    blk.append(Paragraph(
                        f'<font color="{hx(ACCENT)}">模範解答: {esc(it["model"])}</font>',
                        S["exp"]))
                    for a in it["alts"]:
                        blk.append(Paragraph(
                            f'<font size=9.5 color="#555">別解: {esc(a)}</font>', S["exp"]))
                    rows = [[Paragraph(f'<font size=9>採点のポイント（{s["pt"]}点満点）</font>',
                                       S["note"]),
                             Paragraph('<font size=9>配点</font>', S["note"])]]
                    for k, pt in it["elements"]:
                        rows.append([Paragraph(f'<font size=9>{esc(k)}</font>', S["note"]),
                                     Paragraph(f'<font size=9>{pt}点</font>', S["note"])])
                    t = Table(rows, colWidths=[BODY_W - 36 * mm, 16 * mm], hAlign="RIGHT")
                    t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
                        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]))
                    blk += [Spacer(1, 2), t, Spacer(1, 3)]

                blk.append(Paragraph(f'<font size=9.5>{esc(it["exp"])}</font>', S["exp"]))
                if it.get("point"):
                    # ★前書きが「間違えた問題がどの単元かを確かめる」と指示しているので、
                    #   各問に単元番号を出す（無い本では今までどおり出さない）。
                    u = str(it.get("unit") or "")
                    tag = (f'〔単元{u[1:]}〕' if u.startswith("U") and u[1:].isdigit()
                           else ("〔総合〕" if u else ""))
                    blk.append(Paragraph(f'▶ {tag}{esc(it["point"])}', S["pt"]))
                # ★1問＝模範解答・別解・採点表・解説をまとめて1かたまり。
                #   表だけを avoid にしていたため、模範解答が前ページ・採点表が次ページに
                #   分かれ、突き合わせられない紙面が出た（解答解説編 p21→p22）。
                f.append(KeepTogether(bandhead + blk if i == 1 else blk))
            f.append(Spacer(1, 3 * mm))
        f.append(PageBreak())
    return f


# ------------------------------------------------------------------ ビルド
def build(path, flow_fn, label):
    """2パス。1パス目でページ→見出し対応を採取し、2パス目でヘッダに刻む。"""
    global PAGE_SEC
    for pass_no in (1, 2):
        doc = Doc(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                  topMargin=20 * mm, bottomMargin=16 * mm, title=label)
        frame = Frame(MARGIN, 16 * mm, BODY_W, A4[1] - 36 * mm, id="f",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        doc.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=on_cover),
            PageTemplate(id="normal", frames=[frame], onPage=make_on_page(label)),
        ])
        doc.build(flow_fn())
        if pass_no == 1:
            sec, last = {}, ""
            for pg in range(1, doc.page + 1):
                sec[pg] = doc.first_on_page.get(pg, last)
                last = doc.last_on_page.get(pg, last)
            PAGE_SEC = sec
    return path


def main():
    print("── 機械ゲート ──")
    if not gates.main():
        sys.exit("ゲート FAIL のため PDF を書きません。")
    print("\n── 組版 ──")
    build(TMP_Q, flow_questions, f'{BOOK["title"]} / 問題編')
    build(TMP_A, flow_answers, f'{BOOK["title"]} / 解答・解説編')
    for tmp, final in ((TMP_Q, FINAL_Q), (TMP_A, FINAL_A)):
        subprocess.run(["mv", tmp, final], check=True)
        print(f"  → {final}  ({os.path.getsize(final)/1024:.0f}KB)")


if __name__ == "__main__":
    main()
