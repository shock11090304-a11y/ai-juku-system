# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.04 — 単一ソース
テーマ: Why Sleep Is Not Wasted Time (眠りは時間の無駄ではない) / MARCH・難関私大 (The Rules 2〜3 相当)
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "04",
    "level": "MARCH レベル",
    "level_sub": "難関私大 / The Rules 2〜3 相当",
    "theme_ja": "眠りは時間の無駄ではない",
    "theme_en": "Why Sleep Is Not Wasted Time",
    "minutes": 18,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Among students preparing for examinations, sleep has a poor reputation. It is widely '
        'treated as a blank stretch of time in which nothing happens &mdash; hours that could '
        'have gone into one more practice paper. In this atmosphere, cutting back on sleep can '
        'even look admirable &mdash; proof, many seem to believe, that you are serious about '
        'your goal. <span class="blank">【&nbsp;A&nbsp;】</span>, sleep scientists take a very '
        'different view. What looks like stillness from the outside, they argue, hides some of '
        'the busiest hours the brain ever has.'),
    (2, 'It is true that waking hours are precious. A student facing an examination has only so '
        'many evenings, and squeezing an extra hour of study out of each looks entirely '
        'reasonable. An hour asleep produces no notes and no finished exercises &mdash; nothing '
        'that can be counted. Measured by what we can see, staying awake seems the obvious '
        'choice.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, a sleeping brain is not a brain at rest. '
        'Its cells keep working busily through the night; far from pausing, the brain is '
        'finishing tasks that the day left undone. Chief among these tasks is the handling of '
        'memory. During sleep, research suggests, the brain sorts through what was learned '
        'during the day; it strengthens what matters and lets the trivial fade &mdash; in '
        'short, it decides what deserves a place in long-term memory. In this respect it '
        'behaves like <u>a librarian working after closing time<sup>(1)</sup></u>, placing the '
        'day&rsquo;s new arrivals on the right shelves.'),
    (4, 'This nightly sorting has a consequence that every learner can use. In a familiar kind '
        'of experiment, people who study new material and then sleep remember it better the '
        'next day than those who stay up all night with the same material. The all-night group '
        'may feel that they have gained time; in reality, researchers say, much of what those '
        'hours put in has already leaked away. Learning, it seems, is completed not at the desk '
        'but on the pillow.'),
    (5, 'Memory is not the only thing the night looks after. Sleep also repairs the machinery '
        'of attention and settles the emotions stirred up during the day. After a full night we '
        'concentrate longer and meet small frustrations with patience; after a short one, the '
        'opposite happens. Because attention is the gate through which everything we study must '
        'pass, cutting sleep weakens the very capacity we need to hold on to what we learn. A '
        'tired brain does not simply feel unpleasant &mdash; it keeps less.'),
    (6, 'Seen in this light, the hours we give to sleep deserve a different name. <u>Sleep, '
        'researchers increasingly argue, is not lost time but a form of investment &mdash; a '
        'payment the brain demands before it will turn today&rsquo;s effort into '
        'tomorrow&rsquo;s ability.<sup>(2)</sup></u> When we shorten the night to win an hour '
        'at the desk, we are not adding to our studies; we are canceling <u>the services we '
        'were counting on<sup>(3)</sup></u>, and we pay for it the next day.'),
    (7, 'None of this means that longer sleep always brings better results. Sleep beyond what '
        'the body asks for earns no extra reward. The real target of the argument is a habit of '
        'mind: our admiration for those who boast of studying until dawn. If the night is when '
        'effort becomes ability, the courage to cut sleep is no virtue &mdash; it is a polite '
        'way of undoing our own work. The question worth asking before an examination is not '
        'how long we can stay awake, but how much we let the night do for us.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Among students preparing for examinations, sleep has a poor reputation. It is widely "
    "treated as a blank stretch of time in which nothing happens hours that could have gone "
    "into one more practice paper. In this atmosphere, cutting back on sleep can even look "
    "admirable proof, many seem to believe, that you are serious about your goal. And yet, "
    "sleep scientists take a very different view. What looks like stillness from the outside, "
    "they argue, hides some of the busiest hours the brain ever has. "
    "It is true that waking hours are precious. A student facing an examination has only so "
    "many evenings, and squeezing an extra hour of study out of each looks entirely reasonable. "
    "An hour asleep produces no notes and no finished exercises nothing that can be counted. "
    "Measured by what we can see, staying awake seems the obvious choice. "
    "Even so, a sleeping brain is not a brain at rest. Its cells keep working busily through "
    "the night; far from pausing, the brain is finishing tasks that the day left undone. Chief "
    "among these tasks is the handling of memory. During sleep, research suggests, the brain "
    "sorts through what was learned during the day; it strengthens what matters and lets the "
    "trivial fade in short, it decides what deserves a place in long-term memory. In this "
    "respect it behaves like a librarian working after closing time, placing the day's new "
    "arrivals on the right shelves. "
    "This nightly sorting has a consequence that every learner can use. In a familiar kind of "
    "experiment, people who study new material and then sleep remember it better the next day "
    "than those who stay up all night with the same material. The all-night group may feel that "
    "they have gained time; in reality, researchers say, much of what those hours put in has "
    "already leaked away. Learning, it seems, is completed not at the desk but on the pillow. "
    "Memory is not the only thing the night looks after. Sleep also repairs the machinery of "
    "attention and settles the emotions stirred up during the day. After a full night we "
    "concentrate longer and meet small frustrations with patience; after a short one, the "
    "opposite happens. Because attention is the gate through which everything we study must "
    "pass, cutting sleep weakens the very capacity we need to hold on to what we learn. A "
    "tired brain does not simply feel unpleasant it keeps less. "
    "Seen in this light, the hours we give to sleep deserve a different name. Sleep, "
    "researchers increasingly argue, is not lost time but a form of investment a payment the "
    "brain demands before it will turn today's effort into tomorrow's ability. When we shorten "
    "the night to win an hour at the desk, we are not adding to our studies; we are canceling "
    "the services we were counting on, and we pay for it the next day. "
    "None of this means that longer sleep always brings better results. Sleep beyond what the "
    "body asks for earns no extra reward. The real target of the argument is a habit of mind: "
    "our admiration for those who boast of studying until dawn. If the night is when effort "
    "becomes ability, the courage to cut sleep is no virtue it is a polite way of undoing our "
    "own work. The question worth asking before an examination is not how long we can stay "
    "awake, but how much we let the night do for us."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① As a result &nbsp; ② For instance &nbsp; ③ And yet &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① Likewise &nbsp; ② Even so &nbsp; ③ Therefore &nbsp; ④ For example",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(2) <span class='en'>Sleep, researchers increasingly argue, is not lost time "
             "but a form of investment &mdash; a payment the brain demands before it will turn "
             "today&rsquo;s effort into tomorrow&rsquo;s ability.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) について、眠っている脳が「閉館後に働く図書館司書（<span class='en'>a "
             "librarian working after closing time</span>）」のようだとはどういうことか。本文に即して"
             "日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で紹介されている「学習と睡眠」に関する実験の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 徹夜で学習を続けた人々の方が、眠った人々よりも翌日の記憶の成績が良かった。",
         "② 新しく学んだ後に眠っても眠らなくても、翌日の記憶にはほとんど差がなかった。",
         "③ 睡眠は覚えている量を増やす一方で、学んだ内容の正確さを大きく下げていた。",
         "④ 学んだ後に眠った人々の方が、徹夜をした人々よりも翌日よく覚えていた。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>the services we were counting on</span> の「サービス"
             "（<span class='en'>services</span>）」とは何か。本文全体をふまえ、二つ挙げて日本語で"
             "説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 睡眠は脳が今日の努力を明日の能力に変える「投資」であり、眠りを削る勇気を称える発想こそ問い直すべきだ。",
         "② 長く眠れば眠るほど学習の成果は必ず上がるのだから、勉強の時間を削ってでも睡眠を延ばすべきである。",
         "③ 睡眠の効用はまだ科学的に確かめられていない以上、試験の前は起きて勉強する方がずっと合理的である。",
         "④ 睡眠は心身の回復には役立つものの、記憶の定着とはほとんど関係がない、と筆者は考えている。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 睡眠を削って勉強に充てることを、目標に真剣である証しとして立派だとみなすような空気が存在する。",
         "② 筆者によれば、眠っている間の脳は完全に活動を停止し、翌朝まで休んでいる。",
         "③ 眠っている間に脳は日中に学んだことを整理し、重要なものを長期記憶に残す。",
         "④ たとえ睡眠を削っても、学んだ内容を保持する力が下がることは決してない。",
         "⑤ 体が求める以上に長く眠るほど、さらに大きな見返りが得られると筆者は述べている。",
         "⑥ 筆者は、夜明けまで勉強したと誇る人々への称賛のまなざしそのものを疑っている。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ③ And yet　　B ＝ ② Even so",
     "exp": "A：「睡眠＝空白の時間。削るのが立派」という通念に対し、睡眠科学者が「まったく異なる見方」で"
            "反論する流れ。<b>逆接</b>でつなぐ → And yet。As a result（因果）・For instance（例示）・"
            "In addition（追加）は不可。<br>"
            "B：第2段「確かに起きている時間は貴重（＝譲歩）」を受けて、第3段は「それでも眠る脳は止まって"
            "いない」と主張へ<b>転換</b>する。譲歩を受けて反転する Even so。Likewise（類比）・Therefore"
            "（因果）・For example（例示）は流れに合わない。 〔<b>解法ルール R7</b>／<b>読解ルール "
            "R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "④",
     "exp": "第4段「people who study new material and then sleep remember it better the next day "
            "than those who stay up all night」＝学んでから眠った人の方が、徹夜した人より翌日よく覚えて"
            "いた。①は逆、②は「差がなかった」で本文に反する、③の「正確さを下げた」は本文にない。 "
            "〔<b>読解ルール R4</b>／<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "①",
     "exp": "第6段「not lost time but a form of investment ＝ 今日の努力を明日の能力に変える前に脳が"
            "要求する支払い」＋第7段「the courage to cut sleep is no virtue（眠りを削る勇気は美徳では"
            "ない）」と一致。②は言い過ぎ（第7段「長いほど良い結果になるという意味ではない」に反する）。"
            "③は逆（筆者は研究知見を根拠に睡眠の働きを認めている）。④も逆（記憶の定着こそ議論の中心）。 "
            "〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・③・⑥",
     "exp": "②×：第3段「a sleeping brain is not a brain at rest ／ Its cells keep working busily」"
            "に反する（「完全に停止」は<b>言い過ぎ</b>）。④×：第5段「cutting sleep weakens the very "
            "capacity we need to hold on to what we learn」に反する（「決してない」は<b>言い過ぎ</b>）。"
            "⑤×：第7段「Sleep beyond what the body asks for earns no extra reward（体が求める以上の"
            "睡眠に追加の見返りはない）」に反する。 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」"
            "の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(2)和訳",
     "model": "睡眠は、失われた時間ではなく一種の投資——すなわち、今日の努力を明日の能力へと変えるのに"
              "先立って脳が要求する支払い——なのだ、と研究者たちはますます強く論じている。",
     "points": "▶<b>採点要素</b>：①挿入 <b>researchers increasingly argue</b> を括弧に入れ、Sleep is "
               "not A but B という骨格を先に取って訳す〔<b>構文ルール R17</b>〕／②<b>not lost time but "
               "a form of investment</b>＝「失われた時間ではなく（一種の）投資」の対比〔<b>読解ルール "
               "R3</b>〕／③ダッシュ以下＝investment の言い換え（a payment … before it will turn A "
               "into B＝AをBに変える前に要求する支払い）を訳出〔<b>読解ルール R16</b>〕。"},
    {"no": "問3", "pts": "8点・記述",
     "model": "眠っている間の脳は活動を止めているのではなく、閉館後の図書館で司書が新着の本を正しい棚に"
              "並べるように、日中に学んだ情報を整理して、重要なものを強め些細なものは消し、長期記憶に"
              "残す価値のあるものを選び分けている、ということ。",
     "points": "▶<b>採点要素</b>：①比喩の中身を直前の文（第3段第4文）から補う——セミコロン・ダッシュは"
               "直前の言い換え・具体化の合図〔<b>読解ルール R16</b>／<b>解法ルール R8</b>〕／②「日中に"
               "学んだことを整理・選別する」／③「重要なものを長期記憶へ残す（些細なものは消す）」の"
               "二つの内容。",},
    {"no": "問5", "pts": "10点・記述",
     "model": "①日中に学んだことを眠っている間に整理し、重要なものを長期記憶へ定着させる働き。"
              "②注意力を回復させ、日中にかき乱された感情を鎮めるという、心身を整える働き。",
     "points": "▶<b>採点要素</b>：第6段の the services（＝夜が私たちのためにしてくれる仕事）の中身を、"
               "本文全体から二つ取り出す。①<b>記憶の整理・定着</b>（第3〜4段：sort through → long-term "
               "memory）／②<b>注意・感情のメンテナンス</b>（第5段：repairs the machinery of attention "
               "and settles the emotions）。各5点。 〔<b>解法ルール R8</b>：言い換えのイコール関係で核を"
               "作る〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（And yet→睡眠科学者の反論）、空所B（Even so→主張転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that waking hours are precious」→ 第3段 Even so で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(2) not lost time but a form of investment、第4段 not at the desk but on the pillow。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段の「学んで眠る vs 徹夜」の実験は、第3段「夜の整理→定着」という抽象の具体例。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第5段 Because attention is the gate … → 睡眠を削ると保持する力そのものが弱まる。"),
        ("R16", "★NEW セミコロン(;)・ダッシュ(—)は直前の言い換え・具体化の合図", "★★★",
         "第3段「; it strengthens … &mdash; in short, …」、下線部(2)のダッシュ以下＝investment の言い換え。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。セミコロン・ダッシュ・コロンの言い換え（R16）を核に使う。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。②「完全に停止」・④「決してない」・「長いほど必ず上がる」は典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "a blank stretch of time &lt;in which nothing happens&gt;、the emotions &lt;stirred up during the day&gt; 型。"),
        ("R17", "★NEW 挿入（コンマに挟まれた researchers say / it seems 等）は括弧に入れて、先に文の骨格（SVOC）を取る", "★★★",
         "下線部(2) Sleep, researchers increasingly argue, is …／第4段 in reality, researchers say ／ Learning, it seems, …。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「睡眠＝何も起きない空白。削って勉強に回すのが偉い」を提示。→ <b>And yet（R1）</b>："
             "睡眠科学者は「外からは静止に見えるものが、脳の最も忙しい時間を隠している」と反論。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに起きている時間は貴重。眠る1時間は目に見える成果を"
             "何も生まず、起きている方が合理的に<i>見える</i>。＝通念の一部は認める。"},
    {"arrow": "◀ Even so 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "眠る脳は休止していない——昼が残した仕事を仕上げている。理由①＝<b>記憶の整理</b>：学んだ"
             "ことを選別し、重要なものを長期記憶へ（<b>；と—の言い換え・具体化＝R16</b>）。＝閉館後の"
             "司書の比喩（下線(1)）。"},
    {"arrow": "↓　理由①の具体化"},
    {"role": "理由①", "para": "¶4", "kind": "reason",
     "text": "実験知見：学んで眠った人の方が、徹夜した人より翌日よく覚えている。<b>抽象→具体（R4）</b>。"
             "挿入 researchers say / it seems（<b>R17</b>）。学習は「机の上でなく枕の上で」完成（R3）。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>心身のメンテナンス</b>：注意力の回復・感情の整理。注意は学びの通り道の「門」だから"
             "（<b>Because＝R6</b>）、睡眠を削ると学んだことを保持する力そのものが弱まる。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "睡眠は <b>not lost time but a form of investment（R3）</b>＝今日の努力を明日の能力に変える"
             "前に脳が要求する「支払い」。夜を削る＝<b>当てにしていたサービス（下線(3)）の取り消し</b>で、"
             "代価は翌日払う。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：長く眠るほど良いという話ではない。標的は<b>「眠りを削る勇気」を称える"
             "心の習慣</b>そのもの。問うべきは「どれだけ起きていられるか」ではなく「どれだけ夜に仕事を"
             "させてやれるか」。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 試験前夜の二つの選択",
     "caption": "同じ「学んだ内容」でも、<b>徹夜で詰め込む</b>と多くが漏れ出し、<b>学んでから眠る</b>と"
                "夜の整理を経て定着する。「時間を稼いだ」という実感は、目に見える成果だけで測った錯覚。",
     "para": "→ 第1・2・4段"},
    {"id": "fig2", "title": "図2 ｜ 夜の脳の二つの仕事（＝the services）",
     "caption": "夜が果たすサービスは二つ。①<b>記憶の整理→長期記憶への定着</b>（第3〜4段）、"
                "②<b>注意力の回復・感情の整理</b>（第5段）。下線部(3)の the services はこの二つを指す。",
     "para": "→ 第3〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 睡眠は「失われた時間」ではなく「投資」",
     "caption": "睡眠は何も起きない空白ではなく、<b>今日の努力を明日の能力に変える支払い</b>。"
                "問い直すべきは、「眠りを削る勇気」を称える発想そのもの。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "試験に備える生徒たちの間で、睡眠の評判は芳しくない。それは、何も起きていない空白のひと続きの"
        "時間——もう1枚の演習問題に充てられたはずの時間——として広く扱われている。こうした空気の中では、"
        "睡眠を削ることは立派なことにさえ見えうる——多くの人はそれを、目標に本気であることの証拠だと"
        "思っているらしいのだ。<b>それでもなお</b>、睡眠科学者たちはまったく異なる見方を取る。外から見れば"
        "静止にしか見えないものが、脳が持つ中で最も忙しい時間の一部を隠しているのだ、と彼らは論じる。"),
    (2, "確かに、起きている時間は貴重である。試験を控えた生徒に残された夜は限られており、その一晩一晩から"
        "もう1時間の勉強を絞り出すことは、まったく合理的に見える。眠って過ごす1時間は、ノートも、解き終えた"
        "問題も生み出さない——数えられるものを、何も。目に見えるもので測るなら、起きていることが当然の選択に"
        "思える。"),
    (3, "<b>それでも</b>、眠っている脳は、休止している脳ではない。その細胞は夜通しせっせと働き続けている。"
        "休むどころか、脳は昼が未完のまま残した仕事を仕上げつつあるのだ。それらの仕事の最たるものが、記憶の"
        "処理である。眠っている間に脳は、日中に学ばれたことを整理する、と研究は示唆している。重要なものを"
        "強め、些細なものは消えるに任せる——要するに、何が長期記憶に居場所を得るに値するかを決めているので"
        "ある。この点で脳は、<b>閉館後に働く図書館司書</b>のように振る舞う——その日の新着図書を、正しい棚に"
        "並べながら。"),
    (4, "この夜ごとの整理には、すべての学習者が利用できる帰結がある。よく知られた種類の実験では、新しい内容を"
        "学んでから眠る人々の方が、同じ内容を抱えて徹夜する人々よりも、翌日それをよく覚えている。徹夜組は、"
        "自分たちは時間を稼いだと感じるかもしれない。だが実際には、その時間が詰め込んだものの多くは、すでに"
        "漏れ出てしまっているのだ、と研究者は言う。学習はどうやら、机の上でではなく、枕の上で完成するらしい。"),
    (5, "夜が世話をしているのは、記憶だけではない。睡眠はまた、注意力という機構を修復し、日中にかき乱された"
        "感情を鎮める。十分に眠った夜の後は、より長く集中でき、小さな苛立ちも辛抱強く受け止められる。短い夜の"
        "後には、その逆が起こる。注意力は、私たちが学ぶすべてのものが通らねばならない門なのだから、睡眠を削る"
        "ことは、学んだことを手放さずにいるために必要な、まさにその能力を弱めてしまう。疲れた脳は、単に不快に"
        "感じられるだけではない——保持できる量そのものが減るのである。"),
    (6, "このように見てみると、私たちが睡眠に充てる時間は、別の呼び名に値するようになる。<b>睡眠は、"
        "失われた時間ではなく一種の投資——すなわち、今日の努力を明日の能力へと変えるのに先立って脳が要求する"
        "支払い——なのだ、と研究者たちはますます強く論じている。</b>机での1時間を得ようと夜を削るとき、私たちは"
        "勉強を増やしているのではない。<b>当てにしていたサービス</b>を取り消しているのであり、その代価を翌日に"
        "支払うことになるのだ。"),
    (7, "とはいえ以上のことは、眠りが長いほど常に良い結果になる、という意味ではない。体が求める以上の睡眠は、"
        "追加の見返りを何も得ない。この議論の本当の標的は、ある心の習慣——夜明けまで勉強したと誇る人々への、"
        "私たちの称賛——である。夜こそが、努力が能力になる時間なのだとすれば、眠りを削る勇気は美徳などでは"
        "まったくない——それは、自分自身の仕事を取り消していく、体裁のよいやり方なのだ。試験の前に問う価値の"
        "ある問いは、どれだけ長く起きていられるか、ではなく、どれだけ多くの仕事を夜にさせてやれるか、なので"
        "ある。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("reputation", "評判"),
    ("a blank stretch of time", "空白のひと続きの時間"),
    ("cut back on ~", "〜を切り詰める、削る"),
    ("admirable", "立派な、称賛に値する"),
    ("stillness", "静止、静けさ"),
    ("squeeze A out of B", "BからAを絞り出す"),
    ("at rest", "休止して、静止して"),
    ("far from doing", "〜するどころか"),
    ("leave ~ undone", "〜を未完のままにしておく"),
    ("sort through ~", "〜を整理する、より分ける"),
    ("trivial", "些細な、つまらない"),
    ("fade", "薄れる、消えていく"),
    ("stay up", "（寝ずに）起きている"),
    ("leak away", "漏れ出ていく"),
    ("look after ~", "〜の世話をする"),
    ("stir up ~", "〜をかき乱す、かき立てる"),
    ("frustration", "苛立ち、欲求不満"),
    ("capacity", "能力、容量"),
    ("hold on to ~", "〜を手放さない、保持する"),
    ("count on ~", "〜を当てにする、頼る"),
    ("boast of ~", "〜を自慢する、誇る"),
    ("virtue", "美徳、長所"),
    ("undo", "取り消す、台なしにする"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 問題提起：睡眠＝空白という通念と、その反転",
  "sentences": [
    {"chunks": [("M","(Among students &lt;preparing for examinations&gt;),","試験に備える生徒たちの間で"),
                ("S","sleep","睡眠は"),("V","has","持っている"),("O","a poor reputation.","芳しくない評判を")],
     "note":"▶ preparing …＝現在分詞が students を後ろから修飾〔<b>R11</b>〕。have a poor reputation＝「評判が悪い」。"},
    {"chunks": [("S","It","それ（睡眠）は"),("V","is widely treated","広く扱われている"),
                ("C","as a blank stretch of time &lt;in which nothing happens&gt;","何も起きていない空白のひと続きの時間として"),
                ("-","&mdash; hours &lt;that could have gone into one more practice paper&gt;.","——もう1枚の演習問題に充てられたはずの時間、と")],
     "note":"▶ treat A as B の受動態。in which＝前置詞＋関係代名詞〔<b>R11</b>〕。ダッシュ以下＝time の言い換え（同格）〔<b>R16</b>〕。could have gone＝「行けたはずの」（仮定の含み）。"},
    {"chunks": [("M","(In this atmosphere),","こうした空気の中では"),
                ("S","cutting back on sleep","睡眠を削ることは"),("V","can even look","〜にさえ見えうる"),
                ("C","admirable","立派なものに"),
                ("-","&mdash; proof,","——（それは）証拠なのだ、と"),
                ("M","many seem to believe,","多くの人は思っているらしい"),
                ("-","[that you are serious about your goal].","目標に本気だという（証拠）")],
     "note":"▶ 動名詞 cutting back on sleep＝主語。proof that …＝<b>同格の that 節</b>。many seem to believe は<b>挿入</b>〔<b>R17</b>〕——括弧に入れて proof that … のつながりを先に取る。"},
    {"chunks": [("接","And yet,","それでもなお"),("S","sleep scientists","睡眠科学者たちは"),
                ("V","take","取る"),("O","a very different view.","まったく異なる見方を")],
     "note":"▶ <b>R1｜逆接 And yet の直後が主張</b>（＝空所A）。通念に対する反論がここから始まる。"},
    {"chunks": [("S","[What looks like stillness from the outside],","外から見れば静止に見えるものが"),
                ("M","they argue,","と彼らは論じる"),("V","hides","隠している"),
                ("O","some of the busiest hours &lt;(that) the brain ever has&gt;.","脳が持つ中で最も忙しい時間の一部を")],
     "note":"▶ 関係代名詞 what＝「〜するもの」（名詞節が主語）。they argue は<b>挿入</b>〔<b>R17</b>〕。(that) the brain ever has＝関係詞省略〔<b>R11</b>〕。"},
  ]},
 {"head": "第2段 — 譲歩：確かに起きている時間は貴重（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当だ"),
                ("-","[that waking hours are precious].","起きている時間が貴重だということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。形式主語 It＝真主語 that 節。第3段 Even so で反転する前振り。"},
    {"chunks": [("S","A student &lt;facing an examination&gt;","試験を控えた生徒には"),
                ("V","has","ある"),("O","only so many evenings,","限られた数の夜しか"),
                ("接","and","そして"),
                ("S","squeezing an extra hour of study out of each","その一晩一晩からもう1時間の勉強を絞り出すことは"),
                ("V","looks","見える"),("C","entirely reasonable.","まったく合理的に")],
     "note":"▶ facing …＝分詞修飾〔<b>R11</b>〕。only so many＝「限られた数の」。squeeze A out of B＝「BからAを絞り出す」。動名詞 squeezing …＝後半の主語。"},
    {"chunks": [("S","An hour asleep","眠って過ごす1時間は"),("V","produces","生み出さない"),
                ("O","no notes and no finished exercises","ノートも、解き終えた問題も"),
                ("-","&mdash; nothing &lt;that can be counted&gt;.","——数えられるものを何も")],
     "note":"▶ ダッシュ以下＝直前のまとめ・言い換え〔<b>R16</b>〕。that can be counted＝関係代名詞〔<b>R11</b>〕。no A and no B の否定の並列。"},
    {"chunks": [("M","(Measured by [what we can see]),","目に見えるもので測るなら"),
                ("S","staying awake","起きていることが"),("V","seems","思える"),
                ("C","the obvious choice.","当然の選択に")],
     "note":"▶ Measured …＝<b>過去分詞の分詞構文</b>（＝If it is measured …）。what we can see＝関係代名詞 what。ここまでが譲歩〔<b>R2</b>〕。"},
  ]},
 {"head": "第3段 — 主張の転換：眠る脳は休んでいない（Even so）＋理由①記憶の整理",
  "sentences": [
    {"chunks": [("接","Even so,","それでもなお"),("S","a sleeping brain","眠っている脳は"),
                ("V","is not","ではない"),("C","a brain &lt;at rest&gt;.","休止している脳")],
     "note":"▶ <b>R1｜逆接 Even so＝主張転換点</b>（＝空所B）。第2段の譲歩を認めた上で反転する。at rest＝形容詞句で brain を修飾。"},
    {"chunks": [("S","Its cells","その細胞は"),("V","keep working","働き続ける"),
                ("M","busily (through the night);","夜通しせっせと"),
                ("M","(far from pausing),","休止するどころか"),
                ("S","the brain","脳は"),("V","is finishing","仕上げつつある"),
                ("O","tasks &lt;that the day left undone&gt;.","昼が未完のまま残した仕事を")],
     "note":"▶ <b>R16｜セミコロン(;)＝直前の言い換え・具体化</b>。far from doing＝「〜するどころか」。leave O undone＝「Oを未完のままにする」（that …＝関係代名詞〔<b>R11</b>〕）。"},
    {"chunks": [("C","Chief (among these tasks)","これらの仕事の中で最たるもの"),
                ("V","is","である"),("S","the handling of memory.","記憶の処理こそが")],
     "note":"▶ <b>CVS の倒置</b>：補語 Chief … が文頭に出て、主語 the handling of memory が後ろへ。理由①の主題提示。"},
    {"chunks": [("M","(During sleep),","眠っている間に"),("M","research suggests,","と研究は示唆する"),
                ("S","the brain","脳は"),("V","sorts through","整理する"),
                ("O","[what was learned during the day];","日中に学ばれたことを"),
                ("S","it","脳は"),("V","strengthens","強め"),("O","[what matters]","重要なものを"),
                ("接","and","そして"),("V","lets","させておく"),("O","the trivial","些細なものを"),("C","fade","消えるままに"),
                ("接","&mdash; in short,","——要するに"),
                ("S","it","脳は"),("V","decides","決めている"),
                ("O","[what deserves a place in long-term memory].","何が長期記憶に居場所を得るに値するかを")],
     "note":"▶ research suggests＝<b>挿入</b>〔<b>R17</b>〕。<b>R16｜セミコロンとダッシュ（in short）＝言い換え・具体化</b>の二段重ね。let O 原形＝「Oに〜させておく」。the trivial＝the＋形容詞「些細なもの」。what …＝名詞節×3。"},
    {"chunks": [("M","(In this respect)","この点で"),("S","it","脳は"),("V","behaves like","のように振る舞う"),
                ("C","a librarian &lt;working after closing time&gt;,","閉館後に働く図書館司書"),
                ("M","placing the day&rsquo;s new arrivals (on the right shelves).","その日の新着図書を正しい棚に並べながら")],
     "note":"▶ working …＝分詞修飾〔<b>R11</b>〕。placing …＝分詞構文（付帯状況）。比喩の中身は直前の第4文（整理・選別・定着）〔<b>R8</b>〕。＝<b>下線部(1)＝問3</b>。"},
  ]},
 {"head": "第4段 — 理由①の具体化：学んで眠る vs 徹夜（抽象→具体）",
  "sentences": [
    {"chunks": [("S","This nightly sorting","この夜ごとの整理は"),("V","has","持つ"),
                ("O","a consequence &lt;that every learner can use&gt;.","すべての学習者が利用できる帰結を")],
     "note":"▶ This nightly sorting＝第3段の内容の言い換え（まとめ）。that …＝関係代名詞〔<b>R11</b>〕。"},
    {"chunks": [("M","(In a familiar kind of experiment),","よく知られた種類の実験では"),
                ("S","people &lt;who study new material and then sleep&gt;","新しい内容を学んでから眠る人々は"),
                ("V","remember","覚えている"),("O","it","それを"),
                ("M","better (the next day)","翌日、より良く"),
                ("M","(than those &lt;who stay up all night with the same material&gt;).","同じ内容を抱えて徹夜する人々よりも")],
     "note":"▶ <b>R4｜抽象→具体</b>：この実験は「夜の整理→定着」（第3段）の具体例。those who …＝「〜する人々」〔<b>R11</b>〕。stay up＝「（寝ずに）起きている」。"},
    {"chunks": [("S","The all-night group","徹夜組は"),("V","may feel","感じるかもしれない"),
                ("O","[that they have gained time];","自分たちは時間を稼いだと"),
                ("M","(in reality),","実際には"),("M","researchers say,","と研究者は言う"),
                ("S","much of [what those hours put in]","その時間が詰め込んだものの多くは"),
                ("V","has already leaked away.","すでに漏れ出てしまっている")],
     "note":"▶ researchers say＝<b>挿入</b>〔<b>R17</b>〕：括弧に入れて much of … has leaked away の骨格を先に取る。<b>R16｜セミコロン</b>以下が「時間を稼いだ」という実感を裏返して具体化。what those hours put in＝名詞節。"},
    {"chunks": [("S","Learning,","学習は"),("M","it seems,","どうやら"),
                ("V","is completed","完成する"),
                ("M","not (at the desk) but (on the pillow).","机の上でではなく、枕の上で")],
     "note":"▶ it seems＝<b>挿入</b>〔<b>R17</b>〕。<b>R3｜not A but B</b>：重心は B（on the pillow＝眠っている間）。理由①のまとめの一文。"},
  ]},
 {"head": "第5段 — 理由②：心身のメンテナンス（注意力と感情）",
  "sentences": [
    {"chunks": [("S","Memory","記憶は"),("V","is not","ではない"),
                ("C","the only thing &lt;(that) the night looks after&gt;.","夜が世話をする唯一のもの")],
     "note":"▶ not the only ~＝「〜だけではない」（理由②への橋渡し）。(that) …＝関係詞省略〔<b>R11</b>〕。look after＝「世話をする」。"},
    {"chunks": [("S","Sleep","睡眠は"),("M","also","また"),("V","repairs","修復し"),
                ("O","the machinery of attention","注意力という機構を"),
                ("接","and","そして"),("V","settles","鎮める"),
                ("O","the emotions &lt;stirred up during the day&gt;.","日中にかき乱された感情を")],
     "note":"▶ stirred up …＝<b>過去分詞</b>が emotions を後ろから修飾〔<b>R11</b>〕。一つの主語 Sleep が repairs と settles の二つの動詞を取る。"},
    {"chunks": [("M","(After a full night)","十分に眠った夜の後は"),("S","we","私たちは"),
                ("V","concentrate","集中し"),("M","longer","より長く"),
                ("接","and","そして"),("V","meet","受け止める"),("O","small frustrations","小さな苛立ちを"),
                ("M","(with patience);","辛抱強く"),
                ("M","(after a short one),","短い夜の後は"),
                ("S","the opposite","その逆が"),("V","happens.","起こる")],
     "note":"▶ <b>R16｜セミコロン</b>＝対になる言い換え（十分な夜⇔短い夜の対句）。one＝night の代用。"},
    {"chunks": [("接","Because","〜なので"),("S","attention","注意力は"),("V","is","である"),
                ("C","the gate &lt;through which everything &lt;(that) we study&gt; must pass&gt;,","私たちが学ぶすべてのものが通らねばならない門"),
                ("S","cutting sleep","睡眠を削ることは"),("V","weakens","弱める"),
                ("O","the very capacity &lt;(that) we need to hold on to [what we learn]&gt;.","学んだことを手放さずにいるために必要な、まさにその能力を")],
     "note":"▶ <b>R6｜Because＝因果</b>：注意＝学びの門 → 削れば保持力が下がる。through which＝前置詞＋関係代名詞〔<b>R11</b>〕。the very ~＝「まさにその〜」。hold on to＝「保持する」。"},
    {"chunks": [("S","A tired brain","疲れた脳は"),("V","does not simply feel","単に感じるだけではない"),
                ("C","unpleasant","不快に"),
                ("-","&mdash;","——"),("S","it","それは"),("V","keeps","保持する"),("O","less.","より少なくしか")],
     "note":"▶ <b>R16｜ダッシュ＝直前の含意の具体化</b>：「不快なだけでなく、保持量そのものが減る」。not simply A — B の対比。"},
  ]},
 {"head": "第6段 — 核心的主張：睡眠＝投資（not lost time but …）",
  "sentences": [
    {"chunks": [("M","(Seen in this light),","このような光の下で見ると"),
                ("S","the hours &lt;(that) we give to sleep&gt;","私たちが睡眠に充てる時間は"),
                ("V","deserve","値する"),("O","a different name.","別の呼び名に")],
     "note":"▶ Seen …＝<b>過去分詞の分詞構文</b>（＝If they are seen …）。(that) we give …＝関係詞省略〔<b>R11</b>〕。"},
    {"chunks": [("S","Sleep,","睡眠は"),("M","researchers increasingly argue,","と研究者はますます強く論じる"),
                ("V","is","である"),
                ("C","not lost time but a form of investment","失われた時間ではなく、一種の投資"),
                ("-","&mdash; a payment &lt;(that) the brain demands (before it will turn today&rsquo;s effort into tomorrow&rsquo;s ability)&gt;.","——今日の努力を明日の能力に変えるより前に、脳が要求する支払い")],
     "note":"▶ <b>R17｜挿入 researchers increasingly argue を括弧に入れ、Sleep is not A but B の骨格を先に取る</b>。<b>R3｜not A but B＝Bが核心</b>。ダッシュ以下＝investment の言い換え〔<b>R16</b>〕。turn A into B＝「AをBに変える」。＝<b>下線部(2)＝問2</b>。"},
    {"chunks": [("M","(When we shorten the night to win an hour at the desk),","机での1時間を得ようと夜を削るとき"),
                ("S","we","私たちは"),("V","are not adding to","増やしてはいない"),("O","our studies;","勉強を"),
                ("S","we","私たちは"),("V","are canceling","取り消しているのだ"),
                ("O","the services &lt;(that) we were counting on&gt;,","当てにしていたサービスを"),
                ("接","and","そして"),("S","we","私たちは"),("V","pay for","代価を払う"),("O","it","それの"),
                ("M","(the next day).","翌日に")],
     "note":"▶ <b>R16｜セミコロン</b>＝「足しているのではなく、引いている」の言い換え。the services＝①記憶の整理・定着（第3〜4段）＋②注意・感情のメンテ（第5段）。count on＝「当てにする」。＝<b>下線部(3)＝問5</b>。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：問うべきは「眠りを削る勇気」への称賛",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),("V","means","意味しない"),
                ("O","[that longer sleep always brings better results].","眠りが長いほど常に良い結果になるとは")],
     "note":"▶ None of this means that …＝譲歩つき結論の合図。<b>R9注意</b>：設問の「長いほど必ず上がる」型の肢はここで×になる。"},
    {"chunks": [("S","Sleep &lt;beyond [what the body asks for]&gt;","体が求める以上の睡眠は"),
                ("V","earns","得ない"),("O","no extra reward.","追加の見返りを何も")],
     "note":"▶ beyond …＝前置詞句が Sleep を修飾。what the body asks for＝関係代名詞 what（名詞節）。"},
    {"chunks": [("S","The real target of the argument","この議論の本当の標的は"),
                ("V","is","である"),("C","a habit of mind:","ある心の習慣"),
                ("-","our admiration for those &lt;who boast of studying until dawn&gt;.","——夜明けまで勉強したと誇る人々への、私たちの称賛")],
     "note":"▶ コロン(:)＝直前の言い換え〔<b>R16</b>／<b>R8</b>〕。those who …＝「〜する人々」〔<b>R11</b>〕。boast of doing＝「〜したと自慢する」。"},
    {"chunks": [("M","(If the night is [when effort becomes ability]),","夜が、努力が能力になる時間なのだとすれば"),
                ("S","the courage &lt;to cut sleep&gt;","眠りを削る勇気は"),
                ("V","is","ではない"),("C","no virtue","何ら美徳"),
                ("-","&mdash; it is a polite way of undoing our own work.","——それは、自分自身の仕事を取り消していく、体裁のよいやり方なのだ")],
     "note":"▶ to cut sleep＝不定詞が courage を修飾。<b>R16｜ダッシュ以下＝no virtue の言い換え</b>。undo＝「取り消す・台なしにする」。"},
    {"chunks": [("S","The question &lt;worth asking before an examination&gt;","試験の前に問う価値のある問いは"),
                ("V","is","である"),
                ("C","not [how long we can stay awake], but [how much we let the night do for us].","どれだけ長く起きていられるか、ではなく、どれだけ多くの仕事を夜にさせてやれるか")],
     "note":"▶ worth doing＝「〜する価値がある」（question を修飾）。<b>R3｜not A but B</b>＝重心は B。how long / how much …＝間接疑問（名詞節）。let O do＝「Oに〜させてやる」。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=5文/第2段=4文/第3段=5文/第4段=4文/第5段=5文/第6段=3文/第7段=5文)
SVOC_LOGIC = {
    (1, 4): "対比", (1, 5): "主張",              # s4 And yet→反論 / s5 最も忙しい時間を隠す
    (2, 1): "譲歩", (2, 4): "譲歩",              # s1 It is true / s4 目に見えるもので測れば
    (3, 1): "対比", (3, 4): "主張", (3, 5): "具体例",   # s1 Even so / s4 整理・選別・定着 / s5 司書の比喩
    (4, 2): "具体例", (4, 3): "対比", (4, 4): "主張",   # s2 実験 / s3 実感vs実際 / s4 枕の上で完成
    (5, 2): "追加", (5, 4): "因果", (5, 5): "主張",     # s2 also=理由② / s4 Because / s5 保持量が減る
    (6, 2): "主張", (6, 3): "因果",              # s2 not lost time but investment / s3 削る→代価
    (7, 1): "譲歩", (7, 3): "主張", (7, 4): "主張", (7, 5): "主張",
}
