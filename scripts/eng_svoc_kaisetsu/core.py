# -*- coding: utf-8 -*-
"""
過去問 SVOCM 構造解析プリント — 共通コア

★分解 DSL は自前で定義しない。scripts/eng_hinshi_bunkai/core.py のパーサを
  そのまま読み込んで使う（塾内の記号法を 1 本に保つため）。
  {LBL:text} / ( 副詞のカタマリ ) / [ 名詞のカタマリ ] / < 形容詞のカタマリ >

★単一ソース原則: 本文は RAW（過去問プリントの印字そのまま）だけを正典として持ち、
  空所は FILLS で機械的に埋める。解析 DSL から復元した英文が
  「RAW に FILLS を当てたもの」と一致することを check.py が全文照合する。
  → 解析の途中で語を落とす・言い換えるといった事故が構造的に起きない。
"""
import os, re, sys, html, shutil, subprocess, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
HB_CORE = os.path.join(SCRIPTS, "eng_hinshi_bunkai", "core.py")


def _load_hb_core():
    """品詞分解教材のコア（DSL パーサ）を読み込む。塾内の記号法の正典。"""
    if not os.path.exists(HB_CORE):
        raise RuntimeError(f"DSL パーサが見つからない: {HB_CORE}")
    spec = importlib.util.spec_from_file_location("hb_core", HB_CORE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hb = _load_hb_core()
parse = hb.parse
plain_text = hb.plain_text
render_analysis = hb.render_analysis
render_skeleton = hb.render_skeleton
ALLOWED_LABELS = hb.ALLOWED_LABELS

esc = lambda s: html.escape(str(s), quote=False)

# ---------------------------------------------------------------- 照合用の正規化
# 引用符は「どちらの語にくっつくか」が機械的に決まらないので照合対象から外す。
# それ以外（語・コンマ・ピリオド・コロン・ハイフン）は 1 文字も落とさず照合する。
_QUOTES = re.compile(r'["\u201c\u201d\u2018\u2019]')
# {S:He} {V:'s going} のように短縮形を割って貼れるようにする
_CONTRACT = re.compile(r"\s+'(s|d|ll|re|ve|m)\b")
_SP_PUNCT = re.compile(r"\s+([,.;:?!])")


def cmp_norm(s):
    """DSL 復元文と原文プリントを突き合わせるための正規化。"""
    s = _QUOTES.sub("", str(s))
    s = re.sub(r"\s+", " ", s).strip()
    s = _CONTRACT.sub(r"'\1", s)
    s = _SP_PUNCT.sub(r"\1", s)
    return s


def apply_fills(raws, fills):
    """本文（段落のリスト）の空所マーカー（[ 1 ] や (B29) など）を解答で埋める。

    ★埋めた本文は保存しない。常に RAW + FILLS から作り直す（単一ソース）。
    どこにも出てこない FILLS・埋め残しのマーカーはここで例外にする。
    """
    if isinstance(raws, str):
        raws = [raws]
    out = list(raws)
    joined = " ".join(out)
    for marker in fills:
        if marker not in joined:
            raise ValueError(f"空所マーカーが本文のどこにも無い: {marker!r}")
    for marker, word in fills.items():
        out = [p.replace(marker, word) for p in out]
    left = re.findall(r"\[\s*\d+\s*\]|\((?:B\d+|[A-G])\)", " ".join(out))
    if left:
        raise ValueError(f"埋め残しの空所マーカー: {left}")
    return out


# ---------------------------------------------------------------- 文型の語彙
PATTERNS = {
    "SV": "第1文型（SV）", "SVC": "第2文型（SVC）", "SVO": "第3文型（SVO）",
    "SVOO": "第4文型（SVOO）", "SVOC": "第5文型（SVOC）",
}

# ---------------------------------------------------------------- PDF
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/opt/pw-browsers/chromium",
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
]
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        p = shutil.which(name)
        if p:
            return p
    return None


def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def render_pdf(html_str, out_path, foot_label):
    """HTML → PDF（Chrome headless）→ ページ番号を焼く。Chrome が無ければ False。"""
    chrome = find_chrome()
    if not chrome:
        print("  [skip] Chrome/Chromium が見つからないので PDF は作らない")
        return False
    tmp = out_path + ".src.html"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html_str)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", f"--print-to-pdf={out_path}", "file://" + tmp]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(tmp)
    _stamp_pages(out_path, foot_label)
    return True


def _stamp_pages(path, label):
    """ページ番号と柱を下端に焼く。

    ★TextWriter は PyMuPDF の版によって原点が上左/下左でぶれる。
      page.insert_text() は上左原点で固定なのでこちらを使う（実測で下端に出ることを確認済み）。
    """
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            return
    font_path = find_font()
    if not font_path:
        return
    d = fitz.open(path)
    font = fitz.Font(fontfile=font_path)
    n = d.page_count
    for i, page in enumerate(d):
        y = page.rect.height - 16
        page.insert_text(fitz.Point(40, y), label, fontname="stampf",
                         fontfile=font_path, fontsize=7.4, color=(0.42, 0.45, 0.5))
        num = f"{i + 1} / {n}"
        w = font.text_length(num, 7.4)
        page.insert_text(fitz.Point(page.rect.width - 40 - w, y), num, fontname="stampf",
                         fontfile=font_path, fontsize=7.4, color=(0.42, 0.45, 0.5))
    try:
        d.subset_fonts()
    except Exception:
        pass
    d.save(path + ".tmp", garbage=4, deflate=True)
    d.close()
    os.replace(path + ".tmp", path)
