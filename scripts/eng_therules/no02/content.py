# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.02 — 単一ソース
テーマ: Why Learn a Language When Machines Can Translate? (機械翻訳の時代に、なぜ外国語を学ぶのか) / MARCH・難関私大 (The Rules 2〜3 相当)
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "02",
    "level": "MARCH レベル",
    "level_sub": "難関私大 / The Rules 2〜3 相当",
    "theme_ja": "機械翻訳の時代に、なぜ外国語を学ぶのか",
    "theme_en": "Why Learn a Language When Machines Can Translate?",
    "minutes": 18,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Open a translation app, point your phone at a menu in a foreign city, and the words '
        'rearrange themselves into your own language within seconds. Such tools are now so quick '
        'and so cheap that many people ask an obvious question: why spend years struggling with '
        'vocabulary and grammar when a machine can do the job in an instant? Learning a foreign '
        'language, they conclude, is a waste of time. <span class="blank">【&nbsp;A&nbsp;】</span>, '
        'this conclusion, reasonable as it sounds, rests on a narrow idea of what language is for.'),
    (2, 'It is true that machines have become remarkably good at practical translation. For a '
        'tourist reading a sign, a traveler ordering dinner, or a company preparing an instruction '
        'manual, translation software is often faster and more accurate than most human learners '
        'will ever be. Research suggests that for routine, factual texts the gap between machines '
        'and professionals keeps narrowing. If the only purpose of language were to move '
        'information from head to head, the argument against learning would be hard to resist.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, moving information is not the only thing a '
        'language does. When we treat words as mere containers for facts, we forget that every '
        'language is also a record of how a community has lived and thought. The value of '
        'learning one, therefore, cannot be measured by translation alone. A machine delivers '
        'the content of a message; a learner slowly gains something that no software even '
        'attempts to offer.'),
    (4, 'Consider how differently languages carve up the world. One language may need several '
        'words where another is content with one, and a color basic in one tongue may have no '
        'name in the next. Systems of polite speech oblige speakers to notice rank and closeness '
        'every time they speak, and even a simple greeting may ask about the weather in one '
        'country and about whether you have eaten in another. <u>To learn a language, in other '
        'words, is to borrow another community\'s way of noticing the world.<sup>(1)</sup></u> '
        'The learner gains not just new labels for old things but new things to see.'),
    (5, 'The process of learning matters as much as the result. Why should anyone struggle to '
        'speak badly what a machine can render perfectly? Because the struggle itself carries a '
        'message. When you greet people in their own language, however clumsily, you show them '
        'that they were worth your effort, and such respect opens doors no app can unlock. At '
        'the same time, wrestling with a foreign grammar lets you see your mother tongue from '
        'the outside, as one way of speaking among many rather than the natural voice of reality.'),
    (6, 'Here, then, is the heart of the matter. <u>What a foreign language gives us is not so '
        'much a means of exchanging information as a new pair of eyes and a new way of standing '
        'beside other people.<sup>(2)</sup></u> Translation moves messages; learning moves the '
        'learner. A machine can tell you what was said, but it cannot make you the kind of '
        'person who sees why it was said that way, or who earns trust by trying to understand.'),
    (7, 'None of this is a call to throw away translation software, which removes barriers and '
        'saves time when used well. The point is not that machines translate badly, but that '
        'translation was never the whole of language. Now that information travels by itself, '
        '<u>the reasons to learn a foreign language have, if anything, increased<sup>(3)</sup></u>. '
        'What remains for us is precisely the part of language that no machine can carry.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Open a translation app, point your phone at a menu in a foreign city, and the words "
    "rearrange themselves into your own language within seconds. Such tools are now so quick and "
    "so cheap that many people ask an obvious question: why spend years struggling with "
    "vocabulary and grammar when a machine can do the job in an instant? Learning a foreign "
    "language, they conclude, is a waste of time. Nevertheless, this conclusion, reasonable as "
    "it sounds, rests on a narrow idea of what language is for. "
    "It is true that machines have become remarkably good at practical translation. For a "
    "tourist reading a sign, a traveler ordering dinner, or a company preparing an instruction "
    "manual, translation software is often faster and more accurate than most human learners "
    "will ever be. Research suggests that for routine, factual texts the gap between machines "
    "and professionals keeps narrowing. If the only purpose of language were to move information "
    "from head to head, the argument against learning would be hard to resist. "
    "Still, moving information is not the only thing a language does. When we treat words as "
    "mere containers for facts, we forget that every language is also a record of how a "
    "community has lived and thought. The value of learning one, therefore, cannot be measured "
    "by translation alone. A machine delivers the content of a message; a learner slowly gains "
    "something that no software even attempts to offer. "
    "Consider how differently languages carve up the world. One language may need several words "
    "where another is content with one, and a color basic in one tongue may have no name in the "
    "next. Systems of polite speech oblige speakers to notice rank and closeness every time they "
    "speak, and even a simple greeting may ask about the weather in one country and about "
    "whether you have eaten in another. To learn a language, in other words, is to borrow "
    "another community's way of noticing the world. The learner gains not just new labels for "
    "old things but new things to see. "
    "The process of learning matters as much as the result. Why should anyone struggle to speak "
    "badly what a machine can render perfectly? Because the struggle itself carries a message. "
    "When you greet people in their own language, however clumsily, you show them that they "
    "were worth your effort, and such respect opens doors no app can unlock. At the same time, "
    "wrestling with a foreign grammar lets you see your mother tongue from the outside, as one "
    "way of speaking among many rather than the natural voice of reality. "
    "Here, then, is the heart of the matter. What a foreign language gives us is not so much a "
    "means of exchanging information as a new pair of eyes and a new way of standing beside "
    "other people. Translation moves messages; learning moves the learner. A machine can tell "
    "you what was said, but it cannot make you the kind of person who sees why it was said that "
    "way, or who earns trust by trying to understand. "
    "None of this is a call to throw away translation software, which removes barriers and "
    "saves time when used well. The point is not that machines translate badly, but that "
    "translation was never the whole of language. Now that information travels by itself, the "
    "reasons to learn a foreign language have, if anything, increased. What remains for us is "
    "precisely the part of language that no machine can carry."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Therefore &nbsp; ② For instance &nbsp; ③ In addition &nbsp; ④ Nevertheless",
         "【 B 】 &nbsp; ① Still &nbsp; ② As a result &nbsp; ③ Likewise &nbsp; ④ Otherwise",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(2) <span class='en'>What a foreign language gives us is not so much a means "
             "of exchanging information as a new pair of eyes and a new way of standing beside "
             "other people.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) について、言語を学ぶことが「別の共同体の世界への注意の向け方を借りること"
             "(<span class='en'>to borrow another community's way of noticing the world</span>)」"
             "だとはどういうことか。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "第4段で述べられている「言語ごとの違い」の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 敬語のある言語を話す人は、そうでない言語を話す人よりも礼儀正しい人柄になる。",
         "② どの言語も、基本的な色を表す単語は必ず共通して持っている。",
         "③ 挨拶ひとつをとっても、天気について尋ねる言語もあれば、食事を済ませたかを尋ねる言語もある。",
         "④ 言語の違いは単語の数の違いにすぎず、世界の見え方には影響しない。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>the reasons to learn a foreign language have, if "
             "anything, increased</span> について、筆者が「外国語を学ぶ理由はむしろ増えた」と"
             "考えるのはなぜか。本文全体をふまえ、学習が与えるものを二つ挙げて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 機械翻訳はまだ不正確なので、当面は人間による外国語学習が必要である。",
         "② 外国語学習の目的は、機械よりも速く正確に情報を伝えられるようになることである。",
         "③ 機械翻訳の登場により、外国語をわざわざ学ぶ理由はほとんど失われた。",
         "④ 機械翻訳は道具として活用すればよく、外国語学習には情報伝達を超えた価値（新しい視点・人との関係）があるので、学ぶ理由はむしろ増えた。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 機械翻訳は今や、文学作品を含むあらゆる種類の文章を、人間の専門家より正確に翻訳できる。",
         "② 挨拶や敬語のあり方は言語によって異なり、それぞれの言語は世界への異なる注意の向け方を話者に身につけさせている。",
         "③ 筆者によれば、外国語を下手に話しかけることは相手に失礼な印象を与えるので、避けるべきである。",
         "④ 外国語の文法と格闘することで、母語を「数ある話し方の一つ」として外側から眺められるようになる。",
         "⑤ 筆者は、翻訳ソフトの使用を完全にやめるよう読者に勧めている。",
         "⑥ 情報がひとりでに行き来する時代になったからこそ、外国語を学ぶ理由はむしろ増えた、と筆者は考えている。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ④ Nevertheless　　B ＝ ① Still",
     "exp": "A：直前まで「学習＝時間の無駄」という通念、直後で「この結論は狭い考えに基づく」と"
            "筆者が反論する流れ。<b>逆接</b>でつなぐ → Nevertheless。Therefore（因果）・"
            "For instance（例示）・In addition（追加）は不可。<br>"
            "B：第2段「確かに機械は実用翻訳が得意（＝譲歩）。情報伝達だけが目的なら学習不要論は"
            "強い」に対し、第3段は「それでも、情報を運ぶことだけが言語の仕事ではない」と主張へ"
            "<b>転換</b>する。逆接（それでもなお）→ Still。As a result（因果）・Likewise（類比）・"
            "Otherwise（さもなければ）は流れに合わない。 〔<b>解法ルール R7</b>／<b>読解ルール "
            "R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "③",
     "exp": "第4段「even a simple greeting may ask about the weather in one country and about "
            "whether you have eaten in another」＝挨拶で天気を尋ねる言語も、食事を済ませたかを"
            "尋ねる言語もある。①は言い過ぎ（敬語は上下・親疎に「気づかせる」だけで、人柄までは"
            "述べていない）、②は本文と逆（a color basic in one tongue may have no name）、"
            "④も本文と逆（学習者は new things to see＝新しい見え方を得る）。 〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "④",
     "exp": "第6段「not so much a means of exchanging information as a new pair of eyes and a "
            "new way of standing beside other people」＋第7段「None of this is a call to throw "
            "away translation software」「the reasons … have, if anything, increased」と一致。"
            "①は本文と逆（第2段で機械の速さ・正確さを認めている）。②は下線部(2)の重心（B側＝"
            "視点と関係）に反する。③は第7段と正反対。 〔<b>読解ルール R3</b>／<b>構文ルール "
            "R13</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "②・④・⑥",
     "exp": "①×：第2段が認めるのは実用的な文章（routine, factual texts）での性能——「文学作品を"
            "含む<b>あらゆる</b>文章」は言い過ぎ。③×：第5段「however clumsily … you show them "
            "that they were worth your effort」＝下手でも努力が敬意として伝わる、と逆。"
            "⑤×：第7段「None of this is a call to throw away translation software」で明確に否定"
            "——「<b>完全に</b>やめる」は言い過ぎ。 〔<b>解法ルール R9</b>：言い換えの見抜き＋"
            "「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(2)和訳",
     "model": "外国語が私たちに与えてくれるものは、情報をやり取りするための手段であるというよりも、"
              "むしろ新しい目であり、他の人々のかたわらに立つための新しいあり方なのである。",
     "points": "▶<b>採点要素</b>：①<b>not so much A as B</b>＝「AというよりむしろB」（重心はB）の"
               "構文訳出／②What a foreign language gives us＝関係代名詞 what 節が主語「外国語が"
               "与えてくれるもの」／③a means of exchanging information＝情報交換の手段、a new "
               "pair of eyes ＋ a new way of standing beside other people＝新しい目（視点）と、"
               "人のかたわらに立つ新しいあり方（関係）。 〔<b>構文ルール R13</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "語彙の区切り方や色の名前、敬語、挨拶の仕方が言語ごとに異なることからわかるように、"
              "各言語には「世界のどこに注意を向けるか」という独自の型があり、外国語を学ぶことは、"
              "その言語を話す共同体に固有の、世界への注意の向け方（ものの見方）を自分のものとして"
              "身につけることだ、ということ。",
     "points": "▶<b>採点要素</b>：①前提＝言語ごとに世界の切り取り方が違う（第4段冒頭）／②具体例"
               "（語彙・色名・敬語・挨拶）への言及／③「借りる」＝その共同体のものの見方・注意の"
               "向け方を自分のものにする、の言い換え。直前の <b>in other words</b>（イコール関係）が"
               "ヒント。 〔<b>解法ルール R8</b>／<b>読解ルール R4</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①各言語は世界の切り取り方（注意の向け方）をそれぞれ持っており、外国語を学ぶことは"
              "新しいものの見方・新しい視点を与えてくれるから。②下手でも相手の言語で話そうとする"
              "努力そのものが敬意として伝わって人との関係を開き、さらに母語を数ある話し方の一つと"
              "して外側から眺めさせてくれるなど、学ぶ過程それ自体に価値があるから。（情報の伝達は"
              "機械に任せられる今、機械には運べないこれらの価値こそが学ぶ理由として残り、際立つ。）",
     "points": "▶<b>採点要素</b>：本文の二本柱を対応させる。①<b>視点</b>（第4段：世界の切り取り方"
               "→第6段：a new pair of eyes）／②<b>過程の効用</b>（第5段：努力＝敬意→関係、母語の"
               "相対化）。各5点。「情報伝達は機械で足りる」という前提（第2・7段）に触れていれば"
               "なお良い。 〔<b>解法ルール R8</b>：本文全体の二本柱（第4〜5段）と対応させる〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A・B。第1段（Nevertheless→筆者の反論）、第3段（Still→主張への転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that machines have become remarkably good …」→ 第3段 Still で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "第7段 not that machines translate badly, but that …、第4段 not just new labels but new things to see。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段の色名・敬語・挨拶の例は「言語＝世界の切り取り方」という抽象の具体例。"),
        ("R12", "★NEW 筆者自身の疑問文は「これから答える」という約束——直後の答えが主張", "★★★",
         "第5段 Why should anyone …? → 直後の Because the struggle itself carries a message が筆者の答え＝主張。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。下線部(1)直前の in other words、第4〜5段の二本柱との対応を利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。①の「あらゆる文章」、⑤の「完全にやめる」は典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "the kind of person &lt;who sees …&gt;、doors &lt;no app can unlock&gt;、a tourist &lt;reading a sign&gt; 型。"),
        ("R13", "★NEW not so much A as B ＝「AというよりむしろB」（重心はB）", "★★★",
         "下線部(2)＝問2。a means of exchanging information（A）より a new pair of eyes …（B）に重心。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「高性能な機械翻訳がある今、外国語学習＝時間の無駄」を提示。→ <b>Nevertheless"
             "（R1）</b>：この結論は「言語＝情報伝達」という狭い考えに基づく、と筆者が反論。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに実用翻訳（標識・注文・マニュアル）では機械は"
             "速く正確。情報を運ぶだけが目的なら、学習不要論には抗いがたい。＝通念の一部は認める。"},
    {"arrow": "◀ Still 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "情報を運ぶことだけが言語の仕事ではない。言語は共同体の<b>生き方・考え方の記録</b>でも"
             "あり、学ぶ価値は翻訳だけでは測れない。"},
    {"arrow": "↓　理由①"},
    {"role": "理由①", "para": "¶4", "kind": "reason",
     "text": "<b>言語＝世界の切り取り方</b>：語彙の区切り・色名・敬語・挨拶の違い（<b>抽象→具体"
             "（R4）</b>）。学ぶ＝その共同体の「世界への注意の向け方」を借りること（下線部(1)）。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>学ぶ過程そのものの効用</b>：修辞疑問「なぜ下手に話す苦労を？」→<b>直後に筆者が"
             "答える（R12）</b>＝努力そのものが敬意を伝えて扉を開き、母語を外から見せてくれる。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "<b>not so much A as B（R13）</b>：外国語が与えるのは情報交換の手段というより"
             "<b>「新しい目」と「人のかたわらに立つ新しいあり方」</b>。翻訳はメッセージを動かし、"
             "学習は学ぶ者自身を動かす。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：翻訳ソフトを捨てよという話ではない（<b>not A but B（R3）</b>）。"
             "情報がひとりでに旅する今こそ、<b>学ぶ理由はむしろ増えた</b>——残るのは機械が運べない"
             "言語のあの部分。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ ことばとの二つの関わり方",
     "caption": "同じ「外国語」でも、<b>機械に任せる</b>と届くのは情報だけ、<b>自分で学ぶ</b>と"
                "視点と関係が育つ。実用の場面では機械で十分——だが、学ぶ理由はそこにはない。",
     "para": "→ 第1・2・6段"},
    {"id": "fig2", "title": "図2 ｜ 外国語学習が与える二つのもの",
     "caption": "学習が与えるものは二つ。①<b>世界の切り取り方→新しい視点</b>（第4段）、"
                "②<b>学ぶ過程そのもの→敬意と母語の相対化</b>（第5段）。下線部(3)「学ぶ理由は"
                "むしろ増えた」の中身はこの二つ。",
     "para": "→ 第4〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 翻訳が運ぶのは情報、学習が与えるのは視点と関係",
     "caption": "外国語学習は「時間の無駄」ではない。翻訳は<b>情報</b>を運び、学習は<b>視点と関係</b>を"
                "与える——<b>not so much A as B（R13）</b>。機械は道具として使いつつ、学ぶ理由は"
                "むしろ増えた。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "翻訳アプリを開き、外国の街でメニューにスマートフォンをかざしてみるといい。単語たちは数秒の"
        "うちに、あなた自身の言語へと並び変わる。この種の道具は今やあまりに速く、あまりに安価になった"
        "ので、多くの人が当然の疑問を口にする——機械が一瞬で用を足してくれるのに、なぜ何年も語彙や文法に"
        "苦労するのか、と。外国語を学ぶことは時間の無駄だ、と彼らは結論づける。<b>それにもかかわらず</b>、"
        "この結論は、もっともらしく聞こえはするものの、「言語は何のためにあるのか」についての狭い考えの"
        "上に成り立っている。"),
    (2, "確かに、機械は実用的な翻訳において驚くほど有能になった。標識を読もうとする観光客、夕食を注文"
        "する旅行者、取扱説明書を用意する会社にとって、翻訳ソフトは、たいていの人間の学習者が到達し得る"
        "水準よりも、しばしば速く、正確である。研究の示唆するところでは、決まりきった事実中心の文章に"
        "ついては、機械とプロとの差は狭まり続けている。もし言語の唯一の目的が情報を頭から頭へ移すこと"
        "だったなら、学習不要論に抗うのは難しいだろう。"),
    (3, "<b>それでも</b>、情報を運ぶことだけが、言語のする仕事ではない。単語を事実の単なる容れ物として"
        "扱うとき、私たちは、あらゆる言語が、ある共同体がどのように生き、どのように考えてきたかの記録"
        "でもあることを忘れている。それゆえ、一つの言語を学ぶことの価値は、翻訳だけでは測れない。機械が"
        "届けるのはメッセージの中身であり、学習者がゆっくりと手に入れるのは、どんなソフトも提供しようと"
        "さえしないものなのだ。"),
    (4, "言語がどれほど異なる仕方で世界を切り分けているか、考えてみてほしい。ある言語が、別の言語なら"
        "一語で済むところにいくつもの単語を必要とすることもあれば、ある言語では基本的な色が、隣の言語"
        "では名前を持たないこともある。敬語の体系は、話すたびに上下や親疎に気づくことを話者に義務づける"
        "し、単純な挨拶でさえ、ある国では天気を尋ね、別の国では食事を済ませたかどうかを尋ねる。"
        "<b>言い換えれば、言語を学ぶことは、別の共同体の「世界への注意の向け方」を借りることなのである。</b>"
        "学習者が手に入れるのは、古い物につける新しいラベルだけではなく、新しく見えてくるものなのだ。"),
    (5, "学ぶ過程は、結果と同じだけ重要である。機械が完璧に訳せるものを、なぜわざわざ苦労して下手に話す"
        "必要があるのか。——その苦労そのものが、メッセージを運ぶからだ。相手自身の言語で挨拶をすれば、"
        "どれほどぎこちなくても、「あなたは私の努力に値する人だった」ということが相手に伝わり、そうした"
        "敬意は、どんなアプリにも開けられない扉を開く。同時に、外国語の文法と格闘することは、母語を外側"
        "から——現実の自然な声としてではなく、数ある話し方の一つとして——眺めることを可能にしてくれる。"),
    (6, "さて、ここからが問題の核心である。<b>外国語が私たちに与えてくれるものは、情報をやり取りする"
        "ための手段であるというよりも、むしろ新しい目であり、他の人々のかたわらに立つための新しいあり方"
        "なのだ。</b>翻訳はメッセージを動かすが、学習は学ぶ者自身を動かす。機械は、何が言われたかを教えて"
        "くれる。しかし機械は、なぜそれがそのように言われたのかを理解できる人間、理解しようと努めたこと"
        "で信頼を得る人間に、あなたを変えることはできない。"),
    (7, "以上のことは、翻訳ソフトを捨てよという呼びかけではない。うまく使えば、それは障壁を取り除き、"
        "時間を節約してくれるのだから。要点は、機械の翻訳が下手だということではなく、翻訳はそもそも言語"
        "のすべてではなかった、ということだ。情報がひとりでに行き来する今だからこそ、<b>外国語を学ぶ理由"
        "は、むしろ増えたのである。</b>私たちに残されているのは、まさに、どんな機械にも運ぶことのできない、"
        "言語のあの部分なのだ。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("point A at B", "AをBに向ける"),
    ("within seconds", "数秒のうちに"),
    ("struggle with ~", "〜に苦労する、〜と格闘する"),
    ("do the job", "用を足す、役目を果たす"),
    ("in an instant", "一瞬で"),
    ("reasonable as it sounds", "もっともらしく聞こえるが（譲歩の as）"),
    ("rest on ~", "〜に基づく、〜の上に成り立つ"),
    ("remarkably", "驚くほど"),
    ("instruction manual", "取扱説明書"),
    ("routine", "決まりきった、日常的な"),
    ("resist", "抵抗する、あらがう"),
    ("mere", "単なる"),
    ("container", "容器、容れ物"),
    ("carve up ~", "〜を切り分ける"),
    ("be content with ~", "〜で満足している"),
    ("oblige A to do", "Aに〜することを義務づける"),
    ("render", "（別の形に）変える、訳す、表現する"),
    ("clumsily", "ぎこちなく、下手に"),
    ("be worth ~", "〜に値する"),
    ("wrestle with ~", "〜と格闘する"),
    ("mother tongue", "母語"),
    ("now that SV", "今や〜なのだから"),
    ("if anything", "どちらかと言えば、むしろ"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 問題提起：「機械が訳せるなら学習は無駄」という通念と、その反転",
  "sentences": [
    {"chunks": [("V","Open","開け"),("O","a translation app,","翻訳アプリを"),
                ("V","point","向けよ"),("O","your phone","スマホを"),
                ("M","(at a menu in a foreign city),","外国の街のメニューに"),
                ("接","and","そうすれば"),("S","the words","単語たちは"),
                ("V","rearrange","並べ替える"),("O","themselves","自らを"),
                ("M","(into your own language) (within seconds).","あなた自身の言語へと、数秒のうちに")],
     "note":"▶ <b>命令文, and …</b>＝「〜せよ、そうすれば…」。rearrange oneself＝再帰代名詞「自らを並べ替える（＝並び変わる）」。"},
    {"chunks": [("S","Such tools","そのような道具は"),("V","are","である"),("M","now","今や"),
                ("C","so quick and so cheap","とても速く、とても安価"),
                ("M","(that many people ask an obvious question):","多くの人が当然の疑問を口にするほどに"),
                ("-","why spend years struggling with vocabulary and grammar (when a machine can do the job in an instant)?","なぜ何年も語彙と文法に苦労するのか——機械が一瞬で用を足せるというのに")],
     "note":"▶ <b>so … that ~</b>＝「とても…なので〜」。コロン(:)以下＝an obvious question の中身（同格）。why＋動詞原形＝「なぜ〜するのか」。"},
    {"chunks": [("S","Learning a foreign language,","外国語を学ぶことは"),
                ("M","they conclude,","と彼らは結論づける"),("V","is","である"),
                ("C","a waste of time.","時間の無駄")],
     "note":"▶ 動名詞 Learning …＝主語。they conclude は挿入。ここまでが「通念」の提示。"},
    {"chunks": [("接","Nevertheless,","それにもかかわらず"),("S","this conclusion,","この結論は"),
                ("M","(reasonable as it sounds),","もっともらしく聞こえはするが"),
                ("V","rests on","基づいている"),
                ("O","a narrow idea of [what language is for].","「言語は何のためにあるのか」についての狭い考えに")],
     "note":"▶ <b>R1｜逆接 Nevertheless の直後が筆者の主張</b>（＝空所A）。<b>形容詞 as S V</b>＝「〜ではあるが」（譲歩の as）。what language is for＝前置詞 of の目的語となる名詞節。"},
  ]},
 {"head": "第2段 — 譲歩：確かに機械は実用翻訳が得意だ（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当だ"),
                ("-","[that machines have become remarkably good at practical translation].","機械が実用的な翻訳において驚くほど有能になった、ということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。形式主語 It＝真主語 that 節。後の逆接（第3段 Still）で反転する前振り。"},
    {"chunks": [("M","(For a tourist &lt;reading a sign&gt;, a traveler &lt;ordering dinner&gt;, or a company &lt;preparing an instruction manual&gt;),","標識を読む観光客、夕食を注文する旅行者、取扱説明書を用意する会社にとっては"),
                ("S","translation software","翻訳ソフトは"),("V","is","である"),("M","often","しばしば"),
                ("C","faster and more accurate","より速く、より正確"),
                ("M","(than most human learners will ever be).","たいていの人間の学習者が今後なり得る水準よりも")],
     "note":"▶ reading／ordering／preparing＝いずれも現在分詞が直前の名詞を後ろから修飾〔<b>R11</b>〕。than … will ever be＝「これからなり得る以上に」。"},
    {"chunks": [("S","Research","研究は"),("V","suggests","示唆する"),
                ("O","[that (for routine, factual texts) the gap between machines and professionals keeps narrowing].","決まりきった事実中心の文章では、機械とプロの差は狭まり続けている、と")],
     "note":"▶ keep -ing＝「〜し続ける」。<b>routine, factual texts＝「実用的文章」への限定</b>——問7①「あらゆる文章」はここで×になる〔<b>R9</b>〕。"},
    {"chunks": [("M","(If the only purpose of language were to move information from head to head),","もし言語の唯一の目的が、情報を頭から頭へ移すことだったなら"),
                ("S","the argument against learning","学習反対論は"),
                ("V","would be","であろう"),("C","hard to resist.","抗いがたい（もの）")],
     "note":"▶ <b>仮定法過去</b>（If S were …, S would …）＝「実際はそうではない」が含意——第3段への橋渡し。hard to resist＝難易の to 不定詞（resist の目的語＝主語 the argument）。"},
  ]},
 {"head": "第3段 — 主張の転換：情報を運ぶことだけが言語の仕事ではない（Still）",
  "sentences": [
    {"chunks": [("接","Still,","それでも"),("S","moving information","情報を運ぶことは"),
                ("V","is","である"),
                ("C","not the only thing &lt;(that) a language does&gt;.","言語がする唯一のことではない")],
     "note":"▶ <b>R1｜逆接 Still＝ここが主張転換点</b>（＝空所B）。動名詞 moving …＝主語。a language does＝関係詞省略で thing を修飾〔R11〕。"},
    {"chunks": [("M","(When we treat words as mere containers for facts),","単語を事実の単なる容れ物として扱うとき"),
                ("S","we","私たちは"),("V","forget","忘れている"),
                ("O","[that every language is also a record of how a community has lived and thought].","あらゆる言語は、ある共同体がどう生き、どう考えてきたかの記録でもある、ということを")],
     "note":"▶ treat A as B＝「AをBとして扱う」。a record of how …＝「どう〜してきたかの記録」（how の名詞節が前置詞 of の目的語）。"},
    {"chunks": [("S","The value of learning one,","一つ（の言語）を学ぶことの価値は"),
                ("M","therefore,","したがって"),("V","cannot be measured","測ることができない"),
                ("M","(by translation alone).","翻訳だけでは")],
     "note":"▶ one＝a language の代用。受動態 be measured by …。alone＝名詞・代名詞の直後で「〜だけ」。"},
    {"chunks": [("S","A machine","機械は"),("V","delivers","届ける"),
                ("O","the content of a message;","メッセージの中身を"),
                ("S","a learner","学習者は"),("M","slowly","ゆっくりと"),("V","gains","手に入れる"),
                ("O","something &lt;that no software even attempts to offer&gt;.","どんなソフトも提供しようとさえしないものを")],
     "note":"▶ セミコロン(;)で機械と学習者を<b>対比</b>。that …＝関係代名詞（offer の目的語）〔R11〕。「それが何か」は第4〜6段で明かされる。"},
  ]},
 {"head": "第4段 — 理由①：言語＝世界の切り取り方（抽象→具体）",
  "sentences": [
    {"chunks": [("V","Consider","考えてみよ"),
                ("O","[how differently languages carve up the world].","言語がどれほど異なる仕方で世界を切り分けているかを")],
     "note":"▶ 命令文。how differently …＝consider の目的語となる名詞節（間接疑問）。<b>R4｜この抽象を、以下の具体例（語彙・色名・敬語・挨拶）が支える</b>。"},
    {"chunks": [("S","One language","ある言語は"),("V","may need","必要とするかもしれない"),
                ("O","several words","いくつもの単語を"),
                ("M","(where another is content with one),","別の言語なら一語で満足するところで"),
                ("接","and","そして"),
                ("S","a color &lt;basic in one tongue&gt;","ある言語では基本的な色が"),
                ("V","may have","持たないかもしれない"),("O","no name","名前を"),
                ("M","(in the next).","その隣の言語では")],
     "note":"▶ where ＝「〜するところで（は）」（場所の副詞節）。basic in one tongue＝形容詞句が color を後置修飾〔R11〕。tongue＝「言語」。"},
    {"chunks": [("S","Systems of polite speech","敬語の体系は"),("V","oblige","義務づける"),
                ("O","speakers","話者に"),("C","to notice rank and closeness","上下や親疎に気づくことを"),
                ("M","(every time they speak),","話すたびに"),
                ("接","and","また"),("S","even a simple greeting","単純な挨拶でさえ"),
                ("V","may ask","尋ねるかもしれない"),
                ("M","(about the weather) (in one country)","ある国では天気について"),
                ("接","and","そして"),
                ("M","(about [whether you have eaten]) (in another).","別の国では食事を済ませたかどうかについて")],
     "note":"▶ <b>oblige O to do</b>＝「Oに〜することを義務づける」。every time SV＝「〜するたびに」（接続詞的）。whether …＝「〜かどうか」（前置詞 about の目的語となる名詞節）。＝<b>問4③の根拠</b>。"},
    {"chunks": [("S","To learn a language,","言語を学ぶことは"),
                ("M","in other words,","言い換えれば"),("V","is","である"),
                ("C","to borrow another community's way of noticing the world.","別の共同体の、世界への注意の向け方を借りること")],
     "note":"▶ <b>R8｜in other words＝直前の具体例のイコール言い換え（抽象化）</b>。To learn＝不定詞主語／to borrow＝補語。way of doing＝「〜する仕方」。＝<b>下線部(1)＝問3</b>。"},
    {"chunks": [("S","The learner","学習者は"),("V","gains","手に入れる"),
                ("O","not just new labels for old things but new things &lt;to see&gt;.","古い物への新しいラベルだけでなく、新しく見えてくるものを")],
     "note":"▶ <b>not just A but B</b>＝「AだけでなくB」——重心はB〔<b>R3</b>の仲間〕。to see＝不定詞が things を修飾〔R11〕。"},
  ]},
 {"head": "第5段 — 理由②：学ぶ過程そのものの効用（修辞疑問→筆者の答え）",
  "sentences": [
    {"chunks": [("S","The process of learning","学ぶという過程は"),("V","matters","重要である"),
                ("M","(as much as the result).","結果と同じくらい")],
     "note":"▶ <b>matter＝動詞「重要である」</b>。as much as …＝同等比較。理由②の主題提示。"},
    {"chunks": [("M","Why","なぜ"),("V","should","〜しなければならないのか（助動詞が疑問で前へ）"),
                ("S","anyone","一体誰が"),("V","struggle","わざわざ苦労する"),
                ("M","(to speak badly [what a machine can render perfectly])?","機械が完璧に訳せるものを、下手に話そうとして")],
     "note":"▶ <b>R12｜筆者自身の疑問文は「これから答える」という約束</b>。疑問文なので助動詞 should が主語 anyone の前に出た形。what …＝関係代名詞 what（speak の目的語）。render＝「（別の形で）表現する、訳す」。"},
    {"chunks": [("接","Because","なぜなら"),("S","the struggle itself","その苦労そのものが"),
                ("V","carries","運ぶからだ"),("O","a message.","メッセージを")],
     "note":"▶ <b>R12｜直前の疑問への筆者自身の答え＝ここが主張</b>。itself＝強調「〜そのもの」。Because 単独の文＝「答え」を際立たせる書き方。"},
    {"chunks": [("M","(When you greet people in their own language), (however clumsily),","相手自身の言語で挨拶するとき——それがどれほどぎこちなくても"),
                ("S","you","あなたは"),("V","show","示す"),("O","them","相手に"),
                ("O","[that they were worth your effort],","相手はあなたの努力に値する存在だった、と"),
                ("接","and","そして"),("S","such respect","そのような敬意は"),
                ("V","opens","開く"),
                ("O","doors &lt;(that) no app can unlock&gt;.","どんなアプリにも解錠できない扉を")],
     "note":"▶ <b>however＋副詞</b>＝「どれほど〜でも」（譲歩）。show O1 O2（that節）。be worth ~＝「〜に値する」。no app can unlock＝関係詞省略で doors を修飾〔R11〕。"},
    {"chunks": [("M","(At the same time),","同時に"),
                ("S","wrestling with a foreign grammar","外国語の文法と格闘することは"),
                ("V","lets","させてくれる"),("O","you","あなたに"),
                ("C","see your mother tongue","母語を眺めることを"),
                ("M","(from the outside), (as one way of speaking among many rather than the natural voice of reality).","外側から——現実の自然な声としてではなく、数ある話し方の一つとして")],
     "note":"▶ 使役 <b>let O do（原形）</b>。動名詞 wrestling …＝主語。as A rather than B＝「BとしてではなくAとして」（否定される側＝rather than の後ろ）。"},
  ]},
 {"head": "第6段 — 核心：not so much A as B — 翻訳は情報を、学習は視点と関係を",
  "sentences": [
    {"chunks": [("M","Here, then,","さて、ここに"),("V","is","ある"),
                ("S","the heart of the matter.","問題の核心が")],
     "note":"▶ <b>倒置</b>：Here is S＝「ここにSがある」。then＝「それでは、つまり」。核心の予告。"},
    {"chunks": [("S","[What a foreign language gives us]","外国語が私たちに与えてくれるものは"),
                ("V","is","である"),
                ("C","not so much a means of exchanging information as a new pair of eyes and a new way of standing beside other people.","情報を交換する手段というよりむしろ、新しい目と、他の人々のかたわらに立つ新しいあり方")],
     "note":"▶ <b>R13｜not so much A as B＝「AというよりむしろB」（重心はB）</b>。What …＝関係代名詞 what の名詞節が主語。means of doing＝「〜する手段」。＝<b>下線部(2)＝問2</b>。"},
    {"chunks": [("S","Translation","翻訳は"),("V","moves","動かす"),("O","messages;","メッセージを"),
                ("S","learning","学習は"),("V","moves","動かす"),("O","the learner.","学ぶ者を")],
     "note":"▶ セミコロン対比＋同語反復（moves）による<b>対句</b>。「翻訳が動かすのは情報、学習が動かすのは人」——前文の言い換え〔R8〕。"},
    {"chunks": [("S","A machine","機械は"),("V","can tell","伝えられる"),("O","you","あなたに"),
                ("O","[what was said],","何が言われたかを"),
                ("接","but","しかし"),("S","it","それは"),("V","cannot make","できない"),
                ("O","you","あなたを"),
                ("C","the kind of person &lt;who sees why it was said that way&gt;, or &lt;who earns trust by trying to understand&gt;.","なぜそれがそのように言われたのかを理解する種類の人、あるいは、理解しようと努めることで信頼を得る種類の人に（することは）")],
     "note":"▶ 使役 <b>make O C</b>（OをCにする）。what was said＝名詞節／why it was said that way＝間接疑問（sees の目的語）。who …, or who …＝二つの関係詞節が person を修飾〔R11〕。"},
  ]},
 {"head": "第7段 — 譲歩つき結論：翻訳を捨てよという話ではない——学ぶ理由はむしろ増えた",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),("V","is","ではない"),
                ("C","a call &lt;to throw away translation software&gt;,","翻訳ソフトを捨てよという呼びかけ"),
                ("-","&lt;which removes barriers and saves time (when used well)&gt;.","——それ（翻訳ソフト）は、うまく使えば障壁を取り除き、時間を節約してくれるのだが")],
     "note":"▶ None of this is …＝全否定。<b>R9注意</b>：問7⑤「完全にやめるよう勧めている」はこの文で×。which＝非制限用法の関係代名詞（補足説明）。when (it is) used well＝「主語＋be動詞」の省略。"},
    {"chunks": [("S","The point","要点"),("V","is","である"),
                ("C","not [that machines translate badly], but [that translation was never the whole of language].","機械の翻訳が下手だということではなく、翻訳はそもそも言語のすべてではなかった、ということ")],
     "note":"▶ <b>R3｜not A but B＝Bの側が核心</b>。二つの that 節が補語。never the whole of ~＝「決して〜の全体ではない」。"},
    {"chunks": [("M","(Now that information travels by itself),","今や情報はひとりでに旅をするのだから"),
                ("S","the reasons &lt;to learn a foreign language&gt;","外国語を学ぶ理由は"),
                ("V","have, (if anything), increased.","むしろ増えたのである")],
     "note":"▶ <b>now that SV</b>＝「今や〜なのだから」（理由）。if anything＝「どちらかと言えば、むしろ」（挿入）。to learn …＝不定詞が reasons を修飾〔R11〕。＝<b>下線部(3)＝問5</b>。"},
    {"chunks": [("S","[What remains for us]","私たちに残されているものは"),("V","is","である"),
                ("M","precisely","まさに"),
                ("C","the part of language &lt;that no machine can carry&gt;.","どんな機械にも運べない、言語のあの部分")],
     "note":"▶ What …＝関係代名詞 what 節が主語。that no machine can carry＝関係代名詞（carry の目的語）が part を修飾〔R11〕。「翻訳が運ぶのは情報、学習が与えるのは視点と関係」という第6段の核心を締めくくる。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=4文/第2段=4文/第3段=4文/第4段=5文/第5段=5文/第6段=4文/第7段=4文)
SVOC_LOGIC = {
    (1, 4): "対比",                                   # s4 Nevertheless→筆者の反論
    (2, 1): "譲歩", (2, 4): "譲歩",                    # s1 It is true / s4 仮定法の駄目押し
    (3, 1): "対比", (3, 3): "因果", (3, 4): "対比",     # s1 Still→転換 / s3 therefore / s4 機械 vs 学習者
    (4, 1): "主張", (4, 2): "具体例", (4, 3): "具体例", (4, 4): "主張", (4, 5): "追加",
    (5, 1): "主張", (5, 3): "主張", (5, 4): "因果", (5, 5): "追加",
    (6, 2): "主張", (6, 3): "対比", (6, 4): "対比",
    (7, 1): "譲歩", (7, 2): "対比", (7, 3): "主張", (7, 4): "主張",
}
