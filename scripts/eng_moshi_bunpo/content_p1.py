# -*- coding: utf-8 -*-
"""第1回 標準レベル（日東駒専・地方国公立の文法問題と同程度の難度）20問／100点

★姉妹編（eng_kokkoritsu_nankan / eng_chuken_kokkoritsu）との違い
- 記述模試で実際に使われる三つの形式だけを集める: 四択10＋語句整序5＋誤り指摘5。
  （模試1回分の再現ではない。整序は模試では英作文の大問に入る形式）
- 制限時間25分。模試と同じく、速く正確に型を当てはめる練習。
- 誤答の選択肢は文法的に破綻させる（意味の好みで割れる選択肢を置かない）。
"""

PART = {
    "no": 1,
    "level": "標準レベル",
    "univ": "日東駒専・地方国公立の文法問題と同程度の難度",
    "aim": "夏までに固めた型を、模試の出題形式そのままで素早く正確に使えるかを確認する回。"
           "1問あたり1分強で判断する。ここで落とした項目が、秋以降の失点源になる。",
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
                    "stem": "By the time you (        ) back, I will have finished packing.",
                    "choices": ["come", "will come", "came", "had come"],
                    "ans": 0,
                    "exp": "by the time は「〜するまでには」と時のまとまりを作る接続詞で、"
                           "その節の中では未来のことも現在形で表す。したがって come が正しい。"
                           "will come はこの節の中では使えない。came・had come は過去の形で、"
                           "主節の will have finished（未来の完了）とかみ合わない。",
                    "point": "by the time など時のまとまりを作る節の中では、未来も現在形。",
                },
                {
                    "stem": "The coach had each player (        ) their own name "
                            "on the sheet before leaving the gym.",
                    "choices": ["write", "to write", "written", "wrote"],
                    "ans": 0,
                    "exp": "have は使役動詞で〈have＋O＋動詞の原形〉の形を取る。to は付けない。"
                           "make / let も同じ並びになる。"
                           "この位置の語が説明するのは目的語の each player なので、"
                           "written では「選手が書かれる」、wrote では動詞が二つ並ぶ形になる。"
                           "to write は不定詞なので、原形しか取らない使役の have には続かない"
                           "（ask / tell 型の〈V＋O＋to do〉と混同しやすい）。",
                    "point": "使役動詞 have［make / let］＋O＋動詞の原形。",
                },
                {
                    "stem": "I can't find my umbrella anywhere. "
                            "I (        ) it on the train this morning.",
                    "choices": ["must have left", "must leave",
                                "ought to leave", "may be leaving"],
                    "ans": 0,
                    "exp": "「今朝、電車に置き忘れたに違いない」と過去の出来事を推量する場面。"
                           "must have left（〜したに違いない）が正しい。"
                           "must leave / ought to leave / may be leaving はどれも"
                           "これから先の話をする形で、this morning（今朝）と両立しない。",
                    "point": "must have＋過去分詞＝「〜したに違いない」（過去の推量）。",
                },
                {
                    "stem": "A new bridge (        ) across the river, "
                            "and it will be completed next spring.",
                    "choices": ["is being built", "is building", "has built", "builds"],
                    "ans": 0,
                    "exp": "橋は「建てられる」側で、来春完成予定＝今まさに工事が進んでいる。"
                           "「〜されているところだ」は is being built で表す。"
                           "has built / builds は橋が自分で何かを建てる形になり、目的語も無い。"
                           "is building は古い英語では「建設中だ」の意味で使われたが、"
                           "現代の標準的な英語では受動の形（being＋過去分詞）にする。",
                    "point": "「〜されている最中だ」は be動詞＋being＋過去分詞。",
                },
                {
                    "stem": "I was not used to (        ) in front of a large audience, "
                            "so my voice was shaking.",
                    "choices": ["speaking", "speak", "be spoken", "have spoken"],
                    "ans": 0,
                    "exp": "be used to A「Aに慣れている」の to は前置詞なので、"
                           "後ろには名詞か -ing 形が来る。speaking が正しい。"
                           "speak・have spoken は動詞の形のままでは前置詞の後ろに置けない。"
                           "be spoken は「話される」で、自分が話す場面に合わない。"
                           "used to＋動詞の原形（昔は〜したものだ）と混同しないこと。",
                    "point": "be used to＋名詞・-ing「〜に慣れている」。この to は前置詞。",
                },
                {
                    "stem": "The results of the experiment were (        ), "
                            "so the team checked them three times.",
                    "choices": ["surprising", "surprised", "surprise", "surprisingly"],
                    "ans": 0,
                    "exp": "実験結果は人を「驚かせる」側なので surprising。"
                           "surprised は「驚かされた」で人の側に使う。"
                           "surprise は名詞・動詞の形のままでは were の補語にならず、"
                           "surprisingly は副詞なので be動詞の補語になれない。",
                    "point": "感情を「与える」側は -ing 形、「受け取る」人の側は -ed 形。",
                },
                {
                    "stem": "The lecture was difficult, but (        ) impressed me most "
                            "was the speaker's passion.",
                    "choices": ["what", "that", "which", "who"],
                    "ans": 0,
                    "exp": "「私を最も感心させたもの」という名詞のかたまりを、"
                           "先行詞なしで作れるのは what（＝the thing which）。"
                           "that や which を使うなら直前に先行詞となる名詞が必要だが、ここには無い。"
                           "who も同様で、さらに人を指す点が合わない。",
                    "point": "what＝「〜すること・もの」。先行詞を自分の中に含む。",
                },
                {
                    "stem": "This new smartphone costs twice (        ) the previous model.",
                    "choices": ["as much as", "as many as", "much as", "so much as"],
                    "ans": 0,
                    "exp": "「〜の2倍…」は〈倍数＋as … as〜〉の型で、"
                           "金額は量なので twice as much as が正しい。"
                           "as many as は数えられる名詞用。much as は前の as が抜けており"
                           "倍数の型として成立しない。so much as は否定文などで使う別の表現で、"
                           "倍数とは組めない。",
                    "point": "倍数の言い方は〈X times as ＋ much／many ＋ as〜〉。",
                },
                {
                    "stem": "The committee will (        ) the problem "
                            "at next week's meeting.",
                    "choices": ["discuss", "discuss about", "talk", "mention about"],
                    "ans": 0,
                    "exp": "discuss は前置詞なしで直接目的語を取る他動詞。discuss about は誤り。"
                           "mention も同じく前置詞を付けずに目的語を取るので mention about は誤り。"
                           "talk は自動詞で目的語を直接取れないため talk the problem とは言えない"
                           "（talk about the problem なら正しいが、about が無い形は不可）。",
                    "point": "discuss・mention は前置詞を付けずに目的語を取る。",
                },
                {
                    "stem": "My computer is too old to use, so I'm thinking of "
                            "buying a new (        ).",
                    "choices": ["one", "it", "that", "another"],
                    "ans": 0,
                    "exp": "前に出た数えられる名詞（computer）の代わりで、"
                           "a new のように形容詞を付けて言い直せるのは one。"
                           "it は「その物そのもの」を指し、a new it とは言えない。"
                           "that・another も a new の後ろには置けない"
                           "（another は an＋other で、冠詞を二重に持てない）。",
                    "point": "〈a＋形容詞＋one〉＝前に出た名詞の言い換え。it との違いに注意。",
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
                    "ja": "駅まで歩いて15分かかります。",
                    "frame": "It [            ] to the station.",
                    "tokens": ["fifteen", "minutes", "takes", "to", "walk"],
                    "ans": "takes fifteen minutes to walk",
                    "exp": "〈It takes＋時間＋to do〉「…するのに（時間）がかかる」の型。"
                           "It は形式的な主語で、実際の内容は to walk 以下が表す。"
                           "It takes A B（Aに時間Bがかかる）と人を入れる形も併せて覚える。",
                    "point": "It takes（＋人）＋時間＋to do「…するのに〜かかる」。",
                },
                {
                    "ja": "その映画はとても感動的だったので、私は二度見た。",
                    "frame": "The movie [            ] twice.",
                    "tokens": ["I", "it", "moving", "so", "that", "was", "watched"],
                    "ans": "was so moving that I watched it",
                    "exp": "〈so＋形容詞＋that …〉「とても〜なので…」の型。"
                           "so と that は離れていても一組で働くので、"
                           "so は形容詞 moving の直前に置く（was moving so that … と並べると"
                           "so that が「その結果〜」を導く別の型に読まれ、"
                           "「とても〜なので」という程度の強調が消える）。"
                           "moving は「人を感動させる」側なので -ing 形になっている点も確認。",
                    "point": "so ＋ 形容詞・副詞 ＋ that …「とても〜なので…」。",
                },
                {
                    "ja": "私は彼に手伝ってくれるように頼みました。",
                    "frame": "I [            ] with my homework.",
                    "tokens": ["asked", "help", "him", "me", "to"],
                    "ans": "asked him to help me",
                    "exp": "〈ask＋人＋to do〉「人に〜するよう頼む」の型。"
                           "tell / want / advise も同じ並びを取る。"
                           "help A with B で「BのことでAを手伝う」。"
                           "ask that … の形にすると意味が硬くなるので、この型で覚える。",
                    "point": "ask［tell / want］＋人＋to do「人に〜するよう頼む」。",
                },
                {
                    "ja": "彼は、自分が間違っているということを認めるのを拒んだ。",
                    "frame": "He [            ] wrong.",
                    "tokens": ["admit", "he", "refused", "that", "to", "was"],
                    "ans": "refused to admit that he was",
                    "exp": "refuse は目的語に to＋動詞の原形を取る（-ing 形は取らない）。"
                           "refuse to admit「認めることを拒む」を作り、"
                           "認める内容を that he was wrong の節で続ける。",
                    "point": "refuse to do「〜するのを拒む」。-ing 形は続かない。",
                },
                {
                    "ja": "次に何をすべきか教えてください。",
                    "frame": "Please [            ] next.",
                    "tokens": ["do", "me", "tell", "to", "what"],
                    "ans": "tell me what to do",
                    "exp": "〈疑問詞＋to do〉で「何を〜すべきか」という名詞のかたまりを作る。"
                           "tell は〈tell＋人＋物〉の並びを取るので、"
                           "me の後ろに what to do を置く。",
                    "point": "疑問詞＋to do＝「何を（いつ・どう）〜すべきか」。",
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
                    "stem": "{a} of the reasons {b} the project failed {c} that "
                            "the team {d} enough time to test the system.",
                    "parts": ["One", "why", "were", "did not have"],
                    "ans": 2, "fix": "were → was",
                    "exp": "主語は One of the reasons（理由のうちの一つ）で、中心は One。"
                           "単数なので was が正しい。直前の複数形 reasons につられないこと。"
                           "why the project failed は the reasons を後ろから説明する部分で、"
                           "主語の数には関係しない。",
                    "point": "one of＋複数名詞が主語のとき、動詞は one に合わせて単数。",
                },
                {
                    "stem": "Mr. Tanaka {a} to Osaka three years ago, and {b} he lives "
                            "in a small apartment near his office, he {c} the city very much "
                            "and {d} to move away.",
                    "parts": ["has moved", "although", "likes", "does not want"],
                    "ans": 0, "fix": "has moved → moved",
                    "exp": "three years ago（3年前に）は過去の一点を明示する語句なので、"
                           "動詞は過去形 moved にする。has moved の形は ago と共に使えない。"
                           "現在完了は「いつ起きたか」を言わない形なので、"
                           "過去の一点を示す語句とは同居できないと覚える。",
                    "point": "〜ago など過去の一点を示す語句には過去形。",
                },
                {
                    "stem": "The typhoon {a} the island directly, and {b} near the coast "
                            "{c} damaged, so {d} had to move to shelters.",
                    "parts": ["hit", "almost houses", "were badly", "many residents"],
                    "ans": 1, "fix": "almost houses → almost all the houses"
                           "（almost all houses / most of the houses / most houses も可）",
                    "exp": "almost は副詞なので、名詞 houses を直接修飾できない。"
                           "almost all the houses（ほとんどすべての家）のように、"
                           "all などの語を almost が修飾する形にする。"
                           "most of the houses と言い換えることもできる。"
                           "every は単数名詞を取るので、複数扱いの were とは組めない。",
                    "point": "almost は副詞。名詞を数えるなら almost all（の形）か most。",
                },
                {
                    "stem": "Experts {a} that the price of gasoline, which {b} stable "
                            "for months, will {c} sharply {d} the new tax.",
                    "parts": ["predict", "has remained", "raise", "because of"],
                    "ans": 2, "fix": "raise → rise",
                    "exp": "「価格が上がる」は自動詞 rise（rise-rose-risen）。"
                           "raise は「〜を上げる」という意味で目的語が必要な動詞なので、"
                           "will raise sharply と目的語なしでは使えない。"
                           "has remained stable（ずっと安定している）・because of＋名詞は正しい。",
                    "point": "rise＝自動詞「上がる」／raise＝他動詞「〜を上げる」。",
                },
                {
                    "stem": "The library {a} last spring {b} a wide range of "
                            "digital materials, {c} many students {d} them "
                            "from home at any time.",
                    "parts": ["renovating", "offers", "and", "can access"],
                    "ans": 0, "fix": "renovating → renovated（which was renovated も可）",
                    "exp": "図書館は「改装される」側なので、後ろから説明する分詞は過去分詞。"
                           "renovated last spring で「昨春に改装された（図書館）」となり、"
                           "文の動詞は offers が担う。"
                           "renovating では図書館が何かを改装していることになり、"
                           "目的語も無いので成立しない。"
                           "offers・and・can access はいずれも正しい形。",
                    "point": "名詞を後ろから説明する分詞は、「される」側なら過去分詞。",
                }
            ],
        },
    ],
}
