#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""青山学院大 2026 英語 実戦問題を、冊子受験アプリ (神テスト) の取り込み bundle にする。

    python3 scripts/aoyama_eigo_mirror/build.py            # 先に問題編 HTML/PDF を作る
    python3 scripts/aoyama_eigo_mirror/make_bundle.py      # bundle/ に JSON と問題 PDF
    python3 scripts/book_exam/import_books.py scripts/aoyama_eigo_mirror/bundle \\
        --pdf-dir scripts/aoyama_eigo_mirror/bundle        # 非公開で取り込む

■ 何を載せるか
    問題Ⅰ (長文・マーク 問1〜10) と 問題Ⅳ (語彙・マーク 問11〜15) の **15 問だけ**。
    ★問題Ⅱ (和訳) と 問題Ⅲ (英作文) は記述で、アプリの採点形式 (choice / short) では
      扱えないため載せない。冊子 PDF には全部刷ってあるので、記述は紙で講師が採点する。

■ 正典は content.json ただ 1 つ
    正解 (ans) も解説 (explanations_seki.json) もそこから引く。書き写さない。
    page は**刷り上がりの PDF から実測**する (当てずっぽうで書かない)。

■ 命名の約束 (import_books.find_pdf が完全一致で探す)
    "source" が「青山学院大_2026英語_実戦.yaml」なら
    PDF は「青山学院大_2026英語_実戦_問題.pdf」でなければならない。

★ bundle/*.pdf は生成物なのでコミットしない (.gitignore)。
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bundle")
PDF_SRC = os.path.normpath(os.path.join(HERE, "..", "book_exam", "materials", "_out"))
PDF_NAME = "青学2026英語実戦問題_問題編.pdf"   # build.py が刷る名前

STEM = "青山学院大_2026英語_実戦"
TITLE = "青山学院大 2026 英語 実戦問題 (問題Ⅰ・Ⅳ マーク式)"
SUBJECT = "reading"
LEVEL = "難関"
TIME_LIMIT_MIN = 80


def sq(s):
    return re.sub(r"\s+", "", s)


def measure_pages(pdf_path, probes):
    """設問ごとの掲載ページを刷り上がりから実測する。1 つでも見つからなければ中止。"""
    from pypdf import PdfReader
    pages = [sq(p.extract_text() or "") for p in PdfReader(pdf_path).pages]
    pg, miss = {}, []
    for n, probe in probes.items():
        f = sq(probe)
        hit = next((i for i, t in enumerate(pages, 1) if f and f in t), None)
        if hit is None:
            miss.append(n)
        pg[n] = hit
    if miss:
        raise SystemExit(f"✗ 設問 {miss} の掲載ページを PDF から特定できません。"
                         f"問題編 PDF が最新か確認してください ({os.path.basename(pdf_path)})")
    return pg, len(pages)


def explanation(exp, ans, options):
    """解説を組み立てる。正典の quote / reason / distractors をそのまま使う。"""
    out = [f"## ✅ 正解 {ans}　{options[ans - 1]}"]
    if exp.get("quote"):
        out += ["", "## 📍 本文の根拠", f"> {exp['quote']}", exp.get("quote_ja", "")]
    if exp.get("reason"):
        out += ["", "## 🔬 なぜそう読めるか", exp["reason"]]
    if exp.get("distractors"):
        out += ["", "## ❌ 誤答 NG 理由", exp["distractors"]]
    return "\n".join(x for x in out if x is not None)


def main():
    os.makedirs(OUT, exist_ok=True)
    d = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    exps = json.load(open(os.path.join(HERE, "explanations_seki.json"), encoding="utf-8"))

    pdf_src = os.path.join(PDF_SRC, PDF_NAME)
    if not os.path.exists(pdf_src):
        raise SystemExit(f"✗ 問題編 PDF がありません: {pdf_src}\n"
                         f"  先に build.py で HTML を作り、PDF に刷ってください。")

    # --- 設問を通し番号で並べる (Ⅰ=1〜10 / Ⅳ=11〜15。冊子の解答欄の番号と同じ) ---
    rows, probes = [], {}
    for q in d["I"]["questions"]:
        n = int(q["q_label"])
        rows.append((n, q["ans"], q["options"], exps.get(f"I_{n}", {}), "AOYAMA-I-READ"))
        probes[n] = q["stem"][:45]
    for it in d["IV"]["items"]:
        n = int(it["n"])
        rows.append((n, it["ans"], it["options"], exps.get(f"IV_{n}", {}), "AOYAMA-IV-VOCAB"))
        probes[n] = it["lines"][0]["text"][:45]

    rows.sort(key=lambda r: r[0])
    pg, n_pages = measure_pages(pdf_src, probes)

    qs = []
    for n, ans, options, exp, tag in rows:
        if not (isinstance(ans, int) and 1 <= ans <= len(options)):
            raise SystemExit(f"✗ 第{n}問: 正解 {ans!r} が選択肢の範囲 (1〜{len(options)}) にない")
        qs.append({"number": n, "page": pg[n], "answer_type": "choice",
                   "choice_count": len(options), "correct_answer": str(ans),
                   "points": 1, "unit_tag": tag,
                   "explanation": explanation(exp, ans, options)})

    bundle = {"source": f"{STEM}.yaml", "subject_name": "英語",
              "book": {"title": TITLE, "subject": SUBJECT, "level": LEVEL,
                       "time_limit_min": TIME_LIMIT_MIN},
              "questions": qs}
    shutil.copyfile(pdf_src, os.path.join(OUT, f"{STEM}_問題.pdf"))
    with open(os.path.join(OUT, f"{STEM}.json"), "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=1)
    print(f"[ok] {STEM}.json ({len(qs)} 問 / PDF {n_pages} 頁) + {STEM}_問題.pdf")
    print("  ページ割り:", {n: pg[n] for n, *_ in rows})
    print("\n次: python3 scripts/book_exam/import_books.py scripts/aoyama_eigo_mirror/bundle "
          "--pdf-dir scripts/aoyama_eigo_mirror/bundle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
