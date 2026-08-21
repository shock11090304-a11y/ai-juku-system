#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""刷り上がりの問題 PDF を正典 (build_*.py の QUESTIONS) と逆照合する。

    python3 scripts/book_exam/materials/check_pdf_canon_match.py

引数なし = **materials/*/build_*.py の全冊子** (CLAUDE.md「引数なしの既定は刷るもの全部」)。
2 つの正典の形に対応する — 旧 `_grammar_build` 系 (STEM / TITLE / 8 要素タプルの QUESTIONS) と
新 `_book_build` 系 (META / dict の QUESTIONS)。後者の照合は _book_build.verify_pdf() を
そのまま呼ぶ (build 時と同じ実装。二重管理しない)。**どちらでもない形は落とす**。
run_all_gates.py が check* として自動で拾う。何を見たかを必ず印字する。

相互チェックの ① 層 (CLAUDE.md 2026-08-16「出力物どうしの照合」) の恒久化:
  正典 → PDF の生成が正しくても、**PDF から読み返して**全問・全選択肢が実在することを
  独立に確かめるまで「できた」と言わない。見るもの:
    ・冊子タイトルが 1 ページ目に在る / ページ数が正典の最大ページと一致
    ・全設問の「第N問」・設問文 (空所含む)・選択肢 1〜4 が、正典どおりのページに在る

★ PDF ライブラリは pypdf → pymupdf (fitz) の順で**関数内 import** (CI は pymupdf を入れる。
  トップレベルで fitz を import すると run_all_gates の --no-pdf に外されるが、この冊子 PDF は
  コミット済みなので CI でも実検査できる)。どちらも無ければ**落とす** — 黙って緑を出さない。
"""
import glob
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _book_build as BB  # noqa: E402  (新しい正典の形の照合はここが持つ)


def extract_pages(pdf_path):
    """PDF の各ページのテキスト。pypdf → fitz の順に試す。無ければ None。"""
    try:
        from pypdf import PdfReader
        return [p.extract_text() or "" for p in PdfReader(pdf_path).pages]
    except ImportError:
        pass
    try:
        import fitz
        with fitz.open(pdf_path) as doc:
            return [pg.get_text() for pg in doc]
    except ImportError:
        return None


def load_build(path):
    name = "canon_" + re.sub(r"\W", "_", os.path.relpath(path, HERE))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def squeeze(s):
    return re.sub(r"\s+", "", s)


def main():
    builds = sorted(glob.glob(os.path.join(HERE, "*", "build_*.py")))
    if not builds:
        print("NG: 検査対象の build_*.py が 1 つも無い (materials/*/)")
        return 1
    bad, n_books, n_qs = [], 0, 0
    for path in builds:
        label = os.path.relpath(path, HERE)
        try:
            m = load_build(path)
        except Exception as e:
            bad.append(f"{label}: 正典を読めない ({e})")
            continue
        meta = getattr(m, "META", None)
        questions = getattr(m, "QUESTIONS", None)
        if questions is None:
            bad.append(f"{label}: QUESTIONS が無い")
            continue
        if meta is not None:                      # --- 新 (_book_build) の形 ---
            stem, title = meta.get("stem"), meta.get("title")
        elif hasattr(m, "STEM"):                  # --- 旧 (_grammar_build) の形 ---
            stem, title = m.STEM, m.TITLE
        else:
            bad.append(f"{label}: META も STEM も無い (知らない正典の形)")
            continue
        pdf = os.path.join(os.path.dirname(path), f"{stem}_問題.pdf")
        if not os.path.exists(pdf):
            bad.append(f"{label}: 問題 PDF が無い ({os.path.basename(pdf)})。build を回してコミットすること")
            continue
        pages = extract_pages(pdf)
        if pages is None:
            print("NG: pypdf も pymupdf も無い。PDF を読めないので検査できない "
                  "(python3 -m pip install pypdf)")
            return 1
        n_books += 1
        n_qs += len(questions)
        # --- 埋め込みフォント (字形が日本語か) — 新旧どちらの正典でも見る -----
        #   ★ 日本語フォントが 1 つも無い環境で刷ると Chrome が中国語フォントに
        #     落ちる。PDF は正常に出るので紙を見るまで気づけない。
        names = BB.pdf_font_names(pdf)
        if names is None:
            bad.append(f"{stem}: 埋め込みフォントを読めない")
        else:
            for e in BB.font_problems(names):
                bad.append(f"{stem}: {e}")

        if meta is not None:
            if squeeze(title) not in squeeze(pages[0]):
                bad.append(f"{stem}: 1 ページ目に冊子タイトルが無い")
            for e in BB.verify_pdf(meta, questions, pdf):
                bad.append(f"{stem}: {e}")
            if not any(x.startswith(stem) or x.startswith(label) for x in bad):
                print(f"[OK] {stem} ({len(questions)}問 / {len(pages)}頁 ⇔ PDF 一致)")
            continue
        want_pages = max(q[1] for q in questions)
        if len(pages) != want_pages:
            bad.append(f"{stem}: ページ数がずれている (PDF {len(pages)} 頁 / 正典 {want_pages} 頁)")
            continue
        norm = [squeeze(t) for t in pages]
        if squeeze(title) not in norm[0]:
            bad.append(f"{stem}: 1 ページ目に冊子タイトルが無い")
        for no, page, q_stem, choices, _ans, _pts, _tag, _exp in questions:
            pg = norm[page - 1]
            if f"第{no}問" not in pg:
                bad.append(f"{stem} 第{no}問: 「第{no}問」が {page} ページ目に無い")
            if squeeze(q_stem) not in pg:
                bad.append(f"{stem} 第{no}問: 設問文が {page} ページ目に無い")
            for i, c in enumerate(choices, 1):
                if squeeze(f"{i}.{c}") not in pg:
                    bad.append(f"{stem} 第{no}問: 選択肢 {i} ({c}) が {page} ページ目に無い")
        if not any(x.startswith(stem) or x.startswith(label) for x in bad):
            print(f"[OK] {stem} ({len(questions)}問 / {len(pages)}頁 ⇔ PDF 一致)")
    if bad:
        for x in bad:
            print(f"NG: {x}")
        print(f"違反 {len(bad)} 件")
        return 1
    print(f"=== ALL PASS (冊子 {n_books} / 設問 {n_qs} — 正典⇔PDF 全数一致) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
