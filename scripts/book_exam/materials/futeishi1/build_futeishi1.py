#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 不定詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/futeishi1/build_futeishi1.py

出力 (どちらも**コミットする**。取り込みセッションが git 経由で受け取るため):
    英文法_不定詞_第1集.json        … import_books.py にそのまま渡す bundle
    英文法_不定詞_第1集_問題.pdf    … 冊子 (find_pdf の完全一致名: {source の stem}_問題.pdf)

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同じデータから
  同時に生成する (kateiho2 と同じ作り)。
★ 正解の位置は 1:2 問 / 2:3 問 / 3:3 問 / 4:2 問 に配ってある
  (CLAUDE.md「正解番号は偏らせない」)。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ①build 後に check_pdf_canon_match.py で刷り上がりを
  逆照合 ②_grammar_build.verify() + check_grammar_books.py ③正解の一意性は敵対的に再読する。
  正解になりうる別形 (例: so as not to に対する in order not to) は**選択肢に入れない**。

取り込み (kamitest-import 環境のセッション or Mac):
    python3 scripts/book_exam/import_books.py scripts/book_exam/materials/futeishi1 \
        --pdf-dir scripts/book_exam/materials/futeishi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_不定詞_第1集"
TITLE = "英文法 不定詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

# (番号, ページ, 設問文, [選択肢1..4], 正解番号(1起算), 配点, unit_tag, 解説)
QUESTIONS = [
    (1, 1,
     "It is important (          ) breakfast every morning.",
     ["eat", "ate", "to eat", "eaten"], 3, 2, "FUTEI-KEISHIKI",
     "## 🎯 コアイメージ\n"
     "**It is 〜 to do … の形式主語構文**。頭でっかちな不定詞の主語を後ろへ回し、"
     "仮の主語 It を立てる。It =「to 以下のこと」。\n\n"
     "## 🔬 文構造分析\n"
     "**It** is important **to eat breakfast** every morning.\n"
     "It = to eat breakfast every morning。「毎朝朝食をとること」が本当の主語。\n\n"
     "## 📍 正解の根拠\n"
     "形式主語 It を受けて「〜すること」を表すのは **to eat** (名詞的用法)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. eat — 原形のままでは It との文法関係が作れない (述語は is がもうある)。\n"
     "2. ate — 過去形の述語動詞。is と衝突する。\n"
     "4. eaten — 過去分詞単独。「食べられる」方向になり、It とのつながりも作れない。"),

    (2, 1,
     "I don't know (          ) this machine.",
     ["how to use", "what to use", "how using", "for using"], 1, 2, "FUTEI-GIMONSHI",
     "## 🎯 コアイメージ\n"
     "**疑問詞 + to 不定詞**で「〜すべきか」の名詞のかたまりを作る: how to do "
     "(やり方) / what to do (何をすべきか) / where to go (どこへ行くべきか)。\n\n"
     "## 🔬 文構造分析\n"
     "I don't know **how to use this machine**.\n"
     "how to use this machine (この機械の使い方) 全体が know の目的語。use の"
     "目的語は this machine で埋まっている。\n\n"
     "## 📍 正解の根拠\n"
     "「使い**方**が分からない」+ use の目的語 (this machine) が後ろに残っている → "
     "**how to use**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. what to use — what は use の目的語になるはずだが、this machine が既に目的語で衝突する。\n"
     "3. how using — 疑問詞に -ing は続かない。to 不定詞の形にする。\n"
     "4. for using —「〜のために」。know の目的語 (名詞のかたまり) が無くなり文が壊れる。"),

    (3, 1,
     "This coffee is too hot for me (          ).",
     ["drinking", "drink", "to drinking", "to drink"], 4, 2, "FUTEI-TOO",
     "## 🎯 コアイメージ\n"
     "**too 〜 (for 人) to do =「…が〜するには…すぎる」= 熱すぎて飲めない**。"
     "too が限度超えを宣言し、to 以下が「何をするには」を示す。\n\n"
     "## 🔬 文構造分析\n"
     "This coffee is **too hot for me to drink**.\n"
     "for me = to drink の意味上の主語。drink の目的語は主語 This coffee と同じ"
     "なので**書かない** (to drink it としない)。\n\n"
     "## 📍 正解の根拠\n"
     "too + 形容詞とセットで「〜するには」を作るのは **to drink** (to 不定詞)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. drinking — too 〜 と呼応する形は to 不定詞。-ing では構文にならない。\n"
     "2. drink — 原形だけでは for me とも too hot ともつながらない。\n"
     "3. to drinking — to の後ろは原形。-ing を続けるのは前置詞の to だけ。"),

    (4, 2,
     "He was kind (          ) to carry my bag upstairs.",
     ["so", "enough", "too", "very"], 2, 2, "FUTEI-ENOUGH",
     "## 🎯 コアイメージ\n"
     "**形容詞 + enough to do =「〜するのに十分…」**。enough は形容詞・副詞の"
     "**後ろ**に置く、という語順まで含めて 1 つの型。\n\n"
     "## 🔬 文構造分析\n"
     "He was **kind enough to carry** my bag upstairs.\n"
     "kind enough (十分に親切) + to carry (運んでくれるほど)。「親切にも〜して"
     "くれた」と訳す定番形。\n\n"
     "## 📍 正解の根拠\n"
     "形容詞 kind の直後に置けて to 不定詞と呼応するのは **enough** だけ。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. so — kind so to carry という語順は無い (so kind **as** to carry なら別の型)。\n"
     "3. too — too は形容詞の**前**に置く語。kind too という語順が壊れている上、意味も「〜すぎて…できない」で逆。\n"
     "4. very — very も形容詞の前に置く語。後ろには置けず、to 不定詞とも呼応しない。"),

    (5, 2,
     "He seems (          ) ill last week.",
     ["to be", "being", "to have been", "to being"], 3, 2, "FUTEI-KANRYO",
     "## 🎯 コアイメージ\n"
     "**to have + 過去分詞 (完了不定詞) = 述語動詞より前の時間**を表す。"
     "seems (今そう見える) より前の last week の話は to have been。\n\n"
     "## 🔬 文構造分析\n"
     "He **seems to have been** ill **last week**.\n"
     "= It seems that he **was** ill last week。seems (現在) と was (過去) の"
     "時間差を to have been が背負う。\n\n"
     "## 📍 正解の根拠\n"
     "last week (過去) の内容を現在の seems の後ろに置く → 完了不定詞 "
     "**to have been**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. to be — seems と同じ時 (今病気に見える) になり、last week と合わない。\n"
     "2. being — seem の後ろに -ing は続かない。\n"
     "4. to being — to 不定詞の to の後ろは原形。-ing は置けない。"),

    (6, 2,
     "It was careless (          ) you to leave your umbrella on the train.",
     ["of", "for", "to", "with"], 1, 2, "FUTEI-SEISHITSU",
     "## 🎯 コアイメージ\n"
     "不定詞の意味上の主語は普通 **for 人**。ただし kind / careless / foolish など"
     "**人の性質をほめる・責める形容詞のときは of 人**になる。\n\n"
     "## 🔬 文構造分析\n"
     "It was careless **of you** to leave your umbrella on the train.\n"
     "careless は「あなた」の性質の評価 → of you。You were careless と言い換え"
     "られるのが of のサイン。\n\n"
     "## 📍 正解の根拠\n"
     "careless = 人の性質を表す形容詞 → 意味上の主語は **of** you。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. for — 性質の形容詞でないとき (important / necessary など) の形。\n"
     "3. to — careless to you では「あなたに対して不注意」となり、忘れ物をした本人の性質を表せない。\n"
     "4. with — この構文で意味上の主語を導く働きは無い。"),

    (7, 3,
     "My mother made me (          ) my room before dinner.",
     ["cleaned", "clean", "to clean", "cleaning"], 2, 2, "FUTEI-SHIEKI",
     "## 🎯 コアイメージ\n"
     "**使役動詞 make + O + 動詞の原形 =「O に (強制的に) 〜させる」**。make / "
     "let / have の後ろは to の無い**原形不定詞**。\n\n"
     "## 🔬 文構造分析\n"
     "My mother **made me clean** my room before dinner.\n"
     "made (使役) + me (させられる人) + clean (原形)。me と clean は「私が掃除"
     "する」という能動の関係。\n\n"
     "## 📍 正解の根拠\n"
     "使役の make の後ろは原形 → **clean**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. cleaned — 過去分詞だと「私が掃除される」という受動になり不成立。\n"
     "3. to clean — make に to 不定詞は続かない (受動態 be made **to** clean のときだけ to が現れる)。\n"
     "4. cleaning — make + O + -ing という型は無い。"),

    (8, 3,
     "(          ), I have never read the book.",
     ["Telling the truth", "Told the truth", "For telling the truth",
      "To tell the truth"], 4, 2, "FUTEI-DOKURITSU",
     "## 🎯 コアイメージ\n"
     "**独立不定詞** = 文全体を修飾する決まり文句: to tell the truth (実を言うと) / "
     "to be honest (正直に言うと) / to make matters worse (さらに悪いことに)。\n\n"
     "## 🔬 文構造分析\n"
     "**To tell the truth**, I have never read the book.\n"
     "To tell the truth が文頭でコンマまでのかたまりを作り、後ろの文全体に"
     "「実を言うと」の注釈を付ける。\n\n"
     "## 📍 正解の根拠\n"
     "「実を言うと」は **to tell the truth** で固定の慣用表現。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Telling the truth —「実を言うと」の慣用は to 不定詞で固定 (frankly speaking と混同しない)。\n"
     "2. Told the truth — 過去分詞では「真実を告げられて」となり意味を成さない。\n"
     "3. For telling the truth —「真実を言ったことに対して」となり、注釈の働きをしない。"),

    (9, 3,
     "The doctor told him (          ) smoking.",
     ["giving up", "give up", "to give up", "to giving up"], 3, 2, "FUTEI-SVOC",
     "## 🎯 コアイメージ\n"
     "**tell + O + to do =「O に〜するように言う」**。tell / ask / advise / want "
     "は「O + to 不定詞」の型を取る (原形は続かない — make / let との違い)。\n\n"
     "## 🔬 文構造分析\n"
     "The doctor **told him to give up** smoking.\n"
     "him = to give up の意味上の主語。「彼がタバコをやめる」よう医者が指示した。\n\n"
     "## 📍 正解の根拠\n"
     "tell + O の後ろに動作を続けるなら **to give up** (to 不定詞)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. giving up — tell + O + -ing という型は無い。\n"
     "2. give up — 原形が続くのは使役 (make / let / have) と知覚動詞。tell は違う。\n"
     "4. to giving up — to 不定詞の to の後ろは原形。-ing は置けない。"),

    (10, 3,
     "She left home early (          ) miss the first train.",
     ["so as to not", "so as not to", "not so as to", "so not as to"], 2, 2,
     "FUTEI-MOKUTEKI",
     "## 🎯 コアイメージ\n"
     "目的「〜するために」は so as to do。**否定「〜しないように」は not を to の"
     "直前**に置いて so as **not to** do。\n\n"
     "## 🔬 文構造分析\n"
     "She left home early **so as not to miss** the first train.\n"
     "= in order not to miss 〜。「始発を逃さないように」早く家を出た。\n\n"
     "## 📍 正解の根拠\n"
     "不定詞の否定は **to の直前に not** → so as **not to** miss。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. so as to not — not は to の後ろでなく直前に置く。\n"
     "3. not so as to — not が構文全体の前に出るこの語順は無い。\n"
     "4. so not as to — so と as の間に not は挟めない。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
