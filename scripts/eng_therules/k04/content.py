# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.04 — 単一ソース
テーマ: Mistakes Are Part of Learning (まちがいは学びの一部) / 基礎レベル（偏差値55〜60 / The Rules 1〜2 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "04",
    "level": "基礎レベル",
    "level_sub": "偏差値55〜60 / The Rules 1〜2 相当",
    "theme_ja": "まちがいは学びの一部",
    "theme_en": "Mistakes Are Part of Learning",
    "minutes": 15,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Many students see mistakes as something shameful. A wrong answer, we feel, is proof '
        'of weakness, and a red mark looks like a small punishment. So we try to avoid '
        'mistakes, and we hide them when they happen. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, many teachers and researchers argue '
        'that this attitude slows our growth. In their view, mistakes are not the opposite of '
        'learning; they are part of it.'),
    (2, 'It is true that mistakes cost points on a test. When two students sit for the same '
        'exam, the one who makes fewer errors gets the higher score. Test day is a place for '
        'showing what we have learned, and careful answers matter there. Nobody would '
        'say that wrong answers are welcome on such a day.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, practice is a different stage, and the '
        'rules there are different. Practice is not the place for proving ourselves; it is '
        'the place for building ourselves. In fact, the moment we make a mistake is often the '
        'moment our brain learns most. An error wakes us up and makes us pay close attention '
        'to the right answer.'),
    (4, 'Research on memory suggests a simple pattern. When we try to recall something, miss '
        'it, and check the correct answer right away, that answer stays in memory better '
        'than an answer we simply read again. Imagine a student who tests herself on new '
        'words, gets some wrong, and corrects them at once. She will remember more '
        'than a student who just looks over the list and never risks an answer. We grow more '
        'by trying and missing than by not trying at all.'),
    (5, 'Fear of mistakes, on the other hand, does real damage. When we are afraid of looking '
        'foolish, we stop raising our hands and trying new problems. Because hard '
        'questions carry the risk of failure, we begin to choose only the easy ones. Easy '
        'tasks feel safe, but they teach us little, and so our growth quietly stops. The fear '
        'itself, not the mistakes, is what holds us back.'),
    (6, 'All of this points to one simple idea. <u>A mistake made in practice is not proof of '
        'weakness but a sign that learning is happening.<sup>(1)</sup></u> Getting something '
        'wrong shows that you are working at the edge of your ability, where new skill is '
        'born. A notebook full of corrected errors is not a record '
        'of failure; it is a record of growth.'),
    (7, 'None of this means that we should make mistakes on purpose in a real exam. The point '
        'is the way we treat mistakes in practice. Do not hide a wrong answer or rub '
        'it out and forget it. Instead, look at it, ask why it happened, and <u>use it as '
        'material for your next step.<sup>(2)</sup></u> <u>Small errors, faced honestly, can '
        'teach us more than a page of perfect answers.<sup>(3)</sup></u> Learning to welcome '
        'them may be the first skill a growing student needs.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Many students see mistakes as something shameful. A wrong answer, we feel, is proof of "
    "weakness, and a red mark looks like a small punishment. So we try to avoid "
    "mistakes, and we hide them when they happen. However, many teachers "
    "and researchers argue that this attitude slows our growth. In their view, mistakes "
    "are not the opposite of learning; they are part of it. "
    "It is true that mistakes cost points on a test. When two students sit for the same exam, "
    "the one who makes fewer errors gets the higher score. Test day is a place for showing "
    "what we have learned, and careful answers matter there. Nobody would say that "
    "wrong answers are welcome on such a day. "
    "Still, practice is a different stage, and the rules there are different. Practice is "
    "not the place for proving ourselves; it is the place for building ourselves. In fact, the "
    "moment we make a mistake is often the moment our brain learns most. An error wakes us up "
    "and makes us pay close attention to the right answer. "
    "Research on memory suggests a simple pattern. When we try to recall something, miss it, "
    "and check the correct answer right away, that answer stays in memory better than an "
    "answer we simply read again. Imagine a student who tests herself on new words, gets some "
    "wrong, and corrects them at once. She will remember more than a student who just "
    "looks over the list and never risks an answer. We grow more by trying and missing than "
    "by not trying at all. "
    "Fear of mistakes, on the other hand, does real damage. When we are afraid of looking "
    "foolish, we stop raising our hands and trying new problems. Because hard questions "
    "carry the risk of failure, we begin to choose only the easy ones. Easy tasks feel safe, "
    "but they teach us little, and so our growth quietly stops. The fear itself, not the "
    "mistakes, is what holds us back. "
    "All of this points to one simple idea. A mistake made in practice is not proof of "
    "weakness but a sign that learning is happening. Getting something wrong shows "
    "that you are working at the edge of your ability, where new skill is "
    "born. A notebook full of corrected errors is not a record of failure; it is a record of "
    "growth. "
    "None of this means that we should make mistakes on purpose in a real exam. The point is "
    "the way we treat mistakes in practice. Do not hide a wrong answer or rub it out "
    "and forget it. Instead, look at it, ask why it happened, and use it as material for your "
    "next step. Small errors, faced honestly, can teach us more than a page of perfect "
    "answers. Learning to welcome them may be the first skill a growing student needs."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Therefore &nbsp; ② For example &nbsp; ③ However &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① Still &nbsp; ② As a result &nbsp; ③ For instance &nbsp; ④ Similarly",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(1) <span class='en'>A mistake made in practice is not proof of weakness "
             "but a sign that learning is happening.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(2) <span class='en'>use it as material for your next step</span>"
             "（それを次の一歩の材料として使う）とはどういうことか。「それ（<span class='en'>it"
             "</span>）」が何を指すかを明らかにしつつ、本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で紹介されている「記憶に関する研究」の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 間違えた直後に正解を見ると、かえって間違えた答えの方が記憶に残ってしまうと述べられている。",
         "② 新しい単語は、自分で思い出そうとするよりも、リストを何度も静かに見直す方がよく覚えられる。",
         "③ 何が記憶に残るかは、練習の回数や使う教材の質によってほぼ決まると述べられている。",
         "④ 思い出そうとして間違えても、直後に正解を確かめれば、ただ読み直すよりも記憶に残りやすい。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>Small errors, faced honestly, can teach us more than "
             "a page of perfect answers</span> について、なぜ正直に向き合った小さなまちがいは、"
             "完璧な解答よりも多くを教えてくれるのか。本文全体をふまえ、その理由を二つ挙げて"
             "日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① まちがいは多いほど学びになるのだから、本番の試験でもまちがいをまったく気にする必要はない、と筆者は述べている。",
         "② 練習でのまちがいは弱さの証拠ではなく学びが起きている印であり、隠さずに次の一歩の材料として扱うべきだ。",
         "③ 学習の最終的な目標はまちがいを完全になくすことなので、練習では確実に解ける易しい問題を選ぶのが賢い。",
         "④ まちがいを恐れる気持ちは生まれつき決まっているもので、どんな学び方をしても変えることはできない。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 筆者によれば、本番のテストの得点においては、まちがいの数が多いか少ないかはまったく重要ではない。",
         "② 思い出そうとして間違え、直後に正解を確かめると記憶に残りやすい、という知見が紹介されている。",
         "③ 挑戦して間違えるよりも、まちがいを避けて挑戦しないでいる方が、結局は大きく伸びると述べられている。",
         "④ 恥をかくことへの恐れから挑戦をやめ、易しい問題ばかり選ぶようになると、伸びは止まってしまう。",
         "⑤ まちがえた答えは、隠したり消して忘れたりせずに、次の一歩の材料として使うべきだと筆者は述べている。",
         "⑥ 筆者は、練習の場面だけでなく本番の試験でも、わざとまちがえてみることを勧めていると読み取れる。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ③ However　　B ＝ ① Still",
     "exp": "A：「まちがい＝恥。避けて隠すもの」という通念に対し、教師や研究者が「その態度こそ"
            "成長を遅らせる」と<b>反論</b>する流れ。逆接 → However。Therefore（因果）・"
            "For example（例示）・In addition（追加）は不可。<br>"
            "B：第2段「確かにテストではまちがいが点を失わせる（＝譲歩）」に対し、第3段は「だが"
            "練習は別のステージ」と主張へ<b>転換</b>する。逆接 → Still。As a result（因果）・"
            "For instance（例示）・Similarly（類比）は流れに合わない。 〔<b>解法ルール R7</b>／"
            "<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "④",
     "exp": "第4段「When we try to recall something, miss it, and check the correct "
            "answer right away, that answer stays in memory better than an answer we simply "
            "read again」＝思い出そうとして間違えても、直後に正解を確かめれば、ただ読み直した"
            "答えよりよく記憶に残る。①は本文にない（誤答の方が残るとは述べていない）、②は逆"
            "（リストを眺めるだけの生徒の方が覚えが少ない）、③も本文にない（回数や教材の質の"
            "話はしていない）。 〔<b>解法ルール R9</b>／<b>読解ルール R4</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "②",
     "exp": "第6段「not proof of weakness but a sign that learning is happening」＋第7段"
            "「The point is the way we treat mistakes in practice ／ use it as material for "
            "your next step」と一致。①は第2段（テストではまちがいが点を失わせる）と第7段"
            "（本番でわざと間違えるべきだという意味ではない）に反する（「まったく」も言い過ぎ）。"
            "③は第5段（易しい問題ばかり選ぶと伸びが止まる）に反する。④は本文にない（恐れが"
            "生まれつきで変えられないとは述べていない）。 〔<b>読解ルール R3</b>／<b>解法ルール "
            "R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "②・④・⑤",
     "exp": "①×：第2段「It is true that mistakes cost points on a test（テストではまちがいが"
            "点を失わせる）」に反する。「まったく」が典型的な<b>言い過ぎ</b>。"
            "③×：第4段「We grow more by trying and missing than by not trying at all（挑戦して"
            "間違える方が、挑戦しないより伸びる）」と逆。"
            "⑥×：第7段「None of this means that we should make mistakes on purpose in a real "
            "exam」で明確に否定。 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(1)和訳",
     "model": "練習の中でなされたまちがいは、弱さの証拠ではなく、学びが起きているという印なのである。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「AではなくB」の対比を訳に反映／②a mistake "
               "&lt;made in practice&gt;＝過去分詞の後置修飾を「練習で（の中で）なされたまちがい」と"
               "名詞にかけて訳す／③a sign that …＝<b>同格の that 節</b>「学びが起きているという印」。 "
               "〔<b>読解ルール R3</b>／<b>構文ルール R11</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "間違えた答え（＝it）を、隠したり消して忘れたりするのではなく、じっくり見つめて"
              "なぜその誤りが起きたのかを考え、次に何をどう学ぶかという次の一歩に生かす、ということ。",
     "points": "▶<b>採点要素</b>：①it＝a wrong answer（間違えた答え）だと明示（<b>R5</b>）／"
               "②直前の「隠す・消して忘れる」の否定と <b>Instead</b> の対比を反映／③「材料」＝"
               "誤りの原因を考え、次の学習・行動に生かすことだと本文（第7段）から補って説明。 "
               "〔<b>読解ルール R5</b>／<b>解法ルール R8</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①思い出そうとして間違え、その直後に正解を確かめると、ただ読み直すだけの場合よりも"
              "記憶に強く残るから。②完璧にこなせる易しい課題は安全でも学べることが少ないのに対し、"
              "まちがいは能力の際（＝新しい力が生まれる場所）で挑戦している印であり、挑戦して間違える"
              "方が挑戦しないよりも人を伸ばすから。",
     "points": "▶<b>採点要素</b>：本文全体から理由を二つ取り出す。①<b>記憶</b>（第4段：recall→miss→"
               "check → stays in memory better）／②<b>挑戦と成長</b>（第4〜6段：easy tasks teach "
               "little ／ the edge of your ability ／ grow more by trying and missing）。各5点。 "
               "〔<b>読解ルール R4・R6</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（However→教師・研究者の反論）、空所B（Still→第3段で「練習は別」と主張へ転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that mistakes cost points on a test」→ 第3段 Still で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(1) not proof of weakness but a sign、第5段 The fear itself, not the mistakes。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段の〈思い出す→間違える→すぐ訂正〉の知見と単語テストの生徒は、〈まちがいの瞬間に学ぶ〉の具体例。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "第1段 this attitude、第6段 All of this、第7段 None of this と it（＝a wrong answer）。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第5段 Because hard questions carry the risk … と〈恐れ→挑戦停止→易しい問題→伸び停止〉の連鎖。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。A＝通念⇔反論（逆接）、B＝譲歩⇔主張（逆接）。因果・例示・追加・類比の選択肢は不成立。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。第7段 Instead 前後の対比と、第6段の〈まちがい＝学びの印〉の言い換えを利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。①「まったく重要ではない」・⑥「本番でもわざと」などが典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "a mistake &lt;made in practice&gt;、Small errors, &lt;faced honestly&gt;（過去分詞）、"
         "the moment &lt;(when) we make a mistake&gt;。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「まちがい＝恥・弱さの証拠。避けて隠すもの」を提示。→ <b>However（R1）</b>：教師・"
             "研究者は「その態度こそ成長を遅らせる。まちがいは学びの一部」と反論。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かにテストではまちがいが点を失わせ、誤りの少ない方が"
             "高得点。＝通念の一部（本番での慎重さ）は認める。"},
    {"arrow": "◀ Still 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "だが<b>練習は別のステージ</b>。証明の場ではなく自分をつくる場（not A；B＝R3の変奏）。"
             "まちがえた瞬間こそ、脳が最も学ぶ瞬間。"},
    {"arrow": "↓　具体化（R4）"},
    {"role": "理由①", "para": "¶4", "kind": "reason",
     "text": "<b>記憶</b>：思い出そうとして間違え、直後に正解を確かめると、ただ読み直すより記憶に残る"
             "（研究の一般的知見）。挑戦して間違える方が、挑戦しないより伸びる。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>恐れの害</b>：恥への恐れ→挙手や挑戦をやめる→易しい問題ばかり選ぶ→伸びが止まる"
             "（<b>R6 因果の連鎖</b>）。足かせはまちがいではなく恐れそのもの。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "練習でのまちがいは<b>弱さの証拠ではなく「学びが起きている印」</b>（not proof of weakness "
             "but a sign＝<b>R3</b>）。誤り＝能力の際で挑んでいる証拠。直した誤りのノートは成長の記録。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：本番でわざと間違えろという話ではない。変えるのは<b>練習でのまちがいの"
             "扱い方</b>——隠したり消したりせず、原因を考え、次の一歩の材料にする。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 本番と練習——まちがいの意味は場所で変わる",
     "caption": "同じ「まちがい」でも、<b>本番のテスト</b>では点を失わせるもの（第2段＝譲歩）、"
                "<b>練習の段階</b>では脳が最も学ぶ瞬間（第3段）。練習は示す場ではなく、自分をつくる場。",
     "para": "→ 第2〜4段"},
    {"id": "fig2", "title": "図2 ｜ まちがいが学びになる二つの理由",
     "caption": "①<b>記憶</b>（第4段）：思い出す→間違える→すぐ正解を確認、でただ読み直すより記憶に残る。"
                "②<b>挑戦</b>（第5段）：恐れなければ難しい問題に挑み続けられる——恐れると易しい問題"
                "ばかりになり、伸びが止まる。問5の二つの理由はここ。",
     "para": "→ 第4〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — まちがいは「弱さの証拠」ではなく「学びの印」",
     "caption": "まちがい＝弱さの証拠だから隠す、のではなく、<b>学びが起きている印</b>として、原因を"
                "考えて<b>次の一歩の材料</b>にする。前提：本番でわざと間違えろという話ではない（第7段）。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "多くの生徒は、まちがいを何か恥ずかしいものとみなしている。誤った答えは弱さの証拠であり、赤い印"
        "は小さな罰のように見える、と私たちは感じてしまう。だから私たちは、まちがいを避けようとし、"
        "まちがいが起きたときにはそれを隠す。<b>しかし</b>、多くの教師や研究者が、"
        "この態度こそが私たちの成長を遅らせるのだ、と論じている。彼らの見方では、まちがいは学びの正反対"
        "のものではない。学びの一部なのである。"),
    (2, "確かに、テストではまちがいが点を失わせる。二人の生徒が同じ試験を受ければ、誤りの少ない方が高い"
        "得点を取る。試験の日は、学んだことを示すための場であり、そこでは慎重な解答が重要になる。"
        "そのような日に誤答が歓迎されるなどとは、誰も言わないだろう。"),
    (3, "<b>それでも</b>、練習は別のステージであり、そこでのルールも別である。練習は自分の力を証明"
        "するための場ではない。自分をつくり上げるための場なのだ。実のところ、私たちがまちがえる瞬間は、"
        "しばしば脳が最も学ぶ瞬間である。誤りは私たちをはっと目覚めさせ、正解に細心の注意を払わせる。"),
    (4, "記憶に関する研究は、単純なパターンを示唆している。何かを思い出そうとして、間違え、その直後に"
        "正解を確かめると、その答えは、ただ読み直しただけの答えよりもよく記憶に残るのである。新しい単語"
        "を自分でテストし、いくつか間違え、すぐに直す生徒を思い浮かべてみよう。その生徒は、"
        "リストを眺めるだけで、思い切って答えてみようとしない生徒よりも多くを覚えているだろう。私たちは、"
        "まったく挑戦しないことによってよりも、挑戦して間違えることによって、より大きく伸びるのだ。"),
    (5, "他方で、まちがいへの恐れは実際の害を与える。愚かに見えることを恐れると、私たちは手を挙げること"
        "や、新しい問題に挑むことをやめてしまう。難しい問題には失敗の危険が伴うため、私たちは易しい問題"
        "ばかりを選び始める。易しい課題は安全に感じられるが、教えてくれることはほとんどなく、その結果、"
        "私たちの伸びは静かに止まる。私たちを押しとどめているのは、まちがいではなく、恐れそのものなので"
        "ある。"),
    (6, "以上のすべては、一つの単純な考えを指し示している。<b>練習の中でなされたまちがいは、弱さの証拠"
        "ではなく、学びが起きているという印なのである。</b>何かを間違えるということは、あなたが自分の"
        "能力の際（ぎりぎりのところ）——新しい力が生まれる場所——で取り組んでいることを示している。"
        "直した誤りでいっぱいのノートは、失敗の記録ではない。成長の記録なのだ。"),
    (7, "とはいえ以上のことは、本番の試験でわざとまちがえるべきだという意味ではない。要点は、練習での"
        "まちがいの扱い方である。誤った答えを隠してはいけないし、消して忘れてしまってもいけない。そうでは"
        "なく、それを見つめ、なぜ起きたのかを問い、<b>それを次の一歩の材料として使う</b>のだ。<b>正直に"
        "向き合われた小さな誤りは、完璧な解答が並んだ1ページよりも多くを、私たちに教えてくれる。</b>"
        "誤りを歓迎できるようになること——それは、伸びていく生徒が必要とする最初の技能なのかもしれない。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("see A as B", "AをBとみなす"),
    ("shameful", "恥ずべき、恥ずかしい"),
    ("proof of ~", "〜の証拠"),
    ("punishment", "罰"),
    ("attitude", "態度、姿勢"),
    ("slow（動詞）", "〜を遅らせる"),
    ("the opposite of ~", "〜の正反対（のもの）"),
    ("cost（動詞）", "〜を失わせる、犠牲にさせる"),
    ("sit for an exam", "試験を受ける"),
    ("matter（動詞）", "重要である"),
    ("prove oneself", "自分の力を証明する"),
    ("pay attention to ~", "〜に注意を払う"),
    ("recall", "〜を思い出す"),
    ("right away / at once", "すぐに、直ちに"),
    ("get ~ wrong", "〜を間違える"),
    ("look over ~", "〜にざっと目を通す"),
    ("risk（動詞）", "思い切って〜してみる、賭ける"),
    ("look foolish", "愚かに見える"),
    ("hold ~ back", "〜を押しとどめる、妨げる"),
    ("at the edge of ~", "〜の際（ぎりぎりのところ）で"),
    ("on purpose", "わざと、故意に"),
    ("rub ~ out", "〜を（消しゴムで）消す"),
    ("material", "材料"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：「まちがい＝恥」という通念と、その反転",
  "sentences": [
    {"chunks": [("S","Many students","多くの生徒は"),("V","see","みなしている"),
                ("O","mistakes","まちがいを"),("C","as something shameful.","何か恥ずかしいものとして")],
     "note":"▶ <b>see A as B</b>＝「AをBとみなす」。something＋形容詞（後置修飾）＝「何か恥ずかしいもの」。通念の提示。"},
    {"chunks": [("S","A wrong answer,","誤った答えは"),("M","we feel,","と私たちは感じる"),
                ("V","is","である"),("C","proof of weakness,","弱さの証拠"),
                ("接","and","そして"),("S","a red mark","赤い印は"),
                ("V","looks like","のように見える"),("C","a small punishment.","小さな罰")],
     "note":"▶ we feel は挿入。proof of ~＝「〜の証拠」。look like＋名詞＝「〜のように見える」。"},
    {"chunks": [("接","So","だから"),("S","we","私たちは"),("V","try to avoid","避けようとする"),
                ("O","mistakes,","まちがいを"),
                ("接","and","そして"),("S","we","私たちは"),("V","hide","隠す"),("O","them","それを"),
                ("M","(when they happen).","それが起きたときには")],
     "note":"▶ try to do＝「〜しようとする」。when 節＝副詞節（時）。「避ける＋隠す」＝通念の行動。"},
    {"chunks": [("接","However,","しかし"),("S","many teachers and researchers","多くの教師や研究者が"),
                ("V","argue","論じている"),
                ("O","[that this attitude slows our growth].","この態度こそが私たちの成長を遅らせるのだ、と")],
     "note":"▶ <b>R1｜逆接 However の直後が主張</b>（＝空所A）。<b>R5</b>｜this attitude＝「まちがい＝恥。避けて隠す」という直前の態度。slow＝動詞「遅らせる」。"},
    {"chunks": [("M","(In their view),","彼らの見方では"),("S","mistakes","まちがいは"),
                ("V","are","である"),("C","not the opposite of learning;","学びの正反対のものではない"),
                ("S","they","それは"),("V","are","である"),("C","part of it.","学びの一部")],
     "note":"▶ セミコロンで〈not A；B〉を並置（<b>R3</b>の変奏）＝「正反対ではなく一部」。it＝learning。タイトルの回収。"},
  ]},
 {"head": "第2段 — 譲歩：確かにテストではまちがいが点を失わせる（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当"),
                ("-","[that mistakes cost points on a test].","テストではまちがいが点を失わせるということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。形式主語 It＝真主語 that 節。cost＝「〜を失わせる」。後の逆接（第3段 Still）で反転する前振り。"},
    {"chunks": [("M","(When two students sit for the same exam),","二人の生徒が同じ試験を受けるとき"),
                ("S","the one &lt;who makes fewer errors&gt;","誤りの少ない方の生徒が"),
                ("V","gets","取る"),("O","the higher score.","より高い得点を")],
     "note":"▶ sit for an exam＝「試験を受ける」。one＝a student の代用。<b>R11｜関係詞 who</b> が one を後ろから説明。"},
    {"chunks": [("S","Test day","試験の日は"),("V","is","である"),
                ("C","a place &lt;for showing [what we have learned]&gt;,","学んだことを示すための場"),
                ("接","and","そして"),("S","careful answers","慎重な解答が"),("V","matter","重要である"),
                ("M","there.","そこでは")],
     "note":"▶ what …＝関係代名詞 what「〜すること」。matter＝動詞「重要である」。〈示す場〉が第3段の〈つくる場〉と対比される伏線。"},
    {"chunks": [("S","Nobody","誰も〜ない"),("V","would say","言わないだろう"),
                ("O","[that wrong answers are welcome on such a day].","そのような日に誤答が歓迎されるとは")],
     "note":"▶ welcome＝形容詞「歓迎される」。譲歩の駄目押し（本番での慎重さは否定しない）。"},
  ]},
 {"head": "第3段 — 主張転換：練習は別のステージ（Still）",
  "sentences": [
    {"chunks": [("接","Still,","それでも"),("S","practice","練習は"),("V","is","である"),
                ("C","a different stage,","別のステージ"),
                ("接","and","そして"),("S","the rules there","そこでのルールも"),
                ("V","are","である"),("C","different.","別")],
     "note":"▶ <b>R1｜Still＝逆接でここが主張転換点</b>（＝空所B）。〈本番⇔練習〉の対比を宣言。there＝in practice。"},
    {"chunks": [("S","Practice","練習は"),("V","is","ではない"),
                ("C","not the place &lt;for proving ourselves&gt;;","自分の力を証明するための場"),
                ("S","it","それは"),("V","is","である"),
                ("C","the place &lt;for building ourselves&gt;.","自分をつくり上げるための場")],
     "note":"▶ セミコロンで〈not A；B〉＝<b>R3</b>の変奏。prove oneself＝「自分の力を証明する」。proving⇔building の対句。"},
    {"chunks": [("M","(In fact),","実のところ"),
                ("S","the moment &lt;(when) we make a mistake&gt;","私たちがまちがえる瞬間は"),
                ("V","is","である"),("M","often","しばしば"),
                ("C","the moment &lt;(when) our brain learns most&gt;.","脳が最も学ぶ瞬間")],
     "note":"▶ いずれも関係副詞 when の省略（<b>R11</b>）。主張の核＝「まちがいの瞬間こそ学びの瞬間」。"},
    {"chunks": [("S","An error","誤りは"),("V","wakes","目覚めさせる"),
                ("O","us","私たちを"),("M","up","（はっと）"),
                ("接","and","そして"),("V","makes","させる"),("O","us","私たちに"),
                ("C","pay close attention (to the right answer).","正解に細心の注意を払う（ように）")],
     "note":"▶ wake ~ up＝「目を覚まさせる」。使役 <b>make O do</b>（<b>R6</b> 因果：誤り→注意→学び）。pay attention to ~＝「〜に注意を払う」。"},
  ]},
 {"head": "第4段 — 理由①：記憶（抽象→具体：思い出す→間違える→すぐ訂正）",
  "sentences": [
    {"chunks": [("S","Research &lt;on memory&gt;","記憶に関する研究は"),("V","suggests","示唆している"),
                ("O","a simple pattern.","単純なパターンを")],
     "note":"▶ <b>R4｜抽象→具体</b>：ここから〈まちがいの瞬間に学ぶ〉の具体化。固有の実験名ではなく一般的知見（research suggests）として提示。"},
    {"chunks": [("M","(When we try to recall something, miss it, and check the correct answer right away),","何かを思い出そうとして、間違え、その直後に正解を確かめると"),
                ("S","that answer","その答えは"),("V","stays","残る"),("M","(in memory)","記憶に"),
                ("M","better (than an answer &lt;(that) we simply read again&gt;).","ただ読み直しただけの答えよりもよく")],
     "note":"▶ When 節内で try／miss／check の三つが並列。an answer &lt;(that) we simply read again&gt;＝関係詞省略（<b>R11</b>）。＝<b>問4④の根拠</b>。"},
    {"chunks": [("V","Imagine","思い浮かべてみよう"),
                ("O","a student &lt;who tests herself on new words, gets some wrong, and corrects them at once&gt;.","新しい単語を自分でテストし、いくつか間違え、すぐに直す生徒を")],
     "note":"▶ 命令文。<b>R11｜関係詞 who</b> 以下の三つの動詞が並列で student を説明。get O wrong＝「Oを間違える」。at once＝「すぐに」。"},
    {"chunks": [("S","She","彼女は"),("V","will remember","覚えているだろう"),
                ("O","more","より多くを"),
                ("M","(than a student &lt;who just looks over the list and never risks an answer&gt;).","リストを眺めるだけで、思い切って答えてみようとしない生徒よりも")],
     "note":"▶ 比較 more than …。look over＝「ざっと目を通す」。risk an answer＝「思い切って答えてみる」。〈試して間違える⇔試さない〉の対比。"},
    {"chunks": [("S","We","私たちは"),("V","grow","伸びる"),("M","more","より大きく"),
                ("M","(by trying and missing)","挑戦して間違えることによって"),
                ("M","(than by not trying at all).","まったく挑戦しないことによってよりも")],
     "note":"▶ by <i>doing</i>＝「〜することによって」。not trying＝動名詞の否定。<b>R9注意</b>：問7③はこの文と逆で×。"},
  ]},
 {"head": "第5段 — 理由②：恐れの害 → 伸びの停止",
  "sentences": [
    {"chunks": [("S","Fear of mistakes,","まちがいへの恐れは"),("M","on the other hand,","他方で"),
                ("V","does","与える"),("O","real damage.","実際の害を")],
     "note":"▶ on the other hand＝対比の転換（まちがいの効用⇔恐れの害）。do damage＝「害を与える」。理由②の主題提示。"},
    {"chunks": [("M","(When we are afraid of looking foolish),","愚かに見えることを恐れると"),
                ("S","we","私たちは"),("V","stop","やめる"),
                ("O","raising our hands and trying new problems.","手を挙げることや、新しい問題に挑むことを")],
     "note":"▶ be afraid of <i>doing</i>。stop <i>doing</i>＝「〜するのをやめる」（動名詞二つの並列）。<b>R6</b>｜恐れ→挑戦の停止という因果の始まり。"},
    {"chunks": [("接","Because","〜なので"),("S","hard questions","難しい問題は"),("V","carry","伴う"),
                ("O","the risk of failure,","失敗の危険を"),
                ("S","we","私たちは"),("V","begin to choose","選び始める"),
                ("O","only the easy ones.","易しい問題ばかりを")],
     "note":"▶ <b>R6｜Because＝因果</b>。ones＝questions の代用。＝<b>問7④の根拠</b>。"},
    {"chunks": [("S","Easy tasks","易しい課題は"),("V","feel","感じられる"),("C","safe,","安全に"),
                ("接","but","しかし"),("S","they","それは"),("V","teach","教えない"),
                ("O","us","私たちに"),("O","little,","ほとんど何も"),
                ("接","and so","その結果"),("S","our growth","私たちの伸びは"),
                ("V","quietly stops.","静かに止まる")],
     "note":"▶ little＝準否定「ほとんど〜ない」。but／and so で〈安全→学び少ない→伸び停止〉の連鎖（<b>R6</b>）。"},
    {"chunks": [("S","The fear itself, (not the mistakes),","まちがいではなく、恐れそのものが"),
                ("V","is","である"),("C","[what holds us back].","私たちを押しとどめているもの")],
     "note":"▶ <b>R3｜B, not A の形（＝not A but B の変形）</b>。itself＝強調。what …＝関係代名詞 what。hold ~ back＝「〜を妨げる」。"},
  ]},
 {"head": "第6段 — 核心的主張：まちがいは「弱さの証拠」ではなく「学びの印」",
  "sentences": [
    {"chunks": [("S","All of this","以上のすべては"),("V","points to","指し示している"),
                ("O","one simple idea.","一つの単純な考えを")],
     "note":"▶ <b>R5｜All of this＝第3〜5段の内容全体</b>を受ける。核心段の予告。"},
    {"chunks": [("S","A mistake &lt;made in practice&gt;","練習の中でなされたまちがいは"),
                ("V","is","である"),
                ("C","not proof of weakness but a sign","弱さの証拠ではなく、印"),
                ("-","[that learning is happening].","＝学びが起きているという")],
     "note":"▶ <b>R3｜not A but B＝Bこそ核心</b>。<b>R11</b>｜made in practice＝過去分詞の後置修飾。that learning is happening＝a sign の中身を示す<b>同格</b>の that 節。＝<b>下線部(1)＝問2</b>。"},
    {"chunks": [("S","Getting something wrong","何かを間違えるということは"),
                ("V","shows","示している"),
                ("O","[that you are working at the edge of your ability, &lt;where new skill is born&gt;].","自分の能力の際（ぎりぎりのところ）——新しい力が生まれる場所——で取り組んでいるということを")],
     "note":"▶ 動名詞 Getting …＝主語。get O wrong＝「Oを間違える」。where＝関係副詞の非制限用法（<b>R11</b>）＝「そしてそこで新しい力が生まれる」。"},
    {"chunks": [("S","A notebook &lt;full of corrected errors&gt;","直した誤りでいっぱいのノートは"),
                ("V","is","ではない"),("C","not a record of failure;","失敗の記録"),
                ("S","it","それは"),("V","is","である"),("C","a record of growth.","成長の記録")],
     "note":"▶ full of ~＝形容詞句の後置修飾（<b>R11</b>）。セミコロンで〈not A；B〉＝<b>R3</b>の変奏。核心の具体的イメージ。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：扱い方を変える——隠さず、次の一歩の材料に",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも〜ない"),("V","means","意味しない"),
                ("O","[that we should make mistakes on purpose in a real exam].","本番の試験でわざとまちがえるべきだとは")],
     "note":"▶ <b>R5｜None of this＝第6段までの主張全体</b>を受ける。<b>R9注意</b>：問7⑥はこの文に反する。on purpose＝「わざと」。"},
    {"chunks": [("S","The point","要点は"),("V","is","である"),
                ("C","the way &lt;(that) we treat mistakes in practice&gt;.","練習でのまちがいの扱い方")],
     "note":"▶ the way (that) SV＝「〜のやり方」（関係副詞の省略・<b>R11</b>）。主張の焦点＝まちがいの有無ではなく「扱い方」。"},
    {"chunks": [("V","Do not hide","隠してはいけない"),("O","a wrong answer","誤った答えを"),
                ("接","or","また〜もいけない"),("V","rub","消して"),("O","it","それを"),
                ("M","out","（消しゴムで）"),
                ("接","and","〜して"),("V","forget","忘れては"),("O","it.","それを")],
     "note":"▶ 否定の命令文の並列。rub ~ out＝「（消しゴムで）消す」。次文の Instead の前振り（何を否定するか）。"},
    {"chunks": [("接","Instead,","そうではなく"),("V","look at","見つめ"),("O","it,","それを"),
                ("V","ask","問い"),("O","[why it happened],","なぜそれが起きたのかを"),
                ("接","and","そして"),("V","use","使え"),("O","it","それを"),
                ("M","(as material for your next step).","次の一歩の材料として")],
     "note":"▶ Instead＝前文の否定を受けて「そうではなく」（<b>R8</b>｜対比で中身を確定）。三つの命令文の並列。why …＝間接疑問。use A as B。＝<b>下線部(2)＝問3</b>。"},
    {"chunks": [("S","Small errors, &lt;faced honestly&gt;,","正直に向き合われた小さな誤りは"),
                ("V","can teach","教えてくれうる"),("O","us","私たちに"),("O","more","より多くを"),
                ("M","(than a page of perfect answers).","完璧な解答が並んだ1ページよりも")],
     "note":"▶ <b>R11｜過去分詞 faced honestly</b> が挿入で errors を修飾。teach O1 O2＝「O1にO2を教える」。＝<b>下線部(3)＝問5</b>。"},
    {"chunks": [("S","Learning to welcome them","誤りを歓迎できるようになることは"),
                ("V","may be","かもしれない"),
                ("C","the first skill &lt;(that) a growing student needs&gt;.","伸びていく生徒が必要とする最初の技能")],
     "note":"▶ 動名詞 Learning …＝主語。them＝small errors。that 省略の関係詞（<b>R11</b>）が skill を後ろから説明。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=5文/第2段=4文/第3段=4文/第4段=5文/第5段=5文/第6段=4文/第7段=6文)
SVOC_LOGIC = {
    (1, 4): "対比", (1, 5): "主張",                    # However→反論(=空所A) / 学びの一部
    (2, 1): "譲歩", (2, 4): "譲歩",                    # It is true / 駄目押し
    (3, 1): "対比", (3, 2): "対比", (3, 3): "主張", (3, 4): "因果",
    (4, 1): "主張", (4, 2): "因果", (4, 3): "具体例", (4, 4): "対比", (4, 5): "主張",
    (5, 1): "主張", (5, 2): "因果", (5, 3): "因果", (5, 4): "因果", (5, 5): "主張",
    (6, 2): "主張", (6, 3): "因果", (6, 4): "対比",
    (7, 1): "譲歩", (7, 2): "主張", (7, 3): "対比", (7, 4): "主張", (7, 5): "主張",
}
