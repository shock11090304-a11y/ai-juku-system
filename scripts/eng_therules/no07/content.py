# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.07 — 単一ソース
テーマ: Every Map Is an Argument (どんな地図も一つの主張である)
／ MARCH レベル（The Rules 3 相当）
問題編 + 解説編 を build.py が生成。

★ この content.py が**唯一の正典**。問題編・解説編・全訳・SVOC は同じデータから作る。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_therules.py が引用の全数照合・配点合計・
  設問と解答の対応・SVOC_LOGIC の範囲を検査 ② 生成 PDF の逆照合 ③ 正解の一意性を敵対的に再読。
★ 既存号とテーマが重ならないこと (no02 機械翻訳/no03 都市と自然/no04 睡眠/no05 歴史/
  no06 多様性、content_no01 退屈 …)。足すときは必ず全号の theme_ja を確認してから書く。
"""

META = {
    "series": "The Rules 式",
    "no": "07",
    "level": "MARCH レベル",
    "level_sub": "偏差値60〜65 / The Rules 3 相当",
    "theme_ja": "どんな地図も一つの主張である",
    "theme_en": "Every Map Is an Argument",
    "minutes": 20,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    (1, 'Of all the documents we consult, few seem less controversial than a map. A map, we '
        'assume, simply shows us what is there: coastlines, borders, rivers, and roads, '
        'recorded as faithfully as instruments allow. Disagreements may arise about history or '
        'politics, but surely geography is settled. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, the moment we ask how a round earth is '
        'placed on a flat page, this comfortable assumption begins to dissolve.'),
    (2, 'It is true that mapmakers are not free to invent. A cartographer who moved a city a '
        'hundred kilometres for the sake of a pleasing design would be guilty of an error, not '
        'of art, and no survey would confirm the result. Measurement disciplines the map at '
        'every stage, and this is why maps remain among the most useful documents we possess.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span> discipline is not the same as neutrality. '
        'A sphere cannot be flattened without damage, and every projection must therefore '
        'decide which kind of damage it will accept. <u>The familiar classroom map preserves '
        'direction faithfully, and pays for that fidelity by inflating the lands near the '
        'poles.<sup>(1)</sup></u> Other projections keep areas honest and let shapes suffer '
        'instead. No projection escapes the choice; there is only the question of which loss is '
        'thought acceptable, and by whom.'),
    (4, 'Selection works in the same direction. A map that showed everything would be useless, '
        'and so the mapmaker must decide what deserves a line and what does not. A railway '
        'appears; a footpath vanishes. One settlement is named in bold, another in a type so '
        'small that the eye passes over it. <u>These choices are rarely announced, and that '
        'silence is what makes them powerful.<sup>(2)</sup></u> The reader receives a set of '
        'judgements as though receiving a photograph.'),
    (5, 'History supplies the sharper cases. Colonial maps drew confident lines across regions '
        'their authors had never walked, and those lines later hardened into borders that '
        'shaped the lives of millions. Territories in dispute are still shown differently '
        'depending on where an atlas is printed. Even the position of the centre carries a '
        'message: a world map places some ocean, and some continent, at its heart, and quietly '
        'assigns everything else to a margin.'),
    (6, 'To notice this is not to conclude that maps deceive us, nor that one map is as good as '
        'another. <u>A map is not a photograph of the world but an argument about it, and '
        'arguments can be made well or badly.<sup>(3)</sup></u> The projection that suits a '
        'navigator misleads a student of population; a map that hides a footpath may be exactly '
        'what a driver needs. What a map should be judged by is not whether it selects, since '
        'all of them do, but whether its selections serve the purpose for which it is used.'),
    (7, 'The practical lesson is a habit of reading rather than a suspicion of maps. Before '
        'accepting the picture, it is worth asking what the map was made for, what it leaves '
        'out, and whose interests its choices happen to serve. Such questions do not make the '
        'coastlines dissolve. They simply return the map to the human hands that drew it.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める・下線/タグは除去)
PASSAGE_PLAIN = (
    "Of all the documents we consult, few seem less controversial than a map. A map, we assume, "
    "simply shows us what is there: coastlines, borders, rivers, and roads, recorded as "
    "faithfully as instruments allow. Disagreements may arise about history or politics, but "
    "surely geography is settled. Yet, the moment we ask how a round earth is placed on a flat "
    "page, this comfortable assumption begins to dissolve. "
    "It is true that mapmakers are not free to invent. A cartographer who moved a city a "
    "hundred kilometres for the sake of a pleasing design would be guilty of an error, not of "
    "art, and no survey would confirm the result. Measurement disciplines the map at every "
    "stage, and this is why maps remain among the most useful documents we possess. "
    "But discipline is not the same as neutrality. A sphere cannot be flattened without damage, "
    "and every projection must therefore decide which kind of damage it will accept. The "
    "familiar classroom map preserves direction faithfully, and pays for that fidelity by "
    "inflating the lands near the poles. Other projections keep areas honest and let shapes "
    "suffer instead. No projection escapes the choice; there is only the question of which loss "
    "is thought acceptable, and by whom. "
    "Selection works in the same direction. A map that showed everything would be useless, and "
    "so the mapmaker must decide what deserves a line and what does not. A railway appears; a "
    "footpath vanishes. One settlement is named in bold, another in a type so small that the "
    "eye passes over it. These choices are rarely announced, and that silence is what makes "
    "them powerful. The reader receives a set of judgements as though receiving a photograph. "
    "History supplies the sharper cases. Colonial maps drew confident lines across regions "
    "their authors had never walked, and those lines later hardened into borders that shaped "
    "the lives of millions. Territories in dispute are still shown differently depending on "
    "where an atlas is printed. Even the position of the centre carries a message: a world map "
    "places some ocean, and some continent, at its heart, and quietly assigns everything else "
    "to a margin. "
    "To notice this is not to conclude that maps deceive us, nor that one map is as good as "
    "another. A map is not a photograph of the world but an argument about it, and arguments "
    "can be made well or badly. The projection that suits a navigator misleads a student of "
    "population; a map that hides a footpath may be exactly what a driver needs. What a map "
    "should be judged by is not whether it selects, since all of them do, but whether its "
    "selections serve the purpose for which it is used. "
    "The practical lesson is a habit of reading rather than a suspicion of maps. Before "
    "accepting the picture, it is worth asking what the map was made for, what it leaves out, "
    "and whose interests its choices happen to serve. Such questions do not make the coastlines "
    "dissolve. They simply return the map to the human hands that drew it."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Yet &nbsp; ② Therefore &nbsp; ③ For example &nbsp; ④ Likewise",
         "【 B 】 &nbsp; ① Similarly &nbsp; ② But &nbsp; ③ Hence &nbsp; ④ For instance",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(3) <span class='en'>A map is not a photograph of the world but an argument "
             "about it, and arguments can be made well or badly.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) <span class='en'>The familiar classroom map preserves direction "
             "faithfully, and pays for that fidelity by inflating the lands near the poles.</span> "
             "について、地図が「代償を払う（<span class='en'>pays for that fidelity</span>）」とは"
             "どういうことか。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "第2段で筆者が述べていることとして最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 地図製作者は美しい構図のためであれば都市の位置を移してもよいとされている。",
         "② 測量が各段階で地図を律しており、それゆえ地図は最も有用な文書の一つであり続けている。",
         "③ 測量には限界があるため、地図の有用性は歴史や政治の文書より低いと考えられている。",
         "④ 地図製作者は自由に発明してよく、その自由こそが地図を芸術に近づけている。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(2) <span class='en'>These choices are rarely announced, and that silence is "
             "what makes them powerful.</span> について、（ア）ここでいう「選択」とは具体的に"
             "どのようなものか、（イ）なぜその「沈黙」が選択を強力にするのか、を本文全体をふまえて"
             "日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 地図はどれも作り手の利害を反映した虚構であり、読者は地図を信頼すべきではない。",
         "② 地図はすべて選択を含むという点で等価であり、優劣を論じることには意味がない。",
         "③ 地図は選択を含む主張であり、その選択が用途に適っているかによって評価されるべきだ。",
         "④ 投影法の歪みは技術の進歩によって解消されつつあるので、選択の問題は重要性を失った。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 球面は損なわれることなく平面にできないため、どの投影法もどの種類の歪みを受け入れるかを"
         "決めなければならない。",
         "② すべてを示す地図は役に立たないので、地図製作者は何に線を与えるかを決めなければならない。",
         "③ 係争中の領域は、地図帳がどこで印刷されるかにかかわらず、同じように描かれている。",
         "④ 植民地時代の地図が引いた線が、のちに国境として固まり、多くの人々の生活を形づくった。",
         "⑤ 航海者に適した投影法は、人口を研究する者にとっても同じように適している。",
         "⑥ 世界地図の中心にどの海や大陸を置くかは単なる慣習であり、何のメッセージも担わない。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ① Yet　　B ＝ ② But",
     "exp": "A：「地図は議論の余地がない・地理は決着済み」という通念に対し、「丸い地球を平らな紙に"
            "置く方法を問うた瞬間、その心地よい前提は溶け始める」と<b>反転</b>する。逆接 → Yet。"
            "Therefore（因果）・For example（例示）・Likewise（同様に）は不可。<br>"
            "B：第2段「確かに地図製作者は勝手に発明できない——測量が地図を律する（＝譲歩）」に対し、"
            "第3段は「<b>だが律せられていることと中立であることは同じではない</b>」と主張へ転換する。"
            "逆接 → But。Similarly（類比）・Hence（因果）・For instance（例示）は流れに合わない。 "
            "〔<b>解法ルール R7</b>／<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "②",
     "exp": "第2段末「<span class='en'>Measurement disciplines the map at every stage, and this "
            "is why maps remain among the most useful documents we possess</span>」と一致。"
            "①④×：同段は逆に「<span class='en'>mapmakers are not free to invent</span>」とし、"
            "都市を動かす製作者は「<span class='en'>guilty of an error, not of art</span>」"
            "（芸術ではなく誤りの罪）だと述べる。③×：本文は地図を最も有用な文書の一つとしている。 "
            "〔<b>読解ルール R2</b>：譲歩段の内容／<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "③",
     "exp": "第6段「<span class='en'>What a map should be judged by is not whether it selects, "
            "since all of them do, but whether its selections serve the purpose for which it is "
            "used</span>」と一致。①×：同段冒頭「<span class='en'>To notice this is not to "
            "conclude that maps deceive us</span>」に反する。②×：同じ文の"
            "「<span class='en'>nor that one map is as good as another</span>」（どの地図も"
            "同じように良いわけではない）に反する。④×：技術による歪みの解消は本文にない。 "
            "〔<b>読解ルール R3</b>：not A but B／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・②・④",
     "exp": "①〇：第3段「<span class='en'>A sphere cannot be flattened without damage</span>」＋"
            "「<span class='en'>every projection must therefore decide which kind of damage it "
            "will accept</span>」。②〇：第4段「<span class='en'>A map that showed everything "
            "would be useless</span>」＋「<span class='en'>the mapmaker must decide what deserves "
            "a line and what does not</span>」。④〇：第5段「<span class='en'>those lines later "
            "hardened into borders that shaped the lives of millions</span>」。<br>"
            "③×：第5段は逆——「<span class='en'>Territories in dispute are still shown differently "
            "depending on where an atlas is printed</span>」（印刷地によって<b>異なって</b>描かれる）。"
            "⑤×：第6段「<span class='en'>The projection that suits a navigator misleads a student "
            "of population</span>」（航海者に適した投影法は人口研究者を<b>誤らせる</b>）に反する。"
            "⑥×：第5段「<span class='en'>Even the position of the centre carries a message</span>」"
            "＝中心の位置<b>さえもメッセージを担う</b>に真っ向から反する。 "
            "〔<b>解法ルール R9</b>：本文と逆の選択肢を切る〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(3)和訳",
     "model": "地図とは世界を写した写真ではなく、世界についての一つの主張であり、そして主張というものは"
              "うまく行うことも、まずく行うこともできるのである。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「AではなくB」の対比を構文どおり訳出"
               "〔<b>読解ルール R3</b>〕／②<b>an argument about it</b> の it＝the world を受けて"
               "「世界についての主張」と訳す〔<b>読解ルール R5</b>〕／③<b>arguments can be made "
               "well or badly</b>＝受動態を「うまく／まずく行われうる」と訳し、<b>優劣がある</b>ことを"
               "示す（「どの地図も同じ」ではない、という直前の否定と呼応する）。"},
    {"no": "問3", "pts": "8点・記述",
     "model": "球面である地球は損なわれずには平面にできないので、どの投影法も何らかの歪みを引き受け"
              "なければならない。教室でおなじみの地図は方位を忠実に保つという長所を選んだ結果、"
              "その代償として極に近い陸地の面積を実際より大きく膨らませてしまっている、ということ。",
     "points": "▶<b>採点要素</b>：①<b>前提</b>——球面は損傷なしに平面化できず、投影法は"
               "<b>どの歪みを受け入れるかを選ぶ</b>（第3段前半）／②<b>得たもの＝方位の忠実さ</b>／"
               "③<b>払った代償＝極付近の陸地が膨張する</b>（inflating the lands near the poles）。"
               "「pay for＝代償を払う」を〈長所と引き換えに別の正確さを失う〉と説明できていること。 "
               "〔<b>読解ルール R6</b>：因果／<b>解法ルール R8</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "（ア）地図製作者が行う取捨選択のこと。すなわち、鉄道は載せるが小道は消す、ある集落は"
              "太字で名を示し、別の集落は目が素通りするほど小さな活字で示す、といった、何に線と名を"
              "与え、何を与えないかという判断である。（イ）こうした判断は地図の上で明示されないため、"
              "読者はそれが誰かの判断の集まりであることに気づかず、あたかも写真を受け取るように、"
              "ありのままの世界の姿として受け取ってしまう。だからこそ、その沈黙が選択を強力にする"
              "のである。",
     "points": "▶<b>採点要素</b>：（ア）<b>選択の中身</b>＝鉄道／小道、太字／極小の活字という"
               "本文の具体例を挙げる（4点）〔<b>読解ルール R4</b>〕／（イ）<b>announced されない"
               "＝明示されない</b>ので読者が判断だと気づかない（3点）／<b>as though receiving a "
               "photograph</b>＝「写真のように」＝ありのままの記録として受け取ってしまう（3点）"
               "〔<b>読解ルール R5</b>：These choices / that silence の中身を確定〕。"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（Yet→通念の反転）、空所B（But→第3段の主張転換「律せられている≠中立」）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（but / yet）で反転し主張を強める", "★★★",
         "第2段「It is true that mapmakers are not free to invent」→ 第3段 But で反転。"),
        ("R3", "not A but B / not X, nor Y は、後ろ側または否定の外に主張がある", "★★★",
         "下線部(3) not a photograph … but an argument、第6段 not whether it selects … but whether its selections serve …。"),
        ("R4", "抽象 → 具体（A railway appears / Colonial maps …）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段の鉄道・小道・活字の大小、第5段の植民地地図・係争地・中心の位置——すべて「選択が語る」ことの例。"),
        ("R5", "指示語（this / these choices / that silence / it）は必ず中身を確定する", "★★★",
         "下線部(2) These choices・that silence（問5）、下線部(3) an argument about <b>it</b>＝the world。"),
        ("R6", "因果（therefore / and so / this is why）で理由と結論をつなぐ", "★★",
         "第3段 every projection must <b>therefore</b> decide …、第4段 <b>and so</b> the mapmaker must decide …。"),
        ("R13", "譲歩の後の「限定つき肯定」を読む——筆者は全否定していない", "★★★",
         "第6段 To notice this is not to conclude that maps deceive us, nor that one map is as good as another（＝両極端をともに退ける）。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。pays for … by -ing の因果、as though receiving a photograph の比喩を利用する。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、逆・言い過ぎ（all / never / regardless）を疑う", "★★★",
         "問4・問6・問7。③「印刷地にかかわらず同じ」・⑤「同じように適している」はいずれも本文と逆。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "A cartographer <who moved a city …>、regions <(that) their authors had never walked>、"
         "borders <that shaped the lives of millions>、the purpose <for which it is used> 型。"),
        ("R14", "What で始まる名詞節が主語になる（関係代名詞 what）", "★★",
         "第4段 that silence is <b>what makes them powerful</b>、第6段 <b>What a map should be judged by</b> is …。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「地図ほど議論の余地のない文書はない。歴史や政治はもめても<b>地理は決着済み</b>」を提示。"
             "→ <b>Yet（R1）</b>：丸い地球をどう平らな紙に載せるかを問うた瞬間、その心地よい前提は"
             "溶け始める。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに製作者は勝手に発明できない。構図のために都市を"
             "動かせば<b>芸術ではなく誤りの罪</b>。<b>測量が各段階で地図を律する</b>——だからこそ地図は"
             "最も有用な文書の一つであり続ける（問4）。"},
    {"arrow": "◀ But 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "だが<b>律せられていること（discipline）と中立であること（neutrality）は同じではない</b>。"
             "球面は損傷なしに平面化できない→<b>どの投影法も「どの歪みを引き受けるか」を選ぶ</b>。"
             "教室の地図は方位を守り、<b>その代償に極付近を膨らませる</b>（下線部(1)＝問3）。"},
    {"arrow": "↓　同じ構造がもう一段（R4 具体化）"},
    {"role": "理由②（選択）", "para": "¶4", "kind": "reason",
     "text": "<b>取捨選択も同じ方向に働く</b>：すべてを示す地図は無用→<b>何に線を与えるかを決める</b>"
             "（鉄道は現れ、小道は消える／太字と極小の活字）。<b>その判断は告げられず、その沈黙が"
             "選択を強力にする</b>（下線部(2)＝問5）——読者は<b>写真を受け取るように</b>判断の束を受け取る。"},
    {"arrow": "↓　歴史の実例（R4）"},
    {"role": "具体例（歴史）", "para": "¶5", "kind": "reason",
     "text": "植民地地図は<b>歩いたこともない地域</b>に自信ありげな線を引き、その線はのちに<b>国境として"
             "固まり数百万の生を形づくった</b>。係争地は<b>印刷地によって違って</b>描かれる。"
             "<b>中心の位置</b>さえ主張——ある海と大陸を中心に据え、他を余白へ回す。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "ただし<b>両極端をともに退ける（R13）</b>：地図が我々を欺くとも、どの地図も同じように良い"
             "とも結論しない。<b>地図は世界の写真ではなく世界についての主張であり、主張には巧拙がある"
             "（not A but B・R3）</b>＝下線部(3)。<b>評価軸は「選択するか否か」ではなく「その選択が"
             "用途に適うか」</b>（問6）。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "実践的教訓は<b>地図への疑いではなく読み方の習慣</b>：何のために作られたか／何を落としたか"
             "／その選択は誰の利害に資するか、と問う。問うても海岸線は溶けない——<b>地図を、それを描いた"
             "人間の手に返すだけ</b>。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 地図をめぐる二つの前提",
     "caption": "〈写真〉と見なせば地図は<b>ありのままの記録</b>で議論の余地がない（第1段）。"
                "〈主張〉と見なせば、そこには<b>引き受けた歪みと落とした情報</b>という選択が見える"
                "（第3・4段）。本文は Yet を境に前者から後者へ反転する。",
     "para": "→ 第1・3・6段"},
    {"id": "fig2", "title": "図2 ｜ 選択が入り込む二つの場所",
     "caption": "①<b>投影</b>：球を平面にする以上どこかが歪む。方位を守れば極付近が膨らむ／面積を守れば"
                "形が崩れる（第3段）。②<b>取捨</b>：鉄道は載り小道は消える、名は太字か極小か（第4段）。"
                "どちらも<b>告げられないまま</b>読者に届く。",
     "para": "→ 第3〜4段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 写真ではなく主張、ゆえに巧拙がある",
     "caption": "「地図は嘘つき」でも「どれも同じ」でもない。<b>not a photograph but an argument</b>——"
                "主張である以上、<b>用途に適っているか</b>で評価できる。航海者に適した投影法が人口の研究者を"
                "誤らせるのはそのため（第6段）。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "私たちが参照するあらゆる文書の中で、地図ほど論争の余地がなさそうに見えるものはほとんどない。"
        "地図は、そこにあるものをただ示してくれるだけだ、と私たちは思い込んでいる——海岸線、国境、"
        "河川、道路が、器具の許す限り忠実に記録されているのだ、と。歴史や政治については意見の相違が"
        "生じるかもしれないが、地理はさすがに決着がついている、と。<b>しかし</b>、丸い地球がどのように"
        "平らな紙の上に置かれているのかと問うた瞬間、この心地よい思い込みは溶け始める。"),
    (2, "確かに、地図製作者は好き勝手に作り出す自由を持っているわけではない。心地よい構図のために"
        "都市を百キロメートル動かすような製図者は、芸術の罪ではなく誤りの罪を犯していることになり、"
        "どんな測量もその結果を裏づけはしないだろう。測量はあらゆる段階で地図を律している。"
        "そしてこれこそが、地図が私たちの持つ最も有用な文書の一つであり続けている理由なのである。"),
    (3, "<b>だが</b>、律せられているということは、中立であるということと同じではない。球体は損なわれる"
        "ことなく平らにされることはできず、それゆえどの投影法も、どの種類の損なわれ方を受け入れるかを"
        "決めなければならない。<b>教室でおなじみの地図は方位を忠実に保ち、そしてその忠実さの代償として、"
        "極に近い陸地を膨らませているのである。</b>他の投影法は面積を正直に保ち、代わりに形の方を"
        "犠牲にする。どの投影法もこの選択から逃れられない。あるのはただ、どの損失が受け入れられると"
        "みなされるのか、そして<b>誰によって</b>そうみなされるのか、という問いだけである。"),
    (4, "取捨選択も同じ方向に働く。すべてを示すような地図は役に立たないだろう。だからこそ地図製作者は、"
        "何が線を与えられるに値し、何がそうでないかを決めなければならない。鉄道が現れ、小道が消える。"
        "ある集落は太字で名を記され、別の集落は目が素通りしてしまうほど小さな活字で記される。"
        "<b>こうした選択が告げられることはめったになく、そしてその沈黙こそが、選択を強力なものにして"
        "いるのだ。</b>読者は、まるで一枚の写真を受け取るかのようにして、判断の束を受け取っている。"),
    (5, "歴史はより鋭い事例を提供してくれる。植民地時代の地図は、その作者が一度も歩いたことのない"
        "地域を横切って自信ありげな線を引き、それらの線はのちに国境として固まって、数百万の人々の"
        "生活を形づくった。係争中の領域は、今なお、地図帳がどこで印刷されるかによって異なった形で"
        "示される。中心の位置さえもが一つのメッセージを担っている——世界地図はある海を、そしてある"
        "大陸を、その中心に据え、それ以外のすべてを静かに周縁へと割り当てるのだ。"),
    (6, "このことに気づくのは、地図が私たちを欺いていると結論することでもなければ、どの地図も同じように"
        "良いと結論することでもない。<b>地図とは世界を写した写真ではなく、世界についての一つの主張で"
        "あり、そして主張というものはうまく行うことも、まずく行うこともできるのである。</b>"
        "航海者に適した投影法は、人口を研究する者を誤らせる。小道を隠す地図は、車を運転する人にとっては"
        "まさに必要なものであるかもしれない。地図が判断されるべき基準は、それが取捨選択をしているか"
        "どうかではなく——どの地図もそうしているのだから——その取捨選択が、その地図が使われる目的に"
        "かなっているかどうかなのである。"),
    (7, "実践的な教訓は、地図への疑いというよりは、読み方の習慣である。その絵を受け入れる前に、"
        "その地図は何のために作られたのか、何を省いているのか、そしてその選択はたまたま誰の利害に"
        "かなっているのか、と問うてみる価値がある。そうした問いが海岸線を溶かしてしまうわけではない。"
        "それらはただ、地図を、それを描いた人間の手へと返すだけなのである。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("consult", "（辞書・資料を）参照する"),
    ("controversial", "論争を呼ぶ"),
    ("assume", "〜だと思い込む、前提とする"),
    ("faithfully", "忠実に"),
    ("instrument", "器具、道具"),
    ("arise", "生じる"),
    ("settled", "決着のついた"),
    ("assumption", "思い込み、前提"),
    ("dissolve", "溶ける、消えてなくなる"),
    ("invent", "作り出す、でっち上げる"),
    ("cartographer", "地図製作者、製図者"),
    ("for the sake of ~", "〜のために"),
    ("be guilty of ~", "〜の罪を犯している"),
    ("survey", "測量、調査"),
    ("confirm", "〜を裏づける"),
    ("discipline", "（動詞）〜を律する"),
    ("possess", "〜を所有する"),
    ("neutrality", "中立性"),
    ("sphere", "球体"),
    ("flatten", "〜を平らにする"),
    ("projection", "投影法"),
    ("preserve", "〜を保つ"),
    ("fidelity", "忠実さ"),
    ("inflate", "〜を膨らませる"),
    ("escape", "〜から逃れる"),
    ("deserve", "〜に値する"),
    ("vanish", "消える"),
    ("settlement", "集落"),
    ("announce", "〜を公表する、告げる"),
    ("as though ~", "まるで〜であるかのように"),
    ("judgement", "判断"),
    ("harden into ~", "固まって〜になる"),
    ("in dispute", "係争中の"),
    ("atlas", "地図帳"),
    ("assign A to B", "AをBに割り当てる"),
    ("margin", "周縁、余白"),
    ("deceive", "〜を欺く"),
    ("mislead", "〜を誤らせる"),
    ("serve", "〜にかなう、役立つ"),
    ("suspicion", "疑い"),
    ("leave out ~", "〜を省く"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：通念「地図に論争の余地はない」と、その反転（Yet）",
  "sentences": [
    {"chunks": [("M","(Of all the documents &lt;(that) we consult&gt;),","私たちが参照するあらゆる文書の中で"),
                ("S","few","ほとんど〜ない"),("V","seem","見える"),
                ("C","less controversial than a map.","地図ほど論争の余地がなさそうには")],
     "note":"▶ <b>few＝準否定の主語</b>「ほとんど〜ない」。<b>比較級 + than</b> で「地図より論争が少なく見えるものはほとんどない」"
            "＝事実上の最上級。関係代名詞の省略 (that) we consult〔R11〕。"},
    {"chunks": [("S","A map,","地図は"),("M","we assume,","と私たちは思い込んでいる"),
                ("M","simply","ただ"),("V","shows","示す"),("O","us","私たちに"),
                ("O","[what is there]:","そこにあるものを"),
                ("-","coastlines, borders, rivers, and roads, &lt;recorded as faithfully as instruments allow&gt;.","——海岸線・国境・河川・道路が、器具の許す限り忠実に記録されて")],
     "note":"▶ we assume＝挿入。what 節＝名詞節〔R14〕。コロン以下は同格の言い換えで、"
            "過去分詞 recorded … が名詞群を説明〔R11〕。<b>as ~ as … allow</b>＝「…が許す限り〜」。"},
    {"chunks": [("S","Disagreements","意見の相違は"),("V","may arise","生じるかもしれない"),
                ("M","(about history or politics),","歴史や政治については"),("接","but","しかし"),
                ("M","surely","さすがに"),("S","geography","地理は"),("V","is","である"),("C","settled.","決着済み")],
     "note":"▶ 通念の核。surely＝「きっと〜のはずだ」という話者の確信（ここでは<b>後で覆される前提</b>）。"},
    {"chunks": [("接","Yet,","しかし"),
                ("M","(the moment we ask [how a round earth is placed on a flat page]),","丸い地球がどのように平らな紙の上に置かれているのかと問うた瞬間"),
                ("S","this comfortable assumption","この心地よい思い込みは"),("V","begins","始める"),
                ("O","to dissolve.","溶け")],
     "note":"▶ <b>R1｜逆接 Yet の直後が主張</b>（＝空所A）。<b>the moment S V</b>＝接続詞「〜した瞬間に」。"
            "how 節＝間接疑問（ask の目的語）。"},
  ]},
 {"head": "第2段 — 譲歩：測量が地図を律している（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当"),
                ("-","[that mapmakers are not free to invent].","地図製作者が好き勝手に作り出す自由を持っていないということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。第3段の But（反転）の前振り。"
            "be free to do＝「自由に〜できる」。"},
    {"chunks": [("S","A cartographer &lt;who moved a city a hundred kilometres (for the sake of a pleasing design)&gt;","心地よい構図のために都市を百キロメートル動かすような製図者は"),
                ("V","would be","であろう"),("C","guilty of an error, not of art,","芸術の罪ではなく誤りの罪を犯していること"),
                ("接","and","そして"),("S","no survey","どんな測量も"),("V","would confirm","裏づけないだろう"),
                ("O","the result.","その結果を")],
     "note":"▶ <b>仮定法過去</b>（moved / would be）＝現実にはありえない想定。"
            "<b>not A but B の変形（B, not A）</b>＝「芸術ではなく誤りの」〔R3〕。関係詞節が主語を修飾〔R11〕。"},
    {"chunks": [("S","Measurement","測量は"),("V","disciplines","律する"),("O","the map","地図を"),
                ("M","(at every stage),","あらゆる段階で"),("接","and","そして"),
                ("S","this","これが"),("V","is","である"),
                ("C","why maps remain among the most useful documents &lt;(that) we possess&gt;.","地図が私たちの持つ最も有用な文書の一つであり続けている理由")],
     "note":"▶ discipline＝<b>動詞</b>「律する」。<b>this is why …</b>＝因果〔R6〕。"
            "among the most ~＝「最も〜なものの一つ」。<b>問4②の根拠</b>。"},
  ]},
 {"head": "第3段 — 主張の転換：律せられていること ≠ 中立（But）",
  "sentences": [
    {"chunks": [("接","But","だが"),("S","discipline","律せられているということは"),
                ("V","is not","ではない"),("C","the same as neutrality.","中立であることと同じ")],
     "note":"▶ <b>R1｜But＝逆接でここが主張転換点</b>（＝空所B）。<b>the same as ~</b>＝「〜と同じ」。"
            "第2段の譲歩（測量が律する）を認めたうえで、それが中立を意味しないと切り返す。"},
    {"chunks": [("S","A sphere","球体は"),("V","cannot be flattened","平らにされることはできない"),
                ("M","(without damage),","損なわれることなく"),("接","and","そして"),
                ("S","every projection","どの投影法も"),("M","therefore","それゆえ"),
                ("V","must decide","決めなければならない"),
                ("O","[which kind of damage it will accept].","どの種類の損なわれ方を受け入れるかを")],
     "note":"▶ 助動詞つき受動態 cannot be flattened。<b>therefore＝因果</b>〔R6〕。"
            "which 節＝間接疑問（decide の目的語）。<b>問7①の根拠</b>。"},
    {"chunks": [("S","The familiar classroom map","教室でおなじみの地図は"),("V","preserves","保ち"),
                ("O","direction","方位を"),("M","faithfully,","忠実に"),("接","and","そして"),
                ("V","pays","払う"),("M","(for that fidelity)","その忠実さの代償を"),
                ("M","(by inflating the lands near the poles).","極に近い陸地を膨らませることによって")],
     "note":"▶ <b>下線部(1)＝問3</b>。<b>pay for ~</b>＝「〜の代償を払う」。<b>by -ing</b>＝手段。"
            "「得るものと失うもの」の交換が読み取れるかが要点。"},
    {"chunks": [("S","Other projections","他の投影法は"),("V","keep","保ち"),("O","areas","面積を"),
                ("C","honest","正直に"),("接","and","そして"),("V","let","させる"),
                ("O","shapes","形の方を"),("C","suffer","犠牲になるように"),("M","instead.","代わりに")],
     "note":"▶ <b>keep O C</b>／<b>let O do</b>（使役）。前文との対比で「どちらを守ってもどこかが崩れる」ことを示す。"},
    {"chunks": [("S","No projection","どの投影法も〜ない"),("V","escapes","逃れない"),("O","the choice;","この選択から"),
                ("M","there","（存在）"),("V","is","ある"),
                ("S","only the question of [which loss is thought acceptable], and by whom.","どの損失が受け入れられるとみなされるのか、そして誰によってか、という問いだけが")],
     "note":"▶ No + 名詞＝全否定。there is 構文。<b>be thought C</b>＝「Cだとみなされる」。"
            "文末の <b>and by whom</b> が「中立ではない＝誰かの判断だ」という主張を決定づける。"},
  ]},
 {"head": "第4段 — 選択：告げられない判断が読者に届く",
  "sentences": [
    {"chunks": [("S","Selection","取捨選択も"),("V","works","働く"),("M","(in the same direction).","同じ方向に")],
     "note":"▶ 段落の導入。「投影」に続き「取捨」でも同じ構造（＝選択が入る）が起きると宣言する。"},
    {"chunks": [("S","A map &lt;that showed everything&gt;","すべてを示すような地図は"),
                ("V","would be","であろう"),("C","useless,","役に立たない"),("接","and so","だからこそ"),
                ("S","the mapmaker","地図製作者は"),("V","must decide","決めなければならない"),
                ("O","[what deserves a line] and [what does not].","何が線を与えられるに値し、何がそうでないかを")],
     "note":"▶ <b>仮定法過去</b>（showed / would be）。<b>and so＝因果</b>〔R6〕。what 節が二つ並列〔R14〕。"
            "<b>問7②の根拠</b>。"},
    {"chunks": [("S","A railway","鉄道が"),("V","appears;","現れ"),
                ("S","a footpath","小道が"),("V","vanishes.","消える")],
     "note":"▶ <b>R4｜具体例</b>。セミコロンで二文を並置し、対照を短く際立たせる。"},
    {"chunks": [("S","One settlement","ある集落は"),("V","is named","名を記され"),("M","(in bold),","太字で"),
                ("S","another","別の集落は"),("M","(in a type &lt;so small that the eye passes over it&gt;).","目が素通りしてしまうほど小さな活字で（名を記される）")],
     "note":"▶ 後半は is named の省略。<b>so ~ that …</b>＝「あまりに〜なので…」。"
            "one … another …＝「あるものは…別のものは…」。"},
    {"chunks": [("S","These choices","こうした選択は"),("V","are","である"),("M","rarely","めったに〜ない"),
                ("C","announced,","告げられ（ない）"),("接","and","そして"),
                ("S","that silence","その沈黙こそが"),("V","is","である"),
                ("C","[what makes them powerful].","選択を強力なものにしているもの")],
     "note":"▶ <b>下線部(2)＝問5</b>。rarely＝準否定。<b>R14｜what 節が補語</b>。<b>make O C</b>。"
            "them＝These choices〔R5〕。"},
    {"chunks": [("S","The reader","読者は"),("V","receives","受け取る"),("O","a set of judgements","判断の束を"),
                ("M","(as though receiving a photograph).","まるで一枚の写真を受け取るかのようにして")],
     "note":"▶ <b>as though + 分詞</b>＝「まるで〜するかのように」（as though he were receiving の省略形）。"
            "問5（イ）の解答の核——<b>判断なのに記録として受け取ってしまう</b>。"},
  ]},
 {"head": "第5段 — 歴史の実例：線は国境になり、中心は序列を語る",
  "sentences": [
    {"chunks": [("S","History","歴史は"),("V","supplies","提供する"),("O","the sharper cases.","より鋭い事例を")],
     "note":"▶ <b>R4｜抽象→具体</b>の合図。比較級 sharper＝前段までの例より強い例が来る。"},
    {"chunks": [("S","Colonial maps","植民地時代の地図は"),("V","drew","引いた"),
                ("O","confident lines","自信ありげな線を"),
                ("M","(across regions &lt;(that) their authors had never walked&gt;),","その作者が一度も歩いたことのない地域を横切って"),
                ("接","and","そして"),("S","those lines","それらの線は"),("M","later","のちに"),
                ("V","hardened","固まった"),
                ("M","(into borders &lt;that shaped the lives of millions&gt;).","数百万の人々の生活を形づくった国境へと")],
     "note":"▶ 関係代名詞の省略＋<b>過去完了</b>（had never walked＝線を引いた時点より前）〔R11〕。"
            "harden into ~＝「固まって〜になる」。<b>問7④の根拠</b>。"},
    {"chunks": [("S","Territories &lt;in dispute&gt;","係争中の領域は"),("M","still","今なお"),
                ("V","are shown","示される"),("M","differently","異なった形で"),
                ("M","(depending on [where an atlas is printed]).","地図帳がどこで印刷されるかによって")],
     "note":"▶ depending on ~＝「〜によって」。where 節＝名詞節。"
            "<b>問7③はこの文と逆</b>（「印刷地にかかわらず同じ」は誤り）〔R9〕。"},
    {"chunks": [("M","Even","〜さえもが"),("S","the position of the centre","中心の位置"),
                ("V","carries","担っている"),("O","a message:","一つのメッセージを"),
                ("S","a world map","世界地図は"),("V","places","据え"),
                ("O","some ocean, and some continent,","ある海を、そしてある大陸を"),
                ("M","(at its heart),","その中心に"),("接","and","そして"),
                ("M","quietly","静かに"),("V","assigns","割り当てる"),("O","everything else","それ以外のすべてを"),
                ("M","(to a margin).","周縁へと")],
     "note":"▶ コロン以下が a message の中身を具体化。<b>assign A to B</b>＝「AをBに割り当てる」。"
            "margin＝「周縁・余白」（第7段の「人間の手」への伏線）。"},
  ]},
 {"head": "第6段 — 核心：写真ではなく主張、ゆえに巧拙がある（not A but B）",
  "sentences": [
    {"chunks": [("S","To notice this","このことに気づくのは"),("V","is not","ではない"),
                ("C","to conclude [that maps deceive us],","地図が私たちを欺いていると結論すること"),
                ("-","nor [that one map is as good as another].","どの地図も同じように良いと結論することでもない")],
     "note":"▶ <b>R13｜両極端をともに退ける</b>。不定詞が主語と補語。<b>nor</b>＝「〜もまた…ない」。"
            "<b>問6①②はこの一文で×</b>〔R9〕。"},
    {"chunks": [("S","A map","地図とは"),("V","is","である"),
                ("C","not a photograph of the world but an argument about it,","世界を写した写真ではなく、世界についての一つの主張"),
                ("接","and","そして"),("S","arguments","主張は"),("V","can be made","なされうる"),
                ("M","well or badly.","うまくも、まずくも")],
     "note":"▶ <b>下線部(3)＝問2</b>。<b>R3｜not A but B＝Bが主張</b>。it＝the world〔R5〕。"
            "受動態 can be made＝「なされうる」＝<b>巧拙がある</b>（前文の「どれも同じ」の否定と呼応）。"},
    {"chunks": [("S","The projection &lt;that suits a navigator&gt;","航海者に適した投影法は"),
                ("V","misleads","誤らせる"),("O","a student of population;","人口を研究する者を"),
                ("S","a map &lt;that hides a footpath&gt;","小道を隠す地図は"),("V","may be","かもしれない"),
                ("C","exactly [what a driver needs].","車を運転する人がまさに必要とするもの")],
     "note":"▶ 関係詞節が二つ〔R11〕、what 節が補語〔R14〕。セミコロンで並置し「<b>目的が変われば評価が"
            "変わる</b>」ことを示す。<b>問7⑤はこの文と逆</b>〔R9〕。"},
    {"chunks": [("S","[What a map should be judged by]","地図が判断されるべき基準は"),("V","is","である"),
                ("C","not [whether it selects], (since all of them do), but [whether its selections serve the purpose &lt;for which it is used&gt;].","それが取捨選択をしているかどうかではなく——どの地図もそうしているのだから——その取捨選択が、その地図が使われる目的にかなっているかどうか")],
     "note":"▶ <b>R14｜What 節が主語</b>（judged <b>by</b> の by が文末に残らず前に出た形）。"
            "<b>not A but B</b> の A・B がともに whether 節〔R3〕。<b>前置詞＋関係代名詞 for which</b>〔R11〕。"
            "<b>問6③の根拠＝本文の評価基準</b>。"},
  ]},
 {"head": "第7段 — 結論：疑いではなく、読み方の習慣を",
  "sentences": [
    {"chunks": [("S","The practical lesson","実践的な教訓は"),("V","is","である"),
                ("C","a habit of reading","読み方の習慣"),
                ("M","rather than a suspicion of maps.","地図への疑いというよりは")],
     "note":"▶ <b>A rather than B</b>＝「BよりむしろA」〔R3〕。「疑え」ではないと明示する点が本文の品位。"
            "<b>問7⑥の判断に関わる一文</b>。"},
    {"chunks": [("M","(Before accepting the picture),","その絵を受け入れる前に"),("S","it","（形式主語）"),
                ("V","is","である"),("C","worth","価値がある"),
                ("-","asking [what the map was made for], [what it leaves out], and [whose interests its choices happen to serve].","その地図は何のために作られたのか、何を省いているのか、その選択はたまたま誰の利害にかなっているのか、と問うてみることは")],
     "note":"▶ <b>it is worth -ing</b>＝「〜する価値がある」。間接疑問が三つ並列〔R14〕。"
            "<b>happen to do</b>＝「たまたま〜する」（皮肉のニュアンス）。"},
    {"chunks": [("S","Such questions","そうした問いは"),("V","do not make","させはしない"),
                ("O","the coastlines","海岸線を"),("C","dissolve.","溶け")],
     "note":"▶ <b>make O do</b>（使役）の否定。第1段の dissolve を回収し、「相対主義に陥るのではない」と限定する〔R13〕。"},
    {"chunks": [("S","They","それらは"),("M","simply","ただ"),("V","return","返す"),("O","the map","地図を"),
                ("M","(to the human hands &lt;that drew it&gt;).","それを描いた人間の手へと")],
     "note":"▶ 締めの一文。関係詞節が the human hands を修飾〔R11〕。"
            "<b>「自然の記録」から「人の作品」へ</b>という本文全体の主張を一文で回収する。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=4文/第2段=3文/第3段=5文/第4段=6文/第5段=4文/第6段=4文/第7段=4文)
SVOC_LOGIC = {
    (1, 1): "対比", (1, 3): "対比", (1, 4): "主張",
    (2, 1): "譲歩", (2, 2): "具体例", (2, 3): "因果",
    (3, 1): "対比", (3, 2): "因果", (3, 3): "主張", (3, 4): "対比", (3, 5): "主張",
    (4, 1): "追加", (4, 2): "因果", (4, 3): "具体例", (4, 4): "具体例", (4, 5): "主張", (4, 6): "主張",
    (5, 1): "具体例", (5, 2): "具体例", (5, 3): "具体例", (5, 4): "主張",
    (6, 1): "譲歩", (6, 2): "主張", (6, 3): "対比", (6, 4): "主張",
    (7, 1): "主張", (7, 2): "具体例", (7, 3): "譲歩", (7, 4): "主張",
}
