"""Instagram ストーリー画像 3バリエーション生成 (1080x1920)
- story-1.png: 朝の通学時間訴求 (受験生向け)
- story-2.png: 親へのDM風 (保護者向け)
- story-3.png: 紹介プログラムシェア用
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/System/Library/Fonts"
FONT_REGULAR = f"{FONT_DIR}/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = f"{FONT_DIR}/ヒラギノ角ゴシック W6.ttc"
FONT_BLACK = f"{FONT_DIR}/ヒラギノ角ゴシック W9.ttc"

W, H = 1080, 1920

BG_DARK = (10, 14, 30)
BRAND_PURPLE = (139, 92, 246)
BRAND_PURPLE_DARK = (91, 33, 182)
BRAND_PINK = (236, 72, 153)
BRAND_GOLD = (251, 191, 36)
BRAND_RED = (220, 38, 38)
TEXT = (245, 245, 250)
TEXT_DIM = (170, 175, 195)
TEXT_MUTED = (130, 135, 150)


def load_font(p, s):
    return ImageFont.truetype(p, s)


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


def text_w(d, t, f):
    b = d.textbbox((0, 0), t, font=f)
    return b[2] - b[0]


def draw_centered(d, t, f, y, c, w=W):
    tw = text_w(d, t, f)
    d.text(((w - tw) // 2, y), t, font=f, fill=c)


def base_canvas():
    img = Image.new("RGB", (W, H), BG_DARK)
    img = draw_gradient_bg(img, (6, 10, 24), (24, 16, 46))
    draw_orb(img, 850, 400, 400, BRAND_PINK, 50)
    draw_orb(img, 200, 1500, 500, BRAND_PURPLE, 50)
    return img


def draw_link_sticker_hint(d, y):
    """『リンクステッカー』の位置を示すヒント (実際のIGストーリー作成時に配置)"""
    box_w, box_h = 700, 110
    box_x = (W - box_w) // 2
    d.rounded_rectangle((box_x, y, box_x + box_w, y + box_h), radius=24, fill=(255, 255, 255), outline=BRAND_PINK, width=4)
    f = load_font(FONT_BLACK, 36)
    fs = load_font(FONT_BOLD, 22)
    draw_centered(d, "trillion-ai-juku.com", f, y + 22, (40, 40, 80))
    draw_centered(d, "↑ ここにリンクステッカーを貼る", fs, y + 70, BRAND_RED)


# ============================================================
# Story 1: 朝の通学訴求 (受験生向け)
# ============================================================
def story_1():
    img = base_canvas()
    d = ImageDraw.Draw(img)

    # 上部: ブランド
    f_b = load_font(FONT_BLACK, 36)
    draw_centered(d, "AI学習コーチ塾", f_b, 100, BRAND_PURPLE)

    # メインフック
    f_huge = load_font(FONT_BLACK, 130)
    f_big = load_font(FONT_BLACK, 90)
    f_med = load_font(FONT_BOLD, 50)

    draw_centered(d, "通学電車の", f_med, 350, TEXT_DIM)
    draw_centered(d, "20分で、", f_big, 440, TEXT)
    draw_centered(d, "偏差値5", f_huge, 580, BRAND_GOLD)
    draw_centered(d, "上げる方法。", f_big, 740, TEXT)

    # サブ
    f_s = load_font(FONT_BOLD, 38)
    draw_centered(d, "AIが昨日の弱点だけを", f_s, 920, TEXT_DIM)
    draw_centered(d, "ピンポイント復習。", f_s, 980, TEXT_DIM)

    # 価格カード
    card_w, card_h = 850, 220
    card_x = (W - card_w) // 2
    card_y = 1130
    d.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h),
                        radius=24, fill=(35, 25, 60), outline=BRAND_GOLD, width=3)
    f_label = load_font(FONT_BOLD, 32)
    f_price = load_font(FONT_BLACK, 110)
    draw_centered(d, "今だけ 3日間 体験", f_label, card_y + 30, TEXT_DIM)
    draw_centered(d, "¥1,980", f_price, card_y + 75, BRAND_GOLD)

    # 緊急性
    f_urge = load_font(FONT_BLACK, 28)
    badge_w, badge_h = 600, 60
    badge_x = (W - badge_w) // 2
    badge_y = 1430
    d.rounded_rectangle((badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
                        radius=30, fill=BRAND_RED)
    draw_centered(d, "先着100名 限定", f_urge, badge_y + 16, TEXT)

    # リンクステッカーヒント
    draw_link_sticker_hint(d, 1620)

    # 注記
    f_note = load_font(FONT_REGULAR, 18)
    draw_centered(d, "※個人の感想です。3日体験後はスタンダード¥24,980/月+入塾金¥10,000 (初回のみ)", f_note, 1810, TEXT_MUTED)

    img.save(f"{OUT_DIR}/story-1-morning.png", "PNG", optimize=True)
    print("✓ story-1-morning.png")


# ============================================================
# Story 2: 保護者向け (DM風)
# ============================================================
def story_2():
    img = base_canvas()
    d = ImageDraw.Draw(img)

    f_b = load_font(FONT_BLACK, 36)
    draw_centered(d, "AI学習コーチ塾", f_b, 100, BRAND_PURPLE)

    # フック (保護者の不安)
    f_h = load_font(FONT_BLACK, 70)
    draw_centered(d, "塾代 月3万円。", f_h, 280, TEXT)
    draw_centered(d, "本当に意味ある？", f_h, 380, BRAND_GOLD)

    # DM風カード (保護者LINE風)
    card_x, card_y, card_w, card_h = 80, 540, 920, 600
    d.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h),
                        radius=24, fill=(245, 245, 250))

    # ヘッダー
    f_dm_h = load_font(FONT_BOLD, 26)
    d.rectangle((card_x, card_y, card_x + card_w, card_y + 70), fill=(7, 199, 85))
    draw_centered(d, "親LINEグループ", f_dm_h, card_y + 22, (255, 255, 255))

    # メッセージ1 (左寄せ)
    msg_y = card_y + 100
    f_msg = load_font(FONT_BOLD, 24)
    f_name = load_function = load_font(FONT_REGULAR, 18)
    d.text((card_x + 30, msg_y), "Aさん", font=f_name, fill=(100, 100, 120))
    bub_x = card_x + 30
    bub_y = msg_y + 26
    bub_w = 700
    d.rounded_rectangle((bub_x, bub_y, bub_x + bub_w, bub_y + 110),
                        radius=16, fill=(220, 230, 250))
    d.text((bub_x + 20, bub_y + 18), "うちの子、塾通っても伸び悩んでて…", font=f_msg, fill=(40, 40, 60))
    d.text((bub_x + 20, bub_y + 50), "月3万も払ってるのに。", font=f_msg, fill=(40, 40, 60))
    d.text((bub_x + 20, bub_y + 82), "何かいい方法ない？", font=f_msg, fill=(40, 40, 60))

    # メッセージ2 (右寄せ - 自分)
    msg_y2 = bub_y + 150
    d.text((card_x + card_w - 100, msg_y2), "あなた", font=f_name, fill=(100, 100, 120))
    bub_x2 = card_x + card_w - bub_w - 30
    bub_y2 = msg_y2 + 26
    d.rounded_rectangle((bub_x2, bub_y2, bub_x2 + bub_w, bub_y2 + 250),
                        radius=16, fill=(140, 220, 255))
    d.text((bub_x2 + 20, bub_y2 + 18), "うちは AI学習コーチ塾に切替えて", font=f_msg, fill=(20, 30, 60))
    d.text((bub_x2 + 20, bub_y2 + 50), "スタンダード¥24,980/月。", font=f_msg, fill=(20, 30, 60))
    d.text((bub_x2 + 20, bub_y2 + 82), "24時間AIが個別指導 + 9機能。", font=f_msg, fill=(20, 30, 60))
    d.text((bub_x2 + 20, bub_y2 + 114), "週次レポートで進捗わかるし、", font=f_msg, fill=(20, 30, 60))
    d.text((bub_x2 + 20, bub_y2 + 146), "通塾不要だから時間も浮く。", font=f_msg, fill=(20, 30, 60))
    d.text((bub_x2 + 20, bub_y2 + 178), "まず3日¥1,980で試せるよ。", font=f_msg, fill=BRAND_PINK)
    f_link = load_font(FONT_BOLD, 22)
    d.text((bub_x2 + 20, bub_y2 + 212), "↓ プロフィールリンクから", font=f_link, fill=BRAND_PINK)

    # CTA
    f_cta = load_font(FONT_BLACK, 38)
    draw_centered(d, "保護者の方も多数登録中", f_cta, 1230, BRAND_GOLD)

    # リンクステッカー
    draw_link_sticker_hint(d, 1420)

    # 注記
    f_note = load_font(FONT_REGULAR, 18)
    draw_centered(d, "※個人の感想です。効果には個人差があります。", f_note, 1660, TEXT_MUTED)
    draw_centered(d, "3日後はスタンダード¥24,980/月+入塾金¥10,000 (初回のみ・ワンタップ即解約可)", f_note, 1690, TEXT_MUTED)

    img.save(f"{OUT_DIR}/story-2-parent.png", "PNG", optimize=True)
    print("✓ story-2-parent.png")


# ============================================================
# Story 3: 紹介プログラム (シェア用)
# ============================================================
def story_3():
    img = base_canvas()
    d = ImageDraw.Draw(img)

    f_b = load_font(FONT_BLACK, 36)
    draw_centered(d, "AI学習コーチ塾", f_b, 100, BRAND_PURPLE)

    # フック
    f_h = load_font(FONT_BLACK, 76)
    draw_centered(d, "友達紹介で", f_h, 290, TEXT)
    draw_centered(d, "2人とも", f_h, 400, TEXT)

    # ハイライト
    f_em = load_font(FONT_BLACK, 110)
    draw_centered(d, "得をする。", f_em, 520, BRAND_GOLD)

    # 特典 2カード
    card_w, card_h = 460, 360
    gap = 30
    total_w = card_w * 2 + gap
    left_x = (W - total_w) // 2
    right_x = left_x + card_w + gap
    top = 760

    # 左: あなた
    d.rounded_rectangle((left_x, top, left_x + card_w, top + card_h),
                        radius=24, fill=(28, 32, 60), outline=BRAND_PURPLE, width=3)
    f_role = load_font(FONT_BOLD, 36)
    f_reward = load_font(FONT_BLACK, 56)
    f_desc = load_font(FONT_BOLD, 22)
    # カラム内中央配置 (バグ修正: draw_centered と d.text の二重描画を解消)
    rl_w = text_w(d, "あなた", f_role)
    d.text((left_x + (card_w - rl_w) // 2, top + 40), "あなた", font=f_role, fill=BRAND_PURPLE)
    rw_w = text_w(d, "1ヶ月", f_reward)
    d.text((left_x + (card_w - rw_w) // 2, top + 110), "1ヶ月", font=f_reward, fill=BRAND_GOLD)
    fr_w = text_w(d, "無料", f_reward)
    d.text((left_x + (card_w - fr_w) // 2, top + 180), "無料", font=f_reward, fill=BRAND_GOLD)
    dc_w = text_w(d, "次回月額が", f_desc)
    d.text((left_x + (card_w - dc_w) // 2, top + 290), "次回月額が", font=f_desc, fill=TEXT_DIM)
    dc2_w = text_w(d, "¥0 になる", f_desc)
    d.text((left_x + (card_w - dc2_w) // 2, top + 320), "¥0 になる", font=f_desc, fill=TEXT_DIM)

    # 右: 友達
    d.rounded_rectangle((right_x, top, right_x + card_w, top + card_h),
                        radius=24, fill=(28, 32, 60), outline=BRAND_PINK, width=3)
    fr_w = text_w(d, "友達", f_role)
    d.text((right_x + (card_w - fr_w) // 2, top + 40), "友達", font=f_role, fill=BRAND_PINK)
    rw2 = "初月50%"
    rw2_w = text_w(d, rw2, f_reward)
    d.text((right_x + (card_w - rw2_w) // 2, top + 110), rw2, font=f_reward, fill=BRAND_GOLD)
    rw3 = "OFF"
    rw3_w = text_w(d, rw3, f_reward)
    d.text((right_x + (card_w - rw3_w) // 2, top + 180), rw3, font=f_reward, fill=BRAND_GOLD)
    dc_w = text_w(d, "月¥24,980 →", f_desc)
    d.text((right_x + (card_w - dc_w) // 2, top + 290), "月¥24,980 →", font=f_desc, fill=TEXT_DIM)
    dc2_w = text_w(d, "初月¥12,490 になる", f_desc)
    d.text((right_x + (card_w - dc2_w) // 2, top + 320), "初月¥12,490 になる", font=f_desc, fill=TEXT_DIM)

    # CTA
    f_cta = load_font(FONT_BLACK, 38)
    draw_centered(d, "あなた専用コードを発行中", f_cta, 1180, BRAND_GOLD)
    f_sub = load_font(FONT_BOLD, 26)
    draw_centered(d, "AIJ-XXXX-YYYY 形式で即発行・LINE/Xシェア", f_sub, 1240, TEXT_DIM)

    # リンクステッカー
    draw_link_sticker_hint(d, 1420)

    # 注記
    f_note = load_font(FONT_REGULAR, 18)
    draw_centered(d, "※紹介成立後、自動で特典付与されます。", f_note, 1690, TEXT_MUTED)

    img.save(f"{OUT_DIR}/story-3-referral.png", "PNG", optimize=True)
    print("✓ story-3-referral.png")


if __name__ == "__main__":
    story_1()
    story_2()
    story_3()
    print(f"\n✅ Generated 3 stories at: {OUT_DIR}")
