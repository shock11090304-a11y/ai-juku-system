#!/usr/bin/env python3
"""📺 スタサプ 第N講の題名がコミットに紛れ込んでいないかを見る **手元専用** の点検 (2026-10-10 スタサプ段階 B・SPEC2 §4.4)。

塾長決定 D1: 講の題名は本番 DB だけ。公開リポジトリ (コード・テスト・コメント・CLAUDE.md・コミットメッセージ) に出さない。
題名の元データ (取込用 JSON) は Desktop にだけあり CI には無いので、これは手元で回す点検。

  python3 scripts/sapuri_lessons/check_no_titles_in_diff.py                  # git diff --cached (commit 前に)
  python3 scripts/sapuri_lessons/check_no_titles_in_diff.py --range 6857cfe..HEAD   # その範囲の追加行とコミットメッセージ
  python3 scripts/sapuri_lessons/check_no_titles_in_diff.py --all-files      # 追跡中の全ファイル (重い・数十秒)

- 題名は builder (build_sapuri_import.py) の出力 sapuri_lessons_*.json から読む
  (既定 ~/Desktop/🏫 運営・集客/塾運営/スタサプ講義データ/取込用/・--data-dir で変更)。
  **ファイルが無ければ SKIP で exit 0** (CI・別の端末。run_all_gates.py が引数なしで拾っても落ちない)。
- 題名 (と EKZB の「／」で区切った各回) のうち 4 文字以上 (--min-len) を、NFKC でそろえた追加行に探す。
- 表示は件数と「ファイル:行・講座コード 第N講」だけ。**題名そのものは表示しない** (この点検の出力も公開ログに残りうる)。
- **一般語の除外**: 題名には「三角関数」「名詞・代名詞」のような単元名そのものも多い。基準のコミット (--baseline・既定
  6857cfe = スタサプ講単位の作業を始める前の origin/main) の追跡ファイルに既にある文字列と、タグ語彙・別名
  (server/main.py の SAPURI_TAG_VOCAB / SAPURI_TAG_ALIASES) と同じ文字列は「一般語」として数えるだけにする。
  当たった題名だけを基準のコミットの blob (`git cat-file --batch`) に探す (ファイルに書かない)。
- 一般語でない題名が当たったら exit 1。行を開いて題名の写しかどうかを確かめる。
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATA_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "🏫 運営・集客", "塾運営", "スタサプ講義データ", "取込用")
MAX_FILE = 8 * 1024 * 1024
BASELINE = "6857cfe"      # スタサプ講単位 (段階 A/B) の作業を始める前の origin/main


def norm(s):
    return unicodedata.normalize("NFKC", s or "")


def load_titles(data_dir, min_len):
    """{題名(NFKC): [(講座コード, seq)]}。題名は呼び出し側で表示しない。"""
    titles = {}
    files = sorted(glob.glob(os.path.join(data_dir, "sapuri_lessons_*.json")))
    for path in files:
        try:
            obj = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cc = str(obj.get("course_code") or os.path.basename(path))
        for les in obj.get("lessons") or []:
            t = norm(str(les.get("title") or "")).strip()
            if t.endswith("…"):
                t = t[:-1].strip()               # 80 字で切った題名は切る前の部分で探す
            for piece in {t, *t.split("／")}:
                piece = piece.strip()
                if len(piece) >= min_len:
                    titles.setdefault(piece, []).append((cc, les.get("seq")))
    return files, titles


class Finder:
    """先頭 min_len 文字で引く索引。行を 1 回なめるだけで全題名を探す (題名 × 行の総当たりをしない)。"""

    def __init__(self, titles, min_len):
        self.k = min_len
        self.idx = {}
        for t in titles:
            self.idx.setdefault(t[:min_len], []).append(t)
        self.ascii_titles = any(t.isascii() for t in titles)

    def find(self, line):
        if not self.ascii_titles and line.isascii():
            return set()
        hit = set()
        k = self.k
        for i in range(len(line) - k + 1):
            cands = self.idx.get(line[i:i + k])
            if cands:
                for t in cands:
                    if line.startswith(t, i):
                        hit.add(t)
        return hit


def vocab_words(repo):
    """タグ語彙と別名 (一般語)。builder と同じく server/main.py を ast で読む。読めなければ空。"""
    sys.dont_write_bytecode = True
    sys.path.insert(0, HERE)
    try:
        import build_sapuri_import as B
        c = B.load_main_consts(os.path.join(repo, "server", "main.py"))
    except Exception:
        return set()
    words = set()
    for v in c["SAPURI_TAG_VOCAB"].values():
        words |= {norm(x) for x in v}
    for m in c["SAPURI_TAG_ALIASES"].values():
        words |= {norm(x) for x in m}
    return words


def tree_texts(rev, repo):
    """rev の追跡ファイル (テキストだけ・8MB まで) の中身を 1 本ずつ返す。`git cat-file --batch` でまとめて読む。"""
    ls = subprocess.run(["git", "ls-tree", "-r", "-z", "-l", rev], cwd=repo, capture_output=True)
    if ls.returncode != 0:
        raise RuntimeError(f"git ls-tree が失敗 (exit {ls.returncode})")
    shas = []
    for ent in ls.stdout.split(b"\0"):
        if not ent:
            continue
        meta = ent.split(b"\t", 1)[0].split()
        if len(meta) >= 4 and meta[1] == b"blob" and meta[3].isdigit() and int(meta[3]) <= MAX_FILE:
            shas.append(meta[2])
    r = subprocess.run(["git", "cat-file", "--batch"], cwd=repo, input=b"\n".join(shas) + b"\n",
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git cat-file が失敗 (exit {r.returncode})")
    buf, pos = r.stdout, 0
    while pos < len(buf):
        nl = buf.index(b"\n", pos)
        head = buf[pos:nl].split()
        if len(head) < 3:                      # missing
            pos = nl + 1
            continue
        size = int(head[2])
        body = buf[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1
        if b"\0" not in body[:8192]:
            yield body.decode("utf-8", "replace")


def in_baseline(cands, rev, repo, min_len):
    """cands のうち基準のコミットの追跡ファイルに既にある文字列 (一般語)。基準が無ければ None。

    ★`git grep -F -e …` を 100 個以上の日本語の語で回すと何分も返らない (実測) ので、blob を読んで同じ索引で探す。
    """
    if subprocess.run(["git", "rev-parse", "-q", "--verify", rev + "^{commit}"], cwd=repo,
                      capture_output=True).returncode != 0:
        return None
    finder = Finder(cands, min_len)
    found = set()
    try:
        for text in tree_texts(rev, repo):
            for line in text.splitlines():
                found |= finder.find(norm(line))
            if found >= set(cands):
                break
    except (OSError, RuntimeError, ValueError):
        return None
    return found


def git(args, repo):
    r = subprocess.run(["git"] + args, cwd=repo, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} が失敗 (exit {r.returncode})")
    return r.stdout.decode("utf-8", "replace")


def added_lines(diff_text):
    """unified diff → [(path, 行番号, 行)] の追加行。"""
    out, path, ln = [], None, 0
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            p = line[4:]
            path = p[2:] if p.startswith("b/") else p
            continue
        if line.startswith("@@"):
            try:
                ln = int(line.split("+", 1)[1].split(" ", 1)[0].split(",")[0])
            except (IndexError, ValueError):
                ln = 0
            continue
        if line.startswith("+") and not line.startswith("+++"):
            out.append((path, ln, line[1:]))
            ln += 1
        elif not line.startswith("-") and not line.startswith("\\"):
            ln += 1
    return out


def main():
    ap = argparse.ArgumentParser(description="スタサプの講の題名がコミットに紛れ込んでいないかを見る (手元専用・題名は表示しない)")
    ap.add_argument("--data-dir", default=DATA_DIR, help="builder の出力フォルダ (sapuri_lessons_*.json)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--range", help="A..B の追加行とコミットメッセージを見る (既定は git diff --cached)")
    g.add_argument("--all-files", action="store_true", help="追跡中の全ファイルを見る")
    ap.add_argument("--repo", default=REPO, help="見るリポジトリ (既定: このスクリプトのあるリポジトリ)")
    ap.add_argument("--min-len", type=int, default=4, help="この文字数以上の題名だけ探す (既定 4)")
    ap.add_argument("--baseline", default=BASELINE,
                    help=f"このコミットに既にある文字列は一般語として数えるだけ (既定 {BASELINE}・'' で除外しない)")
    a = ap.parse_args()

    files, titles = load_titles(a.data_dir, a.min_len)
    if not files:
        print(f"SKIP: 取込データ (sapuri_lessons_*.json) が無い = この端末では点検できない ({a.data_dir})")
        return 0
    if not titles:
        print(f"SKIP: 取込データ {len(files)} ファイルに {a.min_len} 文字以上の題名が無い")
        return 0
    finder = Finder(titles, a.min_len)

    targets = []           # (場所, 行番号, 行)
    try:
        if a.all_files:
            names = [n for n in git(["ls-files", "-z"], a.repo).split("\0") if n]
            mode = f"追跡中の全ファイル {len(names)} 本"
            for n in names:
                p = os.path.join(a.repo, n)
                try:
                    if os.path.getsize(p) > MAX_FILE:
                        continue
                    raw = open(p, "rb").read()
                except OSError:
                    continue
                if b"\0" in raw[:8192]:
                    continue                       # バイナリ
                for i, line in enumerate(raw.decode("utf-8", "replace").splitlines(), 1):
                    targets.append((n, i, line))
        elif a.range:
            if ".." not in a.range:
                print("--range は A..B の形で指定する", file=sys.stderr)
                return 2
            targets = added_lines(git(["diff", "-U0", "--no-color", "--no-ext-diff", a.range], a.repo))
            msgs = git(["log", "--format=%B", a.range], a.repo)
            targets += [("(コミットメッセージ)", i, line) for i, line in enumerate(msgs.splitlines(), 1)]
            mode = f"{a.range} の追加行 {len(targets)} 行 (コミットメッセージを含む)"
        else:
            targets = added_lines(git(["diff", "--cached", "-U0", "--no-color", "--no-ext-diff"], a.repo))
            mode = f"git diff --cached の追加行 {len(targets)} 行"
    except (OSError, RuntimeError) as e:
        print(f"点検できない: {e}", file=sys.stderr)
        return 2

    hits = []
    for where, ln, line in targets:
        for t in finder.find(norm(line)):
            hits.append((where, ln, t))
    print(f"題名 {len(titles)} 種 ({len(files)} 講座・{a.min_len} 文字以上) を {mode} で探した")
    if not hits:
        print("✅ 講の題名は見つからない")
        return 0
    distinct = {t for _, _, t in hits}
    generic = distinct & vocab_words(a.repo)
    base = in_baseline(distinct - generic, a.baseline, a.repo, a.min_len) if a.baseline else set()
    if base is None:
        print(f"注意: 基準のコミット {a.baseline} が見つからない = 一般語の除外はタグ語彙だけ")
        base = set()
    generic |= base
    real = [h for h in hits if h[2] not in generic]
    ng = len(hits) - len(real)
    if ng:
        print(f"一般語 (タグ語彙・{a.baseline or '基準なし'} に既にある語) と同じ題名: {ng} か所 "
              f"({len(distinct & generic)} 種) は数えるだけ")
    if not real:
        print("✅ 一般語でない講の題名は見つからない")
        return 0
    rd = {t for _, _, t in real}
    print(f"❌ 講の題名と同じ文字列が {len(real)} か所 (題名 {len(rd)} 種)。題名は表示しない。行を開いて確かめること:")
    for where, ln, t in real[:40]:
        refs = titles[t]
        ref = ", ".join(f"{cc} 第{seq}講" for cc, seq in refs[:2]) + (f" ほか {len(refs) - 2}" if len(refs) > 2 else "")
        print(f"  {where}:{ln}  ← {ref} ({len(t)} 文字)")
    if len(real) > 40:
        print(f"  … ほか {len(real) - 40} か所")
    return 1


if __name__ == "__main__":
    sys.exit(main())
