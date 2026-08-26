#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「数学I 二次関数 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 -m pip install sympy          # 正解の独立再計算に要る
    python3 scripts/book_exam/materials/sugaku_nijikansu1/build_sugaku_nijikansu1.py

出力 (どちらも**コミットする**): 数学I_二次関数_第1集.json / 数学I_二次関数_第1集_問題.pdf
作法は docs/kamitest-manual/README.md (共通編) と sugaku.md。

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _book_build.py が同時生成する。
★ **正解を手入力しない** (CLAUDE.md)。各問は
      solve : 正解を sympy で独立に計算する関数
      vals  : 選択肢 4 つの sympy 値 (**表示はここから生成する**ので表示と値がずれない)
  を持ち、verify_math() が
      ① vals[answer-1] が solve() と一致するか
      ② 選択肢どうしが同値でないか (別表記の同値が混じると正解が 2 つになる)
  を再計算で確かめる。
★ **page を書いていない**。刷り上がりから実ページを読み取って
  JSON に入れる (選択肢の組版が変われば行数も変わるため)。
★ 正解の位置は 1:3 / 2:2 / 3:3 / 4:2 (第1問から 3,1,4,2,1,3,2,4,1,3)。設問を足したら配り直す。
★ 相互チェック (CLAUDE.md 2026-08-16):
  ① _book_build.run() が刷り上がり PDF を読み返して全問・全選択肢とページを逆照合し、
     生の LaTeX が残っていないこと (= KaTeX が全部描けたこと) を確かめる
  ② verify() + verify_math() + check_grammar_books.py
  ③ 正解の一意性を敵対的に再読 — 定義域つきの最大最小は「頂点が定義域に入るか」で
     割れるので、入る問 (第5問) と端で決まる問を混ぜ、いずれも整数値で一意に決まる形に限った。

取り込み: python3 scripts/book_exam/import_books.py \
    scripts/book_exam/materials/sugaku_nijikansu1 \
    --pdf-dir scripts/book_exam/materials/sugaku_nijikansu1 --dry-run
"""
import os
import sys

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _book_build as B  # noqa: E402

x, k, a, b, c = sp.symbols("x k a b c")

META = {
    "stem": "数学I_二次関数_第1集",
    "title": "数学I 二次関数 演習 第1集",
    "subject": "math",
    "subject_name": "数学",
    "level": "標準",
    "time_limit_min": 25,
    "intro": "答えはすべて整数になります。計算用の余白はこの冊子に直接書き込んで"
             "かまいません。解答は別画面の答案に、選択肢の番号で入力してください。",
}

# --- 各問: solve() は正解を独立に計算する。vals から選択肢の表示を作る -------
RAW = [
    dict(
        number=1, points=2, unit_tag="SUGAKU1A-HEIHOU",
        stem="2 次関数 $y = x^{2} - 4x + 1$ の最小値を求めよ。",
        solve=lambda: sp.minimum(x**2 - 4*x + 1, x),
        vals=[1, 3, -3, 2], answer=3,
        explanation=(
            "【方針】平方完成して頂点を出す。下に凸なので頂点の y 座標が最小値。\n"
            "【立式】y = x^2 - 4x + 1 = (x - 2)^2 - 4 + 1\n"
            "【計算】(x - 2)^2 - 3。頂点は (2, -3)。x^2 の係数が正なので下に凸。\n"
            "【答え】最小値 -3 (このとき x = 2)\n"
            "【誤答の切り方】\n"
            "1. 1 — 定数項をそのまま最小値にした。x = 0 のときの値でしかない。\n"
            "2. 3 — 平方完成で引く 3 の符号を落とした。\n"
            "4. 2 — 頂点の x 座標。聞かれているのは y の最小値。\n"
            "別解: 軸 x = -(-4)/2 = 2 を代入しても 4 - 8 + 1 = -3。"),
    ),
    dict(
        number=2, points=2, unit_tag="SUGAKU1A-JOUTOTSU",
        stem="2 次関数 $y = -2x^{2} + 8x - 5$ の最大値を求めよ。",
        solve=lambda: sp.maximum(-2*x**2 + 8*x - 5, x),
        vals=[3, -5, 2, -3], answer=1,
        explanation=(
            "【方針】x^2 の係数が負なので上に凸。頂点の y 座標が最大値。\n"
            "【立式】y = -2(x^2 - 4x) - 5 = -2{(x - 2)^2 - 4} - 5\n"
            "【計算】-2(x - 2)^2 + 8 - 5 = -2(x - 2)^2 + 3。頂点は (2, 3)。\n"
            "【答え】最大値 3 (このとき x = 2)\n"
            "【誤答の切り方】\n"
            "2. -5 — 定数項をそのまま答えにした。x = 0 のときの値でしかない。\n"
            "3. 2 — 頂点の x 座標。聞かれているのは y の最大値。\n"
            "4. -3 — -2 でくくるときに符号を追い切れなかった形。\n"
            "上に凸か下に凸かは x^2 の係数の符号だけで決まる。最初に見ること。"),
    ),
    dict(
        number=3, points=2, unit_tag="SUGAKU1A-HANBETSU",
        stem="2 次関数 $y = x^{2} - 6x + k$ のグラフが $x$ 軸に接するとき、"
             "定数 $k$ の値を求めよ。",
        solve=lambda: max(sp.solve(sp.discriminant(x**2 - 6*x + k, x), k)),
        vals=[3, 6, -9, 9], answer=4,
        explanation=(
            "【方針】x 軸に接する = x^2 - 6x + k = 0 が重解をもつ = 判別式が 0。\n"
            "【立式】D = (-6)^2 - 4 · 1 · k = 0\n"
            "【計算】36 - 4k = 0 より 4k = 36、k = 9。\n"
            "【答え】k = 9 (このとき y = (x - 3)^2 で、頂点 (3, 0) が x 軸上)\n"
            "【誤答の切り方】\n"
            "1. 3 — 頂点の x 座標。k ではない。\n"
            "2. 6 — x の係数の絶対値をそのまま答えにした。\n"
            "3. -9 — 判別式の移項で符号を取り違えた。k = 9 でないと接しない。\n"
            "「接する」は交点 1 個。交点 2 個なら D > 0、交点なしなら D < 0。"),
    ),
    dict(
        number=4, points=2, unit_tag="SUGAKU1A-HEIKOU",
        stem="2 次関数 $y = x^{2} + 2x + 3$ のグラフを $x$ 軸方向に 3 だけ平行移動した"
             "放物線の頂点の $x$ 座標を求めよ。",
        solve=lambda: sp.solve(sp.diff(x**2 + 2*x + 3, x), x)[0] + 3,
        vals=[-4, 2, -1, 4], answer=2,
        explanation=(
            "【方針】もとの頂点を出してから、x 座標だけ 3 動かす。\n"
            "【立式】y = x^2 + 2x + 3 = (x + 1)^2 + 2。もとの頂点は (-1, 2)。\n"
            "【計算】x 軸方向に 3 → x 座標は -1 + 3 = 2。y 座標は 2 のまま。\n"
            "【答え】2\n"
            "【誤答の切り方】\n"
            "1. -4 — 3 を足すところを引いた。x 軸方向の移動は足す。\n"
            "3. -1 — もとの頂点の x 座標。移動させていない。\n"
            "4. 4 — 平方完成前の 2x の 2 を頂点の x 座標と取り違えた形。\n"
            "式で言うと y = (x - 3)^2 + 2(x - 3) + 3 と置き換えるのと同じこと。"),
    ),
    dict(
        number=5, points=2, unit_tag="SUGAKU1A-TEIGIIKI",
        stem="$1 \\leqq x \\leqq 4$ における 2 次関数 $y = -x^{2} + 6x - 5$ の"
             "最大値を求めよ。",
        solve=lambda: sp.maximum(-x**2 + 6*x - 5, x, sp.Interval(1, 4)),
        vals=[4, 3, 0, -5], answer=1,
        explanation=(
            "【方針】上に凸。軸が定義域の中にあるかどうかで場合が分かれる。\n"
            "【立式】y = -(x^2 - 6x) - 5 = -(x - 3)^2 + 9 - 5 = -(x - 3)^2 + 4\n"
            "【計算】軸は x = 3 で、1 以上 4 以下の中にある。だから頂点で最大。\n"
            "【答え】最大値 4 (このとき x = 3)\n"
            "【誤答の切り方】\n"
            "2. 3 — 軸の x 座標。聞かれているのは y の最大値。\n"
            "3. 0 — 左端 x = 1 の値。上に凸で軸が中にあるので端は最大にならない。\n"
            "4. -5 — 定数項。x = 0 のときの値で、そもそも定義域の外。\n"
            "軸が定義域の外なら端が最大になる。まず軸の位置を確かめること。"),
    ),
    dict(
        number=6, points=2, unit_tag="SUGAKU1A-SAISHOU",
        stem="$0 \\leqq x \\leqq 3$ における 2 次関数 $y = x^{2} - 2x + 2$ の"
             "最小値を求めよ。",
        solve=lambda: sp.minimum(x**2 - 2*x + 2, x, sp.Interval(0, 3)),
        vals=[2, 5, 1, -1], answer=3,
        explanation=(
            "【方針】下に凸。軸が定義域の中にあるかを見る。\n"
            "【立式】y = (x - 1)^2 - 1 + 2 = (x - 1)^2 + 1\n"
            "【計算】軸は x = 1 で 0 以上 3 以下の中にある。下に凸なので頂点で最小。\n"
            "【答え】最小値 1 (このとき x = 1)\n"
            "【誤答の切り方】\n"
            "1. 2 — 左端 x = 0 の値。軸が定義域の中にあるので端は最小にならない。\n"
            "2. 5 — 右端 x = 3 の値。これは同じ範囲での最大値。\n"
            "4. -1 — 平方完成の途中の -1 をそのまま答えにした。+2 を足し忘れている。\n"
            "同じ範囲での最大値は 5 (x = 3)。最大と最小を取り違えないこと。"),
    ),
    dict(
        number=7, points=2, unit_tag="SUGAKU1A-FUTOUSHIKI",
        stem="2 次不等式 $x^{2} - 5x - 6 < 0$ を満たす整数 $x$ は全部で何個あるか。",
        solve=lambda: len([i for i in range(-30, 30) if i**2 - 5*i - 6 < 0]),
        vals=[5, 6, 7, 8], answer=2,
        explanation=(
            "【方針】因数分解して解の範囲を出し、その中の整数を数える。\n"
            "【立式】x^2 - 5x - 6 = (x - 6)(x + 1) < 0\n"
            "【計算】解は -1 < x < 6。等号が無いので -1 と 6 は入らない。"
            "中の整数は 0, 1, 2, 3, 4, 5 の 6 個。\n"
            "【答え】6 個\n"
            "【誤答の切り方】\n"
            "1. 5 — 0 を数え忘れた。0 も整数。\n"
            "3. 7 — 端の -1 か 6 の一方を入れてしまった。不等号に等号は無い。\n"
            "4. 8 — 両端を入れてしまった。それは x^2 - 5x - 6 ≦ 0 の答え。\n"
            "下に凸の放物線が負になるのは 2 解の間。不等号の向きを毎回確かめること。"),
    ),
    dict(
        number=8, points=2, unit_tag="SUGAKU1A-OUYOU",
        stem="周の長さが 20 の長方形のうち、面積が最大になるものの面積を求めよ。",
        solve=lambda: sp.maximum(x * (10 - x), x),
        vals=[20, 100, 10, 25], answer=4,
        explanation=(
            "【方針】縦を x と置いて、面積を x の 2 次関数にする。\n"
            "【立式】周が 20 なので 縦 + 横 = 10。横は 10 - x。"
            "面積 S = x(10 - x) で、x のとりうる値は 0 < x < 10。\n"
            "【計算】S = -x^2 + 10x = -(x - 5)^2 + 25。軸 x = 5 は 0 < x < 10 の中にあり、"
            "上に凸なので x = 5 で最大。\n"
            "【答え】面積の最大値 25 (縦も横も 5 の正方形のとき)\n"
            "【誤答の切り方】\n"
            "1. 20 — 周の長さをそのまま面積にした。単位が違う量。\n"
            "2. 100 — 縦も横も 10 とした。それでは周が 40 になり条件に合わない。\n"
            "3. 10 — 縦と横の和。面積ではない。\n"
            "「周が一定なら正方形で面積最大」は覚えておくと検算に使える。"),
    ),
    dict(
        number=9, points=2, unit_tag="SUGAKU1A-KOTEN",
        stem="2 次関数 $y = x^{2} - 3x - 4$ のグラフが $x$ 軸から切り取る線分の長さを"
             "求めよ。",
        solve=lambda: (lambda r: max(r) - min(r))(sp.solve(x**2 - 3*x - 4, x)),
        vals=[5, 3, 4, -4], answer=1,
        explanation=(
            "【方針】x 軸との交点を出し、その 2 点の距離を取る。\n"
            "【立式】x^2 - 3x - 4 = (x - 4)(x + 1) = 0\n"
            "【計算】交点は x = -1 と x = 4。長さは 4 - (-1) = 5。\n"
            "【答え】5\n"
            "【誤答の切り方】\n"
            "2. 3 — 2 解の和。x の係数の符号を変えた値でしかない。\n"
            "3. 4 — 大きい方の解。原点からの距離であって、2 交点の間の長さではない。\n"
            "4. -4 — 2 解の積 (定数項)。長さは差であって積ではないし、負にもならない。\n"
            "一般に長さは √(b^2 - 4ac) / |a|。ここでは √(9 + 16) / 1 = 5 で一致する。"),
    ),
    dict(
        number=10, points=2, unit_tag="SUGAKU1A-KETTEI",
        stem="2 次関数 $y = ax^{2} + bx + c$ のグラフが 3 点 $(0,\\ 1)$, $(1,\\ 0)$, "
             "$(2,\\ 3)$ を通るとき、$a$ の値を求めよ。",
        solve=lambda: sp.solve([c - 1, a + b + c, 4*a + 2*b + c - 3],
                               [a, b, c])[a],
        vals=[1, -2, 2, 3], answer=3,
        explanation=(
            "【方針】3 点を代入して 3 つの式を作り、連立して a を出す。\n"
            "【立式】(0,1) より c = 1。(1,0) より a + b + c = 0。"
            "(2,3) より 4a + 2b + c = 3。\n"
            "【計算】c = 1 を入れて a + b = -1、4a + 2b = 2 すなわち 2a + b = 1。"
            "辺々引くと a = 2。このとき b = -3。\n"
            "【答え】a = 2 (求める式は y = 2x^2 - 3x + 1)\n"
            "【誤答の切り方】\n"
            "1. 1 — c の値。聞かれているのは a。\n"
            "2. -2 — 引く向きを逆にした。2a + b から a + b を引く。\n"
            "4. 3 — b = -3 の符号を落とした値。a ではない。\n"
            "求めた式に 3 点を戻して確かめる習慣をつけること。"),
    ),
]


def to_question(r):
    """vals から選択肢の表示を作る。**表示と値がずれない**のが要点。"""
    q = {kk: vv for kk, vv in r.items() if kk not in ("solve", "vals")}
    q["choices"] = [f"${sp.latex(sp.sympify(v))}$" for v in r["vals"]]
    q["choices_plain"] = [str(sp.sympify(v)) for v in r["vals"]]
    return q


QUESTIONS = [to_question(r) for r in RAW]


def verify_math(meta, questions):
    """正解と誤答を sympy で独立に確かめる (手入力の正解を信じない)。"""
    errs = []
    for r in RAW:
        at = f"第{r['number']}問"
        vals = [sp.sympify(v) for v in r["vals"]]
        try:
            got = sp.sympify(r["solve"]())
        except Exception as e:                       # noqa: BLE001
            errs.append(f"{at}: 正解の再計算が失敗した ({e})")
            continue
        want = vals[r["answer"] - 1]
        if sp.simplify(want - got) != 0:
            errs.append(f"{at}: 正解が再計算と合わない "
                        f"(選択肢 {r['answer']} = {want} / 再計算 = {got})")
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                if sp.simplify(vals[i] - vals[j]) == 0:
                    errs.append(f"{at}: 選択肢 {i + 1} と {j + 1} が同値 "
                                f"({vals[i]})。正解が 2 つになる")
    return errs


if __name__ == "__main__":
    sys.exit(B.run(HERE, META, QUESTIONS, verify_extra=verify_math))
