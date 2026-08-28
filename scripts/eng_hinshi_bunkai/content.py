# -*- coding: utf-8 -*-
"""英語 品詞分解トレーニング — 単一ソース（本文・分解・設問・全訳）"""

META = {
    "title": "英語 品詞分解トレーニング",
    "sub": "長文で鍛える S・V・O・C と「句・節」の識別",
    "level": "高校標準〜MARCH",
    "brand": "トリリオン",
    "n_pass": 4,
    "n_sent": 24,
}

# ---------------------------------------------------------------- 巻頭：記号ルール
RULES = [
    {"cls": "rc-svoc", "h": "S V O C … 文の骨組み",
     "b": "主語 S・述語動詞 V・目的語 O・補語 C。単独の副詞には M を付ける。"
          "従属節の中の要素には S′ V′ O′ C′ のようにダッシュを付け、さらに内側なら S″ V″ とする。",
     "ex": "the students＝S　became＝V　quiet＝C"},
    {"cls": "rc-adv", "h": "( ) … 副詞のカタマリ",
     "b": "前置詞句・副詞節・分詞構文など「動詞や文全体を修飾する」2 語以上のかたまり。"
          "多くは外しても文が成立するので、まず外して骨組みを見る"
          "（deprive A of B のように動詞とセットで外せないものもある）。",
     "ex": "( For most of the twentieth century ) , planners treated ..."},
    {"cls": "rc-noun", "h": "〈 〉 … 名詞のカタマリ",
     "b": "that 節・what 節・whether 節・動名詞句・不定詞の名詞用法など、S / O / C になれるかたまり。"
          "外すと文が壊れる。",
     "ex": "Researchers argue 〈 that green space does measurable work 〉."},
    {"cls": "rc-adj", "h": "[ ] … 形容詞のカタマリ（関係詞節・分詞）",
     "b": "関係詞節・分詞の後置修飾・形容詞用法の不定詞や前置詞句。"
          "直前の名詞に線を引いて結ぶと構造が見える。"
          "ただしコンマ＋which の非制限用法だけは例外で、先行詞が前の内容全体になることがある。",
     "ex": "the brain [ that appears to be resting ] is busy ..."},
]

STEPS = [
    "① 前から読んで、( ) [ ] 〈 〉 の <b>カタマリの切れ目</b>に印を入れる。目印は「前置詞・接続詞・関係詞・-ing / -ed / to」。",
    "② カタマリを全部外し、残った<b>裸の骨組み</b>を見る。まず <b>V（述語動詞）</b>を 1 つ確定させる。",
    "③ V の前の名詞が S、V の後ろの名詞が O、V の後ろの形容詞・名詞で「S = それ」なら C。",
    "④ 骨組みが決まってから<b>文型を確定</b>し、外したカタマリを「どの語にかかるか」を決めながら戻す。",
    "⑤ 最後に和訳する。<b>訳せたかではなく、S V O C を指させるか</b>で自己採点すること。",
]

RULE_EXAMPLES = [
    {"dsl": "{S:The book} <on the desk> {V:is} {C:mine} .",
     "pat": "第2文型（SVC）",
     "note": "[ on the desk ] を外すと The book is mine. という骨組みが残る。"
             "前置詞句が名詞の直後にあるときは、まず「形容詞のカタマリ」を疑う。"},
    {"dsl": "{S:I} {V:know} [O: {接:that} {S':he} {V':lives} ( in Kyoto ) ] .",
     "pat": "第3文型（SVO）",
     "note": "that 以下がまるごと know の目的語。〈 〉 を外すと I know だけになり、"
             "他動詞 know の O が消えてしまう＝ 〈 〉 は外せない。"},
    {"dsl": "( {接:When} {S':the bell} {V':rang} ) , {S:the students} "
            "<{S':who} {V':were talking}> {V:became} {C:quiet} .",
     "pat": "第2文型（SVC）",
     "note": "( ) は外せる副詞のカタマリ、[ ] は the students にかかる形容詞のカタマリ。"
             "V が 3 つ（rang / were talking / became）見えるが、"
             "<b>主節の V は became ただ 1 つ</b>。残りは接続詞・関係詞が連れてきた V′。"},
]

# ---------------------------------------------------------------- 長文 1
P1 = {
    "no": 1,
    "title": "Room to Breathe",
    "jtitle": "都市に「息をする場所」を",
    "field": "都市・環境",
    "paras": [
        "For most of the twentieth century, planners treated empty land in a city as a problem. "
        "@1{Open ground was space that had not yet been used, and the obvious solution was to build on it.} "
        "@2{Parks survived mainly because wealthy citizens defended them, not because anyone could prove "
        "that they were useful.}",

        "That view has changed. "
        "@3{Researchers who study public health now argue that green space does measurable work.} "
        "People who live within a short walk of a park report lower levels of stress, and children in "
        "leafy neighborhoods tend to concentrate better at school. "
        "@4{What surprises many planners is that the benefit does not depend on the size of the park.} "
        "@5{A row of trees along a busy street can matter as much as a large field on the edge of town.}",

        "The lesson is simple: a city needs room to breathe. "
        "@6{Land left open is not wasted land; it is an investment whose returns appear slowly, "
        "in hospitals that stay less crowded and in streets where people are willing to walk.}",
    ],
    "vocab": [
        ("planner", "名 都市計画の担当者"), ("open ground", "熟 空き地・更地"),
        ("obvious", "形 明らかな"), ("defend", "動 〜を擁護する・守る"),
        ("measurable", "形 測定できる・目に見える"), ("benefit", "名 恩恵・利益"),
        ("a row of ~", "熟 一列に並んだ〜"), ("on the edge of ~", "熟 〜の外れに"),
        ("investment", "名 投資"), ("return", "名 見返り・利益"),
        ("leafy", "形 緑の多い・木々の茂った"),
        ("within a short walk of ~", "熟 〜から歩いてすぐの所に"),
        ("be willing to do", "熟 進んで〜する"),
    ],
    "sents": [
        {
            "dsl": "{S:Open ground} {V:was} {C:space} <{S':that} {V':had not yet been used}> , "
                   "{接:and} {S:the obvious solution} {V:was} [C: to build on it ] .",
            "pat": "第2文型（SVC）＋第2文型（SVC）",
            "tag": "関係代名詞 that / 不定詞の名詞用法",
            "notes": [
                "and が結ぶのは <b>2 つの文</b>（Open ground was space … と the obvious solution was …）。"
                "and を見たら「何と何を結んでいるか」を必ず口に出す。",
                "[ that had not yet been used ] は space にかかる形容詞のカタマリ。"
                "that の直後が動詞なので<b>主格の関係代名詞</b>で、that 自身が S′ を兼ねる。",
                "not yet は「まだ〜ない」。had been used（過去完了の受動態）に割り込んでいるだけで、"
                "V′ は had not yet been used ひとかたまり。",
                "〈 to build on it 〉 は「〜すること」＝名詞のカタマリで was の C。"
                "build on it の it は open ground を指す。",
            ],
            "ja": "空いている土地とは、まだ使われていない場所のことであり、当然の解決策はそこに建物を建てることだった。",
        },
        {
            "dsl": "{S:Parks} {V:survived} ( mainly {接:because} {S':wealthy citizens} "
                   "{V':defended} {O':them} ) , ( not {接:because} {S':anyone} {V':could prove} "
                   "[O': {接:that} {S'':they} {V'':were} {C'':useful} ] ) .",
            "pat": "第1文型（SV）",
            "tag": "because 節 2 つ / not の作用範囲",
            "notes": [
                "( ) を 2 つとも外すと <b>Parks survived.</b> だけが残る＝第 1 文型。"
                "「公園は生き残った」がこの文の骨組み。",
                "not は直後の <b>because 節だけ</b>を否定する。"
                "「有用だと証明できたから生き残ったのでは<u>ない</u>」という意味で、"
                "「生き残らなかった」ではない。<b>not because …</b> は入試頻出の誤読ポイント。",
                "〈 that they were useful 〉 は prove の目的語（名詞のカタマリ）。"
                "because 節の中のさらに内側なので S″ V″ C″ とダッシュを 2 つ付けている。",
            ],
            "ja": "公園が生き残ったのは主に裕福な市民がそれを擁護したからであって、"
                  "公園が役に立つと誰かが証明できたからではなかった。",
        },
        {
            "dsl": "{S:Researchers} <{S':who} {V':study} {O':public health}> {M:now} {V:argue} "
                   "[O: {接:that} {S':green space} {V':does} {O':measurable work} ] .",
            "pat": "第3文型（SVO）",
            "tag": "関係代名詞 who / 接続詞 that",
            "notes": [
                "S（Researchers）と V（argue）が [ ] で <b>引き離されている</b>のがこの文の急所。"
                "[ who study public health ] を外せば Researchers now argue … と一瞬で見える。",
                "study の主語は who＝Researchers なので三単現の s が付かない。"
                "動詞の形は「どの名詞が主語か」を教えてくれる<b>証拠</b>として使う。",
                "〈 that … 〉 は argue の目的語。この that は<b>接続詞</b>で、"
                "後ろに green space does … という<b>欠けのない完全な文</b>が続く。"
                "関係代名詞の that なら後ろの文はどこかが欠ける。",
            ],
            "ja": "公衆衛生を研究する研究者たちは今や、緑地は目に見える働きをしていると主張している。",
        },
        {
            "dsl": "[S: {S':What} {V':surprises} {O':many planners} ] {V:is} "
                   "[C: {接:that} {S':the benefit} {V':does not depend} ( on the size <of the park> ) ] .",
            "pat": "第2文型（SVC）",
            "tag": "関係代名詞 what / 名詞節 2 つ",
            "notes": [
                "骨組みは <b>〈名詞のカタマリ〉 is 〈名詞のカタマリ〉</b>。"
                "文頭の What を「何が？」と疑問詞に取ると読み進めなくなる。",
                "what は<b>先行詞を含む関係代名詞</b>で「〜すること・もの」。"
                "What surprises many planners＝「多くの計画者を驚かせること」。"
                "what 節の中では what 自身が S′ になっている。",
                "is の直後の that 節は<b>補語</b>。"
                "[ of the park ] は the size にかかる形容詞のカタマリで、"
                "( on the size of the park ) 全体が depend にかかる副詞のカタマリ。",
            ],
            "ja": "多くの都市計画者を驚かせるのは、その恩恵が公園の大きさに左右されないという点である。",
        },
        {
            "dsl": "{S:A row} <of trees> <along a busy street> {V:can matter} "
                   "( as much as a large field <on the edge <of town>> ) .",
            "pat": "第1文型（SV）",
            "tag": "前置詞句の連続 / as ~ as の比較",
            "notes": [
                "S の<b>核</b>は A row（一列）であって trees ではない。"
                "[ of trees ][ along a busy street ] はどちらも A row にかかる形容詞のカタマリ。"
                "ここは助動詞 can があるため<b>動詞の形に単複が現れない</b>（can は主語が単数でも複数でも同形）。"
                "つまり動詞から核を逆算できないので、修飾のカタマリを外して核を特定するしかない。",
                "後置修飾は原則として直前の名詞にかかるが、"
                "[ along a busy street ] は直前の trees ではなく<b>核の A row</b> に戻る。"
                "[ of A ] が挟まるときは、かかり先が核まで飛ぶことがあると覚えておく。",
                "matter は<b>自動詞で「重要である」</b>。名詞「問題」と読むと骨組みが崩れる。",
                "( as much as … ) は can matter を修飾する副詞のカタマリ。"
                "比べているのは「A row of trees が重要な度合い」と"
                "「a large field が重要な度合い」で、as much as の後ろには "
                "can matter が省略されている。",
            ],
            "ja": "交通量の多い通り沿いの一列の並木は、町外れの広い野原と同じくらい重要でありうる。",
        },
        {
            "dsl": "{S:Land} <left open> {V:is not} {C:wasted land} ; {S:it} {V:is} "
                   "{C:an investment} <{S':whose returns} {V':appear} {M':slowly} , "
                   "( in hospitals <{S'':that} {V'':stay} {C'':less crowded}> ) {接:and} "
                   "( in streets <{M'':where} {S'':people} {V'':are} {C'':willing} ( to walk )> )> .",
            "pat": "第2文型（SVC）＋第2文型（SVC）",
            "tag": "過去分詞の後置修飾 / whose / 関係副詞 where",
            "notes": [
                "[ left open ] は<b>過去分詞の後置修飾</b>で「空いたままにされている土地」。"
                "left を過去形の V と読むと文が二重動詞になって破綻する。",
                "対する wasted land は<b>前置</b>修飾。"
                "過去分詞が <b>1 語だけ</b>なら名詞の前、"
                "後ろに語句を伴う（left <u>open</u> / printed <u>in one city</u>）なら名詞の後ろ、"
                "というのが原則。この 1 文で前置と後置が並んでいるので見比べること。",
                "セミコロン（;）は<b>ピリオドに近い切れ目</b>。前後は独立した 2 文と考えてよい。",
                "[ whose returns … ] の whose は<b>所有格の関係代名詞</b>で、"
                "an investment の returns（見返り）という関係。"
                "whose returns がそのまま関係詞節の S′ になる。",
                "( in hospitals … ) ( in streets … ) は関係詞節の<b>内側</b>にあり、"
                "appear（現れる）を修飾している。"
                "さらにその中の [ that stay less crowded ][ where people are willing to walk ] が "
                "hospitals / streets にかかる二重構造。",
            ],
            "ja": "空いたままの土地は無駄にされた土地ではない。それは、"
                  "混み合わずに済む病院や、人々が進んで歩きたくなる通りという形で、"
                  "ゆっくりと見返りが現れる投資なのである。",
        },
    ],
    "mcq": [
        {"q": "下線部 (1) の <span class=\"en\">that had not yet been used</span> が"
              "修飾している語はどれか。",
         "choices": ["Open ground", "the obvious solution", "it", "space"],
         "ans": 3,
         "exp": "関係代名詞節は原則として直前の名詞にかかる。ここでは was の補語 space にかかり、"
                "「まだ使われていない場所」となる。Open ground は文の S であって、"
                "関係詞節との間に was space が割り込んでいる。"},
        {"q": "下線部 (3) の <span class=\"en\">that green space does measurable work</span> "
              "の働きとして最も適切なものはどれか。",
         "choices": ["Researchers を後ろから修飾する関係代名詞節",
                     "argue の目的語となる名詞のカタマリ",
                     "直前の名詞と同格の関係にある名詞節",
                     "理由を表す副詞のカタマリ"],
         "ans": 1,
         "exp": "argue は他動詞で目的語を必要とする。that の後ろは green space does measurable work という"
                "欠けのない完全な文なので、この that は接続詞。名詞節をつくって argue の O になっている。"},
        {"q": "下線部 (4) の <span class=\"en\">What surprises many planners</span> の"
              "文中での働きはどれか。",
         "choices": ["文全体の主語となる名詞のカタマリ",
                     "is の補語となる名詞のカタマリ",
                     "直前の名詞を修飾する形容詞のカタマリ",
                     "譲歩を表す副詞のカタマリ"],
         "ans": 0,
         "exp": "what は先行詞を含む関係代名詞で「〜すること」。この名詞節の直後に is があり、"
                "その後ろに that 節（補語）が続くので、what 節は文全体の S。"},
        {"q": "下線部 (5) の <span class=\"en\">as much as a large field on the edge of town</span> "
              "の働きはどれか。",
         "choices": ["A row を後ろから修飾する形容詞のカタマリ",
                     "can matter の目的語となる名詞のカタマリ",
                     "can matter を修飾する副詞のカタマリ",
                     "文全体の補語となる形容詞のカタマリ"],
         "ans": 2,
         "exp": "matter は自動詞なので目的語を取らない。as much as … は「同じくらい」と"
                "程度を表す副詞のカタマリで、can matter にかかる。"},
    ],
    "trans": [
        {"n": 2, "points": ["not が 2 つ目の because 節だけを否定していると読めているか"
                            "（「生き残らなかった」と訳していないか）",
                            "mainly because A, not because B の対比を訳し分けられているか",
                            "prove that … の that 節を prove の目的語として訳せているか"]},
        {"n": 6, "points": ["left open を過去分詞の後置修飾として訳せているか（wasted land は前置修飾）",
                            "whose returns「その見返りが」と所有格で訳せているか",
                            "in hospitals … and in streets … を appear にかかる副詞句として処理できているか"]},
    ],
    "fulltrans": [
        "二十世紀のほとんどの期間、都市計画の担当者たちは、街の中の空き地を問題として扱っていた。"
        "(1) 空いている土地とは、まだ使われていない場所のことであり、当然の解決策はそこに建物を建てることだった。"
        "(2) 公園が生き残ったのは主に裕福な市民がそれを擁護したからであって、"
        "公園が役に立つと誰かが証明できたからではなかった。",

        "その見方は変わった。"
        "(3) 公衆衛生を研究する研究者たちは今や、緑地は目に見える働きをしていると主張している。"
        "公園まで歩いてすぐの場所に住む人はストレスの水準が低いと報告しており、"
        "緑の多い地域の子どもは学校でより集中できる傾向がある。"
        "(4) 多くの都市計画者を驚かせるのは、その恩恵が公園の大きさに左右されないという点である。"
        "(5) 交通量の多い通り沿いの一列の並木は、町外れの広い野原と同じくらい重要でありうる。",

        "教訓は単純だ。街には息をするための余地が必要なのである。"
        "(6) 空いたままの土地は無駄にされた土地ではない。それは、"
        "混み合わずに済む病院や、人々が進んで歩きたくなる通りという形で、"
        "ゆっくりと見返りが現れる投資なのである。",
    ],
}

# ---------------------------------------------------------------- 長文 2
P2 = {
    "no": 2,
    "title": "Inventing the Hour",
    "jtitle": "「時刻」は発明された",
    "field": "歴史・科学技術",
    "paras": [
        "Before the railway, every town kept its own time. "
        "@1{Noon was the moment when the sun stood highest over the local church tower, "
        "which meant that clocks in two towns fifty miles apart could differ by several minutes.} "
        "Nobody minded. "
        "@2{A traveler on horseback covered so little ground in a day that the difference never mattered.}",

        "The railway destroyed this comfortable arrangement. "
        "@3{Trains that ran on a published timetable required a single standard, for a schedule "
        "printed in one city was useless in another unless both cities kept the same time.} "
        "British railway companies adopted London time in the 1840s, and in 1880 Parliament "
        "made it law.",

        "What followed was stranger than the railway companies had expected. "
        "@4{Having accepted railway time, people gradually stopped consulting the sun altogether.} "
        "@5{The clock, rather than the sky, became the authority to which daily life answered.} "
        "@6{It is easy to forget that the hours we now treat as natural were designed by companies "
        "that wanted their trains to arrive when they said they would.}",
    ],
    "vocab": [
        ("railway", "名 鉄道"), ("noon", "名 正午"), ("mind", "動 気にする"),
        ("on horseback", "熟 馬に乗って"), ("cover ground", "熟 距離を進む"),
        ("published", "形 公表された"),
        ("timetable", "名 時刻表"), ("standard", "名 基準"), ("schedule", "名 予定表・運行表"),
        ("keep the same time", "熟 同じ時刻を用いる"),
        ("arrangement", "名 取り決め・仕組み"),
        ("adopt", "動 〜を採用する"), ("Parliament", "名 （英国）議会"),
        ("consult", "動 〜を参照する・見る"), ("altogether", "副 まったく・完全に"),
        ("authority", "名 権威・より所"),
    ],
    "sents": [
        {
            "dsl": "{S:Noon} {V:was} {C:the moment} <{M':when} {S':the sun} {V':stood} {M':highest} "
                   "( over the local church tower )> , <{S':which} {V':meant} "
                   "[O': {接:that} {S'':clocks} <in two towns <fifty miles apart>> "
                   "{V'':could differ} ( by several minutes ) ]> .",
            "pat": "第2文型（SVC）",
            "tag": "関係副詞 when / 非制限用法の which",
            "notes": [
                "[ when … ] は the moment にかかる<b>関係副詞節</b>。"
                "when の後ろは the sun stood highest … と<b>欠けのない文</b>である点が、"
                "関係代名詞との決定的な違い。",
                "コンマ＋which は<b>非制限用法</b>。ここでの先行詞は直前の 1 語ではなく"
                "「正午とは太陽が最も高くなる瞬間だ」という<b>前の内容全体</b>。"
                "which meant that …「そしてそれは〜を意味した」と前から訳し下ろす。",
                "[ in two towns … ] は clocks にかかる形容詞のカタマリ。"
                "その<b>内側</b>の [ fifty miles apart ] は clocks ではなく "
                "<b>two towns</b> にかかる（＝「50 マイル離れた 2 つの町」）。"
                "後置修飾は直前の名詞にかかるという原則どおりで、"
                "入れ子になった修飾は「どの名詞に戻るか」を必ず確認する。",
                "differ は自動詞「異なる」。( by several minutes ) の by は<b>差を表す by</b>で"
                "「数分だけ」。",
                "stood highest の highest は「最も高く」と<b>場所・程度を表す副詞</b>なので M′。"
                "P4 の lie still（still＝「じっとした」状態を表す形容詞＝C′）と見分けること。"
                "「S＝その語」が成り立てば C、成り立たなければ M。",
            ],
            "ja": "正午とは、地元の教会の塔の上で太陽が最も高く昇る瞬間のことであり、"
                  "そのため 50 マイル離れた 2 つの町の時計は数分ずれることがありえた。",
        },
        {
            "dsl": "{S:A traveler} <on horseback> {V:covered} {O:so little ground} ( in a day ) "
                   "( {接:that} {S':the difference} {M':never} {V':mattered} ) .",
            "pat": "第3文型（SVO）",
            "tag": "so ~ that … 構文",
            "notes": [
                "so little ground の so と、後ろの that が<b>離れて呼応</b>している。"
                "so + 形容詞 + 名詞 … that ～「とても〜な…なので～」。",
                "cover ground は「距離を進む」。cover を「覆う」と訳すと意味が取れない。",
                "( that … ) は結果を表す<b>副詞のカタマリ</b>。"
                "同じ形でも「名詞のカタマリをつくる that」ではない点に注意。"
                "外しても A traveler covered so little ground in a day. と文が成立する"
                "＝副詞のカタマリの証拠。",
                "little は「ほとんど〜ない」という<b>否定の語</b>。"
                "a little（少しある）との違いで意味が反転する。",
                "matter はここでも自動詞「重要である」。never が V′ の直前に入っている。",
            ],
            "ja": "馬に乗った旅人が一日に進む距離はごくわずかだったので、その差が問題になることは決してなかった。",
        },
        {
            "dsl": "{S:Trains} <{S':that} {V':ran} ( on a published timetable )> {V:required} "
                   "{O:a single standard} , {接:for} {S:a schedule} <printed in one city> {V:was} "
                   "{C:useless} ( in another ) ( {接:unless} {S':both cities} {V':kept} "
                   "{O':the same time} ) .",
            "pat": "第3文型（SVO）＋第2文型（SVC）",
            "tag": "等位接続詞 for / 過去分詞の後置修飾 / unless",
            "notes": [
                "コンマ＋for は<b>等位接続詞</b>で「というのも〜だからだ」。"
                "前置詞の for（〜のために）と混同しないこと。"
                "見分け方は<b>後ろに S V が続くかどうか</b>。ここは a schedule … was … と文が続く。",
                "[ printed in one city ] は a schedule にかかる過去分詞。"
                "「ある都市で印刷された運行表」。printed を過去形の V と読むと "
                "was と動詞が 2 つ並んで破綻する。",
                "another は another city のこと。",
                "( unless … ) は「〜しない限り」＝ if … not の副詞のカタマリ。"
                "unless 自体に否定の意味が入っているので、節の中をさらに否定しない。",
            ],
            "ja": "公表された時刻表に従って走る列車には単一の基準が必要だった。"
                  "というのも、ある都市で印刷された運行表は、両方の都市が同じ時刻を用いていない限り、"
                  "別の都市では役に立たなかったからである。",
        },
        {
            "dsl": "( Having accepted railway time ) , {S:people} {M:gradually} {V:stopped} "
                   "[O: consulting the sun ] {M:altogether} .",
            "pat": "第3文型（SVO）",
            "tag": "完了分詞構文 / 動名詞",
            "notes": [
                "( Having accepted … ) は<b>分詞構文</b>＝副詞のカタマリ。"
                "文頭にあり、主節の主語 people と意味上の主語が一致する。"
                "Having+過去分詞は主節より<b>前に起きた</b>ことを表すので"
                "「鉄道時間を受け入れてしまうと（受け入れた後は）」。",
                "〈 consulting the sun 〉 は stopped の目的語となる<b>動名詞句</b>。"
                "stop doing「〜するのをやめる」と stop to do「〜するために立ち止まる」の区別は必出。",
                "分詞構文には S V O C のラベルを付けない。"
                "S と V を持つ「節」ではなく、-ing が導く「句」だからである。",
            ],
            "ja": "鉄道の時間を受け入れてしまうと、人々は次第に太陽を参照することを完全にやめてしまった。",
        },
        {
            "dsl": "{S:The clock} , ( rather than the sky ) , {V:became} {C:the authority} "
                   "<{M':to which} {S':daily life} {V':answered}> .",
            "pat": "第2文型（SVC）",
            "tag": "挿入句 / 前置詞＋関係代名詞",
            "notes": [
                "コンマに挟まれた ( rather than the sky ) は<b>挿入</b>。"
                "いったん飛ばして The clock became the authority … と読むのが正しい手順。"
                "意味の上では主語 The clock と対比される要素だが、"
                "文の骨組みには入らないので、ここでは副詞のカタマリの記号を借りて示している。",
                "[ to which daily life answered ] は the authority にかかる形容詞のカタマリ。"
                "answer to ~「〜に従う・〜に責任を負う」の to が"
                "関係代名詞 which の前に出た形（前置詞＋関係代名詞）。",
                "前置詞＋関係代名詞の後ろは<b>欠けのない完全な文</b>（daily life answered）になる。"
                "which の後ろが欠けていたら to which ではなく which 単独のはず、と逆算できる。",
            ],
            "ja": "空ではなく時計こそが、日々の生活が従う先となったのである。",
        },
        {
            "dsl": "{S:It} {V:is} {C:easy} [真S: to forget [ {接:that} {S':the hours} "
                   "<{S'':we} {M'':now} {V'':treat} {C'':as natural}> {V':were designed} "
                   "( by companies <{S'':that} {V'':wanted} {O'':their trains} {C'':to arrive} "
                   "( when they said they would )> ) ] ] .",
            "pat": "第2文型（SVC）／形式主語構文",
            "tag": "形式主語 It / 関係代名詞の省略 / SVOC",
            "notes": [
                "It is easy to do の It は<b>形式主語</b>。真の主語は 〈 to forget … 〉 で、"
                "「〜を忘れがちだ」と訳す。",
                "the hours の直後に we が来る＝<b>目的格の関係代名詞 which / that の省略</b>。"
                "[ we now treat as natural ]「私たちが今では当然だと考えている」が the hours にかかる。"
                "treat A as B の A が先行詞に移動しているので、節の中に O″ が見えない。",
                "この関係詞節を外すと the hours were designed by companies … という骨組みが見える。"
                "S′ と V′ が長い修飾で引き離される典型パターン。",
                "[ that wanted their trains to arrive … ] は companies にかかる関係詞節。"
                "その中は want O to do＝<b>第 5 文型</b>で、O″＝their trains、C″＝to arrive。",
                "文末の they would は they would arrive の<b>省略</b>。"
                "「到着すると会社が言った時刻に到着する」という意味。",
            ],
            "ja": "私たちが今では自然なものとして扱っている時間は、"
                  "自分たちの列車を宣言どおりの時刻に到着させたいと考えた企業によって設計された、"
                  "ということは忘れられがちである。",
        },
    ],
    "mcq": [
        {"q": "下線部 (1) の <span class=\"en\">which</span> が受けている内容として"
              "最も適切なものはどれか。",
         "choices": ["補語になっている the moment という名詞 1 語",
                     "直前に置かれた the local church tower という名詞句",
                     "直前の節が述べている内容全体",
                     "次の文の Nobody minded という内容"],
         "ans": 2,
         "exp": "コンマ＋which の非制限用法では、直前の 1 語だけでなく前の節全体を先行詞に取ることができる。"
                "「時計が数分ずれた」のは、町ごとに正午を決めていたという直前の内容が原因なので、"
                "先行詞は節全体。"},
        {"q": "下線部 (3) の <span class=\"en\">for</span> の働きはどれか。",
         "choices": ["「というのも〜だから」と理由を述べる等位接続詞",
                     "「〜のために」という目的を表す前置詞",
                     "「〜の間」という期間を表す前置詞",
                     "「〜する限り」という条件を表す従位接続詞"],
         "ans": 0,
         "exp": "for の後ろに a schedule … was useless … という S V が続いているので前置詞ではない。"
                "コンマ＋for で理由を後から補足する等位接続詞。"},
        {"q": "下線部 (4) の <span class=\"en\">Having accepted railway time</span> の"
              "文法上の働きはどれか。",
         "choices": ["people を後ろから修飾する形容詞のカタマリ",
                     "stopped の目的語となる名詞のカタマリ",
                     "主語 people と同格の名詞句",
                     "主節に時・理由を添える副詞のカタマリ（分詞構文）"],
         "ans": 3,
         "exp": "文頭にあってコンマで主節と切れており、外しても people gradually stopped … が成立する。"
                "したがって副詞のカタマリ＝分詞構文。Having+過去分詞なので主節より前の出来事を表す。"},
        {"q": "下線部 (5) の <span class=\"en\">to which daily life answered</span> が"
              "修飾している語はどれか。",
         "choices": ["the sky", "the authority", "The clock", "daily life"],
         "ans": 1,
         "exp": "前置詞＋関係代名詞の節は直前の名詞にかかる。answer to the authority「その権威に従う」"
                "という関係が復元できる。"},
    ],
    "trans": [
        {"n": 2, "points": ["so … that の因果を「とても〜なので…」と訳せているか",
                            "little を「ほとんど〜ない」と否定で訳せているか"
                            "（a little「少しはある」と取り違えていないか）",
                            "matter を自動詞「重要である・問題になる」と訳せているか"]},
        {"n": 6, "points": ["It … to forget の形式主語を「〜を忘れがちだ」と処理できているか",
                            "the hours we now treat as natural の関係代名詞の省略を訳出できているか",
                            "wanted their trains to arrive を第 5 文型として訳せているか"]},
    ],
    "fulltrans": [
        "鉄道が現れる前は、どの町も独自の時間を守っていた。"
        "(1) 正午とは、地元の教会の塔の上で太陽が最も高く昇る瞬間のことであり、"
        "そのため 50 マイル離れた 2 つの町の時計は数分ずれることがありえた。"
        "誰も気にしなかった。"
        "(2) 馬に乗った旅人が一日に進む距離はごくわずかだったので、その差が問題になることは決してなかった。",

        "鉄道はこの居心地のよい仕組みを壊してしまった。"
        "(3) 公表された時刻表に従って走る列車には単一の基準が必要だった。"
        "というのも、ある都市で印刷された運行表は、両方の都市が同じ時刻を用いていない限り、"
        "別の都市では役に立たなかったからである。"
        "英国の鉄道会社各社は 1840 年代にロンドン時間を採用し、1880 年に議会がそれを法律にした。",

        "その後に起きたことは、鉄道会社が予想していたよりも奇妙だった。"
        "(4) 鉄道の時間を受け入れてしまうと、人々は次第に太陽を参照することを完全にやめてしまった。"
        "(5) 空ではなく時計こそが、日々の生活が従う先となったのである。"
        "(6) 私たちが今では自然なものとして扱っている時間は、"
        "自分たちの列車を宣言どおりの時刻に到着させたいと考えた企業によって設計された、"
        "ということは忘れられがちである。",
    ],
}

# ---------------------------------------------------------------- 長文 3
P3 = {
    "no": 3,
    "title": "The Cost of a Full Plate",
    "jtitle": "満杯の皿が払う代償",
    "field": "社会・行動科学",
    "paras": [
        "@1{It is tempting to assume that people waste food because they do not care about it.} "
        "Surveys suggest otherwise. "
        "@2{Most shoppers say that throwing away food makes them uncomfortable, yet the average "
        "household in a wealthy country discards roughly a fifth of what it buys.}",

        "@3{The gap between what people believe and what they actually do is not a failure of values "
        "but a failure of design.} "
        "Supermarkets sell in quantities that suit the seller. "
        "@4{Date labels, invented to signal freshness, are read as medical warnings.} "
        "@5{A shopper standing in front of a shelf has neither the time nor the information required "
        "to judge whether the yogurt is still safe.}",

        "Small changes therefore work better than lectures. "
        "@6{When one chain replaced its sell-by dates with best-before dates and added a line "
        "explaining the difference, waste in the households it served fell by fourteen percent.} "
        "It was a result that campaigns urging people to care for the planet had struggled to achieve.",
    ],
    "vocab": [
        ("tempting", "形 〜したくなるような"), ("assume", "動 〜だと決めてかかる"),
        ("survey", "名 調査"), ("otherwise", "副 そうではないと"),
        ("discard", "動 〜を捨てる"), ("roughly", "副 おおよそ"),
        ("a fifth", "熟 5 分の 1"), ("failure", "名 失敗・不備"),
        ("quantity", "名 量"), ("suit", "動 〜に都合がよい"),
        ("freshness", "名 鮮度"), ("shelf", "名 棚"), ("lecture", "名 説教・小言"),
        ("chain", "名 チェーン店"), ("sell-by date", "熟 販売期限"),
        ("best-before date", "熟 賞味期限"), ("date label", "熟 （食品の）日付表示"),
    ],
    "sents": [
        {
            "dsl": "{S:It} {V:is} {C:tempting} [真S: to assume [ {接:that} {S':people} {V':waste} "
                   "{O':food} ( {接:because} {S'':they} {V'':do not care} ( about it ) ) ] ] .",
            "pat": "第2文型（SVC）／形式主語構文",
            "tag": "形式主語 It / 名詞節の入れ子",
            "notes": [
                "It is tempting to do「つい〜したくなる／〜と考えがちだ」。"
                "It は<b>形式主語</b>で、真の主語は 〈 to assume … 〉 全体。",
                "名詞のカタマリが<b>二重</b>になっている。"
                "外側 〈 to assume … 〉（真主語）の中に、"
                "内側 〈 that people waste food 〉（assume の目的語）が入っている。",
                "( because … ) は waste にかかる副詞のカタマリ。"
                "assume の内容の一部なので、that 節の中に収まっている点に注意。",
            ],
            "ja": "人は食べ物を大切に思っていないから無駄にするのだ、とつい決めつけたくなる。",
        },
        {
            "dsl": "{S:Most shoppers} {V:say} [O: {接:that} [S': throwing away food ] {V':makes} "
                   "{O':them} {C':uncomfortable} ] , {接:yet} {S:the average household} "
                   "<in a wealthy country> {V:discards} {O:roughly a fifth} "
                   "<of [ {O':what} {S':it} {V':buys} ]> .",
            "pat": "第3文型（SVO）＋第3文型（SVO）",
            "tag": "動名詞句が主語 / 第5文型 / 関係代名詞 what",
            "notes": [
                "that 節の中の S′ は 〈 throwing away food 〉（動名詞句）。"
                "動名詞句は<b>単数扱い</b>なので makes に三単現の s が付く。"
                "food を主語と誤読すると意味が反転する。",
                "makes them uncomfortable は make O C＝<b>第 5 文型</b>。"
                "「them＝uncomfortable の状態にする」という O = C の関係を確認する。",
                "yet はここでは<b>等位接続詞「しかし」</b>。副詞「まだ」ではない。"
                "後ろに S V が続いていることが手がかり。",
                "[ of what it buys ] は a fifth にかかる形容詞のカタマリ。"
                "その中の 〈 what it buys 〉 は前置詞 of の目的語となる名詞節で、"
                "what は buys の目的語（O′）を兼ねている。",
            ],
            "ja": "買い物客の大半は、食べ物を捨てるのは気分が悪いと言う。"
                  "それにもかかわらず、豊かな国の平均的な家庭は、買ったもののおよそ 5 分の 1 を捨てている。",
        },
        {
            "dsl": "{S:The gap} <between [ {O':what} {S':people} {V':believe} ] {接:and} "
                   "[ {O':what} {S':they} {M':actually} {V':do} ]> {V:is} not {C:a failure} "
                   "<of values> {接:but} {C:a failure} <of design> .",
            "pat": "第2文型（SVC）",
            "tag": "not A but B / what 節 2 つ",
            "notes": [
                "S の核は The gap。[ between … ] がそれにかかり、"
                "between A and B の A と B が<b>どちらも what 節</b>になっている。",
                "what 節は「〜すること」。"
                "what people believe＝「人が信じていること」、"
                "what they actually do＝「人が実際にすること」。"
                "what はいずれも believe / do の目的語（O′）を兼ねている。",
                "not A but B「A ではなく B」。"
                "A と B は<b>同じ形</b>（a failure of ~）で対応しており、"
                "どちらも is の補語。ここを見抜くと訳が一気に決まる。",
            ],
            "ja": "人が信じていることと実際にすることの隔たりは、価値観の失敗ではなく、"
                  "設計の失敗なのである。",
        },
        {
            "dsl": "{S:Date labels} , <invented ( to signal freshness )> , {V:are read} "
                   "{C:as medical warnings} .",
            "pat": "第5文型の受動態（read O as C → be read as C）",
            "tag": "過去分詞の挿入 / read A as B の受動態",
            "notes": [
                "コンマに挟まれた [ invented … ] は Date labels にかかる<b>過去分詞句の挿入</b>。"
                "外すと Date labels are read as medical warnings. という骨組みが残る。",
                "invented を過去形の V と読むと、are read と動詞が 2 つ並んで破綻する。"
                "<b>コンマ＋-ed …, は後置修飾の合図</b>と覚えておく。",
                "read A as B「A を B とみなす」の受動態。"
                "能動なら A が O、B が C の第 5 文型なので、"
                "受動態になった as medical warnings は <b>C として残っている</b>。",
                "( to signal freshness ) は invented にかかる目的の副詞用法「〜するために」。",
            ],
            "ja": "鮮度を示すために考案された食品の日付表示が、医学的な警告として読み取られている。",
        },
        {
            "dsl": "{S:A shopper} <standing in front of a shelf> {V:has} {接:neither} {O:the time} "
                   "{接:nor} {O:the information} <required ( to judge [ {接:whether} {S':the yogurt} "
                   "{V':is} {M':still} {C':safe} ] )> .",
            "pat": "第3文型（SVO）",
            "tag": "現在分詞の後置修飾 / neither A nor B / whether 節",
            "notes": [
                "[ standing in front of a shelf ] は A shopper にかかる<b>現在分詞の後置修飾</b>。"
                "「棚の前に立っている買い物客」。ここを V と読むと has と衝突する。",
                "neither A nor B「A も B も〜ない」。"
                "A と B はどちらも has の目的語（the time / the information）。",
                "[ required … ] は過去分詞の後置修飾。位置としては直前の the information にかかるが、"
                "意味の上では <b>neither A nor B のかたまり全体</b>（時間も情報も）に及ぶ。"
                "「判断するのに必要な時間も情報も無い」と訳すのが自然。",
                "〈 whether the yogurt is still safe 〉 は judge の目的語となる<b>名詞節</b>で"
                "「〜かどうか」。"
                "「〜であろうとなかろうと」という副詞節の whether と混同しないこと。"
                "他動詞 judge の O が必要なので、ここは名詞節と確定できる。",
            ],
            "ja": "棚の前に立つ買い物客には、そのヨーグルトがまだ安全かどうかを判断するのに必要な"
                  "時間も情報もない。",
        },
        {
            "dsl": "( {接:When} {S':one chain} {V':replaced} {O':its sell-by dates} "
                   "( with best-before dates ) {接:and} {V':added} {O':a line} "
                   "<explaining the difference> ) , {S:waste} <in the households "
                   "<{S':it} {V':served}>> {V:fell} ( by fourteen percent ) .",
            "pat": "第1文型（SV）",
            "tag": "when 副詞節 / 関係代名詞の省略 / 差を表す by",
            "notes": [
                "文頭の ( When … ) を最後まで外すのが第一歩。"
                "外すと <b>waste … fell by fourteen percent.</b> という第 1 文型が残る。",
                "when 節の中で and が結んでいるのは <b>replaced と added</b>（2 つの V′）。"
                "主語 one chain は共通で、2 度目は省略されている。",
                "[ explaining the difference ] は a line にかかる現在分詞の後置修飾。",
                "the households の直後に it が来る＝<b>目的格の関係代名詞の省略</b>。"
                "[ it served ]「そのチェーンが商品を届けていた（家庭）」。"
                "[ in the households … ] 全体が waste にかかる形容詞のカタマリで、"
                "S の核はあくまで waste。",
                "( by fourteen percent ) の by は<b>差・程度を表す by</b>「14 パーセント分」。",
            ],
            "ja": "あるチェーン店が販売期限の表示を賞味期限の表示に置き換え、"
                  "その違いを説明する一文を添えたところ、そのチェーンが商品を届けていた家庭での廃棄は"
                  " 14 パーセント減少した。",
        },
    ],
    "mcq": [
        {"q": "下線部 (1) の <span class=\"en\">It</span> の働きとして最も適切なものはどれか。",
         "choices": ["直後の that 節を受ける形式目的語",
                     "漠然と状況を指す非人称の it",
                     "天候・時間・距離を表す非人称の it",
                     "後ろの to 不定詞句を受ける形式主語"],
         "ans": 3,
         "exp": "It is tempting to do の形。It 自体に指示内容はなく、"
                "後ろの to 不定詞句を先取りしているだけの形式主語である。"
                "形式目的語なら It ではなく他動詞の後ろに置かれる（例: I find it hard to …）。"},
        {"q": "下線部 (2) の <span class=\"en\">makes them uncomfortable</span> の文型はどれか。",
         "choices": ["第3文型（SVO）", "第5文型（SVOC）", "第4文型（SVOO）", "第2文型（SVC）"],
         "ans": 1,
         "exp": "them = uncomfortable という O = C の関係が成り立つので第 5 文型。"
                "them と uncomfortable の間に be 動詞を入れて意味が通るかが判定法。"},
        {"q": "下線部 (4) の <span class=\"en\">invented to signal freshness</span> "
              "の働きはどれか。",
         "choices": ["この文全体の述語動詞となる過去形",
                     "目的を表す副詞のカタマリ（不定詞の副詞用法）",
                     "Date labels を後ろから修飾する形容詞のカタマリ",
                     "are read の補語となる名詞のカタマリ"],
         "ans": 2,
         "exp": "コンマに挟まれた過去分詞句で、Date labels を後置修飾している。"
                "述語動詞は are read の 1 つだけ。"},
        {"q": "下線部 (5) の <span class=\"en\">whether the yogurt is still safe</span> "
              "の働きはどれか。",
         "choices": ["judge の目的語となる名詞のカタマリ",
                     "the information を修飾する形容詞のカタマリ",
                     "「〜であろうとなかろうと」という副詞のカタマリ",
                     "required の主語"],
         "ans": 0,
         "exp": "judge は他動詞で目的語が必要。whether 節が「〜かどうか」という名詞節として"
                "その目的語になっている。"},
    ],
    "trans": [
        {"n": 3, "points": ["between A and B の A・B がともに what 節であることを訳出できているか",
                            "not A but B を「A ではなく B」と訳せているか",
                            "failure of values / failure of design の対応を崩していないか"]},
        {"n": 6, "points": ["When 節の中で and が replaced と added を結んでいると読めているか",
                            "the households it served の関係代名詞の省略を訳出できているか",
                            "fell by fourteen percent を「14 パーセント減少した」と訳せているか"]},
    ],
    "fulltrans": [
        "(1) 人は食べ物を大切に思っていないから無駄にするのだ、とつい決めつけたくなる。"
        "調査はそうではないと示唆している。"
        "(2) 買い物客の大半は、食べ物を捨てるのは気分が悪いと言う。"
        "それにもかかわらず、豊かな国の平均的な家庭は、買ったもののおよそ 5 分の 1 を捨てている。",

        "(3) 人が信じていることと実際にすることの隔たりは、価値観の失敗ではなく、設計の失敗なのである。"
        "スーパーマーケットは売り手に都合のよい量で商品を売る。"
        "(4) 鮮度を示すために考案された食品の日付表示が、医学的な警告として読み取られている。"
        "(5) 棚の前に立つ買い物客には、そのヨーグルトがまだ安全かどうかを判断するのに必要な"
        "時間も情報もない。",

        "したがって、小さな変更のほうが説教よりもうまくいく。"
        "(6) あるチェーン店が販売期限の表示を賞味期限の表示に置き換え、"
        "その違いを説明する一文を添えたところ、そのチェーンが商品を届けていた家庭での廃棄は"
        " 14 パーセント減少した。"
        "それは、地球を大切にしようと訴えるキャンペーンがなかなか達成できずにいた成果だった。",
    ],
}

# ---------------------------------------------------------------- 長文 4
P4 = {
    "no": 4,
    "title": "The Work of Sleep",
    "jtitle": "眠りという仕事",
    "field": "自然科学",
    "paras": [
        "@1{Sleep looks like the absence of activity, but the brain that appears to be resting "
        "is in fact busy sorting the day.} "
        "@2{During the hours when we lie still, patterns of firing recorded while we were awake "
        "are replayed, sometimes faster than they originally occurred.} "
        "@3{What the brain seems to be doing is deciding which of the day's experiences deserve "
        "to be kept.}",

        "@4{Deprive a student of sleep on the night after a lesson, and the material is usually far "
        "harder to recall a week later, even if the student sleeps normally afterward.} "
        "The damage is done not by tiredness but by the loss of the sorting process itself.",

        "@5{Only when this process is understood does the familiar advice make sense.} "
        "@6{Studying late into the night, however conscientious it may look, removes the very hours "
        "in which what has been learned is turned into something that lasts.}",
    ],
    "vocab": [
        ("absence", "名 不在・欠如"), ("sort", "動 〜を仕分ける"),
        ("firing", "名 （神経細胞の）発火"), ("replay", "動 〜を再生する"),
        ("originally", "副 もともと"), ("deserve to do", "熟 〜するに値する"),
        ("deprive A of B", "熟 A から B を奪う"), ("recall", "動 〜を思い出す"),
        ("afterward", "副 その後"), ("tiredness", "名 疲労"),
        ("conscientious", "形 まじめな・勤勉な"),
        ("make sense", "熟 意味をなす・筋が通る"), ("the very ~", "熟 まさにその〜"),
        ("material", "名 学習内容・教材"), ("lie still", "熟 じっと横たわる"),
        ("last", "動 続く・持続する"),
    ],
    "sents": [
        {
            "dsl": "{S:Sleep} {V:looks} {C:like the absence} <of activity> , {接:but} {S:the brain} "
                   "<{S':that} {V':appears to be resting}> {V:is} {M:in fact} {C:busy} "
                   "( sorting the day ) .",
            "pat": "第2文型（SVC）＋第2文型（SVC）",
            "tag": "look like / 関係代名詞 that / be busy doing",
            "notes": [
                "look like +名詞「〜のように見える」。like は品詞としては<b>前置詞</b>だが、"
                "Sleep＝the absence of activity という <b>S = C の関係</b>が成り立つ。"
                "補語かどうかは「外せるか」ではなく<b>S とイコールで結べるか</b>で判定する。"
                "したがってここは修飾語ではなく C で、前半は第 2 文型。",
                "[ that appears to be resting ] は the brain にかかる関係詞節。"
                "appear to do は「〜のように見える」で<b>ひとかたまりの述語</b>として扱う。",
                "S（the brain）と V（is）が関係詞節で引き離されている。"
                "[ ] を外して the brain is busy … と読むのが第一手。",
                "be busy doing「〜するのに忙しい」。( sorting the day ) は busy を修飾する。",
            ],
            "ja": "睡眠は活動が無い状態のように見えるが、休んでいるように見える脳は実際には"
                  "その日を仕分けるのに忙しい。",
        },
        {
            "dsl": "( During the hours <{M':when} {S':we} {V':lie} {C':still}> ) , {S:patterns} "
                   "<of firing> <recorded ( {接:while} {S':we} {V':were} {C':awake} )> "
                   "{V:are replayed} , {M:sometimes} ( faster {接:than} {S':they} {M':originally} "
                   "{V':occurred} ) .",
            "pat": "第3文型の受動態（SV）",
            "tag": "関係副詞 when / 過去分詞＋副詞節の割り込み / 比較",
            "notes": [
                "S から V までが<b>最長の距離</b>にある文。"
                "S の核は patterns で、[ of firing ][ recorded … ] が続けてかかり、"
                "ようやく V の are replayed に届く。",
                "[ recorded while we were awake ] の中に副詞節 ( while … ) が"
                "入れ子になっている。"
                "recorded は過去分詞（記録された）で、were を V と早合点しないこと。",
                "lie still は「じっと横たわる」。still は<b>形容詞で C′</b>（副詞「まだ」ではない）。"
                "lie は自動詞なので後ろに O は来ない。",
                "( faster than they originally occurred ) は are replayed を修飾する副詞のカタマリ。"
                "比べているのは「再生される速さ」と「もともと起きた速さ」。",
            ],
            "ja": "私たちがじっと横たわっている時間帯に、起きている間に記録された発火のパターンが"
                  "再生される。ときには、もともと起きたときよりも速く再生される。",
        },
        {
            "dsl": "[S: {O':What} {S':the brain} {V':seems to be doing} ] {V:is} "
                   "[C: deciding [ {S':which} <of the day's experiences> {V':deserve to be kept} ] ] .",
            "pat": "第2文型（SVC）",
            "tag": "関係代名詞 what / 疑問詞節 / 動名詞",
            "notes": [
                "骨組みは <b>〈名詞のカタマリ〉 is 〈名詞のカタマリ〉</b>。",
                "what 節の中では what が doing の<b>目的語</b>（O′）を兼ねている。"
                "「脳がしているように見えること」。"
                "P1 の What surprises …（what が主語）と役割が違う点を比べること。",
                "〈 deciding … 〉 は is の補語となる動名詞句。",
                "〈 which of the day's experiences deserve to be kept 〉 は "
                "deciding の目的語となる<b>疑問詞節</b>「その日の経験のうちどれが〜か」。"
                "which が S′ で、deserve に三単現の s が付かないのは "
                "which が複数の experiences を指しているから。",
            ],
            "ja": "脳がしているように見えるのは、その日の経験のうちどれが残すに値するかを"
                  "決めるという作業である。",
        },
        {
            "dsl": "{V:Deprive} {O:a student} ( of sleep ) ( on the night <after a lesson> ) , "
                   "{接:and} {S:the material} {V:is} {M:usually} {C:far harder} ( to recall ) "
                   "( a week later ) , ( {接:even if} {S':the student} {V':sleeps} {M':normally} "
                   "{M':afterward} ) .",
            "pat": "命令文（第3文型）＋第2文型（SVC）",
            "tag": "命令文, and … / deprive A of B / 不定詞の副詞用法",
            "notes": [
                "文頭が原形動詞 Deprive＝<b>命令文</b>。主語 You が省略されているので S が無い。",
                "<b>命令文, and …</b>「〜しなさい、そうすれば…」。"
                "ここでは「〜してみなさい、そうすれば…になる」と条件を表す。"
                "If you deprive … と書き換えられる。",
                "deprive A of B「A から B を奪う」。of は<b>分離の of</b>。",
                "harder to recall の ( to recall ) は<b>不定詞の副詞用法</b>で "
                "harder の範囲を限定する「思い出すのが」。far は比較級を強める副詞。",
                "( even if … )「たとえ〜だとしても」は譲歩の副詞のカタマリ。",
            ],
            "ja": "授業のあった日の夜に生徒から睡眠を奪ってみなさい。そうすれば、"
                  "その後は普通に眠ったとしても、一週間後にその内容を思い出すのはたいていはるかに難しくなる。",
        },
        {
            "dsl": "( Only {接:when} {S':this process} {V':is understood} ) {助:does} "
                   "{S:the familiar advice} {V:make} {O:sense} .",
            "pat": "第3文型（SVO）／倒置",
            "tag": "Only + 副詞節の文頭倒置",
            "notes": [
                "<b>Only</b> を伴う副詞のカタマリが文頭に出ると、"
                "主節が<b>疑問文と同じ語順</b>に倒置される（助動詞＋S＋動詞の原形）。"
                "ここでは does the familiar advice make sense がその形。",
                "does は強調の do ではなく、<b>倒置のために持ち出された助動詞</b>。"
                "倒置を戻すと The familiar advice makes sense only when this process is understood. となる。",
                "「この過程が理解されて<b>はじめて</b>、よく聞くあの助言は筋が通る」と"
                "「はじめて」を補って訳すのが定訳。",
                "make sense は「意味をなす・筋が通る」。sense が O。",
            ],
            "ja": "この過程が理解されてはじめて、よく耳にするあの助言は筋が通る。",
        },
        {
            "dsl": "[S: Studying late into the night ] , ( {M':however} {C':conscientious} {S':it} "
                   "{V':may look} ) , {V:removes} {O:the very hours} <{M':in which} "
                   "[S': {S'':what} {V'':has been learned} ] {V':is turned} "
                   "{C':into something} <{S'':that} {V'':lasts}>> .",
            "pat": "第3文型（SVO）",
            "tag": "動名詞が主語 / 複合関係副詞 however / 前置詞＋関係代名詞",
            "notes": [
                "S は 〈 Studying late into the night 〉（動名詞句）。"
                "V は removes、O は the very hours。"
                "コンマに挟まれた ( however … ) を外せば骨組みが見える。",
                "however + 形容詞 + S + V「どれほど〜であっても」。"
                "<b>however の直後に形容詞 conscientious が引き寄せられる</b>語順が急所。"
                "No matter how conscientious it may look と同意。",
                "[ in which … ] は the very hours にかかる関係詞節。"
                "in which の後ろは欠けのない完全な文になる。",
                "その関係詞節の S′ が 〈 what has been learned 〉（名詞節）＝「学ばれたこと」、"
                "V′ が is turned。turn A into B「A を B に変える」の受動態で、"
                "into 以下は外せない<b>補語相当</b>なので C′ とする"
                "（P3 の be read as C と同じ扱い）。",
                "[ that lasts ] は something にかかる関係詞節。last は動詞で「続く」。",
            ],
            "ja": "夜遅くまで勉強することは、どれほどまじめに見えたとしても、"
                  "学んだことが長続きするものへと変えられる、まさにその時間を奪ってしまう。",
        },
    ],
    "mcq": [
        {"q": "下線部 (2) の主節の主語（S）と述語動詞（V）の組み合わせとして正しいものはどれか。",
         "choices": ["S = patterns / V = are replayed",
                     "S = the hours / V = lie",
                     "S = we / V = were",
                     "S = firing / V = recorded"],
         "ans": 0,
         "exp": "of firing と recorded while we were awake はいずれも patterns にかかる修飾。"
                "これらを外すと patterns … are replayed という骨組みが残る。"},
        {"q": "下線部 (3) の <span class=\"en\">What the brain seems to be doing</span> の"
              "働きはどれか。",
         "choices": ["is の補語となる名詞のカタマリ",
                     "deciding の目的語となる名詞のカタマリ",
                     "文全体の主語となる名詞のカタマリ",
                     "時を表す副詞のカタマリ"],
         "ans": 2,
         "exp": "直後に is があり、その後ろに deciding … という補語が続く。"
                "したがって what 節は文全体の S。"},
        {"q": "下線部 (5) で <span class=\"en\">does</span> が用いられている理由はどれか。",
         "choices": ["動詞 make の意味を強調するため",
                     "Only を伴う副詞節が文頭に出て倒置が起きたから",
                     "この文が疑問文の形をとっているから",
                     "前に出た動詞句を受ける代動詞だから"],
         "ans": 1,
         "exp": "Only when …, Not until …, Little … など否定・限定の副詞句が文頭に出ると、"
                "主節は助動詞＋S＋原形の語順に倒置される。does はそのために補われた助動詞。"},
        {"q": "下線部 (6) の <span class=\"en\">in which</span> が導く関係詞節の主語（S）は"
              "どれか。",
         "choices": ["the very hours", "something", "Studying late into the night",
                     "what has been learned"],
         "ans": 3,
         "exp": "in which の後ろは完全な文になる。その文の主語は名詞節 what has been learned"
                "（学ばれたこと）で、述語動詞は is turned。"},
    ],
    "trans": [
        {"n": 1, "points": ["[ that appears to be resting ] を the brain にかかる"
                            "関係詞節として訳せているか",
                            "be busy doing「〜するのに忙しい」を訳せているか",
                            "but の前後が「見かけ」と「実際」の対比になっていると訳出できているか"]},
        {"n": 4, "points": ["命令文, and …「〜しなさい、そうすれば…」の構文として訳せているか",
                            "deprive A of B「A から B を奪う」を訳せているか",
                            "even if「たとえ〜だとしても」を譲歩で訳せているか"]},
    ],
    "fulltrans": [
        "(1) 睡眠は活動が無い状態のように見えるが、休んでいるように見える脳は実際には"
        "その日を仕分けるのに忙しい。"
        "(2) 私たちがじっと横たわっている時間帯に、起きている間に記録された発火のパターンが"
        "再生される。ときには、もともと起きたときよりも速く再生される。"
        "(3) 脳がしているように見えるのは、その日の経験のうちどれが残すに値するかを"
        "決めるという作業である。",

        "(4) 授業のあった日の夜に生徒から睡眠を奪ってみなさい。そうすれば、"
        "その後は普通に眠ったとしても、一週間後にその内容を思い出すのはたいていはるかに難しくなる。"
        "その損害は疲労によってではなく、仕分けそのものが失われることによって生じる。",

        "(5) この過程が理解されてはじめて、よく耳にするあの助言は筋が通る。"
        "(6) 夜遅くまで勉強することは、どれほどまじめに見えたとしても、"
        "学んだことが長続きするものへと変えられる、まさにその時間を奪ってしまう。",
    ],
}

PASSAGES = [P1, P2, P3, P4]
