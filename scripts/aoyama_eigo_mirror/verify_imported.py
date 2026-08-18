#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取り込んだ青学実戦を DB から読み返し、正典・刷り上がり PDF と**全問**突き合わせる。

    python3 scripts/aoyama_eigo_mirror/verify_imported.py

★ import_books.py の照合表は「1 冊 1 問」しか出さない。それだけでは
  「2 問目以降がずれている」事故を見つけられないので、ここで全問を照合する
  (CLAUDE.md 2026-08-16「取り込み後の DB 読み返し」)。

見るもの (相互チェックの 3 層):
  ① 正典 ⇔ DB   … 全問の正解・選択肢数・出題形式
  ② DB ⇔ 刷り上がり … DB が持つ掲載ページに、その設問文が**実際に刷られているか**
  ③ 解説の貼り違え … 解説の先頭に書いた正解番号が correct_answer と矛盾しないか

★ このスクリプトは**読むだけ**。書き込みはしない。
   ログインは環境変数 EXAM_TEACHER_EMAIL / EXAM_TEACHER_PASSWORD。
"""
import json
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.join(HERE, "bundle")
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "book_exam")))
import import_books as ib  # noqa: E402


def sq(s):
    return re.sub(r"\s+", "", s)


def canon():
    """正典から 通し番号 → (正解, 選択肢数, 設問文) を作る。"""
    d = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    out = {}
    for q in d["I"]["questions"]:
        out[int(q["q_label"])] = (q["ans"], len(q["options"]), q["stem"])
    for it in d["IV"]["items"]:
        out[int(it["n"])] = (it["ans"], len(it["options"]), it["lines"][0]["text"])
    return out


def main():
    email = os.environ.get("EXAM_TEACHER_EMAIL")
    password = os.environ.get("EXAM_TEACHER_PASSWORD")
    if not (email and password):
        print("NG: EXAM_TEACHER_EMAIL / EXAM_TEACHER_PASSWORD が未設定")
        return 1
    bpath = os.path.join(BUNDLE, "青山学院大_2026英語_実戦.json")
    pdf = os.path.join(BUNDLE, "青山学院大_2026英語_実戦_問題.pdf")
    if not os.path.exists(bpath):
        print(f"NG: bundle がありません ({bpath})。make_bundle.py を先に回すこと")
        return 1
    bundle = json.load(open(bpath, encoding="utf-8"))
    want = canon()

    url, anon = ib.load_config()
    api = ib.Api(url, anon)
    api.login(email, password)

    title = bundle["book"]["title"]
    rows = api.call("GET", f"/rest/v1/books?title=eq.{urllib.parse.quote(title)}"
                           f"&select=id,page_count,is_published")
    if not rows:
        print(f"NG: DB に冊子がありません ({title})")
        return 1
    book = rows[0]
    qs = api.call("GET", f"/rest/v1/questions?book_id=eq.{book['id']}"
                         f"&select=number,page,answer_type,choice_count,correct_answer,"
                         f"explanation&order=number")
    db = {q["number"]: q for q in qs}

    pages = None
    if os.path.exists(pdf):
        from pypdf import PdfReader
        pages = [sq(p.extract_text() or "") for p in PdfReader(pdf).pages]

    bad = []
    if len(qs) != len(want):
        bad.append(f"設問数が DB {len(qs)} / 正典 {len(want)} で違う")
    for n in sorted(want):
        ans, n_opt, stem = want[n]
        r = db.get(n)
        if r is None:
            bad.append(f"第{n}問: DB に無い")
            continue
        if str(r["correct_answer"]) != str(ans):
            bad.append(f"第{n}問: DB の正解 {r['correct_answer']} が正典の {ans} と違う")
        if r.get("choice_count") != n_opt or r.get("answer_type") != "choice":
            bad.append(f"第{n}問: 形式が choice/{n_opt} でない "
                       f"({r.get('answer_type')}/{r.get('choice_count')})")
        # ② 刷り上がりとの照合
        if pages is not None:
            pg = r.get("page")
            if not (isinstance(pg, int) and 1 <= pg <= len(pages)):
                bad.append(f"第{n}問: ページ {pg} が総ページ {len(pages)} の外")
            elif sq(stem[:45]) not in pages[pg - 1]:
                bad.append(f"第{n}問: {pg} ページ目にこの設問文が刷られていない")
        # ③ 解説の貼り違え
        exp = r.get("explanation") or ""
        if len(exp) < 30:
            bad.append(f"第{n}問: 解説が短すぎる ({len(exp)} 字)")
        m = re.search(r"正解\s*([1-9])", exp)
        if m and m.group(1) != str(ans):
            bad.append(f"第{n}問: 解説が「正解 {m.group(1)}」と書いており正解 {ans} と矛盾する")

    if pages is None:
        print("-- 刷り上がり PDF が無いのでページ照合は省略 (make_bundle.py を回すこと)")
    if bad:
        for x in bad:
            print(f"NG: {x}")
        print(f"違反 {len(bad)} 件")
        return 1
    pub = "公開" if book.get("is_published") else "非公開"
    print(f"[OK] {title} — {len(qs)}問 / {book['page_count']}頁 / {pub}")
    print(f"=== ALL PASS (設問 {len(qs)} — 正典⇔DB⇔刷り上がり 全問一致) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
