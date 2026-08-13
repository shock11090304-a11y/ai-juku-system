#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""動作確認用の問題冊子 PDF を作る。

    python3 supabase/demo/build_sample_pdf.py

出力: supabase/demo/sample-book.pdf (2 ページ / 5 問)

★ 出来上がった PDF も **コミットする**。デモは「Storage に上げた PDF を
  署名付き URL で配る」経路を確かめるためのもので、PDF が無いと何も始まらない。
  生成物だが実行時に要るファイルなので、ここでは .gitignore していない。

★ 設問の並びと配点は supabase/seed.sql と**一対一で対応している**。
  片方だけ直すと「PDF の第3問」と「答案の第3問」がずれる。両方直すこと。
  対応は下の QUESTIONS が正典で、seed.sql 側にも同じ番号・同じページを書いてある。

Chrome の print-to-pdf を使うのはこのリポジトリの他のビルダーと同じ作法。
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sample-book.pdf")

# (設問番号, ページ, 設問文, 選択肢 or None, 配点)
#   選択肢が None = 短答。番号は seed.sql の questions.number と一致させる。
QUESTIONS = [
    (1, 1, "If I (          ) you, I would accept that offer right away.",
     ["am", "was", "were", "will be"], 1),
    (2, 1, "If she had started ten minutes earlier, she (          ) the last train.",
     ["catches", "caught", "would catch", "would have caught"], 2),
    (3, 1, "I wish I (          ) speak French fluently."
     "<br><span class=\"note\">can を適切な形にして書きなさい。</span>", None, 2),
    (4, 2, "(          ) it not been for your advice, "
     "I would have made a serious mistake.",
     ["If", "Had", "Were", "Should"], 1),
    (5, 2, "If it (          ) tomorrow, we will go hiking."
     "<br><span class=\"note\">not rain を適切な形にして書きなさい。</span>", None, 2),
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Noto Sans CJK JP", "Noto Sans JP", "Hiragino Kaku Gothic ProN",
       "Yu Gothic", sans-serif; color: #111; font-size: 11.5pt; line-height: 1.85; }
.head { border-bottom: 2px solid #111; padding-bottom: 6px; margin-bottom: 22px; }
.head h1 { font-size: 16pt; margin: 0 0 2px; }
.head .meta { font-size: 9.5pt; color: #555; }
.q { margin-bottom: 26px; page-break-inside: avoid; }
.q .no { font-weight: 700; font-size: 11pt; }
.q .pt { font-size: 9pt; color: #666; margin-left: 8px; font-weight: 400; }
.q .stem { margin: 4px 0 8px; }
.q .note { font-size: 9.5pt; color: #555; }
ol.ch { list-style: none; padding-left: 14px; margin: 0; }
ol.ch li { margin: 2px 0; }
ol.ch .n { display: inline-block; width: 1.9em; font-weight: 600; }
.blank { border-bottom: 1px solid #444; display: inline-block; width: 60mm; height: 1.15em; }
.foot { position: fixed; bottom: 0; left: 0; right: 0; text-align: center;
        font-size: 8.5pt; color: #888; }
.pagebreak { page-break-after: always; }
"""


def render_question(no, stem, choices, pts):
    html = [f'<div class="q"><div class="no">第{no}問<span class="pt">（{pts}点）</span></div>',
            f'<div class="stem">{stem}</div>']
    if choices:
        html.append('<ol class="ch">')
        for i, c in enumerate(choices, 1):
            html.append(f'<li><span class="n">{i}.</span>{c}</li>')
        html.append("</ol>")
    else:
        html.append('<div><span class="blank"></span></div>')
    html.append("</div>")
    return "".join(html)


def build_html():
    pages = {}
    for no, page, stem, choices, pts in QUESTIONS:
        pages.setdefault(page, []).append(render_question(no, stem, choices, pts))

    body = []
    for idx, page in enumerate(sorted(pages)):
        if idx == 0:
            body.append('<div class="head"><h1>英文法 仮定法 演習5</h1>'
                        '<div class="meta">標準 / 全5問 8点 / 制限時間 10 分'
                        ' — 解答は別画面の答案に入力してください</div></div>')
        else:
            body.append(f'<div class="head"><h1>英文法 仮定法 演習5'
                        f'<span style="font-size:10pt;font-weight:400"> — {page} ページ目'
                        f'</span></h1></div>')
        body.extend(pages[page])
        if idx < len(pages) - 1:
            body.append('<div class="pagebreak"></div>')

    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>英文法 仮定法 演習5</title><style>{CSS}</style></head>'
            f'<body>{"".join(body)}</body></html>')


def find_chrome():
    for c in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    # Playwright 同梱 (この環境ではこちら)
    for root in ("/opt/pw-browsers",):
        if not os.path.isdir(root):
            continue
        for d in sorted(os.listdir(root), reverse=True):
            p = os.path.join(root, d, "chrome-linux", "chrome")
            if os.path.exists(p):
                return p
    mac = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    return mac if os.path.exists(mac) else None


def main():
    chrome = find_chrome()
    if not chrome:
        print("✗ Chrome / Chromium が見つからない。PDF を作れない。")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "book.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(build_html())
        cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox",
               "--no-pdf-header-footer", f"--print-to-pdf={OUT}", "file://" + src]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode or not os.path.exists(OUT):
            print("✗ print-to-pdf が失敗:", (r.stderr or r.stdout)[-400:])
            return 1

    size = os.path.getsize(OUT)
    print(f"[ok] {os.path.relpath(OUT, os.path.dirname(os.path.dirname(HERE)))} "
          f"({size // 1024} KB / 設問 {len(QUESTIONS)} 問)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
