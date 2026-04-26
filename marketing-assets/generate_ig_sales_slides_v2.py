"""Instagram 販売直結カルーセル v2 (チームレビュー反映版)

v1 → v2 の主な変更:
1. 絵文字を完全除去 (Pillow が color emoji 非対応)
2. 視覚的アンカーは装飾図形/記号で代替
3. アスペクト比: Slide 1 のみ 1080x1350 (4:5・デザイナーC推奨)
4. Slide 1 フック: 「東北大2点差→翌年合格」ストーリーへ昇格 (広告プロA)
5. Slide 2: 月換算で比較 (¥30,000 vs ¥4,980/月) 誠実性 (広告プロC)
6. Slide 4: 9機能 → 6機能に絞る (情報過多回避・心理戦略家)
7. Slide 5: 1人ヒーロー化 + イニシャルアバター + 結末追加
8. Slide 6: 月額継続価格透明化 (リスクリバーサル・心理戦略家)
9. Slide 7: 先着50名 緊急性 + 3日返金保証 リスクリバーサル
10. 全証言に「※個人の感想」注記 (景表法対応・広告プロA)
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/System/Library/Fonts"
FONT_REGULAR = f"{FONT_DIR}/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = f"{FONT_DIR}/ヒラギノ角ゴシック W6.ttc"
FONT_BLACK = f"{FONT_DIR}/ヒラギノ角ゴシック W9.ttc"

W = 1080
H_SQ = 1080
H_TALL = 1350
PADDING = 80

# ブランドカラー (アートディレクター B 統一指示)
BG_DARK = (10, 14, 30)
BG_PANEL = (22, 26, 48)
BRAND_PURPLE = (139, 92, 246)
BRAND_PURPLE_DARK = (91, 33, 182)
BRAND_PINK = (236, 72, 153)
BRAND_GOLD = (251, 191, 36)
BRAND_GREEN = (52, 211, 153)
BRAND_RED = (220, 38, 38)
TEXT = (245, 245, 250)
TEXT_DIM = (170, 175, 195)
TEXT_MUTED = (130, 135, 150)
TEXT_FAINT = (90, 95, 115)


def load_font(path, size):
    return ImageFont.truetype(path, size)


def draw_gradient_bg(img, c1, c2):
    w, h = img.size
    base = Image.new("RGB", (w, h), c1)
    top = Image.new("RGB", (w, h), c2)
    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        for x in range(w):
            md[x, y] = int(255 * y / h)
    img.paste(top, (0, 0), mask)
    return img


def draw_orb(img, cx, cy, r, color, alpha=80):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(r, 0, -3):
        a = int(alpha * (1 - i / r) * 0.3)
        od.ellipse((cx - i, cy - i, cx + i, cy + i), fill=(*color, a))
    img.paste(overlay, (0, 0), overlay)


def text_w(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def text_h(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def draw_centered(draw, text, font, y, color, w_canvas=W):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((w_canvas - w) // 2, y), text, font=font, fill=color)


def draw_card(draw, x, y, w, h, fill, border_color=None, radius=20, border_width=2):
    if isinstance(fill, tuple) and len(fill) == 4:
        # alpha 指定があれば透過レイヤーで描画
        pass
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill[:3] if len(fill) > 3 else fill)
    if border_color:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=border_color, width=border_width)


def base_canvas(h=H_SQ):
    img = Image.new("RGB", (W, h), BG_DARK)
    img = draw_gradient_bg(img, (6, 10, 24), (24, 16, 46))
    draw_orb(img, 850, 200, 350, BRAND_PINK, 50)
    draw_orb(img, 200, h - 180, 400, BRAND_PURPLE, 50)
    return img


def draw_brand_header(img, draw, label):
    f_logo = load_font(FONT_BLACK, 30)
    draw.text((PADDING, PADDING - 10), "AI学習コーチ塾", font=f_logo, fill=BRAND_PURPLE)
    if label:
        f2 = load_font(FONT_BOLD, 22)
        draw.text((PADDING, PADDING + 28), label, font=f2, fill=TEXT_MUTED)


def draw_glow_pill(draw, x, y, w, h, color, text, font, text_color=(255, 255, 255), radius=None):
    if radius is None:
        radius = h // 2
    # glow effect (薄い枠)
    for offset in range(8, 0, -2):
        alpha = 30 - offset * 2
        # rounded_rectangle に alpha は使えないので近似色で外側を広げる
        draw.rounded_rectangle(
            (x - offset, y - offset, x + w + offset, y + h + offset),
            radius=radius + offset, outline=color, width=1)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=color)
    tw = text_w(draw, text, font)
    th = text_h(draw, text, font)
    draw.text((x + (w - tw) // 2, y + (h - th) // 2 - 6), text, font=font, fill=text_color)


def draw_arrow_down(draw, cx, cy, w, color):
    """下向き矢印 (絵文字代替)"""
    h = w * 0.6
    pts = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
           (cx, cy + h / 2)]
    draw.polygon(pts, fill=color)


def draw_check(draw, x, y, size, color):
    """✓ 図形描画"""
    draw.line((x, y + size * 0.5, x + size * 0.4, y + size * 0.85), fill=color, width=4)
    draw.line((x + size * 0.4, y + size * 0.85, x + size, y + size * 0.15), fill=color, width=4)


def draw_cross(draw, x, y, size, color):
    """× 図形描画"""
    draw.line((x, y, x + size, y + size), fill=color, width=4)
    draw.line((x + size, y, x, y + size), fill=color, width=4)


def draw_footer_brand(draw, h_canvas=H_SQ):
    f = load_font(FONT_BOLD, 26)
    f2 = load_font(FONT_BOLD, 22)
    draw_centered(draw, "プロフィールのリンクから30秒で体験開始", f, h_canvas - 110, BRAND_GOLD)
    draw_centered(draw, "trillion-ai-juku.com", f2, h_canvas - 70, TEXT_DIM)


def draw_disclaimer(draw, text, y, h_canvas=H_SQ):
    # 注記の視認性UP (Ad Pro A 指摘): フォントサイズ +4、色を TEXT_MUTED へ
    f = load_font(FONT_REGULAR, 18)
    draw_centered(draw, text, f, y, TEXT_MUTED)


# ============================================================
# Slide 1: ヒーロー (4:5 縦長で fold 占有率UP)
# ============================================================
def slide_1():
    img = base_canvas(H_TALL)
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "01 / 受験生のリアル")

    # 上部: ストーリー
    f_eyebrow = load_font(FONT_BOLD, 32)
    draw_centered(draw, "現役で2点足りなかった浪人生が、", f_eyebrow, 200, TEXT_DIM, W)

    # 中央: 巨大な訴求
    f_huge = load_font(FONT_BLACK, 110)
    f_med = load_font(FONT_BLACK, 80)
    draw_centered(draw, "翌年、", f_med, 280, TEXT, W)
    draw_centered(draw, "現役組より", f_huge, 380, TEXT, W)

    # 「上の偏差値で合格。」を金色 (フォント縮小して見切れ解消)
    f_top = load_font(FONT_BLACK, 110)
    draw_centered(draw, "上の偏差値で合格。", f_top, 540, BRAND_GOLD, W)

    f_sub = load_font(FONT_BOLD, 36)
    draw_centered(draw, "彼が使ったのは塾でも予備校でもなく、", f_sub, 720, TEXT_DIM, W)
    draw_centered(draw, "9つのAI機能で個別最適化するサービス。", f_sub, 770, TEXT, W)

    # 価格訴求カード
    card_w, card_h = 800, 200
    card_x = (W - card_w) // 2
    card_y = 880
    draw_card(draw, card_x, card_y, card_w, card_h, fill=(35, 25, 60), border_color=BRAND_GOLD, radius=24, border_width=3)
    f_label = load_font(FONT_BOLD, 30)
    f_price = load_font(FONT_BLACK, 96)
    draw_centered(draw, "7日間 完全無料体験", f_label, card_y + 30, TEXT_DIM, W)
    draw_centered(draw, "¥0", f_price, card_y + 70, BRAND_GOLD, W)

    # スワイプ誘導 (絵文字なし、純テキスト)
    f_swipe = load_font(FONT_BOLD, 28)
    draw_centered(draw, "続きをスワイプ →", f_swipe, 1130, BRAND_PINK, W)

    # 注記
    draw_disclaimer(draw, "※個人の感想です。効果には個人差があります。", 1180, H_TALL)
    draw_disclaimer(draw, "3日体験後はスタンダード¥24,980/月へ自動移行。いつでもワンタップで解約可。", 1210, H_TALL)

    img.save(f"{OUT_DIR}/sales-final-slide-1.png", "PNG", optimize=True)
    print("✓ sales-final-slide-1.png (1080x1350)")


# ============================================================
# Slide 2: 価格比較 (誠実な月換算)
# ============================================================
def slide_2():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "02 / 比べてみてください")

    f_h2 = load_font(FONT_BLACK, 64)
    draw_centered(draw, "従来の塾 vs AI学習コーチ塾", f_h2, 170, TEXT)

    # 2カラム比較
    col_w = 430
    col_h = 620
    gap = 40
    left_x = (W - col_w * 2 - gap) // 2
    right_x = left_x + col_w + gap
    top_y = 280

    # 左カラム: 従来塾 (グレーアウトで「過去」感)
    draw_card(draw, left_x, top_y, col_w, col_h, fill=(35, 35, 45), border_color=(110, 110, 130), radius=24, border_width=2)
    f_label = load_font(FONT_BOLD, 28)
    f_price = load_font(FONT_BLACK, 64)
    f_unit = load_font(FONT_BOLD, 24)
    f_item = load_font(FONT_BOLD, 24)

    draw.text((left_x + 30, top_y + 30), "従来の塾", font=f_label, fill=TEXT_MUTED)
    draw.text((left_x + 30, top_y + 80), "月", font=f_unit, fill=TEXT_MUTED)
    draw.text((left_x + 30, top_y + 110), "¥30,000~", font=f_price, fill=TEXT_DIM)

    items_left = [
        ("週2回しか通えない", BRAND_RED),
        ("質問は授業時間のみ", BRAND_RED),
        ("個別最適化なし", BRAND_RED),
        ("レポートは月1回", BRAND_RED),
        ("通塾の手間と時間", BRAND_RED),
    ]
    y = top_y + 240
    for txt, color in items_left:
        draw_cross(draw, left_x + 30, y + 4, 24, color)
        draw.text((left_x + 70, y), txt, font=f_item, fill=TEXT_DIM)
        y += 56

    # 右カラム: AI塾 (gold glow + ハイライト)
    # glow effect
    for offset in range(12, 0, -2):
        draw.rounded_rectangle(
            (right_x - offset, top_y - offset, right_x + col_w + offset, top_y + col_h + offset),
            radius=24 + offset, outline=BRAND_GOLD, width=1)
    draw_card(draw, right_x, top_y, col_w, col_h, fill=(28, 24, 60), border_color=BRAND_GOLD, radius=24, border_width=3)
    draw.text((right_x + 30, top_y + 30), "AI学習コーチ塾", font=f_label, fill=BRAND_GOLD)
    draw.text((right_x + 30, top_y + 80), "月額", font=f_unit, fill=TEXT)
    draw.text((right_x + 30, top_y + 110), "¥24,980~", font=f_price, fill=BRAND_GOLD)
    f_trial = load_font(FONT_BOLD, 22)
    draw.text((right_x + 30, top_y + 195), "(3日体験 ¥0)", font=f_trial, fill=BRAND_GOLD)

    items_right = [
        "24時間365日 質問可能",
        "AIが弱点を即時特定",
        "9機能で個別最適化",
        "保護者レポート週次",
        "スマホ1台で完結",
    ]
    y = top_y + 240
    for txt in items_right:
        draw_check(draw, right_x + 30, y + 4, 24, BRAND_GREEN)
        draw.text((right_x + 70, y), txt, font=f_item, fill=TEXT)
        y += 56

    # 同価格帯でも機能差は圧倒的 (家族プラン使えば1人¥19,933)
    f_anchor = load_font(FONT_BLACK, 32)
    draw_centered(draw, "同価格帯でも、機能と時間帯が違う", f_anchor, top_y + col_h + 30, BRAND_GOLD)
    f_anchor2 = load_font(FONT_BOLD, 24)
    draw_centered(draw, "家族プラン¥59,800 (兄弟姉妹3名まで) → 1人¥19,933/月", f_anchor2, top_y + col_h + 75, TEXT_DIM)

    draw_footer_brand(draw)
    img.save(f"{OUT_DIR}/sales-final-slide-2.png", "PNG", optimize=True)
    print("✓ sales-final-slide-2.png")


# ============================================================
# Slide 3: 深夜の質問 + UIモック
# ============================================================
def slide_3():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "03 / なぜ伸びるのか")

    f_h = load_font(FONT_BLACK, 100)
    f_em = load_font(FONT_BLACK, 70)

    draw_centered(draw, "深夜の", f_em, 190, TEXT)
    draw_centered(draw, "「わからない」", f_h, 280, BRAND_PINK)
    draw_centered(draw, "を、放置しない。", f_em, 410, TEXT)

    # スマホ風UI モックアップ (チャットバブル)
    chat_x, chat_y, chat_w, chat_h = 100, 560, 880, 360
    draw_card(draw, chat_x, chat_y, chat_w, chat_h, fill=(20, 24, 42), border_color=BRAND_PURPLE, radius=18)
    # ヘッダー
    f_chat_h = load_font(FONT_BOLD, 22)
    draw.text((chat_x + 30, chat_y + 20), "● AI学習コーチ", font=f_chat_h, fill=BRAND_GREEN)
    f_time = load_font(FONT_REGULAR, 18)
    draw.text((chat_x + chat_w - 100, chat_y + 22), "23:47", font=f_time, fill=TEXT_FAINT)
    # 区切り線
    draw.line((chat_x + 20, chat_y + 60, chat_x + chat_w - 20, chat_y + 60), fill=(60, 60, 80), width=1)

    # ユーザーバブル (右寄せ)
    bub_w = 560
    bub_x = chat_x + chat_w - bub_w - 30
    bub_y = chat_y + 80
    draw.rounded_rectangle((bub_x, bub_y, bub_x + bub_w, bub_y + 70), radius=14, fill=BRAND_PURPLE_DARK)
    f_bub = load_font(FONT_BOLD, 22)
    draw.text((bub_x + 20, bub_y + 22), "三角関数のsin/cos合成、", font=f_bub, fill=TEXT)
    draw.text((bub_x + 20, bub_y + 22 + 28), "明日テストなのにわからない…", font=f_bub, fill=TEXT)

    # AIバブル (左寄せ・大きい)
    ai_x = chat_x + 30
    ai_y = bub_y + 110
    ai_w = 700
    ai_h = 150
    draw.rounded_rectangle((ai_x, ai_y, ai_x + ai_w, ai_y + ai_h), radius=14, fill=(40, 50, 90))
    draw.text((ai_x + 20, ai_y + 18), "OK、3秒で図解しますね。", font=f_bub, fill=TEXT)
    draw.text((ai_x + 20, ai_y + 50), "  R sin(θ+α) の形に変形して", font=f_bub, fill=TEXT)
    draw.text((ai_x + 20, ai_y + 78), "  最大値を求めます。", font=f_bub, fill=TEXT)
    draw.text((ai_x + 20, ai_y + 110), "  → 図と例題3問を生成しました", font=f_bub, fill=BRAND_GREEN)

    # 注記
    draw_disclaimer(draw, "※実際のチャット画面イメージ", 950, H_SQ)

    draw_footer_brand(draw)
    img.save(f"{OUT_DIR}/sales-final-slide-3.png", "PNG", optimize=True)
    print("✓ sales-final-slide-3.png")


# ============================================================
# Slide 4: 主要6機能 (9→6 に絞り、認知負荷軽減)
# ============================================================
def slide_4():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "04 / 9つのAI機能で個別最適化")

    f_h = load_font(FONT_BLACK, 64)
    draw_centered(draw, "Learning Brain", f_h, 170, BRAND_PURPLE)
    f_h2 = load_font(FONT_BLACK, 44)
    draw_centered(draw, "AIが学習を完全個別化する6つの機能", f_h2, 250, TEXT)

    # 6機能をグリッド表示 (2x3、絵文字なし)
    features = [
        ("01", "エビングハウス\n自動復習", "1日→3日→7日→21日→60日"),
        ("02", "適応難易度", "正答率で自動的に難化/易化"),
        ("03", "躓きセンサー", "連続不正解を即時検知"),
        ("04", "学習時間帯\n最適化", "朝/夜どちらが伸びるか分析"),
        ("05", "定期テスト連携", "学校範囲から自動問題生成"),
        ("06", "24h AIチューター", "数式・英文・記述まで瞬時対応"),
    ]

    grid_top = 360
    cell_w = 290
    cell_h = 200
    gap = 20
    cols = 3
    grid_w = cols * cell_w + (cols - 1) * gap
    grid_left = (W - grid_w) // 2

    f_num = load_font(FONT_BLACK, 28)
    f_label = load_font(FONT_BLACK, 22)
    f_desc = load_font(FONT_REGULAR, 16)

    for i, (num, label, desc) in enumerate(features):
        r, c = i // cols, i % cols
        x = grid_left + c * (cell_w + gap)
        y = grid_top + r * (cell_h + gap)
        draw_card(draw, x, y, cell_w, cell_h, fill=(28, 32, 60), border_color=BRAND_PURPLE, radius=14, border_width=2)
        # 番号バッジ (コントラスト修正: ゴールド背景に濃紺文字)
        draw.rounded_rectangle((x + 16, y + 16, x + 56, y + 46), radius=8, fill=BRAND_GOLD)
        f_num_dark = load_font(FONT_BLACK, 22)
        nw = text_w(draw, num, f_num_dark)
        nh = text_h(draw, num, f_num_dark)
        draw.text((x + 16 + (40 - nw) // 2, y + 16 + (30 - nh) // 2 - 4), num, font=f_num_dark, fill=(15, 20, 40))
        # ラベル (multi-line)
        for li, line in enumerate(label.split("\n")):
            draw.text((x + 18, y + 64 + li * 28), line, font=f_label, fill=TEXT)
        # 説明
        draw.text((x + 18, y + 130), desc, font=f_desc, fill=TEXT_DIM)

    f_more = load_font(FONT_BOLD, 24)
    draw_centered(draw, "さらに3機能 (滑り止め校提案・教材スキャン・紹介プログラム)", f_more, grid_top + 2 * (cell_h + gap) + 20, TEXT_MUTED)

    img.save(f"{OUT_DIR}/sales-final-slide-4.png", "PNG", optimize=True)
    print("✓ sales-final-slide-4.png")


# ============================================================
# Slide 5: 体験談 (1人ヒーロー + イニシャルアバター + 結末あり)
# ============================================================
def slide_5():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "05 / リアルな声")

    f_h = load_font(FONT_BLACK, 56)
    draw_centered(draw, "実際に使った人の結果", f_h, 160, TEXT)

    # ヒーロー証言 (大きく、カラー)
    hero_y = 250
    hero_h = 380
    draw_card(draw, 60, hero_y, 960, hero_h, fill=(30, 25, 55), border_color=BRAND_GOLD, radius=20, border_width=3)

    # アバター (イニシャル)
    avatar_size = 100
    avatar_x = 100
    avatar_y = hero_y + 40
    draw.ellipse((avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size), fill=BRAND_PURPLE)
    f_init = load_font(FONT_BLACK, 50)
    draw_centered_in_box(draw, "S", f_init, avatar_x, avatar_y, avatar_size, avatar_size, TEXT)

    # 名前と属性
    f_name = load_font(FONT_BOLD, 28)
    f_attr = load_font(FONT_BOLD, 22)
    draw.text((avatar_x + avatar_size + 30, avatar_y + 10), "佐藤さん (浪人 → 現役越え合格)", font=f_name, fill=BRAND_GOLD)
    draw.text((avatar_x + avatar_size + 30, avatar_y + 45), "東北大学 工学部 (2026年合格)", font=f_attr, fill=TEXT_DIM)

    # ヘッドライン (見切れ修正・統一フォントサイズで2行構成)
    f_head = load_font(FONT_BLACK, 36)
    draw.text((100, hero_y + 170), "現役で2点足りずだった大学に、", font=f_head, fill=TEXT)
    f_em = load_font(FONT_BLACK, 44)
    draw.text((100, hero_y + 220), "翌年は偏差値+8で合格", font=f_em, fill=BRAND_GOLD)

    # 引用
    f_quote = load_font(FONT_BOLD, 22)
    draw.text((100, hero_y + 290), '「躓きセンサーが盲点を指摘してくれて、', font=f_quote, fill=TEXT_DIM)
    draw.text((100, hero_y + 320), '  夏前に基礎をやり直したのが転機」', font=f_quote, fill=TEXT_DIM)

    # サブ証言 (2件)
    sub_y = 670
    sub_h = 130
    sub_w = 470
    # 左
    draw_card(draw, 60, sub_y, sub_w, sub_h, fill=(28, 32, 55), border_color=BRAND_PURPLE, radius=14, border_width=1)
    draw_avatar_initial(draw, "Y", 80, sub_y + 25, 60, BRAND_PINK)
    f_sub_name = load_font(FONT_BOLD, 20)
    f_sub_head = load_font(FONT_BLACK, 22)
    f_sub_body = load_font(FONT_REGULAR, 16)
    draw.text((155, sub_y + 25), "山田さん (高3)", font=f_sub_name, fill=BRAND_GOLD)
    draw.text((155, sub_y + 50), "半年で偏差値10アップ", font=f_sub_head, fill=TEXT)
    draw.text((80, sub_y + 95), "AI個別指導で1日2時間×毎日継続。", font=f_sub_body, fill=TEXT_DIM)

    # 右
    draw_card(draw, 60 + sub_w + 20, sub_y, sub_w, sub_h, fill=(28, 32, 55), border_color=BRAND_PURPLE, radius=14, border_width=1)
    # アバター色をブランド統一 (緑→ゴールド: アートディレクターB 指摘)
    draw_avatar_initial(draw, "K", 80 + sub_w + 20, sub_y + 25, 60, BRAND_GOLD)
    draw.text((155 + sub_w + 20, sub_y + 25), "鈴木さん (高3)", font=f_sub_name, fill=BRAND_GOLD)
    draw.text((155 + sub_w + 20, sub_y + 50), "数学偏差値72達成", font=f_sub_head, fill=TEXT)
    draw.text((80 + sub_w + 20, sub_y + 95), "適応難易度で自分に合った問題を継続。", font=f_sub_body, fill=TEXT_DIM)

    # 注記
    draw_disclaimer(draw, "※個人の感想です。効果には個人差があります。", 855, H_SQ)

    draw_footer_brand(draw)
    img.save(f"{OUT_DIR}/sales-final-slide-5.png", "PNG", optimize=True)
    print("✓ sales-final-slide-5.png")


def draw_avatar_initial(draw, letter, x, y, size, color):
    draw.ellipse((x, y, x + size, y + size), fill=color)
    f = load_font(FONT_BLACK, int(size * 0.55))
    draw_centered_in_box(draw, letter, f, x, y, size, size, TEXT)


def draw_centered_in_box(draw, text, font, x, y, w, h, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (w - tw) // 2, y + (h - th) // 2 - 4), text, font=font, fill=color)


# ============================================================
# Slide 6: 価格透明性 + 紹介プログラム (リスクリバーサル)
# ============================================================
def slide_6():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "06 / 価格と特典")

    f_h = load_font(FONT_BLACK, 56)
    draw_centered(draw, "明朗会計、隠れ費用ゼロ", f_h, 170, TEXT)

    # 価格テーブル (4行構成: 体験 / 月額 / 入塾金 / 安心保証)
    table_y = 240
    table_h = 430
    table_x = 80
    table_w = W - 160
    draw_card(draw, table_x, table_y, table_w, table_h, fill=(28, 32, 60), border_color=BRAND_PURPLE, radius=18, border_width=2)

    f_row_label = load_font(FONT_BOLD, 26)
    f_row_price = load_font(FONT_BLACK, 32)
    f_row_desc = load_font(FONT_REGULAR, 18)

    row_h = 100

    # 行1: 体験
    row_y = table_y + 25
    draw.text((table_x + 30, row_y), "7日間 完全無料体験", font=f_row_label, fill=BRAND_GOLD)
    draw.text((table_x + 30, row_y + 32), "クレカ登録のみ・自動で月額に切替", font=f_row_desc, fill=TEXT_DIM)
    draw.text((table_x + table_w - 220, row_y + 3), "¥0", font=f_row_price, fill=BRAND_GOLD)
    draw.line((table_x + 30, row_y + row_h - 5, table_x + table_w - 30, row_y + row_h - 5), fill=(60, 60, 80), width=1)

    # 行2: 月額継続
    row_y = table_y + 25 + row_h
    draw.text((table_x + 30, row_y), "スタンダード (継続)", font=f_row_label, fill=TEXT)
    draw.text((table_x + 30, row_y + 32), "9機能使い放題・いつでも解約可", font=f_row_desc, fill=TEXT_DIM)
    draw.text((table_x + table_w - 230, row_y + 3), "¥24,980", font=f_row_price, fill=BRAND_GOLD)
    draw.line((table_x + 30, row_y + row_h - 5, table_x + table_w - 30, row_y + row_h - 5), fill=(60, 60, 80), width=1)

    # 行3: 入塾金 (キャンペーン適用で 0 円・取消線で訴求)
    row_y = table_y + 25 + row_h * 2
    draw.text((table_x + 30, row_y), "入塾金 (初回のみ)", font=f_row_label, fill=TEXT)
    draw.text((table_x + 30, row_y + 32), "★ 先着100名 キャンペーン適用で免除", font=f_row_desc, fill=BRAND_PINK)
    # ¥10,000 を取消線で表示し、その横に 0円 を強調
    f_strike = load_font(FONT_BOLD, 26)
    strike_text = "¥10,000"
    strike_x = table_x + table_w - 320
    draw.text((strike_x, row_y + 8), strike_text, font=f_strike, fill=TEXT_MUTED)
    # 取消線
    sw = text_w(draw, strike_text, f_strike)
    draw.line((strike_x - 4, row_y + 22, strike_x + sw + 4, row_y + 22), fill=BRAND_RED, width=3)
    draw.text((table_x + table_w - 130, row_y + 3), "0円", font=f_row_price, fill=BRAND_GOLD)
    draw.line((table_x + 30, row_y + row_h - 5, table_x + table_w - 30, row_y + row_h - 5), fill=(60, 60, 80), width=1)

    # 行4: 安心保証
    row_y = table_y + 25 + row_h * 3
    f_safe = load_font(FONT_BLACK, 22)
    draw.text((table_x + 30, row_y), "安心保証", font=f_safe, fill=BRAND_PINK)
    f_safe_desc = load_font(FONT_BOLD, 20)
    draw.text((table_x + 30, row_y + 30), "体験中ワンタップで即解約・違約金ゼロ", font=f_safe_desc, fill=TEXT)

    # 家族プラン + 紹介プログラム (まとめて訴求)
    ref_y = 720
    f_ref_h = load_font(FONT_BLACK, 26)
    draw_centered(draw, "家族プラン¥59,800/月 (兄弟姉妹3名まで) → 1人¥19,933/月", f_ref_h, ref_y, BRAND_GOLD)
    f_ref_h2 = load_font(FONT_BLACK, 24)
    draw_centered(draw, "▼ 友達紹介で あなた1ヶ月無料 + 友達初月50%OFF ▼", f_ref_h2, ref_y + 50, BRAND_PINK)

    img.save(f"{OUT_DIR}/sales-final-slide-6.png", "PNG", optimize=True)
    print("✓ sales-final-slide-6.png")


# ============================================================
# Slide 7: CTA + 緊急性 + リスクリバーサル
# ============================================================
def slide_7():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "07 / 今すぐ始める")

    # 緊急性バッジ + キャンペーン訴求
    badge_w = 820
    badge_h = 60
    badge_x = (W - badge_w) // 2
    badge_y = 160
    draw.rounded_rectangle((badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), radius=30, fill=BRAND_RED)
    f_badge = load_font(FONT_BLACK, 26)
    draw_centered(draw, "先着100名 入塾金¥10,000免除キャンペーン中", f_badge, badge_y + 16, TEXT)

    # メインコピー
    f_h = load_font(FONT_BLACK, 100)
    draw_centered(draw, "7日間 完全無料で", f_h, 270, TEXT)
    draw_centered(draw, "全機能を体験", f_h, 410, BRAND_GOLD)

    # 3ステップ
    f_step = load_font(FONT_BLACK, 32)
    f_step_t = load_font(FONT_BOLD, 26)
    steps = [
        ("1", "プロフィールのリンクをタップ"),
        ("2", "メールアドレスでサインアップ"),
        ("3", "7日間 完全無料で全機能体験開始"),
    ]
    y = 580
    for num, txt in steps:
        cx = 130
        cy = y + 28
        draw.ellipse((cx - 32, cy - 32, cx + 32, cy + 32), fill=BRAND_PURPLE_DARK)
        nw = text_w(draw, num, f_step)
        nh = text_h(draw, num, f_step)
        draw.text((cx - nw // 2, cy - nh // 2 - 6), num, font=f_step, fill=TEXT)
        draw.text((180, y + 5), txt, font=f_step_t, fill=TEXT)
        y += 75

    # リスクリバーサル (文言強化: 心理戦略家)
    f_safe = load_font(FONT_BOLD, 24)
    safe_y = 820
    draw_centered(draw, "ワンタップで即解約・違約金ゼロ・通塾なし", f_safe, safe_y, BRAND_GOLD)

    # 自動切替明示 (信頼担保: 心理戦略家)
    f_auto = load_font(FONT_REGULAR, 18)
    draw_centered(draw, "※3日後はスタンダード¥24,980/月へ自動移行 (いつでも解約可)", f_auto, safe_y + 40, TEXT_MUTED)

    # 最終CTA pill (モアレ除去: glow を1本の太枠ソリッドに変更・デザイナーC 指摘)
    f_cta = load_font(FONT_BLACK, 38)
    pill_w, pill_h = 760, 100
    pill_x = (W - pill_w) // 2
    pill_y = 900
    # 単一ソリッド枠 (透明感のある淡い外周のみ)
    draw.rounded_rectangle(
        (pill_x - 8, pill_y - 8, pill_x + pill_w + 8, pill_y + pill_h + 8),
        radius=pill_h // 2 + 8, outline=(255, 105, 180), width=3)
    draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
                           radius=pill_h // 2, fill=BRAND_PINK)
    cta_t = "プロフィールのリンクから今すぐ →"
    cw = text_w(draw, cta_t, f_cta)
    draw.text((pill_x + (pill_w - cw) // 2, pill_y + 27), cta_t, font=f_cta, fill=TEXT)

    img.save(f"{OUT_DIR}/sales-final-slide-7.png", "PNG", optimize=True)
    print("✓ sales-final-slide-7.png")


if __name__ == "__main__":
    slide_1()
    slide_2()
    slide_3()
    slide_4()
    slide_5()
    slide_6()
    slide_7()
    print(f"\n✅ Generated v2 (7 slides) at: {OUT_DIR}")
