#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 関係詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/kankeishi1/build_kankeishi1.py

出力 (どちらも**コミットする**。取り込みセッションが git 経由で受け取るため):
    英文法_関係詞_第1集.json        … import_books.py にそのまま渡す bundle
    英文法_関係詞_第1集_問題.pdf    … 冊子 (find_pdf の完全一致名: {source の stem}_問題.pdf)

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同じデータから
  同時に生成する (kateiho2 と同じ作り)。
★ 正解の位置は 1:2 問 / 2:3 問 / 3:3 問 / 4:2 問 に配ってある
  (CLAUDE.md「正解番号は偏らせない」)。設問を足したら配り直すこと。
★ 解説は英語教材の 4 セクション形式 (コアイメージ → 文構造分析 → 根拠 → 誤答 NG 理由)。
  番号と選択肢のずれは _grammar_build.verify() が機械で落とす。

取り込み (kamitest-import 環境のセッション or Mac):
    python3 scripts/book_exam/import_books.py scripts/book_exam/materials/kankeishi1 \
        --pdf-dir scripts/book_exam/materials/kankeishi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_関係詞_第1集"
TITLE = "英文法 関係詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

# (番号, ページ, 設問文, [選択肢1..4], 正解番号(1起算), 配点, unit_tag, 解説)
QUESTIONS = [
    (1, 1,
     "The woman (          ) lives next door is a doctor.",
     ["whom", "who", "whose", "which"], 2, 2, "KANKEI-SHUKAKU",
     "## 🎯 コアイメージ\n"
     "関係代名詞は「格」で選ぶ。**空所の後ろに何が欠けているか**を見る: "
     "動詞がいきなり続く → 主語が欠けている → 主格。\n\n"
     "## 🔬 文構造分析\n"
     "The woman **who lives** next door is a doctor.\n"
     "who lives next door が The woman を修飾。空所の直後が動詞 lives — "
     "節の中で**主語**の働きをする主格の関係代名詞が要る。\n\n"
     "## 📍 正解の根拠\n"
     "先行詞 The woman = 人、節内の役割 = 主語。人 + 主格 = **who**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. whom — 目的格。後ろに「主語 + 動詞」が続く形 (The woman whom I met) で使う。\n"
     "3. whose — 所有格。後ろには名詞が続く (whose husband など)。動詞 lives とはつながらない。\n"
     "4. which — 先行詞が物のときの関係代名詞。The woman (人) は受けられない。"),

    (2, 1,
     "(          ) he said at the meeting surprised everyone.",
     ["That", "Which", "Who", "What"], 4, 2, "KANKEI-WHAT",
     "## 🎯 コアイメージ\n"
     "what は**先行詞を自分の中に含む**関係代名詞: what = the thing(s) which"
     "「〜すること・もの」。名詞のかたまりを作って、文の主語や目的語になれる。\n\n"
     "## 🔬 文構造分析\n"
     "**What he said** at the meeting **surprised** everyone.\n"
     "What he said (彼が言ったこと) 全体がこの文の主語。said の目的語が欠けた"
     "**不完全な文**を what が引き受けている。\n\n"
     "## 📍 正解の根拠\n"
     "空所の前に先行詞が無く、節の中は said の目的語が欠けた不完全な文 — "
     "先行詞を含む **What** の出番。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. That — that 節が主語になるなら中は**完全な文**のはず。said の目的語が無く形が壊れる。\n"
     "2. Which — 関係代名詞の which には先行詞が必要。文頭に先行詞なしでは置けない。\n"
     "3. Who —「〜する人」の意味で先行詞なしには使えない (those who なら可)。"),

    (3, 1,
     "This is the town (          ) I was born.",
     ["where", "which", "what", "who"], 1, 2, "KANKEI-FUKUSHI",
     "## 🎯 コアイメージ\n"
     "関係副詞は「**後ろが完全な文**」のときに使う。関係代名詞 (which など) は"
     "節内に名詞の欠けが要る — この違いだけで大半の問題は解ける。\n\n"
     "## 🔬 文構造分析\n"
     "This is the town **where I was born**.\n"
     "I was born は主語も述語もそろった**完全な文**。場所の先行詞 the town + "
     "完全な文 = 関係副詞 where。\n\n"
     "## 📍 正解の根拠\n"
     "where = in which。「その町**で**生まれた」という副詞の働きを関係詞が兼ねる"
     "ので、後ろは完全な文でよい。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. which — 節内に名詞の欠けが必要。使うなら the town in which I was born と前置詞が要る。\n"
     "3. what — 先行詞を含む関係代名詞。the town という先行詞と同時には使えない。\n"
     "4. who — 人を受ける関係代名詞。先行詞 the town (場所) に合わない。"),

    (4, 2,
     "The house in (          ) they live was built fifty years ago.",
     ["that", "where", "which", "whom"], 3, 2, "KANKEI-ZENCHI",
     "## 🎯 コアイメージ\n"
     "live **in** the house の in を関係代名詞の前に引き出した形が「前置詞 + 関係"
     "代名詞」。前置詞の直後に置ける関係代名詞は **which (物) / whom (人)** だけ。\n\n"
     "## 🔬 文構造分析\n"
     "The house **in which they live** was built fifty years ago.\n"
     "they live in the house → in を which の前へ。in which they live が "
     "The house を修飾する。\n\n"
     "## 📍 正解の根拠\n"
     "先行詞 The house = 物、前置詞 in の直後 → **which**。in which = where と"
     "置き換えられる。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. that — 関係代名詞 that は**前置詞の直後には置けない** (in that ×)。\n"
     "2. where — 関係副詞は in の意味をすでに含む。in where では前置詞が二重になる。\n"
     "4. whom — 人を受ける目的格。先行詞 The house (物) に合わない。"),

    (5, 2,
     "He failed the exam, (          ) disappointed his parents.",
     ["that", "what", "who", "which"], 4, 2, "KANKEI-HISEIGEN",
     "## 🎯 コアイメージ\n"
     "コンマ付きの関係詞 (非制限用法) は先行詞に**補足説明**を加える。which は"
     "名詞だけでなく、**前の文の内容まるごと**を先行詞にできる。\n\n"
     "## 🔬 文構造分析\n"
     "He failed the exam, **which disappointed** his parents.\n"
     "which の先行詞は「彼が試験に落ちたこと」という前半の内容全体。それが主語に"
     "なって disappointed につながる。\n\n"
     "## 📍 正解の根拠\n"
     "コンマの後ろで、前文の内容を受けて「そのことが両親を落胆させた」と言えるのは "
     "**which** だけ。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. that — 関係代名詞 that は**コンマ付きの非制限用法では使えない**。\n"
     "2. what — 先行詞を含む関係代名詞。前の内容に補足を付けるコンマ用法は無い。\n"
     "3. who — 人を受ける。「落ちたこと」という出来事は受けられない。"),

    (6, 2,
     "(          ) comes first will get the best seat.",
     ["Who", "Whoever", "Whomever", "However"], 2, 2, "KANKEI-FUKUGO",
     "## 🎯 コアイメージ\n"
     "複合関係代名詞 whoever = **anyone who**「〜する人は誰でも」。それ自体が"
     "名詞のかたまりを作り、文の主語になれる。\n\n"
     "## 🔬 文構造分析\n"
     "**Whoever comes first** will get the best seat.\n"
     "Whoever comes first (最初に来る人は誰でも) が主語。空所の直後が動詞 comes "
     "なので、節の中では**主格**。\n\n"
     "## 📍 正解の根拠\n"
     "「誰でも」の意味 + 節内で主語の働き = 主格の **Whoever**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Who — 疑問詞だと「誰が最初に来るか」という**問い**が主語になり、「席を取る」動作の主体にならない。\n"
     "3. Whomever — 目的格。直後に動詞 comes が続く主語の位置には置けない。\n"
     "4. However —「どんなに〜でも」。直後には形容詞・副詞が来る形で、名詞のかたまりを作れない。"),

    (7, 3,
     "The book (          ) you lent me last week was really interesting.",
     ["whose", "whom", "which", "what"], 3, 2, "KANKEI-MOKKAKU",
     "## 🎯 コアイメージ\n"
     "空所の後ろに「主語 + 動詞」が続き、その動詞の**目的語が欠けている**なら"
     "目的格の関係代名詞。目的格は省略もできる (今回は選ぶ問題)。\n\n"
     "## 🔬 文構造分析\n"
     "The book **which you lent** me last week was really interesting.\n"
     "you lent me (   ) — lent の「貸したもの」が欠けている。その欠けを which が"
     "埋め、The book を修飾する。\n\n"
     "## 📍 正解の根拠\n"
     "先行詞 The book = 物、節内の役割 = lent の目的語 → 物の目的格 **which**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. whose — 所有格。後ろに無冠詞の名詞が続く形で、主語 you とはつながらない。\n"
     "2. whom — 人の目的格。先行詞 The book (物) に合わない。\n"
     "4. what — 先行詞を含む。The book という先行詞と同時には使えない。"),

    (8, 3,
     "Nobody knows the reason (          ) she quit her job.",
     ["why", "which", "what", "where"], 1, 2, "KANKEI-FUKUSHI",
     "## 🎯 コアイメージ\n"
     "関係副詞は先行詞とペアで覚える: 場所 → where / 時 → when / **理由 "
     "(the reason) → why**。後ろには完全な文が続く。\n\n"
     "## 🔬 文構造分析\n"
     "Nobody knows the reason **why she quit** her job.\n"
     "she quit her job は目的語までそろった**完全な文**。先行詞 the reason に"
     "理由の関係副詞 why をつなぐ。\n\n"
     "## 📍 正解の根拠\n"
     "先行詞が the reason で後ろが完全な文 → **why** (= for which)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. which — 節内に名詞の欠けが必要。完全な文の前には置けない (the reason for which なら可)。\n"
     "3. what — 先行詞を含む関係代名詞。the reason という先行詞と同時には使えない。\n"
     "4. where — 場所の関係副詞。先行詞 the reason (理由) に合わない。"),

    (9, 3,
     "(          ) hard you try, you cannot please everyone.",
     ["Whatever", "Whichever", "However", "Whenever"], 3, 2, "KANKEI-FUKUGO",
     "## 🎯 コアイメージ\n"
     "however は「**どんなに〜でも**」の譲歩。直後に**形容詞・副詞**を引き連れて "
     "however + 形/副 + S + V の語順を作る。\n\n"
     "## 🔬 文構造分析\n"
     "**However hard** you try, you cannot please everyone.\n"
     "= No matter how hard you try。副詞 hard を However が前に引き出し、その"
     "あとに you try が続く。\n\n"
     "## 📍 正解の根拠\n"
     "空所の直後が副詞 hard — 形容詞・副詞を従えられる譲歩の複合関係詞は "
     "**However** だけ。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Whatever — 従えるのは名詞 (Whatever excuse you make)。副詞 hard は従えない。\n"
     "2. Whichever — 同じく名詞を従える形 (Whichever way you choose)。hard とはつながらない。\n"
     "4. Whenever —「〜するときはいつでも」。直後は S + V で、hard を挟む形にならない。"),

    (10, 3,
     "I have a friend (          ) father is a famous musician.",
     ["who", "whose", "whom", "which"], 2, 2, "KANKEI-SHOYU",
     "## 🎯 コアイメージ\n"
     "所有格 whose は「先行詞**の**〜」。後ろには**冠詞の付かない名詞**が直接続き、"
     "whose + 名詞 でひとかたまりになる。\n\n"
     "## 🔬 文構造分析\n"
     "I have a friend **whose father** is a famous musician.\n"
     "whose father (その友人の父) が節の主語。a friend's father の 's の働きを "
     "whose がしている。\n\n"
     "## 📍 正解の根拠\n"
     "空所の直後が無冠詞の名詞 father で、「友人**の**父」という所有関係 → "
     "**whose**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. who — 主格。直後に動詞が来る形で、名詞 father との「誰の」の関係は作れない。\n"
     "3. whom — 目的格。後ろに主語 + 動詞が続く形で、father との所有関係は表せない。\n"
     "4. which — 物を受ける関係代名詞。先行詞 a friend (人) に合わない。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
