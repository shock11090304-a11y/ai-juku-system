#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取り込み済みの冊子の**体裁だけ**を差し替える (刷り直した PDF とページ番号)。

    python3 scripts/eiken_junichi/mogi/refresh_pdf.py --dry-run   # ★まず予行
    python3 scripts/eiken_junichi/mogi/refresh_pdf.py             # 反映する

■ なぜ import_books.py ではだめか
    import_books.py は「設問が保存済みの同名冊子には触らない」。入れ直すには設問を
    消すことになるが、**設問を消すと受験記録 (attempts / answers) が道連れになる**。
    公開後に体裁を直したいだけなら、設問 ID を保ったまま
      ① storage の PDF を同じパスへ上書き ② books.page_count ③ questions.page
    の 3 つだけを更新すればよい。設問文・選択肢・正解・解説には触らない。

■ 安全の作り
    ・**正解が 1 問でも食い違ったら中止する**。体裁の差し替えのつもりで中身が
      変わっているなら、それは別の作業 (入れ直し) であって、ここでやってはいけない。
    ・設問数が合わない冊子も中止する。
    ・--dry-run で「何ページが何ページになるか」を先に出す。
    ・PDF は同じ storage パスへ x-upsert。孤児ファイルを作らない。

★ 公開中の冊子を書き換えるので、受験中の生徒がいない時間に回すこと。
"""
import argparse
import glob
import json
import os
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.join(HERE, "bundle")
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "book_exam")))
import import_books as ib  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="何を変えるかだけ出す")
    a = ap.parse_args()

    email = os.environ.get("EXAM_TEACHER_EMAIL")
    password = os.environ.get("EXAM_TEACHER_PASSWORD")
    if not (email and password):
        raise SystemExit("✗ EXAM_TEACHER_EMAIL / EXAM_TEACHER_PASSWORD が未設定")
    url, anon = ib.load_config()
    api = ib.Api(url, anon)
    api.login(email, password)

    from pypdf import PdfReader
    n_done = 0
    for bp in sorted(glob.glob(os.path.join(BUNDLE, "*.json"))):
        bundle = json.load(open(bp, encoding="utf-8"))
        title = bundle["book"]["title"]
        pdf = bp.replace(".json", "_問題.pdf")
        if not os.path.exists(pdf):
            raise SystemExit(f"✗ {os.path.basename(pdf)} が無い。make_bundle.py を先に回すこと")
        pages = len(PdfReader(pdf).pages)

        rows = api.call("GET", f"/rest/v1/books?title=eq.{urllib.parse.quote(title)}"
                               f"&select=id,page_count,pdf_path,is_published")
        if not rows:
            print(f"  — {title}: DB に無い (未取り込み)。import_books.py で入れること")
            continue
        book = rows[0]
        qs = api.call("GET", f"/rest/v1/questions?book_id=eq.{book['id']}"
                             f"&select=id,number,page,correct_answer&order=number")
        db = {q["number"]: q for q in qs}

        # --- 中止条件: 中身が変わっているなら体裁の差し替えではない -----------
        if len(qs) != len(bundle["questions"]):
            raise SystemExit(f"✗ {title}: 設問数が DB {len(qs)} / bundle "
                             f"{len(bundle['questions'])} で違う。体裁だけの差し替えではない")
        bad = [q["number"] for q in bundle["questions"]
               if q["number"] not in db
               or str(db[q["number"]]["correct_answer"]) != str(q["correct_answer"])]
        if bad:
            raise SystemExit(f"✗ {title}: 第{bad}問の正解が DB と違う。"
                             f"体裁の差し替えでなく入れ直しが要る")

        moved = [(q["number"], db[q["number"]]["page"], q["page"])
                 for q in bundle["questions"] if db[q["number"]]["page"] != q["page"]]
        pub = "公開中" if book.get("is_published") else "非公開"
        print(f"  ○ {title} [{pub}]")
        print(f"      総ページ {book['page_count']} → {pages} / ページが動く設問 {len(moved)} 問")
        if a.dry_run:
            for n, o, w in moved[:8]:
                print(f"        第{n}問 p{o} → p{w}")
            if len(moved) > 8:
                print(f"        … 他 {len(moved) - 8} 問")
            continue

        # --- ① PDF を同じパスへ上書き ---------------------------------------
        path = book.get("pdf_path") or f"books/{book['id']}.pdf"
        with open(pdf, "rb") as f:
            api.call("POST", f"/storage/v1/object/book-pdfs/{path}", raw=f.read(),
                     headers={"Content-Type": "application/pdf", "x-upsert": "true"})
        # --- ② 総ページ数 ---------------------------------------------------
        upd = api.call("PATCH", f"/rest/v1/books?id=eq.{book['id']}",
                       {"pdf_path": path, "page_count": pages},
                       headers={"Prefer": "return=representation"})
        if not upd:
            raise SystemExit(f"✗ {title}: page_count を更新できたか確認できない (返却 0 行)")
        # --- ③ 動いた設問のページだけ更新 -----------------------------------
        for n, _old, want in moved:
            r = api.call("PATCH", f"/rest/v1/questions?id=eq.{db[n]['id']}",
                         {"page": want}, headers={"Prefer": "return=representation"})
            if not r:
                raise SystemExit(f"✗ {title} 第{n}問: ページを更新できたか確認できない")
        print(f"      → PDF 差し替え済み / ページ {len(moved)} 問を更新")
        n_done += 1

    if a.dry_run:
        print("\n[予行] 何も書き込んでいません。反映するなら --dry-run を外してください。")
    else:
        print(f"\n{n_done} 冊を更新しました。verify_imported.py で読み返してください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
