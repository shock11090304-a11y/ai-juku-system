#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML → PNG を撮る所を 1 本にまとめた土台。

★ここが正典。build.py (1:1 カルーセル) と build_vol.py (4:5 vol シリーズ) の
  両方がこれを呼ぶ。撮り方 (device scale factor・背景・待ち時間) を片方だけ直すと
  同じブランドの画像で解像度や余白が食い違うので、書き写さないこと。

Chrome の在り処は環境で違う:
  - 塾長の Mac        : /Applications/Google Chrome.app/...
  - クラウド/CI (Linux): /opt/pw-browsers/chromium-*/chrome-linux/chrome
探索順は find_chrome() の CANDIDATES を見ること。`CHROME_BIN` を渡せば最優先で使う。
"""
import glob
import os
import shutil
import subprocess

# 環境変数で明示的に上書きできる (どの環境でも最優先)
ENV_VAR = "CHROME_BIN"


def _playwright_globs():
    """Playwright が入れた Chromium を探す。PLAYWRIGHT_BROWSERS_PATH が既定を上書きする。"""
    roots = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "/opt/pw-browsers",
             os.path.expanduser("~/.cache/ms-playwright")]
    pats = []
    for r in roots:
        pats += [
            os.path.join(r, "chromium-*/chrome-linux/chrome"),
            os.path.join(r, "chromium_headless_shell-*/chrome-linux/headless_shell"),
            os.path.join(r, "chromium/chrome-linux/chrome"),
            os.path.join(r, "chromium"),
        ]
    return pats


def find_chrome():
    """使える Chrome/Chromium の実行ファイルを返す。見つからなければ RuntimeError。"""
    env = os.environ.get(ENV_VAR)
    if env:
        if os.path.isfile(env) and os.access(env, os.X_OK):
            return env
        raise RuntimeError(f"{ENV_VAR}={env} が実行可能なファイルではない")

    for pat in _playwright_globs():
        for p in sorted(glob.glob(pat)):
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p

    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p

    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.isfile(mac):
        return mac

    raise RuntimeError(
        "Chrome/Chromium が見つからない。CHROME_BIN に実行ファイルのパスを渡すか、\n"
        "  macOS: Google Chrome をインストール\n"
        "  Linux: PLAYWRIGHT_BROWSERS_PATH 配下に chromium を置く"
    )


# ★--window-size の高さは「実際に描画される高さ」と一致しない。
#   Linux の headless Chromium (1194) では 87 CSS px 少なく描画され、
#   足りない分は地の色で埋められる = 版面の下端が丸ごと出ない。
#   macOS の Chrome では 0 だった。環境で違うので定数で持たず、実測して吸収する。
#
# ★★測れなかったときに 0 を返してはいけない。0 は「Mac では正しい値」なので、
#   「測れなかった」と「本当に 0」が区別できなくなる。実際に一度そう書いて、
#   Pillow が無い環境や較正が失敗した環境で**フッターの無い PNG を無言で納品する**
#   経路を作った (実寸は正しいので寸法検査も通ってしまう)。測れなければ必ず落とす。
_UI_OFFSET = {}


class CalibrationError(RuntimeError):
    pass


def _measure_ui_offset(chrome_bin, scale):
    """--window-size のうち描画されない高さ (CSS px) を実測して返す。

    測れなければ CalibrationError。**0 を返して誤魔化さない。**
    """
    if scale in _UI_OFFSET:
        return _UI_OFFSET[scale]
    try:
        from PIL import Image
    except ImportError as e:
        raise CalibrationError(
            "Pillow が要る (版面の下端が欠けていないかを較正するため)。"
            "python3 -m pip install Pillow") from e
    import tempfile
    ask_h = 1000
    d = tempfile.mkdtemp(prefix="chromecal-")
    hp, pp = os.path.join(d, "cal.html"), os.path.join(d, "cal.png")
    with open(hp, "w", encoding="utf-8") as f:
        f.write('<!doctype html><html><head><meta charset=utf-8><style>'
                '*{margin:0;padding:0}html{background:#ff0000}'
                '</style></head><body>'
                '<div style="height:4000px;background:#00ff00"></div></body></html>')
    r = subprocess.run(_argv(chrome_bin, hp, pp, 400, ask_h, scale),
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60)
    if not os.path.exists(pp):
        err = (r.stderr or b"").decode("utf-8", "replace")[-400:]
        raise CalibrationError(
            f"較正のスクリーンショットが撮れなかった (exit={r.returncode})\n"
            f"  chrome={chrome_bin}\n{err}")
    im = Image.open(pp).convert("RGB")
    px, (w, h) = im.load(), im.size
    drawn = 0
    for y in range(h):
        if px[w // 2, y] != (0, 255, 0):
            break
        drawn = y + 1
    if drawn == 0:
        raise CalibrationError(
            "較正の画像が全面 緑ではない = 何も描画できていない。"
            f"chrome={chrome_bin}")
    off = max(0, ask_h - drawn // scale)
    if off >= ask_h // 2:
        raise CalibrationError(
            f"較正の結果が異常 (描画されたのは {drawn // scale}/{ask_h} CSSpx)。"
            f"chrome={chrome_bin}")
    _UI_OFFSET[scale] = off
    return off


def _argv(chrome_bin, html_path, png_path, width, height, scale):
    return [
        chrome_bin, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none",
        f"--force-device-scale-factor={scale}",
        f"--window-size={width},{height}",
        "--virtual-time-budget=2000",
        f"--screenshot={png_path}", "file://" + os.path.abspath(html_path),
    ]


def shot(html_path, png_path, width, height, scale=2, timeout=120):
    """html_path を width x height の版面で撮って png_path に width*scale x height*scale で書く。

    ★終了コードだけでなく、PNG の存在・実寸・**下端が本当に描画されたか**まで見る。
      Chrome は 0 終了でも PNG を書かないことがあり、書けても下端が
      未描画のまま地の色で埋まっていることがある (実寸は正しいので気づけない)。
    """
    chrome = find_chrome()
    if os.path.exists(png_path):
        os.remove(png_path)
    off = _measure_ui_offset(chrome, scale)   # 測れなければここで落ちる
    r = subprocess.run(_argv(chrome, html_path, png_path, width, height + off, scale),
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout)
    if not os.path.exists(png_path):
        err = (r.stderr or b"").decode("utf-8", "replace")[-800:]
        raise RuntimeError(f"PNG が生成されなかった (exit={r.returncode})\n"
                           f"  chrome={chrome}\n  html={html_path}\n{err}")
    want = (width * scale, height * scale)
    from PIL import Image
    im = Image.open(png_path).convert("RGB")
    if im.size != want:
        im = im.crop((0, 0, *want))
        im.save(png_path)
    got = png_size(png_path)
    if got != want:
        raise RuntimeError(f"PNG の実寸が {got} — {want} でなければならない "
                           f"(--window-size のUI分オフセット={off}px)")
    return png_path


def png_size(path):
    """PNG の実寸を (w, h) で返す。Pillow なしで読めるように IHDR を直接見る。"""
    import struct
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"PNG ではない: {path}")
    return struct.unpack(">II", head[16:24])


if __name__ == "__main__":
    print(find_chrome())
