#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""縦書きHTML(kokugo-nankan.html)を Chrome の --print-to-pdf で
縦書きのまま PDF 化する（kokugo-nankan.pdf）。

reportlab は縦書き(vertical-rl)を扱えないため、CSS で組んだ縦書きHTMLを
ブラウザ印刷でPDF化する方式に切り替えた。build_html.py を先に実行しておくこと。
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
HTML = os.path.join(REPO, "kokugo-nankan.html")
OUT = os.path.join(REPO, "kokugo-nankan.pdf")

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("Chrome/Chromium が見つかりません: " + ", ".join(CHROME_CANDIDATES))

def main():
    if not os.path.exists(HTML):
        raise SystemExit("先に build_html.py を実行してください: " + HTML)
    chrome = find_chrome()
    if os.path.exists(OUT):
        os.remove(OUT)
    cmd = [
        chrome, "--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        "--virtual-time-budget=6000",
        f"--print-to-pdf={OUT}",
        "file://" + HTML,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(OUT):
        sys.stderr.write(r.stdout + "\n" + r.stderr + "\n")
        # 旧フラグ名でリトライ
        cmd2 = [c for c in cmd if c != "--no-pdf-header-footer"]
        cmd2.insert(4, "--print-to-pdf-no-header")
        subprocess.run(cmd2, capture_output=True, text=True)
    if os.path.exists(OUT):
        print("WROTE", OUT, "|", os.path.getsize(OUT), "bytes")
    else:
        raise SystemExit("PDF 生成に失敗しました")

if __name__ == "__main__":
    main()
