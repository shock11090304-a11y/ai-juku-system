"""第2動画: 模試結果→志望校→AIカリキュラム自動生成 訴求の60秒 Reels。

Usage:
    python3 generate_reels_video_v2.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import subprocess
import shutil

# === パス ===
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(OUT_DIR, "video-frames-v2")
FONT_DIR = "/System/Library/Fonts"
FONT_REGULAR = f"{FONT_DIR}/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = f"{FONT_DIR}/ヒラギノ角ゴシック W6.ttc"
FONT_BLACK = f"{FONT_DIR}/ヒラギノ角ゴシック W9.ttc"

W, H = 1080, 1920
FPS = 30

# === カラー ===
BG = (10, 10, 26)
PANEL = (22, 22, 42)
PANEL_DARK = (30, 30, 60)
PRIMARY = (99, 102, 241)
PRIMARY_LIGHT = (129, 140, 248)
ACCENT = (236, 72, 153)
TEXT = (228, 228, 231)
TEXT_DIM = (203, 213, 225)
TEXT_MUTED = (148, 163, 184)
SUCCESS = (16, 185, 129)
WARNING = (251, 191, 36)
RED = (248, 113, 113)
BLUE = (59, 130, 246)
GRAD_T1 = (199, 210, 254)
GRAD_T2 = (249, 168, 212)
GRAD_P1 = (251, 191, 36)
GRAD_P2 = (236, 72, 153)
GRAD_B1 = (129, 140, 248)
GRAD_B2 = (14, 165, 233)


def font(path, size):
    return ImageFont.truetype(path, size, index=0)


def gradient_bg():
    img = Image.new("RGB", (W, H), BG)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([-300, 1200, 700, 2200], fill=(99, 102, 241, 70))
    od.ellipse([500, -300, 1500, 700], fill=(236, 72, 153, 60))
    od.ellipse([300, 1500, 900, 2100], fill=(14, 165, 233, 40))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=150))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return img


def grad_text(img, text, fnt, xy, c1=GRAD_T1, c2=GRAD_T2):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=fnt, fill=255)
    bbox = mask.getbbox()
    if not bbox:
        return
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    grad = Image.new("RGB", (w, h))
    px = grad.load()
    for x in range(w):
        for y in range(h):
            t = (x + y) / max(w + h, 1)
            px[x, y] = (int(c1[0]*(1-t)+c2[0]*t), int(c1[1]*(1-t)+c2[1]*t), int(c1[2]*(1-t)+c2[2]*t))
    img.paste(grad, (x1, y1), mask.crop(bbox))


def center_text(draw, text, fnt, y, color):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) // 2, y), text, font=fnt, fill=color)


def phone_frame(draw, y=380, h=1320):
    """アプリ画面風の枠を描画。内側の座標範囲を返す"""
    x = 100
    w = W - 200
    draw.rounded_rectangle([x, y, x + w, y + h], radius=48, fill=PANEL, outline=(60, 60, 100), width=3)
    return x, y, w, h


# ==============================================================
# Scenes
# ==============================================================

def scene_hook(out_path):
    """0-3s: HOOK - ブランド(trillion-AI管理) + 志望校への問いかけ"""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BLACK, 72)
    f_huge = font(FONT_BLACK, 88)
    f_sub = font(FONT_BOLD, 54)

    # ブランド: trillion-AI管理 (画面上部)
    grad_text(img, "trillion-AI管理", f_brand, ((W - 720) // 2, 300), GRAD_B1, GRAD_B2)
    draw = ImageDraw.Draw(img)
    # 区切り線
    draw.rounded_rectangle([(W - 240) // 2, 430, (W + 240) // 2, 438], radius=4, fill=PRIMARY_LIGHT)

    center_text(draw, "模試E判定の今から、", f_huge, 620, TEXT)
    price_text = "志望校まで届きますか？"
    bbox = draw.textbbox((0, 0), price_text, font=f_huge)
    pw = bbox[2] - bbox[0]
    grad_text(img, price_text, f_huge, ((W - pw) // 2, 780), GRAD_P1, GRAD_P2)
    draw = ImageDraw.Draw(img)
    center_text(draw, "— 残り時間、何をすべきか —", f_sub, 1200, TEXT_MUTED)
    img.save(out_path, "PNG")
    return img


def scene_fears(out_path):
    """3-10s: 受験生・保護者の3つの不安"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_title = font(FONT_BLACK, 80)
    f_item = font(FONT_BOLD, 56)
    f_mark = font(FONT_BLACK, 70)

    # タイトル行1+2に分割して収める
    center_text(draw, "受験生が抱える、", f_title, 240, TEXT)
    grad_text(img, "3つの不安。", f_title, ((W - 380) // 2, 330), GRAD_P1, GRAD_P2)

    draw = ImageDraw.Draw(img)
    items = [
        "何をどれだけ勉強すれば",
        "今の実力で合格できるのか",
        "残り時間で挽回できるのか",
    ]
    for i, item in enumerate(items):
        y = 660 + i * 180
        draw.rounded_rectangle([120, y, 230, y + 100], radius=20, fill=(139, 30, 30))
        draw.text((150, y + 10), "?", font=f_mark, fill=RED)
        draw.text((270, y + 20), item, font=f_item, fill=TEXT)

    img.save(out_path, "PNG")
    return img


def scene_transition(out_path):
    """10-13s: 解決策の予告"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 50)
    f_body = font(FONT_BLACK, 105)

    center_text(draw, "— AI学習コーチ塾なら —", f_brand, 650, PRIMARY_LIGHT)

    grad_text(img, "3分で解決します。", f_body, (110, 830), GRAD_T1, GRAD_T2)

    draw = ImageDraw.Draw(img)
    f_sub = font(FONT_BOLD, 52)
    center_text(draw, "模試と志望校を入れるだけ。", f_sub, 1050, TEXT)
    img.save(out_path, "PNG")
    return img


def scene_step1_mock(out_path):
    """13-23s: STEP1 模試結果入力"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 44)
    f_head = font(FONT_BLACK, 60)

    draw.rounded_rectangle([60, 100, 260, 180], radius=20, fill=PRIMARY)
    draw.text((90, 120), "STEP 1", font=font(FONT_BLACK, 40), fill=TEXT)
    draw.text((290, 120), "模試結果を入力", font=f_brand, fill=PRIMARY_LIGHT)

    grad_text(img, "5科目・5秒で入力", f_head, (120, 220), GRAD_T1, GRAD_T2)

    x, y, w, h = phone_frame(draw, y=340, h=1380)
    draw = ImageDraw.Draw(img)

    # ヘッダー
    draw.rounded_rectangle([x + 20, y + 20, x + w - 20, y + 120], radius=24, fill=PANEL_DARK)
    draw.text((x + 50, y + 50), "模試成績入力", font=font(FONT_BOLD, 38), fill=TEXT)

    # 模試選択
    draw.rounded_rectangle([x + 50, y + 160, x + w - 50, y + 240], radius=16, fill=PANEL_DARK)
    draw.text((x + 80, y + 170), "模試:", font=font(FONT_BOLD, 26), fill=TEXT_DIM)
    draw.text((x + 80, y + 200), "2026年 第1回 全統模試", font=font(FONT_BOLD, 32), fill=TEXT)

    # 科目×点数グリッド
    subjects = [
        ("英語", 62, 100, 180, SUCCESS),
        ("数学", 48, 100, 180, WARNING),
        ("国語", 71, 100, 180, SUCCESS),
        ("理科", 53, 100, 180, WARNING),
        ("社会", 58, 100, 180, WARNING),
    ]
    list_y = y + 290
    for i, (subj, score, max_s, bar_base, color) in enumerate(subjects):
        ry = list_y + i * 130
        # 背景カード
        draw.rounded_rectangle([x + 50, ry, x + w - 50, ry + 110], radius=16, fill=PANEL_DARK)
        # 科目名
        draw.text((x + 80, ry + 20), subj, font=font(FONT_BLACK, 34), fill=TEXT)
        # スコア
        draw.text((x + 200, ry + 20), f"{score}", font=font(FONT_BLACK, 44), fill=color)
        draw.text((x + 280, ry + 35), f"/ {max_s}", font=font(FONT_BOLD, 28), fill=TEXT_MUTED)
        # プログレスバー
        bar_x = x + 400
        bar_w = w - 460
        draw.rounded_rectangle([bar_x, ry + 45, bar_x + bar_w, ry + 75], radius=15, fill=(50, 50, 80))
        fill_w = int(bar_w * score / max_s)
        draw.rounded_rectangle([bar_x, ry + 45, bar_x + fill_w, ry + 75], radius=15, fill=color)

    # 合計・判定
    tot_y = list_y + 5 * 130 + 30
    draw.rounded_rectangle([x + 50, tot_y, x + w - 50, tot_y + 170], radius=20,
                           fill=(60, 40, 60), outline=RED, width=3)
    draw.text((x + 80, tot_y + 25), "総合判定:", font=font(FONT_BOLD, 30), fill=TEXT)
    draw.text((x + 80, tot_y + 70), "E", font=font(FONT_BLACK, 90), fill=RED)
    draw.text((x + 230, tot_y + 100), "(あと偏差値+8必要)", font=font(FONT_BOLD, 28), fill=TEXT_DIM)

    img.save(out_path, "PNG")
    return img


def scene_step2_target(out_path):
    """23-33s: STEP2 志望校入力"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 44)
    f_head = font(FONT_BLACK, 60)

    draw.rounded_rectangle([60, 100, 260, 180], radius=20, fill=PRIMARY)
    draw.text((90, 120), "STEP 2", font=font(FONT_BLACK, 40), fill=TEXT)
    draw.text((290, 120), "志望校・期限を設定", font=f_brand, fill=PRIMARY_LIGHT)

    grad_text(img, "ゴールから逆算", f_head, (220, 220), GRAD_T1, GRAD_T2)

    x, y, w, h = phone_frame(draw, y=340, h=1380)
    draw = ImageDraw.Draw(img)

    # ヘッダー
    draw.rounded_rectangle([x + 20, y + 20, x + w - 20, y + 120], radius=24, fill=PANEL_DARK)
    draw.text((x + 50, y + 50), "志望校設定", font=font(FONT_BOLD, 38), fill=TEXT)

    # 志望校カード (メイン)
    card_y = y + 160
    draw.rounded_rectangle([x + 50, card_y, x + w - 50, card_y + 280], radius=24,
                           fill=(50, 50, 100), outline=PRIMARY_LIGHT, width=4)
    draw.text((x + 80, card_y + 25), "第1志望", font=font(FONT_BOLD, 28), fill=PRIMARY_LIGHT)
    draw.text((x + 80, card_y + 70), "早稲田大学 政治経済学部", font=font(FONT_BLACK, 44), fill=TEXT)
    draw.text((x + 80, card_y + 150), "偏差値目標: 70", font=font(FONT_BOLD, 30), fill=WARNING)
    draw.text((x + 80, card_y + 200), "試験日: 2027年2月22日", font=font(FONT_BOLD, 30), fill=TEXT_DIM)

    # ギャップ分析
    gap_y = card_y + 320
    draw.rounded_rectangle([x + 50, gap_y, x + w - 50, gap_y + 480], radius=24, fill=PANEL_DARK)
    draw.text((x + 80, gap_y + 30), "AIによるギャップ分析", font=font(FONT_BOLD, 34), fill=ACCENT)

    gap_items = [
        ("現在の偏差値", "62", TEXT_DIM),
        ("志望校偏差値", "70", WARNING),
        ("必要な伸び", "+8", ACCENT),
        ("残り期間", "302日", SUCCESS),
        ("必要な学習時間/日", "3.5h〜", PRIMARY_LIGHT),
    ]
    for i, (label, val, col) in enumerate(gap_items):
        ry = gap_y + 100 + i * 72
        draw.text((x + 80, ry), label, font=font(FONT_BOLD, 30), fill=TEXT_DIM)
        # 値を右寄せ
        bbox = draw.textbbox((0, 0), val, font=font(FONT_BLACK, 42))
        vw = bbox[2] - bbox[0]
        draw.text((x + w - 80 - vw, ry - 5), val, font=font(FONT_BLACK, 42), fill=col)

    # Generate ボタン
    btn_y = gap_y + 510
    draw.rounded_rectangle([x + 50, btn_y, x + w - 50, btn_y + 100], radius=20, fill=PRIMARY)
    btn_text = "AIカリキュラム生成"
    bbox = draw.textbbox((0, 0), btn_text, font=font(FONT_BLACK, 38))
    bw = bbox[2] - bbox[0]
    draw.text((x + (w - bw) // 2, btn_y + 30), btn_text, font=font(FONT_BLACK, 38), fill=TEXT)

    img.save(out_path, "PNG")
    return img


def scene_step3_curriculum(out_path):
    """33-48s: STEP3 AI生成カリキュラム — 実アプリの3フェーズ設計に忠実"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 40)
    f_head = font(FONT_BLACK, 58)

    # ヘッダーバッジ
    draw.rounded_rectangle([60, 100, 290, 180], radius=20, fill=SUCCESS)
    draw.text((90, 123), "カリキュラム", font=font(FONT_BLACK, 32), fill=TEXT)
    draw.text((320, 120), "AIが自動生成！", font=f_brand, fill=SUCCESS)

    grad_text(img, "あなた専用の学習計画", f_head, (100, 220), GRAD_T1, GRAD_T2)

    # アプリ画面フレーム
    x, y, w, h = phone_frame(draw, y=340, h=1400)
    draw = ImageDraw.Draw(img)

    # タイトル: 生成されたカリキュラム
    draw.text((x + 40, y + 30), "生成されたカリキュラム", font=font(FONT_BLACK, 42), fill=PRIMARY_LIGHT)

    # サブタイトル: 3フェーズ設計
    draw.rounded_rectangle([x + 30, y + 110, x + w - 30, y + 175], radius=14, fill=(40, 40, 80), outline=PRIMARY_LIGHT, width=2)
    draw.text((x + 50, y + 125), "■ 3フェーズ設計", font=font(FONT_BLACK, 32), fill=PRIMARY_LIGHT)

    # Phase 1: 基礎固め (4-6月、3ヶ月)
    ph1_y = y + 210
    draw.text((x + 40, ph1_y), "フェーズ1: 基礎固め (4-6月、3ヶ月)", font=font(FONT_BLACK, 30), fill=PRIMARY_LIGHT)
    # 完了条件
    draw.rounded_rectangle([x + 40, ph1_y + 55, x + w - 40, ph1_y + 140], radius=10, fill=(50, 25, 40))
    draw.text((x + 55, ph1_y + 65), "完了条件:", font=font(FONT_BLACK, 24), fill=ACCENT)
    draw.text((x + 55, ph1_y + 100), "青チャ例題2周・正答率85%", font=font(FONT_BOLD, 23), fill=TEXT)
    # 科目別タスク
    p1_items = [
        ("英単語", "シス単 No.1-1200 (1日60語×3周)"),
        ("英文法", "Vintage 1-900番 (1日30問)"),
        ("数学", "青チャ数IA 例題1-300 (1日5-8題)"),
    ]
    for i, (subj, detail) in enumerate(p1_items):
        ry = ph1_y + 165 + i * 65
        draw.text((x + 55, ry), "•", font=font(FONT_BLACK, 28), fill=PRIMARY_LIGHT)
        draw.text((x + 85, ry + 2), subj + ":", font=font(FONT_BOLD, 24), fill=TEXT)
        draw.text((x + 210, ry + 2), detail, font=font(FONT_BOLD, 22), fill=TEXT_DIM)

    # Phase 2: 標準演習 (7-10月、4ヶ月)
    ph2_y = ph1_y + 400
    draw.text((x + 40, ph2_y), "フェーズ2: 標準演習 (7-10月、4ヶ月)", font=font(FONT_BLACK, 30), fill=PRIMARY_LIGHT)
    draw.rounded_rectangle([x + 40, ph2_y + 55, x + w - 40, ph2_y + 140], radius=10, fill=(50, 25, 40))
    draw.text((x + 55, ph2_y + 65), "完了条件:", font=font(FONT_BLACK, 24), fill=ACCENT)
    draw.text((x + 55, ph2_y + 100), "1対1対応 7割理解・長文週2題正答", font=font(FONT_BOLD, 23), fill=TEXT)
    p2_items = [
        ("英語", "ポレポレ + やっておきたい500"),
        ("数学", "1対1対応の演習 数IA/IIB"),
    ]
    for i, (subj, detail) in enumerate(p2_items):
        ry = ph2_y + 165 + i * 65
        draw.text((x + 55, ry), "•", font=font(FONT_BLACK, 28), fill=PRIMARY_LIGHT)
        draw.text((x + 85, ry + 2), subj + ":", font=font(FONT_BOLD, 24), fill=TEXT)
        draw.text((x + 180, ry + 2), detail, font=font(FONT_BOLD, 22), fill=TEXT_DIM)

    # Phase 3: 過去問 (予告) — 見切れて次を示唆
    ph3_y = ph2_y + 310
    if ph3_y + 60 < y + h - 30:
        draw.text((x + 40, ph3_y), "フェーズ3: 過去問演習 (11-2月) ...", font=font(FONT_BOLD, 28), fill=TEXT_MUTED)

    img.save(out_path, "PNG")
    return img


def scene_benefit(out_path):
    """48-54s: 価値訴求 — チェックマークをポリゴン描画で確実に表示"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_top = font(FONT_BOLD, 54)
    f_big = font(FONT_BLACK, 110)
    f_sub = font(FONT_BOLD, 48)

    center_text(draw, "もう、迷わない。", f_top, 480, TEXT_DIM)

    grad_text(img, "何をいつやるか、", f_big, (130, 620), GRAD_T1, GRAD_T2)
    grad_text(img, "AIが決める。", f_big, (240, 780), GRAD_T1, GRAD_T2)

    draw = ImageDraw.Draw(img)
    center_text(draw, "あとは、実行するだけ。", f_sub, 1070, ACCENT)

    # 3つのチェック — 緑丸の中にポリゴンチェックマーク
    bullets = [
        "模試成績の弱点分析",
        "志望校からの逆算カリキュラム",
        "週次で自動アップデート",
    ]
    for i, b in enumerate(bullets):
        y = 1260 + i * 120
        # 緑丸
        cx, cy, r = 180, y + 40, 42
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUCCESS)
        # ポリゴンでチェックマーク描画
        draw.line([(cx - 18, cy + 2), (cx - 4, cy + 16), (cx + 20, cy - 12)],
                  fill=TEXT, width=8)
        # テキスト
        draw.text((260, y + 15), b, font=font(FONT_BOLD, 42), fill=TEXT)

    img.save(out_path, "PNG")
    return img


def scene_cta(out_path):
    """54-60s: CTA — 強い煽り+緊急性"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_top = font(FONT_BOLD, 46)
    f_big = font(FONT_BLACK, 130)
    f_cta = font(FONT_BLACK, 66)
    f_foot = font(FONT_BOLD, 38)
    f_hint = font(FONT_BOLD, 32)

    center_text(draw, "あなたの志望校合格まで、", f_top, 220, TEXT_DIM)

    grad_text(img, "7日間 完全無料で", f_big, (150, 340), GRAD_T1, GRAD_T2)

    draw = ImageDraw.Draw(img)
    center_text(draw, "模試入力 → カリキュラム生成を", f_top, 580, TEXT)
    center_text(draw, "すべて試せます。", f_top, 650, TEXT)

    # 緊急性バッジ
    badge_w = 520
    badge_x = (W - badge_w) // 2
    draw.rounded_rectangle([badge_x, 770, badge_x + badge_w, 850], radius=20,
                           fill=(60, 30, 40), outline=RED, width=3)
    draw.text((badge_x + 25, 788), "創設メンバー50名限定・早い者勝ち", font=font(FONT_BLACK, 30), fill=RED)

    center_text(draw, "継続は月額¥24,980〜 (自動課金なし)", f_hint, 880, WARNING)

    # CTAボックス
    box_y = 970
    box_h = 200
    draw.rounded_rectangle([100, box_y, W - 100, box_y + box_h], radius=50, fill=PRIMARY)
    bbox = draw.textbbox((0, 0), "trillion-ai-juku.com", font=f_cta)
    bw = bbox[2] - bbox[0]
    draw.text(((W - bw) // 2, box_y + 62), "trillion-ai-juku.com", font=f_cta, fill=TEXT)

    center_text(draw, "— プロフィールのリンクから —", f_foot, box_y + box_h + 80, PRIMARY_LIGHT)

    center_text(draw, "AI学習コーチ塾", font(FONT_BLACK, 52), 1560, TEXT)

    img.save(out_path, "PNG")
    return img


# ==============================================================
# Main
# ==============================================================

def main():
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR)

    scenes = [
        (3, scene_hook),
        (7, scene_fears),
        (3, scene_transition),
        (10, scene_step1_mock),
        (10, scene_step2_target),
        (15, scene_step3_curriculum),
        (6, scene_benefit),
        (6, scene_cta),
    ]
    total = sum(s[0] for s in scenes)
    print(f"Total duration: {total}s (target: 60s)")

    scene_files = []
    for i, (dur, fn) in enumerate(scenes, 1):
        out = os.path.join(FRAMES_DIR, f"scene-{i:02d}.png")
        fn(out)
        scene_files.append((out, dur))
        print(f"  ✓ Scene {i}: {out} ({dur}s)")

    concat_path = os.path.join(FRAMES_DIR, "concat.txt")
    with open(concat_path, "w") as f:
        for img, dur in scene_files:
            f.write(f"file '{img}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{scene_files[-1][0]}'\n")

    out_mp4 = os.path.join(OUT_DIR, "reels-curriculum-60sec.mp4")
    ffmpeg_bin = os.path.expanduser("~/.local/bin/ffmpeg")
    cmd = [
        ffmpeg_bin, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_path,
        "-vf", f"fps={FPS},format=yuv420p,scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out_mp4,
    ]
    print("\n▶ Running ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg stderr:\n", result.stderr[-2000:])
        raise RuntimeError("ffmpeg failed")

    # Trim to exactly 60s
    trimmed = out_mp4 + ".tmp.mp4"
    subprocess.run([ffmpeg_bin, "-y", "-i", out_mp4, "-t", "60", "-c", "copy", trimmed],
                   capture_output=True)
    os.replace(trimmed, out_mp4)

    size_kb = os.path.getsize(out_mp4) // 1024
    print(f"\n✅ Video generated: {out_mp4} ({size_kb} KB)")


if __name__ == "__main__":
    main()
