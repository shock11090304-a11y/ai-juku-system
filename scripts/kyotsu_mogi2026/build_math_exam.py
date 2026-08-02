#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト模試 2026 数学I・A ── 本番形式 (会話文 + 誘導連鎖) の seed JSON 生成器。

【build_math.py (単元別ドリル) との違い】
  build_math.py       : 各小問が独立。公式を 1 つ当てはめれば終わる。単元別の反復練習向け。
  build_math_exam.py  : ★こちら。本番の共通テストと同じ作り。
                        - 300〜800 字の場面設定 (会話文・実測データ)
                        - 誘導連鎖: 問1 の結果を問2 で、問2 の結果を問3 で使う
                        - 1 大問が [1][2] の 2 場面で構成される (第1問・第2問)

  塾長指摘 (2026-08-02)「実際の共通模試のレベル・形式になってない」への対応。
  実測で場面設定が 79〜171 字・誘導連鎖ゼロだったため、本番構成で作り直した。

【本番の数学I・A 構成 (新課程 2025〜・70分・100点・全問必答)】
  第1問 [1] 数と式 / [2] 図形と計量          30点
  第2問 [1] 二次関数 / [2] データの分析       30点
  第3問 場合の数と確率                        20点
  第4問 図形の性質                            20点

  投入先は (rikei, math_1a, kyotsu_rikei) = MOCK_EXAM_TEMPLATES["kyotsu_math"] が引く枠。

【正解の作り方】
  correct / distractors を「LaTeX と sympy 値」の組で持ち、verify() が独立に再計算して照合する。
  誘導連鎖でも各小問の verify() は前問の答えに依存させず、定義から計算し直す
  (誘導の途中で 1 問間違えると以降が全部ずれる、という連鎖事故を検出するため)。

【解説フォーマット】
  server/main.py 理系プロンプト準拠「方針→立式→計算→答え→補足」の 5 セクション。

出力: seed-data/kyotsu_mogi2026_math_exam_manual.json
実行: python3 scripts/kyotsu_mogi2026/build_math_exam.py
"""
import json
import hashlib
import os

from sympy import (
    Integer, Rational, symbols, sqrt, simplify, expand, factor, Tuple, Interval,
    S, solveset, Eq, binomial, sin, cos, pi, oo, Union, FiniteSet,
)

x, a, n = symbols('x a n')

OUT = os.path.join(os.path.dirname(__file__), '..', '..',
                   'seed-data', 'kyotsu_mogi2026_math_exam_manual.json')
SOURCE = 'kyotsu-mogi2026-exam-20260802'
MODEL = 'claude-kyotsu-mogi2026-exam-verified'
SECTIONS = ('方針', '立式', '計算', '答え', '補足')

DAIMON = []


def D(part_key, group, points, passage, subqs):
    DAIMON.append(dict(part_key=part_key, group=group, points=points,
                       passage=passage, subqs=subqs))


def Q(stem, unit, correct, distractors, verify, hoshin, rishiki, keisan, kotae, hosoku):
    return dict(stem=stem, unit=unit, correct=correct, distractors=distractors, verify=verify,
                hoshin=hoshin, rishiki=rishiki, keisan=keisan, kotae=kotae, hosoku=hosoku)


def _eq(u, v):
    if isinstance(u, str) or isinstance(v, str):
        return u == v
    if isinstance(u, Tuple) or isinstance(v, Tuple):
        if not (isinstance(u, Tuple) and isinstance(v, Tuple)) or len(u) != len(v):
            return False
        return all(_eq(ui, vi) for ui, vi in zip(u, v))
    if isinstance(u, (FiniteSet, Interval, Union)) or isinstance(v, (FiniteSet, Interval, Union)):
        return u == v
    try:
        return simplify(u - v) == 0
    except TypeError:
        return u == v


C = binomial


# =====================================================================
# 第1問 [1] 数と式 / [2] 図形と計量   (30点・7小問)
# =====================================================================
D("math_1a", "数学I・A 第1問", [4, 4, 4, 4, 4, 5, 5],
  """第1問は [1]、[2] の 2 つの場面からなる。

[1] 太郎さんと花子さんは、文字 \\(a\\) を含む 2 次不等式について話している。以下の会話を読み、問1〜問3に答えよ。

 太郎: 不等式 \\(x^2-(a+3)x+3a\\le 0\\) を考えてみよう。\\(a\\) は実数の定数だよ。
 花子: 左辺は因数分解できそうね。因数分解してしまえば、\\(a\\) の値によって解がどう変わるかが見えるはず。
 太郎: そうだね。まず因数分解して、それから \\(a\\) に具体的な値を入れて確かめてみよう。
 花子: 最後に、解に含まれる整数の個数が \\(a\\) によってどう変わるかも調べてみたいわ。

[2] 花子さんは、校庭にある三角形の土地 ABC の広さを調べるため、辺 AB の長さと 2 つの角を測定した。
測定の結果、\\(AB=8\\ \\mathrm{m}\\)、\\(\\angle ABC=105^\\circ\\)、\\(\\angle BCA=45^\\circ\\) であった。
この土地について問4〜問7に答えよ。""",
  [
    # ---- [1] 数と式 (誘導連鎖: 問1 → 問2 → 問3) ----
    Q("[1] 2 次式 \\(x^2-(a+3)x+3a\\) を因数分解せよ。",
      "数と式",
      ("\\((x-3)(x-a)\\)", expand((x - 3) * (x - a))),
      [("\\((x+3)(x+a)\\)", expand((x + 3) * (x + a))),
       ("\\((x-3)(x+a)\\)", expand((x - 3) * (x + a))),
       ("\\((x-1)(x-3a)\\)", expand((x - 1) * (x - 3 * a)))],
      lambda: expand(factor(x ** 2 - (a + 3) * x + 3 * a)),
      hoshin="定数項 \\(3a\\) が「\\(3\\times a\\)」と読めることに着目し、"
             "和が \\(a+3\\)、積が \\(3a\\) になる 2 数を探す。",
      rishiki="\\((x-p)(x-q)\\) とおくと \\(p+q=a+3\\)、\\(pq=3a\\)。",
      keisan="\\(p=3,\\ q=a\\) とすると \\(p+q=a+3\\)、\\(pq=3a\\) をどちらも満たす。"
             "よって \\(x^2-(a+3)x+3a=(x-3)(x-a)\\)。",
      kotae="\\((x-3)(x-a)\\)。",
      hosoku="文字を含む 2 次式でも、和と積で 2 数を探す手順は変わらない。"
             "展開して \\(x^2-ax-3x+3a=x^2-(a+3)x+3a\\) と検算しておくこと。"
             "以降の問2・問3 はこの因数分解を出発点にする。"),
    Q("[1] 問1 の結果 \\(x^2-(a+3)x+3a=(x-3)(x-a)\\) を用いる。"
      "\\(a=5\\) のとき、不等式 \\(x^2-(a+3)x+3a\\le 0\\) を解け。",
      "数と式",
      ("\\(3\\le x\\le 5\\)", Interval(3, 5)),
      [("\\(x\\le 3\\) または \\(5\\le x\\)", Union(Interval(-oo, 3), Interval(5, oo))),
       ("\\(-5\\le x\\le -3\\)", Interval(-5, -3)),
       ("\\(3\\le x\\le 8\\)", Interval(3, 8))],
      lambda: solveset((x - 3) * (x - 5) <= 0, x, S.Reals),
      hoshin="因数分解した形に \\(a\\) の値を代入し、下に凸の放物線が 0 以下になる範囲を読む。",
      rishiki="\\(a=5\\) を代入して \\((x-3)(x-5)\\le 0\\)。",
      keisan="\\(x\\) 軸との交点は \\(x=3,\\ 5\\)。下に凸なので 0 以下になるのは 2 解の間。"
             "よって \\(3\\le x\\le 5\\)。",
      kotae="\\(3\\le x\\le 5\\)。",
      hosoku="\\(\\le 0\\) は「2 解の間」、\\(\\ge 0\\) は「2 解の外側」。"
             "不等号の向きを取り違えると \\(x\\le3\\) または \\(5\\le x\\) を選んでしまう。"),
    Q("[1] \\(a>3\\) とする。このとき不等式 \\((x-3)(x-a)\\le 0\\) の解は \\(3\\le x\\le a\\) である。"
      "解に含まれる整数がちょうど 4 個であるような \\(a\\) の値の範囲を求めよ。",
      "数と式",
      ("\\(6\\le a<7\\)", Interval.Ropen(6, 7)),
      [("\\(6<a\\le 7\\)", Interval.Lopen(6, 7)),
       ("\\(7\\le a<8\\)", Interval.Ropen(7, 8)),
       ("\\(5\\le a<6\\)", Interval.Ropen(5, 6))],
      lambda: (lambda hits: Interval.Ropen(min(hits), max(hits) + Rational(1, 100)))(
          [Rational(i, 100) for i in range(300, 900)
           if len([k for k in range(-50, 50) if 3 <= k <= Rational(i, 100)]) == 4]),
      hoshin="解の区間 \\(3\\le x\\le a\\) に入る整数を小さい方から数え、"
             "4 個目までは入り 5 個目は入らない、という条件を \\(a\\) の不等式にする。",
      rishiki="区間に入る整数は \\(3,\\ 4,\\ 5,\\ \\dots\\) と続く。"
              "ちょうど 4 個 \\(=3,4,5,6\\) が入り、\\(7\\) は入らない条件を書く。",
      keisan="\\(6\\) が入るには \\(a\\ge 6\\)、\\(7\\) が入らないためには \\(a<7\\)。"
             "よって \\(6\\le a<7\\)。",
      kotae="\\(6\\le a<7\\)。",
      hosoku="端点の扱いが分かれ目。\\(a=6\\) のとき解は \\(3\\le x\\le6\\) で整数は "
             "\\(3,4,5,6\\) の 4 個 (条件を満たす)。"
             "\\(a=7\\) のとき \\(7\\) も入って 5 個になるので \\(a=7\\) は除く。"
             "不等号の等号の有無を、端の値を実際に代入して確かめる習慣をつけること。"),
    # ---- [2] 図形と計量 (誘導連鎖: 問4 → 問5 → 問6 → 問7) ----
    Q("[2] \\(AB=8\\)、\\(\\angle ABC=105^\\circ\\)、\\(\\angle BCA=45^\\circ\\) の三角形 ABC について、"
      "\\(\\angle BAC\\) の大きさを求めよ。",
      "図形と計量",
      ("\\(30^\\circ\\)", Integer(30)),
      [("\\(45^\\circ\\)", Integer(45)), ("\\(60^\\circ\\)", Integer(60)), ("\\(75^\\circ\\)", Integer(75))],
      lambda: Integer(180) - Integer(105) - Integer(45),
      hoshin="三角形の内角の和は \\(180^\\circ\\)。残り 1 つの角は引き算で出る。",
      rishiki="\\(\\angle BAC=180^\\circ-\\angle ABC-\\angle BCA=180^\\circ-105^\\circ-45^\\circ\\)。",
      keisan="\\(180^\\circ-150^\\circ=30^\\circ\\)。",
      kotae="\\(30^\\circ\\)。",
      hosoku="この \\(30^\\circ\\) が問5 以降の出発点になる。"
             "測量の問題では、まず分かる角をすべて埋めてから定理を選ぶと迷わない。"),
    Q("[2] 三角形 ABC において \\(AB=8\\)、\\(\\angle BAC=30^\\circ\\)、\\(\\angle BCA=45^\\circ\\) であるとき、"
      "辺 \\(BC\\) の長さを求めよ。",
      "図形と計量",
      ("\\(4\\sqrt{2}\\)", 4 * sqrt(2)),
      [("\\(8\\sqrt{2}\\)", 8 * sqrt(2)), ("\\(4\\sqrt{3}\\)", 4 * sqrt(3)), ("\\(4\\)", Integer(4))],
      lambda: simplify(Integer(8) * sin(pi / 6) / sin(pi / 4)),
      hoshin="「1 辺とその両端でない角」の組が 2 つ分かっているので正弦定理を使う。"
             "求める辺 \\(BC\\) の対角は \\(\\angle A\\)、既知の辺 \\(AB\\) の対角は \\(\\angle C\\)。",
      rishiki="\\(\\dfrac{BC}{\\sin A}=\\dfrac{AB}{\\sin C}\\) より "
              "\\(BC=\\dfrac{AB\\sin A}{\\sin C}=\\dfrac{8\\sin30^\\circ}{\\sin45^\\circ}\\)。",
      keisan="\\(\\sin30^\\circ=\\dfrac12\\)、\\(\\sin45^\\circ=\\dfrac{\\sqrt2}{2}\\) だから "
             "\\(BC=\\dfrac{8\\cdot\\frac12}{\\frac{\\sqrt2}{2}}=\\dfrac{4\\cdot2}{\\sqrt2}"
             "=\\dfrac{8}{\\sqrt2}=4\\sqrt2\\)。",
      kotae="\\(4\\sqrt{2}\\)。",
      hosoku="辺と対角の対応を取り違えるのが最大のミス。"
             "\\(BC\\) の向かい側は \\(A\\)、\\(AB\\) の向かい側は \\(C\\) と、"
             "図に矢印を書き込んでから式を立てるとよい。"),
    Q("[2] 三角形 ABC において \\(AB=8\\)、\\(BC=4\\sqrt{2}\\)、\\(\\angle ABC=105^\\circ\\) であるとき、"
      "三角形 ABC の面積を求めよ。必要なら \\(\\sin105^\\circ=\\dfrac{\\sqrt{6}+\\sqrt{2}}{4}\\) を用いてよい。",
      "図形と計量",
      ("\\(8\\sqrt{3}+8\\)", 8 * sqrt(3) + 8),
      [("\\(16\\sqrt{3}+16\\)", 16 * sqrt(3) + 16),
       ("\\(8\\sqrt{3}\\)", 8 * sqrt(3)),
       ("\\(4\\sqrt{6}+4\\sqrt{2}\\)", 4 * sqrt(6) + 4 * sqrt(2))],
      lambda: simplify(Rational(1, 2) * Integer(8) * (4 * sqrt(2)) * sin(105 * pi / 180)),
      hoshin="2 辺とその間の角がそろったので \\(S=\\dfrac12ab\\sin C\\)。"
             "間の角は問4・問5 で使った \\(\\angle ABC\\)。",
      rishiki="\\(S=\\dfrac12\\cdot AB\\cdot BC\\cdot\\sin\\angle ABC"
              "=\\dfrac12\\cdot8\\cdot4\\sqrt2\\cdot\\sin105^\\circ\\)。",
      keisan="\\(\\dfrac12\\cdot8\\cdot4\\sqrt2=16\\sqrt2\\)。"
             "\\(16\\sqrt2\\cdot\\dfrac{\\sqrt6+\\sqrt2}{4}=4\\sqrt2(\\sqrt6+\\sqrt2)"
             "=4(\\sqrt{12}+2)=4(2\\sqrt3+2)=8\\sqrt3+8\\)。",
      kotae="\\(8\\sqrt{3}+8\\)。",
      hosoku="\\(\\sqrt2\\cdot\\sqrt6=\\sqrt{12}=2\\sqrt3\\) の整理を落とすと "
             "\\(4\\sqrt6+4\\sqrt2\\) の形のまま止まってしまう。"
             "根号は必ず最後まで簡単にしてから選択肢と照合する。"
             "\\(\\dfrac12\\) を掛け忘れると \\(16\\sqrt3+16\\)。"),
    Q("[2] 三角形 ABC の面積が \\(8\\sqrt{3}+8\\)、\\(BC=4\\sqrt{2}\\) であるとき、"
      "頂点 A から辺 BC に下ろした垂線の長さを求めよ。",
      "図形と計量",
      ("\\(2\\sqrt{6}+2\\sqrt{2}\\)", 2 * sqrt(6) + 2 * sqrt(2)),
      [("\\(\\sqrt{6}+\\sqrt{2}\\)", sqrt(6) + sqrt(2)),
       ("\\(4\\sqrt{6}+4\\sqrt{2}\\)", 4 * sqrt(6) + 4 * sqrt(2)),
       ("\\(2\\sqrt{3}+2\\)", 2 * sqrt(3) + 2)],
      lambda: simplify(2 * (8 * sqrt(3) + 8) / (4 * sqrt(2))),
      hoshin="「底辺 × 高さ ÷ 2」を高さについて解く。底辺を \\(BC\\) とみれば高さが求める垂線。",
      rishiki="\\(S=\\dfrac12\\cdot BC\\cdot h\\) より \\(h=\\dfrac{2S}{BC}"
              "=\\dfrac{2(8\\sqrt3+8)}{4\\sqrt2}\\)。",
      keisan="\\(h=\\dfrac{16\\sqrt3+16}{4\\sqrt2}=\\dfrac{4\\sqrt3+4}{\\sqrt2}"
             "=\\dfrac{(4\\sqrt3+4)\\sqrt2}{2}=2\\sqrt2(\\sqrt3+1)=2\\sqrt6+2\\sqrt2\\)。",
      kotae="\\(2\\sqrt{6}+2\\sqrt{2}\\)。",
      hosoku="分母の有理化を忘れると選択肢の形にならない。"
             "概算 \\(2\\times2.449+2\\times1.414\\approx7.7\\) と、"
             "\\(S\\approx21.9\\)、\\(BC\\approx5.66\\) から \\(h=2S/BC\\approx7.7\\) が一致することで検算できる。"),
  ])


# =====================================================================
# 第2問 [1] 二次関数 / [2] データの分析   (30点・7小問)
# =====================================================================
_times = [12, 15, 18, 20, 22, 25, 28, 30, 35, 45]

D("math_1a", "数学I・A 第2問", [4, 4, 4, 5, 4, 4, 5],
  """第2問は [1]、[2] の 2 つの場面からなる。

[1] 太郎さんの学校では、長さ \\(40\\ \\mathrm{m}\\) のロープで長方形の花壇を囲む計画を立てている。
ロープはたるみなく使い切り、長方形の縦の長さを \\(x\\ \\mathrm{m}\\) とする。以下の会話を読み、問1〜問4に答えよ。

 太郎: ロープの長さが決まっているから、縦を決めれば横も決まるね。
 先生: そうです。まず面積を \\(x\\) の式で表してごらんなさい。
 太郎: 2 次式になりそうです。平方完成すれば、いちばん広くなる形も分かりますね。
 先生: そのとおり。最後に「面積が一定以上になる縦の範囲」も考えてみましょう。

[2] 花子さんは、クラスの生徒 10 人に通学時間 (分) を聞き、小さい順に並べた。

  12, 15, 18, 20, 22, 25, 28, 30, 35, 45

このデータについて問5〜問7に答えよ。""",
  [
    # ---- [1] 二次関数 (誘導連鎖: 問1 → 問2 → 問3 → 問4) ----
    Q("[1] 周の長さが \\(40\\ \\mathrm{m}\\) の長方形の縦を \\(x\\ \\mathrm{m}\\) とするとき、"
      "面積 \\(S\\ (\\mathrm{m}^2)\\) を \\(x\\) の式で表せ。",
      "二次関数",
      ("\\(S=x(20-x)\\)", expand(x * (20 - x))),
      [("\\(S=x(40-x)\\)", expand(x * (40 - x))),
       ("\\(S=x(20-2x)\\)", expand(x * (20 - 2 * x))),
       ("\\(S=2x(20-x)\\)", expand(2 * x * (20 - x)))],
      lambda: expand(x * (Rational(40, 2) - x)),
      hoshin="周の長さの式から横の長さを \\(x\\) で表し、面積 = 縦 × 横 に代入する。",
      rishiki="横を \\(y\\) とすると \\(2(x+y)=40\\) より \\(y=20-x\\)。"
              "面積は \\(S=xy\\)。",
      keisan="\\(S=x(20-x)=20x-x^2\\)。",
      kotae="\\(S=x(20-x)\\)。",
      hosoku="周の長さは縦と横を 2 回ずつ足したもの。"
             "\\(x+y=40\\) と誤ると \\(S=x(40-x)\\) になる。"
             "「\\(40\\div2=20\\) が縦と横の和」と押さえること。この式を問2 以降で使う。"),
    Q("[1] 問1 の \\(S=x(20-x)\\) を平方完成した形として正しいものはどれか。",
      "二次関数",
      ("\\(S=-(x-10)^2+100\\)", expand(-(x - 10) ** 2 + 100)),
      [("\\(S=-(x-10)^2-100\\)", expand(-(x - 10) ** 2 - 100)),
       ("\\(S=(x-10)^2+100\\)", expand((x - 10) ** 2 + 100)),
       ("\\(S=-(x-20)^2+400\\)", expand(-(x - 20) ** 2 + 400))],
      lambda: expand(20 * x - x ** 2),
      hoshin="\\(x^2\\) の係数が負なので、まず \\(-1\\) でくくってから平方完成する。",
      rishiki="\\(S=20x-x^2=-(x^2-20x)\\)。",
      keisan="\\(x^2-20x=(x-10)^2-100\\) だから "
             "\\(S=-\\{(x-10)^2-100\\}=-(x-10)^2+100\\)。",
      kotae="\\(S=-(x-10)^2+100\\)。",
      hosoku="\\(-1\\) でくくった中身を平方完成したあと、"
             "カッコを外すときに \\(-100\\) の符号が \\(+100\\) に変わる点が急所。"
             "上に凸なので頂点が最大を与える。"),
    Q("[1] 問2 の \\(S=-(x-10)^2+100\\) から、花壇の面積が最大になるときの面積を求めよ。"
      "ただし \\(0<x<20\\) とする。",
      "二次関数",
      ("\\(100\\ \\mathrm{m}^2\\)", Integer(100)),
      [("\\(50\\ \\mathrm{m}^2\\)", Integer(50)),
       ("\\(200\\ \\mathrm{m}^2\\)", Integer(200)),
       ("\\(400\\ \\mathrm{m}^2\\)", Integer(400))],
      lambda: max((Rational(i, 10) * (20 - Rational(i, 10)) for i in range(1, 200))),
      hoshin="上に凸の放物線なので、頂点が定義域に入っていれば頂点の \\(y\\) 座標が最大値。",
      rishiki="頂点は \\((10,\\ 100)\\)。定義域 \\(0<x<20\\) に \\(x=10\\) は含まれる。",
      keisan="よって最大値は \\(100\\)。このとき縦 \\(10\\)、横 \\(20-10=10\\) の正方形になる。",
      kotae="\\(100\\ \\mathrm{m}^2\\)。",
      hosoku="周の長さが決まっているとき、長方形は正方形のとき面積が最大になる。"
             "この結論は覚えておくと検算に使える。"),
    Q("[1] 花壇の面積が \\(96\\ \\mathrm{m}^2\\) 以上になるような縦の長さ \\(x\\) の範囲を求めよ。"
      "ただし \\(S=x(20-x)\\)、\\(0<x<20\\) とする。",
      "二次関数",
      ("\\(8\\le x\\le 12\\)", Interval(8, 12)),
      [("\\(x\\le 8\\) または \\(12\\le x\\)", Union(Interval(-oo, 8), Interval(12, oo))),
       ("\\(4\\le x\\le 16\\)", Interval(4, 16)),
       ("\\(8<x<12\\)", Interval.open(8, 12))],
      lambda: solveset(x * (20 - x) >= 96, x, S.Reals),
      hoshin="「面積が 96 以上」を不等式にし、移項して 2 次不等式として解く。",
      rishiki="\\(x(20-x)\\ge 96\\) より \\(20x-x^2\\ge96\\)、"
              "整理して \\(x^2-20x+96\\le 0\\)。",
      keisan="\\(x^2-20x+96=(x-8)(x-12)\\) だから \\((x-8)(x-12)\\le0\\)。"
             "下に凸なので 2 解の間で、\\(8\\le x\\le 12\\)。"
             "これは定義域 \\(0<x<20\\) に含まれる。",
      kotae="\\(8\\le x\\le 12\\)。",
      hosoku="移項のときに全体の符号が変わり、不等号の向きも変わる点が最大のミス源。"
             "「以上」なので等号を含む。端の \\(x=8\\) を代入すると "
             "\\(8\\times12=96\\) でちょうど条件を満たすことが確かめられる。"),
    # ---- [2] データの分析 (誘導連鎖: 問5 → 問6 → 問7) ----
    Q("[2] 通学時間 12, 15, 18, 20, 22, 25, 28, 30, 35, 45 (分) の中央値を求めよ。",
      "データの分析",
      ("\\(23.5\\) 分", Rational(47, 2)),
      [("\\(22\\) 分", Integer(22)), ("\\(25\\) 分", Integer(25)), ("\\(23\\) 分", Integer(23))],
      lambda: Rational(_times[4] + _times[5], 2),
      hoshin="データの個数が偶数なので、中央に並ぶ 2 個の平均が中央値。",
      rishiki="10 個なので 5 番目と 6 番目の平均。5 番目は \\(22\\)、6 番目は \\(25\\)。",
      keisan="\\(\\dfrac{22+25}{2}=\\dfrac{47}{2}=23.5\\)。",
      kotae="\\(23.5\\) 分。",
      hosoku="奇数個なら真ん中 1 個、偶数個なら真ん中 2 個の平均。"
             "個数を先に数える習慣をつけると取り違えない。"
             "平均値 \\(25\\) 分とは別物である点にも注意 (このデータは \\(45\\) 分が平均を押し上げている)。"),
    Q("[2] 通学時間 12, 15, 18, 20, 22, 25, 28, 30, 35, 45 (分) の四分位範囲を求めよ。",
      "データの分析",
      ("\\(12\\) 分", Integer(12)),
      [("\\(10\\) 分", Integer(10)), ("\\(15\\) 分", Integer(15)), ("\\(33\\) 分", Integer(33))],
      lambda: Integer(sorted(_times)[7] - sorted(_times)[2]),
      hoshin="四分位範囲は \\(Q_3-Q_1\\)。中央値でデータを下位・上位に分け、それぞれの中央値をとる。",
      rishiki="下位 5 個は \\(12,15,18,20,22\\)、上位 5 個は \\(25,28,30,35,45\\)。"
              "それぞれの中央値が \\(Q_1,\\ Q_3\\)。",
      keisan="\\(Q_1=18\\)、\\(Q_3=30\\)。よって四分位範囲は \\(30-18=12\\)。",
      kotae="\\(12\\) 分。",
      hosoku="範囲 (最大 − 最小) \\(=45-12=33\\) と混同しないこと。"
             "四分位範囲は外れ値の影響を受けにくい散らばりの指標で、"
             "\\(45\\) 分という大きな値があっても値が跳ねない。"),
    Q("[2] 問6 より \\(Q_1=18\\)、\\(Q_3=30\\)、四分位範囲は \\(12\\) である。"
      "\\(Q_1-1.5\\times(\\text{四分位範囲})\\) 以下、または "
      "\\(Q_3+1.5\\times(\\text{四分位範囲})\\) 以上の値を外れ値とするとき、"
      "このデータに外れ値は何個あるか。",
      "データの分析",
      ("\\(0\\) 個", Integer(0)),
      [("\\(1\\) 個", Integer(1)), ("\\(2\\) 個", Integer(2)), ("\\(3\\) 個", Integer(3))],
      lambda: Integer(len([v for v in _times if v <= 18 - Rational(3, 2) * 12 or v >= 30 + Rational(3, 2) * 12])),
      hoshin="外れ値の境界を先に数値で求め、その外側にデータがあるかを数える。",
      rishiki="下側の境界は \\(Q_1-1.5\\times12=18-18\\)、"
              "上側の境界は \\(Q_3+1.5\\times12=30+18\\)。",
      keisan="下側は \\(0\\) 以下、上側は \\(48\\) 以上。"
             "最小値は \\(12\\) で \\(0\\) より大きく、最大値は \\(45\\) で \\(48\\) より小さい。"
             "よって外れ値は 1 つもない。",
      kotae="\\(0\\) 個。",
      hosoku="\\(45\\) 分だけ他より大きいので外れ値に見えるが、"
             "基準に照らすと \\(48\\) に届かないので外れ値ではない。"
             "「見た目で判断せず基準値を計算する」ことがこの設問の要点。"),
  ])


# =====================================================================
# 第3問 場合の数と確率   (20点・5小問)
# =====================================================================
D("math_1a", "数学I・A 第3問", [4, 4, 4, 4, 4],
  """箱の中に、\\(1\\) から \\(6\\) までの番号が 1 つずつ書かれたカードが 1 枚ずつ、合計 6 枚入っている。
この箱から同時に 3 枚のカードを取り出す。太郎さんと花子さんは、取り出した 3 枚の番号について
次のように話している。以下の会話を読み、問1〜問5に答えよ。

 太郎: まず、取り出し方が全部で何通りあるかを数えよう。同時に取り出すから順番は関係ないね。
 花子: そうね。そのあとで「番号の和が偶数になる確率」を考えてみたいわ。
 太郎: 和の偶奇は、奇数のカードが何枚入っているかで決まるはずだよ。
 花子: なるほど。最大の番号がいくつになるかも面白そう。最大値の期待値まで出してみましょう。""",
  [
    Q("\\(1\\) から \\(6\\) の番号のカード 6 枚から同時に 3 枚を取り出すとき、取り出し方は何通りあるか。",
      "場合の数・確率",
      ("\\(20\\) 通り", C(6, 3)),
      [("\\(120\\) 通り", Integer(120)), ("\\(216\\) 通り", Integer(216)), ("\\(18\\) 通り", Integer(18))],
      lambda: C(6, 3),
      hoshin="「同時に取り出す」ので順番は区別しない。組合せで数える。",
      rishiki="\\({}_6\\mathrm{C}_3\\)。",
      keisan="\\(\\dfrac{6\\cdot5\\cdot4}{3\\cdot2\\cdot1}=20\\)。",
      kotae="\\(20\\) 通り。",
      hosoku="順番を区別すると \\({}_6\\mathrm{P}_3=120\\) 通りで 6 倍になる。"
             "この \\(20\\) 通りが問2 以降すべての確率の分母になる。"),
    Q("問1 より全事象は \\(20\\) 通りである。取り出した 3 枚の番号の和が偶数になる確率を求めよ。",
      "場合の数・確率",
      ("\\(\\dfrac{1}{2}\\)", Rational(1, 2)),
      [("\\(\\dfrac{2}{5}\\)", Rational(2, 5)),
       ("\\(\\dfrac{3}{5}\\)", Rational(3, 5)),
       ("\\(\\dfrac{9}{20}\\)", Rational(9, 20))],
      lambda: Rational(len([1 for i in range(1, 7) for j in range(i + 1, 7) for k in range(j + 1, 7)
                            if (i + j + k) % 2 == 0]), C(6, 3)),
      hoshin="和の偶奇は奇数カードの枚数だけで決まる。奇数が偶数枚 (0 枚か 2 枚) なら和は偶数。",
      rishiki="奇数は \\(1,3,5\\) の 3 枚、偶数は \\(2,4,6\\) の 3 枚。"
              "\\((\\text{奇数 0 枚,偶数 3 枚})\\) と \\((\\text{奇数 2 枚,偶数 1 枚})\\) を数える。",
      keisan="奇数 0 枚: \\({}_3\\mathrm{C}_0\\times{}_3\\mathrm{C}_3=1\\) 通り。"
             "奇数 2 枚: \\({}_3\\mathrm{C}_2\\times{}_3\\mathrm{C}_1=3\\times3=9\\) 通り。"
             "合計 \\(10\\) 通りで、確率は \\(\\dfrac{10}{20}=\\dfrac12\\)。",
      kotae="\\(\\dfrac{1}{2}\\)。",
      hosoku="「奇数を何枚取るか」で場合分けするのがこの型の定石。"
             "奇数 1 枚・3 枚のときは和が奇数になるので、"
             "残りの \\(10\\) 通りがそちらに対応し、合計 \\(20\\) 通りに合う。"),
    Q("取り出した 3 枚の番号の最大値が \\(5\\) である確率を求めよ。ただし全事象は \\(20\\) 通りである。",
      "場合の数・確率",
      ("\\(\\dfrac{3}{10}\\)", Rational(3, 10)),
      [("\\(\\dfrac{1}{4}\\)", Rational(1, 4)),
       ("\\(\\dfrac{1}{2}\\)", Rational(1, 2)),
       ("\\(\\dfrac{1}{10}\\)", Rational(1, 10))],
      lambda: Rational(len([1 for i in range(1, 7) for j in range(i + 1, 7) for k in range(j + 1, 7)
                            if max(i, j, k) == 5]), C(6, 3)),
      hoshin="「最大値が \\(5\\)」は「\\(5\\) を含み、かつ \\(6\\) を含まない」と言い換える。",
      rishiki="\\(5\\) は必ず取り、\\(6\\) は取らない。"
              "残り 2 枚を \\(1,2,3,4\\) の 4 枚から選ぶ。",
      keisan="\\({}_4\\mathrm{C}_2=6\\) 通り。確率は \\(\\dfrac{6}{20}=\\dfrac{3}{10}\\)。",
      kotae="\\(\\dfrac{3}{10}\\)。",
      hosoku="「最大値が \\(5\\) 以下」\\(({}_5\\mathrm{C}_3=10)\\) から"
             "「最大値が \\(4\\) 以下」\\(({}_4\\mathrm{C}_3=4)\\) を引いて "
             "\\(10-4=6\\) 通り、としても同じ結果になる。"
             "この差の考え方は問4 でそのまま使える。"),
    Q("取り出した 3 枚の番号の最大値を \\(X\\) とする。\\(X\\) の期待値を求めよ。ただし全事象は \\(20\\) 通りである。",
      "場合の数・確率",
      ("\\(\\dfrac{21}{4}\\)", Rational(21, 4)),
      [("\\(\\dfrac{9}{2}\\)", Rational(9, 2)), ("\\(5\\)", Integer(5)), ("\\(\\dfrac{11}{2}\\)", Rational(11, 2))],
      lambda: sum(Integer(max(i, j, k)) for i in range(1, 7) for j in range(i + 1, 7)
                  for k in range(j + 1, 7)) / C(6, 3),
      hoshin="\\(X\\) のとりうる値ごとに場合の数を数えて確率分布を作り、"
             "\\(E(X)=\\sum xP(X=x)\\) を計算する。",
      rishiki="最大値が \\(m\\) となるのは、\\(m\\) を取り残り 2 枚を \\(1\\) から \\(m-1\\) の "
              "\\(m-1\\) 枚から選ぶ場合で \\({}_{m-1}\\mathrm{C}_2\\) 通り。\\(m=3,4,5,6\\)。",
      keisan="\\({}_2\\mathrm{C}_2=1,\\ {}_3\\mathrm{C}_2=3,\\ {}_4\\mathrm{C}_2=6,\\ "
             "{}_5\\mathrm{C}_2=10\\) で合計 \\(20\\) 通り (全事象と一致)。"
             "\\(E(X)=\\dfrac{3\\cdot1+4\\cdot3+5\\cdot6+6\\cdot10}{20}"
             "=\\dfrac{3+12+30+60}{20}=\\dfrac{105}{20}=\\dfrac{21}{4}\\)。",
      kotae="\\(\\dfrac{21}{4}\\)。",
      hosoku="場合の数の合計が全事象 \\(20\\) と一致するかを必ず確かめること。"
             "ここが合わなければ数え落としがある。"
             "\\(\\dfrac{21}{4}=5.25\\) で、最大値は \\(6\\) に寄るという直観とも合う。"),
    Q("取り出した 3 枚の中に \\(6\\) が含まれているとき、3 枚の番号の和が偶数である条件付き確率を求めよ。",
      "場合の数・確率",
      ("\\(\\dfrac{2}{5}\\)", Rational(2, 5)),
      [("\\(\\dfrac{1}{2}\\)", Rational(1, 2)),
       ("\\(\\dfrac{3}{5}\\)", Rational(3, 5)),
       ("\\(\\dfrac{1}{5}\\)", Rational(1, 5))],
      lambda: (lambda tri: Rational(
          len([t for t in tri if 6 in t and sum(t) % 2 == 0]), len([t for t in tri if 6 in t])))(
              [(i, j, k) for i in range(1, 7) for j in range(i + 1, 7) for k in range(j + 1, 7)]),
      hoshin="条件付き確率なので、「\\(6\\) を含む」場合だけを新しい全事象として数え直す。",
      rishiki="\\(6\\) を含む取り出し方は、残り 2 枚を \\(1\\) から \\(5\\) の 5 枚から選ぶので "
              "\\({}_5\\mathrm{C}_2=10\\) 通り。"
              "\\(6\\) は偶数だから、和が偶数になるのは残り 2 枚の和が偶数のとき。",
      keisan="残り 2 枚の和が偶数 = 2 枚とも偶数 か 2 枚とも奇数。"
             "偶数は \\(2,4\\) で \\({}_2\\mathrm{C}_2=1\\) 通り、"
             "奇数は \\(1,3,5\\) で \\({}_3\\mathrm{C}_2=3\\) 通り。"
             "合計 \\(4\\) 通りだから \\(\\dfrac{4}{10}=\\dfrac25\\)。",
      kotae="\\(\\dfrac{2}{5}\\)。",
      hosoku="全事象 \\(20\\) 通りのまま計算すると誤り。"
             "条件付き確率では分母が「条件を満たす場合の数」に置き換わる。"
             "問2 の答え \\(\\dfrac12\\) と値が違うのは、"
             "\\(6\\) を含むという情報が和の偶奇に影響しているため。"),
  ])


# =====================================================================
# 第4問 図形の性質   (20点・5小問)
# =====================================================================
D("math_1a", "数学I・A 第4問", [4, 4, 4, 4, 4],
  """三角形 ABC において \\(AB=6\\)、\\(BC=5\\)、\\(CA=4\\) とする。
\\(\\angle A\\) の二等分線と辺 BC の交点を D とし、三角形 ABC の外接円と直線 AD の交点のうち
A でない方を E とする。花子さんは次のように考えている。以下を読み、問1〜問5に答えよ。

 花子: 角の二等分線があるから、まず BC がどう分けられるかが分かるはず。
 太郎: 3 辺の長さが全部分かっているから、余弦定理も使えるね。
 花子: 二等分線の長さ AD も出せそう。そのあと、円があるから方べきの定理が効きそうね。
 太郎: 最後に三角形の面積も求めてみよう。""",
  [
    Q("三角形 ABC において \\(AB=6\\)、\\(BC=5\\)、\\(CA=4\\) であり、"
      "\\(\\angle A\\) の二等分線と辺 BC の交点を D とする。\\(BD\\) の長さを求めよ。",
      "図形の性質",
      ("\\(3\\)", Integer(3)),
      [("\\(2\\)", Integer(2)), ("\\(\\dfrac{5}{2}\\)", Rational(5, 2)), ("\\(\\dfrac{10}{3}\\)", Rational(10, 3))],
      lambda: simplify(Integer(5) * Rational(6, 6 + 4)),
      hoshin="角の二等分線は、対辺をそれをはさむ 2 辺の比に内分する。",
      rishiki="\\(BD:DC=AB:AC=6:4=3:2\\)。\\(BC=5\\) をこの比に分ける。",
      keisan="\\(BD=5\\times\\dfrac{3}{3+2}=3\\)、\\(DC=5\\times\\dfrac{2}{5}=2\\)。",
      kotae="\\(3\\)。",
      hosoku="\\(B\\) の側に \\(AB\\)、\\(C\\) の側に \\(AC\\) が対応する。"
             "比を逆にすると \\(BD=2\\) になる。"
             "この \\(BD=3,\\ DC=2\\) は問3・問4 で使う。"),
    Q("三角形 ABC において \\(AB=6\\)、\\(BC=5\\)、\\(CA=4\\) であるとき、\\(\\cos\\angle BAC\\) の値を求めよ。",
      "図形の性質",
      ("\\(\\dfrac{9}{16}\\)", Rational(9, 16)),
      [("\\(\\dfrac{3}{4}\\)", Rational(3, 4)),
       ("\\(\\dfrac{1}{8}\\)", Rational(1, 8)),
       ("\\(\\dfrac{9}{20}\\)", Rational(9, 20))],
      lambda: simplify((Integer(6) ** 2 + Integer(4) ** 2 - Integer(5) ** 2) / (2 * 6 * 4)),
      hoshin="3 辺が分かっているので余弦定理を角 \\(A\\) について解いた形で使う。",
      rishiki="\\(\\cos\\angle BAC=\\dfrac{AB^2+CA^2-BC^2}{2\\cdot AB\\cdot CA}\\)。"
              "角 \\(A\\) をはさむ辺は \\(AB=6,\\ CA=4\\)、向かい合う辺は \\(BC=5\\)。",
      keisan="\\(\\cos\\angle BAC=\\dfrac{36+16-25}{2\\cdot6\\cdot4}=\\dfrac{27}{48}=\\dfrac{9}{16}\\)。",
      kotae="\\(\\dfrac{9}{16}\\)。",
      hosoku="引くのは対辺 \\(BC\\) の 2 乗。"
             "\\(\\cos\\) が正なので \\(\\angle A\\) は鋭角であり、"
             "最長辺 \\(AB=6\\) の対角 \\(\\angle C\\) が最大角になることとも矛盾しない。"
             "この値は問5 で \\(\\sin\\) に直して使う。"),
    Q("問1 で求めたように、\\(\\angle A\\) の二等分線と辺 BC の交点 D は \\(BD=3\\)、\\(DC=2\\) を満たす。"
      "\\(AB=6\\)、\\(CA=4\\) であるとき、線分 \\(AD\\) の長さを求めよ。"
      "必要なら \\(AD^2=AB\\cdot AC-BD\\cdot DC\\) を用いてよい。",
      "図形の性質",
      ("\\(3\\sqrt{2}\\)", 3 * sqrt(2)),
      [("\\(\\sqrt{30}\\)", sqrt(30)), ("\\(3\\)", Integer(3)), ("\\(2\\sqrt{6}\\)", 2 * sqrt(6))],
      lambda: simplify(sqrt(Integer(6) * Integer(4) - Integer(3) * Integer(2))),
      hoshin="角の二等分線の長さの公式 \\(AD^2=AB\\cdot AC-BD\\cdot DC\\) に、"
             "問1 で求めた \\(BD,\\ DC\\) を代入する。",
      rishiki="\\(AD^2=6\\times4-3\\times2\\)。",
      keisan="\\(AD^2=24-6=18\\)、\\(AD=\\sqrt{18}=3\\sqrt2\\)。",
      kotae="\\(3\\sqrt{2}\\)。",
      hosoku="公式の後半 \\(-BD\\cdot DC\\) を引き忘れると \\(\\sqrt{24}=2\\sqrt6\\) になる。"
             "\\(AD\\) は \\(AB=6\\) と \\(AC=4\\) の間の長さ "
             "\\((3\\sqrt2\\approx4.24)\\) に収まるので、値の妥当性も確認できる。"),
    Q("三角形 ABC の外接円と直線 AD の交点のうち A でない方を E とする。"
      "問1・問3 の結果より \\(BD=3\\)、\\(DC=2\\)、\\(AD=3\\sqrt{2}\\) である。線分 \\(DE\\) の長さを求めよ。",
      "図形の性質",
      ("\\(\\sqrt{2}\\)", sqrt(2)),
      [("\\(2\\sqrt{2}\\)", 2 * sqrt(2)), ("\\(\\dfrac{\\sqrt{2}}{2}\\)", sqrt(2) / 2), ("\\(2\\)", Integer(2))],
      lambda: simplify(Integer(3) * Integer(2) / (3 * sqrt(2))),
      hoshin="円の内部の点 D で 2 本の弦 BC と AE が交わっているので、方べきの定理を使う。",
      rishiki="\\(BD\\cdot DC=AD\\cdot DE\\) より \\(DE=\\dfrac{BD\\cdot DC}{AD}\\)。",
      keisan="\\(DE=\\dfrac{3\\times2}{3\\sqrt2}=\\dfrac{6}{3\\sqrt2}=\\dfrac{2}{\\sqrt2}=\\sqrt2\\)。",
      kotae="\\(\\sqrt{2}\\)。",
      hosoku="方べきの定理は、円の外部の点なら \\(PA\\cdot PB=PT^2\\)、"
             "内部の点なら「交わる 2 弦の積が等しい」という形になる。"
             "D は弦 BC 上にあるので内部の形を使う。"
             "有理化を忘れると選択肢の形にならない。"),
    Q("問2 で求めた \\(\\cos\\angle BAC=\\dfrac{9}{16}\\) を用いる。\\(AB=6\\)、\\(CA=4\\) であるとき、"
      "三角形 ABC の面積を求めよ。",
      "図形の性質",
      ("\\(\\dfrac{15\\sqrt{7}}{4}\\)", Rational(15, 4) * sqrt(7)),
      [("\\(\\dfrac{15\\sqrt{7}}{2}\\)", Rational(15, 2) * sqrt(7)),
       ("\\(\\dfrac{27}{4}\\)", Rational(27, 4)),
       ("\\(\\dfrac{5\\sqrt{7}}{4}\\)", Rational(5, 4) * sqrt(7))],
      lambda: simplify(sqrt(Rational(15, 2) * (Rational(15, 2) - 6) * (Rational(15, 2) - 5) * (Rational(15, 2) - 4))),
      hoshin="\\(\\cos\\) から \\(\\sin\\) を出し、\\(S=\\dfrac12ab\\sin C\\) に入れる。",
      rishiki="\\(\\sin^2\\angle BAC=1-\\left(\\dfrac{9}{16}\\right)^2\\)。"
              "\\(\\angle BAC\\) は三角形の内角なので \\(\\sin>0\\)。"
              "\\(S=\\dfrac12\\cdot AB\\cdot CA\\cdot\\sin\\angle BAC\\)。",
      keisan="\\(\\sin^2=1-\\dfrac{81}{256}=\\dfrac{175}{256}\\)、"
             "\\(\\sin=\\dfrac{\\sqrt{175}}{16}=\\dfrac{5\\sqrt7}{16}\\)。"
             "\\(S=\\dfrac12\\cdot6\\cdot4\\cdot\\dfrac{5\\sqrt7}{16}"
             "=12\\cdot\\dfrac{5\\sqrt7}{16}=\\dfrac{15\\sqrt7}{4}\\)。",
      kotae="\\(\\dfrac{15\\sqrt{7}}{4}\\)。",
      hosoku="ヘロンの公式 \\(s=\\dfrac{6+5+4}{2}=\\dfrac{15}{2}\\)、"
             "\\(S=\\sqrt{s(s-6)(s-5)(s-4)}\\) でも同じ値になり、検算に使える。"
             "\\(\\sqrt{175}=5\\sqrt7\\) の整理を落とすと形が合わない。"),
  ])


# =====================================================================
# 検証 → JSON
# =====================================================================
def _answer_positions():
    keys = [(dm["group"], qi) for dm in DAIMON for qi in range(len(dm["subqs"]))]
    ranked = sorted(keys, key=lambda kk: hashlib.md5(f'{SOURCE}:{kk[0]}:{kk[1]}'.encode()).hexdigest())
    return {kk: i % 4 for i, kk in enumerate(ranked)}


def build():
    rows, errors, total_sub, total_pts = [], [], 0, 0
    positions = _answer_positions()

    for dm in DAIMON:
        subs = []
        pts = dm["points"]
        if len(pts) != len(dm["subqs"]):
            errors.append(f'{dm["group"]}: 配点 {len(pts)} 個 vs 小問 {len(dm["subqs"])} 個')
        for qi, sq in enumerate(dm["subqs"]):
            tag = f'{dm["group"]} 問{qi + 1}'
            c_latex, c_val = sq["correct"]
            try:
                got = sq["verify"]()
            except Exception as e:  # noqa: BLE001
                errors.append(f'{tag}: verify() が例外 {type(e).__name__}: {e}')
                continue
            if not _eq(got, c_val):
                errors.append(f'{tag}: verify()={got} ≠ correct={c_val}')

            seen = [c_val]
            for d_latex, d_val in sq["distractors"]:
                if any(_eq(d_val, s) for s in seen):
                    errors.append(f'{tag}: 誤答「{d_latex}」が他の選択肢と同値')
                seen.append(d_val)
            if len(sq["distractors"]) != 3:
                errors.append(f'{tag}: 誤答は 3 個必要')

            body = {"方針": sq["hoshin"], "立式": sq["rishiki"], "計算": sq["keisan"],
                    "答え": sq["kotae"], "補足": sq["hosoku"]}
            for name in SECTIONS:
                if not (body[name] or "").strip():
                    errors.append(f'{tag}: 解説の「{name}」が空')
            if c_latex not in body["答え"]:
                errors.append(f'{tag}: 「答え:」に正答「{c_latex}」が含まれていない')
            explanation = "\n".join(f'{name}: {body[name]}' for name in SECTIONS)

            pos = positions[(dm["group"], qi)]
            choices = [d[0] for d in sq["distractors"]]
            choices.insert(pos, c_latex)

            subs.append({
                "id": f"q{qi + 1}", "type": "multiple_choice", "stem": sq["stem"],
                "choices": choices, "answer": pos, "unit": sq["unit"], "explanation": explanation,
            })
            total_sub += 1
        total_pts += sum(pts)

        rows.append({
            "exam_id": "rikei", "part_key": dm["part_key"], "eiken_grade": "kyotsu_rikei",
            "model": MODEL,
            "question_data": {
                "passage": dm["passage"], "subject": "数学",
                "univ_simulated": "共通テスト模試", "year_simulated": 2026,
                "source": SOURCE, "exam_format": True, "group": dm["group"],
                "points": pts, "questions": subs,
            },
        })

    # 誘導連鎖が実際に入っているか (前問の結果を stem が引き継いでいるか) を確認
    import re as _re
    for r in rows:
        qd = r["question_data"]
        chained = sum(1 for q in qd["questions"]
                      if _re.search(r'問\d+\s*(の結果|より|で求めた)|問\d+ より', q["stem"]))
        if chained == 0:
            errors.append(f'{qd["group"]}: 誘導連鎖 (前問の結果を使う小問) が 1 つも無い')

    if errors:
        print("❌ 検証エラー:")
        for e in errors:
            print("   -", e)
        raise SystemExit(1)

    dist = {0: 0, 1: 0, 2: 0, 3: 0}
    for r in rows:
        for q in r["question_data"]["questions"]:
            dist[q["answer"]] += 1

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"questions": rows, "skip_full": False}, f, ensure_ascii=False, indent=1)

    print(f"✅ 検証 OK: 数学I・A 本番形式 {len(rows)} 大問 / {total_sub} 小問 / 満点 {total_pts} 点")
    for r in rows:
        qd = r["question_data"]
        n_chain = sum(1 for q in qd["questions"]
                      if _re.search(r'問\d+\s*(の結果|より|で求めた)|問\d+ より', q["stem"]))
        print(f'   {qd["group"]:16} 場面設定 {len(qd["passage"]):4}字 / '
              f'小問 {len(qd["questions"])} / 誘導連鎖 {n_chain} 問 / 配点 {sum(qd["points"])}')
    print(f'   正解位置の分布: {dist}')
    print(f'   → {os.path.relpath(OUT)}')


if __name__ == "__main__":
    build()
