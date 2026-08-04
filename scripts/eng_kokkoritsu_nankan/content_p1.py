# -*- coding: utf-8 -*-
"""第1部 上位国公立レベル（神戸大・筑波大・千葉大・広島大・横浜国立大 型）38問／100点

出題形式は「文法分野別」ではなく**本番の大問構成**に寄せた実戦ミックス。
- 問題編には解説・ポイント・文法項目名を一切出さない（解答漏洩の防止）。
- 誤り指摘の誤り位置は (a)(b)(c)(d) 均等。
"""

PART = {
    "no": 1,
    "level": "上位国公立レベル",
    "univ": "神戸大・筑波大・千葉大・広島大・横浜国立大 の二次試験レベル",
    "aim": "標準〜やや難。語句整序と空所補充が主戦場で、"
           "「文構造を自分で組み立てられるか」を問う。",
    "time": 60,
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
                    "stem": "{a}, the number of visitors to the exhibition {b} steadily "
                            "since it {c}, and the museum is now considering {d} "
                            "the exhibition period.",
                    "parts": ["Contrary to expectations", "have increased", "opened", "extending"],
                    "ans": 1, "fix": "have increased → has increased",
                    "exp": "the number of A は「Aの数」で主語の中心は number。単数扱いなので has increased。"
                           "a number of A（多数のA）なら複数扱いで have increased となる点と対で覚える。",
                    "point": "the number of A＝単数／a number of A＝複数。",
                },
                {
                    "stem": "{a} in a language that few scholars can now read, the inscription "
                            "{b} for more than a century, and even after it was deciphered "
                            "experts {c} about {d} "
                            "it actually means.",
                    "parts": ["Writing", "remained undeciphered", "disagree", "what"],
                    "ans": 0, "fix": "Writing → Written",
                    "exp": "分詞構文の意味上の主語は主節の主語と同じ。"
                           "主語は the inscription（碑文）で「書かれる」側だから過去分詞 Written にする。"
                           "現在分詞のままだと「碑文が言語で書いていた」という意味になる。",
                    "point": "分詞構文は主節の主語との関係が能動なら -ing、受動なら過去分詞。",
                },
                {
                    "stem": "The committee members {a} to {b} in the discussion, and almost "
                            "half of them {c} the proposal {d} that it was too costly.",
                    "parts": ["were asked", "take part", "objected", "on the grounds"],
                    "ans": 2, "fix": "objected → objected to",
                    "exp": "object は自動詞で、反対の対象は to で受ける（object to A）。"
                           "同型の「日本語につられて他動詞と誤りやすい」語に "
                           "apologize to A for B, complain to A about B, graduate from A がある。",
                    "point": "object to A／oppose A（oppose は他動詞）を区別する。",
                },
                {
                    "stem": "Although the new device is {a} than the old one, its performance "
                            "is {b}, and many engineers {c} {d} any other model on the market.",
                    "parts": ["considerably more expensive", "in some ways superior",
                              "regard it as", "more preferable than"],
                    "ans": 3, "fix": "more preferable than → preferable to",
                    "exp": "preferable は語そのものに比較の意味を含むので more を付けない。"
                           "また比較の相手は than ではなく to で受ける。"
                           "-ior で終わるラテン比較級（superior / inferior / senior / junior）も"
                           "同じく to をとる（preferable は prefer＋-able の派生でラテン比較級ではないが、to をとる点は同じ）。",
                    "point": "superior / inferior / senior / junior / preferable は than でなく to。",
                },
                {
                    "stem": "If I {a} that the lecture had been cancelled, I {b} the early "
                            "train and {c} the morning {d} for the seminar.",
                    "parts": ["would have known", "would not have taken", "would have spent",
                              "preparing"],
                    "ans": 0, "fix": "would have known → had known",
                    "exp": "仮定法過去完了は〈If＋S＋had＋過去分詞, S＋would have＋過去分詞〉。"
                           "would は帰結節にだけ置き、if 節には置かない。"
                           "spend＋時間＋doing（〜して時間を過ごす）も頻出。",
                    "point": "if 節に would を入れない。",
                },
                {
                    "stem": "What impressed me most about her presentation {a} she had "
                            "collected {b} she explained them {c} {d} background.",
                    "parts": ["was not the data", "but the way how", "to an audience",
                              "with no technical"],
                    "ans": 1, "fix": "but the way how → but the way（または but how / but the way in which）",
                    "exp": "「〜する方法」は the way / how / the way in which のいずれかで表し、"
                           "the way how とは重ねられない。not A but B の相関表現の骨格も確認しておく。",
                    "point": "the way how は不可。the way か how のどちらか一方。",
                },
                {
                    "stem": "The researchers {a} {b} suggesting that {c} improves {d} physical "
                            "health but also mental well-being.",
                    "parts": ["have collected", "a great deal of evidence", "a regular exercise",
                              "not only"],
                    "ans": 2, "fix": "a regular exercise → regular exercise",
                    "exp": "「運動」の意味の exercise は不可算名詞なので a を付けられない。"
                           "「練習問題」の意味では可算（an exercise / exercises）になる点に注意。"
                           "evidence, information, advice, equipment も不可算。",
                    "point": "不可算名詞に a／-s は付けない。exercise は意味で可算・不可算が変わる。",
                },
                {
                    "stem": "{a} begun {b} one of the participants raised an objection, {c} "
                            "the chairperson to postpone {d} a final decision until the "
                            "following week.",
                    "parts": ["Hardly had the meeting", "when", "which forced", "to make"],
                    "ans": 3, "fix": "to make → making",
                    "exp": "postpone は動名詞のみを目的語にとる（postpone doing）。"
                           "同型に finish, avoid, mind, give up, put off, consider がある。"
                           "hardly ... when ... の倒置と、前文全体を受ける非制限用法の which は正しい。",
                    "point": "postpone / put off＋doing。to 不定詞は不可。",
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
                    "ja": "その本を読めば読むほど、彼の主張は理解しにくくなった。",
                    "frame": "[            ], the harder it became to understand his argument.",
                    "tokens": ["book", "I", "more", "read", "the", "the"],
                    "ans": "The more I read the book",
                    "exp": "〈The＋比較級＋S＋V, the＋比較級＋S＋V〉「〜すればするほど…」。"
                           "前半の the more は read の目的語ではなく副詞的に働き、"
                           "the book が目的語として残る。",
                    "point": "The 比較級 …, the 比較級 … は前半が従属節・後半が主節。",
                },
                {
                    "ja": "彼の説明は、私たちが予想していたよりはるかに説得力があった。",
                    "frame": "His explanation [            ].",
                    "tokens": ["expected", "far", "had", "more", "persuasive", "than", "was", "we"],
                    "ans": "was far more persuasive than we had expected",
                    "exp": "比較級の強調は far / much / a lot / even（very は不可）。"
                           "than 以下は we had expected (it to be) ... の共通部分が省略された節で、"
                           "than が接続詞として節を導いている。",
                    "point": "比較級を強めるのは far / much / even。very は原級専用。",
                },
                {
                    "ja": "彼は自分の意見を他人に押し付けるような人ではない。",
                    "frame": "He [            ] on others.",
                    "tokens": ["force", "is", "his", "last", "opinions", "person", "the", "to"],
                    "ans": "is the last person to force his opinions",
                    "exp": "the last person to do は「最も〜しそうにない人」。"
                           "last を「最後の」と直訳すると意味を取り違える。"
                           "force A on B で「AをBに押し付ける」。",
                    "point": "the last A to do＝最も〜しそうにないA。",
                },
                {
                    "ja": "一晩中働いたのだから、彼女が疲れているのも当然だ。",
                    "frame": "[            ] tired, since she worked all night.",
                    "tokens": ["is", "is", "it", "natural", "only", "she", "that"],
                    "ans": "It is only natural that she is",
                    "exp": "It is natural that ... の形式主語構文。only は natural を強めて"
                           "「当然だ」の意味を作る。なお natural の that 節では should を用いて"
                           "It is only natural that she should be tired ともできる。",
                    "point": "感情・判断を表す形容詞＋that節は形式主語 It で受ける。",
                },
                {
                    "ja": "その事故のせいで、彼は二度と車を運転しなくなった。",
                    "frame": "The accident [            ] a car again.",
                    "tokens": ["driving", "ever", "from", "him", "kept"],
                    "ans": "kept him from ever driving",
                    "exp": "keep A from doing「Aに〜させない」。無生物主語＋人を目的語にとる型で、"
                           "直訳の「事故が彼を妨げた」を「事故のせいで彼は〜できなかった」と訳し上げる。"
                           "prevent / stop / discourage も同型。",
                    "point": "無生物主語＋keep [prevent] A from doing は「Sのせいで A は〜できない」。",
                },
                {
                    "ja": "私が驚いたのは、彼が一言も文句を言わなかったことだ。",
                    "frame": "[            ] he did not complain at all.",
                    "tokens": ["me", "surprised", "that", "was", "what"],
                    "ans": "What surprised me was that",
                    "exp": "関係代名詞 what が導く名詞節を主語に置き、補語に that 節を置く"
                           "〈What V O is that SV〉の型。話題の焦点を後ろに送る強調の働きを持つ。",
                    "point": "What surprised me was that SV.＝私が驚いたのは…ということだ。",
                },
                {
                    "ja": "その計画については、検討すべき点がまだ多く残っている。",
                    "frame": "There [            ] about the plan.",
                    "tokens": ["be", "considered", "much", "remains", "to"],
                    "ans": "remains much to be considered",
                    "exp": "There 構文は be 動詞以外に remain / exist / seem to be なども使える。"
                           "much は「検討される」側なので、不定詞は受動態 to be considered。"
                           "硬い書き言葉では a lot より much が自然。",
                    "point": "There remains ... ／不定詞の意味上の関係が受動なら to be done。",
                },
                {
                    "ja": "彼の助けがなかったら、私はその試験に合格していなかっただろう。",
                    "frame": "[            ], I would not have passed the exam.",
                    "tokens": ["been", "for", "had", "help", "his", "it", "not"],
                    "ans": "Had it not been for his help",
                    "exp": "If it had not been for A（Aがなかったら）の if を省略して倒置した形。"
                           "同義に But for A / Without A がある。現在の話なら Were it not for A。",
                    "point": "If の省略＝倒置（Had S 過去分詞 / Were S / Should S）。",
                },
                {
                    "ja": "その政策が経済に与える影響は、まだ十分に検証されていない。",
                    "frame": "The effect [            ] has yet to be fully examined.",
                    "tokens": ["economy", "has", "on", "policy", "the", "the"],
                    "ans": "the policy has on the economy",
                    "exp": "The effect [(which) the policy has on the economy] has yet to ... の"
                           "接触節（関係代名詞の省略）。長い主語の直後にもう一つ動詞が来る形は"
                           "難関で頻出。have an effect on A（Aに影響を与える）が下敷き。",
                    "point": "名詞＋SV… と続いたら関係代名詞の省略を疑う。",
                },
                {
                    "ja": "多くの困難があったので、その研究は予定より大幅に遅れた。",
                    "frame": "[            ], the research fell far behind schedule.",
                    "tokens": ["a", "being", "difficulties", "number", "of", "there"],
                    "ans": "There being a number of difficulties",
                    "exp": "分詞構文の意味上の主語が主節と異なるときは、その主語を分詞の前に置く"
                           "（独立分詞構文）。There is 構文の分詞構文は、主語の位置に立つ there をそのまま残して"
                           "There being ... とする。分詞構文は既定で理由・付帯状況に読まれるので、"
                           "「〜にもかかわらず」の譲歩を表したいときは分詞構文ではなく "
                           "Despite / Although を使う。",
                    "point": "独立分詞構文。There is → There being。",
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
                    "stem": "It is essential that every applicant (        ) the required "
                            "documents by Friday.",
                    "given": "submit",
                    "ans": "submit", "accept": [],
                    "exp": "essential / necessary / important / desirable などの後の that 節は"
                           "動詞を原形にする（仮定法現在。主に米用法）。"
                           "should＋原形とすることもできる（主に英用法）。"
                           "主語が三人称単数でも submits にしない。",
                    "point": "要求・提案・必要を表す形容詞＋that節→動詞は原形。",
                },
                {
                    "stem": "He is used to (        ) in public, so he was not nervous at all.",
                    "given": "speak",
                    "ans": "speaking", "accept": [],
                    "exp": "be used to doing「〜することに慣れている」。to は前置詞なので動名詞が続く。"
                           "used to do「かつて〜した」との区別が問われる定番。",
                    "point": "be used to doing／used to do を混同しない。",
                },
                {
                    "stem": "You (        ) me you were coming; I would have prepared something.",
                    "given": "should, have, tell",
                    "ans": "should have told", "accept": [],
                    "exp": "should have＋過去分詞は「〜すればよかったのに」で、"
                           "実際にはしなかったことへの後悔・非難を表す。"
                           "must have done（〜したにちがいない）、cannot have done（〜したはずがない）、"
                           "need not have done（〜する必要はなかったのに）と対で覚える。",
                    "point": "助動詞＋have＋過去分詞は過去への推量・後悔。",
                },
                {
                    "stem": "If only I (        ) his advice when I had the chance.",
                    "given": "have, take",
                    "ans": "had taken", "accept": [],
                    "exp": "If only ...「〜でさえあればなあ」は仮定法で受ける。"
                           "when I had the chance が過去の一点を示しているので、"
                           "それに反する後悔は仮定法過去完了 had＋過去分詞。"
                           "現在の願望なら If only I knew ... のように過去形になる。",
                    "point": "If only＋仮定法。過去への後悔は had＋過去分詞。",
                },
                {
                    "stem": "She was so absorbed (   i    ) her work that she did not notice "
                            "me come in.",
                    "hint": "i",
                    "ans": "in", "accept": [],
                    "exp": "be absorbed in A「Aに夢中である」。"
                           "同型の受動態イディオムに be engaged in, be involved in, "
                           "be interested in がある。",
                    "point": "be absorbed in A。",
                },
                {
                    "stem": "No (   s    ) had he sat down than the telephone rang.",
                    "hint": "s",
                    "ans": "sooner", "accept": [],
                    "exp": "No sooner had S 過去分詞 than S 過去形「〜するやいなや…」。"
                           "否定の副詞句が文頭に出たので倒置が起きている。"
                           "Hardly [Scarcely] had S 過去分詞 when [before] S 過去形 も同義。",
                    "point": "No sooner ... than ... ／Hardly ... when ...。",
                },
                {
                    "stem": "There is no (   p    ) in arguing with him; he never changes his mind.",
                    "hint": "p",
                    "ans": "point", "accept": [],
                    "exp": "There is no point in doing「〜しても無駄だ」。"
                           "頭文字の指定がなければ There is no use in doing / "
                           "It is no use doing も同義で使える。",
                    "point": "There is no point [use] in doing.",
                },
                {
                    "stem": "I still remember the day (        ) which I first met her.",
                    "ans": "on", "accept": [],
                    "exp": "前置詞は、先行詞を元の文に戻して決める。"
                           "I first met her on that day. の on が関係代名詞の前に出た形で、"
                           "on which は関係副詞 when に置き換えられる。"
                           "先行詞が place なら in which（＝where）、reason なら for which（＝why）。",
                    "point": "前置詞＋関係代名詞は、先行詞を元の文に戻して前置詞を決める。",
                },
                {
                    "stem": "I could not make myself (        ) in the noisy hall.",
                    "given": "hear",
                    "ans": "heard", "accept": [],
                    "exp": "make oneself heard は「自分の声を相手に届かせる」。"
                           "oneself は「聞かれる」側なので過去分詞にする。"
                           "make oneself understood（話を分かってもらう）、"
                           "have one's hair cut（髪を切ってもらう）も同じ〈make [have]＋O＋過去分詞〉。",
                    "point": "make [have]＋O＋過去分詞＝Oが〜される。",
                },
                {
                    "stem": "I have no idea (        ) or not she will accept the offer.",
                    "ans": "whether", "accept": [],
                    "exp": "or not を直後に置けるのは whether だけで、if ... or not は"
                           "or not が文末にあるときしか使えない。"
                           "前置詞の後・主語の位置・to 不定詞の前でも if は使えない。",
                    "point": "whether or not は可。if or not（直後）は不可。",
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
                    "context": "Many people assume that learning a language is mainly a matter "
                               "of memorizing words.",
                    "src": "What actually distinguishes fluent speakers from beginners is not "
                           "the number of words they know, but the speed with which they can "
                           "put those words together.",
                    "model": "流暢な話し手を初心者から実際に区別しているのは、知っている単語の数ではなく、"
                             "それらの単語をどれだけ速くつなぎ合わせられるかである。",
                    "alts": ["流暢に話せる人と初心者とを本当に分けているのは、単語をいくつ知っているか"
                             "ではなく、その単語をどれだけ速くつなぎ合わせられるかである。"],
                    "elements": [["What ... is not A but B（実際に区別するのはAではなくBだ）の"
                                  "骨格を訳出できている", 2],
                                 ["distinguish A from B を「AをBと区別する／AとBを分ける」と"
                                  "訳せている", 2],
                                 ["the speed with which ... を「〜する速さ／どれだけ速く〜できるか」"
                                  "と訳せている", 2]],
                    "exp": "先頭の What は関係代名詞で、What ... beginners までが主語。"
                           "is の後ろが not A but B で並列されている。"
                           "the speed with which S V は〈前置詞＋関係代名詞〉で、"
                           "with the speed（その速さで）が前に出た形。"
                           "the number of words they know の they know は接触節。",
                    "point": "文頭の What節が長いときは、どこまでが主語かを先に見切る。",
                },
                {
                    "context": "The city council has been debating the new library project for "
                               "over a year.",
                    "src": "Faced with a shrinking budget, the council has had to decide which "
                           "of the services now offered to residents can be reduced without "
                           "provoking serious opposition.",
                    "model": "縮小していく予算に直面して、市議会は、住民に現在提供されているサービスの"
                             "うちどれなら深刻な反対を招かずに削減できるかを決めなければならなくなっている。",
                    "alts": ["予算が減っていく中で、市議会は、いま住民に提供されているサービスの"
                             "どれなら大きな反発を呼ばずに減らせるかを、決断せざるをえなくなっている。"],
                    "elements": [["Faced with A を「Aに直面して／Aという状況で」と受動の意味で"
                                  "訳せている", 2],
                                 ["which of the services ... can be reduced が decide の目的語"
                                  "（間接疑問）であることを訳出できている", 2],
                                 ["now offered to residents が the services を修飾していることを"
                                  "訳に反映できている", 2]],
                    "exp": "Faced with A は Being faced with A の Being が省略された受動の分詞構文。"
                           "decide の目的語は which ... opposition までの間接疑問全体。"
                           "now offered to residents は過去分詞句が the services を後ろから修飾している"
                           "（which are now offered の関係代名詞＋be の省略）。",
                    "point": "他動詞の後ろが長いときは、目的語がどこで終わるかを先に確定する。",
                },
                {
                    "context": "Historians often warn against judging the past by the standards "
                               "of the present.",
                    "src": "No period of history is so easily misunderstood as the one "
                           "immediately before our own, precisely because it looks familiar "
                           "enough for us to assume that we already know it.",
                    "model": "自分たちのすぐ前の時代ほど誤解されやすい時代はない。まさにそれが、"
                             "すでに知っていると思い込んでしまうほど見慣れたものに見えるからである。",
                    "alts": ["歴史上、自分たちの直前の時代ほど容易に誤解される時代はない。"
                             "それはまさに、その時代が、もう分かっていると我々が思い込むほどに"
                             "馴染み深く見えるからだ。"],
                    "elements": [["No A is so ... as B（BほどAなものはない）を最上級の意味で"
                                  "訳出できている", 2],
                                 ["the one が period of history を受けていることを訳に"
                                  "反映できている", 2],
                                 ["familiar enough for us to assume ... の〈形容詞＋enough for A "
                                  "to do〉を訳せている", 2]],
                    "exp": "〈No＋名詞＋so 原級 as B〉は「Bほど〜なものはない」で最上級と同義。"
                           "the one は前に出た period of history の反復を避ける代名詞。"
                           "enough は形容詞の後ろに置き、for us が不定詞の意味上の主語。",
                    "point": "否定＋原級／比較級は最上級に読み替えて訳す。",
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
                    "ja": "最近の若者は本を読まなくなったとよく言われるが、私はそうは思わない。",
                    "model": "It is often said that young people today have stopped reading "
                             "books, but I do not think so.",
                    "alts": ["People often say that young people these days no longer read "
                             "books, but I disagree."],
                    "elements": [["「〜とよく言われる」を It is often said that ... または "
                                  "People often say that ... で表せている", 1],
                                 ["「最近の若者」を young people today / these days で表せている", 1],
                                 ["「読まなくなった」を have stopped doing / no longer do など"
                                  "変化を含む形で表せている", 1],
                                 ["「私はそうは思わない」を but＋否定（I do not think so / I disagree）で"
                                  "表せている", 1]],
                    "exp": "「〜と言われる」は It is said that ... が最も安全。"
                           "「読まなくなった」は過去との対比なので現在完了 have stopped reading が自然で、"
                           "単に do not read だと「もともと読まない」に読める。",
                },
                {
                    "ja": "初めて外国に行ったとき、私は自分がいかに何も知らなかったかに気づいた。",
                    "model": "When I went abroad for the first time, I realized how little "
                             "I had known.",
                    "alts": ["It was when I first went abroad that I realized how little "
                             "I knew about the world."],
                    "elements": [["「初めて」を for the first time / first で表せている", 1],
                                 ["「外国に行く」を go abroad（to a foreign country）で表せている", 1],
                                 ["「いかに何も知らなかったか」を how little ... の間接疑問で表せている", 1],
                                 ["「知らなかった」の時制を realize との関係で正しく処理できている"
                                  "（had known / knew）", 1]],
                    "exp": "「いかに何も知らないか」は how little I knew。"
                           "how much I did not know と直訳すると不自然。"
                           "abroad は副詞なので to abroad とはしない。",
                },
                {
                    "ja": "どんなに忙しくても、彼は毎晩必ず子どもに本を読んでやる。",
                    "model": "No matter how busy he is, he never fails to read a book to his "
                             "children every night.",
                    "alts": ["However busy he may be, he always reads his children a book "
                             "before they go to bed."],
                    "elements": [["「どんなに忙しくても」を No matter how busy ... / However busy ... "
                                  "で表せている", 1],
                                 ["形容詞 busy を how / however の直後に置けている", 1],
                                 ["「必ず〜する」を never fail to do / always で表せている", 1],
                                 ["read A to B または read B A の語順が正しい", 1]],
                    "exp": "however / no matter how の直後には形容詞・副詞が来る"
                           "（However he is busy は誤り）。"
                           "「必ず〜する」は never fail to do が定型。",
                },
                {
                    "ja": "その問題を解決するには、私たちが今まで当然だと思ってきたことを見直す必要がある。",
                    "model": "To solve the problem, we need to reconsider what we have taken "
                             "for granted.",
                    "alts": ["In order to solve the problem, it is necessary for us to "
                             "rethink what we have long regarded as a matter of course."],
                    "elements": [["「〜するには」を To do / In order to do で表せている", 1],
                                 ["「見直す必要がある」を need to / it is necessary to で表せている", 1],
                                 ["「〜してきたこと」を関係代名詞 what の節で表せている", 1],
                                 ["「当然だと思ってきた」を現在完了 have taken for granted などで"
                                  "表せている", 1]],
                    "exp": "take A for granted「Aを当然と思う」。目的語が what 節のときは"
                           "take what ... for granted と分断せず take for granted what ... とも書ける。"
                           "「今まで〜してきた」は継続・経験の現在完了。",
                },
            ],
        },
    ],
}
