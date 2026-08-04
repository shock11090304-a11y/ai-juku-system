# -*- coding: utf-8 -*-
"""
高校日本史 演習プリント No.01  機械ゲート（build.py が先に実行し、FAIL ならビルドを中止する）

検査するもの:
  1. 年代整序問題：解答の並びを「事実の年代」から独立に再計算し、content の ans と一致するか
  2. 選択肢：4択の重複なし／ans が範囲内
  3. 配点：小問の合計が大問の point と一致／全体合計が META['total'] と一致
  4. 解説：全問に exp があるか
  5. 汎用ゲート（_workbook_gates.Gate）：正解位置の偏り／正解肢が最長のテル／
     解説の選択肢番号ズレ／絵文字・制御文字などのグリフ監査
"""
import sys, os, re
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import content as C  # noqa: E402
from _workbook_gates import Gate  # noqa: E402

FAIL, WARN = [], []


def fail(msg):
    FAIL.append(msg)


# ---------------------------------------------------------------- 1. 年代整序の独立検算
# 設問文中に登場する「年代の古い順」問題のラベル→史実年をここで独立に持つ
# （content.py の ans を信用せず、史実そのものから正しい並びを再計算するのが目的）。
YEAR = {
    "大宝律令の制定": 701, "乙巳の変": 645, "墾田永年私財法の発布": 743,
    "平治の乱": 1159, "保元の乱": 1156, "平清盛が太政大臣となる": 1167,
    "文永の役": 1274, "御成敗式目の制定": 1232, "弘安の役": 1281,
    "足利尊氏が征夷大将軍に任じられる": 1338, "建武の新政が始まる": 1334, "南北朝の合一": 1392,
    "豊臣秀吉が刀狩令を出す": 1588, "本能寺の変": 1582, "豊臣秀吉が全国統一を達成する": 1590,
    "島原の乱（島原・天草一揆）": 1637, "武家諸法度に参勤交代が追加される": 1635,
    "ポルトガル船の来航が禁止される": 1639,
    "寛政の改革（棄捐令）": 1789, "天保の改革（上知令）": 1843, "享保の改革（公事方御定書の制定）": 1742,
    "地租改正条例の公布": 1873, "大日本帝国憲法の発布": 1889, "国会開設の勅諭": 1881,
    "満州事変": 1931, "普通選挙法の成立": 1925, "世界恐慌がおこる": 1929,
    "日独伊三国同盟の成立": 1940, "満州国の建国": 1932, "日中戦争の開始（盧溝橋事件）": 1937,
    "朝鮮戦争がおこる": 1950, "サンフランシスコ平和条約の調印": 1951, "日本国憲法の公布": 1946,
}
ROMAN = ["I", "II", "III", "IV"]


def check_order_questions():
    n = 0
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            if "年代の古い順" not in q["q"]:
                continue
            n += 1
            items = re.findall(r"(I{1,3})　(.+)", q["q"])
            if not items:
                fail(f"[整序] {b['no']}問{i} 「I　」形式のラベルを1件も検出できない（区切り文字が全角スペースか確認）")
                continue
            missing = [label for _, label in items if label not in YEAR]
            if missing:
                fail(f"[整序] {b['no']}問{i} YEAR辞書に無いラベル: {missing}")
                continue
            order = sorted(items, key=lambda x: YEAR[x[1]])
            correct_str = "→".join(r for r, _ in order)
            if q["choices"][q["ans"]] != correct_str:
                fail(f"[整序] {b['no']}問{i} 独立再計算={correct_str} だが content の正解="
                     f"{q['choices'][q['ans']]}（史実年: " +
                     "／".join(f'{r}={YEAR[l]}' for r, l in items) + "）")
            else:
                print(f"  [整序] {b['no']}問{i} 独立再計算={correct_str} 一致 OK")
    print(f"  [整序] 年代整序問題 合計 {n} 問")


# ---------------------------------------------------------------- 2. 選択肢の重複・範囲
def check_choices():
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            if len(q["choices"]) != 4:
                fail(f"[選択肢] {b['no']}問{i} 選択肢が4つでない: {len(q['choices'])}件")
            if len(set(q["choices"])) != len(q["choices"]):
                fail(f"[選択肢] {b['no']}問{i} 選択肢に重複がある")
            if not (0 <= q["ans"] < len(q["choices"])):
                fail(f"[選択肢] {b['no']}問{i} ans が範囲外: {q['ans']}")
    print("  [選択肢] 全問4択・重複なし・ans範囲内 OK")


# ------------------------------------------- 2b. 正解位置パターンの予測可能性
# ★2026-07-30 3並列レビューで「第9〜11問が3大問連続で全く同じ配置(②②③)」を検出。
#   choice_position（全体の偏り）だけでは検出できない、大問単位の反復パターンを
#   ここで機械チェックする。1大問=3問の正解位置(0始まり)をタプル化し、重複が
#   あれば通しで解く生徒に読まれてしまう。
def check_pattern_repeat():
    triples = [tuple(q["ans"] for q in b["qs"]) for b in C.PART2]
    seen = {}
    for b, t in zip(C.PART2, triples):
        seen.setdefault(t, []).append(b["no"])
    dups = {t: bs for t, bs in seen.items() if len(bs) > 1}
    if dups:
        fail("[正解位置パターン] 複数の大問が同じ配置パターンを共有している（通しで解くと読まれる）: "
             + "／".join(f'{t}: {"・".join(bs)}' for t, bs in dups.items()))
    else:
        print(f"  [正解位置パターン] 大問{len(triples)}本 すべて異なる配置パターン OK")


# ---------------------------------------------------------------- 3. 配点
def check_points():
    total = 0
    for b in C.PART2:
        sub = sum(q["pt"] for q in b["qs"])
        if sub != b["point"]:
            fail(f"[配点] {b['no']} 小問配点合計{sub} != 大問配点{b['point']}")
        total += sub
    if total != C.META["total"]:
        fail(f"[配点] 全体合計{total} != META['total']={C.META['total']}")
    else:
        print(f"  [配点] 大問12本 合計{total}点 = META['total'] OK")


# ---------------------------------------------------------------- 4. 解説の有無
def check_exp():
    n = 0
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            n += 1
            if not q.get("exp"):
                fail(f"[解説] {b['no']}問{i} に exp が無い")
    print(f"  [解説] 全{n}問に exp あり OK")


# ---------------------------------------------------------------- 実行
def main():
    print("=== 高校日本史 演習 No.01 機械ゲート ===")
    print("[1] 年代整序の独立検算"); check_order_questions()
    print("[2] 選択肢の重複・範囲");  check_choices()
    print("[2b] 正解位置パターンの重複"); check_pattern_repeat()
    print("[3] 配点");              check_points()
    print("[4] 解説の有無");         check_exp()

    print("[5] 汎用ゲート（_workbook_gates）")
    g = Gate()
    mcs = [{"where": f'{b["no"]}問{i}', "choices": q["choices"], "ans": q["ans"], "exp": q["exp"], "q": q["q"]}
           for b in C.PART2 for i, q in enumerate(b["qs"], start=1)]
    # ★組合せ（あ－正／い－誤…）と整序（I→II→III…）は選択肢が同じ語の並べ替えにすぎず、
    #   4択とも文字数が必ず一致する（＝どれを正解にしても機械的に「最長」判定される）。
    #   longest_tell は「内容で選ばせる四択」だけに適用する。
    content_mcs = [m for m in mcs if "の組み合わせ" not in m["q"] and "年代の古い順" not in m["q"]]
    tied_mcs = [m for m in mcs if m not in content_mcs]
    bad_tie = [m["where"] for m in tied_mcs if len(set(len(c) for c in m["choices"])) != 1]
    if bad_tie:
        fail(f"[整序/組合せ] 選択肢の文字数が完全一致していない（内容以外の要因で答えが割れる恐れ）: {bad_tie}")
    else:
        print(f"  [整序/組合せ] {len(tied_mcs)}問 選択肢は常に同一文字数（longest_tell対象外は妥当）OK")
    g.longest_tell(content_mcs)
    g.exp_choice_refs(mcs)
    g.choice_position(mcs)
    g.glyphs({"META": C.META, "PART2": C.PART2})
    ok = g.report(exit_on_fail=False)
    if not ok:
        FAIL.append("_workbook_gates.Gate で FAIL")

    print()
    for w in WARN:
        print("WARN:", w)
    if FAIL:
        print(f"\n=== FAIL {len(FAIL)}件 ===")
        for f in FAIL:
            print(" ×", f)
        sys.exit(1)
    print(f"\n=== ALL PASS ({len(WARN)} warnings) ===")


if __name__ == "__main__":
    main()
