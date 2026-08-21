#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""materials/ 以下の冊子 bundle (JSON + 問題 PDF) を全数検査する。

    python3 scripts/book_exam/materials/check_grammar_books.py

引数なし = **コミット済みの bundle 全部** (CLAUDE.md「引数なしの既定は刷るもの全部」)。
run_all_gates.py が check* として自動で拾う。何を見たかを必ず印字する。

見るもの:
  ・import_books.validate_questions_py と同じ規則 (正典の写しを再利用。二重管理しない)
  ・取り込みが前提にする問題 PDF ({source の stem}_問題.pdf) が隣に在ること・大きさ
  ・**教科ごとの**解説の見出し (英語 = コアイメージ → 文構造分析 → 正解の根拠 → 誤答 NG 理由 /
    数学・国語・理科・社会 = 【】の 5 見出し)。正典は _book_build.SUBJECT_HEADINGS で、
    ビルダーと同じものを import している (二重管理しない)
  ・誤答を潰す節の番号 (正解がそこに載っていない / 誤答が全部ある)
  ・正解位置の配り (選択肢の数がそろっているなら各番号が均等 ±1・同じ番号の 3 連続なし)

★ ここで見られるのは JSON に写った範囲だけ。**選択肢の文字列は bundle に無い**ので、
  番号と選択肢の突き合わせは正典 (build_*.py の QUESTIONS) を持つ
  _grammar_build.verify() / _book_build.verify() が build 時に行う。

★ 名前は grammar のままだが、対象は materials/ の**全教科**。
  (CI と run_all_gates の一覧に出ている名前なので、改名はしていない)
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import import_books as ib  # noqa: E402  (validate_questions_py と PDF 上限の正典)
import _book_build as BB   # noqa: E402  (教科ごとの解説見出しの正典)


def check_explanation_format(name, qs, heads, bad):
    """解説の見出しと、誤答を潰す節の番号。heads[-1] が誤答の節。"""
    for q in qs:
        at = f"{name} 第{q.get('number')}問"
        exp = q.get("explanation") or ""
        pos = -1
        for h in heads:
            p = exp.find(h)
            if p < 0:
                bad.append(f"{at}: 解説に「{h}」が無い")
            elif p < pos:
                bad.append(f"{at}: 解説のセクションの順番が崩れている ({h})")
            else:
                pos = p
        if q.get("answer_type") != "choice" or heads[-1] not in exp:
            continue
        ans = str(q.get("correct_answer"))
        cc = q.get("choice_count") or 0
        ng = exp.split(heads[-1])[-1]
        ng_nums = {m.group(1) for m in re.finditer(r"^\s*([1-9])\.", ng, re.M)}
        if ans in ng_nums:
            bad.append(f"{at}: 正解 {ans} が誤答の節に載っている")
        missing = [str(n) for n in range(1, cc + 1)
                   if str(n) != ans and str(n) not in ng_nums]
        if missing:
            bad.append(f"{at}: 誤答 {'/'.join(missing)} の説明が無い")


def check_answer_positions(name, qs, bad):
    seq = [int(q["correct_answer"]) for q in qs
           if q.get("answer_type") == "choice"
           and re.fullmatch(r"[1-9][0-9]?", str(q.get("correct_answer") or ""))]
    counts = {q.get("choice_count") for q in qs if q.get("answer_type") == "choice"}
    if seq and len(counts) == 1 and isinstance(next(iter(counts)), int):
        c = counts.pop()
        lo, hi = len(seq) // c, -(-len(seq) // c)
        dist = {k: seq.count(k) for k in range(1, c + 1)}
        if not all(lo <= v <= hi for v in dist.values()):
            bad.append(f"{name}: 正解位置が偏っている {dist} (各 {lo}〜{hi} 回)")
    for i in range(len(seq) - 2):
        if seq[i] == seq[i + 1] == seq[i + 2]:
            bad.append(f"{name}: 正解番号 {seq[i]} が 3 連続している (第{i + 1}問から)")


def main():
    files = sorted(glob.glob(os.path.join(HERE, "*", "*.json")))
    bad, n_books, n_qs = [], 0, 0
    for path in files:
        name = os.path.basename(path)
        try:
            b = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            bad.append(f"{name}: JSON が読めない ({e})")
            continue
        if not (isinstance(b, dict) and isinstance(b.get("questions"), list)
                and isinstance(b.get("book"), dict)):
            print(f"[SKIP] {name} (bundle でない)")
            continue
        n_books += 1
        qs = b["questions"]
        n_qs += len(qs)
        for e in ib.validate_questions_py(qs):
            bad.append(f"{name}: {e}")
        title = (b["book"].get("title") or "").strip()
        if not title:
            bad.append(f"{name}: タイトルが空")
        tl = b["book"].get("time_limit_min")
        if not (isinstance(tl, int) and tl >= 1):
            bad.append(f"{name}: time_limit_min が 1 以上の整数でない ({tl!r})")
        # --- 問題 PDF: 取り込み (find_pdf) と同じ完全一致名が隣に在ること ----
        stem = os.path.splitext(os.path.basename(b.get("source") or ""))[0]
        if not stem:
            bad.append(f"{name}: source が空 (PDF 名を組めない)")
        else:
            pdf = os.path.join(os.path.dirname(path), f"{stem}_問題.pdf")
            if not os.path.exists(pdf):
                bad.append(f"{name}: 問題 PDF が無い ({os.path.basename(pdf)})")
            elif os.path.getsize(pdf) == 0:
                bad.append(f"{name}: 問題 PDF が空ファイル")
            elif os.path.getsize(pdf) > ib.MAX_PDF_BYTES:
                bad.append(f"{name}: 問題 PDF が上限 50MB を超えている")
        subject = b["book"].get("subject")
        heads = BB.SUBJECT_HEADINGS.get(subject)
        if heads is None:
            bad.append(f"{name}: subject {subject!r} は使えない "
                       f"(使えるのは {sorted(BB.SUBJECT_HEADINGS)})")
        else:
            check_explanation_format(name, qs, heads, bad)
            check_answer_positions(name, qs, bad)
        print(f"[OK] {name} ({len(qs)}問 / {b['book'].get('subject')})"
              if not any(x.startswith(name) for x in bad) else
              f"[..] {name} ({len(qs)}問) に指摘あり (下に一覧)")
    if not n_books:
        print("NG: 検査対象の bundle が 1 つも無い (materials/*/ *.json)")
        return 1
    if bad:
        for x in bad:
            print(f"NG: {x}")
        print(f"違反 {len(bad)} 件")
        return 1
    print(f"=== ALL PASS (冊子 {n_books} / 設問 {n_qs}) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
