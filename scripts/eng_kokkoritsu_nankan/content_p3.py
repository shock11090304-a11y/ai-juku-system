# -*- coding: utf-8 -*-
"""第3部 最難関レベル（東京大・京都大・一橋大 型）34問／100点

★形式の対応（一次情報＝大学公式の過去問・出題意図で確認済み。過大に名乗らないこと）
- 誤り指摘: 東大4(A)は**約600語の英文を5段落に割り、各段落の(a)〜(e)から1つを記号で選ぶ**
  形式で、訂正は書かせない。本書の「単文＋4下線部＋訂正を記述」は東大4(A)の再現ではなく、
  東北大の文法正誤（読解大問内の小問）に近い、文法力を単独で鍛えるための形。
- 英文和訳: 東大4(B)・京大Ⅰ/Ⅱ・一橋Ⅰに実在。3大学すべてが出す。
- 和文英訳: 東大2(B)・京大Ⅲに実在。一橋にはない。
- 語句整序: 東大1(B)・一橋Ⅱに実在。ただし本番はいずれも読解大問内の小問。
"""

PART = {
    "no": 3,
    "level": "最難関レベル",
    "univ": "東京大・京都大・一橋大 の二次試験レベル",
    "aim": "最難。誤りは一読では気づかない位置に置かれ、"
           "和文英訳は日本語を一度「言い換えて」から英語にする作業を要求される。",
    "time": 80,
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
                    "stem": "Although the population of this city {a} than {b} of the "
                            "neighboring prefecture, its total economic output is {c}, "
                            "which explains {d} move here every spring.",
                    "parts": ["is considerably smaller", "that", "much more larger",
                              "why so many young people"],
                    "ans": 2, "fix": "much more larger → much larger（far larger）",
                    "exp": "比較級に more を重ねる二重比較は誤り。"
                           "比較級を強めるのは much / far / a lot / even / still。"
                           "比較対象を that of ... で受けている (b) は正しい（population どうしの比較）。",
                    "point": "-er と more は併用しない。強調は much / far / even。",
                },
                {
                    "stem": "Among the causes of the decline that historians have identified, "
                            "one of {a} was the failure of successive governments to invest in "
                            "education, a failure {b} {c} in communities {d}.",
                    "parts": ["the most serious factor", "the consequences of which",
                              "are still being felt", "scattered across the country"],
                    "ans": 0, "fix": "the most serious factor → the most serious factors",
                    "exp": "one of the＋最上級の後ろは必ず複数名詞（「最も〜なものの一つ」なので"
                           "母集団が複数）。the consequences of which（＝whose consequences）の"
                           "非制限用法、communities を修飾する過去分詞 scattered はいずれも正しい。",
                    "point": "one of the＋最上級＋複数名詞。",
                },
                {
                    "stem": "{a} the theory has survived for so long {b} it can accommodate "
                            "almost any observation, {c} it, in the eyes of its critics, less a "
                            "scientific hypothesis {d} an article of faith.",
                    "parts": ["The reason why", "is because", "making", "than"],
                    "ans": 1, "fix": "is because → is that",
                    "exp": "The reason is because ... は理由が二重になる誤り。"
                           "The reason is that ... とするか、"
                           "文全体を This is because ... に組み替える。"
                           "less A than B（AというよりむしろB）の than は正しい。",
                    "point": "The reason ... is that SV.（is because は不可）",
                },
                {
                    "stem": "Historians {a} the revolution was inevitable, but few would deny "
                            "that the speed {b} the old regime collapsed astonished even its "
                            "fiercest opponents, {c} had expected a struggle {d}.",
                    "parts": ["disagree about whether", "with which", "most of whom",
                              "during several years"],
                    "ans": 3, "fix": "during several years → lasting several years（of several years）",
                    "exp": "during は「特定の期間の間に」を表し、数値で示された期間の長さには使えない。"
                           "「何年も続く闘争」なら lasting several years / of several years、"
                           "動詞にかけるなら for several years。",
                    "point": "for＋期間の長さ／during＋特定の期間（the war, the summer）。",
                },
                {
                    "stem": "He {a} that the data {b} before the deadline, but when pressed "
                            "he admitted that he {c} whether the analysis {d} in time.",
                    "parts": ["assured the committee", "would be ready", "has no idea",
                              "could be completed"],
                    "ans": 2, "fix": "has no idea → had no idea",
                    "exp": "主節の動詞が過去（admitted）なので、その目的語となる that 節の中の動詞も"
                           "過去にそろえる（時制の一致）。"
                           "現在も変わらない事実・不変の真理・仮定法は一致させない例外だが、"
                           "「そのとき見当がつかなかった」はその例外に当たらない。"
                           "assure＋人＋that 節、would be ready（過去から見た未来）は正しい。",
                    "point": "主節が過去なら従属節も過去へ（時制の一致）。",
                },
                {
                    "stem": "It {a} nearly a decade since the government {b} to reform the "
                            "pension system, and yet almost nothing {c}, which suggests that "
                            "the obstacles are political {d} technical.",
                    "parts": ["has been", "has promised", "has changed", "rather than"],
                    "ans": 1, "fix": "has promised → promised",
                    "exp": "It is [has been]＋期間＋since S＋過去形。"
                           "since が導く節は「起点となる過去の一点」なので過去形にする。"
                           "現在完了は起点を表せない。",
                    "point": "It has been N years since S＋過去形。",
                },
                {
                    "stem": "The new drug is {a} effective as the old one, and in some respects "
                            "more so, but because it {b} far more expensive, hospitals {c} it "
                            "{d} the price falls.",
                    "parts": ["at least as", "is", "remain reluctant adopting", "until"],
                    "ans": 2, "fix": "remain reluctant adopting → remain reluctant to adopt",
                    "exp": "reluctant は to 不定詞をとる形容詞（be reluctant to do）。"
                           "willing, eager, anxious, ready, likely も同じく to 不定詞。"
                           "at least as ... as は「少なくとも同じくらい」で正しい。",
                    "point": "reluctant [willing / eager / ready] to do。動名詞は不可。",
                },
                {
                    "stem": "{a} accounts for all the observed phenomena, and researchers {b} "
                            "to models that combine elements of several, {c} some critics "
                            "dismiss {d} of the central problem.",
                    "parts": ["No single theory", "have increasingly turned", "what",
                              "as an evasion"],
                    "ans": 2, "fix": "what → which",
                    "exp": "前の節全体を先行詞とする非制限用法の関係代名詞は which。"
                           "what は先行詞を含む関係代名詞なので、先行詞のある節はつくれない。"
                           "dismiss A as B（AをBとして退ける）の as は正しい。",
                    "point": "前文全体を受ける「,which」。what は先行詞をとれない。",
                },
                {
                    "stem": "{a} the difficulty of the task, it is remarkable that the team "
                            "{b} to complete the survey within a year, though several members "
                            "later admitted that they {c} the amount of data they would have "
                            "to process and {d} more time had they known.",
                    "parts": ["Given", "managed", "had underestimated", "would request"],
                    "ans": 3, "fix": "would request → would have requested",
                    "exp": "文末の had they known は If they had known の倒置＝仮定法過去完了。"
                           "したがって帰結にあたる部分も would have＋過去分詞にそろえる。"
                           "Given A（Aを考慮すると）、manage to do は正しい。",
                    "point": "帰結節の形は条件節の時制で決まる。過去の反実仮想＝would have＋過去分詞。",
                },
                {
                    "stem": "Whether artificial intelligence will eventually surpass human "
                            "judgment {a} a question that cannot be settled in advance, but "
                            "{b} is that the systems now in use reflect the assumptions of "
                            "{c} designed them, and those assumptions deserve far more "
                            "scrutiny {d} they currently receive.",
                    "parts": ["is", "that is certain", "those who", "than"],
                    "ans": 1, "fix": "that is certain → what is certain",
                    "exp": "「確かなこと」という名詞のかたまりを作るには、"
                           "先行詞を含む関係代名詞 what が必要（what is certain is that ...）。"
                           "that は先行詞なしでは名詞節の主語になれない。"
                           "文頭の Whether 節が主語なので (a) の is は単数で正しい。",
                    "point": "what＝the thing which。先行詞がないときは that ではなく what。",
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
                    "ja": "彼が言おうとしていたのは、科学とは知識の集積ではなく、問いを立てる技術だ"
                          "ということだった。",
                    "frame": "What he was trying to say was that science is [            ] "
                             "asking questions.",
                    "tokens": ["a", "an", "art", "body", "but", "knowledge", "not", "of", "of"],
                    "ans": "not a body of knowledge but an art of",
                    "exp": "not A but B の A と B を〈冠詞＋名詞＋of〉でそろえる並列。"
                           "a body of knowledge（知識の体系）と an art of doing（〜する技術）は"
                           "どちらも of で後続要素につながる。",
                    "point": "not A but B は A と B の形をそろえる。",
                },
                {
                    "ja": "人は自分に理解できないものを恐れる傾向がある、というのは古くからの真理だ。",
                    "frame": "It is an old truth that [            ] they cannot understand.",
                    "tokens": ["afraid", "be", "of", "people", "tend", "to", "what"],
                    "ans": "people tend to be afraid of what",
                    "exp": "tend to do「〜する傾向がある」。"
                           "be afraid of の of の目的語が関係代名詞 what の節になっている。"
                           "It is ... that ~ は形式主語構文（強調構文ではない）。",
                    "point": "前置詞の目的語になる what 節。",
                },
                {
                    "ja": "その決定がどのような結果をもたらすかは、誰にも予測できなかった。",
                    "frame": "[            ] the decision would lead to.",
                    "tokens": ["consequences", "could", "foresee", "no", "one", "what"],
                    "ans": "No one could foresee what consequences",
                    "exp": "疑問形容詞 what＋名詞（どのような結果）が間接疑問の先頭に出た形。"
                           "文末の to は lead to A の前置詞が残ったもの（前置詞の後の目的語が"
                           "前に出ている）。",
                    "point": "間接疑問は〈疑問詞（＋名詞）＋S＋V〉の語順。",
                },
                {
                    "ja": "私たちが歴史から学ぶのは、人間は歴史から学ばないということだ、と彼は言った。",
                    "frame": "He said that [            ] learn from history.",
                    "tokens": ["do", "from", "history", "is", "learn", "not", "that", "we",
                               "we", "what"],
                    "ans": "what we learn from history is that we do not",
                    "exp": "〈What S V is that SV〉の型。主語が what 節、補語が that 節。"
                           "「学ぶのは」を主語、「〜ということだ」を補語に置く構造を見抜く。",
                    "point": "What S V is that SV.＝SがVするのは…ということだ。",
                },
                {
                    "ja": "その本が出版されてからというもの、彼の名前は誰もが知るところとなった。",
                    "frame": "[            ], his name has been known to everyone.",
                    "tokens": ["book", "ever", "of", "publication", "since", "the", "the"],
                    "ans": "Ever since the publication of the book",
                    "exp": "ever since は since を強めて「〜以来ずっと」。"
                           "後ろに節ではなく名詞句（the publication of the book）を置いた前置詞用法。"
                           "主節が現在完了になるのが対応関係。",
                    "point": "ever since＋名詞句／節。主節は現在完了。",
                },
                {
                    "ja": "彼は自分の失敗を書き留めておいた。二度と同じ過ちを繰り返さないように。",
                    "frame": "He wrote down his mistakes [            ] repeat them.",
                    "tokens": ["he", "might", "never", "so", "that"],
                    "ans": "so that he might never",
                    "exp": "so that S may [might / can / could] do は目的を表す「〜するように」。"
                           "主節が過去形なので助動詞も過去形 might にそろえる。"
                           "コンマを打って so that ... とすると結果「その結果〜」に読めるので、"
                           "目的のときはコンマを入れない。in order that S may do も同義。",
                    "point": "目的の so that S may [can] do。結果の「,so that」と区別する。",
                },
                {
                    "ja": "彼は自分の失敗を認めるどころか、それを他人のせいにした。",
                    "frame": "[            ], he blamed others for it.",
                    "tokens": ["admitting", "far", "from", "his", "mistake"],
                    "ans": "Far from admitting his mistake",
                    "exp": "far from doing「〜するどころか／決して〜でない」。"
                           "from は前置詞なので動名詞が続く。"
                           "blame A for B（BのことでAを責める）と対で押さえる。",
                    "point": "far from doing＝〜するどころか。",
                },
                {
                    "ja": "その理論が正しいかどうかを知る唯一の方法は、実験で確かめることだ。",
                    "frame": "[            ] whether the theory is right is to test it by "
                             "experiment.",
                    "tokens": ["of", "only", "telling", "the", "way"],
                    "ans": "The only way of telling",
                    "exp": "the way of doing / the way to do はどちらも「〜する方法」。"
                           "tell には「見分ける・判断する」の意味があり、"
                           "tell whether ... で「〜かどうかを判断する」。",
                    "point": "tell＝見分ける。There is no telling / the way of telling。",
                },
                {
                    "ja": "一度口にした言葉は、もう取り消すことができない。",
                    "frame": "[            ] cannot be taken back.",
                    "tokens": ["been", "has", "once", "said", "what"],
                    "ans": "What has once been said",
                    "exp": "関係代名詞 what が主語となる名詞節。"
                           "節の中は現在完了の受動態 has been said で、once が完了形の中に割り込む。"
                           "「一度言われてしまったこと」という完了の含みが要点。",
                    "point": "what節＋現在完了受動態。副詞は has と過去分詞の間。",
                },
                {
                    "ja": "彼は自分の考えを、誰にでも分かるように説明する術を心得ていた。",
                    "frame": "He knew how to explain his ideas [            ] anyone could "
                             "understand.",
                    "tokens": ["a", "in", "such", "that", "way"],
                    "ans": "in such a way that",
                    "exp": "in such a way that ... は「…するようなやり方で」で、結果・様態を表す。"
                           "such が way を修飾し、that 節がその内容を説明する。"
                           "so that（目的・結果）との違いは、such a way が具体的な「やり方」を"
                           "指す名詞であること。in a way that ... も同義で使える。",
                    "point": "in such a way that SV＝〜するようなやり方で。",
                },
            ],
        },
        # ============================================================ 大問3
        {
            "no": 3, "kind": "fill", "pt": 2,
            "title": "空所補充（記述）",
            "inst": "次の各文の空所に入る最も適切な語を書け。( ) 内に語が示されている場合は、"
                    "示された語をすべて使い、適切な形に変えて書け（形を変える必要が"
                    "なければそのまま書く）。",
            "items": [
                {
                    "stem": "He spoke about the accident as if he (        ) it with his own eyes.",
                    "given": "have, see",
                    "ans": "had seen", "accept": [],
                    "exp": "as if＋仮定法。主節（spoke）と同時の事実に反する仮定なら仮定法過去、"
                           "主節より前のことなら仮定法過去完了にする。"
                           "ここは「話している時点より前に見た」という設定なので had seen。"
                           "as though も同じように使える。",
                    "point": "as if＋仮定法過去完了＝主節より前の、事実に反する仮定。",
                },
                {
                    "stem": "The problem is far more serious than (        ) at first sight.",
                    "given": "it, appear",
                    "ans": "it appears", "accept": ["it appeared"],
                    "exp": "than の後ろは節で、ここでは it appears (to be) serious の"
                           "共通部分が省略されている。"
                           "at first sight は「一見したところでは」。"
                           "than の後ろを than to appear のように不定詞にはできない。"
                           "at first sight を「初めて見たとき」と過去の一点に取れば "
                           "it appeared も可。",
                    "point": "than は接続詞。後ろには節が来る。",
                },
                {
                    "stem": "A whale is no (        ) a fish than a horse is.",
                    "ans": "more", "accept": [],
                    "exp": "no more A than B は「BがAでないのと同様にAでない」で、"
                           "AもBもともに否定する（いわゆるクジラの構文）。"
                           "no less A than B は逆に「Bと同様にAである」で両方を肯定する。"
                           "not more A than B（BほどAではない）とは意味が違うので注意。",
                    "point": "no more A than B＝どちらも否定／no less A than B＝どちらも肯定。",
                },
                {
                    "stem": "He did not so (        ) as glance at the letter before throwing "
                            "it away.",
                    "ans": "much", "accept": [],
                    "exp": "not so much as do「〜さえしない」。"
                           "without so much as doing（〜さえせずに）の形でも頻出。"
                           "not so much A as B（AというよりB）とは別表現なので文脈で見分ける。",
                    "point": "not so much as do＝〜すらしない。",
                },
                {
                    "stem": "It goes without (        ) that no theory can be proved beyond "
                            "all doubt.",
                    "given": "say",
                    "ans": "saying", "accept": [],
                    "exp": "It goes without saying that ...「〜は言うまでもない」。"
                           "without は前置詞なので動名詞。"
                           "Needless to say, ... と言い換えられる。",
                    "point": "It goes without saying that SV.",
                },
                {
                    "stem": "For all we (        ), the universe may be teeming with life.",
                    "ans": "know", "accept": [],
                    "exp": "for all we know「もしかすると（＝私たちの知る限りでは否定できない）」。"
                           "for all A（Aにもかかわらず）の A が節になった慣用表現で、"
                           "断定を避ける前置きとして使われる。",
                    "point": "for all we know＝ひょっとすると。",
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
                    "context": "The idea of progress has a longer history than the word itself.",
                    "src": "What we call progress is less a description of where we are going "
                           "than an expression of the confidence, peculiar to a handful of "
                           "centuries, that where we are going is somewhere we should want to "
                           "arrive at.",
                    "model": "我々が進歩と呼ぶものは、自分たちがどこへ向かっているのかについての"
                             "記述というよりも、ほんの数世紀に特有の、自分たちの向かう先は"
                             "到達したいと思うべき場所なのだ、という確信の表れなのである。",
                    "alts": ["進歩と我々が呼んでいるものは、自分たちの行き先を述べたものというより、"
                             "ごく限られた数世紀だけが抱いた確信、すなわち、自分たちが向かっている"
                             "先は本来行き着きたいと願うべき場所だ、という確信の現れである。"],
                    "elements": [["less A than B（AというよりむしろB）を訳出できている", 2],
                                 ["peculiar to a handful of centuries が the confidence を"
                                  "修飾する挿入であることを訳に反映できている", 2],
                                 ["that where we are going is ... が the confidence の同格であること、"
                                  "および should want to（〜したいと思って当然の）を"
                                  "訳出できている", 2]],
                    "exp": "less A than B は not so much A as B と同義。"
                           "the confidence の直後にコンマで peculiar to ...（形容詞句）が挿入され、"
                           "その後ろの that 節が the confidence の同格として続く"
                           "＝修飾語をはさんで同格の that が離れている形。"
                           "somewhere we should want to arrive は接触節。",
                    "point": "同格の that は挿入をまたいで前の名詞につながることがある。",
                },
                {
                    "context": "Every generation rewrites the history it inherits.",
                    "src": "It is not that the facts change, but that each age asks of the past "
                           "the questions it most needs answered, and a question no one thinks "
                           "to ask is, for all practical purposes, a fact no one will find.",
                    "model": "事実が変わるということではなく、どの時代も過去に対して、自分が最も"
                             "答えを必要としている問いを投げかけるということであり、そして誰も"
                             "問おうと思いつかない問いは、事実上、誰にも発見されない事実なのである。",
                    "alts": ["事実そのものが変化するのではない。どの時代も、自分が何より答えを"
                             "求めている問いを過去に向けて発するのであり、誰も発想しない問いは、"
                             "実質的に、誰にも発見されない事実なのだ。"],
                    "elements": [["It is not that A but that B を訳出できている"
                                  "（「AということではなくBということだ」でも"
                                  "「AだからではなくBだからだ」でも可）", 2],
                                 ["asks of the past the questions ... の語順（ask A of B の"
                                  "A が後置された形）を正しく訳せている", 2],
                                 ["a question no one thinks to ask ／ a fact no one will find の"
                                  "接触節をそれぞれ訳せている", 2]],
                    "exp": "It is not that A but that B は「AだからではなくBだからだ」の型。"
                           "ask A of B（BにAを尋ねる）の A（the questions ...）が長いため "
                           "of the past の後ろに回っている。"
                           "needs answered は need＋O＋過去分詞（Oが〜されるのを必要とする）。"
                           "a question (that) no one thinks to ask は目的格の関係代名詞の省略。",
                    "point": "目的語が長いと後ろに回る（重い要素は文末へ）。",
                },
                {
                    "context": "Economists disagree about almost everything except the "
                               "difficulty of prediction.",
                    "src": "It would be wrong to conclude, from the failure of every model to "
                           "predict a crisis, that models are useless; what follows is only "
                           "that we should stop asking of them the one thing they were never "
                           "designed to do.",
                    "model": "あらゆるモデルが危機を予測できずにきたことから、"
                             "モデルは役に立たないと結論づけるのは誤りであろう。そこから導かれるのは、"
                             "そもそもモデルが果たすようには設計されていなかった、まさにその一点を"
                             "モデルに求めるのはやめるべきだ、ということだけである。",
                    "alts": ["どのモデルも危機を予測できなかったことをもって、モデルは無用だと"
                             "断じるのは誤りだろう。そこから言えるのはただ、そもそもモデルが"
                             "果たすようには設計されていなかったことを、モデルに求めるのは"
                             "やめるべきだ、ということだけである。"],
                    "elements": [["It would be wrong to conclude, from A, that B（Aから B と"
                                  "結論づけるのは誤りだろう）の骨格を訳出できている", 2],
                                 ["what follows is only that ... を「そこから導かれるのは…だけだ」"
                                  "と訳せている", 2],
                                 ["the one thing they were never designed to do の接触節を"
                                  "訳せている", 2]],
                    "exp": "conclude that ... の that 節が、挿入された from the fact that ... の"
                           "後ろに回っている（conclude ... that の間が離れる形）。"
                           "ask A of B の A が the one thing ... で、これも長いため後置。"
                           "what follows は「そこから帰結すること」。",
                    "point": "動詞と that 節の間に副詞句が割り込むことがある。骨格を先に取る。",
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
                    "ja": "他人の目を気にしすぎる人は、結局、自分の人生を生きられない。",
                    "model": "People who worry too much about how others see them will, in the "
                             "end, never live a life of their own.",
                    "alts": ["Those who are too concerned with the opinions of others will "
                             "ultimately fail to live their own lives."],
                    "elements": [["「他人の目を気にする」を how others see them / "
                                  "what others think of them / the opinions of others などで"
                                  "表せている", 1],
                                 ["「〜すぎる」を too much / excessively などで表せている", 1],
                                 ["「結局」を in the end / ultimately / after all などで"
                                  "表せている", 1],
                                 ["「自分の人生を生きる」を live a life of their own / "
                                  "live their own lives で表せている", 1]],
                    "exp": "「他人の目」を other people's eyes と直訳しない。"
                           "英語では「他人が自分をどう見るか」「他人がどう思うか」と節で表す。"
                           "「自分の人生を生きる」は live one's own life が定型で、"
                           "of one's own を使うと「自分だけの」という所有の強調になる。",
                },
                {
                    "ja": "便利な道具が増えるにつれて、私たちは自分の頭で考える機会を"
                          "少しずつ失っているのかもしれない。",
                    "model": "As convenient tools multiply, we may be gradually losing the "
                             "chance to think for ourselves.",
                    "alts": ["The more convenient tools we have, the less often we may stop "
                             "to think for ourselves."],
                    "elements": [["「〜につれて」の比例関係を As S V ／ The 比較級 … で表せている", 1],
                                 ["「かもしれない」を may / might で表せている", 1],
                                 ["「少しずつ失っている」という進行中の変化を、進行形や"
                                  "The 比較級 などで表せている", 1],
                                 ["「自分の頭で考える」を think for ourselves で表せている", 1]],
                    "exp": "「自分の頭で考える」は think for oneself が定型（by oneself は「独力で」）。"
                           "「〜つつある」という進行中の変化は現在進行形で表す。",
                },
                {
                    "ja": "自分が何を知らないかを知っている人だけが、本当に学ぶことができる。",
                    "model": "Only those who know what they do not know can really learn.",
                    "alts": ["It is only those who are aware of their own ignorance that can "
                             "truly learn anything."],
                    "elements": [["「〜する人だけが」を Only those who ... などで表せている", 1],
                                 ["Only＋主語のときは倒置しないことを踏まえ、語順が正しい", 1],
                                 ["「自分が何を知らないか」を what they do not know や "
                                  "their own ignorance などで表せている", 1],
                                 ["「本当に学ぶことができる」を can really [truly] learn で"
                                  "表せている", 1]],
                    "exp": "Only が付くのが主語のときは倒置しない（Only those who ... can learn.）。"
                           "倒置が起こるのは Only＋副詞句・副詞節が文頭に出たときだけで、"
                           "Only then did he realize ... のように助動詞が主語の前に出る。"
                           "この違いは難関大で繰り返し問われる。",
                },
                {
                    "ja": "子どもに必要なのは、失敗しないように守ってやることではなく、"
                          "失敗から立ち直る力を育ててやることだ。",
                    "model": "What children need is not to be protected from failure but to be "
                             "helped to develop the strength to recover from it.",
                    "alts": ["What children need is not to be shielded from failure but to be "
                             "given the strength to get back on their feet."],
                    "elements": [["「子どもに必要なのは」を What children need is ... または"
                                  "Children need ... で表せている", 1],
                                 ["not A but B の A と B を同じ形でそろえられている", 1],
                                 ["「失敗しないように守る」を protect [shield] A from failure で"
                                  "表せている", 1],
                                 ["「立ち直る力」を the strength [power] to recover from ... で"
                                  "表せている", 1]],
                    "exp": "子どもは「守られる」「育ててもらう」側なので受動の不定詞にする。"
                           "「失敗から立ち直る」は recover from failure / get over failure。",
                },
                {
                    "ja": "言葉は使えば使うほどすり減っていくが、同時に新しい意味を帯びていく。",
                    "model": "The more words are used, the more they wear out, and yet at the "
                             "same time they take on new meanings.",
                    "alts": ["Words lose their edge the more often they are used, but at the "
                             "same time they acquire new meanings."],
                    "elements": [["「使えば使うほど」の比例関係を The 比較級 …, the 比較級 … や"
                                  "the more often ... などで表せている", 1],
                                 ["「使う」の動作主を出さずに（受動態など）自然に処理できている", 1],
                                 ["「すり減る」を wear out / lose their edge などで表せている", 1],
                                 ["「同時に新しい意味を帯びる」を at the same time＋take on "
                                  "[acquire] new meanings で表せている", 1]],
                    "exp": "主語が「言葉」で動作主が人なので、従属節は受動態にすると自然。"
                           "「意味を帯びる」は take on / acquire a meaning。"
                           "wear out は自動詞で「すり減る」。",
                },
            ],
        },
    ],
}
