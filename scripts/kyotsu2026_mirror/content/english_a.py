# -*- coding: utf-8 -*-
"""english_a.py: 2026共通テスト英語R そっくり類似 第1問〜第3問。

第1問(配点6・マーク1〜3)  グループチャット+絵の4択
第2問(配点12・マーク4〜7) 調査記事Webページ+コメント2件
第3問(配点9・マーク8〜13) 物語+整序(9→10→11→12)+人物評
"""

# ---------------------------------------------------------------- 第1問素材

_BANNER_PHOTO = (
    "<svg viewBox='0 0 150 62' width='120' style='display:block;margin:1.5mm 0 0 auto'>"
    "<rect x='1' y='1' width='148' height='60' fill='none' stroke='#333' stroke-width='1.4'/>"
    "<line x1='12' y1='14' x2='30' y2='22' stroke='#333' stroke-width='1'/>"
    "<line x1='138' y1='14' x2='120' y2='22' stroke='#333' stroke-width='1'/>"
    "<circle cx='12' cy='14' r='2' fill='#333'/><circle cx='138' cy='14' r='2' fill='#333'/>"
    "<path d='M30,22 L120,22 L120,44 L112,50 L104,44 L96,50 L88,44 L80,50 L72,44 L64,50 L56,44 L48,50 L40,44 L30,44 Z'"
    " fill='none' stroke='#333' stroke-width='1.4'/>"
    "<path d='M38,34 l3,-6 3,6 -3,-2 z' fill='#333'/>"
    "<text x='75' y='37' font-size='11' text-anchor='middle' font-weight='bold'>TENNIS TEAM</text>"
    "</svg>")

_CHAT = """<div class="chat">
<div class="me"><div class="cname">♣ You</div><span class="bub">Hi everyone! Great news &mdash; our pancake
stand for the school festival next month has been approved. Now we need to decide how to
decorate it. Any ideas?</span></div>
<div><div class="cname">♦ Yuki</div><span class="bub">How about hanging a large cloth banner with our club
logo above the counter? I made this one for the tennis team last year, and it really caught
people's eyes.""" + _BANNER_PHOTO + """</span></div>
<div><div class="cname">♥ Ben</div><span class="bub">I love it! Let's also put some candles on the counter.
Our stand will look warm and cozy like a little caf&eacute; when it gets dark.</span></div>
<div><div class="cname">♠ Tom</div><span class="bub">Candles? That sounds risky to me. We'll be cooking on
hot plates right there, and the paper decorations around the stand could easily catch
fire.</span></div>
<div><div class="cname">♦ Yuki</div><span class="bub">Tom has a point. An open flame near the cooking area
is dangerous. Instead, why don't we hang battery-powered string lights around the counter?
They'll create the same cozy feeling without any danger.</span></div>
<div class="me"><div class="cname">♣ You</div><span class="bub">Perfect. A banner and string lights, then.
Before we buy anything, though, we should check the school's fire-safety rules with
Ms. Hara. She said she'll be free in the club room tomorrow morning before first
period.</span></div>
</div>"""


def _stall(banner=False, candles=False, lights=False):
    """屋台の線画(第1問 問2の絵選択肢)。banner/candles/lights の組合せで描き分け。"""
    p = ["<svg viewBox='0 0 170 135' width='150'>"]
    # 屋根(帯+スカラップ)
    p.append("<rect x='15' y='8' width='140' height='14' fill='none' stroke='#333' stroke-width='1.5'/>")
    p.append("<path d='M15,22 Q22,31 29,22 Q36,31 43,22 Q50,31 57,22 Q64,31 71,22 Q78,31 85,22 "
             "Q92,31 99,22 Q106,31 113,22 Q120,31 127,22 Q134,31 141,22 Q148,31 155,22' "
             "fill='none' stroke='#333' stroke-width='1.3'/>")
    # 柱
    p.append("<line x1='25' y1='22' x2='25' y2='95' stroke='#333' stroke-width='1.5'/>")
    p.append("<line x1='145' y1='22' x2='145' y2='95' stroke='#333' stroke-width='1.5'/>")
    # カウンター
    p.append("<rect x='15' y='95' width='140' height='28' fill='none' stroke='#333' stroke-width='1.5'/>")
    p.append("<line x1='15' y1='103' x2='155' y2='103' stroke='#333' stroke-width='1'/>")
    if lights:  # 電飾ライト(たるんだワイヤ+電球)
        p.append("<path d='M25,26 Q85,44 145,26' fill='none' stroke='#333' stroke-width='1'/>")
        for x, y in ((40, 31), (55, 36), (70, 38.5), (85, 39.5), (100, 38.5), (115, 36), (130, 31)):
            p.append(f"<line x1='{x}' y1='{y}' x2='{x}' y2='{y+4}' stroke='#333' stroke-width='.8'/>")
            p.append(f"<circle cx='{x}' cy='{y+7}' r='3' fill='none' stroke='#333' stroke-width='1.1'/>")
    if banner:  # クラブロゴ(パンケーキ)入りバナー
        p.append("<line x1='25' y1='34' x2='48' y2='48' stroke='#333' stroke-width='1'/>")
        p.append("<line x1='145' y1='34' x2='122' y2='48' stroke='#333' stroke-width='1'/>")
        p.append("<rect x='48' y='46' width='74' height='24' fill='none' stroke='#333' stroke-width='1.4'/>")
        p.append("<ellipse cx='85' cy='62' rx='15' ry='3.5' fill='none' stroke='#333' stroke-width='1.1'/>")
        p.append("<ellipse cx='85' cy='58' rx='13' ry='3.2' fill='none' stroke='#333' stroke-width='1.1'/>")
        p.append("<ellipse cx='85' cy='54' rx='11' ry='3' fill='none' stroke='#333' stroke-width='1.1'/>")
        p.append("<rect x='82' y='49' width='6' height='4' fill='#333'/>")
    if candles:  # キャンドル2本(炎つき)
        for x in (55, 115):
            p.append(f"<rect x='{x-3}' y='82' width='6' height='13' fill='none' stroke='#333' stroke-width='1.2'/>")
            p.append(f"<line x1='{x}' y1='82' x2='{x}' y2='79' stroke='#333' stroke-width='1'/>")
            p.append(f"<path d='M{x},70 Q{x+4},75 {x},79 Q{x-4},75 {x},70 Z' fill='#333'/>")
    p.append("</svg>")
    return "".join(p)


_SEC1 = {
    "no": 1, "points": 6,
    "parts": [{"label": "", "blocks": [
        {"t": "p", "text": "You belong to the international food club at your school. You are exchanging "
                           "messages with your club members about your food stand at the school festival "
                           "next month."},
        {"t": "html", "html": _CHAT},
        {"t": "q", "qlabel": "1", "no": 1,
         "stem": "Who thinks that Ben's suggestion could be dangerous?",
         "choices": ["Ben and Tom", "Ben and Yuki", "Tom and You", "Tom and Yuki"]},
        {"t": "q", "qlabel": "2", "no": 2, "cols": 2,
         "stem": "Which picture best shows how your stand will most likely look at the festival?",
         "choices": [_stall(banner=True, lights=True),
                     _stall(banner=True),
                     _stall(banner=True, candles=True),
                     _stall(candles=True, lights=True)]},
        {"t": "q", "qlabel": "3", "no": 3,
         "stem": "What will your club most likely do first tomorrow morning?",
         "choices": ["Buy battery-powered string lights.",
                     "Check the fire-safety rules with Ms. Hara.",
                     "Cook pancakes at the stand.",
                     "Hang the banner above the counter."]},
    ]}],
}

# ---------------------------------------------------------------- 第2問素材

_WEB = """<div class="web">
<div class="web-bar">https://www.***-university.ac.uk/library/survey2026</div>
<div class="web-in">
<div style="text-align:right;font-size:8.8pt"><b><i>Posted by the University Library Team</i></b><br>
<i>8 January 2026</i></div>
<h3>Campus Library: Student Satisfaction Survey</h3>
<p style="margin:1mm 0">Every two years, the University Library Team asks students about our library
services. This January, 78% of all students completed the online questionnaire. Although the
response rate was not 100%, we believe the results give a fairly accurate picture of student
life on campus.</p>
<p style="margin:1mm 0">The results were generally positive. 84% of the students were satisfied with our
opening hours, five points higher than in the last survey. In addition, 71% said that our staff
were helpful. On the other hand, only 39% said they could always find a seat during exam
weeks, nine points lower than last time. To solve this problem, we will add 80 new seats this
spring, and our popular 24-hour study room will stay open.</p>
<p style="margin:1mm 0">Overall, almost nine out of ten students said they were happy with our library.
We will keep working to make it even better.</p>
<div class="handw" style="text-align:center;font-weight:700;margin-top:2.5mm">Share your comments below!</div>
<div class="comment"><span class="cwho">&#9679; Taiga</span><br>
Most of my friends study in their own rooms, but I decided to go to the library every evening.
It was the right choice. I made new friends there, and I concentrate much better. The air
conditioning was a little too cold in summer, but I solved that by bringing a jacket.</div>
<div class="comment"><span class="cwho">&#9679; Marta</span><br>
The staff are kind and helpful. However, on weekends, many high school students from the town
use the library and often chat loudly near the quiet zone. It is almost impossible to prepare
for exams there. Also, the chairs in the reading rooms are so old that my back hurts after an
hour.</div>
</div></div>"""

_SEC2 = {
    "no": 2, "points": 12,
    "parts": [{"label": "", "blocks": [
        {"t": "p", "text": "You are going to study at a university in the UK next year. On its website, "
                           "you find the results of a survey about the university library, followed by "
                           "comments from students."},
        {"t": "html", "html": _WEB},
        {"t": "q", "qlabel": "1", "no": 4,
         "stem": "Which of the following is an <u>opinion</u> stated in the article?",
         "choices": ["Eighty more seats will be added to the library this spring.",
                     "Seventy-eight percent of the students answered the survey.",
                     "The survey is carried out every two years.",
                     "The survey results give a fairly accurate picture of student life."]},
        {"t": "q", "qlabel": "2", "no": 5,
         "stem": "Which of the following is true according to the survey results?",
         "choices": ["More than eighty percent of the students said the staff were helpful.",
                     "Satisfaction with the opening hours went down from the last survey.",
                     "The number of students who could always find a seat during exam weeks decreased.",
                     "The twenty-four-hour study room will be closed this spring."]},
        {"t": "q", "qlabel": "3", "no": 6,
         "stem": "According to his comment, Taiga {Q}.",
         "choices": ["feels that studying in the library was the right choice",
                     "hopes to find a quieter place to study next year",
                     "regrets not studying in his own room",
                     "thinks the library should turn off the air conditioning"]},
        {"t": "q", "qlabel": "4", "no": 7,
         "stem": "From Marta's comment, you learn that {Q}.",
         "choices": ["high school students are not allowed to use the library",
                     "many students want more group-study rooms",
                     "studying quietly in the library may be difficult on weekends",
                     "the chairs in the reading rooms were recently replaced"]},
    ]}],
}

# ---------------------------------------------------------------- 第3問素材

_BOY_SVG = (
    "<svg viewBox='0 0 150 130' width='105' style='float:right;margin:0 0 2mm 3mm'>"
    # 頭・髪
    "<circle cx='98' cy='30' r='13' fill='none' stroke='#333' stroke-width='1.4'/>"
    "<path d='M86,26 Q92,14 104,18 Q111,21 111,29' fill='none' stroke='#333' stroke-width='1.4'/>"
    # 胴(正座・前かがみ)
    "<path d='M92,42 Q78,50 72,66 Q70,74 74,78' fill='none' stroke='#333' stroke-width='1.4'/>"
    "<path d='M103,42 Q108,56 104,70 Q118,72 120,80' fill='none' stroke='#333' stroke-width='1.4'/>"
    "<path d='M74,78 Q88,84 120,80 L120,88 Q92,92 72,86 Z' fill='none' stroke='#333' stroke-width='1.4'/>"
    # 腕+筆
    "<path d='M96,50 Q84,58 66,62' fill='none' stroke='#333' stroke-width='1.4'/>"
    "<line x1='64' y1='54' x2='68' y2='68' stroke='#333' stroke-width='1.6'/>"
    "<rect x='66.5' y='68' width='3' height='6' fill='#333'/>"
    # 文机と紙・墨のシミ(鳥)
    "<rect x='14' y='78' width='52' height='5' fill='none' stroke='#333' stroke-width='1.4'/>"
    "<line x1='20' y1='83' x2='20' y2='94' stroke='#333' stroke-width='1.4'/>"
    "<line x1='60' y1='83' x2='60' y2='94' stroke='#333' stroke-width='1.4'/>"
    "<polygon points='22,78 52,78 58,70 28,70' fill='none' stroke='#333' stroke-width='1.1'/>"
    "<path d='M36,73 q3,-4 6,0 q4,-3 6,1 l-4,1 2,2 -6,-1 -3,1 z' fill='#333'/>"
    # 硯
    "<rect x='4' y='88' width='16' height='5' rx='2' fill='none' stroke='#333' stroke-width='1.2'/>"
    "</svg>")

_STORY = """<div class="mat">
<div class="mat-t">The Ink Bird</div>
""" + _BOY_SVG + """
<p style="text-indent:1em;margin:.9mm 0">Last spring, my mother suggested that I take a calligraphy class
at the community center. She had read in a magazine that calligraphy improves concentration, and
she often said I could not sit still for more than ten minutes. I was not interested at first,
but when I heard that my friend Ryo had already joined, I decided to give it a try and signed up
the next day. The class met every Saturday morning, and our teacher was a quiet old man named
Mr. Sugiyama.</p>
<p style="text-indent:1em;margin:.9mm 0">One morning, while I was reaching for a fresh sheet of paper, my
elbow hit the ink stone. Black ink flew across the piece I had been working on for nearly an
hour. I sat frozen, staring at the large ugly blot in the middle of my best character. Ryo
stopped his brush and looked at me.</p>
<p style="text-indent:1em;margin:.9mm 0">I grabbed the paper and stood up to throw it away, but
Mr. Sugiyama gently took it from my hands. Without a word, he laid it back on the desk and picked
up his own brush. He added a few quick strokes to the blot &mdash; a beak here, a tail there &mdash; and
suddenly the ink stain became a small black bird flying above my character. Everyone in the
class gathered around to watch. Mr. Sugiyama smiled, hung the paper on the classroom wall, and
said, &ldquo;A mistake is not the end of your work. Sometimes it is the beginning of something
better.&rdquo;</p>
<p style="text-indent:1em;margin:.9mm 0">Honestly, I cannot say yet whether calligraphy has improved my
concentration. But every Saturday, when I see the little bird on the wall, I remember that
something that looks ruined can turn into something new.</p>
<div style="clear:both"></div>
</div>"""

_SEC3 = {
    "no": 3, "points": 9,
    "parts": [{"label": "", "blocks": [
        {"t": "p", "text": "Your English teacher has told you to read the following story before the "
                           "next class."},
        {"t": "html", "html": _STORY},
        {"t": "q", "qlabel": "1", "no": 8,
         "stem": "The author joined the calligraphy class because {Q}.",
         "choices": ["a classmate praised his beautiful handwriting",
                     "a family member recommended it to him",
                     "his friend Ryo invited him to join",
                     "his mother signed him up without asking him"]},
        {"t": "q", "qlabel": "2", "no": 9,
         "stem": "Choose <u>four</u> out of the five options (①〜⑤) and rearrange them in the order "
                 "they happened.　{Q} → <span class=\"qslot\">10</span> → "
                 "<span class=\"qslot\">11</span> → <span class=\"qslot\">12</span>",
         "choices": ["The teacher changed the ink mark into a small bird.",
                     "The teacher hung the writer's paper on the classroom wall.",
                     "The writer hit the ink stone and spilled ink on his paper.",
                     "The writer signed up for a calligraphy class.",
                     "The writer threw his paper into the trash can."]},
        {"t": "q", "qlabel": "3", "no": 13,
         "stem": "Which of the following words best describes Mr. Sugiyama?",
         "choices": ["angry", "careless", "cold", "creative"]},
    ]}],
}

SECTIONS = [_SEC1, _SEC2, _SEC3]

# ---------------------------------------------------------------- 解答・解説

ANS_SECTIONS = [
    {"section": 1, "points": 6,
     "answers": [{"qno": 1, "answer": "④", "points": 2},
                 {"qno": 2, "answer": "①", "points": 2},
                 {"qno": 3, "answer": "②", "points": 2}],
     "kai": [
         {"heading": "問1", "blocks": [{"t": "p", "text":
             "正解④。Benの提案はキャンドル。Tomは「Candles? That sounds risky to me. "
             "... could easily catch fire」と火事の危険を指摘し、Yukiも「An open flame near "
             "the cooking area is dangerous」と同調している。よって危険だと考えているのは"
             "TomとYukiの2人。①②のBenは提案者本人で危険には触れていない。③のYouは"
             "安全面の発言をしていないので誤り。"}]},
         {"heading": "問2", "blocks": [{"t": "p", "text":
             "正解①。最終的に採用されたのはYouの最後の発話「A banner and string lights, "
             "then.」のとおり、クラブロゴ入りバナーと電池式の電飾ライト。①はその両方が"
             "描かれている。②はライトが無く、③は却下されたキャンドルが置かれ、④はバナーが"
             "無いので誤り。"}]},
         {"heading": "問3", "blocks": [{"t": "p", "text":
             "正解②。Youは「Before we buy anything, we should check the school's "
             "fire-safety rules with Ms. Hara. She said she'll be free in the club room "
             "tomorrow morning before first period.」と述べており、明日の朝一番にするのは"
             "先生への防火規則の確認。①の購入は「buy する前に確認」なので確認の後。"
             "④のバナー掲示や③の調理は文化祭当日の行動であり、明日の予定ではない。"}]},
     ]},
    {"section": 2, "points": 12,
     "answers": [{"qno": 4, "answer": "④", "points": 3},
                 {"qno": 5, "answer": "③", "points": 3},
                 {"qno": 6, "answer": "①", "points": 3},
                 {"qno": 7, "answer": "③", "points": 3}],
     "kai": [
         {"heading": "問1", "blocks": [{"t": "p", "text":
             "正解④。第1段落の「we believe the results give a fairly accurate picture of "
             "student life on campus」は書き手の考えを述べた意見(we believe が目印)。"
             "①(80席増設)・②(回答率78%)・③(2年ごとに実施)はいずれも記事に書かれた"
             "検証可能な事実なので、意見としては誤り。"}]},
         {"heading": "問2", "blocks": [{"t": "p", "text":
             "正解③。「only 39% said they could always find a seat during exam weeks, "
             "nine points lower than last time」より、席を見つけられた学生の割合は前回から"
             "9ポイント減少している(decreased への言い換え)。①はスタッフ評価が71%なので"
             "「80%超」は誤り。②の開館時間の満足度は「five points higher」と上昇しており逆。"
             "④の24時間自習室は「will stay open」なので閉鎖は誤り。"}]},
         {"heading": "問3", "blocks": [{"t": "p", "text":
             "正解①。Taigaは図書館通いを「It was the right choice.」と評価し、友人ができ"
             "集中もできると満足している。②の「もっと静かな場所を探したい」や③の後悔は"
             "本文に無い。④は、冷房の寒さを「brought a jacket」で自分で解決した話であり、"
             "「冷房を切るべきだ」とまでは言っていない。"}]},
         {"heading": "問4", "blocks": [{"t": "p", "text":
             "正解③。「on weekends, many high school students ... chat loudly near the "
             "quiet zone. It is almost impossible to prepare for exams there.」から、週末は"
             "図書館で静かに勉強するのが難しいと推論できる(interfere/difficult への言い換え)。"
             "①は「立入禁止」とは書かれておらず、実際に高校生が利用している描写と矛盾。"
             "②のグループ学習室の話は本文に無い。④は椅子が「so old」とあるので"
             "「最近交換された」は逆。"}]},
     ]},
    {"section": 3, "points": 9,
     "answers": [{"qno": 8, "answer": "②", "points": 3},
                 {"qno": 9, "answer": "④", "points": "3*"},
                 {"qno": 10, "answer": "③", "points": "＊"},
                 {"qno": 11, "answer": "①", "points": "＊"},
                 {"qno": 12, "answer": "②", "points": "＊"},
                 {"qno": 13, "answer": "④", "points": 3}],
     "kai": [
         {"heading": "問1", "blocks": [{"t": "p", "text":
             "正解②。第1段落「my mother suggested that I take a calligraphy class」より、"
             "勧めたのは母=家族の一員(a family member)。④は「本人に無断で申し込んだ」の"
             "部分が誤りで、申し込んだのは筆者自身(「I decided to give it a try and signed "
             "up the next day」)。③のRyoは先に入会していただけで筆者を誘ってはいない。"
             "①のように字を褒められた事実は本文に無い。"}]},
         {"heading": "問2（9〜12は完答で3点）", "blocks": [{"t": "p", "text":
             "正解 9=④ → 10=③ → 11=① → 12=②。時系列は、④書道教室に申し込む(第1段落)"
             "→③肘が硯に当たり紙に墨をこぼす(第2段落)→①先生が墨のシミに筆を加えて小鳥の絵に"
             "変える(第3段落)→②先生がその紙を教室の壁に掲示する(第3段落後半)。⑤「紙をゴミ箱に"
             "捨てた」は本文では起きていない出来事——筆者は捨てようと立ち上がったが、"
             "「Mr. Sugiyama gently took it from my hands」と先生が受け取ったため、除外する。"}]},
         {"heading": "問3", "blocks": [{"t": "p", "text":
             "正解④。墨のシミに数筆を加えて鳥の絵に変えてしまう発想と行動から、"
             "creative(創造的)が最も適切。①angry・③cold は「gently」「smiled」という描写と"
             "矛盾し、②careless(不注意)は不注意だったのは筆者の方なので誤り。"}]},
     ]},
]
