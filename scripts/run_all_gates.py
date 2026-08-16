#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""教材の品質ゲートを**リポジトリの中だけで**まとめて回す単一の入口。

    python3 scripts/run_all_gates.py              # 全部
    python3 scripts/run_all_gates.py rika_kagaku  # 名前で絞る（部分一致・複数可）
    python3 scripts/run_all_gates.py --list       # 何が対象かを見るだけ

★このファイルが存在する理由（2026-08-04 の調査で判明した構造的な穴）
  教材ごとに check.py / verify.py / *_gate.py を書いてきたが、**呼ぶ人がいなかった**。
  - `.claude/settings.json` の Stop フックで回す設計だったが、`.claude/` は .gitignore 対象で
    **永久にコミットできない**。実際 settings.json はディスクにも無く、
    scripts/kyotsu_mogi2026/README.md の「層2 Stopフック」は実体の無い記述だった。
  - CI（exam-quality.yml）の対象は seed-data と kyotsu_mogi2026 だけで、他の教材を1つも見ていない。
  結果、「ルール化したのに次のセッションで効いていない」が繰り返し起きていた。
  → **リポジトリの中に入口を1つ置く**。ローカルでも CI でも同じコマンドで回る形にする。

■ 何を回すか
  scripts/ 以下（**再帰**）の check*/verify*/validate*/audit*/preflight*/qa*/*_gate を、
  そのファイルのディレクトリを作業ディレクトリにして実行する（相対 import と cwd 前提が多い）。
  build*.py は PDF を書き出す副作用があるので**回さない**（CI に Chrome は無い）。

■ 判定（★「検査したつもり」を作らないための約束）
  PASS   終了コード 0 で、違反を自称していない。
  FAIL   終了コードが 0 でない。**理由は問わず失敗**。違反検出(VIOLATION)かゲート自体の
         故障(CRASH)かは表示だけの区別。壊れたゲートは「通ったゲート」ではない。
  INCONSISTENT  終了コードは 0 なのに出力が違反を報告している。`sys.exit(1)` の書き忘れ
         1行でゲートは無力化されるので、**合格を自称しながら違反を印字している状態**を落とす。
  LIB    単体では何も起きない（＝呼ばれる側）。**実際に実行されたゲートから import されて
         いれば健全**。build*.py からしか呼ばれないものは DEAD（ランナーは build を回さない）。
  DEAD   誰からも呼ばれない＝一度も走らない検査。**失敗として落とす**。
         今回の調査で見つかった穴そのもの（書いただけで呼ばれていない）を機械で捕まえる。

■ --no-pdf（CI 用）
  刷った PDF を開く検査は、**PDF がリポジトリに無いので CI では原理的に回せない**
  （生成物は .gitignore で除外）。--no-pdf で外す。★外したものは必ず一覧に出す。
  黙って減らすと「全部通った」に見えて、今回と同じ事故になる。
  ローカルでは付けずに回すこと。PDF が無ければ落ちる＝「build を回し忘れている」の合図。
"""
import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 300          # 1ゲートあたり（秒）

# 回す対象のファイル名（build 系は副作用があるので入れない）
# ★先頭 `_` は共有ライブラリの慣習（_workbook_check.py 等）。実行対象にしない。
GATE_RE = re.compile(
    r"^(?!_)(?:[a-z0-9_]*check[a-z0-9_]*|verify.*|validate.*|audit.*|preflight.*"
    r"|qa|qa_.*|.*_gate)\.py$")

WALK_SKIP = {"__pycache__", ".git", "node_modules", ".venv", "venv"}

# 子プロセスから外す環境変数。
# ★教材の検査対象を env で切り替える設計が実在する（eng_kokkoritsu_nankan/check.py の
#   WORKBOOK_DIR は4冊を1本で検査する）。それを export したままの shell でランナーを回すと、
#   **別の本を検査して PASS** が出るのにログからは判別できない。明示的に落とす。
DROP_ENV = ("WORKBOOK_DIR", "BOOK_DIR", "CONTENT", "CONTENT_MOD", "STUDENT_NAME")

# 対象から外すもの（理由を必ず書く。理由なしに足さないこと）
SKIP = {
    # exam-quality.yml が既に専用の手順で回している（引数と seed の前提がある）
    "scripts/kyotsu_mogi2026/preflight.py": "exam-quality.yml が回す",
    "scripts/kyotsu_mogi2026/audit.py": "exam-quality.yml が回す",
    # 対象がリポジトリ全体でこのランナーの粒度（教材ディレクトリ単位）と違うため、
    # 通常のゲートとしては回さず、**最後に必ず1回**別扱いで回す（下の run_pii_gate）。
    "scripts/check_no_pii.py": "最後に別枠で回す（対象がリポジトリ全体）",
    # 引数（part 番号 / ファイル名）が必須で、単体では IndexError や usage で終わる
    "scripts/kyotsu2026_mirror/build/check_part.py": "part 番号が必須（build から呼ばれる）",
    "scripts/chugaku_dojo/post_insert_check2.py": "part 名が必須（取込後に手で回す）",
    "scripts/eng_kyotsu_2026/validate_and_build.py": "対象ファイルが必須（build から呼ばれる）",
    # 本番 DB / 本番 API につなぐ。CI から回してはいけない
    "scripts/health_check/prod_healthcheck.py": "本番DB接続が要る（railway run -s Postgres で回す）",
    "scripts/chugaku_dojo/post_insert_check.py": "本番DB接続が要る（取込後に手で回す）",
    "scripts/audit_pool_health.py": "本番APIに223回つなぐ・教材でなく出題プールの在庫監査",
    "scripts/chugaku_dojo/futeishi/post_check.py": "本番APIにつなぐ（取込後に手で回す）",
    "scripts/eiken_junichi/mogi/verify_imported.py":
        "冊子受験アプリのDBを読み返す（取込後に手で回す。講師アカウントの認証が要る）",
    # ★検査ではなく**データを書き換える**スクリプト。名前に check が入るので拾われてしまう。
    #   回すたびに教材データがスクリプト内蔵の版へ巻き戻る（実測で part1_vocab.json が戻った）。
    "scripts/eiken_junichi/fix_recheck.py": "検査でなくデータ修正（適用済み・再実行で巻き戻る）",
}

# 「検査なのにファイルを書く」ことが正当なもの（一時ファイル・出力先の作成のみ）。
# ここに無いのに書き込むゲートは実行せずに落とす（上の fix_recheck.py と同じ事故を防ぐ）。
WRITE_OK = {
    "book_exam/check_exam_book_browser.py":
        "tempfile の使い捨てディレクトリに検査用PDFと偽supabaseを置くだけ（リポジトリには書かない）",
    "book_exam/check_import_books.py":
        "tempfile の使い捨てディレクトリに検査用JSON/PDFを置き、localhostに偽Supabaseを立てるだけ（リポジトリには書かない）",
    "book_exam/check_signup.py":
        "localhost に偽 Stripe/偽 Supabase を立てて往復するだけ（外部には出ない・リポジトリには書かない）",
    "chem_camp/katex_gate.py": "KaTeX 描画用の一時HTMLを書くだけ",
    "eng_hinshi_bunkai/qa.py": "出力ディレクトリを作るだけ",
    "kyotsu2026_mirror/build/qa_machine.py": "QA レポートを書くだけ",
    "math_workbook/ia_jaku_gate.py": "KaTeX 描画用の一時HTML/PDFを書いて消すだけ",
    "math_workbook/unit_check_ia_jaku.py": "KaTeX 描画用の一時HTML/PDFを書いて消すだけ",
}

# 「検査なのに通信する」ことが正当なもの。★127.0.0.1 に自分で立てた偽サーバとの
# 往復**だけ**に限る (本番 API・外部ドメインに出るものは絶対に入れない —
# CI から本番 API を 223 回叩いた事故の再発防止がこの検出の目的)。
# 理由には「どこにつなぐか」を必ず書くこと。
NET_OK = {
    "book_exam/check_signup.py":
        "127.0.0.1 に立てた偽 Stripe/偽 Supabase と、検査対象ハンドラ (同じく 127.0.0.1) への往復のみ",
}

# 合格を自称しながら違反を印字している状態を捕まえる。
# ★`FAIL=0` `NG 0 件` は正常な集計行。`^(FAIL|NG)\b` で行頭を見る書き方だと
#   それらに当たって**通っているゲートを3本falseで落とした**（実測）。件数が1以上の形だけを見る。
# ★`×` (U+00D7) は入れない。「4 点 × 10 問」の**掛け算**で使われ、合格時の説明行を
#   INCONSISTENT で落とす（集計行で3本を誤って落としたのと同じ型の再発）。不合格マークは ✗ ❌ ✘。
# ★件数を伴わない個別の違反行（`NG: 第3問 選択肢欠落`）も拾う。件数形 `FAIL=0` とは
#   区切り文字で区別できる（前者は `:`、後者は `=`）。
# INCONSISTENT の判定から外すもの（違反文言を印字するのが**正常**なゲート）。
# ★自己テストは「わざと壊した例を検出できるか」を見るので、[NG] 行が並ぶのが合格の姿。
INCONSISTENT_OK = {
    "eng_hinshi_bunkai/selftest_gate.py": "自己テスト。わざと壊した例の検出結果を印字する",
}

# 色付きで出すゲートが実在する（check_course_price_sync.py の FAIL = "\033[31m❌\033[0m"）。
# 剥がしてから当てないと、記号が語の途中に見えて素通りする。
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

_BAD_OUT = re.compile(
    r"(?<![\w])(?:❌|✗|✘)"
    # ★行頭の `×` は違反マーク（`math_workbook/sync_check.py` が実際にこの形で出す）。
    #   行の途中の `×` は掛け算なので拾わない（「4 点 × 10 問」で正常ゲートを落とした）。
    r"|^[ \t]*×[ \t]"
    # ★ASCII の語は境界を付ける。付けないと re.I で `checking` `warning` `loading` の
    #   "ng" に当たり、英語で進捗を出すゲートが全部 INCONSISTENT になる。
    r"|(?:(?<![A-Za-z])(?:FAIL|ERROR|NG|VIOLATION|MISMATCH)(?![A-Za-z])|違反|不一致|漏洩)"
    r"[ \t]*[=:]?[ \t]*[1-9]\d*[ \t]*(?:件|$|[ \t])"
    # ★件数なしの `NG: 第5問 …` を拾う。ただし `NG: 0 件` `違反: なし` は合格の集計行。
    #   除外の先読みの**前**に `\s*` を置くとバックトラックして 0 文字に戻り、先読みが
    #   空白の位置で成功して**除外が効かない**（4巡連続でここを間違えた）。
    #   空白を先読みの中に入れ、後続に非空白を要求する。
    r"|^[ \t]*\[?(?:(?<![A-Za-z])(?:NG|FAIL|ERROR)(?![A-Za-z])|違反)\]?[ \t]*[:：]"
    r"(?![ \t]*(?:0(?:[ \t]|件|$)|なし|none\b|N/?A\b))[ \t]*\S"
    r"|^[ \t]*\[(?:(?<![A-Za-z])(?:NG|FAIL|ERROR)(?![A-Za-z])|違反)\][ \t]*"
    r"(?!0(?:[ \t]|件|$)|なし|none\b)\S"
    # ★`(件数 N)` 形（grammar_workbook/validate.py が使う）。0件は合格の集計行なので除く。
    r"|[（(]件数[ \t]*[1-9]\d*[）)]"
    # ★`[MC MATCH]` `[COUNT]` `[NO EXPL]` のような **ASCII 大文字のタグ**は違反の目印。
    #   日本語のタグ（[構造] [配点] [info]）は正常出力にも出るので当てない。
    #   実測: 主要ゲート8本の全出力で ASCII 大文字タグは1つも出ない。
    #   ★`(?-i:)` で**大文字小文字を区別**する。全体に re.I が効いているので、これが無いと
    #     `[check]` `[info]` `[LaTeX]` `[chart]` まで当たり、通っているゲート5本を落とす（実測）。
    #     さらに `[OK ]` `[PASS]` のような正常タグは明示的に除く。
    #   件数0の集計行（`[NG] 0 件`）は合格なので、ここでも除外を効かせる。
    r"|^[ \t]*(?-i:\[(?!OK|PASS|INFO|WARN|DONE|SKIP|NOTE)[A-Z][A-Z0-9 _]{1,14}\])"
    r"[ \t]*(?!0(?:[ \t]|件|$)|なし|none\b)\S",
    re.M | re.I)

# ★この正規表現は 4 巡続けて「正常なゲートを落とす／違反を見逃す」を作った。
#   目視レビューでは止まらなかったので、**表を持って起動時に自己テストする**。
#   ここに載っている形は実在ゲートの出力から取っている。増やすときは実物を見て足すこと。
_BAD_OUT_CASES = [
    # (出力の1行, 違反として拾うべきか)
    ("=== ALL PASS (14 warnings) ===", False),
    ("FAIL=0 WARN=0", False),
    ("NG 0 件 / WARN 2 件", False),
    ("NG: 0 件", False),
    ("ERROR: 0", False),
    ("違反: なし", False),
    ("[NG] 0 件", False),
    ("==== TOTAL FAIL=0  DUP=0 ====", False),
    ("ERROR=0  WARN=0", False),
    ("検査した本=4/4", False),
    ("合計 0 件", False),
    ("[配点] 4 点 × 10 問 = 40 点", False),
    ("配点は 5 × 20 = 100", False),
    ("Checking 5 files", False),
    ("warning 2 件", False),
    ("Loading 3 seeds", False),
    ("  × 、続けて白", True),
    ("NG: 第3問 選択肢が欠落", True),
    ("[NG] 第5問 解答が2つ", True),
    ("FAIL 3 件", True),
    ("❌ standard コースの name が一致しない", True),
    ("=== FAIL 1 ===", True),
    ("違反 3 件", True),
    # 2026-08-05 に増えたゲートの実際の出力（全角括弧・集計行）。表は実物に合わせる。
    ("=== ALL PASS（0 warnings）===", False),
    ("########## 検査した本 5/5 冊（PASS 5 ＋ FAIL 0 ＋ 未実行 0 ＝ 5）##########", False),
    ("=== 禁止文字 (件数 0) ===", False),
    ("=== 問題点 (件数 0) ===", False),
    ("=== 検査量の食い違い (件数 0) ===", False),
    ("=== 問題点 (件数 7) ===", True),
    ("=== 禁止文字 (件数 23) ===", True),
    ("  [MC MATCH] 比較#3: choices[1]='more' != answer_text='most'", True),
    # ★ここから下は「正常なのに落とした」実物。re.I が効いて [check] [info] [LaTeX] [chart]
    #   まで「ASCII 大文字タグ」に当たり、通っているゲート5本を落とした（2026-08-05・5回目）。
    ("[check] 全10回 / 200問 / 見出し語 200 語", False),
    ("[check] PASS  (FAIL 0 / WARN 2)", False),
    ("[info] 文法 5講 / 長文 5講 検査完了", False),
    ("[OK ] Q3 ア: derived='②' claim='②'", False),
    ("  [LaTeX] 全81問＋POINTS9件 $の対応OK／数式内に日本語なし", False),
    ("  [chart] Ａ モスクワ       年平均  6.3℃ 年降水  713.0mm OK", False),
    ("  [COUNT] 01_sentence-patterns.json: 24 questions (expected 25)", True),
    ("  [NO EXPL] 助動詞#9", True),
]


def selftest_bad_out():
    """判定表どおりに動くか。ずれていたらランナー自身を落とす。"""
    return [(t, want) for t, want in _BAD_OUT_CASES
            if bool(_BAD_OUT.search(_ANSI.sub("", t))) != want]


# PDF が無いせいで落ちたのか、中身が悪くて落ちたのかを実測で分ける。
# ★「PDFが要るか」は静的には判定しきれない（fitz を兄弟モジュール経由で使うゲートがある）。
#   実行して FileNotFoundError が .pdf を指していれば「刷っていないだけ」と分かる。
#   ★例外を握って自分の言葉に変換するゲートもあるので、日本語の言い回しも見る。
_PDF_MISSING = re.compile(r"(?:FileNotFoundError|No such file|no such file)[^\n]*\.pdf"
                          r"|PDF\s*が\s*(?:無|な)い", re.I)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def discover(filters):
    """scripts/ 以下を**再帰**で探す。

    ★1階層しか見ないと、実在して動く検査が見えないまま「DEAD にも計上されない」。
      実測で eng_therules/rulehunt01..04/check.py など 9 本が不可視だった
      （＝このファイルが撲滅したかった穴そのものが、このファイルの死角に隠れていた）。
    """
    out = []
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in WALK_SKIP and not d.startswith(".")]
        for f in sorted(files):
            if not GATE_RE.match(f):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, os.path.dirname(HERE))
            if rel in SKIP:
                continue
            label = os.path.relpath(path, HERE)
            if filters and not any(x in label for x in filters):
                continue
            out.append((label, path))
    return sorted(out)


_DECL = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
         ast.ClassDef, ast.Assign, ast.AnnAssign, ast.AugAssign)


def is_library(src):
    """「実行しても何も起きない」ファイルか。

    ★`__main__` の有無で判定してはいけない。トップレベルに print や sys.exit を直接書く
      ゲートは実在し（負のテストで検出した）、それを「ライブラリ」と誤判定すると
      **本物の検査が一度も走らないまま DEAD 扱い**になる。
      判定は「トップレベルが宣言(import/def/class/代入/docstring)だけか」で行う。
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False           # 構文エラーは実行させて CRASH で落とす
    for n in tree.body:
        if isinstance(n, _DECL):
            continue
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
            continue           # docstring
        return False           # 実行される文がある＝スクリプト
    return True


def local_imports(src):
    """このファイルが import しているモジュール名（トップレベル名のみ）。関数内 import も含む。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            out.add(n.module.split(".")[0])
    return out


_PDF_MODS = {"fitz", "pymupdf"}


def needs_pdf(path, cache):
    """PDF が無いと**何もできない**検査か（＝リポジトリのソースだけでは回せない）。

    トップレベルで fitz を import しているものだけを対象にする。関数の中で import する作りは
    「PDF を渡されたときだけ紙を見る」＝PDF が無ければ自分で飛ばせるので、対象に残す。
    ★間接依存（兄弟モジュールが fitz を使う）はここで判定しない。
      それを外すと内容検査まで CI から消えるため、**モジュールを CI に入れる**ことで解決している
      （material-gates.yml が pymupdf を入れる）。判定するのは「PDF ファイルが要るか」であって
      「fitz が要るか」ではない。
    """
    src = cache.get(path) or read(path)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for n in tree.body:
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] in _PDF_MODS for a in n.names):
            return True
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in _PDF_MODS:
            return True
    return False


_NET_CALLS = {"urlopen", "urlretrieve", "get", "post", "put", "delete", "request"}
_NET_MODS = {"requests", "httpx", "urllib", "aiohttp"}


def side_effects(src):
    """検査のはずが「書き込む」「外につなぐ」ものを見つける。

    ★`fix_recheck.py`（名前に check が入るデータ修正スクリプト）を実行してしまい、
      **回すたびに教材データが巻き戻る**事故が起きた。検査の入口が破壊的なのは論外なので
      機械で捕まえる。ネットワークも同様（CI から本番 API を 223 回叩いていた）。
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if name == "open":
                for arg in list(n.args[1:2]) + [k.value for k in n.keywords if k.arg == "mode"]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                            and any(c in arg.value for c in "wxa+"):
                        out.add("書き込み")
            elif name in ("write_text", "write_bytes", "mkdir", "makedirs"):
                out.add("書き込み")
            elif name in ("dump",) and len(n.args) >= 2:
                out.add("書き込み")           # json.dump(obj, fp)
            elif name in _NET_CALLS and isinstance(f, ast.Attribute):
                root = f.value
                while isinstance(root, ast.Attribute):
                    root = root.value
                if getattr(root, "id", "") in _NET_MODS:
                    out.add("外部通信")
    return out


def uses_argv(src):
    """引数で検査対象が変わるゲートか（引数なしで回すと『見本』を検査しかねない）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr == "argv":
            return True
    return False


_IGNORED_CACHE = {}
_GIT_OK = [True]        # git が使えたか（使えないと無視判定ができない）


def is_ignored(rel):
    """.gitignore で無視されるパスか（正当な中間物を誤って責めないため）。"""
    if rel not in _IGNORED_CACHE:
        try:
            r = subprocess.run(["git", "check-ignore", "-q", rel],
                               cwd=os.path.dirname(HERE), capture_output=True)
            _IGNORED_CACHE[rel] = (r.returncode == 0)
        except OSError:
            # ★git が無い環境で例外を投げると、45本を走らせ切った後に traceback だけ残して
            #   集計も一覧も全部消える。無視判定ができないだけなので False にして続ける。
            _IGNORED_CACHE[rel] = False
            _GIT_OK[0] = False
    return _IGNORED_CACHE[rel]


def worktree_state():
    """`scripts/` 配下のファイルの状態（path -> (サイズ, mtime)）。検査が書き換えたかを実測する。

    ★静的解析（side_effects）は helper 越しの書き込み・Path.open・shutil・subprocess を
      取りこぼす。語彙を足すのは追いかけっこなので、**実際に変わったかを測る**方を主にする。
    ★`git status --porcelain` の**行**を比べてはいけない。未追跡ディレクトリは `?? dir/` に
      畳まれるので、その中で何を書き換えても行が変わらない。教材データが巻き戻った
      `scripts/eiken_junichi/` はまさにその位置だった。ファイル単位で測る。
    ★見るのは `scripts/` と `seed-data/` だけ。このリポジトリは**並行セッション運用が前提**で、
      リポジトリ全体を見ると別セッションが直下の *.html を編集しただけで全体 FAIL になる
      （実測で enrollment.html を踏んだ）。ゲートが書き換えうる教材データはこの2つに収まる
      （seed-data は模試シードの置き場で、将来ここを書くゲートが入ると無音で通るため足した）。
    """
    state = {}
    roots = [HERE, os.path.join(os.path.dirname(HERE), "seed-data")]
    for root in roots:
      if not os.path.isdir(root):
          continue
      for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in WALK_SKIP and not d.startswith(".")]
        for f in files:
            fp = os.path.join(base, f)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            state[os.path.relpath(fp, os.path.dirname(HERE))] = (st.st_size, st.st_mtime_ns)
    return state


def run_pii_gate(env):
    """生徒の個人情報ゲート。**総括行より前**に回して、結果を総括に含める。

    ★CLAUDE.md に「検査を回す入口は1本」と書いた以上、手元でこのコマンドを叩いたときに
      PII が検査されないのは宣言と実態のずれ。CI にしか無い検査は「忘れられる検査」になる。
    ★総括行のあとに出すと `FAIL 0` と印字してから違反を並べることになり、
      「見た目は緑なのに exit 1」になる。このファイルが潰そうとしている状態そのもの。
    """
    gate = os.path.join(HERE, "check_no_pii.py")
    print("\n=== 生徒の個人情報・秘密（リポジトリ全体）===")
    if not os.path.exists(gate):
        print("  ✗ scripts/check_no_pii.py が無い（個人情報の検査がされていない）")
        return ("check_no_pii.py", "MISSING", ["個人情報の検査そのものが無い"])
    try:
        r = subprocess.run([sys.executable, gate], cwd=os.path.dirname(HERE),
                           capture_output=True, encoding="utf-8", errors="replace",
                           timeout=TIMEOUT, env=env)
        out = (r.stdout + r.stderr).strip().splitlines()
        code = r.returncode
    except subprocess.TimeoutExpired:
        out, code = [f"{TIMEOUT}秒でタイムアウト"], -9
    except Exception as e:
        out, code = [f"起動できない: {e.__class__.__name__}: {e}"], -1
    for line in (out if code else out[:3]):
        print("  " + line)
    if code:
        return ("check_no_pii.py", "PII", [x for x in out if "✗" in x][:3] or out[-3:])
    return None


def main():
    try:
        return _main()
    finally:
        _cleanup_pycache()


_PYCACHE = []


def _cleanup_pycache():
    import shutil
    for d in _PYCACHE:
        shutil.rmtree(d, ignore_errors=True)
    _PYCACHE.clear()


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filters", nargs="*", help="教材ディレクトリ名の部分一致")
    ap.add_argument("--list", action="store_true", help="対象を出すだけ")
    ap.add_argument("--no-pdf", action="store_true",
                    help="刷ったPDFを読む検査を外す（CI 用。PDFはリポジトリに無い）")
    a = ap.parse_args()

    gates = discover(a.filters)
    if a.list:
        for label, _ in gates:
            print(f"  {label}")
        print(f"\n計 {len(gates)} 本")
        return 0
    if not gates:
        print(f"✗ 対象のゲートが1つも見つからない（filters={a.filters or 'なし'}）")
        return 1

    src_cache = {p: read(p) for _, p in gates}
    env = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    # ★ゲートが兄弟モジュール（content.py / build.py）を import して中の答えを検査する形は
    #   24本ある。`import` は **pyc キャッシュ**を使い、有効性の判定はソースの mtime(秒)と
    #   サイズだけなので、`ans=3 → 4` のような**サイズが変わらない書き換え**を同じ秒に保存すると
    #   古い pyc が再利用され、**ゲートが古いデータを見て ALL PASS** になる
    #   （meiji で発見し、nihonshi_koukou_workbook でも実際に見逃しを再現した）。
    #   毎回まっさらなキャッシュ置き場を渡せば、全ゲートに一度に効く。
    #   ※`-B` / PYTHONDONTWRITEBYTECODE は**書き込みを止めるだけで既存 pyc の読み込みは止まらない**。
    #   ★作りっぱなしにすると実行のたびに1個増える（実測で97MB溜まっていた）。
    #     最後に必ず消す（下の finally）。
    _pycache = tempfile.mkdtemp(prefix="gates-pyc-")
    env["PYTHONPYCACHEPREFIX"] = _pycache
    _PYCACHE.append(_pycache)

    off = selftest_bad_out()
    if off:
        # ★ゲートを判定する側が壊れていたら、その先の結果は全部あてにならない。
        print("✗ ランナー自身の自己テストが落ちた（違反の判定表とずれている）:")
        for t, want in off:
            print(f"    {t!r} は {'違反として拾う' if want else '拾わない'} はずだった")
        return 1

    tree_before = worktree_state()
    print(f"=== 教材の品質ゲート {len(gates)} 本 ===\n")
    npass = 0
    bad, lib_pending, skipped_pdf, argv_gates = [], [], [], []
    noout = set()        # 実行できたが出力ゼロだったもの（DEAD と原因が違う）
    # label -> そのファイルが import しているモジュール名。
    # ★PASS したゲートだけを入れてはいけない。呼び出し元が**違反を検出して落ちた**とき、
    #   そのゲートが呼ぶライブラリが「誰も呼んでいない(DEAD)」と誤報告され、
    #   1件の違反が2件の FAIL になり、片方は事実と違う（デバッグを誤った方向へ誘導する）。
    #   起動できた全ゲートと、--no-pdf で外したゲート（静的に読む）を入れる。
    ran_ok = {}

    for label, path in gates:
        src = src_cache[path]
        if a.no_pdf and needs_pdf(path, src_cache):
            skipped_pdf.append(label)
            ran_ok[label] = local_imports(src)   # 実行しないが「呼び出し元」ではある
            print(f"  --    {label}  刷ったPDFが要る＝ここでは検査していない")
            continue
        if is_library(src):
            lib_pending.append((label, path))     # 呼び出し元の判定は全ゲート実行後
            continue
        eff = (side_effects(src)
               - ({"書き込み"} if label in WRITE_OK else set())
               - ({"外部通信"} if label in NET_OK else set()))
        if eff:
            # ★実行しない。検査の入口が教材データを書き換えたり本番を叩いたりするのは論外。
            bad.append((label, "SIDE-EFFECT",
                        [f"検査なのに{'と'.join(sorted(eff))}をする。実行していない。",
                         "本当に検査なら WRITE_OK (書き込み) / NET_OK (127.0.0.1 限定の通信) に"
                         "理由を書く。そうでなければ SKIP に入れる。"]))
            ran_ok[label] = local_imports(src)   # 実行しないが「呼び出し元」ではある
            print(f"  FAIL  {label}  [SIDE-EFFECT] {'/'.join(sorted(eff))}")
            continue
        if uses_argv(src):
            argv_gates.append(label)

        t0 = time.time()
        try:
            r = subprocess.run([sys.executable, os.path.basename(path)],
                               cwd=os.path.dirname(path), capture_output=True,
                               encoding="utf-8", errors="replace", timeout=TIMEOUT, env=env)
            code, out = r.returncode, (r.stdout + r.stderr).strip().splitlines()
            crashed = "Traceback (most recent call last)" in r.stderr
        except subprocess.TimeoutExpired:
            code, out, crashed = -9, [f"{TIMEOUT}秒でタイムアウト"], True
        except Exception as e:
            # ★1本のゲートの都合でランナーごと死ぬと、残りが1本も走らない。
            #   そのゲートだけ CRASH にして続ける（集計は必ず最後まで出す）。
            code, out, crashed = -1, [f"起動できない: {e.__class__.__name__}: {e}"], True
        dt = time.time() - t0
        last = (out[-1] if out else "")[:60]
        ran_ok[label] = local_imports(src)   # 起動できた＝呼び出し元として数える（結果は問わない）
        joined = _ANSI.sub("", "\n".join(out))

        if code != 0 and _PDF_MISSING.search(joined):
            # 刷った PDF が無いだけ。CI には PDF が無いので落とさず一覧に出す。
            # ローカル（--no-pdf 無し）では「build を回し忘れている」ので落とす。
            if a.no_pdf:
                skipped_pdf.append(label)
                print(f"  --    {label}  刷ったPDFが無い＝ここでは検査していない")
            else:
                bad.append((label, "PDF-MISSING",
                            ["刷った PDF が無い。build を回してから再実行すること"]))
                print(f"  FAIL  {label}  ({dt:.1f}s) [PDF-MISSING] {last}")
        elif code != 0:
            kind = "CRASH" if crashed else "VIOLATION"
            detail = [x for x in out if _BAD_OUT.search(_ANSI.sub("", x))][:3] or out[-4:]
            bad.append((label, kind, detail))
            print(f"  FAIL  {label}  ({dt:.1f}s) [{kind}] {last}")
        elif not out:
            # 出力ゼロ＝検査した証拠が無い。静的判定を外れたライブラリ（トップレベルに
            # sys.path 操作がある等）はここに落ちるので、呼び出し元の有無で決め直す。
            # ★「誰も呼んでいない」と「何も出力しない」は別の話。原因を断定しないよう区別する。
            noout.add(label)
            lib_pending.append((label, path))
        elif _BAD_OUT.search(joined) and label not in INCONSISTENT_OK:
            # 合格を自称しながら違反を印字している（sys.exit(1) の書き忘れ等）
            bad.append((label, "INCONSISTENT",
                        [x for x in out if _BAD_OUT.search(_ANSI.sub("", x))][:3]))
            print(f"  FAIL  {label}  ({dt:.1f}s) [INCONSISTENT] {last}")
        else:
            npass += 1
            print(f"  PASS  {label}  ({dt:.1f}s)  {last}")

    # --- ライブラリは「実際に走ったゲートから呼ばれているか」で判定する。
    #     ★正規表現で「引用符に囲まれた単語」を探す実装だと、import ですらない文字列 1 個で
    #       LIB と誤報告する（負のテストで確認）。ast の import だけを数える。
    #     ★build*.py からしか呼ばれないものは DEAD。ランナーは build を回さないので実行されない。
    lib = []
    for label, path in lib_pending:
        mod = os.path.basename(path)[:-3]
        # ★同一ディレクトリ限定にすると、sys.path を足して scripts/ 直下の共通ライブラリを
        #   呼ぶ形（実在する）が「誰も呼んでいない」と誤報告される。
        #   かといって制約を外すと、**別ディレクトリの同名モジュール**（どの教材にも verify.py が
        #   ある）を呼び出し元と誤認して DEAD を見逃す（負のテストで検出）。
        #   → ライブラリが scripts/ 直下なら誰が呼んでもよい、サブディレクトリなら同じ階層だけ。
        d = os.path.dirname(label)
        callers = [g for g, imps in ran_ok.items()
                   if mod in imps and (d == "" or os.path.dirname(g) == d)]
        if callers:
            lib.append((label, callers[0]))
            print(f"  LIB   {label}  ← {os.path.basename(callers[0])} が呼ぶ")
        else:
            why = ("実行されたゲートのどれからも import されていない＝一度も走らない検査"
                   if label not in noout else
                   "実行しても何も出力せず、どのゲートからも import されていない")
            bad.append((label, "DEAD" if label not in noout else "NO-OUTPUT", [why]))
            print(f"  {'DEAD  ' if label not in noout else 'NO-OUT'} {label}  "
                  + ("誰も呼んでいない" if label not in noout else "何も出力しない"))

    # ★検査が作業ツリーを書き換えていないかを**実測**する。静的解析(side_effects)は
    #   helper 越しの書き込みや subprocess を取りこぼすので、こちらが本命の網。
    tree_after = worktree_state()
    changed = sorted(k for k in set(tree_before) | set(tree_after)
                     if tree_before.get(k) != tree_after.get(k))
    # gitignore 済みの中間物（_katex_gate.html 等）は正当なので除く
    changed = [k for k in changed if not is_ignored(k)]
    if changed and not _GIT_OK[0]:
        # git が無いと .gitignore 済みの中間物を除けないので、参考情報にとどめる
        print(f"\n--- 参考: {len(changed)} 件のファイルが変わった"
              f"（git が使えず、無視すべき中間物を区別できない）---")
        for x in changed[:5]:
            print(f"      {x}")
    elif changed:
        bad.append(("(ランナー全体)", "WROTE",
                    ["検査を回しただけでファイルが変わった＝どれかが書き換えている"]
                    + [f"  {x}" for x in changed[:5]]))
        print(f"\n  ✗ 検査を回しただけで {len(changed)} 件のファイルが変わった:")
        for x in changed[:5]:
            print(f"      {x}")

    # ★総括行より前に PII を回す（あとに出すと「FAIL 0」と印字してから違反を並べることになる）。
    if a.filters:
        # 絞り込み実行では全体走査をしない。★黙って飛ばさない（skipped_pdf と同じ作法）。
        print("\n--- ここでは検査していない: 生徒の個人情報（絞り込み実行のため全体走査を省略）---")
        print("  → `python3 scripts/run_all_gates.py`（引数なし）か "
              "`python3 scripts/check_no_pii.py` で回すこと。")
    else:
        pii = run_pii_gate(env)
        if pii:
            bad.append(pii)

    # ★このランナーは「検査を書いたのに呼ばれていない」を撲滅するために作ったのに、
    #   **自分が回す本数**は無検査だった。未追跡のゲートは CI のチェックアウトに存在しないので
    #   手元では走るが CI では1度も走らない（実測で新設3本が該当し、誰も報告しなかった）。
    #   ★git が無い環境で例外を投げると、45本を走らせ切った後に traceback だけ残して
    #     集計も一覧も全部消える。このファイルの作法どおり「ここでは検査していない」と出す。
    tracked = None
    try:
        r = subprocess.run(["git", "ls-files", "-z", "scripts"],
                           cwd=os.path.dirname(HERE), capture_output=True)
        if r.returncode == 0:
            tracked = {p.decode("utf-8", "surrogateescape")
                       for p in r.stdout.split(b"\0") if p}
    except OSError as e:
        print(f"\n--- ここでは検査していない: ゲートの追跡状態（git が使えない: {e}）---")
    if tracked is None:
        if not os.path.isdir(os.path.join(os.path.dirname(HERE), ".git")):
            print("\n--- ここでは検査していない: ゲートの追跡状態（.git が無い）---")
    else:
        untracked = [label for label, path in gates
                     if os.path.relpath(path, os.path.dirname(HERE)) not in tracked]
        if untracked:
            bad.append(("(ランナー全体)", "UNTRACKED",
                        ["git に入っていないゲートは CI では1度も走らない（コミットすること）"]
                        + [f"  {x}" for x in untracked[:8]]))
            print(f"\n  ✗ git に入っていないゲートが {len(untracked)} 本"
                  f"（手元では走るが CI では走らない）:")
            for x in untracked[:8]:
                print(f"      {x}")
        # ★「ゲートが1本消えた」は内訳の等式では**原理的に**捕まえられない
        #   （counted も len(gates) も同じ discover() から出るので恒等式になる）。
        #   git に入っているゲートの一覧と突き合わせて、消えた・改名されたものを落とす。
        known = {p for p in tracked
                 if GATE_RE.match(os.path.basename(p)) and p not in SKIP}
        found = {os.path.relpath(path, os.path.dirname(HERE)) for _, path in gates}
        lost = sorted(known - found)
        if lost and not a.filters:
            bad.append(("(ランナー全体)", "LOST",
                        ["git にあるのに発見されないゲート（消した？改名した？）"]
                        + [f"  {x}" for x in lost[:8]]))
            print(f"\n  ✗ git にあるのに発見されないゲートが {len(lost)} 本:")
            for x in lost[:8]:
                print(f"      {x}")

    # 内訳の等式。★除外は**ラベル文字列でなく対象集合**で判定する。
    #   `run_pii_gate` が返すラベルは "(ランナー全体)" ではないので、文字列比較にすると
    #   **PII 違反のたびに「内訳が合わない」が余分に出る**（生徒の氏名が混入した最悪の場面で
    #   デバッグを誤誘導する）。実測で FAIL 1件が2件になった。
    _labels = {label for label, _ in gates}
    counted = npass + len([b for b in bad if b[0] in _labels]) + len(lib) + len(skipped_pdf)
    if counted != len(gates):
        bad.append(("(ランナー全体)", "COUNT",
                    [f"内訳の合計 {counted} が対象 {len(gates)} 本と合わない"
                     "（どこかで黙って落ちている）"]))
        print(f"\n  ✗ 内訳の合計 {counted} ≠ 対象 {len(gates)} 本")

    print(f"\n=== PASS {npass} / FAIL {len(bad)} / LIB {len(lib)}（check 経由で走る）===")
    if skipped_pdf:
        # ★黙って減らさない。「全部通った」に見えるのが一番あぶない。
        print(f"\n--- ここでは検査していない {len(skipped_pdf)} 本（刷ったPDFが要る）---")
        for label in skipped_pdf:
            print(f"  - {label}")
        print("  → 紙の検査はローカルで build 後に `python3 scripts/run_all_gates.py` を回すこと。")
    if argv_gates:
        # ★引数で対象が変わるゲートを引数なしで回すと「見本」を検査して PASS しうる。
        #   実測で kaki_koushuu_eng/check.py が sample_content を検査して緑になっていた。
        print(f"\n--- 引数で検査対象が変わる {len(argv_gates)} 本（何を見たか出力で確認すること）---")
        for label in argv_gates:
            print(f"  ? {label}")
    if bad:
        print("\n--- 落ちたゲート ---")
        for label, kind, detail in bad:
            print(f"  ✗ {label}  [{kind}]")
            for x in detail:
                print(f"      {x[:100]}")
        print("\n  ★CRASH / DEAD / INCONSISTENT は「通った」ではない。検査していないだけ。")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
