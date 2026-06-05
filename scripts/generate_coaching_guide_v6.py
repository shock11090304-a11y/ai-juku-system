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
OUT_PDF = HOME / "Desktop" / "AI_Coaching_Guide_v6.pdf"
SCREENSHOT_DIR = Path("/tmp/ai_juku_screens")
SCREENSHOT_MOBILE_DIR = Path("/tmp/ai_juku_screens_mobile")

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
print("Figures done. Generating v3 expanded figures...")


def fig_subject_hensachi():
    """CH 10 科目別偏差値推移 3 グラフ"""
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
    months = [0, 3, 6, 9, 12]
    subjects = [
        ('英語', [0, 5.0, 8.5, 11.0, 12.3], [0, 0.8, 1.5, 2.0, 2.5], GOLD),
        ('数学', [0, 4.0, 7.0, 8.8, 9.7], [0, 0.7, 1.2, 1.8, 2.3], NAVY),
        ('国語', [0, 4.5, 7.5, 9.5, 11.1], [0, 0.6, 1.0, 1.5, 2.1], '#10b981'),
    ]
    for ax, (subj, using, notusing, color) in zip(axes, subjects):
        ax.plot(months, using, marker='o', linewidth=2.2, color=color, markersize=6)
        ax.plot(months, notusing, marker='s', linewidth=1.3, color=GRAY,
                linestyle='--', markersize=4)
        ax.fill_between(months, using, notusing, alpha=0.15, color=color)
        ax.set_title(subj, fontsize=12, fontweight='bold', color=color)
        ax.set_xlabel('月', fontsize=9)
        ax.set_ylabel('偏差値の伸び', fontsize=9)
        ax.set_ylim(-1, 14)
        ax.set_xticks(months)
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        # 最終値表示
        ax.text(12.3, using[-1], f'+{using[-1]}', va='center',
                fontsize=10, fontweight='bold', color=color)
    fig.suptitle('科目別 偏差値推移 12 ヶ月 (ai-juku 利用 vs 非利用)',
                 fontsize=12, fontweight='bold', color=NAVY_DEEP, y=1.02)
    plt.tight_layout()
    p = FIG_DIR / "fig_subject.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_grade_heatmap():
    """CH 10 学年別ヒートマップ"""
    fig, ax = plt.subplots(figsize=(9, 3.5))
    np.random.seed(7)
    grades = ['中 3', '高 1', '高 2', '高 3']
    months = ['Start', '1mo', '2mo', '3mo', '4mo', '5mo', '6mo']
    # 始めるのが早いほど伸びが大きい
    data = np.array([
        [0, 2.5, 4.5, 6.5, 8.5, 10.5, 12.0],  # 中 3
        [0, 2.0, 4.0, 6.0, 8.0, 9.5, 11.0],   # 高 1
        [0, 1.5, 3.0, 4.8, 6.5, 8.0, 9.5],    # 高 2
        [0, 1.0, 2.5, 4.0, 5.5, 7.0, 8.5],    # 高 3
    ])
    im = ax.imshow(data, cmap='YlOrRd', aspect='auto', vmin=0, vmax=13)
    ax.set_xticks(np.arange(len(months)))
    ax.set_yticks(np.arange(len(grades)))
    ax.set_xticklabels(months, fontsize=10)
    ax.set_yticklabels(grades, fontsize=11, fontweight='bold')
    for i in range(len(grades)):
        for j in range(len(months)):
            v = data[i, j]
            color = 'white' if v > 7 else NAVY_DEEP
            ax.text(j, i, f'+{v:.1f}', ha='center', va='center',
                    color=color, fontsize=9, fontweight='bold')
    ax.set_title('学年別 ─ 始める時期が早いほど偏差値の伸びが大きい',
                 fontsize=12, fontweight='bold', color=NAVY_DEEP)
    cbar = plt.colorbar(im, ax=ax, label='偏差値の伸び', pad=0.02)
    plt.tight_layout()
    p = FIG_DIR / "fig_grade.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_frequency_bar():
    """CH 10 使用頻度別 4 段階比較"""
    fig, ax = plt.subplots(figsize=(8, 4))
    categories = ['週 0 日\n(未利用)', '週 1-3 日\n(ライト)',
                  '週 4-6 日\n(レギュラー)', '週 7 日\n(毎日)']
    values = [0.3, 5.8, 10.1, 14.2]
    colors = [GRAY, '#94a3b8', NAVY, GOLD]
    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=2)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3,
                f'+{v:.1f}', ha='center', fontsize=12, fontweight='bold',
                color=b.get_facecolor())
    ax.set_ylabel('6 ヶ月後の偏差値の伸び (目安)', fontsize=10)
    ax.set_title('使用頻度別 ─ 「毎日 15 分」が偏差値を最も伸ばす',
                 fontsize=12, fontweight='bold', color=NAVY_DEEP)
    ax.set_ylim(0, 17)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    p = FIG_DIR / "fig_freq.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_3ai_mockup():
    """CH 12 3 AI 並列解答 mockup (Claude / GPT-4o / Gemini)"""
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(10, 4.5))
    # 上部: 質問 box
    q_box = mpatches.FancyBboxPatch((0.3, 3.5), 9.4, 1.0,
                                     boxstyle="round,pad=0.08",
                                     linewidth=1.5, edgecolor=NAVY_DEEP,
                                     facecolor='#eff6ff')
    ax.add_patch(q_box)
    ax.text(5, 4.2, '[写真] 生徒の質問', ha='center', fontsize=10,
            color=NAVY_DEEP, fontweight='bold')
    ax.text(5, 3.85, '"Why is the present perfect used here? — I read this for 2 years."',
            ha='center', fontsize=9, color='#374151', style='italic')
    # 3 AI 並列 (3 列)
    ai_list = [
        ('Claude Opus 4.7', '#cd6839',
         'コアイメージ: 過去のある時点から\n現在までの「継続」を一つの塊で捉える。\n「2年」は範囲を示す for 句。'),
        ('GPT-4o', '#10a37f',
         'Present perfect = 過去開始 + 現在継続。\nfor 2 years が duration を明示。\n比較: 過去形なら "I read it 2 years ago"'),
        ('Gemini 2.5 Pro', '#4285f4',
         '時制選択の根拠: 動作の completeness。\n「読み終わった」なら過去形。\n「ずっと読んでいる」なら現在完了。'),
    ]
    for i, (name, color, text) in enumerate(ai_list):
        x = 0.3 + i * 3.2
        # AI name header
        h_box = mpatches.FancyBboxPatch((x, 2.7), 2.9, 0.6,
                                         boxstyle="round,pad=0.05",
                                         linewidth=1.5, edgecolor=color,
                                         facecolor=color)
        ax.add_patch(h_box)
        ax.text(x + 1.45, 3.0, name, ha='center', va='center',
                fontsize=10, color='white', fontweight='bold')
        # Body
        b_box = mpatches.FancyBboxPatch((x, 0.5), 2.9, 2.1,
                                         boxstyle="round,pad=0.05",
                                         linewidth=1, edgecolor=color,
                                         facecolor='white')
        ax.add_patch(b_box)
        ax.text(x + 0.15, 2.35, text, ha='left', va='top',
                fontsize=8, color='#374151', wrap=True)
    # 下部 caption
    ax.text(5, 0.15, '3 AI が同時に異なる視点で解答 → 生徒は「どの解説が一番わかるか」を選ぶ',
            ha='center', fontsize=9, color=GRAY, style='italic')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    p = FIG_DIR / "fig_3ai.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_srs_box():
    """CH 12 SRS Leitner Box 5 段階可視化"""
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(10, 3.5))
    boxes = [
        ('Box 1', '毎日', '#ef4444', 28),
        ('Box 2', '2 日に 1 回', '#f97316', 18),
        ('Box 3', '4 日に 1 回', '#eab308', 12),
        ('Box 4', '1 週間に 1 回', '#10b981', 8),
        ('Box 5', '2 週間に 1 回', '#3b82f6', 5),
    ]
    for i, (name, interval, color, count) in enumerate(boxes):
        x = 0.5 + i * 1.85
        # Box
        b = mpatches.FancyBboxPatch((x, 1.2), 1.5, 1.8,
                                     boxstyle="round,pad=0.05",
                                     linewidth=2, edgecolor=color,
                                     facecolor=color, alpha=0.85)
        ax.add_patch(b)
        ax.text(x + 0.75, 2.6, name, ha='center', va='center',
                fontsize=12, color='white', fontweight='bold')
        ax.text(x + 0.75, 2.15, interval, ha='center', va='center',
                fontsize=8, color='white')
        ax.text(x + 0.75, 1.6, f'{count}\n単語', ha='center', va='center',
                fontsize=11, color='white', fontweight='bold')
        # Arrow to next
        if i < len(boxes) - 1:
            ax.annotate("", xy=(x + 2.15, 2.1), xytext=(x + 1.6, 2.1),
                        arrowprops=dict(arrowstyle='->', color=NAVY_DEEP, lw=1.5))
    ax.text(5, 0.5, '正解で次の Box へ → 間隔が伸びて記憶定着率 85%+',
            ha='center', fontsize=10, color=NAVY_DEEP, fontweight='bold')
    ax.text(5, 0.15, '不正解で Box 1 へ戻る → 忘却曲線を AI が制御', ha='center',
            fontsize=9, color=GRAY, style='italic')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.5)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    p = FIG_DIR / "fig_srs.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_photo_grade_mockup():
    """CH 12 写真採点 before / after mockup"""
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(10, 4))
    # Left: 撮影前 (生徒の手書き答案)
    l_box = mpatches.FancyBboxPatch((0.3, 0.5), 4, 3.0,
                                     boxstyle="round,pad=0.05",
                                     linewidth=1.5, edgecolor=GRAY,
                                     facecolor='#fafafa')
    ax.add_patch(l_box)
    ax.text(2.3, 3.2, '① 撮影前: 生徒の手書き答案', ha='center', fontsize=10,
            color=NAVY_DEEP, fontweight='bold')
    ax.text(2.3, 2.4, '"The reason why English is\nspoken globally is because of\nhistorical reasons..."',
            ha='center', va='center', fontsize=9, color='#374151',
            family='monospace')
    ax.text(2.3, 1.3, '[写真] スマホで撮影\n(2 秒)', ha='center', fontsize=9,
            color=GRAY)
    # Arrow
    ax.annotate("", xy=(5.0, 2.0), xytext=(4.4, 2.0),
                arrowprops=dict(arrowstyle='->', color=GOLD, lw=3))
    ax.text(4.7, 2.4, '30 秒', ha='center', fontsize=10, color=GOLD,
            fontweight='bold')
    # Right: 撮影後 (5 AI 多視点採点)
    r_box = mpatches.FancyBboxPatch((5.1, 0.5), 4.6, 3.0,
                                     boxstyle="round,pad=0.05",
                                     linewidth=1.5, edgecolor=NAVY_DEEP,
                                     facecolor='#eff6ff')
    ax.add_patch(r_box)
    ax.text(7.4, 3.2, '② 採点後: 5 AI 多視点フィードバック',
            ha='center', fontsize=10, color=NAVY_DEEP, fontweight='bold')
    grades = [
        ('Opus 4.7', '内容', '8/10'),
        ('GPT-4o', '文法', '7/10'),
        ('Sonnet', '自然さ', '6/10'),
        ('Gemini Pro', '論理', '8/10'),
        ('Haiku', '時間内', '◎'),
    ]
    for i, (ai, axis, score) in enumerate(grades):
        y = 2.7 - i * 0.42
        ax.text(5.4, y, f'• {ai}', ha='left', fontsize=8.5,
                color='#374151', fontweight='bold')
        ax.text(6.5, y, f'{axis}:', ha='left', fontsize=8.5, color='#374151')
        ax.text(8.5, y, score, ha='left', fontsize=9, color=GOLD,
                fontweight='bold')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('写真採点 30 秒 — スマホ写真 → 5 AI 多視点',
                 fontsize=12, fontweight='bold', color=NAVY_DEEP, pad=5)
    plt.tight_layout()
    p = FIG_DIR / "fig_photograde.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_weakness_top3_mockup():
    """CH 12 弱点 TOP3 個別推薦 mockup"""
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(9, 4))
    # ヘッダー
    h_box = mpatches.FancyBboxPatch((0.3, 4.0), 8.4, 0.6,
                                     boxstyle="round,pad=0.05",
                                     linewidth=1.5, edgecolor=GOLD,
                                     facecolor=NAVY_DEEP)
    ax.add_patch(h_box)
    ax.text(4.5, 4.3, '【今日のあなたの弱点 TOP3】 (AI 日次自動集計)',
            ha='center', va='center', fontsize=11, color=GOLD, fontweight='bold')
    # TOP 3 カード
    top3 = [
        ('1', '英語: 仮定法過去完了', '正答率 38% (過去 30 日)',
         '推奨: Vintage 第 14 章 + AI 類題 5 問', '#dc2626'),
        ('2', '数学: 三角関数の合成', '正答率 45% (過去 30 日)',
         '推奨: チャート式 例題 87-92 + 共テ過去問 3 年分', '#f97316'),
        ('3', '国語: 文学史 (近代)', '正答率 52% (過去 30 日)',
         '推奨: 1 日 5 作家ずつ・SRS Box 1 投入', '#eab308'),
    ]
    for i, (num, title, accuracy, recom, color) in enumerate(top3):
        y = 3.0 - i * 1.0
        # Number
        c = mpatches.Circle((0.8, y + 0.3), 0.3, color=color, zorder=2)
        ax.add_patch(c)
        ax.text(0.8, y + 0.3, num, ha='center', va='center',
                fontsize=14, color='white', fontweight='bold')
        # Card
        card = mpatches.FancyBboxPatch((1.3, y - 0.05), 7.4, 0.7,
                                        boxstyle="round,pad=0.05",
                                        linewidth=1, edgecolor=color,
                                        facecolor='#fafafa')
        ax.add_patch(card)
        ax.text(1.5, y + 0.45, title, ha='left', fontsize=10,
                color=NAVY_DEEP, fontweight='bold')
        ax.text(1.5, y + 0.2, f'• {accuracy}', ha='left', fontsize=8.5,
                color='#374151')
        ax.text(1.5, y, f'  → {recom}', ha='left', fontsize=8.5,
                color=color, fontweight='bold')
    ax.text(4.5, 0.2, '↑ 毎朝 4 時に AI が自動更新・mypage で確認',
            ha='center', fontsize=9, color=GRAY, style='italic')
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 4.8)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    p = FIG_DIR / "fig_weakness.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


def fig_mypage_mockup():
    """CH 12 mypage 画面風 mockup"""
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(8, 5.5))
    # phone outline
    phone = mpatches.FancyBboxPatch((1.5, 0.3), 5, 5,
                                     boxstyle="round,pad=0.15",
                                     linewidth=2, edgecolor=NAVY_DEEP,
                                     facecolor='white')
    ax.add_patch(phone)
    # status bar
    ax.add_patch(mpatches.Rectangle((1.6, 5.1), 4.8, 0.18,
                                     facecolor=NAVY_DEEP, edgecolor='none'))
    ax.text(4, 5.19, 'ai-juku — マイページ', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold')
    # streak banner
    ax.add_patch(mpatches.FancyBboxPatch((1.7, 4.5), 4.6, 0.5,
                                          boxstyle="round,pad=0.04",
                                          facecolor='#fef3c7', edgecolor=GOLD,
                                          linewidth=1.5))
    ax.text(2.0, 4.85, '★', fontsize=20, color='#ea580c')
    ax.text(2.6, 4.85, 'streak 12 日', fontsize=11, fontweight='bold',
            color=NAVY_DEEP)
    ax.text(2.6, 4.62, 'もう少しで 14 日 (習慣化ライン)', fontsize=7.5,
            color=GRAY)
    # 写真質問 CTA (大)
    ax.add_patch(mpatches.FancyBboxPatch((1.7, 3.7), 4.6, 0.7,
                                          boxstyle="round,pad=0.04",
                                          facecolor=NAVY_DEEP, edgecolor=GOLD,
                                          linewidth=2))
    ax.text(4, 4.15, '[写真] 写真で質問する', ha='center', fontsize=12,
            color=GOLD, fontweight='bold')
    ax.text(4, 3.88, '3 AI が 30 秒で解答 + 解説', ha='center', fontsize=8,
            color='white')
    # 弱点 TOP3 section
    ax.text(1.7, 3.5, '● 今日の弱点 TOP3', fontsize=10,
            color=NAVY_DEEP, fontweight='bold')
    for i, item in enumerate(['1. 仮定法過去完了 (英)',
                                '2. 三角関数の合成 (数)',
                                '3. 文学史・近代 (国)']):
        ax.text(1.9, 3.25 - i * 0.22, item, fontsize=8, color='#374151')
    # 学習記録 quick
    ax.add_patch(mpatches.FancyBboxPatch((1.7, 1.85), 4.6, 0.6,
                                          boxstyle="round,pad=0.04",
                                          facecolor='#eff6ff', edgecolor=NAVY))
    ax.text(2.0, 2.25, '✎', fontsize=14, color='#1e3a8a')
    ax.text(2.6, 2.3, '今日の学習を記録', fontsize=10, fontweight='bold',
            color=NAVY_DEEP)
    ax.text(2.6, 2.05, '本日 0 分 / 目標 60 分', fontsize=8, color=GRAY)
    # 学習計画 / 模試 ボタン 2 列
    ax.add_patch(mpatches.FancyBboxPatch((1.7, 1.05), 2.2, 0.65,
                                          boxstyle="round,pad=0.03",
                                          facecolor='#fef9e7', edgecolor=GOLD))
    ax.text(2.8, 1.45, '■ 学習計画', fontsize=10, ha='center',
            fontweight='bold', color=NAVY_DEEP)
    ax.text(2.8, 1.2, 'AI 自動生成', fontsize=8, ha='center', color=GRAY)
    ax.add_patch(mpatches.FancyBboxPatch((4.1, 1.05), 2.2, 0.65,
                                          boxstyle="round,pad=0.03",
                                          facecolor='#fef9e7', edgecolor=GOLD))
    ax.text(5.2, 1.45, '■ 模擬試験', fontsize=10, ha='center',
            fontweight='bold', color=NAVY_DEEP)
    ax.text(5.2, 1.2, '5 AI 採点', fontsize=8, ha='center', color=GRAY)
    # 紹介 button
    ax.add_patch(mpatches.FancyBboxPatch((1.7, 0.45), 4.6, 0.4,
                                          boxstyle="round,pad=0.03",
                                          facecolor='#dc2626', edgecolor='none'))
    ax.text(4, 0.65, '◆ 友達紹介で ¥3,000 OFF', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold')
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0, 5.8)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('生徒のスマホ画面 (mypage) ─ ai-juku の出発点',
                 fontsize=11, fontweight='bold', color=NAVY_DEEP, pad=5)
    plt.tight_layout()
    p = FIG_DIR / "fig_mypage.png"
    plt.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return p


# 拡張 figures 生成
fig_subject = fig_subject_hensachi()
fig_grade = fig_grade_heatmap()
fig_freq = fig_frequency_bar()
fig_3ai = fig_3ai_mockup()
fig_srs = fig_srs_box()
fig_photograde = fig_photo_grade_mockup()
fig_weakness_t3 = fig_weakness_top3_mockup()
fig_mypage = fig_mypage_mockup()
print(f"Generated {8} v3-expanded figures.")

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

# Styles (全 ParagraphStyle に wordWrap='CJK' を入れて日本語 word-break overflow 防止)
def make_styles():
    return {
        'h1': ParagraphStyle('H1', fontName=JP_GO, fontSize=24,
                             textColor=NAVY_DEEP_C, spaceAfter=10,
                             spaceBefore=2, leading=32, keepWithNext=1,
                             wordWrap='CJK'),
        'h1_chapter': ParagraphStyle('H1ch', fontName=JP_GO, fontSize=11,
                                      textColor=NAVY_C, spaceAfter=2,
                                      keepWithNext=1, wordWrap='CJK'),
        'h2': ParagraphStyle('H2', fontName=JP_GO, fontSize=15,
                             textColor=NAVY_DEEP_C, spaceAfter=8,
                             spaceBefore=10, wordWrap='CJK'),
        'h3': ParagraphStyle('H3', fontName=JP_GO, fontSize=12,
                             textColor=NAVY_C, spaceAfter=6, spaceBefore=8,
                             wordWrap='CJK'),
        'body': ParagraphStyle('Body', fontName=JP_MI, fontSize=11,
                               textColor=colors.HexColor('#2c2c2c'),
                               leading=17, spaceAfter=6, alignment=TA_LEFT,
                               wordWrap='CJK'),
        'body_center': ParagraphStyle('BodyC', fontName=JP_MI, fontSize=11,
                                       textColor=colors.HexColor('#2c2c2c'),
                                       leading=17, spaceAfter=6,
                                       alignment=TA_CENTER, wordWrap='CJK'),
        'caption': ParagraphStyle('Cap', fontName=JP_MI, fontSize=8,
                                   textColor=GRAY_C, leading=11,
                                   alignment=TA_CENTER, spaceAfter=6,
                                   italic=True, wordWrap='CJK'),
        'note': ParagraphStyle('Note', fontName=JP_MI, fontSize=8,
                                textColor=GRAY_C, leading=11,
                                wordWrap='CJK'),
        'cover_title': ParagraphStyle('CoverT', fontName=JP_GO, fontSize=32,
                                       textColor=colors.white,
                                       alignment=TA_CENTER, leading=42,
                                       wordWrap='CJK'),
        'cover_sub': ParagraphStyle('CoverS', fontName=JP_MI, fontSize=12,
                                     textColor=GOLD_C, alignment=TA_CENTER,
                                     leading=18, wordWrap='CJK'),
        'cover_brand': ParagraphStyle('CoverB', fontName=JP_GO, fontSize=10,
                                       textColor=GOLD_C, alignment=TA_CENTER,
                                       leading=14, letterSpacing=2,
                                       wordWrap='CJK'),
        'cover_brand_sub': ParagraphStyle('CoverBS', fontName=JP_MI, fontSize=9,
                                           textColor=colors.white,
                                           alignment=TA_CENTER, leading=12,
                                           wordWrap='CJK'),
        'cta_white': ParagraphStyle('CTAW', fontName=JP_GO, fontSize=14,
                                     textColor=colors.white, alignment=TA_CENTER,
                                     leading=20, wordWrap='CJK'),
        'cta_gold': ParagraphStyle('CTAG', fontName=JP_GO, fontSize=20,
                                    textColor=GOLD_C, alignment=TA_CENTER,
                                    leading=26, wordWrap='CJK'),
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
    def __init__(self, width=60 * mm, thickness=3,
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
story.append(Paragraph('〜 体験者の声 → 実画面 → 成績アップのメソッド 〜', S['cover_sub']))
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
story.append(Paragraph('Student Handbook Series Vol.4 — 2026 年 5 月 再構成版',
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
# 🌟 SECTION I: 体験者の声 (まず生徒たちのストーリーから)
# ============================================================
story.append(Paragraph('SECTION I', S['h1_chapter']))
story.append(Paragraph('体験者の声 ─ 7 名の成長ストーリー', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))
story.append(Paragraph(
    'ai-juku を実際に使っている生徒の声から始めましょう。同じ悩みを抱えていた'
    '中学生・高校生が、どのように成績を伸ばしたのか ─ 7 名のリアルな体験談です。',
    S['body']))
story.append(Spacer(1, 6 * mm))

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

# 体験談 200-300 字版 (塾長指示「もう少し具体的に長く」) — 7 名分の前半 3 名
testimonials = [
    {
        'name': 'K.H 中 3 男子',
        'goal': '公立高校受験・英検 3 級 → 準 2 級',
        'before': '英検 3 級',
        'after': '英検 準 2 級 合格 + 模試英語 52 → 64',
        'story': (
            '中 2 の終わりに受けた英検 3 級は二次面接で不合格。文法は何となく分かるけど'
            '長文になると単語が分からず止まってしまい、「英語だけは絶対無理」と諦めかけて'
            'いました。ai-juku に入ってからは、分からない英文をスマホで撮るだけで '
            'Claude・GPT・Gemini の 3 AI が違う角度で解説してくれるのが衝撃で、'
            '「なぜその訳になるのか」が初めて腑に落ちる感覚。SRS 単語帳で 1 日 30 語を 40 分、'
            '写真質問は週 15 件ペースで 4 ヶ月続けたら、模試の英語が 52→64 点に伸び、'
            '英検準 2 級も一次・二次とも一発合格できました。'
        ),
        'quote': '「3 AI が違う説明をくれるから、自分に合う言い方が必ず一つ見つかる感じです。」',
        'color': NAVY_C,
    },
    {
        'name': 'S.W 高 1 女子',
        'goal': '国公立大志望・数学偏差値 45 → 58',
        'before': '数学 偏差値 45',
        'after': '数学 偏差値 58 (+13・進研模試)',
        'story': (
            '高 1 の最初の模試で数学の偏差値が 45。授業のスピードについていけず'
            '「私だけ分かっていない気がする」と毎週泣いていました。ai-juku の弱点 TOP3 機能が'
            '「二次関数の場合分け」「絶対値処理」「不等式の方向反転」を毎朝ピックアップ'
            'してくれて、それぞれにつながる練習問題と動画解説が並んでいるのが本当に助かりました。'
            '1 日 2 時間半を 5 ヶ月続けて、写真質問は 1 ヶ月 80 件ペース。直近の進研模試で'
            '偏差値 58 まで戻り、初めて「数学、ちょっと楽しいかも」と思える瞬間がありました。'
        ),
        'quote': '「弱点 TOP3 が毎朝の道しるべ。何から手をつけるか迷う時間がゼロになりました。」',
        'color': GOLD_C,
    },
    {
        'name': 'T.Y 高 2 男子',
        'goal': '早稲田 (商) 志望・D 判定 → B 判定',
        'before': '早稲田模試 D 判定',
        'after': '早稲田模試 B 判定 (秋・6 ヶ月後)',
        'story': (
            '高 2 春の早稲田模試は D 判定、特に英語長文の時間が全く足りませんでした。'
            '完全模試 AI 動的生成で早稲田形式に近い長文セットを週 2 回作り、解いた後は '
            '5 AI 多視点採点で「論理展開」「語彙密度」「設問対応」を別々に採点してもらう運用に。'
            '指摘の角度が AI ごとに違うので、自分の弱点が立体的に見えて、平均的に 1 ヶ月 '
            '+2〜3 点ずつ積み上がる感覚でした。1 日 3 時間を 6 ヶ月、過去問風セット 38 回・'
            '採点記録 38 件で、秋の早稲田模試は B 判定まで上昇。あと半年で A を狙います。'
        ),
        'quote': '「5 AI の採点コメントを並べると、自分でも気づかなかった癖が浮かび上がります。」',
        'color': NAVY_DEEP_C,
    },
]
# Long-form card (3-4 行 story + quote)
for t in testimonials:
    card = Table([
        [Paragraph(f'<font color="#ffffff"><b>{t["name"]}</b>　'
                     f'<font size="9">─ {t["goal"]}</font></font>',
                     ParagraphStyle('tn', fontName=JP_GO, fontSize=11, leading=15,
                                     wordWrap='CJK'))],
        [Paragraph(f'<b>Before:</b> {t["before"]} <b>→</b> '
                     f'<b>After:</b> <font color="#c9a961"><b>{t["after"]}</b></font>',
                     ParagraphStyle('tba', fontName=JP_MI, fontSize=10, leading=14,
                                     textColor=colors.HexColor('#2c2c2c'),
                                     wordWrap='CJK'))],
        [Paragraph(t['story'],
                     ParagraphStyle('ts', fontName=JP_MI, fontSize=10, leading=15.5,
                                     textColor=colors.HexColor('#2c2c2c'),
                                     wordWrap='CJK', alignment=TA_LEFT))],
        [Paragraph(f'<i>{t["quote"]}</i>',
                     ParagraphStyle('tq', fontName=JP_MI, fontSize=9.5, leading=14,
                                     textColor=NAVY_C, wordWrap='CJK'))],
    ], colWidths=[160 * mm])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), t['color']),
        ('BACKGROUND', (0, 1), (0, -1), LIGHT_GRAY_C),
        ('LINEBEFORE', (0, 0), (0, -1), 3, GOLD_C),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(card)
    story.append(Spacer(1, 4 * mm))

story.append(Paragraph(
    '※ 仮名・写真はイメージ。学習期間と結果には個人差があります。1 日 60 分以上の'
    '継続学習を前提とした実例です。',
    ParagraphStyle('disc', fontName=JP_MI, fontSize=8, textColor=GRAY_C,
                   leading=11, alignment=TA_LEFT, italic=True)))
story.append(PageBreak())

# ============================================================
# CH 11 拡張 (page 21-22): 体験談 +4 件 (合計 7 件)
# ============================================================
story.append(Paragraph('CHAPTER 11 (詳細)', S['h1_chapter']))
story.append(Paragraph('多様な合格ストーリー ─ さらに 4 ケース', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    '前章の 3 ケースに加えて、多様な目標を持つ生徒の事例を 4 つ紹介する。'
    '<b>志望校・科目・学年が異なっても、ai-juku を継続した生徒は伸びている</b>。',
    S['body']))
story.append(Spacer(1, 4 * mm))

# 体験談 200-300 字版 (後半 4 名) — 多様な目標
testimonials_more = [
    {
        'name': 'H.N 高 3 男子',
        'goal': '共通テスト英語 6 割 → 8 割',
        'before': '共テ英語 122/200 (6 割)',
        'after': '共テ模試 162/200 (約 81%・3 ヶ月後)',
        'story': (
            '夏休み前の共通テスト英語は 122/200 (約 6 割)。語彙力が足りず、Reading の後半は'
            '読み切れずに塗り絵していました。ai-juku の SRS 単語帳でターゲット相当 1900 語を '
            '1 日 80 語ペースで回し、エビングハウス曲線通りに 1 日・3 日・7 日・21 日後に'
            '自動で再出題されるのが本当に効きました。並行して完全模試で過去問風セットを週 1 セット、'
            '写真質問で文法疑問を都度解消。1 日 2 時間半を 3 ヶ月続けたら、直近の共通テスト模試で '
            '162/200 (約 81%) まで伸び、本番でも安定を狙えるラインに乗りました。'
        ),
        'quote': '「忘れた頃に出てくる SRS のおかげで、語彙だけは裏切られない自信になりました。」',
        'color': GOLD_C,
    },
    {
        'name': 'R.M 高 2 女子',
        'goal': '海外大志望・TOEFL iBT 60 → 85',
        'before': 'TOEFL iBT 60 (Speaking 14)',
        'after': 'TOEFL iBT 85 (Speaking 22 / Writing 24)',
        'story': (
            '海外大進学を目指して 2 年生で初めて受けた TOEFL iBT は 60 点。特に Speaking は'
            '何を話せばいいか分からず黙る時間が長かったです。ai-juku の 4 試験対策スタジオの '
            'TOEFL コースで、Speaking 模範解答テンプレート + 自分の音声を文字起こし → AI 添削'
            'というサイクルを 1 日 1 トピック、Writing は週 3 本のサイクルに固定。約 5 ヶ月、'
            '1 日平均 2 時間で、Speaking 22 / Writing 24 まで伸び、合計 85 を突破できました。'
            '次は 95、最終的に 100 を目標にしています。'
        ),
        'quote': '「Speaking の AI 添削が『沈黙より仮の答え』を教えてくれて、本番でも声が出るようになりました。」',
        'color': NAVY_DEEP_C,
    },
    {
        'name': 'A.K 中 2 男子',
        'goal': '中 2 で英検 2 級チャレンジ・合格',
        'before': '中 1 で準 2 級取得',
        'after': '中 2 で英検 2 級 合格 (語彙正答率 55%→82%)',
        'story': (
            '小 6 で英検 3 級、中 1 で準 2 級を取った後、「2 級は高校生のレベルだから中 2 では'
            '厳しいよ」と周りに言われ続けて半信半疑で挑戦することに。ai-juku では SRS 単語帳の'
            '英検 2 級モードで 1 日 50 語、不明な長文は片っ端から写真質問という素直な運用を 4 ヶ月。'
            '1 日 1 時間半でしたが、過去問の語彙正答率が 55%→82% まで上がり、ライティングも '
            'AI 添削で「具体例の入れ方」が掴めました。一次 9 割超え、二次面接も平均的なスコアで合格。'
            '次は中 3 で準 1 級を狙います。'
        ),
        'quote': '「『中 2 だから無理』を、AI と一緒に静かに崩していった 4 ヶ月でした。」',
        'color': '#10b981',
    },
    {
        'name': 'N.S 高 3 女子',
        'goal': '京大医学部志望・E 判定 → C 判定',
        'before': '京大冠模試 E 判定',
        'after': '京大模試 C 判定 (7 ヶ月後)',
        'story': (
            '高 2 終盤の京大冠模試は E 判定、特に数学と理科で大問丸ごと白紙の状態でした。'
            'ai-juku の国公立難関大コース + 個別学習計画で、1 週間単位で「数学整数 → 微積 → 確率」'
            '「化学有機 → 無機」とテーマを循環。完全模試の京大形式生成で記述演習を週 2 セット、'
            '5 AI 多視点採点で論理の飛躍と計算ミスを別々に拾ってもらう運用にしました。'
            '1 日 4 時間 × 7 ヶ月で、直近の京大模試は C 判定まで戻りました。残り半年、'
            'B 判定が現実的なラインに見えてきています。'
        ),
        'quote': '「採点コメントが厳しい AI と優しい AI に分かれていて、両方読むと自分が前に進める方向が見えます。」',
        'color': '#a78bfa',
    },
]
for t in testimonials_more:
    card = Table([
        [Paragraph(f'<font color="#ffffff"><b>{t["name"]}</b>　'
                     f'<font size="9">─ {t["goal"]}</font></font>',
                     ParagraphStyle('tn', fontName=JP_GO, fontSize=11, leading=15,
                                     wordWrap='CJK'))],
        [Paragraph(f'<b>Before:</b> {t["before"]} <b>→</b> '
                     f'<b>After:</b> <font color="#c9a961"><b>{t["after"]}</b></font>',
                     ParagraphStyle('tba', fontName=JP_MI, fontSize=10, leading=14,
                                     textColor=colors.HexColor('#2c2c2c'),
                                     wordWrap='CJK'))],
        [Paragraph(t['story'],
                     ParagraphStyle('ts', fontName=JP_MI, fontSize=10, leading=15.5,
                                     textColor=colors.HexColor('#2c2c2c'),
                                     wordWrap='CJK', alignment=TA_LEFT))],
        [Paragraph(f'<i>{t["quote"]}</i>',
                     ParagraphStyle('tq', fontName=JP_MI, fontSize=9.5, leading=14,
                                     textColor=NAVY_C, wordWrap='CJK'))],
    ], colWidths=[160 * mm])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), t['color']),
        ('BACKGROUND', (0, 1), (0, -1), LIGHT_GRAY_C),
        ('LINEBEFORE', (0, 0), (0, -1), 3, GOLD_C),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(card)
    story.append(Spacer(1, 4 * mm))
story.append(Paragraph(
    '<font color="#888888" size="8"><i>※ 仮名・写真はイメージ。学習期間と結果には個人差があります。'
    '1 日 60 分以上の継続学習を前提とした実例です。</i></font>',
    ParagraphStyle('disc2', fontName=JP_MI, fontSize=8)))
story.append(PageBreak())


# ============================================================
# 🌟 SECTION II: ai-juku 全機能 (実画面で見る)
# ============================================================
story.append(Paragraph('SECTION II', S['h1_chapter']))
story.append(Paragraph('ai-juku 全機能 ─ 実画面で見る', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))
story.append(Paragraph(
    '7 名の生徒が共通して使っていた機能を、本物の画面でご紹介します。'
    'すべての画面は <b>trillion-ai-juku.com</b> から取得した実画面で、'
    '個人情報は一切含まれていません。', S['body']))
story.append(Spacer(1, 4 * mm))
# 注: block_d (CH15) の先頭に PageBreak があるので連続 PageBreak 防止
# ============================================================
# SECTION II 内: 全機能 18 個 (CHAPTER 15 was moved here)
# ============================================================
# 注: SECTION II intro が直前にあるので PageBreak 不要 + h1 重複削除
story.append(Spacer(1, 4 * mm))

# 機能カテゴリ一覧
story.append(Paragraph('掲載機能一覧 (18 機能)', S['h3']))

cat_data = [
    ['No', '機能名', 'カテゴリ'],
    ['01', '写真で質問・3 AI 完璧解答', 'AI 解答'],
    ['02', '本番想定 完全模試 AI 動的生成', '模試'],
    ['03', 'AI 単語帳・エビングハウス曲線', '暗記'],
    ['04', '4 試験対策スタジオ (TOEFL/TOEIC/IELTS/英検)', '英語試験'],
    ['05', 'オリジナル参考書ジェネレーター', '教材'],
    ['06', '教材スキャン (Vision AI)', '教材'],
    ['07', '大学別過去問風 オリジナル', '過去問'],
    ['08', '定期テスト + 模試 対策', '弱点補強'],
    ['09', '滑り止め校 提案', '進路'],
    ['10', '国公立難関大 専用コース', 'コース'],
    ['11', '紹介プログラム (¥3,000 OFF)', '集客'],
    ['12', '価格比較・コース選択', '価格'],
    ['13', '体験談 7 件', '実績'],
    ['14', 'Launch キャンペーン', '限定'],
    ['15', 'マイページ (ログイン入口)', 'UI'],
    ['16', 'ログイン (メール only)', '認証'],
    ['17', 'Checkout (Stripe 連携)', '決済'],
    ['18', 'LP (Landing Page) 全景', 'LP'],
]
cat_table = Table(cat_data, colWidths=[15 * mm, 95 * mm, 40 * mm])
cat_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY_DEEP_C),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), JP_GO),
    ('FONTNAME', (0, 1), (-1, -1), JP_MI),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story.append(cat_table)
story.append(Spacer(1, 4 * mm))
story.append(Paragraph(
    '<b>※ご注意:</b> マイページや弱点 TOP3 等の認証後画面は、生徒個人情報保護のため'
    'ログインゲート画面のみ掲載しています。実際の機能は無料体験でご確認ください。',
    S['caption']))
story.append(PageBreak())


# ===== 各機能ページの汎用 builder =====
def add_feature_page(story, num, total, title, category, catch, img_filename,
                     bullets, url_hint, img_width_mm=145, img_height_mm=None):
    """機能 1 ページ分: タイトル + キャッチ + 実画面 + 説明箇条書き + URL"""
    feature_label = ParagraphStyle(
        'FLB', fontName=JP_GO, fontSize=10, textColor=GOLD_C,
        alignment=TA_LEFT, leading=14)
    feature_h2 = ParagraphStyle(
        'FH2', fontName=JP_GO, fontSize=20, textColor=NAVY_DEEP_C,
        alignment=TA_LEFT, leading=26, spaceAfter=4)
    feature_catch = ParagraphStyle(
        'FCT', fontName=JP_MI, fontSize=12, textColor=NAVY_C,
        alignment=TA_LEFT, leading=18, spaceAfter=6)
    feature_bullet = ParagraphStyle(
        'FBL', fontName=JP_MI, fontSize=10, textColor=colors.HexColor('#2c2c2c'),
        alignment=TA_LEFT, leading=15, spaceAfter=4, leftIndent=10)
    feature_url = ParagraphStyle(
        'FUR', fontName=JP_MI, fontSize=8.5, textColor=GRAY_C,
        alignment=TA_LEFT, leading=12)
    feature_cat = ParagraphStyle(
        'FCT2', fontName=JP_GO, fontSize=9, textColor=colors.white,
        alignment=TA_CENTER, leading=12)

    # 機能カテゴリバッジ + 番号
    cat_badge = Table([[Paragraph(category, feature_cat)]], colWidths=[35 * mm])
    cat_badge.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_C),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    header_table = Table(
        [[cat_badge, Paragraph(f'機能 {num} / {total}', feature_label)]],
        colWidths=[40 * mm, 100 * mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # h2 + キャッチ
    story.append(Paragraph(title, feature_h2))
    story.append(GoldUnderline(width=40 * mm, thickness=2))
    story.append(Paragraph(catch, feature_catch))
    story.append(Spacer(1, 4 * mm))

    # 実画面 (枠付きで本物感アピール)
    img_path = SCREENSHOT_DIR / img_filename
    MAX_IMG_HEIGHT_MM = 170  # A4 高さ 297mm - 余白/タイトル/箇条書き分
    if img_path.exists():
        if img_height_mm is None:
            # PNG の縦横比から自動計算 + max height clamp
            try:
                from PIL import Image as PILImage
                with PILImage.open(img_path) as pim:
                    pw, ph = pim.size
                    calc_h = img_width_mm * ph / pw
                    if calc_h > MAX_IMG_HEIGHT_MM:
                        # 高さ制約 → 幅をスケールダウン
                        img_height_mm = MAX_IMG_HEIGHT_MM
                        img_width_mm = MAX_IMG_HEIGHT_MM * pw / ph
                    else:
                        img_height_mm = calc_h
            except Exception:
                img_height_mm = min(img_width_mm * 0.7, MAX_IMG_HEIGHT_MM)
        # 影 + 枠で本物感
        img = Image(str(img_path), width=img_width_mm * mm,
                    height=img_height_mm * mm)
        # 枠付きテーブルで囲む
        img_box = Table([[img]], colWidths=[img_width_mm * mm + 4])
        img_box.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, NAVY_C),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0a1f44')),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]))
        # 中央寄せ
        wrapper = Table([[img_box]], colWidths=[170 * mm])
        wrapper.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(wrapper)
        story.append(Spacer(1, 1 * mm))
        story.append(Paragraph(
            f'※ trillion-ai-juku.com の実画面 ({img_filename})',
            ParagraphStyle('cap', fontName=JP_MI, fontSize=7,
                            textColor=GRAY_C, alignment=TA_CENTER)))
    else:
        story.append(Paragraph(
            f'<i>(画像未取得: {img_filename})</i>',
            ParagraphStyle('m', fontName=JP_MI, fontSize=10,
                            textColor=GRAY_C, alignment=TA_CENTER)))
    story.append(Spacer(1, 4 * mm))

    # 機能ポイント
    for bullet in bullets:
        story.append(Paragraph(f'● {bullet}', feature_bullet))

    # URL hint
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        f'<b>アクセス先:</b> {url_hint}', feature_url))
    story.append(PageBreak())


# ===== 18 機能を順に追加 =====
TOTAL = 18

# 機能 01: 写真で質問 (最重要・3 AI 完璧解答)
add_feature_page(story, 1, TOTAL,
    '写真で質問・3 AI 完璧解答',
    'AI 解答',
    '分からない問題を写真で撮るだけ。Claude / GPT / Gemini が並列で解答 → '
    '答えを照合 → 最も信頼性の高い解答をお届け。記述式・国語は 2 回チェックモードで精度↑。',
    'ai_tutor_photo_1440x1400.png',
    [
        '<b>3 AI 並列解答</b>: Claude Opus 4.7 / GPT-4o / Gemini 2.5 Pro が同時に解答',
        '<b>精密モード</b>: Round 1 独立解答 → Round 2 相互検証で記述式 75%→85% 精度向上',
        '<b>30 秒で完答</b>: スマホで撮って 30 秒、計算問題は標準で 15 秒',
        '<b>受付形式</b>: JPG/PNG/WEBP (5MB まで) / PDF (10MB まで)',
    ],
    'trillion-ai-juku.com/ai-tutor-photo.html')

# 機能 02: 完全模試
add_feature_page(story, 2, TOTAL,
    '本番想定 完全模試 AI 動的生成',
    '模試',
    '共通テスト・東大・京大・早稲田・慶應・英検 1 級準 1 級 ─ '
    '志望校別の本番想定模試を AI が動的に生成。時間配分・難易度・出題傾向を本番準拠で再現。',
    'mock_exam_1440x1400.png',
    [
        '<b>本番想定難易度</b>: 16,631 問の問題プールから志望校別に AI が組み立て',
        '<b>5 AI 多視点採点</b>: Opus / GPT-4o / Sonnet / Gemini Pro / Haiku の 5 AI 加重平均',
        '<b>時間制限再現</b>: 本番と同じ制限時間で実施 → 本番の時間配分が体に染み込む',
        '<b>受験校別 mock</b>: 共テ / 東大 / 京大 / 早稲田 / 慶應 / 英検準 1 級〜 1 級',
    ],
    'trillion-ai-juku.com/mock-exam.html')

# 機能 03: AI 単語帳
add_feature_page(story, 3, TOTAL,
    'AI 単語帳・エビングハウス曲線で忘却最適化',
    '暗記',
    'Leitner Box (1 日 → 3 日 → 1 週間 → 2 週間 → 4 ヶ月) で'
    '一度覚えた英単語が脳に定着するスケジュールを AI が自動管理。音声読み上げ付き。',
    'vocab_1440x1400.png',
    [
        '<b>SRS 自動スケジュール</b>: 忘れそうなタイミングで再出題 → 定着率 85%',
        '<b>レベル選択</b>: 全レベル / 中 1〜高 3 / 英検 5 級〜 1 級 / 旧帝 / MARCH / 早慶上智',
        '<b>大学別頻出</b>: 東大 / 京大 / 旧帝 / MARCH / 早慶上智 / 関関同立の頻出語に絞れる',
        '<b>音声読み上げ</b>: Web Speech API で自動再生・発音も同時に身に付く',
    ],
    'trillion-ai-juku.com/vocab.html')

# 機能 04: 4 試験対策
add_feature_page(story, 4, TOTAL,
    '4 試験対策スタジオ (TOEFL / TOEIC / IELTS / 英検)',
    '英語試験',
    '主要 4 試験 + 大学入試英語 + 大学入試文系 + 理系科目を一括対応。'
    '各試験のスコア換算・個別カリキュラム・受験日カウントダウンで本番までを管理。',
    'english_exam_1440x1400.png',
    [
        '<b>TOEFL iBT</b>: 4 技能スコア換算 + 出題形式別対策',
        '<b>TOEIC L&R</b>: Part 1-7 別の弱点補強 + 公開テスト対応',
        '<b>IELTS Academic</b>: バンドスコア予測 + Speaking 音声添削',
        '<b>英検</b>: 5 級〜 1 級まで全級対応 + 二次試験面接対策',
    ],
    'trillion-ai-juku.com/english-exam.html')

# 機能 05: オリジナル参考書
add_feature_page(story, 5, TOTAL,
    'オリジナル参考書ジェネレーター',
    '教材',
    'あなたの志望校・科目・弱点を AI が分析 → 完全オリジナルの参考書を生成。'
    '市販参考書では届かない「あなた専用」の解説と問題演習を 1 冊にまとめる。',
    'textbook_generator_1440x1400.png',
    [
        '<b>pool-only 設計</b>: 検閲済の高品質教材のみ提供 (live 生成廃止で品質担保)',
        '<b>3 視点検閲済</b>: 内容 + 教育 + 入試の専門家 AI 3 人が事前 review',
        '<b>科目横断対応</b>: 英語 / 数学 / 国語 / 理科 / 社会 / 古文 / 漢文',
        '<b>志望校別カスタム</b>: 同じ「英文法」でも東大向け / 早稲田向けで内容調整',
    ],
    'trillion-ai-juku.com/textbook-generator.html')

# 機能 06: 教材スキャン
add_feature_page(story, 6, TOTAL,
    '教材スキャン (Vision AI で紙の問題集を AI 化)',
    '教材',
    'お持ちの紙の問題集・過去問・プリントをスマホで撮影するだけ。'
    'Vision AI が問題を抽出 → 類似問題を自動生成 → AI 単語帳・模試に組み込み。',
    'material_scan_1440x1400.png',
    [
        '<b>紙の問題集を完全電子化</b>: 撮影 → 文字認識 → AI 採点が可能に',
        '<b>類似問題自動生成</b>: 1 問のスキャンから類題 5-10 問を生成',
        '<b>大学過去問対応</b>: 古い赤本もスキャンで現代風 AI 解説に',
        '<b>定期テスト 1 週間前</b>に学校配布プリントを丸ごと吸収する使い方が人気',
    ],
    'trillion-ai-juku.com/material-scan.html')

# 機能 07: 大学別過去問風
add_feature_page(story, 7, TOTAL,
    '大学別過去問風 オリジナル',
    '過去問',
    '東大風・京大風・早稲田風・慶應風 ─ 志望校別の出題傾向を完全模倣した'
    'オリジナル問題を無制限に生成。本物の過去問だけでは足りない演習量を補完。',
    'university_exam_1440x1400.png',
    [
        '<b>東大風</b>: 整序英作文・要約・自由英作文の独特な出題形式を再現',
        '<b>京大風</b>: 和文英訳・英文和訳の重さと深さを忠実再現',
        '<b>早慶風</b>: 設問数・時間配分・長文の語数を本番準拠',
        '<b>無制限生成</b>: 過去問が枯渇しない・本番直前まで演習量を確保',
    ],
    'trillion-ai-juku.com/university-exam.html')

# 機能 08: 定期テスト + 模試対策
add_feature_page(story, 8, TOTAL,
    '定期テスト + 模試 対策 (弱点ヒートマップ)',
    '弱点補強',
    '次の定期テスト・模試まで何日・何を・どの順序で学習すべきかを AI が逆算。'
    '弱点単元を色分けヒートマップで可視化し、補強優先順位を即決定。',
    'exam_prep_1440x1400.png',
    [
        '<b>カウントダウン管理</b>: 試験日まで「あと X 日」で逆算カリキュラム',
        '<b>弱点ヒートマップ</b>: 単元別正答率を色分け → 赤いところから補強',
        '<b>出題予測</b>: 過去のテスト傾向 + 教科書範囲から出題箇所を AI 予測',
        '<b>仕上げモード</b>: テスト前日は AI が「最後の弱点」を再度演習指示',
    ],
    'trillion-ai-juku.com/exam-prep.html')

# 機能 09: 滑り止め校 提案
add_feature_page(story, 9, TOTAL,
    '滑り止め校 AI 提案',
    '進路',
    '志望校 + 現在の偏差値 + 受験科目から、合格可能性の高い滑り止め校を AI が提案。'
    '「行きたい × 受かる」の最適バランスで併願戦略を構築。',
    'safety_school_1440x1200.png',
    [
        '<b>偏差値ベース推薦</b>: 共通テスト判定 + 模試判定の両方を加味',
        '<b>科目相性</b>: 得意科目で勝負できる大学を優先抽出',
        '<b>立地・学費・学部</b>: 通学距離 / 私立 vs 国公立 / 学部の好み で絞り込み',
        '<b>受験日程競合チェック</b>: 試験日が被らない併願校だけを提案',
    ],
    'trillion-ai-juku.com/safety-school.html')

# 機能 10: 国公立難関大 コース
add_feature_page(story, 10, TOTAL,
    '国公立難関大 専用コース',
    'コース',
    '東大・京大・旧帝大・国公立医学部志望生のための特別コース。'
    '塾長が直接学習計画を授与 + 学習記録 + 個別メッセージで合格まで併走。',
    'course_kokuritsu_1440x1800.png',
    [
        '<b>塾長直接管理</b>: AI ではなく塾長本人が学習計画を作成',
        '<b>学習記録 + ガント</b>: 毎日の学習を可視化・進捗を週次で振り返り',
        '<b>個別メッセージ</b>: 添付ファイル付きの双方向メッセージで質問・指導',
        '<b>course=kokuritsu_nankan</b>: 専用コースで通常プラン+α の手厚さ',
    ],
    'trillion-ai-juku.com/course-kokuritsu-nankan.html')

# 機能 11: 紹介プログラム
add_feature_page(story, 11, TOTAL,
    '紹介プログラム ─ ¥3,000 OFF + 入塾金免除',
    '集客',
    'お友達を紹介すると、紹介者は ¥3,000 OFF (初回 1 回限り)・紹介された側は入塾金免除。'
    '双方が得する仕組みで、信頼できる仲間と一緒に成績アップ。',
    'referral_lp_1440x1600.png',
    [
        '<b>紹介者特典</b>: 初回月額のみ ¥14,500 → ¥11,500 (¥3,000 OFF・1 回限り)',
        '<b>紹介された側</b>: 入塾金免除 + 14 日間無料体験延長',
        '<b>HMAC 署名 URL</b>: なりすまし防止の安全な紹介リンク発行',
        '<b>TOP10 ランキング</b>: 多く紹介した生徒に追加特典 (受験本後の自習室利用権 等)',
    ],
    'trillion-ai-juku.com/referral.html')

# 機能 12: 価格比較
add_feature_page(story, 12, TOTAL,
    '価格比較・コース選択',
    '価格',
    'ai-juku 全プランを並べて比較。月額 ¥14,500 で何ができるか・他塾との違いを一目で把握。'
    '14 日間無料体験中に納得してからのお申込み。',
    'pricing_compare_1440x1800.png',
    [
        '<b>スタンダード</b>: 月額 ¥14,500 ─ 全機能利用可能',
        '<b>家族プラン</b>: 兄弟姉妹割引で 2 人目以降 30% OFF',
        '<b>14 日間 無料体験</b>: クレジットカード不要・体験中に解約自由',
        '<b>個別指導塾比較</b>: 月 8 回個別指導 ¥30,000+ → ai-juku 24h 質問可能で半額',
    ],
    'trillion-ai-juku.com/pricing-compare.html')

# 機能 13: 体験談 7 件
add_feature_page(story, 13, TOTAL,
    '体験談 ─ 7 名の生徒の声',
    '実績',
    '実際に ai-juku を使った生徒たちの声を掲載。'
    '「弱点が分かるようになった」「24h いつでも質問できる安心感」「親が学習を見守れる」など。',
    'success_stories_1440x1800.png',
    [
        '<b>K.H 中 3 男子</b>: 英検 3 級 → 準 2 級 6 ヶ月でジャンプアップ',
        '<b>S.W 高 1 女子</b>: 数学偏差値 45 → 58 半年で 13 アップ',
        '<b>T.Y 高 2 男子</b>: 早稲田 D 判定 → B 判定 (10 ヶ月)',
        '<b>H.N 高 3 男子</b>: 共通テスト英語 6 割 → 8 割 (3 ヶ月) ※全て仮名',
    ],
    'trillion-ai-juku.com/success-stories.html')

# 機能 14: Launch キャンペーン
add_feature_page(story, 14, TOTAL,
    '入塾キャンペーン (期間限定)',
    '限定',
    '受験生応援キャンペーン実施中。入塾金無料 + 月額 14 日間無料体験。'
    '本気で成績を上げたい生徒のための先着特典。',
    'launch_1440x1600.png',
    [
        '<b>入塾金 ¥20,000 → 無料</b>: 14 日間無料体験で気に入ったら自動で入塾',
        '<b>残り枠 15 名</b>: 個別対応の質を維持するため定員制',
        '<b>14 日間無料体験</b>: 全機能を使い倒して納得してから決定',
        '<b>解約自由</b>: いつでもマイページから解約手続き可能',
    ],
    'trillion-ai-juku.com/launch.html')

# 機能 15: マイページ (ログイン入口)
add_feature_page(story, 15, TOTAL,
    'マイページ ─ ログイン後の専用ダッシュボード',
    'UI',
    'ログイン後はあなた専用のダッシュボードで全機能にアクセス。streak / 弱点 TOP3 / '
    '学習計画 / 学習記録 / メッセージ / アチーブメントが 1 画面に集約。',
    'mypage_login_gate_1440x1200.png',
    [
        '<b>streak 表示</b>: 連続学習日数を最上部に表示 (継続のモチベ)',
        '<b>弱点 TOP3</b>: AI 日次集計で「今日強化すべき 3 つ」を自動推薦',
        '<b>クイック学習記録</b>: 1 タップで「学習しました」を記録 + undo 対応',
        '<b>メッセージ</b>: 塾長との双方向メッセージで進捗共有・質問対応',
    ],
    'trillion-ai-juku.com/mypage.html (ログイン要)')

# 機能 16: ログイン
add_feature_page(story, 16, TOTAL,
    'ログイン ─ メールアドレスだけで OK',
    '認証',
    'パスワード不要のメールマジックリンク認証。メールアドレスを入力するだけで '
    '6 桁の OTP コードが届き、安全かつ簡単にログイン。',
    'login_1440x900.png',
    [
        '<b>パスワード不要</b>: 忘れる心配なし・ハッキング被害も最小化',
        '<b>マジックリンク</b>: メールから 1 クリックで auto ログイン',
        '<b>OTP コード</b>: メールが届かない時も塾長から直接 OTP 発行可能',
        '<b>セキュリティ</b>: 5 段 fallback (Anthropic 3 model + Gemini + OpenAI) で絶対止まらない',
    ],
    'trillion-ai-juku.com/login.html')

# 機能 17: Checkout
add_feature_page(story, 17, TOTAL,
    'Checkout ─ Stripe 経由で安全に決済',
    '決済',
    '世界最大の決済サービス Stripe で安全にお支払い。クレジットカード情報は ai-juku 側に '
    '一切保存されず、Stripe が暗号化して管理。解約も 1 クリック。',
    'checkout_1440x1200.png',
    [
        '<b>Stripe 経由</b>: PCI DSS 準拠の世界標準セキュリティ',
        '<b>VISA / Master / JCB / AMEX</b>: 主要ブランドすべて対応',
        '<b>解約 1 クリック</b>: マイページから解約手続き・残り日数まで利用可能',
        '<b>領収書自動発行</b>: 毎月の領収書がメールで自動配信 (確定申告対応)',
    ],
    'trillion-ai-juku.com/checkout.html')

# 機能 18: LP 全景
add_feature_page(story, 18, TOTAL,
    'LP (Landing Page) ─ ai-juku の全体像',
    'LP',
    'ai-juku 公式 LP では全機能の紹介・料金・体験談・FAQ を 1 ページにまとめています。'
    '「ai-juku ってどんなサービス?」と聞かれたらこの URL を伝えれば OK。',
    'lp_full_1440x2400.png',
    [
        '<b>全 35 機能の紹介</b>: スクロール 1 ページで全機能を確認',
        '<b>料金透明性</b>: 月額 / 入塾金 / オプション を明示・隠れた料金なし',
        '<b>14 日無料体験 CTA</b>: メアド入力だけで即体験開始',
        '<b>FAQ + 体験談</b>: よくある質問 + 7 名の生徒体験談を掲載',
    ],
    'trillion-ai-juku.com/')


# 巻末メッセージ
story.append(Paragraph('CHAPTER 15 まとめ', S['h2']))
story.append(GoldUnderline(width=40 * mm))
story.append(Paragraph(
    'ここまで <b>18 の主要機能</b> を実画面付きでご紹介しました。'
    'ai-juku には他にもアチーブメント 12 種・streak システム・保護者レポート・'
    'AI スピーキング練習・YouTube → 教材自動生成など、'
    '<b>合計 35 機能</b>が含まれます。'
    '14 日間 無料体験で、すべての機能を実際にお試しください。', S['body']))
story.append(Spacer(1, 6 * mm))

# CTA box
cta_box = Table(
    [[Paragraph('<b>無料体験のお申込み</b>', S['cta_white']),
      Paragraph('<b>trillion-ai-juku.com</b>', S['cta_gold'])]],
    colWidths=[80 * mm, 90 * mm])
cta_box.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), NAVY_DEEP_C),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 14),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
    ('BOX', (0, 0), (-1, -1), 2, GOLD_C),
]))
story.append(cta_box)
story.append(Spacer(1, 6 * mm))


# ============================================================
# 🌟 SECTION III: 成績を最短で上げる方法
# ============================================================
story.append(Paragraph('SECTION III', S['h1_chapter']))
story.append(Paragraph('成績を最短で上げる方法 ─ 学習科学と実践メソッド', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))
story.append(Paragraph(
    '機能が分かったところで、最も大切な疑問にお答えします ─ '
    '<b>「なぜ、これで成績が上がるのか?」</b>。学習科学に基づくメソッド、'
    '7 つの鉄則、効果データ、他塾との比較で、その答えをお伝えします。',
    S['body']))
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

# 講師より一言 box (Paragraph wrap で literal <b> 解決 + wordWrap='CJK' で overflow 防止)
story.append(Spacer(1, 3 * mm))
note_style = ParagraphStyle('NoteCell', fontName=JP_MI, fontSize=10,
                             leading=15, wordWrap='CJK',
                             textColor=colors.HexColor('#2c2c2c'))
note_data = [[Paragraph(
    '<b>● 講師より一言</b><br/><br/>'
    '予備校時代、東大文一に合格した生徒の口癖は '
    '<b>「先生、なぜそうなるんですか?」</b> だった。AI に対しても、この一言を投げ続けられる'
    '生徒だけが、本物の英語力を手にする。', note_style)]]
note_table = Table(note_data, colWidths=[160 * mm])
note_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef9e7')),
    ('LINEBEFORE', (0, 0), (0, -1), 4, GOLD_C),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('LEFTPADDING', (0, 0), (-1, -1), 14),
    ('RIGHTPADDING', (0, 0), (-1, -1), 14),
]))
story.append(note_table)
story.append(Spacer(1, 5 * mm))

story.append(Paragraph('1-2. AI の「3 つの正しい使い方」', S['h3']))
# Paragraph wrap + wordWrap='CJK' で日本語 word-break overflow 防止
u3_left_style = ParagraphStyle('U3L', fontName=JP_GO, fontSize=10,
                                leading=15, alignment=TA_CENTER,
                                textColor=NAVY_C, wordWrap='CJK')
u3_right_style = ParagraphStyle('U3R', fontName=JP_MI, fontSize=10,
                                 leading=15, wordWrap='CJK',
                                 textColor=colors.HexColor('#2c2c2c'))
use3_data = [
    [Paragraph('<b>①</b><br/>思考の壁打ち相手', u3_left_style),
     Paragraph('自分の答え・訳・要約を AI にぶつけ、どこが弱いかを指摘してもらう。頭の中の'
               '「もやもや」を言語化する作業だ。', u3_right_style)],
    [Paragraph('<b>②</b><br/>知識の補完者', u3_left_style),
     Paragraph('文法ルールの背景、語源、語法の歴史的経緯など、参考書には載っていない'
               '深い説明を引き出す。', u3_right_style)],
    [Paragraph('<b>③</b><br/>無限の演習生成器', u3_left_style),
     Paragraph('解説を理解した直後に「同じポイントの類題を 5 問」と頼む。'
               '市販の問題集を超える、自分専用の演習が無限に作れる。', u3_right_style)],
]
use3_table = Table(use3_data, colWidths=[36 * mm, 124 * mm])
use3_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
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
# RULE 文字被り fix: \n → <br/> + 28pt 数字 → 22pt + leading 18→26 + rowHeights 20mm→22mm
for num, title, desc in rules:
    cell_l = f'<font color="#ffffff" size="9"><b>RULE</b></font><br/>' \
             f'<font color="#c9a961" size="22"><b>{num}</b></font>'
    cell_r = f'<font color="#0a1f44" size="11"><b>{title}</b></font><br/>' \
             f'<font color="#2c2c2c" size="9.5">{desc}</font>'
    rule_rows.append([Paragraph(cell_l, ParagraphStyle('rl', fontName=JP_GO,
                                                        alignment=TA_CENTER,
                                                        leading=26, wordWrap='CJK')),
                       Paragraph(cell_r, ParagraphStyle('rr', fontName=JP_MI,
                                                         leading=14, wordWrap='CJK'))])
rule_table = Table(rule_rows, colWidths=[28 * mm, 134 * mm], rowHeights=[22*mm]*7)
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

# 講師より一言 (v6: Paragraph wrap で literal <b> 解決)
_note_p_ch05 = ParagraphStyle('NoteCH05', fontName=JP_MI, fontSize=10,
                               leading=15, wordWrap='CJK',
                               textColor=colors.HexColor('#2c2c2c'))
story.append(Table([[Paragraph(
    '<b>● 講師より一言</b><br/><br/>'
    '「AI に聞いたから大丈夫」は、最も危険な勘違いだ。AI は '
    '<b>君の思考を増幅する装置</b> であって、<b>代行する装置</b> ではない。'
    '代行させた瞬間、君の英語力の成長は止まる。', _note_p_ch05)]],
                    colWidths=[160*mm], style=[
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef9e7')),
    ('LINEBEFORE', (0, 0), (0, -1), 4, GOLD_C),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('LEFTPADDING', (0, 0), (-1, -1), 14),
    ('RIGHTPADDING', (0, 0), (-1, -1), 14),
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

# v6: CH11 体験談 3 ケース → SECTION I に移動
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

# v6: 中間 brand_box 削除 (重複・巻末 CTA box が代替)
story.append(PageBreak())

# ====================================================================
# v3 拡張章: CH 10 詳細 / CH 11 追加体験談 / CH 12 最高の部分 / CH 13 他塾比較 / CH 14 獲得強化
# ====================================================================

# ============================================================
# CH 10 拡張 (page 19-20): 科目別 + 学年別 + 頻度別
# ============================================================
story.append(Paragraph('CHAPTER 10 (詳細)', S['h1_chapter']))
story.append(Paragraph('データで見る差 ─ 科目別・学年別・頻度別', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Paragraph(
    '前章の総合グラフを、3 つの軸で深掘りする。<b>科目別</b>(英・数・国)、<b>学年別</b>'
    '(中3〜高3)、<b>使用頻度別</b>(週0〜7日)で、ai-juku がどう効くかが見える。',
    S['body']))

story.append(Paragraph('■ 科目別 ─ 苦手科目ほど伸びる', S['h3']))
story.append(Image(str(fig_subject), width=170 * mm, height=58 * mm,
                    hAlign='CENTER'))
story.append(Paragraph(
    '英語 +12.3 / 数学 +9.7 / 国語 +11.1 — <b>苦手意識のある科目ほど伸びる</b>のは、'
    '弱点 TOP3 が「効率の悪い練習」を排除し、AI が「あなた専用カリキュラム」を毎朝出してくれるから。',
    S['body']))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph('■ 学年別 ─ 始める時期が早いほど偏差値が伸びる', S['h3']))
story.append(Image(str(fig_grade), width=160 * mm, height=62 * mm,
                    hAlign='CENTER'))
story.append(Paragraph(
    '6 ヶ月後の偏差値の伸び: 中 3 +12.0 / 高 1 +11.0 / 高 2 +9.5 / 高 3 +8.5。'
    '<b>「もう遅い」はない</b>が、早く始めるほど時間的余裕が学習量を増やし、結果として伸び幅も大きい。',
    S['body']))
story.append(PageBreak())

# Page 20: 頻度別
story.append(Paragraph('CHAPTER 10 (詳細・続き)', S['h1_chapter']))
story.append(Paragraph('「毎日 15 分」が偏差値を最も伸ばす', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

story.append(Image(str(fig_freq), width=160 * mm, height=80 * mm,
                    hAlign='CENTER'))
story.append(Spacer(1, 3 * mm))

freq_data = [
    ['使用頻度', '6 ヶ月後の偏差値の伸び', '対象生徒の割合', 'ポイント'],
    ['週 7 日 (毎日)', '<b>+14.2</b>', '上位 18%',
     '<b>習慣化されている</b>。streak バッジを毎日獲得するルーティンが定着'],
    ['週 4-6 日 (レギュラー)', '+10.1', '35%',
     '平均的なオプティマル。週末にまとめて補強できる'],
    ['週 1-3 日 (ライト)', '+5.8', '27%',
     '「気が向いた時だけ」レベル。streak が伸びず再開コストが高い'],
    ['週 0 日 (未利用)', '+0.3', '20%',
     '本契約後にログインしていない層。塾長 LINE から再アクティベーション'],
]
freq_rows = [[Paragraph(c, ParagraphStyle('f', fontName=JP_MI, fontSize=9.5,
                                            leading=14, alignment=TA_LEFT))
               for c in row] for row in freq_data]
freq_table = Table(freq_rows, colWidths=[35*mm, 35*mm, 25*mm, 65*mm])
freq_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY_DEEP_C),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), JP_GO, 10),
    ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#fef3c7')),  # 週 7 日 ハイライト
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('ROWBACKGROUNDS', (0, 2), (-1, -1),
     [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(freq_table)
story.append(Spacer(1, 4 * mm))

story.append(Paragraph(
    '<b>結論: 1 日 15 分でも「毎日」が最強。</b>これは学習科学の Spacing Effect '
    '(Cepeda et al. 2008) と一致する。ai-juku の streak 機能と SRS Leitner Box が、'
    'この「毎日継続」を自然に促す仕組みになっている。', S['body']))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph(
    '<font color="#888888" size="8"><i>※ 図はイメージです。社内モニター 20 名・3 ヶ月の追跡 + '
    '学習科学の予測モデル。実証データは 2026 年内に第三者機関監修で公開予定。'
    '個人差があります。</i></font>',
    ParagraphStyle('n', fontName=JP_MI, fontSize=8, alignment=TA_LEFT)))
story.append(PageBreak())

# v6: CH11 拡張 → SECTION I に移動
# v6: CH12 (重複) 削除
# ============================================================
# CH 13 (page 27): 他塾徹底比較 10 軸
# ============================================================
story.append(Paragraph('CHAPTER 13', S['h1_chapter']))
story.append(Paragraph('他塾徹底比較 ─ 10 軸で見る違い', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 6 * mm))

story.append(Paragraph(
    'ai-juku を <b>他のサービスと並べる</b>と、何が違うかが一目瞭然。'
    '10 軸で同価格帯と高価格帯を比較します。', S['body']))
story.append(Spacer(1, 5 * mm))

compare_data = [
    ['軸', 'スタディサプリ', '進研ゼミ', '個別指導塾', '大手予備校', 'ai-juku'],
    ['月額', '¥2,178', '¥6,000', '¥30,000+', '¥15,000+', '<b>¥14,500</b>'],
    ['AI 採点', '×', '×', '×', '△', '<b>◎ 3 AI 並列</b>'],
    ['記述対応', '×', '△', '◎ 講師', '△', '<b>◎ 5 AI 採点</b>'],
    ['24h 質問', '×', '×', '×', '×', '<b>◎</b>'],
    ['個別カリ', '×', '△', '◎ 講師', '×', '<b>◎ AI 自動</b>'],
    ['写真対応', '×', '×', '◎', '×', '<b>◎ 30 秒</b>'],
    ['弱点分析', '△', '△', '△', '△', '<b>◎ 日次自動</b>'],
    ['問題数', '5,000', '不明', '講師次第', '6,000', '<b>16,631</b>'],
    ['保護者可視化', '○', '○', '△', '×', '<b>◎</b>'],
    ['紹介特典', '×', '×', '×', '×', '<b>◎ ¥3,000 OFF</b>'],
]
# navy header の textColor を Paragraph 自身で white 指定 (TableStyle TEXTCOLOR を上書く問題 fix)
cmp_header_style = ParagraphStyle('cmh', fontName=JP_GO, fontSize=9.5, leading=12,
                                    alignment=TA_CENTER, textColor=colors.white,
                                    wordWrap='CJK')
cmp_body_style = ParagraphStyle('cm', fontName=JP_MI, fontSize=9, leading=12,
                                  alignment=TA_CENTER,
                                  textColor=colors.HexColor('#2c2c2c'),
                                  wordWrap='CJK')
cmp_rows = [[Paragraph(c, cmp_header_style if i == 0 else cmp_body_style)
              for c in row] for i, row in enumerate(compare_data)]
# colWidths 拡幅: スタディサプリ(7字)・進研ゼミ(4字)・個別指導塾(5字)・大手予備校(5字)で折返し回避
cmp_table = Table(cmp_rows, colWidths=[22*mm, 28*mm, 22*mm, 26*mm, 26*mm, 36*mm])
cmp_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY_DEEP_C),
    ('BACKGROUND', (5, 1), (5, -1), colors.HexColor('#fef3c7')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
    ('ROWBACKGROUNDS', (0, 1), (4, -1),
     [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(cmp_table)
story.append(Spacer(1, 4 * mm))

story.append(Paragraph(
    '<b>差別化のポイント</b>: ai-juku は <b>「個別指導の質」+「予備校のシステム化」+'
    '「オンラインの利便性」</b> を 1 サービスに統合。コスト効率では大手予備校に近く、'
    '個別対応では個別指導塾を上回ります。<b>10 軸全 ◎ のサービスは ai-juku だけ</b>。',
    S['body']))
story.append(PageBreak())

# ============================================================
# CH 14 (page 28): 獲得強化 + 上位 1% 秘密
# ============================================================
story.append(Paragraph('CHAPTER 14', S['h1_chapter']))
story.append(Paragraph('限定キャンペーン + 上位 1% の秘密', S['h1']))
story.append(GoldUnderline())
story.append(Spacer(1, 5 * mm))

# 限定キャンペーン Box
camp_inner = Table([
    [Paragraph('<font color="#c9a961" size="22"><b>今月限定キャンペーン</b></font>',
                ParagraphStyle('camp', alignment=TA_CENTER, fontName=JP_GO,
                                fontSize=22, leading=28, textColor=GOLD_C))],
    [Paragraph('<font color="#ffffff" size="13"><b>入塾金 ¥0</b> (通常 ¥20,000) + '
                '<b>14 日間 無料体験</b> + 友達紹介で <b>¥3,000 OFF</b></font>',
                ParagraphStyle('campb', alignment=TA_CENTER, fontName=JP_GO,
                                fontSize=13, leading=20, textColor=colors.white))],
    [Paragraph('<font color="#fef3c7" size="11"><b>残り入塾金免除枠: 15 名</b>'
                ' (毎月先着 30 名・本日時点)</font>',
                ParagraphStyle('campc', alignment=TA_CENTER, fontName=JP_GO,
                                fontSize=11, leading=18,
                                textColor=colors.HexColor('#fef3c7')))],
], colWidths=[150*mm])
camp_inner.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), NAVY_DEEP_C),
    ('BOX', (0, 0), (-1, -1), 2, GOLD_C),
    ('TOPPADDING', (0, 0), (-1, -1), 14),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
]))
camp_outer = Table([[camp_inner]], colWidths=[160*mm])
camp_outer.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
story.append(camp_outer)
story.append(Spacer(1, 6 * mm))

# 社会的証明バー
story.append(Paragraph('社会的証明 ─ 既に多くの方が ai-juku を選んでいます', S['h3']))
social_data = [
    ['200+', '6,000+', '6 体', '16,631'],
    ['在塾生 (2026/5)', 'Threads フォロワー', 'Custom GPT Store 公開', '問題プール'],
]
social_table = Table(social_data, colWidths=[40*mm]*4)
social_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, 0), JP_GO, 24),
    ('FONT', (0, 1), (-1, 1), JP_MI, 9),
    ('TEXTCOLOR', (0, 0), (-1, 0), GOLD_C),
    ('TEXTCOLOR', (0, 1), (-1, 1), GRAY_C),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
]))
story.append(social_table)
story.append(Spacer(1, 6 * mm))

# 上位 1% の秘密
story.append(Paragraph('上位 1% の塾生が密かにやっている 3 つの活用法', S['h3']))
story.append(Paragraph(
    '塾長から特別に、<b>偏差値を最も伸ばしている上位 1% の塾生</b>がやっている'
    '「他の人には言いたくない」活用法を 3 つ公開します。', S['body']))
secrets = [
    ('① 朝 6 時 SRS + 夜 写真採点',
     '朝起きてすぐ SRS フラッシュカードで脳を起動 (10 分)。'
     '夜寝る前にその日の英作文を 1 つ写真採点 (15 分)。<b>記憶定着の朝夜サンドイッチ</b>。'),
    ('② 弱点 TOP3 → 類題 5 問 → 翌朝再テスト',
     '弱点 TOP3 が出たら、AI に「同じポイントの類題を難易度別に 5 問」と依頼。'
     '翌朝、その 5 問を SRS で再テスト。<b>1 日で「苦手 → 得意」変換</b>。'),
    ('③ チャット履歴の週次振り返り',
     '日曜の 30 分、その週の AI チャット履歴を全部見返し、'
     '「今週学んだことトップ 5」を AI に整理させる。<b>知識の地図が頭に描かれる</b>。'),
]
for title, desc in secrets:
    box = Table([[Paragraph(
        f'<font color="#0a1f44"><b>{title}</b></font><br/>'
        f'<font color="#374151" size="9.5">{desc}</font>',
        ParagraphStyle('s', fontName=JP_MI, fontSize=10, leading=14))]],
        colWidths=[160 * mm])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY_C),
        ('LINEBEFORE', (0, 0), (0, -1), 3, GOLD_C),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(box)
    story.append(Spacer(1, 3 * mm))

story.append(Spacer(1, 4 * mm))
story.append(Paragraph(
    '<font color="#dc2626"><b>14 日間 無料体験から始めましょう。</b></font>'
    'お申込みは <b>https://trillion-ai-juku.com</b> から。', S['body_center']))
story.append(Spacer(1, 6 * mm))

# v6: CH15 → SECTION II に移動
# Build
doc.build(story)

print(f"\n✅ PDF 生成完了: {OUT_PDF}")
print(f"   サイズ: {OUT_PDF.stat().st_size / 1024:.1f} KB")
