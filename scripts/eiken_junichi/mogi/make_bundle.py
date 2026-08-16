#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英検模試の data_no*.json を、冊子受験アプリ (神テスト) の取り込み bundle に変換する。

    python3 scripts/eiken_junichi/mogi/build.py          # 先に問題編 PDF の元 HTML を作る
    python3 scripts/eiken_junichi/mogi/make_pdf.sh       # (または build 済み PDF を用意)
    python3 scripts/eiken_junichi/mogi/make_bundle.py    # bundle/ に JSON と問題 PDF を用意
    python3 scripts/book_exam/import_books.py scripts/eiken_junichi/mogi/bundle \\
        --pdf-dir scripts/eiken_junichi/mogi/bundle      # 非公開で取り込む

■ 何をしているか
    data_no*.json (作問の正典) → bundle/英検準1級_模試_第N回.json (取り込み契約の形)
    ・大問1〜3 の 31 問だけを載せる。**大問4 (要約) と大問5 (意見論述) は自由英作文で、
      アプリの採点 (choice / short) では扱えないため載せない**。生徒は紙で書いて講師が採点する。
    ・解説は data の語義・和訳・誤答の語釈・段落の根拠から組み立てる (二重管理しない)。
    ・page は**刷り上がりの PDF から実測**する。当てずっぽうで書かない
      (page > page_count だと取り込みが弾かれ、ずれると生徒が別の頁を見る)。

■ 命名の約束 (import_books.find_pdf が完全一致で探す)
    bundle の "source" が「英検準1級_模試_第N回.yaml」なら、
    PDF は「英検準1級_模試_第N回_問題.pdf」でなければならない。

★ bundle/*.pdf は生成物なのでコミットしない (.gitignore)。取り込む前にこのスクリプトを回す。
"""
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bundle")
PDF_SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                       "scripts", "book_exam", "materials", "_out")
# ↑ build 済み PDF の置き場 (リポジトリ外に出さない・.gitignore 済み)
PDF_SRC = os.path.normpath(os.path.join(HERE, "..", "..", "book_exam", "materials", "_out"))

TIME_LIMIT_MIN = 90          # 一次筆記 (大問1〜5) の本番の持ち時間
LEVEL = "難関"
SUBJECT = "eiken"


def sq(s):
    return re.sub(r"\s+", "", s)


def measure_pages(pdf_path, d):
    """各設問が PDF の何ページに刷られているかを実測する。

    ★ 番号 "(19)" での照合はしない。本文中の空所マーカーと重複して**別の頁を指す**
      (実測で 18 / 24 / 31 が二重に当たった)。設問固有の英文で引く。
    """
    from pypdf import PdfReader
    pages = [sq(p.extract_text() or "") for p in PdfReader(pdf_path).pages]

    def find(frag):
        f = sq(frag)
        for i, t in enumerate(pages, 1):
            if f and f in t:
                return i
        return None

    pg, n, miss = {}, 1, []
    for it in d["part1"]:
        pg[n] = find(it["sentence"][:45]); n += 1
    for ps in d["part2"]:
        for b in ps["blanks"]:
            pg[n] = find(max(b["choices"], key=len)); n += 1   # 最長の選択肢を目印にする
    for ps in d["part3"]:
        for q in ps["questions"]:
            pg[n] = find(q["q"][:45]); n += 1
    miss = [k for k, v in pg.items() if v is None]
    if miss:
        raise SystemExit(f"✗ 設問 {miss} の掲載ページを PDF から特定できませんでした。"
                         f"問題編 PDF が最新か確認してください ({os.path.basename(pdf_path)})")
    return pg, len(pages)


def exp_part1(it):
    ans = it["choices"][it["answer"]]
    lines = [f"## ✅ 正解 {it['answer'] + 1}　{ans}",
             f"{it.get('pos', '')} {it['gloss_ja']}".strip(),
             "",
             "## 📘 全文和訳",
             it["trans_ja"]]
    dis = it.get("distractors_ja") or {}
    if dis:
        lines += ["", "## ❌ 他の選択肢",
                  "　".join(f"{k}: {v}" for k, v in dis.items())]
    return "\n".join(lines)


def exp_part2(b, ps):
    return "\n".join([f"## ✅ 正解 {b['answer'] + 1}　{b['choices'][b['answer']]}",
                      "", "## 🔎 根拠", b["exp_ja"],
                      "", "## 📗 この英文の要旨", ps["summary_ja"]])


def exp_part3(q, ps):
    return "\n".join([f"## ✅ 正解 {q['answer'] + 1}",
                      "", "## ❓ 設問", q["q_ja"],
                      "", "## 🔎 根拠と誤答の処理", q["exp_ja"],
                      "", "## 📗 この英文の要旨", ps["summary_ja"]])


def build_bundle(d, pg):
    qs, n = [], 1
    for it in d["part1"]:
        qs.append({"number": n, "page": pg[n], "answer_type": "choice", "choice_count": 4,
                   "correct_answer": str(it["answer"] + 1), "points": 1,
                   "unit_tag": "EIKEN-P1-VOCAB", "explanation": exp_part1(it)})
        n += 1
    for ps in d["part2"]:
        for b in ps["blanks"]:
            qs.append({"number": n, "page": pg[n], "answer_type": "choice", "choice_count": 4,
                       "correct_answer": str(b["answer"] + 1), "points": 1,
                       "unit_tag": "EIKEN-P2-CLOZE", "explanation": exp_part2(b, ps)})
            n += 1
    for ps in d["part3"]:
        for q in ps["questions"]:
            qs.append({"number": n, "page": pg[n], "answer_type": "choice", "choice_count": 4,
                       "correct_answer": str(q["answer"] + 1), "points": 1,
                       "unit_tag": "EIKEN-P3-READ", "explanation": exp_part3(q, ps)})
            n += 1
    no = d["meta"]["no"]
    stem = f"英検準1級_模試_第{no}回"
    return stem, {
        "source": f"{stem}.yaml",
        "subject_name": "英語",
        "book": {"title": f"英検準1級 オリジナル模試 第{no}回 (筆記 大問1〜3)",
                 "subject": SUBJECT, "level": LEVEL, "time_limit_min": TIME_LIMIT_MIN},
        "questions": qs,
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(HERE, "data_no*.json")))
    if not files:
        raise SystemExit("✗ data_no*.json が見つかりません")
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        no = d["meta"]["no"]
        pdf_src = os.path.join(PDF_SRC, f"英検準1級模試_第{no}回_問題編.pdf")
        if not os.path.exists(pdf_src):
            raise SystemExit(f"✗ 問題編 PDF がありません: {pdf_src}\n"
                             f"  先に build.py で HTML を作り、PDF に印刷してください。")
        pg, n_pages = measure_pages(pdf_src, d)
        stem, bundle = build_bundle(d, pg)
        # 取り込みが完全一致で探す名前に合わせて置く
        shutil.copyfile(pdf_src, os.path.join(OUT, f"{stem}_問題.pdf"))
        with open(os.path.join(OUT, f"{stem}.json"), "w", encoding="utf-8") as fp:
            json.dump(bundle, fp, ensure_ascii=False, indent=1)
        print(f"[ok] {stem}.json ({len(bundle['questions'])} 問 / PDF {n_pages} 頁) "
              f"+ {stem}_問題.pdf")
    print("\n次: python3 scripts/book_exam/import_books.py scripts/eiken_junichi/mogi/bundle "
          "--pdf-dir scripts/eiken_junichi/mogi/bundle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
