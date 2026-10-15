#!/usr/bin/env python3
"""📖🧪 取込の検査スクリプト・取込スクリプト (scripts/drill_import) がサーバと食い違っていないか・単体で動くかの回帰テスト (2026-10-15)。

検査スクリプト (validate_drill_import.py) と取込スクリプト (import_drill_file.py) は、塾長のデスクトップ
(~/Desktop/📝 模試・演習/習熟度テスト/_tools/) に写して単体で動かす (Python 3.9 の標準ライブラリだけ・`python3 -I`・
サーバのデプロイ前でも動く)。そのためサーバの単元表を SERVER_TABLES に写して持っている。

  [1] 写し (SERVER_TABLES) が server/main.py の定数と同じ (main.py は import せず構文木で読む)
  [2] 取込スクリプトが付ける出典の形が、サーバの自動配信の許可リスト (英語長文 el- / englong:) と禁止 (習熟度テスト pt- / ptest:) に合う
  [3] 標準ライブラリだけ・Python 3.9 の文法・`python3 -I` で別のフォルダから動く (自己検査・fixtures の無い _tools の写し・
      __pycache__ を作らない)
  [4] 取込スクリプトの安全装置: 送り先は https (手元の 127.0.0.1 だけ http)・秘密のファイルは 0600 で自分のもの・
      値は画面に出さない・リポジトリの中のファイルは送らない
  [5] 仕様書 (docs/drill-import-spec.md) 11 章のエラー・警告のコードを検査スクリプトが全部持つ

実行:
    python3 scripts/health_check/test_drill_import_parity.py      # exit 0 = PASS / 1 = FAIL
通信しない。書くのは tempfile の一時フォルダだけ。
"""
import ast
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
DI = os.path.join(REPO, "scripts", "drill_import")
VALIDATOR = os.path.join(DI, "validate_drill_import.py")
IMPORTER = os.path.join(DI, "import_drill_file.py")
GATE = os.path.join(DI, "check_no_test_keys_in_repo.py")
SPEC = os.path.join(REPO, "docs", "drill-import-spec.md")
STDLIB_OK = {"argparse", "ast", "datetime", "hashlib", "importlib", "json", "os", "re", "shutil", "stat", "subprocess", "sys",
             "tempfile", "unicodedata", "urllib"}

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load(path, name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def server_constants(names):
    """server/main.py のトップレベルの代入を構文木で読む (リテラル・frozenset({...})・re.compile(r'...') の第 1 引数)。"""
    tree = ast.parse(open(MAIN_PY, encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name not in names:
            continue
        v = node.value
        if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "frozenset":
            out[name] = set(ast.literal_eval(v.args[0]))
        elif isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "compile":
            out[name] = ast.literal_eval(v.args[0])
        else:
            out[name] = ast.literal_eval(v)
    return out


def main():
    print("📖🧪 取込の検査・取込スクリプト (scripts/drill_import) のサーバとの一致・単体での動作 回帰テスト\n")
    V = load(VALIDATOR, "validate_drill_import_parity")
    I = load(IMPORTER, "import_drill_file_parity")

    print("[1] 写し (SERVER_TABLES) = server/main.py")
    names = list(V.SERVER_TABLES) + ["_AUTO_DELIVERY_REVIEWED_SOURCES_DEFAULT", "_AUTO_DELIVERY_DENY_SOURCE_PREFIXES",
                                     "_AUTO_DELIVERY_DENY_SUBJECTS"]
    srv = server_constants(set(names))
    for k, mine in V.SERVER_TABLES.items():
        got = srv.get(k)
        if isinstance(got, set):
            ok = sorted(got) == sorted(mine)
        else:
            ok = got == mine
        if isinstance(got, dict) and isinstance(mine, dict) and not ok:
            detail = {s: {"server": got.get(s), "写し": mine.get(s)} for s in sorted(set(got) | set(mine)) if got.get(s) != mine.get(s)}
        else:
            detail = f"server={got!r} / 写し={mine!r}"
        check(f"{k} が server/main.py と同じ" + (" (並び順も)" if isinstance(mine, (list, dict)) and not isinstance(got, set) else ""),
              ok, f"{detail} → validate_drill_import.py の SERVER_TABLES を直し、デスクトップの _tools/ にも写す")
    check("写しの正規表現でサーバの単元名の例が通る・崩れた形は通らない",
          bool(V.PTEST_UNIT_RE.match("高校英語 習熟度テスト 第1回")) and bool(V.PTEST_UNIT_RE.match("中学数学 習熟度テスト 第12回改2"))
          and not V.PTEST_UNIT_RE.match("高校英文法 習熟度テスト 第1回") and not V.PTEST_UNIT_RE.match("高校英語 習熟度 テスト 第1回"))

    print("\n[2] 出典の形 = 自動配信の許可リスト・禁止")
    allow = srv.get("_AUTO_DELIVERY_REVIEWED_SOURCES_DEFAULT", {})
    deny = tuple(srv.get("_AUTO_DELIVERY_DENY_SOURCE_PREFIXES", ()))

    def allowed(subject, source):
        pats = allow.get(subject, ())
        return any(source.startswith(p[:-1]) if p.endswith("*") else source == p for p in pats)

    el = json.load(open(os.path.join(DI, "fixtures", "ok_english_long.json"), encoding="utf-8"))
    pt = json.load(open(os.path.join(DI, "fixtures", "ok_proficiency_test.json"), encoding="utf-8"))
    pel = I.build_payloads(el, "0" * 64)[0]
    ppt = I.build_payloads(pt, "0" * 64)[0]
    el_src = [p["source"] for p in pel["passages"]] + [q["source"] for p in pel["passages"] for q in p["questions"]]
    check("英語長文: 本文 englong:<set_id>:<pid>・設問 el-<set_id>-<qid> がすべて english_long の許可リストに入る",
          el_src and all(allowed("english_long", s) for s in el_src)
          and all(len(p["source"].split(":")) == 3 for p in pel["passages"]), el_src)
    pt_src = [p["source"] for p in ppt["passages"]] + [q["source"] for p in ppt["passages"] for q in p["questions"]]
    check("習熟度テスト: 本文 ptest:・設問 pt- がすべて自動配信の禁止の接頭辞に当たる・科目も禁止",
          pt_src and all(s.startswith(deny) for s in pt_src) and "proficiency_test" in srv.get("_AUTO_DELIVERY_DENY_SUBJECTS", set()),
          (pt_src, deny))
    check("設問の出典は 30 字以内・本文の出典は 60 字以内 (サーバが切り詰める長さ)",
          all(len(q["source"]) <= 30 for p in pel["passages"] + ppt["passages"] for q in p["questions"])
          and all(len(p["source"]) <= 60 for p in pel["passages"] + ppt["passages"]))
    check("盲検の要約: protocol・3 名・all_agree・test_id / set_id (サーバの _grammar_import_review_problem が見る形)",
          ppt["review"]["protocol"] == srv["_GRAMMAR_REVIEW_PROTOCOL"] and len(ppt["review"]["solvers"]) == 3
          and ppt["review"]["all_agree"] is True and ppt["review"]["test_id"] == "FXHS01" and pel["review"]["set_id"] == "FX001")
    n_q = sum(len(s["questions"]) for s in pt["sections"])
    flat = [q for p in ppt["passages"] for q in p["questions"]]
    filq = [q for s in sorted(pt["sections"], key=lambda s: s["section_no"]) for q in s["questions"]]
    check("習熟度テスト: 大問の順・設問の順のまま 0 始まりに直す (全問 choices[answer] = ファイルの choices[correct_choice_no - 1])",
          len(flat) == n_q and all(a["choices"][a["answer"]] == b["choices"][b["correct_choice_no"] - 1] and a["answer"] == b["correct_choice_no"] - 1
                                   for a, b in zip(flat, filq)))
    bad = json.loads(json.dumps(pt))
    bad["sections"][0]["questions"][0]["correct_choice_no"] += 1    # 解説の 1 行目と合わない = 番号ずれ
    try:
        I.build_payloads(bad, "")
        stopped = False
    except ValueError as e:
        stopped = "変換の後の照合" in str(e)
    check("変換の後の照合: correct_choice_no と解説の 1 行目がずれていたら送る前に止める", stopped)
    nr = json.loads(json.dumps(el))
    nr.pop("_review")
    try:
        I.build_payloads(nr, "")
        stopped = False
    except ValueError:
        stopped = True
    check("盲検の記録が無いファイルは変換しない", stopped)

    print("\n[3] 単体で動く (標準ライブラリだけ・3.9 の文法・python3 -I・別のフォルダ)")
    for path in (VALIDATOR, IMPORTER, GATE):
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        try:
            ast.parse(src, feature_version=(3, 9))
            ok39 = True
        except SyntaxError as e:
            ok39 = str(e)
        check(f"{os.path.basename(path)}: 標準ライブラリだけ {sorted(mods - STDLIB_OK) or ''}・3.9 の文法",
              mods <= STDLIB_OK and ok39 is True, (sorted(mods - STDLIB_OK), ok39))
        check(f"{os.path.basename(path)}: 型注釈を使わない (3.9 で X | Y が評価されて落ちるのを避ける)",
              not any(isinstance(n, ast.AnnAssign) or (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                                                       and (n.returns is not None or any(a.annotation is not None for a in n.args.args)))
                      for n in ast.walk(tree)))
    with tempfile.TemporaryDirectory(prefix="drill-parity-") as tmp:
        cp = subprocess.run([sys.executable, "-I", VALIDATOR], cwd=tmp, capture_output=True, encoding="utf-8")
        check("検査スクリプトの自己検査 (python3 -I・別のフォルダから): exit 0・PASS",
              cp.returncode == 0 and "自己検査 PASS" in cp.stdout, (cp.returncode, (cp.stdout + cp.stderr)[-600:]))
        tools = os.path.join(tmp, "_tools")
        os.makedirs(tools)
        for p in (VALIDATOR, IMPORTER):
            shutil.copy2(p, tools)
        work = os.path.join(tmp, "work")
        shutil.copytree(os.path.join(DI, "fixtures"), work)
        env = {k: v for k, v in os.environ.items() if k not in ("CRON_SECRET", "AI_JUKU_API_BASE")}
        cp = subprocess.run([sys.executable, "-I", os.path.join(tools, "validate_drill_import.py"),
                             os.path.join(work, "ok_english_long.json")], cwd=tmp, capture_output=True, encoding="utf-8", env=env)
        check("_tools の写し (fixtures なし) の検査スクリプトで英語長文を検査: exit 0", cp.returncode == 0 and "エラーなし" in cp.stdout,
              (cp.returncode, cp.stdout[-400:], cp.stderr[-400:]))
        cp = subprocess.run([sys.executable, "-I", os.path.join(tools, "validate_drill_import.py")], cwd=tmp,
                            capture_output=True, encoding="utf-8", env=env)
        check("_tools の写しを引数なしで動かすと使い方を出して exit 2 (自己検査の fixtures が無い)", cp.returncode == 2, cp.returncode)
        cp = subprocess.run([sys.executable, "-I", os.path.join(tools, "import_drill_file.py"),
                             os.path.join(work, "ok_proficiency_test.json"), "--offline"], cwd=tmp, capture_output=True,
                            encoding="utf-8", env=env)
        check("_tools の写しの取込スクリプト --offline: 検査と変換だけで exit 0 (通信しない)",
              cp.returncode == 0 and "送っていません" in cp.stdout and "本文 3 本・設問 7 問" in cp.stdout, (cp.returncode, cp.stdout[-400:]))
        check("_tools に __pycache__ を作らない", sorted(os.listdir(tools)) == ["import_drill_file.py", "validate_drill_import.py"],
              os.listdir(tools))
        cp = subprocess.run([sys.executable, "-I", os.path.join(tools, "validate_drill_import.py"), "--make-blind",
                             os.path.join(work, "_review", "blind_sheet"), os.path.join(work, "ok_english_long.json")],
                            cwd=tmp, capture_output=True, encoding="utf-8", env=env)
        made = sorted(os.listdir(os.path.join(work, "_review", "blind_sheet"))) if cp.returncode == 0 else []
        check("--make-blind <フォルダ>/_review/blind_sheet <ファイル> で 3 ファイル",
              made == ["answer_template.json", "blind_sheet.json", "blind_sheet.md"], (cp.returncode, cp.stderr[-300:], made))

        print("\n[4] 取込スクリプトの安全装置")
        I.HTTP = lambda *a, **k: (_ for _ in ()).throw(AssertionError("通信してはいけない"))
        for base, ok in (("https://ai-juku-api-production.up.railway.app", True), ("http://127.0.0.1:8000", True),
                         ("http://example.org", False), ("ftp://x", False), ("https://", False)):
            os.environ["AI_JUKU_API_BASE"] = base
            try:
                I.api_base()
                got, code = True, 0
            except I.ImportStop as e:
                got, code = False, e.code
            check(f"送り先 {base} → {'可' if ok else '拒否 (exit 2)'}", got is ok and (ok or code == 2), (got, code))
        os.environ.pop("AI_JUKU_API_BASE", None)
        check("送り先の既定は本番の API", I.DEFAULT_BASE == "https://ai-juku-api-production.up.railway.app" and I.api_base() == I.DEFAULT_BASE)
        os.environ.pop("CRON_SECRET", None)
        sec = os.path.join(tmp, "secret")
        I.SECRET_FILE = sec
        with open(sec, "w") as f:
            f.write("fixture-secret-value\n")
        os.chmod(sec, 0o644)
        try:
            I.read_secret()
            refused = False
        except I.ImportStop as e:
            refused = e.code == 2 and "chmod 600" in str(e) and "fixture-secret-value" not in str(e)
        check("秘密のファイルが 0644 (他の人も読める) なら止める・値はメッセージに出さない", refused)
        os.chmod(sec, 0o600)
        check("0600 なら読む (前後の空白・改行を落とす)", I.read_secret() == "fixture-secret-value")
        os.remove(sec)
        try:
            I.read_secret()
            refused = False
        except I.ImportStop as e:
            refused = "chmod 600" in str(e)
        check("秘密のファイルが無ければ置き方を案内して止める", refused)
        os.environ["CRON_SECRET"] = "env-secret"
        check("環境変数 CRON_SECRET があればそれを使う", I.read_secret() == "env-secret")
        os.environ.pop("CRON_SECRET", None)
        buf = io.StringIO()
        rc = I.run([os.path.join(DI, "fixtures", "ok_english_long.json"), "--apply"], out=buf)
        check("リポジトリの中のファイルは送らない (exit 2・通信しない)", rc == 2 and "取り込みません" in buf.getvalue(), buf.getvalue()[-300:])
        sd = os.path.join(tmp, "seed-data")
        os.makedirs(sd)
        shutil.copy2(os.path.join(work, "ok_english_long.json"), sd)
        buf = io.StringIO()
        rc = I.run([os.path.join(sd, "ok_english_long.json")], out=buf)
        check("seed-data の中のファイルは送らない (exit 2)", rc == 2, buf.getvalue()[-300:])
        buf = io.StringIO()
        rc = I.run([os.path.join(work, "bad_figure.json"), "--apply"], out=buf)
        check("検査のエラーがあれば送らない (exit 1)", rc == 1 and "何も送っていません" in buf.getvalue(), buf.getvalue()[-300:])
        d = json.load(open(os.path.join(work, "ok_english_long.json"), encoding="utf-8"))
        d["unit"] = "長文 Lv.2"      # 語数の目安の外 = 警告 (盲検は有効のまま)
        wp = os.path.join(work, "warn_words.json")
        json.dump(d, open(wp, "w", encoding="utf-8"), ensure_ascii=False)
        buf = io.StringIO()
        rc = I.run([wp, "--offline"], out=buf)
        rc2 = I.run([wp, "--offline", "--accept-warnings"], out=io.StringIO())
        check("警告があれば --accept-warnings が無いと止める", rc == 1 and "--accept-warnings" in buf.getvalue() and rc2 == 0, (rc, rc2))

    print("\n[5] 仕様書 11 章のコード")
    spec = open(SPEC, encoding="utf-8").read()
    ch11 = spec.split("## 11.")[1] if "## 11." in spec else ""
    codes = set(re.findall(r"\b([EW]_[A-Z_]+)\b", ch11))
    vsrc = open(VALIDATOR, encoding="utf-8").read()
    have = set(re.findall(r'"([EW]_[A-Z_]+)"', vsrc))
    check(f"仕様書 11 章のコード {len(codes)} 個を検査スクリプトが全部出せる", codes and codes <= have, sorted(codes - have))
    check("仕様書に無いコードは W_QUESTIONS (設問数の目安)・W_SKILL (単元名の無い科目の skill を外す) だけ (README に記載)",
          have - codes == {"W_QUESTIONS", "W_SKILL"}, sorted(have - codes))
    readme = open(os.path.join(DI, "README.md"), encoding="utf-8").read()
    check("README に W_QUESTIONS と W_SKILL の説明", "W_QUESTIONS" in readme and "W_SKILL" in readme)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ PASS (取込の検査・取込スクリプト: サーバの表と一致・出典の形・単体で動く・安全装置・仕様書のコード)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
