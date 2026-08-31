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
    "2": ["so-that-result", "too-to", "that-of", "compound-relative", "do-emphasis", "insertion", "only-inversion", "subjunctive-inversion", "superlative-equivalent", "ellipsis-clause", "infinitive-adjective", "relative-possessive"],
    "3-1": ["prep-relative", "relative-adverb", "what-clause", "chain-relative", "nonrestrictive", "appositive-that"],
    "3-2": ["not-so-much-as", "no-more-than", "comparative-ellipsis", "the-more-the-more", "negative-inversion", "cleft"],
    "3-3": ["with-absolute", "inanimate-subject", "nominalization", "subjunctive", "correlative", "concessive-as"],
}

# ---------------------------------------------------------------- 第1部 SVOCM 判別
PART1 = [
    {"g": "Ａ　5文型の骨格を見抜く", "sub": "第1〜第5文型／M を混ぜて骨組みだけを取り出す", "pool": "1A", "items": [
        {"id": "A1",
         "syn": "sv",
         "en": "The wooden bridge over the narrow river shakes slightly whenever a heavy truck passes.",
         "dsl": "{S:The wooden bridge} < M: over the narrow river > {V:shakes} {M:slightly} ( M: {接:whenever} {S':a heavy truck} {V':passes} ) .",
         "pat": "第1文型（SV）",
         "tag": "第1文型 SV（O も C も無い）",
         "notes": [
                   "急所は S と V の間。The wooden bridge のうしろに &lt;M: over the narrow river &gt; が割り込むので、"
                   "river を主語だと思うと V の相手を見失う。前置詞のうしろの名詞は主節の S になれない。",
                   "shakes は「〜を揺らす」とも読める動詞だが、うしろに名詞は無く {M:slightly} が続くだけである。O も C も無いのだから第1文型で確定する。",
                   "( M: whenever … ) は主節の外の副詞のカタマリ。中の {V':passes} を主節の V と数えると V が 2 つある文になってしまう。"
                   "主節の V は shakes ただ 1 つ。",
                   "&lt;M:&gt; と ( M: ) と {M:slightly} を外すと The wooden bridge shakes という S と V の "
                   "2 つだけが残る。骨格を見抜くとは、ここまで削ぎ落とすことである。"],
         "ja": "その木の橋は、大型トラックが通るたびに少し揺れる。"},
        {"id": "A2",
         "syn": "svc-adj",
         "en": "The water in the village well stays cold even during the hottest weeks of summer.",
         "dsl": "{S:The water} < M: in the village well > {V:stays} {C:cold} ( M: even during the hottest weeks < M': of summer > ) .",
         "pat": "第2文型（SVC）",
         "tag": "stay ＋ 形容詞の C",
         "notes": [
                   "急所は stays。「とどまる」という第1文型で切ってしまうと、そのあとの cold が行き場を失う。stay は be の仲間で、うしろの形容詞は S "
                   "の状態を述べる C になる。",
                   "S の核は The water だけ。&lt;M: in the village well &gt; を S のマスに抱え込むと、S がどこまでかを答えられなくなる。"
                   "前置詞句は必ず外へ出す。",
                   "cold は名詞ではないので O にはなれない。O か C かは品詞だけで切れることがあり、形容詞が来たならそれは必ず C である。",
                   "( M: even during … ) は時を表す副詞のカタマリ。外しても The water stays cold は崩れないので、骨格の 3 点には数えない。"],
         "ja": "その村の井戸の水は、夏のいちばん暑い時期でさえ冷たいままだ。"},
        {"id": "A3",
         "syn": "svc-noun",
         "en": "The empty lot behind the station has become a small community garden in recent years.",
         "dsl": "{S:The empty lot} < M: behind the station > {V:has become} {C:a small community garden} ( M: in recent years ) .",
         "pat": "第2文型（SVC）",
         "tag": "become ＋ 名詞の C",
         "notes": [
                   "急所は has become のうしろ。名詞が来ると O に見えるが、become は目的語を取らない動詞なので、この名詞は C しかありえない。",
                   "C が名詞のときは S ＝ C が立つかで確かめる。「空き地」＝「小さな共同菜園」で等号が成り立つので、O ではなく C と決まる。",
                   "has become は完了の have ＋ 過去分詞で 1 つの述語。has を別のマスにせず {V:has become} と 1 マスに握るのが約束である。",
                   "&lt;M: behind the station &gt; は The empty lot を後ろから説明する形容詞のカタマリ、( M: in recent "
                   "years ) は動詞にかかる副詞。働きが違うので括弧の形も変える。"],
         "ja": "駅の裏の空き地は、ここ数年で小さな共同菜園になっている。"},
        {"id": "A4",
         "syn": "svo",
         "en": "Heavy spring rain often delays the start of the rice planting season by several weeks.",
         "dsl": "{S:Heavy spring rain} {M:often} {V:delays} {O:the start} < M: of the rice planting season > ( M: by several weeks ) .",
         "pat": "第3文型（SVO）",
         "tag": "delays は名詞ではなく V",
         "notes": [
                   "急所は delays。「遅れ」という名詞にも見えるが、直前に {M:often} があり、副詞は名詞を修飾しない。だから delays はこの文の V である。",
                   "O の核は the start だけ。&lt;M: of the rice planting season &gt; を O のマスに抱え込むと、O がどこで終わるかを言えなくなる。"
                   "of 句は外へ出す。",
                   "delays のうしろの名詞は S の言い換えではない。「雨 ＝ 始まり」という等号は立たないので、C ではなく O、つまり第3文型と決まる。",
                   "( M: by several weeks ) は「どれだけ遅らせるか」を言う副詞で、名詞にかかる &lt;M:&gt; とは別物。外しても O の中身は変わらない。"],
         "ja": "春の大雨は、田植えの時期の始まりを数週間も遅らせることが多い。"},
        {"id": "A5",
         "syn": "svo",
         "en": "A single careless comment can ruin the atmosphere of a whole meeting within seconds.",
         "dsl": "{S:A single careless comment} {V:can ruin} {O:the atmosphere} < M: of a whole meeting > ( M: within seconds ) .",
         "pat": "第3文型（SVO）",
         "tag": "can ＋ 動詞は 1 つのマス",
         "notes": [
                   "急所は can ruin。助動詞と動詞は切り離さず 1 つの V のマスに入れる。can だけを別に数えると、V が 2 つあるように見えてしまう。",
                   "the atmosphere は ruin の相手なので O。「発言 ＝ 雰囲気」という等号は立たないから C ではなく、ここで第3文型が確定する。",
                   "&lt;M: of a whole meeting &gt; は the atmosphere にかかる。of 句をマスの中に入れたままだと O の核が "
                   "1 つに絞れない。",
                   "&lt;M:&gt; と ( M: ) の使い分けは「直前の名詞にかかるか、動詞にかかるか」で決める。within seconds は台無しにする速さを言うので "
                   "( M: ) になる。"],
         "ja": "たった一言の不用意な発言が、会議全体の雰囲気を数秒で台無しにしてしまうことがある。"},
        {"id": "A6",
         "syn": "svoo-give",
         "en": "The head teacher promised the parents a full report without any hesitation.",
         "dsl": "{S:The head teacher} {V:promised} {O1:the parents} {O2:a full report} ( M: without any hesitation ) .",
         "pat": "第4文型（SVOO）",
         "tag": "promise O1 O2（授与型）",
         "notes": [
                   "急所は promised のうしろに名詞が 2 つ並ぶこと。the parents と a full report の間に主語述語の関係は立たないので、第5文型ではなく "
                   "O1 O2 の第4文型である。",
                   "人が先・物があとという並びが授与型の目印。前後を入れ替えるなら promised a full report to the parents となり、to が必要になる。",
                   "promise は that 節も取る動詞で、promised that … なら O が 1 つだけの第3文型になる。動詞だけで決めず、うしろの形を見てから文型を決めること。",
                   "( M: without any hesitation ) は promised のしかたを言う副詞。外しても S V O1 O2 の 4 つは残るので骨格には数えない。"],
         "ja": "校長は、少しもためらわずに、保護者たちに詳しい報告をすると約束した。"},
        {"id": "A7",
         "syn": "svoo-take",
         "en": "The long delay at the airport cost the team an entire day of training.",
         "dsl": "{S:The long delay} < M: at the airport > {V:cost} {O1:the team} {O2:an entire day} < M: of training > .",
         "pat": "第4文型（SVOO）",
         "tag": "cost O1 O2（奪う型の第4文型）",
         "notes": [
                   "急所は cost。原形と過去形が同じ形なので動詞に見えにくいが、{S:The long delay} を受ける述語はこれしかない。まず V を 1 つに決めること。",
                   "cost のうしろも名詞が 2 つで第4文型だが、O2 は与えられたものではなく失われたものである。第4文型を「授与」だけで覚えていると読めない。",
                   "the team と an entire day の間に主語述語の関係は立たない。立たないので第5文型ではなく O1 O2 と決まる。A6 と同じ手順で切り分ける。",
                   "&lt;M: at the airport &gt; は The long delay に、&lt;M: of training &gt; は an entire "
                   "day にかかる。どちらも直前の名詞にかかるので ( M: ) にはしない。"],
         "ja": "空港での長い遅れのせいで、そのチームは丸一日の練習を失った。"},
        {"id": "A8",
         "syn": "svoc-adj",
         "en": "The sudden power cut left the whole shopping street completely dark last Friday evening.",
         "dsl": "{S:The sudden power cut} {V:left} {O:the whole shopping street} {C:completely dark} ( M: last Friday evening ) .",
         "pat": "第5文型（SVOC）",
         "tag": "leave O C（C が形容詞）",
         "notes": [
                   "急所は left。「去った」と取ると the whole shopping street が行き先に見えるが、そうすると completely dark "
                   "が宙に浮いてしまう。",
                   "leave O C は「O を C の状態のまま残す」。C が形容詞なので第5文型で、O と C の間には street is dark という関係が隠れている。",
                   "dark は名詞ではないので O2 にはなれない。うしろの 2 つ目が名詞なら第4文型、形容詞なら第5文型と、品詞のところで分かれる。",
                   "( M: last Friday evening ) はいつの出来事かを言う副詞。外すと S V O C の 4 点だけが一直線に並び、骨格が見える。"],
         "ja": "先週の金曜の夜、突然の停電が商店街全体を真っ暗にした。"},
        {"id": "A9",
         "syn": "svoc-noun",
         "en": "The club members elected a retired teacher their new chairperson at the spring meeting.",
         "dsl": "{S:The club members} {V:elected} {O:a retired teacher} {C:their new chairperson} ( M: at the spring meeting ) .",
         "pat": "第5文型（SVOC）",
         "tag": "elect O C（C が名詞）",
         "notes": [
                   "急所は elected のうしろの名詞 2 つ。a retired teacher と their new chairperson は同じ人を指すので、O1 "
                   "O2 ではなく O と C である。",
                   "第4文型なら 2 つの名詞は別物になる（A6 の the parents と a full report）。ここは「＝」で結べるかどうかが分かれ目になる。",
                   "elect O C は「O を C に選ぶ」。as が無くても C で、elect O as C とも書けることが名詞の C だと見抜く目印になる。",
                   "( M: at the spring meeting ) は選出が行われた場面を言う副詞。骨格の S V O C の 4 つを数えるときは先に外して考える。"],
         "ja": "クラブの会員たちは、春の集まりで、退職した教師を新しい会長に選んだ。"},
        {"id": "A10",
         "syn": "svoc-pp",
         "en": "A thick layer of dry sand can keep buried seeds almost perfectly preserved for many years.",
         "dsl": "{S:A thick layer} < M: of dry sand > {V:can keep} {O:buried seeds} {C:almost perfectly preserved} ( M: for many years ) .",
         "pat": "第5文型（SVOC）",
         "tag": "keep O C（C が過去分詞）",
         "notes": [
                   "急所は keep の型。keep O C は「O を C の状態のままにしておく」。「保つ」と訳して O だけで切ると almost perfectly "
                   "preserved が宙に浮く。",
                   "keep は O だけでも使える動詞で、keep the receipt / keep a spare key なら「取っておく」の意味になる。ここは C "
                   "が無いと「砂が種をしまっておく」となって意味が立たないので第5文型と決まる。",
                   "C が過去分詞のときは O との間に受動の関係が立つかを見る。seeds are preserved が成り立つので almost perfectly preserved "
                   "は C である。",
                   "O の中の buried は seeds にかかる飾りで骨格には数えない。&lt;M: of dry sand &gt; と ( M: for many "
                   "years ) を外せば S V O C の 4 つだけが残る。"],
         "ja": "厚く積もった乾いた砂は、埋もれた種を何年ものあいだほぼ完全な状態のまま保つことがある。"},
        {"id": "A11",
         "syn": "svoc-bare",
         "en": "A sudden change in the weather can make even experienced climbers doubt their own judgment.",
         "dsl": "{S:A sudden change} < M: in the weather > {V:can make} {O:even experienced climbers} [ C: {V':doubt} {O':their own judgment} ] .",
         "pat": "第5文型（SVOC）",
         "tag": "make O C（C が原形不定詞）",
         "notes": [
                   "急所は doubt。to も ing も付かない裸の原形が並ぶので V が 2 つあるように見えるが、これは make が取る C である。",
                   "make のうしろに名詞が 2 つ並ぶ形なら第4文型もありうるが、2 つ目が原形のときは第5文型に限られる。品詞を見た時点で第4文型は消える。",
                   "C が動詞を含むので平のマス 1 つでは置かず、[ C: {V':doubt} {O':their own judgment} ] と囲んで中まで分解する。"
                   "囲みの中なのでダッシュが 1 本付く。",
                   "&lt;M: in the weather &gt; は A sudden change にかかる形容詞のカタマリ。S のマスに巻き込むと S の核が言えなくなる。"],
         "ja": "天候の急変は、経験を積んだ登山者にさえ自分の判断を疑わせることがある。"},
        {"id": "A12",
         "syn": "svoc-to",
         "en": "Most drama schools now expect applicants with no stage experience to prepare two short speeches.",
         "dsl": "{S:Most drama schools} {M:now} {V:expect} {O:applicants} < M: with no stage experience > [ C: {V':to prepare} {O':two short speeches} ] .",
         "pat": "第5文型（SVOC）",
         "tag": "expect O to do（C が to 不定詞）",
         "notes": [
                   "急所は to prepare。「用意するために」と副詞に取ると、expect applicants で終わる第3文型に見えてしまう。",
                   "applicants prepare two short speeches という主語述語の関係が立つので、この不定詞は O に対する C である。",
                   "C が動詞を含むので [ C: {V':to prepare} {O':two short speeches} ] と囲む。A11 の原形の C と書き方をそろえるのが約束である。",
                   "O と C の間に &lt;M: with no stage experience &gt; が挟まっても expect O to do の型は変わらない。"
                   "{M:now} と合わせて外せば骨格が並ぶ。"],
         "ja": "たいていの演劇学校は今や、舞台経験の無い志願者にも短いせりふを二つ用意してくることを求める。"},
    ]},
    {"g": "Ｂ　修飾語 M を切り離す", "sub": "S と V が修飾で引き離されている形", "pool": "1B", "items": [
        {"id": "B1",
         "syn": "relative-subject",
         "en": "Volunteers who have worked at an animal shelter for years can calm a frightened dog in minutes.",
         "dsl": "{S:Volunteers} < M: {S':who} {V':have worked} ( M': at an animal shelter ) ( M': for years ) > {V:can calm} {O:a frightened dog} ( M: in minutes ) .",
         "pat": "第3文型（SVO）／主語に関係詞節",
         "tag": "主格の関係代名詞（who）が S と V を割る",
         "notes": [
                   "急所は who。関係詞がそのまま節の中の S' の働きをするので、&lt;M: who … for years &gt; の内側にもう一つ主語を置く場所は無い。"
                   "have worked を主節の V と数えると、後ろの can calm が主語を失って余る。",
                   "飾りの &lt;M: … &gt; を丸ごと外すと Volunteers can calm a frightened dog が残る。calm は他動詞で直後の "
                   "a frightened dog が O、( M: in minutes ) は外しても文が立つ副詞なので骨組みは第3文型。",
                   "関係詞節は先行詞の直後で始まり、節の中で完結する。for years まで来ると節が閉じるので、そこから先に出てくる can calm が主節の V だと決まる。"
                   "動詞の個数ではなく、囲みの内側か外側かで切る。",
                   "規約1 のとおり助動詞は動詞と同じマスなので {V:can calm} は 1 マス。( M': at an animal shelter ) と ( M': "
                   "for years ) はどちらも関係詞節の内側の副詞で、ダッシュ 1 本がその深さを示している。"],
         "ja": "動物保護施設で何年も働いてきたボランティアは、おびえた犬を数分で落ち着かせることができる。"},
        {"id": "B2",
         "syn": "relative-object",
         "en": "The furniture that the previous owner abandoned in the basement now fills the small entrance hall.",
         "dsl": "{S:The furniture} < M: {O':that} {S':the previous owner} {V':abandoned} ( M': in the basement ) > {M:now} {V:fills} {O:the small entrance hall} .",
         "pat": "第3文型（SVO）／主語に関係詞節",
         "tag": "目的格の関係代名詞（that）が S と V を割る",
         "notes": [
                   "that の後ろは the previous owner abandoned と続き、abandoned の目的語が空いている。その空所に The furniture "
                   "が入るので、この that は目的格の関係代名詞 {O':that} である。接続詞の that だと読むと空所を説明できない。",
                   "誤読の急所は abandoned。過去形が二つ並んでいるように見えるが、abandoned は &lt;M: … &gt; の中の V' で、主節の V "
                   "は fills のほう。単数扱いの The furniture に fills が対応している点も手がかりになる。",
                   "( M': in the basement ) は関係詞節の内側の副詞。ここで文が終わったと思い込むと S の The furniture が動詞を持たないまま残る。"
                   "飾りを外すと The furniture now fills the small entrance hall となり第3文型と分かる。",
                   "{M:now} は S と V の間に入った副詞で骨組みには数えない。目的格の関係代名詞は省略もできるので、名詞のあとにいきなり別の名詞と動詞が続いたら、"
                   "まず空所を探す癖をつける。"],
         "ja": "前の持ち主が地下室に置き去りにした家具が、今では小さな玄関ホールを埋めている。"},
        {"id": "B3",
         "syn": "participle-postmod",
         "en": "Cooking methods developed in rural households centuries ago still offer modern chefs a useful lesson.",
         "dsl": "{S:Cooking methods} < M: {V':developed} ( M': in rural households ) ( M': centuries ago ) > {M:still} {V:offer} {O1:modern chefs} {O2:a useful lesson} .",
         "pat": "第4文型（SVOO）／主語に過去分詞の後置修飾",
         "tag": "過去分詞の後置修飾が S と V を割る",
         "notes": [
                   "Cooking methods developed までを読むと「調理法が発展した」という S と V にそのまま見える。これがいちばん多い誤読で、後ろの "
                   "still offer が主語を失うことで初めて破綻に気づく。",
                   "-ed が飾りか主節の V かは、直前に be があるかどうかでは決まらない。決め手は「別に定形動詞が残るか」で、ここは現在形の offer が残るので "
                   "developed のほうが過去分詞 {V':developed} と確定する。",
                   "&lt;M: developed … centuries ago &gt; を丸ごと外し、さらに {M:still} も外すと Cooking methods "
                   "offer modern chefs a useful lesson が残る。人（O1: modern chefs）と物（O2: a useful lesson）が続くので第4文型と判定できる。",
                   "規約4 のとおり &lt; &gt; の中の分詞は素の語で置かず {V':developed} と示す。同じ過去分詞でも B7 の Faced は文全体にかかるので "
                   "( M ) になる。かかる先が名詞か文かで括弧の種類が変わる。"],
         "ja": "何世紀も前に農村の家庭で生まれた調理法は、今なお現代の料理人に有益な教訓を与えてくれる。"},
        {"id": "B4",
         "syn": "gerund-object",
         "en": "Students at the summer language camp practice introducing themselves in English every single morning.",
         "dsl": "{S:Students} < M: at the summer language camp > {V:practice} [ O: {V':introducing} {O':themselves} ( M': in English ) ] ( M: every single morning ) .",
         "pat": "第3文型（SVO）／目的語が動名詞句",
         "tag": "動名詞句が O（practice doing）",
         "notes": [
                   "急所は practice。名詞にも動詞にもなる語なので the summer language camp practice を一つの名詞のかたまりと読みたくなるが、"
                   "そう読むと文全体に定形動詞が一つも残らない。残らないと分かった時点で practice が主節の V と決まる。",
                   "introducing は直前に be が無いので進行形ではない。practice の目的語になった動名詞で、[ O: {V':introducing} "
                   "{O':themselves} ( M': in English ) ] という名詞のカタマリ一つぶんがそのまま O のマスに収まる。",
                   "&lt;M: at the summer language camp &gt; は S の Students を後ろから説明する形容詞のカタマリ。外すと "
                   "Students practice … と S と V が隣り合うので、骨組みが第3文型だと確かめられる。",
                   "-ing が名詞のカタマリなら [ ]、名詞にかかる飾りなら &lt; &gt;、文にかかる飾りなら ( ) と括弧を変える。( M: every single "
                   "morning ) は practice にかかる副詞なので骨組みには数えない。"],
         "ja": "その夏の語学キャンプの生徒たちは、毎朝欠かさず英語で自己紹介をする練習をしている。"},
        {"id": "B5",
         "syn": "adverb-intrusion",
         "en": "The publisher, after nearly two years of silence, suddenly sent the young translator a new contract.",
         "dsl": "{S:The publisher} , ( M: after nearly two years < M': of silence > ) , {M:suddenly} {V:sent} {O1:the young translator} {O2:a new contract} .",
         "pat": "第4文型（SVOO）／S と V の間に副詞句が割り込む",
         "tag": "S と V の間に割り込む副詞句",
         "notes": [
                   "急所は二つのコンマに挟まれた ( M: after nearly two years of silence )。S の The publisher と V "
                   "の sent の間に割り込んだ副詞のカタマリで骨組みではない。直前の silence を主語と読むと、動詞 sent に主語が二つできてしまう。",
                   "割り込みを外すと The publisher suddenly sent the young translator a new contract が残る。"
                   "人（O1: the young translator）と物（O2: a new contract）が並ぶので第4文型で、{M:suddenly} も外して数えない副詞である。",
                   "&lt;M': of silence &gt; は two years にかかる形容詞のカタマリで、( M ) の内側の飾り。ダッシュ 1 本が「一枚内側」を表しているので、"
                   "外の骨格には数えないと記号だけで分かる。",
                   "文頭に出る副詞句（B6 の Behind …）も S と V の間に入る副詞句も、働きは同じ M。位置ではなく「外しても文が立つか」で M かどうかを決めると、"
                   "コンマの数に惑わされない。"],
         "ja": "その出版社は、二年近く何の連絡もないまま過ぎたあと、突然その若い翻訳者に新しい契約書を送ってきた。"},
        {"id": "B6",
         "syn": "long-fronted-pp",
         "en": "Behind the tall fences of the construction site, several old fruit trees have survived the winter.",
         "dsl": "( M: Behind the tall fences < M': of the construction site > ) , {S:several old fruit trees} {V:have survived} {O:the winter} .",
         "pat": "第3文型（SVO）／文頭に長い前置詞句",
         "tag": "文頭の長い前置詞句（Behind …）",
         "notes": [
                   "前置詞 Behind の目的語である the tall fences も、その後ろの the construction site も S にはなれない。前置詞句の中の名詞を主語と読むのが最大の誤読で、"
                   "そう読むと後ろの have survived が行き場を失う。",
                   "( M: Behind … the construction site ) を丸ごと外して初めて主節が見える。S は several old fruit "
                   "trees、V は have survived、O は the winter で第3文型。長い M の後ろに来る短い S はいちばん見落としやすい。",
                   "&lt;M': of the construction site &gt; は the tall fences にかかる形容詞のカタマリで、( M ) の内側の飾り。"
                   "囲みが二重になったら、内側の名詞は外の骨格の候補から外す。",
                   "文頭の長い前置詞句はコンマで「ここまでが飾り」と合図することが多い。コンマの後ろから S を探し、そこで見つけた名詞と対応する動詞を V に決める、という順番を固定しておく。"],
         "ja": "工事現場の高い塀の裏側で、何本かの古い果樹が冬を越して生き残っている。"},
        {"id": "B7",
         "syn": "participial-construction",
         "en": "Faced with a shortage of skilled workers, a growing number of manufacturers have begun training their own technicians.",
         "dsl": "( M: {V':Faced} ( M': with a shortage < M'': of skilled workers > ) ) , {S:a growing number} < M: of manufacturers > {V:have begun} [ O: {V':training} {O':their own technicians} ] .",
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
         "en": "The coastal road between the harbor and the fishing village becomes extremely dangerous after heavy rain.",
         "dsl": "{S:The coastal road} < M: between the harbor {接:and} the fishing village > {V:becomes} {C:extremely dangerous} ( M: after heavy rain ) .",
         "pat": "第2文型（SVC）／主語に前置詞句が付く",
         "tag": "名詞に付く前置詞句（between A and B）",
         "notes": [
                   "S は The coastal road の三語だけ。between 以下が長いので、直前の the fishing village を主語と見て becomes "
                   "を対応させる誤読が起きる。前置詞の後ろの名詞は S になれないと決めておけば防げる。",
                   "&lt;M: between the harbor and the fishing village &gt; は road を後ろから説明する形容詞のカタマリ。"
                   "外すと The coastal road becomes extremely dangerous が残り、becomes の後ろは O ではなく C なので第2文型。",
                   "{接:and} が結ぶのは the harbor と the fishing village という二つの名詞で、文と文ではない。and の前後に同じ形が並んでいるかを見ると、"
                   "どこまでが一つの前置詞句なのかが決まる。",
                   "同じ前置詞句でも、名詞だけを説明するなら &lt; &gt;、文にかかるなら ( ) と書き分ける。( M: after heavy rain ) は becomes "
                   "にかかる副詞なので ( ) に入れる。"],
         "ja": "港と漁村を結ぶその海沿いの道は、大雨のあとには非常に危険になる。"},
        {"id": "B9",
         "syn": "comparative-postmod",
         "en": "A crowd far larger than the organizers had expected gathered quietly outside the main entrance.",
         "dsl": "{S:A crowd} < M: far larger ( M': {接:than} {S'':the organizers} {V'':had expected} ) > {V:gathered} {M:quietly} ( M: outside the main entrance ) .",
         "pat": "第1文型（SV）／主語に比較の句が付く",
         "tag": "比較の句が名詞を後ろから修飾する",
         "notes": [
                   "急所は than の節がどこで閉じるか。&lt;M: far larger ( M': than the organizers had expected "
                   ") &gt; までが A crowd の説明で、had expected を主節の V と読むと、後ろの gathered が主語を失って余ってしまう。",
                   "far larger は crowd を後ろから修飾する形容詞なので、than 以下まで込みで &lt; &gt; の一かたまりになる。飾りを外すと A "
                   "crowd gathered quietly outside the main entrance が残り、目的語が無いので第1文型。",
                   "than の後ろは the organizers had expected と主語と動詞がそろっているように見えるが、expected の目的語が空いている。"
                   "この空所こそ比較の節の目印で、空所がある節は主節の骨格には数えない。",
                   "{M:quietly} と ( M: outside the main entrance ) はどちらも gathered にかかる副詞。gathered "
                   "の後ろに名詞が一つも無いことを確かめてから第1文型と決めると、C や O と迷わない。"],
         "ja": "主催者が予想していたよりはるかに大きな人だかりが、正面入口の外に静かに集まった。"},
    ]},
    {"g": "Ｃ　誤読しやすい形", "sub": "形式主語・there 構文・受動態・知覚動詞・群動詞・whether", "pool": "1C", "items": [
        {"id": "C1",
         "syn": "formal-subject",
         "en": "It is no surprise that many first-time visitors lose their way in the crowded streets around the central market.",
         "dsl": "{S:It} {V:is} {C:no surprise} [ 真S: {接:that} {S':many first-time visitors} {V':lose} {O':their way} ( M': in the crowded streets < M'': around the central market > ) ] .",
         "pat": "第2文型（SVC）＋形式主語 It … 真S（that 節）",
         "tag": "形式主語 It … 真S（that 節）",
         "notes": [
                   "急所は文頭の It。「それは」と訳した瞬間に指す先が消える。中身を持たない仮の主語で、実体は後ろの [ 真S: that … ] にある。",
                   "[ 真S: … ] を丸ごと外すと It is no surprise だけが残る。is の後ろが名詞のカタマリなので、主節は S V C の第2文型と確定する。",
                   "対抗する読みは surprise にかかる同格の that 節。だが同格なら It が何かを指していなければならないのに、指す先が文中にも前にも無い。だから形式主語と決まる。",
                   "真S の中の骨組みは {S':many first-time visitors} と {V':lose} と {O':their way}。( M': in "
                   "the crowded streets &lt; M'': around the central market &gt; ) は lose にかかる副詞のカタマリで、"
                   "骨組みには数えない。around the central market は streets を後ろから説明するので、外に並べず内側に入れ子にする。"],
         "ja": "中央市場のまわりの混み合った通りで、初めて訪れた人の多くが道に迷うのは、驚くようなことではない。"},
        {"id": "C2",
         "syn": "formal-object",
         "en": "Centuries of rebuilding make it extremely difficult to date the older parts of a medieval castle.",
         "dsl": "{S:Centuries} < M: of rebuilding > {V:make} {O:it} {C:extremely difficult} [ 真O: {V':to date} {O':the older parts} < M': of a medieval castle > ] .",
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
         "ja": "何世紀にもわたる建て直しのせいで、中世の城の古い部分の年代を特定することは、きわめて難しくなっている。"},
        {"id": "C3",
         "syn": "that-clause-object",
         "en": "Some gardeners still believe that the phase of the moon decides the best day for planting beans.",
         "dsl": "{S:Some gardeners} {M:still} {V:believe} [ O: {接:that} {S':the phase} < M': of the moon > {V':decides} {O':the best day} < M': for planting beans > ] .",
         "pat": "第3文型（SVO）＋接続詞 that 節が O",
         "tag": "that 節が丸ごと O",
         "notes": [
                   "急所は that の後ろが欠けの無い完全な文であること。関係代名詞なら節の中で S か O が1つ欠ける。ここは接続詞で、節がまるごと believe の O になる。",
                   "[ O: … ] を外すと Some gardeners still believe が残る。主節の V は believe ひとつで、節の中の decides "
                   "は V′ にすぎない。",
                   "節の中の S′ は the phase であって the moon ではない。&lt; M': of the moon &gt; を名詞のマスから外へ出すと、"
                   "decides に対応する主語がはっきり見える。",
                   "{M:still} は S と V の間に割り込んだ副詞で骨組みではない。副詞を M として外に置き、その次に来る believe を V の位置から動かさない。"],
         "ja": "月の満ち欠けが豆をまくのに一番よい日を決めると、いまだに信じている庭師もいる。"},
        {"id": "C4",
         "syn": "whether-clause",
         "en": "Experienced buyers cannot tell from a photograph alone whether a chair is a genuine antique or a clever copy.",
         "dsl": "{S:Experienced buyers} {V:cannot tell} ( M: from a photograph alone ) [ O: {接:whether} {S':a chair} {V':is} {C':a genuine antique} {接:or} {C':a clever copy} ] .",
         "pat": "第3文型（SVO）＋ whether の名詞節が O",
         "tag": "whether の名詞節が O",
         "notes": [
                   "whether を「たとえ〜であろうと」の譲歩（副詞のカタマリ）と読むと、他動詞 tell の目的語がどこにも残らない。この欠落が起きるので、ここは「〜かどうか」の名詞節で記号は O。",
                   "V の直後に ( M: from a photograph alone ) が割り込む。O を探すときは前置詞句を飛ばし、その次に現れる名詞のカタマリまで進むこと。",
                   "{接:or} は [ O: ] の中で {C':a genuine antique} と {C':a clever copy} を結んでいるだけ。ここで文が切れて新しい "
                   "S が始まると考えない。",
                   "「A か B か」と2つ並んでいても、whether から文末までで名詞のカタマリ1つぶん。[ O: ] は文末で閉じるので、主節の要素はこれ以上増えない。"],
         "ja": "経験を積んだ買い手でも、写真だけでは、その椅子が本物の骨董品なのか、よくできた模造品なのかを見分けられない。"},
        {"id": "C5",
         "syn": "there-construction",
         "en": "There hung above the entrance of the old factory a large clock with only one hand.",
         "dsl": "{M:There} {V:hung} ( M: above the entrance < M': of the old factory > ) {S:a large clock} < M: with only one hand > .",
         "pat": "第1文型（SV）＋ there 構文（There は M、S は V の後ろ）",
         "tag": "there 構文（There は M）",
         "notes": [
                   "文頭の There は主語ではなく M。巻頭の表記規約にも「there 構文の There は M。実際の S は動詞の後ろの名詞」と書いてある。答案では "
                   "There に M と書く。",
                   "この文の S は V より後ろの a large clock で、S と V の順序が入れ替わっている。「文頭の名詞が S」という思い込みだけで解くと必ず外す形である。",
                   "V(hung) と S の間に ( M: above the entrance &lt; M': of the old factory &gt; ) が割り込む。"
                   "of the old factory は entrance にかかるので内側に入れ子にする。ここで factory を主語と取ると、後ろの clock が宙に浮いてしまう。",
                   "&lt; M: with only one hand &gt; は clock を後ろから説明する形容詞のカタマリ。hung にかかる副詞と取ると、S がどこで終わるのかが読めなくなる。"],
         "ja": "その古い工場の入口の上には、針が1本しかない大きな時計が掛かっていた。"},
        {"id": "C6",
         "syn": "passive",
         "en": "In this small village, the church bells are rung by hand on the morning of every festival.",
         "dsl": "( M: In this small village ) , {S:the church bells} {V:are rung} ( M: by hand ) ( M: on the morning < M': of every festival > ) .",
         "pat": "第1文型（SV）＋受動態（be + 過去分詞で 1 つの V）",
         "tag": "受動態 be + 過去分詞",
         "notes": [
                   "急所は are rung を2つに割らないこと。受動の be と過去分詞は合わせて1つの V のマスに入れる。are を V、rung を C と読むと、"
                   "受動態を第2文型に誤判定する。",
                   "V の後ろに名詞のカタマリが1つも残っていない。だからこの文は O を持たず、骨組みは S と V だけの第1文型と決まる。",
                   "( M: by hand ) は動作主ではなく「手で」という方法を表す。受動態の by が必ず動作主だと決めてかかると、ここで S を探し直すことになる。",
                   "文頭の ( M: In this small village ) は骨組みの外。コンマの後ろに現れる the church bells が主節の S であって、"
                   "village を S と取らない。"],
         "ja": "この小さな村では、祭りの日の朝には教会の鐘が手で鳴らされる。"},
        {"id": "C7",
         "syn": "perception-verb",
         "en": "From the shore, the fishermen could see a thin line of smoke rise slowly into a windless sky.",
         "dsl": "( M: From the shore ) , {S:the fishermen} {V:could see} {O:a thin line} < M: of smoke > [ C: {V':rise} {M':slowly} ( M': into a windless sky ) ] .",
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
         "ja": "岸から、漁師たちは細い煙の筋が風のない空へゆっくりと立ちのぼるのを見ることができた。"},
        {"id": "C8",
         "syn": "causative",
         "en": "An instructor at a good driving school has the learner describe each step of the parking procedure aloud.",
         "dsl": "{S:An instructor} < M: at a good driving school > {V:has} {O:the learner} [ C: {V':describe} {O':each step} < M': of the parking procedure > {M':aloud} ] .",
         "pat": "第5文型（SVOC）＋使役動詞 have + O + 原形不定詞",
         "tag": "使役動詞 have + O + 原形",
         "notes": [
                   "急所は has。完了の助動詞と読むなら後ろに過去分詞が要るが、describe は原形なので成り立たない。原形不定詞を C に取る使役の has である。",
                   "「指導員が学習者を持っている」と読むと describe 以下が宙に浮く。{O:the learner} と [ C: describe … ] の間に主述関係が立つので、"
                   "ここは第5文型。",
                   "C は動詞を含むカタマリなので平のマスに置かず [ C: ] で囲んで中まで分解する。&lt; M': of the parking procedure "
                   "&gt; と {M':aloud} はどちらもその内側の要素である。",
                   "&lt; M: at a good driving school &gt; は instructor を後ろから説明する形容詞のカタマリ。S の核は An "
                   "instructor で、直前にあるからといって school を S と取らない。"],
         "ja": "よい自動車教習所の指導員は、学習者に駐車の手順を一つ一つ声に出して説明させる。"},
        {"id": "C9",
         "syn": "group-verb",
         "en": "Several small dairy farms have taken advantage of the new railway in order to send fresh milk into the city.",
         "dsl": "{S:Several small dairy farms} {V:have taken advantage of} {O:the new railway} ( M: in order {V':to send} {O':fresh milk} ( M': into the city ) ) .",
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
     "en": "The pharmacist spoke in such a quiet voice that several patients asked her to repeat the dose twice.",
     "dsl": "{S:The pharmacist} {V:spoke} ( M: in such a quiet voice ) ( M: {接:that} {S':several patients} {V':asked} {O':her} [ C': {V'':to repeat} {O'':the dose} {M'':twice} ] ) .",
     "pat": "第1文型（SV）",
     "tag": "結果を表す such … that",
     "notes": [
               "such の直後で名詞のカタマリが終わらず that 節が続いたら、結果を表す so / such … that の呼応を疑う。",
               "spoke は目的語を取らない自動詞なので、後ろの that 節は O ではなく副詞のカタマリ ( M ) として並ぶ。",
               "主節の骨組みは The pharmacist と spoke の 2 つだけで、残りはすべて ( M ) の修飾語である。",
               "that 節の中の asked her to repeat は O と C を取る第5文型。C は動詞を含むので囲んで中も分解する。"],
     "ja": "その薬剤師はあまりに静かな声で話したので、何人かの患者は薬の量を二度言い直してほしいと彼女に頼んだ。",
     "q": "that several patients asked her to repeat the dose twice は、この文でどのような働きをしているか。最も適切なものを "
          "1 つ選びなさい。",
     "choices": [
                 "in such a quiet voice と呼応し、その結果どうなったかを述べる副詞のカタマリ",
                 "spoke の目的語となり、薬剤師が話した内容そのものを表す名詞のカタマリ",
                 "a quiet voice を後ろから説明し、どのような声だったかを限定する形容詞のカタマリ",
                 "The pharmacist を後ろから説明し、どのような薬剤師なのかを限定する形容詞のカタマリ"],
     "ans": 0,
     "exp": "such a quiet voice の such と、後ろの that 節が呼応している。in such a quiet voice ほど静かな声だった、その結果どうなったかを述べるのが "
            "that 以下で、分解図でも V の外に並ぶ 2 つ目の ( M ) になる。spoke は目的語を取らない自動詞なので、that 節を O と読むと置き場所がなく、主節が第3文型に化けてしまうので誤り。"
            "a quiet voice を後ろから説明する形容詞のカタマリと取ると、声そのものの中身を that 節が述べることになり、患者が頼んだという別の出来事の説明にならないので誤り。"
            "The pharmacist にかかると取ると、that 節との間に spoke in such a quiet voice がまるごと挟まっており、名詞から遠く離れた "
            "that 節がその名詞を限定することはないので誤り。"},
    {"id": "G2",
     "syn": "too-to",
     "en": "The young sprinter was too anxious about her start to run the first fifty meters at her usual speed.",
     "dsl": "{S:The young sprinter} {V:was} {C:too anxious about her start} ( M: {V':to run} {O':the first fifty meters} ( M': at her usual speed ) ) .",
     "pat": "第2文型（SVC）",
     "tag": "too … to の否定的な意味",
     "notes": [
               "too … to … は否定語を使わずに「…すぎて〜できない」を表す。to の前で切って程度を読む。",
               "was の後ろの too anxious about her start は主語の状態を述べる C で、この文は第2文型である。",
               "to run 以下は名詞にかかる形容詞ではなく、too と呼応して程度と結果を示す副詞のカタマリになる。",
               "anxious about のように形容詞が呼び出す前置詞は、C のマスの中に残したまま 1 かたまりで見る。"],
     "ja": "その若いスプリンターはスタートのことを気にしすぎていて、最初の五十メートルをいつもの速さで走ることができなかった。",
     "q": "この文の主節の文型として最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "was が V で、too anxious about her start を O にとる第3文型である",
                 "was が V で、too anxious about her start が C にあたる第2文型である",
                 "was が V で、her start が O、to run 以下が C にあたる第5文型である",
                 "was が V で、その後ろに O も C も無く修飾語だけが続く第1文型である"],
     "ans": 1,
     "exp": "was の後ろの too anxious about her start は、主語がどういう状態かを述べる補語なので、この文は第2文型である。too … to … は否定語を使わずに「…すぎて〜できない」を表す形で、"
            "to run 以下は too と呼応して程度と結果を示す副詞のカタマリになる。O と取ると、be 動詞が目的語を取ることになり、しかも主語と同じものを指す関係が説明できないので誤り。"
            "her start を O、to run 以下を C と取ると、彼女のスタートが走るという意味になってしまい、was を第5文型の動詞として使うことになるので誤り。O "
            "も C も無い第1文型と取ると、was だけでは文の意味が完結せず、too anxious about her start の置き場所が消えるので誤り。"},
    {"id": "G3",
     "syn": "that-of",
     "en": "Under the new lighting, the colors of the restored ceiling look far brighter than those of the unrestored section.",
     "dsl": "( M: Under the new lighting ) , {S:the colors} <M: of the restored ceiling> {V:look} {C:far brighter} ( M: {接:than} {S':those} <M': of the unrestored section> ) .",
     "pat": "第2文型（SVC）",
     "tag": "比較の代用 those of",
     "notes": [
               "比較の相手をそろえるために、前に出た名詞のくり返しを that / those で置き換える。複数なら those を使う。",
               "those の直後の of the unrestored section まで含めて、比べる相手 1 つ分のカタマリになる。",
               "文頭の Under the new lighting は比較の相手ではなく、どんな条件での話かを示す ( M ) である。",
               "look は第2文型を作る動詞で、far brighter が C。far は比較級を強める副詞で C の中に残す。"],
     "ja": "新しい照明の下では、修復された天井の色は、修復されていない部分の色よりもはるかに明るく見える。",
     "q": "than those of the unrestored section の those は何を指しているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "the restored ceiling を受けており、修復した天井そのものと比べていることを示す",
                 "the new lighting を受けており、新しい照明の明るさと比べていることを示す",
                 "the colors を受けており、修復していない部分の色と比べていることを示す",
                 "the colors of the restored ceiling 全体を受け、同じ天井の色をもう一度指している"],
     "ans": 2,
     "exp": "those は前に出た名詞のくり返しを避ける代用の語で、ここでは the colors を受けている。than those of the unrestored section "
            "は、the colors of the restored ceiling と、修復していない部分の色とを比べる形で、比べる相手をそろえるためにこの those が要る。"
            "the restored ceiling を受けると取ると、色と天井という違うものを比べることになり、brighter が何について明るいのか決まらないので誤り。the "
            "new lighting を受けると取ると、Under the new lighting は文全体の条件を示す副詞のカタマリで比較の相手ではないので誤り。the colors "
            "of the restored ceiling の全体を受けると取ると、同じものどうしを比べることになり、比較そのものが成り立たなくなるので誤り。"},
    {"id": "G4",
     "syn": "compound-relative",
     "en": "Whatever the committee decides at tomorrow's meeting will affect the working hours of every employee in the factory.",
     "dsl": "[ S: {O':Whatever} {S':the committee} {V':decides} ( M': at tomorrow's meeting ) ] {V:will affect} {O:the working hours} <M: of every employee <M': in the factory> > .",
     "pat": "第3文型（SVO）",
     "tag": "複合関係代名詞 whatever",
     "notes": [
               "Whatever は先行詞を自分の中に含む複合関係代名詞で、節の全体が名詞のカタマリになる。",
               "コンマが無く、後ろの will affect に主語が無い。だから譲歩ではなく主語の名詞節だと決まる。",
               "カタマリの中では Whatever が decides の目的語。中に目的語の欠けがあることが見分けの手がかり。",
               "of every employee は the working hours の核から外に出し、名詞にかかる形容詞のカタマリとして示す。"],
     "ja": "委員会が明日の会議で決めることは何であれ、工場のすべての従業員の労働時間に影響する。",
     "q": "この文の主節の主語 (S) にあたるのはどれか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "the committee で、決定を下す側がそのまま主節の動作主になっている",
                 "Whatever の 1 語で、後ろの the committee decides はコンマの無い挿入である",
                 "the working hours で、will affect の後ろに置かれた名詞が主語である",
                 "Whatever the committee decides at tomorrow's meeting の全体である"],
     "ans": 3,
     "exp": "Whatever は先行詞を自分の中に含む複合関係代名詞で、Whatever the committee decides at tomorrow's meeting の全体が "
            "1 つの名詞のカタマリになり、will affect の主語として働く。カタマリの中では Whatever が decides の目的語で、決められる中身そのものを指している。"
            "the committee を主語と取ると、Whatever が宙に浮き、しかも decides と will affect という 2 つの述語を 1 つの主語が支えることになるので誤り。"
            "Whatever の 1 語だけを主語と取ると、後ろの部分が挿入になるが、挿入はコンマなどで区切るのが普通で、ここにはその印が無いので誤り。the working hours "
            "を主語と取ると、動詞の後ろの名詞を主語と読むことになり、動詞の前に主語が無い文になってしまうので誤り。"},
    {"id": "G5",
     "syn": "do-emphasis",
     "en": "The old law does allow street traders to stay in the square until midnight on the night of the winter festival.",
     "dsl": "{S:The old law} {V:does allow} {O:street traders} [ C: {V':to stay} ( M': in the square ) ( M': until midnight ) ( M': on the night <M'': of the winter festival> ) ] .",
     "pat": "第5文型（SVOC）",
     "tag": "強調の do",
     "notes": [
               "強調の do は、過去でも疑問でも否定でもない場所に現れ、直後に動詞の原形を連れてくる。",
               "does allow は 1 つのマスにまとめる。助動詞は動詞と同じマスに入れるのがこの教材の約束である。",
               "allow は O と to 不定詞の C を取る第5文型。C は動詞を含むので囲んで中まで分解する。",
               "三単現の s が allow ではなく does に付き、直後が原形になっている点も強調の do の目印である。"],
     "ja": "その古い法律は、冬の祭りの夜、露天商が広場に真夜中までいることを確かに認めている。",
     "q": "does allow の does はどのような働きをしているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "allow を強め、確かに認めているのだという肯定の意味を押し出している",
                 "疑問文をつくる助動詞で、後ろの語順が疑問文と同じになっている",
                 "否定の not が省かれた形で、実際には認めていないことを示している",
                 "allow の代わりに置かれた代動詞で、前に出た動詞を受け直している"],
     "ans": 0,
     "exp": "does allow の does は、後ろの動詞の意味を強める強調の do で、確かに認めているのだ、という肯定の押しを加える。過去でも疑問でも否定でもないのに do "
            "が現れ、しかも直後に原形の allow が続いたら、この用法を疑う。疑問文をつくる助動詞と取ると、The old law does allow は主語が先に来ており疑問文の語順ではないので誤り。"
            "not が省かれた形と取ると、否定語は省略できず、補ってしまうと後半の内容と矛盾するので誤り。代動詞と取ると、代動詞はくり返しを避けるために動詞を置かない形で使うのに、"
            "ここでは allow が実際に書かれているので誤り。"},
    {"id": "G6",
     "syn": "insertion",
     "en": "The autumn storms along this coast, most local fishermen say, cause far less damage than the sudden fogs of early spring.",
     "dsl": "{S:The autumn storms} <M: along this coast> , ( 挿入: {S':most local fishermen} {V':say} ) , {V:cause} {O:far less damage} ( M: {接:than} {S':the sudden fogs} <M': of early spring> ) .",
     "pat": "第3文型（SVO）",
     "tag": "コンマにはさまれた挿入",
     "notes": [
               "コンマ 2 つにはさまれた S と V の組は、話し手以外の判断を差し込む挿入で、骨組みには数えない。",
               "挿入を取り去っても文が成り立つかどうかで見分ける。残った側の動詞が主節の V である。",
               "The autumn storms は複数なので、対応するのは三単現の形ではない cause である。動詞の形も手がかり。",
               "along this coast は直前の名詞を後ろから説明する形容詞のカタマリで、主語 1 つ分に含めて読む。"],
     "ja": "この海岸沿いの秋の嵐は、地元の漁師の多くが言うには、早春の突然の霧よりもはるかに小さな被害しかもたらさない。",
     "q": "この文の主節の動詞 (V) にあたるのはどれか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "say で、most local fishermen を主語にとり文全体をまとめている",
                 "cause で、コンマにはさまれた挿入をまたいで主語を受けている",
                 "cause と say が対等に並び、2 つの動詞が 1 つの主語を共有している",
                 "cause は不定詞相当で、実際の主節の動詞はコンマの中の say である"],
     "ans": 1,
     "exp": "コンマにはさまれた most local fishermen say は、話し手以外の判断を差し込む挿入で、主節の骨組みからは外れている。この部分を取り去ると、The "
            "autumn storms along this coast が主語、cause が動詞という骨組みが残る。say を主節の動詞と取ると、コンマの外に残る主語が述語を失い、"
            "cause の置き場所も無くなるので誤り。cause と say が対等に並ぶと取ると、対等な並列には接続詞が要るうえ、コンマ 2 つで囲む形にもならないので誤り。cause "
            "を不定詞相当と取ると、to も付いておらず、主語に対する述語がどこにも無い文になるので誤り。"},
    {"id": "G7",
     "syn": "only-inversion",
     "en": "Only at the very end of the announcement did the station staff mention the change in the evening timetable.",
     "dsl": "( M: Only at the very end < M': of the announcement > ) {助:did} {S:the station staff} {V:mention} {O:the change} <M: in the evening timetable> .",
     "pat": "第3文型（SVO）",
     "tag": "Only … による倒置",
     "notes": [
               "Only で始まる副詞句が文頭に出ると、後ろは疑問文と同じ語順になり、助動詞が主語の前に出る。",
               "did の後ろの名詞が主語。助動詞と動詞が主語をはさんで割れている形だと見抜く。",
               "倒置なので did の後ろの動詞は原形の mention になる。時制は did が背負っていると読む。",
               "文頭の Only at the very end … は副詞 Only ＋前置詞句のカタマリで、名詞のカタマリではないから主語になれない。"],
     "ja": "アナウンスのいちばん最後になってようやく、駅員は夕方の時刻表の変更について口にした。",
     "q": "did the station staff mention という語順になっているこの文の主語 (S) はどれか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "Only at the very end で、文頭の副詞句がそのまま主語になっている",
                 "the announcement で、of の後ろの名詞が主語の働きをしている",
                 "the station staff で、文頭の Only … に引かれて did の後ろに回っている",
                 "the change で、mention の後ろに置かれた名詞が主語になっている"],
     "ans": 2,
     "exp": "文頭に Only … の限定句が出ると、後ろは疑問文と同じ語順になる。ここでも助動詞の did が主語の前に飛び出しており、did の後ろに置かれた the station "
            "staff が主節の主語である。did を取り除いて動詞を過去形に戻せば、普通の語順に戻る。Only at the very end を主語と取ると、これは副詞 Only "
            "＋前置詞句のカタマリで名詞のカタマリではなく主語になれず、did の後ろの名詞が浮いてしまうので誤り。the announcement を主語と取ると、of の後ろの名詞は直前の名詞を説明しているだけで、"
            "文の主語にはなれないので誤り。the change を主語と取ると、これは mention の目的語で、何を口にしたのかを表す名詞なので誤り。"},
    {"id": "G8",
     "syn": "subjunctive-inversion",
     "en": "Had the diary been found fifty years earlier, the story of the village would have taken a very different shape.",
     "dsl": "( M: {助:Had} {S':the diary} {V':been found} ( M': fifty years earlier ) ) , {S:the story} <M: of the village> {V:would have taken} {O:a very different shape} .",
     "pat": "第3文型（SVO）",
     "tag": "if の省略による倒置",
     "notes": [
               "仮定法の if 節は、if を落として助動詞や be 動詞を主語の前に出す倒置の形にできる。",
               "文頭が Had で、後ろに主語と過去分詞が続いたら、疑問文ではなく仮定法過去完了の倒置を疑う。",
               "主節が would have taken という形になっていることが、仮定法過去完了だと確かめる裏づけになる。",
               "of the village は the story の核から外に出し、名詞にかかる形容詞のカタマリとして示す。"],
     "ja": "その日記が五十年早く見つかっていたら、その村の物語はまったく違った形になっていただろう。",
     "q": "文頭の Had the diary been found について、省略されている語の説明として最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "When が省かれ、日記が見つかった時期を述べる副詞節になっている",
                 "疑問文の Did が Had に変わったもので、省略されている語は無い",
                 "Because が省かれ、後半の内容の理由を述べる副詞節になっている",
                 "If が省かれ、その埋め合わせに Had が主語の前に出た仮定法の形である"],
     "ans": 3,
     "exp": "仮定法の条件節では、if を省いて助動詞や be 動詞を主語の前に出すことができる。ここも文頭の if が消え、had が主語の前に回って Had the diary "
            "been found という形になっている。主節が would have taken という形であることも手がかりになる。When が省かれたと取ると、時を表す節では倒置は起こらず、"
            "実際に見つかったという事実の話になってしまうので誤り。疑問の Did が変化した形と取ると、コンマの後ろに主節が続いており疑問文になっていないので誤り。Because "
            "が省かれたと取ると、理由の節も倒置しないうえ、事実を述べる文と読むと主節の形と合わないので誤り。"},
    {"id": "G9",
     "syn": "superlative-equivalent",
     "en": "No other dish on the menu requires as much care as the fish stew that the chef serves on Fridays.",
     "dsl": "{S:No other dish} <M: on the menu> {V:requires} {O:as much care} ( M: {接:as} {S':the fish stew} <M': {O'':that} {S'':the chef} {V'':serves} ( M'': on Fridays ) > ) .",
     "pat": "第3文型（SVO）",
     "tag": "最上級と同じ内容を表す形",
     "notes": [
               "No other に単数の名詞が続き、後ろで as … as と比べる形は、最上級と同じ内容を表す。",
               "比べているのは requires の程度で、as much care as の後ろが比較の相手になる。",
               "as の後ろは the fish stew までで、その後の that 節はどのシチューかを絞る形容詞のカタマリである。",
               "on the menu は直前の No other dish を後ろから説明し、比べる範囲を示している。"],
     "ja": "献立のほかのどの料理も、料理長が金曜日に出すその魚のシチューほどの手間を必要としない。",
     "q": "この文は内容としてどのようなことを述べているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "献立の中ではこの魚のシチューがいちばん手間のかかる料理だということ",
                 "この魚のシチューと同じだけ手間のかかる料理がほかにもあるということ",
                 "この魚のシチューは金曜日以外には手間をかけずに作られるということ",
                 "料理長は献立のどの料理にも同じだけの手間をかけているということ"],
     "ans": 0,
     "exp": "No other dish on the menu requires as much care as the fish stew は、このシチュー以外のどの料理もこれほどの手間はかからない、"
            "と述べており、最上級と同じ内容になる。だから、いちばん手間がかかるのはこの魚のシチューだということになる。同じだけ手間のかかる料理がほかにもあると取ると、文頭の No "
            "other がほかの料理をすべて外しているので誤り。金曜日以外は手間をかけないと取ると、on Fridays は the chef serves にかかり、いつ出すかを言っているだけなので誤り。"
            "どの料理にも同じだけの手間をかけていると取ると、比較そのものが打ち消され、as much care as という形が意味を失うので誤り。"},
    {"id": "G10",
     "syn": "ellipsis-clause",
     "en": "Although rewritten several times before publication, the short novel still keeps the ending that its author first imagined.",
     "dsl": "( M: {接:Although} {V':rewritten} ( M': several times ) ( M': before publication ) ) , {S:the short novel} {M:still} {V:keeps} {O:the ending} <M: {O':that} {S':its author} {M':first} {V':imagined} > .",
     "pat": "第3文型（SVO）",
     "tag": "副詞節中の S + be の省略",
     "notes": [
               "接続詞の直後にいきなり過去分詞が来たら、主語と be 動詞が省かれた副詞節を疑う。",
               "省けるのは主節の主語と同じ場合だけで、ここでは the short novel を受ける主語と be 動詞が省かれている。",
               "分詞は素の語で置かず、副詞節の中の動詞として示す。省略があっても節の骨組みは変わらない。",
               "the ending の後ろの that は関係代名詞で、imagined の目的語が欠けているので目的格だと分かる。"],
     "ja": "出版の前に何度も書き直されたけれども、その短い小説は作者が最初に思い描いた結末を今も保っている。",
     "q": "Although rewritten several times before publication では、Although の直後に何が省略されているか。最も適切なものを "
          "1 つ選びなさい。",
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
    {"id": "G11",
     "syn": "infinitive-adjective",
     "en": "In an ordinary school week, learners of a second language rarely have a real chance to use it naturally outside the classroom.",
     "dsl": "( M: In an ordinary school week ) , {S:learners} <M: of a second language> {M:rarely} {V:have} {O:a real chance} <M: {V':to use} {O':it} {M':naturally} ( M': outside the classroom ) > .",
     "pat": "第3文型（SVO）",
     "tag": "不定詞の形容詞用法",
     "notes": [
               "名詞の直後の to 不定詞は、その名詞を後ろから説明する形容詞のはたらきをすることが多い。",
               "目的の副詞と読むと a real chance が何の機会か決まらない。名詞に不足が残る側を選ぶ。",
               "to 不定詞のカタマリに入るのは副詞 naturally と前置詞句 outside the classroom で、どちらも use にかかる。文頭の In an "
               "ordinary school week はこのカタマリの外にあり、主節の have にかかる。",
               "of a second language は learners の核から外に出し、名詞にかかる形容詞のカタマリとして示す。"],
     "ja": "ふつうの学校の一週間のうちに、第二言語の学習者が、教室の外でそれを自然に使う本当の機会を持つことはめったにない。",
     "q": "to use it naturally outside the classroom は、どの語にかかっているか。最も適切なものを 1 つ選びなさい。",
     "choices": [
                 "have にかかり、何のために機会を持つのかという目的を表している",
                 "learners にかかり、どのような学習者なのかを後ろから説明している",
                 "a real chance にかかり、どのような機会なのかを後ろから説明している",
                 "a second language にかかり、その言語がどう使われるかを説明している"],
     "ans": 2,
     "exp": "名詞の直後に置かれた to 不定詞は、その名詞を後ろから説明する形容詞のはたらきをする。ここでも to use it naturally outside the classroom "
            "は直前の a real chance にかかり、どういう機会が乏しいのかを述べている。have にかかる目的の副詞と取ると、機会を持つ目的が言語を使うことになり、a real "
            "chance が何の機会なのか決まらないまま残るので誤り。learners にかかると取ると、間に rarely have a real chance がまるごと挟まっており、"
            "離れた名詞に後ろからかかることはないので誤り。a second language にかかると取ると、of で始まるカタマリの中の名詞に文末までのカタマリがかかることになり、"
            "it が指すものと重なって意味が回らなくなるので誤り。なお文頭の In an ordinary school week は主節の have にかかる ( M ) で、to "
            "不定詞のカタマリの中には入らない。"},
    {"id": "G12",
     "syn": "relative-possessive",
     "en": "Last Sunday the newspaper finally corrected a report whose opening paragraph had named the wrong street.",
     "dsl": "( M: Last Sunday ) {S:the newspaper} {M:finally} {V:corrected} {O:a report} <M: {S':whose opening paragraph} {V':had named} {O':the wrong street} > .",
     "pat": "第3文型（SVO）",
     "tag": "所有格の関係代名詞 whose",
     "notes": [
               "whose は所有格の関係代名詞で、直前の名詞と後ろの名詞を「〜の」で結びつける。",
               "whose の後ろには冠詞の無い名詞が直接続き、その名詞が関係詞節の主語や目的語になる。",
               "関係詞節の中で主語も目的語も欠けていないのが所有格の目印。欠けがあれば主格か目的格である。",
               "文頭の Last Sunday はいつの話かを示す ( M ) で、主語ではない。主語は the newspaper である。"],
     "ja": "先週の日曜日、その新聞はようやく、書き出しの段落が間違った通りの名前を挙げていた記事を訂正した。",
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
]

# ---------------------------------------------------------------- 第3部 英文解釈
PART3 = [
    {"g": "①　関係詞", "sub": "かかり先を決める", "pool": "3-1", "items": [
        {"id": "D1",
         "syn": "prep-relative",
         "en": "The many channels through which false information now spreads across the internet have forced many newspapers to rethink the way they check their sources.",
         "dsl": "{S:The many channels} <M: ( M': through which ) {S':false information} {M':now} {V':spreads} ( M': across the internet ) > {V:have forced} {O:many newspapers} [C: {V':to rethink} {O':the way} <M': {S'':they} {V'':check} {O'':their sources} > ] .",
         "pat": "第5文型（SVOC）",
         "tag": "前置詞つき関係代名詞 through which",
         "notes": [
                   "急所は The many channels と have forced の間に 9 語の関係詞節が割り込むこと。先に目に入る spreads を主節の V "
                   "と取ると、文全体の骨組みが組めなくなる。",
                   "&lt;M: through which … across the internet&gt; を丸ごと外すと The many channels have "
                   "forced many newspapers … が残る。外して残る形が主節で、S V O C の第5文型だと決まる。",
                   "through which は前置詞つきの関係代名詞。through は節の中の spreads にかかる（spread through the channels）ので、"
                   "( M': through which ) と副詞のカタマリで囲んで示す。",
                   "節の中に名詞の欠けが無ければ、関係副詞か「前置詞 + 関係代名詞」のどちらか。関係詞の直前に前置詞が付いていればこちら、付いていなければ関係副詞（D2 の "
                   "why）である。",
                   "force O to do の [C: to rethink … ] は C。{O:many newspapers} と rethink の間に主語述語の関係が立つので、"
                   "「見直すために」の副詞用法では取れない（何を強いたのかが文から消える）。",
                   "{O':the way} の後ろの &lt;M': they check their sources&gt; は関係副詞 that または in which "
                   "が省略された節。the way how とは言えないので、the way + 完全な文 で 1 つの名詞のかたまりと覚える。"],
         "ja": "偽の情報が今やインターネット中に広まっていく、その数多くの経路が、多くの新聞社に情報源の確認の仕方を見直すことを迫っている。",
         "points": [
                    "through which 節を The many channels にかけ、「偽情報が広まっていく数多くの経路」と S を一つの名詞のかたまりとして訳せている",
                    "主節の動詞が have forced であって spreads ではないと分かる訳になっている",
                    "force O to do を「O に〜することを迫る／〜せざるを得なくする」と第5文型で訳せている",
                    "the way they check their sources を「情報源の確認の仕方」と名詞のまとまりで訳せている"]},
        {"id": "D2",
         "syn": "relative-adverb",
         "en": "One reason why so many beginners give up the piano within a few weeks is said to be that they expect their first attempts to sound completely smooth.",
         "dsl": "{S:One reason} <M: {M':why} {S':so many beginners} {V':give up} {O':the piano} ( M': within a few weeks ) > {V:is said} [C: {V':to be} [C': {接:that} {S'':they} {V'':expect} {O'':their first attempts} [C'': {V'':to sound} {C'':completely smooth} ] ] ] .",
         "pat": "第2文型（SVC）",
         "tag": "関係副詞 why",
         "notes": [
                   "急所は主節が One reason is said to be that … の第2文型だと最後まで見えないこと。{S:One reason} と {V:is "
                   "said} の間に 12 語の関係副詞節が割り込んでいる。",
                   "&lt;M: why … within a few weeks&gt; を丸ごと外すと One reason is said to be that … が残り、"
                   "S と V が隣り合う。外しても主節が立つものが修飾のカタマリだと確かめる手順である。",
                   "関係詞の後ろが完全な文なら、関係副詞か「前置詞 + 関係代名詞」のどちらか。直前に前置詞が無いので why は関係副詞。名詞が 1 つ欠けていれば裸の関係代名詞である。",
                   "why は節の中で副詞の働きをするので {M':why} と示す。give up の目的語は the piano ですでに埋まっており、why の入る場所は残っていないことを図で確かめる。",
                   "is said to be … は「〜だと言われている」。受動の be は V と同じマスに入れるので {V:is said} とし、その後ろの [C: "
                   "to be that … ] が補語になる。同じ that でも D6 の [同格: ] は直前の名詞の中身を言い換えるもので、こちらは to be の後ろに立つ補語なので働きが違う。",
                   "[C': that … ] の中はさらに S V O C になっている。{O'':their first attempts} と to sound completely "
                   "smooth の間に主語述語の関係が立つので、C は [ ] で囲んで中も分解する（規約13）。"],
         "ja": "これほど多くの初心者が数週間でピアノを投げ出してしまう理由の一つは、初めて弾いたものがまったくなめらかに聞こえることを期待してしまう点にあると言われている。",
         "points": [
                    "why 節を One reason にかけ「〜する理由の一つは」と訳せている",
                    "is said to be … を「〜だと言われている／〜だとされる」と訳し、断定した言い方にしていない",
                    "to be の後ろの that 節を補語と見て「〜ということだ／〜という点にある」と訳せている",
                    "give up the piano within a few weeks を「数週間でピアノを投げ出す」と訳せている",
                    "expect their first attempts to sound completely smooth を第5文型と見て「初めて弾いたものがまったくなめらかに聞こえることを期待する」と訳せている"]},
        {"id": "D3",
         "syn": "what-clause",
         "en": "What discourages many new volunteers is the paperwork that the small charities they support must complete before the end of each year.",
         "dsl": "[S: {S':What} {V':discourages} {O':many new volunteers} ] {V:is} {C:the paperwork} <M: {O':that} {S':the small charities} <M': {S'':they} {V'':support} > {V':must complete} ( M': before the end < M'': of each year > ) > .",
         "pat": "第2文型（SVC）",
         "tag": "関係代名詞 what（先行詞を含む）",
         "notes": [
                   "急所は文頭の What。疑問詞ではなく先行詞を含む関係代名詞で、What discourages many new volunteers 全体が 1 つの名詞のカタマリ "
                   "[S: ] になる。",
                   "What の前に名詞が無いことが「先行詞込み」の目印。節の中では {S':What} と主語の働きをしており、the thing which … に置き換えても意味が変わらない。",
                   "主節の V は {V:is} で、[S: What … volunteers ] ＝ {C:the paperwork} という第2文型。文頭の What "
                   "に引かれて疑問文と読むと、V が 2 つあるように見えて骨組みが決まらない。",
                   "&lt;M: that … each year&gt; の中に、もう一枚 &lt;M': they support&gt; が入る二重構造。外側の {O':that} "
                   "は must complete の目的語で、内側は the small charities を修飾する目的格の関係詞が省略された節である。",
                   "動詞が discourages / support / must complete / is と 4 つ並ぶ。囲みの外に立っているのは is だけなので、"
                   "ラベルのダッシュの本数を数えれば主節の V が 1 つに決まる。"],
         "ja": "多くの新しいボランティアの意欲をくじくのは、彼らが支援している小さな慈善団体が毎年、年の終わりまでに仕上げなければならない事務書類である。",
         "points": [
                    "What … volunteers を「〜するのは／〜するもの」と名詞のかたまりとして主語に訳せている",
                    "主節の動詞が is で、What 節 ＝ the paperwork という第2文型だと分かる訳になっている",
                    "that … must complete を the paperwork にかけて訳せている",
                    "they support を the small charities にかけ、「彼らが支援している小さな慈善団体」と二重の修飾を訳し分けられている"]},
        {"id": "D4",
         "syn": "chain-relative",
         "en": "The step which professional bakers insist is the most important in making good bread is simply to wait until the dough has fully risen.",
         "dsl": "{S:The step} <M: {S':which} ( 挿入: {S'':professional bakers} {V'':insist} ) {V':is} {C':the most important} ( M': in making good bread ) > {V:is} {M:simply} [C: {V':to wait} ( M': {接:until} {S'':the dough} {助:has} {M'':fully} {V'':risen} ) ] .",
         "pat": "第2文型（SVC）",
         "tag": "連鎖関係代名詞",
         "notes": [
                   "連鎖関係代名詞。which の直後に professional bakers insist が割り込むので、which を insist の目的語だと取ってしまうのが急所である。",
                   "( 挿入: professional bakers insist ) を括って外すと &lt;M: which is the most important "
                   "…&gt; が残り、{S':which} が {V':is} の主語だと分かる。insist の後ろは接続詞 that が省略された節である。",
                   "記号は 3 つを使い分ける。主節相当の節がそのまま割り込むもの（professional bakers insist 型）が 挿入、名詞の言い換えが 同格、"
                   "関係詞節は非制限用法でも形容詞のカタマリなので &lt;M&gt; である。",
                   "is が 2 つある。&lt; &gt; を外して残る後ろの {V:is} が主節の V で、The step is to wait … が骨組み。ここで第2文型だと確定する。",
                   "文末は {助:has} {M'':fully} {V'':risen} と 3 マスに割る。助動詞と動詞の間に副詞が割り込んだら 助 を独立させ、副詞は "
                   "M にする（規約11）。",
                   "{M:simply} は述語にかかる副詞。[C: to wait until … ] が C で、The step ＝ to wait … という S ＝ "
                   "C の関係が立つ。( M': until … ) は wait にかかる副詞節である。"],
         "ja": "プロのパン職人がおいしいパンを焼くうえで最も大切だと言い張る工程は、ただ生地が十分にふくらむまで待つということにすぎない。",
         "points": [
                    "which … is the most important in making good bread を The step にかけて訳せている",
                    "professional bakers insist を挿入として処理し、which を insist の目的語にしていない",
                    "主節の動詞が後ろの is だと分かり、「工程は〜まで待つことである」と第2文型で訳せている",
                    "simply を「ただ〜だけ／〜にすぎない」と述語にかけて訳せている",
                    "until the dough has fully risen を wait にかかる副詞節として訳せている"]},
        {"id": "D5",
         "syn": "nonrestrictive",
         "en": "Over the past decade, many firms have replaced their fixed desks with shared workspaces, which has reduced costs but may also have weakened the sense of belonging among the staff.",
         "dsl": "( M: Over the past decade ) , {S:many firms} {V:have replaced} {O:their fixed desks} ( M: with shared workspaces ) , <M: {S':which} {V':has reduced} {O':costs} {接:but} {助:may} {M':also} {V':have weakened} {O':the sense} <M': of belonging among the staff > > .",
         "pat": "第3文型（SVO）",
         "tag": "コンマ + which の非制限用法",
         "notes": [
                   "急所は which の先行詞。直前の名詞 shared workspaces ではなく、コンマまでの内容全体（固定席を共用スペースに置き換えたこと）を受けている。",
                   "決め手は動詞の has。先行詞が複数形の shared workspaces なら have reduced になるはずで、単数扱いの has が「前の内容全体」を受けている証拠である。"
                   "同じ文の many firms には have が付いていることと見比べる。",
                   "&lt;M: which … among the staff&gt; を外しても主節は完全に成立する。非制限用法でも関係詞節は形容詞のカタマリなので、記号は制限用法と同じ "
                   "&lt;M&gt; を使う。コンマの有無で記号は変わらない。",
                   "記号の 3 分割をここで固める。節がそのまま割り込むのが ( 挿入: )（D4 の professional bakers insist）、名詞の言い換えが "
                   "[ 同格: ]（D6 の that 節）、関係詞節は非制限用法でも &lt;M&gt; である。",
                   "節の中に {V':has reduced} と {V':have weakened} が {接:but} で 2 つ並び、{S':which} が両方の主語を兼ねている。"
                   "後ろは {助:may} {M':also} {V':have weakened} と割り、副詞 also を V のマスに入れない（規約11）。",
                   "文頭の ( M: Over the past decade ) は主節の外側の副詞のカタマリで S ではない。{O':the sense} は核だけをマスにし、"
                   "of 以下は &lt;M': of belonging among the staff&gt; として外に出す（規約6）。"],
         "ja": "この十年ほどで、多くの企業が固定席を共用の作業スペースに置き換えてきたが、そのことは費用を減らした一方で、社員の帰属意識を弱めもしたかもしれない。",
         "points": [
                    "コンマ + which の先行詞を前半の内容全体と取り、「そのことは／その結果」と訳せている",
                    "has reduced と have weakened の 2 つの動詞がともに which を主語にしていると分かる訳になっている",
                    "replace A with B を「A を B に置き換える」と訳せている",
                    "may also have weakened を「弱めもしたかもしれない」と控えめな推量として訳せている",
                    "Over the past decade を「この十年ほどで」と主節の外側の修飾として訳し、主語にしていない"]},
        {"id": "D6",
         "syn": "appositive-that",
         "en": "The old view that history is always written by the winners may have narrowed the range of voices that appear in most school textbooks.",
         "dsl": "{S:The old view} [同格: {接:that} {S':history} {助:is} {M':always} {V':written} ( M': by the winners ) ] {V:may have narrowed} {O:the range} <M: of voices <M': {S'':that} {V'':appear} ( M'': in most school textbooks ) > > .",
         "pat": "第3文型（SVO）",
         "tag": "名詞 + 同格の that 節",
         "notes": [
                   "that の後ろは history is always written by the winners で、S も O も欠けていない完全な文。だから関係代名詞ではなく同格の "
                   "that であり、記号は名詞のカタマリ [同格: ] を使う。",
                   "同じ文に that が 2 つある。後ろの &lt;M'': that appear …&gt; のほうは appear の主語が欠けているので関係代名詞で、"
                   "{S'':that} と示す。欠けの有無だけが見分けの基準である。",
                   "[同格: that … by the winners ] を丸ごと外すと The old view may have narrowed the range "
                   "… が残る。同格節は S と V を 8 語ぶん引き離す装置だと考えるとよい。",
                   "主節の V は {V:may have narrowed}。助動詞も完了の have も V と同じマスに入れる。一方 同格節の中は always が割り込むので "
                   "{助:is} {M':always} {V':written} と 助 を独立させる。同じ規約の表と裏である。",
                   "{O:the range} に続く of 句は外に出し、その中の voices にさらに関係詞節がかかる。&lt;M: of voices &lt;M': "
                   "that appear …&gt;&gt; と入れ子にして、関係詞節のかかる先が range ではなく voices だと図で示している。"],
         "ja": "歴史は常に勝者によって書かれるという古くからの見方が、たいていの学校の教科書に現れる声の幅を狭めてきたのかもしれない。",
         "points": [
                    "that 節を The old view の同格と見て「〜という見方」と訳せている",
                    "主語が The old view、動詞が may have narrowed だと分かる訳になっている",
                    "後ろの that appear in most school textbooks を voices にかけ、range にかけていない",
                    "may have done を「〜したのかもしれない」と控えめな推量として訳せている",
                    "is always written by the winners を受動態として「勝者によって書かれる」と訳せている"]},
    ]},
    {"g": "②　比較・倒置・強調", "sub": "何と何を比べているか／なぜ語順が崩れたか", "pool": "3-2", "items": [
        {"id": "E1",
         "syn": "not-so-much-as",
         "en": "The value of a university education lies not so much in the facts it provides as in the habits of mind it develops.",
         "dsl": "{S:The value} <M:of a university education> {V:lies} ( M: not so much in the facts <M': {S'':it} {V'':provides} > ) ( M: {接:as} in the habits <M':of mind <M'': {S'':it} {V'':develops} > > ) .",
         "pat": "第1文型（SV）",
         "tag": "not so much A as B",
         "notes": [
                   "急所は as の正体。「〜として」でも「〜のとき」でもなく、not so much A <b>as</b> B「A というよりむしろ B」の相棒である。lies "
                   "の直後に not so much を見た時点で、対応する as を文の後ろへ先に探しに行く。",
                   "A と B は必ず<b>同じ形</b>で並ぶ。( M: not so much in the facts … ) と ( M: as in the habits "
                   "… ) はどちらも in で始まる副詞のカタマリで、as は B 側のカタマリの頭に置く。形のそろい方が比較の相手を決める証拠になる。",
                   "この as は<b>接続詞</b>であって関係代名詞ではない。比較の as 節・than 節では前の節と重なる語句が落ちるのが普通で、ここも as の後ろに節が立たず前置詞句だけが残っている。"
                   "欠けを見て関係詞と読み替えないこと。",
                   "&lt; it provides &gt; と &lt; it develops &gt; は関係代名詞が省略された形容詞のカタマリ。名詞の直後に主語と動詞が続いたら省略を疑う。"
                   "2 つとも外せば lies not so much in A as in B の骨格が残り、主節は S と V だけの第1文型と決まる。",
                   "lies と ( not so much in the facts … ) を別のマスにしたのは規約どおり。<b>他動詞の群動詞（動詞＋前置詞）を 1 マスにしてよいのは受動態にできるときだけ</b>で、"
                   "lie in はそれに当たらないから前置詞句は M として外に出す。動詞＋副詞辞（come out / put off）なら 1 マスでよい。記号を分けても "
                   "lie in「〜にある」と、動詞と切り離さずに意味を取る。"],
         "ja": "大学教育の価値は、それが与えてくれる事実そのものにあるというよりも、むしろそれが育てる考え方の習慣にある。",
         "points": [
                    "not so much A as B を「A というよりむしろ B」と訳し、A に in the facts …、B に in the habits of "
                    "mind … を当てている",
                    "it provides / it develops を関係代名詞の省略と見て、それぞれ the facts・the habits of mind にかけて訳している",
                    "lies in を「〜にある」と訳し、「横たわる」としていない",
                    "2 つの it がともに a university education を指すと分かる訳になっている"]},
        {"id": "E2",
         "syn": "no-more-than",
         "en": "A student who has memorized a single formula is no more a mathematician than a tourist with a phrasebook is a fluent speaker of the language.",
         "dsl": "{S:A student} <M: {S':who} {V':has memorized} {O':a single formula} > {V:is} {C:no more a mathematician} ( M: {接:than} {S':a tourist} <M':with a phrasebook> {V':is} {C':a fluent speaker} <M':of the language> ) .",
         "pat": "第2文型（SVC）",
         "tag": "no more A than B",
         "notes": [
                   "落とし穴は no more … than を「〜より多くない」と量で読むこと。X is no more A than Y is B は<b>両方まとめて否定する</b>形で、"
                   "「Y が B でないのと同様に X も A ではない」と読む。程度の比較にすると主張が逆さになる。",
                   "than の後ろに a tourist … is a fluent speaker … という<b>もう 1 つの文</b>が立っているのが目印。ここが句ではなく節だと分かれば、"
                   "比べられているのが「生徒は数学者だ」と「旅行者は流暢な話し手だ」という 2 つの断定だと見える。",
                   "&lt; M: who has memorized a single formula &gt; を外すと A student is no more a mathematician "
                   "が残り、骨組みは S・V・C の第2文型。完了の has は memorized と同じマスに入れて {V':has memorized} と示す。",
                   "C は no more a mathematician で、補語に立っているのは名詞である。no more は C の中に置いたままにする。more だけを "
                   "M として切り出すと、否定を担う no と離れて「より多く」という量の比較に読み替わってしまう。",
                   "&lt; M': with a phrasebook &gt; は a tourist を後ろから絞り、&lt; M': of the language "
                   "&gt; は a fluent speaker にかかる。どちらも直前の名詞だけを説明しているので ( M ) ではなく &lt; M &gt; で示す。"],
         "ja": "公式を 1 つ暗記しただけの生徒が数学者でないのは、会話帳を持っただけの旅行者がその言語を流暢に話せる人ではないのと同じである。",
         "points": [
                    "no more A than B を「B でないのと同様に A でもない」という全否定で訳している（「旅行者より数学者らしくない」という程度の比較にしていない）",
                    "who has memorized a single formula を A student にかけ、主節の動詞は is だと分かる訳になっている",
                    "than 以下を a tourist with a phrasebook is a fluent speaker of the language という節として訳している",
                    "a fluent speaker of the language を「その言語を流暢に話せる人」と訳せている"]},
        {"id": "E3",
         "syn": "comparative-ellipsis",
         "en": "Pottery students often learn much more useful lessons from the pots that crack in the heat than they can from the ones that come out perfect.",
         "dsl": "{S:Pottery students} {M:often} {V:learn} {O:much more useful lessons} ( M: from the pots <M': {S'':that} {V'':crack} ( M'': in the heat ) > ) ( M: {接:than} {S':they} {助:can} ( M': from the ones <M'': {S'':that} {V'':come out} {C'':perfect} > ) ) .",
         "pat": "第3文型（SVO）",
         "tag": "比較の than 節の省略",
         "notes": [
                   "急所は than の後ろ。they can で切れて動詞が出てこないので、ここで多くの生徒が崩れる。比較の than 節では<b>前の節と重なる部分がまるごと落ちる</b>ので、"
                   "can の後ろに learn useful lessons を補って読む。",
                   "( M: {接:than} {S':they} {助:can} … ) の中に V のマスが無いことが図に出ている。<b>マスの空きそのものが省略の印</b>で、"
                   "助動詞 can だけが残っているのは、落ちた動詞がどこにあったかを教える目印である。",
                   "they が指すのは Pottery students、the ones が指すのは the pots。than 節に lessons が残らず from "
                   "the ones だけが残っていることが、<b>from … は名詞 lessons ではなく動詞 learn の側に付いている</b>証拠で、だからこの前置詞句は "
                   "&lt; M &gt; ではなく ( M ) で示す。",
                   "&lt; that crack in the heat &gt; と &lt; that come out perfect &gt; はどちらも直前の名詞にかかる形容詞のカタマリ。"
                   "2 つとも外すと learn much more useful lessons from the pots という骨組みが見え、主節は S・V・O の第3文型と決まる。",
                   "much more useful lessons はまとめて O の 1 マスに置く。much は more useful を強め、その more useful "
                   "が lessons を説明する<b>質の比較</b>である（数を比べるなら many more lessons という形になり、much は使えない）。比較級を作る "
                   "more を単独で M として切り出すと名詞のカタマリが割れてしまう。"],
         "ja": "陶芸を学ぶ生徒は、熱で割れてしまった作品から、きれいに仕上がった作品から学べるよりもずっと役に立つことを学ぶことが多い。",
         "points": [
                    "than 節の省略を補い、「きれいに仕上がった作品から学べるよりもずっと役に立つことを学ぶ」という質の比較として訳している（「多くを学ぶ」という数の比較にしていない）",
                    "learn A from B の骨格をとらえ、主語が Pottery students、動詞が learn だと分かる訳になっている",
                    "that crack in the heat を the pots に、that come out perfect を the ones にかけて訳し分けている",
                    "the ones が the pots の言い換えだと分かる訳になっている（漠然と「もの」で済ませていない）"]},
        {"id": "E4",
         "syn": "the-more-the-more",
         "en": "The longer a cyclist puts off replacing a worn brake cable, the more expensive the repair needed to make the bicycle safe becomes.",
         "dsl": "( M: {M':The longer} {S':a cyclist} {V':puts off} [ O': {V'':replacing} {O'':a worn brake cable} ] ) , {C:the more expensive} {S:the repair} <M: {V':needed} ( M': {V'':to make} {O'':the bicycle} {C'':safe} ) > {V:becomes} .",
         "pat": "第2文型（SVC）",
         "tag": "the 比較級 …, the 比較級 …",
         "notes": [
                   "落とし穴は文頭の The を冠詞と読んでしまうこと。The＋比較級 で始まり、コンマの後にもう一度 the＋比較級 が来たら「〜すればするほど…」の形である。"
                   "前半が条件、後半が主節と決まる。",
                   "前半の ( ) の中は The longer が先に飛び出しているだけで、中身は主語が a cyclist、動詞が puts off、[ O′ ] が動名詞句 "
                   "replacing a worn brake cable。この [ ] が puts off の目的語にあたる。",
                   "後半は<b>補語が文頭に出た前置</b>で、S と V の順序は変わっていない（the repair … becomes のまま）。並び順どおりに振ると "
                   "C・S・V、戻すと the repair … becomes more expensive となり、<b>戻した形で</b> becomes の後ろが形容詞だから第2文型と確定する。"
                   "E5 のように助動詞が主語の前に出る倒置とは別物である。",
                   "後半の主語は the repair、動詞は文末の becomes。&lt; M: needed to make the bicycle safe &gt; "
                   "が両者を引き離しているので、まず後置修飾を外して主語と動詞を隣り合わせてから文型を決める。needed を主節の動詞と読むと becomes が宙に浮く。",
                   "後置修飾の分詞は素の語で置かず {V':needed} と示し、続く不定詞句も素のまま置かずに ( M': {V'':to make} {O'':the "
                   "bicycle} {C'':safe} ) と中まで刻む。needed の前に be が無いことも、これが主節の述語ではない手掛かりになる。"],
         "ja": "自転車に乗る人がすり減ったブレーキワイヤーの交換を先延ばしにすればするほど、その自転車を安全な状態にするために必要な修理は高くつくものになる。",
         "points": [
                    "the 比較級 …, the 比較級 … を「〜すればするほど…」と訳し、前半を条件、後半を帰結として並べている",
                    "後半の主語が the repair、動詞が becomes だと分かる訳になっている（前に出た the more expensive を戻せている）",
                    "needed to make the bicycle safe を the repair にかかる後置修飾として訳している",
                    "puts off replacing a worn brake cable を「すり減ったブレーキワイヤーの交換を先延ばしにする」と動名詞の目的語として訳せている"]},
        {"id": "E5",
         "syn": "negative-inversion",
         "en": "At no point in the long trial did the witness change the account he had given to the police.",
         "dsl": "( M: At no point <M':in the long trial> ) {助:did} {S:the witness} {V:change} {O:the account} <M: {S':he} {V':had given} ( M': to the police ) > .",
         "pat": "第3文型（SVO）",
         "tag": "否定の副詞句の文頭倒置",
         "notes": [
                   "急所は did。過去の話なのに change が原形なのは、<b>否定の副詞句 At no point … が文頭に出て、主節が疑問文の語順になった</b>から。"
                   "did と change が the witness をはさんで割れているだけで、意味は the witness did not change … である。",
                   "( M: At no point &lt;M': in the long trial&gt; ) でこれ全体が 1 つの副詞のカタマリ。in the long "
                   "trial は「どの時点も…ない」の point を後ろから絞る形容詞のカタマリなので、外へ出さず中に入れ子にする。",
                   "否定を担っているのは At no point であって動詞ではない。change を否定形に書き換えて訳すのではなく、「一度も…しなかった」と副詞句の否定を主節全体に及ぼす。"
                   "not を勝手に補って書き直さないこと。",
                   "記号は並び順どおりに M・助・S・V・O。<b>倒置は語順の話であって文型は変えない</b>ので骨組みは第3文型のまま。Never / Rarely / "
                   "Seldom / Not until が文頭に出たときも、同じように助動詞が主語の前へ出る。",
                   "&lt; M: he had given to the police &gt; は the account にかかる関係代名詞の省略。given の目的語がこの節の中で欠けていることが証拠で、"
                   "完了の had は given と同じマスに入れる。"],
         "ja": "長い裁判の間、その証人は警察に話した供述を一度も変えなかった。",
         "points": [
                    "At no point … を「一度も…しなかった」と訳し、否定を主節全体に及ぼせている",
                    "倒置を戻し、主語が the witness、述語が did change（＝変えた）だと分かる訳になっている",
                    "he had given to the police を the account にかかる関係代名詞の省略として訳している",
                    "in the long trial を「長い裁判の間」と At no point に結びつけて訳せている"]},
        {"id": "E6",
         "syn": "cleft",
         "en": "It is the quality of the questions we ask that ultimately determines the value of the answers we receive.",
         "dsl": "{S:It} {V:is} {C:the quality} <M:of the questions <M': {S'':we} {V'':ask} > > [ 強調: {接:that} {M':ultimately} {V':determines} {O':the value} <M':of the answers <M'': {S'':we} {V'':receive} > > ] .",
         "pat": "第2文型（SVC）",
         "tag": "強調構文 It is … that …",
         "notes": [
                   "急所は It の正体。<b>It is と that を消してみる</b>と The quality … determines the value … という欠けの無い文が残る。"
                   "残れば強調構文の<b>候補</b>で、天候や時刻を表す it ではない。",
                   "形式主語なら消したときに主語が無くなって文が壊れ、that 以下は 真S になる。ここは壊れないので 真S は付けない。判定は必ず「消して残るか」で行う。",
                   "残る可能性は「It が前の文の何かを指す代名詞で、that 以下は the quality にかかる関係詞節」という読み。決め手は<b>It の指す先が前に無い</b>ことである。"
                   "指す先を言えないので強調構文と決まる。",
                   "記号は {S:It} {V:is} {C:…} に [ 強調: … ] を続ける。<b>形の上は第2文型</b>として扱い、that 以下は名詞のカタマリの記号 "
                   "[ ] で囲む。( ) は副詞のカタマリの記号なので強調構文の枠には使わない。",
                   "強調されているのは the quality の 2 語ではなく、of the questions も we ask も抱えた<b>名詞のかたまり全体</b>。"
                   "&lt; we ask &gt; は the quality ではなく the questions にかかるので &lt; &gt; の中へ入れ子にする。"
                   "that の直後がいきなり determines なのが、強調された部分がもと主語だった証拠。"],
         "ja": "最終的に、私たちが得る答えの価値を決めるのは、私たちが投げかける問いの質そのものなのである。",
         "points": [
                    "It is … that … を強調構文と見抜き、「〜こそが」「〜なのである」と訳している（「それは〜だ」と形式的に訳していない）",
                    "強調されているのが the quality of the questions we ask 全体で、それが determines の主語にあたると分かる訳になっている",
                    "we ask を the questions に、we receive を the answers にかけて訳し分けている（関係代名詞の省略を 2 か所とも処理できている）",
                    "ultimately を「最終的に」、determines を「決める」と訳せている"]},
    ]},
    {"g": "③　分詞構文・無生物主語・名詞構文・仮定法", "sub": "動詞でない語に隠れた主語述語を見る", "pool": "3-3", "items": [
        {"id": "F1",
         "syn": "with-absolute",
         "en": "With snow still falling on the narrow mountain road, the rescue team postponed the search until the weather forecast improved.",
         "dsl": "( M: With {S':snow} {M':still} {V':falling} ( M': on the narrow mountain road ) ) , {S:the rescue team} {V:postponed} {O:the search} ( M: {接:until} {S':the weather forecast} {V':improved} ) .",
         "pat": "第3文型（SVO）",
         "tag": "付帯状況の with（with O doing）",
         "notes": [
                   "文頭の With を「〜と一緒に」の前置詞と読むと、直後の falling が宙に浮く。( M: With {S':snow} {M':still} {V':falling} "
                   "… ) のように with の後ろに主語と述語の関係が並んでいるので、この ( ) 全体で「〜という状況で」を表す副詞のカタマリになる。",
                   "{V':falling} は分詞であって主節の V ではない。主節の V は postponed ただ 1 つで、( ) を 2 つとも外すと the rescue "
                   "team postponed the search という骨格だけが残る。",
                   "付帯状況の with は O の後ろに doing のほかに過去分詞・形容詞・前置詞句も取る（with the door open / with his "
                   "eyes closed）。O と後ろの語の間に「O が〜する・される」の関係が読めるかどうかで見分ける。",
                   "{M':still} は falling にかかる副詞なので V のマスに巻き込まない。副詞を動詞と同じマスに入れると、どの語が述語なのかが図の上で見えなくなる。",
                   "文末の ( M: {接:until} {S':the weather forecast} {V':improved} ) は接続詞 until が導く副詞節。"
                   "until の後ろに S と V が続いているので前置詞ではなく接続詞だと決まる。"],
         "ja": "雪がまだ狭い山道に降り続く中、救助隊は天気予報が好転するまで捜索を見合わせた。",
         "points": [
                    "With snow still falling … を付帯状況の with と見て「雪が降り続く中で」と、主節と同時の状況として訳せている",
                    "snow と falling の間に主述関係を読み取り「雪が降っている」と訳せている（with を「〜と一緒に」と訳していない）",
                    "still を falling にかけて「まだ降り続いている」と訳せている（主節の postponed にかけていない）",
                    "until the weather forecast improved を「天気予報が良くなるまで」と、延期の期限を表す副詞節として訳せている"]},
        {"id": "F2",
         "syn": "inanimate-subject",
         "en": "A burst water pipe under the main stage prevented the theater company from opening its new play on time.",
         "dsl": "{S:A burst water pipe} < M: under the main stage > {V:prevented} {O:the theater company} ( M: from {V':opening} {O':its new play} ( M': on time ) ) .",
         "pat": "第3文型（SVO）",
         "tag": "無生物主語（prevent O from doing）",
         "notes": [
                   "S の A burst water pipe は人ではない。「破裂した水道管が劇団を妨げた」と直訳すると日本語が壊れるので、S を原因の副詞に変えて「舞台の下で水道管が破裂したせいで」と読み替える。"
                   "これが無生物主語の処理である。",
                   "prevent A from B は「A が B するのを妨げる」で、from は前置詞だから後ろに来るのは -ing 形（動名詞）である。前置詞のカタマリはどれだけ長くても "
                   "C にはならないので、( M: from … ) と副詞のカタマリで外に出し、中の -ing には {V':opening} と印を付けて目的語まで分解する。"
                   "( ) と &lt; &gt; をすべて外すと S V O だけが残るから、この文は第3文型である。",
                   "同じ「妨げる」の型に keep O from doing / stop O from doing がある。どれも O と doing の間に「O が〜する」という主述の関係があるが、"
                   "間に from がはさまっているので O の後ろを C とは呼ばない。前に from が無く to 不定詞が続く force O to do・enable "
                   "O to do とは図の形が変わる。",
                   "&lt; M: under the main stage &gt; は直前の名詞 pipe にかかる形容詞のカタマリ。V の prevented にかけて「舞台の下で妨げた」と読むと、"
                   "どこで水道管が破裂したのかという中心の情報が消える。",
                   "prevent は英文に not が無くても訳文に否定が出る動詞である。S を「〜のせいで」、O を訳の主語に立て直して「その劇団は…始めることができなかった」と、"
                   "否定を含む形に置き換えると自然な日本語になる。",
                   "( M': on time ) は opening にかかる副詞のカタマリで、( M: from … ) の内側にある。ダッシュが 1 本増えているのは囲みが "
                   "1 つ深くなったというしるしである。"],
         "ja": "舞台の下で水道管が破裂したために、その劇団は新作の上演を予定どおりに始めることができなかった。",
         "points": [
                    "A burst water pipe を無生物主語と見て「水道管が破裂したせいで／破裂したために」と原因の形に訳せている",
                    "prevented … from opening を「…が上演を始めるのを妨げた」＝「…は上演を始められなかった」と、否定を含む形に訳せている",
                    "under the main stage を pipe にかけて「舞台の下の水道管」と訳せている（prevented にかけていない）",
                    "on time を opening にかけて「予定どおりに（上演を）始める」と訳せている"]},
        {"id": "F3",
         "syn": "nominalization",
         "en": "The unexpected arrival of two large tour groups doubled the number of visitors to the small aquarium in a single afternoon.",
         "dsl": "{S:The unexpected arrival} < M: of two large tour groups > {V:doubled} {O:the number} < M: of visitors < M': to the small aquarium > > ( M: in a single afternoon ) .",
         "pat": "第3文型（SVO）",
         "tag": "名詞構文（主格の of）",
         "notes": [
                   "The unexpected arrival of two large tour groups は「大きな団体客が二つ思いがけず到着したこと」と、名詞のカタマリを一度文に開いて読む。"
                   "of の後ろが arrive する側なので、この of は主格の of である。",
                   "主格か目的格かは、名詞を動詞に戻したときに of の名詞が S になるか O になるかで決める。arrive は目的語を取れない動詞なので、ここは主格の "
                   "of 以外に読みようがない。",
                   "名詞構文では形容詞が副詞の働きをする。unexpected は arrival にかかる形容詞だが、文に開くと arrived unexpectedly "
                   "と副詞に変わる。「予想外の到着」と名詞のまま訳すと日本語が硬くなる。",
                   "同じ of でも働きは同じではない。&lt; M: of visitors &gt; は the number の中身を示す of であって、動詞に戻せる名詞構文の "
                   "of ではない。of の前が動作を表す名詞かどうかで見分ける。",
                   "名詞のマス（S や O）に of 句を抱え込まないので、S は The unexpected arrival まで、O は the number までである。"
                   "of 以下はすべて &lt; M: … &gt; として外に出す。",
                   "( M: in a single afternoon ) は doubled にかかる副詞のカタマリ。( ) と &lt; &gt; をすべて外すと S "
                   "V O だけが残るから、この文は第3文型と決まる。"],
         "ja": "大きな団体客が二つ思いがけず到着したことで、その小さな水族館の来館者数はたった一日の午後で2倍になった。",
         "points": [
                    "The unexpected arrival of two large tour groups を「大きな団体客が二つ思いがけず到着したこと」と文に開いて訳せている",
                    "unexpected を副詞のように「思いがけず・予想外に」と訳し、名詞構文をほどけている",
                    "the number of visitors to the small aquarium を「その小さな水族館の来館者数」と、to 句が visitors "
                    "にかかると分かる形で訳せている",
                    "doubled を「2倍にした・2倍になった」と訳し、in a single afternoon を doubled にかけて訳せている"]},
        {"id": "F4",
         "syn": "subjunctive",
         "en": "Without the detailed letters that survived in a private collection, historians would have found the painter's long silence impossible to explain.",
         "dsl": "( M: Without the detailed letters < M': {S'':that} {V'':survived} ( M'': in a private collection ) > ) , {S:historians} {V:would have found} {O:the painter's long silence} {C:impossible to explain} .",
         "pat": "第5文型（SVOC）",
         "tag": "仮定法（Without ＋ would have done）",
         "notes": [
                   "Without を「〜なしで」と副詞のように流すと、主節の would have found の時制が浮いてしまう。Without + 名詞 は If it "
                   "had not been for + 名詞 と同じで、過去の事実に反する仮定を作っている。",
                   "仮定法の目印は if ではなく主節の助動詞のほうにある。would have + 過去分詞を見た時点で「実際には手紙が残っていたので説明がついた」という、"
                   "事実の裏返しを読み取る。Without は But for に置き換えられる。",
                   "found の後ろに the painter's long silence と impossible to explain が並び、両者に「沈黙が説明しがたい」という主述の関係がある。"
                   "だから後ろは O ではなく C で、この文は第5文型になる。",
                   "&lt; M': {S'':that} {V'':survived} … &gt; は the detailed letters にかかる関係詞節で、( "
                   "M: Without … ) の内側にある。ダッシュが 1 本増えているのは、囲みが 1 つ深くなったというしるしである。",
                   "impossible to explain の to explain は explain の目的語が欠けた形で、欠けているのは silence にあたる。"
                   "この形では to be explained とはしない点にも注意する。",
                   "{C:impossible to explain} は to 不定詞を含むが、形容詞 impossible を中心にしたひとかたまりなので、この C は形容詞のかたまりとして平のマスのままにし "
                   "[ C: … ] では囲まない。囲んで中まで分解するのは、原形不定詞や to 不定詞そのものが骨になっている C のほうである。第2部 G2 の {C:too "
                   "anxious about her start} と同じ扱いになる。"],
         "ja": "個人の収集品の中に残っていた詳細な手紙が無かったら、歴史家たちはその画家の長い沈黙を説明のしようがないものと感じていただろう。",
         "points": [
                    "Without … を仮定法の条件と見て「…が無かったら」と、過去の事実に反する仮定として訳せている",
                    "would have found を「…と感じていただろう」と、実際にはそうならなかったことを含めて訳せている",
                    "found O C を第5文型と取り、「その画家の長い沈黙を説明のしようがないものと感じた」と O と C の主述関係を訳せている",
                    "that survived in a private collection を the detailed letters にかかる関係詞節と取り「個人の収集品の中に残っていた詳細な手紙」と訳せている"]},
        {"id": "F5",
         "syn": "correlative",
         "en": "A relaxed evening meal can give busy teenagers not only a short rest but also a rare chance to talk with their parents.",
         "dsl": "{S:A relaxed evening meal} {V:can give} {O1:busy teenagers} [ O2: {接:not only} {O':a short rest} {接:but also} {O':a rare chance} < M': {V'':to talk} ( M'': with their parents ) > ] .",
         "pat": "第4文型（SVOO）",
         "tag": "相関接続詞（not only A but also B）と共通関係",
         "notes": [
                   "not only を見たら but also を探す。A と B は文法上つり合う形で並ぶので、ここは {O':a short rest} と {O':a "
                   "rare chance} という名詞どうしになる。2 つ合わせて 1 つの O2 なので [ O2: … ] と名詞のカタマリで囲む。",
                   "結ばれている 2 項が図の上で同じ {O':} のラベルを持っていることが確認の手がかりになる。ラベルがそろわない読み方をしたなら、A と B のつり合いが取れていないので読み違えている。",
                   "can give の後ろに busy teenagers と [ O2: … ] という名詞が 2 つ並ぶので第4文型である。teenagers と rest "
                   "の間に「teenagers = rest」の関係は無く「teenagers に rest を与える」の関係だから、第5文型ではない。",
                   "共通関係は「くくり出せるか」で見抜く。can give busy teenagers は not only の前に一度だけ置かれ、A と B の両方に掛かっている。"
                   "but also の後ろで改めて S や V を探しに行かないこと。",
                   "&lt; M': to talk with their parents &gt; は直前の a rare chance だけにかかる形容詞のカタマリで、[ "
                   "O2: … ] の内側にある。can give にかけて「親と話すために与える」と読むと chance の中身が空になる。",
                   "not only A but also B は「A だけでなく B も」で、力点は後ろの B にある。also は落ちることがあり、B の後ろに as well "
                   "を置く形（not only A but B as well）も同じ働きをする。"],
         "ja": "ゆったりとした夕食は、忙しい10代の子どもたちに短い休息を与えるだけでなく、親と話す貴重な機会も与えてくれる。",
         "points": [
                    "not only A but also B を「A だけでなく B も」と訳し、A と B が a short rest と a rare chance "
                    "という名詞どうしの並びだと示せている",
                    "can give busy teenagers が not only の前後どちらにも掛かる共通部分だと読み、「忙しい10代の子どもたちに…を与える」と "
                    "1 回だけ訳せている",
                    "第4文型と見て O1（busy teenagers）と O2（not only … but also …）を「…に…を与える」と訳し分けている",
                    "a rare chance to talk with their parents を「親と話す貴重な機会」と、to 不定詞を chance にかけて訳せている"]},
        {"id": "F6",
         "syn": "concessive-as",
         "en": "Tired as the volunteers were after eight hours of sorting donations, none of them left before the last box was labeled.",
         "dsl": "( M: {C':Tired} {接:as} {S':the volunteers} {V':were} ( M': after eight hours < M'': of sorting donations > ) ) , {S:none} < M: of them > {V:left} ( M: {接:before} {S':the last box} {V':was labeled} ) .",
         "pat": "第1文型（SV）",
         "tag": "譲歩の as（形容詞 + as + S + V）",
         "notes": [
                   "文頭の Tired を「疲れて」の分詞構文と読み進めると、直後の as で行き詰まる。形容詞 + as + S + V の語順は譲歩で、Although "
                   "the volunteers were tired とほぼ同じ内容を表す。",
                   "( ) の中で {C':Tired} が節の頭に出ているのが目印である。もともと the volunteers were tired だった補語が as "
                   "の前へ移動した形で、この語順の入れ替わりが譲歩の as を見抜く手がかりになる。",
                   "as には「〜のように」「〜なので」「〜するとき」もある。文頭に冠詞の無い形容詞や名詞が裸で置かれて as が続いたら譲歩と決めてよく、though に置き換えて意味が通るかで確かめられる。",
                   "主節の S は {S:none} で、&lt; M: of them &gt; は名詞のマスから外へ出した of 句である。否定を担っているのは S の側なので「一人も〜しなかった」と訳し、"
                   "V の left を否定形にして訳し直さない。",
                   "( ) を 2 つとも外すと none left だけが残る。この left は「その場を離れた」の意味で目的語を取らないので、この文は第1文型である。"],
         "ja": "ボランティアたちは寄付品を8時間仕分けして疲れていたが、最後の箱にラベルが貼られるまで誰一人その場を離れなかった。",
         "points": [
                    "Tired as the volunteers were を「疲れてはいたけれども」と譲歩で訳せている（「疲れていたので」と理由で訳していない）",
                    "none of them left を「彼らのうち一人もその場を離れなかった」と、S の側にある否定として訳せている",
                    "after eight hours of sorting donations を were にかけて「寄付品を8時間仕分けしたあとで」と訳せている",
                    "before the last box was labeled を「最後の箱にラベルが貼られるまで」と、主節にかかる副詞節として訳せている"]},
    ]},
]
