#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 比較 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/hikaku1/build_hikaku1.py

出力 (どちらも**コミットする**。取り込みセッションが git 経由で受け取るため):
    英文法_比較_第1集.json        … import_books.py にそのまま渡す bundle
    英文法_比較_第1集_問題.pdf    … 冊子 (find_pdf の完全一致名: {source の stem}_問題.pdf)

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同じデータから
  同時に生成する (kateiho2 と同じ作り)。
★ 正解の位置は 1:2 問 / 2:3 問 / 3:3 問 / 4:2 問 に配ってある
  (CLAUDE.md「正解番号は偏らせない」)。設問を足したら配り直すこと。
★ 解説は英語教材の 4 セクション形式 (コアイメージ → 文構造分析 → 根拠 → 誤答 NG 理由)。
  番号と選択肢のずれは _grammar_build.verify() が機械で落とす。

取り込み (kamitest-import 環境のセッション or Mac):
    python3 scripts/book_exam/import_books.py scripts/book_exam/materials/hikaku1 \
        --pdf-dir scripts/book_exam/materials/hikaku1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_比較_第1集"
TITLE = "英文法 比較 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

# (番号, ページ, 設問文, [選択肢1..4], 正解番号(1起算), 配点, unit_tag, 解説)
QUESTIONS = [
    (1, 1,
     "Tom can run as (          ) as his older brother.",
     ["faster", "fastest", "more fast", "fast"], 4, 2, "HIKAKU-GENKYU",
     "## 🎯 コアイメージ\n"
     "as 〜 as の間に挟むのは**原級** (もとの形)。「同じくらい〜」は比べる 2 つを"
     "同じ高さに置くイメージ。\n\n"
     "## 🔬 文構造分析\n"
     "Tom can run **as fast as** his older brother.\n"
     "run を修飾する副詞 fast が as 〜 as に挟まれる。as + 原級 + as の型。\n\n"
     "## 📍 正解の根拠\n"
     "as 〜 as の間は原級と決まっている → **fast**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. faster — 比較級。as 〜 as の間には置けない (比較級は than とペア)。\n"
     "2. fastest — 最上級。同じく as 〜 as の型に合わない。\n"
     "3. more fast — fast は短い語なので比較級でも faster。more は付けない (しかもここは原級の位置)。"),

    (2, 1,
     "This problem is much (          ) than it looks.",
     ["difficult", "more difficult", "most difficult", "the more difficult"], 2, 2,
     "HIKAKU-HIKAKU",
     "## 🎯 コアイメージ\n"
     "**than** が見えたら比較級。difficult のような長い形容詞は more を前に置いて"
     "比較級を作る。much は比較級の強調「ずっと」。\n\n"
     "## 🔬 文構造分析\n"
     "This problem is much **more difficult than** it looks.\n"
     "more difficult (比較級) + than 〜。much が比較級全体を強めている。\n\n"
     "## 📍 正解の根拠\n"
     "後ろに than がある以上、空所は比較級 **more difficult** の一択。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. difficult — 原級。than と組めない (原級は as 〜 as とペア)。\n"
     "3. most difficult — 最上級。than と組めない。\n"
     "4. the more difficult — the が余計。「2 つのうちでより〜」(the + 比較級 of the two) は別の構文。"),

    (3, 1,
     "Mt. Fuji is (          ) mountain in Japan.",
     ["higher", "the higher", "the highest", "the most high"], 3, 2, "HIKAKU-SAIJO",
     "## 🎯 コアイメージ\n"
     "「〜の中で一番」は **the + 最上級**。範囲は in + 場所 / of + 複数 で示す。\n\n"
     "## 🔬 文構造分析\n"
     "Mt. Fuji is **the highest** mountain **in Japan**.\n"
     "in Japan という範囲の中の一番 → 最上級 highest に the を付ける。\n\n"
     "## 📍 正解の根拠\n"
     "in Japan があるので「日本で一番高い」= **the highest**。high は短い語なので "
     "-est 型。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. higher — 比較級。than も無く、「一番」の意味も出ない。\n"
     "2. the higher — the + 比較級は「2 つのうちの高い方」(of the two)。範囲 in Japan と合わない。\n"
     "4. the most high — high のような短い語は most でなく -est で最上級を作る。"),

    (4, 2,
     "The more you practice, (          ) you will become.",
     ["the better", "better", "the best", "good"], 1, 2, "HIKAKU-SOUKAN",
     "## 🎯 コアイメージ\n"
     "**The + 比較級 〜, the + 比較級 …** =「〜すればするほど、ますます…」。"
     "前後がセットの相関構文で、**両方に the** が要る。\n\n"
     "## 🔬 文構造分析\n"
     "**The more** you practice, **the better** you will become.\n"
     "前半 The more とペアを組む後半も the + 比較級。you will become (the) better "
     "の better が前に出た形。\n\n"
     "## 📍 正解の根拠\n"
     "The more 〜 で始まっている以上、後半は **the better** で受けるのが型。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. better — 比較級だが the が無い。この相関構文では the を省けない。\n"
     "3. the best — 最上級。「するほど、ますます」の比例関係を作れない。\n"
     "4. good — 原級。比例関係の型に合わない。"),

    (5, 2,
     "He had (          ) five hundred yen with him, so he couldn't buy the book.",
     ["not less than", "no more than", "not more than", "no less than"], 2, 2,
     "HIKAKU-KANYO",
     "## 🎯 コアイメージ\n"
     "no + 比較級は**気持ちを込めた強調**: no more than =「**たった**〜しか」"
     "(= only)。not + 比較級は客観的な上限・下限 (= at most / at least)。\n\n"
     "## 🔬 文構造分析\n"
     "He had **no more than** five hundred yen with him, so he couldn't buy the "
     "book.\n"
     "so 以下「本が買えなかった」= 所持金の**少なさ**を嘆く文脈。\n\n"
     "## 📍 正解の根拠\n"
     "「500 円**しか**持っていなかった (から買えなかった)」— 少なさの強調 = "
     "**no more than**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. not less than —「少なくとも 500 円」(= at least)。多い方向の含みで文脈と合わない。\n"
     "3. not more than —「多くても 500 円」(= at most)。客観的な上限を言うだけで、「たった」の嘆きが出ない。\n"
     "4. no less than —「500 円**も**」(= as much as)。多さの強調で、買えなかった文脈と矛盾する。"),

    (6, 2,
     "This bridge is (          ) as long as that one.",
     ["three times more", "as three times", "more three times", "three times"], 4, 2,
     "HIKAKU-BAISU",
     "## 🎯 コアイメージ\n"
     "倍数は **X times + as + 原級 + as** の語順。「3 倍長い」は、3 倍という係数を "
     "as 〜 as の**前**に置く。\n\n"
     "## 🔬 文構造分析\n"
     "This bridge is **three times as long as** that one.\n"
     "three times (3 倍) が as long as (同じ長さ) の前に係数として乗る。\n\n"
     "## 📍 正解の根拠\n"
     "as long as が既にあるので、空所に入るのは倍数の係数 **three times** だけで"
     "よい。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. three times more — more と as long as が二重になり形が壊れる (three times longer than なら別の型)。\n"
     "2. as three times — as が先に来るこの語順は無い。\n"
     "3. more three times — この語順も存在しない。"),

    (7, 3,
     "(          ) other student in the class is as diligent as Ken.",
     ["No", "Not", "None", "Nothing"], 1, 2, "HIKAKU-HITEI",
     "## 🎯 コアイメージ\n"
     "**No other + 単数名詞 + as 原級 as A** =「A ほど〜な…は他にない」。原級・"
     "比較級で**最上級の内容**を言い換える定番の型。\n\n"
     "## 🔬 文構造分析\n"
     "**No other student** in the class is as diligent as Ken.\n"
     "= Ken is the most diligent student in the class。No が名詞 student を直接"
     "打ち消して主語のかたまりを作る。\n\n"
     "## 📍 正解の根拠\n"
     "名詞 (other student) を直接修飾して「〜な生徒は 1 人もいない」と言えるのは"
     "形容詞の **No**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. Not — 副詞。名詞をじかに修飾して主語のかたまりを作ることはできない。\n"
     "3. None — 代名詞。名詞を続けるなら none of the students の形が要る。\n"
     "4. Nothing —「何も〜ない」の代名詞。直後に other student は続けられない。"),

    (8, 3,
     "This new model is (          ) the old one in every respect.",
     ["more superior than", "superior than", "superior to", "the superior of"], 3, 2,
     "HIKAKU-LATIN",
     "## 🎯 コアイメージ\n"
     "ラテン語系の比較 (superior / inferior / senior / junior など) は、それ自体に"
     "比較の意味を含み、相手は **than でなく to** で示す。\n\n"
     "## 🔬 文構造分析\n"
     "This new model is **superior to** the old one in every respect.\n"
     "superior (優れている) + to + 比較の相手 (the old one)。\n\n"
     "## 📍 正解の根拠\n"
     "superior の比較相手は **to** で示す — superior to で「〜より優れている」。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. more superior than — superior 自体が比較の意味を持つので more を重ねない。相手も than でなく to。\n"
     "2. superior than — 相手の示し方が誤り。than でなく to。\n"
     "4. the superior of — the superior は「目上の人」という名詞用法で、ここの形には合わない。"),

    (9, 3,
     "He is not so much a novelist (          ) a journalist.",
     ["but", "as", "than", "so"], 2, 2, "HIKAKU-KANYO",
     "## 🎯 コアイメージ\n"
     "**not so much A as B** =「A というより (むしろ) B」。as 〜 as の原級比較を"
     "否定して「A の度合いは B ほどではない」→「むしろ B」。\n\n"
     "## 🔬 文構造分析\n"
     "He is not **so much** a novelist **as** a journalist.\n"
     "so much A ... as B の呼応。A = a novelist、B = a journalist。\n\n"
     "## 📍 正解の根拠\n"
     "前半に not so much がある以上、受けるのは **as** — not so much A as B "
     "の型。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. but — not A but B (A でなく B) は so much が付かない別の型。\n"
     "3. than — 比較級が無いので than は呼応しない (so much は原級の系統)。\n"
     "4. so — so 〜 so と重ねる型は無い。"),

    (10, 3,
     "The Tone is the (          ) longest river in Japan.",
     ["two", "twice", "second", "double"], 3, 2, "HIKAKU-JOSU",
     "## 🎯 コアイメージ\n"
     "「◯番目に〜」は **the + 序数 + 最上級**。順位のはしごを上から数える言い方。\n\n"
     "## 🔬 文構造分析\n"
     "The Tone is the **second longest** river in Japan.\n"
     "the + second (序数) + longest (最上級) + 名詞。利根川は信濃川に次いで日本で "
     "2 番目に長い。\n\n"
     "## 📍 正解の根拠\n"
     "「日本で **2 番目に**長い川」→ 序数 **second** を最上級 longest の前に"
     "置く。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. two — 基数。「2 番目」という順位は序数で表す。\n"
     "2. twice —「2 回・2 倍」。順位の意味は無い。\n"
     "4. double —「2 倍の」。同じく順位は表せない。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
