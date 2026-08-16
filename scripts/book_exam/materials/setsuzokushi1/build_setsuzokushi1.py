#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 接続詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/setsuzokushi1/build_setsuzokushi1.py

出力 (どちらも**コミットする**): 英文法_接続詞_第1集.json / 英文法_接続詞_第1集_問題.pdf
★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同時生成 (kateiho2 型)。
★ 正解の位置は 1:2 / 2:3 / 3:3 / 4:2。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_pdf_canon_match.py ② verify() +
  check_grammar_books.py ③ 正解の一意性の敵対的再読。unless / in case など文脈で切る
  問題は、誤答の読みが不合理になる根拠 (帰結や理由の 1 文) を必ず添える。

取り込み: python3 scripts/book_exam/import_books.py scripts/book_exam/materials/setsuzokushi1 \
    --pdf-dir scripts/book_exam/materials/setsuzokushi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_接続詞_第1集"
TITLE = "英文法 接続詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

QUESTIONS = [
    (1, 1,
     "The problem is (          ) we don't have enough time to prepare.",
     ["what", "if", "that", "which"], 3, 2, "SETSU-MEISHI",
     "## 🎯 コアイメージ\n"
     "**that 節 =「〜ということ」という名詞のかたまり**。後ろに**完全な文**を"
     "従えて、文の主語・目的語・補語になれる。\n\n"
     "## 🔬 文構造分析\n"
     "The problem is **that we don't have enough time** to prepare.\n"
     "that 以下が補語 (問題 = 時間が足りないということ)。節の中は欠けの無い完全な"
     "文。\n\n"
     "## 📍 正解の根拠\n"
     "後ろが完全な文で、「〜ということ」の意味 → 接続詞 **that**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. what — 関係代名詞 what の節は中に名詞の欠けが要る。ここは完全な文なので置けない。\n"
     "2. if —「〜かどうか」の名詞節は目的語の位置が基本で、補語には whether を使う。意味も合わない。\n"
     "4. which — 疑問詞・関係詞のどちらでも、先行詞や選択の文脈が無くつながらない。"),

    (2, 1,
     "(          ) you like it or not, you have to do your homework.",
     ["Whether", "If", "That", "Unless"], 1, 2, "SETSU-WHETHER",
     "## 🎯 コアイメージ\n"
     "**whether A or not =「A であろうとなかろうと」**という譲歩の副詞節。"
     "or not との呼応が whether のサイン。\n\n"
     "## 🔬 文構造分析\n"
     "**Whether you like it or not**, you have to do your homework.\n"
     "好き (like it) と嫌い (or not) の両方をカバーして「どちらでも宿題はやる」。\n\n"
     "## 📍 正解の根拠\n"
     "文末の **or not** と呼応して譲歩を作れるのは **Whether** だけ。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. If — 条件「もし好きなら」。or not と呼応する譲歩の用法は無い。\n"
     "3. That —「〜ということ」の名詞節。副詞節の位置には置けない。\n"
     "4. Unless —「〜しない限り」。or not とつながらない。"),

    (3, 1,
     "I'll be at the office by nine (          ) the train is delayed.",
     ["if", "unless", "because", "so"], 2, 2, "SETSU-UNLESS",
     "## 🎯 コアイメージ\n"
     "**unless =「〜しない限り・〜の場合を除いて」**= if ... not。例外の 1 ケース"
     "だけを切り出す接続詞。\n\n"
     "## 🔬 文構造分析\n"
     "I'll be at the office by nine **unless the train is delayed**.\n"
     "基本は「9 時までに着く」。例外 = 電車が遅れた場合、だけを unless が除外"
     "する。\n\n"
     "## 📍 正解の根拠\n"
     "「電車が遅れ**ない限り** 9 時までに着く」→ **unless**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. if —「遅れた**ら**着く」となり因果が逆立ちする。\n"
     "3. because —「遅れる**から**着く」。理由として成り立たない。\n"
     "4. so — 等位接続詞「だから」。ここに置くと「着く、だから遅れる」となり意味も語順も壊れる。"),

    (4, 2,
     "It was (          ) a beautiful day that we decided to go on a picnic.",
     ["so", "very", "too", "such"], 4, 2, "SETSU-SUCHTHAT",
     "## 🎯 コアイメージ\n"
     "**such + a + 形容詞 + 名詞 + that … =「とても〜な…なので」**。名詞を含む"
     "かたまりを強調するのは such (so は形容詞・副詞だけを強調)。\n\n"
     "## 🔬 文構造分析\n"
     "It was **such a beautiful day that** we decided to go on a picnic.\n"
     "such + a beautiful day (名詞のかたまり) + that 節 (結果)。\n\n"
     "## 📍 正解の根拠\n"
     "空所の直後が **a + 形容詞 + 名詞**の並び → **such**。(so なら so beautiful "
     "a day の語順になる)\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. so — so の後ろは形容詞が先: so beautiful a day。so a beautiful day の語順は無い。\n"
     "2. very — very a beautiful day という語順は無く、that 節とも呼応しない。\n"
     "3. too — too 〜 to do とペアを組む語。that 節とは呼応しない。"),

    (5, 2,
     "(          ) I know, he has never been late for school.",
     ["As long as", "As far as", "By the time", "In case"], 2, 2, "SETSU-KANYO",
     "## 🎯 コアイメージ\n"
     "**as far as =「〜の範囲では」(範囲) / as long as =「〜しさえすれば」(条件)**。"
     "as far as I know「私の知る限り」は範囲の代表慣用。\n\n"
     "## 🔬 文構造分析\n"
     "**As far as I know**, he has never been late for school.\n"
     "「私の知識の範囲では」という限定を文全体にかぶせる。\n\n"
     "## 📍 正解の根拠\n"
     "know (知識) の**範囲**を限る → **As far as** I know。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. As long as — 条件「〜でありさえすれば」。As long as I know だと「私が知ってさえいれば」となり意味不明。\n"
     "3. By the time —「〜する時までには」。時の締め切りで、文意に合わない。\n"
     "4. In case —「〜するといけないから」。備えの意味で、知識の範囲を表せない。"),

    (6, 2,
     "She is not only a talented pianist (          ) a good teacher.",
     ["and also", "but then", "but also", "and yet"], 3, 2, "SETSU-NOTONLY",
     "## 🎯 コアイメージ\n"
     "**not only A but also B =「A だけでなく B も」**。not only と but also が"
     "呼応のペアで、A と B には文法的に同じ形が入る。\n\n"
     "## 🔬 文構造分析\n"
     "She is **not only** a talented pianist **but also** a good teacher.\n"
     "A = a talented pianist / B = a good teacher (どちらも名詞句)。\n\n"
     "## 📍 正解の根拠\n"
     "前半の **not only** を受けるのは **but also** — 固定の呼応。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. and also — not only との呼応にならない (only の否定が宙に浮く)。\n"
     "2. but then —「しかしその一方」という談話表現。呼応のペアではない。\n"
     "4. and yet —「それでいて」。同じく not only と呼応しない。"),

    (7, 3,
     "Take an umbrella with you (          ) it rains.",
     ["in case", "so that", "as if", "unless"], 1, 2, "SETSU-INCASE",
     "## 🎯 コアイメージ\n"
     "**in case 〜 =「〜するといけないから・〜の場合に備えて」**。起きてほしくない"
     "事態への**備え**を表す。節の中は現在形 (will を使わない)。\n\n"
     "## 🔬 文構造分析\n"
     "Take an umbrella with you **in case it rains**.\n"
     "傘を持つ = 備え。雨が降る = 備える対象。因果がまっすぐ通る。\n\n"
     "## 📍 正解の根拠\n"
     "「降るといけないから持って行け」= **in case**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. so that — 目的「雨が降る**ように**傘を持て」となり意味が通らない (普通 can / will を伴う)。\n"
     "3. as if —「まるで降るかのように」。様態の表現で、備えの意味が出ない。\n"
     "4. unless —「降らない限り持って行け」となり論理が逆さまになる。"),

    (8, 3,
     "(          ) he was very tired, he kept on working.",
     ["Despite", "During", "Because of", "Although"], 4, 2, "SETSU-JOHO",
     "## 🎯 コアイメージ\n"
     "譲歩「〜だけれども」— 後ろに**節 (S + V) が続くなら接続詞 although**、"
     "名詞だけなら前置詞 despite / in spite of。品詞の見極めが全て。\n\n"
     "## 🔬 文構造分析\n"
     "**Although he was very tired**, he kept on working.\n"
     "空所の直後が he was 〜 という節 → 接続詞が要る。\n\n"
     "## 📍 正解の根拠\n"
     "節を従えられる譲歩の語は選択肢の中で **Although** だけ。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Despite — 前置詞。後ろに置けるのは名詞 (Despite his tiredness) で、節は取れない。\n"
     "2. During — 前置詞「〜の間」。節を取れず、譲歩の意味も無い。\n"
     "3. Because of — 前置詞句。節を取れない上、「疲れたから働き続けた」は因果も不自然。"),

    (9, 3,
     "Speak louder (          ) everyone can hear you.",
     ["as if", "even though", "so that", "in order"], 3, 2, "SETSU-MOKUTEKI",
     "## 🎯 コアイメージ\n"
     "**so that + S + can / will =「S が〜できるように」**という目的の副詞節。"
     "can / will が付くのが目的の so that のサイン。\n\n"
     "## 🔬 文構造分析\n"
     "Speak louder **so that everyone can hear** you.\n"
     "大声で話す (手段) → 全員に聞こえる (目的)。can が目的の型を完成させる。\n\n"
     "## 📍 正解の根拠\n"
     "「皆に聞こえる**ように**」+ 節内の can → **so that**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. as if —「まるで皆に聞こえるかのように」。様態で、目的の意味が出ない。\n"
     "2. even though — 譲歩「聞こえるけれども大声で話せ」となり不合理。\n"
     "4. in order — 単独では節を取れない (in order **that** なら可)。"),

    (10, 3,
     "Hurry up, (          ) you will be late for the meeting.",
     ["and", "or", "but", "so"], 2, 2, "SETSU-MEIREI",
     "## 🎯 コアイメージ\n"
     "**命令文 + or 〜 =「…しなさい、さもないと〜」**。命令文 + and 〜 =「…しな"
     "さい、そうすれば〜」とペアで覚える。\n\n"
     "## 🔬 文構造分析\n"
     "Hurry up, **or you will be late** for the meeting.\n"
     "急げ (命令) + or (さもないと) + 遅れる (悪い帰結)。\n\n"
     "## 📍 正解の根拠\n"
     "帰結が「遅れる」という**悪い側** → 「さもないと」の **or**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. and —「急げ、そうすれば遅れる」となり因果が逆さまになる。\n"
     "3. but — 逆接。命令とその帰結をつなぐ働きが無い。\n"
     "4. so —「急げ、だから遅れる」となり意味が通らない。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
