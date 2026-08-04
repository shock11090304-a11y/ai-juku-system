# -*- coding: utf-8 -*-
"""english_c.py: 2026共通テスト英語(リーディング) そっくり類似 — 第6問・第7問・第8問。

第6問 (配点12・マーク24〜31): 額縁構造の創作物語+作中手書きメモ→Story Outline完成
  - 現在→◆◆◆◆◆→中学の回想→◆◆◆◆◆→現在 の額縁構造 (約780語)
  - 問1: 人物特性 2 of 5 順不同(24・25) / 問2: 時系列 4 of 5 並べ替え(26→29)
  - 問3: 年長者の性質の抽象化 4択(30) / 問4: 主人公への長期的影響 4択(31)
第7問 (配点16・マーク32〜37): 科学的論説(退屈 boredom)→プレゼンスライド6枚完成
  - 問1(32)定義 / 問2(33・34)効果2 of 5順不同 / 問3(35)メカニズム / 問4(36)研究知見
  - 問5(37)生徒カード4枚→Tips合致2人の組合せ C(4,2)=6択全列挙
第8問 (配点17・マーク38〜44): エッセイ執筆プロセス型 (学校でのAI利用の是非)
  - 意見5本(賛2/反2/条件付1)→POSITIONメモ完答(40・41・42)→アウトライン→Source A論説+Source B棒グラフ
  - 問1(38)要旨 / 問2(39)二者共通 / 問3(40・41・42)完答 / 問4(43)Source A / 問5(44)Source B棒グラフ

マーク番号は english_b.py(第5問が23で終了)に接続し、実物2026と同一の 24〜44 を使用。
"""

# =====================================================================
# ============================ 第6問 ==================================
# =====================================================================

# --- 作中の手書き風感謝メモ (平行四辺形に傾いた枠+花のライン画) ---
_FLOWER_TL = (
    "<svg viewBox='0 0 40 40' width='30' style='position:absolute;top:-6px;left:-6px'>"
    "<circle cx='20' cy='20' r='4' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<ellipse cx='20' cy='10' rx='3' ry='6' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<ellipse cx='20' cy='30' rx='3' ry='6' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<ellipse cx='10' cy='20' rx='6' ry='3' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<ellipse cx='30' cy='20' rx='6' ry='3' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<path d='M22 24 Q30 32 30 39' fill='none' stroke='#8a7a5a' stroke-width='1'/></svg>")
_FLOWER_BR = (
    "<svg viewBox='0 0 40 40' width='30' style='position:absolute;bottom:-6px;right:-4px'>"
    "<circle cx='20' cy='20' r='4' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<ellipse cx='20' cy='10' rx='3' ry='6' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<ellipse cx='20' cy='30' rx='3' ry='6' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<ellipse cx='10' cy='20' rx='6' ry='3' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<ellipse cx='30' cy='20' rx='6' ry='3' fill='none' stroke='#8a7a5a' stroke-width='1'/>"
    "<path d='M18 16 Q10 8 10 1' fill='none' stroke='#8a7a5a' stroke-width='1'/></svg>")

_Q6_NOTE = f"""
<div style="display:flex;justify-content:center;margin:3mm 0">
 <div class="handw" style="position:relative;transform:skewX(-7deg) rotate(-1.4deg);
   border:1.4px solid #7a6a4a;background:#fffaf0;padding:4mm 7mm 5mm;width:112mm;
   font-size:11pt;line-height:1.95;box-shadow:1px 2px 5px rgba(0,0,0,.12)">
  {_FLOWER_TL}{_FLOWER_BR}
  <div style="transform:skewX(3deg)">
   Dear Mr. Sato,<br>
   Thank you for the extra one you slipped into my bag. I ran hard and came in third,
   so I finally got to the finals! I know your secret now &mdash; the young man in that old
   photo, running so fast, is you, isn't it? Next time I'll bring a teammate along. Please
   get well soon.<br>
   <span style="display:block;text-align:right;margin-top:1mm">&mdash; Haruka</span>
  </div>
 </div>
</div>
"""

# --- 物語本文 (約780語, 額縁構造) ---
_DIAMOND = ('<div style="text-align:center;letter-spacing:.5em;margin:3mm 0;'
            'font-size:11pt;color:#333">◆◆◆◆◆</div>')

_Q6_STORY = f"""
<div class="passage" style="font-family:'Times New Roman','Hiragino Mincho ProN',serif;
  font-size:10.2pt;line-height:1.85;text-align:justify;padding:5mm 6mm">
 <div style="text-align:center;font-weight:700;font-size:12.5pt;margin-bottom:3mm;
   font-family:'Times New Roman',serif">The <i>Taiyaki</i> Stand</div>

 <p style="margin:1.5mm 0">Haruka sat alone on a bench in the city park, ten minutes before the
 biggest presentation of her career. In her hands was a warm <i>taiyaki</i>, or a fish-shaped
 cake filled with sweet red-bean paste, bought from a stand by the station. She was not really
 hungry. She had bought it because, whenever she felt her heart beating too fast, this simple
 taste brought her back to a small stand near her old school and to the person who once stood
 behind it.</p>

 <p style="margin:1.5mm 0">When she bit into the tail, warm and slightly burnt, she was thirteen
 again.</p>

 {_DIAMOND}

 <p style="margin:1.5mm 0">Back then, there was a tiny <i>taiyaki</i> stand at the corner of the
 shopping street, halfway between the school and the river where the track club ran every
 afternoon. It was run by an old man the students simply called "Mr. Sato." He rarely spoke.
 He would take your coins, press the batter into the iron mould, and hand over the hot cake
 wrapped in thin paper, all without more than a nod. Some students thought he was unfriendly.
 Haruka, tired and out of breath after practice, thought only that his taiyaki was the best
 thing in the world.</p>

 <p style="margin:1.5mm 0">She always ordered the red-bean one, the cheapest on the little
 board. She counted her coins carefully; that was all she could afford after buying her
 running shoes. Day after day she came, said little, and left. But over the weeks she began to
 notice things. Behind the counter hung an old, faded photograph. In it, a young man in a
 running vest was crossing a finish line, his face bright with effort, a number pinned to his
 chest. The more she looked, the more the sharp eyes in the photo seemed to match the quiet
 man at the mould. She wanted to ask him about it, but she never found the courage.</p>

 <p style="margin:1.5mm 0">The day before the regional meet, she left in a hurry and forgot her
 spikes &mdash; her running shoes &mdash; leaning against the stand. She only realised it that
 night and could not sleep, sure they were lost. But the next morning, before the meet, she
 ran to the corner. Mr. Sato reached under the counter and, without a word about how worried
 she must have been, held out the shoes. As she thanked him again and again, he only said, in
 his low, rough voice, "Don't lose your footing out there," and turned back to his iron mould.</p>

 <p style="margin:1.5mm 0">At the meet she opened her bag to eat before her race and found two
 taiyaki inside, though she had bought only one. The second was a custard one, the kind she had
 always wanted but never bought because it cost a little more. There was no note, no message.
 She ate it slowly, and somehow her legs felt lighter that day. She ran her personal best and
 reached the finals.</p>

 <p style="margin:1.5mm 0">She went straight back to thank him, still in her uniform. But the
 stand was closed. A younger woman was cleaning the counter. She explained that her father had
 been taken to hospital that morning, nothing too serious, and that she would keep the stand
 open for him. When the woman turned, Haruka caught her breath: the same bright, sharp eyes as
 the runner in the photo. So it really had been him. Haruka bought a pen and, on the back of a
 taiyaki wrapper, wrote a few clumsy lines and asked the woman to give them to Mr. Sato.</p>

 {_Q6_NOTE}

 <p style="margin:1.5mm 0">After that, whenever a meet was near, a second taiyaki would quietly
 appear in her bag &mdash; always a custard one, always without a word. She never once heard him
 say "good luck." He never needed to. His kindness was in what he did, not in what he said, and
 somehow that made it easier to carry.</p>

 {_DIAMOND}

 <p style="margin:1.5mm 0">Haruka finished the last of the red-bean taiyaki and stood up. The old
 stand was long gone, and she had never learned what became of Mr. Sato. But the lesson had
 stayed with her: that the people who believe in you most are often the ones who say the least.
 She brushed the crumbs from her hands, straightened her jacket, and walked toward the hall.
 It was time to smash the presentation.</p>
</div>
"""

# --- Story Outline (手書き風・空所ボックス) ---
_Q6_OUTLINE = """
<div class="outline handw" style="font-size:10.4pt;line-height:1.75">
 <div class="o-t" style="font-size:12pt">Story Outline</div>
 <hr style="border:none;border-top:1px solid #888;margin:1mm 0 2.5mm">

 <div style="font-weight:700;margin:1.5mm 0 .5mm">Setting and characters</div>
 <div style="margin-left:2mm"><b>Haruka</b>
  <ul style="margin:.3mm 0 1.5mm;padding-left:1.4em">
   <li>a member of the track club in junior high school</li>
   <li>visits a small taiyaki stand after practice every day</li>
   <li>can only afford the cheapest taiyaki on the board</li>
  </ul>
 </div>
 <div style="margin-left:2mm"><b>Old man (Mr. Sato)</b>
  <ul style="margin:.3mm 0 1mm;padding-left:1.4em">
   <li>runs the taiyaki stand and rarely speaks to customers</li>
   <li><span class="qslot">24</span></li>
   <li><span class="qslot">25</span></li>
  </ul>
 </div>

 <div style="font-weight:700;margin:2.5mm 0 .5mm">Important incidents</div>
 <div style="display:flex;gap:3mm;align-items:stretch;margin-left:2mm">
  <div style="flex:0 0 auto;display:flex;flex-direction:column;align-items:center;padding-top:1mm">
   <div style="flex:1;width:2px;background:#444;min-height:26mm"></div>
   <div style="width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;
     border-top:8px solid #444"></div>
  </div>
  <div style="flex:1">
   <div style="margin:.6mm 0">1. <span class="qslot">26</span></div>
   <div style="margin:.6mm 0">2. <span class="qslot">27</span></div>
   <div style="margin:.6mm 0">3. <span class="qslot">28</span></div>
   <div style="margin:.6mm 0">4. <span class="qslot">29</span></div>
  </div>
 </div>

 <div style="font-weight:700;margin:2.5mm 0 .5mm">What does the story tell us?</div>
 <ul style="margin:.3mm 0 0;padding-left:1.4em">
  <li>The old man <span class="qslot">30</span>.</li>
  <li>Haruka's <span class="qslot">31</span>.</li>
 </ul>
</div>
"""

_SEC6 = {
    "no": 6, "points": 12,
    "parts": [{"label": "", "blocks": [
        {"t": "p", "text": "In English class, your teacher has asked you to read a short story and "
                           "complete a Story Outline for a class presentation. Read the story below and "
                           "fill in the blanks in the outline that follows."},
        {"t": "html", "html": _Q6_STORY},
        {"t": "pagebreak"},
        {"t": "html", "html": _Q6_OUTLINE},
        {"t": "q", "qlabel": "1", "no": 24, "multi": True,
         "stem": "Choose the best <u>two</u> options for <span class=\"qslot\">24</span> and "
                 "<span class=\"qslot\">25</span> to complete the <b>Old man (Mr. Sato)</b> section. "
                 "(The order does not matter.)",
         "choices": [
             "shows his kindness through his actions rather than his words",
             "used to be a runner when he was young",
             "often chats cheerfully with the students who visit",
             "refuses to sell the more expensive kind of taiyaki",
             "teaches Haruka how to make taiyaki at the stand",
         ]},
        {"t": "q", "qlabel": "2", "no": 26,
         "stem": "Choose <u>four</u> out of the five options (①〜⑤) and put them in the order they "
                 "happened in Haruka's junior high school days. "
                 "{Q} → <span class=\"qslot\">27</span> → <span class=\"qslot\">28</span> → "
                 "<span class=\"qslot\">29</span>",
         "choices": [
             "Haruka noticed that the man in the old photo looked like Mr. Sato.",
             "Haruka left a handwritten note for Mr. Sato with his daughter.",
             "Haruka found a custard taiyaki she had not bought inside her bag.",
             "Haruka forgot her spikes at the stand and got them back the next morning.",
             "Haruka ate a red-bean taiyaki in the park before her presentation.",
         ]},
        {"t": "q", "qlabel": "3", "no": 30,
         "stem": "Choose the best option for <span class=\"qslot\">30</span>.<br>The old man {Q}.",
         "choices": [
             "encourages people by cheering loudly for them",
             "cares about people quietly by doing small things for them",
             "gives advice only to students who ask him questions",
             "hides his past because he is ashamed of it",
         ]},
        {"t": "q", "qlabel": "4", "no": 31,
         "stem": "Choose the best option for <span class=\"qslot\">31</span>.<br>Haruka's {Q}.",
         "choices": [
             "memory of the man's silent support still gives her strength today",
             "wish to run in a marathon has never left her since middle school",
             "habit of eating taiyaki has helped her save a lot of money",
             "friendship with Mr. Sato's daughter continues to this day",
         ]},
    ]}],
}

# =====================================================================
# ============================ 第7問 ==================================
# =====================================================================

_THINKER = (
    "<svg viewBox='0 0 60 70' width='42' style='display:block;margin:2mm auto 0'>"
    "<ellipse cx='30' cy='66' rx='16' ry='3' fill='none' stroke='#666' stroke-width='1'/>"
    "<rect x='14' y='58' width='32' height='6' fill='none' stroke='#333' stroke-width='1.4'/>"
    "<circle cx='30' cy='16' r='7' fill='none' stroke='#333' stroke-width='1.6'/>"
    "<path d='M30 23 Q22 26 21 40 Q20 50 26 58 L40 58 Q44 50 42 42 L44 34' "
    "fill='none' stroke='#333' stroke-width='1.6'/>"
    "<path d='M42 42 Q46 40 40 33 L34 30' fill='none' stroke='#333' stroke-width='1.6'/>"
    "<path d='M34 30 Q30 27 28 22' fill='none' stroke='#333' stroke-width='1.6'/></svg>")

# --- 論説本文 (約680語) ---
_Q7_PASSAGE = """
<div class="passage" style="font-family:'Times New Roman','Hiragino Mincho ProN',serif;
  font-size:10.2pt;line-height:1.82;text-align:justify;padding:5mm 6mm">
 <div style="text-align:center;font-weight:700;font-size:12.5pt;margin-bottom:3mm;
   font-family:'Times New Roman',serif">Boredom: The Uncomfortable Engine of Ideas</div>

 <p style="margin:1.5mm 0">Think of a child sitting in a waiting room with nothing to do, sighing
 and swinging her legs. We usually treat boredom as an empty, useless state &mdash; a gap to be
 filled as quickly as possible with a phone or a snack. Yet scientists who study the mind are
 beginning to see boredom not as a hole to escape, but as a signal worth listening to.</p>

 <p style="margin:1.5mm 0">Boredom is the unpleasant feeling that comes when we want to be engaged
 in a satisfying activity but cannot find one. It is surprisingly common: in one survey, adults
 reported feeling bored during about 20 percent of their waking hours. Because the feeling is so
 uncomfortable, we naturally think of it as a problem to be removed.</p>

 <p style="margin:1.5mm 0">For a long time, researchers focused only on its costs. Boredom has been
 linked to poor concentration, careless mistakes at work, and even overeating, as people reach
 for food simply to have something to do. Students who are frequently bored tend to get lower
 grades. Given all this, it is easy to conclude that boredom is something we should avoid at all
 costs.</p>

 <p style="margin:1.5mm 0">But recent studies tell a more surprising story. When boredom is
 allowed to run its course, rather than being cut short, it can actually push us toward
 creativity. The reason is that a bored mind dislikes doing nothing. Once the outside world
 stops giving it interesting input, the mind turns inward and starts generating its own &mdash;
 imagining, planning, and combining old ideas in new ways. In this sense, boredom works like an
 alarm clock that pushes us to look for something more meaningful.</p>

 <p style="margin:1.5mm 0">In one well-known experiment, people were first given a dull task:
 copying numbers out of a telephone book for several minutes. Afterward, they were asked to think
 of as many creative uses as possible for an everyday object, such as a paper cup. The people who
 had done the boring task came up with more, and more original, ideas than those who had not been
 bored first. Being stuck in a dull moment seemed to prepare the mind to reach further once it was
 finally set free.</p>

 <p style="margin:1.5mm 0">Brain research helps explain why. In a 2015 study conducted in Canada,
 scientists watched the brains of bored volunteers and found that a set of connected regions,
 later called the "wandering network," became highly active. This network switches on when we are
 not focused on the outside world &mdash; when we daydream, remember the past, or picture the
 future. It appears to be the workshop where loose thoughts are quietly put together. A more
 recent 2021 study in Ireland went further: it showed that this network was even <i>more</i>
 active during mild boredom than during light, easy tasks, suggesting that an empty moment is not
 an empty brain at all.</p>

 <p style="margin:1.5mm 0">So how can we make friends with boredom instead of fighting it? First,
 leave some gaps in your day on purpose. Do not fill every spare minute with a screen; let a bus
 ride or a walk be a time when your mind can wander. Next, try keeping a small notebook nearby,
 because the ideas that surface during dull moments are easily forgotten. Another suggestion is to
 change tasks before you are completely worn out, since a fresh but simple activity can reset your
 attention. Finally, remember that being bored is not the same as being lazy; treat it as a sign
 that your mind is ready for something new.</p>

 <p style="margin:1.5mm 0">Boredom will never feel pleasant, and no one is asking us to enjoy it.
 But if we stop rushing to escape it, we may find that this uncomfortable feeling is quietly doing
 some of our most creative work for us.</p>
</div>
"""

# --- スライド6枚 (2列×3段グリッド) ---
_Q7_SLIDES = f"""
<div class="slides" style="grid-template-columns:1fr 1fr">
 <div class="slide" style="position:relative;text-align:center;display:flex;flex-direction:column;
   justify-content:center;min-height:34mm">
  <div style="font-size:14pt;font-weight:700;letter-spacing:.02em;font-family:'Helvetica Neue',Arial,sans-serif">Boredom</div>
  <div style="font-size:8.6pt;color:#555;margin-top:.5mm">The Uncomfortable Engine of Ideas</div>
  {_THINKER}
  <div style="position:absolute;right:2mm;bottom:1mm;font-size:8pt;color:#777">1</div>
 </div>

 <div class="slide" style="position:relative;min-height:34mm">
  <div class="s-t">The Nature of Boredom</div>
  <div style="margin-top:2mm">It happens <span class="qslot">32</span>.</div>
  <div style="position:absolute;right:2mm;bottom:1mm;font-size:8pt;color:#777">2</div>
 </div>

 <div class="slide" style="position:relative;min-height:34mm">
  <div class="s-t">Two Faces of Boredom</div>
  <ul style="margin-top:1.5mm">
   <li style="margin:1mm 0">It <span class="qslot">33</span>.</li>
   <li style="margin:1mm 0">It <span class="qslot">34</span>.</li>
  </ul>
  <div style="position:absolute;right:2mm;bottom:1mm;font-size:8pt;color:#777">3</div>
 </div>

 <div class="slide" style="position:relative;min-height:34mm;display:flex;flex-direction:column">
  <div class="s-t">Why Does a Dull Moment Spark Ideas?</div>
  <div style="margin:auto 0;text-align:center;font-weight:600"><span class="qslot">35</span></div>
  <div style="position:absolute;right:2mm;bottom:1mm;font-size:8pt;color:#777">4</div>
 </div>

 <div class="slide" style="position:relative;min-height:34mm;display:flex;flex-direction:column">
  <div class="s-t">A Finding From Brain Research</div>
  <div style="margin:auto 0;text-align:center;font-weight:600"><span class="qslot">36</span></div>
  <div style="position:absolute;right:2mm;bottom:1mm;font-size:8pt;color:#777">5</div>
 </div>

 <div class="slide" style="position:relative;min-height:34mm">
  <div class="s-t">Discussion</div>
  <div style="margin-top:2mm;font-size:8.8pt">Look at the daily habits of the four students on the
  next page. <b>Which two of them are already making the most of boredom?</b></div>
  <div style="position:absolute;right:2mm;bottom:1mm;font-size:8pt;color:#777">6</div>
 </div>
</div>
"""

# --- 生徒の習慣カード4枚 (2×2) ---
def _habit_card(name, body):
    return (f'<div class="handw" style="border:1.1px solid #666;border-radius:2.5mm;'
            f'padding:2.5mm 3.5mm;background:#fffdf5;font-size:9.6pt;line-height:1.7">'
            f'{body}<div style="text-align:right;font-weight:700;margin-top:1mm">&mdash;{name}</div></div>')

_Q7_CARDS = f"""
<div style="border:1.3px solid #333;padding:3mm;margin:2mm 1mm">
 <div style="display:grid;grid-template-columns:1fr 1fr;gap:3mm">
  {_habit_card("Ami",
    "I love reading, so I often stay up past midnight with a good book. To keep myself awake in "
    "class, I drink strong green tea all day. I get only about five hours of sleep, but I feel that "
    "reading a lot makes me a creative person.")}
  {_habit_card("Barry",
    "I don't like sitting still. Every morning I cycle to school along the river, and on weekends I "
    "go hiking in the hills with my dog. Being outside with nothing but the scenery around me is "
    "when my best ideas seem to come.")}
  {_habit_card("Chihiro",
    "My weekdays are packed with club activities and homework. On weekends, though, I switch off my "
    "phone and just soak in a hot bath at the local bathhouse for a long time, doing nothing at all. "
    "I always feel refreshed afterward.")}
  {_habit_card("Dean",
    "I want to be an online influencer, so the moment I wake up I grab my phone and start replying "
    "to comments before I even get out of bed. I keep checking my accounts all day so that I never "
    "miss anything important.")}
 </div>
</div>
"""

_SEC7 = {
    "no": 7, "points": 16,
    "parts": [{"label": "", "blocks": [
        {"t": "p", "text": "You prepared a presentation with a discussion question for a science class, "
                           "based on the following passage. Read the passage and complete the slides."},
        {"t": "html", "html": _Q7_PASSAGE},
        {"t": "pagebreak"},
        {"t": "html", "html": '<div style="font-weight:700;margin:1mm 0 2mm">Slide drafts</div>'},
        {"t": "html", "html": _Q7_SLIDES},
        {"t": "q", "qlabel": "1", "no": 32,
         "stem": "Choose the best option for <span class=\"qslot\">32</span> on Slide 2. {Q}",
         "choices": [
             "only when we are doing a difficult and important job",
             "when we want to be doing something engaging but cannot",
             "because our brain stops working while we rest",
             "mainly among people who have too much free time",
         ]},
        {"t": "q", "qlabel": "2", "no": 33, "multi": True,
         "stem": "Choose the best <u>two</u> options for <span class=\"qslot\">33</span> and "
                 "<span class=\"qslot\">34</span> on Slide 3. (The order does not matter.)",
         "choices": [
             "can lead to careless mistakes and lower grades",
             "can push the mind toward more creative ideas",
             "helps people concentrate harder on boring tasks",
             "makes people eat less than they usually do",
             "improves a person's memory of the distant past",
         ]},
        {"t": "q", "qlabel": "3", "no": 35,
         "stem": "Choose the best option for <span class=\"qslot\">35</span> on Slide 4. {Q}",
         "choices": [
             "The mind stops all activity until an interesting task appears.",
             "The unpleasant feeling forces us to fill the time with a screen.",
             "A mind with no outside input starts creating ideas of its own.",
             "Boredom trains people to copy numbers more quickly and neatly.",
         ]},
        {"t": "q", "qlabel": "4", "no": 36,
         "stem": "Choose the best option for <span class=\"qslot\">36</span> on Slide 5. {Q}",
         "choices": [
             "A network of several brain regions becomes active when the mind is not focused outward.",
             "One single area of the brain shuts down completely whenever people feel bored.",
             "The brain is more active during easy tasks than during mild boredom.",
             "Boredom damages the brain regions used for daydreaming and memory.",
         ]},
        {"t": "pagebreak"},
        {"t": "q", "qlabel": "5", "no": 37,
         "stem": "For the Discussion on Slide 6, look at the four students' daily habits below. According "
                 "to the passage, which <u>two</u> students are already living in a way that lets them "
                 "benefit from boredom? {Q}",
         "choices": [
             "Ami and Barry", "Ami and Chihiro", "Ami and Dean",
             "Barry and Chihiro", "Barry and Dean", "Chihiro and Dean",
         ], "cols": 2},
        {"t": "html", "html": _Q7_CARDS},
    ]}],
}

# =====================================================================
# ============================ 第8問 ==================================
# =====================================================================

def _opinion(name, job, text):
    return (f'<div style="border-bottom:1px solid #666;padding:2.2mm 0">'
            f'<div style="font-weight:700;margin-bottom:.6mm">{name} ({job})</div>'
            f'<div style="text-align:justify">{text}</div></div>')

_Q8_OPINIONS = f"""
<div style="border:1.3px solid #333;padding:1mm 4mm 3mm;margin:3mm 1mm;
  font-family:'Times New Roman','Hiragino Mincho ProN',serif;font-size:9.8pt;line-height:1.68">
 {_opinion("Akane", "teacher",
   "I worry about fairness. AI writing tools are improving fast, but the best ones cost money. "
   "Students from wealthy families can pay for powerful paid versions, while others must use weak "
   "free ones or nothing at all. If we allow AI in schoolwork, we may simply be rewarding students "
   "for how much their families can spend, not for how hard they think. Education should narrow the "
   "gap between rich and poor, not widen it.")}
 {_opinion("Fiona", "software engineer",
   "Let me raise a question rather than give an answer. Suppose two students write equally good "
   "essays, but one did it alone and the other used an AI assistant. Have they really shown the same "
   "ability? I build these tools, so I know how helpful they are. Yet I am not sure a teacher can "
   "tell the two essays apart, and if grades are supposed to measure a student's own thinking, that "
   "uncertainty troubles me.")}
 {_opinion("Jack", "high school student",
   "I say let us use it. When I get stuck, an AI tutor explains a maths problem in three different "
   "ways until I finally understand. It is like having a patient teacher available at midnight. My "
   "grades have gone up, and I actually enjoy studying more now. Banning such a useful tool would "
   "just make school feel out of touch with the real world we are heading into.")}
 {_opinion("Michael", "retired teacher",
   "In my day, students struggled with a problem for hours, and that struggle was the learning. I "
   "fear that if AI hands them the answer instantly, they will never build the patience and deep "
   "understanding that hard thinking gives. Skipping the difficult middle part is unfair to the "
   "students themselves, because they lose the very effort that makes knowledge stick.")}
 <div style="padding:2.2mm 0">
  <div style="font-weight:700;margin-bottom:.6mm">Tamara (librarian)</div>
  <div style="text-align:justify">Remember when calculators first entered classrooms? Teachers were
  sure students would forget how to do arithmetic. Instead, we learned to use calculators for the
  dull parts and save our brains for real problem-solving, and today nobody complains. AI is the
  next calculator. Used well, it frees students from busywork so they can focus on ideas that
  matter. Technology, handled wisely, raises the quality of learning.</div>
 </div>
</div>
"""

# --- POSITIONメモ (手書き風) ---
_Q8_POSITION = """
<div class="hnote handw" style="font-size:10.4pt;line-height:1.95">
 <div><b>POSITION:</b> We should welcome the use of AI tools in schoolwork.</div>
 <div>&bull; <span class="qslot">40</span> and <span class="qslot">41</span> support this position the most.</div>
 <div>&bull; An idea shared by these two people is that <span class="qslot">42</span>.</div>
</div>
"""

# --- エッセイアウトライン (手書き風・注記はセリフ体) ---
_Q8_OUTLINE = """
<div class="outline handw" style="font-size:10.2pt;line-height:1.7">
 <div class="o-t" style="font-size:12pt">Technology in the Classroom</div>

 <div style="font-weight:700;margin:1.5mm 0 .5mm">Introduction</div>
 <div style="margin-left:2mm">Schools are debating whether to allow AI tools in learning.<br>
  I believe we should welcome them.</div>

 <div style="font-weight:700;margin:2.5mm 0 .5mm">Body</div>
 <ul style="margin:.3mm 0;padding-left:1.4em">
  <li style="margin:1mm 0">REASON 1:
   <span style="font-family:'Times New Roman',serif">[the common idea in Step 2]</span></li>
  <li style="margin:1mm 0">REASON 2:
   <span class="qslot">43</span>
   <span style="font-family:'Times New Roman',serif">[based on Source A]</span></li>
  <li style="margin:1mm 0">REASON 3: AI can reduce the busywork that tires students out
   <span style="font-family:'Times New Roman',serif">[based on support from Source B:
   <span class="qslot">44</span>]</span></li>
 </ul>

 <div style="font-weight:700;margin:2.5mm 0 .5mm">Conclusion</div>
 <div style="margin-left:2mm">Handled wisely, AI raises the quality of learning.<br>
  Schools should embrace it, with sensible rules.</div>
</div>
"""

# --- Source A (論説 約155語) ---
_Q8_SOURCE_A = """
<div class="passage" style="font-family:'Times New Roman','Hiragino Mincho ProN',serif;
  font-size:9.9pt;line-height:1.75;text-align:justify;padding:4mm 5mm;margin:3mm 1mm">
 <div style="font-weight:700;margin-bottom:1.5mm">Source A</div>
 <p style="margin:1mm 0">Some critics argue that AI writing tools threaten the honesty of school
 assessment: if a machine can produce an essay, how can a grade reflect a student's own ability?
 The concern is real, but a total ban is not the answer. The smarter path is to combine the
 technology with clear rules. When calculators entered mathematics classes in the 1970s, schools
 did not forbid them; instead, they designed new kinds of questions and taught students when the
 tool was and was not appropriate. The same can be done with AI. In 2023, several universities
 introduced "AI-use statements," requiring students to record exactly how they used AI in an
 assignment. Far from cheapening the work, such rules made students think more carefully about
 their own contribution. Guided by sensible rules, AI can support learning while still keeping
 grades meaningful &mdash; the two goals can be achieved together.</p>
</div>
"""

# --- Source B 棒グラフ (SVG・3群×3特徴・境界値トラップ) ---
# 数値: understanding: 78/81/72  time: 55/49/44  stress: 62/71/68
# 群 = beginners(黒ドット) / intermediate(グレー) / advanced(白)
def _q8_barchart():
    groups = ["Help in\nunderstanding", "Time saved\non busywork", "Less stress\nfrom homework"]
    data = {
        "understanding": [78, 81, 72],
        "time": [55, 49, 44],
        "stress": [62, 71, 68],
    }
    order = ["understanding", "time", "stress"]
    W, H = 440, 250
    ml, mr, mt, mb = 46, 12, 16, 54
    plot_h = H - mt - mb
    plot_w = W - ml - mr
    x0 = ml
    y0 = H - mb

    def y(v):
        return y0 - (v / 100.0) * plot_h

    parts = [f"<svg viewBox='0 0 {W} {H}' width='420' "
             f"style='font-family:\"Helvetica Neue\",Arial,sans-serif'>"]
    parts.append("<defs><pattern id='dots' width='5' height='5' patternUnits='userSpaceOnUse'>"
                 "<rect width='5' height='5' fill='#fff'/>"
                 "<circle cx='2.5' cy='2.5' r='1.15' fill='#222'/></pattern></defs>")
    # Y grid + labels
    for v in range(0, 101, 10):
        yy = y(v)
        parts.append(f"<line x1='{x0}' y1='{yy:.1f}' x2='{x0+plot_w}' y2='{yy:.1f}' "
                     f"stroke='#ccc' stroke-width='0.7'/>")
        parts.append(f"<text x='{x0-5}' y='{yy+3:.1f}' font-size='9' text-anchor='end'>{v}</text>")
    # axes
    parts.append(f"<line x1='{x0}' y1='{mt}' x2='{x0}' y2='{y0}' stroke='#333' stroke-width='1.3'/>")
    parts.append(f"<line x1='{x0}' y1='{y0}' x2='{x0+plot_w}' y2='{y0}' stroke='#333' stroke-width='1.3'/>")
    parts.append(f"<text x='{x0-33}' y='{mt+plot_h/2:.1f}' font-size='9' text-anchor='middle' "
                 f"transform='rotate(-90 {x0-33} {mt+plot_h/2:.1f})'>Students out of 100</text>")
    fills = ["url(#dots)", "#9a9a9a", "#ffffff"]
    n_cat = len(order)
    cat_w = plot_w / n_cat
    bar_w = 22
    gap = 3
    group_w = bar_w * 3 + gap * 2
    for ci, key in enumerate(order):
        cx = x0 + cat_w * ci + (cat_w - group_w) / 2
        vals = data[key]
        for bi, v in enumerate(vals):
            bx = cx + bi * (bar_w + gap)
            by = y(v)
            parts.append(f"<rect x='{bx:.1f}' y='{by:.1f}' width='{bar_w}' height='{y0-by:.1f}' "
                         f"fill='{fills[bi]}' stroke='#333' stroke-width='1'/>")
            parts.append(f"<text x='{bx+bar_w/2:.1f}' y='{by-2:.1f}' font-size='9' "
                         f"text-anchor='middle' font-weight='bold'>{v}</text>")
        lines = groups[ci].split("\n")
        lx = x0 + cat_w * ci + cat_w / 2
        for li, ln in enumerate(lines):
            parts.append(f"<text x='{lx:.1f}' y='{y0+14+li*11}' font-size='9' "
                         f"text-anchor='middle'>{ln}</text>")
    # legend
    ly = H - 12
    legend = [("Beginners", "url(#dots)"), ("Intermediate", "#9a9a9a"), ("Advanced", "#ffffff")]
    lx = x0 + 8
    for name, f in legend:
        parts.append(f"<rect x='{lx:.1f}' y='{ly-8}' width='11' height='11' fill='{f}' "
                     f"stroke='#333' stroke-width='0.9'/>")
        parts.append(f"<text x='{lx+15:.1f}' y='{ly+1}' font-size='9'>{name}</text>")
        lx += 15 + len(name) * 5.4 + 20
    parts.append("</svg>")
    return "".join(parts)

_Q8_SOURCE_B = f"""
<div class="passage" style="font-family:'Times New Roman','Hiragino Mincho ProN',serif;
  font-size:9.9pt;line-height:1.72;text-align:justify;padding:4mm 5mm;margin:3mm 1mm">
 <div style="font-weight:700;margin-bottom:1.5mm">Source B</div>
 <p style="margin:1mm 0 2mm">A study asked three groups of 100 students each &mdash; beginners,
 intermediate learners, and advanced learners &mdash; who had used an AI study assistant for one
 term. The graph below shows, for each group, the number of students out of 100 who responded
 positively that the tool gave them help in understanding, saved them time on busywork, and left
 them with less stress from homework.</p>
 <div class="fig" style="text-align:center">{_q8_barchart()}</div>
</div>
"""

_SEC8 = {
    "no": 8, "points": 17,
    "parts": [{"label": "", "blocks": [
        {"t": "p", "text": "You are working on an essay about <b>the use of AI tools in schools</b>, "
                           "following the steps below:"},
        {"t": "boxnote", "title": "", "lines": [
            "<b>Step 1</b>　Read a range of opinions posted online about the topic.",
            "<b>Step 2</b>　Decide your own position on the topic.",
            "<b>Step 3</b>　Make an outline for your essay using an additional source.",
        ]},
        {"t": "html", "html": '<div style="font-weight:700;margin:3mm 0 1mm">'
                              '&#9654; [Step 1] Read a range of opinions</div>'},
        {"t": "html", "html": _Q8_OPINIONS},
        {"t": "q", "qlabel": "1", "no": 38,
         "stem": "Which of the following best summarizes Akane's opinion? {Q}",
         "choices": [
             "AI tools should be banned because they make students lazy.",
             "Free AI tools are just as powerful as the paid ones.",
             "Allowing AI may reward family wealth rather than a student's effort.",
             "Teachers cannot tell whether a student used an AI tool.",
         ]},
        {"t": "q", "qlabel": "2", "no": 39,
         "stem": "Both Fiona and Michael mention that {Q}.",
         "choices": [
             "using AI can take away something valuable from a student's own learning",
             "AI tools are too expensive for most families to afford",
             "students today enjoy studying far more than they used to",
             "calculators once faced the same criticism that AI faces now",
         ]},
        {"t": "pagebreak"},
        {"t": "html", "html": '<div style="font-weight:700;margin:2mm 0 1mm">'
                              '&#9654; [Step 2] Decide your own position</div>'},
        {"t": "html", "html": _Q8_POSITION},
        {"t": "q", "qlabel": "3", "no": 40,
         "stem": "Complete the POSITION memo above. You must have <u>all</u> of "
                 "<span class=\"qslot\">40</span>–<span class=\"qslot\">42</span> correct to "
                 "get points.<br><br>"
                 "<b>Options for <span class=\"qslot\">40</span> and <span class=\"qslot\">41</span> "
                 "(the order does not matter):</b>",
         "choices": ["Akane", "Fiona", "Jack", "Michael", "Tamara"], "cols": 5},
        {"t": "choices", "for": "<b>Options for <span class=\"qslot\">42</span>:</b>",
         "items": [
             "technology, used wisely, can improve the quality of learning",
             "AI mainly benefits students whose families are wealthy",
             "grades can no longer measure a student's true ability",
             "students should struggle on their own without any tools",
         ], "cols": 1, "labels": ["①", "②", "③", "④"]},
        {"t": "html", "html": '<div style="height:2mm"></div>'},
        {"t": "html", "html": '<div style="font-weight:700;margin:3mm 0 1mm">'
                              '&#9654; [Step 3] Make an outline using an additional source</div>'},
        {"t": "html", "html": _Q8_OUTLINE},
        {"t": "html", "html": _Q8_SOURCE_A},
        {"t": "q", "qlabel": "4", "no": 43,
         "stem": "Based on Source A, which of the following is the most appropriate for "
                 "<b>REASON 2</b> in the essay outline? {Q}",
         "choices": [
             "AI tools should be completely banned to protect honest grading.",
             "With sensible rules, AI can support learning while keeping grades meaningful.",
             "Calculators proved that any new technology eventually harms education.",
             "Universities should stop asking students how they used AI.",
         ]},
        {"t": "pagebreak"},
        {"t": "html", "html": _Q8_SOURCE_B},
        {"t": "q", "qlabel": "5", "no": 44,
         "stem": "Based on Source B, which of the following best supports <b>REASON 3</b> in the essay "
                 "outline? {Q}",
         "choices": [
             "In every group, over half of the students said the tool saved them time on busywork; "
             "this shows AI cuts down tiring routine work.",
             "For “less stress from homework,” every group had more than half respond "
             "positively, and no group fell below 60; this shows AI eases the pressure of homework.",
             "Advanced learners responded most positively about time saved, proving that AI helps "
             "skilled students most with routine tasks.",
             "More than three out of four students in every group found the tool reduced stress, "
             "showing that AI removes almost all homework pressure.",
         ]},
    ]}],
}

SECTIONS = [_SEC6, _SEC7, _SEC8]

# =====================================================================
# ========================= ANS_SECTIONS ==============================
# =====================================================================

ANS_SECTIONS = [
    {
        "section": 6, "points": 12,
        "answers": [
            {"qno": 24, "answer": "①・②", "points": 3},   # 24・25 完答で3点(順不同)
            {"qno": 25, "answer": "①・②", "points": 0},
            {"qno": 26, "answer": "①", "points": 3},   # 26→27→28→29 = ①→④→③→②(完答3点)
            {"qno": 27, "answer": "④", "points": 0},
            {"qno": 28, "answer": "③", "points": 0},
            {"qno": 29, "answer": "②", "points": 0},
            {"qno": 30, "answer": "②", "points": 3},
            {"qno": 31, "answer": "①", "points": 3},
        ],
        "kai": [
            {"heading": "問1 (解答番号24・25)", "blocks": [{"t": "p", "text":
                "正解①・②(順不同・完答3点)。<b>Old man</b>欄の空所2つを、5択から本文の記述に合う2つで埋める。"
                "①「言葉ではなく行動で優しさを示す」は、無言で2個目のtaiyakiを袋に入れる/靴を黙って預かる、という一連の"
                "描写と、物語末尾「His kindness was in what he did, not in what he said」に直接一致する。"
                "②「若い頃はランナーだった」は、色あせた写真の走者が店主本人だと娘の目(同じ鋭い目)や手書きメモで示される"
                "描写に一致する。誤答:③「訪れる生徒と陽気におしゃべりする」は「He rarely spoke」「without more than a "
                "nod」の逆(本文と逆転型)。④「高い方のtaiyakiを売るのを拒む」はcustard(高い方)を黙っておまけに入れる"
                "描写と矛盾(誤結合型)。⑤「Harukaにtaiyakiの作り方を教える」は本文に一切記述がない(言及なし型)。"}]},
            {"heading": "問2 (解答番号26→27→28→29) — 全列挙で唯一解を検証", "blocks": [{"t": "p", "text":
                "正解 26=① → 27=④ → 28=③ → 29=②。5択のうち<b>回想(中学時代)</b>の出来事4つを選び時系列に並べる。"
                "まずダミーの特定:⑤「発表前に公園でred-bean taiyakiを食べた」は<b>額縁(現在)</b>の出来事なので"
                "回想に含まれない=これが除外する1つ。残る①②③④を本文の順に並べる。本文の時系列は "
                "(i)毎日通ううちに写真を見て走者=店主かと気づく〔①〕→ (ii)大会前日に靴を置き忘れ翌朝返してもらう〔④〕"
                "→ (iii)大会当日、買っていないcustard taiyakiを袋に発見〔③〕→ (iv)報告に行くと店主不在、娘に手書き"
                "メモを託す〔②〕。したがって ①→④→③→② が唯一の正しい順。"}]},
            {"heading": "問2 補足(選択肢の対応確認)", "blocks": [{"t": "p", "text":
                "選択肢と本文の対応:①「古い写真の男がMr. Satoに似ていると気づいた」=第4段落(毎日通ううちに気づく・"
                "靴の件より前)。④「靴を置き忘れ翌朝返してもらった」=第5段落(大会前日〜当日朝)。③「買っていないcustard "
                "taiyakiを袋に発見」=第6段落(大会当日)。②「娘に手書きメモを託した」=第7段落(報告時)。よってマーク欄は"
                "26=①、27=④、28=③、29=②の順で一意に定まる。"}]},
            {"heading": "問3 (解答番号30)", "blocks": [{"t": "p", "text":
                "正解②。「The old man ___.」を4択で完成。本文全体で店主は「言葉少なだが、黙って小さな親切をする」人物"
                "として一貫して描かれる(靴を黙って預かる/2個目を無言で入れる)。②「小さなことを人のためにして、静かに"
                "気にかける」がこの行動パターンの抽象化。①「大声で応援して励ます」は「never once heard him say good "
                "luck」の逆。③「質問した生徒にだけ助言する」は本文に根拠がなく、Harukaはそもそも質問できずにいた。"
                "④「過去を恥じて隠す」は誤結合型で、写真を店内に掲げている事実(隠していない)と矛盾する。"}]},
            {"heading": "問4 (解答番号31)", "blocks": [{"t": "p", "text":
                "正解①。「Haruka's ___.」を4択で。額縁の現在パートで、彼女は発表直前にtaiyakiを口にして店主の思い出から"
                "力を得ており(「brought her back」「the lesson had stayed with her」)、①「男の無言の支えの記憶が今も"
                "彼女に力を与えている」が長期的影響として正しい。②「マラソンで走りたいという願い」は本文になし(言及なし型)。"
                "③「taiyakiを食べる習慣が節約に役立った」は、お金に余裕がなかった描写を逆手に取った誤結合型で因果が本文と"
                "逆(むしろ出費)。④「娘との友情が今も続く」は、娘とは一度会っただけで継続の記述がない(言及なし型)。"}]},
        ],
    },
    {
        "section": 7, "points": 16,
        "answers": [
            {"qno": 32, "answer": "②", "points": 3},
            {"qno": 33, "answer": "①・②", "points": 3},
            {"qno": 34, "answer": "①・②", "points": 3},
            {"qno": 35, "answer": "③", "points": 3},
            {"qno": 36, "answer": "①", "points": 2},
            {"qno": 37, "answer": "④", "points": 2},   # Barry and Chihiro
        ],
        "kai": [
            {"heading": "問1 (解答番号32)", "blocks": [{"t": "p", "text":
                "正解②。スライド2「The Nature of Boredom / It happens ___.」。第2段落の定義「boredom is the "
                "unpleasant feeling that comes when we want to be engaged in a satisfying activity but "
                "cannot find one」の言い換えが②「満足できる何かをしたいのにそれが見つからないとき」。①「難しく重要な"
                "仕事をしているときだけ」は本文と逆(退屈は無為のときに起こる)。③「休むと脳が働かなくなるから」は第6段落"
                "「an empty moment is not an empty brain」に反する。④「暇が多すぎる人に主に起こる」は本文になし"
                "(20%という頻度は誰にでも起こる一般的感情として提示されている)。"}]},
            {"heading": "問2 (解答番号33・34)", "blocks": [{"t": "p", "text":
                "正解①・②(順不同・各3点)。スライド3「Two Faces of Boredom」=退屈の負の面と正の面を1つずつ。"
                "①「不注意なミスや成績低下につながりうる」は第3段落(costs:poor concentration/careless mistakes/lower "
                "grades)の言い換え。②「心をより創造的なアイデアへ押しやりうる」は第4段落(benefits)の言い換え。誤答は"
                "すべて「本文と逆」型:③「退屈な作業への集中を助ける」は「poor concentration」の逆。④「いつもより食べる"
                "量を減らす」は「overeating」の逆。⑤「遠い過去の記憶を良くする」は本文に言及なし(wandering networkが"
                "過去を思い出す際に働くとはあるが、記憶力が向上するとは述べていない)。"}]},
            {"heading": "問3 (解答番号35)", "blocks": [{"t": "p", "text":
                "正解③。スライド4「Why Does a Dull Moment Spark Ideas?」。第4段落「Once the outside world stops "
                "giving it interesting input, the mind turns inward and starts generating its own」の言い換えが"
                "③「外からの入力がない心は、自分自身のアイデアを生み出し始める」。①「面白い作業が現れるまで心は全活動を"
                "止める」は本文と逆(心は無為を嫌い内側に向かう)。②「不快感が画面で時間を埋めさせる」は、我々がそうしがち"
                "という通説であって、アイデアが生まれる仕組みの説明ではない(論点ずらし)。④「数字を速く写せるよう訓練する」"
                "は実験の手段(退屈を作る作業)を取り違えた誤結合。"}]},
            {"heading": "問4 (解答番号36)", "blocks": [{"t": "p", "text":
                "正解①。スライド5「A Finding From Brain Research」。第6段落「a set of connected regions ... became "
                "highly active ... switches on when we are not focused on the outside world」の正確な理解が"
                "①「複数の脳領域のネットワークが、心が外に向いていないときに活発になる」。②「単一の領域が完全に停止する」"
                "はsingle/completelyで断定を歪める誤り(実際は複数領域が活性化)。③「退屈時より簡単な作業時の方が活発」は"
                "2021年アイルランドの研究(mild boredomの方がより活発)の逆。④「退屈が脳領域を損傷する」は本文に根拠なし。"}]},
            {"heading": "問5 (解答番号37) — C(4,2)=6通り全列挙で唯一解を検証", "blocks": [{"t": "p", "text":
                "正解④「Barry and Chihiro」。本文のTips=①一日に意図的な隙間を作り画面で埋めない(散歩・バス移動で心を"
                "さまよわせる)②退屈=怠けではなく新しいことへの合図と捉える(=単純で入力の少ない時間を確保する)。"
                "4人を照合すると、Barry=毎朝の川沿いサイクリング+週末のハイキングで、景色以外に何もない屋外の時間に一番"
                "アイデアが湧く→隙間で心をさまよわせるTipに<b>合致</b>。Chihiro=週末はスマホを切り、銭湯で何もせず長く"
                "浸かる→単純で入力の少ない時間を確保するTipに<b>合致</b>。Ami=読書家だが深夜まで起きて強い緑茶で覚醒を保つ"
                "→常に入力を詰め込み隙間を作らず、睡眠も削るので<b>違反</b>。Dean=起床直後からスマホでコメント対応、一日中"
                "アカウントを確認→隙間を全て画面で埋めるので<b>違反</b>。"}]},
            {"heading": "問5 補足(組合せ6通りの検証)", "blocks": [{"t": "p", "text":
                "①Ami&Barry=Ami違反で不可。②Ami&Chihiro=Ami違反で不可。③Ami&Dean=両者違反で不可。"
                "④Barry&Chihiro=両者合致で<b>正解</b>。⑤Barry&Dean=Dean違反で不可。⑥Chihiro&Dean=Dean違反で不可。"
                "合致する2名を同時に選べるのは④のみで一意に定まる。"}]},
        ],
    },
    {
        "section": 8, "points": 17,
        "answers": [
            {"qno": 38, "answer": "③", "points": 3},
            {"qno": 39, "answer": "①", "points": 3},
            {"qno": 40, "answer": "③・⑤", "points": 4},
            {"qno": 41, "answer": "③・⑤", "points": 0},
            {"qno": 42, "answer": "①", "points": 0},
            {"qno": 43, "answer": "②", "points": 3},
            {"qno": 44, "answer": "②", "points": 4},
        ],
        "kai": [
            {"heading": "問1 (解答番号38)", "blocks": [{"t": "p", "text":
                "正解③。Akaneの意見の要旨を問う。彼女の主張は「有料の高性能AIは裕福な家庭の生徒だけが使え、AIを許可すると"
                "『どれだけ努力して考えたか』ではなく『家がいくら払えるか』を評価してしまう」=公平性の問題。③「AIの許可は、"
                "生徒の努力よりも家庭の裕福さを評価してしまう恐れがある」がmain pointの言い換え。①「怠けるから禁止すべき」は"
                "Akaneでなく Michael の論点(別人の意見との混同)。②「無料AIも有料AIと同じくらい高性能」は彼女の主張の逆。"
                "④「教師は使用を見分けられない」は Fiona の論点(誤結合)。"}]},
            {"heading": "問2 (解答番号39)", "blocks": [{"t": "p", "text":
                "正解①。FionaとMichaelの<b>共通点</b>を問う。Fiona=AIを使った生徒と自力の生徒が同じ力を示したとは言えず、"
                "成績が本人の思考を測れなくなる懸念。Michael=AIが即答を渡すと、苦しむ過程(=学び)を飛ばし、忍耐と深い理解を"
                "築けなくなる。両者に共通するのは①「AIを使うと生徒自身の学びから価値あるものが失われうる」。②「AIは高価で"
                "多くの家庭に手が届かない」はAkaneのみ。③「今の生徒は昔より勉強を楽しむ」はJackのみ。④「電卓もかつて同じ"
                "批判を受けた」はTamaraのみ(=片方だけ/どちらも非言及の型)。"}]},
            {"heading": "問3 (解答番号40・41・42) — 完答", "blocks": [{"t": "p", "text":
                "正解 40・41=③・⑤(Jack・Tamara/順不同)、42=①(3枠すべて正解で4点=完答)。立場「学校の学習でAIの利用を"
                "歓迎すべき」を最も支持するのは賛成派の2人。Jack(高校生)=AIチューターで理解が進み成績も上がった→賛成。"
                "Tamara(司書)=電卓と同じでうまく使えば雑務から解放され学びの質が上がる→賛成。Akane・Michaelは反対、"
                "Fionaは条件付き/問題提起であり『支持』ではない。42=2人に共通する考えは①「technology, used wisely, can "
                "improve the quality of learning(技術は賢く使えば学びの質を高める)」で、Jackの『便利な道具で学びが効果的・"
                "楽しくなる』とTamaraの『うまく使えば学びの質が上がる』の共通項。②はAkane、③はFiona、④はMichaelの主張で"
                "2人の共通項ではない。"}]},
            {"heading": "問4 (解答番号43)", "blocks": [{"t": "p", "text":
                "正解②。Source Aは「AIは採点の公正さ(integrity)を脅かしうるが、全面禁止でなく明確なルールと併用するのが"
                "賢い道。電卓や大学のAI-use statementの実例のように、ルール次第で学びを支えつつ成績の意味も保てる」という"
                "論説。REASON 2(Source Aに基づく)として最適なのは②「賢明なルールがあれば、AIは成績の意味を保ちながら学びを"
                "支えられる」=本文の結論の言い換え。①「公正な採点を守るため完全に禁止すべき」は本文が退ける立場(integrityを"
                "逆手に取った誤答)。③「電卓は新技術が結局教育を害すると証明した」は本文の電卓の例の趣旨(共存できた)と逆。"
                "④「大学はAI使用の申告をやめるべき」は本文の推奨(申告制が良い効果)と逆。"}]},
            {"heading": "問5 (解答番号44) — グラフ数値×論点適合の二重判定", "blocks": [{"t": "p", "text":
                "正解②。REASON 3=「AIは生徒を疲れさせる雑務(busywork)を減らし、宿題の負担・ストレスを和らげる」。Source B"
                "の数値は understanding=78/81/72、time saved on busywork=55/49/44、less stress from homework=62/71/68。"
                "①は「time savedで全群が過半数(50超)」と主張するが intermediate=49・advanced=44 で50未満のため数値が誤り"
                "(境界値トラップ:50を跨ぐ)。②は「less stress from homeworkで全群が過半数、かつどの群も60を下回らない」="
                "62・71・68 で正しく、REASON 3(宿題のストレス軽減=雑務削減の裏づけ)にも適合するので正解。③「advancedが"
                "time savedで最も肯定的」は44で実際は最小値(数値誤読)。④「4分の3超(75超)がストレス軽減と回答」は62・71・68"
                "で75に届かず誤り(境界値トラップ:75を跨ぐ)。"}]},
        ],
    },
]
