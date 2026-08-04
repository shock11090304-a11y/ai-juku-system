# -*- coding: utf-8 -*-
"""
MARCH英語 文法・英作演習 No.01  データ単一ソース
- GRAMMAR: 文法25問（choice12 / order5 / error5 / rewrite3）
- WRITING: 英作6題（translation4 / essay2）
氏名欄は空欄（配布フリー）。正解位置は build 側で監査。
解説は「核心の一言 → なぜ → 原則化」＋コアイメージ・語りかけ（関正生スタイルに着想）。
"""

META = {
    "series": "MARCH英語 実戦演習",
    "no": "01",
    "title_g": "英文法・語法 25問",
    "title_w": "英作文 6題（和文英訳・自由英作）",
    "level": "MARCH レベル",
    "target": "私大文系・GMARCH志望",
    "student": "",  # 空欄=配布フリー
}

# ============================================================
#  文法・語法 25問
# ============================================================

# --- (1) 空所補充 四択 12問 ---
# 正解 index(0始まり) は ①②③④に均等配分（各3問）。
CHOICE = [
    {
        "q": "By the time you ( arrive ) at the station, I ______ writing the report.",
        "note": "駅に着くころには、私はレポートを書き終えているだろう。",
        "choices": ["will finish", "have finished", "finished", "will have finished"],
        "ans": 3,
        "point": "未来完了",
        "expl": "「〜する時までには、もう終わっている」——このゴール前の“完了”を表すのが未来完了 will have p.p.。"
                "単なる will finish だと「駅に着くのと同時に書き上げる」ことになり、締め切りに間に合わせた感じが消えてしまう。"
                "なお by the time は「時を表す副詞節」なので、未来の話でも arrive と現在形にするのがルール。",
    },
    {
        "q": "______ I known you were coming, I would have prepared a better meal.",
        "note": "君が来ると知っていたら、もっと良い食事を用意したのに。",
        "choices": ["If", "Should", "Were", "Had"],
        "ans": 3,
        "point": "仮定法過去完了・if省略の倒置",
        "expl": "仮定法のカギは「現実との距離」。実際には来ると知らなかった——その“事実とのズレ”を過去完了 had known で表す。"
                "この if は省略でき、その合図として had が主語の前に出て倒置（Had I known …）になる。"
                "If だけ残して過去分詞を続けることはできない。",
    },
    {
        "q": "You ______ have told me about the change earlier; I could have helped you.",
        "note": "その変更をもっと早く言ってくれればよかったのに。手伝えたのだから。",
        "choices": ["must", "can", "will", "should"],
        "ans": 3,
        "point": "should have p.p.（非難・後悔）",
        "expl": "should の芯にあるのは「当然」。その矢印を過去に向けると「本来〜すべきだったのに（実際はしなかった）」という"
                "後悔・非難になり、後半の could have helped（手伝えたのに）と裏返しで呼応する。"
                "must have p.p. は「〜したに違いない」の過去推量なので、悔やむこの文脈には合わない。",
    },
    {
        "q": "I'll never forget ______ the Grand Canyon for the first time. It was breathtaking.",
        "note": "初めてグランドキャニオンを見たことは決して忘れないだろう。",
        "choices": ["to see", "to have seen", "seeing", "see"],
        "ans": 2,
        "point": "forget doing（過去にした事の記憶）",
        "expl": "to不定詞は「これから（未来）」、-ing は「もう起きたこと」を指す——この時間の向きが決め手。"
                "ここは「初めて見た」という過去の体験を忘れない話なので、頭に映像として残る seeing。"
                "forget to see なら「これから見るのを忘れる」になり、意味がずれてしまう。",
    },
    {
        "q": "She is a novelist ______ books have sold millions of copies worldwide.",
        "note": "彼女は、著書が世界中で何百万部も売れている小説家だ。",
        "choices": ["who", "whom", "whose", "which"],
        "ans": 2,
        "point": "所有格の関係代名詞 whose",
        "expl": "関係代名詞は「2つの文をつなぐ接着剤」。元の Her books have sold …（彼女の著書が売れている）の"
                "her（所有格）を関係詞にしたのが whose なので、直後には必ず名詞（books）が続くのが目印。"
                "who / whom は直後に名詞を従えられず、which は人（小説家）を先行詞にできない。",
    },
    {
        "q": "The population of Tokyo is far larger than ______ of any other city in Japan.",
        "note": "東京の人口は、日本の他のどの都市の人口よりもはるかに多い。",
        "choices": ["this", "that", "it", "one"],
        "ans": 1,
        "point": "比較対象の一致（the population の反復＝that）",
        "expl": "比較は「同じもの同士を比べる」のが大原則。ここは“東京の人口”と“他都市の人口”の勝負なので、"
                "繰り返す the population を that で受ける（that＝the＋既出名詞）。"
                "it は「まさにそれ」で別物を指せず、one は「不特定の一つ」なので、the … of ~ の言い換えには使えない。",
    },
    {
        "q": "He explained the rules slowly ______ everyone in the room could understand them.",
        "note": "彼は部屋の全員が理解できるように、ゆっくりルールを説明した。",
        "choices": ["so that", "such that", "in order", "so as"],
        "ans": 0,
        "point": "目的の so that S can",
        "expl": "「全員が理解できるように」という“目的”を表すのが so that S can[could]。"
                "②such that は「〜となるような」と程度・結果を表す別物で、目的には使えない。"
                "in order は後ろに that節か to不定詞（in order to）が要り、so as は so as to do の形でしか使えない。"
                "空所の後ろに S V が続く以上、節をそのまま導ける so that が正解。",
    },
    {
        "q": "______ his enormous wealth, he always seemed lonely and unsatisfied.",
        "note": "莫大な富にもかかわらず、彼はいつも孤独で満たされないようだった。",
        "choices": ["Despite", "Although", "However", "Even though"],
        "ans": 0,
        "point": "譲歩の前置詞 despite＋名詞",
        "expl": "ここは英文法最大の分かれ道「前置詞か、接続詞か」。判断材料は空所の後ろの形だけ。"
                "後ろは名詞のカタマリ（his enormous wealth）なので、名詞を直接導ける前置詞の Despite が正解。"
                "Although と Even though はどちらも「〜だけれども」の接続詞で、後ろには S V の文が必要。"
                "However は副詞なので、そもそも名詞句を導けない——残り3つは全て「形」の一点で外れる。",
    },
    {
        "q": "During the crowded festival, she had her smartphone ______ from her bag.",
        "note": "混雑した祭りの最中に、彼女はバッグからスマホを盗まれた。",
        "choices": ["steal", "stole", "stolen", "to steal"],
        "ans": 2,
        "point": "have＋O＋p.p.（被害）",
        "expl": "have O＋過去分詞のキモは、O と後ろの動詞が「される」関係（受け身）になること。"
                "スマホは自分で盗むのでなく「盗まれる」側なので、過去分詞 stolen が正解。"
                "同じ形が「〜してもらう（have my hair cut）」にもなり、“被害”か“依頼”かは文脈が決める——形は一つと考えればOK。",
    },
    {
        "q": "A number of passengers ______ still waiting for the delayed flight to depart.",
        "note": "多くの乗客が、遅れている便の出発をまだ待っている。",
        "choices": ["is", "are", "was", "has been"],
        "ans": 1,
        "point": "a number of＋複数名詞＝複数扱い",
        "expl": "主語の「主役」がどこかで動詞が決まる。a number of passengers の主役は passengers（乗客）＝"
                "「たくさんの乗客」なので複数扱いで are。冠詞が the に変わる the number of ~（〜の数）だと"
                "主役は number そのものになり単数扱い、と裏返しで覚えると混同しない。",
    },
    {
        "q": "Your voice ______ me of an old friend I haven't seen in years.",
        "note": "君の声は、何年も会っていない旧友を思い出させる。",
        "choices": ["remembers", "reminds", "memorizes", "recalls"],
        "ans": 1,
        "point": "remind A of B（AにBを思い出させる）",
        "expl": "remind は re（再び）＋mind（心）で「心に再び浮かばせる＝思い出させる」。"
                "of は「関連づけて引き出す」働きなので、remind A of B ＝「A（人）の頭から B を引っ張り出す」と考えればOK。"
                "remember / recall / memorize は自分が思い出す・覚える側なので、この“人 of もの”の型は作れない。",
    },
    {
        "q": "The engineers worked overnight to ______ a solution to the sudden system failure.",
        "note": "技術者たちは突然のシステム障害の解決策を思いつくため徹夜で作業した。",
        "choices": ["come up with", "put up with", "get away with", "do away with"],
        "ans": 0,
        "point": "come up with（〜を思いつく）",
        "expl": "熟語も丸暗記でなくパーツで見る。come up with は、解決策がふっと「浮かび上がって（up）自分の所に来る（come）」"
                "イメージで「思いつく」。put up with（我慢する）・get away with（うまく逃れる）・do away with（廃止する）は"
                "形が似て意味が全く別なので、イメージごと切り分けておこう。",
    },
]

# --- (2) 語句整序 5問（和文付き・語群から並べ替え） ---
ORDER = [
    {
        "jp": "このアプリを使えば、外国語を学ぶのがずっと簡単になる。",
        "words": ["it", "to learn", "makes", "much easier", "a foreign language", "This app"],
        "answer": "This app makes it much easier to learn a foreign language",
        "point": "make＋形式目的語 it＋C＋to do",
        "expl": "英語には「長くて重いものは後ろに回す」という大原則がある。目的語 to learn a foreign language が長いので"
                "後ろへ送り、空いた席に仮の目的語 it を置いたのがこの形（make it C to do）。"
                "主語が This app（モノ）なので、「このアプリのおかげで〜」と訳し上げると自然。",
    },
    {
        "jp": "実際にその国に住んで初めて、私たちはその文化を本当に理解できる。",
        "words": ["that", "we can truly understand", "live in a country",
                  "It is not until", "its culture", "we actually"],
        "answer": "It is not until we actually live in a country that we can truly understand its culture",
        "point": "It is not until … that …（〜して初めて…）",
        "expl": "直訳は「実際に住むまでは本当には理解できない」——これを裏返すと「住んで初めて理解できる」になる。"
                "この not until …（〜まで〜ない）のカタマリを、強調構文 It is ~ that の枠にはめ込んだ形。"
                "日本語の「初めて」につられて first などを入れないのがコツ。",
    },
    {
        "jp": "私は、彼が難しい問題に取り組むやり方が気に入っている。",
        "words": ["the way", "deals with", "I like", "difficult problems", "he"],
        "answer": "I like the way he deals with difficult problems",
        "point": "the way SV（〜する方法／やり方）",
        "expl": "「〜する方法・やり方」は the way の後ろに S V を続けるだけでOK。"
                "注意は the way how と重ねないこと——the way と how は同じ役目なので、どちらか一方しか使わない（how he deals … でも同義）。"
                "日本語の「やり方」に that / which を足したくなるが、これも不要。",
    },
    {
        "jp": "どんなに一生懸命努力しても、私は彼を説得することができなかった。",
        "words": ["how hard", "I couldn't", "No matter", "persuade him", "I tried"],
        "answer": "No matter how hard I tried I couldn't persuade him",
        "point": "no matter how＋形/副＋SV（どんなに〜でも）",
        "expl": "no matter how は「どんなに〜でも」という譲歩の合図。ポイントは how の直後に程度を表す語をくっつけること。"
                "ここは hard を連れて no matter how hard I tried とする。how を単独で後ろに残さず、セットで前に出すのが型。",
    },
    {
        "jp": "彼は日本の他のどの作家にも劣らず有名だ。",
        "words": ["as famous as", "in Japan", "He is", "writer", "any other"],
        "answer": "He is as famous as any other writer in Japan",
        "point": "as 〜 as any other＋単数名詞（最上級相当）",
        "expl": "見た目はふつうの as ~ as だが、「他のどの作家“一人”と比べても同じくらい有名」＝実質「最も有名な作家の一人」を表す。"
                "比べる相手は1人ずつなので、any other の後ろは単数形 writer。"
                "最上級を使わずにトップ級を言える便利な型、と考えればOK。",
    },
]

# --- (3) 誤り指摘 5問（下線(a)〜(d)から誤りを1つ） ---
# html: 下線は [a|語句] のマーカーで表す。ans=誤りの記号, correct=訂正。
ERROR = [
    {
        "html": "[a|The number] of students [b|who] [c|want] to study abroad [d|have] increased sharply this year.",
        "ans": "d",
        "correct": "have → has",
        "point": "the number of＝単数扱い",
        "expl": "主語の「主役」は先頭の The number（数そのもの）で単数扱いなので、has increased が正解。"
                "直前の students（複数）に釣られて have にしてしまう「近くの名詞に引っぱられる罠」に注意。"
                "「〜の数が増えた」なら主役は常に number、と押さえておこう。",
    },
    {
        "html": "[a|Hardly] had I [b|left] the house [c|than] it [d|began] to rain heavily.",
        "ans": "c",
        "correct": "than → when",
        "point": "hardly … when 〜（〜するやいなや）",
        "expl": "「〜するやいなや」には相棒（相関語）が決まった型が2つ——hardly[scarcely] … when ~ と no sooner … than ~。"
                "hardly の相手は than ではなく when なので、ここは than → when。"
                "文頭に否定の hardly が出て had I left と倒置している形自体は正しく、直すのはこの一語だけ。",
    },
    {
        "html": "My sister has been [a|married] [b|with] a lawyer [c|who] works [d|for] a global firm.",
        "ans": "b",
        "correct": "with → to",
        "point": "be married to 〜",
        "expl": "marry はもともと「〜と結婚する」という他動詞。「〜と結婚している」状態は be married to ~ の形で表し、"
                "結びつく相手に向かう to を使うのがポイント。日本語の「〜と」につられて with としがちだが誤り"
                "（なお work for a firm「〜に勤める」の for は正しい）。",
    },
    {
        "html": "I'm really [a|looking] forward [b|to] [c|see] you [d|again] at the reunion next month.",
        "ans": "c",
        "correct": "see → seeing",
        "point": "look forward to doing（to＝前置詞）",
        "expl": "ここは受験生が必ず引っかかる、to の正体がテーマ。look forward to の to は不定詞ではなく前置詞なので、"
                "後ろは名詞か動名詞——seeing が正解。見分け方は「to の後ろに名詞を置けるか」で、"
                "look forward to the party と言える以上、前置詞だと分かる。",
    },
    {
        "html": "The climate of Okinawa is much milder than [a|that] [b|of] Hokkaido, but [c|more humid] than [d|Tokyo].",
        "ans": "d",
        "correct": "Tokyo → that of Tokyo",
        "point": "比較対象の一致",
        "expl": "比較は「同じ種類のもの同士」で揃えるのが鉄則。比べているのは“沖縄の気候”と“東京の気候”なので、"
                "Tokyo（都市）ではなく that of Tokyo（東京の気候）にしなければいけない。"
                "前半が正しく that of Hokkaido となっているのが、そのまま後半のお手本になる。",
    },
]

# --- (4) 同意文完成（書き換え）3問 ---
REWRITE = [
    {
        "given": "He was so exhausted that he could not walk any farther.",
        "target": "He was ______ exhausted ______ walk any farther.",
        "blanks": ["too", "to"],
        "point": "so … that S can't ＝ too … to do",
        "expl": "too は単なる「とても」ではなく「度を越して（マイナス）」が芯。だから too ~ to do は「〜すぎて…できない」と"
                "否定を含み、so ~ that S can't と同じ意味になる。主語が同じ人（he）なので、to walk の前に意味上の主語は要らない。",
    },
    {
        "given": "Because I did not know what to say, I just kept silent.",
        "target": "______ ______ what to say, I just kept silent.",
        "blanks": ["Not", "knowing"],
        "point": "理由の分詞構文（否定は not＋doing）",
        "expl": "分詞構文は「接続詞＋主語＋動詞」をぎゅっと -ing 一語に圧縮する技。Because I did not know … の余分を削って"
                "動詞を knowing にし、否定の not はその前に置いて Not knowing what to say とする。"
                "主語が主節と同じ（I）だから省ける、という点もセットで押さえよう。",
    },
    {
        "given": "If it had not been for your advice, I would have made a serious mistake.",
        "target": "______ ______ your advice, I would have made a serious mistake.",
        "blanks": ["But", "for"],
        "point": "if it had not been for ＝ but for / without",
        "expl": "If it had not been for ~（〜がなかったら）は長いので、名詞ひとつで同じ仮定を言える But for ~（＝Without ~）に"
                "圧縮できる。前提を短くしただけなので、帰結節は仮定法過去完了 would have made のまま。"
                "But for の後ろは必ず名詞、と形で覚えておこう。",
    },
]

GRAMMAR = {"choice": CHOICE, "order": ORDER, "error": ERROR, "rewrite": REWRITE}

# ============================================================
#  英作文 6題
# ============================================================

TRANSLATION = [
    {
        "jp": "その突然の知らせを聞いて、彼女は言葉を失った。",
        "models": [
            "The sudden news left her speechless.",
            "She was so shocked at the sudden news that she could not say a word.",
        ],
        "point": "日本語は「彼女は」で始めたくなるが、英語は「知らせが彼女を無言にした」とモノを主語にする（無生物主語）と一気に締まる。"
                 "leave O C は「O を C の状態のままにする」で、the news left her speechless の形。硬ければ so ~ that … でもOK。",
        "mistakes": "「言葉を失う」を lost her words と直訳すると不自然。状態を表す形容詞 speechless か、"
                    "be at a loss for words という決まり文句で表す。",
    },
    {
        "jp": "もっと早く家を出ていれば、私は始発電車に間に合ったのに。",
        "models": [
            "If I had left home earlier, I could have caught the first train.",
            "Had I left home earlier, I would have been in time for the first train.",
        ],
        "point": "過去の事実に反する「〜だったら…だったのに」は、if節・帰結節ともに“ひとつ過去へずらして距離を作る”のが仮定法過去完了。"
                 "If S had p.p., S would/could have p.p. の形で、両方を完了側にそろえる。",
        "mistakes": "最頻出ミスは帰結節を would catch と現在の形にすること。過去の話なので would have caught と完了にそろえる。"
                    "「間に合う」は catch the train / be in time for ~。",
    },
    {
        "jp": "インターネットのおかげで、私たちは世界中の情報に瞬時にアクセスできるようになった。",
        "models": [
            "The Internet has enabled us to access information from all over the world instantly.",
            "Thanks to the Internet, we can now gain instant access to information around the world.",
        ],
        "point": "「〜のおかげで」も The Internet を主語にして enable O to do（モノが人に〜を可能にする）で表すと自然。"
                 "thanks to ~ を使う手もある。動詞の access は他動詞で、後ろに前置詞は要らない。",
        "mistakes": "名詞の access（access to ~）と混同し、動詞なのに access to information とする誤りが多発。"
                    "access information と直接つなぐ。information は不可算なので informations も誤り。",
    },
    {
        "jp": "本を読めば読むほど、自分がいかに無知であるかがよくわかる。",
        "models": [
            "The more books you read, the more clearly you realize how ignorant you are.",
            "The more you read, the more you come to see how little you know.",
        ],
        "point": "「〜すればするほど…」の比例は The 比較級 …, the 比較級 … で表し、比較級のカタマリ（the more books）を"
                 "各節の頭に出すのが型。文中の how ignorant you are は間接疑問なので、「疑問詞＋ふつうの語順（S V）」に戻す。",
        "mistakes": "how you are ignorant と語順を崩すミスに注意——how ignorant のあとに you are と続ける。"
                    "また「無知だとわかる」を「賢くなる」と反対の意味にしないこと。",
    },
]

ESSAY = [
    {
        "prompt": "「高校生はアルバイトをするべきだ」という意見に賛成か反対か。理由を添えて60語程度の英語で書きなさい。",
        "length": "約60語",
        "models": [
            ("賛成の立場",
             "I agree that high school students should be allowed to have part-time jobs. "
             "Working outside school teaches them the value of money and how to deal with different kinds of people. "
             "These are practical skills that textbooks alone cannot provide. As long as the work does not harm their studies, "
             "a part-time job helps them grow into responsible adults."),
        ],
        "point": "自由英作は難しい単語より「型」で決まる。①立場を最初に一文で宣言 → ②理由を2つ → "
                 "③具体例や条件（As long as ~）で肉付け、の順に並べるだけで説得力が出る。語数は指定の±10%に収めるのが安全。",
        "mistakes": "よくある失点は、理由が1つで薄いことと、主語・動詞の抜け。とくに because は接続詞なので後ろは必ず S V——"
                    "名詞だけ置きたいなら because of に変える、という前置詞/接続詞の判断を忘れずに。",
    },
    {
        "prompt": "オンライン授業と対面授業では、どちらが優れていると思うか。理由とともに70語程度の英語で書きなさい。",
        "length": "約70語",
        "models": [
            ("対面授業を支持する立場",
             "In my opinion, face-to-face classes are better than online ones. First, students can concentrate more easily "
             "because there are fewer distractions in a classroom than at home. Second, they can ask questions and receive "
             "immediate answers from their teachers. Online lessons are certainly convenient, but the direct communication of a "
             "real classroom helps students understand the material more deeply. That is why I prefer face-to-face learning."),
        ],
        "point": "比較テーマは「立場 → First / Second で理由 → 相手の長所を一度認める（convenient）→ でも自分の主張」の順に組むと"
                 "大人びた答案になる。First / Second などの“つなぎ語”は読み手への道しるべなので、必ず入れる。",
        "mistakes": "better を使ったら比べる相手 than online ones を必ず添えること（比較対象の書き忘れが最多ミス）。"
                    "つなぎ語がないと理由がただの羅列に見えるので、標識を置いて論理の流れを見せる。",
    },
]

WRITING = {"translation": TRANSLATION, "essay": ESSAY}
