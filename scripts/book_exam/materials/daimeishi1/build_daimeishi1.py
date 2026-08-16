#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 代名詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/daimeishi1/build_daimeishi1.py

出力 (どちらも**コミットする**): 英文法_代名詞_第1集.json / 英文法_代名詞_第1集_問題.pdf
★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同時生成 (kateiho2 型)。
★ 正解の位置は 1:2 / 2:3 / 3:3 / 4:2。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_pdf_canon_match.py ② verify() +
  check_grammar_books.py ③ 正解の一意性の敵対的再読。単数動詞 (has / was) や of の
  有無など、**形の手がかりだけで一意に決まる**作りを優先する。

取り込み: python3 scripts/book_exam/import_books.py scripts/book_exam/materials/daimeishi1 \
    --pdf-dir scripts/book_exam/materials/daimeishi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_代名詞_第1集"
TITLE = "英文法 代名詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

QUESTIONS = [
    (1, 1,
     "I've lost my umbrella, so I have to buy (          ).",
     ["it", "them", "the one", "one"], 4, 2, "DAIMEI-ONE",
     "## 🎯 コアイメージ\n"
     "**one = 同じ種類の不特定の 1 つ / it = さっき出てきたその物そのもの**。"
     "「傘というもの」を買うのか、「あの傘」を指すのかで使い分ける。\n\n"
     "## 🔬 文構造分析\n"
     "I've lost my umbrella, so I have to buy **one** (= an umbrella).\n"
     "買うのは失くした傘そのものではなく、同種の新しい 1 本。\n\n"
     "## 📍 正解の根拠\n"
     "失くした物は買えない。「(代わりの) 傘を 1 本」= 不特定の **one**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. it — 失くしたその傘そのものを指す。手元に無い物は買えない。\n"
     "2. them — 複数。傘は 1 本の話。\n"
     "3. the one — the が付くと特定の 1 本になり、どの傘か指す修飾が無いと浮く。"),

    (2, 1,
     "I have two brothers. One lives in Tokyo, and (          ) lives in Osaka.",
     ["another", "the other", "other", "others"], 2, 2, "DAIMEI-OTHER",
     "## 🎯 コアイメージ\n"
     "**2 つのうち残りの 1 つ = the other** (残りが確定するから the)。3 つ以上で"
     "「別のもう 1 つ」なら another。\n\n"
     "## 🔬 文構造分析\n"
     "I have **two** brothers. **One** lives in Tokyo, and **the other** lives "
     "in Osaka.\n"
     "全体が 2 人 → 1 人目 (One) を除いた残りは自動的に 1 人に確定。\n\n"
     "## 📍 正解の根拠\n"
     "two brothers の「残りの 1 人」= 特定できる → **the other**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. another — an + other =「不特定の別の 1 つ」。2 人しかいないので「残り」は特定でき、an は合わない。\n"
     "3. other — 単独では主語になれない (形容詞的な語)。\n"
     "4. others — 複数「他の人たち」。残りは 1 人なので合わない。"),

    (3, 1,
     "Yesterday I met an old friend of (          ) at the station.",
     ["mine", "me", "my", "I"], 1, 2, "DAIMEI-SHOYU",
     "## 🎯 コアイメージ\n"
     "**a friend of mine =「私の友人 (の 1 人)」**。a と my は名詞の前に並べられ"
     "ないので、of + **所有代名詞** (mine = my friends) の形で逃がす。\n\n"
     "## 🔬 文構造分析\n"
     "I met an old friend **of mine** at the station.\n"
     "= my old friends のうちの 1 人。an 〜 of mine が定番の組み合わせ。\n\n"
     "## 📍 正解の根拠\n"
     "of の後ろで「私のもの (友人たち)」を表す所有代名詞 → **mine**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. me — 目的格。a friend of me とは言わない (所有の意味が出ない)。\n"
     "3. my — 所有格は後ろに名詞が要る。of my で文が切れると宙に浮く。\n"
     "4. I — 主格。前置詞 of の後ろには置けない。"),

    (4, 2,
     "(          ) the students in this class come to school by bike.",
     ["Almost", "The most of", "Most of", "Almost of"], 3, 2, "DAIMEI-MOSTOF",
     "## 🎯 コアイメージ\n"
     "**Most of the + 名詞 =「〜の大部分」**。almost は副詞なので名詞を直接修飾"
     "できない (almost all the students なら可) — 定番の引っかけ。\n\n"
     "## 🔬 文構造分析\n"
     "**Most of the students** in this class come to school by bike.\n"
     "Most (代名詞) + of + the students (特定の集団)。\n\n"
     "## 📍 正解の根拠\n"
     "the students という特定集団の大部分 → **Most of** the 〜。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Almost — 副詞。名詞 the students をじかに修飾できない (Almost all なら可)。\n"
     "2. The most of — most に the は付けない (the most は最上級の形)。\n"
     "4. Almost of — この形は存在しない。"),

    (5, 2,
     "There are shops on (          ) side of the street.",
     ["both", "either", "all", "most"], 2, 2, "DAIMEI-EITHER",
     "## 🎯 コアイメージ\n"
     "**either side =「(2 つある) どちらの側にも」**。either は**単数名詞**を"
     "従えて「2 つのどちらも」を表せる (= on both sides)。\n\n"
     "## 🔬 文構造分析\n"
     "There are shops on **either side** of the street.\n"
     "空所の直後が side (**単数**) — ここが決め手。通りの両側それぞれに店がある。\n\n"
     "## 📍 正解の根拠\n"
     "単数形 side を従えて「両側に」と言えるのは **either**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. both — both は複数名詞とペア (both **sides** なら可)。単数 side には付かない。\n"
     "3. all — 3 つ以上 + 複数名詞に使う。単数 side に合わない。\n"
     "4. most — most side という形は無い (most of the 〜 なら別)。"),

    (6, 2,
     "(          ) is about ten minutes' walk from here to the station.",
     ["This", "There", "That", "It"], 4, 2, "DAIMEI-IT",
     "## 🎯 コアイメージ\n"
     "**距離・時間・天候・明暗は it が主語**を務める (訳さない it)。ここから駅まで"
     "の「距離」の話は It is 〜 で始める。\n\n"
     "## 🔬 文構造分析\n"
     "**It** is about ten minutes' walk from here to the station.\n"
     "from here to the station の距離を it が代表する。\n\n"
     "## 📍 正解の根拠\n"
     "距離を述べる文の形式的な主語 → **It**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. This —「これ」と指す対象が無く、距離の形式主語にはならない。\n"
     "2. There — There is 構文は「〜がある」の存在文。距離の言い方はこの形を取らない。\n"
     "3. That —「あれ」と指す対象が無い。距離の主語は it と決まっている。"),

    (7, 3,
     "Heaven helps (          ) who help themselves.",
     ["these", "them", "those", "they"], 3, 2, "DAIMEI-THOSE",
     "## 🎯 コアイメージ\n"
     "**those who 〜 =「〜する人々」**。those が「人々」を指し、who 以下が条件を"
     "付ける。ことわざ・格言の頻出形。\n\n"
     "## 🔬 文構造分析\n"
     "Heaven helps **those who help themselves**.\n"
     "「天は自ら助くる者を助く」。those (人々) + who help themselves (自分で"
     "努力する)。\n\n"
     "## 📍 正解の根拠\n"
     "関係詞 who を従えて「〜する人々」を作るのは **those**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. these —「これらの」。目の前の物を指す語で、一般の「人々」を作れない。\n"
     "2. them — 目的格の代名詞に who の節は直接続けられない (this usage は不可)。\n"
     "4. they — 主格。helps の目的語の位置に置けない。"),

    (8, 3,
     "Please make (          ) at home.",
     ["yourself", "you", "yours", "your"], 1, 2, "DAIMEI-SAIKI",
     "## 🎯 コアイメージ\n"
     "**make oneself at home =「くつろぐ」**。主語 (命令文なら you) と同じ人が"
     "目的語になるときは**再帰代名詞 -self**。\n\n"
     "## 🔬 文構造分析\n"
     "Please make **yourself** at home.\n"
     "命令文の隠れた主語 = you。その you 自身を目的語にする → yourself。\n\n"
     "## 📍 正解の根拠\n"
     "主語と目的語が同一人物 + 決まり文句 make oneself at home → "
     "**yourself**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. you — 主語と同じ人を目的語にするときは再帰代名詞にする。\n"
     "3. yours — 所有代名詞「あなたのもの」。くつろぐ本人を指せない。\n"
     "4. your — 所有格。後ろに名詞が無いと使えない。"),

    (9, 3,
     "(          ) of the four answers was correct.",
     ["No one", "Anyone", "None", "Nothing"], 3, 2, "DAIMEI-NONE",
     "## 🎯 コアイメージ\n"
     "**none of the 〜 =「〜のどれも…ない」**。of とペアで使える全否定は none "
     "(no one / nothing は of the 〜 を従えない)。\n\n"
     "## 🔬 文構造分析\n"
     "**None of the four answers** was correct.\n"
     "4 つの選択肢という母集団 (of the four answers) の中のゼロ個。\n\n"
     "## 📍 正解の根拠\n"
     "of the 〜 を従えて全否定 → **None** of the four answers。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. No one —「誰も〜ない」(人専用)。of the 〜 は続けられない。\n"
     "2. Anyone — 肯定の平叙文では「誰でも」となり、否定の意味が出ない。\n"
     "4. Nothing —「何も〜ない」。of the 〜 で母集団を限る使い方はできない。"),

    (10, 3,
     "(          ) of the students has to give a short speech in English.",
     ["Every", "Each", "All", "Some"], 2, 2, "DAIMEI-EACH",
     "## 🎯 コアイメージ\n"
     "**each of the 〜 + 単数動詞 =「〜の一人ひとりが」**。each は「1 人ずつ」に"
     "焦点を当てるので、of を従えられて動詞は単数で受ける。\n\n"
     "## 🔬 文構造分析\n"
     "**Each of the students has** to give a short speech in English.\n"
     "動詞が **has** (単数) — ここが決め手。1 人ずつ全員がスピーチをする。\n\n"
     "## 📍 正解の根拠\n"
     "of の前に置けて、単数動詞 has と呼応する → **Each**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Every — 形容詞なので単独で of の前に立てない (every one of なら可)。\n"
     "3. All — All of the students なら動詞は **have** (複数)。has と合わない。\n"
     "4. Some — Some of the students も複数扱いで have。has と合わない。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
