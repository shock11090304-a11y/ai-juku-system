# -*- coding: utf-8 -*-
"""英語長文 ルール発見トレーニング No.03「識別・省略編」の単一ソース。

No.01(流れ6)・No.02(構造6)の続編。「同じ形の見分け(識別)＋見えないものを補う」応用6ターゲット:
 ①thatの識別 ②itの識別 ③asの識別 ④省略 ⑤共通関係(並列) ⑥程度・結果構文
No.01+No.02+No.03=英文読解の18ルールで完全網羅(巻頭に「全18ルール地図」)。

ANNOT が解答キーの single source。check.py が本文との突合＋識別語(that/it/as/so/such/too/enough)の
**位置ごとの網羅**を機械検査する。t は本文中の**正確な**部分文字列(同一文内で一意・部分重複は不可)。
ルール整理は関正生『The Rules』のアプローチに着想を得た当塾オリジナル(文言・番号は独自)。
"""

META = {
    "series": "英語長文 ルール発見トレーニング",
    "no": "No.03",
    "edition": "識別・省略編",
    "subtitle": "The Rules式・別冊ドリル ｜ 迷う形を見分け、省略を補う練習",
    "level": "共通テスト〜MARCH・関関同立／難関大の応用",
    "time": "1周目: 時間無制限 ／ 2周目: 各12分",
    "note": "関正生『The Rules』のアプローチに着想を得たトリリオンAI塾オリジナルの整理です。ルール番号・文言は独自。",
}

# ------------------------------------------------------------------
# 6ターゲット(探すもの・目印・付ける印・合言葉) —— 全18ルール中の⑬〜⑱
# ------------------------------------------------------------------
TARGETS = [
    {"key": "tid", "no": "①", "gno": "⑬", "name": "that の識別", "color": "#4338ca", "cls": "tid",
     "what": "同じ that が5つの顔を持つ。どれかを即断する",
     "sign": "接続詞(後ろが完全文) ／ 関係代名詞(後ろが不完全) ／ 同格(名詞の中身) ／ 指示 that・those ／ 強調構文 It is A that",
     "mark": "that に〇をつけ、上に「接/関/同/指/強」と役割を書く",
     "slogan": "that は後ろを見よ —— 完全文なら接続詞・同格、欠けたら関係代名詞。",
     "series": "識別No.1 ｜ 下線和訳・空所補充の要"},
    {"key": "iid", "no": "②", "gno": "⑭", "name": "it の識別", "color": "#0e7490", "cls": "iid",
     "what": "その it は何者か。指すものが有るか無いかを見抜く",
     "sign": "仮主語(It is … to/that) ／ 仮目的語(make it … to) ／ 代名詞(前に指すもの) ／ 強調構文 It is A that ／ 状況・天候の it",
     "mark": "it に〇をつけ、上に「仮主/仮目/代/強/状」と役割を書く",
     "slogan": "it を見たら「指すものは?」——無ければ仮主語・仮目的語・強調・状況。",
     "series": "識別No.2 ｜ 訳のねじれ防止"},
    {"key": "aid", "no": "③", "gno": "⑮", "name": "as の識別", "color": "#a21caf", "cls": "aid",
     "what": "多義の as。後ろの形と意味で役割を決める",
     "sign": "様態(〜のように) ／ 理由(〜なので) ／ 時・比例(〜するにつれて) ／ 前置詞「〜として」(後ろが名詞) ／ as … as(比較)",
     "mark": "as に〇をつけ、上に「様/理/時/前/比」と役割を書く",
     "slogan": "as は後ろ次第 —— 名詞なら「として」、S+V なら様態・理由・時を文脈で。",
     "series": "識別No.3 ｜ 最頻出の多義語"},
    {"key": "ell", "no": "④", "gno": "⑯", "name": "省略", "color": "#c2410c", "cls": "ell",
     "what": "消えた語を補って読む。反復・共通・接続詞の脱落",
     "sign": "反復語句の省略(gapping) ／ 接続詞 that・関係詞の省略 ／ than・as の後ろの省略(did/be=代動詞) ／ 副詞節の S+be 省略",
     "mark": "省略の位置に「∧」を書き、補う語を（　）で添える",
     "slogan": "スカスカに見えたら省略 —— 前と同じ形を探して補え。",
     "series": "見えない語を補う応用"},
    {"key": "par", "no": "⑤", "gno": "⑰", "name": "共通関係(並列)", "color": "#15803d", "cls": "par",
     "what": "and / but / or が「何と何」を結ぶか。共通部分をくくり出す",
     "sign": "等位接続 A and/but/or B ／ 相関接続 not only A but also B・both A and B・either A or B ／ A rather than B ／ not A but B",
     "mark": "並ぶ要素を[　]でくくり、接続詞に△、共通部分に波線",
     "slogan": "and を見たら「何と何?」——形が同じもの同士が並ぶ。共通項をくくり出せ。",
     "series": "長い文の骨格を保つ"},
    {"key": "deg", "no": "⑥", "gno": "⑱", "name": "程度・結果構文", "color": "#b91c1c", "cls": "deg",
     "what": "so / such / too / enough が作る「程度→結果」の型",
     "sign": "so + 形容詞/副詞 + that … ／ such + (a) 名詞 + that … ／ too + 形/副 + to … ／ … enough to …",
     "mark": "so / such / too / enough に□、結びつく that・to まで矢印を引く",
     "slogan": "so・such・too・enough を見たら that か to を探せ —— 「程度→結果」で1セット。",
     "series": "結果節の見落とし防止"},
]

# ------------------------------------------------------------------
# 全18ルール地図(巻頭) — No.01(流れ)+No.02(構造)+No.03(識別・省略)
# ------------------------------------------------------------------
RULEMAP = {
    "A": {"title": "No.01「流れ・論理」6", "sub": "文と文をつなぐ目印",
          "rows": [
              ("①", "ディスコースマーカー", "□で囲む", "逆接の後ろに主張"),
              ("②", "因果構文", "下線＋矢印", "原因 → 結果 の向き"),
              ("③", "仮定法", "波線", "would=妄想モード"),
              ("④", "受動態", "〔　〕", "「する側」を隠す"),
              ("⑤", "分詞構文", "〈　〉", "接続詞+S+V の圧縮"),
              ("⑥", "助動詞 will", "◎", "100%そうなる法則"),
          ]},
    "B": {"title": "No.02「1文の構造」6", "sub": "正確に和訳する目印",
          "rows": [
              ("⑦", "比較", "二重下線", "何と何を、どっちが上"),
              ("⑧", "強調構文", "《　》", "It…that を外して戻る"),
              ("⑨", "倒置", "⤸ ←正順", "? が無い疑問文の形"),
              ("⑩", "関係詞(切れ目)", "/ 〇", "先行詞＋カタマリ"),
              ("⑪", "無生物主語", "▭ →", "モノ主語→ because/by"),
              ("⑫", "同格・挿入", "（ ）＝", "コロン・ダッシュ・that"),
          ]},
    "C": {"title": "No.03「識別・省略」6", "sub": "迷う形を見分ける目印",
          "rows": [
              ("⑬", "that の識別", "〇＋接関同指強", "後ろが完全文か"),
              ("⑭", "it の識別", "〇＋仮代強状", "指すものは有るか"),
              ("⑮", "as の識別", "〇＋様理時前比", "後ろの形で決める"),
              ("⑯", "省略", "∧＋補い", "前と同じ形を補う"),
              ("⑰", "共通関係(並列)", "[ ] △", "and は何と何"),
              ("⑱", "程度・結果構文", "□→that/to", "so/such/too/enough"),
          ]},
}

# ------------------------------------------------------------------
# 長文2題(原創・識別高密度)
# ------------------------------------------------------------------
PASSAGES = [
    {"key": "p1", "label": "訓練 1", "hint": True,
     "title": "Why Curiosity Outlasts Talent",
     "jtitle": "なぜ好奇心は才能より長続きするのか",
     "paras": [
        [
         {"n": 1, "en": "It is clear that curiosity, not raw talent, is what carries a person the furthest."},
         {"n": 2, "en": "Talented people often give up too soon to discover what they might become, as they expect success to come easily."},
         {"n": 3, "en": "Curiosity, by contrast, is so powerful that it can turn a boring task into a puzzle, and a dull hour into a game."},
        ],
        [
         {"n": 4, "en": "As Einstein once put it, he had no special gift — only a restless and endless curiosity."},
         {"n": 5, "en": "Children ask why about everything; adults, about almost nothing."},
         {"n": 6, "en": "Curiosity makes it possible to enjoy problems that others avoid, and to learn calmly from the very failures that most people fear."},
        ],
        [
         {"n": 7, "en": "As we grow older, we build such a store of ready answers that we ask far fewer questions than we once did."},
         {"n": 8, "en": "Curiosity not only keeps the mind flexible but also reminds us that learning never truly ends."},
         {"n": 9, "en": "Those who stay curious see every new field not as a wall but as a door."},
        ],
        [
         {"n": 10, "en": "In the end, it is curiosity, not talent, that decides how far a mind will travel."},
        ],
     ]},
    {"key": "p2", "label": "訓練 2", "hint": False,
     "title": "Why Hard Books Repay the Effort",
     "jtitle": "なぜ難しい本は苦労に報いるのか",
     "paras": [
        [
         {"n": 1, "en": "It is tempting to believe that a book should be as easy as a friendly conversation, but the ones that truly change us are rarely the easy ones."},
         {"n": 2, "en": "A hard book asks us to slow down, to reread, and to stay with a difficult passage too long to feel fully at ease."},
        ],
        [
         {"n": 3, "en": "As the argument grows more complex, it quietly demands that we hold several ideas in mind at once."},
         {"n": 4, "en": "It is precisely this effort that trains the mind, just as lifting a weight, not watching someone else lift it, builds real strength."},
         {"n": 5, "en": "Easy books hand us answers; hard ones, questions."},
        ],
        [
         {"n": 6, "en": "Those who read only for comfort miss what a book can do as a form of thinking."},
         {"n": 7, "en": "Some passages are such tangled puzzles that we begin to suspect the author is testing us."},
         {"n": 8, "en": "The old idea that struggle deepens memory is supported both by careful studies and by ordinary experience."},
        ],
        [
         {"n": 9, "en": "As we fight through a difficult chapter, we understand far more than we did before."},
         {"n": 10, "en": "It takes patience, but the reward is great enough to change the way we read everything else."},
         {"n": 11, "en": "In the end, it is not the easy book but the hard one that stays with us, working on the mind long after the last page is turned."},
        ],
     ]},
]

# ------------------------------------------------------------------
# 解答キー(単一ソース) — t は本文の正確な部分文字列
# 二刀流(dual)は同一 t を両カテゴリに載せる／入れ子は許容・部分重複は不可
# ------------------------------------------------------------------
ANNOT = {
 "p1": {
  "tid": [
    {"s": 1, "t": "that curiosity", "role": "接続詞", "note": "It is clear that … の that。後ろは完全文(curiosity is what…)。仮主語 It の真主語をつくる名詞節。"},
    {"s": 6, "t": "that others avoid", "role": "関係代名詞", "note": "problems を修飾。avoid の目的語が欠ける(不完全)=関係代名詞。"},
    {"s": 6, "t": "that most people fear", "role": "関係代名詞", "note": "failures を修飾。fear の目的語が欠ける=関係代名詞。"},
    {"s": 8, "t": "that learning never truly ends", "role": "接続詞", "note": "reminds us that … の that。後ろは完全文=接続詞(名詞節)。"},
    {"s": 9, "t": "Those who stay curious", "role": "指示(those)", "note": "those=「〜する人々」。後ろの who 節とセットで「好奇心を保つ人は」。"},
    {"s": 10, "t": "that decides how far a mind will travel", "role": "強調構文", "note": "it is A that … の that。A(=curiosity)を強調。It is と that を外すと Curiosity decides … に戻る。"},
  ],
  "iid": [
    {"s": 1, "t": "It is clear", "role": "仮主語", "note": "It=後ろの that 節。「好奇心が…と、いうことは明らかだ」。指すものは前に無い。"},
    {"s": 3, "t": "it can turn", "role": "代名詞", "note": "it=Curiosity(前に指すものが有る)。"},
    {"s": 4, "t": "put it", "role": "代名詞(慣用)", "note": "as X put it =「Xが言ったように」。it は漠然と「それ・その考え」を指す代名詞。"},
    {"s": 6, "t": "makes it possible", "role": "仮目的語", "note": "make it possible to … の it。真の目的語は後ろの to 不定詞。"},
    {"s": 10, "t": "it is curiosity", "role": "強調構文", "note": "it is A that … の it。指すものは無く、A を押し出すための形式の it。"},
  ],
  "aid": [
    {"s": 2, "t": "as they expect success to come easily", "role": "理由", "note": "「彼らは成功が楽に来ると思っているので」。後ろが S+V で、文脈は原因・理由。"},
    {"s": 4, "t": "As Einstein once put it", "role": "様態", "note": "「アインシュタインが言ったように」。as+S+V で「〜のように」。"},
    {"s": 7, "t": "As we grow older", "role": "時・比例", "note": "「年をとるにつれて」。as+S+V で変化の並行(比例)。"},
    {"s": 9, "t": "as a wall", "role": "前置詞「として」", "note": "see A as B の as。後ろが名詞=前置詞「〜として」。"},
    {"s": 9, "t": "as a door", "role": "前置詞「として」", "note": "同上。not as a wall but as a door で2つの as が並ぶ。"},
  ],
  "ell": [
    {"s": 4, "t": "only a restless and endless curiosity", "supply": "(he had)", "note": "ダッシュの後ろ。前の he had no special gift と共通の he had が省略。"},
    {"s": 5, "t": "adults, about almost nothing", "supply": "(ask why)", "note": "前の Children ask why と共通の動詞句 ask why が省略(gapping)。カンマが省略の合図。"},
    {"s": 7, "t": "than we once did", "supply": "(asked)", "note": "than の後ろの省略。did は代動詞=前の ask(ed) の代用。"},
  ],
  # ★par の scope: (i)and/or/but が結ぶ句・語レベルの並列, (ii)相関接続(not only/both/not A but B),
  #   (iii)セミコロンの対句(gapping)を印す。節全体を結ぶ but(p2s1)や、強調構文の焦点に置かれた
  #   短い同格対比(p1s1/s10 の「curiosity, not talent」)は二重印を避けるため対象外(scope 決定)。
  "par": [
    {"s": 3, "t": "a boring task into a puzzle, and a dull hour into a game", "kind": "and(等位)", "joins": "退屈な作業→パズル ／ 退屈な時間→ゲーム", "note": "turn A into B が2つ並列。and の前後は同じ形。"},
    {"s": 5, "t": "Children ask why about everything; adults, about almost nothing", "kind": "対句(並列・gapping)", "joins": "子ども→何にでも「なぜ」 ／ 大人→ほとんど何にも(なぜと尋ねない)", "note": "セミコロンで2文が対に並ぶ。後半は ask why が省略(④と二刀流)。"},
    {"s": 4, "t": "a restless and endless curiosity", "kind": "and(等位)", "joins": "restless ／ endless", "note": "形容詞2つが and で並列し curiosity を修飾。"},
    {"s": 6, "t": "to enjoy problems that others avoid, and to learn calmly from the very failures", "kind": "and(等位)", "joins": "問題を楽しむ ／ 失敗から学ぶ", "note": "to 不定詞2つが並列。共通は makes it possible。"},
    {"s": 8, "t": "not only keeps the mind flexible but also reminds us", "kind": "相関(not only A but also B)", "joins": "心を柔軟に保つ ／ 学びは終わらないと気づかせる", "note": "not only A but also B。A・B は同じ動詞句の形。"},
    {"s": 9, "t": "not as a wall but as a door", "kind": "相関(not A but B)", "joins": "壁として(×) ／ 扉として(○)", "note": "not A but B。前置詞句 as … が2つ並ぶ。"},
  ],
  "deg": [
    {"s": 2, "t": "too soon to discover", "kind": "too + 副 + to(〜すぎて…できない)", "note": "「早くに立ち止まりすぎて、なれたはずの姿を発見できない」。too と to が1セット。"},
    {"s": 3, "t": "so powerful that", "kind": "so + 形 + that(とても…なので〜)", "note": "so powerful → 結果 that it can turn …。so と that を矢印で結ぶ。"},
    {"s": 7, "t": "such a store of ready answers that", "kind": "such + (a) 名 + that", "note": "such a store … → 結果 that we ask far fewer …。such は名詞のカタマリに付く。"},
  ],
 },
 "p2": {
  "tid": [
    {"s": 1, "t": "that a book should be", "role": "接続詞", "note": "believe that … の that。後ろは完全文=接続詞(名詞節)。"},
    {"s": 1, "t": "that truly change us", "role": "関係代名詞", "note": "the ones を修飾。change の主語が欠ける=主格の関係代名詞。"},
    {"s": 3, "t": "that we hold several ideas in mind at once", "role": "接続詞", "note": "demands that S (should) V の that。要求の that 節=接続詞。"},
    {"s": 4, "t": "that trains the mind", "role": "強調構文", "note": "It is A that … の that。A(=this effort)を強調。"},
    {"s": 6, "t": "Those who read only for comfort", "role": "指示(those)", "note": "those=「〜する人々」。"},
    {"s": 8, "t": "that struggle deepens memory", "role": "同格", "note": "The idea that … の that。後ろは完全文で idea の中身を説明=同格。"},
    {"s": 11, "t": "that stays with us", "role": "強調構文", "note": "it is not A but B that … の that。B(=the hard one)を強調。"},
  ],
  "iid": [
    {"s": 1, "t": "It is tempting", "role": "仮主語", "note": "It=後ろの to believe …。「〜と信じたくなる」。"},
    {"s": 3, "t": "it quietly demands", "role": "代名詞", "note": "it=a hard book(前に指すものが有る)。"},
    {"s": 4, "t": "It is precisely this effort", "role": "強調構文", "note": "It is A that … の形式の it。指すものは無い。"},
    {"s": 4, "t": "lift it", "role": "代名詞", "note": "it=a weight。watching someone else lift it の it は代名詞。"},
    {"s": 10, "t": "It takes patience", "role": "状況", "note": "It takes … =「(状況として)忍耐が要る」。特定のものを指さない状況の it。"},
    {"s": 11, "t": "it is", "role": "強調構文", "note": "it is not A but B that … の形式の it。指すものは無い。"},
  ],
  "aid": [
    {"s": 1, "t": "as easy as a friendly conversation", "role": "as … as(比較)", "note": "as+形容詞+as で「〜と同じくらい簡単」。2つの as が対。"},
    {"s": 3, "t": "As the argument grows more complex", "role": "時・比例", "note": "「議論が複雑になるにつれて」。as+S+V の比例。"},
    {"s": 4, "t": "just as", "role": "様態", "note": "just as … =「ちょうど〜のように」。後ろは lifting …(S+V相当)で様態の as。"},
    {"s": 6, "t": "as a form of thinking", "role": "前置詞「として」", "note": "what a book can do as … の as。後ろが名詞=前置詞「〜として」。"},
    {"s": 9, "t": "As we fight through a difficult chapter", "role": "時・比例", "note": "「難所を進むにつれて」。as+S+V の比例。"},
  ],
  "ell": [
    {"s": 5, "t": "hard ones, questions", "supply": "(hand us)", "note": "前の Easy books hand us answers と共通の hand us が省略(gapping)。カンマが合図。"},
    {"s": 7, "t": "suspect the author is testing us", "supply": "(that)", "note": "suspect と the author の間に接続詞 that が省略。"},
    {"s": 9, "t": "than we did before", "supply": "(understood)", "note": "than の後ろの省略。did は代動詞=前の understood の代用。"},
  ],
  "par": [
    {"s": 2, "t": "to slow down, to reread, and to stay with a difficult passage", "kind": "and(等位・3つ)", "joins": "slow down ／ reread ／ stay with a difficult passage", "note": "to 不定詞3つが and で並列。共通は asks us。"},
    {"s": 4, "t": "lifting a weight, not watching someone else lift it", "kind": "A, not B(対比の並列)", "joins": "重りを持ち上げる(○) ／ 他人が持つのを見る(×)", "note": "A, not B(肯定→否定の順)。並ぶのは同じ -ing の形。"},
    {"s": 5, "t": "Easy books hand us answers; hard ones, questions", "kind": "対句(並列)", "joins": "易しい本→答え ／ 難しい本→問い", "note": "セミコロンで2文が対に並ぶ。後半は hand us が省略。"},
    {"s": 8, "t": "both by careful studies and by ordinary experience", "kind": "相関(both A and B)", "joins": "入念な研究によって ／ 日常の経験によって", "note": "both A and B。前置詞句 by … が2つ並ぶ。"},
    {"s": 11, "t": "not the easy book but the hard one", "kind": "相関(not A but B)", "joins": "易しい本(×) ／ 難しい本(○)", "note": "not A but B。強調構文 it is … that の強調される焦点が、この対比になっている(⑭⑬と二刀流)。"},
  ],
  "deg": [
    {"s": 2, "t": "too long to feel fully at ease", "kind": "too + 副 + to", "note": "「安らげないほど長くとどまる」。too と to が1セット。"},
    {"s": 7, "t": "such tangled puzzles that", "kind": "such + 名 + that", "note": "such tangled puzzles → 結果 that we begin to suspect …。"},
    {"s": 10, "t": "great enough to change", "kind": "形 + enough + to", "note": "「変えるのに十分なほど大きい」。enough は形容詞の後ろ、to と1セット。"},
  ],
 },
}

# チェッカー用: 識別語(that/it/as/so/such/too/enough)のうち、ターゲットに数えない箇所(理由必須)。
IGNORE = [
]

# 解説編に載せる「ひっかけ」解説
TRAPS = [
    {"target": "tid", "t": "the idea that struggle deepens memory (同格) ／ problems that others avoid (関係代名詞)",
     "note": "同じ「名詞+that」でも、後ろが完全文(欠けなし)なら同格、不完全(目的語や主語が欠ける)なら関係代名詞。that の直後だけを見て判定する。"},
    {"target": "iid", "t": "It is precisely this effort that trains the mind (強調構文) ／ It is tempting to believe … (仮主語)",
     "note": "どちらも It is … だが、It is と that/to を外して元の文に戻せれば強調構文、that/to 以下が It の中身なら仮主語。指すものが前に無い点は共通。"},
    {"target": "aid", "t": "as a form of thinking (前置詞) ／ As the argument grows … (接続詞)",
     "note": "as の後ろが「名詞」なら前置詞「〜として」、「S+V」なら接続詞(様態/理由/時・比例)。まず後ろが名詞か文かを見る。"},
    {"target": "ell", "t": "than we once did (訓練1) ／ we did before (訓練2)",
     "note": "than/as の後ろの did・does・is などは、前の動詞の代わりをする代動詞。省略された動詞を前から補って意味を取る。"},
]

# ------------------------------------------------------------------
# ミニ講義(解説編)
# ------------------------------------------------------------------
LECTURES = {
 "tid": ("that は英文で最も顔が多い語。判定は「that の直後」を見るだけ——(1)完全文なら接続詞(名詞節)か同格"
         "(直前が the idea/fact など抽象名詞なら同格)、(2)主語や目的語が欠けた不完全文なら関係代名詞、"
         "(3)後ろに名詞が来る that/those は指示、(4)It is A that … は強調構文。訓練1では接続詞・関係代名詞・指示・強調が、"
         "訓練2では同格も加わる。that に〇を付けて役割を書き込む癖が、長文の速度を一段上げる。"),
 "iid": ("it を見たら反射的に「指すものは前に有るか?」と問う。有れば代名詞、無ければ形式の it——"
         "(1)It is … to/that の仮主語、(2)make/find it … to の仮目的語、(3)It is A that … の強調構文、"
         "(4)天候・時・距離・漠然の状況の it。訓練1① It is clear that … は仮主語、⑩ it is curiosity that … は強調。"
         "同じ It is … でも中身が名詞1つ(強調)か文全体(仮主語)かで別物。"),
 "aid": ("as は「後ろの形」で役割の8割が決まる。後ろが名詞なら前置詞「〜として」(treat A as B)。"
         "後ろが S+V なら接続詞で、意味は様態(〜のように)・理由(〜なので)・時/比例(〜するにつれて)を文脈で選ぶ。"
         "as … as は比較。訓練1では理由・様態・時・前置詞が、訓練2では as … as も出る。"
         "迷ったら「として」で訳せるか(名詞が続くか)をまず確かめる。"),
 "ell": ("英語は「前に出た形の繰り返し」を嫌って省略する。だから省略はいつも『前を見れば復元できる』。"
         "型は4つ——(1)反復語句の省略(gapping。カンマが合図: adults, about almost nothing)、"
         "(2)接続詞 that・目的格の関係詞の省略、(3)than・as の後ろの省略(did/be=代動詞)、"
         "(4)副詞節の S+be 省略(when young など)。省略位置に∧を書き、前から同じ形を補う。"),
 "par": ("and/but/or を見たら必ず「何と何を結ぶ?」と問う。並ぶのは必ず同じ形(名詞と名詞、to と to、節と節)。"
         "相関接続 not only A but also B ／ both A and B ／ either A or B ／ A rather than B ／ not A but B は、"
         "A と B の形を揃えて読むと骨格が崩れない。共通部分(訓練1⑥の makes it possible など)は一度だけくくり出す。"
         "長い等位接続ほど、共通項を外に出すと文が一気に短く見える。"),
 "deg": ("so・such・too・enough は単独では終わらない——必ず相方の that か to を連れてくる「程度→結果」の1セット。"
         "so+形/副+that / such+(a)名+that / too+形/副+to / 形/副+enough+to。so と such の違いは「後ろが形容詞か名詞か」。"
         "too … to は否定(〜すぎて…できない)、enough to は肯定(…するのに十分)。"
         "so/such/too/enough に□を付けたら、視線を that・to まで飛ばして結果節を確保する。"),
}

# ------------------------------------------------------------------
# 全訳(文番号つき)
# ------------------------------------------------------------------
TRANS = {
 "p1": {
  1: "好奇心こそが——生まれ持った才能ではなく——人を最も遠くまで運ぶものだ、ということは明らかだ。",
  2: "才能のある人は、なれたはずの姿を発見する前に、あまりに早く立ち止まってしまうことが多い。成功は楽に手に入ると思い込んでいるからだ。",
  3: "対照的に、好奇心はとても強力なので、退屈な作業をパズルに、退屈な一時間をゲームに変えてしまう。",
  4: "アインシュタインが言ったように、彼には特別な才能などなく、あったのはただ、落ち着きのない、尽きることのない好奇心だけだった。",
  5: "子どもは何にでも「なぜ」と尋ねる。大人は、ほとんど何についても「なぜ」とは尋ねない。",
  6: "好奇心があれば、他人が避ける問題を楽しみ、多くの人が恐れるまさにその失敗からも、落ち着いて学ぶことができる。",
  7: "年をとるにつれて、私たちは出来合いの答えを大量に蓄えていき、その結果、かつてよりずっと少なくしか質問しなくなる。",
  8: "好奇心は心を柔軟に保つだけでなく、学びは本当の意味では決して終わらない、ということを思い出させてくれる。",
  9: "好奇心を持ち続ける人は、新しい分野をどれも、壁としてではなく扉として見る。",
  10: "結局、心がどこまで遠くへ行けるかを決めるのは、才能ではなく好奇心なのだ。",
 },
 "p2": {
  1: "本は気のおけない会話と同じくらい簡単であるべきだ、と信じたくなる。しかし、私たちを本当に変える本は、たいてい簡単な本ではない。",
  2: "難しい本は、速度を落とし、読み返し、そして——十分に安心していられないほど長く——難しい箇所にとどまることを、私たちに求める。",
  3: "議論が複雑になるにつれて、その本は、いくつもの考えを一度に頭の中に保っておくよう、静かに要求してくる。",
  4: "心を鍛えるのは、まさにこの努力である——ちょうど、他人が持ち上げるのを見ることではなく、自分で重りを持ち上げることが、本物の力をつけるように。",
  5: "易しい本は私たちに答えを手渡す。難しい本は、問いを手渡す。",
  6: "心地よさだけを求めて読む人は、本が「考える一つの形」として果たせることを、見逃してしまう。",
  7: "いくつかの箇所はあまりに込み入ったパズルなので、著者は私たちを試しているのではないか、と疑い始めるほどだ。",
  8: "苦労は記憶を深める、という昔からの考えは、入念な研究によっても、日常の経験によっても裏づけられている。",
  9: "難しい章を苦労して進むにつれて、私たちは以前よりずっと多くを理解する。",
  10: "忍耐が要る。しかしその見返りは、他のすべての読み方を変えてしまうほどに大きい。",
  11: "結局、私たちの心に残り、最後のページをめくった後も長く心に働きかけ続けるのは、易しい本ではなく難しい本のほうなのだ。",
 },
}
