# -*- coding: utf-8 -*-
"""第3部 総合仕上げ（学年末の実力テスト／高校入試の入り口レベル）34問／100点

★このファイルは assemble.py が生成する。手で直してよいが、
  再生成すると上書きされる（作問JSON側も直すこと）。
"""

PART = {
    "no": 3,
    "level": "総合仕上げ",
    "univ": "学年末の実力テスト／高校入試の入り口レベル",
    "aim": "一文の中に二つ以上の文法が入ります。読む力と書く力を同時に使う部です。ここで8割取れたら、中2の文法は仕上がったと考えてよいです。",
    "time": 50,
    "total": 100,
    "steps": [
        "50分を計って解く。",
        "一文の中で決めることが二つ以上ある。二つとも合って正解になる。",
        "8割に届かなかった単元は、第1部の同じ単元の問題をもう一度解き直す。"
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
                    "stem": "Last Friday Mei (        ) some water in a small pot for a simple science experiment.",
                    "choices": [
                        "boiled",
                        "boils",
                        "is boiling",
                        "boil"
                    ],
                    "ans": 0,
                    "exp": "Last Friday という過去を表す語句があるので、動詞は過去形の boiled にする。boils と boil は現在のことを表す形なので、終わった話には使えない。is boiling は今まさに進行中の意味になり合わない。時を表す語句を先にさがすとよい。",
                    "point": "文の中にある時を表す語句を手がかりに、動詞を現在形か過去形かに決める。"
                },
                {
                    "unit": "U3",
                    "stem": "The science club will use the big telescope tomorrow night if the sky (        ) clear.",
                    "choices": [
                        "is",
                        "will be",
                        "are",
                        "be"
                    ],
                    "ans": 0,
                    "exp": "明日の夜のことでも、if で始まるまとまりの中の動詞は現在形にする決まりなので is が正しい。will be はこのまとまりの中では使えない。are は sky が単数なので合わない。be だけの形も主語のあとには置けない。まとまりの外の will use はそのままでよい。",
                    "point": "if や when が作るまとまりの中では、未来のことを言うときもwill を使わず現在形で書く。"
                },
                {
                    "unit": "U4",
                    "stem": "Last Saturday Haruto (        ) clean the science room alone because it was very dirty.",
                    "choices": [
                        "had to",
                        "must",
                        "has to",
                        "have to"
                    ],
                    "ans": 0,
                    "exp": "Last Saturday という過去のできごとなので、had to を使う。must には過去を表す形がないため、そのままでは過去の意味にならない。has to と have to は今のことを表す形なので合わない。to のあとは形を変えない wash になる。",
                    "point": "過去にしなければならなかったことは had to で表し、あとに原形を続ける。"
                },
                {
                    "unit": "U5",
                    "stem": "Mei wrote the results in her notebook (        ) the experiment finished, so she did not forget them.",
                    "choices": [
                        "after",
                        "before",
                        "during",
                        "because of"
                    ],
                    "ans": 0,
                    "exp": "実験が終わって結果が出たあとでなければ結果は書けないので after が合う。before にすると、まだ出ていない結果を書いたことになる。during と because of は前置詞なので、うしろに主語と動詞のある文を続けられない。",
                    "point": "before と after はうしろに文を続けられるが、during と because of は続けられない。"
                },
                {
                    "unit": "U6",
                    "stem": "(        ) on the shelf by the door, and Mei uses it in every science class.",
                    "choices": [
                        "The new camera is",
                        "There is the new camera",
                        "There are the new camera",
                        "There was the new camera"
                    ],
                    "ans": 0,
                    "exp": "the が付いた the new camera のように、どれのことか決まっている物は There is 〜 の文の主語にしない。その物を主語にして The new camera is 〜 と言う。There is 〜 は、相手がまだ知らないものを新しく持ち出すときの言い方。",
                    "point": "the や my が付く物を言うときは、There is ではなくその物を主語にする。"
                },
                {
                    "unit": "U7",
                    "stem": "Mei was looking for a good place (        ) the stars, and Ms. Ito helped her.",
                    "choices": [
                        "to watch",
                        "watch",
                        "watched",
                        "watches"
                    ],
                    "ans": 0,
                    "exp": "to ＋ 原形には「〜すること」「〜するための」「〜するために」の3つのはたらきがある。ここは place がどんな場所かを後ろから説明する「〜するための」なので to watch が正しい。watch、watched、watches は名詞のすぐあとに続けられない。",
                    "point": "名詞のすぐ後ろに置く to ＋ 原形は、その名詞がどんなものかを説明する。"
                },
                {
                    "unit": "U8",
                    "stem": "Mei learned the names of many stars by (        ) at the night sky from her bedroom window.",
                    "choices": [
                        "looking",
                        "look",
                        "looks",
                        "to look"
                    ],
                    "ans": 0,
                    "exp": "by や without などの前置詞のあとに動詞を続けるときは、-ing 形にして名詞と同じはたらきをさせる。だから looking が正しい。look と looks は前置詞のすぐあとには置けず、to look もこの位置では使えない。by ＋ -ing は手段を表す。",
                    "point": "前置詞のあとに動詞を置くときは、-ing 形にして名詞のはたらきをさせる。"
                },
                {
                    "unit": "U2",
                    "stem": "Haruto (        ) at the stars when the rain started, because he was reading in his room.",
                    "choices": [
                        "was not looking",
                        "were not looking",
                        "did not looking",
                        "not was looking"
                    ],
                    "ans": 0,
                    "exp": "過去のある時に続いていた動作を打ち消すので、〈was / were ＋ not ＋ -ing〉にする。主語 Haruto は一人なので was not looking。were は複数の主語に使う。did not のあとは原形なので looking と並べられず、not was の語順も誤り。",
                    "point": "過去に進行中だった動作を打ち消すときは、was / were のすぐあとに not を置く。"
                },
                {
                    "unit": "U11",
                    "stem": "This small telescope is made (        ) plastic, so Haruto can carry it in his bag easily.",
                    "choices": [
                        "of",
                        "by",
                        "to",
                        "in"
                    ],
                    "ans": 0,
                    "exp": "何でできているかを言うときは be made of の形を使うので of が正しい。by は「〜によって」と作った人などを示す形で、材料には使えない。in は作られた場所を言う形、to はこの言い方に合わない。受け身には by 以外の前置詞をとる形もある。",
                    "point": "受け身のあとに続く前置詞は by だけではなく、of や with を使う形もある。"
                },
                {
                    "unit": "U12",
                    "stem": "Ms. Ito told Haruto (        ) with the empty bottles, and he washed them at once.",
                    "choices": [
                        "what to do",
                        "what doing",
                        "to what do",
                        "what do"
                    ],
                    "ans": 0,
                    "exp": "what と to ＋ 原形を並べると「何を〜すればよいか」という一つのかたまりになり、told のあとの内容として置ける。what doing は to ＋ 原形の形になっていない。to what do は語順が逆で、what do は to が足りない。",
                    "point": "〈動詞 ＋ 人 ＋ what ＋ to ＋ 原形〉で「何をすればよいかを伝える」を表す。"
                }
            ]
        },
        {
            "no": 2,
            "kind": "error",
            "pt": 3,
            "title": "誤りの指摘と訂正",
            "inst": "次の各文には文法上の誤りが1か所ある。誤りを含む部分の記号を一つ選び、あわせて正しい形を書け。",
            "items": [
                {
                    "unit": "U1",
                    "stem": "{a} {b} {c} {d}?",
                    "parts": [
                        "Did Kaito and Airi",
                        "visited the old temple",
                        "near the river",
                        "during their school trip"
                    ],
                    "ans": 1,
                    "fix": "visited → visit",
                    "exp": "Did で始まる疑問文の動詞は、いつも原形にする。過去の意味は Did が受け持つので、visited だと過去が二重になる。ほかの三つの下線部は、前置詞も語順も正しく、直す必要はない。",
                    "point": "Did を使った疑問文の動詞は、過去形ではなく原形にする"
                },
                {
                    "unit": "U5",
                    "stem": "{a} {b} {c} {d}.",
                    "parts": [
                        "Kaito took many pictures",
                        "of the old temple",
                        "when he visits this city",
                        "with Airi and his family"
                    ],
                    "ans": 2,
                    "fix": "when he visits → when he visited",
                    "exp": "中心の文が took と過去形なので、when のあとの動詞も過去形 visited にそろえる。visits にすると今もくり返している習慣の話になり、過去のできごとを語る前半と時がずれる。ほかの三つの下線部は、前置詞も語順も正しく、直す必要はない。",
                    "point": "when でつないだ文の中の動詞も、中心の文と同じ時（現在か過去か）にそろえる"
                },
                {
                    "unit": "U6",
                    "stem": "{a} {b}, {c} {d}.",
                    "parts": [
                        "There is many shops",
                        "near the old temple",
                        "and Kaito often goes",
                        "shopping there with Airi"
                    ],
                    "ans": 0,
                    "fix": "There is → There are",
                    "exp": "There のあとの名詞が二つ以上なら be動詞は are、一つなら is。ここは shops なので There are が正しい形になる。ほかの三つの下線部は、前置詞も動詞の形も正しく、直す必要はない。",
                    "point": "There のあとに続く名詞が二つ以上なら are、一つなら is を選ぶ"
                },
                {
                    "unit": "U9",
                    "stem": "{a} {b} {c}, {d}.",
                    "parts": [
                        "Last weekend Kaito",
                        "showed the old pictures Airi",
                        "at the city festival",
                        "and she looked very happy"
                    ],
                    "ans": 1,
                    "fix": "showed the old pictures Airi → showed Airi the old pictures（showed the old pictures to Airi も可）",
                    "exp": "show は〈show ＋ 相手 ＋ 見せる物〉の順に並べる。物を先に置くなら showed the old pictures to Airi のように to が必要だ。to がないのに物が先に来ているのが誤りで、ほかの下線部は正しい形だ。相手を先に置かずに〈物 ＋ to ＋ 人〉の形にしてshowed the old pictures to Airi と直してもよい。",
                    "point": "show は〈相手 ＋ 物〉の順。物を先に置くなら、相手の前に to を付ける"
                },
                {
                    "unit": "U10",
                    "stem": "{a}, {b} {c} {d}.",
                    "parts": [
                        "The city has many old buildings",
                        "but Airi thinks",
                        "that this temple",
                        "is oldest of all"
                    ],
                    "ans": 3,
                    "fix": "is oldest → is the oldest",
                    "exp": "「いちばん〜だ」と言うときの -est には前に the を付け、is the oldest とする。the が付くと、多くの中で一つに決まる意味になる。ほかの三つの下線部は、語順も動詞の形もすべて正しい。",
                    "point": "「いちばん〜だ」と言うときは -est の前に the を付ける"
                },
                {
                    "unit": "U2",
                    "stem": "{a}, {b} {c} {d}.",
                    "parts": [
                        "When the festival started",
                        "Airi and Kaito",
                        "were having a map",
                        "of the old city"
                    ],
                    "ans": 2,
                    "fix": "were having → had",
                    "exp": "be動詞 ＋ -ing は、そのとき進行中の動作を表す形だ。have は「持っている」という状態を表す動詞なので、この形にはできない。過去の文なので had に直す。When the festival started は過去形で正しく、残りの二つも自然な形だ。",
                    "point": "「持っている」という意味の have は -ing の形にはしない"
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
                    "ja": "リクが浜辺で大きなカニを見つけたとき、私たちは昼ごはんを作っていました。",
                    "frame": "[ ] a big crab on the beach.",
                    "tokens": [
                        "Riku",
                        "cooking",
                        "when",
                        "were",
                        "found",
                        "We",
                        "lunch"
                    ],
                    "ans": "We were cooking lunch when Riku found",
                    "exp": "続いていた動作は were cooking のように be動詞の過去形と -ing で表し、その途中で起きた出来事は when のあとに過去形 found を置く。found は find の過去形。were を落として We cooking としないように気をつけよう。",
                    "point": "動作の最中は be動詞の過去形＋-ing、区切りの出来事は when 節に過去形で置く"
                },
                {
                    "unit": "U3",
                    "ja": "明日の夜、山で大きなキャンプファイヤーがあるでしょう。",
                    "frame": "[ ] in the mountains tomorrow night.",
                    "tokens": [
                        "big",
                        "be",
                        "There",
                        "campfire",
                        "will",
                        "a"
                    ],
                    "ans": "There will be a big campfire",
                    "exp": "未来のことでも There で始める形は変わらず、There will be ＋ 名詞 の順に並べる。will のあとは必ず原形なので will is とはしない。a big campfire のように数えられる名詞でも be は原形のままでよい。",
                    "point": "これから〜がある は There will be ＋ 名詞。be は原形のまま変えない"
                },
                {
                    "unit": "U4",
                    "ja": "すみません、この浜辺で私たち家族の写真を撮っていただけませんか。",
                    "frame": "Excuse me, [ ] of our family on this beach?",
                    "tokens": [
                        "take",
                        "you",
                        "picture",
                        "could",
                        "a"
                    ],
                    "ans": "could you take a picture",
                    "exp": "Can you 〜? よりていねいに頼むときは Could you 〜? を使い、you のあとは動詞の原形 take を置く。 は you と動詞の間に入れると自然。Could you to take のように to を入れてはいけない。",
                    "point": "相手にていねいに頼むときは Could you のあとに動詞の原形を置く"
                },
                {
                    "unit": "U7",
                    "ja": "私のおじは山の頂上からとてもたくさんの星が見えて驚きました。",
                    "frame": "My uncle [ ] from the top of the mountain.",
                    "tokens": [
                        "stars",
                        "surprised",
                        "many",
                        "was",
                        "see",
                        "so",
                        "to"
                    ],
                    "ans": "was surprised to see so many stars",
                    "exp": "be surprised のあとに to see を続けると、驚いた理由が「星を見たこと」だと分かる。この to と原形の組み合わせは気持ちの原因を表す使い方。see の前の to を落とすと文の形が崩れてしまう。",
                    "point": "うれしい・驚いたなどの気持ちの理由は、そのあとに to と動詞の原形で示す"
                },
                {
                    "unit": "U8",
                    "ja": "重い荷物を持ってあの高い山に登ることは、ヒナと私にはとてもたいへんでした。",
                    "frame": "[ ] was very hard for Hina and me.",
                    "tokens": [
                        "mountain",
                        "heavy",
                        "Climbing",
                        "with",
                        "high",
                        "bags",
                        "that"
                    ],
                    "ans": "Climbing that high mountain with heavy bags",
                    "exp": "Climbing のように -ing で始まるまとまりが、そのまま「登ること」という意味の主語になる。目的語 that high mountain は Climbing のすぐあとに置き、様子を表す with heavy bags は最後に回す。",
                    "point": "動詞の -ing 形は「〜すること」という名詞のはたらきをして文の先頭に来る"
                },
                {
                    "unit": "U10",
                    "ja": "海と山では、どちらが私たちの家族にとってよりわくわくしますか。",
                    "frame": "[ ], the sea or the mountains?",
                    "tokens": [
                        "exciting",
                        "is",
                        "our",
                        "Which",
                        "for",
                        "more",
                        "family"
                    ],
                    "ans": "Which is more exciting for our family",
                    "exp": "2つを比べて「どちらが」とたずねるので Which で始め、is のあとに more exciting を置く。最後にコンマで区切り、比べる相手 the sea or the mountains を並べる。exciting は more を使って比べる語。",
                    "point": "2つを比べてたずねるときは Which is 〜, A or B? の形にする"
                },
                {
                    "unit": "U11",
                    "ja": "海の近くのこの小さな村に、あの古いホテルはいつ建てられたのですか。",
                    "frame": "[ ] in this small village near the sea?",
                    "tokens": [
                        "old",
                        "was",
                        "built",
                        "When",
                        "hotel",
                        "that"
                    ],
                    "ans": "When was that old hotel built",
                    "exp": "「いつ建てられたか」は受け身の疑問文なので、When のあとに was ＋ 主語 ＋ 過去分詞 built と並べる。built は build の過去分詞。When did that hotel build では「ホテルが建てた」という意味になってしまう。",
                    "point": "受け身をたずねる文は、疑問詞のあとに be動詞＋過去分詞を続けて作る"
                },
                {
                    "unit": "U12",
                    "ja": "去年の夏、おじは私たちに、キャンプ場の近くでどこできれいな水が手に入るか教えてくれました。",
                    "frame": "My uncle [ ] near our camp site last summer.",
                    "tokens": [
                        "where",
                        "us",
                        "water",
                        "told",
                        "find",
                        "clean",
                        "to"
                    ],
                    "ans": "told us where to find clean water",
                    "exp": "where に to と原形 find を続けると「どこで見つければよいか」という意味のまとまりになり、told us のあとにそのまま置ける。to を落として where find とすると形が崩れる。",
                    "point": "where のあとに to と原形を置くと「どこで〜すればよいか」を表す"
                }
            ]
        },
        {
            "no": 4,
            "kind": "rewrite",
            "pt": 3,
            "title": "書き換え",
            "inst": "次の各文を、（　）内の指示にしたがって書き換えよ。",
            "items": [
                {
                    "unit": "U5",
                    "src": "Sara came home from school yesterday. Her favorite drama was already on TV.",
                    "inst": "2つの文を接続詞 when を使って1つの文にしなさい。When で始めること。",
                    "ans": "When Sara came home from school yesterday, her favorite drama was already on TV.",
                    "exp": "「サラが昨日学校から帰ってきたとき」が時を表す部分なので、その文の前に when を置く。when の文を先に書いたときは、その終わりにコンマを入れてもう一方の文を続ける。うしろの文の Her は小文字の her になる。",
                    "point": "2つの文は、「〜のとき」にあたる方の前に when を置いて1つにまとめる"
                },
                {
                    "unit": "U7",
                    "src": "I want to see the new movie with Sara this weekend.",
                    "inst": "ていねいな言い方に書きかえなさい。would like を使うこと。",
                    "ans": "I would like to see the new movie with Sara this weekend.",
                    "accept": [
                        "I'd like to see the new movie with Sara this weekend."
                    ],
                    "exp": "want to 〜 をていねいにした形が would like to 〜。would like のあとは to ＋ 動詞の原形なので、see を原形のままにする。I would like は I'd like と縮めて書ける。店で注文するときの I'd like this one. と同じ言い方。",
                    "point": "want to 〜 は、ていねいに言うとき would like to 〜 の形にする"
                },
                {
                    "unit": "U8",
                    "src": "You helped me with my homework yesterday. Thank you.",
                    "inst": "2つの文を、Thank you for で始まる1文にしなさい。helped を適切な形に変えて使うこと。",
                    "ans": "Thank you for helping me with my homework yesterday.",
                    "exp": "for のうしろに動詞をそのままの形で置くことはできない。help を helping に変えると「手伝ってくれてありがとう」という意味の1文になる。もとの文にあった You は相手のことなので、書かなくても伝わる。",
                    "point": "Thank you for のあとの動作は、動詞を -ing の形にして表す"
                },
                {
                    "unit": "U9",
                    "src": "Everyone calls that popular TV actor Sunny Ken.",
                    "inst": "ほぼ同じ意味の文に書きかえなさい。The actor's nickname で始めること。",
                    "ans": "The actor's nickname is Sunny Ken.",
                    "exp": "call A B は「A を B と呼ぶ」という意味で、B は A の呼び名を表している。だから「その俳優の呼び名は Sunny Ken だ」と言いかえられる。calls のあとに並ぶ2つのうち、前が呼ばれる人、うしろが呼び名。",
                    "point": "call A B の B は A の呼び名なので、Aの呼び名は B だ、と言いかえられる"
                },
                {
                    "unit": "U10",
                    "src": "This music program is more interesting than the drama on channel eight.",
                    "inst": "ほぼ同じ意味の文に書きかえなさい。The drama on channel eight で始めること。",
                    "ans": "The drama on channel eight is not as interesting as this music program.",
                    "accept": [
                        "The drama on channel eight isn't as interesting as this music program.",
                        "The drama on channel eight is less interesting than this music program."
                    ],
                    "exp": "A is more 〜 than B は「A の方が〜だ」なので、B を主語にすると「B は A ほど〜ではない」という言い方になる。not as 〜 as の間の形容詞には more を付けず、もとの interesting をそのまま入れる。",
                    "point": "A の方が〜だという文は、B を主語にして not as 〜 as A と言いかえられる"
                },
                {
                    "unit": "U12",
                    "src": "Yuma does not know the way to the concert hall.",
                    "inst": "ほぼ同じ意味の文に書きかえなさい。how to を使うこと。",
                    "ans": "Yuma does not know how to get to the concert hall.",
                    "accept": [
                        "Yuma does not know how to go to the concert hall.",
                        "Yuma doesn't know how to get to the concert hall.",
                        "Yuma doesn't know how to go to the concert hall."
                    ],
                    "exp": "the way to 〜 は「〜への道」で、how to ＋ 原形を使うと「どうやって〜すればよいか」と言いかえられる。to のあとは原形なので gets や going にはしない。know の目的語がかたまりごと入れかわっているだけで、文の骨組みは変わらない。",
                    "point": "「〜への道が分かる」は、how to ＋ 原形を使って「行き方が分かる」と言いかえられる。"
                }
            ]
        },
        {
            "no": 5,
            "kind": "jtrans",
            "pt": 6,
            "title": "英文和訳",
            "inst": "次の英文の下線部を日本語に直せ。下線のない部分は、場面がわかるように示したものである。",
            "items": [
                {
                    "unit": "MIX",
                    "context": "Rei is writing a report about the history of our town for school.",
                    "src": "The river in our town is very beautiful because it is cleaned by many volunteers every month.",
                    "model": "私たちの町の川はとても美しい。なぜなら、その川は毎月たくさんのボランティアの人たちによってきれいにされているからだ。",
                    "alts": [
                        "私たちの町を流れる川は、毎月多くのボランティアの人たちによって清掃されているので、とても美しい。"
                    ],
                    "elements": [
                        [
                            "主節を「私たちの町の川はとても美しい」と訳したうえで、because 以下を「〜だから」「〜ので」「なぜなら〜」と理由として結べている",
                            2
                        ],
                        [
                            "is cleaned を「きれいにされている」「そうじされている」のように受け身の意味で訳せている",
                            2
                        ],
                        [
                            "だれが（by many volunteers）と、どのくらい（every month）の両方が訳せている（片方だけなら1点）",
                            2
                        ]
                    ],
                    "exp": "is cleaned は be動詞と過去分詞を並べた受け身で、「きれいにされている」という意味になる。だれがするのかは by のあとの many volunteers。because は理由を表すので、後半を「〜だからだ」とまとめてから前半につなぐと自然な日本語になる。",
                    "point": "受け身の文と理由を表す節が組み合わさった長い文は、意味のまとまりで区切って訳す。"
                },
                {
                    "unit": "MIX",
                    "context": "Rei and Tomoya are members of the same volunteer group at their school.",
                    "src": "Last Sunday Rei got up earlier than Tomoya to take part in the volunteer work at the park.",
                    "model": "この前の日曜日、レイは公園でのボランティア活動に参加するために、トモヤより早く起きた。",
                    "alts": [
                        "この前の日曜日、レイは公園のボランティア活動に参加しようと、トモヤよりも早く起きた。"
                    ],
                    "elements": [
                        [
                            "いつ（Last Sunday）と、どこで（at the park）の両方が訳せている（片方だけなら1点）",
                            2
                        ],
                        [
                            "got up earlier than Tomoya を「トモヤより早く起きた」と2人を比べる意味で訳せている",
                            2
                        ],
                        [
                            "to take part in 〜 を「参加するために」のように目的を表す訳にできている",
                            2
                        ]
                    ],
                    "exp": "earlier than Tomoya は early の比較級で、2人の起きた時刻を比べている。to take part in 〜 は「参加するために」と目的を表す形。got up が過去形なので、全体を日曜日の出来事として過去の言い方で訳す。",
                    "point": "than の前後を比べて訳し、to のかたまりは目的を表す言い方として日本語にする。"
                }
            ]
        },
        {
            "no": 6,
            "kind": "trans",
            "pt": 4,
            "title": "英作文",
            "inst": "次の日本語を英語に直せ。",
            "items": [
                {
                    "unit": "U6",
                    "ja": "去年、私の家の近くには図書館が1つもありませんでした。",
                    "model": "There were no libraries near my house last year.",
                    "alts": [
                        "There was no library near my house last year.",
                        "There were not any libraries near my house last year."
                    ],
                    "elements": [
                        [
                            "「〜がなかった」を There ＋ be動詞の過去形 で表せている",
                            1
                        ],
                        [
                            "あとに続く名詞の数に be動詞が合っている（複数なら were、単数なら was）",
                            1
                        ],
                        [
                            "「1つもない」を no または not any で表せている",
                            1
                        ],
                        [
                            "「私の家の近くには」「去年」という場所と時が入っている",
                            1
                        ]
                    ],
                    "exp": "「〜がある」の There is / There are を過去にすると There was / There were になる。「1つもない」は名詞の前に no を置くか、not any を使って表す。last year があるので現在形の are にはしない。",
                    "point": "「〜がなかった」は There was / There were のあとに no ＋ 名詞 を続ける。"
                },
                {
                    "unit": "U3",
                    "ja": "私の姉は来年、東京で日本語を教えるつもりです。（be going to を使って）",
                    "model": "My sister is going to teach Japanese in Tokyo next year.",
                    "alts": [
                        "Next year my sister is going to teach Japanese in Tokyo.",
                        "My sister is going to teach the Japanese language in Tokyo next year."
                    ],
                    "elements": [
                        [
                            "「〜するつもりです」を〈be going to ＋ 動詞の原形〉で表せている",
                            1
                        ],
                        [
                            "主語が三人称単数なので be動詞が is になっている",
                            1
                        ],
                        [
                            "「日本語を教える」という内容が表せている",
                            1
                        ],
                        [
                            "「東京で」「来年」という場所と時が入っている",
                            1
                        ]
                    ],
                    "exp": "前もって決めている予定は〈be going to ＋ 動詞の原形〉で表す。主語 my sister は三人称単数なので be動詞は is。to のあとは必ず原形なので teaches や teaching とは書かない。",
                    "point": "前もって決めている予定は〈be going to ＋ 動詞の原形〉で表す。"
                }
            ]
        }
    ]
}
