META = {
    "title": "英文解釈 × SVOCM 判別",
    "sub": "関関同立の英文を『なんとなく』から『記号で指せる』へ",
    "level": "関関同立（同志社・立命館・関西学院・関西大）",
    "brand": "トリリオン",
}

# ---------------------------------------------------------------- 巻頭：記号のルール
RULES = [
    {"cls": "rc-svoc", "h": "S V O C … 文の骨組み",
     "b": "主語 S・述語動詞 V・目的語 O・補語 C。第4文型の 2 つの目的語は O1・O2。"
          "骨組み以外の語はすべて修飾語 M。従属節の中の要素には S′ V′ O′ C′ とダッシュを付け、"
          "さらに内側なら S″ V″ とする。",
     "ex": "the rule＝S　made＝V　the students＝O　careful＝C"},
    {"cls": "rc-adv", "h": "( ) … 副詞のカタマリ",
     "b": "前置詞句・副詞節・分詞構文など、動詞や文全体を修飾する 2 語以上のかたまり。"
          "外しても文が成立するので、<b>まず外して骨組みを見る</b>。"
          "ただし deprive A of B のように動詞とセットで外せないものもある。",
     "ex": "( Although the technology is new ) , the problem is familiar."},
    {"cls": "rc-noun", "h": "[ ] … 名詞のカタマリ",
     "b": "that 節・what 節・whether 節・動名詞句・不定詞の名詞用法など、S / O / C になれるかたまり。"
          "<b>外すと文が壊れる</b>のが副詞のカタマリとの違い。"
          "形式主語 It の中身なら 真S、形式目的語 it の中身なら 真O のラベルを付ける。",
     "ex": "It is clear [ that the plan has failed ]."},
    {"cls": "rc-adj", "h": "&lt; &gt; … 形容詞のカタマリ",
     "b": "関係詞節・分詞の後置修飾・形容詞用法の不定詞や前置詞句。直前の名詞に線で結ぶと構造が見える。"
          "働きとしては<b>修飾語なので M</b>。ただしコンマ + which の非制限用法は例外で、"
          "先行詞が前の内容全体になることがある。",
     "ex": "the students &lt; who were talking &gt; became quiet"},
]

STEPS = [
    "前から読んで、( ) [ ] &lt; &gt; の<b>カタマリの切れ目</b>に印を入れる。"
    "目印は「前置詞・接続詞・関係詞・-ing / -ed / to」。",
    "カタマリを全部外し、残った<b>裸の骨組み</b>を見る。まず <b>V（述語動詞）</b>を 1 つ確定させる。"
    "接続詞・関係詞が連れてきた V′ は主節の V ではない。",
    "V の前の名詞が S、V の後ろの名詞が O、V の後ろで「O = それ」なら C。"
    "<b>O と C の間に「主語＋述語」の関係があるか</b>で第4文型と第5文型を分ける。",
    "骨組みが決まってから<b>文型を確定</b>し、外したカタマリを「どの語にかかるか」を決めながら戻す。"
    "かかり先が 2 通りあると感じたら、意味ではなく<b>語順と語法</b>で決める。",
    "最後に和訳する。<b>訳せたかではなく、S・V・O・C を指させるか</b>で自己採点すること。"
    "指せないまま訳が合っていたのは、当てただけである。",
]

RULE_EXAMPLES = [
    {"dsl": "{S:The book} <M:on the desk> {V:is} {C:mine} .",
     "pat": "第2文型（SVC）",
     "note": "&lt; on the desk &gt; を外すと The book is mine. という骨組みが残る。"
             "名詞の直後に前置詞句が来たら、まず<b>その名詞にかかる形容詞のカタマリ</b>を疑う。"
             "働きは修飾語なので記号は M。"},
    {"dsl": "{S:The new rule} {V:made} {O:the students} {C:more careful} .",
     "pat": "第5文型（SVOC）",
     "note": "the students <b>=</b> more careful という「主語と述語の関係」が O と C の間にある。"
             "これが第5文型の目印で、第4文型（O1 に O2 を与える）とはここで見分ける。"},
    {"dsl": "{S:It} {V:is} {C:clear} [真S: {接:that} {S':the plan} {V':has failed} ] .",
     "pat": "第2文型（SVC）",
     "note": "It は<b>形式主語</b>で、中身は [ that … ] のほう。中身に 真S のラベルを付ける。"
             "骨組みは It is clear の第2文型で、訳すときは真S から先に訳す。"},
    {"dsl": "( M: {接:When} {S':the bell} {V':rang} ) , {S:the students} "
            "<M: {S':who} {V':were talking} > {V:became} {C:quiet} .",
     "pat": "第2文型（SVC）",
     "note": "V に見える語が 3 つ（rang / were talking / became）あるが、"
             "<b>主節の V は became ただ 1 つ</b>。残りは接続詞 When と関係代名詞 who が連れてきた V′ である。"
             "( ) と &lt; &gt; を外せば the students became quiet が残る。"},
]

PART1 = [
    {"g": "Ａ　5文型の骨格を見抜く", "sub": "第1〜第5文型", "items": [
        {"id": "A1", "en": "The news made everyone in the room extremely happy.",
         "dsl": "{S:The news} {V:made} {O:everyone} <M:in the room> {C:extremely happy} .",
         "pat": "第5文型（SVOC）", "tag": "make O C",
         "notes": ["everyone と extremely happy の間に主語述語の関係があるので第5文型である。",
                   "&lt; in the room &gt; は everyone にかかる形容詞のカタマリで骨組みではない。",
                   "made を「作った」と訳すと崩れる。第5文型の make は「O を C の状態にする」。"],
         "ja": "その知らせは部屋にいた全員をこの上なく喜ばせた。"},
        {"id": "A2", "en": "The librarian handed the students a list of useful references.",
         "dsl": "{S:The librarian} {V:handed} {O1:the students} {O2:a list} <M:of useful references> .",
         "pat": "第4文型（SVOO）", "tag": "hand O1 O2",
         "notes": ["hand は「人に物を手渡す」型の動詞で、O1 に人、O2 に物が来る第4文型である。",
                   "&lt; of useful references &gt; は a list にかかる形容詞のカタマリなので M。",
                   "the students と a list の間に主語述語の関係は無い。だから第5文型ではない。"],
         "ja": "司書は学生たちに有用な参考文献の一覧を手渡した。"},
        {"id": "A3", "en": "The proposal remains controversial among local residents.",
         "dsl": "{S:The proposal} {V:remains} {C:controversial} ( M: among local residents ) .",
         "pat": "第2文型（SVC）", "tag": "remain + 形容詞",
         "notes": ["remain は「〜のままである」で、後ろに来る形容詞は O ではなく C である。",
                   "The proposal = controversial という「主語 = 補語」の関係が第2文型の目印。",
                   "( among local residents ) は外しても文が成立する副詞のカタマリなので M。"],
         "ja": "その提案は地元の住民の間で依然として賛否の分かれるものである。"},
        {"id": "A4", "en": "The committee members carefully examined every document.",
         "dsl": "{S:The committee members} {M:carefully} {V:examined} {O:every document} .",
         "pat": "第3文型（SVO）", "tag": "副詞の割り込み",
         "notes": ["carefully は S と V の間に割り込んだ副詞で、骨組みではないので M。",
                   "examined は他動詞で、直後の every document が目的語 O である。",
                   "副詞が S と V の間に入ると V を見失いやすい。まず副詞を外して骨組みを見る。"],
         "ja": "委員会のメンバーはすべての書類を注意深く調べた。"},
    ]},
    {"g": "Ｂ　修飾語 M を切り離す", "sub": "S と V が離れる形", "items": [
        {"id": "B1", "en": "Students who study abroad for a year often return with a wider view.",
         "dsl": "{S:Students} <M: {S':who} {V':study} ( abroad ) ( for a year ) > {M:often} "
                "{V:return} ( M: with a wider view ) .",
         "pat": "第1文型（SV）", "tag": "主語に関係詞節",
         "notes": ["S（Students）と V（return）が関係詞節で引き離されているのが急所である。",
                   "&lt; who … a year &gt; を外すと Students often return が残り、第1文型と分かる。",
                   "( with a wider view ) は return にかかる副詞のカタマリで骨組みではない。"],
         "ja": "1年間海外で学ぶ学生は、より広い視野を持って帰ってくることが多い。"},
    ]},
]

PART2 = [
    {"id": "G1", "en": "The report that the committee published last week surprised many readers.",
     "dsl": "{S:The report} <M: {O':that} {S':the committee} {V':published} ( last week ) > "
            "{V:surprised} {O:many readers} .",
     "pat": "第3文型（SVO）", "tag": "関係代名詞 that の目的格",
     "notes": ["that の後ろが the committee published で目的語が欠けている。だから関係代名詞である。",
               "同格の that なら後ろは欠けの無い完全な文になる。ここで見分ける。",
               "主節の V は surprised で、published は関係詞節の中の V′ である。"],
     "ja": "その委員会が先週公表した報告書は、多くの読者を驚かせた。",
     "q": "この文の that の働きとして最も適切なものを 1 つ選びなさい。",
     "choices": ["関係代名詞（目的格）で、published の目的語にあたる",
                 "接続詞で、The report の内容を説明する同格の節を導く",
                 "指示代名詞で、前の文の内容を指している",
                 "関係副詞で、published にかかる副詞の働きをしている"],
     "ans": 0,
     "exp": "that の後ろは the committee published last week で、published の目的語が欠けている。"
            "欠けがあるので関係代名詞であり、先行詞 The report がその目的語にあたる。"
            "同格の that なら後ろは欠けの無い完全な文になるので誤り。"
            "指示代名詞なら that の直後に動詞が来るはずで、ここでは the committee という名詞が続くので誤り。"
            "関係副詞なら後ろが完全な文になるので、目的語が欠けている本文には当てはまらない。"},
    {"id": "G2", "en": "The government announced a plan to reduce the number of cars in the city center.",
     "dsl": "{S:The government} {V:announced} {O:a plan} <M:to reduce the number of cars> "
            "( M: in the city center ) .",
     "pat": "第3文型（SVO）", "tag": "不定詞の形容詞用法",
     "notes": ["announced の目的語は a plan で、to reduce 以下はその a plan の中身を説明している。",
               "不定詞が名詞の直後に来たら、まず「その名詞にかかる形容詞用法」を疑うのが定石。",
               "副詞用法（〜するために）と取ると「発表した目的」になり、announce の語法に合わない。"],
     "ja": "政府は都心部の自動車の数を減らす計画を発表した。",
     "q": "to reduce 以下は何にかかっているか。最も適切なものを 1 つ選びなさい。",
     "choices": ["announced にかかる副詞のカタマリで、発表した目的を表している",
                 "a plan にかかる形容詞のカタマリで、その計画の中身を説明している",
                 "The government にかかる形容詞のカタマリである",
                 "the number にかかる形容詞のカタマリである"],
     "ans": 1,
     "exp": "a plan to do は「〜するという計画」で、不定詞が直前の名詞の中身を説明する形容詞用法である。"
            "announced にかかる副詞用法だとすると「減らすために発表した」となり、"
            "何を発表したのかが文中から消えてしまうので誤り。"
            "The government にかかるとすると「減らす政府」となり意味をなさないので誤り。"
            "the number にかかるとすると to reduce の直前の名詞は cars であって the number ではなく、"
            "語順の上で成り立たないので誤り。"},
    {"id": "G3", "en": "The number of students who apply to universities in urban areas has increased steadily.",
     "dsl": "{S:The number} <M:of students> <M: {S':who} {V':apply} ( to universities ) "
            "( in urban areas ) > {V:has increased} {M:steadily} .",
     "pat": "第1文型（SV）", "tag": "主語の核を見抜く",
     "notes": ["has increased は単数扱いなので、主語の核は students ではなく The number である。",
               "&lt; of students &gt; と &lt; who … areas &gt; を外すと The number has increased が残る。",
               "the number of ~ は「~の数」。動詞の数の一致が、主語がどれかを教える証拠になる。"],
     "ja": "都市部の大学に出願する学生の数は着実に増加している。",
     "q": "has increased の主語はどれか。最も適切なものを 1 つ選びなさい。",
     "choices": ["students", "universities", "The number", "urban areas"],
     "ans": 2,
     "exp": "the number of ~ が主語のとき、動詞の数を決めるのは核となる The number のほうである。"
            "has という単数扱いの形がその証拠になる。"
            "students は of に続く語で、直後の who apply の主語ではあるが主節の主語ではないので誤り。"
            "universities と urban areas はどちらも前置詞のあとに来る語で、"
            "前置詞の目的語は主語になれないので誤り。"},
    {"id": "G4", "en": "Continuous exposure to loud noise can leave workers unable to concentrate on simple tasks.",
     "dsl": "{S:Continuous exposure} <M:to loud noise> {V:can leave} {O:workers} "
            "{C:unable to concentrate on simple tasks} .",
     "pat": "第5文型（SVOC）", "tag": "leave O C",
     "notes": ["workers と unable … の間に「労働者が集中できない」という主語述語の関係がある。",
               "leave O C は「O を C の状態のままにする」。「置き忘れる」ではないので注意する。",
               "&lt; to loud noise &gt; は exposure にかかる形容詞のカタマリで骨組みではない。"],
     "ja": "騒音にさらされ続けると、労働者は単純な作業にも集中できない状態に置かれることがある。",
     "q": "この文の文型として正しいものを 1 つ選びなさい。",
     "choices": ["第2文型（SVC）", "第3文型（SVO）", "第4文型（SVOO）", "第5文型（SVOC）"],
     "ans": 3,
     "exp": "leave の後ろに workers と unable … の 2 つが並び、両者の間に主語述語の関係があるので第5文型である。"
            "第2文型なら leave の直後が補語 1 つだけになるはずで、名詞と形容詞が続く本文には合わない。"
            "第3文型なら目的語 1 つで文が終わるはずだが、unable 以下が余ってしまうので誤り。"
            "第4文型なら「workers に unable … を与える」となるが、unable は名詞ではなく形容詞なので"
            "O2 になれず、誤りである。"},
]

PART3 = [
    {"g": "①　関係詞・挿入・同格", "sub": "かかり先を決める", "items": [
        {"id": "D1",
         "en": "The speed with which the new policy was introduced left local officials little time to prepare.",
         "dsl": "{S:The speed} <M: ( with which ) {S':the new policy} {V':was introduced} > "
                "{V:left} {O1:local officials} {O2:little time} <M:to prepare> .",
         "pat": "第4文型（SVOO）", "tag": "前置詞 + 関係代名詞",
         "notes": ["with which は前置詞つきの関係代名詞で、the speed にかかる形容詞のカタマリを作る。",
                   "&lt; with which … introduced &gt; を外すと The speed left … が残り第4文型と分かる。",
                   "leave O1 O2 は「O1 に O2 を残す」。ここでは「時間をほとんど残さなかった」。"],
         "ja": "その新しい政策が導入された速さは、地元の職員にほとんど準備する時間を残さなかった。",
         "points": ["with which を the speed にかけて訳せている",
                    "leave A B を「A に B を残す」と第4文型で訳せている",
                    "little を「ほとんど〜ない」と否定的に訳せている"]},
    ]},
]
