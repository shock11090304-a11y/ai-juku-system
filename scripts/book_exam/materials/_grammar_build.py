#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英文法 演習シリーズ共通の組み立て (kateiho2/build_kateiho2.py の型の共通化)。

各冊子の build_*.py が QUESTIONS (**唯一の正典**) を持ち、ここの run() を呼んで
取り込み JSON と問題 PDF を**同じデータから同時に**生成する。「画面の第3問と
冊子の第3問が違う」というずれは構造的に起きない。

★ ここは書式の器だけ。設問の中身 (英文・選択肢・解説) は各 build_*.py が持つ。
★ verify() が落とす形 — どれも採点崩れ・解説崩れに直結する:
    ・正解位置の偏り (各番号 2〜3 回、同じ番号の 3 連続) … 勘で当たる冊子になる
    ・解説 4 セクション (コアイメージ → 文構造分析 → 正解の根拠 → 誤答 NG 理由) の欠け
    ・誤答 NG 理由の番号と選択肢のずれ (正解を NG に載せる / 誤答の説明が欠ける)
    ・空所 "(          )" の無い設問文 / 選択肢の重複
★ 先頭 `_` はゲートランナーの対象外 (共有ライブラリの慣習)。コミット済み JSON の
  検査は隣の check_grammar_books.py が CI で回す。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HEADINGS = ("## 🎯 コアイメージ", "## 🔬 文構造分析",
            "## 📍 正解の根拠", "## ❌ 誤答 NG 理由")
BLANK = re.compile(r"\(\s{6,}\)")          # 設問文の空所 "(          )"


def verify(questions):
    """QUESTIONS を機械で確かめる。@returns エラー文の一覧 (空なら合格)。"""
    errs = []
    for i, (no, page, stem, choices, ans, pts, tag, exp) in enumerate(questions):
        at = f"第{no}問"
        if no != i + 1:
            errs.append(f"{at}: 番号が飛んでいる (期待 {i + 1})")
        if not (isinstance(page, int) and page >= 1):
            errs.append(f"{at}: page が 1 以上の整数でない")
        if i and page < questions[i - 1][1]:
            errs.append(f"{at}: page が前の設問より戻っている")
        if not BLANK.search(stem):
            errs.append(f"{at}: 設問文に空所 \"(          )\" が無い")
        if len(choices) != 4:
            errs.append(f"{at}: 選択肢が 4 つでない ({len(choices)})")
        if len(set(choices)) != len(choices):
            errs.append(f"{at}: 選択肢に同じものが混ざっている")
        if not (isinstance(ans, int) and 1 <= ans <= 4):
            errs.append(f"{at}: 正解番号が 1〜4 でない ({ans})")
            continue
        if not (isinstance(pts, int) and pts >= 1):
            errs.append(f"{at}: 配点が 1 以上の整数でない")
        if not re.fullmatch(r"[A-Z0-9]+-[A-Z0-9]+", tag or ""):
            errs.append(f"{at}: unit_tag の形が崩れている ({tag!r})")
        # --- 解説: 4 セクションが順番どおりに 1 回ずつ ---------------------
        pos = -1
        for h in HEADINGS:
            p = exp.find(h)
            if p < 0:
                errs.append(f"{at}: 解説に「{h}」が無い")
            elif exp.count(h) > 1:
                errs.append(f"{at}: 解説に「{h}」が 2 回以上ある")
            elif p < pos:
                errs.append(f"{at}: 解説のセクションの順番が崩れている ({h})")
            else:
                pos = p
        # --- 誤答 NG 理由: 番号と選択肢の文字列まで突き合わせる -------------
        ng = exp.split(HEADINGS[3])[-1]
        for n in range(1, 5):
            line = next((ln.strip() for ln in ng.splitlines()
                         if ln.strip().startswith(f"{n}.")), None)
            if n == ans:
                if line:
                    errs.append(f"{at}: 正解 {n} が誤答 NG 理由に載っている")
            elif line is None:
                errs.append(f"{at}: 誤答 {n} の NG 理由が無い")
            elif not line.startswith(f"{n}. {choices[n - 1]}"):
                errs.append(f"{at}: NG 理由 {n} の語が選択肢と違う "
                            f"(期待 {choices[n - 1]!r})")
    # --- 正解位置の配り: 各番号 2〜3 回・同じ番号の 3 連続なし ---------------
    seq = [q[4] for q in questions]
    dist = {k: seq.count(k) for k in (1, 2, 3, 4)}
    if len(questions) == 10 and not all(2 <= dist[k] <= 3 for k in dist):
        errs.append(f"正解位置が偏っている: {dist}")
    for i in range(len(seq) - 2):
        if seq[i] == seq[i + 1] == seq[i + 2]:
            errs.append(f"正解番号 {seq[i]} が第{i + 1}問から 3 連続している")
    return errs


CSS = """
@page { size: A4; margin: 18mm 16mm; }
/* ★ IPA を必ず並べる。日本語フォントが 1 つも当たらないと Chrome は
      中国語フォント (WenQuanYi) に落ち、字形が中国語になったまま刷れてしまう。 */
body { font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "YuGothic",
       "IPAexGothic", "IPAPGothic", "IPAGothic",
       "Noto Sans CJK JP", "Noto Sans JP", sans-serif;
       color: #111; font-size: 11.5pt; line-height: 1.85; }
.head { border-bottom: 2px solid #111; padding-bottom: 6px; margin-bottom: 22px; }
.head h1 { font-size: 16pt; margin: 0 0 2px; }
.head .meta { font-size: 9.5pt; color: #555; }
.q { margin-bottom: 30px; page-break-inside: avoid; }
.q .no { font-weight: 700; font-size: 11pt; }
.q .pt { font-size: 9pt; color: #666; margin-left: 8px; font-weight: 400; }
.q .stem { margin: 4px 0 8px; }
ol.ch { list-style: none; padding-left: 14px; margin: 0; }
ol.ch li { margin: 2px 0; }
ol.ch .n { display: inline-block; width: 1.9em; font-weight: 600; }
.pagebreak { page-break-after: always; }
"""


def render_question(no, stem, choices, pts):
    html = [f'<div class="q"><div class="no">第{no}問<span class="pt">（{pts}点）</span></div>',
            f'<div class="stem">{stem}</div>', '<ol class="ch">']
    for i, c in enumerate(choices, 1):
        html.append(f'<li><span class="n">{i}.</span>{c}</li>')
    html.append("</ol></div>")
    return "".join(html)


def build_html(title, level, time_limit_min, questions):
    total = sum(q[5] for q in questions)
    pages = {}
    for no, page, stem, choices, _ans, pts, _tag, _exp in questions:
        pages.setdefault(page, []).append(render_question(no, stem, choices, pts))
    body = []
    for idx, page in enumerate(sorted(pages)):
        if idx == 0:
            body.append(f'<div class="head"><h1>{title}</h1>'
                        f'<div class="meta">{level} / 全{len(questions)}問 {total}点 / '
                        f'制限時間 {time_limit_min} 分'
                        f' — 解答は別画面の答案に入力してください</div></div>')
        else:
            body.append(f'<div class="head"><h1>{title}'
                        f'<span style="font-size:10pt;font-weight:400"> — {page} ページ目'
                        f'</span></h1></div>')
        body.extend(pages[page])
        if idx < len(pages) - 1:
            body.append('<div class="pagebreak"></div>')
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{title}</title><style>{CSS}</style></head>'
            f'<body>{"".join(body)}</body></html>')


def build_json(stem, title, level, time_limit_min, questions):
    """import_books.py が読む bundle。source の stem が PDF 名と一致する。"""
    return {
        "source": f"{stem}.yaml",
        "subject_name": "英語",
        "book": {"title": title, "subject": "grammar", "level": level,
                 "time_limit_min": time_limit_min},
        "questions": [
            {"number": no, "page": page, "answer_type": "choice", "choice_count": 4,
             "correct_answer": str(ans), "points": pts, "unit_tag": tag,
             "explanation": exp}
            for no, page, _stem, _choices, ans, pts, tag, exp in questions
        ],
    }


def find_chrome():
    for c in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    for root in ("/opt/pw-browsers",):
        if os.path.isdir(root):
            direct = os.path.join(root, "chromium")
            if os.path.exists(direct):
                return direct
            for d in sorted(os.listdir(root), reverse=True):
                p = os.path.join(root, d, "chrome-linux", "chrome")
                if os.path.exists(p):
                    return p
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if os.path.exists(mac) else None


def run(here, stem, title, level, time_limit_min, questions):
    errs = verify(questions)
    if errs:
        for e in errs:
            print(f"✗ {e}")
        return 1

    out_json = os.path.join(here, f"{stem}.json")
    out_pdf = os.path.join(here, f"{stem}_問題.pdf")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(build_json(stem, title, level, time_limit_min, questions),
                  f, ensure_ascii=False, indent=1)
    print(f"[ok] {os.path.basename(out_json)} ({len(questions)} 問)")

    chrome = find_chrome()
    if not chrome:
        print("✗ Chrome / Chromium が見つからない。PDF を作れない。")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "book.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(build_html(title, level, time_limit_min, questions))
        cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox",
               "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}", "file://" + src]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode or not os.path.exists(out_pdf):
            print("✗ print-to-pdf が失敗:", (r.stderr or r.stdout)[-400:])
            return 1
    print(f"[ok] {os.path.basename(out_pdf)} ({os.path.getsize(out_pdf) // 1024} KB)")
    return 0
