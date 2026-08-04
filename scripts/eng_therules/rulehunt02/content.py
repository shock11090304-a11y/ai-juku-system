# -*- coding: utf-8 -*-
"""英語長文 ルール発見トレーニング No.02「文構造編」(The Rules式・別冊ドリル) の単一ソース。

No.01(流れ・論理を追う6ルール)の続編。1文の構造を一瞬で見抜くための6ターゲット:
 ①比較 ②強調構文 ③倒置 ④関係詞(意味の切れ目) ⑤無生物主語 ⑥同格・挿入
No.01(6)+No.02(6)=英文読解の構文ルール12個で網羅する設計(巻頭に「全12ルール地図」)。

ANNOT が解答キーの single source — 問題編のヒント個数・解答編の表・マーク本文は
すべてここから生成される(check.py が本文との突合と網羅性を機械検査する)。
文番号(s)は各長文の通し番号。t は本文中の**正確な**部分文字列。
ルール整理は関正生『The Rules』のアプローチに着想を得た当塾オリジナル(文言・番号は独自)。
"""

META = {
    "series": "英語長文 ルール発見トレーニング",
    "no": "No.02",
    "edition": "文構造編",
    "subtitle": "The Rules式・別冊ドリル ｜ 1文の「設計図」を見抜く練習",
    "level": "共通テスト〜MARCH・関関同立／難関大の土台",
    "time": "1周目: 時間無制限 ／ 2周目: 各12分",
    "note": "関正生『The Rules』のアプローチに着想を得たトリリオンAI塾オリジナルの整理です。ルール番号・文言は独自。",
}

# ------------------------------------------------------------------
# 6ターゲット(探すもの・目印・付ける印・合言葉) —— 全12ルール中の⑦〜⑫
# ------------------------------------------------------------------
TARGETS = [
    {"key": "cmp", "no": "①", "gno": "⑦", "name": "比較", "color": "#0f766e", "cls": "cmp",
     "what": "2つ(以上)を比べる表現。「AはBより〜」「AはBと同じくらい〜」+ 比較を使った最上級相当",
     "sign": "than ／ as … as ／ the 比較級, the 比較級 ／ no other ／ no more … than。比較対象は省略されることが多い",
     "mark": "二重下線を引き、比べているもの2つを〇で囲んで線で結ぶ",
     "slogan": "比較は「何と何を、どっちが上か」——than と as の相手を必ず探せ。",
     "series": "英文解釈の要 ｜ 差がつく最頻出構文"},
    {"key": "clf", "no": "②", "gno": "⑧", "name": "強調構文", "color": "#be123c", "cls": "clf",
     "what": "文の一部を「まさにそれだ」と押し出す構文。It is A that … ／ 強調の do ／ What … is ~",
     "sign": "決定打は「It is と that を外して元の文に戻せるか」。戻せなければ形式主語(It=that節)",
     "mark": "It〜that / 強調の do を《　》で囲む",
     "slogan": "It と that を外して文が戻れば強調構文。戻らなければ形式主語。",
     "series": "形式主語との見分けが命 ｜ 下線和訳の頻出"},
    {"key": "inv", "no": "③", "gno": "⑨", "name": "倒置", "color": "#6d28d9", "cls": "inv",
     "what": "語順が S+V でなく V+S / 助動詞+S になっている箇所。強調・否定語・仮定法が引き金",
     "sign": "否定の副詞が文頭(Never/Not only/Little/Hardly/Only)→助動詞+S。場所句が文頭→V+S。仮定法 Had S も倒置",
     "mark": "語順を⤸で示し、V と S を線で結び「←正順」とメモ",
     "slogan": "? が無いのに疑問文の形——それは倒置。正順に戻して主語を確保しろ。",
     "series": "「主語はどれ?」を守る守備範囲"},
    {"key": "rel", "no": "④", "gno": "⑩", "name": "関係詞(意味の切れ目)", "color": "#047857", "cls": "rel",
     "what": "名詞のうしろの「説明のカタマリ」を導く語。文の「意味の切れ目」の目印",
     "sign": "非制限用法(, which / , who)、関係代名詞 what(=〜こと/もの)、関係副詞(where/when)、複合関係詞(whatever/whoever)",
     "mark": "切れ目に「/」を入れ、関係詞に〇。カタマリを外して骨格(S+V)を残す",
     "slogan": "関係詞は「意味の切れ目」——先行詞を押さえ、カタマリを外して骨格を残せ。",
     "series": "長い名詞をほどく最重要スキル"},
    {"key": "isu", "no": "⑤", "gno": "⑪", "name": "無生物主語", "color": "#b45309", "cls": "isu",
     "what": "「人」でなく「モノ・こと」が主語になって人に何かをする文。因果・手段・条件が隠れている",
     "sign": "主語がモノ/抽象名詞で、他動詞が人を目的語に取る(allow / let / make / give / tell / lead / force / cost / take など)",
     "mark": "主語を▭で囲み、「→ 〜ので/によって/があれば」と訳を書く",
     "slogan": "モノが主語で人を動かしたら「〜のせいで/によって」——because・by で訳せ。",
     "series": "和訳が一気に自然になる関正生の看板"},
    {"key": "app", "no": "⑥", "gno": "⑫", "name": "同格・挿入", "color": "#475569", "cls": "app",
     "what": "ある名詞を別の言い方で「＝」と言い換えたり、補足を割り込ませたりする形",
     "sign": "名詞 + that(同格・後ろが完全文)、コロン(:)、ダッシュ(—)、カンマ挿入。前の名詞の中身・言い換えを導く",
     "mark": "挿入・言い換えを（ ）でくくり、前の語との間に「＝」を書く",
     "slogan": "コロン・ダッシュ・that は「＝言い換え」——骨格を切らずに中身を差し替えろ。",
     "series": "関係代名詞 that との見分けがカギ"},
]

# ------------------------------------------------------------------
# 全12ルール地図(巻頭) — No.01(流れ)+No.02(構造)
# ------------------------------------------------------------------
RULEMAP = {
    "A": {"title": "No.01「流れ・論理を追う」6ルール", "sub": "段落と段落・文と文をつなぐ目印",
          "rows": [
              ("①", "ディスコースマーカー", "□で囲む", "逆接(However/Yet)の後ろに主張"),
              ("②", "因果構文", "下線＋矢印", "原因 → 結果 の向きを即決する"),
              ("③", "仮定法", "波線", "would を見たら妄想モード=現実は逆"),
              ("④", "受動態", "〔　〕", "「する側」を隠す装置・by の有無"),
              ("⑤", "分詞構文", "〈　〉", "接続詞+S+V の圧縮ファイル"),
              ("⑥", "助動詞 will", "◎", "100%そうなる法則・習性"),
          ]},
    "B": {"title": "No.02「1文の構造を解く」6ルール", "sub": "1文を正確に和訳・解釈する目印",
          "rows": [
              ("⑦", "比較", "二重下線", "何と何を、どっちが上か"),
              ("⑧", "強調構文", "《　》", "It…that を外して戻れば強調"),
              ("⑨", "倒置", "⤸ ←正順", "? が無い疑問文の形"),
              ("⑩", "関係詞(意味の切れ目)", "/ 〇", "先行詞を押さえてカタマリを外す"),
              ("⑪", "無生物主語", "▭ →", "モノが主語→ because/by で訳す"),
              ("⑫", "同格・挿入", "（ ）＝", "コロン・ダッシュ・that は言い換え"),
          ]},
}

# ------------------------------------------------------------------
# 長文2題(原創・構文高密度)
# ------------------------------------------------------------------
PASSAGES = [
    {"key": "p1", "label": "訓練 1", "hint": True,
     "title": "What Fiction Does to the Mind",
     "jtitle": "物語が心にすること",
     "paras": [
        [
         {"n": 1, "en": "A single good story can shape our beliefs more powerfully than a whole page of statistics ever could."},
         {"n": 2, "en": "It is not the numbers that stay with us for years, but the characters — their hopes, their failures, their unforgettable voices."},
         {"n": 3, "en": "Rarely do we cry over a spreadsheet, yet millions have wept for a person who never existed."},
        ],
        [
         {"n": 4, "en": "Fiction works like a flight simulator for the mind, which lets us rehearse fear, grief, and love without any real danger."},
         {"n": 5, "en": "The more deeply we enter a character's world, the more our own sense of other people expands."},
         {"n": 6, "en": "What fiction trains is not memory but empathy — the quiet art of imagining whatever another person feels."},
        ],
        [
         {"n": 7, "en": "Frequent readers of novels tend to score at least as high on empathy tests as people who rarely read, and they enjoy the process far more."},
         {"n": 8, "en": "Not only does fiction widen the circle of people we care about, but it also trains us to notice the moment when a friendly smile turns false."},
         {"n": 9, "en": "A novel hands us a hundred lives to try on, and we quietly keep what each one teaches."},
        ],
        [
         {"n": 10, "en": "Only when we lose ourselves in whatever story we are reading do we truly practice stepping outside our own point of view."},
         {"n": 11, "en": "No other art form supports the belief that we can truly know another person, and none places us so completely inside another mind."},
         {"n": 12, "en": "Fiction does deserve a place beside history and science, for it teaches the one lesson that facts alone cannot: how it feels to be someone else."},
        ],
     ]},
    {"key": "p2", "label": "訓練 2", "hint": False,
     "title": "Why Boredom Is Worth Keeping",
     "jtitle": "退屈を手放さないほうがいい理由",
     "paras": [
        [
         {"n": 1, "en": "Boredom has a worse reputation than almost any other feeling, and yet it may be one of the mind's most useful states."},
         {"n": 2, "en": "It is often said that boredom is a sign of laziness — a comforting myth, but a myth all the same."},
         {"n": 3, "en": "Deep in the restless mind lies a workshop where new ideas are slowly and quietly assembled."},
        ],
        [
         {"n": 4, "en": "Nothing pushes us toward imagination more reliably than an afternoon with absolutely nothing to do."},
         {"n": 5, "en": "A restless child is no more broken than a field left empty between harvests; both are simply gathering strength."},
         {"n": 6, "en": "It is precisely when nothing is happening that the brain switches on its default network, which links memory, planning, and the sense of self."},
        ],
        [
         {"n": 7, "en": "Never has the world offered more ways to escape boredom, and never have our minds had less room to wander."},
         {"n": 8, "en": "The old idea that idle time is wasted time is far more costly than it looks, because the mind needs empty hours to connect what it has already learned."},
         {"n": 9, "en": "Whoever learns to sit with boredom gains a freedom that constant entertainment can never give."},
        ],
        [
         {"n": 10, "en": "Boredom does have a purpose — it quietly signals that the mind is ready for something new."},
         {"n": 11, "en": "The less we fear empty time, the more richly our inner life grows."},
         {"n": 12, "en": "So the next time boredom arrives, do not immediately reach for your phone: the most creative moment of your day may be the empty minute you were about to throw away."},
        ],
     ]},
]

# ------------------------------------------------------------------
# 解答キー(単一ソース) — t は本文の正確な部分文字列
# dual: 他ターゲットとの二刀流は同一 t を両カテゴリに載せる(note で明示)
# ------------------------------------------------------------------
ANNOT = {
 "p1": {
  "cmp": [
    {"s": 1, "t": "more powerfully than a whole page of statistics ever could", "kind": "比較級 + than",
     "pair": "a good story ⇄ a page of statistics", "note": "比べる相手は「統計のページ」。ever could =「どんなに頑張っても」で差を強める。"},
    {"s": 5, "t": "The more deeply we enter a character's world, the more our own sense of other people expands", "kind": "the 比較級, the 比較級",
     "pair": "入り込む深さ ⇄ 共感力の広がり", "note": "「〜すればするほど、それだけ〜」。2つの量が連動する比例の型。"},
    {"s": 7, "t": "at least as high on empathy tests as people who rarely read", "kind": "at least as … as(同等以上)",
     "pair": "小説をよく読む人 ⇄ めったに読まない人", "note": "「めったに読まない人と少なくとも同じくらい高い」。at least as … as で「〜以上」。娯楽なのに引けを取らない、が核。"},
    {"s": 7, "t": "enjoy the process far more", "kind": "比較級(than 省略)",
     "pair": "読者 ⇄ (めったに読まない人)", "note": "far more の後ろに than people who rarely read が省略。比較対象の省略に慣れる。far は比較級を強める。"},
    {"s": 11, "t": "No other art form supports", "kind": "no other …(最上級相当)",
     "pair": "小説 ⇄ 他のすべての芸術", "note": "No other+単数名詞=「他のどんな芸術も…ない」=「小説が最も支える」の言い換え。否定で最上級を作る型。後半 none places … と並列。"},
    {"s": 11, "t": "none places us so completely inside another mind", "kind": "none … so …(最上級相当)",
     "pair": "小説 ⇄ 他のすべての芸術", "note": "none(=no other art form)+so completely(as fiction does 省略)=「他のどんな芸術も、これほど完全には…しない」=最上級相当。so の程度が比較の核。"},
  ],
  "clf": [
    {"s": 2, "t": "It is not the numbers that stay with us for years", "kind": "It is A that(A を強調・否定)",
     "focus": "the numbers(を否定)", "note": "「何年も残るのは数字ではない」。It is と that を外すと The numbers stay with us … に戻る=真性の強調構文。not A but B と連動。"},
    {"s": 6, "t": "What fiction trains is not memory but empathy", "kind": "What … is(擬似分裂文)",
     "focus": "empathy", "note": "「フィクションが鍛えるのは…共感だ」。What 節=主語のカタマリを丸ごと強調して後ろに答えを置く。"},
    {"s": 12, "t": "does deserve", "kind": "強調の do + 原形",
     "focus": "deserve(動詞を強調)", "note": "「確かに値する」。do/does/did+原形で動詞を強める。前文の「捨てるべきでない」に対する念押し。"},
  ],
  "inv": [
    {"s": 3, "t": "Rarely do we cry over a spreadsheet", "trig": "否定の副詞 Rarely が文頭",
     "normal": "We rarely cry over a spreadsheet", "note": "否定・準否定の副詞が文頭に出ると、後ろは疑問文の語順(助動詞 do + S)。"},
    {"s": 8, "t": "Not only does fiction widen the circle of people we care about", "trig": "Not only が文頭",
     "normal": "Fiction not only widens the circle …", "note": "Not only A but also B の A を文頭に出した倒置。does + 原形 widen に分解される。"},
    {"s": 10, "t": "Only when we lose ourselves in whatever story we are reading do we truly practice stepping outside our own point of view", "trig": "Only + 副詞節が文頭",
     "normal": "We truly practice … only when we lose ourselves …", "note": "Only+副詞(節)が文頭→主節が倒置(do we practice)。「〜して初めて」の強調。"},
  ],
  "rel": [
    {"s": 4, "t": ", which lets us rehearse fear, grief, and love", "kind": "非制限用法 , which",
     "ref": "先行詞=a flight simulator（=Fiction）", "note": "カンマ+which で「そしてそれが〜」と補足。先行詞は前の a flight simulator(=Fiction)。which が人を動かす無生物主語でもある(⑤と二刀流)。"},
    {"s": 6, "t": "whatever another person feels", "kind": "複合関係詞 whatever",
     "ref": "=anything that … feels", "note": "「別の人が感じることは何でも」。whatever=先行詞を含む(=any … that)。"},
    {"s": 8, "t": "the moment when a friendly smile turns false", "kind": "関係副詞 when",
     "ref": "先行詞=the moment", "note": "when 以下が the moment を説明。時を表す名詞+when は「〜する(その)時」。"},
    {"s": 9, "t": "what each one teaches", "kind": "関係代名詞 what",
     "ref": "=the thing(s) which …", "note": "what=先行詞を含む関係代名詞。「一つ一つが教えること」。名詞のカタマリを作る。"},
    {"s": 10, "t": "whatever story we are reading", "kind": "複合関係詞 whatever(形容詞用法)",
     "ref": "=any story that we are reading", "note": "whatever+名詞で「どんな〜でも」。story を修飾する複合関係形容詞。"},
  ],
  "isu": [
    {"s": 1, "t": "A single good story can shape our beliefs", "read": "→ 「良い物語が一つあれば、それによって信念が形づくられる」(条件・手段)",
     "note": "主語=story(モノ)。直訳「物語が信念を形づくる」より、物語を条件・手段にして訳すと自然。"},
    {"s": 4, "t": ", which lets us rehearse fear, grief, and love", "read": "→ 「それによって私たちは…を予行演習できる」(手段)",
     "note": "which(=fiction)が let で人(us)を動かす無生物主語。関係詞④との二刀流。let 型は「〜のおかげで…できる」。"},
    {"s": 8, "t": "it also trains us to notice", "read": "→ 「フィクションによって、私たちは…に気づけるようになる」(手段・因果)",
     "note": "it=fiction(モノ)が train で人(us)を動かす典型の無生物主語。s6「What fiction trains」と同じ train が動詞。s8 は倒置③・関係詞④との三刀流。"},
    {"s": 9, "t": "A novel hands us a hundred lives to try on", "read": "→ 「小説を読めば、百の人生を試すことができる」(手段・条件)",
     "note": "主語=A novel(モノ)、hand=手渡す。人(us)を目的語に取る典型の無生物主語。"},
    {"s": 12, "t": "it teaches the one lesson that facts alone cannot", "read": "→ 「フィクションによって、事実だけでは学べないことを学べる」(手段)",
     "note": "it=fiction。teach の主語が人でなくモノ。「〜が人に…を教える」→「〜によって人は…を学ぶ」。"},
  ],
  "app": [
    {"s": 2, "t": "the characters — their hopes, their failures, their unforgettable voices", "kind": "ダッシュ(—)+同格・言い換え",
     "eq": "the characters =(希望・失敗・声)", "note": "ダッシュの後ろは the characters を具体化した言い換え。骨格の外の補足。"},
    {"s": 6, "t": "— the quiet art of imagining whatever another person feels", "kind": "ダッシュ(—)+同格",
     "eq": "empathy =(他人の感情を想像する技術)", "note": "直前の empathy をダッシュで言い換え。「つまり〜という技術」と補足。中に複合関係詞 whatever(④)を含む。"},
    {"s": 11, "t": "the belief that we can truly know another person", "kind": "同格の that(後ろが完全文)",
     "eq": "the belief =(私たちは他者を本当に知りうる、という内容)", "note": "the belief の中身を that 節が説明。that 以下は完全文(欠けが無い)=同格。関係代名詞 that との違い。"},
    {"s": 12, "t": ": how it feels to be someone else", "kind": "コロン(:)+言い換え",
     "eq": "the one lesson =(他人であるとはどんな感じか)", "note": "コロンで「そのただ一つのこと(the one lesson)」の中身を提示。直前の that facts alone cannot は関係代名詞(cannot teach)。"},
  ],
 },
 "p2": {
  "cmp": [
    {"s": 1, "t": "a worse reputation than almost any other feeling", "kind": "比較級 + than + any other(準・最上級相当)",
     "pair": "退屈 ⇄ 他のほぼすべての感情", "note": "「他のほぼどんな感情よりも悪い評判」=「ほぼ最下位・最も評判が悪い部類」。almost があるので厳密な最上級ではなく“ほぼ最悪”。"},
    {"s": 1, "t": "one of the mind's most useful states", "kind": "最上級 most(one of the 最上級)",
     "pair": "この状態 ⇄ 心のすべての状態", "note": "one of the 最上級+複数=「最も…なものの一つ」。前半の否定的評価との対比が主張。"},
    {"s": 4, "t": "more reliably than an afternoon with absolutely nothing to do", "kind": "比較級 more … than(最上級相当)",
     "pair": "何もない午後 ⇄ 他のすべて", "note": "文全体 Nothing … more … than =「何もない午後ほど確実に…はない」=「何もない午後が最も確実に…する」。最上級を否定で作る型。主語 Nothing は無生物主語⑤との二刀流(下段)。"},
    {"s": 5, "t": "no more broken than a field left empty between harvests", "kind": "no more A than B(クジラ構文)",
     "pair": "落ち着きのない子 ⇄ 休閑地", "note": "A is no more … than B =「B が…でないのと同様に A も…でない」。両者を並べて否定する型。"},
    {"s": 7, "t": "more ways to escape boredom", "kind": "比較級(than ever 省略・最上級相当)",
     "pair": "今 ⇄ 過去のどの時代も", "note": "Never has … offered more ways =「かつてないほど多くの手段」=最上級相当。倒置③との二刀流。比較対象 than ever before が省略。"},
    {"s": 7, "t": "less room to wander", "kind": "比較級(than ever 省略・最上級相当)",
     "pair": "今 ⇄ 過去のどの時代も", "note": "never have … had less room =「かつてないほど余地が少ない」。more ways と対の否定的最上級相当。倒置③との二刀流。"},
    {"s": 8, "t": "far more costly than it looks", "kind": "比較級 + than",
     "pair": "実際のコスト ⇄ 見た目", "note": "far は比較級を強める(「ずっと」)。「見た目よりずっと高くつく」。"},
    {"s": 11, "t": "The less we fear empty time, the more richly our inner life grows", "kind": "the 比較級, the 比較級",
     "pair": "恐れの少なさ ⇄ 内面の豊かさ", "note": "「恐れないほど、それだけ豊かになる」。less と more の対で比例を作る。"},
    {"s": 12, "t": "the most creative moment of your day", "kind": "最上級 most",
     "pair": "その瞬間 ⇄ 一日の全瞬間", "note": "the most+形容詞=最上級。「一日で最も創造的な瞬間」。結論での価値の逆転。"},
  ],
  "clf": [
    {"s": 6, "t": "It is precisely when nothing is happening that the brain switches on its default network", "kind": "It is A that(A=副詞節を強調)",
     "focus": "precisely when nothing is happening", "note": "強調されているのは「何も起きていないまさにその時」。It is と that を外すと the brain switches … precisely when … に戻る=真性の強調構文。"},
    {"s": 10, "t": "does have", "kind": "強調の do + 原形",
     "focus": "have(動詞を強調)", "note": "「(退屈には)ちゃんと目的がある」。does+原形 have で「本当に持っている」と念押し。世間の誤解への反論。"},
  ],
  "inv": [
    {"s": 3, "t": "Deep in the restless mind lies", "trig": "場所を表す句が文頭",
     "normal": "A workshop lies deep in the restless mind", "note": "場所・方向の副詞句が文頭に出ると V+S の倒置(lies+a workshop)。主語は動詞 lies の後ろの a workshop。"},
    {"s": 7, "t": "Never has the world offered more ways to escape boredom", "trig": "否定の副詞 Never が文頭",
     "normal": "The world has never offered more ways …", "note": "Never 文頭→助動詞 has+S の倒置。「かつて…したことがない」。"},
    {"s": 7, "t": "never have our minds had less room to wander", "trig": "never が文頭(and の後ろ)",
     "normal": "our minds have never had less room …", "note": "and の後ろでも never が節の頭なら倒置(have+S)。1文に倒置が2連発。"},
  ],
  "rel": [
    {"s": 3, "t": "a workshop where new ideas are slowly and quietly assembled", "kind": "関係副詞 where",
     "ref": "先行詞=a workshop", "note": "場所の名詞+where で「〜する(その)場所」。where 以下が workshop を説明。"},
    {"s": 6, "t": ", which links memory, planning, and the sense of self", "kind": "非制限用法 , which",
     "ref": "先行詞=its default network", "note": "カンマ+which で「そしてそれが〜」。which(=network)が links の主語=無生物主語でもある。"},
    {"s": 8, "t": "what it has already learned", "kind": "関係代名詞 what",
     "ref": "=the things which it has learned", "note": "what=「すでに学んだこと」。connect の目的語になる名詞のカタマリ。"},
    {"s": 9, "t": "Whoever learns to sit with boredom", "kind": "複合関係詞 whoever(名詞節・主語)",
     "ref": "=Anyone who learns …", "note": "Whoever=「〜する人は誰でも」。節全体が gains の主語。先行詞を含む。"},
  ],
  "isu": [
    {"s": 4, "t": "Nothing pushes us toward imagination", "read": "→ 「何もしない午後があってこそ想像力がわく／何もない午後によって私たちは想像力へ駆り立てられる」(手段・条件)",
     "note": "Nothing(=何もない午後)が push で人(us)を動かす無生物主語。比較①(more … than)との二刀流。直訳「何も…押し出さない」より条件・手段で訳す。"},
    {"s": 8, "t": "the mind needs empty hours to connect", "read": "→ 「心には、結びつけるために空の時間が必要だ」",
     "note": "主語=the mind。need の主語を「〜には…が必要」と読み替えると自然。"},
    {"s": 9, "t": "constant entertainment can never give", "read": "→ 「絶え間ない娯楽では、決して得られない」(手段の否定)",
     "note": "主語=entertainment(モノ)、give の主語がモノ。「〜が与えない」→「〜では得られない」。"},
    {"s": 10, "t": "it quietly signals that the mind is ready for something new", "read": "→ 「退屈によって、心の準備ができたと分かる」(合図・手段)",
     "note": "it=boredom。signal の主語がモノ。「退屈が合図する」→「退屈によって…と分かる」。"},
  ],
  "app": [
    {"s": 2, "t": "a sign of laziness — a comforting myth, but a myth all the same", "kind": "ダッシュ(—)+言い換え",
     "eq": "(退屈=怠惰のしるし、という説)=(心地よいが、しょせん俗説)", "note": "ダッシュで直前の主張(俗説)を言い換え・評価。骨格の外の補足。"},
    {"s": 8, "t": "The old idea that idle time is wasted time", "kind": "同格の that(後ろが完全文)",
     "eq": "The old idea =(暇な時間は無駄な時間だ、という内容)", "note": "the idea の中身を that 節が説明。idle time is wasted time は完全文=同格の that。"},
    {"s": 10, "t": "a purpose — it quietly signals that the mind is ready for something new", "kind": "ダッシュ(—)+言い換え",
     "eq": "a purpose =(心の準備ができたと知らせる合図)", "note": "ダッシュで a purpose の中身を具体化。「つまり〜という合図」。"},
    {"s": 12, "t": "your phone: the most creative moment of your day may be the empty minute", "kind": "コロン(:)+言い換え・理由",
     "eq": "(スマホに手を伸ばすな):(その空白こそ最も創造的だから)", "note": "コロンで前文の理由・中身を提示。「なぜなら〜」と続く。"},
  ],
 },
}

# チェッカー用: 候補パターンに一致するが解答キーに入れない箇所(理由必須)。
# ★このうち「ひっかけ」系は解説編のトラップ解説にも使う(TRAPS 参照)。
IGNORE = [
    {"p": "p2", "s": 2, "t": "It is often said that", "why": "It is … that だが that 以下が It の中身(=形式主語)。『退屈は怠惰のしるしだ、とよく言われる』。It と that を外しても元の文が復元できないので強調構文ではない。"},
    {"p": "p2", "s": 12, "t": "do not immediately reach", "why": "do not+動詞は「〜するな」の否定命令の do。強調の do(肯定を強める)でも倒置の do(否定副詞+do+S)でもない。"},
    {"p": "p1", "s": 3, "t": "who never existed", "why": "カンマの無い制限用法 who。先行詞 a person を絞り込むだけで「意味の大きな切れ目」にはならないため、本ドリルの関係詞ターゲット(非制限・what・複合関係詞・関係副詞)には数えない。"},
    {"p": "p1", "s": 7, "t": "people who rarely read", "why": "同上、制限用法 who。先行詞 people を絞るだけで切れ目として弱いのでターゲット外。"},
    {"p": "p2", "s": 4, "t": "nothing to do", "why": "do は一般動詞「する」(nothing to do=することが何もない)。強調の do でも倒置の do でもない。"},
]

# 解説編に載せる「ひっかけ」解説
TRAPS = [
    {"target": "clf", "t": "It is often said that boredom is a sign of laziness (訓練2 ②)",
     "note": "It is … that でも、that 以下が It の中身なら形式主語(=『…と言われる』)。強調構文は It is/was と that を外すと元の文に戻り、A に名詞・副詞句が1つ残る。戻せなければ形式主語。"},
    {"target": "inv", "t": "do not immediately reach for your phone (訓練2 ⑫)",
     "note": "do not+動詞は「〜するな」の否定命令。強調の do(do+原形で肯定を強める)でも、倒置の do(否定副詞+do+S)でもない。do を見たら「否定命令/強調/倒置」を語順で判定する。"},
    {"target": "app", "t": "the idea that idle time is wasted (同格) ／ a freedom that entertainment can give (関係代名詞) (訓練2 ⑧⑨)",
     "note": "同じ「名詞+that」でも、that 以下が完全文なら同格(idea の中身)、不完全(give の目的語が欠ける)なら関係代名詞。完全文か欠けているかで一瞬に見分ける。"},
    {"target": "rel", "t": "a person who never existed (訓練1 ③) ／ people who rarely read (訓練1 ⑦)",
     "note": "カンマの無い who/which/that は制限用法——先行詞を絞り込むだけで意味の大きな切れ目にはならない。切れ目として効くのはカンマ付きの非制限(, which / , who)・関係代名詞 what・複合関係詞。だから本ドリルではそちらを優先して探す。"},
]

# ------------------------------------------------------------------
# ミニ講義(解説編) — 各ターゲットの「見つけ方」総まとめ本体
# ------------------------------------------------------------------
LECTURES = {
 "cmp": ("比較は「①比較級/最上級 ②何と何を比べているか(比較対象)」の2点セットで読む。than・as … as の相手は"
         "省略されることが多く、訓練1⑦ far more は「(読まない人)より」が隠れている。the 比較級, the 比較級(訓練1⑤/訓練2⑪)は"
         "「〜するほど、それだけ〜」、no other・no more … than(訓練2④⑤)は比較を使った最上級・否定の言い回し。"
         "見つけたら「どちらが上か」を必ず一言で口に出すと、誤読が消える。"),
 "clf": ("強調構文は It is/was A that … で「A こそが」と一点を押し出す形。見分けの決定打は"
         "「It is と that を外して元の文に戻せるか」——戻せれば強調構文(訓練1②/訓練2⑥)、"
         "戻せず that 以下が It の中身なら形式主語(訓練2②のニセモノ)。"
         "強調の do/does/did+原形(訓練1⑫/訓練2⑩)は「本当に〜する」と動詞を強め、"
         "What … is ~(訓練1⑥)は主語を丸ごと強調する擬似分裂文。"),
 "inv": ("倒置は「? が無いのに疑問文の語順」。引き金は3つ——(1) 否定・準否定の副詞が文頭"
         "(Never / Not only / Little / Hardly / Only)→助動詞+S(訓練1③⑧⑩/訓練2⑦)、"
         "(2) 場所・方向の句が文頭→V+S(訓練2③ lies a workshop)、(3) 仮定法の Had S。"
         "見つけたら必ず正順(S+V)に戻して主語をつかむ。前に出た要素=筆者が今いちばん見せたい情報。"),
 "rel": ("関係詞は長い名詞の「意味の切れ目」の標識。非制限用法(, which / , who)は「そして/というのも」と情報を追加"
         "(訓練1④/訓練2⑥)、関係代名詞 what は「〜すること/もの」で名詞のカタマリを作り(訓練1⑨/訓練2⑧)、"
         "関係副詞 where/when は場所・時に説明を足し(訓練1⑧/訓練2③)、複合関係詞 whatever/whoever は"
         "「〜するものは何でも/人は誰でも」(訓練1⑥⑩/訓練2⑨)。カタマリを外すと骨格(S+V)が浮かぶ。"),
 "isu": ("無生物主語は「モノ・抽象名詞」が主語になって人を動かす形。allow / let / make / give / tell / lead / force / cost / take "
         "などの動詞が合図。直訳の「モノが〜する」は不自然なので、主語を「〜のせいで/によって/があれば」と副詞的に、"
         "目的語の人を主語にして訳し直す。訓練1①「物語のおかげで信念が形づくられる」、訓練2⑧「心には空の時間が必要だ」、"
         "⑨「娯楽では自由は得られない」——因果・手段・条件が主語に畳み込まれている。"),
 "app": ("同格・挿入は「＝言い換え」の装置。名詞+that(that 以下が完全文=中身の説明。訓練2⑧ the old idea that …)、"
         "コロン(:)とダッシュ(—)は「つまり」と前の語を具体化(訓練1⑥⑫/訓練2②⑩⑫)、カンマ挿入は補足の割り込み。"
         "関係代名詞 that(うしろが不完全)との違いは「that 節が完全文かどうか」。"
         "骨格は切らず、中身だけ差し替えて読むと長文が締まる。"),
}

# ------------------------------------------------------------------
# 全訳(文番号つき)
# ------------------------------------------------------------------
TRANS = {
 "p1": {
  1: "たった一つの良い物語は、統計の数字がびっしり並んだ一ページがどんなに束になっても及ばないほど強く、私たちの信念を形づくることがある。",
  2: "何年も心に残るのは数字ではなく、登場人物たち——その希望、その失敗、その忘れがたい声——なのだ。",
  3: "表計算ソフトを前に涙する人はめったにいない。それでも、実在しない人物の運命に、これまで何百万もの人が涙してきた。",
  4: "フィクションは心のためのフライトシミュレーターのように働き、それによって私たちは、現実には何の危険もないまま、恐れや悲しみや愛を予行演習できる。",
  5: "ある登場人物の世界に深く入り込むほど、私たち自身の「他者を感じ取る力」もそれだけ広がっていく。",
  6: "フィクションが鍛えるのは記憶ではなく共感——他人が感じていることが何であれ、それを想像するという静かな技術——である。",
  7: "小説をよく読む人は、共感力のテストで、めったに本を読まない人と少なくとも同じくらい高い点を取る傾向がある。しかも、その過程をはるかに楽しんでいる。",
  8: "フィクションは、私たちが気にかける人々の輪を広げるだけでなく、親しげな笑顔が偽物に変わるその瞬間に気づく目も鍛えてくれる。",
  9: "一冊の小説は、試しに生きてみるための百の人生を私たちに手渡し、私たちはその一つ一つが教えることを静かに自分のものにしていく。",
  10: "今読んでいる物語が何であれ、その中で我を忘れて初めて、私たちは自分の視点の外に出る練習を本当にすることになる。",
  11: "他のどんな芸術形式も、「私たちは他者を本当に知りうる」という信念をこれほど支えてはくれないし、これほど完全に別の心の中へ私たちを置いてくれるものもない。",
  12: "フィクションは、歴史や科学と並ぶ場所に確かに値する。なぜなら、事実だけでは決して教えられないただ一つのこと——他の誰かであるとはどんな感じかを、教えてくれるからだ。",
 },
 "p2": {
  1: "退屈は、他のほとんどどんな感情よりも評判が悪い。それでいて、心の最も有用な状態の一つかもしれない。",
  2: "退屈は怠惰のしるしだ、とよく言われる——心地よい俗説だが、しょせん俗説にすぎない。",
  3: "落ち着きのない心の奥深くには、新しいアイデアがゆっくり静かに組み立てられる工房がある。",
  4: "何もすることのない午後ほど、確実に私たちを想像力へと押し出すものはない。",
  5: "落ち着きのない子どもが「壊れている」なんてことは、収穫と収穫の間に休ませてある畑が壊れていないのと同じで、まったくない。どちらもただ力を蓄えているだけなのだ。",
  6: "何も起きていないまさにそのときにこそ、脳はデフォルト・モード・ネットワークを起動する——記憶と計画と自己の感覚を結びつける、あの回路を。",
  7: "世界がこれほど多くの「退屈から逃れる手段」を差し出したことはかつてないし、私たちの心がこれほど「さまよう余地」を失ったこともかつてない。",
  8: "「暇な時間は無駄な時間だ」という古い考えは、見た目よりずっと高くつく。というのも、心は、すでに学んだことを結びつけるために、空っぽの時間を必要とするからだ。",
  9: "退屈とともに座っていられる者は誰でも、絶え間ない娯楽では決して得られない自由を手にする。",
  10: "退屈にはちゃんと目的がある——それは、新しい何かを受け入れる準備が心にできた、とそっと知らせる合図なのだ。",
  11: "空っぽの時間を恐れなくなるほど、私たちの内面はそれだけ豊かに育っていく。",
  12: "だから今度退屈が訪れたら、すぐにスマホに手を伸ばしてはいけない。その日で最も創造的な瞬間は、あなたが捨てようとしていた、その空っぽの一分間かもしれないのだから。",
 },
}
