#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 分詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/bunshi1/build_bunshi1.py

出力 (どちらも**コミットする**。取り込みセッションが git 経由で受け取るため):
    英文法_分詞_第1集.json        … import_books.py にそのまま渡す bundle
    英文法_分詞_第1集_問題.pdf    … 冊子 (find_pdf の完全一致名: {source の stem}_問題.pdf)

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同じデータから
  同時に生成する (kateiho2 と同じ作り)。
★ 正解の位置は 1:2 問 / 2:3 問 / 3:3 問 / 4:2 問 に配ってある
  (CLAUDE.md「正解番号は偏らせない」)。設問を足したら配り直すこと。
★ 解説は英語教材の 4 セクション形式 (コアイメージ → 文構造分析 → 根拠 → 誤答 NG 理由)。
  番号と選択肢のずれは _grammar_build.verify() が機械で落とす。

取り込み (kamitest-import 環境のセッション or Mac):
    python3 scripts/book_exam/import_books.py scripts/book_exam/materials/bunshi1 \
        --pdf-dir scripts/book_exam/materials/bunshi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_分詞_第1集"
TITLE = "英文法 分詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

# (番号, ページ, 設問文, [選択肢1..4], 正解番号(1起算), 配点, unit_tag, 解説)
QUESTIONS = [
    (1, 1,
     "The girl (          ) the piano over there is my sister.",
     ["played", "plays", "playing", "to playing"], 3, 2, "BUNSHI-GENZAI",
     "## 🎯 コアイメージ\n"
     "分詞 + 語句のかたまりは名詞を**後ろから**修飾できる。名詞が動作を「**する側**」"
     "なら現在分詞 (-ing)、「**される側**」なら過去分詞。\n\n"
     "## 🔬 文構造分析\n"
     "The girl **playing the piano** over there is my sister.\n"
     "playing the piano over there が The girl を後ろから修飾 (= who is playing 〜)。"
     "文全体の述語は is。\n\n"
     "## 📍 正解の根拠\n"
     "The girl はピアノを「弾く側」(能動) で、目的語 the piano を従えている → "
     "現在分詞 **playing**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. played — 過去分詞なら「弾かれる少女」となり不成立。過去形の述語と読んでも、文の述語 is と衝突する。\n"
     "2. plays — 述語動詞がもう 1 つ増え、接続詞なしで is と並ぶことになり形が壊れる。\n"
     "4. to playing — この並びの形は存在しない (to 不定詞なら to play)。"),

    (2, 1,
     "This is a novel (          ) by a famous French author.",
     ["written", "writing", "wrote", "writes"], 1, 2, "BUNSHI-KAKO",
     "## 🎯 コアイメージ\n"
     "名詞が動作を「**される側**」なら過去分詞で後ろから修飾。by 〜 (〜によって) が"
     "続くのは受け身のサイン。\n\n"
     "## 🔬 文構造分析\n"
     "This is a novel **written by** a famous French author.\n"
     "written by 〜 が a novel を後ろから修飾 (= which was written by 〜)。\n\n"
     "## 📍 正解の根拠\n"
     "novel は作家に「書かれる側」。動作主を示す **by** もあるので、受け身の過去分詞 "
     "**written**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. writing — 現在分詞は「書いている側」。小説自身が書くことになり、by 〜 とも合わない。\n"
     "3. wrote — 過去形の述語動詞。関係代名詞なしには novel の後ろに置けない。\n"
     "4. writes — 現在形の述語動詞。同じく接続詞・関係詞なしでは置けない。"),

    (3, 1,
     "(          ) tired after the long walk, she went to bed early.",
     ["Being felt", "To feel", "Felt", "Feeling"], 4, 2, "BUNSHI-KOUBUN",
     "## 🎯 コアイメージ\n"
     "分詞構文は「接続詞 + S + V」を分詞に圧縮した形。主節の主語が動作を「**する側**」"
     "なら現在分詞で始める。\n\n"
     "## 🔬 文構造分析\n"
     "**Feeling tired** after the long walk, she went to bed early.\n"
     "= Because she felt tired 〜。主節の主語 she が feel の主語を兼ねる。\n\n"
     "## 📍 正解の根拠\n"
     "she が「疲れを感じる」側 (能動) → 現在分詞 **Feeling**。feel tired で"
     "「疲れている」。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Being felt — 受け身「感じられて」。she が誰かに感じられることになり意味が通らない。\n"
     "2. To feel — 不定詞だと「感じるために」という目的になり、早く寝た理由の説明にならない。\n"
     "3. Felt — 過去分詞 1 語も受け身の意味。「感じられて」となり不成立。"),

    (4, 2,
     "(          ) from a distance, the rock looks like a human face.",
     ["Seeing", "Seen", "To see", "Having seen"], 2, 2, "BUNSHI-KOUBUN",
     "## 🎯 コアイメージ\n"
     "分詞構文の意味上の主語は**主節の主語**。主節の主語が動作を「される側」なら、"
     "(Being を省いた) 過去分詞で始める。\n\n"
     "## 🔬 文構造分析\n"
     "**Seen from** a distance, the rock looks like a human face.\n"
     "= When it (= the rock) is seen from a distance 〜。主語 the rock は"
     "「見られる」側。\n\n"
     "## 📍 正解の根拠\n"
     "見るのは人で、岩は**見られる**側 → 受け身の分詞構文 **Seen**。「遠くから"
     "見ると」の定番形。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Seeing — 現在分詞だと the rock が「見る側」になってしまう。\n"
     "3. To see —「見るために岩が〜」と主語がねじれる (To see 〜, you would … のように主語が人なら別)。\n"
     "4. Having seen — 完了・能動「見てしまった後で」。岩が見る側になる点で同じく不成立。"),

    (5, 2,
     "He was listening to music with his eyes (          ).",
     ["closed", "closing", "close", "to close"], 1, 2, "BUNSHI-FUZOKU",
     "## 🎯 コアイメージ\n"
     "付帯状況の with + O + 分詞 =「O を〜した (された) 状態で」。O と分詞の間の"
     "**能動か受動か**の関係で分詞を選ぶ。\n\n"
     "## 🔬 文構造分析\n"
     "He was listening to music **with his eyes closed**.\n"
     "his eyes と closed の間は「目が**閉じられている**」という受動の関係。\n\n"
     "## 📍 正解の根拠\n"
     "目は close one's eyes の目的語 = 閉じる動作の「される側」→ 過去分詞 "
     "**closed**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. closing — 現在分詞だと「目が (何かを) 閉じつつある」という能動になり不成立。\n"
     "3. close — 形容詞の close は「近い」。「閉じた状態」の意味にはならない。\n"
     "4. to close — with + O + to 不定詞という形は無い。"),

    (6, 2,
     "(          ) the movie before, I didn't want to see it again.",
     ["Seeing", "Seen", "Having seen", "To see"], 3, 2, "BUNSHI-KANRYO",
     "## 🎯 コアイメージ\n"
     "分詞構文で「主節より**前**の時間」をはっきり示すときは完了形 **Having + "
     "過去分詞**。\n\n"
     "## 🔬 文構造分析\n"
     "**Having seen** the movie **before**, I didn't want to see it again.\n"
     "= Because I had seen the movie before 〜。「見た」のは「見たくなかった」"
     "時点より前。\n\n"
     "## 📍 正解の根拠\n"
     "before (以前に) がある以上、映画を見たのは主節より前の時間 → 完了形 "
     "**Having seen**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Seeing — 単純形は主節と**同じ時**を表すのが基本。before との時間差に合わない。\n"
     "2. Seen — 受け身「見られて」。I が見られることになり不成立。\n"
     "4. To see —「見るために」。「もう見たくない」理由の説明にならない。"),

    (7, 3,
     "I saw a stranger (          ) around the house last night.",
     ["wandered", "wandering", "to wander", "wanders"], 2, 2, "BUNSHI-CHIKAKU",
     "## 🎯 コアイメージ\n"
     "知覚動詞 see / hear + O + **-ing** =「O が〜している**ところ**を見る・聞く」。"
     "動作の途中を切り取るニュアンス。\n\n"
     "## 🔬 文構造分析\n"
     "I saw a stranger **wandering around** the house last night.\n"
     "see + O (a stranger) + 現在分詞 (wandering)。a stranger が「うろつく」側。\n\n"
     "## 📍 正解の根拠\n"
     "見知らぬ人が「うろついている最中」を目撃した — O と分詞が能動・進行の関係"
     "なので **wandering**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. wandered — 過去分詞は「O が〜される」の受動。wander (うろつく) に受け身の関係は作れない。\n"
     "3. to wander — see + O + to 不定詞の形は取れない (受動態 be seen to do のときだけ to が現れる)。\n"
     "4. wanders — 定形動詞。接続詞なしで saw の後ろには置けない。"),

    (8, 3,
     "I had my smartphone (          ) at the shop yesterday.",
     ["repair", "repairing", "to repair", "repaired"], 4, 2, "BUNSHI-SHIEKI",
     "## 🎯 コアイメージ\n"
     "have + O + **過去分詞** =「O を〜して**もらう**」(使役)。O が動作を「される側」"
     "のときの形。\n\n"
     "## 🔬 文構造分析\n"
     "I **had** my smartphone **repaired** at the shop yesterday.\n"
     "my smartphone は「修理**される**」側。have + O + p.p. の型。\n\n"
     "## 📍 正解の根拠\n"
     "スマホは店に「直してもらう」= 修理される側 → 過去分詞 **repaired**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. repair — have + O + 原形は「O (人) に〜させる」。スマホが修理する側になってしまう。\n"
     "2. repairing —「スマホが修理している最中」という能動になり不成立。\n"
     "3. to repair — have + O + to 不定詞という形は無い (get + O + to do なら O は人)。"),

    (9, 3,
     "The result of the experiment was really (          ) to us all.",
     ["surprised", "surprising", "surprise", "to surprising"], 2, 2, "BUNSHI-KANJO",
     "## 🎯 コアイメージ\n"
     "感情を表す動詞の分詞は「感情を**与える側 = -ing / 受ける側 = -ed**」。"
     "物・事が主語なら、驚きを与える側で -ing。\n\n"
     "## 🔬 文構造分析\n"
     "The result of the experiment was really **surprising** to us all.\n"
     "主語は The result (物事)。結果が私たちに驚きを**与える**側。\n\n"
     "## 📍 正解の根拠\n"
     "主語が感情の**原因** (物事) → 現在分詞 **surprising**「(人を) 驚かせる"
     "ような」。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. surprised —「驚かされた」= 感情を受ける側。人が主語のときの形 (We were surprised)。\n"
     "3. surprise — 名詞なら a surprise と冠詞が要り、副詞 really との並びに合わない。\n"
     "4. to surprising — この並びの形は存在しない。"),

    (10, 3,
     "We will hold the game tomorrow, weather (          ).",
     ["permits", "permitted", "permitting", "to permit"], 3, 2, "BUNSHI-DOKURITSU",
     "## 🎯 コアイメージ\n"
     "主節の主語と**別の主語**を分詞の前に置く形が独立分詞構文。**weather "
     "permitting** =「天気が許せば」は決まり文句。\n\n"
     "## 🔬 文構造分析\n"
     "We will hold the game tomorrow, **weather permitting**.\n"
     "= if the weather permits。分詞 permitting の意味上の主語 weather を前に"
     "置いている。\n\n"
     "## 📍 正解の根拠\n"
     "weather が「許す」側 (能動) → 現在分詞 **permitting**。慣用表現として"
     "この形で覚える。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. permits — 定形動詞。接続詞 if なしでは 2 つ目の文を作れない。\n"
     "2. permitted — 受け身「天気が許されれば」となり主客が逆。\n"
     "4. to permit — 不定詞に意味上の主語を裸で前置するこの形は無い。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
