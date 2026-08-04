# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.06 — 単一ソース (基礎編)
テーマ: Music While Studying: Friend or Enemy? (音楽を聴きながらの勉強は敵か味方か)
基礎レベル（偏差値55〜60 / The Rules 1〜2 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "06",
    "level": "基礎レベル",
    "level_sub": "偏差値55〜60 / The Rules 1〜2 相当",
    "theme_ja": "音楽を聴きながらの勉強は敵か味方か",
    "theme_en": "Music While Studying: Friend or Enemy?",
    "minutes": 15,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Walk into any library at night, and you will see the same scene. Half of the '
        'students are studying with earphones in their ears. Many of them believe that they '
        'study better with their favorite songs playing. Music makes a long evening feel '
        'shorter, they say, and silence sounds dull. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, the truth is not so simple. Whether '
        'music helps or hurts depends on the kind of study you are doing.'),
    (2, 'It is true that music has real power. A favorite song brightens your mood and '
        'gives you energy before a hard task. For simple, boring work, music can be a true '
        'helper. When you are sorting word cards or copying a list of dates, a good beat '
        'keeps your hands moving. In such moments, music works like a cheerful coach.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span> the picture changes when the study '
        'itself uses words. Reading long passages, writing essays, and memorizing new words '
        'all depend on the language system of your brain. A song with lyrics uses the very '
        'same system. In other words, <u>the words in the song and the words in your '
        'textbook fight for the same space in your head.<sup>(1)</sup></u> Your brain cannot '
        'follow two streams of words at the same time.'),
    (4, 'Research on reading gives a clear example. When people read while listening to '
        'songs with lyrics, they tend to read the same lines again and again. They also '
        'remember less of what they have read. Music without words, such as quiet piano '
        'pieces, causes much smaller problems. Natural sounds, like rain or waves, seem '
        'almost harmless. The real danger, research suggests, lies mainly in the lyrics.'),
    (5, 'There is a second problem: music creates a false sense of progress. Because your '
        'favorite songs put you in a good mood, the evening feels smooth and productive. '
        'You feel that you are moving fast, even when you are not. In fact, <u>the feeling '
        'of progress and the real result are two different things.<sup>(2)</sup></u> A '
        'pleasant three hours with music can teach you less than one quiet hour without it.'),
    (6, 'What should students do, then? The answer begins with a change of view. <u>Music '
        'is not an enemy or a friend but a tool, and what matters is when you use it and '
        'when you turn it off.<sup>(3)</sup></u> A hammer is perfect for a nail but useless '
        'for a screw. Music, too, works only when the job fits.'),
    (7, 'Of course, this does not mean that you must throw your music away. During breaks, '
        'let your favorite songs wash your stress away. For simple tasks, use music to keep '
        'your hands moving. But when you sit down to read, write, or memorize, choose '
        'silence instead. Using music well is not a matter of loving it or hating it. It is '
        'a matter of knowing the right time for each. That quiet skill may raise the value '
        'of every study hour.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Walk into any library at night, and you will see the same scene. Half of the students "
    "are studying with earphones in their ears. Many of them believe that they study better "
    "with their favorite songs playing. Music makes a long evening feel shorter, they say, "
    "and silence sounds dull. Still, the truth is not so simple. Whether music helps or "
    "hurts depends on the kind of study you are doing. "
    "It is true that music has real power. A favorite song brightens your mood and gives "
    "you energy before a hard task. For simple, boring work, music can be a true helper. "
    "When you are sorting word cards or copying a list of dates, a good beat keeps your "
    "hands moving. In such moments, music works like a cheerful coach. "
    "Yet the picture changes when the study itself uses words. Reading long passages, "
    "writing essays, and memorizing new words all depend on the language system of your "
    "brain. A song with lyrics uses the very same system. In other words, the words in the "
    "song and the words in your textbook fight for the same space in your head. Your brain "
    "cannot follow two streams of words at the same time. "
    "Research on reading gives a clear example. When people read while listening to songs "
    "with lyrics, they tend to read the same lines again and again. They also remember less "
    "of what they have read. Music without words, such as quiet piano pieces, causes much "
    "smaller problems. Natural sounds, like rain or waves, seem almost harmless. The real "
    "danger, research suggests, lies mainly in the lyrics. "
    "There is a second problem: music creates a false sense of progress. Because your "
    "favorite songs put you in a good mood, the evening feels smooth and productive. You "
    "feel that you are moving fast, even when you are not. In fact, the feeling of progress "
    "and the real result are two different things. A pleasant three hours with music can "
    "teach you less than one quiet hour without it. "
    "What should students do, then? The answer begins with a change of view. Music is not "
    "an enemy or a friend but a tool, and what matters is when you use it and when you turn "
    "it off. A hammer is perfect for a nail but useless for a screw. Music, too, works only "
    "when the job fits. "
    "Of course, this does not mean that you must throw your music away. During breaks, let "
    "your favorite songs wash your stress away. For simple tasks, use music to keep your "
    "hands moving. But when you sit down to read, write, or memorize, choose silence "
    "instead. Using music well is not a matter of loving it or hating it. It is a matter of "
    "knowing the right time for each. That quiet skill may raise the value of every study "
    "hour."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① As a result &nbsp; ② Still &nbsp; ③ For example &nbsp; ④ Moreover",
         "【 B 】 &nbsp; ① Therefore &nbsp; ② For instance &nbsp; ③ Yet &nbsp; ④ In addition",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(3) <span class='en'>Music is not an enemy or a friend but a tool, and "
             "what matters is when you use it and when you turn it off.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) について、歌の中のことばと教科書のことばが「頭の中の同じ場所を取り合う"
             "（<span class='en'>fight for the same space in your head</span>）」とはどういうことか。"
             "本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で述べられている「歌詞のある曲と読書」に関する研究の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 歌詞のある曲を聴きながら読むと、同じ行を何度も読み直しがちになり、内容の記憶も減る。",
         "② 歌詞のある曲を聴きながら読んだ方が、読み直しが減って、内容の理解はかえって深まる。",
         "③ 歌詞のない静かな曲は、歌詞のある曲よりも、読書をはるかに大きく妨げると分かっている。",
         "④ 雨や波のような自然の音は、歌詞のある曲と同じくらい強く、読んでいる内容の妨げになる。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(2) <span class='en'>the feeling of progress and the real result are two "
             "different things.</span> について、音楽を聴きながら勉強すると、なぜ「はかどっている"
             "感覚」と「本当の結果」がずれるのか。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 音楽はどんな種類の勉強でも必ず妨げになるので、勉強中に聴くことは一切やめるべきだ。",
         "② 音楽は気分を高めて元気をくれるのだから、あらゆる勉強で積極的に聴き続けるのがよい。",
         "③ 歌詞のない曲を選びさえすれば、ことばを使う勉強の効果も大きく高めることができる。",
         "④ 音楽は敵でも味方でもなく道具であり、いつ使い、いつ止めるかの使い分けこそが大切だ。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 音楽は、歌詞があってもなくても、読んでいる内容の理解をどんな場合も必ず妨げてしまう。",
         "② 音楽を聴きながら勉強すると、気分だけでなく、実際の勉強の結果も同じように良くなる。",
         "③ 単語カードの整理のような単純な作業では、音楽は手を動かし続けるための助けになりうる。",
         "④ 筆者は、勉強の妨げになるのだから、音楽そのものを完全に捨て去るべきだと述べている。",
         "⑤ 歌詞のある曲を聴きながら読むと、同じ行の読み直しが増え、内容が記憶に残りにくくなる。",
         "⑥ 筆者は、休憩や単純作業では音楽を使い、ことばの勉強では静けさを選ぶよう勧めている。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ② Still　　B ＝ ③ Yet",
     "exp": "A：第1段は「お気に入りの曲と一緒の方がよく勉強できる」という生徒の通念→空所の後は"
            "「真実はそう単純ではない」と反転する。<b>逆接</b>でつなぐ → Still（それでも・しかし）。"
            "As a result（因果）・For example（例示）・Moreover（追加）は不可。<br>"
            "B：第2段「確かに音楽には本物の力がある（＝譲歩）」に対し、第3段は「だが、勉強そのものが"
            "ことばを使うものだと話が変わる」と主張へ<b>転換</b>する。逆接 → Yet。Therefore（因果）・"
            "For instance（例示）・In addition（追加）は流れに合わない。 〔<b>解法ルール R7</b>／"
            "<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "①",
     "exp": "第4段「they tend to read the same lines again and again」＋「They also remember "
            "less of what they have read」＝同じ行を何度も読み直しがちになり、読んだ内容の記憶も"
            "減る。②は逆。③は逆（歌詞のない曲は causes much smaller problems＝問題はずっと小さい）。"
            "④も逆（Natural sounds … seem almost harmless＝ほぼ無害）。 〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "④",
     "exp": "第6段「Music is not an enemy or a friend but a tool」＋「what matters is when you "
            "use it and when you turn it off」と一致。①は「一切やめるべき」が<b>言い過ぎ</b>"
            "（第2段・第7段：単純作業や休憩では味方になる）。②は本文と逆（第3〜5段：ことばの勉強では"
            "妨げになる）。③は本文にない（歌詞のない曲は「問題が小さい」だけで、効果を「高める」とは"
            "述べていない）。 〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "③・⑤・⑥",
     "exp": "①×：第4段「Music without words … causes much smaller problems」「Natural sounds … "
            "seem almost harmless」に反する——「どんな場合も必ず」は典型的な<b>言い過ぎ</b>。"
            "②×：第5段「the feeling of progress and the real result are two different things"
            "（気分は上がっても結果は別物）」に反する。④×：第7段「this does not mean that you must "
            "throw your music away」と明確に否定——「完全に捨て去る」も<b>言い過ぎ</b>。"
            " 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(3)和訳",
     "model": "音楽は敵でも味方でもなく道具なのであり、大事なのは、いつそれを使い、いつそれを止める"
              "（切る）かということである。",
     "points": "▶<b>採点要素</b>：①<b>not A or B but C</b>＝「AでもBでもなくC」の対比を訳出／"
               "②<b>what matters</b>＝関係代名詞 what「大事なこと・重要なのは」を主語として訳す／"
               "③when you use it and when you turn it off＝「いつ使い、いつ止めるか」（名詞節）。"
               " 〔<b>読解ルール R3</b>／<b>構文ルール R11</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "長文を読む・英作文を書く・単語を覚えるといったことばの勉強は、どれも脳の言語システムを"
              "使うが、歌詞のある曲もまさに同じシステムを使うため、脳は二つのことばの流れを同時に追う"
              "ことができず、歌詞と教材のことばが互いに脳の働きを奪い合ってしまう、ということ。",
     "points": "▶<b>採点要素</b>：①ことばの勉強と歌詞が、脳の<b>同じ言語システム</b>を使う（3点）／"
               "②脳は二つのことばの流れを同時に処理できない（3点）／③そのため互いに取り合いが起こり、"
               "教材のことばに働きが回らなくなる（2点）。直前の二文と In other words の<b>イコール"
               "関係</b>から中身を確定する。 〔<b>解法ルール R8</b>／<b>読解ルール R5</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "お気に入りの曲は気分を良くするため、音楽を聴きながら勉強すると、夜全体がなめらかで"
              "生産的に感じられ、実際には進んでいないときでさえ速く進んでいる気がしてしまう。しかし、"
              "それは音楽が作り出した「はかどっている」という誤った感覚にすぎず、実際に理解し覚えられた"
              "量（結果）が増えているわけではない。だから、感覚と結果はずれるのである。",
     "points": "▶<b>採点要素</b>：①音楽が気分を上げる→「速く進んでいる感じ」が生まれる、という因果"
               "（4点）〔<b>R6</b>〕／②それは a false sense of progress＝音楽が作る<b>錯覚</b>であり、"
               "実際の結果（理解・記憶）は増えていない（4点）／③音楽つきの快適な3時間が、静かな1時間に"
               "劣ることさえある、という帰結（2点）。 〔<b>読解ルール R6</b>／<b>解法ルール R8</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A・B。第1段（Still→「そう単純ではない」）、第3段（Yet→主張へ転換）、第7段の But。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that music has real power」→ 第3段 Yet で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(3) not an enemy or a friend but a tool、第7段 not a matter of … / a matter of …。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第2段（単純作業→カード整理・書き写し）、第4段の研究の知見、第6段の金づちのたとえ。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "第3段 the very same system、第7段 That quiet skill＝「時を知る技術」。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第5段 Because your favorite songs put you in a good mood → はかどり感（錯覚）が生まれる。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。A・Bとも前後がぶつかる＝逆接。因果／例示／追加の肢は不成立。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。In other words と第5段のコロン(:)＝直前・直後の言い換えを利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。①「どんな場合も必ず」・④「完全に捨て去る」などは典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "the kind of study &lt;(that) you are doing&gt;、[what they have read]・[what matters]＝関係代名詞 what。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「好きな音楽と一緒の方が勉強がはかどる」を提示。→ <b>Still（R1）</b>：真実はそう"
             "単純ではない——助けになるか妨げになるかは<b>勉強の種類</b>で決まる。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：音楽の力は本物。気分を上げ、カード整理や書き写しの"
             "ような単純作業では手を動かし続けさせてくれる。＝通念の一部は認める。"},
    {"arrow": "◀ Yet 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "ことばを使う勉強（読解・英作文・暗記）では話が別。歌詞のことばと教材のことばが、脳の"
             "<b>同じ言語システム</b>を取り合う——二つのことばの流れは同時に追えない。"},
    {"arrow": "↓　具体化（R4）"},
    {"role": "理由①の具体化", "para": "¶4", "kind": "reason",
     "text": "研究の知見：歌詞入りの曲を聴きながら読むと<b>読み直しが増え、記憶に残る量が減る</b>。"
             "歌詞のない曲や自然音なら影響は小さい——危険の正体は主に<b>歌詞</b>。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>はかどり錯覚</b>：音楽は気分を上げるので、実際より進んでいるように感じる"
             "（<b>R6因果</b>）。感覚と結果は別物——快適な3時間が静かな1時間に劣ることも。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "音楽は敵でも味方でもなく<b>道具</b>——<b>not an enemy or a friend but a tool（R3）</b>。"
             "大事なのは<b>いつ使い、いつ止めるか</b>。金づちがくぎ専用であるのと同じ。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：音楽を捨てろという話ではない。休憩・単純作業では<b>味方</b>にし、"
             "ことばの勉強では<b>静けさ</b>を選ぶ——使い分けこそが答え。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 勉強の種類で音楽の顔が変わる",
     "caption": "同じ「音楽」でも、<b>単純作業</b>（カード整理・書き写し）では手を動かし続けさせる味方に"
                "なり、<b>ことばの勉強</b>（読解・英作文・暗記）では歌詞が教材のことばと頭の同じ場所を"
                "取り合う。本文は Still／Yet を境に、通念から主張へ反転する。",
     "para": "→ 第2〜4段"},
    {"id": "fig2", "title": "図2 ｜ 歌詞つき音楽が生む二つの問題",
     "caption": "問題は二つ。①<b>ことばの取り合い</b>：同じ行を読み直し、内容が記憶に残りにくい"
                "（第3〜4段）。②<b>はかどり錯覚</b>：気分だけが上がり、「はかどっている感じ」と本当の"
                "結果がずれる（第5段）。",
     "para": "→ 第3〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 音楽は「敵」でも「味方」でもなく「道具」",
     "caption": "敵か味方かの二択をやめる。音楽は<b>道具</b>——金づちがくぎ専用であるように、合う仕事の"
                "ときだけ働く。<b>いつ使い、いつ止めるか</b>を知ることが答え（not an enemy or a friend "
                "but a tool）。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "夜、どこかの図書館に入ってみれば、同じ光景を目にするだろう。生徒の半分は、耳にイヤホンを入れた"
        "まま勉強している。彼らの多くは、お気に入りの曲を流しながらの方がよく勉強できる、と信じている。"
        "音楽は長い夜を短く感じさせてくれるし、静けさは退屈に聞こえる、と彼らは言う。<b>それでも</b>、"
        "真実はそれほど単純ではない。音楽が助けになるか妨げになるかは、いましている勉強の種類によって"
        "決まるのだ。"),
    (2, "確かに、音楽には本物の力がある。お気に入りの一曲は気分を明るくし、難しい課題の前に元気を与えて"
        "くれる。単純で退屈な作業にとって、音楽は本当の助っ人になりうる。単語カードを整理したり日付の"
        "一覧を書き写したりしているとき、心地よいビートは手を動かし続けさせてくれる。そうした場面では、"
        "音楽は陽気なコーチのように働くのだ。"),
    (3, "<b>だが</b>、勉強そのものがことばを使うものになると、様子は一変する。長い文章を読むことも、"
        "エッセイ（英作文）を書くことも、新しい単語を暗記することも、すべて脳の言語システムに頼っている。"
        "歌詞のある曲は、まさにその同じシステムを使う。言い換えれば、<b>歌の中のことばと教科書のことばが、"
        "頭の中の同じ場所を取り合う</b>のである。脳は、二つのことばの流れを同時に追うことはできない。"),
    (4, "読むことに関する研究が、分かりやすい例を与えてくれる。歌詞のある曲を聴きながら文章を読むと、"
        "人は同じ行を何度も読み直しがちになる。しかも、読んだ内容を覚えている量も少なくなる。静かな"
        "ピアノ曲のような歌詞のない音楽なら、引き起こす問題はずっと小さい。雨や波のような自然の音は、"
        "ほとんど無害のようだ。本当の危険は主に歌詞にある、と研究は示唆している。"),
    (5, "二つ目の問題がある。すなわち、音楽は「はかどっている」という誤った感覚を作り出すのだ。お気に"
        "入りの曲は気分を良くしてくれるので、その晩は、なめらかで生産的に感じられる。実際には速く進んで"
        "いないときでさえ、速く進んでいる気がしてしまう。だが実のところ、<b>はかどっている感覚と本当の"
        "結果は、別のものなのである。</b>音楽と過ごす心地よい3時間が、音楽なしの静かな1時間よりも、"
        "教えてくれるものが少ないこともあるのだ。"),
    (6, "それでは、生徒はどうすればよいのだろうか。答えは、ものの見方を変えることから始まる。<b>音楽は"
        "敵でも味方でもなく道具なのであり、大事なのは、いつそれを使い、いつそれを止めるかということだ。"
        "</b>金づちは、くぎにはうってつけだが、ねじには役に立たない。音楽もまた、仕事（用途）が合うとき"
        "にだけ働くのである。"),
    (7, "もちろんこれは、音楽を捨ててしまわなければならないという意味ではない。休憩中には、お気に入りの"
        "曲にストレスを洗い流してもらえばよい。単純な作業では、手を動かし続けるために音楽を使えばよい。"
        "しかし、読む・書く・覚えるために机に向かうときは、代わりに静けさを選ぶことだ。音楽をうまく使う"
        "ことは、音楽を愛するか嫌うかという問題ではない。それぞれにふさわしい時を知っている、という問題"
        "なのだ。その静かな技術が、勉強の一時間一時間の価値を高めてくれるかもしれない。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("scene", "光景、場面"),
    ("with earphones in one's ears", "耳にイヤホンを入れたまま（付帯状況）"),
    ("brighten one's mood", "気分を明るくする"),
    ("sort", "整理する、分類する"),
    ("beat", "拍子、ビート"),
    ("cheerful", "陽気な、明るい"),
    ("lyrics", "歌詞"),
    ("memorize", "暗記する"),
    ("depend on ~", "〜に頼る、〜次第である"),
    ("the very same ~", "まさにその同じ〜"),
    ("fight for ~", "〜を取り合う、〜を求めて争う"),
    ("stream", "流れ"),
    ("again and again", "何度も繰り返して"),
    ("cause", "引き起こす"),
    ("harmless", "無害な"),
    ("lie in ~", "〜にある、〜に存在する"),
    ("a false sense of ~", "〜という誤った感覚"),
    ("put A in a good mood", "Aを良い気分にさせる"),
    ("productive", "生産的な、はかどる"),
    ("turn ~ off", "〜を止める、（スイッチを）切る"),
    ("throw ~ away", "〜を捨てる"),
    ("a matter of ~", "〜の問題"),
    ("instead", "その代わりに"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：音楽と一緒の方がはかどる、という通念と、その反転",
  "sentences": [
    {"chunks": [("V","Walk","歩いて入ってみよ"),("M","(into any library at night),","夜、どこかの図書館に"),
                ("接","and","そうすれば"),("S","you","あなたは"),
                ("V","will see","目にするだろう"),("O","the same scene.","同じ光景を")],
     "note":"▶ <b>命令文 + and …</b>＝「〜せよ、そうすれば…」。any＝「どの〜でも」。"},
    {"chunks": [("S","Half of the students","生徒の半分は"),("V","are studying","勉強している"),
                ("M","(with earphones in their ears).","耳にイヤホンを入れたまま")],
     "note":"▶ <b>with＋名詞＋場所（付帯状況）</b>＝「〜を…に付けたまま」。導入の情景描写。"},
    {"chunks": [("S","Many of them","彼らの多くは"),("V","believe","信じている"),
                ("O","[that they study better with their favorite songs playing].","お気に入りの曲が流れている状態の方がよく勉強できる、と")],
     "note":"▶ believe that 節。<b>with O doing（付帯状況）</b>＝「Oが〜している状態で」。＝通念の中身。"},
    {"chunks": [("S","Music","音楽は"),("V","makes","させる"),("O","a long evening","長い夜を"),
                ("C","feel shorter,","より短く感じるように"),("M","they say,","と彼らは言う"),
                ("接","and","そして"),("S","silence","静けさは"),("V","sounds","聞こえる"),("C","dull.","退屈に")],
     "note":"▶ <b>make O do（原形）</b>＝「Oに〜させる」。sound＋形容詞＝「〜に聞こえる」。they say は挿入。"},
    {"chunks": [("接","Still,","それでも（しかし）"),("S","the truth","真実は"),("V","is","である"),
                ("C","not so simple.","それほど単純ではない")],
     "note":"▶ <b>R1｜逆接 Still の直後が筆者側の主張</b>（＝空所A）。Still＝「それでも・しかし」の副詞。"},
    {"chunks": [("S","[Whether music helps or hurts]","音楽が助けになるか妨げになるかは"),
                ("V","depends on","〜によって決まる"),
                ("O","the kind of study &lt;(that) you are doing&gt;.","いましている勉強の種類に")],
     "note":"▶ <b>whether A or B</b>＝「AかBか」の名詞節が主語。you are doing＝関係詞省略で study を修飾〔<b>R11</b>〕。本文全体の見取り図。"},
  ]},
 {"head": "第2段 — 譲歩：確かに音楽の力は本物（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当"),
                ("-","[that music has real power].","音楽に本物の力があるということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。後の逆接（第3段 Yet）で反転する前振り。"},
    {"chunks": [("S","A favorite song","お気に入りの一曲は"),("V","brightens","明るくし"),("O","your mood","気分を"),
                ("接","and","そして"),("V","gives","与える"),("O","you","あなたに"),("O","energy","元気を"),
                ("M","(before a hard task).","難しい課題の前に")],
     "note":"▶ 一つの主語に brightens／gives の二つの動詞が並列。<b>give O1 O2</b>＝「O1にO2を与える」。"},
    {"chunks": [("M","(For simple, boring work),","単純で退屈な作業にとっては"),
                ("S","music","音楽は"),("V","can be","なりうる"),("C","a true helper.","本当の助っ人に")],
     "note":"▶ for A＝「Aにとって」。can＝可能性「〜でありうる」。譲歩の中心文。"},
    {"chunks": [("M","(When you are sorting word cards or copying a list of dates),","単語カードを整理したり日付の一覧を書き写したりしているとき"),
                ("S","a good beat","心地よいビートは"),("V","keeps","保つ"),
                ("O","your hands","手を"),("C","moving.","動き続ける（状態に）")],
     "note":"▶ <b>R4｜抽象（単純作業）→具体（カード整理・書き写し）</b>。<b>keep O doing</b>＝「Oを〜し続けさせる」。sorting／copying が並列。"},
    {"chunks": [("M","(In such moments),","そうした場面では"),("S","music","音楽は"),
                ("V","works","働く"),("M","(like a cheerful coach).","陽気なコーチのように")],
     "note":"▶ such moments＝前文の「カード整理・書き写し」の場面を指す〔<b>R5</b>〕。work like A＝「Aのように働く」。"},
  ]},
 {"head": "第3段 — 主張への転換：ことばの勉強では話が別（Yet）",
  "sentences": [
    {"chunks": [("接","Yet","だが"),("S","the picture","様子は"),("V","changes","一変する"),
                ("M","(when the study itself uses words).","勉強そのものがことばを使うときには")],
     "note":"▶ <b>R1｜Yet＝逆接。ここが主張への転換点</b>（＝空所B）。itself＝「〜そのもの」の強調。"},
    {"chunks": [("S","Reading long passages, writing essays, and memorizing new words","長い文章を読むこと・エッセイを書くこと・新しい単語を暗記することは"),
                ("M","all","すべて"),("V","depend on","〜に頼っている"),
                ("O","the language system of your brain.","脳の言語システムに")],
     "note":"▶ <b>動名詞（Reading／writing／memorizing）三つの並列</b>が主語。all＝主語全体を受ける同格語。"},
    {"chunks": [("S","A song with lyrics","歌詞のある曲は"),("V","uses","使う"),
                ("O","the very same system.","まさにその同じシステムを")],
     "note":"▶ <b>the very same ～</b>＝「まさにその同じ〜」。the same system＝前文の言語システムを指す〔<b>R5</b>〕。"},
    {"chunks": [("M","In other words,","言い換えれば"),
                ("S","the words in the song and the words in your textbook","歌の中のことばと教科書のことばが"),
                ("V","fight for","取り合う"),("O","the same space","同じ場所を"),
                ("M","(in your head).","頭の中の")],
     "note":"▶ <b>R8｜in other words＝イコール関係の目印</b>。前の二文の言い換え。fight for A＝「Aを求めて争う」。＝<b>下線部(1)＝問3</b>。"},
    {"chunks": [("S","Your brain","脳は"),("V","cannot follow","追うことができない"),
                ("O","two streams of words","二つのことばの流れを"),
                ("M","(at the same time).","同時に")],
     "note":"▶ stream＝「流れ」。下線部(1)の理由を述べる駄目押しの一文（説明記述の核）。"},
  ]},
 {"head": "第4段 — 具体化：研究の知見——危険の正体は歌詞（抽象→具体）",
  "sentences": [
    {"chunks": [("S","Research on reading","読むことに関する研究は"),("V","gives","与えてくれる"),
                ("O","a clear example.","分かりやすい例を")],
     "note":"▶ <b>R4｜ここから具体化</b>。research は一般表現（特定の研究者名は挙げない書き方）。"},
    {"chunks": [("M","(When people read while listening to songs with lyrics),","歌詞のある曲を聴きながら文章を読むと"),
                ("S","they","人は"),("V","tend to read","読みがちになる"),
                ("O","the same lines","同じ行を"),("M","again and again.","何度も繰り返して")],
     "note":"▶ <b>while doing</b>＝「〜しながら」（接続詞＋分詞）。tend to do＝「〜する傾向がある」。問4・問7⑤の根拠。"},
    {"chunks": [("S","They","彼らは"),("M","also","また"),("V","remember","覚えている"),
                ("O","less of [what they have read].","読んだことのより少ない量しか")],
     "note":"▶ <b>関係代名詞 what</b>「〜したこと」〔<b>R11</b>〕。less of A＝「Aのより少ない部分」＝記憶に残る量が減る。"},
    {"chunks": [("S","Music without words,","歌詞のない音楽は"),
                ("-","such as quiet piano pieces,","（例えば静かなピアノ曲のような）"),
                ("V","causes","引き起こす"),("O","much smaller problems.","ずっと小さい問題を")],
     "note":"▶ such as＝例示の挿入。much＋比較級＝比較の強調。問7①を切る根拠。"},
    {"chunks": [("S","Natural sounds,","自然の音は"),("-","like rain or waves,","（雨や波のような）"),
                ("V","seem","〜のようだ"),("C","almost harmless.","ほとんど無害")],
     "note":"▶ seem＋形容詞＝「〜のように見える」。like A＝例示。問4④を切る根拠。"},
    {"chunks": [("S","The real danger,","本当の危険は"),("M","research suggests,","と研究は示唆する"),
                ("V","lies","ある"),("M","mainly (in the lyrics).","主に歌詞に")],
     "note":"▶ research suggests＝挿入。<b>lie in A</b>＝「Aにある」。段落の結論文＝「危険の正体は歌詞」。"},
  ]},
 {"head": "第5段 — 理由②：音楽は「はかどり錯覚」を作る",
  "sentences": [
    {"chunks": [("V","There is","ある"),("S","a second problem:","二つ目の問題が"),
                ("S","music","（すなわち）音楽は"),("V","creates","作り出す"),
                ("O","a false sense of progress.","「はかどっている」という誤った感覚を")],
     "note":"▶ There is 構文。<b>R8｜コロン(:)＝直前の言い換え</b>。a second problem の中身がコロンの後。"},
    {"chunks": [("M","(Because your favorite songs put you in a good mood),","お気に入りの曲があなたを良い気分にさせるので"),
                ("S","the evening","その晩は"),("V","feels","感じられる"),
                ("C","smooth and productive.","なめらかで生産的に")],
     "note":"▶ <b>R6｜Because＝因果</b>（気分アップ→はかどり感）。put A in a good mood＝「Aを良い気分にさせる」。feel＋形容詞。"},
    {"chunks": [("S","You","あなたは"),("V","feel","感じる"),
                ("O","[that you are moving fast],","速く進んでいると"),
                ("M","(even when you are not).","実際にはそうでないときでさえ")],
     "note":"▶ feel that 節。even when …＝「〜ときでさえ」。you are not（moving fast）＝繰り返しの省略。"},
    {"chunks": [("M","In fact,","実のところ"),
                ("S","the feeling of progress and the real result","はかどっている感覚と本当の結果は"),
                ("V","are","である"),("C","two different things.","二つの別のもの")],
     "note":"▶ In fact＝「（見かけに反して）実際は」。感覚≠結果、という段落の核。＝<b>下線部(2)＝問5</b>。"},
    {"chunks": [("S","A pleasant three hours with music","音楽と過ごす心地よい3時間は"),
                ("V","can teach","教えることがある"),("O","you","あなたに"),
                ("O","less","より少ししか"),
                ("M","(than one quiet hour without it).","音楽なしの静かな1時間よりも")],
     "note":"▶ <b>無生物主語＋teach O1 O2</b>＝「（物）からO1はO2を学ぶ」。a ～ three hours＝ひとまとまりの時間は単数扱い。比較 less than …。"},
  ]},
 {"head": "第6段 — 核心的主張：音楽は敵でも味方でもなく道具（not A or B but C）",
  "sentences": [
    {"chunks": [("O","What","何を"),("V","should","〜すべきか"),("S","students","生徒は"),
                ("V","do,","する"),("M","then?","それでは")],
     "note":"▶ 疑問文＝筆者の問題提起。疑問詞 What（do の目的語）が文頭に出て、should が主語の前に出た形（倒置）。"},
    {"chunks": [("S","The answer","答えは"),("V","begins","始まる"),
                ("M","(with a change of view).","ものの見方を変えることから")],
     "note":"▶ begin with A＝「Aから始まる」。a change of view＝次文の「道具」観への転換を予告。"},
    {"chunks": [("S","Music","音楽は"),("V","is","である"),
                ("C","not an enemy or a friend but a tool,","敵でも味方でもなく道具"),
                ("接","and","そして"),("S","[what matters]","大事なことは"),("V","is","である"),
                ("C","[when you use it and when you turn it off].","いつそれを使い、いつそれを止めるか（ということ）")],
     "note":"▶ <b>R3｜not A or B but C＝Cこそ核心</b>。[what matters]＝関係代名詞 what の名詞節が主語〔<b>R11</b>〕。when 節二つ＝「いつ〜か」の名詞節（補語）。＝<b>下線部(3)＝問2（和訳）</b>。"},
    {"chunks": [("S","A hammer","金づちは"),("V","is","である"),("C","perfect","うってつけ"),
                ("M","(for a nail)","くぎには"),("接","but","だが"),
                ("C","useless","役立たず"),("M","(for a screw).","ねじには")],
     "note":"▶ <b>R4｜たとえ（具体）</b>：道具は用途が合うときだけ役に立つ。perfect／useless の対比。"},
    {"chunks": [("S","Music,","音楽も"),("M","too,","また"),("V","works","働く"),
                ("M","(only when the job fits).","仕事（用途）が合うときにだけ")],
     "note":"▶ only when …＝「〜ときにだけ」。金づちのたとえを音楽に戻して核心を締める（＝何のたとえかに戻す〔<b>R4</b>〕）。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：捨てるのではなく、使い分ける",
  "sentences": [
    {"chunks": [("M","Of course,","もちろん"),("S","this","このことは"),
                ("V","does not mean","意味しない"),
                ("O","[that you must throw your music away].","音楽を捨ててしまわなければならないとは")],
     "note":"▶ Of course, …＝譲歩の型。throw A away＝「Aを捨てる」。問7④「完全に捨て去るべき」を切る根拠〔<b>R9</b>〕。"},
    {"chunks": [("M","(During breaks),","休憩中は"),("V","let","させてやれ"),
                ("O","your favorite songs","お気に入りの曲に"),
                ("C","wash your stress away.","ストレスを洗い流す（ように）")],
     "note":"▶ <b>let O do（原形）</b>＝「Oに〜させてやる」。wash A away＝「Aを洗い流す」。使い分け①＝休憩。"},
    {"chunks": [("M","(For simple tasks),","単純な作業では"),("V","use","使え"),("O","music","音楽を"),
                ("M","(to keep your hands moving).","手を動かし続けるために")],
     "note":"▶ 命令文。to keep …＝目的の不定詞「〜するために」。keep O doing＝第2段の再登場。使い分け②＝単純作業。"},
    {"chunks": [("接","But","しかし"),
                ("M","(when you sit down to read, write, or memorize),","読む・書く・覚えるために机に向かうときは"),
                ("V","choose","選べ"),("O","silence","静けさを"),("M","instead.","代わりに")],
     "note":"▶ <b>R1｜But の直後に筆者の核心の指示</b>。to read, write, or memorize＝目的の不定詞3並列。使い分け③＝ことばの勉強。"},
    {"chunks": [("S","Using music well","音楽をうまく使うことは"),("V","is","である"),
                ("C","not a matter of loving it or hating it.","それを愛するか嫌うかの問題ではない")],
     "note":"▶ 動名詞 Using …＝主語。<b>not A</b>（次文の a matter of … が B）＝ not A but B が二文に分かれた形〔<b>R3</b>〕。"},
    {"chunks": [("S","It","それは"),("V","is","である"),
                ("C","a matter of knowing the right time for each.","それぞれにふさわしい時を知っているという問題")],
     "note":"▶ It＝Using music well〔<b>R5</b>〕。<b>B の側＝核心</b>：好き嫌いでなく「時を知る」こと〔<b>R3</b>〕。"},
    {"chunks": [("S","That quiet skill","その静かな技術が"),("V","may raise","高めるかもしれない"),
                ("O","the value of every study hour.","勉強の一時間一時間の価値を")],
     "note":"▶ That quiet skill＝前文の「ふさわしい時を知る」技術を指す〔<b>R5</b>〕。無生物主語。タイトルの問いに答えて締める。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=6文/第2段=5文/第3段=5文/第4段=6文/第5段=5文/第6段=5文/第7段=7文)
SVOC_LOGIC = {
    (1, 5): "対比", (1, 6): "主張",                       # s5 Still→反転 / s6 種類で決まる(見取り図)
    (2, 1): "譲歩", (2, 4): "具体例", (2, 5): "譲歩",       # s1 It is true / s4 カード整理 / s5 コーチ
    (3, 1): "対比", (3, 2): "因果", (3, 4): "主張", (3, 5): "因果",
    (4, 1): "具体例", (4, 2): "具体例", (4, 3): "具体例", (4, 4): "対比", (4, 5): "対比", (4, 6): "主張",
    (5, 1): "主張", (5, 2): "因果", (5, 3): "具体例", (5, 4): "主張", (5, 5): "具体例",
    (6, 3): "主張", (6, 4): "具体例", (6, 5): "主張",
    (7, 1): "譲歩", (7, 2): "具体例", (7, 3): "具体例", (7, 4): "対比", (7, 5): "主張", (7, 6): "主張", (7, 7): "主張",
}
