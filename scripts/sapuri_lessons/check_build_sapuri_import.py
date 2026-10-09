#!/usr/bin/env python3
"""📺 build_sapuri_import.py (スタサプ 第N講の取込用 JSON を作る builder) の自己テスト (run_all_gates.py が拾う)。

★本物の講義一覧は使わない (題名は本番 DB だけ = 塾長決定 D1)。架空の TSV・タグ付け・定数ファイル (「テスト講義A」等) を
  tempfile の使い捨てディレクトリに作り、builder を別プロセスで回して出力を確かめる。リポジトリには 1 文字も書かない。
  標準ライブラリだけ・DB / 通信なし・数秒で終わる。

確かめること:
  1. 講の取り出し: 第N講の番号 / 補講と第0講を捨てる / 同じ講の複数チャプターは 1 講 / 80 字で切る / < > を全角に /
     EKZB は topic_code の講番号で束ねて PART・Chapter を外し「／」で連結 / 分割講座 (第41講〜) の番号
  2. 講座の選び方: has_lessons=False は書かない / 講数が first..last と合わない講座は書かずに理由を残す
  3. タグ: 別名を語彙に展開 / 語彙外・科目キー外・講の無い seq は捨てて数える / topic は NFKC・範囲外の seq と 4 講以上は捨てる
  4. 講師名: 題名に氏名・姓だけ・名だけ → 何も書かずに失敗 (名前を表示しない) / topic は氏名そのものだけで失敗
  5. パス: リポジトリの中・別の git 作業ツリーの中の --out-dir を拒否 (フォルダも作らない)
  6. 前回の出力は消さない (summary の stale_files) / --dry-run は書かない / 2 回回して同じ / --help の文言 / 通信・URL を持たない
  7. 本物の server/main.py から SAPURI_COURSES 等を ast で読める (講座コードがファイル名に使える形)

実行: python3 scripts/sapuri_lessons/check_build_sapuri_import.py   # exit 0 = 合格 / 1 = 違反あり
"""
import ast
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BUILDER = os.path.join(HERE, "build_sapuri_import.py")

problems = []
passed = [0]


def ok(cond, label):
    if cond:
        passed[0] += 1
    else:
        problems.append(label)
        print(f"  ❌ {label}")


PRESENTER = "架空 太郎"
TSV_COLS = ["course_set_name", "grade_code", "subject_name", "subject_code", "course_name", "course_code",
            "course_description", "presenter_name", "topic_name", "topic_code", "chapter_title", "chapter_code",
            "chapter_position", "video_id"]
LONG = "テスト講義の長い題名" * 10      # 100 字

FAKE_MAIN = '''
SAPURI_COURSES = [
    {"code": "TESTA0001", "name": "テスト講座A", "first": 1, "last": 4, "has_lessons": True},
    {"code": "EKZBTEST01", "name": "テスト講座E", "first": 1, "last": 2, "has_lessons": True},
    {"code": "TESTB0002", "name": "テスト講座B", "first": 1, "last": 4, "has_lessons": True},
    {"code": "TESTC0003", "name": "テスト講座C", "first": 1, "last": 2, "has_lessons": False},
    {"code": "TESTD0004_2", "name": "テスト講座D", "first": 41, "last": 42, "has_lessons": True},
]
SAPURI_SUBJECT_KEYS = ("eng_grammar", "math")
SAPURI_TAG_VOCAB = {"eng_grammar": ["時制", "倒置", "強調"], "math": ["数列"]}
SAPURI_TAG_ALIASES = {"eng_grammar": {"倒置・強調": ["倒置", "強調"]}}
def _not_a_constant():
    SAPURI_COURSES = []
'''


def tsv_rows(extra_title=None):
    rows = []

    def add(cc, topic, tcode, chap="1"):
        rows.append({"course_set_name": "テスト", "grade_code": "h3", "subject_name": "英語", "subject_code": "en",
                     "course_name": "テスト講座", "course_code": cc, "course_description": "架空の説明",
                     "presenter_name": PRESENTER, "topic_name": topic, "topic_code": tcode,
                     "chapter_title": "チャプター", "chapter_code": tcode + chap, "chapter_position": chap,
                     "video_id": "v" + tcode + chap})
    add("TESTA0001", "第0講 テストの導入", "TA00")
    add("TESTA0001", "第1講 テスト講義A", "TA01", "1")
    add("TESTA0001", "第1講 テスト講義A", "TA01", "2")          # 同じ講の 2 チャプター目
    add("TESTA0001", "第２講　テスト講義B", "TA02")              # 全角数字・全角空白 (NFKC)
    add("TESTA0001", extra_title or "第3講 テスト講義C", "TA03")
    add("TESTA0001", "第4講 " + LONG, "TA04")
    add("TESTA0001", "補講 テストのまとめ", "TA99")
    add("EKZBTEST01", "PART1 テスト導入", "EKGB010010")          # 講0 → 捨てる
    add("EKZBTEST01", "PART1 テスト前半", "EKGB010110")
    add("EKZBTEST01", "Chapter2 テスト後半", "EKGB010120")
    add("EKZBTEST01", "PART1 テスト第二", "EKGB010210")
    add("EKZBTEST01", "補講 テスト補足", "EKGB010220")            # 補講の part は捨てる
    for i in (1, 2, 3):                                           # 4 講のはずが 3 講 → 講座ごと飛ばす
        add("TESTB0002", f"第{i}講 テスト講義B{i}", f"TB0{i}")
    add("TESTC0003", "第1講 テスト講義C1", "TC01")
    add("TESTC0003", "第2講 テスト講義C2", "TC02")
    add("TESTD0004_2", "第41講 テスト講義<X>", "TD41")
    add("TESTD0004_2", "第42講 テスト講義Y", "TD42")
    return rows


def tags_fixture(extra_topic=None):
    topics = [{"topic": "時制（現在完了）", "seqs": [1]},
              {"topic": "範囲外", "seqs": [7]},
              {"topic": "重ね", "seqs": [1, 2]},
              {"topic": "重ね", "seqs": [3, 4]},                  # 合わせて 4 講 → 捨てる
              {"topic": "合わせる", "seqs": [1]},
              {"topic": "合わせる", "seqs": [2, 1]}]              # 合わせて [1, 2]
    if extra_topic:
        topics.append({"topic": extra_topic, "seqs": [1]})
    return [
        {"id": "eng_grammar__TESTA0001",
         "lesson_tags": [{"seq": 1, "tags": ["時制"]}, {"seq": 2, "tags": ["倒置・強調", "未知のタグ"]},
                         {"seq": 9, "tags": ["時制"]}],
         "topic_lessons": topics},
        {"id": "chemistry__TESTA0001", "lesson_tags": [{"seq": 1, "tags": ["理論化学"]}], "topic_lessons": []},
        {"id": "math__TESTB0002", "lesson_tags": [{"seq": 1, "tags": ["数列"]}], "topic_lessons": []},
        {"id": "eng_grammar__EKZBTEST01", "lesson_tags": [{"seq": 2, "tags": ["強調"]}], "topic_lessons": []},
    ]


def write_fixture(d, extra_title=None, extra_topic=None):
    tsv = os.path.join(d, "fixture.tsv")
    with open(tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TSV_COLS, delimiter="\t")
        w.writeheader()
        for r in tsv_rows(extra_title):
            w.writerow(r)
    tags = os.path.join(d, "tags.json")
    with open(tags, "w", encoding="utf-8") as f:
        json.dump(tags_fixture(extra_topic), f, ensure_ascii=False)
    main_py = os.path.join(d, "fake_main.py")
    with open(main_py, "w", encoding="utf-8") as f:
        f.write(FAKE_MAIN)
    return tsv, tags, main_py


def run(*args):
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    r = subprocess.run([sys.executable, "-B", BUILDER] + list(args), capture_output=True, encoding="utf-8",
                       errors="replace", timeout=60, env=env)
    return r.returncode, r.stdout + r.stderr


def load(d, name):
    with open(os.path.join(d, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    tmp = tempfile.mkdtemp(prefix="sapuri-builder-selftest-")
    try:
        return _main(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _main(tmp):
    print("=== 📺 スタサプ builder の自己テスト (架空のデータ) ===")
    src_dir = os.path.join(tmp, "src")
    os.makedirs(src_dir)
    tsv, tags, main_py = write_fixture(src_dir)
    out = os.path.join(tmp, "out")
    os.makedirs(out)
    with open(os.path.join(out, "sapuri_lessons_OLD0000.json"), "w", encoding="utf-8") as f:
        f.write("{}")

    code, text = run("--tsv", tsv, "--tags", tags, "--out-dir", out, "--main", main_py)
    ok(code == 0, f"架空データで builder が通る (exit {code})")
    if code != 0:
        print("    " + text.strip().replace("\n", "\n    ")[:800])
        return 1
    files = sorted(os.listdir(out))
    ok(files == ["sapuri_lessons_EKZBTEST01.json", "sapuri_lessons_OLD0000.json", "sapuri_lessons_TESTA0001.json",
                 "sapuri_lessons_TESTD0004_2.json", "summary.json"],
       f"書くのは講数の合う has_lessons 講座だけ・前回の出力は消さない: {files}")
    ok(not any(n.endswith(".tmp") for n in files), "書きかけの .tmp が残らない")

    a = load(out, "sapuri_lessons_TESTA0001.json")
    ok(a["course_code"] == "TESTA0001", "course_code")
    ok(a["source"] == "studysapuri.jp 通年講座一覧 (2022-06 時点の公開データ)", "source の文言")
    ok(isinstance(a.get("built_at"), str) and a["built_at"].endswith("+09:00"), "built_at は JST")
    les = {x["seq"]: x for x in a["lessons"]}
    ok(sorted(les) == [1, 2, 3, 4], f"第0講・補講を捨て、同じ講の 2 チャプターを 1 講に: {sorted(les)}")
    ok(les.get(1, {}).get("title") == "テスト講義A", "題名 (第N講 を外す)")
    ok(les.get(2, {}).get("title") == "テスト講義B", "全角の講番号・空白を NFKC でそろえる")
    t4 = les.get(4, {}).get("title", "")
    ok(len(t4) == 80 and t4.endswith("…") and t4.startswith("テスト講義の長い題名"), f"80 字で切る (len {len(t4)})")
    ok(les.get(1, {}).get("tags") == [{"subject_key": "eng_grammar", "tag": "時制"}], "タグ (語彙内)")
    ok(les.get(2, {}).get("tags") == [{"subject_key": "eng_grammar", "tag": "倒置"},
                                      {"subject_key": "eng_grammar", "tag": "強調"}], "別名を 2 タグに展開・語彙外を捨てる")
    ok(les.get(3, {}).get("tags") == [], "タグの無い講は空配列")
    ok(set(a) == {"course_code", "source", "built_at", "lessons", "topic_lessons"}, f"最上位の鍵: {sorted(a)}")
    ok(all(set(x) == {"seq", "title", "tags"} for x in a["lessons"]), "講の鍵は seq / title / tags だけ")
    tl = {(x["subject_key"], x["topic_norm"]): x["seqs"] for x in a["topic_lessons"]}
    ok(tl == {("eng_grammar", "時制(現在完了)"): [1], ("eng_grammar", "合わせる"): [1, 2]},
       f"topic は NFKC・範囲外の seq と 4 講以上は捨て・同じ topic は合わせる: {tl}")

    e = load(out, "sapuri_lessons_EKZBTEST01.json")
    el = {x["seq"]: x for x in e["lessons"]}
    ok(sorted(el) == [1, 2], f"EKZB: 講0を捨て topic_code の講番号で束ねる: {sorted(el)}")
    ok(el.get(1, {}).get("title") == "テスト前半／テスト後半", "EKZB: PART・Chapter を外して「／」で連結")
    ok(el.get(2, {}).get("title") == "テスト第二", "EKZB: 補講の part を捨てる")
    ok(el.get(2, {}).get("tags") == [{"subject_key": "eng_grammar", "tag": "強調"}], "EKZB のタグ")

    dd = load(out, "sapuri_lessons_TESTD0004_2.json")
    ok([x["seq"] for x in dd["lessons"]] == [41, 42], "分割講座は第41講からの番号のまま")
    ok(dd["lessons"][0]["title"] == "テスト講義＜X＞", "< > は全角にする (取込 API は HTML を拒否)")

    s = load(out, "summary.json")
    tot = s.get("totals", {})
    ok(tot.get("courses_written") == 3 and tot.get("courses_skipped") == 1, f"summary の講座数: {tot}")
    ok([x["course_code"] for x in s.get("skipped", [])] == ["TESTB0002"] and "講数" in s["skipped"][0]["reason"],
       "講数の合わない講座は理由つきで飛ばす")
    ok(tot.get("lessons") == 8, f"summary の講数 (4+2+2): {tot.get('lessons')}")
    ok(tot.get("dropped_tags") == 1 and s["dropped"]["tags"] == {"eng_grammar:未知のタグ": 1}, "語彙外のタグを数える")
    ok(tot.get("dropped_subject_keys") == 1 and s["dropped"]["subject_keys"] == {"chemistry": 1}, "科目キー外を数える")
    ok(tot.get("dropped_lesson_tags_no_lesson") == 1, "講の無い seq へのタグを数える")
    ok(s["dropped"]["topics"] == {"seq": 1, "empty": 0, "too_many": 1, "too_long": 0}, f"topic の捨て: {s['dropped']['topics']}")
    ok(s.get("tagged_courses_not_written") == [{"course_code": "TESTB0002",
                                                "reason": "講座を書かない (has_lessons=False か講数不一致)"}],
       "書かない講座のタグ付けを報告")
    ok(s.get("stale_files") == ["sapuri_lessons_OLD0000.json"], "前回の出力を stale_files に出す")
    blob = json.dumps(s, ensure_ascii=False)
    ok("テスト講義" not in blob and "テスト前半" not in blob, "summary.json に題名を入れない")
    ok("テスト講義" not in text and PRESENTER not in text and "架空" not in text, "builder の表示に題名・講師名を出さない")
    ok("架空" not in json.dumps([a, e, dd], ensure_ascii=False), "出力に講師名・説明文の列を持ち込まない")

    # 2 回回して同じ (built_at 以外)
    code2, _ = run("--tsv", tsv, "--tags", tags, "--out-dir", out, "--main", main_py)
    a2 = load(out, "sapuri_lessons_TESTA0001.json")
    ok(code2 == 0 and {k: v for k, v in a2.items() if k != "built_at"} == {k: v for k, v in a.items() if k != "built_at"},
       "2 回回して同じ出力")

    # --dry-run は書かない
    out_dry = os.path.join(tmp, "out_dry")
    code3, _ = run("--tsv", tsv, "--tags", tags, "--out-dir", out_dry, "--main", main_py, "--dry-run")
    ok(code3 == 0 and not os.path.exists(out_dry), "--dry-run はフォルダもファイルも作らない")

    # 講師名の検査 (題名: 氏名・姓だけ・名だけ / topic: 氏名そのものだけ)
    for i, (title, topic, want_fail, label) in enumerate([
            ("第3講 架空太郎のテスト", None, True, "題名に氏名 (空白なし)"),
            ("第3講 架空 太郎のテスト", None, True, "題名に氏名 (空白あり)"),
            ("第3講 太郎のテスト", None, True, "題名に名だけ"),
            ("第3講 架空のテスト", None, True, "題名に姓だけ"),
            (None, "思想(架空太郎)", True, "topic に氏名"),
            (None, "思想(架空の人物)", False, "topic に姓だけは通す (歴史上の人物名と重なる)")]):
        d = os.path.join(tmp, f"name{i}")
        os.makedirs(d)
        t2, g2, m2 = write_fixture(d, extra_title=title, extra_topic=topic)
        o2 = os.path.join(d, "out")
        c, txt = run("--tsv", t2, "--tags", g2, "--out-dir", o2, "--main", m2)
        if want_fail:
            ok(c == 1 and not os.path.exists(o2), f"講師名で止まり何も書かない: {label} (exit {c})")
            ok("太郎" not in txt and "架空" not in txt, f"止めたときも講師名を表示しない: {label}")
            ok("講師名" in txt, f"止めた理由を出す: {label}")
        else:
            ok(c == 0, f"{label} (exit {c})")

    # パス: リポジトリの中・別の git 作業ツリーの中を拒否
    inside = os.path.join(HERE, "out_selftest_must_not_exist")
    c, txt = run("--tsv", tsv, "--tags", tags, "--out-dir", inside, "--main", main_py)
    ok(c == 2 and not os.path.exists(inside), f"リポジトリの中の --out-dir を拒否しフォルダも作らない (exit {c})")
    if os.path.isdir(inside) and os.path.basename(inside) == "out_selftest_must_not_exist":
        shutil.rmtree(inside, ignore_errors=True)               # 拒否が壊れていたときに架空の出力をリポジトリに残さない
    c, _ = run("--tsv", tsv, "--tags", os.path.join(REPO, "tags.json"), "--out-dir", out, "--main", main_py)
    ok(c == 2, "リポジトリの中の --tags を拒否")
    other = os.path.join(tmp, "other_clone")
    os.makedirs(other)
    with open(os.path.join(other, ".git"), "w", encoding="utf-8") as f:
        f.write("gitdir: /nowhere\n")                             # worktree の .git はファイル
    c, _ = run("--tsv", tsv, "--tags", tags, "--out-dir", os.path.join(other, "x", "y"), "--main", main_py)
    ok(c == 2 and not os.path.exists(os.path.join(other, "x")), "別の git 作業ツリーの中の --out-dir を拒否")

    # --help の文言
    c, txt = run("--help")
    ok(c == 0 and "studysapuri.jp・mediacdn を取得しない" in txt and "塾長がブラウザで保存したファイルから作る" in txt,
       "--help に「取得しない・塾長が保存したファイルから作る」")

    # 通信・URL を持たない (ast で import と文字列を見る)
    bsrc = open(BUILDER, encoding="utf-8").read()
    tree = ast.parse(bsrc)
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {x.name.split(".")[0] for x in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module.split(".")[0])
    net = mods & {"urllib", "http", "requests", "httpx", "socket", "aiohttp", "ssl", "ftplib", "subprocess"}
    ok(not net, f"builder は通信・外部コマンドの module を import しない: {sorted(net)}")
    ok("http://" not in bsrc and "https://" not in bsrc and "mediacdn." not in bsrc, "builder に URL が無い")

    # 本物の server/main.py の定数を ast で読める
    sys.dont_write_bytecode = True
    sys.path.insert(0, HERE)
    import build_sapuri_import as B
    consts = B.load_main_consts()
    courses = consts["SAPURI_COURSES"]
    ok(len(courses) > 100, f"本物の SAPURI_COURSES を読める ({len(courses)} 講座)")
    hl = [c for c in courses if c.get("has_lessons")]
    ok(len(hl) > 0 and all(B.RE_CODE.match(c["code"]) and isinstance(c["first"], int) and isinstance(c["last"], int)
                           and c["first"] <= c["last"] for c in hl),
       f"講データのある講座 {len(hl)} のコード・first・last が builder で扱える形")
    ok(set(consts["SAPURI_TAG_VOCAB"]) <= set(consts["SAPURI_SUBJECT_KEYS"]) or
       set(consts["SAPURI_SUBJECT_KEYS"]) <= set(consts["SAPURI_TAG_VOCAB"]),
       "語彙の科目キーと SAPURI_SUBJECT_KEYS がそろう")

    if problems:
        print(f"\n❌ builder 自己テスト: {len(problems)} 件 (合格 {passed[0]})")
        return 1
    print(f"✅ builder 自己テスト: {passed[0]} 項目すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
