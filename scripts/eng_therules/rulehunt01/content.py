# -*- coding: utf-8 -*-
"""英語長文 ルール発見トレーニング No.01 (The Rules式・別冊ドリル) の単一ソース。

「読解問題」ではなく、文法・論理の目印を本文から**見つけるためだけ**の訓練。
6ターゲット: ①ディスコースマーカー ②因果構文 ③仮定法 ④受動態 ⑤分詞構文 ⑥助動詞will

ANNOT が解答キーの single source — 問題編のヒント個数・解答編の表・マーク本文は
すべてここから生成される(check.py が本文との突合と網羅性を機械検査する)。
文番号(s)は各長文の通し番号。t は本文中の**正確な**部分文字列。
ルール整理は関正生『The Rules』のアプローチに着想を得た当塾オリジナル(文言・番号は独自)。
"""

META = {
    "series": "英語長文 ルール発見トレーニング",
    "no": "No.01",
    "subtitle": "The Rules式・別冊ドリル ｜ 読む前に「見つける」練習",
    "level": "共通テスト〜日大・MARCH基礎",
    "time": "1周目: 時間無制限 ／ 2周目: 各10分",
    "note": "関正生『The Rules』のアプローチに着想を得たトリリオンAI塾オリジナルの整理です。",
}

# ------------------------------------------------------------------
# 6ターゲット(探すもの・目印・付ける印・合言葉)
# ------------------------------------------------------------------
TARGETS = [
    {"key": "marker", "no": "①", "name": "ディスコースマーカー", "color": "#2563eb",
     "what": "話の流れを切り替える標識語 (However / For example / Moreover / Indeed など)",
     "sign": "文頭・文中の副詞(句)や接続詞(yet など)。カンマを従えることが多い",
     "mark": "□で囲む", "cls": "mk",
     "slogan": "マーカーは道路標識 —— 見えたら一時停止。「逆接の後ろに主張」が最重要。",
     "series": "本編 R1(逆接)・R4(具体例)・R7(論理関係)とつながる"},
    {"key": "causal", "no": "②", "name": "因果構文", "color": "#dc2626",
     "what": "原因と結果をつなぐ動詞・接続詞・前置詞 (lead to / result in / result from / cause / because など)",
     "sign": "「原因 → 結果」型か「結果 ← 原因」型かで矢印の向きが逆になる",
     "mark": "下線を引き、矢印(→/←)を書き込む", "cls": "cz",
     "slogan": "因果は矢印が命 —— 動詞を見た瞬間に「どっちが原因か」を決めろ。",
     "series": "本編 R6(因果)とつながる"},
    {"key": "subj", "no": "③", "name": "仮定法", "color": "#7c3aed",
     "what": "「現実ではない妄想」の話 (If+過去形 / would・could・might+動詞の原形 / would have+過去分詞)",
     "sign": "if が無くても Without 〜 / 倒置 Had S 〜 が条件の代役をする(隠れ仮定法)",
     "mark": "波線を引く", "cls": "sj",
     "slogan": "would を見たら妄想モード —— 「現実はその逆」と1秒で気づけ。",
     "series": "ドリル専用ターゲット"},
    {"key": "passive", "no": "④", "name": "受動態", "color": "#059669",
     "what": "be動詞 + 過去分詞 「〜される」",
     "sign": "be と過去分詞の間に not / often / being などが割り込むことがある",
     "mark": "〔　〕で囲む", "cls": "ps",
     "slogan": "受動態は「する側を隠す」装置 —— by が無いのは、書かなくても分かる(or 言いたくない)から。",
     "series": "ドリル専用ターゲット"},
    {"key": "part", "no": "⑤", "name": "分詞構文", "color": "#ea580c",
     "what": "文頭の -ing／過去分詞 + カンマ、または「, -ing」で文に添えるカタマリ",
     "sign": "接続詞+S+V を圧縮した形。「〜して/〜しながら/そして〜」と骨格に添える",
     "mark": "〈　〉で囲む", "cls": "pc",
     "slogan": "カンマ挟みの -ing は接続詞の圧縮 —— 意味は「時・理由・付帯」のどれかに落ちる。",
     "series": "本編 R19(分詞構文)とつながる"},
    {"key": "will", "no": "⑥", "name": "助動詞 will", "color": "#b45309",
     "what": "「未来」ではない will —— 「(こういうものは)100%必ず〜する」という習性・法則の will",
     "sign": "主語が「人一般・モノの性質」のとき、will は予定でなく法則を表す",
     "mark": "◎で囲む", "cls": "wl",
     "slogan": "will の核心は「100%そうなる」 —— 未来はその一部にすぎない。",
     "series": "ドリル専用ターゲット"},
]

# ------------------------------------------------------------------
# 長文2題(原創・特徴高密度)
# ------------------------------------------------------------------
PASSAGES = [
    {"key": "p1", "label": "訓練 1", "hint": True,
     "title": "Why Handwriting Survives in a Digital Age",
     "jtitle": "デジタル時代に手書きが生き残る理由",
     "paras": [
        [
         {"n": 1, "en": "Most students today type faster than they write, and lecture halls are filled with the quiet sound of keyboards."},
         {"n": 2, "en": "Typing is quick, and typed notes are neat and easy to search, so notes pile up at amazing speed."},
         {"n": 3, "en": "However, speed is not the same thing as learning."},
         {"n": 4, "en": "In fact, several studies suggest that the students who type the most may remember the least."},
        ],
        [
         {"n": 5, "en": "When we write by hand, letters are formed slowly, one stroke at a time, and this slowness has hidden value."},
         {"n": 6, "en": "Because the pen cannot keep up with speech, writers are forced to choose only the most important ideas."},
         {"n": 7, "en": "This effort of choosing leads to deeper processing, and deeper processing results in stronger memory."},
         {"n": 8, "en": "For example, in one famous experiment, students who took notes by hand performed better on conceptual questions than those who typed everything they heard."},
         {"n": 9, "en": "Their advantage was not caused by better handwriting; it came from the extra thinking that handwriting demands."},
         {"n": 10, "en": "Moreover, the physical movement of the hand leaves its own trace, linking each word to a motion that the brain remembers."},
        ],
        [
         {"n": 11, "en": "If students typed every note and never wrote anything by hand, much of this slow, careful thinking would disappear."},
         {"n": 12, "en": "Without the friction of the pen, ideas would slide past us before they had a chance to sink in."},
         {"n": 13, "en": "This does not mean that computers should be thrown away."},
         {"n": 14, "en": "Typing is useful for long reports, and digital notes are easily shared and stored."},
         {"n": 15, "en": "Yet a student who writes key ideas by hand will usually hold on to them longer."},
         {"n": 16, "en": "Choosing the pen for the moments that matter, we can enjoy the best of both worlds."},
        ],
     ]},
    {"key": "p2", "label": "訓練 2", "hint": False,
     "title": "What Laughter Does for Us",
     "jtitle": "笑いは私たちに何をしてくれるか",
     "paras": [
        [
         {"n": 1, "en": "Laughter is often treated as a small break from serious life, yet its effects reach deep into the body."},
         {"n": 2, "en": "When we laugh, stress hormones drop, and chemicals that kill pain are released in the brain."},
         {"n": 3, "en": "As a result, a good laugh can relax muscles and calm the heart, leaving the body at ease for up to forty-five minutes."},
         {"n": 4, "en": "These changes are not caused by humor alone; they result from the physical act of laughing itself."},
        ],
        [
         {"n": 5, "en": "Laughter also works as social glue."},
         {"n": 6, "en": "In one study, strangers who watched a funny video together trusted each other more than pairs who watched a neutral one."},
         {"n": 7, "en": "Shared laughter brings about a sense of safety, and this feeling contributes to honest conversation."},
         {"n": 8, "en": "On the other hand, a team in which nobody laughs will slowly grow stiff and silent."},
         {"n": 9, "en": "Laughing together, people lower their guard without noticing it."},
         {"n": 10, "en": "Indeed, some researchers say that laughter came before language as a tool for building trust."},
        ],
        [
         {"n": 11, "en": "The value of laughter becomes clearest when we imagine its absence."},
         {"n": 12, "en": "If laughter were truly useless, evolution would have removed it long ago."},
         {"n": 13, "en": "Had our ancestors laughed less, human groups might have found it harder to hold together."},
         {"n": 14, "en": "Without laughter, meetings would feel longer, apologies would be harder, and friendships would cool more quickly."},
        ],
        [
         {"n": 15, "en": "None of this means that we should force ourselves to laugh all day."},
         {"n": 16, "en": "Yet the next time you hear laughter in a classroom or an office, remember that serious work is quietly being helped by it."},
         {"n": 17, "en": "A workplace where people can laugh freely will keep its members healthier, closer, and more creative."},
        ],
     ]},
]

# ------------------------------------------------------------------
# 解答キー(単一ソース) — t は本文の正確な部分文字列
# dual: 他ターゲットと二刀流の instance は note で明示(受動×因果 など)
# ------------------------------------------------------------------
ANNOT = {
 "p1": {
  "marker": [
    {"s": 3, "t": "However", "sub": "逆接", "note": "直後が筆者の主張「速さ≠学び」。本編R1そのもの。"},
    {"s": 4, "t": "In fact", "sub": "強調・追い打ち", "note": "前文の主張を研究で補強。「それどころか」の追い打ち。"},
    {"s": 8, "t": "For example", "sub": "具体例", "note": "⑦の抽象(選ぶ努力→深い処理→記憶)を実験で具体化。R4。"},
    {"s": 10, "t": "Moreover", "sub": "追加", "note": "手書きの利点をもう1つ積む「さらに」。"},
    {"s": 15, "t": "Yet", "sub": "逆接", "note": "譲歩(⑬⑭タイピングも有用)からの反転。逆接の後ろ=結論。"},
  ],
  "causal": [
    {"s": 2, "t": "so", "dir": "原因 → 結果", "note": "「速くて整理しやすい」→(だから)→「ノートがどんどん貯まる」。"},
    {"s": 6, "t": "Because", "dir": "原因 → 結果", "note": "接続詞型。「ペンは speech に追いつけない」が原因。"},
    {"s": 7, "t": "leads to", "dir": "原因 → 結果", "note": "V型・順方向。「選ぶ努力」→「深い処理」。"},
    {"s": 7, "t": "results in", "dir": "原因 → 結果", "note": "in は「結果の中へ」。「深い処理」→「強い記憶」。"},
    {"s": 9, "t": "was not caused by", "dir": "結果 ← 原因", "note": "受動で向きが反転。「利点」←「きれいな字(ではない!)」。受動態との二刀流。"},
    {"s": 9, "t": "came from", "dir": "結果 ← 原因", "note": "from は「原因から」。「利点」←「余分に考えること」。"},
  ],
  "subj": [
    {"s": 11, "t": "If students typed every note and never wrote anything by hand, much of this slow, careful thinking would disappear",
     "mk": "If + 過去形 / would + 原形", "note": "仮定法過去=現在の妄想。現実は「手書きもしている→思考は消えていない」。"},
    {"s": 12, "t": "Without the friction of the pen, ideas would slide past us",
     "mk": "Without 〜 = if 節の代役 / would + 原形", "note": "隠れ仮定法。Without = 「もし〜がなければ」。"},
  ],
  "passive": [
    {"s": 1, "t": "are filled", "note": "by 〜なし: 満たす側(キーボード音)は with で示され、文の主役は lecture halls。"},
    {"s": 5, "t": "are formed", "note": "書く人より「文字が形づくられる過程」にカメラを向けるための受動。"},
    {"s": 6, "t": "are forced", "note": "force する側=「ペンの遅さ」。直前の Because 節に書いてあるので by は不要。"},
    {"s": 9, "t": "was not caused by", "note": "因果構文との二刀流。not に注意 —— be と p.p. の間に割り込む。"},
    {"s": 13, "t": "should be thrown away", "note": "助動詞 + be + p.p.。「捨てられるべき(ではない)」。"},
    {"s": 14, "t": "are easily shared and stored", "note": "1つの are に p.p. が2つ(shared / stored)。easily が割り込み。"},
  ],
  "part": [
    {"s": 10, "t": "linking each word to a motion that the brain remembers", "kind": "文末型「, -ing」",
     "note": "「そして〜する」(結果)。leaves its own trace した結果、語と動きが結びつく。"},
    {"s": 16, "t": "Choosing the pen for the moments that matter", "kind": "文頭型「-ing, 」",
     "note": "「〜すれば」(条件寄り)。接続詞 If we choose の圧縮。"},
  ],
  "will": [
    {"s": 15, "t": "will usually hold on to them longer", "kind": "習性・法則",
     "note": "特定の未来の予定ではない。「手書きする生徒は(決まって)長く覚えているものだ」という法則。usually は習性の will によく随伴して頻度をやわらげる副詞。"},
  ],
 },
 "p2": {
  "marker": [
    {"s": 1, "t": "yet", "sub": "逆接", "note": "文中の yet。「小休止扱い」⇔「体の奥まで効く」の反転。"},
    {"s": 3, "t": "As a result", "sub": "因果・結果", "note": "因果系マーカー。②の変化を受けて「その結果」。"},
    {"s": 5, "t": "also", "sub": "追加", "note": "文中の also は見落とし率 No.1。However 型(文頭+カンマ)だけがマーカーではない。"},
    {"s": 8, "t": "On the other hand", "sub": "対比", "note": "「笑いのあるチーム」⇔「誰も笑わないチーム」の対比。"},
    {"s": 10, "t": "Indeed", "sub": "強調", "note": "「それどころか実際」と主張を一段強める。"},
    {"s": 16, "t": "Yet", "sub": "逆接", "note": "譲歩(⑮無理に笑う必要はない)からの反転。結論はこの後ろ。"},
  ],
  "causal": [
    {"s": 4, "t": "are not caused by", "dir": "結果 ← 原因", "note": "受動で逆向き。「変化」←「ユーモア(だけではない!)」。受動態との二刀流。"},
    {"s": 4, "t": "result from", "dir": "結果 ← 原因", "note": "from = 原因から。「変化」←「笑うという身体動作そのもの」。訓練1⑦の results in と対で覚える。"},
    {"s": 7, "t": "brings about", "dir": "原因 → 結果", "note": "bring about = 引き起こす。「共有された笑い」→「安心感」。"},
    {"s": 7, "t": "contributes to", "dir": "原因 → 結果", "note": "to = 結果へ向かう。「安心感」→「正直な会話」。"},
  ],
  "subj": [
    {"s": 12, "t": "If laughter were truly useless, evolution would have removed it long ago",
     "mk": "If + were / would have + p.p.", "note": "前半は現在の妄想(仮定法過去)、後半は過去の妄想(would have p.p.)のミックス。現実は「役に立つ→除去されなかった」。"},
    {"s": 13, "t": "Had our ancestors laughed less, human groups might have found it harder to hold together",
     "mk": "倒置 Had S + p.p. / might have + p.p.", "note": "If our ancestors had laughed の if 消失→倒置。見た目が疑問文でも「?」が無ければ仮定法を疑え。"},
    {"s": 14, "t": "Without laughter, meetings would feel longer, apologies would be harder, and friendships would cool more quickly",
     "mk": "Without 〜 / would + 原形 ×3", "note": "隠れ仮定法。1つの Without に would が3連発 —— 全部妄想の話。"},
  ],
  "passive": [
    {"s": 1, "t": "is often treated as", "note": "treat する側=世間一般。言わなくても分かるので by なし。often が割り込み。"},
    {"s": 2, "t": "are released", "note": "release する側=脳の仕組み。主役は「鎮痛物質」の側。"},
    {"s": 4, "t": "are not caused by", "note": "因果構文との二刀流。by 〜が「原因」を明示するタイプ。"},
    {"s": 16, "t": "is quietly being helped", "note": "進行形の受動 be being p.p.「今まさに助けられつつある」。quietly が割り込み。"},
  ],
  "part": [
    {"s": 3, "t": "leaving the body at ease for up to forty-five minutes", "kind": "文末型「, -ing」",
     "note": "「そして〜」(結果)。筋肉と心臓を鎮めた結果、体がくつろぐ。"},
    {"s": 9, "t": "Laughing together", "kind": "文頭型「-ing, 」",
     "note": "「〜しながら/〜すると」(時)。When people laugh together の圧縮。"},
  ],
  "will": [
    {"s": 8, "t": "will slowly grow stiff and silent", "kind": "習性・法則",
     "note": "「誰も笑わないチームは(必ず)こわばって静かになっていく」—— 法則の will。未来の予定ではない。"},
    {"s": 17, "t": "will keep its members healthier", "kind": "習性・法則",
     "note": "「自由に笑える職場は(どこでも必ず)メンバーを健康に保つ」。主語が「一般の職場」= 法則。"},
  ],
 },
}

# チェッカー用: 候補語が検出されても解答キーに入れない箇所(理由必須)。
# ★このうち「ひっかけ」系は解説編のトラップ解説にも使う(TRAPS 参照)。
IGNORE = [
    {"p": "p1", "s": 12, "t": "had", "why": "before they had a chance の had は、would の妄想世界に合わせて時制をそろえただけの過去形(時の before 節)。仮定法の目印(if+過去形/would)そのものではない。"},
    {"p": "p2", "s": 10, "t": "came before", "why": "came before は時間の前後関係(〜より前に生まれた)。因果構文ではない。"},
    {"p": "p1", "s": 2, "t": "is quick", "why": "be + 形容詞。過去分詞ではない。"},
    {"p": "p2", "s": 12, "t": "were truly useless", "why": "be + 形容詞(仮定法の were)。受動態ではない。"},
    {"p": "p1", "s": 2, "t": "Typing", "why": "Typing is quick の Typing は動名詞主語(「タイプすること」)。カンマで骨格に添えていないので分詞構文ではない。"},
    {"p": "p1", "s": 14, "t": "Typing", "why": "同上。動名詞主語。"},
    {"p": "p2", "s": 9, "t": "without noticing it", "why": "without + 動名詞 =「〜せずに」のただの前置詞句。判定基準は「would とセットか」——この文の動詞 lower は直説法で、妄想モードではない。"},
]

# 解説編に載せる「ひっかけ」解説(IGNORE の教材化)
TRAPS = [
    {"target": "part", "t": "Typing is quick … (訓練1 ②/⑭)",
     "note": "文頭の -ing でも、カンマで骨格に添えず「〜すること」と主語になっていれば動名詞。分詞構文はカンマで切れて骨格の外にいる。"},
    {"target": "subj", "t": "without noticing it (訓練2 ⑨)",
     "note": "without + -ing は「〜せずに」のただの前置詞句。判定の本体は「would とセットか」——would の無い without は仮定法ではない。"},
    {"target": "subj", "t": "before they had a chance (訓練1 ⑫)",
     "note": "この had は would の妄想世界に時制をそろえただけの過去形(時の before 節)。had を見ただけで仮定法と決めつけない——would とセットかを確認。"},
    {"target": "passive", "t": "typed notes (訓練1 ②) ／ Shared laughter (訓練2 ⑦)",
     "note": "名詞の前に付く過去分詞はただの形容詞用法。be が無ければ受動態ではないし、カンマで骨格に添えていないので分詞構文でもない。"},
]

# ------------------------------------------------------------------
# ミニ講義(解説編) — ▶なぜ大事か / 見つけ方 / ★合言葉 は TARGETS から、
# ここでは各ターゲットの「本文に出た形の総まとめ」を短く。
# ------------------------------------------------------------------
LECTURES = {
 "marker": ("マーカーを□で囲む習慣がつくと、長文が「段落の設計図」に見えてくる。特に逆接(However / Yet)の直後は、"
            "筆者が一番言いたいことの定位置。本文でも ③「速さ≠学び」、⑮「手書きの生徒は長く覚える」、"
            "訓練2の⑯「まじめな仕事は笑いに助けられている」——全部、逆接の直後に核心が来ていた。"),
 "causal": ("因果の動詞は「向き」だけ覚えれば機械的に処理できる。順方向(原因 → 結果)= lead to / result in / "
            "bring about / contribute to / cause。逆方向(結果 ← 原因)= result from / come from / be caused by / be due to。"
            "to・in は「結果へ向かう」、from は「原因から出てくる」——前置詞のイメージで向きが復元できる。"
            "設問で「なぜ?」と聞かれたら、まず本文の因果表現に戻るのが最短ルート。"),
 "subj": ("仮定法は「動詞の形が1つ過去にずれた妄想モード」。目印は3段構え——(1) if + 過去形、"
          "(2) would / could / might + 原形(現在の妄想) or + have p.p.(過去の妄想)、"
          "(3) if が無い隠れ型: Without 〜 / 倒置 Had S p.p. / otherwise。"
          "妄想が見えたら「現実はその逆」を1行添えると、筆者の主張(=現実側)がくっきりする。"),
 "passive": ("受動態は「する側を隠す」か「話題の主役を保つ」ための装置。by 〜が無いのは、(a) 言わなくても分かる、"
             "(b) 誰でもよい・一般論、(c) 言いたくない——のどれか。be と p.p. の間には not / often / easily / being が"
             "割り込むので、「be を見たら p.p. を探しに行く」癖をつける。訓練2⑯ is quietly being helped のような進行形受動も、"
             "分解すれば be + being + p.p. で同じ仲間。"),
 "part": ("分詞構文は「接続詞 + S + V」の圧縮ファイル。文頭型(-ing, )は「〜すると/〜して」、"
          "文末型(, -ing)は「そして〜/〜しながら」と、置かれた位置で訳の相場が決まる。"
          "見つけたら〈 〉で囲んで骨格(S+V)から切り離す——長文が急に短く見える。"),
 "will": ("will = 「100%必ず〜する」が核心。未来の予定はその一部にすぎない。主語が「〜する人(一般)」「〜なチーム/職場」の"
          "とき、will は法則・習性を宣言している。本文の3つの will はどれも実験や経験から導いた「いつでも成り立つ法則」——"
          "だから筆者の主張の置き場所として超重要。will の文に◎を付けると、主張の骨が拾える。"),
}

# ------------------------------------------------------------------
# 全訳(文番号つき)
# ------------------------------------------------------------------
TRANS = {
 "p1": {
  1: "今日、たいていの学生は書くよりタイプする方が速く、講義室はキーボードの静かな音で満ちている。",
  2: "タイピングは速く、タイプしたノートはきれいで検索も簡単なので、ノートは驚くほどの速さで積み上がっていく。",
  3: "しかし、速さは学びと同じものではない。",
  4: "それどころか、いくつかの研究が「最も多くタイプする学生が最も覚えていない可能性がある」と示唆している。",
  5: "手で書くとき、文字は一画ずつゆっくり形づくられる——そしてこの遅さには隠れた価値がある。",
  6: "ペンは話す速さに追いつけないため、書き手は最も重要な考えだけを選ばざるを得なくなる。",
  7: "この「選ぶ努力」がより深い処理につながり、深い処理はより強い記憶という結果を生む。",
  8: "たとえば、ある有名な実験では、手でノートを取った学生は、聞いたことを全部タイプした学生よりも、概念を問う問題で良い成績を収めた。",
  9: "彼らの優位は、字がきれいだったことによって生じたのではない。それは手書きが要求する「余分に考えること」から来ていた。",
  10: "さらに、手の物理的な動きはそれ自体の痕跡を残し、一つ一つの語を脳が覚えている動きに結びつける。",
  11: "もし学生がすべてのノートをタイプし、手では何も書かなかったとしたら、このゆっくりで注意深い思考の多くは消えてしまうだろう。",
  12: "ペンの摩擦がなければ、アイデアは心に沈み込む間もなく、私たちを素通りしていくだろう。",
  13: "これは、コンピュータを捨てるべきだという意味ではない。",
  14: "タイピングは長いレポートに向いているし、デジタルのノートは簡単に共有・保存される。",
  15: "それでも、大事な考えを手で書く学生は、たいていそれをより長く手放さずにいる。",
  16: "ここぞという場面でペンを選べば、私たちは両方の世界のいいとこ取りができるのだ。",
 },
 "p2": {
  1: "笑いはよく、まじめな生活からの小さな息抜き扱いされる。しかしその効果は体の奥深くにまで届く。",
  2: "笑うと、ストレスホルモンが減り、痛みを抑える物質が脳内に放出される。",
  3: "その結果、思いきり笑うと筋肉がゆるんで心拍が落ち着くことがあり、体は最大45分間くつろいだ状態になる。",
  4: "こうした変化はユーモアだけによって生じるのではない。笑うという身体の動作そのものから生じるのだ。",
  5: "笑いはまた、社会の接着剤としても働く。",
  6: "ある研究では、面白い動画を一緒に見た初対面どうしは、中立的な動画を見たペアよりも互いを信頼した。",
  7: "共有された笑いは安心感を生み出し、この感覚が正直な会話に寄与する。",
  8: "一方、誰も笑わないチームは、ゆっくりとこわばり、沈黙していくものだ。",
  9: "一緒に笑いながら、人は気づかないうちに警戒を解いていく。",
  10: "実際、笑いは信頼を築く道具として、言語より先に生まれたと言う研究者もいる。",
  11: "笑いの価値は、それが無い世界を想像したとき最もはっきりする。",
  12: "もし笑いが本当に無用なら、進化はとうの昔にそれを取り除いていただろう。",
  13: "私たちの祖先の笑いがもっと少なかったなら、人間の集団はまとまり続けるのがもっと難しかったかもしれない。",
  14: "笑いがなければ、会議はより長く感じられ、謝罪はより難しくなり、友情はより早く冷めていくだろう。",
  15: "以上のどれも、一日中無理に笑うべきだという意味ではない。",
  16: "それでも、今度教室や職場で笑い声を聞いたら、思い出してほしい——まじめな仕事は、静かに笑いに助けられているのだ。",
  17: "自由に笑える職場は、メンバーをより健康に、より親密に、より創造的に保ってくれるものだ。",
 },
}
