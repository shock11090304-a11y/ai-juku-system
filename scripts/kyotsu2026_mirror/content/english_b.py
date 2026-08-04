# -*- coding: utf-8 -*-
"""english_b.py: 2026共通テスト英語(リーディング) そっくり類似 — 第4問・第5問。

第4問 (配点12・解答番号14〜17): 生徒の草稿+顧問の手書き風コメント(推敲問題)
  - 下線(1)(3)(4) + 波括弧(2) + 挿入マーカー<A>〜<D> + Overall comments帯
  - 設問4形式: 追加句選択 / 文挿入位置 / 文差替 / 句差替
第5問 (配点16・解答番号18〜23): 3素材連鎖 リーフレット→オンライン申込フォーム→返信メール
  - A〜D命題×6択組合せ / "not"下線の除外特定 / 順不同2枠(22・23)

マーク番号は english_a.py(第3問が13で終了)に接続し、実物2026と同一の 14〜23 を使用。
"""

# ==================== 第4問 素材: 2カラム草稿 ====================

_Q4_DRAFT = """
<div class="mat" style="font-family:'Times New Roman','Hiragino Mincho ProN',serif;font-size:9.6pt;line-height:1.72;padding:4mm 4.5mm">
 <div class="twocol">
  <div>
   <div style="font-style:italic;font-size:8.6pt">February 2026<br>English Club News</div>
   <div style="text-align:center;font-weight:700;font-size:11.5pt;margin:1.2mm 0 2mm">Join Health Week Events</div>
   <p style="margin:1mm 0;text-align:justify">Do you get enough sleep, eat well, and exercise every day?
   Many students say no. According to a recent school survey, more than half of us skip breakfast at
   least once a week. To help everyone build better habits, our school will hold Health Week from
   16 to 20 February. Here are its three main events.</p>
   <p style="margin:2mm 0;text-align:justify">The first event is <sup>(1)</sup><u>a healthy recipe contest</u>.
   Create an original recipe for a well-balanced meal and send it to the club by 13 February. During
   Health Week, everyone can vote for their favorites in the cafeteria. The top three recipes will be
   chosen and posted on the school website, so please don't miss this chance.</p>
   <div style="display:flex;align-items:center;gap:1.5mm;margin:2mm 0">
     <p style="flex:1;margin:0;text-align:justify">The second event is a morning walking rally in Green
     Park, and students from other schools are also welcome. <b>&lt;A&gt;</b> First, make a team of three
     people and sign up at the student office by 13 February. <b>&lt;B&gt;</b> On the day of the rally, come
     to the main gate of the park by 8:30 a.m. to receive a route map and a stamp card. <b>&lt;C&gt;</b> While
     walking the course, find the ten checkpoints shown on the map and collect a stamp at each one.
     <b>&lt;D&gt;</b> The results will be announced at the closing ceremony, and the winning team will be
     introduced on the town's website.</p>
     <div style="font-size:32pt;font-weight:300;line-height:1;flex:0 0 auto">}</div>
     <div class="handw" style="font-size:9.5pt;flex:0 0 auto">(2)</div>
   </div>
   <p style="margin:2mm 0;text-align:justify">The third event is a healthy snack class. Bring vegetables
   or fruit from home and create your own original snack with our cooking teacher.
   <sup>(3)</sup><u>Cooking at home saves you a lot of money.</u> The best snack will be served in the
   cafeteria after the event.</p>
   <p style="margin:2mm 0 1mm;text-align:justify">As you can see, Health Week is not just a school event.
   It is a good chance to <sup>(4)</sup><u>enjoy cooking with your friends</u>. Why don't you start with
   something small, like walking to school or eating breakfast every morning? Let's make healthy habits
   together during Health Week!</p>
  </div>
  <div class="handw" style="border-left:1px solid #555;padding-left:3mm;font-size:9.6pt;line-height:1.7">
   <div style="font-weight:700;text-decoration:underline;margin-bottom:1mm">Comments:</div>
   <p style="margin:1.5mm 0">(1) Why are you holding this contest? Add your purpose here.</p>
   <p style="margin:1.5mm 0">(2) Readers will want to know how the winning team is decided. Add that
   information.</p>
   <p style="margin:1.5mm 0">(3) This sentence does not fit this paragraph. Rewrite it.</p>
   <p style="margin:1.5mm 0">(4) This does not express the main message of your newsletter. Rewrite it.</p>
  </div>
 </div>
 <div class="handw" style="border-top:1.2px solid #333;margin-top:2.5mm;padding-top:1.5mm;font-size:9.6pt">
  <b>Overall comments:</b> Well done! Your newsletter gives clear information about all three events.
  I'm sure it will encourage many students to join. I look forward to reading the final version.
 </div>
</div>
"""

# ==================== 第5問 素材1: リーフレット ====================

_PENNANTS = "".join(
    f'<path d="M{8 + i * 33} 3 L{8 + i * 33 + 15} 3 L{8 + i * 33 + 7.5} 20 Z" '
    f'fill="{"#555" if i % 2 else "none"}" stroke="#333" stroke-width="1.4"/>'
    for i in range(14)
)

_GAME_ART = """
<svg viewBox="0 0 100 74" width="80" style="flex:0 0 auto">
 <rect x="6" y="26" width="34" height="34" rx="5" fill="none" stroke="#333" stroke-width="2.2"/>
 <circle cx="15" cy="35" r="2.6" fill="#333"/><circle cx="23" cy="43" r="2.6" fill="#333"/>
 <circle cx="31" cy="51" r="2.6" fill="#333"/>
 <rect x="46" y="36" width="24" height="24" rx="4" fill="none" stroke="#333" stroke-width="2"/>
 <circle cx="58" cy="48" r="2.6" fill="#333"/>
 <circle cx="86" cy="30" r="7" fill="none" stroke="#333" stroke-width="2.2"/>
 <path d="M77 62 Q77 45 86 42 Q95 45 95 62 Z" fill="none" stroke="#333" stroke-width="2.2"/>
</svg>
"""

_Q5_FLYER = f"""
<div class="flyer">
 <svg viewBox="0 0 470 24" width="440" style="display:block;margin:0 auto 1.5mm">
  <line x1="4" y1="3" x2="466" y2="3" stroke="#333" stroke-width="1.4"/>{_PENNANTS}
 </svg>
 <div class="f-title">Rainbow Hall Community Centre</div>
 <div class="f-sub" style="font-weight:700;font-size:10.5pt">Game Recommendations &amp; Volunteers Wanted</div>
 <hr>
 <p style="margin:1.5mm 0;text-align:justify">The first Family Game Festa will be held from 7 to 14
 February 2026, so that young children in our town can discover how much fun board games are.
 Recommended games will be displayed in the entrance hall all week. On the final day, families can try
 them at 'Game Time' in the kids corner, and joining is free.</p>
 <p style="margin:1.5mm 0;text-align:justify">We are now looking for two kinds of help: board games that
 preschool children can enjoy, and volunteers to help children play at 'Game Time'. Volunteers will
 receive a free drink ticket for the hall café as a small thank-you.</p>
 <div style="display:flex;gap:4mm;align-items:center;margin:1.5mm 0">
  <div style="flex:1"><b>Please note:</b>
   <ul style="margin:.5mm 0 0;padding-left:1.3em">
    <li>Games from any country are welcome.</li>
    <li>Each game must be £25 or less.</li>
    <li>Recommendations must arrive between 10 December 2025 and 16 January 2026.</li>
   </ul>
  </div>
  {_GAME_ART}
 </div>
 <hr>
 <p style="margin:1mm 0">To recommend a game or sign up as a volunteer, please use <u>the online form</u>.<br>
 For questions, contact: ✉ familygamefesta@***.hall.uk</p>
</div>
"""

# ==================== 第5問 素材2: オンラインフォーム ====================

_FBOX = 'border:1px solid #777;padding:0 1.5mm;display:inline-block;min-width:16mm'


def _game_block(title, designer, year, price, artist, comment):
    return f"""
 <div style="border:1.1px solid #555;padding:2mm 3mm;margin:2.5mm 0">
  <div style="margin:.6mm 0">Title <span style="{_FBOX}">{title}</span>
   Designed by <span style="{_FBOX}">{designer}</span></div>
  <div style="margin:.6mm 0">Year <span style="{_FBOX}">{year}</span>
   Price <span style="{_FBOX}">{price}</span>
   Box art by <span style="{_FBOX}">{artist}</span></div>
  <div style="margin:1mm 0 .4mm">Comment</div>
  <div style="border:1px solid #777;padding:1mm 2mm;line-height:1.62;text-align:justify">{comment}</div>
 </div>"""


_Q5_FORM = f"""
<div class="mat" style="padding:3.5mm 4.5mm">
 <div class="mat-t">Family Game Festa Online Form</div>
 <div style="margin:1.2mm 0">Name <span style="{_FBOX}">**** ******</span>
  Email <span style="{_FBOX}">********@******</span></div>
 <div style="margin:1.2mm 0">Will you be a 'Game Time' helper?　○ Yes　● No</div>
 <div style="font-weight:700;margin:2.5mm 0 1mm;border-bottom:1px solid #999;padding-bottom:.5mm">Game Recommendations</div>
{_game_block("Sunny Farm", "Taro Okada", "2019", "£12", "Taro Okada",
             "In this game, players help farm animals get back to the farmhouse before the rain starts. "
             "My little cousin is four, and she learned the rules in a few minutes. Everyone plays as one "
             "team, so nobody feels sad about losing. It is perfect for children aged three to six.")}
{_game_block("The Sleepy Lion", "Emma Hill", "1988", "£24", "Emma Hill",
             "This is a classic game that parents in the UK often played when they were small. Players "
             "take turns moving their mice quietly past a sleeping lion without waking him up. Children "
             "have to stay quiet, so it is also popular with parents! Even three-year-olds can enjoy it.")}
{_game_block("Castle of Riddles", "Sofia Rossi", "2021", "£18", "Leo Rossi",
             "Players work together to escape from an old castle by solving word riddles. A clever fox "
             "appears and gives hints when players get stuck. The story is exciting, but some riddles "
             "need reading skills, so this game is better for children over ten. The beautiful box "
             "picture will catch everyone's eyes.")}
{_game_block("Good Night, Little Bear", "Nina Park", "2004", "£9", "Nina Park",
             "A bear family is getting ready for bed, and players help Little Bear find his toys before "
             "the lights go out. The pictures are soft and warm, and the game ends with everyone saying "
             "good night. Many nursery schools in my town use it for children aged three to five.")}
 <div style="text-align:center;margin-top:3mm">
  <span style="border:1.2px solid #555;background:#e4e4e4;padding:.6mm 5mm;border-radius:1mm">Submit</span>
  <span style="border:1.2px solid #555;background:#e4e4e4;padding:.6mm 5mm;border-radius:1mm">Cancel</span>
 </div>
</div>
"""

# ==================== 第5問 素材3: 返信メール ====================

_Q5_EMAIL = """
<div class="email">
 <div class="ehead">
  <div><b>From:</b> familygamefesta@***.hall.uk</div>
  <div><b>Date:</b> 14 January 2026</div>
  <div><b>Subject:</b> Game Recommendations</div>
 </div>
 <div class="ebody">
  <p style="margin:1mm 0">Thank you very much for recommending four board games for the Family Game
  Festa. Comments like yours will be translated into several languages by our staff, so that visitors
  from many countries can enjoy the display.</p>
  <p style="margin:1mm 0">We are happy to tell you that three of your games have been accepted (please
  see the attachment). Unfortunately, the other one does not match the age group of the Festa. We would
  be glad if you could suggest one more game. Just send us an email by 16 January.</p>
  <p style="margin:1mm 0">Also, we still need a few more helpers for 'Game Time' on the final day.
  Could you think about it again?</p>
  <p style="margin:1mm 0">Thanks again,<br>Festa Staff, Rainbow Hall Community Centre</p>
  <div style="border-top:1px dashed #888;margin-top:1.5mm;padding-top:1mm">📎 Attachment: <u>List of accepted games</u></div>
 </div>
</div>
"""

# ==================== SECTIONS ====================

SECTIONS = [
    {
        "no": 4, "points": 12,
        "parts": [{"label": "", "blocks": [
            {"t": "p", "text": "In English Club, you are writing an online newsletter to tell students "
                               "about your school's Health Week. This is your latest draft, which you are "
                               "improving based on comments from your club advisor."},
            {"t": "html", "html": _Q4_DRAFT},
            {"t": "q", "qlabel": "1", "no": 14,
             "stem": "Based on Comment (1), choose the best phrase to add after "
                     "<sup>(1)</sup><u>a healthy recipe contest</u>.",
             "choices": [
                 "to advertise the school cafeteria's new menu",
                 "to find the best young chef in the school",
                 "to help students think about their daily eating habits",
                 "to raise money for new kitchen equipment",
             ]},
            {"t": "q", "qlabel": "2", "no": 15,
             "stem": "Based on Comment (2), choose the best place to add the following sentence. {Q}"
                     "<br><br>　<b>The team that collects all ten stamps in the shortest time will be "
                     "the winner.</b>",
             "choices": ["<A>", "<B>", "<C>", "<D>"], "cols": 4},
            {"t": "q", "qlabel": "3", "no": 16,
             "stem": "Based on Comment (3), choose the best sentence to replace "
                     "<sup>(3)</sup><u>Cooking at home saves you a lot of money</u>.",
             "choices": [
                 "Eating healthy snacks instead of sweet ones is an easy way to improve your daily eating habits.",
                 "Fresh vegetables sold at the local morning market are much cheaper than those at big supermarkets.",
                 "Learning how to use a kitchen knife safely takes a long time for most beginner cooks.",
                 "Some sweet snacks sold at convenience stores are becoming more and more popular among high school students.",
             ]},
            {"t": "q", "qlabel": "4", "no": 17,
             "stem": "Based on Comment (4), choose the best phrase to replace "
                     "<sup>(4)</sup><u>enjoy cooking with your friends</u>.",
             "choices": [
                 "learn how to cook well-balanced meals",
                 "review and improve your daily habits",
                 "solve every health problem in our community",
                 "walk around the town with students from other schools",
             ]},
        ]}],
    },
    {
        "no": 5, "points": 16,
        "parts": [{"label": "", "blocks": [
            {"t": "p", "text": "You are studying in the UK. You found a leaflet at the community centre "
                               "near your host family's house, sent an online form, and later received an "
                               "email from the centre."},
            {"t": "html", "html": _Q5_FLYER},
            {"t": "pagebreak"},
            {"t": "html", "html": _Q5_FORM},
            {"t": "html", "html": _Q5_EMAIL},
            {"t": "pagebreak"},
            {"t": "q", "qlabel": "1", "no": 18,
             "stem": "What is the main purpose of the Family Game Festa?",
             "choices": [
                 "To collect old board games for children in other countries.",
                 "To find new full-time staff for the community centre.",
                 "To introduce young children to the fun of board games.",
                 "To sell popular board games at low prices.",
             ]},
            {"t": "q", "qlabel": "2", "no": 19,
             "stem": "Which is true about the Family Game Festa?",
             "choices": [
                 "Helpers at 'Game Time' will receive a small present.",
                 "It is held at the community centre every year.",
                 "The games will be displayed only on the final day.",
                 "Visitors must pay to join 'Game Time'.",
             ]},
            {"t": "q", "qlabel": "3", "no": 20,
             "stem": "According to your online form, which combination of the following statements is "
                     "true? {Q}<br><br>"
                     "A: All of the games were made after 2000.<br>"
                     "B: All of the games cost less than £25.<br>"
                     "C: Animals appear in all of the games.<br>"
                     "D: The box pictures of all the games were drawn by their designers.",
             "choices": ["A and B", "A and C", "A and D", "B and C", "B and D", "C and D"],
             "cols": 3},
            {"t": "q", "qlabel": "4", "no": 21,
             "stem": "Which of the four games will probably <u>not</u> be displayed at the Family Game "
                     "Festa?",
             "choices": ["Castle of Riddles", "Good Night, Little Bear", "Sunny Farm", "The Sleepy Lion"],
             "cols": 2},
            {"t": "q", "qlabel": "5", "no": 22, "multi": True,
             "stem": "According to the email, what two things are you asked to do? "
                     "{Q}・<span class=\"qslot\">23</span>　(The order does not matter.)",
             "choices": [
                 "Buy a new board game for the Festa.",
                 "Help children play games at 'Game Time'.",
                 "Send the rules of your games by post.",
                 "Suggest one more game for the Festa.",
                 "Translate your game comments into other languages.",
                 "Visit the community centre to correct your form.",
             ]},
        ]}],
    },
]

# ==================== ANS_SECTIONS ====================

ANS_SECTIONS = [
    {
        "section": 4, "points": 12,
        "answers": [
            {"qno": 14, "answer": "③", "points": 3},
            {"qno": 15, "answer": "④", "points": 3},
            {"qno": 16, "answer": "①", "points": 3},
            {"qno": 17, "answer": "②", "points": 3},
        ],
        "kai": [
            {"heading": "問1 (解答番号14)", "blocks": [
                {"t": "p", "text": "正解③。コメント(1)は「なぜこのコンテストを開くのか。目的をここに書き足して」という指示。"
                                   "第1段落に「朝食を抜く生徒が半数以上」という調査結果と「みんながより良い習慣を作る手助けをするために"
                                   "Health Weekを開く」という趣旨が示されており、レシピコンテストの目的として文脈に合うのは"
                                   "③「生徒に毎日の食習慣について考えてもらうため」。①「食堂の新メニューの宣伝」と④「調理器具の資金集め」"
                                   "は本文に記述がない(cafeteriaは投票場所として出てくるだけ)。②「学校一の若手シェフを探すため」は"
                                   "「コンテスト」という語の連想を利用した引っかけで、健康習慣というニュースレター全体の趣旨と無関係。"},
            ]},
            {"heading": "問2 (解答番号15)", "blocks": [
                {"t": "p", "text": "正解④。挿入文は「スタンプ10個を最も短い時間で集めたチームが優勝」という勝敗の決め方"
                                   "(=コメント(2)が要求する情報)。この段落は「チーム作り→当日集合して地図とスタンプカードを受け取る→"
                                   "チェックポイントを回ってスタンプを集める→結果発表」という時系列。<A>・<B>の位置では"
                                   "スタンプカードも「10か所のチェックポイント」もまだ登場していない。<C>ではスタンプを集める"
                                   "説明より前に勝敗基準が来てしまい不自然。スタンプ集めの説明の直後・結果発表の直前である"
                                   "<D>に置くと流れが通る。"},
            ]},
            {"heading": "問3 (解答番号16)", "blocks": [
                {"t": "p", "text": "正解①。この段落の話題は「健康的なおやつ作り教室」の紹介。下線部(3)「家で料理するとお金がかなり"
                                   "節約できる」はお金の話で、健康を勧めるという段落・ニュースレター全体の主旨に合わない(コメント(3)の指摘)。"
                                   "①「甘いお菓子の代わりに健康的なおやつを食べるのは毎日の食習慣を良くする簡単な方法」なら教室の意義の"
                                   "説明として段落に溶け込む。②は市場の野菜の値段の話で、削除すべき文と同じ「お金」話題の引っかけ。"
                                   "③は包丁の練習の話で行事の宣伝文として不適。④はコンビニの甘いおやつの流行の話で、主旨と逆方向。"},
            ]},
            {"heading": "問4 (解答番号17)", "blocks": [
                {"t": "p", "text": "正解②。ニュースレター全体の主張は「Health Weekをきっかけに、睡眠・食事・運動といった毎日の習慣を"
                                   "見直そう」(第1段落と最終段落の呼びかけ)。②「毎日の習慣を見直して改善する」がこれを過不足なく要約する。"
                                   "①「バランスの良い食事の作り方を学ぶ」は料理関連のイベントだけを指し狭すぎる。④「他校の生徒と町を歩く」"
                                   "はウォーキングラリーだけで狭すぎる。③「地域のあらゆる健康問題を解決する」は学校行事の告知の主張として"
                                   "広すぎる。「広すぎ/狭すぎ」を切って全体をちょうど要約する句を選ぶのがポイント。"},
            ]},
        ],
    },
    {
        "section": 5, "points": 16,
        "answers": [
            {"qno": 18, "answer": "③", "points": 3},
            {"qno": 19, "answer": "①", "points": 3},
            {"qno": 20, "answer": "④", "points": 3},
            {"qno": 21, "answer": "①", "points": 3},
            {"qno": 22, "answer": "②・④", "points": 2},
            {"qno": 23, "answer": "②・④", "points": 2},
        ],
        "kai": [
            {"heading": "問1 (解答番号18)", "blocks": [
                {"t": "p", "text": "正解③。リーフレット第1段落に「町の幼い子どもたちにボードゲームがどれほど楽しいかを発見してもらう"
                                   "ために(so that young children ... can discover how much fun board games are)開催する」と目的が"
                                   "明示されており、③はその言い換え。①「外国の子どものために古いゲームを集める」・④「人気ゲームを安く売る」"
                                   "は本文にない。②「センターの新しい常勤職員を探す」はボランティア募集の記述を利用した引っかけだが、"
                                   "募集はFesta当日の手伝いであって、Festa開催の目的でも職員採用でもない。"},
            ]},
            {"heading": "問2 (解答番号19)", "blocks": [
                {"t": "p", "text": "正解①。リーフレットに「ボランティアにはお礼としてホールのカフェの無料ドリンク券を進呈"
                                   "(a free drink ticket ... as a small thank-you)」とあり、①「'Game Time'の手伝いをする人は"
                                   "ちょっとした贈り物を受け取る」はその言い換え(drink ticket→present)。②「毎年開催」は"
                                   "「第1回(The first Family Game Festa)」と矛盾。③「展示は最終日だけ」は「1週間ずっとエントランス"
                                   "ホールで展示」の逆。④「'Game Time'への参加は有料」は「参加は無料(joining is free)」の逆。"},
            ]},
            {"heading": "問3 (解答番号20)", "blocks": [
                {"t": "p", "text": "正解④。A〜Dをフォームの4作品すべてで検証する(全数チェック)。A「全ゲームが2000年より後に作られた」"
                                   "→ The Sleepy Lionは1988年なので偽。B「全ゲームが£25未満」→ £12・£24・£18・£9で真。"
                                   "C「全ゲームに動物が登場」→ 農場の動物/ライオンとねずみ/きつね/くまの家族で真。"
                                   "D「箱の絵は全てデザイナー本人が描いた」→ Castle of Riddlesだけ箱絵がLeo Rossi"
                                   "(デザイナーはSofia Rossi)なので偽。①〜⑥の6通りの組合せのうち両方が真になるのは"
                                   "④「B and C」だけ。"},
            ]},
            {"heading": "問4 (解答番号21)", "blocks": [
                {"t": "p", "text": "正解①。リーフレット×フォーム×メールの3素材統合問題。リーフレットの募集条件は「未就学の子ども"
                                   "(preschool children)が楽しめるゲーム」。フォームのCastle of Riddlesのコメントには「なぞなぞに"
                                   "読む力が必要なので10歳より上の子ども向き(better for children over ten)」とあり、条件に合わない。"
                                   "メールにも「1つは対象年齢に合わなかったが、他の3つは受理(添付の受理リスト参照)」とある。"
                                   "よって展示されないのは①。他の3作品はコメントで「3〜6歳向け」「3歳児でも楽しめる」「3〜5歳向け」と"
                                   "明記され、条件を満たす。"},
            ]},
            {"heading": "問5 (解答番号22・23)", "blocks": [
                {"t": "p", "text": "正解②・④(順不同・各2点)。メール内の依頼は2つ。(a)「もう1つゲームを推薦してもらえたらうれしい。"
                                   "16 Januaryまでにメールを」→ ④「Festaのためにもう1つゲームを提案する」。(b)「最終日の'Game Time'の"
                                   "手伝いがまだ足りない。もう一度考えてもらえないか」→ ②「'Game Time'で子どもたちがゲームで遊ぶのを"
                                   "手伝う」。①ゲームの購入、③ルールの郵送、⑥フォーム修正のための来館はメールに書かれていない。"
                                   "⑤「コメントを他言語に翻訳する」は、センターのスタッフが行うと書かれており、あなたへの依頼ではない。"},
            ]},
        ],
    },
]
