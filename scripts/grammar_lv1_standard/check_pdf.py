#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""刷った PDF そのものを検査する（build_pdf.py を回した後に手元で回す）。

    python3 scripts/grammar_lv1_standard/build_pdf.py
    python3 scripts/grammar_lv1_standard/check_pdf.py

check.py はデータ (units/*.json) を見るだけなので、**紙になった時点で壊れるもの**は
捕まえられない。ここで見るのはその3つ:

  P1 豆腐        フォントにグリフが無くて □ / 空白になった文字
                 (日本語フォントに ✓ や絵文字が無いのは CLAUDE.md に既出の事故)
  P2 取りこぼし  設問文・選択肢・解説が組版から落ちていないか
                 (Paragraph に渡し忘れても reportlab は黙って出力する)
  P3 解答漏洩    ★問題編のページに答えが印字されていないか
                 データ上は分かれていても、組版のページ割りでずれると紙で漏れる。
                 「どのページまでが問題編か」を PDF のヘッダから読んで判定する。

★fitz(pymupdf) を import しているので、run_all_gates.py は --no-pdf のとき
  このゲートを自動で外し、「刷ったPDFが要る＝ここでは検査していない」と一覧に出す。
  CI は --no-pdf。ローカルでは必ず --no-pdf 無しで回すこと。
"""
import json
import os
import re
import sys
import unicodedata

import fitz  # noqa: F401  ← run_all_gates.py はこの import で「PDF が要る」と判定する

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS_DIR = os.path.join(HERE, "units")
PDF_PATH = os.path.join(HERE, "高校英文法レベル1_標準演習_仮定法不定詞動名詞時制_120問.pdf")

UNIT_ORDER = [
    ("01_tenses.json", "時制"),
    ("02_infinitive.json", "不定詞"),
    ("03_gerund.json", "動名詞"),
    ("04_subjunctive.json", "仮定法"),
]

# build_pdf.clean() が描画前に置き換える文字。照合はこの後の形で行う。
TRANS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "―": "-", "…": "...",
    "　": " ",
}

# 紙に出る記号のうち、和文フォントに有ることを個別に確かめておきたいもの。
DECOR = "①②③④■▶〈〉・～"


def norm(s):
    for k, v in TRANS.items():
        s = str(s).replace(k, v)
    # PDF から抜いた文字列は改行・連続空白が入るので、比較前に潰す
    return re.sub(r"\s+", " ", s).strip()


def squeeze(s):
    """空白を全部落とした形。**照合はこちらで行う。**

    ★1段落がページをまたぐと、ページごとに取り出した文字列を継ぎ足す時点で
      本来無い空白が語の途中に入る。空白を残したまま照合すると、
      「組版から落ちた」のか「ページをまたいだ」のか区別できず、
      実際に初版で解説8本を誤検出した。
    """
    return re.sub(r"\s+", "", norm(s))


def main():
    problems = []
    if not os.path.exists(PDF_PATH):
        print(f"✗ PDF が無い: {PDF_PATH}\n  先に build_pdf.py を回すこと。", file=sys.stderr)
        sys.exit(1)

    doc = fitz.open(PDF_PATH)

    # ★柱(ヘッダ)とノンブルを本文と分けて取り出す。
    #   build_pdf.py の on_page は本文を描いた**後**に柱を描くので、
    #   ページ全体を get_text() すると柱とノンブルが文字列の末尾に付く。
    #   段落がページをまたぐと、継ぎ足したときに柱の文字列が段落の途中に割り込み、
    #   「紙に出ていない」と誤検出する(初版で解説4本を誤検出した)。
    MM = 72 / 25.4
    heads, bodies = [], []
    for page in doc:
        w, h = page.rect.width, page.rect.height
        heads.append(page.get_text("text", clip=fitz.Rect(0, 0, w, 15 * MM)))
        bodies.append(page.get_text("text", clip=fitz.Rect(0, 15 * MM, w, h - 13 * MM)))
    print(f"=== 何を検査したか ===\n対象: {PDF_PATH}\nページ数: {len(bodies)}")

    # ---- 問題編 / 解答・解説編 の境目を柱から読む ----
    # build_pdf.py は各ページ右上に「問題編 · 単元名」「解答・解説編 · 単元名」を刷る。
    q_pages = [i for i, t in enumerate(heads) if "問題編" in t and "解答・解説編" not in t]
    a_pages = [i for i, t in enumerate(heads) if "解答・解説編" in t]
    if not q_pages or not a_pages:
        problems.append(f"[SECTION] 柱から問題編/解答編の境目が読めない (問題編 {len(q_pages)}頁 / "
                        f"解答編 {len(a_pages)}頁)。build_pdf.py の on_page が効いていない可能性"
                        "(NextPageTemplate の付け忘れで全ページが表紙テンプレートになると柱が消える)")
    print(f"問題編と判定したページ: {len(q_pages)} 頁 / 解答・解説編: {len(a_pages)} 頁")
    q_text = squeeze(" ".join(bodies[i] for i in q_pages))
    all_text = squeeze(" ".join(bodies))

    # ---- P1 豆腐 ----
    # get_text で拾えない＝グリフが無い、を直接見る代わりに、
    # 「データにある文字が本文テキストに1つも現れない」を種類ごとに数える。
    used = set()
    for fname, _u in UNIT_ORDER:
        with open(os.path.join(UNITS_DIR, fname), encoding="utf-8") as f:
            d = json.load(f)
        for q in d["questions"]:
            for v in q.values():
                for s in (v if isinstance(v, list) else [v]):
                    if isinstance(s, str):
                        used.update(norm(s))
    used |= set(DECOR)
    missing = sorted(c for c in used
                     if not c.isspace() and c not in all_text)
    if missing:
        problems.append("[GLYPH] 紙に1度も出ていない文字がある(豆腐の疑い): "
                        + " ".join(f"{c!r}(U+{ord(c):04X} {unicodedata.name(c, '?')})"
                                   for c in missing))

    # ---- P2 取りこぼし / P3 解答漏洩 ----
    checked = leaked = 0
    for fname, unit in UNIT_ORDER:
        with open(os.path.join(UNITS_DIR, fname), encoding="utf-8") as f:
            d = json.load(f)
        for q in d["questions"]:
            tag = f"{unit}#{q['no']}"
            must = []                    # 紙のどこかに必ず出ているべきもの
            if q["type"] == "mc":
                must.append(q["stem"])
                must += q["choices"]
            elif q["type"] == "order":
                must.append(q["prompt_ja"])
                must += q["tokens"]
            else:
                must.append(q["original"])
                must.append(q["instruction"])
            must.append(q["explanation"])
            must.append(q["point"])
            for s in must:
                checked += 1
                if squeeze(s) not in all_text:
                    problems.append(f"[MISSING TEXT] {tag}: 紙に出ていない: {norm(s)[:60]!r}")

            # ★答えが問題編のページに出ていないか。
            #   4択は選択肢として必ず問題編に出るので対象外(そこは check.py の守備範囲)。
            if q["type"] in ("order", "rewrite"):
                if squeeze(q["answer_text"]) in q_text:
                    problems.append(f"[ANSWER ON PAPER] {tag}: 答えが問題編のページに印字されている: "
                                    f"{q['answer_text']!r}")
                    leaked += 1

    print(f"紙と照合した文字列: {checked} 本")
    print(f"問題編での解答漏洩: {leaked} 件")
    print()
    print(f"=== 問題点 ({len(problems)} 件) ===")
    for p in problems:
        print("  " + p)
    if problems:
        print(f"\n  ✗ 不合格: 上の {len(problems)} 件を直すこと")
        sys.exit(1)
    print("\n  OK: 刷った PDF に問題なし")


if __name__ == "__main__":
    main()
