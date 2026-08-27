# -*- coding: utf-8 -*-
"""慶應義塾大学 経済学部 2018 大問 I — 本文（正典）と全文 SVOCM 解析"""

META = {
    "key": "keio2018",
    "school": "慶應義塾大学 経済学部",
    "year": "2018",
    "qno": "大問 I",
    "title": '"Lowering the Minimum Legal Drinking Age"',
    "author": "by Aisla Vapeint (2014)",
    "jtitle": "飲酒可能年齢の引き下げについて",
    "lead": "論説文。筆者は「18 歳で他の大人の責任は負わせるのに飲酒だけ禁じるのは一貫性が無い」と主張する。"
            "主張 → 反論の先取り → 再反論、という型で進むので、段落の頭の 1 文を拾うだけで論の骨が見える。",
}

# ---------------------------------------------------------------- 本文（印字そのまま）
RAW = [
    "In many US states today a boy or girl of eighteen can legally drive a car, vote, get married and "
    "have children, purchase and carry a deadly weapon such as a pistol or rifle, and serve the nation "
    "in the armed forces, possibly to die on the battlefield. But one thing that person [ 1 ] not do "
    "legally anywhere in the USA would be to purchase an alcoholic drink. This is absurd. Changes "
    "should be made to our laws, so they reflect properly our social values.",

    "Deciding whether or not to lower the minimum legal drinking age might, on the face of it, seem "
    "like a simple matter - why make unnecessary changes? However, the issue cannot be judged in "
    "isolation. It is precisely because society considers [ 2 ] perform other more critical roles as "
    "citizens that the drinking issue has arisen. Today, American youth has access to and use of "
    "firearms; young people drive automobiles, and in many states can receive adult prison sentences. "
    "Is it not a double standard to treat them as adults in so many other ways, but to restrict their "
    "drinking? To be sure, we need to control the use and abuse of alcohol, but we also need to be "
    "consistent.",

    "The existing laws, which were enacted due to the concerns of a parent worried about family "
    "relations, combined with pressure by a small interest group campaigning for increased road "
    "safety, have in any case been largely ineffective. To understand this, we need to examine two "
    "different sets of statistics. The first deals with traffic accidents. True, the number of "
    "traffic-related deaths in the US has declined since the alcohol age-limit was raised in 1982. But "
    "to link the two is simply to make a common error of logic: fatalities have fallen in all age "
    "ranges, even in countries which had a lower drinking age, for example, Canada, and which made no "
    "changes to the law. What appears to be connected at first sight is simply a statistical "
    "illusion. [ 3 ]",

    "Another statistical set of evidence documents how people avoid the law: that is, the failure of "
    "existing laws to prevent alcohol consumption by under-age drinkers. America [ 4 ], one might have "
    "thought, to have learned its lesson on this issue, after the mistake of Prohibition in the 1920s, "
    "when alcohol was officially banned, but consumption continued anyway. Today, data shows that over "
    "5,000 people under 21 still lose their lives to alcohol in the USA every year. The law has made "
    "no difference in their case.",

    "Furthermore, binge-drinking, that is to say excessive drinking on a single occasion, has "
    "flourished despite the age restrictions in the USA. Of course, we may not be able to attribute "
    "[ 5 ] this phenomenon directly to the current laws; but [ 6 ]. Indeed, because so many "
    "21-year-olds are not used to alcohol, the problem of on-campus drinking is, according to many "
    "college presidents, made worse: as soon as students can touch the \"forbidden fruit\", they "
    "overdo things, with dangerous or even fatal results.",

    "Fear about the potential misuse of a substance is not a genuine reason to legislate against it. "
    "[ 7 ] legislate against a large number of usually harmless items and substances which might in "
    "the hands of certain individuals prove dangerous - from knives, scissors, and frying pans, to "
    "mushrooms and chemical fertilizers. Again, we are talking about responsibility: most people are "
    "assumed to be responsible enough. We should treat them this way as regards alcohol, too.",

    "Across most of Europe, Latin America, Africa, Asia and Oceania, eighteen is the age of adulthood, "
    "and is the age at which drinking is allowed. That is right: [ 8 ] do all the activities listed in "
    "the first paragraph above, then that person is also surely sufficiently mature to consume "
    "alcohol. In many other countries it is recognized that the young will have an occasional drink "
    "even in childhood, and that growing up around alcohol is one sure way to lessen the risk that a "
    "person will become a problem drinker later in life.",

    "Will some problems arise as a direct result of changing the law? It might seem so, but the truth "
    "is that no one can say for sure. Proving that legal changes directly cause social changes is "
    "always an uncertain business. But the issues which worry some parents and legislators already "
    "exist and will probably not go away simply by keeping the current laws. What will [ 9 ] change "
    "with new legislation is certain: public perception of the young. If our young people are old "
    "enough to vote, to marry, to raise families and to die in battle for their country, then they are "
    "old enough - indeed they deserve - to have a drink. [ 10 ]",
]

# ---------------------------------------------------------------- 空所を埋める
# 構造を取るために必要な範囲だけ。[3][5][9][10] は空所ではなく「下線部の位置を示す印」なので消す。
FILLS = {
    "[ 1 ]": "could",
    "[ 2 ]": "young people old enough to",
    "[ 4 ]": "ought",
    "[ 6 ]": "they are at least connected",
    "[ 7 ]": "If it were, we would",
    "[ 8 ]": "whenever we legally grant a person the right to",
    "[ 3 ]": "", "[ 5 ]": "", "[ 9 ]": "", "[ 10 ]": "",
}

FILL_NOTES = [
    ("[ 1 ]", "2. could",
     "後半が would be となっている。「（仮に買おうとしても）買えないであろう唯一のもの」という"
     "仮定法的な流れなので、時制を合わせて could。can だと would と噛み合わない。"),
    ("[ 2 ]", "2. old（3 番目にくる語）",
     "並べ替えると young people old enough to。consider O C（第 5 文型）の O が young people、"
     "C が old enough to perform ...。〈young / people / old / enough / to〉で 3 番目は old。"),
    ("[ 4 ]", "3. ought",
     "ought, one might have thought, to have learned … と挿入をまたいで ought to have learned が"
     "つながる。「〜すべきだったのに（していない）」の完了不定詞。"),
    ("[ 6 ]", "1. they are at least connected",
     "直前が「現在の法律のせいだと断定はできないが」。but の後は「少なくとも無関係ではない」"
     "＝譲歩からの引き戻し。they は「一気飲みの流行」と「現行法」。"),
    ("[ 7 ]", "3. If it were, we would",
     "前文が is not a genuine reason。「もし（本当にそれが正当な理由）だとしたら」＝"
     "事実に反する仮定なので仮定法過去 If it were …, we would …。"),
    ("[ 8 ]", "4. whenever we legally grant a person the right to",
     "grant A B（第 4 文型）で「A に B を与える」。the right to do all the activities … と続き、"
     "後半の then that person is … と呼応する。"),
]

# ---------------------------------------------------------------- 全文 SVOCM 解析
PARAS = [
    # ------------------------------------------------------------ ①
    {"no": 1, "sum": "現状の矛盾を並べて「これはおかしい」と切り出す。", "sents": [
        {"dsl": "( In many US states ) {M:today} {S:a boy or girl} <of eighteen> {助:can} {M:legally} "
                "{V:drive} {O:a car} , {V:vote} , {V:get} {C:married} {接:and} {V:have} {O:children} , "
                "{V:purchase and carry} {O:a deadly weapon} <such as a pistol or rifle> , {接:and} "
                "{V:serve} {O:the nation} ( in the armed forces ) , ( possibly to die on the "
                "battlefield ) .",
         "pat": "第3文型（SVO）の連続 ＋ get married は第2文型（SVC）",
         "tag": "助動詞 can に動詞が 5 つぶら下がる",
         "notes": [
             "can の後ろに <b>drive / vote / get / purchase and carry / serve</b> の 5 つが並列。"
             "「どこまでが can の支配下か」を最後の serve まで伸ばせるかが第 1 関門。",
             "get married だけ O ではなく <b>C</b>（married は形容詞扱い）。動詞ごとに文型が違う。",
             "文末の possibly to die on the battlefield は<b>結果を表す副詞用法の不定詞</b>。"
             "「そして戦場で死ぬこともある」。serve の O ではない。",
         ],
         "ja": "今日、アメリカの多くの州では、18 歳の男女が合法的に車を運転し、投票し、結婚して子を持ち、"
               "拳銃やライフルのような殺傷力のある武器を購入して携帯し、軍隊で国に仕え、"
               "場合によっては戦場で命を落とすこともある。"},
        {"dsl": "{接:But} {S:one thing} <{S':that person} {助:could} {M:not} {V':do} {M:legally} "
                "{M:anywhere} ( in the USA )> {V:would be} [C: to purchase an alcoholic drink ] .",
         "pat": "第2文型（SVC）",
         "tag": "★関係代名詞（目的格）の省略 ／ that は「その」",
         "notes": [
             "<b>that person は「その人物」</b>（前文の a boy or girl を受ける指示形容詞 that ＋ person）。"
             "関係代名詞の that ではない。ここを取り違えると S が消える。",
             "one thing の直後に<b>目的格の関係代名詞が省略</b>されている"
             "（one thing 〈which/that〉 that person could not do …）。do の O が抜けている＝省略の合図。",
             "主節の V は would be ただ 1 つ。S は one thing、C は to purchase an alcoholic drink。",
         ],
         "ja": "しかし、その人物がアメリカのどこであれ合法的にできない唯一のことが、"
               "酒類を購入することなのである。"},
        {"dsl": "{S:This} {V:is} {C:absurd} .", "pat": "第2文型（SVC）", "tag": "",
         "ja": "これは馬鹿げている。"},
        {"dsl": "{S:Changes} {助:should} {V:be made} ( to our laws ) , ( {接:so} {S':they} {V':reflect} "
                "{M':properly} {O':our social values} ) .",
         "pat": "受動態（能動なら SVO）＋ so 節",
         "tag": "make changes to ~ の受動",
         "notes": ["能動なら We should make changes to our laws。O にあたる changes が S に出た形なので、"
                   "made の後ろに O が無いのは正しい。",
                   "so 節の中は reflect（V′）と our social values（O′）の間に properly（M′）が割り込んでいる。"],
         "ja": "我々の社会的価値観を法がきちんと反映するよう、法律は改められるべきだ。"},
    ]},
    # ------------------------------------------------------------ ②
    {"no": 2, "sum": "「単純な話に見えるが切り離しては論じられない」＝論点の設定。", "sents": [
        {"dsl": "[S: Deciding [O': whether or not to lower the minimum legal drinking age ] ] {助:might} , "
                "( on the face of it ) , {V:seem} {C:like a simple matter} - {M:why} {V:make} "
                "{O:unnecessary changes} ?",
         "pat": "第2文型（SVC）",
         "tag": "動名詞句が S ／ 挿入 ／ seem like ~",
         "notes": [
             "S は <b>Deciding … age</b> までの動名詞句。長い S を 1 かたまりで括れるかが勝負。",
             "might と seem の間に , on the face of it ,（一見したところ）が<b>挿入</b>されている。"
             "コンマ 2 つで挟まれたら、まず外して読む。",
             "why make …? は <b>why ＋ 動詞の原形</b>で「なぜ〜するのか（＝する必要はない）」という反語。",
         ],
         "ja": "飲酒可能年齢の最低ラインを引き下げるべきかどうかを判断することは、"
               "一見したところ単純な問題に思えるかもしれない——なぜ不必要な変更をするのか、と。"},
        {"dsl": "{M:However} , {S:the issue} {助:cannot} {V:be judged} ( in isolation ) .",
         "pat": "受動態（能動なら SVO）", "tag": "",
         "ja": "しかし、この問題を切り離して判断することはできない。"},
        {"dsl": "{S:It} {V:is} {M:precisely} ( {接:because} {S':society} {V':considers} "
                "{O':young people} {C':old enough} ( to perform other more critical roles ( as "
                "citizens ) ) ) {接:that} {S:the drinking issue} {V:has arisen} .",
         "pat": "強調構文（It is 〜 that …）／ 内側は第5文型（SVOC）",
         "tag": "★It is 〜 that の見分け ／ consider O C",
         "notes": [
             "<b>強調構文</b>。It is と that を外すと "
             "<i>The drinking issue has arisen precisely because society considers …</i> "
             "という完全な文が残る。形式主語構文なら that 以下が「〜ということ」と訳せるはずで、"
             "ここは訳せない＝強調構文と確定する。",
             "強調されているのは <b>because 節まるごと</b>（理由の強調）。"
             "「まさに〜だからこそ」と訳す。",
             "consider O C（第 5 文型）＝「O を C だとみなす」。O が young people、"
             "C が old enough to perform …。<b>ここが空所［2］の正体</b>。",
         ],
         "ja": "社会が若者を、市民としてより重大な他の役割を果たせるだけの年齢に達しているとみなしている"
               "からこそ、飲酒の問題が生じているのである。"},
        {"dsl": "{M:Today} , {S:American youth} {V:has} {O:access to and use of firearms} ; {S:young "
                "people} {V:drive} {O:automobiles} , {接:and} ( in many states ) {助:can} {V:receive} "
                "{O:adult prison sentences} .",
         "pat": "第3文型（SVO）×3",
         "tag": "セミコロンで文を並べる",
         "notes": ["access to と use of が共通の目的語 firearms を取っている"
                   "（access to firearms and use of firearms）。",
                   "セミコロンは「ピリオドより弱い区切り」。前後は<b>対等な独立文</b>。"],
         "ja": "今日、アメリカの若者は銃器を入手し使用することができる。若者は車を運転し、"
               "多くの州では成人と同じ刑期を科されることもある。"},
        {"dsl": "{V:Is} {S:it} {M:not} {C:a double standard} [真S: to treat {O':them} ( as adults ) "
                "( in so many other ways ) , {接:but} to restrict {O':their drinking} ] ?",
         "pat": "第2文型（SVC）／ 形式主語",
         "tag": "形式主語 it ＝ to 不定詞 2 つ",
         "notes": ["it は形式主語。<b>真の S は to treat … but to restrict …</b> の 2 つの不定詞句。",
                   "Is it not …? は「〜ではないだろうか」という反語（＝そうだ、と言いたい）。"],
         "ja": "他の非常に多くの点では彼らを大人として扱いながら、飲酒だけを制限するのは、"
               "二重基準ではないだろうか。"},
        {"dsl": "( To be sure ) , {S:we} {V:need} [O: to control the use and abuse <of alcohol> ] , "
                "{接:but} {S:we} {M:also} {V:need} [O: to be consistent ] .",
         "pat": "第3文型（SVO）×2",
         "tag": "To be sure 〜, but … の譲歩",
         "notes": ["<b>To be sure, 〜 but …</b> は「確かに〜だが、しかし…」の型。"
                   "but の後ろが筆者の言いたいこと。"],
         "ja": "確かに、我々は飲酒とその乱用を規制する必要がある。だが同時に、一貫性を保つ必要もある。"},
    ]},
    # ------------------------------------------------------------ ③
    {"no": 3, "sum": "反論①：現行法は成立の経緯からして効果が無い。統計の見せかけの相関を叩く。", "sents": [
        {"dsl": "{S:The existing laws} , <{S':which} {V':were enacted} ( due to the concerns <of a "
                "parent <worried about family relations>> , <combined with pressure <by a small "
                "interest group <campaigning for increased road safety>>> )> , {助:have} ( in any "
                "case ) {V:been} {M:largely} {C:ineffective} .",
         "pat": "第2文型（SVC）",
         "tag": "★S と V が長い挿入で切り離される",
         "notes": [
             "コンマで挟まれた <b>which … road safety</b> は非制限用法の関係詞節（挿入）。"
             "外すと <i>The existing laws have in any case been largely ineffective.</i> "
             "＝ S V C の骨組みだけが残る。",
             "have と been の間にも in any case（いずれにせよ）が割り込む。"
             "<b>have been が 1 セット</b>で、その C が ineffective。",
             "worried about family relations は a parent を、campaigning for … は a small interest "
             "group を後ろから修飾する分詞。combined with 〜 は the concerns にかかる。"
             "<b>入れ子の &lt; &gt; を 3 段たどれるか</b>がこの文の山場。",
         ],
         "ja": "現行の法律は、家族関係を心配したある親の懸念に、交通安全の強化を求める小さな利益団体の"
               "圧力が加わって制定されたものだが、いずれにせよほとんど効果を上げてこなかった。"},
        {"dsl": "( To understand this ) , {S:we} {V:need} [O: to examine two different sets <of "
                "statistics> ] .",
         "pat": "第3文型（SVO）", "tag": "副詞用法の不定詞（目的）",
         "ja": "このことを理解するには、2 種類の統計を検討する必要がある。"},
        {"dsl": "{S:The first} {V:deals} ( with traffic accidents ) .",
         "pat": "第1文型（SV）", "tag": "deal with ~",
         "notes": ["deal with は「〜を扱う」だが with 以下は前置詞句なので O ではない。"
                   "<b>意味が他動詞的でも形は第 1 文型</b>。"],
         "ja": "1 つ目は交通事故に関するものである。"},
        {"dsl": "{M:True} , {S:the number} <of traffic-related deaths> <in the US> {V:has declined} "
                "( {接:since} {S':the alcohol age-limit} {V':was raised} ( in 1982 ) ) .",
         "pat": "第1文型（SV）", "tag": "True, 〜（譲歩の副詞）",
         "notes": ["文頭の True, は「なるほど確かに」。<b>次に But が来る合図</b>。"],
         "ja": "確かに、アメリカにおける交通事故関連の死者数は、1982 年に飲酒可能年齢が引き上げられて以降、"
               "減少している。"},
        {"dsl": "{接:But} [S: to link the two ] {V:is} {M:simply} [C: to make a common error <of "
                "logic> ] : {S:fatalities} {V:have fallen} ( in all age ranges ) , ( even in countries "
                "<{S':which} {V':had} {O':a lower drinking age}> , for example , Canada , {接:and} "
                "<{S':which} {V':made} {O':no changes} ( to the law )>) .",
         "pat": "第2文型（SVC）／ コロン以下は第1文型（SV）",
         "tag": "不定詞が S と C の両方に立つ",
         "notes": ["<b>To 〜 is to …</b>「〜することは…することだ」。S も C も不定詞句。",
                   "コロンは「つまり／その証拠に」。後ろが前の言い換え・根拠になる。",
                   "which … age と which … law の <b>2 つの関係詞節がともに countries にかかる</b>。"
                   "間に for example, Canada, が挟まっているので見失いやすい。"],
         "ja": "しかし、この 2 つを結びつけるのは、よくある論理の誤りを犯すことにほかならない。"
               "死者数はあらゆる年齢層で減少しており、たとえばカナダのように、飲酒可能年齢がより低く、"
               "しかも法改正を行わなかった国でさえ減っているのである。"},
        {"dsl": "[S: {S':What} {V':appears} [C': to be connected ] ( at first sight ) ] {V:is} "
                "{M:simply} {C:a statistical illusion} .",
         "pat": "第2文型（SVC）", "tag": "★関係代名詞 what が作る名詞節が S（下線部［3］）",
         "notes": ["<b>What appears … sight までが丸ごと S</b>。what は「〜するもの・こと」。",
                   "節の中は What（S′）appears（V′）to be connected（C′）＝第 2 文型。",
                   "設問 3 はこの文の言い換えを選ぶ問題。"
                   "「一見つながって見えるものは、実は統計上の錯覚にすぎない」＝"
                   "<b>早合点して結びつけるとデータの誤読になる</b>、という趣旨に合う選択肢を選ぶ。"],
         "ja": "一見つながっているように見えるものは、単なる統計上の錯覚にすぎない。"},
    ]},
    # ------------------------------------------------------------ ④
    {"no": 4, "sum": "反論②：法があっても未成年は飲む。禁酒法の失敗という前例。", "sents": [
        {"dsl": "{S:Another statistical set} <of evidence> {V:documents} [O: {M':how} {S':people} "
                "{V':avoid} {O':the law} ] : that is , {同格:the failure} <of existing laws> <to prevent "
                "alcohol consumption <by under-age drinkers>> .",
         "pat": "第3文型（SVO）",
         "tag": "document が動詞 ／ 疑問詞節が O",
         "notes": ["<b>documents は名詞ではなく動詞</b>「〜を記録する・裏づける」。"
                   "Another … evidence までが S だと決まれば V は documents しかない。",
                   "how 以下は「どのように人々が法を回避しているか」という名詞節で O。",
                   "コロン ＋ that is（すなわち）以下は O の言い換え（同格）。"],
         "ja": "もう 1 つの統計的証拠は、人々がどのように法を回避しているか——つまり、"
               "未成年者の飲酒を防ぐという点で現行法が失敗していること——を裏づけている。"},
        {"dsl": "{S:America} {助:ought} , ( one might have thought ) , {V:to have learned} {O:its "
                "lesson} ( on this issue ) , ( after the mistake <of Prohibition> <in the 1920s> , "
                "<{M':when} {S':alcohol} {V':was officially banned} , {接:but} {S':consumption} "
                "{V':continued} {M':anyway}> ) .",
         "pat": "第3文型（SVO）",
         "tag": "★ought to が挿入で割れる ／ 完了不定詞",
         "notes": ["<b>ought と to have learned の間に one might have thought が挿入</b>されている。"
                   "「〜と思われたかもしれないが」。コンマ 2 つを外して ought to have learned をつなぐ。",
                   "<b>ought to have done</b>＝「〜すべきだったのに（実際はしなかった）</b>」。"
                   "この含みが次文の「それでも年 5000 人が死んでいる」につながる。"],
         "ja": "アメリカは、1920 年代の禁酒法——酒が公式に禁止されたが、消費はいずれにせよ続いた——"
               "という失敗のあとで、この問題について教訓を学んでいてしかるべきだった、"
               "と思われたかもしれない。"},
        {"dsl": "{M:Today} , {S:data} {V:shows} [O: {接:that} {S':over 5,000 people} <under 21> "
                "{M':still} {V':lose} {O':their lives} ( to alcohol ) ( in the USA ) {M':every year} ] .",
         "pat": "第3文型（SVO）", "tag": "that 節が O",
         "ja": "今日のデータによれば、アメリカでは 21 歳未満の 5000 人以上が、"
               "いまなお毎年アルコールで命を落としている。"},
        {"dsl": "{S:The law} {V:has made} {O:no difference} ( in their case ) .",
         "pat": "第3文型（SVO）", "tag": "make no difference",
         "notes": ["make no difference＝「何の違いも生まない・効果が無い」。"
                   "no は difference にかかる形容詞で、<b>V を否定しているのではない</b>。"],
         "ja": "彼らに関しては、法律は何の効果もあげていない。"},
    ]},
    # ------------------------------------------------------------ ⑤
    {"no": 5, "sum": "反論③：むしろ一気飲みが悪化した。禁じるほど暴走する。", "sents": [
        {"dsl": "{M:Furthermore} , {S:binge-drinking} , that is to say {同格:excessive drinking} <on a "
                "single occasion> , {V:has flourished} ( despite the age restrictions <in the USA> ) .",
         "pat": "第1文型（SV）", "tag": "that is to say（同格の合図）",
         "notes": ["コンマ ＋ that is to say ＋ コンマ は<b>直前の名詞の言い換え</b>。"
                   "外しても文は成立する。"],
         "ja": "さらに、一気飲み——つまり一度の機会に過度に飲むこと——は、"
               "アメリカでは年齢制限があるにもかかわらず広がっている。"},
        {"dsl": "( Of course ) , {S:we} {助:may} {M:not} {V:be able to attribute} {O:this phenomenon} "
                "{M:directly} ( to the current laws ) ; {接:but} {S:they} {V:are} {M:at least} "
                "{C:connected} .",
         "pat": "第3文型（SVO）／ セミコロン以下は第2文型（SVC）",
         "tag": "attribute A to B ／ 空所［6］",
         "notes": ["<b>attribute A to B</b>「A を B のせいだと考える」。"
                   "A（this phenomenon）と to B の間に directly が割り込んでいる。",
                   "Of course 〜 ; but … も譲歩の型。but の後ろが主張。",
                   "設問 5 の attribute はここでは<b>動詞</b>なので、"
                   "アクセントは第 2 音節 <b>at-<u>trib</u>-ute</b>（名詞なら第 1 音節）。"],
         "ja": "もちろん、この現象を現行の法律のせいだと直接に断定することはできないかもしれない。"
               "だが、両者は少なくとも無関係ではない。"},
        {"dsl": "{M:Indeed} , ( {接:because} {S':so many 21-year-olds} {V':are} {M':not} {C':used} "
                "( to alcohol ) ) , {S:the problem} <of on-campus drinking> {助:is} , ( according to "
                "many college presidents ) , {V:made} {C:worse} : ( {接:as soon as} {S':students} "
                "{助:can} {V':touch} {O':the \"forbidden fruit\"} ) , {S:they} {V:overdo} {O:things} , "
                "( with dangerous or even fatal results ) .",
         "pat": "第5文型（SVOC）の受動態 ／ コロン以下は第3文型（SVO）",
         "tag": "★be made worse ＝ SVOC の受動",
         "notes": ["能動なら <i>the laws make the problem worse</i>（make O C）。"
                   "O が S に出た受動態なので、<b>made の後ろに C（worse）が残る</b>。"
                   "ここを「made worse で 1 つの動詞」と処理すると第 5 文型が見えない。",
                   "is と made の間に , according to many college presidents , が挿入されている。",
                   "be used to 〜 は「〜に慣れている」。used は C。"],
         "ja": "実際、非常に多くの 21 歳がアルコールに慣れていないため、多くの大学学長によれば、"
               "キャンパス内での飲酒問題はかえって悪化している。学生は「禁断の果実」に手が届いたとたん、"
               "度を越してしまい、危険な、時には命に関わる結果を招くのである。"},
    ]},
    # ------------------------------------------------------------ ⑥
    {"no": 6, "sum": "反論④：悪用の恐れは規制の根拠にならない（包丁もキノコも同じ）。", "sents": [
        {"dsl": "{S:Fear} <about the potential misuse <of a substance>> {V:is} {M:not} {C:a genuine "
                "reason} <to legislate against it> .",
         "pat": "第2文型（SVC）", "tag": "S が長い名詞句",
         "notes": ["S は <b>Fear</b> 1 語。about 以下は全部 &lt; &gt; の修飾。"
                   "「S ＝ Fear、V ＝ is」と裸にできれば一瞬で終わる。"],
         "ja": "ある物質が悪用されるかもしれないという恐れは、それを法で禁じる正当な理由にはならない。"},
        {"dsl": "( {接:If} {S':it} {V':were} ) , {S:we} {助:would} {V:legislate} ( against a large "
                "number <of usually harmless items and substances> <{S':which} {助:might} ( in the "
                "hands <of certain individuals> ) {V':prove} {C':dangerous}> ) - ( from knives , "
                "scissors , and frying pans , to mushrooms and chemical fertilizers ) .",
         "pat": "第1文型（SV）／ 仮定法過去",
         "tag": "★空所［7］＝ If it were, we would ／ prove C",
         "notes": ["<b>仮定法過去</b>（If ＋ S ＋ 過去形, S ＋ would ＋ 原形）。"
                   "前文が is not a genuine reason なので、If it were＝「仮にそうだとしたら」"
                   "という<b>事実に反する仮定</b>。",
                   "If it were の後ろには a genuine reason が省略されている。",
                   "which 節の中でも might と prove の間に in the hands of certain individuals が"
                   "割り込む。<b>prove は「〜だと判明する」で C（dangerous）を取る第 2 文型</b>。",
                   "from A to B（A から B まで）が items and substances の具体例。"],
         "ja": "もしそうだとしたら、我々は、特定の人間の手にかかれば危険になりうる、"
               "普段は無害な多数の品物や物質を——ナイフやはさみ、フライパンから、"
               "キノコや化学肥料に至るまで——法で禁じることになるだろう。"},
        {"dsl": "{M:Again} , {S:we} {V:are talking} ( about responsibility ) : {S:most people} "
                "{V:are assumed} [C: to be responsible enough ] .",
         "pat": "第1文型（SV）／ コロン以下は第5文型（SVOC）の受動態",
         "tag": "be assumed to do",
         "notes": ["能動なら <i>we assume most people to be responsible enough</i>（assume O C）。"
                   "受動になって C の to be responsible enough が残っている。"],
         "ja": "繰り返すが、問題にしているのは責任能力である。たいていの人は十分に責任を持てるものと"
               "みなされている。"},
        {"dsl": "{S:We} {助:should} {V:treat} {O:them} {M:this way} ( as regards alcohol ) , {M:too} .",
         "pat": "第3文型（SVO）", "tag": "as regards ~（〜に関しては）",
         "ja": "酒に関しても、我々は彼らを同じように扱うべきなのだ。"},
    ]},
    # ------------------------------------------------------------ ⑦
    {"no": 7, "sum": "国際比較：18 歳成人＝18 歳飲酒が世界標準。酒に囲まれて育つ方が安全。", "sents": [
        {"dsl": "( Across most <of Europe , Latin America , Africa , Asia and Oceania> ) , "
                "{S:eighteen} {V:is} {C:the age} <of adulthood> , {接:and} {V:is} {C:the age} <at which "
                "{S':drinking} {V':is allowed}> .",
         "pat": "第2文型（SVC）×2", "tag": "前置詞＋関係代名詞",
         "notes": ["and の後ろは S（eighteen）が省略され V（is）から始まる。",
                   "<b>at which</b>＝ the age に at がついた形（drinking is allowed <u>at</u> the age）。"
                   "前置詞が前に出ているだけで、節の中は S′ V′ が揃っている。"],
         "ja": "ヨーロッパ、ラテンアメリカ、アフリカ、アジア、オセアニアの大部分では、"
               "18 歳が成人年齢であり、飲酒が許される年齢でもある。"},
        {"dsl": "{S:That} {V:is} {C:right} : ( {接:whenever} {S':we} {M':legally} {V':grant} {O1':a "
                "person} {O2':the right} <to do all the activities <listed ( in the first paragraph "
                "above )>> ) , {M:then} {S:that person} {V:is} {M:also surely} {C:sufficiently "
                "mature} ( to consume alcohol ) .",
         "pat": "第2文型（SVC）／ whenever 節の中は第4文型（SVOO）",
         "tag": "★空所［8］＝ grant A B ／ whenever 〜, then …",
         "notes": ["<b>grant A B</b>（第 4 文型）＝「A に B を与える」。"
                   "a person が O1、the right to do … が O2。",
                   "listed in the first paragraph above は all the activities を後ろから修飾する過去分詞。",
                   "whenever（〜するときはいつでも）と then が呼応する。"
                   "空所［8］を選ぶときは、<b>後ろの do の主語が誰か</b>を確かめること。"],
         "ja": "それは正しい。第 1 段落に挙げたすべての行為をする権利を法的にある人物に認めるのなら、"
               "その人物は酒を飲むにも十分に成熟しているはずだからだ。"},
        {"dsl": "( In many other countries ) {S:it} {V:is recognized} [真S: {接:that} {S':the young} "
                "{助:will} {V':have} {O':an occasional drink} ( even in childhood ) ] , {接:and} "
                "[真S: {接:that} [S': growing up ( around alcohol ) ] {V':is} {C':one sure way} <to "
                "lessen the risk <{同格:that} {S'':a person} {助:will} {V'':become} {C'':a problem "
                "drinker} ( later in life )>> ] .",
         "pat": "受動態＋形式主語 ／ 2 つ目の that 節の中は第2文型（SVC）",
         "tag": "★that 節 3 つの役割を見分ける",
         "notes": ["it は形式主語。<b>真の S は that 節 2 つ</b>（that the young … と that growing up …）。"
                   "and が結ぶのは that 節どうし。",
                   "3 つ目の <b>the risk that a person will become …</b> の that は<b>同格</b>。"
                   "「〜という危険」。関係代名詞なら risk が節の中で S か O の働きをするはずだが、"
                   "ここは節が完全文なので同格と判断する。",
                   "growing up around alcohol（動名詞句）が 2 つ目の that 節の S′。"],
         "ja": "他の多くの国では、若者は子どものうちでさえ時折酒を口にするものであり、"
               "また酒のある環境で育つことこそが、その人が後年に問題のある飲酒者になる危険を減らす"
               "確実な方法の 1 つである、と認識されている。"},
    ]},
    # ------------------------------------------------------------ ⑧
    {"no": 8, "sum": "結論：副作用は不確かだが、若者の見られ方が変わることは確実。", "sents": [
        {"dsl": "{助:Will} {S:some problems} {V:arise} ( as a direct result <of changing the law> ) ?",
         "pat": "第1文型（SV）", "tag": "arise は自動詞",
         "notes": ["arise（生じる）は自動詞なので O を取らない。"
                   "他動詞 raise（〜を上げる）と混同しないこと。"],
         "ja": "法を変えた直接の結果として、何らかの問題が生じるだろうか。"},
        {"dsl": "{S:It} {助:might} {V:seem} {C:so} , {接:but} {S:the truth} {V:is} [C: {接:that} {S':no "
                "one} {助:can} {V':say} ( for sure ) ] .",
         "pat": "第2文型（SVC）×2", "tag": "so ＝ 前文の代用",
         "ja": "そう思えるかもしれないが、実のところ、誰にも確かなことは言えない。"},
        {"dsl": "[S: Proving [O': {接:that} {S'':legal changes} {M'':directly} {V'':cause} {O'':social "
                "changes} ] ] {V:is} {M:always} {C:an uncertain business} .",
         "pat": "第2文型（SVC）", "tag": "動名詞句が S ／ 二重の入れ子",
         "notes": ["S は <b>Proving … changes</b> まで。その中に that 節（O′）が入り、"
                   "さらにその中に S″ V″ O″ がある<b>二重の入れ子</b>。",
                   "文全体の V は is。Proving の -ing に引っ張られて V を取り違えないこと。"],
         "ja": "法改正が社会の変化を直接引き起こしていると証明することは、常に不確かな作業である。"},
        {"dsl": "{接:But} {S:the issues} <{S':which} {V':worry} {O':some parents and legislators}> "
                "{M:already} {V:exist} {接:and} {助:will} {M:probably not} {V:go away} ( simply by "
                "keeping the current laws ) .",
         "pat": "第1文型（SV）×2", "tag": "worry は他動詞",
         "notes": ["<b>which worry some parents</b>＝「親たちを心配させる」。"
                   "worry は「心配する」ではなく<b>「〜を心配させる」という他動詞</b>。"
                   "which が S′、some parents and legislators が O′。",
                   "and が結ぶのは exist と will … go away の 2 つの V。S は共通の the issues。"],
         "ja": "しかし、一部の親や議員を不安にさせている問題はすでに存在しており、"
               "現行法を維持するだけでは、おそらく消えはしないだろう。"},
        {"dsl": "[S: {S':What} {助:will} {V':change} ( with new legislation ) ] {V:is} {C:certain} : "
                "{同格:public perception} <of the young> .",
         "pat": "第2文型（SVC）", "tag": "★下線部［9］の斜体 will",
         "notes": ["what 節が S。「新しい法律によって変わるもの」。",
                   "<b>will が斜体</b>なのは、直前が will probably not go away（＝不確か）"
                   "だったのに対し、「これだけは<u>確実に</u>変わる」と対比・強調するため。",
                   "コロン以下 public perception of the young が「変わるもの」の中身（同格）。"],
         "ja": "新しい法律によって変わるものは何かといえば、それは確実である——"
               "すなわち、若者に対する世間の見方だ。"},
        {"dsl": "( {接:If} {S':our young people} {V':are} {C':old enough} ( to vote , to marry , to "
                "raise families {接:and} to die ( in battle ) ( for their country ) ) ) , {M:then} "
                "{S:they} {V:are} {C:old enough} - ( indeed {S':they} {V':deserve} ) - ( to have a "
                "drink ) .",
         "pat": "第2文型（SVC）", "tag": "old enough to do ／ ダッシュによる挿入",
         "notes": ["ダッシュ 2 つに挟まれた indeed they deserve は挿入。"
                   "外すと they are old enough to have a drink が残る。",
                   "<b>to have a drink は old enough と deserve の両方にかかる</b>。"
                   "「飲むに足る年齢だし、実際その資格がある」。"],
         "ja": "我々の若者が、投票し、結婚し、家庭を築き、そして国のために戦場で死ぬに足る年齢だと"
               "いうのなら、彼らは酒を飲むにも十分な年齢である——いや、飲む資格があるのだ。"},
    ]},
]

# 本文中の下線部（表示用）。(ラベル, 本文中で一意なアンカー, その中で下線を引く部分)
# ★[3][5][9] は空所ではなく「直前の語・文に下線が引かれている」ことを示す印。
# ★アンカーは本文全体で **ちょうど 1 回** しか出てこないこと。check.py が数える。
#   （"will" だけを目印にすると別の will に下線が付く。2026-08-27 に刷り上がり検査で検出。）
UNDERLINE = [
    ("3", "What appears to be connected at first sight is simply a statistical illusion.",
     "What appears to be connected at first sight is simply a statistical illusion."),
    ("5", "able to attribute this phenomenon", "attribute"),
    ("9", "What will change with new legislation", "will"),
]
