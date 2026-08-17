#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""materials/ 以下の冊子 bundle (JSON + 問題 PDF) を全数検査する。

    python3 scripts/book_exam/materials/check_grammar_books.py

引数なし = **コミット済みの bundle 全部** (CLAUDE.md「引数なしの既定は刷るもの全部」)。
run_all_gates.py が check* として自動で拾う。何を見たかを必ず印字する。

見るもの:
  ・import_books.validate_questions_py と同じ規則 (正典の写しを再利用。二重管理しない)
  ・取り込みが前提にする問題 PDF ({source の stem}_問題.pdf) が隣に在ること・大きさ
  ・grammar 冊子の解説 4 セクション (コアイメージ → 文構造分析 → 正解の根拠 → 誤答 NG 理由)
  ・誤答 NG 理由の番号 (正解が NG に載っていない / 誤答 3 つが全部ある)
  ・正解位置の配り (10 問 4 択なら各番号 2〜3 回・同じ番号の 3 連続なし)

★ ここで見られるのは JSON に写った範囲だけ。選択肢の文字列と NG 理由の突き合わせは
  正典 (build_*.py の QUESTIONS) を持つ _grammar_build.verify() が build 時に行う。
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import import_books as ib  # noqa: E402  (validate_questions_py と PDF 上限の正典)

HEADINGS = ("## 🎯 コアイメージ", "## 🔬 文構造分析",
            "## 📍 正解の根拠", "## ❌ 誤答 NG 理由")


def check_grammar_format(name, qs, bad):
    for q in qs:
        at = f"{name} 第{q.get('number')}問"
        exp = q.get("explanation") or ""
        pos = -1
        for h in HEADINGS:
            p = exp.find(h)
            if p < 0:
                bad.append(f"{at}: 解説に「{h}」が無い")
            elif p < pos:
                bad.append(f"{at}: 解説のセクションの順番が崩れている ({h})")
            else:
                pos = p
        if q.get("answer_type") != "choice" or HEADINGS[3] not in exp:
            continue
        ans = str(q.get("correct_answer"))
        cc = q.get("choice_count") or 0
        ng = exp.split(HEADINGS[3])[-1]
        heads = {m.group(1) for m in re.finditer(r"^\s*([1-9])\.", ng, re.M)}
        if ans in heads:
            bad.append(f"{at}: 正解 {ans} が誤答 NG 理由に載っている")
        missing = [str(n) for n in range(1, cc + 1) if str(n) != ans and str(n) not in heads]
        if missing:
            bad.append(f"{at}: 誤答 {'/'.join(missing)} の NG 理由が無い")


def check_answer_positions(name, qs, bad):
    seq = [int(q["correct_answer"]) for q in qs
           if q.get("answer_type") == "choice"
           and re.fullmatch(r"[1-9][0-9]?", str(q.get("correct_answer") or ""))]
    if len(seq) == 10 and all((q.get("choice_count") == 4) for q in qs):
        dist = {k: seq.count(k) for k in (1, 2, 3, 4)}
        if not all(2 <= dist[k] <= 3 for k in dist):
            bad.append(f"{name}: 正解位置が偏っている {dist}")
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
        if b["book"].get("subject") == "grammar":
            check_grammar_format(name, qs, bad)
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
