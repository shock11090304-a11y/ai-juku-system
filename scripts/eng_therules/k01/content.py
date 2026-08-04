# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.01 — 単一ソース (基礎編)
テーマ: Exercise Trains the Brain, Not Just the Body (運動は体だけでなく脳も鍛える)
基礎レベル（偏差値55〜60 / The Rules 1〜2 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "01",
    "level": "基礎レベル",
    "level_sub": "偏差値55〜60 / The Rules 1〜2 相当",
    "theme_ja": "運動は体だけでなく脳も鍛える",
    "theme_en": "Exercise Trains the Brain, Not Just the Body",
    "minutes": 15,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Ask a group of students what exercise is for, and most of them will talk about the '
        'body. Exercise builds muscles, burns energy, and keeps us in shape, they will say. '
        'For a student preparing for exams, it can even look like a luxury. Every minute spent '
        'on running or walking seems to be a minute stolen from the textbook. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, research on the brain suggests that this '
        'common view misses something important. Exercise, scientists say, trains the brain '
        'as well as the body.'),
    (2, 'It is true that the hours you spend at your desk matter. No one masters English '
        'words or math rules without sitting down and learning them. Steady practice, day '
        'after day, is still the base of success in any exam. If exercise really robbed '
        'students of that time, they would be right to avoid it.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span> the story does not end there. Right '
        'after you move your body, your brain is in a special state: <u>it is ready to '
        'learn.<sup>(1)</sup></u> Exercise sends more blood to the brain, and the mind wakes '
        'up. In this state, new information seems to enter the head more smoothly. In other '
        'words, the minutes after exercise are a golden time for study.'),
    (4, 'The exercise does not have to be long or hard. Research suggests that even a short '
        'walk can change the way we study. After walking for a few minutes, people often find '
        'it easier to focus on a task. What they learn in that state also tends to stay in '
        'their memory longer. A light walk, in short, may prepare the mind better than '
        'another cup of coffee.'),
    (5, 'Exercise helps students in a second way: it lifts their mood. When we move our '
        'bodies, feelings of worry grow lighter. Stress that has piled up during long hours '
        'of study slowly melts away. <u>This change gives us the power to return to our desks '
        'and try again.<sup>(2)</sup></u> A student who takes a short break to move often '
        'studies better afterward than one who never leaves the chair.'),
    (6, 'Seen in this way, exercise deserves a new place in student life. <u>It is not an '
        'enemy that steals your study time but a friend that makes each hour at your desk '
        'more valuable.<sup>(3)</sup></u> Time used for a little movement is not lost; it '
        'comes back with extra value. The real waste may be forcing a tired, cloudy head to '
        'stare at the same page.'),
    (7, 'Of course, this does not mean that you should spend hours on hard training. '
        'Exercise will not remove every difficulty in your studies, either. The point is '
        'much simpler than that. When your head feels heavy during a break, stand up and '
        'walk for about ten minutes. That small step is enough as an entrance to this new '
        'habit. Your brain, not just your body, will thank you for it.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Ask a group of students what exercise is for, and most of them will talk about the body. "
    "Exercise builds muscles, burns energy, and keeps us in shape, they will say. For a "
    "student preparing for exams, it can even look like a luxury. Every minute spent on "
    "running or walking seems to be a minute stolen from the textbook. However, research on "
    "the brain suggests that this common view misses something important. Exercise, "
    "scientists say, trains the brain as well as the body. "
    "It is true that the hours you spend at your desk matter. No one masters English words or "
    "math rules without sitting down and learning them. Steady practice, day after day, is "
    "still the base of success in any exam. If exercise really robbed students of that time, "
    "they would be right to avoid it. "
    "Yet the story does not end there. Right after you move your body, your brain is in a "
    "special state: it is ready to learn. Exercise sends more blood to the brain, and the "
    "mind wakes up. In this state, new information seems to enter the head more smoothly. In "
    "other words, the minutes after exercise are a golden time for study. "
    "The exercise does not have to be long or hard. Research suggests that even a short walk "
    "can change the way we study. After walking for a few minutes, people often find it "
    "easier to focus on a task. What they learn in that state also tends to stay in their "
    "memory longer. A light walk, in short, may prepare the mind better than another cup of "
    "coffee. "
    "Exercise helps students in a second way: it lifts their mood. When we move our bodies, "
    "feelings of worry grow lighter. Stress that has piled up during long hours of study "
    "slowly melts away. This change gives us the power to return to our desks and try again. "
    "A student who takes a short break to move often studies better afterward than one who "
    "never leaves the chair. "
    "Seen in this way, exercise deserves a new place in student life. It is not an enemy that "
    "steals your study time but a friend that makes each hour at your desk more valuable. "
    "Time used for a little movement is not lost; it comes back with extra value. The real "
    "waste may be forcing a tired, cloudy head to stare at the same page. "
    "Of course, this does not mean that you should spend hours on hard training. Exercise "
    "will not remove every difficulty in your studies, either. The point is much simpler "
    "than that. When your head feels heavy during a break, stand up and walk for about ten "
    "minutes. That small step is enough as an entrance to this new habit. Your brain, not "
    "just your body, will thank you for it."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Therefore &nbsp; ② However &nbsp; ③ For example &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① Similarly &nbsp; ② For instance &nbsp; ③ As a result &nbsp; ④ Yet",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(3) <span class='en'>It is not an enemy that steals your study time but a "
             "friend that makes each hour at your desk more valuable.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) について、運動の直後に脳が「学ぶ準備ができている（<span class='en'>it is "
             "ready to learn</span>）」とはどういうことか。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で述べられている「短い散歩」の効果として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 集中力が高まるのは、一時間以上の激しい運動を行った直後に限られる。",
         "② 散歩のあとには、学んだ内容がかえって記憶から抜けやすくなる。",
         "③ 短い散歩のあとの方が課題に集中しやすく、学んだことが記憶に残りやすい。",
         "④ 散歩には体力を高める効果があるが、集中力や記憶とは関係がない。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(2) <span class='en'>This change gives us the power to return to our desks "
             "and try again.</span> の <span class='en'>This change</span>（この変化）とはどのような"
             "変化か。また、その変化は勉強にどのように役立つと筆者は述べているか。本文に即して"
             "日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 受験期には、勉強時間を削ってでも毎日長時間の運動を行うべきである。",
         "② 運動は勉強の敵ではなく味方であり、休憩に短い運動を取り入れる価値がある。",
         "③ 運動の価値はあくまで体を鍛えることにあり、脳への効果は期待できない。",
         "④ 運動には気分を明るくする効果しかなく、集中力や記憶力とは関係がない。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 試験を控えた生徒には、運動が勉強時間を奪うぜいたくのように見えることがある。",
         "② 筆者は、机に向かって勉強する時間はそれほど重要ではないと考えている。",
         "③ 運動の効果を得るためには、長くて激しい運動を行うことが必要である。",
         "④ 体を動かすと不安な気持ちが軽くなり、机に戻って勉強する力が回復する。",
         "⑤ 筆者は、休憩中に10分ほど歩くことを、この習慣の入口として勧めている。",
         "⑥ 運動さえすれば、勉強上の困難は完全になくなると筆者は述べている。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ② However　　B ＝ ④ Yet",
     "exp": "A：「運動＝体のため、勉強時間を奪うぜいたく」という通念に対し、脳の研究が「この見方は"
            "大切な何かを見落としている」と反論する流れ。<b>逆接</b>でつなぐ → However。"
            "Therefore（因果）・For example（例示）・In addition（追加）は不可。<br>"
            "B：第2段「確かに机の時間は大切（＝譲歩）」に対し、第3段は「だが話はそこで終わらない」と"
            "主張へ<b>転換</b>する。逆接 → Yet。Similarly（類比）・For instance（例示）・"
            "As a result（因果）は流れに合わない。 〔<b>解法ルール R7</b>／<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "③",
     "exp": "第4段「people often find it easier to focus on a task」＋「What they learn in that "
            "state also tends to stay in their memory longer」＝短い散歩のあとの方が集中しやすく、"
            "学んだことが記憶に残りやすい。①は「一時間以上・激しい」が本文と逆（第4段冒頭 does not "
            "have to be long or hard）。②は逆（記憶に長くとどまる）。④「関係がない」は本文にない。"
            " 〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "②",
     "exp": "第6段「not an enemy … but a friend（敵ではなく味方）」＋第7段「休憩に10分歩けば入口と"
            "して十分」と一致。①は第7段「何時間も激しいトレーニングをすべきだという意味ではない」に"
            "反する。③は本文と逆（運動は脳も鍛える）。④は「効果しかなく」が言い過ぎ（第4段で集中・"
            "記憶への効果を述べている）。 〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・④・⑤",
     "exp": "②×：第2段冒頭「It is true that the hours you spend at your desk matter（机で過ごす"
            "時間が重要なのは本当だ）」と認めている。③×：第4段「The exercise does not have to be "
            "long or hard」に反する。⑥×：第7段「Exercise will not remove every difficulty in your "
            "studies（あらゆる困難を取り除くわけではない）」に反する——「完全に」は典型的な"
            "<b>言い過ぎ</b>の引っかけ。 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(3)和訳",
     "model": "運動（それ）は、あなたの勉強時間を盗む敵ではなく、机に向かう一時間一時間をより価値ある"
              "ものにしてくれる味方（友）なのである。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「AではなくB」の対比を訳出／②an enemy "
               "&lt;that steals your study time&gt;＝関係詞節「勉強時間を盗む敵」／③a friend &lt;that "
               "makes each hour at your desk more valuable&gt;＝make O C（比較級）「机での一時間を"
               "より価値あるものにする味方」。 〔<b>読解ルール R3</b>／<b>構文ルール R11</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "運動の直後には、脳により多くの血液が送られて頭が目を覚ましており、新しい情報がより"
              "すんなりと頭に入りやすい状態になっている、ということ。",
     "points": "▶<b>採点要素</b>：①脳への血流が増える／②頭（心）が目覚める／③新しい情報が入り"
               "やすい（＝勉強の好機）。コロン（:）の言い換えと、段落末の In other words のまとめ"
               "（<b>イコール関係</b>）から「特別な状態」の中身を確定する。 〔<b>解法ルール R8</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "体を動かすことで不安の感情が軽くなり、長時間の勉強の間に積み重なったストレスが溶ける"
              "ように消えていく、という気分の変化。この変化によって、机に戻ってもう一度勉強に取り組む"
              "力が回復するので、休憩に体を動かした生徒の方がそのあとよく勉強できる、と筆者は述べて"
              "いる。",
     "points": "▶<b>採点要素</b>：①<b>This change</b>＝直前の二文（不安が軽くなる＋ストレスが消える）"
               "の気分の変化だと確定（各3点）／②その変化が「机に戻って再び取り組む力」を与え、休憩に"
               "動いた生徒の方がその後よく勉強できる（4点）。 〔<b>読解ルール R5</b>：指示語の中身を"
               "確定／<b>R6</b>：因果〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A・B。第1段（However→研究による反論）、第3段（Yet→主張へ転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that the hours … matter」→ 第3段 Yet で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(3) not an enemy but a friend＝「敵ではなく味方」が本文の核心。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第3段の抽象（学ぶ準備）→第4段の具体（短い散歩・集中・記憶）。第7段の「10分歩く」。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "下線部(2) This change＝「不安が軽くなり、ストレスが消える」変化を指す。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第3段 sends more blood → wakes up、第5段 When we move … grow lighter（動かす→軽くなる）。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。A・Bとも前後がぶつかる＝逆接。因果／例示／追加／類比の肢は不成立。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3。コロン(:)・in other words の言い換えで「学ぶ準備」の中身を確定。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。⑥の「完全になくなる」、③の「必要である」などは典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "an enemy &lt;that steals …&gt;／a friend &lt;that makes …&gt;、Every minute &lt;spent on …&gt; 型。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「運動＝体のためのもの。受験生には勉強時間を奪うぜいたく」を提示。→ <b>However（R1）</b>："
             "脳の研究は「この見方は大切な何かを見落としている」＝運動は脳も鍛える。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに机に向かう時間は大切。こつこつした練習が合格の土台。"
             "＝通念の一部は認める。"},
    {"arrow": "◀ Yet 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "運動直後の脳は<b>「学ぶ準備」完了</b>——血流が増え、頭が目覚め、新しい情報が入りやすい。"
             "運動後の数分は勉強の黄金時間。"},
    {"arrow": "↓　具体化（R4）"},
    {"role": "理由①の具体化", "para": "¶4", "kind": "reason",
     "text": "<b>長い運動は不要</b>：短い散歩でさえ効果あり。数分歩いたあとの方が課題に集中しやすく、"
             "学んだことが記憶に残りやすい（研究の示唆）。＝学習効果（理由①）。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>気分とストレス</b>：動くと不安が軽くなり、たまったストレスが消える→机に戻って再挑戦する"
             "力が回復（<b>R6因果</b>）。＝<b>This change</b>。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "運動は勉強時間の<b>敵ではなく味方</b>——<b>not an enemy but a friend（R3）</b>。動いた時間は"
             "失われず、価値を付けて戻る。本当の無駄は疲れた頭で同じページを見つめ続けること。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：長時間の激しい運動をせよという話ではないし、運動は万能でもない。"
             "休憩に<b>10分歩く</b>——それだけでこの習慣の入口として十分。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 受験生の運動への二つの見方",
     "caption": "同じ「運動」でも、〈敵〉と見なせば勉強時間を奪うぜいたくに見え、〈味方〉と見なせば"
                "机の一時間の価値を高める仲間になる。本文は However を境に、上の通念から下の主張へ反転する。",
     "para": "→ 第1・3・6段"},
    {"id": "fig2", "title": "図2 ｜ 運動が勉強を助ける二つの道",
     "caption": "運動の働きは二つ。①<b>脳への効果</b>：血流が増えて「学ぶ準備」が整い、集中・記憶が"
                "よくなる（第3〜4段）。②<b>心への効果</b>：不安・ストレスが減り、机に戻る力が回復する（第5段）。",
     "para": "→ 第3〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 運動は「敵」ではなく「味方」",
     "caption": "問題は運動そのものではなく「時間泥棒」という思い込み。短い運動に使った時間は失われず、"
                "<b>価値を付けて戻ってくる</b>——敵ではなく味方（not an enemy but a friend）。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "生徒たちに「運動は何のためのものか」と尋ねてみれば、その大半は体のことを話すだろう。運動は筋肉を"
        "作り、エネルギーを燃やし、体型を保ってくれる、と彼らは言うはずだ。試験に備える生徒にとっては、"
        "運動はぜいたく品のようにさえ見えることがある。走ったり歩いたりに使われる一分一分が、教科書から"
        "盗まれた一分のように思えるのだ。<b>しかし</b>、脳に関する研究は、このよくある見方が大切な何かを"
        "見落としていることを示唆している。運動は体だけでなく脳も鍛えるのだ、と科学者たちは言う。"),
    (2, "確かに、机に向かって過ごす時間は重要である。座って学ぶことなしに、英単語や数学の規則を身につける"
        "人はいない。来る日も来る日も続けるこつこつした練習は、今なお、どんな試験においても合格の土台で"
        "ある。もし運動が本当にその時間を生徒から奪うのなら、生徒たちが運動を避けるのは正しいことに"
        "なるだろう。"),
    (3, "<b>だが</b>、話はそこで終わらない。体を動かした直後、脳は特別な状態にある。すなわち、<b>学ぶ準備が"
        "できている</b>のだ。運動は脳により多くの血液を送り、頭は目を覚ます。この状態では、新しい情報が"
        "よりすんなりと頭に入っていくように見える。言い換えれば、運動のあとの数分間は、勉強のための黄金の"
        "時間なのである。"),
    (4, "その運動は、長くも激しくもある必要はない。短い散歩でさえ、私たちの勉強のあり方を変えうることを、"
        "研究は示唆している。数分間歩いたあとには、人はしばしば、課題に集中するのがより楽だと感じる。"
        "また、その状態で学んだことは、より長く記憶にとどまる傾向がある。要するに、軽い散歩は、もう一杯の"
        "コーヒーよりもうまく頭を整えてくれるのかもしれない。"),
    (5, "運動は二つ目のやり方でも生徒を助ける。すなわち、気分を上向かせるのだ。体を動かすと、不安の感情は"
        "軽くなっていく。長時間の勉強の間に積み重なったストレスも、ゆっくりと溶けて消えていく。<b>この変化"
        "が、机に戻ってもう一度やってみる力を私たちに与えてくれる。</b>だから、体を動かす短い休憩を取る"
        "生徒は、多くの場合、椅子を一度も離れない生徒よりも、そのあとよく勉強できるのである。"),
    (6, "このように見ると、運動は生徒の生活の中で新しい位置づけに値する。<b>運動は、あなたの勉強時間を盗む"
        "敵ではなく、机に向かう一時間一時間をより価値あるものにしてくれる味方なのである。</b>少し体を動かす"
        "ために使った時間は失われない。おまけの価値を付けて戻ってくるのだ。本当の無駄はむしろ、疲れて"
        "ぼんやりした頭に、同じページを無理やり見つめさせ続けることかもしれない。"),
    (7, "もちろん、これは何時間も激しいトレーニングをすべきだという意味ではない。また、運動が勉強上の"
        "あらゆる困難を取り除いてくれるわけでもない。要点はそれよりずっと単純だ。休憩中に頭が重く感じられ"
        "たら、立ち上がって10分ほど歩いてみることだ。その小さな一歩だけで、この新しい習慣への入口としては"
        "十分である。そして、あなたの体だけでなく脳が、そのことに感謝してくれるだろう。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("keep A in shape", "Aをよい体型・調子に保つ"),
    ("prepare for ~", "〜に備える、〜の準備をする"),
    ("luxury", "ぜいたく（品）"),
    ("suggest", "示唆する、それとなく示す"),
    ("A as well as B", "BだけでなくAも"),
    ("master（動詞）", "（技能などを）身につける"),
    ("steady", "着実な、こつこつした"),
    ("rob A of B", "AからBを奪う"),
    ("right after ~", "〜の直後に"),
    ("be ready to do", "〜する準備ができている"),
    ("wake up", "目を覚ます"),
    ("smoothly", "なめらかに、すんなりと"),
    ("in other words", "言い換えれば"),
    ("focus on ~", "〜に集中する"),
    ("tend to do", "〜する傾向がある"),
    ("in short", "要するに"),
    ("lift one's mood", "気分を上向かせる"),
    ("pile up", "積み重なる、たまる"),
    ("melt away", "溶けるように消える"),
    ("afterward", "そのあとで"),
    ("deserve", "〜に値する"),
    ("valuable", "価値のある"),
    ("force A to do", "Aに無理やり〜させる"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：運動＝体のため、という通念と、その反転",
  "sentences": [
    {"chunks": [("V","Ask","尋ねてみよ"),("O","a group of students","生徒たちに"),
                ("O","[what exercise is for],","運動は何のためのものかと"),
                ("接","and","そうすれば"),("S","most of them","その大半は"),
                ("V","will talk about","語るだろう"),("O","the body.","体のことを")],
     "note":"▶ <b>命令文 + and …</b>＝「〜せよ、そうすれば…」。what exercise is for＝間接疑問（名詞節）で ask の二つ目の目的語。"},
    {"chunks": [("S","Exercise","運動は"),("V","builds","作り"),("O","muscles,","筋肉を"),
                ("V","burns","燃やし"),("O","energy,","エネルギーを"),("接","and","そして"),
                ("V","keeps","保つ"),("O","us","私たちを"),("C","in shape,","よい体型に"),
                ("M","they will say.","と彼らは言うだろう")],
     "note":"▶ 一つの主語 Exercise に builds／burns／keeps の三つの動詞が並列。<b>keep O C</b>＝「OをCに保つ」。they will say は伝達部。"},
    {"chunks": [("M","(For a student &lt;preparing for exams&gt;),","試験に備える生徒にとっては"),
                ("S","it","それ（運動）は"),
                ("V","can even look like","〜のようにさえ見えうる"),("C","a luxury.","ぜいたく品")],
     "note":"▶ preparing for exams＝現在分詞が student を後ろから修飾〔<b>R11</b>〕。look like＋名詞＝「〜のように見える」。"},
    {"chunks": [("S","Every minute &lt;spent on running or walking&gt;","走ったり歩いたりに使われる一分一分は"),
                ("V","seems to be","〜であるように思える"),
                ("C","a minute &lt;stolen from the textbook&gt;.","教科書から盗まれた一分")],
     "note":"▶ <b>R11｜過去分詞の後置修飾</b>が2箇所（spent …／stolen …）。seem to be C＝「Cであるように思える」。通念のまとめ。"},
    {"chunks": [("接","However,","しかし"),("S","research on the brain","脳に関する研究は"),
                ("V","suggests","示唆する"),
                ("O","[that this common view misses something important].","このよくある見方が大切な何かを見落としている、と")],
     "note":"▶ <b>R1｜逆接 However の直後が筆者側の主張</b>（＝空所A）。something important＝-thing＋形容詞は後置。"},
    {"chunks": [("S","Exercise,","運動は"),("M","scientists say,","と科学者は言う"),
                ("V","trains","鍛える"),("O","the brain","脳を"),
                ("M","(as well as the body).","体だけでなく")],
     "note":"▶ scientists say＝挿入。<b>A as well as B</b>＝「BだけでなくAも」で力点はA（脳）。タイトルを回収する主題文。"},
  ]},
 {"head": "第2段 — 譲歩：確かに机の時間は大切（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当"),
                ("-","[that the hours &lt;(that) you spend at your desk&gt; matter].","机で過ごす時間が重要だということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。後の逆接（第3段 Yet）で反転する前振り。the hours (that) you spend＝関係詞省略〔<b>R11</b>〕。matter＝動詞「重要である」。"},
    {"chunks": [("S","No one","誰も〜ない"),("V","masters","身につけ（ない）"),
                ("O","English words or math rules","英単語や数学の規則を"),
                ("M","(without sitting down and learning them).","座って学ぶことなしに")],
     "note":"▶ no one＋肯定動詞＝全否定。<b>without doing</b>＝「〜せずに」。「座学は欠かせない」と譲歩を強める一文。"},
    {"chunks": [("S","Steady practice,","こつこつした練習は"),("M","day after day,","来る日も来る日も"),
                ("V","is","である"),("M","still","今なお"),
                ("C","the base of success in any exam.","どんな試験でも合格の土台")],
     "note":"▶ day after day＝挿入の副詞句。still「それでもなお」が譲歩の継続を示す。"},
    {"chunks": [("M","(If exercise really robbed students of that time),","もし運動が本当にその時間を生徒から奪うのなら"),
                ("S","they","彼らは"),("V","would be","〜だろう"),
                ("C","right &lt;to avoid it&gt;.","それを避けるのが正しい")],
     "note":"▶ <b>仮定法過去</b>（If S 過去形 …, S would do）＝「実際には奪わない」という含み。rob A of B＝「AからBを奪う」。次段の反転への橋。"},
  ]},
 {"head": "第3段 — 主張への転換：運動直後の脳は「学ぶ準備」完了（Yet）",
  "sentences": [
    {"chunks": [("接","Yet","だが"),("S","the story","話は"),("V","does not end","終わらない"),
                ("M","there.","そこで")],
     "note":"▶ <b>R1｜Yet＝逆接。ここが主張への転換点</b>（＝空所B）。第2段の譲歩を受けて反転する。"},
    {"chunks": [("M","(Right after you move your body),","体を動かした直後には"),
                ("S","your brain","脳は"),("V","is","ある"),
                ("M","(in a special state):","特別な状態に"),
                ("S","it","それは"),("V","is","である"),("C","ready &lt;to learn&gt;.","学ぶ準備ができて")],
     "note":"▶ <b>R8｜コロン(:)＝直前の言い換え</b>。a special state の中身が it is ready to learn。＝<b>下線部(1)＝問3</b>。"},
    {"chunks": [("S","Exercise","運動は"),("V","sends","送る"),("O","more blood","より多くの血液を"),
                ("M","(to the brain),","脳へ"),("接","and","そして"),
                ("S","the mind","頭は"),("V","wakes up.","目を覚ます")],
     "note":"▶ send A to B。and が軽い因果（血流増→覚醒）をつなぐ〔<b>R6</b>〕。「学ぶ準備」の生理的な中身。"},
    {"chunks": [("M","(In this state),","この状態では"),("S","new information","新しい情報は"),
                ("V","seems to enter","入っていくように見える"),("O","the head","頭に"),
                ("M","more smoothly.","よりすんなりと")],
     "note":"▶ this state＝前文の「血流が増え、目覚めた状態」を指す指示語〔<b>R5</b>〕。seem to do＝断定を避ける言い方。"},
    {"chunks": [("M","In other words,","言い換えれば"),
                ("S","the minutes after exercise","運動のあとの数分間は"),("V","are","である"),
                ("C","a golden time for study.","勉強のための黄金の時間")],
     "note":"▶ <b>R8｜in other words＝イコール関係の目印</b>。段落の主張をまとめ直す一文。"},
  ]},
 {"head": "第4段 — 具体化：短い散歩でも効果は出る（抽象→具体）",
  "sentences": [
    {"chunks": [("S","The exercise","その運動は"),("V","does not have to be","〜である必要はない"),
                ("C","long or hard.","長くも激しくも")],
     "note":"▶ <b>don't have to do</b>＝「〜する必要はない」（禁止の must not と区別）。問7③を切る根拠の一文。"},
    {"chunks": [("S","Research","研究は"),("V","suggests","示唆する"),
                ("O","[that even a short walk can change the way &lt;(that) we study&gt;].","短い散歩でさえ、私たちの勉強のあり方を変えうる、と")],
     "note":"▶ <b>R4｜ここから具体化</b>（短い散歩）。the way (that) we study＝関係副詞の省略〔<b>R11</b>〕。even＝「〜でさえ」。"},
    {"chunks": [("M","(After walking for a few minutes),","数分間歩いたあとには"),
                ("S","people","人は"),("M","often","しばしば"),("V","find","気づく"),
                ("O","it","（形式目的語）"),("C","easier","より楽だと"),
                ("-","&lt;to focus on a task&gt;.","課題に集中することが")],
     "note":"▶ <b>find it C to do</b>＝形式目的語構文。真の目的語は to focus on a task。比較級 easier＝「（歩く前）より楽」。"},
    {"chunks": [("S","[What they learn in that state]","その状態で学んだことは"),
                ("M","also","また"),("V","tends to stay","とどまる傾向がある"),
                ("M","(in their memory)","記憶に"),("M","longer.","より長く")],
     "note":"▶ <b>関係代名詞 what</b>「〜すること」＝名詞節が主語。tend to do＝「〜する傾向がある」。"},
    {"chunks": [("S","A light walk,","軽い散歩は"),("M","in short,","要するに"),
                ("V","may prepare","整えるかもしれない"),("O","the mind","頭を"),
                ("M","(better than another cup of coffee).","もう一杯のコーヒーよりもうまく")],
     "note":"▶ in short＝まとめの目印〔<b>R8</b>〕。比較 better than …。段落の結論文。"},
  ]},
 {"head": "第5段 — 理由②：運動は気分を上向かせ、机に戻る力を返す",
  "sentences": [
    {"chunks": [("S","Exercise","運動は"),("V","helps","助ける"),("O","students","生徒を"),
                ("M","(in a second way):","二つ目のやり方で"),
                ("S","it","それは"),("V","lifts","上向かせる"),("O","their mood.","気分を")],
     "note":"▶ <b>R8｜コロン(:)＝言い換え</b>。「二つ目のやり方」の中身＝気分を上向かせること。理由②の主題提示。"},
    {"chunks": [("M","(When we move our bodies),","体を動かすと"),
                ("S","feelings of worry","不安の感情は"),("V","grow","なっていく"),
                ("C","lighter.","より軽く")],
     "note":"▶ <b>R6｜when 節が事実上の因果</b>（動かす→軽くなる）。grow＋比較級＝「だんだん〜になる」。"},
    {"chunks": [("S","Stress &lt;that has piled up during long hours of study&gt;","長時間の勉強の間に積み重なったストレスは"),
                ("M","slowly","ゆっくりと"),("V","melts away.","溶けて消える")],
     "note":"▶ that has piled up …＝関係代名詞節が Stress を後ろから修飾〔<b>R11</b>〕。melt away＝「溶けるように消える」。"},
    {"chunks": [("S","This change","この変化が"),("V","gives","与える"),("O","us","私たちに"),
                ("O","the power &lt;to return to our desks and try again&gt;.","机に戻ってもう一度やってみる力を")],
     "note":"▶ <b>R5｜This change＝前の二文（不安が軽くなる＋ストレスが消える）の変化を指す</b>。give O1 O2。to return …＝power を修飾する不定詞。＝<b>下線部(2)＝問5</b>。"},
    {"chunks": [("S","A student &lt;who takes a short break to move&gt;","体を動かす短い休憩を取る生徒は"),
                ("M","often","多くの場合"),("V","studies","勉強する"),
                ("M","better afterward","そのあと、より良く"),
                ("M","(than one &lt;who never leaves the chair&gt;).","椅子を一度も離れない生徒よりも")],
     "note":"▶ 関係代名詞 who が2箇所〔<b>R11</b>〕。one＝a student の代用。比較 studies better … than …。"},
  ]},
 {"head": "第6段 — 核心的主張：運動は敵ではなく味方（not A but B）",
  "sentences": [
    {"chunks": [("M","(Seen in this way),","このように見ると"),("S","exercise","運動は"),
                ("V","deserves","値する"),("O","a new place","新しい位置づけに"),
                ("M","(in student life).","生徒の生活の中で")],
     "note":"▶ Seen in this way＝過去分詞の分詞構文（＝If it is seen …）。deserve O＝「Oに値する」。"},
    {"chunks": [("S","It","それ（運動）は"),("V","is","である"),
                ("C","not an enemy &lt;that steals your study time&gt;","勉強時間を盗む敵ではなく"),
                ("C","but a friend &lt;that makes each hour at your desk more valuable&gt;.","机に向かう一時間一時間をより価値あるものにする味方")],
     "note":"▶ <b>R3｜not A but B＝Bこそ核心</b>。that の関係詞節が enemy／friend をそれぞれ修飾〔<b>R11</b>〕。make O C（比較級）。＝<b>下線部(3)＝問2（和訳）</b>。"},
    {"chunks": [("S","Time &lt;used for a little movement&gt;","少し体を動かすために使われた時間は"),
                ("V","is not lost;","失われない"),
                ("S","it","それは"),("V","comes back","戻ってくる"),
                ("M","(with extra value).","おまけの価値を付けて")],
     "note":"▶ used for …＝過去分詞の後置修飾〔<b>R11</b>〕。セミコロン(;)＝前半の言い換え・補足〔<b>R8</b>〕。"},
    {"chunks": [("S","The real waste","本当の無駄は"),("V","may be","〜かもしれない"),
                ("C","forcing a tired, cloudy head to stare at the same page.","疲れてぼんやりした頭に同じページを見つめさせ続けること")],
     "note":"▶ 動名詞 forcing …＝補語。<b>force O to do</b>＝「Oに無理やり〜させる」。通念（運動＝無駄）を逆転させて核心を締める。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：10分の散歩で十分な「入口」",
  "sentences": [
    {"chunks": [("M","Of course,","もちろん"),("S","this","このことは"),
                ("V","does not mean","意味しない"),
                ("O","[that you should spend hours on hard training].","何時間も激しいトレーニングをすべきだとは")],
     "note":"▶ Of course, …＝譲歩の型。spend＋時間＋on A「Aに時間を使う」。主張の行き過ぎを防ぐ限定（問6①を切る根拠）。"},
    {"chunks": [("S","Exercise","運動は"),("V","will not remove","取り除きはしない"),
                ("O","every difficulty in your studies,","勉強上のあらゆる困難を"),
                ("M","either.","（〜も）また")],
     "note":"▶ <b>not ＋ every＝部分否定</b>「すべてを〜するわけではない」。問7⑥「完全になくなる」を切る根拠〔<b>R9</b>〕。either＝否定文の「〜もまた」。"},
    {"chunks": [("S","The point","要点は"),("V","is","である"),("C","much simpler","はるかに単純"),
                ("M","(than that).","それよりも")],
     "note":"▶ much＋比較級＝比較の強調。that＝前の二文（長時間の運動・万能の解決）を指す〔<b>R5</b>〕。"},
    {"chunks": [("M","(When your head feels heavy during a break),","休憩中に頭が重く感じられたら"),
                ("V","stand up","立ち上がれ"),("接","and","そして"),("V","walk","歩け"),
                ("M","(for about ten minutes).","10分ほど")],
     "note":"▶ 命令文二つの並列。feel＋形容詞＝「〜に感じられる」。結論の具体的な行動提案〔<b>R4</b>〕。"},
    {"chunks": [("S","That small step","その小さな一歩で"),("V","is","である"),
                ("C","enough","十分"),
                ("M","(as an entrance to this new habit).","この新しい習慣への入口としては")],
     "note":"▶ enough＝補語。as A＝「Aとして」。問7⑤の根拠となる一文。"},
    {"chunks": [("S","Your brain,","あなたの脳が"),("M","not just your body,","体だけでなく"),
                ("V","will thank","感謝するだろう"),("O","you","あなたに"),
                ("M","(for it).","そのことで")],
     "note":"▶ not just A＝挿入で「Aだけでなく」。thank A for B＝「BのことでAに感謝する」。タイトルを回収して締める。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=6文/第2段=4文/第3段=5文/第4段=5文/第5段=5文/第6段=4文/第7段=6文)
SVOC_LOGIC = {
    (1, 5): "対比", (1, 6): "主張",              # s5 However→反論 / s6 脳も鍛える(主題文)
    (2, 1): "譲歩", (2, 4): "譲歩",              # s1 It is true / s4 仮定法の駄目押し
    (3, 1): "対比", (3, 2): "主張", (3, 3): "因果", (3, 4): "因果", (3, 5): "主張",
    (4, 1): "主張", (4, 2): "具体例", (4, 3): "具体例", (4, 4): "具体例", (4, 5): "主張",
    (5, 1): "主張", (5, 2): "因果", (5, 3): "因果", (5, 4): "因果", (5, 5): "具体例",
    (6, 1): "主張", (6, 2): "主張", (6, 3): "追加", (6, 4): "対比",
    (7, 1): "譲歩", (7, 2): "譲歩", (7, 4): "主張", (7, 5): "主張", (7, 6): "主張",
}
