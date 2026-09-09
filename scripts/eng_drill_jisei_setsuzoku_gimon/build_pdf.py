# -*- coding: utf-8 -*-
"""同じ正典から、印刷・LINE 配布用の PDF を 2 冊刷る。

    python3 scripts/eng_drill_jisei_setsuzoku_gimon/build_pdf.py
    STUDENT_NAME="姓 名" python3 ... build_pdf.py     # 宛名入り (省略時は氏名欄が空欄)

出力 (どちらも .gitignore 対象 = リポジトリには入らない):
    英文法練習_時制接続詞疑問_問題.pdf        … 90問 + 解答記入欄
    英文法練習_時制接続詞疑問_解答解説.pdf    … 正解一覧 + 全問の解説

★アプリのドリルと**同じ build.build() の出力**から刷る。選択肢の並びも正解番号も
  一致するので、「アプリの第3問と紙の第3問が違う」というずれは構造的に起きない。
★宛名はコードに書かない (このリポジトリは公開)。刷るときだけ STUDENT_NAME で渡す。
★刷り上がりの照合は check_pdf.py。build しただけで配らないこと。
"""
import html
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build    # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
PDF_Q = os.path.join(BASE, "英文法練習_時制接続詞疑問_問題.pdf")
PDF_A = os.path.join(BASE, "英文法練習_時制接続詞疑問_解答解説.pdf")
BLANK = "(   )"
MARU = "①②③④"
LEVEL_JA = {"basic": "基礎", "standard": "標準", "advanced": "やや難"}

# ★日本語フォントを必ず名指しする。総称の sans-serif だけだと、この環境では
#   fontconfig が中国語フォント (WenQuanYi) を選び、字形が中国語字体になる (実測)。
FONT = ('"Noto Sans CJK JP", "Noto Sans JP", "Hiragino Kaku Gothic ProN", '
        '"Yu Gothic", "IPAPGothic", "IPAGothic", sans-serif')

CSS = f"""
@page {{ size: A4; margin: 16mm 14mm 14mm; }}
body {{ font-family: {FONT}; color: #111; font-size: 10.5pt; line-height: 1.7; margin: 0; }}
.head {{ border-bottom: 2.5px solid #111; padding-bottom: 6px; margin-bottom: 12px; }}
.head h1 {{ font-size: 15pt; margin: 0 0 3px; letter-spacing: 0.02em; }}
.head .meta {{ font-size: 9pt; color: #444; }}
.namebox {{ float: right; font-size: 9pt; color: #444; border: 1px solid #999;
           padding: 3px 10px; border-radius: 4px; }}
.lead {{ font-size: 9.5pt; background: #f2f4f7; border-left: 3px solid #555;
        padding: 6px 10px; margin: 0 0 14px; }}
h2.unit {{ font-size: 12pt; margin: 16px 0 6px; padding: 3px 8px;
          background: #111; color: #fff; border-radius: 3px; page-break-after: avoid; }}
h3.lv {{ font-size: 10pt; margin: 10px 0 4px; color: #333; border-bottom: 1px dotted #999;
        page-break-after: avoid; }}
.q {{ margin: 0 0 9px; page-break-inside: avoid; }}
.q .stem {{ margin: 0 0 2px; }}
.q .no {{ font-weight: 700; margin-right: 5px; }}
.ch {{ display: flex; flex-wrap: wrap; margin-left: 1.9em; font-size: 10pt; }}
.ch span {{ width: 50%; box-sizing: border-box; padding-right: 6px; }}
.en {{ font-family: "Times New Roman", serif; font-size: 11pt; }}
.pagebreak {{ page-break-after: always; }}
table.ans {{ border-collapse: collapse; font-size: 9.5pt; width: 100%; }}
table.ans td, table.ans th {{ border: 1px solid #888; padding: 3px 2px; text-align: center; }}
table.ans th {{ background: #eee; width: 3.2em; }}
.a-item {{ margin: 0 0 11px; page-break-inside: avoid; }}
.a-item .line1 {{ font-weight: 700; }}
.a-item .full {{ margin: 1px 0; }}
.a-item .exp {{ font-size: 9.5pt; color: #222; margin-top: 1px; }}
.tag {{ font-size: 8.5pt; color: #666; font-weight: 400; margin-left: 6px; }}
"""


def esc(s):
    return html.escape(s, quote=False)


def stem_html(stem):
    """空所を下線に置き換えて印刷用にする。英文は明朝で組んで日本語と見分けやすくする。"""
    return ('<span class="en">'
            + esc(stem).replace(esc(BLANK), '<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>')
            + '</span>')


def filled(stem, answer):
    """空所に正解を入れた完成文 (解説編に載せる)。"""
    return stem.replace(BLANK, answer)


def group(rows):
    """(単元, レベル) の順に並べ直さず、正典の並び (単元→レベル) のまま区切りを返す。"""
    out, cur = [], None
    for i, r in enumerate(rows):
        key = (r["unit"], r["level"])
        if key != cur:
            out.append((key, []))
            cur = key
        out[-1][1].append((i + 1, r))
    return out


def page_questions(rows, student):
    body = [f'<div class="head"><div class="namebox">氏名 {esc(student) or "&nbsp;" * 14}'
            f'　/　日付 &nbsp;&nbsp;&nbsp;&nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;</div>'
            f'<h1>英文法 練習問題 — 時制 / 接続詞 / 疑問詞・間接疑問</h1>'
            f'<div class="meta">全{len(rows)}問・4択　各単元 基礎 / 標準 / やや難</div></div>',
            '<p class="lead">各問、空所に入れるのに最も適切なものを ①〜④ から1つ選びなさい。'
            '答えは最後のページの解答欄に記入すること。</p>']
    last_unit = None
    for (unit, level), items in group(rows):
        if unit != last_unit:
            body.append(f'<h2 class="unit">{esc(unit)}</h2>')
            last_unit = unit
        body.append(f'<h3 class="lv">{LEVEL_JA.get(level, level)}</h3>')
        for no, r in items:
            body.append(f'<div class="q"><div class="stem"><span class="no">{no}.</span>'
                        f'{stem_html(r["stem"])}</div><div class="ch">'
                        + "".join(f'<span>{MARU[i]} <span class="en">{esc(c)}</span></span>'
                                  for i, c in enumerate(r["choices"]))
                        + '</div></div>')
    # --- 解答欄 (自分で答え合わせできるように問題編の最後に付ける)
    body.append('<div class="pagebreak"></div>'
                '<div class="head"><h1>解答欄</h1>'
                '<div class="meta">選んだ番号 (1〜4) を書き入れてください。</div></div>')
    cells = []
    for start in range(0, len(rows), 10):
        nums = range(start + 1, min(start + 10, len(rows)) + 1)
        cells.append("<tr><th>問</th>" + "".join(f"<th>{n}</th>" for n in nums) + "</tr>")
        cells.append("<tr><th>答</th>" + "<td>&nbsp;</td>" * len(list(nums)) + "</tr>")
    body.append('<table class="ans">' + "".join(cells) + "</table>")
    return "".join(body)


def page_answers(rows, student):
    body = [f'<div class="head"><div class="namebox">氏名 {esc(student) or "&nbsp;" * 14}</div>'
            f'<h1>英文法 練習問題 — 解答・解説</h1>'
            f'<div class="meta">時制 / 接続詞 / 疑問詞・間接疑問　全{len(rows)}問</div></div>']
    cells = []
    for start in range(0, len(rows), 10):
        pair = [(n, rows[n - 1]) for n in range(start + 1, min(start + 10, len(rows)) + 1)]
        cells.append("<tr><th>問</th>" + "".join(f"<th>{n}</th>" for n, _ in pair) + "</tr>")
        cells.append("<tr><th>答</th>" + "".join(f"<td>{r['answer'] + 1}</td>" for _, r in pair) + "</tr>")
    body.append('<table class="ans">' + "".join(cells) + "</table>")
    body.append('<div class="pagebreak"></div>')

    last_unit = None
    for (unit, level), items in group(rows):
        if unit != last_unit:
            body.append(f'<h2 class="unit">{esc(unit)}</h2>')
            last_unit = unit
        body.append(f'<h3 class="lv">{LEVEL_JA.get(level, level)}</h3>')
        for no, r in items:
            ans = r["choices"][r["answer"]]
            body.append(
                f'<div class="a-item"><div class="line1">{no}. 正解 {MARU[r["answer"]]} '
                f'<span class="en">{esc(ans)}</span>'
                f'<span class="tag">{esc(r["unit"])} / {LEVEL_JA.get(r["level"], r["level"])}</span></div>'
                f'<div class="full en">{esc(filled(r["stem"], ans))}</div>'
                f'<div class="exp">{esc(r["explanation"])}</div></div>')
    return "".join(body)


def find_chrome():
    for c in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    root = "/opt/pw-browsers"
    if os.path.isdir(root):
        for d in sorted(os.listdir(root), reverse=True):
            p = os.path.join(root, d, "chrome-linux", "chrome")
            if os.path.exists(p):
                return p
        direct = os.path.join(root, "chromium")
        if os.path.exists(direct):
            return direct
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if os.path.exists(mac) else None


def to_pdf(chrome, title, inner, out_pdf):
    doc = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
           f'<title>{esc(title)}</title><style>{CSS}</style></head><body>{inner}</body></html>')
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "sheet.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(doc)
        r = subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                            "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}",
                            "file://" + src],
                           capture_output=True, text=True, timeout=180)
    if r.returncode or not os.path.exists(out_pdf):
        print("印刷に失敗:", (r.stderr or r.stdout)[-400:])
        return False
    print(f"[ok] {os.path.basename(out_pdf)} ({os.path.getsize(out_pdf) // 1024} KB)")
    return True


def main():
    rows, _blind = build.build()
    ng = __import__("_rules").validate(rows, build.answers(),
                                       os.path.normpath(os.path.join(BASE, "..", "..")))
    if ng:
        print(f"違反 {len(ng)} 件 — 刷らない")
        for m in ng:
            print(" ", m)
        return 1
    student = os.environ.get("STUDENT_NAME", "").strip()
    chrome = find_chrome()
    if not chrome:
        print("Chrome / Chromium が見つからないので PDF を作れない")
        return 1
    ok = to_pdf(chrome, "英文法練習 問題", page_questions(rows, student), PDF_Q)
    ok = to_pdf(chrome, "英文法練習 解答解説", page_answers(rows, student), PDF_A) and ok
    if ok:
        print("★配る前に check_pdf.py で刷り上がりを照合すること")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
