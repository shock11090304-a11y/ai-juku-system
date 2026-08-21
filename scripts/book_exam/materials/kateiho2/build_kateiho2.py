#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 仮定法 演習 第2集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/kateiho2/build_kateiho2.py

出力 (どちらも**コミットする**。取り込みセッションが git 経由で受け取るため):
    英文法_仮定法_第2集.json        … import_books.py にそのまま渡す bundle
    英文法_仮定法_第2集_問題.pdf    … 冊子 (find_pdf の完全一致名: {source の stem}_問題.pdf)

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF を同じデータから同時に生成するので、
  「画面の第3問と冊子の第3問が違う」というずれは構造的に起きない
  (supabase/demo/build_sample_pdf.py の教訓を一段進めた形)。
★ 正解の位置は 1:2 問 / 2:3 問 / 3:3 問 / 4:2 問 に配ってある
  (CLAUDE.md「正解番号は偏らせない」)。設問を足したら配り直すこと。
★ 解説は英語教材の 4 セクション形式 (コアイメージ → 文構造分析 → 根拠 → 誤答 NG 理由)。

取り込み (kamitest-import 環境のセッション or Mac):
    python3 scripts/book_exam/import_books.py scripts/book_exam/materials/kateiho2 \
        --pdf-dir scripts/book_exam/materials/kateiho2          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEM = "英文法_仮定法_第2集"
OUT_JSON = os.path.join(HERE, f"{STEM}.json")
OUT_PDF = os.path.join(HERE, f"{STEM}_問題.pdf")

TITLE = "英文法 仮定法 演習 第2集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

# (番号, ページ, 設問文, [選択肢1..4], 正解番号(1起算), 配点, unit_tag, 解説)
QUESTIONS = [
    (1, 1,
     "If I (          ) more time, I could travel around the world.",
     ["have", "will have", "had", "have had"], 3, 2, "KATEI-KAKO",
     "## 🎯 コアイメージ\n"
     "仮定法過去は「今の現実とは違う世界」を語る形。**現在の話なのに過去形**を使うことで、"
     "現実から一歩引いた「もしも」の距離感を出す。\n\n"
     "## 🔬 文構造分析\n"
     "If I **had** more time, I **could travel** around the world.\n"
     "if 節 = 過去形 (had) / 帰結節 = 助動詞の過去形 + 動詞の原形 (could travel)。"
     "この「過去形 + could/would + 原形」のペアが仮定法過去の型。\n\n"
     "## 📍 正解の根拠\n"
     "帰結節に could travel (助動詞の過去形) がある以上、if 節は仮定法過去の **had**。"
     "「実際には時間がない」という現在の事実の裏返しを表す。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. have — 直説法の現在形。帰結節の could と型が合わない。\n"
     "2. will have — if 節の中に will は置けない (条件節では未来も現在形で表す)。\n"
     "4. have had — 現在完了。仮定法の型ではない。"),

    (2, 1,
     "If she had taken my advice, she (          ) in trouble now.",
     ["wouldn't be", "wouldn't have been", "isn't", "won't be"], 1, 2, "KATEI-KONGO",
     "## 🎯 コアイメージ\n"
     "混合仮定法 =「**過去にこうしていれば、今こうなのに**」。if 節と帰結節で時間が違う"
     "ときは、それぞれの時間に合わせて形を選ぶ。\n\n"
     "## 🔬 文構造分析\n"
     "If she **had taken** my advice (過去完了 = 過去の仮定), she **wouldn't be** in trouble "
     "**now** (would + 原形 = 現在の帰結)。\n\n"
     "## 📍 正解の根拠\n"
     "文末の **now** が決め手。帰結は「今」の話なので仮定法過去の形 **wouldn't be**。"
     "if 節が過去完了だからといって機械的に would have p.p. にしない。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. wouldn't have been —「過去にそうならなかっただろう」。now と矛盾する。\n"
     "3. isn't — 直説法。仮定の帰結にならない。\n"
     "4. won't be — 単純未来。仮定法の型ではない。"),

    (3, 1,
     "I wish I (          ) harder when I was a student.",
     ["studied", "study", "would study", "had studied"], 4, 2, "KATEI-GANBO",
     "## 🎯 コアイメージ\n"
     "I wish は「現実はそうでない」と分かっていて言う願望。**いつの話を悔やむか**で"
     "形が変わる: 今のこと → 過去形 / 過去のこと → 過去完了。\n\n"
     "## 🔬 文構造分析\n"
     "I wish I **had studied** harder **when I was a student**.\n"
     "wish の後ろが「学生だった当時」= 過去の内容なので、時間を 1 つ深くして過去完了。\n\n"
     "## 📍 正解の根拠\n"
     "**when I was a student** が過去を指す以上、過去への後悔 = **had studied**。"
     "「あのとき勉強しておけばよかった」。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. studied —「今もっと勉強していればなあ」という現在の願望になり、when 節と時間が合わない。\n"
     "2. study — 直説法の現在形。wish の後ろには使えない。\n"
     "3. would study — would は「これから〜してくれたらいいのに」という未来方向の願望。過去の後悔には使えない。"),

    (4, 2,
     "He talks as if he (          ) everything about the plan.",
     ["knows", "knew", "has known", "will know"], 2, 2, "KATEI-ASIF",
     "## 🎯 コアイメージ\n"
     "as if は「まるで〜であるかのように」。**実際はそうではない**というニュアンスを"
     "出すときは仮定法 (過去形) を使う。\n\n"
     "## 🔬 文構造分析\n"
     "He talks **as if** he **knew** everything about the plan.\n"
     "主節 talks は現在。as if 節の内容も「話すのと同じ時」なので、時制を 1 つ下げた過去形。\n\n"
     "## 📍 正解の根拠\n"
     "「実際には全部を知っているわけではない」のに知っているかのように話す — この"
     "現実との距離を表すのが仮定法過去 **knew**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. knows — 直説法。「本当に知っている」ことになり as if の含みが消える。\n"
     "3. has known — 現在完了。as if の仮定法の型ではない。\n"
     "4. will know — 未来形。時間の関係が成り立たない。"),

    (5, 2,
     "(          ) your help, we couldn't have finished the project on time.",
     ["Without", "With", "Unless", "For"], 1, 2, "KATEI-SHORYAKU",
     "## 🎯 コアイメージ\n"
     "if 節の代わりに**前置詞句**で仮定を背負わせる形。Without 〜 =「〜がなかったら」は"
     "if it had not been for 〜 の圧縮形。\n\n"
     "## 🔬 文構造分析\n"
     "**Without** your help(= If it had not been for your help), we **couldn't have finished** "
     "the project on time.\n"
     "帰結節が couldn't have p.p. なので、過去の事実に反する仮定 (仮定法過去完了) と分かる。\n\n"
     "## 📍 正解の根拠\n"
     "「実際には助けてもらえたから間に合った」の裏返し。「〜がなかったら」= **Without**。"
     "But for your help も同じ意味。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. With —「助けがあったら間に合わなかった」となり意味が逆。\n"
     "3. Unless — 接続詞なので後ろに節 (主語+動詞) が要る。名詞句は置けない。\n"
     "4. For — 「〜のために」。仮定の意味は出ない。"),

    (6, 2,
     "(          ) I known her phone number, I would have called her.",
     ["If", "Should", "Had", "Were"], 3, 2, "KATEI-TOCHI",
     "## 🎯 コアイメージ\n"
     "仮定法の if は**省略できる**。省略すると、残った助動詞・be・had が主語の前に出る"
     "(疑問文と同じ倒置の形)。\n\n"
     "## 🔬 文構造分析\n"
     "**Had I known** her phone number(= If I had known 〜), I would have called her.\n"
     "空所の直後が「主語 + 過去分詞 (I known)」— この並びを作れるのは had の倒置だけ。\n\n"
     "## 📍 正解の根拠\n"
     "帰結節 would have called (仮定法過去完了) と対になる if 節は had + p.p.。"
     "if が無い以上、**Had** を文頭に出した倒置形が正解。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. If — If I known は動詞の形が壊れている (known だけでは述語にならない)。\n"
     "2. Should — Should I know なら形になるが、known (過去分詞) とはつながらない。\n"
     "4. Were — Were I known だと受け身になり「私が知られていたら」と意味不明になる。"),

    (7, 3,
     "If the sun (          ) to rise in the west, I would not change my mind.",
     ["is", "were", "will be", "had been"], 2, 2, "KATEI-MIRAI",
     "## 🎯 コアイメージ\n"
     "were to は「万が一〜するようなことがあっても」— **起こりそうにない未来**を仮定する"
     "格式ばった形。太陽が西から昇る = 絶対に起きないことの定番例。\n\n"
     "## 🔬 文構造分析\n"
     "If the sun **were to rise** in the west, I **would not change** my mind.\n"
     "if 節 = were to + 原形 / 帰結節 = would + 原形。主語が三人称単数でも **were**。\n\n"
     "## 📍 正解の根拠\n"
     "「たとえ絶対に起きないことが起きても」という未来のあり得ない仮定は **were to** で"
     "表す。仮定法では be 動詞は人称に関係なく were が基本形。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. is — 直説法。「実際に西から昇る」前提になってしまう。\n"
     "3. will be — if 節の中に will は置けない。\n"
     "4. had been — 過去完了 + to 不定詞はこの構文の形ではない。"),

    (8, 3,
     "It's high time you (          ) to bed.",
     ["go", "will go", "have gone", "went"], 4, 2, "KATEI-KANYO",
     "## 🎯 コアイメージ\n"
     "It is (high) time + 主語 + **過去形** =「もう〜してもいい時間だ (のにまだしていない)」。"
     "「まだ寝ていない」という現実とのずれを過去形が背負う。\n\n"
     "## 🔬 文構造分析\n"
     "It's high time you **went** to bed.\n"
     "time の後ろは節。内容は「これから寝る」ことなのに、形は仮定法過去の **went**。\n\n"
     "## 📍 正解の根拠\n"
     "It is time 構文の後ろは仮定法過去、が固定ルール。high は「とっくに」の強調。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. go — 原形・現在形はこの構文では使えない (to 不定詞 It's time to go なら可)。\n"
     "2. will go — 未来形は置けない。\n"
     "3. have gone — 現在完了は「もう寝てしまった」ことになり構文の意味と衝突する。"),

    (9, 3,
     "(          ) anything happen to me, please give this letter to my family.",
     ["If", "Would", "Should", "Had"], 3, 2, "KATEI-TOCHI",
     "## 🎯 コアイメージ\n"
     "should の倒置 =「**万一**〜したら」。if を省略して Should を文頭に出す。"
     "帰結節には命令文や will も置ける (現実に起こる可能性を少し残した仮定)。\n\n"
     "## 🔬 文構造分析\n"
     "**Should** anything **happen** to me(= If anything should happen 〜), please give 〜.\n"
     "空所の直後が「主語 + 動詞の原形 (anything happen)」— この並びを作れるのは "
     "should の倒置だけ。\n\n"
     "## 📍 正解の根拠\n"
     "「万一のことがあれば」= if 〜 should の倒置形 **Should**。帰結が please の命令文"
     "なのも should 仮定の典型。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. If — If anything happen は三単現の s が無く形が壊れている (happens なら直説法)。\n"
     "2. Would — would の倒置はこの意味では使わない。\n"
     "4. Had — Had なら後ろは過去分詞のはずで、happen (原形) とつながらない。"),

    (10, 3,
     "If only I (          ) him the truth then!",
     ["told", "had told", "could tell", "can tell"], 2, 2, "KATEI-GANBO",
     "## 🎯 コアイメージ\n"
     "If only 〜! =「〜でありさえすればなあ」。I wish よりも強い嘆き。時間の使い分けは "
     "wish と同じ: 過去のことを悔やむなら過去完了。\n\n"
     "## 🔬 文構造分析\n"
     "If only I **had told** him the truth **then**!\n"
     "then (あのとき) が過去を指すので、過去への後悔 = 過去完了。\n\n"
     "## 📍 正解の根拠\n"
     "「あのとき本当のことを言っておけば」— **then** がある以上 **had told** の一択。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. told —「今言えたらなあ」という現在の願望になり、then と時間が合わない。\n"
     "3. could tell — これも現在方向 (「今言えたらなあ」)。then と合わない。\n"
     "4. can tell — 直説法。If only の願望の型ではない。"),
]

# 正解位置の配り (1:2 / 2:3 / 3:3 / 4:2) を機械で確かめる — 偏ると勘で当たる
_dist = {}
for _q in QUESTIONS:
    _dist[_q[4]] = _dist.get(_q[4], 0) + 1
assert all(2 <= _dist.get(k, 0) <= 3 for k in (1, 2, 3, 4)), f"正解位置が偏っている: {_dist}"


# ★ 組版・検証・出力は隣の _grammar_build.py が引き受ける (英文法 15 冊の共通型)。
#   この冊子はシリーズの 1 冊目で、共通化の**前**に書かれていたため、
#   render_question / build_html / build_json / find_chrome / main を自前で持ち、
#   しかも verify() を通していなかった。共通ビルダーに寄せて、
#   ・日本語フォントの指定 (中国語フォントに落ちない)
#   ・verify() の全項目 (解説 4 セクション・誤答 NG 理由の照合・正解位置)
#   を他の 14 冊と同じにする。
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
