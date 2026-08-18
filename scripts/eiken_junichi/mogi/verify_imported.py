#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取り込んだ英検模試を DB から読み返し、作問の正典と**全問**突き合わせる。

    python3 scripts/eiken_junichi/mogi/verify_imported.py

★ import_books.py の照合表は「1 冊 1 問」しか出さない。それだけでは
  「2 問目以降がずれている」事故を見つけられないので、ここで全問を照合する
  (CLAUDE.md 2026-08-16「取り込み後の DB 読み返し」)。

見るもの:
  ・冊子が存在し、非公開か、ページ数と制限時間が合っているか
  ・設問数が正典と一致するか
  ・**全問の正解**が data_no*.json の答えと一致するか (1 問でも違えば落とす)
  ・**全問の掲載ページ**が bundle と一致し、page ≤ page_count か
  ・解説が空でないか、解説の先頭に書いた正解番号が correct_answer と矛盾しないか
    (「解説だけ別の問題のものを貼った」を捕まえる)

★ このスクリプトは**読むだけ**。書き込みはしない。
   ログインは環境変数 EXAM_TEACHER_EMAIL / EXAM_TEACHER_PASSWORD。
"""
import glob
import json
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.join(HERE, "bundle")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "book_exam"))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "book_exam")))
import import_books as ib  # noqa: E402


def expected_answers(data_path):
    """作問の正典 (data_no*.json) から、通し番号 → 正解番号 (1 起算) を作る。"""
    d = json.load(open(data_path, encoding="utf-8"))
    out, n = {}, 1
    for it in d["part1"]:
        out[n] = it["answer"] + 1; n += 1
    for ps in d["part2"]:
        for b in ps["blanks"]:
            out[n] = b["answer"] + 1; n += 1
    for ps in d["part3"]:
        for q in ps["questions"]:
            out[n] = q["answer"] + 1; n += 1
    return d, out


def main():
    email = os.environ.get("EXAM_TEACHER_EMAIL")
    password = os.environ.get("EXAM_TEACHER_PASSWORD")
    if not (email and password):
        print("NG: EXAM_TEACHER_EMAIL / EXAM_TEACHER_PASSWORD が未設定")
        return 1
    url, anon = ib.load_config()
    api = ib.Api(url, anon)
    api.login(email, password)

    bad, n_books, n_qs = [], 0, 0
    for bpath in sorted(glob.glob(os.path.join(BUNDLE, "*.json"))):
        bundle = json.load(open(bpath, encoding="utf-8"))
        title = bundle["book"]["title"]
        no = re.search(r"第(\d+)回", title).group(1)
        data_path = os.path.join(HERE, f"data_no{int(no):02d}.json")
        if not os.path.exists(data_path):
            bad.append(f"{title}: 作問の正典 {os.path.basename(data_path)} が無い")
            continue
        _d, want = expected_answers(data_path)

        q = urllib.parse.quote(title)
        rows = api.call("GET", f"/rest/v1/books?title=eq.{q}"
                               f"&select=id,title,page_count,time_limit_sec,is_published")
        if not rows:
            bad.append(f"{title}: DB に冊子が無い")
            continue
        book = rows[0]
        n_books += 1
        if book.get("is_published"):
            print(f"[INFO] {title} は公開済み")
        want_sec = (bundle["book"]["time_limit_min"] or 0) * 60
        if book.get("time_limit_sec") != want_sec:
            bad.append(f"{title}: 制限時間が {book.get('time_limit_sec')} 秒 (期待 {want_sec})")

        qs = api.call("GET", f"/rest/v1/questions?book_id=eq.{book['id']}"
                             f"&select=number,page,answer_type,choice_count,correct_answer,"
                             f"points,unit_tag,explanation&order=number")
        n_qs += len(qs)
        if len(qs) != len(bundle["questions"]):
            bad.append(f"{title}: DB の設問数 {len(qs)} が bundle の {len(bundle['questions'])} と違う")
        by_no = {r["number"]: r for r in qs}
        b_by_no = {r["number"]: r for r in bundle["questions"]}
        for n in sorted(want):
            r = by_no.get(n)
            if r is None:
                bad.append(f"{title} 第{n}問: DB に無い")
                continue
            # ① 正解 — 作問の正典と直接照合する (bundle 経由の写し間違いも捕まる)
            if str(r["correct_answer"]) != str(want[n]):
                bad.append(f"{title} 第{n}問: DB の正解 {r['correct_answer']} が"
                           f" 正典の {want[n]} と違う")
            # ② ページ
            wb = b_by_no.get(n, {})
            if r.get("page") != wb.get("page"):
                bad.append(f"{title} 第{n}問: DB のページ {r.get('page')} が"
                           f" bundle の {wb.get('page')} と違う")
            if r.get("page") and book.get("page_count") and r["page"] > book["page_count"]:
                bad.append(f"{title} 第{n}問: ページ {r['page']} が総ページ {book['page_count']} を超える")
            # ③ 形式
            if r.get("answer_type") != "choice" or r.get("choice_count") != 4:
                bad.append(f"{title} 第{n}問: 形式が choice/4 でない "
                           f"({r.get('answer_type')}/{r.get('choice_count')})")
            # ④ 解説 — 空でなく、先頭に書いた正解番号が correct_answer と一致するか
            exp = r.get("explanation") or ""
            if len(exp) < 30:
                bad.append(f"{title} 第{n}問: 解説が短すぎる ({len(exp)} 字)")
            m = re.search(r"正解\s*([1-4])", exp)
            if m and m.group(1) != str(want[n]):
                bad.append(f"{title} 第{n}問: 解説が「正解 {m.group(1)}」と書いており"
                           f" 正解 {want[n]} と矛盾する (別問題の解説の貼り違え)")
        if not any(x.startswith(title) for x in bad):
            print(f"[OK] {title} — {len(qs)}問 / {book['page_count']}頁 / "
                  f"{'公開' if book.get('is_published') else '非公開'} / 全問一致")
    if not n_books:
        bad.append("DB から冊子を 1 冊も読めなかった")
    if bad:
        for x in bad:
            print(f"NG: {x}")
        print(f"違反 {len(bad)} 件")
        return 1
    print(f"=== ALL PASS (冊子 {n_books} / 設問 {n_qs} — 正典⇔DB 全問一致) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
