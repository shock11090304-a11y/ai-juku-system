#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 動名詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/domeishi1/build_domeishi1.py

出力 (どちらも**コミットする**。取り込みセッションが git 経由で受け取るため):
    英文法_動名詞_第1集.json        … import_books.py にそのまま渡す bundle
    英文法_動名詞_第1集_問題.pdf    … 冊子 (find_pdf の完全一致名: {source の stem}_問題.pdf)

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同じデータから
  同時に生成する (kateiho2 と同じ作り)。
★ 正解の位置は 1:2 問 / 2:3 問 / 3:3 問 / 4:2 問 に配ってある
  (CLAUDE.md「正解番号は偏らせない」)。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ①build 後に check_pdf_canon_match.py で刷り上がりを
  逆照合 ②_grammar_build.verify() + check_grammar_books.py ③正解の一意性は敵対的に再読する。
  forget/stop など不定詞との対比問題は、時間指標や文脈の 1 文で誤答が切れることを確認する。
  正解になりうる別形 (例: needs repairing に対する needs to be repaired) は**選択肢に入れない**。

取り込み (kamitest-import 環境のセッション or Mac):
    python3 scripts/book_exam/import_books.py scripts/book_exam/materials/domeishi1 \
        --pdf-dir scripts/book_exam/materials/domeishi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_動名詞_第1集"
TITLE = "英文法 動名詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

# (番号, ページ, 設問文, [選択肢1..4], 正解番号(1起算), 配点, unit_tag, 解説)
QUESTIONS = [
    (1, 1,
     "My grandfather enjoys (          ) in the park every morning.",
     ["to walk", "walk", "walked", "walking"], 4, 2, "DOMEI-MOKUTEKIGO",
     "## 🎯 コアイメージ\n"
     "**enjoy は動名詞 (-ing) だけを目的語に取る**動詞。enjoy / finish / mind / "
     "give up / avoid / practice がこの仲間 (megafeps の一部)。\n\n"
     "## 🔬 文構造分析\n"
     "My grandfather **enjoys walking** in the park every morning.\n"
     "enjoys の目的語 = walking (歩くこと)。動名詞が名詞の働きをしている。\n\n"
     "## 📍 正解の根拠\n"
     "enjoy + -ing は固定の型 → **walking**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. to walk — enjoy は to 不定詞を目的語に取らない。\n"
     "2. walk — 原形。enjoys という述語の後ろに裸の動詞は置けない。\n"
     "3. walked — 過去形・過去分詞。目的語の位置に置けない。"),

    (2, 1,
     "She is good at (          ) pictures.",
     ["draw", "drawing", "to draw", "drawn"], 2, 2, "DOMEI-ZENCHISHI",
     "## 🎯 コアイメージ\n"
     "**前置詞の後ろに動詞を置くなら動名詞**。前置詞の目的語になれるのは名詞の"
     "働きをする形 = -ing だけ。\n\n"
     "## 🔬 文構造分析\n"
     "She is good **at drawing** pictures.\n"
     "be good at 〜 (〜が得意だ) の at は前置詞。その目的語が drawing pictures。\n\n"
     "## 📍 正解の根拠\n"
     "前置詞 at の直後 → 動名詞 **drawing**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. draw — 原形は前置詞の目的語になれない。\n"
     "3. to draw — 前置詞の直後に to 不定詞は置けない。\n"
     "4. drawn — 過去分詞。名詞の働きが無く、at の目的語になれない。"),

    (3, 1,
     "Would you mind (          ) the window? It's a little cold in here.",
     ["to close", "close", "closing", "closed"], 3, 2, "DOMEI-MIND",
     "## 🎯 コアイメージ\n"
     "**Would you mind -ing? =「〜していただけませんか」**。mind (〜を嫌がる) は"
     "動名詞だけを目的語に取る動詞。直訳は「〜するのは嫌ですか」。\n\n"
     "## 🔬 文構造分析\n"
     "Would you **mind closing** the window?\n"
     "mind の目的語 = closing the window (窓を閉めること)。\n\n"
     "## 📍 正解の根拠\n"
     "mind + -ing は固定の型 → **closing**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. to close — mind は to 不定詞を目的語に取らない。\n"
     "2. close — 原形。mind の目的語の位置に裸の動詞は置けない。\n"
     "4. closed — 過去分詞。「閉められる」方向になり、依頼の意味を作れない。"),

    (4, 2,
     "I'll never forget (          ) the Alps for the first time last summer.",
     ["seeing", "to see", "see", "to seeing"], 1, 2, "DOMEI-TAIHI",
     "## 🎯 コアイメージ\n"
     "forget / remember は後ろの形で意味が変わる: **-ing =「〜した (過去の) こと」 / "
     "to do =「(これから) 〜すること」**。動名詞は過去向き、不定詞は未来向き。\n\n"
     "## 🔬 文構造分析\n"
     "I'll never forget **seeing the Alps** for the first time **last summer**.\n"
     "last summer (去年の夏) = もう起きた経験 → forget + -ing「見たことを忘れ"
     "ない」。\n\n"
     "## 📍 正解の根拠\n"
     "去年の夏に**見た**という過去の経験の記憶 → **seeing**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. to see — forget to do は「これから見ることを忘れる」。last summer と時間が逆。\n"
     "3. see — 原形。forget の目的語の位置に裸の動詞は置けない。\n"
     "4. to seeing — forget はこの形を取らない (look forward to -ing と混同しない)。"),

    (5, 2,
     "The doctor advised my father to stop (          ).",
     ["smoke", "to smoking", "to smoke", "smoking"], 4, 2, "DOMEI-STOP",
     "## 🎯 コアイメージ\n"
     "**stop -ing =「〜するのをやめる」 / stop to do =「〜するために立ち止まる」**。"
     "-ing はやめる対象 (目的語)、to do は立ち止まる目的 (副詞) で役割が違う。\n\n"
     "## 🔬 文構造分析\n"
     "The doctor advised my father to **stop smoking**.\n"
     "stop の目的語 = smoking。「喫煙という習慣をやめる」ことを医者が勧めた。\n\n"
     "## 📍 正解の根拠\n"
     "医者が勧めるのは「タバコを**やめる**こと」→ stop + 動名詞 **smoking**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. smoke — 原形。stop の目的語の位置に裸の動詞は置けない。\n"
     "2. to smoking — stop はこの形を取らない。\n"
     "3. to smoke —「タバコを吸うために立ち止まる」となり、医者の助言として意味が通らない。"),

    (6, 2,
     "I'm looking forward to (          ) you again soon.",
     ["see", "seeing", "have seen", "be seen"], 2, 2, "DOMEI-TOING",
     "## 🎯 コアイメージ\n"
     "**look forward to の to は前置詞**。だから後ろは動名詞。be used to -ing / "
     "object to -ing も同じ仲間 —「to があれば原形」という思い込みを突く定番。\n\n"
     "## 🔬 文構造分析\n"
     "I'm looking forward **to seeing** you again soon.\n"
     "to (前置詞) + seeing (動名詞) =「会えること」を楽しみに待つ。\n\n"
     "## 📍 正解の根拠\n"
     "この to は前置詞 → 動名詞 **seeing**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. see — to を不定詞と誤解した形。前置詞の後ろに原形は置けない。\n"
     "3. have seen — 完了形。前置詞の目的語になれない。\n"
     "4. be seen — 受け身の原形。「あなたに会う」という能動の内容にも、前置詞の後ろという位置にも合わない。"),

    (7, 3,
     "There is no (          ) what will happen in the future.",
     ["telling", "to tell", "told", "tell"], 1, 2, "DOMEI-KANYO",
     "## 🎯 コアイメージ\n"
     "**There is no -ing =「〜することはできない」**という動名詞の慣用表現。"
     "= It is impossible to do。There is no telling 〜 (〜は分からない) が代表例。\n\n"
     "## 🔬 文構造分析\n"
     "There is no **telling** what will happen in the future.\n"
     "no + telling (動名詞)。「未来に何が起きるかは誰にも分からない」。\n\n"
     "## 📍 正解の根拠\n"
     "There is no + **動名詞**の慣用 → **telling**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. to tell — この慣用は動名詞で固定。to 不定詞は続かない。\n"
     "3. told — 過去分詞。no の後ろの名詞の位置に置けない。\n"
     "4. tell — 原形。同じく名詞の働きが無く置けない。"),

    (8, 3,
     "There is no hope of (          ) the game.",
     ["we win", "we winning", "our winning", "us to win"], 3, 2, "DOMEI-SHUGO",
     "## 🎯 コアイメージ\n"
     "動名詞に**意味上の主語**を付けるときは**所有格 (または目的格)** を -ing の"
     "直前に置く: our winning =「私たちが勝つこと」。\n\n"
     "## 🔬 文構造分析\n"
     "There is no hope of **our winning** the game.\n"
     "of (前置詞) + our (意味上の主語) + winning (動名詞)。「私たちがその試合に"
     "勝つ見込みは無い」。\n\n"
     "## 📍 正解の根拠\n"
     "前置詞 of の後ろで「私たちが勝つこと」→ 所有格 + 動名詞 = **our "
     "winning**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. we win — 主語 + 動詞の節は前置詞の目的語になれない。\n"
     "2. we winning — 意味上の主語に主格 we は使えない (所有格 our か目的格 us)。\n"
     "4. us to win — of の後ろに「目的格 + to 不定詞」の形は置けない。"),

    (9, 3,
     "This museum is well worth (          ).",
     ["to visit", "visiting", "visited", "to visiting"], 2, 2, "DOMEI-WORTH",
     "## 🎯 コアイメージ\n"
     "**be worth -ing =「〜する価値がある」**。worth の後ろは動名詞で固定。"
     "well worth と強調しても型は変わらない。\n\n"
     "## 🔬 文構造分析\n"
     "This museum is well worth **visiting**.\n"
     "主語 This museum が visiting の意味上の目的語を兼ねる (visit it としない) "
     "のがこの構文の癖。\n\n"
     "## 📍 正解の根拠\n"
     "worth の後ろは動名詞 → **visiting**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. to visit — worth に to 不定詞は続かない。\n"
     "3. visited — 過去分詞。worth の後ろの名詞の位置に置けない。\n"
     "4. to visiting — worth はこの形を取らない (to 自体が不要)。"),

    (10, 3,
     "This old watch needs (          ).",
     ["to repair", "repaired", "repairing", "to be repairing"], 3, 2, "DOMEI-NEED",
     "## 🎯 コアイメージ\n"
     "**need -ing =「〜される必要がある」**。主語が動作を「される側」なのに、"
     "形は能動の -ing で受け身の意味を表す変わり者 (= need to be repaired)。\n\n"
     "## 🔬 文構造分析\n"
     "This old watch **needs repairing**.\n"
     "watch は「修理される」側。needs + repairing で「修理 (されること) を必要と"
     "している」。\n\n"
     "## 📍 正解の根拠\n"
     "物が主語の need の後ろは動名詞 → **repairing** (受け身の意味)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. to repair — 能動「時計が (何かを) 修理する」ことになり不成立 (needs to **be** repaired なら可)。\n"
     "2. repaired — needs の目的語に過去分詞単独は置けない。\n"
     "4. to be repairing —「修理している最中である必要」となり意味を成さない。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
