# -*- coding: utf-8 -*-
"""第2部 実力の確認（定期テスト・実力テストの標準〜応用レベル）37問／100点

★このファイルは assemble.py が生成する。手で直してよいが、
  再生成すると上書きされる（作問JSON側も直すこと）。
"""

PART = {
    "no": 2,
    "level": "実力の確認",
    "univ": "定期テスト・実力テストの標準〜応用レベル",
    "aim": "第1部と同じ範囲を、少し長い文で問い直す部です。一文の中で決めることが二つになります。ここが8割取れたら第3部へ進んでください。",
    "time": 45,
    "total": 100,
    "steps": [
        "45分を計って解く。",
        "一文を読んだら、まず主語と動詞を指で押さえてから空所を見る。",
        "間違えた問題が12の単元のどれだったかを、解答解説編の一覧で必ず確かめる。"
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
                    "stem": "The station and the small airport (        ) very crowded last Sunday morning.",
                    "choices": [
                        "was",
                        "were",
                        "are",
                        "is"
                    ],
                    "ans": 1,
                    "exp": "station と airport の2つが主語なので複数のあつかいになり、be動詞の過去形は were を使う。was は主語が1つのときの形なので合わない。last Sunday morning と過去を表す語があるため、現在形の are と is も入らない。",
                    "point": "be動詞の過去形は、主語が単数なら was、複数なら were を使う"
                },
                {
                    "unit": "U2",
                    "stem": "Saki (        ) the way to the airport station, so she did not ask anyone.",
                    "choices": [
                        "knew",
                        "was knowing",
                        "knows",
                        "is knowing"
                    ],
                    "ans": 0,
                    "exp": "know は「知っている」という状態を表す動詞なので、was knowing のように -ing の形にはしない。後ろの did not ask から過去の話だとわかるので、現在形の knows と is knowing も合わない。正しくは過去形の knew。",
                    "point": "know のように状態を表す動詞は -ing の形にせず、そのまま使う"
                },
                {
                    "unit": "U4",
                    "stem": "Saki, you (        ) run on the platform, because you may hurt other people.",
                    "choices": [
                        "don't have to",
                        "must not",
                        "don't have",
                        "must have to"
                    ],
                    "ans": 1,
                    "exp": "人にけがをさせるかもしれないから禁止する場面なので must not が入る。don't have to は「その必要はない」という意味で、正反対になってしまう。don't have は to が抜けているので、うしろに原形 run を続けられない。must have to は助動詞のあとに義務の言い方を重ねた形で、ここでは意味が通らない。",
                    "point": "must not は禁止、don't have to は不要を表し、意味が逆になる"
                },
                {
                    "unit": "U5",
                    "stem": "Saki will take a taxi (        ) the plane arrives late tonight.",
                    "choices": [
                        "that",
                        "so",
                        "of",
                        "if"
                    ],
                    "ans": 3,
                    "exp": "「もし〜なら」という条件は if でつなぐ。if の後ろは未来のことでも arrives と現在形にするのがきまり。that は後ろの文をつなぐ働きが違い、of は前置詞なので文を続けられない。so は「だから」で前後の意味が通らない。",
                    "point": "もし〜ならという条件は if で表し、その中は未来でも現在形にする"
                },
                {
                    "unit": "U7",
                    "stem": "My host family was very glad (        ) us again after the long flight.",
                    "choices": [
                        "seeing",
                        "to see",
                        "see",
                        "to seeing"
                    ],
                    "ans": 1,
                    "exp": "glad のように気持ちを表す語の後ろでは、その気持ちの理由を to ＋ 動詞の原形で表す。seeing や to seeing はこの位置に置けない。see だけを続ける形も誤り。happy や sad の後ろでも同じ形が使える。",
                    "point": "気持ちを表す語の後ろに to ＋ 原形を置くと、その理由になる"
                },
                {
                    "unit": "U8",
                    "stem": "Daiki is very good at (        ) maps, so we never get lost in Tokyo.",
                    "choices": [
                        "reading",
                        "read",
                        "to read",
                        "reads"
                    ],
                    "ans": 0,
                    "exp": "at は前置詞なので、後ろに動詞をそのままの形では置けない。動詞を -ing にして reading とすると名詞のはたらきになり、前置詞の後ろに続けられる。read と reads と to read はどれもこの位置には入らない形。",
                    "point": "得意なことを言う be good at では、続く動詞を -ing に変える"
                },
                {
                    "unit": "U9",
                    "stem": "The people in this town (        ) this old blue train the Sky Runner.",
                    "choices": [
                        "say",
                        "talk",
                        "call",
                        "speak"
                    ],
                    "ans": 2,
                    "exp": "「A を B と呼ぶ」というときは、call の後ろに呼ぶものとその名前を続けて並べる。say は後ろに2つの語をこの順で並べられない。talk と speak もこの語順を作れないので誤り。呼び名には the が付くこともある。",
                    "point": "A を B と呼ぶときは call の後ろに A、B の順で2語を並べる"
                },
                {
                    "unit": "U10",
                    "stem": "For young travelers, this airport bus is (        ) than the local train.",
                    "choices": [
                        "popularer",
                        "most popular",
                        "more popularer",
                        "more popular"
                    ],
                    "ans": 3,
                    "exp": "popular はつづりの長い形容詞なので -er を付けず、前に more を置いて more popular とする。popularer や more popularer という形は英語にない。most popular は一番を表す形で than とは使わない。",
                    "point": "つづりが長い形容詞は more をその前に置き、than で相手を示す"
                },
                {
                    "unit": "U11",
                    "stem": "(        ) these old maps sold at the shop near the station gate?",
                    "choices": [
                        "Are",
                        "Is",
                        "Do",
                        "Does"
                    ],
                    "ans": 0,
                    "exp": "受け身の疑問文は be動詞を主語の前に出す。主語 these old maps は複数なので Are。Is は単数のときの形。地図は「売られる」側なので〈be動詞 ＋ 過去分詞〉になり、Do や Does では過去分詞 sold を続けられない。",
                    "point": "受け身の疑問文は be動詞を主語の前に出し、過去分詞はそのまま残す"
                },
                {
                    "unit": "U12",
                    "stem": "The guide showed Saki (        ) the tickets at the small station.",
                    "choices": [
                        "where to buy",
                        "where buying",
                        "to where buy",
                        "where buy"
                    ],
                    "ans": 0,
                    "exp": "〈動詞 ＋ 人 ＋ 疑問詞 ＋ to ＋ 原形〉の形で「人にどこで〜すればよいかを示す」を表す。where のあとは to ＋ 原形なので where to buy。where buy は to が足りず、to where buy は語順が逆。where buying は to ＋ 原形の形になっていない。",
                    "point": "〈動詞 ＋ 人 ＋ where ＋ to ＋ 原形〉で「どこで〜すればよいか」を示す。"
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
                    "stem": "Rina (   ) the violin in her room for two hours last night.",
                    "ans": "practiced",
                    "given": "practice",
                    "exp": "last night は過去を表す語句なので、動詞は過去形にする。practice は e で終わるので d だけを付けて practiced とする規則動詞である。現在形のまま practices としてしまう間違いが多いので、文のどこかに過去を示す語がないかを先に探す習慣をつけよう。",
                    "point": "last night のような過去を表す語句があるとき、動詞は過去形にする。"
                },
                {
                    "unit": "U3",
                    "stem": "Kota and Rina ( a ) going to sing together at the school concert.",
                    "ans": "are",
                    "given": "be",
                    "hint": "a",
                    "exp": "be going to の be は主語によって形が変わる。主語が Kota and Rina で複数だから are を使う。am や is は単数の主語のときの形なので入らない。going to のあとの動詞はいつも原形のままである点もあわせて確かめておこう。",
                    "point": "be going to の be は主語に合わせて is や are に変える。"
                },
                {
                    "unit": "U4",
                    "stem": "Kota, you ( s ) bring your own guitar to school tomorrow, because all the school guitars are broken.",
                    "ans": "should",
                    "hint": "s",
                    "exp": "「〜したほうがよい」と助言するときは should を使い、うしろは動詞の原形にする。学校のギターが全部こわれているので、自分のギターを持ってくるほうがよい、という流れになる。must ほど強くなく、相手に決めさせる言い方。",
                    "point": "相手に助言するときは should を動詞の原形の前に置く。"
                },
                {
                    "unit": "U6",
                    "stem": "There ( i ) piano in this small room, so we practice in the music room.",
                    "ans": "is no",
                    "hint": "i",
                    "accept": [
                        "isn't a",
                        "is not a"
                    ],
                    "exp": "「〜がない」は There is no のあとに名詞を続けて表す。後半の「だから音楽室で練習する」が、ここにピアノが無いことを示す手がかりになる。今のことなので was ではなく is、piano は1つなので are にもしない。",
                    "point": "「〜がない」は There is no のあとに名詞を続けて表す。"
                },
                {
                    "unit": "U7",
                    "stem": "Our band has many songs ( t ) play at the festival next month.",
                    "ans": "to",
                    "hint": "t",
                    "exp": "songs のうしろに to ＋ 動詞の原形を置くと、「演奏するための歌」と前の名詞をうしろから説明できる。この to のあとは必ず原形なので plays や playing にはしない。for playing のように前置詞を使う言い方とは組み立てが違う。",
                    "point": "名詞のうしろに to ＋ 動詞の原形を置くと、「〜するための」と前の名詞を説明できる。"
                },
                {
                    "unit": "U8",
                    "stem": "How about (   ) a new poster for the school concert this year?",
                    "ans": "making",
                    "given": "make",
                    "exp": "How about のうしろに動詞を続けるときは -ing の形にする。about は前置詞なので、原形の make や to make は置けない。「〜しませんか」と相手をさそう言い方で、Why don't we 〜? とほぼ同じ意味。",
                    "point": "How about のあとの動詞は -ing 形にして、相手を誘う言い方になる。"
                },
                {
                    "unit": "U9",
                    "stem": "Rina's mother ( m ) her a new dress for the chorus contest last week.",
                    "ans": "made",
                    "given": "make",
                    "hint": "m",
                    "exp": "〈make ＋ 人 ＋ 物〉で「人に物を作ってあげる」を表し、相手を先、作る物をあとに置く。last week があるので過去形 made にする。make の過去形は形が変わるので、maked とは書かない。",
                    "point": "〈make ＋ 人 ＋ 物〉で「人に物を作ってあげる」を表し、相手を先に置く。"
                },
                {
                    "unit": "U10",
                    "stem": "Kota plays the guitar the best ( o ) all the band members.",
                    "ans": "of",
                    "hint": "o",
                    "exp": "「〜の中で」を表す語は、後ろに来る語で決まる。all the band members のように複数を表す語の前では of を使う。in は my class や Japan のような場所や範囲を表す単数の語の前で使う。ここは members が複数なので of。",
                    "point": "the -est のあとの「〜の中で」は、複数を表す語の前なら of。"
                },
                {
                    "unit": "U11",
                    "stem": "That famous song ( w ) sung at the school concert tomorrow.",
                    "ans": "will be",
                    "hint": "w",
                    "exp": "tomorrow とあるので、これから「〜される」と言う文。〈will ＋ be ＋ 過去分詞〉の形にするので、空所には will be が入る。will sung のように be をとばしたり、is にして今のことにしたりはできない。だれが歌うかを言う必要がないときは、by 〜 を書かなくてよい。",
                    "point": "これから「〜される」と言うときは、〈will ＋ be ＋ 過去分詞〉の形にする。"
                },
                {
                    "unit": "U10",
                    "stem": "This guitar is (   ) than mine, so Kota can carry it to school easily.",
                    "ans": "lighter",
                    "given": "light",
                    "exp": "2つを比べて「より〜だ」と言うときは、形容詞に -er を付けて than を続ける。light は短い語なので more light とは言わず lighter にする。than のあとには比べる相手を置く。",
                    "point": "短い形容詞は -er を付けて than を続け、2つを比べる。"
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
                    "unit": "U2",
                    "ja": "私たちが自分たちの本を読んでいる間に、先生が古い新聞を何部か持ってきてくれました。",
                    "frame": "[ ], the teacher brought us some old newspapers.",
                    "tokens": [
                        "reading",
                        "we",
                        "our",
                        "While",
                        "books",
                        "were"
                    ],
                    "ans": "While we were reading our books",
                    "exp": "while は〈〜している間に〉という意味で、あとに〈主語＋be動詞の過去形＋動詞のing形〉を続ける。主語 we に合う過去形は were なので were reading となる。その最中に起きた出来事を表す後半は過去形 brought だ。",
                    "point": "while のあとは〈主語＋be動詞の過去＋動詞のing〉で進行中の場面を表す"
                },
                {
                    "unit": "U4",
                    "ja": "これらの重い本を読書室まで運びましょうか。",
                    "frame": "[ ] to the reading room?",
                    "tokens": [
                        "heavy",
                        "carry",
                        "Shall",
                        "books",
                        "I",
                        "these"
                    ],
                    "ans": "Shall I carry these heavy books",
                    "exp": "Shall I 〜? は相手のために〈〜しましょうか〉と自分から申し出るときの言い方だ。I のすぐあとには動詞の原形 carry を置く。Will you 〜? だと相手に頼む意味になり、向きが逆になるので注意しよう。",
                    "point": "Shall I 〜? は自分から〈〜しましょうか〉と申し出るときの形"
                },
                {
                    "unit": "U5",
                    "ja": "ユナは、ソウタが市の図書館から歴史の本を5冊借りたことを知っています。",
                    "frame": "Yuna knows [ ] from the city library.",
                    "tokens": [
                        "books",
                        "five",
                        "Sota",
                        "history",
                        "borrowed"
                    ],
                    "ans": "Sota borrowed five history books",
                    "exp": "knows のあとには〈ソウタが〜した〉という文がそのまま続く。本来はその前に that が入るが、話し言葉でも書き言葉でもよく省かれ、省いても意味は変わらない。borrow は「自分が借りる」、lend は「相手に貸す」という意味のちがいもあわせて覚えておこう。",
                    "point": "文と文をつなぐ that は know などのあとではよく省略される"
                },
                {
                    "unit": "U6",
                    "ja": "窓のそばの読書コーナーには絵本が何冊ありますか。",
                    "frame": "[ ] in the reading corner near the window?",
                    "tokens": [
                        "books",
                        "there",
                        "How",
                        "are",
                        "picture",
                        "many"
                    ],
                    "ans": "How many picture books are there",
                    "exp": "数をたずねるときは How many のあとに複数形の名詞 picture books を置き、続けて are there? とする。もとの There are 〜. の疑問文なので are が there の前に出る。名詞を単数の book にしないよう気をつけよう。",
                    "point": "How many ＋ 複数名詞 のあとに are there? を置いて数をたずねる"
                },
                {
                    "unit": "U7",
                    "ja": "私たちのクラブは学校新聞に新しいページを作ることに決めました。",
                    "frame": "Our club [ ] for the school newspaper.",
                    "tokens": [
                        "make",
                        "new",
                        "decided",
                        "page",
                        "a",
                        "to"
                    ],
                    "ans": "decided to make a new page",
                    "exp": "decide は〈〜することに決める〉という意味で、決めた内容を〈to ＋ 動詞の原形〉で表す。ここでは to make のかたまりが decided の目的語だ。to のあとは必ず原形なので made や making にはしない。",
                    "point": "decide の目的語になる〈to ＋ 動詞の原形〉は〈〜すること〉の意味"
                },
                {
                    "unit": "U9",
                    "ja": "ソウタは先週末、本屋でユナに新しい辞書を買ってあげました。",
                    "frame": "Sota [ ] at the bookshop last weekend.",
                    "tokens": [
                        "for",
                        "new",
                        "bought",
                        "Yuna",
                        "dictionary",
                        "a"
                    ],
                    "ans": "bought a new dictionary for Yuna",
                    "exp": "buy を使って〈だれかに買ってあげる〉と言うときは、買った物を先に置き、相手の前に for を入れる。give のように to ではなく for を使う動詞なので区別して覚えよう。bought は buy の過去形だ。",
                    "point": "〈buy ＋ 物 ＋ for ＋ 人〉の形では人の前に for が必要になる"
                },
                {
                    "unit": "U11",
                    "ja": "この本はやさしい英語で書かれていなかったので、ソウタはそれを理解できませんでした。",
                    "frame": "This book [ ], so Sota could not understand it.",
                    "tokens": [
                        "written",
                        "easy",
                        "was",
                        "English",
                        "not",
                        "in"
                    ],
                    "ans": "was not written in easy English",
                    "exp": "〈be動詞＋過去分詞〉で〈〜される〉を表し、否定にするときは be動詞のすぐあとに not を入れる。主語 this book は単数で過去のことなので was not written となる。write の過去分詞は written だ。",
                    "point": "受け身を否定するときは be動詞のすぐあとに not を置く"
                },
                {
                    "unit": "U8",
                    "ja": "英語で長い物語を読むことは簡単ではありません。",
                    "frame": "[ ] easy.",
                    "tokens": [
                        "is",
                        "English",
                        "Reading",
                        "not",
                        "a",
                        "in",
                        "long",
                        "story"
                    ],
                    "ans": "Reading a long story in English is not",
                    "exp": "動詞をそのまま主語にすることはできないので、read を -ing の形にして Reading a long story in English までを一つの主語のかたまりにする。かたまり全体を一つのものとして扱うので、be動詞は are ではなく is。",
                    "point": "動詞の -ing 形は、そのまとまり全体を文の主語にできる。"
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
                    "unit": "U3",
                    "src": "Mao will feed the rabbits at the animal park next Sunday.",
                    "inst": "ほぼ同じ意味になるように、be going to を使った文に書き換えなさい。",
                    "ans": "Mao is going to feed the rabbits at the animal park next Sunday.",
                    "exp": "will も be going to も、これからすることを言うときに使う。be going to のあとは動詞の原形なので feed はそのまま。主語 Mao は三人称単数だから be は is を選び、is going to feed と並べる。to を落とさないこと。",
                    "point": "未来を表す will は、〈be going to ＋ 動詞の原形〉に置きかえて言える"
                },
                {
                    "unit": "U5",
                    "src": "The baby panda was very cute, so a lot of people visited the zoo.",
                    "inst": "ほぼ同じ意味になるように、because を使って A lot of で始まる文に書き換えなさい。",
                    "ans": "A lot of people visited the zoo because the baby panda was very cute.",
                    "exp": "so は前に原因、後ろに結果がくる。ここでは「赤ちゃんパンダがとてもかわいかった」が原因、「たくさんの人が動物園を訪れた」が結果。because は後ろに原因を置くので、二つのまとまりを前後入れかえてつなぐ。",
                    "point": "so の前後を入れかえ、原因の部分を because で導くと同じ内容になる"
                },
                {
                    "unit": "U8",
                    "src": "Jun likes to take pictures of the elephants and the lions.",
                    "inst": "ほぼ同じ意味になるように、動詞の -ing 形を使った文に書き換えなさい。",
                    "ans": "Jun likes taking pictures of the elephants and the lions.",
                    "exp": "like のあとには to ＋ 動詞の原形も、動詞の -ing 形も置ける。どちらも「〜するのが好きだ」という意味になる。take は最後の e を取って taking とつづる点に注意。takeing と書いたり、to taking のように to を残したりしてはいけない。",
                    "point": "like のあとの動詞は -ing 形にでき、to ＋ 原形のときと同じ意味を表す"
                },
                {
                    "unit": "U9",
                    "src": "The zookeeper taught Mao the names of many African animals.",
                    "inst": "ほぼ同じ意味になるように、to を使った文に書き換えなさい。",
                    "ans": "The zookeeper taught the names of many African animals to Mao.",
                    "exp": "teach は人を先に置いて〈teach ＋ 人 ＋ 物〉と言えるが、物を先に置くときは相手を表す語の前に to が要る。to をつけ忘れると相手が伝わらない。for にしないこと。長いまとまりを先に、相手を最後に置く語順に慣れよう。",
                    "point": "teach は〈人 ＋ 物〉の順でも〈物 ＋ to ＋ 人〉の順でも同じ内容を表せる"
                },
                {
                    "unit": "U10",
                    "src": "My dog Momo is not as big as the tiger at the zoo.",
                    "inst": "ほぼ同じ意味になるように、The tiger で始まる文に書き換えなさい。",
                    "ans": "The tiger at the zoo is bigger than my dog Momo.",
                    "accept": [
                        "The tiger at the zoo is larger than my dog Momo."
                    ],
                    "exp": "not as ... as ... は「…ほど〜ではない」。モモはトラほど大きくない、つまりトラのほうが大きいということ。くらべる二つを入れかえ、big の g を重ねて bigger とし、than を続ける。as を残したままにしない。",
                    "point": "「A は B ほど〜でない」は、A と B を入れかえた -er than の文で言える"
                },
                {
                    "unit": "U11",
                    "src": "The zookeeper cleaned the monkey cages early this morning.",
                    "inst": "ほぼ同じ意味になるように、The monkey cages で始まる受け身の文に書き換えなさい。",
                    "ans": "The monkey cages were cleaned early this morning by the zookeeper.",
                    "accept": [
                        "The monkey cages were cleaned by the zookeeper early this morning."
                    ],
                    "exp": "もとの文の目的語 the monkey cages をそのまま主語に立て、動詞を〈be動詞 ＋ 過去分詞〉に変える。主語は複数で時は過去だから be は were、clean の過去分詞は cleaned。動作をした人は by のあとに置く。",
                    "point": "もとの目的語を主語に立て、動詞を be動詞 ＋ 過去分詞 に変えると受け身になる"
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
                    "unit": "U3",
                    "ja": "ナオとケンタは明日、家族のためにお弁当を作るつもりです。（be going to を使って）",
                    "model": "Nao and Kenta are going to make box lunches for their family tomorrow.",
                    "alts": [
                        "Nao and Kenta are going to cook box lunches for their family tomorrow.",
                        "Nao and Kenta are going to make box lunches tomorrow for their family."
                    ],
                    "elements": [
                        [
                            "「〜するつもりです」という予定を〈be going to ＋ 動詞の原形〉で表せている",
                            1
                        ],
                        [
                            "主語が2人なので be動詞が are になっている",
                            1
                        ],
                        [
                            "「家族のために」という意味が for their family などで入っている",
                            1
                        ],
                        [
                            "「お弁当を作る」という内容と「明日」がそろっている",
                            1
                        ]
                    ],
                    "exp": "これからしようと決めていることは〈be going to ＋ 動詞の原形〉で表す。主語が2人なので be動詞は are になり、is にはしない。to のあとは必ず原形だから makes や making とは書かず、going を goes に変えるのも誤り。",
                    "point": "これからやろうと決めていることは be going to ＋ 動詞の原形で言い表す"
                },
                {
                    "unit": "U6",
                    "ja": "台所のテーブルの上に、卵が6個とトマトが2個あります。",
                    "model": "There are six eggs and two tomatoes on the kitchen table.",
                    "alts": [
                        "There are two tomatoes and six eggs on the kitchen table.",
                        "There are six eggs and two tomatoes on the table in the kitchen."
                    ],
                    "elements": [
                        [
                            "「〜があります」を There で始まる存在の文で表せている",
                            1
                        ],
                        [
                            "あとに続く名詞が複数なので be動詞が are になっている",
                            1
                        ],
                        [
                            "卵6個とトマト2個という数と、名詞の複数形が正しい",
                            1
                        ],
                        [
                            "「台所のテーブルの上に」という場所が表せている",
                            1
                        ]
                    ],
                    "exp": "ものが存在すると伝えるときは There is / There are で文を始め、あとに置く名詞の数で be動詞を決める。卵もトマトも2つ以上だから are を使い、eggs, tomatoes と複数形にする。場所を表す語句は文の終わりにそえる。",
                    "point": "数えられるものが2つ以上あると言うときは There are ＋ 複数形で始める"
                },
                {
                    "unit": "U10",
                    "ja": "ケンタのチャーハンは私のものより辛いですが、とてもおいしいです。",
                    "model": "Kenta's fried rice is spicier than mine, but it is really good.",
                    "alts": [
                        "Kenta's fried rice is hotter than mine, but it is really delicious.",
                        "Kenta's fried rice is spicier than my fried rice, but it tastes very good."
                    ],
                    "elements": [
                        [
                            "形容詞を比較の形にして「より辛い」を表せている",
                            1
                        ],
                        [
                            "比べる相手の前に than を置けている",
                            1
                        ],
                        [
                            "「私のもの」にあたる語（mine など）で比べる相手が示せている",
                            1
                        ],
                        [
                            "「とてもおいしい」という後半の内容がつながっている",
                            1
                        ]
                    ],
                    "exp": "2つを比べて程度が上だと言うときは、形容詞を比較の形にして than を続ける。spicy は子音字と y で終わるので、y を i に変えて spicier とし、more spicy とは言わない。than のあとは mine と一語でも言える。",
                    "point": "比較の文では形容詞を -er の形にして、比べる相手の前に than を置く"
                }
            ]
        }
    ]
}
