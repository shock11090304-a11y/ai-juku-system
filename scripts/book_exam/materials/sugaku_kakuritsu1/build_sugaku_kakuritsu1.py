#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「数学A 第3問 場合の数と確率 共通テスト本番相当 第1集」。

    python3 scripts/book_exam/materials/sugaku_kakuritsu1/build_sugaku_kakuritsu1.py

作法は docs/kamitest-manual/README.md (共通編) と sugaku.md。

■ なぜこの単元か
  数学の既存 3 冊はすべて 2 次関数 (sugaku_nijikansu1 / sugaku_kyotsu1 /
  sugaku_honban1)。重ならない単元として、共通テスト第3問にあたる
  「場合の数と確率」を選んだ。軸は**条件付き確率** — 受験生が最も落とす論点で、
  「引く順番で有利不利は変わるか」という判断まで含められる。

■ 本番相当の構成 (sugaku.md §6.5)
  ・会話文の場面設定を passages に置く
  ・誘導連鎖: 1 人目 → 2 人ぶん同時 → 2 人目 → 余事象 → 条件付き
  ・**判断の設問** (第7問「先に引いた方が有利」の当否)
  ・**転用** (第8〜10問: 戻す場合 / 3 人 / 当たりの本数を変える)

★ 正解を手入力しない。vals (sympy の Rational) を solve() の再計算と照合し、
  選択肢どうしが同値でないことも確かめる (verify_math)。
★ 選択肢の表示は sympy.latex(vals) から生成する。分数はどれも \\frac{a}{b} の形に
  そろうので、**見た目が答えのヒントにならない** (sugaku_honban1 で平方完成の
  並べ替えが問題になったのとは事情が違う)。
★ 解説の分数は「3/10」の形で書く。画面は素のテキストなので LaTeX は書けない。
★ ページは書いていない。刷り上がりから実ページを読み取って JSON に入れる。
★ 正解の位置は 1:3 / 2:2 / 3:3 / 4:2 (第1問から 3,1,4,2,1,3,2,4,1,3)。
★ 相互チェック: ① 刷り上がりの逆照合 ② verify() + verify_math()
  ③ 正解の一意性の敵対的再読 — 確率は「同じ値になる別の解釈」が生まれやすいので、
     誤答はすべて**別の設定なら正しい値**（戻す場合・条件を使わない場合など）に
     とどめ、この設問では一意に決まるようにした。

取り込み: python3 scripts/book_exam/import_books.py \
    scripts/book_exam/materials/sugaku_kakuritsu1 \
    --pdf-dir scripts/book_exam/materials/sugaku_kakuritsu1 --dry-run
"""
import os
import sys

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _book_build as B  # noqa: E402

R = sp.Rational
ATARI, TOTAL = 3, 10          # 当たり 3 本 / 全 10 本

P_TARO = R(ATARI, TOTAL)                                   # 太郎が当たる
P_BOTH = R(ATARI, TOTAL) * R(ATARI - 1, TOTAL - 1)         # 2 人とも当たる
P_X_O = R(TOTAL - ATARI, TOTAL) * R(ATARI, TOTAL - 1)      # 太郎× 花子○
P_HANAKO = P_BOTH + P_X_O                                  # 花子が当たる
P_ATLEAST = 1 - R(TOTAL - ATARI, TOTAL) * R(TOTAL - ATARI - 1, TOTAL - 1)
P_COND = P_BOTH / P_HANAKO                                 # P(太郎○ | 花子○)
P_REPL = R(ATARI, TOTAL) ** 2                              # 戻す場合の 2 人とも
P_THREE = (R(ATARI, TOTAL) * R(ATARI - 1, TOTAL - 1)
           * R(ATARI - 2, TOTAL - 2))                      # 3 人とも
ATARI4 = 4
P_AT4 = 1 - R(TOTAL - ATARI4, TOTAL) * R(TOTAL - ATARI4 - 1, TOTAL - 1)

KAIWA = (
    f"<p>文化祭の抽選会に、{TOTAL} 本のくじが用意されている。"
    f"そのうち {ATARI} 本が当たりで、残りははずれである。"
    "太郎さんと花子さんが、この順に 1 本ずつ引く。"
    "<b>引いたくじは箱に戻さない。</b></p>"
    "<p><b>太郎</b>「先に引いたほうが当たりやすい気がするな。」<br>"
    "<b>花子</b>「本当にそうかな。順番で変わるのかどうか、式で確かめてみよう。」<br>"
    "<b>太郎</b>「引いたくじを箱に戻す場合はどうなるのかも気になる。」<br>"
    "<b>花子</b>「当たりの本数を変えたらどうなるかも見てみたいね。」</p>"
    "<div class=\"note\">以下、どのくじも同じ確からしさで引かれるものとする。"
    "第8問以降で、くじを戻す場合や本数を変える場合を考える。"
    "答えはすべて既約分数で表してある。</div>")

META = {
    "stem": "数学A_第3問_場合の数と確率_本番相当_第1集",
    "title": "数学A 第3問 場合の数と確率 共通テスト本番相当 第1集",
    "subject": "math",
    "subject_name": "数学",
    "level": "共通テスト本番相当",
    "time_limit_min": 25,
    "intro": "1 ページ目の場面と会話を読み、第1問から順に答えてください。"
             "前の問いの結果を次の問いで使います。"
             "解答は別画面の答案に入力してください。",
    "passages": [{"title": "第3問　くじ引きと条件付き確率（配点 20）",
                  "html": KAIWA}],
}


def m(hoshin, rikishiki, keisan, kotae, ngs):
    return ("【方針】" + hoshin + "\n【立式】" + rikishiki + "\n【計算】" + keisan
            + "\n【答え】" + kotae + "\n【誤答の切り方】\n" + "\n".join(ngs))


RAW = [
    dict(number=1, points=2, unit_tag="KAKURITSU-KIHON",
         stem="太郎さんが当たりを引く確率を 1 つ選べ。",
         vals=[R(1, 10), R(3, 7), P_TARO, R(7, 10)], answer=3,
         solve=lambda: R(ATARI, TOTAL),
         explanation=m(
             "同じ確からしさで引くので、(当たりの本数) ÷ (全部の本数)。",
             "P = (当たりの本数) / (くじの本数)",
             "P = 3/10",
             "3/10",
             ["1. 1/10 — 当たりを 1 本と数えている。当たりは 3 本ある。",
              "2. 3/7 — 分母をはずれの本数 7 にしている。分母は全部の本数 10。",
              "4. 7/10 — **はずれる**確率。聞かれているのは当たる確率。"])),

    dict(number=2, points=2, unit_tag="KAKURITSU-DOUJI",
         stem="太郎さんと花子さんの 2 人とも当たりを引く確率を 1 つ選べ。",
         vals=[P_BOTH, R(9, 100), R(3, 50), R(1, 30)], answer=1,
         solve=lambda: R(ATARI, TOTAL) * R(ATARI - 1, TOTAL - 1),
         explanation=m(
             "続けて起こる 2 つのことなので、かけ算。"
             "★ くじを戻さないので、2 人目のときは本数が減っている。",
             "P = (太郎が当たる) × (太郎が当たったあと花子も当たる)",
             "P = 3/10 × 2/9 = 6/90 = 1/15。"
             "2 人目は、残り 9 本のうち当たりが 2 本。",
             "1/15",
             ["2. 9/100 — くじを**戻す**場合の確率 (3/10 × 3/10)。"
              "この設問では戻さない。",
              "3. 3/50 — 分母を 10 のままにした形 (3/10 × 2/10)。"
              "1 本引いた後は 9 本しかない。",
              "4. 1/30 — 2 人目の当たりを 1 本と数えた形 (3/10 × 1/9)。"
              "太郎が引いたあとも当たりは 2 本残っている。"])),

    dict(number=3, points=2, unit_tag="KAKURITSU-NIBANME",
         stem="花子さんが当たりを引く確率を 1 つ選べ。"
              "太郎さんが当たったかどうかは分からないものとする。",
         vals=[R(2, 9), P_X_O, P_BOTH, P_HANAKO], answer=4,
         solve=lambda: P_BOTH + P_X_O,
         explanation=m(
             "太郎が当たった場合とはずれた場合に分けて、両方を足す。",
             "P = (太郎○ かつ 花子○) + (太郎× かつ 花子○)",
             "P = 3/10 × 2/9 + 7/10 × 3/9 = 6/90 + 21/90 = 27/90 = 3/10",
             "3/10 — **第1問と同じ値**。引く順番によって当たる確率は変わらない。",
             ["1. 2/9 — 太郎が当たったと**分かっている**ときの確率。"
              "ここでは太郎の結果は分からない。",
              "2. 7/30 — 太郎がはずれた場合だけを数えている。"
              "太郎が当たった場合も足す必要がある。",
              "3. 1/15 — 2 人とも当たる確率 (第2問)。"])),

    dict(number=4, points=2, unit_tag="KAKURITSU-BUNKATSU",
         stem="太郎さんがはずれ、花子さんが当たりを引く確率を 1 つ選べ。",
         vals=[P_TARO, P_X_O, R(21, 100), P_BOTH], answer=2,
         solve=lambda: R(TOTAL - ATARI, TOTAL) * R(ATARI, TOTAL - 1),
         explanation=m(
             "順に起こることのかけ算。太郎がはずれても当たりの本数は減らない。",
             "P = (太郎がはずれる) × (そのあと花子が当たる)",
             "P = 7/10 × 3/9 = 21/90 = 7/30。"
             "太郎がはずれを引いたので、残り 9 本に当たりは 3 本のまま。",
             "7/30",
             ["1. 3/10 — 花子が当たる確率 (第3問)。太郎の結果を指定していない。",
              "3. 21/100 — くじを**戻す**場合 (7/10 × 3/10)。",
              "4. 1/15 — 2 人とも当たる確率 (第2問)。太郎がはずれる場合ではない。"])),

    dict(number=5, points=2, unit_tag="KAKURITSU-YOJISHOU",
         stem="少なくとも一方が当たりを引く確率を 1 つ選べ。",
         vals=[P_ATLEAST, R(3, 5), R(7, 15), P_BOTH], answer=1,
         solve=lambda: 1 - R(TOTAL - ATARI, TOTAL) * R(TOTAL - ATARI - 1,
                                                       TOTAL - 1),
         explanation=m(
             "「少なくとも一方」は余事象。**2 人ともはずれ**の確率を 1 から引く。",
             "P = 1 - (2 人ともはずれる確率)",
             "2 人ともはずれ = 7/10 × 6/9 = 42/90 = 7/15。"
             "P = 1 - 7/15 = 8/15",
             "8/15",
             ["2. 3/5 — 3/10 + 3/10 と単純に足した形。"
              "2 人とも当たる場合を二重に数えている。",
              "3. 7/15 — **2 人ともはずれる**確率。1 から引いていない。",
              "4. 1/15 — 2 人とも当たる確率 (第2問)。「少なくとも一方」ではない。"])),

    dict(number=6, points=2, unit_tag="KAKURITSU-JOUKEN",
         stem="花子さんが当たりを引いたことが分かっているとき、"
              "太郎さんも当たりを引いていた確率を 1 つ選べ。",
         vals=[P_BOTH, P_TARO, P_COND, R(1, 3)], answer=3,
         solve=lambda: P_BOTH / P_HANAKO,
         explanation=m(
             "条件付き確率。分かっていること (花子が当たり) を分母に置く。",
             "P(太郎○ | 花子○) = P(太郎○ かつ 花子○) / P(花子○)",
             "分子は第2問の 1/15、分母は第3問の 3/10。"
             "(1/15) ÷ (3/10) = (1/15) × (10/3) = 10/45 = 2/9",
             "2/9",
             ["1. 1/15 — 分子だけ。条件付きにするには花子が当たる確率で割る。",
              "2. 3/10 — 条件を使わずに、太郎が当たる確率をそのまま答えている。",
              "4. 1/3 — 3/9 と考えた形。1 本引かれたあとも当たりが 3 本残っている"
              "としているが、花子が当たっているので当たりは減っている。"])),

    dict(number=7, points=2, unit_tag="KAKURITSU-HANDAN",
         stem="太郎さんの「先に引いたほうが当たりやすい」という考えについて、"
              "正しく述べたものを 1 つ選べ。",
         vals=["saki", "onaji", "ato", "hikakufuka"], answer=2,
         solve=lambda: "onaji",
         tex=["正しい。先に引く太郎さんのほうが、当たる確率は高い。",
              "正しくない。引く順番によらず、当たる確率はどちらも 3/10 で等しい。",
              "正しくない。後に引く花子さんのほうが、当たる確率は高い。",
              "正しくない。太郎さんの結果によって花子さんの確率が変わるので、"
              "2 人の当たりやすさは比べられない。"],
         explanation=m(
             "計算ではなく結論の吟味。第1問と第3問の値を見比べる。",
             "太郎が当たる確率 (第1問) と、花子が当たる確率 (第3問) を比べる",
             "どちらも 3/10 で等しい。花子の確率は、太郎が当たった場合"
             "(6/90) とはずれた場合 (21/90) を足して 27/90 = 3/10 になる。",
             "正しくない。順番によらず等しい。",
             ["1. 正しい。先に引く太郎さんのほうが — 第3問で花子も 3/10 と"
              "出ている。有利不利は無い。",
              "3. 正しくない。後に引く花子さんのほうが — 向きが逆なだけで、"
              "やはり誤り。どちらも 3/10。",
              "4. 正しくない。太郎さんの結果によって花子さんの確率が変わるので "
              "— 太郎の結果を**知っている**なら確かに変わる (第6問) が、"
              "知らないまま比べるなら 3/10 で決まっている。"])),

    dict(number=8, points=2, unit_tag="KAKURITSU-FUKUGEN",
         stem="引いたくじを毎回箱に戻すことにした。ほかの条件は同じとするとき、"
              "2 人とも当たりを引く確率を 1 つ選べ。",
         vals=[P_BOTH, R(3, 50), P_TARO, P_REPL], answer=4,
         solve=lambda: R(ATARI, TOTAL) ** 2,
         explanation=m(
             "戻すので、2 人目のときも本数と当たりの数が最初と同じ。",
             "P = (3/10) × (3/10)",
             "P = 9/100",
             "9/100 — 戻さない場合の 1/15 (= 6/90) より大きい。"
             "戻すと当たりが減らないぶん、2 人とも当たりやすくなる。",
             ["1. 1/15 — 戻**さない**場合の確率 (第2問)。",
              "2. 3/50 — 3/10 × 2/10。戻したのに当たりだけ 1 本減らしている。",
              "3. 3/10 — 1 人ぶんの確率。2 人ぶんはかけ算する。"])),

    dict(number=9, points=2, unit_tag="KAKURITSU-SANNIN",
         stem="くじを戻さない場合に戻す。太郎さん、花子さん、次郎さんの 3 人が"
              "この順に 1 本ずつ引くとき、3 人とも当たりを引く確率を 1 つ選べ。",
         vals=[P_THREE, P_BOTH, R(27, 1000), R(1, 720)], answer=1,
         solve=lambda: (R(ATARI, TOTAL) * R(ATARI - 1, TOTAL - 1)
                        * R(ATARI - 2, TOTAL - 2)),
         explanation=m(
             "第2問の続き。1 人増えるごとに本数も当たりも 1 ずつ減る。",
             "P = 3/10 × 2/9 × 1/8",
             "P = 6/720 = 1/120。当たりは 3 本しかないので、"
             "4 人目は必ずはずれる。",
             "1/120",
             ["2. 1/15 — 2 人ぶんで止めている (第2問)。3 人目を掛けていない。",
              "3. 27/1000 — 毎回**戻す**場合 (3/10 の 3 乗)。",
              "4. 1/720 — 分子を 1 にした形。分子は 3 × 2 × 1 = 6。"])),

    dict(number=10, points=2, unit_tag="KAKURITSU-TENYOU",
         stem=f"当たりの本数を {ATARI4} 本に増やし、くじは戻さないものとする。"
              "このとき、太郎さんと花子さんの少なくとも一方が当たりを引く確率を"
              "1 つ選べ。",
         vals=[P_ATLEAST, R(1, 3), P_AT4, R(4, 5)], answer=3,
         solve=lambda: 1 - R(TOTAL - ATARI4, TOTAL) * R(TOTAL - ATARI4 - 1,
                                                        TOTAL - 1),
         explanation=m(
             "第5問と同じ手順を、数だけ変えてもう一度たどる。",
             "P = 1 - (2 人ともはずれる確率)",
             "はずれは 6 本。2 人ともはずれ = 6/10 × 5/9 = 30/90 = 1/3。"
             "P = 1 - 1/3 = 2/3",
             "2/3 — 当たりが 3 本のときの 8/15 より大きい。",
             ["1. 8/15 — 当たりが 3 本のときの値 (第5問)。本数を変えたのに"
              "更新していない。",
              "2. 1/3 — **2 人ともはずれる**確率。1 から引いていない。",
              "4. 4/5 — 4/10 + 4/10 と単純に足した形。"
              "2 人とも当たる場合を二重に数えている。"])),
]


def to_q(r):
    q = {k: v for k, v in r.items()
         if k not in ("vals", "solve", "tex")}
    if "tex" in r:                     # 文章の選択肢はそのまま
        q["choices"] = list(r["tex"])
        q["choices_plain"] = list(r["tex"])
    else:                              # 数値は値から表示を作る (ずれない)
        # ★ 選択肢は全部分数なので、行内の小さい分数だと読みにくい。
        #   \dfrac にして本文と同じ大きさで組む。
        q["choices"] = [f"${sp.latex(v).replace(chr(92) + 'frac', chr(92) + 'dfrac')}$"
                        for v in r["vals"]]
        q["choices_plain"] = [str(v) for v in r["vals"]]
    return q


QUESTIONS = [to_q(r) for r in RAW]


def same(a, b):
    if isinstance(a, sp.Basic) and isinstance(b, sp.Basic):
        return sp.simplify(a - b) == 0
    return a == b


def verify_math(meta, questions):
    """正解と誤答を sympy で独立に確かめる (手入力の正解を信じない)。"""
    errs = []
    for r in RAW:
        at = f"第{r['number']}問"
        vals = r["vals"]
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
        for v in vals:
            if isinstance(v, sp.Rational) and not (0 <= v <= 1):
                errs.append(f"{at}: 確率でない値が選択肢にある ({v})")
    # ★ 第3問の値が第1問と一致することが、この冊子の山 (順番によらない)。
    if P_TARO != P_HANAKO:
        errs.append("第1問と第3問の値が食い違う (順番によらないという結論が崩れる)")
    return errs


if __name__ == "__main__":
    sys.exit(B.run(HERE, META, QUESTIONS, verify_extra=verify_math))
