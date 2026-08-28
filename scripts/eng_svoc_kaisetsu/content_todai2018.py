# -*- coding: utf-8 -*-
"""東京大学 2018 第5問 — 本文（正典）・全文 SVOCM 解析・設問(A)〜(G)の解答解説"""

META = {
    "key": "todai2018",
    "school": "東京大学",
    "year": "2018",
    "qno": "第 5 問",
    "title": "（小説・出典表示なし）",
    "author": "sign language ＝「手話」（問題文の注）",
    "jtitle": "沈黙の中に生きる娘と、抑えのきかない母",
    "lead": "耳の聞こえない女性 Janey が主人公の小説。現在（下宿人クラーク氏）→ 回想（失聴と母との衝突）"
            "→ 現在（外出をめぐる母との対立）の 3 場面。"
            "★東大の小説は「代名詞が誰を指すか」で全部決まる。she / her が母か娘かを毎文ごとに確定させること。",
}

# ---------------------------------------------------------------- 本文（印字そのまま）
RAW = [
    '"Janey, this is Mr. Clark. He\'s going to take a look at the room under the stairs." Her mother '
    "spoke too slowly and carefully, so that Janey could be sure to read each word. She had told her "
    "mother many times that she didn't have to do this, but her mother almost always did, even in "
    "front of people, to her embarrassment.",

    "Mr. Clark kept looking at Janey intently. Maybe, because of the way her mother had spoken, he "
    "suspected she was deaf. It would be like her mother not to have mentioned it. Perhaps he was "
    "waiting to see if she'd speak so that he could confirm his suspicion. She simply left her silence "
    "open to interpretation.",

    '"Will you show him the room?" her mother said.',

    "She nodded again, and turned so that he would follow her. Directly ahead and beneath a portion of "
    "the stairs was a single bedroom. She opened the door and he walked past her into the room, "
    "turned, and looked at her. She grew uncomfortable under his gaze, though she didn't feel as if he "
    "were looking at her as a woman, the way she might once have wanted if it were the right man. She "
    "felt she'd gone past the age for romance. It was a passing she'd lamented, then gotten over.",

    '"I like the room," he spelled out in sign language. "(B29)"',

    "That was all. No conversation, no explanation about how he'd known for certain that she was deaf "
    "or how he'd learned to speak with his hands.",

    "Janey came back to her mother and signed a question.",

    '"He is a photographer," she said, again speaking too slowly. "Travels around the world taking '
    'pictures, he says."',

    '"(B30)"',

    '"Buildings."',

    "Music was her entry into silence. She'd been only ten years old, sitting on the end of the porch "
    "above the steps, listening to the church choir. Then she began to feel dizzy, and suddenly fell "
    "backwards into the music.",

    "She woke into silence nights later, there in her room, in her bed. She'd called out from her "
    "confusion as any child would, and her mother was there instantly. But something (C) wrong, or had "
    "not (C), except inside her where illness and confusion grew. She hadn't heard herself, hadn't "
    "heard the call she'd made - Mama. And though her mother was already gripping her tightly, she'd "
    "called out again, but only into silence, which is where she lived now, had been living for so "
    "many years that she didn't feel uncomfortable inside its invisibility. Sometimes she thought it "
    "saved her, gave her a separate place to withdraw into as far as she might need at any given "
    "moment - and there were moments.",

    "The floor had always carried her mother's anger. She'd learned this first as little girl when her "
    "mother and father argued. Their words might not have existed as sound for her, but anger always "
    "caused its own vibration.",

    "She hadn't been exactly sure why they argued all those years ago, but sensed, the way a child "
    "will, that it was usually about her. One day her mother found her playing in the woods behind "
    "their house, and when she wouldn't follow her mother home, her mother grabbed her by the arm and "
    "dragged her through the trees. She finally pulled back and shouted at her mother, not in words "
    "but in a scream that expressed all she felt in one great vibration. Her mother slapped her hard "
    'across her face. She saw her mother shaking and knew her mother loved her, but love was sometimes '
    'like silence, beautiful but hard to bear. Her father told her, "She can\'t help herself."',

    'Weeks later, Mr. Clark said to Janey, "You might be able to help me."',

    '"If I can," she spelled with her fingers.',

    '"I\'ll need to (F) tomorrow. Maybe you can tell me some history about them."',

    "She nodded and felt glad to be needed, useful in some small way. Then Mr. Clark asked her to "
    'accompany him to the old house at the top of Oakhill. "You might enjoy that. Some time away from '
    'here."',

    "She looked toward the kitchen door, not aware at first why she turned that way. Perhaps she "
    "understood, on some unconscious level, what she hadn't a moment before. Her mother was standing "
    "there. She'd been listening to him.",

    'When Janey turned back to him, she read his lips. "Why don\'t you go with me tomorrow?"',

    "She felt the quick vibration of her mother's approach. She turned to her mother, and saw her "
    "mother's anger and fear, the way she'd always seen them. Janey drew in her breath and forced the "
    "two breath-filled words out in a harsh whisper that might have (C), for all she knew, like a sick "
    'child or someone dying: she said, "(B31)"',

    "Her mother stared at her in surprise, and Janey wasn't sure if her mother was more shocked that "
    "she had used what was left of her voice, or at what she'd said.",

    '"You can\'t. You just can\'t," her mother said. "I need you to help me with some things around '
    'the house tomorrow."',

    '"No," she signed, then shook her head. "(B32)"',

    '"You know good and well I do. There\'s cleaning to be done."',

    '"It will (G)," she said and walked out before her mother could reply.',
]

FILLS = {
    "(B29)": "I'll take it.",
    "(B30)": "Of what?",
    "(B31)": "I'll go.",
    "(B32)": "You don't.",
    "(C)": "sounded",
    "(F)": "know something about the buildings, the ones I will photograph",
    "(G)": "wait",
}

SCENES = {
    1: "場面 1 ─ 現在：下宿を見に来たクラーク氏",
    11: "場面 2 ─ 回想：10 歳での失聴と、母との衝突",
    15: "場面 3 ─ 現在：明日の外出をめぐる母との対立",
}

# ---------------------------------------------------------------- 全文 SVOCM 解析
PARAS = [
    {"no": 1, "sents": [
        {"dsl": "{M:Janey} , {S:this} {V:is} {C:Mr. Clark} .", "pat": "第2文型（SVC）",
         "tag": "呼びかけの M", "ja": "「ジェイニー、こちらがクラークさんよ。"},
        {"dsl": "{S:He} {V:'s going to take} {O:a look} ( at the room ) <under the stairs> .",
         "pat": "第3文型（SVO）", "tag": "take a look at ~",
         "notes": ["take a look が V ＋ O。at 以下は前置詞句なので O ではない。"],
         "ja": "階段下の部屋を見ていかれるの」"},
        {"dsl": "{S:Her mother} {V:spoke} {M:too slowly and carefully} , ( {接:so that} {S':Janey} "
                "{助:could} {V':be} {C':sure} ( to read each word ) ) .",
         "pat": "第1文型（SV）", "tag": "so that S can 〜（目的）",
         "notes": ["<b>so that ＋ S ＋ can/could</b>＝「S が〜できるように」。"
                   "ここが「母は娘が読唇できるようにゆっくり話す」という設定の説明になっている。"],
         "ja": "母はジェイニーが一語一語を確実に読み取れるように、あまりにゆっくりと、はっきりと話した。"},
        {"dsl": "{S:She} {V:had told} {O1:her mother} {M:many times} [O2: {接:that} {S':she} "
                "{V':didn't have to do} {O':this} ] , {接:but} {S:her mother} {M:almost always} "
                "{V:did} , ( even in front of people ) , ( to her embarrassment ) .",
         "pat": "第4文型（SVOO）＋第1文型（SV・代動詞 did）", "tag": "★代動詞 did ／ to one's 感情",
         "notes": ["tell A that 〜 は第 4 文型。O1＝her mother、O2＝that 節。",
                   "<b>her mother almost always did</b> の did は代動詞。"
                   "＝ spoke too slowly and carefully。何の代わりかを必ず口に出すこと。",
                   "<b>to her embarrassment</b>＝「彼女が恥ずかしいことに」。"
                   "to one's 感情名詞 の型（to my surprise など）。"],
         "ja": "そんなことをしなくていいと彼女は母に何度も伝えていたのに、母はほとんどいつもそうしたし、"
               "人前でさえそうするので、彼女は恥ずかしい思いをした。"},
    ]},
    {"no": 2, "sents": [
        {"dsl": "{S:Mr. Clark} {V:kept looking} ( at Janey ) {M:intently} .",
         "pat": "第1文型（SV）", "tag": "keep doing",
         "notes": ["keep doing「〜し続ける」。looking を C と取って第 2 文型と数えてもよい。"
                   "どちらで取っても <b>at Janey は前置詞句＝M</b> である点は変わらない。"],
         "ja": "クラーク氏はジェイニーをじっと見つめ続けた。"},
        {"dsl": "{M:Maybe} , ( because of the way <{S':her mother} {V':had spoken}> ) , {S:he} "
                "{V:suspected} [O: {S':she} {V':was} {C':deaf} ] .",
         "pat": "第3文型（SVO）", "tag": "the way S V（関係副詞の代用）",
         "notes": ["<b>the way ＋ S ＋ V</b>＝「S が V するやり方」。"
                   "the way の後ろは that / in which が省略された関係詞節。",
                   "suspected の O は that の省略された名詞節。"],
         "ja": "たぶん母親の話し方のせいで、彼は彼女の耳が聞こえないのではないかと感づいた。"},
        {"dsl": "{S:It} {助:would} {V:be} {C:like her mother} [真S: not to have mentioned it ] .",
         "pat": "第2文型（SVC）／ 形式主語",
         "tag": "★下線部(A) ／ It is like ＋人＋ to do",
         "notes": ["<b>It is like ＋人＋ to do</b>＝「〜するのはいかにも（その人）らしい」。"
                   "like は前置詞で、her mother がその目的語。",
                   "It は形式主語、<b>真の S は not to have mentioned it</b>。"
                   "不定詞の否定は to の直前に not を置く。",
                   "完了不定詞 to have mentioned は would be より<b>前の時</b>を表す。",
                   "<b>文末の it ＝ 直前の she was deaf</b>（彼女の耳が聞こえないということ）。設問(A)の核心。"],
         "ja": "そのことを母が言っていなかったとしたら、いかにも母らしいことだった。"},
        {"dsl": "{M:Perhaps} {S:he} {V:was waiting} ( to see [O': {接:if} {S'':she} {助:'d} "
                "{V'':speak} ] ( {接:so that} {S'':he} {助:could} {V'':confirm} {O'':his suspicion} ) ) .",
         "pat": "第1文型（SV）", "tag": "if＝「〜かどうか」",
         "notes": ["この if は<b>「もし」ではなく「〜かどうか」</b>（＝whether）。see の O′。",
                   "wait to do（〜しようと待つ）の to see 以下がすべて副詞のカタマリ。"],
         "ja": "おそらく彼は、疑いを確かめられるように、彼女が口をきくかどうかを見ようと待っていたのだ。"},
        {"dsl": "{S:She} {M:simply} {V:left} {O:her silence} {C:open} ( to interpretation ) .",
         "pat": "第5文型（SVOC）", "tag": "★leave O C",
         "notes": ["<b>leave O C</b>＝「O を C のままにしておく」。"
                   "left を「去った」と取ると O と C が宙に浮く。",
                   "open to interpretation＝「解釈に開かれた＝どうとでも取れる」。"
                   "to interpretation は<b>名詞ではなく形容詞 open にかかる</b>ので、"
                   "形容詞のカタマリ [ ] ではなく副詞のカタマリ ( ) で括ってある。"
                   "＝あえて否定も肯定もしなかった、ということ。"],
         "ja": "彼女はただ、自分の沈黙をどうとでも取れるままにしておいた。"},
    ]},
    {"no": 3, "sents": [
        {"dsl": "{助:Will} {S:you} {V:show} {O1:him} {O2:the room} ? {S:her mother} {V:said} .",
         "pat": "引用文は第4文型（SVOO）／ 地の文は第1文型（SV）", "tag": "show A B",
         "ja": "「部屋を見せてあげてくれる?」と母は言った。"},
    ]},
    {"no": 4, "sents": [
        {"dsl": "{S:She} {V:nodded} {M:again} , {接:and} {V:turned} ( {接:so that} {S':he} {助:would} "
                "{V':follow} {O':her} ) .",
         "pat": "第1文型（SV）×2", "tag": "",
         "ja": "彼女はもう一度うなずき、彼がついてくるように向きを変えた。"},
        {"dsl": "( Directly ahead {接:and} beneath a portion <of the stairs> ) {V:was} {S:a single "
                "bedroom} .",
         "pat": "第1文型（SV）★倒置（M V S）",
         "tag": "★場所を表す副詞句が文頭に出た倒置",
         "notes": ["<b>場所の副詞句が文頭に出ると S と V がひっくり返る</b>（MVS）。"
                   "Directly ahead and beneath … stairs までが M で、V が was、S が a single bedroom。",
                   "was の前に名詞が無いことが倒置の合図。"
                   "「the stairs が S」と読むと was の主語が複数形になって噛み合わない。",
                   "この型は東大が好んで出す。<b>V の前に S が見当たらなければ倒置を疑う</b>。"],
         "ja": "すぐ正面、階段の一部の下に、一人用の寝室があった。"},
        {"dsl": "{S:She} {V:opened} {O:the door} {接:and} {S:he} {V:walked} ( past her ) ( into the "
                "room ) , {V:turned} , {接:and} {V:looked} ( at her ) .",
         "pat": "第3文型（SVO）＋第1文型（SV）×3", "tag": "",
         "ja": "彼女がドアを開けると、彼は彼女の脇を通って部屋に入り、振り返って彼女を見た。"},
        {"dsl": "{S:She} {V:grew} {C:uncomfortable} ( under his gaze ) , ( {接:though} {S':she} "
                "{V':didn't feel} ( {接:as if} {S'':he} {V'':were looking} ( at her ) ( as a woman ) ) "
                ", ( the way <{S'':she} {助:might} {M'':once} {V'':have wanted}> ( {接:if} {S'':it} "
                "{V'':were} {C'':the right man} ) ) ) .",
         "pat": "第2文型（SVC）", "tag": "★grow C ／ 仮定法（as if / if it were）",
         "notes": ["<b>grow ＋ 形容詞</b>＝「（だんだん）〜になる」。become と同じ第 2 文型。"
                   "「育つ」ではない。",
                   "<b>as if he were looking</b>と<b>if it were the right man</b>はどちらも仮定法過去。"
                   "were が he / it という単数主語に付いているのが目印。",
                   "the way she might once have wanted＝「かつては望んだかもしれないような形で」。"
                   "might have done は過去の推量。"],
         "ja": "彼の視線の下で彼女は落ち着かなくなった。もっとも、相手が意中の男性であれば"
               "かつては望んだかもしれないような、女として見られている感じはしなかったのだが。"},
        {"dsl": "{S:She} {V:felt} [O: {S':she} {助:'d} {V':gone} ( past the age <for romance> ) ] .",
         "pat": "第3文型（SVO）", "tag": "that の省略",
         "ja": "恋愛をする年齢はもう過ぎてしまったと彼女は感じていた。"},
        {"dsl": "{S:It} {V:was} {C:a passing} <{S':she} {助:'d} {V':lamented} , {M':then} {V':gotten "
                "over}> .",
         "pat": "第2文型（SVC）", "tag": "★目的格の関係代名詞の省略",
         "notes": ["a passing の直後に<b>目的格の関係代名詞（which/that）が省略</b>されている。"
                   "lamented にも gotten over にも O が無いのが合図。",
                   "a passing は「過ぎ去ってしまったもの」。"
                   "get over＝「乗り越える・あきらめがつく」。"],
         "ja": "それは彼女が嘆き、そのうち乗り越えた喪失だった。"},
    ]},
    {"no": 5, "sents": [
        {"dsl": "{S:I} {V:like} {O:the room} , {S:he} {V:spelled out} ( in sign language ) .",
         "pat": "引用文は第3文型（SVO）／ 地の文は第1文型（SV）", "tag": "",
         "ja": "「この部屋が気に入りました」と彼は手話で綴った。"},
        {"dsl": "{S:I} {助:'ll} {V:take} {O:it} .", "pat": "第3文型（SVO）",
         "tag": "★空所(B29) ／ I'll take it.",
         "notes": ["<b>I'll take it.</b>＝「これにします／借ります」。店や不動産で決める決まり文句。"
                   "take の O は the room。"],
         "ja": "「借ります」"},
    ]},
    {"no": 6, "sents": [
        {"dsl": "{S:That} {V:was} {C:all} .", "pat": "第2文型（SVC）", "tag": "",
         "ja": "それだけだった。"},
        {"dsl": "{S:No conversation} , {S:no explanation} <about [ {M':how} {S':he} {助:'d} "
                "{V':known} ( for certain ) [O'': {接:that} {S'':she} {V'':was} {C'':deaf} ] ] "
                "{接:or} [ {M':how} {S':he} {助:'d} {V':learned} [O': to speak ( with his hands ) ] "
                "]> .", "frag": True,
         "pat": "省略文（There was 〜 の V が落ちた名詞句だけの文）",
         "tag": "V の無い文",
         "notes": ["主節に V が無い。<b>There was no conversation, no explanation …</b> の省略。"
                   "小説では珍しくない。「V が見当たらない＝省略」と判断できるかどうか。",
                   "about の後ろに how 節が 2 つ（or で並列）ぶら下がる。"],
         "ja": "会話もなければ、なぜ彼女の耳が聞こえないと確信できたのか、"
               "どこで手話を覚えたのかについての説明もなかった。"},
    ]},
    {"no": 7, "sents": [
        {"dsl": "{S:Janey} {V:came back} ( to her mother ) {接:and} {V:signed} {O:a question} .",
         "pat": "第1文型（SV）＋第3文型（SVO）", "tag": "sign が動詞",
         "notes": ["<b>signed は「手話で伝えた」</b>。名詞 sign（記号）ではない。"],
         "ja": "ジェイニーは母のところへ戻り、手話で質問した。"},
    ]},
    {"no": 8, "sents": [
        {"dsl": "{S:He} {V:is} {C:a photographer} , {S:she} {V:said} , ( again speaking too slowly ) .",
         "pat": "引用文は第2文型（SVC）／ 地の文は第1文型（SV）", "tag": "分詞構文（付帯状況）",
         "notes": ["again speaking too slowly は<b>分詞構文</b>。"
                   "意味上の主語は she（＝母）。「またもゆっくり話しながら」。"],
         "ja": "「あの人は写真家よ」と、母はまたゆっくりすぎるほどの話し方で言った。"},
        {"dsl": "{V:Travels} ( around the world ) ( taking pictures ) , {S:he} {V:says} .",
         "pat": "引用文は第1文型（SV）★主語の省略 ／ 地の文も第1文型（SV）", "tag": "口語での S 省略",
         "notes": ["<b>Travels の前に He が省略</b>されている。会話文でよくある省略。"
                   "動詞に -s が付いているのが三人称単数の主語がある証拠。",
                   "taking pictures は分詞構文（付帯状況）。"],
         "ja": "「世界中を回って写真を撮っているんですって」"},
    ]},
    {"no": 9, "sents": [
        {"dsl": "( Of what ) ?", "frag": True,
         "pat": "省略疑問（（Pictures）of what? の名詞が落ちた形）",
         "tag": "★空所(B30)",
         "notes": ["<b>前置詞だけを残した聞き返し</b>。"
                   "直前の taking pictures を受けて「（写真って）何の?」。",
                   "直後の母の返答が <b>Buildings.</b> であることが決め手。"
                   "「何の写真か」を尋ねたからこそ「建物よ」と答えが返る。"],
         "ja": "「何の?」"},
    ]},
    {"no": 10, "sents": [
        {"dsl": "Buildings .", "frag": True,
         "pat": "省略文（（Pictures of）buildings. の答え）", "tag": "",
         "ja": "「建物よ」"},
    ]},
    {"no": 11, "sents": [
        {"dsl": "{S:Music} {V:was} {C:her entry} <into silence> .", "pat": "第2文型（SVC）",
         "tag": "無生物主語",
         "notes": ["直訳「音楽が沈黙への入り口だった」＝「音楽をきっかけに彼女は沈黙へ入った」。"
                   "<b>無生物主語は「〜によって」と副詞的に訳す</b>と日本語が締まる。"],
         "ja": "音楽こそが、彼女が沈黙へ入っていく入り口だった。"},
        {"dsl": "{S:She} {助:'d} {V:been} {C:only ten years old} , ( sitting ( on the end <of the "
                "porch <above the steps>> ) ) , ( listening ( to the church choir ) ) .",
         "pat": "第2文型（SVC）", "tag": "分詞構文 2 つ",
         "notes": ["sitting … と listening … はどちらも分詞構文（付帯状況）。"
                   "意味上の主語はいずれも She。"],
         "ja": "彼女はまだ 10 歳で、階段の上のポーチの端に座り、教会の聖歌隊の歌に聞き入っていた。"},
        {"dsl": "{M:Then} {S:she} {V:began} [O: to feel dizzy ] , {接:and} {M:suddenly} {V:fell} "
                "{M:backwards} ( into the music ) .",
         "pat": "第3文型（SVO）＋第1文型（SV）", "tag": "",
         "notes": ["fell backwards into the music＝「音楽の中へ後ろ向きに倒れ込んだ」。"
                   "倒れた先を「音楽」と言うことで失聴の瞬間を印象づけている。"],
         "ja": "やがて彼女はめまいを感じはじめ、突然、音楽の中へ後ろ向きに倒れ込んだ。"},
    ]},
    {"no": 12, "sents": [
        {"dsl": "{S:She} {V:woke} ( into silence ) {M:nights later} , ( there ) ( in her room ) , "
                "( in her bed ) .",
         "pat": "第1文型（SV）", "tag": "",
         "ja": "何日か後の夜、彼女は沈黙の中へと目を覚ました。自分の部屋の、自分のベッドで。"},
        {"dsl": "{S:She} {助:'d} {V:called out} ( from her confusion ) ( {接:as} {S':any child} "
                "{助:would} ) , {接:and} {S:her mother} {V:was} {M:there} {M:instantly} .",
         "pat": "第1文型（SV）×2", "tag": "★代動詞 would",
         "notes": ["<b>as any child would</b> の would の後ろに call out が省略</b>されている。"
                   "「どんな子どももそうするように」。"],
         "ja": "どんな子どももそうするように、彼女は混乱の中から叫んだ。母はすぐさまそこにいた。"},
        {"dsl": "{接:But} {S:something} {V:sounded} {C:wrong} , {接:or} {助:had} {M:not} {V:sounded} "
                ", ( except inside her <{M':where} {S':illness and confusion} {V':grew}> ) .",
         "pat": "第2文型（SVC）／ 後半は第1文型（SV）",
         "tag": "★空所(C) ／ sound の 2 つの使い方",
         "notes": ["前半 <b>sounded wrong</b> は sound ＋ 形容詞（第 2 文型）＝「変な音がした」。",
                   "後半 <b>had not sounded</b> は補語なしの完全自動詞＝「音がしなかった」。"
                   "この 2 つを同じ 1 語でまかなえるのが sound の強み。",
                   "「何かが変に響いた、いや、そもそも音がしていなかった」と"
                   "<b>言い直している</b>のがこの文の骨。失聴の瞬間の描写。"],
         "ja": "だが何かが変に響いた——いや、そもそも音などしていなかったのだ。"
               "病と混乱が広がっていく彼女の内側を除いては。"},
        {"dsl": "{S:She} {V:hadn't heard} {O:herself} , {V:hadn't heard} {O:the call} <{S':she} "
                "{助:'d} {V':made}> - {同格:Mama} .",
         "pat": "第3文型（SVO）×2", "tag": "目的格の関係代名詞の省略",
         "ja": "彼女には自分の声が聞こえていなかった。自分が発した呼び声——「ママ」——が聞こえていなかった。"},
        {"dsl": "{接:And} ( {接:though} {S':her mother} {V':was already gripping} {O':her} "
                "{M':tightly} ) , {S:she} {助:'d} {V:called out} {M:again} , {接:but} ( only into "
                "silence ) , <{S':which} {V':is} [C': {M'':where} {S'':she} {V'':lived} {M'':now} ] , "
                "{V':had been living} ( for so many years {接:that} {S'':she} {V'':didn't feel} "
                "{C'':uncomfortable} ( inside its invisibility ) )> .",
         "pat": "第1文型（SV）", "tag": "★非制限用法の which ／ so 〜 that …",
         "notes": ["<b>, which の先行詞は silence</b>。「沈黙、それは今や彼女が生きる場所であり」。",
                   "which に対する V′ が <b>is</b> と <b>had been living</b> の 2 つ並んでいる"
                   "（間のコンマで並列）。",
                   "<b>so many years that …</b>＝「あまりに長い年月なので…」。"
                   "for so many years の so と that が呼応する。"],
         "ja": "母がすでに強く抱きしめてくれていたのに、彼女はもう一度叫んだ。"
               "だがそれは沈黙の中へ消えるだけだった。その沈黙こそ今や彼女が生きる場所であり、"
               "あまりに長くそこに住んできたので、その見えなさの中にいても居心地の悪さを感じないほどだった。"},
        {"dsl": "{M:Sometimes} {S:she} {V:thought} [O: {S':it} {V':saved} {O':her} , {V':gave} "
                "{O1':her} {O2':a separate place} <to withdraw into> ( {接:as far as} {S'':she} "
                "{助:might} {V'':need} ) ( at any given moment ) ] - {接:and} {M:there} {V:were} "
                "{S:moments} .",
         "pat": "第3文型（SVO）／ O の中は SVO ＋ 第4文型（SVOO）／ 文末は There 構文",
         "tag": "★下線部(D) ／ 前置詞で終わる関係詞句",
         "notes": ["<b>a separate place to withdraw into</b>＝「引きこもるための、別の場所」。"
                   "into の目的語が place（withdraw into the place）。"
                   "<b>前置詞で終わっていたら、その目的語が前にある</b>。",
                   "there were moments の there は M、moments が S（There 構文）。",
                   "ダッシュ以下は「（引きこもる必要が生じる）瞬間は、実際にあったのだ」と念を押す。"
                   "設問(D)はこの moments に続く節を補う問題。"],
         "ja": "沈黙が自分を救ってくれたのだ、と彼女は思うことがあった。"
               "沈黙はいつであれ必要なだけ引きこもれる、自分だけの場所を与えてくれた——"
               "そして、その必要が生じる瞬間は確かにあったのだ。"},
    ]},
    {"no": 13, "sents": [
        {"dsl": "{S:The floor} {助:had} {M:always} {V:carried} {O:her mother's anger} .",
         "pat": "第3文型（SVO）", "tag": "無生物主語",
         "notes": ["「床が母の怒りを運んだ」＝<b>母の怒りは床の振動として伝わってきた</b>。"
                   "耳が聞こえない主人公にとって振動が情報源であることを示す一文。"],
         "ja": "床はいつも母の怒りを伝えてきた。"},
        {"dsl": "{S:She} {助:'d} {V:learned} {O:this} {M:first} ( as little girl ) ( {接:when} "
                "{S':her mother and father} {V':argued} ) .",
         "pat": "第3文型（SVO）", "tag": "",
         "notes": ["※配布プリントは as little girl だが、本来は <b>as a little girl</b>（冠詞 a が必要）。"
                   "原文の印字どおりに載せてある。"],
         "ja": "幼い少女だったころ、両親が言い争うのを通して、彼女は最初にそれを学んだ。"},
        {"dsl": "{S:Their words} {助:might} {M:not} {V:have existed} ( as sound ) ( for her ) , "
                "{接:but} {S:anger} {M:always} {V:caused} {O:its own vibration} .",
         "pat": "第1文型（SV）＋第3文型（SVO）", "tag": "might not have done",
         "notes": ["<b>might not have existed</b>＝「存在していなかったかもしれない」（過去への推量）。",
                   "「言葉は音としては彼女に届かなかったが、怒りは振動を生んだ」"
                   "＝内容ではなく感情だけが伝わる、という対比。"],
         "ja": "両親の言葉は彼女にとって音としては存在しなかったかもしれない。"
               "だが怒りはいつも、それ自体の振動を生んだ。"},
    ]},
    {"no": 14, "sents": [
        {"dsl": "{S:She} {V:hadn't been} {M:exactly} {C:sure} [ {M':why} {S':they} {V':argued} "
                "( all those years ago ) ] , {接:but} {V:sensed} , ( the way <{S':a child} "
                "{助:will}> ) , [O: {接:that} {S':it} {V':was} {M':usually} {C':about her} ] .",
         "pat": "第2文型（SVC）＋第3文型（SVO）",
         "tag": "★挿入で V と O が切り離される ／ 習性の will",
         "notes": ["but の後ろの V は <b>sensed</b>。その O は文末の that 節。"
                   "間に , the way a child will , が<b>挿入</b>されているので離れている。",
                   "<b>the way a child will</b> の will は「〜するものだ」という<b>習性の will</b>。"
                   "後ろに sense が省略されている。「子どもがそうであるように、感じ取っていた」。",
                   "be sure why 〜 は be sure of 〜 の of が落ちた形。"],
         "ja": "なぜ両親があの頃言い争っていたのか、彼女にははっきりとは分からなかった。"
               "だが子どもというものがそうであるように、たいていは自分のことなのだと感じ取っていた。"},
        {"dsl": "( One day ) {S:her mother} {V:found} {O:her} {C:playing} ( in the woods <behind "
                "their house> ) , {接:and} ( {接:when} {S':she} {助:wouldn't} {V':follow} {O':her "
                "mother} {M':home} ) , {S:her mother} {V:grabbed} {O:her} ( by the arm ) {接:and} "
                "{V:dragged} {O:her} ( through the trees ) .",
         "pat": "第5文型（SVOC）＋第3文型（SVO）×2",
         "tag": "★find O C ／ 動詞＋A＋by the＋体の部位",
         "notes": ["<b>find O C</b>（第 5 文型）＝「O が C しているのを見つける」。"
                   "playing 以下は her を説明する C。「森で遊んでいる彼女を見つけた」。",
                   "<b>grab A by the arm</b>＝「A の腕をつかむ」。"
                   "英語は「人」を O にして、部位は by the 〜 で示す。"
                   "grab her arm ではなく grab her by the arm。",
                   "wouldn't は「どうしても〜しようとしなかった」（拒絶の would の否定）。"],
         "ja": "ある日、母は家の裏の森で遊んでいる彼女を見つけた。彼女がどうしても母について帰ろうと"
               "しなかったので、母は彼女の腕をつかみ、木々の間を引きずっていった。"},
        {"dsl": "{S:She} {M:finally} {V:pulled back} {接:and} {V:shouted} ( at her mother ) , "
                "( not in words {接:but} in a scream <{S':that} {V':expressed} {O':all} <{S'':she} "
                "{V'':felt}> ( in one great vibration )> ) .",
         "pat": "第1文型（SV）×2", "tag": "★not A but B",
         "notes": ["<b>not A but B</b>＝「A ではなく B」。"
                   "A ＝ in words、B ＝ in a scream。どちらも shouted にかかる副詞句。",
                   "all の後ろに<b>目的格の関係代名詞が省略</b>（all (that) she felt）。"],
         "ja": "とうとう彼女は身を引き、母に向かって叫んだ。言葉によってではなく、"
               "感じていたすべてを一つの大きな振動にして吐き出す悲鳴によって。"},
        {"dsl": "{S:Her mother} {V:slapped} {O:her} {M:hard} ( across her face ) .",
         "pat": "第3文型（SVO）", "tag": "hard は副詞",
         "notes": ["<b>hard は「強く」という副詞</b>。hardly（ほとんど〜ない）とは別語。"],
         "ja": "母は彼女の頬を強くぶった。"},
        {"dsl": "{S:She} {V:saw} {O:her mother} {C:shaking} {接:and} {V:knew} [O: {S':her mother} "
                "{V':loved} {O':her} ] , {接:but} {S:love} {V:was} {M:sometimes} {C:like silence} , "
                "{同格:beautiful but hard to bear} .",
         "pat": "第5文型（SVOC）＋第3文型（SVO）＋第2文型（SVC）",
         "tag": "★知覚動詞 see O C",
         "notes": ["<b>see O ＋ 現在分詞</b>＝「O が〜しているのを見る」（第 5 文型）。"
                   "shaking は her mother の状態を説明する C。",
                   "beautiful but hard to bear は silence の言い換え（同格）。"
                   "<b>この一文が母子関係の要約</b>。設問(E)の背景になる。"],
         "ja": "母が震えているのを見て、母が自分を愛しているのだと彼女は分かった。"
               "だが愛は時に沈黙に似ていた。美しいけれど、耐えるのが苦しいのだ。"},
        {"dsl": "{S:Her father} {V:told} {O1:her} , [O2: {S':She} {助:can't} {V':help} "
                "{O':herself} ] .",
         "pat": "第4文型（SVOO）",
         "tag": "★下線部(E) ／ can't help oneself",
         "notes": ["<b>can't help oneself</b>＝「自分を抑えられない・どうしようもない」。"
                   "この help は「助ける」ではなく<b>「避ける・こらえる」</b>"
                   "（cannot help doing の help と同じ）。",
                   "told の O2 が引用文まるごと。引用文自体は S V O の第 3 文型。",
                   "<b>her（O1）＝ジェイニー、She（引用文の S）＝母親</b>。"
                   "同じ女性の代名詞が入り混じるので、指示対象を必ず確定させること。"],
         "ja": "父は彼女に言った。「母さんは自分ではどうしようもないんだ」"},
    ]},
    {"no": 15, "sents": [
        {"dsl": "{M:Weeks later} , {S:Mr. Clark} {V:said} ( to Janey ) , [O: {S':You} {助:might} "
                "{V':be able to help} {O':me} ] .",
         "pat": "第3文型（SVO）", "tag": "say to 人（第4文型にはならない）",
         "notes": ["<b>say は第 4 文型を作らない</b>。「人に」は to 人 で表す。"
                   "tell 人 that 〜 との違いに注意。",
                   "said の O は引用文まるごと（〈 〉 の中）。引用文自体は S V O の第 3 文型。"],
         "ja": "数週間後、クラーク氏はジェイニーに言った。「手を貸してもらえるかもしれません」"},
    ]},
    {"no": 16, "sents": [
        {"dsl": "( {接:If} {S':I} {助:can} ) , {S:she} {V:spelled} ( with her fingers ) .",
         "pat": "第1文型（SV）", "tag": "if 節の中の省略",
         "notes": ["If I can の後ろに help you が省略されている。"],
         "ja": "「できることなら」と彼女は指で綴った。"},
    ]},
    {"no": 17, "sents": [
        {"dsl": "{S:I} {助:'ll} {V:need} [O: to know {O':something} ( about the buildings ) ] , "
                "{同格:the ones} <{S':I} {助:will} {V':photograph} {M':tomorrow}> .",
         "pat": "第3文型（SVO）", "tag": "★空所(F) ／ 同格のコンマ",
         "notes": ["need to do の to の後ろは<b>動詞の原形</b>。"
                   "与えられた語のうち原形で置けるのは know だけ（photograph は will と組む）。",
                   "<b>the ones ＝ the buildings の言い換え（同格）</b>。"
                   "だから設問は「どこか 1 か所にコンマ」と指定している。",
                   "the ones の後ろに目的格の関係代名詞が省略。"
                   "tomorrow は空所の外の語で、photograph にかかる。"],
         "ja": "「明日撮る建物について、少し知っておく必要があるんです。"},
        {"dsl": "{M:Maybe} {S:you} {助:can} {V:tell} {O1:me} {O2:some history} <about them> .",
         "pat": "第4文型（SVOO）", "tag": "tell A B",
         "notes": ["<b>them ＝ the buildings</b>。空所(F)に buildings が入る決め手になる。"],
         "ja": "その由来を教えてもらえるかもしれない」"},
    ]},
    {"no": 18, "sents": [
        {"dsl": "{S:She} {V:nodded} {接:and} {V:felt} {C:glad} ( to be needed ) , {C:useful} "
                "( in some small way ) .",
         "pat": "第1文型（SV）＋第2文型（SVC）", "tag": "感情の原因を表す不定詞",
         "notes": ["felt の C は glad と useful の 2 つ（コンマで並列）。",
                   "to be needed は<b>感情の原因</b>を表す副詞用法「必要とされて（嬉しい）」。受動の不定詞。"],
         "ja": "彼女はうなずき、必要とされることを、ささやかながら役に立てることを嬉しく思った。"},
        {"dsl": "{M:Then} {S:Mr. Clark} {V:asked} {O:her} [C: to accompany him ( to the old house "
                "<at the top <of Oakhill>> ) ] .",
         "pat": "第5文型（SVOC）", "tag": "ask O to do",
         "notes": ["<b>ask O to do</b>＝「O に〜するよう頼む」。to accompany 以下が C。",
                   "accompany は他動詞なので前置詞は不要（accompany him）。"],
         "ja": "それからクラーク氏は、オークヒルの丘の上にある古い家まで一緒に来てほしいと彼女に頼んだ。"},
        {"dsl": "{S:You} {助:might} {V:enjoy} {O:that} .", "pat": "第3文型（SVO）", "tag": "",
         "ja": "「きっと楽しいですよ。"},
        {"dsl": "{S:Some time} <away from here> .", "frag": True,
         "pat": "省略文（It would be 〜 の V が落ちた名詞句）", "tag": "",
         "ja": "ここを少し離れてね」"},
    ]},
    {"no": 19, "sents": [
        {"dsl": "{S:She} {V:looked} ( toward the kitchen door ) , ( not aware ( at first ) "
                "[ {M':why} {S':she} {V':turned} {M':that way} ] ) .",
         "pat": "第1文型（SV）", "tag": "分詞構文（being の省略）",
         "notes": ["not aware … は <b>(being) not aware …</b> の being が省略された分詞構文。"
                   "意味上の主語は She。"],
         "ja": "彼女は台所の扉のほうを見た。なぜそちらを向いたのか、初めは自分でも分かっていなかった。"},
        {"dsl": "{M:Perhaps} {S:she} {V:understood} , ( on some unconscious level ) , [O: {O':what} "
                "{S':she} {V':hadn't} ( a moment before ) ] .",
         "pat": "第3文型（SVO）", "tag": "★代動詞的な省略",
         "notes": ["<b>what she hadn't</b> の後ろに understood が省略</b>されている。"
                   "「ほんの少し前には分かっていなかったこと」。",
                   "V（understood）と O（what 節）の間に , on some unconscious level , が挿入。"],
         "ja": "おそらく彼女は、意識のどこか深いところで、ほんの少し前には分かっていなかったことを"
               "理解したのだ。"},
        {"dsl": "{S:Her mother} {V:was standing} {M:there} .", "pat": "第1文型（SV）", "tag": "",
         "ja": "母がそこに立っていた。"},
        {"dsl": "{S:She} {助:'d} {V:been listening} ( to him ) .", "pat": "第1文型（SV）",
         "tag": "過去完了進行形",
         "notes": ["<b>had been listening</b>＝「（ずっと）聞いていた」。"
                   "娘が気づく前から聞いていた、という時間の前後関係を出している。"],
         "ja": "母はずっと彼の話を聞いていたのだ。"},
    ]},
    {"no": 20, "sents": [
        {"dsl": "( {接:When} {S':Janey} {V':turned back} ( to him ) ) , {S:she} {V:read} {O:his "
                "lips} .", "pat": "第3文型（SVO）", "tag": "read one's lips（読唇）",
         "ja": "ジェイニーが彼のほうへ向き直ると、彼女は彼の唇を読んだ。"},
        {"dsl": "{M:Why} {助:don't} {S:you} {V:go} ( with me ) {M:tomorrow} ?",
         "pat": "第1文型（SV）", "tag": "Why don't you 〜?（勧誘）",
         "notes": ["<b>Why don't you 〜?</b> は「なぜ〜しないのか」ではなく<b>「〜しませんか」という誘い</b>。"],
         "ja": "「明日、一緒に行きませんか?」"},
    ]},
    {"no": 21, "sents": [
        {"dsl": "{S:She} {V:felt} {O:the quick vibration} <of her mother's approach> .",
         "pat": "第3文型（SVO）", "tag": "",
         "notes": ["母が近づくのを<b>振動で</b>感じ取る。第 13 段落の「床が母の怒りを運ぶ」と対応。"],
         "ja": "母が近づいてくる素早い振動を彼女は感じた。"},
        {"dsl": "{S:She} {V:turned} ( to her mother ) , {接:and} {V:saw} {O:her mother's anger and "
                "fear} , ( the way <{S':she} {助:'d} {M':always} {V':seen} {O':them}> ) .",
         "pat": "第1文型（SV）＋第3文型（SVO）", "tag": "the way S V",
         "ja": "彼女は母のほうを向き、いつもそう見てきたとおりに、母の怒りと恐れを見た。"},
        {"dsl": "{S:Janey} {V:drew in} {O:her breath} {接:and} {V:forced} {O:the two breath-filled "
                "words} {M:out} ( in a harsh whisper <{S':that} {助:might} {V':have sounded} , "
                "( for all she knew ) , {C':like a sick child or someone dying}> ) : {S:she} "
                "{V:said} , [O: {S':I} {助:'ll} {V':go} ] .",
         "pat": "第3文型（SVO）×3",
         "tag": "★空所(C)(B31) ／ force O out ／ for all she knew",
         "notes": ["コロン以下 she said の O が引用文 [ I'll go ]。引用文自体は S V の第 1 文型。",
                   "<b>forced … out</b>＝「（声を）無理やり押し出した</b>」。"
                   "O が長いので out が後ろに回っている（force out ＋ O の分離）。",
                   "<b>the two breath-filled words</b>＝「息だけでできた 2 語」。"
                   "空所(B31)が<b>2 語</b>でなければならない決定的な根拠。I'll ＋ go で 2 語。",
                   "<b>for all she knew</b>＝「彼女の知る限りでは・ひょっとしたら」。挿入。",
                   "that … の C′ が like a sick child or someone dying なので、"
                   "空所(C)は<b>「〜のように聞こえる」を作れる語</b>でなければならない。"],
         "ja": "ジェイニーは息を吸い込み、息だけでできた 2 語を、"
               "彼女の知る限りでは病気の子どもか死にかけた人のように聞こえたかもしれない"
               "かすれたささやき声で、無理やり押し出した。彼女は言った。「私は行く」"},
    ]},
    {"no": 22, "sents": [
        {"dsl": "{S:Her mother} {V:stared} ( at her ) ( in surprise ) , {接:and} {S:Janey} "
                "{V:wasn't} {C:sure} [ {接:if} {S':her mother} {V':was} {C':more shocked} "
                "[ {接:that} {S'':she} {V'':had used} [O'': {S'':what} {V'':was left} ( of her "
                "voice ) ] ] , {接:or} ( at [ {O'':what} {S'':she} {助:'d} {V'':said} ] ) ] .",
         "pat": "第1文型（SV）＋第2文型（SVC）", "tag": "★shocked that 〜 or at 〜 の並列",
         "notes": ["<b>more shocked that 〜, or at 〜</b>＝「〜ということにより衝撃を受けたのか、"
                   "それとも〜に受けたのか」。shocked は that 節でも at 〜 でも理由を取れる。"
                   "<b>並列されているのは that 節と at 句</b>で、形が違うので見抜きにくい。",
                   "<b>what was left of her voice</b>＝「彼女の声のうち残っていたもの」。"
                   "leave の受動で「残される」。",
                   "この if も「〜かどうか」。"],
         "ja": "母は驚いて彼女を見つめた。ジェイニーには、母がより衝撃を受けたのが、"
               "自分に残っていた声を娘が使ったことなのか、それとも娘が言った内容のほうなのか、"
               "分からなかった。"},
    ]},
    {"no": 23, "sents": [
        {"dsl": "{S:You} {助:can't} .", "frag": True,
         "pat": "省略文（can't の後ろに go が落ちている）", "tag": "",
         "notes": ["<b>You can't (go).</b> 直前のジェイニーの I'll go. を受けての制止。"
                   "ここが空所(B31)を I'll go. と決める根拠になる。"],
         "ja": "「だめよ。"},
        {"dsl": "{S:You} {M:just} {助:can't} , {S:her mother} {V:said} .",
         "pat": "省略文＋第1文型（SV）", "tag": "", "ja": "とにかくだめ」と母は言った。"},
        {"dsl": "{S:I} {V:need} {O:you} [C: to help me ( with some things <around the house> ) "
                "{M':tomorrow} ] .",
         "pat": "第5文型（SVOC）", "tag": "need O to do",
         "notes": ["<b>need O to do</b>＝「O に〜してもらう必要がある」。"
                   "to help 以下が C。ここが空所(B32)の You don't. が受ける内容。"],
         "ja": "「明日は家のことをいくつか手伝ってもらう必要があるの」"},
    ]},
    {"no": 24, "sents": [
        {"dsl": "{M:No} , {S:she} {V:signed} , {M:then} {V:shook} {O:her head} .",
         "pat": "第1文型（SV）＋第3文型（SVO）", "tag": "",
         "ja": "「いいえ」と彼女は手話で示し、それから首を横に振った。"},
        {"dsl": "{S:You} {助:don't} .", "frag": True,
         "pat": "省略文（don't の後ろに need me が落ちている）",
         "tag": "★空所(B32)",
         "notes": ["<b>You don't (need me).</b> 母の I need you to help me … を否定している。",
                   "直後の母の返答 <b>You know good and well I do.</b> の <b>I do ＝ I do need you</b> と"
                   "鏡合わせになっているのが決め手。"],
         "ja": "「必要ないでしょ」"},
    ]},
    {"no": 25, "sents": [
        {"dsl": "{S:You} {V:know} {M:good and well} [O: {S':I} {V':do} ] .",
         "pat": "第3文型（SVO）", "tag": "★強調の代動詞 do",
         "notes": ["<b>I do ＝ I do need you</b>。娘の You don't. を打ち返す代動詞。",
                   "good and well は口語で「重々・よくよく」。"],
         "ja": "「必要なのは重々分かっているでしょう。"},
        {"dsl": "{M:There} {V:'s} {S:cleaning} <to be done> .",
         "pat": "第1文型（SV）★There 構文", "tag": "受動の不定詞",
         "notes": ["<b>to be done</b>（受動の不定詞）＝「されるべき」。"
                   "cleaning を後ろから修飾する形容詞用法。"],
         "ja": "掃除をしないといけないんだから」"},
    ]},
    {"no": 26, "sents": [
        {"dsl": "{S:It} {助:will} {V:wait} , {S:she} {V:said} {接:and} {V:walked out} ( {接:before} "
                "{S':her mother} {助:could} {V':reply} ) .",
         "pat": "引用文は第1文型（SV）／ 地の文は第1文型（SV）×2",
         "tag": "★空所(G) ／ 物を主語にした wait",
         "notes": ["<b>It will wait.</b>＝「それは後回しでいい・急がない」。"
                   "wait は「（物事が）待てる」の意味で無生物を主語に取れる。It ＝ the cleaning。",
                   "before her mother could reply＝「母が言い返す前に」＝言い切って出ていった。"],
         "ja": "「それは後でいい」と彼女は言い、母が言い返す前に部屋を出ていった。"},
    ]},
]

# ---------------------------------------------------------------- 設問 (A)〜(G)
# 解説フォーマットは server/main.py の生成プロンプトが正典（🎯→🔬→📍→❌ の4セクション必須）。
# 記述問題には誤答選択肢が無いので、4 つ目は「よくある誤り」として同じ位置に置く。
QUESTIONS = [
    {
        "no": "(A)", "kind": "和訳",
        "q": "下線部 (A) を、文末の it の内容がわかるように訳せ。",
        "target": "It would be like her mother not to have mentioned it.",
        "ans": "自分（ジェイニー）の耳が聞こえないということを母がクラーク氏に伝えていなかった"
               "のだとしたら、それはいかにも母親らしいふるまいだった。",
        "ansnote": "「it ＝ 彼女が耳が聞こえないということ」を訳文の中に必ず出すこと。"
                   "「そのこと」で済ませると設問の指示に答えたことにならない。",
        "core": [
            "<b>It is like ＋人＋ to do</b>＝「〜するのはいかにも（その人）らしい」。"
            "この like は動詞「好き」ではなく<b>前置詞</b>で、コアは「〜に似ている」→「その人の性分に合う」。",
            "<b>would</b> は「（もしそうなら）〜だろう」という控えめな推量。"
            "ジェイニーが確かめたわけではなく、母ならやりそうだと推し量っている。",
            "<b>完了不定詞 to have mentioned</b> は述語動詞（would be）より<b>前の時</b>を表す。"
            "「（すでに）言っていなかった」。",
        ],
        "struct": [
            "主節: S＝It（形式主語） / 助＝would / V＝be / C＝like her mother",
            "真S＝〈 not to have mentioned it 〉（不定詞句）── It が指す中身はこれ",
            "・like は前置詞、her mother がその目的語",
            "・not は to have mentioned を否定（不定詞の否定は to の直前）",
            "・mentioned の O＝it ← <b>これが設問の問う it</b>",
            "文末の it ＝ 直前の文の she was deaf（彼女の耳が聞こえないということ）",
        ],
        "evidence": [
            ("he suspected she was deaf",
             "直前の文。it が受ける内容はここ。母が伝えていれば「感づく」必要がない。"),
            ("No conversation, no explanation about how he'd known for certain that she was deaf",
             "第 6 段落。母が説明していなかったことが後から裏づけられる。"),
            ("Her mother spoke too slowly and carefully, so that Janey could be sure to read each word.",
             "第 1 段落。母は「耳が聞こえない」と口で言わず、態度で示してしまう人物。"),
        ],
        "ng": [
            "文末の it を「そのこと」とだけ訳す → 設問が「it の内容がわかるように」と指定している。ここが配点。",
            "like を動詞「好きだ」と取る → It would be like 〜 の like は前置詞。V は be。",
            "not の作用範囲を誤り「母親らしくない」と訳す → not がかかるのは to have mentioned。"
            "「言わずにおくのが母らしい」。",
            "would を単なる過去形と見て断定的に訳す → 推量の would。「〜だろう／〜のようだった」。",
        ],
    },
    {
        "no": "(B)", "kind": "空所補充（記号・重複不可）",
        "q": "空所 (B29)〜(B32) を埋めるのに最も適切な表現を選べ。同じ記号を複数回用いてはならない。",
        "target": "a) I'll go.  b) I can't.  c) I won't.  d) Of what?  e) I'll take it.  "
                  "f) You don't.  g) Don't you dare.",
        "ans": "(B29) e)　(B30) d)　(B31) a)　(B32) f)",
        "ansnote": "使わないのは b) I can't. / c) I won't. / g) Don't you dare. の 3 つ。",
        "core": [
            "<b>take it</b> のコアは「それを受け取る」→ 店や不動産で<b>「これにします」</b>。",
            "<b>Of what?</b> は Pictures of what? の名詞が落ちた聞き返し。"
            "<b>前置詞だけを残して問い返す</b>のは会話文の定番。",
            "<b>You don't. / I do.</b> は<b>代動詞</b>。後ろの動詞句をまるごと受ける。"
            "何を受けているかを毎回言えるようにする。",
        ],
        "struct": [
            "(B29) S＝I / 助＝'ll / V＝take / O＝it（第3文型）　it ＝ the room",
            "(B30) 省略疑問。（Pictures）of what?　── of の目的語だけを問う",
            "(B31) S＝I / 助＝'ll / V＝go（第1文型）　── I'll ＋ go で<b>ちょうど 2 語</b>",
            "(B32) S＝You / 助＝don't（以下省略）　＝ You don't need me to help you.",
        ],
        "evidence": [
            ("I like the room",
             "(B29) の直前。気に入った → 次に来るのは契約の一言。直後が That was all.（それだけ）"
             "なので、交渉も説明もない短い決定文が入る。"),
            ("Travels around the world taking pictures, he says.",
             "(B30) の直前。写真を撮っている、と聞いた直後の聞き返し。"),
            ("Buildings.",
             "(B30) の直後。「建物よ」と答えが返る＝「何の（写真）?」と尋ねたことが確定する。"),
            ("forced the two breath-filled words out",
             "(B31) の直前。<b>2 語</b>と明記されている。I'll go. が 2 語。"),
            ("Why don't you go with me tomorrow?",
             "(B31) の直前のクラーク氏の誘い。これに答える形。"),
            ("You can't. You just can't,",
             "(B31) の直後の母の制止。「行く」と言ったからこそ「だめ」と返る。"),
            ("I need you to help me with some things around the house tomorrow.",
             "(B32) の直前。これを否定するのが You don't."),
            ("You know good and well I do.",
             "(B32) の直後。<b>I do ＝ I do need you</b>。You don't. と鏡合わせになっている。"),
        ],
        "ng": [
            "b) I can't. を (B31) に入れる → 直後の母の You can't. が意味をなさない"
            "（本人がすでに「できない」と言っているのに制止する理由がない）。",
            "c) I won't. を (B31) に入れる → 同上。また母が驚いた理由（声を出してまで言った内容）"
            "が「行かない」では、その後の口論に発展しない。",
            "g) Don't you dare.（やめておきなさい）は母の側の台詞。"
            "ジェイニーの発話位置には入らないうえ、直後の会話の流れとも噛み合わない。",
            "(B29) に a) I'll go. → 部屋を見に来た場面。go では「借りる」意思が伝わらず、"
            "直後の That was all. の「それだけ」と噛み合わない。",
            "(B32) に b) I can't. → 母の I do（＝I do need you）が受けるものが無くなる。"
            "否定されているのは「私が必要かどうか」であって、娘の能力ではない。",
        ],
    },
    {
        "no": "(C)", "kind": "空所補充（3 か所に同じ 1 語）",
        "q": "本文中に 3 か所ある空所 (C) にはいずれも同じ単語が入る。最も適切な単語を選べ。"
             "　a) ended　b) gone　c) seemed　d) sounded　e) went",
        "target": "① something (C) wrong　② or had not (C)　③ a harsh whisper that might have (C), "
                  "for all she knew, like a sick child or someone dying",
        "ans": "d) sounded",
        "ansnote": "3 か所すべてに同じ語が入るので、①②③ の<b>どれか 1 つでも通らない語は即消える</b>。"
                   "先に②の形（過去分詞）で 2 語まで絞ってから、①③の意味で決めるのが速い。",
        "core": [
            "<b>sound</b> のコアは「音が出る／音として届く」。そこから 2 つの使い方が出る。"
            "(1) sound ＋ 形容詞／like ＋ 名詞＝「〜に聞こえる」（第2文型）"
            "(2) 補語なしで「音がする」（完全自動詞）。",
            "★<b>「音がする」という自動詞用法を持つのは sound だけ</b>。seem は必ず補語を要求するので、"
            "②を seemed にすると直前の wrong を補って読むしかなく、"
            "「変に思えた、いや変に思えなかった」と<b>自家撞着する</b>。ここが本問の分かれ目。",
            "②が <b>had not ＋ (C)</b> なので、入る語は<b>過去分詞</b>。"
            "①は裸で使われているので<b>過去形</b>。よって<b>過去形と過去分詞が同形</b>の語に限られる。",
        ],
        "struct": [
            "① But something sounded wrong ── S＝something / V＝sounded / C＝wrong（第2文型）",
            "② or had not sounded ── 助＝had not / V＝sounded（補語なしの第1文型）",
            "　※ ①②は「変に響いた、いや、そもそも音などしなかった」という<b>言い直し</b>",
            "③ a harsh whisper [ that might have sounded, for all she knew, like a sick child or "
            "someone dying ]",
            "　S'＝that（先行詞 a harsh whisper） / 助＝might have / V'＝sounded / "
            "C'＝like a sick child or someone dying（第2文型）",
        ],
        "evidence": [
            ("She hadn't heard herself, hadn't heard the call she'd made - Mama.",
             "①②の直後。<b>音が届かなかった</b>場面だと確定する。"),
            ("except inside her where illness and confusion grew",
             "②の続き。「彼女の内側を除いては（何も音がしなかった）」。"
             "except が効くのは「音がしなかった」という否定文に対してである。"),
            ("Janey drew in her breath and forced the two breath-filled words out in a harsh whisper",
             "③の直前。whisper（ささやき声）が何に<b>聞こえた</b>かを述べる場面。"),
        ],
        "ng": [
            "a) ended → ③ might have ended like a sick child が意味を成さない。"
            "①も something ended wrong では wrong を C に取れない。",
            "b) gone → ① something gone wrong は述語動詞が無く文にならない"
            "（had gone なら可だが①に助動詞は無い）。",
            "c) seemed → <b>最大の罠</b>。①③は形の上では通ってしまう。決め手は②で、"
            "seem は補語を省略できないので had not seemed は直前の wrong を補って読むしかなく、"
            "「変に思えた、いや変に思えなかった」と自家撞着する。"
            "sounded なら「音がしなかった」という別の意味になり、直後の "
            "She hadn't heard herself（自分の声が聞こえなかった）と噛み合う。"
            "③も for all she knew（自分では聞こえないので分からないが）が<b>聴覚</b>の話だと示している。",
            "e) went → ② had not <u>went</u> が不可（過去分詞は gone）。"
            "「3 か所に同じ 1 語」という条件で落ちる。",
        ],
    },
    {
        "no": "(D)", "kind": "内容補充（選択）",
        "q": "下線部 (D) の後にさらに言葉を続けるとしたら、次のうちどれが最も適切か。"
             "　a) given her when needed　b) when she didn't feel uncomfortable　"
             "c) when her mother would not let her go　d) when she needed to retreat into silence",
        "target": "and there were moments",
        "ans": "d) when she needed to retreat into silence",
        "ansnote": "moments（瞬間）にかかる<b>関係副詞 when の節</b>を補う問題。"
                   "「どんな瞬間か」は直前の as far as she might need が答えている。",
        "core": [
            "<b>moment</b> は「時・瞬間」なので、後ろに続く修飾節は <b>when 〜</b> になる。"
            "選択肢の形（when で始まるか）だけで a) は落ちる。",
            "<b>withdraw into ＝ retreat into</b>。どちらも「〜へ引きこもる」。"
            "本文の言い換えを選ばせる典型。",
            "ダッシュ（-）は<b>直前の内容に念を押す</b>働き。"
            "「必要なだけ引きこもれる場所があった──そして実際、その必要がある瞬間はあったのだ」。",
        ],
        "struct": [
            "Sometimes she thought 〈 it saved her, gave her a separate place to withdraw into "
            "as far as she might need at any given moment 〉",
            "　主節: S＝she / V＝thought / O＝〈 〉（that 省略）",
            "　〈 〉 の中: S'＝it（＝silence） / V'＝saved / O'＝her ／ V'＝gave / O1'＝her / "
            "O2'＝a separate place",
            "　[ to withdraw into ] ← a separate place を修飾（into の目的語が place）",
            "and there were moments ── M＝there / V＝were / S＝moments（There 構文）",
            "補うのは moments を後ろから修飾する [ when 節 ]",
        ],
        "evidence": [
            ("gave her a separate place to withdraw into as far as she might need at any given moment",
             "直前。<b>withdraw into（引きこもる）</b>と <b>she might need（必要になる）</b>の 2 語が"
             "そのまま d) の needed to retreat into silence に対応する。"),
            ("and there were moments",
             "「（引きこもる必要が生じる）瞬間は実際にあった」。"
             "この後の母との衝突の回想が、その具体例として続く。"),
            ("Her mother slapped her hard across her face.",
             "第 14 段落。実際に「引きこもる必要が生じた瞬間」の中身。"),
        ],
        "ng": [
            "a) given her when needed → when で始まる節になっておらず moments を修飾できない。"
            "内容も直前の gave her 〜 の繰り返しで、新しい情報が無い。",
            "b) when she didn't feel uncomfortable → 本文の she didn't feel uncomfortable inside "
            "its invisibility は「沈黙の中に居続けた結果、居心地の悪さを感じない」という話。"
            "「引きこもる必要が生じた瞬間」とは<b>逆向き</b>。",
            "c) when her mother would not let her go → 補うべきは「<b>沈黙へ引きこもる必要が生じた</b>瞬間」。"
            "これは母が行かせてくれない<b>状況</b>を述べているだけで、直前の "
            "withdraw into … as far as she might need の言い換えになっていない。"
            "特定の一場面に限定してしまう点も、at any given moment（いつであれ）という"
            "一般化と噛み合わない。",
        ],
    },
    {
        "no": "(E)", "kind": "内容説明（記述）",
        "q": "下線部 (E) の内容を、She が誰を指すか、また She のどのような行動を指して言っているのか"
             "わかるように説明せよ。",
        "target": '"She can\'t help herself."',
        "ans": "She はジェイニーの母親を指す。母は娘への愛情の裏返しである不安や怒りを自分では"
               "抑えることができず、森から帰ろうとしない娘の腕をつかんで木々の間を引きずったり、"
               "娘の頬を強くぶったりしてしまう。父は、そうした激しい振る舞いは母がわざとやっている"
               "のではなく、自分でもどうしようもないのだ、と娘に説明している。",
        "ansnote": "①She＝母親 ②具体的な行動（引きずる・ぶつ）③「抑えられない」という含み"
                   "──の 3 点を必ず入れる。行動を書かずに「感情的になること」で済ませると"
                   "設問の「どのような行動を指して」に答えていない。",
        "core": [
            "<b>can't help oneself</b>＝「自分を抑えられない・どうしようもない」。"
            "この help のコアは<b>「避ける・こらえる」</b>（cannot help doing の help と同じ）で、"
            "「助ける」ではない。",
            "<b>代名詞の切り分けが本問の本体</b>。この段落には her（＝ジェイニー）、"
            "her mother、She が入り混じる。父が<b>娘に向かって</b>語っている場面なので、"
            "話題の第三者＝母親。",
        ],
        "struct": [
            "Her father told her, \"She can't help herself.\"",
            "　主節: S＝Her father / V＝told / O1＝her（＝ジェイニー） / O2＝引用文（第4文型）",
            "　引用文: S＝She（＝母親） / 助＝can't / V＝help / O＝herself（第3文型）",
            "★ told の O1 が her、引用文の S が She。<b>この 2 つは別人</b>。",
        ],
        "evidence": [
            ("her mother grabbed her by the arm and dragged her through the trees",
             "「どのような行動か」の具体例①。腕をつかんで引きずる。"),
            ("Her mother slapped her hard across her face.",
             "具体例②。頬を強くぶつ。"),
            ("She saw her mother shaking and knew her mother loved her",
             "母が<b>震えていた</b>＝感情を抑えられていない。"
             "同時に<b>愛していた</b>ことも娘は分かっている。"),
            ("The floor had always carried her mother's anger.",
             "第 13 段落。母の怒りが日常的なものであったこと。"),
            ("love was sometimes like silence, beautiful but hard to bear",
             "愛情ゆえに苦しい、という母子関係の要約。"),
        ],
        "ng": [
            "She をジェイニー自身と取る → 直前の文の主語はジェイニーだが、"
            "ここは父が<b>娘に語りかけている</b>台詞。娘に向かって娘を She とは呼ばない。",
            "help を「助ける」と訳す →「母は自分を助けられない」では意味が通らない。"
            "help ＝「こらえる」。",
            "「母は娘を愛していない」と読む → 本文に knew her mother loved her と明記。"
            "<b>愛しているのに抑えが利かない</b>という含みを落とすと減点。",
            "行動を書かず「感情的になること」とだけ書く → 設問が"
            "「どのような行動を指して」と明示的に要求している。",
        ],
    },
    {
        "no": "(F)", "kind": "語句整序（コンマ 1 か所）",
        "q": "与えられた語を正しい順に並べ替え、空所 (F) を埋めよ。すべての語を用い、"
             "どこか 1 か所にコンマを入れること。"
             "　about / buildings / I / know / ones / photograph / something / the / the / will",
        "target": "\"I'll need to (F) tomorrow.  Maybe you can tell me some history about them.\"",
        "ans": "know something about the buildings, the ones I will photograph",
        "ansnote": "完成形は I'll need to <b>know something about the buildings, the ones I will "
                   "photograph</b> tomorrow.　tomorrow は空所の<b>外</b>の語で、photograph にかかる。",
        "core": [
            "<b>need to ＋ 動詞の原形</b>。to の直後に置けるのは原形だけ。"
            "候補は know と photograph の 2 つで、<b>語数だけでは決まらない</b>。"
            "決めるのは直後の 2 文（help me ／ tell me some history about them）で、"
            "彼が求めているのは<b>知識</b>だから to の後ろは know。",
            "<b>the ones ＝ the buildings の言い換え（同格）</b>。"
            "設問が「どこか 1 か所にコンマ」と指定しているのは、この同格のコンマのこと。",
            "the ones の直後に<b>目的格の関係代名詞が省略</b>されている"
            "（the ones (which) I will photograph）。photograph に O が無いのが合図。",
        ],
        "struct": [
            "I'll need to know something about the buildings, the ones I will photograph tomorrow.",
            "　主節: S＝I / 助＝'ll / V＝need / O＝〈 to know something about the buildings 〉",
            "　不定詞句: V'＝know / O'＝something / M'＝( about the buildings )",
            "　同格: the ones ← the buildings の言い換え",
            "　[ (which) I will photograph tomorrow ] ← the ones を修飾（関係代名詞省略）",
        ],
        "evidence": [
            ("Maybe you can tell me some history about them.",
             "直後の文。<b>them ＝ the buildings</b>。空所に buildings が入ることの決め手。"),
            ("He is a photographer",
             "第 8 段落。クラーク氏は写真家。"),
            ("Buildings.",
             "第 10 段落。撮る対象は建物。"),
            ("Then Mr. Clark asked her to accompany him to the old house at the top of Oakhill.",
             "第 18 段落。翌日撮るのは具体的な建物であること。"),
        ],
        "ng": [
            "★<b>photograph the buildings, the ones I will know something about</b> "
            "── <b>最有力の誤答</b>。10 語をちょうど使い切り、コンマも 1 か所に入るので、"
            "語数と形だけでは弾けない。決め手は<b>直後の 2 文</b>で、"
            "You might be able to help me.／Maybe you can tell me some history about them. "
            "が示すとおり、彼が彼女に求めているのは<b>建物についての知識</b>であって撮影ではない。"
            "この並びだと「明日 know something about することになる建物を撮る」となり、"
            "彼女に history を尋ねる理由が消える。",
            "know something about the buildings the ones I will photograph（コンマ無し）→ "
            "設問の指定（コンマ 1 か所）に反するうえ、the ones の同格関係が読み取れない。",
            "to の直後に原形以外を置く → need to の後ろは<b>動詞の原形</b>。"
            "will と組ませずに原形で立てられるのは know だけ。",
        ],
    },
    {
        "no": "(G)", "kind": "空所補充（選択）",
        "q": "空所 (G) を埋めるのに最も適切な単語を選べ。　a) do　b) not　c) postpone　d) wait",
        "target": '"It will (G)," she said and walked out before her mother could reply.',
        "ans": "d) wait",
        "ansnote": "It ＝ the cleaning（掃除）。「掃除は待てる＝後回しでいい」と言い切って出ていく場面。",
        "core": [
            "<b>wait</b> は人だけでなく<b>物事を主語</b>にできる。"
            "It can wait. / It will wait.＝<b>「それは急がない・後回しでいい」</b>。"
            "「待つ」という訳語だけを覚えていると出てこない用法。",
            "空所の前が will（助動詞）なので、入るのは<b>動詞の原形</b>。",
        ],
        "struct": [
            "\"It will wait,\" she said and walked out before her mother could reply.",
            "　引用文: S＝It（＝the cleaning） / 助＝will / V＝wait（第1文型）",
            "　地の文: S＝she / V＝said and walked out / M＝( before her mother could reply )",
        ],
        "evidence": [
            ("There's cleaning to be done.",
             "直前の母の台詞。<b>It が受けるのは cleaning</b>。"),
            ("I need you to help me with some things around the house tomorrow.",
             "母の要求は「明日の家事」。それに対して「それは後でいい」と返している。"),
            ("walked out before her mother could reply",
             "言い返す隙を与えずに出ていった＝議論を打ち切る強い一言だったこと。"),
        ],
        "ng": [
            "a) do → It will do. は「それで間に合う・十分だ」の意味。"
            "掃除を後回しにする文脈と合わず、母の反論を封じる台詞にならない。",
            "b) not → will の後ろに not を置いても<b>動詞が無い</b>。"
            "It will not. だけでは何を否定しているのか決まらない。",
            "c) postpone → postpone は他動詞で O が必要（It will postpone では O が無い）。"
            "また「掃除が何かを延期する」という意味になってしまう。",
        ],
    },
]

# ---------------------------------------------------------------- 相互チェック用の正典
# ★選択肢は「問題冊子の印字」をそのまま持つ。FILLS（本文に実際に入れた語）と
#   ANSWER_MAP（解説が主張する記号）を突き合わせて、check.py が食い違いを弾く。
#   これが無いと「解説では d) と書いたのに本文には別の語を入れていた」が通ってしまう。
OPTIONS = {
    "(B)": {"a": "I'll go.", "b": "I can't.", "c": "I won't.", "d": "Of what?",
            "e": "I'll take it.", "f": "You don't.", "g": "Don't you dare."},
    "(C)": {"a": "ended", "b": "gone", "c": "seemed", "d": "sounded", "e": "went"},
    "(D)": {"a": "given her when needed", "b": "when she didn't feel uncomfortable",
            "c": "when her mother would not let her go",
            "d": "when she needed to retreat into silence"},
    "(G)": {"a": "do", "b": "not", "c": "postpone", "d": "wait"},
}

# 本文の空所マーカー → (設問, 選ぶ記号)
ANSWER_MAP = {
    "(B29)": ("(B)", "e"), "(B30)": ("(B)", "d"),
    "(B31)": ("(B)", "a"), "(B32)": ("(B)", "f"),
    "(C)": ("(C)", "d"), "(G)": ("(G)", "d"),
}

# 選択問題だが本文の空所ではないもの（下線部の後ろに続ける語句）
STANDALONE_ANSWER = {"(D)": "d"}

# (F) の語句整序：問題冊子で与えられた語（この 10 語をすべて使う・コンマ 1 か所）
F_WORDS = ["about", "buildings", "I", "know", "ones", "photograph",
           "something", "the", "the", "will"]

# 本文中の下線部（表示用）。(ラベル, 本文中で一意なアンカー, その中で下線を引く部分)
# ★アンカーは本文全体で **ちょうど 1 回** しか出てこないこと。check.py が数える。
UNDERLINE = [
    ("A", "It would be like her mother not to have mentioned it.",
     "It would be like her mother not to have mentioned it."),
    ("D", "there were moments", "there were moments"),
    ("E", "She can't help herself.", "She can't help herself."),
]

# ---------------------------------------------------------------- 空所の答え一覧（本文の直下に出す）
# ★答えそのものはここに書かない。FILLS / ANSWER_MAP / OPTIONS から機械的に組み立てる。
#   （慶應側は選択肢データが無いので FILL_NOTES に手書きし、check.py が FILLS と照合する。）
#   ここには「根拠の一行」だけを持つ ＝ 表と本文がずれようがない。
FILL_HINT = {
    "(B29)": "気に入った直後の一言。直後が That was all.（それだけ）＝交渉も説明もない決定文が入る。",
    "(B30)": "直前が taking pictures、直後の答えが Buildings.＝「何の（写真）?」と聞き返している。",
    "(B31)": "直前に the two breath-filled words（2 語）と明記。直後に母が You can't. と制止する。",
    "(B32)": "母の I need you … を否定。直後の You know good and well I do.（I do＝I do need you）と対。",
    "(C)": "3 か所すべてに同じ 1 語。② had not (C) が過去分詞・① は過去形なので、同形の語に限られる。",
    "(F)": "need to の後ろは原形。与えられた語で原形に置けるのは know だけ（photograph は will と組む）。",
    "(G)": "直前の There's cleaning to be done. を受けて It ＝ 掃除。「それは後回しでいい」。",
}

# ---------------------------------------------------------------- かかり先（先行詞）
# 形容詞のカタマリ [ ] が<b>どの語にかかるか</b>。(段落, 文) → [ (かかる先, 先頭, 種類), ... ]
REFS = {
    (1, 2): [("the room", "under the stairs", "前置詞句")],
    (2, 2): [("the way", "her mother had spoken", "the way S V（関係副詞相当・that の省略）")],
    (4, 2): [("a portion", "of the stairs", "前置詞句")],
    (4, 4): [("the way", "she might once have wanted", "the way S V（関係副詞相当）")],
    (4, 5): [("the age", "for romance", "前置詞句")],
    (4, 6): [("a passing", "she'd lamented", "関係代名詞（目的格・省略）")],
    (6, 2): [("no explanation", "about how he'd known", "前置詞句")],
    (11, 1): [("her entry", "into silence", "前置詞句")],
    (11, 2): [("the end", "of the porch", "前置詞句"),
              ("the porch", "above the steps", "前置詞句")],
    (12, 3): [("inside her", "where illness and confusion grew", "関係副詞")],
    (12, 4): [("the call", "she'd made", "関係代名詞（目的格・省略）")],
    (12, 5): [("silence", "which is where she lived", "関係代名詞（主格・非制限用法）")],
    (12, 6): [("a separate place", "to withdraw into", "不定詞の形容詞用法（前置詞で終わる）")],
    (14, 1): [("the way", "a child will", "the way S V（関係副詞相当）")],
    (14, 2): [("the woods", "behind their house", "前置詞句")],
    (14, 3): [("a scream", "that expressed all", "関係代名詞（主格）"),
              ("all", "she felt", "関係代名詞（目的格・省略）")],
    (17, 1): [("the ones", "I will photograph", "関係代名詞（目的格・省略）")],
    (17, 2): [("some history", "about them", "前置詞句")],
    (18, 2): [("the old house", "at the top", "前置詞句"),
              ("the top", "of Oakhill", "前置詞句")],
    (18, 4): [("Some time", "away from here", "前置詞句")],
    (21, 1): [("the quick vibration", "of her mother's approach", "前置詞句")],
    (21, 2): [("the way", "she'd always seen them", "the way S V（関係副詞相当）")],
    (21, 3): [("a harsh whisper", "that might have sounded", "関係代名詞（主格）")],
    (23, 3): [("some things", "around the house", "前置詞句")],
    (25, 2): [("cleaning", "to be done", "不定詞の形容詞用法（受動）")],
}
