# -*- coding: utf-8 -*-
"""第1部 標準レベル（地方国公立の易しめ／日東駒専・産近甲龍 レベル）37問／100点

★難関版（scripts/eng_kokkoritsu_nankan/）との違い
- 四択を大問1に置く。この帯の大学は選択式を実際に出すし、手が止まりにくい。
- 一文が短く、修飾のかたまりは一つまで。
- 英文和訳は1文、和文英訳も1文で、日本語をそのまま英語の型に載せられるものにする。
"""

PART = {
    "no": 1,
    "level": "標準レベル",
    "univ": "地方国公立の易しめ／日本大・東洋大・駒澤大・専修大・京都産業大・近畿大 レベル",
    "aim": "基礎の確認。中学〜高1で習う型を、入試の形で使えるかを見る。"
           "一文が短く、迷う要素は一つだけ。ここが8割取れたら第2部へ進む。",
    "time": 50,
    "total": 100,
    "sections": [
        # ============================================================ 大問1
        {
            "no": 1, "kind": "mc", "pt": 2,
            "title": "空所補充（四択）",
            "inst": "次の各文の空所に入る最も適切なものを、①〜④から一つ選べ。",
            "items": [
                {
                    "stem": "I have known him (        ) we were children.",
                    "choices": ["for", "since", "during", "while"],
                    "ans": 1,
                    "exp": "since は「〜して以来」で、後ろに節（we were children）を置ける。"
                           "for は期間の長さ（for ten years）を表し節を導けない。"
                           "during は前置詞で名詞のみ。while は節を導けるが「〜する間」で"
                           "現在完了の起点にはならない。",
                    "point": "現在完了＋since＋過去の一点／for＋期間の長さ。",
                },
                {
                    "stem": "She is looking forward to (        ) her cousin next month.",
                    "choices": ["see", "seeing", "be seen", "have seen"],
                    "ans": 1,
                    "exp": "look forward to の to は前置詞なので、後ろは動名詞になる。"
                           "同じ形に be used to doing、object to doing がある。"
                           "「会う」側なので受動の be seen は不可。",
                    "point": "look forward to＋doing。to を不定詞と間違えない。",
                },
                {
                    "stem": "The book (        ) I borrowed from the library was very useful.",
                    "choices": ["what", "who", "which", "whose"],
                    "ans": 2,
                    "exp": "先行詞が the book（物）で、関係詞節の中で borrowed の目的語が"
                           "欠けているので目的格の which。"
                           "what は先行詞をとれない。whose は後ろに名詞が続く。",
                    "point": "先行詞が物＋節に欠けがある→which（that も可）。",
                },
                {
                    "stem": "If it (        ) tomorrow, we will cancel the picnic.",
                    "choices": ["will rain", "rains", "rained", "would rain"],
                    "ans": 1,
                    "exp": "時・条件を表す副詞節の中では、未来のことも現在形で表す。"
                           "主節の we will cancel が未来を示しているので、if 節は rains。"
                           "「〜かどうか」の名詞節の if なら will も使える点と区別する。",
                    "point": "時・条件の副詞節では未来を現在形で表す。",
                },
                {
                    "stem": "There (        ) a lot of people waiting in front of the station.",
                    "choices": ["is", "was", "were", "has been"],
                    "ans": 2,
                    "exp": "There 構文では be 動詞の後ろの名詞が主語。"
                           "a lot of people は複数なので were。"
                           "waiting は people を後ろから修飾する現在分詞。",
                    "point": "There is [are] の後ろの名詞が主語。数を合わせる。",
                },
                {
                    "stem": "This question is much (        ) than the last one.",
                    "choices": ["difficult", "more difficult", "most difficult",
                                "the difficult"],
                    "ans": 1,
                    "exp": "than があるので比較級 more difficult。"
                           "difficult のように音節の多い形容詞は -er ではなく more を付ける。"
                           "比較級を強めるのは much / far / a lot で、very は原級専用。",
                    "point": "長い形容詞の比較級は more＋原級。強調は much / far。",
                },
                {
                    "stem": "My father made me (        ) the dishes after dinner.",
                    "choices": ["to wash", "washing", "wash", "washed"],
                    "ans": 2,
                    "exp": "make は使役動詞で〈make＋O＋原形〉。to は付けない。"
                           "let / have も同じ。"
                           "ただし受動態では I was made to wash ... と to が復活する。",
                    "point": "使役動詞 make [let / have]＋O＋原形。",
                },
                {
                    "stem": "He speaks English as (        ) as his brother does.",
                    "choices": ["good", "well", "better", "best"],
                    "ans": 1,
                    "exp": "as ... as の間には原級が入る。ここは動詞 speaks を修飾するので"
                           "副詞 well。good は形容詞なので名詞や補語に使う。",
                    "point": "as ... as の間は原級。動詞を修飾するなら副詞。",
                },
                {
                    "stem": "I don't know (        ) he will come to the party.",
                    "choices": ["that", "whatever", "whether", "which"],
                    "ans": 2,
                    "exp": "「〜かどうか」は whether（または if）。"
                           "that だと「〜ということ」で意味が通らない。"
                           "後ろの節に欠けがないので what / which は不可。",
                    "point": "「〜かどうか」＝whether [if]＋完全な文。",
                },
                {
                    "stem": "The letter (        ) in French, so I could not read it.",
                    "choices": ["wrote", "was written", "has written", "writing"],
                    "ans": 1,
                    "exp": "手紙は「書かれる」側なので受動態 was written。"
                           "write は他動詞で、能動なら目的語が必要になる。",
                    "point": "主語が「される」側なら受動態〈be＋過去分詞〉。",
                },
                {
                    "stem": "It is important (        ) us to protect the environment.",
                    "choices": ["of", "for", "to", "with"],
                    "ans": 1,
                    "exp": "形式主語構文で不定詞の意味上の主語を示すのは for A。"
                           "kind / careless / foolish など人の性質を表す形容詞のときだけ of A になる。",
                    "point": "It is 形容詞 for A to do。人の性質を表す形容詞なら of A。",
                },
                {
                    "stem": "She has two brothers; one is a doctor and (        ) is a teacher.",
                    "choices": ["another one", "other", "the other", "others"],
                    "ans": 2,
                    "exp": "2つのうち「一方」と「残りのもう一方」は one ... the other ...。"
                           "残りが1つに決まるので the が付く。"
                           "3つ以上で「もう一つ」なら another。",
                    "point": "2つなら one / the other、3つ以上なら one / another / the others。",
                },
            ],
        },
        # ============================================================ 大問2
        {
            "no": 2, "kind": "order", "pt": 3,
            "title": "語句整序",
            "inst": "日本語の意味を表すように、[  ] 内の語をすべて並べ替えて英文を完成させよ。"
                    "ただし、文頭に来るべき語も小文字で示してある。",
            "items": [
                {
                    "ja": "その知らせを聞いて、彼女はとてもうれしそうだった。",
                    "frame": "She [            ] the news.",
                    "tokens": ["happy", "hear", "looked", "to", "very"],
                    "ans": "looked very happy to hear",
                    "exp": "look＋形容詞で「〜に見える」。"
                           "to hear は感情の原因を表す副詞的用法の不定詞で、"
                           "happy / glad / sorry / surprised の後ろによく続く。",
                    "point": "感情を表す形容詞＋to do＝〜して…だ（原因）。",
                },
                {
                    "ja": "この町には訪れる価値のある場所がたくさんある。",
                    "frame": "There [            ] in this town.",
                    "tokens": ["are", "many", "places", "visiting", "worth"],
                    "ans": "are many places worth visiting",
                    "exp": "be worth doing「〜する価値がある」の worth doing が"
                           "places を後ろから修飾している。"
                           "doing は能動の形のまま受動の意味（訪れられる価値がある）を表すので、"
                           "worth being visited とはしない。",
                    "point": "名詞＋worth doing＝〜する価値のある…。",
                },
                {
                    "ja": "私たちは彼が来るのを午前中ずっと待った。",
                    "frame": "We [            ] all morning.",
                    "tokens": ["come", "for", "him", "to", "waited"],
                    "ans": "waited for him to come",
                    "exp": "wait for A to do「Aが〜するのを待つ」。"
                           "for him は不定詞の意味上の主語で、"
                           "「彼が来る」という関係を示している。"
                           "wait A to do とは言えない。",
                    "point": "wait for A to do。for A が不定詞の意味上の主語。"
                             "（for an hour のような for と重ならないよう注意）",
                },
                {
                    "ja": "私は彼に駅への行き方を尋ねた。",
                    "frame": "I asked him [            ] the station.",
                    "tokens": ["get", "how", "to", "to"],
                    "ans": "how to get to",
                    "exp": "〈疑問詞＋to do〉で「どのように〜すべきか」。"
                           "how to get to A は「Aへの行き方」の定型。"
                           "get to A の to を落とさないこと。",
                    "point": "how [what / where]＋to do は名詞のかたまり。",
                },
                {
                    "ja": "私が昨日会った女性は、彼の叔母だった。",
                    "frame": "The woman [            ] his aunt.",
                    "tokens": ["I", "met", "was", "yesterday"],
                    "ans": "I met yesterday was",
                    "exp": "The woman の後ろに目的格の関係代名詞が省略されている（接触節）。"
                           "「名詞＋主語＋動詞」と続いたら省略を疑う。"
                           "文全体の動詞は was。",
                    "point": "名詞＋SV… と続いたら関係代名詞の省略。",
                },
                {
                    "ja": "彼は宿題を終えてしまうまで外出しなかった。",
                    "frame": "He did not go out [            ] his homework.",
                    "tokens": ["finished", "had", "he", "until"],
                    "ans": "until he had finished",
                    "exp": "外出しなかった時点より前に宿題が終わっているので過去完了。"
                           "until は「〜するまでずっと」で、否定文と組むと"
                           "「〜して初めて…する」の意味になる。",
                    "point": "過去のある時点より前のことは過去完了。",
                },
                {
                    "ja": "この写真を見ると、私は子どものころを思い出す。",
                    "frame": "This picture [            ] my childhood.",
                    "tokens": ["me", "of", "reminds"],
                    "ans": "reminds me of",
                    "exp": "remind A of B「AにBを思い出させる」。"
                           "無生物主語なので「この写真を見ると私は〜を思い出す」と訳し上げる。"
                           "同型に inform A of B、rob A of B がある。",
                    "point": "remind [inform / rob] A of B。",
                },
                {
                    "ja": "彼が来られないのは残念だ。",
                    "frame": "[            ] he cannot come.",
                    "tokens": ["a", "is", "it", "pity", "that"],
                    "ans": "It is a pity that",
                    "exp": "It が形式主語で、that 節が本当の主語。"
                           "It is a pity [shame] that ... は「〜は残念だ」の定型。"
                           "この It を「それは」と訳さない。",
                    "point": "形式主語 It ＋ that 節。It は訳さない。",
                },
                {
                    "ja": "母は私に部屋を掃除するように言った。",
                    "frame": "My mother [            ] my room.",
                    "tokens": ["clean", "me", "to", "told"],
                    "ans": "told me to clean",
                    "exp": "tell A to do「Aに〜するように言う」。"
                           "ask / want / advise も同じ〈V＋O＋to do〉。"
                           "say は say to A that ... の形で、say A to do とはできない。",
                    "point": "tell [ask / want]＋O＋to do。say は不可。",
                },
                {
                    "ja": "この本は易しい英語で書かれているので、読みやすい。",
                    "frame": "This book, [            ], is easy to read.",
                    "tokens": ["English", "in", "simple", "which", "is", "written"],
                    "ans": "which is written in simple English",
                    "exp": "コンマではさんだ非制限用法の関係代名詞で、"
                           "先行詞 this book に説明を加えている。"
                           "本は「書かれる」側なので受動態 is written。",
                    "point": "コンマ＋which は先行詞に説明を足す（非制限用法）。",
                },
            ],
        },
        # ============================================================ 大問3
        {
            "no": 3, "kind": "fill", "pt": 2,
            "title": "空所補充（記述）",
            "inst": "次の各文の空所に入る最も適切な語を書け。( ) 内に語が示されている場合は、"
                    "示された語をすべて使い、適切な形に変えて書け（形を変える必要がなければ"
                    "そのまま書く）。頭文字が示されている場合はその文字で始まる語を書け。",
            "items": [
                {
                    "stem": "The window (        ) by someone last night.",
                    "given": "be, break",
                    "ans": "was broken", "accept": [],
                    "exp": "窓は「割られる」側なので受動態〈be＋過去分詞〉。"
                           "last night があるので be 動詞は過去形 was。"
                           "break の過去分詞は broken（broke は過去形）。",
                    "point": "受動態は〈be＋過去分詞〉。過去分詞の形に注意。",
                },
                {
                    "stem": "I am interested (   i    ) learning about other cultures.",
                    "hint": "i",
                    "ans": "in", "accept": [],
                    "exp": "be interested in A「Aに興味がある」。"
                           "in は前置詞なので後ろは動名詞 learning。"
                           "be surprised at、be satisfied with も感情を表す受動態の定型。",
                    "point": "be interested in＋名詞／動名詞。",
                },
                {
                    "stem": "He is the tallest (   o    ) all the students in his class.",
                    "hint": "o",
                    "ans": "of", "accept": [],
                    "exp": "最上級の範囲を示すとき、複数を表す語句の前は of、"
                           "場所や集団を表す単数名詞の前は in を使う。"
                           "ここは all the students（複数）なので of。",
                    "point": "最上級の範囲＝of＋複数／in＋場所・集団。",
                },
                {
                    "stem": "She kept (        ) along the river for more than an hour.",
                    "given": "walk",
                    "ans": "walking", "accept": [],
                    "exp": "keep doing「〜し続ける」。"
                           "keep は動名詞を目的語にとる動詞で、to 不定詞はとらない。"
                           "enjoy / finish / stop / mind も同じ。",
                    "point": "keep [enjoy / finish / mind]＋doing。",
                },
                {
                    "stem": "(   N    ) of my three friends has ever been to Australia.",
                    "hint": "N",
                    "ans": "None", "accept": [],
                    "exp": "None of A で「Aのうち誰も〜ない」。"
                           "3人なので Neither（2者限定）は使えない。"
                           "後ろの has が単数なので None（No one of とは言わない）。"
                           "ever は否定文脈で「これまでに」の意味を強める。",
                    "point": "None of A＋単数動詞（複数も可）。",
                },
                {
                    "stem": "He was busy (        ) for the entrance examination all last month.",
                    "given": "prepare",
                    "ans": "preparing", "accept": [],
                    "exp": "be busy doing「〜するのに忙しい」。"
                           "be busy with＋名詞 の形もあるが、動詞を続けるときは動名詞。"
                           "to prepare とはしない。",
                    "point": "be busy doing。to 不定詞は不可。",
                },
                {
                    "stem": "Do you mind (        ) the window? It is a little cold in here.",
                    "given": "close",
                    "ans": "closing", "accept": [],
                    "exp": "Do you mind doing?「〜していただけませんか」。"
                           "mind は動名詞をとる。"
                           "承諾するときは No, not at all.（＝気にしません）と答える点も要注意。",
                    "point": "Do you mind doing? の答えは No が承諾。",
                },
                {
                    "stem": "The train had already left (        ) we arrived at the station.",
                    "ans": "when", "accept": ["before"],
                    "exp": "過去完了 had left が示すのは「駅に着いた時点よりも前」。"
                           "その基準となる過去の一点を when 節が示している。"
                           "before でも成立するが、その場合は基準点の前後関係が重複する。",
                    "point": "過去完了は「過去のある時点」を基準に使う。",
                },
                {
                    "stem": "This is the house (        ) my grandfather lived for fifty years.",
                    "ans": "where", "accept": ["in which"],
                    "exp": "先行詞が場所 the house で、後ろの節に欠けがない"
                           "（lived は自動詞で目的語不要）ので関係副詞 where。"
                           "in which と書き換えられる。"
                           "which だけにすると lived in which と前置詞が必要になる。",
                    "point": "先行詞が場所＋完全な文→where（＝in which）。",
                },
            ],
        },
        # ============================================================ 大問4
        {
            "no": 4, "kind": "jtrans", "pt": 6,
            "title": "英文和訳",
            "inst": "次の各文の下線部を日本語に訳せ。下線のない部分は文脈として示したもので、"
                    "訳す必要はない。",
            "items": [
                {
                    "context": "My grandmother lived in a small village all her life.",
                    "src": "She often told me that the people in her village were happy "
                           "because they were satisfied with what they already had.",
                    "model": "彼女はよく私に、村の人たちは、すでに持っているもので満足していたから"
                             "幸せだったのだ、と話していた。",
                    "alts": ["祖母は私によく、村の人々が幸福だったのは、"
                             "すでに手にしているもので満ち足りていたからだ、と言っていた。"],
                    "elements": [["because 節の因果関係を訳出できている", 2],
                                 ["be satisfied with A の「Aで満ち足りている」という意味を"
                                  "訳出できている。語句は問わない", 2],
                                 ["already の「すでに」の含意を落とさずに訳出できている。"
                                  "語句は問わない", 2]],
                    "exp": "told me that ... の that 節の中に、さらに because 節が入っている。"
                           "what they already had は前置詞 with の目的語になる名詞節で、"
                           "「すでに持っているもの」。"
                           "already を訳し落とすと「持っているもの」となり原文の含みが消える。",
                    "point": "前置詞の目的語になる what 節。修飾語（already）を落とさない。"
                },
                {
                    "context": "Some students give up after only a few weeks.",
                    "src": "What matters is not how many words you memorize in a day, but "
                           "whether you keep studying every day without giving up.",
                    "model": "大切なのは、一日に何語覚えるかではなく、"
                             "あきらめずに毎日勉強を続けるかどうかである。",
                    "alts": ["重要なのは、一日にいくつ単語を暗記するかということではなく、"
                             "投げ出さずに毎日学習を続けられるかどうかだ。"],
                    "elements": [["What matters is ... を「大切なのは…である」と訳せている", 2],
                                 ["how many words you memorize の間接疑問を訳せている", 2],
                                 ["whether ... を「〜かどうか」と訳せている", 2]],
                    "exp": "文頭の What は先行詞を含む関係代名詞で、What matters が主語。"
                           "is の後ろが not A but B で、A も B も名詞のかたまり"
                           "（間接疑問と whether 節）になっている。",
                    "point": "What で始まる主語は「〜すること・もの」。",
                },
            ],
        },
        # ============================================================ 大問5
        {
            "no": 5, "kind": "trans", "pt": 4,
            "title": "和文英訳",
            "inst": "次の日本語を英語に訳せ。",
            "items": [
                {
                    "ja": "彼は毎朝6時に起きて、学校まで歩いて行く。",
                    "model": "He gets up at six every morning and walks to school.",
                    "alts": ["Every morning he wakes up at six and goes to school on foot."],
                    "elements": [["「起きる」を get up / wake up で表せている", 1],
                                 ["主語が三人称単数なので動詞に -s を付けられている", 1],
                                 ["「毎朝」を every morning で表せている", 1],
                                 ["「歩いて行く」を walk to / go on foot で表せている", 1]],
                    "exp": "習慣は現在形で表す。"
                           "主語が he なので gets / walks と -s を付ける。"
                           "and でつないだ2つ目の動詞にも -s が必要な点を落としやすい。",
                },
                {
                    "ja": "私は昨日、駅で偶然古い友人に会った。",
                    "model": "I happened to meet an old friend at the station yesterday.",
                    "alts": ["Yesterday I ran into an old friend of mine at the station."],
                    "elements": [["「偶然〜する」を happen to do / run into で表せている", 1],
                                 ["過去形で表せている", 1],
                                 ["「古い友人」を an old friend で表せている", 1],
                                 ["「駅で」を at the station で表せている", 1]],
                    "exp": "「偶然〜する」は happen to do が最も安全。"
                           "「古い友人」は an old friend で、「年老いた友人」の意味にはならない。"
                           "場所の at と時の yesterday の語順は〈場所→時〉。",
                },
                {
                    "ja": "この本は難しすぎて、私には理解できなかった。",
                    "model": "This book was too difficult for me to understand.",
                    "alts": ["This book was so difficult that I could not understand it."],
                    "elements": [["過去形で too ... to do または so ... that S could not ~ の型で"
                                  "表せている", 1],
                                 ["「私には」を for me（または that 節の主語 I）で表せている", 1],
                                 ["「理解する」を understand で表せている", 1],
                                 ["選んだ型に応じて it の有無が正しい（too ... to では置かない／"
                                  "so ... that では置く）", 1]],
                    "exp": "too ... to do では、不定詞の目的語が文の主語と同じなので"
                           "understand it とはしない。"
                           "so ... that に書き換えたときは that 節が独立した文なので it が必要。",
                },
                {
                    "ja": "彼女がその試験に合格したと聞いて、私はうれしかった。",
                    "model": "I was glad to hear that she had passed the exam.",
                    "alts": ["It made me happy to hear that she passed the examination."],
                    "elements": [["「〜してうれしい」を be glad [happy] to do や "
                                  "It made me happy to do などで表せている", 1],
                                 ["「〜と聞いて」を hear that ... で表せている", 1],
                                 ["「合格した」を pass the exam で表せている", 1],
                                 ["was glad との時間関係を過去完了 had passed か過去形で"
                                  "示せている", 1]],
                    "exp": "感情の原因は〈形容詞＋to do〉で表す。"
                           "「合格した」のは「うれしかった」より前なので had passed が正確だが、"
                           "文脈が明らかなので passed でもよい。",
                },
            ],
        },
    ],
}
