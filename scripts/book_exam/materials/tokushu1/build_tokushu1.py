#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 特殊構文 演習 第1集」(否定・倒置・強調) — PDF と JSON を作る。

    python3 scripts/book_exam/materials/tokushu1/build_tokushu1.py

出力 (どちらも**コミットする**): 英文法_特殊構文_第1集.json / 英文法_特殊構文_第1集_問題.pdf
★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同時生成 (kateiho2 型)。
★ 正解の位置は 1:2 / 2:3 / 3:3 / 4:2。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_pdf_canon_match.py ② verify() +
  check_grammar_books.py ③ 正解の一意性の敵対的再読。正解になりうる別形
  (例: Never have I seen に対する Never did I see) は**選択肢に入れない**。

取り込み: python3 scripts/book_exam/import_books.py scripts/book_exam/materials/tokushu1 \
    --pdf-dir scripts/book_exam/materials/tokushu1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_特殊構文_第1集"
TITLE = "英文法 特殊構文 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

QUESTIONS = [
    (1, 1,
     "(          ) was my sister that broke the vase yesterday.",
     ["That", "It", "There", "What"], 2, 2, "TOKUSHU-KYOCHO",
     "## 🎯 コアイメージ\n"
     "**強調構文 It is 〜 that … =「…なのは〜だ」**。伝えたい 1 語 (句) を "
     "It is と that で挟んで前に出す。\n\n"
     "## 🔬 文構造分析\n"
     "**It** was **my sister** that broke the vase yesterday.\n"
     "元の文 My sister broke the vase 〜 の my sister を挟んで強調。「花瓶を"
     "割ったのは (他でもない) 姉だ」。\n\n"
     "## 📍 正解の根拠\n"
     "後ろの that とペアで強調の枠を作る → **It** was 〜 that …。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. That — That was my sister だと後ろの that 節とつながらない。\n"
     "3. There — There is 構文は「〜がある」の存在文。that 節と呼応しない。\n"
     "4. What — What was my sister だと疑問文になり、that 以下が浮く。"),

    (2, 1,
     "Never (          ) such a beautiful rainbow before.",
     ["have I seen", "I have seen", "I see", "I am seen"], 1, 2, "TOKUSHU-TOCHI",
     "## 🎯 コアイメージ\n"
     "**否定の副詞 (Never / Little / Hardly) を文頭に出したら、後ろは疑問文の語順"
     "(倒置)**。否定を先に立てた分、主語と助動詞がひっくり返る。\n\n"
     "## 🔬 文構造分析\n"
     "**Never have I seen** such a beautiful rainbow before.\n"
     "= I have never seen 〜。Never が文頭 → have (助動詞) + I (主語) + seen。\n\n"
     "## 📍 正解の根拠\n"
     "文頭の Never + before (経験) → 倒置の現在完了 **have I seen**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. I have seen — 通常の語順のまま。否定語が文頭に出たら倒置が必須。\n"
     "3. I see — 語順も時制 (before の経験) も合わない。\n"
     "4. I am seen — 受け身「私が見られる」。意味も語順も成り立たない。"),

    (3, 1,
     "My wife likes Italian food, and (          ).",
     ["so I do", "so am I", "neither do I", "so do I"], 4, 2, "TOKUSHU-SODO",
     "## 🎯 コアイメージ\n"
     "**「〜も同じ」= so + 助動詞 + 主語** (倒置)。前の文が一般動詞なら do / does / "
     "did、be 動詞なら am / is で受ける。\n\n"
     "## 🔬 文構造分析\n"
     "My wife **likes** Italian food, and **so do I**.\n"
     "likes (一般動詞・現在) を受ける代役 = do。so + do + I の語順。\n\n"
     "## 📍 正解の根拠\n"
     "肯定文を受けて「私も好き」→ **so do I** (倒置)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. so I do — 倒置なしの語順は「確かにそうです」という同意の返事で、「私も」の意味にならない。\n"
     "2. so am I — be 動詞の受け方。前の文の動詞は likes (一般動詞) なので do で受ける。\n"
     "3. neither do I — 否定文を受ける形。前の文は肯定文。"),

    (4, 2,
     "The most expensive restaurants are (          ) the best ones.",
     ["always not", "not either", "not always", "no always"], 3, 2, "TOKUSHU-BUBUN",
     "## 🎯 コアイメージ\n"
     "**not + always / all / every = 部分否定「必ずしも〜とは限らない」**。"
     "not が always を打ち消して「100% ではない」と言う形。\n\n"
     "## 🔬 文構造分析\n"
     "The most expensive restaurants are **not always** the best ones.\n"
     "not (否定) → always (いつも) の順。「一番高い店がいつも一番良いとは"
     "限らない」。\n\n"
     "## 📍 正解の根拠\n"
     "部分否定の語順は **not always** (not が先)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. always not — 語順が逆。部分否定は not が always の前に来る。\n"
     "2. not either — either は「(2 つのうち) どちらか」。比べる 2 択が無く、are not either 〜 では形が浮く。\n"
     "4. no always — no は副詞 always を打ち消せない (no の後ろは名詞)。"),

    (5, 2,
     "Little (          ) that he would become a famous singer.",
     ["did I dream", "I dreamed", "I did dream", "dreamed I"], 1, 2, "TOKUSHU-TOCHI",
     "## 🎯 コアイメージ\n"
     "**Little did I dream / know 〜 =「〜とは夢にも思わなかった」**。準否定の "
     "Little が文頭に出た倒置の決まり文句。\n\n"
     "## 🔬 文構造分析\n"
     "**Little did I dream** that he would become a famous singer.\n"
     "= I little dreamed that 〜。過去の一般動詞の倒置 → did + I + dream "
     "(原形)。\n\n"
     "## 📍 正解の根拠\n"
     "文頭の Little (準否定) → 助動詞 did を立てた倒置 **did I dream**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. I dreamed — 通常の語順。否定語が文頭に出たら倒置が必須。\n"
     "3. I did dream — did を使っていても主語が先では倒置になっていない。\n"
     "4. dreamed I — 一般動詞をじかにひっくり返す形は現代英語には無い (did を立てる)。"),

    (6, 2,
     "I (          ) hope you will get well soon.",
     ["does", "do", "am", "did"], 2, 2, "TOKUSHU-KYOCHODO",
     "## 🎯 コアイメージ\n"
     "**強調の do =「本当に・確かに〜する」**。動詞の前に do / does / did を置いて"
     "気持ちを強める。後ろの動詞は必ず**原形**。\n\n"
     "## 🔬 文構造分析\n"
     "I **do hope** you will get well soon.\n"
     "do (強調) + hope (原形)。「一日も早い回復を**心から**願っています」。\n\n"
     "## 📍 正解の根拠\n"
     "主語 I・現在の文 → 強調の助動詞は **do**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. does — 三人称単数用。主語は I。\n"
     "3. am — be 動詞の後ろに動詞の原形 hope は置けない。\n"
     "4. did — 過去の強調になり、you **will** get well (これからの話) と時間が合わない。"),

    (7, 3,
     "\"Will it rain this afternoon?\" \"I'm afraid (          ).\"",
     ["it", "yes", "so", "that"], 3, 2, "TOKUSHU-DAIYO",
     "## 🎯 コアイメージ\n"
     "**so が前の文の内容を丸ごと代用する**: I'm afraid so. (残念ながらそうなり"
     "そう) / I hope so. / I think so.。so = that it will rain。\n\n"
     "## 🔬 文構造分析\n"
     "\"Will it rain this afternoon?\" \"I'm afraid **so**.\"\n"
     "so が「午後は雨が降る (だろう)」という節全体の身代わり。\n\n"
     "## 📍 正解の根拠\n"
     "afraid の後ろで前文の内容を受ける代用語 → **so**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. it — I'm afraid it では「それが怖い」となり、節の代用にならない。\n"
     "2. yes — I'm afraid yes という言い方は無い (返事の Yes は文頭に立つ)。\n"
     "4. that — 単独の that は節の代用に使えない (I'm afraid that 〜 なら後ろに文が要る)。"),

    (8, 3,
     "My father doesn't smoke, and (          ).",
     ["so do I", "neither I do", "so don't I", "neither do I"], 4, 2, "TOKUSHU-SODO",
     "## 🎯 コアイメージ\n"
     "**否定文を受けて「〜も…ない」= neither + 助動詞 + 主語**。肯定は so、否定は "
     "neither (= nor) で受ける、と対で覚える。\n\n"
     "## 🔬 文構造分析\n"
     "My father **doesn't** smoke, and **neither do I**.\n"
     "doesn't (否定・一般動詞・現在) を受ける → neither + do + I。\n\n"
     "## 📍 正解の根拠\n"
     "否定文の「私も吸わない」→ **neither do I** (倒置)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. so do I — 肯定文を受ける形。「私は吸う」ことになり前半と食い違う。\n"
     "2. neither I do — 倒置になっていない。neither の後ろは助動詞が先。\n"
     "3. so don't I — この形は存在しない (否定の「〜も」は neither / nor)。"),

    (9, 3,
     "It was not (          ) yesterday that I heard the news.",
     ["by", "until", "since", "when"], 2, 2, "TOKUSHU-UNTIL",
     "## 🎯 コアイメージ\n"
     "**It is not until 〜 that … =「〜になって初めて…する」**。not until (〜まで"
     "…ない) を強調構文の枠に入れた定番の型。\n\n"
     "## 🔬 文構造分析\n"
     "It was **not until yesterday** that I heard the news.\n"
     "= I didn't hear the news until yesterday。「昨日になって初めてその知らせを"
     "聞いた」。\n\n"
     "## 📍 正解の根拠\n"
     "It was not **until** 〜 that … の固定の型。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. by — not by yesterday では「昨日までに〜ない」となり、that 以下と噛み合わない。\n"
     "3. since — not since では「昨日以来〜ない」となり「初めて聞いた」の意味が出ない。\n"
     "4. when — It was not when 〜 は強調構文の型にならない。"),

    (10, 3,
     "His explanation was (          ) from satisfactory, so we asked more questions.",
     ["free", "away", "far", "apart"], 3, 2, "TOKUSHU-JUNHITEI",
     "## 🎯 コアイメージ\n"
     "**far from 〜 =「〜どころではない・決して〜でない」**という準否定の慣用。"
     "「〜から遠い」の比喩で強く打ち消す。\n\n"
     "## 🔬 文構造分析\n"
     "His explanation was **far from satisfactory**, so we asked more "
     "questions.\n"
     "far from + 形容詞 (satisfactory)。「満足には程遠い説明だった」→ だから質問を"
     "重ねた。\n\n"
     "## 📍 正解の根拠\n"
     "「満足とは**程遠い**」という準否定 → **far** from。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. free — free from は「〜が無い」で、後ろには名詞が来る (free from errors)。形容詞は続かない。\n"
     "2. away — away from は物理的な距離。「決して〜でない」の慣用にならない。\n"
     "4. apart — apart from は「〜は別として」。打ち消しの意味が出ない。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
