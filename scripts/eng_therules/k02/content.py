# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.02 — 単一ソース
テーマ: Reading Stories Is Practice in Understanding Others
（物語を読むことは他人を理解する練習になる）/ 基礎レベル（偏差値55〜60 / The Rules 1〜2 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "02",
    "level": "基礎レベル",
    "level_sub": "偏差値55〜60 / The Rules 1〜2 相当",
    "theme_ja": "物語を読むことは他人を理解する練習になる",
    "theme_en": "Reading Stories Is Practice in Understanding Others",
    "minutes": 15,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Many people believe that reading stories is just a pleasant way to pass the time. '
        'Novels are fun, they say, but they do not really teach us anything useful. If you '
        'want useful knowledge, you should pick up a textbook or a practical guide instead. '
        'Parents often tell their children to put down novels and study something serious. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, this common view may be missing '
        'something important. Stories can train a skill that few textbooks even try to teach.'),
    (2, 'It is true that practical books are often the fastest road to information. If you '
        'want to learn how to cook rice, a clear guide helps you at once. A textbook gives '
        'you names, dates, and rules in a neat order. Nobody learns math mainly by reading '
        'novels. For gaining facts and skills, practical books usually win.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, stories can do something that '
        'practical books cannot. When we read a story, we do more than receive information '
        'about a character. We step inside that character\'s head and live there for a '
        'while. We see the world through the eyes of a nervous student, a tired nurse, or a '
        'lonely old man. A textbook tells us about people; a story lets us be another person '
        'for a moment.'),
    (4, 'Think about what actually happens as we turn the pages. When the hero faces a hard '
        'choice, we feel her fear and hesitate with her. When she hurts a friend without '
        'meaning to, we feel sorry and ask what we would have done. <u>Reading a novel is, '
        'in a sense, trying on another person\'s life, like a piece of '
        'clothing.<sup>(1)</sup></u> In other words, fiction gives us safe chances to '
        'practice feeling, judging, and choosing as somebody else.'),
    (5, 'This practice matters because everyday life keeps demanding the same skill. A '
        'friend suddenly stops talking to you; a customer looks upset for no clear reason. '
        'In such moments, we must imagine feelings that we cannot see directly. Research '
        'suggests that people who read fiction regularly tend to be better at guessing what '
        'others think and feel. Because stories make us repeat this guessing, they quietly '
        'build a base for friendship and for work.'),
    (6, 'Some people still say that readers of novels are running away from the real world. '
        'The truth is closer to the opposite. <u>Reading stories is not an escape from real '
        'life but practice for it.<sup>(2)</sup></u> Every hour spent inside another '
        'person\'s story trains the imagination we need when we face real people.'),
    (7, 'Of course, none of this means that practical books are unnecessary. We still need '
        'textbooks for facts and guides for skills, and stories cannot replace them. <u>The '
        'two kinds of books are not rivals; they simply do different jobs.<sup>(3)</sup></u> '
        'One fills our heads with knowledge, and the other stretches our hearts toward other '
        'people. A good reader keeps a place on the shelf for both.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める・下線/タグは除去)
PASSAGE_PLAIN = (
    "Many people believe that reading stories is just a pleasant way to pass the time. "
    "Novels are fun, they say, but they do not really teach us anything useful. If you want "
    "useful knowledge, you should pick up a textbook or a practical guide instead. Parents "
    "often tell their children to put down novels and study something serious. Still, this "
    "common view may be missing something important. Stories can train a skill that few "
    "textbooks even try to teach. "
    "It is true that practical books are often the fastest road to information. If you want "
    "to learn how to cook rice, a clear guide helps you at once. A textbook gives you names, "
    "dates, and rules in a neat order. Nobody learns math mainly by reading novels. For "
    "gaining facts and skills, practical books usually win. "
    "However, stories can do something that practical books cannot. When we read a story, we "
    "do more than receive information about a character. We step inside that character's "
    "head and live there for a while. We see the world through the eyes of a nervous "
    "student, a tired nurse, or a lonely old man. A textbook tells us about people; a story "
    "lets us be another person for a moment. "
    "Think about what actually happens as we turn the pages. When the hero faces a hard "
    "choice, we feel her fear and hesitate with her. When she hurts a friend without meaning "
    "to, we feel sorry and ask what we would have done. Reading a novel is, in a sense, "
    "trying on another person's life, like a piece of clothing. In other words, fiction "
    "gives us safe chances to practice feeling, judging, and choosing as somebody else. "
    "This practice matters because everyday life keeps demanding the same skill. A friend "
    "suddenly stops talking to you; a customer looks upset for no clear reason. In such "
    "moments, we must imagine feelings that we cannot see directly. Research suggests that "
    "people who read fiction regularly tend to be better at guessing what others think and "
    "feel. Because stories make us repeat this guessing, they quietly build a base for "
    "friendship and for work. "
    "Some people still say that readers of novels are running away from the real world. The "
    "truth is closer to the opposite. Reading stories is not an escape from real life but "
    "practice for it. Every hour spent inside another person's story trains the imagination "
    "we need when we face real people. "
    "Of course, none of this means that practical books are unnecessary. We still need "
    "textbooks for facts and guides for skills, and stories cannot replace them. The two "
    "kinds of books are not rivals; they simply do different jobs. One fills our heads with "
    "knowledge, and the other stretches our hearts toward other people. A good reader keeps "
    "a place on the shelf for both."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Therefore &nbsp; ② For example &nbsp; ③ In addition &nbsp; ④ Still",
         "【 B 】 &nbsp; ① As a result &nbsp; ② However &nbsp; ③ For instance &nbsp; ④ Similarly",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(2) <span class='en'>Reading stories is not an escape from real life but "
             "practice for it.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) について、小説を読むことが「服のように他人の人生を試着すること（<span "
             "class='en'>trying on another person's life</span>）」だとはどういうことか。本文に即して"
             "日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で紹介されている研究の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 物語をよく読む人は、他人が考えたり感じたりしていることを推測するのが得意な傾向がある。",
         "② 物語をよく読む人は、実用書をよく読む人よりも多くの知識を身につけている傾向がある。",
         "③ 物語をよく読む人は、現実の世界での人づきあいをしだいに避けるようになる傾向がある。",
         "④ 物語をよく読む人は、登場人物への共感に流されて、冷静な判断を誤りやすい傾向がある。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>they simply do different jobs</span> について、実用書（教科書・"
             "手引書）と物語それぞれの「仕事」とは何か。本文全体をふまえ、日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 実用書は情報を得るには速いが内容が浅いため、深く学びたい人はまず物語から読書を始めるべきである。",
         "② 物語は本来楽しむためのものなのだから、役に立つかどうかという基準で読書の価値を測るべきではない。",
         "③ 物語を読むことは結局は現実からの逃避なので、他人を理解したければ実際に人と会って話す方がよい。",
         "④ 物語は他人の頭の中を生きる練習として現実で効く力を育てるものであり、実用書とは役割が違うだけだ。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 事実や技能を身につけるという点でも、実用書より物語の方が役に立つ、と筆者は述べている。",
         "② 物語を読むとき、読者は登場人物の頭の中に入り、その人物として世界を見て生きる体験をする。",
         "③ フィクションをよく読む人は他人の考えや気持ちの推測が得意な傾向がある、という研究がある。",
         "④ 物語の中で過ごす時間は、現実の生活には決して役立たない、と筆者は考えている。",
         "⑤ 筆者は、物語さえあれば教科書や実用書はもはや一切不要になる、と主張している。",
         "⑥ 実用書と物語は競争相手ではなく、それぞれ異なる仕事をしている、と筆者は考えている。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ④ Still　　B ＝ ② However",
     "exp": "A：「物語＝時間つぶし・まじめな勉強の邪魔」という通念に対し、「この見方は重要なことを"
            "見落としているかもしれない」と<b>反転</b>する流れ。逆接 → Still（それでも）。"
            "Therefore（因果）・For example（例示）・In addition（追加）は不可。<br>"
            "B：第2段「確かに実用書は情報への最短の道（＝譲歩）」に対し、第3段は「だが物語には実用書に"
            "できないことがある」と主張へ<b>転換</b>する。逆接 → However。As a result（因果）・"
            "For instance（例示）・Similarly（類比）は流れに合わない。 "
            "〔<b>解法ルール R7</b>／<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "①",
     "exp": "第5段「Research suggests that people who read fiction regularly tend to be better "
            "at guessing what others think and feel」＝フィクションを定期的に読む人は、他人の考えや"
            "気持ちを推測するのがより得意な傾向がある。②「知識の量」の比較は本文にない。③は本文と逆"
            "（物語は友人関係や仕事の<i>土台を築く</i>・第5段）。④「判断を誤りやすい」も本文にない。 "
            "〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "④",
     "exp": "第6段「Reading stories is not an escape from real life but practice for it」＋"
            "第7段「they simply do different jobs」と一致。①は第2段「事実や技能を得る点では実用書が"
            "たいてい勝つ」に反し、「まず物語から」も本文にない。②は本文と逆（筆者はまさに物語の"
            "「役に立つ」働きを論じている・第1段最終文）。③は第6段「真実はその正反対に近い」に反する。 "
            "〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "②・③・⑥",
     "exp": "①×：第2段最終文「For gaining facts and skills, practical books usually win（事実や"
            "技能の点では実用書が勝つ）」に反する。④×：第6段の下線部(2)「現実のための練習」に真っ向から"
            "反する——「決して役立たない」は<b>言い過ぎ</b>。⑤×：第7段第1文「none of this means that "
            "practical books are unnecessary（実用書が不要という意味ではない）」で明確に否定——"
            "「一切不要」も<b>言い過ぎ</b>。 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(2)和訳",
     "model": "物語を読むことは、現実の生活からの逃避ではなく、現実の生活のための練習なのである。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「AではなくB」の対比を構文どおり訳出"
               "〔<b>読解ルール R3</b>〕／②an escape from real life＝「現実（の生活）からの逃避」／"
               "③practice for it の <b>it＝real life</b> を受けて「現実（の生活）のための練習」と訳す"
               "〔<b>読解ルール R5</b>〕。動名詞 Reading stories＝主語（「物語を読むことは」）。"},
    {"no": "問3", "pts": "8点・記述",
     "model": "小説を読むことは、服を試着するように、しばらくの間、自分ではない他人の人生を安全に"
              "体験してみることだ、ということ。すなわち、登場人物の頭の中に入り、その人物として感じ、"
              "判断し、選ぶ練習を、現実の危険なしに行えるということ。",
     "points": "▶<b>採点要素</b>：①「試着」＝<b>一時的に・気軽に身につけてみる</b>→「つかの間、別の"
               "人間として生きてみる」（第3段）を反映／②直後の言い換え「In other words, fiction gives "
               "us safe chances to practice feeling, judging, and choosing as somebody else」（第4段）"
               "から〈感じ・判断し・選ぶ練習〉を補う〔<b>読解ルール R18</b>／<b>解法ルール R8</b>〕／"
               "③「安全に（現実の危険なしに）」のニュアンス。"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①実用書・教科書の仕事は、事実や技能などの知識を速く整った形で与え、私たちの頭を知識で"
              "満たすこと。②物語の仕事は、登場人物として他人の頭の中を生きる練習をさせ、見えない気持ちを"
              "想像する力を育てて、私たちの心を他人へと向けて伸ばすこと。",
     "points": "▶<b>採点要素</b>：第7段「One fills our heads with knowledge, and the other stretches "
               "our hearts toward other people」の対比を軸に、①<b>実用書＝知識</b>（第2段：情報への"
               "最短の道）／②<b>物語＝他人を想像する力の練習</b>（第3〜5段）を本文から補って説明。"
               "各5点。 〔<b>読解ルール R5</b>：different jobs の中身を確定／<b>解法ルール R8</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（Still→通念の反転）、空所B（However→第3段の主張転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that practical books are often the fastest road …」→ 第3段 However で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(2) not an escape from real life but practice for it、第7段 not rivals。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第3段の生徒・看護師・老人、第4段の読書の場面、第5段の友人・客——すべて「他人の頭の中を生きる練習」の例。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "This practice（第5段）＝第4段の〈感じ・判断し・選ぶ練習〉、practice for it の it＝real life、different jobs の中身。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第5段 because everyday life keeps demanding … ／ Because stories make us repeat this guessing …。"),
        ("R18", "比喩・たとえ話は、直前直後の主張の言い換えとして読む（比喩だけで終わらせない）", "★★★",
         "第4段「服の試着」の比喩＝下線部(1)。直後の In other words … が比喩の中身を確定する（問3）。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。In other words・one … the other … の言い換え・対比を利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。④「決して役立たない」・⑤「一切不要」は典型的な言い過ぎの引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "a skill <that few textbooks even try to teach>、feelings <that we cannot see directly>、"
         "Every hour <spent inside another person's story> 型。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「物語＝楽しい時間つぶし。役に立つのは教科書・実用書」を提示。→ <b>Still（R1）</b>："
             "この見方は重要なことを見落としている——物語は教科書が教えない技能を鍛える。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに実用書は情報への最短の道。事実や技能を得る点では"
             "たいてい実用書が勝つ。＝通念の一部は認める。"},
    {"arrow": "◀ However 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "だが物語には実用書にできないことがある——登場人物の頭の中に入り、<b>つかの間、別の人間として"
             "生きる</b>こと。教科書は人々「について」語り、物語は人に「なる」ことをさせる。"},
    {"arrow": "↓　具体化（R4）"},
    {"role": "理由①（具体化）", "para": "¶4", "kind": "reason",
     "text": "読書の実際：主人公と共に恐れ、ためらい、「自分ならどうしたか」と自問する。＝<b>他人の人生の"
             "「試着」（R18・比喩）</b>→ 直後に言い換え：<b>感じ・判断し・選ぶ練習の安全な機会</b>。"},
    {"arrow": "↓　理由②（R6 因果）"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "その練習は<b>現実で効く</b>：日常は「見えない気持ちの想像」を絶えず要求する（友人・客の例）。"
             "フィクションをよく読む人は他人の心の推測が得意な傾向（研究）→ 友人関係・仕事の土台。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "「読者は現実逃避」という声への反転：<b>not an escape from real life but practice for it"
             "（R3）</b>＝物語は現実からの逃避ではなく、現実のための練習。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：実用書が不要という話ではない。二種類の本は<b>競争相手ではなく役割が違う</b>"
             "——一方は頭を知識で満たし、他方は心を他人へ伸ばす。棚には両方の場所を。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 二種類の本、二つの仕事",
     "caption": "実用書・教科書は<b>知識を速く整った形で</b>与え（第2段）、物語は<b>他人の頭の中を生きる"
                "体験</b>を与える（第3段）。どちらが上かではなく、<b>届く場所（頭と心）が違う</b>。",
     "para": "→ 第2・3・7段"},
    {"id": "fig2", "title": "図2 ｜ 物語がくれる「練習」の中身",
     "caption": "①ページの中で<b>登場人物として感じ・迷い・選ぶ</b>（第4段）＝他人の人生の安全な「試着」。"
                "②その繰り返しが<b>見えない気持ちを想像する力</b>を育て、友人関係や仕事の土台になる（第5段）。",
     "para": "→ 第4〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 逃避ではなく、現実のための練習",
     "caption": "通念「物語＝現実からの逃避・娯楽にすぎない」に対し、筆者は<b>not an escape but "
                "practice</b>＝「現実のための練習」と反転する。実用書とは競争相手ではなく、役割が違うだけ。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "多くの人は、物語を読むことは時間をつぶす楽しい方法にすぎない、と信じている。小説は楽しいが、"
        "実際に役立つことは何も教えてくれない、と彼らは言う。役に立つ知識が欲しいなら、代わりに教科書か"
        "実用的な手引書を手に取るべきだ、と。親はしばしば子どもに、小説を置いて何かまじめなものを勉強"
        "しなさい、と言う。<b>それでも</b>、このよくある見方は、何か重要なことを見落としているのかも"
        "しれない。物語は、ほとんどの教科書が教えようとさえしない技能を、鍛えることができるのだ。"),
    (2, "確かに、実用書はしばしば情報への最短の道である。米の炊き方を学びたいなら、わかりやすい手引書が"
        "すぐに助けてくれる。教科書は、名前や年代や規則を整った順序で与えてくれる。主に小説を読むことで"
        "数学を学ぶ人などいない。事実や技能を得るという点では、たいてい実用書が勝つのだ。"),
    (3, "<b>しかし</b>、物語には、実用書にはできないことができる。物語を読むとき、私たちは登場人物に"
        "ついての情報を受け取る以上のことをしている。私たちはその人物の頭の中に足を踏み入れ、しばらく"
        "そこで生きるのだ。不安な生徒、疲れた看護師、あるいは孤独な老人の目を通して、世界を見る。教科書は"
        "人々について語ってくれるが、物語は、つかの間、私たちを別の人間にしてくれるのである。"),
    (4, "ページをめくるとき、実際に何が起きているかを考えてみよう。主人公が難しい選択に直面すると、"
        "私たちは彼女の恐れを感じ、彼女と共にためらう。彼女が心ならずも友人を傷つけると、私たちは申し訳"
        "なく思い、自分ならどうしただろうかと自問する。<b>小説を読むことは、ある意味で、一着の服のように、"
        "他人の人生を試着してみることなのだ。</b>言い換えれば、フィクションは、自分ではない誰かとして"
        "感じ、判断し、選ぶ練習をする安全な機会を、私たちに与えてくれるのである。"),
    (5, "この練習が重要なのは、日常生活が同じ技能を絶えず要求してくるからだ。友人が突然、口をきいて"
        "くれなくなる。客が、はっきりした理由もなく腹を立てているように見える。そのような瞬間、私たちは"
        "直接には見えない気持ちを想像しなければならない。研究の示唆するところでは、フィクションを定期的に"
        "読む人は、他人が考え感じていることを推測するのがより得意な傾向がある。物語は私たちにこの推測を"
        "何度も繰り返させるからこそ、友人関係と仕事のための土台を、静かに築いてくれるのである。"),
    (6, "小説の読者は現実の世界から逃げているのだ、といまだに言う人もいる。真実は、その正反対に近い。"
        "<b>物語を読むことは、現実の生活からの逃避ではなく、現実の生活のための練習なのである。</b>"
        "他人の物語の中で過ごす一時間一時間が、現実の人間と向き合うときに必要な想像力を鍛えているのだ。"),
    (7, "もちろん、以上のことは、実用書が不要だという意味ではない。私たちには相変わらず、事実のための"
        "教科書と技能のための手引書が必要であり、物語がそれらに取って代わることはできない。<b>この二種類の"
        "本は競争相手ではない。ただ、異なる仕事をしているだけなのだ。</b>一方は私たちの頭を知識で満たし、"
        "他方は私たちの心を他人へと向けて伸ばしてくれる。よい読者は、その両方のために棚の場所を取って"
        "おくものだ。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("pass the time", "時間をつぶす"),
    ("practical", "実用的な"),
    ("pick up ~", "〜を手に取る"),
    ("put down ~", "〜を（下に）置く"),
    ("miss", "〜を見落とす、見逃す"),
    ("train", "（能力などを）鍛える"),
    ("at once", "すぐに、直ちに"),
    ("gain", "〜を得る、獲得する"),
    ("step inside ~", "〜の中に足を踏み入れる"),
    ("through the eyes of ~", "〜の目を通して"),
    ("for a moment", "つかの間、少しの間"),
    ("face", "〜に直面する、〜と向き合う"),
    ("hesitate", "ためらう"),
    ("without meaning to", "そのつもりなく、心ならずも"),
    ("try on ~", "〜を試着する"),
    ("in other words", "言い換えれば"),
    ("matter", "重要である"),
    ("upset", "腹を立てた、動揺した"),
    ("regularly", "定期的に、日頃から"),
    ("run away from ~", "〜から逃げる"),
    ("escape from ~", "〜からの逃避"),
    ("replace", "〜に取って代わる"),
    ("rival", "競争相手、ライバル"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：通念「物語＝時間つぶし」と、その反転（Still）",
  "sentences": [
    {"chunks": [("S","Many people","多くの人は"),("V","believe","信じている"),
                ("O","[that reading stories is just a pleasant way &lt;to pass the time&gt;].","物語を読むことは、時間をつぶす楽しい方法にすぎない、と")],
     "note":"▶ believe that …＝名詞節。節内の主語は動名詞 reading stories。to pass the time＝way を修飾する不定詞（形容詞的用法）。"},
    {"chunks": [("S","Novels","小説は"),("V","are","である"),("C","fun,","楽しいもの"),
                ("M","they say,","と彼らは言う"),("接","but","しかし"),
                ("S","they","それは"),("V","do not really teach","実際には教えてくれない"),
                ("O","us","私たちに"),("O","anything useful.","役に立つことを何も")],
     "note":"▶ they say＝挿入。<b>teach O1 O2</b>（第4文型）。anything <b>useful</b>＝-thing 語は形容詞を後ろに置く。"},
    {"chunks": [("M","(If you want useful knowledge),","役に立つ知識が欲しいなら"),
                ("S","you","あなたは"),("V","should pick up","手に取るべきだ"),
                ("O","a textbook or a practical guide","教科書か実用的な手引書を"),("M","instead.","代わりに")],
     "note":"▶ If 節＝副詞節（条件）。pick up＝句動詞「手に取る」。instead＝「（小説の）代わりに」。ここまでが通念の中身。"},
    {"chunks": [("S","Parents","親は"),("M","often","しばしば"),("V","tell","言う"),
                ("O","their children","子どもに"),
                ("C","to put down novels and study something serious.","小説を置いて、何かまじめなものを勉強しなさいと")],
     "note":"▶ <b>tell O to do</b>（第5文型）。put down と study が and で並列（どちらも to につながる）。"},
    {"chunks": [("接","Still,","それでも"),("S","this common view","このよくある見方は"),
                ("V","may be missing","見落としているのかもしれない"),("O","something important.","何か重要なことを")],
     "note":"▶ <b>R1｜逆接 Still の直後が筆者の主張</b>（＝空所A）。may be -ing＝「〜しているのかもしれない」。something <b>important</b>＝形容詞後置。"},
    {"chunks": [("S","Stories","物語は"),("V","can train","鍛えることができる"),
                ("O","a skill &lt;that few textbooks even try to teach&gt;.","ほとんどの教科書が教えようとさえしない技能を")],
     "note":"▶ <b>R11｜関係代名詞 that</b> のカタマリが a skill を後ろから説明。<b>few</b>＝「ほとんど〜ない」（準否定）。この「技能」の中身が本文の主題。"},
  ]},
 {"head": "第2段 — 譲歩：確かに実用書は速い（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当"),
                ("-","[that practical books are often the fastest road to information].","実用書がしばしば情報への最短の道であることは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。形式主語 It＝真主語 that 節。第3段の However（反転）の前振り。"},
    {"chunks": [("M","(If you want to learn how to cook rice),","米の炊き方を学びたいなら"),
                ("S","a clear guide","わかりやすい手引書が"),("V","helps","助けてくれる"),
                ("O","you","あなたを"),("M","at once.","すぐに")],
     "note":"▶ <b>how to do</b>＝「〜のしかた」（learn の目的語）。If 節＝副詞節。"},
    {"chunks": [("S","A textbook","教科書は"),("V","gives","与える"),("O","you","あなたに"),
                ("O","names, dates, and rules","名前・年代・規則を"),("M","(in a neat order).","整った順序で")],
     "note":"▶ <b>give O1 O2</b>（第4文型）。O2 は三つの名詞の並列。"},
    {"chunks": [("S","Nobody","誰も〜ない"),("V","learns","学ばない"),("O","math","数学を"),
                ("M","(mainly by reading novels).","主に小説を読むことによっては")],
     "note":"▶ Nobody＝否定の主語（「誰も…ない」と訳し下ろす）。by -ing＝手段「〜することによって」。"},
    {"chunks": [("M","(For gaining facts and skills),","事実や技能を得るという点では"),
                ("S","practical books","実用書が"),("M","usually","たいてい"),("V","win.","勝つ")],
     "note":"▶ 譲歩の締め。<b>R9注意</b>：問7①「実用書より物語の方が役に立つ」はこの文で×。"},
  ]},
 {"head": "第3段 — 主張の転換：物語は「他人の頭の中を生きる」（However）",
  "sentences": [
    {"chunks": [("接","However,","しかし"),("S","stories","物語は"),("V","can do","することができる"),
                ("O","something &lt;that practical books cannot&gt;.","実用書にはできないことを")],
     "note":"▶ <b>R1｜However＝逆接でここが主張転換点</b>（＝空所B）。that … cannot (do)＝関係代名詞・文末の do は省略。〔R11〕"},
    {"chunks": [("M","(When we read a story),","物語を読むとき"),("S","we","私たちは"),
                ("V","do","する"),("O","more than receive information about a character.","登場人物についての情報を受け取る以上のことを")],
     "note":"▶ <b>more than do</b>＝「〜する以上のこと（をする）」。When 節＝副詞節。"},
    {"chunks": [("S","We","私たちは"),("V","step","足を踏み入れる"),
                ("M","(inside that character's head)","その人物の頭の中に"),("接","and","そして"),
                ("V","live","生きる"),("M","there (for a while).","しばらくそこで")],
     "note":"▶ 一つの主語 We が step と live の二つの動詞を取る。「他人の頭の中を生きる」＝本文のキーイメージ。"},
    {"chunks": [("S","We","私たちは"),("V","see","見る"),("O","the world","世界を"),
                ("M","(through the eyes of a nervous student, a tired nurse, or a lonely old man).","不安な生徒・疲れた看護師・孤独な老人の目を通して")],
     "note":"▶ <b>R4｜抽象→具体</b>：「別の人間として生きる」の具体例が三つ並ぶ。through the eyes of ~＝「〜の目を通して」。"},
    {"chunks": [("S","A textbook","教科書は"),("V","tells","語る"),("O","us","私たちに"),
                ("M","(about people);","人々について"),("S","a story","物語は"),("V","lets","させてくれる"),
                ("O","us","私たちを"),("C","be another person","別の人間でいるように"),
                ("M","(for a moment).","つかの間")],
     "note":"▶ セミコロン（;）で二文を並置し<b>対比</b>：tells us <i>about</i>（〜について語る）vs <b>lets us be</b>（〜にならせる）。let O do＝使役。"},
  ]},
 {"head": "第4段 — 具体化：感じ、迷い、選ぶ——人生の「試着」",
  "sentences": [
    {"chunks": [("V","Think about","考えてみよう"),
                ("O","[what actually happens (as we turn the pages)].","ページをめくるとき実際に何が起きているかを")],
     "note":"▶ 命令文。what 節＝名詞節（about の目的語）。as＝「〜するとき」（副詞節）。"},
    {"chunks": [("M","(When the hero faces a hard choice),","主人公が難しい選択に直面すると"),
                ("S","we","私たちは"),("V","feel","感じる"),("O","her fear","彼女の恐れを"),
                ("接","and","そして"),("V","hesitate","ためらう"),("M","(with her).","彼女と共に")],
     "note":"▶ <b>R4｜具体化</b>：読書中に起きることの実況。feel と hesitate が並列。"},
    {"chunks": [("M","(When she hurts a friend without meaning to),","彼女が心ならずも友人を傷つけると"),
                ("S","we","私たちは"),("V","feel","感じ"),("C","sorry","申し訳なく"),
                ("接","and","そして"),("V","ask","自問する"),
                ("O","[what we would have done].","自分ならどうしただろうかと")],
     "note":"▶ without meaning to (do)＝「そのつもりなく」（to の後の hurt が省略）。<b>would have done</b>＝仮定法過去完了「（もし自分だったら）どうしていただろうか」。"},
    {"chunks": [("S","Reading a novel","小説を読むことは"),("V","is,","である"),
                ("M","in a sense,","ある意味で"),
                ("C","trying on another person's life,","他人の人生を試着すること"),
                ("M","like a piece of clothing.","一着の服のように")],
     "note":"▶ <b>R18｜比喩は直前直後の言い換えで意味を確定</b>。動名詞 Reading＝主語、trying on＝補語。＝<b>下線部(1)＝問3</b>。中身は次の文（In other words）が確定する。"},
    {"chunks": [("接","In other words,","言い換えれば"),("S","fiction","フィクションは"),
                ("V","gives","与えてくれる"),("O","us","私たちに"),
                ("O","safe chances &lt;to practice feeling, judging, and choosing (as somebody else)&gt;.","別の誰かとして感じ・判断し・選ぶ練習をする安全な機会を")],
     "note":"▶ <b>R8｜In other words＝直前の比喩のイコール言い換え</b>。to practice …＝chances を修飾する不定詞。三つの動名詞（feeling / judging / choosing）が並列。〔R11〕"},
  ]},
 {"head": "第5段 — 理由②：その練習は現実で効く（因果）",
  "sentences": [
    {"chunks": [("S","This practice","この練習は"),("V","matters","重要である"),
                ("M","(because everyday life keeps demanding the same skill).","日常生活が同じ技能を絶えず要求してくるから")],
     "note":"▶ <b>R6｜because＝因果</b>。<b>R5｜This practice</b>＝第4段の〈感じ・判断し・選ぶ練習〉。matter＝「重要である」（自動詞）。keep -ing＝「〜し続ける」。"},
    {"chunks": [("S","A friend","友人が"),("M","suddenly","突然"),("V","stops","やめる"),
                ("O","talking (to you);","あなたと口をきくのを"),
                ("S","a customer","客が"),("V","looks","見える"),("C","upset","腹を立てているように"),
                ("M","(for no clear reason).","はっきりした理由もなく")],
     "note":"▶ <b>R4｜具体例</b>が二つ、セミコロンで並置。stop -ing＝「〜するのをやめる」。look C＝「Cに見える」。"},
    {"chunks": [("M","(In such moments),","そのような瞬間には"),("S","we","私たちは"),
                ("V","must imagine","想像しなければならない"),
                ("O","feelings &lt;that we cannot see directly&gt;.","直接には見えない気持ちを")],
     "note":"▶ <b>R11｜関係代名詞 that</b> が feelings を後ろから説明（see の目的語が欠けた不完全文）。"},
    {"chunks": [("S","Research","研究は"),("V","suggests","示唆している"),
                ("O","[that people &lt;who read fiction regularly&gt; tend to be better at guessing what others think and feel].","フィクションを定期的に読む人は、他人が考え感じていることを推測するのがより得意な傾向がある、と")],
     "note":"▶ that 節の中：主語 people を関係詞節 who … が修飾〔R11〕。be good at -ing の比較級 better at guessing。what others think and feel＝guessing の目的語（名詞節）。問4①・問7③の根拠。"},
    {"chunks": [("M","(Because stories make us repeat this guessing),","物語は私たちにこの推測を繰り返させるので"),
                ("S","they","それは"),("M","quietly","静かに"),("V","build","築く"),
                ("O","a base for friendship and for work.","友人関係と仕事のための土台を")],
     "note":"▶ <b>R6｜Because＝因果</b>。<b>make O do</b>＝使役「Oに〜させる」。this guessing＝前文の「見えない気持ちの推測」〔R5〕。"},
  ]},
 {"head": "第6段 — 核心：逃避ではなく、現実のための練習（not A but B）",
  "sentences": [
    {"chunks": [("S","Some people","一部の人は"),("M","still","いまだに"),("V","say","言う"),
                ("O","[that readers of novels are running away from the real world].","小説の読者は現実の世界から逃げているのだと")],
     "note":"▶ 反対意見の提示（この直後に筆者が反転する）。run away from ~＝「〜から逃げる」。"},
    {"chunks": [("S","The truth","真実は"),("V","is","である"),
                ("C","closer to the opposite.","その正反対に近いもの")],
     "note":"▶ 短い一文で反転を宣言。次の文が本文の<b>核心</b>。close to ~ の比較級。"},
    {"chunks": [("S","Reading stories","物語を読むことは"),("V","is","である"),
                ("C","not an escape from real life but practice for it.","現実の生活からの逃避ではなく、現実の生活のための練習")],
     "note":"▶ <b>R3｜not A but B＝Bの側が核心</b>。it＝real life〔R5〕。＝<b>下線部(2)＝問2</b>。動名詞 Reading stories＝主語。"},
    {"chunks": [("S","Every hour &lt;spent inside another person's story&gt;","他人の物語の中で過ごされる一時間一時間が"),
                ("V","trains","鍛える"),
                ("O","the imagination &lt;(that) we need (when we face real people)&gt;.","現実の人間と向き合うときに必要な想像力を")],
     "note":"▶ <b>R11｜過去分詞 spent … が hour を、関係代名詞省略 (that) we need が imagination を後ろから説明</b>。when 節＝副詞節。核心の言い換え・補強。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：二つの本は競争相手ではなく役割が違う",
  "sentences": [
    {"chunks": [("M","Of course,","もちろん"),("S","none of this","以上のどれも"),
                ("V","means","意味しない"),
                ("O","[that practical books are unnecessary].","実用書が不要だとは")],
     "note":"▶ 譲歩つき結論の型。<b>R9注意</b>：問7⑤「実用書は一切不要」はこの文で明確に×。none of ~＝全否定。"},
    {"chunks": [("S","We","私たちは"),("M","still","相変わらず"),("V","need","必要とする"),
                ("O","textbooks for facts and guides for skills,","事実のための教科書と、技能のための手引書を"),
                ("接","and","そして"),("S","stories","物語は"),("V","cannot replace","取って代わることはできない"),
                ("O","them.","それらに")],
     "note":"▶ A for B（〜のためのA）が二組並列。them＝textbooks and guides〔R5〕。"},
    {"chunks": [("S","The two kinds of books","二種類の本は"),("V","are","である"),
                ("C","not rivals;","競争相手ではない"),
                ("S","they","それらは"),("M","simply","ただ"),("V","do","している"),
                ("O","different jobs.","異なる仕事を")],
     "note":"▶ <b>R3｜not A（rivals）の否定→直後に正しい関係（different jobs）を言い直す</b>。＝<b>下線部(3)＝問5</b>。「異なる仕事」の中身は次の文が具体化する。"},
    {"chunks": [("S","One","一方（実用書）は"),("V","fills","満たし"),("O","our heads","私たちの頭を"),
                ("M","(with knowledge),","知識で"),("接","and","そして"),
                ("S","the other","他方（物語）は"),("V","stretches","伸ばす"),("O","our hearts","私たちの心を"),
                ("M","(toward other people).","他人へ向けて")],
     "note":"▶ <b>one … the other …</b>＝「（二つのうち）一方は…他方は…」。<b>fill A with B</b>＝「AをBで満たす」。頭（知識）と心（想像力）の対比＝問5の解答の核。"},
    {"chunks": [("S","A good reader","よい読者は"),("V","keeps","取っておく"),
                ("O","a place on the shelf","棚の場所を"),("M","(for both).","両方のために")],
     "note":"▶ both＝実用書と物語。締めの一文：どちらか一方を選ぶ話ではない、という結論の言い換え。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=6文/第2段=5文/第3段=5文/第4段=5文/第5段=5文/第6段=4文/第7段=5文)
SVOC_LOGIC = {
    (1, 5): "対比", (1, 6): "主張",              # s5 Still→反転 / s6 教科書が教えない技能
    (2, 1): "譲歩", (2, 5): "譲歩",              # s1 It is true / s5 実用書が勝つ(譲歩の締め)
    (3, 1): "対比", (3, 3): "主張", (3, 4): "具体例", (3, 5): "対比",
    (4, 1): "具体例", (4, 2): "具体例", (4, 3): "具体例", (4, 4): "主張", (4, 5): "主張",
    (5, 1): "因果", (5, 2): "具体例", (5, 4): "具体例", (5, 5): "因果",
    (6, 1): "譲歩", (6, 2): "対比", (6, 3): "主張", (6, 4): "主張",
    (7, 1): "譲歩", (7, 2): "譲歩", (7, 3): "主張", (7, 4): "具体例", (7, 5): "主張",
}
