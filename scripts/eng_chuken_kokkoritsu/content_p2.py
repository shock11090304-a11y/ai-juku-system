# -*- coding: utf-8 -*-
"""第2部 中堅国公立レベル（信州・新潟・静岡・岡山・熊本・鹿児島 レベル）37問／100点

第1部との違いは「一文に判断ポイントが二つ入る」こと。
語彙もセンター〜共通テストの上限あたりまで上げる。
"""

PART = {
    "no": 2,
    "level": "中堅国公立レベル",
    "univ": "信州大・新潟大・静岡大・岡山大・熊本大・鹿児島大 レベル",
    "aim": "標準。一文の中で判断すべきことが二つになる。"
           "選択肢も紛らわしくなり、記述の分量が増える。ここが本命帯の生徒の主戦場。",
    "time": 60,
    "total": 100,
    "sections": [
        # ============================================================ 大問1
        {
            "no": 1, "kind": "mc", "pt": 2,
            "title": "空所補充（四択）",
            "inst": "次の各文の空所に入る最も適切なものを、①〜④から一つ選べ。",
            "items": [
                {
                    "stem": "It was not until he lost his job (        ) he realized how much "
                            "he had relied on it.",
                    "choices": ["when", "that", "which", "then"],
                    "ans": 1,
                    "exp": "It is [was] not until A that B「Aして初めてBする」。"
                           "強調構文の枠に not until 節を入れた形なので、"
                           "空所には that が入る。",
                    "point": "It was not until A that B＝Aして初めてBした。",
                },
                {
                    "stem": "(        ) from the top of the tower, the city looks like a maze.",
                    "choices": ["Seeing", "To see", "Seen", "Having seen"],
                    "ans": 2,
                    "exp": "主節の主語は the city で「見られる」側なので過去分詞。"
                           "Seeing にすると街が見る側になる。"
                           "分詞構文は主節の主語との関係で -ing か過去分詞かを決める。",
                    "point": "分詞構文は主節の主語との能動・受動で形が決まる。",
                },
                {
                    "stem": "The committee demanded that the report (        ) submitted by Friday.",
                    "choices": ["is", "was", "be", "will be"],
                    "ans": 2,
                    "exp": "demand / require / insist / suggest / propose などの後の that 節では"
                           "動詞を原形にする（仮定法現在）。"
                           "主語が単数でも -s は付けず、should be としてもよい。",
                    "point": "要求・提案の動詞＋that S＋原形。",
                },
                {
                    "stem": "The number of students taking this course (        ) increased "
                            "sharply this year.",
                    "choices": ["have", "has", "are", "were"],
                    "ans": 1,
                    "exp": "主語の中心は the number で単数。"
                           "taking this course は students を修飾する現在分詞句。"
                           "a number of A（多数のA）なら複数扱いになる点と対で覚える。",
                    "point": "the number of A＝単数／a number of A＝複数。",
                },
                {
                    "stem": "I would rather stay home tonight (        ) go out in this rain.",
                    "choices": ["than", "then", "rather", "to"],
                    "ans": 0,
                    "exp": "would rather A than B「BするよりむしろAしたい」。"
                           "than の後ろも原形でそろえる（to go out としない）。",
                    "point": "would rather 原形 than 原形。",
                },
                {
                    "stem": "Hardly (        ) the room when the telephone started ringing.",
                    "choices": ["he had entered", "had he entered", "he entered",
                                "did he enter"],
                    "ans": 1,
                    "exp": "否定・準否定の副詞が文頭に出ると〈助動詞＋S＋V〉の倒置が起こる。"
                           "hardly ... when ... は「〜するやいなや」で、"
                           "前半は過去完了、後半は過去形にする。",
                    "point": "文頭の Hardly [Scarcely / Never]→倒置。",
                },
                {
                    "stem": "This is the reason (        ) she decided to change her career.",
                    "choices": ["which", "why", "what", "how"],
                    "ans": 1,
                    "exp": "先行詞が the reason で、後ろの節に欠けがないので関係副詞 why。"
                           "for which と書き換えられる。"
                           "which だけにすると節の中に前置詞が必要になる。",
                    "point": "先行詞が reason＋完全な文→why（＝for which）。",
                },
                {
                    "stem": "He was seen (        ) the building just before the fire broke out.",
                    "choices": ["leave", "to leave", "leaving to", "left"],
                    "ans": 1,
                    "exp": "知覚動詞は能動なら〈see＋O＋原形〉だが、"
                           "受動態にすると to 不定詞が復活して be seen to do になる。"
                           "使役の make も同じ（be made to do）。",
                    "point": "知覚・使役動詞の受動態では to が戻る。",
                },
                {
                    "stem": "Some people prefer working alone, while (        ) enjoy working "
                            "in a team.",
                    "choices": ["another", "other", "others", "the others"],
                    "ans": 2,
                    "exp": "some ... others ...「〜する人もいれば…する人もいる」。"
                           "残り全部を指すわけではないので the は付けない。"
                           "others は代名詞なので other だけでは主語になれない。",
                    "point": "some ... others ...（不特定の他の人々）。",
                },
                {
                    "stem": "Little (        ) that his simple idea would change the whole "
                            "industry.",
                    "choices": ["he knew", "he did know", "did he know", "knew he"],
                    "ans": 2,
                    "exp": "否定の副詞 little が文頭に出たので〈助動詞＋S＋V〉に倒置する。"
                           "この little は「ほとんど〜ない」の意味。",
                    "point": "Little did S know that ...＝〜とは思いもしなかった。",
                },
                {
                    "stem": "The town is not (        ) it used to be when I was a child.",
                    "choices": ["that", "which", "what", "how"],
                    "ans": 2,
                    "exp": "what S used to be「かつてのS」。"
                           "what は先行詞を含む関係代名詞で、be 動詞の補語が欠けている。"
                           "what S is（今のS）と対で覚える。",
                    "point": "what S is [was / used to be]＝今の[昔の]S。",
                },
                {
                    "stem": "(        ) the heavy traffic, we managed to arrive on time.",
                    "choices": ["Although", "Despite", "Because", "However"],
                    "ans": 1,
                    "exp": "後ろが名詞句 the heavy traffic なので前置詞 despite。"
                           "although は接続詞で節を導く。"
                           "however は副詞で、コンマではさんで使う。",
                    "point": "despite [in spite of]＋名詞／although＋SV。",
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
                    "ja": "彼が何を言おうとしているのか、私にはさっぱり分からなかった。",
                    "frame": "I [            ] to say.",
                    "tokens": ["had", "he", "idea", "no", "trying", "was", "what"],
                    "ans": "had no idea what he was trying",
                    "exp": "have no idea＋間接疑問で「まったく分からない」。"
                           "間接疑問は〈疑問詞＋S＋V〉の語順で、"
                           "what he was trying to say の what は say の目的語にあたる。",
                    "point": "have no idea＋疑問詞＋S＋V。",
                },
                {
                    "ja": "その計画は費用がかかりすぎるという理由で却下された。",
                    "frame": "The plan was rejected [            ] too expensive.",
                    "tokens": ["grounds", "it", "on", "the", "that", "was"],
                    "ans": "on the grounds that it was",
                    "exp": "on the grounds that ...「〜という理由で」。"
                           "the grounds の内容を that 節が説明する同格の that。"
                           "関係代名詞と違い、後ろの節に欠けがない。",
                    "point": "on the grounds that SV＝〜という理由で。",
                },
                {
                    "ja": "私は彼に何度も注意したが、彼は聞こうとしなかった。",
                    "frame": "I warned him again and again, [            ] listen.",
                    "tokens": ["but", "he", "not", "would"],
                    "ans": "but he would not",
                    "exp": "would not do は過去の強い拒絶「どうしても〜しようとしなかった」。"
                           "単なる過去の否定 did not listen より意志の強さが出る。"
                           "肯定の will は「〜する習性がある」。",
                    "point": "would not do＝どうしても〜しようとしなかった。",
                },
                {
                    "ja": "この機械の使い方を教えていただけませんか。",
                    "frame": "Could you [            ] this machine?",
                    "tokens": ["how", "me", "show", "to", "use"],
                    "ans": "show me how to use",
                    "exp": "show A B（AにBを見せる・教える）の B が"
                           "〈疑問詞＋to do〉の名詞のかたまりになった形。"
                           "how to use A で「Aの使い方」。",
                    "point": "show [tell] A＋疑問詞＋to do。",
                },
                {
                    "ja": "彼女は私の3倍の数の本を持っている。",
                    "frame": "She has [            ] I do.",
                    "tokens": ["as", "as", "books", "many", "three", "times"],
                    "ans": "three times as many books as",
                    "exp": "倍数は〈倍数＋as＋原級＋as〉。"
                           "数を比べるので many を使い、as many books as の形で"
                           "名詞を as ... as の中に入れる。",
                    "point": "N times as many [much]＋名詞＋as。",
                },
                {
                    "ja": "彼は約束を守らなかったことで、みんなの信頼を失った。",
                    "frame": "He lost the trust of everyone [            ] his promise.",
                    "tokens": ["by", "failing", "keep", "to"],
                    "ans": "by failing to keep",
                    "exp": "by doing「〜することによって」。by は前置詞なので動名詞が続く。"
                           "fail to do は「〜しそこなう・〜しない」で、"
                           "その動名詞形が failing to do。"
                           "keep a promise で「約束を守る」。",
                    "point": "by doing＝〜することで／fail to do＝〜しない。",
                },
                {
                    "ja": "彼女は私に、その計画については何も知らないと言った。",
                    "frame": "She told me [            ] the plan.",
                    "tokens": ["about", "knew", "nothing", "she", "that"],
                    "ans": "that she knew nothing about",
                    "exp": "tell A that ... の that 節。"
                           "主節が過去（told）なので従属節も過去にそろえる（時制の一致）。"
                           "know nothing about A で「Aについて何も知らない」。",
                    "point": "主節が過去なら従属節も過去へ（時制の一致）。",
                },
                {
                    "ja": "その事故のせいで、彼は三週間入院することになった。",
                    "frame": "The accident [            ] for three weeks.",
                    "tokens": ["him", "hospital", "in", "put", "the"],
                    "ans": "put him in the hospital",
                    "exp": "put A in the hospital「Aを入院させる」。"
                           "無生物主語なので「その事故のせいで彼は入院することになった」"
                           "と訳し上げる。"
                           "英語は原因を主語に立てることを好む。",
                    "point": "無生物主語＝Sのせいで／Sのおかげで、と訳し上げる。",
                },
                {
                    "ja": "彼が正直だということは、誰の目にも明らかだった。",
                    "frame": "[            ] was obvious to everyone.",
                    "tokens": ["he", "honest", "that", "was"],
                    "ans": "That he was honest",
                    "exp": "that 節が文の主語になった形。"
                           "It was obvious to everyone that he was honest. と"
                           "形式主語で書くほうが普通だが、that 節を主語に置くこともできる。",
                    "point": "that 節は主語にもなれる（形式主語 It で受けるのが普通）。",
                },
                {
                    "ja": "この問題を解決する方法を、私たちは見つけなければならない。",
                    "frame": "We must [            ] this problem.",
                    "tokens": ["a", "find", "solve", "to", "way"],
                    "ans": "find a way to solve",
                    "exp": "a way to do「〜する方法」。"
                           "to solve は way を後ろから修飾する形容詞的用法の不定詞。"
                           "a way of solving とも書ける。",
                    "point": "a way to do＝a way of doing＝〜する方法。",
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
                    "stem": "I regret (        ) harder when I was a student.",
                    "given": "not, study",
                    "ans": "not studying", "accept": ["not having studied"],
                    "exp": "regret doing は「〜したことを後悔する」で、すでにした事柄を指す。"
                           "動名詞の否定は not を直前に置く。"
                           "regret to do は「残念ながら〜する」でこれから言う内容を指す。",
                    "point": "regret doing（後悔）／regret to do（残念ながら〜する）。",
                },
                {
                    "stem": "She was (   a    ) of the fact that her decision would affect many "
                            "people.",
                    "hint": "a",
                    "ans": "aware", "accept": [],
                    "exp": "be aware of A「Aに気づいている・自覚している」。"
                           "of の後ろが the fact that ... という中立的な内容なので、"
                           "「恐れる」の be afraid of は入らない。"
                           "be aware that ... と that 節を直接置くこともできる。",
                    "point": "be aware of A＝Aを分かっている。",
                },
                {
                    "stem": "I could not help (        ) when I saw his serious face.",
                    "given": "laugh",
                    "ans": "laughing", "accept": [],
                    "exp": "cannot help doing「〜せずにはいられない」。"
                           "この help は「避ける」の意味で、後ろは動名詞。"
                           "cannot but do（原形）とも書ける。",
                    "point": "cannot help doing＝つい〜してしまう。",
                },
                {
                    "stem": "It is no (        ) arguing with him; he never changes his mind.",
                    "ans": "use", "accept": ["good"],
                    "exp": "It is no use doing「〜しても無駄だ」。"
                           "It is no good doing も同義で使える。"
                           "There is no point in doing / There is no use in doing も同義。"
                           "use は名詞で「役に立つこと」。",
                    "point": "It is no use doing＝〜しても無駄だ。",
                },
                {
                    "stem": "He talks (        ) he knew everything about the matter.",
                    "given": "as, if",
                    "ans": "as if", "accept": ["as though"],
                    "exp": "as if＋仮定法。主節（talks）と同時の、事実に反する仮定なので"
                           "後ろは仮定法過去 knew。"
                           "実際には全部は知らない、という含みが出る。",
                    "point": "as if＋仮定法＝まるで〜であるかのように。",
                },
                {
                    "stem": "(        ) up early, you will not miss the first train.",
                    "given": "get",
                    "ans": "Getting", "accept": ["If you get"],
                    "exp": "条件を表す分詞構文。"
                           "主節の主語 you が「起きる」側なので現在分詞 Getting。"
                           "If you get up early, ... と書き換えられる。",
                    "point": "分詞構文は時・理由・条件などを文脈で決める。",
                },
                {
                    "stem": "I have lived here for ten years, (        ) I still do not know "
                            "my neighbors well.",
                    "ans": "but", "accept": ["yet"],
                    "exp": "前半（10年住んでいる）と後半（隣人をよく知らない）は"
                           "対立する内容なので逆接の but。"
                           "yet も逆接の等位接続詞として使える。",
                    "point": "対立する2文をつなぐのは but / yet。",
                },
                {
                    "stem": "The problem is far more complex than it (        ) at first sight.",
                    "given": "appear",
                    "ans": "appears", "accept": ["appeared"],
                    "exp": "than の後ろは節で、ここでは it appears (to be) complex の"
                           "共通部分が省略されている。"
                           "主語 it は三人称単数、時制は現在（is に合わせる）なので appears。"
                           "at first sight は「一見したところでは」。",
                    "point": "than は接続詞。後ろには節が来る。",
                },
                {
                    "stem": "She spent the whole afternoon (        ) for her lost key.",
                    "given": "look",
                    "ans": "looking", "accept": [],
                    "exp": "spend＋時間＋doing「〜して時間を過ごす」。"
                           "to look とはしない。"
                           "It takes＋人＋時間＋to do との形の違いに注意。",
                    "point": "spend 時間 doing／It takes 人 時間 to do。",
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
                    "context": "Volunteer work has become popular among university students.",
                    "src": "One reason why so many young people take part in such activities is "
                           "that they want to feel useful to someone outside their own circle "
                           "of friends.",
                    "model": "これほど多くの若者がそうした活動に参加する理由の一つは、"
                             "自分の友人という枠の外にいる誰かの役に立っていると"
                             "感じたいからである。",
                    "alts": ["多くの若者がこの種の活動に加わる理由の一つは、"
                             "身近な友人以外の誰かにとって自分が役立っていると"
                             "実感したいということだ。"],
                    "elements": [["One reason why ... is that ... の骨格（〜する理由の一つは"
                                  "…ということだ）を訳出できている", 2],
                                 ["take part in を「参加する」と訳せている", 2],
                                 ["useful to someone outside ... の修飾関係を"
                                  "訳に反映できている", 2]],
                    "exp": "主語は One reason why ... activities までで、述語は is。"
                           "why 以下が reason を修飾する関係副詞節なので、"
                           "主語がどこまでかを先に見切る。",
                    "point": "長い主語は、まず述語動詞（is）を探して切れ目を決める。",
                },
                {
                    "context": "Cities around the world are getting hotter every summer.",
                    "src": "Planting more trees along streets is one of the simplest ways to "
                           "lower the temperature of a city, though it takes many years before "
                           "the effect can be felt.",
                    "model": "通りに沿ってもっと木を植えることは、都市の気温を下げる最も簡単な"
                             "方法の一つだが、その効果が感じられるようになるまでには"
                             "長い年月がかかる。",
                    "alts": ["街路により多くの木を植えるのは、都市の気温を下げるいちばん手軽な"
                             "やり方の一つである。もっとも、効果が実感できるまでには"
                             "何年もかかるのだが。"],
                    "elements": [["動名詞 Planting ... が主語であることを訳出できている", 2],
                                 ["one of the simplest ways to do を「最も簡単な方法の一つ」と"
                                  "訳せている", 2],
                                 ["though 以下の譲歩と it takes ... before ... を"
                                  "訳せている", 2]],
                    "exp": "文頭の Planting は動名詞で、streets までが主語。"
                           "it takes 時間 before ... は「…するまでに時間がかかる」。"
                           "before 節は「〜する前に」ではなく「〜するまでに」と訳す。",
                    "point": "It takes 時間 before SV＝〜するまでに時間がかかる。",
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
                    "ja": "その本を読み終えるのに、私は一週間かかった。",
                    "model": "It took me a week to finish reading the book.",
                    "alts": ["I spent a week finishing the book."],
                    "elements": [["It takes 人 時間 to do または spend 時間 doing の型で"
                                  "表せている", 1],
                                 ["「一週間」を a week で表せている", 1],
                                 ["「読み終える」を finish reading / finish the book などで表せている", 1],
                                 ["過去形で表せている", 1]],
                    "exp": "finish は動名詞をとるので finish reading。"
                           "It takes と spend では後ろの形が違うので、"
                           "どちらの型を選んだかで最後まで揃える。",
                },
                {
                    "ja": "彼女は私に、二度と遅刻しないようにと言った。",
                    "model": "She told me not to be late again.",
                    "alts": ["She warned me never to be late again."],
                    "elements": [["tell [warn] A to do の型で表せている", 1],
                                 ["不定詞の否定を not [never] to do の語順で表せている", 1],
                                 ["「遅刻する」を be late で表せている", 1],
                                 ["「二度と〜ない」を again / never で表せている", 1]],
                    "exp": "不定詞の否定は not を to の直前に置く（to not be は避ける）。"
                           "「遅刻する」は be late で、come late とも言えるが"
                           "be late が最も自然。",
                },
                {
                    "ja": "もっと早く出発していれば、私たちは終電に間に合っただろう。",
                    "model": "If we had left earlier, we could have caught the last train.",
                    "alts": ["Had we started earlier, we would have been in time for the last "
                             "train."],
                    "elements": [["仮定法過去完了〈If S had 過去分詞, S would [could] have "
                                  "過去分詞〉で表せている", 1],
                                 ["if 節に would を入れていない", 1],
                                 ["「終電」を the last train で表せている", 1],
                                 ["「間に合う」を catch / be in time for で表せている", 1]],
                    "exp": "過去の事実に反する仮定なので仮定法過去完了。"
                           "if 節は had＋過去分詞、主節は would [could] have＋過去分詞。"
                           "if 節に would を入れる誤りが最も多い。",
                },
                {
                    "ja": "彼は日本で最も有名な作家の一人だと言われている。",
                    "model": "He is said to be one of the most famous writers in Japan.",
                    "alts": ["It is said that he is one of the best-known writers in Japan."],
                    "elements": [["「〜と言われている」を be said to do / It is said that ... で"
                                  "表せている", 1],
                                 ["one of the＋最上級＋複数名詞 の形になっている", 1],
                                 ["最上級の範囲を in Japan で表せている", 1],
                                 ["「作家」を writer / author で表せている", 1]],
                    "exp": "one of the の後ろは必ず複数名詞。"
                           "最上級の範囲は、場所や集団を表す単数名詞の前なら in。"
                           "「〜と言われている」は主語を He にして be said to do が簡潔。",
                },
            ],
        },
    ],
}
