#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「英文法 前置詞 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/zenchishi1/build_zenchishi1.py

出力 (どちらも**コミットする**): 英文法_前置詞_第1集.json / 英文法_前置詞_第1集_問題.pdf
★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _grammar_build.py が同時生成 (kateiho2 型)。
★ 正解の位置は 1:2 / 2:3 / 3:3 / 4:2。設問を足したら配り直すこと。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_pdf_canon_match.py ② verify() +
  check_grammar_books.py ③ 正解の一意性の敵対的再読。正解になりうる別形
  (例: die of に対する die from) は**選択肢に入れない**。

取り込み: python3 scripts/book_exam/import_books.py scripts/book_exam/materials/zenchishi1 \
    --pdf-dir scripts/book_exam/materials/zenchishi1          # 未公開で入る
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _grammar_build as G  # noqa: E402

STEM = "英文法_前置詞_第1集"
TITLE = "英文法 前置詞 演習 第1集"
LEVEL = "標準"
TIME_LIMIT_MIN = 20

QUESTIONS = [
    (1, 1,
     "The ceremony will be held (          ) the morning of May 5.",
     ["on", "in", "at", "by"], 1, 2, "ZENCHI-TOKI",
     "## 🎯 コアイメージ\n"
     "時の前置詞は**幅**で選ぶ: at (時刻の点) < on (日・曜日) < in (月・年・季節)。"
     "morning は普通 in だが、**特定の日の朝は「日」扱いで on** になる。\n\n"
     "## 🔬 文構造分析\n"
     "The ceremony will be held **on the morning of May 5**.\n"
     "of May 5 が付いて「5 月 5 日の朝」という**特定の日付**になっている。\n\n"
     "## 📍 正解の根拠\n"
     "特定日の朝 (the morning of May 5) → 日付扱いで **on**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. in — in the morning は「(一般に) 朝に」。of May 5 で特定された日には使わない。\n"
     "3. at — 時刻の一点 (at seven) に使う。朝という幅には合わない。\n"
     "4. by —「〜までに」(期限)。日時の指定にならない。"),

    (2, 1,
     "Please hand in your report (          ) next Friday.",
     ["until", "till", "by", "during"], 3, 2, "ZENCHI-KIGEN",
     "## 🎯 コアイメージ\n"
     "**by =「〜までに」(期限・一回の動作) / until =「〜までずっと」(継続)**。"
     "動詞が一回きりの動作か、続く状態かで選ぶ。\n\n"
     "## 🔬 文構造分析\n"
     "Please hand in your report **by next Friday**.\n"
     "hand in (提出する) は一回きりの動作 → 締め切りの by。\n\n"
     "## 📍 正解の根拠\n"
     "提出という 1 回の動作の**期限** → **by**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. until —「金曜までずっと提出し続ける」となり、一回の動作と合わない。\n"
     "2. till — until と同じ継続の意味。同じ理由で置けない。\n"
     "4. during —「〜の間じゅう」。後ろには期間の名詞 (the meeting など) が来る。"),

    (3, 1,
     "The thief entered the house (          ) the window.",
     ["from", "in", "at", "through"], 4, 2, "ZENCHI-KEIRO",
     "## 🎯 コアイメージ\n"
     "**through =「〜を通り抜けて」**という経路の前置詞。トンネル・窓・森など、"
     "くぐり抜ける通り道を指す。\n\n"
     "## 🔬 文構造分析\n"
     "The thief entered the house **through the window**.\n"
     "enter の経路 (どこを通って入ったか) を through が示す。\n\n"
     "## 📍 正解の根拠\n"
     "窓という通り道を**くぐり抜けて**入った → **through**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. from — 起点「〜から」。窓は出発地ではなく通り道なので合わない。\n"
     "2. in — 場所の中「〜の中で」。経路を表せない。\n"
     "3. at — 地点「〜のところで」。同じく通り抜けの意味が出ない。"),

    (4, 2,
     "Kyoto is famous (          ) its old temples and shrines.",
     ["with", "for", "to", "of"], 2, 2, "ZENCHI-JUKUGO",
     "## 🎯 コアイメージ\n"
     "**be famous for 〜 =「〜で有名」**。有名である**理由・売り物**を for が指す "
     "(for = 理由の用法)。\n\n"
     "## 🔬 文構造分析\n"
     "Kyoto is famous **for its old temples** and shrines.\n"
     "有名さの理由 = 古い寺社。famous for がひとつのかたまり。\n\n"
     "## 📍 正解の根拠\n"
     "有名の理由を示す固定ペア → be famous **for**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. with — famous with という慣用は無い (be filled with などと混同しない)。\n"
     "3. to — famous to では「有名さの向かう相手」になり、理由を示せない。\n"
     "4. of — famous of という形は無い (proud of と混同しやすい)。"),

    (5, 2,
     "Her opinion is quite different (          ) mine.",
     ["with", "in", "from", "of"], 3, 2, "ZENCHI-DIFFER",
     "## 🎯 コアイメージ\n"
     "**be different from 〜 =「〜と違う」**。from は分離「〜から離れて」— "
     "違い = 離れているイメージ。differ from も同じ from。\n\n"
     "## 🔬 文構造分析\n"
     "Her opinion is quite different **from mine** (= my opinion).\n"
     "比べる相手 (私の意見) を from が指す。\n\n"
     "## 📍 正解の根拠\n"
     "different とペアを組む前置詞は **from**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. with — different with という慣用は無い。\n"
     "2. in — different in は「〜の点で違う」(different in size)。比べる相手は指せない。\n"
     "4. of — different of という形は無い。"),

    (6, 2,
     "He fell asleep (          ) the meeting yesterday afternoon.",
     ["during", "while", "for", "between"], 1, 2, "ZENCHI-KIKAN",
     "## 🎯 コアイメージ\n"
     "**during + 名詞 =「〜の間に」/ while + S + V**。同じ意味でも、後ろに来る"
     "形で前置詞 during と接続詞 while を使い分ける。\n\n"
     "## 🔬 文構造分析\n"
     "He fell asleep **during the meeting** yesterday afternoon.\n"
     "空所の直後が the meeting という**名詞** → 前置詞 during。\n\n"
     "## 📍 正解の根拠\n"
     "名詞 (the meeting) を従えて「〜の間に」→ **during**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "2. while — 接続詞。後ろには節 (while he was in the meeting) が要る。\n"
     "3. for — 期間の長さ (for two hours) に使う。出来事の名詞には during。\n"
     "4. between —「2 つの間」。会議 1 つの間には使えない。"),

    (7, 3,
     "Ken was absent (          ) school because he had a cold.",
     ["in", "from", "at", "of"], 2, 2, "ZENCHI-ABSENT",
     "## 🎯 コアイメージ\n"
     "**be absent from 〜 =「〜を欠席する」**。from の分離「〜から離れて」が"
     "そのまま「その場にいない」を作る。\n\n"
     "## 🔬 文構造分析\n"
     "Ken was absent **from school** because he had a cold.\n"
     "欠席した場所 (学校) を from が指す。\n\n"
     "## 📍 正解の根拠\n"
     "absent とペアを組む前置詞は **from**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. in — absent in という慣用は無い (present in と混同しない)。\n"
     "3. at — 「学校に居る」なら at school。欠席の「離れて」は表せない。\n"
     "4. of — absent of という形は無い。"),

    (8, 3,
     "His grandfather died (          ) cancer two years ago.",
     ["for", "by", "at", "of"], 4, 2, "ZENCHI-GENIN",
     "## 🎯 コアイメージ\n"
     "**die of + 病気 =「〜で死ぬ」**。of は原因・出どころを指す用法。病名・飢え"
     "など直接の原因は of で受けるのが基本形。\n\n"
     "## 🔬 文構造分析\n"
     "His grandfather died **of cancer** two years ago.\n"
     "死因 (がん) を of が指す。die of がひとつのかたまり。\n\n"
     "## 📍 正解の根拠\n"
     "病気が原因の「〜で亡くなる」→ die **of**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. for — die for は「〜のために (大義に) 命を捧げる」。病名とは組まない。\n"
     "2. by — 受動態の動作主に使う by。die は受動でないので病名を by では受けない。\n"
     "3. at — 地点・時点の at。原因を表す用法が無い。"),

    (9, 3,
     "They are very proud (          ) their son's success.",
     ["with", "of", "for", "in"], 2, 2, "ZENCHI-PROUD",
     "## 🎯 コアイメージ\n"
     "**be proud of 〜 =「〜を誇りに思う」**。of は「〜について」の対象を指す。"
     "動詞形なら pride oneself on / take pride in と前置詞が変わるので区別する。\n\n"
     "## 🔬 文構造分析\n"
     "They are very proud **of their son's success**.\n"
     "誇りの対象 (息子の成功) を of が指す。\n\n"
     "## 📍 正解の根拠\n"
     "proud とペアを組む前置詞は **of**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. with — proud with という慣用は無い (pleased with と混同しない)。\n"
     "3. for — proud for という形は標準では無い。\n"
     "4. in — take pride **in** の in。形容詞 proud には付かない。"),

    (10, 3,
     "He is taller than his father (          ) five centimeters.",
     ["with", "in", "by", "at"], 3, 2, "ZENCHI-SA",
     "## 🎯 コアイメージ\n"
     "**差・程度の by =「〜の差で」**。比較・増減・勝ち負けの「どれだけ」を by が"
     "背負う (win by two points / older by three years)。\n\n"
     "## 🔬 文構造分析\n"
     "He is taller than his father **by five centimeters**.\n"
     "taller than 〜 (比較) にその**差** (5cm) を by で添える。\n\n"
     "## 📍 正解の根拠\n"
     "「5 センチ**の差で**高い」→ 差の **by**。\n\n"
     "## ❌ 誤答 NG 理由\n"
     "1. with — 道具・同伴の with。差の意味は無い。\n"
     "2. in —「〜の点で」(in height なら可)。数値の差は受けない。\n"
     "4. at — 地点・時点の at。差を表す用法が無い。"),
]

if __name__ == "__main__":
    sys.exit(G.run(HERE, STEM, TITLE, LEVEL, TIME_LIMIT_MIN, QUESTIONS))
