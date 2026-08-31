# -*- coding: utf-8 -*-
"""check.py の各ゲートが「本当に落とせるか」を、故意の欠陥を注入して確かめる。

★ゲートは `sys.exit(1)` の書き忘れ 1 行で無力化される。「検査を書いた」と
  「検査が効いている」は別なので、機械で固定する。
  ここに並ぶ [NG] / [素通り] の行は**合格時の正常な出力**（わざと壊した例の検出結果）。
"""
import copy
import signal
import sys

import build
import check as K
import content as C

PARTS = ("PART1", "PART2", "PART3")
DICTS = ("SYN_POOL",)


def snapshot():
    base = {k: copy.deepcopy(getattr(C, k)) for k in PARTS}
    base.update({k: copy.deepcopy(getattr(C, k)) for k in DICTS})
    return base


def restore(base):
    # ★スライス代入で**同じリスト実体**を書き換える。新しいリストを代入すると
    #   check / build が import 時に束縛した参照が古いままになり、注入が効かない。
    for k in PARTS:
        getattr(C, k)[:] = copy.deepcopy(base[k])
    for k in DICTS:
        d = getattr(C, k)
        d.clear()
        d.update(copy.deepcopy(base[k]))


def run_check():
    K.ERR.clear()
    K.WARN.clear()
    code = 0
    try:
        K.main()
    except SystemExit as e:
        code = e.code or 0
    return code, list(K.ERR)


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


def first1(): return C.PART1[0]["items"][0]
def first3(): return C.PART3[0]["items"][0]


@case("分解DSLと英文のドリフト（en だけ書き換える）")
def _():
    first1()["en"] = first1()["en"].replace(" ", " very ", 1)


@case("トップレベルのラベル漏れ（解答欄が空のまま刷られる）")
def _():
    it = first1()
    it["dsl"] = it["dsl"].replace("{S:", "", 1).replace("}", "", 1)


@case("pat（文型）と主節ラベルの不一致")
def _():
    it = first1()
    it["pat"] = "第4文型（SVOO）" if "第4" not in it["pat"] else "第1文型（SV）"


@case("第1部に主節の V が 2 つある")
def _():
    it = first1()
    it["dsl"] = it["dsl"].replace("{S:", "{V:", 1)


@case("4択の正解位置の偏り")
def _():
    for q in C.PART2:
        q["ans"] = 0


@case("設問文が、その文に無い英語を引用している")
def _():
    C.PART2[0]["q"] += "　下線部 the quiet mountain village of yesterday に注目せよ。"


@case("解説が自称する正解と ans のずれ")
def _():
    q = C.PART2[0]
    wrong = "①②③④"[(q["ans"] + 1) % 4]
    q["exp"] = f"正解は{wrong}。" + q["exp"]


@case("選択肢の重複")
def _():
    C.PART2[0]["choices"][1] = C.PART2[0]["choices"][0]


@case("正解肢だけが極端に長い（長さテル）")
def _():
    q = C.PART2[0]
    q["choices"][q["ans"]] = q["choices"][q["ans"]] + "。" + "この選択肢だけがとても長い" * 6


@case("生タグ混入（解説に < を直書きして語が消える）")
def _():
    first1()["notes"][0] = "<who study public health> は researchers にかかる形容詞のカタマリ。"


@case("英文の重複（同じ文を 2 か所に出す）")
def _():
    C.PART1[0]["items"][1]["en"] = first1()["en"]
    C.PART1[0]["items"][1]["dsl"] = first1()["dsl"]


@case("id の重複")
def _():
    C.PART1[0]["items"][1]["id"] = first1()["id"]


@case("採点ポイントが足りない（第3部）")
def _():
    first3()["points"] = first3()["points"][:1]


@case("notes が足りない")
def _():
    first1()["notes"] = first1()["notes"][:1]


@case("構文カテゴリが割り当て表のプールに無い")
def _():
    first1()["syn"] = "cleft"


@case("割り当て表に宣言した構文が出題されていない")
def _():
    # ★「入れたつもりで入っていない」を捕まえる検査。宣言だけ残して中身を差し替える。
    C.SYN_POOL["1A"].append("negative-inversion")
    return lambda: C.SYN_POOL["1A"].remove("negative-inversion")


@case("第3部の解説が丸数字で位置を指している（丸数字は第1部にしか刷られない）")
def _():
    first3()["notes"][0] = "②の位置にある動詞が主節の V である。" + first3()["notes"][0]


@case("同じ名詞句を主語にした問題が2問ある")
def _():
    a, b = C.PART1[0]["items"][0], C.PART1[0]["items"][1]
    head = a["dsl"].split("}")[0] + "}"
    b["dsl"] = head + b["dsl"][b["dsl"].index("}") + 1:]
    b["en"] = None
    from layout import parse, plain_text
    b["en"] = plain_text(parse(b["dsl"]))


@case("絵文字の混入（PDF で豆腐になる）")
def _():
    first1()["ja"] = "😀 " + first1()["ja"]


@case("答えの先出し（解説を設問文に混ぜて問題編に印字させる）")
def _():
    C.PART2[0]["q"] = C.PART2[0]["q"] + "　" + C.PART2[0]["exp"]


@case("第3部の英文が問題編に刷られていない（刷り漏れ）")
def _():
    # ★組版側を壊す。原稿は正しいのに紙に出ない、という一番気づけない事故を再現する。
    orig = build.render_blank
    build.render_blank = lambda *a, **k: ""
    return lambda: setattr(build, "render_blank", orig)


@case("答えの入った解答欄が問題編に刷られる（組版の取り違え）")
def _():
    orig = build.slot_table
    build.slot_table = lambda segs, answers=None: orig(segs, [lb for lb, _t, _u in segs])
    return lambda: setattr(build, "slot_table", orig)


@case("第3部の英文が短すぎる（関関同立の 1 文になっていない）")
def _():
    it = first3()
    it["dsl"] = "{S:The plan} {V:failed} ."
    it["en"] = "The plan failed."
    it["pat"] = "第1文型（SV）"


def main():
    base = snapshot()
    code, errs = run_check()
    if code or errs:
        print("!! ベースラインが既に NG。先に本体を直すこと。")
        for e in errs:
            print("  ", e)
        sys.exit(1)
    print("baseline: ALL CHECKS PASSED\n")

    missed = 0
    for name, mutate in CASES:
        restore(base)
        undo = mutate()
        code, errs = run_check()
        if undo:
            undo()
        caught = bool(code) and bool(errs)
        print(f"[{'検出' if caught else '素通り'}] {name}")
        if caught:
            print(f"         -> {errs[0][:120]}")
        else:
            missed += 1
    restore(base)

    # parse() の孤立 '}' がハングせず ValueError になること（無限ループの再発防止）
    from layout import parse

    def on_alarm(*_):
        raise TimeoutError("parse がハングした")

    signal.signal(signal.SIGALRM, on_alarm)
    signal.alarm(3)
    try:
        parse("{S:A} {V:b} } {O:c} .")
        print("[素通り] 孤立した '}' が例外にならない")
        missed += 1
    except TimeoutError:
        print("[素通り] 孤立した '}' で parse が無限ループ")
        missed += 1
    except ValueError:
        print("[検出] 孤立した '}' -> ValueError")
    finally:
        signal.alarm(0)

    # 問題編がそもそも組めること（組版の例外で検査が空回りしていないこと）
    page = build.build_mondai()
    if len(page) < 4000:
        print("[素通り] 問題編の組版が短すぎる（中身が出ていない）")
        missed += 1
    else:
        print(f"[検出] 問題編の組版 OK（{len(page)} 文字）")

    print(f"\n素通り {missed} 件 / 全 {len(CASES) + 2} ケース")
    sys.exit(1 if missed else 0)


if __name__ == "__main__":
    main()
