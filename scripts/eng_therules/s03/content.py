# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.03 (最難関編) — 単一ソース
テーマ: The 'Nothing to Hide' Fallacy: What Privacy Is Really For
       (「隠すものは何もない」の誤り——プライバシーの本当の価値)
最難関レベル（早慶・旧帝 / The Rules 4 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "03",
    "level": "最難関レベル",
    "level_sub": "早慶・旧帝 / The Rules 4 相当",
    "theme_ja": "「隠すものは何もない」の誤り——プライバシーの本当の価値",
    "theme_en": "The 'Nothing to Hide' Fallacy: What Privacy Is Really For",
    "minutes": 25,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Whenever surveillance is debated, one reply arrives almost before the question is '
        'finished: if you have done nothing wrong, you have nothing to hide; and if you have '
        'nothing to hide, you have nothing to fear. It is often said, in this spirit, that '
        'privacy is a shelter for wrongdoers &mdash; a luxury which honest citizens can happily '
        'surrender in exchange for safety and convenience. Some even argue that the desire to '
        'remain unobserved is itself grounds for suspicion. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, a long line of philosophers and legal '
        'scholars has insisted that this familiar reasoning, however plausible it may sound, '
        'misunderstands what privacy is for &mdash; and that the misunderstanding is anything '
        'but harmless.'),
    (2, 'It is true that trading personal information for benefit is not always foolish. We '
        'tell a doctor what we would tell no one else because sound treatment depends on honest '
        'disclosure; we let a navigation app record our movements because we want the fastest '
        'route home. Where the watcher is accountable and the purpose is narrow and clear, such '
        'bargains can be perfectly rational, and a society that refused every one of them would '
        'be poorer for it.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, the "nothing to hide" argument fails, '
        'and it fails at the root, for it assumes that privacy is essentially a means of '
        'concealment &mdash; a screen behind which the guilty conceal their guilt. If that were '
        'all privacy did, the innocent would indeed lose little by giving it up. But what '
        'privacy protects is not, at bottom, our secrets; it is the conditions under which we '
        'form a self that is genuinely our own.'),
    (4, 'Consider what happens when people believe they are being watched. Observed, we '
        'perform; unobserved, we experiment. Research on behaviour under observation suggests '
        'that even the mere possibility of being seen makes people more obedient to majority '
        'opinion and less willing to voice an unpopular view. Because the watcher need not '
        'actually be present &mdash; the feeling of being watched is enough &mdash; '
        'surveillance does its deepest work inside the mind, where it quietly persuades us to '
        'edit ourselves in advance. <u>The internalization of the observer\'s gaze thus leads, '
        'almost imperceptibly, to the abandonment of the very trial and error through which '
        'opinions are tested, revised, and sometimes reversed.<sup>(1)</sup></u>'),
    (5, 'Defenders of surveillance reply that whatever is lost in this way is trivial beside '
        'the security gained; a little self-consciousness, they say, is a small price for safer '
        'streets. The objection deserves a serious answer, and the answer is that it measures '
        'the wrong thing. <u>What a watched society loses is not an individual comfort but a '
        'shared resource.<sup>(2)</sup></u> When everyone edits themselves in advance, '
        'unpopular ideas are not defeated in argument; they simply go unspoken, and a community '
        'that hears only safe opinions gradually loses the diversity of thought on which '
        'correction, reform, and progress depend.'),
    (6, 'Privacy, properly understood, is <u>not a wall behind which we hide what is shameful, '
        'but a margin within which we may become who we are.<sup>(3)</sup></u> Inside that '
        'margin we rehearse identities, entertain doubts, and hold opinions still too fragile '
        'to defend in public; deprived of it, we do not become more honest &mdash; we merely '
        'become more uniform. The value of privacy, in short, lies less in what it conceals '
        'than in what it makes possible.'),
    (7, 'None of this amounts to a demand that we stop sharing information altogether, still '
        'less to a defence of those who abuse secrecy to escape justice. The point is that the '
        'familiar question &mdash; "What have you got to hide?" &mdash; is the wrong one, for '
        'it places the burden of proof on the watched rather than on the watcher. The questions '
        'worth asking run the other way: who is watching, for what purpose, with whose '
        'permission, and within what limits? A society that learns to ask them will not have '
        'abandoned safety; it will merely have refused to purchase safety with the quiet '
        'surrender of the space in which its citizens become themselves.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Whenever surveillance is debated, one reply arrives almost before the question is "
    "finished: if you have done nothing wrong, you have nothing to hide; and if you have "
    "nothing to hide, you have nothing to fear. It is often said, in this spirit, that privacy "
    "is a shelter for wrongdoers a luxury which honest citizens can happily surrender in "
    "exchange for safety and convenience. Some even argue that the desire to remain unobserved "
    "is itself grounds for suspicion. Nonetheless, a long line of philosophers and legal "
    "scholars has insisted that this familiar reasoning, however plausible it may sound, "
    "misunderstands what privacy is for and that the misunderstanding is anything but harmless. "
    "It is true that trading personal information for benefit is not always foolish. We tell a "
    "doctor what we would tell no one else because sound treatment depends on honest "
    "disclosure; we let a navigation app record our movements because we want the fastest route "
    "home. Where the watcher is accountable and the purpose is narrow and clear, such bargains "
    "can be perfectly rational, and a society that refused every one of them would be poorer "
    "for it. "
    "Even so, the \"nothing to hide\" argument fails, and it fails at the root, for it assumes "
    "that privacy is essentially a means of concealment a screen behind which the guilty "
    "conceal their guilt. If that were all privacy did, the innocent would indeed lose little "
    "by giving it up. But what privacy protects is not, at bottom, our secrets; it is the "
    "conditions under which we form a self that is genuinely our own. "
    "Consider what happens when people believe they are being watched. Observed, we perform; "
    "unobserved, we experiment. Research on behaviour under observation suggests that even the "
    "mere possibility of being seen makes people more obedient to majority opinion and less "
    "willing to voice an unpopular view. Because the watcher need not actually be present the "
    "feeling of being watched is enough surveillance does its deepest work inside the mind, "
    "where it quietly persuades us to edit ourselves in advance. The internalization of the "
    "observer's gaze thus leads, almost imperceptibly, to the abandonment of the very trial and "
    "error through which opinions are tested, revised, and sometimes reversed. "
    "Defenders of surveillance reply that whatever is lost in this way is trivial beside the "
    "security gained; a little self-consciousness, they say, is a small price for safer "
    "streets. The objection deserves a serious answer, and the answer is that it measures the "
    "wrong thing. What a watched society loses is not an individual comfort but a shared "
    "resource. When everyone edits themselves in advance, unpopular ideas are not defeated in "
    "argument; they simply go unspoken, and a community that hears only safe opinions gradually "
    "loses the diversity of thought on which correction, reform, and progress depend. "
    "Privacy, properly understood, is not a wall behind which we hide what is shameful, but a "
    "margin within which we may become who we are. Inside that margin we rehearse identities, "
    "entertain doubts, and hold opinions still too fragile to defend in public; deprived of it, "
    "we do not become more honest we merely become more uniform. The value of privacy, in "
    "short, lies less in what it conceals than in what it makes possible. "
    "None of this amounts to a demand that we stop sharing information altogether, still less "
    "to a defence of those who abuse secrecy to escape justice. The point is that the familiar "
    "question \"What have you got to hide?\" is the wrong one, for it places the burden of "
    "proof on the watched rather than on the watcher. The questions worth asking run the other "
    "way: who is watching, for what purpose, with whose permission, and within what limits? A "
    "society that learns to ask them will not have abandoned safety; it will merely have "
    "refused to purchase safety with the quiet surrender of the space in which its citizens "
    "become themselves."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Consequently &nbsp; ② Nonetheless &nbsp; ③ For instance &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① Even so &nbsp; ② As a result &nbsp; ③ For example &nbsp; ④ Likewise",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(1) <span class='en'>The internalization of the observer's gaze thus leads, "
             "almost imperceptibly, to the abandonment of the very trial and error through which "
             "opinions are tested, revised, and sometimes reversed.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(3) について、プライバシーが「壁ではなく余白（<span class='en'>not a wall … "
             "but a margin</span>）」だとはどういうことか。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で紹介されている「観察下の行動」に関する研究の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 見られている可能性があるというだけでも、人は多数派の意見に従いやすくなり、不人気な意見を口にしにくくなる。",
         "② 監視者が実際にその場にいる場合に限って、人は多数派の意見に従いやすくなり、自分の意見を言えなくなる。",
         "③ 見られていると感じた人々は、かえって多数派の意見に逆らって、不人気な自分の意見を主張しやすくなった。",
         "④ 監視は人前での行動こそ変えるものの、心の内側で行われる思考そのものにまで影響が及ぶことはなかった。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(2) <span class='en'>What a watched society loses is not an individual "
             "comfort but a shared resource.</span> の <span class='en'>a shared resource</span>"
             "（共有の資源）として失われるものは何か。本文全体をふまえ、二つ挙げて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① プライバシーとは結局のところ、やましい秘密を世間の目から隠すための壁にすぎず、隠すもののない正直に生きる市民にとってはほとんど価値を持たない。",
         "② 安全や利便と引き換えに個人情報を差し出す取引はどれも例外なく不合理であり、私たちは医師や経路アプリへの開示を含む一切の情報共有を直ちにやめるべきである。",
         "③ 監視によって失われるのはせいぜい個人のわずかな気詰まり程度にすぎず、より安全な街路という治安上の利益はその損失をつねに上回ると筆者も認めている。",
         "④ プライバシーの価値は秘密の隠蔽ではなく、人が自分自身になるための余白を守ることにあり、問うべきは「誰が・何のために・どこまで見るのか」である。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 筆者によれば、何も悪いことをしていない正直な人々は、たとえ監視が広がっても、失うものを初めから何も持っていない。",
         "② 実際に見られていなくても、見られているという感覚だけで、人は前もって自分自身を検閲するようになる。",
         "③ 医師への打ち明けや経路アプリのように、監視者に説明責任があり目的が限定された情報の取引は、合理的でありうる。",
         "④ 全員が自己検閲する社会では、不人気な考えは議論で敗れるのではなく、単に語られないまま消えていく。",
         "⑤ 筆者は、あらゆる情報共有を完全にやめることを、市民の誰に対しても、例外なく直ちに実行するよう要求している。",
         "⑥ 監視が人々の行動や発言を変えるのは、監視者が実際にその場に居合わせ、行動を直接見ている場合に限られる。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ② Nonetheless　　B ＝ ① Even so",
     "exp": "A：直前は「よく言われる」「〜と論じる者さえいる」＝<b>他人の声（通念）</b>。直後で哲学者・"
            "法学者が「この論法は取り違えだ」と反論する。ぶつかる流れ＝<b>逆接</b> → Nonetheless。"
            "Consequently（因果）・For instance（例示）・In addition（追加）は不可。<br>"
            "B：第2段「確かに合理的な取引もある（＝譲歩）」に対し、第3段は「それでもこの論は根本で"
            "破綻している」と主張へ<b>転換</b>する。逆接 → Even so。As a result（因果）・For example"
            "（例示）・Likewise（類比）は流れに合わない。 〔<b>解法ルール R7</b>／<b>読解ルール "
            "R1・R2・R26</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "①",
     "exp": "第4段「even the mere possibility of being seen makes people more obedient to "
            "majority opinion and less willing to voice an unpopular view」＝見られる<b>可能性だけ</b>"
            "でも従順になり、不人気な意見を言わなくなる。②は「その場にいる場合に限って」が本文"
            "「the watcher need not actually be present」に反する。③は逆。④も逆（surveillance does "
            "its deepest work <b>inside the mind</b>＝最も深い仕事は心の内側で行われる）。 "
            "〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "④",
     "exp": "第6段「not a wall … but a margin within which we may become who we are」＋第7段「who "
            "is watching, for what purpose, with whose permission, and within what limits?」と一致。"
            "①は第3・6段の主張と正反対（それは筆者が退ける通念の側）。②は言い過ぎ——第2段で合理的な"
            "取引の存在を認め、第7段でも「情報共有をすべてやめよという要求ではない」と明言。③は第5段"
            "の擁護者の声であり、筆者はまさにそれに再反論している（R26：誰の声かを区別）。 "
            "〔<b>読解ルール R3・R26</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "②・③・④",
     "exp": "①×：第3段「プライバシーが守るのは秘密ではなく、自分自身の自己を形づくる条件」＋第6段"
            "「奪われれば画一的になる」——正直な人も失うものを持つ（第1段のこの論法自体、筆者が誤り"
            "とする通念。R26）。⑤×：第7段「None of this amounts to a demand that we stop sharing "
            "information altogether」＝「完全にやめよ」は<b>言い過ぎ</b>。⑥×：第4段「the watcher "
            "need not actually be present — the feeling of being watched is enough」に反する。 "
            "〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除／<b>読解ルール R26</b>〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(1)和訳",
     "model": "こうして、観察者のまなざしを内面化することは、ほとんどそれと気づかれないうちに、意見が"
              "試され、修正され、時には覆される、まさにその試行錯誤を放棄することへとつながるのである。",
     "points": "▶<b>採点要素</b>：①<b>名詞構文の訳し戻し</b>——The internalization of the observer's "
               "gaze＝「観察者のまなざしを内面化すること」／the abandonment of …＝「…を放棄すること」"
               "と、動詞に戻して訳す／②almost imperceptibly（挿入）＝「ほとんど気づかれないうちに」"
               "の訳出／③through which … reversed＝関係詞節が the very trial and error を修飾"
               "（試され・修正され・覆される試行錯誤）。 〔<b>構文ルール R27</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "プライバシーとは、恥ずべき秘密を人目から隠すための壁のようなものではなく、人前で守る"
              "にはまだ脆すぎる考えや疑いを自由に試し、その中で人が本当に自分自身と言える自己を形づく"
              "っていくための「余白」となる空間だ、ということ。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「壁ではなく余白」の対比を反映／②「壁」＝隠蔽の"
               "手段（やましいものを隠す）の否定／③「余白」＝〈あり方を試し・疑いを抱き・脆い意見を"
               "育てる＝自己形成の条件〉であることを本文（第3・6段）から補って説明。 "
               "〔<b>読解ルール R3</b>／<b>解法ルール R8</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①意見が試され、修正され、時には覆されながら、考えが形づくられていく試行錯誤の過程"
              "——社会の成員が共有する営み。②不人気な意見も口に出されることで保たれる、社会全体の思考の"
              "多様性——訂正・改革・進歩を支える土台。",
     "points": "▶<b>採点要素</b>：「共有の資源」の中身を本文から二つ取り出す。①<b>試行錯誤の過程</b>"
               "（第4段：trial and error through which opinions are tested, revised, and sometimes "
               "reversed）／②<b>思考の多様性</b>（第5段：the diversity of thought on which "
               "correction, reform, and progress depend）。各5点。 〔<b>解法ルール R8</b>／"
               "<b>読解ルール R14</b>：再反論の中身を確定〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（Nonetheless→哲学者・法学者の反論）、空所B（Even so→主張転換）、第3段 But。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that trading personal information … is not always foolish」→ 第3段 Even so で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(3) not a wall … but a margin、下線部(2) not an individual comfort but a shared resource、第3段 not … our secrets; it is …。"),
        ("R14", "反対意見・コスト批判への「再反論」は主張の強化——譲歩⇄再反論の往復を追う", "★★★",
         "第5段 Defenders of surveillance reply …（批判）→ The objection deserves a serious answer（受け止め）→ it measures the wrong thing（再反論）。問5。"),
        ("R26", "★NEW “誰の声か”を区別する——some argue / it is said は筆者の主張ではない。筆者の評価は逆接の後に来る", "★★★",
         "第1段 It is often said … / Some even argue …＝通念の声 → Nonetheless の後が筆者側。第5段 they say も擁護者の声。問6③・問7①。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。ダッシュ(—)・not A but B・セミコロン後の言い換えを利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。⑤の「完全にやめることを要求」、②の「例外なく不合理」は典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "a margin &lt;within which we may become who we are&gt;、the security &lt;gained&gt;、a community &lt;that hears only safe opinions&gt; 型。"),
        ("R27", "★NEW 名詞構文——動詞から派生した名詞は文に戻して訳す（the loss of X＝Xを失うこと）", "★★★",
         "下線部(1)＝問2 the internalization of the observer's gaze／the abandonment of the very trial and error、第7段 the quiet surrender of the space。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「隠すものがなければ恐れる必要はない」を<b>他人の声（It is often said / Some even "
             "argue＝R26）</b>として提示。→ <b>Nonetheless（R1）</b>：哲学者・法学者は「この論法は"
             "プライバシーの目的を取り違えている」と反論。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに、見る側に説明責任があり目的が限定された情報の"
             "取引（医師・経路アプリ）は合理的でありうる。＝通念の一部は認める。"},
    {"arrow": "◀ Even so 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "「隠すものは何もない」論は<b>根本の前提が誤り</b>——プライバシー＝隠蔽の手段ではない。"
             "守っているのは秘密ではなく<b>「自分自身の自己を形づくる条件」（R3）</b>。"},
    {"arrow": "↓　深化（なぜ条件なのか）"},
    {"role": "理由（深化）", "para": "¶4", "kind": "reason",
     "text": "<b>見られると人は変わる</b>：見られる可能性だけで従順になり、少数意見を言わなくなる"
             "（研究）。監視は心の内側で働き、<b>前もっての自己検閲</b>を促す→<b>試行錯誤の放棄</b>"
             "（下線部(1)・名詞構文 R27）。"},
    {"arrow": "◀ 批判 ⇄ 再反論（R14） ▶"},
    {"role": "再反論", "para": "¶5", "kind": "claim",
     "text": "擁護者「失うものは安全に比べればささいだ」→ 再反論：<b>測るものが違う</b>。失われるのは"
             "個人の快適さではなく<b>共有の資源（R3）</b>＝思考の多様性（訂正・改革・進歩の土台）。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "プライバシーは<b>「隠すための壁」ではなく「人が自分自身になるための余白」（R3）</b>。"
             "奪われても正直にはならず、ただ<b>画一的</b>になる。価値は「何を隠すか」でなく「何を"
             "可能にするか」。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：情報共有をやめよという話ではない。問うべきは「隠すものがあるか」では"
             "なく<b>「誰が・何のために・誰の許可で・どこまで見るのか」</b>。その問いを学んだ社会は、"
             "安全を捨てるのではなく、自己形成の空間と引き換えに安全を買うことを拒むだけだ。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ プライバシーをめぐる二つの見方",
     "caption": "通念（＝他人の声）は「プライバシー＝やましい者の隠れ蓑」とみなし、正直者なら手放せる"
                "贅沢品だとする。筆者は<b>Nonetheless の後（R1・R26）</b>でこれを退け、プライバシーを"
                "「自分自身の自己を形づくる条件」と捉え直す。",
     "para": "→ 第1・3・6段"},
    {"id": "fig2", "title": "図2 ｜ 「見られること」が奪うもの（＝a shared resource）",
     "caption": "監視は心の内側で働く：見られている<b>感覚だけ</b>で人は前もって自己検閲する。"
                "その先で失われるのが、①<b>試行錯誤の過程（余地）</b>（第4段）と ②<b>思考の多様性</b>"
                "（第5段）。下線部(2)の a shared resource はこの二つを指す。",
     "para": "→ 第4〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 壁ではなく「余白」",
     "caption": "プライバシーは恥を隠す<b>壁</b>ではなく、考えを試し・疑い・育てて<b>人が自分自身に"
                "なるための余白</b>。問うべきは「隠すものがあるか」ではなく「誰が・何のために・どこまで"
                "見るのか」（第7段）。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "監視の是非が論じられるときにはいつでも、問いが言い終わらぬうちに、ほとんど決まって一つの返答が"
        "返ってくる。すなわち、「悪いことをしていないなら、隠すものは何もないはずだ。そして隠すものが"
        "ないなら、恐れるものも何もないはずだ」と。こうした調子で、プライバシーとは悪事を働く者の隠れ家"
        "——正直な市民なら安全と利便と引き換えに喜んで手放せる贅沢品——だ、としばしば言われる。人に見られ"
        "ずにいたいという欲求それ自体が疑いの根拠だ、とまで論じる者さえいる。<b>それでもなお</b>、哲学者"
        "や法学者たちは連綿と主張してきた。このおなじみの論法は、どれほどもっともらしく聞こえようとも、"
        "プライバシーが何のためにあるのかを取り違えており、しかもその取り違えは決して無害ではないのだ、と。"),
    (2, "確かに、個人情報を利益と引き換えに差し出すことが、常に愚かであるわけではない。適切な治療は正直な"
        "開示に懸かっているからこそ、私たちは他の誰にも言わないことを医師には打ち明けるし、一番早く家に"
        "帰る道を知りたいからこそ、経路案内アプリに自分の移動を記録させる。見る側に説明責任があり、目的が"
        "狭く明確である場合には、そうした取引は完全に合理的でありうるし、そのすべてを拒むような社会は、"
        "かえって貧しくなってしまうだろう。"),
    (3, "<b>それでもやはり</b>、「隠すものは何もない」論は破綻している。しかも根本のところで破綻している。"
        "というのもこの論は、プライバシーとは本質的に隠蔽の手段——やましい者が自らのやましさを隠す衝立——"
        "だと想定しているからだ。もしプライバシーのすることがそれだけなら、なるほど潔白な人々は、それを"
        "手放してもほとんど失うものはないだろう。だが、プライバシーが守っているのは、突き詰めれば、私たち"
        "の秘密ではない。それは、私たちが本当に自分自身のものと言える自己を形づくるための、条件なのである。"),
    (4, "人々が「見られている」と信じるとき、何が起こるかを考えてみてほしい。見られていれば、私たちは演じ"
        "る。見られていなければ、試してみる。観察下の行動に関する研究が示唆するところでは、見られている"
        "可能性があるというだけでも、人は多数派の意見に従いやすくなり、不人気な意見を口にしたがらなくなる。"
        "監視者が実際にその場にいる必要はない——見られているという感覚だけで十分なのだ——から、監視はその"
        "最も深い仕事を心の内側で行い、そこで私たちに、前もって自分自身を検閲するようそっと促す。<b>こうし"
        "て、観察者のまなざしを内面化することは、ほとんどそれと気づかれないうちに、意見が試され、修正され、"
        "時には覆される、まさにその試行錯誤を放棄することへとつながるのである。</b>"),
    (5, "監視の擁護者たちはこう答える。この形で失われるものが何であれ、得られる安全に比べればささいなもの"
        "だ。多少の気詰まりなど、より安全な街路のための小さな代価だ、と。この異論は真剣な答えに値する。"
        "そしてその答えは、この異論は測るべきものを測り違えている、というものだ。<b>監視される社会が失う"
        "のは、個人の快適さではなく、共有の資源である。</b>全員が前もって自分を検閲するとき、不人気な考え"
        "は議論で打ち負かされるのではない。ただ語られないままになるのであり、無難な意見しか耳にしない共同"
        "体は、訂正も改革も進歩もそれに依存している思考の多様性を、少しずつ失っていくのだ。"),
    (6, "プライバシーとは、正しく理解するなら、<b>恥ずべきものを隠すための壁ではなく、私たちが自分自身に"
        "なることのできる余白である。</b>その余白の中で私たちは、自分のあり方をいくつも試し、疑いを心に"
        "抱き、人前で守るにはまだ脆すぎる意見を持ちこたえさせる。それを奪われたとき、私たちはより正直に"
        "なるのではない——ただ、より画一的になるだけだ。要するにプライバシーの価値は、それが何を隠すかより"
        "も、それが何を可能にするかにあるのである。"),
    (7, "以上のいずれも、あらゆる情報共有をやめよという要求ではないし、まして、正義を逃れるために秘密を"
        "悪用する者たちの弁護でもない。要点はこうだ。おなじみの問い——「何か隠すものでもあるのか」——は"
        "問いとして間違っている。それは立証の責任を、見る側ではなく見られる側に負わせるからだ。問う価値の"
        "ある問いは、逆の向きに走る。すなわち、誰が見ているのか、何のためにか、誰の許可の下でか、そして"
        "どこまでの限度でか、と。これらを問うことを学んだ社会は、安全を捨てたことにはならないだろう。ただ、"
        "市民が自分自身になるための空間を静かに明け渡すという代価で安全を買うことを、拒んだだけなのである。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("surveillance", "監視"),
    ("wrongdoer", "悪事を働く者"),
    ("surrender", "（動）手放す、明け渡す／（名）明け渡し"),
    ("in exchange for ~", "〜と引き換えに"),
    ("grounds for ~", "〜の根拠・理由"),
    ("plausible", "もっともらしい"),
    ("anything but ~", "決して〜ではない"),
    ("disclosure", "開示、打ち明けること"),
    ("accountable", "説明責任を負う"),
    ("concealment", "隠すこと、隠蔽"),
    ("at bottom", "根本において、突き詰めれば"),
    ("obedient", "従順な"),
    ("voice（動詞）", "（意見など）を口に出す"),
    ("imperceptibly", "気づかれないほどに"),
    ("trial and error", "試行錯誤"),
    ("reverse", "覆す、逆転させる"),
    ("trivial", "ささいな、取るに足らない"),
    ("objection", "異論、反対"),
    ("go unspoken", "語られないままになる"),
    ("rehearse", "練習する、試しに演じる"),
    ("entertain（考え・疑い）", "（考え・疑いを）心に抱く"),
    ("fragile", "脆い、壊れやすい"),
    ("the burden of proof", "立証責任"),
    ("still less ~", "まして〜ではない"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：通念（他人の声）と、Nonetheless 後の筆者側の反論",
  "sentences": [
    {"chunks": [("M","(Whenever surveillance is debated),","監視が論じられるときはいつでも"),
                ("S","one reply","一つの返答が"),("V","arrives","やってくる"),
                ("M","(almost before the question is finished):","問いが言い終わらぬうちに(ほとんど)"),
                ("-","if you have done nothing wrong, you have nothing to hide;","「悪いことをしていなければ、隠すものは何もない。"),
                ("-","and if you have nothing to hide, you have nothing to fear.","そして隠すものがなければ、恐れるものも何もない」")],
     "note":"▶ <b>コロン(:)以下＝one reply の中身（同格）</b>。if 節が連鎖する対句。<b>R26｜これは筆者の声ではなく「よくある返答」</b>——この段階では誰の主張かを保留して読む。"},
    {"chunks": [("S","It","（形式主語）"),("V","is often said,","しばしば言われる"),
                ("M","in this spirit,","こうした調子で"),
                ("-","[that privacy is a shelter for wrongdoers]","プライバシーは悪事を働く者の隠れ家だと"),
                ("-","&mdash; a luxury &lt;which honest citizens can happily surrender (in exchange for safety and convenience)&gt;.","——正直な市民が安全と利便と引き換えに喜んで手放せる贅沢品——")],
     "note":"▶ <b>R26｜It is often said＝伝聞</b>（筆者の主張ではない）。形式主語 It＝真主語 that 節。ダッシュ以下は a shelter の言い換え（同格）。which …＝関係代名詞（<b>R11</b>）。"},
    {"chunks": [("S","Some","ある者たちは"),("V","even argue","〜とさえ論じる"),
                ("O","[that the desire &lt;to remain unobserved&gt; is itself grounds for suspicion].","見られずにいたいという欲求それ自体が疑いの根拠だ、と")],
     "note":"▶ <b>R26｜Some argue も他人の声</b>。to remain unobserved＝不定詞が desire を修飾。itself＝強調（それ自体が）。"},
    {"chunks": [("接","Nonetheless,","それでもなお"),
                ("S","a long line of philosophers and legal scholars","連綿と続く哲学者・法学者たちが"),
                ("V","has insisted","主張してきた"),
                ("O","[that this familiar reasoning, (however plausible it may sound), misunderstands what privacy is for]","このおなじみの論法は、どれほどもっともらしく聞こえようとも、プライバシーが何のためにあるかを取り違えている、と"),
                ("接","&mdash; and","そして"),
                ("O","[that the misunderstanding is anything but harmless].","その取り違えは決して無害ではない、と")],
     "note":"▶ <b>R1｜逆接 Nonetheless の直後が筆者側の主張</b>（＝空所A）。<b>R26｜通念 → 逆接 → 筆者の評価</b>の典型形。however plausible it may sound＝譲歩の挿入。anything but＝「決して〜ない」。"},
  ]},
 {"head": "第2段 — 譲歩：確かに合理的な取引はある（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当だ"),
                ("-","[that trading personal information for benefit is not always foolish].","個人情報を利益と引き換えに差し出すことが常に愚かであるわけではない、ということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。not always＝部分否定。後の逆接（第3段 Even so）で反転する前振り。"},
    {"chunks": [("S","We","私たちは"),("V","tell","打ち明ける"),("O","a doctor","医師に"),
                ("O","[what we would tell no one else]","他の誰にも言わないであろうことを"),
                ("M","(because sound treatment depends on honest disclosure);","適切な治療は正直な開示に懸かっているから"),
                ("S","we","私たちは"),("V","let","させる"),("O","a navigation app","経路案内アプリに"),
                ("C","record our movements","自分の移動を記録"),
                ("M","(because we want the fastest route home).","一番早い帰り道を知りたいから")],
     "note":"▶ tell O1 O2（O2＝関係代名詞 what の名詞節）。<b>let O do</b>＝使役。セミコロンで対等な二例を並置＝譲歩の具体例。"},
    {"chunks": [("M","(Where the watcher is accountable and the purpose is narrow and clear),","見る側に説明責任があり、目的が狭く明確である場合には"),
                ("S","such bargains","そうした取引は"),("V","can be","でありうる"),("C","perfectly rational,","完全に合理的"),
                ("接","and","そして"),
                ("S","a society &lt;that refused every one of them&gt;","そのすべてを拒む社会は"),
                ("V","would be","なるだろう"),("C","poorer","より貧しく"),("M","(for it).","そのために")],
     "note":"▶ <b>Where SV</b>＝「〜する場合には」（接続詞）。that refused …＝仮定の意味を含む関係詞節（would と呼応）（<b>R11</b>）。"},
  ]},
 {"head": "第3段 — 主張転換：この論は根本で破綻している（Even so）",
  "sentences": [
    {"chunks": [("接","Even so,","それでもやはり"),
                ("S","the \"nothing to hide\" argument","「隠すものは何もない」論は"),("V","fails,","破綻している"),
                ("接","and","しかも"),("S","it","それは"),("V","fails","破綻している"),("M","(at the root),","根本のところで"),
                ("接","for","というのも"),("S","it","それは"),("V","assumes","想定しているからだ"),
                ("O","[that privacy is essentially a means of concealment]","プライバシーとは本質的に隠蔽の手段だと"),
                ("-","&mdash; a screen &lt;behind which the guilty conceal their guilt&gt;.","——やましい者がその後ろにやましさを隠す衝立——")],
     "note":"▶ <b>R1｜Even so＝逆接でここが主張転換点</b>（＝空所B）。for＝理由の等位接続詞。the guilty＝〈the＋形容詞〉「やましい者たち」。behind which …＝前置詞＋関係代名詞（<b>R11</b>）。"},
    {"chunks": [("M","(If that were all &lt;(that) privacy did&gt;),","もしそれがプライバシーのすることのすべてなら"),
                ("S","the innocent","潔白な人々は"),("V","would indeed lose","なるほど失わないだろう"),
                ("O","little","ほとんど何も"),("M","(by giving it up).","それを手放しても")],
     "note":"▶ <b>仮定法過去</b>（were / would）。all (that) privacy did＝関係詞省略。the innocent＝〈the＋形容詞〉。indeed は譲歩の「なるほど（確かに）」。"},
    {"chunks": [("接","But","だが"),("S","[what privacy protects]","プライバシーが守っているものは"),
                ("V","is not,","ではない"),("M","(at bottom),","突き詰めれば"),("C","our secrets;","私たちの秘密"),
                ("S","it","それは"),("V","is","である"),
                ("C","the conditions &lt;under which we form a self &lt;that is genuinely our own&gt;&gt;.","私たちが本当に自分自身のものである自己を形づくる、その条件")],
     "note":"▶ <b>R3｜is not A; it is B ＝ not A but B の変形</b>——核心はB「自己形成の条件」。what 節＝主語。under which … / that is …＝関係詞の二重のカタマリ（<b>R11</b>）。"},
  ]},
 {"head": "第4段 — 深化：見られていると人は変わる（自己検閲→試行錯誤の放棄）",
  "sentences": [
    {"chunks": [("V","Consider","考えてみてほしい"),
                ("O","[what happens (when people believe they are being watched)].","人々が「見られている」と信じるとき、何が起こるかを")],
     "note":"▶ 命令文。what happens …＝間接疑問（名詞節）。believe (that) they are being watched＝that 省略＋進行形の受動態。"},
    {"chunks": [("M","(Observed),","見られていれば"),("S","we","私たちは"),("V","perform;","演じる"),
                ("M","(unobserved),","見られていなければ"),("S","we","私たちは"),("V","experiment.","試してみる")],
     "note":"▶ <b>過去分詞一語の分詞構文</b>（＝When we are observed / When we are unobserved）。省略を伴う鋭い対句——最難関レベル頻出の圧縮表現。"},
    {"chunks": [("S","Research (on behaviour under observation)","観察下の行動に関する研究は"),
                ("V","suggests","示唆する"),
                ("O","[that even the mere possibility of being seen makes people more obedient to majority opinion and less willing to voice an unpopular view].","見られる可能性があるというだけでも、人は多数派の意見により従順になり、不人気な意見を口にしたがらなくなる、と")],
     "note":"▶ that 節内は <b>make O C</b>（C＝more obedient … and less willing …の並列）。the mere possibility of being seen＝「見られるという可能性だけ」（<b>R27</b>の香り：見られる<i>こと</i>の可能性）。"},
    {"chunks": [("M","(Because the watcher need not actually be present)","監視者が実際にその場にいる必要はないので"),
                ("-","&mdash; the feeling of being watched is enough &mdash;","——見られているという感覚だけで十分なのだ——"),
                ("S","surveillance","監視は"),("V","does","行う"),("O","its deepest work","その最も深い仕事を"),
                ("M","(inside the mind),","心の内側で"),
                ("M","&lt;where it quietly persuades us to edit ourselves in advance&gt;.","そしてそこで私たちに、前もって自分自身を検閲するようそっと促す")],
     "note":"▶ need not＝助動詞の need「〜する必要はない」。ダッシュに挟まれた部分＝<b>挿入</b>（理由の補強）。where＝非制限用法の関係副詞（＝and there）。persuade O to do。"},
    {"chunks": [("S","The internalization of the observer's gaze","観察者のまなざしを内面化することは"),
                ("M","thus","こうして"),("V","leads,","つながる"),
                ("M","(almost imperceptibly),","ほとんど気づかれないうちに"),
                ("M","(to the abandonment of the very trial and error &lt;through which opinions are tested, revised, and sometimes reversed&gt;).","意見が試され、修正され、時には覆される、まさにその試行錯誤を放棄することへと")],
     "note":"▶ <b>R27｜名詞構文</b>：internalization＝「内面化<i>すること</i>」／abandonment＝「放棄<i>すること</i>」と動詞に戻して訳す。lead to＝因果。through which …＝関係詞節が trial and error を修飾（<b>R11</b>）。＝<b>下線部(1)＝問2</b>。"},
  ]},
 {"head": "第5段 — 批判と再反論：失われるのは「共有の資源」",
  "sentences": [
    {"chunks": [("S","Defenders of surveillance","監視の擁護者たちは"),("V","reply","こう答える"),
                ("O","[that whatever is lost in this way is trivial beside the security &lt;gained&gt;];","この形で失われるものが何であれ、得られる安全に比べればささいだ、と"),
                ("S","a little self-consciousness,","多少の気詰まりなど"),
                ("M","they say,","と彼らは言う"),("V","is","である"),
                ("C","a small price (for safer streets).","より安全な街路のための小さな代価")],
     "note":"▶ <b>R14｜批判（コスト論）の提示</b>。whatever＝複合関係代名詞（that 節内の主語）。gained＝過去分詞1語が security を後置修飾（<b>R11</b>）。<b>R26｜they say＝擁護者の声</b>（筆者ではない）。"},
    {"chunks": [("S","The objection","この異論は"),("V","deserves","値する"),("O","a serious answer,","真剣な答えに"),
                ("接","and","そして"),("S","the answer","その答えは"),("V","is","である"),
                ("C","[that it measures the wrong thing].","それは測るべきものを測り違えている、ということ")],
     "note":"▶ <b>R14｜受け止め → 再反論</b>の蝶番となる一文。deserve＝「〜に値する」。that 節＝補語になる名詞節。"},
    {"chunks": [("S","[What a watched society loses]","監視される社会が失うものは"),
                ("V","is","である"),
                ("C","not an individual comfort but a shared resource.","個人の快適さではなく、共有の資源")],
     "note":"▶ <b>R3｜not A but B＝Bが核心</b>：「共有の資源」。what 節＝主語。a watched society＝過去分詞の前置修飾。＝<b>下線部(2)＝問5</b>。"},
    {"chunks": [("M","(When everyone edits themselves in advance),","全員が前もって自分を検閲するとき"),
                ("S","unpopular ideas","不人気な考えは"),("V","are not defeated","打ち負かされるのではない"),
                ("M","(in argument);","議論で"),
                ("S","they","それらは"),("V","simply go","ただ〜ままになる"),("C","unspoken,","語られない"),
                ("接","and","そして"),
                ("S","a community &lt;that hears only safe opinions&gt;","無難な意見しか耳にしない共同体は"),
                ("V","gradually loses","少しずつ失っていく"),
                ("O","the diversity of thought &lt;on which correction, reform, and progress depend&gt;.","訂正・改革・進歩がそれに依存している、思考の多様性を")],
     "note":"▶ <b>go＋形容詞</b>＝「〜のままになる」（go unspoken）。depend on の on が関係詞の前に出た形（on which … depend）（<b>R11</b>）。「共有の資源」の中身②＝思考の多様性。"},
  ]},
 {"head": "第6段 — ★核心：壁ではなく「余白」（not a wall but a margin）",
  "sentences": [
    {"chunks": [("S","Privacy,","プライバシーとは"),("M","(properly understood),","正しく理解するなら"),
                ("V","is","である"),
                ("C","not a wall &lt;behind which we hide [what is shameful]&gt;, but a margin &lt;within which we may become [who we are]&gt;.","恥ずべきものをその後ろに隠す壁ではなく、私たちが自分自身になることのできる余白")],
     "note":"▶ <b>R3｜not A but B＝本文全体の核心</b>。properly understood＝過去分詞の挿入（＝if it is properly understood）。behind which / within which＝前置詞＋関係代名詞（<b>R11</b>）。＝<b>下線部(3)＝問3</b>。"},
    {"chunks": [("M","(Inside that margin)","その余白の中で"),("S","we","私たちは"),
                ("V","rehearse","試しに演じ"),("O","identities,","自分のあり方を"),
                ("V","entertain","心に抱き"),("O","doubts,","疑いを"),
                ("接","and","そして"),("V","hold","持ちこたえさせる"),
                ("O","opinions &lt;still too fragile to defend in public&gt;;","人前で守るにはまだ脆すぎる意見を"),
                ("M","(deprived of it),","それを奪われると"),
                ("S","we","私たちは"),("V","do not become","なるのではない"),("C","more honest","より正直に"),
                ("-","&mdash;","——"),
                ("S","we","私たちは"),("V","merely become","ただなるだけだ"),("C","more uniform.","より画一的に")],
     "note":"▶ rehearse / entertain / hold＝三つの動詞の並列。too … to ～＝「～するには…すぎる」。deprived of it＝受動の分詞構文（＝if we are deprived of it）。not more honest — merely more uniform の対比。"},
    {"chunks": [("S","The value of privacy,","プライバシーの価値は"),("M","in short,","要するに"),
                ("V","lies","ある"),
                ("M","(less in [what it conceals] than in [what it makes possible]).","それが何を隠すかよりも、それが何を可能にするかに")],
     "note":"▶ lie in＝「〜にある」。<b>less A than B</b>＝「AというよりB」（重心はB＝可能にするもの）。what 節×2＝前置詞 in の目的語。"},
  ]},
 {"head": "第7段 — 譲歩つき結論：問うべきは「誰が・何のために・どこまで」",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),("V","amounts to","〜に等しくはない"),
                ("O","a demand &lt;that we stop sharing information altogether&gt;,","あらゆる情報共有をやめよという要求に"),
                ("接","still less","まして〜ではない"),
                ("O","(to) a defence of those &lt;who abuse secrecy to escape justice&gt;.","正義を逃れるために秘密を悪用する者たちの弁護には")],
     "note":"▶ <b>R9注意</b>：この文が設問⑤「完全にやめることを要求」を否定する根拠。a demand that SV＝<b>同格の that</b>（「〜という要求」）。still less＝「まして〜ない」（否定の追い打ち）。"},
    {"chunks": [("S","The point","要点は"),("V","is","である"),
                ("C","[that the familiar question &mdash; \"What have you got to hide?\" &mdash; is the wrong one],","おなじみの問い——「何か隠すものでもあるのか」——は間違った問いだ、ということ"),
                ("接","for","というのも"),("S","it","それは"),("V","places","負わせるからだ"),
                ("O","the burden of proof","立証の責任を"),
                ("M","(on the watched rather than on the watcher).","見る側ではなく、見られる側に")],
     "note":"▶ ダッシュに挟まれた引用＝<b>挿入</b>。the watched / the watcher＝〈the＋分詞・名詞〉の対。rather than＝<b>R3</b>系の対比（重心は on the watched への批判）。"},
    {"chunks": [("S","The questions &lt;worth asking&gt;","問う価値のある問いは"),
                ("V","run","走る"),("M","(the other way):","逆の向きに"),
                ("-","who is watching, for what purpose, with whose permission, and within what limits?","誰が見ているのか、何のためにか、誰の許可の下でか、そしてどこまでの限度でか")],
     "note":"▶ worth asking＝「問う価値のある」（worth＋動名詞）が questions を後置修飾（<b>R11</b>）。コロン以下＝the questions の中身（同格）。四つの疑問の並列が「監視を問い直す枠組み」。"},
    {"chunks": [("S","A society &lt;that learns to ask them&gt;","これらを問うことを学ぶ社会は"),
                ("V","will not have abandoned","捨てたことにはならないだろう"),("O","safety;","安全を"),
                ("S","it","それは"),("V","will merely have refused","ただ拒んだだけなのである"),
                ("O","to purchase safety (with the quiet surrender of the space &lt;in which its citizens become themselves&gt;).","市民が自分自身になる空間を静かに明け渡すという代価で、安全を買うことを")],
     "note":"▶ 未来完了 will have done＝「（その時点で）〜したことになる」。purchase A with B＝「Bを代価にAを買う」。<b>R27｜the quiet surrender of the space＝「空間を静かに明け渡すこと」</b>と文に戻して訳す。in which …＝関係詞（<b>R11</b>）。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=4文/第2段=3文/第3段=3文/第4段=5文/第5段=4文/第6段=3文/第7段=4文)
SVOC_LOGIC = {
    (1, 3): "追加", (1, 4): "対比",               # s3 Some even argue(通念の追加) / s4 Nonetheless→筆者側
    (2, 1): "譲歩", (2, 2): "具体例", (2, 3): "譲歩",
    (3, 1): "対比", (3, 2): "譲歩", (3, 3): "主張",
    (4, 2): "対比", (4, 3): "具体例", (4, 4): "因果", (4, 5): "因果",
    (5, 1): "譲歩", (5, 2): "主張", (5, 3): "主張", (5, 4): "因果",
    (6, 1): "主張", (6, 2): "対比", (6, 3): "主張",
    (7, 1): "譲歩", (7, 2): "主張", (7, 3): "主張", (7, 4): "主張",
}
