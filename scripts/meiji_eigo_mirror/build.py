# -*- coding: utf-8 -*-
"""
明治大学2026 英語 実戦問題（第1問=長文読解）ビルダ
- 実物構成: 1本の長文に対しマーク式24問(1-24)+記述式6問(A-F)、60分。
- 本文は著作権配慮で完全オリジナル(テーマ並行: 難民の少女が言語とスポーツを学び、移住抽選で寒冷国へ)。
- 出力: 問題編HTML/解答編HTML -> Chrome --print-to-pdf。
"""
import os, subprocess

OUT = os.path.expanduser("~/Desktop/明治大学2026_英語実戦問題")
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))

MARU = ["①","②","③","④","⑤","⑥","⑦"]

# ============================================================
# 本文（オリジナル）。空所=(n)、番号下線=<u>..</u><sup>(n)</sup>、
# 記述下線=<u class=L>..</u><sup>(A)</sup>、空所F=(F)。
# ============================================================
def bk(label):   # 空所ボックス
    return f'<span class="bk">(&nbsp;{label}&nbsp;)</span>'
def ul(word, n): # 番号付き下線（マーク設問用）
    return f'<u>{word}</u><sup class="qn">({n})</sup>'
def ulL(word, L):# 記述設問用下線(A-F)
    return f'<u class="L">{word}</u><sup class="qL">({L})</sup>'

PARAS = [
 f"""Nadia was fifteen years old. For the past three years she had been living in refugee camps near the border &mdash; first at a camp called Toref, and then at a larger one called Bela.""",

 f"""Toref had been a miserable place, set down in the middle of a flat, dusty plain. A high fence of wire ran around the whole camp, and you were not allowed to step outside {bk(1)} you were leaving for good. To Nadia it felt almost like a cage. More than forty thousand people lived at Toref, though some said the true number was far higher. A few families had managed to escape the fighting together, but most of the people in the camp, like Nadia herself, were children who had lost their parents.""",

 f"""The villagers who farmed the land nearby did not want the camp so close to their fields. After dark they would sometimes slip in and carry off whatever they could [&hellip;].""",

 f"""One afternoon Nadia heard {bk(2)} another camp, far away to the west, where &mdash; people whispered &mdash; the food was better and there were real schools. With a group of others she walked for six days to reach it. But when they arrived at Bela, they found that {ul('things',3)} were no different from before. Many people here had been {ulL('injured','A')} on the long road, and almost every week Nadia heard of others who had been hurt or even killed in the fighting they had fled.""",

 f"""Still, Nadia refused to give up the one thought that kept her going: that one day she might {bk(4)} the camp and go on with her education somehow.""",

 f"""At Bela the days were long and empty. There was nothing to do {bk(5)} wait &mdash; wait for the next meal, wait for news, wait for the war to end. It was hard to keep hope alive when there was so little to {bk(6)} it. People said you might stay for a few weeks or, {bk(7)}, a few months; Nadia had already been waiting for years.""",

 f"""Then she met Joseph. Joseph was a quiet young man who had once trained to be a teacher. He almost {bk(8)}, even when her words came out wrong.""",

 f"""Every evening he sat with her and a handful of other children, practicing {bk(9)} the letters in the dust with a stick. Nadia already knew how to read in her mother tongue. The {bk(10)} she had grown up with had thirty-two letters, while the English one had only twenty-six, so at first the new shapes looked strange to her.""",

 f"""Joseph was patient. When Nadia confused two letters that looked alike, he would point out some small difference so that it was easy to {ul('tell',11)} them apart. &ldquo;It is good to rest your eyes now and then,&rdquo; he said one evening, standing up to stretch. &ldquo;Come &mdash; it is good to take a break {ulL('from work','B')}.&rdquo; He led her to a bare patch of ground where a bent hoop hung from a wooden post, and tossed her a worn ball. &ldquo;I&rsquo;m thinking {ulL("you&rsquo;ll be good at this",'C')} &mdash; you are tall for your age.&rdquo;""",

 f"""So Nadia learned two things from Joseph: how to read, and how to play basketball.""",

 f"""The talk of resettlement began as a {bk('12-ア')}, but within days it had grown into a {bk('12-イ')} that filled every corner of the camp: a distant country called Canada was going to take in some of the young people orphaned by the war.""",

 f"""The camp office began to post lists of names &mdash; the people who would be sent abroad. Nadia pushed her way to the front of the crowd, but her name was not there. {bk(13)} was it on the next list, or the one after that.""",

 f"""Each time a fresh list went up, she felt she was being {ulL('torn','D')} in two by the hoping and the not-hoping. She would race to the board, then slow down and try to catch her {ul('breath',14)} before she let herself look.""",

 f"""&ldquo;I will not look too quickly,&rdquo; she would tell herself, though {ul('her hands were shaking',15)}.""",

 f"""At last, on a gray morning, Nadia {bk(16)} her way through the crowd until she was standing right in front of the newest list. And there, halfway down, was her own name.""",

 f"""The journey took three flights. The first, in a tiny, rattling plane, frightened her so badly that she was sure they would drop out of the sky. So when the second plane left the ground, Nadia {ul('gripped the armrests with all her strength',17)} and shut her eyes.""",

 f"""On the {bk(18)} to the city where her new family lived, she looked down for hours at a floor of white cloud, and the mood among the passengers was oddly cheerful.""",

 f"""At the airport she could not help {ul('studying',19)} the families who waited beyond the gate, wondering which of them might be hers. <em>What if my new family isn&rsquo;t here?</em> she thought. <em>What if {ulL('they have changed their minds','E')}? What if they meet me and decide they do not like me?</em>""",

 f"""Then she saw a man and a woman holding a card with her name on it, and two small children bouncing at their side. She felt her shoulders drop a little at the sight of {ul('their eager smiles',20)}. She wondered {bk(21)} she looked as frightened as she felt.""",

 f"""On the drive from the airport the woman said, with a laugh, that in this country people did not sit still through the long winter; out of doors they {ul('stayed on the move',22)} all season &mdash; skating, sledding, walking to school in the dark. Nadia could hardly believe it.""",

 f"""{bk('23-ア')} the airport, she thought, felt like {bk('23-イ')} her old life behind forever &mdash; the camp, the dusty plain, the faces she might never see again.""",

 f"""Outside, the glass doors slid open and the winter air struck her like a wall of ice. Never {bk('F')} she felt anything so cold. But Nadia pulled her thin coat tight, wiped her eyes, and took her first step out into the snow.""",
]

SOURCE_NOTE = "（注）本文中の [&hellip;] は省略を示す。sledding = そり遊び（雪ぞりで滑る遊び）。本問題は明治大学2026年度英語の出題形式に準拠して作成したオリジナル問題であり、実際の入試問題の文章とは異なります。"

LEAD = ("以下の英文は、内戦によって故郷を追われ、難民キャンプで暮らした少女 Nadia について書かれた文章である。"
        "これを読んで、後の問に答えなさい。なお、文中の [&hellip;] は省略を示している。")

# ============================================================
# マーク設問 1-24
# opts: 選択肢（Q8/24等は特殊）, ans: 正解番号(1始まり), exp: 解説
# ============================================================
MARK = [
 dict(n=1, kind="空所補充", stem="空所 (1) に入れるのに最も適切なものを1つ選べ。",
      opts=["unless","because","for","as","when"], ans=1,
      exp="「〜でない限り出られない」の意。unless = if...not。"),
 dict(n=2, kind="空所補充", stem="空所 (2) に入れるのに最も適切なものを1つ選べ。",
      opts=["by","in","of","to","with"], ans=3,
      exp="hear of 〜 =「〜のことを（うわさに）聞く」。"),
 dict(n=3, kind="語義選択", stem="下線部 (3) things の本文中の意味に最も近いものを1つ選べ。",
      opts=["direction","duration","expectation","generation","situation"], ans=5,
      exp="「（新しい土地でも）状況は前と変わらなかった」。things = 状況・事態 = situation。"),
 dict(n=4, kind="空所補充", stem="空所 (4) に入れるのに最も適切なものを1つ選べ。",
      opts=["build","keep","leave","run","save"], ans=3,
      exp="「いつかキャンプを離れて（leave）進学しよう」という文脈。"),
 dict(n=5, kind="語法", stem="空所 (5) に入れるのに最も適切なものを1つ選べ。",
      opts=["and","but","for","than","with"], ans=2,
      exp="nothing to do but +動詞原形 =「〜する以外にすることがない」。"),
 dict(n=6, kind="動詞", stem="空所 (6) に入れるのに最も適切なものを1つ選べ。",
      opts=["buy","eat","get","kill","feed"], ans=5,
      exp="feed hope =「希望を養う・保つ」。前文 keep hope alive と呼応。"),
 dict(n=7, kind="熟語", stem="空所 (7) に入れるのに最も適切なものを1つ選べ。",
      opts=["at all","at ease","at least","at most","at once"], ans=4,
      exp="「せいぜい（多くても）数か月」。at most = 多くても。"),
 dict(n=8, kind="語句整序", stem=("空所 (8) に次の①〜⑦の語句を並べ替えて入れるとき、"
        "<b>2番目</b>と<b>6番目</b>に来るものをそれぞれ選べ。"),
      opts=["what","say","was","to understand","Nadia","trying to","always seemed"],
      ans=None, order=[7,4,1,5,3,6,2],  # 正しい並び(選択肢番号列): always seemed / to understand / what / Nadia / was / trying to / say
      ans2=(4,6),  # 2番目=④, 6番目=⑥
      exp=("完成文: He almost <b>always seemed to understand what Nadia was trying to say</b>. "
           "並び ⑦→④→①→⑤→③→⑥→②。よって2番目=④ to understand、6番目=⑥ trying to。")),
 dict(n=9, kind="動詞", stem="空所 (9) に入れるのに最も適切なものを1つ選べ。",
      opts=["drawing","hitting","rolling","sending","typing"], ans=1,
      exp="棒で地面に文字を「書いて（draw）」練習する。practice drawing the letters。"),
 dict(n=10, kind="名詞", stem="空所 (10) に入れるのに最も適切なものを1つ選べ。",
      opts=["alphabet","code","custom","figure","pattern"], ans=1,
      exp="「32文字のアルファベット」対「26文字の英語のアルファベット」。alphabet = 文字体系。"),
 dict(n=11, kind="語法（多義語）",
      stem="下線部 (11) tell と最も意味が異なる用法を含む文を1つ選べ。",
      opts=["Can you tell the twins apart?",
            "You can tell silk from nylon by touch.",
            "Please tell me what really happened.",
            "It is hard to tell a real coin from a fake.",
            "I cannot tell butter from margarine by taste."], ans=3,
      exp="本文と①②④⑤の tell は「区別する（distinguish）」。③のみ「（人に）言う・伝える」で意味が異なる。"),
 dict(n=12, kind="組合せ補充",
      stem="空所 (12-ア)・(12-イ) に入れる語の組合せとして最も適切なものを1つ選べ。",
      opts=["murmur &mdash; silence","shout &mdash; echo","song &mdash; noise",
            "whisper &mdash; roar","sound &mdash; voice"], ans=4,
      exp="「ささやき（whisper）で始まり、やがて（キャンプ中に響く）轟音（roar）になった」。小→大の対比。"),
 dict(n=13, kind="倒置", stem="空所 (13) に入れるのに最も適切なものを1つ選べ。",
      opts=["Never","Nobody","None","Nor","Nothing"], ans=4,
      exp="否定の継続。Nor was it on the next list =「次の名簿にも載っていなかった」。Nor+倒置。"),
 dict(n=14, kind="発音", stem="下線部 (14) breath の下線部と母音が異なるものを1つ選べ。",
      opts=["feet","friend","head","meant","tent"], ans=1,
      exp="breath /breθ/ = /e/。friend・head・meant・tent も /e/。feet /fiːt/ のみ /iː/ で異なる。"),
 dict(n=15, kind="心情", stem="下線部 (15) から読み取れる Nadia の心情として最も適切なものを1つ選べ。",
      opts=["tired","nervous","confused","delighted","disappointed"], ans=2,
      exp="「手が震えていた」=名簿を見るのが怖く不安。nervous。"),
 dict(n=16, kind="語彙（品詞転換）", stem="空所 (16) に入れるのに最も適切なものを1つ選べ。",
      opts=["armed","fingered","kneed","nosed","shouldered"], ans=5,
      exp="shoulder one's way through 〜 =「肩で（人混みを）押し分けて進む」。名詞shoulderの動詞用法。"),
 dict(n=17, kind="行動理由", stem="下線部 (17) の行動をとった理由として最も適切なものを1つ選べ。",
      opts=["座席が硬くて座り心地が悪かったから",
            "最初の飛行がとても恐ろしかったから",
            "外の景色に見とれていたから",
            "早く目的地に着きたかったから",
            "眠ってしまわないようにするため"], ans=2, jp=True,
      exp="直前で「最初の小型機の飛行がひどく怖かった」とある。だから離陸時に手すりを強く握った。"),
 dict(n=18, kind="名詞", stem="空所 (18) に入れるのに最も適切なものを1つ選べ。",
      opts=["boat","bus","car","plane","train"], ans=4,
      exp="「雲の上を見下ろす」文脈＝空の旅。3便目の plane。"),
 dict(n=19, kind="語義選択", stem="下線部 (19) studying の本文中の意味に最も近いものを1つ選べ。",
      opts=["facing","learning","remembering","working","observing"], ans=5,
      exp="ここでの study は「じっと観察する（observe）」。待つ家族をよく見ていた。"),
 dict(n=20, kind="理由選択",
      stem="下線部 (20) について、Nadia の肩の力が少し抜けた理由として最も適切なものを1つ選べ。",
      opts=["Because the children were crying loudly.",
            "Because the family looked happy to meet her.",
            "Because there was no one to meet her.",
            "Because she had found an old friend.",
            "Because the plane had arrived early."], ans=2,
      exp="their eager smiles =「（迎えの家族の）うれしそうな笑顔」を見て安心した。"),
 dict(n=21, kind="接続詞", stem="空所 (21) に入れるのに最も適切なものを1つ選べ。",
      opts=["as","for","if","to","whom"], ans=3,
      exp="wonder if 〜 =「〜かどうかと思う」。"),
 dict(n=22, kind="語義選択", stem="下線部 (22) stayed on the move の本文中の意味に最も近いものを1つ選べ。",
      opts=["be active","be alone","be hungry","be pleased","be restless"], ans=1,
      exp="stay on the move =「動き回る・活動的でいる」。前文 did not sit still（じっとしていない）と呼応し、スケートやそり遊びで冬も活動的に過ごす。be active。"),
 dict(n=23, kind="空所補充（同一語）",
      stem="空所 (23-ア)・(23-イ) に共通して入れるのに最も適切なものを1つ選べ。",
      opts=["approaching","entering","landing","leaving","starting"], ans=4,
      exp="「空港を出ること（leaving）は、旧生活を後にすること（leaving...behind）のように感じた」。両空所とも leaving。"),
 dict(n=24, kind="内容一致",
      stem="本文の内容と合致<b>しない</b>ものを1つ選べ。",
      opts=["Nadia は数年間、難民キャンプで暮らした。",
            "Joseph は Nadia に読み方とバスケットボールを教えた。",
            "Nadia はカナダへ渡るのに複数回飛行機に乗った。",
            "空港には新しい家族が Nadia を迎えに来ていた。",
            "Nadia の名前は最初に張り出された名簿に載っていた。"], ans=5, jp=True,
      exp="本文では「最初の名簿に名前はなく（not there）、次の名簿にも載っていなかった」。⑤が不一致。"),
]

# ============================================================
# 記述設問 A-F
# ============================================================
DESC = [
 dict(L="A", stem="下線部 A (injured) に最も近い意味をもつ単語を、本文中から<b>一語</b>抜き出して書きなさい。",
      ans="hurt",
      exp="同じ段落の &ldquo;others who had been <u>hurt</u> or even killed&rdquo; の hurt が injured の言い換え。"),
 dict(L="B", stem="下線部 B について、このとき Nadia が主に取り組んでいたことは何か。<b>7字以上12字以内</b>の日本語で書きなさい（句読点は用いない）。",
      ans="英語の読み書き",
      exp="Joseph のもとで英語の文字を書き取り、読む練習をしていた。「英語の読み書き」(7字)・「英語を読む練習」(7字)・「英語の文字の学習」など、英語の読みの学習を表していれば可(7〜12字)。"),
 dict(L="C", stem="下線部 C の this が指す内容がわかるように、解答欄の文を完成させなさい。ただし、空欄には<b>一語ずつ</b>入る。<br>&nbsp;&nbsp;<span class='ansline'>You will be good at (&nbsp;&nbsp;&nbsp;&nbsp;) (&nbsp;&nbsp;&nbsp;&nbsp;).</span>",
      ans="playing / basketball",
      exp="直前でボールを渡し「背が高い」と言っている＝this = バスケットボールをすること。(playing)(basketball)。"),
 dict(L="D", stem="下線部 D (torn) の単語の<b>原形</b>を書きなさい。",
      ans="tear",
      exp="torn は tear（引き裂く）の過去分詞。原形は tear。"),
 dict(L="E", stem="下線部 E について、they が指すものを明らかにして日本語に訳しなさい。",
      ans="（新しい受け入れ家族が）気持ちを変えてしまっていたら（どうしよう）",
      exp="they = Nadia を迎える新しい（受け入れ）家族。訳例:「もし新しい家族が気持ちを変えてしまっていたらどうしよう。」"),
 dict(L="F", stem="空欄 F に入れるのに最も適切な<b>一語</b>を書きなさい。",
      ans="had",
      exp="Never had she felt anything so cold. 否定語 Never が文頭→倒置で had she felt。"),
]

# ============================================================
# 関正生風の解説を外部JSONから注入（あれば上書き）
#   explanations_seki.json: {"Q1": {quote,quote_ja,reason,distractors,point}, ..., "A": {...}}
#     （旧: 値が文字列でも後方互換で exp にそのまま入る）
#   overview_seki.txt: 答案編冒頭の総論（関正生風・任意）
# ============================================================
import json
OVERVIEW = ""
def _inject(q, v):
    if isinstance(v, dict):
        q["exp_struct"] = v      # 構造化解説
    else:
        q["exp"] = v             # 旧・文字列解説
_exp_path = os.path.join(HERE, "explanations_seki.json")
if os.path.exists(_exp_path):
    _EXP = json.load(open(_exp_path, encoding="utf-8"))
    for q in MARK:
        v = _EXP.get(f"Q{q['n']}")
        if v: _inject(q, v)
    for q in DESC:
        v = _EXP.get(q["L"])
        if v: _inject(q, v)
_ov_path = os.path.join(HERE, "overview_seki.txt")
if os.path.exists(_ov_path):
    OVERVIEW = open(_ov_path, encoding="utf-8").read().strip()

# ============================================================
# HTML 生成
# ============================================================
CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Times New Roman','Hiragino Mincho ProN','Yu Mincho',serif;
       color:#000; font-size:10.8pt; line-height:1.9; }
.exam-head { text-align:center; border-bottom:2.5px solid #000; padding-bottom:6px; margin-bottom:12px; }
.exam-head .t1 { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.exam-head .t2 { font-size:10pt; margin-top:3px; }
.daimon { font-size:12pt; font-weight:bold; border-left:6px solid #000; padding-left:8px; margin:14px 0 8px; }
.lead { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:10.2pt;
        background:#f4f4f4; border:1px solid #999; padding:7px 10px; margin-bottom:10px; line-height:1.7;}
.passage p { margin:0 0 7px; text-align:justify; text-indent:0; }
.passage { margin-bottom:6px; }
u { text-decoration: underline; text-underline-offset:2px; }
u.L { text-decoration: underline; text-decoration-style: double; }
sup.qn { font-weight:bold; font-size:8pt; }
sup.qL { font-weight:bold; font-size:8pt; color:#000; }
.bk { font-weight:bold; white-space:nowrap; }
.srcnote { font-family:'Hiragino Mincho ProN',serif; font-size:8.6pt; color:#333; margin:8px 0 4px; }
.qsec-title { font-size:11pt; font-weight:bold; margin:16px 0 6px; border-bottom:1.5px solid #000; padding-bottom:2px; }
.q { margin:0 0 9px; page-break-inside:avoid; }
.q .stem { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.8pt; font-weight:bold; line-height:1.6; }
.q .opts { margin:2px 0 0 1.2em; }
.q .opts .op { display:inline-block; margin:1px 14px 1px 0; font-size:10pt; }
.q.jp .opts .op { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.6pt; }
.order-list .op { display:block; margin:1px 0; }
.ansline { font-family:'Times New Roman',serif; }
.ansbox { display:inline-block; min-width:2.4em; border-bottom:1px solid #000; text-align:center; }
/* 解答編 */
.ans-row { display:flex; flex-wrap:wrap; gap:6px 10px; margin:6px 0 12px; }
.ans-cell { border:1px solid #999; padding:3px 8px; font-size:10pt; min-width:64px; text-align:center;
            font-family:'Hiragino Mincho ProN',serif; }
.ans-cell b { font-size:11pt; }
.exp { margin:6px 0 11px; font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.4pt; line-height:1.6; }
.exp .lab { font-weight:bold; }
.exp-head { font-weight:bold; font-size:10pt; border-bottom:1px solid #bbb; padding-bottom:1px; margin-bottom:3px; break-inside:avoid; }
.ep { display:flex; gap:7px; margin:2.5px 0; line-height:1.68; break-inside:avoid; }
.ep .pl { flex:0 0 5.7em; align-self:flex-start; font-weight:bold; color:#fff; background:#555;
          text-align:center; padding:0.8px 0; border-radius:2px; font-size:8pt; letter-spacing:0;
          white-space:nowrap; }
.ep .pl.pt { background:#8a6d1a; }
.ep .ec { flex:1; }
.ep .quo { font-family:'Times New Roman',serif; }
.ep .qja { color:#333; }
.overview { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.8pt; line-height:1.75;
            background:#f6f6f2; border-left:4px solid #444; padding:8px 12px; margin:4px 0 12px; text-align:justify; }
.desc-ans { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.8pt; margin:4px 0; }
"""

def passage_html():
    ps = "\n".join(f"<p>{p}</p>" for p in PARAS)
    return f'<div class="passage">{ps}</div>'

def mark_q_html(q):
    cls = "q jp" if q.get("jp") else "q"
    if q["n"] == 8:  # 語句整序
        opts = "".join(f'<span class="op">{MARU[i]} {o}</span>' for i,o in enumerate(q["opts"]))
        return (f'<div class="{cls}"><div class="stem">問{q["n"]}. {q["stem"]}</div>'
                f'<div class="opts order-list">{opts}</div></div>')
    opts = "".join(f'<span class="op">{MARU[i]} {o}</span>' for i,o in enumerate(q["opts"]))
    orderclass = "opts order-list" if q["kind"] in ("語法（多義語）","理由選択") and not q.get("jp") else "opts"
    return (f'<div class="{cls}"><div class="stem">問{q["n"]}. {q["stem"]}</div>'
            f'<div class="{orderclass}">{opts}</div></div>')

def desc_q_html(q):
    return (f'<div class="q jp"><div class="stem">'
            f'<span style="font-weight:bold;">問 {q["L"]}.</span> {q["stem"]}</div></div>')

def build_problem():
    head = (f'<div class="exam-head"><div class="t1">明治大学 2026 英語 実戦問題</div>'
            f'<div class="t2">第1問（長文読解）／試験時間 60分／解答番号 1 〜 24 および A 〜 F</div></div>')
    daimon = '<div class="daimon">第1問　次の英文を読んで、後の問(問1〜24 および 問A〜F)に答えなさい。</div>'
    lead = f'<div class="lead">{LEAD}</div>'
    psg = passage_html()
    src = f'<div class="srcnote">{SOURCE_NOTE}</div>'
    mk = '<div class="qsec-title">Ⅰ　マーク式設問（問1〜24）　次の各問について、最も適切なものを①〜⑤から1つずつ選び、マークしなさい。</div>'
    mk += "\n".join(mark_q_html(q) for q in MARK)
    de = '<div class="qsec-title">Ⅱ　記述式設問（問A〜F）　各問の指示に従い、解答欄に記入しなさい。</div>'
    de += "\n".join(desc_q_html(q) for q in DESC)
    body = head + daimon + lead + psg + src + mk + de
    return f"<!doctype html><html lang='ja'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

def _exp_body(q):
    """構造化解説(exp_struct)があればラベル付きブロックで、無ければ従来の文字列で描画"""
    s = q.get("exp_struct")
    if not s:
        return f'<div class="ep"><span class="ec">{q.get("exp","")}</span></div>'
    parts = []
    if s.get("quote"):
        qja = f'<span class="qja">（{s["quote_ja"]}）</span>' if s.get("quote_ja") else ""
        parts.append(f'<div class="ep"><span class="pl">該当箇所</span>'
                     f'<span class="ec"><span class="quo">{s["quote"]}</span> {qja}</span></div>')
    if s.get("reason"):
        parts.append(f'<div class="ep"><span class="pl">考え方</span><span class="ec">{s["reason"]}</span></div>')
    if s.get("distractors"):
        parts.append(f'<div class="ep"><span class="pl">他の選択肢</span><span class="ec">{s["distractors"]}</span></div>')
    if s.get("point"):
        parts.append(f'<div class="ep"><span class="pl pt">ポイント</span><span class="ec">{s["point"]}</span></div>')
    return "".join(parts)

def build_answer():
    head = (f'<div class="exam-head"><div class="t1">明治大学 2026 英語 実戦問題 &mdash; 解答編</div>'
            f'<div class="t2">第1問（長文読解）　解答・解説</div></div>')
    # マーク解答一覧
    cells = ""
    for q in MARK:
        if q["n"] == 8:
            val = f'2番目=④／6番目=⑥'
        else:
            val = MARU[q["ans"]-1]
        cells += f'<div class="ans-cell">問{q["n"]}<br><b>{val}</b></div>'
    ans_row = f'<div class="qsec-title">マーク式 解答一覧</div><div class="ans-row">{cells}</div>'
    # 総論（関正生風・任意）
    overview = ""
    if OVERVIEW:
        overview = (f'<div class="qsec-title">この長文の読み方・攻略の視点</div>'
                    f'<div class="overview">{OVERVIEW}</div>')
    # マーク解説
    exps = '<div class="qsec-title">マーク式 解説</div>'
    for q in MARK:
        if q["n"] == 8:
            av = "2番目=④ to understand ／ 6番目=⑥ trying to"
        else:
            av = f'{MARU[q["ans"]-1]} {q["opts"][q["ans"]-1]}'
        exps += (f'<div class="exp"><div class="exp-head">問{q["n"]}〔{q["kind"]}〕　正解 {av}</div>'
                 f'{_exp_body(q)}</div>')
    # 記述解答・解説
    de = '<div class="qsec-title">記述式 解答・解説</div>'
    for q in DESC:
        de += (f'<div class="exp"><div class="exp-head">問{q["L"]}　解答: {q["ans"]}</div>'
               f'{_exp_body(q)}</div>')
    body = head + ans_row + overview + exps + de
    return f"<!doctype html><html lang='ja'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

def render_pdf(html, name):
    hp = os.path.join(HERE, f"_{name}.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    pdf = os.path.join(OUT, f"{name}.pdf")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", pdf)

if __name__ == "__main__":
    render_pdf(build_problem(), "明治2026英語実戦問題_問題編")
    render_pdf(build_answer(),  "明治2026英語実戦問題_解答編")
    print("OUT:", OUT)
