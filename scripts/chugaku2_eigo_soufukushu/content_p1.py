# -*- coding: utf-8 -*-
"""第1部 基礎の確認（教科書の例文レベル／定期テストの基本問題）37問／100点

★このファイルは assemble.py が生成する。手で直してよいが、
  再生成すると上書きされる（作問JSON側も直すこと）。
"""

PART = {
    "no": 1,
    "level": "基礎の確認",
    "univ": "教科書の例文レベル／定期テストの基本問題",
    "aim": "まず形を思い出す部です。一文が短く、判断することは一つだけ。ここが8割取れたら第2部へ進んでください。",
    "time": 40,
    "total": 100,
    "steps": [
        "まず40分を目安に、最後まで解ききる（1回目は時間をこえてもよい）。",
        "わからない問題も飛ばさず、必ず何かを書いてから次へ進む。",
        "答え合わせのあと、間違えた問題の日本語をもう一度読み、自分で英文を作り直す。"
    ],
    "sections": [
        {
            "no": 1,
            "kind": "mc",
            "pt": 2,
            "title": "空所補充（四択）",
            "inst": "次の各文の空所に入る最も適切なものを、①〜④から一つ選び、その番号を◯で囲め。",
            "items": [
                {
                    "unit": "U1",
                    "stem": "Yuki (        ) her science notebook to Mr. Sato yesterday.",
                    "choices": [
                        "taking",
                        "took",
                        "take",
                        "takes"
                    ],
                    "ans": 1,
                    "exp": "yesterday があるので過去の文にする。take は形が大きく変わる仲間で、過去を表す形は took になる。take と takes は今のことを言う形なので過去の場面には合わない。taking は前に be動詞がないと文の動詞になれない。",
                    "point": "take → took のように形が大きく変わる動詞は、過去を表す形を丸ごと覚える。"
                },
                {
                    "unit": "U2",
                    "stem": "Ken and Emi (        ) their textbooks at four yesterday.",
                    "choices": [
                        "was reading",
                        "reading",
                        "were reading",
                        "are reading"
                    ],
                    "ans": 2,
                    "exp": "at four yesterday は過去のある時点を指すので、そのとき続いていた動作の形にする。主語は2人だから were を選び、あとを read の -ing 形にする。are は今のことを言う形で過去に合わない。reading だけでは文の動詞がそろわない。",
                    "point": "主語が1人なら was、2人以上なら were を使い、動詞は -ing にする。"
                },
                {
                    "unit": "U3",
                    "stem": "Mr. Sato (        ) check our homework tomorrow.",
                    "choices": [
                        "is going to",
                        "going to",
                        "is going",
                        "are going to"
                    ],
                    "ans": 0,
                    "exp": "前もって決まっている予定は〈be動詞 ＋ going to ＋ 原形〉で言い表す。going to だけでは be動詞が足りない。is going には to がなく、あとに check を続けられない。主語は一人なので are going to も合わない。",
                    "point": "すでに決めてある予定は〈be動詞 ＋ going to ＋ 原形〉で言う。"
                },
                {
                    "unit": "U4",
                    "stem": "Ken (        ) use his phone in Mr. Sato's class.",
                    "choices": [
                        "must not to",
                        "must not",
                        "don't must",
                        "not must"
                    ],
                    "ans": 1,
                    "exp": "「してはいけない」と止めるときは must のすぐ後ろに not を置く。must not to は to が余分で、あとの原形 use につながらない。must は助動詞なので don't とは並べられない。not must という語順も英語にはない。",
                    "point": "「〜してはいけない」と禁止するときは must の後ろに not を置く。"
                },
                {
                    "unit": "U5",
                    "stem": "Emi looked sleepy in class (        ) she studied late last night.",
                    "choices": [
                        "because of",
                        "how",
                        "because",
                        "why"
                    ],
                    "ans": 2,
                    "exp": "「遅くまで勉強した」という理由をあとに続けているので because を使う。because of のうしろには名詞が来るため、she studied のような主語と動詞は置けない。how や why はこの位置で二つの文を結びつけるはたらきを持たない。",
                    "point": "理由をあとから説明するときは because を置き、そのあとに主語と動詞を続ける。"
                },
                {
                    "unit": "U6",
                    "stem": "There (        ) seven classes on our schedule today.",
                    "choices": [
                        "is",
                        "have",
                        "be",
                        "are"
                    ],
                    "ans": 3,
                    "exp": "あとに来る名詞が seven classes と複数なので are を選ぶ。is は名詞が1つのときの形で、複数には合わない。be は主語に合わせて形を変えないと文の動詞になれない。have は中2では There のあとに置かない。have で「〜がある」と言うときは Our school has a big gym. のように場所を主語にする。",
                    "point": "後ろの名詞が単数か複数かで、There is と There are を使い分ける。"
                },
                {
                    "unit": "U7",
                    "stem": "Yuki stayed in the computer room (        ) her report.",
                    "choices": [
                        "to print",
                        "to printing",
                        "for print",
                        "print to"
                    ],
                    "ans": 0,
                    "exp": "「印刷するために」と何のためかを言うので〈to ＋ 原形〉にする。to のあとは原形なので to printing は形が違う。for のうしろに動詞の原形は置けないため for print も誤り。print to では語のまとまりが作れない。",
                    "point": "目的をそえるときは to ＋ 原形を使い、「〜するために」と読む。"
                },
                {
                    "unit": "U8",
                    "stem": "Our class enjoyed (        ) English songs in music class.",
                    "choices": [
                        "sing",
                        "singing",
                        "to sing",
                        "sang"
                    ],
                    "ans": 1,
                    "exp": "enjoy のうしろに動作を続けるときは -ing の形にするので singing が正しい。sing や sang をそのまま置くと動詞が二つ並ぶ。enjoy は to のついた形を目的語に取らないので to sing も使えない。finish も同じなかまだ。",
                    "point": "enjoy や finish の目的語になる動詞は -ing の形に変える。"
                },
                {
                    "unit": "U10",
                    "stem": "Mr. Sato's math test was (        ) than the English test.",
                    "choices": [
                        "more hard",
                        "hardest",
                        "hard",
                        "harder"
                    ],
                    "ans": 3,
                    "exp": "than があるので二つをくらべる形にする。hard はつづりの短い語なので語尾に -er を付けて harder にする。hard のままでは比べる意味が出ない。短い語に more は付けない。hardest は三つ以上で「いちばん」と言うときの形。",
                    "point": "二つをくらべるときは、短い語の終わりを -er にして than の前に置く。"
                },
                {
                    "unit": "U11",
                    "stem": "The school library (        ) by two teachers every morning.",
                    "choices": [
                        "opens",
                        "is opened",
                        "is opening",
                        "opened"
                    ],
                    "ans": 1,
                    "exp": "図書室は開けられる側なので〈be動詞 ＋ 過去分詞〉にする。open の過去分詞は opened。opens にすると図書室が自分で開くことになり、by 〜 とつながらない。is opening は今まさに開けている最中の意味になり、every morning と合わない。opened だけでは前に be動詞がなく、文の動詞になれない。",
                    "point": "ものを主語にして「される」と言う文は be動詞と過去分詞で作る。"
                }
            ]
        },
        {
            "no": 2,
            "kind": "fill",
            "pt": 2,
            "title": "空所補充（記述）",
            "inst": "次の各文の空所に入る適切な語句を書け（2語以上になることもある）。空所のうしろに語が示してある場合は、その語を適切な形に変えて書くこと。空所の中に文字が示してある場合は、その文字で始まる語句を書くこと。",
            "items": [
                {
                    "unit": "U1",
                    "stem": "(   ) Taku get up early yesterday morning?",
                    "ans": "Did",
                    "given": "do",
                    "exp": "yesterday morning があるので過去のことをたずねている。一般動詞の過去の疑問文は Did で文を始める。Did が過去を表しているので、うしろの動詞は原形のまま get にしておく。got としないこと。答えるときも Yes, he did. のように did を使う。",
                    "point": "一般動詞の過去の疑問文は Did で始め、うしろの動詞は原形のままにする"
                },
                {
                    "unit": "U2",
                    "stem": "My grandfather was (   ) on the sofa when I came home.",
                    "ans": "sitting",
                    "given": "sit",
                    "exp": "sit は最後の子音字を重ねて sitting とつづる。ing をそのままつけた siting は誤り。e で終わる make は e を取って making になるなど、動詞ごとにつづり方が変わる。",
                    "point": "sit のように最後の字を重ねて -ing をつづる動詞がある"
                },
                {
                    "unit": "U3",
                    "stem": "Aya is busy today, so she ( w ) come to my house.",
                    "ans": "won't",
                    "hint": "w",
                    "accept": [
                        "will not"
                    ],
                    "exp": "will not を1語にちぢめると won't になる。前に忙しいという理由があるので、否定の形を入れる。wo のつづりが will と変わる点に注意。will not と2語で書いても正解。",
                    "point": "will not を1語にちぢめた won't が「〜しないだろう」を表す"
                },
                {
                    "unit": "U4",
                    "stem": "My brother (   ) wash the dishes after dinner every day.",
                    "ans": "has to",
                    "given": "have to",
                    "exp": "主語の my brother は三人称単数なので、have to を has to に形を変える。to のあとの動詞は原形の wash のままでよい。every day があるので現在の文だと分かる。",
                    "point": "主語が三人称単数のときは have to を has to に変える"
                },
                {
                    "unit": "U5",
                    "stem": "I think ( t ) my mother is in the kitchen now.",
                    "ans": "that",
                    "hint": "t",
                    "exp": "I think のあとに〈主語＋動詞〉の文が続くときは that でつなぐ。この that は「〜ということ」を表す目印で、会話では省かれることも多い。ここは1語なので that を書く。",
                    "point": "I think のあとに文を続けるときは that でつなぐ"
                },
                {
                    "unit": "U6",
                    "stem": "There (   ) some old photos on the wall last year.",
                    "ans": "were",
                    "given": "be",
                    "exp": "last year があるので過去の文になり、be動詞も過去形にする。あとにくる photos が複数なので was ではなく were を選ぶ。1枚なら There was an old photo. となる。",
                    "point": "過去のことなら There のあとの be動詞を was か were にする"
                },
                {
                    "unit": "U9",
                    "stem": "I was sick, so my mother made some hot milk ( f ) me.",
                    "ans": "for",
                    "hint": "f",
                    "exp": "〈make ＋ 人 ＋ 物〉は、物を先に置くと〈make ＋ 物 ＋ for ＋ 人〉になる。make や buy は for、give や show は to を使うので、動詞ごとに覚える。相手を先に置くときは for も to もいらない。",
                    "point": "make や buy は、物を先に置くと相手の前に for を使う。"
                },
                {
                    "unit": "U10",
                    "stem": "My grandfather is the (   ) in my family.",
                    "ans": "oldest",
                    "given": "old",
                    "accept": [
                        "eldest"
                    ],
                    "exp": "3つ以上のものを比べていちばん〜だと言うときは、the をつけて old を oldest にする。in my family は比べる範囲を表す。長い形容詞では -est を使わない形もある。",
                    "point": "3つ以上を比べていちばん〜と言うときは the と -est を使う"
                },
                {
                    "unit": "U11",
                    "stem": "This letter was (   ) by my brother last night.",
                    "ans": "written",
                    "given": "write",
                    "exp": "受け身は〈be動詞＋過去分詞〉の形。write の過去分詞は wrote ではなく written で、不規則に変化する。was written で「書かれた」という過去の受け身になる。",
                    "point": "受け身で使う不規則動詞の過去分詞は written のように変わる"
                },
                {
                    "unit": "U12",
                    "stem": "I don't know ( h ) use this washing machine.",
                    "ans": "how to",
                    "hint": "h",
                    "exp": "how to のあとに動詞の原形を置くと「〜のしかた」という意味になる。ここは use の前なので how to が入る。know や learn のあとでよく使う言い方。",
                    "point": "how to のあとに原形を続けると「〜のしかた」の意味になる"
                }
            ]
        },
        {
            "no": 3,
            "kind": "order",
            "pt": 3,
            "title": "語句整序",
            "inst": "日本語の意味を表すように、かっこ内の語をすべて並べ替えて英文を完成させよ。文の最初に来る語も大文字で示してある（人名と I はいつでも大文字）。",
            "items": [
                {
                    "unit": "U3",
                    "ja": "あなたは明日、朝の練習に来てくれますか。",
                    "frame": "[ ] tomorrow?",
                    "tokens": [
                        "come",
                        "Will",
                        "practice",
                        "you",
                        "the",
                        "to",
                        "morning"
                    ],
                    "ans": "Will you come to the morning practice",
                    "exp": "相手にたのんだり予定をたずねたりするときは、will を文の先頭に出して〈Will ＋ 主語 ＋ 動詞の原形〉の形にする。come は原形のままで comes や came にしない。答えるときは Yes, I will. のように言う。",
                    "point": "will を主語の前に出すと、相手に依頼したり予定をたずねたりする疑問文になる。"
                },
                {
                    "unit": "U5",
                    "ja": "ショウが体育館で練習したとき、コーチが彼を手伝ってくれました。",
                    "frame": "[ ], the coach helped him.",
                    "tokens": [
                        "practiced",
                        "gym",
                        "When",
                        "the",
                        "in",
                        "Sho"
                    ],
                    "ans": "When Sho practiced in the gym",
                    "exp": "when のかたまりを先に置くときは〈When ＋ 主語 ＋ 動詞〉の順に並べ、区切りにコンマを打ってから中心の文を続ける。同じ内容を後半に回して言うこともでき、そのときはコンマがいらない。時を表す部分と中心の文を見分けるのがこつ。",
                    "point": "when の節を先に置くときは、そのかたまりの終わりにコンマを入れる。"
                },
                {
                    "unit": "U7",
                    "ja": "ナナは練習のあとに、何か飲み物を持ってきました。",
                    "frame": "[ ] after practice.",
                    "tokens": [
                        "brought",
                        "to",
                        "Nana",
                        "something",
                        "drink"
                    ],
                    "ans": "Nana brought something to drink",
                    "exp": "something をくわしく説明するときは、うしろに to ＋ 動詞の原形を置く。to drink は「飲むための」という意味で、前の something をうしろから説明している。Nana brought to drink something のように、説明される語をうしろへ回すことはできない。",
                    "point": "something は、うしろに to ＋ 原形を続けて中身をくわしく説明する。"
                },
                {
                    "unit": "U8",
                    "ja": "ナナはその試合を見たあとで家に帰りました。",
                    "frame": "[ ] the game.",
                    "tokens": [
                        "home",
                        "Nana",
                        "watching",
                        "after",
                        "went"
                    ],
                    "ans": "Nana went home after watching",
                    "exp": "after は前置詞としても使え、そのうしろに動詞を続けるときは watch ではなく watching の形にする。after watched や after to watch とは言えない。-ing の形はここでは名詞と同じはたらきをしている。",
                    "point": "before や after を前置詞として使うと、次の動詞は -ing の形になる。"
                },
                {
                    "unit": "U9",
                    "ja": "ショウは昨日、私たちに自分の新しいグローブを見せてくれました。",
                    "frame": "Sho [ ] yesterday.",
                    "tokens": [
                        "new",
                        "showed",
                        "us",
                        "his",
                        "glove"
                    ],
                    "ans": "showed us his new glove",
                    "exp": "show のうしろは、見せる相手 us を先に、見せる中身 his new glove をあとに置く。この並びなら to はいらない。his new glove us のように相手をうしろへ回すことはできない。his new は持ち主と様子を表している。",
                    "point": "show のうしろは、見せる相手 のあとに 見せる中身 を続けて2つ並べる。"
                },
                {
                    "unit": "U10",
                    "ja": "ショウはナナと同じくらい速く走ることができます。",
                    "frame": "[ ] Nana.",
                    "tokens": [
                        "fast",
                        "Sho",
                        "as",
                        "run",
                        "can",
                        "as"
                    ],
                    "ans": "Sho can run as fast as",
                    "exp": "程度が同じだと言うときは、as と as のあいだに形容詞や副詞をそのままの形ではさむ。ここは速く走るなので副詞 fast を使い、faster のように形を変えてはいけない。うしろの as のあとには、くらべる相手を置く。",
                    "point": "as と as ではさんだ形容詞や副詞はもとの形のままで、程度が同じことを表す。"
                },
                {
                    "unit": "U11",
                    "ja": "その部室は私たちのチームによってそうじされました。",
                    "frame": "[ ] our team.",
                    "tokens": [
                        "cleaned",
                        "club",
                        "The",
                        "by",
                        "was",
                        "room"
                    ],
                    "ans": "The club room was cleaned by",
                    "exp": "〈was ＋ 過去分詞〉でされたという意味を表し、動作をした側を言い足すときは by を続ける。by がないと、だれがしたのか分からない文になる。clean は規則変化なので過去分詞も cleaned。主語が単数なので be動詞は was を選ぶ。",
                    "point": "動作をした人をはっきり示したいときは、受け身の文に by を付け加える。"
                },
                {
                    "unit": "U12",
                    "ja": "毎回の試合に勝つことは大変です。",
                    "frame": "[ ] every game.",
                    "tokens": [
                        "to",
                        "is",
                        "hard",
                        "It",
                        "win"
                    ],
                    "ans": "It is hard to win",
                    "exp": "この It はそれという意味ではなく、形だけの主語。本当に伝えたい内容は to win every game で、あとから示す形になる。to のうしろは必ず原形なので wins や won にしない。ようすを表す hard は It is のすぐあとに置く。",
                    "point": "文の主語の位置に It を置き、本当の内容は to ＋ 原形であとから示す。"
                }
            ]
        },
        {
            "no": 4,
            "kind": "rewrite",
            "pt": 4,
            "title": "書き換え",
            "inst": "次の各文を、（　）内の指示にしたがって書き換えよ。",
            "items": [
                {
                    "unit": "U1",
                    "src": "Ryo plans the school trip with his classmates.",
                    "inst": "過去の文に直しなさい。",
                    "ans": "Ryo planned the school trip with his classmates.",
                    "exp": "plan は最後の n を重ねて planned とする。規則動詞は -ed を付けるのが基本だが、短い母音＋子音字で終わる語は子音字を重ねる。study のように子音字＋y で終わる語は y を i に変えてから -ed を付ける。",
                    "point": "規則動詞の過去形は -ed を付けるが、つづりが変わる語に注意する。"
                },
                {
                    "unit": "U4",
                    "src": "The students must clean the gym before the sports day.",
                    "inst": "must を have to を使った文に直しなさい。",
                    "ans": "The students have to clean the gym before the sports day.",
                    "exp": "must と have to はどちらも義務を表し、ほぼ同じ意味で使える。主語が The students と複数なので、形を変えずに have to を置く。have to のうしろの動詞は原形なので、clean はそのままにする。",
                    "point": "しなければならないという義務は、must でも have to でも表せる。"
                },
                {
                    "unit": "U6",
                    "src": "There is a big tent in the park.",
                    "inst": "疑問文に直しなさい。",
                    "ans": "Is there a big tent in the park?",
                    "exp": "There is 〜 の疑問文は、be動詞の is を there の前に出して Is there 〜? の形にする。do や does は使わない。答えるときは Yes, there is. / No, there is not. のように there を残すのが特徴。",
                    "point": "There is の文の疑問文は、is を there の前に出して作る。"
                },
                {
                    "unit": "U9",
                    "src": "Our school gave the students new raincoats.",
                    "inst": "ほぼ同じ意味の文に直しなさい。Our school で始め、to を使うこと。",
                    "ans": "Our school gave new raincoats to the students.",
                    "exp": "give のあとに人と物がこの順で並ぶ文は、物を先に出して人の前に to を置く形に書きかえられる。この to を落とすと、だれに渡したのかが分からなくなる。buy や make のなかまは to ではなく for を使うので、動詞ごとに覚えておくとよい。",
                    "point": "〈give ＋ 人 ＋ 物〉は、物を先に置いて〈物 ＋ to ＋ 人〉にできる。"
                },
                {
                    "unit": "U10",
                    "src": "Ryo sang well at the school festival.",
                    "inst": "than Miki を加えて、Miki とくらべる文に直しなさい。",
                    "ans": "Ryo sang better than Miki at the school festival.",
                    "accept": [
                        "Ryo sang better than Miki did at the school festival.",
                        "Ryo sang better at the school festival than Miki.",
                        "Ryo sang better at the school festival than Miki did."
                    ],
                    "exp": "well の比較の形は more well ではなく better という特別な形になる。good をくらべるときも同じ better を使うので、形が変わる心配はない。ここでは well を better にして than Miki を続ける。",
                    "point": "good と well の比較級はどちらも better という特別な形になる。"
                },
                {
                    "unit": "U11",
                    "src": "Many people from our town visit our school festival.",
                    "inst": "されるという意味の文に直しなさい。Our school festival で始めなさい。",
                    "ans": "Our school festival is visited by many people from our town.",
                    "exp": "もとの文の目的語 our school festival をそのまま主語の位置に置き、動詞を is visited に変える。だれがするのかを言いたいときは by を付けて文のうしろに回す。主語が単数なので be動詞は is を選ぶ。",
                    "point": "能動の文を受け身にすると、もとの目的語が主語の位置に移る。"
                }
            ]
        },
        {
            "no": 5,
            "kind": "trans",
            "pt": 4,
            "title": "英作文",
            "inst": "次の日本語を英語に直せ。",
            "items": [
                {
                    "unit": "U2",
                    "ja": "ヒロはそのとき、レストランでカレーを食べていました。",
                    "model": "Hiro was eating curry at the restaurant then.",
                    "alts": [
                        "Hiro was having curry at the restaurant at that time."
                    ],
                    "elements": [
                        [
                            "「〜していました」を〈be動詞の過去形 ＋ -ing〉で表せている",
                            1
                        ],
                        [
                            "主語が一人なので be動詞が was になっている",
                            1
                        ],
                        [
                            "「レストランでカレーを食べる」という内容が表せている",
                            1
                        ],
                        [
                            "「そのとき」にあたる語（then / at that time）が入っている",
                            1
                        ]
                    ],
                    "exp": "「〜していました」は過去のある時点で続いていた動作なので、be動詞の過去形と -ing 形を組み合わせて表す。主語 Hiro は一人だから was を選び、were にはしない。ate と一語の過去形にすると一回で終わった話になり、続いていた感じが消える。",
                    "point": "その時進行中だった動作は、主語に合う was か were に -ing をそえて表す"
                },
                {
                    "unit": "U7",
                    "ja": "カナは昼食にサンドイッチを注文したいと思っています。",
                    "model": "Kana wants to order a sandwich for lunch.",
                    "alts": [
                        "For lunch, Kana wants to order a sandwich.",
                        "Kana would like to order a sandwich for lunch."
                    ],
                    "elements": [
                        [
                            "「〜したい」を〈want ＋ to ＋ 動詞の原形〉などの形で表せている",
                            1
                        ],
                        [
                            "主語が三人称単数であることに動詞の形が合っている（wants など。would like を使ったときはそのままでよい）",
                            1
                        ],
                        [
                            "「サンドイッチを注文する」という内容が表せている",
                            1
                        ],
                        [
                            "「昼食に」という意味が入っている",
                            1
                        ]
                    ],
                    "exp": "want は「ほしい」という意味だが、すぐうしろに to ＋ 動詞の原形を続けると「〜したい」を表せる。to のあとは必ず原形なので orders や ordering にはしない。主語 Kana は三人称単数だから wants にする点も忘れやすい。",
                    "point": "「〜したい」は want のあとを to ＋ 動詞の原形にして言い表す"
                },
                {
                    "unit": "U4",
                    "ja": "メニューを見せてくれませんか。",
                    "model": "Can you show me the menu?",
                    "alts": [
                        "Could you show me the menu?",
                        "Can you show the menu to me?"
                    ],
                    "elements": [
                        [
                            "「〜してくれませんか」を Can you 〜? の形でたずねられている",
                            1
                        ],
                        [
                            "Can you のあとが動詞の原形になっている",
                            1
                        ],
                        [
                            "「メニューを見せる」という内容が表せている",
                            1
                        ],
                        [
                            "だれに見せるのか（私に）が示せている",
                            1
                        ]
                    ],
                    "exp": "人に何かを頼むときは Can you ＋ 動詞の原形 ＋ ? の形にする。Can のあとは必ず原形なので shows や showing にはしない。ていねいに言うなら Could you 〜? にする。文の終わりのクエスチョンマークを忘れない。",
                    "point": "人に何かを頼むときは Can you ＋ 動詞の原形 ＋ ? の形にする。"
                }
            ]
        }
    ]
}
