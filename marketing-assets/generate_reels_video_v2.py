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
    """0-3s: HOOK - 志望校への問いかけ"""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    f_huge = font(FONT_BLACK, 88)
    f_sub = font(FONT_BOLD, 54)
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
    f_title = font(FONT_BLACK, 95)
    f_item = font(FONT_BOLD, 58)
    f_mark = font(FONT_BLACK, 75)

    center_text(draw, "受験生が抱える、3つの不安", f_title, 280, TEXT)

    items = [
        "何をどれだけ勉強すれば",
        "今の実力で合格できるのか",
        "残り時間で挽回できるのか",
    ]
    for i, item in enumerate(items):
        y = 620 + i * 180
        draw.rounded_rectangle([120, y, 230, y + 100], radius=20, fill=(139, 30, 30))
        draw.text((143, y + 10), "?", font=f_mark, fill=RED)
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
    """33-48s: STEP3 AI生成カリキュラム(1週間の時間割)"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 44)
    f_head = font(FONT_BLACK, 60)

    draw.rounded_rectangle([60, 100, 280, 180], radius=20, fill=SUCCESS)
    draw.text((90, 123), "カリキュラム", font=font(FONT_BLACK, 32), fill=TEXT)
    draw.text((310, 120), "AIが自動生成！", font=f_brand, fill=SUCCESS)

    grad_text(img, "あなた専用の時間割", f_head, (150, 220), GRAD_T1, GRAD_T2)

    x, y, w, h = phone_frame(draw, y=340, h=1380)
    draw = ImageDraw.Draw(img)

    # ヘッダー
    draw.rounded_rectangle([x + 20, y + 20, x + w - 20, y + 120], radius=24, fill=PANEL_DARK)
    draw.text((x + 50, y + 50), "今週のスケジュール", font=font(FONT_BOLD, 38), fill=TEXT)

    # 週次スケジュール (月〜日)
    days = ["月", "火", "水", "木", "金", "土", "日"]
    schedule = [
        # (subject_code, title, duration, color)
        ("英", "長文読解・ﾊﾟﾗｸﾞﾗﾌ整序", "1.5h", (59, 130, 246)),
        ("数", "数III 極限・微分", "1.0h", (236, 72, 153)),
        ("英", "リスニング特訓", "1.0h", (59, 130, 246)),
        ("数", "積分の応用問題", "1.5h", (236, 72, 153)),
        ("国", "現代文 論説読解", "1.0h", (16, 185, 129)),
        ("模", "過去問演習 (早稲田 2023)", "3.0h", (251, 191, 36)),
        ("休", "復習 + AI診断", "1.0h", (148, 163, 184)),
    ]
    list_y = y + 160
    for i, (day, (code, title, dur, color)) in enumerate(zip(days, schedule)):
        ry = list_y + i * 150
        # カード
        draw.rounded_rectangle([x + 40, ry, x + w - 40, ry + 130], radius=16,
                               fill=PANEL_DARK, outline=color, width=2)
        # 曜日バッジ
        draw.rounded_rectangle([x + 60, ry + 25, x + 160, ry + 105], radius=14, fill=color)
        bbox = draw.textbbox((0, 0), day, font=font(FONT_BLACK, 56))
        tw = bbox[2] - bbox[0]
        draw.text((x + 60 + (100 - tw) // 2, ry + 22), day, font=font(FONT_BLACK, 56), fill=TEXT)
        # 科目コード
        draw.text((x + 190, ry + 25), f"[{code}]", font=font(FONT_BLACK, 30), fill=color)
        # タイトル
        draw.text((x + 190, ry + 65), title, font=font(FONT_BOLD, 28), fill=TEXT)
        # 時間 (右端)
        dur_text = dur
        bbox = draw.textbbox((0, 0), dur_text, font=font(FONT_BLACK, 36))
        dw = bbox[2] - bbox[0]
        draw.text((x + w - 40 - dw - 20, ry + 45), dur_text, font=font(FONT_BLACK, 36), fill=color)

    img.save(out_path, "PNG")
    return img


def scene_benefit(out_path):
    """48-54s: 価値訴求"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_top = font(FONT_BOLD, 54)
    f_big = font(FONT_BLACK, 110)
    f_sub = font(FONT_BOLD, 48)

    center_text(draw, "もう、迷わない。", f_top, 500, TEXT_DIM)

    grad_text(img, "何をいつやるか、", f_big, (130, 650), GRAD_T1, GRAD_T2)
    grad_text(img, "AIが決める。", f_big, (240, 810), GRAD_T1, GRAD_T2)

    draw = ImageDraw.Draw(img)
    center_text(draw, "あとは、実行するだけ。", f_sub, 1100, ACCENT)

    # 3つのチェック
    bullets = [
        "模試成績の弱点分析",
        "志望校からの逆算カリキュラム",
        "週次で自動アップデート",
    ]
    for i, b in enumerate(bullets):
        y = 1280 + i * 110
        draw.ellipse([140, y, 220, y + 80], fill=SUCCESS)
        draw.text((162, y + 10), "✓", font=font(FONT_BLACK, 54), fill=TEXT)
        draw.text((260, y + 15), b, font=font(FONT_BOLD, 42), fill=TEXT)

    img.save(out_path, "PNG")
    return img


def scene_cta(out_path):
    """54-60s: CTA"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_top = font(FONT_BOLD, 48)
    f_big = font(FONT_BLACK, 130)
    f_cta = font(FONT_BLACK, 70)
    f_foot = font(FONT_BOLD, 38)
    f_hint = font(FONT_BOLD, 34)

    center_text(draw, "あなたの志望校合格まで、", f_top, 250, TEXT_DIM)

    grad_text(img, "¥1,980で3日間", f_big, (150, 380), GRAD_T1, GRAD_T2)

    draw = ImageDraw.Draw(img)
    center_text(draw, "模試入力 → カリキュラム生成を", f_top, 620, TEXT)
    center_text(draw, "すべて試せます。", f_top, 690, TEXT)

    center_text(draw, "継続は月額¥24,980〜", f_hint, 790, WARNING)

    # CTAボックス
    box_y = 940
    box_h = 200
    draw.rounded_rectangle([100, box_y, W - 100, box_y + box_h], radius=50, fill=PRIMARY)
    bbox = draw.textbbox((0, 0), "trillion-ai-juku.com", font=f_cta)
    bw = bbox[2] - bbox[0]
    draw.text(((W - bw) // 2, box_y + 60), "trillion-ai-juku.com", font=f_cta, fill=TEXT)

    center_text(draw, "— プロフィールのリンクから —", f_foot, box_y + box_h + 80, PRIMARY_LIGHT)

    center_text(draw, "AI学習コーチ塾", font(FONT_BLACK, 52), 1550, TEXT)

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
