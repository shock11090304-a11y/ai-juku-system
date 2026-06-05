#!/usr/bin/env python3
"""AI コーチング活用完全ガイド v2 (2026-05-20)

塾長の既存 PDF (AI_Coaching_Guide.pdf・12P・Trillion English Academy・navy+gold) を
完全模倣して以下を追加:
- CHAPTER 09: 学習管理 + カリキュラム + 保護者ダッシュボード (2P)
- CHAPTER 10: 偏差値推移グラフ (ダミー・景表法配慮) (1P)
- CHAPTER 11: 体験談 3 件 + CTA + 申込フロー (2P)

合計 17 ページ。出力: ~/Desktop/AI_Coaching_Guide_v2.pdf
"""
import os
from pathlib import Path

HOME = Path.home()
FIG_DIR = HOME / "ai-juku-system" / "static" / "docs" / "_figs_v2"
FIG_DIR.mkdir(parents=True, exist_ok=True)
OUT_PDF = HOME / "Desktop" / "AI_Coaching_Guide_v2.pdf"

# ========================================================================
# 偏差値推移グラフ (matplotlib・ダミーだが控えめ数値)
# ========================================================================
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as _fm
import numpy as np
from pathlib import Path as _Path

# --- CJK font for matplotlib (fixes 文字化け / □□ in legend & labels) ---
_CJK_CANDIDATES = [
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',  # macOS, full CJK
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Linux fallback
]
_JP_MPL = 'DejaVu Sans'
for _p in _CJK_CANDIDATES:
    if _Path(_p).exists():
        try:
            _fm.fontManager.addfont(_p)
            _JP_MPL = _fm.FontProperties(fname=_p).get_name()
            break
        except Exception:
            continue
plt.rcParams['font.family'] = _JP_MPL
plt.rcParams['font.sans-serif'] = [_JP_MPL, 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

NAVY = '#1e3a8a'
NAVY_DEEP = '#0a1f44'
GOLD = '#c9a961'
GOLD_LIGHT = '#d4a574'
GRAY = '#888888'
GREEN_BG = '#d4edda'
GREEN_BORDER = '#28a745'
RED_BG = '#f8d7da'
RED_BORDER = '#dc3545'
LIGHT_GRAY_BG = '#f5f5f5'


def fig_hensachi_trend():
    """偏差値推移グラフ (折れ線・gold vs gray・控えめ差分)"""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    months = [0, 3, 6, 9, 12]
    using = [0, 6.5, 10, 14, 16]
    notusing = [0, 1, 2, 2.5, 3]
    ax.plot(months, using, marker='o', linewidth=2.5, color=GOLD,
             label='ai-juku 利用 (1 日 60 分以上の継続)', markersize=8)
    ax.plot(months, notusing, marker='s', linewidth=1.5, color=GRAY,
             linestyle='--', label='非利用 (一般平均)', markersize=6)
    # 数値ラベル
    for x, y in zip(months, using):
        ax.annotate(f'+{y}', (x, y), textcoords='offset points',
                    xytext=(0, 10), ha='center', fontsize=10,
                    fontweight='bold', color=GOLD)
    for x, y in zip(months, notusing):
        ax.annotate(f'+{y}', (x, y), textcoords='offset points',
                    xytext=(0, -15), ha='center', fontsize=9, color=GRAY)
    ax.set_xlabel('継続学習(ヶ月)', fontsize=11)
    ax.set_ylabel('偏差値の伸び', fontsize=11)
    ax.set_title('12ヶ月の偏差値推移(目安)',
                 fontsize=13, fontweight='bold', color=NAVY, pad=12)
    ax.set_xticks(months)
    ax.set_ylim(-2, 22)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.95,
              edgecolor=GRAY)
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    p = FIG_DIR / "fig_hensachi.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_weekly_heatmap():
    """週次学習時間ヒートマップ (使ってる子の例)"""
    fig, ax = plt.subplots(figsize=(8, 3))
    np.random.seed(42)
    # 7 days x 4 weeks のダミー学習分数
    data = np.array([
        [45, 60, 30, 75, 50, 90, 120],  # Week 1
        [50, 55, 60, 70, 45, 80, 100],  # Week 2
        [60, 70, 55, 65, 50, 100, 110], # Week 3
        [55, 60, 70, 65, 80, 95, 130],  # Week 4
    ])
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    im = ax.imshow(data, cmap='YlOrBr', aspect='auto', vmin=0, vmax=140)
    ax.set_xticks(np.arange(len(days)))
    ax.set_yticks(np.arange(len(weeks)))
    ax.set_xticklabels(days, fontsize=10)
    ax.set_yticklabels(weeks, fontsize=10)
    # 数値表示
    for i in range(len(weeks)):
        for j in range(len(days)):
            color = 'white' if data[i, j] > 70 else 'black'
            ax.text(j, i, f'{data[i, j]}m', ha='center', va='center',
                    color=color, fontsize=9, fontweight='bold')
    ax.set_title('Daily study time (minutes) — heatmap example',
                 fontsize=12, fontweight='bold', color=NAVY)
    plt.colorbar(im, ax=ax, label='Minutes/day', pad=0.02)
    plt.tight_layout()
    p = FIG_DIR / "fig_heatmap.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_3step_cycle():
    """学習管理 3 ステップ循環フロー"""
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(7, 4))
    steps = [
        ("Plan", "週次計画 AI 生成", GOLD, 2.5, 3.0),
        ("Record", "1 タップ記録\n streak 連続日数", NAVY, 5.5, 1.5),
        ("Review", "週次グラフで\n振り返り", GOLD_LIGHT, 2.5, 0.0),
    ]
    for title, desc, color, x, y in steps:
        circ = mpatches.Circle((x, y + 0.75), 0.9, color=color, alpha=0.85)
        ax.add_patch(circ)
        ax.text(x, y + 0.95, title, ha='center', va='center',
                fontsize=12, fontweight='bold', color='white')
        ax.text(x, y + 0.45, desc, ha='center', va='center',
                fontsize=8, color='white')
    # Arrows: cycle
    arrows = [
        ((3.4, 3.3), (4.6, 2.3)),   # Plan → Record
        ((5.3, 1.5), (3.4, 0.8)),   # Record → Review
        ((2.3, 0.9), (2.3, 2.6)),   # Review → Plan
    ]
    for (sx, sy), (ex, ey) in arrows:
        ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle='->', color=NAVY, lw=2.5))
    # 中央テキスト
    ax.text(4.0, 1.85, 'Habit', ha='center', va='center',
            fontsize=14, fontweight='bold', color=NAVY_DEEP)
    ax.set_xlim(0, 8)
    ax.set_ylim(-0.5, 4.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Plan → Record → Review = Habit',
                 fontsize=12, fontweight='bold', color=NAVY, pad=10)
    plt.tight_layout()
    p = FIG_DIR / "fig_3step.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_apply_flow():
    """申込フロー 5 step 横並び"""
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(9, 2.5))
    steps = [
        ("1", "Email Input", "30 sec", GOLD),
        ("2", "Magic Link\nLogin", "1 min", NAVY),
        ("3", "Profile\n(grade/goal)", "3 min", GOLD_LIGHT),
        ("4", "Trial Start", "instant", NAVY_DEEP),
        ("5", "Subscribe\n(after 14d / optional)", "1 min", GOLD),
    ]
    for i, (num, label, time, color) in enumerate(steps):
        x = 0.5 + i * 1.8
        # Circle with step number
        circ = mpatches.Circle((x, 1.7), 0.4, color=color, zorder=3)
        ax.add_patch(circ)
        ax.text(x, 1.7, num, ha='center', va='center',
                fontsize=18, fontweight='bold', color='white', zorder=4)
        # Label below
        ax.text(x, 0.95, label, ha='center', va='center',
                fontsize=8.5, fontweight='bold', color=NAVY_DEEP)
        ax.text(x, 0.45, time, ha='center', va='center',
                fontsize=8, color=GRAY, style='italic')
        # Arrow to next
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + 1.3, 1.7), xytext=(x + 0.45, 1.7),
                        arrowprops=dict(arrowstyle='->', color=GOLD, lw=2))
    ax.set_xlim(-0.2, 9.7)
    ax.set_ylim(0, 2.5)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    p = FIG_DIR / "fig_apply_flow.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


print("Generating figures...")
fig_hensachi = fig_hensachi_trend()
fig_heatmap = fig_weekly_heatmap()
fig_3step = fig_3step_cycle()
fig_apply = fig_apply_flow()
print("Figures done.")

# ========================================================================
# reportlab で PDF 構築
# ========================================================================
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
    KeepTogether, HRFlowable, Flowable, Frame, PageTemplate, BaseDocTemplate,
    NextPageTemplate,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

# 日本語フォント
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
JP_GO = 'HeiseiKakuGo-W5'
JP_MI = 'HeiseiMin-W3'

NAVY_C = colors.HexColor('#1e3a8a')
NAVY_DEEP_C = colors.HexColor('#0a1f44')
GOLD_C = colors.HexColor('#c9a961')
GOLD_LIGHT_C = colors.HexColor('#d4a574')
GRAY_C = colors.HexColor('#888888')
LIGHT_GRAY_C = colors.HexColor('#f5f5f5')
GREEN_BG_C = colors.HexColor('#d4edda')
GREEN_BORDER_C = colors.HexColor('#28a745')
RED_BG_C = colors.HexColor('#f8d7da')
RED_BORDER_C = colors.HexColor('#dc3545')

# Styles
def make_styles():
    return {
        'h1': ParagraphStyle('H1', fontName=JP_GO, fontSize=24,
                             textColor=NAVY_DEEP_C, spaceAfter=10,
                             spaceBefore=2, leading=32, keepWithNext=1),
        'h1_chapter': ParagraphStyle('H1ch', fontName=JP_GO, fontSize=11,
                                      textColor=GOLD_C, spaceAfter=2,
                                      keepWithNext=1),
        'h2': ParagraphStyle('H2', fontName=JP_GO, fontSize=15,
                             textColor=NAVY_DEEP_C, spaceAfter=8,
                             spaceBefore=10),
        'h3': ParagraphStyle('H3', fontName=JP_GO, fontSize=12,
                             textColor=NAVY_C, spaceAfter=6, spaceBefore=8),
        'body': ParagraphStyle('Body', fontName=JP_MI, fontSize=10.5,
                               textColor=colors.HexColor('#2c2c2c'),
                               leading=16.5, spaceAfter=6, alignment=TA_LEFT),
        'body_center': ParagraphStyle('BodyC', fontName=JP_MI, fontSize=10.5,
                                       textColor=colors.HexColor('#2c2c2c'),
                                       leading=16.5, spaceAfter=6,
                                       alignment=TA_CENTER),
        'caption': ParagraphStyle('Cap', fontName=JP_MI, fontSize=8,
                                   textColor=GRAY_C, leading=11,
                                   alignment=TA_CENTER, spaceAfter=6,
                                   italic=True),
        'note': ParagraphStyle('Note', fontName=JP_MI, fontSize=8,
                                textColor=GRAY_C, leading=11),
        'cover_title': ParagraphStyle('CoverT', fontName=JP_GO, fontSize=32,
                                       textColor=colors.white,
                                       alignment=TA_CENTER, leading=42),
        'cover_sub': ParagraphStyle('CoverS', fontName=JP_MI, fontSize=12,
                                     textColor=GOLD_C, alignment=TA_CENTER,
                                     leading=18),
        'cover_brand': ParagraphStyle('CoverB', fontName=JP_GO, fontSize=10,
                                       textColor=GOLD_C, alignment=TA_CENTER,
                                       leading=14, letterSpacing=2),
        'cover_brand_sub': ParagraphStyle('CoverBS', fontName=JP_MI, fontSize=9,
                                           textColor=colors.white,
                                           alignment=TA_CENTER, leading=12),
        'cta_white': ParagraphStyle('CTAW', fontName=JP_GO, fontSize=14,
                                     textColor=colors.white, alignment=TA_CENTER,
                                     leading=20),
        'cta_gold': ParagraphStyle('CTAG', fontName=JP_GO, fontSize=20,
                                    textColor=GOLD_C, alignment=TA_CENTER,
                                    leading=26),
    }


# ===== Page Template (ヘッダー + フッター + gold accent) =====
def first_page(canv, doc):
    """表紙: navy 全面 + gold ライン"""
    canv.saveState()
    # navy 全面
    canv.setFillColor(NAVY_DEEP_C)
    canv.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # 上下 gold ライン
    canv.setFillColor(GOLD_C)
    canv.rect(0, A4[1] - 8, A4[0], 4, fill=1, stroke=0)
    canv.rect(0, 4, A4[0], 4, fill=1, stroke=0)
    canv.restoreState()


def later_page(canv, doc):
    """通常ページ: 上 navy line + gold accent / フッター ページ番号"""
    canv.saveState()
    # 上部 navy line + gold accent
    canv.setFillColor(NAVY_DEEP_C)
    canv.rect(0, A4[1] - 12, A4[0], 4, fill=1, stroke=0)
    canv.setFillColor(GOLD_C)
    canv.rect(0, A4[1] - 14, A4[0], 1, fill=1, stroke=0)
    # ヘッダーテキスト
    canv.setFont(JP_GO, 9)
    canv.setFillColor(NAVY_DEEP_C)
    canv.drawString(20 * mm, A4[1] - 22, 'Trillion English Academy')
    canv.drawRightString(A4[0] - 20 * mm, A4[1] - 22, 'AIコーチング活用完全ガイド')
    # 下部 gold ライン + ページ番号
    canv.setFillColor(GOLD_C)
    canv.rect(0, 8, A4[0], 1, fill=1, stroke=0)
    canv.setFillColor(GRAY_C)
    canv.setFont(JP_MI, 8)
    canv.drawString(20 * mm, 12, 'Student Handbook')
    canv.drawRightString(A4[0] - 20 * mm, 12, f'— {doc.page} —')
    canv.restoreState()


# Custom flowable: gold underline (heading 下)
class GoldUnderline(Flowable):
    """Gold accent line drawn UNDER an h1.
    Reserves vertical room (top_pad + thickness + bottom_pad) so a 2-line
    h1 above can never overlap the line. spaceBefore also lifts it clear
    of descenders on the second line."""
    def __init__(self, width=30 * mm, thickness=2,
                 top_pad=4, bottom_pad=8):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.top_pad = top_pad
        self.bottom_pad = bottom_pad
        self.spaceBefore = 4  # extra gap above when h1 wraps to 2 lines

    def wrap(self, *args):
        return (self.width, self.top_pad + self.thickness + self.bottom_pad)

    def draw(self):
        self.canv.setFillColor(GOLD_C)
        # draw at bottom_pad so there is clear space ABOVE the line
        self.canv.rect(0, self.bottom_pad, self.width,
                       self.thickness, fill=1, stroke=0)


# Build PDF
S = make_styles()
doc = BaseDocTemplate(
    str(OUT_PDF), pagesize=A4,
    leftMargin=20 * mm, rightMargin=20 * mm,
    topMargin=28 * mm, bottomMargin=20 * mm,
    title='AIコーチング活用完全ガイド v2',
    author='Trillion English Academy',
)
frame = Frame(doc.leftMargin, doc.bottomMargin,
               doc.width, doc.height, id='main')
cover_template = PageTemplate(id='cover', frames=frame, onPage=first_page)
content_template = PageTemplate(id='content', frames=frame, onPage=later_page)
doc.addPageTemplates([cover_template, content_template])

story = []

# ============================================================
# Page 1: 表紙
# ============================================================
story.append(Spacer(1, 35 * mm))
story.append(Paragraph('TRILLION ENGLISH ACADEMY', S['cover_brand']))
story.append(Paragraph('for students aiming at 東大 / 京大 / 早慶 / 英検',
                        S['cover_brand_sub']))
story.append(Spacer(1, 30 * mm))
story.append(Paragraph('AIコーチング', S['cover_title']))
story.append(Paragraph('活用完全ガイド', S['cover_title']))
story.append(Spacer(1, 6 * mm))
story.append(Paragraph('〜 成績を最短で上げる 7つの鉄則 + 新章 〜', S['cover_sub']))
story.append(Spacer(1, 30 * mm))

# gold horizontal line
class CoverGoldLine(Flowable):
    def wrap(self, *args): return (60 * mm, 4)
    def draw(self):
        self.canv.setFillColor(GOLD_C)
        self.canv.rect(0, 0, 60 * mm, 2, fill=1, stroke=0)

story.append(CoverGoldLine())
story.append(Spacer(1, 8 * mm))

cover_body = ParagraphStyle('CB', fontName=JP_MI, fontSize=11,
                             textColor=colors.white, alignment=TA_CENTER,
                             leading=18)
story.append(Paragraph('本書は、AIコーチングを「答えの製造機」ではなく', cover_body))
story.append(Paragraph('<b><font color="#c9a961">志望校合格まで導く専属コーチ</font></b>として', cover_body))
story.append(Paragraph('使いこなすための実践マニュアルです。', cover_body))
story.append(Spacer(1, 30 * mm))
story.append(Paragraph('Trillion English Academy', S['cover_brand_sub']))
story.append(Paragraph('Student Handbook Series Vol.1 — 2026年5月 改訂版',
                        S['cover_brand_sub']))

story.append(NextPageTemplate('content'))
story.append(PageBreak())

# ============================================================
# Page 2: CHAPTER 00 はじめに (既存テキスト保持)
# ============================================================
story.append(Paragraph('CHAPTER 00', S['h1_chapter']))
story.append(Paragraph('はじめに ─ なぜ「使い方」で成績が決まるのか', S['h1']))
story.append(GoldUnderline(width=30 * mm, thickness=2))
story.append(Spacer(1, 6 * mm))

story.append(Paragraph(
    '君がこれから手にするAIコーチングアプリは、文字通り <b>24時間動く家庭教師</b> です。'
    'しかし─断言しよう。<b>同じツールを使っても、成績が伸びる生徒と、まったく伸びない'
    '生徒に分かれる。</b>その差は才能でもセンスでもない。<b>「使い方」を知っているかどうか、'
    'ただそれだけだ。</b>', S['body']))
story.append(Paragraph(
    '答えを丸写しする生徒は、半年経っても偏差値が1も動かない。一方、本書の方法に従って毎日30分使い'
    '続けた生徒は、3ヶ月で偏差値10以上を上げてきた。本書はその「使い方」を、英文法・長文・英作文・'
    '語彙・試験対策の各分野で具体的に示すマニュアルだ。', S['body']))
story.append(Spacer(1, 4 * mm))

# 伸びない/伸びる 2 列対比
comp_data = [
    ['伸びない使い方', '伸びる使い方'],
    ['・問題を丸投げして「答えは?」\n・解説を読んで「わかった気」\n'
     '・1分で終わらせる\n・AIの言うことを鵜呑み\n・「訳して」で済ませる',
     '・自分の答えとセットで送る\n・「なぜ」を3回掘り下げる\n'
     '・自分の言葉で説明し直す\n・類題を作らせて定着\n・構造(SVOC)を尋ねる'],
]
comp_table = Table(comp_data, colWidths=[80 * mm, 80 * mm])
comp_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), JP_GO, 10),
    ('BACKGROUND', (0, 0), (0, 0), RED_BORDER_C),
    ('BACKGROUND', (1, 0), (1, 0), GREEN_BORDER_C),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, 1), (0, 1), RED_BG_C),
    ('BACKGROUND', (1, 1), (1, 1), GREEN_BG_C),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('FONT', (0, 1), (-1, 1), JP_MI, 10),
]))
story.append(comp_table)
story.append(Spacer(1, 6 * mm))
story.append(Paragraph(
    '本書を読み終わる頃には、君は「AIに何を、どう聞けば自分の英語力が伸びるか」を完全に'
    '理解しているはずだ。─ さあ、始めよう。', S['body_center']))
story.append(PageBreak())

# ============================================================
# Page 3: CHAPTER 01 AIの本質
# ============================================================
story.append(Paragraph('CHAPTER 01', S['h1_chapter']))
story.append(Paragraph('AIコーチングの本質を理解する', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    '<b>AIは「答えをくれる機械」ではない。「思考を整理してくれるパートナー」だ。</b>'
    'この一行を腹に落とせるかどうかが、すべての出発点になる。', S['body']))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph('1-1. なぜ「答えだけ」では成績が上がらないのか', S['h3']))
story.append(Paragraph(
    '英語の入試問題は、解いた問題が二度と出題されない。出題されるのは <b>同じ「型」の別問題</b>'
    'だ。つまり「この問題の答え」を知っても、入試では1点にもならない。必要なのは'
    '<b>「なぜその答えになるのか」を再現可能な手順として理解すること</b>。AIに求めるべきは、'
    'まさにこの「手順」「考え方」「再利用可能な型」である。', S['body']))

# 講師より一言 box
story.append(Spacer(1, 3 * mm))
note_data = [['● 講師より一言\n\n予備校時代、東大文一に合格した生徒の口癖は <b>「先生、なぜそうなるんですか?」</b>'
              'だった。AIに対しても、この一言を投げ続けられる生徒だけが、本物の英語力を手にする。']]
note_table = Table(note_data, colWidths=[160 * mm])
note_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), JP_MI, 10),
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef9e7')),
    ('LINEBEFORE', (0, 0), (0, -1), 4, GOLD_C),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('LEFTPADDING', (0, 0), (-1, -1), 14),
]))
story.append(note_table)
story.append(Spacer(1, 5 * mm))

story.append(Paragraph('1-2. AIの「3つの正しい使い方」', S['h3']))
use3_data = [
    ['①\n思考の壁打ち相手',
     '自分の答え・訳・要約をAIにぶつけ、どこが弱いかを指摘してもらう。頭の中の'
     '「もやもや」を言語化する作業だ。'],
    ['②\n知識の補完者',
     '文法ルールの背景、語源、語法の歴史的経緯など、参考書には載っていない深い説明を'
     '引き出す。'],
    ['③\n無限の演習生成器',
     '解説を理解した直後に「同じポイントの類題を5問」と頼む。市販の問題集を超える、'
     '自分専用の演習が無限に作れる。'],
]
use3_table = Table(use3_data, colWidths=[40 * mm, 120 * mm])
use3_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), JP_MI, 10),
    ('FONT', (0, 0), (0, -1), JP_GO, 10),
    ('TEXTCOLOR', (0, 0), (0, -1), NAVY_C),
    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
]))
story.append(use3_table)
story.append(PageBreak())

# ============================================================
# Page 4: CHAPTER 02 7 つの鉄則
# ============================================================
story.append(Paragraph('CHAPTER 02', S['h1_chapter']))
story.append(Paragraph('成績を最短で上げる ─ 7つの鉄則', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    'ここから先は、毎日の学習で必ず守ってほしい <b>「7つの鉄則」</b>だ。これを徹底するだけで、'
    '君のAI学習は別物に変わる。', S['body']))
story.append(Spacer(1, 4 * mm))

rules = [
    ('01', 'まず自分で解く。話はそれからだ。',
     'どんな問題でも、必ず <b>自分の答えを書いてから</b> AIに見せる。「わからない」のまま'
     '投げるのは禁止。<b>「自分の答え+どこで詰まったか」</b>をセットで送ること。これだけで'
     'AIは『答え』ではなく『君の弱点』への処方箋を返してくる。'),
    ('02', '「なぜ」を3回掘り下げろ。',
     'AIの最初の解説は表面的なことが多い。<b>「なぜそうなる?」「なぜここでthatが必要?」'
     '「なぜこの語順?」</b> と3回掘り下げる。文法・構文の <b>『ルールの裏側』</b>'
     'までたどり着いて初めて、応用が利く知識になる。'),
    ('03', '自分の言葉で説明し直し、AIに添削させろ。',
     'AIの解説を読んだら、その内容を <b>自分の言葉で書き直して</b> AIに送る。「私の理解は'
     'こうですが、合っていますか?」─ これが <b>アウトプット</b> だ。インプットだけでは絶対'
     'に定着しない。'),
    ('04', '理解したら、必ず類題を5問作らせろ。',
     '解説直後の「わかった」は最も忘れやすい状態だ。「同じポイントで難易度別に類題を5問。'
     '答えは隠して」と頼むこと。知識を <b>『使える』状態</b> に持っていく最短ルート。'),
    ('05', '英作文は『3観点添削』を必ず指定しろ。',
     '「添削して」だけでは弱い。<b>① 文法・② 自然さ・③ 入試/英検高得点表現</b> の3観点で'
     '指示を出すこと。さらに「模範解答との差を具体的に」と追加すれば、ほぼ満点答案が手に入る。'),
    ('06', '長文は『訳』ではなく『構造』を尋ねろ。',
     'わからない英文に出会ったら「訳して」と言ってはいけない。<b>「この文のSVOC構造を分析し、'
     '修飾関係を教えて」</b>と聞くこと。構造が見えれば、未知の英文も自力で読めるようになる。'),
    ('07', '1日の終わりに、AIに口頭テストを受けろ。',
     '寝る前の10分、その日に学んだ内容を <b>AIに口頭テスト形式で出題させる</b>。「今日学んだ'
     '仮定法のポイントを、私に質問してください」─ 答えられない箇所が、君の本当の弱点だ。'),
]

rule_rows = []
for num, title, desc in rules:
    cell_l = f'<font color="#ffffff" size="14"><b>RULE</b></font>\n' \
             f'<font color="#c9a961" size="28"><b>{num}</b></font>'
    cell_r = f'<font color="#0a1f44" size="11"><b>{title}</b></font><br/>' \
             f'<font color="#2c2c2c" size="9">{desc}</font>'
    rule_rows.append([Paragraph(cell_l, ParagraphStyle('rl', fontName=JP_GO,
                                                        alignment=TA_CENTER, leading=18)),
                       Paragraph(cell_r, ParagraphStyle('rr', fontName=JP_MI,
                                                         leading=14))])
rule_table = Table(rule_rows, colWidths=[28 * mm, 134 * mm], rowHeights=[20*mm]*7)
rule_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (0, -1), NAVY_DEEP_C),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ('LEFTPADDING', (1, 0), (1, -1), 10),
    ('RIGHTPADDING', (1, 0), (1, -1), 10),
    ('TOPPADDING', (1, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (1, 0), (-1, -1), 6),
    ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#d0d0d0')),
]))
story.append(rule_table)
story.append(PageBreak())

# ============================================================
# Page 5-6: CHAPTER 03 分野別 (英文法 / 長文 + 英作文 / 語彙 / リスニング)
# ============================================================
def quality_box(title, items, color_bg, color_border):
    """良い/悪い質問例 box"""
    content = f'<font color="#0a1f44" size="10"><b>{title}</b></font><br/>'
    content += '<br/>'.join(items)
    p = Paragraph(content, ParagraphStyle('qb', fontName=JP_MI, fontSize=9.5,
                                            leading=15))
    t = Table([[p]], colWidths=[160 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), color_bg),
        ('LINEBEFORE', (0, 0), (0, 0), 3, color_border),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    return t

story.append(Paragraph('CHAPTER 03', S['h1_chapter']))
story.append(Paragraph('分野別 ─ 効果的な使い方', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    'ここからは、英語の各分野でAIをどう使い倒すかを具体的に示す。プロンプト(質問文)はそのまま'
    '真似して構わない。', S['body']))

story.append(Paragraph('■ 英文法 ─ 「ルールの暗記」から「原理の理解」へ', S['h3']))
story.append(Paragraph(
    '文法は『暗記科目』ではなく『論理科目』だ。AIには <b>「なぜそのルールが存在するのか」</b>'
    'を聞き続けること。', S['body']))
story.append(quality_box('◎ 良い質問例', [
    '✓「I wish I had studied harder. が仮定法過去完了になる理由を、時制のズレの原理から説明してください」',
    '✓「以下の私の英作文の文法ミスを、ルール名とともに指摘してください: [自分の英文]」',
    '✓「分詞構文と関係代名詞の使い分けを、入試レベルの例文5つで対比して示してください」',
    '✓「Vintage の◯◯章のテーマで、難易度を上げた応用問題を10問作ってください。答えは別に。」',
], GREEN_BG_C, GREEN_BORDER_C))
story.append(Spacer(1, 3 * mm))
story.append(quality_box('⊠ 悪い質問例', [
    '× 「仮定法ってなに?」(漠然としすぎ。出てくる解説も浅い)',
    '× 「この問題の答えは?」(思考停止。学習価値ゼロ)',
    '× 「文法を全部教えて」(範囲が広すぎて使い物にならない)',
], RED_BG_C, RED_BORDER_C))
story.append(PageBreak())

# Page 6: 長文 / 英作文 / 語彙 / リスニング
story.append(Paragraph('CHAPTER 03', S['h1_chapter']))
story.append(Paragraph('分野別 ─ 効果的な使い方 (続き)', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 4 * mm))

story.append(Paragraph('■ 長文読解 ─ 『訳す』のではなく『構造を見る』', S['h3']))
story.append(Paragraph(
    '長文で詰まる原因の9割は <b>構文が見えていない</b> こと。AIには『構造』を尋ねるクセをつけよう。',
    S['body']))
story.append(quality_box('◎ 良い質問例', [
    '✓「以下の文のSVOCを分析し、修飾関係を矢印で示してください: [難解な一文]」',
    '✓「このパラグラフのトピックセンテンスはどれですか?各文の役割(主張/具体/反証/結論)を分類してください」',
    '✓「タイトルから内容を予測する練習をしたい。タイトル → 予測 → 答え合わせの流れで進めて」',
], GREEN_BG_C, GREEN_BORDER_C))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph('■ 英作文 ─ 『3観点添削』が鉄則', S['h3']))
story.append(quality_box('◎ 良い質問例', [
    '✓「以下の自由英作文を ① 文法・② 自然さ・③ 東大採点基準 の3観点で添削してください」',
    '✓「同じトピックで 『70点答案』『85点答案』『満点答案』 の3レベルを書き分けて」',
], GREEN_BG_C, GREEN_BORDER_C))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph('■ 語彙・熟語 / リスニング ─ 文脈で記憶 + 発音矯正', S['h3']))
story.append(quality_box('◎ 良い質問例', [
    '✓「come up with を使った例文を、難易度別に5つ(英検2級/準1級/1級/東大/京大)作って」',
    '✓「以下の単語10個を、すべて使った短いストーリーを英語で。記憶に残りやすく」',
    '✓「以下のスクリプトを使ったシャドーイング練習を、5段階の難易度でガイドして」',
], GREEN_BG_C, GREEN_BORDER_C))
story.append(PageBreak())

# ============================================================
# Page 7-8: CHAPTER 04 試験別
# ============================================================
story.append(Paragraph('CHAPTER 04', S['h1_chapter']))
story.append(Paragraph('試験別 ─ 戦略的活用法', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 4 * mm))

story.append(Paragraph('4-1. 共通テスト対策 ─ 『速読力』と『時間配分』', S['h3']))
story.append(quality_box('◎ 良い質問例', [
    '✓「共通テストリーディング第6問レベルの英文を、新しいテーマで1本作って。設問も6問」',
    '✓「以下の英文を、私が3分で読めるよう パラグラフごとの『最重要1文』 を抽出して」',
], GREEN_BG_C, GREEN_BORDER_C))
story.append(Spacer(1, 4 * mm))

story.append(Paragraph('4-2. 英検2級〜1級対策 ─ 『型』を体に染み込ませる', S['h3']))
story.append(quality_box('◎ 良い質問例', [
    '✓「英検準1級ライティングの4観点(内容・構成・語彙・文法)で、以下の私の答案を採点して」',
    '✓「英検準1級の二次面接シミュレーションを。あなたが面接官役、私が受験者役で」',
    '✓「英検1級の語彙問題で、頻出だが私が知らなさそうな単語を10個、例文付きで」',
], GREEN_BG_C, GREEN_BORDER_C))
story.append(Spacer(1, 4 * mm))

story.append(Paragraph('4-3. 東大・京大・早慶対策 ─ 『他の受験生と差がつく』使い方', S['h3']))
story.append(quality_box('◎ 良い質問例', [
    '✓【東大要約】「以下の英文を、私の要約とあなたの要約を 並べて比較 し、抽象度・情報量・論理性の3点で差を分析」',
    '✓【京大英訳】「以下の和文を 直訳・標準訳・京大満点答案 の3レベルで英訳し、違いを解説」',
    '✓【慶應自由英作文】「以下のテーマで300語のエッセイを。論理展開・パラグラフ構成・結論の3観点で批評」',
    '✓【早稲田正誤】「早稲田法学部の正誤問題形式で、難問を10問作って。引っかけポイントも明示」',
], GREEN_BG_C, GREEN_BORDER_C))
story.append(PageBreak())

# ============================================================
# Page 8: CHAPTER 05 NG 行動
# ============================================================
story.append(Paragraph('CHAPTER 05', S['h1_chapter']))
story.append(Paragraph('やってはいけない ─ NG行動チェックリスト', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 4 * mm))

story.append(Paragraph(
    'ここまでで「やるべきこと」を見てきた。最後に、絶対に避けてほしい <b>NG行動</b>'
    'を一覧にする。これらをやっている限り、AIは君の成績を1点も上げない。', S['body']))
story.append(Spacer(1, 3 * mm))

ng_data = [
    ['NG行動', 'なぜダメか / どう直すか'],
    ['× 解答を丸写しする', '思考のプロセスを飛ばすため記憶に残らない。<b>まず自分で解く</b>こと。'],
    ['× 「これ訳して」だけで送る', '訳をもらっても読解力は伸びない。<b>「SVOC構造を分析して」</b>に置き換える。'],
    ['× 自分の答えなしで質問する', 'AIが君の弱点を特定できない。<b>「自分の答え + 詰まった箇所」</b>をセットで送る。'],
    ['× AIの解答を疑わない', 'AIは時々もっともらしい誤りを出す。<b>違和感があったら『出典は?』『根拠は?』</b>と聞く。'],
    ['× 1分で済ませる', '対話の深さが学びの深さ。<b>1問につき最低3往復</b>はやりとりすること。'],
    ['× 解説を読んで終わる', '読むのはインプット。<b>自分の言葉で説明し直すアウトプット</b>を必ずセットに。'],
    ['× 類題を作らせない', '『理解』と『運用』は別物。<b>必ず類題5問で運用練習</b>。'],
    ['× 試験直前に新ジャンルを学ぶ', 'AIは <b>復習・補強・添削</b> 用。新規分野は <b>講義・教科書</b> が先。'],
]
ng_rows = []
for i, row in enumerate(ng_data):
    if i == 0:
        ng_rows.append([Paragraph(c, ParagraphStyle('h', fontName=JP_GO,
                                                     fontSize=10, textColor=colors.white))
                         for c in row])
    else:
        ng_rows.append([Paragraph(row[0], ParagraphStyle('ng', fontName=JP_MI,
                                                          fontSize=9.5,
                                                          textColor=RED_BORDER_C,
                                                          leading=14)),
                         Paragraph(row[1], ParagraphStyle('nd', fontName=JP_MI,
                                                           fontSize=9.5, leading=14))])
ng_table = Table(ng_rows, colWidths=[55 * mm, 105 * mm])
ng_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY_DEEP_C),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
     [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0, 0), (-1, -1), 7),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
]))
story.append(ng_table)
story.append(Spacer(1, 4 * mm))

# 講師より一言
story.append(Table([['● 講師より一言\n\n「AIに聞いたから大丈夫」は、最も危険な勘違いだ。AIは '
                      '<b>君の思考を増幅する装置</b> であって、<b>代行する装置</b> ではない。'
                      '代行させた瞬間、君の英語力の成長は止まる。']],
                    colWidths=[160*mm], style=[
    ('FONT', (0, 0), (-1, -1), JP_MI, 10),
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef9e7')),
    ('LINEBEFORE', (0, 0), (0, -1), 4, GOLD_C),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('LEFTPADDING', (0, 0), (-1, -1), 14),
]))
story.append(PageBreak())

# ============================================================
# Page 9: CHAPTER 06 1 日の理想ルーティン
# ============================================================
story.append(Paragraph('CHAPTER 06', S['h1_chapter']))
story.append(Paragraph('1日の理想的なルーティン', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 4 * mm))

story.append(Paragraph(
    'AIコーチングは <b>「短く・毎日・継続」</b> が最強。以下が、塾生に実際に推奨している'
    '1日40〜60分の標準パターンだ。', S['body']))
story.append(Spacer(1, 3 * mm))

routine_data = [
    ['時間帯', '所要', 'やること', 'AIへのプロンプト例'],
    ['朝 (登校前)', '10分', '昨日学んだ内容の口頭テスト',
     '「昨日学んだ仮定法のポイントを、5問口頭テスト形式で出題して」'],
    ['昼休み / 隙間', '10分', '単語・熟語1テーマの深掘り',
     '「come up with の例文を難易度別に5つ。+ 関連表現3つ」'],
    ['夕方 (自習時)', '20-30分', '自分で解いた問題の解説 + 英作文添削',
     '「以下の英作文を3観点(文法/自然さ/東大採点基準)で添削して」'],
    ['夜 (就寝前)', '10分', '今日の学びベスト3を整理',
     '「今日のチャット履歴から、最も重要な学び3つを箇条書きで」'],
]
routine_table = Table(routine_data, colWidths=[26*mm, 18*mm, 50*mm, 66*mm])
routine_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), JP_MI, 9.5),
    ('FONT', (0, 0), (-1, 0), JP_GO, 10),
    ('BACKGROUND', (0, 0), (-1, 0), NAVY_DEEP_C),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
     [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(routine_table)
story.append(Spacer(1, 5 * mm))

story.append(Paragraph('週次・月次の使い方', S['h3']))
wm_data = [
    ['週次 (週末60分)', '・1週間で間違えた問題を全部AIに見せ、弱点の傾向を分析させる\n'
                        '・「今週の私の弱点トップ3を特定し、来週の優先課題を提案して」\n'
                        '・週末に模試形式の演習(AI生成問題)で実力チェック'],
    ['月次 (月末60分)', '・1ヶ月のチャット履歴を振り返り、『学んだことリスト』を作成\n'
                        '・「今月学んだ文法事項を全部リストアップし、習熟度を5段階で評価して」\n'
                        '・志望校の最新問題に対して『今の実力で何点取れそうか』をAIに見積もらせる'],
]
wm_table = Table(wm_data, colWidths=[35*mm, 125*mm])
wm_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), JP_MI, 9.5),
    ('FONT', (0, 0), (0, -1), JP_GO, 10),
    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
    ('TEXTCOLOR', (0, 0), (0, -1), NAVY_C),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
]))
story.append(wm_table)
story.append(PageBreak())

# ============================================================
# Page 10: CHAPTER 07 コピペプロンプト集
# ============================================================
story.append(Paragraph('CHAPTER 07', S['h1_chapter']))
story.append(Paragraph('コピペで使える ─ 厳選プロンプト集', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 4 * mm))

story.append(Paragraph(
    '最後に、明日から <b>そのままコピペで使える</b> 厳選プロンプトを置いておく。[ ]'
    'の中だけ自分の状況に置き換えて使うこと。', S['body']))

prompts = [
    ('【英文法 ─ 詰まった問題を分析】',
     '以下の問題で、私は [自分の答え] と答えましたが正解は [正解] でした。なぜ私の答えが間違いで、'
     '正解が正しいのかを、文法ルールの原理から段階的に説明してください。最後に、同じポイントを'
     '問う類題を3問、難易度別に作ってください。'),
    ('【長文 ─ 構造分析リクエスト】',
     '以下の英文のSVOC構造を分析し、修飾関係を明確に示してください。特に、どの語句がどこに'
     'かかっているのかを矢印や箇条書きで視覚的に示してください。最後に、この文を訳す際の'
     '『考え方の順番』を3ステップで教えてください。'),
    ('【英作文 ─ 3観点採点】',
     '以下の私の自由英作文を、(1) 文法・(2) 自然さ・(3) 東大採点基準 の3観点で採点してください。'
     '各観点を5段階評価し、具体的な改善案を最低2つずつ提示してください。最後に、私の答案を'
     '改良した『満点答案バージョン』も書いてください。'),
    ('【弱点分析 ─ 週末用】',
     '以下は今週私が間違えた問題のリストです。これらに共通する『弱点パターン』を特定し、'
     '来週優先して取り組むべき学習項目を3つ提案してください。具体的な演習計画も。'),
    ('【入試直前 ─ 仕上げチェック】',
     '[志望校・学部] の英語入試で必ず問われる頻出ジャンルを5つ挙げ、それぞれについて'
     '『これを知っていれば差がつく』というポイントを3つずつまとめてください。'),
]
for title, body_text in prompts:
    t = Table([[Paragraph(f'<font color="#0a1f44"><b>{title}</b></font><br/>'
                            f'<font color="#2c2c2c" size="9.5">{body_text}</font>',
                            ParagraphStyle('p', fontName=JP_MI, fontSize=10, leading=14))]],
              colWidths=[160 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY_C),
        ('LINEBEFORE', (0, 0), (0, -1), 3, GOLD_C),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 3 * mm))
story.append(PageBreak())

# ============================================================
# Page 11: CHAPTER 08 終わりに
# ============================================================
story.append(Paragraph('CHAPTER 08', S['h1_chapter']))
story.append(Paragraph('終わりに ─ 君の努力を10倍にする道具', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    'ここまで読んでくれてありがとう。最後に、私から君に伝えたいことが2つある。', S['body']))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph('① AIは『努力する人』のためだけにある', S['h3']))
story.append(Paragraph(
    'AIは魔法ではない。君が自分で問題を解き、自分で考え、自分で詰まった時に初めて、本当の力を'
    '発揮する。<b>『楽をする道具』として使えば、君は楽をしながら成績を落とす。『努力を増幅する'
    '道具』として使えば、君の努力は10倍の成果を生む。</b>どちらを選ぶかは、毎日の使い方が決める。',
    S['body']))

story.append(Paragraph('② 結局、最後に勝つのは『問い続ける生徒』だ', S['h3']))
story.append(Paragraph(
    '私が予備校時代から、東大・京大・早慶に送り出してきた生徒たちには共通点がある。それは'
    '<b>『なぜ?』『どうして?』『他には?』を、絶対にやめない</b> ことだ。AIが普及した今、'
    'この姿勢は <b>無限の対話相手</b> を手に入れることを意味する。君が問い続ける限り、AIは'
    '答え続ける。そして3ヶ月後、半年後、君は自分でも信じられないほどの力を手にしているはずだ。',
    S['body']))
story.append(Spacer(1, 8 * mm))
story.append(GoldUnderline(width=80 * mm, thickness=2))
story.append(Spacer(1, 5 * mm))
story.append(Paragraph(
    '<font color="#0a1f44"><b>「使い方を知っている者だけが、AI時代の勝者になる。」</b></font>',
    ParagraphStyle('c', fontName=JP_GO, fontSize=14, alignment=TA_CENTER,
                   leading=22)))
story.append(Spacer(1, 3 * mm))
story.append(Paragraph(
    '君の努力が、最短最速で結果に変わることを ─ 心から祈っている。', S['body_center']))
story.append(PageBreak())

# ============================================================
# Page 12-13: CHAPTER 09 学習管理 + カリキュラム + 保護者ダッシュボード (新規)
# ============================================================
story.append(Paragraph('CHAPTER 09', S['h1_chapter']))
story.append(Paragraph('学習管理 ─ 自宅学習を「習慣」に変える 3 ステップ', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    'AIコーチングと並ぶ、ai-juku のもう一つの核が <b>学習管理機能</b>。塾任せでも、放任でもない、'
    '<b>生徒が「自走できる」第三の道</b>を提供する。', S['body']))

story.append(Image(str(fig_3step), width=130 * mm, height=75 * mm,
                    hAlign='CENTER'))
story.append(Paragraph('図 1: Plan → Record → Review の循環で学習が習慣化される',
                        S['caption']))
story.append(Spacer(1, 3 * mm))

manage_data = [
    ['Step', '機能', '具体的な使い方'],
    ['① Plan',
     '<b>学習計画</b>',
     '「明日、英語 60 分・数学 90 分」を前日にセット。AI が単元を割り当て、'
     'カリキュラムに沿って科目バランスを最適化する。'],
    ['② Record',
     '<b>学習記録 (streak)</b>',
     '勉強した分だけ 1 タップで記録。連続記録日数 (streak) が伸びるたびに'
     'バッジが付与される。3 日連続未記録で警告バナーが出るためサボれない。'],
    ['③ Review',
     '<b>週次振り返り</b>',
     '週末に「今週は英語 4 時間、数学 2 時間」のような学習時間グラフが表示。'
     '「英語が落ちている」を可視化し、来週の計画に反映する。'],
]
manage_rows = [[Paragraph(c, ParagraphStyle('m', fontName=JP_MI, fontSize=9.5, leading=14))
                 for c in row] for row in manage_data]
manage_table = Table(manage_rows, colWidths=[25*mm, 30*mm, 105*mm])
manage_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY_DEEP_C),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), JP_GO, 10),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
     [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(manage_table)
story.append(PageBreak())

story.append(Paragraph('CHAPTER 09', S['h1_chapter']))
story.append(Paragraph('カリキュラム ─ 志望校別の最短ルート (5 コース)', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    'ai-juku は <b>志望校・目的別に 5 つのコース</b> を用意。各コースには問題プール'
    '16,600+ 問とフラッシュカード SRS が紐づき、毎日の課題が自動で出題される。', S['body']))

curriculum_data = [
    ['コース', '対象', '主な内容'],
    ['<b>国公立難関</b>', '東大・京大・一橋・東工大志望',
     '英数国理社 全 5 教科 + 二次記述対策・本試水準の演習'],
    ['<b>私立難関</b>', '早慶上理・MARCH 志望',
     '英数国 3 教科特化 + 過去問演習・大学別の傾向対策'],
    ['<b>共通テスト対策</b>', '国公立志望全般',
     'マーク形式特化・時間配分訓練・速読力強化'],
    ['<b>英検 + 大学受験</b>', '英検 2 級〜準 1 級 + 受験英語',
     '4 技能 + 長文読解・二次面接シミュレーション'],
    ['<b>通塾生 addon</b>', '既存通塾生 (¥9,800/月)',
     '自宅学習を ai-juku で補完・塾と AI の両輪'],
]
cur_rows = [[Paragraph(c, ParagraphStyle('cu', fontName=JP_MI, fontSize=9.5, leading=14))
              for c in row] for row in curriculum_data]
cur_table = Table(cur_rows, colWidths=[35*mm, 45*mm, 80*mm])
cur_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY_DEEP_C),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), JP_GO, 10),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
     [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(cur_table)
story.append(Spacer(1, 6 * mm))

story.append(Paragraph('● 保護者ダッシュボード ─ 自宅学習の「見える化」', S['h3']))
story.append(Paragraph(
    '保護者は専用 URL から以下を確認できる。「子どもが本当に勉強しているか」が'
    '<b>数値とグラフで完全に見える</b>。', S['body']))
story.append(Paragraph(
    '✓ 今週の学習時間 (科目別・グラフ表示)<br/>'
    '✓ 連続記録日数 (streak)<br/>'
    '✓ 塾長からのメッセージ履歴<br/>'
    '✓ AI チューター質問履歴 (どこで詰まったか)<br/>'
    '✓ 模試スコア推移 (月次)', S['body']))
story.append(Spacer(1, 4 * mm))

story.append(Image(str(fig_heatmap), width=150 * mm, height=58 * mm,
                    hAlign='CENTER'))
story.append(Paragraph(
    '図 2: 週次学習時間ヒートマップ — どの曜日にサボったかが一目瞭然',
    S['caption']))
story.append(PageBreak())

# ============================================================
# Page 14: CHAPTER 10 偏差値推移データ
# ============================================================
story.append(Paragraph('CHAPTER 10', S['h1_chapter']))
story.append(Paragraph('データで見る差 ─ 使う子と使わない子の 12 ヶ月', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    'AIコーチングを <b>1 日 60 分以上、継続して使った生徒</b> と、'
    'まったく使わなかった生徒の偏差値推移には、明確な差が現れる。'
    '以下は、社内モニター生徒 20 名・3 ヶ月の追跡データに、学習科学の予測モデルを'
    '加えてまとめた <b>12 ヶ月ベンチマーク</b> だ。', S['body']))

story.append(Image(str(fig_hensachi), width=160 * mm, height=90 * mm,
                    hAlign='CENTER'))
story.append(Paragraph(
    '<b>※ 図はイメージです。実際の伸びは個人差があります。1 日 60 分以上の継続学習が前提。'
    '社内モニター 20 名・3 ヶ月の追跡 + 学習科学の予測モデル。実証データは 2026 年内に '
    '第三者機関監修で公開予定です。</b>',
    ParagraphStyle('warn', fontName=JP_MI, fontSize=8, textColor=GRAY_C,
                   leading=11, alignment=TA_CENTER, italic=True)))
story.append(Spacer(1, 6 * mm))

# 数値ハイライト
highlight_data = [
    ['期間', 'ai-juku 利用 (目安)', '非利用 (一般平均)', '差'],
    ['3 ヶ月', '+6.5', '+1.0', '<b>約 5.5 倍</b>'],
    ['6 ヶ月', '+10', '+2.0', '<b>約 5.0 倍</b>'],
    ['12 ヶ月', '+16', '+3.0', '<b>約 5.3 倍</b>'],
]
hl_rows = [[Paragraph(c, ParagraphStyle('h', fontName=JP_MI, fontSize=10, leading=14,
                                         alignment=TA_CENTER))
             for c in row] for row in highlight_data]
hl_table = Table(hl_rows, colWidths=[35*mm, 45*mm, 45*mm, 35*mm])
hl_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY_DEEP_C),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), JP_GO, 10),
    ('BACKGROUND', (1, 1), (1, -1), colors.HexColor('#fef9e7')),
    ('TEXTCOLOR', (1, 1), (1, -1), GOLD_C),
    ('FONT', (1, 1), (1, -1), JP_GO, 11),
    ('BACKGROUND', (3, 1), (3, -1), colors.HexColor('#eff6ff')),
    ('TEXTCOLOR', (3, 1), (3, -1), NAVY_C),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(hl_table)
story.append(Spacer(1, 4 * mm))
story.append(Paragraph(
    '<b>差を生む要因 (推定)</b>: ① 弱点 TOP3 の自動推薦で「効率の悪い練習」を回避 / '
    '② SRS フラッシュカードで定着率 85%+ / ③ 写真採点 30 秒返答で「分からない時間」'
    'をゼロに / ④ streak と週次振り返りで学習習慣化。', S['body']))
story.append(PageBreak())

# ============================================================
# Page 15-16: CHAPTER 11 体験談 + CTA
# ============================================================
story.append(Paragraph('CHAPTER 11', S['h1_chapter']))
story.append(Paragraph('生徒の声 ─ 実際の伸び方 (3 ケース)', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    '以下は、ai-juku を 3 ヶ月以上継続した生徒の <b>実際の伸び方 (匿名・仮名)</b>。'
    '志望校・科目・学年が異なる 3 ケースで紹介する。', S['body']))
story.append(Spacer(1, 3 * mm))

testimonials = [
    {
        'name': '中 3 男子 A.K さん',
        'subject': '英語',
        'period': '3 ヶ月',
        'before': '英検 3 級',
        'after': '英検 準 2 級 合格',
        'quote': '「英検 3 級から 3 ヶ月で準 2 級合格。AI が苦手な過去問だけ厳選してくれる」',
        'color': NAVY_C,
    },
    {
        'name': '高 2 女子 M.S さん',
        'subject': '国数英',
        'period': '6 ヶ月',
        'before': '校内偏差値 55',
        'after': '校内偏差値 62 (+7)',
        'quote': '「記述添削が 24h 返ってくるから模試前が楽。先生に頼らなくても大丈夫に」',
        'color': GOLD_C,
    },
    {
        'name': '高 3 男子 R.T さん',
        'subject': '英語',
        'period': '9 ヶ月',
        'before': '共通テスト 130 点',
        'after': '共通テスト 168 点 (+38)',
        'quote': '「3 AI 解説で詰まる所が無くなった。誰に聞いても分からなかった構造分析が手に入る」',
        'color': NAVY_DEEP_C,
    },
]
for t in testimonials:
    card = Table([
        [Paragraph(f'<font color="#ffffff"><b>{t["name"]}</b>　'
                     f'<font size="9">({t["subject"]}・{t["period"]})</font></font>',
                     ParagraphStyle('tn', fontName=JP_GO, fontSize=11, leading=14))],
        [Paragraph(f'<font color="#2c2c2c"><b>Before:</b> {t["before"]} <b>→</b> '
                     f'<b>After:</b> <font color="#c9a961"><b>{t["after"]}</b></font></font>',
                     ParagraphStyle('tba', fontName=JP_MI, fontSize=10, leading=14))],
        [Paragraph(f'<font color="#2c2c2c" size="9.5"><i>{t["quote"]}</i></font>',
                     ParagraphStyle('tq', fontName=JP_MI, fontSize=9.5, leading=14))],
    ], colWidths=[160 * mm])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), t['color']),
        ('BACKGROUND', (0, 1), (0, 2), LIGHT_GRAY_C),
        ('LINEBEFORE', (0, 0), (0, -1), 3, GOLD_C),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(card)
    story.append(Spacer(1, 4 * mm))

story.append(Paragraph(
    '※ 仮名・写真はイメージ。学習期間と結果には個人差があります。1 日 60 分以上の'
    '継続学習を前提とした実例です。',
    ParagraphStyle('disc', fontName=JP_MI, fontSize=8, textColor=GRAY_C,
                   leading=11, alignment=TA_LEFT, italic=True)))
story.append(PageBreak())

# Page 16: CTA + 申込フロー
story.append(Paragraph('CHAPTER 11', S['h1_chapter']))
story.append(Paragraph('申込 ─ 次回値上げ前ラスト募集', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 6 * mm))

# CTA box (deep navy + gold border)
cta_inner = Table([
    [Paragraph('<font color="#c9a961" size="22"><b>次回値上げ前ラスト募集</b></font>',
                ParagraphStyle('cta', alignment=TA_CENTER, fontName=JP_GO,
                                fontSize=22, leading=28, textColor=GOLD_C))],
    [Paragraph('<font color="#ffffff" size="14"><b>14 日間 無料体験</b> + '
                '<b>入塾金 ¥0</b> + 友達紹介で <b>¥3,000 OFF</b></font>',
                ParagraphStyle('ctab', alignment=TA_CENTER, fontName=JP_GO,
                                fontSize=13, leading=20, textColor=colors.white))],
    [Paragraph('<font color="#d4d4d4" size="9">在塾生 200 名超 / Threads 6,000 フォロワー / 紹介ループ拡散中</font>',
                ParagraphStyle('ctac', alignment=TA_CENTER, fontName=JP_MI,
                                fontSize=9, leading=14,
                                textColor=colors.HexColor('#d4d4d4')))],
], colWidths=[150*mm])
cta_inner.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), NAVY_DEEP_C),
    ('BOX', (0, 0), (-1, -1), 2, GOLD_C),
    ('TOPPADDING', (0, 0), (-1, -1), 14),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
]))
cta_outer = Table([[cta_inner]], colWidths=[160*mm])
cta_outer.setStyle(TableStyle([
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
]))
story.append(cta_outer)
story.append(Spacer(1, 8 * mm))

story.append(Paragraph('申込フロー ─ 3 分で体験開始', S['h3']))
story.append(Image(str(fig_apply), width=170 * mm, height=47 * mm,
                    hAlign='CENTER'))
story.append(Spacer(1, 6 * mm))

story.append(Paragraph('申込 URL', S['h3']))
url_data = [[Paragraph(
    '<font color="#0a1f44" size="14"><b>https://trillion-ai-juku.com</b></font><br/>'
    '<font color="#888888" size="9">↑ メールアドレスを入力するだけ。'
    '3 分で体験開始できます。utm_source=pdf_guide_2026-05 で計測中。</font>',
    ParagraphStyle('u', fontName=JP_GO, alignment=TA_CENTER, leading=22))]]
url_table = Table(url_data, colWidths=[160*mm])
url_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY_C),
    ('LINEBEFORE', (0, 0), (0, -1), 3, GOLD_C),
    ('TOPPADDING', (0, 0), (-1, -1), 12),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
]))
story.append(url_table)
story.append(Spacer(1, 4 * mm))

story.append(Paragraph('お問い合わせ', S['h3']))
story.append(Paragraph(
    '<b>メール</b>: info@trillion-ai-juku.com<br/>'
    '<b>LINE 公式アカウント</b>: ai-juku<br/>'
    '<b>Threads</b>: @ai_juku_official (6,000 フォロワー)', S['body']))
story.append(Spacer(1, 6 * mm))

story.append(HRFlowable(width="100%", thickness=1, color=GOLD_C))
story.append(Spacer(1, 3 * mm))

# Final box (brand)
brand_box = Table([
    [Paragraph('<font color="#c9a961"><b>Trillion English Academy</b></font>',
                ParagraphStyle('b', fontName=JP_GO, fontSize=12, alignment=TA_CENTER,
                                leading=18, textColor=GOLD_C))],
    [Paragraph('<font color="#ffffff" size="9">東大 / 京大 / 早慶 / 英検 専門 オンライン英語塾</font>',
                ParagraphStyle('bs', fontName=JP_MI, fontSize=9, alignment=TA_CENTER,
                                leading=12, textColor=colors.white))],
    [Paragraph('<font color="#d4d4d4" size="8">本書は塾生・体験生のために制作された非売品です。'
                '無断複製・再配布を禁じます。 Vol.1 — 2026年5月 改訂版</font>',
                ParagraphStyle('bd', fontName=JP_MI, fontSize=8, alignment=TA_CENTER,
                                leading=11, textColor=colors.HexColor('#d4d4d4')))],
], colWidths=[160*mm])
brand_box.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), NAVY_DEEP_C),
    ('TOPPADDING', (0, 0), (-1, -1), 14),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
]))
story.append(brand_box)

# Build
doc.build(story)

print(f"\n✅ PDF 生成完了: {OUT_PDF}")
print(f"   サイズ: {OUT_PDF.stat().st_size / 1024:.1f} KB")
