#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「数学I 二次関数 共通テスト型 第1集」— 問題 PDF と取り込み JSON。

    python3 scripts/book_exam/materials/sugaku_kyotsu1/build_sugaku_kyotsu1.py

出力 (どちらも**コミットする**): 数学I_二次関数_共通テスト型_第1集.json / 同_問題.pdf
作法は docs/kamitest-manual/README.md (共通編) と sugaku.md。

■ これは「単元別ドリル」ではなく**誘導形式**の 1 冊
  ・場面設定 (会話文) を passages に置き、そこから 8 問が一続きに誘導される
  ・前問の結果を次問で使う (辺の長さ → 面積の式 → 定義域 → 平方完成 → 最大 →
    条件を満たす範囲 → 条件を変えた転用)
  ★ 神テストの画面には大問の枠が無い (第1問〜第8問が並ぶだけ) が、
    冊子側で 1 つの大問として組めば誘導は成立する。

■ ★ できないこと — 共通テストの**マーク欄**は入らない
  本番は「アに 5、イに −3」のように 1 桁ずつマークする。神テストは
  ・記述 (short) の正解が数字だけだと取り込みが弾く
  ・選択式 (choice) は 1〜10 の番号で、0 や負号を表現できない
  ので、マーク欄はそのまま載せられない (sugaku.md §1)。
  **誘導の中身は本番どおり、解答形式だけ 4 択**にしてある。

★ 正解を手入力しない。vals (sympy) を solve() の再計算と照合し、選択肢どうしが
  同値でないことも確かめる (verify_math)。
★ 第1集と違い、**選択肢の LaTeX は手書き**。sympy の latex() は
  「200 - 2(x-10)^2」のように項を並べ替えるので、平方完成の設問だけ
  正解の見た目が他と揃わず**形が答えのヒントになる**。表示は手で揃え、
  値は sympy が独立に確かめる。
★ 正解の位置は 1:2 / 2:2 / 3:2 / 4:2 (8 問でちょうど 2 回ずつ)。
★ 相互チェック: ① 刷り上がり PDF の逆照合 ② verify() + verify_math()
  ③ 正解の一意性の敵対的再読 — 誘導形式は前問の誤りが後ろに伝播するので、
     各問が**単独でも解ける**ように、必要な値は設問文にも書いた。

取り込み: python3 scripts/book_exam/import_books.py \
    scripts/book_exam/materials/sugaku_kyotsu1 \
    --pdf-dir scripts/book_exam/materials/sugaku_kyotsu1 --dry-run
"""
import os
import sys

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _book_build as B  # noqa: E402

x = sp.symbols("x")

S = sp.expand(x * (40 - 2 * x))                       # 面積
DOM = (sp.solve_univariate_inequality(x > 0, x, relational=False)
       .intersect(sp.solve_univariate_inequality(40 - 2 * x > 0, x,
                                                 relational=False)))
IV150 = sp.solve_univariate_inequality(S >= 150, x, relational=False)


# ★ 範囲も数式として組む。設問文の x は斜体なので、選択肢だけ立体だと
#   同じ文字が 2 つの字形で出てしまう (本番の組版では起こらない)。
def op_tex(a, b):
    return f"${a} < x < {b}$"


def cl_tex(a, b):
    return f"${a} \\leqq x \\leqq {b}$"


def op(iv):
    return f"{iv.start} < x < {iv.end}"


def cl(iv):
    return f"{iv.start} ≦ x ≦ {iv.end}"


KAIWA = (
    "<p>花子さんと太郎さんは、校庭に長方形の花壇をつくる計画を立てている。</p>"
    "<p><b>花子</b>「校舎の壁を花壇の 1 辺として使えば、ロープで囲うのは"
    "残りの 3 辺だけでいいね。」<br>"
    "<b>太郎</b>「ロープは全部で 40 m あるよ。壁に垂直な辺の長さを $x$ m と"
    "おいてみよう。」<br>"
    "<b>花子</b>「垂直な辺は 2 本あるから、壁に平行な辺の長さは $x$ で表せるね。」<br>"
    "<b>太郎</b>「そうすると花壇の面積 $S$ は $x$ の 2 次関数になる。"
    "いちばん広くなるときの $x$ を求めよう。」<br>"
    "<b>花子</b>「面積を 150 m² 以上にしたいときの $x$ の範囲も知りたいな。」</p>"
    "<div class=\"note\">以下、ロープはたるみなく使い、壁は十分に長いものとする。"
    "長さの単位は m、面積の単位は m² とする。</div>")

META = {
    "stem": "数学I_二次関数_共通テスト型_第1集",
    "title": "数学I 二次関数 共通テスト型 第1集",
    "subject": "math",
    "subject_name": "数学",
    "level": "標準",
    "time_limit_min": 20,
    "intro": "1 ページ目の会話を読み、第1問から順に答えてください。"
             "前の問いの結果を次の問いで使います。"
             "解答は別画面の答案に入力してください。",
    "passages": [{"page": 1, "title": "第1問　花壇をつくる（配点 16）",
                  "html": KAIWA}],
}


def m(hoshin, rikishiki, keisan, kotae, ngs):
    return ("【方針】" + hoshin + "\n【立式】" + rikishiki + "\n【計算】" + keisan
            + "\n【答え】" + kotae + "\n【誤答の切り方】\n" + "\n".join(ngs))


RAW = [
    dict(number=1, page=1, points=2, unit_tag="KYOTSU1A-SHIKI",
         stem="壁に平行な辺の長さを $x$ を用いて表したものとして正しいものを"
              "1 つ選べ。ロープの長さは 40 m である。",
         tex=["$40 - x$", "$40 - 2x$", "$20 - 2x$", "$20 - x$"],
         plain=["40 - x", "40 - 2x", "20 - 2x", "20 - x"],
         vals=[40 - x, 40 - 2 * x, 20 - 2 * x, 20 - x], answer=2,
         solve=lambda: 40 - 2 * x,
         explanation=m(
             "ロープで囲うのは 3 辺だけ。垂直な辺 2 本ぶんを引いた残りが平行な辺。",
             "(平行な辺) = 40 - (垂直な辺) × 2",
             "= 40 - 2x",
             "40 - 2x",
             ["1. 40 - x — 垂直な辺を 1 本しか引いていない。壁に垂直な辺は 2 本ある。",
              "3. 20 - 2x — ロープの長さを先に半分にしている。"
              "長方形の周の公式と混同した形。",
              "4. 20 - x — 上の 2 つの誤りが重なった形。"])),

    dict(number=2, page=1, points=2, unit_tag="KYOTSU1A-MENSEKI",
         stem="花壇の面積 $S$ を $x$ を用いて表したものとして正しいものを 1 つ選べ。",
         tex=["$S = -x^{2} + 40x$", "$S = 2x^{2} - 40x$",
              "$S = -2x^{2} + 20x$", "$S = -2x^{2} + 40x$"],
         plain=["S = -x^2 + 40x", "S = 2x^2 - 40x",
                "S = -2x^2 + 20x", "S = -2x^2 + 40x"],
         vals=[-x**2 + 40 * x, 2 * x**2 - 40 * x, -2 * x**2 + 20 * x, S],
         answer=4, solve=lambda: sp.expand(x * (40 - 2 * x)),
         explanation=m(
             "(縦) × (横)。第1問で出した平行な辺を使う。",
             "S = x(40 - 2x)",
             "S = 40x - 2x^2 = -2x^2 + 40x",
             "S = -2x^2 + 40x",
             ["1. S = -x^2 + 40x — x に掛ける 2x の 2 を落としている。",
              "2. S = 2x^2 - 40x — 展開の符号が全部逆。x^2 の係数が正だと"
              "下に凸になり、面積に最大値が無くなる。",
              "3. S = -2x^2 + 20x — 第1問で 20 - 2x を選んだときの式。"])),

    dict(number=3, page=2, points=2, unit_tag="KYOTSU1A-TEIGIIKI",
         stem="$x$ のとりうる値の範囲として正しいものを 1 つ選べ。"
              "ロープの長さは 40 m である。",
         tex=[op_tex(DOM.start, DOM.end), op_tex(0, 40), op_tex(0, 10),
              cl_tex(0, 20)],
         plain=[op(DOM), "0 < x < 40", "0 < x < 10", "0 ≦ x ≦ 20"],
         vals=[DOM, "0 < x < 40", "0 < x < 10", "0 ≦ x ≦ 20"], answer=1,
         solve=lambda: DOM,
         explanation=m(
             "長さは正でなければならない。垂直な辺と平行な辺の両方に条件が付く。",
             "x > 0 かつ 40 - 2x > 0",
             "2 つ目から x < 20。合わせて 0 < x < 20。",
             "0 < x < 20",
             ["2. 0 < x < 40 — 平行な辺が負になる範囲まで入っている。"
              "x = 30 では 40 - 2x = -20 で長さにならない。",
              "3. 0 < x < 10 — 上限を半分にしている。x = 15 でも花壇はつくれる。",
              "4. 0 ≦ x ≦ 20 — 端では辺の長さが 0 になり、長方形にならない。"
              "等号は入らない。"])),

    dict(number=4, page=2, points=2, unit_tag="KYOTSU1A-HEIHOU",
         stem="第2問の $S$ を平方完成したものとして正しいものを 1 つ選べ。",
         tex=["$-2(x - 10)^{2} + 100$", "$-2(x - 20)^{2} + 200$",
              "$-2(x - 10)^{2} + 200$", "$2(x - 10)^{2} - 200$"],
         plain=["-2(x - 10)^2 + 100", "-2(x - 20)^2 + 200",
                "-2(x - 10)^2 + 200", "2(x - 10)^2 - 200"],
         vals=[-2 * (x - 10)**2 + 100, -2 * (x - 20)**2 + 200,
               -2 * (x - 10)**2 + 200, 2 * (x - 10)**2 - 200],
         answer=3, solve=lambda: sp.expand(x * (40 - 2 * x)),
         explanation=m(
             "x^2 の係数 -2 でくくってから、かっこの中を平方完成する。",
             "S = -2x^2 + 40x = -2(x^2 - 20x)",
             "= -2{(x - 10)^2 - 100} = -2(x - 10)^2 + 200",
             "S = -2(x - 10)^2 + 200 (頂点は (10, 200))",
             ["1. -2(x - 10)^2 + 100 — くくり出した -2 を戻すのを忘れている。"
              "-2 × (-100) は +200。",
              "2. -2(x - 20)^2 + 200 — かっこの中を半分にしていない。"
              "x^2 - 20x の平方完成は (x - 10)^2。",
              "4. 2(x - 10)^2 - 200 — 符号が全部逆。展開すると 2x^2 - 40x になり、"
              "第2問の S と一致しない。"])),

    dict(number=5, page=2, points=2, unit_tag="KYOTSU1A-SAIDAI",
         stem="面積 $S$ が最大になるときの $x$ の値を 1 つ選べ。",
         tex=["$5$", "$10$", "$15$", "$20$"],
         plain=["5", "10", "15", "20"],
         vals=[5, 10, 15, 20], answer=2,
         solve=lambda: sp.solve(sp.diff(S, x), x)[0],
         explanation=m(
             "第4問の平方完成から頂点を読む。上に凸なので頂点で最大。",
             "S = -2(x - 10)^2 + 200",
             "軸は x = 10。これは第3問の範囲 0 < x < 20 の中にあるので、"
             "そのまま最大を与える。",
             "x = 10",
             ["1. 5 — 第7問で出てくる境目の値。最大を与える x ではない。",
              "3. 15 — 同じく第7問の境目。左右対称の反対側。",
              "4. 20 — 定義域の端で、しかも範囲に含まれない。"
              "ここでは平行な辺が 0 になる。"])),

    dict(number=6, page=3, points=2, unit_tag="KYOTSU1A-SAIDAICHI",
         stem="面積 $S$ の最大値を 1 つ選べ。単位は $\\mathrm{m}^{2}$ である。",
         tex=["$200$", "$100$", "$150$", "$400$"],
         plain=["200", "100", "150", "400"],
         vals=[200, 100, 150, 400], answer=1,
         solve=lambda: sp.maximum(S, x, DOM),
         explanation=m(
             "第5問で求めた x を S に入れる。平方完成の形からも直接読める。",
             "S = -2(x - 10)^2 + 200 に x = 10 を代入",
             "S = -2 × 0 + 200 = 200",
             "最大値 200 (このとき縦 10、横 20 の長方形)",
             ["2. 100 — 第4問で定数項を 100 と誤った場合の値。",
              "3. 150 — 第7問で条件として出てくる値。最大値ではない。",
              "4. 400 — 縦横をどちらも 20 としたときの面積。"
              "ロープが 40 m では足りない。"])),

    dict(number=7, page=3, points=2, unit_tag="KYOTSU1A-FUTOUSHIKI",
         stem="面積 $S$ が 150 m² 以上になる $x$ の範囲として正しいものを 1 つ選べ。",
         tex=["$0 < x \\leqq 5$", cl_tex(10, 15), op_tex(5, 10),
              cl_tex(IV150.start, IV150.end)],
         plain=["0 < x ≦ 5", "10 ≦ x ≦ 15", "5 < x < 10", cl(IV150)],
         vals=["0 < x ≦ 5", "10 ≦ x ≦ 15", "5 < x < 10", IV150], answer=4,
         solve=lambda: IV150,
         explanation=m(
             "S ≧ 150 を 2 次不等式にして解く。",
             "-2x^2 + 40x ≧ 150",
             "両辺を -2 で割ると不等号の向きが変わり x^2 - 20x + 75 ≦ 0。"
             "因数分解して (x - 5)(x - 15) ≦ 0 より 5 ≦ x ≦ 15。"
             "これは第3問の 0 < x < 20 の中に収まっている。",
             "5 ≦ x ≦ 15",
             ["1. 0 < x ≦ 5 — 上に凸の放物線が 150 以上になるのは 2 解の**間**。"
              "外側ではない。",
              "2. 10 ≦ x ≦ 15 — 軸 x = 10 から右だけを取っている。"
              "左右対称なので 5 から始まる。",
              "3. 5 < x < 10 — 等号が落ち、しかも右半分が抜けている。"])),

    dict(number=8, page=3, points=2, unit_tag="KYOTSU1A-TENYOU",
         stem="ロープの長さを 40 m から 60 m に変えた。ほかの条件は同じとするとき、"
              "花壇の面積の最大値を 1 つ選べ。単位は $\\mathrm{m}^{2}$ である。",
         tex=["$300$", "$400$", "$450$", "$900$"],
         plain=["300", "400", "450", "900"],
         vals=[300, 400, 450, 900], answer=3,
         solve=lambda: sp.maximum(x * (60 - 2 * x), x),
         explanation=m(
             "同じ手順を数だけ変えて繰り返す。誘導の型をそのまま使う。",
             "平行な辺は 60 - 2x、面積は S = x(60 - 2x) = -2x^2 + 60x",
             "-2(x - 15)^2 + 450。軸 x = 15 は 0 < x < 30 の中にあるので"
             "そこで最大。",
             "最大値 450 (このとき縦 15、横 30)",
             ["1. 300 — 縦 10、横 30 としたときの面積。最大ではない。",
              "2. 400 — ロープが 40 m のときの値 200 を 2 倍しただけ。"
              "面積は長さの 2 乗で効くので比例しない。",
              "4. 900 — 一辺 30 の正方形の面積。3 辺で 60 m には収まらない。"])),
]


def to_q(r):
    q = {k: v for k, v in r.items() if k not in ("tex", "plain", "vals", "solve")}
    q["choices"] = list(r["tex"])
    q["choices_plain"] = list(r["plain"])
    return q


QUESTIONS = [to_q(r) for r in RAW]


def same(a, b):
    """式・集合・文字列のどれでも「同じか」を判定する。"""
    if isinstance(a, sp.Basic) and isinstance(b, sp.Basic):
        if isinstance(a, sp.Set) or isinstance(b, sp.Set):
            return a == b
        return sp.simplify(a - b) == 0
    return a == b


def verify_math(meta, questions):
    """正解と誤答を sympy で独立に確かめる (手入力の正解を信じない)。"""
    errs = []
    for r in RAW:
        at = f"第{r['number']}問"
        vals = r["vals"]
        if not (len(vals) == len(r["tex"]) == len(r["plain"])):
            errs.append(f"{at}: vals / tex / plain の数が揃っていない")
            continue
        try:
            got = r["solve"]()
        except Exception as e:                        # noqa: BLE001
            errs.append(f"{at}: 正解の再計算が失敗した ({e})")
            continue
        if not same(vals[r["answer"] - 1], got):
            errs.append(f"{at}: 正解が再計算と合わない "
                        f"(選択肢 {r['answer']} = {vals[r['answer'] - 1]} / "
                        f"再計算 = {got})")
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                if same(vals[i], vals[j]):
                    errs.append(f"{at}: 選択肢 {i + 1} と {j + 1} が同値 "
                                f"({vals[i]})。正解が 2 つになる")
    return errs


if __name__ == "__main__":
    sys.exit(B.run(HERE, META, QUESTIONS, verify_extra=verify_math))
