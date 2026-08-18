# -*- coding: utf-8 -*-
"""第3回 上位レベル（GMARCH・地方国公立の文法問題と同程度の難度）20問／100点

- 第1・2回と同じ 四択10＋語句整序5＋誤り指摘5・制限時間25分。
- 一文が長く、構造をつかまないと空所の役割が見えない問題を集める。
  「細かい知識」ではなく「文の骨格が読めているか」で差がつく帯。
"""

PART = {
    "no": 3,
    "level": "上位レベル",
    "univ": "GMARCH・地方国公立の文法問題と同程度の難度",
    "aim": "一文が長く、空所の前後だけを見ても答えが決まらない問題を集めた回。"
           "主語と動詞の骨格をつかんでから空所の役割を決める。"
           "ここで8割取れたら、早慶・旧帝大レベルの文法問題集へ進んでよい"
           "（本書はその手前までを扱う）。",
    "time": 25,
    "total": 100,
    "sections": [
        # ============================================================ 大問1
        {
            "no": 1, "kind": "mc", "pt": 4,
            "title": "空所補充（四択）",
            "inst": "次の各文の空所に入る最も適切なものを、①〜④から一つ選べ。",
            "items": [
                {
                    "stem": "The researcher proposed that the new drug (        ) "
                            "to a wider group of patients before its release.",
                    "choices": ["be administered", "is administered",
                                "will be administered", "administers"],
                    "ans": 0,
                    "exp": "propose・suggest・demand・insist・recommend などが"
                           "「〜すべきだ」という提案・要求の意味で that 節を取るとき、"
                           "節の中の動詞は原形になる（should が省略された形）。"
                           "薬は「投与される」側なので、原形の be を使って be administered。"
                           "is / will be administered はこの型では使わない。"
                           "administers では薬が投与する側になってしまう。",
                    "point": "propose・demand・insist that S＋動詞の原形（提案・要求）。",
                },
                {
                    "stem": "Rarely (        ) such a detailed account of "
                            "the incident from an eyewitness.",
                    "choices": ["have we heard", "we have heard",
                                "we heard have", "did we heard"],
                    "ans": 0,
                    "exp": "Rarely・Seldom・Never・Little など否定の意味を持つ副詞が文頭に出ると、"
                           "その後ろは疑問文と同じ語順（助動詞＋主語＋動詞）になる。"
                           "have we heard が正しい。we have heard は語順が戻ってしまい、"
                           "we heard have は助動詞と動詞の位置が入れ替わっていて英語の語順にならない。"
                           "did we heard は did の後ろが原形でない点でも誤り。",
                    "point": "否定の副詞が文頭に出ると、後ろは疑問文の語順になる。",
                },
                {
                    "stem": "The committee members could not agree on "
                            "(        ) the deadline should be extended.",
                    "choices": ["whether", "that", "which", "what"],
                    "ans": 0,
                    "exp": "前置詞 on の後ろに置ける名詞のかたまりを作り、かつ"
                           "「延ばすべきかどうか」という意味になるのは whether。"
                           "that 節は前置詞の直後に置けない。"
                           "which / what を使うなら後ろの文に欠けが必要だが、"
                           "the deadline should be extended は部品がそろっている。",
                    "point": "前置詞の後ろで「〜かどうか」を言えるのは whether（if は不可）。",
                },
                {
                    "stem": "The novel, (        ) was published posthumously, "
                            "is now regarded as her masterpiece.",
                    "choices": ["which", "that", "what", "it"],
                    "ans": 0,
                    "exp": "コンマで挟んで補足説明を加える形（継続用法）では that を使えない。"
                           "先行詞が the novel（物）なので which が正しい。"
                           "what は先行詞を取らない。it を置くと接続詞なしで文が二つ並ぶ。",
                    "point": "コンマ＋関係詞の補足説明に that は使えない。",
                },
                {
                    "stem": "(        ) the report may be, it has to reach the committee "
                            "before Friday afternoon.",
                    "choices": ["However long", "Though long", "As long", "So long"],
                    "ans": 0,
                    "exp": "〈However＋形容詞・副詞＋S＋V〉「どんなに〜であっても」の型。"
                           "long は形容詞なので However の直後に置く。"
                           "譲歩を though で表すなら Long though the report may be と"
                           "形容詞を先頭に出す語順になり、Though long … とは言わない。"
                           "As long / So long は as long as / so long as（〜する限り）の形で"
                           "初めて使えるもので、後ろに主語＋動詞を直接続けられない。",
                    "point": "However＋形容詞・副詞＋S＋V「どんなに〜でも」。",
                },
                {
                    "stem": "It was not the technology itself (        ) transformed "
                            "the industry, but the way people chose to use it.",
                    "choices": ["that", "what", "which it", "when"],
                    "ans": 0,
                    "exp": "It was ... that ... で文の一部を強調して取り出す形。"
                           "強調されているのが the technology itself という主語なので、"
                           "その後ろは that（人なら who）で受ける。"
                           "what はこの型では使わない。which it では主語が二重になる。"
                           "when は時を取り出すときの形。",
                    "point": "It is ... that ... の強調構文。取り出した部分を that で受ける。",
                },
                {
                    "stem": "The manuscript is said (        ) in the twelfth century, "
                            "long before the invention of printing.",
                    "choices": ["to have been written", "to be written",
                                "to have written", "writing"],
                    "ans": 0,
                    "exp": "is said（今言われている）よりも書かれたのは前のことなので、"
                           "to have been written と一段古い形にする。"
                           "写本は「書かれる」側なので受け身であることも必要。"
                           "to be written では時のずれが表せず、"
                           "to have written では写本が何かを書いたことになる。"
                           "writing は is said に続く形として成立しない。",
                    "point": "本動詞より前の内容は to have＋過去分詞で表す。",
                },
                {
                    "stem": "Some critics dismissed the theory as speculative; "
                            "(        ), it later proved remarkably accurate.",
                    "choices": ["nevertheless", "therefore", "moreover", "likewise"],
                    "ans": 0,
                    "exp": "前半（根拠が薄いと退けられた）と後半（実は非常に正確だった）は"
                           "逆の向きの内容なので、逆接の nevertheless が入る。"
                           "therefore は順当な結果、moreover は追加、"
                           "likewise は同様のことを並べる語で、いずれも向きが合わない。",
                    "point": "つなぎ語は前後の向き（逆接・順接・追加）で選ぶ。",
                },
                {
                    "stem": "If the committee (        ) the risks earlier, "
                            "the project would not be so far behind schedule now.",
                    "choices": ["had recognized", "recognized", "has recognized",
                                "would recognize"],
                    "ans": 0,
                    "exp": "if 節が「もっと早い時点で」という過去の想定、"
                           "主節が now を伴う現在の結果になっている混合型の仮定法。"
                           "過去の想定は had＋過去分詞で表すので had recognized。"
                           "recognized（過去形）は現在の想定に使う形で earlier と合わない。"
                           "has recognized は仮定法では使わない。"
                           "would recognize は主節側に置く形。",
                    "point": "過去の想定＋現在の結果＝If S had done …, S would do now.",
                },
                {
                    "stem": "Wealth does not (        ) bring happiness; "
                            "some of the richest people are also the loneliest.",
                    "choices": ["necessarily", "necessary", "necessity", "necessitate"],
                    "ans": 0,
                    "exp": "not necessarily で「必ずしも〜とは限らない」。"
                           "全部を否定するのではなく、一部に例外があることを示す言い方。"
                           "空所は does not と bring の間なので、動詞を修飾する副詞の形が入る。"
                           "necessary は形容詞、necessity は名詞、necessitate は動詞で、"
                           "いずれもこの位置に置けない。",
                    "point": "not necessarily［always / all］＝「必ずしも〜ない」（一部だけの否定）。",
                },
            ],
        },
        # ============================================================ 大問2
        {
            "no": 2, "kind": "order", "pt": 6,
            "title": "語句整序",
            "inst": "日本語の意味を表すように、[  ] 内の語をすべて並べ替えて、"
                    "文として成立する英文を完成させよ。",
            "items": [
                {
                    "ja": "その資料は、一見したところ役に立ちそうになかった。",
                    "frame": "The material [            ] at first glance.",
                    "tokens": ["be", "did", "not", "seem", "to", "useful"],
                    "ans": "did not seem to be useful",
                    "exp": "seem to be＋形容詞で「〜のように見える」。"
                           "否定は seem の側に付けて did not seem to be … とするのが自然で、"
                           "did seem not to be … と並べると強調の did になり、"
                           "「役に立たないように見えた」と否定の位置がずれる。"
                           "It seemed that the material was not useful とも言い換えられる。",
                    "point": "seem to be＋形容詞。否定は seem に付ける（did not seem to be）。",
                },
                {
                    "ja": "夜に車を運転するときは、いくら注意してもしすぎることはない。",
                    "frame": "You [            ] when you drive at night.",
                    "tokens": ["be", "cannot", "careful", "too"],
                    "ans": "cannot be too careful",
                    "exp": "cannot ... too〜 で「いくら〜してもしすぎることはない」。"
                           "「〜できない」と「〜すぎる」を組み合わせて、"
                           "上限がないほど望ましいという意味を作る決まった言い方。"
                           "直訳の「注意しすぎることはできない」から意味をたどるとよい。",
                    "point": "cannot ＋動詞＋too＋形容詞・副詞「いくら〜してもしすぎない」。",
                },
                {
                    "ja": "その資料は、委員会の委員が理解するのに二、三日かかった。",
                    "frame": "The document took [            ] to understand.",
                    "tokens": ["a", "committee", "days", "few",
                               "members", "of", "the", "the"],
                    "ans": "the members of the committee a few days",
                    "exp": "〈take＋人＋時間＋to do〉「人が…するのに（時間）がかかる」。"
                           "「もの」を主語に立てて〈took＋人＋時間〉と並べる形で、"
                           "It took the members of the committee a few days to "
                           "understand the document. と書き換えられる。"
                           "of the committee は members を後ろから説明する句なので、"
                           "人を表すかたまり（the members of the committee）を"
                           "壊さずに took の直後へ置く。",
                    "point": "take＋人＋時間＋to do（It takes＋時間＋for A＋to do と対）。",
                },
                {
                    "ja": "彼女は親切にも駅まで車で送ってくれた。",
                    "frame": "She [            ] to the station.",
                    "tokens": ["as", "drive", "kind", "me", "so", "to", "was"],
                    "ans": "was so kind as to drive me",
                    "exp": "〈so＋形容詞＋as to do〉「とても〜なので…する／親切にも…する」。"
                           "was kind enough to drive me と言い換えられる。"
                           "so ... that 節との違いは、as to の後ろが動詞の原形になる点。"
                           "kind so as to drive me と並べると「送るために親切だった」という"
                           "目的の意味になり、日本語と合わない。",
                    "point": "so＋形容詞＋as to do（＝形容詞＋enough to do）。",
                },
                {
                    "ja": "私たちが当然だと思っていることの多くは、実は真実ではない。",
                    "frame": "Much of [            ] is not actually true.",
                    "tokens": ["for", "granted", "take", "we", "what"],
                    "ans": "what we take for granted",
                    "exp": "take A for granted「Aを当然のことと思う」の A が what になって"
                           "前に出た形。what は先行詞を含むので、"
                           "Much of what we take for granted（当然だと思っていることの多く）"
                           "というかたまりがそのまま主語になる。",
                    "point": "take A for granted「Aを当然と思う」＋先行詞を含む what。",
                },
            ],
        },
        # ============================================================ 大問3
        {
            "no": 3, "kind": "error", "pt": 6,
            "title": "誤り指摘",
            "inst": "次の各文の下線部 (a)〜(d) のうち、文法・語法上誤っているものを"
                    "一つ選び、正しい形に直せ（語の差し替えも含む。記号と訂正の両方で1問）。",
            "items": [
                {
                    "stem": "{a} in recent years, the number of students {b} "
                            "to study abroad {c} sharply, {d} many universities "
                            "to expand their exchange programs.",
                    "parts": ["Despite the economic slowdown", "choosing",
                              "has risen", "prompted"],
                    "ans": 3, "fix": "prompted → prompting（which prompted も可）",
                    "exp": "コンマの後ろで「その結果〜させた」と続けるのは、"
                           "主節の内容を受けて結果を表す分詞構文 prompting。"
                           "prompted と過去形にすると、接続詞なしに文が二つ並ぶ形になる。"
                           "この形の分詞構文は「そして〜した」と前から訳し下ろす。"
                           "choosing は students を後ろから説明する分詞で正しい。",
                    "point": "コンマ＋-ing で「その結果〜した」（結果を表す分詞構文）。",
                },
                {
                    "stem": "When the students asked about the experiment, the professor "
                            "{a} them the procedure in detail, {b} why each step "
                            "{c}, and then {d} them to try it themselves.",
                    "parts": ["explained", "showing", "was necessary", "encouraged"],
                    "ans": 0, "fix": "explained → explained to（told も可）",
                    "exp": "explain は〈人〉を直接目的語に取れない動詞で、"
                           "explain A to B（AをBに説明する）か explain to B A の形にする。"
                           "同じ仲間に suggest／propose／announce がある。"
                           "一方 tell・teach・show は〈人＋物〉をそのまま並べられる。",
                    "point": "explain・suggest は〈人〉の前に to が要る（explain A to B）。",
                },
                {
                    "stem": "The theory {a} by many scholars for decades {b} "
                            "when new evidence {c}, and today {d} takes it "
                            "seriously.",
                    "parts": ["accepted", "was finally abandoned", "emerged",
                              "hardly no one"],
                    "ans": 3, "fix": "hardly no one → hardly anyone（almost no one も可）",
                    "exp": "hardly はそれ自体が「ほとんど〜ない」という否定の意味を持つので、"
                           "no one と重ねると否定が二重になる。hardly anyone が正しい。"
                           "同様に can't hardly／without no も誤り。"
                           "accepted は The theory を後ろから説明する過去分詞で正しい。",
                    "point": "hardly・scarcely は否定語。no・not と重ねない。",
                },
                {
                    "stem": "The population of this city {a} much larger than {b}, "
                            "{c} the two cities {d} almost the same area.",
                    "parts": ["is now", "Kyoto", "even though", "cover"],
                    "ans": 1, "fix": "Kyoto → that of Kyoto（Kyoto's も可）",
                    "exp": "比べているのは「この市の人口」と「京都の人口」なので、"
                           "than の後ろも人口でそろえる必要がある。"
                           "the population の繰り返しを避けて that of Kyoto とする"
                           "（複数名詞なら those of）。"
                           "than Kyoto では「人口」と「都市そのもの」を比べる形になり成立しない。",
                    "point": "比較は同じ種類のものどうし。名詞の繰り返しは that［those］of で受ける。",
                },
                {
                    "stem": "The city government {a} the bridge {b} in less than a year, "
                            "which was remarkable {c} the fact that the engineers "
                            "{d} with a limited budget.",
                    "parts": ["managed to have", "repaired", "considered", "were working"],
                    "ans": 2, "fix": "considered → considering（given も可）",
                    "exp": "considering the fact that …「〜という事実を考えると」は"
                           "考える側の -ing 形で決まった言い方（前置詞のように使う）。"
                           "considered では受け身の意味になり、the fact 以下とつながらない。"
                           "given the fact that … も同じ意味で使える（given だけでも可）。"
                           "managed to have the bridge repaired は〈have＋O＋過去分詞〉"
                           "「Oを〜してもらう」で正しい。",
                    "point": "considering ＋名詞・that節「〜を考慮すると」。",
                },
            ],
        },
    ],
}
