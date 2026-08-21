#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テストの問題作成マニュアル (docs/kamitest-manual/) と**実物のコード**のずれを落とす。

    python3 scripts/book_exam/check_kamitest_manual.py

引数なし = **マニュアル全部** (CLAUDE.md「引数なしの既定は刷るもの全部」)。
run_all_gates.py が check* として自動で拾う。何を見たかを必ず印字する。

■ なぜ要るか
    マニュアルは書いた日には正しい。壊れるのは**コードが動いたとき**で、
    しかも壊れても誰も気づかない。「マニュアルどおりに作ったのに取り込みが落ちる」は
    マニュアルを読んだ人の時間を丸ごと捨てる。CLAUDE.md の
    「ルールの置き場所はリポジトリの中に限る」の実装。

■ 何を突き合わせるか (マニュアル側は <!-- canon:… --> で囲った所だけを読む)
    ・subject の閉じた集合            ↔ exam-app/exam-book-admin-model.mjs の SUBJECTS
    ・選択肢の数の範囲・PDF の上限    ↔ 同 MIN_CHOICES / MAX_CHOICES / MAX_PDF_BYTES
    ・bundle の設問キー               ↔ import_books.question_payload_py が作るキー
    ・科目名 → 既定の制限時間         ↔ import_books.TIME_LIMIT_MIN
    ・教科ごとの解説の見出し           ↔ materials/_book_build.py の SUBJECT_HEADINGS
    ・英語の 4 見出しの二重定義        ↔ _grammar_build.HEADINGS と一致しているか
    ・subject の取りこぼし             ↔ 'other' 以外の全 subject に教科別ページがあるか
    ・「解説は素のテキスト」の根拠     ↔ exam-book-answers.mjs / exam-book.css の実物
    ・教科別マニュアルの subject 値   ↔ SUBJECTS に実在するか
    ・マニュアルが挙げるファイルパス   ↔ 実在するか (置き場所を移したら落ちる)

★ ここが落ちたときに直すのは**マニュアルの側**が既定。コードを合わせに行くのは、
  コードの変更がそもそも意図しないものだったときだけ。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MANUAL_DIR = os.path.join(ROOT, "docs", "kamitest-manual")
ADMIN_MJS = os.path.join(ROOT, "exam-app", "exam-book-admin-model.mjs")
ANSWERS_MJS = os.path.join(ROOT, "exam-app", "exam-book-answers.mjs")
BOOK_CSS = os.path.join(ROOT, "exam-app", "exam-book.css")

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "materials"))
import import_books as ib              # noqa: E402  (取り込みの正典)
import _grammar_build as G             # noqa: E402  (英文法 15 冊のビルダー)
import _book_build as BB               # noqa: E402  (全教科共通ビルダーの正典)

# 教科別マニュアル。README から張られていることも見る。
SUBJECT_PAGES = ("eigo.md", "sugaku.md", "kokugo.md", "rika.md", "shakai.md")

# マニュアルが挙げるパスの拾い方。リポジトリの実在する根から始まるものだけ見る
# (「〈冊子名〉」「*」を含む書きかけの例は、この形に合わないので自然に外れる)。
PATH_RE = re.compile(
    r"(?:scripts|exam-app|supabase|docs|seed-data|server|api)"
    r"/[A-Za-z0-9_./-]+\.(?:mjs|json|html|css|sql|py|js|md|sh)")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def canon(text, name, path, bad):
    """<!-- canon:name --> … <!-- /canon:name --> の中身。無ければ違反。"""
    m = re.search(rf"<!--\s*canon:{name}\s*-->(.*?)<!--\s*/canon:{name}\s*-->",
                  text, re.S)
    if not m:
        bad.append(f"{os.path.basename(path)}: <!-- canon:{name} --> のブロックが無い")
        return None
    return m.group(1)


def mjs_const(src, name, bad):
    m = re.search(rf"export const {name}\s*=\s*(\d+)", src)
    if not m:
        bad.append(f"exam-book-admin-model.mjs: {name} を読み取れない (形が変わった)")
        return None
    return int(m.group(1))


def mjs_subjects(src, bad):
    m = re.search(r"export const SUBJECTS\s*=\s*Object\.freeze\(\[(.*?)\]\)", src, re.S)
    if not m:
        bad.append("exam-book-admin-model.mjs: SUBJECTS を読み取れない (形が変わった)")
        return []
    return re.findall(r"\{\s*value:\s*'([^']+)'\s*,\s*label:\s*'([^']+)'\s*\}", m.group(1))


# =============================================================================
# 個別の照合
# =============================================================================
def check_subjects(readme, subjects, bad):
    """README の subject 表 ↔ SUBJECTS (値も表示名も順番も)。"""
    block = canon(readme, "subjects", "README.md", bad)
    if block is None:
        return
    rows = [(m.group(1), m.group(2).strip()) for m in
            re.finditer(r"^\|\s*`([a-z]+)`\s*\|\s*(.+?)\s*\|\s*$", block, re.M)]
    if rows != subjects:
        bad.append("README.md: subject の一覧が exam-book-admin-model.mjs の "
                   f"SUBJECTS と違う\n    マニュアル: {rows}\n    実物      : {subjects}")


def check_limits(readme, src, bad):
    """選択肢の数の範囲と PDF の上限が README の本文に正しく書いてあるか。"""
    lo = mjs_const(src, "MIN_CHOICES", bad)
    hi = mjs_const(src, "MAX_CHOICES", bad)
    cap = mjs_const(src, "MAX_PDF_BYTES", bad)
    if lo is None or hi is None or cap is None:
        return
    if f"{lo}〜{hi}" not in readme:
        bad.append(f"README.md: 選択肢の数の範囲「{lo}〜{hi}」が本文に無い "
                   f"(MIN_CHOICES / MAX_CHOICES が変わった?)")
    mb = cap // 1024 // 1024
    if f"{mb}MB" not in readme:
        bad.append(f"README.md: PDF の上限「{mb}MB」が本文に無い (MAX_PDF_BYTES={cap})")
    if cap != ib.MAX_PDF_BYTES:
        bad.append(f"exam-book-admin-model.mjs と import_books.py で PDF の上限が違う "
                   f"({cap} / {ib.MAX_PDF_BYTES})")


def check_question_keys(readme, bad):
    """README の設問サンプル ↔ import_books.question_payload_py が作るキー。"""
    block = canon(readme, "question-keys", "README.md", bad)
    if block is None:
        return
    m = re.search(r"```json\s*(\{.*?\})\s*```", block, re.S)
    if not m:
        bad.append("README.md: canon:question-keys の中に json ブロックが無い")
        return
    try:
        sample = json.loads(m.group(1))
    except Exception as e:
        bad.append(f"README.md: canon:question-keys の JSON が壊れている ({e})")
        return
    want = sorted(k for k in ib.question_payload_py({}, "x") if k != "book_id")
    got = sorted(sample)
    if got != want:
        bad.append(f"README.md: 設問のキーが取り込みの写像と違う\n"
                   f"    マニュアル: {got}\n    実物      : {want}")
    errs = ib.validate_questions_py([sample])
    if errs:
        bad.append("README.md: 設問のサンプルが取り込みの検証を通らない: "
                   + " / ".join(errs))


def check_time_limits(readme, bad):
    """README の「科目名 分」 ↔ import_books.TIME_LIMIT_MIN。"""
    block = canon(readme, "time-limits", "README.md", bad)
    if block is None:
        return
    got = {m.group(1): int(m.group(2))
           for m in re.finditer(r"([^\s/]+)\s+(\d+)", block)}
    if got != ib.TIME_LIMIT_MIN:
        bad.append(f"README.md: 既定の制限時間が import_books.TIME_LIMIT_MIN と違う\n"
                   f"    マニュアル: {got}\n    実物      : {ib.TIME_LIMIT_MIN}")


HEAD_TOKEN = re.compile(r"^\s*(##\s+\S.*?)\s*$|^\s*(【[^】]+】)")


def heading_tokens(block):
    """見出しだけを行頭から拾う (英語は `## …`、他教科は `【…】`)。"""
    out = []
    for ln in block.splitlines():
        m = HEAD_TOKEN.match(ln)
        if m:
            out.append((m.group(1) or m.group(2)).strip())
    return tuple(out)


def check_headings(texts, declared, bad):
    """各教科ページの見出し ↔ _book_build.SUBJECT_HEADINGS (順番も)。"""
    for name, text in texts.items():
        if name == "README.md":
            continue
        block = canon(text, "headings", name, bad)
        if block is None:
            continue
        values = declared.get(name) or []
        want = {v: BB.SUBJECT_HEADINGS[v] for v in values
                if v in BB.SUBJECT_HEADINGS}
        if len(set(want.values())) != 1:
            bad.append(f"{name}: 宣言している subject {values} の解説見出しが "
                       f"_book_build.SUBJECT_HEADINGS で一致していない "
                       f"(1 ページにまとめられない)")
            continue
        expect = next(iter(want.values()))
        got = heading_tokens(block)
        if got != expect:
            bad.append(f"{name}: 解説の見出しが _book_build.SUBJECT_HEADINGS と違う\n"
                       f"    マニュアル: {got}\n    実物      : {expect}")


def check_builder_parity(bad):
    """英語の 4 見出しが 2 か所にある。ずれたら片方の冊子だけ落ちる。"""
    if G.HEADINGS != BB.SUBJECT_HEADINGS["grammar"]:
        bad.append(f"_grammar_build.HEADINGS と _book_build.SUBJECT_HEADINGS['grammar'] "
                   f"が違う\n    旧: {G.HEADINGS}\n    新: "
                   f"{BB.SUBJECT_HEADINGS['grammar']}")


def check_subject_coverage(subjects, declared, bad):
    """'other' 以外の subject に、必ずどれかの教科別ページがあるか。"""
    covered = {v for vs in declared.values() for v in vs}
    for value, label in subjects:
        if value == "other":
            continue
        if value not in covered:
            bad.append(f"subject '{value}' ({label}) を扱う教科別ページが無い "
                       f"(docs/kamitest-manual/ に足すか、既存ページの "
                       f"canon:subject-value に加える)")
    for value in sorted(covered):
        if value not in BB.SUBJECT_HEADINGS:
            bad.append(f"subject '{value}' が _book_build.SUBJECT_HEADINGS に無い "
                       f"(ビルダーが解説の見出しを知らない)")


def check_plain_text_claim(bad):
    """「解説は素のテキストで出る」の根拠が実装に残っているか。

    ★ ここが変わる (Markdown を描くようになる) と、マニュアルの §5 と
      教科別の「LaTeX を書くな」「【】で囲め」が全部ひっくり返る。
    """
    ans = read(ANSWERS_MJS)
    if not re.search(r"\.textContent\s*=\s*r\.explanation", ans):
        bad.append("exam-book-answers.mjs: explanation を textContent で入れる行が無い。"
                   "解説の表示が変わったならマニュアル §5 と教科別の記法を全部見直すこと")
    css = read(BOOK_CSS)
    if not re.search(r"\.res-exp\s*\{[^}]*white-space:\s*pre-wrap", css):
        bad.append("exam-book.css: .res-exp の white-space: pre-wrap が無い。"
                   "解説の改行が潰れるならマニュアル §5 を見直すこと")


def check_subject_pages(readme, subjects, bad, seen, declared):
    """教科別マニュアルの存在・README からのリンク・宣言している subject 値。"""
    values = {v for v, _ in subjects}
    for name in SUBJECT_PAGES:
        path = os.path.join(MANUAL_DIR, name)
        if not os.path.exists(path):
            bad.append(f"docs/kamitest-manual/{name} が無い")
            continue
        if f"({name})" not in readme:
            bad.append(f"README.md: {name} へのリンクが無い (一覧から落ちている)")
        text = read(path)
        seen[name] = text
        block = canon(text, "subject-value", name, bad)
        if block is None:
            continue
        vals = re.findall(r"`([a-z]+)`", block)
        declared[name] = vals
        if not vals:
            bad.append(f"{name}: canon:subject-value に `値` が 1 つも無い")
        for v in vals:
            if v not in values:
                bad.append(f"{name}: subject '{v}' は SUBJECTS に無い "
                           f"(使えるのは {sorted(values)})")
    extra = [f for f in sorted(os.listdir(MANUAL_DIR))
             if f.endswith(".md") and f != "README.md" and f not in SUBJECT_PAGES]
    for f in extra:
        bad.append(f"docs/kamitest-manual/{f} がこのゲートの一覧に無い "
                   f"(教科を足したら check_kamitest_manual.py の SUBJECT_PAGES にも足す)")


def check_paths(texts, bad):
    """マニュアルが挙げるファイルが実在するか。"""
    n = 0
    for name, text in texts.items():
        for rel in sorted(set(PATH_RE.findall(text))):
            n += 1
            if not os.path.exists(os.path.join(ROOT, rel)):
                bad.append(f"{name}: 存在しないパスを指している ({rel})")
    return n


# =============================================================================
def main():
    bad = []
    if not os.path.isdir(MANUAL_DIR):
        print(f"NG: {MANUAL_DIR} が無い")
        return 1
    readme_path = os.path.join(MANUAL_DIR, "README.md")
    if not os.path.exists(readme_path):
        print("NG: docs/kamitest-manual/README.md (共通編) が無い")
        return 1

    readme = read(readme_path)
    src = read(ADMIN_MJS)
    subjects = mjs_subjects(src, bad)
    texts = {"README.md": readme}

    check_subjects(readme, subjects, bad)
    check_limits(readme, src, bad)
    check_question_keys(readme, bad)
    check_time_limits(readme, bad)
    check_plain_text_claim(bad)
    declared = {}
    check_subject_pages(readme, subjects, bad, texts, declared)
    check_headings(texts, declared, bad)
    check_builder_parity(bad)
    check_subject_coverage(subjects, declared, bad)
    n_paths = check_paths(texts, bad)

    print("=== 神テスト 問題作成マニュアルの検査 ===")
    for name in ["README.md"] + list(SUBJECT_PAGES):
        mark = "[OK]" if name in texts else "[--]"
        print(f"  {mark} docs/kamitest-manual/{name}")
    print(f"  照合先: exam-book-admin-model.mjs (SUBJECTS {len(subjects)} 件 / 上限) / "
          f"import_books.py (設問キー・制限時間) / "
          f"_book_build.py (解説見出し {len(BB.SUBJECT_HEADINGS)} 教科) + "
          f"_grammar_build.py (英語の二重定義) / "
          f"exam-book-answers.mjs + exam-book.css (解説の表示)")
    print(f"  マニュアルが挙げるパス {n_paths} 件の実在を確認")

    if bad:
        for x in bad:
            print(f"NG: {x}")
        print(f"違反 {len(bad)} 件")
        return 1
    print("=== ALL PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
