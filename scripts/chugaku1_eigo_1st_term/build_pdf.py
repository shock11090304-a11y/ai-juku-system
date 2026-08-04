#!/usr/bin/env python3
"""
中学1年1学期英文法 100問 PDF生成スクリプト
reportlab で問題編/解答編/解説編を生成
"""

import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, Image
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# フォント登録
try:
    # macOS では /Library/Fonts にあることが多い
    font_path = '/Library/Fonts/Arial Unicode.ttf'
    pdfmetrics.registerFont(TTFont('Arial Unicode', font_path))
    FONT_NAME = 'Arial Unicode'
except:
    # フォールバック
    FONT_NAME = 'Helvetica'
    print("Warning: Arial Unicode not found, using Helvetica fallback")

from content import PROBLEMS

# ページサイズと余白
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 15 * mm
MARGIN_RIGHT = 15 * mm
MARGIN_TOP = 15 * mm
MARGIN_BOTTOM = 15 * mm

def create_styles():
    """reportlab スタイルを定義"""
    styles = getSampleStyleSheet()

    # タイトル
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName=FONT_NAME,
    )

    # 単元見出し
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#2c3e50'),
        spaceAfter=8,
        spaceBefore=12,
        fontName=FONT_NAME,
        borderPadding=4,
    )

    # 問題テキスト
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=4,
        fontName=FONT_NAME,
        wordWrap='CJK',
        alignment=TA_LEFT,
    )

    # 選択肢テキスト
    option_style = ParagraphStyle(
        'Option',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=2,
        fontName=FONT_NAME,
        wordWrap='CJK',
        alignment=TA_LEFT,
    )

    # 解説テキスト
    explanation_style = ParagraphStyle(
        'Explanation',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        spaceAfter=3,
        fontName=FONT_NAME,
        wordWrap='CJK',
        alignment=TA_LEFT,
        textColor=HexColor('#555555'),
    )

    # ティップス
    tips_style = ParagraphStyle(
        'Tips',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        spaceAfter=6,
        fontName=FONT_NAME,
        wordWrap='CJK',
        alignment=TA_LEFT,
        textColor=HexColor('#666666'),
        leftIndent=8,
    )

    # フッター
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#999999'),
        alignment=TA_CENTER,
    )

    return {
        'title': title_style,
        'heading': heading_style,
        'question': question_style,
        'option': option_style,
        'explanation': explanation_style,
        'tips': tips_style,
        'footer': footer_style,
    }

def build_problems_edition(output_path):
    """問題編PDF生成"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    styles = create_styles()
    story = []

    # 表紙
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph(
        '中学1年1学期 英文法<br/>選択式演習問題集',
        styles['title']
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        '100問 問題編',
        ParagraphStyle(
            'Subtitle',
            parent=styles['title'],
            fontSize=16,
            spaceAfter=40,
        )
    ))
    story.append(Spacer(1, 50 * mm))
    story.append(Paragraph(
        f'作成日: {datetime.now().strftime("%Y年%m月%d日")}',
        styles['footer']
    ))
    story.append(PageBreak())

    # 問題をカテゴリ別に表示（連続フロー + KeepTogether で半端ページを回避）
    current_category = None
    category_groups = []
    current_group = []

    for prob in PROBLEMS:
        # カテゴリ変更時
        if prob['category'] != current_category:
            if current_group:
                category_groups.append(current_group)
            current_category = prob['category']
            current_group = [Paragraph(
                f"【{prob['category']}】",
                styles['heading']
            )]

        # 問題番号と問題文
        q_text = f"<b>{prob['number']}.</b> {prob['question']}"
        current_group.append(Paragraph(q_text, styles['question']))

        # 選択肢
        for i, opt in enumerate(prob['options'], 1):
            opt_text = f"({chr(64 + i)}) {opt}"
            current_group.append(Paragraph(opt_text, styles['option']))

        current_group.append(Spacer(1, 3 * mm))

    # 最後のグループを追加
    if current_group:
        category_groups.append(current_group)

    # グループを story に追加（KeepTogether で見出し+問題はなるべく同じページに）
    for group in category_groups:
        story.extend(group)

    doc.build(story)
    print(f"✓ 問題編作成: {output_path}")

def build_answers_edition(output_path):
    """解答編PDF生成"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    styles = create_styles()
    story = []

    # 表紙
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph(
        '中学1年1学期 英文法<br/>選択式演習問題集',
        styles['title']
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        '100問 解答編',
        ParagraphStyle(
            'Subtitle',
            parent=styles['title'],
            fontSize=16,
            spaceAfter=40,
        )
    ))
    story.append(Spacer(1, 30 * mm))

    # 解答表
    current_category = None
    table_data = []

    for prob in PROBLEMS:
        # カテゴリ変更時
        if prob['category'] != current_category:
            if table_data:
                # 前のテーブルを追加
                t = Table(table_data, colWidths=[20*mm, 50*mm, 100*mm], splitByRow=True)
                t.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), FONT_NAME, 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8f4f8')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                t.repeatRows = 1
                story.append(t)
                story.append(Spacer(1, 8*mm))

            current_category = prob['category']
            story.append(Paragraph(
                f"【{prob['category']}】",
                styles['heading']
            ))
            table_data = [
                [
                    Paragraph('<b>問</b>', styles['option']),
                    Paragraph('<b>答</b>', styles['option']),
                    Paragraph('<b>選択肢</b>', styles['option']),
                ]
            ]

        # 正解文字（A/B/C/D）
        answer_letter = chr(65 + prob['answer_index'])  # A/B/C/D
        answer_text = prob['options'][prob['answer_index']]

        table_data.append([
            Paragraph(str(prob['number']), styles['option']),
            Paragraph(f"<b>{answer_letter}</b>", styles['option']),
            Paragraph(answer_text, styles['option']),
        ])

    # 最後のテーブルを追加
    if table_data and len(table_data) > 1:
        t = Table(table_data, colWidths=[20*mm, 50*mm, 100*mm], splitByRow=True)
        t.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), FONT_NAME, 10),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8f4f8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        t.repeatRows = 1  # ページをまたぐ時もヘッダ行を繰り返す
        story.append(t)

    doc.build(story)
    print(f"✓ 解答編作成: {output_path}")

def build_explanation_edition(output_path):
    """解説編PDF生成"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    styles = create_styles()
    story = []

    # 表紙
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph(
        '中学1年1学期 英文法<br/>選択式演習問題集',
        styles['title']
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        '100問 解説編',
        ParagraphStyle(
            'Subtitle',
            parent=styles['title'],
            fontSize=16,
            spaceAfter=40,
        )
    ))
    story.append(Spacer(1, 50 * mm))
    story.append(PageBreak())

    # 解説を問題ごとに表示
    current_category = None

    for prob in PROBLEMS:
        # カテゴリ変更時に見出しを追加
        if prob['category'] != current_category:
            if current_category is not None:
                story.append(Spacer(1, 6 * mm))
            current_category = prob['category']
            story.append(Paragraph(
                f"【{prob['category']}】",
                styles['heading']
            ))

        # 問題番号、正解、問題文
        answer_letter = chr(65 + prob['answer_index'])
        answer_text = prob['options'][prob['answer_index']]

        story.append(Paragraph(
            f"<b>問 {prob['number']} [正解: {answer_letter}] {answer_text}</b>",
            styles['question']
        ))

        # 問題文
        story.append(Paragraph(prob['question'], styles['option']))
        story.append(Spacer(1, 2 * mm))

        # 解説
        exp_text = f"▲ {prob['explanation']}"
        story.append(Paragraph(exp_text, styles['explanation']))

        # ティップス
        tips_text = f"★ {prob['tips']}"
        story.append(Paragraph(tips_text, styles['tips']))

        story.append(Spacer(1, 4 * mm))

    doc.build(story)
    print(f"✓ 解説編作成: {output_path}")

def main():
    # 出力ディレクトリ
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path.home() / "Desktop" / f"chugaku1_eigo_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📚 中学1年1学期英文法 100問 PDF生成")
    print(f"出力先: {output_dir}")
    print()

    # 問題編・解答編・解説編を生成
    problems_path = output_dir / "01_問題編.pdf"
    answers_path = output_dir / "02_解答編.pdf"
    explanation_path = output_dir / "03_解説編.pdf"

    build_problems_edition(str(problems_path))
    build_answers_edition(str(answers_path))
    build_explanation_edition(str(explanation_path))

    print()
    print("✓ PDF生成完了")
    return 0

if __name__ == '__main__':
    sys.exit(main())
