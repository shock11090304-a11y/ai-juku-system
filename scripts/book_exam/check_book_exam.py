#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冊子受験画面 (exam-book*) のゲート。

    python3 scripts/book_exam/check_book_exam.py

■ 何を見るか
  1. **往復検査** — exam-book-model.mjs を node で実際に動かし、意地の悪い入力から
     「クライアントが送る JSON」を作って、使い捨て Postgres の strokes_are_valid() に
     食わせる。保証したいのは
         クライアントが送れるもの ⊆ DB が受け取るもの
     これが崩れると「画面では保存したつもりなのに DB に拒否される」= 書き込みの消失。
  2. **静的検査** — 設計 (docs/book-exam.md) で「これをやると壊れる」と結論した書き方を
     コードから探す。列単位 grant があるので upsert が使えない、update は返却行数で
     判定しないと 0 行でも成功に見える、等。

■ 引数を取らない
  CLAUDE.md の「引数で検査対象が変わるゲートを引数なしで回すと見本を検査して緑になる」を
  踏まないため、対象は常に「配信する exam-book* 全部」。何を見たかは必ず印字する。

■ 実DB検査が回せないとき
  Postgres が無ければ往復検査は実行しないが、**飛ばしたことを必ず印字する**。
  静的検査は常に回る。
"""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL = os.path.join(ROOT, "exam-book-model.mjs")
ROUNDTRIP = os.path.join(ROOT, "scripts", "book_exam", "roundtrip_strokes.mjs")
MIG_DIR = os.path.join(ROOT, "supabase", "migrations")
STUBS = os.path.join(ROOT, "supabase", "tests", "00_local_stubs.sql")
VENDOR = os.path.join(ROOT, "vendor", "pdfjs")

problems = []


def ng(msg):
    problems.append(msg)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def app_files():
    """配信する exam-book* を全部。存在するものだけ返す。"""
    out = []
    for f in sorted(os.listdir(ROOT)):
        if re.match(r"^exam-book.*\.(mjs|html|css)$", f):
            out.append(os.path.join(ROOT, f))
    return out


# =============================================================================
# 静的検査
# =============================================================================
def static_checks(files):
    srcs = {p: read(p) for p in files}
    js = {p: s for p, s in srcs.items() if p.endswith(".mjs")}

    # --- 1. pdf.js の版が vendor と参照で一致しているか ----------------------
    ver_file = os.path.join(VENDOR, "VERSION")
    if not os.path.exists(ver_file):
        ng("vendor/pdfjs/VERSION が無い (版を照合できない)")
    else:
        want = read(ver_file).strip()
        # vendor に版が 2 つ同居していないか (v3 と v6 が混ざる事故を止める)
        stray = [f for f in os.listdir(VENDOR)
                 if re.match(r"^pdf.*\.(js|mjs)$", f)
                 and f not in ("pdf.min.mjs", "pdf.worker.min.mjs")]
        if stray:
            ng(f"vendor/pdfjs に想定外のビルドが同居している: {stray}")
        refs = set()
        for p, s in srcs.items():
            for m in re.finditer(r"/vendor/pdfjs/[\w.]+\?v=([\d.]+)", s):
                refs.add(m.group(1))
        for r in refs:
            if r != want:
                ng(f"pdf.js の参照が ?v={r} だが vendor/pdfjs/VERSION は {want}")
        if js and not refs:
            ng("pdf.js を読み込んでいる箇所が 1 つも無い (?v= 付きで参照すること)")

    # --- 2. answers に upsert を使っていないか -------------------------------
    # 列単位の grant のため PostgREST の upsert は **初回の insert から 42501**。
    # 使うと全問白紙 0 点になる。
    for p, s in js.items():
        for m in re.finditer(r"\.from\(\s*['\"]answers['\"]\s*\)[\s\S]{0,200}?\.upsert\(", s):
            ng(f"{os.path.basename(p)}: answers に .upsert( を使っている "
               f"(列単位の grant があるので初回から 42501 になる)")

    # --- 3. update / insert の結果を行数で見ているか -------------------------
    # 提出後の .update() は 0 行更新でもエラーにならない。返却行を見ないと
    # 「保存しました」と出しながら書かれていない状態が作れる。
    for p, s in js.items():
        for m in re.finditer(r"\.(update|insert)\(", s):
            tail = s[m.end():m.end() + 300]
            if ".select(" not in tail:
                line = s[:m.start()].count("\n") + 1
                ng(f"{os.path.basename(p)}:{line} .{m.group(1)}() に .select() が無い "
                   f"(返却行数で判定しないと 0 行でも成功に見える)")

    # --- 4. CDN 直リンクを持ち込んでいないか ---------------------------------
    for p, s in srcs.items():
        for m in re.finditer(r"https?://(?!\S*supabase\.co)[\w.-]*(cdn|unpkg|jsdelivr|cdnjs)[\w.-]*/",
                             s, re.I):
            ng(f"{os.path.basename(p)}: CDN 直リンクがある ({m.group(0)})。vendor に固定すること")

    # --- 5. モデルを写経していないか ----------------------------------------
    # 往復検査がモデルを import せず自前で計算していたら、本物が壊れても緑になる。
    if os.path.exists(ROUNDTRIP):
        rt = read(ROUNDTRIP)
        if "exam-book-model.mjs" not in rt:
            ng("roundtrip_strokes.mjs が exam-book-model.mjs を import していない "
               "(写経していると本物が壊れても緑になる)")

    # --- 6. no-cache ヘッダ --------------------------------------------------
    # 保存形式を直した日に、古い exam-book-model.mjs を掴んだ端末が古い形式で書き続ける。
    vj = os.path.join(ROOT, "vercel.json")
    if js and os.path.exists(vj):
        conf = read(vj)
        if "exam-book" not in conf:
            ng("vercel.json に exam-book* の no-cache 指定が無い "
               "(古いモデルを掴んだ端末が古い形式で書き続ける)")

    # --- 7. anon 以外のキーを貼れないようにしているか ------------------------
    # ★ 「service_role という文字列があるか」を見ない。それだと注意書きに反応して
    #   赤くなり、注意書きを消す方向に圧力がかかる。**実際に貼られている値**を見る。
    cfg = os.path.join(ROOT, "exam-book-config.mjs")
    if os.path.exists(cfg):
        s = read(cfg)
        if "assertAnonKey" not in s:
            ng("exam-book-config.mjs に assertAnonKey() が無い "
               "(service_role を貼ると RLS が全部素通りする)")
        m = re.search(r"anonKey\s*:\s*['\"]([^'\"]*)['\"]", s)
        key = m.group(1) if m else ""
        if key.startswith("sb_secret_"):
            ng("exam-book-config.mjs に secret キーが貼られている")
        parts = key.split(".")
        if len(parts) == 3:
            import base64
            try:
                pad = parts[1] + "=" * (-len(parts[1]) % 4)
                claims = json.loads(base64.urlsafe_b64decode(pad))
                if claims.get("role") not in (None, "anon"):
                    ng(f"exam-book-config.mjs の anonKey の role が "
                       f"\"{claims.get('role')}\" になっている")
            except Exception:
                pass

    # --- 8. answers の update に余計な列を混ぜていないか ----------------------
    # 行オブジェクトをそのまま .update(row) に渡すと id / is_correct が payload に入り、
    # 列 grant に無いので permission denied。★ 0 点になるのに画面は普通に動く。
    ALLOWED = {"user_answer", "time_spent_sec"}
    for p, s in js.items():
        for m in re.finditer(r"\.from\(\s*['\"]answers['\"]\s*\)([\s\S]{0,400}?)\.update\(([^)]*)\)", s):
            arg = m.group(2).strip()
            if arg.startswith("answerPatch("):
                continue          # 送信オブジェクトを作る唯一の関数を通っている
            keys = set(re.findall(r"(\w+)\s*:", arg))
            if not arg.startswith("{"):
                ng(f"{os.path.basename(p)}: answers の .update() に変数を渡している "
                   f"({arg[:40]}…)。answerPatch() を通すこと")
            elif keys - ALLOWED:
                ng(f"{os.path.basename(p)}: answers の .update() に "
                   f"{sorted(keys - ALLOWED)} が入っている (列 grant に無いので 42501)")

    # --- 9. 選択肢の値を作る場所が 1 つだけか --------------------------------
    # DB の correct_answer は 1 起算の数字文字列。0 起算や 'A'/'①' をどこかで作ると
    # **全員 0 点**になり、それを落とす検査は RPC にもスキーマにも無い。
    defs = []
    for p, s in js.items():
        for m in re.finditer(r"function\s+choiceValue\s*\(", s):
            defs.append(os.path.basename(p))
    if not defs:
        ng("choiceValue() が無い (選択肢の値を作る場所を 1 つに絞ること)")
    elif len(defs) > 1:
        ng(f"choiceValue() が {len(defs)} 箇所にある: {defs}")
    for p, s in js.items():
        lines = s.split("\n")
        for i, line in enumerate(lines):
            if "choice_count" not in line:
                continue
            near = "\n".join(lines[max(0, i - 12):i + 13])
            if "choiceValue(" not in near:
                ng(f"{os.path.basename(p)}:{i + 1} choice_count から値を作っているのに "
                   f"choiceValue() を通していない (0 起算や 'A' を書くと全員 0 点)")

    # --- 10. annotations の書き込みが validateStrokes を通っているか ---------
    for p, s in js.items():
        for m in re.finditer(r"\.from\(\s*['\"]annotations['\"]\s*\)([\s\S]{0,400}?)\.(insert|update)\(", s):
            before = s[max(0, m.start() - 1200):m.start()]
            if "validateStrokes(" not in before:
                line = s[:m.start()].count("\n") + 1
                ng(f"{os.path.basename(p)}:{line} annotations への書き込みが "
                   f"validateStrokes() を通っていない")

    # --- 11. HTML に無い id を JS が掴んでいないか ---------------------------
    # $('#foo') の綴り違いは実行するまで気づけず、しかも「押しても何も起きない」で終わる。
    html = [p for p in files if p.endswith(".html")]
    if html and js:
        have = set()
        for p in html:
            have |= set(re.findall(r"\bid=[\"']([\w-]+)[\"']", srcs[p]))
        for p, s in js.items():
            want = set(re.findall(r"\$\(\s*['\"]#([\w-]+)['\"]\s*\)", s))
            want |= set(re.findall(r"getElementById\(\s*['\"]([\w-]+)['\"]\s*\)", s))
            for miss in sorted(want - have):
                ng(f"{os.path.basename(p)}: #{miss} を掴んでいるが HTML に無い")
        # data-* の静的セレクタも同じ理由で照合する
        attrs = set()
        for p in html:
            attrs |= set(re.findall(r"\b(data-[\w-]+)=[\"']([^\"']*)[\"']", srcs[p]))
        for p, s in js.items():
            for a, v in re.findall(r"querySelector(?:All)?\(\s*['\"]\[(data-[\w-]+)=\\?[\"']([^\"'\]\\]+)", s):
                if (a, v) not in attrs:
                    ng(f"{os.path.basename(p)}: [{a}=\"{v}\"] を掴んでいるが HTML に無い")

    # --- 12. 構文が通るか (node) --------------------------------------------
    node = shutil.which("node")
    if node:
        for p in js:
            r = subprocess.run([node, "--check", p], capture_output=True, text=True, timeout=30)
            if r.returncode:
                ng(f"{os.path.basename(p)}: 構文エラー — "
                   f"{(r.stderr or '').strip().splitlines()[-1][:160] if r.stderr else ''}")
    else:
        ng("node が無いので構文検査を飛ばした")

    return {"files": [os.path.basename(p) for p in files]}


# =============================================================================
# 往復検査 (node → Postgres)
# =============================================================================
PROD_MARKERS = ("railway.app", "rlwy.net", "supabase.com", "supabase.co",
                "amazonaws.com", "neon.tech")


def find_psql():
    dsn = os.environ.get("ENGLISH_SCHEMA_TEST_DSN", "").strip()
    if dsn:
        low = dsn.lower()
        hit = [m for m in PROD_MARKERS if m in low]
        if hit:
            ng(f"ENGLISH_SCHEMA_TEST_DSN が本番らしいホストを指している ({hit[0]})")
            return None, None
        return ("dsn", dsn), "ENGLISH_SCHEMA_TEST_DSN"
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


def psql(conn, dbname, args, timeout=120, stdin=None):
    """★ 大きな SQL は引数でなく **標準入力**で渡す。
    4800 本のストロークを -c に載せると `Argument list too long` で落ちる (実測)。
    一時ファイルは使わない (検査が書き込みを持つと run_all_gates が破壊的と見なす)。"""
    kind, dsn = conn
    if kind == "dsn":
        base = dsn.rsplit("/", 1)[0] + "/" + dbname if dbname else dsn
        return subprocess.run(["psql", "-q", "-v", "ON_ERROR_STOP=1", "-d", base] + args,
                              capture_output=True, text=True, timeout=timeout, input=stdin)
    import shlex
    cmd = "psql -q -v ON_ERROR_STOP=1 " + (f"-d {shlex.quote(dbname)} " if dbname else "")
    cmd += " ".join(shlex.quote(a) for a in args)
    return subprocess.run(["su", "postgres", "-c", cmd],
                          capture_output=True, text=True, timeout=timeout, input=stdin)


def roundtrip(conn):
    node = shutil.which("node")
    if not node:
        ng("node が無いので往復検査を回せない")
        return
    r = subprocess.run([node, ROUNDTRIP], capture_output=True, text=True,
                       cwd=ROOT, timeout=120)
    if r.returncode:
        ng(f"roundtrip_strokes.mjs が落ちた: {(r.stderr or r.stdout).strip()[-300:]}")
        return

    rows = [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
    writes = [x for x in rows if x["kind"] == "write"]
    reads = [x for x in rows if x["kind"] in ("read", "merge")]
    if not writes:
        ng("往復検査の入力が 0 件 (生成側が何も出していない)")
        return

    db = f"bookexam_gate_{os.getpid()}"
    try:
        rr = psql(conn, None, ["-c", f'drop database if exists {db}',
                               "-c", f'create database {db}'])
        if rr.returncode:
            ng(f"検査用 DB を作れない: {(rr.stderr or rr.stdout).strip()[:200]}")
            return
        for path in [STUBS] + sorted(
                os.path.join(MIG_DIR, f) for f in os.listdir(MIG_DIR) if f.endswith(".sql")):
            rr = psql(conn, db, ["-f", path])
            if rr.returncode:
                err = [x for x in (rr.stderr or "").splitlines() if "ERROR" in x]
                ng(f"{os.path.basename(path)} を流せない: {(err[0] if err else rr.stderr)[:200]}")
                return

        # クライアントが送るものを **1 本の SQL にまとめて** DB の判定に通す。
        # ★ payload に $ は現れない (数値・16進の色・英字キーだけ) ので $json$ で括れる。
        sent = [w for w in writes if w["clientOk"]]
        for w in sent:
            if "$json$" in json.dumps(w["payload"]):
                ng(f"payload に $json$ が含まれる ({w['name']}) — 括り方を変えること")
                return
        lines = []
        for i, w in enumerate(sent):
            payload = json.dumps(w["payload"], ensure_ascii=False)
            lines.append(f"select {i} as i, "
                         f"public.strokes_are_valid($json${payload}$json$::jsonb) as ok")
        sql = "\nunion all\n".join(lines) + "\norder by i;\n"

        rr = psql(conn, db, ["-tA", "-F", "|", "-f", "-"], timeout=180, stdin=sql)
        if rr.returncode:
            ng(f"往復検査の SQL が落ちた: {(rr.stderr or '').strip()[:200]}")
            return
        got = {}
        for line in (rr.stdout or "").splitlines():
            if "|" in line:
                a, b = line.split("|", 1)
                got[int(a)] = b.strip()
        rejected = 0
        for i, w in enumerate(sent):
            if got.get(i) != "t":
                rejected += 1
                ng(f"★クライアントが送る JSON を DB が拒否した: 「{w['name']}」 "
                   f"→ {got.get(i, '(結果なし)')}")
        if len(got) != len(sent):
            ng(f"往復検査の結果が {len(got)} 件しか返っていない (送ったのは {len(sent)} 件)")
        print(f"  [live] クライアントが送る {len(sent)} 件すべてを DB が受け取る "
              f"(拒否 {rejected} 件)")

        # 「モデルが弾いたもの」は送られないので DB 判定は問わない。
        # ただし 1 件も弾いていなければモデルが素通しになっている。
        dropped = [w for w in writes if not w["clientOk"] or w["strokeCount"] == 0]
        if len(dropped) < 5:
            ng(f"モデルが弾いた入力が {len(dropped)} 件しかない "
               f"(意地の悪い入力が検査に入っていない疑い)")
        print(f"  [live] モデルが送らずに落とした入力 {len(dropped)} 件")
        print(f"  [live] 読み込み側 {len(reads)} 件")
    except subprocess.TimeoutExpired:
        ng("往復検査がタイムアウトした")
    finally:
        try:
            psql(conn, None, ["-c", f'drop database if exists {db}'])
        except Exception:
            pass


# =============================================================================
def main():
    files = app_files()
    print("=== 冊子受験画面ゲート ===")
    if not os.path.exists(MODEL):
        print("✗ exam-book-model.mjs が無い")
        return 1
    print(f"検査対象 {len(files)} 本:")
    for p in files:
        print(f"  - {os.path.basename(p)}")

    static_checks(files)
    print("  [check] 静的検査 (pdf.js の版 / upsert 禁止 / 返却行数 / CDN 直リンク / 写経 / "
          "no-cache / anon key / answers の列 / choiceValue / validateStrokes / "
          "HTML の id と data-* / 構文)")

    conn, label = find_psql()
    if conn:
        print(f"  [live] {label} に使い捨て DB を作って往復検査")
        roundtrip(conn)
    else:
        print("  [skip] 往復検査は未実行 — Postgres が見つからない。")
        print("         静的検査だけ回した。手元では ENGLISH_SCHEMA_TEST_DSN を指定するか "
              "postgres を起動すること")

    print()
    if problems:
        print(f"=== 問題 (件数 {len(problems)}) ===")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    print("=== ALL PASS (問題 0 件) ===")
    return 0


sys.exit(main())
