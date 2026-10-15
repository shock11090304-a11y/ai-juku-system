#!/usr/bin/env python3
"""🧒 学年の判定を 1 つにそろえた回帰テスト (2026-10-15 塾長「中学生と高校生は問題の配信はミスらないように」)。

背景: 学年は自由入力で、「中２」「中三」「中Ⅲ」のような全角・漢数字が混ざる。以前はサーバの
  `_student_mode_from_grade` も student-mode.js の `ajStudentMode` もこれを中学と読まず、高校生モードで
  表示していた (CEO の取り違えガード `_gdMode` は「判定できない」に倒していた)。自動配信で中学生に高校の
  問題を出さないため、判定の前に数字ゆれを半角へそろえる規則を サーバ・student-mode.js・ceo.html で同じにした。

固定する性質 (一時 SQLite・外部通信なし):
  1. サーバ `_student_mode_from_grade` (3 値・表示用・未知は kosei) が下の表どおり
  2. サーバ `_student_grade_band` (4 値・自動配信用・未知は '') が表どおり。unknown_as_kosei=True なら未知は kosei
     `_student_chugaku_year` は中学の学年 (1〜3) か None
  3. student-mode.js の `ajStudentMode` / `ajNormGrade` と ceo.html の `_gdMode` を JS エンジンで実際に動かし、
     サーバと同じ答えになる (node → osascript → jsc。どれも無いときは置き換え表をソースで突き合わせる)
  4. 数字ゆれの置き換え表 (全角・漢数字・ローマ数字) がサーバと student-mode.js で同じ
  5. student-mode.js を読む画面はすべて同じ ?v= で読む (ai-tutor-photo.html も ?v= 付き)。ceo.html の _gdMode は ajNormGrade を通す

実行:
    python3 scripts/health_check/test_grade_band_consistency.py
    # exit 0 = PASS / 1 = FAIL
"""
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
STUDENT_MODE_JS = os.path.join(REPO, "student-mode.js")
CEO_HTML = os.path.join(REPO, "ceo.html")
PAGES = ("mypage.html", "ceo.html", "dojo-drill.html", "mock-exam.html", "ai-tutor-photo.html")
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc"
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []

# (学年の文字列, 3 値の mode, 4 値の band, unknown_as_kosei の band, 中学の学年)
TABLE = [
    ("中1", "chugaku", "chugaku", "chugaku", 1),
    ("中２", "chugaku", "chugaku", "chugaku", 2),
    ("中三", "chugaku", "chugaku", "chugaku", 3),
    ("中Ⅲ", "chugaku", "chugaku", "chugaku", 3),
    ("中ⅱ", "chugaku", "chugaku", "chugaku", 2),
    ("中学3年", "chugaku", "chugaku", "chugaku", 3),
    ("中学２年生", "chugaku", "chugaku", "chugaku", 2),
    ("中学一年", "chugaku", "chugaku", "chugaku", 1),
    ("中学３年", "chugaku", "chugaku", "chugaku", 3),
    ("  中２ ", "chugaku", "chugaku", "chugaku", 2),
    ("中学生", "chugaku", "chugaku", "chugaku", None),
    ("中高一貫 中3", "chugaku", "chugaku", "chugaku", 3),
    ("中学受験", "shougaku", "shougaku", "shougaku", None),
    ("中受", "shougaku", "shougaku", "shougaku", None),
    ("小６", "shougaku", "shougaku", "shougaku", None),
    ("小学5年", "shougaku", "shougaku", "shougaku", None),
    ("小学五年生", "shougaku", "shougaku", "shougaku", None),
    ("高１", "kosei", "kosei", "kosei", None),
    ("高二", "kosei", "kosei", "kosei", None),
    ("高3", "kosei", "kosei", "kosei", None),
    ("高校2年", "kosei", "kosei", "kosei", None),
    ("高校三年", "kosei", "kosei", "kosei", None),
    ("既卒", "kosei", "kosei", "kosei", None),
    ("浪人", "kosei", "kosei", "kosei", None),
    ("既卒・浪人", "kosei", "kosei", "kosei", None),
    ("中高一貫 高2", "kosei", "kosei", "kosei", None),   # 「中高1貫」の 中 の後ろは数字でない
    ("大学1年", "kosei", "kosei", "kosei", None),
    ("その他", "kosei", "", "kosei", None),
    ("社会人", "kosei", "", "kosei", None),
    ("", "kosei", "", "kosei", None),
    (None, "kosei", "", "kosei", None),
]


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="grade_band_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_grade_band", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def server_numeral_pairs():
    """server/main.py の _normalize_grade_numerals の置き換え表 (2 文字のタプルの並び) を AST で読む。"""
    tree = ast.parse(read(MAIN_PY))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_normalize_grade_numerals":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Tuple) and sub.elts and all(
                        isinstance(e, ast.Tuple) and len(e.elts) == 2 for e in sub.elts):
                    try:
                        return [tuple(ast.literal_eval(e)) for e in sub.elts]
                    except ValueError:
                        return []
    return []


def js_numeral_map(src):
    """student-mode.js の GRADE_NUM_MAP (置き換え表) を読む。読めなければ {}。"""
    m = re.search(r"var\s+GRADE_NUM_MAP\s*=\s*\{(.*?)\};", src, re.S)
    if not m:
        return {}
    return {a: b for a, b in re.findall(r"'([^'])'\s*:\s*'([^'])'", m.group(1))}


def js_function(src, name):
    """src から `function name(...) { ... }` を波かっこの対応で切り出す (文字列・コメントの中のかっこは数えない簡易版)。"""
    i = src.find(f"function {name}(")
    if i < 0:
        return ""
    j = src.index("{", i)
    depth, k, quote = 0, j, None
    while k < len(src):
        ch = src[k]
        if quote:
            if ch == "\\":
                k += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif src.startswith("//", k):
            k = src.index("\n", k)
            continue
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[i:k + 1]
        k += 1
    return ""


def js_engine():
    want = os.environ.get("AJ_JS_ENGINE", "").strip()
    cands = {
        "node": ["node"] if shutil.which("node") else None,
        "osascript": ["osascript", "-l", "JavaScript"] if shutil.which("osascript") else None,
        "jsc": [JSC] if os.path.exists(JSC) else None,
    }
    if want:
        return cands.get(want)
    for k in ("node", "osascript", "jsc"):
        if cands[k]:
            return cands[k]
    return None


JS_PROGRAM = r"""
var window = (typeof globalThis !== 'undefined') ? globalThis : this;
var __res = { mode: [], norm: [], gd: [], hasNorm: false, hasGd: false };
(function () {
%(student_mode)s
})();
%(gd_mode)s
__res.hasNorm = (typeof window.ajNormGrade === 'function');
__res.hasGd = (typeof _gdMode === 'function');
var __inputs = %(inputs)s;
for (var i = 0; i < __inputs.length; i++) {
  var g = __inputs[i];
  __res.mode.push(window.ajStudentMode(g));
  __res.norm.push(__res.hasNorm ? window.ajNormGrade(g) : null);
  __res.gd.push(__res.hasGd ? _gdMode(g) : null);
}
var __s = 'RESULT ' + JSON.stringify(__res);
if (typeof process !== 'undefined' && typeof console !== 'undefined' && console.log) console.log(__s);
else if (typeof print === 'function') print(__s);
else if (typeof console !== 'undefined' && console.log) console.log(__s);
"""


def run_js(engine, program):
    with tempfile.TemporaryDirectory(prefix="grade_band_js_") as td:
        path = os.path.join(td, "case.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(program)
        r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=120)
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    for line in text.split("\n"):
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):]), ""
    return None, f"exit {r.returncode}: {text[-1500:]}"


def main():
    mod = load_main()

    print("\n[1] サーバ _student_mode_from_grade (3 値・表示用)")
    for g, mode, band, band_k, year in TABLE:
        got = mod._student_mode_from_grade(g)
        check(f"mode({g!r}) == {mode}", got == mode, got)

    print("\n[2] サーバ _student_grade_band (4 値・自動配信用) / _student_chugaku_year")
    for g, mode, band, band_k, year in TABLE:
        got = mod._student_grade_band(g)
        check(f"band({g!r}) == {band!r}", got == band, got)
        got_k = mod._student_grade_band(g, unknown_as_kosei=True)
        check(f"band({g!r}, unknown_as_kosei=True) == {band_k!r}", got_k == band_k, got_k)
        got_y = mod._student_chugaku_year(g)
        check(f"chugaku_year({g!r}) == {year!r}", got_y == year, got_y)
    check("band の値は 4 種類だけ", {mod._student_grade_band(t[0]) for t in TABLE} <= {"shougaku", "chugaku", "kosei", ""})
    check("_GRADE_KNOWN_RE は ceo.html _gdMode と同じ正規表現",
          mod._GRADE_KNOWN_RE in read(CEO_HTML), mod._GRADE_KNOWN_RE)

    print("\n[3] 置き換え表 (全角・漢数字・ローマ数字) がサーバと student-mode.js で同じ")
    sm_src = read(STUDENT_MODE_JS)
    srv_pairs = server_numeral_pairs()
    js_map = js_numeral_map(sm_src)
    check("サーバの置き換え表を読めた", len(srv_pairs) >= 18, srv_pairs)
    check("student-mode.js の GRADE_NUM_MAP を読めた", len(js_map) >= 18, js_map)
    check("置き換え表が一致 (サーバ == student-mode.js)", dict(srv_pairs) == js_map,
          {"server_only": sorted(set(dict(srv_pairs).items()) - set(js_map.items())),
           "js_only": sorted(set(js_map.items()) - set(dict(srv_pairs).items()))})
    check("ajStudentMode は判定の前に ajNormGrade を通す",
          re.search(r"function ajStudentMode\([^)]*\)\s*\{[^}]*ajNormGrade\(", sm_src) is not None)
    check("window.ajNormGrade を公開している", "window.ajNormGrade = ajNormGrade" in sm_src)

    print("\n[4] student-mode.js / ceo.html _gdMode を JS で実行してサーバと突き合わせる")
    ceo = read(CEO_HTML)
    gd_src = js_function(ceo, "_gdMode")
    check("ceo.html の _gdMode を切り出せた", bool(gd_src))
    check("ceo.html の _gdMode は ajNormGrade を通す", "ajNormGrade" in gd_src, gd_src[:300])
    inputs = [t[0] for t in TABLE] + [a for a, _ in srv_pairs]
    eng = js_engine()
    print(f"  JS エンジン: {eng[0] if eng else 'なし (置き換え表の突き合わせ [3] だけで判定)'}")
    if eng:
        prog = JS_PROGRAM % {"student_mode": sm_src, "gd_mode": gd_src,
                             "inputs": json.dumps(inputs, ensure_ascii=False)}
        res, err = run_js(eng, prog)
        check("JS が最後まで走った", res is not None, err)
        if res:
            check("JS: window.ajNormGrade がある", res["hasNorm"])
            check("JS: _gdMode を読めた", res["hasGd"])
            for i, (g, mode, band, band_k, year) in enumerate(TABLE):
                check(f"JS ajStudentMode({g!r}) == サーバ ({mode})", res["mode"][i] == mode, res["mode"][i])
                check(f"JS ceo _gdMode({g!r}) == サーバ band ({band!r})", res["gd"][i] == band, res["gd"][i])
            for k, (a, b) in enumerate(srv_pairs):
                got = res["norm"][len(TABLE) + k]
                check(f"JS ajNormGrade({a!r}) == {b!r} (サーバ {mod._normalize_grade_numerals(a)!r})",
                      got == b == mod._normalize_grade_numerals(a), got)

    print("\n[5] student-mode.js の ?v= (Vercel は JS をキャッシュする)")
    vs = {}
    for page in PAGES:
        html = read(os.path.join(REPO, page))
        tags = re.findall(r'<script[^>]+src="student-mode\.js(\?v=[^"]*)?"', html)
        check(f"{page} は student-mode.js を 1 回だけ読む", len(tags) == 1, tags)
        if tags:
            check(f"{page} の student-mode.js に ?v= がある", bool(tags[0]), tags)
            vs[page] = tags[0]
    check("student-mode.js の ?v= は全画面で同じ値", len(set(vs.values())) == 1, vs)
    check("?v= は 2026-10-16 以降の値 (正規化を入れた版)",
          all(re.match(r"\?v=(\d{8})", v) and re.match(r"\?v=(\d{8})", v).group(1) >= "20261016" for v in vs.values()), vs)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ PASS (学年の判定はサーバ・student-mode.js・ceo.html で一致)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
