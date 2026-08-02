#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト模試 2026 (英語リーディング) の seed JSON 生成器。

対象プール (EXAM_QUESTION_ROTATION と一致必須):
  ("daigaku", "r_short", "kyotsu")  … MOCK_EXAM_TEMPLATES["kyotsu"] 第1セクション「短文読解」
  ("daigaku", "r_long",  "kyotsu")  … 同 第2セクション「長文読解」

大問構成 (共通テスト リーディングの大問形式に対応):
  r_short : 第1問A(メッセージ) / 第1問B(告知) / 第2問A(比較+レビュー) / 第2問B(記事・事実と意見)
  r_long  : 第3問B(体験ブログ・時系列) / 第4問(複数資料の統合) / 第5問(伝記+ノート)
            / 第6問A(論説) / 第6問B(説明文)

【解説フォーマット (server/main.py の英語系生成プロンプト準拠・絶対遵守)】
  「explanation は Markdown で以下4セクションを必ず明示。1セクションでも欠けたら不合格」

      ## 🎯 コアイメージ    … 語法・文法・時制・前置詞のコアイメージ
      ## 🔬 文構造分析      … S/V/O/C/M をラベル付きで明示 (絶対省略禁止)
      ## 📍 本文の根拠      … 該当箇所の引用 + 段落
      ## ❌ 誤答 NG 理由    … 各誤答が構造的・本質的に NG な理由

  加えて、同一プール (daigaku/r_short・r_long/kyotsu) の既存 seed
  dojo_eng_kyotsu2026_manual.json (140問) の慣行に合わせ、冒頭に
  「正解は「<正答の選択肢テキスト>」。」の 1 行を置く。
  これは scripts/eng_kyotsu_2026/validate_and_build.py の検査にも通り、
  解説と選択肢の食い違いを機械検出できる。

  ★ 解説本体は kaisetsu_eng.py に (大問, 小問index) をキーとして分離。
    build 時に 4 セクションの存在と、誤答理由が誤答 3 件と 1 対 1 対応することを検査する。

検証 (scripts/eng_kyotsu_2026/validate_and_build.py と同じ品質ゲート):
  - 行スキーマ / 小問スキーマ / 選択肢 4 個 / answer が範囲内
  - explanation が「正解は「<正答の選択肢テキスト>」。」で始まり、正答と完全一致
  - 選択肢の重複なし
  - HTML エンティティの残存なし
  - 図・グラフ依存表現 (the figure above 等) の混入なし … 本文は文字だけで自己完結させる
  - 大問本文の content hash 重複なし
  - 正解位置を md5 順の round-robin で 0..3 に完全均等配分

出力: seed-data/kyotsu_mogi2026_eng_manual.json
実行: python3 scripts/kyotsu_mogi2026/build_eng.py
"""
import json
import re
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kaisetsu_eng import K as KAISETSU   # noqa: E402  解説本体 (4セクション)

OUT = os.path.join(os.path.dirname(__file__), '..', '..',
                   'seed-data', 'kyotsu_mogi2026_eng_manual.json')
SOURCE = 'kyotsu-mogi2026-20260802'
MODEL = 'claude-kyotsu-mogi2026-verified'

ENTITY_RE = re.compile(r'&(lt|gt|amp|quot|#\d+);')
FIGURE_HINTS = ['the graph above', 'the graph below', 'the picture', 'the figure', 'the diagram',
                'as shown in the image', 'see the chart', '下のグラフ', '右の図', '左の図', '上の図']

DAIMON = []


def D(part_key, group, passage, subqs):
    DAIMON.append({"part_key": part_key, "group": group, "passage": passage, "subqs": subqs})


SECTIONS = ("## 🎯 コアイメージ", "## 🔬 文構造分析", "## 📍 本文の根拠", "## ❌ 誤答 NG 理由")


def Q(stem, unit, correct, distractors):
    """小問 1 つ。解説本体は kaisetsu_eng.py 側に (大問, index) をキーとして持たせる。"""
    return dict(stem=stem, unit=unit, correct=correct, distractors=distractors)


def build_explanation(group, qi, correct, distractors):
    """4 セクションの解説を組み立てる。欠けていれば (None, 理由) を返す。"""
    k = KAISETSU.get((group, qi))
    if not k:
        return None, f'kaisetsu_eng.py に ("{group}", {qi}) の解説が無い'
    for f in ("core", "kouzou", "konkyo", "ng"):
        if not k.get(f):
            return None, f'解説の {f} が空'
    if len(k["ng"]) != len(distractors):
        return None, f'誤答 NG 理由が {len(k["ng"])} 件 (誤答は {len(distractors)} 件)'
    ng_lines = "\n".join(f'- 「{d}」… {why}' for d, why in zip(distractors, k["ng"]))
    return (f'正解は「{correct}」。\n\n'
            f'{SECTIONS[0]}\n{k["core"]}\n\n'
            f'{SECTIONS[1]}\n{k["kouzou"]}\n\n'
            f'{SECTIONS[2]}\n{k["konkyo"]}\n\n'
            f'{SECTIONS[3]}\n{ng_lines}'), None


# =====================================================================
# r_short — 第1問・第2問 相当
# =====================================================================

D("r_short", "第1問A メッセージ読解",
  """You are a member of your school's international exchange club. You received the following message from Emma, an exchange student who will arrive next month.

Hi!

Thanks for offering to help me during my stay. I arrive in Osaka on 5 September, and my host family will meet me at the airport, so you don't need to come — but I'd love to see you at school on Monday the 8th.

Two things I want to ask about. First, my host mother says the school has a "cleaning time" every day. Is that right? In my country only the cleaning staff do that, so I'd like to know what I'm supposed to bring. Second, I've been learning Japanese for two years, but almost all of it has been reading. I can write hiragana slowly and I know maybe 200 kanji, so please speak slowly at first — I promise I'll catch up.

I've also signed up for the calligraphy club, because my grandmother collects Japanese brushes and I want to send her something I made myself. Someone told me the club meets on Thursdays after school, but the school website says Wednesdays. Could you check which one is correct before I arrive?

See you soon!
Emma""",
  [
    Q("What does Emma ask you to do before she arrives?",
      "詳細理解",
      "Find out which day the calligraphy club meets.",
      ["Meet her at the airport on 5 September.",
       "Teach her 200 more kanji.",
       "Introduce her to her host family."]),
    Q("What is true about Emma's Japanese?",
      "詳細理解",
      "She has more experience reading it than writing it.",
      ["She has never studied it before.",
       "She can write kanji quickly but cannot read them.",
       "She learned it from her grandmother."]),
    Q("Why did Emma join the calligraphy club?",
      "推論",
      "She wants to make a present for a member of her family.",
      ["Her host mother recommended it to her.",
       "It is the only club that meets after school.",
       "She has already practised calligraphy for two years."]),
  ])


D("r_short", "第1問B 告知の読み取り",
  """You are a first-year student at Minami High School. The school library has posted the following notice on its website.

===========================================
   SUMMER READING CHALLENGE 2026
   Minami High School Library
===========================================

Read, record, and win! The library is running its annual reading challenge from 21 July to 25 August.

HOW IT WORKS
 1. Pick up a Reading Card at the library counter, or download one from the library page.
 2. Each time you finish a book, write the title and one comment of 30 words or more on the card.
 3. Bring the completed card to the counter by 28 August.

LEVELS
 Bronze ( 3 books)  a bookmark designed by the art club
 Silver ( 6 books)  a bookmark and a free drink ticket for the school cafe
 Gold  (10 books)  both of the above, and your review printed in the September library newsletter

RULES
 * Manga and picture books do not count, but graphic novels of more than 100 pages do.
 * Books borrowed from the city library may be included; they do not have to be ours.
 * Comments may be written in English or Japanese, but each comment written in English earns
   you one extra book credit, up to a maximum of three extra credits.

BORROWING DURING THE SUMMER
 The library is open Monday to Friday, 9:00-16:00. It is closed at weekends and from 11 to 15 August.
 You may borrow five books at a time during the summer, instead of the usual two.

Questions? Email the library staff.""",
  [
    Q("What must you do to receive a prize?",
      "詳細理解",
      "Hand in a card with a written comment for each finished book by 28 August.",
      ["Email a list of the books you have read to the library staff.",
       "Borrow every book you read from the school library.",
       "Write all of your comments in English."]),
    Q("A student finishes six books and writes all six comments in English. What will that student receive?",
      "情報統合",
      "A bookmark and a free drink ticket.",
      ["A bookmark only.",
       "A bookmark, a drink ticket, and a printed review.",
       "Three bookmarks and a drink ticket."]),
    Q("Which of the following books can be counted for the challenge?",
      "詳細理解",
      "A 150-page graphic novel borrowed from the city library.",
      ["A manga series borrowed from a friend.",
       "A picture book read to a younger brother.",
       "A 200-page novel that you have not finished."]),
    Q("What is different about the library during the summer?",
      "事実把握",
      "Students may borrow more books at one time than they usually can.",
      ["The library opens on Saturday mornings.",
       "The library is open every day from 21 July to 25 August.",
       "Borrowed books may be kept until the end of September."]),
  ])


D("r_short", "第2問A 比較とレビュー",
  """Your class is choosing a vocabulary app for English homework. Your teacher has given you the following page from a school magazine.

WHICH VOCABULARY APP IS RIGHT FOR YOU?
Three apps compared by our student reporters

--------------------------------------------------------------
                      WordStep      QuizLeaf      MemoRise
--------------------------------------------------------------
 Monthly cost         Free          500 yen       300 yen
 Words in database    3,000         12,000        8,000
 Works offline        Yes           No            Yes
 Speaking practice    No            Yes           Yes
 Daily reminder       Yes           Yes           No
 Progress report      Weekly        Daily         Monthly
--------------------------------------------------------------

REVIEWS

Kenta (2nd year): I used WordStep every day on the train, where my phone often loses its signal, and that never caused a problem. The word list is short, though, so I finished it in two months and had nothing left to study. If price is the only thing you care about, start here.

Aya (3rd year): QuizLeaf's speaking check is strict — it told me my "th" sound was wrong about fifty times — but my score on the pronunciation test went up by twelve points. The daily report is useful, yet I cannot open the app on the school bus, because there is no Wi-Fi there. For me, the result was worth the cost.""",
  [
    Q("Which app allows a student with no internet connection to practise speaking?",
      "情報統合",
      "MemoRise",
      ["WordStep", "QuizLeaf", "None of the three apps"]),
    Q("What problem did Kenta have with WordStep?",
      "詳細理解",
      "He ran out of new words to study.",
      ["The app stopped working when he lost his signal.",
       "He had to pay more than he had expected.",
       "The daily reminder came too often."]),
    Q("Which statement about QuizLeaf is an opinion rather than a fact?",
      "事実と意見の区別",
      "The results the app produces are worth what it costs.",
      ["The app cannot be used without an internet connection.",
       "The app checks how the user pronounces words.",
       "The app sends the user a report every day."]),
    Q("A student wants an app that costs nothing and reminds them to study every day. Which app fits?",
      "情報統合",
      "WordStep",
      ["QuizLeaf", "MemoRise", "Either QuizLeaf or MemoRise"]),
    Q("According to the reviews, what happened to Aya after she used QuizLeaf?",
      "詳細理解",
      "Her score on a pronunciation test improved.",
      ["She stopped taking the school bus.",
       "She was able to study offline for the first time.",
       "She learned all 12,000 words in the database."]),
  ])


D("r_short", "第2問B 記事(事実と意見)",
  """You are writing a report about school schedules. You have found the following article in a school newspaper written by a student committee.

SHOULD OUR SCHOOL DAY START LATER?
by the Student Life Committee, Kita High School

Last month our committee asked all 612 students at this school about the daily schedule, and 478 students answered. Of those, 61% said that they usually sleep fewer than six hours on school nights, and 74% said that they feel sleepy during first period.

Our school day begins at 8:20, which is fifteen minutes earlier than the average starting time for public high schools in this city. Students who travel by train from the west side of the city have to leave home before 7:00.

We think that a later start would help. A study carried out at a high school in another prefecture found that when the first class was moved from 8:15 to 8:45, the number of students arriving late fell by 40% over one term. The same report noted that average test scores in the first-period subject rose slightly, though the researchers themselves said that the change was too small to be certain about.

Of course, a later start means a later finish. Club activities would lose about thirty minutes of practice time on weekdays, and several teachers have told us that this is the most serious problem with the idea. Our committee believes that shorter but better-organised practice would be no less effective, and that arriving at school awake matters more than half an hour on the field.

We will present these results to the school council in October.""",
  [
    Q("What did the committee's survey find?",
      "詳細理解",
      "About three-quarters of the students who replied feel sleepy in the first class.",
      ["All 612 students at the school answered the survey.",
       "Most students want the school day to begin at 8:45.",
       "Students from the west side of the city arrive late most often."]),
    Q("Which of the following is a fact stated in the article?",
      "事実と意見の区別",
      "The school day at Kita High School starts fifteen minutes earlier than the city average.",
      ["A later start would help the students at this school.",
       "Shorter practice can be just as effective as longer practice.",
       "Coming to school awake matters more than extra practice time."]),
    Q("Which of the following is an opinion stated in the article?",
      "事実と意見の区別",
      "Practice that is shorter but better organised would be just as effective.",
      ["478 of the 612 students answered the survey.",
       "At a school in another prefecture, late arrivals fell by 40% in one term.",
       "Students from the west side of the city have to leave home before 7:00."]),
    Q("What does the article say about the study from another prefecture?",
      "詳細理解",
      "Its finding about test scores was not strong enough to be sure of.",
      ["It showed that test scores fell after the change.",
       "It was carried out over a period of three years.",
       "It found no change in the number of students arriving late."]),
    Q("What will the committee do next?",
      "要点把握",
      "Report the results of the survey to the school council.",
      ["Ask the teachers to shorten club activities.",
       "Change the starting time to 8:45 in October.",
       "Carry out a second survey of all 612 students."]),
  ])


# =====================================================================
# r_long — 第3問B・第4問・第5問・第6問 相当
# =====================================================================

D("r_long", "第3問B 体験ブログ(時系列)",
  """You are reading a blog written by a Japanese high school student who took part in an international science camp.

MY WEEK AT THE PACIFIC SCIENCE CAMP
Posted by Sora | 12 August

When my teacher handed me the application form in April, I almost gave it straight back. The camp was to be held entirely in English, and I had never spoken English outside a classroom. My teacher only said, "Write the essay first, then decide." So I wrote it, and three weeks later an email told me that I had been chosen as one of forty students from eleven countries.

I spent May and June in a quiet panic. I made a list of two hundred science words and tested myself on it every morning on the bus. Looking back, that list was the least useful thing I did, because nobody at the camp talked like a textbook.

Day 1. We were put into teams of five and told that by Friday each team had to present a solution to a local problem. My team had a student from Chile, one from Kenya, one from Thailand and one from Australia. For the first hour I said almost nothing. Ana, from Chile, noticed and asked me a question directly. I answered in five words. She waited, and then said, "Okay, so you mean ..." and repeated my idea as a full sentence. Nobody laughed.

Day 2. Our problem was the plastic waste washing up on the beach two kilometres from the camp. We spent the morning collecting and sorting rubbish. Kwame, from Kenya, kept asking "why" about everything: why did most of the bottles have foreign labels, why were the pieces smaller near the river mouth. By lunchtime we had thrown out our first idea completely.

Day 3. This was the day I stopped translating. I was explaining how a filter my grandfather uses for rice-field water might be adapted, and halfway through I realised that I had not thought in Japanese for several minutes. My grammar was poor. It did not seem to matter.

Day 4. We built a model, and it failed twice. Ana wanted to redesign it; Kwame wanted to test the same model again first. They argued for twenty minutes. In the end we did both, and I was the one who suggested it — my first complete idea in English.

Day 5. We presented. We did not win; a team from Thailand did, with a much simpler idea. But the judge who spoke to us afterwards said that our team had changed its mind more often than any other team, and that he meant this as a compliment.

I came home with the two-hundred-word list still in my bag, mostly unused. What I actually brought back is smaller and harder to explain: I now know what it feels like to be understood by someone who is not simply being polite.""",
  [
    Q("What did Sora do first, immediately after receiving the application form?",
      "時系列把握",
      "Wrote the essay that the application required.",
      ["Made a list of two hundred science words.",
       "Returned the form to the teacher without applying.",
       "Sent an email to the camp organisers."]),
    Q("Which of these happened last?",
      "時系列把握",
      "Sora made a suggestion that the whole team accepted.",
      ["Sora's team gave up their first idea.",
       "Sora realised that he had stopped translating in his head.",
       "Sora learned that he had been chosen for the camp."]),
    Q("Why does Sora call the word list \"the least useful thing\" he did?",
      "推論",
      "The English actually used at the camp was not like the English in a textbook.",
      ["He lost the list on the first day of the camp.",
       "The camp turned out to be held in Japanese.",
       "The other students had already learned all the words on it."]),
    Q("What did the judge praise Sora's team for?",
      "詳細理解",
      "Being willing to change their ideas.",
      ["Presenting the simplest solution of all the teams.",
       "Building a model that worked at the first attempt.",
       "Speaking the most fluent English."]),
    Q("What does Sora suggest that he gained from the camp?",
      "要点把握",
      "A sense of what it is like to communicate real meaning in English.",
      ["A large vocabulary of scientific terms.",
       "A prize for the best presentation at the camp.",
       "A decision to study science at university."]),
  ])


D("r_long", "第4問 複数資料の統合",
  """Your class is preparing a presentation about how students travel to school. You have found two short reports.

REPORT A (from a city education office newsletter)

In June we surveyed 1,200 high school students in Higashi City about how they travel to school. The results are shown below. We also asked students to rate their journey from 1 (very unpleasant) to 5 (very pleasant).

   Method     Students    Average time    Average rating
   Train         468         42 min            2.9
   Bicycle       372         24 min            3.8
   Bus           204         35 min            2.6
   Walking       156         18 min            4.1

Students who cycle or walk gave clearly higher ratings than those who use public transport. The groups differ in one other way, however: almost all of the students who walk live within 1.5 km of their school.

REPORT B (from the student newspaper of Higashi North High School)

We repeated the city survey at our own school, where 84% of students come by train. Our average rating for the train journey was 2.2 — much lower than the city figure of 2.9. When we asked why, the most common answer was not the length of the journey but the crowding: 71% of train users said that they could not sit down, and 55% said that they could not read or study on board.

One result surprised us. Students who had to change trains once rated their journey higher (2.6) than students who took a single direct train (2.1). In interviews, several students explained that the change gave them a short break and a chance to get a seat on the second train.""",
  [
    Q("According to Report A, which group spends the least time travelling to school?",
      "詳細理解",
      "Students who walk.",
      ["Students who cycle.",
       "Students who take the bus.",
       "Students who take the train."]),
    Q("According to Report A, how many of the students surveyed use public transport?",
      "情報統合",
      "672",
      ["468", "528", "1,200"]),
    Q("What does Report A suggest about the high ratings given by students who walk?",
      "推論",
      "They may be partly explained by the short distances those students live from school.",
      ["They show that walking is more comfortable than cycling in every case.",
       "They are based on a much larger sample than the other groups.",
       "They were collected in a different month from the rest of the data."]),
    Q("According to Report B, what do train users at Higashi North High School dislike most?",
      "要点把握",
      "The trains are too crowded.",
      ["The journey takes too long.",
       "The trains are often late.",
       "The fares are too expensive."]),
    Q("Which conclusion is supported by both reports?",
      "情報統合",
      "A shorter journey is not always rated as a better one.",
      ["The students who travel longest are always the least satisfied.",
       "Users of public transport are more satisfied than cyclists.",
       "The city survey and the school survey produced the same results."]),
  ])


D("r_long", "第5問 伝記とノート作成",
  """You are preparing a presentation for your English class about a person introduced in a magazine article. Read the article and organise the information.

THE WOMAN WHO DREW WHAT NOBODY COULD SEE

Ines Bertrand was born in 1901 in a small town in the south of France, the fourth of six children. Her father repaired clocks. There was no money for the art school she wanted to attend, so at sixteen she took a job painting numbers onto clock faces in her father's workshop — work that demanded a steady hand and a very fine brush.

In 1922 a visiting university lecturer, Dr Hugo Meyer, brought a broken microscope to the workshop. While he waited, he noticed the drawings Ines had made in the margins of the workshop's order book: leaves, insect wings, the inside of a flower. He asked whether she had ever drawn what she saw through a lens. She had never looked through one.

Meyer invited her to his laboratory in Lyon. Photography of microscopic samples was still poor at that time; a photograph flattened everything into grey, and important details disappeared. A trained illustrator could do what a camera could not — decide which parts mattered and show them clearly. Ines was employed as a technical assistant in 1923.

Over the next eleven years she produced more than four thousand illustrations for research papers. She never signed them. Scientific illustrations were then regarded as part of the equipment, like a test tube, and the illustrator's name did not appear. Colleagues later recalled that she would sometimes spend a whole day at the microscope before making a single mark on paper, insisting that she could not draw a structure until she understood what it did.

In 1934 she was refused permission to attend a conference in Berlin at which twelve of her illustrations were displayed, because assistants were not invited. She resigned two weeks later.

What followed was unexpected. She opened a small studio and began teaching illustration to science students — first four of them, then thirty. Her argument was simple and, at the time, unusual: a scientist who could draw a specimen would observe it more carefully than one who could only photograph it. Two of her students went on to lead university departments, and both taught drawing to their own students.

Ines Bertrand died in 1988. In 1994 a researcher who was matching handwriting in laboratory notebooks identified 3,800 of her unsigned drawings. A collection of them was published in 2001, one hundred years after her birth, under a title she never chose: Seeing First.""",
  [
    Q("What did Ines Bertrand's first paid work require her to do?",
      "詳細理解",
      "Use a very fine brush with great precision.",
      ["Repair broken microscopes for customers.",
       "Teach drawing to younger students.",
       "Photograph samples for a laboratory."]),
    Q("Why were drawings preferred to photographs in Meyer's laboratory?",
      "詳細理解",
      "An illustrator could choose which details to show clearly.",
      ["Photography was more expensive than illustration.",
       "Cameras could not be attached to a microscope at all.",
       "Researchers were unable to understand photographs."]),
    Q("Why did her name not appear on her illustrations?",
      "推論",
      "The work of an illustrator was treated as technical support rather than authorship.",
      ["She had asked for her name to be removed from them.",
       "Each drawing was made by several people working together.",
       "Her employer published them under his own name by mistake."]),
    Q("Which of the following shows the correct order of events in her life?",
      "時系列把握",
      "She drew through a microscope → she resigned → she began teaching → her work was published.",
      ["She began teaching → she drew through a microscope → she resigned → her work was published.",
       "She resigned → she drew through a microscope → she began teaching → her work was published.",
       "She drew through a microscope → she resigned → her work was published → she began teaching."]),
    Q("What was her main argument as a teacher?",
      "要点把握",
      "Drawing a specimen makes a scientist observe it more carefully.",
      ["Every scientific paper should contain a signed illustration.",
       "Photography should be removed from scientific training.",
       "Illustrators should be paid as much as researchers."]),
  ])


D("r_long", "第6問A 論説文の要旨",
  """You are in a discussion group that is reading about cities and the environment. Read the following article.

MORE TREES IS NOT ALWAYS THE ANSWER

[1] For the past two decades, planting trees has been the most popular answer to almost every urban environmental problem. Cities have announced plans to plant a million trees, and then two million. The appeal is obvious: trees are cheap, they are visible, and nobody objects to them. But researchers who study urban heat have begun to argue that the number of trees a city plants matters far less than where it plants them, and that some planting programmes have produced almost no measurable benefit.

[2] The main way trees cool a city is not by absorbing carbon dioxide, which happens far too slowly to affect summer temperatures, but by providing shade and by releasing water vapour from their leaves. Both effects are strongly local. A tree cools the ground beneath it and the air within a few metres of it; a hundred metres away the difference may be too small to measure. A thousand trees planted in a park on the edge of a city therefore do very little for the crowded central district where the temperature is highest.

[3] Those hot central districts are also, in most cities that have been studied, the districts where the fewest trees already grow, and where residents have the least influence over planning decisions. A survey of thirty-seven cities found that districts with lower average incomes had, on average, 24% less tree cover than wealthier districts in the same city. When a city counts only the total number of trees planted, a programme can look like a complete success while leaving that gap exactly where it was.

[4] There is a further complication. Trees need water, and in dry regions a young tree may require regular watering for its first three to five years. Several cities have found that a large share of the trees they planted did not survive long enough to provide any shade at all. One review of North American programmes estimated that between 15% and 30% of newly planted street trees die within five years, and that survival depends far more on maintenance budgets than on which species is chosen.

[5] None of this is an argument against planting trees. It is an argument against counting them. A programme that plants two hundred trees along a treeless street in a hot district, waters them for five years and replaces those that die will do more for the people who live there than a programme that plants twenty thousand seedlings and then walks away. The second programme, however, produces a much better headline.

[6] The question a city should ask is not "how many trees have we planted?" but "how many people are now standing in shade at two o'clock in the afternoon?" That number is harder to collect and much harder to celebrate. It is also the only one that measures what the trees were planted for.""",
  [
    Q("What is the main point of paragraph [2]?",
      "要点把握",
      "The cooling effect of a tree reaches only a short distance from it.",
      ["Trees absorb carbon dioxide faster than researchers expected.",
       "A park on the edge of a city cools the whole city evenly.",
       "Water vapour released by leaves raises the air temperature."]),
    Q("According to paragraph [3], what can a tree-planting programme hide?",
      "詳細理解",
      "The unequal distribution of trees between richer and poorer districts.",
      ["The high cost of buying young trees.",
       "The difficulty of finding space in which to plant.",
       "The slow growth rate of native species."]),
    Q("According to paragraph [4], what most affects whether a newly planted street tree survives?",
      "詳細理解",
      "How much money is available to look after it.",
      ["Which species of tree is chosen.",
       "How old the tree is when it is planted.",
       "How many trees are planted at the same time."]),
    Q("What does the author mean by \"It is an argument against counting them\" in paragraph [5]?",
      "推論",
      "Programmes should be judged by their effects rather than by their totals.",
      ["Cities should stop keeping any records of the trees they plant.",
       "Cities should plant fewer trees than they do at present.",
       "Cities should not report the results of their programmes to the public."]),
    Q("Which title best expresses the author's argument?",
      "要点把握",
      "Where a city plants matters more than how many trees it plants",
      ["Why cities should stop planting trees in hot districts",
       "The evidence that trees do not cool cities at all",
       "How planting a million trees solved one city's heat problem"]),
  ])


D("r_long", "第6問B 説明文の整理",
  """You are making a poster for a school project on food waste. Read the following article and organise the information.

WHERE FOOD IS LOST

[1] Roughly a third of the food produced for people to eat is never eaten. That figure is quoted so often that it has stopped meaning very much. It hides the more useful question: at which point does the food disappear, and does the answer differ from country to country?

[2] It does, and sharply. In lower-income countries most losses happen early, between the field and the market. Crops are damaged by insects during storage, or spoil in transport because there is no refrigeration, or simply cannot reach a buyer before they rot. Very little is thrown away by households, because food is expensive relative to income and people are careful with it.

[3] In higher-income countries the pattern is reversed. Storage and transport are efficient, and losses before the shop are comparatively small. The waste happens at the end of the chain: in supermarkets, in restaurants and, above all, in homes. In several European studies, households were responsible for between 45% and 55% of all the food wasted in the country — more than farms, factories, shops and restaurants combined.

[4] Household waste is also the hardest kind to reduce, because it is not one behaviour but many. A shopper buys three peppers because they are sold in a pack of three, uses one, and finds the others soft a week later. A family cooks for four when three are eating. A label reading "best before" is understood as if it read "use by", and a perfectly good yoghurt goes into the bin. Each of these has a different solution, and none of those solutions is a poster telling people not to waste food.

[5] This is why the measures that work best tend to be structural rather than educational. When one supermarket chain removed date labels from fresh fruit and vegetables — items for which the label adds no safety information — waste of those items in customers' homes fell measurably. When another chain allowed customers to buy single items instead of fixed packs, sales of the affected products fell slightly while waste fell a great deal more.

[6] Educational campaigns are not useless, but their effects fade. Studies of household campaigns generally show a reduction while the campaign is running and a return to earlier levels within a year of its end. Changes to the way food is sold, by contrast, keep working whether or not anyone is paying attention.

[7] For a country deciding where to act, then, the first step is not a slogan. It is to find out where in its own food chain the food is actually being lost — and to accept that the answer for one country is not the answer for another.""",
  [
    Q("Why does the author say that the figure \"a third of all food\" has \"stopped meaning very much\"?",
      "要点把握",
      "It does not show at which stage of the food chain the loss happens.",
      ["It is based on research that is now out of date.",
       "It is too small a share to be a serious problem.",
       "It applies only to lower-income countries."]),
    Q("According to paragraph [2], why do households in lower-income countries waste little food?",
      "詳細理解",
      "Food takes up a large share of their income, so they use it carefully.",
      ["They have better refrigeration than richer countries.",
       "They buy most of their food already cooked.",
       "Their governments fine households that waste food."]),
    Q("What do the European studies mentioned in paragraph [3] show?",
      "詳細理解",
      "Homes account for more waste than all the other stages put together.",
      ["Restaurants waste more food than homes do.",
       "Losses during transport are the largest single category.",
       "Supermarkets waste about half of the food they receive."]),
    Q("Why does the author call household waste \"the hardest kind to reduce\"?",
      "推論",
      "It comes from many different habits, each needing a different solution.",
      ["Households refuse to take part in surveys about it.",
       "The amount wasted in homes cannot be measured at all.",
       "It occurs only in the wealthiest countries."]),
    Q("What does the article conclude about educational campaigns?",
      "詳細理解",
      "Their effect tends to disappear after the campaign ends.",
      ["They are more effective than changing the way food is sold.",
       "They have no effect on household behaviour at all.",
       "They work best in lower-income countries."]),
  ])


# =====================================================================
# 検証 → JSON 組み立て
# =====================================================================

def _answer_positions():
    """全小問の正解位置を md5 順の round-robin で 0..3 に完全均等配分する。"""
    keys = [(dm["group"], qi) for dm in DAIMON for qi in range(len(dm["subqs"]))]
    ranked = sorted(keys, key=lambda kk: hashlib.md5(f'{SOURCE}:{kk[0]}:{kk[1]}'.encode()).hexdigest())
    return {kk: i % 4 for i, kk in enumerate(ranked)}


def build():
    errors = []
    rows = []
    seen_hashes = {}
    positions = _answer_positions()
    total_sub = 0

    for dm in DAIMON:
        passage = dm["passage"]
        h = hashlib.md5(passage.encode('utf-8')).hexdigest()
        if h in seen_hashes:
            errors.append(f'{dm["group"]}: 本文が「{seen_hashes[h]}」と重複')
        seen_hashes[h] = dm["group"]

        if ENTITY_RE.search(passage):
            errors.append(f'{dm["group"]}: 本文に HTML エンティティが残存')
        low = passage.lower()
        for hint in FIGURE_HINTS:
            if hint in low:
                errors.append(f'{dm["group"]}: 図依存表現「{hint}」を含む (本文だけで解けない恐れ)')

        subs = []
        for qi, sq in enumerate(dm["subqs"]):
            tag = f'{dm["group"]} 問{qi + 1}'
            correct = sq["correct"]
            distractors = sq["distractors"]

            if len(distractors) != 3:
                errors.append(f'{tag}: 誤答は 3 個必要 (実際 {len(distractors)} 個)')
            allc = [correct] + list(distractors)
            if len(set(allc)) != len(allc):
                errors.append(f'{tag}: 選択肢に重複がある')
            for ch in allc:
                if ENTITY_RE.search(ch):
                    errors.append(f'{tag}: 選択肢に HTML エンティティ「{ch}」')
                if not ch.strip():
                    errors.append(f'{tag}: 空の選択肢')

            pos = positions[(dm["group"], qi)]
            choices = list(distractors)
            choices.insert(pos, correct)
            if choices[pos] != correct:
                errors.append(f'{tag}: 正解位置の挿入に失敗')
            if not (0 <= pos < len(choices)):
                errors.append(f'{tag}: answer={pos} が選択肢の範囲外')

            explanation, why = build_explanation(dm["group"], qi, correct, distractors)
            if explanation is None:
                errors.append(f'{tag}: {why}')
                explanation = ''
            else:
                m = re.match(r'^正解は「(.*?)」。', explanation, re.S)
                if not m:
                    errors.append(f'{tag}: explanation が規定の書式で始まっていない')
                elif m.group(1) != choices[pos]:
                    errors.append(f'{tag}: explanation の正答テキストが選択肢と不一致')
                for sec in SECTIONS:
                    if sec not in explanation:
                        errors.append(f'{tag}: 必須セクション「{sec}」が無い')
                order = [explanation.find(sec) for sec in SECTIONS]
                if order != sorted(order):
                    errors.append(f'{tag}: 4 セクションの順序が規定と違う')
            if not sq["stem"].strip():
                errors.append(f'{tag}: 設問文が空')
            if not sq["unit"].strip():
                errors.append(f'{tag}: unit が空')

            subs.append({
                "id": f"q{qi + 1}",
                "type": "multiple_choice",
                "stem": sq["stem"],
                "choices": choices,
                "answer": pos,
                "unit": sq["unit"],
                "explanation": explanation,
            })
            total_sub += 1

        rows.append({
            "exam_id": "daigaku",
            "part_key": dm["part_key"],
            "eiken_grade": "kyotsu",
            "model": MODEL,
            "question_data": {
                "passage": passage,
                "subject": "英語",
                "univ_simulated": "共通テスト模試",
                "year_simulated": 2026,
                "source": SOURCE,
                "format_type": dm["group"],
                "questions": subs,
            },
        })

    if errors:
        print("❌ 検証エラー:")
        for e in errors:
            print("   -", e)
        raise SystemExit(1)

    dist = {0: 0, 1: 0, 2: 0, 3: 0}
    for r in rows:
        for q in r["question_data"]["questions"]:
            dist[q["answer"]] += 1

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"questions": rows, "skip_full": False}, f, ensure_ascii=False, indent=1)

    print(f"✅ 検証 OK: {len(rows)} 大問 / {total_sub} 小問")
    for pk in ("r_short", "r_long"):
        cnt = sum(1 for r in rows if r["part_key"] == pk)
        sub = sum(len(r["question_data"]["questions"]) for r in rows if r["part_key"] == pk)
        print(f"   {pk}: {cnt} 大問 / {sub} 小問")
    print(f"   正解位置の分布: {dist}")
    print(f"   → {os.path.relpath(OUT)}")


if __name__ == "__main__":
    build()
