# -*- coding: utf-8 -*-
"""dojo_eng_kyotsu2026_graph_manual.json の解説本体 (4 セクション)。

キー = (大問番号, 問番号) いずれも 1 始まり。
  core   … ## 🎯 コアイメージ    語法・文法・設問タイプのコアを 2-4 行
  kouzou … ## 🔬 文構造分析      S/V/O/C/M をラベル付きで明示 (絶対省略禁止)
  konkyo … ## 📍 本文の根拠      本文からの**逐語**引用 + どこにあるか
  ng     … ## ❌ 誤答 NG 理由    choices 順 (正答を除く) の理由リスト

★ konkyo の英文引用は passage に一字一句そのまま存在させること。
  validate.py が全数照合する。要約を「」で囲んではいけない。
★ 誤答の見出しは apply_graph.py が choices から機械生成する。ここには理由だけ書く。
★ 図 (Source B) の数値は passage 本文には無い。図から読む数値は
  「図(Source B)より」と明示し、英文の逐語引用としては扱わない。
"""

K = {}


def _d(g, q, core, kouzou, konkyo, ng):
    K[(g, q)] = dict(core=core, kouzou=kouzou, konkyo=konkyo, ng=ng)


# =====================================================================
# 大問1 スマートフォンの持ち込み
# =====================================================================
_d(1, 1,
   core="""- `depend on ~` のコアは「〜に寄りかかっている」。**結果がそれ次第で変わる**という含み。
- `whether A or B` は「AなのかBなのか」という未決の二択を、名詞のかたまりにする形。
- 「主張の核」を問う設問では、その人が**何を条件として置いているか**を探すのが最短。""",
   kouzou="""Mei の結論文:
`[If teachers decide clearly [when phones may and may not be used]], [the same tool [that distracts us]] can actually help us learn.`
  M(条件節)=If teachers decide clearly when phones may and may not be used
  S=the same tool that distracts us / V=can help / O=us / C=learn (原形不定詞)
→ 「**同じ**道具」が条件次第で逆の結果を生む、という構造そのものが
  「whether ... depends on ...」の言い換えになっている。""",
   konkyo="""第3段 Mei。「The problem isn't the device; it's the rules.」でまず対比軸を置き、
続けて「If teachers decide clearly when phones may and may not be used, the same tool that distracts us can actually help us learn.」
と条件を明示する。締めも「Banning them completely just wastes a chance to teach us a skill we genuinely need.」で、
禁止そのものを否定している。""",
   ng=["Mei は理科の授業で辞書アプリとニュース記事を使い「that has made lessons more interesting」と述べている。難しくなるという記述は本文に無く、評価も逆。",
       "Mei が求めるのは「教師が使ってよい時を明確に決める」ことであって、常時自由使用ではない。ルールの必要性を説く主張と正反対。",
       "辞書アプリは例として挙がるだけで、同じ文で news articles も挙げている。「唯一認められる用途」とは述べていない。"])

_d(1, 2,
   core="""- `be willing to V` は「進んで〜する」より「**〜してもかまわない**」という受け入れの姿勢。
- 共通点を問う設問は、**理由が違っても結論が一致していればよい**。動機の一致を探しにいくと外す。
- `would rather V` / `would accept ~ing` はどちらも「その案なら受け入れる」という譲歩の型。""",
   kouzou="""Ken: `[I]'d rather leave [mine] [in a locker] [during lessons].`
  S=I / V=would rather leave / O=mine (= my phone) / M=in a locker, during lessons
Riku: `[I]'d accept [phones being collected each morning and returned at the end of the day].`
  S=I / V=would accept / O=動名詞句 (phones が意味上の主語・being collected と returned が並列)
→ 動詞は違うが、どちらも「日中は手元から離す」案の**受け入れ**を目的語に取っている。""",
   konkyo="""第2段 Ken「I'd rather leave mine in a locker during lessons.」
第4段 Riku「I'd accept phones being collected each morning and returned at the end of the day.」
二人とも授業中・在校中は端末を手元から離すことを容認している。""",
   ng=["Ken は「I'm not against phones themselves」と明言し、Riku も下校時の返却を前提にしている。校内からの完全排除ではない。",
       "Ken は冒頭で「I understand that phones can be handy in an emergency」と利点を認めている。「利点は一切ない」ではない。",
       "Riku は「I worry less about grades and more about how attached we are becoming」と述べ、成績ではなく依存を問題にしている。"])

_d(1, 3,
   core="""- `not A but B` は「AではなくB」。**主張は必ず but の後**にある。
- 「どの意見が資料の推奨と一致するか」型は、まず資料の**結論文だけ**を取り出してから
  各人の主張と突き合わせる。資料全体の話題(依存・集中)に引きずられないこと。""",
   kouzou="""Source A の結論文:
`[Its overall recommendation] is [not a total ban] but [a clear set of rules [about when devices may be used]].`
  S=Its overall recommendation / V=is / C=not a total ban but a clear set of rules
  M=about when devices may be used (前置詞 + 疑問詞節)
→ C が not A but B。取るべきは B =「いつ使ってよいかの明確なルール」。""",
   konkyo="""Source A。「When phones are used under clear teacher guidance—for example, to look up information during a specific task—students often become more engaged.」
で指導下の有効性を示し、末尾で「Its overall recommendation is not a total ban but a clear set of rules about when devices may be used.」と結ぶ。
これは Mei の「教師が使用時を明確に決めれば道具は学習を助ける」と同じ主張。""",
   ng=["Source A は「Problems appear when use is unrestricted」と無制限使用の弊害を述べており、常時利用可という Aoi の立場は推奨と合わない。",
       "Source A の結論は「not a total ban」。常時締め出しを求める Ken の立場は推奨と逆向き。",
       "Source A は対面会話の減少にも触れるが、それは「a separate concern」として添えられた論点で、結論はあくまで使用ルールの整備。"])

_d(1, 4,
   core="""- `rarely A, but B` は「めったにAではなく、むしろB」。**頻度の副詞が否定を担う**型。
- `A rather than B` は「BではなくA」で、**前が主役**。not A but B と前後が逆なので注意。
- 資料の結論を問う設問は、本文が繰り返し置いている**対比軸**を見つければ答えが決まる。""",
   kouzou="""`[Researchers] found [that [the issue] is [rarely the phone itself], but [how and when it is used]].`
  S=Researchers / V=found / O=that 節
  that 節内: S=the issue / V=is / C=rarely the phone itself, but how and when it is used
  (C に疑問詞節 how and when ... が入り、「使い方と時機」が補語になっている)
→ 「端末そのもの」対「使い方と時機」という対比が、そのまま設問の答えの軸。""",
   konkyo="""Source A 冒頭「Researchers found that the issue is rarely the phone itself, but how and when it is used.」
以降も同じ軸で一貫している。指導下では「students often become more engaged」、
無制限使用では「students who keep notifications switched on during lessons take noticeably longer to return to a task after each interruption」。""",
   ng=["本文は「the issue is rarely the phone itself」と明言している。端末が存在すること自体が主因という読みは正反対。",
       "無制限使用の生徒は復帰に「noticeably longer」かかると、測定できる差として書かれている。影響なしとは述べていない。",
       "結論は「not a total ban」。社会性への懸念は述べるが、全端末の撤去は推奨されていない。"])

_d(1, 5,
   core="""- 図と複数の意見を突き合わせる設問は、**指標ごとに「誰の主張を裏づけるか」を 1 対 1** で対応させる。
- 指標が複数あるときに、**最大値ひとつで全体を語らない**のが鉄則。
  「最も高い数字が出た方が優れた政策」は典型的な過度の一般化。
- `while` は対比の接続詞。前半と後半で**別々の指標**を語っていることが多い。""",
   kouzou="""正答の選択肢:
`[Clear-rules schools] supported [Mei's view] [by letting far more students use phones for learning], while [total bans] did better [at increasing face-to-face talk], [matching Riku's concern].`
  主節: S=Clear-rules schools / V=supported / O=Mei's view / M=by ~ing (手段)
  対比節: S=total bans / V=did better / M=at ~ing (どの点で優れたか)
  末尾の matching ~ は分詞構文で「それが誰の懸念と合うか」を添える。
→ **2 つの指標を 2 人に振り分ける**構造。片方の指標だけを見る選択肢は落ちる。""",
   konkyo="""図(Source B)より、「Used phone for learning」は Clear-rules 58% に対し Total-ban 14%。
「More face-to-face talk」は Total-ban 71% に対し Clear-rules 49%。
前者は Mei「If teachers decide clearly when phones may and may not be used, the same tool that distracts us can actually help us learn.」を、
後者は Riku「School should be one place where we step away from our screens and actually practice talking with real people.」を裏づける。""",
   ng=["学習活用は 58% と 14% で 4 倍以上の開きがある。「ほぼ同じ結果」とは言えない。",
       "学習活用は Clear-rules 58% > Total-ban 14%。優劣が逆になっている。",
       "最大値の 71% は Total-ban の対面会話だが、同じ Total-ban は学習活用で 14% と大きく劣る。単一の指標だけで全体を結論づけている。"])


# =====================================================================
# 大問2 部活動の時間
# =====================================================================
_d(2, 1,
   core="""- 意見の要約を問う設問は、「**結論**＋**その理由**」の両方を含む選択肢を選ぶ。
  結論だけ合っていて理由が別人のもの、という誤答がよく混ざる。
- `keep their hours` = 現状維持。`cut / reduce` = 削減。まずどちら側かを確定する。""",
   kouzou="""`[Because practice ends late], [I] have to use [the short gaps in my day] [wisely], and [my grades] have actually gone up [since I joined].`
  M(理由節)=Because practice ends late
  S=I / V=have to use / O=the short gaps in my day / M=wisely
  等position節: S=my grades / V=have gone up / M=since I joined
→ 「練習が長い」→「隙間時間を使う力がついた」→「成績が上がった」という
  因果の鎖。だから時間を削るなという主張につながる。""",
   konkyo="""第1段 Daichi。「At my baseball club, I learned how to manage my time far better than I ever did before.」
で得たものを述べ、「Cutting club time would not give students more useful study hours; it would just take away the very place where I learned discipline.」
で削減を否定する。""",
   ng=["時間短縮と睡眠の確保は Hana の主張。Daichi は「clubs should keep their current hours」と現状維持を求めている。",
       "生徒個人の裁量に委ねるべきというのは Riku の主張。Daichi は全体として現状維持を主張している。",
       "練習の質を時間数より重視するのは Mei の主張。Daichi は時間があることで身についたものを語っている。"])

_d(2, 2,
   core="""- 共通点を問う設問は、**結論の一致**ではなく「**何を問題の中心に置いているか**」で揃うことがある。
- `A rather than B` = 「BではなくA」。何を主犯と見るかを示す型。
- 「〜そのものには反対しない」という譲歩表現は、**争点をずらす合図**。""",
   kouzou="""Mei の中心文:
`[The problem] is [not the clock] but [how tired students are].`
  S=The problem / V=is / C=not the clock but how tired students are
  (not A but B の B に疑問詞節 how tired students are が入る)
Hana の中心文:
`[I] am not against [clubs themselves], but [the hours] have become [too long].`
  → どちらも「クラブの存在」を否定せず、争点を**疲労・時間の質**に移している。""",
   konkyo="""第2段 Hana「I am not against clubs themselves, but the hours have become too long.」
「If schools limited practice to a reasonable level, students could rest properly and still enjoy their activities.」
第4段 Mei「The problem is not the clock but how tired students are.」
二人とも、クラブの存在ではなく生徒の疲労・休息を核心と見ている。""",
   ng=["Hana は「a reasonable level」への制限を望むが法的規制とは述べていない。Mei はむしろ時間で区切る発想そのものを否定している。",
       "生徒本人が決めるべきという主張は Riku のもの。Hana は学校による制限、Mei は練習の質を求めている。",
       "Hana は長時間練習の翌日に「They fall asleep in class the next day.」と学業への影響を述べている。影響がないとは考えていない。"])

_d(2, 3,
   core="""- 「誰の意見が資料に支持されるか」型は、**資料の論点を先に取り出す**。
  ここでは (1) 適度なら有益・過度は有害 (2) 睡眠が時間数より重要かも
  (3) 部員と非部員の単純比較は危うい、の 3 点。
- 資料が扱っていない論点(現状維持・個人裁量)を語る人は、正しくても「支持される」には当たらない。""",
   kouzou="""Source A の結論文:
`[The amount of sleep [students get]], [they conclude], may matter [more than the raw number of hours [spent at practice]].`
  S=The amount of sleep students get / V=may matter / M=more than the raw number of hours spent at practice
  they conclude は挿入節 (主語・動詞を割り込ませる形)
→ 比較の軸が「練習時間」ではなく「睡眠量」に置き換えられている。""",
   konkyo="""Source A。「a reasonable amount of activity supports concentration and motivation, but beyond a certain point, tiredness begins to harm learning」
と山なりの関係を述べ、末尾で「The amount of sleep students get, they conclude, may matter more than the raw number of hours spent at practice.」と結ぶ。
これは Hana の「students could rest properly」と、Mei の「The problem is not the clock but how tired students are.」に直接対応する。""",
   ng=["Daichi は現状維持、Riku は個人裁量で、どちらも Source A が軸に置く疲労・睡眠の議論に触れていない。",
       "Mei は合致するが、Riku の「生徒本人が決めるべき」は Source A が扱っている論点ではない。",
       "Hana は合致するが、Daichi の「時間管理が身についた」は Source A の疲労・睡眠の議論とは別の話。"])

_d(2, 4,
   core="""- `a curve rather than a straight line` = 「**山なり**の関係であって単調増加ではない」。
  曲線と言われたら「途中までは上がる、どこかから下がる」と読む。
- 資料の結論を問う設問では、**両端(ゼロと過剰)がどちらも最良でない**という形の
  選択肢が正解になりやすい。""",
   kouzou="""`[students [who spent moderate time in clubs]] scored [higher on tests] than [students [who did no club activity at all]], while [those [with extremely long practice hours]] scored [lower].`
  S=students who spent moderate time in clubs / V=scored / M=higher on tests than ...
  while 節: S=those with extremely long practice hours / V=scored / M=lower
→ 「適度 > ゼロ」かつ「過剰 < 適度」。この 2 つを同時に満たす読みが山なりの関係。""",
   konkyo="""Source A。「Experts explain this as a curve rather than a straight line: a reasonable amount of activity supports concentration and motivation, but beyond a certain point, tiredness begins to harm learning.」
さらに「The amount of sleep students get, they conclude, may matter more than the raw number of hours spent at practice.」
と、過剰が害になる経路として睡眠を挙げている。""",
   ng=["本文は「a curve rather than a straight line」と明言している。練習時間に比例して得点が上がり続けるという読みは、この一文に真っ向から反する。",
       "適度な活動をした生徒は「students who did no club activity at all」より高得点だと書かれている。活動ゼロが最良という結論は逆。",
       "本文は「comparing club members and non-members directly can be misleading」と警告し、「differ in personality and habits before they ever join a club」と述べている。差の原因を練習時間だけに帰することはできない。"])

_d(2, 5,
   core="""- 2 系列のグラフは、**両方が同じ向きに振れている群**を探すと資料の主張と結びつく。
- 「最高」「最低」は必ず**数値で確かめる**。印象で決めると、単調増加でないグラフを
  単調と読み違える。
- 分詞構文 `supporting ~` は「その事実が何を裏づけるか」を後ろから添える形。""",
   kouzou="""正答の選択肢:
`[The group [practicing 4+ hours]] has [both the lowest test score and the least sleep], [supporting the view [that excessive practice and lost sleep can harm learning]].`
  S=The group practicing 4+ hours (practicing 以下は現在分詞の後置修飾)
  V=has / O=both A and B (2 つの指標を同時に持つことが要点)
  supporting ~ = 分詞構文。that 節は the view の同格。""",
   konkyo="""図(Source B)より、4+ hrs 群は test score 58 で最低、sleep 5.6 時間で最少。
最高得点は 2 hrs 群の 71 で、0 hrs 群は 62。
これは Source A の「beyond a certain point, tiredness begins to harm learning」と、
Mei の「The problem is not the clock but how tired students are.」を同時に裏づける。""",
   ng=["4+ hrs 群は 58 点で、0 hrs 群の 62 点より低い。「どれだけ長くても常に得点を上げる」は図と矛盾する。",
       "2 hrs 群は睡眠 7.1 時間で 1 hr 群の 7.5 時間より少ないのに、得点は 71 > 68 と高い。この群自体が「睡眠が多いほど高得点」の反例になっている。",
       "得点は 62 → 68 → 71 と上がったあと 66 → 58 と下がる。単調増加ではないので、長いほどよいという結論は導けない。"])


# =====================================================================
# 大問3 紙の本と電子書籍
# =====================================================================
_d(3, 1,
   core="""- `it depends on ~` は「〜次第」。二者択一を問われて「どちらとも言えない」と答える型では、
  必ず**何によって決まるか**という判断基準が示される。そこが主張の核。
- `rather than ~ing` = 「〜するのではなく」。捨てた側を示すので、主張は前半にある。""",
   kouzou="""Aoi の冒頭:
`[I] don't think [one is simply better than the other]; [it] depends on [what you are doing].`
  S=I / V=don't think / O=that 節 (接続詞 that が省略)
  セミコロン以降: S=it / V=depends on / O=what you are doing (疑問詞節)
→ 前半で二者択一そのものを否定し、後半で判断基準を置く。この 2 段構えが
  「Neither ... best overall; the right choice depends on the task.」と同じ形。""",
   konkyo="""第3段 Aoi。「I don't think one is simply better than the other; it depends on what you are doing.」
と述べたうえで、「So I use both, choosing the right tool for each task rather than insisting that only one works.」
と締める。用途で使い分けるという立場が一貫している。""",
   ng=["Aoi は「For quick review or looking things up, e-books are excellent」と電子書籍の利点を認めている。always とは言えない。",
       "電子書籍への全面移行を主張するのは Mei。Aoi は「I use both」と併用を明言している。",
       "Aoi は電子書籍を「excellent」と評価して実際に使っている。画面を完全に避けよとは述べていない。"])

_d(3, 2,
   core="""- 共通点は「**違う道筋から同じ結論**」に至っている場合が多い。
  Riku は好みと習慣から、Sota は失敗経験から、同じ結論に着いている。
- `make O C` = 「O を C の状態にする」。`help + O + 原形` = 「O が〜するのを助ける」。""",
   kouzou="""Riku: `For me, [paper] simply makes [deep, focused study] [possible], even if [it] is [heavier to carry around].`
  S=paper / V=makes / O=deep, focused study / C=possible (make O C)
  even if 節=譲歩。「重くても」と不利を認めたうえで結論を守る形。
Sota: `[When I went back to paper for my hardest subjects], [my concentration] returned.`
  M(時の節)=When I went back to paper for my hardest subjects / S=my concentration / V=returned""",
   konkyo="""第1段 Riku「For me, paper simply makes deep, focused study possible, even if it is heavier to carry around.」
「I also write notes in the margins and underline important points by hand, which helps me remember them later.」
第4段 Sota「When I went back to paper for my hardest subjects, my concentration returned.」
画面については「I rarely remembered where information appeared」。集中と記憶の 2 点で一致する。""",
   ng=["二人とも逆の立場で、Sota は「for serious studying that demands memory, paper works better for me」と明言している。",
       "軽さ・携帯性を利点に挙げるのは Mei。Riku はむしろ紙が「heavier to carry around」だと認めたうえで紙を選んでいる。",
       "Sota は媒体を変えて「my test scores actually dropped」と実際の差を報告している。違いは無いとは考えていない。"])

_d(3, 3,
   core="""- 「誰の意見が資料に支持されるか」型は、資料が示す**因果の向き**を確かめる。
  ここでは「画面 → 速く浅い読み・注意散漫 → 記憶が弱い」。
- 選択肢は「誰」＋「because 以下の理由」の 2 つでできている。
  **人が合っていても理由が資料と違えば誤り**なので、後半まで必ず読む。""",
   kouzou="""`[Screens], by contrast, often invite [faster, shallower reading] and carry [the risk of digital distractions [such as messages or links]].`
  S=Screens / V=invite ... and carry ... (等位の 2 動詞) / M=by contrast, often
  O1=faster, shallower reading / O2=the risk of digital distractions such as messages or links
→ 1 つの主語に 2 つの述語がぶら下がり、「浅い読み」と「気の散り」を同時に述べる。""",
   konkyo="""Source A。「One reason may be that the physical layout of a page helps readers build a mental "map" of where information is located, which supports memory.」
で紙が記憶を支える理屈を示し、対比として「Screens, by contrast, often invite faster, shallower reading and carry the risk of digital distractions such as messages or links.」
と述べる。これは Sota の「I kept getting distracted by messages and other apps, and I rarely remembered where information appeared.」に正確に対応する。""",
   ng=["Source A は「they often perform slightly better on paper than on screens」と紙がやや有利と述べており、電子が全面的に優れるとは書いていない。",
       "Source A に余白への手書きについての記述は無い。Riku 自身の習慣であって資料の裏づけではない。",
       "Source A は「the device itself is not the only factor」と述べている。「唯一の要因ではない」であって「差が無い」ではない。"])

_d(3, 4,
   core="""- `not the only factor` は「**他にもある**」であって「関係ない」ではない。
  限定の否定を全否定と読み違えるのが典型的な失点。
- `just as much as ~` = 「〜と同じくらい」。両者を並べて**どちらも重い**と言う型。""",
   kouzou="""`[How carefully a student reads], and [whether they avoid distractions], can matter [just as much as the medium].`
  S=How carefully a student reads / whether they avoid distractions (疑問詞節と whether 節が並列して主語)
  V=can matter / M=just as much as the medium
→ 主語が「読み方」と「気を散らさないか」の 2 つ。媒体と同格に置かれている。""",
   konkyo="""Source A。「However, researchers also note that the device itself is not the only factor.」に続けて
「How carefully a student reads, and whether they avoid distractions, can matter just as much as the medium.」
と述べ、さらに「For tasks like quick searching or skimming, digital texts can even be more efficient.」と補う。""",
   ng=["「the device itself is not the only factor」と正面から矛盾する。媒体だけで決まるとは書かれていない。",
       "「For tasks like quick searching or skimming, digital texts can even be more efficient.」と矛盾する。用途によっては電子が有利。",
       "同じ一文で検索・流し読みでは電子が効率的だと述べており、every task で紙が優るとは言えない。"])

_d(3, 5,
   core="""- グラフと意見を突き合わせる設問では、**課題の種類ごとにどちらが選ばれたか**を並べてから、
  その並び全体と一致する主張を探す。
- 1 つの課題の数値から**別の課題へ結論を広げない**。これが最も多い誤答の型。""",
   kouzou="""正答の選択肢:
`[The survey] shows [students favor paper for tasks [needing concentration and memory], but e-books for searching and portability], [matching the idea [that each format suits different tasks]].`
  S=The survey / V=shows / O=that 節 (接続詞 that が省略)
  O 内は `A for X, but B for Y` の対比。needing ~ は tasks を後置修飾する現在分詞。
  matching ~ = 分詞構文で「その事実が何と噛み合うか」を添える。""",
   konkyo="""図(Source B)より、「Deep reading」は Paper 72%、「Memorizing」は Paper 65% で紙が多数。
「Quick search」は E-book 80%、「Carrying many books」は E-book 85% で電子が多数。
集中・記憶は紙、検索・携帯は電子という並びは、Aoi の「it depends on what you are doing」と、
Source A の「For tasks like quick searching or skimming, digital texts can even be more efficient.」に一致する。""",
   ng=["携帯性の数値から深い読みへ結論を広げている。図では Deep reading は Paper 72% で、むしろ逆の結果。",
       "同じ図で Quick search 80%、Carrying many books 85% が電子を選んでいる。「どの用途でも役に立たない」は成り立たない。",
       "図が示すのは選好の割合であって可否ではない。多くが電子を選んだことから「紙では検索できない」は導けない。"])


# =====================================================================
# 大問4 制服か私服か
# =====================================================================
_d(4, 1,
   core="""- 共通点は「賛成しているもの」だけでなく「**反対しているもの**」でも揃う。
  二人が何を嫌っているかを言い換えて重ねる。
- `be forced into ~` = 「〜へ押し込まれる」。`only one correct way` の **only** が争点。
- `not A but B` = 「AではなくB」。反発の対象が B 側に置かれる。""",
   kouzou="""Ren の中心文:
`[What bothers me about strict uniforms] is [not the clothing itself] but [being told [there is only one correct way to look]].`
  S=What bothers me about strict uniforms (関係代名詞 what 節が主語)
  V=is / C=not the clothing itself but being told ~ (not A but B・B は動名詞の受動)
→ 服そのものではなく「唯一の正解を言い渡されること」に反発している、と明示している。
  これが Daniel の「a uniform takes that freedom away」と同じ争点。""",
   konkyo="""第2段 Daniel「Clothes are one of the few ways students can show who they are, and a uniform takes that freedom away.」
第4段 Ren「What bothers me about strict uniforms is not the clothing itself but being told there is only one correct way to look.」
二人とも、見た目を一つに強制されることへの反発で一致する。""",
   ng=["Daniel は「A piece of clothing will not solve that problem.」といじめ防止効果を否定している。Ren もいじめには触れていない。",
       "Ren は「total freedom could cause problems too」と述べ、「a few approved colors」という規則を提案している。規則の全廃は求めていない。",
       "費用を最も重い理由に挙げるのは Saki。Daniel も Ren も費用には触れていない。"])

_d(4, 2,
   core="""- 「誰が資料と合うか」型は、選択肢の **because 以下まで含めて**正誤を決める。
  人が合っていても理由が資料の記述と違えば誤り。
- `practical` = 「実用的」。資料が利点を **practical** と限定していることが手がかり。""",
   kouzou="""Source A の結論文:
`[The clearest benefit], experts agree, is [practical]: [a shared rule] removes [daily decisions and small status competitions over fashion], but only if [the rule] is applied [fairly] [to everyone].`
  S=The clearest benefit / V=is / C=practical / 挿入=experts agree
  コロン以降が practical の中身: S=a shared rule / V=removes / O=daily decisions and small status competitions
  but only if ~ = 条件つきの限定 (公平に適用される場合に限る)""",
   konkyo="""Source A「The clearest benefit, experts agree, is practical: a shared rule removes daily decisions and small status competitions over fashion, but only if the rule is applied fairly to everyone.」
Mika はまさにこの実用面を理由に挙げており、「With a uniform, I never have to think about what to wear.」
「The point for me is saving time and trouble, not looking the same as everyone else.」と述べている。""",
   ng=["Source A は「uniforms alone cannot stop social problems」「these continue even when clothing is identical」と述べ、不公平が解消されるとは書いていない。",
       "Source A は「Uniforms do not directly improve test scores」と述べるだけで、服装の自由が成績を上げるとは書いていない。",
       "「a few approved colors」は Ren 自身の提案であって、Source A の記述ではない。"])

_d(4, 3,
   core="""- 資料の結論は「**何をしないか**」と「**何をするか**」を両方おさえると決まる。
  ここでは「成績を直接上げるのではない」＋「日々の決定を取り除く」。
- `not by ~ing` は**手段の否定**。何によって効くのかを限定する型。""",
   kouzou="""Source A 冒頭:
`[Uniforms] do not directly improve [test scores]; [what matters] is [the sense of belonging and routine [they can create]].`
  S=Uniforms / V=do not improve / O=test scores / M=directly
  セミコロン以降: S=what matters (関係代名詞 what 節) / V=is
  C=the sense of belonging and routine they can create (they can create は routine を後置修飾)""",
   konkyo="""Source A「Uniforms do not directly improve test scores; what matters is the sense of belonging and routine they can create.」
と「The clearest benefit, experts agree, is practical: a shared rule removes daily decisions and small status competitions over fashion」。
この 2 文を合わせると、効き目は学力そのものではなく日々の選択を減らす点にあると結論できる。""",
   ng=["「Bullying and exclusion are driven by differences in money, popularity, and behavior, and these continue even when clothing is identical.」と正面から矛盾する。",
       "「Uniforms do not directly improve test scores」と矛盾する。always higher とは書かれていない。",
       "制服は服装による自己表現をむしろ減らす側で、Source A も自己表現を利点として挙げていない。"])

_d(4, 4,
   core="""- `more ... than any other + 単数名詞` = 「他のどれよりも〜」で、事実上の最上級。
- 図と意見を結ぶ設問では、まず**その人が挙げた理由がグラフのどの項目か**を特定する。
  ここでは Mika の「時間と手間の節約」＝ Saving time。""",
   kouzou="""正答の選択肢:
`[The reason [Mika emphasizes]] was chosen [by more students] [than any other single reason].`
  S=The reason Mika emphasizes (目的格の関係代名詞が省略され、Mika emphasizes が the reason を修飾)
  V=was chosen (受動態) / M=by more students than any other single reason
→ 「Mika が強調する理由」を主語にまとめてから、最上級相当の比較で受ける形。""",
   konkyo="""Mika が最重視するのは「The point for me is saving time and trouble, not looking the same as everyone else.」。
図(Source B)の「Saving time」は 34% で、Self-expression 29%、Lower cost 25%、Stopping bullying 12% の
いずれよりも多い。つまり Mika の挙げた理由が単独で最多。""",
   ng=["図は「最も重要と考える理由」の割合であって、いじめの原因を示すものではない。最小値から因果を導いている。",
       "Self-expression は 29% で最多ではない (Saving time が 34%)。しかも自己表現は制服に反対する側の理由で、費用を挙げる Saki の主張とは結びつかない。",
       "Lower cost (25%) は制服を支持する理由、Self-expression (29%) は制服に反対する理由で向きが逆。足し合わせて「制服を拒否」とは読めない。"])


# =====================================================================
# 大問5 オンライン授業か対面授業か
# =====================================================================
_d(5, 1,
   core="""- `blended` = 「混ぜた」。二者択一を否定する意見は、必ず「では**何で振り分けるか**」の
  基準を示す。そこが主張の核になる。
- `belong in ~` = 「〜にこそ属する」。そこが本来の居場所だ、という強い言い方。""",
   kouzou="""Aisha の結論文:
`[The real question] is [not online or in-person], but [which subjects and activities suit each style].`
  S=The real question / V=is
  C=not A but B (B に疑問詞節 which subjects and activities suit each style が入る)
→ 二択そのものを退けて、問いを「どれがどちらに向くか」へ立て直している。""",
   konkyo="""第3段 Aisha。「A "blended" approach makes the most sense to me.」と立場を示し、
「Routine lessons, such as watching a science video or practicing grammar, work well online and save travel time. But discussions, science experiments, and group projects belong in the classroom.」
と振り分けを例示したうえで、「The real question is not online or in-person, but which subjects and activities suit each style.」と結ぶ。""",
   ng=["Aisha は「discussions, science experiments, and group projects belong in the classroom」と教室に残すものを明示している。全科目のオンライン化とは逆。",
       "通信環境の格差を理由に慎重を求めるのは Kenji の立場。Aisha は環境格差には触れていない。",
       "対面でしか育たないものを強調するのは Daniel。Aisha は両方を使い分けると述べている。"])

_d(5, 2,
   core="""- 「意見が食い違う点」を問う設問は、**同じ対象について逆の評価**をしている箇所を探す。
  ここでは「インターネット」という同じ対象が、片方では救いの手段、片方では格差の原因。
- `Not every ~` は**部分否定**で「すべてが〜なわけではない」。
- `leave ~ behind` = 「置き去りにする」。""",
   kouzou="""Hana: `[For students in small towns far from good schools], [the internet] is [the only way [to reach skilled teachers]].`
  M=For students in small towns far from good schools / S=the internet / V=is
  C=the only way to reach skilled teachers (to 不定詞が way を修飾)
Kenji: `[Not every family] has [a fast internet connection or a quiet space to study], so [some students] are left behind.`
  S=Not every family (部分否定) / V=has / O=a fast internet connection or a quiet space to study
  so 節: S=some students / V=are left behind (受動態)""",
   konkyo="""第1段 Hana「For students in small towns far from good schools, the internet is the only way to reach skilled teachers.」
第4段 Kenji「Not every family has a fast internet connection or a quiet space to study, so some students are left behind.」
同じインターネットを、届かない生徒に届く手段と見るか、届かない生徒を置き去りにする原因と見るかで割れている。""",
   ng=["録画の見返しは Hana が利点として挙げるだけで、Kenji は触れていない。対立点になっていない。",
       "teamwork と patience を挙げるのは Daniel。Hana と Kenji の対立点ではない。",
       "画面越しでは気づけないと述べるのは Daniel。Hana と Kenji の対立点ではない。"])

_d(5, 3,
   core="""- 資料が「**問いの立て方そのものを変えよ**」と言っている場合、その新しい問いに沿って
  考えている人が正解になる。
- `advise A not to ask X but rather Y` = 「AにXではなくむしろYを問うよう勧める」。
  not A but rather B の骨格を外さないこと。""",
   kouzou="""`[Experts] therefore advise [schools] [not to ask "which format is better?" but rather "which format fits this lesson, this subject, and these particular students?"].`
  S=Experts / V=advise / O=schools
  C=不定詞句 (目的格補語)。中身は not to ask A but rather B の対比。
→ 退けられているのは「どちらが優れるか」という問いそのもの。""",
   konkyo="""Source A「Experts therefore advise schools not to ask "which format is better?" but rather "which format fits this lesson, this subject, and these particular students?"」
「The goal, they argue, should be the right tool for each purpose, not one tool for everything.」
これは Aisha の「The real question is not online or in-person, but which subjects and activities suit each style.」と同じ問いの立て方。""",
   ng=["Source A は「A well-planned online lesson with clear goals, regular feedback, and chances for students to interact can match or even beat a poorly run classroom lesson.」と条件つきで述べるだけで、常に優るとは書いていない。",
       "Source A に「通信環境が公平になるまで待て」という記述は無い。Kenji 自身の主張であって資料の裏づけではない。",
       "Source A は形式の優劣ではなく設計の質と生徒の特性で判断せよと述べており、対面を中心に据えよとは言っていない。"])

_d(5, 4,
   core="""- 資料が**一般論と例外**を両方述べているときは、片方だけの選択肢は必ず落ちる。
  「ただし〜な生徒は別」という但し書きまで含めた選択肢を選ぶ。
- `matters less than ~` = 「〜ほどには重要でない」。`tend to ~` = 「〜しがち」で断定を避ける形。""",
   kouzou="""`[Researchers [who study education]] warn [that [the format of a class] matters [less than how carefully it is designed]].`
  S=Researchers who study education / V=warn / O=that 節
  that 節内: S=the format of a class / V=matters / M=less than how carefully it is designed
  (比較の対象に疑問詞節が入り、「形式」対「設計の丁寧さ」を天秤にかけている)""",
   konkyo="""Source A は「the format of a class matters less than how carefully it is designed」で一般論を置き、
続けて「However, studies also find that younger learners and those who struggle to manage their own time tend to fall behind when left alone in front of a screen. These students benefit most from the structure and personal attention of a classroom.」
と例外を述べる。両方を含む結論だけが本文全体と整合する。""",
   ng=["「the format of a class matters less than how carefully it is designed」と矛盾する。設計を無視して形式だけで優劣は決まらない。",
       "Source A が挙げる条件は「clear goals, regular feedback, and chances for students to interact」。動画とチャットさえあれば常に優るとは書いていない。",
       "「younger learners and those who struggle to manage their own time tend to fall behind when left alone in front of a screen」と正反対。"])

_d(5, 5,
   core="""- 用途別のグラフは「**一人でする作業**」と「**人と関わる作業**」で線を引くと読みやすい。
  その線引き自体が、用途で使い分けよという主張の裏づけになる。
- `which` の非制限用法は、**直前の内容全体**を受けて「そのことが〜」とつなぐ。""",
   kouzou="""正答の選択肢:
`[Students] tended to prefer [online] [for individual tasks like reviewing and saving time], but [in-person] [for social tasks like discussion and friendship], [which supports Aisha's blended approach].`
  S=Students / V=tended to prefer / O=online ... but in-person ...(目的語が対比で 2 つ)
  which ~ = 関係代名詞の非制限用法。前の内容全体を受ける。""",
   konkyo="""図(Source B)より、オンラインを選んだ割合は「Reviewing lessons at own pace」78%、
「Saving travel time」71% と高く、「Group discussion」22%、「Making friends」14% と低い。
一人でする作業と人と関わる作業のあいだに線が引ける。これは Aisha の
「The real question is not online or in-person, but which subjects and activities suit each style.」を裏づける。""",
   ng=["図では「Making friends」でオンラインを選んだのは 14% と 4 項目中最も低い。前提が図と逆になっている。",
       "同じ図で「Reviewing lessons at own pace」78%、「Saving travel time」71% と高い用途がある。ひとつの低い数値から全否定へ飛躍している。",
       "復習の数値だけを根拠に全科目へ広げている。討論 22%、友達づくり 14% という低い用途を無視した過度の一般化。"])


# =====================================================================
# 大問6 地域の観光振興
# =====================================================================
_d(6, 1,
   core="""- 要旨を問う設問は、その人が**繰り返し戻ってくる論点**を探す。
  Mei は「お金 → 商売の復活 → 町が生きる」を一貫して語っている。
- `a living town, not a dying one` の one は town の代用。対比で締める常套句。""",
   kouzou="""`[Tourism] gives [our town] [money [it badly needs]], and [that money] pays for [schools and roads].`
  S=Tourism / V=gives / O1=our town / O2=money it badly needs
  (it badly needs は money を修飾する関係詞節。目的格の関係代名詞が省略されている)
  等位節: S=that money / V=pays for / O=schools and roads
→ 「観光 → 町にお金 → 学校と道路」という一本の流れが、そのまま要旨。""",
   konkyo="""第1段 Mei。「Now small restaurants, guesthouses, and craft shops are busy again, and some young people who moved away have come back to work.」
で商売と雇用の回復を挙げ、「Tourism gives our town money it badly needs, and that money pays for schools and roads.」
と続け、「To me, a town with visitors is a living town, not a dying one.」で締める。""",
   ng=["ルールを先に定めることを条件に据えるのは Sophie の立場。Mei は条件を付けていない。",
       "自然環境を金銭より優先せよと述べるのは Kenji の立場。",
       "住民の日常が苦しくなると訴えるのは Daniel の立場。Mei はむしろ町が生き返ったと述べている。"])

_d(6, 2,
   core="""- 共通点は「**条件つきの容認**」で揃うことがある。まず二人とも全否定していないことを確認し、
  次に「何が満たされれば認めるか」を並べる。
- `only if ~` = 「〜の場合に限り」。条件が満たされないと成り立たないことを示す。""",
   kouzou="""Sophie: `[But if the town sets limits, charges visitors a small fee, and uses that fee to fix problems], [tourism] can be [good for everyone].`
  M(条件節)=if 節。sets / charges / uses の 3 動詞が並列
  S=tourism / V=can be / C=good for everyone
Kenji: `[If we protect nature first], [tourism] can continue [for many years].`
  M(条件節)=If we protect nature first / S=tourism / V=can continue
→ どちらも「if 節 + tourism can ~」という同じ骨格。条件が付く点で一致している。""",
   konkyo="""第3段 Sophie「But if the town sets limits, charges visitors a small fee, and uses that fee to fix problems, tourism can be good for everyone.」
第4段 Kenji「If we protect nature first, tourism can continue for many years.」
二人とも観光を全否定せず、害を抑える条件のもとでのみ認めている。""",
   ng=["二人とも「tourism can be good for everyone」「tourism can continue for many years」と、条件つきなら続けられると述べている。全面禁止は主張していない。",
       "買い物や交通の不便を中心に訴えるのは Daniel。Sophie は管理の仕方、Kenji は自然環境を論点にしている。",
       "Kenji は「Money is useful」と経済的利益を認めている。Sophie も利益と問題が同時に現れると述べており、利益を否定していない。"])

_d(6, 3,
   core="""- 「誰が資料に支持されるか」型は、資料の**因果の結論**をそのまま述べている人を選ぶ。
- 選択肢の because 以下が**資料に実際に書かれているか**を必ず確かめる。
  もっともらしいが資料に無い理由が並ぶのが、この形式の定石。""",
   kouzou="""`[Studies] report [that [when such measures are introduced], [both tourism income and resident satisfaction] can rise [together], because [the benefits] stay [while the worst problems are reduced]].`
  S=Studies / V=report / O=that 節
  that 節内: M(時の節)=when such measures are introduced
            S=both tourism income and resident satisfaction / V=can rise / M=together
  because 節がその理由。while は対比ではなく「〜する一方で」の同時進行。""",
   konkyo="""Source A「The towns that keep both their economy and their residents' goodwill tend to be the ones that manage visitor numbers actively.」
「Studies report that when such measures are introduced, both tourism income and resident satisfaction can rise together, because the benefits stay while the worst problems are reduced.」
これは Sophie の「Whether tourism helps or hurts depends entirely on how the town manages it.」と直接一致する。""",
   ng=["Source A に「住民を常に訪問者より優先せよ」という記述は無い。資料が論じているのは管理の仕方。",
       "Source A は「uncontrolled tourism does raise incomes at first, but ...」と、収入が上がるのは最初だけだと明示している。always keeps rising とは書いていない。",
       "「once a beautiful river or beach is ruined, no amount of money brings it back」は Kenji 自身の言葉であって、Source A の記述ではない。"])

_d(6, 4,
   core="""- `A rather than B` = 「BではなくA」で**前が主役**。
- 資料が「無秩序なら反発 / 管理すれば両立」と、**同じ観光でも結果が割れる**ことを示していれば、
  分岐点は観光そのものではなく管理の仕方だと結論できる。""",
   kouzou="""正答の選択肢:
`[How a town manages tourism], rather than [tourism itself], decides [whether residents end up supporting or opposing it].`
  S=How a town manages tourism (疑問詞節が主語)
  挿入=rather than tourism itself (主語の対比を割り込ませる)
  V=decides / O=whether 節 (支持に回るか反対に回るか)""",
   konkyo="""Source A は「In many towns, uncontrolled tourism does raise incomes at first, but crowding, higher prices, and environmental damage soon push local residents to oppose it.」
で無秩序な場合を述べ、「The towns that keep both their economy and their residents' goodwill tend to be the ones that manage visitor numbers actively.」
で管理した場合を述べる。同じ観光でも管理の有無で結果が分かれている。""",
   ng=["冒頭で「the choice is rarely between welcoming all visitors and refusing them」と、その二択自体を退けている。",
       "「both tourism income and resident satisfaction can rise together」と正面から矛盾する。",
       "「spending that fee on local transport, cleaning, and repairs」と、料金を地域に使うことが挙げられている。訪問者への返金は書かれていない。"])

_d(6, 5,
   core="""- 「利益」と「問題」が**両方とも高い**グラフは、「どちらか一方」ではなく
  「**同時に起きる**」という主張を支える。
- 「最多はどれか」は必ず数値で確かめる。印象で決めると順位を取り違える。""",
   kouzou="""正答の選択肢:
`[Source B] shows [that jobs and crowding were both reported [by large shares of residents]], [supporting Sophie's view [that benefits and problems tend to appear together]].`
  S=Source B / V=shows / O=that 節 (中は受動態 were reported。by ~ が動作主)
  supporting ~ = 分詞構文。末尾の that 節は view の同格。""",
   konkyo="""図(Source B)より「More local jobs」64%、「Worse crowding/traffic」58% と、
利益と問題の両方が高い割合で報告されている。これは Sophie の
「The benefits and the problems usually appear together, so the real question is not "tourism: yes or no?" but "how do we control it well?"」
を最もよく支える。""",
   ng=["最も多く報告されたのは「More local jobs」64% で、混雑は 58%。「他のどの影響より多い」という前提が図と違う。",
       "64% が仕事の増加を報告している。「ほとんど誰も利益を得ていない」は図と矛盾する。",
       "「Better public facilities」は 39% で 4 項目中最も低い。最多という前提が誤りで、公共施設は Kenji の自然環境の論点とも別。"])
