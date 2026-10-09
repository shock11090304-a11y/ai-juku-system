#!/usr/bin/env python3
"""📺 スタサプ講座カタログ (server/main.py のコード定数) の検査ゲート (2026-10-10 スタサプ段階 A)。

server/main.py を **import せず ast で読む** (標準ライブラリだけ・DB に触れない)。引数なし = 全部を検査する。

検査すること:
  1. SAPURI_COURSES: code が一意 / first ≤ last / total_lessons ≥ last-first+1 (番号の無い補講で 1 多い講座がある) /
     共通テスト対策は first=last=total=0 / level・band・subject が語彙内 / has_lessons の講座は講数が公開 /
     講師名の気配が無い (「講師」「先生」の語・「24講 (◯)」のような講数の後ろのかっこ書き) / notes に「題名」が無い (D1)
  2. SAPURI_COVERS (と文化史・史料の TIER1_ONLY): code が実在 / 科目キーが SAPURI_SUBJECT_KEYS / タグが語彙内 /
     共通テスト・中学総復習・総合問題編 (_2) を入れていない / 各科目キーに 高3 と 高1・2 の講座がある (全学年は両方)
  3. SAPURI_TAG_VOCAB / SAPURI_TAG_ALIASES / _UNIT_TAG_ALIASES / SAPURI_MATH_TAG_FIELD の整合
  4. _SAPURI_COURSE_LABELS_DECLARED == _COURSE_CLASSES[_SAPURI_COURSE_NAME] (順不同・3 件)
  5. SAPURI_LEGACY_NAME_TO_CODE の code が実在 / app.js の SAPURI_LEGACY_CAPS がその写しと一致・
     TEXTBOOK_TOTAL_UNITS に旧名の鍵を二重に持たない
  6. 旧初期データ (SAPURI_LECTURES_SEED) の参照が残っていない・起動時に sapuri_lectures へ投入しない・
     sapuri_lectures 表を SELECT/INSERT する箇所が無い
  7. 講の題名の置き場にしない: リポジトリに high_category*.tsv / sapuri_lessons_*.json / sapuri_import/ が無い

実行: python3 scripts/sapuri_lessons/check_sapuri_catalog.py   # exit 0 = 合格 / 1 = 違反あり
"""
import ast
import os
import re
import subprocess
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
APP_JS = os.path.join(REPO, "app.js")

LEVELS = {"ベーシック", "スタンダード", "ハイ", "トップ", "トップ&ハイ", "ハイ&スタンダード", "共通テスト", "—"}
BANDS = {"高3", "高1・2", "全学年"}
SUBJECTS = {"英語", "数学", "国語", "物理", "化学", "生物", "地学", "日本史", "世界史", "地理", "政経", "倫理", "公共",
            "情報", "小論文"}
KEYS = {"code", "name", "subject", "field", "level", "band", "first", "last", "total_lessons", "dev_min", "dev_max",
        "weeks", "has_lessons", "notes"}

problems = []


def bad(msg):
    problems.append(msg)
    print(f"  ❌ {msg}")


def good(msg):
    print(f"  ✅ {msg}")


def load_consts():
    src = open(MAIN_PY, encoding="utf-8").read()
    tree = ast.parse(src)
    want = {"SAPURI_COURSES", "SAPURI_SUBJECT_KEYS", "SAPURI_TAG_VOCAB", "SAPURI_TAG_ALIASES", "SAPURI_MATH_TAG_FIELD",
            "SAPURI_COVERS", "SAPURI_COVERS_TIER1_ONLY", "SAPURI_LEGACY_NAME_TO_CODE", "_SAPURI_COURSE_NAME",
            "_SAPURI_COURSE_LABELS_DECLARED", "_COURSE_CLASSES", "_UNIT_TAG_ALIASES"}
    out = {}
    for node in tree.body:   # module 直下の代入だけ (関数内のローカルは読まない)
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in want:
                if name in out:
                    bad(f"{name} が module 直下で 2 回代入されている (片方だけ直す事故の元)")
                try:
                    out[name] = ast.literal_eval(node.value)
                except Exception as e:
                    bad(f"{name} がリテラルとして読めない ({type(e).__name__})")
    for name in sorted(want - set(out)):
        bad(f"{name} が server/main.py の module 直下に無い")
    return src, tree, out


def norm(s):
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = re.sub(r"[〈《<]", "<", s)
    s = re.sub(r"[〉》>]", ">", s)
    return re.sub(r"\s+", "", s)


def main():
    print("📺 スタサプ講座カタログ ゲート (server/main.py を ast で検査)\n")
    src, tree, K = load_consts()
    courses = K.get("SAPURI_COURSES") or []
    by_code = {}

    print("[1] SAPURI_COURSES")
    n0 = len(problems)
    for c in courses:
        code = c.get("code")
        if set(c) != KEYS:
            bad(f"{code}: 項目が違う ({sorted(set(c) ^ KEYS)})")
            continue
        if code in by_code:
            bad(f"{code}: code が重複")
        by_code[code] = c
        first, last, total = c["first"], c["last"], c["total_lessons"]
        if c["level"] == "共通テスト":
            if (first, last, total) != (0, 0, 0) or c["has_lessons"]:
                bad(f"{code}: 共通テスト対策は講数非公開 (first=last=total=0・has_lessons=False) のはず")
        else:
            if not (1 <= first <= last):
                bad(f"{code}: first ≤ last でない ({first}..{last})")
            if total < last - first + 1 or total > last - first + 2:
                bad(f"{code}: total_lessons={total} が範囲 {first}..{last} と合わない (補講 1 本まで)")
        if c["level"] not in LEVELS:
            bad(f"{code}: level {c['level']!r} が語彙外")
        if c["band"] not in BANDS:
            bad(f"{code}: band {c['band']!r} が語彙外")
        if c["subject"] not in SUBJECTS:
            bad(f"{code}: subject {c['subject']!r} が語彙外")
        if not (isinstance(c["dev_min"], int) and isinstance(c["dev_max"], int) and c["dev_min"] < c["dev_max"]):
            bad(f"{code}: dev_min < dev_max でない")
        for k in ("name", "field", "notes"):
            v = str(c[k])
            if "講師" in v or "先生" in v:
                bad(f"{code}: {k} に講師名の気配 (講師/先生)")
            # 公開ラインナップは講数の後ろに講師の姓を「24講（◯◯）」と書く。写していないか (漢字 1〜4 字だけのかっこ)
            if re.search(r"\d+\s*講\s*[（(]\s*[一-龥々]{1,4}\s*[)）]", v):
                bad(f"{code}: {k} の講数の後ろに姓のようなかっこ書き (講師名を写していないか)")
        if "題名" in str(c["notes"]):
            bad(f"{code}: notes に講の題名の話が書かれている (D1: 題名は本番 DB だけ)")
    if len(problems) == n0 and courses:
        good(f"{len(courses)} 講座: code 一意・講番号の範囲・語彙・講師名なし")

    print("\n[2] SAPURI_COVERS")
    skeys = tuple(K.get("SAPURI_SUBJECT_KEYS") or ())
    vocab = K.get("SAPURI_TAG_VOCAB") or {}
    covers = K.get("SAPURI_COVERS") or {}
    tier1 = K.get("SAPURI_COVERS_TIER1_ONLY") or {}
    n0 = len(problems)
    for label, table in (("SAPURI_COVERS", covers), ("SAPURI_COVERS_TIER1_ONLY", tier1)):
        for code, m in table.items():
            c = by_code.get(code)
            if not c:
                bad(f"{label}: {code} が SAPURI_COURSES に無い")
                continue
            if c["total_lessons"] <= 0 or c["field"] in ("共通テスト", "中学総復習") or code.endswith("_2"):
                bad(f"{label}: {code} ({c['field']}) は講座選びの母集団に入れない (共通テスト/中学総復習/総合問題編)")
            for sk, tags in m.items():
                if sk not in skeys:
                    bad(f"{label}: {code} の科目キー {sk} が SAPURI_SUBJECT_KEYS に無い")
                    continue
                if tags != "*" and (not isinstance(tags, list) or not tags or not set(tags) <= set(vocab.get(sk, []))):
                    bad(f"{label}: {code} の {sk} のタグが語彙外 ({tags})")
    for code in set(covers) & set(tier1):
        bad(f"{code} が SAPURI_COVERS と TIER1_ONLY の両方にある")
    for sk in skeys:
        bands = {by_code[code]["band"] for code, m in covers.items() if sk in m and code in by_code}
        if not (bands & {"高3", "全学年"}):
            bad(f"科目キー {sk} に 高3 (または全学年) の講座が無い")
        if not (bands & {"高1・2", "全学年"}):
            bad(f"科目キー {sk} に 高1・2 (または全学年) の講座が無い")
    if len(problems) == n0:
        good(f"{len(covers)} 講座 (+ 文化史・史料 {len(tier1)}): 実在・語彙内・{len(skeys)} 科目キーとも 高3 / 高1・2 の講座あり")

    print("\n[3] タグの語彙と別名")
    n0 = len(problems)
    if set(vocab) != set(skeys):
        bad(f"SAPURI_TAG_VOCAB の科目キーが SAPURI_SUBJECT_KEYS と違う ({sorted(set(vocab) ^ set(skeys))})")
    for sk, tags in vocab.items():
        if len(tags) != len(set(tags)):
            bad(f"SAPURI_TAG_VOCAB[{sk}] にタグの重複")
    for sk, amap in (K.get("SAPURI_TAG_ALIASES") or {}).items():
        if sk not in vocab:
            bad(f"SAPURI_TAG_ALIASES の科目キー {sk} が語彙に無い")
            continue
        for a, vals in amap.items():
            if a in vocab[sk]:
                bad(f"SAPURI_TAG_ALIASES[{sk}] の別名 {a} が語彙そのもの (別名にしない)")
            if not vals or not set(vals) <= set(vocab[sk]):
                bad(f"SAPURI_TAG_ALIASES[{sk}][{a}] の値 {vals} が語彙外")
    for a, v in (K.get("_UNIT_TAG_ALIASES") or {}).items():
        if v not in vocab.get("eng_grammar", []):
            bad(f"_UNIT_TAG_ALIASES[{a}] = {v} が英文法の語彙に無い")
    mt = K.get("SAPURI_MATH_TAG_FIELD") or {}
    if set(mt) != set(vocab.get("math", [])):
        bad(f"SAPURI_MATH_TAG_FIELD のタグが数学の語彙と違う ({sorted(set(mt) ^ set(vocab.get('math', [])))})")
    if len(problems) == n0:
        good("語彙・別名 (SAPURI_TAG_ALIASES / _UNIT_TAG_ALIASES)・数学のタグ → 科目の表が整合")

    print("\n[4] 対象クラス (D2)")
    n0 = len(problems)
    declared = tuple(K.get("_SAPURI_COURSE_LABELS_DECLARED") or ())
    runtime = (K.get("_COURSE_CLASSES") or {}).get(K.get("_SAPURI_COURSE_NAME"))
    if len(declared) != 3 or runtime is None or sorted(declared) != sorted(runtime):
        bad(f"_SAPURI_COURSE_LABELS_DECLARED {declared} が _COURSE_CLASSES[{K.get('_SAPURI_COURSE_NAME')!r}] {runtime} と違う")
    if len(problems) == n0:
        good(f"宣言の 3 ラベル = _COURSE_CLASSES[{K.get('_SAPURI_COURSE_NAME')}]")

    print("\n[5] 旧名の対応 (SAPURI_LEGACY_NAME_TO_CODE と app.js の SAPURI_LEGACY_CAPS)")
    n0 = len(problems)
    legacy = K.get("SAPURI_LEGACY_NAME_TO_CODE") or {}
    for name, codes in legacy.items():
        for code in codes:
            if code not in by_code:
                bad(f"SAPURI_LEGACY_NAME_TO_CODE[{name}] の {code} が SAPURI_COURSES に無い")
    js = open(APP_JS, encoding="utf-8").read()
    m = re.search(r"const SAPURI_LEGACY_CAPS = \{\n(.*?)\n\};", js, re.S)
    caps = {}
    if not m:
        bad("app.js に const SAPURI_LEGACY_CAPS = {…}; が無い")
    else:
        for line in m.group(1).split("\n"):
            mm = re.match(r'\s*"([^"]+)":\s*\[(\d+),\s*(\d+)\],\s*$', line)
            if not mm:
                bad(f"app.js SAPURI_LEGACY_CAPS の読めない行: {line.strip()[:60]}")
                continue
            caps[mm.group(1)] = (int(mm.group(2)), int(mm.group(3)))
        by_stripped = {}
        for name, codes in legacy.items():
            by_stripped.setdefault(norm(re.sub(r"^高[123]\s*", "", name)), set()).update(codes)
        for k, (a, b) in caps.items():
            if not (1 <= a <= b):
                bad(f"app.js SAPURI_LEGACY_CAPS[{k}] = [{a}, {b}] が不正")
            codes = [x for x in by_stripped.get(norm(k), ()) if x in by_code and by_code[x]["last"] > 0]
            if codes:
                want = (min(by_code[x]["first"] for x in codes), max(by_code[x]["last"] for x in codes))
                if (a, b) != want:
                    bad(f"app.js SAPURI_LEGACY_CAPS[{k}] = [{a}, {b}] がカタログ ({sorted(codes)} → {list(want)}) と違う")
        mt2 = re.search(r"const TEXTBOOK_TOTAL_UNITS = \{(.*?)\n\};", js, re.S)
        tb_keys = set(re.findall(r"'([^']+)':\s*\d+", mt2.group(1))) if mt2 else set()
        dup = {k for k in tb_keys if norm(k) in {norm(x) for x in caps}}
        if dup:
            bad(f"app.js TEXTBOOK_TOTAL_UNITS にスタサプの旧名の鍵が残っている: {sorted(dup)[:5]}")
        if "server/main.py の SAPURI_LEGACY_NAME_TO_CODE" not in js:
            bad("app.js の SAPURI_LEGACY_CAPS に出所 (server/main.py の SAPURI_LEGACY_NAME_TO_CODE) の注記が無い")
    if len(problems) == n0:
        good(f"旧名 {len(legacy)} 件の code が実在・app.js の静的表 {len(caps)} 件がカタログの写しと一致")

    print("\n[6] 旧初期データ・表の読み書きが残っていない")
    n0 = len(problems)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "SAPURI_LECTURES_SEED":
            bad(f"SAPURI_LECTURES_SEED の参照が残っている (行 {node.lineno})")
    for node in tree.body:   # 起動時 (module 直下) の呼び出し
        for sub in ast.walk(node) if isinstance(node, (ast.Expr, ast.Try)) else ():
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in (
                    "_seed_sapuri_lectures", "_cleanup_old_sapuri_lectures"):
                bad(f"起動時に {sub.func.id}() を呼んでいる (行 {sub.lineno})")
    if re.search(r"(?:SELECT\b[^\"';]*\bFROM\s+sapuri_lectures|INSERT\s+INTO\s+sapuri_lectures)", src, re.I):
        bad("sapuri_lectures 表を SELECT / INSERT する箇所が残っている (講座の正典は SAPURI_COURSES)")
    if len(problems) == n0:
        good("SAPURI_LECTURES_SEED の参照なし・起動時の投入なし・sapuri_lectures を読む箇所なし")

    print("\n[7] 講の題名をリポジトリに置かない (D1)")
    n0 = len(problems)
    try:
        files = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split("\n")
    except Exception as e:
        files = None
        bad(f"git ls-files が読めない ({type(e).__name__}) — 確かめられない")
    if files is not None:
        hits = [f for f in files if re.search(r"(^|/)high_category[^/]*\.tsv$|(^|/)sapuri_lessons_[^/]*\.json$|(^|/)sapuri_import/", f)]
        for f in hits:
            bad(f"講の題名の元データ・取込ファイルがリポジトリにある: {f}")
        if len(problems) == n0:
            good(f"high_category*.tsv / sapuri_lessons_*.json / sapuri_import/ はリポジトリに無い ({len([f for f in files if f])} ファイル)")

    print()
    if problems:
        print(f"違反 {len(problems)} 件")
        return 1
    print("✅ スタサプ講座カタログ: 違反なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
