#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テストの冊子を**教科を問わず**組む共通ビルダー (docs/kamitest-manual/ の実装)。

各冊子の build_*.py が META と QUESTIONS (**唯一の正典**) を持ち、ここの run() を呼んで
取り込み JSON と問題 PDF を**同じデータから同時に**生成する。
「画面の第3問と冊子の第3問が違う」というずれは構造的に起きない。

■ 英文法 15 冊の _grammar_build.py との関係
    あちらは英文法専用 (subject 固定・空所必須・4択固定・8 要素のタプル)。**触らない**。
    こちらは全教科向けで、設問を dict で持ち、choice / short・数式・本文・図に対応する。
    新しい冊子はこちらで書く。

■ ★ node は要らない
    数式は **Chrome の中で KaTeX (vendor/katex) が描く**。塾長の Mac に node は無いので、
    node を要求する経路 (kyotsu_mogi2026/build_pdf.py) は持ち込まない。
    Chrome は print-to-pdf でどのみち要る。

■ ★ 3 層の相互チェックを build に埋め込む (CLAUDE.md 2026-08-16)
    ① 出力物どうしの照合 — 刷り上がり PDF を**読み返して**、
       ・生の LaTeX (`$` `\\frac` `¥(`) が 1 つも残っていないこと
         (KaTeX が 1 つでも落ちると、その式は生ソースのまま印刷され、PDF 生成は成功する)
       ・全設問の「第N問」と、数式以外の文字列が**正典どおりのページに**在ること
    ② 機械検査 — verify() が正典を直接見る (§下)
    ③ 人手 — 正解の一意性は機械に見えない。全問を敵対的に読み直すこと

    PDF を読む道具 (pypdf / pymupdf) が無いときは **黙って飛ばさず落とす**。
    どうしても先へ進めたいときだけ `SKIP_PDF_VERIFY=1` を明示する (理由が印字される)。

■ verify() が落とす形 — どれも採点崩れ・解説崩れに直結する
    ・番号の飛び / ページの逆行 / 選択肢の重複 / 正解番号が範囲外
    ・記述の正解が数字だけ (取り込みが弾く形) / 記述に選択肢がある
    ・正解位置の偏り (各番号が均等 ±1 に収まらない) / 同じ番号の 3 連続
    ・教科ごとの解説見出しの欠け・順番違い (SUBJECT_HEADINGS)
    ・誤答を潰す節の番号と選択肢のずれ (正解を誤答に載せる / 誤答の説明が欠ける)
      ★ 選択肢が数式のときは、設問に choices_plain (素の表記) を持たせる。
        解説に LaTeX は書けない (画面が素のテキスト表示) ので、照合はそちらで行う。
    ・解説に生の LaTeX (画面は素のテキスト表示なのでそのまま出てしまう)
    ・記述の正解が冊子の別の場所に印字されている (解答漏洩)

★ 先頭 `_` はゲートランナーの対象外 (共有ライブラリの慣習)。
  コミット済み JSON の検査は隣の check_grammar_books.py が CI で回す
  (同じ規則をここから import しているので二重管理にならない)。
"""
import glob
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # リポジトリ直下
KATEX_DIR = os.path.join(ROOT, "vendor", "katex")

# -----------------------------------------------------------------------------
# 教科ごとの解説の見出し (docs/kamitest-manual/ の教科別ページと一致させる。
# ずれたら scripts/book_exam/check_kamitest_manual.py が落とす)
# ★ 最後の 1 つは「誤答を 1 つずつ潰す節」。番号と選択肢の文字列を照合する。
# -----------------------------------------------------------------------------
ENG_HEADINGS = ("## 🎯 コアイメージ", "## 🔬 文構造分析",
                "## 📍 正解の根拠", "## ❌ 誤答 NG 理由")

SUBJECT_HEADINGS = {
    "grammar":  ENG_HEADINGS,
    "reading":  ENG_HEADINGS,
    "eiken":    ENG_HEADINGS,
    "mock":     ENG_HEADINGS,
    "math":     ("【方針】", "【立式】", "【計算】", "【答え】", "【誤答の切り方】"),
    "japanese": ("【設問の型】", "【本文の根拠】", "【正解の理由】",
                 "【誤答の切り方】", "【次に使える型】"),
    "science":  ("【何が起きているか】", "【使う法則】", "【立式】",
                 "【計算】", "【誤答の切り方】"),
    "social":   ("【何を問うているか】", "【資料のどこ】", "【正解の理由】",
                 "【誤答の切り方】", "【覚え方の目印】"),
}

# 解説に書いてはいけない生の LaTeX (画面は textContent 表示なのでそのまま出る)
RAW_TEX_IN_EXP = re.compile(r"\$|\\\(|\\\)|\\frac|\\dfrac|\\sqrt|\\times|\\mathrm|¥\(")
# 刷り上がり PDF に残っていてはいけないもの (KaTeX が落ちた合図)
RAW_TEX_IN_PDF = re.compile(r"\$|\\frac|\\dfrac|\\sqrt|\\times|\\mathrm|\\circ|¥\(|\\\(")
MATH = re.compile(r"\$([^$]+)\$")
TAG = re.compile(r"[A-Z0-9]+-[A-Z0-9]+")


def strip_math(s):
    """$…$ を落として素の文字列にする (PDF 逆照合と誤答照合はこの形で見る)。"""
    return re.sub(r"\s+", " ", MATH.sub(lambda m: m.group(1), s or "")).strip()


def plain_segments(s):
    """$…$ の外側だけを取り出す (KaTeX が描いた式は PDF で別の字形になるため)。"""
    return [seg.strip() for seg in MATH.split(s or "")[::2] if seg.strip()]


# =============================================================================
# 検証 (正典を直接見る唯一の層)
# =============================================================================
def verify(meta, questions, extra=None):
    """@returns エラー文の一覧 (空なら合格)。"""
    errs = []
    subject = meta.get("subject")
    heads = SUBJECT_HEADINGS.get(subject)
    if heads is None:
        errs.append(f"subject {subject!r} は使えない "
                    f"(使えるのは {sorted(SUBJECT_HEADINGS)})")
        return errs
    if not (isinstance(meta.get("time_limit_min"), int)
            and meta["time_limit_min"] >= 1):
        errs.append("time_limit_min が 1 以上の整数でない")
    for key in ("stem", "title", "subject_name", "level"):
        if not str(meta.get(key) or "").strip():
            errs.append(f"META の {key} が空")

    printed = []          # 解答漏洩の走査対象 (問題編に刷る全文)
    for text in (meta.get("intro"), ):
        if text:
            printed.append(strip_math(text))
    for p in meta.get("passages") or []:
        printed.append(strip_math(re.sub(r"<[^>]+>", " ", p.get("html") or "")))

    for i, q in enumerate(questions):
        no = q.get("number")
        at = f"第{no}問"
        if no != i + 1:
            errs.append(f"{at}: 番号が飛んでいる (期待 {i + 1})")
        page = q.get("page")
        if not (isinstance(page, int) and page >= 1):
            errs.append(f"{at}: page が 1 以上の整数でない")
        elif i and page < questions[i - 1].get("page", 0):
            errs.append(f"{at}: page が前の設問より戻っている")
        stem = str(q.get("stem") or "").strip()
        if not stem:
            errs.append(f"{at}: 設問文が空")
        printed.append(strip_math(stem))
        pts = q.get("points")
        if not (isinstance(pts, int) and not isinstance(pts, bool) and pts >= 1):
            errs.append(f"{at}: 配点が 1 以上の整数でない")
        if not TAG.fullmatch(str(q.get("unit_tag") or "")):
            errs.append(f"{at}: unit_tag の形が崩れている ({q.get('unit_tag')!r})")

        choices = q.get("choices")
        ans = q.get("answer")
        if choices is None:                       # --- 記述 -------------------
            a = str(ans or "").strip()
            if not a:
                errs.append(f"{at}: 記述の正解が空")
            elif re.fullmatch(r"[0-9]+", a):
                errs.append(f"{at}: 記述の正解が数字だけ ({a!r})。"
                            f"単位を付けるか選択式にする")
            for alt in q.get("accepted") or []:
                if not str(alt).strip():
                    errs.append(f"{at}: accepted に空のものが混ざっている")
        else:                                     # --- 選択式 -----------------
            if not (2 <= len(choices) <= 10):
                errs.append(f"{at}: 選択肢が 2〜10 でない ({len(choices)})")
            if len(set(choices)) != len(choices):
                errs.append(f"{at}: 選択肢に同じものが混ざっている")
            if q.get("accepted"):
                errs.append(f"{at}: 別解は記述のときだけ使える")
            if not (isinstance(ans, int) and not isinstance(ans, bool)
                    and 1 <= ans <= len(choices)):
                errs.append(f"{at}: 正解番号が 1〜{len(choices)} でない ({ans!r})")
            for c in choices:
                printed.append(strip_math(str(c)))

        # --- 解説: 教科の見出しが順番どおりに 1 回ずつ ----------------------
        exp = str(q.get("explanation") or "")
        if RAW_TEX_IN_EXP.search(exp):
            errs.append(f"{at}: 解説に生の LaTeX がある "
                        f"(画面は素のテキスト表示。x^2 / (a+b)/2 / √2 の形で書く)")
        pos = -1
        for h in heads:
            p = exp.find(h)
            if p < 0:
                errs.append(f"{at}: 解説に「{h}」が無い")
            elif exp.count(h) > 1:
                errs.append(f"{at}: 解説に「{h}」が 2 回以上ある")
            elif p < pos:
                errs.append(f"{at}: 解説のセクションの順番が崩れている ({h})")
            else:
                pos = p
        # --- 誤答を潰す節: 番号と選択肢の文字列まで突き合わせる --------------
        if heads[-1] in exp and isinstance(choices, list) and \
                isinstance(ans, int) and 1 <= ans <= len(choices):
            ng = exp.split(heads[-1])[-1]
            lines = {}
            for ln in ng.splitlines():
                m = re.match(r"\s*([1-9])\.\s*(.*)", ln)
                if m:
                    lines[int(m.group(1))] = m.group(2)
            if ans in lines:
                errs.append(f"{at}: 正解 {ans} が誤答の節に載っている")
            plain = q.get("choices_plain") or [strip_math(str(c)) for c in choices]
            if len(plain) != len(choices):
                errs.append(f"{at}: choices_plain の数が選択肢と違う")
                plain = [strip_math(str(c)) for c in choices]
            for n in range(1, len(choices) + 1):
                if n == ans:
                    continue
                if n not in lines:
                    errs.append(f"{at}: 誤答 {n} の説明が無い")
                elif str(plain[n - 1]) not in strip_math(lines[n]):
                    errs.append(f"{at}: 誤答 {n} の説明が選択肢と合っていない "
                                f"(選択肢 {plain[n-1]!r})")

    # --- 記述の正解が問題編のどこかに刷られていないか (解答漏洩) -------------
    for q in questions:
        if q.get("choices") is not None:
            continue
        a = strip_math(str(q.get("answer") or ""))
        core = re.sub(r"[0-9．.\s]+", "", a)      # 単位・数値を除いた語の部分
        if len(core) < 2:
            continue
        for j, text in enumerate(printed):
            if core in text:
                errs.append(f"第{q.get('number')}問: 記述の答え「{core}」が"
                            f"問題編の別の場所に印字されている")
                break

    # --- 正解位置の配り -----------------------------------------------------
    seq = [q["answer"] for q in questions
           if isinstance(q.get("choices"), list)
           and isinstance(q.get("answer"), int)]
    counts = {len(q["choices"]) for q in questions if isinstance(q.get("choices"), list)}
    if seq and len(counts) == 1:
        c = counts.pop()
        n = len(seq)
        lo, hi = n // c, -(-n // c)
        dist = {k: seq.count(k) for k in range(1, c + 1)}
        if not all(lo <= v <= hi for v in dist.values()):
            errs.append(f"正解位置が偏っている: {dist} (各 {lo}〜{hi} 回に収める)")
    for i in range(len(seq) - 2):
        if seq[i] == seq[i + 1] == seq[i + 2]:
            errs.append(f"正解番号 {seq[i]} が第{i + 1}問から 3 連続している")

    if extra:
        errs.extend(extra(meta, questions) or [])
    return errs


# =============================================================================
# 取り込み JSON
# =============================================================================
def build_json(meta, questions):
    """import_books.py が読む bundle。source の stem が PDF 名と一致する。"""
    out = []
    for q in questions:
        choices = q.get("choices")
        row = {
            "number": q["number"], "page": q["page"],
            "answer_type": "choice" if choices is not None else "short",
            "choice_count": len(choices) if choices is not None else None,
            "correct_answer": (str(q["answer"]) if choices is not None
                               else str(q["answer"]).strip()),
            "points": q["points"], "unit_tag": q["unit_tag"],
            "explanation": q["explanation"],
        }
        if choices is None and q.get("accepted"):
            row["accepted_answers"] = list(q["accepted"])
        out.append(row)
    return {
        "source": f"{meta['stem']}.yaml",
        "subject_name": meta["subject_name"],
        "book": {"title": meta["title"], "subject": meta["subject"],
                 "level": meta["level"], "time_limit_min": meta["time_limit_min"]},
        "questions": out,
    }


# =============================================================================
# 問題 PDF
# =============================================================================
CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Noto Sans CJK JP", "Noto Sans JP", "Hiragino Kaku Gothic ProN",
       "Yu Gothic", sans-serif; color: #111; font-size: 11.5pt; line-height: 1.85; }
.head { border-bottom: 2px solid #111; padding-bottom: 6px; margin-bottom: 20px; }
.head h1 { font-size: 16pt; margin: 0 0 2px; }
.head .meta { font-size: 9.5pt; color: #555; }
.intro { border: 1px solid #bbb; padding: 8px 10px; margin-bottom: 18px;
         font-size: 10pt; line-height: 1.7; }
.passage { border: 1px solid #333; padding: 10px 12px; margin-bottom: 18px;
           page-break-inside: avoid; }
.passage h2 { font-size: 11pt; margin: 0 0 6px; }
.passage .body { font-size: 10.5pt; line-height: 2.0; }
.passage .src { font-size: 8.5pt; color: #555; margin-top: 6px; }
.q { margin-bottom: 26px; page-break-inside: avoid; }
.q .no { font-weight: 700; font-size: 11pt; }
.q .pt { font-size: 9pt; color: #666; margin-left: 8px; font-weight: 400; }
.q .stem { margin: 4px 0 8px; }
.q .fig { margin: 8px 0; text-align: center; }
.q .fig svg { max-width: 100%; height: auto; }
ol.ch { list-style: none; padding-left: 14px; margin: 0; }
ol.ch li { margin: 2px 0; }
ol.ch .n { display: inline-block; width: 1.9em; font-weight: 600; }
.short { margin-left: 14px; }
.short .box { display: inline-block; min-width: 46mm; border-bottom: 1px solid #111;
              height: 1.6em; vertical-align: -0.35em; }
.short .unit { margin-left: 6px; }
.pagebreak { page-break-after: always; }
.katex { font-size: 1.03em; }
"""

_KATEX_BOOT = """
<script src="katex.min.js"></script>
<script src="auto-render.min.js"></script>
<script>
  document.addEventListener('DOMContentLoaded', function () {
    renderMathInElement(document.body, {
      delimiters: [{left: '$', right: '$', display: false}],
      throwOnError: true
    });
    document.title = document.title + ' [katex-done]';
  });
</script>
"""


def _esc(s):
    """設問文の HTML 化。$…$ は KaTeX に渡すのでそのまま残す。"""
    return _html.escape(str(s), quote=False)


def render_question(q):
    out = [f'<div class="q"><div class="no">第{q["number"]}問'
           f'<span class="pt">（{q["points"]}点）</span></div>',
           f'<div class="stem">{_esc(q["stem"])}</div>']
    if q.get("figure"):
        out.append(f'<div class="fig">{q["figure"]}</div>')
    if q.get("choices") is not None:
        out.append('<ol class="ch">')
        for i, c in enumerate(q["choices"], 1):
            out.append(f'<li><span class="n">{i}.</span>{_esc(c)}</li>')
        out.append("</ol>")
    else:
        unit = q.get("unit") or ""
        out.append(f'<div class="short">答 <span class="box"></span>'
                   f'<span class="unit">{_esc(unit)}</span></div>')
    out.append("</div>")
    return "".join(out)


def build_html(meta, questions):
    total = sum(q["points"] for q in questions)
    by_page = {}
    for q in questions:
        by_page.setdefault(q["page"], []).append(q)
    passages = {}
    for p in meta.get("passages") or []:
        passages.setdefault(p["page"], []).append(p)

    body = []
    pages = sorted(set(by_page) | set(passages))
    for idx, page in enumerate(pages):
        if idx == 0:
            body.append(
                f'<div class="head"><h1>{_esc(meta["title"])}</h1>'
                f'<div class="meta">{_esc(meta["level"])} / 全{len(questions)}問 '
                f'{total}点 / 制限時間 {meta["time_limit_min"]} 分'
                f' — 解答は別画面の答案に入力してください</div></div>')
            if meta.get("intro"):
                body.append(f'<div class="intro">{_esc(meta["intro"])}</div>')
        else:
            body.append(f'<div class="head"><h1>{_esc(meta["title"])}'
                        f'<span style="font-size:10pt;font-weight:400"> — '
                        f'{page} ページ目</span></h1></div>')
        for p in passages.get(page, []):
            src = (f'<div class="src">{_esc(p["source"])}</div>'
                   if p.get("source") else "")
            body.append(f'<div class="passage"><h2>{_esc(p.get("title") or "")}</h2>'
                        f'<div class="body">{p["html"]}</div>{src}</div>')
        for q in by_page.get(page, []):
            body.append(render_question(q))
        if idx < len(pages) - 1:
            body.append('<div class="pagebreak"></div>')

    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{_esc(meta["title"])}</title>'
            f'<link rel="stylesheet" href="katex.min.css">'
            f'<style>{CSS}</style>{_KATEX_BOOT}</head>'
            f'<body>{"".join(body)}</body></html>')


def find_chrome():
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    for pat in (f"{base}/chromium-*/chrome-linux/chrome",
                f"{base}/chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    direct = os.path.join(base, "chromium")
    if os.path.exists(direct) and os.access(direct, os.X_OK):
        return direct
    for c in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if os.path.exists(mac) else None


def write_pdf(meta, questions, out_pdf):
    """@returns エラー文 (None なら成功)。"""
    chrome = find_chrome()
    if not chrome:
        return "Chrome / Chromium が見つからない。PDF を作れない"
    if not os.path.isdir(KATEX_DIR):
        return f"vendor/katex が無い ({KATEX_DIR})"
    with tempfile.TemporaryDirectory() as tmp:
        # ★ katex 一式を同じフォルダへ写す。file:// を跨がせない (フォントが落ちる)
        for name in ("katex.min.js", "katex.min.css", "auto-render.min.js"):
            shutil.copy(os.path.join(KATEX_DIR, name), os.path.join(tmp, name))
        shutil.copytree(os.path.join(KATEX_DIR, "fonts"),
                        os.path.join(tmp, "fonts"))
        src = os.path.join(tmp, "book.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(build_html(meta, questions))
        cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox",
               "--no-pdf-header-footer", "--virtual-time-budget=15000",
               f"--print-to-pdf={out_pdf}", "file://" + src]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode or not os.path.exists(out_pdf):
            return "print-to-pdf が失敗: " + (r.stderr or r.stdout)[-400:]
    return None


# =============================================================================
# 刷り上がり PDF の読み返し (相互チェック ①層)
# =============================================================================
def pdf_pages(path):
    """各ページのテキスト。pypdf → pymupdf の順。無ければ None。"""
    try:
        from pypdf import PdfReader
        return [p.extract_text() or "" for p in PdfReader(path).pages]
    except Exception:
        pass
    for mod in ("pymupdf", "fitz"):          # fitz は旧名 (警告が出る)
        try:
            m = __import__(mod)
            with m.open(path) as doc:
                return [pg.get_text() for pg in doc]
        except ImportError:
            continue
        except Exception:
            return None
    return None


def verify_pdf(meta, questions, path):
    """@returns エラー文の一覧。"""
    errs = []
    pages = pdf_pages(path)
    if pages is None:
        return ["PDF を読み返せない (pypdf も pymupdf も無い)。"
                "python3 -m pip install pypdf"]
    want_pages = max(q["page"] for q in questions)
    if len(pages) != want_pages:
        errs.append(f"PDF が {len(pages)} ページ (正典は {want_pages} ページ)")
    flat = [re.sub(r"\s+", "", p) for p in pages]
    whole = "".join(pages)
    # --- 生の LaTeX が残っていないか (KaTeX が落ちた合図) --------------------
    m = RAW_TEX_IN_PDF.search(whole)
    if m:
        i = max(0, m.start() - 40)
        errs.append(f"PDF に生の LaTeX が残っている (KaTeX が落ちている): "
                    f"…{whole[i:m.start() + 40]!r}…")
    # --- 全設問が正典どおりのページに在るか --------------------------------
    for q in questions:
        idx = q["page"] - 1
        if idx >= len(flat):
            continue
        page_text = flat[idx]
        if f"第{q['number']}問" not in page_text:
            errs.append(f"第{q['number']}問: PDF の {q['page']} ページに見つからない")
            continue
        for seg in plain_segments(q["stem"]):
            if re.sub(r"\s+", "", seg) not in page_text:
                errs.append(f"第{q['number']}問: 設問文が PDF に無い ({seg[:24]!r})")
                break
        for i, c in enumerate(q.get("choices") or [], 1):
            for seg in plain_segments(str(c)):
                if re.sub(r"\s+", "", seg) not in page_text:
                    errs.append(f"第{q['number']}問: 選択肢 {i} が PDF に無い "
                                f"({seg[:24]!r})")
                    break
    return errs


# =============================================================================
def run(here, meta, questions, verify_extra=None):
    """build_*.py から呼ぶ入口。@returns 終了コード。"""
    errs = verify(meta, questions, verify_extra)
    if errs:
        for e in errs:
            print(f"✗ {e}")
        return 1
    print(f"[ok] verify — {len(questions)} 問 / {meta['subject']} / "
          f"見出し {'・'.join(SUBJECT_HEADINGS[meta['subject']])}")

    stem = meta["stem"]
    out_json = os.path.join(here, f"{stem}.json")
    out_pdf = os.path.join(here, f"{stem}_問題.pdf")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(build_json(meta, questions), f, ensure_ascii=False, indent=1)
    print(f"[ok] {os.path.basename(out_json)}")

    why = write_pdf(meta, questions, out_pdf)
    if why:
        print(f"✗ {why}")
        return 1
    print(f"[ok] {os.path.basename(out_pdf)} ({os.path.getsize(out_pdf) // 1024} KB)")

    if os.environ.get("SKIP_PDF_VERIFY") == "1":
        print("! 刷り上がり PDF の読み返しを飛ばした (SKIP_PDF_VERIFY=1)。"
              "相互チェックの①層が抜けている")
        return 0
    errs = verify_pdf(meta, questions, out_pdf)
    if errs:
        for e in errs:
            print(f"✗ PDF 読み返し: {e}")
        return 1
    print(f"[ok] PDF 読み返し — 全{len(questions)}問・全選択肢が正典どおりの"
          f"ページに在る / 生の LaTeX なし")
    return 0
