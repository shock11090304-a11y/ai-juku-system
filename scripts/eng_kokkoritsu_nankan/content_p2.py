# -*- coding: utf-8 -*-
"""第2部 旧帝大レベル（大阪大・名古屋大・東北大・九州大・北海道大 型）37問／100点

第1部との違いは「一文の長さ」と「構文の入れ子」。単発の知識ではなく、
長い一文の骨格を見抜けるかを問う。和文英訳は日本語が抽象的になる。
"""

PART = {
    "no": 2,
    "level": "旧帝大レベル",
    "univ": "大阪大・名古屋大・東北大・九州大・北海道大 の二次試験レベル",
    "aim": "難。一文が長く、修飾のかたまりが二重三重に入れ子になる。"
           "和文英訳は直訳できない日本語を英語の型に置き換える力が要る。",
    "time": 70,
    "total": 100,
    "sections": [
        # ============================================================ 大問1
        {
            "no": 1, "kind": "error", "pt": 2,
            "title": "文法・語法の誤り指摘",
            "inst": "次の各文の下線部 (a)〜(d) には、文法・語法上の誤りが一箇所ずつある。"
                    "誤りを含む記号を選び、正しい形に直せ。",
            "items": [
                {
                    "stem": "Recent studies {a} that children {b} to a second language before "
                            "the age of six {c} to acquire native-like pronunciation far more "
                            "easily than {d} who start later.",
                    "parts": ["have shown", "exposed", "tends", "those"],
                    "ans": 2, "fix": "tends → tend",
                    "exp": "主語は children で、exposed to a second language before the age of six は"
                           "過去分詞による後置修飾。修飾語をはさんでも動詞は主語 children に一致させる。"
                           "直前の名詞（six）に引きずられないこと。",
                    "point": "後置修飾で主語と動詞が離れたら、主語の核を探して一致を確認する。",
                },
                {
                    "stem": "Neither of the two proposals {a} the conditions the client {b}, "
                            "so the team {c} a third one {d} the end of the week.",
                    "parts": ["seem to satisfy", "laid down last month",
                              "has decided to draft", "well before"],
                    "ans": 0, "fix": "seem to satisfy → seems to satisfy",
                    "exp": "neither / either / each / every one は単数扱い。"
                           "neither of＋複数名詞でも動詞は単数で受ける。"
                           "口語では複数扱いも見られるが、入試では単数が正解。",
                    "point": "neither [either] of A＋単数動詞。",
                },
                {
                    "stem": "The professor insisted that the experiment {a} under strictly "
                            "controlled conditions, but the graduate students, {b} were "
                            "unfamiliar with the equipment, {c} consistent results, {d} the "
                            "whole project.",
                    "parts": ["be repeated", "most of them", "failed to obtain",
                              "seriously delaying"],
                    "ans": 1, "fix": "most of them → most of whom",
                    "exp": "接続詞なしにコンマだけで二つの節をつなぐことはできない。"
                           "先行詞 the graduate students を受ける関係代名詞を用いて "
                           "most of whom were unfamiliar ... とする。"
                           "insist that＋原形（仮定法現在）と、結果を表す分詞構文 delaying は正しい。",
                    "point": "「,＋名詞of them＋V」は不可。of whom / of which にする。",
                },
                {
                    "stem": "{a} in the nineteenth century, the theory {b} accepted until the "
                            "1950s, when a series of experiments {c} evidence that {d} it "
                            "decisively.",
                    "parts": ["First proposed", "remained widely", "produced",
                              "contradicted with"],
                    "ans": 3, "fix": "contradicted with → contradicted",
                    "exp": "contradict は他動詞で前置詞をとらない。"
                           "同じく日本語につられて前置詞を入れがちな他動詞に "
                           "discuss, mention, marry, approach, resemble, enter, reach がある。",
                    "point": "contradict / discuss / mention / resemble は直後に目的語。",
                },
                {
                    "stem": "By the time the research team {a} its final report, the funding "
                            "agency {b} its priorities, and {c} they had discovered {d} "
                            "practical interest.",
                    "parts": ["finally submitted", "has already changed", "much of what",
                              "was of little"],
                    "ans": 1, "fix": "has already changed → had already changed",
                    "exp": "by the time＋過去形 が示す過去の一点より、さらに前に完了していた出来事なので"
                           "過去完了にする。現在完了は過去を表す語句と共起できない。"
                           "much of what ... は単数扱いで was も正しい。",
                    "point": "過去の一点より前＝過去完了。現在完了は過去の時点と併用不可。",
                },
                {
                    "stem": "{a} to believe that the human brain stops developing in early "
                            "adulthood, but recent research suggests that new connections {b} "
                            "throughout life, leading many {c} {d} they had long assumed.",
                    "parts": ["Scientists used", "continue to form", "neuroscientists reconsider",
                              "what"],
                    "ans": 2, "fix": "neuroscientists reconsider → neuroscientists to reconsider",
                    "exp": "lead は〈lead＋O＋to do〉で「Oに〜させる」。"
                           "cause / force / enable / allow も同じく to 不定詞をとる。"
                           "to を落として原形にできるのは、使役動詞 make / let / have と"
                           "知覚動詞 see / hear / watch / feel、および help に限られる。",
                    "point": "原形をとるのは使役動詞・知覚動詞・help。lead / cause / force は to do。",
                },
                {
                    "stem": "{a} the number of applicants was much larger than expected, the "
                            "university had no choice but {b} the entrance examination in two "
                            "separate sessions, {c} caused considerable confusion among {d} "
                            "had already made travel arrangements.",
                    "parts": ["Owing to", "to hold", "which", "those who"],
                    "ans": 0, "fix": "Owing to → Because（Since / As）",
                    "exp": "owing to / due to / because of は前置詞句なので後ろに節（SV）を置けない。"
                           "節を導くには接続詞 because / since / as を使う。"
                           "have no choice but to do（〜せざるをえない）の to 不定詞は正しい。",
                    "point": "because of＋名詞／because＋SV。前置詞句と接続詞を混同しない。",
                },
                {
                    "stem": "{a} how complex the issue is, the author avoids simple conclusions "
                            "and instead {b} readers to weigh the evidence for themselves, a "
                            "strategy {c} the editors believe {d} more responsible than "
                            "offering a single answer.",
                    "parts": ["Aware of", "invites", "that", "being"],
                    "ans": 3, "fix": "being → is",
                    "exp": "a strategy that the editors believe is more responsible ... は"
                           "連鎖関係詞。that は believe の目的語節の主語にあたるので、"
                           "節の述語動詞が必要（is）。being にすると節が成立しない。"
                           "believe を用いるなら that を落として "
                           "a strategy the editors believe to be more responsible とする。",
                    "point": "連鎖関係詞〈名詞＋関係代名詞＋S＋think/believe＋V〉。",
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
                    "ja": "彼の言葉は、私が長い間感じていながら一度も言葉にできなかったことを表していた。",
                    "frame": "His words expressed [            ] never put into words.",
                    "tokens": ["but", "felt", "had", "had", "I", "long", "what"],
                    "ans": "what I had long felt but had",
                    "exp": "関係代名詞 what が導く名詞節が expressed の目的語。"
                           "節の中で had long felt と had never put が but で並列されている。"
                           "並列される二つの動詞の時制を揃えるのが要点。",
                    "point": "what節の中の等位接続。並列要素は形をそろえる。",
                },
                {
                    "ja": "その経験のおかげで私は、以前よりずっと辛抱強くなれた。",
                    "frame": "The experience [            ] than I had been before.",
                    "tokens": ["become", "enabled", "far", "me", "more", "patient", "to"],
                    "ans": "enabled me to become far more patient",
                    "exp": "enable A to do「Aが〜できるようにする」。"
                           "無生物主語なので「その経験のおかげで私は〜できた」と訳し上げる。"
                           "far は比較級 more patient を強める副詞。",
                    "point": "S enable A to do＝Sのおかげで A は〜できる。",
                },
                {
                    "ja": "彼が正直だからといって、有能だということにはならない。",
                    "frame": "[            ] does not necessarily mean that he is competent.",
                    "tokens": ["fact", "he", "honest", "is", "that", "the"],
                    "ans": "The fact that he is honest",
                    "exp": "the fact that SV は同格の that。関係代名詞の that と違い、"
                           "後ろの節に欠けている要素がない点で区別する。"
                           "not necessarily は部分否定で「必ずしも〜ない」。",
                    "point": "同格の that＝後ろが完全な文／関係代名詞の that＝後ろが不完全。",
                },
                {
                    "ja": "その発見の重要性は、いくら強調してもしすぎることはない。",
                    "frame": "We [            ] of that discovery too much.",
                    "tokens": ["cannot", "emphasize", "importance", "the"],
                    "ans": "cannot emphasize the importance",
                    "exp": "cannot ... too ~「いくら〜してもしすぎることはない」。"
                           "否定語と too が組み合わさると強い肯定になる。"
                           "同義に cannot overemphasize / It is impossible to overemphasize がある。",
                    "point": "cannot ... too ~ は否定と too の組み合わせで強い肯定になる。",
                },
                {
                    "ja": "知識は、それをどう使うかを知って初めて本当に価値を持つ。",
                    "frame": "[            ] that knowledge becomes truly valuable.",
                    "tokens": ["how", "is", "it", "it", "know", "only", "to", "use", "when", "you"],
                    "ans": "It is only when you know how to use it",
                    "exp": "It is ... that ~ の強調構文で only when 節を強調した形。"
                           "「〜して初めて…する」の定番表現。"
                           "how to use it は know の目的語となる疑問詞＋不定詞。",
                    "point": "It is only when ... that ~＝〜して初めて…する。",
                },
                {
                    "ja": "この地域の人口密度は、全国平均の三倍以上ある。",
                    "frame": "The population density of this area is [            ] the "
                             "national average.",
                    "tokens": ["as", "as", "high", "more", "than", "three", "times"],
                    "ans": "more than three times as high as",
                    "exp": "倍数は〈倍数＋as＋原級＋as〉で表す。"
                           "half as large as（半分）、twice as long as（2倍）のように、"
                           "倍数を表す語は必ず最初の as の前に置く。"
                           "「〜以上」は more than をさらにその前に付ける。",
                    "point": "倍数は〈N times as 原級 as〉。倍数語は前の as の前。",
                },
                {
                    "ja": "彼女は、自分の研究が社会にどれほど大きな影響を与えうるかを理解していなかった。",
                    "frame": "She did not realize [            ] on society.",
                    "tokens": ["an", "could", "effect", "enormous", "have", "her", "how",
                               "research"],
                    "ans": "how enormous an effect her research could have",
                    "exp": "〈how＋形容詞＋a(n)＋名詞〉の語順。how の直後に形容詞が来て、"
                           "冠詞はその後ろに回る（so / as / too も同じ語順をとる）。"
                           "have an effect on A が下敷き。",
                    "point": "how [so / as / too]＋形容詞＋a(n)＋名詞 の語順。",
                },
                {
                    "ja": "丘の上には、町全体を見下ろす古い城が立っていた。",
                    "frame": "[            ] an old castle overlooking the whole town.",
                    "tokens": ["at", "hill", "of", "stood", "the", "the", "top"],
                    "ans": "At the top of the hill stood",
                    "exp": "場所を表す副詞句が文頭に出ると〈副詞句＋V＋S〉の倒置が起こる。"
                           "主語が長いときに使われる文体的倒置で、疑問文の語順（助動詞＋S）とは別物。"
                           "overlooking 以下は castle を修飾する現在分詞。",
                    "point": "場所の副詞句＋動詞＋主語（文体的倒置）。",
                },
                {
                    "ja": "人間と動物の違いは、程度の差であって種類の差ではない。",
                    "frame": "The difference between humans and animals is [            ].",
                    "tokens": ["degree", "kind", "not", "of", "of", "one"],
                    "ans": "one of degree, not of kind",
                    "exp": "この one は前出の名詞 difference を受ける代名詞。"
                           "a difference of degree（程度の差）と a difference of kind（種類の差）を"
                           "not で対比している。",
                    "point": "反復を避ける代名詞 one（＝a＋既出の名詞）。",
                },
                {
                    "ja": "彼は若いが、その分野では誰よりも経験を積んでいる。",
                    "frame": "[            ], he has more experience in the field than anyone else.",
                    "tokens": ["as", "be", "he", "may", "young"],
                    "ans": "Young as he may be",
                    "exp": "〈形容詞＋as＋S＋V〉で「〜ではあるが」の譲歩。"
                           "文頭の補語が前に出るため冠詞は落ちる（Child as he was）。"
                           "though を使って Young though he may be とも書ける。",
                    "point": "形容詞＋as＋SV＝譲歩（〜だけれども）。",
                },
            ],
        },
        # ============================================================ 大問3
        {
            "no": 3, "kind": "fill", "pt": 2,
            "title": "空所補充（記述）",
            "inst": "次の各文の空所に入る最も適切な語を書け。( ) 内に語が示されている場合は、"
                    "示された語をすべて使い、適切な形に変えて書け（形を変える必要が"
                    "なければそのまま書く）。頭文字が示されている場合はその文字で始まる語を書け。",
            "items": [
                {
                    "stem": "Little (        ) that his decision would change the course of "
                            "the company.",
                    "given": "do, he, know",
                    "ans": "did he know", "accept": [],
                    "exp": "否定・準否定の副詞（little, never, seldom, rarely, hardly）が文頭に出ると"
                           "〈助動詞＋S＋V〉の倒置が起こる。ここでの little は「ほとんど〜ない」。",
                    "point": "否定の副詞が文頭→疑問文と同じ語順に倒置。",
                },
                {
                    "stem": "(   B    ) for the invention of the printing press, the spread of "
                            "knowledge would have been far slower.",
                    "hint": "B",
                    "ans": "But", "accept": [],
                    "exp": "But for A「Aがなかったら」。Without A と同義で、"
                           "仮定法過去にも仮定法過去完了にも使える。"
                           "ここは帰結節が would have been なので過去の反実仮想。",
                    "point": "But for A＝Without A＝If it were [had] not been for A。",
                },
                {
                    "stem": "So (        ) was the evidence that no one dared to question the "
                            "conclusion.",
                    "given": "convince",
                    "ans": "convincing", "accept": [],
                    "exp": "so ... that ~ の so＋補語が文頭に出た倒置文（So C＋V＋S＋that ...）。"
                           "evidence は「納得させる」側なので現在分詞由来の convincing。"
                           "convinced だと「納得した」で、人が主語のときに使う。",
                    "point": "-ing＝〜させる／-ed＝〜させられた。物が主語なら -ing。",
                },
                {
                    "stem": "The report is well worth (        ) carefully before the meeting.",
                    "given": "read",
                    "ans": "reading", "accept": [],
                    "exp": "be worth doing「〜する価値がある」。"
                           "doing は能動の形のまま受動の意味（読まれる価値がある）を表すので、"
                           "being read とはしない。"
                           "need doing / want doing（〜される必要がある）も同じ仕組み。",
                    "point": "be worth [need / want]＋doing は能動の形で受動の意味。",
                },
                {
                    "stem": "(   F    ) all his efforts, the negotiations broke down in the end.",
                    "hint": "F",
                    "ans": "For", "accept": [],
                    "exp": "for all A「Aにもかかわらず」＝ in spite of A / despite A / with all A。"
                           "for の「〜の割には」の用法から派生した譲歩表現。",
                    "point": "for all A＝with all A＝〜にもかかわらず。",
                },
                {
                    "stem": "These three theories, (        ) of which has ever been proved, "
                            "are still widely taught in schools.",
                    "ans": "none", "accept": [],
                    "exp": "〈数量詞＋of which〉で先行詞を受ける非制限用法。"
                           "none of＋複数名詞は単数でも複数でも受けられるが、ここは has に合わせて none。"
                           "none of them とすると接続詞がなくなり文が成立しない。"
                           "先行詞が3つなので neither（2つのうちどちらも〜ない）は使えない。"
                           "先行詞が単数なら none 自体が使えない（none は複数・不可算を受ける）。",
                    "point": "none [some / most / many]＋of which [whom] で節をつなぐ。",
                },
                {
                    "stem": "I am strongly opposed to (        ) like a child in front of "
                            "my colleagues.",
                    "given": "be, treat",
                    "ans": "being treated", "accept": [],
                    "exp": "be opposed to の to は前置詞なので動名詞が続く。"
                           "さらに「私が扱われる」という受動関係なので being treated。"
                           "look forward to doing, object to doing, get used to doing も同型。",
                    "point": "to＋動名詞をとる表現群。受動なら being＋過去分詞。",
                },
                {
                    "stem": "(        ) is often the case with him, he arrived half an hour "
                            "late for the meeting.",
                    "ans": "As", "accept": [],
                    "exp": "As is often the case with A「Aにはよくあることだが」。"
                           "この as は主節全体を先行詞とする擬似関係代名詞で、"
                           "後ろの節は主語が欠けた不完全文になる。",
                    "point": "as は節全体を受ける関係代名詞になれる（which は文末に限る）。",
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
                    "context": "Debates about artificial intelligence often circle back to a "
                               "single question.",
                    "src": "The belief that machines will eventually think as we do rests on an "
                           "assumption which, though rarely stated, shapes almost every argument "
                           "on the subject: that thinking is something that can be separated "
                           "from having a body.",
                    "model": "機械がいずれ我々と同じように考えるようになるという信念は、"
                             "めったに明言されないもののこの主題に関するほとんどすべての議論を"
                             "形づくっている一つの前提、すなわち、思考とは身体を持つことから"
                             "切り離せるものだ、という前提に基づいている。",
                    "alts": ["機械もやがて人間と同じように思考するという考えは、ある前提の上に"
                             "成り立っている。それは、口にされることはまれだがこの問題に関する"
                             "議論のほぼすべてを規定している前提、つまり、思考とは身体を持つことと"
                             "切り離しうるものだ、という前提である。"],
                    "elements": [["The belief that ... の that が同格（〜という信念）であることを"
                                  "訳出できている", 2],
                                 ["which, though rarely stated, shapes ... の挿入を処理して"
                                  "関係詞節を訳せている", 2],
                                 ["コロン以下の that 節が an assumption の内容（同格）であることを"
                                  "訳に反映できている", 2]],
                    "exp": "主語は The belief that ... do までで、that は同格。"
                           "述語は rests on。an assumption を受ける関係詞 which の直後に"
                           "though rarely stated（though it is rarely stated の省略）が挿入されている。"
                           "コロンの後ろの that 節は an assumption の内容を言い直したもの。",
                    "point": "コロンは「すなわち」。直前の名詞の中身を言い直す合図。",
                },
                {
                    "context": "Not every scientific advance is welcomed at once.",
                    "src": "Only when a discovery threatens to overturn what a discipline has "
                           "long taken for granted does it meet the kind of resistance that "
                           "later generations find hard to explain.",
                    "model": "ある発見が、その学問分野が長らく当然だと思ってきたことを覆しかねない"
                             "ときに初めて、その発見は、後の世代には説明しがたいと思われる種類の"
                             "抵抗に遭うのである。",
                    "alts": ["発見というものは、ある分野が長年当たり前としてきたことをひっくり返し"
                             "そうになったときにようやく、のちの世代には説明しがたいような抵抗を"
                             "受けることになる。"],
                    "elements": [["Only when ... does it meet の倒置を、only の限定が出る形で"
                                  "訳せている（〜して初めて／〜したときにようやく など）", 2],
                                 ["what a discipline has long taken for granted を「長らく当然だと"
                                  "思ってきたこと」と訳せている", 2],
                                 ["the kind of resistance that later generations find hard to "
                                  "explain の関係詞節を訳せている", 2]],
                    "exp": "Only＋副詞節が文頭に出たので、主節が does it meet と倒置している。"
                           "訳では「〜して初めて…する」とするのが定型。"
                           "take A for granted の A が what 節になって前に出ている。"
                           "find O C（OをCだと思う）の O が関係代名詞 that。",
                    "point": "文頭の Only＋副詞節 → 主節は必ず倒置。",
                },
                {
                    "context": "Translators are often accused of betraying the works they "
                               "translate.",
                    "src": "However faithful a translation may appear, it inevitably reflects "
                           "choices that the original author never had to make, and it is in "
                           "those choices, rather than in any single mistranslation, that the "
                           "translator's presence is most clearly felt.",
                    "model": "翻訳がどれほど忠実に見えようとも、それは原著者が下す必要のなかった"
                             "選択を必ず反映しており、翻訳者の存在が最もはっきり感じられるのは、"
                             "個々の誤訳においてではなく、まさにそうした選択においてなのである。",
                    "alts": ["どんなに忠実に見える翻訳であっても、原著者がする必要のなかった選択が"
                             "必ず入り込んでおり、訳者の存在が最も明瞭に現れるのは、"
                             "一つ一つの誤訳よりも、そうした選択の中においてである。"],
                    "elements": [["However faithful ... may appear の譲歩を「どれほど〜でも」と"
                                  "訳せている", 2],
                                 ["choices that the original author never had to make を"
                                  "「原著者がする必要のなかった選択」と訳せている"
                                  "（「できなかった」は不可）", 2],
                                 ["it is in those choices ... that ... の強調構文を訳出できている", 2]],
                    "exp": "However＋形容詞＋S＋V は譲歩で、形容詞が however の直後に来る。"
                           "後半の it is ... that ... は強調構文で、副詞句 in those choices を"
                           "強調している（it を「それは」と訳さない）。"
                           "rather than in any single mistranslation は挿入。",
                    "point": "it is＋副詞句＋that は強調構文。形式主語構文と取り違えない。",
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
                    "ja": "便利さを追い求めるあまり、私たちは何か大切なものを失ってきたのではないだろうか。",
                    "model": "I sometimes wonder whether we have lost something important in "
                             "our pursuit of convenience.",
                    "alts": ["In our eagerness to make life more convenient, have we not lost "
                             "something precious?"],
                    "elements": [["「〜ではないだろうか」という含みを I wonder whether ... や"
                                  "修辞疑問などで表せている", 1],
                                 ["「便利さを追い求めるあまり」を in our pursuit of convenience / "
                                  "in our eagerness to ... などの句で表せている", 1],
                                 ["「失ってきた」を現在完了 have lost で表せている", 1],
                                 ["「何か大切なもの」を something important と形容詞後置で表せている", 1]],
                    "exp": "「〜ではないだろうか」は疑問文にせず I wonder if [whether] ... と平叙文に"
                           "収めるのが安全。something / anything / nothing を修飾する形容詞は後ろに置く。",
                },
                {
                    "ja": "自分の経験から学ぶ人は多いが、他人の経験から学べる人は少ない。",
                    "model": "Many people learn from their own experience, but few can learn "
                             "from that of others.",
                    "alts": ["A great many people learn from what they themselves have gone "
                             "through, but hardly anyone can learn from other people's "
                             "experience."],
                    "elements": [["「〜する人は多いが…する人は少ない」の対比を表せている", 1],
                                 ["「経験から学ぶ」を learn from experience（無冠詞）で表せている", 1],
                                 ["「他人の経験」を that of others / other people's experience "
                                  "などで表せている", 1],
                                 ["少なさを few / hardly anyone など否定的な語で表せている"
                                  "（a few は不可）", 1]],
                    "exp": "few は「ほとんどいない」で否定、a few は「少しはいる」で肯定。"
                           "ここは対比なので few。"
                           "「経験」の意味の experience は不可算で無冠詞、"
                           "「経験したこと」の意味なら可算（an experience / experiences）。"
                           "反復を避けるには that of others を使う。",
                },
                {
                    "ja": "若いうちに苦労しておけば、その経験は後になって必ず生きてくる。",
                    "model": "If you go through hardships while you are young, the experience "
                             "will surely be of use to you later in life.",
                    "alts": ["Hardships you experience in your youth are sure to pay off later on."],
                    "elements": [["「〜しておけば」の条件関係を if 節、または条件の意味を含んだ"
                                  "主語（Hardships you experience ... など）で表せている", 1],
                                 ["「若いうちに」を while you are young / in your youth で表せている", 1],
                                 ["「必ず〜だろう」を will surely / be sure to で表せている", 1],
                                 ["「生きてくる」を be useful / be of use / pay off などで表せている", 1]],
                    "exp": "時・条件を表す副詞節では未来のことも現在形で表す。"
                           "「苦労する」は go through hardships / have a hard time。"
                           "「生きてくる」を live と直訳しない。",
                },
                {
                    "ja": "他人の意見に耳を傾けることと、それに従うこととは別のことだ。",
                    "model": "Listening to other people's opinions is one thing; following "
                             "them is another.",
                    "alts": ["To listen to what others say is one thing, and to act on it is "
                             "quite another."],
                    "elements": [["A is one thing, B is another の型で「別のことだ」を表せている", 1],
                                 ["主語を動名詞または不定詞でそろえて並列できている", 1],
                                 ["「耳を傾ける」を listen to で表せている", 1],
                                 ["「それに従う」を follow / act on で表せている", 1]],
                    "exp": "A is one thing, B is another「AとBとは別のことだ」。"
                           "並列される二つの主語は動名詞なら動名詞、不定詞なら不定詞でそろえる。",
                },
                {
                    "ja": "教育の目的は、答えを与えることではなく、問いを立てる力を育てることにある。",
                    "model": "The purpose of education lies not in giving answers but in "
                             "developing the ability to ask questions.",
                    "alts": ["The aim of education is not to provide answers but to cultivate "
                             "the ability to raise questions."],
                    "elements": [["「目的は〜にある」を The purpose ... is / lies in で表せている", 1],
                                 ["not A but B の相関表現で対比できている", 1],
                                 ["not と but の後の形（in doing どうし、to do どうし）をそろえられている", 1],
                                 ["「問いを立てる力」を the ability to ask [raise] questions で表せている", 1]],
                    "exp": "not A but B は A と B を必ず同じ品詞・同じ形にそろえる（並列の原則）。"
                           "lies in を使ったら but の後も in、is to do を使ったら but の後も to do。",
                },
            ],
        },
    ],
}
