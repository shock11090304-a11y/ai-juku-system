# -*- coding: utf-8 -*-
"""中学英語「不定詞の用法」4択ドリル 30問 (公立高校入試 標準レベル)。

塾長依頼 2026-07-29: 月曜1限 中学応用 (高校受験生) 向けの不定詞ドリル宿題。
無課金 = AI生成は使わず本セッションで作問し、検証後に exam_questions へ直INSERT。

★ unit / filter = '不定詞の用法'
   既存の '不定詞・動名詞' と startsWith 衝突しない (どちらも互いの接頭辞ではない) ため、
   dojo-drill の unitExact (pref(q.unit).startsWith(filter)) で相互に混ざらない。
   - '不定詞・動名詞'.startsWith('不定詞の用法') === false
   - '不定詞の用法'.startsWith('不定詞・動名詞') === false
   ※ filter を素の '不定詞' にすると既存の '不定詞・動名詞' を巻き込むので不可。

★ 出題形式を意図的に混ぜている理由 (tell 対策):
   空所補充だけで揃えると「答えはいつも to +原形」= 文法を知らなくても形だけで当たる。
   原形不定詞 / too〜to・enough to の語選択 / 同意文書きかえ / 語順選択 / 用法の識別 /
   意味の選択 を混ぜ、正解が「to +原形」になる問題を 12/30 に抑えている。

各項目 = (correct, distractors[3], stem, expl, usage)
正解の index は round-robin (0,1,2,3) で後段が決めるので、ここでは正解「テキスト」で持つ。
解説も正解テキスト参照で書く = 選択肢を入れ替えてもズレない。
"""

ITEMS = [
    # ───────── 名詞的用法 (〜すること) ─────────
    dict(
        usage="名詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nIt is difficult for me ( ) up early in the morning.",
        correct="to get",
        distractors=["get", "getting", "got"],
        expl="〈It is +形容詞+ for 人 + to +動詞の原形〉で「(人)にとって〜することは…だ」を表します。文頭の It は形式主語で、本当の主語は to get up early のほう(名詞的用法)です。「私にとって朝早く起きることは難しい」。",
    ),
    dict(
        usage="名詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nI didn't know what ( ) to her at that time.",
        correct="to say",
        distractors=["say", "saying", "said"],
        expl="〈疑問詞+ to +動詞の原形〉で「何を〜すればよいか」を表し、know の目的語になります(名詞的用法)。what to say で「何を言えばよいか」。「そのとき私は彼女に何と言えばよいかわからなかった」。",
    ),
    dict(
        usage="名詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nKen promised ( ) his little sister to the zoo on Sunday.",
        correct="to take",
        distractors=["take", "taking", "took"],
        expl="promise は後ろに〈to +動詞の原形〉をとり、「〜すると約束する」という意味になります。ここでは promised の目的語になっている名詞的用法です。「ケンは日曜日に妹を動物園へ連れて行くと約束した」。",
    ),
    dict(
        usage="名詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nMy father taught me how ( ) a bike.",
        correct="to ride",
        distractors=["ride", "riding", "rode"],
        expl="〈how to +動詞の原形〉で「〜のしかた、どうやって〜すればよいか」。teach の目的語になる名詞的用法です。teach 人 how to 〜 で「(人)に〜のしかたを教える」となります。「父は私に自転車の乗り方を教えてくれた」。",
    ),
    # ───────── 副詞的用法 (目的・感情の原因) ─────────
    dict(
        usage="副詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nKen got up early ( ) the first train.",
        correct="to catch",
        distractors=["catch", "catching", "caught"],
        expl="「〜するために」と目的を表す副詞的用法です。got up early(早く起きた)という動作の目的を、後ろから〈to +動詞の原形〉が説明しています。「ケンは始発電車に乗るために早く起きた」。",
    ),
    dict(
        usage="副詞的用法",
        stem="次の対話の( )に入る最も適切なものを選びなさい。\nA: Why do you use this app every day?\nB: ( ) new English words.",
        correct="To learn",
        distractors=["Learn", "Learning", "Learned"],
        expl="Why 〜? に「〜するためです」と目的で答えるときは〈To +動詞の原形〉で始めます(副詞的用法)。Because I want to learn 〜 と同じ内容を短く答えた形です。原形のままだと命令文になり、Learning や Learned では Why への答えになりません。「新しい英単語を覚えるためです」。",
    ),
    dict(
        usage="副詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nI was very glad ( ) you at the station yesterday.",
        correct="to see",
        distractors=["see", "seeing", "saw"],
        expl="glad, happy, sad, sorry などの感情を表す形容詞の後ろに置く〈to +動詞の原形〉は「〜して」と感情の原因を表す副詞的用法です。glad のあとに see や saw、seeing をそのまま続けることはできません。「昨日は駅であなたに会えてとてもうれしかった」。",
    ),
    dict(
        usage="副詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nShe was surprised ( ) the news about the accident.",
        correct="to hear",
        distractors=["hear", "hears", "heard"],
        expl="be surprised to 〜 で「〜して驚く」。感情の原因を表す副詞的用法です。surprised の後ろに動詞をそのままの形(hear)や hears・heard の形を続けることはできません。「彼女はその事故の知らせを聞いて驚いた」。",
    ),
    # ───────── 形容詞的用法 (〜するための/〜すべき) ─────────
    dict(
        usage="形容詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nI had no time ( ) TV yesterday.",
        correct="to watch",
        distractors=["watch", "watching", "watched"],
        expl="直前の名詞 time を後ろから説明する形容詞的用法です。time to watch TV で「テレビを見る時間」。「昨日はテレビを見る時間がなかった」。",
    ),
    dict(
        usage="形容詞的用法",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nWe have nothing ( ) for lunch. Let's go shopping.",
        correct="to eat",
        distractors=["eat", "eating", "ate"],
        expl="nothing to eat で「食べるものが何もない」。-thing で終わる語も、不定詞が後ろから説明します(形容詞的用法)。「昼食に食べるものが何もない。買い物に行こう」。",
    ),
    dict(
        usage="形容詞的用法",
        stem="次の日本文の意味に合う英文として最も適切なものを選びなさい。\n私は彼に何か冷たい飲み物をあげたい。",
        correct="I want to give him something cold to drink.",
        distractors=[
            "I want to give him cold something to drink.",
            "I want to give him something to drink cold.",
            "I want to give something cold to drink for him.",
        ],
        expl="something を形容詞と不定詞の両方で説明するときは〈something +形容詞+ to +動詞の原形〉の順に並べます(不定詞は形容詞的用法)。cold something のように形容詞を前に置くことはできません。「彼に〜をあげる」は give him 〜 の語順で、give 〜 for him とは言いません。",
    ),
    # ───────── 〈動詞+人+ to do〉 ─────────
    dict(
        usage="人+to do",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nMy mother told me ( ) my room before dinner.",
        correct="to clean",
        distractors=["clean", "cleaning", "cleaned"],
        expl="〈tell +人+ to +動詞の原形〉で「(人)に〜するように言う」。「母は私に夕食の前に部屋をそうじするように言った」。",
    ),
    dict(
        usage="人+to do",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nI asked him ( ) the window because the room was very hot.",
        correct="to open",
        distractors=["open", "opening", "opened"],
        expl="〈ask +人+ to +動詞の原形〉で「(人)に〜してくれるように頼む」。「部屋がとても暑かったので、私は彼に窓を開けてくれるように頼んだ」。",
    ),
    dict(
        usage="人+to do",
        stem="次の中から、英文として正しいものを選びなさい。",
        correct="I want you to come to my party.",
        distractors=[
            "I want you come to my party.",
            "I want that you come to my party.",
            "I want you to coming to my party.",
        ],
        expl="「(人)に〜してほしい」は〈want +人+ to +動詞の原形〉で表します。人のあとの to を落として want you come とはできず、want は後ろに that 節もとれません。また不定詞の to のあとは必ず動詞の原形なので to coming の形にもなりません。",
    ),
    # ───────── 原形不定詞 (let / make + 人 + 動詞の原形) ─────────
    dict(
        usage="原形不定詞",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nPlease let me ( ) your new camera.",
        correct="use",
        distractors=["to use", "using", "used"],
        expl="〈let +人+ 動詞の原形〉で「(人)に〜させてあげる」。let の後ろでは to をつけない原形不定詞を使います。「あなたの新しいカメラを使わせてください」。",
    ),
    dict(
        usage="原形不定詞",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nThis song always makes me ( ) happy.",
        correct="feel",
        distractors=["to feel", "feeling", "felt"],
        expl="〈make +人+ 動詞の原形〉で「(人)に〜させる」。make の後ろも to をつけない原形不定詞です。「この歌はいつも私を幸せな気持ちにさせてくれる」。",
    ),
    # ───────── 不定詞の否定 (not to do) ─────────
    dict(
        usage="不定詞の否定",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nBe careful ( ) the glass. It is very old.",
        correct="not to break",
        distractors=["not break", "not breaking", "don't break"],
        expl="不定詞を打ち消すときは to の直前に not を置き、〈not to +動詞の原形〉の形にします。be careful not to 〜 で「〜しないように気をつける」。not だけを動詞の前に置いたり、don't を続けたりすることはできません。「そのコップを割らないように気をつけて。とても古いものです」。",
    ),
    # ───────── too 〜 to / 〜 enough to ─────────
    dict(
        usage="too〜to/enough to",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nI was ( ) tired to do my homework last night.",
        correct="too",
        distractors=["very", "so", "enough"],
        expl="〈too +形容詞+ to +動詞の原形〉で「あまりに…すぎて〜できない」。so を使うなら so tired that I couldn't 〜 のように that が必要です。very には「〜できない」という打ち消しの意味がなく、enough は tired の後ろに置く語なので、どちらもこの形では使えません。「昨夜は疲れすぎて宿題ができなかった」。",
    ),
    dict(
        usage="too〜to/enough to",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nShe spoke slowly ( ) for us to understand her English.",
        correct="enough",
        distractors=["too", "very", "much"],
        expl="〈形容詞・副詞+ enough (for 人) to +動詞の原形〉で「(人)が〜できるほど十分…」。enough は形容詞や副詞の後ろに置くのが大切なきまりです。形容詞・副詞の後ろに置いて「十分に」の意味を足せるのは enough だけで、too・very・much はいずれも前に置く語です。「彼女は私たちが彼女の英語を理解できるくらいゆっくり話してくれた」。",
    ),
    dict(
        usage="too〜to/enough to",
        stem="次の2文がほぼ同じ意味になるように、( )に入る最も適切なものを選びなさい。\nThis bag is so heavy that I cannot carry it.\n= This bag is ( ).",
        correct="too heavy for me to carry",
        distractors=[
            "heavy enough for me to carry",
            "so heavy for me to carry",
            "very heavy for me to carry",
        ],
        expl="〈so +形容詞+ that 主語 cannot 〜〉は〈too +形容詞+ for 人 + to +動詞の原形〉に書きかえられます。「運べない」という打ち消しの意味は too が担います。enough を使うと「運べるほど十分重い」と反対の意味になり、that 〜 cannot を伴わない so や very だけでは「〜できない」を表せません。もとの文の it(=かばん)を to carry の後ろに残さない点にも注意しましょう。",
    ),
    dict(
        usage="too〜to/enough to",
        stem="次の2文がほぼ同じ意味になるように、( )に入る最も適切なものを選びなさい。\nThis book is easy enough for me to read.\n= This book is so easy that I ( ) read it.",
        correct="can",
        distractors=["cannot", "should", "must"],
        expl="〈形容詞+ enough for 人 + to +動詞の原形〉は「(人)が〜できるほど十分…」という意味なので、〈so +形容詞+ that 主語 can 〜〉に書きかえられます。cannot では反対の意味になり、should や must では「できる」という意味になりません。「この本はやさしいので私にも読める」。",
    ),
    # ───────── 意味の理解 ─────────
    dict(
        usage="意味の理解",
        stem="次の英文の意味として最も適切なものを選びなさい。\nHe was too busy to answer my e-mail.",
        correct="彼は忙しすぎて、私のメールに返事ができなかった。",
        distractors=[
            "彼はとても忙しかったが、私のメールに返事をした。",
            "彼は私のメールに返事をするために、とても忙しくしていた。",
            "彼は私のメールに返事をするほど忙しくはなかった。",
        ],
        expl="〈too +形容詞+ to +動詞の原形〉は「…すぎて〜できない」という打ち消しの意味を表します。英文に not はありませんが、日本語にするときは「〜できなかった」と訳す点がポイントです。「忙しかったが返事をした」「返事をするために忙しくした」「返事をするほど忙しくない」は、どれも「〜できなかった」という打ち消しになっていません。",
    ),
    # ───────── 原形不定詞・否定の追加分 ─────────
    #   ★「to +原形の選択肢を選べば当たる」というヒューリスティックを罰する問題を意図的に足している。
    #     (下の2問は to +原形の肢が"誤答"側にある)
    dict(
        usage="原形不定詞",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nMy parents don't let me ( ) video games on weekdays.",
        correct="play",
        distractors=["to play", "playing", "played"],
        expl="〈let +人+ 動詞の原形〉で「(人)に〜させてあげる」。let の後ろは to をつけない原形不定詞です。「両親は平日は私にゲームをさせてくれない」。",
    ),
    dict(
        usage="原形不定詞",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nOur teacher makes us ( ) English in every class.",
        correct="speak",
        distractors=["to speak", "speaking", "spoke"],
        expl="〈make +人+ 動詞の原形〉で「(人)に〜させる」。make の後ろも to をつけない原形不定詞です。「先生は毎回の授業で私たちに英語を話させる」。",
    ),
    dict(
        usage="不定詞の否定",
        stem="次の文の( )に入る最も適切なものを選びなさい。\nThe baby is sleeping. Please try ( ) any noise.",
        correct="not to make",
        distractors=["not make", "not making", "not to making"],
        expl="try not to 〜 で「〜しないようにする」。不定詞を打ち消す not は to の直前に置き、〈not to +動詞の原形〉の形にします。not だけを動詞の前に置いたり、to のあとを -ing にしたりはできません。「赤ちゃんが眠っています。音を立てないようにしてください」。",
    ),
    # ───────── 意味の理解・正誤の追加分 ─────────
    dict(
        usage="意味の理解",  # _usage は「出題形式」の内訳を見るためのラベル (q22 の too〜to と同じ枠)
        stem="次の英文の意味として最も適切なものを選びなさい。\nCould you tell me how to use this washing machine?",
        # ★4肢とも「この洗濯機を〜か教えていただけますか。」の形にそろえる。正解だけ文の形が違うと
        #   英文を読まずに「形の違う1本」を選んで当てられてしまう(前版の欠陥)。
        correct="この洗濯機をどう使えばよいか教えていただけますか。",
        distractors=[
            "この洗濯機を使ってもよいか教えていただけますか。",
            "この洗濯機を使ったことがあるか教えていただけますか。",
            "この洗濯機をいつ使えばよいか教えていただけますか。",
        ],
        expl="〈how to +動詞の原形〉は「どうやって〜すればよいか、〜のしかた」を表します。「〜してもよいか」は may、「いつ〜すればよいか」は when to 〜、「〜したことがあるか」は have used を使う言い方で、どれも how to 〜 とは意味が違います。",
    ),
    dict(
        usage="名詞的用法",  # ★〈It is +形容詞+ for 人 + to 〜〉は形式主語構文=名詞的用法 (tell/ask+人+to とは別物)
        stem="次の中から、英文として正しいものを選びなさい。",
        correct="It is important for us to help each other.",
        distractors=[
            "It is important for us help each other.",
            "It is important for us helping each other.",
            "It is important that for us to help each other.",
        ],
        expl="〈It is +形容詞+ for 人 + to +動詞の原形〉が正しい形です。It は形式主語で、to help 〜 が本当の主語になる名詞的用法です。for 人 のあとは必ず〈to +動詞の原形〉で、to をつけずに動詞の原形を置いたり -ing にしたりはできません。that を入れることもできません。",
    ),
    # ───────── 用法の識別 ─────────
    dict(
        usage="用法の識別",
        stem="次の文の to see と同じ用法の不定詞を含む文を選びなさい。\nI went to the park to see the cherry blossoms.",
        correct="He came to Japan to study Japanese.",
        distractors=[
            "I want to see your new car.",
            "She has a lot of work to do today.",
            "It is fun to see old friends.",
        ],
        expl="例文の to see は「桜を見るために」と目的を表す副詞的用法です。「日本語を勉強するために来日した」も同じ目的を表しています。want to see は名詞的用法、work to do は名詞を説明する形容詞的用法、It is fun to see 〜 は形式主語 It を使った名詞的用法です。",
    ),
    dict(
        usage="用法の識別",
        stem="次の文の to read と同じ用法の不定詞を含む文を選びなさい。\nI have many books to read this summer.",
        correct="This is a good place to take pictures.",
        distractors=[
            "I like to read comic books.",
            "He studied hard to pass the exam.",
            "To read English books is not easy.",
        ],
        expl="例文の to read は直前の名詞 books を後ろから説明する形容詞的用法です。名詞 place を後ろから説明している文が同じ用法にあたります。like to read は名詞的用法、studied hard to pass は目的を表す副詞的用法、To read 〜 is not easy は主語になる名詞的用法です。",
    ),
    dict(
        usage="用法の識別",
        stem="次の文の to be と同じ用法の不定詞を含む文を選びなさい。\nMy dream is to be a nurse.",
        correct="She wants to study science at college.",
        distractors=[
            "He has a lot of homework to do.",
            "I was happy to win the game.",
            "We use computers to study English.",
        ],
        expl="例文の to be は is の後ろで「〜になること」という意味を表す名詞的用法です。wants の目的語になっている「〜すること」も同じ名詞的用法です。homework to do は名詞を説明する形容詞的用法、happy to win は感情の原因、use computers to study は目的を表す副詞的用法です。",
    ),
]

UNIT = "不定詞の用法"
assert len(ITEMS) == 30, len(ITEMS)
for _it in ITEMS:
    assert len(_it["distractors"]) == 3, _it["stem"]
