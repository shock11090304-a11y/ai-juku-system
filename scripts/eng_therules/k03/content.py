# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.03 — 単一ソース
テーマ: The Power of Small Habits (小さな習慣の力) / 基礎レベル（偏差値55〜60 / The Rules 1〜2 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "03",
    "level": "基礎レベル",
    "level_sub": "偏差値55〜60 / The Rules 1〜2 相当",
    "theme_ja": "小さな習慣の力",
    "theme_en": "The Power of Small Habits",
    "minutes": 15,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Many of us believe that big results demand big decisions. To change our lives, we '
        'think, we must make a grand plan and attack it with one great burst of effort. We '
        'wait for the perfect Monday, buy a thick notebook, and promise to become a new '
        'person overnight. <span class="blank">【&nbsp;A&nbsp;】</span>, research on human '
        'behavior suggests that this belief is exactly what makes so many of our plans '
        'collapse.'),
    (2, 'It is true that the excitement of a fresh start feels wonderful. When we write down '
        'our goals for a new year, our hearts beat faster and everything seems possible. That '
        'energy is real, and it can push us through the first few days. Nobody should feel '
        'ashamed of loving that bright, hopeful moment.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, what carries us through the months '
        'ahead is not strong resolve but a small system. A habit is an action so easy that we '
        'can repeat it every day, such as reading two pages before bed. Motivation rises and '
        'falls like the weather; a small daily habit, in contrast, works quietly whatever our '
        'mood. It is a quiet engine that keeps running after the fireworks of the first week '
        'have faded.'),
    (4, 'Consider a student who practices English vocabulary for just five minutes a day. '
        'Five minutes looks almost meaningless, and on any single day it changes nothing. '
        'Over a year, however, those minutes add up to more than thirty hours of steady '
        'practice. The student who repeats a tiny step every day will stand, twelve months '
        'later, far ahead of one who kept waiting for a free weekend.'),
    (5, 'Smallness has another advantage: it is hard to fail. Because the bar is so low, we '
        'can start even on busy or tired days. And each time we finish, we collect a small '
        'piece of evidence that we can continue. That evidence becomes confidence, and '
        'confidence makes the next day easier still. In this way success feeds on itself, '
        'one tiny win at a time.'),
    (6, 'Here lies the real lesson about failure. <u>When we abandon a goal, the true cause '
        'is usually not a lack of willpower but a first step that is too big.<sup>(1)</sup></u> '
        'If the first step asks for an hour of effort, a single hard day can break the chain. '
        'If it asks for five minutes, almost nothing can stop us. We do not need a stronger '
        'will; we need a smaller beginning.'),
    (7, 'None of this means that we should shrink our dreams. Aim as high as you like &mdash; '
        'a distant university, a foreign language, a healthier body. The advice is simpler '
        'and kinder: <u>keep the goal large and the entrance small.<sup>(2)</sup></u> A door '
        'of five minutes is one that we can open every single day. And <u>small habits, '
        'repeated daily, will carry us further than grand resolutions ever do.<sup>(3)</sup></u>'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Many of us believe that big results demand big decisions. To change our lives, we think, "
    "we must make a grand plan and attack it with one great burst of effort. We wait for the "
    "perfect Monday, buy a thick notebook, and promise to become a new person overnight. Yet, "
    "research on human behavior suggests that this belief is exactly what makes so many of our "
    "plans collapse. "
    "It is true that the excitement of a fresh start feels wonderful. When we write down our "
    "goals for a new year, our hearts beat faster and everything seems possible. That energy is "
    "real, and it can push us through the first few days. Nobody should feel ashamed of loving "
    "that bright, hopeful moment. "
    "Still, what carries us through the months ahead is not strong resolve but a small system. "
    "A habit is an action so easy that we can repeat it every day, such as reading two pages "
    "before bed. Motivation rises and falls like the weather; a small daily habit, in contrast, "
    "works quietly whatever our mood. It is a quiet engine that keeps running after the "
    "fireworks of the first week have faded. "
    "Consider a student who practices English vocabulary for just five minutes a day. Five "
    "minutes looks almost meaningless, and on any single day it changes nothing. Over a year, "
    "however, those minutes add up to more than thirty hours of steady practice. The student "
    "who repeats a tiny step every day will stand, twelve months later, far ahead of one who "
    "kept waiting for a free weekend. "
    "Smallness has another advantage: it is hard to fail. Because the bar is so low, we can "
    "start even on busy or tired days. And each time we finish, we collect a small piece of "
    "evidence that we can continue. That evidence becomes confidence, and confidence makes the "
    "next day easier still. In this way success feeds on itself, one tiny win at a time. "
    "Here lies the real lesson about failure. When we abandon a goal, the true cause is usually "
    "not a lack of willpower but a first step that is too big. If the first step asks for an "
    "hour of effort, a single hard day can break the chain. If it asks for five minutes, almost "
    "nothing can stop us. We do not need a stronger will; we need a smaller beginning. "
    "None of this means that we should shrink our dreams. Aim as high as you like a distant "
    "university, a foreign language, a healthier body. The advice is simpler and kinder: keep "
    "the goal large and the entrance small. A door of five minutes is one that we can open "
    "every single day. And small habits, repeated daily, will carry us further than grand "
    "resolutions ever do."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Yet &nbsp; ② Therefore &nbsp; ③ For example &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① As a result &nbsp; ② For instance &nbsp; ③ Still &nbsp; ④ Similarly",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(1) <span class='en'>When we abandon a goal, the true cause is usually not "
             "a lack of willpower but a first step that is too big.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(2) <span class='en'>keep the goal large and the entrance small</span>"
             "（目標は大きく、入口は小さく保て）とはどういうことか。「入口（<span class='en'>the "
             "entrance</span>）」が何を指すかを明らかにしつつ、本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で挙げられている「1日5分の英単語練習」の例の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 5分の練習は、たとえ1日だけでも大きな変化を生むので、すぐに成果を実感できると述べられている。",
         "② 1日単位ではほとんど何も変わらないが、1年間続ければ30時間を超える着実な練習になると述べられている。",
         "③ 5分の練習は短すぎて意味がないので、まとまった時間の取れる週末に学習する方がよいと述べられている。",
         "④ 単語の練習では、毎日の練習時間の長さよりも、使う教材の質の方がはるかに重要だと述べられている。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>small habits, repeated daily, will carry us further "
             "than grand resolutions ever do</span> について、なぜ小さな習慣は壮大な決意よりも"
             "私たちを遠くまで運ぶのか。本文全体をふまえ、その理由を二つ挙げて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 意志の力さえ鍛えれば、どんなに大きな計画でも一気の努力によって必ずやり遂げることができる。",
         "② 失敗を避けるためには、夢や目標そのものをできるだけ小さくしておくのが賢明なやり方である。",
         "③ 挫折の真の原因は意志の弱さではなく最初の一歩の大きさにあり、目標は大きく保ったまま入口を小さくすべきだ。",
         "④ 新しい目標を立てるときの高揚感は失敗のもとになる有害なものなので、完全に捨て去るべきである。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 私たちは、人生を変えるには壮大な計画と一度の大きな集中的努力が必要だと思い込みがちである。",
         "② 小さな毎日の習慣は、天気のように上下する意欲とは違い、どんな気分の日でも静かに働き続ける。",
         "③ 筆者は、新しい出発のときに感じる高揚感は本物ではないので、信じてはならないと述べている。",
         "④ ハードルの低い習慣であっても、忙しい日や疲れている日には決して始めることができない。",
         "⑤ 筆者は、確実に達成するために、大きな夢はあきらめて目標を縮小するようにと勧めている。",
         "⑥ 最初の一歩が1時間の努力を求めるものだと、たった一日つらい日があるだけで継続が途切れうる。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ① Yet　　B ＝ ③ Still",
     "exp": "A：「大きな結果には大きな決断が必要」という通念に対し、研究は「その思い込みこそ挫折の"
            "原因」と<b>反論</b>する流れ。逆接 → Yet。Therefore（因果）・For example（例示）・"
            "In addition（追加）は不可。<br>"
            "B：第2段「確かに新しい出発の高揚感は本物（＝譲歩）」に対し、第3段は「だが続くのは決意"
            "ではなく小さな仕組み」と主張へ<b>転換</b>する。逆接 → Still。As a result（因果）・"
            "For instance（例示）・Similarly（類比）は流れに合わない。 〔<b>解法ルール R7</b>／"
            "<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "②",
     "exp": "第4段「on any single day it changes nothing」＋「Over a year, however, those "
            "minutes add up to more than thirty hours of steady practice」＝1日では何も変わらないが、"
            "1年で30時間超の練習になる。①は逆（1日では何も変わらない）、③は本文と逆（週末を待った"
            "生徒の方が遅れる）、④は本文にない（教材の質の話はしていない）。 〔<b>解法ルール R9</b>／"
            "<b>読解ルール R4</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "③",
     "exp": "第6段「not a lack of willpower but a first step that is too big」＋第7段「keep the "
            "goal large and the entrance small」と一致。①は第1段の通念そのもので、研究が否定して"
            "いる（「必ず」も言い過ぎ）。②は第7段「None of this means that we should shrink our "
            "dreams」に反する。④は第2段「That energy is real（本物だ）」に反する（「完全に」も"
            "言い過ぎ）。 〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・②・⑥",
     "exp": "③×：第2段「That energy is real（そのエネルギーは本物）」に反する。"
            "④×：第5段「we can start even on busy or tired days（忙しい日や疲れた日でさえ始め"
            "られる）」に反する。「決して」が典型的な<b>言い過ぎ</b>。"
            "⑤×：第7段「None of this means that we should shrink our dreams（夢を縮めるべきだ"
            "という意味ではない）」で明確に否定。 〔<b>解法ルール R9</b>：言い換えの見抜き＋"
            "「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(1)和訳",
     "model": "私たちが目標を投げ出すとき、その本当の原因はたいてい、意志の力が足りないことではなく、"
              "最初の一歩が大きすぎることなのである。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「AではなくB」の対比を訳に反映／②a lack of "
               "willpower＝意志力の欠如・不足／③a first step &lt;that is too big&gt;＝関係詞節を"
               "「大きすぎる最初の一歩」と名詞にかけて訳す。 〔<b>読解ルール R3</b>／<b>構文ルール "
               "R11</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "目指す目標そのものは高く大きいまま保ってよいが、そこへ向かって毎日実際に取りかかる"
              "最初の行動（＝入口）は、1日5分の練習のように、どんな日でも必ず始められるほど小さく"
              "せよ、ということ。",
     "points": "▶<b>採点要素</b>：①「目標は大きく」＝夢や目標を縮めない（第7段）／②「入口」＝毎日"
               "実際に始める最初の行動・第一歩だと明示／③「小さく」＝5分の扉のように毎日開けられる・"
               "失敗しにくい小ささにする。 〔<b>解法ルール R8</b>：コロン(:)の言い換えを利用／"
               "<b>読解ルール R3</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①小さな一歩は毎日積み重なり、1日5分の練習が1年で30時間を超えるように、長い目で見れば"
              "大きな差を生むから。②ハードルが低いため忙しい日や疲れた日でも始められて失敗しにくく、"
              "続いたという証拠が自信となって、翌日の継続をさらに容易にするから。",
     "points": "▶<b>採点要素</b>：本文全体から小さな習慣の強みを二つ取り出す。①<b>積み重ね</b>"
               "（第4段：add up to more than thirty hours）／②<b>失敗しにくさ＋自信の好循環</b>"
               "（第5段：hard to fail → evidence → confidence）。各5点。 〔<b>読解ルール R4・R6</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（Yet→研究の反論）、空所B（Still→第3段で主張へ転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that the excitement … feels wonderful」→ 第3段 Still で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "第3段 not strong resolve but a small system、下線部(1) not a lack of willpower but a first step。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段「1日5分の単語練習」は〈小さな習慣→大きな差〉という抽象の具体例。第7段の目標の列挙も例示。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "第5段 That evidence＝「やり終えた」という事実、第7段 None of this＝第6段までの主張全体。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第5段 Because the bar is so low … と〈証拠→自信→翌日が容易〉の連鎖、第6段の If 節。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。A＝通念⇔研究（逆接）、B＝譲歩⇔主張（逆接）。因果・例示・追加・類比の選択肢は不成立。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。第5段・第7段のコロン(:)＝直前の言い換え・中身の提示を利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。④「決して始められない」・①「必ずやり遂げられる」などが典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "a first step &lt;that is too big&gt;、small habits, &lt;repeated daily&gt;（過去分詞）。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「大きな結果には大きな決断と一気の努力が必要」を提示。→ <b>Yet（R1）</b>：研究は"
             "「この思い込みこそが計画を挫折させる」と反論。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに新しい出発の高揚感は本物で、最初の数日を"
             "押し進めてくれる。＝通念の魅力は認める。"},
    {"arrow": "◀ Still 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "数か月を乗り切らせるのは<b>強い決意ではなく「小さな仕組み」＝毎日の小さな習慣"
             "（not A but B＝R3）</b>。意欲は天気のように変わるが、習慣は静かなエンジン。"},
    {"arrow": "↓　具体化（R4）"},
    {"role": "理由①", "para": "¶4", "kind": "reason",
     "text": "<b>積み重ね</b>：1日5分の単語練習は、1日では何も変えないが、1年で30時間超の練習に"
             "なる。小さな一歩の反復が、1年後の大きな差を生む。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>失敗しにくさ</b>：ハードルが低い→忙しい日でも始められる→「続けられた」という証拠が"
             "自信になり、翌日がさらに容易になる（<b>R6 因果の連鎖</b>）。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "挫折の真因は<b>意志の弱さではなく「大きすぎる最初の一歩」</b>（not a lack of willpower "
             "but a first step that is too big＝<b>R3</b>）。必要なのは強い意志ではなく小さな始まり。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：夢を縮めよという話ではない。<b>目標は大きく、入口は小さく</b>——"
             "5分の扉は毎日開けられ、小さな習慣は壮大な決意より遠くへ運ぶ。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 同じ目標への二つの入口",
     "caption": "同じ目標でも、<b>大きな決意・一気の努力</b>から入ると、つらい一日で継続の鎖が"
                "切れてしまう。<b>小さな習慣（1日5分）</b>から入ると、毎日続いて1年後に大きな差がつく。",
     "para": "→ 第1・4・6段"},
    {"id": "fig2", "title": "図2 ｜ 小さな習慣が効く二つの理由",
     "caption": "小さな習慣の強みは二つ。①<b>積み重ね</b>（第4段）：1日5分→1年で30時間超。"
                "②<b>失敗しにくさ</b>（第5段）：低いハードル→続いた証拠→自信→さらに継続。"
                "下線部(3)＝問5はこの二つを指す。",
     "para": "→ 第4〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 意志の弱さではなく、一歩の大きさ",
     "caption": "挫折の真因は<b>意志の力の欠如ではなく、大きすぎる最初の一歩</b>。夢を縮めるのでは"
                "なく、<b>目標は大きく、入口は小さく</b>——入口を「5分の扉」にする。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "私たちの多くは、大きな結果には大きな決断が必要だと信じている。人生を変えるには、壮大な計画を"
        "立て、一度の大きな集中的努力でそれに立ち向かわなければならない、と考えるのだ。私たちは完璧な"
        "月曜日が来るのを待ち、分厚いノートを買い、一晩で新しい人間になると誓う。<b>しかし</b>、人間の"
        "行動に関する研究は、まさにこの思い込みこそが、私たちの計画の多くを挫折させるものなのだと示唆"
        "している。"),
    (2, "確かに、新たな出発の高揚感はすばらしいものに感じられる。新しい年の目標を書き出すとき、心臓は"
        "高鳴り、すべてが可能に思える。そのエネルギーは本物であり、最初の数日間を乗り切らせてもくれる。"
        "あの明るく希望に満ちた瞬間を愛することを、誰も恥じる必要はない。"),
    (3, "<b>それでも</b>、この先の数か月を乗り切らせてくれるのは、強い決意ではなく、小さな仕組みである。"
        "習慣とは、寝る前に2ページ読むというような、毎日繰り返せるほど簡単な行動のことだ。意欲は天気の"
        "ように上がり下がりするが、それとは対照的に、毎日の小さな習慣は、気分がどうであれ静かに働き"
        "続ける。それは、最初の1週間の花火が消えたあとも回り続ける、静かなエンジンなのである。"),
    (4, "1日にたった5分だけ英単語を練習する生徒のことを考えてみよう。5分はほとんど無意味に見えるし、"
        "どの一日を取ってみても、それは何も変えはしない。しかし1年間では、その数分が積み重なって、"
        "30時間を超える着実な練習になる。小さな一歩を毎日繰り返す生徒は、12か月後には、空いた週末を"
        "ずっと待ち続けていた生徒のはるか先に立っているだろう。"),
    (5, "小ささには、もう一つの利点がある。すなわち、失敗しにくいということだ。ハードルがとても低いので、"
        "忙しい日や疲れた日でさえ始めることができる。そして一回やり終えるたびに、私たちは「自分は続け"
        "られる」という小さな証拠を手に入れる。その証拠は自信となり、自信は翌日をさらに容易にする。"
        "このようにして、成功は一度に一つの小さな勝利ずつ、自らを糧にして育っていくのである。"),
    (6, "ここにこそ、失敗についての本当の教訓がある。<b>私たちが目標を投げ出すとき、その本当の原因は"
        "たいてい、意志の力が足りないことではなく、最初の一歩が大きすぎることなのである。</b>最初の一歩が"
        "1時間の努力を要求するものなら、たった一日つらい日があるだけで、継続の鎖は断ち切られかねない。"
        "それが5分しか求めないなら、私たちを止められるものはほとんど何もない。必要なのはより強い意志では"
        "ない。より小さな始まりなのだ。"),
    (7, "とはいえ以上のことは、夢を縮めるべきだという意味ではない。好きなだけ高く狙えばよい——遠くの"
        "大学でも、外国語でも、より健康な体でも。助言はもっと単純で優しいものだ。すなわち、<b>目標は"
        "大きく、入口は小さく保て</b>。5分の扉なら、一日も欠かさず開けることができる。そして、<b>毎日"
        "繰り返される小さな習慣は、壮大な決意がそうしてくれる以上に遠くまで、私たちを運んでいくので"
        "ある。</b>"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("demand", "〜を必要とする、要求する"),
    ("a burst of effort", "一気の（集中的な）努力"),
    ("overnight", "一晩で、たちまち"),
    ("collapse", "崩れる、挫折する"),
    ("a fresh start", "新たな出発"),
    ("push A through B", "AにBを乗り切らせる"),
    ("be ashamed of ~", "〜を恥じる"),
    ("resolve", "（名詞）決意"),
    ("carry A through B", "AにBを乗り切らせる、切り抜けさせる"),
    ("in contrast", "対照的に"),
    ("whatever our mood", "気分がどうであれ"),
    ("fade", "薄れる、消えていく"),
    ("add up to ~", "積み重なって（合計で）〜になる"),
    ("steady", "着実な"),
    ("far ahead of ~", "〜のはるか先に"),
    ("advantage", "利点"),
    ("the bar is low", "ハードルが低い"),
    ("feed on ~", "〜を糧にする"),
    ("abandon", "〜を投げ出す、断念する"),
    ("willpower", "意志の力"),
    ("break the chain", "（継続の）鎖を断ち切る"),
    ("shrink", "〜を縮める"),
    ("resolution", "決意、（新年の）誓い"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：「大きな結果には大きな決断」という通念と、その反転",
  "sentences": [
    {"chunks": [("S","Many of us","私たちの多くは"),("V","believe","信じている"),
                ("O","[that big results demand big decisions].","大きな結果は大きな決断を必要とする、と")],
     "note":"▶ believe that 節。<b>demand</b>＝「〜を要求する・必要とする」。通念の提示（この後 Yet で反転される）。"},
    {"chunks": [("M","(To change our lives),","人生を変えるためには"),("M","we think,","と私たちは考える"),
                ("S","we","私たちは"),("V","must make","立てなければならない"),("O","a grand plan","壮大な計画を"),
                ("接","and","そして"),("V","attack","攻めなければ（ならない）"),("O","it","それに"),
                ("M","(with one great burst of effort).","一度の大きな集中的努力で")],
     "note":"▶ To change …＝目的の不定詞。we think は挿入。make と attack は must を共有する並列。a burst of effort＝「一気の努力」。"},
    {"chunks": [("S","We","私たちは"),("V","wait for","待ち"),("O","the perfect Monday,","完璧な月曜日を"),
                ("V","buy","買い"),("O","a thick notebook,","分厚いノートを"),
                ("接","and","そして"),("V","promise","誓う"),
                ("O","to become a new person overnight.","一晩で新しい人間になることを")],
     "note":"▶ wait for ／ buy ／ promise の三つの動詞が並列。promise to do＝「〜すると誓う」。overnight＝「一晩で」。"},
    {"chunks": [("接","Yet,","しかし"),("S","research &lt;on human behavior&gt;","人間の行動に関する研究は"),
                ("V","suggests","示唆している"),
                ("O","[that this belief is exactly what makes so many of our plans collapse].","この思い込みこそが、私たちの計画の多くを挫折させるものなのだ、と")],
     "note":"▶ <b>R1｜逆接 Yet の直後が主張</b>（＝空所A）。what makes O <i>do</i>＝「Oを〜させるもの」（make O 原形）。exactly が what 節を強調＝「まさに〜こそ」。"},
  ]},
 {"head": "第2段 — 譲歩：確かに新しい出発の高揚感は本物だ（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当"),
                ("-","[that the excitement of a fresh start feels wonderful].","新たな出発の高揚感がすばらしく感じられるということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。形式主語 It＝真主語 that 節。後の逆接（第3段 Still）で反転する前振り。"},
    {"chunks": [("M","(When we write down our goals for a new year),","新しい年の目標を書き出すとき"),
                ("S","our hearts","心臓は"),("V","beat","打つ"),("M","faster","より速く"),
                ("接","and","そして"),("S","everything","すべてが"),("V","seems","思われる"),("C","possible.","可能に")],
     "note":"▶ When 節＝副詞節（時）。seem C＝「Cに思われる」。二つの短い文の並列で高揚感を描く。"},
    {"chunks": [("S","That energy","そのエネルギーは"),("V","is","である"),("C","real,","本物"),
                ("接","and","そして"),("S","it","それは"),("V","can push","押し進めてくれる"),("O","us","私たちを"),
                ("M","(through the first few days).","最初の数日間を")],
     "note":"▶ <b>push A through B</b>＝「AにBを乗り切らせる」。<b>R9注意</b>：問7③「高揚感は本物ではない」はこの文（real）に反する。"},
    {"chunks": [("S","Nobody","誰も〜ない"),("V","should feel","感じるべきではない"),("C","ashamed","恥ずかしく"),
                ("M","(of loving that bright, hopeful moment).","あの明るく希望に満ちた瞬間を愛することを")],
     "note":"▶ feel ashamed of <i>doing</i>＝「〜することを恥じる」。動名詞 loving。譲歩の駄目押し（高揚感を否定しない）。"},
  ]},
 {"head": "第3段 — 主張転換：続くのは決意ではなく「小さな仕組み」（Still）",
  "sentences": [
    {"chunks": [("接","Still,","それでも"),
                ("S","[what carries us through the months ahead]","この先の数か月を乗り切らせてくれるものは"),
                ("V","is","である"),
                ("C","not strong resolve but a small system.","強い決意ではなく、小さな仕組み")],
     "note":"▶ <b>R1｜Still＝逆接でここが主張転換点</b>（＝空所B）。<b>R3｜not A but B＝Bが核心</b>。関係代名詞 what＝「〜するもの」のカタマリが主語。"},
    {"chunks": [("S","A habit","習慣とは"),("V","is","である"),
                ("C","an action &lt;so easy that we can repeat it every day&gt;,","毎日繰り返せるほど簡単な行動"),
                ("M","such as reading two pages before bed.","たとえば寝る前に2ページ読むような")],
     "note":"▶ <b>so … that ~</b>＝「~するほど…」が action を説明。such as＝例示（<b>R4</b>）。"},
    {"chunks": [("S","Motivation","意欲は"),("V","rises and falls","上がり下がりする"),
                ("M","(like the weather);","天気のように"),
                ("S","a small daily habit,","毎日の小さな習慣は"),("M","in contrast,","対照的に"),
                ("V","works","働く"),("M","quietly (whatever our mood).","気分がどうであれ、静かに")],
     "note":"▶ セミコロン＋<b>in contrast</b>＝〈意欲⇔習慣〉の対比を並置。whatever our mood＝「気分がどうであれ」（譲歩）。＝問7②の根拠。"},
    {"chunks": [("S","It","それは"),("V","is","である"),
                ("C","a quiet engine &lt;that keeps running (after the fireworks of the first week have faded)&gt;.","最初の1週間の花火が消えたあとも回り続ける、静かなエンジン")],
     "note":"▶ <b>R11｜関係詞 that</b> が engine を後ろから説明。keep <i>doing</i>＝「〜し続ける」。比喩：決意＝花火（一瞬）⇔習慣＝エンジン（持続）。"},
  ]},
 {"head": "第4段 — 理由①：積み重ね（抽象→具体：1日5分の単語練習）",
  "sentences": [
    {"chunks": [("V","Consider","考えてみよう"),
                ("O","a student &lt;who practices English vocabulary for just five minutes a day&gt;.","1日たった5分だけ英単語を練習する生徒を")],
     "note":"▶ <b>R4｜抽象→具体</b>：ここからが「小さな習慣」の具体例。命令文 Consider ＝「〜を考えてみよ」。who＝関係代名詞。"},
    {"chunks": [("S","Five minutes","5分は"),("V","looks","見える"),("C","almost meaningless,","ほとんど無意味に"),
                ("接","and","そして"),("M","(on any single day)","どの一日を取っても"),
                ("S","it","それは"),("V","changes","変えない"),("O","nothing.","何も")],
     "note":"▶ look C＝「Cに見える」。change nothing＝「何も変えない」。まず「小ささ」を認める（譲歩）。問4①はこの文に反する。"},
    {"chunks": [("M","(Over a year),","1年間では"),("接","however,","しかし"),
                ("S","those minutes","その数分は"),("V","add up to","積み重なって〜になる"),
                ("O","more than thirty hours of steady practice.","30時間を超える着実な練習に")],
     "note":"▶ <b>add up to</b>＝「合計で〜になる」。however＝対比（1日⇔1年）。＝問4②の根拠。"},
    {"chunks": [("S","The student &lt;who repeats a tiny step every day&gt;","小さな一歩を毎日繰り返す生徒は"),
                ("V","will stand,","立っているだろう"),("M","twelve months later,","12か月後に"),
                ("M","(far ahead of one &lt;who kept waiting for a free weekend&gt;).","空いた週末を待ち続けた生徒のはるか先に")],
     "note":"▶ <b>R11｜関係詞</b>が二つの student を対比的に説明。one＝a student の代用。keep <i>doing</i>＝「〜し続ける」。"},
  ]},
 {"head": "第5段 — 理由②：失敗しにくさ → 自信の好循環",
  "sentences": [
    {"chunks": [("S","Smallness","小ささには"),("V","has","ある"),("O","another advantage:","もう一つの利点が"),
                ("S","it","それは"),("V","is","である"),("C","hard to fail.","失敗しにくい（ということ）")],
     "note":"▶ <b>R8｜コロン(:)＝直前の言い換え・中身の提示</b>。advantage の中身＝hard to fail。理由②の主題提示。"},
    {"chunks": [("接","Because","〜なので"),("S","the bar","ハードルが"),("V","is","である"),("C","so low,","とても低い"),
                ("S","we","私たちは"),("V","can start","始められる"),
                ("M","(even on busy or tired days).","忙しい日や疲れた日でさえ")],
     "note":"▶ <b>R6｜Because＝因果</b>。the bar＝「ハードル・基準」。<b>R9注意</b>：問7④「決して始められない」はこの文に反する（言い過ぎ）。"},
    {"chunks": [("M","(And each time we finish),","そして、やり終えるたびに"),
                ("S","we","私たちは"),("V","collect","集める"),
                ("O","a small piece of evidence","小さな証拠を"),
                ("-","[that we can continue].","＝自分は続けられるという")],
     "note":"▶ each time SV＝接続詞的「〜するたびに」。that we can continue＝evidence の中身を示す<b>同格</b>の that 節。"},
    {"chunks": [("S","That evidence","その証拠は"),("V","becomes","になる"),("C","confidence,","自信に"),
                ("接","and","そして"),("S","confidence","自信は"),("V","makes","する"),
                ("O","the next day","翌日を"),("C","easier still.","さらに容易に")],
     "note":"▶ <b>R6｜因果の連鎖</b>：続いた事実→自信→翌日が容易。<b>R5</b>｜That evidence＝直前の「やり終えた」という事実。make O C。easier still＝「いっそう容易に」。"},
    {"chunks": [("M","(In this way)","このようにして"),("S","success","成功は"),
                ("V","feeds on","糧にして育つ"),("O","itself,","自分自身を"),
                ("M","one tiny win at a time.","一度に一つの小さな勝利ずつ")],
     "note":"▶ feed on oneself＝「自らを糧に増幅する」。In this way＝直前の因果ループの要約。"},
  ]},
 {"head": "第6段 — 核心的主張：意志の弱さではなく「大きすぎる最初の一歩」",
  "sentences": [
    {"chunks": [("M","Here","ここに"),("V","lies","ある"),
                ("S","the real lesson &lt;about failure&gt;.","失敗についての本当の教訓が")],
     "note":"▶ <b>Here lies S</b>＝副詞が文頭に出た倒置（M＋V＋S）。核心段の予告。"},
    {"chunks": [("M","(When we abandon a goal),","目標を投げ出すとき"),
                ("S","the true cause","本当の原因は"),("V","is","である"),("M","usually","たいてい"),
                ("C","not a lack of willpower but a first step &lt;that is too big&gt;.","意志の力の欠如ではなく、大きすぎる最初の一歩")],
     "note":"▶ <b>R3｜not A but B＝Bこそ核心</b>。<b>R11</b>｜that is too big＝関係詞が step を後ろから説明。＝<b>下線部(1)＝問2</b>。"},
    {"chunks": [("接","If","もし〜なら"),("S","the first step","最初の一歩が"),("V","asks for","要求する"),
                ("O","an hour of effort,","1時間の努力を"),
                ("S","a single hard day","たった一日のつらい日が"),("V","can break","断ち切りうる"),
                ("O","the chain.","（継続の）鎖を")],
     "note":"▶ <b>R6｜If＝条件→因果</b>。ask for＝「〜を要求する」。＝問7⑥の根拠。"},
    {"chunks": [("接","If","もし〜なら"),("S","it","それが"),("V","asks for","要求する（だけ）なら"),
                ("O","five minutes,","5分を"),
                ("S","almost nothing","ほとんど何も〜ない"),("V","can stop","止められない"),("O","us.","私たちを")],
     "note":"▶ 前文と対句（1時間⇔5分）。almost nothing＝準否定の主語＝「ほとんど何も〜ない」。"},
    {"chunks": [("S","We","私たちは"),("V","do not need","必要としない"),("O","a stronger will;","より強い意志を"),
                ("S","we","私たちは"),("V","need","必要とする"),("O","a smaller beginning.","より小さな始まりを")],
     "note":"▶ セミコロンで〈not A；B〉の対比を並置（<b>R3</b>の変奏）。核心の言い換え＝「強い意志より小さな始まり」。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：目標は大きく、入口は小さく",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも〜ない"),("V","means","意味しない"),
                ("O","[that we should shrink our dreams].","夢を縮めるべきだとは")],
     "note":"▶ <b>R5｜None of this＝第6段までの主張全体</b>を受ける。<b>R9注意</b>：問7⑤・問6②はこの文に反する。shrink＝「縮める」。"},
    {"chunks": [("V","Aim","狙え"),("M","as high as you like","好きなだけ高く"),
                ("-","&mdash; a distant university, a foreign language, a healthier body.","——遠くの大学、外国語、より健康な体")],
     "note":"▶ 命令文。ダッシュ以下＝「高い目標」の具体例の列挙（<b>R4</b>）。"},
    {"chunks": [("S","The advice","その助言は"),("V","is","である"),("C","simpler and kinder:","もっと単純で優しいもの"),
                ("V","keep","保て"),("O","the goal","目標を"),("C","large","大きく"),
                ("接","and","そして"),("O","the entrance","入口を"),("C","small.","小さく")],
     "note":"▶ <b>R8｜コロン(:)＝助言の中身の提示</b>。keep O C＝「OをCに保つ」が二組並列。＝<b>下線部(2)＝問3</b>。"},
    {"chunks": [("S","A door of five minutes","5分の扉は"),("V","is","である"),
                ("C","one &lt;that we can open every single day&gt;.","一日も欠かさず開けられる扉")],
     "note":"▶ one＝a door の代用。<b>R11｜関係詞</b>が one を後ろから説明。every single day＝every の強調形。"},
    {"chunks": [("接","And","そして"),("S","small habits, &lt;repeated daily&gt;,","毎日繰り返される小さな習慣は"),
                ("V","will carry","運んでいく"),("O","us","私たちを"),
                ("M","further (than grand resolutions ever do).","壮大な決意がそうする以上に遠くへ")],
     "note":"▶ <b>R11｜過去分詞 repeated daily</b> が habits を修飾。比較級 further than … <b>do</b>（代動詞＝carry us）。＝<b>下線部(3)＝問5</b>。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=4文/第2段=4文/第3段=4文/第4段=4文/第5段=5文/第6段=5文/第7段=5文)
SVOC_LOGIC = {
    (1, 4): "対比",                                   # Yet→研究の反論(=空所A)
    (2, 1): "譲歩", (2, 3): "譲歩",                    # It is true / エネルギーは本物
    (3, 1): "対比", (3, 2): "具体例", (3, 3): "対比", (3, 4): "主張",
    (4, 1): "具体例", (4, 2): "譲歩", (4, 3): "対比", (4, 4): "主張",
    (5, 1): "主張", (5, 2): "因果", (5, 3): "因果", (5, 4): "因果", (5, 5): "主張",
    (6, 1): "主張", (6, 2): "主張", (6, 3): "因果", (6, 4): "因果", (6, 5): "主張",
    (7, 1): "譲歩", (7, 2): "具体例", (7, 3): "主張", (7, 4): "因果", (7, 5): "主張",
}
