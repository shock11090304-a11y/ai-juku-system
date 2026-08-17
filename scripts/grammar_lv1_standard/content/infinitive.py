# -*- coding: utf-8 -*-
"""不定詞 — 高校英文法レベル1 標準演習 (偏差値55-60)。

基礎  = 3用法の見分け、want to do、to 不定詞の基本。
ここ  = 前置詞の残留、意味上の主語 for / of、完了不定詞、原形不定詞と使役の受動、
        be to 構文、結果の不定詞、否定の位置、独立不定詞、慣用表現。
"""

UNIT = "不定詞"
UNIT_SLUG = "infinitive"

QUESTIONS = [
    # ---------------- mc ----------------
    {
        "type": "mc", "level": "standard",
        "stem": "I am looking for a house ( ) with my family.",
        "choices": ["to live", "to live in", "living", "to be lived"],
        "answer": "to live in",
        "explanation": "live は自動詞なので「~に住む」には前置詞 in が必要で、live in a house の形がもとになっている。"
                       "house を後ろから修飾する形容詞用法にしても in は消えずに残るため to live in が正しい。"
                       "to live では前置詞が抜けており、living は「住んでいる家」と現在の状態を表してしまう。to be lived は受動で「住まれる家」となり不自然。",
        "point": "自動詞 + 前置詞は不定詞でも前置詞を残す",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "It was careless ( ) to leave your umbrella on the train.",
        "choices": ["for you", "of you", "to you", "with you"],
        "answer": "of you",
        "explanation": "careless は「不注意だ」と人の性質を評価する形容詞なので、意味上の主語は of + 人で表し of you になる。"
                       "You are careless. と言い換えられるかどうかが of を選ぶ目印になる。"
                       "for you は難易・必要を表す形容詞のときの形で、性質を評価するこの文には使えない。to you や with you は意味上の主語を示す形ではない。",
        "point": "人の性質を評価する形容詞は of + 人",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "It is difficult ( ) to solve this problem in ten minutes.",
        "choices": ["of him", "for him", "to him", "that he"],
        "answer": "for him",
        "explanation": "difficult は事柄の難易を表す形容詞なので、不定詞の意味上の主語は for + 人で表し for him になる。"
                       "He is difficult. とは言い換えられないので of him は使えない。"
                       "to him は「彼にとって」と感じ方を添える形で不定詞の主語を示さず、that he は後ろが節になる形なので to solve と続けられない。",
        "point": "難易・必要を表す形容詞は for + 人",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "He seems ( ) rich when he was young.",
        "choices": ["to be", "to have been", "being", "having been"],
        "answer": "to have been",
        "explanation": "述語動詞 seems は現在だが、when he was young が示す内容は現在より前のことなので完了不定詞 to have been にする。"
                       "to be では「今裕福らしい」となり、過去を表す when 節と時間が合わない。"
                       "being や having been は動名詞なので、seem の後ろに置いて補語をとる形にはならない。",
        "point": "述語より前の内容は to have p.p.",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "The boy was made ( ) the room by his mother.",
        "choices": ["clean", "to clean", "cleaning", "cleaned"],
        "answer": "to clean",
        "explanation": "使役動詞 make は能動態では make + 目的語 + 原形不定詞だが、受動態になると省かれていた to が復活して be made to do の形になるので to clean が入る。"
                       "そのため原形の clean は受動態では使えない。"
                       "cleaning や cleaned では made の後ろに続く形として成り立たず、「掃除させられた」という使役の意味も出ない。",
        "point": "be made to do (使役の受動は to が戻る)",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "I saw him ( ) the building around noon.",
        "choices": ["to enter", "enter", "entered", "to entering"],
        "answer": "enter",
        "explanation": "see は知覚動詞なので see + 目的語 + 原形不定詞の形をとり、「彼が建物に入るのを見た」を表す。"
                       "知覚動詞の後ろでは to を付けないため to enter や to entering は誤り。"
                       "entered は過去形で、目的語の後ろに続く形として成り立たない。",
        "point": "知覚動詞 + O + 原形不定詞",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "( ) the truth, I do not agree with his plan.",
        "choices": ["To tell", "Telling", "Told", "To be told"],
        "answer": "To tell",
        "explanation": "To tell the truth は「実を言うと」という意味の独立不定詞で、文全体に話し手の態度を添える決まった形。"
                       "文の主語 I が tell の動作主なので、Telling や Told のような分詞にすると主語との関係がずれる。"
                       "To be told は受動で「告げられると」の意味になり、the truth を目的語にとれない。",
        "point": "To tell the truth =「実を言うと」",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "If you ( ) succeed in this field, you must work much harder.",
        "choices": ["are to", "are going", "will", "have"],
        "answer": "are to",
        "explanation": "be to 不定詞が if 節の中で使われると「~するつもりなら・~したいのなら」という意図を表すので、主語 you に合わせた are to が入る。"
                       "are going の後ろには to が必要で、この形のままでは原形 succeed を続けられない。"
                       "will は if 節の中で単なる未来を表すのに使わない形であり、have も後ろに to が無いので succeed とつながらない。",
        "point": "If S be to do =「~するつもりなら」",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "She hurried to the station, only ( ) that the last train had already gone.",
        "choices": ["finding", "to find", "found", "to have found"],
        "answer": "to find",
        "explanation": "only to do は「~したが、結局…しただけだった」という残念な結果を表す不定詞の副詞的用法なので to find が入る。"
                       "only の後ろは to + 動詞の原形と決まっているので finding や found は続けられない。"
                       "to have found は主節より前の出来事を表す形で、「急いだ結果あとで分かった」という時間の流れと逆になる。",
        "point": "only to do =「~したが結局…だった」",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "This box is too heavy for me ( ).",
        "choices": ["to carry", "to carry it", "carrying", "to be carried"],
        "answer": "to carry",
        "explanation": "too ~ to do の構文では、文の主語 This box がそのまま不定詞の意味上の目的語になる。"
                       "そのため to carry it とすると目的語が二重になり誤りで、目的語を置かない to carry が正しい。"
                       "carrying は too ~ to の形を作れない。"
                       "to be carried にすると for me が「私が運ばれる」の意味上の主語になってしまい、箱を運ぶという内容とずれる。",
        "point": "too ~ to do の後ろに目的語は置かない",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "He was kind ( ) me the way to the station.",
        "choices": ["enough to show", "enough showing", "to enough show", "enough for showing"],
        "answer": "enough to show",
        "explanation": "enough は形容詞や副詞を後ろから修飾するので kind enough の語順になり、続けて to 不定詞を置く enough to show が正しい (~ enough to do で「…するほど~だ」)。"
                       "enough showing や enough for showing は enough の後ろに不定詞を置く形から外れている。"
                       "to enough show は to と動詞の間に enough が割り込んでおり、語順として成り立たない。",
        "point": "形容詞 + enough + to do の語順",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "I could not decide ( ) for her birthday.",
        "choices": ["what to buy", "what buying", "to buy what", "what buy"],
        "answer": "what to buy",
        "explanation": "疑問詞 + to 不定詞は「何を~すべきか」という意味の名詞のかたまりを作るので、what to buy が decide の目的語になる。"
                       "what buying や what buy は疑問詞の後ろが to 不定詞になっていないため名詞のかたまりを作れない。"
                       "to buy what は疑問詞が後ろに残っており、目的語としてのまとまりにならない。",
        "point": "疑問詞 + to do で名詞のかたまり",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "I am sorry ( ) you waiting so long yesterday.",
        "choices": ["to keep", "to have kept", "keeping", "having kept"],
        "answer": "to have kept",
        "explanation": "謝っているのは今だが、待たせたのは yesterday なので、述語より前の内容を表す完了不定詞 to have kept を使う。"
                       "to keep では「これから待たせること」または今の状態を指し、yesterday と噛み合わない。"
                       "keeping や having kept は動名詞で、be sorry の後ろに前置詞なしで直接続けることはできない。",
        "point": "be sorry to have p.p.(過去のことを謝る)",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "It took me three hours ( ) the report.",
        "choices": ["finish", "finishing", "to finish", "for finishing"],
        "answer": "to finish",
        "explanation": "It takes + 人 + 時間 + to do は「人が~するのに時間がかかる」を表す決まった形で、後ろは必ず to 不定詞になる。"
                       "この It は形式主語で、本当の主語は to finish the report である。"
                       "原形 finish や動名詞 finishing、for finishing はこの構文の形に当てはまらない。",
        "point": "It takes + 人 + 時間 + to do",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "He left home early ( ) miss the first train.",
        "choices": ["so as not to", "so as to not", "not so as to", "in order not"],
        "answer": "so as not to",
        "explanation": "「~しないように」と目的を否定するときは so as not to do または in order not to do の形にし、not は to の直前に置く。"
                       "so as to not は not の位置がずれており、学校文法では正しい形として扱わない。"
                       "not so as to は否定語が構文全体の前に出てしまい、in order not は to が抜けているため原形 miss を続けられない。",
        "point": "否定の目的は so as not to do",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "They finally managed ( ) the top of the mountain before sunset.",
        "choices": ["reaching", "to reach", "reach", "reached"],
        "answer": "to reach",
        "explanation": "manage は to 不定詞だけを目的語にとる動詞なので to reach が入り、manage to do で「なんとか~する」を表す。"
                       "動名詞 reaching を目的語にとることはできない。"
                       "原形 reach や過去形 reached は managed の後ろに直接続けられる形ではない。",
        "point": "manage to do =「なんとか~する」",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "We had no choice ( ) the plan.",
        "choices": ["but to accept", "but accepting", "except accept", "than to accept"],
        "answer": "but to accept",
        "explanation": "have no choice but to do は「~するより仕方がない」を表す決まった形で、but の後ろは to 不定詞になるので but to accept が正しい。"
                       "この but は「~以外に」という意味の前置詞だが、この構文では例外的に to 不定詞を続ける。"
                       "but accepting や except accept、than to accept はいずれもこの決まった形から外れている。",
        "point": "have no choice but to do",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "He promised ( ) late again.",
        "choices": ["not to be", "to not be", "to be not", "not being"],
        "answer": "not to be",
        "explanation": "不定詞を否定するときは not を to の直前に置いて not to do とするのが原則なので not to be が正しい。"
                       "to not be は to と動詞の間に not が割り込んだ形で、学校文法では正しい形として扱わない。"
                       "to be not は否定語の位置が後ろすぎて成り立たず、not being は動名詞なので promise の目的語にできない。",
        "point": "不定詞の否定は not + to do",
    },

    # ---------------- order ----------------
    {
        "type": "order", "level": "standard",
        "prompt_ja": "私は彼に何と言えばよいのか分からなかった。",
        "answer": "I did not know what to say to him.",
        "explanation": "「何と言えばよいか」は疑問詞 + to 不定詞の what to say で表し、know の目的語にする。"
                       "「彼に」は say の相手なので to him を後ろに置く。to が2つ出てくるが、前の to は不定詞、後ろの to は前置詞である。"
                       "文頭に置けるのは大文字の I だけで、him が文末になるため語順は一つに定まる。",
        "point": "what to say + to + 相手",
    },
    {
        "type": "order", "level": "standard",
        "prompt_ja": "この川は泳ぐには危険すぎる。",
        "answer": "This river is too dangerous to swim in.",
        "explanation": "too + 形容詞 + to do で「~するには…すぎる」を表す。"
                       "swim は自動詞で「川で泳ぐ」は swim in the river なので、主語 This river が意味上の目的語になるこの形では前置詞 in が文末に残る。"
                       "大文字で始まる This が文頭、in が文末になるため語順は一つに定まる。",
        "point": "too ~ to do でも前置詞は残す",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "彼女は親切にも私を駅まで車で送ってくれた。",
        "answer": "It was kind of her to drive me to the station.",
        "explanation": "形式主語 It で始め、人の性質を評価する kind には意味上の主語を of her で示す。"
                       "本当の主語である to drive me to the station を後ろに置いて「駅まで車で送ってくれたこと」を表す。"
                       "大文字で始まる It が文頭、station が文末になるため語順は一つに定まる。",
        "point": "It is kind of + 人 + to do",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "始発電車に乗り遅れないように、早く家を出なさい。",
        "answer": "Leave home early so as not to miss the first train.",
        "explanation": "命令文なので動詞の原形 Leave で始め、目的の否定は so as not to do の形にする。"
                       "not は to の直前に置き、その後ろに原形 miss を続ける。"
                       "大文字で始まる Leave が文頭、train が文末になるため語順は一つに定まる。",
        "point": "so as not to + 原形",
    },
    {
        "type": "order", "level": "standard",
        "prompt_ja": "私に何か冷たい飲み物をください。",
        "answer": "Please give me something cold to drink.",
        "explanation": "-thing で終わる代名詞は形容詞を後ろに置くので something cold の語順になる。"
                       "さらに後ろから to drink が修飾して「飲むための冷たい何か」となり、形容詞と不定詞の順番が決まる。"
                       "大文字で始まる Please が文頭、drink が文末になるため語順は一つに定まる。",
        "point": "something + 形容詞 + to 不定詞",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "彼は若い頃、有名な歌手だったようだ。",
        "answer": "He seems to have been a famous singer when he was young.",
        "explanation": "「~のようだ」は seem を現在形で使い、「若い頃だった」という述語より前の内容は完了不定詞 to have been で表す。"
                       "時を示す when he was young を文末に置く。"
                       "大文字で始まる He が文頭、young が文末になるため語順は一つに定まる。",
        "point": "seem to have p.p. で「~だったようだ」",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "彼は大きくなって有名な科学者になった。",
        "answer": "He grew up to be a famous scientist.",
        "explanation": "grow up to be ~ は「成長して~になる」という結果を表す不定詞の副詞的用法。"
                       "「~するために大きくなった」という目的ではなく、成長した結果どうなったかを表す点が要点。"
                       "大文字で始まる He が文頭、scientist が文末になるため語順は一つに定まる。",
        "point": "grow up to be ~(結果の不定詞)",
    },

    # ---------------- rewrite ----------------
    {
        "type": "rewrite", "level": "standard",
        "original": "This coffee is so hot that I cannot drink it.",
        "instruction": "too ~ to を使い、原文の I を意味上の主語として残したまま、This coffee で始まる一文に書き換えなさい。",
        "answer": "This coffee is too hot for me to drink.",
        "explanation": "so ~ that S cannot do は too ~ to do で言い換えられる。"
                       "原文の主語 I は不定詞の意味上の主語として for me の形で残す。"
                       "書き換え後は主語 This coffee が drink の意味上の目的語になるので、原文の it は落として to drink とする。",
        "point": "so ~ that S cannot = too ~ for 人 to do",
    },
    {
        "type": "rewrite", "level": "standard",
        "original": "He was so kind that he carried my bag.",
        "instruction": "不定詞を使い、It was で始まる一文に書き換えなさい。",
        "answer": "It was kind of him to carry my bag.",
        "explanation": "kind は人の性質を評価する形容詞なので、形式主語 It を立てると意味上の主語は of him になる。"
                       "実際にした行為である carried は不定詞 to carry にして本当の主語にする。"
                       "for him にすると人の性質を評価する形から外れるので、of を選ぶことが要点。",
        "point": "性質の評価は It is 形容詞 of 人 to do",
    },
    {
        "type": "rewrite", "level": "advanced",
        "original": "It seems that she was ill last week.",
        "instruction": "She を主語にし、不定詞を使った一文に書き換えなさい。",
        "answer": "She seems to have been ill last week.",
        "explanation": "It seems that S + 過去形 は、主語を人に変えると seem to have p.p. の形になる。"
                       "seems は現在で that 節の中は過去なので、時間のずれを表すために完了不定詞にする。"
                       "to be ill にすると「今病気らしい」となり last week と合わなくなる。",
        "point": "It seems that S 過去 = S seems to have p.p.",
    },
    {
        "type": "rewrite", "level": "advanced",
        "original": "My mother made me wash the dishes.",
        "instruction": "I を主語にした受動態の一文に書き換えなさい。",
        "answer": "I was made to wash the dishes by my mother.",
        "explanation": "使役動詞 make は能動態では原形不定詞を続けるが、受動態になると to が復活して be made to do になる。"
                       "目的語 me を主語 I に変え、動作主は by my mother で示す。"
                       "wash をそのまま原形で残すと受動態の形として成り立たない。",
        "point": "make O do の受動は be made to do",
    },
    {
        "type": "rewrite", "level": "advanced",
        "original": "He worked hard so that he could pass the exam.",
        "instruction": "in order to を使い、He で始まる一文に書き換えなさい。",
        "answer": "He worked hard in order to pass the exam.",
        "explanation": "so that S can do は目的を表す副詞節で、主語が主節と同じときは in order to do で言い換えられる。"
                       "節が句に変わるので、主語 he と助動詞 could は消えて動詞は原形 pass になる。"
                       "in order to を使うと指定されているので答えは一つに定まる。",
        "point": "so that S can do = in order to do",
    },
]
