#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英語学習アプリの DB スキーマ (supabase/migrations/*.sql) のゲート。

    python3 scripts/english_schema/check_schema.py

■ 2 段構えになっている
  1. 静的検査 … SQL を読んで「RLS を有効にし忘れたテーブル」「ポリシーの無い操作」
                「search_path を固定していない security definer 関数」等を落とす。
                DB は要らないので CI (material-gates.yml) でも必ず回る。
  2. 実DB検査 … 使い捨ての Postgres に stubs → migrations → 期待値テストを流す。
                supabase/tests/10_schema_expectations.sql が本体 (58 件)。
                Postgres が無ければ **回さないことを明示して** 静的検査だけで終わる。

■ なぜ静的検査が要るか (実DBテストがあるのに)
  RLS は「ポリシーを書き忘れたテーブル」が一番危ない。書き忘れたテーブルは
  期待値テストにも書かれていないので、**実DBテストは緑のまま通り抜ける**。
  「テーブルを足したのに RLS を足していない」を捕まえられるのは静的検査の方。

■ 引数を取らない
  CLAUDE.md の「引数で検査対象が変わるゲートを引数なしで回すと見本を検査して緑になる」
  を踏まないため、対象は常に supabase/migrations/*.sql 全部。何を見たかは必ず印字する。
"""
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIG_DIR = os.path.join(ROOT, "supabase", "migrations")
TEST_DIR = os.path.join(ROOT, "supabase", "tests")
STUBS = os.path.join(TEST_DIR, "00_local_stubs.sql")
EXPECT = os.path.join(TEST_DIR, "10_schema_expectations.sql")

# 元の設計書にあるテーブル。ここから 1 つでも欠けたら失敗させる
# (migration を分割・改名したときに「消えたのに気づかない」を防ぐ)。
EXPECTED_TABLES = [
    "profiles", "books", "questions", "attempts", "answers", "annotations", "review_items",
]

# ポリシーが無くてよい操作。**理由を必ず書く**。理由なしに足さないこと。
POLICY_EXEMPT = {
    ("profiles", "delete"): "退会は auth.users を消して cascade で落とす。delete 権限自体を配っていない",
    ("attempts", "update"): "提出も採点も submit_attempt() 経由。直接の UPDATE 権限を配っていない",
}

problems = []


def ng(msg):
    problems.append(msg)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def strip_sql_comments(sql):
    """`--` 行コメントを落とす。コメントの中の create table を数えないため。"""
    return re.sub(r"--[^\n]*", "", sql)


# =============================================================================
# 静的検査
# =============================================================================
def static_checks(mig_files):
    all_sql = ""
    for path in mig_files:
        all_sql += "\n" + strip_sql_comments(read(path))

    # --- 1. ファイル名が Supabase CLI の形式か -------------------------------
    for path in mig_files:
        name = os.path.basename(path)
        if not re.match(r"^\d{14}_[a-z0-9_]+\.sql$", name):
            ng(f"migration 名が Supabase CLI の形式でない: {name} "
               f"(期待: 20260813010000_name.sql)")

    # --- 2. 期待するテーブルが全部あるか ------------------------------------
    created = re.findall(r"create\s+table\s+(?:if\s+not\s+exists\s+)?public\.(\w+)",
                         all_sql, re.I)
    for t in EXPECTED_TABLES:
        if t not in created:
            ng(f"テーブル public.{t} を作る migration が無い")

    # --- 3. すべてのテーブルで RLS が有効か ----------------------------------
    rls_on = set(re.findall(r"alter\s+table\s+public\.(\w+)\s+enable\s+row\s+level\s+security",
                            all_sql, re.I))
    for t in created:
        if t not in rls_on:
            ng(f"public.{t} に RLS が無い — 誰でも全行を読める "
               f"(alter table public.{t} enable row level security)")

    # --- 4. 4 操作すべてにポリシーがあるか ----------------------------------
    # `create policy <名前> on public.<表> for <操作>`
    pol = re.findall(
        r"create\s+policy\s+\"?(\w+)\"?\s+on\s+public\.(\w+)\s+for\s+(select|insert|update|delete|all)",
        all_sql, re.I)
    by_table = {}
    for _, table, action in pol:
        by_table.setdefault(table, set()).add(action.lower())
    for t in sorted(rls_on):
        acts = by_table.get(t, set())
        if "all" in acts:
            continue
        for a in ("select", "insert", "update", "delete"):
            if a not in acts and (t, a) not in POLICY_EXEMPT:
                ng(f"public.{t} に {a} のポリシーが無い — RLS が有効なので "
                   f"その操作は誰にもできない (意図的なら POLICY_EXEMPT に理由を書く)")

    # --- 5. ポリシーを anon に配っていないか --------------------------------
    for m in re.finditer(r"create\s+policy\s+\"?(\w+)\"?\s+on\s+([\w.]+)[^;]*?\bto\s+([\w\s,]+?)\s+(using|with)",
                         all_sql, re.I | re.S):
        roles = {r.strip().lower() for r in m.group(3).split(",")}
        if "anon" in roles or "public" in roles:
            ng(f"ポリシー {m.group(1)} が anon/public 向けになっている ({m.group(2)})")

    # --- 6. security definer 関数の search_path が固定されているか ----------
    # 固定しないと呼び出し側が search_path を差し替えて別の表を読ませられる。
    for m in re.finditer(r"create\s+or\s+replace\s+function\s+([\w.]+)\s*\((.*?)\)(.*?)\bas\s+\$\$",
                         all_sql, re.I | re.S):
        head = m.group(3)
        if re.search(r"security\s+definer", head, re.I) and not re.search(
                r"set\s+search_path\s*=", head, re.I):
            ng(f"security definer 関数 {m.group(1)}() に search_path の固定が無い")

    # --- 7. 何度流しても安全か ----------------------------------------------
    for path in mig_files:
        sql = strip_sql_comments(read(path))
        base = os.path.basename(path)
        for m in re.finditer(r"create\s+table\s+(?!if\s+not\s+exists)([\w.]+)", sql, re.I):
            ng(f"{base}: create table {m.group(1)} に if not exists が無い (2 回流すと落ちる)")
        for m in re.finditer(r"create\s+index\s+(?!if\s+not\s+exists)([\w.]+)", sql, re.I):
            ng(f"{base}: create index {m.group(1)} に if not exists が無い")
        # create policy は if not exists を持てないので、直前に drop policy if exists が要る
        dropped = {mm.group(1).lower() for mm in
                   re.finditer(r"drop\s+policy\s+if\s+exists\s+\"?(\w+)\"?", sql, re.I)}
        for mm in re.finditer(r"create\s+policy\s+\"?(\w+)\"?", sql, re.I):
            if mm.group(1).lower() not in dropped:
                ng(f"{base}: ポリシー {mm.group(1)} に対応する "
                   f"drop policy if exists が無い (2 回流すと落ちる)")
        for mm in re.finditer(r"create\s+trigger\s+(\w+)", sql, re.I):
            if not re.search(r"drop\s+trigger\s+if\s+exists\s+" + re.escape(mm.group(1)),
                             sql, re.I):
                ng(f"{base}: トリガ {mm.group(1)} に対応する drop trigger if exists が無い")
        for mm in re.finditer(r"create\s+view\s+([\w.]+)", sql, re.I):
            if not re.search(r"drop\s+view\s+if\s+exists\s+" + re.escape(mm.group(1)),
                             sql, re.I):
                ng(f"{base}: view {mm.group(1)} に対応する drop view if exists が無い")

    # --- 8. 参照先が先に作られているか --------------------------------------
    known = {"auth.users"}
    for path in mig_files:
        sql = strip_sql_comments(read(path))
        base = os.path.basename(path)
        # 1 ファイルの中では create table の順に見る
        events = []
        for m in re.finditer(r"create\s+table\s+(?:if\s+not\s+exists\s+)?([\w.]+)", sql, re.I):
            events.append((m.start(), "create", m.group(1).lower()))
        for m in re.finditer(r"references\s+([\w.]+)\s*\(", sql, re.I):
            events.append((m.start(), "ref", m.group(1).lower()))
        for _, kind, name in sorted(events):
            if kind == "create":
                known.add(name)
            elif name not in known:
                ng(f"{base}: {name} を参照しているが、その時点でまだ作られていない")

    # --- 9. テスト用のスタブが本番の migration に紛れていないか -------------
    for path in mig_files:
        sql = read(path)
        if re.search(r"create\s+(?:or\s+replace\s+)?function\s+auth\.uid", sql, re.I) or \
           re.search(r"create\s+table\s+(?:if\s+not\s+exists\s+)?auth\.users", sql, re.I):
            ng(f"{os.path.basename(path)}: auth.users / auth.uid() を自分で作っている。"
               f"Supabase の実体を上書きする。スタブは supabase/tests/ に置くこと")

    # --- 10. 実DBテストが存在するか -----------------------------------------
    for p in (STUBS, EXPECT):
        if not os.path.exists(p):
            ng(f"実DBテストのファイルが無い: {os.path.relpath(p, ROOT)}")

    # --- 11. seed の設問と、問題冊子 PDF の設問がずれていないか -------------
    check_seed_matches_pdf()

    return {"tables": created, "rls": rls_on, "policies": len(pol)}


SEED = os.path.join(ROOT, "supabase", "seed.sql")
PDF_BUILDER = os.path.join(ROOT, "supabase", "demo", "build_sample_pdf.py")

# seed.sql の 1 冊目 (5eed0001…) の設問タプルから
#   number, page, answer_type, choice_count, correct_answer, points
# を取る。値の並びは seed.sql の insert の列順に依存しているので、
# 列を足すときはここも直すこと (ずれたら「取れない」で落ちる)。
_SEED_Q = re.compile(
    r"\('5eedaa\w+-[^']+',\s*'5eed0001-[^']+',\s*"
    r"(\d+),\s*(\d+),\s*'(\w+)',\s*(\d+|null),\s*'([^']*)',\s*"
    r"(?:null|array\[[^\]]*\]),\s*(\d+),", re.S)


def check_seed_matches_pdf():
    """答案 (seed.sql) と問題冊子 (PDF ビルダー) の設問が一対一で対応しているか。

    ★ 設問文は PDF の中にあり、DB 側は「何ページの第何問か」しか持たない。
      片方だけ直すと **画面の第3問と冊子の第3問が違う問題を指す**。
      生徒には気づけない形でずれるので、機械で止める。
    """
    if not os.path.exists(SEED):
        return                                  # seed は必須ではない
    if not os.path.exists(PDF_BUILDER):
        ng("supabase/seed.sql はあるのに問題冊子のビルダーが無い "
           "(supabase/demo/build_sample_pdf.py)")
        return

    seed_rows = {}
    for m in _SEED_Q.finditer(read(SEED)):
        no, page, atype, cc, _ans, pts = m.groups()
        seed_rows[int(no)] = (int(page), atype, None if cc == "null" else int(cc), int(pts))
    if not seed_rows:
        ng("supabase/seed.sql から設問を 1 件も読めない (列順が変わった可能性)")
        return

    # ビルダーの QUESTIONS を import せずに読む (import すると副作用の心配がある)
    src = read(PDF_BUILDER)
    ns = {}
    try:
        block = re.search(r"^QUESTIONS = \[.*?^\]", src, re.S | re.M).group(0)
        exec(compile(block, PDF_BUILDER, "exec"), ns)     # リテラルだけの代入
    except Exception as e:
        ng(f"問題冊子のビルダーから QUESTIONS を読めない: {type(e).__name__}: {e}")
        return

    pdf_rows = {no: (page, ("choice" if ch else "short"), len(ch) if ch else None, pts)
                for no, page, _stem, ch, pts in ns["QUESTIONS"]}

    if set(seed_rows) != set(pdf_rows):
        ng(f"設問番号が食い違う — seed={sorted(seed_rows)} / 冊子={sorted(pdf_rows)}")
        return
    for no in sorted(seed_rows):
        if seed_rows[no] != pdf_rows[no]:
            ng(f"第{no}問がずれている — "
               f"seed=(ページ{seed_rows[no][0]}, {seed_rows[no][1]}, "
               f"選択肢{seed_rows[no][2]}, {seed_rows[no][3]}点) / "
               f"冊子=(ページ{pdf_rows[no][0]}, {pdf_rows[no][1]}, "
               f"選択肢{pdf_rows[no][2]}, {pdf_rows[no][3]}点)")

    pdf = os.path.join(ROOT, "supabase", "demo", "sample-book.pdf")
    if not os.path.exists(pdf):
        ng("問題冊子 PDF が無い (python3 supabase/demo/build_sample_pdf.py で作る)")
    print(f"  [check] 答案と問題冊子の対応 {len(seed_rows)} 問（番号・ページ・形式・配点）")


# =============================================================================
# 実DB検査
# =============================================================================
# 本番に向けて流さないための拒否リスト (server/main.py の mirror 防御と同じ考え方)
PROD_MARKERS = ("railway.app", "rlwy.net", "railway.internal", "supabase.com", "supabase.co",
                "amazonaws.com", "neon.tech")


def find_psql():
    """(runner, ラベル) を返す。runner(sql_path, dbname) -> subprocess.CompletedProcess"""
    dsn = os.environ.get("ENGLISH_SCHEMA_TEST_DSN", "").strip()
    if dsn:
        low = dsn.lower()
        hit = [m for m in PROD_MARKERS if m in low]
        if hit:
            ng(f"ENGLISH_SCHEMA_TEST_DSN が本番らしいホストを指している ({hit[0]})。"
               f"使い捨ての DB を作って消すので本番には向けないこと")
            return None, None
        return ("dsn", dsn), f"ENGLISH_SCHEMA_TEST_DSN ({dsn.split('@')[-1]})"

    # 手元の Postgres (root で回していて postgres ユーザがいるとき)
    if shutil.which("psql") and os.geteuid() == 0:
        try:
            import pwd
            pwd.getpwnam("postgres")
        except (ImportError, KeyError):
            return None, None
        r = subprocess.run(["su", "postgres", "-c", "psql -tAc 'select 1'"],
                           capture_output=True, text=True, timeout=20)
        if r.returncode == 0:
            return ("local", None), "手元の Postgres (unix socket)"
    return None, None


def psql(conn, dbname, args, timeout=120):
    kind, dsn = conn
    if kind == "dsn":
        base = dsn.rsplit("/", 1)[0] + "/" + dbname if dbname else dsn
        return subprocess.run(["psql", "-q", "-v", "ON_ERROR_STOP=1", "-d", base] + args,
                              capture_output=True, text=True, timeout=timeout)
    import shlex
    cmd = "psql -q -v ON_ERROR_STOP=1 " + (f"-d {shlex.quote(dbname)} " if dbname else "")
    cmd += " ".join(shlex.quote(a) for a in args)
    return subprocess.run(["su", "postgres", "-c", cmd],
                          capture_output=True, text=True, timeout=timeout)


def live_checks(conn, mig_files):
    """使い捨ての DB に流して、期待値テストを回す。migration は 2 回流して冪等性も見る。"""
    db = f"engschema_gate_{os.getpid()}"
    try:
        r = psql(conn, None, ["-c", f'drop database if exists {db}',
                              "-c", f'create database {db}'])
        if r.returncode:
            ng(f"検査用 DB を作れない: {(r.stderr or r.stdout).strip()[:200]}")
            return
        # 1 巡目 + 2 巡目 (冪等性)。stubs も migrations も何度流しても通ること。
        for lap in (1, 2):
            for path in [STUBS] + mig_files:
                r = psql(conn, db, ["-f", path])
                if r.returncode:
                    err = [x for x in (r.stderr or "").splitlines() if "ERROR" in x]
                    ng(f"{lap} 巡目で {os.path.basename(path)} が流せない: "
                       f"{(err[0] if err else (r.stderr or r.stdout)).strip()[:200]}")
                    return
        print("  [live] stubs + migrations を 2 回流せた (冪等)")

        r = psql(conn, db, ["-f", EXPECT], timeout=180)
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode:
            for line in out.splitlines():
                if "[fail]" in line or "ERROR" in line:
                    ng(f"期待値テスト: {line.strip()[:220]}")
                    break
            else:
                ng(f"期待値テストが落ちた: {out.strip()[-220:]}")
            return
        for line in out.splitlines():
            if "[ok]" in line:
                print("  [live] " + line.split("NOTICE:")[-1].strip())
        if "全ての検査を通過" not in out:
            ng("期待値テストが最後まで到達していない (途中で終わっている)")
    except subprocess.TimeoutExpired:
        ng("実DB検査がタイムアウトした")
    finally:
        try:
            psql(conn, None, ["-c", f'drop database if exists {db}'])
        except Exception:
            pass


# =============================================================================
def main():
    if not os.path.isdir(MIG_DIR):
        print(f"✗ {os.path.relpath(MIG_DIR, ROOT)} が無い")
        return 1

    mig_files = sorted(os.path.join(MIG_DIR, f)
                       for f in os.listdir(MIG_DIR) if f.endswith(".sql"))
    if not mig_files:
        # ★ 0 件で ALL PASS を出さない (「検査したつもり」の典型)
        print("✗ supabase/migrations/*.sql が 1 本も無い — 検査対象が空")
        return 1

    print("=== 英語学習アプリ スキーマゲート ===")
    print(f"検査対象 {len(mig_files)} 本:")
    for p in mig_files:
        print(f"  - supabase/migrations/{os.path.basename(p)}")

    info = static_checks(mig_files)
    print(f"  [check] テーブル {len(info['tables'])} / RLS 有効 {len(info['rls'])} "
          f"/ ポリシー {info['policies']} 件")

    conn, label = find_psql()
    if conn:
        print(f"  [live] {label} に使い捨て DB を作って実際に流す")
        live_checks(conn, mig_files)
    else:
        # ★ 黙って飛ばさない。飛ばしたことを必ず出す (CLAUDE.md の約束)。
        print("  [skip] 実DB検査は未実行 — Postgres が見つからない。")
        print("         手元で回すには: ENGLISH_SCHEMA_TEST_DSN=postgresql://localhost/postgres "
              "python3 scripts/english_schema/check_schema.py")

    print()
    if problems:
        print(f"=== 問題 (件数 {len(problems)}) ===")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    print("=== ALL PASS (問題 0 件) ===")
    return 0


sys.exit(main())
