#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 時制 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/jisei1/build_jisei1.py

出力 (どちらも**コミットする**。取り込みセッションが git 経由で受け取るため):
    英文法_時制_第1集.json        … import_books.py にそのまま渡す bundle
    英文法_時制_第1集_問題.pdf    … 冊子 (find_pdf の完全一致名: {source の stem}_問題.pdf)

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同じデータから
  同時に生成する (kateiho2 と同じ作り)。
★ 正解の位置は 1:2 問 / 2:3 問 / 3:3 問 / 4:2 問 に配ってある
  (CLAUDE.md「正解番号は偏らせない」)。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ①build 後に check_pdf_canon_match.py で刷り上がりを
  逆照合 ②_grammar_build.verify() + check_grammar_books.py ③正解の一意性は敵対的に再読する。
  正解になりうる別形 (例: 大過去の代わりの過去形 gave) は**選択肢に入れない**こと。

取り込み (kamitest-import 環境のセッション or Mac):
    python3 scripts/book_exam/import_books.py scripts/book_exam/materials/jisei1 \
        --pdf-dir scripts/book_exam/materials/jisei1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_時制_第1集"
TITLE = "英文法 時制 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

# (番号, ページ, 設問文, [選択肢1..4], 正解番号(1起算), 配点, unit_tag, 解説)
QUESTIONS = [
    (1, 1,
     "I will call you as soon as I (          ) at the station.",
     ["arrive", "will arrive", "arrived", "will have arrived"], 1, 2, "JISEI-FUKUSHI",
     "## 🎯 コアイメージ\n"
     "**時・条件の副詞節の中では、未来のことでも現在形**で表す。as soon as / when / "
     "if / until などが作る「いつ・どんな条件で」の節がこの対象。\n\n"
     "## 🔬 文構造分析\n"
     "I will call you **as soon as I arrive** at the station.\n"
     "主節 I will call (未来) + as soon as の副詞節。節の中は未来の内容でも現在形 "
     "arrive。\n\n"
     "## 📍 正解の根拠\n"
     "as soon as 〜 は時の副詞節 → will を使わず現在形 **arrive**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. will arrive — 時の副詞節の中に will は置けない。\n"
     "3. arrived — 過去形。主節が will call (未来) なので時間が合わない。\n"
     "4. will have arrived — will を含む形はどれも副詞節の中には置けない。"),

    (2, 1,
     "We (          ) each other since we were children.",
     ["know", "knew", "have known", "are knowing"], 3, 2, "JISEI-KEIZOKU",
     "## 🎯 コアイメージ\n"
     "**since (〜以来) は現在完了の目印**。過去の起点から今までずっと続いている"
     "ことは、過去形でも現在形でもなく現在完了で表す。\n\n"
     "## 🔬 文構造分析\n"
     "We **have known** each other **since we were children**.\n"
     "起点 = since we were children (子供の頃)、そこから現在までの継続 = "
     "have + 過去分詞。\n\n"
     "## 📍 正解の根拠\n"
     "「子供の頃から (今も) 知り合いだ」という**過去→現在の継続** → 現在完了 "
     "**have known**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. know — 現在形は「今」だけを切り取り、since からの継続を表せない。\n"
     "2. knew — 過去形は過去で話が終わり、「今も知り合い」がこぼれ落ちる。\n"
     "4. are knowing — know は状態動詞なので進行形にしない。"),

    (3, 1,
     "I lost the watch my father (          ) me for my birthday.",
     ["gives", "had given", "has given", "will give"], 2, 2, "JISEI-DAIKAKO",
     "## 🎯 コアイメージ\n"
     "過去のある時点より**さらに前**の出来事は過去完了 (had + 過去分詞) = 大過去。"
     "「失くした」より「もらった」が前。\n\n"
     "## 🔬 文構造分析\n"
     "I **lost** the watch my father **had given** me for my birthday.\n"
     "基準 = lost (過去)。もらったのはその前 → had given。関係詞節が the watch を"
     "修飾する。\n\n"
     "## 📍 正解の根拠\n"
     "「失くした (過去)」時点より前の「もらった」→ 過去完了 **had given**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. gives — 現在形。過去の話の中で時間が浮いてしまう。\n"
     "3. has given — 現在完了は「今」とつながる形。失くした過去の話の基準に合わない。\n"
     "4. will give —「これからくれる」。もう失くしている以上あり得ない。"),

    (4, 2,
     "This bicycle (          ) to my brother.",
     ["is belonging", "belonging", "is belonged", "belongs"], 4, 2, "JISEI-JOUTAI",
     "## 🎯 コアイメージ\n"
     "belong / know / like のような**状態動詞は進行形にしない**。「〜している最中」"
     "という動作の途中経過が無いから。\n\n"
     "## 🔬 文構造分析\n"
     "This bicycle **belongs to** my brother.\n"
     "belong to 〜 =「〜のものである」。主語が三人称単数なので belongs。\n\n"
     "## 📍 正解の根拠\n"
     "所属という**状態**を表すので、単純な現在形 **belongs**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. is belonging — 状態動詞 belong は進行形にできない。\n"
     "2. belonging — -ing 単独では述語動詞にならない。\n"
     "3. is belonged — belong は自動詞なので受け身を作れない。"),

    (5, 2,
     "Mr. Sato (          ) to Osaka three days ago.",
     ["has moved", "has been moving", "moved", "will move"], 3, 2, "JISEI-KAKO",
     "## 🎯 コアイメージ\n"
     "**〜 ago (〜前に) のような「明確な過去」を指す語句は、過去形とだけ組む**。"
     "現在完了は「今」とつながる形なので、過去の一点を指す語句とは合わない。\n\n"
     "## 🔬 文構造分析\n"
     "Mr. Sato **moved** to Osaka **three days ago**.\n"
     "three days ago が過去の一点を指定 → 述語は単純過去。\n\n"
     "## 📍 正解の根拠\n"
     "ago がある以上、過去形 **moved** の一択。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. has moved — 現在完了は ago と共起できない (定番の禁止ペア)。\n"
     "2. has been moving — 同じく現在完了 (進行) なので ago と組めない。\n"
     "4. will move — 未来形。ago (過去) と矛盾する。"),

    (6, 2,
     "By next month, I (          ) here for ten years.",
     ["will have lived", "have lived", "am living", "lived"], 1, 2, "JISEI-MIRAIKANRYO",
     "## 🎯 コアイメージ\n"
     "**未来のある時点までの継続・完了は未来完了 (will have + 過去分詞)**。"
     "by 〜 (〜までには) が未来の締め切り線を引く。\n\n"
     "## 🔬 文構造分析\n"
     "**By next month**, I **will have lived** here **for ten years**.\n"
     "基準 = 来月 (未来)。その時点で「10 年住んだことになる」= will have lived。\n\n"
     "## 📍 正解の根拠\n"
     "by next month という**未来の基準点**での継続の完成 → 未来完了 "
     "**will have lived**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. have lived — 現在完了は「今まで」の話。来月という未来の基準には届かない。\n"
     "3. am living —「今住んでいる」だけで、10 年・来月という枠組みを背負えない。\n"
     "4. lived — 過去形。未来の話に置けない。"),

    (7, 3,
     "It (          ) raining since last night.",
     ["is", "was", "had been", "has been"], 4, 2, "JISEI-KANRYOSHINKO",
     "## 🎯 コアイメージ\n"
     "**動作の継続は現在完了進行形 (have been -ing)**。「昨夜からずっと降り続いて"
     "いる」= 起点 since + 今も進行中。\n\n"
     "## 🔬 文構造分析\n"
     "It **has been raining** since last night.\n"
     "since last night (起点) → 現在まで続く動作 rain → has been + -ing。\n\n"
     "## 📍 正解の根拠\n"
     "since があり、かつ「降る」という動作が今も続いている → **has been** "
     "raining。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. is — 現在進行形は「今」だけ。since last night からの継続を表せない。\n"
     "2. was — 過去進行形は過去で切れてしまい、since 〜 now がつながらない。\n"
     "3. had been — 過去完了進行は「過去のある基準時まで」の形。基準が今なので使えない。"),

    (8, 3,
     "By the time you (          ) back, I will have finished the report.",
     ["will come", "come", "came", "will have come"], 2, 2, "JISEI-FUKUSHI",
     "## 🎯 コアイメージ\n"
     "by the time 〜 (〜する時までには) も**時の副詞節**。未来の内容でも節の中は"
     "現在形 — as soon as / when と同じ規則。\n\n"
     "## 🔬 文構造分析\n"
     "**By the time you come back**, I will have finished the report.\n"
     "主節は will have finished (未来完了)。by the time の節は現在形 come で未来を"
     "表す。\n\n"
     "## 📍 正解の根拠\n"
     "by the time 〜 は時の副詞節 → will を使わず現在形 **come**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. will come — 時の副詞節の中に will は置けない。\n"
     "3. came — 過去形。主節 will have finished (未来) と時間が合わない。\n"
     "4. will have come — will を含む形は副詞節の中には置けない。"),

    (9, 3,
     "This is the most beautiful sunset I (          ).",
     ["never saw", "had ever seen", "have ever seen", "ever see"], 3, 2, "JISEI-KEIKEN",
     "## 🎯 コアイメージ\n"
     "**最上級 + I have ever seen** =「今までに見た中で一番〜」。ever (今までに) と"
     "経験の現在完了がセット。\n\n"
     "## 🔬 文構造分析\n"
     "This is the most beautiful sunset (that) I **have ever seen**.\n"
     "主節 This is (現在) + 関係詞節「今までに見た」= 現在までの経験 → 現在完了 + "
     "ever。\n\n"
     "## 📍 正解の根拠\n"
     "「今までの経験の中で一番」— 現在が基準の経験なので **have ever seen**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. never saw — never だと「見た中で一番きれいなのに一度も見ていない」と矛盾する。\n"
     "2. had ever seen — 過去完了。主節が This **is** (現在) なので基準がずれる。\n"
     "4. ever see — 現在形。「今までに」という経験の幅を表せない。"),

    (10, 3,
     "He is still on vacation. I don't know when he (          ) back.",
     ["comes", "will come", "came", "has come"], 2, 2, "JISEI-MEISHI",
     "## 🎯 コアイメージ\n"
     "when の節が**名詞節 (「いつ〜か」= know の目的語) のときは、未来のことは"
     "素直に will** で表す。「副詞節では現在形」の規則は副詞節限定。\n\n"
     "## 🔬 文構造分析\n"
     "I don't know **when he will come back**.\n"
     "when 〜 back が know の目的語 (名詞節)。「いつ戻って来るのか」という未来の"
     "内容 → will come。\n\n"
     "## 📍 正解の根拠\n"
     "この when 節は名詞節。まだ休暇中 (still on vacation) = 戻りは未来 → "
     "**will come**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. comes —「未来でも現在形」は時・条件の**副詞節**の規則。名詞節には適用しない。\n"
     "3. came — 過去形。まだ休暇中なので「いつ戻ったか」は成り立たない。\n"
     "4. has come — 現在完了「もう戻って来た」。still on vacation と矛盾する。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
