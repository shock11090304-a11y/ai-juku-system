# -*- coding: utf-8 -*-
"""仮定法 — 高校英文法レベル1 標準演習 (偏差値55-60)。

基礎  = 仮定法過去と仮定法過去完了の基本形、I wish。
ここ  = 混合仮定法、if の省略による倒置、if 節の代用 (But for / If it were not for)、
        It is time + 過去形、would rather + S + 過去形、要求提案の that 節の原形、
        otherwise、主語や副詞句が条件を表す形。
"""

UNIT = "仮定法"
UNIT_SLUG = "subjunctive"

QUESTIONS = [
    # ---------------- mc ----------------
    {
        "type": "mc", "level": "standard",
        "stem": "If I ( ) about the meeting, I would have attended it.",
        "choices": ["knew", "had known", "have known", "know"],
        "answer": "had known",
        "explanation": "主節が would have attended という形なので、過去の事実に反する仮定を表す仮定法過去完了だと分かる。"
                       "if 節は had + 過去分詞にそろえるので had known が正しい。"
                       "knew は仮定法過去で現在の事実に反する仮定になり、主節と時制が噛み合わない。have known や know も仮定法の形ではない。",
        "point": "If S had p.p., S would have p.p.",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "If she had taken the medicine last night, she ( ) much better now.",
        "choices": ["would feel", "would have felt", "felt", "will feel"],
        "answer": "would feel",
        "explanation": "if 節は last night の事実に反する仮定なので had taken だが、主節には now があり現在の結果を述べている。"
                       "このように条件と結果で時がずれる混合仮定法では、主節を would + 動詞の原形にするので would feel が正しい。"
                       "would have felt では過去の結果になり now と合わず、felt や will feel は仮定法の主節の形ではない。",
        "point": "過去の仮定 + 現在の結果は would + 原形",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "( ) I known your address, I would have written to you.",
        "choices": ["If", "Had", "Have", "Should"],
        "answer": "Had",
        "explanation": "If I had known your address から if を省略すると、had が主語の前に出て Had I known という倒置の形になる。"
                       "If を選ぶと後ろが I known となり、had が抜けた形になってしまう。"
                       "Have は時制が現在になり過去の仮定を表せず、Should は「万一~なら」で後ろに原形が必要なため known と続かない。",
        "point": "If S had p.p. の if 省略は Had S p.p.",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "( ) I in your position, I would accept the offer at once.",
        "choices": ["Were", "Was", "Am", "Had"],
        "answer": "Were",
        "explanation": "If I were in your position から if を省略した倒置形なので、be 動詞が主語の前に出て Were I となる。"
                       "仮定法では主語が I でも be 動詞は were を使うので、Was は倒置形として認められない。"
                       "Am は現在の事実を述べる形で仮定法にならず、Had は後ろに過去分詞が必要なため in your position と続かない。",
        "point": "If I were ~ の if 省略は Were I ~",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "( ) you need any help, please call this number at any time.",
        "choices": ["Should", "Would", "Were", "Had"],
        "answer": "Should",
        "explanation": "Should you need ~ は If you should need ~ の if を省略した倒置形で、should は「万一~なら」という可能性の低い仮定を表す。"
                       "この形では主節に命令文や will を置くことができ、please call と自然につながる。"
                       "Would は仮定法の if 節では使わず、Were の後ろには原形 need を置けない。Had は過去分詞が必要なため need と続かない。",
        "point": "Should S 原形 =「万一~なら」",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "I wish I ( ) how to play the guitar.",
        "choices": ["know", "knew", "have known", "will know"],
        "answer": "knew",
        "explanation": "I wish の後ろは仮定法で、現在の事実に反する願望は過去形で表すので knew が正しい。"
                       "実際には弾き方を知らないという現在の事実を、裏返して願っている。"
                       "現在形 know や未来形 will know では事実に反する願望にならず、have known も仮定法の形ではない。",
        "point": "I wish + 仮定法過去(現在の願望)",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "I wish I ( ) harder when I was a high school student.",
        "choices": ["studied", "had studied", "would study", "have studied"],
        "answer": "had studied",
        "explanation": "願っているのは今だが、内容は高校時代という過去のことなので、仮定法過去完了 had studied にする。"
                       "studied は仮定法過去で現在の願望を表す形なので、when I was a high school student と時が合わない。"
                       "would study はこれからのことへの願望を表し、have studied は仮定法の形ではない。",
        "point": "過去への後悔は I wish + had p.p.",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "He talks about the accident as if he ( ) it with his own eyes.",
        "choices": ["sees", "saw", "had seen", "has seen"],
        "answer": "had seen",
        "explanation": "talks は現在だが、事故を見たかどうかは talks より前のことなので、as if の後ろは仮定法過去完了 had seen にする。"
                       "saw は仮定法過去で「今~であるかのように」と同時のことを表すため、済んだ出来事には合わない。"
                       "sees や has seen は事実として述べる形で、「まるで~したかのように」という事実に反する言い方にならない。",
        "point": "述語より前なら as if + had p.p.",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "( ) your help, I could not finish this work by tomorrow.",
        "choices": ["If it were not for", "If it had not been for", "Unless", "In case of"],
        "answer": "If it were not for",
        "explanation": "主節が could not finish という仮定法過去なので、現在の事実に反する仮定を表す If it were not for ~「~がなければ」を選ぶ。"
                       "If it had not been for は仮定法過去完了で、主節が could not have finished のときに使う形なので時制が合わない。"
                       "Unless は後ろに節が必要で名詞 your help を直接置けず、In case of は「~の場合に備えて」で仮定法の条件にならない。",
        "point": "If it were not for ~ =「今~がなければ」",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "( ) the heavy snow, we would have arrived on time.",
        "choices": ["But for", "Except for", "Instead of", "Owing to"],
        "answer": "But for",
        "explanation": "But for ~ は「~がなかったら」と if 節の代わりをする表現で、主節の would have arrived と組んで過去の事実に反する仮定を表す。"
                       "Except for は「~を除けば」と例外を示すだけで、仮定法の条件を作らない。"
                       "Instead of は「~の代わりに」、Owing to は「~のせいで」と実際の原因を述べる表現なので、事実に反する仮定にならない。",
        "point": "But for ~ =「~がなかったら」",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "It is time you ( ) to bed. It is almost midnight.",
        "choices": ["go", "went", "have gone", "will go"],
        "answer": "went",
        "explanation": "It is time + 主語 + 過去形は「もう~してもよい頃だ」を表し、まだ実行されていないことを遠回しに促す言い方。"
                       "形は過去形でも内容は現在のことなので、went が正しい。"
                       "現在形 go はこの構文では使わず、have gone や will go も It is time に続く形として認められない。",
        "point": "It is time + S + 過去形",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "I would rather you ( ) anything about this to him.",
        "choices": ["do not say", "did not say", "not say", "will not say"],
        "answer": "did not say",
        "explanation": "would rather の後ろに主語を続けるときは、事実に反する希望として過去形を使うので did not say が正しい。"
                       "内容は「これから言わないでほしい」だが、形は過去形になる点が要点。"
                       "do not say や will not say は事実を述べる形で希望を表せず、not say は would rather の直後に主語がある場合の形として成り立たない。",
        "point": "would rather + S + 過去形",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "The doctor suggested that he ( ) smoking immediately.",
        "choices": ["stops", "stopped", "stop", "will stop"],
        "answer": "stop",
        "explanation": "suggest, insist, demand, propose などの後ろの that 節は (should) + 動詞の原形になる。"
                       "この should は省略できるので、主語が三人称単数でも s を付けずに stop のままにする。"
                       "stops や stopped、will stop は事実を述べる形で、提案の内容を表すこの構文には使えない。",
        "point": "suggest that S (should) + 原形",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "It is necessary that every student ( ) the safety rules.",
        "choices": ["follows", "follow", "followed", "will follow"],
        "answer": "follow",
        "explanation": "It is necessary / important / essential that の後ろの that 節も (should) + 動詞の原形になる。"
                       "should が省略されているので、主語 every student が三人称単数でも follow のまま s を付けない。"
                       "follows や followed、will follow は事実を述べる形で、必要性を述べるこの構文には使えない。",
        "point": "It is necessary that S (should) + 原形",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "I was very tired that day. ( ), I would have joined the party.",
        "choices": ["However", "Otherwise", "Therefore", "Instead"],
        "answer": "Otherwise",
        "explanation": "Otherwise は「そうでなければ」と直前の事実を裏返して条件にする語で、if 節の代わりをする。"
                       "主節が would have joined という仮定法過去完了なので、条件を表す語が必要になる。"
                       "However は「しかし」、Therefore は「したがって」、Instead は「その代わりに」で、いずれも事実に反する条件を作らない。",
        "point": "otherwise =「そうでなければ」(if 節の代用)",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "A wise person ( ) such a careless mistake.",
        "choices": ["does not make", "would not make", "has not made", "did not make"],
        "answer": "would not make",
        "explanation": "主語 A wise person が「もし賢い人なら」という条件を含んでおり、if 節が無くても仮定法の文になっている。"
                       "そのため主節は would + 動詞の原形の形をとり、would not make が正しい。"
                       "does not make や has not made、did not make は実際の事実を述べる形で、仮定の結果を表せない。",
        "point": "主語が条件を含むと主節は would + 原形",
    },
    {
        "type": "mc", "level": "advanced",
        "stem": "If the sun ( ) rise in the west, I would still love you.",
        "choices": ["were to", "was to", "is to", "had to"],
        "answer": "were to",
        "explanation": "If S were to do は、実現の可能性がほとんど無い未来のことを仮定する形。"
                       "仮定法なので be 動詞は主語に関係なく were を使い、was to は使わない。"
                       "is to は事実としての予定や義務を表し、had to は「~しなければならなかった」で、どちらも主節の would と噛み合わない。",
        "point": "If S were to do(可能性の低い未来の仮定)",
    },
    {
        "type": "mc", "level": "standard",
        "stem": "If I had more free time, I ( ) a new computer game every month.",
        "choices": ["will buy", "would buy", "would have bought", "bought"],
        "answer": "would buy",
        "explanation": "if 節が had という過去形なので、現在の事実に反する仮定を表す仮定法過去だと分かる。"
                       "仮定法過去では主節を would / could / might + 動詞の原形にするので would buy が正しい。"
                       "will buy は事実としての未来を表す形で仮定法にならず、would have bought は過去の仮定の結果、bought は主節の形として成り立たない。",
        "point": "If S 過去形, S would + 原形",
    },

    # ---------------- order ----------------
    {
        "type": "order", "level": "standard",
        "prompt_ja": "もし時間がもっとあれば、私はその手紙をもっと注意深く書けるのに。",
        "answer": "If I had more time, I could write the letter more carefully.",
        "explanation": "現在の事実に反する仮定なので、if 節は過去形 had、主節は could + 動詞の原形にする。"
                       "「もっと時間」は more time と名詞を修飾し、「もっと注意深く」は more carefully と副詞を修飾するので、2つの more の位置が決まる。"
                       "大文字で始まる If が文頭、コンマの付いた time, が前半の切れ目、carefully が文末になるため語順は一つに定まる。",
        "point": "If S 過去形, S could + 原形",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "あなたの助けがなかったら、私は成功できなかっただろう。",
        "answer": "If it had not been for your help, I could not have succeeded.",
        "explanation": "過去の事実に反する仮定なので、「~がなかったら」は If it had not been for ~ の形にする。"
                       "主節は could not have + 過去分詞で「~できなかっただろう」を表す。"
                       "大文字で始まる If が文頭、コンマの付いた help, が前半の切れ目、succeeded が文末になるため語順は一つに定まる。",
        "point": "If it had not been for ~(過去の条件)",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "もっと熱心に練習していれば、彼女は今チームのキャプテンだろうに。",
        "answer": "If she had practiced harder, she would be the captain of the team.",
        "explanation": "練習は過去のことなので if 節は had practiced、「今キャプテンだ」という結果は現在のことなので主節は would be にする。"
                       "このように条件と結果で時がずれるのが混合仮定法で、would have been にすると過去の結果になり現在の状態を表せない。"
                       "大文字で始まる If が文頭、コンマの付いた harder, が前半の切れ目、team が文末になるため語順は一つに定まる。",
        "point": "混合仮定法は if 節が過去・主節が現在",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "もし私があなたなら、その仕事を引き受けるだろう。",
        "answer": "Were I you, I would take that job.",
        "explanation": "If I were you から if を省略すると、be 動詞が主語の前に出て Were I you となる。"
                       "主節は仮定法過去の結果なので would + 動詞の原形にする。"
                       "大文字で始まる Were が文頭、コンマの付いた you, が前半の切れ目、job が文末になるため語順は一つに定まる。",
        "point": "Were I you =「もし私があなたなら」",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "万一何か問題があれば、すぐに私に知らせてください。",
        "answer": "Should there be any problem, please let me know at once.",
        "explanation": "If there should be any problem から if を省略した倒置形で、should が there の前に出る。"
                       "should は「万一~なら」という可能性の低い仮定を表し、主節に命令文を置ける。"
                       "大文字で始まる Should が文頭、コンマの付いた problem, が前半の切れ目、once が文末になるため語順は一つに定まる。",
        "point": "Should S 原形, 命令文",
    },
    {
        "type": "order", "level": "standard",
        "prompt_ja": "彼女がここに私といてくれたらいいのに。",
        "answer": "I wish she were here with me.",
        "explanation": "I wish の後ろは現在の事実に反する願望なので仮定法過去にし、be 動詞は主語が she でも were を使う。"
                       "実際には彼女がここにいないという事実を裏返して願っている。"
                       "文頭に置けるのは大文字の I だけで、me が文末になるため語順は一つに定まる。",
        "point": "I wish + S + were(仮定法の be)",
    },
    {
        "type": "order", "level": "advanced",
        "prompt_ja": "彼はまるで何もかも知っているかのような口ぶりだ。",
        "answer": "He talks as if he knew everything.",
        "explanation": "talks と同時のことを「まるで~であるかのように」と言うので、as if の後ろは仮定法過去 knew にする。"
                       "実際には全部を知っているわけではないという含みがあるため、事実を述べる knows は使わない。"
                       "大文字で始まる He が文頭、everything が文末になるため語順は一つに定まる。",
        "point": "as if + 仮定法過去(同時のこと)",
    },

    # ---------------- rewrite ----------------
    {
        "type": "rewrite", "level": "standard",
        "original": "As I do not have enough money, I cannot buy that bike.",
        "instruction": "仮定法過去を使い、原文の cannot (できない) の意味を保って、If で始まる一文に書き換えなさい。",
        "answer": "If I had enough money, I could buy that bike.",
        "explanation": "現在の事実を裏返して仮定するので、if 節は do not have を肯定の過去形 had にする。"
                       "原文の cannot は「買えない」という可能の否定なので、主節も would buy ではなく could buy にして意味を保つ。"
                       "使う形と保つべき意味が指定されているので答えは一つに定まる。",
        "point": "can/cannot の意味は could で受ける",
    },
    {
        "type": "rewrite", "level": "advanced",
        "original": "I am sorry that I did not listen to your advice.",
        "instruction": "I wish で始め、仮定法過去完了を使った一文に書き換えなさい。",
        "answer": "I wish I had listened to your advice.",
        "explanation": "後悔しているのは今だが、内容は過去のことなので I wish + 仮定法過去完了にする。"
                       "原文の否定 did not listen を裏返し、肯定の had listened にする点が要点。"
                       "書き出しと使う形が指定されているので答えは一つに定まる。",
        "point": "過去への後悔は I wish + had p.p.",
    },
    {
        "type": "rewrite", "level": "advanced",
        "original": "If you had not helped me, I would have failed.",
        "instruction": "if を使わない倒置の形にして、同じ意味の一文に書き換えなさい。",
        "answer": "Had you not helped me, I would have failed.",
        "explanation": "仮定法過去完了の if 節から if を省略すると、had が主語の前に出て倒置になる。"
                       "否定語 not は主語の後ろに残るので Had you not helped の語順になる。"
                       "主節 I would have failed はそのまま変えない。",
        "point": "If S had not p.p. = Had S not p.p.",
    },
    {
        "type": "rewrite", "level": "advanced",
        "original": "Without water, no living thing could survive.",
        "instruction": "If で始め、仮定法過去を使った一文に書き換えなさい。",
        "answer": "If it were not for water, no living thing could survive.",
        "explanation": "Without ~ は if 節の代用で、主節が could survive という仮定法過去なので If it were not for ~ に言い換える。"
                       "現在の事実に反する仮定なので、had not been for ではなく were not for にする。"
                       "主節 no living thing could survive はそのまま残す。",
        "point": "Without ~ = If it were not for ~",
    },
    {
        "type": "rewrite", "level": "advanced",
        "original": "I did not know his phone number, so I could not call him.",
        "instruction": "仮定法過去完了を使い、原文の could not (できなかった) の意味を保って、If で始まる一文に書き換えなさい。",
        "answer": "If I had known his phone number, I could have called him.",
        "explanation": "過去の事実を裏返して仮定するので、if 節は did not know を肯定の had known にする。"
                       "原文の could not は可能の否定なので、主節も would have called ではなく could have called にして意味を保つ。"
                       "使う形と保つべき意味が指定されているので答えは一つに定まる。",
        "point": "過去の事実の逆は If S had p.p., S could have p.p.",
    },
]
