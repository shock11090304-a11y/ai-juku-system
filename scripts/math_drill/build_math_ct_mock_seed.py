#!/usr/bin/env python3
"""📐 高校数学ドリル: 共通テスト型オリジナル模試 第1回・第2回 (数学ⅠA 29 問 + 数学ⅡBC 32 問 ずつ) を単元ドリルのシードにする
(2026-10-06 塾長「1→2でやって」= 数学教材のうち、そのまま 4 択で使えるこの模試から先に入れる)。

出所 (塾のオリジナル。冊子 PDF は 📚 教材/数学/04_模試・共通テスト/共通テスト数学_第1回・第2回オリジナル模試 と同一):
  MATH_CT_MOCK_DIR/build_mock_exams.py (第1回) と build_mock_exams_set2.py (第2回。第1回のモジュールを読み込んで数値を替えたもの)。
  問題冊子は「設定文 P/formula_box/info_box → mcq(code, 設問, 選択肢4つ, 配点)」の並びで組まれ、正解は Sol(code, ア〜エ, 配点, 解説)、
  確認ポイントは *_DETAIL_POINTS / *_DETAIL_TEXT にある。ここでは reportlab の部品を記録用の関数に差し替えて問題冊子の組み立てを
  そのまま走らせ、並びを読み取る (PDF は作らない)。

1 問ずつの 4 択にする: 大問の 〔１〕〔２〕 ごとに、その設問までに出た設定文をすべて stem の先頭に付ける (前の設問の答えは使わない)。
  図は画面に出せないので「図のように、」「図は … である。」の文は落とす (どの図も本文の条件だけで解ける。盲検で確かめる)。
  第2回の設問文は短く、前の設問の文に条件が書かれているものがある → PROMPT_FIX で第1回と同じ書き方に直す。
数式: 独自記法 [[f|分子|分母]] [[v|AB]] [[o|∫|下端|上端]] と <sub>/<super>、√… を \( \) の LaTeX に直す (mypage と class.html の
  KaTeX が描く)。x² や ≦ などは文字のまま。
単元名は入試道場の単元タイル (dojo-drill.html の topic) と同じ文字列 (弱点の「コーチの一手」から道場の同じタイルが開く。道場は小問の
  単元タグで記録するので弱点の行は別)。level は全問 standard。
正解の位置: 元は ウ が 38% (ア 8%) と偏っているので、選択肢を巡回させて単元ごとに 4 位置へ順番に配る (表示の位置だけを散らす。値の大小の順位は
  巡回では変わらないので、順位の偏りは CHOICE_SET で直す)。

使い方:
  python3 scripts/math_drill/build_math_ct_mock_seed.py            # seed-data/math_drill_ct_mock_v1.json
  python3 scripts/math_drill/build_math_ct_mock_seed.py --blind DIR  # 盲検用 (答え・解説なし) と正解表
★盲検 3 名の全員一致だけを採る ([[exam-material-review-rule]])。直すものは下の PROMPT_FIX / CHOICE_FIX / DROP に理由つきで書く。
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import date

HOME = os.path.expanduser("~")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.environ.get("MATH_CT_MOCK_DIR", f"{HOME}/Desktop/📚 教材/数学/04_模試・共通テスト/math_common_test_mock（生成元）")
OUT = os.path.join(REPO, "seed-data", "math_drill_ct_mock_v1.json")

# 入試道場の単元タイル (dojo-drill.html) の topic と同じ文字列
U = {
    "set": "数学I 集合と命題", "numexp": "数学I 数と式", "trig_meas": "基礎数学 図形と計量", "quad": "基礎数学 二次関数",
    "data": "基礎数学 データ", "geom": "数学A 図形の性質", "prob": "基礎数学 確率", "figeq": "数学II 図形と方程式",
    "trigfn": "基礎数学 三角関数", "calc": "基礎数学 微積", "seq": "基礎数学 数列", "stat": "数学B 統計的な推測",
    "vec": "基礎数学 ベクトル", "cplx": "数学C 複素数平面",
}
UNIT_IA = {"1-1": "set", "1-2": "set", "1-3": "numexp", "1-4": "numexp", "1-5": "trig_meas", "1-6": "trig_meas", "1-7": "trig_meas",
           "1-8": "trig_meas", "1-9": "trig_meas", "2-1": "quad", "2-2": "quad", "2-3": "quad", "2-4": "quad", "2-5": "quad",
           "2-6": "data", "2-7": "data", "2-8": "data", "2-9": "data", "2-10": "data", "3-1": "trig_meas", "3-2": "trig_meas",
           "3-3": "trig_meas", "3-4": "geom", "3-5": "geom", "4-1": "prob", "4-2": "prob", "4-3": "prob", "4-4": "prob", "4-5": "prob"}
UNIT_IIBC = {"1": "figeq", "2": "trigfn", "3": "calc", "4": "seq", "5": "stat", "6": "vec", "7": "cplx"}

# 第2回は設問文が短く、条件が前の設問の文にだけ書かれているものがある → 1 問だけで解ける文に直す (第1回の書き方に合わせる)
PROMPT_FIX = {
    ("2", "IA", "1-1"): "A∩B の要素の個数を求めよ。",
    ("2", "IA", "1-2"): "A にも B にも属さない整数の個数を求めよ。",
    ("2", "IA", "1-5"): "辺 AC の長さを求めよ。",
    ("2", "IA", "1-6"): "辺 BC の長さを求めよ。",
    ("2", "IA", "1-7"): "三角形 ABC の面積を求めよ。",
    ("2", "IA", "1-8"): "線分 CH の長さを求めよ。",
    ("2", "IA", "1-9"): "三角形 ABC の内接円の半径はどれか。",
    ("2", "IA", "2-4"): "新しい売上額を最大にする整数 k はどれか。",
    ("2", "IA", "2-7"): "A、B の四分位範囲の組はどれか。",
    ("2", "IA", "2-8"): "四分位範囲の1.5倍を用いる外れ値の基準によると、A の外れ値はどれか。",
    ("2", "IA", "2-9"): "A、B の平均値について正しいものはどれか。",
    ("2", "IA", "2-10"): "A の各値 x を y=3x-2 に変換する。変換後の中央値と四分位範囲の組はどれか。",
    ("2", "IA", "3-1"): "cos A の値はどれか。",
    ("2", "IA", "3-2"): "三角形 ABC の面積はどれか。",
    ("2", "IA", "3-3"): "内接円の半径 r はどれか。",
    ("2", "IA", "3-4"): "接点 D について、BD の長さはどれか。",
    ("2", "IA", "3-5"): "角の二等分線と辺 BC の交点 G について、BG の長さはどれか。",
    ("2", "IA", "4-4"): "E が起こったときに F も起こる条件付き確率 P<sub>E</sub>(F) はどれか。",
    ("2", "IIBC", "1-1"): "2円の交点 P、Q の座標の組はどれか。",
    ("2", "IIBC", "1-2"): "共通弦 PQ の長さを求めよ。",
    ("2", "IIBC", "1-3"): "四角形 O<sub>1</sub>PO<sub>2</sub>Q の面積を求めよ。",
    ("2", "IIBC", "1-4"): "x 軸上の点 T=(t,0) が2円の内部または周上の両方にあるための t の範囲を求めよ。",
    ("2", "IIBC", "2-1"): "関数 h(t) の周期を求めよ。",
    ("2", "IIBC", "2-2"): "t=4.5 におけるゴンドラの高さ (m) を求めよ。",
    ("2", "IIBC", "2-3"): "0≦t≦18 での高さの最大値と、そのときの t の組を求めよ。",
    ("2", "IIBC", "2-4"): "ゴンドラの高さが21 m以上である時刻の範囲を求めよ。",
    ("2", "IIBC", "2-5"): "このゴンドラと直径の反対側にあるゴンドラを考える。2台の高さの差が最初に12 mになる時刻を求めよ。",
    ("2", "IIBC", "3-1"): "導関数 f<sub>a</sub>'(x) はどれか。",
    ("2", "IIBC", "3-2"): "極大値と極小値をとる x の記述として正しいものはどれか。",
    ("2", "IIBC", "3-3"): "x=a における曲線 y=f<sub>a</sub>(x) の接線を ℓ とする。ℓ と曲線のもう一つの交点の x 座標はどれか。",
    ("2", "IIBC", "3-4"): "曲線 y=f<sub>a</sub>(x) と x 軸との3つの交点の x 座標として正しいものはどれか。",
    ("2", "IIBC", "3-5"): "曲線 y=f<sub>a</sub>(x) と x 軸で囲まれる2つの部分の面積の和はどれか。",
    ("2", "IIBC", "3-6"): "x=a における接線を ℓ とする。曲線と ℓ で囲まれる部分の面積を S<sub>1</sub>、曲線と x 軸で囲まれる2部分の面積の和を S<sub>2</sub> とする。[[f|S_1|S_2]] はどれか。",
    ("2", "IIBC", "4-1"): "{a<sub>n</sub>} を等比数列に帰着させるため b<sub>n</sub>=a<sub>n</sub>+c とおく。適切な c と、b<sub>n</sub> の漸化式の組はどれか。",
    ("2", "IIBC", "4-3"): "S<sub>n</sub>=a<sub>1</sub>+a<sub>2</sub>+…+a<sub>n</sub> とするとき、S<sub>4</sub> はどれか。",
    ("2", "IIBC", "5-1"): "母比率 p の95%信頼区間として最も近いものはどれか。",
    ("2", "IIBC", "5-2"): "帰無仮説 H<sub>0</sub>:p=0.55、対立仮説 H<sub>1</sub>:p>0.55 として片側検定を行う。利用したいと答えた人数を X とするとき、H<sub>0</sub> のもとでの X の近似分布の平均と標準偏差はどれか。",
    ("2", "IIBC", "5-3"): "帰無仮説 H<sub>0</sub>:p=0.55、対立仮説 H<sub>1</sub>:p>0.55 として片側検定を行う。観測値290に対する標準化得点 z と上側確率の組はどれか。",
    ("2", "IIBC", "5-4"): "帰無仮説 H<sub>0</sub>:p=0.55、対立仮説 H<sub>1</sub>:p>0.55 として片側検定を行う。検定結果と標本数の影響について正しいものはどれか（「200人」は、利用したいと答えた人の比率が同じ[[f|290|500]]のまま標本数を200人にした場合）。",
    ("2", "IIBC", "6-1"): "点 P の座標はどれか。",
    ("2", "IIBC", "6-2"): "点 R の座標はどれか。",
    ("2", "IIBC", "6-3"): "ベクトル [[v|AR]] を [[v|AB]]、[[v|AC]] で表した式はどれか。",
    ("2", "IIBC", "6-4"): "交点 R が直線 x=4 上にあるとき、λ の値はどれか。",
    ("2", "IIBC", "7-1"): "w の描く図形の中心と半径の組はどれか。",
    ("2", "IIBC", "7-4"): "Im(w) が最大となるときの z はどれか。",
    # 第2回 4-5 は「E(X)」と書き、事象 E と期待値の E が同じ文字になる
    ("2", "IA", "4-5"): "2数の和が偶数ならその和を得点 X とし、和が奇数なら得点を0とする。得点 X の期待値はどれか。",
    # 第1回 5-4 の「同じ比率55/100」は 220/400 そのものとも読める (盲検で指摘) → 100 人中 55 人の場合と明記
    ("1", "IIBC", "5-4"): "検定結果と標本数の影響について正しい記述はどれか（「同じ比率[[f|55|100]]」は、標本数を100人にして、そのうち55人が「利用したい」と答えた場合）。",
}
# 1 問完結にするための設定文の直し (2026-10-06 変換の点検で指摘): (回, 科目, 元の文に含まれる語句, 置き換え後の文全体)
CONTEXT_FIX = [
    # 第2回 第2問〔1〕は売上額を R(k) と置いていない (第1回は置いている) → 2-2・2-3 で R(k) が未定義になる
    ("2", "IA", "値上げ回数をk回（0≦k≦15の整数）とする。",
     "入場料1500円では240人が来場する。100円値上げするごとに12人減る。値上げ回数をk回（0≦k≦15の整数）とし、1日の売上額を R(k) 円とする。"),
    # 第2回 第2問 (観覧車) はゴンドラも h(t) の意味も書いていない → 第1回と同じ書き方に
    ("2", "IIBC", "18分で1回転する観覧車を考える。",
     "地面から中心までの高さが15 m、半径が12 m の観覧車が、一定の速さで18分に1回転している。あるゴンドラが最下点に来た時刻を t=0 とする。0≦t≦18 におけるゴンドラの高さ h(t) m は次の式で表される。"),
    # 第2回 第5問は p も Φ も正規近似も書いていない → 第1回と同じ書き方に
    ("2", "IIBC", "500人を無作為に調査し、290人が新サービスを利用したいと答えた。",
     "ある地域で新サービスを利用したい人の割合を p とする。無作為に500人を調査したところ、290人が「利用したい」と答えた。標本は十分に大きく、正規近似を用いてよいものとする。"),
    ("2", "IIBC", "Φ(0.85)=0.8023", "標準正規分布 Z について　Φ(0.85)=0.8023, Φ(1.28)=0.8997, Φ(1.35)=0.9115, Φ(1.96)=0.9750"),
    # 第1回 第2問の「h(t) m は」の後ろの式が箱で、文が切れる
    ("1", "IIBC", "におけるゴンドラの高さ h(t) m は",
     "地面から中心までの高さが12 m、半径が10 m の観覧車が、一定の速さで12分に1回転している。あるゴンドラが最下点に来た時刻を t=0 とする。0≦t≦12 におけるゴンドラの高さ h(t) m は次の式で表される。"),
]
# 解説の直し: (回, 科目, code) → {"main": 本文を差し替え, "detail": 確認ポイントを差し替え, "replace": [(旧, 新)]}
EXPL_FIX = {
    ("1", "IA", "1-4"): {"main": "有理化すると x = 2 + √3、y = 2 - √3 より x + y = 4、xy = 1。よって x³ + y³ = (x+y)³ - 3xy(x+y) = 4³ - 3×1×4 = 52。"},
    ("2", "IA", "1-4"): {"main": "有理化すると x=[[f|3+√5|2]]、y=[[f|3-√5|2]] より x+y=3、xy=1。よって x³+y³=(x+y)³-3xy(x+y)=3³-3×1×3=18である。",
                         "detail": "立方和の公式に x+y=3、xy=1 を代入する。"},
    ("1", "IA", "1-5"): {"detail": "30°の向かいの辺は斜辺の半分になる。どの角の向かいかを、自分で図をかいて確認する。"},
    ("1", "IA", "2-10"): {"main": "一次変換 y = 2x + 5 では中央値も同じ式で変換され、四分位範囲は正の係数2倍になる。A の中央値は49、四分位範囲は6なので、変換後の中央値は 2×49+5=103、四分位範囲は 2×6=12。"},
    ("1", "IIBC", "1-4"): {"detail": "C<sub>1</sub> では -5≦t≦5、C<sub>2</sub> では1≦t≦11。両方を満たす区間だけを残す。"},
    ("1", "IIBC", "4-1"): {"detail": "a<sub>n+1</sub>+c=2a<sub>n</sub>+3+c が 2(a<sub>n</sub>+c) と等しくなるように 3+c=2c、すなわち c=3 と決める。"},
    ("1", "IIBC", "6-4"): {"replace": [("前問と同様に求めると", "2直線の式を連立して求めると")]},
}
# 第2回 IA 2-10 の選択肢は「範囲」と書いて四分位範囲を指している (調査 2026-10-06)
CHOICE_FIX = {("2", "IA", "2-10"): {"範囲": "四分位範囲"}}
# 誤答が「正解の一部だけを変えたもの」で、各部分の多数派を拾うと本文を読まずに当たる 13 問 (scan_choice_convergence.py・2026-10-06)
#   → 2×2 (各部分の値がちょうど 2 回ずつ出る) に組み直す。生成元の書き方のまま書き、正解の文は元と同じにする。
CHOICE_SET = {
    ("1", "IA", "2-1"): ["-1000k² + 8000k + 240000", "-1000k² + 12000k + 240000", "-100k² + 8000k + 240000", "-100k² + 12000k + 240000"],
    ("2", "IA", "2-1"): ["-1200k²+6000k+360000", "-1200k²+12000k+360000", "-1000k²+6000k+360000", "-1000k²+12000k+360000"],
    ("2", "IA", "2-6"): ["A:39, B:39", "A:39, B:39.5", "A:40, B:39", "A:40, B:39.5"],
    ("2", "IA", "2-10"): ["中央値115、範囲24", "中央値115、範囲22", "中央値117、範囲24", "中央値117、範囲22"],   # 「範囲」→「四分位範囲」は CHOICE_FIX が直す
    ("1", "IIBC", "1-4"): ["1≦t≦5", "1≦t≦11", "-5≦t≦5", "-5≦t≦11"],
    ("2", "IIBC", "1-4"): ["2≦t≦6", "2≦t≦14", "-6≦t≦6", "-6≦t≦14"],
    ("2", "IIBC", "1-2"): ["4√5", "4√3", "2√5", "2√3"],
    ("1", "IIBC", "2-3"): ["22 m, t=6", "22 m, t=3", "20 m, t=6", "20 m, t=3"],
    ("2", "IIBC", "2-3"): ["27 m,t=9", "27 m,t=4.5", "24 m,t=9", "24 m,t=4.5"],
    ("1", "IIBC", "3-2"): ["x=-√aで極大、x=√aで極小", "x=-√aで極小、x=√aで極大", "x=-aで極大、x=aで極小", "x=-aで極小、x=aで極大"],
    ("2", "IIBC", "3-2"): ["-aで極大、aで極小", "-aで極小、aで極大", "-√aで極大、√aで極小", "-√aで極小、√aで極大"],
    ("1", "IIBC", "6-2"): ["(3,1)", "(3,[[f|4|3]])", "(2,1)", "(2,[[f|4|3]])"],
    ("1", "IIBC", "7-1"): ["中心(-[[f|1|3]],0), 半径[[f|2|3]]", "中心(-[[f|1|3]],0), 半径[[f|1|3]]", "中心([[f|1|3]],0), 半径[[f|2|3]]", "中心([[f|1|3]],0), 半径[[f|1|3]]"],
}
# 数値の選択肢 65 問で、正解が「2 番目に大きい値」に 45% 偏っていた (元の誤答の作り方・巡回では変わらない。コミット前レビュー 2026-10-06)
#   → 6 問の誤答を 1 つずつ、正解の反対側にある典型的な誤りに入れ替える (順位の分布 6/16/29/14 → 6/20/23/16)
CHOICE_SET.update({
    ("1", "IA", "2-2"): ["3", "4", "5", "8"],                       # 8 = 頂点の公式で 2 を落とした (8000/1000)
    ("2", "IA", "1-3"): ["6", "7", "8", "9"],                       # 9 = (x+y)² で 2xy を引き忘れた
    ("1", "IIBC", "1-3"): ["20", "24", "30", "48"],                 # 48 = 対角線の積で ½ を忘れた
    ("2", "IA", "3-4"): ["[[f|3|2]]", "2", "3", "4"],               # 4 = AD (=s-BC) を BD と取り違えた
    ("1", "IIBC", "4-4"): ["3", "4", "5", "6"],                     # 項の数え違い
    ("2", "IIBC", "4-4"): ["2", "3", "4", "5"],                     # 項の数え違い
})
DROP = {}   # {(回, 科目, code): 理由}

problems = []


# ───────── 生成元を読み込み、reportlab の部品を記録用に差し替える ─────────
def load_sources():
    spec = importlib.util.spec_from_file_location("common_test_set2_reader", os.path.join(SRC, "build_mock_exams_set2.py"))
    s2 = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = s2
    cwd = os.getcwd()
    try:
        os.chdir(SRC)
        spec.loader.exec_module(s2)
    finally:
        os.chdir(cwd)
    m = s2.m   # 第1回 (set2 が読み込んだもの)

    class FakeTable:
        def __init__(self, rows, *a, **k):
            self.rows = rows

        def setStyle(self, *a, **k):
            pass

    class FakeDoc:
        captured = []

        def __init__(self, *a, **k):
            pass

        def build(self, st):
            FakeDoc.captured.append(st)

    def P(text, style="body"):
        return ("P", text, style)

    for mod in (m, s2):
        mod.P = P
        mod.Table = FakeTable
        mod.Spacer = lambda *a, **k: None
        mod.PageBreak = lambda *a, **k: None
    m.formula_box = lambda text, accent=None: ("F", text)
    m.info_box = lambda text, accent=None: ("I", text)
    m.banner = lambda text, accent=None: ("B", text)
    m.mcq = lambda code, prompt, choices, points: [("Q", code, prompt, list(choices), points)]
    m.answer_sheet = lambda *a, **k: []
    m.ExamDoc = FakeDoc
    for name in dir(m):
        if name.endswith("Diagram"):
            setattr(m, name, (lambda n: (lambda *a, **k: ("FIG", n)))(name))
    s2.FIG = {k: (lambda kk: (lambda: ("FIG", kk)))(k) for k in s2.FIG}

    out = {}
    for (ed, subj), fn in ((("1", "IA"), m.build_ia_problem), (("1", "IIBC"), m.build_iibc_problem),
                           (("2", "IA"), s2.build_ia2_problem), (("2", "IIBC"), s2.build_iibc2_problem)):
        FakeDoc.captured.clear()
        fn("/dev/null")
        assert len(FakeDoc.captured) == 1
        out[(ed, subj)] = FakeDoc.captured[0]
    sols = {("1", "IA"): [m.IA_Q1, m.IA_Q2, m.IA_Q3, m.IA_Q4],
            ("1", "IIBC"): [m.IIBC_Q1, m.IIBC_Q2, m.IIBC_Q3, m.IIBC_Q4, m.IIBC_Q5, m.IIBC_Q6, m.IIBC_Q7],
            ("2", "IA"): [s2.IA2_Q1, s2.IA2_Q2, s2.IA2_Q3, s2.IA2_Q4],
            ("2", "IIBC"): [s2.IIBC2_Q1, s2.IIBC2_Q2, s2.IIBC2_Q3, s2.IIBC2_Q4, s2.IIBC2_Q5, s2.IIBC2_Q6, s2.IIBC2_Q7]}
    details = {("1", "IA"): m.IA_DETAIL_POINTS, ("1", "IIBC"): m.IIBC_DETAIL_POINTS}
    for k, cand in ((("2", "IA"), ("IA2_DETAIL_TEXT", "IA2_DETAIL_POINTS")), (("2", "IIBC"), ("IIBC2_DETAIL_TEXT", "IIBC2_DETAIL_POINTS"))):
        details[k] = next((getattr(s2, c) for c in cand if hasattr(s2, c)), {})
    letters = m.ANSWER_DIGIT
    return out, sols, details, letters


# ───────── 記法の変換 ─────────
SUP = {"²": "2", "³": "3", "⁴": "4"}


def tex_inner(s):
    """[[f|..]] の分子・分母や ∫ の端など、\\( \\) の中に入る部分を LaTeX にする。"""
    s = s.replace("&lt;", "<").replace("&gt;", ">")
    s = re.sub(r"<sub>(.*?)</sub>", r"_{\1}", s)
    s = re.sub(r"<super>(.*?)</super>", r"^{\1}", s)
    s = re.sub(r"√\(((?:[^()]|\([^()]*\))*)\)", r"\\sqrt{\1}", s)
    s = re.sub(r"√(\d+(?:\.\d+)?|[a-zA-Z])", r"\\sqrt{\1}", s)
    for k, v in SUP.items():
        s = s.replace(k, "^{" + v + "}")
    s = re.sub(r"(\w)の共役", r"\\overline{\1}", s)   # [[f|wの共役|｜w｜²]] → \frac{\overline{w}}{|w|^{2}}
    s = s.replace("｜", "|")
    s = (s.replace("×", r"\times ").replace("π", r"\pi ").replace("−", "-").replace("・", r"\cdot ").replace("°", r"^{\circ}")
         .replace("λ", r"\lambda ").replace("∩", r"\cap ").replace("∪", r"\cup ").replace("≦", r"\leqq ").replace("≧", r"\geqq "))
    return s.strip()


def to_text(s):
    """生成元の文字列 → ドリル用 (LaTeX は \\( \\) で囲む・それ以外は文字のまま)。"""
    s = str(s)
    s = s.replace("<br/>", " ").replace("<br>", " ")
    s = re.sub(r"</?(b|u)>", "", s)
    segs = []

    def keep(tex):
        segs.append(tex)
        return f"\x00{len(segs) - 1}\x00"
    # 独自記法
    s = re.sub(r"\[\[f\|([^|\]]*)\|([^|\]]*)\]\]", lambda mm: keep(r"\frac{%s}{%s}" % (tex_inner(mm.group(1)), tex_inner(mm.group(2)))), s)
    s = re.sub(r"\[\[v\|([^|\]]*)\]\]", lambda mm: keep(r"\overrightarrow{\mathrm{%s}}" % mm.group(1)), s)
    s = re.sub(r"\[\[o\|([^|\]]*)\|([^|\]]*)\|([^|\]]*)\]\]",
               lambda mm: keep((r"\int" if mm.group(1) == "∫" else r"\sum") + r"_{%s}^{%s}" % (tex_inner(mm.group(2)), tex_inner(mm.group(3)))), s)
    # 前に付く添字 (₃C₂) と、記号の後ろの添字・指数
    s = re.sub(r"(?<![A-Za-z0-9)])<sub>([^<]*)</sub>([A-Z])<sub>([^<]*)</sub>", lambda mm: keep(r"{}_{%s}\mathrm{%s}_{%s}" % (mm.group(1), mm.group(2), mm.group(3))), s)
    s = re.sub(r"([A-Za-zΦ\d)]+)<sub>([^<]*)</sub>", lambda mm: keep("%s_{%s}" % (mm.group(1), tex_inner(mm.group(2)))), s)
    s = re.sub(r"([A-Za-z\d)]+)<super>([^<]*)</super>", lambda mm: keep("%s^{%s}" % (mm.group(1), tex_inner(mm.group(2)))), s)
    # 根号 (中に分数などの数式があるときは、その LaTeX を中に戻してから包む)
    def raw(x):
        return re.sub(r"\x00(\d+)\x00", lambda mm: segs[int(mm.group(1))], x)
    s = re.sub(r"√\(((?:[^()]|\([^()]*\))*)\)", lambda mm: keep(r"\sqrt{%s}" % tex_inner(raw(mm.group(1)))), s)
    s = re.sub(r"√(\d+(?:\.\d+)?|[a-zA-Z])", lambda mm: keep(r"\sqrt{%s}" % mm.group(1)), s)
    s = s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    # 隣り合う数式は 1 つにまとめる (例: 3 と √3 の間には何もない → 3\sqrt{3} にはせず、文字の 3 の後ろに \(\sqrt{3}\) を置く)
    s = re.sub(r"\x00(\d+)\x00", lambda mm: r"\(" + segs[int(mm.group(1))] + r"\)", s)
    s = s.replace(r"\)\(", " ")  # 連続した数式の境目を詰める (\(a\)\(b\) → \(a b\))
    if re.search(r"\[\[|<sub>|<super>|</?b>|\x00", s):
        problems.append(f"変換し残し: {s[:80]}")
    return re.sub(r"[ \t　]+", " ", s).strip()


def drop_figure_refs(s):
    s = re.sub(r"と箱ひげ図(?=は)", "", s)              # 「データと箱ひげ図は次のとおり」→「データは次のとおり」(表は文字で出す)
    s = re.sub(r"図のように、?", "", s)
    s = re.sub(r"(?:^|(?<=[。、\s]))図は[^。]*。", "", s)   # 「図は a=1 の場合である。」
    return s.strip()


def fix_context(ed, subj, t):
    for e, sj, frag, repl in CONTEXT_FIX:
        if e == ed and sj == subj and frag in t:
            return repl
    return t


# ───────── 問題冊子の並び → 1 問ずつの 4 択 ─────────
def items_from_story(st, ed, subj):
    out = []
    ctx = []
    for el in st:
        if el is None:
            continue
        if isinstance(el, tuple):
            kind = el[0]
            if kind == "B":
                ctx = []
            elif kind == "P":
                text, style = el[1], el[2]
                if style == "subhead":
                    ctx = []
                elif style in ("tiny", "center", "small"):
                    pass
                else:
                    t = drop_figure_refs(text)
                    if t.startswith("次に、正の数"):
                        ctx = []   # 〔１〕の後半 (x, y の式の値) は前半の集合の設定を使わない
                        t = t[len("次に、"):]
                    if t:
                        ctx.append(fix_context(ed, subj, t))
            elif kind in ("F", "I"):
                t = el[1].replace("　　", "、") if kind == "F" else el[1]
                ctx.append(fix_context(ed, subj, t))
            elif kind == "FIG":
                pass
            elif kind == "Q":
                _, code, prompt, choices, pts = el
                out.append({"ed": ed, "subj": subj, "code": code, "ctx": list(ctx), "prompt": prompt, "choices": choices})
        elif type(el).__name__ == "FakeTable":
            rows = el.rows
            if rows and any("問題" == (c[1] if isinstance(c, tuple) else "") for c in rows[0]):
                continue   # 選択問題の説明表 (大問の前)
            lines = []
            for r in rows[1:]:
                cells = [c[1] for c in r if isinstance(c, tuple)]
                if len(cells) >= 2:
                    lines.append(f"{cells[0]}：{cells[1]}")
            head = [c[1] for c in rows[0] if isinstance(c, tuple)]
            ctx.append("\n".join(([head[1]] if len(head) > 1 else []) + lines))
        else:
            problems.append(f"{ed}-{subj}: 想定外の要素 {type(el).__name__}")
    return out


def rotate(choices, ans, target):
    r = (target - ans) % 4
    return [choices[(i - r) % 4] for i in range(4)], target


def build():
    stories, sols, details, letters = load_sources()
    qs = []
    for (ed, subj), st in stories.items():
        items = items_from_story(st, ed, subj)
        sol = {s.code: s for group in sols[(ed, subj)] for s in group}
        want = 29 if subj == "IA" else 32
        if len(items) != want:
            problems.append(f"第{ed}回 {subj}: 設問 {len(items)} (想定 {want})")
        for it in items:
            key = (ed, subj, it["code"])
            if key in DROP:
                continue
            s = sol.get(it["code"])
            if s is None:
                problems.append(f"{key}: 正解 (Sol) が無い"); continue
            ai = int(letters[s.answer])
            prompt = PROMPT_FIX.get(key, it["prompt"])
            choices = list(it["choices"])
            if key in CHOICE_SET:
                correct = choices[ai]
                if correct not in CHOICE_SET[key] or len(set(CHOICE_SET[key])) != 4:
                    problems.append(f"{key}: CHOICE_SET に元の正解 {correct!r} が無い / 4 つ相異でない")
                else:
                    choices = list(CHOICE_SET[key])
                    ai = choices.index(correct)
            for a, b in (CHOICE_FIX.get(key) or {}).items():
                choices = [re.sub(r"(?<!四分位)" + re.escape(a), b, c) for c in choices]
            stem = "\n".join([to_text(c) for c in it["ctx"]] + [to_text(prompt)])
            ch = [to_text(c) for c in choices]
            det = (details.get((ed, subj)) or {}).get(it["code"])
            fx = EXPL_FIX.get(key) or {}
            main = fx.get("main", s.explanation)
            det = fx.get("detail", det)
            for a_, b_ in fx.get("replace", []):
                if a_ not in main:
                    problems.append(f"{key}: EXPL_FIX の置換元が解説に無い: {a_}")
                main = main.replace(a_, b_)
            expl = to_text(main) + (f"\n【確認ポイント】{to_text(det)}" if det else "")
            unit = U[UNIT_IA[it["code"]]] if subj == "IA" else U[UNIT_IIBC[it["code"].split("-")[0]]]
            qs.append({"subject": "math", "unit": unit, "level": "standard", "stem": stem, "choices": ch, "answer": ai,
                       "explanation": expl, "source": f"mathct-r{ed}-{subj.lower()}-{it['code']}"})
    # 正解の位置を単元ごとに 4 位置へ順に配る (巡回なので数値の大小の並びは保たれる)
    counter = collections.Counter()
    for q in sorted(qs, key=lambda x: (x["unit"], x["source"])):
        target = counter[q["unit"]] % 4
        counter[q["unit"]] += 1
        q["choices"], q["answer"] = rotate(q["choices"], q["answer"], target)
    return qs


def validate(qs):
    seen = {}
    for q in qs:
        src = q["source"]
        if len(q["choices"]) != 4 or len({c.strip() for c in q["choices"]}) != 4 or any(not c.strip() for c in q["choices"]):
            problems.append(f"{src}: 選択肢が 4 つ相異でない {q['choices']}")
        if not (0 <= q["answer"] <= 3):
            problems.append(f"{src}: answer 範囲外")
        if re.search(r"[⓪①②③④]|選択肢\s*[0-9０-９]|[アイウエ](?:の解答群|が正解)", q["explanation"] + q["stem"]):
            problems.append(f"{src}: 番号・記号の参照が残る")
        if re.search(r"図(?:のように|は|に示|の)", q["stem"]):
            problems.append(f"{src}: stem に図への言及")
        for t in [q["stem"], q["explanation"]] + q["choices"]:
            if t.count(r"\(") != t.count(r"\)"):
                problems.append(f"{src}: \\( \\) の数が合わない: {t[:60]}")
        k = q["stem"].strip()
        if k in seen:
            problems.append(f"{src}: stem が {seen[k]} と重複")
        seen[k] = src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind", default=None)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    qs = build()
    validate(qs)
    by_unit = collections.Counter(q["unit"] for q in qs)
    pos = collections.defaultdict(collections.Counter)
    for q in qs:
        pos[q["unit"]][q["answer"]] += 1
    print("問題数:", len(qs))
    for u, n in sorted(by_unit.items()):
        print(f"  {u}: {n} 問 正解位置 {dict(sorted(pos[u].items()))}")
    if problems:
        print(f"\n❌ 検査 NG {len(problems)} 件 (書き出しません):")
        for p in problems[:80]:
            print("  -", p)
        sys.exit(1)
    if a.blind:
        os.makedirs(a.blind, exist_ok=True)
        blind = [{"id": "M-" + hashlib.sha1(q["stem"].encode()).hexdigest()[:8], "unit": q["unit"], "stem": q["stem"], "choices": q["choices"]} for q in qs]
        assert len({b["id"] for b in blind}) == len(blind)
        key = {b["id"]: {"answer": q["choices"][q["answer"]], "source": q["source"]} for b, q in zip(blind, qs)}
        json.dump(blind, open(os.path.join(a.blind, "blind_math_ct.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(key, open(os.path.join(a.blind, "key_math_ct.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"盲検用: {a.blind}/blind_math_ct.json ({len(blind)} 問)")
        return
    meta = {"name": "math_drill_ct_mock_v1", "created": date.today().isoformat(), "subject": "math", "units": dict(sorted(by_unit.items())),
            "sources": ["共通テスト数学 第1回・第2回オリジナル模試 (Desktop/📚 教材/数学/04_模試・共通テスト/math_common_test_mock（生成元）/build_mock_exams.py・build_mock_exams_set2.py)"],
            "blind_review": BLIND_NOTE,
            "note": "全部この塾のオリジナル (過去問なし)。大問の設定文を各設問の stem に付けた 1 問完結の 4 択。数式は \\( \\) の LaTeX。単元名は入試道場の topic と同じ。level は全問 standard。"}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": meta, "questions": qs}, ensure_ascii=False, indent=1) + "\n")
    print("✅", a.out, len(qs), "問")


BLIND_NOTE = ("盲検 (2026-10-06): 正解を伏せた独立ソルバー 3 名が全 122 問を解き 121 問が全員一致・指摘なし。残る 1 問 (第1回 ⅡBC 5-4 の「同じ比率55/100」) "
              "と変換の照合 2 名の指摘 (設定文の不足・前問参照など) を PROMPT_FIX/CONTEXT_FIX/EXPL_FIX で直し、文が変わった 35 問を 3 名で解き直して全員一致。"
              "誤答を 2×2 に組み直した 13 問と、正解の値の順位の偏りを直した 6 問 (CHOICE_SET) も 3 名で解き直して全員一致。生の解答はコミットしない。")

if __name__ == "__main__":
    main()
