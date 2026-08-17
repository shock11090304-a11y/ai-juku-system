# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.07 — 単一ソース
テーマ: Why Writing by Hand Still Helps You Learn (なぜ今も手で書くことが学びを助けるのか)
／ 基礎レベル（偏差値55〜60 / The Rules 1〜2 相当）
問題編 + 解説編 を build.py が生成。

★ この content.py が**唯一の正典**。問題編・解説編・全訳・SVOC は同じデータから作る。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check_therules.py が引用の全数照合・配点合計・
  設問と解答の対応・SVOC_LOGIC の範囲を検査 ② 生成 PDF の逆照合 ③ 正解の一意性を敵対的に再読。
★ 既存号とテーマが重ならないこと (k01 運動/k02 物語/k03 習慣/k04 まちがい/k05 教える/
  k06 音楽、no04 睡眠 …)。足すときは必ず全号の theme_ja を確認してから書く。
"""

META = {
    "series": "The Rules 式",
    "no": "07",
    "level": "基礎レベル",
    "level_sub": "偏差値55〜60 / The Rules 1〜2 相当",
    "theme_ja": "なぜ今も手で書くことが学びを助けるのか",
    "theme_en": "Why Writing by Hand Still Helps You Learn",
    "minutes": 15,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    (1, 'In a modern classroom, the sound of typing has replaced the sound of pens. Students '
        'arrive with laptops, and notes appear on the screen almost as fast as the teacher '
        'speaks. Writing by hand, in this scene, looks slow and old-fashioned, a habit left '
        'over from a world without machines. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, researchers who study note-taking argue '
        'that the slowness of the hand is not a weakness. It is the very thing that makes '
        'handwriting useful.'),
    (2, 'It is true that a keyboard has real advantages. Typed notes are clean, easy to search, '
        'and simple to share with a friend who was absent. A fast typist can record almost '
        'every sentence of a lecture, while a pen falls behind after the first few minutes. If '
        'the goal is to save words, the machine clearly wins.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span> saving words is not the same as '
        'understanding them. Because the hand cannot keep up with speech, a student who writes '
        'must decide, second by second, which ideas are worth keeping. <u>The pen is too slow '
        'to copy everything, so the mind is forced to choose.<sup>(1)</sup></u> That choosing '
        'is already a kind of thinking, and it happens while the lesson is still going on.'),
    (4, 'Experiments have compared students who typed their notes with students who wrote them '
        'by hand. On simple questions about names and dates, the two groups performed about the '
        'same. On questions that asked why something happened, however, the writers did better. '
        'Researchers found that typed notes often repeated the teacher\'s sentences word for '
        'word, while handwritten notes were shorter and rebuilt in the student\'s own language.'),
    (5, 'A written page also has a shape that a screen does not. Arrows run between boxes, a '
        'question sits in the margin, and a key formula is circled twice. Later, we remember '
        'not only the words but where they were on the page. <u>A page written by hand is a '
        'picture of the way one student thought that day.<sup>(2)</sup></u> Rows of identical '
        'type, by contrast, keep no record of the effort behind them.'),
    (6, 'None of this means that pens contain some kind of magic. A student who copies a '
        'textbook by hand without thinking gains very little. <u>The value lies not in the tool '
        'but in the work the tool forces us to do.<sup>(3)</sup></u> A keyboard can also be '
        'used slowly and thoughtfully; the danger is only that it makes thoughtless copying so '
        'easy.'),
    (7, 'The practical answer, then, is not to throw the laptop away. Use the machine when you '
        'need to store, search, or send information, and use the hand when you need to '
        'understand. Before a difficult class, it may be worth leaving the laptop in the bag '
        'and picking up a pen. The notes will be shorter, and that is exactly the point.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める・下線/タグは除去)
PASSAGE_PLAIN = (
    "In a modern classroom, the sound of typing has replaced the sound of pens. Students arrive "
    "with laptops, and notes appear on the screen almost as fast as the teacher speaks. Writing "
    "by hand, in this scene, looks slow and old-fashioned, a habit left over from a world "
    "without machines. However, researchers who study note-taking argue that the slowness of "
    "the hand is not a weakness. It is the very thing that makes handwriting useful. "
    "It is true that a keyboard has real advantages. Typed notes are clean, easy to search, and "
    "simple to share with a friend who was absent. A fast typist can record almost every "
    "sentence of a lecture, while a pen falls behind after the first few minutes. If the goal "
    "is to save words, the machine clearly wins. "
    "Yet saving words is not the same as understanding them. Because the hand cannot keep up "
    "with speech, a student who writes must decide, second by second, which ideas are worth "
    "keeping. The pen is too slow to copy everything, so the mind is forced to choose. That "
    "choosing is already a kind of thinking, and it happens while the lesson is still going on. "
    "Experiments have compared students who typed their notes with students who wrote them by "
    "hand. On simple questions about names and dates, the two groups performed about the same. "
    "On questions that asked why something happened, however, the writers did better. "
    "Researchers found that typed notes often repeated the teacher's sentences word for word, "
    "while handwritten notes were shorter and rebuilt in the student's own language. "
    "A written page also has a shape that a screen does not. Arrows run between boxes, a "
    "question sits in the margin, and a key formula is circled twice. Later, we remember not "
    "only the words but where they were on the page. A page written by hand is a picture of the "
    "way one student thought that day. Rows of identical type, by contrast, keep no record of "
    "the effort behind them. "
    "None of this means that pens contain some kind of magic. A student who copies a textbook "
    "by hand without thinking gains very little. The value lies not in the tool but in the work "
    "the tool forces us to do. A keyboard can also be used slowly and thoughtfully; the danger "
    "is only that it makes thoughtless copying so easy. "
    "The practical answer, then, is not to throw the laptop away. Use the machine when you need "
    "to store, search, or send information, and use the hand when you need to understand. "
    "Before a difficult class, it may be worth leaving the laptop in the bag and picking up a "
    "pen. The notes will be shorter, and that is exactly the point."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Therefore &nbsp; ② For example &nbsp; ③ However &nbsp; ④ In addition",
         "【 B 】 &nbsp; ① Yet &nbsp; ② Similarly &nbsp; ③ As a result &nbsp; ④ For instance",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(3) <span class='en'>The value lies not in the tool but in the work the tool "
             "forces us to do.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1) <span class='en'>The pen is too slow to copy everything, so the mind is "
             "forced to choose.</span> について、ペンが遅いことがなぜ学びの助けになるのか。"
             "本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "本文で紹介されている実験の結果として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 名前や年代についての易しい問題でも、手で書いた学生の方がはっきりと良い成績だった。",
         "② なぜそれが起きたのかを問う問題では、手で書いた学生の方が良い成績だった。",
         "③ どちらの問題でも、パソコンで打った学生の方が良い成績だった。",
         "④ 手で書いた学生のノートの方が、教師の文をそのまま繰り返している割合が高かった。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(2) <span class='en'>A page written by hand is a picture of the way one "
             "student thought that day.</span> とはどういうことか。手書きのページと画面上の"
             "文字列との違いにふれながら、本文全体をふまえて日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① パソコンは学びを妨げるものなので、学生は授業では使わない方がよい。",
         "② 手で書くこと自体に特別な力があるので、教科書は書き写すのが最もよい。",
         "③ 記録や共有にはパソコンを、理解が目的のときには手書きを使い分けるのがよい。",
         "④ ノートは講義の言葉をできる限り多く残すことが目的なので、速く打てる方がよい。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 速く打てる人は講義のほとんどの文を記録できるが、最初の数分を過ぎるとペンは遅れ始める。",
         "② 手が話す速さに追いつけないため、書く学生はどの考えを残す価値があるかを選ばねばならない。",
         "③ 手書きのノートはパソコンのノートより長く、教師の言葉をそのまま多く含んでいた。",
         "④ 手書きのページでは、言葉だけでなくそれがページのどこにあったかも思い出される。",
         "⑤ 筆者は、難しい授業の前でもパソコンを持ち込む方が結局は効率がよいと述べている。",
         "⑥ キーボードは常に思考を妨げるので、ゆっくり使っても無意味だ、と筆者は述べている。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ③ However　　B ＝ ① Yet",
     "exp": "A：「手書きは遅くて時代遅れ」という通念に対し、研究者は「手の遅さは弱点ではない」と"
            "<b>反転</b>する流れ。逆接 → However。Therefore（因果）・For example（例示）・"
            "In addition（追加）は不可。<br>"
            "B：第2段「確かにキーボードには本当の利点がある（＝譲歩）」に対し、第3段は「だが語を"
            "保存することは理解することと同じではない」と主張へ<b>転換</b>する。逆接 → Yet。"
            "Similarly（類比）・As a result（因果）・For instance（例示）は流れに合わない。 "
            "〔<b>解法ルール R7</b>／<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "②",
     "exp": "第4段「<span class='en'>On questions that asked why something happened, however, the "
            "writers did better</span>」＝「なぜ起きたか」を問う問題では手書き側が良かった。"
            "①×：易しい問題では「<span class='en'>the two groups performed about the same</span>"
            "（ほぼ同じ）」。③×：手書き側が良かった設問がある。④×：そのまま繰り返していたのは"
            "<b>打った側</b>のノート。 〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "③",
     "exp": "第7段「<span class='en'>Use the machine when you need to store, search, or send "
            "information, and use the hand when you need to understand</span>」と一致。"
            "①×：第7段第1文「<span class='en'>The practical answer, then, is not to throw the "
            "laptop away</span>」に反する。②×：第6段「<span class='en'>None of this means that "
            "pens contain some kind of magic</span>」＋「考えずに書き写す学生は得るものがほとんど"
            "ない」に反する。④×：第3段「語を保存することは理解することと同じではない」に反する。 "
            "〔<b>読解ルール R3</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・②・④",
     "exp": "①〇：第2段「<span class='en'>A fast typist can record almost every sentence of a "
            "lecture, while a pen falls behind after the first few minutes</span>」。"
            "②〇：第3段「<span class='en'>Because the hand cannot keep up with speech</span>」＋"
            "「<span class='en'>which ideas are worth keeping</span>」。④〇：第5段"
            "「<span class='en'>we remember not only the words but where they were on the page</span>」。<br>"
            "③×：第4段は<b>主語が逆</b>——そのまま繰り返すのは<b>打った側</b>で、手書きは"
            "「<span class='en'>shorter and rebuilt in the student's own language</span>」（より短い）。"
            "⑤×：第7段「<span class='en'>it may be worth leaving the laptop in the bag and picking "
            "up a pen</span>」に反する。⑥×：第6段「<span class='en'>A keyboard can also be used "
            "slowly and thoughtfully</span>」に反する（「常に妨げる」は<b>言い過ぎ</b>）。 "
            "〔<b>解法ルール R9</b>：主語の取り違え＋言い過ぎの排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(3)和訳",
     "model": "価値は道具そのものにあるのではなく、その道具が私たちにせざるをえなくさせる作業の方に"
              "あるのだ。",
     "points": "▶<b>採点要素</b>：①<b>not A but B</b>＝「AではなくB」の対比を構文どおり訳出"
               "〔<b>読解ルール R3</b>〕／②<b>lie in ~</b>＝「〜にある」（横たわる、ではない）／"
               "③<b>the work &lt;(that) the tool forces us to do&gt;</b>＝関係代名詞の省略を見抜き"
               "「その道具が私たちにさせる作業」と訳す〔<b>構文ルール R11</b>〕。"
               "force A to do＝「Aに無理やり〜させる」。"},
    {"no": "問3", "pts": "8点・記述",
     "model": "ペンは話す速さに追いつけず、すべてを書き写すことができない。そのため書く学生は、"
              "どの考えを残す価値があるかを一秒ごとに選ばなければならない。この「選ぶ」という作業が"
              "すでに一種の思考であり、しかも授業が進んでいるその最中に行われるので、遅さがかえって"
              "理解を助けることになる。",
     "points": "▶<b>採点要素</b>：①<b>手が話す速さに追いつけない</b>（第3段 Because the hand cannot "
               "keep up with speech）／②だから<b>何を残すかを選ばざるをえない</b>（must decide … "
               "which ideas are worth keeping）／③<b>その選択自体が思考であり、授業中に行われる</b>"
               "（That choosing is already a kind of thinking）。"
               "「遅い＝欠点」ではなく「遅い＝考えさせる仕組み」と反転させて説明できていること。 "
               "〔<b>読解ルール R6</b>：因果／<b>解法ルール R8</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①手書きのページには、矢印や囲み、余白の疑問、二重に丸をつけた公式といった形があり、"
              "あとから言葉だけでなくそれがページのどこにあったかまで思い出される。②つまりページの"
              "見た目そのものが、その日その学生がどう考え、何を重要だと判断したかの記録になっている、"
              "ということ。③これに対し、画面上の同じ形の文字が並ぶだけの列は、その背後にあった"
              "思考の労力を何も残さない。",
     "points": "▶<b>採点要素</b>：①<b>ページの「形」</b>＝矢印・囲み・余白の疑問・丸（第5段）と"
               "<b>場所の記憶</b>（where they were on the page）（各3点）／②<b>その日の考え方の"
               "「絵」＝思考の記録</b>だという中心の言い換え（4点）／③対比として"
               "<b>同一の活字の列は労力の記録を残さない</b>（Rows of identical type … keep no record "
               "of the effort behind them）に触れる。 〔<b>読解ルール R5</b>：比喩の中身を確定／"
               "<b>解法ルール R8</b>〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A（However→通念の反転）、空所B（Yet→第3段の主張転換）。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true that a keyboard has real advantages」→ 第3段 Yet で反転。"),
        ("R3", "not A but B は B の側が主張・核心", "★★★",
         "第1段 the slowness of the hand is not a weakness、下線部(3) not in the tool but in the work。"),
        ("R4", "抽象 → 具体（Experiments … / Arrows run …）を往復し、具体例は「何の例か」に戻す", "★★",
         "第4段の実験、第5段の矢印・余白・丸——すべて「手書きが思考を残す」ことの具体。"),
        ("R5", "指示語・比喩（it / that choosing / a picture）は必ず中身を確定する", "★★",
         "第1段 It is the very thing …、第3段 That choosing、下線部(2) a picture of the way …（問5）。"),
        ("R6", "因果（because / so / forces）で理由と結論をつなぐ", "★★",
         "第3段 Because the hand cannot keep up …, so the mind is forced to choose（問3の骨格）。"),
        ("R18", "比喩・たとえ話は、直前直後の主張の言い換えとして読む（比喩だけで終わらせない）", "★★★",
         "第5段「a picture of the way one student thought」＝下線部(2)。前後の矢印・余白・場所の記憶が中身を確定する。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。because … so … の因果、by contrast の対比を利用する。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、主語の取り違え・言い過ぎを疑う", "★★★",
         "問4・問6・問7。③「そのまま繰り返すのは手書き」は<b>主語の取り違え</b>（実際は打った側）。"),
    ],
    "構文ルール": [
        ("R11", "関係詞・分詞はカタマリで、名詞を後ろから説明する", "★★",
         "researchers <who study note-taking>、a shape <that a screen does not (have)>、"
         "the work <(that) the tool forces us to do>、A page <written by hand> 型。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「教室ではタイプ音がペン音に取って代わった。手書き＝遅くて時代遅れ」を提示。"
             "→ <b>However（R1）</b>：ノート取りの研究者は「<b>手の遅さは弱点ではない</b>——それこそが"
             "手書きを役立てているもの」と反転する。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true that …（R2）</b>：確かにキーボードには利点がある——きれい・検索できる・"
             "共有しやすい・速い人は講義のほぼ全文を記録できる。<b>語を保存するのが目的なら機械の勝ち</b>。"},
    {"arrow": "◀ Yet 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "だが<b>語を保存することは理解することと同じではない</b>。手は話す速さに追いつけない→"
             "<b>何を残すかを一秒ごとに選ぶ</b>（下線部(1)）。<b>その選択がすでに思考</b>であり、"
             "しかも授業の進行中に起きる。"},
    {"arrow": "↓　具体化（R4）"},
    {"role": "理由①（具体化）", "para": "¶4", "kind": "reason",
     "text": "実験：名前・年代の易しい問題では<b>両群ほぼ同じ</b>。だが<b>「なぜ」を問う問題では手書きが"
             "上</b>。打ったノートは教師の文をそのまま繰り返しがちで、手書きは<b>より短く、自分の言葉で"
             "組み直されていた</b>（問4）。"},
    {"arrow": "↓　理由②"},
    {"role": "理由②", "para": "¶5", "kind": "reason",
     "text": "紙のページには<b>画面にない「形」</b>がある：矢印・囲み・余白の疑問・二重丸。あとで"
             "<b>言葉だけでなく位置まで</b>思い出す。＝<b>その日の考え方の「絵」（下線部(2)・R18）</b>。"
             "同一の活字の列は労力の記録を残さない。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "ペンに魔法があるわけではない（考えずに書き写す学生は得るものがない）。"
             "<b>価値は道具ではなく、道具が強いる作業の側にある（not A but B・R3）</b>＝下線部(3)。"
             "キーボードもゆっくり使えるが、<b>考えない書き写しを容易にする</b>点が危うい。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "実践的な答えは「パソコンを捨てよ」ではない。<b>保存・検索・送信には機械、理解には手</b>と"
             "使い分ける。難しい授業の前は鞄にしまってペンを持つ価値がある——<b>ノートは短くなるが、"
             "それこそが狙い</b>。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 手書きへの二つの見方",
     "caption": "同じ「手の遅さ」でも、〈弱点〉と見れば時代遅れの習慣に見え（第1段）、〈仕組み〉と見れば"
                "<b>何を残すかを選ばせる装置</b>になる（第3段）。本文は However を境に反転する。",
     "para": "→ 第1・3段"},
    {"id": "fig2", "title": "図2 ｜ 打つノートと書くノート",
     "caption": "打つ＝速い・きれい・検索できるが、<b>教師の文をそのまま複製</b>しがち（第2・4段）。"
                "書く＝遅いので<b>選び、短く、自分の言葉に組み直す</b>。だから「なぜ」を問う問題で差が出る"
                "（第4段）。",
     "para": "→ 第2・4段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 価値は道具ではなく、道具が強いる作業に",
     "caption": "ペンそのものに魔法はない（考えずに写すなら得るものはない）。<b>not in the tool but in "
                "the work</b>＝遅さが選択と再構成を強いることに価値がある。ゆえに<b>保存には機械、"
                "理解には手</b>（第6〜7段）。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "現代の教室では、タイプの音がペンの音に取って代わってしまった。学生はノートパソコンを持って"
        "やって来て、教師が話すのとほとんど同じ速さで、画面上にノートが現れる。この光景の中では、"
        "手で書くことは遅く時代遅れに見える——機械のなかった世界から残された習慣に。"
        "<b>しかし</b>、ノートの取り方を研究する研究者たちは、手の遅さは弱点ではない、と主張する。"
        "それこそが、手書きを役に立つものにしているまさにそのものなのだ、と。"),
    (2, "確かに、キーボードには本当の利点がある。打ったノートはきれいで、検索しやすく、"
        "欠席した友人と共有するのも簡単だ。速く打てる人なら講義のほとんどすべての文を記録できるが、"
        "ペンは最初の数分を過ぎると遅れ始める。もし目的が語を保存することなら、機械の勝ちは明らかだ。"),
    (3, "<b>だが</b>、語を保存することは、それを理解することと同じではない。手は話す速さに追いつけない"
        "ので、書く学生は、どの考えが残す価値のあるものかを、一秒ごとに決めなければならない。"
        "<b>ペンは遅すぎてすべてを書き写すことができない。だから、頭の方が選ぶことを強いられるのだ。</b>"
        "その「選ぶ」という行為がすでに一種の思考であり、しかもそれは授業がまだ続いている最中に"
        "起きている。"),
    (4, "いくつもの実験が、ノートを打った学生と手で書いた学生とを比べてきた。名前や年代についての"
        "易しい問題では、二つのグループはほぼ同じ成績だった。しかし、なぜそれが起きたのかを問う問題では、"
        "書いた側の方が良い成績だった。研究者たちが見いだしたのは、打ったノートはしばしば教師の文を"
        "一語一語そのまま繰り返しているのに対し、手書きのノートはより短く、その学生自身の言葉で"
        "組み直されている、ということだった。"),
    (5, "手で書かれたページには、画面にはない「形」もある。矢印がいくつもの囲みの間を走り、疑問が"
        "余白に座り、重要な公式には二重に丸がつけられている。あとになって私たちは、言葉だけでなく、"
        "それがページのどこにあったかまで思い出す。<b>手で書かれた一ページは、その日ひとりの学生が"
        "どう考えたかを写した絵なのである。</b>それに対して、同じ形の活字が並ぶ列は、その背後にあった"
        "労力の記録を何も残さない。"),
    (6, "以上のことは、ペンに何か魔法のようなものが宿っている、という意味ではまったくない。"
        "何も考えずに教科書を手で書き写す学生が得るものは、ごくわずかだ。<b>価値は道具そのものにあるの"
        "ではなく、その道具が私たちにせざるをえなくさせる作業の方にあるのだ。</b>キーボードだって"
        "ゆっくり、考えながら使うことはできる。危ういのはただ、それが何も考えない書き写しをあまりにも"
        "簡単にしてしまう、という点だけである。"),
    (7, "とすれば、実践的な答えは、ノートパソコンを捨てることではない。情報を保存し、検索し、"
        "送る必要があるときには機械を使い、理解する必要があるときには手を使えばよい。難しい授業の前には、"
        "パソコンを鞄に入れたままにして、ペンを手に取る価値があるかもしれない。ノートは短くなるだろう——"
        "そして、それこそがまさに狙いなのである。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("replace", "〜に取って代わる"),
    ("old-fashioned", "時代遅れの"),
    ("left over from ~", "〜から残された"),
    ("note-taking", "ノートを取ること"),
    ("argue", "〜と主張する"),
    ("weakness", "弱点"),
    ("the very ~", "まさにその〜"),
    ("advantage", "利点"),
    ("search", "〜を検索する"),
    ("share A with B", "AをBと共有する"),
    ("absent", "欠席して"),
    ("record", "〜を記録する"),
    ("fall behind", "遅れる、後れを取る"),
    ("keep up with ~", "〜に追いつく、遅れずについていく"),
    ("second by second", "一秒ごとに"),
    ("be worth -ing", "〜する価値がある"),
    ("be forced to do", "〜せざるをえない"),
    ("go on", "続く、進行する"),
    ("compare A with B", "AをBと比べる"),
    ("perform", "（成績などを）収める、やってのける"),
    ("word for word", "一語一語、逐語的に"),
    ("rebuild", "〜を組み直す、再構築する"),
    ("margin", "余白"),
    ("circle", "〜に丸をつける"),
    ("identical", "まったく同じ"),
    ("by contrast", "それに対して"),
    ("keep no record of ~", "〜の記録を残さない"),
    ("lie in ~", "〜にある、〜に存する"),
    ("force A to do", "Aに無理やり〜させる"),
    ("thoughtless", "何も考えない、不注意な"),
    ("throw ~ away", "〜を捨てる"),
    ("it is worth -ing", "〜する価値がある"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：通念「手書き＝遅くて時代遅れ」と、その反転（However）",
  "sentences": [
    {"chunks": [("M","(In a modern classroom),","現代の教室では"),
                ("S","the sound of typing","タイプの音が"),
                ("V","has replaced","取って代わった"),("O","the sound of pens.","ペンの音に")],
     "note":"▶ replace＝「〜に取って代わる」（他動詞。to は不要）。現在完了＝すでにそうなっている状態。"},
    {"chunks": [("S","Students","学生は"),("V","arrive","やって来る"),("M","(with laptops),","ノートパソコンを持って"),
                ("接","and","そして"),("S","notes","ノートが"),("V","appear","現れる"),
                ("M","(on the screen)","画面上に"),("M","(almost as fast as the teacher speaks).","教師が話すのとほとんど同じ速さで")],
     "note":"▶ <b>as ~ as …</b>＝同等比較（副詞 fast）。almost が比較全体を和らげる。"},
    {"chunks": [("S","Writing by hand,","手で書くことは"),("M","in this scene,","この光景の中では"),
                ("V","looks","見える"),("C","slow and old-fashioned,","遅く時代遅れに"),
                ("-","a habit &lt;left over from a world without machines&gt;.","——機械のなかった世界から残された習慣に")],
     "note":"▶ 動名詞 Writing by hand＝主語。look C＝「Cに見える」。コンマ以下は<b>同格</b>の言い換えで、"
            "過去分詞 left over … が a habit を後ろから説明〔R11〕。"},
    {"chunks": [("接","However,","しかし"),
                ("S","researchers &lt;who study note-taking&gt;","ノートの取り方を研究する研究者たちは"),
                ("V","argue","主張する"),
                ("O","[that the slowness of the hand is not a weakness].","手の遅さは弱点ではない、と")],
     "note":"▶ <b>R1｜逆接 However の直後が筆者の主張</b>（＝空所A）。関係詞節 who … が researchers を修飾〔R11〕。"},
    {"chunks": [("S","It","それは"),("V","is","である"),
                ("C","the very thing &lt;that makes handwriting useful&gt;.","手書きを役に立つものにしているまさにそのもの")],
     "note":"▶ <b>the very ~</b>＝「まさにその〜」（強調）。<b>make O C</b>＝「OをCにする」。"
            "It＝the slowness of the hand〔R5〕。ここが第1段の主張の核。"},
  ]},
 {"head": "第2段 — 譲歩：キーボードには本当の利点がある（It is true that …）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true","本当"),
                ("-","[that a keyboard has real advantages].","キーボードには本当の利点があるということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>。第3段の Yet（反転）の前振り。"},
    {"chunks": [("S","Typed notes","打ったノートは"),("V","are","である"),
                ("C","clean, easy to search, and simple to share (with a friend &lt;who was absent&gt;).","きれいで、検索しやすく、欠席した友人と共有するのも簡単")],
     "note":"▶ 補語が三つ並列。<b>easy / simple + to do</b>＝「〜しやすい」（主語が to 以下の意味上の目的語）。"
            "who was absent＝関係詞節〔R11〕。"},
    {"chunks": [("S","A fast typist","速く打てる人は"),("V","can record","記録できる"),
                ("O","almost every sentence of a lecture,","講義のほとんどすべての文を"),
                ("接","while","一方"),("S","a pen","ペンは"),("V","falls behind","遅れ始める"),
                ("M","(after the first few minutes).","最初の数分を過ぎると")],
     "note":"▶ <b>while＝対比の接続詞</b>（「〜する一方で」）。fall behind＝「遅れを取る」。<b>問7①の根拠</b>。"},
    {"chunks": [("M","(If the goal is to save words),","もし目的が語を保存することなら"),
                ("S","the machine","機械が"),("M","clearly","明らかに"),("V","wins.","勝つ")],
     "note":"▶ 譲歩の締め。to save words＝補語になる不定詞（名詞的用法）。次段でこの前提自体が疑われる。"},
  ]},
 {"head": "第3段 — 主張の転換：保存と理解は違う／遅さが選択を強いる（Yet）",
  "sentences": [
    {"chunks": [("接","Yet","だが"),("S","saving words","語を保存することは"),
                ("V","is not","ではない"),("C","the same as understanding them.","それを理解することと同じ")],
     "note":"▶ <b>R1｜Yet＝逆接でここが主張転換点</b>（＝空所B）。動名詞 saving＝主語。"
            "<b>the same as ~</b>＝「〜と同じ」。them＝words〔R5〕。"},
    {"chunks": [("M","(Because the hand cannot keep up with speech),","手は話す速さに追いつけないので"),
                ("S","a student &lt;who writes&gt;","書く学生は"),("V","must decide,","決めなければならない"),
                ("M","second by second,","一秒ごとに"),
                ("O","[which ideas are worth keeping].","どの考えが残す価値のあるものかを")],
     "note":"▶ <b>R6｜Because＝因果</b>。keep up with ~＝「追いつく」。which 節＝間接疑問（decide の目的語）。"
            "<b>be worth -ing</b>＝「〜する価値がある」。"},
    {"chunks": [("S","The pen","ペンは"),("V","is","である"),("C","too slow to copy everything,","遅すぎてすべてを書き写せない"),
                ("接","so","だから"),("S","the mind","頭の方が"),("V","is forced","強いられる"),
                ("C","to choose.","選ぶことを")],
     "note":"▶ <b>下線部(1)＝問3</b>。<b>too ~ to do</b>＝「…すぎて〜できない」。so＝因果の接続詞。"
            "be forced to do＝force A to do の受動態〔R6〕。"},
    {"chunks": [("S","That choosing","その「選ぶ」という行為は"),("V","is","である"),
                ("M","already","すでに"),("C","a kind of thinking,","一種の思考"),("接","and","そして"),
                ("S","it","それは"),("V","happens","起きる"),
                ("M","(while the lesson is still going on).","授業がまだ続いている最中に")],
     "note":"▶ <b>R5｜That choosing</b>＝前文の「選ばざるをえない」ことを指す。go on＝「続く」。"
            "「思考が授業中に起きる」という点が手書きの利点の核心。"},
  ]},
 {"head": "第4段 — 具体化：実験——「なぜ」を問う問題で差が出た",
  "sentences": [
    {"chunks": [("S","Experiments","いくつもの実験が"),("V","have compared","比べてきた"),
                ("O","students &lt;who typed their notes&gt;","ノートを打った学生を"),
                ("M","(with students &lt;who wrote them by hand&gt;).","手で書いた学生と")],
     "note":"▶ <b>compare A with B</b>＝「AをBと比べる」。関係詞節が二つ〔R11〕。them＝their notes〔R5〕。"},
    {"chunks": [("M","(On simple questions about names and dates),","名前や年代についての易しい問題では"),
                ("S","the two groups","二つのグループは"),("V","performed","成績を収めた"),
                ("M","about the same.","ほぼ同じ")],
     "note":"▶ perform＝「（成績を）収める」。<b>問4①はこの文で×</b>（易しい問題では差がない）〔R9〕。"},
    {"chunks": [("M","(On questions &lt;that asked why something happened&gt;),","なぜそれが起きたのかを問う問題では"),
                ("M","however,","しかし"),("S","the writers","書いた側が"),("V","did","収めた"),("M","better.","より良い成績を")],
     "note":"▶ <b>R4｜具体の中の対比</b>。that asked … ＝関係詞節〔R11〕。do better＝「より良い成績を収める」。"
            "<b>問4②の根拠</b>。"},
    {"chunks": [("S","Researchers","研究者たちは"),("V","found","見いだした"),
                ("O","[that typed notes often repeated the teacher's sentences word for word, (while handwritten notes were shorter and rebuilt in the student's own language)].","打ったノートはしばしば教師の文を一語一語繰り返すのに対し、手書きのノートはより短く、その学生自身の言葉で組み直されている、と")],
     "note":"▶ that 節の中に while（対比）の副詞節。word for word＝「一語一語」。"
            "<b>問7③は主語が逆</b>（そのまま繰り返すのは打った側）〔R9〕。"},
  ]},
 {"head": "第5段 — 理由②：ページの「形」は思考の記録になる",
  "sentences": [
    {"chunks": [("S","A written page","手で書かれたページは"),("M","also","もまた"),("V","has","持つ"),
                ("O","a shape &lt;that a screen does not&gt;.","画面にはない「形」を")],
     "note":"▶ also＝理由②への追加。関係詞節の末尾は does not (have) の省略〔R11〕。"},
    {"chunks": [("S","Arrows","矢印が"),("V","run","走り"),("M","(between boxes),","いくつもの囲みの間を"),
                ("S","a question","疑問が"),("V","sits","座り"),("M","(in the margin),","余白に"),
                ("接","and","そして"),("S","a key formula","重要な公式には"),
                ("V","is circled","丸がつけられている"),("M","twice.","二重に")],
     "note":"▶ <b>R4｜具体例</b>が三つ並列。<b>擬人法</b>（矢印が走る・疑問が座る）で紙面の様子を描く。"},
    {"chunks": [("M","Later,","あとになって"),("S","we","私たちは"),("V","remember","思い出す"),
                ("O","not only the words","言葉だけでなく"),
                ("O","but where they were on the page.","それがページのどこにあったかまで")],
     "note":"▶ <b>not only A but (also) B</b>＝「AだけでなくBも」。B は where 節（名詞節）。"
            "<b>問7④の根拠</b>。"},
    {"chunks": [("S","A page &lt;written by hand&gt;","手で書かれた一ページは"),("V","is","である"),
                ("C","a picture of the way &lt;one student thought that day&gt;.","その日ひとりの学生がどう考えたかを写した絵")],
     "note":"▶ <b>下線部(2)＝問5</b>。過去分詞 written by hand が A page を説明〔R11〕。"
            "the way (that) S V＝「SがVするやり方」。<b>R18｜比喩</b>——中身は前後の文が確定する。"},
    {"chunks": [("S","Rows of identical type,","同じ形の活字が並ぶ列は"),("M","by contrast,","それに対して"),
                ("V","keep","残す"),("O","no record of the effort &lt;behind them&gt;.","その背後にあった労力の記録を何も（残さない）")],
     "note":"▶ <b>by contrast＝対比の目印</b>。keep <b>no</b> record＝否定。type＝「活字」（不可算）。"
            "手書きとの対比が問5の解答要素になる。"},
  ]},
 {"head": "第6段 — 核心：価値は道具ではなく、道具が強いる作業にある",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),("V","means","意味しない"),
                ("O","[that pens contain some kind of magic].","ペンに何か魔法のようなものが宿っているとは")],
     "note":"▶ 譲歩つきで自説を限定する型。none of ~＝全否定。<b>問6②はこの文で×</b>〔R9〕。"},
    {"chunks": [("S","A student &lt;who copies a textbook by hand without thinking&gt;","何も考えずに教科書を手で書き写す学生は"),
                ("V","gains","得る"),("O","very little.","ごくわずかしか（得ない）")],
     "note":"▶ 関係詞節が主語を修飾〔R11〕。without -ing＝「〜せずに」。very little＝準否定「ごくわずか」。"
            "<b>問7⑥の根拠</b>。"},
    {"chunks": [("S","The value","価値は"),("V","lies","ある"),
                ("M","not (in the tool)","道具そのものにではなく"),
                ("M","but (in the work &lt;the tool forces us to do&gt;).","その道具が私たちにさせる作業の方に")],
     "note":"▶ <b>下線部(3)＝問2</b>。<b>R3｜not A but B＝Bが主張</b>。lie in ~＝「〜にある」。"
            "the work (that) the tool forces us to do＝関係代名詞の省略〔R11〕。"},
    {"chunks": [("S","A keyboard","キーボードも"),("V","can also be used","使うことができる"),
                ("M","slowly and thoughtfully;","ゆっくり、考えながら"),
                ("S","the danger","危ういのは"),("V","is","である"),("M","only","ただ"),
                ("C","[that it makes thoughtless copying so easy].","それが何も考えない書き写しをあまりにも簡単にしてしまうという点だけ")],
     "note":"▶ 助動詞つき受動態 can be used。セミコロンで譲歩と限定を並置。"
            "<b>make O C</b>＝「OをCにする」（O＝thoughtless copying）。"},
  ]},
 {"head": "第7段 — 結論：保存には機械、理解には手",
  "sentences": [
    {"chunks": [("S","The practical answer,","実践的な答えは"),("M","then,","とすれば"),
                ("V","is","である"),("C","not to throw the laptop away.","ノートパソコンを捨てることではない")],
     "note":"▶ 不定詞が補語（名詞的用法）。throw ~ away＝「〜を捨てる」。<b>問6①はこの文で×</b>〔R9〕。"},
    {"chunks": [("V","Use","使え"),("O","the machine","機械を"),
                ("M","(when you need to store, search, or send information),","情報を保存し、検索し、送る必要があるときには"),
                ("接","and","そして"),("V","use","使え"),("O","the hand","手を"),
                ("M","(when you need to understand).","理解する必要があるときには")],
     "note":"▶ 命令文が二つ並列。<b>本文の結論を一文で示す核心文</b>（問6③の根拠）。"
            "store / search / send が to の後で並列。"},
    {"chunks": [("M","(Before a difficult class),","難しい授業の前には"),("S","it","（形式主語）"),
                ("V","may be","かもしれない"),("C","worth","価値がある"),
                ("-","leaving the laptop in the bag and picking up a pen.","パソコンを鞄に入れたままにして、ペンを手に取ることは")],
     "note":"▶ <b>it is worth -ing</b>＝「〜する価値がある」。動名詞が二つ並列。<b>問7⑤はこの文で×</b>〔R9〕。"},
    {"chunks": [("S","The notes","ノートは"),("V","will be","なるだろう"),("C","shorter,","より短く"),
                ("接","and","そして"),("S","that","それが"),("V","is","である"),
                ("C","exactly the point.","まさに狙い")],
     "note":"▶ 締めの一文。短くなることを<b>欠点ではなく狙い</b>と言い切って、第3段の「選ぶ＝思考」に回収する。"
            "that＝ノートが短くなること〔R5〕。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=5文/第2段=4文/第3段=4文/第4段=4文/第5段=5文/第6段=4文/第7段=4文)
SVOC_LOGIC = {
    (1, 3): "対比", (1, 4): "主張", (1, 5): "主張",
    (2, 1): "譲歩", (2, 3): "対比", (2, 4): "譲歩",
    (3, 1): "対比", (3, 2): "因果", (3, 3): "主張", (3, 4): "主張",
    (4, 1): "具体例", (4, 2): "具体例", (4, 3): "対比", (4, 4): "具体例",
    (5, 1): "追加", (5, 2): "具体例", (5, 4): "主張", (5, 5): "対比",
    (6, 1): "譲歩", (6, 2): "具体例", (6, 3): "主張", (6, 4): "譲歩",
    (7, 1): "譲歩", (7, 2): "主張", (7, 3): "具体例", (7, 4): "主張",
}
