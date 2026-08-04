# -*- coding: utf-8 -*-
"""
英語長文 The Rules 式 No.02（最難関編） — 単一ソース
テーマ: Science Does Not Deal in Certainty (科学は確実性を売らない) / 最難関レベル（早慶・旧帝 / The Rules 4 相当）
問題編 + 解説編 を build.py が生成。
"""

META = {
    "series": "The Rules 式",
    "no": "02",
    "level": "最難関レベル",
    "level_sub": "早慶・旧帝 / The Rules 4 相当",
    "theme_ja": "科学は確実性を売らない",
    "theme_en": "Science Does Not Deal in Certainty",
    "minutes": 25,
    "student": "",  # 配布用: 空欄(生徒が記入)
    "full": 60,
}

# ------------------------------------------------------------------
# 本文 (問題編用HTML)。段落番号つき。空所=<span class="blank">、下線=<u>…<sup>。
# ------------------------------------------------------------------
PASSAGE_HTML = [
    # (para_no, html)
    (1, 'When people turn to science, what they usually want is an answer &mdash; a firm, '
        'final verdict on which they can safely act. Public confidence, surveys suggest, tends '
        'to fall when experts revise their advice, as though a change of position were a '
        'confession of incompetence. Such impatience is understandable, for a society that must '
        'act on scientific findings naturally wants those findings to be settled. '
        '<span class="blank">【&nbsp;A&nbsp;】</span>, the expectation underneath it &mdash; '
        'that science exists to hand us certainties &mdash; rests on a deep misunderstanding of '
        'what science actually is.'),
    (2, 'It is true, of course, that the practical authority of science is beyond serious '
        'dispute. The bridges we cross do not, as a rule, collapse; the medicines we swallow '
        'work, and measurably so. The aircraft, the antibiotics, and the satellites on which '
        'modern life depends were all built on scientific foundations, and no other way of '
        'investigating the world has produced results of comparable reliability. To deny this '
        'success would be absurd, and nothing that follows is meant to deny it.'),
    (3, '<span class="blank">【&nbsp;B&nbsp;】</span> the source of that success is precisely '
        'what the demand for certainty overlooks. Science is not a warehouse of finished '
        'truths, patiently accumulated and never to be touched again; it is a method &mdash; a '
        'discipline of proposing hypotheses that could be wrong, exposing them to evidence, and '
        'revising or abandoning whatever fails the test. What makes a claim scientific is not '
        'that it is certain but that it is fallible in a controlled way: we know, at least in '
        'principle, what would prove it false.'),
    (4, 'Seen from this angle, the familiar complaint turns upside down. <u>When a researcher '
        'abandons a once-favoured position in the light of new evidence, this is not a symptom '
        'of failure but a sign that the method is doing exactly what it was designed to '
        'do.<sup>(1)</sup></u> A field in which nobody ever changed their mind would be a field '
        'in which nothing was being tested; ideas would be defended, careers protected, and '
        'evidence, if consulted at all, consulted only for decoration. Individual scientists '
        'are seldom, if ever, free of vanity or bias &mdash; but the system as a whole is '
        'arranged so that even a cherished theory must sooner or later answer to data it cannot '
        'explain.'),
    (5, '&ldquo;Then what are we supposed to believe?&rdquo; the frustrated reader may ask, '
        'and the question deserves a straight answer. If what you require is certainty, you '
        'must seek it outside science &mdash; in mathematics, perhaps, or in faith &mdash; '
        'because nothing that rests on evidence can be guaranteed never to change. <u>What '
        'science offers instead is less comforting but more honest: probabilities, and '
        'provisional best explanations that stand only until something better survives the '
        'evidence.<sup>(2)</sup></u> The choice we are so often presented with &mdash; trust '
        'the experts blindly or fall back on gut feeling &mdash; is therefore a false one. '
        'There is a third answer: trust the method itself, uncertainty included, for it is the '
        'only procedure we possess that systematically catches its own mistakes.'),
    (6, 'This is why our anxiety about scientific uncertainty, however natural, aims at the '
        'wrong target. <u>Uncertainty is not a weakness that science must apologize for; it is '
        'the very condition that makes science science, the price of a system in which '
        'evidence, not authority, has the final word.<sup>(3)</sup></u> Remove it &mdash; '
        'demand that every question be settled once and for all &mdash; and what remains is no '
        'longer science but dogma wearing its costume.'),
    (7, 'None of this means that every scientific claim is equally provisional, or that a '
        'finding announced yesterday deserves the confidence we grant a theory tested for a '
        'century. Evidence comes in different weights, and so, accordingly, should our trust. '
        'What we need to abandon is not science but the all-or-nothing demand we bring to it '
        '&mdash; the assumption that whatever falls short of absolute certainty is worth '
        'nothing at all. To accept that the best available answer may still be revised, and to '
        'act on it anyway, is not a betrayal of reason; it is where an intelligent relationship '
        'with science begins.'),
]

# 語数カウント用のプレーン本文 (空所は正解語で埋める)
PASSAGE_PLAIN = (
    "When people turn to science, what they usually want is an answer a firm, final verdict on "
    "which they can safely act. Public confidence, surveys suggest, tends to fall when experts "
    "revise their advice, as though a change of position were a confession of incompetence. Such "
    "impatience is understandable, for a society that must act on scientific findings naturally "
    "wants those findings to be settled. Even so, the expectation underneath it that science "
    "exists to hand us certainties rests on a deep misunderstanding of what science actually is. "
    "It is true, of course, that the practical authority of science is beyond serious dispute. "
    "The bridges we cross do not, as a rule, collapse; the medicines we swallow work, and "
    "measurably so. The aircraft, the antibiotics, and the satellites on which modern life "
    "depends were all built on scientific foundations, and no other way of investigating the "
    "world has produced results of comparable reliability. To deny this success would be absurd, "
    "and nothing that follows is meant to deny it. "
    "And yet the source of that success is precisely what the demand for certainty overlooks. "
    "Science is not a warehouse of finished truths, patiently accumulated and never to be touched "
    "again; it is a method a discipline of proposing hypotheses that could be wrong, exposing "
    "them to evidence, and revising or abandoning whatever fails the test. What makes a claim "
    "scientific is not that it is certain but that it is fallible in a controlled way: we know, "
    "at least in principle, what would prove it false. "
    "Seen from this angle, the familiar complaint turns upside down. When a researcher abandons a "
    "once-favoured position in the light of new evidence, this is not a symptom of failure but a "
    "sign that the method is doing exactly what it was designed to do. A field in which nobody "
    "ever changed their mind would be a field in which nothing was being tested; ideas would be "
    "defended, careers protected, and evidence, if consulted at all, consulted only for "
    "decoration. Individual scientists are seldom, if ever, free of vanity or bias but the system "
    "as a whole is arranged so that even a cherished theory must sooner or later answer to data "
    "it cannot explain. "
    "\"Then what are we supposed to believe?\" the frustrated reader may ask, and the question "
    "deserves a straight answer. If what you require is certainty, you must seek it outside "
    "science in mathematics, perhaps, or in faith because nothing that rests on evidence can be "
    "guaranteed never to change. What science offers instead is less comforting but more honest: "
    "probabilities, and provisional best explanations that stand only until something better "
    "survives the evidence. The choice we are so often presented with trust the experts blindly "
    "or fall back on gut feeling is therefore a false one. There is a third answer: trust the "
    "method itself, uncertainty included, for it is the only procedure we possess that "
    "systematically catches its own mistakes. "
    "This is why our anxiety about scientific uncertainty, however natural, aims at the wrong "
    "target. Uncertainty is not a weakness that science must apologize for; it is the very "
    "condition that makes science science, the price of a system in which evidence, not "
    "authority, has the final word. Remove it demand that every question be settled once and for "
    "all and what remains is no longer science but dogma wearing its costume. "
    "None of this means that every scientific claim is equally provisional, or that a finding "
    "announced yesterday deserves the confidence we grant a theory tested for a century. Evidence "
    "comes in different weights, and so, accordingly, should our trust. What we need to abandon "
    "is not science but the all-or-nothing demand we bring to it the assumption that whatever "
    "falls short of absolute certainty is worth nothing at all. To accept that the best available "
    "answer may still be revised, and to act on it anyway, is not a betrayal of reason; it is "
    "where an intelligent relationship with science begins."
)

# ------------------------------------------------------------------
# 設問 (問題編)
# ------------------------------------------------------------------
QUESTIONS = [
    {"no": "問1", "pts": "各4点",
     "stem": "空所【 A 】・【 B 】に入れるのに最も適切な語（句）を、それぞれ次の①〜④から一つ選べ。",
     "choices": [
         "【 A 】 &nbsp; ① Consequently &nbsp; ② For instance &nbsp; ③ In addition &nbsp; ④ Even so",
         "【 B 】 &nbsp; ① Accordingly &nbsp; ② By the same token &nbsp; ③ And yet &nbsp; ④ For example",
     ]},
    {"no": "問2", "pts": "8点",
     "stem": "下線部(3) <span class='en'>Uncertainty is not a weakness that science must "
             "apologize for; it is the very condition that makes science science, the price of "
             "a system in which evidence, not authority, has the final word.</span> を日本語に訳せ。",
     "choices": []},
    {"no": "問3", "pts": "8点",
     "stem": "下線部(1)について、研究者が新しい証拠に照らして見解を捨てることが「方法が設計どおりの仕事を"
             "していることの印（<span class='en'>a sign that the method is doing exactly what it was "
             "designed to do</span>）」であるとはどういうことか。本文に即して日本語で説明せよ。",
     "choices": []},
    {"no": "問4", "pts": "6点",
     "stem": "「科学者が見解を変えること」に関する本文の内容として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 科学者が見解を改めるのは、当初の研究の設計そのものに不誠実な点があったことを示すので、その分野への信頼を下げる十分な理由になる。",
         "② 見解の変更ができる科学者は、個人として虚栄心や偏見をすでに克服した人物であり、その人格的な成熟こそが科学の信頼性を支えている。",
         "③ 新しい証拠に照らして見解を改めることは失敗の兆候ではなく、仮説を検証し修正し続けるという科学の方法が機能していることの印である。",
         "④ 誰も一度も見解を変えたことのない分野こそ、検証がすべて完了した理想的な科学の姿であり、社会が最も信頼を寄せるべき分野である。",
     ]},
    {"no": "問5", "pts": "10点",
     "stem": "下線部(2)について、筆者によれば、科学が確実性の代わりに差し出すものは何か。本文に即して"
             "二つ挙げ、それぞれ日本語で説明せよ。",
     "choices": []},
    {"no": "問6", "pts": "8点",
     "stem": "筆者の主張として最も適切なものを、次の①〜④から一つ選べ。",
     "choices": [
         "① 不確実性は科学の欠陥ではなく、証拠によって誤りを見つけて修正し続ける方法としての科学を成り立たせる条件であり、「絶対か無か」という要求を捨てることが科学との知的な付き合いの出発点となる。",
         "② 科学の主張はどれも等しく暫定的であって、いつ覆るか分からないのだから、最終的に何を信じるかは専門家ではなく各人の直感に委ねるほかない、というのが筆者のたどり着いた結論である。",
         "③ 橋や薬などの実用的成功が証明するように、科学はすでに確実な真理の集積に到達しており、いまだに見解を変える科学者がいるのは方法ではなく個人の資質に問題があるからである。",
         "④ 科学は私たちに確実性を与えられない以上、数学や信仰と並ぶ選択肢の一つにすぎず、誤りを見つける手続きとして科学だけを特別扱いする理由はない、と筆者は主張している。",
     ]},
    {"no": "問7", "pts": "各4点",
     "stem": "本文の内容と一致するものを、次の①〜⑥から三つ選べ。",
     "choices": [
         "① 人々は専門家が助言を変えると科学への信頼を下げがちだが、その根底には科学は確実な答えをくれるはずだという期待がある。",
         "② 橋が落ちず薬が効くという実用的な成功は、科学が完成した真理の倉庫であることを裏づける動かぬ証拠だ、と筆者は述べている。",
         "③ 科学は最終的にはあらゆる誤りを完全に取り除き、二度と修正される必要のない知識に到達する、と筆者は考えている。",
         "④ どうしても確実性を求めるのであれば、数学や信仰など、科学の外部にそれを探すほかない、と筆者は述べている。",
         "⑤ 一度も見解の変更が起きたことのない分野は、検証がすべて完了した成熟した分野として信頼してよい、と本文は述べている。",
         "⑥ すべての科学的主張が同じ程度に暫定的なわけではなく、それを支える証拠の重みに応じて信頼の度合いにも差をつけるべきである。",
     ]},
]

# ------------------------------------------------------------------
# 解答・配点・記述解答例
# ------------------------------------------------------------------
ANSWERS_TABLE = [
    {"no": "問1", "pts": "各4点", "ans": "A ＝ ④ Even so　　B ＝ ③ And yet",
     "exp": "A：直前は「社会が確定した助言を望むのは当然（＝通念への理解）」、直後は「その期待は深い誤解に"
            "基づく（＝筆者の反転）」。譲歩を受けて反転する<b>逆接</b> → Even so（それでもなお）。"
            "Consequently（因果）・For instance（例示）・In addition（追加）はいずれも不成立。<br>"
            "B：第2段「It is true, of course, that …（＝実用的成功は認める）」の譲歩から、第3段「その成功の"
            "源こそ見落とされている」という主張へ<b>転換</b>する。逆接 → And yet。Accordingly（因果）・"
            "By the same token（類比）・For example（例示）は流れに合わない。 〔<b>解法ルール R7</b>／"
            "<b>読解ルール R1・R2</b>〕"},
    {"no": "問4", "pts": "6点", "ans": "③",
     "exp": "第4段の下線部(1)「this is not a symptom of failure but a sign that the method is doing "
            "exactly what it was designed to do」と一致。①は因果のすり替え（不誠実の証拠とは述べていない）。"
            "②はすり替え（第4段「Individual scientists are seldom, if ever, free of vanity or bias」＝個人は"
            "虚栄・偏見から自由になることはまずない、とむしろ逆）。④は逆転（同段「誰も意見を変えない分野＝"
            "何も検証されていない分野」）。 〔<b>解法ルール R9</b>〕"},
    {"no": "問6", "pts": "8点", "ans": "①",
     "exp": "第6段（下線部(3)）「不確実性は弱点ではなく科学を科学たらしめる条件」＋第5段「第三の答え＝不確実性"
            "込みで方法を信頼する」＋第7段最終文「『絶対か無か』を捨てることが知的な付き合いの始まり」と一致。"
            "②は「等しく暫定的」「直感に委ねる」がそれぞれ第7段冒頭・第5段の「偽の二択」に反する。③は第3段"
            "「完成した真理の倉庫ではない」に反し、個人の資質への<b>すり替え</b>。④は第5段「自らの誤りを組織的に"
            "捕まえる、私たちの持つ唯一の手続き」に反する。 〔<b>読解ルール R3・R24</b>／<b>解法ルール R9</b>〕"},
    {"no": "問7", "pts": "各4点", "ans": "①・④・⑥",
     "exp": "②×：第3段「Science is not a warehouse of finished truths」——成功の源は方法であり、「完成した"
            "真理の倉庫」の証拠ではない。③×：第5段「nothing that rests on evidence can be guaranteed never "
            "to change」に真っ向から反する（「完全に」「二度と」は<b>言い過ぎ</b>）。⑤×：第4段「誰も意見を"
            "変えない分野＝何も検証されていない分野」に反する。①は第1段、④は第5段、⑥は第7段と一致。"
            " 〔<b>解法ルール R9</b>：言い換えの見抜き＋「言い過ぎ」の排除〕"},
]

ANSWERS_WRITTEN = [
    {"no": "問2", "pts": "8点・下線部(3)和訳",
     "model": "不確実性は、科学が謝罪しなければならないような弱点ではない。それは、科学を科学たらしめている"
              "まさにその条件、すなわち、権威ではなく証拠が最終決定権を持つ仕組みの代価なのである。",
     "points": "▶<b>採点要素</b>：①<b>not A; it is B</b>＝「Aではない。（むしろ）Bだ」の対比構造（弱点の否定→"
               "条件そのもの）／②<b>makes science science</b>＝make O C「科学を科学たらしめる」の訳出／③the "
               "price of a system …＝the very condition の<b>同格</b>で、「<b>evidence, not authority</b>（権威では"
               "なく証拠）が最終決定権を持つ仕組みの代価」。挿入 not authority の対比を落とさない。 "
               "〔<b>読解ルール R3</b>／<b>構文ルール R17</b>〕"},
    {"no": "問3", "pts": "8点・記述",
     "model": "科学とは、誤りうる仮説を立てて証拠にさらし、検証に耐えないものを修正・放棄していく方法である"
              "から、研究者が新しい証拠に照らして従来の立場を捨てるのは失敗どころか、その検証と更新の仕組みが"
              "設計どおり正しく働いていることの表れだ、ということ。",
     "points": "▶<b>採点要素</b>：①科学＝<b>誤りうる仮説を証拠で検証し、更新し続ける方法</b>である（第3段）こと"
               "を前提として示す／②見解の変更＝失敗ではなく、その方法の<b>正常な作動</b>である（第4段）ことを"
               "説明／③「誰も意見を変えない分野＝何も検証されていない分野」（同段）との対比に触れられれば加点。 "
               "〔<b>読解ルール R3</b>／<b>解法ルール R8</b>〕"},
    {"no": "問5", "pts": "10点・記述",
     "model": "①確実な断定ではなく、どの程度確からしいかという形で示される確率。②よりよい説明が証拠による"
              "検証を生き延びて現れるまでのあいだだけ通用する、暫定的な最良の説明。",
     "points": "▶<b>採点要素</b>：下線部(2)の<b>コロン(:)以下が直前の言い換え</b>。①<b>probabilities</b>＝確率"
               "（5点）／②<b>provisional best explanations that stand only until something better survives "
               "the evidence</b>＝暫定的な最良の説明＋「よりよいものが証拠に耐えて現れるまで」という限定（5点）。"
               "限定を落とすと減点。 〔<b>解法ルール R8</b>：イコール関係（コロン）で核を作る〕"},
]

# ------------------------------------------------------------------
# この長文で使う The Rules（読解／解法／構文）
# ※トリリオン式に整理した読解ルール。関正生『The Rules』の“ルールで読む”手法に着想を得た当塾オリジナル。
# ------------------------------------------------------------------
RULES = {
    "読解ルール": [
        ("R1", "逆接（however / yet / but）の直後に筆者の主張が来る", "★★★",
         "空所A・B。第1段 Even so →「期待は誤解に基づく」、第3段 And yet →「成功の源こそ見落とされている」。"),
        ("R2", "It is true that … は譲歩の合図。直後の逆接（yet / but）で反転し主張を強める", "★★★",
         "第2段「It is true, of course, that …（実用的成功は認める）」→ 第3段 And yet で反転。"),
        ("R3", "not A but B / rather than は B の側が主張・核心", "★★★",
         "第3段 not a warehouse … ; it is a method、第6段 not a weakness … ; the very condition（下線部(3)）。"),
        ("R14", "反対意見・コスト批判への「再反論」は主張の強化——譲歩⇄再反論の往復を追う", "★★★",
         "第5段「では何を信じればいいのか」という反対視点を自ら取り上げ、正面から答えて主張を強める。"),
        ("R24", "★NEW AかBかの二項対立に筆者が第三の答えを出したら、それが核心", "★★★",
         "第5段「専門家を盲信するか、直感に戻るか」＝偽の二択 → 第三の答え「不確実性込みで方法を信頼する」が核心。"),
    ],
    "解法ルール": [
        ("R7", "空所補充（接続表現）は、前後の論理関係（逆接／因果／例示／追加）で決める", "★★★",
         "問1。前後がぶつかる＝逆接、順につながる＝因果／追加、具体が続く＝例示、並べる＝類比。"),
        ("R8", "記述説明・言い換え問題は、文脈の「イコール関係」で核を作る", "★★",
         "問3・問5。第5段のコロン(:)＝直前の言い換え、第3段のセミコロン・同格を利用。"),
        ("R9", "内容一致は本文の「言い換え」を見抜き、「言い過ぎ（all / never / completely）」を疑う", "★★★",
         "問4・問6・問7。問7③「完全に取り除き、二度と修正されない」は典型的な言い過ぎ。"),
    ],
    "構文ルール": [
        ("R17", "挿入（コンマに挟まれた researchers say / it seems 等）は括弧に入れて、先に文の骨格（SVOC）を取る", "★★★",
         "surveys suggest（第1段）／of course・as a rule（第2段）／however natural・not authority（第6段）。"),
        ("R25", "★NEW 省略——共通要素の省略は補って読む。if any / if ever は「あるとしても」", "★★★",
         "第4段 careers (would be) protected ／ evidence … (would be) consulted、if consulted at all、"
         "seldom, if ever。第7段 so should our trust (come in different weights)。"),
    ],
}

# ------------------------------------------------------------------
# 論理構造マップ
# ------------------------------------------------------------------
LOGIC_MAP = [
    {"role": "導入", "para": "¶1", "kind": "intro",
     "text": "通念「科学＝確実な答えをくれるもの。意見を変える専門家は信頼できない」。その苛立ちに理解を"
             "示した上で → <b>Even so（R1）</b>：その期待は「科学とは何か」への深い誤解に基づく。"},
    {"arrow": "↓"},
    {"role": "譲歩", "para": "¶2", "kind": "concession",
     "text": "<b>It is true, of course（R2）</b>：橋は落ちず、薬は効く。科学の実用的成功は疑いようがなく、"
             "以下の議論はそれを否定するものではない。＝通念の土台は認める。"},
    {"arrow": "◀ And yet 逆接（R1）で主張へ転換 ▶"},
    {"role": "主張転換", "para": "¶3", "kind": "claim",
     "text": "その成功の源こそが見落とされている。科学は<b>完成した真理の倉庫ではなく、誤りうる仮説を証拠で"
             "検証・更新し続ける方法（R3）</b>。科学的＝確実ではなく「統制されたやり方で誤りうる」こと。"},
    {"arrow": "↓　深化"},
    {"role": "深化", "para": "¶4", "kind": "reason",
     "text": "だから「科学者が意見を変えた」は失敗の印ではなく<b>方法が機能している印</b>（下線部(1)）。"
             "誰も意見を変えない分野＝何も検証されていない分野。個人は偏見を免れないが、システムが誤りを正す。"},
    {"arrow": "↓　反対視点への応答（R14）"},
    {"role": "再反論", "para": "¶5", "kind": "reason",
     "text": "「では何を信じれば？」→ 確実性が要るなら<b>科学の外</b>（数学・信仰）へ。科学が与えるのは"
             "<b>確率と暫定的な最良の説明</b>（下線部(2)）。「盲信か直感か」は偽の二択で、<b>第三の答え＝"
             "不確実性込みの方法への信頼（R24）</b>。"},
    {"arrow": "↓"},
    {"role": "★核心的主張", "para": "¶6", "kind": "core",
     "text": "<b>不確実性は弱点ではなく、科学を科学たらしめる条件（R3）</b>＝権威ではなく証拠が最終決定権を"
             "持つ仕組みの代価（下線部(3)）。それを取り除けば、残るのは科学の衣装をまとったドグマ。"},
    {"arrow": "↓"},
    {"role": "結論", "para": "¶7", "kind": "conclusion",
     "text": "譲歩つきまとめ：すべてが等しく暫定的なのではない——<b>証拠の重みに応じて信頼にも差</b>をつける。"
             "捨てるべきは科学ではなく<b>「絶対か無か」の要求</b>。修正されうる最良の答えに基づいて行動する"
             "ことこそ、科学との知的な付き合いの出発点。"},
]

# ------------------------------------------------------------------
# 図解 (SVGを build 側で生成。ここは説明文のみ)
# ------------------------------------------------------------------
FIGURES = [
    {"id": "fig1", "title": "図1 ｜ 科学への二つの見方",
     "caption": "通念は科学を<b>「完成した真理の倉庫」</b>とみなすので、専門家が意見を変えるたびに信頼が"
                "崩れる。実像は<b>「誤りうる仮説を証拠で更新し続ける方法」</b>なので、意見の変化はむしろ"
                "方法が機能している印になる。",
     "para": "→ 第1・3・4段"},
    {"id": "fig2", "title": "図2 ｜ 科学が与えるもの（＝確実性の代わりに）",
     "caption": "下線部(2)のコロン以下が答え。科学が差し出すのは①<b>確率</b>と②<b>暫定的な最良の説明</b>の"
                "二つで、どちらも「確実な断定」ではない。問5はこの二つを説明する。",
     "para": "→ 第5段"},
    {"id": "fig3", "title": "図3 ｜ 核心 — 不確実性は「弱点」ではなく「条件」",
     "caption": "不確実性は科学の欠陥ではなく、<b>権威ではなく証拠が最終決定権を持つ仕組みの代価</b>であり、"
                "科学を科学たらしめる条件そのもの。「絶対か無か」の二択を捨てることが出発点。",
     "para": "→ 第6〜7段"},
]

# ------------------------------------------------------------------
# 全訳
# ------------------------------------------------------------------
TRANSLATION = [
    (1, "人々が科学に頼るとき、たいてい求めているのは答え——安心してそれに基づいて行動できる、確固たる最終"
        "判決——である。世間の信頼は、調査が示すところでは、専門家が助言を修正すると下がりがちだ。まるで立場を"
        "変えることが、無能の告白ででもあるかのように。こうした苛立ちは理解できる。科学の知見に基づいて行動"
        "しなければならない社会が、その知見には確定していてほしいと望むのは当然だからである。<b>それでもなお</b>、"
        "その底にある期待——科学は私たちに確実性を手渡すために存在する、という期待——は、科学が実際には何で"
        "あるのかについての深い誤解の上に成り立っている。"),
    (2, "もちろん、科学の実用的な権威にまじめな論争の余地がないことは、本当である。私たちが渡る橋は、めったな"
        "ことでは崩れない。私たちが飲む薬は効く——しかも、測定できるほどはっきりと。現代の生活が依存する航空機も"
        "抗生物質も人工衛星も、みな科学の土台の上に築かれたものであり、世界を調べる他のいかなる方法も、これに"
        "匹敵する信頼性の結果を生み出してはいない。この成功を否定するとすれば馬鹿げたことだろうし、これから"
        "述べることのどれにも、それを否定する意図はない。"),
    (3, "<b>それでもなお</b>、その成功の源こそ、確実性への要求が見落としているものにほかならない。科学は、辛抱強く"
        "蓄積され二度と手を触れられることのない、完成した真理の倉庫ではない。それは方法——誤っているかもしれない"
        "仮説を立て、それを証拠にさらし、検証に耐えないものを修正あるいは放棄していく営み——である。ある主張を"
        "科学的なものにするのは、それが確実だということではなく、統制されたやり方で誤りうるということだ。すなわち"
        "私たちは、少なくとも原理的には、何がその主張を偽と証明することになるのかを知っているのである。"),
    (4, "この角度から見ると、おなじみの不満はひっくり返る。<b>研究者が新しい証拠に照らして、かつて支持していた"
        "立場を捨てるとき、それは失敗の兆候ではなく、方法がまさに設計されたとおりの仕事をしていることの印なので"
        "ある。</b>誰も決して意見を変えない分野があるとすれば、それは何も検証されていない分野だろう。そこでは考えは"
        "擁護され、経歴は守られ、証拠は——仮に参照されるとしても——飾りのためだけに参照されるだろう。個々の科学者が"
        "虚栄心や偏見と無縁であることは、あるとしてもめったにない。だがシステム全体は、どれほど大切にされている"
        "理論であっても、遅かれ早かれ、自らには説明できないデータに向き合わねばならないように組み立てられて"
        "いるのだ。"),
    (5, "「では、私たちは何を信じればよいのか」。苛立った読者はそう尋ねるかもしれないし、この問いは率直な答えに"
        "値する。あなたの求めるものが確実性であるなら、それは科学の外に——おそらくは数学に、あるいは信仰に——探す"
        "しかない。証拠の上に成り立つものは何ひとつ、決して変わらないと保証されえないからだ。<b>科学が代わりに"
        "差し出すのは、より心安らぐものではないが、より誠実なもの、すなわち確率と、よりよいものが証拠による検証を"
        "生き延びて現れるまでのあいだだけ通用する、暫定的な最良の説明である。</b>したがって、私たちがしばしば突き"
        "つけられる二者択一——専門家を盲信するか、直感に立ち戻るか——は、偽の二択である。第三の答えがあるのだ。"
        "すなわち、不確実性も込みで、方法そのものを信頼すること。それは、自らの誤りを組織的に捕まえる、私たちの"
        "持つ唯一の手続きなのだから。"),
    (6, "こういうわけで、科学の不確実性をめぐる私たちの不安は——それがどれほど自然なものであっても——誤った標的を"
        "狙っている。<b>不確実性は、科学が謝罪しなければならないような弱点ではない。それは、科学を科学たらしめて"
        "いるまさにその条件、すなわち、権威ではなく証拠が最終決定権を持つ仕組みの代価なのである。</b>それを取り"
        "除いてみればよい——あらゆる問いがきっぱりと最終的に確定されることを要求してみればよい。そのとき残って"
        "いるのは、もはや科学ではなく、科学の衣装をまとった教義（ドグマ）である。"),
    (7, "とはいえ以上のことは、あらゆる科学的主張が等しく暫定的だという意味でも、昨日発表された知見が、一世紀に"
        "わたって検証されてきた理論に与えるのと同じ信頼に値するという意味でもない。証拠にはさまざまな重みがあり、"
        "したがって私たちの信頼にも、それに応じた差があってしかるべきなのだ。捨てる必要があるのは科学ではなく、"
        "私たちが科学に持ち込む「絶対か無か」の要求——絶対の確実性に届かないものには何の価値もない、という思い"
        "込み——である。現時点で得られる最良の答えがなお修正されうると認め、それでもその答えに基づいて行動する"
        "こと。それは理性への裏切りではなく、そこからこそ、科学との知的な付き合いが始まるのである。"),
]

# ------------------------------------------------------------------
# 重要語彙
# ------------------------------------------------------------------
VOCAB = [
    ("verdict", "評決、（最終的な）判断"),
    ("act on ~", "〜に基づいて行動する"),
    ("revise", "修正する、改訂する"),
    ("incompetence", "無能"),
    ("settled", "確定した、決着済みの"),
    ("as a rule", "概して、普通は"),
    ("measurably", "測定できるほど（はっきりと）"),
    ("comparable", "匹敵する、同等の"),
    ("overlook", "見落とす"),
    ("hypothesis（複 hypotheses）", "仮説"),
    ("fallible", "誤りうる"),
    ("in principle", "原理的には"),
    ("in the light of ~", "〜に照らして"),
    ("seldom, if ever", "（あるとしても）めったに〜ない"),
    ("vanity", "虚栄心"),
    ("cherished", "大切にされている"),
    ("provisional", "暫定的な"),
    ("fall back on ~", "〜に頼る、〜に立ち戻る"),
    ("gut feeling", "直感"),
    ("once and for all", "きっぱりと、これを最後に"),
    ("dogma", "教義、ドグマ"),
    ("fall short of ~", "〜に達しない、〜に届かない"),
    ("betrayal", "裏切り"),
]

# ------------------------------------------------------------------
# SVOC 構文解説
#   各段落: head + sentences[]
#   sentence: {"chunks": [(tag, en, ja), ...], "note": "..."}
#   tag: S V O C M 接 - （- は同格・その他）
# ------------------------------------------------------------------
SVOC = [
 {"head": "第1段 — 導入：確実性への期待と、その反転（Even so）",
  "sentences": [
    {"chunks": [("M","(When people turn to science),","人々が科学に頼るとき"),
                ("S","[what they usually want]","彼らがたいてい求めているものは"),
                ("V","is","である"),("C","an answer","答え"),
                ("-","&mdash; a firm, final verdict &lt;on which they can safely act&gt;.","——すなわち、安心してそれに基づいて行動できる、確固たる最終判決")],
     "note":"▶ 関係代名詞 <b>what</b>＝「〜するもの」（名詞節が主語）。ダッシュ以下は an answer の<b>同格</b>（言い換え）。"
            "on which … act＝前置詞＋関係代名詞（act on ~「〜に基づいて行動する」）。"},
    {"chunks": [("S","Public confidence,","世間の信頼は"),
                ("M","surveys suggest,","——調査が示すところでは——"),
                ("V","tends to fall","下がりがちである"),
                ("M","(when experts revise their advice),","専門家が助言を修正すると"),
                ("M","(as though a change of position were a confession of incompetence).","まるで立場の変更が無能の告白であるかのように")],
     "note":"▶ <b>R17｜挿入 surveys suggest を括弧に入れ、骨格（confidence tends to fall）を先に取る</b>。"
            "as though＋仮定法過去 were＝「まるで〜であるかのように」。"},
    {"chunks": [("S","Such impatience","そうした苛立ちは"),("V","is","である"),("C","understandable,","理解できるもの"),
                ("接","for","というのも"),
                ("S","a society &lt;that must act on scientific findings&gt;","科学の知見に基づいて行動しなければならない社会は"),
                ("M","naturally","当然"),("V","wants","望むからだ"),
                ("O","those findings","その知見が"),("C","to be settled.","確定していることを")],
     "note":"▶ 等位接続詞 <b>for</b>＝「というのも〜だから」（理由を後ろから添える）。want O to do＝「Oに〜してほしい」。"
            "通念に理解を示す＝譲歩の身振り。"},
    {"chunks": [("接","Even so,","それでもなお"),
                ("S","the expectation &lt;underneath it&gt;","その底にある期待は"),
                ("-","&mdash; [that science exists to hand us certainties] &mdash;","——科学は私たちに確実性を手渡すために存在する、という——"),
                ("V","rests on","基づいている"),
                ("O","a deep misunderstanding (of [what science actually is]).","科学が実際には何であるかについての深い誤解に")],
     "note":"▶ <b>R1｜逆接 Even so の直後が筆者の主張</b>（＝空所A）。that … certainties＝the expectation の"
            "<b>同格の that 節</b>（「〜という期待」）。rest on ~＝「〜に基づく」。"},
  ]},
 {"head": "第2段 — 譲歩：実用的成功は疑いようがない（It is true, of course）",
  "sentences": [
    {"chunks": [("S","It","（形式主語）"),("V","is","である"),("C","true,","本当"),
                ("M","of course,","もちろん"),
                ("-","[that the practical authority of science is beyond serious dispute].","科学の実用的権威にまじめな論争の余地がない、ということは")],
     "note":"▶ <b>R2｜It is true that … は譲歩の合図</b>（第3段 And yet で反転する前振り）。of course も譲歩の目印"
            "（<b>R17</b>挿入）。beyond dispute＝「議論の余地がない」。"},
    {"chunks": [("S","The bridges &lt;(that) we cross&gt;","私たちが渡る橋は"),
                ("V","do not, (as a rule), collapse;","（概して）崩れない"),
                ("S","the medicines &lt;(that) we swallow&gt;","私たちが飲む薬は"),
                ("V","work,","効く"),
                ("M","and measurably so.","しかも、測定できるほどはっきりと")],
     "note":"▶ 関係詞省略×2（bridges (that) we cross／medicines (that) we swallow）。as a rule＝挿入（<b>R17</b>）。"
            "so＝work の代用（「そのように＝はっきりと効く」）。セミコロンで対句。"},
    {"chunks": [("S","The aircraft, the antibiotics, and the satellites &lt;on which modern life depends&gt;","現代の生活が依存する航空機・抗生物質・人工衛星は"),
                ("V","were all built","みな築かれた"),
                ("M","(on scientific foundations),","科学の土台の上に"),
                ("接","and","そして"),
                ("S","no other way (of investigating the world)","世界を調べる他のいかなる方法も"),
                ("V","has produced","生み出してはいない"),
                ("O","results (of comparable reliability).","これに匹敵する信頼性の結果を")],
     "note":"▶ on which＝前置詞＋関係代名詞（depend on ~）。<b>no other ＋名詞</b>＝否定の主語「他のどの〜も…ない」"
            "（＝科学の比類なさを裏から言う）。"},
    {"chunks": [("S","To deny this success","この成功を否定することは"),
                ("V","would be","だろう"),("C","absurd,","馬鹿げたこと"),
                ("接","and","そして"),
                ("S","nothing &lt;that follows&gt;","これから述べることのどれも"),
                ("V","is meant to deny","否定する意図はない"),("O","it.","それを")],
     "note":"▶ 不定詞主語＋<b>would</b>＝「（否定するとすれば）〜だろう」の仮定の含み。be meant to do＝「〜する"
            "ことを意図されている」。譲歩の駄目押し。"},
  ]},
 {"head": "第3段 — 主張転換：科学は「真理の倉庫」ではなく「方法」（And yet）",
  "sentences": [
    {"chunks": [("接","And yet","それでもなお"),
                ("S","the source (of that success)","その成功の源こそ"),
                ("V","is","である"),("M","precisely","まさに"),
                ("C","[what the demand for certainty overlooks].","確実性への要求が見落としているもの")],
     "note":"▶ <b>R1｜And yet＝逆接でここが主張転換点</b>（＝空所B）。第2段の譲歩を受けて反転。関係代名詞 what"
            "（overlooks の目的語が欠けた名詞節）。"},
    {"chunks": [("S","Science","科学は"),("V","is","ではない"),
                ("C","not a warehouse of finished truths, &lt;patiently accumulated and never to be touched again&gt;;","辛抱強く蓄積され、二度と手を触れられることのない「完成した真理の倉庫」では"),
                ("S","it","それは"),("V","is","である"),("C","a method","方法"),
                ("-","&mdash; a discipline of proposing hypotheses &lt;that could be wrong&gt;, exposing them to evidence, and revising or abandoning [whatever fails the test].","——誤っているかもしれない仮説を立て、それを証拠にさらし、検証に耐えないものは何であれ修正・放棄していく営み")],
     "note":"▶ <b>R3｜not A; it is B ＝ B が核心</b>（倉庫ではなく方法）。accumulated／never to be touched＝"
            "warehouse への後置修飾。proposing／exposing／revising or abandoning＝三つの動名詞の並列。"
            "whatever＝複合関係代名詞「〜するものは何でも」。"},
    {"chunks": [("S","[What makes a claim scientific]","ある主張を科学的なものにするのは"),
                ("V","is","である"),
                ("C","not [that it is certain] but [that it is fallible in a controlled way]:","それが確実だということではなく、統制されたやり方で誤りうるということ"),
                ("S","we","私たちは"),("V","know,","知っている"),
                ("M","at least in principle,","少なくとも原理的には"),
                ("O","[what would prove it false].","何がその主張を偽と証明することになるかを")],
     "note":"▶ <b>R3｜not A but B</b>：科学的＝「確実」ではなく「統制された誤りやすさ」。make O C（makes a claim "
            "scientific）。<b>コロン(:)＝直前の言い換え</b>（R8で使う）。at least in principle＝挿入（<b>R17</b>）。"},
  ]},
 {"head": "第4段 — 深化：意見を変える＝方法が機能している印（下線部(1)）",
  "sentences": [
    {"chunks": [("M","(Seen from this angle),","この角度から見ると"),
                ("S","the familiar complaint","おなじみの不満は"),
                ("V","turns upside down.","ひっくり返る")],
     "note":"▶ 過去分詞の分詞構文 <b>Seen from ~</b>＝「〜から見ると」（＝If it is seen from ~ の省略形）。"},
    {"chunks": [("M","(When a researcher abandons a once-favoured position in the light of new evidence),","研究者が新しい証拠に照らして、かつて支持していた立場を捨てるとき"),
                ("S","this","これは"),("V","is","である"),
                ("C","not a symptom of failure but a sign","失敗の兆候ではなく、印"),
                ("-","[that the method is doing exactly what it was designed to do].","方法が、まさに設計されたとおりの仕事をしている、という")],
     "note":"▶ <b>R3｜not A but B</b>。a sign <b>that</b> …＝<b>同格の that 節</b>「〜という印」。in the light of ~＝"
            "「〜に照らして」。once-favoured＝「かつて支持された」。＝<b>下線部(1)＝問3</b>。"},
    {"chunks": [("S","A field &lt;in which nobody ever changed their mind&gt;","誰も決して意見を変えない分野は"),
                ("V","would be","だろう"),
                ("C","a field &lt;in which nothing was being tested&gt;;","何も検証されていない分野"),
                ("S","ideas","考えは"),("V","would be defended,","擁護され"),
                ("S","careers","経歴は"),("V","protected,","守られ（るだろう）"),
                ("S","and evidence,","そして証拠は"),
                ("M","(if consulted at all),","仮に参照されるとしても"),
                ("V","consulted","参照される（だろう）"),
                ("M","only for decoration.","飾りのためだけに")],
     "note":"▶ <b>R25｜共通要素の省略を補う</b>：careers <b>(would be)</b> protected／evidence <b>(would be)</b> "
            "consulted。if consulted at all＝<b>if (it is) consulted at all</b>「仮に参照されるとしても」。"
            "would＝仮定法（実在しない分野の想定）。"},
    {"chunks": [("S","Individual scientists","個々の科学者は"),
                ("V","are","である"),
                ("M","seldom, if ever,","めったに——あるとしても——〜ない"),
                ("C","free of vanity or bias","虚栄心や偏見と無縁"),
                ("接","&mdash; but","——だが"),
                ("S","the system as a whole","システム全体は"),
                ("V","is arranged","組み立てられている"),
                ("M","(so that even a cherished theory must sooner or later answer to data &lt;(that) it cannot explain&gt;).","どれほど大切にされている理論でも、遅かれ早かれ、自らには説明できないデータに向き合わねばならないように")],
     "note":"▶ <b>R25｜seldom, if ever ＝「あるとしてもめったに〜ない」</b>。so that ＋ must＝「〜するように」"
            "（目的・帰結）。data (that) it cannot explain＝関係詞省略。個人の弱さ vs システムの強さの対比。"},
  ]},
 {"head": "第5段 — 再反論と第三の答え：確率と暫定的な最良の説明（下線部(2)）",
  "sentences": [
    {"chunks": [("O","&ldquo;Then what are we supposed to believe?&rdquo;","「では、私たちは何を信じればよいのか」と"),
                ("S","the frustrated reader","苛立った読者は"),
                ("V","may ask,","尋ねるかもしれない"),
                ("接","and","そして"),
                ("S","the question","その問いは"),("V","deserves","値する"),
                ("O","a straight answer.","率直な答えに")],
     "note":"▶ 引用文＝ask の目的語が文頭に出た形。be supposed to do＝「〜することになっている」。"
            "<b>R14｜反対視点を自ら取り上げ、以下で正面から答える（再反論）</b>。"},
    {"chunks": [("M","(If [what you require] is certainty),","あなたの求めるものが確実性であるなら"),
                ("S","you","あなたは"),("V","must seek","探さねばならない"),("O","it","それを"),
                ("M","(outside science) &mdash; in mathematics, perhaps, or in faith &mdash;","科学の外に——おそらくは数学に、あるいは信仰に——"),
                ("M","(because nothing &lt;that rests on evidence&gt; can be guaranteed never to change).","証拠の上に成り立つものは何ひとつ、決して変わらないと保証されえないのだから")],
     "note":"▶ <b>R14｜再反論①</b>：確実性が要るなら科学の外へ。nothing that … can be guaranteed＝否定主語。"
            "guarantee O never to do の受動＝「決して〜しないと保証する」。<b>R9注意</b>：問7③「二度と修正されない"
            "知識に到達」はこの文で反駁できる。"},
    {"chunks": [("S","[What science offers instead]","科学が代わりに差し出すものは"),
                ("V","is","である"),
                ("C","less comforting but more honest:","より心安らぐものではないが、より誠実なもの"),
                ("-","probabilities, and provisional best explanations &lt;that stand only until something better survives the evidence&gt;.","すなわち、確率と、よりよいものが証拠（の検証）を生き延びるまでのあいだだけ通用する、暫定的な最良の説明")],
     "note":"▶ <b>R8｜コロン(:)＝直前の言い換え</b>：less comforting but more honest の中身＝①確率 ②暫定的な"
            "最良の説明。that stand only until ~＝関係詞節「〜までのあいだだけ有効な」。＝<b>下線部(2)＝問5</b>。"},
    {"chunks": [("S","The choice &lt;(that) we are so often presented with&gt;","私たちがしばしば突きつけられる二択は"),
                ("-","&mdash; trust the experts blindly or fall back on gut feeling &mdash;","——専門家を盲信するか、直感に立ち戻るか——"),
                ("V","is","である"),("M","therefore","したがって"),
                ("C","a false one.","偽の二択")],
     "note":"▶ <b>R24｜「AかBか」の二項対立を筆者自身が「偽の二択（a false one）」と斥ける</b>——次文の第三の答えが"
            "核心になる合図。present A with B の受動＋関係詞省略。one＝choice の代用。"},
    {"chunks": [("V","There is","ある"),("S","a third answer:","第三の答えが"),
                ("-","trust the method itself, (uncertainty included),","すなわち——不確実性も込みで——方法そのものを信頼せよ"),
                ("接","for","というのも"),
                ("S","it","それは"),("V","is","だからだ"),
                ("C","the only procedure &lt;we possess&gt; &lt;that systematically catches its own mistakes&gt;.","自らの誤りを組織的に捕まえる、私たちの持つ唯一の手続き")],
     "note":"▶ <b>R24｜第三の答え＝本文の核心</b>：不確実性込みの「方法への信頼」。uncertainty included＝独立分詞"
            "構文的な付帯「不確実性を含めて」。the only procedure に <b>we possess／that … catches</b> の二重の"
            "修飾。for＝理由の等位接続詞。"},
  ]},
 {"head": "第6段 — 核心：不確実性は科学を科学たらしめる条件（下線部(3)）",
  "sentences": [
    {"chunks": [("M","This is why","こういうわけで"),
                ("S","our anxiety (about scientific uncertainty),","科学の不確実性をめぐる私たちの不安は"),
                ("M","(however natural),","どれほど自然なものであっても"),
                ("V","aims at","狙っている"),
                ("O","the wrong target.","誤った標的を")],
     "note":"▶ This is why SV＝「こういうわけでSはVする」。<b>R25｜however natural＝however natural (it may be) "
            "の省略</b>（譲歩の挿入、<b>R17</b>）。"},
    {"chunks": [("S","Uncertainty","不確実性は"),
                ("V","is","ではない"),
                ("C","not a weakness &lt;that science must apologize for&gt;;","科学が謝罪しなければならない弱点では"),
                ("S","it","それは"),("V","is","である"),
                ("C","the very condition &lt;that makes science science&gt;,","科学を科学たらしめる、まさにその条件"),
                ("-","the price of a system &lt;in which evidence, (not authority), has the final word&gt;.","——権威ではなく証拠が最終決定権を持つ仕組みの、代価")],
     "note":"▶ <b>R3｜not A; it is B</b>：弱点の否定→条件そのもの。<b>make O C</b>（makes science science＝「科学を"
            "科学たらしめる」）。the price …＝the very condition の<b>同格</b>。evidence, not authority＝挿入の対比"
            "（<b>R17</b>）。＝<b>下線部(3)＝問2</b>。"},
    {"chunks": [("V","Remove","取り除いてみよ"),("O","it","それを"),
                ("-","&mdash; demand [that every question be settled once and for all] &mdash;","——あらゆる問いがきっぱりと最終的に確定されることを要求してみよ——"),
                ("接","and","そうすれば"),
                ("S","[what remains]","残るものは"),
                ("V","is","である"),
                ("C","no longer science but dogma &lt;wearing its costume&gt;.","もはや科学ではなく、科学の衣装をまとった教義（ドグマ）")],
     "note":"▶ <b>命令文＋and</b>＝「〜せよ、そうすれば…」。demand that S ＋<b>原形 be</b>＝仮定法現在。"
            "no longer A but B＝R3型の対比。wearing its costume＝dogma への分詞修飾（its＝science's）。"},
  ]},
 {"head": "第7段 — 譲歩つき結論：「絶対か無か」を捨てる（証拠の重みに差）",
  "sentences": [
    {"chunks": [("S","None of this","以上のどれも"),
                ("V","means","意味しない"),
                ("O","[that every scientific claim is equally provisional],","あらゆる科学的主張が等しく暫定的だとは"),
                ("接","or","また〜も"),
                ("O","[that a finding &lt;announced yesterday&gt; deserves the confidence &lt;we grant a theory tested for a century&gt;].","昨日発表された知見が、一世紀検証されてきた理論に与えるのと同じ信頼に値するとも")],
     "note":"▶ None of this means that …, or that …＝譲歩つき結論の型。announced／tested＝過去分詞の後置修飾。"
            "grant O1 O2＝「O1にO2を与える」（the confidence (that) we grant a theory＝関係詞省略）。"
            "<b>R9注意</b>：問6②「等しく暫定的」はこの文で反駁。"},
    {"chunks": [("S","Evidence","証拠は"),
                ("V","comes","現れる"),
                ("M","(in different weights),","さまざまな重みを伴って"),
                ("接","and","そして"),
                ("M","so, (accordingly),","それに応じて〜もまたそうであるべきだ"),
                ("V","should","（そうある）べきである"),
                ("S","our trust.","私たちの信頼も")],
     "note":"▶ <b>so ＋ 助動詞 ＋ 主語の倒置</b>＝「〜もまたそうだ」。<b>R25｜should の後ろは come in different "
            "weights の省略</b>＝「信頼にも（証拠の重みに応じた）差があるべきだ」。accordingly＝挿入（<b>R17</b>）。"},
    {"chunks": [("S","[What we need to abandon]","私たちが捨てる必要があるものは"),
                ("V","is","である"),
                ("C","not science but the all-or-nothing demand &lt;(that) we bring to it&gt;","科学ではなく、私たちが科学に持ち込む「絶対か無か」の要求"),
                ("-","&mdash; the assumption [that whatever falls short of absolute certainty is worth nothing at all].","——絶対の確実性に届かないものには何の価値もない、という思い込み")],
     "note":"▶ <b>R3｜not A but B</b>：捨てるのは科学ではなく「絶対か無か」の要求。the assumption <b>that</b>＝同格。"
            "whatever falls short of ~＝「〜に届かないものは何でも」。be worth nothing＝「何の価値もない」。"},
    {"chunks": [("S","To accept [that the best available answer may still be revised], and to act on it anyway,","現時点で得られる最良の答えがなお修正されうると認め、それでもその答えに基づいて行動することは"),
                ("V","is","ではない"),
                ("C","not a betrayal of reason;","理性への裏切りでは"),
                ("S","it","それは"),("V","is","である"),
                ("C","[where an intelligent relationship with science begins].","科学との知的な付き合いが始まる地点")],
     "note":"▶ 不定詞主語の並列（To accept … and to act …）。<b>R3｜not A; it is B</b> が最終文でも反復——文章全体の"
            "締めくくり。where 節＝補語になる名詞節「〜する所」。"},
  ]},
]

# 各文に付ける「論理の目印」チップ。キー=(段, 文番号) いずれも1始まり。無い文はチップなし。
# ★実データの文順と必ず照合すること(第1段=4文/第2段=4文/第3段=3文/第4段=4文/第5段=5文/第6段=3文/第7段=4文)
SVOC_LOGIC = {
    (1, 3): "譲歩", (1, 4): "対比",                       # s3 苛立ちに理解 / s4 Even so→反転
    (2, 1): "譲歩", (2, 4): "譲歩",                       # s1 It is true / s4 駄目押し
    (3, 1): "対比", (3, 2): "主張", (3, 3): "主張",       # s1 And yet転換 / s2 倉庫でなく方法 / s3 誤りうること=科学的
    (4, 1): "対比", (4, 2): "主張", (4, 3): "因果", (4, 4): "対比",
    (5, 1): "譲歩", (5, 2): "因果", (5, 3): "主張", (5, 4): "対比", (5, 5): "主張",
    (6, 1): "因果", (6, 2): "主張", (6, 3): "因果",
    (7, 1): "譲歩", (7, 2): "主張", (7, 3): "主張", (7, 4): "主張",
}
