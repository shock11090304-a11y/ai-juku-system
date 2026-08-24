# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.01 — 単一ソース（最難関編）
テーマ: Trusting Experts Is Not the Same as Blind Faith (専門家への信頼は思考停止か)
最難関レベル（早慶・旧帝 / The Rules 4 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "01",
    "level": "最難関レベル",
    "level_sub": "早慶・旧帝 / The Rules 4 相当",
    "theme_ja": "専門家への信頼は思考停止か",
    "theme_en": "Trusting Experts Is Not the Same as Blind Faith",
    "minutes": 25,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, "&ldquo;Do not take the experts' word for it; look into the matter yourself.&rdquo; "
        "In recent years this advice has hardened into something like a creed. To question "
        "official knowledge is presented as a mark of intellectual courage, while accepting "
        "what specialists say is dismissed as laziness &mdash; or worse, as the quiet surrender "
        "of one's own judgment. The truly independent thinker, we are told, verifies everything "
        'personally and bows to no authority. <span class="blank">【&nbsp;A&nbsp;】</span>, '
        "this flattering picture of the self-reliant mind, for all its appeal, rests on an "
        "illusion &mdash; one that becomes visible the moment we ask what &ldquo;checking for "
        "yourself&rdquo; actually involves."),
    (2, "It is true that experts are fallible, and that the record of blind deference to them "
        "is not a happy one. Specialists have defended theories that later collapsed, and "
        "institutions have at times protected their own reputation more carefully than the "
        "public they were meant to serve. Whole fields have had to withdraw claims once "
        "announced with confidence. Anyone who urges us simply to obey the credentialed, no "
        "questions asked, has not read much history. The suspicion that now surrounds expertise "
        "did not come from nowhere; it was, in part, earned."),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, the ideal of checking everything for '
        "oneself dissolves the moment it is examined. The person who &ldquo;does her own "
        "research&rdquo; does not visit the laboratory, repeat the experiments, or re-derive "
        "the statistics; she reads documents written by strangers, posted on platforms built "
        "by other strangers, summarizing measurements she will never witness. Every step of "
        "her inquiry borrows the labor, and the honesty, of people she has never met. "
        "<u>It is not that independent verification is a noble goal we sadly fail to reach, "
        "but that, for creatures whose knowledge is stitched together from the testimony of "
        "others, complete intellectual self-reliance was never a possibility in the first "
        "place.<sup>(1)</sup></u>"),
    (4, "What looks like a private achievement, then, is in fact a social arrangement. Modern "
        "knowledge has grown far beyond the capacity of any single head: the chemist trusts "
        "the physicist, the doctor trusts the medical journal, and all of them trust "
        "instruments that none of them could build alone. Never in this long division of labor "
        "has reliance on others been a sign of idleness; it is the very mechanism by which a "
        "community comes to know more than any of its members. To trust well, on this view, is "
        "not to stop thinking but to think with other people."),
    (5, "Does it follow that we may believe whomever we please? Hardly. <u>Trust, practiced "
        "well, carries its own instruments of testing.<sup>(2)</sup></u> We can ask whether a "
        "speaker stands to profit from being believed; whether she has admitted and corrected "
        "her past errors, or quietly buried them; and whether those best placed to catch her "
        "mistakes &mdash; rivals within her own field &mdash; have largely come to agree with "
        "her. None of these checks requires us to repeat the science ourselves; they demand "
        "something humbler and more attainable &mdash; attention to how a claim has survived "
        "the scrutiny of others."),
    (6, "The real question, therefore, is poorly framed as a choice between trusting and "
        "doubting. What we need is <u>not a verdict on experts but a craft of "
        "trust<sup>(3)</sup></u>: the discipline of judging whom to believe, about which "
        "questions, and on what grounds. A physicist deserves our confidence about particles, "
        "not necessarily about politics; a careful weigher of evidence in one domain may be a "
        "novice in the next. Framed this way, trust ceases to be a lapse of intelligence and "
        "becomes one of its most demanding exercises."),
    (7, "None of this asks us to abandon doubt; a healthy intellectual culture needs skeptics "
        "as a body needs an immune system. But doubt spread evenly over everything protects "
        "nothing &mdash; it merely exhausts us. Only when suspicion is aimed &mdash; informed "
        "by a speaker's interests, record, and peers &mdash; does it begin to do useful work. "
        "The choice before us was never between thinking for ourselves and trusting others. It "
        "is the harder, more adult task of doing both at once: doubting like a scientist "
        "rather than like someone determined in advance to believe nothing."),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Do not take the experts' word for it; look into the matter yourself. In recent years "
    "this advice has hardened into something like a creed. To question official knowledge is "
    "presented as a mark of intellectual courage, while accepting what specialists say is "
    "dismissed as laziness, or worse, as the quiet surrender of one's own judgment. The truly "
    "independent thinker, we are told, verifies everything personally and bows to no "
    "authority. And yet, this flattering picture of the self-reliant mind, for all its "
    "appeal, rests on an illusion, one that becomes visible the moment we ask what checking "
    "for yourself actually involves. "
    "It is true that experts are fallible, and that the record of blind deference to them is "
    "not a happy one. Specialists have defended theories that later collapsed, and "
    "institutions have at times protected their own reputation more carefully than the public "
    "they were meant to serve. Whole fields have had to withdraw claims once announced with "
    "confidence. Anyone who urges us simply to obey the credentialed, no questions asked, has "
    "not read much history. The suspicion that now surrounds expertise did not come from "
    "nowhere; it was, in part, earned. "
    "Nonetheless, the ideal of checking everything for oneself dissolves the moment it is "
    "examined. The person who does her own research does not visit the laboratory, repeat the "
    "experiments, or re-derive the statistics; she reads documents written by strangers, "
    "posted on platforms built by other strangers, summarizing measurements she will never "
    "witness. Every step of her inquiry borrows the labor, and the honesty, of people she has "
    "never met. It is not that independent verification is a noble goal we sadly fail to "
    "reach, but that, for creatures whose knowledge is stitched together from the testimony "
    "of others, complete intellectual self-reliance was never a possibility in the first "
    "place. "
    "What looks like a private achievement, then, is in fact a social arrangement. Modern "
    "knowledge has grown far beyond the capacity of any single head: the chemist trusts the "
    "physicist, the doctor trusts the medical journal, and all of them trust instruments that "
    "none of them could build alone. Never in this long division of labor has reliance on "
    "others been a sign of idleness; it is the very mechanism by which a community comes to "
    "know more than any of its members. To trust well, on this view, is not to stop thinking "
    "but to think with other people. "
    "Does it follow that we may believe whomever we please? Hardly. Trust, practiced well, "
    "carries its own instruments of testing. We can ask whether a speaker stands to profit "
    "from being believed; whether she has admitted and corrected her past errors, or quietly "
    "buried them; and whether those best placed to catch her mistakes, rivals within her own "
    "field, have largely come to agree with her. None of these checks requires us to repeat "
    "the science ourselves; they demand something humbler and more attainable, attention to "
    "how a claim has survived the scrutiny of others. "
    "The real question, therefore, is poorly framed as a choice between trusting and "
    "doubting. What we need is not a verdict on experts but a craft of trust: the discipline "
    "of judging whom to believe, about which questions, and on what grounds. A physicist "
    "deserves our confidence about particles, not necessarily about politics; a careful "
    "weigher of evidence in one domain may be a novice in the next. Framed this way, trust "
    "ceases to be a lapse of intelligence and becomes one of its most demanding exercises. "
    "None of this asks us to abandon doubt; a healthy intellectual culture needs skeptics as "
    "a body needs an immune system. But doubt spread evenly over everything protects nothing; "
    "it merely exhausts us. Only when suspicion is aimed, informed by a speaker's interests, "
    "record, and peers, does it begin to do useful work. The choice before us was never "
    "between thinking for ourselves and trusting others. It is the harder, more adult task of "
    "doing both at once: doubting like a scientist rather than like someone determined in "
    "advance to believe nothing."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① And yet &nbsp; ② As a result &nbsp; ③ For example &nbsp; ④ Furthermore",
         "【 B 】 &nbsp; ① Therefore &nbsp; ② Nonetheless &nbsp; ③ For instance &nbsp; ④ Likewise",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(1) <span class='en'>It is not that independent verification is a noble goal "
             "we sadly fail to reach, but that, for creatures whose knowledge is stitched "
             "together from the testimony of others, complete intellectual self-reliance was "
             "never a possibility in the first place.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(2) について、信頼が「自前の検査の道具を備えている（<span class='en'>carries its own "
             "instruments of testing</span>）」とはどういうことか。本文に即して具体的に日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "第4段で述べられる「知識の分業」についての筆者の考えとして最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 知識の分業は個々人の思考力を確実に衰えさせるので、可能な限り個人の検証に置き換えていくべきである。",
         "② 他人への信頼は怠慢のしるしではなく、共同体が個々の成員の限界を超えて知るための仕組みそのものである。",
         "③ 専門家たちは互いをまったく信頼していないからこそ、科学の共同体は誤りを自ら正すことができるのである。",
         "④ 現代の知識も努力しだいで一人で抱えきれるが、分業のほうが効率的なので信頼が選ばれているにすぎない。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>not a verdict on experts but a craft of trust</span>"
             "（専門家への判定ではなく、信頼の技術）とはどういうことか。本文全体をふまえて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 専門家や制度は歴史的に誤りを重ねてきたのだから、専門知を疑ってかかることこそが知的に誠実な唯一の態度である。",
         "② 完全に独力で検証することは誰にもできない以上、私たちは疑うこと自体を手放し、判断をすべて専門家に委ねるほかない。",
         "③ 問うべきは信頼か懐疑かの二択ではなく、誰を・何について・どんな根拠で信頼するかという技術であり、それは知性の行使である。",
         "④ 信頼とは共同体全体で成り立つ仕組みなのだから、個人が語り手の利害や訂正の履歴をいちいち確かめる必要はまったくない。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 筆者によれば、専門家や学問の制度がかつて重大な誤りを犯したり主張を撤回したりしたことは一度もない。",
         "② 「自分で調べる」人も、実際には見知らぬ他人が作った文書や測定の要約に頼ってその調査を行っている。",
         "③ 語り手が信じてもらうことで利益を得る立場かどうかは、信頼するか否かの判断とは無関係だと筆者は述べている。",
         "④ あらゆる主張へ等しく疑いを向け続けることこそが、結局は私たちを最もよく守ると筆者は主張している。",
         "⑤ 物理学者は素粒子については信頼に値するとしても、政治についても同様に信頼できるとは限らない。",
         "⑥ 筆者は疑うことをやめよと説くのではなく、疑いを有効に働かせるために狙いの定まった信頼の判断を説いている。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ① And yet　　B ＝ ② Nonetheless",
     "exp": "A：第1段前半は「専門家を鵜呑みにせず自分で調べよ」という通念の礼賛。直後で筆者は「この自立した"
            "精神像は幻想の上に成り立つ」と反転する → <b>逆接</b> And yet。As a result（因果）・"
            "For example（例示）・Furthermore（追加）は不可。<br>"
            "B：第2段「It is true that …（確かに専門家も誤る）」という譲歩を受け、第3段は「それでも"
            "『すべて自分で確かめる』という理想は崩れる」と主張へ<b>転換</b>する → 逆接 Nonetheless。"
            "Therefore（因果）・For instance（例示）・Likewise（類比）は流れに合わない。"
            " 〔<b>解法ルール R7</b>／<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "②",
     "exp": "第4段「Never in this long division of labor has reliance on others been a sign of "
            "idleness; it is the very mechanism by which a community comes to know more than any "
            "of its members」＝他人への信頼は怠惰のしるしではなく、共同体が成員の限界を超えて知るための"
            "仕組みそのもの。①は逆（分業を個人の検証に置き換えよとは述べていない）。③は主語のすり替え"
            "（本文は the chemist trusts the physicist と、専門家同士の信頼をむしろ前提にしている。"
            "ライバルの相互チェックは第5段の「信頼の検査」の話）。④は逆（far beyond the capacity of "
            "any single head＝一人では抱えきれない）。 〔<b>解法ルール R9</b>／<b>構文ルール R23</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "③",
     "exp": "第6段「What we need is not a verdict on experts but a craft of trust: the discipline "
            "of judging whom to believe, about which questions, and on what grounds」＋同段末"
            "「trust … becomes one of its most demanding exercises（知性の最も骨の折れる行使の一つ）」"
            "と一致。①は第1段の通念そのもので、筆者はこれを幻想と呼ぶ。②は言い過ぎ（第7段 None of this "
            "asks us to abandon doubt に反する）。④は第5段（利害・訂正の履歴の検査をまさに求めている）に"
            "真っ向から反する。 〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "②・⑤・⑥",
     "exp": "①×：第2段「Specialists have defended theories that later collapsed」「Whole fields "
            "have had to withdraw claims …」に正反対（「一度もない」は典型的な<b>言い過ぎ</b>）。"
            "③×：第5段は「whether a speaker stands to profit from being believed」をまさに確かめよと"
            "述べている（無関係どころか判断材料）。④×：第7段「doubt spread evenly over everything "
            "protects nothing（等しくばらまかれた疑いは何も守らない）」に反する。"
            " 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(1)和訳",
     "model": "独力の検証とは、私たちが残念ながら到達できずにいる崇高な目標だ、ということではない。そうでは"
              "なく、その知識が他人の証言からつなぎ合わされてできている生き物（＝人間）にとって、完全な知的"
              "自立というものは、そもそも初めから可能ですらなかった、ということなのだ。",
     "points": "▶<b>採点要素</b>：①<b>It is not that A but that B</b>＝「AなのではなくBなのだ」——not の"
               "射程は that 節A全体に及ぶ（「崇高な目標でない」と訳すのは誤り）〔<b>読解ルール R22</b>〕／"
               "②a noble goal (that) we sadly fail to reach＝関係詞省略「私たちが残念ながら届かずにいる"
               "崇高な目標」／③whose knowledge is stitched together from the testimony of others＝"
               "「その知識が他人の証言から縫い合わされている」（for creatures … は挿入の副詞句）／"
               "④never a possibility in the first place＝「そもそも初めから可能性ではなかった」。"},
    {"no": "問3", "pts": "8点・記述",
     "model": "信頼は盲信とは違い、根拠を確かめる手立てを伴っているということ。具体的には、語り手が信じられる"
              "ことで利益を得る立場にないか、過去の誤りを認めて訂正してきたか（それともひそかに葬ったか）、"
              "同じ分野で誤りを見つけるのに最も適したライバルたちがおおむね同意しているか、を確かめることで、"
              "科学そのものを自分で繰り返さなくても、主張が他人の吟味を生き延びてきたかを検査できる、という"
              "こと。",
     "points": "▶<b>採点要素</b>：①「盲信ではなく、信頼には根拠の確かめ方がある」という核／②検査の中身＝"
               "〈発言者の利害〉〈訂正の履歴〉〈同分野の合意〉（第5段）から二つ以上／③「科学を自分で繰り返す"
               "必要はない」（＝もっと謙虚で手の届く方法）への言及。 〔<b>解法ルール R8</b>／"
               "<b>読解ルール R14</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "必要なのは、専門家（一般）を信じるべきか疑うべきかという一括の判定を下すことではなく、誰を、"
              "どの問題について、どんな根拠で信頼するかを、その都度判断する技術だ、ということ。信頼は領域ごと"
              "に与えるべきものであり（物理学者は素粒子については信頼に値しても、政治については限らない）、"
              "そのように行われる信頼は知性の放棄ではなく、むしろその最も骨の折れる行使である。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b> の対比＝「専門家への一括の判定（信じる／疑うの二択）」"
               "の否定〔<b>読解ルール R3</b>〕（3点）／②「誰を・何について・どんな根拠で」を個別に判断する"
               "<b>技術・鍛錬</b>であること（4点）／③その信頼は知性の放棄ではなく行使である（第6段末）こと"
               "（3点）。 〔<b>解法ルール R8</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（And yet→自立像は幻想という筆者の反転）、空所B（Nonetheless→主張転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that experts are fallible …」→ 第3段 Nonetheless で反転。"),
        ("R3", "not A but B は <b>B</b> が核心／A rather than B は <b>A</b> が核心"
               "——どちらも「否定される側」が通念", "★★★",
         "下線部(3) not a verdict on experts but a craft of trust、第4段 not to stop thinking but "
         "to think with other people、第7段 doubting like a scientist rather than …"
         "（rather than は<b>語順が逆</b>で、前の doubting like a scientist が核心。→ 文法 G3）。"),
        ("R14", "反対意見・コスト批判への「再反論」は主張の強化——譲歩⇄再反論の往復を追う", "★★★",
         "第5段「Does it follow that we may believe whomever we please? Hardly.」→ 信頼の検査道具で再反論。"),
        ("R22", "★NEW It is not that A but that B／not because A but because B——否定がどこまで及ぶか（否定の射程）を確定してから訳す", "★★★",
         "下線部(1)＝問2。not の射程は that 節A全体（「目標が崇高でない」のではない）。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。A・Bとも前後がぶつかる＝逆接。因果・例示・追加・類比の distractor を消す。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。コロン(:)・not A but B・ダッシュの言い換えを利用して核を組み立てる。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。①「一度もない」・④「等しく疑うことが守る」などの言い過ぎ・逆転を排除。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "documents &lt;written by strangers, posted on …, summarizing …&gt;、theories &lt;that later collapsed&gt; など頻出。"),
        ("R23", "★NEW 倒置——否定・限定の副詞（句）が文頭に出ると疑問文の語順になる（Never / Only / Little など）", "★★★",
         "第4段 Never in this long division of labor <b>has reliance</b> … been ～、第7段 Only when suspicion is aimed … <b>does it begin</b> ～。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「専門家を鵜呑みにせず自分で調べよ」＝知的勇気、受け入れる＝思考の放棄、という風潮を提示。"
             "→ <b>And yet（R1）</b>：この「自立した精神」の像は幻想の上に成り立っている。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに専門家も誤り、盲従の歴史も本物。理論の崩壊・主張の撤回は"
             "実際にあった。専門知への疑念は部分的には「身から出た錆」。＝通念の一部は認める。"},
    {"arrow": "◀ Nonetheless 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "「自分で調べる」もまた、見知らぬ他人の労働と誠実さへの<b>信頼の連鎖</b>で成り立つ。"
             "<b>It is not that A but that B（R22）</b>：完全な知的自立はそもそも不可能だった。"},
    {"arrow": "↓　深化"},
    {"role": "深化", "para": "¶4", "kind": "reason",
     "text": "<b>知識の分業</b>：現代の知は一人の頭を超え、信頼は怠慢ではなく共同体が成員の限界を超えて知る"
             "<b>仕組み</b>（Never 倒置＝R23）。信頼するとは考えるのをやめることではなく「他人とともに考える」こと（R3）。"},
    {"arrow": "◀ では誰でも信じてよいのか？ → 再反論（R14） ▶"},
    {"role": "再反論", "para": "¶5", "kind": "reason",
     "text": "信頼には<b>検査の道具</b>がある：①発言者の利害 ②訂正の履歴 ③同分野のライバルの合意。"
             "科学を自分で繰り返さなくても、主張が「吟味を生き延びたか」は確かめられる。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "問いは「信頼か懐疑か」ではない。<b>not a verdict on experts but a craft of trust（R3）</b>＝"
             "誰を・何について・どんな根拠で信頼するかという<b>技術</b>。信頼は知性の放棄ではなく、その最も"
             "骨の折れる行使。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：疑うことを捨てよという話ではない（懐疑は免疫系）。だが等しくばらまかれた疑いは"
             "何も守らない。<b>狙いの定まった疑い（Only 倒置＝R23）</b>だけが働く——自分で考えることと他人を"
             "信頼することを同時に行え。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 「自分で調べる」の通念と実態",
     "caption": "同じ「自分で調べる」でも、通念は<b>誰にも頼らない独力の検証</b>を想定する。だが実態は"
                "<b>見知らぬ他人への信頼の連鎖</b>——文書を書く人・基盤を作る人・測定する人の労働と誠実さを"
                "借りて成り立つ。完全な知的自立はそもそも不可能（第3段）。",
     "para": "→ 第1・3段"},
    {"id": "fig2", "title": "図2 ｜ 信頼の検査道具（instruments of testing）",
     "caption": "信頼は盲信ではなく、<b>検査の道具</b>を持つ。①<b>語り手側</b>：信じられることで利益を得る"
                "立場か・過去の誤りを訂正してきたか、②<b>共同体側</b>：同分野のライバルがおおむね同意して"
                "いるか。下線部(2)の instruments はこれを指す。",
     "para": "→ 第5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 「判定」ではなく「信頼の技術」",
     "caption": "問うべきは「信頼か懐疑か」の一括判定ではなく、<b>誰を・何について・どんな根拠で</b>信頼する"
                "かという技術。このとき信頼は知性の放棄ではなく、その<b>最も骨の折れる行使</b>になる。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "「専門家の言うことを鵜呑みにするな。その問題は自分で調べよ。」近年、この助言は信条のようなものへと"
        "固まってきた。公式の知識を疑うことは知的勇気の証として示され、専門家の言うことを受け入れることは"
        "怠惰として——さらに悪くすれば、自分自身の判断の静かな放棄として——退けられる。真に独立した思考の"
        "持ち主は、あらゆることを自分の手で検証し、いかなる権威にも屈しないのだ——と私たちは聞かされる。"
        "<b>だがそれでも</b>、この自立した精神という心地よい像は、その魅力にもかかわらず、一つの幻想の上に"
        "成り立っている——「自分で確かめる」ということが実際に何を含むのかを問うた瞬間に見えてくる幻想の上に。"),
    (2, "確かに、専門家は誤りうるし、彼らへの盲目的な服従の記録が幸福なものでないことも本当である。専門家たち"
        "は後に崩れ去る理論を擁護してきたし、諸制度は時に、本来仕えるべき公衆よりも自らの評判のほうを入念に"
        "守ってきた。分野全体が、かつて自信をもって発表された主張を撤回せねばならなかったこともある。資格ある"
        "者に何も問わずただ従え、と促す者は、歴史をろくに読んでいない。今日専門知を取り巻く疑念は、どこからと"
        "もなく生じたのではない。それは部分的には、自ら招いたものなのだ。"),
    (3, "<b>それにもかかわらず</b>、すべてを自分で確かめるという理想は、検討されたその瞬間に溶けて消える。"
        "「自分で調べる」人は、実験室を訪れもしなければ、実験を繰り返しもせず、統計を導き直しもしない。"
        "見知らぬ他人が書き、別の見知らぬ他人が作った基盤に載せられ、自分では決して目にすることのない測定を"
        "要約した文書を、読むのである。彼女の調査の一歩一歩が、会ったこともない人々の労働と誠実さとを借りて"
        "いる。<b>独力の検証とは、私たちが残念ながら到達できずにいる崇高な目標だ、ということではない。そうで"
        "はなく、その知識が他人の証言からつなぎ合わされてできている生き物にとって、完全な知的自立というものは、"
        "そもそも初めから可能ですらなかった、ということなのだ。</b>"),
    (4, "とすると、個人の達成のように見えるものは、実のところ社会的な仕組みである。現代の知識は、どの一人の"
        "頭の容量をもはるかに超えて成長した。すなわち、化学者は物理学者を信頼し、医師は医学誌を信頼し、そして"
        "彼らの全員が、誰一人単独では作れない機器を信頼している。この長い分業の歴史の中で、他人に頼ることが"
        "怠惰のしるしであったことは一度もない。それは、共同体がその成員の誰よりも多くを知るに至る、まさにその"
        "仕組みなのである。上手に信頼するとは、この見方に立てば、考えるのをやめることではなく、他人とともに"
        "考えることなのだ。"),
    (5, "では、誰でも好きな人を信じてよい、ということになるのだろうか。まさか、そうではない。<b>正しく実践"
        "されるなら、信頼はそれ自身の検査の道具を備えている。</b>私たちは問うことができる——語り手は、信じて"
        "もらうことで利益を得る立場にないか。過去の誤りを認めて訂正してきたか、それともひそかに葬ってきたか。"
        "そして、その誤りを見つけるのに最も適した人々——同じ分野のライバルたち——が、おおむねその人に同意する"
        "に至っているか。これらの検査のどれ一つとして、科学を自分で繰り返すことを私たちに求めはしない。それら"
        "が求めるのは、もっと謙虚で、もっと手の届くもの——ある主張が他人の吟味をどのように生き延びてきたのか"
        "への注意である。"),
    (6, "したがって本当の問いは、「信頼するか、疑うか」という二者択一として立てるのではまずい。私たちに必要な"
        "のは、<b>専門家への判定ではなく、信頼の技術</b>——誰を信じるか、どの問題について、どんな根拠で、を"
        "判断する鍛錬——なのだ。物理学者は素粒子については私たちの信頼に値するが、必ずしも政治についてでは"
        "ない。ある領域で証拠を慎重に量れる人も、隣の領域では素人かもしれない。このように問いを立て直せば、"
        "信頼は知性の放棄であることをやめ、その最も骨の折れる行使の一つとなる。"),
    (7, "以上のどれも、疑うことを捨てよと求めるものではない。健全な知的文化が懐疑派を必要とするのは、身体が"
        "免疫系を必要とするのと同じである。だが、あらゆるものの上に等しくばらまかれた疑いは、何も守らない——"
        "ただ私たちを疲れさせるだけだ。疑いが狙いを定められて——語り手の利害、実績、同業者の評価に裏づけられて"
        "——初めて、それは有用な仕事をし始める。私たちの前にある選択は、自分で考えることと他人を信頼することと"
        "の間の選択では、決してなかった。それは、両方を同時に行うという、より難しく、より大人の課題である。"
        "すなわち、初めから何も信じまいと決めてかかる者のようにではなく、科学者のように疑う、ということなのだ。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("take A's word for it", "Aの言葉を（確かめずに）そのまま信じる"),
    ("harden into ~", "固まって〜になる"),
    ("creed", "信条、教義"),
    ("dismiss A as B", "AをBだとして退ける"),
    ("surrender", "放棄、明け渡し"),
    ("for all ~", "〜にもかかわらず"),
    ("rest on ~", "〜の上に成り立つ、〜に基づく"),
    ("fallible", "誤りうる"),
    ("deference", "（敬意からの）服従、追従"),
    ("withdraw", "撤回する"),
    ("the credentialed", "資格・肩書きを持つ人々"),
    ("no questions asked", "何も問わずに"),
    ("dissolve", "溶けて消える、崩れる"),
    ("testimony", "証言"),
    ("stitch together", "縫い合わせる、つなぎ合わせる"),
    ("self-reliance", "自立、独力"),
    ("division of labor", "分業"),
    ("idleness", "怠惰"),
    ("stand to do", "〜する立場にある"),
    ("scrutiny", "綿密な吟味、精査"),
    ("verdict", "評決、判定"),
    ("novice", "初心者、素人"),
    ("lapse", "（一時的な）放棄、失効、過失"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：「自分で調べよ」という通念と、その反転",
  "sentences": [
    {"chunks": [("V","Do not take","そのまま信じるな"),
                ("O","the experts' word","専門家の言葉を"),
                ("M","(for it);","その件について"),
                ("V","look into","調べよ"),("O","the matter","その問題を"),
                ("M","yourself.","自分自身で")],
     "note":"▶ 命令文の二連発＝世間の合言葉（通念）の引用的提示。<b>take A's word for it</b>＝「Aの言葉を（確かめずに）信じる」。"},
    {"chunks": [("M","(In recent years)","近年"),("S","this advice","この助言は"),
                ("V","has hardened","固まってきた"),
                ("M","(into something like a creed).","信条のようなものへと")],
     "note":"▶ harden into A＝「固まってAになる」。現在完了＝現在に至る変化。"},
    {"chunks": [("S","To question official knowledge","公式の知識を疑うことは"),
                ("V","is presented","示され"),
                ("M","(as a mark of intellectual courage),","知的勇気の証として"),
                ("接","while","一方"),
                ("S","accepting [what specialists say]","専門家の言うことを受け入れることは"),
                ("V","is dismissed","退けられる"),
                ("M","(as laziness &mdash; or worse, as the quiet surrender of one's own judgment).","怠惰として——さらに悪ければ、自分自身の判断の静かな放棄として")],
     "note":"▶ 不定詞句・動名詞句がそれぞれ主語。<b>present A as B／dismiss A as B</b> の受動態。what specialists say＝関係代名詞 what の名詞節。"},
    {"chunks": [("S","The truly independent thinker,","真に独立した思考の持ち主は"),
                ("M","we are told,","——と私たちは聞かされる——"),
                ("V","verifies","検証し"),("O","everything","あらゆることを"),
                ("M","personally","自分の手で"),
                ("接","and","そして"),("V","bows to","屈する"),
                ("O","no authority.","いかなる権威にも（〜ない）")],
     "note":"▶ we are told＝コンマに挟まれた挿入。bow to <b>no</b> authority＝否定語が目的語に入り「どんな権威にも屈しない」。"},
    {"chunks": [("接","And yet,","だがそれでも"),
                ("S","this flattering picture of the self-reliant mind,","この自立した精神という心地よい像は"),
                ("M","(for all its appeal),","その魅力にもかかわらず"),
                ("V","rests on","〜の上に成り立っている"),
                ("O","an illusion","一つの幻想"),
                ("-","&mdash; one &lt;that becomes visible (the moment we ask [what &ldquo;checking for yourself&rdquo; actually involves])&gt;.","——「自分で確かめる」が実際に何を含むかを問うた瞬間に見えてくる幻想")],
     "note":"▶ <b>R1｜逆接 And yet の直後が筆者の主張</b>（＝空所A）。for all ～＝「〜にもかかわらず」。one＝an illusion の言い換え（同格）。the moment SV＝「〜する瞬間に」。"},
  ]},
 {"head": "第2段 — 譲歩：確かに専門家も誤る（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当だ"),
                ("-","[that experts are fallible], and [that the record of blind deference to them is not a happy one].","専門家も誤りうるということ、そして彼らへの盲目的な服従の記録が幸福なものでないということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。真主語の that 節が2つ並列。fallible＝「誤りうる」。one＝record の代用。"},
    {"chunks": [("S","Specialists","専門家たちは"),("V","have defended","擁護してきた"),
                ("O","theories &lt;that later collapsed&gt;,","後に崩れ去った理論を"),
                ("接","and","そして"),("S","institutions","諸制度は"),
                ("V","have at times protected","時に守ってきた"),
                ("O","their own reputation","自らの評判を"),
                ("M","(more carefully than the public &lt;(that) they were meant to serve&gt;).","本来仕えるべき公衆よりも入念に")],
     "note":"▶ that later collapsed＝関係代名詞〔<b>R11</b>〕。比較 more carefully than ～。the public (that) they were meant to serve＝関係詞省略。be meant to do＝「〜することになっている」。"},
    {"chunks": [("S","Whole fields","分野全体が"),("V","have had to withdraw","撤回せねばならなかった"),
                ("O","claims &lt;once announced with confidence&gt;.","かつて自信をもって発表された主張を")],
     "note":"▶ 過去分詞 announced … が claims を後ろから修飾〔<b>R11</b>〕。have had to do＝現在完了＋have to。"},
    {"chunks": [("S","Anyone &lt;who urges us simply to obey the credentialed, no questions asked,&gt;","資格ある者に何も問わずただ従えと促す者は誰であれ"),
                ("V","has not read","読んでこなかった"),
                ("O","much history.","歴史をろくに")],
     "note":"▶ urge O to do＝「Oに〜するよう促す」。<b>the＋形容詞（分詞）</b>＝the credentialed「資格を持つ人々」。no questions asked＝「何の質問もなしに」（独立分詞構文由来の定型句）。"},
    {"chunks": [("S","The suspicion &lt;that now surrounds expertise&gt;","今日専門知を取り巻く疑念は"),
                ("V","did not come","生じたのではない"),
                ("M","(from nowhere);","どこからともなく"),
                ("S","it","それは"),("V","was, in part, earned.","部分的には、自ら招かれたものだ")],
     "note":"▶ that＝主格の関係代名詞〔<b>R11</b>〕。earn＝「（当然の報いとして）得る」→受動で「身から出た錆」の含み。in part＝挿入。譲歩の締め。"},
  ]},
 {"head": "第3段 — 主張転換：「自分で調べる」も信頼の連鎖（Nonetheless）",
  "sentences": [
    {"chunks": [("接","Nonetheless,","それにもかかわらず"),
                ("S","the ideal of checking everything for oneself","すべてを自分で確かめるという理想は"),
                ("V","dissolves","溶けて消える"),
                ("M","(the moment it is examined).","検討されたその瞬間に")],
     "note":"▶ <b>R1｜逆接 Nonetheless の直後が主張転換点</b>（＝空所B）。the moment SV＝「〜する瞬間に」。dissolve＝「（検討に耐えず）崩れる」。"},
    {"chunks": [("S","The person &lt;who &ldquo;does her own research&rdquo;&gt;","「自分で調べる」人は"),
                ("V","does not visit","訪れもせず"),("O","the laboratory,","実験室を"),
                ("V","repeat","繰り返しもせず"),("O","the experiments,","実験を"),
                ("V","or re-derive","導き直しもしない"),("O","the statistics;","統計を"),
                ("S","she","彼女は"),("V","reads","読むのである"),
                ("O","documents &lt;written by strangers, posted on platforms built by other strangers, summarizing measurements she will never witness&gt;.","見知らぬ他人が書き、別の見知らぬ他人が作った基盤に載せられ、彼女が決して目にしない測定を要約した文書を")],
     "note":"▶ 3つの動詞（visit / repeat / re-derive）の並列否定。written / posted / summarizing＝3つの分詞句が documents を後ろから修飾〔<b>R11</b>〕。measurements (that) she will never witness＝関係詞省略。"},
    {"chunks": [("S","Every step of her inquiry","彼女の調査の一歩一歩が"),
                ("V","borrows","借りている"),
                ("O","the labor, and the honesty, of people &lt;(that) she has never met&gt;.","会ったこともない人々の労働と、誠実さとを")],
     "note":"▶ the labor と the honesty をコンマで並べて強調。people (that) she has never met＝関係詞省略〔<b>R11</b>〕。「調べる」＝他人への信頼の連鎖、の核となる一文。"},
    {"chunks": [("S","It","（形式的な主語）"),("V","is","である"),
                ("C","not [that independent verification is a noble goal &lt;(that) we sadly fail to reach&gt;],","独力の検証が、私たちが残念ながら届かずにいる崇高な目標だ、ということではなく"),
                ("接","but","そうではなく"),
                ("C","[that, (for creatures &lt;whose knowledge is stitched together from the testimony of others&gt;), complete intellectual self-reliance was never a possibility (in the first place)].","その知識が他人の証言から縫い合わされている生き物にとって、完全な知的自立はそもそも初めから可能性ではなかった、ということだ")],
     "note":"▶ <b>R22｜It is not that A but that B</b>＝「AなのではなくBなのだ」——<b>not の射程は that 節A全体</b>（「目標が崇高でない」と訳すと誤訳）。for creatures …＝挿入の副詞句。whose＝所有格の関係代名詞〔<b>R11</b>〕。＝<b>下線部(1)＝問2</b>。"},
  ]},
 {"head": "第4段 — 深化：知識の分業——信頼は怠慢ではなく仕組み",
  "sentences": [
    {"chunks": [("S","[What looks like a private achievement],","個人の達成のように見えるものは"),
                ("M","then,","とすると"),("V","is","である"),
                ("M","in fact","実のところ"),
                ("C","a social arrangement.","社会的な仕組み")],
     "note":"▶ 関係代名詞 what の名詞節が主語。then＝「とすると」（前段の帰結）。"},
    {"chunks": [("S","Modern knowledge","現代の知識は"),("V","has grown","成長した"),
                ("M","(far beyond the capacity of any single head):","どの一人の頭の容量もはるかに超えて"),
                ("S","the chemist","化学者は"),("V","trusts","信頼し"),("O","the physicist,","物理学者を"),
                ("S","the doctor","医師は"),("V","trusts","信頼し"),("O","the medical journal,","医学誌を"),
                ("接","and","そして"),("S","all of them","彼らの全員が"),("V","trust","信頼する"),
                ("O","instruments &lt;that none of them could build alone&gt;.","誰一人単独では作れない機器を")],
     "note":"▶ コロン(:)＝直前の抽象（頭の容量を超えた）の具体化。that＝関係代名詞〔<b>R11</b>〕。none of them＝「彼らの誰一人〜ない」。"},
    {"chunks": [("M","Never (in this long division of labor)","この長い分業の中で一度も（〜ない）"),
                ("V","has","（倒置の助動詞）"),
                ("S","reliance on others","他人への信頼が"),
                ("V","been","であったことは"),
                ("C","a sign of idleness;","怠惰のしるしで"),
                ("S","it","それは"),("V","is","である"),
                ("C","the very mechanism &lt;by which a community comes to know more than any of its members&gt;.","共同体がその成員の誰より多くを知るに至る、まさにその仕組み")],
     "note":"▶ <b>R23｜倒置</b>——否定の副詞 Never が文頭に出て <b>has reliance … been</b> と疑問文の語順に。by which＝前置詞＋関係代名詞〔<b>R11</b>〕。the very ～＝「まさにその〜」。"},
    {"chunks": [("S","To trust well,","上手に信頼することは"),
                ("M","on this view,","この見方では"),
                ("V","is","である"),
                ("C","not to stop thinking but to think with other people.","考えるのをやめることではなく、他人とともに考えること")],
     "note":"▶ <b>R3｜not A but B＝Bが核心</b>。不定詞句が主語・補語。第4段の結論＝「信頼＝共同の思考」。"},
  ]},
 {"head": "第5段 — 再反論：では誰でも信じてよいのか？（R14）",
  "sentences": [
    {"chunks": [("V","Does it follow","当然の帰結になるのか"),
                ("-","[that we may believe whomever we please]?","誰でも好きな人を信じてよい、ということが")],
     "note":"▶ it＝形式主語。follow＝「（論理的に）帰結する」。whomever we please＝複合関係代名詞「誰でも好きな人を」。<b>R14｜反対視点を自問で提示→直後に再反論</b>。"},
    {"chunks": [("M","Hardly.","まさか（決してそうではない）")],
     "note":"▶ 一語文。Hardly＝準否定語による強い否定「とんでもない」。再反論の開始の合図。"},
    {"chunks": [("S","Trust,","信頼は"),
                ("M","(practiced well),","正しく実践されるなら"),
                ("V","carries","備えている"),
                ("O","its own instruments of testing.","それ自身の検査の道具を")],
     "note":"▶ practiced well＝過去分詞の挿入（＝if it is practiced well）。＝<b>下線部(2)＝問3</b>。「道具」の中身は次文で列挙される。"},
    {"chunks": [("S","We","私たちは"),("V","can ask","問うことができる"),
                ("O","[whether a speaker stands to profit from being believed];","語り手が、信じられることで利益を得る立場にないか"),
                ("O","[whether she has admitted and corrected her past errors, or quietly buried them];","過去の誤りを認めて訂正してきたか、それともひそかに葬ったか"),
                ("接","and","そして"),
                ("O","[whether those &lt;best placed to catch her mistakes&gt; &mdash; rivals within her own field &mdash; have largely come to agree with her].","その誤りを見つけるのに最も適した人々——同分野のライバルたち——が、おおむね彼女に同意するに至っているか")],
     "note":"▶ whether 節×3の並列（すべて ask の目的語）。stand to do＝「〜する立場にある」。those &lt;best placed to do&gt;＝過去分詞の後置修飾「〜するのに最も適した人々」〔<b>R11</b>〕。ダッシュ＝同格の言い換え。"},
    {"chunks": [("S","None of these checks","これらの検査のどれ一つ"),
                ("V","requires","求めない"),("O","us","私たちに"),
                ("C","to repeat the science ourselves;","科学を自分で繰り返すことを"),
                ("S","they","それらは"),("V","demand","求める"),
                ("O","something humbler and more attainable","もっと謙虚で、もっと手の届くものを"),
                ("-","&mdash; attention to [how a claim has survived the scrutiny of others].","——主張が他人の吟味をどう生き延びてきたかへの注意を")],
     "note":"▶ require O to do。-thing＋形容詞は後置（something humbler）。how 節＝名詞節（to の目的語）。ダッシュ＝同格（something の中身）。"},
  ]},
 {"head": "第6段 — ★核心：問いは「信頼か懐疑か」ではなく「信頼の技術」",
  "sentences": [
    {"chunks": [("S","The real question,","本当の問いは"),
                ("M","therefore,","したがって"),
                ("V","is poorly framed","まずい形で立てられている"),
                ("M","(as a choice between trusting and doubting).","信頼か懐疑かの二者択一として")],
     "note":"▶ frame A as B（AをBとして立てる）の受動。between A and B＝動名詞の並列。「二択の枠組みそのものが誤り」→次文が正しい問い。"},
    {"chunks": [("S","[What we need]","私たちに必要なもの"),
                ("V","is","は〜である"),
                ("C","not a verdict on experts but a craft of trust:","専門家への判定ではなく、信頼の技術"),
                ("-","the discipline of judging [whom to believe], (about which questions), and (on what grounds).","すなわち、誰を信じるかを——どの問題について・どんな根拠で——判断する鍛錬")],
     "note":"▶ <b>R3｜not A but B＝Bが核心</b>。コロン(:)＝a craft of trust の定義・言い換え。whom to believe＝疑問詞＋to不定詞。＝<b>下線部(3)＝問5</b>。"},
    {"chunks": [("S","A physicist","物理学者は"),("V","deserves","値する"),
                ("O","our confidence","私たちの信頼に"),
                ("M","(about particles), not necessarily (about politics);","素粒子については——だが必ずしも政治についてではない"),
                ("S","a careful weigher of evidence in one domain","ある領域で証拠を慎重に量れる人も"),
                ("V","may be","かもしれない"),
                ("C","a novice in the next.","隣の領域では素人")],
     "note":"▶ not necessarily＝部分否定「必ずしも〜ではない」。「信頼は領域ごと」という抽象の具体化。weigher＝weigh（量る）の名詞化。"},
    {"chunks": [("M","(Framed this way),","このように問いを立て直せば"),
                ("S","trust","信頼は"),
                ("V","ceases to be","であることをやめ"),
                ("C","a lapse of intelligence","知性の放棄"),
                ("接","and","そして"),
                ("V","becomes","なる"),
                ("C","one of its most demanding exercises.","その最も骨の折れる行使の一つに")],
     "note":"▶ 過去分詞の分詞構文（＝If it is framed this way）。cease to do＝「〜しなくなる」。its＝intelligence's。核心の締め＝「信頼は知性の行使」。"},
  ]},
 {"head": "第7段 — 譲歩つき結論：疑いを有効にするための信頼の設計",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),
                ("V","asks","求めてはいない"),("O","us","私たちに"),
                ("C","to abandon doubt;","疑うことを捨てるようにとは"),
                ("S","a healthy intellectual culture","健全な知的文化は"),
                ("V","needs","必要とする"),("O","skeptics","懐疑派を"),
                ("M","(as a body needs an immune system).","身体が免疫系を必要とするように")],
     "note":"▶ ask O to do。as SV＝「〜するように」（様態）。譲歩つき結論の開始——懐疑の価値は認める。"},
    {"chunks": [("接","But","だが"),
                ("S","doubt &lt;spread evenly over everything&gt;","あらゆるものの上に等しくばらまかれた疑いは"),
                ("V","protects","守らない"),("O","nothing","何も"),
                ("-","&mdash; it merely exhausts us.","——それはただ私たちを疲れさせるだけだ")],
     "note":"▶ spread＝過去分詞の後置修飾（spread–spread–spread）〔<b>R11</b>〕。protect <b>nothing</b>＝否定語が目的語。<b>R9注意</b>：設問④「等しく疑うことが守る」はこの一文で×。"},
    {"chunks": [("M","Only (when suspicion is aimed &mdash; informed by a speaker's interests, record, and peers &mdash;)","疑いが狙いを定められて——語り手の利害・実績・同業者の評価に裏づけられて——初めて"),
                ("V","does","（倒置の助動詞）"),
                ("S","it","それは"),
                ("V","begin to do","し始める"),
                ("O","useful work.","有用な仕事を")],
     "note":"▶ <b>R23｜倒置</b>——限定の副詞 Only＋副詞節が文頭に出て <b>does it begin</b> と疑問文の語順に。informed by …＝挿入された過去分詞句。"},
    {"chunks": [("S","The choice before us","私たちの前にある選択は"),
                ("V","was never","決して〜ではなかった"),
                ("C","between thinking for ourselves and trusting others.","自分で考えることと他人を信頼することとの間の（選択）")],
     "note":"▶ between A and B＝動名詞の並列。「二者択一」そのものの否定——次文が本当の課題を言い直す。"},
    {"chunks": [("S","It","それは"),("V","is","である"),
                ("C","the harder, more adult task of doing both at once:","両方を同時に行うという、より難しく、より大人の課題"),
                ("-","doubting like a scientist rather than like someone &lt;determined in advance to believe nothing&gt;.","すなわち、初めから何も信じまいと決めてかかる者のようにではなく、科学者のように疑うこと")],
     "note":"▶ コロン(:)＝task の中身の言い換え。<b>R3｜A rather than B</b>＝Aの側（科学者のように疑う）が核心。determined … ＝過去分詞の後置修飾〔<b>R11</b>〕。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=5文/第2段=5文/第3段=4文/第4段=4文/第5段=5文/第6段=4文/第7段=5文)
SVOC_LOGIC = {
    (1, 3): "対比", (1, 5): "主張",                    # s3 疑う=勇気⇔受け入れる=怠惰 / s5 And yet→幻想(筆者の主張)
    (2, 1): "譲歩", (2, 2): "具体例", (2, 5): "譲歩",   # s1 It is true / s2 崩壊した理論の例 / s5 疑念は身から出た錆
    (3, 1): "対比", (3, 2): "具体例", (3, 3): "主張", (3, 4): "主張",
    (4, 1): "主張", (4, 2): "具体例", (4, 3): "主張", (4, 4): "主張",
    (5, 1): "譲歩", (5, 2): "対比", (5, 3): "主張", (5, 4): "具体例", (5, 5): "主張",
    (6, 1): "対比", (6, 2): "主張", (6, 3): "具体例", (6, 4): "主張",
    (7, 1): "譲歩", (7, 2): "対比", (7, 3): "主張", (7, 4): "主張", (7, 5): "主張",
}

# ------------------------------------------------------------------
# 設問別・根拠箇所 (該当箇所の提示)
#   本文のどこが根拠かを、原文の逐語引用＋訳＋判断で示す。
#   ★ en は必ず PASSAGE_PLAIN に実在する逐語引用にすること
#     (CLAUDE.md「解説が引用する英文は本文に実在させる」/ check_therules.py が全数照合する)。
#   mark: 選択肢の正誤 (○ / ×)。省略可 (記述問題など)。
# ------------------------------------------------------------------
EVIDENCE = [
    {"no": "問1", "ans": "A ＝ ① And yet　／　B ＝ ② Nonetheless", "items": [
        {"para": "¶1", "where": "空所【A】の直前",
         "en": "The truly independent thinker, we are told, verifies everything personally "
               "and bows to no authority.",
         "ja": "真に独立した思考の持ち主は、あらゆることを自分の手で検証し、いかなる権威にも屈しない——"
               "と私たちは聞かされる。",
         "why": "ここまでは<b>通念の紹介</b>（しかも we are told ＝「そう聞かされている」と距離を置いた言い方）。"
                "空所の前は<b>まだ筆者の主張ではない</b>。"},
        {"para": "¶1", "where": "空所【A】の直後（同じ文）",
         "en": "this flattering picture of the self-reliant mind, for all its appeal, rests on an illusion",
         "ja": "この自立した精神という心地よい像は、その魅力にもかかわらず、一つの幻想の上に成り立っている",
         "why": "直後で<b>その通念を否定</b>している（illusion＝幻想）。前＝通念、後＝否定 なので"
                "<b>逆接</b>しか入らない → ① And yet。②As a result（因果）・③For example（例示）・"
                "④Furthermore（追加）はいずれも「前を受けて同じ向きに進む」語で、反転を作れない。"},
        {"para": "¶2", "where": "空所【B】の直前（第2段全体の役割）",
         "en": "It is true that experts are fallible, and that the record of blind deference to them "
               "is not a happy one.",
         "ja": "確かに、専門家は誤りうるし、彼らへの盲目的な服従の記録が幸福なものでないことも本当である。",
         "why": "<b>It is true that …＝譲歩の合図</b>。第2段は丸ごと「相手の言い分を認める」段。"
                "譲歩の後には必ず<b>逆接で主張が戻ってくる</b>と身構える。"},
        {"para": "¶3", "where": "空所【B】の直後（同じ文）",
         "en": "the ideal of checking everything for oneself dissolves the moment it is examined",
         "ja": "すべてを自分で確かめるという理想は、検討されたその瞬間に溶けて消える",
         "why": "譲歩（専門家も誤る）を受けて<b>「それでも自力検証の理想は崩れる」と主張へ転換</b>している。"
                "→ 逆接 ② Nonetheless。①Therefore（因果）だと「専門家は誤る→だから自力検証は崩れる」となり"
                "意味が通らない。③For instance（例示）・④Likewise（類比）も反転を作れない。"},
    ]},
    {"no": "問2", "ans": "下線部(1) の和訳", "items": [
        {"para": "¶3", "where": "下線部(1) そのもの",
         "en": "It is not that independent verification is a noble goal we sadly fail to reach, "
               "but that, for creatures whose knowledge is stitched together from the testimony of others, "
               "complete intellectual self-reliance was never a possibility in the first place.",
         "ja": "独力の検証とは、私たちが残念ながら到達できずにいる崇高な目標だ、ということではない。そうではなく、"
               "その知識が他人の証言からつなぎ合わされてできている生き物にとって、完全な知的自立というものは、"
               "そもそも初めから可能ですらなかった、ということなのだ。",
         "why": "<b>It is not that A but that B</b> の骨格をまず取る。not が否定するのは"
                "<b>that 節A の内容全体</b>（＝「届かない崇高な目標だ」という<b>捉え方</b>そのもの）。"},
        {"para": "¶3", "where": "直前2文（A の内容を確定させる文脈）",
         "en": "she reads documents written by strangers, posted on platforms built by other strangers, "
               "summarizing measurements she will never witness",
         "ja": "彼女は、見知らぬ他人が書き、別の見知らぬ他人が作った基盤に載せられ、自分では決して目にする"
               "ことのない測定を要約した文書を読むのである",
         "why": "「自分で調べる」の実態＝<b>他人への信頼の連鎖</b>。だから下線部は「努力不足で届かない」"
                "のではなく<b>「最初から不可能」</b>だと言っている、と確認できる。"},
        {"para": "¶3", "where": "直前1文（creatures の中身）",
         "en": "Every step of her inquiry borrows the labor, and the honesty, of people she has never met.",
         "ja": "彼女の調査の一歩一歩が、会ったこともない人々の労働と誠実さとを借りている。",
         "why": "creatures whose knowledge is stitched together from the testimony of others ＝"
                "この文の言い換え。<b>creatures は「人間」</b>を指すと確定できる。"},
    ]},
    {"no": "問3", "ans": "下線部(2) の説明", "items": [
        {"para": "¶5", "where": "下線部(2) そのもの",
         "en": "Trust, practiced well, carries its own instruments of testing.",
         "ja": "正しく実践されるなら、信頼はそれ自身の検査の道具を備えている。",
         "why": "設問の核。<b>「道具」の中身は直後に列挙される</b>ので、次の文が答えの本体になる。"},
        {"para": "¶5", "where": "道具①〜③（whether 節の並列）",
         "en": "We can ask whether a speaker stands to profit from being believed; whether she has admitted "
               "and corrected her past errors, or quietly buried them; and whether those best placed to catch "
               "her mistakes, rivals within her own field, have largely come to agree with her.",
         "ja": "私たちは問うことができる——語り手は信じてもらうことで利益を得る立場にないか。過去の誤りを認めて"
               "訂正してきたか、それともひそかに葬ってきたか。そして、その誤りを見つけるのに最も適した人々——"
               "同じ分野のライバルたち——が、おおむねその人に同意するに至っているか。",
         "why": "<b>①語り手の利害 ②訂正の履歴 ③同分野のライバルの合意</b>——この3つが「検査の道具」の中身。"
                "記述はここから<b>2つ以上</b>を必ず入れる。"},
        {"para": "¶5", "where": "道具の性格（何を要求しないか）",
         "en": "None of these checks requires us to repeat the science ourselves; they demand something "
               "humbler and more attainable, attention to how a claim has survived the scrutiny of others.",
         "ja": "これらの検査のどれ一つとして、科学を自分で繰り返すことを私たちに求めはしない。それらが求めるのは、"
               "もっと謙虚で、もっと手の届くもの——ある主張が他人の吟味をどのように生き延びてきたのかへの注意である。",
         "why": "「自分で実験し直す必要はない」＝<b>盲信でもなければ独力検証でもない第三の道</b>。"
                "ここを落とすと「信頼＝結局は自分で確かめること」という誤読の答案になる。"},
    ]},
    {"no": "問4", "ans": "②", "items": [
        {"para": "¶4", "where": "根拠の中心（②の直接の言い換え）",
         "en": "Never in this long division of labor has reliance on others been a sign of idleness; "
               "it is the very mechanism by which a community comes to know more than any of its members.",
         "ja": "この長い分業の歴史の中で、他人に頼ることが怠惰のしるしであったことは一度もない。それは、共同体が"
               "その成員の誰よりも多くを知るに至る、まさにその仕組みなのである。",
         "why": "②「怠慢のしるしではなく／共同体が個々の成員の限界を超えて知るための仕組みそのもの」と"
                "<b>前半・後半とも一対一で対応</b>する。○"},
        {"para": "¶4", "where": "④を切る根拠",
         "en": "Modern knowledge has grown far beyond the capacity of any single head",
         "ja": "現代の知識は、どの一人の頭の容量をもはるかに超えて成長した",
         "why": "④「努力しだいで一人で抱えきれる」は<b>正反対</b>。分業は「効率のための選択」ではなく"
                "<b>不可避の条件</b>として書かれている。×"},
        {"para": "¶4", "where": "③を切る根拠",
         "en": "the chemist trusts the physicist, the doctor trusts the medical journal",
         "ja": "化学者は物理学者を信頼し、医師は医学誌を信頼する",
         "why": "③「専門家たちは互いをまったく信頼していない」は本文と逆。本文は"
                "<b>専門家同士の信頼を前提</b>にしている（ライバルの相互チェックは第5段の別の話）。×"},
        {"para": "¶4", "where": "①を切る根拠（段の結論）",
         "en": "To trust well, on this view, is not to stop thinking but to think with other people.",
         "ja": "上手に信頼するとは、この見方に立てば、考えるのをやめることではなく、他人とともに考えることなのだ。",
         "why": "①「思考力を確実に衰えさせる／個人の検証に置き換えるべき」は、この文の"
                "<b>not to stop thinking</b> に真っ向から反する。×"},
    ]},
    {"no": "問5", "ans": "下線部(3) の説明", "items": [
        {"para": "¶6", "where": "下線部(3) を含む文（コロンが定義を与える）",
         "en": "What we need is not a verdict on experts but a craft of trust: the discipline of judging "
               "whom to believe, about which questions, and on what grounds.",
         "ja": "私たちに必要なのは、専門家への判定ではなく、信頼の技術——誰を信じるか、どの問題について、"
               "どんな根拠で、を判断する鍛錬——なのだ。",
         "why": "<b>コロン(:)の後ろが a craft of trust の定義</b>。記述の骨は"
                "「<b>誰を・何について・どんな根拠で</b>」の3点セットで作る。"},
        {"para": "¶6", "where": "「領域ごと」の具体例",
         "en": "A physicist deserves our confidence about particles, not necessarily about politics",
         "ja": "物理学者は素粒子については私たちの信頼に値するが、必ずしも政治についてではない",
         "why": "「専門家一般への一括の判定」が成り立たない理由。<b>信頼は人単位ではなく"
                "〈人×領域〉単位で与える</b>——これが verdict（一括評決）との対比。"},
        {"para": "¶6", "where": "結論部（技術であることの意味）",
         "en": "Framed this way, trust ceases to be a lapse of intelligence and becomes one of its most "
               "demanding exercises.",
         "ja": "このように問いを立て直せば、信頼は知性の放棄であることをやめ、その最も骨の折れる行使の一つとなる。",
         "why": "「技術（craft）」の含意＝<b>信頼は知性の放棄ではなく行使</b>。記述の締めに必ず入れる。"},
        {"para": "¶6", "where": "「判定」が否定される理由（段の入口）",
         "en": "The real question, therefore, is poorly framed as a choice between trusting and doubting.",
         "ja": "したがって本当の問いは、「信頼するか、疑うか」という二者択一として立てるのではまずい。",
         "why": "a verdict on experts ＝「信じるか疑うかを専門家という集団にまとめて下す判決」。"
                "<b>その問いの立て方自体が誤り</b>だという指摘が、not A の側の中身。"},
    ]},
    {"no": "問6", "ans": "③", "items": [
        {"para": "¶6", "where": "③の根拠（前半）",
         "en": "What we need is not a verdict on experts but a craft of trust: the discipline of judging "
               "whom to believe, about which questions, and on what grounds.",
         "ja": "私たちに必要なのは、専門家への判定ではなく、信頼の技術——誰を信じるか、どの問題について、"
               "どんな根拠で、を判断する鍛錬——なのだ。",
         "why": "③「誰を・何について・どんな根拠で信頼するかという技術」と一致。○"},
        {"para": "¶6", "where": "③の根拠（後半＝「知性の行使」）",
         "en": "trust ceases to be a lapse of intelligence and becomes one of its most demanding exercises",
         "ja": "信頼は知性の放棄であることをやめ、その最も骨の折れる行使の一つとなる",
         "why": "③の末尾「それは知性の行使である」に対応。<b>選択肢の全要素が本文で裏づく</b>のは③だけ。○"},
        {"para": "¶1・¶3", "where": "①を切る根拠",
         "en": "this flattering picture of the self-reliant mind, for all its appeal, rests on an illusion",
         "ja": "この自立した精神という心地よい像は、その魅力にもかかわらず、一つの幻想の上に成り立っている",
         "why": "①「疑ってかかることこそ知的に誠実な<b>唯一の</b>態度」は第1段の<b>通念</b>そのもので、"
                "筆者はそれを illusion と呼んで否定した側。×（「唯一」は言い過ぎの印）"},
        {"para": "¶7", "where": "②を切る根拠",
         "en": "None of this asks us to abandon doubt; a healthy intellectual culture needs skeptics as a "
               "body needs an immune system.",
         "ja": "以上のどれも、疑うことを捨てよと求めるものではない。健全な知的文化が懐疑派を必要とするのは、"
               "身体が免疫系を必要とするのと同じである。",
         "why": "②「疑うこと自体を手放し、判断をすべて専門家に委ねるほかない」は<b>この文の正面からの否定</b>。×"},
        {"para": "¶5", "where": "④を切る根拠",
         "en": "We can ask whether a speaker stands to profit from being believed",
         "ja": "私たちは、語り手が信じてもらうことで利益を得る立場にないかを問うことができる",
         "why": "④「個人が語り手の利害や訂正の履歴をいちいち確かめる必要はまったくない」は、"
                "筆者が<b>まさに求めていること</b>の否定。×"},
    ]},
    {"no": "問7", "ans": "②・⑤・⑥", "items": [
        {"para": "¶2", "where": "選択肢①", "mark": "×",
         "en": "Specialists have defended theories that later collapsed",
         "ja": "専門家たちは、後に崩れ去る理論を擁護してきた",
         "why": "同段 Whole fields have had to withdraw claims once announced with confidence "
                "（分野全体が主張を撤回せねばならなかった）もある。①「一度もない」は"
                "<b>正反対＋全否定の言い過ぎ</b>。×"},
        {"para": "¶3", "where": "選択肢②", "mark": "○",
         "en": "she reads documents written by strangers, posted on platforms built by other strangers, "
               "summarizing measurements she will never witness",
         "ja": "彼女は、見知らぬ他人が書き、別の見知らぬ他人が作った基盤に載せられ、自分では決して目にする"
               "ことのない測定を要約した文書を読むのである",
         "why": "②「見知らぬ他人が作った文書や測定の要約に頼って調査している」と一対一で対応。○"},
        {"para": "¶5", "where": "選択肢③", "mark": "×",
         "en": "We can ask whether a speaker stands to profit from being believed",
         "ja": "私たちは、語り手が信じてもらうことで利益を得る立場にないかを問うことができる",
         "why": "③「信頼の判断とは無関係だと筆者は述べている」は逆。<b>無関係どころか第一の判断材料</b>。×"},
        {"para": "¶7", "where": "選択肢④", "mark": "×",
         "en": "But doubt spread evenly over everything protects nothing; it merely exhausts us.",
         "ja": "だが、あらゆるものの上に等しくばらまかれた疑いは、何も守らない——ただ私たちを疲れさせるだけだ。",
         "why": "④「等しく疑い続けることが最もよく守る」は<b>protects nothing の正反対</b>。"
                "「疑いは狙いを定めて初めて働く」が筆者の立場。×"},
        {"para": "¶6", "where": "選択肢⑤", "mark": "○",
         "en": "A physicist deserves our confidence about particles, not necessarily about politics",
         "ja": "物理学者は素粒子については私たちの信頼に値するが、必ずしも政治についてではない",
         "why": "⑤「素粒子については信頼に値するとしても、政治についても同様とは限らない」＝"
                "<b>not necessarily（部分否定）</b>の正確な訳。○"},
        {"para": "¶7", "where": "選択肢⑥", "mark": "○",
         "en": "Only when suspicion is aimed, informed by a speaker's interests, record, and peers, "
               "does it begin to do useful work.",
         "ja": "疑いが狙いを定められて——語り手の利害、実績、同業者の評価に裏づけられて——初めて、"
               "それは有用な仕事をし始める。",
         "why": "同段 None of this asks us to abandon doubt と合わせて、⑥「疑うことをやめよと説くのではなく、"
                "疑いを有効に働かせるために狙いの定まった判断を説く」と一致。○"},
    ]},
]

# ------------------------------------------------------------------
# 文法的視点からのアプローチ
#   GRAMMAR_STEPS = 1文を崩す手順 / GRAMMAR = 本文で実際に問われた文法の型
#   ★ ex の en も PASSAGE_PLAIN 実在の逐語引用 (check_therules.py が照合)
# ------------------------------------------------------------------
GRAMMAR_STEPS = [
    ("STEP 1", "主節の S と V を先に取る",
     "コンマやダッシュで挟まれた部分（挿入）、関係詞・分詞のカタマリを<b>いったん括弧に入れて外す</b>。"
     "残った骨が主節。例：Trust <span class='ins'>(, practiced well,)</span> carries its own instruments "
     "of testing. → S=Trust / V=carries。"),
    ("STEP 2", "否定語を探し、<b>射程</b>（どこまで否定するか）を決める",
     "not / never / no / nothing / hardly / none。<b>否定は「直後の語」ではなく「そのカタマリ全体」に"
     "かかることがある</b>。not A but B なら not の範囲は A の全体。ここを外すと和訳が反対の意味になる。"),
    ("STEP 3", "等位・対比の軸（not A but B / rather than / A, not B）を見つける",
     "英語の主張は<b>「Aではなく B」の形</b>で置かれることが多い。<b>B の側が筆者の主張</b>。"
     "設問の記述解答は、この B をそのまま骨にすると外さない。"),
    ("STEP 4", "コロン(:)・セミコロン(;)・ダッシュ(—)を「＝」として読む",
     "コロンとダッシュの後ろは<b>直前の抽象語の言い換え・具体化</b>。"
     "抽象的な語（a craft of trust など）の意味は、<b>必ず近くに言い換えが置かれている</b>。"),
    ("STEP 5", "文頭の倒置・譲歩の合図に反応する",
     "Never / Only + 副詞句が文頭 → 疑問文の語順（強調）。It is true that … / Of course … → 譲歩なので"
     "<b>直後の逆接で主張が来る</b>と身構える。"),
]

GRAMMAR = [
    {"id": "G1", "title": "否定の射程 — It is not that A but that B", "star": "★★★", "use": "問2（和訳）",
     "point": "「A ということではなく、B ということだ」。<b>not が否定するのは that 節A の内容全体</b>で、"
              "A の中の一語（noble）ではない。<b>訳し出す順序</b>：①「〜ということではない」→"
              "②「そうではなく、〜ということだ」と2文に割ると、日本語が壊れない。",
     "ex": [("It is not that independent verification is a noble goal we sadly fail to reach, but that, "
             "for creatures whose knowledge is stitched together from the testimony of others, complete "
             "intellectual self-reliance was never a possibility in the first place.",
             "独力の検証とは、私たちが残念ながら到達できずにいる崇高な目標だ、ということではない。そうではなく、"
             "その知識が他人の証言からつなぎ合わされてできている生き物にとって、完全な知的自立というものは、"
             "そもそも初めから可能ですらなかった、ということなのだ。")],
     "how": "but that の <b>that は It is not that の that と対</b>。まず but that を探し、"
            "A と B を切り分けてから中身を訳す。B の中の for creatures … others は<b>挿入の副詞句</b>なので"
            "先に外し、骨（complete intellectual self-reliance was never a possibility）を取る。",
     "trap": "×「独力の検証は崇高な目標ではない」——これは not の射程を noble だけに縮めた誤訳。"
             "筆者は「崇高さ」を否定していない。否定しているのは<b>「努力が足りず届かないだけだ」という捉え方</b>。"},
    {"id": "G2", "title": "倒置 — 否定・限定の副詞が文頭に出ると疑問文の語順", "star": "★★★", "use": "問4・問7④",
     "point": "Never / Only / Little / Not until … が文頭に出ると、<b>助動詞（be / have / do）が主語の前</b>に"
              "出る。意味は「強調」で、<b>否定文・限定文であることは変わらない</b>。読むときは"
              "<b>語順を元に戻す</b>のが最短。",
     "ex": [("Never in this long division of labor has reliance on others been a sign of idleness",
             "この長い分業の歴史の中で、他人に頼ることが怠惰のしるしであったことは一度もない"),
            ("Only when suspicion is aimed, informed by a speaker's interests, record, and peers, "
             "does it begin to do useful work.",
             "疑いが狙いを定められて、語り手の利害・実績・同業者の評価に裏づけられて初めて、"
             "それは有用な仕事をし始める。")],
     "how": "① Never … has reliance been ～ → 戻すと <b>reliance has never been ～</b>（他人への依存は"
            "怠惰だったことなど一度もない）。② Only when SV does it begin ～ → 戻すと"
            "<b>it begins to do useful work only when SV</b>（〜のときに<b>限って</b>働き始める）。",
     "trap": "Only when … の文を「疑いはいつでも役に立つ」と読むと問7④に引っかかる。"
             "<b>only は「それ以外のときは働かない」という限定</b>で、事実上の否定を含む。"},
    {"id": "G3", "title": "not A but B / rather than — 主張は必ず B 側", "star": "★★★", "use": "問4・問5・問6",
     "point": "英語の論説は「Aではなく B」の型で主張を置く。<b>設問が「どういうことか」と問うのは"
              "ほぼ B の中身</b>。A（否定される側）は<b>世間の通念</b>であることが多い。",
     "ex": [("To trust well, on this view, is not to stop thinking but to think with other people.",
             "上手に信頼するとは、この見方に立てば、考えるのをやめることではなく、他人とともに考えることなのだ。"),
            ("What we need is not a verdict on experts but a craft of trust",
             "私たちに必要なのは、専門家への判定ではなく、信頼の技術である"),
            ("doubting like a scientist rather than like someone determined in advance to believe nothing",
             "初めから何も信じまいと決めてかかる者のようにではなく、科学者のように疑うということ")],
     "how": "A と B は<b>文法的に同じ形</b>で並ぶ（to do ↔ to do、名詞 ↔ 名詞、like ～ ↔ like ～）。"
            "<b>形が揃うところ</b>を目印に切れ目を見つけると、長くても迷わない。",
     "trap": "rather than は<b>前が主張</b>（A rather than B ＝ B ではなく A）。not A but B と"
             "<b>語順が逆</b>なので、機械的に「後ろが主張」と覚えていると第7段末で逆に取る。"},
    {"id": "G4", "title": "後置修飾のカタマリ — 関係詞の省略・分詞の連続", "star": "★★★", "use": "問2・問7②",
     "point": "名詞の後ろに<b>いきなり SV</b>が来たら関係代名詞の省略。名詞の後ろに<b>過去分詞・現在分詞</b>が"
              "来たらそこから修飾のカタマリ。<b>カタマリの終わりを見つけて括弧でくくる</b>のが読解の要。",
     "ex": [("she reads documents written by strangers, posted on platforms built by other strangers, "
             "summarizing measurements she will never witness",
             "彼女は、見知らぬ他人によって書かれ、別の見知らぬ他人が作った基盤に載せられ、"
             "自分では決して目にすることのない測定を要約している文書を読む"),
            ("Every step of her inquiry borrows the labor, and the honesty, of people she has never met.",
             "彼女の調査の一歩一歩が、会ったこともない人々の労働と誠実さとを借りている。")],
     "how": "documents ＜written …／posted …／summarizing …＞ と<b>3つの分詞句が並列で1つの名詞</b>を"
            "説明している。並列だと気づけば「誰が書いたか分からない文書を読んでいるだけ」という趣旨が一発で出る。"
            "people ＜(whom) she has never met＞ も関係詞の省略。",
     "trap": "posted / summarizing を<b>文の述語動詞と誤認</b>して「彼女は投稿し、要約する」と読むと、"
             "主語がすり替わって意味が反転する。述語は<b>reads 一つだけ</b>。"},
    {"id": "G5", "title": "挿入（コンマ・ダッシュに挟まれた部分）を外して骨を見る", "star": "★★", "use": "問1・問3",
     "point": "コンマやダッシュで挟まれた語句は<b>主語と動詞の間に割り込む</b>ことが多い。"
              "<b>外しても文が成立する</b>のが挿入の見分け方。",
     "ex": [("The truly independent thinker, we are told, verifies everything personally and bows to no authority.",
             "真に独立した思考の持ち主は——と私たちは聞かされるのだが——あらゆることを自分の手で検証し、"
             "いかなる権威にも屈しない。"),
            ("Trust, practiced well, carries its own instruments of testing.",
             "信頼は、正しく実践されるなら、それ自身の検査の道具を備えている。")],
     "how": "① we are told を外すと The truly independent thinker verifies … と骨が出る。"
            "しかもこの挿入は<b>「筆者自身の意見ではない」という距離の合図</b>で、問1【A】の逆接につながる。"
            "② practiced well ＝ if it is practiced well の分詞構文（条件）。"
            "<b>「正しく実践されれば」という条件つき</b>である点が問3の答案で効く。",
     "trap": "practiced を過去形の述語と読むと「信頼はよく実践した」となり主語と動詞が二重になる。"
             "<b>述語は carries</b>。"},
    {"id": "G6", "title": "コロン(:)・ダッシュ(—)は「＝」— 抽象語の意味はすぐ隣にある", "star": "★★★", "use": "問3・問5",
     "point": "抽象的な語句が出たら、<b>直後のコロン・ダッシュ・同格</b>を探す。"
              "<b>記述問題の解答は、この言い換えをそのまま骨にする</b>のが最も安全。",
     "ex": [("What we need is not a verdict on experts but a craft of trust: the discipline of judging "
             "whom to believe, about which questions, and on what grounds.",
             "私たちに必要なのは、専門家への判定ではなく、信頼の技術——誰を信じるか、どの問題について、"
             "どんな根拠で、を判断する鍛錬——なのだ。"),
            ("they demand something humbler and more attainable, attention to how a claim has survived "
             "the scrutiny of others",
             "それらが求めるのは、もっと謙虚で、もっと手の届くもの——ある主張が他人の吟味をどのように"
             "生き延びてきたのかへの注意——である")],
     "how": "a craft of trust という抽象語の中身は<b>コロンの後ろが全て</b>。"
            "whom to believe / about which questions / on what grounds ＝"
            "<b>疑問詞＋to不定詞・疑問詞句の3並列</b>で「誰を・何について・どんな根拠で」。"
            "問5はこの3点を落とさなければ核が立つ。",
     "trap": "something humbler and more attainable のような <b>-thing＋形容詞は後置</b>。"
             "「もっと謙虚な何か」と正しく取れないと、後ろの同格（attention to …）と結びつかない。"},
    {"id": "G7", "title": "譲歩の合図と部分否定 — 「言い過ぎ」を作らない読み", "star": "★★★", "use": "問1・問6・問7",
     "point": "It is true that … ＝<b>譲歩</b>（後で必ず反転）。not necessarily / not always ＝<b>部分否定</b>"
              "「必ずしも〜とは限らない」。<b>全否定と部分否定の区別</b>が内容一致の合否を分ける。",
     "ex": [("It is true that experts are fallible, and that the record of blind deference to them is not a happy one.",
             "確かに、専門家は誤りうるし、彼らへの盲目的な服従の記録が幸福なものでないことも本当である。"),
            ("A physicist deserves our confidence about particles, not necessarily about politics",
             "物理学者は素粒子については信頼に値するが、必ずしも政治についてではない"),
            ("None of this asks us to abandon doubt", "以上のどれも、疑うことを捨てよと求めるものではない")],
     "how": "It is true that … を見たら<b>「ここは筆者の最終主張ではない」と印をつけて先へ進む</b>。"
            "第2段まるごとが譲歩、第3段冒頭の Nonetheless で反転——この設計が問1【B】。"
            "not necessarily は<b>「政治については信頼できない」と断定していない</b>点が問7⑤の正誤の分かれ目。",
     "trap": "選択肢の「一度もない」「唯一の」「まったく必要ない」「すべて委ねる」は"
             "<b>言い過ぎの典型</b>。本文が部分否定・譲歩で書いている箇所を、選択肢が全否定に強めていないか"
             "を必ず確かめる（問7①③④はすべてこの型）。"},
    {"id": "G8", "title": "否定語の位置と準否定語 — 目的語や主語に入り込む否定", "star": "★★", "use": "問4・問7④",
     "point": "英語は<b>否定語を目的語や主語の中に入れる</b>ことができる（no / nothing / none / hardly）。"
              "日本語は文末で否定するので、<b>訳すときは文末に回す</b>。",
     "ex": [("bows to no authority", "いかなる権威にも屈しない"),
            ("But doubt spread evenly over everything protects nothing", "だが、あらゆるものの上に等しくばらまかれた疑いは、何も守らない"),
            ("None of these checks requires us to repeat the science ourselves",
             "これらの検査のどれ一つとして、科学を自分で繰り返すことを私たちに求めはしない")],
     "how": "protects nothing は<b>肯定文の形をした否定文</b>。"
            "「疑いが（何かを）守る」と読み違えると問7④で逆を選ぶ。"
            "Hardly.（第5段）は<b>一語の準否定</b>で「まさか、そんなことはない」＝直前の自問への強い否定。",
     "trap": "doubt spread evenly over everything の spread は<b>過去分詞</b>（spread–spread–spread）で"
             "doubt を後置修飾。述語は protects。ここを「疑いが広がる」と動詞に取ると主節の動詞が消える。"},
    {"id": "G9", "title": "what 節と無生物主語 — 抽象名詞句が主語に立つ", "star": "★★", "use": "問4・問6",
     "point": "<b>関係代名詞 what ＝「〜すること／もの」</b>で名詞のカタマリを作り、そのまま主語になる。"
              "無生物主語は<b>「〜は」と訳さず、副詞的に訳す</b>と日本語が自然になることが多い。",
     "ex": [("What looks like a private achievement, then, is in fact a social arrangement.",
             "個人の達成のように見えるものは、とすると、実のところ社会的な仕組みである。"),
            ("What we need is not a verdict on experts but a craft of trust",
             "私たちに必要なのは、専門家への判定ではなく、信頼の技術である")],
     "how": "What … の切れ目は<b>2つ目の動詞</b>で決まる。① What looks like a private achievement ｜ is …、"
            "② What we need ｜ is … 。<b>「What節 is …」は定義・言い換えの型</b>なので、"
            "筆者の主張がここに置かれやすい（実際 ②が第6段の核心＝問6の根拠）。",
     "trap": "What looks like A is B を「Aのように見えるものはBのように見える」と重ねて訳さない。"
             "<b>looks like は what 節の中の動詞</b>、主節の動詞は is。"},
]
