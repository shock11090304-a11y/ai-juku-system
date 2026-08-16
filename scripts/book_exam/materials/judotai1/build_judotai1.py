#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 受動態 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/judotai1/build_judotai1.py

出力 (どちらも**コミットする**): 英文法_受動態_第1集.json / 英文法_受動態_第1集_問題.pdf
★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同時生成 (kateiho2 型)。
★ 正解の位置は 1:2 / 2:3 / 3:3 / 4:2。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_pdf_canon_match.py ② verify() +
  check_grammar_books.py ③ 正解の一意性の敵対的再読。正解になりうる別形
  (例: was seen to enter に対する was seen entering) は**選択肢に入れない**。

取り込み: python3 scripts/book_exam/import_books.py scripts/book_exam/materials/judotai1 \
    --pdf-dir scripts/book_exam/materials/judotai1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_受動態_第1集"
TITLE = "英文法 受動態 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

QUESTIONS = [
    (1, 1,
     "This temple (          ) about five hundred years ago.",
     ["built", "was built", "has built", "is building"], 2, 2, "JUDO-KIHON",
     "## 🎯 コアイメージ\n"
     "主語が動作を「**される側**」なら受動態 be + 過去分詞。寺は「建てられる」"
     "側。時間は be 動詞が背負う (ago → 過去形 was)。\n\n"
     "## 🔬 文構造分析\n"
     "This temple **was built** about five hundred years ago.\n"
     "主語 This temple = build される側。ago (過去の一点) → was + built。\n\n"
     "## 📍 正解の根拠\n"
     "「寺が建てられた」という過去の受け身 → **was built**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. built — 能動の過去形。「寺が (何かを) 建てた」ことになり、目的語も無い。\n"
     "3. has built — 能動の現在完了。ago と共起できない上、寺が建てる側になる。\n"
     "4. is building — 能動の現在進行。500 年前の話に現在形は置けない。"),

    (2, 1,
     "A new bridge (          ) over the river now.",
     ["is building", "builds", "is built", "is being built"], 4, 2, "JUDO-SHINKO",
     "## 🎯 コアイメージ\n"
     "**進行形の受動態 = be + being + 過去分詞**「今まさに〜されている最中」。"
     "be 動詞が進行を、being 以下が受け身を背負う二段構え。\n\n"
     "## 🔬 文構造分析\n"
     "A new bridge **is being built** over the river now.\n"
     "is (現在) + being (進行) + built (受け身)。橋は「建てられている」最中。\n\n"
     "## 📍 正解の根拠\n"
     "now + 建設の真っ最中 + 橋は建てられる側 → **is being built**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. is building — 能動の進行形。「橋が (何かを) 建てている」ことになる。\n"
     "2. builds — 能動の現在形。同じく橋が建てる側になり、now の進行も出ない。\n"
     "3. is built — 単純な受動の現在形は習慣・状態向き。「今まさに」の進行が表せない。"),

    (3, 1,
     "The top of the mountain (          ) with snow all year round.",
     ["covers", "is covering", "is covered", "is being covered"], 3, 2, "JUDO-JOTAI",
     "## 🎯 コアイメージ\n"
     "**be covered with 〜 =「〜で覆われている」**という状態の受動態。動作主の "
     "by ではなく、材料・中身を with で示す慣用ペア。\n\n"
     "## 🔬 文構造分析\n"
     "The top of the mountain **is covered with** snow all year round.\n"
     "山頂は雪に「覆われる」側。all year round (一年中) = 恒常的な状態。\n\n"
     "## 📍 正解の根拠\n"
     "覆われた**状態**が一年中続く → 単純現在の受動 **is covered** (+ with)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. covers — 能動。「山頂が (何かを) 覆う」ことになり、with とも合わない。\n"
     "2. is covering — 能動の進行形。同じく山頂が覆う側になる。\n"
     "4. is being covered — 進行の受動「今まさに覆われつつある」。all year round の恒常状態と合わない。"),

    (4, 2,
     "The baby was (          ) by her grandmother.",
     ["taken care of", "taken care", "taking care of", "took care of"], 1, 2,
     "JUDO-GUNDOSHI",
     "## 🎯 コアイメージ\n"
     "**群動詞 (take care of など) は 1 つの動詞のかたまり**として受動態にする。"
     "最後の前置詞 of を**落とさない**のがポイント。\n\n"
     "## 🔬 文構造分析\n"
     "The baby was **taken care of** by her grandmother.\n"
     "Her grandmother took care of the baby. → the baby を主語に。take care of "
     "が丸ごと過去分詞化して taken care of。\n\n"
     "## 📍 正解の根拠\n"
     "take care **of** のかたまりを保ったまま受動化 → was **taken care of**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. taken care — of が欠けている。かたまりの一部を落とすと「誰を」がつながらない。\n"
     "3. taking care of — 能動の進行。「赤ん坊が世話をしている」ことになる。\n"
     "4. took care of — 過去形。直前の was と述語が二重になる。"),

    (5, 2,
     "This work must (          ) by tomorrow morning.",
     ["finish", "be finishing", "be finished", "have finished"], 3, 2, "JUDO-JODOSHI",
     "## 🎯 コアイメージ\n"
     "**助動詞付きの受動態 = 助動詞 + be + 過去分詞**。must / can / will の後ろでも"
     "受け身の芯 (be + p.p.) は変わらない。\n\n"
     "## 🔬 文構造分析\n"
     "This work must **be finished** by tomorrow morning.\n"
     "仕事は「終えられる」側。must (義務) + be finished (受け身)。\n\n"
     "## 📍 正解の根拠\n"
     "主語 This work は finish される側 → must の後ろは **be finished**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. finish — 能動。「仕事が (何かを) 終える」ことになり、目的語も無い。\n"
     "2. be finishing — 能動の進行。同じく仕事が終える側になる。\n"
     "4. have finished — 能動の完了。主語との「される」関係が作れない。"),

    (6, 2,
     "The man was seen (          ) the building late at night.",
     ["enter", "to enter", "entered", "to be entered"], 2, 2, "JUDO-CHIKAKU",
     "## 🎯 コアイメージ\n"
     "**知覚動詞の受動態では、隠れていた to が現れる**: see him enter (原形) → "
     "he was seen **to** enter。make の受動 (be made to do) と同じ現象。\n\n"
     "## 🔬 文構造分析\n"
     "The man was seen **to enter** the building late at night.\n"
     "Someone saw the man enter 〜 の受動態。原形 enter が to enter に変わる。\n\n"
     "## 📍 正解の根拠\n"
     "be seen の後ろに動作を続けるなら **to enter** (to 不定詞)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. enter — 原形が置けるのは能動 (saw him enter) のときだけ。受動では to が要る。\n"
     "3. entered — 過去形・過去分詞。was seen と並べる形が無い。\n"
     "4. to be entered —「建物に入られる」という受動になり意味が通らない。"),

    (7, 3,
     "Everyone was surprised (          ) the news of his sudden resignation.",
     ["with", "for", "to", "at"], 4, 2, "JUDO-KANJO",
     "## 🎯 コアイメージ\n"
     "感情の受動態は**前置詞をセットで暗記**: be surprised **at** (〜に驚く) / "
     "be satisfied with / be interested in。by 以外の前置詞が慣用で決まっている。\n\n"
     "## 🔬 文構造分析\n"
     "Everyone was surprised **at the news** of his sudden resignation.\n"
     "驚きの向かう先 (原因) を at が指す。\n\n"
     "## 📍 正解の根拠\n"
     "be surprised **at** 〜 が固定の型。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. with — be satisfied with (満足) などの型。surprised とは組まない。\n"
     "2. for — surprised for という慣用は無い。\n"
     "3. to — be surprised to hear (不定詞) の形はあるが、名詞 the news を直接は続けられない。"),

    (8, 3,
     "He was made (          ) the room by his mother.",
     ["to clean", "clean", "cleaning", "cleaned"], 1, 2, "JUDO-SHIEKI",
     "## 🎯 コアイメージ\n"
     "**使役 make の受動態でも、隠れていた to が現れる**: made him clean (原形) → "
     "he was made **to** clean。知覚動詞の受動と同じ現象。\n\n"
     "## 🔬 文構造分析\n"
     "He was made **to clean** the room by his mother.\n"
     "His mother made him clean 〜 の受動態。原形 clean が to clean に変わる。\n\n"
     "## 📍 正解の根拠\n"
     "be made の後ろに動作を続けるなら **to clean** (to 不定詞)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. clean — 原形が置けるのは能動 (made him clean) のときだけ。\n"
     "3. cleaning — be made -ing という型は無い。\n"
     "4. cleaned —「彼が掃除される」方向になり、部屋という目的語ともつながらない。"),

    (9, 3,
     "The singer is known (          ) people of all ages.",
     ["by", "to", "with", "as"], 2, 2, "JUDO-KNOWN",
     "## 🎯 コアイメージ\n"
     "**be known to 人 =「〜に知られている」**。know の受動は動作主でも by でなく "
     "to を使う慣用 (be known by は「〜で見分けがつく」という別の意味)。\n\n"
     "## 🔬 文構造分析\n"
     "The singer is known **to people** of all ages.\n"
     "知られている**相手** (あらゆる世代の人々) を to が指す。\n\n"
     "## 📍 正解の根拠\n"
     "「人々に知られている」= be known **to** 〜 の固定ペア。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. by — be known by は「〜によって見分けられる」という別表現になる。\n"
     "3. with — known with という慣用は無い。\n"
     "4. as — be known as は「〜として知られる」。後ろに肩書き・名前が来る形で、people には合わない。"),

    (10, 3,
     "The missing wallet (          ) yet.",
     ["did not find", "has not found", "has not been found", "was not finding"],
     3, 2, "JUDO-KANRYO",
     "## 🎯 コアイメージ\n"
     "**完了形の受動態 = have + been + 過去分詞**。yet (まだ) は完了形の否定文と"
     "組んで「まだ〜されていない」。\n\n"
     "## 🔬 文構造分析\n"
     "The missing wallet **has not been found** yet.\n"
     "財布は「見つけられる」側。has not (完了の否定) + been found (受け身)。\n\n"
     "## 📍 正解の根拠\n"
     "yet + 財布は見つけられる側 → 完了の受動 **has not been found**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. did not find — 能動。「財布が (何かを) 見つけなかった」ことになる。\n"
     "2. has not found — 能動の完了。同じく財布が見つける側になる。\n"
     "4. was not finding — 能動の過去進行。主語との関係も yet との相性も壊れる。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
