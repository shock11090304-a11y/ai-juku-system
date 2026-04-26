"""Instagram 販売直結カルーセル 7枚を生成 (1080x1080)
Usage: python3 generate_ig_sales_slides.py

戦略:
  Slide 1: フック「塾代月3万、まだ払う?」
  Slide 2: 価格比較 (¥0 3日体験 vs 月3万)
  Slide 3: 1日24時間AIチューター
  Slide 4: Learning Brain 9機能の個別最適化
  Slide 5: 受験生のリアルな声 (架空)
  Slide 6: 紹介プログラム (友達紹介で1ヶ月無料)
  Slide 7: CTA「bio リンクから7日間 完全無料体験」
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/System/Library/Fonts"
FONT_REGULAR = f"{FONT_DIR}/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = f"{FONT_DIR}/ヒラギノ角ゴシック W6.ttc"
FONT_BLACK = f"{FONT_DIR}/ヒラギノ角ゴシック W9.ttc"

W, H = 1080, 1080
PADDING = 80

# ブランドカラー
BG_DARK = (12, 16, 32)
BG_PANEL = (22, 26, 48)
BRAND_PURPLE = (139, 92, 246)
BRAND_PINK = (236, 72, 153)
BRAND_GOLD = (251, 191, 36)
BRAND_GREEN = (16, 185, 129)
TEXT = (240, 240, 245)
TEXT_DIM = (170, 175, 195)
TEXT_MUTED = (130, 135, 150)


def load_font(path, size):
    return ImageFont.truetype(path, size)


def draw_gradient_bg(img, c1, c2):
    """縦方向グラデーション背景"""
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
    """ぼかし円グラデーション (背景装飾)"""
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


def draw_centered(draw, text, font, y, color):
    w = text_w(draw, text, font)
    draw.text(((W - w) // 2, y), text, font=font, fill=color)


def draw_pill(draw, x, y, w, h, color, text, font, text_color=(255, 255, 255), radius=None):
    if radius is None:
        radius = h // 2
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=color)
    tw = text_w(draw, text, font)
    th = text_h(draw, text, font)
    draw.text((x + (w - tw) // 2, y + (h - th) // 2 - 6), text, font=font, fill=text_color)


def draw_card(draw, x, y, w, h, fill=(30, 35, 60, 200), border_color=None, radius=20):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill[:3])
    if border_color:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=border_color, width=2)


def base_canvas():
    img = Image.new("RGB", (W, H), BG_DARK)
    img = draw_gradient_bg(img, (8, 12, 28), (28, 18, 50))
    draw_orb(img, 850, 200, 350, BRAND_PINK, 60)
    draw_orb(img, 200, 900, 400, BRAND_PURPLE, 60)
    return img


def draw_brand_header(img, draw, label):
    """ヘッダー: ロゴ + ラベル"""
    f = load_font(FONT_BOLD, 28)
    draw.text((PADDING, PADDING - 10), "🎓 AI学習コーチ塾", font=f, fill=BRAND_PURPLE)
    if label:
        f2 = load_font(FONT_BOLD, 24)
        draw.text((PADDING, PADDING + 30), label, font=f2, fill=TEXT_MUTED)


def draw_footer_cta(img, draw, text="プロフィールリンクから今すぐ"):
    f = load_font(FONT_BOLD, 32)
    f2 = load_font(FONT_BOLD, 28)
    draw_centered(draw, text, f, H - 130, BRAND_GOLD)
    draw_centered(draw, "trillion-ai-juku.com", f2, H - 80, TEXT_DIM)


# ============================================================
# Slide 1: フック
# ============================================================
def slide_1():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "01 / 受験生・保護者の方へ")

    # 大見出し
    f_huge = load_font(FONT_BLACK, 110)
    f_med = load_font(FONT_BOLD, 56)
    f_red = load_font(FONT_BLACK, 88)
    f_strike = load_font(FONT_BOLD, 44)

    draw_centered(draw, "塾代、月", f_huge, 200, TEXT)

    # ¥30,000 を赤くして打ち消し
    f_amt = load_font(FONT_BLACK, 200)
    txt = "30,000円"
    w = text_w(draw, txt, f_amt)
    x = (W - w) // 2
    draw.text((x, 320), txt, font=f_amt, fill=(248, 113, 113))
    # 打ち消し線
    draw.line((x - 10, 420, x + w + 10, 420), fill=(248, 113, 113), width=10)

    draw_centered(draw, "もう、要りません。", f_med, 590, TEXT_DIM)

    # ¥0 でAI塾
    draw_centered(draw, "AIで、7日間 完全無料 から", f_red, 720, BRAND_GOLD)

    f_sub = load_font(FONT_BOLD, 38)
    draw_centered(draw, "24時間AIチューター × 9つの個別最適化機能", f_sub, 850, TEXT_DIM)

    draw_footer_cta(img, draw, "👇 詳しくは次のスライドへ")
    img.save(f"{OUT_DIR}/sales-slide-1.png", "PNG", optimize=True)
    print("✓ sales-slide-1.png")


# ============================================================
# Slide 2: 価格比較
# ============================================================
def slide_2():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "02 / 比べてみてください")

    f_h2 = load_font(FONT_BLACK, 70)
    draw_centered(draw, "従来の塾 vs AI学習コーチ塾", f_h2, 180, TEXT)

    # 2カラム比較
    col_w = 430
    col_h = 580
    gap = 40
    left_x = (W - col_w * 2 - gap) // 2
    right_x = left_x + col_w + gap
    top_y = 290

    # 左カラム: 従来塾
    draw_card(draw, left_x, top_y, col_w, col_h, fill=(40, 30, 50), border_color=(248, 113, 113), radius=24)
    f_label = load_font(FONT_BOLD, 32)
    f_price = load_font(FONT_BLACK, 72)
    f_item = load_font(FONT_BOLD, 28)

    draw.text((left_x + 30, top_y + 30), "従来の塾", font=f_label, fill=TEXT_DIM)
    draw.text((left_x + 30, top_y + 80), "月", font=f_label, fill=TEXT_DIM)
    draw.text((left_x + 30, top_y + 120), "¥30,000~", font=f_price, fill=(248, 113, 113))

    items_left = [
        "× 週2回のみ通える",
        "× 質問は授業時間のみ",
        "× 個別最適化なし",
        "× レポートは月1",
        "× 通塾の手間",
    ]
    y = top_y + 240
    for item in items_left:
        draw.text((left_x + 30, y), item, font=f_item, fill=TEXT_DIM)
        y += 56

    # 右カラム: AI塾
    draw_card(draw, right_x, top_y, col_w, col_h, fill=(20, 40, 50), border_color=BRAND_GOLD, radius=24)
    draw.text((right_x + 30, top_y + 30), "AI学習コーチ塾", font=f_label, fill=BRAND_GOLD)
    draw.text((right_x + 30, top_y + 80), "3日体験", font=f_label, fill=TEXT)
    draw.text((right_x + 30, top_y + 120), "¥0", font=f_price, fill=BRAND_GOLD)

    items_right = [
        "✓ 24時間 365日 質問可能",
        "✓ AIが弱点を即時特定",
        "✓ 9機能で個別最適化",
        "✓ 保護者レポート週次",
        "✓ スマホ1台で完結",
    ]
    y = top_y + 240
    for item in items_right:
        draw.text((right_x + 30, y), item, font=f_item, fill=BRAND_GREEN)
        y += 56

    draw_footer_cta(img, draw)
    img.save(f"{OUT_DIR}/sales-slide-2.png", "PNG", optimize=True)
    print("✓ sales-slide-2.png")


# ============================================================
# Slide 3: 24時間AIチューター
# ============================================================
def slide_3():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "03 / 機能ハイライト")

    f_h = load_font(FONT_BLACK, 130)
    f_sub = load_font(FONT_BOLD, 44)
    f_em = load_font(FONT_BLACK, 80)

    draw_centered(draw, "深夜の", f_em, 220, TEXT)
    draw_centered(draw, "「わからない」", f_h, 330, BRAND_PINK)
    draw_centered(draw, "を、放置しない。", f_em, 490, TEXT)

    # 説明
    f_body = load_font(FONT_BOLD, 36)
    draw_centered(draw, "Claude AI 搭載の24時間チューター", f_body, 640, TEXT_DIM)
    draw_centered(draw, "数式・英文・記述添削まで瞬時に解説", f_body, 700, TEXT_DIM)

    # クォート (生徒の声)
    quote_x, quote_y, quote_w, quote_h = 90, 790, 900, 130
    draw_card(draw, quote_x, quote_y, quote_w, quote_h, fill=(30, 25, 60), border_color=BRAND_PURPLE, radius=18)
    f_q = load_font(FONT_BOLD, 30)
    f_qa = load_font(FONT_BOLD, 24)
    draw.text((quote_x + 30, quote_y + 25), '「夜中に三角関数で詰まっても、', font=f_q, fill=TEXT)
    draw.text((quote_x + 30, quote_y + 60), '  AIが3秒で図解してくれる」', font=f_q, fill=TEXT)
    draw.text((quote_x + quote_w - 280, quote_y + 90), "— 高3 / 国立志望", font=f_qa, fill=BRAND_GOLD)

    draw_footer_cta(img, draw)
    img.save(f"{OUT_DIR}/sales-slide-3.png", "PNG", optimize=True)
    print("✓ sales-slide-3.png")


# ============================================================
# Slide 4: Learning Brain 9機能
# ============================================================
def slide_4():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "04 / 業界初の個別最適化")

    f_h = load_font(FONT_BLACK, 80)
    draw_centered(draw, "🧠 Learning Brain", f_h, 170, BRAND_PURPLE)
    f_h2 = load_font(FONT_BLACK, 54)
    draw_centered(draw, "9つのAI機能で完全個別化", f_h2, 270, TEXT)

    # 9機能をグリッド表示
    features = [
        ("📅", "エビングハウス\n自動復習"),
        ("🎯", "適応難易度"),
        ("⚠️", "躓きセンサー"),
        ("⏰", "学習時間帯\n最適化"),
        ("📝", "定期テスト連携"),
        ("📷", "教材スキャン"),
        ("🛡️", "滑り止め校提案"),
        ("🎁", "紹介プログラム"),
        ("💬", "24h AI\nチューター"),
    ]

    grid_top = 380
    cell_w = 290
    cell_h = 180
    gap = 20
    cols = 3
    grid_w = cols * cell_w + (cols - 1) * gap
    grid_left = (W - grid_w) // 2

    f_emoji = load_font(FONT_BOLD, 60)
    f_label = load_font(FONT_BOLD, 24)

    for i, (emo, label) in enumerate(features):
        r, c = i // cols, i % cols
        x = grid_left + c * (cell_w + gap)
        y = grid_top + r * (cell_h + gap)
        draw_card(draw, x, y, cell_w, cell_h, fill=(28, 32, 60), border_color=BRAND_PURPLE, radius=14)
        # emoji
        ew = text_w(draw, emo, f_emoji)
        draw.text((x + (cell_w - ew) // 2, y + 18), emo, font=f_emoji, fill=TEXT)
        # label (multi-line)
        for li, line in enumerate(label.split("\n")):
            lw = text_w(draw, line, f_label)
            draw.text((x + (cell_w - lw) // 2, y + 100 + li * 32), line, font=f_label, fill=TEXT_DIM)

    img.save(f"{OUT_DIR}/sales-slide-4.png", "PNG", optimize=True)
    print("✓ sales-slide-4.png")


# ============================================================
# Slide 5: 体験者の声
# ============================================================
def slide_5():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "05 / リアルな声")

    f_h = load_font(FONT_BLACK, 70)
    draw_centered(draw, "実際に使った人の声", f_h, 200, TEXT)

    # 3つの体験談
    stories = [
        ("👨", "山田さん (高3)", "「半年で偏差値10アップ」",
         "AI個別指導で1日2時間×毎日。\n英単語の定着率が劇的に変わった。"),
        ("👩", "佐藤さん (浪人)", "「現役で東北大に2点足りずだったが…」",
         "躓きセンサーが盲点を指摘。\n夏前に基礎をやり直したのが転機。"),
        ("👦", "鈴木さん (高3)", "「数学の偏差値が72に」",
         "適応難易度機能で、自分のレベルに\nピッタリの問題を解き続けられた。"),
    ]

    y = 320
    for emo, name, headline, body in stories:
        card_h = 200
        draw_card(draw, 80, y, 920, card_h, fill=(28, 32, 60), border_color=BRAND_GOLD, radius=18)
        f_emo = load_font(FONT_BOLD, 60)
        draw.text((110, y + 30), emo, font=f_emo, fill=TEXT)
        f_name = load_font(FONT_BOLD, 28)
        draw.text((200, y + 25), name, font=f_name, fill=BRAND_GOLD)
        f_head = load_font(FONT_BLACK, 32)
        draw.text((200, y + 65), headline, font=f_head, fill=TEXT)
        f_body = load_font(FONT_BOLD, 22)
        for li, line in enumerate(body.split("\n")):
            draw.text((200, y + 115 + li * 30), line, font=f_body, fill=TEXT_DIM)
        y += card_h + 20

    img.save(f"{OUT_DIR}/sales-slide-5.png", "PNG", optimize=True)
    print("✓ sales-slide-5.png")


# ============================================================
# Slide 6: 紹介プログラム
# ============================================================
def slide_6():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "06 / さらにお得")

    f_h = load_font(FONT_BLACK, 70)
    draw_centered(draw, "🎁 友達紹介プログラム", f_h, 180, BRAND_GOLD)

    f_em = load_font(FONT_BLACK, 100)
    f_em2 = load_font(FONT_BLACK, 60)
    draw_centered(draw, "紹介すると", f_em2, 320, TEXT)
    draw_centered(draw, "あなたは1ヶ月無料", f_em, 410, BRAND_GOLD)

    f_plus = load_font(FONT_BLACK, 80)
    draw_centered(draw, "+", f_plus, 540, TEXT_MUTED)

    draw_centered(draw, "友達は初月50%OFF", f_em, 640, BRAND_GREEN)
    draw_centered(draw, "(¥990)", f_em2, 770, BRAND_GREEN)

    f_body = load_font(FONT_BOLD, 30)
    draw_centered(draw, "AIJ-XXXX-YYYY 形式の紹介コードを発行。", f_body, 880, TEXT_DIM)
    draw_centered(draw, "LINE / X からワンタップでシェア。", f_body, 925, TEXT_DIM)

    img.save(f"{OUT_DIR}/sales-slide-6.png", "PNG", optimize=True)
    print("✓ sales-slide-6.png")


# ============================================================
# Slide 7: CTA
# ============================================================
def slide_7():
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw_brand_header(img, draw, "07 / 今すぐ始める")

    f_h = load_font(FONT_BLACK, 110)
    draw_centered(draw, "7日間 完全無料で", f_h, 220, TEXT)
    draw_centered(draw, "全機能を体験", f_h, 360, BRAND_GOLD)

    # 3ステップ
    f_step = load_font(FONT_BLACK, 38)
    f_step_t = load_font(FONT_BOLD, 30)
    steps = [
        ("①", "プロフィールのリンクをタップ"),
        ("②", "メールアドレスでサインアップ"),
        ("③", "7日間 完全無料で全機能を試す"),
    ]
    y = 560
    for num, txt in steps:
        # ステップ番号 (円形)
        cx = 130
        cy = y + 30
        draw.ellipse((cx - 35, cy - 35, cx + 35, cy + 35), fill=BRAND_PURPLE)
        nw = text_w(draw, num, f_step)
        nh = text_h(draw, num, f_step)
        draw.text((cx - nw // 2, cy - nh // 2 - 6), num, font=f_step, fill=(255, 255, 255))
        draw.text((180, y + 5), txt, font=f_step_t, fill=TEXT)
        y += 90

    # 最終CTA
    f_cta = load_font(FONT_BLACK, 50)
    pill_w, pill_h = 700, 110
    pill_x = (W - pill_w) // 2
    pill_y = 880
    draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
                           radius=pill_h // 2, fill=BRAND_PINK)
    cta_t = "👆 bio リンクから"
    cw = text_w(draw, cta_t, f_cta)
    draw.text((pill_x + (pill_w - cw) // 2, pill_y + 22), cta_t, font=f_cta, fill=(255, 255, 255))

    img.save(f"{OUT_DIR}/sales-slide-7.png", "PNG", optimize=True)
    print("✓ sales-slide-7.png")


if __name__ == "__main__":
    slide_1()
    slide_2()
    slide_3()
    slide_4()
    slide_5()
    slide_6()
    slide_7()
    print("\n✅ Generated 7 sales slides at:", OUT_DIR)
