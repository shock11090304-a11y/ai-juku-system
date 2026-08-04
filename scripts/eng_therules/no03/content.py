# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.03 — 単一ソース
テーマ: Why Cities Need Nature (都市に自然が必要な理由) / MARCH・難関私大 (The Rules 2〜3 相当)
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "03",
    "level": "MARCH レベル",
    "level_sub": "難関私大 / The Rules 2〜3 相当",
    "theme_ja": "都市に自然が必要な理由",
    "theme_en": "Why Cities Need Nature",
    "minutes": 18,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'A city, in most people\'s imagination, is everything that nature is not: concrete '
        'and glass, traffic and noise, a landscape built by humans for humans. In this picture, '
        'parks and street trees appear as pleasant extras &mdash; decoration that softens urban '
        'life but could be removed without real loss. When budgets tighten, greenery is often '
        'the first thing to be cut. <span class="blank">【&nbsp;A&nbsp;】</span>, a different '
        'view has been gaining ground among researchers and planners: the green corners of a '
        'city may be doing far more serious work than we give them credit for.'),
    (2, 'The advantages of city life are real. Cities concentrate jobs, schools, and ideas; '
        'millions of people can live, meet, and trade within a small area, and culture thrives '
        'where strangers gather. It is precisely this density that makes urban life efficient, '
        'and density leaves little room for open land. Seen this way, the shortage of nature '
        'can look like a fair price for everything a city offers.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, the greenery that survives among the '
        'buildings is not mere ornament. Research suggests that time spent in or near green '
        'space helps the mind recover its capacity for attention, which city noise and crowds '
        'constantly wear down. People who see trees from a window, or cross a park on the way '
        'to work, also tend to report less stress. Nature, in other words, quietly maintains '
        'the very residents who keep the city running.'),
    (4, 'Nature also works on the city itself. <u>A single mature tree can cool the street '
        'beneath it, because its shade blocks the sun while the moisture released from its '
        'leaves lowers the temperature of the surrounding air.<sup>(1)</sup></u> Multiply that '
        'tree by thousands, and a heat wave becomes easier to survive. Below ground, soil and '
        'roots absorb heavy rain, holding back water that would otherwise rush into the drains '
        'and flood the streets. Concrete can do neither of these jobs: it stores heat and '
        'repels water.'),
    (5, 'Critics reply that greenery is expensive: trees must be planted, watered, and pruned, '
        'and parks demand constant care. The objection deserves an answer, and it has one. '
        '<u>The money a city spends on its green spaces quietly comes back in other '
        'forms.<sup>(2)</sup></u> Residents who stay healthier place a lighter burden on '
        'medical services; shaded streets reduce the electricity used for cooling; and ground '
        'that drinks the rain cuts the cost of flood damage. What looks like spending is, over '
        'time, closer to saving.'),
    (6, 'The conclusion these facts point to is simple but easily missed: urban nature is '
        '<u>not decoration but a kind of infrastructure,<sup>(3)</sup></u> as essential to a '
        'working city as roads, pipes, and power lines. We do not call a water system a luxury '
        'and ask whether the city can afford it; we ask how to keep it working. Trees and '
        'parks deserve the same question. A city that treats its greenery as an ornament will '
        'cut it first and pay for the loss later.'),
    (7, 'None of this means that every city should be turned back into a forest, or that a '
        'lawn matters more than a hospital. The real question is one of design: what does a '
        'city count as necessary? As long as nature sits in the category of the merely '
        'pleasant, it will always lose to the next urgent demand. Move it into the category '
        'of necessity, and the city we build will support the people who live in it &mdash; '
        'not despite being a city, but by being a better one.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "A city, in most people's imagination, is everything that nature is not: concrete and "
    "glass, traffic and noise, a landscape built by humans for humans. In this picture, parks "
    "and street trees appear as pleasant extras decoration that softens urban life but could "
    "be removed without real loss. When budgets tighten, greenery is often the first thing to "
    "be cut. Nevertheless, a different view has been gaining ground among researchers and "
    "planners: the green corners of a city may be doing far more serious work than we give "
    "them credit for. "
    "The advantages of city life are real. Cities concentrate jobs, schools, and ideas; "
    "millions of people can live, meet, and trade within a small area, and culture thrives "
    "where strangers gather. It is precisely this density that makes urban life efficient, and "
    "density leaves little room for open land. Seen this way, the shortage of nature can look "
    "like a fair price for everything a city offers. "
    "Still, the greenery that survives among the buildings is not mere ornament. Research "
    "suggests that time spent in or near green space helps the mind recover its capacity for "
    "attention, which city noise and crowds constantly wear down. People who see trees from a "
    "window, or cross a park on the way to work, also tend to report less stress. Nature, in "
    "other words, quietly maintains the very residents who keep the city running. "
    "Nature also works on the city itself. A single mature tree can cool the street beneath "
    "it, because its shade blocks the sun while the moisture released from its leaves lowers "
    "the temperature of the surrounding air. Multiply that tree by thousands, and a heat wave "
    "becomes easier to survive. Below ground, soil and roots absorb heavy rain, holding back "
    "water that would otherwise rush into the drains and flood the streets. Concrete can do "
    "neither of these jobs: it stores heat and repels water. "
    "Critics reply that greenery is expensive: trees must be planted, watered, and pruned, and "
    "parks demand constant care. The objection deserves an answer, and it has one. The money a "
    "city spends on its green spaces quietly comes back in other forms. Residents who stay "
    "healthier place a lighter burden on medical services; shaded streets reduce the "
    "electricity used for cooling; and ground that drinks the rain cuts the cost of flood "
    "damage. What looks like spending is, over time, closer to saving. "
    "The conclusion these facts point to is simple but easily missed: urban nature is not "
    "decoration but a kind of infrastructure, as essential to a working city as roads, pipes, "
    "and power lines. We do not call a water system a luxury and ask whether the city can "
    "afford it; we ask how to keep it working. Trees and parks deserve the same question. A "
    "city that treats its greenery as an ornament will cut it first and pay for the loss "
    "later. "
    "None of this means that every city should be turned back into a forest, or that a lawn "
    "matters more than a hospital. The real question is one of design: what does a city count "
    "as necessary? As long as nature sits in the category of the merely pleasant, it will "
    "always lose to the next urgent demand. Move it into the category of necessity, and the "
    "city we build will support the people who live in it not despite being a city, but by "
    "being a better one."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Nevertheless &nbsp; ② Therefore &nbsp; ③ For instance &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① As a result &nbsp; ② In other words &nbsp; ③ Likewise &nbsp; ④ Still",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(1) <span class='en'>A single mature tree can cool the street beneath it, "
             "because its shade blocks the sun while the moisture released from its leaves "
             "lowers the temperature of the surrounding air.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(2) について、都市が緑地に使うお金が「静かに別の形で戻ってくる（<span "
             "class='en'>quietly comes back in other forms</span>）」とはどういうことか。"
             "本文に即して具体的に説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で述べられている「緑地と人の心」に関する研究知見の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 緑地の中で時間を過ごすと注意力はかえって消耗するが、木々が窓から見える場合に限って、ストレスだけは減ると研究は示している。",
         "② 緑地の中やその近くで過ごす時間は、都市生活ですり減る注意力の回復を助け、窓から木々が見えるような人はストレスが少ない傾向もある、と研究は示唆している。",
         "③ 緑の効果を心が受け取るためには、窓から木々を眺めるだけではまったく足りず、毎日公園の中で長時間過ごすことが不可欠である。",
         "④ 緑地の効果は夏の気温を下げたり雨水を吸収したりといった物理的なものに限られ、注意力やストレスなど人の心には影響しない。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>not decoration but a kind of infrastructure</span> "
             "とあるが、都市の自然が「飾りではなくインフラの一種」であるとはどういうことか。"
             "緑が果たしている働きの中身にふれながら、本文全体をふまえて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 都市の密度や効率がもたらすとされる利点は幻想であり、住民の健康を考えれば、都市生活そのものに本当の利点はない。",
         "② 緑地は維持に金がかかるのだから、財政の苦しい都市はまず公園や街路樹の予算から削るのが最も合理的である。",
         "③ 都市の緑は飾りではなく都市を支えるインフラの一種であり、何を「必需」とみなすかという都市設計の発想を問い直すべきだ。",
         "④ すべての都市は建物を減らして森に戻し、人間の便利さよりも自然を何よりも優先すべきである。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 筆者によれば、都市が与えてくれる仕事や文化といった利点は、実際には見せかけにすぎない。",
         "② 予算が苦しくなると、緑はしばしば真っ先に削られる対象になる。",
         "③ コンクリートは木々と同じように、熱を和らげ、雨水を吸収することができる。",
         "④ 木陰と、葉から放出される水分は、暑い日に通りの気温を下げる働きをする。",
         "⑤ 緑地への支出は、医療の負担減・冷房電力の削減・水害費用の削減という形で戻ってくる、と筆者は論じている。",
         "⑥ 都市に十分な数の木を植えれば、洪水の被害を完全になくすことができる。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ① Nevertheless　　B ＝ ④ Still",
     "exp": "A：「都市＝自然の反対物、緑＝真っ先に削られる飾り」という通念に対し、研究者・計画家が"
            "「緑ははるかに重大な仕事をしている」と反論する流れ。<b>逆接</b>でつなぐ → Nevertheless。"
            "Therefore（因果）・For instance（例示）・In addition（追加）は不可。<br>"
            "B：第2段「都市の利点は本物（＝譲歩）」に対し、第3段は「それでも緑は単なる飾りではない」と"
            "主張へ<b>転換</b>する。逆接 → Still。As a result（因果）・In other words（言い換え）・"
            "Likewise（類比）は流れに合わない。 〔<b>解法ルール R7</b>／<b>読解ルール R1</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "②",
     "exp": "第3段「time spent in or near green space helps the mind recover its capacity for "
            "attention」＋「People who see trees from a window … tend to report less stress」＝"
            "緑地の中や近くで過ごす時間は注意力の回復を助け、木々が見える人はストレスも少ない傾向。"
            "①は逆（注意力は<i>回復</i>する）、③は本文にない（窓から見えるだけでもよい）、"
            "④は第3段（心への効果そのものを述べている）と矛盾。 〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "③",
     "exp": "第6段「urban nature is not decoration but a kind of infrastructure」＋第7段"
            "「The real question is one of design: what does a city count as necessary?」と一致。"
            "①は第2段冒頭「The advantages of city life are real」に反する。②は本文と逆（飾り扱い"
            "して削る都市は後で代償を払う・第6段）。④は第7段「森に戻すべきだという意味ではない」で"
            "明確に否定。 〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "②・④・⑤",
     "exp": "①×：第2段冒頭「The advantages of city life are real（都市の利点は本物）」に反する。"
            "③×：第4段末「Concrete can do neither of these jobs（コンクリートは熱を蓄え水をはじく）」"
            "に反する。⑥×：本文は「水を堰き止める」「水害の費用を減らす」（第4・5段）であり、"
            "「完全になくす」は<b>言い過ぎ</b>。 〔<b>解法ルール R9</b>：言い換えの見抜き＋"
            "「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(1)和訳",
     "model": "一本の成木があるだけで、その真下の通りは涼しくなりうる。木陰が日差しをさえぎる一方で、"
              "葉から放出される水分がまわりの空気の温度を下げてくれるからである。",
     "points": "▶<b>採点要素</b>：①<b>無生物主語</b> A single mature tree can cool … を「一本の成木の"
               "おかげで／成木が一本あるだけで〜涼しくなる」のように<b>副詞的に</b>訳す（「木が通りを"
               "冷やす」の直訳も可だがやや不自然）／②because 以下の二つの因果（shade blocks the sun／"
               "moisture … lowers the temperature）を正しく訳出／③released from its leaves＝過去分詞の"
               "後置修飾（「葉から放出される水分」）。 〔<b>構文ルール R15・R11</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "都市が緑地に支出した費用は、緑のおかげで住民が健康を保って医療サービスへの負担が軽く"
              "なり、木陰で冷房に使う電力が減り、雨水を吸い込む地面のおかげで水害の被害額が減る、"
              "という節約の形で埋め合わされるので、長期的には支出というより節約に近い、ということ。",
     "points": "▶<b>採点要素</b>：「別の形」の中身＝第5段の三並列を拾う。①<b>医療への負担減</b>／"
               "②<b>冷房電力の削減</b>／③<b>水害費用の削減</b>（各2点程度）＋④支出が長期的には"
               "<b>節約</b>になるというまとめ。批判（緑は金がかかる）への<b>再反論</b>である点を"
               "押さえる。 〔<b>読解ルール R14・R5</b>／<b>解法ルール R8</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "都市の緑は、あってもなくてもよい飾りなのではなく、注意力の回復やストレスの低減によって"
              "都市を動かす住民の心身を支え、木陰と葉からの水分で夏の熱を和らげ、土と根で雨水を吸収して"
              "洪水を防ぐなど、道路や水道と同じように都市が機能するために不可欠な基盤（インフラ）として"
              "働いている、ということ。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「飾り（＝取り除いても実害のないおまけ）」の"
               "否定を反映／②働きの具体＝<b>住民の心身の維持</b>（第3段）＋<b>熱の緩和・雨水の吸収</b>"
               "（第4段）の両方にふれる／③道路・水道管・送電線と同列の「<b>必需</b>」＝都市の機能に"
               "不可欠、を明示。各3〜4点。 〔<b>読解ルール R3</b>／<b>解法ルール R8</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（Nevertheless→研究者・計画家の反論）、空所B（Still→主張転換）。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(3) not decoration but a kind of infrastructure、第7段 not despite being a city, but by being a better one。"),
        ("R5", "指示語・総称（this / it / its work / the problem）は必ず中身を確定する", "★★",
         "第4段 these jobs（冷やす＋雨水を吸う）、第5段 one＝an answer、第6段 these facts。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第4段 because its shade blocks …、第6段「飾り扱い→真っ先に削る→後で代償」。"),
        ("R14", "★NEW 反対意見・コスト批判への「再反論」は主張の強化——譲歩⇄再反論の往復を追う", "★★★",
         "第5段 Critics reply …（批判）→ The objection deserves an answer（受け止め）→ comes back in other forms（再反論）。問3。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。コロン(:)・in other words・not A but B の言い換えを利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。⑥「洪水を完全になくせる」、①「利点は見せかけ」などは典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "the greenery <that survives among the buildings>、the moisture <released from its leaves> 型。"),
        ("R15", "★NEW 無生物主語は副詞的に訳す（〜のおかげで／〜すると）", "★★★",
         "下線部(1)＝問2 A single mature tree can cool …。第5段 shaded streets reduce … も同型。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「都市＝自然の反対物。公園や街路樹は『あれば嬉しい飾り』で、予算が苦しければ真っ先に"
             "削るもの」を提示。→ <b>Nevertheless（R1）</b>：研究者・計画家は「緑ははるかに重大な仕事を"
             "している」と反論。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "都市の利点（仕事・機会・文化）は<b>本物</b>だと認める。密度こそが効率を生み、密度は空き地の"
             "余地を残さない。＝「自然の不足は妥当な対価」に見える。"},
    {"arrow": "◀ Still 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換＋理由①", "para": "¶3", "kind": "claim",
     "text": "緑は<b>単なる飾りではない</b>。理由①＝<b>人を支える</b>：緑地は注意力の回復・ストレスの"
             "低減を助け、都市を動かす住民の心身を静かに維持している（一般的な研究知見）。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶4", "kind": "reason",
     "text": "<b>環境インフラ</b>：木陰と葉からの水分が夏の通りを冷やし（<b>無生物主語＝R15</b>）、"
             "土と根が雨水を吸収して洪水を防ぐ。コンクリートにはどちらの仕事もできない。"},
    {"arrow": "↓　批判 → 再反論（R14）"},
    {"role": "批判→再反論", "para": "¶5", "kind": "concession",
     "text": "「緑は金がかかる」という批判を正面から受け止め→<b>再反論</b>：緑への支出は医療・冷房・治水の"
             "<b>節約</b>という「別の形」で戻る（<b>R6</b>因果）。支出はむしろ節約に近い。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "<b>not decoration but a kind of infrastructure（R3）</b>：緑は飾りではなく、道路・水道管・"
             "送電線と同列の<b>インフラ</b>。水道に「贅沢かどうか」を問わないのと同じ問いを緑にも。"
             "飾り扱いする都市は真っ先に削り、後で代償を払う。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：都市を森に戻せという話ではない。<b>何を「必需」とみなすか</b>という設計思想の"
             "問い直しこそが本題。緑を「必需」の区分に移せば、都市はそこに住む人を支えるものになる。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 緑への二つのまなざし",
     "caption": "同じ「都市の緑」でも、<b>飾りとみなす</b>と予算難で真っ先に削られ後で代償を払い、"
                "<b>必需（インフラ）とみなす</b>と維持されて都市を支え続ける。第1段の通念と第6〜7段の"
                "核心の対比。",
     "para": "→ 第1・6・7段"},
    {"id": "fig2", "title": "図2 ｜ 緑の二つの働きと「戻ってくるお金」",
     "caption": "緑の仕事は二つ。①<b>人を支える</b>（注意の回復・ストレス低減、第3段）、②<b>都市を"
                "支える</b>（木陰・蒸散・雨水吸収、第4段）。この働きが医療・冷房・治水の<b>節約</b>と"
                "なって戻る（第5段＝下線部(2)）。",
     "para": "→ 第3〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 緑は「飾り」ではなく「インフラ」",
     "caption": "問題は「緑を置く余裕があるか」ではなく、<b>何を「必需」とみなすか</b>という設計思想。"
                "緑は贅沢品ではなく、道路や水道と同列の基盤である。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "都市とは、たいていの人の想像の中では、自然がそうでないものすべて——コンクリートとガラス、交通と"
        "騒音、人間が人間のために造った風景——である。この見取り図の中では、公園や街路樹は心地よいおまけ、"
        "すなわち都市生活を和らげはするが取り除いても実害のない飾りとして現れる。予算が苦しくなると、緑は"
        "しばしば真っ先に削られる。<b>それにもかかわらず</b>、研究者や都市計画家の間では異なる見方が支持を"
        "広げてきている。すなわち、都市の緑の一角は、私たちが認めているよりもはるかに重大な仕事をしている"
        "のかもしれない、というのである。"),
    (2, "都市生活の利点は本物である。都市は仕事や学校や発想を一か所に集め、何百万もの人々が狭い地域の中で"
        "暮らし、出会い、取引することができ、見知らぬ者同士が集まる場所では文化が花開く。都市生活を効率的に"
        "しているのはまさにこの密度であり、そして密度は、空き地のための余地をほとんど残さない。このように"
        "見れば、自然の不足は、都市が与えてくれるすべてのものへの妥当な対価のようにも見えうる。"),
    (3, "<b>それでも</b>、建物の間に生き残っている緑は、単なる飾りではない。研究が示唆するところでは、"
        "緑地の中やその近くで過ごす時間は、都市の騒音と人混みが絶えずすり減らしている注意力を、心が取り戻す"
        "助けになる。窓から木々が見えたり、通勤の途中で公園を横切ったりする人々は、ストレスが少ないと報告"
        "する傾向もある。言い換えれば、自然は、都市を動かし続けているまさにその住民たちを、静かに維持して"
        "いるのである。"),
    (4, "自然はまた、都市そのものにも働きかける。<b>一本の成木があるだけで、その真下の通りは涼しくなりうる。"
        "木陰が日差しをさえぎる一方で、葉から放出される水分がまわりの空気の温度を下げてくれるからである。</b>"
        "その木を何千本にも増やしてみれば、熱波は生き延びやすいものになる。地面の下では、土と根が激しい雨を"
        "吸収し、そうでなければ排水溝に殺到して通りを水浸しにするはずの水を、堰き止めてくれる。コンクリートに"
        "は、このどちらの仕事もできない。熱を蓄え、水をはじくのだ。"),
    (5, "批判者たちはこう言い返す——緑は金がかかる。木は植え、水をやり、剪定しなければならず、公園は絶え間"
        "ない手入れを要求する、と。この反対意見は答えるに値するものであり、そして答えはある。<b>都市が緑地に"
        "使うお金は、静かに、別の形で戻ってくるのである。</b>より健康なままでいられる住民は医療サービスへの"
        "負担を軽くし、木陰の通りは冷房に使われる電力を減らし、雨を飲み込む地面は水害の被害額を削る。支出に"
        "見えるものは、時がたてば、節約に近いのだ。"),
    (6, "これらの事実が指し示す結論は、単純だが見落とされやすい。すなわち、都市の自然は<b>飾りではなく一種の"
        "インフラ</b>——道路や水道管や送電線と同じくらい、機能する都市に不可欠なもの——なのである。私たちは"
        "水道網を贅沢品と呼んで、都市にそれを持つ余裕があるかどうかを問うたりはしない。どうすれば機能させ"
        "続けられるかを問う。木々や公園も、同じ問いに値する。緑を飾りとして扱う都市は、真っ先にそれを削り、"
        "あとでその損失の代償を払うことになるだろう。"),
    (7, "とはいえ以上のことは、すべての都市を森に戻すべきだとか、芝生が病院より大事だとかいう意味ではない。"
        "本当の問いは設計の問いである。すなわち、都市は何を「必要」とみなすのか、ということだ。自然が「単に"
        "心地よいもの」という区分に置かれている限り、それは次の緊急の要求に必ず負け続けるだろう。それを"
        "「必需」の区分に移してみよ。そうすれば、私たちが造る都市は、そこに住む人々を支えるものになる——"
        "都市であるにもかかわらず、ではなく、より良い都市であることによって。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("gain ground", "支持を広げる、優勢になる"),
    ("give A credit for B", "AにBの功績を認める"),
    ("concentrate", "集中させる、一か所に集める"),
    ("thrive", "栄える、花開く"),
    ("density", "密度、密集"),
    ("leave little room for ~", "〜の余地をほとんど残さない"),
    ("ornament", "装飾、飾り"),
    ("capacity for ~", "〜の能力"),
    ("wear down", "すり減らす"),
    ("mature", "成熟した、（木が）成木の"),
    ("moisture", "水分、湿気"),
    ("surrounding", "周囲の"),
    ("absorb", "吸収する"),
    ("hold back", "堰き止める、抑える"),
    ("otherwise", "そうでなければ"),
    ("repel", "はじく、寄せつけない"),
    ("prune", "剪定する"),
    ("constant", "絶え間ない"),
    ("burden", "負担"),
    ("infrastructure", "インフラ、（社会の）基盤設備"),
    ("luxury", "贅沢品"),
    ("afford", "（金銭的・時間的に）〜する余裕がある"),
    ("urgent", "緊急の"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 問題提起：都市＝自然の反対物という通念と、その反転",
  "sentences": [
    {"chunks": [("S","A city,","都市とは"),("M","(in most people's imagination),","たいていの人の想像の中では"),
                ("V","is","である"),("C","everything &lt;that nature is not&gt;:","自然がそうでないものすべて"),
                ("-","concrete and glass, traffic and noise, a landscape &lt;built by humans for humans&gt;.","＝コンクリートとガラス、交通と騒音、人間が人間のために造った風景")],
     "note":"▶ コロン(:)以下は everything の中身を並べる<b>同格</b>。that nature is not＝関係代名詞（not の後の補語が欠けた形）。built by …＝過去分詞が landscape を修飾〔<b>R11</b>〕。"},
    {"chunks": [("M","(In this picture),","この見取り図の中では"),("S","parks and street trees","公園や街路樹は"),
                ("V","appear as","〜として現れる"),("C","pleasant extras","心地よいおまけ"),
                ("-","&mdash; decoration &lt;that softens urban life but could be removed without real loss&gt;.","＝都市生活を和らげはするが、取り除いても実害のない飾り")],
     "note":"▶ appear as A＝「Aとして現れる」。decoration 以下は extras の<b>同格</b>言い換え。that …＝関係代名詞が softens と could be removed の二つの動詞を取る〔<b>R11</b>〕。"},
    {"chunks": [("M","(When budgets tighten),","予算が苦しくなると"),("S","greenery","緑は"),
                ("V","is","である"),("C","often the first thing &lt;to be cut&gt;.","しばしば真っ先に削られるもの")],
     "note":"▶ to be cut＝不定詞（受動）が the first thing を修飾〔<b>R11</b>〕。通念の帰結＝「緑は削ってよい飾り」。第6段の will cut it first と呼応する。"},
    {"chunks": [("接","Nevertheless,","それにもかかわらず"),("S","a different view","異なる見方が"),
                ("V","has been gaining ground","支持を広げてきている"),
                ("M","(among researchers and planners):","研究者や都市計画家の間で"),
                ("S","the green corners of a city","（すなわち）都市の緑の一角は"),
                ("V","may be doing","しているのかもしれない"),("O","far more serious work","はるかに重大な仕事を"),
                ("M","(than we give them credit for).","私たちが認めているよりも")],
     "note":"▶ <b>R1｜逆接 Nevertheless の直後が主張</b>（＝空所A）。コロン(:)以下＝a different view の中身〔<b>R8</b>〕。give A credit for B＝「AにBの功績を認める」。"},
  ]},
 {"head": "第2段 — 譲歩：都市の利点は本物だ",
  "sentences": [
    {"chunks": [("S","The advantages of city life","都市生活の利点は"),("V","are","である"),("C","real.","本物")],
     "note":"▶ 譲歩の開始＝都市の利点を<b>本物</b>と認める〔<b>R14</b>の「譲歩」側〕。問7①「利点は見せかけ」はこの一文で×。"},
    {"chunks": [("S","Cities","都市は"),("V","concentrate","一か所に集め"),("O","jobs, schools, and ideas;","仕事・学校・発想を"),
                ("S","millions of people","何百万もの人々が"),("V","can live, meet, and trade","暮らし、出会い、取引でき"),
                ("M","(within a small area),","狭い地域の中で"),
                ("接","and","そして"),("S","culture","文化が"),("V","thrives","花開く"),
                ("M","(where strangers gather).","見知らぬ者同士が集まる場所で")],
     "note":"▶ セミコロン(;)と and で三つの文を並列。where …＝場所の副詞節「〜する場所で」。"},
    {"chunks": [("S","It is precisely this density","まさにこの密度こそが"),("V","that makes","〜にしている"),
                ("O","urban life","都市生活を"),("C","efficient,","効率的に"),
                ("接","and","そして"),("S","density","密度は"),("V","leaves","残さない"),
                ("O","little room","ほとんど余地を"),("M","(for open land).","空き地のための")],
     "note":"▶ <b>It is X that …＝強調構文</b>「まさにXこそが…」。make O C。leave little room for A＝「Aの余地をほとんど残さない」。"},
    {"chunks": [("M","(Seen this way),","このように見れば"),("S","the shortage of nature","自然の不足は"),
                ("V","can look like","〜のように見えうる"),
                ("C","a fair price &lt;for everything (that) a city offers&gt;.","都市が与えてくれるすべてのものへの妥当な対価")],
     "note":"▶ Seen this way＝受動の分詞構文（＝If it is seen this way）。everything (that) a city offers＝関係詞省略〔<b>R11</b>〕。譲歩の締め＝「自然の不足は仕方ない」に一度乗ってみせる。"},
  ]},
 {"head": "第3段 — 主張の転換＋理由①：緑は人を支える（Still）",
  "sentences": [
    {"chunks": [("接","Still,","それでも"),("S","the greenery &lt;that survives among the buildings&gt;","建物の間に生き残っている緑は"),
                ("V","is","である"),("C","not mere ornament.","単なる飾りではない")],
     "note":"▶ <b>R1｜Still＝逆接でここが主張転換点</b>（＝空所B）。not mere …＝「単なる〜ではない」（本当の働きがこの後に続く）。that survives …＝関係代名詞〔<b>R11</b>〕。"},
    {"chunks": [("S","Research","研究は"),("V","suggests","示唆する"),
                ("O","[that time &lt;spent in or near green space&gt; helps the mind recover its capacity for attention, &lt;which city noise and crowds constantly wear down&gt;].","緑地の中やその近くで過ごされる時間は、都市の騒音と人混みが絶えずすり減らしている注意力を、心が取り戻すのを助ける、と")],
     "note":"▶ help O do（原形不定詞）＝「Oが〜するのを助ける」。spent …＝過去分詞が time を修飾。, which …＝非制限用法で its capacity for attention を補足〔<b>R11</b>〕。固有名詞・数値を出さない「Research suggests」＝一般的知見の提示。"},
    {"chunks": [("S","People &lt;who see trees from a window, or cross a park on the way to work&gt;,","窓から木々が見えたり、通勤の途中で公園を横切ったりする人々は"),
                ("M","also","また"),("V","tend to report","報告する傾向がある"),("O","less stress.","より少ないストレスを")],
     "note":"▶ who …＝関係代名詞が see と cross の二つの動詞を取る〔<b>R11</b>〕。tend to do＝「〜する傾向がある」（断定しない研究知見の言い方）。＝問4の根拠。"},
    {"chunks": [("S","Nature,","自然は"),("M","in other words,","言い換えれば"),
                ("V","quietly maintains","静かに維持している"),
                ("O","the very residents &lt;who keep the city running&gt;.","都市を動かし続けているまさにその住民たちを")],
     "note":"▶ in other words＝言い換えの合図〔<b>R8</b>〕。keep O doing＝「Oを〜させ続ける」。the very＝「まさにその」。理由①のまとめ＝緑は<b>人</b>を支える。"},
  ]},
 {"head": "第4段 — 理由②：緑は都市そのものを支える（環境インフラ）",
  "sentences": [
    {"chunks": [("S","Nature","自然は"),("M","also","また"),("V","works on","働きかける"),("O","the city itself.","都市そのものに")],
     "note":"▶ work on A＝「Aに働きかける」。itself＝強調。対象が「人」（第3段）から「都市そのもの」へ＝理由②の主題提示。"},
    {"chunks": [("S","A single mature tree","一本の成木が"),("V","can cool","冷やすことができる"),
                ("O","the street beneath it,","その真下の通りを"),
                ("接","because","〜なので"),("S","its shade","その木陰が"),("V","blocks","さえぎり"),("O","the sun","日差しを"),
                ("接","while","一方で"),("S","the moisture &lt;released from its leaves&gt;","葉から放出される水分が"),
                ("V","lowers","下げる（から）"),("O","the temperature of the surrounding air.","まわりの空気の温度を")],
     "note":"▶ <b>R15｜無生物主語は副詞的に訳す</b>：「一本の成木の<b>おかげで</b>通りは涼しくなりうる」。because 節内も無生物主語（shade／moisture）の連続。released …＝過去分詞が moisture を修飾〔<b>R11</b>〕。＝<b>下線部(1)＝問2</b>。"},
    {"chunks": [("V","Multiply","増やしてみよ"),("O","that tree","その木を"),("M","(by thousands),","何千本にも"),
                ("接","and","そうすれば"),("S","a heat wave","熱波は"),("V","becomes","なる"),
                ("C","easier &lt;to survive&gt;.","生き延びやすいものに")],
     "note":"▶ <b>命令文 + and …</b>＝「〜せよ、そうすれば…」。easier to survive＝不定詞が easier を限定（survive の目的語が主語 a heat wave に上がった形）。"},
    {"chunks": [("M","(Below ground),","地面の下では"),("S","soil and roots","土と根が"),
                ("V","absorb","吸収する"),("O","heavy rain,","激しい雨を"),
                ("M","holding back water &lt;that would otherwise rush into the drains and flood the streets&gt;.","そうでなければ排水溝に殺到して通りを水浸しにするはずの水を、堰き止めながら")],
     "note":"▶ holding back …＝分詞構文（付帯状況）。<b>otherwise</b>＝「そうでなければ」（仮定を一語で含む→ would と呼応）。that …＝関係代名詞が rush と flood を並列〔<b>R11</b>〕。「完全になくす」とは言っていない＝問7⑥の言い過ぎ判定に使う。"},
    {"chunks": [("S","Concrete","コンクリートは"),("V","can do","できる"),("O","neither of these jobs:","これらの仕事のどちらも〜ない"),
                ("S","it","それは"),("V","stores","蓄え"),("O","heat","熱を"),
                ("接","and","そして"),("V","repels","はじく"),("O","water.","水を")],
     "note":"▶ neither of A＝「Aのどちらも〜ない」。<b>R5｜these jobs＝直前の二つ（通りを冷やす＋雨水を吸う）</b>。コロン(:)以下＝できない理由の言い換え〔<b>R8</b>〕。＝問7③の反駁根拠。"},
  ]},
 {"head": "第5段 — 批判と再反論：緑にかけた金は「別の形」で戻る",
  "sentences": [
    {"chunks": [("S","Critics","批判者たちは"),("V","reply","言い返す"),
                ("O","[that greenery is expensive]:","緑は金がかかる、と"),
                ("S","trees","（すなわち）木は"),("V","must be planted, watered, and pruned,","植えられ、水をやられ、剪定されねばならず"),
                ("接","and","そして"),("S","parks","公園は"),("V","demand","要求する"),("O","constant care.","絶え間ない手入れを")],
     "note":"▶ <b>R14｜反対意見の提示</b>。コロン(:)以下＝expensive の具体的中身〔<b>R8</b>〕。planted／watered／pruned＝受動の三並列。"},
    {"chunks": [("S","The objection","その反対意見は"),("V","deserves","値する"),("O","an answer,","答えに"),
                ("接","and","そして"),("S","it","それは"),("V","has","持っている"),("O","one.","その答えを")],
     "note":"▶ <b>R5｜one＝an answer</b> の言い換え。<b>R14｜批判をまともに受け止めてから→次文で再反論へ</b>。この往復が主張を強める。"},
    {"chunks": [("S","The money &lt;(that) a city spends on its green spaces&gt;","都市が緑地に使うお金は"),
                ("M","quietly","静かに"),("V","comes back","戻ってくる"),("M","(in other forms).","別の形で")],
     "note":"▶ <b>R14｜再反論の核</b>。(that) a city spends …＝関係詞省略（spends の目的語が money）〔<b>R11</b>〕。in other forms の中身は次文の三並列で確定〔<b>R5</b>〕。＝<b>下線部(2)＝問3</b>。"},
    {"chunks": [("S","Residents &lt;who stay healthier&gt;","より健康なままでいる住民は"),
                ("V","place","かける"),("O","a lighter burden","より軽い負担を"),("M","(on medical services);","医療サービスに"),
                ("S","shaded streets","木陰の通りは"),("V","reduce","減らし"),
                ("O","the electricity &lt;used for cooling&gt;;","冷房に使われる電力を"),
                ("接","and","そして"),("S","ground &lt;that drinks the rain&gt;","雨を飲み込む地面は"),
                ("V","cuts","削る"),("O","the cost of flood damage.","水害の被害額を")],
     "note":"▶ セミコロン(;)の三並列＝「別の形」の具体（医療・冷房・治水）〔<b>R8</b>〕。<b>R15｜無生物主語の連続</b>：「木陰の通りの<b>おかげで</b>冷房の電力が減る」のように副詞的に訳すと自然。used／that drinks＝分詞・関係詞の後置修飾〔<b>R11</b>〕。"},
    {"chunks": [("S","[What looks like spending]","支出に見えるものは"),("V","is,","である"),
                ("M","over time,","時がたてば"),("C","closer to saving.","節約に近いもの")],
     "note":"▶ 関係代名詞 what＝「〜するもの」（名詞節が主語）。spending ↔ saving の対比で<b>R14｜再反論</b>を締める。"},
  ]},
 {"head": "第6段 — 核心的主張：緑は飾りではなくインフラ",
  "sentences": [
    {"chunks": [("S","The conclusion &lt;(that) these facts point to&gt;","これらの事実が指し示す結論は"),
                ("V","is","である"),("C","simple but easily missed:","単純だが見落とされやすい"),
                ("S","urban nature","（すなわち）都市の自然は"),("V","is","である"),
                ("C","not decoration but a kind of infrastructure,","飾りではなく一種のインフラ"),
                ("-","as essential to a working city as roads, pipes, and power lines.","＝道路や水道管や送電線と同じくらい、機能する都市に不可欠なもの")],
     "note":"▶ <b>R3｜not A but B＝B（インフラ）こそ核心</b>。コロン(:)以下＝結論の中身〔<b>R8</b>〕。as … as ～＝同等比較。<b>R5｜these facts＝第3〜5段の働きと節約</b>。＝<b>下線部(3)＝問5</b>。"},
    {"chunks": [("S","We","私たちは"),("V","do not call","呼ばない"),("O","a water system","水道網を"),("C","a luxury","贅沢品と"),
                ("接","and","そして"),("V","ask","問わない"),("O","[whether the city can afford it];","都市にそれを持つ余裕があるかどうかを"),
                ("S","we","私たちは"),("V","ask","問う"),("O","[how to keep it working].","どうすれば機能させ続けられるかを")],
     "note":"▶ call O C＝「OをCと呼ぶ」。whether 節・how to do＝いずれも ask の目的語（名詞のカタマリ）。水道との類比＝「インフラには『贅沢か』ではなく『どう維持するか』を問う」。"},
    {"chunks": [("S","Trees and parks","木々や公園は"),("V","deserve","値する"),("O","the same question.","同じ問いに")],
     "note":"▶ <b>R5｜the same question＝「どう機能させ続けるか」という問い</b>（前文の後半）。緑を水道と同列に置く一文。"},
    {"chunks": [("S","A city &lt;that treats its greenery as an ornament&gt;","緑を飾りとして扱う都市は"),
                ("V","will cut","削るだろう"),("O","it","それを"),("M","first","真っ先に"),
                ("接","and","そして"),("V","pay for","代償を払う（だろう）"),("O","the loss","その損失の"),("M","later.","あとで")],
     "note":"▶ treat A as B（第1段の通念の言い方をそのまま使って反撃）。will が cut と pay の両方にかかる。<b>R6｜因果</b>：飾り扱い→真っ先に削る→後で代償。"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：問いは「何を必需とみなすか」",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),("V","means","意味しない"),
                ("O","[that every city should be turned back into a forest],","すべての都市を森に戻すべきだとは"),
                ("接","or","あるいは"),("O","[that a lawn matters more than a hospital].","芝生が病院より大事だとも")],
     "note":"▶ None of this means that …, or that …＝譲歩つき結論の型。turn A back into B の受動。matter＝動詞「重要である」。<b>R9注意</b>：問6④の「言い過ぎ」を切る根拠。"},
    {"chunks": [("S","The real question","本当の問いは"),("V","is","である"),("C","one of design:","設計の問い"),
                ("-","what does a city count as necessary?","＝都市は何を「必要」とみなすのか？")],
     "note":"▶ <b>R5｜one＝question</b>。コロン(:)以下＝その問いの中身〔<b>R8</b>〕。count A as B＝「AをBとみなす」。"},
    {"chunks": [("M","(As long as nature sits in the category of the merely pleasant),","自然が「単に心地よいもの」という区分に置かれている限り"),
                ("S","it","それは"),("V","will always lose","必ず負け続けるだろう"),
                ("M","(to the next urgent demand).","次の緊急の要求に")],
     "note":"▶ as long as ＳＶ＝「〜する限り」（条件の副詞節）。the merely pleasant＝the＋形容詞「〜なもの」。lose to A＝「Aに負ける」。"},
    {"chunks": [("V","Move","移してみよ"),("O","it","それを"),("M","(into the category of necessity),","「必需」の区分に"),
                ("接","and","そうすれば"),("S","the city &lt;(that) we build&gt;","私たちが造る都市は"),
                ("V","will support","支えるだろう"),("O","the people &lt;who live in it&gt;","そこに住む人々を"),
                ("M","&mdash; not despite being a city, but by being a better one.","都市であるにもかかわらず、ではなく、より良い都市であることによって")],
     "note":"▶ <b>命令文 + and …</b>（第4段と同型）。(that) we build＝関係詞省略〔<b>R11</b>〕。<b>R3｜not A but B</b>：by being a better one が核心。one＝city〔<b>R5</b>〕。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=4文/第2段=4文/第3段=4文/第4段=5文/第5段=5文/第6段=4文/第7段=4文)
SVOC_LOGIC = {
    (1, 4): "対比",                                   # s4 Nevertheless→反論(主張)
    (2, 1): "譲歩", (2, 4): "譲歩",                    # s1 利点は本物 / s4 妥当な対価に見える
    (3, 1): "対比", (3, 2): "具体例", (3, 3): "具体例", (3, 4): "主張",
    (4, 1): "主張", (4, 2): "因果", (4, 3): "因果", (4, 4): "追加", (4, 5): "対比",
    (5, 1): "譲歩", (5, 2): "譲歩", (5, 3): "主張", (5, 4): "具体例", (5, 5): "対比",
    (6, 1): "主張", (6, 2): "具体例", (6, 4): "因果",
    (7, 1): "譲歩", (7, 2): "主張", (7, 3): "因果", (7, 4): "主張",
}
