"""Instagram用1080x1080スライド5枚を自動生成する。

Usage:
    python3 generate_ig_slides.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

# パス設定
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/System/Library/Fonts"
FONT_REGULAR = f"{FONT_DIR}/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = f"{FONT_DIR}/ヒラギノ角ゴシック W6.ttc"
FONT_BLACK = f"{FONT_DIR}/ヒラギノ角ゴシック W9.ttc"

# サイズ
W, H = 1080, 1080
PADDING = 100

# カラー
BG = (10, 10, 26)
BRAND_PURPLE = (167, 139, 250)
TEXT_LIGHT = (228, 228, 231)
TEXT_DIM = (203, 213, 225)
TEXT_MUTED = (148, 163, 184)
GRAD_TITLE_FROM = (199, 210, 254)  # light indigo
GRAD_TITLE_TO = (249, 168, 212)     # light pink
GRAD_PRICE_FROM = (251, 191, 36)    # amber
GRAD_PRICE_TO = (236, 72, 153)      # pink
SUCCESS = (16, 185, 129)


def load_font(path: str, size: int):
    """ヒラギノは .ttc なので index 指定。0=Regular weight family内。"""
    return ImageFont.truetype(path, size, index=0)


def make_background():
    """グラデーション背景＋装飾orb（柔らかい光）"""
    img = Image.new("RGB", (W, H), BG)

    # 大きなぼかしorb 3つを別レイヤーで合成
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_o = ImageDraw.Draw(overlay)

    # 左下の紫orb (大)
    draw_o.ellipse([-200, 600, 600, 1400], fill=(99, 102, 241, 70))
    # 右上のピンクorb (中)
    draw_o.ellipse([600, -150, 1400, 650], fill=(236, 72, 153, 60))
    # 中央下の青orb (小)
    draw_o.ellipse([350, 800, 850, 1300], fill=(14, 165, 233, 40))

    # ぼかし
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=120))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return img


def draw_gradient_text(img, text, font, xy, c1, c2, anchor="lt"):
    """テキストにLinearグラデーションを適用してdrawする。"""
    # 一時的に白でテキストを描画したマスクを作る
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.text(xy, text, font=font, fill=255, anchor=anchor)

    # bbox取ってグラデーション画像作成
    bbox = mask.getbbox()
    if not bbox:
        return
    x1, y1, x2, y2 = bbox
    grad_w = x2 - x1
    grad_h = y2 - y1
    grad = Image.new("RGB", (grad_w, grad_h))
    pixels = grad.load()
    for x in range(grad_w):
        for y in range(grad_h):
            t = (x + y) / (grad_w + grad_h)  # 対角グラデーション
            r = int(c1[0] * (1 - t) + c2[0] * t)
            g = int(c1[1] * (1 - t) + c2[1] * t)
            b = int(c1[2] * (1 - t) + c2[2] * t)
            pixels[x, y] = (r, g, b)
    # マスクを適用してimgに貼り付け
    img.paste(grad, (x1, y1), mask.crop(bbox))


def draw_text_centered(draw, text, font, y, color):
    """中央揃えでテキスト描画（X中心）"""
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (W - w) // 2
    draw.text((x, y), text, font=font, fill=color)


def draw_multiline(draw, lines, font, x, y, color, line_height=None):
    """複数行を順に描画。line_height指定なければfont sizeから自動。"""
    if line_height is None:
        bbox = draw.textbbox((0, 0), "あ", font=font)
        line_height = (bbox[3] - bbox[1]) + 20
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_height), line, font=font, fill=color)


def make_slide(slide_num: int, build_fn):
    img = make_background()
    build_fn(img)
    out = os.path.join(OUT_DIR, f"ig-slide-{slide_num}.png")
    img.save(out, "PNG", optimize=True)
    print(f"  ✓ {out}")


# ============================================================
# Slide 1: HERO
# ============================================================
def slide_1_hero(img):
    draw = ImageDraw.Draw(img)
    f_brand = load_font(FONT_BOLD, 32)
    f_title_big = load_font(FONT_BLACK, 130)
    f_sub = load_font(FONT_BOLD, 50)
    f_foot = load_font(FONT_BOLD, 36)

    # ブランド (上)
    draw.text((PADDING, PADDING + 20), "AI学習コーチ塾 / LAUNCH", font=f_brand, fill=BRAND_PURPLE)

    # タイトル (中央)
    draw_gradient_text(img, "塾の限界を、", f_title_big, (PADDING, 280), GRAD_TITLE_FROM, GRAD_TITLE_TO)
    draw_gradient_text(img, "AIで超える。", f_title_big, (PADDING, 440), GRAD_TITLE_FROM, GRAD_TITLE_TO)

    # サブテキスト
    draw = ImageDraw.Draw(img)  # re-fetch (paste した後)
    draw.text((PADDING, 660), "第1期生100名限定", font=f_sub, fill=TEXT_DIM)
    draw.text((PADDING, 730), "販売開始しました", font=f_sub, fill=TEXT_DIM)

    # 下部CTA
    draw.text((PADDING, H - PADDING - 40), "→ trillion-ai-juku.com", font=f_foot, fill=BRAND_PURPLE)


# ============================================================
# Slide 2: PROBLEM (3 limits)
# ============================================================
def slide_2_problem(img):
    draw = ImageDraw.Draw(img)
    f_brand = load_font(FONT_BOLD, 32)
    f_title = load_font(FONT_BLACK, 100)
    f_item = load_font(FONT_BOLD, 54)
    f_outro = load_font(FONT_BOLD, 42)
    f_mark = load_font(FONT_BLACK, 54)
    RED = (248, 113, 113)

    draw.text((PADDING, PADDING + 20), "02 / こんな経験ありませんか？", font=f_brand, fill=BRAND_PURPLE)

    # タイトル
    draw_gradient_text(img, '塾の"3つの限界"', f_title, (PADDING, 250), GRAD_TITLE_FROM, GRAD_TITLE_TO)

    # 3項目 — × (赤) + テキスト (白)
    draw = ImageDraw.Draw(img)
    items = [
        "深夜の質問は届かない",
        "クラス授業で個別最適は無理",
        "保護者報告は月1回が限界",
    ]
    for i, item in enumerate(items):
        y = 450 + i * 100
        draw.text((PADDING, y), "×", font=f_mark, fill=RED)
        draw.text((PADDING + 70, y), item, font=f_item, fill=TEXT_LIGHT)

    # 下部メッセージ
    draw.text((PADDING, H - PADDING - 80), "全部、AIなら解決できます。", font=f_outro, fill=TEXT_DIM)


# ============================================================
# Slide 3: FEATURES (5 main features)
# ============================================================
def slide_3_features(img):
    draw = ImageDraw.Draw(img)
    f_brand = load_font(FONT_BOLD, 32)
    f_item = load_font(FONT_BOLD, 50)
    f_foot = load_font(FONT_REGULAR, 30)

    draw.text((PADDING, PADDING + 20), "03 / 5つの主要機能", font=f_brand, fill=BRAND_PURPLE)

    items = [
        "✓ 24時間AIチューター",
        "✓ 個別カリキュラム自動生成",
        "✓ 教材AI自動生成",
        "✓ 毎週の保護者レポート",
        "✓ 模試履歴AI分析",
    ]
    for i, item in enumerate(items):
        # チェックマークは緑、テキストは白
        draw.text((PADDING, 280 + i * 110), "✓", font=f_item, fill=SUCCESS)
        draw.text((PADDING + 60, 280 + i * 110), item.replace("✓ ", ""), font=f_item, fill=TEXT_LIGHT)

    draw.text((PADDING, H - PADDING - 50), "全科目対応 / Claude Opus 4.7搭載", font=f_foot, fill=TEXT_MUTED)


# ============================================================
# Slide 4: COMPARE (¥30,000 vs ¥1,980)
# ============================================================
def slide_4_compare(img):
    draw = ImageDraw.Draw(img)
    f_brand = load_font(FONT_BOLD, 32)
    f_title = load_font(FONT_BLACK, 80)
    f_col_label = load_font(FONT_BOLD, 32)
    f_price_big = load_font(FONT_BLACK, 70)
    f_price_norm = load_font(FONT_BLACK, 60)
    f_col_sub = load_font(FONT_REGULAR, 22)

    draw.text((PADDING, PADDING + 20), "04 / 圧倒的コスパ", font=f_brand, fill=BRAND_PURPLE)

    # タイトル
    draw_gradient_text(img, "15分の1の料金で", f_title, (PADDING, 230), GRAD_TITLE_FROM, GRAD_TITLE_TO)
    draw_gradient_text(img, "10倍の学習密度", f_title, (PADDING, 340), GRAD_TITLE_FROM, GRAD_TITLE_TO)

    # 2カラム比較ボックスを別RGBAレイヤーで描画（半透明正しく表現）
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    box_y = 530
    box_h = 380
    col_w = (W - PADDING * 2 - 40) // 2
    left_x = PADDING
    right_x = PADDING + col_w + 40
    # 左 (普通の塾) - 暗めの半透明白
    od.rounded_rectangle([left_x, box_y, left_x + col_w, box_y + box_h], radius=24, fill=(255, 255, 255, 18))
    # 右 (AI塾) - 強調ボーダー付き
    od.rounded_rectangle([right_x, box_y, right_x + col_w, box_y + box_h], radius=24, fill=(99, 102, 241, 60), outline=(129, 140, 248, 200), width=4)
    # RGBAをRGB画像に合成
    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, overlay)
    # In-place で元imgを置き換え
    img.paste(img_rgba.convert("RGB"))
    draw = ImageDraw.Draw(img)

    # 左カラム内テキスト
    draw.text((left_x + 30, box_y + 30), "普通の塾", font=f_col_label, fill=TEXT_MUTED)
    draw.text((left_x + 30, box_y + 110), "¥30,000+", font=f_price_norm, fill=TEXT_DIM)
    draw.text((left_x + 30, box_y + 260), "週2〜3回", font=f_col_sub, fill=TEXT_MUTED)
    draw.text((left_x + 30, box_y + 300), "月1回の手書き報告", font=f_col_sub, fill=TEXT_MUTED)

    # 右カラム内テキスト
    draw.text((right_x + 30, box_y + 30), "AI学習コーチ塾", font=f_col_label, fill=BRAND_PURPLE)
    draw_gradient_text(img, "¥1,980", f_price_big, (right_x + 30, box_y + 110), GRAD_PRICE_FROM, GRAD_PRICE_TO)
    draw = ImageDraw.Draw(img)
    draw.text((right_x + 30, box_y + 260), "24時間対応", font=f_col_sub, fill=(199, 210, 254))
    draw.text((right_x + 30, box_y + 300), "毎週自動レポート", font=f_col_sub, fill=(199, 210, 254))


# ============================================================
# Slide 5: CTA
# ============================================================
def slide_5_cta(img):
    draw = ImageDraw.Draw(img)
    f_brand = load_font(FONT_BOLD, 32)
    f_title = load_font(FONT_BLACK, 100)
    f_price = load_font(FONT_BLACK, 140)
    f_sub = load_font(FONT_BOLD, 44)
    f_cta = load_font(FONT_BLACK, 52)
    f_foot = load_font(FONT_BOLD, 30)

    draw.text((PADDING, PADDING + 20), "05 / 今すぐスタート", font=f_brand, fill=BRAND_PURPLE)

    # タイトル（小さくして収める）
    draw_gradient_text(img, "3日間トライアル", f_title, (PADDING, 260), GRAD_TITLE_FROM, GRAD_TITLE_TO)
    # 価格ドーンと
    draw_gradient_text(img, "¥1,980", f_price, (PADDING, 400), GRAD_PRICE_FROM, GRAD_PRICE_TO)

    # サブ
    draw = ImageDraw.Draw(img)
    draw.text((PADDING, 600), "月¥24,980〜", font=f_sub, fill=TEXT_DIM)
    draw.text((PADDING, 660), "第1期生100名限定", font=f_sub, fill=TEXT_DIM)

    # 大きなCTAボックス
    box_x = PADDING
    box_y = 780
    box_w = W - PADDING * 2
    box_h = 130
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=30, fill=(99, 102, 241))
    bbox = draw.textbbox((0, 0), "trillion-ai-juku.com", font=f_cta)
    cta_w = bbox[2] - bbox[0]
    draw.text((box_x + (box_w - cta_w) // 2, box_y + 34), "trillion-ai-juku.com", font=f_cta, fill=(255, 255, 255))

    # 下部
    draw_text_centered(draw, "プロフィールのリンクから", f_foot, H - PADDING + 30, BRAND_PURPLE)


# ============================================================
# Run
# ============================================================
if __name__ == "__main__":
    print("Generating Instagram carousel slides (1080x1080)...")
    make_slide(1, slide_1_hero)
    make_slide(2, slide_2_problem)
    make_slide(3, slide_3_features)
    make_slide(4, slide_4_compare)
    make_slide(5, slide_5_cta)
    print("\n✅ All 5 slides generated in:", OUT_DIR)
