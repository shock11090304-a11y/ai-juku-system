# -*- coding: utf-8 -*-
"""判定 (_rules.py) と ゲート (check.py) が本当に効いているかを、わざと壊して確かめる (変異試験)。

    python3 scripts/eng_drill_jisei_setsuzoku_gimon/selftest_gate.py

★「検査が緑」と「検査している」は別物。条件の書き間違いや sys.exit(1) の書き忘れ 1 行で、
  ゲートは無音のまま無力化される (2026-08-04 に実在した穴)。ここでは**メモリ上だけ**で
  取込データを1か所ずつ壊し、その1件が必ず指摘されることを確かめる。ディスクには何も書かない。

★変異は「検査の見えやすい位置」に置かない。先頭の問だけを壊すと、たまたま別のガードが
  拾って緑になる。壊す位置は分散させ、期待する文言もガードごとに固有のものを見る。
"""
import contextlib
import copy
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, "..", ".."))
SEED_PATH = os.path.join(ROOT, "seed-data", "grammar_drill_pool_v2_jisei_setsuzoku_gimon.json")

sys.path.insert(0, BASE)
import _rules    # noqa: E402
import build     # noqa: E402
import check     # noqa: E402

DOC = json.loads(open(SEED_PATH, encoding="utf-8").read())
ROWS = DOC["questions"]
ANSWERS = build.answers()


# ---------------------------------------------------------------- 変異の定義
# (名前, 壊す関数(rows, answers) -> (rows, answers), 検出されるべき文言)
def m_pos_token(rows, ans):
    rows[7]["explanation"] = "正解は①。" + rows[7]["explanation"]
    return rows, ans


def m_dup_choice(rows, ans):
    r = rows[23]
    r["choices"] = [r["choices"][0], r["choices"][0], r["choices"][2], r["choices"][3]]
    r["answer"] = 2 if r["choices"][2] == ans[23] else r["answer"]
    return rows, ans


def m_no_value_ref(rows, ans):
    rows[41]["explanation"] = "この形が文脈に最も自然につながるため正しい。ほかの形は文法的に成り立たない。"
    return rows, ans


def m_no_distractor_reason(rows, ans):
    # ★正解 have known の中に埋もれた know を「誤答に触れた」と数えないか (包含関係の実測)
    i = next(k for k, r in enumerate(rows) if r["stem"].startswith("We (   ) each other since"))
    rows[i]["explanation"] = ("since we were children が起点を示すので、現在まで続く継続を表す "
                              "have known を用いる。ほかの形ではこの意味にならない。")
    return rows, ans


def m_answer_points_elsewhere(rows, ans):
    r = rows[55]
    r["answer"] = (r["answer"] + 1) % 4          # 正典の正解文字列と食い違わせる
    return rows, ans


def m_bad_unit(rows, ans):
    rows[12]["unit"] = "時制(新)"
    return rows, ans


def m_bad_level(rows, ans):
    rows[33]["level"] = "kiso"
    return rows, ans


def m_bad_subject(rows, ans):
    rows[66]["subject"] = "eng"
    return rows, ans


def m_no_blank(rows, ans):
    rows[70]["stem"] = rows[70]["stem"].replace("(   )", "___")
    return rows, ans


def m_jp_in_stem(rows, ans):
    # ★文末の記号は問によって . と ? が混在する。置換で当てにいくと**空振りして緑になる**
    #   (実測でここを1度落とした)。最後の1字の手前に差し込む形なら必ず混入する。
    s = rows[85]["stem"]
    rows[85]["stem"] = s[:-1] + " (疑問詞)" + s[-1]
    return rows, ans


def m_dup_stem_inside(rows, ans):
    rows[60]["stem"] = rows[61]["stem"]
    rows[60]["unit"] = rows[61]["unit"]
    return rows, ans


def m_dup_stem_other_file(rows, ans):
    # 既存プール (grammar_drill_pool_v1) と同文・同単元 = 取込時に黙って skip される
    rows[15]["stem"] = "If it (   ) tomorrow, we will cancel the picnic."
    rows[15]["unit"] = "時制"
    return rows, ans


def m_long_source(rows, ans):
    rows[9]["source"] = "drill-tense-conj-wh-20260909-toolong"
    return rows, ans


def m_answer_bias(rows, ans):
    for r in rows:                                # 全問の正解を先頭へ = 偏り + 連続
        a = r["choices"][r["answer"]]
        r["choices"] = [a] + [c for c in r["choices"] if c != a]
        r["answer"] = 0
    return rows, ans


def m_cyclic_answers(rows, ans):
    for i, r in enumerate(rows):                  # 1,2,3,4,1,2,3,4… の周期に戻す
        a = r["choices"][r["answer"]]
        rest = [c for c in r["choices"] if c != a]
        rest.insert(i % 4, a)
        r["choices"] = rest
        r["answer"] = i % 4
    return rows, ans


def m_short_expl(rows, ans):
    rows[48]["explanation"] = ans[48] + " が正しい。"
    return rows, ans


def m_missing_question(rows, ans):
    del rows[3]                                   # 正典と問数がずれる
    return rows, ans


MUTATIONS = [
    ("解説に位置トークン (①)",          m_pos_token,              "位置を指す書き方"),
    ("選択肢の重複",                    m_dup_choice,             "同じ選択肢が2つ"),
    ("解説が正解を値で示さない",        m_no_value_ref,           "値参照になっていない"),
    ("解説が誤答に触れない",            m_no_distractor_reason,   "誤答に一切触れていない"),
    ("answer が別の選択肢を指す",       m_answer_points_elsewhere, "正典の正解と違う"),
    ("単元名が GRAMMAR_UNITS 外",       m_bad_unit,               "GRAMMAR_UNITS に無い"),
    ("レベル名が不正",                  m_bad_level,              "GRAMMAR_LEVELS に無い"),
    ("subject が english でない",       m_bad_subject,            "subject が english でない"),
    ("stem に空所が無い",               m_no_blank,               "空所"),
    ("stem に日本語が混ざる",           m_jp_in_stem,             "日本語が混ざっている"),
    ("同一ファイル内で stem 重複",      m_dup_stem_inside,        "同文"),
    ("source が30字超",                 m_long_source,            "30字を超える"),
    ("正解位置の偏り・連続",            m_answer_bias,            "偏っている"),
    ("正解位置が周期的 (1,2,3,4の反復)", m_cyclic_answers,        "等差で"),
    ("解説が短すぎる",                  m_short_expl,             "短すぎる"),
    ("問数が正典とずれる",              m_missing_question,       "問数が正典と違う"),
]


def run_rules(mutate):
    rows, ans = mutate(copy.deepcopy(ROWS), list(ANSWERS))
    return "\n".join(_rules.validate(rows, ans, ROOT))


def run_check():
    """check.main() を回して (終了コード, 出力) を返す。例外も出力として扱う。"""
    check.NG.clear()
    buf, code = io.StringIO(), 0
    try:
        with contextlib.redirect_stdout(buf):
            check.main()
    except SystemExit as e:
        code = e.code or 0
    except Exception as e:
        code = 1
        buf.write(f"{type(e).__name__}: {e}")
    return code, buf.getvalue()


def main():
    print("=== 判定とゲートの自己テスト (変異試験) ===")
    missed = []

    # --- 壊していない状態では通ること (ここが赤なら以降の判定は意味を持たない)
    code, out = run_check()
    if code != 0:
        print("壊していない状態で check.py が通らない。先に指摘を直すこと:")
        print(out)
        sys.exit(1)
    print("  検出: (対照) 壊していない状態では通る")

    # --- _rules.validate の各ガード
    for name, mutate, expected in MUTATIONS:
        out = run_rules(mutate)
        ok = expected in out
        print(f"  {'検出' if ok else '素通り'}: {name}")
        if not ok:
            missed.append(name)

    # --- 他ファイルとの重複 (別の入口なので別に回す)
    out = "\n".join(_rules.duplicate_across_seed(
        *m_dup_stem_other_file(copy.deepcopy(ROWS), list(ANSWERS))[:1], ROOT, SEED_PATH))
    ok = "同文" in out
    print(f"  {'検出' if ok else '素通り'}: 既存プールと stem 重複")
    if not ok:
        missed.append("既存プールと stem 重複")

    # --- CEO 画面の取込ボタン (押せる導線が消えた/数字がずれた/線が外れた)
    html = open(os.path.join(ROOT, "ceo.html"), encoding="utf-8").read()
    seed_url = "/seed-data/" + os.path.basename(SEED_PATH)
    for name, broken, expected in [
        ("ボタンごと消えた",
         html.replace('id="grammarTenseConjWhImportBtn"', 'id="somethingElse"'), "取込ボタン"),
        ("data-size がシードとずれた",
         html.replace('data-size="90"', 'data-size="88"'), "問数と違う"),
        ("data-seed が別ファイルを指す",
         html.replace(seed_url, "/seed-data/grammar_drill_pool_v1.json"), "指していない"),
        ("click ハンドラが外れた",
         html.replace("getElementById('grammarTenseConjWhImportBtn')", "getElementById('x')"),
         "click ハンドラが繋がっていない"),
    ]:
        out = "\n".join(_rules.ceo_button_wiring(broken, seed_url, len(ROWS)))
        ok = expected in out
        print(f"  {'検出' if ok else '素通り'}: CEO の取込ボタン — {name}")
        if not ok:
            missed.append(f"CEOボタン({name})")

    # --- JSON を手で書き換えた場合 (ビルダーの出力と食い違う)
    orig = build.build
    try:
        build.build = lambda: ((lambda rs, bl: ([dict(r, stem=r["stem"] + " ") for r in rs], bl))(*orig()))
        code, out = run_check()
        ok = code != 0 and "build.py の出力と一致しない" in out
    finally:
        build.build = orig
    print(f"  {'検出' if ok else '素通り'}: JSON の手編集 (再生成と差分)")
    if not ok:
        missed.append("JSON の手編集")

    if missed:
        print(f"\n素通りした変異 {len(missed)} 件: " + " / ".join(missed))
        print("ガードが効いていない。_rules.py / check.py を直すこと。")
        sys.exit(1)
    print(f"\n違反: 0 件  [OK] 変異 {len(MUTATIONS) + 6} 種すべてを検出した")


if __name__ == "__main__":
    main()
