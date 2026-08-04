# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.06 — 単一ソース
テーマ: Why Diverse Teams Think Better (多様性はなぜチームを強くするのか) / MARCH・難関私大 (The Rules 2〜3 相当)
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "06",
    "level": "MARCH レベル",
    "level_sub": "難関私大 / The Rules 2〜3 相当",
    "theme_ja": "多様性はなぜチームを強くするのか",
    "theme_en": "Why Diverse Teams Think Better",
    "minutes": 18,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'Ask people to picture a strong team, and most will describe a group that gets along '
        'effortlessly &mdash; colleagues who share the same tastes, laugh at the same jokes, and '
        'rarely disagree. The belief runs deep: harmony produces results, while friction only '
        'slows things down. Given the choice, we usually hire people who remind us of ourselves. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, research on group performance keeps '
        'arriving at an awkward conclusion: the teams we find most comfortable are often not the '
        'teams that think best.'),
    (2, 'It is true that like-minded teams enjoy real advantages. Members who share a background '
        'understand one another quickly; meetings run smoothly, decisions come fast, and nobody '
        'feels like an outsider. Little needs explaining, because so much can be left unsaid. '
        'When the task is simple, such a group can be admirably efficient. Nobody who has worked '
        'in a warm, harmonious team would deny how pleasant it is.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span>, feeling comfortable and thinking well are '
        'not the same thing. <u>A smooth agreement may prove nothing more than that nobody in '
        'the room is questioning the assumptions everyone shares.<sup>(1)</sup></u> Members from '
        'different backgrounds cannot rely on shared habits of thought, so they are forced to '
        'explain their reasoning and to defend it. Because what is obvious to one member is '
        'puzzling to another, weaknesses that would otherwise stay hidden are dragged into the '
        'open before they can do harm. A clash of viewpoints, in short, erases the blind spots '
        'that a united group never even notices.'),
    (4, 'Research on group decision-making illustrates the pattern. Homogeneous teams tend to '
        'reach their answers quickly and to feel highly confident about them, yet those answers '
        'are often wrong. Diverse teams, by contrast, argue more, take longer, and report less '
        'confidence &mdash; but their conclusions turn out to be more accurate. The friction of '
        'disagreement, it appears, serves a purpose: it pushes the group to examine information '
        'carefully instead of settling on the first idea that feels familiar.'),
    (5, 'A minority voice matters even before it changes anyone\'s mind. When everyone agrees, '
        'individuals tend to relax and lean on the judgment of the group. But when a single '
        'member sees things differently, the majority can no longer take its own position for '
        'granted; people start checking their evidence and considering possibilities they had '
        'skipped. The dissenting opinion does not have to be right to be useful, because its '
        'value lies in what it makes everyone else do. None of this is enjoyable &mdash; and '
        'that is precisely the point.'),
    (6, 'All of this invites us to redefine what diversity means. <u>The real value lies not in '
        'the simple idea that a team should look varied, but in the harder claim that its '
        'members should think in genuinely different ways.<sup>(2)</sup></u> Diversity, properly '
        'understood, is a difference in mental toolboxes &mdash; in the questions people ask, '
        'the experience they draw on, and the errors they are trained to catch. <u>Seen in this '
        'light, the awkwardness of working with people unlike ourselves is not a price we pay '
        'for fairness; it is the very feature that makes a team intelligent.<sup>(3)</sup></u>'),
    (7, 'None of this means that difference alone guarantees success. A team whose members share '
        'no common goal and no respect for one another will simply fall apart, however varied '
        'its talents. Diversity works only when a group is mature enough to disagree without '
        'breaking. The question to ask about a team, then, is not whether it feels comfortable, '
        'but whether it makes its members smarter than they would be alone.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "Ask people to picture a strong team, and most will describe a group that gets along "
    "effortlessly colleagues who share the same tastes, laugh at the same jokes, and rarely "
    "disagree. The belief runs deep: harmony produces results, while friction only slows things "
    "down. Given the choice, we usually hire people who remind us of ourselves. Even so, "
    "research on group performance keeps arriving at an awkward conclusion: the teams we find "
    "most comfortable are often not the teams that think best. "
    "It is true that like-minded teams enjoy real advantages. Members who share a background "
    "understand one another quickly; meetings run smoothly, decisions come fast, and nobody "
    "feels like an outsider. Little needs explaining, because so much can be left unsaid. When "
    "the task is simple, such a group can be admirably efficient. Nobody who has worked in a "
    "warm, harmonious team would deny how pleasant it is. "
    "Nonetheless, feeling comfortable and thinking well are not the same thing. A smooth "
    "agreement may prove nothing more than that nobody in the room is questioning the "
    "assumptions everyone shares. Members from different backgrounds cannot rely on shared "
    "habits of thought, so they are forced to explain their reasoning and to defend it. Because "
    "what is obvious to one member is puzzling to another, weaknesses that would otherwise stay "
    "hidden are dragged into the open before they can do harm. A clash of viewpoints, in short, "
    "erases the blind spots that a united group never even notices. "
    "Research on group decision-making illustrates the pattern. Homogeneous teams tend to reach "
    "their answers quickly and to feel highly confident about them, yet those answers are often "
    "wrong. Diverse teams, by contrast, argue more, take longer, and report less confidence but "
    "their conclusions turn out to be more accurate. The friction of disagreement, it appears, "
    "serves a purpose: it pushes the group to examine information carefully instead of settling "
    "on the first idea that feels familiar. "
    "A minority voice matters even before it changes anyone's mind. When everyone agrees, "
    "individuals tend to relax and lean on the judgment of the group. But when a single member "
    "sees things differently, the majority can no longer take its own position for granted; "
    "people start checking their evidence and considering possibilities they had skipped. The "
    "dissenting opinion does not have to be right to be useful, because its value lies in what "
    "it makes everyone else do. None of this is enjoyable and that is precisely the point. "
    "All of this invites us to redefine what diversity means. The real value lies not in the "
    "simple idea that a team should look varied, but in the harder claim that its members "
    "should think in genuinely different ways. Diversity, properly understood, is a difference "
    "in mental toolboxes in the questions people ask, the experience they draw on, and the "
    "errors they are trained to catch. Seen in this light, the awkwardness of working with "
    "people unlike ourselves is not a price we pay for fairness; it is the very feature that "
    "makes a team intelligent. "
    "None of this means that difference alone guarantees success. A team whose members share no "
    "common goal and no respect for one another will simply fall apart, however varied its "
    "talents. Diversity works only when a group is mature enough to disagree without breaking. "
    "The question to ask about a team, then, is not whether it feels comfortable, but whether "
    "it makes its members smarter than they would be alone."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Therefore &nbsp; ② For example &nbsp; ③ Moreover &nbsp; ④ Even so",
         "【 B 】 &nbsp; ① Consequently &nbsp; ② For instance &nbsp; ③ Nonetheless &nbsp; ④ Similarly",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(2) <span class='en'>The real value lies not in the simple idea that a team "
             "should look varied, but in the harder claim that its members should think in "
             "genuinely different ways.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) について、「滑らかな合意（<span class='en'>a smooth agreement</span>）」が"
             "示しているにすぎないかもしれないこととは何か。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で紹介されている「集団の意思決定」に関する研究の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 多様なチームは議論が長引く分だけ結論の正確さでも劣り、同質なチームの方が速さと正確さの両方で勝っていた。",
         "② 同質なチームは速く自信を持って答えを出すが誤りやすく、多様なチームは時間はかかるものの、結論はより正確だった。",
         "③ 同質なチームは議論を重ねるほど自信を失っていき、最終的には結論そのものを出せなくなることが多かった。",
         "④ 多様なチームは最初に浮かんだ案をためらわず採用することで、決定の速さと結論の正確さを同時に達成していた。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(3) <span class='en'>it is the very feature that makes a team intelligent"
             "</span> について、多様性がチームを「賢く」する働きとはどのようなものか。本文全体をふまえ、"
             "二つ挙げて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 多様性の価値は見た目の違いではなく思考の仕方の違いにあり、そこで生じる居心地の悪さは代償ではなく、チームを賢くする機能そのものである。",
         "② 同質なチームは速く快適に決定できるのだから、課題の種類にかかわらず、チームは気の合う似た者同士で組むのが最も合理的である。",
         "③ 多様なチームは議論に時間がかかりすぎるため、成果を急ぐ場面では、意見の対立を避けて滑らかな合意を優先するべきである。",
         "④ メンバーの違いさえ確保しておけばチームは自然に賢くなるので、共通の目的や互いへの敬意はなくても成果には影響しない。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 同質なチームには、会議が滑らかに進み決定が速いといった利点は何一つ存在しない。",
         "② 反対意見がチームの役に立つのは、その意見そのものが正しい場合に限られる。",
         "③ 背景の異なるメンバーは共有された思考の習慣に頼れず、自分の推論を説明し擁護せざるを得なくなる。",
         "④ 全員の意見が一致していると、個人は気を緩めて集団の判断に寄りかかりがちになる。",
         "⑤ 筆者は、メンバーに違いさえあればチームの成功は保証される、と述べている。",
         "⑥ チームについて問うべきは、快適かどうかではなく、メンバーを一人のときより賢くするかどうかである。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ④ Even so　　B ＝ ③ Nonetheless",
     "exp": "A：直前は「私たちは自分に似た人を選ぶ」＝通念どおりの行動。直後は「最も快適なチーム≠"
            "最もよく考えるチーム」という研究の厄介な結論＝通念への反論。前後がぶつかる → <b>逆接</b>の "
            "Even so（それでもなお）。Therefore（因果）・For example（例示）・Moreover（追加）は不可。<br>"
            "B：第2段「確かに同質チームは快適で速い（＝譲歩）」に対し、第3段は「だが快適さと賢さは別物」"
            "と主張へ<b>転換</b>する。逆接 → Nonetheless。Consequently（因果）・For instance（例示）・"
            "Similarly（類比）は流れに合わない。 〔<b>解法ルール R7</b>／<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "②",
     "exp": "第4段「Homogeneous teams tend to reach their answers quickly and to feel highly "
            "confident …, yet those answers are often wrong. Diverse teams … argue more, take "
            "longer, and report less confidence — but their conclusions turn out to be more "
            "accurate」＝同質チームは速く自信満々だが誤りやすく、多様チームは遅いが正確。①は逆。"
            "③は本文にない（自信を失い結論を出せなくなる、とは述べていない）。④は逆（本文は「最初に"
            "浮かんだ案に落ち着くのを防ぐ」のが多様チーム）。 〔<b>解法ルール R9</b>／<b>読解ルール R4</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "①",
     "exp": "第6段の定義し直し「a difference in mental toolboxes（見た目ではなく思考の道具箱の違い）」"
            "〔<b>読解ルール R20</b>〕＋下線部(3)「not a price … but the very feature（代償ではなく機能）」"
            "〔<b>読解ルール R3</b>〕と一致。②は「課題の種類にかかわらず」が<b>言い過ぎ</b>（本文は"
            "「課題が単純なら効率的」と限定）。③は本文と逆（滑らかな合意こそ危険信号）。④は第7段"
            "「共通の目的も敬意もなければ崩壊する」に反する。 〔<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "③・④・⑥",
     "exp": "①×：第2段「It is true that like-minded teams enjoy real advantages」＝利点は認めて"
            "いる。「何一つ存在しない」は<b>言い過ぎ</b>。②×：第5段「The dissenting opinion does not "
            "have to be right to be useful」＝正しくなくても役に立つ、に反する。⑤×：第7段「None of "
            "this means that difference alone guarantees success」で明確に否定。 "
            "〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(2)和訳",
     "model": "真の価値は、チームは見た目が多様であるべきだという単純な考えの中にあるのではなく、"
              "メンバーが真に異なる仕方で考えるべきだという、より困難な主張の中にあるのだ。",
     "points": "▶<b>採点要素</b>：①<b>not in A, but in B</b>＝「Aの中にではなくBの中に」の対比を訳出／"
               "②<b>the idea that SV／the claim that SV</b>＝<b>同格のthat</b>「〜という考え／〜という主張」"
               "を正しく処理（関係代名詞と混同しない）／③look varied＝「見た目が多様である」・think in "
               "genuinely different ways＝「真に異なる仕方で考える」。 〔<b>構文ルール R21</b>／"
               "<b>読解ルール R3</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "会議が滑らかに合意に達しても、それは、その場の誰一人として、全員が共有している前提を"
              "疑って点検していない、ということを示しているだけかもしれないということ。つまり合意の"
              "心地よさは、考えの正しさを何ら保証しない。",
     "points": "▶<b>採点要素</b>：①nothing more than that …＝「〜ということ以上の何も（証明しない）」の"
               "限定を反映／②「誰も疑っていない」の対象＝<b>全員が共有する前提（assumptions）</b>である"
               "ことを明示／③直前の主張「心地よく感じること≠よく考えること」（第3段第1文）と結びつけて"
               "説明。 〔<b>解法ルール R8</b>／<b>読解ルール R1</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①背景の異なるメンバーどうしは共有された思考の習慣に頼れないため、互いに推論の説明と"
              "擁護を迫られ、隠れたままなら害をなしたはずの弱点や盲点が、表に出て消される働き。"
              "②異なる意見を持つメンバーが一人いるだけで、多数派は自分の立場を当然視できなくなり、"
              "根拠を点検し、見落としていた可能性を検討し始める働き。",
     "points": "▶<b>採点要素</b>：本文全体から「賢くする」働きを二つ取り出す。①<b>視点の衝突→盲点の消去</b>"
               "（第3〜4段：explain and defend / blind spots erased）／②<b>少数派の存在→根拠の再点検</b>"
               "（第5段：take … for granted できなくなる→ checking their evidence）。各5点。 "
               "〔<b>読解ルール R6</b>：因果で「働き」を追う／<b>解法ルール R8</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（Even so→研究の反論）・空所B（Nonetheless→主張転換）、第4段 yet / but、第5段 But。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that like-minded teams enjoy real advantages」→ 第3段 Nonetheless で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "下線部(2) not in the simple idea … but in the harder claim、下線部(3) not a price … ; the very feature、第7段 not whether … but whether …。"),
        ("R4", "抽象 → 具体（for example / In one … research）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段の意思決定研究は「快適さ≠賢さ」（第3段）という抽象の具体化。問4。"),
        ("R6", "因果（because / so / push … to / lead to）で理由と結論をつなぐ", "★★",
         "第3段 so they are forced … / Because what is obvious …、第4段 it pushes the group to …、第5段 because its value lies in …。"),
        ("R20", "★NEW 筆者がキーワードを定義し直したら、その新しい定義が文章の核心", "★★★",
         "第6段 redefine what diversity means：多様性＝見た目ではなく「思考の道具箱の違い」と定義し直す。ここが本文の核心＝問6。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。コロン(:)・nothing more than・not A but B の言い換えを利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。①の「何一つ存在しない」、②の「課題の種類にかかわらず」などは典型的な引っかけ。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "the blind spots &lt;that a united group never even notices&gt;、a team &lt;whose members share …&gt;、possibilities &lt;(that) they had skipped&gt; 型。"),
        ("R21", "★NEW 同格のthat（the idea that SV）＝「SVという考え」——関係代名詞のthatと区別する", "★★★",
         "下線部(2)＝問2 the simple idea that a team should look varied ／ the harder claim that its members should think …。that の後ろが完全な文なら同格、欠けていれば関係代名詞。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「気の合う似た者同士のチームが一番うまくいく（調和＝成果）」を提示。→ <b>Even so（R1）</b>："
             "研究は「最も快適なチーム≠最もよく考えるチーム」という厄介な結論に。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かに同質チームは速くて快適——会議は滑らか・決定は速い。"
             "ただし「課題が単純なら」という限定つき。＝通念の一部は認める。"},
    {"arrow": "◀ Nonetheless 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "快適さと賢さは別物。滑らかな合意＝<b>誰も前提を疑っていないだけ</b>かも（下線部(1)）。"
             "理由①：背景が違えば説明・擁護を迫られ、<b>視点の衝突が盲点を消す（R6因果）</b>。"},
    {"arrow": "↓　理由①の具体化（R4）"},
    {"role": "理由①", "para": "¶4", "kind": "reason",
     "text": "研究の知見：同質チームは<b>速く自信満々だが誤りやすい</b>／多様チームは遅く自信なげだが"
             "<b>結論は正確</b>。対立の摩擦が、丁寧な情報の検討を強いる。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "<b>少数派の存在自体の効果</b>：一人違う意見があるだけで、多数派は立場を当然視できず、"
             "根拠の点検を始める。反対意見は正しくなくても有用。楽ではない——それこそが核心。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "多様性の<b>定義し直し（R20）</b>：見た目の違いではなく<b>「思考の道具箱の違い」</b>。"
             "居心地の悪さは公平さの代償ではなく<b>チームを賢くする機能（R3）</b>（下線部(2)(3)）。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：違いだけでは成功は保証されない（共通の目的＋互いへの敬意が前提）。"
             "問うべきは「心地よいか」ではなく<b>「メンバーを賢くするか」（R3）</b>。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 二つのチーム像 — 快適さと賢さは別物",
     "caption": "同質チームは<b>速く快適で自信満々</b>だが、誰も前提を疑わないため誤りやすい。"
                "多様チームは議論が長く自信も控えめだが、<b>盲点が表に出て消え、結論は正確</b>になる。",
     "para": "→ 第2〜4段"},
    {"id": "fig2", "title": "図2 ｜ 多様性がチームを賢くする二つの働き",
     "caption": "働きは二つ。①<b>視点の衝突→「当たり前」を疑わせ、盲点を消す</b>（第3〜4段）、"
                "②<b>少数派の声→多数派に根拠の点検を始めさせる</b>（第5段）。問5はこの二つを答える。",
     "para": "→ 第3〜5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 居心地の悪さは「代償」ではなく「機能」",
     "caption": "筆者は多様性を<b>「思考の道具箱の違い」と定義し直す（R20）</b>。そこで生じる居心地の"
                "悪さは、公平さのために払うコストではなく、<b>チームを賢くするまさにその機能</b>。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "強いチームを思い描いてみてほしいと人々に頼めば、たいていの人は、苦もなく仲良くやれる集団——同じ趣味を"
        "持ち、同じ冗談に笑い、めったに意見が対立しない同僚たち——を描写するだろう。この思い込みは根深い。すな"
        "わち、調和は成果を生み、摩擦は物事を遅らせるだけだ、と。選べるなら、私たちはたいてい、自分自身を思い"
        "出させてくれる人を採用する。<b>それでもなお</b>、集団の成果に関する研究は、ある厄介な結論にたどり着き"
        "続けている。すなわち、私たちが最も心地よく感じるチームは、最もよく考えるチームではないことが多いのだ。"),
    (2, "確かに、気の合う者同士のチームには本物の利点がある。背景を共有するメンバーは互いをすばやく理解する。"
        "会議は滑らかに進み、決定は速く下り、誰もよそ者のようには感じない。非常に多くのことを言わずに済ませら"
        "れるので、説明はほとんど要らない。課題が単純であれば、そのような集団は見事なほど効率的でありうる。温"
        "かく和気あいあいとしたチームで働いたことのある人なら、それがどれほど心地よいかを否定しはしないだろう。"),
    (3, "<b>それにもかかわらず</b>、心地よく感じることと、よく考えることは同じではない。<b>滑らかな合意は、そ"
        "の場の誰一人として、全員が共有している前提を疑っていない、ということ以上の何も証明していないのかもし"
        "れない。</b>異なる背景から来たメンバーは、共有された思考の習慣に頼ることができないため、自分の推論を"
        "説明し、擁護することを迫られる。あるメンバーにとって自明のことが、別のメンバーには不可解であるからこ"
        "そ、そうでなければ隠れたままだったはずの弱点が、害をなす前に表へと引きずり出される。要するに、視点の"
        "衝突は、一枚岩の集団なら気づきさえしない盲点を消し去るのである。"),
    (4, "集団の意思決定に関する研究が、この型を例証している。同質なチームは、すばやく答えに達し、その答えに大"
        "きな自信を抱く傾向があるが、その答えはしばしば誤っている。対照的に、多様なチームはより多く議論し、よ"
        "り時間をかけ、自信のほども控えめだと報告する——だが、その結論はより正確であることが判明する。意見対立"
        "の摩擦は、どうやら一つの目的を果たしているらしい。すなわちそれは、馴染みに感じられる最初の案に落ち着"
        "いてしまうのではなく、情報を注意深く検討するよう集団に迫るのだ。"),
    (5, "少数派の声は、誰かの考えを変えるより前から、すでに重要である。全員の意見が一致していると、個人は気を"
        "緩め、集団の判断に寄りかかりがちになる。しかし、たった一人のメンバーが物事を違ったふうに見ているだけ"
        "で、多数派はもはや自分自身の立場を当然のものとは見なせなくなる。人々は自分の根拠を点検し、飛ばしてい"
        "た可能性を検討し始めるのだ。その反対意見は、役に立つために正しくある必要はない。その価値は、それが他"
        "の全員にさせることの中にあるからだ。このどれ一つとして楽しいものではない——そして、それこそがまさに核"
        "心なのである。"),
    (6, "以上のすべては、多様性が意味するものを定義し直すよう私たちを促す。<b>真の価値は、チームは見た目が多様"
        "であるべきだという単純な考えの中にあるのではなく、メンバーが真に異なる仕方で考えるべきだという、より"
        "困難な主張の中にあるのだ。</b>正しく理解するなら、多様性とは思考の道具箱の違い——すなわち、人が発する"
        "問い、頼りにする経験、見つけるよう訓練されてきた誤りの違い——である。<b>この光の下で見れば、自分と似て"
        "いない人々と働くことの居心地の悪さは、公平さのために私たちが払う代償なのではない。それこそが、チーム"
        "を賢くするまさにその機能なのだ。</b>"),
    (7, "とはいえ以上のことは、違いさえあれば成功が保証される、という意味ではない。メンバーが共通の目的も互い"
        "への敬意も共有しないチームは、その才能がどれほど多様でも、ただ崩壊するだけだろう。多様性が機能するの"
        "は、壊れることなく意見をぶつけ合えるだけの成熟が集団にあるときだけである。とすると、チームについて問"
        "うべき問いは、そのチームが心地よく感じられるかどうかではなく、メンバーを一人でいるときよりも賢くして"
        "くれるかどうか、なのである。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("get along", "仲良くやっていく"),
    ("effortlessly", "苦もなく、楽々と"),
    ("run deep", "（信念・感情が）根深い"),
    ("friction", "摩擦、あつれき"),
    ("remind A of B", "AにBを思い出させる"),
    ("awkward", "厄介な、気まずい"),
    ("like-minded", "気の合う、考え方の似た"),
    ("outsider", "よそ者、部外者"),
    ("leave ~ unsaid", "〜を言わずにおく"),
    ("admirably", "見事なほど、立派に"),
    ("assumption", "前提、思い込み"),
    ("rely on ~", "〜に頼る"),
    ("reasoning", "推論、論拠"),
    ("drag ~ into the open", "〜を表に引きずり出す"),
    ("blind spot", "盲点"),
    ("homogeneous", "同質的な、均質な"),
    ("settle on ~", "〜に（安易に）決める、落ち着く"),
    ("take A for granted", "Aを当然のことと思う"),
    ("dissenting", "反対意見の、異議を唱える"),
    ("redefine", "定義し直す"),
    ("draw on ~", "〜を頼りにする、活用する"),
    ("fall apart", "崩壊する、ばらばらになる"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 問題提起：似た者同士＝最強という通念と、その反転",
  "sentences": [
    {"chunks": [("V","Ask","頼んでみよ"),("O","people","人々に"),
                ("C","to picture a strong team,","強いチームを思い描くように"),
                ("接","and","そうすれば"),("S","most","たいていの人は"),("V","will describe","描写するだろう"),
                ("O","a group &lt;that gets along effortlessly&gt;","苦もなく仲良くやれる集団を"),
                ("-","&mdash; colleagues &lt;who share the same tastes, laugh at the same jokes, and rarely disagree&gt;.","——同じ趣味を持ち、同じ冗談に笑い、めったに対立しない同僚たち")],
     "note":"▶ <b>命令文 + and …</b>＝「〜せよ、そうすれば…」。ask O to do。colleagues 以下は a group の<b>同格</b>（言い換え）。who 節内は share／laugh／disagree の三つの動詞が並列。〔<b>R11</b>〕"},
    {"chunks": [("S","The belief","その思い込みは"),("V","runs","である"),("C","deep:","根深い"),
                ("S","harmony","（すなわち）調和は"),("V","produces","生む"),("O","results,","成果を"),
                ("M","(while friction only slows things down).","一方、摩擦は物事を遅らせるだけだ（と）")],
     "note":"▶ run deep＝「根深い」（run＋形容詞）。<b>コロン(:)＝直前の belief の中身</b>の言い換え〔<b>R8</b>〕。while＝対比「一方で」。"},
    {"chunks": [("M","(Given the choice),","選べるなら"),("S","we","私たちは"),("M","usually","たいてい"),
                ("V","hire","採用する"),("O","people &lt;who remind us of ourselves&gt;.","自分自身を思い出させてくれる人々を")],
     "note":"▶ Given ~＝「〜が与えられれば・〜があるなら」（分詞構文由来）。<b>remind A of B</b>＝「AにBを思い出させる」。〔<b>R11</b>〕"},
    {"chunks": [("接","Even so,","それでもなお"),("S","research on group performance","集団の成果に関する研究は"),
                ("V","keeps arriving at","たどり着き続けている"),("O","an awkward conclusion:","ある厄介な結論に"),
                ("S","the teams &lt;(that) we find most comfortable&gt;","（すなわち）私たちが最も心地よいと感じるチームは"),
                ("V","are","である"),("C","often not the teams &lt;that think best&gt;.","最もよく考えるチームでは、しばしばない")],
     "note":"▶ <b>R1｜逆接 Even so の直後が主張</b>（＝空所A）。コロン以下＝conclusion の中身。we find (the teams) most comfortable＝find O C の関係詞化（関係詞省略）。〔<b>R11</b>〕"},
  ]},
 {"head": "第2段 — 譲歩：確かに同質チームは快適で速い（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当だ"),
                ("-","[that like-minded teams enjoy real advantages].","気の合う者同士のチームに本物の利点がある、ということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。形式主語 It＝真主語 that 節。後の逆接（第3段 Nonetheless）で反転する前振り。"},
    {"chunks": [("S","Members &lt;who share a background&gt;","背景を共有するメンバーは"),("V","understand","理解する"),
                ("O","one another","互いを"),("M","quickly;","すばやく"),
                ("S","meetings","会議は"),("V","run","進む"),("M","smoothly,","滑らかに"),
                ("S","decisions","決定は"),("V","come","下る"),("M","fast,","速く"),
                ("接","and","そして"),("S","nobody","誰も〜ない"),("V","feels like","〜のようには感じない"),("C","an outsider.","よそ者だと")],
     "note":"▶ セミコロン＋短文三つの並列で「同質チームの快適さ」を畳みかける。feel like＋名詞。〔<b>R11</b>〕"},
    {"chunks": [("S","Little","ほとんど何も〜ない"),("V","needs","必要としない"),("O","explaining,","説明されることを"),
                ("M","(because so much can be left unsaid).","非常に多くを言わずに済ませられるので")],
     "note":"▶ <b>need doing</b>＝「〜される必要がある」。Little＝否定の主語「ほとんど〜ない」。because＝因果〔<b>R6</b>〕。leave ~ unsaid。"},
    {"chunks": [("M","(When the task is simple),","課題が単純なときは"),("S","such a group","そのような集団は"),
                ("V","can be","なりうる"),("C","admirably efficient.","見事なほど効率的に")],
     "note":"▶ when 節＝条件の副詞節。<b>「単純な課題なら」という限定</b>に注意——問6②「課題の種類にかかわらず」を切る根拠。"},
    {"chunks": [("S","Nobody &lt;who has worked in a warm, harmonious team&gt;","温かく和気あいあいとしたチームで働いたことのある人は誰も〜ない"),
                ("V","would deny","否定しないだろう"),("O","[how pleasant it is].","それがどれほど心地よいかを")],
     "note":"▶ 関係詞節が Nobody を修飾〔<b>R11</b>〕。how pleasant it is＝間接感嘆の名詞節。譲歩の駄目押し。"},
  ]},
 {"head": "第3段 — 主張の転換：快適さ≠賢さ（Nonetheless）＋理由①",
  "sentences": [
    {"chunks": [("接","Nonetheless,","それにもかかわらず"),
                ("S","feeling comfortable and thinking well","心地よく感じることと、よく考えることは"),
                ("V","are","である"),("C","not the same thing.","同じものではない")],
     "note":"▶ <b>R1｜逆接 Nonetheless でここが主張転換点</b>（＝空所B）。動名詞二つ（feeling / thinking）が主語。「快適さ≠賢さ」が本文の背骨。"},
    {"chunks": [("S","A smooth agreement","滑らかな合意は"),("V","may prove","証明しないかもしれない"),
                ("O","nothing more than [that nobody in the room is questioning the assumptions &lt;(that) everyone shares&gt;].","その場の誰一人、全員が共有する前提を疑っていない、ということ以上の何も")],
     "note":"▶ <b>nothing more than ~</b>＝「〜以上の何ものでもない」。that 節＝prove の目的語（名詞節）。assumptions の後は関係詞省略〔<b>R11</b>〕。＝<b>下線部(1)＝問3</b>。"},
    {"chunks": [("S","Members &lt;from different backgrounds&gt;","異なる背景出身のメンバーは"),
                ("V","cannot rely on","頼ることができない"),("O","shared habits of thought,","共有された思考の習慣に"),
                ("接","so","だから"),("S","they","彼らは"),("V","are forced","強いられる"),
                ("C","to explain their reasoning and to defend it.","自分の推論を説明し、それを擁護するように")],
     "note":"▶ <b>R6｜so＝因果</b>。force O to do の受動態。to explain と to defend の並列。＝問7③の根拠。"},
    {"chunks": [("M","(Because what is obvious to one member is puzzling to another),","あるメンバーにとって自明のことが、別のメンバーには不可解なので"),
                ("S","weaknesses &lt;that would otherwise stay hidden&gt;","そうでなければ隠れたままだったはずの弱点が"),
                ("V","are dragged","引きずり出される"),("M","(into the open)","表へと"),
                ("M","(before they can do harm).","害をなす前に")],
     "note":"▶ <b>R6｜Because＝因果</b>。Because 節内の what＝関係代名詞「〜こと」。<b>otherwise</b>＝「そうでなければ」（仮定を含む would）。〔<b>R11</b>〕"},
    {"chunks": [("S","A clash of viewpoints,","視点の衝突は"),("M","in short,","要するに"),
                ("V","erases","消し去る"),
                ("O","the blind spots &lt;that a united group never even notices&gt;.","一枚岩の集団なら気づきさえしない盲点を")],
     "note":"▶ in short＝要約の挿入＝理由①のまとめ。that＝関係代名詞（notices の目的語）〔<b>R11</b>〕。"},
  ]},
 {"head": "第4段 — 理由①の具体化：研究の知見（抽象→具体）",
  "sentences": [
    {"chunks": [("S","Research on group decision-making","集団の意思決定に関する研究が"),
                ("V","illustrates","例証している"),("O","the pattern.","この型を")],
     "note":"▶ <b>R4｜抽象（第3段の主張）→具体（研究の知見）</b>への合図。illustrate＝「実例で示す」。"},
    {"chunks": [("S","Homogeneous teams","同質なチームは"),("V","tend","傾向がある"),
                ("C","to reach their answers quickly and to feel highly confident about them,","すばやく答えに達し、それに大きな自信を抱く"),
                ("接","yet","だが"),("S","those answers","その答えは"),("V","are","である"),("C","often wrong.","しばしば誤り")],
     "note":"▶ tend to do。<b>R1｜yet＝逆接</b>：「速さ・自信」と「誤り」の対比。＝<b>問4の根拠（前半）</b>。"},
    {"chunks": [("S","Diverse teams,","多様なチームは"),("M","by contrast,","対照的に"),
                ("V","argue","議論する"),("M","more,","より多く"),("V","take","かける"),("M","longer,","より長く（時間を）"),
                ("接","and","そして"),("V","report","報告する"),("O","less confidence","より低い自信を"),
                ("接","&mdash; but","——だが"),("S","their conclusions","その結論は"),
                ("V","turn out to be","判明する"),("C","more accurate.","より正確だと")],
     "note":"▶ by contrast＝対比の目印。<b>turn out to be C</b>＝「Cだと判明する」。＝<b>問4の根拠（後半）</b>。"},
    {"chunks": [("S","The friction of disagreement,","意見対立の摩擦は"),("M","it appears,","どうやら"),
                ("V","serves","果たしている"),("O","a purpose:","一つの目的を"),
                ("S","it","それは"),("V","pushes","促す"),("O","the group","集団を"),
                ("C","to examine information carefully","情報を注意深く検討するように"),
                ("M","(instead of settling on the first idea &lt;that feels familiar&gt;).","馴染みに感じられる最初の案に落ち着いてしまう代わりに")],
     "note":"▶ it appears＝挿入。コロン＝purpose の中身の言い換え〔<b>R8</b>〕。<b>push O to do</b>＝因果〔<b>R6</b>〕。instead of doing。〔<b>R11</b>〕"},
  ]},
 {"head": "第5段 — 理由②：少数派の存在それ自体の効果",
  "sentences": [
    {"chunks": [("S","A minority voice","少数派の声は"),("V","matters","重要である"),
                ("M","(even before it changes anyone's mind).","誰かの考えを変えるより前からすでに")],
     "note":"▶ <b>matter</b>（自動詞）＝「重要だ」。理由②の主題提示：意見の中身より「存在」の効果。"},
    {"chunks": [("M","(When everyone agrees),","全員の意見が一致していると"),("S","individuals","個人は"),
                ("V","tend","傾向がある"),
                ("C","to relax and lean on the judgment of the group.","気を緩め、集団の判断に寄りかかる")],
     "note":"▶ lean on ~＝「〜に寄りかかる」。＝<b>問7④の根拠</b>。"},
    {"chunks": [("接","But","だが"),("M","(when a single member sees things differently),","たった一人のメンバーが物事を違ったふうに見ると"),
                ("S","the majority","多数派は"),("V","can no longer take","もはや〜とは見なせない"),
                ("O","its own position","自分自身の立場を"),("M","for granted;","当然のものとは"),
                ("S","people","人々は"),("V","start","始める"),
                ("O","checking their evidence and considering possibilities &lt;(that) they had skipped&gt;.","自分の根拠を点検し、飛ばしていた可能性を検討することを")],
     "note":"▶ <b>R1｜But＝逆接</b>。<b>take A for granted</b>＝「Aを当然と思う」。start doing。had skipped＝過去完了（点検より前に飛ばしていた）。関係詞省略〔<b>R11</b>〕。"},
    {"chunks": [("S","The dissenting opinion","その反対意見は"),("V","does not have to be","である必要はない"),
                ("C","right","正しく"),("M","to be useful,","役に立つためには"),
                ("M","(because its value lies in [what it makes everyone else do]).","その価値は、それが他の全員にさせることの中にあるので")],
     "note":"▶ not have to do＝「〜する必要はない」。because＝因果〔<b>R6</b>〕。what it makes everyone else do＝関係代名詞 what＋<b>make O do</b>（使役）。＝<b>問7②を切る根拠</b>。"},
    {"chunks": [("S","None of this","このどれ一つとして"),("V","is","ではない"),("C","enjoyable","楽しいもの"),
                ("接","&mdash; and","——そして"),("S","that","それこそが"),("V","is","である"),
                ("C","precisely the point.","まさに核心")],
     "note":"▶ None of ~＝全否定「どれ一つ〜ない」。the point＝「眼目・狙い」。不快さは欠陥ではなく狙いどおりの働き——第6段「機能」への橋渡し。"},
  ]},
 {"head": "第6段 — 核心：多様性の定義し直し（同格のthat）",
  "sentences": [
    {"chunks": [("S","All of this","以上のすべては"),("V","invites","促す"),("O","us","私たちに"),
                ("C","to redefine [what diversity means].","多様性が意味するものを定義し直すように")],
     "note":"▶ <b>R20｜筆者がキーワード（diversity）を定義し直す宣言＝ここからが核心</b>。invite O to do。what 節＝名詞節（means の目的語のカタマリ）。"},
    {"chunks": [("S","The real value","真の価値は"),("V","lies","ある"),
                ("M","(not in the simple idea) [that a team should look varied],","チームは見た目が多様であるべきだ、という単純な考えの中に、ではなく"),
                ("M","(but in the harder claim) [that its members should think in genuinely different ways].","メンバーは真に異なる仕方で考えるべきだ、という、より困難な主張の中に")],
     "note":"▶ <b>R21｜同格の that</b>：the idea <b>that</b> SV／the claim <b>that</b> SV＝「SVという考え／主張」。that の後ろが<b>完全な文</b>なので関係代名詞ではない。<b>R3｜not A but B</b>＝Bが核心。lie in ~＝「〜の中にある」。＝<b>下線部(2)＝問2</b>。"},
    {"chunks": [("S","Diversity,","多様性とは"),("M","properly understood,","正しく理解すれば"),
                ("V","is","である"),("C","a difference in mental toolboxes","思考の道具箱の違い"),
                ("-","&mdash; in the questions &lt;people ask&gt;, the experience &lt;they draw on&gt;, and the errors &lt;they are trained to catch&gt;.","——すなわち、人が発する問い、頼りにする経験、見つけるよう訓練されてきた誤り（の違い）")],
     "note":"▶ <b>R20｜定義し直しの中身</b>＝「見た目」ではなく「思考の道具箱」。properly understood＝分詞構文（挿入）。ダッシュ以下は toolboxes の具体化（三つの並列・いずれも関係詞省略）〔<b>R11</b>〕。"},
    {"chunks": [("M","(Seen in this light),","この光の下で見れば"),
                ("S","the awkwardness &lt;of working with people unlike ourselves&gt;","自分と似ていない人々と働くことの居心地の悪さは"),
                ("V","is","である"),("C","not a price &lt;(that) we pay for fairness&gt;;","公平さのために私たちが払う代償では、ない"),
                ("S","it","それは"),("V","is","である"),
                ("C","the very feature &lt;that makes a team intelligent&gt;.","チームを賢くする、まさにその機能")],
     "note":"▶ Seen …＝受動の分詞構文。<b>R3｜not A（but）B の変形（not A; B）</b>：核心はB＝「機能（feature）」。the very ~＝「まさにその〜」。make O C（使役）。＝<b>下線部(3)＝問5</b>。〔<b>R11</b>〕"},
  ]},
 {"head": "第7段 — 譲歩つきの結論：問うべきは「快適か」ではなく「賢くなれるか」",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),("V","means","意味しない"),
                ("O","[that difference alone guarantees success].","違いだけで成功が保証される、とは")],
     "note":"▶ 譲歩つき結論の合図。alone＝「〜だけで」。<b>R9注意</b>：これが<b>問7⑤を切る根拠</b>。"},
    {"chunks": [("S","A team &lt;whose members share no common goal and no respect for one another&gt;","メンバーが共通の目的も互いへの敬意も共有しないチームは"),
                ("V","will simply fall apart,","ただ崩壊するだけだろう"),
                ("M","(however varied its talents).","その才能がどれほど多様でも")],
     "note":"▶ <b>whose</b>＝所有格の関係代名詞〔<b>R11</b>〕。<b>however 形容詞 (SV)</b>＝「どれほど〜でも」（譲歩・ここは be 動詞の省略）。fall apart＝「崩壊する」。"},
    {"chunks": [("S","Diversity","多様性は"),("V","works","機能する"),
                ("M","(only when a group is mature enough to disagree without breaking).","集団が、壊れずに意見をぶつけ合えるほど成熟しているときにだけ")],
     "note":"▶ only when ~＝「〜のときにだけ」。<b>enough to do</b>＝「〜できるほど十分に」。without doing＝「〜せずに」。"},
    {"chunks": [("S","The question &lt;to ask about a team&gt;,","チームについて問うべき問いは"),
                ("M","then,","つまるところ"),("V","is","である"),
                ("C","not [whether it feels comfortable], but [whether it makes its members smarter (than they would be alone)].","そのチームが心地よく感じられるかどうか、ではなく、メンバーを一人でいるときより賢くするかどうか")],
     "note":"▶ <b>R3｜not A but B</b>：核心はB。whether 節＝名詞節「〜かどうか」。make O C。than they would be alone＝仮定を含む比較（「一人でいるとしたら、そうであろうよりも」）。＝<b>問7⑥の根拠</b>。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=4文/第2段=5文/第3段=5文/第4段=4文/第5段=5文/第6段=4文/第7段=4文)
SVOC_LOGIC = {
    (1, 4): "対比",                                   # s4 Even so→研究の反論
    (2, 1): "譲歩", (2, 3): "因果", (2, 5): "譲歩",     # s1 It is true / s3 because / s5 駄目押し
    (3, 1): "対比", (3, 2): "主張", (3, 3): "因果", (3, 4): "因果", (3, 5): "主張",
    (4, 1): "具体例", (4, 2): "対比", (4, 3): "対比", (4, 4): "因果",
    (5, 1): "主張", (5, 2): "因果", (5, 3): "対比", (5, 4): "因果", (5, 5): "主張",
    (6, 1): "主張", (6, 2): "主張", (6, 3): "具体例", (6, 4): "主張",
    (7, 1): "譲歩", (7, 2): "因果", (7, 3): "譲歩", (7, 4): "主張",
}
