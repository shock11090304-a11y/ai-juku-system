# -*- coding: utf-8 -*-
"""英語長文 ルール発見トレーニング No.04「読解の運用編」の単一ソース。

No.01(流れ6)・No.02(構造6)・No.03(識別6)の続編にして完結編。読解の「運用(運転技術)」6ターゲット:
 ①語彙・多義語の推測 ②指示語の特定 ③言い換え ④抽象と具体 ⑤筆者の主張・評価 ⑥論理の予測(マーカー運用)
No.01〜04=英文読解の24ルールで完全網羅(巻頭に「全24ルール地図」4列)。各長文に「設問の解き方」を付す。

ANNOT が解答キーの single source。check.py が本文との突合＋機械判定できる指標(指示語 this/these/such/those、
主張 should/must、論理マーカー)の位置網羅を検査。語彙推測・言い換え・抽象具体は意味判断のため転記＋敵対検証。
ルール整理は関正生『The Rules』のアプローチに着想を得た当塾オリジナル(文言・番号は独自)。
"""

META = {
    "series": "英語長文 ルール発見トレーニング",
    "no": "No.04",
    "edition": "読解の運用編",
    "subtitle": "The Rules式・別冊ドリル ｜ 文脈で意味を絞り、設問を解く練習",
    "level": "共通テスト〜MARCH・関関同立／難関大の仕上げ",
    "time": "1周目: 時間無制限 ／ 2周目: 各13分",
    "note": "関正生『The Rules』のアプローチに着想を得たトリリオンAI塾オリジナルの整理です。ルール番号・文言は独自。",
}

# ------------------------------------------------------------------
# 6ターゲット —— 全24ルール中の⑲〜㉔
# ------------------------------------------------------------------
TARGETS = [
    {"key": "vcb", "no": "①", "gno": "⑲", "name": "語彙・多義語の推測", "color": "#b45309", "cls": "vcb",
     "what": "知らない語・多義語の意味を、文脈のヒントから絞る",
     "sign": "言い換え(= / be / or / コロン・ダッシュ) ／ 対比(but / not の反対) ／ 具体例 ／ 語の成り立ち(接頭辞・語根)",
     "mark": "その語に〇、根拠になる語句に下線＋「言／対／例／源」",
     "slogan": "知らない語で止まるな —— 周りに必ず「意味のヒント」が置いてある。",
     "series": "運用No.1 ｜ 未知語設問の核"},
    {"key": "ref", "no": "②", "gno": "⑳", "name": "指示語の特定", "color": "#1d4ed8", "cls": "ref",
     "what": "this / these / such / that / it が「何を指すか」を確定する",
     "sign": "指示語は原則「前」を指す(直前の名詞・句・文・段落)。this+名詞は要約、such は「そのような」",
     "mark": "指示語に〇、指す先へ矢印を引く",
     "slogan": "指示語を見たら即「前に戻る」—— 指す中身を1語〜1文で言えるまで探せ。",
     "series": "運用No.2 ｜ 指示語問題の直球"},
    {"key": "par", "no": "③", "gno": "㉑", "name": "言い換え(同義の対応)", "color": "#0f766e", "cls": "par",
     "what": "同じ内容を別の言葉で言い換えた箇所。設問・選択肢は本文の言い換え",
     "sign": "in other words / that is / つまり / be動詞 / コロン ／ 上位語↔下位語 ／ 抽象↔具体 の対応",
     "mark": "言い換えのペアを線で結び、間に「＝」",
     "slogan": "設問は本文の言い換え —— 「同じ内容・違う言葉」を線で結べ。",
     "series": "運用No.3 ｜ 内容一致・空所の要"},
    {"key": "abc", "no": "④", "gno": "㉒", "name": "抽象と具体", "color": "#7c3aed", "cls": "abc",
     "what": "抽象語(problem / idea / way / factor / this trend など)の「中身」は後ろに来る",
     "sign": "抽象名詞・まとめ語の直後や次文に、For example / コロン等で具体が続く。抽象→具体の橋渡し",
     "mark": "抽象語に〇、その具体的中身に下線＋「具体」",
     "slogan": "抽象語を見たら「中身は?」—— 具体は後ろに置かれる。",
     "series": "運用No.4 ｜ 段落の骨組み"},
    {"key": "clm", "no": "⑤", "gno": "㉓", "name": "筆者の主張・評価", "color": "#dc2626", "cls": "clm",
     "what": "筆者の立場を示すシグナル。設問「筆者の考え」はここに直結",
     "sign": "should / must / need to(提案) ／ important / crucial(価値づけ) ／ fortunately / worse / smartest(評価語) ／ 逆接の直後",
     "mark": "主張・評価の語に◎をつける",
     "slogan": "should と評価語は筆者の顔 —— 主張はマーカーや逆接の後ろに出る。",
     "series": "運用No.5 ｜ 主旨・筆者の考え"},
    {"key": "mkr", "no": "⑥", "gno": "㉔", "name": "論理の予測(マーカー運用)", "color": "#1e3a8a", "cls": "mkr",
     "what": "マーカーから「次に何が来るか」を予測して読む",
     "sign": "However / Yet → 主張 ／ For example → 具体 ／ Therefore / So → 結論 ／ On the other hand → 対比 ／ In other words → 言い換え",
     "mark": "マーカーに□、直後に「主張／例／結論／対比」を予測メモ",
     "slogan": "マーカーは道路標識の“次の案内”—— 見た瞬間に続きを予測しろ。",
     "series": "運用No.6 ｜ No.01①の実戦運用"},
]

# ------------------------------------------------------------------
# 全24ルール地図(巻頭・4列)
# ------------------------------------------------------------------
RULEMAP = {
    "A": {"title": "No.01 流れ・論理", "sub": "文をつなぐ目印",
          "rows": [
              ("①", "ディスコースマーカー", "□", "逆接の後ろに主張"),
              ("②", "因果構文", "→", "原因→結果の向き"),
              ("③", "仮定法", "波線", "would=妄想"),
              ("④", "受動態", "〔〕", "する側を隠す"),
              ("⑤", "分詞構文", "〈〉", "接続詞+SVの圧縮"),
              ("⑥", "助動詞 will", "◎", "100%の法則"),
          ]},
    "B": {"title": "No.02 1文の構造", "sub": "正確に和訳",
          "rows": [
              ("⑦", "比較", "二重線", "何と何・どっち上"),
              ("⑧", "強調構文", "《》", "It…that を外す"),
              ("⑨", "倒置", "⤸", "?無い疑問文の形"),
              ("⑩", "関係詞", "/〇", "先行詞+カタマリ"),
              ("⑪", "無生物主語", "▭", "→because/by"),
              ("⑫", "同格・挿入", "()＝", "コロン・ダッシュ"),
          ]},
    "C": {"title": "No.03 識別・省略", "sub": "迷う形を見分け",
          "rows": [
              ("⑬", "that の識別", "接関同指強", "後ろが完全文か"),
              ("⑭", "it の識別", "仮代強状", "指すものは有るか"),
              ("⑮", "as の識別", "様理時前比", "後ろの形で決める"),
              ("⑯", "省略", "∧", "前と同じ形を補う"),
              ("⑰", "共通関係", "[ ]△", "and は何と何"),
              ("⑱", "程度・結果構文", "□→", "so/such/too/enough"),
          ]},
    "D": {"title": "No.04 読解の運用", "sub": "文脈と設問",
          "rows": [
              ("⑲", "語彙推測", "〇＋根拠", "ヒントで意味を絞る"),
              ("⑳", "指示語の特定", "〇→", "前を見て指す先"),
              ("㉑", "言い換え", "＝線", "同じ内容・違う言葉"),
              ("㉒", "抽象と具体", "〇＋下線", "抽象語の中身は後ろ"),
              ("㉓", "主張・評価", "◎", "should/評価語=筆者"),
              ("㉔", "マーカー予測", "□→", "次に主張/例/結論"),
          ]},
}

# ------------------------------------------------------------------
# 長文2題(原創・運用高密度)
# ------------------------------------------------------------------
PASSAGES = [
    {"key": "p1", "label": "訓練 1", "hint": True,
     "title": "The Myth of Multitasking",
     "jtitle": "マルチタスクという神話",
     "paras": [
        [
         {"n": 1, "en": "Many people are proud of their ability to multitask — to juggle several tasks at the same moment."},
         {"n": 2, "en": "However, research on the brain tells a very different story."},
         {"n": 3, "en": "What we call multitasking is usually just rapid switching: moving our attention back and forth so fast that we barely notice the gaps."},
        ],
        [
         {"n": 4, "en": "This constant switching comes at a hidden cost."},
         {"n": 5, "en": "For example, every time we jump from a report to a text message and back, the brain needs a moment to reload the first task."},
         {"n": 6, "en": "These small delays add up, and studies show that heavy multitaskers are often slower and make more mistakes than people who focus on one thing."},
        ],
        [
         {"n": 7, "en": "Worse still, this habit can slowly weaken our very ability to concentrate."},
         {"n": 8, "en": "The problem is not the technology itself but the way we let it fragment our attention."},
        ],
        [
         {"n": 9, "en": "Therefore, if we truly want to work well, we should protect long blocks of uninterrupted time."},
         {"n": 10, "en": "Doing one thing at a time may feel slower, but it is, in fact, the faster route to doing good work."},
        ],
     ]},
    {"key": "p2", "label": "訓練 2", "hint": False,
     "title": "Why Sleep Beats Cramming",
     "jtitle": "なぜ睡眠は一夜漬けに勝るのか",
     "paras": [
        [
         {"n": 1, "en": "Before a big exam, many students stay up all night, convinced that more hours must mean more learning."},
         {"n": 2, "en": "Yet this belief overlooks what actually happens while we sleep."},
        ],
        [
         {"n": 3, "en": "During deep sleep, the brain replays and files away the day's lessons — a process that scientists call consolidation."},
         {"n": 4, "en": "In other words, sleep is not lost time but the very moment when memory takes hold."},
         {"n": 5, "en": "Students who sleep after studying remember more than those who cram straight through the night."},
        ],
        [
         {"n": 6, "en": "This advantage appears even when the total study time is exactly the same."},
         {"n": 7, "en": "For example, in one experiment, a group that slept scored far higher on a later memory test than a group that stayed awake."},
         {"n": 8, "en": "Such results point to a simple but powerful rule."},
        ],
        [
         {"n": 9, "en": "When the material really matters, sleep is not a luxury; it is part of studying itself."},
         {"n": 10, "en": "So the night before an exam, the smartest move may be to close the book and go to bed."},
        ],
     ]},
]

# ------------------------------------------------------------------
# 解答キー(単一ソース) — t は本文の正確な部分文字列。入れ子可・部分重複不可。
# ------------------------------------------------------------------
ANNOT = {
 "p1": {
  "vcb": [
    {"s": 1, "t": "multitask", "clue": "several tasks at the same moment", "kind": "言い換え(ダッシュ)",
     "guess": "複数の作業を同時にこなす", "note": "ダッシュの後ろが multitask の定義=言い換え。知らなくても意味が取れる。"},
    {"s": 1, "t": "juggle", "clue": "several tasks", "kind": "多義(曲芸→やりくり)",
     "guess": "(複数を)同時にやりくりする", "note": "本来「(ボールを)お手玉する」。目的語が tasks なので比喩=「掛け持ちでこなす」。"},
    {"s": 3, "t": "rapid switching", "clue": "moving our attention back and forth", "kind": "言い換え(コロン)",
     "guess": "注意を高速で切り替えること", "note": "コロンの後ろが switching の中身=言い換え。"},
  ],
  "ref": [
    {"s": 4, "t": "This constant switching", "refers": "文(3)の rapid switching(注意を高速で切り替えること)", "note": "this+名詞で前文を1語に要約。指す中身は文(3)。"},
    {"s": 6, "t": "These small delays", "refers": "文(5)の reload に要する一瞬の遅れ", "note": "these+名詞。直前(5)の「読み込み直しの時間」をまとめている。"},
    {"s": 7, "t": "this habit", "refers": "マルチタスク＝注意の高速切り替え(文1・3)", "note": "this habit=「この習慣」。話題の中心(マルチタスク)を指す。"},
    {"s": 8, "t": "let it fragment", "refers": "it=the technology", "note": "直前の the technology itself を受ける代名詞 it。"},
    {"s": 10, "t": "it is, in fact", "refers": "it=Doing one thing at a time(文10冒頭)", "note": "文頭の動名詞主語 Doing one thing at a time を受ける代名詞 it。"},
  ],
  "par": [
    {"s": 3, "t": "rapid switching", "equals": "multitasking", "note": "What we call multitasking is usually just … で「マルチタスク=高速の切り替え」と言い換え(㉑と語彙⑲の二刀流)。"},
    {"s": 8, "t": "the way we let it fragment our attention", "equals": "This constant switching(文4)＝The problem の正体", "note": "not A but B。問題の正体を「注意を断片化する切り替え方」と言い換えている。"},
    {"s": 10, "t": "Doing one thing at a time", "equals": "focus on one thing(文6)", "note": "文6の focus on one thing の言い換え。「一度に一つ」＝集中。"},
  ],
  "abc": [
    {"s": 4, "t": "a hidden cost", "concrete": "文(5)の「脳が最初の作業を読み込み直す時間」", "note": "抽象語 a hidden cost。中身は For example の後ろ(文5)に具体化。"},
    {"s": 8, "t": "The problem", "concrete": "the way we let it fragment our attention", "note": "抽象の The problem の中身を、同じ文の not A but B で具体化。"},
  ],
  "clm": [
    {"s": 7, "t": "Worse still", "kind": "評価(否定的)", "note": "「さらに悪いことに」。筆者のマイナス評価=立場が出る。"},
    {"s": 9, "t": "we should protect long blocks of uninterrupted time", "kind": "主張(should)", "note": "should=筆者の提案。Therefore の後ろ=結論の主張。設問「筆者の考え」の直球。"},
    {"s": 10, "t": "the faster route to doing good work", "kind": "評価(主張の要約)", "note": "in fact を伴う価値づけ。「一度に一つ」を最終的に肯定する筆者の結論。"},
  ],
  "mkr": [
    {"s": 2, "t": "However", "predict": "主張(前の常識をひっくり返す)", "note": "逆接→直後に筆者の主張。「実は違う」の合図。"},
    {"s": 5, "t": "For example", "predict": "具体例(hidden cost の中身)", "note": "具体化の合図→前の抽象(a hidden cost)の中身が来る。"},
    {"s": 9, "t": "Therefore", "predict": "結論(だから〜すべき)", "note": "結論の合図→直後に主張(should)。"},
  ],
 },
 "p2": {
  "vcb": [
    {"s": 2, "t": "overlooks", "clue": "this belief（主語）… what actually happens while we sleep", "kind": "多義(見下ろす→見落とす)",
     "guess": "見落とす・見過ごす", "note": "over+look。主語が this belief(信念は文字通り“見下ろせ”ない)なので比喩=「見落とす」。"},
    {"s": 3, "t": "consolidation", "clue": "the brain replays and files away the day's lessons", "kind": "言い換え(同格・call)",
     "guess": "(記憶の)定着・固定", "note": "a process that scientists call … で直前の内容を一語に命名。ダッシュ前が定義。"},
    {"s": 4, "t": "takes hold", "clue": "memory takes hold（主語 memory は文字通り“つかめ”ない）", "kind": "多義(つかむ→根づく)",
     "guess": "根づく・定着する", "note": "主語が memory なので比喩=「記憶が根づく」。前の consolidation の言い換え。"},
  ],
  "ref": [
    {"s": 2, "t": "this belief", "refers": "文(1)の「時間が長いほど学べる」という思い込み", "note": "this+名詞で前文を要約。指す中身は文(1)の convinced that …。"},
    {"s": 5, "t": "those who cram", "refers": "those=students(一夜漬けする学生)", "note": "those=「〜する人々」。前の Students who sleep と対比。"},
    {"s": 6, "t": "This advantage", "refers": "文(5)の「眠った学生の方が多く覚えている」利点", "note": "this+名詞。直前(5)の比較結果をまとめている。"},
    {"s": 8, "t": "Such results", "refers": "文(6)(7)の実験結果(眠った方が高得点)", "note": "such+名詞=「そのような結果」。直前の研究を受ける。"},
  ],
  "par": [
    {"s": 4, "t": "the very moment when memory takes hold", "equals": "consolidation(文3)", "note": "In other words の後ろ=文3の consolidation の言い換え(㉑とマーカー㉔の連動)。"},
    {"s": 9, "t": "part of studying itself", "equals": "『贅沢(a luxury)』の逆＝勉強に不可欠", "note": "not A but B。「睡眠=贅沢ではなく勉強の一部」と言い換え、筆者の主張に直結。"},
  ],
  "abc": [
    {"s": 6, "t": "This advantage", "concrete": "文(7)の「眠った集団が高得点を取った」実験", "note": "抽象の This advantage の中身を、For example の後ろ(文7)で具体化。"},
    {"s": 8, "t": "a simple but powerful rule", "concrete": "文(9)の「重要な内容では睡眠は勉強の一部」", "note": "抽象の a … rule の中身が次文(9)に置かれる。抽象→具体の橋渡し。"},
  ],
  "clm": [
    {"s": 9, "t": "sleep is not a luxury; it is part of studying itself", "kind": "主張(断定)", "note": "筆者の中心主張。not A but B で「睡眠は勉強の一部」と断定。"},
    {"s": 10, "t": "the smartest move may be to close the book and go to bed", "kind": "評価(最上級)", "note": "smartest=評価語。So の後ろ=結論として筆者の推奨が出る。"},
  ],
  "mkr": [
    {"s": 2, "t": "Yet", "predict": "主張(思い込みへの反論)", "note": "逆接→直後に筆者の主張。this belief を否定する。"},
    {"s": 4, "t": "In other words", "predict": "言い換え(前文の要約)", "note": "言い換えの合図→前(文3)の内容を平たく言い直す。"},
    {"s": 7, "t": "For example", "predict": "具体例(This advantage の中身)", "note": "具体化の合図→前の抽象(This advantage)の中身が来る。"},
    {"s": 10, "t": "So", "predict": "結論(だから〜)", "note": "結論の合図→直後に筆者の推奨(smartest move)。"},
  ],
 },
}

# ------------------------------------------------------------------
# 設問の解き方(各訓練) — 指示語・下線部・言い換え/主旨。機械チェック外(敵対検証で担保)
# ------------------------------------------------------------------
QSET = {
 "p1": [
   {"q": "文(7) の this habit は何を指すか。本文の語句を使って答えよ。", "tag": "指示語(⑳)",
    "ans": "マルチタスク＝注意を高速で切り替えること（文(3) rapid switching）。",
    "how": "指示語は前に戻る(⑳)。this habit の前で繰り返し話題になっているのは「切り替え(switching)」。this constant switching(文4)とも一致。"},
   {"q": "文(8) the way we let it fragment our attention とは、どういうことか。本文の言い換えを使って説明せよ。", "tag": "下線部・言い換え(㉒㉑⑳)",
    "ans": "技術そのものが悪いのではなく、私たち自身が技術に注意を断片化させてしまう（＝あちこちに切り替えて集中をバラバラにさせる）、その“やり方”に問題があるということ。",
    "how": "it=the technology(⑳)。let it fragment=「(自ら)技術に断片化させておく」で主体は we。fragment our attention は前の This constant switching(文3・4)の言い換え(㉑)。not A but B の B が答えの中心。"},
 ],
 "p2": [
   {"q": "文(6) の This advantage は何を指すか。本文の語句を使って答えよ。", "tag": "指示語(⑳)",
    "ans": "勉強のあとに眠った学生の方が、一夜漬けの学生より多く覚えているという利点（文(5)）。",
    "how": "this+名詞は前文の要約(⑳)。直前(5)の remember more than those who cram をまとめている。文(7)の実験がその具体(㉒)。"},
   {"q": "文(9) sleep is not a luxury; it is part of studying itself で、筆者が最も言いたいことは何か。", "tag": "主旨・下線部(㉓㉑)",
    "ans": "重要な内容を学ぶときは、睡眠は省いてよい贅沢ではなく、勉強の一部だ（眠ることで記憶が定着する＝consolidation）。",
    "how": "not A but B の B が主張(㉓)。it=sleep(⑳)。part of studying は文(3)(4)の consolidation / memory takes hold の言い換え(㉑)。"},
 ],
}

# チェッカー用: 機械走査で当たるが対象に数えない箇所(理由必須)。
IGNORE = [
    {"p": "p1", "s": 8, "t": "the technology itself", "why": "the+名詞+itself は指示語ではなく「技術そのもの」。文脈の主題語だが指示語ターゲット(this/these/such/those)ではない。"},
    {"p": "p2", "s": 1, "t": "must mean", "why": "この must は学生の“思い込み”の中の must(=にちがいない)。筆者の主張ではないので主張・評価⑤には数えない(むしろ Yet で否定される対象)。"},
]

# 解説編に載せる「ひっかけ」解説
TRAPS = [
    {"target": "vcb", "t": "juggle (訓練1) ／ overlooks・takes hold (訓練2)",
     "note": "知っている語の“別の意味(多義)”ほど危ない。juggle=お手玉、overlook=見下ろす、take hold=つかむ、が第一義。だが目的語・主語との相性(jobs/what happens/memory)で「やりくり・見落とす・根づく」と決まる。第一義で固まらず、周りに合わせて意味を選ぶ。"},
    {"target": "ref", "t": "this belief / This advantage / Such results (訓練2)",
     "note": "this+名詞・such+名詞は、直前の1文や段落を『名詞1つに要約』した合図。指示語問題は、その名詞の中身を前から探して1文で言えれば勝ち。"},
    {"target": "abc", "t": "a hidden cost → 文(5) ／ a simple but powerful rule → 文(9)",
     "note": "抽象語(cost/rule/idea/way)が出たら『中身は?』と身構える。答えは直後・次文、For example やコロンの後ろに具体で置かれる。抽象で分からなくても、具体まで読めば必ず分かる。"},
    {"target": "clm", "t": "we should …(訓練1) ／ not a luxury but part of studying(訓練2)",
     "note": "設問「筆者の考え」は、should/must・評価語・逆接や Therefore の直後を見れば直球で当たる。本文の“事実”ではなく、筆者の“判断語”に◎を付ける癖をつける。"},
]

# ------------------------------------------------------------------
# ミニ講義(解説編)
# ------------------------------------------------------------------
LECTURES = {
 "vcb": ("知らない語で立ち止まるのは時間の無駄。長文は親切で、難しい語には必ず近くにヒントを置く——(1)言い換え"
         "(= / be動詞 / or / コロン・ダッシュ / that is)、(2)対比(but・not の“反対”から逆算)、(3)具体例、(4)語の成り立ち"
         "(over+look=見下ろす→見落とす)。多義語はさらに注意——第一義で固めず、目的語・主語との相性で意味を選ぶ"
         "(juggle jobs=掛け持ちでこなす)。未知語の設問は、この“文脈のヒント”を指させれば解ける。"),
 "ref": ("this / these / that / such / it を見たら、反射的に「前に戻る」。指示語は原則、直前の名詞・句・文・段落を指す。"
         "とくに this+名詞・such+名詞は、前の内容を『名詞1つに要約』した合図(this belief=前の思い込み、Such results=前の実験)。"
         "指示語問題は、その中身を本文の語で1文にできれば満点。代名詞 it も、直前の名詞に矢印を引いて確定する。"),
 "par": ("英語は同じ内容を何度も『違う言葉』で言い換えながら進む。in other words / that is / be動詞 / コロン、"
         "上位語↔下位語、抽象↔具体が言い換えの合図。そして設問・選択肢は、ほぼ必ず本文の言い換えでできている——"
         "だから『本文のどこの言い換えか』を線で結べれば、内容一致も空所補充も解ける。"
         "訓練1の multitasking=rapid switching、訓練2の consolidation=memory takes hold が典型。"),
 "abc": ("problem / idea / way / factor / cost / rule のような抽象語・まとめ語が出たら、『中身は?』と身構える。"
         "英語は「抽象で宣言→具体で説明」の順が基本で、具体は直後・次文、For example やコロンの後ろに置かれる"
         "(a hidden cost→reload の時間、a simple rule→睡眠は勉強の一部)。抽象で意味が取れなくても、具体まで読めば必ず分かる。"
         "逆に、具体の連続に迷ったら、それを束ねる抽象語を探すと段落の骨組みが見える。"),
 "clm": ("設問で最も問われるのは『筆者の考え』。それは本文の“事実”ではなく、筆者の“判断語”に出る——"
         "should / must / need to(提案)、important / crucial / essential(価値づけ)、fortunately / worse / smartest(評価語)、"
         "そして逆接(However/Yet)や Therefore/So の直後。これらに◎を付けておくと、主張が一目で拾える。"
         "訓練1の we should protect …、訓練2の sleep is … part of studying が筆者の中心主張。"),
 "mkr": ("マーカーは『次の案内標識』。見た瞬間に続きを予測して読むと、速度も精度も上がる——However/Yet→主張、"
         "For example/For instance→具体、Therefore/So/Thus→結論、On the other hand/In contrast→対比、"
         "In other words/That is→言い換え。No.01①で“印を付ける”練習をした語を、ここでは“先を予測する”運用に上げる。"
         "マーカーの直後には、筆者が一番読ませたい情報(主張・結論)が来やすい。"),
}

# ------------------------------------------------------------------
# 全訳(文番号つき)
# ------------------------------------------------------------------
TRANS = {
 "p1": {
  1: "多くの人は、マルチタスク——まさに同じ瞬間にいくつもの仕事を掛け持ちでこなすこと——ができるのを誇りに思っている。",
  2: "しかし、脳に関する研究は、まったく違う話を語っている。",
  3: "私たちがマルチタスクと呼ぶものは、たいてい単なる高速の切り替えにすぎない。つまり、注意をあちこちへとあまりに速く動かすので、その切れ目にほとんど気づかないのだ。",
  4: "この絶え間ない切り替えには、隠れた代償がある。",
  5: "たとえば、報告書からメッセージへ、そしてまた戻る、そのたびに、脳は最初の作業を読み込み直すのに一瞬を要する。",
  6: "こうした小さな遅れは積み重なり、研究によれば、マルチタスクを多用する人は、一つのことに集中する人よりも、しばしば遅く、より多くのミスをする。",
  7: "さらに悪いことに、この習慣は、私たちの集中する力そのものを、少しずつ弱めかねない。",
  8: "問題は、技術そのものではなく、私たちがそれに注意を断片化させてしまう、そのやり方にある。",
  9: "だから、本当にきちんと良い仕事をしたいなら、私たちは、途切れのない長い時間のかたまりを守るべきだ。",
  10: "一度に一つのことをするのは、遅く感じるかもしれない。しかし実のところ、それこそが良い仕事をするための“より速い道”なのだ。",
 },
 "p2": {
  1: "大きな試験の前、多くの学生は一晩中起きている——時間が長いほど、学べる量も多いにちがいない、と思い込んで。",
  2: "けれども、この思い込みは、私たちが眠っている間に実際に起きていることを見落としている。",
  3: "深い眠りの間、脳はその日の学びを再生し、しまい込む——科学者が「固定化(consolidation)」と呼ぶ過程だ。",
  4: "言い換えれば、睡眠は失われた時間ではなく、記憶が根づく、まさにその瞬間なのだ。",
  5: "勉強したあとに眠る学生は、夜通し一夜漬けをする学生よりも、多くを覚えている。",
  6: "この利点は、総勉強時間がまったく同じでも現れる。",
  7: "たとえば、ある実験では、眠った集団は、起きていた集団よりも、後の記憶テストではるかに高い点を取った。",
  8: "こうした結果は、単純だが強力な一つのルールを指し示している。",
  9: "内容が本当に重要なとき、睡眠は贅沢ではない。それは勉強そのものの一部なのだ。",
  10: "だから試験前夜、最も賢い一手は、本を閉じて寝ることかもしれない。",
 },
}
