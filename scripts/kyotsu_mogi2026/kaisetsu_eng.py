# -*- coding: utf-8 -*-
"""共通テスト模試 2026 英語 の解説本体 (4 セクション)。

server/main.py の英語系生成プロンプトが定める必須フォーマットに準拠する:

    ## 🎯 コアイメージ      … 語法・文法・時制・前置詞のコアイメージ
    ## 🔬 文構造分析        … S/V/O/C/M をラベル付きで明示 (絶対省略禁止)
    ## 📍 本文の根拠        … 該当箇所の引用 + 段落
    ## ❌ 誤答 NG 理由      … 各誤答が構造的・本質的に NG な理由

キーは (大問ラベル, 小問の 0 始まり index)。値は dict(core, kouzou, konkyo, ng)。
  core   : 箇条書き文字列 (行頭 "- ")
  kouzou : 構造を括り出した英文 + S/V/O/C ラベル行
  konkyo : 本文引用を含む根拠
  ng     : 誤答 3 つの理由 (リスト。選択肢テキストと 1 対 1 で対応させる)

build_eng.py が組み立て時に 4 セクションの存在と、ng が誤答 3 件に対応することを検査する。
"""

K = {}


def E(group, idx, core, kouzou, konkyo, ng):
    K[(group, idx)] = dict(core=core, kouzou=kouzou, konkyo=konkyo, ng=ng)


# =====================================================================
# 第1問A メッセージ読解
# =====================================================================
G = "第1問A メッセージ読解"

E(G, 0,
  core="- `Could you check ~?` =「〜を確認してもらえますか」(依頼のコア。`can` より一段丁寧)\n"
       "- `which one is correct` = 間接疑問。疑問詞のあとが **SV の平叙語順**になる\n"
       "- `before I arrive` = 時を表す副詞節。未来の内容でも **現在形**で書く",
  kouzou="`[Someone told me [(that) the club meets on Thursdays]], but [the school website says [(that) Wednesdays]].`\n"
         "  前半: S=Someone / V=told / O1=me / O2=that 節 (接続詞 that 省略)\n"
         "  後半: S=the school website / V=says / O=that 節\n"
         "`Could you check [which one is correct] [before I arrive]?`\n"
         "  S=you / V=check / O=間接疑問節 which one is correct / M=before 節",
  konkyo="第3段「Someone told me the club meets on Thursdays after school, but the school website says Wednesdays. "
         "**Could you check which one is correct before I arrive?**」\n"
         "依頼は `Could you ~?` の一文だけであり、それ以外の文はすべて状況説明である。",
  ng=["第1段 `my host family will meet me at the airport, so you don't need to come` で明確に否定されている。"
      "`don't need to` =「する必要がない」。",
      "第2段 `I know maybe 200 kanji` は現状報告であって依頼ではない。"
      "依頼文の形 (`Could you ~?`) をとっていない箇所は依頼として数えない。",
      "ホストファミリーは既に決まっていて空港で出迎える側なので、紹介を頼む状況自体が成立しない。"])

E(G, 1,
  core="- `have been ~ing` = 現在完了進行形。「過去のある時点から今まで続いている」がコア\n"
       "- `almost all of it has been reading` = 主語は「学習の中身」、C が reading (= 読むことだった)\n"
       "- `can write ~ slowly` = 能力の `can` + 副詞。「できるが速くはない」を含意",
  kouzou="`[I've been learning Japanese for two years], but [almost all of it has been reading].`\n"
         "  前半: S=I / V=have been learning (現在完了進行) / O=Japanese / M=for two years\n"
         "  後半: S=almost all of it (it = 日本語学習) / V=has been / C=reading\n"
         "`I can write hiragana slowly and I know maybe 200 kanji.`\n"
         "  S=I / V=can write / O=hiragana / M=slowly ・ S=I / V=know / O=maybe 200 kanji",
  konkyo="第2段「I've been learning Japanese for two years, but **almost all of it has been reading**. "
         "I can write hiragana slowly」\n"
         "`but` を挟んで「2 年学んだ」→「その大半は読むことだった」と限定しており、"
         "書く方は `slowly` と但し書きがつく。読む経験 > 書く経験 が読み取れる。",
  ng=["`for two years` と正面から矛盾する。現在完了進行形は「今も続いている」ことを示す。",
      "本文は読む中心・書くのは `slowly` なので、能力の向きが逆になっている。",
      "祖母は第3段で `collects Japanese brushes` (筆を集めている) と紹介されるだけで、"
      "日本語を教えた人物としては登場しない。"])

E(G, 2,
  core="- `because` = 理由を導く従属接続詞。直後に動機そのものが来る\n"
       "- `something I made myself` = 目的格の関係代名詞 which/that の省略 + 再帰代名詞 `myself` (「自分の手で」の強調)\n"
       "- `send 人 物` = 第4文型 (SVOO)。「人に物を送る」",
  kouzou="`I've also signed up for the calligraphy club, [because [my grandmother collects Japanese brushes] "
         "and [I want to send her [something [(which) I made myself]]]].`\n"
         "  主節: S=I / V=have signed up / M=for the calligraphy club\n"
         "  because 節: 等位接続された 2 文\n"
         "    後半 S=I / V=want to send / O1=her / O2=something + 関係詞節 (which 省略)",
  konkyo="第3段「I've also signed up for the calligraphy club, "
         "**because my grandmother collects Japanese brushes and I want to send her something I made myself**」\n"
         "`because` 以下がそのまま入部理由になっている。",
  ng=["ホストマザーは第2段で `cleaning time` の話題にのみ登場し、部活を勧めた記述はない。",
      "他の部活動についての記述が本文になく、`the only` (唯一) を支える根拠が存在しない。",
      "2 年間続けてきたのは第2段の通り日本語の学習であり、書道ではない。期間の係り先の取り違え。"])


# =====================================================================
# 第1問B 告知の読み取り
# =====================================================================
G = "第1問B 告知の読み取り"

E(G, 0,
  core="- `Each time SV` =「〜するたびに」(接続詞のはたらきをする名詞句)\n"
       "- `by 28 August` = 期限の `by`「〜までに (完了)」。継続の `until` とは別物\n"
       "- 命令文の列挙 (`Pick up ~` / `write ~` / `Bring ~`) = 手順の指示",
  kouzou="`Each time [you finish a book], write [the title] and [one comment of 30 words or more] on the card.`\n"
         "  従属節: S=you / V=finish / O=a book\n"
         "  主節 (命令文): V=write / O=the title と one comment (等位接続) / M=on the card\n"
         "`Bring [the completed card] to the counter [by 28 August].`\n"
         "  V=Bring / O=the completed card / M=to the counter, by 28 August",
  konkyo="HOW IT WORKS の 2「**Each time you finish a book, write the title and one comment of 30 words or more "
         "on the card.**」と 3「**Bring the completed card to the counter by 28 August.**」\n"
         "この 2 つが賞を受け取るための手続きのすべてである。",
  ng=["提出方法はカウンターへの持参と指定されている。メールは末尾で質問窓口として案内されるだけ。",
      "RULES に `Books borrowed from the city library may be included` とあり、"
      "学校図書館の本に限る条件は存在しない。",
      "RULES の `Comments may be written in English or Japanese` より英語は任意。"
      "英語は追加クレジットが得られる条件であって必須条件ではない。"])

E(G, 1,
  core="- `up to a maximum of three` =「最大 3 まで」。上限を示す `up to` がこの問題の急所\n"
       "- `each comment written in English` = 過去分詞の後置修飾「英語で書かれた各コメント」\n"
       "- `earns you one extra credit` = 第4文型。「あなたに 1 単位をもたらす」",
  kouzou="`Comments may be written in English or Japanese, but [each comment [written in English]] "
         "earns you [one extra book credit], [up to a maximum of three extra credits].`\n"
         "  S=each comment (+ 過去分詞句 written in English が後置修飾)\n"
         "  V=earns / O1=you / O2=one extra book credit / M=up to a maximum of three extra credits",
  konkyo="RULES 第3項「each comment written in English earns you one extra book credit, "
         "**up to a maximum of three extra credits**」と LEVELS の "
         "「Silver ( 6 books) a bookmark and a free drink ticket」「Gold (10 books)」\n"
         "6 冊 + 追加 3 = 9 クレジット。Gold の 10 に届かず Silver 止まりになる。",
  ng=["Bronze (3 冊) は超えているので bookmark だけでは足りない。到達段階の読み違い。",
      "printed review は Gold (10 冊) の特典。上限 3 を無視して 6+6=12 と数えると"
      "この選択肢に誘導される。`up to a maximum of three` が上限を切っている。",
      "bookmark が段階ごとに複数もらえるという記述は LEVELS のどこにもない。"])

E(G, 2,
  core="- `A do not count, but B do` = 対比の `but` + 代動詞 `do` (= count)。B は算入される\n"
       "- `of more than 100 pages` = 前置詞句による後置修飾「100 ページを超える〜」\n"
       "- `may be included` = 許可の `may` の受動態「含めてよい」",
  kouzou="`[Manga and picture books] do not count, but [graphic novels [of more than 100 pages]] do.`\n"
         "  前半: S=Manga and picture books / V=do not count\n"
         "  後半: S=graphic novels (+ 前置詞句 of more than 100 pages) / V=do (= count の代動詞)\n"
         "`Books [borrowed from the city library] may be included.`\n"
         "  S=Books + 過去分詞句 borrowed from the city library / V=may be included",
  konkyo="RULES 第1項「Manga and picture books do not count, **but graphic novels of more than 100 pages do**」"
         "および第2項「**Books borrowed from the city library may be included**」\n"
         "150 ページのグラフィックノベルは 100 ページ超で条件を満たし、市立図書館の本でも問題ない。",
  ng=["`Manga ~ do not count` で明示的に除外されている。",
      "`picture books do not count` で明示的に除外されている。",
      "HOW IT WORKS 2 の `Each time you finish a book` を満たさない。"
      "読み終えていない本は記録の対象にならない。"])

E(G, 3,
  core="- `instead of ~` =「〜の代わりに」。直前の内容と入れ替わることを示す\n"
       "- `the usual two` = `the usual` + 数詞で「いつもの 2 冊」。名詞 books の省略\n"
       "- `during the summer` = 期間限定を示す前置詞句。通常時との対比が前提",
  kouzou="`You may borrow [five books] [at a time] [during the summer], [instead of the usual two].`\n"
         "  S=You / V=may borrow / O=five books\n"
         "  M=at a time (一度に), during the summer (夏の間), instead of the usual two (通常の 2 冊の代わりに)",
  konkyo="BORROWING DURING THE SUMMER「**You may borrow five books at a time during the summer, "
         "instead of the usual two.**」\n"
         "`instead of the usual two` が「普段は 2 冊」という対比を作り、夏だけ増えることを示す。",
  ng=["`It is closed at weekends` と直接矛盾する。",
      "`closed at weekends and from 11 to 15 August` があるので「毎日開いている」は成立しない。",
      "貸出期間についての記述は本文になく、9 月末という日付はどこにも現れない。"])


# =====================================================================
# 第2問A 比較とレビュー
# =====================================================================
G = "第2問A 比較とレビュー"

E(G, 0,
  core="- 表の 2 項目を **同時に**満たすものを探す (AND 条件) のがこの形式のコア\n"
       "- `with no internet connection` = 付帯状況の `with` + 否定「接続がない状態で」\n"
       "- `allow 人 to do` =「人が〜するのを可能にする」",
  kouzou="`Which app allows [a student [with no internet connection]] [to practise speaking]?`\n"
         "  S=Which app / V=allows / O=a student (+ 前置詞句 with no internet connection が後置修飾) "
         "/ C=to practise speaking (不定詞)\n"
         "  → 求める条件は Works offline = Yes **かつ** Speaking practice = Yes",
  konkyo="比較表の Works offline 行と Speaking practice 行。\n"
         "WordStep = Yes / No、QuizLeaf = No / Yes、MemoRise = **Yes / Yes**。\n"
         "2 条件を同時に満たすのは MemoRise だけである。",
  ng=["WordStep は Works offline = Yes だが Speaking practice = No。発音練習の機能がない。",
      "QuizLeaf は Speaking practice = Yes だが Works offline = No。"
      "Aya も `I cannot open the app on the school bus, because there is no Wi-Fi there` と裏づけている。",
      "MemoRise が両方 Yes なので「該当なし」は成立しない。"])

E(G, 1,
  core="- `though` = 譲歩の副詞。文中・文末に置かれ「〜だけれども」と直前の評価を打ち消す\n"
       "- `had nothing left to study` = `nothing` + 過去分詞 `left` (残された) + 不定詞「勉強するものが残っていなかった」\n"
       "- `never caused a problem` = 否定の `never`。問題は起きなかった",
  kouzou="`[The word list is short], though, so [I finished it in two months] and [had nothing left to study].`\n"
         "  第1文: S=The word list / V=is / C=short / 挿入=though\n"
         "  so 以下: S=I / V=finished / O=it / M=in two months\n"
         "    等位: V=had / O=nothing (+ 過去分詞 left + 不定詞 to study が後置修飾)",
  konkyo="Kenta のレビュー「**The word list is short, though, so I finished it in two months "
         "and had nothing left to study.**」\n"
         "収録語数 3,000 という表の数値とも一致する (3 アプリ中で最少)。",
  ng=["`that never caused a problem` と正面から矛盾する。"
      "電波が切れても支障はなかったと明言している。",
      "表の Monthly cost が Free なので、そもそも支払いが発生しない。",
      "Daily reminder は Yes だが、それを問題として挙げた記述はない。"
      "厳しいと述べられているのは QuizLeaf の発音チェックの方。"])

E(G, 2,
  core="- 事実 = 検証できる記述 / 意見 = 書き手の価値判断。これが区別の唯一の基準\n"
       "- `For me, ~ was worth the cost` = `For me` (私にとっては) + 価値語 `worth`。**典型的な意見マーカー**\n"
       "- 表に載っている項目は原則として事実側",
  kouzou="`[For me], [the result] was [worth the cost].`\n"
         "  M=For me (話し手限定の視点) / S=the result / V=was / C=worth the cost (形容詞句)\n"
         "  → 主語が話し手の評価対象であり、`worth` という価値判断語が C に立つ = 意見",
  konkyo="Aya のレビュー最終文「**For me, the result was worth the cost.**」\n"
         "`For me` が「人によって違いうる」ことを示しており、検証可能な事実ではない。",
  ng=["表 Works offline = No で確認できる**事実**。"
      "Aya の `there is no Wi-Fi there` も同じ事実を裏づける。",
      "表 Speaking practice = Yes で確認できる**事実**。"
      "`QuizLeaf's speaking check is strict` も機能の存在を前提にしている。",
      "表 Progress report = Daily で確認できる**事実**。"])

E(G, 3,
  core="- ここも AND 条件。`costs nothing` (無料) **かつ** `reminds them every day` (毎日通知)\n"
       "- `cost nothing` = 動詞 `cost` + `nothing`「費用がかからない」\n"
       "- `remind 人 to do` =「人に〜するよう思い出させる」",
  kouzou="`A student wants [an app [that costs nothing]] and [reminds them to study every day].`\n"
         "  S=A student / V=wants / O=an app + 関係詞節\n"
         "  関係詞節 that costs nothing / (that) reminds them to study every day … 2 つが and で並列\n"
         "  → 関係詞 that の先行詞は共通で an app。よって両方を満たす 1 つのアプリを探す",
  konkyo="比較表の Monthly cost 行と Daily reminder 行。\n"
         "WordStep = **Free / Yes**、QuizLeaf = 500 yen / Yes、MemoRise = 300 yen / No。\n"
         "Kenta の `If price is the only thing you care about, start here.` も後押しになる。",
  ng=["QuizLeaf は Daily reminder = Yes だが Monthly cost が 500 yen で無料ではない。",
      "MemoRise は 300 yen かかるうえ Daily reminder = No。2 条件とも満たさない。",
      "QuizLeaf も MemoRise も有料なので、どちらでもよいという選択にはならない。"])

E(G, 4,
  core="- `go up by ~` =「〜だけ上がる」。`by` は差・程度を表す前置詞 (増減幅のコア)\n"
       "- `my score on the pronunciation test` = `on` が「〜における得点」の対象を示す\n"
       "- 逆接 `but` の後ろに書き手が本当に言いたい結果が来る",
  kouzou="`[QuizLeaf's speaking check is strict] — it told me my \"th\" sound was wrong about fifty times — "
         "but [my score on the pronunciation test went up by twelve points].`\n"
         "  前半: S=QuizLeaf's speaking check / V=is / C=strict\n"
         "  ダッシュ挿入: S=it / V=told / O1=me / O2=that 節 (that 省略)\n"
         "  but 以下: S=my score on the pronunciation test / V=went up / M=by twelve points",
  konkyo="Aya のレビュー「but **my score on the pronunciation test went up by twelve points**」\n"
         "`but` の後ろが結果であり、これが設問の問う「何が起きたか」にあたる。",
  ng=["バスでアプリが開けないと述べているだけで、"
      "バス通学をやめたとは書かれていない。因果の飛躍。",
      "表の Works offline = No。QuizLeaf ではオフライン学習はできない。",
      "12,000 は表にある収録語数であって、Aya が覚えた語数ではない。数値の係り先の取り違え。"])


# =====================================================================
# 第2問B 記事(事実と意見)
# =====================================================================
G = "第2問B 記事(事実と意見)"

E(G, 0,
  core="- `Of those, 74% said ~` = `those` が直前の「回答した 478 人」を受ける。**母数は回答者**\n"
       "- `three-quarters` = 4 分の 3 (= 75%)。74% の言い換え\n"
       "- `feel sleepy` = 感覚動詞 feel + 形容詞",
  kouzou="`[Of those], [61% said [(that) they usually sleep fewer than six hours on school nights]], "
         "and [74% said [(that) they feel sleepy during first period]].`\n"
         "  M=Of those (回答した 478 人のうち)\n"
         "  S=74% / V=said / O=that 節 (S=they / V=feel / C=sleepy / M=during first period)",
  konkyo="第1段「our committee asked all 612 students at this school ~, and 478 students answered. "
         "Of those, 61% ~, and **74% said that they feel sleepy during first period**」\n"
         "74% ≒ 4 分の 3 で、母数は「回答した生徒」である。",
  ng=["`our committee asked all 612 students ~ and 478 students answered` より、"
      "回答したのは 478 人。全員ではない。`asked` と `answered` の主語の違いが急所。",
      "8:45 は第3段で紹介される**他県の高校の事例**の時刻であり、"
      "この学校の生徒の希望として調査された事実はない。",
      "西側から通う生徒については `have to leave home before 7:00` とあるだけで、"
      "遅刻が最も多いという記述はない。"])

E(G, 1,
  core="- 事実 = 数値・出来事など検証できるもの / 意見 = `We think` `believes` を伴う主張\n"
       "- `fifteen minutes earlier than ~` = 比較級 + 差の表現。数値で確認できる = 事実\n"
       "- 意見マーカー: `We think` / `Our committee believes` / `matters more than`",
  kouzou="`[Our school day] begins [at 8:20], [which is fifteen minutes earlier "
         "than [the average starting time for public high schools in this city]].`\n"
         "  S=Our school day / V=begins / M=at 8:20\n"
         "  which 節 = 非制限用法の関係代名詞 (先行詞は at 8:20 という内容)\n"
         "    S=which / V=is / C=fifteen minutes earlier than ~ (比較級 + 差 fifteen minutes)",
  konkyo="第2段「**Our school day begins at 8:20, which is fifteen minutes earlier than "
         "the average starting time for public high schools in this city.**」\n"
         "時刻の比較という検証可能な記述であり、意見マーカーを伴わない。",
  ng=["第3段冒頭 `**We think** that a later start would help.` の内容そのもので、意見。",
      "最終段 `Our committee **believes** that shorter but better-organised practice "
      "would be no less effective` の内容で、意見。",
      "同じく最終段の `Our committee believes ~ that arriving at school awake "
      "**matters more than** half an hour on the field` の内容で、価値判断。"])

E(G, 2,
  core="- `no less effective` = `no + 比較級`「決して劣らない = 同じくらい効果的」。強い主張のコア\n"
       "- `believes that ~` = 意見であることを明示する動詞\n"
       "- `shorter but better-organised` = 譲歩を含む形容詞の並列",
  kouzou="`[Our committee] believes [that [shorter but better-organised practice] "
         "would be [no less effective]].`\n"
         "  S=Our committee / V=believes / O=that 節\n"
         "  that 節: S=shorter but better-organised practice / V=would be / C=no less effective\n"
         "  → 主節の V が believes である時点で、that 節の中身は検証済みの事実ではなく主張",
  konkyo="最終段「**Our committee believes that shorter but better-organised practice "
         "would be no less effective**」\n"
         "根拠となるデータは示されておらず、委員会の判断として述べられている。",
  ng=["第1段の調査結果の数値そのもので、検証可能な**事実**。",
      "第3段で紹介される他県の研究結果の数値で、**事実**として提示されている。",
      "第2段 `Students who travel by train from the west side of the city have to leave home "
      "before 7:00` は通学の実態を述べた**事実**。時刻という検証できる情報しか含まない。"])

E(G, 3,
  core="- `though` = 譲歩の接続詞。直前の肯定的な内容に留保をつける\n"
       "- `too small to be certain about` = `too ~ to do`「〜すぎて…できない」。**断定できない**が結論\n"
       "- `rose slightly` = 上がったが `slightly` (わずかに) と限定",
  kouzou="`The same report noted [that [average test scores in the first-period subject] rose slightly], "
         "[though [the researchers themselves said [that [the change] was [too small to be certain about]]]].`\n"
         "  主節: S=The same report / V=noted / O=that 節 (S=average test scores / V=rose / M=slightly)\n"
         "  though 節: S=the researchers themselves / V=said / O=that 節\n"
         "    that 節: S=the change / V=was / C=too small to be certain about",
  konkyo="第3段「average test scores in the first-period subject rose slightly, "
         "**though the researchers themselves said that the change was too small to be certain about**」\n"
         "`too ~ to ...` が「確信できるほどではない」という否定的結論を作っている。",
  ng=["`rose` (上がった) と書かれており、下がったのではない。動詞の意味の取り違え。",
      "調査期間は `over one term` (1 学期間) と明記されている。3 年間ではない。",
      "`the number of students arriving late fell by 40%` と明記されている。"
      "変化がなかったという記述と正反対。"])

E(G, 4,
  core="- `will present` = 未来の予定。設問「次に何をするか」に直結する\n"
       "- `present A to B` =「A を B に提示する」\n"
       "- `in October` = 予定の時期。この時期に何をするのかを取り違えない",
  kouzou="`We will present [these results] [to the school council] [in October].`\n"
         "  S=We (= the Student Life Committee) / V=will present / O=these results\n"
         "  M=to the school council (提示先), in October (時期)",
  konkyo="最終行「**We will present these results to the school council in October.**」\n"
         "記事全体の締めくくりであり、次の行動を述べた唯一の文である。",
  ng=["部活動の時間短縮は始業を遅らせた場合に生じる帰結として触れられているだけで、"
      "教員に依頼するとは述べていない。",
      "10 月に行うのは**報告**であって、始業時刻の変更ではない。"
      "変更は評議会に諮る段階にすら至っていない。",
      "2 回目の調査についての記述は本文にない。"])


# =====================================================================
# 第3問B 体験ブログ(時系列)
# =====================================================================
G = "第3問B 体験ブログ(時系列)"

E(G, 0,
  core="- `almost gave it straight back` = `almost` +過去形「危うく〜するところだった (実際にはしなかった)」\n"
       "- `Write the essay first, then decide.` = 命令文。先生の助言が行動の順序を決めている\n"
       "- `So I wrote it` の `So` が助言→実行の因果をつなぐ",
  kouzou="`[When my teacher handed me the application form in April], I almost gave it straight back.`\n"
         "  従属節: S=my teacher / V=handed / O1=me / O2=the application form / M=in April\n"
         "  主節: S=I / V=almost gave back / O=it → `almost` により**実際には返していない**\n"
         "`My teacher only said, \"Write the essay first, then decide.\" So I wrote it.`\n"
         "  S=I / V=wrote / O=it (= the essay)",
  konkyo="第1段「When my teacher handed me the application form in April, I almost gave it straight back. "
         "~ My teacher only said, \"Write the essay first, then decide.\" **So I wrote it**」\n"
         "用紙を受け取った直後の行動はエッセイを書くことである。",
  ng=["単語リストを作ったのは第2段の `I spent May and June` の時期で、"
      "合格の知らせを受けた**後**。時系列が逆。",
      "`almost gave it straight back` は「危うく返しかけた」であって、"
      "実際には返していない。`almost` の処理が急所。",
      "メールは `an email told me that I had been chosen` と、"
      "受け取った側として登場する。送ってはいない。"])

E(G, 1,
  core="- ブログは日付順 (Day 1〜Day 5) に並ぶので、**どの日の出来事か**を特定すれば順序が決まる\n"
       "- `In the end we did both` = 議論の決着を示す。その直後が Sora の行動\n"
       "- `I was the one who suggested it` = 強調構文的な `the one who`「〜したのは私だった」",
  kouzou="`In the end [we did both], and [I was [the one [who suggested it]]] — my first complete idea in English.`\n"
         "  前半: S=we / V=did / O=both\n"
         "  後半: S=I / V=was / C=the one + 関係詞節 who suggested it\n"
         "  同格のダッシュ: my first complete idea in English が it を言い換える",
  konkyo="Day 4「In the end we did both, and **I was the one who suggested it** — "
         "my first complete idea in English.」\n"
         "選択肢の出来事は Day 4 / Day 2 / Day 3 / 4〜5月 に対応し、最も遅いのが Day 4。",
  ng=["Day 2 の `By lunchtime we had thrown out our first idea completely` で、Day 4 より前。",
      "Day 3 の `This was the day I stopped translating` で、Day 4 より前。",
      "第1段の `three weeks later an email told me that I had been chosen` で、"
      "キャンプ開始前 (4〜5月)。最も早い出来事。"])

E(G, 2,
  core="- `nobody talked like a textbook` = 否定の主語 `nobody` +様態の `like`「教科書のようには話さなかった」\n"
       "- `the least useful thing` = 最上級の否定的用法「最も役に立たなかったもの」\n"
       "- `because` が理由を直接示す",
  kouzou="`Looking back, [that list] was [the least useful thing [I did]], "
         "[because [nobody at the camp talked like a textbook]].`\n"
         "  分詞構文: Looking back (振り返ると)\n"
         "  主節: S=that list / V=was / C=the least useful thing + 関係詞節 (that 省略) I did\n"
         "  because 節: S=nobody at the camp / V=talked / M=like a textbook",
  konkyo="第2段「Looking back, that list was the least useful thing I did, "
         "**because nobody at the camp talked like a textbook**」\n"
         "理由は `because` 以下に明示されている。",
  ng=["最終段に `the two-hundred-word list still in my bag` とあり、紛失していない。",
      "第1段に `The camp was to be held entirely in English` とあり、英語で行われた。",
      "他の参加者がその単語を知っていたかどうかは本文で一切触れられていない。"])

E(G, 3,
  core="- `changed its mind` =「考えを変えた」。`mind` は単数で「意向」\n"
       "- `more often than any other team` = 比較級 + `any other` で事実上の最上級\n"
       "- `he meant this as a compliment` = 一見否定的な内容を**褒め言葉**として述べたと明示",
  kouzou="`the judge [who spoke to us afterwards] said [that [our team had changed its mind "
         "more often than any other team]], and [that he meant this as a compliment].`\n"
         "  S=the judge + 関係詞節 who spoke to us afterwards / V=said / O=that 節 × 2 (and で並列)\n"
         "  第1の that 節: S=our team / V=had changed (過去完了) / O=its mind "
         "/ M=more often than any other team",
  konkyo="Day 5「the judge who spoke to us afterwards said that **our team had changed its mind "
         "more often than any other team, and that he meant this as a compliment**」",
  ng=["`a team from Thailand did, with a much simpler idea` とあり、"
      "最も簡単な案で勝ったのは別のチーム。",
      "Day 4 に `We built a model, and it failed twice` とある。一度で成功していない。",
      "英語の流暢さについて審査員が言及した記述はない。"
      "Sora 自身も `My grammar was poor` と述べている。"])

E(G, 4,
  core="- `what it feels like to ~` =「〜するのがどんな感じか」。体験知を表す定型\n"
       "- `be understood` = 受動態「理解される」\n"
       "- `who is not simply being polite` = 進行形の `being polite`「その場だけ礼儀正しくふるまう」の否定",
  kouzou="`I now know [what it feels like [to be understood by [someone [who is not simply being polite]]]].`\n"
         "  S=I / M=now / V=know / O=what 節\n"
         "  what 節: it = 形式主語、真主語 = to be understood ~ (不定詞句)\n"
         "  関係詞節 who is not simply being polite が someone を修飾",
  konkyo="最終段「What I actually brought back is smaller and harder to explain: "
         "**I now know what it feels like to be understood by someone who is not simply being polite.**」\n"
         "コロンの後がブログ全体の結論にあたる。",
  ng=["単語リストは `mostly unused` (ほとんど使わなかった) と述べられている。"
      "得たものとして正面から否定されている。",
      "`We did not win; a team from Thailand did` とあり、賞は取っていない。",
      "大学進学や専攻についての記述は本文にない。"])


# =====================================================================
# 第4問 複数資料の統合
# =====================================================================
G = "第4問 複数資料の統合"

E(G, 0,
  core="- 表は**どの列を見るか**で答えが変わる。設問の `time` は Average time 列\n"
       "- `the least time` = 最上級。最小値を選ぶ\n"
       "- 人数 (Students 列) と所要時間 (Average time 列) を取り違えないのがこの形式の急所",
  kouzou="`Which group spends [the least time] [travelling to school]?`\n"
         "  S=Which group / V=spends / O=the least time / M=travelling to school (分詞句)\n"
         "  → `spend + 時間 + doing`「〜するのに時間を費やす」の型",
  konkyo="REPORT A の表 Average time 列: Train 42 min / Bicycle 24 min / Bus 35 min / **Walking 18 min**。\n"
         "最小は Walking の 18 分。",
  ng=["Bicycle は 24 min で Walking より長い。",
      "Bus は 35 min。Walking の約 2 倍。",
      "Train は 42 min で 4 群の中で最長。最小と最大の取り違え。"])

E(G, 1,
  core="- `public transport` = 公共交通機関。ここでは Train と Bus の 2 つを指す\n"
       "- 表の複数行を**足す**タイプの設問。どの行が該当するかの判断が本体\n"
       "- 自転車・徒歩は公共交通機関に含まれない",
  kouzou="`How many students [surveyed] use [public transport]?`\n"
         "  S=How many students + 過去分詞 surveyed が後置修飾 (調査対象の生徒)\n"
         "  V=use / O=public transport\n"
         "  → 該当する行 = Train (468) + Bus (204)",
  konkyo="REPORT A の表 Students 列: Train **468** / Bicycle 372 / Bus **204** / Walking 156。\n"
         "468 + 204 = 672。",
  ng=["468 は Train のみの人数。Bus を足し忘れている。",
      "528 は Bicycle 372 + Walking 156 で、公共交通機関**ではない**方の合計。",
      "1,200 は調査対象全体の人数。4 群すべての合計であり、公共交通機関に限らない。"])

E(G, 2,
  core="- `however` = 転換の副詞。**直前の結論に別の説明を持ち込む**合図\n"
       "- `differ in ~` =「〜の点で異なる」\n"
       "- `almost all of ~ live within 1.5 km` = 距離という交絡要因の提示",
  kouzou="`[The groups] differ [in one other way], however: "
         "[almost all of [the students [who walk]]] live [within 1.5 km of their school].`\n"
         "  第1文: S=The groups / V=differ / M=in one other way / 挿入=however\n"
         "  コロン以下: S=almost all of the students + 関係詞節 who walk / V=live "
         "/ M=within 1.5 km of their school",
  konkyo="REPORT A 末尾「Students who cycle or walk gave clearly higher ratings ~. "
         "**The groups differ in one other way, however: almost all of the students who walk "
         "live within 1.5 km of their school.**」\n"
         "`however` 以下が、高評価を距離という別要因で説明しうると示唆している。",
  ng=["自転車との比較で「あらゆる場合に」と言い切る根拠は本文にない。"
      "`in every case` は本文より強すぎる一般化。",
      "Walking は 156 人で 4 群中**最少**。標本が大きいという記述と逆。",
      "調査は `In June we surveyed` と一括で行われている。別の月ではない。"])

E(G, 3,
  core="- `not A but B` = 「A ではなく B」。**A を明確に否定する**構文\n"
       "- `the most common answer` = 最も多かった回答 = 主たる理由\n"
       "- `crowding` = 混雑。動名詞から派生した名詞",
  kouzou="`[The most common answer] was [not [the length of the journey] but [the crowding]]: "
         "[71% said [(that) they could not sit down]], and [55% said [(that) they could not read or study on board]].`\n"
         "  S=The most common answer / V=was / C=not A but B\n"
         "    A=the length of the journey (否定される) / B=the crowding (これが答え)\n"
         "  コロン以下が B の具体的な内訳",
  konkyo="REPORT B「the most common answer was **not the length of the journey but the crowding**: "
         "71% of train users said that they could not sit down」",
  ng=["`not the length of the journey` で**明示的に否定**されている。"
      "not A but B の A にあたる。",
      "遅延についての記述は本文に一切ない。",
      "運賃についての記述も本文に一切ない。"])

E(G, 4,
  core="- 「両方の資料が支持する結論」= どちらにも反例がない選択肢を選ぶ\n"
       "- `not always` = 部分否定「必ずしも〜ではない」。**1 つでも反例があれば成り立つ**\n"
       "- `always` を含む選択肢は反例 1 つで崩れる (全称命題)",
  kouzou="`[A shorter journey] is [not always] rated [as a better one].`\n"
         "  S=A shorter journey / V=is rated (受動態) / C=as a better one / M=not always (部分否定)\n"
         "  → 「短い方が高評価」が**常には**成り立たないことを 1 例でも示せばよい",
  konkyo="REPORT A: Train 42 min = 2.9 に対し Bus 35 min = 2.6。**より短いバスの方が低評価**で、"
         "所要時間と満足度が単純に対応していない。\n"
         "REPORT B:「the most common answer was **not the length of the journey but the crowding**」と、"
         "所要時間が主因であることを正面から否定している。"
         "さらに「Students who had to change trains once rated their journey higher (2.6) "
         "than students who took a single direct train (2.1).」も同じ向きの例。\n"
         "2 つの資料のどちらにも反例があるので、部分否定 `not always` が支持される。",
  ng=["`always` を含む全称命題。REPORT A の Train (42 min・2.9) > Bus (35 min・2.6) が反例になる。",
      "REPORT A で Bicycle 3.8 は Train 2.9・Bus 2.6 より高い。逆の記述。",
      "REPORT B は自校の train 評価 2.2 が市の 2.9 より `much lower` と明記しており、"
      "同一の結果ではない。"])


# =====================================================================
# 第5問 伝記とノート作成
# =====================================================================
G = "第5問 伝記とノート作成"

E(G, 0,
  core="- `work that demanded ~` = 関係代名詞 that が work を修飾。**仕事の中身**を説明\n"
       "- `a steady hand` =「ぶれない手」= 精密さのコア\n"
       "- `at sixteen` = `at + 年齢`「16 歳のときに」",
  kouzou="`At sixteen she took [a job [painting numbers onto clock faces in her father's workshop]] "
         "— [work [that demanded [a steady hand] and [a very fine brush]]].`\n"
         "  S=she / V=took / O=a job + 現在分詞句 painting ~ が後置修飾\n"
         "  ダッシュ以下は同格: work + 関係詞節 that demanded A and B",
  konkyo="第1段「at sixteen she took a job painting numbers onto clock faces in her father's workshop "
         "— **work that demanded a steady hand and a very fine brush**」",
  ng=["時計を修理していたのは父親 (`Her father repaired clocks`)。主語の取り違え。",
      "教える仕事を始めるのは 1934 年の辞職**後**。時期が異なる。",
      "撮影は当時の研究室の手法として言及されるだけで、彼女の仕事ではない。"])

E(G, 1,
  core="- `do what a camera could not` = 関係代名詞 what「カメラにできないこと」\n"
       "- `decide which parts mattered` = 間接疑問 + `matter` (自動詞「重要である」)\n"
       "- `flattened everything into grey` = 写真の欠点を示す比喩",
  kouzou="`[A trained illustrator] could do [what a camera could not] "
         "— [decide [which parts mattered]] and [show them clearly].`\n"
         "  S=A trained illustrator / V=could do / O=what 節\n"
         "  ダッシュ以下は what の内容の言い換え (原形不定詞 2 つが and で並列)\n"
         "    decide + 間接疑問 which parts mattered / show + O=them + M=clearly",
  konkyo="第3段「a photograph flattened everything into grey, and important details disappeared. "
         "**A trained illustrator could do what a camera could not — decide which parts mattered "
         "and show them clearly.**」",
  ng=["費用についての比較は本文にない。",
      "`Photography of microscopic samples was still poor at that time` は"
      "「質が低かった」であって「使えなかった」ではない。程度の取り違え。",
      "研究者が写真を理解できなかったという記述はない。"
      "問題は写真の情報が失われることであって、読解力ではない。"])

E(G, 2,
  core="- `were regarded as ~` = 受動態「〜とみなされていた」。**当時の慣行**を示す\n"
       "- `like a test tube` = 様態の like。「実験器具と同じ扱い」という比喩がコア\n"
       "- `the illustrator's name did not appear` = 結果としての事実",
  kouzou="`[Scientific illustrations] were then regarded [as [part of the equipment], [like a test tube]], "
         "and [the illustrator's name did not appear].`\n"
         "  前半: S=Scientific illustrations / V=were regarded (受動) / C=as part of the equipment "
         "/ M=like a test tube, then (当時)\n"
         "  後半: S=the illustrator's name / V=did not appear",
  konkyo="第4段「She never signed them. **Scientific illustrations were then regarded as "
         "part of the equipment, like a test tube, and the illustrator's name did not appear.**」\n"
         "個人の事情ではなく当時の分野全体の慣行として説明されている。",
  ng=["本人が削除を求めたという記述はない。慣行として名前が載らなかった。",
      "共同制作についての記述はない。1994 年に `3,800 of her unsigned drawings` が"
      "彼女個人のものと特定されている。",
      "雇用主が自分の名で発表したという記述はなく、`by mistake` を支える根拠もない。"])

E(G, 3,
  core="- 伝記は**西暦**が並べ替えの手がかり。1923 → 1934 → その後 → 2001\n"
       "- `What followed was unexpected.` = 直前の出来事 (辞職) の**直後**を示すつなぎ\n"
       "- `She resigned two weeks later` の `later` が基準点からの前後関係を確定させる",
  kouzou="`Ines was employed [as a technical assistant] [in 1923].` … 顕微鏡の仕事の開始\n"
         "`She resigned [two weeks later].` (1934 年の会議拒否の 2 週間後)\n"
         "`[What followed] was unexpected. She opened a small studio and began teaching ~.`\n"
         "  S=What followed (関係代名詞 what「続いて起きたこと」) / V=was / C=unexpected\n"
         "`[A collection of them] was published [in 2001].`",
  konkyo="第3段「Ines was employed as a technical assistant in **1923**」→ "
         "第5段「In **1934** she was refused permission ~ She resigned two weeks later.」→ "
         "第6段「**What followed was unexpected.** She opened a small studio and began teaching」→ "
         "最終段「A collection of them was published in **2001**」",
  ng=["教え始めたのは辞職後 (`What followed`)。顕微鏡の仕事より前ではない。",
      "辞職は 1934 年で、顕微鏡の仕事を始めた 1923 年より後。最初の 2 つが逆。",
      "出版は 2001 年で、教え始めた 1934 年以降より後。最後の 2 つが逆。"])

E(G, 4,
  core="- `a scientist who could draw ~ would observe it more carefully than one who could only photograph it`\n"
       "  = 仮定法的な would + 比較級。**描ける科学者の方がよく観察する**が主張の核\n"
       "- `one` = a scientist の代用 (繰り返しを避ける代名詞)\n"
       "- `Her argument was simple` が主張の提示を予告する",
  kouzou="`[A scientist [who could draw a specimen]] would observe it [more carefully] "
         "than [one [who could only photograph it]].`\n"
         "  S=A scientist + 関係詞節 who could draw a specimen / V=would observe / O=it\n"
         "  M=more carefully than one who could only photograph it (比較の対象)\n"
         "  one = a scientist の代名詞",
  konkyo="第6段「Her argument was simple and, at the time, unusual: "
         "**a scientist who could draw a specimen would observe it more carefully "
         "than one who could only photograph it.**」\n"
         "コロンの後が彼女の主張そのもの。",
  ng=["署名の問題は第4段で経歴として語られるが、教育者としての主張ではない。",
      "写真を排除せよとは述べていない。描くことで観察が深まる、という主張にとどまる。",
      "報酬についての主張は本文にない。"])


# =====================================================================
# 第6問A 論説文の要旨
# =====================================================================
G = "第6問A 論説文の要旨"

E(G, 0,
  core="- `Both effects are strongly local.` = 段落の主題文。`local` =「局所的」がコア\n"
       "- `not by A but by B` = 冷却の仕組みを A ではなく B と特定する\n"
       "- `too small to measure` = `too ~ to do`「小さすぎて測れない」",
  kouzou="`[The main way [trees cool a city]] is [not by absorbing carbon dioxide ~ "
         "but by [providing shade] and [releasing water vapour from their leaves]].`\n"
         "  S=The main way + 関係詞節 (trees cool a city) / V=is / C=not by A but by B\n"
         "`A tree cools [the ground beneath it] and [the air within a few metres of it]; "
         "[a hundred metres away] [the difference] may be [too small to measure].`\n"
         "  セミコロンで近距離と遠距離を対比",
  konkyo="第2段「**Both effects are strongly local.** A tree cools the ground beneath it and "
         "the air within a few metres of it; a hundred metres away the difference may be too small to measure.」\n"
         "この主題文と具体化が段落全体を支配している。",
  ng=["`absorbing carbon dioxide, which happens far too slowly to affect summer temperatures` と、"
      "むしろ遅いと否定されている。",
      "同段落末で `A thousand trees planted in a park on the edge of a city therefore do very little "
      "for the crowded central district` と、都市全体には効かないと明言。",
      "蒸散 (releasing water vapour) は**冷却**の仕組みとして挙げられている。効果の向きが逆。"])

E(G, 1,
  core="- `while leaving that gap exactly where it was` = 付帯状況の while + 分詞。「格差をそのままにしたまま」\n"
       "- `can look like a complete success` = 見かけ上の成功。**実態との乖離**がこの段落の主張\n"
       "- `24% less tree cover` = 差を示す比較表現",
  kouzou="`[When a city counts only the total number of trees planted], [a programme] can look "
         "[like a complete success] [while leaving [that gap] [exactly where it was]].`\n"
         "  従属節: S=a city / V=counts / O=only the total number of trees planted\n"
         "  主節: S=a programme / V=can look / C=like a complete success\n"
         "  while 分詞句: leaving + O=that gap + C=exactly where it was (格差は元のまま)",
  konkyo="第3段「A survey of thirty-seven cities found that districts with lower average incomes had, "
         "on average, 24% less tree cover than wealthier districts in the same city. ~ "
         "**When a city counts only the total number of trees planted, a programme can look like "
         "a complete success while leaving that gap exactly where it was.**」",
  ng=["苗木の価格については `trees are cheap` と第1段にあり、高コストは論点ではない。",
      "植える場所の確保が難しいという記述はない。論点は「どこに植えるか」の選択であって用地不足ではない。",
      "成長速度についての記述はない。第4段の論点は生存率であって成長率ではない。"])

E(G, 2,
  core="- `depends far more on A than on B` = 比較級の強調 `far more`。**A の方が決定的**\n"
       "- `maintenance budgets` = 維持管理予算。ここが生存率の決定要因\n"
       "- `than on which species is chosen` = 比較対象として樹種を明示的に退ける",
  kouzou="`One review ~ estimated [that [between 15% and 30% of newly planted street trees] die "
         "[within five years]], and [that [survival] depends [far more on maintenance budgets] "
         "than [on which species is chosen]].`\n"
         "  S=One review / V=estimated / O=that 節 × 2 (and で並列)\n"
         "  第2の that 節: S=survival / V=depends / M=far more on A than on B\n"
         "    A=maintenance budgets / B=which species is chosen (間接疑問)",
  konkyo="第4段「**survival depends far more on maintenance budgets than on which species is chosen**」\n"
         "`far more ~ than` が予算 > 樹種 という優劣を明示している。",
  ng=["`than on which species is chosen` で、比較対象として**退けられている**側。"
      "far more A than B の B にあたる。",
      "植えるときの樹齢についての記述はない。",
      "同時に植える本数は第5段の論点 (総数主義への批判) だが、"
      "個々の木の生存率の決定要因としては挙げられていない。"])

E(G, 3,
  core="- `None of this is an argument against planting trees.` = 直前で**植樹自体は否定していない**と断る\n"
       "- `It is an argument against counting them.` = 対比。否定されるのは**数えること**\n"
       "- `counting` = 総本数を成果指標にすること、の言い換え",
  kouzou="`[None of this] is [an argument against planting trees]. "
         "[It] is [an argument against counting them].`\n"
         "  第1文: S=None of this / V=is / C=an argument against planting trees (植樹への反対を否定)\n"
         "  第2文: S=It / V=is / C=an argument against counting them\n"
         "  → against の目的語が planting → counting に置き換わる対比構造",
  konkyo="第5段「**None of this is an argument against planting trees. It is an argument against "
         "counting them.**」に続いて、200 本を 5 年間手入れする計画の方が 20,000 本植えて放置する計画より"
         "住民の役に立つ、と具体化される。\n"
         "最終段の「how many people are now standing in shade」も同じ主張の言い換え。",
  ng=["記録すること自体の否定ではない。最終段は**別の指標で測れ**と提案しており、計測の放棄ではない。",
      "本数を減らせとは述べていない。`None of this is an argument against planting trees` と明確に断っている。",
      "公表をやめよとは述べていない。むしろ `much harder to celebrate` な数値を採れと求めている。"])

E(G, 4,
  core="- タイトル問題は**第1段の主張文**と**最終段の結論**の両方に整合するものを選ぶ\n"
       "- `matters far less than where it plants them` = 「どこに植えるか」>「何本植えるか」\n"
       "- 本文が否定していない事柄まで否定する選択肢は不適",
  kouzou="`[researchers ~] have begun to argue [that [the number of trees a city plants] matters "
         "[far less than [where it plants them]]], and [that [some planting programmes] have produced "
         "[almost no measurable benefit]].`\n"
         "  S=researchers / V=have begun to argue / O=that 節 × 2\n"
         "  第1の that 節: S=the number of trees a city plants / V=matters / M=far less than where ~",
  konkyo="第1段「**the number of trees a city plants matters far less than where it plants them**」\n"
         "最終段「The question a city should ask is not \"how many trees have we planted?\" "
         "but \"**how many people are now standing in shade at two o'clock in the afternoon?**\"」\n"
         "冒頭の主張と結末の問いが一致している。",
  ng=["暑い地区こそ植えるべきだというのが本文の主張。正反対。",
      "`None of this is an argument against planting trees` および第2段の冷却機構の説明と矛盾する。"
      "冷却効果そのものは否定されていない。",
      "100 万本規模の計画は第1段・第5段で**批判の対象**として挙げられている。解決事例ではない。"])


# =====================================================================
# 第6問B 説明文の整理
# =====================================================================
G = "第6問B 説明文の整理"

E(G, 0,
  core="- `It hides the more useful question` = `hide`「覆い隠す」。**数字が問いを隠す**が主張\n"
       "- `at which point does the food disappear` = 前置詞 + 関係詞の間接疑問\n"
       "- `has stopped meaning very much` = 現在完了「意味を持たなくなってしまった」",
  kouzou="`[That figure] is quoted [so often] [that it has stopped meaning very much]. "
         "[It] hides [the more useful question]: [at which point does the food disappear], "
         "and [does the answer differ from country to country]?`\n"
         "  第1文: so ~ that 構文 (あまりに頻繁に引用され、その結果〜)\n"
         "  第2文: S=It (= that figure) / V=hides / O=the more useful question\n"
         "  コロン以下がその question の中身 (2 つの疑問文)",
  konkyo="第1段「That figure is quoted so often that it has stopped meaning very much. "
         "**It hides the more useful question: at which point does the food disappear, "
         "and does the answer differ from country to country?**」",
  ng=["数字が古いとは述べていない。問題にしているのは**内訳が見えないこと**。",
      "`Roughly a third` は小さい割合ではなく、深刻さを示す数字として引用されている。",
      "第2段以降で低所得国と高所得国の**両方**を扱っており、適用範囲の限定は誤り。"])

E(G, 1,
  core="- `expensive relative to income` = `relative to`「〜に比べて」。**所得比での高さ**がコア\n"
       "- `be careful with ~` =「〜を大事に扱う」\n"
       "- `because` が理由を直接示す",
  kouzou="`[Very little] is thrown away [by households], [because [food is expensive relative to income] "
         "and [people are careful with it]].`\n"
         "  主節: S=Very little / V=is thrown away (受動) / M=by households\n"
         "  because 節: 2 文が and で並列\n"
         "    S=food / V=is / C=expensive relative to income ・ S=people / V=are careful with it",
  konkyo="第2段「Very little is thrown away by households, "
         "**because food is expensive relative to income and people are careful with it.**」",
  ng=["同じ段落に `spoil in transport because there is no refrigeration` とあり、冷蔵設備は**ない**。正反対。",
      "調理済み食品の購入についての記述はない。",
      "罰金などの政策についての記述はない。"])

E(G, 2,
  core="- `more than A, B, C and D combined` = 「A〜D を合わせたより多い」。**combined** が急所\n"
       "- `be responsible for ~` =「〜の原因である・〜を占める」\n"
       "- `between 45% and 55%` = 幅を持った割合",
  kouzou="`[In several European studies], [households] were responsible for "
         "[between 45% and 55% of all the food wasted in the country] "
         "— [more than [farms, factories, shops and restaurants] combined].`\n"
         "  S=households / V=were responsible for / O=between 45% and 55% ~\n"
         "  ダッシュ以下が比較の補足: more than A, B, C and D combined",
  konkyo="第4段「**households were responsible for between 45% and 55% of all the food wasted "
         "in the country — more than farms, factories, shops and restaurants combined.**」",
  ng=["レストランは家庭より少ない側として列挙されている。大小が逆。",
      "第4段冒頭に `losses before the shop are comparatively small` とあり、"
      "高所得国では輸送段階の損失は小さい。",
      "45〜55% は**家庭**の割合。スーパーマーケットの数値ではない。数値の係り先の取り違え。"])

E(G, 3,
  core="- `not one behaviour but many` = not A but B。**単一の行動ではなく多数**\n"
       "- `Each of these has a different solution` = だから対策も一つにならない\n"
       "- `read as if it read \"use by\"` = 仮定法の as if。表示の誤読を示す",
  kouzou="`[Household waste] is also [the hardest kind to reduce], "
         "[because [it] is [not one behaviour but many]].`\n"
         "  主節: S=Household waste / V=is / C=the hardest kind to reduce (不定詞が kind を修飾)\n"
         "  because 節: S=it / V=is / C=not one behaviour but many (= many behaviours)\n"
         "  → 続く 3 つの具体例 (3 個パック・作りすぎ・表示の誤読) が many の中身",
  konkyo="第5段「Household waste is also the hardest kind to reduce, "
         "**because it is not one behaviour but many.**」\n"
         "3 つの例のあとに「**Each of these has a different solution**」と締められる。",
  ng=["調査への非協力についての記述はない。",
      "第4段で家庭の割合が数値化されており、測定できている。",
      "第2段で低所得国の家庭についても論じており、富裕国限定ではない。"])

E(G, 4,
  core="- `their effects fade` = `fade`「薄れる」。**効果の減衰**がこの段落の主張\n"
       "- `a return to earlier levels within a year of its end` = 終了後 1 年以内に元の水準へ戻る\n"
       "- `not useless, but ~` = 全否定ではない譲歩。断定の強さに注意",
  kouzou="`[Educational campaigns] are [not useless], but [their effects fade]. "
         "Studies ~ show [a reduction [while the campaign is running]] and "
         "[a return to earlier levels [within a year of its end]].`\n"
         "  第1文: S=Educational campaigns / V=are / C=not useless ・ S=their effects / V=fade\n"
         "  第2文: S=Studies / V=show / O=a reduction と a return (等位接続)",
  konkyo="第7段「Educational campaigns are not useless, but **their effects fade.** "
         "Studies of household campaigns generally show a reduction while the campaign is running "
         "and **a return to earlier levels within a year of its end.**」",
  ng=["第6段は `the measures that work best tend to be structural rather than educational` とし、"
      "販売方法の変更の方が有効だと述べている。優劣が逆。",
      "`Educational campaigns are not useless` と明示的に否定されている。"
      "「全く効果がない」は本文より強すぎる。",
      "低所得国との関連づけは本文にない。"])


# =====================================================================
# 第3問A 体験記事
# =====================================================================
G = "第3問A 体験記事"

E(G, 0,
  core="- `What surprised me was ~` = 強調構文的な what 節。**驚いた対象**が be 動詞の後ろに来る\n"
       "- `I had expected it to be soft. In fact ~` = 予想と現実の対比。`In fact` の後ろが実際\n"
       "- `grip` =「つかんで離さない」。柔らかさの逆を表す動詞がコア",
  kouzou="`[What surprised me] was [the mud].`\n"
         "  S=What surprised me (関係代名詞 what 節) / V=was / C=the mud\n"
         "`In fact [it] grips [your feet] and does not let go, and "
         "[lifting one leg while balancing on the other] is [far harder than it looks].`\n"
         "  前半: S=it (= the mud) / V=grips / O=your feet ・ V=does not let go\n"
         "  後半: S=動名詞句 lifting one leg ~ / V=is / C=far harder than it looks",
  konkyo="第4段「**What surprised me was the mud.** I had expected it to be soft. "
         "In fact it grips your feet and does not let go, and lifting one leg while balancing "
         "on the other is far harder than it looks.」\n"
         "`What surprised me was ~` が「最も驚いたこと」を名指ししている。",
  ng=["電車は `the 6:40 train` `about an hour north of the city` と述べられるだけで、"
      "所要時間に驚いたという記述はない。",
      "第1段に `now works it alone` (今は一人で耕している) とあり、雇っている人はいない。"
      "むしろ人手がないことが招待の背景になっている。",
      "水の冷たさについての記述は本文にない。驚いたのは泥の「柔らかさの予想が外れたこと」。"])

E(G, 1,
  core="- `return` =「戻る」。同じ場所への再訪を含意する\n"
       "- `for the harvest` = 目的の for。「収穫のために」\n"
       "- `Sign up ~ by 5 August` = 期限の by。締切であって実施日ではない",
  kouzou="`[The club] returns [in September] [for the harvest].`\n"
         "  S=The club / V=returns (確定した予定を表す現在形) / M=in September, for the harvest\n"
         "`Sign up [at the club room] [by 5 August].`\n"
         "  命令文: V=Sign up / M=at the club room, by 5 August",
  konkyo="最終段「**The club returns in September for the harvest.** "
         "Sign up at the club room by 5 August.」\n"
         "9 月の予定は「収穫の手伝いに戻る」こと。8 月 5 日は申込の締切であって活動日ではない。",
  ng=["Mr Ito が学校を訪れるという記述はない。訪れるのは部員の側。",
      "`returns` は同じ場所に戻ることを示す。別の村へ行くとは述べられていない。",
      "`We can take twenty-five people this time` と 25 人規模の活動であり、"
      "Nao が単独で作業するという記述はない。"])
