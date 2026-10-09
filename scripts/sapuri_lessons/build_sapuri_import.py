#!/usr/bin/env python3
"""📺 スタサプ 第N講の取込用 JSON (講座ごとに 1 ファイル) を作る builder (2026-10-10 スタサプ段階 B・SPEC2 §4.4)。

★このファイルは **コードだけ**。講の題名 (第N講の題名) はリポジトリに入れない (塾長決定 D1: 題名は本番 DB だけ)。
  入力も出力もリポジトリの外 (既定は ~/Desktop/🏫 運営・集客/塾運営/スタサプ講義データ/) で、リポジトリ内のパスは拒否する。
★studysapuri.jp・mediacdn を取得しない (URL も通信処理も持たない)。塾長がブラウザで保存したファイルから作る。

入力:
  --tsv   公開の通年講座一覧 (high_category.tsv。列: course_code / topic_name / topic_code / presenter_name …)
  --tags  タグ付けの結果 (tagged_final.json: [{id:"<subject_key>__<course_code>", lesson_tags:[{seq,tags:[…]}],
          topic_lessons:[{topic, seqs:[…]}]}, …])
  講座カタログ・科目キー・タグ語彙・別名は server/main.py の SAPURI_COURSES / SAPURI_SUBJECT_KEYS / SAPURI_TAG_VOCAB /
  SAPURI_TAG_ALIASES を **ast で読む** (main.py は import しない)。

講の取り出し規則 (タグ付けに使った抽出と同じ):
  - 「第N講 題名」の N を seq にする。番号の無い回 (補講・講座の選び方) と第0講は捨てる。
  - EKZB (新版) は topic_code EKGB{2桁}{講2桁}{part}0 の講番号で束ね、各回の PART/Chapter の接頭辞を外して「／」で連結。
  - 80 字を超える題名は 79 字 + 「…」。改行・制御文字は空白に、< > は全角 (＜＞) に (取込 API は HTML を拒否する)。
講座の選び方: カタログで has_lessons=True かつ 取り出した講が first..last にちょうど 1 講ずつ (講数 = last-first+1)。
  合わない講座は書かずに summary.json の skipped に理由を残す (2022 年版と今の講数のずれ対策)。
講師名の検査: TSV の presenter_name の値を含む題名 (氏名・空白で分けた 2 文字以上の部分) と topic (氏名そのもの) があれば
  **何も書かずに失敗**する。名前そのものは表示しない (講座コードと講番号だけ)。列は検査の直後に捨てる。

出力 (out-dir):
  sapuri_lessons_<course_code>.json = {course_code, source, built_at, lessons:[{seq,title,tags:[{subject_key,tag}]}],
                                      topic_lessons:[{subject_key, topic_norm, seqs}]}  (CEO「📺 スタサプ講義データ」で取り込む)
  summary.json = 講座ごとの件数・飛ばした講座と理由・捨てたタグ/topic の件数 (題名は入れない)
  ★前回の出力で今回書かなかったファイルは消さない (デスクトップの約束: 削除しない)。summary の stale_files に出す。

使い方:
  python3 scripts/sapuri_lessons/build_sapuri_import.py \\
      --tsv  "~/Desktop/🏫 運営・集客/塾運営/スタサプ講義データ/元データ/high_category.tsv" \\
      --tags "~/Desktop/🏫 運営・集客/塾運営/スタサプ講義データ/タグ付け/tagged_final.json" \\
      --out-dir "~/Desktop/🏫 運営・集客/塾運営/スタサプ講義データ/取込用"
自己テスト: scripts/sapuri_lessons/check_build_sapuri_import.py (架空のデータで回す・run_all_gates が拾う)
"""
import argparse
import ast
import csv
import datetime
import json
import os
import re
import sys
import unicodedata
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")

DATA_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "🏫 運営・集客", "塾運営", "スタサプ講義データ")
DEFAULT_TSV = os.path.join(DATA_ROOT, "元データ", "high_category.tsv")
DEFAULT_TAGS = os.path.join(DATA_ROOT, "タグ付け", "tagged_final.json")
DEFAULT_OUT = os.path.join(DATA_ROOT, "取込用")

SOURCE = "studysapuri.jp 通年講座一覧 (2022-06 時点の公開データ)"
OUT_PREFIX = "sapuri_lessons_"
MAX_TITLE = 80
MAX_TOPIC = 120
MAX_TOPIC_SEQS = 3
JST = datetime.timezone(datetime.timedelta(hours=9))

RE_DAI = re.compile(r"^第\s*(\d+)\s*講\s*(.*)$")
RE_EKGB = re.compile(r"^EKGB(\d{2})(\d{2})(\d)0$")
RE_PART = re.compile(r"^(?:PART|Chapter|チャプター)\s*[0-9０-９]+\s*", re.I)
RE_CODE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
RE_CTRL = re.compile(r"[\x00-\x1f\x7f  ]+")
TEACHER_WORDS = ("講師", "先生")
NEEDED_COLS = ("course_code", "topic_name", "topic_code", "presenter_name")
CONSTS = ("SAPURI_COURSES", "SAPURI_SUBJECT_KEYS", "SAPURI_TAG_VOCAB", "SAPURI_TAG_ALIASES")

csv.field_size_limit(10 ** 9)


class BuildError(Exception):
    """入力・検査の失敗 (何も書かない)。メッセージに題名・講師名を入れないこと。"""


def norm(s):
    return unicodedata.normalize("NFKC", s or "").strip()


# ---------------------------------------------------------------- パス
def git_root_of(path):
    """path (存在しなくてよい) がどこかの git 作業ツリーの中なら、その根を返す。

    この builder のあるリポジトリ (公開) に加え、共有 checkout など別の clone の中も拒否する
    (親を順にたどって .git を探す。worktree の .git はファイルなので exists で見る)。
    """
    p = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
    repo = os.path.realpath(REPO)
    if p == repo or p.startswith(repo + os.sep):
        return repo
    cur = p
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


# ---------------------------------------------------------------- main.py の定数
def load_main_consts(main_py=MAIN_PY):
    try:
        src = open(main_py, encoding="utf-8").read()
    except OSError as e:
        raise BuildError(f"server/main.py が読めない: {e.__class__.__name__}")
    out = {}
    for node in ast.parse(src).body:   # module 直下の代入だけ
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in CONSTS and name not in out:
                try:
                    out[name] = ast.literal_eval(node.value)
                except Exception:
                    raise BuildError(f"{name} がリテラルとして読めない")
    missing = [n for n in CONSTS if n not in out]
    if missing:
        raise BuildError(f"server/main.py の module 直下に無い定数: {', '.join(missing)}")
    return out


# ---------------------------------------------------------------- TSV
def read_tsv(path):
    """TSV → ({course_code: {seq: entry}}, 講師名の集合)。講師名の集合は呼び出し側で検査後すぐ捨てる。"""
    courses = OrderedDict()
    presenters = set()
    try:
        f = open(path, encoding="utf-8", newline="")
    except OSError as e:
        raise BuildError(f"--tsv が読めない: {e.__class__.__name__}")
    with f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = reader.fieldnames or []
        missing = [c for c in NEEDED_COLS if c not in cols]
        if missing:
            raise BuildError(f"--tsv に必要な列が無い: {', '.join(missing)} (公開の通年講座一覧ではない?)")
        for r in reader:
            pn = norm(r.get("presenter_name"))
            if pn:
                presenters.add(pn)
            cc = (r.get("course_code") or "").strip()
            if not cc:
                continue
            lessons = courses.setdefault(cc, OrderedDict())
            tname = r.get("topic_name") or ""
            tcode = (r.get("topic_code") or "").strip()
            if cc.startswith("EKZB"):
                m = RE_EKGB.match(tcode)
                if not m:
                    continue
                seq = int(m.group(2))
                if seq == 0:
                    continue                       # 講0 (導入) は第N講ではない
                part = RE_PART.sub("", norm(tname)).strip()
                if part.startswith("補講"):
                    continue
                ent = lessons.setdefault(seq, {"parts": OrderedDict()})
                if part and "parts" in ent:
                    ent["parts"][tcode] = part
                continue
            m = RE_DAI.match(norm(tname))
            if not m:
                continue                           # 補講・講座の選び方など番号の無い回
            seq = int(m.group(1))
            if seq == 0:
                continue
            lessons.setdefault(seq, {"title": m.group(2).strip()})
    return courses, presenters


def clean_title(t):
    t = RE_CTRL.sub(" ", t)
    t = t.replace("<", "＜").replace(">", "＞")
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > MAX_TITLE:
        t = t[:MAX_TITLE - 1] + "…"
    return t


def extract_lessons(courses):
    """{course_code: [{seq, title}]} (seq 昇順)。"""
    out = OrderedDict()
    for cc, lessons in courses.items():
        rows = []
        for seq in sorted(lessons):
            ent = lessons[seq]
            if "parts" in ent:
                title = "／".join(OrderedDict.fromkeys(ent["parts"].values()))
            else:
                title = ent["title"]
            rows.append({"seq": seq, "title": clean_title(title)})
        if rows:
            out[cc] = rows
    return out


def name_needles(presenters):
    """講師名の検査に使う文字列 → (氏名そのもの・空白を詰めた形, 空白で分けた 2 文字以上の部分)。

    部分 (姓だけ・名だけ) は題名にだけ当てる。タグ付けの topic は塾の弱点単元名で、歴史上の人物名
    (日本思想の儒学者など) が講師の姓と同じことがある (実データで 1 件)。topic には氏名そのものだけを当てる。
    """
    full, parts = set(), set()
    for p in presenters:
        p = norm(p)
        if not p:
            continue
        full.add(p)
        full.add(re.sub(r"\s+", "", p))
        for part in re.split(r"[\s、,/・／]+", p):
            if len(part) >= 2:
                parts.add(part)
    full = {n for n in full if len(n) >= 2}
    return full, parts | full


# ---------------------------------------------------------------- タグ付け
def read_tags(path):
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise BuildError(f"--tags が読めない: {e.__class__.__name__}")
    if not isinstance(data, list):
        raise BuildError("--tags の最上位が配列ではない (tagged_final.json の形: [{id, lesson_tags, topic_lessons}, …])")
    return data


# ---------------------------------------------------------------- 組み立て
def build(tsv_path, tags_path, main_py=MAIN_PY, now=None):
    """(講座ごとの出力 {code: obj}, summary) を返す。失敗は BuildError。ファイルは書かない。"""
    consts = load_main_consts(main_py)
    catalog = OrderedDict((c["code"], c) for c in consts["SAPURI_COURSES"])
    subject_keys = set(consts["SAPURI_SUBJECT_KEYS"])
    vocab = {k: set(v) for k, v in consts["SAPURI_TAG_VOCAB"].items()}
    aliases = consts["SAPURI_TAG_ALIASES"]

    raw, presenters = read_tsv(tsv_path)
    full_names, name_parts = name_needles(presenters)
    del presenters                                  # 講師名の列はここで捨てる (以後どこにも持たない)
    lessons_by_code = extract_lessons(raw)
    del raw
    tagged = read_tags(tags_path)

    # 講師名・「講師」「先生」の検査 (TSV にある全講座の題名 + タグ付けの topic)。名前・題名は出さない。
    hits = []
    for cc, rows in lessons_by_code.items():
        for r in rows:
            if any(n in r["title"] for n in name_parts):
                hits.append(f"{cc} 第{r['seq']}講")
    for ent in tagged:
        for tl in (ent.get("topic_lessons") or []) if isinstance(ent, dict) else []:
            t = norm(str((tl or {}).get("topic") or ""))
            if t and any(n in t for n in full_names):
                hits.append(f"{ent.get('id', '?')} の topic")
    del full_names, name_parts
    if hits:
        raise BuildError(f"講師名を含む題名・topic が {len(hits)} 件 (例: {', '.join(hits[:5])})。"
                         "元データを確かめること (何も書いていない)")

    skipped = []
    outputs = OrderedDict()
    for code, c in catalog.items():
        if not c.get("has_lessons"):
            continue
        rows = lessons_by_code.get(code)
        if not RE_CODE.match(code):
            skipped.append({"course_code": code, "reason": "講座コードがファイル名に使えない形"})
            continue
        if not rows:
            skipped.append({"course_code": code, "reason": "TSV に第N講の回が無い"})
            continue
        want = list(range(int(c["first"]), int(c["last"]) + 1))
        got = [r["seq"] for r in rows]
        if got != want:
            skipped.append({"course_code": code,
                            "reason": f"講数が合わない (TSV {len(got)} 講 {min(got)}〜{max(got)} / "
                                      f"カタログ 第{c['first']}〜{c['last']}講 = {len(want)} 講)"})
            continue
        bad_t = [r["seq"] for r in rows if not r["title"] or any(w in r["title"] for w in TEACHER_WORDS)]
        if bad_t:
            skipped.append({"course_code": code,
                            "reason": f"題名が空か「講師」「先生」を含む講がある (第{bad_t[0]}講 ほか {len(bad_t)} 講)"})
            continue
        outputs[code] = {"course": c, "lessons": OrderedDict((r["seq"], {"seq": r["seq"], "title": r["title"], "tags": []})
                                                              for r in rows),
                         "topics": OrderedDict(), "tagged": False}
    # TSV にあるがカタログに無い講座は数だけ
    not_in_catalog = sorted(cc for cc in lessons_by_code if cc not in catalog)

    dropped_tags = {}            # "subject_key:tag" -> 件数
    dropped_sk = {}              # subject_key -> 件数 (SAPURI_SUBJECT_KEYS に無い)
    dropped_topics = {"seq": 0, "empty": 0, "too_many": 0, "too_long": 0}
    dropped_lesson_tags = 0      # 講が無い seq へのタグ
    tagged_skipped = {}          # 講座が書かれない (has_lessons=False・講数不一致・カタログ外) タグ付け
    bad_ids = 0
    for ent in tagged:
        if not isinstance(ent, dict) or "__" not in str(ent.get("id") or ""):
            bad_ids += 1
            continue
        sk, code = str(ent["id"]).split("__", 1)
        if sk not in subject_keys:
            dropped_sk[sk] = dropped_sk.get(sk, 0) + 1
            continue
        if code not in outputs:
            tagged_skipped[code] = "カタログに無い" if code not in catalog else "講座を書かない (has_lessons=False か講数不一致)"
            continue
        o = outputs[code]
        o["tagged"] = True
        for lt in ent.get("lesson_tags") or []:
            try:
                seq = int(lt.get("seq"))
            except (TypeError, ValueError, AttributeError):
                dropped_lesson_tags += 1
                continue
            les = o["lessons"].get(seq)
            if les is None:
                dropped_lesson_tags += 1
                continue
            for t in lt.get("tags") or []:
                t = norm(str(t))
                for tag in (aliases.get(sk, {}).get(t) or [t]):
                    if tag in vocab.get(sk, ()):
                        pair = {"subject_key": sk, "tag": tag}
                        if pair not in les["tags"]:
                            les["tags"].append(pair)
                    else:
                        k = f"{sk}:{tag}"
                        dropped_tags[k] = dropped_tags.get(k, 0) + 1
        for tl in ent.get("topic_lessons") or []:
            topic = norm(str((tl or {}).get("topic") or ""))
            if not topic:
                dropped_topics["empty"] += 1
                continue
            if len(topic) > MAX_TOPIC or RE_CTRL.search(topic):
                dropped_topics["too_long"] += 1
                continue
            seqs = []
            ok = True
            for s in (tl.get("seqs") or []):
                try:
                    s = int(s)
                except (TypeError, ValueError):
                    ok = False
                    break
                if s not in o["lessons"]:
                    ok = False
                    break
                if s not in seqs:
                    seqs.append(s)
            if not ok or not seqs:
                dropped_topics["seq"] += 1
                continue
            key = (sk, topic)
            merged = o["topics"].get(key, []) + [s for s in seqs if s not in o["topics"].get(key, [])]
            o["topics"][key] = merged
        # 同じ topic を 2 回書いて 4 講以上になったものは取込 API が拒否するので落とす
        for key in [k for k, v in o["topics"].items() if len(v) > MAX_TOPIC_SEQS]:
            del o["topics"][key]
            dropped_topics["too_many"] += 1

    built_at = (now or datetime.datetime.now(JST)).isoformat(timespec="seconds")
    files = OrderedDict()
    per_course = []
    for code, o in outputs.items():
        lessons = list(o["lessons"].values())
        topics = [{"subject_key": sk, "topic_norm": t, "seqs": seqs} for (sk, t), seqs in o["topics"].items()]
        files[code] = {"course_code": code, "source": SOURCE, "built_at": built_at,
                       "lessons": lessons, "topic_lessons": topics}
        per_course.append({"course_code": code, "file": f"{OUT_PREFIX}{code}.json", "lessons": len(lessons),
                           "first": lessons[0]["seq"], "last": lessons[-1]["seq"],
                           "tagged": o["tagged"], "tagged_lessons": sum(1 for x in lessons if x["tags"]),
                           "tags": sum(len(x["tags"]) for x in lessons), "topic_lessons": len(topics)})
    summary = {
        "source": SOURCE,
        "built_at": built_at,
        "note": "題名はこのファイルに入れない。講座ごとの JSON を CEO「📺 スタサプ講義データ」で dry_run → 取り込む",
        "totals": {
            "catalog_courses": len(catalog),
            "catalog_has_lessons": sum(1 for c in catalog.values() if c.get("has_lessons")),
            "courses_written": len(files),
            "courses_skipped": len(skipped),
            "courses_untagged": sum(1 for p in per_course if not p["tagged"]),
            "lessons": sum(p["lessons"] for p in per_course),
            "tagged_lessons": sum(p["tagged_lessons"] for p in per_course),
            "tags": sum(p["tags"] for p in per_course),
            "topic_lessons": sum(p["topic_lessons"] for p in per_course),
            "dropped_tags": sum(dropped_tags.values()),
            "dropped_subject_keys": sum(dropped_sk.values()),
            "dropped_lesson_tags_no_lesson": dropped_lesson_tags,
            "dropped_topics": sum(dropped_topics.values()),
            "tagged_courses_not_written": len(tagged_skipped),
            "tagged_bad_ids": bad_ids,
            "tsv_courses_not_in_catalog": len(not_in_catalog),
        },
        "courses": per_course,
        "skipped": skipped,
        "dropped": {"tags": dict(sorted(dropped_tags.items())), "subject_keys": dict(sorted(dropped_sk.items())),
                    "topics": dropped_topics},
        "tagged_courses_not_written": [{"course_code": k, "reason": v} for k, v in sorted(tagged_skipped.items())],
        "tsv_courses_not_in_catalog": not_in_catalog,
    }
    return files, summary


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="build_sapuri_import.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "📺 スタサプ 第N講の取込用 JSON (講座ごと) を作る。\n"
            "studysapuri.jp・mediacdn を取得しない。塾長がブラウザで保存したファイルから作る。\n"
            "入力・出力はリポジトリの外 (既定: ~/Desktop/🏫 運営・集客/塾運営/スタサプ講義データ/)。"
            "git の作業ツリーの中のパスは拒否する (講の題名を公開リポジトリに入れない = 塾長決定 D1)。"),
        epilog="出力: sapuri_lessons_<講座コード>.json と summary.json。CEO「📺 スタサプ講義データ」で dry_run してから取り込む。")
    ap.add_argument("--tsv", default=DEFAULT_TSV, help="公開の通年講座一覧 high_category.tsv (既定: 元データ/)")
    ap.add_argument("--tags", default=DEFAULT_TAGS, help="タグ付けの結果 tagged_final.json (既定: タグ付け/)")
    ap.add_argument("--out-dir", default=DEFAULT_OUT, help="出力先フォルダ (既定: 取込用/)")
    ap.add_argument("--catalog-from-main", action="store_true",
                    help="(互換のための指定。常に server/main.py の SAPURI_COURSES を ast で読む)")
    ap.add_argument("--main", default=MAIN_PY, help=argparse.SUPPRESS)   # 自己テスト用 (架空の定数ファイル)
    ap.add_argument("--dry-run", action="store_true", help="検査と件数の表示だけ (ファイルを書かない)")
    a = ap.parse_args(argv)

    paths = {"--tsv": a.tsv, "--tags": a.tags, "--out-dir": a.out_dir}
    for flag, p in paths.items():
        root = git_root_of(p)
        if root:
            print(f"拒否: {flag} が git の作業ツリーの中を指している ({root})。"
                  "講の題名をリポジトリに入れない決まり (D1)。リポジトリの外を指定すること", file=sys.stderr)
            return 2
    tsv, tags, out_dir = (os.path.abspath(os.path.expanduser(p)) for p in (a.tsv, a.tags, a.out_dir))
    for flag, p in (("--tsv", tsv), ("--tags", tags)):
        if not os.path.isfile(p):
            print(f"止めた: {flag} のファイルが無い ({p})", file=sys.stderr)
            return 2

    try:
        files, summary = build(tsv, tags, main_py=a.main)
    except BuildError as e:
        print(f"止めた: {e}", file=sys.stderr)
        return 1

    tot = summary["totals"]
    print(f"講座: 書く {tot['courses_written']} / 飛ばす {tot['courses_skipped']} "
          f"(カタログ {tot['catalog_courses']}・講データあり {tot['catalog_has_lessons']})")
    print(f"講 {tot['lessons']} (タグつき {tot['tagged_lessons']}・タグ {tot['tags']})・topic {tot['topic_lessons']}・"
          f"タグ付けの無い講座 {tot['courses_untagged']}")
    print(f"捨てた: タグ {tot['dropped_tags']}・科目キー {tot['dropped_subject_keys']}・"
          f"講の無い seq {tot['dropped_lesson_tags_no_lesson']}・topic {tot['dropped_topics']}・"
          f"書かない講座のタグ付け {tot['tagged_courses_not_written']}")
    for s in summary["skipped"]:
        print(f"  飛ばした講座 {s['course_code']}: {s['reason']}")
    if a.dry_run:
        print("--dry-run: ファイルは書いていない")
        return 0

    os.makedirs(out_dir, exist_ok=True)
    written = set()
    for code, obj in files.items():
        name = f"{OUT_PREFIX}{code}.json"
        write_json(os.path.join(out_dir, name), obj)
        written.add(name)
    stale = sorted(n for n in os.listdir(out_dir)
                   if n.startswith(OUT_PREFIX) and n.endswith(".json") and n not in written)
    summary["stale_files"] = stale
    write_json(os.path.join(out_dir, "summary.json"), summary)
    print(f"書いた: {len(written)} ファイル + summary.json → {out_dir}")
    if stale:
        print(f"注意: 今回書かなかった前回の出力が {len(stale)} 件残っている (消していない・取り込まないこと)。"
              "summary.json の stale_files を見る")
    return 0


if __name__ == "__main__":
    sys.exit(main())
