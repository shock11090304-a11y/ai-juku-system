#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 助動詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/jodoshi1/build_jodoshi1.py

出力 (どちらも**コミットする**。取り込みセッションが git 経由で受け取るため):
    英文法_助動詞_第1集.json        … import_books.py にそのまま渡す bundle
    英文法_助動詞_第1集_問題.pdf    … 冊子 (find_pdf の完全一致名: {source の stem}_問題.pdf)

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同じデータから
  同時に生成する (kateiho2 と同じ作り)。
★ 正解の位置は 1:2 問 / 2:3 問 / 3:3 問 / 4:2 問 に配ってある
  (CLAUDE.md「正解番号は偏らせない」)。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ①build 後に check_pdf_canon_match.py で刷り上がりを
  逆照合 ②_grammar_build.verify() + check_grammar_books.py ③正解の一意性は敵対的に再読する。
  推量の問題は根拠の 1 文を必ず添えて、文脈で誤答が切れることを確認する。
  正解になりうる別形 (例: may have taken に対する must have taken) は**選択肢に入れない**。

取り込み (kamitest-import 環境のセッション or Mac):
    python3 scripts/book_exam/import_books.py scripts/book_exam/materials/jodoshi1 \
        --pdf-dir scripts/book_exam/materials/jodoshi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_助動詞_第1集"
TITLE = "英文法 助動詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

# (番号, ページ, 設問文, [選択肢1..4], 正解番号(1起算), 配点, unit_tag, 解説)
QUESTIONS = [
    (1, 1,
     "The ground is wet. It (          ) last night.",
     ["must rain", "must have rained", "should rain", "had to rain"], 2, 2,
     "JODO-KAKOSUIRYO",
     "## 🎯 コアイメージ\n"
     "**助動詞 + have + 過去分詞 = 過去への推量**。must have p.p. =「〜したに"
     "違いない」。今見えている証拠 (地面が濡れている) から過去を推理する形。\n\n"
     "## 🔬 文構造分析\n"
     "The ground is wet. It **must have rained** last night.\n"
     "根拠 = 現在の状態 (is wet)。推量の対象 = last night (過去) → must + "
     "have + p.p.。\n\n"
     "## 📍 正解の根拠\n"
     "過去 (昨夜) のことへの確信度の高い推量 → **must have rained**「降ったに"
     "違いない」。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. must rain — must + 原形は現在・未来への推量や義務。last night (過去) に届かない。\n"
     "3. should rain —「降るはずだ」という未来方向。過去の出来事の推量にならない。\n"
     "4. had to rain —「降らねばならなかった」という義務で、証拠からの推量の意味が出ない。"),

    (2, 1,
     "He (          ) hungry. He has just eaten a big lunch.",
     ["must be", "may be", "should be", "can't be"], 4, 2, "JODO-SUIRYO",
     "## 🎯 コアイメージ\n"
     "**can't (cannot) =「〜のはずがない」**という強い否定の推量。must be「〜に"
     "違いない」のちょうど裏側。\n\n"
     "## 🔬 文構造分析\n"
     "He **can't be** hungry. He **has just eaten** a big lunch.\n"
     "根拠 = 大盛りの昼食を食べたばかり (現在完了 just)。そこから「空腹のはずが"
     "ない」と否定方向に推量する。\n\n"
     "## 📍 正解の根拠\n"
     "食べたばかりという根拠と両立するのは、否定の推量 **can't be** だけ。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. must be —「空腹に違いない」。食べたばかりという根拠と正反対。\n"
     "2. may be —「空腹かもしれない」。根拠の文が肯定の可能性をつぶしている。\n"
     "3. should be —「空腹のはずだ」。これも根拠と逆方向。"),

    (3, 1,
     "You (          ) go out in this storm. It's dangerous.",
     ["had better not", "had not better", "don't have better", "had better not to"],
     1, 2, "JODO-HADBETTER",
     "## 🎯 コアイメージ\n"
     "had better + 原形「〜したほうがよい (さもないと困る)」の否定は、**not を"
     "better の直後**に置く: had better **not** + 原形。\n\n"
     "## 🔬 文構造分析\n"
     "You **had better not go** out in this storm.\n"
     "had better がひとかたまりの助動詞の働き。否定語 not はかたまりの直後、"
     "動詞の原形 go の直前。\n\n"
     "## 📍 正解の根拠\n"
     "had better の否定形は **had better not** + 原形、の一択。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. had not better — not の位置が違う。better の前には置けない。\n"
     "3. don't have better — had better は have better に分解できない決まり文句。\n"
     "4. had better not to — 後ろは to 不定詞でなく原形。to が余計。"),

    (4, 2,
     "There (          ) be a movie theater around here.",
     ["was used to", "is used to", "used to", "would used to"], 3, 2, "JODO-USEDTO",
     "## 🎯 コアイメージ\n"
     "**used to + 原形 =「昔は〜だった (今は違う)」**。過去と現在の対比を 1 語で"
     "背負う助動詞。be used to -ing「〜に慣れている」と混同しないこと。\n\n"
     "## 🔬 文構造分析\n"
     "There **used to be** a movie theater around here.\n"
     "There is 構文の is の位置に used to + be が入る。「昔はこの辺りに映画館が"
     "あった (今は無い)」。\n\n"
     "## 📍 正解の根拠\n"
     "「かつて存在した」という過去の状態 → **used to** + 原形 be。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. was used to — be used to は後ろに名詞・-ing を取る「慣れ」の表現。原形 be は続かない。\n"
     "2. is used to — 同上。There is used to be という形は作れない。\n"
     "4. would used to — 助動詞を二重に重ねることはできない。"),

    (5, 2,
     "I (          ) harder for the exam. I failed it.",
     ["should have studied", "should study", "must have studied", "cannot have studied"],
     1, 2, "JODO-KOUKAI",
     "## 🎯 コアイメージ\n"
     "**should have + 過去分詞 =「〜すべきだったのに (しなかった)」**という過去への"
     "後悔・非難。実際はしなかった、という裏の意味まで背負う。\n\n"
     "## 🔬 文構造分析\n"
     "I **should have studied** harder for the exam. I **failed** it.\n"
     "failed (落ちた) という過去の結果 → その前の行動への後悔 = should have "
     "p.p.。\n\n"
     "## 📍 正解の根拠\n"
     "「もっと勉強しておくべきだった (のにしなかったから落ちた)」→ "
     "**should have studied**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. should study —「(これから) 勉強すべきだ」。もう落ちた試験の話に合わない。\n"
     "3. must have studied —「勉強したに違いない」という推量。落ちた事実と噛み合わない。\n"
     "4. cannot have studied —「勉強したはずがない」。自分自身への後悔の文にならない。"),

    (6, 2,
     "The teacher demanded that every student (          ) the room at once.",
     ["leaves", "leaving", "will leave", "leave"], 4, 2, "JODO-YOKYU",
     "## 🎯 コアイメージ\n"
     "demand / suggest / insist など**要求・提案の動詞の that 節は「(should +) "
     "動詞の原形」**。実際にするかどうか未定の「これからのこと」だから、時制を"
     "背負わない原形になる (仮定法現在)。\n\n"
     "## 🔬 文構造分析\n"
     "The teacher demanded that every student **(should) leave** the room at "
     "once.\n"
     "demanded (過去) に釣られず、that 節は原形 leave。should leave としてもよい。\n\n"
     "## 📍 正解の根拠\n"
     "要求の demand + that 節 → 原形 **leave** (三単現の s も時制の一致も付けない)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. leaves — 三単現の直説法。要求の that 節では原形にする。\n"
     "2. leaving — -ing 単独では述語にならない。\n"
     "3. will leave — 要求の that 節に will は置かない。"),

    (7, 3,
     "You (          ) be too careful when you drive a car.",
     ["may not", "cannot", "must not", "should not"], 2, 2, "JODO-KANYO",
     "## 🎯 コアイメージ\n"
     "**cannot 〜 too … =「いくら…してもしすぎることはない」**。「注意の上限には"
     "到達 **できない**」→ だから無限に注意してよい、という論理の慣用表現。\n\n"
     "## 🔬 文構造分析\n"
     "You **cannot be too careful** when you drive a car.\n"
     "cannot (不可能) + too careful (注意しすぎ) の組み合わせだけがこの意味を"
     "作る。\n\n"
     "## 📍 正解の根拠\n"
     "「運転では**いくら注意してもしすぎることはない**」= **cannot** 〜 too。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. may not —「注意しすぎないかもしれない」となり慣用の意味を成さない。\n"
     "3. must not —「注意しすぎてはいけない」という禁止になり、言いたいことと逆。\n"
     "4. should not — must not と同じく「しすぎるな」方向で、慣用表現にならない。"),

    (8, 3,
     "I would rather stay home (          ) go shopping in this rain.",
     ["to", "and", "than", "but"], 3, 2, "JODO-WOULDRATHER",
     "## 🎯 コアイメージ\n"
     "**would rather A than B =「B するくらいなら A したい」**。A・B には動詞の"
     "**原形**が入り、rather 〜 than が天秤の両側を作る。\n\n"
     "## 🔬 文構造分析\n"
     "I would rather **stay** home **than go** shopping in this rain.\n"
     "rather と対になるのは than。stay (原形) と go (原形) が比べられている。\n\n"
     "## 📍 正解の根拠\n"
     "前半に would rather がある以上、受けるのは **than** — would rather A "
     "than B の型。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. to — rather と呼応しない。stay home to go 〜 では目的の意味になり文意が壊れる。\n"
     "2. and —「家にいて、買い物にも行く」となり、二択を比べる rather と噛み合わない。\n"
     "4. but — 逆接。rather の比較の相手を示せない。"),

    (9, 3,
     "You (          ) come with me if you don't want to.",
     ["must not", "don't have to", "cannot", "may not"], 2, 2, "JODO-FUYO",
     "## 🎯 コアイメージ\n"
     "**don't have to =「〜しなくてよい」(不必要) / must not =「〜してはいけない」"
     "(禁止)**。否定になると must と have to は別物になる。\n\n"
     "## 🔬 文構造分析\n"
     "You **don't have to come** with me if you don't want to.\n"
     "if 節「来たくないなら」→ 主節は「来る**必要はない**」という免除。\n\n"
     "## 📍 正解の根拠\n"
     "「嫌なら来なくてよい」= 義務の免除 → **don't have to**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. must not — 禁止「来てはいけない」。「来たくないなら」という条件と噛み合わない。\n"
     "3. cannot —「来られない」(不可能)。本人の意思の話に合わない。\n"
     "4. may not —「来てはいけない」(不許可)。同じく免除の意味が出ない。"),

    (10, 3,
     "Kate is late. She (          ) the wrong train.",
     ["must take", "should take", "may have taken", "can have taken"], 3, 2,
     "JODO-KAKOSUIRYO",
     "## 🎯 コアイメージ\n"
     "**may have + 過去分詞 =「〜したかもしれない」**という過去への控えめな推量。"
     "確信の強さで must have (違いない) > may have (かもしれない) と使い分ける。\n\n"
     "## 🔬 文構造分析\n"
     "Kate is late. She **may have taken** the wrong train.\n"
     "遅れている (現在) という手がかりから、乗り間違い (過去) の**可能性**を"
     "述べる。\n\n"
     "## 📍 正解の根拠\n"
     "過去の行動への「かもしれない」→ **may have taken**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. must take — must + 原形は現在・未来向き。過去の「乗ってしまった」に届かない。\n"
     "2. should take —「乗るべきだ」。推量ではなく助言になってしまう。\n"
     "4. can have taken — 肯定文の can have p.p. は不可 (この形は疑問文・否定文だけ)。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
