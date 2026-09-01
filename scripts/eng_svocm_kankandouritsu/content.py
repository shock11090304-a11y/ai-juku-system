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

# ---------------------------------------------------------------- 巻頭：記号の書き方（表記規約）
# ★ここは lint.py 冒頭の「表記規約」と 1 対 1 で対応する。片方だけ直さないこと。
#   同じ構文が 2 通りに書けると「記号を指させるか」で採点できなくなる。
NOTATION = [
    ("助動詞・完了・受動", "助動詞 can / will、完了の have、受動の be は<b>述語動詞と同じマス</b>にまとめる。",
     "has become＝V　can cost＝V　is discovered＝V"),
    ("副詞が割り込んだとき", "助動詞と動詞の間に副詞や主語が入ったときだけ、助動詞を 助 として分ける。",
     "has＝助　recently＝M　won＝V"),
    ("ダッシュの本数", "囲みの外＝ダッシュなし、囲み 1 つの中＝S′、囲み 2 つ以上の中＝S″。"
     "深くなっても 2 本で止める。接・同格・挿入・強調・真S・真O にはダッシュを付けない。",
     "( 接 S′ V′ &lt; S″ V″ &gt; )"),
    ("括弧と働きをそろえる", "( ) は副詞のカタマリなので M か 挿入、[ ] は名詞のカタマリなので S / O / C など、"
     "&lt; &gt; は形容詞のカタマリなので M。<b>括弧の形と記号が食い違ってはいけない</b>。",
     "( M: … )　[ O: … ]　&lt; M: … &gt;"),
    ("分詞の後置修飾", "&lt; &gt; の中の分詞には V′ を付ける。素の語のまま置かない。",
     "&lt; M: adopted＝V′ ( M′: by most schools ) &gt;"),
    ("that の見分け", "&lt; &gt; の中の that は関係詞なので S′ か O′ を付ける。"
     "同格の that 節は名詞のカタマリなので [ 同格: … ] で囲む。",
     "&lt; M: that＝O′ … &gt;　／　[ 同格: that … ]"),
    ("名詞に付く of 句", "S・O のマスに of 句を抱え込まない。<b>核だけをマス</b>にして of 句は外に出す。"
     "ただし be capable of / take advantage of のように<b>語法が要求する前置詞</b>はマスに残す。",
     "the cost＝S　&lt; M: of the repairs &gt;"),
    ("挿入と同格", "文中に割り込む節は ( 挿入: … )。コンマで挟んだ名詞の言い換えは [ 同格: … ]。",
     "( 挿入: many doctors say )"),
    ("強調構文", "It is X that … は形の上は第2文型。It＝S、is＝V、X＝C とし、that 以下は [ 強調: … ]。"
     "that 以下を ( ) で囲まない（( ) は副詞の記号なので意味が食い違う）。",
     "It＝S　is＝V　the teacher＝C　[ 強調: that … ]"),
    ("受動態の文型", "be + 過去分詞は 1 つの V として数える。後ろに何も無ければ<b>第1文型</b>とする。",
     "is discovered＝V　→ 第1文型"),
    ("準助動詞", "tend to / have to / be going to / seem to は<b>助動詞ではない</b>ので V のマスに入れない。"
     "動詞を V にし、to 不定詞は別のマスにする。",
     "tend＝V　[ O′: to report … ]"),
    ("補語が節のとき", "C が動詞を含むとき（to 不定詞・原形不定詞）は [ C: … ] で囲んで中も分解する。"
     "形容詞 1 つの C、および<b>形容詞 + to 不定詞</b>（impossible to explain / hard to read）は"
     "形容詞のかたまりなので平のマスのままでよい。",
     "[ C: to stay＝V′　fresh＝C′ ]　／　hard to read＝C"),
    ("there 構文", "There は主語ではなく <b>M</b>。本当の S は動詞の後ろの名詞。",
     "There＝M　are＝V　many reasons＝S"),
    ("カタマリの中の of 句", "( ) や &lt; &gt; の中に「名詞 + of 句」が素のまま入っていたら、"
     "of 以下を &lt; M &gt; で割って外に出す。<b>ただしその of 句のうしろにさらに修飾が続くときは割らない</b>"
     "（割ると次の行の禁じ手になる）。",
     "( M: in the middle &lt; M′: of the night &gt; )"),
    ("カタマリを2つ並べない", "同じ深さに &lt; &gt; を 2 つ並べない。2 つ目が 1 つ目の中の名詞にかかるなら"
     "<b>入れ子</b>にする。並べるとどちらにかかるか図から読めない。",
     "&lt; M: of the roof &lt; M′: above the stage &gt; &gt;"),
    ("前置詞句をどちらに付けるか", "直前の<b>名詞だけ</b>を説明していれば &lt; M &gt;（形容詞）。"
     "<b>動詞が要求</b>していて動詞を消すと意味が立たないなら ( M )（副詞）。",
     "an impact &lt; M: on companies &gt;　／　received … ( M: from the office )"),
    ("群動詞", "「動詞 + 前置詞」を 1 マスにしてよいのは<b>受動態にできるとき</b>だけ"
     "（look after → was looked after が成り立つ）。"
     "できないものは前置詞句を M として外に出す（意味は切り離さない）。"
     "「動詞 + 副詞辞」（come out / put off）は 1 マスでよく、受動態のテストは使わない。",
     "look after＝V　／　depend＝V ( M: on … )"),
]


# ---------------------------------------------------------------- 構文の割り当て表
# ★この教材が何を教えるかの設計図。グループごとに**重ならない**プールを持たせ、
#   check.py が「プール外の構文を出していないか」と「プールの構文が全部出ているか」を落とす。
#   重複を tag（自由文）で数えると書き換えるだけですり抜けられるので slug で数える。
#   ★宣言した構文が1つでも欠けたら FAIL。「入れたつもりで入っていない」を機械で見つける。
SYN_POOL = {
    "1A": ["sv", "svc-adj", "svc-noun", "svo", "svoo-give", "svoo-take", "svoc-adj", "svoc-noun", "svoc-pp", "svoc-bare", "svoc-to"],
    "1B": ["relative-subject", "relative-object", "participle-postmod", "gerund-object", "adverb-intrusion", "long-fronted-pp", "participial-construction", "pp-postmod", "comparative-postmod"],
    "1C": ["formal-subject", "formal-object", "that-clause-object", "whether-clause", "there-construction", "passive", "perception-verb", "causative", "group-verb"],
    "2": ["so-that-result", "too-to", "infinitive-adjective", "relative-possessive", "that-of", "compound-relative", "do-emphasis", "insertion", "superlative-equivalent", "only-inversion", "subjunctive-inversion", "ellipsis-clause"],
    "3-1": ["prep-relative", "relative-adverb", "what-clause", "chain-relative", "nonrestrictive", "appositive-that", "as-if"],
    "3-2": ["not-so-much-as", "no-more-than", "comparative-ellipsis", "the-more-the-more", "negative-inversion", "cleft", "no-sooner-than"],
    "3-3": ["with-absolute", "inanimate-subject", "nominalization", "subjunctive", "correlative", "concessive-as", "neither-nor"],
}

# ---------------------------------------------------------------- 第1部 SVOCM 判別
PART1 = [
    {"g": "Ａ　5文型の骨格を見抜く", "sub": "第1〜第5文型／M を混ぜて骨組みだけを取り出す", "pool": "1A", "items": [
        {"id": "A1",
         "syn": "sv",
         "en": "The timber bridge over the narrow ravine shakes slightly whenever a loaded truck passes.",
         "dsl": "{S:The timber bridge} < M: over the narrow ravine > {V:shakes} {M:slightly} ( M: {接:whenever} {S':a loaded truck} {V':passes} ) .",
         "pat": "第1文型（SV）",
         "tag": "第1文型 SV（O も C も無い）",
         "notes": [
                   "急所は S と V の間。The timber bridge のうしろに &lt;M: over the narrow ravine &gt; が割り込むので、"
                   "ravine を主語だと思うと V の相手を見失う。前置詞のうしろの名詞は主節の S になれない。",
                   "shakes は「〜を揺らす」とも読める動詞だが、うしろに名詞は無く {M:slightly} が続くだけである。O も C も無いのだから第1文型で確定する。",
                   "( M: whenever … ) は主節の外の副詞のカタマリ。中の {V':passes} を主節の V と数えると V が 2 つある文になってしまう。"
                   "主節の V は shakes ただ 1 つ。",
                   "&lt;M:&gt; と ( M: ) と {M:slightly} を外すと The timber bridge shakes という S と V の "
                   "2 つだけが残る。骨格を見抜くとは、ここまで削ぎ落とすことである。"],
         "ja": "その木造の橋は、荷を積んだトラックが通るたびに少し揺れる。"},
        {"id": "A2",
         "syn": "svc-adj",
         "en": "The water in the village reservoir stays cold even during the harshest weeks of summer.",
         "dsl": "{S:The water} < M: in the village reservoir > {V:stays} {C:cold} ( M: even during the harshest weeks < M': of summer > ) .",
         "pat": "第2文型（SVC）",
         "tag": "stay ＋ 形容詞の C",
         "notes": [
                   "急所は stays。「とどまる」という第1文型で切ってしまうと、そのあとの cold が行き場を失う。stay は be の仲間で、うしろの形容詞は S "
                   "の状態を述べる C になる。",
                   "S の核は The water だけ。&lt;M: in the village reservoir &gt; を S のマスに抱え込むと、S がどこまでかを答えられなくなる。"
                   "前置詞句は必ず外へ出す。",
                   "cold は名詞ではないので O にはなれない。O か C かは品詞だけで切れることがあり、形容詞が来たならそれは必ず C である。",
                   "( M: even during … ) は時を表す副詞のカタマリ。外しても The water stays cold は崩れないので、骨格の 3 点には数えない。"],
         "ja": "その村の貯水池の水は、夏のいちばん厳しい時期でさえ冷たいままだ。"},
        {"id": "A3",
         "syn": "svc-noun",
         "en": "The derelict lot behind the station has become a thriving community garden in recent years.",
         "dsl": "{S:The derelict lot} < M: behind the station > {V:has become} {C:a thriving community garden} ( M: in recent years ) .",
         "pat": "第2文型（SVC）",
         "tag": "become ＋ 名詞の C",
         "notes": [
                   "急所は has become のうしろ。名詞が来ると O に見えるが、become は目的語を取らない動詞なので、この名詞は C しかありえない。",
                   "C が名詞のときは S ＝ C が立つかで確かめる。「荒れた空き地」＝「にぎわう共同菜園」で等号が成り立つので、O ではなく C と決まる。",
                   "has become は完了の have ＋ 過去分詞で 1 つの述語。has を別のマスにせず {V:has become} と 1 マスに握るのが約束である。",
                   "&lt;M: behind the station &gt; は The derelict lot を後ろから説明する形容詞のカタマリ、( M: in recent "
                   "years ) は動詞にかかる副詞。働きが違うので括弧の形も変える。"],
         "ja": "駅の裏の荒れた空き地は、ここ数年でにぎわう共同菜園になっている。"},
        {"id": "A4",
         "syn": "svo",
         "en": "Persistent spring rain often delays the onset of the rice planting season by several weeks.",
         "dsl": "{S:Persistent spring rain} {M:often} {V:delays} {O:the onset} < M: of the rice planting season > ( M: by several weeks ) .",
         "pat": "第3文型（SVO）",
         "tag": "delays は名詞ではなく V",
         "notes": [
                   "急所は delays。「遅れ」という名詞にも見えるが、直前に {M:often} があり、副詞は名詞を修飾しない。だから delays はこの文の V である。",
                   "O の核は the onset だけ。&lt;M: of the rice planting season &gt; を O のマスに抱え込むと、O がどこで終わるかを言えなくなる。"
                   "of 句は外へ出す。",
                   "delays のうしろの名詞は S の言い換えではない。「雨 ＝ 始まり」という等号は立たないので、C ではなく O、つまり第3文型と決まる。",
                   "( M: by several weeks ) は「どれだけ遅らせるか」を言う副詞で、名詞にかかる &lt;M:&gt; とは別物。外しても O の中身は変わらない。"],
         "ja": "春の長雨は、田植えの時期の始まりを数週間も遅らせることが多い。"},
        {"id": "A5",
         "syn": "svo",
         "en": "A single tactless remark can wreck the atmosphere of an entire negotiation within seconds.",
         "dsl": "{S:A single tactless remark} {V:can wreck} {O:the atmosphere} < M: of an entire negotiation > ( M: within seconds ) .",
         "pat": "第3文型（SVO）",
         "tag": "can ＋ 動詞は 1 つのマス",
         "notes": [
                   "急所は can wreck。助動詞と動詞は切り離さず 1 つの V のマスに入れる。can だけを別に数えると、V が 2 つあるように見えてしまう。",
                   "the atmosphere は wreck の相手なので O。「発言 ＝ 雰囲気」という等号は立たないから C ではなく、ここで第3文型が確定する。",
                   "&lt;M: of an entire negotiation &gt; は the atmosphere にかかる。of 句をマスの中に入れたままだと "
                   "O の核が 1 つに絞れない。",
                   "&lt;M:&gt; と ( M: ) の使い分けは「直前の名詞にかかるか、動詞にかかるか」で決める。within seconds は台無しにする速さを言うので "
                   "( M: ) になる。"],
         "ja": "たった一言の心ない発言が、交渉全体の雰囲気を数秒で台無しにしてしまうことがある。"},
        {"id": "A6",
         "syn": "svoo-give",
         "en": "The principal promised the guardians a detailed account without any evasion.",
         "dsl": "{S:The principal} {V:promised} {O1:the guardians} {O2:a detailed account} ( M: without any evasion ) .",
         "pat": "第4文型（SVOO）",
         "tag": "promise O1 O2（授与型）",
         "notes": [
                   "急所は promised のうしろに名詞が 2 つ並ぶこと。the guardians と a detailed account の間に主語述語の関係は立たないので、"
                   "第5文型ではなく O1 O2 の第4文型である。",
                   "人が先・物があとという並びが授与型の目印。前後を入れ替えるなら promised a detailed account to the guardians "
                   "となり、to が必要になる。",
                   "promise は that 節も取る動詞で、promised that … なら O が 1 つだけの第3文型になる。動詞だけで決めず、うしろの形を見てから文型を決めること。",
                   "( M: without any evasion ) は promised のしかたを言う副詞。外しても S V O1 O2 の 4 つは残るので骨格には数えない。"],
         "ja": "校長は、少しも言葉を濁さずに、保護者たちに詳しい説明をすると約束した。"},
        {"id": "A7",
         "syn": "svoo-take",
         "en": "The prolonged delay at the terminal cost the squad an entire day of rehearsal.",
         "dsl": "{S:The prolonged delay} < M: at the terminal > {V:cost} {O1:the squad} {O2:an entire day} < M: of rehearsal > .",
         "pat": "第4文型（SVOO）",
         "tag": "cost O1 O2（奪う型の第4文型）",
         "notes": [
                   "急所は cost。原形と過去形が同じ形なので動詞に見えにくいが、{S:The prolonged delay} を受ける述語はこれしかない。まず V を "
                   "1 つに決めること。",
                   "cost のうしろも名詞が 2 つで第4文型だが、O2 は与えられたものではなく失われたものである。第4文型を「授与」だけで覚えていると読めない。",
                   "the squad と an entire day の間に主語述語の関係は立たない。立たないので第5文型ではなく O1 O2 と決まる。A6 と同じ手順で切り分ける。",
                   "&lt;M: at the terminal &gt; は The prolonged delay に、&lt;M: of rehearsal &gt; "
                   "は an entire day にかかる。どちらも直前の名詞にかかるので ( M: ) にはしない。"],
         "ja": "空港での長引いた遅れのせいで、その一団は丸一日の練習を失った。"},
        {"id": "A8",
         "syn": "svoc-adj",
         "en": "The abrupt outage left the entire commercial district completely dark last Friday evening.",
         "dsl": "{S:The abrupt outage} {V:left} {O:the entire commercial district} {C:completely dark} ( M: last Friday evening ) .",
         "pat": "第5文型（SVOC）",
         "tag": "leave O C（C が形容詞）",
         "notes": [
                   "急所は left。「去った」と取ると the entire commercial district が行き先に見えるが、そうすると completely "
                   "dark が宙に浮いてしまう。",
                   "leave O C は「O を C の状態のまま残す」。C が形容詞なので第5文型で、O と C の間には district is dark という関係が隠れている。",
                   "dark は名詞ではないので O2 にはなれない。うしろの 2 つ目が名詞なら第4文型、形容詞なら第5文型と、品詞のところで分かれる。",
                   "( M: last Friday evening ) はいつの出来事かを言う副詞。外すと S V O C の 4 点だけが一直線に並び、骨格が見える。"],
         "ja": "先週の金曜の夜、突然の停電が商業地区全体を真っ暗にした。"},
        {"id": "A9",
         "syn": "svoc-noun",
         "en": "The society members elected a retired diplomat their new chairperson at the annual assembly.",
         "dsl": "{S:The society members} {V:elected} {O:a retired diplomat} {C:their new chairperson} ( M: at the annual assembly ) .",
         "pat": "第5文型（SVOC）",
         "tag": "elect O C（C が名詞）",
         "notes": [
                   "急所は elected のうしろの名詞 2 つ。a retired diplomat と their new chairperson は同じ人を指すので、"
                   "O1 O2 ではなく O と C である。",
                   "第4文型なら 2 つの名詞は別物になる（A6 の the parents と a full report）。ここは「＝」で結べるかどうかが分かれ目になる。",
                   "elect O C は「O を C に選ぶ」。as が無くても C で、elect O as C とも書けることが名詞の C だと見抜く目印になる。",
                   "( M: at the annual assembly ) は選出が行われた場面を言う副詞。骨格の S V O C の 4 つを数えるときは先に外して考える。"],
         "ja": "協会の会員たちは、年次総会で、退職した外交官を新しい会長に選んだ。"},
        {"id": "A10",
         "syn": "svoc-pp",
         "en": "A thick layer of volcanic ash can keep buried seeds almost perfectly preserved for centuries.",
         "dsl": "{S:A thick layer} < M: of volcanic ash > {V:can keep} {O:buried seeds} {C:almost perfectly preserved} ( M: for centuries ) .",
         "pat": "第5文型（SVOC）",
         "tag": "keep O C（C が過去分詞）",
         "notes": [
                   "急所は keep の型。keep O C は「O を C の状態のままにしておく」。「保つ」と訳して O だけで切ると almost perfectly "
                   "preserved が宙に浮く。",
                   "keep は O だけでも使える動詞で、keep the receipt / keep a spare key なら「取っておく」の意味になる。ここは C "
                   "が無いと「火山灰が種をしまっておく」となって意味が立たないので第5文型と決まる。",
                   "C が過去分詞のときは O との間に受動の関係が立つかを見る。seeds are preserved が成り立つので almost perfectly preserved "
                   "は C である。",
                   "O の中の buried は seeds にかかる飾りで骨格には数えない。&lt;M: of volcanic ash &gt; と ( M: for centuries "
                   ") を外せば S V O C の 4 つだけが残る。"],
         "ja": "厚く積もった火山灰は、埋もれた種を何世紀ものあいだほぼ完全な状態のまま保つことがある。"},
        {"id": "A11",
         "syn": "svoc-bare",
         "en": "An unforeseen shift in the weather can make even seasoned climbers doubt their own judgment.",
         "dsl": "{S:An unforeseen shift} < M: in the weather > {V:can make} {O:even seasoned climbers} [ C: {V':doubt} {O':their own judgment} ] .",
         "pat": "第5文型（SVOC）",
         "tag": "make O C（C が原形不定詞）",
         "notes": [
                   "急所は doubt。to も ing も付かない裸の原形が並ぶので V が 2 つあるように見えるが、これは make が取る C である。",
                   "make のうしろに名詞が 2 つ並ぶ形なら第4文型もありうるが、2 つ目が原形のときは第5文型に限られる。品詞を見た時点で第4文型は消える。",
                   "C が動詞を含むので平のマス 1 つでは置かず、[ C: {V':doubt} {O':their own judgment} ] と囲んで中まで分解する。"
                   "囲みの中なのでダッシュが 1 本付く。",
                   "&lt;M: in the weather &gt; は An unforeseen shift にかかる形容詞のカタマリ。S のマスに巻き込むと S の核が言えなくなる。"],
         "ja": "天候の思いがけない変化は、経験を積んだ登山者にさえ自分の判断を疑わせることがある。"},
        {"id": "A12",
         "syn": "svoc-to",
         "en": "Most drama academies now expect applicants with no stage experience to prepare two contrasting monologues.",
         "dsl": "{S:Most drama academies} {M:now} {V:expect} {O:applicants} < M: with no stage experience > [ C: {V':to prepare} {O':two contrasting monologues} ] .",
         "pat": "第5文型（SVOC）",
         "tag": "expect O to do（C が to 不定詞）",
         "notes": [
                   "急所は to prepare。「用意するために」と副詞に取ると、expect applicants で終わる第3文型に見えてしまう。",
                   "applicants prepare two contrasting monologues という主語述語の関係が立つので、この不定詞は O に対する C である。",
                   "C が動詞を含むので [ C: {V':to prepare} {O':two contrasting monologues} ] と囲む。A11 の原形の "
                   "C と書き方をそろえるのが約束である。",
                   "O と C の間に &lt;M: with no stage experience &gt; が挟まっても expect O to do の型は変わらない。"
                   "{M:now} と合わせて外せば骨格が並ぶ。"],
         "ja": "たいていの演劇学校は今や、舞台経験の無い志願者にも対照的な独白を二つ用意してくることを求める。"},
    ]},
    {"g": "Ｂ　修飾語 M を切り離す", "sub": "S と V が修飾で引き離されている形", "pool": "1B", "items": [
        {"id": "B1",
         "syn": "relative-subject",
         "en": "Volunteers who have worked at an animal sanctuary for years can calm a distressed dog in minutes.",
         "dsl": "{S:Volunteers} < M: {S':who} {V':have worked} ( M': at an animal sanctuary ) ( M': for years ) > {V:can calm} {O:a distressed dog} ( M: in minutes ) .",
         "pat": "第3文型（SVO）／主語に関係詞節",
         "tag": "主格の関係代名詞（who）が S と V を割る",
         "notes": [
                   "急所は who。関係詞がそのまま節の中の S' の働きをするので、&lt;M: who … for years &gt; の内側にもう一つ主語を置く場所は無い。"
                   "have worked を主節の V と数えると、後ろの can calm が主語を失って余る。",
                   "飾りの &lt;M: … &gt; を丸ごと外すと Volunteers can calm a distressed dog が残る。calm は他動詞で直後の "
                   "a distressed dog が O、( M: in minutes ) は外しても文が立つ副詞なので骨組みは第3文型。",
                   "関係詞節は先行詞の直後で始まり、節の中で完結する。for years まで来ると節が閉じるので、そこから先に出てくる can calm が主節の V だと決まる。"
                   "動詞の個数ではなく、囲みの内側か外側かで切る。",
                   "規約1 のとおり助動詞は動詞と同じマスなので {V:can calm} は 1 マス。( M': at an animal sanctuary ) と ( "
                   "M': for years ) はどちらも関係詞節の内側の副詞で、ダッシュ 1 本がその深さを示している。"],
         "ja": "動物保護区で何年も働いてきたボランティアは、おびえきった犬を数分で落ち着かせることができる。"},
        {"id": "B2",
         "syn": "relative-object",
         "en": "The furniture that the previous tenant abandoned in the cellar now fills the cramped entrance hall.",
         "dsl": "{S:The furniture} < M: {O':that} {S':the previous tenant} {V':abandoned} ( M': in the cellar ) > {M:now} {V:fills} {O:the cramped entrance hall} .",
         "pat": "第3文型（SVO）／主語に関係詞節",
         "tag": "目的格の関係代名詞（that）が S と V を割る",
         "notes": [
                   "that の後ろは the previous tenant abandoned と続き、abandoned の目的語が空いている。その空所に The furniture "
                   "が入るので、この that は目的格の関係代名詞 {O':that} である。接続詞の that だと読むと空所を説明できない。",
                   "誤読の急所は abandoned。過去形が二つ並んでいるように見えるが、abandoned は &lt;M: … &gt; の中の V' で、主節の V "
                   "は fills のほう。単数扱いの The furniture に fills が対応している点も手がかりになる。",
                   "( M': in the cellar ) は関係詞節の内側の副詞。ここで文が終わったと思い込むと S の The furniture が動詞を持たないまま残る。"
                   "飾りを外すと The furniture now fills the cramped entrance hall となり第3文型と分かる。",
                   "{M:now} は S と V の間に入った副詞で骨組みには数えない。目的格の関係代名詞は省略もできるので、名詞のあとにいきなり別の名詞と動詞が続いたら、"
                   "まず空所を探す癖をつける。"],
         "ja": "前の借り手が地下貯蔵室に置き去りにした家具が、今では小さな玄関ホールを埋めている。"},
        {"id": "B3",
         "syn": "participle-postmod",
         "en": "Cooking methods devised in rural households centuries ago still offer modern chefs a valuable lesson.",
         "dsl": "{S:Cooking methods} < M: {V':devised} ( M': in rural households ) ( M': centuries ago ) > {M:still} {V:offer} {O1:modern chefs} {O2:a valuable lesson} .",
         "pat": "第4文型（SVOO）／主語に過去分詞の後置修飾",
         "tag": "過去分詞の後置修飾が S と V を割る",
         "notes": [
                   "Cooking methods devised までを読むと「調理法が発展した」という S と V にそのまま見える。これがいちばん多い誤読で、後ろの still "
                   "offer が主語を失うことで初めて破綻に気づく。",
                   "-ed が飾りか主節の V かは、直前に be があるかどうかでは決まらない。決め手は「別に定形動詞が残るか」で、ここは現在形の offer が残るので "
                   "developed のほうが過去分詞 {V':developed} と確定する。",
                   "&lt;M: developed … centuries ago &gt; を丸ごと外し、さらに {M:still} も外すと Cooking methods "
                   "offer modern chefs a valuable lesson が残る。人（O1: modern chefs）と物（O2: a valuable "
                   "lesson）が続くので第4文型と判定できる。",
                   "規約4 のとおり &lt; &gt; の中の分詞は素の語で置かず {V':developed} と示す。同じ過去分詞でも B7 の Faced は文全体にかかるので "
                   "( M ) になる。かかる先が名詞か文かで括弧の種類が変わる。"],
         "ja": "何世紀も前に農村の家庭で生まれた調理法は、今なお現代の料理人に貴重な教訓を与えてくれる。"},
        {"id": "B4",
         "syn": "gerund-object",
         "en": "Students at the summer immersion camp practice introducing themselves in English every single morning.",
         "dsl": "{S:Students} < M: at the summer immersion camp > {V:practice} [ O: {V':introducing} {O':themselves} ( M': in English ) ] ( M: every single morning ) .",
         "pat": "第3文型（SVO）／目的語が動名詞句",
         "tag": "動名詞句が O（practice doing）",
         "notes": [
                   "急所は practice。名詞にも動詞にもなる語なので the summer immersion camp practice を一つの名詞のかたまりと読みたくなるが、"
                   "そう読むと文全体に定形動詞が一つも残らない。残らないと分かった時点で practice が主節の V と決まる。",
                   "introducing は直前に be が無いので進行形ではない。practice の目的語になった動名詞で、[ O: {V':introducing} "
                   "{O':themselves} ( M': in English ) ] という名詞のカタマリ一つぶんがそのまま O のマスに収まる。",
                   "&lt;M: at the summer immersion camp &gt; は S の Students を後ろから説明する形容詞のカタマリ。外すと "
                   "Students practice … と S と V が隣り合うので、骨組みが第3文型だと確かめられる。",
                   "-ing が名詞のカタマリなら [ ]、名詞にかかる飾りなら &lt; &gt;、文にかかる飾りなら ( ) と括弧を変える。( M: every single "
                   "morning ) は practice にかかる副詞なので骨組みには数えない。"],
         "ja": "その夏の語学キャンプの生徒たちは、毎朝欠かさず英語で自己紹介をする練習をしている。"},
        {"id": "B5",
         "syn": "adverb-intrusion",
         "en": "The publisher, after nearly two years of silence, abruptly sent the young translator a lucrative contract.",
         "dsl": "{S:The publisher} , ( M: after nearly two years < M': of silence > ) , {M:abruptly} {V:sent} {O1:the young translator} {O2:a lucrative contract} .",
         "pat": "第4文型（SVOO）／S と V の間に副詞句が割り込む",
         "tag": "S と V の間に割り込む副詞句",
         "notes": [
                   "急所は二つのコンマに挟まれた ( M: after nearly two years of silence )。S の The publisher と V "
                   "の sent の間に割り込んだ副詞のカタマリで骨組みではない。直前の silence を主語と読むと、動詞 sent に主語が二つできてしまう。",
                   "割り込みを外すと The publisher abruptly sent the young translator a lucrative contract "
                   "が残る。人（O1: the young translator）と物（O2: a lucrative contract）が並ぶので第4文型で、{M:suddenly} "
                   "も外して数えない副詞である。",
                   "&lt;M': of silence &gt; は two years にかかる形容詞のカタマリで、( M ) の内側の飾り。ダッシュ 1 本が「一枚内側」を表しているので、"
                   "外の骨格には数えないと記号だけで分かる。",
                   "文頭に出る副詞句（B6 の Behind …）も S と V の間に入る副詞句も、働きは同じ M。位置ではなく「外しても文が立つか」で M かどうかを決めると、"
                   "コンマの数に惑わされない。"],
         "ja": "その出版社は、二年近く何の連絡もないまま過ぎたあと、出し抜けにその若い翻訳者に好条件の契約書を送ってきた。"},
        {"id": "B6",
         "syn": "long-fronted-pp",
         "en": "Behind the tall barriers of the demolition site, several ancient fruit trees have survived the winter.",
         "dsl": "( M: Behind the tall barriers < M': of the demolition site > ) , {S:several ancient fruit trees} {V:have survived} {O:the winter} .",
         "pat": "第3文型（SVO）／文頭に長い前置詞句",
         "tag": "文頭の長い前置詞句（Behind …）",
         "notes": [
                   "前置詞 Behind の目的語である the tall barriers も、その後ろの the demolition site も S にはなれない。前置詞句の中の名詞を主語と読むのが最大の誤読で、"
                   "そう読むと後ろの have survived が行き場を失う。",
                   "( M: Behind … the demolition site ) を丸ごと外して初めて主節が見える。S は several ancient fruit "
                   "trees、V は have survived、O は the winter で第3文型。長い M の後ろに来る短い S はいちばん見落としやすい。",
                   "&lt;M': of the demolition site &gt; は the tall barriers にかかる形容詞のカタマリで、( M ) の内側の飾り。"
                   "囲みが二重になったら、内側の名詞は外の骨格の候補から外す。",
                   "文頭の長い前置詞句はコンマで「ここまでが飾り」と合図することが多い。コンマの後ろから S を探し、そこで見つけた名詞と対応する動詞を V に決める、という順番を固定しておく。"],
         "ja": "解体現場の高い仮囲いの裏側で、何本かの古い果樹が冬を越して生き残っている。"},
        {"id": "B7",
         "syn": "participial-construction",
         "en": "Faced with a chronic shortage of skilled labor, a growing number of manufacturers have begun training their own technicians.",
         "dsl": "( M: {V':Faced} ( M': with a chronic shortage < M'': of skilled labor > ) ) , {S:a growing number} < M: of manufacturers > {V:have begun} [ O: {V':training} {O':their own technicians} ] .",
         "pat": "第3文型（SVO）／文頭に分詞構文",
         "tag": "分詞構文（過去分詞 Faced with …）",
         "notes": [
                   "文頭の Faced は分詞構文で、( M: {V':Faced} … ) という文全体にかかる副詞。主語が書かれていないのは主節の S と同じだからで、ここに "
                   "S を探しても見つからない。Being が省かれた受け身だと考えると、本体はコンマの後ろに来ると分かる。",
                   "規約14 のとおり ( ) の中の分詞も素の語で置かず {V':Faced} と示す。B3 の developed が直前の名詞にかかる &lt;M&gt; "
                   "だったのに対し、こちらは文にかかるので ( M ) になる。かかる先の違いが括弧の違いになる。",
                   "S のマスは a growing number までで、of manufacturers は規約6 のとおり &lt;M: of manufacturers "
                   "&gt; として外へ出す。ただし数の一致はこの核では決まらない。a number of / a growing number of ＋複数名詞 は例外で、"
                   "動詞は of の後ろの複数名詞に合わせるので have begun（複数扱い）になる。核＝a growing number でも、数を決めているのは manufacturers のほうである。",
                   "V は have begun、O は名詞のカタマリ [ O: {V':training} {O':their own technicians} ]。begin "
                   "は動名詞を目的語に取れるのでこの一かたまりがそのまま O に収まる。training を進行形の一部と読まないこと。"],
         "ja": "熟練した働き手の不足に直面して、ますます多くの製造業者が自社の技術者を育て始めている。"},
        {"id": "B8",
         "syn": "pp-postmod",
         "en": "The coastal road between the harbor and the fishing hamlet becomes treacherous after prolonged rain.",
         "dsl": "{S:The coastal road} < M: between the harbor {接:and} the fishing hamlet > {V:becomes} {C:treacherous} ( M: after prolonged rain ) .",
         "pat": "第2文型（SVC）／主語に前置詞句が付く",
         "tag": "名詞に付く前置詞句（between A and B）",
         "notes": [
                   "S は The coastal road の三語だけ。between 以下が長いので、直前の the fishing hamlet を主語と見て becomes "
                   "を対応させる誤読が起きる。前置詞の後ろの名詞は S になれないと決めておけば防げる。",
                   "&lt;M: between the harbor and the fishing hamlet &gt; は road を後ろから説明する形容詞のカタマリ。"
                   "外すと The coastal road becomes treacherous が残り、becomes の後ろは O ではなく C なので第2文型。",
                   "{接:and} が結ぶのは the harbor と the fishing hamlet という二つの名詞で、文と文ではない。and の前後に同じ形が並んでいるかを見ると、"
                   "どこまでが一つの前置詞句なのかが決まる。",
                   "同じ前置詞句でも、名詞だけを説明するなら &lt; &gt;、文にかかるなら ( ) と書き分ける。( M: after prolonged rain ) "
                   "は becomes にかかる副詞なので ( ) に入れる。"],
         "ja": "港と漁村の集落を結ぶその海沿いの道は、長雨のあとにはきわめて危険になる。"},
        {"id": "B9",
         "syn": "comparative-postmod",
         "en": "A crowd far larger than the organizers had anticipated assembled quietly outside the main entrance.",
         "dsl": "{S:A crowd} < M: far larger ( M': {接:than} {S'':the organizers} {V'':had anticipated} ) > {V:assembled} {M:quietly} ( M: outside the main entrance ) .",
         "pat": "第1文型（SV）／主語に比較の句が付く",
         "tag": "比較の句が名詞を後ろから修飾する",
         "notes": [
                   "急所は than の節がどこで閉じるか。&lt;M: far larger ( M': than the organizers had anticipated "
                   ") &gt; までが A crowd の説明で、had anticipated を主節の V と読むと、後ろの gathered が主語を失って余ってしまう。",
                   "far larger は crowd を後ろから修飾する形容詞なので、than 以下まで込みで &lt; &gt; の一かたまりになる。飾りを外すと A "
                   "crowd assembled quietly outside the main entrance が残り、目的語が無いので第1文型。",
                   "than の後ろは the organizers had anticipated と主語と動詞がそろっているように見えるが、expected の目的語が空いている。"
                   "この空所こそ比較の節の目印で、空所がある節は主節の骨格には数えない。",
                   "{M:quietly} と ( M: outside the main entrance ) はどちらも gathered にかかる副詞。gathered "
                   "の後ろに名詞が一つも無いことを確かめてから第1文型と決めると、C や O と迷わない。"],
         "ja": "主催者が見込んでいたよりはるかに大きな人だかりが、正面入口の外に静かに集まった。"},
    ]},
    {"g": "Ｃ　誤読しやすい形", "sub": "形式主語・there 構文・受動態・知覚動詞・群動詞・whether", "pool": "1C", "items": [
        {"id": "C1",
         "syn": "formal-subject",
         "en": "It is no surprise that many first-time visitors lose their bearings in the labyrinth of alleys around the central bazaar.",
         "dsl": "{S:It} {V:is} {C:no surprise} [ 真S: {接:that} {S':many first-time visitors} {V':lose} {O':their bearings} ( M': in the labyrinth of alleys < M'': around the central bazaar > ) ] .",
         "pat": "第2文型（SVC）＋形式主語 It … 真S（that 節）",
         "tag": "形式主語 It … 真S（that 節）",
         "notes": [
                   "急所は文頭の It。「それは」と訳した瞬間に指す先が消える。中身を持たない仮の主語で、実体は後ろの [ 真S: that … ] にある。",
                   "[ 真S: … ] を丸ごと外すと It is no surprise だけが残る。is の後ろが名詞のカタマリなので、主節は S V C の第2文型と確定する。",
                   "対抗する読みは surprise にかかる同格の that 節。だが同格なら It が何かを指していなければならないのに、指す先が文中にも前にも無い。だから形式主語と決まる。",
                   "真S の中の骨組みは {S':many first-time visitors} と {V':lose} と {O':their way}。( M': in "
                   "the labyrinth of alleys &lt; M'': around the central bazaar &gt; ) は lose にかかる副詞のカタマリで、"
                   "骨組みには数えない。around the central bazaar は streets を後ろから説明するので、外に並べず内側に入れ子にする。"],
         "ja": "中央の市場のまわりの入り組んだ路地で、初めて訪れた人の多くが方角を見失うのは、驚くようなことではない。"},
        {"id": "C2",
         "syn": "formal-object",
         "en": "Centuries of rebuilding make it extremely difficult to date the earliest portions of a medieval fortress.",
         "dsl": "{S:Centuries} < M: of rebuilding > {V:make} {O:it} {C:extremely difficult} [ 真O: {V':to date} {O':the earliest portions} < M': of a medieval fortress > ] .",
         "pat": "第5文型（SVOC）＋形式目的語 it … 真O",
         "tag": "形式目的語 it … 真O",
         "notes": [
                   "make の直後の it を「それを」と訳さない。中身を持たない仮の目的語で、実体は文末の [ 真O: to date … ] にある。",
                   "並びは V(make) → O(it) → C(extremely difficult) → 真O。difficult を副詞のように読み流すと C が消え、"
                   "第5文型の骨組みが崩れる。",
                   "見抜き方は「it の後ろに形容詞か名詞が1つ余り、<b>さらに文末に to 不定詞か that 節が控えているか</b>」。両方そろったときだけ it は仮の目的語である。",
                   "主語の核は複数形の Centuries で、だから make に -s が付かない。&lt; M: of rebuilding &gt; を名詞のマスに抱え込むと、"
                   "rebuilding を主語の核と取り違える。ただし a number of / a growing number of ＋複数名詞 だけは例外で、この形のときは動詞を "
                   "of の後ろの複数名詞に合わせる。"],
         "ja": "何世紀にもわたる建て直しのせいで、中世の城塞の最も古い部分の年代を特定することは、きわめて難しくなっている。"},
        {"id": "C3",
         "syn": "that-clause-object",
         "en": "Some growers still maintain that the phase of the moon determines the best day for sowing beans.",
         "dsl": "{S:Some growers} {M:still} {V:maintain} [ O: {接:that} {S':the phase} < M': of the moon > {V':determines} {O':the best day} < M': for sowing beans > ] .",
         "pat": "第3文型（SVO）＋接続詞 that 節が O",
         "tag": "that 節が丸ごと O",
         "notes": [
                   "急所は that の後ろが欠けの無い完全な文であること。関係代名詞なら節の中で S か O が1つ欠ける。ここは接続詞で、節がまるごと believe の O になる。",
                   "[ O: … ] を外すと Some growers still maintain が残る。主節の V は believe ひとつで、節の中の determines "
                   "は V′ にすぎない。",
                   "節の中の S′ は the phase であって the moon ではない。&lt; M': of the moon &gt; を名詞のマスから外へ出すと、"
                   "determines に対応する主語がはっきり見える。",
                   "{M:still} は S と V の間に割り込んだ副詞で骨組みではない。副詞を M として外に置き、その次に来る believe を V の位置から動かさない。"],
         "ja": "月の満ち欠けが豆をまくのに一番よい日を決めると、いまだに信じている庭師もいる。"},
        {"id": "C4",
         "syn": "whether-clause",
         "en": "Experienced dealers cannot tell from a photograph alone whether a chair is a genuine antique or a skillful forgery.",
         "dsl": "{S:Experienced dealers} {V:cannot tell} ( M: from a photograph alone ) [ O: {接:whether} {S':a chair} {V':is} {C':a genuine antique} {接:or} {C':a skillful forgery} ] .",
         "pat": "第3文型（SVO）＋ whether の名詞節が O",
         "tag": "whether の名詞節が O",
         "notes": [
                   "whether を「たとえ〜であろうと」の譲歩（副詞のカタマリ）と読むと、他動詞 tell の目的語がどこにも残らない。この欠落が起きるので、ここは「〜かどうか」の名詞節で記号は O。",
                   "V の直後に ( M: from a photograph alone ) が割り込む。O を探すときは前置詞句を飛ばし、その次に現れる名詞のカタマリまで進むこと。",
                   "{接:or} は [ O: ] の中で {C':a genuine antique} と {C':a skillful forgery} を結んでいるだけ。"
                   "ここで文が切れて新しい S が始まると考えない。",
                   "「A か B か」と2つ並んでいても、whether から文末までで名詞のカタマリ1つぶん。[ O: ] は文末で閉じるので、主節の要素はこれ以上増えない。"],
         "ja": "経験を積んだ業者でも、写真だけでは、その椅子が本物の骨董品なのか、よくできた模造品なのかを見分けられない。"},
        {"id": "C5",
         "syn": "there-construction",
         "en": "There hung above the entrance of the abandoned mill a vast clock with only one hand.",
         "dsl": "{M:There} {V:hung} ( M: above the entrance < M': of the abandoned mill > ) {S:a vast clock} < M: with only one hand > .",
         "pat": "第1文型（SV）＋ there 構文（There は M、S は V の後ろ）",
         "tag": "there 構文（There は M）",
         "notes": [
                   "文頭の There は主語ではなく M。巻頭の表記規約にも「there 構文の There は M。実際の S は動詞の後ろの名詞」と書いてある。答案では "
                   "There に M と書く。",
                   "この文の S は V より後ろの a vast clock で、S と V の順序が入れ替わっている。「文頭の名詞が S」という思い込みだけで解くと必ず外す形である。",
                   "V(hung) と S の間に ( M: above the entrance &lt; M': of the abandoned mill &gt; ) "
                   "が割り込む。of the abandoned mill は entrance にかかるので内側に入れ子にする。ここで factory を主語と取ると、後ろの "
                   "clock が宙に浮いてしまう。",
                   "&lt; M: with only one hand &gt; は clock を後ろから説明する形容詞のカタマリ。hung にかかる副詞と取ると、S がどこで終わるのかが読めなくなる。"],
         "ja": "その打ち捨てられた製粉所の入口の上には、針が1本しかない巨大な時計が掛かっていた。"},
        {"id": "C6",
         "syn": "passive",
         "en": "In this secluded parish, the church bells are rung by hand on the morning of every festival.",
         "dsl": "( M: In this secluded parish ) , {S:the church bells} {V:are rung} ( M: by hand ) ( M: on the morning < M': of every festival > ) .",
         "pat": "第1文型（SV）＋受動態（be + 過去分詞で 1 つの V）",
         "tag": "受動態 be + 過去分詞",
         "notes": [
                   "急所は are rung を2つに割らないこと。受動の be と過去分詞は合わせて1つの V のマスに入れる。are を V、rung を C と読むと、"
                   "受動態を第2文型に誤判定する。",
                   "V の後ろに名詞のカタマリが1つも残っていない。だからこの文は O を持たず、骨組みは S と V だけの第1文型と決まる。",
                   "( M: by hand ) は動作主ではなく「手で」という方法を表す。受動態の by が必ず動作主だと決めてかかると、ここで S を探し直すことになる。",
                   "文頭の ( M: In this secluded parish ) は骨組みの外。コンマの後ろに現れる the church bells が主節の S "
                   "であって、village を S と取らない。"],
         "ja": "この人里離れた教区では、祭りの日の朝には教会の鐘が手で鳴らされる。"},
        {"id": "C7",
         "syn": "perception-verb",
         "en": "From the pier, the fishermen could see a thin column of smoke rise slowly into a windless sky.",
         "dsl": "( M: From the pier ) , {S:the fishermen} {V:could see} {O:a thin column} < M: of smoke > [ C: {V':rise} {M':slowly} ( M': into a windless sky ) ] .",
         "pat": "第5文型（SVOC）＋知覚動詞 see + O + 原形不定詞",
         "tag": "知覚動詞 see + O + 原形",
         "notes": [
                   "急所は rise に -s も to も付いていないこと。O の核 a thin line は単数だから、ふつうの述語動詞なら rises になる。これは知覚動詞が取る原形不定詞である。",
                   "{O:a thin line} と [ C: rise … ] の間に「line が rise する」という主述関係が立つ。だから rise 以下がまるごと "
                   "C で、文型は第5文型と決まる。",
                   "名詞のマスに of 句を抱えない。&lt; M: of smoke &gt; を外に出すと O の核が a thin line だと見え、その直後の rise "
                   "が C の先頭だと分かる。",
                   "{M':slowly} と ( M': into a windless sky ) は could see ではなく rise にかかる。C は原形不定詞のカタマリ1つで、"
                   "その修飾語も [ C: ] の内側に入れる。"],
         "ja": "桟橋から、漁師たちは細い一筋の煙の筋が風のない空へゆっくりと立ちのぼるのを見ることができた。"},
        {"id": "C8",
         "syn": "causative",
         "en": "An instructor at a reputable driving school has the learner recite each step of the parking maneuver aloud.",
         "dsl": "{S:An instructor} < M: at a reputable driving school > {V:has} {O:the learner} [ C: {V':recite} {O':each step} < M': of the parking maneuver > {M':aloud} ] .",
         "pat": "第5文型（SVOC）＋使役動詞 have + O + 原形不定詞",
         "tag": "使役動詞 have + O + 原形",
         "notes": [
                   "急所は has。完了の助動詞と読むなら後ろに過去分詞が要るが、describe は原形なので成り立たない。原形不定詞を C に取る使役の has である。",
                   "「指導員が学習者を持っている」と読むと describe 以下が宙に浮く。{O:the learner} と [ C: describe … ] の間に主述関係が立つので、"
                   "ここは第5文型。",
                   "C は動詞を含むカタマリなので平のマスに置かず [ C: ] で囲んで中まで分解する。&lt; M': of the parking maneuver &gt; "
                   "と {M':aloud} はどちらもその内側の要素である。",
                   "&lt; M: at a reputable driving school &gt; は instructor を後ろから説明する形容詞のカタマリ。S の核は "
                   "An instructor で、直前にあるからといって school を S と取らない。"],
         "ja": "よい自動車教習所の指導員は、学習者に駐車の一連の動きを一つ一つ声に出して口に出して言わせる。"},
        {"id": "C9",
         "syn": "group-verb",
         "en": "Several small dairy farms have taken advantage of the new railway in order to dispatch fresh produce into the city.",
         "dsl": "{S:Several small dairy farms} {V:have taken advantage of} {O:the new railway} ( M: in order {V':to dispatch} {O':fresh produce} ( M': into the city ) ) .",
         "pat": "第3文型（SVO）＋群動詞 take advantage of を 1 つの V に切る",
         "tag": "群動詞 take advantage of",
         "notes": [
                   "take advantage of は3語で1つの他動詞。of をふつうの前置詞として切ると the new railway が M になり、主節の O "
                   "が消えて第1文型に見えてしまう。",
                   "1マスにまとめてよいかは受動態にできるかで試す。The new railway has been taken advantage of. が成り立つので群動詞と確定する。"
                   "成り立たない「動詞＋前置詞句」なら前置詞句は M として外に出す。",
                   "完了の have は V と同じマスに入れる決まりなので、V のマスは have taken advantage of までで1つ。have を別の番号として切り出さない。",
                   "in order to と書いてあるので to send は目的を表す副詞用法で確定する。( M: ) の中身なので、send を主節の V と数えないこと。"],
         "ja": "小さな酪農場のいくつかは、新しい鉄道をうまく利用して、新鮮な牛乳を街へ送っている。"},
    ]},
]

# ---------------------------------------------------------------- 第2部 構造判断の4択
PART2 = [
    {"id": "G1",
     "syn": "so-that-result",
     "en": "The consultant spoke in such a subdued voice that several patients asked her to reiterate the discharge instructions twice.",
     "dsl": "{S:The consultant} {V:spoke} ( M: in such a subdued voice ) ( M: {接:that} {S':several patients} {V':asked} {O':her} [ C': {V'':to reiterate} {O'':the discharge instructions} {M'':twice} ] ) .",
     "pat": "第1文型（SV）",
     "tag": "結果を表す such … that",
     "notes": [
               "such の直後で名詞のカタマリが終わらず that 節が続いたら、結果を表す so / such … that の呼応を疑う。",
               "speak は say や tell と違って that 節を目的語に取れないので、後ろの that 節は O ではなく副詞のカタマリ ( M ) として並ぶ。",
               "主節の骨組みは The consultant と spoke の 2 つだけで、残りはすべて ( M ) の修飾語である。",
               "that 節の中の asked her to repeat は O と C を取る第5文型。C は動詞を含むので囲んで中も分解する。"],
     "ja": "その専門医はあまりに抑えた声で話したので、何人かの患者は退院時の説明をもう一度述べ直してほしいと彼女に頼んだ。",
     "q": "that several patients asked her to reiterate the discharge instructions twice は、この文でどのような働きをしているか。"
          "最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "in such a subdued voice と呼応し、その結果どうなったかを述べる副詞のカタマリ",
                 "spoke の目的語となり、看護師が話した内容そのものを表す名詞のカタマリ",
                 "a quiet voice を後ろから説明し、どのような声だったかを限定する形容詞のカタマリ",
                 "The consultant を後ろから説明し、どのような看護師なのかを限定する形容詞のカタマリ"],
     "ans": 0,
     "exp": "such a subdued voice の such と、後ろの that 節が呼応している。in such a subdued voice ほど静かな声だった、その結果どうなったかを述べるのが "
            "that 以下で、分解図でも V の外に並ぶ 2 つ目の ( M ) になる。speak は say や tell と違って that 節を目的語に取れないので、that "
            "節を O と読むと置き場所がなく、主節が第3文型に化けてしまうので誤り。a quiet voice を後ろから説明する形容詞のカタマリと取ると、声そのものの中身を that "
            "節が述べることになり、患者が頼んだという別の出来事の説明にならないので誤り。The consultant にかかると取ると、that 節との間に spoke in such "
            "a subdued voice がまるごと挟まっており、名詞から遠く離れた that 節がその名詞を限定することはないので誤り。"},
    {"id": "G2",
     "syn": "too-to",
     "en": "The young sprinter was too apprehensive about her start to run the opening fifty meters at her customary pace.",
     "dsl": "{S:The young sprinter} {V:was} {C:too apprehensive about her start} ( M: {V':to run} {O':the opening fifty meters} ( M': at her customary pace ) ) .",
     "pat": "第2文型（SVC）",
     "tag": "too … to の否定的な意味",
     "notes": [
               "too … to … は否定語を使わずに「…すぎて〜できない」を表す。to の前で切って程度を読む。",
               "was の後ろの too apprehensive about her start は主語の状態を述べる C で、この文は第2文型である。",
               "to run 以下は名詞にかかる形容詞ではなく、too と呼応して程度と結果を示す副詞のカタマリになる。",
               "anxious about のように形容詞が呼び出す前置詞は、C のマスの中に残したまま 1 かたまりで見る。"],
     "ja": "その若いスプリンターはスタートを不安に思いすぎていて、最初の五十メートルをいつもの調子で走ることができなかった。",
     "q": "この文の主節の文型として最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "was が V で、too apprehensive about her start を O にとる第3文型である",
                 "was が V で、too apprehensive about her start が C にあたる第2文型である",
                 "was が V で、her start が O、to run 以下が C にあたる第5文型である",
                 "was が V で、その後ろに O も C も無く修飾語だけが続く第1文型である"],
     "ans": 1,
     "exp": "was の後ろの too apprehensive about her start は、主語がどういう状態かを述べる補語なので、この文は第2文型である。too … to "
            "… は否定語を使わずに「…すぎて〜できない」を表す形で、to run 以下は too と呼応して程度と結果を示す副詞のカタマリになる。O と取ると、be 動詞が目的語を取ることになり、"
            "しかも主語と同じものを指す関係が説明できないので誤り。her start を O、to run 以下を C と取ると、彼女のスタートが走るという意味になってしまい、was "
            "を第5文型の動詞として使うことになるので誤り。O も C も無い第1文型と取ると、was だけでは文の意味が完結せず、too apprehensive about her "
            "start の置き場所が消えるので誤り。"},
    {"id": "G3",
     "syn": "infinitive-adjective",
     "en": "In a typical school term, learners of a second language rarely have a genuine opportunity to use it spontaneously outside the classroom.",
     "dsl": "( M: In a typical school term ) , {S:learners} <M: of a second language> {M:rarely} {V:have} {O:a genuine opportunity} <M: {V':to use} {O':it} {M':spontaneously} ( M': outside the classroom ) > .",
     "pat": "第3文型（SVO）",
     "tag": "不定詞の形容詞用法",
     "notes": [
               "名詞の直後の to 不定詞は、その名詞を後ろから説明する形容詞のはたらきをすることが多い。",
               "目的の副詞と読むと a genuine opportunity が何の機会か決まらない。名詞に不足が残る側を選ぶ。",
               "to 不定詞のカタマリに入るのは副詞 naturally と前置詞句 outside the classroom で、どちらも use にかかる。文頭の In a "
               "typical school term はこのカタマリの外にあり、主節の have にかかる。",
               "of a second language は learners の核から外に出し、名詞にかかる形容詞のカタマリとして示す。"],
     "ja": "ふつうの学期のうちのうちに、第二言語の学習者が、教室の外でそれを自然に口をついて使う本物の機会を持つことはめったにない。",
     "q": "to use it spontaneously outside the classroom は、どの語にかかっているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "have にかかり、何のために機会を持つのかという目的を表している",
                 "learners にかかり、どのような学習者なのかを後ろから説明している",
                 "a genuine opportunity にかかり、どのような機会なのかを後ろから説明している",
                 "a second language にかかり、その言語がどう使われるかを説明している"],
     "ans": 2,
     "exp": "名詞の直後に置かれた to 不定詞は、その名詞を後ろから説明する形容詞のはたらきをする。ここでも to use it spontaneously outside the "
            "classroom は直前の a genuine opportunity にかかり、どういう機会が乏しいのかを述べている。have にかかる目的の副詞と取ると、機会を持つ目的が言語を使うことになり、"
            "a genuine opportunity が何の機会なのか決まらないまま残るので誤り。learners にかかると取ると、間に rarely have a genuine "
            "opportunity がまるごと挟まっており、離れた名詞に後ろからかかることはないので誤り。a second language にかかると取ると、of で始まるカタマリの中の名詞に文末までのカタマリがかかることになり、"
            "it が指すものと重なって意味が回らなくなるので誤り。なお文頭の In a typical school term は主節の have にかかる ( M ) で、to "
            "不定詞のカタマリの中には入らない。"},
    {"id": "G4",
     "syn": "relative-possessive",
     "en": "Last Sunday the newspaper belatedly retracted a report whose opening paragraph had named the wrong thoroughfare.",
     "dsl": "( M: Last Sunday ) {S:the newspaper} {M:belatedly} {V:retracted} {O:a report} <M: {S':whose opening paragraph} {V':had named} {O':the wrong thoroughfare} > .",
     "pat": "第3文型（SVO）",
     "tag": "所有格の関係代名詞 whose",
     "notes": [
               "whose は所有格の関係代名詞で、直前の名詞と後ろの名詞を「〜の」で結びつける。",
               "whose の後ろには冠詞の無い名詞が直接続き、その名詞が関係詞節の主語や目的語になる。",
               "関係詞節の中で主語も目的語も欠けていないのが所有格の目印。欠けがあれば主格か目的格である。",
               "文頭の Last Sunday はいつの話かを示す ( M ) で、主語ではない。主語は the newspaper である。"],
     "ja": "先週の日曜日、その新聞は遅ればせながら、書き出しの段落が間違った通りの名前を挙げていた記事を撤回した。",
     "q": "whose opening paragraph の whose について、最も適切な説明を 1 つ選びなさい。",
     "choices": [
                 "the newspaper を受け、その新聞社の書き出しの段落、という関係を示す",
                 "疑問詞で、誰の書き出しの段落かを尋ねる間接疑問をつくっている",
                 "who is の短縮で、後ろの opening paragraph が補語になっている",
                 "a report を受け、その記事の書き出しの段落、という所有の関係を示す"],
     "ans": 3,
     "exp": "whose は所有格の関係代名詞で、直前の名詞と、後ろに続く名詞との間に「〜の」という関係をつくる。ここでは直前の a report を受けており、whose opening "
            "paragraph は、その記事の書き出しの段落、という意味になる。この段落が had named の主語になり、関係詞節の中で主語が欠けていないことも所有格の目印である。"
            "the newspaper を受けると取ると、whose は直前の名詞を受けるのが原則で、間にある名詞をまたいで遠くの名詞を受けることはないので誤り。疑問詞と取ると、corrected "
            "の目的語は a report ですでに埋まっており、間接疑問を入れる場所が無いので誤り。who is の短縮と取ると、後ろに続くのは名詞で補語にはならず、had named "
            "の主語も消えるので誤り。"},
    {"id": "G5",
     "syn": "that-of",
     "en": "Under the refurbished lighting, the colors of the restored fresco look appreciably brighter than those of the unrestored section.",
     "dsl": "( M: Under the refurbished lighting ) , {S:the colors} <M: of the restored fresco> {V:look} {C:appreciably brighter} ( M: {接:than} {S':those} <M': of the unrestored section> ) .",
     "pat": "第2文型（SVC）",
     "tag": "比較の代用 those of",
     "notes": [
               "比較の相手をそろえるために、前に出た名詞のくり返しを that / those で置き換える。複数なら those を使う。",
               "those の直後の of the unrestored section まで含めて、比べる相手 1 つ分のカタマリになる。",
               "文頭の Under the refurbished lighting は比較の相手ではなく、どんな条件での話かを示す ( M ) である。",
               "look は第2文型を作る動詞で、far brighter が C。far は比較級を強める副詞で C の中に残す。"],
     "ja": "改修された照明の下では、修復された壁画の色は、修復されていない部分の色よりも目に見えて明るく見える。",
     "q": "than those of the unrestored section の those は何を指しているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "the restored fresco を受けており、修復した天井そのものと比べていることを示す",
                 "the new lighting を受けており、新しい照明の明るさと比べていることを示す",
                 "the colors を受けており、修復していない部分の色と比べていることを示す",
                 "the colors of the restored fresco 全体を受け、同じ天井の色をもう一度指している"],
     "ans": 2,
     "exp": "those は前に出た名詞のくり返しを避ける代用の語で、ここでは the colors を受けている。than those of the unrestored section "
            "は、the colors of the restored fresco と、修復していない部分の色とを比べる形で、比べる相手をそろえるためにこの those が要る。the "
            "restored fresco を受けると取ると、色と天井という違うものを比べることになり、brighter が何について明るいのか決まらないので誤り。the new "
            "lighting を受けると取ると、Under the refurbished lighting は文全体の条件を示す副詞のカタマリで比較の相手ではないので誤り。the "
            "colors of the restored fresco の全体を受けると取ると、同じものどうしを比べることになり、比較そのものが成り立たなくなるので誤り。"},
    {"id": "G6",
     "syn": "compound-relative",
     "en": "Whatever the tribunal decides at tomorrow's hearing will affect the shift patterns of every employee in the plant.",
     "dsl": "[ S: {O':Whatever} {S':the tribunal} {V':decides} ( M': at tomorrow's hearing ) ] {V:will affect} {O:the shift patterns} <M: of every employee <M': in the plant> > .",
     "pat": "第3文型（SVO）",
     "tag": "複合関係代名詞 whatever",
     "notes": [
               "Whatever は先行詞を自分の中に含む複合関係代名詞で、節の全体が名詞のカタマリになる。",
               "コンマが無く、後ろの will affect に主語が無い。だから譲歩ではなく主語の名詞節だと決まる。",
               "カタマリの中では Whatever が decides の目的語。中に目的語の欠けがあることが見分けの手がかり。",
               "of every employee は the shift patterns の核から外に出し、名詞にかかる形容詞のカタマリとして示す。"],
     "ja": "審査会が明日の審理で決めることは何であれ、工場のすべての従業員の勤務の割り振りに影響する。",
     "q": "この文の主節の主語 (S) にあたるのはどれか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "the committee で、決定を下す側の名詞がそのまま主節の動作主として働いている",
                 "Whatever の 1 語で、後ろの the tribunal decides はコンマの無い挿入である",
                 "the shift patterns で、will affect の後ろに置かれた名詞が主語である",
                 "Whatever the tribunal decides at tomorrow's hearing の全体で、これが名詞のカタマリとして主語になっている"],
     "ans": 3,
     "exp": "Whatever は先行詞を自分の中に含む複合関係代名詞で、Whatever the tribunal decides at tomorrow's hearing の全体が "
            "1 つの名詞のカタマリになり、will affect の主語として働く。カタマリの中では Whatever が decides の目的語で、決められる中身そのものを指している。"
            "the committee を主語と取ると、Whatever が宙に浮き、しかも decides と will affect という 2 つの述語を 1 つの主語が支えることになるので誤り。"
            "Whatever の 1 語だけを主語と取ると、後ろの部分が挿入になるが、挿入はコンマなどで区切るのが普通で、ここにはその印が無いので誤り。the shift patterns "
            "を主語と取ると、動詞の後ろの名詞を主語と読むことになり、動詞の前に主語が無い文になってしまうので誤り。"},
    {"id": "G7",
     "syn": "do-emphasis",
     "en": "The ancient statute does permit itinerant traders to remain in the square until midnight on the eve of the winter festival.",
     "dsl": "{S:The ancient statute} {V:does permit} {O:itinerant traders} [ C: {V':to remain} ( M': in the square ) ( M': until midnight ) ( M': on the eve <M'': of the winter festival> ) ] .",
     "pat": "第5文型（SVOC）",
     "tag": "強調の do",
     "notes": [
               "強調の do は、過去でも疑問でも否定でもない場所に現れ、直後に動詞の原形を連れてくる。",
               "does permit は 1 つのマスにまとめる。助動詞は動詞と同じマスに入れるのがこの教材の約束である。",
               "allow は O と to 不定詞の C を取る第5文型。C は動詞を含むので囲んで中まで分解する。",
               "三単現の s が allow ではなく does に付き、直後が原形になっている点も強調の do の目印である。"],
     "ja": "その古い条例は、冬の祭りの夜、行商人が広場に真夜中までいることを確かに認めている。",
     "q": "does permit の does はどのような働きをしているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "allow を強め、確かに認めているのだという肯定の意味を押し出している",
                 "疑問文をつくる助動詞で、後ろの語順が疑問文と同じになっている",
                 "否定の not が省かれた形で、実際には認めていないことを示している",
                 "allow の代わりに置かれた代動詞で、前に出た動詞を受け直している"],
     "ans": 0,
     "exp": "does permit の does は、後ろの動詞の意味を強める強調の do で、確かに認めているのだ、という肯定の押しを加える。過去でも疑問でも否定でもないのに do "
            "が現れ、しかも直後に原形の allow が続いたら、この用法を疑う。疑問文をつくる助動詞と取ると、The ancient statute does permit は主語が先に来ており疑問文の語順ではないので誤り。"
            "not が省かれた形と取ると、否定語は省略できず、補ってしまうと後半の内容と矛盾するので誤り。代動詞と取ると、代動詞はくり返しを避けるために動詞を置かない形で使うのに、"
            "ここでは allow が実際に書かれているので誤り。"},
    {"id": "G8",
     "syn": "insertion",
     "en": "The autumn gales along this coast, most local fishermen say, inflict far less damage than the sudden fogs of early spring.",
     "dsl": "{S:The autumn gales} <M: along this coast> , ( 挿入: {S':most local fishermen} {V':say} ) , {V:inflict} {O:far less damage} ( M: {接:than} {S':the sudden fogs} <M': of early spring> ) .",
     "pat": "第3文型（SVO）",
     "tag": "コンマにはさまれた挿入",
     "notes": [
               "コンマ 2 つにはさまれた S と V の組は、話し手以外の判断を差し込む挿入で、骨組みには数えない。",
               "挿入を取り去っても文が成り立つかどうかで見分ける。残った側の動詞が主節の V である。",
               "The autumn gales は複数なので、対応するのは三単現の形ではない cause である。動詞の形も手がかり。",
               "along this coast は直前の名詞を後ろから説明する形容詞のカタマリで、主語 1 つ分に含めて読む。"],
     "ja": "この海岸沿いの秋の暴風は、地元の漁師の多くが言うには、早春の突然の霧よりもはるかに小さな被害しかもたらさない。",
     "q": "この文の主節の動詞 (V) にあたるのはどれか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "say で、most local fishermen を主語にとり文全体をまとめている",
                 "cause で、コンマにはさまれた挿入をまたいで主語を受けている",
                 "cause と say が対等に並び、2 つの動詞が 1 つの主語を共有している",
                 "cause は不定詞相当で、実際の主節の動詞はコンマの中の say である"],
     "ans": 1,
     "exp": "コンマにはさまれた most local fishermen say は、話し手以外の判断を差し込む挿入で、主節の骨組みからは外れている。この部分を取り去ると、The "
            "autumn gales along this coast が主語、cause が動詞という骨組みが残る。say を主節の動詞と取ると、コンマの外に残る主語が述語を失い、"
            "cause の置き場所も無くなるので誤り。cause と say が対等に並ぶと取ると、対等な並列には接続詞が要るうえ、コンマ 2 つで囲む形にもならないので誤り。cause "
            "を不定詞相当と取ると、to も付いておらず、主語に対する述語がどこにも無い文になるので誤り。"},
    {"id": "G9",
     "syn": "superlative-equivalent",
     "en": "No other dish on the menu demands as much precision as the fish stew that the proprietor serves on Fridays.",
     "dsl": "{S:No other dish} <M: on the menu> {V:demands} {O:as much precision} ( M: {接:as} {S':the fish stew} <M': {O'':that} {S'':the proprietor} {V'':serves} ( M'': on Fridays ) > ) .",
     "pat": "第3文型（SVO）",
     "tag": "最上級と同じ内容を表す形",
     "notes": [
               "No other に単数の名詞が続き、後ろで as … as と比べる形は、最上級と同じ内容を表す。",
               "比べているのは requires の程度で、as much precision as の後ろが比較の相手になる。",
               "as の後ろは the fish stew までで、その後の that 節はどのシチューかを絞る形容詞のカタマリである。",
               "on the menu は直前の No other dish を後ろから説明し、比べる範囲を示している。"],
     "ja": "献立のほかのどの料理も、店主が金曜日に出すその魚のシチューほどの手間を必要としない。",
     "q": "この文は内容としてどのようなことを述べているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "献立の中ではこの魚のシチューがいちばん手間のかかる料理だということ",
                 "この魚のシチューと同じだけ手間のかかる料理がほかにもあるということ",
                 "この魚のシチューは金曜日以外には手間をかけずに作られるということ",
                 "料理長は献立のどの料理にも同じだけの手間をかけているということ"],
     "ans": 0,
     "exp": "No other dish on the menu demands as much precision as the fish stew は、このシチュー以外のどの料理もこれほどの手間はかからない、"
            "と述べており、最上級と同じ内容になる。だから、いちばん手間がかかるのはこの魚のシチューだということになる。同じだけ手間のかかる料理がほかにもあると取ると、文頭の No "
            "other がほかの料理をすべて外しているので誤り。金曜日以外は手間をかけないと取ると、on Fridays は the proprietor serves にかかり、"
            "いつ出すかを言っているだけなので誤り。どの料理にも同じだけの手間をかけていると取ると、比較そのものが打ち消され、as much precision as という形が意味を失うので誤り。"},
    {"id": "G10",
     "syn": "only-inversion",
     "en": "Only at the very end of the announcement did the station personnel mention the alteration to the evening timetable.",
     "dsl": "( M: Only at the very end < M': of the announcement > ) {助:did} {S:the station personnel} {V:mention} {O:the alteration} <M: to the evening timetable> .",
     "pat": "第3文型（SVO）",
     "tag": "Only … による倒置",
     "notes": [
               "Only で始まる副詞句が文頭に出ると、後ろは疑問文と同じ語順になり、助動詞が主語の前に出る。",
               "did の後ろの名詞が主語。助動詞と動詞が主語をはさんで割れている形だと見抜く。",
               "倒置なので did の後ろの動詞は原形の mention になる。時制は did が背負っていると読む。",
               "文頭の Only at the very end … は副詞 Only ＋前置詞句のカタマリで、名詞のカタマリではないから主語になれない。"],
     "ja": "アナウンスのいちばん最後になってようやく、駅の係員は夕方の時刻表の変更について口にした。",
     "q": "did the station personnel mention という語順になっているこの文の主語 (S) はどれか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "Only at the very end で、文頭の副詞句がそのまま主語になっている",
                 "the announcement で、of の後ろの名詞が主語の働きをしている",
                 "the station personnel で、文頭の Only … に引かれて did の後ろに回っている",
                 "the change で、mention の後ろに置かれた名詞が主語になっている"],
     "ans": 2,
     "exp": "文頭に Only … の限定句が出ると、後ろは疑問文と同じ語順になる。ここでも助動詞の did が主語の前に飛び出しており、did の後ろに置かれた the station "
            "personnel が主節の主語である。did を取り除いて動詞を過去形に戻せば、普通の語順に戻る。Only at the very end を主語と取ると、これは副詞 "
            "Only ＋前置詞句のカタマリで名詞のカタマリではなく主語になれず、did の後ろの名詞が浮いてしまうので誤り。the announcement を主語と取ると、of "
            "の後ろの名詞は直前の名詞を説明しているだけで、文の主語にはなれないので誤り。the change を主語と取ると、これは mention の目的語で、何を口にしたのかを表す名詞なので誤り。"},
    {"id": "G11",
     "syn": "subjunctive-inversion",
     "en": "Had the ledger been discovered fifty years earlier, the chronicle of the estate would have taken a markedly different shape.",
     "dsl": "( M: {助:Had} {S':the ledger} {V':been discovered} ( M': fifty years earlier ) ) , {S:the chronicle} <M: of the estate> {V:would have taken} {O:a markedly different shape} .",
     "pat": "第3文型（SVO）",
     "tag": "if の省略による倒置",
     "notes": [
               "仮定法の if 節は、if を落として助動詞や be 動詞を主語の前に出す倒置の形にできる。",
               "文頭が Had で、後ろに主語と過去分詞が続いたら、疑問文ではなく仮定法過去完了の倒置を疑う。",
               "主節が would have taken という形になっていることが、仮定法過去完了だと確かめる裏づけになる。",
               "of the village は the story の核から外に出し、名詞にかかる形容詞のカタマリとして示す。"],
     "ja": "その帳簿が五十年早く見つかっていたら、そのその地所の記録は目に見えて違った形になっていただろう。",
     "q": "文頭の Had the ledger been discovered について、省略されている語の説明として最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "When が省かれ、日記が見つかった時期を述べる副詞節になっている",
                 "疑問文の Did が Had に変わったもので、省略されている語は無い",
                 "Because が省かれ、後半の内容の理由を述べる副詞節になっている",
                 "If が省かれ、その埋め合わせに Had が主語の前に出た仮定法の形である"],
     "ans": 3,
     "exp": "仮定法の条件節では、if を省いて助動詞や be 動詞を主語の前に出すことができる。ここも文頭の if が消え、had が主語の前に回って Had the ledger "
            "been discovered という形になっている。主節が would have taken という形であることも手がかりになる。When が省かれたと取ると、時を表す節では倒置は起こらず、"
            "実際に見つかったという事実の話になってしまうので誤り。疑問の Did が変化した形と取ると、コンマの後ろに主節が続いており疑問文になっていないので誤り。Because "
            "が省かれたと取ると、理由の節も倒置しないうえ、事実を述べる文と読むと主節の形と合わないので誤り。"},
    {"id": "G12",
     "syn": "ellipsis-clause",
     "en": "Although rewritten repeatedly before publication, the novella still retains the ending that its author first envisaged.",
     "dsl": "( M: {接:Although} {V':rewritten} ( M': repeatedly ) ( M': before publication ) ) , {S:the novella} {M:still} {V:retains} {O:the ending} <M: {O':that} {S':its author} {M':first} {V':envisaged} > .",
     "pat": "第3文型（SVO）",
     "tag": "副詞節中の S + be の省略",
     "notes": [
               "接続詞の直後にいきなり過去分詞が来たら、主語と be 動詞が省かれた副詞節を疑う。",
               "省けるのは主節の主語と同じ場合だけで、ここでは the short novel を受ける主語と be 動詞が省かれている。",
               "分詞は素の語で置かず、副詞節の中の動詞として示す。省略があっても節の骨組みは変わらない。",
               "the ending の後ろの that は関係代名詞で、imagined の目的語が欠けているので目的格だと分かる。"],
     "ja": "出版の前に繰り返し書き直されたけれども、その中編小説は作者が最初に思い描いた結末を今も保っている。",
     "q": "Although rewritten repeatedly before publication では、Although の直後に何が省略されているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "people have にあたる主語と助動詞で、書き直した人のほうが主語になっている",
                 "it was にあたる主語と be 動詞で、主節の主語と同じものを指している",
                 "there is にあたる形式的な主語と be 動詞で、存在を表す形になっている",
                 "to be にあたる不定詞で、これから書き直される予定を表す形になっている"],
     "ans": 1,
     "exp": "Although の直後にいきなり過去分詞の rewritten が来ているのは、副詞節の主語と be 動詞が省かれているからである。省かれているのは主節の主語と同じもの、"
            "つまり the short novel を受ける it was で、これを戻すと普通の副詞節になる。people have が省かれていると取ると、能動で補うなら目的語が要るのに "
            "rewritten の後ろに名詞が無いので誤り。there is が省かれていると取ると、存在を表す形では rewritten が宙に浮き、書き直されたのが何なのか決まらないので誤り。"
            "to be が省かれていると取ると、接続詞の後ろに不定詞だけを置く形は無く、これから書き直される予定という読みは、書き直したうえで今の形が残っているという文全体の流れとも合わないので誤り。"},
]

# ---------------------------------------------------------------- 第3部 英文解釈
PART3 = [
    {"g": "①　関係詞と接続", "sub": "かかり先を決める", "pool": "3-1", "items": [
        {"id": "D1",
         "syn": "prep-relative",
         "en": "The care with which the archaeologists recorded each layer of sediment made the later excavation far easier.",
         "dsl": "{S:The care} <M: ( M': with which ) {S':the archaeologists} {V':recorded} {O':each layer} <M': of sediment > > {V:made} {O:the later excavation} {C:far easier} .",
         "pat": "第5文型（SVOC）",
         "tag": "前置詞 + 関係代名詞",
         "notes": [
                   "急所は with which。前置詞つきの関係代名詞で、直前の The care にかかる形容詞のカタマリを作る。",
                   "&lt;M: with which … sediment &gt; を外すと The care made the later excavation far "
                   "easier が残る。O と C が並ぶ第5文型である。",
                   "recorded の主語は the archaeologists であって The care ではない。カタマリの中の S′ V′ を主節と数えないこと。",
                   "前置詞を動詞に戻して recorded each layer with that care と読み直すと、with which のかかり方が見える。"],
         "ja": "考古学者たちが堆積層を一つ一つ記録した丁寧さが、のちの発掘をはるかに容易にした。",
         "points": [
                    "with which を The care にかけ、「〜した丁寧さ」と一つの名詞のかたまりとして訳せている",
                    "made A B を第5文型で「A を B にした」と訳せている（「作った」と訳していない）",
                    "主節の主語が The care であって the archaeologists ではないと分かる訳になっている"]},
        {"id": "D2",
         "syn": "relative-adverb",
         "en": "Few researchers have explained the reason why vaccination rates fall so sharply once an epidemic appears to be over.",
         "dsl": "{S:Few researchers} {V:have explained} {O:the reason} <M: {M':why} {S':vaccination rates} {V':fall} {M':so sharply} ( M': {接:once} {S'':an epidemic} {V'':appears} [ C'': {V'':to be} {C'':over} ] ) > .",
         "pat": "第3文型（SVO）",
         "tag": "関係副詞 why",
         "notes": [
                   "急所は why。疑問詞ではなく、直前の the reason にかかる関係副詞である。後ろは要素の欠けていない完全な文になる。",
                   "欠けがあれば関係代名詞、無ければ関係副詞。ここは rates fall と S′ V′ がそろっているので関係副詞と決まる。",
                   "Few は「ほとんど〜ない」という準否定。not が無くても文全体が否定になる点を落とさない。",
                   "appears to be over の to be は appears の補語。動詞を含むので [ C: ] で囲んで中まで分解する。"],
         "ja": "流行がおさまったように見えたとたんに接種率がこれほど急に落ちる理由を、説明した研究者はほとんどいない。",
         "points": [
                    "the reason why を「〜する理由」と一つの名詞のかたまりとして訳せている",
                    "Few researchers have explained を「説明した研究者はほとんどいない」と準否定で訳せている",
                    "once を「いったん〜すると／〜したとたんに」と接続詞として訳せている"]},
        {"id": "D3",
         "syn": "what-clause",
         "en": "What distinguishes a lasting settlement from a temporary one is a willingness to concede something visible to the other side.",
         "dsl": "[ S: {S':What} {V':distinguishes} {O':a lasting settlement} ( M': from a temporary one ) ] {V:is} {C:a willingness} <M: {V':to concede} {O':something visible} ( M': to the other side ) > .",
         "pat": "第2文型（SVC）",
         "tag": "関係代名詞 what が主語",
         "notes": [
                   "急所は文頭の What。疑問詞ではなく先行詞を含む関係代名詞で、節の全体が名詞のカタマリになって主語になる。",
                   "カタマリの中で What は distinguishes の主語を兼ねている。だから節の中に主語の欠けがある。",
                   "[ S: What … truce ] を一つの名詞として握れば、残るのは is と a willingness だけで第2文型だと見える。",
                   "to concede 以下は a willingness にかかる形容詞のカタマリ。「譲る意思」と、後ろから前へ返して訳す。one は settlement "
                   "の繰り返しを避ける代名詞。"],
         "ja": "長続きする和解を一時的なものと分けるのは、目に見える何かを相手側に譲ろうとする意思である。",
         "points": [
                    "What を「〜するもの・こと」と訳し、節の全体を主語として訳せている",
                    "distinguish A from B を「A を B と区別する」と訳せている",
                    "to concede 以下を a willingness にかけ、「〜しようとする意思」と訳せている"]},
        {"id": "D4",
         "syn": "chain-relative",
         "en": "The witness whom the detectives believed was entirely reliable later admitted that he had fabricated the crucial testimony.",
         "dsl": "{S:The witness} <M: {S':whom} ( 挿入: {S'':the detectives} {V'':believed} ) {V':was} {C':entirely reliable} > {M:later} {V:admitted} [ O: {接:that} {S':he} {V':had fabricated} {O':the crucial testimony} ] .",
         "pat": "第3文型（SVO）",
         "tag": "連鎖関係代名詞",
         "notes": [
                   "急所は関係詞の直後に the detectives believed が割り込むこと。この形を連鎖関係代名詞と呼ぶ。",
                   "割り込んだ部分を ( 挿入: ) で囲んで外すと The witness was entirely reliable が残る。関係詞が受けているのは was "
                   "の主語のほうである。",
                   "だから本来は who が正しく、whom は口語でよく見る形である。<b>believed の目的語ではない</b>と見抜くのが要点。",
                   "主節の V は admitted ただ一つ。believed も was も had fabricated もカタマリの中の V′ である。"],
         "ja": "刑事たちがまったく信用できると思っていたその証人は、のちに決定的な証言を作り上げていたことを認めた。",
         "points": [
                    "the detectives believed を挿入として読み、「刑事たちが〜と思っていた証人」と訳せている",
                    "was entirely reliable の主語が the witness だと分かる訳になっている（刑事が信用できる、と訳していない）",
                    "had fabricated を過去完了で「作り上げていた」と、認めた時点より前の話として訳せている"]},
        {"id": "D5",
         "syn": "nonrestrictive",
         "en": "The council delayed the ballot for another month, which angered the residents who had petitioned for years.",
         "dsl": "{S:The council} {V:delayed} {O:the ballot} ( M: for another month ) , <M: {S':which} {V':angered} {O':the residents} <M': {S'':who} {V'':had petitioned} ( M'': for years ) > > .",
         "pat": "第3文型（SVO）",
         "tag": "非制限用法の which",
         "notes": [
                   "急所はコンマ + which。直前の名詞ではなく、<b>前の内容全体</b>を受けることがある。ここは「投票を延期したこと」を受けている。",
                   "the ballot を受けると読むと「投票用紙が住民を怒らせた」となって意味が通らない。何を受けるかは意味で決める。",
                   "コンマの無い制限用法なら直前の名詞にかかる。コンマの有無で受けるものが変わる点が急所である。",
                   "&lt;M': who had petitioned for years &gt; は the residents にかかる。which 節の中なので、この節のラベルはダッシュを一本、"
                   "その中の要素は二本にする。"],
         "ja": "議会は投票をもう一か月先延ばしにしたが、そのことが何年も請願を続けてきた住民たちを怒らせた。",
         "points": [
                    "which が「投票を先延ばしにしたこと」という前の内容全体を受けていると分かる訳になっている",
                    "delay を「先延ばしにする・遅らせる」と訳せている",
                    "who had petitioned for years を the residents にかけ、過去完了で「請願を続けてきた」と訳せている"]},
        {"id": "D6",
         "syn": "appositive-that",
         "en": "The assumption that rapid economic growth inevitably reduces inequality has been undermined by several recent studies.",
         "dsl": "{S:The assumption} [ 同格: {接:that} {S':rapid economic growth} {M':inevitably} {V':reduces} {O':inequality} ] {V:has been undermined} ( M: by several recent studies ) .",
         "pat": "第1文型（SV）",
         "tag": "同格の that 節",
         "notes": [
                   "急所は that。後ろが growth reduces inequality と要素の欠けていない完全な文なので、関係代名詞ではなく同格の接続詞である。",
                   "名詞の欠けがあれば関係代名詞。この見分けが要点で、同格なら [ 同格: … ] で名詞のカタマリとして囲む。",
                   "has been undermined は受動態で、be + 過去分詞をまとめて一つの V と数える。後ろに名詞が無いので第1文型になる。",
                   "The assumption と that 節は「＝」の関係。「〜という思い込み」と、後ろから前へ返して訳す。"],
         "ja": "急速な経済成長は必ず格差を縮めるという思い込みは、最近のいくつかの研究によって揺らいでいる。",
         "points": [
                    "that 節を The assumption と同格に取り、「〜という思い込み」と訳せている",
                    "has been undermined を受動態で「揺らがされている・掘り崩されている」と訳せている（能動で訳していない）",
                    "inevitably を reduces にかけて「必ず・どうしても」と訳せている"]},
        {"id": "D7",
         "syn": "as-if",
         "en": "The minister answered every question as if the erosion of the coastline had been entirely unforeseeable.",
         "dsl": "{S:The minister} {V:answered} {O:every question} ( M: {接:as if} {S':the erosion} <M': of the coastline > {V':had been} {C':entirely unforeseeable} ) .",
         "pat": "第3文型（SVO）",
         "tag": "as if + 仮定法過去完了",
         "notes": [
                   "急所は as if の後ろの had been。主節が過去形 answered なのに、さらに一つ古い形になっている。",
                   "これは仮定法過去完了で、<b>事実に反する</b>ことを表す。実際には予見できたのに、できなかったかのように話した、という含みが出る。",
                   "as if の節は全体で answered にかかる副詞のカタマリ。外しても The minister answered every question は成立する。",
                   "the erosion に付く of the coastline は名詞にかかるので &lt;M'&gt; として外に出す。動詞にかかる ( M ) と区別する。"],
         "ja": "その大臣は、まるで海岸線の侵食がまったく予見できないことであったかのように、すべての質問に答えた。",
         "points": [
                    "as if + 仮定法過去完了を「まるで〜であったかのように」と、事実に反する含みを出して訳せている",
                    "the erosion of the coastline を「海岸線の侵食」と、of 句を erosion にかけて訳せている",
                    "unforeseeable を「予見できない」と、否定の接頭辞を訳出できている"]},
    ]},
    {"g": "②　比較・倒置・強調", "sub": "何と何を比べているか／なぜ語順が崩れたか", "pool": "3-2", "items": [
        {"id": "E1",
         "syn": "not-so-much-as",
         "en": "The value of a long apprenticeship lies not so much in the skills it transmits as in the habits of patience it builds.",
         "dsl": "{S:The value} <M: of a long apprenticeship > {V:lies} ( M: not so much in the skills <M': {O'':it} {V'':transmits} > ) ( M: {接:as} in the habits <M': of patience <M'': {O'':it} {V'':builds} > > ) .",
         "pat": "第1文型（SV）",
         "tag": "not so much A as B",
         "notes": [
                   "急所は not so much A as B。「A というより B」で、<b>not は文全体を否定していない</b>。「価値が無い」ではない。",
                   "A と B は形をそろえて並ぶ。ここは in the skills … と in the habits … で、どちらも前置詞句である。",
                   "lies は自動詞で O も C も取らない。二つの ( M ) を外すと The value lies だけが残り、第1文型と決まる。",
                   "it transmits と it builds はどちらも直前の名詞にかかる関係詞節で、関係代名詞が省略されている。"],
         "ja": "長い徒弟修業の価値は、それが伝える技術にあるというよりは、それが育てる忍耐の習慣にある。",
         "points": [
                    "not so much A as B を「A というよりむしろ B」と訳せている（「A ではない」と全否定にしていない）",
                    "A と B が in the skills … と in the habits … という同じ形の前置詞句だと分かる訳になっている",
                    "it transmits / it builds を関係代名詞の省略と見て、それぞれ skills / habits にかけて訳せている"]},
        {"id": "E2",
         "syn": "no-more-than",
         "en": "A pupil who has memorized a single formula is no more a mathematician than a tourist with a phrasebook is fluent.",
         "dsl": "{S:A pupil} <M: {S':who} {V':has memorized} {O':a single formula} > {V:is} {C:no more a mathematician} ( M: {接:than} {S':a tourist} <M': with a phrasebook > {V':is} {C':fluent} ) .",
         "pat": "第2文型（SVC）",
         "tag": "no more A than B",
         "notes": [
                   "急所は no more A than B。「B でないのと同じく A でない」という<b>両方を否定する</b>形である。",
                   "than の後ろに「明らかに成り立たない例」を置き、それと同じだと言うことで A を否定する。これが鯨構文と呼ばれる型。",
                   "than 節の中は a tourist is fluent という完全な文。比較の than は接続詞で、関係代名詞ではない。",
                   "&lt;M: who has memorized a single formula &gt; を外すと A student is no more a mathematician "
                   "が残り、第2文型と分かる。"],
         "ja": "公式を一つ暗記した生徒が数学者でないのは、会話帳を持った旅行者が流暢でないのと同じである。",
         "points": [
                    "no more A than B を「B でないのと同じく A でない」と、両方を否定する形で訳せている",
                    "than 以下を「会話帳を持った旅行者が流暢である」という成り立たない例として訳せている",
                    "who has memorized a single formula を A student にかけて訳せている"]},
        {"id": "E3",
         "syn": "comparative-ellipsis",
         "en": "Archivists learn far more from the manuscripts that survive by accident than they do from those that were deliberately preserved.",
         "dsl": "{S:Archivists} {V:learn} {O:far more} ( M: from the manuscripts <M': {S'':that} {V'':survive} ( M'': by accident ) > ) ( M: {接:than} {S':they} {V':do} ( M': from those <M'': {S'':that} {助:were} {M'':deliberately} {V'':preserved} > ) ) .",
         "pat": "第3文型（SVO）",
         "tag": "比較の節内の代動詞 do",
         "notes": [
                   "急所は than they do。この do は learn の繰り返しを避ける<b>代動詞</b>で、than 節が完全な文であることの目印になる。",
                   "比べているのは「偶然残った写本から学ぶ量」と「意図して保存された写本から学ぶ量」。何と何を比べるかを先に決める。",
                   "those は the manuscripts の繰り返しを避ける代名詞。前に出た複数名詞を受けるので that ではなく those になる。",
                   "were preserved は受動態。ただし deliberately が割り込んでいるので、助動詞の were を 助 として分け、副詞は M にする。"],
         "ja": "文書管理者は、意図して保存された写本からよりも、偶然残った写本からのほうがはるかに多くを学ぶ。",
         "points": [
                    "than they do の do を learn の代動詞と見て、「〜から学ぶよりも」と訳せている",
                    "比較の対象が「偶然残った写本」と「意図して保存された写本」だと分かる訳になっている",
                    "those が the manuscripts を受けていると分かる訳になっている"]},
        {"id": "E4",
         "syn": "the-more-the-more",
         "en": "The longer a government delays an unpopular reform, the heavier the compensation it eventually pays becomes.",
         "dsl": "( M: {M':The longer} {S':a government} {V':delays} {O':an unpopular reform} ) , {C:the heavier} {S:the compensation} <M: {O':it} {M':eventually} {V':pays} > {V:becomes} .",
         "pat": "第2文型（SVC）",
         "tag": "the 比較級, the 比較級",
         "notes": [
                   "急所は前半と後半が両方とも the + 比較級で始まること。「〜すればするほど…」という決まった形である。",
                   "後半は補語が文頭に出た<b>前置</b>で、S と V の順序は入れ替わっていない。助動詞が主語の前に出る倒置とは別物。",
                   "後半の骨組みは the compensation becomes the heavier。C を後ろに戻してから訳すと関係が見える。",
                   "&lt;M: it eventually pays &gt; は the compensation にかかる関係詞節で、関係代名詞が省略されている。"],
         "ja": "政府が不人気な改革を先延ばしにすればするほど、最終的に払う代償は重くなる。",
         "points": [
                    "the 比較級, the 比較級 を「〜すればするほど…」と訳せている",
                    "後半の主語が the compensation、述語が becomes だと分かる訳になっている",
                    "it eventually pays を関係代名詞の省略と見て the compensation にかけて訳せている"]},
        {"id": "E5",
         "syn": "negative-inversion",
         "en": "At no point during the inquiry did the official contradict the testimony he had given to the authorities.",
         "dsl": "( M: At no point <M': during the inquiry > ) {助:did} {S:the official} {V:contradict} {O:the testimony} <M: {S':he} {V':had given} ( M': to the authorities ) > .",
         "pat": "第3文型（SVO）",
         "tag": "否定の副詞句が文頭に出る倒置",
         "notes": [
                   "急所は did。過去の話なのに contradict が原形なのは、否定の副詞句が文頭に出て疑問文の語順になったからである。",
                   "倒置を戻すと The official did not contradict … となる。<b>否定を担っているのは文頭の At no point</b> "
                   "で、not は表に出ない。",
                   "did と contradict の間に主語が割り込んでいるので、助動詞を 助 として分ける。",
                   "&lt;M: he had given to the authorities &gt; は the testimony にかかる関係詞節で、関係代名詞が省略されている。"],
         "ja": "取り調べのあいだ、その担当者は当局に話していた証言を一度も変えなかった。",
         "points": [
                    "倒置を戻して「その担当者は一度も〜しなかった」と、否定として訳せている",
                    "At no point を「一度も〜ない」と訳し、否定を担う語だと分かる訳になっている",
                    "he had given to the authorities を the testimony にかけ、過去完了で「話していた」と訳せている"]},
        {"id": "E6",
         "syn": "cleft",
         "en": "It was the careless wording of the announcement, not the ruling itself, that provoked the strongest protest.",
         "dsl": "{S:It} {V:was} {C:the careless wording} <M: of the announcement > , ( 挿入: not the ruling itself ) , [ 強調: {接:that} {V':provoked} {O':the strongest protest} ] .",
         "pat": "第2文型（SVC）",
         "tag": "強調構文 It is ... that",
         "notes": [
                   "急所は It was … that の枠。<b>It が何かを指しているわけではない</b>ので、形式主語とも違う。",
                   "強調されている語句を枠から外すと The careless wording of the announcement provoked the strongest "
                   "protest という一つの文に戻る。",
                   "that の後ろは主語が欠けている。欠けた分が枠の中に引き出されているので、that 以下は [ 強調: ] で囲む。",
                   "コンマで挟まれた not the ruling itself は挿入で、「裁定そのものではなく」と対比を補っている。"],
         "ja": "最も強い抗議を引き起こしたのは、裁定そのものではなく、その発表の不用意な言い回しだった。",
         "points": [
                    "It was … that を強調構文と見て、「〜したのは…だった」と訳せている（「それは〜だった」と訳していない）",
                    "not the ruling itself を挿入の対比として「裁定そのものではなく」と訳せている",
                    "provoked の主語が the careless wording だと分かる訳になっている"]},
        {"id": "E7",
         "syn": "no-sooner-than",
         "en": "No sooner had the magazine printed the correction than the original claim began spreading again on social media.",
         "dsl": "( M: No sooner ) {助:had} {S:the magazine} {V:printed} {O:the correction} ( M: {接:than} {S':the original claim} {V':began} [ O': {V'':spreading} {M'':again} ( M'': on social media ) ] ) .",
         "pat": "第3文型（SVO）",
         "tag": "No sooner ... than",
         "notes": [
                   "急所は文頭の No sooner。否定の副詞が前に出たので、後ろが had + 主語 + 過去分詞という疑問文の語順になる。",
                   "No sooner … than … は「〜するやいなや…」。<b>than と組で一つの形</b>なので、比較の than と混同しない。",
                   "前半のほうが時間的に先。had printed と過去完了になっているのは、than 以下の began より前だからである。",
                   "began spreading は「〜し始めた」。動名詞句が began の目的語になるので [ O: ] で囲んで中まで分解する。"],
         "ja": "その雑誌が訂正記事を出したとたんに、もとの主張がまた交流サイトで広まり始めた。",
         "points": [
                    "No sooner … than … を「〜するやいなや…」と訳せている",
                    "倒置を戻して「雑誌が訂正記事を出した」と、had printed の主語が the magazine だと分かる訳になっている",
                    "began spreading を「広まり始めた」と、began の目的語として訳せている"]},
    ]},
    {"g": "③　分詞構文・無生物主語・名詞構文・仮定法・並列", "sub": "動詞でない語に隠れた主語述語を見る", "pool": "3-3", "items": [
        {"id": "F1",
         "syn": "with-absolute",
         "en": "With the irrigation channels blocked and the harvest failing, the farmers had little choice but to migrate.",
         "dsl": "( M: {接:With} {O':the irrigation channels} {C':blocked} {接:and} {O':the harvest} {C':failing} ) , {S:the farmers} {V:had} {O:little choice} <M: but {V':to migrate} > .",
         "pat": "第3文型（SVO）",
         "tag": "付帯状況の with",
         "notes": [
                   "急所は文頭の With。「〜を持って」ではなく、<b>付帯状況</b>を表す with で、後ろに O と C の組が続く。",
                   "the irrigation channels と blocked の間には「用水路が埋まっている」という主語述語の関係が立つ。だから O′ と C′ になる。",
                   "C′ には過去分詞（blocked）も現在分詞（failing）も来る。O との関係が受動なら過去分詞、能動なら現在分詞になる。",
                   "( M: With … failing ) を丸ごと外すと the farmers had little choice が残る。付帯状況の with は骨組みの外である。"],
         "ja": "用水路がふさがり、収穫も落ちこむなかで、農民たちには移住するよりほかにほとんど道がなかった。",
         "points": [
                    "付帯状況の with を「〜のなかで・〜のまま」と、状況の説明として訳せている（「〜を持って」と訳していない）",
                    "blocked と failing がそれぞれ直前の名詞の状態を述べる補語だと分かる訳になっている",
                    "little choice but to migrate を「移住するよりほかにほとんど道がない」と訳せている"]},
        {"id": "F2",
         "syn": "inanimate-subject",
         "en": "A prolonged drought prevented the region from planting the crop on which its people had always depended.",
         "dsl": "{S:A prolonged drought} {V:prevented} {O:the region} ( M: from planting the crop <M': ( M'': on which ) {S'':its people} {助:had} {M'':always} {V'':depended} > ) .",
         "pat": "第3文型（SVO）",
         "tag": "無生物主語 prevent A from doing",
         "notes": [
                   "急所は prevent A from doing。「A が〜するのを妨げる」で、<b>主語が人ではない</b>のがこの型の目印。",
                   "無生物主語は「〜のせいで A は…できなかった」と、原因として訳し下ろすと日本語になる。直訳の「干ばつが妨げた」は避ける。",
                   "from doing の from は動詞が要求する前置詞。切り離して意味を取らないが、記号の上では ( M ) として外に出す。",
                   "on which は前置詞つきの関係代名詞で the crop にかかる。depend on の on が前に出た形だと見抜く。had と depended "
                   "の間に always が割り込むので、助動詞を 助 として分ける。"],
         "ja": "干ばつが長引いたせいで、その地域の人々がずっと頼りにしてきた作物を植えられなかった。",
         "points": [
                    "prevent A from doing を「A が〜するのを妨げる／〜できなくする」と訳せている",
                    "無生物主語を「干ばつのせいで」と原因として訳し下ろせている",
                    "on which を the crop にかけ、depend on の on だと分かる訳になっている"]},
        {"id": "F3",
         "syn": "nominalization",
         "en": "The sudden withdrawal of the subsidy deprived the orchestra of the only rehearsal space it had used for decades.",
         "dsl": "{S:The sudden withdrawal} <M: of the subsidy > {V:deprived} {O:the orchestra} ( M: of the only rehearsal space <M': {O'':it} {V'':had used} ( M'': for decades ) > ) .",
         "pat": "第3文型（SVO）",
         "tag": "名詞構文（目的格の of）",
         "notes": [
                   "急所は The withdrawal of the subsidy。withdraw は他動詞なので、この of は<b>目的格</b>で「補助金を打ち切ること」の意味になる。",
                   "名詞構文は動詞に戻して読む。someone withdrew the subsidy と読み替えれば、of が主語ではなく目的語を導くと分かる。",
                   "deprive A of B は「A から B を奪う」。この of は動詞が要求するもので、切り離して意味を取らない。",
                   "&lt;M': it had used for decades &gt; は space にかかる関係詞節で、関係代名詞が省略されている。"],
         "ja": "補助金が突然打ち切られたことで、その楽団は何十年も使ってきた唯一の練習場を失った。",
         "points": [
                    "The withdrawal of the subsidy を「補助金を打ち切ること」と、of を目的格に取って訳せている",
                    "deprive A of B を「A から B を奪う」と訳せている",
                    "it had used for decades を space にかけ、過去完了で「使ってきた」と訳せている"]},
        {"id": "F4",
         "syn": "subjunctive",
         "en": "But for the detailed records that survived in a private collection, historians would never have reconstructed the ceremony.",
         "dsl": "( M: But for the detailed records <M': {S'':that} {V'':survived} ( M'': in a private collection ) > ) , {S:historians} {V:would never have reconstructed} {O:the ceremony} .",
         "pat": "第3文型（SVO）",
         "tag": "But for + 仮定法過去完了",
         "notes": [
                   "急所は But for。「〜が無かったら」という仮定を作る形で、if 節の代わりをしている。Without にも書き換えられる。",
                   "主節が would have + 過去分詞なので、<b>過去の事実に反する</b>仮定である。実際には記録は残り、儀式は復元された。",
                   "would never have reconstructed は助動詞と否定と完了がひとかたまり。not / never は V と同じマスに入れる。",
                   "But for … の for は前置詞なので後ろは名詞。接続詞の but（しかし）と混同しない。"],
         "ja": "個人の収集品の中に残っていた詳細な記録が無かったら、歴史家たちはその儀式を復元することはできなかっただろう。",
         "points": [
                    "But for を「〜が無かったら」と、仮定を作る形として訳せている",
                    "would never have reconstructed を過去の事実に反する仮定として「復元できなかっただろう」と訳せている",
                    "that survived in a private collection を ledgers にかけて訳せている"]},
        {"id": "F5",
         "syn": "correlative",
         "en": "A carefully designed rehabilitation program offers patients not only physical recovery but also a clear sense of purpose.",
         "dsl": "{S:A carefully designed rehabilitation program} {V:offers} {O1:patients} [ O2: {接:not only} {O':physical recovery} {接:but also} {O':a clear sense} <M': of purpose > ] .",
         "pat": "第4文型（SVOO）",
         "tag": "not only A but also B",
         "notes": [
                   "急所は not only A but also B。A と B は<b>同じ形</b>で並ぶ。ここはどちらも名詞のかたまりである。",
                   "並んでいるのは O2 の中身だけ。offers patients までは A にも B にも共通で、一度しか書かれていない。",
                   "共通部分を二度訳さないこと。「患者に A を与え、また患者に B を与える」ではなく「患者に A だけでなく B も与える」。",
                   "of purpose は a clear sense にかかるので &lt;M'&gt; として外に出す。名詞のかたまりの核は a clear sense である。"],
         "ja": "よく考えて組まれた機能回復のプログラムは、患者に身体の回復だけでなく、はっきりした目的意識も与えてくれる。",
         "points": [
                    "not only A but also B を「A だけでなく B も」と訳せている",
                    "offers patients が A と B の共通部分だと分かり、一度だけ訳せている",
                    "a clear sense of purpose を「はっきりした目的意識」と、of 句を sense にかけて訳せている"]},
        {"id": "F6",
         "syn": "concessive-as",
         "en": "Exhausted as the volunteers were after eight hours of sorting donations, none of them left before the last box was labeled.",
         "dsl": "( M: {C':Exhausted} {接:as} {S':the volunteers} {V':were} ( M': after eight hours <M'': of sorting donations > ) ) , {S:none} <M: of them > {V:left} ( M: {接:before} {S':the last box} {V':was labeled} ) .",
         "pat": "第1文型（SV）",
         "tag": "譲歩の as（形容詞 + as + S + V）",
         "notes": [
                   "急所は文頭の Exhausted。補語が as の前に飛び出しているので、この as は「〜だけれども」という<b>譲歩</b>になる。",
                   "元の語順は As the volunteers were exhausted。補語を前に出すのは譲歩の合図で、理由の as とはここで見分ける。",
                   "「疲れていたので」と理由に取ると後半とつながらない。前半と後半が逆接になっているかで確かめる。",
                   "none of them は「彼らのうち一人も〜ない」。否定を担うのは S の側なので、動詞を否定して訳さない。"],
         "ja": "寄付品を8時間仕分けして疲れてはいたけれども、最後の箱にラベルが貼られるまで彼らの誰一人その場を離れなかった。",
         "points": [
                    "Exhausted as the volunteers were を「疲れてはいたけれども」と譲歩で訳せている（理由で訳していない）",
                    "none of them left を「彼らのうち一人もその場を離れなかった」と、S の側の否定として訳せている",
                    "before the last box was labeled を「最後の箱にラベルが貼られるまで」と訳せている"]},
        {"id": "F7",
         "syn": "neither-nor",
         "en": "Neither the tariffs imposed last spring nor the subsidies announced in the fall have slowed the decline of the industry.",
         "dsl": "{S:Neither the tariffs} <M: {V':imposed} ( M': last spring ) > {接:nor} {S:the subsidies} <M: {V':announced} ( M': in the fall ) > {V:have slowed} {O:the decline} <M: of the industry > .",
         "pat": "第3文型（SVO）",
         "tag": "neither A nor B",
         "notes": [
                   "急所は neither A nor B。<b>A も B も両方とも否定</b>する形で、not が表に出ないまま文全体が否定になる。",
                   "A と B は同じ形で並ぶ。ここはどちらも「名詞 + 過去分詞の後置修飾」で、形をそろえて置かれている。",
                   "動詞の数は B のほう（近いほう）に合わせるのが原則。ここは the subsidies が複数なので have になっている。",
                   "imposed も announced も直前の名詞にかかる分詞で、主節の V ではない。主節の V は have slowed ただ一つ。"],
         "ja": "春に課された関税も、秋に発表された補助金も、どちらもその産業の衰退を遅らせてはいない。",
         "points": [
                    "neither A nor B を「A も B も〜ない」と、両方の否定として訳せている",
                    "imposed / announced をそれぞれ直前の名詞にかかる分詞として訳せている（主節の動詞にしていない）",
                    "the decline of the industry を「その産業の衰退」と、of 句を decline にかけて訳せている"]},
    ]},
]
