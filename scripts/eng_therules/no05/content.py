# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.05 — 単一ソース
テーマ: History Is Not About Memorizing the Past (歴史は暗記科目ではない) / MARCH・難関私大 (The Rules 2〜3 相当)
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "05",
    "level": "MARCH レベル",
    "level_sub": "難関私大 / The Rules 2〜3 相当",
    "theme_ja": "歴史は暗記科目ではない",
    "theme_en": "History Is Not About Memorizing the Past",
    "minutes": 18,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Ask students what history means to them, and many will describe a subject built out '
        'of dates, names, and lists to be memorized. In an age when any fact can be looked up '
        'in seconds, the subject can seem pointless: why carry in your head what a search '
        'engine will hand you faster? Some even ask whether schools should teach history at '
        'all. <span class="blank">【&nbsp;A&nbsp;】</span>, historians insist that this '
        'familiar picture misses what their discipline actually does, and that history was '
        'never really about memorizing the past.'),
    (2, 'Let us grant the obvious point. If the aim is simply to recall an isolated fact '
        '&mdash; the year a treaty was signed, the name of a king &mdash; a machine beats '
        'human memory every time: it is quicker, it does not forget, and it makes fewer '
        'mistakes. Nobody seriously argues that reciting dates has much value in itself, and '
        'a course that demanded nothing more would deserve its dull reputation.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span> the heart of the discipline lies '
        'elsewhere: not in the possession of facts, but in a way of asking questions about '
        'them. Consider what historians actually do. The past reaches them only in fragments '
        '&mdash; a letter here, a ledger there, a rumor written down years after the event. '
        'From such scattered evidence they must build an explanation that holds together. '
        '<u>In this respect, a historian works like a detective at the scene of a '
        'crime.<sup>(1)</sup></u> The comparison is not mere decoration; it restates the '
        'point: history trains us to reason from incomplete clues toward the most convincing '
        'account of why things happened.'),
    (4, 'This training becomes visible whenever one event yields rival explanations. Suppose '
        'two scholars study the decline of a trading town. One, reading the port records, '
        'concludes that the town faded because ships stopped coming; the other, weighing '
        'letters left by residents, argues that people had begun to leave before trade dried '
        'up. The evidence has not changed; the questions put to it have. Judging which '
        'account fits the fragments better, students learn to test explanations rather than '
        'swallow them whole.'),
    (5, 'History offers a second, quieter lesson: it makes the present look less permanent. '
        'Arrangements we now take for granted &mdash; schools sorted by age, national borders '
        'drawn on maps, even the weekend &mdash; have not always existed; each took shape at '
        'a particular time, under particular pressures, and could have turned out otherwise. '
        'To learn this is to realize that today\'s world is not the only one possible, and '
        'that what people once built, people can still rebuild.'),
    (6, '<u>Seen in this light, history is not so much a record of the past as a lens '
        'through which we examine the present.<sup>(2)</sup></u> Dates and documents still '
        'matter, but they matter the way the parts of a telescope matter: what counts is what '
        'they allow us to see. A student who has practiced asking where our institutions came '
        'from, and why accounts of them differ, carries that habit into newspapers, '
        'elections, and every argument about the future.'),
    (7, 'To say all this is not to dismiss factual knowledge. Without some framework of '
        'names and dates there is nothing to reason about, just as a detective cannot work '
        'without clues. The point is one of emphasis: facts are the skeleton of history, not '
        'its heart. Indeed, precisely because facts have become so easy to look up, <u>the '
        'habits of mind that history cultivates<sup>(3)</sup></u> have grown more valuable, '
        'not less. In a world overflowing with searchable information, the rarest skill is '
        'knowing which questions are worth asking.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Ask students what history means to them, and many will describe a subject built out of "
    "dates, names, and lists to be memorized. In an age when any fact can be looked up in "
    "seconds, the subject can seem pointless: why carry in your head what a search engine "
    "will hand you faster? Some even ask whether schools should teach history at all. "
    "Nonetheless, historians insist that this familiar picture misses what their discipline "
    "actually does, and that history was never really about memorizing the past. "
    "Let us grant the obvious point. If the aim is simply to recall an isolated fact the "
    "year a treaty was signed, the name of a king a machine beats human memory every time: "
    "it is quicker, it does not forget, and it makes fewer mistakes. Nobody seriously argues "
    "that reciting dates has much value in itself, and a course that demanded nothing more "
    "would deserve its dull reputation. "
    "And yet the heart of the discipline lies elsewhere: not in the possession of facts, but "
    "in a way of asking questions about them. Consider what historians actually do. The past "
    "reaches them only in fragments a letter here, a ledger there, a rumor written down "
    "years after the event. From such scattered evidence they must build an explanation that "
    "holds together. In this respect, a historian works like a detective at the scene of a "
    "crime. The comparison is not mere decoration; it restates the point: history trains us "
    "to reason from incomplete clues toward the most convincing account of why things "
    "happened. "
    "This training becomes visible whenever one event yields rival explanations. Suppose two "
    "scholars study the decline of a trading town. One, reading the port records, concludes "
    "that the town faded because ships stopped coming; the other, weighing letters left by "
    "residents, argues that people had begun to leave before trade dried up. The evidence "
    "has not changed; the questions put to it have. Judging which account fits the fragments "
    "better, students learn to test explanations rather than swallow them whole. "
    "History offers a second, quieter lesson: it makes the present look less permanent. "
    "Arrangements we now take for granted schools sorted by age, national borders drawn on "
    "maps, even the weekend have not always existed; each took shape at a particular time, "
    "under particular pressures, and could have turned out otherwise. To learn this is to "
    "realize that today's world is not the only one possible, and that what people once "
    "built, people can still rebuild. "
    "Seen in this light, history is not so much a record of the past as a lens through which "
    "we examine the present. Dates and documents still matter, but they matter the way the "
    "parts of a telescope matter: what counts is what they allow us to see. A student who "
    "has practiced asking where our institutions came from, and why accounts of them differ, "
    "carries that habit into newspapers, elections, and every argument about the future. "
    "To say all this is not to dismiss factual knowledge. Without some framework of names "
    "and dates there is nothing to reason about, just as a detective cannot work without "
    "clues. The point is one of emphasis: facts are the skeleton of history, not its heart. "
    "Indeed, precisely because facts have become so easy to look up, the habits of mind that "
    "history cultivates have grown more valuable, not less. In a world overflowing with "
    "searchable information, the rarest skill is knowing which questions are worth asking."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① As a result &nbsp; ② Nonetheless &nbsp; ③ For instance &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① Likewise &nbsp; ② Therefore &nbsp; ③ For example &nbsp; ④ And yet",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(2) <span class='en'>Seen in this light, history is not so much a record "
             "of the past as a lens through which we examine the present.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) について、歴史家が「犯罪現場の探偵のように働く（<span class='en'>works "
             "like a detective at the scene of a crime</span>）」とはどういうことか。本文に即して"
             "日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "第4段で紹介されている「二人の学者」の例が示す内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 同じ出来事を研究していても、証拠に向ける問いとその読み方しだいで、導かれる説明は変わりうる。",
         "② 港の記録と住民の手紙とでは、住民の手紙の方が証拠として常に信頼できると決まっている。",
         "③ 新しい証拠が発見されて加わったことによって、町の衰退についての従来の説明が覆された。",
         "④ 二人の説明は最終的に同じ結論へ行き着くのだから、証拠をどう読むかは実際には重要でない。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>the habits of mind that history cultivates</span>"
             "（歴史が養う心の習慣）とは何か。本文全体をふまえ、二つ挙げて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 事実の知識にはもはや価値がないのだから、歴史の授業から年号や人名の学習を完全に取り除き、考え方の訓練だけを行うべきである。",
         "② 検索技術が十分に発達した現代では、過去の事実の扱いは機械に任せ、学校は歴史という科目そのものを廃止する方向へ進むべきである。",
         "③ 歴史の核心は事実の所有ではなく問い方・考え方の訓練にあり、事実が簡単に検索できる時代だからこそ、その価値はむしろ増している。",
         "④ 歴史の役割は過去の出来事をできるだけ正確に記録して保存することにあり、現在の社会の問題とは切り離して学ばれるべきものである。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 単に個々の事実を思い出すだけであれば、機械の方が人間の記憶よりも速く、誤りも少ないと筆者は認めている。",
         "② 過去の記録は断片としてしか歴史家に届かず、歴史家は散らばった証拠から筋の通った説明を組み立てる。",
         "③ 二人の学者の例では、新しい証拠が発見されて加わったために、町の衰退についての説明が変化した。",
         "④ 筆者によれば、事実の知識は歴史を学ぶうえで完全に無価値であり、学習から取り除いてよいものである。",
         "⑤ 今日当然と見なされている制度の中には、特定の時代に特定の圧力のもとで形づくられたものがある。",
         "⑥ 情報が簡単に検索できる時代になったことで、歴史が養う心の習慣の価値は以前よりも小さくなった。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ② Nonetheless　　B ＝ ④ And yet",
     "exp": "A：「歴史＝暗記科目で、検索できる時代には無意味」という通念（第1段前半）に対し、"
            "歴史家が「歴史は暗記の科目ではない」と反論する流れ。<b>逆接</b>でつなぐ → Nonetheless。"
            "As a result（因果）・For instance（例示）・In addition（追加）は不可。<br>"
            "B：第2段「確かに事実の想起なら機械が勝つ（＝譲歩）」に対し、第3段は「だが学問の核心は"
            "別のところにある」と主張へ<b>転換</b>する。逆接 → And yet。Likewise（類比）・"
            "Therefore（因果）・For example（例示）は流れに合わない。 〔<b>解法ルール R7</b>／"
            "<b>読解ルール R1</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "①",
     "exp": "第4段「The evidence has not changed; the questions put to it have.」＝証拠は同じでも、"
            "証拠に向ける<b>問い（読み方）</b>が変われば説明が変わる → ①。②は本文にない（どちらの"
            "証拠が信頼できるかは述べていない）。③は「証拠は変わっていない」に真っ向から反する。"
            "④も逆（二つの説明は対立している＝rival explanations）。 〔<b>解法ルール R9</b>／"
            "<b>読解ルール R4</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "③",
     "exp": "第3段「not in the possession of facts, but in a way of asking questions」＋第7段"
            "「precisely because facts have become so easy to look up, the habits of mind … have "
            "grown more valuable, not less」と一致 → ③。①は第7段冒頭「To say all this is not to "
            "dismiss factual knowledge（事実の知識を切り捨てる意味ではない）」に反する。②は本文に"
            "ない（科目の廃止を主張してはいない）。④は第6段「現在を吟味するレンズ」と逆。 "
            "〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・②・⑤",
     "exp": "③×：第4段「The evidence has not changed（証拠は変わっていない）」に反する——変わった"
            "のは問いの方。④×：「完全に無価値」は<b>言い過ぎ</b>。第7段「To say all this is not to "
            "dismiss factual knowledge」に反する。⑥×：第7段「have grown more valuable, not less"
            "（価値はむしろ増した）」と逆。 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(2)和訳",
     "model": "このように見ると、歴史とは、過去の記録というよりも、むしろそれを通して私たちが現在を"
              "吟味する（ための）レンズなのである。",
     "points": "▶<b>採点要素</b>：①<b>not so much A as B</b>＝「AというよりむしろB」の構文訳出"
               "（重心はB＝レンズ）／②<b>Seen in this light</b>＝分詞構文「このように見ると」／"
               "③a lens through which we examine the present＝前置詞＋関係代名詞「それを通して"
               "私たちが現在を吟味するレンズ」。 〔<b>構文ルール R13・R19</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "歴史家のもとに届く過去の記録は、手紙や帳簿や後年の噂話といった断片にすぎず、歴史家は、"
              "探偵が現場に残された不完全な手がかりから事件の筋書きを推理するのと同じように、散らばった"
              "証拠から、なぜその出来事が起きたのかについて最も説得力のある筋の通った説明を組み立てる、"
              "ということ。",
     "points": "▶<b>採点要素</b>：①比喩の直後の言い換え文（it restates the point: history trains us "
               "to reason from incomplete clues toward the most convincing account …）を根拠にする"
               "〔<b>読解ルール R18</b>〕／②過去の記録が<b>断片的</b>であること／③そこから<b>筋の通った"
               "（最も説得力のある）説明を組み立てる・推論する</b>こと。 〔<b>解法ルール R8</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①断片的な証拠から因果関係をたどって筋の通った説明を組み立て、対立する説明のどちらが"
              "証拠に合うかを検証して、説明を鵜呑みにしない習慣。②今日当然と見なされている制度も、"
              "かつては存在しなかったり別の形をとっていたりしたと知り、現在の世界を唯一のあり方と"
              "見なさず、変えられるものとして眺める習慣。",
     "points": "▶<b>採点要素</b>：本文の二本柱と対応させる。①<b>因果推論・説明の検証</b>（第3〜4段："
               "incomplete clues → the most convincing account／test explanations rather than "
               "swallow them whole）／②<b>現在の相対化</b>（第5段：当たり前の制度の歴史性 → what "
               "people once built, people can still rebuild）。各5点。 〔<b>読解ルール R5</b>："
               "the habits of mind の中身を確定／<b>解法ルール R8</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A・B。第1段（Nonetheless→歴史家の反論）、第3段（And yet→主張への転換）。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "第3段 not in the possession of facts, but in a way of asking questions、第7段 the skeleton of history, not its heart。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段「二人の学者」の例は「問いが変われば説明が変わる」という抽象の具体例。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "下線部(3) the habits of mind＝歴史が鍛える二つの習慣（因果推論の検証＋現在の相対化）を指す。"),
        ("R18", "★NEW 比喩・たとえ話は、直前直後の主張の言い換えとして読む（比喩だけで終わらせない）", "★★★",
         "下線部(1)「探偵のように働く」→ 直後の it restates the point: … が比喩の中身。第6段の望遠鏡、第7段の骨組みも同型。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。コロン(:)直後の言い換え（第3段 it restates the point: …）を利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。④の「完全に無価値」、⑥の「価値は小さくなった」などは典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R13", "not so much A as B ＝「AというよりむしろB」（重心はB）", "★★★",
         "下線部(2)＝問2。a record of the past（A）より a lens through which we examine the present（B）に重心。"),
        ("R19", "★NEW 分詞構文（-ing, …）は「〜しながら／〜して／〜すると」で骨格に添える", "★★★",
         "第4段 reading … / weighing … / Judging …、下線部(2)冒頭 Seen in this light（受動の分詞構文）。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「歴史＝年号と人名の暗記科目。検索できる時代に覚える意味はない」を提示。→ "
             "<b>Nonetheless（R1）</b>：歴史家は「歴史は暗記の科目ではない」と反論。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>Let us grant …</b>：確かに、単なる事実の想起なら機械の方が速く・忘れず・正確。"
             "＝通念の一部は認める。"},
    {"arrow": "◀ And yet 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "核心は<b>事実の所有ではなく「問いの立て方」（not A but B＝R3）</b>。理由①＝断片的な"
             "証拠から筋の通った説明を組み立てる訓練。<b>探偵の比喩→直後に言い換え（R18）</b>。"},
    {"arrow": "↓　理由①の具体化（R4）"},
    {"role": "理由①", "para": "¶4", "kind": "reason",
     "text": "「二人の学者」の例：<b>証拠は同じでも、問い（読み方）が変われば説明が変わる</b>。"
             "説明を鵜呑みにせず検証する訓練。<b>分詞構文（R19）</b>が三つ。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>現在の相対化</b>：当たり前の制度（年齢別の学校・国境・週末）もかつては無かった／"
             "別の形だった。＝今日の世界は唯一のあり方ではなく、<b>今も変えられる</b>。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "歴史は<b>過去の記録というより、現在を吟味するレンズ（not so much A as B＝R13）</b>"
             "＝下線部(2)。年号や文書は望遠鏡の部品——大事なのは「何を見せてくれるか」。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：事実の知識は<b>骨組みとして必要</b>（無意味だという話ではない）。"
             "むしろ<b>検索できる時代だからこそ</b>、問い方を鍛える歴史の価値は増した。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 「暗記科目」という通念 vs 歴史家の実像",
     "caption": "同じ「歴史」でも、<b>事実の暗記</b>と見なせば検索に勝てず無意味に見えるが、"
                "<b>問い方の訓練</b>と見なせば、検索できる時代にこそ価値が増す。",
     "para": "→ 第1・2・7段"},
    {"id": "fig2", "title": "図2 ｜ 歴史が鍛える二つの習慣（＝the habits of mind）",
     "caption": "下線部(3)の the habits of mind はこの二つ。①<b>断片的な証拠から因果をたどり、"
                "説明を検証する</b>（第3〜4段）、②<b>現在を当然視せず、変えられるものとして見る</b>"
                "（第5段）。",
     "para": "→ 第3〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 歴史は「過去の記録」というより「現在を読むレンズ」",
     "caption": "核心の一文（下線部(2)）。<b>not so much A as B</b>＝重心はB。事実は骨組みとして"
                "使いつつ——歴史の本体は<b>問い方・考え方の訓練</b>にある。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "生徒たちに、歴史とは自分にとって何かと尋ねてみれば、多くの生徒が、年号と人名と暗記すべき"
        "リストでできた科目だと説明するだろう。どんな事実も数秒で調べられる時代には、この科目は無意味に"
        "見えかねない——検索エンジンがもっと速く手渡してくれるものを、なぜ頭の中に蓄えておくのか、と。"
        "そもそも学校は歴史を教えるべきなのか、とまで問う人さえいる。<b>それにもかかわらず</b>、"
        "歴史家たちは、このおなじみのイメージは自分たちの学問が実際にしていることを捉えそこねており、"
        "歴史はそもそも過去を暗記することが本義だったことなど一度もない、と主張するのである。"),
    (2, "まず、明白な点は認めよう。目的が単に個々の事実——条約が結ばれた年や、王の名前——を思い出す"
        "ことだけなら、機械は毎回、人間の記憶に勝つ。機械の方が速く、忘れず、誤りも少ないのだ。年号の"
        "暗唱それ自体に大きな価値があるなどと本気で主張する者はいないし、それ以上のことを何も求めない"
        "授業であれば、「退屈」というその評判を受けて当然だろう。"),
    (3, "<b>それでもなお</b>、この学問の核心は別のところに——すなわち、事実の所有にではなく、事実への"
        "問いの立て方にある。歴史家が実際に何をしているかを考えてみよう。過去は断片としてしか彼らの"
        "もとに届かない——こちらに手紙が一通、あちらに帳簿が一冊、出来事の何年も後に書き留められた噂話が"
        "一つ、というように。そのような散らばった証拠から、彼らは筋の通った説明を組み立てなければ"
        "ならない。<b>この点で、歴史家は犯罪現場の探偵のように働くのである。</b>この比喩は単なる飾りでは"
        "ない。それは要点をそのまま言い直している。すなわち歴史は、不完全な手がかりから、なぜ物事が"
        "起きたのかについての最も説得力のある説明へと推論するように、私たちを訓練するのだ。"),
    (4, "この訓練は、一つの出来事が対立する説明を生むとき、はっきりと姿を現す。二人の学者が、ある交易の"
        "町の衰退を研究しているとしよう。一人は港の記録を読んで、船が来なくなったせいで町は衰えたと"
        "結論づける。もう一人は住民が残した手紙を吟味して、交易が途絶える前に人々はすでに町を離れ始めて"
        "いたと論じる。証拠は変わっていない。変わったのは、証拠に向けられた問いなのだ。どちらの説明が"
        "より断片に合うかを判定するなかで、生徒は説明を丸ごと鵜呑みにするのではなく、検証することを学ぶ。"),
    (5, "歴史はもう一つの、より静かな教訓を与えてくれる。すなわち、現在をそれほど永続的なものには見えなく"
        "させるのだ。今の私たちが当然視している仕組み——年齢で分けられた学校、地図に引かれた国境、週末で"
        "さえ——は、常に存在してきたわけではない。それぞれが特定の時代に、特定の圧力の下で形をとったので"
        "あり、別の形になっていた可能性もあった。このことを学ぶのは、今日の世界が唯一あり得る世界では"
        "なく、人々がかつて築いたものは今の人々にもなお作り直せるのだ、と悟ることにほかならない。"),
    (6, "<b>このように見ると、歴史とは、過去の記録というよりも、むしろそれを通して私たちが現在を吟味する"
        "レンズなのである。</b>年号や文書は依然として重要だが、それらは、望遠鏡の部品が重要であるのと同じ"
        "意味で重要なのだ。つまり大事なのは、それらが何を見せてくれるかである。私たちの制度がどこから"
        "来たのか、なぜその説明は食い違うのか、と問う練習を積んだ生徒は、その習慣を、新聞へ、選挙へ、"
        "そして未来をめぐるあらゆる議論へと持ち込んでいく。"),
    (7, "以上のことは、事実の知識を切り捨てるという意味ではない。名前と年号というある程度の骨組みが"
        "なければ、推論する対象そのものが存在しない——ちょうど探偵が手がかりなしには働けないように。"
        "要点は力点の置き方にある。すなわち事実は歴史の骨組みであって、その心臓ではない。それどころか、"
        "事実がこれほど検索しやすくなったからこそ、<b>歴史が養う心の習慣</b>の価値は、減るどころか"
        "むしろ増したのである。検索可能な情報であふれる世界で最も稀少な技能とは、どの問いが問うに値する"
        "かを知っていることなのだ。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("look up ~", "〜を調べる、検索する"),
    ("pointless", "無意味な"),
    ("discipline", "学問（分野）"),
    ("possession", "所有"),
    ("fragment", "断片"),
    ("ledger", "帳簿"),
    ("scattered", "散らばった、ばらばらの"),
    ("hold together", "筋が通る、まとまる"),
    ("mere decoration", "単なる飾り"),
    ("restate", "言い直す、再び述べる"),
    ("convincing", "説得力のある"),
    ("account", "説明、記述"),
    ("rival", "対立する、競合する"),
    ("weigh", "吟味する、比較検討する"),
    ("dry up", "枯れる、途絶える"),
    ("swallow ~ whole", "〜を丸ごと鵜呑みにする"),
    ("take ~ for granted", "〜を当然のことと思う"),
    ("turn out otherwise", "別の結果になる"),
    ("examine", "吟味する、調べる"),
    ("institution", "制度"),
    ("dismiss", "切り捨てる、退ける"),
    ("cultivate", "（能力・習慣を）養う、育てる"),
    ("be worth doing", "〜する価値がある"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 問題提起：歴史＝暗記科目という通念と、その反転",
  "sentences": [
    {"chunks": [("V","Ask","尋ねてみよ"),("O","students","生徒たちに"),
                ("O","[what history means to them],","歴史とは自分にとって何かと"),
                ("接","and","そうすれば"),("S","many","多くの生徒が"),("V","will describe","説明するだろう"),
                ("O","a subject &lt;built out of dates, names, and lists to be memorized&gt;.","年号・人名・暗記すべきリストでできた科目だと")],
     "note":"▶ <b>命令文 + and …</b>＝「〜せよ、そうすれば…」。what history means to them＝間接疑問（ask の二つ目の目的語）。built …＝過去分詞が subject を後ろから修飾。"},
    {"chunks": [("M","(In an age &lt;when any fact can be looked up in seconds&gt;),","どんな事実も数秒で検索できる時代には"),
                ("S","the subject","この科目は"),("V","can seem","見えかねない"),("C","pointless:","無意味に"),
                ("M","why carry (in your head)","なぜ頭の中に蓄えるのか"),
                ("O","[what a search engine will hand you faster]?","検索エンジンがもっと速く手渡してくれるものを")],
     "note":"▶ when …＝関係副詞節が an age を修飾。<b>コロン(:)以下</b>＝「無意味に見える」の中身（自問）。what＝関係代名詞「〜するもの」。hand you A＝「あなたにAを手渡す」。"},
    {"chunks": [("S","Some","一部の人は"),("M","even","さらには"),("V","ask","問う"),
                ("O","[whether schools should teach history at all].","そもそも学校は歴史を教えるべきなのか、と")],
     "note":"▶ whether 節＝名詞節「〜かどうか」。at all＝「そもそも・少しでも」。通念側の極端な声＝この後の反論の前振り。"},
    {"chunks": [("接","Nonetheless,","それにもかかわらず"),("S","historians","歴史家たちは"),("V","insist","主張する"),
                ("O","[that this familiar picture misses what their discipline actually does],","このおなじみのイメージは、自分たちの学問が実際にしていることを捉えそこねている、と"),
                ("接","and","また"),
                ("O","[that history was never really about memorizing the past].","歴史はそもそも過去の暗記が本義だったことなど一度もない、と")],
     "note":"▶ <b>R1｜逆接 Nonetheless の直後が主張</b>（＝空所A）。insist that …, and that …＝that 節二つの並列。miss＝「捉えそこねる」。"},
  ]},
 {"head": "第2段 — 譲歩：確かに、事実の想起なら機械が勝つ",
  "sentences": [
    {"chunks": [("V","Let us grant","認めよう"),("O","the obvious point.","明白な点は")],
     "note":"▶ <b>Let us do</b>＝「〜しよう」。まず相手の言い分を認める＝譲歩の宣言。この段全体が譲歩。"},
    {"chunks": [("M","(If the aim is simply to recall an isolated fact)","目的が単に個々の事実を思い出すことだけなら"),
                ("-","&mdash; the year &lt;(when) a treaty was signed&gt;, the name of a king &mdash;","——条約が結ばれた年や、王の名前——"),
                ("S","a machine","機械は"),("V","beats","打ち負かす"),("O","human memory","人間の記憶を"),
                ("M","every time:","毎回"),
                ("S","it","それは"),("V","is","である"),("C","quicker,","より速い"),
                ("S","it","それは"),("V","does not forget,","忘れない"),
                ("接","and","そして"),("S","it","それは"),("V","makes","犯す"),("O","fewer mistakes.","より少ない誤りしか（〜ない）")],
     "note":"▶ If 節＝副詞節。ダッシュ間＝an isolated fact の同格（具体例）。<b>コロン(:)以下</b>＝beats の中身を三つ並列（速い・忘れない・誤りが少ない）。"},
    {"chunks": [("S","Nobody","誰も〜ない"),("M","seriously","本気で"),("V","argues","主張し（ない）"),
                ("O","[that reciting dates has much value in itself],","年号の暗唱それ自体に大きな価値があるとは"),
                ("接","and","そして"),
                ("S","a course &lt;that demanded nothing more&gt;","それ以上を何も求めない授業なら"),
                ("V","would deserve","値するだろう"),("O","its dull reputation.","その「退屈」という評判に")],
     "note":"▶ reciting＝動名詞（that 節内の主語）。that demanded …＝関係代名詞。would＝仮定法（そのような授業があれば）。"},
  ]},
 {"head": "第3段 — 主張の転換：核心は「問いの立て方」＋探偵の比喩（And yet）",
  "sentences": [
    {"chunks": [("接","And yet","それでもなお"),("S","the heart of the discipline","この学問の核心は"),
                ("V","lies","ある"),("M","elsewhere:","別のところに"),
                ("M","not (in the possession of facts), but (in a way of asking questions about them).","事実の所有にではなく、事実への問いの立て方に")],
     "note":"▶ <b>R1｜And yet＝逆接でここが主張転換点</b>（＝空所B）。<b>R3｜not A but B</b>＝Bの側（問いの立て方）が核心。lie in ~＝「〜にある」。"},
    {"chunks": [("V","Consider","考えてみよ"),("O","[what historians actually do].","歴史家が実際に何をしているかを")],
     "note":"▶ 命令文。what …＝間接疑問（名詞節）。ここから「核心」の中身の説明へ。"},
    {"chunks": [("S","The past","過去は"),("V","reaches","届く"),("O","them","彼らのもとに"),
                ("M","only (in fragments)","断片としてしか"),
                ("-","&mdash; a letter here, a ledger there, a rumor &lt;written down years after the event&gt;.","——こちらに手紙が一通、あちらに帳簿が一冊、出来事の何年も後に書き留められた噂話が一つ")],
     "note":"▶ only in fragments＝「断片としてしか」。ダッシュ以下＝fragments の具体的列挙（同格）。written down …＝過去分詞が rumor を修飾。"},
    {"chunks": [("M","(From such scattered evidence)","そのような散らばった証拠から"),
                ("S","they","彼らは"),("V","must build","組み立てねばならない"),
                ("O","an explanation &lt;that holds together&gt;.","筋の通った説明を")],
     "note":"▶ hold together＝「（全体として）まとまる・筋が通る」。that＝関係代名詞。歴史家の仕事＝断片→説明、の要約。"},
    {"chunks": [("M","(In this respect),","この点で"),("S","a historian","歴史家は"),("V","works","働く"),
                ("M","(like a detective at the scene of a crime).","犯罪現場の探偵のように")],
     "note":"▶ <b>下線部(1)＝問3</b>。like ~＝「〜のように」（比喩）。<b>R18｜比喩は直後の言い換えとセットで読む</b>——次の文が比喩の中身。"},
    {"chunks": [("S","The comparison","この比喩は"),("V","is","である"),("C","not mere decoration;","単なる飾りではない"),
                ("S","it","それは"),("V","restates","言い直している"),("O","the point:","要点を"),
                ("S","history","（すなわち）歴史は"),("V","trains","訓練する"),("O","us","私たちを"),
                ("C","to reason (from incomplete clues) (toward the most convincing account of [why things happened]).","不完全な手がかりから、なぜ物事が起きたのかについての最も説得力ある説明へと推論するように")],
     "note":"▶ <b>R18｜比喩の直後の言い換え</b>：コロン(:)以下が「探偵」の比喩の中身〔R8｜コロン＝イコール関係〕。train O to do＝「Oを〜するよう訓練する」。why things happened＝間接疑問（of の目的語）。"},
  ]},
 {"head": "第4段 — 理由①の具体化：問いが変われば説明が変わる（二人の学者）",
  "sentences": [
    {"chunks": [("S","This training","この訓練は"),("V","becomes","なる"),("C","visible","目に見えるように"),
                ("M","(whenever one event yields rival explanations).","一つの出来事が対立する説明を生むときはいつでも")],
     "note":"▶ whenever …＝副詞節「〜するときはいつでも」。yield＝「生む」。<b>R4｜ここから抽象（問いの訓練）→具体（二人の学者）へ</b>。"},
    {"chunks": [("V","Suppose","仮定してみよ"),
                ("O","[(that) two scholars study the decline of a trading town].","二人の学者が、ある交易の町の衰退を研究している、と")],
     "note":"▶ Suppose (that) SV＝「〜と仮定せよ」（that 省略）。具体例の導入〔<b>R4</b>〕。"},
    {"chunks": [("S","One,","一人は"),("M","(reading the port records),","港の記録を読んで"),
                ("V","concludes","結論づける"),
                ("O","[that the town faded (because ships stopped coming)];","船が来なくなったせいで町は衰えた、と"),
                ("S","the other,","もう一人は"),("M","(weighing letters &lt;left by residents&gt;),","住民が残した手紙を吟味して"),
                ("V","argues","論じる"),
                ("O","[that people had begun to leave (before trade dried up)].","交易が途絶える前に、人々はすでに町を離れ始めていた、と")],
     "note":"▶ <b>R19｜reading … / weighing …＝分詞構文</b>「〜して・〜しながら」（主語 One / the other に添える）。left by residents＝過去分詞修飾。過去完了 had begun＝「離れ始め」が「途絶え」より前。"},
    {"chunks": [("S","The evidence","証拠は"),("V","has not changed;","変わっていない"),
                ("S","the questions &lt;put to it&gt;","それに向けられた問いが"),("V","have.","変わったのだ")],
     "note":"▶ put to it＝過去分詞が the questions を修飾。have＝have changed の省略。<b>R9注意</b>：問7③「新しい証拠が加わった」はこの一文で×。"},
    {"chunks": [("M","(Judging [which account fits the fragments better]),","どちらの説明がより断片に合うかを判定しながら"),
                ("S","students","生徒は"),("V","learn","学ぶ"),
                ("O","to test explanations (rather than swallow them whole).","説明を丸ごと鵜呑みにするのではなく、検証することを")],
     "note":"▶ <b>R19｜Judging …＝分詞構文</b>。which account …＝間接疑問。rather than (to) swallow＝<b>R3</b>の仲間（rather than の前＝test の側が主張）。swallow ~ whole＝「丸ごと鵜呑みにする」。"},
  ]},
 {"head": "第5段 — 理由②：現在の相対化——当たり前は永遠ではない",
  "sentences": [
    {"chunks": [("S","History","歴史は"),("V","offers","与える"),
                ("O","a second, quieter lesson:","第二の、より静かな教訓を"),
                ("S","it","それは"),("V","makes","させる"),("O","the present","現在を"),
                ("C","look less permanent.","それほど永続的でないように見える（ように）")],
     "note":"▶ <b>コロン(:)</b>＝lesson の中身（言い換え）〔R8〕。使役 <b>make O do</b>（look が原形不定詞）。理由②の主題提示。"},
    {"chunks": [("S","Arrangements &lt;(that) we now take for granted&gt;","今の私たちが当然視している仕組みは"),
                ("-","&mdash; schools &lt;sorted by age&gt;, national borders &lt;drawn on maps&gt;, even the weekend &mdash;","——年齢で分けられた学校、地図に引かれた国境、週末でさえ——"),
                ("V","have not always existed;","常に存在してきたわけではない"),
                ("S","each","それぞれは"),("V","took","とった"),("O","shape","形を"),
                ("M","(at a particular time), (under particular pressures),","特定の時代に、特定の圧力の下で"),
                ("接","and","そして"),("V","could have turned out","なっていたかもしれない"),("M","otherwise.","別の形に")],
     "note":"▶ take A for granted＝「Aを当然と思う」（関係詞省略）。not always＝<b>部分否定</b>「常に〜とは限らない」。could have done＝「〜だったかもしれない」。sorted / drawn＝過去分詞修飾。"},
    {"chunks": [("S","To learn this","このことを学ぶことは"),("V","is","である"),("C","to realize","悟ることに（等しい）"),
                ("O","[that today's world is not the only one possible],","今日の世界が唯一あり得る世界ではないと"),
                ("接","and","また"),
                ("O","[that [what people once built], people can still rebuild].","人々がかつて築いたものは、今の人々にもなお作り直せるのだと")],
     "note":"▶ 不定詞主語 To learn ＝ 補語 to realize（A is B）。one＝world の代用。what people once built＝rebuild の目的語が文頭に出た形（強調）。"},
  ]},
 {"head": "第6段 — ★核心：歴史は「過去の記録」というより「現在を読むレンズ」",
  "sentences": [
    {"chunks": [("M","(Seen in this light),","このように見ると"),
                ("S","history","歴史は"),("V","is","である"),
                ("C","not so much a record of the past as a lens &lt;through which we examine the present&gt;.","過去の記録というよりも、むしろそれを通して私たちが現在を吟味するレンズ")],
     "note":"▶ <b>下線部(2)＝問2</b>。<b>R13｜not so much A as B＝「AというよりむしろB」（重心はB）</b>。<b>R19｜Seen …＝受動の分詞構文</b>「このように見ると」。through which＝前置詞＋関係代名詞。"},
    {"chunks": [("S","Dates and documents","年号や文書は"),("M","still","依然として"),("V","matter,","重要である"),
                ("接","but","しかし"),("S","they","それらは"),("V","matter","重要なのだ"),
                ("M","(the way the parts of a telescope matter):","望遠鏡の部品が重要であるのと同じ意味で"),
                ("S","[what counts]","重要なのは"),("V","is","である"),
                ("C","[what they allow us to see].","それらが見せてくれるもの")],
     "note":"▶ matter（動詞）＝「重要である」。the way SV＝接続詞的「〜するのと同じように」。<b>R18｜望遠鏡の比喩もコロン(:)直後に言い換え</b>。what counts / what they allow us to see＝関係代名詞 what。allow O to do。"},
    {"chunks": [("S","A student &lt;who has practiced asking [where our institutions came from], and [why accounts of them differ]&gt;,","私たちの制度がどこから来たのか、なぜその説明は食い違うのか、と問う練習を積んだ生徒は"),
                ("V","carries","持ち込む"),("O","that habit","その習慣を"),
                ("M","(into newspapers, elections, and every argument about the future).","新聞へ、選挙へ、そして未来をめぐるあらゆる議論へと")],
     "note":"▶ practice doing＝「〜する練習をする」。where … / why …＝間接疑問の並列。長い主語（A student &lt;who …&gt;）の直後の carries が述語動詞。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：事実は骨組み。検索の時代こそ「問い方」の価値が増す",
  "sentences": [
    {"chunks": [("S","To say all this","以上のことを言うのは"),("V","is not","〜ではない"),
                ("C","to dismiss factual knowledge.","事実の知識を切り捨てることでは")],
     "note":"▶ 不定詞主語＝不定詞補語。誤読の予防線（譲歩）。<b>R9注意</b>：問7④「完全に無価値」はこの一文で×。"},
    {"chunks": [("M","(Without some framework of names and dates)","名前と年号というある程度の骨組みなしには"),
                ("V","there is","存在しない"),("S","nothing &lt;to reason about&gt;,","推論すべき対象が何も"),
                ("M","(just as a detective cannot work without clues).","ちょうど探偵が手がかりなしには働けないように")],
     "note":"▶ there is 構文。to reason about＝不定詞が nothing を修飾。just as ~＝「ちょうど〜のように」（類比）——第3段の探偵の比喩の回収〔<b>R18</b>〕。"},
    {"chunks": [("S","The point","要点は"),("V","is","である"),("C","one of emphasis:","力点の問題"),
                ("S","facts","（すなわち）事実は"),("V","are","である"),
                ("C","the skeleton of history, not its heart.","歴史の骨組みであって、その心臓ではない")],
     "note":"▶ one＝a matter の代用。<b>コロン(:)＝直前の言い換え</b>〔R8〕。<b>R3｜B, not A</b>＝not A but B の変形——「骨組み（必要）だが心臓（本体）ではない」。"},
    {"chunks": [("接","Indeed,","それどころか"),
                ("M","(precisely because facts have become so easy to look up),","事実がこれほど検索しやすくなったからこそ"),
                ("S","the habits of mind &lt;that history cultivates&gt;","歴史が養う心の習慣は"),
                ("V","have grown","なった"),
                ("C","more valuable, not less.","より価値あるものに——減ったのではなく")],
     "note":"▶ <b>下線部(3)＝問5</b>。precisely because＝「まさに〜だからこそ」。easy to look up＝facts が look up の意味上の目的語。<b>R5｜the habits of mind の中身＝二つの習慣（第3〜4段・第5段）を確定</b>。"},
    {"chunks": [("M","(In a world &lt;overflowing with searchable information&gt;),","検索可能な情報であふれる世界では"),
                ("S","the rarest skill","最も稀少な技能は"),("V","is","である"),
                ("C","knowing [which questions are worth asking].","どの問いが問うに値するかを知っていること")],
     "note":"▶ overflowing …＝現在分詞が world を修飾。knowing＝動名詞（補語）。which questions …＝間接疑問。be worth doing＝「〜する価値がある」。締め＝「問い方」こそ核心。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=4文/第2段=3文/第3段=6文/第4段=5文/第5段=3文/第6段=3文/第7段=5文)
SVOC_LOGIC = {
    (1, 4): "対比",                                   # s4 Nonetheless→歴史家の反論
    (2, 1): "譲歩", (2, 3): "譲歩",                    # s1 Let us grant / s3 駄目押し
    (3, 1): "対比", (3, 3): "具体例", (3, 4): "主張", (3, 6): "主張",
    (4, 1): "主張", (4, 2): "具体例", (4, 3): "具体例", (4, 4): "対比", (4, 5): "主張",
    (5, 1): "追加", (5, 2): "具体例", (5, 3): "主張",
    (6, 1): "主張", (6, 2): "対比", (6, 3): "主張",
    (7, 1): "譲歩", (7, 2): "譲歩", (7, 3): "主張", (7, 4): "因果", (7, 5): "主張",
}
