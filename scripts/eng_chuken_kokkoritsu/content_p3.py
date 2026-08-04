# -*- coding: utf-8 -*-
"""第3部 上位への橋渡し（金沢・広島・岡山の難しめ／成蹊・成城・明治学院・南山 レベル）37問／100点

この部を8割取れたら、姉妹編『難関国公立大 英文法 実戦問題集』の第1部に進める。
そのため出題形式もそちらに寄せ、四択を減らして記述の比重を上げてある。
"""

PART = {
    "no": 3,
    "level": "上位への橋渡し",
    "univ": "金沢大・広島大・岡山大の難しめ／成蹊大・成城大・明治学院大・南山大 レベル",
    "aim": "やや難。一文が長くなり、修飾のかたまりが二つ入る。"
           "四択は減り、自分で書く量が増える。ここを8割取れたら難関編へ進む。",
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
                    "stem": "The professor spoke slowly, (        ) made it easier for us to "
                            "take notes.",
                    "choices": ["what", "which", "that", "and which"],
                    "ans": 1,
                    "exp": "コンマの後ろで前の節全体を受ける非制限用法の関係代名詞は which。"
                           "what は先行詞をとれず、that は非制限用法に使えない。"
                           "and which は、前に別の関係詞節がないかぎり使えない。",
                    "point": "前文全体を受ける「,which」。that は非制限用法に使えない。",
                },
                {
                    "stem": "(        ) for your advice, I would have made a serious mistake.",
                    "choices": ["Except", "But", "Without being", "Apart"],
                    "ans": 1,
                    "exp": "But for A「Aがなかったら」＝Without A。"
                           "主節が would have made（仮定法過去完了）なので過去の反実仮想。"
                           "Without your advice と書き換えられる。",
                    "point": "But for A＝Without A＝Aがなかったら。",
                },
                {
                    "stem": "He is the only member of the team (        ) opinion I really "
                            "respect.",
                    "choices": ["which", "who", "whom", "whose"],
                    "ans": 3,
                    "exp": "後ろに名詞 opinion が続き、「その人の意見」という所有の関係なので"
                            "whose。"
                           "whom なら respect の目的語になるが、ここは opinion が目的語。",
                    "point": "関係詞の直後に無冠詞の名詞が続いたら whose。",
                },
                {
                    "stem": "So (        ) was her explanation that no one asked any further "
                            "questions.",
                    "choices": ["clear", "clearly", "the clear", "clearer"],
                    "ans": 0,
                    "exp": "So＋補語が文頭に出た倒置〈So C＋be動詞＋S＋that ...〉。"
                           "was の補語なので形容詞 clear。"
                           "副詞 clearly にすると補語にならない。",
                    "point": "So C＋V＋S＋that ...（補語の前置による倒置）。",
                },
                {
                    "stem": "I could not make myself (        ) in the noisy restaurant.",
                    "choices": ["hear", "hearing", "heard", "to hear"],
                    "ans": 2,
                    "exp": "make oneself heard「自分の声を相手に届かせる」。"
                           "oneself は「聞かれる」側なので過去分詞。"
                           "make oneself understood（話を分かってもらう）も同型。",
                    "point": "make [have]＋O＋過去分詞＝Oが〜される。",
                },
                {
                    "stem": "(        ) he says, I am not going to change my mind.",
                    "choices": ["However", "Whatever", "Whenever", "Whoever"],
                    "ans": 1,
                    "exp": "複合関係代名詞 whatever は no matter what と同義で、"
                           "後ろの節には says の目的語が欠けている（不完全な文）。"
                           "however は後ろに形容詞・副詞が来て、節自体は完全な文になる。",
                    "point": "whatever＋不完全な文／however＋形容詞・副詞＋完全な文。",
                },
                {
                    "stem": "There is little, (        ) any, hope of finding survivors now.",
                    "choices": ["or", "if", "and", "but"],
                    "ans": 1,
                    "exp": "if any は「もしあるとしても」で、little / few の後ろに挿入して"
                           "「ほとんど、あるとしてもごくわずかしか〜ない」と否定を強める。"
                           "if ever（あるとしてもめったに）は seldom / rarely の後ろに置く。",
                    "point": "little [few], if any＝あるとしてもごくわずか。",
                },
                {
                    "stem": "Not only (        ) the deadline, but he also improved the quality of "
                            "the whole report.",
                    "choices": ["he met", "did he meet", "he did meet", "met he"],
                    "ans": 1,
                    "exp": "Not only が文頭に出ると〈助動詞＋S＋V〉の倒置が起こる。"
                           "後半の but he also ... は倒置しない。",
                    "point": "文頭の Not only→前半だけ倒置。",
                },
                {
                    "stem": "There is no (        ) what the result of the election will be.",
                    "choices": ["tell", "telling", "told", "to tell"],
                    "ans": 1,
                    "exp": "There is no doing「〜することはできない」。"
                           "tell には「見分ける・判断する」の意味がある。"
                           "There is no knowing / accounting for も同型。",
                    "point": "There is no doing＝〜できない。",
                },
                {
                    "stem": "The higher the building is, (        ) it sways in a strong wind.",
                    "choices": ["more", "the more", "much more", "the most"],
                    "ans": 1,
                    "exp": "〈The＋比較級 …, the＋比較級 …〉「〜すればするほど…」。"
                           "後半にも the が必要。この the は「それだけ」を表す副詞。",
                    "point": "後半の the を落とさない。",
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
                    "ja": "彼女は自分の失敗を認めるどころか、他人のせいにした。",
                    "frame": "[            ], she blamed others for it.",
                    "tokens": ["admitting", "far", "from", "her", "mistake"],
                    "ans": "Far from admitting her mistake",
                    "exp": "far from doing「〜するどころか」。"
                           "from は前置詞なので動名詞が続く。"
                           "blame A for B（BのことでAを責める）と対で押さえる。",
                    "point": "far from doing＝〜するどころか。",
                },
                {
                    "ja": "その事故のせいで、彼は二度と山に登らなくなった。",
                    "frame": "The accident [            ] mountains again.",
                    "tokens": ["climbing", "from", "him", "kept"],
                    "ans": "kept him from climbing",
                    "exp": "keep A from doing「Aに〜させない」。"
                           "無生物主語なので「その事故のせいで彼は〜しなくなった」と訳し上げる。"
                           "prevent / stop / discourage も同型。",
                    "point": "S keep [prevent] A from doing＝Sのせいで A は〜しない。",
                },
                {
                    "ja": "私が言いたいのは、努力そのものに価値があるということだ。",
                    "frame": "[            ] the effort itself has value.",
                    "tokens": ["is", "say", "that", "to", "want", "what", "I"],
                    "ans": "What I want to say is that",
                    "exp": "〈What S V is that SV〉の型。"
                           "主語が what 節、補語が that 節になる。"
                           "itself は名詞の直後に置いて「〜そのもの」を強調する。",
                    "point": "What S V is that SV.＝SがVするのは…ということだ。",
                },
                {
                    "ja": "彼の助けがなかったら、私はその仕事を終えられなかっただろう。",
                    "frame": "[            ], I could not have finished the work.",
                    "tokens": ["been", "for", "had", "help", "his", "it", "not"],
                    "ans": "Had it not been for his help",
                    "exp": "If it had not been for A の if を省略して倒置した形。"
                           "同義に But for A / Without A がある。"
                           "現在の話なら Were it not for A。",
                    "point": "If の省略＝倒置（Had S 過去分詞／Were S／Should S）。",
                },
                {
                    "ja": "彼女は自分が正しいと確信しているようだった。",
                    "frame": "She [            ] she was right.",
                    "tokens": ["be", "convinced", "seemed", "that", "to"],
                    "ans": "seemed to be convinced that",
                    "exp": "seem to do「〜するようだ」の後ろに be convinced that ...（確信している）"
                           "が続いた形。"
                           "convince は「納得させる」なので、「確信している」は受動態にする。"
                           "It seemed that she was convinced ... とも書ける。",
                    "point": "be convinced that ...＝〜だと確信している（受動態）。",
                },
                {
                    "ja": "私たちは彼が正しかったことを認めざるをえなかった。",
                    "frame": "We [            ] he had been right.",
                    "tokens": ["admit", "but", "choice", "had", "no", "that", "to"],
                    "ans": "had no choice but to admit that",
                    "exp": "have no choice but to do「〜せざるをえない」。"
                           "この but は「〜以外に」の意味の前置詞で、後ろは to 不定詞。"
                           "cannot help doing も同義。",
                    "point": "have no choice but to do＝〜するほかない。",
                },
                {
                    "ja": "彼女は年をとるにつれて、ますます寛容になっていった。",
                    "frame": "[            ], she became more and more tolerant.",
                    "tokens": ["as", "grew", "older", "she"],
                    "ans": "As she grew older",
                    "exp": "as は「〜するにつれて」の比例を表す接続詞。"
                           "more and more＋形容詞で「ますます〜」。"
                           "音節の多い形容詞なので more and more tolerant となる。",
                    "point": "as＝〜するにつれて／more and more＝ますます。",
                },
                {
                    "ja": "その知らせを聞いて驚かない者はいなかった。",
                    "frame": "[            ] at the news.",
                    "tokens": ["no", "not", "one", "surprised", "there", "was", "was", "who"],
                    "ans": "There was no one who was not surprised",
                    "exp": "no one ... not ~ の二重否定で「〜しない者はいない」＝"
                           "「みな〜した」という強い肯定になる。"
                           "who 以下が one を修飾する関係代名詞節で、"
                           "その中にもう一つの否定 not が入る。"
                           "be surprised at A で「Aに驚く」。",
                    "point": "二重否定は強い肯定。no one who is not ~＝誰もが〜だ。",
                },
                {
                    "ja": "彼は、私が正しいと信じていたことが誤りだと教えてくれた。",
                    "frame": "He showed me that [            ] was wrong.",
                    "tokens": ["be", "believed", "had", "I", "right", "to", "what"],
                    "ans": "what I had believed to be right",
                    "exp": "believe A to be B「AをBだと信じる」の A が関係代名詞 what に"
                           "なって前に出た形。to be right だけが後ろに残る。"
                           "その what 節全体が that 節の主語になっている。"
                           "「教えてくれた」より前のことなので過去完了 had believed。",
                    "point": "believe [think] A to be B。A が関係詞になると to be B が残る。",
                },
                {
                    "ja": "彼は一言も言わずに部屋を出て行った。",
                    "frame": "He left the room [            ] a word.",
                    "tokens": ["as", "much", "saying", "so", "without"],
                    "ans": "without so much as saying",
                    "exp": "without so much as doing「〜さえせずに」。"
                           "without doing（〜せずに）に so much as を挟んで強調した形。"
                           "not so much as do（〜さえしない）と同じ仕組み。",
                    "point": "without so much as doing＝〜すらせずに。",
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
                    "stem": "The bridge is believed (        ) more than a hundred years ago.",
                    "given": "to, have, be, build",
                    "ans": "to have been built", "accept": [],
                    "exp": "橋は「架けられる」側なので受動、しかも主節（is believed）より"
                           "前のことなので完了形にして to have been built。"
                           "It is believed that the bridge was built ... と書き換えられる。",
                    "point": "完了不定詞の受動＝to have been＋過去分詞。",
                },
                {
                    "stem": "(   O    ) seeing the letter, she burst into tears.",
                    "hint": "O",
                    "ans": "On", "accept": ["Upon"],
                    "exp": "on doing「〜するとすぐに」。"
                           "前置詞なので動名詞が続く。"
                           "as soon as she saw the letter と書き換えられる。",
                    "point": "on [upon] doing＝as soon as SV。",
                },
                {
                    "stem": "It is high time we (        ) about our future more seriously.",
                    "given": "think",
                    "ans": "thought", "accept": [],
                    "exp": "It is (high) time＋S＋過去形「もう〜してもよいころだ」。"
                           "実際にはまだしていないので仮定法過去を使う。"
                           "It is time to do（不定詞）にすると主語を示せない。",
                    "point": "It is high time＋S＋過去形（仮定法）。",
                },
                {
                    "stem": "(   A    ) is often the case with children, he soon forgot his anger.",
                    "hint": "A",
                    "ans": "As", "accept": [],
                    "exp": "As is often the case with A「Aにはよくあることだが」。"
                           "この as は主節全体を先行詞とする擬似関係代名詞で、"
                           "後ろの節は主語が欠けた不完全文になる。",
                    "point": "as は節全体を受ける関係代名詞になれる。",
                },
                {
                    "stem": "She was so absorbed in her book that she did not (        ) me "
                            "come in.",
                    "given": "notice",
                    "ans": "notice", "accept": [],
                    "exp": "notice は知覚動詞で〈notice＋O＋原形〉。"
                           "did not の後ろなので原形のまま。"
                           "be absorbed in A（Aに夢中である）も定型。",
                    "point": "知覚動詞＋O＋原形（see / hear / notice / feel）。",
                },
                {
                    "stem": "Much (        ) my surprise, he refused the offer without any "
                            "hesitation.",
                    "ans": "to", "accept": [],
                    "exp": "much to one's surprise「大いに驚いたことに」。"
                           "to one's＋感情名詞（joy / disappointment / relief）で"
                           "「〜したことに」を表し、much を付けて強める。"
                           "文頭に置いて、後ろの内容に対する話し手の反応を先に示す。",
                    "point": "to one's surprise＝驚いたことに。much で強調。",
                },
                {
                    "stem": "She is, (        ) it were, a walking dictionary of local history.",
                    "ans": "as", "accept": [],
                    "exp": "as it were「いわば」。仮定法過去 were を含む慣用句で、"
                           "so to speak と同義。挿入句としてコンマではさんで使う。",
                    "point": "as it were＝so to speak＝いわば。",
                },
                {
                    "stem": "I would rather you (        ) this matter to anyone else for now.",
                    "given": "do, not, mention",
                    "ans": "did not mention", "accept": ["didn't mention"],
                    "exp": "would rather＋S＋過去形で「Sに〜してほしくない」という"
                           "現在・未来の願望（仮定法過去）。"
                           "節が続くときは原形ではなく過去形にする。",
                    "point": "would rather＋S＋過去形（仮定法）。",
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
                    "context": "Reading habits have changed a great deal in the past twenty "
                               "years.",
                    "src": "So many people now complain that they have no time for books that "
                           "publishers have begun producing novels short enough to finish on a "
                           "single train ride.",
                    "model": "今では非常に多くの人が本を読む時間がないと訴えるので、出版社は、"
                             "電車に一度乗っている間に読み終えられるほど短い小説を"
                             "作り始めている。",
                    "alts": ["本を読む時間がないと言う人があまりに増えたため、出版社は"
                             "一度の電車移動で読みきれる長さの小説を出すようになってきた。"],
                    "elements": [["So many ... that ~ の因果関係（多さが原因で結果が生じたこと）を"
                                  "訳出できている。語句は問わない", 2],
                                 ["have begun producing の「すでに始まって今も続いている」含みを"
                                  "出せている。語句は問わない", 2],
                                 ["short enough to finish on a single train ride を"
                                  "「一度の乗車で読み終えられるほど短い」と訳せている", 2]],
                    "exp": "that が2回出るが、1つ目は complain の目的語、"
                           "2つ目が So many ... と呼応する結果の that。"
                           "この切れ目を間違えると文全体が読めなくなる。"
                           "形容詞＋enough to do は「〜できるほど…」で、"
                           "short enough to finish が novels を後ろから修飾している。",
                    "point": "so many [much]＋名詞 … that ~＝あまりに多くの…なので〜。"
                },
                {
                    "context": "Smartphones have changed the way we spend our free time.",
                    "src": "It is easy to blame the machines themselves, but the truth is that "
                           "no one forces us to pick them up whenever we have a few minutes to "
                           "spare.",
                    "model": "機械そのものを責めるのは簡単だが、実際のところ、"
                             "少しでも空き時間ができるたびにそれを手に取るよう、"
                             "誰かに強制されているわけではない。",
                    "alts": ["機械のほうが悪いと言うのはたやすいが、本当のところは、"
                             "わずかでも時間が空くたびにそれを手に取れと、"
                             "誰に強いられているわけでもない。"],
                    "elements": [["It is easy to do, but the truth is that ... の対比を"
                                  "訳出できている", 2],
                                 ["no one forces us to do を「誰にも強制されていない」と"
                                  "訳せている", 2],
                                 ["whenever ... to spare を「〜するたびに」「空いている」と"
                                  "訳せている", 2]],
                    "exp": "the truth is that ... は「実のところ〜だ」。"
                           "no one が主語なので「誰も〜しない」＝全体を否定して訳す。"
                           "whenever は「〜するときはいつでも」。"
                           "a few minutes to spare の to spare は minutes を修飾する不定詞で"
                           "「割ける時間」の意味。",
                    "point": "no one が主語のときは、日本語では述語を否定して訳す。",
                },
                {
                    "context": "Many people say that machines will take over most human jobs.",
                    "src": "It is not the machines themselves that we should be afraid of, but "
                           "the way we may come to depend on them without noticing it.",
                    "model": "私たちが恐れるべきなのは機械そのものではなく、"
                             "気づかないうちに機械に頼るようになっていく、そのあり方である。",
                    "alts": ["恐れるべきは機械それ自体ではなく、"
                             "知らないうちに機械に依存するようになってしまう、"
                             "そのなり方のほうだ。"],
                    "elements": [["It is not A that ~ , but B の形の強調構文を訳出できている"
                                  "（It を「それは」と訳していない）", 2],
                                 ["themselves を「そのもの・それ自体」と訳せている", 2],
                                 ["the way we may come to depend on them を"
                                  "「〜するようになるあり方」と訳せている", 2]],
                    "exp": "It is ... that ~ の強調構文で、強調されているのが"
                           "not A but B の形になっている。"
                           "come to do は「〜するようになる」。"
                           "the way SV は「〜するやり方・ありさま」。",
                    "point": "It is＋強調要素＋that ~。It を「それは」と訳さない。",
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
                    "ja": "どんなに忙しくても、彼は必ず両親に電話をかける。",
                    "model": "No matter how busy he is, he never fails to call his parents.",
                    "alts": ["However busy he may be, he always makes a point of calling his "
                             "parents."],
                    "elements": [["「どんなに〜でも」を No matter how ... / However ... で"
                                  "表せている", 1],
                                 ["形容詞 busy を how / however の直後に置けている", 1],
                                 ["「必ず〜する」を never fail to do / always で表せている", 1],
                                 ["「両親に電話する」を call his parents で表せている", 1]],
                    "exp": "however / no matter how の直後には形容詞・副詞が来る"
                           "（However he is busy は誤り）。"
                           "「必ず〜する」は never fail to do が定型。",
                },
                {
                    "ja": "外国語を学ぶことは、自分の言葉を見つめ直すことでもある。",
                    "model": "Learning a foreign language also means looking at your own "
                             "language again.",
                    "alts": ["To study a foreign language is at the same time to take a fresh "
                             "look at your own."],
                    "elements": [["主語を動名詞または不定詞でまとめられている", 1],
                                 ["「〜でもある」を also / at the same time で表せている", 1],
                                 ["対応する二つの部分の形（動名詞どうし／不定詞どうし）を"
                                  "そろえられている", 1],
                                 ["「見つめ直す」を look at ... again / take a fresh look at で"
                                  "表せている", 1]],
                    "exp": "A is B でも A means B でも、対応する A と B の形をそろえる（並列の原則）。"
                           "「見つめ直す」を see again と直訳すると意味がずれる。",
                },
                {
                    "ja": "先生が私に教えてくれたことを、私は今でも覚えている。",
                    "model": "I still remember what my teacher taught me.",
                    "alts": ["To this day I have not forgotten the things my teacher told me."],
                    "elements": [["「〜してくれたこと」を what 節や the thing(s) which [that] などで"
                                  "名詞化できている", 1],
                                 ["「今でも」を still / to this day で表せている", 1],
                                 ["「教えてくれた」を teach A B / tell A B で表せている", 1],
                                 ["「覚えている」は現在、「教わった」は過去と、時制を書き分けられている", 1]],
                    "exp": "「〜こと」は先行詞を含む what で表す。"
                           "the thing which でも書けるが what のほうが簡潔。"
                           "覚えているのは今なので remember は現在形。",
                },
                {
                    "ja": "失敗を避けようとしてばかりいると、新しいことは何も始められない。",
                    "model": "If you always try to avoid failure, you will never start "
                             "anything new.",
                    "alts": ["Someone who is always trying not to fail can never begin "
                             "anything new."],
                    "elements": [["条件を if 節または関係詞つきの主語で表せている", 1],
                                 ["「避けようとしてばかりいる」を always try to avoid / "
                                  "do nothing but ... などで常習性まで表せている", 1],
                                 ["「何も〜ない」を never / not ... anything / nothing で表せている", 1],
                                 ["「新しいこと」を anything new と形容詞後置で表せている", 1]],
                    "exp": "-thing で終わる語を修飾する形容詞は後ろに置く（anything new）。"
                           "「失敗」は failure（不可算）または making mistakes。",
                },
            ],
        },
    ],
}
