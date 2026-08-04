# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.05 — 単一ソース (基礎編)
テーマ: Teaching Others Is Learning Twice (人に教えることは、二度学ぶこと)
基礎レベル（偏差値55〜60 / The Rules 1〜2 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "05",
    "level": "基礎レベル",
    "level_sub": "偏差値55〜60 / The Rules 1〜2 相当",
    "theme_ja": "人に教えることは、二度学ぶこと",
    "theme_en": "Teaching Others Is Learning Twice",
    "minutes": 15,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'When a friend says, "Can you teach me this?", many students feel a quiet alarm. '
        'Time spent teaching someone else looks like time taken away from your own study. '
        'Every minute you give seems to be a minute you lose. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, this common belief overlooks one '
        'important fact. Explaining what you know may be one of the most powerful ways to '
        'learn it again.'),
    (2, 'It is true that exam preparation is a race against time. You have your own weak '
        'subjects, your own homework, and your own deadlines. Wanting to protect your study '
        'hours is completely natural. Nobody should feel guilty for saying, "Sorry, not '
        'today." In this sense, the worry about losing time is easy to understand.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, something surprising happens when you '
        'actually start to explain. Knowledge that felt solid in your head suddenly becomes '
        'shaky. <u>The feeling of "I understand this" often breaks down the moment we try to '
        'put it into words.<sup>(1)</sup></u> You search for a clear example and find none, '
        'or you reach a step you cannot justify. In this way, teaching works as a severe test '
        'of your own understanding. It shows you exactly where the holes are.'),
    (4, 'Consider a formula in mathematics. Using it correctly and explaining why it works '
        'are two different skills. Many students can solve a problem with the formula in '
        'seconds. Far fewer can tell a confused friend, in plain words, what the formula is '
        'really doing. If you get stuck in the middle of your explanation, do not feel '
        'ashamed. That stuck point is a map of your own weakness. It marks the exact place '
        'where your understanding is thin.'),
    (5, 'There is another gift here. Research on learning suggests that expecting to teach '
        'changes how we study. When you read a page believing you will explain it to '
        'someone, your brain starts to organize the information. You look for the main '
        'point, connect ideas, and prepare simple examples. Because of this preparation, the '
        'material goes into your memory in a deeper, more ordered form. You learn '
        'differently, and often better, before you have said a single word.'),
    (6, 'This is why helping a classmate deserves a better name than "lost time." '
        '<u>Teaching is not a one-way favor to the person in front of you, but a second '
        'chance to learn for yourself.<sup>(2)</sup></u> The first learning happens when you '
        'meet the material. The second happens when you rebuild it in your own words, for '
        'somebody else\'s eyes.'),
    (7, 'This does not mean, of course, that you should put off all your own study to teach '
        'others. Your time is limited, and balance matters. The point is smaller and more '
        'practical. When a friend is lost, <u>a five-minute explanation can be the best '
        'shortcut for both of you.<sup>(3)</sup></u> Your friend gets a way forward, and you '
        'get a test, a map, and a deeper memory. To teach is to learn twice.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋め、下線・タグは除去)
PASSAGE_PLAIN = (
    'When a friend says, "Can you teach me this?", many students feel a quiet alarm. Time '
    'spent teaching someone else looks like time taken away from your own study. Every '
    'minute you give seems to be a minute you lose. Yet, this common belief overlooks one '
    'important fact. Explaining what you know may be one of the most powerful ways to learn '
    'it again. '
    'It is true that exam preparation is a race against time. You have your own weak '
    'subjects, your own homework, and your own deadlines. Wanting to protect your study '
    'hours is completely natural. Nobody should feel guilty for saying, "Sorry, not today." '
    'In this sense, the worry about losing time is easy to understand. '
    'However, something surprising happens when you actually start to explain. Knowledge '
    'that felt solid in your head suddenly becomes shaky. The feeling of "I understand '
    'this" often breaks down the moment we try to put it into words. You search for a clear '
    'example and find none, or you reach a step you cannot justify. In this way, teaching '
    'works as a severe test of your own understanding. It shows you exactly where the holes '
    'are. '
    'Consider a formula in mathematics. Using it correctly and explaining why it works are '
    'two different skills. Many students can solve a problem with the formula in seconds. '
    'Far fewer can tell a confused friend, in plain words, what the formula is really '
    'doing. If you get stuck in the middle of your explanation, do not feel ashamed. That '
    'stuck point is a map of your own weakness. It marks the exact place where your '
    'understanding is thin. '
    'There is another gift here. Research on learning suggests that expecting to teach '
    'changes how we study. When you read a page believing you will explain it to someone, '
    'your brain starts to organize the information. You look for the main point, connect '
    'ideas, and prepare simple examples. Because of this preparation, the material goes '
    'into your memory in a deeper, more ordered form. You learn differently, and often '
    'better, before you have said a single word. '
    'This is why helping a classmate deserves a better name than "lost time." Teaching is '
    'not a one-way favor to the person in front of you, but a second chance to learn for '
    "yourself. The first learning happens when you meet the material. The second happens "
    "when you rebuild it in your own words, for somebody else's eyes. "
    'This does not mean, of course, that you should put off all your own study to teach '
    'others. '
    'Your time is limited, and balance matters. The point is smaller and more practical. '
    'When a friend is lost, a five-minute explanation can be the best shortcut for both of '
    'you. Your friend gets a way forward, and you get a test, a map, and a deeper memory. '
    'To teach is to learn twice.'
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Yet &nbsp; ② Therefore &nbsp; ③ For example &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① As a result &nbsp; ② For instance &nbsp; ③ Similarly &nbsp; ④ However",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(2) <span class='en'>Teaching is not a one-way favor to the person in "
             "front of you, but a second chance to learn for yourself.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) について、「わかった」という感覚がことばにしようとした瞬間に崩れる、とは"
             "どういうことか。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で述べられている「数学の公式」の例の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 公式を正しく使える生徒は、そのしくみも当然すらすらと説明できると述べられている。",
         "② 公式を正しく使えることと、なぜ効くのかを平易に説明できることは別の技能だと述べられている。",
         "③ 公式のしくみを人に説明できる生徒の方が、問題そのものも速く解けると述べられている。",
         "④ 公式の説明の途中で詰まることは、恥ずかしい失敗として避けるべきだと述べられている。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>a five-minute explanation can be the best shortcut "
             "for both of you</span> について、短い説明が「教える側」にとっても近道になるのはなぜか。"
             "本文全体をふまえ、教えることの働きを二つ挙げて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 受験生は自分の勉強をすべて後回しにしてでも、できるだけ多くの時間を友人に教えるために使うべきだ。",
         "② 教えることは教わる側だけに利益がある行為なので、時間に余裕のある人だけが引き受けるべきものだ。",
         "③ 教えることは一方的な親切ではなく自分にとって二度目の学びであり、短い説明が双方の近道になりうる。",
         "④ 「わかったつもり」を防ぐには、人に教えるよりも一人で問題を繰り返し解く方がはるかに効果的だ。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 友だちに教える時間は自分の勉強時間の損失だ、と感じる生徒は少なくない。",
         "② 頭の中で確かだと感じられた理解が、ことばにした瞬間に崩れることは決してない。",
         "③ 誰かに説明するつもりで読むだけで、頭は要点を探し、情報を整理し始める。",
         "④ 教えることは、目の前の相手だけが得をする一方的な親切だと筆者は述べている。",
         "⑤ 筆者は、自分の勉強を完全に後回しにしてでも他人に教えるべきだと主張している。",
         "⑥ 説明の途中で詰まった場所は、自分の理解の薄い場所を示す弱点の地図になる。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ① Yet　　B ＝ ④ However",
     "exp": "A：「教える時間＝自分の勉強の損」という通念に対し、「この思い込みは重要な事実を見落と"
            "している」と筆者が<b>反論</b>する流れ。逆接 → Yet。Therefore（因果）・For example（例示）・"
            "In addition（追加）は不可。<br>"
            "B：第2段「確かに時間を守りたい気持ちは自然（＝譲歩）」に対し、第3段は「だが説明を始めた"
            "瞬間に驚くことが起こる」と主張へ<b>転換</b>する。逆接 → However。As a result（因果）・"
            "For instance（例示）・Similarly（類比）は流れに合わない。 〔<b>解法ルール R7</b>／"
            "<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "②",
     "exp": "第4段「Using it correctly and explaining why it works are two different skills」＝"
            "公式を正しく使うことと、なぜ効くのかを説明することは別の技能。①は本文と逆（説明できる"
            "生徒は Far fewer＝はるかに少ない）。③は本文にない因果（説明できる人が速く解けるとは"
            "述べていない）。④も逆（詰まっても do not feel ashamed＝恥じるな、詰まった場所こそ弱点の"
            "地図）。 〔<b>解法ルール R9</b>／<b>読解ルール R4</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "③",
     "exp": "第6段「Teaching is not a one-way favor … but a second chance to learn for "
            "yourself」＋第7段「a five-minute explanation can be the best shortcut for both of "
            "you」と一致。①は第7段「This does not mean … that you should put off all your own "
            "study」に反する言い過ぎ。②は第6段の not a one-way favor（一方的な親切ではない）と正反対。"
            "④は本文にない比較（一人で解く方が効果的とは述べていない）。 〔<b>読解ルール R3</b>／"
            "<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・③・⑥",
     "exp": "②×：第3段「The feeling of 'I understand this' often breaks down」＝しばしば崩れる、"
            "と述べており「決して崩れない」は正反対＋言い過ぎ。④×：第6段「not a one-way favor」＝"
            "一方的な親切<b>ではない</b>、と明確に否定。⑤×：第7段「This does not mean … that you "
            "should put off all your own study」＝「完全に後回しにしてでも」は言い過ぎで×。 "
            "〔<b>解法ルール R9</b>：言い換えの見抜き＋「決して／完全に」型の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(2)和訳",
     "model": "教えることは、目の前にいる相手への一方的な親切ではなく、自分自身にとっての、"
              "もう一度学ぶ二度目の機会なのである。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「AではなくB」の対比を訳出／②a one-way favor "
               "to the person in front of you＝目の前の人への一方的な親切（好意）／③a second chance "
               "to learn for yourself＝自分自身のための、二度目の学びの機会。 〔<b>読解ルール R3</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "頭の中では確かに理解できていると感じていても、実際にことばにして説明しようとすると、"
              "明確な例が一つも見つからなかったり、理由を説明できない箇所に行き当たったりして、"
              "その「わかった」という感覚が実は確かなものでなかったと露呈する、ということ。",
     "points": "▶<b>採点要素</b>：①「わかったつもり」＝頭の中では確か（solid）に感じられる理解／"
               "②説明（ことば化）しようとした瞬間にそれがぐらつく（shaky）／③例が出ない・理由が"
               "言えない、といった理解の穴が露呈する（第3段）。 〔<b>解法ルール R8</b>／"
               "<b>読解ルール R1</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①説明しようとして詰まった場所が自分の理解の穴＝弱点のありかを正確に教えてくれる、"
              "自分の理解の厳しいテストとして働くから。②誰かに説明するつもりで学ぶと、頭が要点を"
              "探して情報を整理し始め、内容がより深く順序立った形で記憶に残るから。",
     "points": "▶<b>採点要素</b>：本文全体から教えることの「働き」を二つ取り出す。①<b>理解のテスト</b>"
               "（第3〜4段：severe test ／ a map of your own weakness）／②<b>教えるつもり効果</b>"
               "（第5段：organize the information → deeper, more ordered form）。各5点。 "
               "〔<b>読解ルール R4・R6</b>／<b>解法ルール R8</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（Yet→通念への反論）・空所B（However→第3段で主張へ転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that exam preparation is a race against time」→ 第3段 However で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(2) not a one-way favor but a second chance to learn＝「二度目の学び」が核心。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段の数学の公式の例は「説明＝理解のテスト」という第3段の抽象の具体例。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "第6段 This is why … ／ 第7段 this does not mean、a test, a map, and a deeper memory の中身。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第5段 Because of this preparation …、第6段 This is why …。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。テスト＝弱点の地図（第3〜4段）、整理→深い記憶（第5段）の言い換えを利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。②の「決して崩れない」・⑤の「完全に後回しにしてでも」は典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "Knowledge &lt;that felt solid in your head&gt;、time &lt;taken away from your own study&gt; 型。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「友だちに教える時間＝自分の勉強時間の損」を提示。→ <b>Yet（R1）</b>：この思い込みは"
             "重要な事実を見落としている——説明は「もう一度学ぶ」最強の方法かもしれない。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに受験は時間との競争。自分の課題・時間を守りたい"
             "気持ちは自然。＝通念の一部は認める。"},
    {"arrow": "◀ However 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "説明を始めた瞬間、<b>「わかったつもり」は崩れる</b>。例が出ない・理由が言えない。"
             "教えることは自分の理解の<b>厳しいテスト</b>＝穴のありかを正確に示す。"},
    {"arrow": "↓　具体化（R4）＝働き①"},
    {"role": "働き①", "para": "¶4", "kind": "reason",
     "text": "<b>数学の公式の例</b>：正しく使えることと、なぜ効くのかを平易に説明できることは"
             "別の技能。説明で<b>詰まった場所＝自分の弱点の地図</b>。"},
    {"arrow": "↓　働き②"},
    {"role": "働き②", "para": "¶5", "kind": "reason",
     "text": "<b>教えるつもり効果</b>：誰かに説明するつもりで読むだけで、頭は要点を探し情報を"
             "整理し始める。<b>Because of this preparation（R6）</b>→ 深く順序立った記憶。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "教えることは<b>一方的な親切ではなく、二度目の学び</b>＝<b>not a one-way favor but a "
             "second chance to learn（R3）</b>。一度目＝内容に出会うとき／二度目＝自分のことばで"
             "組み立て直すとき。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：自分の勉強を<b>全部後回しにせよという話ではない</b>。友だちが迷って"
             "いるとき、5分の説明が<b>双方の最良の近道</b>になりうる。教えることは二度学ぶこと。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 「教える時間」への二つの見方",
     "caption": "同じ5分でも、<b>損</b>とみなせば「わかったつもり」のまま進み、<b>二度目の学び</b>と"
                "みなせば、穴の発見と深い記憶が手に入る。筆者は後者の見方を勧める。",
     "para": "→ 第1・3・7段"},
    {"id": "fig2", "title": "図2 ｜ 教えることの二つの働き",
     "caption": "教えることの仕事は二つ。①<b>理解のテスト</b>＝説明で詰まった場所が弱点の地図になる"
                "（第3〜4段）、②<b>教えるつもり効果</b>＝頭が情報を整理し始める（第5段）。"
                "問5はこの二つを答える。",
     "para": "→ 第3〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 一方的な親切ではなく「二度目の学び」",
     "caption": "問題は「教えるか断るか」ではなく<b>とらえ方</b>。教えることは相手だけの得ではなく、"
                "<b>自分がもう一度学ぶ機会</b>——ただし勉強を全部後回しにせよという話ではない。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "友だちに「これ、教えてくれない？」と言われたとき、多くの生徒は心の中で小さな警報を感じる。"
        "他人に教えることに使われる時間は、自分の勉強から奪われた時間のように見えるのだ。自分が差し"
        "出す一分一分が、失われる一分であるように思える。<b>しかし</b>、このよくある思い込みは、"
        "一つの重要な事実を見落としている。自分の知っていることを説明するのは、それをもう一度学ぶ"
        "最も強力な方法の一つかもしれないのである。"),
    (2, "確かに、受験勉強は時間との競争である。あなたには自分の苦手科目があり、自分の宿題があり、"
        "自分の締め切りがある。自分の勉強時間を守りたいと思うのは、まったく自然なことだ。「ごめん、"
        "今日は無理」と言うことに、罪悪感を覚える必要は誰にもない。この意味で、時間を失うことへの"
        "心配は理解しやすいものである。"),
    (3, "<b>しかし</b>、実際に説明を始めてみると、驚くべきことが起こる。頭の中では確かだと感じられた"
        "知識が、突然ぐらつき始めるのだ。「これはわかった」という感覚は、それをことばにしようとした"
        "瞬間に、しばしば崩れてしまう。明確な例を探しても一つも見つからなかったり、自分では理由を"
        "説明できない段階に行き当たったりする。このようにして、教えることは自分自身の理解の厳しいテストとして"
        "働く。それは、穴がどこにあるのかを正確に示してくれるのである。"),
    (4, "数学の公式を考えてみてほしい。それを正しく使うことと、なぜそれが効くのかを説明することは、"
        "二つの別々の技能である。多くの生徒は、その公式を使えば数秒で問題を解ける。しかし、困って"
        "いる友だちに、その公式が実際には何をしているのかを平易なことばで伝えられる生徒は、はるかに"
        "少ない。説明の途中で行き詰まっても、恥じることはない。その詰まった場所こそ、自分自身の弱点"
        "の地図なのだ。それは、あなたの理解が薄い、まさにその場所を示してくれる。"),
    (5, "ここには、もう一つの贈り物がある。学習に関する研究は、教えることを見込むと勉強の仕方が変わる"
        "ことを示唆している。誰かに説明するつもりでページを読むと、あなたの頭はその情報を整理し始める"
        "のだ。要点を探し、考えをつなぎ、簡単な例を準備する。この準備のおかげで、学んだ内容は、より"
        "深く、より順序立った形で記憶に入っていく。一言も口にする前に、あなたはいつもと違うやり方で"
        "——そしてしばしば、よりよく——学んでいるのである。"),
    (6, "だからこそ、クラスメイトを助けることには、「失われた時間」よりもよい名前がふさわしい。"
        "<b>教えることは、目の前にいる相手への一方的な親切ではなく、自分自身にとっての、もう一度学ぶ"
        "二度目の機会なのである。</b>一度目の学びは、その内容に出会うときに起こる。二度目の学びは、"
        "他の誰かに見せるために、それを自分のことばで組み立て直すときに起こるのだ。"),
    (7, "もちろん、以上のことは、他人に教えるために自分の勉強を全部後回しにすべきだ、という意味では"
        "ない。あなたの時間は限られているし、バランスが大切だ。要点はもっとささやかで、実際的なもの"
        "である。友だちが行き詰まっているとき、<b>5分の説明が、二人にとっての最良の近道になりうる</b>"
        "のだ。友だちは前に進む道を手に入れ、あなたはテストと、地図と、より深い記憶を手に入れる。"
        "教えることは、二度学ぶことなのである。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("alarm", "警報、（はっとする）不安"),
    ("take A away from B", "AをBから奪う・取り上げる"),
    ("overlook", "〜を見落とす"),
    ("a race against time", "時間との競争"),
    ("deadline", "締め切り"),
    ("feel guilty", "罪悪感を覚える"),
    ("in this sense", "この意味で"),
    ("solid", "確かな、しっかりした"),
    ("shaky", "ぐらつく、不確かな"),
    ("break down", "崩れる、壊れる"),
    ("put ~ into words", "〜をことばにする"),
    ("justify", "〜の正当な理由を示す"),
    ("work as ~", "〜として働く・機能する"),
    ("severe", "厳しい"),
    ("in plain words", "平易なことばで"),
    ("get stuck", "行き詰まる、詰まる"),
    ("ashamed", "恥じて"),
    ("organize", "整理する、体系立てる"),
    ("ordered", "順序立った、整った"),
    ("deserve", "〜に値する"),
    ("one-way", "一方通行の、一方的な"),
    ("favor", "親切な行為、好意"),
    ("put off ~", "〜を後回しにする、延期する"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 問題提起：「教える時間＝損」という通念と、その反転",
  "sentences": [
    {"chunks": [("M",'(When a friend says, "Can you teach me this?"),','友だちに「これ教えて」と言われたとき'),
                ("S","many students","多くの生徒は"),("V","feel","感じる"),("O","a quiet alarm.","静かな警報（不安）を")],
     "note":"▶ When SV＝副詞節「〜するとき」。a quiet alarm＝比喩（心の中で鳴る小さな警報）。通念の提示が始まる。"},
    {"chunks": [("S","Time &lt;spent teaching someone else&gt;","他人に教えることに使われた時間は"),
                ("V","looks like","〜のように見える"),
                ("C","time &lt;taken away from your own study&gt;.","自分の勉強から奪われた時間の")],
     "note":"▶ <b>R11｜過去分詞の後置修飾</b>：spent doing ＝「〜に使われた」、taken away from ＝「〜から奪われた」。look like＋名詞。"},
    {"chunks": [("S","Every minute &lt;(that) you give&gt;","あなたが与える一分一分は"),
                ("V","seems to be","〜であるように思える"),
                ("C","a minute &lt;(that) you lose&gt;.","あなたが失う一分で")],
     "note":"▶ 関係代名詞の省略が二か所（give／lose の目的語が先行詞）。seem to be＝「〜であるように思える」。"},
    {"chunks": [("接","Yet,","しかし"),("S","this common belief","このよくある思い込みは"),
                ("V","overlooks","見落としている"),("O","one important fact.","一つの重要な事実を")],
     "note":"▶ <b>R1｜逆接 Yet の直後が筆者の主張</b>（＝空所A）。this common belief＝第1段前半の通念を指す（R5）。overlook＝「見落とす」。"},
    {"chunks": [("S","Explaining [what you know]","自分の知っていることを説明することは"),
                ("V","may be","かもしれない"),
                ("C","one of the most powerful ways &lt;to learn it again&gt;.","それをもう一度学ぶ最も強力な方法の一つ")],
     "note":"▶ 動名詞 Explaining …＝主語。what＝関係代名詞（名詞節）。to learn …＝ways を修飾する不定詞。タイトルの予告。"},
  ]},
 {"head": "第2段 — 譲歩：確かに受験は時間との競争（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当だ"),
                ("-","[that exam preparation is a race against time].","受験勉強が時間との競争だということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。形式主語 It＝真主語 that 節。後の逆接（第3段 However）が本命。"},
    {"chunks": [("S","You","あなたには"),("V","have","ある"),
                ("O","your own weak subjects, your own homework, and your own deadlines.","自分の苦手科目、自分の宿題、自分の締め切りが")],
     "note":"▶ A, B, and C の並列。your own の繰り返しが「自分自身の課題」を強調する。"},
    {"chunks": [("S","Wanting to protect your study hours","自分の勉強時間を守りたいと思うことは"),
                ("V","is","である"),("C","completely natural.","まったく自然")],
     "note":"▶ 動名詞 Wanting …＝主語（want to do を名詞化した形）。譲歩の中心文。"},
    {"chunks": [("S","Nobody","誰も〜ない"),("V","should feel","感じるべきではない"),("C","guilty","罪悪感を"),
                ("M",'(for saying, "Sorry, not today.")','「ごめん、今日は無理」と言うことに対して')],
     "note":"▶ feel＋形容詞＝「〜と感じる」。Nobody should …＝「誰も〜する必要はない」。for doing＝理由・対象。"},
    {"chunks": [("M","(In this sense),","この意味で"),("S","the worry &lt;about losing time&gt;","時間を失うことへの心配は"),
                ("V","is","である"),("C","easy to understand.","理解しやすい")],
     "note":"▶ be easy to do＝「〜しやすい」（understand の目的語が主語 the worry に上がった形）。譲歩の締め。"},
  ]},
 {"head": "第3段 — 主張の転換：説明した瞬間「わかったつもり」は崩れる（However）",
  "sentences": [
    {"chunks": [("接","However,","しかし"),("S","something surprising","驚くべきことが"),
                ("V","happens","起こる"),("M","(when you actually start to explain).","実際に説明を始めると")],
     "note":"▶ <b>R1｜However＝逆接でここが主張転換点</b>（＝空所B）。something surprising＝-thing＋形容詞の後置。"},
    {"chunks": [("S","Knowledge &lt;that felt solid in your head&gt;","頭の中では確かに感じられた知識が"),
                ("M","suddenly","突然"),("V","becomes","なる"),("C","shaky.","ぐらぐらに")],
     "note":"▶ <b>R11｜関係代名詞 that</b> が Knowledge を後ろから修飾。become＋形容詞＝「〜になる」。solid⇔shaky の対比。"},
    {"chunks": [("S",'The feeling &lt;of "I understand this"&gt;','「これはわかった」という感覚は'),
                ("M","often","しばしば"),("V","breaks down","崩れる"),
                ("M","(the moment we try to put it into words).","それをことばにしようとした瞬間に")],
     "note":"▶ <b>The moment SV</b>＝接続詞的「〜する瞬間に」。put A into words＝「Aをことばにする」。＝<b>下線部(1)＝問3</b>。"},
    {"chunks": [("S","You","あなたは"),("V","search for","探す"),("O","a clear example","明確な例を"),
                ("接","and","そして"),("V","find","見つける"),("O","none,","何も（一つも見つからない）"),
                ("接","or","あるいは"),("S","you","あなたは"),("V","reach","たどり着く"),
                ("O","a step &lt;(that) you cannot justify&gt;.","自分では理由を説明できない段階に")],
     "note":"▶ none＝no example（一つも〜ない）。or で「崩れる」の具体場面を二つ並列。a step の後は関係代名詞の省略"
            "（justify の目的語が先行詞）。justify＝「正当な理由を示す」。"},
    {"chunks": [("M","(In this way),","このようにして"),("S","teaching","教えることは"),
                ("V","works as","〜として働く"),
                ("C","a severe test &lt;of your own understanding&gt;.","自分自身の理解の厳しいテスト")],
     "note":"▶ work as A＝「Aとして働く」。第3段の主張の核＝<b>教えること＝理解のテスト</b>。"},
    {"chunks": [("S","It","それは"),("V","shows","示す"),("O","you","あなたに"),
                ("O","[exactly where the holes are].","穴がどこにあるのかを正確に")],
     "note":"▶ show O1 O2（O1＝you／O2＝where 節）。where …＝間接疑問（名詞節）。the holes＝理解の穴。"},
  ]},
 {"head": "第4段 — 働き①の具体化：公式を「使える」と「説明できる」は別（抽象→具体）",
  "sentences": [
    {"chunks": [("V","Consider","考えてみよう"),("O","a formula (in mathematics).","数学の公式を")],
     "note":"▶ 命令文。<b>R4｜ここから「説明＝テスト」という抽象の具体例</b>が始まる。"},
    {"chunks": [("S","Using it correctly and explaining [why it works]","それを正しく使うことと、なぜそれが効くのかを説明することは"),
                ("V","are","である"),("C","two different skills.","二つの別々の技能")],
     "note":"▶ 動名詞主語の並列（Using … and explaining …）。why it works＝間接疑問（名詞節）。＝<b>問4の根拠</b>。"},
    {"chunks": [("S","Many students","多くの生徒は"),("V","can solve","解ける"),("O","a problem","問題を"),
                ("M","(with the formula) (in seconds).","その公式を使って数秒で")],
     "note":"▶ with＝道具「〜を使って」。in seconds＝「数秒で」。「使える」側の描写。"},
    {"chunks": [("S","Far fewer","はるかに少数の生徒しか〜ない"),("V","can tell","伝えられる"),
                ("O","a confused friend,","困っている友だちに"),("M","(in plain words),","平易なことばで"),
                ("O","[what the formula is really doing].","その公式が実際には何をしているのかを")],
     "note":"▶ Far fewer (students)＝名詞の省略。tell O1 O2。what …＝間接疑問。「使える≠説明できる」の対比。"},
    {"chunks": [("M","(If you get stuck in the middle of your explanation),","説明の途中で行き詰まっても"),
                ("V","do not feel","感じるな"),("C","ashamed.","恥ずかしいと")],
     "note":"▶ 否定の命令文。get stuck＝「行き詰まる」。詰まること＝失敗ではない、という転換。"},
    {"chunks": [("S","That stuck point","その詰まった場所こそ"),("V","is","である"),
                ("C","a map &lt;of your own weakness&gt;.","自分自身の弱点の地図")],
     "note":"▶ <b>R5｜That＝直前の「説明の途中で詰まった場所」</b>を指す。map＝比喩（弱点のありかを示すもの）。"},
    {"chunks": [("S","It","それは"),("V","marks","示す"),
                ("O","the exact place &lt;where your understanding is thin&gt;.","あなたの理解が薄い、まさにその場所を")],
     "note":"▶ <b>R11｜関係副詞 where</b> が place を後ろから修飾。thin＝「（理解が）薄い」。"},
  ]},
 {"head": "第5段 — 働き②：教えるつもりで学ぶと、頭が整理を始める",
  "sentences": [
    {"chunks": [("M","There","（there is 構文）"),("V","is","ある"),("S","another gift","もう一つの贈り物が"),
                ("M","here.","ここには")],
     "note":"▶ There is S＝「Sがある」。another＝<b>追加の合図</b>（働き①に続く働き②の予告）。"},
    {"chunks": [("S","Research &lt;on learning&gt;","学習に関する研究は"),("V","suggests","示唆している"),
                ("O","[that expecting to teach changes how we study].","教えることを見込むと勉強の仕方が変わる、ということを")],
     "note":"▶ <b>R6｜Research suggests that …</b>＝一般的知見の提示。that 節内は expecting to teach（動名詞主語）＋changes＋how 節（間接疑問）。"},
    {"chunks": [("M","(When you read a page believing you will explain it to someone),","誰かに説明するつもりでページを読むと"),
                ("S","your brain","あなたの頭は"),("V","starts to organize","整理し始める"),
                ("O","the information.","その情報を")],
     "note":"▶ believing …＝分詞構文（付帯状況）。believe (that) SV の that 省略。start to do＝「〜し始める」。"},
    {"chunks": [("S","You","あなたは"),("V","look for","探し"),("O","the main point,","要点を"),
                ("V","connect","つなぎ"),("O","ideas,","考えを"),
                ("接","and","そして"),("V","prepare","準備する"),("O","simple examples.","簡単な例を")],
     "note":"▶ 三つの動詞句の並列（look for ／ connect ／ prepare）。「整理」の中身を具体的に列挙。"},
    {"chunks": [("M","(Because of this preparation),","この準備のおかげで"),("S","the material","学んだ内容は"),
                ("V","goes","入っていく"),("M","(into your memory)","記憶の中へ"),
                ("M","(in a deeper, more ordered form).","より深く、より順序立った形で")],
     "note":"▶ <b>R6｜Because of＋名詞＝因果</b>。this preparation＝前文の「探す・つなぐ・準備する」を指す（R5）。"},
    {"chunks": [("S","You","あなたは"),("V","learn","学ぶ"),
                ("M","differently, and often better,","違ったやり方で、そしてしばしばよりよく"),
                ("M","(before you have said a single word).","一言も口にする前に")],
     "note":"▶ before 節の現在完了＝「まだ一言も言っていない時点で（すでに学びが起きている）」。a single word＝強調の single。"},
  ]},
 {"head": "第6段 — 核心：一方的な親切ではなく、二度目の学び（not A but B）",
  "sentences": [
    {"chunks": [("S","This","これが"),("V","is","である"),
                ("C",'[why helping a classmate deserves a better name than "lost time."]','クラスメイトを助けることが「失われた時間」よりよい名前に値する理由')],
     "note":"▶ <b>This is why …</b>＝「これが〜の理由だ」（<b>R5・R6</b>：This＝第3〜5段の二つの働き）。deserve A＝「Aに値する」。"},
    {"chunks": [("S","Teaching","教えることは"),("V","is","である"),
                ("C","not a one-way favor &lt;to the person in front of you&gt;, but a second chance &lt;to learn&gt; (for yourself).","目の前の人への一方的な親切ではなく、自分自身のための、二度目の学びの機会")],
     "note":"▶ <b>R3｜not A but B＝Bの側が核心</b>。one-way favor（一方的な親切）を否定し、a second chance to learn と言い切る。＝<b>下線部(2)＝問2</b>。"},
    {"chunks": [("S","The first learning","一度目の学びは"),("V","happens","起こる"),
                ("M","(when you meet the material).","その内容に出会うときに")],
     "note":"▶ meet the material＝「教材・内容に（初めて）出会う」。first ⇔ second の対比が始まる。"},
    {"chunks": [("S","The second","二度目（の学び）は"),("V","happens","起こる"),
                ("M","(when you rebuild it in your own words, for somebody else's eyes).","他の誰かの目のために、それを自分のことばで組み立て直すときに")],
     "note":"▶ The second (learning)＝名詞の省略。rebuild＝「組み立て直す」。in your own words＝「自分のことばで」。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：5分の説明は双方の近道",
  "sentences": [
    {"chunks": [("S","This","以上のことは"),("V","does not mean,","意味しない"),("M","(of course),","もちろん"),
                ("O","[that you should put off all your own study to teach others].","他人に教えるために自分の勉強を全部後回しにすべきだ、とは")],
     "note":"▶ This does not mean that …＝譲歩つきの限定。This＝第3〜6段の内容全体（R5）。of course は挿入。<b>R9注意</b>：これが設問⑤「完全に後回しにしてでも」を否定する根拠。put off＝「後回しにする」。"},
    {"chunks": [("S","Your time","あなたの時間は"),("V","is","である"),("C","limited,","限られたもの"),
                ("接","and","そして"),("S","balance","バランスが"),("V","matters.","重要だ")],
     "note":"▶ matter＝動詞「重要である」。二つの短い SV の並列。"},
    {"chunks": [("S","The point","要点は"),("V","is","である"),
                ("C","smaller and more practical.","もっとささやかで実際的")],
     "note":"▶ 比較級の並列。「大げさな話ではない」と主張の射程を絞る。"},
    {"chunks": [("M","(When a friend is lost),","友だちが行き詰まっているときには"),
                ("S","a five-minute explanation","5分の説明が"),("V","can be","なりうる"),
                ("C","the best shortcut","最良の近道に"),("M","(for both of you).","あなたたち二人にとって")],
     "note":"▶ lost＝「道に迷った→わからなくなった」。can＝可能性「〜になりうる」。＝<b>下線部(3)＝問5</b>。"},
    {"chunks": [("S","Your friend","友だちは"),("V","gets","手に入れる"),("O","a way forward,","前に進む道を"),
                ("接","and","そして"),("S","you","あなたは"),("V","get","手に入れる"),
                ("O","a test, a map, and a deeper memory.","テストと、地図と、より深い記憶を")],
     "note":"▶ 二つの SVO の並列＝「双方の利益」。<b>R5｜三つの名詞の中身</b>：test＝理解のテスト（第3段）／map＝弱点の地図"
            "（第4段）／memory＝深い記憶（第5段）の言い換え。"},
    {"chunks": [("S","To teach","教えることは"),("V","is","である"),("C","to learn twice.","二度学ぶこと")],
     "note":"▶ 不定詞主語＋不定詞補語（To do is to do）。タイトルを回収する結論文。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=5文/第2段=5文/第3段=6文/第4段=7文/第5段=6文/第6段=4文/第7段=6文)
SVOC_LOGIC = {
    (1, 4): "対比", (1, 5): "主張",                  # s4 Yet→反論 / s5 最強の学び直し
    (2, 1): "譲歩", (2, 3): "譲歩", (2, 5): "譲歩",   # It is true / 自然だ / 心配は理解できる
    (3, 1): "対比", (3, 3): "主張", (3, 4): "具体例", (3, 5): "主張",  # However / 下線(1) / 例が出ない・理由が言えない / テスト
    (4, 1): "具体例", (4, 2): "主張", (4, 4): "対比", (4, 6): "主張",
    (5, 1): "追加", (5, 2): "因果", (5, 3): "因果", (5, 5): "因果", (5, 6): "主張",
    (6, 1): "因果", (6, 2): "主張", (6, 4): "対比",
    (7, 1): "譲歩", (7, 4): "主張", (7, 6): "主張",   # 譲歩 / 下線(3)＝近道 / To teach is to learn twice
}
