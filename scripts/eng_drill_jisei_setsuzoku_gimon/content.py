# -*- coding: utf-8 -*-
"""英文法ドリル補充 (時制 / 接続詞 / 疑問詞・間接疑問) の**正典**。

ここが唯一の書き場所。seed-data の JSON は build.py の出力であって、手で直さない
(check.py が「再生成して差分ゼロ」を機械で確認する)。

各問のタプル:
    (unit_key, level, stem, choices(自然な順), answer_text, explanation)

約束 (check.py が全部機械で見る):
  - stem は自己完結。空所は "(   )" ちょうど1個。前後だけで正解が一意に決まる文脈を書く。
  - choices は4つ・重複なし。answer_text は choices のどれかと**完全一致**。
    ★正解を index で書かない (ずれの事故はこれで構造的に起きなくなる)。
  - 誤答は「別解釈で正解になりえない」ものだけ置く。迷う形は選択肢から外す
    (例: will / be going to のように両方成り立つ組は同居させない)。
  - explanation は位置トークン (①②/N番目/答え:N) を書かない = 値参照。
    build.py が正解位置をラウンドロビンで振り直すので、位置を書くと解説が陳腐化する。
  - explanation には正解の語句をそのまま含め、誤答が誤りである理由も述べる。
"""

# unit_key -> server/main.py の GRAMMAR_UNITS に実在する単元名
UNIT_MAP = {
    "tense": "時制",
    "conj": "接続詞",
    "wh": "疑問詞・間接疑問",
}

SOURCE = "drill-tense-conj-wh-20260909"   # <=30字。ロールバック: DELETE FROM grammar_questions WHERE source=...
SUBJECT = "english"

Q = [

# ==================================================================== 時制 (30)
# ---------------------------------------------------------- 時制 basic (8)
("tense", "basic", "My brother (   ) the dishes every evening after dinner; that is his job in our family.",
 ["does", "is doing", "did", "has done"], "does",
 "every evening(毎晩)という習慣を表す語句があり、後半の that is his job も現在の話だと示しているので現在形。"
 "主語 My brother は3人称単数なので does となる。"
 "is doing は今この瞬間に進行中の動作、has done は「やり終えた」という完了を表す。"
 "did なら「昔は毎晩やっていた」と過去の習慣になり、今も担当だと述べる後半と食い違う。"),

("tense", "basic", "Be quiet. The baby (   ) in the next room.",
 ["sleeps", "is sleeping", "slept", "has slept"], "is sleeping",
 "Be quiet.(静かに)と言っている、まさに今の状態なので現在進行形の is sleeping。"
 "sleeps は「いつも眠る」という習慣、slept は過去の出来事、has slept は「眠り終えた」という完了で、"
 "今まさに眠っている最中であることを表せない。"),

("tense", "basic", "I (   ) a shower when the doorbell rang, so I couldn't answer it right away.",
 ["take", "took", "was taking", "have taken"], "was taking",
 "ベルが鳴った過去の一点で進行中だった動作なので過去進行形の was taking。"
 "だからこそ「すぐに出られなかった」という後半につながる。"
 "took だと「ベルが鳴ってからシャワーを浴びた」という順序の意味になり、出られなかった理由にならない。"
 "take は現在形、have taken は現在完了で、過去の一点の場面とは結びつかない。"),

("tense", "basic", "We (   ) each other since we were children.",
 ["know", "knew", "have known", "are knowing"], "have known",
 "since we were children(子どもの頃から)が起点を示し、その状態が今も続いているので現在完了の have known。"
 "know は状態を表す動詞なので are knowing のように進行形にはしない。"
 "現在形 know や過去形 knew では「昔から今まで続いている」という継続が表せない。"),

("tense", "basic", "She didn't (   ) her homework last night because she felt sick.",
 ["do", "did", "does", "done"], "do",
 "否定文を作る didn't のあとは動詞の原形なので do。"
 "did や does は時制を示す形、done は過去分詞で、いずれも didn't のあとには置けない。"),

("tense", "basic", "Look at those dark clouds. It (   ) rain soon.",
 ["is going to", "is going", "will going to", "goes"], "is going to",
 "目の前の状況(黒い雲)を根拠に予測する言い方は be going to + 動詞の原形なので is going to rain となる。"
 "is going だけでは rain とつながらず、will going to は will と be going to を混ぜた誤った形。"
 "goes は現在形で、これから起こることの予測にはならない。"),

("tense", "basic", "I have never (   ) such a beautiful sunset before.",
 ["see", "saw", "seen", "seeing"], "seen",
 "have never のあとは過去分詞を置いて「今までに一度も〜したことがない」という経験を表すので seen。"
 "原形 see や過去形 saw は have のあとに置けず、seeing では完了形を作れない。"),

("tense", "basic", "I haven't finished my report (   ).",
 ["already", "yet", "still", "ever"], "yet",
 "現在完了の否定文の文末に置いて「まだ〜していない」を表すのは yet。"
 "already は肯定文で「もう〜した」、ever は疑問文などで「今までに」を表す。"
 "still も「まだ」だが I still haven't finished のように not の前に置く語で、文末には来ない。"),

# ------------------------------------------------------- 時制 standard (12)
("tense", "standard", "Nobody knows when the approaching typhoon (   ) the island tomorrow.",
 ["reaches", "will reach", "reached", "has reached"], "will reach",
 "この when 節は knows の目的語になる名詞節なので、未来のことは will を使って will reach とする。"
 "approaching(接近中の)と tomorrow がこれから起きることだと示している。"
 "「時や条件の副詞節では未来を現在形で表す」規則は副詞節だけの約束で、名詞節には及ばない。"
 "reached や has reached は過去や完了の形で、これから起こる到達を表せない。"),

("tense", "standard", "They (   ) for more than an hour, and the bus still hasn't come.",
 ["wait", "waited", "have been waiting", "had waited"], "have been waiting",
 "1時間以上前から今この瞬間まで待ち続けているので現在完了進行形の have been waiting。"
 "still hasn't come が「今も来ていない」と現在との結びつきを示している。"
 "waited では現在まで続いていることが表せず、had waited は過去のある時点までの継続、wait は習慣を表す。"),

("tense", "standard", "It was the first time I (   ) a live performance of that orchestra.",
 ["would see", "have seen", "had seen", "was seeing"], "had seen",
 "It was the first time … は「その時までに初めて」の意味なので、続く節は過去完了の had seen になる。"
 "It is the first time なら現在完了だが、主節が was と過去なので過去完了に下げる。"
 "was seeing は一時的に進行中だった動作を表す形で「その時点までの経験」にならず、would see では「これから見る」ことになる。"
 "have seen は現在までの経験で、主節の過去と食い違う。"),

("tense", "standard", "Her hands were covered with paint; she (   ) the fence all morning before we arrived.",
 ["paints", "has been painting", "had been painting", "will have painted"], "had been painting",
 "we arrived という過去の一点まで続いていた動作なので過去完了進行形の had been painting。"
 "paints は現在の習慣、has been painting は現在までの継続で、すでに終わった過去の場面と食い違う。"
 "will have painted は未来のある時点までの完了で、過去の話には使えない。"),

("tense", "standard", "By the end of this year, my grandfather (   ) this shop for fifty years.",
 ["will run", "will be running", "will have been running", "has been running"], "will have been running",
 "未来のある時点(by the end of this year)までの継続を表すので未来完了進行形の will have been running。"
 "will run は単なる未来、will be running はその時点で進行中であることを言うだけで、50年という積み重ねを表せない。"
 "has been running は現在までの継続なので、未来の時点を示す by the end of this year と合わない。"),

("tense", "standard", "Our teacher told us that the Meiji Restoration (   ) place in 1868.",
 ["takes", "took", "would take", "has taken"], "took",
 "歴史上の事実は、主節が過去でも時制を一致させず過去形のままにするので took。"
 "takes は現在形で、1868年に起きた出来事を述べる形にならない。"
 "would take は「そのあとで起こる予定だった」という意味になり、すでに確定した過去の事実には使えない。"
 "has taken は現在完了で、1868 という明確な過去の一点を示す語句とは共存できない。"),

("tense", "standard", "It (   ) five years since my grandmother passed away.",
 ["has been", "is having", "had been", "will have been"], "has been",
 "「〜してから…年になる」は It has been + 期間 + since + 過去形 の形で表すので has been。"
 "since 節の passed away が起点を示し、そこから現在までの経過を現在完了で受ける。"
 "had been は過去のある時点までの経過、will have been は未来の時点までの経過を表し、"
 "is having は have を進行形にした形で状態を表せない。"),

("tense", "standard", "A: (   ) you ever visited Hokkaido?  B: Yes, I went there last winter.",
 ["Did", "Have", "Are", "Were"], "Have",
 "ever を伴って「今までに行ったことがあるか」と経験をたずねる文なので現在完了の Have。"
 "Did は last winter のように過去の一時点を特定してたずねるときの形で、B の答えがその形になっている。"
 "Are や Were は be 動詞で、過去分詞 visited と組んでも「訪れたことがあるか」という経験の意味にならない。"),

("tense", "standard", "This box (   ) all the letters my grandfather wrote during the war.",
 ["is containing", "contains", "has been containing", "contain"], "contains",
 "contain(〜が入っている)は状態を表す動詞なので進行形にせず現在形で使い、主語 This box が3人称単数なので contains。"
 "is containing や has been containing は状態動詞を進行形にした誤った形。"
 "contain は原形で、3人称単数の主語には形が合わない。"),

("tense", "standard", "(   ) you be using your car this weekend? If not, could I borrow it?",
 ["Will", "Do", "Are", "Have"], "Will",
 "「今週末に車を使っている予定ですか」と相手の予定をたずねる未来進行形 will be using なので Will。"
 "Do は現在形の疑問文を作る語、Are は be 動詞、Have は完了形を作る語で、いずれも be using とは結びつかない。"),

("tense", "standard", "My sister isn't here. She (   ) to the post office.",
 ["has been", "has gone", "had gone", "have gone"], "has gone",
 "「行ってしまって今ここにいない」という現在の結果を表すのは has gone to。"
 "has been to は「行ったことがある/行って戻ってきた」の意味になり、isn't here と矛盾する。"
 "had gone は基準となる過去の時点がないため使えず、have gone は3人称単数の主語 She と形が合わない。"),

("tense", "standard", "I (   ) leave the house when the phone rang.",
 ["was about to", "am about to", "will be about to", "have been about to"], "was about to",
 "「まさに家を出ようとしていた」は be about to + 動詞の原形で表し、rang と同じ過去の場面なので was about to。"
 "am about to は現在、will be about to は未来のことになり、電話が鳴った過去の場面と時制が合わない。"
 "have been about to は現在完了で、過去の一点の出来事を述べる形ではない。"),

# ------------------------------------------------------- 時制 advanced (10)
("tense", "advanced", "Please stay in the waiting room until your name (   ).",
 ["is called", "will be called", "calls", "will call"], "is called",
 "until が導く時の副詞節では、未来のことでも現在形で表すので is called。"
 "will be called はこの副詞節の中では用いない。"
 "calls / will call は能動態で、「名前が呼ばれる」という受け身の意味にならない。"),

("tense", "advanced", "We (   ) to finish the project by Friday, but the delay in shipping made it impossible.",
 ["had hoped", "have hoped", "hope", "are hoping"], "had hoped",
 "「〜するつもりだったが実現しなかった」という叶わなかった願望は過去完了で表すので had hoped。"
 "have hoped / hope / are hoping はいずれも現在の願望を述べる形で、"
 "but 以下の「不可能になった」という結末と噛み合わない。"),

("tense", "advanced", "He said he (   ) in Paris for ten years before he moved to Tokyo.",
 ["has lived", "had been living", "is living", "lives"], "had been living",
 "主節が said と過去で、パリでの生活は東京へ移る前まで続いていたので過去完了進行形の had been living。"
 "has lived は現在までの継続、lives / is living は現在の話で、"
 "いずれも「過去のある時点よりさらに前から続いていた」という関係を表せない。"),

("tense", "advanced", "He is always (   ) other people for his own mistakes; nobody wants to work with him.",
 ["blame", "blaming", "blamed", "to blame"], "blaming",
 "always とともに使う進行形は「いつも〜してばかりいる」と非難の気持ちを込める言い方なので blaming。"
 "原形 blame は is のあとに置けない。"
 "is blamed では「責められる」という受け身になり、other people を目的語に取れない。"
 "is to blame は「責任がある」という慣用表現で、後ろに人を目的語として続ける形ではない。"),

("tense", "advanced", "She promised that she (   ) the document the following morning, but it never arrived.",
 ["will send", "would send", "would have sent", "had sent"], "would send",
 "主節が promised と過去で、送るのは the following morning(その翌朝)とさらに後のことなので、"
 "時制の一致でその時点から見た未来を表す would send になる。"
 "will send では主節の過去と一致しない。"
 "would have sent は「(そうしていれば)送っていただろうに」と実際には起こらなかったことを表す形で、約束の内容にならない。"
 "had sent は約束より前に送り終えたことを表す形なので、翌朝という後の時点とは両立しない。"),

("tense", "advanced", "This is the third time you (   ) the same mistake in this report.",
 ["make", "made", "have made", "had made"], "have made",
 "This is the … time は現在を基準にした言い方なので、続く節は現在完了の have made になる。"
 "主節が It was the … time と過去なら過去完了に下げるが、ここは is なので had made は合わない。"
 "make や made ではこれまでに積み重なった回数を表せない。"),

("tense", "advanced", "He (   ) his leg in a skiing accident two years ago and still walks with a limp.",
 ["has broken", "broke", "had broken", "has been breaking"], "broke",
 "two years ago と過去の一時点が示されているので過去形の broke。"
 "現在完了 has broken は「いつ」を特定する語句とは一緒に使えない。"
 "had broken は基準となる過去の時点がなく、has been breaking は骨折という一瞬の出来事を継続の形にしていて不自然。"),

("tense", "advanced", "Over the past decade, the climate of this region (   ) noticeably drier.",
 ["becomes", "became", "has become", "had become"], "has become",
 "Over the past decade(この10年にわたって)は過去から現在までの期間を示すので現在完了の has become。"
 "became では現在との結びつきが切れ、becomes は習慣や一般的な事実を述べる形になる。"
 "had become は過去のある時点までの変化で、現在に至る変化を表せない。"),

("tense", "advanced", "Ever since he (   ) to Tokyo, we have hardly heard from him.",
 ["moves", "moved", "has moved", "had moved"], "moved",
 "since が起点となる過去の一時点を示すときは、since 節を過去形にして主節を現在完了にするので moved。"
 "has moved / had moved は完了形で、起点そのものを示す since 節には置かない。"
 "現在形 moves では過去に起きた出来事を表せない。"),

("tense", "advanced", "The thief had run away before the police (   ) at the scene.",
 ["arrive", "arrived", "had arrived", "has arrived"], "arrived",
 "before が前後関係をはっきり示しているので、あとに起きた出来事は単純過去の arrived でよい。"
 "had arrived にすると警察の到着のほうが逃走より前だったことになり、文意が逆転する。"
 "arrive は現在形、has arrived は現在完了で、過去の出来事を語る文には合わない。"),

# ================================================================== 接続詞 (30)
# -------------------------------------------------------- 接続詞 basic (8)
("conj", "basic", "I'll wait here (   ) you come back.",
 ["until", "while", "during", "by"], "until",
 "「戻ってくるまでずっと待つ」と動作が続く終点を示すので接続詞 until。"
 "while は「〜する間」で終点を示さない。"
 "during と by は前置詞なので、あとに you come back という〈主語+動詞〉を続けられない。"),

("conj", "basic", "He couldn't attend the meeting (   ) he was sick in bed.",
 ["because", "because of", "so that", "in spite of"], "because",
 "あとに he was sick という〈主語+動詞〉の節が続くので、理由を表す接続詞 because。"
 "because of と in spite of は前置詞のはたらきをするので、あとには名詞や動名詞しか置けない。"
 "so that は目的や結果を表す形で、理由を述べる位置には合わない。"),

("conj", "basic", "Please wash your hands (   ) you have dinner.",
 ["before", "until", "unless", "since"], "before",
 "「夕食を食べる前に手を洗う」という前後関係なので接続詞 before。"
 "until は「〜するまでずっと」と継続の終点を示す語で、手を洗い続ける意味になってしまう。"
 "unless は「〜しない限り」、since は「〜以来・〜だから」で、いずれも意味が通らない。"),

("conj", "basic", "My grandmother speaks (   ) English and Chinese fluently.",
 ["both", "either", "neither", "not only"], "both",
 "後ろの and と呼応して「AとBの両方」を表すのは both A and B の形。"
 "either は or と、neither は nor と組む相関表現。"
 "not only は but also と組む形なので、and とは呼応しない。"),

("conj", "basic", "He (   ) smokes nor drinks; he is very careful about his health.",
 ["either", "neither", "both", "not only"], "neither",
 "後ろの nor と呼応して「AもBもしない」を表すのは neither A nor B の形。"
 "either は or と、both は and と、not only は but also と組む形で、いずれも nor とは呼応しない。"),

("conj", "basic", "I'm glad (   ) you passed the entrance examination.",
 ["that", "what", "which", "whether"], "that",
 "「〜ということ」と、感情の原因になる完全な文をまとめて導くのは接続詞 that。"
 "what や which は関係詞・疑問詞で、あとに主語や目的語の欠けた不完全な文が続く。"
 "whether は「〜かどうか」で、合格したという確定した事実を喜ぶ文脈には合わない。"),

("conj", "basic", "I studied very hard, (   ) I couldn't answer the last question.",
 ["but", "so", "for", "or"], "but",
 "「一生懸命勉強したのに解けなかった」と前後が反対の内容なので、逆接の等位接続詞 but。"
 "so は結果、for は理由の付け足し、or は選択を表す語で、対立する内容をつなげない。"),

("conj", "basic", "(   ) I was a child, my family lived in a small fishing village.",
 ["When", "Until", "During", "Because"], "When",
 "「子どもの頃に」と時を表す副詞節を導くのは接続詞 When。"
 "Until は「〜するまで」で、子ども時代を終点とする意味になり文意が通らない。"
 "During は前置詞なので節を導けず、Because では「子どもだったから村に住んだ」となって理由の関係が成り立たない。"),

# ----------------------------------------------------- 接続詞 standard (12)
("conj", "standard", "My brother is very outgoing, (   ) I prefer to spend time alone.",
 ["whereas", "because", "unless", "as if"], "whereas",
 "二つの文を並べて「〜であるのに対して」と対比するのは whereas。"
 "because は理由、unless は「〜しない限り」という否定の条件、as if は「まるで〜のように」で、"
 "いずれも二つの内容を対照させるはたらきを持たない。"),

("conj", "standard", "(   ) you are familiar with the software, could you show me how to use it?",
 ["Since", "Though", "Whether", "Unless"], "Since",
 "「〜なのだから」と、相手も承知している事情を理由として示すのは Since。"
 "Though は譲歩、Unless は否定の条件、Whether は「〜かどうか」で、依頼の根拠を述べる形にならない。"),

("conj", "standard", "(   ) he had practiced for months, he failed to win the championship.",
 ["Despite", "In spite of", "Although", "Because of"], "Although",
 "あとに he had practiced という〈主語+動詞〉の節が続くので、譲歩を表す接続詞 Although。"
 "Despite / In spite of / Because of はいずれも前置詞のはたらきをするので、あとには名詞や動名詞しか置けない。"),

("conj", "standard", "We haven't decided (   ) to hold the event online or in person.",
 ["if", "that", "whether", "what"], "whether",
 "直後に to 不定詞を伴って「〜すべきかどうか」を表せるのは whether。"
 "if も「〜かどうか」の意味を持つが、直後に to 不定詞を続ける用法がない。"
 "that は事実を導く接続詞、what は節の中で名詞のはたらきをする語で、or 以下の二者択一と呼応しない。"),

("conj", "standard", "(   ) you have made a promise, you must keep it no matter what happens.",
 ["Once", "Until", "Unless", "Whether"], "Once",
 "「いったん〜したら」と、ある事が成立した後を条件として示すのは接続詞 Once。"
 "Until は「〜するまで」、Unless は「〜しない限り」という否定の条件、Whether は「〜であろうと」で、"
 "約束を交わした後に義務が生じるという流れを作れない。"),

("conj", "standard", "It must have rained during the night, (   ) the roads are still wet this morning.",
 ["for", "because of", "in case", "though"], "for",
 "前で述べた判断の根拠をあとから付け足す等位接続詞は for。"
 "「道路がまだ濡れているのだから、夜のうちに雨が降ったにちがいない」という流れになる。"
 "because of は前置詞のはたらきなので節を導けない。"
 "in case は「〜するといけないから」と備えを述べる形、though は譲歩を表す形で、"
 "どちらも「そう判断した根拠」を後ろに付け足す働きを持たない。"),

("conj", "standard", "Either you or your brother (   ) to attend the parents' meeting.",
 ["have", "has", "are", "were"], "has",
 "either A or B が主語のときは、動詞を近いほうの主語 your brother に合わせるので3人称単数の has。"
 "have / are / were はいずれも複数の主語に対応する形で、直前の単数の主語と一致しない。"),

("conj", "standard", "(   ) I know, the library is closed on national holidays.",
 ["As far as", "As long as", "As soon as", "As well as"], "As far as",
 "「私の知る限りでは」と、述べる内容の範囲を限定するのは As far as。"
 "As long as は「〜しさえすれば」という条件、As soon as は「〜するとすぐに」という時、"
 "As well as は「〜と同様に」で、知識の及ぶ範囲を示す用法がない。"),

("conj", "standard", "Take this medicine, (   ) you will feel much better in a few hours.",
 ["and", "or", "but", "for"], "and",
 "〈命令文, and …〉で「〜しなさい、そうすれば…」という結果を表すので and。"
 "or なら「そうしないと」という逆の意味になり、薬を飲んだ結果よくなるという流れに合わない。"
 "but は逆接、for は理由の付け足しで、命令文の結果を導く形にならない。"),

("conj", "standard", "The problem was (   ) his ability but his attitude toward the team.",
 ["not", "either", "both", "neither"], "not",
 "後ろの but と呼応して「AではなくB」を表すのは not A but B の形。"
 "either は or と、both は and と、neither は nor と組む相関表現なので、but とは呼応しない。"),

("conj", "standard", "(   ) time went by, the two countries gradually improved their relations.",
 ["As", "While", "When", "Since"], "As",
 "「〜するにつれて」と、二つの変化が並行して進むことを表すのは接続詞 As。"
 "While は「〜する間」、When は「〜する時」で、時間の経過とともに少しずつ変化するという意味を持たない。"
 "Since は「〜以来」で、主節が improved と過去形であることと噛み合わない。"),

("conj", "standard", "(   ) it rains tomorrow, we will hold the festival as planned.",
 ["Even if", "Even though", "As if", "Now that"], "Even if",
 "まだ起きていないことを仮定して「たとえ〜だとしても」と譲歩するのは Even if。"
 "Even though は「実際に〜だけれども」と事実を前提にする形なので、明日の天気のようにまだ決まっていないことには使えない。"
 "As if は「まるで〜のように」、Now that は「今や〜だから」で、譲歩の条件を作れない。"),

# ----------------------------------------------------- 接続詞 advanced (10)
("conj", "advanced", "It was (   ) difficult a question that even our teacher couldn't answer it.",
 ["so", "such", "very", "too"], "so",
 "〈so + 形容詞 + a(n) + 名詞 + that …〉の語順をとるのは so。"
 "such を使うなら such a difficult question の語順になり、形容詞が a より前に出るこの形では使えない。"
 "very や too には、that 節と呼応して「とても〜なので…」という結果を導く用法がない。"),

("conj", "advanced", "You may use the laboratory (   ) that you clean up afterward.",
 ["provided", "supposed", "concerned", "regarded"], "provided",
 "〈provided (that) …〉で「〜という条件であれば」という条件を示す。"
 "supposing なら同じ用法があるが、supposed の形では条件節を導けない。"
 "concerned は as far as … is concerned、regarded は as regards のように別の形で使う語で、条件を示す接続詞にはならない。"),

("conj", "advanced", "Human language differs from animal communication (   ) it can describe events that have not yet happened.",
 ["in that", "for that", "with that", "by that"], "in that",
 "〈in that S V〉で「〜という点において」と、違いや理由の観点を示す。"
 "for that / with that / by that には、このように節を導いて理由や観点を示す用法がない。"),

("conj", "advanced", "(   ) that she has been studying English for only a year, her pronunciation is remarkable.",
 ["Considering", "Regarding", "Concerning", "Including"], "Considering",
 "〈Considering (that) S V〉で「〜であることを考えれば」と判断の前提を示す。"
 "Regarding や Concerning は「〜に関して」、Including は「〜を含めて」という意味の前置詞のはたらきをする語で、"
 "that 節を導いて判断の前提を述べる用法がない。"),

("conj", "advanced", "I didn't say anything, (   ) I agreed with him, but that I didn't want to start an argument.",
 ["not that", "so that", "now that", "in that"], "not that",
 "〈not that A, but that B〉で「Aだからではなく、Bだからだ」と理由を対比する形。"
 "so that は目的や結果、now that は「今や〜だから」、in that は「〜という点で」を表し、"
 "後ろの but that と呼応して理由を打ち消す形にならない。"),

("conj", "advanced", "(   ) I admit that there are some difficulties, I don't think the plan is impossible.",
 ["While", "During", "Despite", "Unless"], "While",
 "文頭の While は「〜ではあるが」と譲歩を表す接続詞として使える。"
 "During と Despite は前置詞なので、あとに I admit という節を続けられない。"
 "Unless は「〜しない限り」で、困難を認めたうえで反論するという流れを作れない。"),

("conj", "advanced", "(   ) that the evidence is limited, the researchers were right to be cautious.",
 ["Granted", "Allowed", "Permitted", "Accepted"], "Granted",
 "〈Granted (that) S V〉で「〜であることは認めるとしても」と譲歩を示す決まった形。"
 "Allowed / Permitted / Accepted は「許された」「受け入れられた」という過去分詞で、"
 "that 節を導いて譲歩を表す用法がない。"),

("conj", "advanced", "Both the coach and the players (   ) satisfied with the result of the match.",
 ["was", "has been", "were", "is"], "were",
 "both A and B が主語のときは複数として扱うので、過去の be 動詞は were。"
 "was や is は単数の主語に対応する形、has been は現在完了で単数の主語を受ける形なので、"
 "いずれも複数扱いのこの主語とは一致しない。"),

("conj", "advanced", "It will not be long (   ) the cherry blossoms come into full bloom.",
 ["before", "since", "that", "when"], "before",
 "〈It will not be long before S V〉で「まもなく〜するだろう」という決まった形になるので before。"
 "since は「〜以来」で現在完了とともに用い、that は名詞節を導く接続詞、when は「〜する時」で、"
 "この構文の一部にはならない。"),

("conj", "advanced", "So (   ) as I am concerned, the current plan needs no revision.",
 ["far", "long", "soon", "much"], "far",
 "〈So far as S is concerned〉で「〜に関する限り」という決まった形になるので far。"
 "So long as は「〜しさえすれば」という条件を表す別の形。"
 "So soon as や So much as は、この意味の慣用表現にならない。"),

# ====================================================== 疑問詞・間接疑問 (30)
# --------------------------------------------- 疑問詞・間接疑問 basic (8)
("wh", "basic", "(   ) broke this window? — I'm afraid I did.",
 ["Who", "Whom", "Whose", "Who did"], "Who",
 "疑問詞がそのまま主語になる文では do / does / did を使わず〈疑問詞+動詞〉の語順にするので Who。"
 "Whom は目的格なので主語にならず、Whose は「誰の〜」と所有を尋ねる語。"
 "Who did のあとには動詞の原形 break が必要で、過去形の broke を続けることはできない。"),

("wh", "basic", "(   ) does it take to get to the airport from here?",
 ["How long", "How far", "How much", "How often"], "How long",
 "take と組んで所要時間を尋ねるのは How long。"
 "How far は距離、How much は量や値段、How often は頻度を尋ねる語で、「どのくらい時間がかかるか」を問えない。"),

("wh", "basic", "(   ) umbrella is this? — It's mine.",
 ["Whose", "Who's", "Who", "Whom"], "Whose",
 "直後の名詞 umbrella を修飾して「誰の傘か」と持ち主を尋ねるので Whose。"
 "Who's は who is の短縮形なので名詞を修飾できない。"
 "Who と Whom は代名詞で、名詞を直接修飾する形にならない。"),

("wh", "basic", "(   ) is the weather like in Sapporo in February?",
 ["What", "How", "Which", "Why"], "What",
 "文末に like があるので、その目的語になる What が必要になる。"
 "How を使うなら How is the weather in Sapporo? と like を付けない形にする。"
 "Which は選ぶ範囲が示されている場合の語、Why は理由を尋ねる語で、like の目的語になれない。"),

("wh", "basic", "I have no idea why (   ) so angry with me.",
 ["is she", "she is", "does she", "she does"], "she is",
 "文の一部に組み込まれた間接疑問は〈疑問詞+主語+動詞〉という平叙文の語順になるので she is。"
 "is she は疑問文の倒置した語順で、従属節の中では使わない。"
 "does she も疑問文の語順であるうえ、be 動詞の文に does を加えるのは誤り。"
 "she does では angry と結びつかない。"),

("wh", "basic", "Open the window, (   )?",
 ["will you", "do you", "are you", "shall we"], "will you",
 "命令文に付ける付加疑問は will you。"
 "do you や are you は平叙文に付ける形で、命令文には使えない。"
 "shall we は Let's で始まる文に付ける形。"),

("wh", "basic", "(   ) times have you visited Kyoto?",
 ["How many", "How much", "How long", "How far"], "How many",
 "直後に数えられる名詞の複数形 times が続くので How many。"
 "How much は数えられない量、How long は長さや期間、How far は距離を尋ねる語で、回数を数える文には合わない。"),

("wh", "basic", "Don't you like natto? — (   ), I love it.",
 ["Yes", "No", "Sure not", "Of course not"], "Yes",
 "英語では、たずね方が否定であっても答える内容が肯定なら Yes を使う。"
 "No は「好きではない」という否定の答えになり、続く I love it と矛盾する。"
 "Sure not や Of course not も否定の応答なので、同じく内容と食い違う。"),

# ------------------------------------------ 疑問詞・間接疑問 standard (12)
("wh", "standard", "(   ) you didn't tell me about the schedule change?",
 ["How come", "How", "Why", "What for"], "How come",
 "How come のあとは〈主語+動詞〉という平叙文の語順が続くので、この文には How come が入る。"
 "How や Why を使うなら didn't you tell me … と疑問文の語順にしなければならない。"
 "What for は What did you … for? のように文末に置いて使う形で、文頭には立てない。"),

("wh", "standard", "(   ) should I address the letter of complaint?",
 ["To who", "To whom", "Whom to", "Who to"], "To whom",
 "前置詞の直後に置く疑問詞は目的格になるので To whom。"
 "To who は前置詞のあとに主格を置いた誤った形。"
 "Whom to / Who to はこの位置で「誰宛てに」という意味を作れない語順。"),

("wh", "standard", "(   ) made you change your mind about studying abroad?",
 ["What", "Why", "How", "When"], "What",
 "他動詞 made の主語になれるのは「何が」を表す What。"
 "Why / How / When は副詞にあたる疑問詞なので、主語の位置には立てない。"),

("wh", "standard", "She asked me where I (   ) the previous weekend.",
 ["have been", "had been", "was being", "am"], "had been",
 "主節が asked と過去なので時制を一致させ、さらに「その前の週末」とより前のことを述べるので過去完了の had been。"
 "have been や am は現在を基準にした形で、主節の過去と一致しない。"
 "was being は一時的なふるまいを表す形で、居場所を述べる文にはならない。"),

("wh", "standard", "(   ) are you saving all this money for?",
 ["What", "Why", "How", "Which"], "What",
 "文末の前置詞 for の目的語になるのは What で、〈What … for?〉は「何のために」と目的を尋ねる形。"
 "Why は理由を尋ねる語で、文末の for と意味が重なってしまう。"
 "How や Which は for の目的語として目的を問うはたらきを持たない。"),

("wh", "standard", "Do you know (   ) the concert will begin?",
 ["when", "when will", "what time will", "that"], "when",
 "Do you know … は Yes / No で答えられる問いなので、中の間接疑問は〈疑問詞+主語+動詞〉の語順にする。"
 "when will や what time will は倒置した疑問文の語順で、従属節には置けない。"
 "that では時をたずねる意味にならない。"
 "なお Do you think … の場合は疑問詞が文頭に出て When do you think it will begin? となる点も押さえておきたい。"),

("wh", "standard", "Do you have any idea (   ) the missing documents?",
 ["who took", "who did take", "did who take", "whom took"], "who took",
 "any idea のあとは間接疑問で、疑問詞 who がそのまま主語になるので〈who + 動詞〉の語順の who took。"
 "who did take は強調の形で、事実をたずねる間接疑問としては不自然。"
 "did who take は倒置した疑問文の語順、whom は目的格なので主語にならない。"),

("wh", "standard", "(   ) do you say to having lunch at that new Italian restaurant?",
 ["What", "How", "Why", "When"], "What",
 "〈What do you say to ~ing?〉で「〜するのはどうですか」と提案する決まった形。"
 "How を使うなら How about having … と to を伴わない形にする。"
 "Why なら Why don't we …?、When は時をたずねる語で、提案の形を作れない。"),

("wh", "standard", "(   ) will the new bridge be completed? — In about two years.",
 ["How soon", "How long", "How much", "How far"], "How soon",
 "「あとどれくらいで〜するか」と完成までの時間をたずねるのは How soon で、答えの In about two years とも呼応する。"
 "How long は続く期間の長さ、How much は量や値段、How far は距離を尋ねる語で、完成の時期を問えない。"),

("wh", "standard", "The police are still investigating (   ) car was parked in front of the bank.",
 ["whose", "who's", "who", "whom"], "whose",
 "直後の名詞 car を修飾して「誰の車が」と持ち主を問う間接疑問なので whose。"
 "who's は who is の短縮形で名詞を修飾できない。"
 "who や whom は名詞を直接修飾する形にならない。"),

("wh", "standard", "(   ) ask your homeroom teacher for advice before you decide?",
 ["Why not", "Why don't", "How about", "What about"], "Why not",
 "〈Why not + 動詞の原形〉で「〜してはどうですか」と提案する形なので Why not。"
 "Why don't のあとには you を補って Why don't you ask … としなければならない。"
 "How about や What about のあとは動名詞 asking が続くので、原形の ask とは結びつかない。"),

("wh", "standard", "Could you tell me (   ) a post office near here?",
 ["if there is", "is there", "there is if", "whether is there"], "if there is",
 "tell me に続く間接疑問は〈接続詞+主語+動詞〉という平叙文の語順になるので if there is。"
 "is there は疑問文の倒置した語順、whether is there も同じく倒置していて使えない。"
 "there is if は語順が入れ替わっており、文として成立しない。"),

# ------------------------------------------ 疑問詞・間接疑問 advanced (10)
("wh", "advanced", "It doesn't matter (   ) wins the election; the basic policy is unlikely to change.",
 ["who", "whom", "whose", "for whom"], "who",
 "名詞節を導き、その節の中で wins の主語になるのは主格の who。"
 "whom は目的格、whose は所有格なので動詞の主語にならない。"
 "for whom は前置詞句なので、主語の位置には立てない。"),

("wh", "advanced", "(   ) is it that determines whether a new business succeeds or fails?",
 ["What", "Which", "How", "Why"], "What",
 "it is … that の強調構文で、that 以下の determines の主語が欠けているので、主語になれる What が入る。"
 "How や Why は副詞にあたる疑問詞なので、determines の主語にはなれない。"
 "Which は選ぶ範囲が示されていないため、この文では意味が成立しない。"),

("wh", "advanced", "(   ) the project will be funded or not remains to be seen.",
 ["Whether", "If", "That", "What"], "Whether",
 "「〜かどうか」という名詞節が文の主語になるときは Whether を使う。"
 "If にも「〜かどうか」の意味はあるが、主語になる名詞節を作ることはできない。"
 "That は事実を導く接続詞で or not と呼応せず、What は節の中で名詞のはたらきをする語が欠けているときに使う。"),

("wh", "advanced", "(   ) has become of the exchange student who stayed with your family last year?",
 ["What", "Who", "How", "Where"], "What",
 "〈What has become of ~?〉で「〜はどうなったのか」と消息をたずねる決まった形。"
 "Who では「誰が〜になったのか」となり、of と結びつかない。"
 "How や Where は become of の主語になれない。"),

("wh", "advanced", "She was at a loss (   ) to turn to for help.",
 ["whom", "whose", "what", "how"], "whom",
 "文末の前置詞 to の目的語になる〈疑問詞+不定詞〉なので、目的格の whom。"
 "whose は所有格なので後ろに名詞が必要になる。"
 "what では「誰を頼るか」という人を指す意味にならず、how では前置詞 to の目的語が欠けたままになる。"),

("wh", "advanced", "(   ) what extent do you think artificial intelligence will replace human workers?",
 ["To", "In", "At", "By"], "To",
 "〈To what extent …?〉で「どの程度まで〜か」と程度をたずねる決まった形。"
 "In / At / By は extent と組んでこの意味を表す形にならない。"),

("wh", "advanced", "(   ) if the typhoon hits the island before the ferry leaves?",
 ["What", "How", "Why", "Which"], "What",
 "〈What if S V?〉で「もし〜だったらどうなるのか」と仮定してたずねる形。"
 "How if / Why if / Which if という言い方は英語にはない。"),

("wh", "advanced", "You would be surprised at (   ) this simple method is.",
 ["how effective", "how is effective", "what effective", "how effective is"], "how effective",
 "前置詞 at の目的語になる間接疑問なので〈how + 形容詞 + 主語 + 動詞〉の語順で how effective this simple method is となる。"
 "how is effective や how effective is は倒置した疑問文の語順で、従属節には使えない。"
 "what には形容詞を直接伴って程度を表す用法がない。"),

("wh", "advanced", "(   ) of the two candidates do you think is more likely to win?",
 ["Which", "What", "Whose", "Whom"], "Which",
 "of the two candidates と選ぶ範囲が二人に限られているので Which。"
 "What は範囲が限定されない問いに使う。"
 "Whose は「誰の〜」と所有を問う語、Whom は目的格なので is の主語にならない。"),

("wh", "advanced", "I don't think she will accept our proposal, (   )?",
 ["will she", "won't she", "do I", "don't I"], "will she",
 "I don't think … の付加疑問は、否定が実質的に that 節の内容にかかると考え、"
 "従属節 she will accept を受けて肯定形の will she を付ける。"
 "won't she では否定が重なってしまう。"
 "do I / don't I は主節の I think を受ける形で、この構文では使わない。"),
]
