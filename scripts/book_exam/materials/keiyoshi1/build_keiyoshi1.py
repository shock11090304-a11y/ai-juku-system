#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 形容詞・副詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/keiyoshi1/build_keiyoshi1.py

出力 (どちらも**コミットする**): 英文法_形容詞副詞_第1集.json / 英文法_形容詞副詞_第1集_問題.pdf
★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同時生成 (kateiho2 型)。
★ 正解の位置は 1:2 / 2:3 / 3:3 / 4:2。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_pdf_canon_match.py ② verify() +
  check_grammar_books.py ③ 正解の一意性の敵対的再読。叙述で両立する形
  (例: 限定の sleeping に対する叙述の asleep) は**限定位置の設問にして**曖昧さを断つ。

取り込み: python3 scripts/book_exam/import_books.py scripts/book_exam/materials/keiyoshi1 \
    --pdf-dir scripts/book_exam/materials/keiyoshi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_形容詞副詞_第1集"
TITLE = "英文法 形容詞・副詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

QUESTIONS = [
    (1, 1,
     "I want to drink (          ) because it's so hot today.",
     ["cold something", "something cold", "something coldly", "cold of something"],
     2, 2, "KEIYO-GOCHI",
     "## 🎯 コアイメージ\n"
     "**-thing / -one / -body を修飾する形容詞は後ろに置く**: something cold / "
     "someone famous。普段の「形容詞 + 名詞」と逆になる特別ルール。\n\n"
     "## 🔬 文構造分析\n"
     "I want to drink **something cold** because it's so hot today.\n"
     "something (代名詞) + cold (後置の形容詞) =「何か冷たいもの」。\n\n"
     "## 📍 正解の根拠\n"
     "-thing 系は形容詞を**後置** → **something cold**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. cold something — -thing 系に前置はできない。語順が逆。\n"
     "3. something coldly — coldly は副詞。名詞 something を修飾できない。\n"
     "4. cold of something — この形は存在しない。"),

    (2, 1,
     "I was so tired that I could (          ) keep my eyes open.",
     ["hard", "hardly ever", "hardly", "harder"], 3, 2, "KEIYO-HITEI",
     "## 🎯 コアイメージ\n"
     "**hardly =「ほとんど〜ない」という準否定の副詞**。hard (熱心に・激しく) とは"
     "別の単語と考える。can hardly do =「ほとんど〜できない」。\n\n"
     "## 🔬 文構造分析\n"
     "I was so tired that I could **hardly keep** my eyes open.\n"
     "so 〜 that (とても疲れていたので) + could hardly (ほとんど〜できなかった)。\n\n"
     "## 📍 正解の根拠\n"
     "「目を開けていられ**ないほど**」という準否定 → **hardly**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. hard —「熱心に・激しく」。否定の意味は無く、「懸命に目を開けた」となり that 節の因果が壊れる。\n"
     "2. hardly ever — 頻度「めったに〜ない」。この場は一度きりの状況なので合わない。\n"
     "4. harder — hard の比較級。同じく否定の意味が出ない。"),

    (3, 1,
     "Look at that (          ) baby on the sofa.",
     ["sleeping", "asleep", "slept", "sleepily"], 1, 2, "KEIYO-GENTEI",
     "## 🎯 コアイメージ\n"
     "**a- で始まる形容詞 (asleep / alive / awake) は叙述専用** — 名詞の前 (限定"
     "用法) には置けない。名詞の前で「眠っている」は sleeping を使う。\n\n"
     "## 🔬 文構造分析\n"
     "Look at that **sleeping baby** on the sofa.\n"
     "baby を**前から**修飾する位置 (限定用法) → 分詞由来の sleeping。\n\n"
     "## 📍 正解の根拠\n"
     "名詞の前の位置 → asleep は不可、**sleeping** の一択。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. asleep — 叙述専用 (The baby is asleep は可)。名詞の前には置けない。\n"
     "3. slept —「眠られた赤ん坊」という受動になり不成立。\n"
     "4. sleepily — 副詞。名詞 baby を修飾できない。"),

    (4, 2,
     "There is (          ) milk left in the bottle, so we have to buy some today.",
     ["a few", "few", "a little", "little"], 4, 2, "KEIYO-SURYO",
     "## 🎯 コアイメージ\n"
     "数えられない名詞は little / a little、数えられる名詞は few / a few。"
     "**a が付けば肯定 (少しある)、無ければ否定 (ほとんど無い)**。\n\n"
     "## 🔬 文構造分析\n"
     "There is **little milk** left in the bottle, so we **have to buy** some "
     "today.\n"
     "milk = 不可算。後半「買わなければ」= 足りていない、という否定方向。\n\n"
     "## 📍 正解の根拠\n"
     "不可算の milk + 「買い足しが必要」という不足の文脈 → **little** (ほとんど"
     "無い)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. a few — 可算名詞用。milk は数えられない。\n"
     "2. few — これも可算名詞用。\n"
     "3. a little —「少しは**ある**」という肯定の含み。買い足しが必要な文脈と合わない。"),

    (5, 2,
     "The pianist is (          ) respected all over the world.",
     ["high", "highest", "highly", "more high"], 3, 2, "KEIYO-FUKUSHI",
     "## 🎯 コアイメージ\n"
     "**同じ語源で意味が分かれる副詞**: high (物理的に高く) / **highly (程度が"
     "大きく・非常に)**。late/lately、near/nearly も同じ仲間。\n\n"
     "## 🔬 文構造分析\n"
     "The pianist is **highly respected** all over the world.\n"
     "respected (尊敬されている) の**程度**を強める → highly。\n\n"
     "## 📍 正解の根拠\n"
     "評価の高さ (程度) を表す → **highly** respected。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. high — 物理的な高さ (jump high)。評価の程度には使わない。\n"
     "2. highest — 最上級の形容詞。respected を修飾する副詞の位置に合わない。\n"
     "4. more high — high の比較級は higher。この形自体が誤り。"),

    (6, 2,
     "Have you seen any good movies (          )?",
     ["late", "lately", "later", "latest"], 2, 2, "KEIYO-LATELY",
     "## 🎯 コアイメージ\n"
     "**lately =「最近」**(現在完了と相性が良い) / late =「遅く」(時刻が遅い)。"
     "high/highly と同じ「-ly で意味が変わる」ペア。\n\n"
     "## 🔬 文構造分析\n"
     "**Have you seen** any good movies **lately**?\n"
     "現在完了 (経験・近況) + lately (最近) の定番コンビ。\n\n"
     "## 📍 正解の根拠\n"
     "「**最近**いい映画を見た?」→ **lately**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. late —「(時刻が) 遅く」。see movies late では「夜遅くに見る」となり近況を聞く文にならない。\n"
     "3. later —「あとで」。未来向きの語で、現在完了の疑問文と合わない。\n"
     "4. latest —「最新の」(形容詞)。文末で副詞の働きはできない。"),

    (7, 3,
     "(          ) all the seats in the theater were taken.",
     ["Most", "Almost of", "The most", "Almost"], 4, 2, "KEIYO-ALMOST",
     "## 🎯 コアイメージ\n"
     "**almost は副詞 —「all・every・no などの語を**修飾する**」**: almost all "
     "(ほとんど全部) / almost every。名詞そのものは修飾できない。\n\n"
     "## 🔬 文構造分析\n"
     "**Almost all the seats** in the theater were taken.\n"
     "almost (副詞) が all を修飾 → almost all the + 名詞。\n\n"
     "## 📍 正解の根拠\n"
     "直後に all がある → all を強める副詞 **Almost**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. Most — Most all という並びは標準では不可 (Most of the seats か Most seats)。\n"
     "2. Almost of — この形は存在しない。\n"
     "3. The most — 最上級の形。all の前には置けない。"),

    (8, 3,
     "About three (          ) people attended the annual festival.",
     ["hundred", "hundreds", "hundred of", "hundreds of"], 1, 2, "KEIYO-SUSHI",
     "## 🎯 コアイメージ\n"
     "**数詞 + hundred / thousand は単数形のまま**: three hundred people。"
     "「何百もの」と漠然と言うときだけ hundreds of と複数になる。\n\n"
     "## 🔬 文構造分析\n"
     "About **three hundred people** attended the annual festival.\n"
     "three (具体的な数詞) + hundred (単数形) + 名詞。\n\n"
     "## 📍 正解の根拠\n"
     "数詞 three が前にある → **hundred** (s も of も付けない)。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. hundreds — 数詞の直後では複数形にしない (three hundreds は誤り)。\n"
     "3. hundred of — of は不要。hundreds of との混同形。\n"
     "4. hundreds of — hundreds of は「何百もの」(数詞なし) の言い方。three とは併用できない。"),

    (9, 3,
     "She is very (          ) to cold, so she always wears thick socks in winter.",
     ["sensible", "sensitive", "sense", "sensibly"], 2, 2, "KEIYO-KONDO",
     "## 🎯 コアイメージ\n"
     "形が似て意味が違う形容詞ペア: **sensitive (敏感な) / sensible (分別のある)**。"
     "be sensitive to 〜 =「〜に敏感だ」で前置詞 to とペア。\n\n"
     "## 🔬 文構造分析\n"
     "She is very **sensitive to cold**, so she always wears thick socks.\n"
     "寒さ (cold) に敏感 → 厚い靴下、と因果がつながる。\n\n"
     "## 📍 正解の根拠\n"
     "to cold と組んで「寒さに**敏感**」→ **sensitive**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. sensible —「分別のある」。sensible to cold という言い方は無く、意味も通らない。\n"
     "3. sense — 名詞。very の後ろ・be 動詞の補語の形容詞の位置に置けない。\n"
     "4. sensibly — 副詞。be 動詞の補語になれない。"),

    (10, 3,
     "I have never seen (          ) as this one.",
     ["a so beautiful picture", "so a beautiful picture", "so beautiful a picture",
      "beautiful so a picture"], 3, 2, "KEIYO-GOJUN",
     "## 🎯 コアイメージ\n"
     "**so + 形容詞 + a + 名詞**の語順 (so beautiful a picture)。such なら "
     "such a beautiful picture — so と such で a の位置が入れ替わる。\n\n"
     "## 🔬 文構造分析\n"
     "I have never seen **so beautiful a picture** as this one.\n"
     "so (副詞) が形容詞 beautiful を先に引き出し、a picture が後ろに続く。"
     "as this one が比較の相手。\n\n"
     "## 📍 正解の根拠\n"
     "so を使うときの語順は **so + 形 + a + 名詞** → so beautiful a picture。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. a so beautiful picture — a が先に来る語順は such 用 (such a beautiful picture)。so では不可。\n"
     "2. so a beautiful picture — so の直後に a は置けない。\n"
     "4. beautiful so a picture — この語順は存在しない。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
