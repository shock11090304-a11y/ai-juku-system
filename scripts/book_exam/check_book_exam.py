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
# ★ 受験アプリは exam-app/ に分離した (専用 Vercel プロジェクト。2026-08-15 §20)
APP = os.path.join(ROOT, "exam-app")
MODEL = os.path.join(APP, "exam-book-model.mjs")
ROUNDTRIP = os.path.join(ROOT, "scripts", "book_exam", "roundtrip_strokes.mjs")
ROUNDTRIP_Q = os.path.join(ROOT, "scripts", "book_exam", "roundtrip_questions.mjs")
ADMIN_MODEL = os.path.join(APP, "exam-book-admin-model.mjs")
CONVERTER = os.path.join(ROOT, "scripts", "book_exam", "convert_workbook.py")
KYOTSU = os.path.join(ROOT, "scripts", "book_exam", "convert_kyotsu_yaml.py")
MIG_DIR = os.path.join(ROOT, "supabase", "migrations")
STUBS = os.path.join(ROOT, "supabase", "tests", "00_local_stubs.sql")
VENDOR = os.path.join(APP, "vendor", "pdfjs")

problems = []


def ng(msg):
    problems.append(msg)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def app_files():
    """配信する exam-book* を全部。存在するものだけ返す。"""
    out = []
    for f in sorted(os.listdir(APP)):
        if re.match(r"^exam-book.*\.(mjs|html|css)$", f):
            out.append(os.path.join(APP, f))
    return out


def vercel_sources(conf_text):
    """vercel.json の rewrites / redirects / headers の source を全部集める。"""
    try:
        conf = json.loads(conf_text)
    except Exception:
        ng("vercel.json が JSON として読めない")
        return []
    out = []
    for key in ("rewrites", "redirects", "headers", "routes"):
        for row in conf.get(key) or []:
            if isinstance(row, dict) and isinstance(row.get("source"), str):
                out.append(row["source"])
    return out


def bad_group(src):
    """path-to-regexp が受け付けない括弧があれば (位置, 理由) を返す。無ければ None。

    ★ 想像で書かない。path-to-regexp 6.2.1 に実際に食わせて、次の 2 つだけが
      弾かれることを確かめてある (2026-08-14):
        ・グループの中の捕捉グループ  … "Capturing groups are not allowed"
            例 /(exam-book.*\\.(mjs|css))   ← これで本番デプロイを落とした
        ・一番外側で `(?` から始まるもの … 'Pattern cannot start with "?"'
            例 /a(?:b|c)
      逆に **中の** `(?:…)` は通る (例 /a((?:b|c)) は OK)。
    """
    depth = 0
    i = 0
    while i < len(src):
        c = src[i]
        if c == "\\":
            i += 2
            continue
        if c == "(":
            noncapturing = src[i + 1:i + 3] == "?:"
            if depth == 0 and src[i + 1:i + 2] == "?" and not noncapturing:
                return i, 'グループが "?" で始まっている'
            if depth == 0 and noncapturing:
                return i, '一番外側のグループを "(?:" で始めている'
            if depth > 0 and not noncapturing:
                return i, "グループの中で括弧を入れ子にしている"
            depth += 1
        elif c == ")" and depth > 0:
            depth -= 1
        i += 1
    return None


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
    vj = os.path.join(APP, "vercel.json")
    if js and os.path.exists(vj):
        conf = read(vj)
        if "exam-book" not in conf:
            ng("vercel.json に exam-book* の no-cache 指定が無い "
               "(古いモデルを掴んだ端末が古い形式で書き続ける)")

        # ★ Vercel の source は **正規表現ではなく path-to-regexp**。入れ子の括弧を書くと
        #   "Invalid route source pattern" で **デプロイが丸ごと失敗する** (2026-08-14 に実際に
        #   `/(exam-book.*\.(mjs|css))` で本番ビルドを落とした)。JSON としては正しいので
        #   構文検査では気づけない。ここで全ルートを見る。
        for src in vercel_sources(conf):
            hit = bad_group(src)
            if hit is not None:
                pos, why = hit
                ng(f"vercel.json の source \"{src}\" — {pos} 文字目で{why}。"
                   f"path-to-regexp が受け付けず **デプロイが丸ごと失敗する** "
                   f"(分けて 2 本書くこと)")

    # --- 7. anon 以外のキーを貼れないようにしているか ------------------------
    # ★ 「service_role という文字列があるか」を見ない。それだと注意書きに反応して
    #   赤くなり、注意書きを消す方向に圧力がかかる。**実際に貼られている値**を見る。
    cfg = os.path.join(APP, "exam-book-config.mjs")
    if os.path.exists(cfg):
        s = read(cfg)
        if "assertAnonKey" not in s:
            ng("exam-book-config.mjs に assertAnonKey() が無い "
               "(service_role を貼ると RLS が全部素通りする)")
        # ★ 顧客 (CUSTOMERS) が複数になったので **全部の鍵** を見る。
        #   1 件目だけ見ていると「2 社目に secret を貼る」事故を素通しする。
        #   コメント行は落とす (記入例に反応しないため。import_books と同じ扱い)。
        body = re.sub(r"^\s*//.*$", "", s, flags=re.M)
        keys = []
        for m in re.finditer(r"anonKey\s*:\s*((?:['\"][^'\"]*['\"]\s*\+?\s*)+)", body):
            keys.append("".join(re.findall(r"['\"]([^'\"]*)['\"]", m.group(1))))
        if not keys:
            ng("exam-book-config.mjs に anonKey が 1 つも無い")
        for i, key in enumerate(keys, 1):
            if key.startswith("sb_secret_"):
                ng(f"exam-book-config.mjs の {i} 件目に secret キーが貼られている")
            parts = key.split(".")
            if len(parts) == 3:
                import base64
                try:
                    pad = parts[1] + "=" * (-len(parts[1]) % 4)
                    claims = json.loads(base64.urlsafe_b64decode(pad))
                    if claims.get("role") not in (None, "anon"):
                        ng(f"exam-book-config.mjs の {i} 件目の anonKey の role が "
                           f"\"{claims.get('role')}\" になっている")
                except Exception:
                    pass
        # 接続先は必ず https (顧客のドメインを http で書くと全通信が平文になる)
        for m in re.finditer(r"url\s*:\s*'([^']+)'", body):
            if not m.group(1).startswith("https://"):
                ng(f"exam-book-config.mjs の url が https でない ({m.group(1)})")

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
    # ★ この規則は「選択肢を **描く** ファイル」だけに掛ける。生徒がタップした値が
    #   answers.user_answer に入るのはそこだけだから。
    #   先生用の登録画面も choice_count を扱うが、あちらは値を **作らず検証する** 側で、
    #   同じ規則を当てると誤検出になる (下の 9b で別に守る)。
    #   判定はファイル名ではなく **挙動** で行う (名前で除外すると、名前を変えただけで穴が開く)。
    for p, s in js.items():
        renders_choices = ("data-value" in s) or ("aria-checked" in s)
        if not renders_choices:
            continue
        lines = s.split("\n")
        for i, line in enumerate(lines):
            if "choice_count" not in line:
                continue
            near = "\n".join(lines[max(0, i - 12):i + 13])
            if "choiceValue(" not in near:
                ng(f"{os.path.basename(p)}:{i + 1} choice_count から値を作っているのに "
                   f"choiceValue() を通していない (0 起算や 'A' を書くと全員 0 点)")

    # --- 9b. questions への書き込みが validateQuestions を通っているか -------
    # ★ correct_answer を 0 起算や 'A' で入れると **その冊子を解いた生徒が全員 0 点**になる。
    #   採点 RPC は突き合わせるだけ、DB の CHECK も「1 起算か」までは判断できないので、
    #   入力の時点で弾くしかない。annotations ← validateStrokes と同じ形の守り方。
    for p, s in js.items():
        for m in re.finditer(r"\.from\(\s*['\"]questions['\"]\s*\)([\s\S]{0,400}?)\.(insert|update)\(", s):
            before = s[max(0, m.start() - 1500):m.start()]
            if "validateQuestions(" not in before:
                line = s[:m.start()].count("\n") + 1
                ng(f"{os.path.basename(p)}:{line} questions への書き込みが "
                   f"validateQuestions() を通っていない (0 起算の正解が入ると全員 0 点)")

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

    # --- 11b. 紙教材の変換が壊れていないか -----------------------------------
    # ★ 変換器は自分でアプリと同じ検証器を通し、通らなければ 1 で終わる。
    #   ここで回すのは「変換器自体が落ちる / 変換結果が検証を通らない」を
    #   コミット前に捕まえるため。--out を付けないので何も書かない。
    if os.path.exists(CONVERTER):
        r = subprocess.run([sys.executable, CONVERTER], capture_output=True,
                           text=True, cwd=ROOT, timeout=180)
        if r.returncode:
            tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-6:]
            ng("紙教材の変換が通らない: " + " / ".join(tail))
        else:
            m = re.search(r"変換できた: (\d+) 冊 / (\d+) 問", r.stdout)
            if m:
                print(f"  [check] 紙教材の変換 {m.group(1)} 冊 / {m.group(2)} 問 "
                      f"(アプリと同じ検証器を通過)")
            else:
                ng("紙教材の変換の出力が読めない (件数を印字していない)")

    # --- 11c. 共通テスト 9 科目の変換器 ---------------------------------------
    # ★ 元データ (~/Desktop/問題生成/) はこの作業環境から読めないので、
    #   見本 (fixtures_kyotsu/*.yaml) で「3 通りのアダプタが動くか」だけ見る。
    #   実物が変換できることの証明ではない。--probe で構造を確かめること。
    if os.path.exists(KYOTSU):
        r = subprocess.run([sys.executable, KYOTSU, "--selftest"], capture_output=True,
                           text=True, cwd=ROOT, timeout=120)
        if r.returncode:
            tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-6:]
            ng("共通テスト変換の自己検査が通らない: " + " / ".join(tail))
        else:
            print("  [check] " + (r.stdout.strip().splitlines() or ["ok"])[-1].lstrip("[ok] "))

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

        # --- 設問の往復 (先生用の登録画面) ---------------------------------
        # 「画面が通すもの ⊆ DB が受け取るもの」。崩れると「登録できたのに保存で
        # 弾かれる」か、もっと悪い「保存できたのに全員 0 点」になる。
        if os.path.exists(ROUNDTRIP_Q) and os.path.exists(ADMIN_MODEL):
            roundtrip_questions(conn, db)
    except subprocess.TimeoutExpired:
        ng("往復検査がタイムアウトした")
    finally:
        try:
            psql(conn, None, ["-c", f'drop database if exists {db}'])
        except Exception:
            pass


def roundtrip_questions(conn, db):
    """登録画面が通した設問が、DB の question_answer_is_valid() も通ることを見る。"""
    node = shutil.which("node")
    r = subprocess.run([node, ROUNDTRIP_Q], capture_output=True, text=True,
                       cwd=ROOT, timeout=60)
    if r.returncode:
        ng(f"roundtrip_questions.mjs が落ちた: {(r.stderr or r.stdout).strip()[-300:]}")
        return
    rows = [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
    passed = [x for x in rows if x["accepted"] and x.get("payload")]
    dropped = [x for x in rows if not x["accepted"]]
    if not passed:
        ng("設問の往復検査で 1 件も通っていない (検証が厳しすぎる)")
        return
    if len(dropped) < 15:
        ng(f"設問の検証が弾いた入力が {len(dropped)} 件しかない "
           f"(0 起算・全角数字・範囲外などが検査に入っていない疑い)")

    lines = []
    for i, x in enumerate(passed):
        pl = x["payload"]
        cc = "null" if pl["choice_count"] is None else str(int(pl["choice_count"]))
        ca = json.dumps(pl["correct_answer"], ensure_ascii=False)
        if "$q$" in ca or "$q$" in pl["answer_type"]:
            ng(f"payload に $q$ が含まれる ({x['name']})")
            return
        lines.append(
            f"select {i} as i, public.question_answer_is_valid("
            f"$q${pl['answer_type']}$q$, {cc}, $q${pl['correct_answer']}$q$) as ok")
    sql = "\nunion all\n".join(lines) + "\norder by i;\n"

    rr = psql(conn, db, ["-tA", "-F", "|", "-f", "-"], timeout=60, stdin=sql)
    if rr.returncode:
        ng(f"設問の往復検査の SQL が落ちた: {(rr.stderr or '').strip()[:200]}")
        return
    got = {}
    for line in (rr.stdout or "").splitlines():
        if "|" in line:
            a, b = line.split("|", 1)
            got[int(a)] = b.strip()
    rejected = 0
    for i, x in enumerate(passed):
        if got.get(i) != "t":
            rejected += 1
            ng(f"★登録画面が通した設問を DB が拒否した: 「{x['name']}」 "
               f"→ {got.get(i, '(結果なし)')}")
    if len(got) != len(passed):
        ng(f"設問の往復検査の結果が {len(got)} 件しか返っていない (送ったのは {len(passed)} 件)")
    print(f"  [live] 登録画面が通す設問 {len(passed)} 件すべてを DB が受け取る "
          f"(拒否 {rejected} 件)")
    print(f"  [live] 登録画面が弾いた入力 {len(dropped)} 件 "
          f"(0 起算・全角数字・範囲外・重複ほか)")


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
