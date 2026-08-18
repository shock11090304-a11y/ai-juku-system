#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 名詞・冠詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/meishi1/build_meishi1.py

出力 (どちらも**コミットする**): 英文法_名詞冠詞_第1集.json / 英文法_名詞冠詞_第1集_問題.pdf
★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同時生成 (kateiho2 型)。
★ 正解の位置は 1:2 / 2:3 / 3:3 / 4:2。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_pdf_canon_match.py ② verify() +
  check_grammar_books.py ③ 正解の一意性の敵対的再読。用法が割れる冠詞
  (例: practice (the) piano) は出題せず、形で一意に決まる型だけを使う。

取り込み: python3 scripts/book_exam/import_books.py scripts/book_exam/materials/meishi1 \
    --pdf-dir scripts/book_exam/materials/meishi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_名詞冠詞_第1集"
TITLE = "英文法 名詞・冠詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

QUESTIONS = [
    (1, 1,
     "They bought (          ) for their new apartment.",
     ["a furniture", "furnitures", "some furniture", "a few furnitures"], 3, 2,
     "MEISHI-FUKASAN",
     "## 🎯 コアイメージ\n"
     "**furniture は数えられない名詞** (家具の総称)。a も複数の -s も付かない。"
     "数えるなら a piece of furniture。information / advice / baggage も同じ仲間。\n\n"
     "## 🔬 文構造分析\n"
     "They bought **some furniture** for their new apartment.\n"
     "不可算名詞に「いくらか」を添える some。形は単数のまま。\n\n"
     "## 📍 正解の根拠\n"
     "不可算の furniture に付けられるのは **some** (無冠詞・単数形)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. a furniture — 不可算名詞に a は付かない。\n"
     "2. furnitures — 不可算名詞に複数の -s は付かない。\n"
     "4. a few furnitures — a few は可算用で、-s も付けられない。二重の誤り。"),

    (2, 1,
     "Let me give you (          ) advice before you leave.",
     ["an", "a piece of", "a number of", "many"], 2, 2, "MEISHI-PIECE",
     "## 🎯 コアイメージ\n"
     "advice も**数えられない名詞**。「1 つの助言」と数えたいときは "
     "**a piece of advice** と入れ物 (piece) の方を数える。\n\n"
     "## 🔬 文構造分析\n"
     "Let me give you **a piece of advice** before you leave.\n"
     "a piece of (1 つの) + advice (不可算のまま)。\n\n"
     "## 📍 正解の根拠\n"
     "不可算の advice を 1 つ分だけ差し出す → **a piece of**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. an — 不可算名詞に an は付かない。\n"
     "3. a number of —「多数の」+ 可算複数 (a number of books)。advice には付かない。\n"
     "4. many — 可算複数用。many advice とは言えない (much advice なら可)。"),

    (3, 1,
     "She goes to her office (          ) every morning.",
     ["by a bus", "by the bus", "on bus", "by bus"], 4, 2, "MEISHI-MUKANSHI",
     "## 🎯 コアイメージ\n"
     "**by + 交通手段は無冠詞**: by bus / by train / by car。「バスという手段で」と"
     "抽象化されるので a も the も付かない。\n\n"
     "## 🔬 文構造分析\n"
     "She goes to her office **by bus** every morning.\n"
     "手段の by + 無冠詞の bus。特定の 1 台を指していない。\n\n"
     "## 📍 正解の根拠\n"
     "交通手段の言い方は **by bus** (無冠詞) で固定。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. by a bus — 手段の by に冠詞は付けない。\n"
     "2. by the bus — 同上。特定の便に乗っている状態なら on the bus と言う。\n"
     "3. on bus — on を使うなら on the bus と冠詞が要る。無冠詞の on bus は無い。"),

    (4, 2,
     "There is (          ) for improvement in your essay.",
     ["room", "a room", "rooms", "the rooms"], 1, 2, "MEISHI-IMICHIGAI",
     "## 🎯 コアイメージ\n"
     "**room は無冠詞だと「余地・スペース」(不可算)**、a room なら「部屋」(可算)。"
     "冠詞の有無で意味が変わる名詞の代表格。\n\n"
     "## 🔬 文構造分析\n"
     "There is **room for improvement** in your essay.\n"
     "room for 〜 =「〜の余地」。改善の余地がある、という決まり文句。\n\n"
     "## 📍 正解の根拠\n"
     "「改善の**余地**」= 不可算・無冠詞の **room**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. a room —「部屋」。作文の中に部屋があることになり意味不明。\n"
     "3. rooms — 複数の部屋。同じく「余地」の意味が消える。\n"
     "4. the rooms — 特定の部屋たち。文意と全く合わない。"),

    (5, 2,
     "In that company, part-time workers are paid by (          ).",
     ["hour", "the hour", "an hour", "hours"], 2, 2, "MEISHI-TANI",
     "## 🎯 コアイメージ\n"
     "**by the + 単位 =「〜単位で・〜ぎめで」**: by the hour (時間ぎめ) / by the "
     "pound (ポンド単位)。単位を代表する the が付くのがポイント。\n\n"
     "## 🔬 文構造分析\n"
     "Part-time workers are paid **by the hour**.\n"
     "支払いの基準単位 = 1 時間。by the hour で「時給で」。\n\n"
     "## 📍 正解の根拠\n"
     "単位ぎめの表現は **by the** + 単位 → by the hour。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. hour — 無冠詞では単位の言い方にならない (by bus の無冠詞と混同しない)。\n"
     "3. an hour —「1 時間につき」なら an hour だけでは形にならない (per hour / an hour あたりの言い方は別構文)。\n"
     "4. hours — 複数形。単位を代表する形は単数 + the。"),

    (6, 2,
     "The (          ) on the crowded train were all looking at their phones.",
     ["customers", "guests", "passengers", "clients"], 3, 2, "MEISHI-TSUKAIWAKE",
     "## 🎯 コアイメージ\n"
     "日本語の「客」は英語で分業: **乗客 = passenger** / 店の買い物客 = customer / "
     "招待客・宿泊客 = guest / 専門職の依頼人 = client。\n\n"
     "## 🔬 文構造分析\n"
     "The **passengers** on the crowded train were all looking at their phones.\n"
     "on the crowded train (満員電車の) が決め手 — 乗り物の客 = passengers。\n\n"
     "## 📍 正解の根拠\n"
     "電車に乗っている客 → **passengers**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. customers — 店で物やサービスを買う客。乗り物には使わない。\n"
     "2. guests — 招かれた客・ホテルの宿泊客。電車の乗客には使わない。\n"
     "4. clients — 弁護士・会計士など専門職の依頼人。文脈に合わない。"),

    (7, 3,
     "The (          ) of Tokyo is much larger than that of Kyoto.",
     ["population", "peoples", "citizen", "member"], 1, 2, "MEISHI-POPULATION",
     "## 🎯 コアイメージ\n"
     "「人口が多い・少ない」は **population + large / small** で言う (many / few は"
     "使わない)。that of 〜 =「〜の人口」という代用表現とセットで頻出。\n\n"
     "## 🔬 文構造分析\n"
     "The **population** of Tokyo is much larger than **that** (= the "
     "population) of Kyoto.\n"
     "larger と呼応する主語 = 人口という「大きさ」を持つ名詞。\n\n"
     "## 📍 正解の根拠\n"
     "larger than that of 〜 と比べられる「東京の何か」→ **population** "
     "(人口)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. peoples —「諸民族」。larger と組んで人口の大小は表せない。\n"
     "3. citizen — 1 人の市民。「東京の市民が京都のそれより大きい」では意味を成さない。\n"
     "4. member — 一員。of Tokyo とも larger とも噛み合わない。"),

    (8, 3,
     "We are in (          ) class, so we see each other every day.",
     ["same", "a same", "same the", "the same"], 4, 2, "MEISHI-SAME",
     "## 🎯 コアイメージ\n"
     "**same には必ず the が付く**: the same class。「同じ」= 比べる相手と重なる"
     "唯一のものだから、常に特定の the とセット。\n\n"
     "## 🔬 文構造分析\n"
     "We are in **the same class**, so we see each other every day.\n"
     "the same + 名詞 =「同じ〜」。毎日顔を合わせる理由になる。\n\n"
     "## 📍 正解の根拠\n"
     "same の前は常に **the** → the same class。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. same — 冠詞なしの same + 名詞は不可。\n"
     "2. a same — same に a は付かない (「同じ」は 1 つに特定されるから)。\n"
     "3. same the — 語順が逆。冠詞は same の前。"),

    (9, 3,
     "The website gives us a lot of useful (          ) about studying abroad.",
     ["informations", "an information", "information", "information's"], 3, 2,
     "MEISHI-FUKASAN",
     "## 🎯 コアイメージ\n"
     "**information も数えられない名詞**。a も -s も付かず、量は a lot of / much / "
     "a piece of で表す。日本語の「情報 1 件」の感覚で数えないこと。\n\n"
     "## 🔬 文構造分析\n"
     "The website gives us a lot of useful **information** about studying "
     "abroad.\n"
     "a lot of + 不可算名詞 (単数形のまま)。\n\n"
     "## 📍 正解の根拠\n"
     "不可算の information は**そのままの形** → information。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. informations — 不可算名詞に複数の -s は付かない。\n"
     "2. an information — 不可算名詞に an は付かない (a piece of information なら可)。\n"
     "4. information's — 所有格。ここでは意味を成さない。"),

    (10, 3,
     "The library is about (          ) walk from the station.",
     ["ten minutes", "ten minutes'", "ten minute", "ten minutes's"], 2, 2,
     "MEISHI-SHOYU",
     "## 🎯 コアイメージ\n"
     "時間・距離の名詞は**所有格で形容詞の働き**をする: ten minutes' walk (10 分の"
     "徒歩)。複数形 -s で終わる語の所有格は**アポストロフィだけ**足す。\n\n"
     "## 🔬 文構造分析\n"
     "The library is about **ten minutes' walk** from the station.\n"
     "ten minutes' (10 分の) が walk を修飾。s の後ろは ' のみ。\n\n"
     "## 📍 正解の根拠\n"
     "複数形 minutes の所有格 → **ten minutes'** walk。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. ten minutes — 所有格の ' が無いと walk と直結できない。\n"
     "3. ten minute — 数詞 ten があるのに単数形のままで、所有格にもなっていない。\n"
     "4. ten minutes's — -s で終わる複数形に 's は付けない (' だけ)。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
