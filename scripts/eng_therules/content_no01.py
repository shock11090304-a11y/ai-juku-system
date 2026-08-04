# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.01 — 単一ソース
テーマ: The Hidden Value of Boredom (退屈の効用) / MARCH・難関私大 (The Rules 2〜3 相当)
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "01",
    "level": "MARCH レベル",
    "level_sub": "難関私大 / The Rules 2〜3 相当",
    "theme_ja": "退屈の効用",
    "theme_en": "The Hidden Value of Boredom",
    "minutes": 18,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Most of us treat boredom as an enemy to be defeated. The moment a queue stops '
        'moving or a conversation slows, we reach for our phones, filling every empty second '
        'with messages, videos, and news. Boredom feels like wasted time, an itch that must be '
        'scratched at once. <span class="blank">【&nbsp;A&nbsp;】</span>, a growing number of '
        'psychologists argue that this restless flight from boredom may cost us something '
        'valuable. The very state we are so eager to escape, they suggest, quietly does '
        'important work in the mind.'),
    (2, 'It is true that boredom is unpleasant. Researchers describe it as the uncomfortable '
        'feeling of wanting, but being unable, to engage in satisfying activity. It can make '
        'minutes crawl and leave us restless and irritable. In small doses it is harmless, yet '
        'chronic boredom has been linked to stress and to a loss of concentration. No one would '
        'pretend that being bored is enjoyable.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span> boredom is not merely a problem to be '
        'solved. When the mind is left with nothing to focus on, it does not switch off; '
        'instead, it begins to wander. Neuroscientists have found that this wandering activates '
        'a network of the brain that is most active precisely when we are doing nothing in '
        'particular. Far from being idle, the unoccupied mind is quietly busy &mdash; sorting '
        'through memories, imagining the future, and making unexpected connections.'),
    (4, 'This wandering is the soil in which creativity grows. Because a bored mind is free to '
        'drift, it stumbles upon associations that a focused mind would miss. In one well-known '
        'line of research, people who were first asked to perform a dull task &mdash; copying '
        'numbers out of a telephone directory &mdash; went on to produce more original ideas '
        'than those who had been kept busy. The boredom, it seems, had loosened their thinking. '
        '<u>The more thoroughly we fill our idle moments, the fewer chances we give our minds '
        'to make such creative leaps.<sup>(1)</sup></u>'),
    (5, 'Boredom also serves as a signal. Just as hunger tells us to eat, boredom tells us '
        'that our current activity has ceased to feel meaningful, pushing us to look for '
        'something that matters more. It is, in this sense, <u>not a malfunction but a '
        'messenger.<sup>(2)</sup></u> People who allow themselves to feel it are more likely to '
        'reflect on what they truly want and to set off after new goals. Remove the discomfort '
        'too quickly, and we may never hear what it is trying to tell us.'),
    (6, 'The problem, then, is not boredom itself but the way we now respond to it. Because a '
        'cure is always within reach in our pockets, <u>we escape the slightest dullness before '
        'it can do its work,<sup>(3)</sup></u> trading the quiet emptiness of an idle moment '
        'for a stream of stimulation in which no reflection can take root. We have not defeated '
        'boredom; we have simply stopped listening to it.'),
    (7, 'None of this means that we should seek out boredom for its own sake, nor that every '
        'dull moment is a hidden gift. The point is subtler: boredom is not the enemy we '
        'imagine, but a tool we have forgotten how to use. Learning to sit with an empty '
        'moment, rather than filling it the instant it appears, may be one of the quiet skills '
        'that a distracted age most needs to recover.'),
]

# 語数カウント用のプレーン本文 (空所は1語 A/B として数える)
PASSAGE_PLAIN = (
    "Most of us treat boredom as an enemy to be defeated. The moment a queue stops moving or a "
    "conversation slows, we reach for our phones, filling every empty second with messages, "
    "videos, and news. Boredom feels like wasted time, an itch that must be scratched at once. "
    "However, a growing number of psychologists argue that this restless flight from boredom may "
    "cost us something valuable. The very state we are so eager to escape, they suggest, quietly "
    "does important work in the mind. "
    "It is true that boredom is unpleasant. Researchers describe it as the uncomfortable feeling "
    "of wanting, but being unable, to engage in satisfying activity. It can make minutes crawl "
    "and leave us restless and irritable. In small doses it is harmless, yet chronic boredom has "
    "been linked to stress and to a loss of concentration. No one would pretend that being bored "
    "is enjoyable. "
    "Yet boredom is not merely a problem to be solved. When the mind is left with nothing to "
    "focus on, it does not switch off; instead, it begins to wander. Neuroscientists have found "
    "that this wandering activates a network of the brain that is most active precisely when we "
    "are doing nothing in particular. Far from being idle, the unoccupied mind is quietly busy "
    "sorting through memories, imagining the future, and making unexpected connections. "
    "This wandering is the soil in which creativity grows. Because a bored mind is free to drift, "
    "it stumbles upon associations that a focused mind would miss. In one well-known line of "
    "research, people who were first asked to perform a dull task copying numbers out of a "
    "telephone directory went on to produce more original ideas than those who had been kept "
    "busy. The boredom, it seems, had loosened their thinking. The more thoroughly we fill our "
    "idle moments, the fewer chances we give our minds to make such creative leaps. "
    "Boredom also serves as a signal. Just as hunger tells us to eat, boredom tells us that our "
    "current activity has ceased to feel meaningful, pushing us to look for something that "
    "matters more. It is, in this sense, not a malfunction but a messenger. People who allow "
    "themselves to feel it are more likely to reflect on what they truly want and to set off "
    "after new goals. Remove the discomfort too quickly, and we may never hear what it is trying "
    "to tell us. "
    "The problem, then, is not boredom itself but the way we now respond to it. Because a cure is "
    "always within reach in our pockets, we escape the slightest dullness before it can do its "
    "work, trading the quiet emptiness of an idle moment for a stream of stimulation in which no "
    "reflection can take root. We have not defeated boredom; we have simply stopped listening to "
    "it. "
    "None of this means that we should seek out boredom for its own sake, nor that every dull "
    "moment is a hidden gift. The point is subtler: boredom is not the enemy we imagine, but a "
    "tool we have forgotten how to use. Learning to sit with an empty moment, rather than filling "
    "it the instant it appears, may be one of the quiet skills that a distracted age most needs "
    "to recover."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Therefore &nbsp; ② However &nbsp; ③ For example &nbsp; ④ Moreover",
         "【 B 】 &nbsp; ① In short &nbsp; ② Because &nbsp; ③ Yet &nbsp; ④ Similarly",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(1) <span class='en'>The more thoroughly we fill our idle moments, the fewer "
             "chances we give our minds to make such creative leaps.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(2) について、退屈が「故障ではなくメッセンジャー(<span class='en'>not a "
             "malfunction but a messenger</span>)」だとはどういうことか。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で紹介されている「退屈と創造性」に関する研究の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 退屈な作業を先にした人々の方が、忙しく過ごした人々よりも独創的なアイデアを多く生み出した。",
         "② 忙しく過ごした人々の方が、退屈な作業をした人々よりも独創的だった。",
         "③ 退屈は集中力を高め、単調な作業そのものの効率を上げた。",
         "④ 退屈な作業は、その後の思考をかえって硬直させた。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>we escape the slightest dullness before it can do its "
             "work</span> の <span class='en'>its work</span>（退屈の働き）とは何か。本文全体をふまえ、"
             "二つ挙げて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 退屈は完全に無害であり、むしろ積極的に退屈を求めるべきだ。",
         "② 退屈そのものが問題なのではなく、それを即座に埋めて働きを奪う私たちの反応こそが問題であり、退屈は使い方を忘れた「道具」である。",
         "③ 退屈は脳の異常であり、テクノロジーによって取り除くべきものだ。",
         "④ 退屈は創造性を生むのだから、集中を要する作業はできるだけ避けるべきだ。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 私たちは退屈を敵とみなし、スマートフォンなどで空いた時間をすぐに埋めがちだ。",
         "② 心が集中する対象を失うと、脳は活動を止めるのではなく、さまよって記憶の整理や未来の想像などを行う。",
         "③ 退屈な単調作業をした人が、その後より独創的なアイデアを生んだ、という研究がある。",
         "④ 慢性的な退屈であっても、ストレスや集中力の低下とは無関係である。",
         "⑤ 筆者は、退屈それ自体を目的として積極的に求めるべきだと述べている。",
         "⑥ 現代人はテクノロジーによって退屈を完全に克服することに成功した。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ② However　　B ＝ ③ Yet",
     "exp": "A：「退屈＝敵、すぐ埋めるもの」という通念に対し、心理学者が「退屈には価値がある」と"
            "反論する流れ。<b>逆接</b>でつなぐ → However。Therefore（因果）・For example（例示）・"
            "Moreover（追加）は不可。<br>"
            "B：第2段「確かに退屈は不快（＝譲歩）」に対し、第3段は「だが単なる問題ではない」と"
            "主張へ<b>転換</b>する。逆接 → Yet。In short（要約）・Because（理由）・Similarly（類比）は"
            "流れに合わない。 〔<b>解法ルール R7</b>／<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "①",
     "exp": "第4段「people who were first asked to perform a dull task … went on to produce "
            "more original ideas than those who had been kept busy」＝退屈な作業を先にした人の方が、"
            "忙しかった人より独創的なアイデアを多く出した。②は逆、③は本文にない（効率の話ではない）、"
            "④も逆（退屈は思考を<i>ほぐした</i>＝loosened）。 〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "②",
     "exp": "第6段「The problem … is not boredom itself but the way we now respond to it」＋"
            "第7段「boredom is … a tool we have forgotten how to use」と一致。①は第7段「求めるべき"
            "という意味ではない」に反する。③は本文と逆（脳の異常ではなく有用な働き）。④は言い過ぎ"
            "（集中作業を避けよとは述べていない）。 〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・②・③",
     "exp": "④×：慢性的な退屈は「ストレスや集中力の低下」と結びつくと述べている（第2段）。"
            "⑤×：第7段で「退屈それ自体を目的に求めるべきという意味ではない」と明確に否定。"
            "⑥×：第6段「We have not defeated boredom（打ち負かしてなどいない）」に反する。"
            " 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(1)和訳",
     "model": "私たちが暇な（何もしていない）時間を徹底的に埋めれば埋めるほど、心にそうした創造的な"
              "飛躍をさせる機会は、それだけ少なくなる。",
     "points": "▶<b>採点要素</b>：①<b>The 比較級 …, the 比較級 …</b>＝「〜すればするほど（いっそう）…」"
               "の構文訳出／②fill our idle moments＝暇な時間を埋める／③fewer chances to make creative "
               "leaps＝創造的な飛躍をする機会が減る。 〔<b>構文ルール R10</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "退屈は、脳の異常や無駄な状態（＝故障）なのではなく、今の活動がもはや意味を感じられなく"
              "なったことを私たちに知らせ、より意味のあるものを探すよう促す「信号（メッセンジャー）」だ、"
              "ということ。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「AではなくB」の対比を訳に反映／②「故障」＝異常・"
               "無用な状態の否定／③「メッセンジャー」＝〈今の活動が無意味になったと知らせ、意味あるものを"
               "求めさせる信号〉であることを本文（第5段）から補って説明。 〔<b>読解ルール R3</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①心をさまよわせ、集中していては見逃すような結びつきに出会わせて、創造的な発想を生ませること。"
              "②今の活動が意味を失ったことを知らせ、より意味のあるものを探すよう私たちを促すこと。",
     "points": "▶<b>採点要素</b>：本文全体から退屈の「働き」を二つ取り出す。①<b>創造性</b>（第3〜4段：mind-"
               "wandering → creative leaps）／②<b>信号</b>（第5段：意味の喪失を知らせ、意味あるものを探させる）。"
               "各5点。 〔<b>読解ルール R5</b>：指示語 its work の中身を確定〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A・B、第1段（However→研究者の主張）、第3段（Yet→主張転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that boredom is unpleasant」→ 第3段 Yet で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(2) not a malfunction but a messenger、第6段 not boredom itself but the way we respond。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段の電話帳の研究は「退屈→創造性」という抽象の具体例。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "下線部(3) its work＝退屈の二つの働き（創造性＋信号）を指す。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第4段 Because a bored mind is free to drift …、第5段 pushing us to look for …。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。コロン(:)・in other words・not A but B の言い換えを利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。⑥の completely、①の「完全に無害」などは典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R10", "The 比較級 …, the 比較級 … ＝「〜すればするほど（いっそう）…」", "★★",
         "下線部(1)＝問2。The more … , the fewer … を必ず構文で訳出。"),
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "a network of the brain <that is most active …>、the pleasures <bought with money> 型。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「退屈＝敵。空いた時間はすぐ埋めるもの」を提示。→ <b>However（R1）</b>：心理学者は"
             "「退屈は心の中で重要な仕事をしている」と反論。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに退屈は不快で、慢性化すればストレス・集中力低下と"
             "結びつく。＝通念の一部は認める。"},
    {"arrow": "◀ Yet 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "退屈は「単に解決すべき問題」ではない。心は止まらず<b>さまよい</b>、脳のネットワークが"
             "活性化＝無為に見えて静かに忙しい。"},
    {"arrow": "↓　理由①"},
    {"role": "理由①", "para": "¶4", "kind": "reason",
     "text": "<b>創造性</b>：さまよう心は集中では見逃す結びつきに出会う。退屈な作業の後の方が独創的な"
             "アイデアが多かった（研究）。<b>抽象→具体（R4）</b>。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>信号</b>：空腹のように「今の活動は無意味」と知らせ、意味あるものを探させる。"
             "＝<b>not a malfunction but a messenger（R3）</b>。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "問題は退屈ではなく<b>「即座に埋める反応」</b>。<b>its work（R5）</b>＝上の二つの働きを"
             "発揮する前に振り払い、内省・想像の余地を刺激と引き換えにしている。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：退屈を積極的に求めよという話ではない。退屈は敵ではなく<b>「使い方を"
             "忘れた道具」</b>。空の時間に耐える力を取り戻せ。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 退屈への二つの向き合い方",
     "caption": "同じ「退屈」でも、<b>即座に埋める</b>と働きは失われ、<b>そのまま留まる</b>と創造や"
                "気づきが生まれる。現代はポケットの中の「治療法」で、常に左へ流れてしまう。",
     "para": "→ 第1・6・7段"},
    {"id": "fig2", "title": "図2 ｜ 退屈の二つの働き（＝its work）",
     "caption": "退屈が果たす仕事は二つ。①<b>心のさまよい→創造的な発想</b>（第3〜4段）、"
                "②<b>信号→意味の探索</b>（第5段）。下線部(3)の its work はこの二つを指す。",
     "para": "→ 第3〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 退屈は「敵」ではなく「道具」",
     "caption": "問題は退屈そのものではなく<b>反応の仕方</b>。退屈は、なくすものではなく"
                "<b>使い方を思い出す</b>もの——敵ではなく道具。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "私たちの多くは、退屈を打ち負かすべき敵のように扱っている。列が進まなくなったり会話が途切れたり"
        "した瞬間、私たちはスマートフォンに手を伸ばし、空いた一秒一秒を、メッセージや動画やニュースで"
        "埋めてしまう。退屈は無駄な時間、すぐにでも掻かずにはいられないかゆみのように感じられる。"
        "<b>しかし</b>、ますます多くの心理学者が、この退屈からの落ち着かない逃避は、私たちから何か価値"
        "あるものを奪っているかもしれない、と論じている。私たちがそれほどまでに逃れたがっているまさに"
        "その状態こそが、心の中で静かに重要な仕事をしている、と彼らは言うのだ。"),
    (2, "確かに、退屈は不快である。研究者はそれを、満足のいく活動に取り組みたいのに取り組めない、という"
        "居心地の悪い感情だと説明する。退屈は時間をのろのろと這わせ、私たちを落ち着かなくさせ、苛立たせる。"
        "少量であれば無害だが、慢性的な退屈はストレスや集中力の低下と結びつけられてきた。退屈であることが"
        "楽しいなどと、誰も言い張りはしないだろう。"),
    (3, "<b>だが</b>、退屈は単に解決すべき問題であるだけではない。心が集中する対象を何も与えられずに置か"
        "れると、それは活動を止めてしまうのではなく、むしろさまよい始める。神経科学者たちは、このさまよいが、"
        "私たちが特に何もしていないときにこそ最も活発になる脳のネットワークを活性化させることを突き止めた。"
        "無為であるどころか、使われていない心は、記憶を整理し、未来を想像し、思いがけない結びつきを作りながら、"
        "静かに忙しく働いているのである。"),
    (4, "このさまよいこそが、創造性が育つ土壌である。退屈した心は自由に漂えるからこそ、集中した心なら見逃して"
        "しまうような結びつきに、ふと出会う。ある有名な一連の研究では、まず退屈な作業——電話帳から番号を書き"
        "写す作業——をさせられた人々の方が、忙しく過ごさせられた人々よりも、そのあと独創的なアイデアを多く生み"
        "出した。退屈が、彼らの思考をほぐしていたようなのだ。<b>私たちが暇な時間を徹底的に埋めれば埋めるほど、"
        "心にそうした創造的な飛躍をさせる機会は、それだけ少なくなる。</b>"),
    (5, "退屈はまた、信号としても働く。ちょうど空腹が「食べよ」と告げるように、退屈は、今の活動がもはや意味を"
        "感じさせなくなったことを私たちに告げ、より意味のあるものを探すよう駆り立てる。その意味で退屈は、"
        "<b>故障ではなくメッセンジャー</b>なのである。退屈を自分に感じさせてやれる人ほど、自分が本当に望むものを"
        "見つめ直し、新たな目標に向かって動き出しやすい。その不快さを急いで取り除いてしまえば、退屈が伝えようと"
        "していることを、私たちは決して聞き取れないかもしれない。"),
    (6, "とすると問題は、退屈そのものではなく、今日の私たちのその向き合い方にある。まぎらす手段が常にポケットの"
        "中の手の届くところにあるために、<b>私たちはほんのわずかな退屈さえも、それが自らの仕事をやり遂げる前に</b>"
        "振り払ってしまう——暇な瞬間の静かな空白を、いかなる内省も根づくことのできない刺激の流れと引き換えにして。"
        "私たちは退屈を打ち負かしたのではない。ただ、それに耳を傾けるのをやめてしまっただけなのだ。"),
    (7, "とはいえ以上のことは、退屈それ自体を目的として求めるべきだとか、どの退屈な瞬間にも隠れた贈り物があると"
        "か、いう意味ではない。要点はもっと微妙だ。すなわち、退屈は私たちが思い込んでいるような敵ではなく、使い方を"
        "忘れてしまった道具なのだ。空いた瞬間を、現れた途端に埋めてしまうのではなく、そのまま共に過ごすことを学ぶ"
        "——それは、気の散りやすいこの時代が取り戻すべき、静かな技能の一つなのかもしれない。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("treat A as B", "AをBとして扱う"),
    ("an itch that must be scratched", "掻かずにはいられないかゆみ"),
    ("restless", "落ち着かない、そわそわした"),
    ("flight from ~", "〜からの逃避"),
    ("be eager to do", "しきりに〜したがる"),
    ("unpleasant", "不快な"),
    ("engage in ~", "〜に取り組む・従事する"),
    ("crawl", "のろのろ進む、這う"),
    ("irritable", "苛立ちやすい"),
    ("chronic", "慢性的な"),
    ("be linked to ~", "〜と結びついている"),
    ("switch off", "活動を止める、電源を切る"),
    ("wander", "さまよう、とりとめなく動く"),
    ("idle", "無為の、何もしていない、暇な"),
    ("stumble upon ~", "〜に偶然出会う"),
    ("loosen", "緩める、ほぐす"),
    ("serve as ~", "〜として働く・役立つ"),
    ("cease to do", "〜しなくなる"),
    ("malfunction", "故障、不具合"),
    ("within reach", "手の届く所に"),
    ("take root", "根づく、定着する"),
    ("for its own sake", "それ自体を目的として"),
    ("distracted", "気の散った、注意をそがれた"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 問題提起：退屈＝敵という通念と、その反転",
  "sentences": [
    {"chunks": [("S","Most of us","私たちの多くは"),("V","treat","扱う"),
                ("O","boredom","退屈を"),("C","as an enemy &lt;to be defeated&gt;","打ち負かすべき敵として")],
     "note":"▶ <b>treat A as B</b>＝「AをBとして扱う」。to be defeated＝不定詞（受動）で enemy を修飾。"},
    {"chunks": [("M","The moment (a queue stops moving or a conversation slows),","列が進まなくなったり会話が途切れたりした瞬間に"),
                ("S","we","私たちは"),("V","reach for","手を伸ばす"),("O","our phones,","スマホに"),
                ("M","filling every empty second (with messages, videos, and news).","空いた一秒一秒をメッセージ・動画・ニュースで埋めながら")],
     "note":"▶ <b>The moment SV</b>＝接続詞的「〜する瞬間に」。filling …＝分詞構文（付帯状況）。"},
    {"chunks": [("S","Boredom","退屈は"),("V","feels like","〜のように感じられる"),
                ("C","wasted time,","無駄な時間"),("-","an itch &lt;that must be scratched at once&gt;.","＝すぐ掻かねばならないかゆみ")],
     "note":"▶ feel like＋名詞。an itch …＝直前の言い換え（<b>同格</b>）。that …＝関係代名詞。"},
    {"chunks": [("接","However,","しかし"),("S","a growing number of psychologists","ますます多くの心理学者が"),
                ("V","argue","論じる"),("O","[that this restless flight from boredom may cost us something valuable].","この退屈からの落ち着かない逃避は、私たちから何か価値あるものを奪うかもしれない、と")],
     "note":"▶ <b>R1｜逆接 However の直後が主張</b>（＝空所A）。argue that …。cost O1 O2＝「O1からO2を奪う」。"},
    {"chunks": [("S","The very state &lt;(that) we are so eager to escape&gt;,","私たちがそれほど逃れたがっているまさにその状態こそが"),
                ("M","they suggest,","と彼らは言う"),("V","quietly does","静かにしている"),
                ("O","important work","重要な仕事を"),("M","(in the mind).","心の中で")],
     "note":"▶ the very state＝「まさにその状態」。we are eager to escape は関係詞省略（escape の目的語が state）。they suggest は挿入。"},
  ]},
 {"head": "第2段 — 譲歩：確かに退屈は不快だ（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当だ"),
                ("-","[that boredom is unpleasant].","退屈が不快であるということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。形式主語 It＝真主語 that 節。後に逆接（第3段 Yet）が来る前振り。"},
    {"chunks": [("S","Researchers","研究者は"),("V","describe","説明する"),("O","it","それを"),
                ("C","as the uncomfortable feeling &lt;of wanting, but being unable, to engage in satisfying activity&gt;.","満足のいく活動に取り組みたいのに取り組めない、という不快な感情として")],
     "note":"▶ <b>describe A as B</b>。of wanting … to engage / but being unable（挿入）＝「〜したいが、できない」。"},
    {"chunks": [("S","It","それは"),("V","can make","させうる"),("O","minutes","時間（分）を"),("C","crawl","のろのろ這う（ように）"),
                ("接","and","そして"),("V","leave","させる"),("O","us","私たちを"),("C","restless and irritable.","落ち着かず苛立った状態に")],
     "note":"▶ 使役 <b>make O do</b>／<b>leave O C</b>。一つの主語 It が make と leave の二つの動詞を取る。"},
    {"chunks": [("M","(In small doses)","少量なら"),("S","it","それは"),("V","is","である"),("C","harmless,","無害"),
                ("接","yet","だが"),("S","chronic boredom","慢性的な退屈は"),("V","has been linked","結びつけられてきた"),
                ("M","(to stress and to a loss of concentration).","ストレスや集中力の低下と")],
     "note":"▶ <b>yet</b>＝逆接。be linked to A＝「Aと結びつく」。ここで「慢性の退屈は害」も一応認める（譲歩の一部）。"},
    {"chunks": [("S","No one","誰も〜ない"),("V","would pretend","ふりはしないだろう"),
                ("O","[that being bored is enjoyable].","退屈であることが楽しいとは")],
     "note":"▶ 動名詞 being bored＝that 節内の主語。「退屈が快いとは誰も言い張らない」＝不快さを認める駄目押し。"},
  ]},
 {"head": "第3段 — 主張の転換：退屈は「単なる問題」ではない（Yet）",
  "sentences": [
    {"chunks": [("接","Yet","だが"),("S","boredom","退屈は"),("V","is","である"),
                ("C","not merely a problem &lt;to be solved&gt;.","単に解決すべき問題であるだけではない")],
     "note":"▶ <b>R1｜Yet＝逆接でここが主張転換点</b>（＝空所B）。<b>not merely …</b>＝「単に〜なだけではない」（この後に働きが続く）。"},
    {"chunks": [("M","(When the mind is left with nothing &lt;to focus on&gt;),","心が集中する対象を何も与えられずに置かれると"),
                ("S","it","それは"),("V","does not switch off;","活動を止めるのではない"),
                ("接","instead,","むしろ"),("S","it","それは"),("V","begins to wander.","さまよい始める")],
     "note":"▶ be left with nothing to focus on＝「集中する対象がない状態に置かれる」。switch off＝「（機能を）止める」。instead で対比。"},
    {"chunks": [("S","Neuroscientists","神経科学者は"),("V","have found","突き止めた"),
                ("O","[that this wandering activates a network of the brain &lt;that is most active (precisely when we are doing nothing in particular)&gt;].","このさまよいが、私たちが特に何もしていないときにこそ最も活発になる脳のネットワークを活性化させる、ということを")],
     "note":"▶ <b>R11｜関係詞は名詞を後ろから説明</b>。that is most active …＝a network を修飾。when …＝副詞節。"},
    {"chunks": [("M","(Far from being idle),","無為であるどころか"),("S","the unoccupied mind","使われていない心は"),
                ("V","is","である"),("C","quietly busy","静かに忙しい"),
                ("M","&mdash; sorting through memories, imagining the future, and making unexpected connections.","記憶を整理し、未来を想像し、思いがけない結びつきを作りながら")],
     "note":"▶ <b>Far from doing</b>＝「〜どころか（決して〜でない）」。sorting / imagining / making＝三つの分詞が並列（付帯状況）。"},
  ]},
 {"head": "第4段 — 理由①：さまよい → 創造性（抽象→具体）",
  "sentences": [
    {"chunks": [("S","This wandering","このさまよいこそが"),("V","is","である"),
                ("C","the soil &lt;in which creativity grows&gt;.","創造性が育つ土壌")],
     "note":"▶ in which＝「前置詞＋関係代名詞」（＝where）。the soil を後ろから説明。"},
    {"chunks": [("接","Because","〜なので"),("S","a bored mind","退屈した心は"),("V","is free to drift,","自由に漂える"),
                ("S","it","それは"),("V","stumbles upon","偶然出会う"),
                ("O","associations &lt;that a focused mind would miss&gt;.","集中した心なら見逃すような結びつきに")],
     "note":"▶ <b>R6｜Because＝因果</b>。stumble upon＝「偶然出会う」。that …＝関係代名詞（miss の目的語）。"},
    {"chunks": [("M","(In one well-known line of research),","ある有名な一連の研究では"),
                ("S","people &lt;who were first asked to perform a dull task&gt;","まず退屈な作業をするよう求められた人々が"),
                ("-","&mdash; copying numbers out of a telephone directory &mdash;","（電話帳から番号を書き写す作業）"),
                ("V","went on to produce","続いて生み出した"),("O","more original ideas","より独創的なアイデアを"),
                ("M","(than those &lt;who had been kept busy&gt;).","忙しくさせられていた人々よりも")],
     "note":"▶ <b>R4｜抽象→具体</b>：この研究は「退屈→創造性」の具体例。go on to do＝「続けて〜する」。比較 more … than those who …。ダッシュ間は task の同格説明。"},
    {"chunks": [("S","The boredom,","その退屈が"),("M","it seems,","どうやら"),
                ("V","had loosened","ほぐしていた（ようだ）"),("O","their thinking.","彼らの思考を")],
     "note":"▶ it seems は挿入。過去完了 had loosened＝生み出した時点より前に「ほぐしていた」。"},
    {"chunks": [("M","The more thoroughly","より徹底的に"),("S","we","私たちが"),("V","fill","埋める"),("O","our idle moments,","暇な時間を"),
                ("O","the fewer chances","より少ない機会（しか）"),("S","we","私たちは"),("V","give","与えない"),("O","our minds","心に"),
                ("M","&lt;to make such creative leaps&gt;.","〔そうした創造的飛躍をする（機会）〕")],
     "note":"▶ <b>R10｜The 比較級 …, the 比較級 …</b>＝「〜すればするほど…」。give O1 O2（O1＝our minds／O2＝chances）の O2 が The 比較級として文頭に出た形。to make …＝chances を修飾する不定詞（離れた修飾）。＝<b>下線部(1)＝問2</b>。"},
  ]},
 {"head": "第5段 — 理由②：退屈は信号（not a malfunction but a messenger）",
  "sentences": [
    {"chunks": [("S","Boredom","退屈は"),("M","also","また"),("V","serves as","〜として働く"),("C","a signal.","信号")],
     "note":"▶ serve as A＝「Aとして働く・役立つ」。理由②の主題提示。"},
    {"chunks": [("M","(Just as hunger tells us to eat),","ちょうど空腹が私たちに食べよと告げるように"),
                ("S","boredom","退屈は"),("V","tells","告げる"),("O","us","私たちに"),
                ("O","[that our current activity has ceased to feel meaningful],","今の活動がもはや意味を感じさせなくなった、と"),
                ("M","pushing us to look for something &lt;that matters more&gt;.","そして、より意味あるものを探すよう私たちを駆り立てながら")],
     "note":"▶ <b>Just as …</b>＝「ちょうど〜のように」（類比）。cease to do＝「〜しなくなる」。pushing …＝分詞構文（<b>R6</b>因果）。that matters more＝関係代名詞。"},
    {"chunks": [("S","It","それは"),("M","in this sense,","この意味で"),("V","is","である"),
                ("C","not a malfunction but a messenger.","故障ではなくメッセンジャー")],
     "note":"▶ <b>R3｜not A but B＝Bこそ主張</b>。故障（＝異常・無用）を否定し、「信号（messenger）」だと言い切る。＝<b>下線部(2)＝問3</b>。"},
    {"chunks": [("S","People &lt;who allow themselves to feel it&gt;","退屈を自分に感じさせてやる人々は"),
                ("V","are more likely to","〜する可能性が高い"),
                ("C","reflect on [what they truly want] and to set off after new goals.","自分が本当に望むものを見つめ直し、新たな目標を追い求め始める")],
     "note":"▶ be likely to do。allow oneself to do＝「自分に〜させてやる」。what they truly want＝関係代名詞 what。set off after＝「〜を求めて動き出す」。"},
    {"chunks": [("V","Remove","取り除け"),("O","the discomfort","その不快さを"),("M","too quickly,","急ぎすぎて"),
                ("接","and","そうすれば"),("S","we","私たちは"),("V","may never hear","決して聞けないかもしれない"),
                ("O","[what it is trying to tell us].","それが伝えようとしていることを")],
     "note":"▶ <b>命令文 + and …</b>＝「〜せよ、そうすれば…」。what it is trying to tell us＝間接疑問／関係代名詞 what。"},
  ]},
 {"head": "第6段 — 核心的主張：問題は退屈でなく「反応」（its work）",
  "sentences": [
    {"chunks": [("S","The problem,","問題は"),("M","then,","では"),("V","is","である"),
                ("C","not boredom itself but the way &lt;(that) we now respond to it&gt;.","退屈そのものではなく、今の私たちのそれへの反応の仕方")],
     "note":"▶ <b>R3｜not A but B</b>：核心は B（反応の仕方）。the way (that) we respond＝関係副詞省略。"},
    {"chunks": [("接","Because","〜なので"),("S","a cure","治療法（＝退屈をまぎらす手段）が"),("V","is","ある"),
                ("M","always within reach in our pockets,","常にポケットの中の手の届く所に"),
                ("S","we","私たちは"),("V","escape","逃れる"),("O","the slightest dullness","ほんのわずかな退屈さえ"),
                ("M","(before it can do its work),","それが自らの働きをやり遂げる前に"),
                ("M","trading the quiet emptiness of an idle moment for a stream of stimulation &lt;in which no reflection can take root&gt;.","暇な瞬間の静かな空白を、いかなる内省も根づけない刺激の流れと引き換えにしながら")],
     "note":"▶ <b>R5｜its work＝退屈の二つの働き（創造性＋信号）を指す</b>。within reach＝「手の届く所に」。<b>trade A for B</b>＝「AをBと引き換えにする」。take root＝「根づく」。＝<b>下線部(3)＝問5</b>。"},
    {"chunks": [("S","We","私たちは"),("V","have not defeated","打ち負かしてはいない"),("O","boredom;","退屈を"),
                ("S","we","私たちは"),("V","have simply stopped","ただやめただけだ"),("O","listening to it.","それに耳を傾けるのを")],
     "note":"▶ <b>R9注意</b>：「打ち負かしていない」＝設問⑥「完全に克服した」は<b>言い過ぎ</b>で×。stop doing＝「〜するのをやめる」。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：退屈は「使い方を忘れた道具」",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),("V","means","意味しない"),
                ("O","[that we should seek out boredom for its own sake],","退屈それ自体を目的に求めるべきだとは"),
                ("接","nor","〜でもない"),("O","[that every dull moment is a hidden gift].","どの退屈な瞬間も隠れた贈り物だとも")],
     "note":"▶ None of this means that …, nor that …。<b>R9注意</b>：これが設問①「積極的に求めるべき」を否定する根拠。for its own sake＝「それ自体を目的に」。"},
    {"chunks": [("S","The point","要点は"),("V","is","である"),("C","subtler:","もっと微妙"),
                ("S","boredom","（すなわち）退屈は"),("V","is","である"),
                ("C","not the enemy &lt;(that) we imagine&gt;, but a tool &lt;(that) we have forgotten how to use&gt;.","私たちが思うような敵ではなく、使い方を忘れてしまった道具")],
     "note":"▶ <b>R8｜コロン(:)＝直前の言い換え</b>。<b>R3｜not A but B</b>：核心＝「道具」。we imagine / we have forgotten how to use はいずれも関係詞省略。"},
    {"chunks": [("S","Learning to sit with an empty moment,","空の瞬間をそのまま共に過ごすことを学ぶことは"),
                ("M","rather than filling it (the instant it appears),","現れた途端にそれを埋めるのではなく"),
                ("V","may be","かもしれない"),
                ("C","one of the quiet skills &lt;that a distracted age most needs to recover&gt;.","気の散りやすい時代が最も取り戻す必要のある、静かな技能の一つ")],
     "note":"▶ 動名詞 Learning …＝主語。rather than doing＝「〜するのではなく」。the instant SV＝接続詞的「〜する途端に」。that …＝関係代名詞（recover の目的語）。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=5文/第2段=5文/第3段=4文/第4段=5文/第5段=5文/第6段=3文/第7段=3文)
SVOC_LOGIC = {
    (1, 4): "対比", (1, 5): "主張",              # s4 However→反論 / s5 重要な仕事をしている
    (2, 1): "譲歩", (2, 4): "対比", (2, 5): "譲歩",  # s1 It is true / s4 yet chronic / s5 駄目押し
    (3, 1): "対比", (3, 2): "対比", (3, 3): "具体例", (3, 4): "主張",
    (4, 1): "主張", (4, 2): "因果", (4, 3): "具体例", (4, 4): "因果", (4, 5): "主張",
    (5, 1): "主張", (5, 2): "因果", (5, 3): "主張", (5, 4): "因果", (5, 5): "因果",
    (6, 1): "主張", (6, 2): "因果", (6, 3): "主張",
    (7, 1): "譲歩", (7, 2): "主張", (7, 3): "主張",
}
