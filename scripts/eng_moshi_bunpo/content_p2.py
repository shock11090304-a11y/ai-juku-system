# -*- coding: utf-8 -*-
"""第2回 標準〜やや難（日東駒専・地方国公立の文法問題と同程度・第1回と同じ帯）20問／100点

- 第1回と同じ 四択10＋語句整序5＋誤り指摘5・制限時間25分。
- 「知っているだけでは落とす」タイプ: 型は基本でも、文の中での見え方をひねってある。
"""

PART = {
    "no": 2,
    "level": "標準〜やや難",
    "univ": "日東駒専・地方国公立の文法問題と同程度の難度（第1回と同じ帯）",
    "aim": "第1回と同じ型を、語順の入れ替え・別の顔をした語・紛らわしい対で問い直す回。"
           "難度は第1回と大きく変えていない。同じ項目を別の角度から2度通すことで、"
           "「見たことはあるが使えない」型を潰すのがねらい。"
           "間違えた問題は、なぜ他の形ではだめなのかを言えるまで解説を読み込むこと。",
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
                    "stem": "She spoke slowly (        ) make herself understood "
                            "by the students in the back row.",
                    "choices": ["so as to", "so that to", "so to", "in order that"],
                    "ans": 0,
                    "exp": "「〜するために」と目的を表すのは so as to＋動詞の原形。"
                           "in order to も同じ意味で使える。"
                           "so that は後ろに〈S＋V〉の形を取るので、"
                           "so that to / so to という並びにはならない。"
                           "in order that も後ろに〈S＋V〉が要る（in order that they could …）。"
                           "make oneself understood は「自分の話を相手に分からせる」。",
                    "point": "目的の so as to［in order to］＋原形／so that＋S＋V。",
                },
                {
                    "stem": "You (        ) all that money on clothes; "
                            "now you can't pay the rent.",
                    "choices": ["shouldn't have spent", "must not spend",
                                "had better not spend", "don't have to spend"],
                    "ans": 0,
                    "exp": "「使うべきではなかったのに（実際は使ってしまった）」という"
                           "過去の行為への非難は shouldn't have spent で表す。"
                           "must not spend / had better not spend / don't have to spend は"
                           "どれもこれからの話で、「今や家賃が払えない」という"
                           "結果が出ている場面に合わない。",
                    "point": "should have＋過去分詞の否定形＝「〜すべきでなかったのに」。",
                },
                {
                    "stem": "(        ) in a hurry, the report contained "
                            "several careless mistakes.",
                    "choices": ["Written", "Writing", "To write", "Having written"],
                    "ans": 0,
                    "exp": "文の主語は the report。報告書は「書かれる」側なので、"
                           "過去分詞 Written で始めて「急いで書かれたので」とする。"
                           "Writing / Having written だと報告書が何かを書くことになる。"
                           "To write では「書くために報告書が誤りを含んでいた」となり意味が通らない。",
                    "point": "文頭の分詞は主語との関係で判断。「される」側なら過去分詞。",
                },
                {
                    "stem": "We were surprised at the news (        ) the old factory "
                            "would close at the end of the year.",
                    "choices": ["that", "which", "what", "of which"],
                    "ans": 0,
                    "exp": "the news の中身を後ろから言い直す同格の that。"
                           "後ろの the old factory would close は部品がそろった文なので、"
                           "欠けを埋める which / what / of which は入らない。"
                           "the fact that / the idea that も同じ形。",
                    "point": "the news［fact / idea］＋that＋完全な文＝「〜という…」（同格）。",
                },
                {
                    "stem": "The higher we climbed, (        ) it became.",
                    "choices": ["the colder", "colder", "the coldest", "much colder"],
                    "ans": 0,
                    "exp": "〈The＋比較の形 …, the＋比較の形 …〉「〜すればするほど…」の型。"
                           "後半にも the が必要なので the colder が正しい。"
                           "colder / much colder では前半の The higher と型がそろわず、"
                           "the coldest は「いちばん」の形なのでこの型に入らない。",
                    "point": "The ＋比較の形 …, the ＋比較の形 …「〜すればするほど…」。",
                },
                {
                    "stem": "(        ) you have finished your homework, "
                            "you may watch TV.",
                    "choices": ["Now that", "Even", "During", "As soon"],
                    "ans": 0,
                    "exp": "「宿題を終えた今はもう〜だから」と、新しく成立した理由を表す"
                           "Now that が正しい。Even は単独では節をつなげない"
                           "（even if / even though なら可）。During は前置詞なので"
                           "後ろに文の形を置けない。As soon は as soon as の形でなければ"
                           "節をつなげない。",
                    "point": "now that ＋ S V「今はもう〜だから」（理由）。",
                },
                {
                    "stem": "The report must be submitted (        ) noon on Friday; "
                            "late submissions will not be accepted.",
                    "choices": ["by", "until", "since", "for"],
                    "ans": 0,
                    "exp": "submit（提出する）は一回で完了する動作なので、"
                           "「〜までに」という期限の by と組む。"
                           "until は「〜までずっと」と続く状態に使う語で、"
                           "肯定文では提出のような一回きりの動作と組めない"
                           "（否定文の not ... until「〜して初めて」は別の型）。"
                           "since は起点、for は期間を示す語なので、"
                           "一回で完了する「提出」の期限を言うこの文には入らない。",
                    "point": "by＝期限「〜までに」／until＝継続「〜までずっと」。",
                },
                {
                    "stem": "I have two brothers: one lives in Tokyo, "
                            "and (        ) works overseas.",
                    "choices": ["the other", "another", "other", "the others"],
                    "ans": 0,
                    "exp": "兄弟は2人と示されているので、一人を one で挙げたら、"
                           "残りの一人は特定できる。特定の「残り一人」は the other。"
                           "another は「さらにもう一人」で2人という前提と矛盾する。"
                           "other は単独ではこの位置に置けない。the others は複数の残りを"
                           "指す上に、動詞 works とも合わない。",
                    "point": "2人のうち残りの1人＝the other。another は「別のもう1つ」。",
                },
                {
                    "stem": "The doctor (        ) me that I should get "
                            "more exercise and sleep.",
                    "choices": ["told", "said", "spoke", "talked"],
                    "ans": 0,
                    "exp": "〈tell＋人＋that節〉「人に〜と言う」の型を取れるのは told だけ。"
                           "say は人を直接目的語に取れず、say to me の形が必要。"
                           "speak / talk は「話す」という行為を表す動詞で、"
                           "後ろに人＋that節を続けられない。",
                    "point": "tell＋人＋that節。say・speak・talk は〈＋人〉を直接取れない。",
                },
                {
                    "stem": "The professor gave me several useful pieces of (        ) "
                            "about my thesis.",
                    "choices": ["advice", "advices", "an advice", "advises"],
                    "ans": 0,
                    "exp": "advice（助言）は数えられない名詞なので、そのままの形で使い、"
                           "数えるときは a piece of / pieces of を添える。"
                           "advices・an advice のように複数形や a を付ける形は無い。"
                           "advises は動詞 advise の変化形で、名詞の位置に置けない。",
                    "point": "advice・information などは pieces of で数える（複数形なし）。",
                },
            ],
        },
        # ============================================================ 大問2
        {
            "no": 2, "kind": "order", "pt": 6,
            "title": "語句整序",
            "inst": "日本語の意味を表すように、[  ] 内の語をすべて並べ替えて、"
                    "文として成立する英文を完成させよ。"
                    "文頭に来るべき語も小文字で示してある。",
            "items": [
                {
                    "ja": "彼女は誰にも相談せずに、その寛大な申し出を断ることに決めた。",
                    "frame": "She decided [            ] anyone.",
                    "tokens": ["consulting", "generous", "offer", "reject", "the", "to", "without"],
                    "ans": "to reject the generous offer without consulting",
                    "exp": "decide は目的語に to＋動詞の原形を取る（-ing 形は取らない）。"
                           "reject A で「Aを断る」（turn down と違い目的語を間に挟めない一語の他動詞）。"
                           "without は前置詞なので後ろの動詞は -ing 形にし、"
                           "without consulting anyone で「誰にも相談せずに」となる。"
                           "without＋-ing は「〜せずに」と付帯状況を表す。",
                    "point": "decide to do／without＋-ing「〜せずに」。",
                },
                {
                    "ja": "その計画は、資金不足のせいで実行に移されなかった。",
                    "frame": "The plan [            ] of funds.",
                    "tokens": ["a", "because", "carried", "lack", "not", "of",
                               "out", "was"],
                    "ans": "was not carried out because of a lack",
                    "exp": "carry out A「Aを実行する」を受動態にした形。"
                           "not は be動詞の後ろ、過去分詞の前に置く。"
                           "理由は because of＋名詞（後ろに文は続かない）で示す。"
                           "because なら because there was a lack of funds と文が続く。",
                    "point": "be動詞＋not＋過去分詞／because of＋名詞。",
                },
                {
                    "ja": "昨日、髪を切ってもらったら、思っていたよりずっと短くなってしまった。",
                    "frame": "Yesterday I [            ] I had expected.",
                    "tokens": ["cut", "got", "hair", "much", "my", "shorter", "than"],
                    "ans": "got my hair cut much shorter than",
                    "exp": "〈get＋O＋過去分詞〉「Oを〜してもらう」の型。"
                           "髪は「切られる」側なので got my hair cut。"
                           "その後ろに much shorter than …（思っていたよりずっと短く）を"
                           "続ける。much は差の大きさを強める。",
                    "point": "get［have］＋O＋過去分詞「Oを〜してもらう・される」。",
                },
                {
                    "ja": "できるだけ多くの本を読みなさい。",
                    "frame": "Read [            ].",
                    "tokens": ["as", "as", "books", "can", "many", "you"],
                    "ans": "as many books as you can",
                    "exp": "「できるだけ〜」は〈as … as one can〉（＝as … as possible）。"
                           "数えられる名詞 books を数えるので as many books as の語順になる。"
                           "many books を as と as の間に丸ごと挟む点がポイント。",
                    "point": "as many［much］＋名詞＋as one can「できるだけ多くの〜」。",
                },
                {
                    "ja": "たとえ何が起ころうとも、私たちは計画を変えるつもりはない。",
                    "frame": "[            ], we will not change our plan.",
                    "tokens": ["happens", "matter", "no", "what"],
                    "ans": "no matter what happens",
                    "exp": "〈no matter what＋V〉「たとえ何が〜しようとも」。"
                           "what が happens の主語を兼ねるので、この3語の後ろに"
                           "そのまま動詞が続く。whatever happens と1語で言い換えられる。",
                    "point": "no matter what（＝whatever）「たとえ何が〜でも」。",
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
                    "stem": "The hotel {a} we stayed last summer {b} by a famous "
                            "architect, and it {c} one of the most popular {d} "
                            "in the region.",
                    "parts": ["which", "was designed", "has become", "destinations"],
                    "ans": 0, "fix": "which → where（at which / in which も可）",
                    "exp": "stay は「泊まる」という自動詞で、後ろの文には欠けがない"
                           "（we stayed there の there に当たる語が要るだけ）。"
                           "欠けのない文をつなぐのは where（または at which）。"
                           "which を使うなら stayed の目的語が欠けている必要があるが、"
                           "stay は目的語を取らない。",
                    "point": "後ろの文に欠けがなければ where、欠けがあれば which。",
                },
                {
                    "stem": "Everyone {a} that Mt. Fuji is higher than {b} in Japan, "
                            "but few people know that its summit {c} covered with "
                            "snow {d}.",
                    "parts": ["knows", "any other mountains", "is often",
                              "even in early summer"],
                    "ans": 1, "fix": "any other mountains → any other mountain"
                           "（any of the other mountains / all the other mountains も可）",
                    "exp": "〈比較の形＋than any other＋単数名詞〉「他のどの〜よりも…」。"
                           "any other の後ろは単数形 mountain にする。"
                           "「他のどの山より高い」＝1つずつ比べるイメージなので単数。"
                           "everyone は単数扱いなので knows は正しい。",
                    "point": "than any other＋単数名詞「他のどの〜よりも」。",
                },
                {
                    "stem": "In terms of design, this model {a} to be superior {b} "
                            "its rivals, {c} it is {d} than they are.",
                    "parts": ["seems", "than", "although", "far more expensive"],
                    "ans": 1, "fix": "than → to",
                    "exp": "superior「〜より優れている」は -er の形を使わずに比較の意味を持つ"
                           "語で、相手は than ではなく to で示す。"
                           "同じ仲間に inferior to／senior to／junior to／prefer A to B がある。"
                           "seems to be（〜のように見える）・far more expensive than they are は正しい。",
                    "point": "superior／inferior など -or 型の比較は相手を to で示す。",
                },
                {
                    "stem": "He promised {a} me with the presentation, but he {b} "
                            "the office before he finished {c} the slides, {d} me "
                            "to do everything alone.",
                    "parts": ["to help", "left", "to prepare", "leaving"],
                    "ans": 2, "fix": "to prepare → preparing",
                    "exp": "finish は目的語に -ing 形を取る動詞で、to＋原形は続かない。"
                           "finished preparing が正しい。同じ仲間に enjoy／mind／give up／"
                           "avoid／practice がある。promise は逆に to＋原形を取る動詞なので"
                           "promised to help は正しい形。",
                    "point": "finish・enjoy・mind などの目的語は -ing 形（to 原形は不可）。",
                },
                {
                    "stem": "My sister {a} a doctor {b} she met in college, and they "
                            "{c} in a small town {d} the past five years.",
                    "parts": ["married", "whom", "have lived", "since"],
                    "ans": 3, "fix": "since → for（over / during も可）",
                    "exp": "the past five years（この5年間）は期間の長さなので for と組む。"
                           "since は「〜以来」と起点（過去の一点）を示す語で、"
                           "期間の長さとは組めない。marry は前置詞なしで"
                           "目的語を取るので married a doctor は正しい。",
                    "point": "for＋期間の長さ／since＋起点。the past ～ years は for。",
                },
            ],
        },
    ],
}
