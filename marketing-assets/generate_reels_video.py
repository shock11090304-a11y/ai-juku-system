"""60秒 Reels 動画を自動生成する。
アプリ画面を PIL で再現したフレーム + ffmpeg で動画合成。

Usage:
    python3 generate_reels_video.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import subprocess
import shutil
import math

# === パス設定 ===
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(OUT_DIR, "video-frames")
FONT_DIR = "/System/Library/Fonts"
FONT_REGULAR = f"{FONT_DIR}/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = f"{FONT_DIR}/ヒラギノ角ゴシック W6.ttc"
FONT_BLACK = f"{FONT_DIR}/ヒラギノ角ゴシック W9.ttc"

# === 動画設定 (Reels: 1080x1920 縦型, 30fps) ===
W, H = 1080, 1920
FPS = 30

# === カラー ===
BG = (10, 10, 26)
PANEL = (22, 22, 42)
PRIMARY = (99, 102, 241)
PRIMARY_LIGHT = (129, 140, 248)
ACCENT = (236, 72, 153)
TEXT = (228, 228, 231)
TEXT_DIM = (203, 213, 225)
TEXT_MUTED = (148, 163, 184)
SUCCESS = (16, 185, 129)
WARNING = (251, 191, 36)
RED = (248, 113, 113)
GRAD_T1 = (199, 210, 254)
GRAD_T2 = (249, 168, 212)
GRAD_P1 = (251, 191, 36)
GRAD_P2 = (236, 72, 153)


def font(path, size):
    return ImageFont.truetype(path, size, index=0)


def gradient_bg():
    """ブランド背景: 暗い+紫ピンクorb"""
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
    """グラデーションテキスト"""
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


def wrap_text(text, fnt, max_w, draw):
    """日本語文字列を max_w 内に折り返し"""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=fnt)
        if bbox[2] - bbox[0] > max_w and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


# ==============================================================
# Scene builders
# ==============================================================

def scene_hook(out_path):
    """0-3s: HOOK - 黒背景に大きなテキスト"""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    f_huge = font(FONT_BLACK, 130)
    f_big = font(FONT_BLACK, 155)
    f_sub = font(FONT_BOLD, 60)
    # 中央に配置
    center_text(draw, "塾に月", f_huge, 600, TEXT)
    # ¥30,000 を中央揃えで(大きさを抑えて画面幅に収める)
    price_text = "¥30,000"
    bbox = draw.textbbox((0, 0), price_text, font=f_big)
    pw = bbox[2] - bbox[0]
    grad_text(img, price_text, f_big, ((W - pw) // 2, 750), GRAD_P1, GRAD_P2)
    draw = ImageDraw.Draw(img)
    center_text(draw, "払ってませんか？", f_huge, 970, TEXT)
    # 下部にブランド
    center_text(draw, "— 3秒だけ、聞いてください —", f_sub, 1250, TEXT_MUTED)
    img.save(out_path, "PNG")
    return img


def scene_problem_intro(out_path):
    """3-8s: 12年塾経営の塾長からの一言"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 42)
    f_body = font(FONT_BLACK, 90)
    f_sub = font(FONT_BOLD, 50)

    center_text(draw, "— AI学習コーチ塾 塾長 —", f_brand, 450, PRIMARY_LIGHT)

    grad_text(img, "塾経営12年で", f_body, (120, 650), GRAD_T1, GRAD_T2)
    grad_text(img, "見つけた限界。", f_body, (120, 800), GRAD_T1, GRAD_T2)

    draw = ImageDraw.Draw(img)
    center_text(draw, "AIで全部、解決できました。", f_sub, 1100, TEXT_DIM)
    img.save(out_path, "PNG")
    return img


def scene_problem_list(out_path):
    """8-15s: 3つの限界"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_title = font(FONT_BLACK, 95)
    f_item = font(FONT_BOLD, 62)
    f_mark = font(FONT_BLACK, 75)

    center_text(draw, "塾の、3つの限界", f_title, 350, TEXT)

    items = [
        "深夜の質問は届かない",
        "クラス授業で個別最適は無理",
        "保護者報告は月1回が限界",
    ]
    for i, item in enumerate(items):
        y = 700 + i * 180
        # 赤い×マーク
        draw.rounded_rectangle([120, y, 230, y + 100], radius=20, fill=(139, 30, 30))
        draw.text((143, y + 10), "×", font=f_mark, fill=RED)
        # テキスト
        draw.text((270, y + 20), item, font=f_item, fill=TEXT)

    img.save(out_path, "PNG")
    return img


def scene_app_chat(out_path):
    """15-25s: AIチューター画面 (チャット風モックアップ)"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 48)
    f_head = font(FONT_BLACK, 62)

    center_text(draw, "機能①  24時間AIチューター", f_brand, 120, PRIMARY_LIGHT)
    grad_text(img, "深夜2時でも、即回答", f_head, (150, 200), GRAD_T1, GRAD_T2)

    # アプリ画面風の枠
    phone_x, phone_y, phone_w, phone_h = 100, 380, W - 200, 1320
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([phone_x, phone_y, phone_x + phone_w, phone_y + phone_h],
                           radius=48, fill=PANEL, outline=(60, 60, 100), width=3)

    # ヘッダー
    draw.rounded_rectangle([phone_x + 20, phone_y + 20, phone_x + phone_w - 20, phone_y + 120],
                           radius=24, fill=(30, 30, 60))
    draw.text((phone_x + 50, phone_y + 50), "[AI] AIチューター", font=font(FONT_BOLD, 38), fill=TEXT)
    draw.ellipse([phone_x + phone_w - 100, phone_y + 55, phone_x + phone_w - 50, phone_y + 105],
                 fill=SUCCESS)

    # 生徒吹き出し (青・右寄せ)
    bubble_r = phone_x + phone_w - 60
    draw.rounded_rectangle([phone_x + 220, phone_y + 180, bubble_r, phone_y + 360],
                           radius=28, fill=(99, 102, 241))
    f_msg = font(FONT_BOLD, 32)
    draw.text((phone_x + 260, phone_y + 210), "二次関数の頂点の", font=f_msg, fill=TEXT)
    draw.text((phone_x + 260, phone_y + 255), "求め方がわからない...", font=f_msg, fill=TEXT)
    draw.text((phone_x + 260, phone_y + 310), "23:47 PM", font=font(FONT_REGULAR, 22), fill=(200, 200, 255))

    # AI吹き出し (パネル・左寄せ)
    draw.rounded_rectangle([phone_x + 60, phone_y + 420, phone_x + phone_w - 100, phone_y + 900],
                           radius=28, fill=(40, 40, 70))
    # AI アイコン
    draw.ellipse([phone_x + 80, phone_y + 440, phone_x + 160, phone_y + 520], fill=ACCENT)
    draw.text((phone_x + 100, phone_y + 455), "AI", font=font(FONT_BLACK, 40), fill=(255, 255, 255))
    f_ans = font(FONT_BOLD, 30)
    lines = [
        "頂点は「平方完成」で求めます",
        "",
        "y = 2x² − 8x + 3 なら",
        "y = 2(x² − 4x) + 3",
        "y = 2(x−2)² − 5",
        "",
        "→ 頂点 (2, −5)",
        "",
        "具体例で練習してみましょう",
    ]
    for i, l in enumerate(lines):
        draw.text((phone_x + 200, phone_y + 455 + i * 48), l, font=f_ans, fill=TEXT)

    # 送信中...風のアニメーション代わりに「✨解説中」
    draw.text((phone_x + 60, phone_y + 950), "解説: 即時回答（平均2秒）", font=font(FONT_BOLD, 28), fill=SUCCESS)

    img.save(out_path, "PNG")
    return img


def scene_app_textbook(out_path):
    """25-34s: 教材生成画面"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 48)
    f_head = font(FONT_BLACK, 62)

    center_text(draw, "機能②  AI教材自動生成", f_brand, 120, PRIMARY_LIGHT)
    grad_text(img, "弱点に合わせて自動作成", f_head, (90, 200), GRAD_T1, GRAD_T2)

    phone_x, phone_y, phone_w, phone_h = 100, 380, W - 200, 1320
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([phone_x, phone_y, phone_x + phone_w, phone_y + phone_h],
                           radius=48, fill=PANEL, outline=(60, 60, 100), width=3)

    # ヘッダー
    draw.text((phone_x + 50, phone_y + 50), "AI 教材ジェネレーター", font=font(FONT_BOLD, 38), fill=TEXT)

    # 入力欄風
    draw.rounded_rectangle([phone_x + 50, phone_y + 150, phone_x + phone_w - 50, phone_y + 320],
                           radius=20, fill=(30, 30, 60))
    draw.text((phone_x + 80, phone_y + 170), "弱点単元:", font=font(FONT_BOLD, 32), fill=TEXT_DIM)
    draw.text((phone_x + 80, phone_y + 220), "✓ 2次関数の最大最小", font=font(FONT_BOLD, 34), fill=TEXT)
    draw.text((phone_x + 80, phone_y + 270), "✓ 絶対値を含む方程式", font=font(FONT_BOLD, 34), fill=TEXT)

    # 生成ボタン
    draw.rounded_rectangle([phone_x + 50, phone_y + 360, phone_x + phone_w - 50, phone_y + 450],
                           radius=18, fill=PRIMARY)
    btn_text = "オリジナル問題を10問生成"
    bbox = draw.textbbox((0, 0), btn_text, font=font(FONT_BOLD, 32))
    bw = bbox[2] - bbox[0]
    draw.text((phone_x + (phone_w - bw) // 2, phone_y + 388), btn_text, font=font(FONT_BOLD, 32), fill=TEXT)

    # 生成結果カード x 3
    results_y = phone_y + 510
    results = [
        ("問題 1", "放物線 y = −x²+4x+3 の頂点を求めよ", "難易度: ★★☆"),
        ("問題 2", "|x−3| + |x+1| = 6 を解け", "難易度: ★★★"),
        ("問題 3", "x²+ax+1=0 の判別式を求めよ", "難易度: ★★☆"),
    ]
    for i, (num, content, diff) in enumerate(results):
        ry = results_y + i * 200
        draw.rounded_rectangle([phone_x + 40, ry, phone_x + phone_w - 40, ry + 170],
                               radius=16, fill=(30, 30, 60), outline=PRIMARY, width=2)
        draw.text((phone_x + 70, ry + 20), num, font=font(FONT_BLACK, 32), fill=PRIMARY_LIGHT)
        draw.text((phone_x + 70, ry + 65), content, font=font(FONT_BOLD, 28), fill=TEXT)
        draw.text((phone_x + 70, ry + 115), diff, font=font(FONT_REGULAR, 26), fill=WARNING)

    # 下部バッジ
    draw.text((phone_x + 60, phone_y + phone_h - 80), "Claude Opus 4.7 搭載",
              font=font(FONT_BOLD, 32), fill=ACCENT)

    img.save(out_path, "PNG")
    return img


def scene_app_report(out_path):
    """34-43s: 保護者レポート"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_brand = font(FONT_BOLD, 48)
    f_head = font(FONT_BLACK, 62)

    center_text(draw, "機能③  週次保護者レポート", f_brand, 120, PRIMARY_LIGHT)
    grad_text(img, "毎週日曜に自動配信", f_head, (180, 200), GRAD_T1, GRAD_T2)

    phone_x, phone_y, phone_w, phone_h = 100, 380, W - 200, 1320
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([phone_x, phone_y, phone_x + phone_w, phone_y + phone_h],
                           radius=48, fill=PANEL, outline=(60, 60, 100), width=3)

    # メール風ヘッダー
    draw.rounded_rectangle([phone_x + 20, phone_y + 20, phone_x + phone_w - 20, phone_y + 160],
                           radius=24, fill=(30, 30, 60))
    draw.text((phone_x + 50, phone_y + 40), "保護者さま宛メール", font=font(FONT_BOLD, 32), fill=TEXT)
    draw.text((phone_x + 50, phone_y + 85), "件名: 【週次レポート】今週の学習状況", font=font(FONT_BOLD, 28), fill=TEXT_DIM)
    draw.text((phone_x + 50, phone_y + 120), "2026/04/26 日曜 20:00 自動送信", font=font(FONT_REGULAR, 24), fill=TEXT_MUTED)

    # KPI 4つ
    kpi_y = phone_y + 200
    kpis = [
        ("時", "14.5h", "今週の学習時間"),
        ("%", "78%", "平均正答率"),
        ("Q", "47回", "AI質問数"),
        ("★", "3/5", "週次目標達成"),
    ]
    col_w = (phone_w - 90) // 2
    for i, (icon, num, label) in enumerate(kpis):
        col = i % 2
        row = i // 2
        cx = phone_x + 30 + col * (col_w + 30)
        cy = kpi_y + row * 220
        draw.rounded_rectangle([cx, cy, cx + col_w, cy + 200], radius=20,
                               fill=(30, 30, 60), outline=PRIMARY, width=2)
        draw.text((cx + 30, cy + 20), icon, font=font(FONT_BLACK, 50), fill=TEXT)
        grad_text(img, num, font(FONT_BLACK, 58), (cx + 30, cy + 80), GRAD_P1, GRAD_P2)
        draw = ImageDraw.Draw(img)
        draw.text((cx + 30, cy + 155), label, font=font(FONT_BOLD, 24), fill=TEXT_DIM)

    # コメント欄
    comment_y = phone_y + 680
    draw.rounded_rectangle([phone_x + 40, comment_y, phone_x + phone_w - 40, comment_y + 380],
                           radius=20, fill=(30, 30, 60))
    draw.text((phone_x + 60, comment_y + 20), "AIコーチからのコメント",
              font=font(FONT_BOLD, 30), fill=PRIMARY_LIGHT)
    comment_lines = [
        "今週は数学に集中して取り組まれました。",
        "苦手だった「2次関数の頂点」は改善傾向。",
        "来週は同じ単元の応用問題に進むのが",
        "理想的なペースです。",
        "",
        "保護者さまが褒めてあげる機会を",
        "ぜひお作りください。",
    ]
    for i, l in enumerate(comment_lines):
        draw.text((phone_x + 60, comment_y + 80 + i * 40), l, font=font(FONT_BOLD, 26), fill=TEXT)

    img.save(out_path, "PNG")
    return img


def scene_price_comparison(out_path):
    """43-50s: 価格比較"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_title = font(FONT_BLACK, 95)

    center_text(draw, "この全部を、", f_title, 250, TEXT)
    grad_text(img, "15分の1の価格で。", f_title, (100, 380), GRAD_T1, GRAD_T2)

    # 2ボックス比較
    draw = ImageDraw.Draw(img)
    box_y = 680
    box_h = 650
    col_w = (W - 200 - 40) // 2

    # 普通の塾
    draw.rounded_rectangle([100, box_y, 100 + col_w, box_y + box_h], radius=32,
                           fill=(40, 40, 60), outline=(80, 80, 110), width=3)
    draw.text((120, box_y + 40), "普通の塾", font=font(FONT_BOLD, 36), fill=TEXT_MUTED)
    draw.text((120, box_y + 140), "¥30,000+", font=font(FONT_BLACK, 72), fill=TEXT_DIM)
    bullets = ["週2〜3回のみ", "月1の紙レポ", "深夜質問不可"]
    for i, b in enumerate(bullets):
        draw.text((120, box_y + 290 + i * 80), "• " + b, font=font(FONT_BOLD, 30), fill=TEXT_MUTED)

    # AI塾 (強調)
    x2 = 100 + col_w + 40
    draw.rounded_rectangle([x2, box_y, x2 + col_w, box_y + box_h], radius=32,
                           fill=(50, 50, 100), outline=PRIMARY_LIGHT, width=5)
    draw.text((x2 + 20, box_y + 40), "AI学習コーチ塾", font=font(FONT_BOLD, 32), fill=PRIMARY_LIGHT)
    grad_text(img, "¥1,980", font(FONT_BLACK, 80), (x2 + 20, box_y + 140), GRAD_P1, GRAD_P2)
    draw = ImageDraw.Draw(img)
    bullets2 = ["24時間対応", "毎週自動レポ", "無制限質問"]
    for i, b in enumerate(bullets2):
        draw.text((x2 + 20, box_y + 290 + i * 80), "✓ " + b, font=font(FONT_BOLD, 30), fill=TEXT)

    # 下部バッジ
    draw = ImageDraw.Draw(img)
    center_text(draw, "※ 初月は体験¥1,980、継続は月¥24,980〜", font(FONT_BOLD, 28), 1430, TEXT_MUTED)

    img.save(out_path, "PNG")
    return img


def scene_urgency(out_path):
    """50-55s: 100名限定"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_top = font(FONT_BOLD, 60)
    f_huge = font(FONT_BLACK, 400)
    f_sub = font(FONT_BOLD, 64)

    center_text(draw, "第1期生", f_top, 300, WARNING)

    # 巨大な 100
    grad_text(img, "100", f_huge, (100, 500), GRAD_P1, GRAD_P2)

    # 100 の右に "名限定"
    draw = ImageDraw.Draw(img)
    center_text(draw, "名限定", f_sub, 950, TEXT)

    # 進捗バー
    bar_x, bar_y, bar_w, bar_h = 150, 1200, W - 300, 60
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=30,
                           fill=(40, 40, 60))
    # 既に使ってる人数(仮): 0なので ほぼ空
    draw.rounded_rectangle([bar_x, bar_y, bar_x + 30, bar_y + bar_h], radius=30,
                           fill=SUCCESS)
    center_text(draw, "募集開始しました。早い者勝ちです。", f_top, 1330, TEXT)

    img.save(out_path, "PNG")
    return img


def scene_cta(out_path):
    """55-60s: 最後のCTA"""
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    f_top = font(FONT_BOLD, 54)
    f_big = font(FONT_BLACK, 130)
    f_price = font(FONT_BLACK, 180)
    f_cta = font(FONT_BLACK, 70)
    f_foot = font(FONT_BOLD, 38)

    center_text(draw, "まずは3日間、", f_top, 300, TEXT_DIM)

    grad_text(img, "¥1,980で体験", f_big, (90, 420), GRAD_T1, GRAD_T2)

    draw = ImageDraw.Draw(img)
    center_text(draw, "自動課金なし。気に入ったら継続を。", f_top, 680, TEXT)

    # CTAボックス
    box_y = 1000
    box_h = 200
    draw.rounded_rectangle([100, box_y, W - 100, box_y + box_h], radius=50, fill=PRIMARY)
    bbox = draw.textbbox((0, 0), "trillion-ai-juku.com", font=f_cta)
    bw = bbox[2] - bbox[0]
    draw.text(((W - bw) // 2, box_y + 60), "trillion-ai-juku.com", font=f_cta, fill=TEXT)

    center_text(draw, "— プロフィールのリンクから —", f_foot, box_y + box_h + 100, PRIMARY_LIGHT)

    # ロゴ
    center_text(draw, "AI学習コーチ塾", font(FONT_BLACK, 52), 1600, TEXT)

    img.save(out_path, "PNG")
    return img


# ==============================================================
# Main: frames + ffmpeg
# ==============================================================

def main():
    # Clean frames dir
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR)

    # Scene list: (duration_sec, builder_func)
    scenes = [
        (3, scene_hook),
        (5, scene_problem_intro),
        (7, scene_problem_list),
        (10, scene_app_chat),
        (9, scene_app_textbook),
        (9, scene_app_report),
        (7, scene_price_comparison),
        (5, scene_urgency),
        (5, scene_cta),
    ]
    total = sum(s[0] for s in scenes)
    print(f"Total duration: {total}s (target: 60s)")

    # Generate one still image per scene
    scene_files = []
    for i, (dur, fn) in enumerate(scenes, 1):
        out = os.path.join(FRAMES_DIR, f"scene-{i:02d}.png")
        fn(out)
        scene_files.append((out, dur))
        print(f"  ✓ Scene {i}: {out} ({dur}s)")

    # Build ffmpeg concat file (ffmpeg needs duration per image)
    concat_path = os.path.join(FRAMES_DIR, "concat.txt")
    with open(concat_path, "w") as f:
        for img, dur in scene_files:
            f.write(f"file '{img}'\n")
            f.write(f"duration {dur}\n")
        # 最後のファイルを再度書く (ffmpeg仕様)
        f.write(f"file '{scene_files[-1][0]}'\n")

    # ffmpeg 実行: concat → mp4 (H.264 yuv420p 30fps)
    out_mp4 = os.path.join(OUT_DIR, "reels-60sec.mp4")
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
        print("FFmpeg stderr (tail):\n", result.stderr[-2000:])
        raise RuntimeError("ffmpeg failed")
    print(f"\n✅ Video generated: {out_mp4}")
    size_kb = os.path.getsize(out_mp4) // 1024
    print(f"   Size: {size_kb} KB")


if __name__ == "__main__":
    main()
