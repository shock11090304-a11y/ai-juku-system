#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紙の教材の中身を、冊子受験アプリに取り込める JSON へ機械変換する。

    python3 scripts/book_exam/convert_workbook.py            # 全部変換して一覧を出す
    python3 scripts/book_exam/convert_workbook.py --out DIR  # DIR に .json を書き出す
    python3 scripts/book_exam/convert_workbook.py kaki       # 名前で絞る

■ なぜ要るか
  冊子アプリは 1 問ごとに「番号 / ページ / 形式 / 選択肢数 / 正解 / 配点 / 解説」を持つ。
  手で入れると 1 問 1〜2 分、リポジトリの紙教材 1,900 問なら 30〜60 時間かかる。
  だが **紙教材の元データには正解も解説も既に入っている**。機械で移せば数分で済む。

■ ★ ページ番号は出せない
  questions.page は「PDF の何ページにあるか」。組版してみないと分からず、
  組版は Chrome を使う build*.py の仕事なので、ここでは **page = null** にする。
  受験画面では「ページ指定なし」のグループに出る。解答も採点もできるが、
  設問からページへ飛べないだけ。ページを入れたければ、取り込んだ後に
  登録画面で直すか、build 側に「何問目が何ページか」を出させること。

■ ★ 変換できなかったものは必ず一覧に出す
  黙って減らすと「全部移した」に見えて、後で足りないことに気づけない。
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# -----------------------------------------------------------------------------
# どの教材をどの教科として入れるか。
# ★ books.subject は閉じた集合 (supabase/migrations/…_books_subject_widen.sql)。
#   ここに無いディレクトリは 'other' で入れる。
# -----------------------------------------------------------------------------
SUBJECT_BY_DIR = {
    "kaki_koushuu_eng": "grammar",
    "eng_kokkoritsu_nankan": "grammar",
    "eng_chuken_kokkoritsu": "grammar",
    "chugaku2_eigo_soufukushu": "grammar",
    "eng_hinshi_bunkai": "grammar",
    "eng_march_gw": "reading",
    "eng_therules": "grammar",
    "kobun_bunpo_12": "japanese",
    "kobun_jodoushi": "japanese",
    "kobun_rules_kanzen": "japanese",
    "kokugo_text": "japanese",
    "math_workbook": "math",
    "rika_enshu": "science",
    "rika_kagaku": "science",
    "shakai_chiri": "social",
    "nihonshi_koukou_workbook": "social",
}

# -----------------------------------------------------------------------------
# ★ わざと変換しないもの。理由を書かずに足さないこと。
# -----------------------------------------------------------------------------
EXCLUDE = {
    "math_workbook":
        "数学は正解が LaTeX ($x=3$ 等) で、文字列一致では採点できない。"
        "生徒に LaTeX を打たせることになるので、この画面には向かない。"
        "紙で配るか、採点しない冊子として扱うこと "
        "(今のスキーマは correct_answer 必須なので後者は表現できない)。",
}

LETTERS = "abcdefghij"


def subject_for(path):
    parts = os.path.normpath(path).split(os.sep)
    for p in parts:
        if p in SUBJECT_BY_DIR:
            return SUBJECT_BY_DIR[p]
    return "other"


# =============================================================================
# 1 問ぶんの変換
# =============================================================================
def detect_base(raws):
    """その教材の選択肢番号が 0 起算か 1 起算かを **論理的に** 判定する。

    ★ ここがこの変換で一番大事。間違えると **その冊子の選択問題が全部 1 つずれる**。
      生徒は正しく選んでいるのに不正解になり、しかも画面上は何も壊れて見えない。

    判定の根拠 (文面の一致では決められない。解説には誤答の説明も入るため):
      ・1 起算なら **0 は絶対に出ない**  → 0 があれば 0 起算で確定
      ・0 起算なら **選択肢数と同じ値は絶対に出ない** → あれば 1 起算で確定
      ・どちらも出なければ決められない (中間の値しか使っていない小さな教材)

    実測 (2026-08-14, リポジトリ全体): 0 起算で確定 45 本 / 1 起算で確定 0 本 /
    判定不能 3 本。**1 起算の教材は 1 本も無い。**
    判定不能なものは全体に合わせて 0 起算として扱い、要確認として一覧に出す。

    @returns 'zero' | 'one' | 'unknown'
    """
    has_zero = has_max = False
    for r in raws:
        a = r.get("ans", r.get("answer"))
        ch = r.get("choices") or r.get("parts")
        if not (isinstance(ch, list) and isinstance(a, int) and not isinstance(a, bool)):
            continue
        if a == 0:
            has_zero = True
        if a == len(ch):
            has_max = True
    if has_zero and has_max:
        return "conflict"        # 同じファイルに両方 = 元データが壊れている
    if has_zero:
        return "zero"
    if has_max:
        return "one"
    return "unknown"


def convert_one(raw, number, base):
    """教材側の 1 問 → アプリの設問。変換できなければ (None, 理由)。

    ★ 形が源によってばらばら (stem/q、choices/parts、ans が数字/文字列) なので、
      **キー名でなく形で** 判定する。名前で決め打ちすると新しい教材で黙って落ちる。
    @param base detect_base() の結果。'one' 以外は 0 起算として +1 する。
    """
    shift = 0 if base == "one" else 1
    stem = raw.get("stem") or raw.get("q") or raw.get("html")
    if not stem:
        return None, "設問文が無い"
    if "ans" not in raw and "answer" not in raw:
        return None, "正解が無い"
    ans = raw.get("ans", raw.get("answer"))

    exp = raw.get("exp") or raw.get("explanation") or ""
    # 誤り指摘系は「正しい形」が別のキーにある。解説の先頭に置く (無いと解説が意味を成さない)
    fix = raw.get("fix") or raw.get("correct")
    if fix and not str(fix).isdigit():
        exp = f"正しい形: {fix}\n{exp}".strip()
    point = raw.get("point")
    if point and len(str(point)) > 24:      # 長いものは単元 ID でなく解説の一部
        exp = f"{exp}\n\n【ポイント】{point}".strip()
        point = None

    points = raw.get("pt") or raw.get("points") or 1
    try:
        points = max(1, int(points))
    except (TypeError, ValueError):
        points = 1

    out = {
        "number": number,
        "page": None,                    # ★ 組版しないと分からない (冒頭の注記)
        "points": points,
        "unit_tag": (str(point).strip() or None) if point else None,
        "explanation": (exp or None),
    }

    choices = raw.get("choices")
    parts = raw.get("parts")

    # --- 選択式: 選択肢の一覧があり、正解が 1 起算の番号 --------------------
    if isinstance(choices, list) and len(choices) >= 2:
        try:
            n = int(ans) + shift          # ★ 0 起算なら 1 起算へ直す (detect_base)
        except (TypeError, ValueError):
            return None, f"選択肢があるのに正解が番号でない ({ans!r})"
        if not (1 <= n <= len(choices)):
            return None, f"正解 {ans} (+{shift}) が選択肢 {len(choices)} 個の範囲外"
        if len(choices) > 10:
            return None, f"選択肢が {len(choices)} 個 (上限 10)"
        out.update(answer_type="choice", choice_count=len(choices),
                   correct_answer=str(n), accepted_answers=[])
        # ★ 人が 30 秒で確かめるための материал。起算の判定は機械では証明しきれないので、
        #   「その番号が指している選択肢の中身」を必ず残す。
        out["_preview"] = {
            "stem": str(stem)[:80],
            "choices": [str(c)[:40] for c in choices],
            "correct_text": str(choices[n - 1])[:40],
        }
        return out, None

    # --- 誤り指摘: 下線部が a/b/c/d で振られている ---------------------------
    #   ★ 選択式にしない。PDF に出ているのは a〜d の記号で、番号のピルを出すと
    #     「PDF は b、答案は 2」というずれが生徒に見える。記号のまま書かせる。
    if isinstance(parts, list) and len(parts) >= 2:
        try:
            i = int(ans) + shift          # ★ 同上
        except (TypeError, ValueError):
            return None, f"下線部があるのに正解が番号でない ({ans!r})"
        if not (1 <= i <= len(parts)) or len(parts) > len(LETTERS):
            return None, f"正解 {ans} (+{shift}) が下線部 {len(parts)} 個の範囲外"
        letter = LETTERS[i - 1]
        out.update(answer_type="short", choice_count=None, correct_answer=letter,
                   accepted_answers=[letter.upper()])
        return out, None

    # --- 記述 ---------------------------------------------------------------
    s = str(ans).strip()
    if s == "":
        return None, "正解が空"
    if isinstance(ans, (int, float)) or re.fullmatch(r"[0-9]+", s):
        # 選択肢が無いのに正解が数字だけ = 元データで選択肢が落ちている疑い。
        # そのまま入れると生徒は数字を打つことになるので、変換しない。
        return None, f"選択肢が無いのに正解が数字だけ ({s})"
    out.update(answer_type="short", choice_count=None, correct_answer=s,
               accepted_answers=[])
    return out, None


# =============================================================================
# 教材ファイルから設問を拾う
# =============================================================================
def harvest(obj):
    """入れ子のどこにあっても「設問らしい dict」を順番に拾う。"""
    found = []

    def walk(o):
        if isinstance(o, dict):
            has_stem = any(k in o for k in ("stem", "q", "html"))
            has_ans = any(k in o for k in ("ans", "answer"))
            if has_stem and has_ans:
                found.append(o)
                return                      # 設問の中はもう掘らない
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    return found


def load_python_content(path):
    """content*.py を読み込んで、モジュールの中の list/dict を全部返す。

    ★ import すると副作用 (PDF 生成・ファイル書き出し) が走るものがあるので
      **exec しない**。ast でリテラルだけを取り出す。
    """
    import ast
    src = open(path, encoding="utf-8", errors="replace").read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return None, f"読めない ({e.msg})"
    out = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        try:
            out.append(ast.literal_eval(node.value))
        except (ValueError, SyntaxError):
            continue          # 関数呼び出しや f-string を含むものは飛ばす
    return out, None


def title_for(path, data):
    """教材の題名。元データに無ければファイル名から作る。"""
    if isinstance(data, dict):
        for k in ("title", "name", "book_title"):
            if isinstance(data.get(k), str) and data[k].strip():
                base = data[k].strip()
                no = data.get("no")
                return f"{base}" + (f" 第{no}講" if no else "")
    stem = os.path.splitext(os.path.basename(path))[0]
    d = os.path.basename(os.path.dirname(path))
    if d == "data":
        d = os.path.basename(os.path.dirname(os.path.dirname(path)))
    return f"{d} / {stem}"


def sources():
    """変換対象のファイル。EXCLUDE のディレクトリは外す。"""
    out = []
    for pat in ("scripts/*/data/*.json", "scripts/*/content*.py", "scripts/*/*/content*.py"):
        import glob
        out += sorted(glob.glob(os.path.join(ROOT, pat)))
    return [p for p in out
            if not any(f"{os.sep}{d}{os.sep}" in p for d in EXCLUDE)]


def convert_file(path):
    rel = os.path.relpath(path, ROOT)
    if path.endswith(".json"):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            return None, [f"{rel}: 読めない ({e})"]
        blobs = [data]
    else:
        blobs, err = load_python_content(path)
        if err:
            return None, [f"{rel}: {err}"]
        data = None

    raws = []
    for b in blobs:
        raws += harvest(b)
    if not raws:
        return None, []                    # 設問を持たないファイル (静かに飛ばす)

    base = detect_base(raws)
    if base == "conflict":
        # ★ 同じファイルに 0 と「選択肢数」の両方が出る = 元データが壊れている。
        #   どちらに寄せても半分が間違うので **変換しない**。
        return None, [f"{rel}: 選択肢番号の起算が混在している (0 も 選択肢数 も出る)。"
                      f"元データを直してから変換すること"]

    questions, skipped = [], []
    for raw in raws:
        q, why = convert_one(raw, len(questions) + 1, base)
        if q is None:
            skipped.append(why)
        else:
            questions.append(q)
    if not questions:
        return None, [f"{rel}: {len(raws)} 問すべて変換できず ({skipped[0] if skipped else '?'})"]

    preview = [dict(q["_preview"], number=q["number"], correct_answer=q["correct_answer"])
               for q in questions if q.get("_preview")][:3]
    has_choice = any(q["answer_type"] == "choice" for q in questions)
    for q in questions:
        q.pop("_preview", None)

    bundle = {
        "source": rel,
        "has_choice": has_choice,
        "preview": preview,
        "choice_base": base,        # 'zero' / 'one' / 'unknown'
        "book": {
            "title": title_for(path, data if isinstance(data, dict) else None),
            "subject": subject_for(rel),
            "level": None,
            "time_limit_min": None,
        },
        "questions": questions,
        "skipped": skipped,
    }
    return bundle, []


# =============================================================================
def validate_with_real_model(bundles):
    """★ 変換したものを **アプリと同じ検証器** に通す。

    Python 側で書き直すと二重管理になり、片方だけ直して気づかない。
    node で実物の exam-book-admin-model.mjs を呼ぶ。
    """
    node = __import__("shutil").which("node")
    if not node:
        return None, "node が無いので検証できなかった"
    payload = json.dumps([{"source": b["source"], "questions": b["questions"]}
                          for b in bundles], ensure_ascii=False)
    script = r"""
import { validateQuestions } from './exam-book-admin-model.mjs';
let buf = ''; process.stdin.setEncoding('utf8');
process.stdin.on('data', (d) => { buf += d; });
process.stdin.on('end', () => {
  const out = [];
  for (const b of JSON.parse(buf)) {
    const v = validateQuestions(b.questions, { pageCount: null });
    out.push({ source: b.source, ok: v.ok,
               errors: v.errors.slice(0, 5).map((e) => `${e.i + 1}行目 ${e.field}: ${e.msg}`) });
  }
  console.log(JSON.stringify(out));
});
"""
    tmp = os.path.join(ROOT, ".convert_validate.mjs")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(script)
        r = subprocess.run([node, tmp], input=payload, capture_output=True,
                           text=True, cwd=ROOT, timeout=120)
        if r.returncode:
            return None, (r.stderr or r.stdout).strip()[-300:]
        return json.loads(r.stdout), None
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filter", nargs="*", help="名前で絞る (部分一致)")
    ap.add_argument("--out", help="書き出し先ディレクトリ")
    a = ap.parse_args()

    files = sources()
    if a.filter:
        files = [f for f in files if any(k in f for k in a.filter)]

    bundles, problems = [], []
    for f in files:
        b, errs = convert_file(f)
        problems += errs
        if b:
            bundles.append(b)

    if not bundles:
        print("変換できるものがありませんでした")
        return 1

    checked, verr = validate_with_real_model(bundles)
    bad = {}
    if checked:
        bad = {c["source"]: c["errors"] for c in checked if not c["ok"]}

    total = sum(len(b["questions"]) for b in bundles)
    skipped = sum(len(b["skipped"]) for b in bundles)
    print(f"=== 紙教材 → 冊子アプリ 変換 ===")
    for d, why in EXCLUDE.items():
        print(f"  [除外] {d}: {why}")
    print(f"  変換できた: {len(bundles)} 冊 / {total} 問")
    print(f"  変換できなかった設問: {skipped} 問")
    if verr:
        print(f"  ★ 検証を回せなかった: {verr}")

    by_subject = {}
    for b in bundles:
        by_subject.setdefault(b["book"]["subject"], [0, 0])
        by_subject[b["book"]["subject"]][0] += 1
        by_subject[b["book"]["subject"]][1] += len(b["questions"])
    BASE_LABEL = {
        "zero": "0 起算 (+1 して変換)",
        "one": "1 起算 (そのまま)",
        "unknown": "判定不能 (0 起算として扱った)",
    }
    bases = {}
    for b in bundles:
        bases[b["choice_base"]] = bases.get(b["choice_base"], 0) + 1
    parts = [f"{BASE_LABEL.get(k, k)}: {v} 冊" for k, v in sorted(bases.items())]
    print("\n  選択肢番号の起算 — " + " / ".join(parts))

    print("\n  教科別:")
    for s, (nb, nq) in sorted(by_subject.items(), key=lambda x: -x[1][1]):
        print(f"    {s:10} {nb:3} 冊 {nq:5} 問")

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        for b in bundles:
            name = re.sub(r"[^\w.-]", "_", b["source"]) + ".json"
            with open(os.path.join(a.out, name), "w", encoding="utf-8") as f:
                json.dump(b, f, ensure_ascii=False, indent=1)
        print(f"\n  {a.out} に {len(bundles)} 件書き出しました")

    # ★ 落としたものは必ず出す。黙って減らすと「全部移した」に見える。
    if bad:
        print(f"\n=== ★ 検証を通らなかった冊子 ({len(bad)} 件) ===")
        for src, errs in list(bad.items())[:20]:
            print(f"  ✗ {src}")
            for e in errs[:3]:
                print(f"      {e}")
    if problems:
        print(f"\n=== 変換できなかったファイル ({len(problems)} 件) ===")
        for p in problems[:20]:
            print(f"  - {p}")

    # ★ 記述だけの冊子は選択肢番号を使わないので、起算が不明でも実害が無い。
    #   全部に警告を出すと、本当に確認が要る冊子が埋もれる。
    unknown = [b for b in bundles if b["choice_base"] == "unknown" and b["has_choice"]]
    if unknown:
        print(f"\n=== ★ 起算を判定できなかった冊子 ({len(unknown)} 件) — 要確認 ===")
        print("   中間の値しか使っていないため 0 と 1 のどちらか決められない。")
        print("   リポジトリ全体が 0 起算なのでそう扱ったが、**1 問だけ実物と照合すること**。")
        for b in unknown:
            print(f"  - {b['source']} ({len(b['questions'])} 問)")

    # ★ 起算の判定は機械では証明しきれない (解説には誤答の説明も入るので文字列一致は
    #   当てにならない)。冊子ごとに「1 問目の正解が指している中身」を出し、
    #   人が実物と 1 件だけ照合できるようにする。
    print("\n=== 起算の確認用 (各冊 1 問目) — 実物と 1 件だけ照合してください ===")
    shown = 0
    for b in bundles:
        if not b["preview"]:
            continue
        pv = b["preview"][0]
        print(f"  {b['source']}")
        print(f"    問{pv['number']}: {pv['stem']}")
        print(f"    → 正解 {pv['correct_answer']} 番 = 「{pv['correct_text']}」")
        shown += 1
        if shown >= 8 and not a.out:
            print(f"  … 残り {len([x for x in bundles if x['preview']]) - shown} 冊は --out で書き出すと全部見られます")
            break

    worst = [b for b in bundles if b["skipped"]]
    if worst:
        print(f"\n=== 一部の設問を落とした冊子 ({len(worst)} 件) ===")
        for b in sorted(worst, key=lambda x: -len(x["skipped"]))[:10]:
            why = {}
            for w in b["skipped"]:
                key = re.sub(r"\(.*\)", "(…)", w)
                why[key] = why.get(key, 0) + 1
            top = sorted(why.items(), key=lambda x: -x[1])[:2]
            print(f"  - {b['source']}: {len(b['skipped'])} 問 — "
                  + " / ".join(f"{k}×{v}" for k, v in top))

    # ★ 起算を間違えると「範囲外の問だけが静かに落ちて、残りは正しい形の
    #   間違った答えになる」。検証器には見分けられない (2 も 3 も legal な正解)。
    #   だが **落ちた理由** には必ず「範囲外」が出る。そこを見張る。
    out_of_range = [w for b in bundles for w in b["skipped"] if "範囲外" in w]
    if out_of_range:
        print(f"\n=== ★ 起算がずれている疑い ({len(out_of_range)} 問) ===")
        print("   選択肢の範囲外になった正解がある。0 起算 / 1 起算 の判定を")
        print("   間違えると、残りの問は **正しい形の間違った答え** になり、")
        print("   検証器では見分けられない。detect_base() を確かめること。")
        for w in out_of_range[:5]:
            print(f"     {w}")

    # ★ 落とした設問が 1 問でもあれば失敗にする。黙って減らすと
    #   「全部移した」に見えて、後から足りないことに気づけない。
    if skipped:
        print(f"\n★ {skipped} 問を変換できていない。理由を確かめて、"
              f"直すか EXCLUDE に理由付きで足すこと")

    return 1 if (bad or skipped) else 0


if __name__ == "__main__":
    # ★ import しても main() が走らないようにしてある。
    #   convert_kyotsu_yaml.py が validate_with_real_model() を借りるため。
    #   ここを外すと import しただけで全教材の変換が走り、ゲートが二重に回る。
    sys.exit(main())
