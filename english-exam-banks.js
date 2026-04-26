// ==========================================================================
// 🎓 4試験サンプル問題バンク (TOEFL iBT / TOEIC L&R / IELTS / 英検)
// ==========================================================================
// english-exam.js から参照される静的問題プール。AI 接続前/失敗時の
// フォールバック + 「サンプル問題」として表示される。
//
// 拡張方針:
//  - Phase 1 (このファイル): 主要 part に各 5-10 問の高品質サンプル
//  - Phase 2 (DB自動生成): バックエンドが毎朝 Anthropic API で各 part に1問追加
//    → window.AUTO_GENERATED_BANKS に統合、フロントが両方から出題
// ==========================================================================

window.SAMPLE_BANKS = {
  // ========================================================================
  // TOEFL iBT
  // ========================================================================
  toefl: {
    r_passage1: {
      passage: `Throughout the 19th century, the Industrial Revolution dramatically reshaped urban landscapes across Europe and North America. Factories sprouted in city centers, drawing rural populations seeking employment. This rapid urbanization created unprecedented challenges: overcrowded tenements, polluted air, and inadequate sanitation. Reformers responded by advocating for public health regulations and worker protections. The cholera epidemics of the 1830s and 1850s, in particular, prompted scientific investigations that ultimately revolutionized epidemiology and urban planning. By the late 1800s, cities began implementing comprehensive sewer systems and zoning laws that would define modern urban infrastructure.`,
      questions: [
        { stem: 'According to the passage, what was a primary cause of urbanization during the Industrial Revolution?', choices: ['Government relocation programs', 'Rural populations seeking factory employment', 'The decline of agricultural productivity', 'New transportation networks alone'], answer: '1', explanation: '本文「drawing rural populations seeking employment」が根拠。雇用を求めて農村から都市へ流入。' },
        { stem: 'Why does the author mention the cholera epidemics?', choices: ['To describe rural-to-urban migration', 'To illustrate technological progress', 'To explain how scientific investigations led to urban reform', 'To criticize 19th-century medicine'], answer: '2', explanation: '直後の「prompted scientific investigations that ultimately revolutionized epidemiology and urban planning」が根拠。' },
        { stem: 'The word "unprecedented" most nearly means:', choices: ['Insignificant', 'Without prior occurrence', 'Carefully planned', 'Government-led'], answer: '1', explanation: 'unprecedented = 前例のない。文脈の「rapid urbanization created [unprecedented] challenges」=従来になかった課題。' },
        { stem: 'According to the passage, sewer systems and zoning laws emerged primarily as a response to:', choices: ['Industrial Revolution-era public health crises', 'Population decline in rural areas', 'Transportation infrastructure needs', 'Religious reform movements'], answer: '0', explanation: '本文最終文「By the late 1800s, cities began implementing comprehensive sewer systems and zoning laws」が、前段の「cholera epidemics → scientific investigations」の流れの結末として書かれている。' },
        { stem: 'The author\'s overall purpose in this passage is to:', choices: ['Argue against urbanization', 'Trace the relationship between industrialization and urban reform', 'Compare European and American cities', 'Predict future urban developments'], answer: '1', explanation: '産業革命→都市化の課題→改革→近代都市インフラの確立、という因果連鎖を辿る論理構造が主目的。' },
      ],
    },
    r_passage2: {
      passage: `Coral reefs are among the most biologically diverse ecosystems on Earth, supporting roughly 25% of all marine species despite covering less than 1% of the ocean floor. The structural complexity of reefs—built over thousands of years by colonies of tiny coral polyps—creates countless microhabitats for fish, invertebrates, and algae. However, these ecosystems are uniquely vulnerable to climate change. When ocean temperatures rise even slightly, corals expel the symbiotic algae living in their tissues, a phenomenon known as bleaching. Without these algae, which provide both color and most of the corals' nutrition, the corals turn ghostly white and may eventually die. Recent studies indicate that mass bleaching events, once rare, now occur every five to seven years in many reef systems—too frequent for full recovery between events.`,
      questions: [
        { stem: 'According to the passage, what makes coral reefs biologically significant?', choices: ['They cover most of the ocean floor', 'They support a disproportionately large share of marine species', 'They are easy to study', 'They provide most of the world\'s seafood'], answer: '1', explanation: '「supporting roughly 25% of all marine species despite covering less than 1% of the ocean floor」=面積比に対して種数が圧倒的多い (disproportionate)。' },
        { stem: 'The word "expel" is closest in meaning to:', choices: ['Absorb', 'Force out', 'Reproduce', 'Photograph'], answer: '1', explanation: 'expel = 追い出す/排出する。文脈は「corals expel the symbiotic algae」=共生藻を体外に放出。' },
        { stem: 'Why are mass bleaching events particularly concerning today?', choices: ['They produce attractive white reefs', 'They occur too frequently for full recovery', 'They only affect small reefs', 'They benefit fish populations'], answer: '1', explanation: '本文最終文「now occur every five to seven years in many reef systems—too frequent for full recovery between events」が根拠。' },
        { stem: 'The relationship between corals and the symbiotic algae is best described as:', choices: ['Predator and prey', 'Mutually beneficial', 'Competitive', 'Parasitic'], answer: '1', explanation: '「provide both color and most of the corals\' nutrition」= 藻が色と栄養の大半を提供。コーラルは住処を提供。互恵関係 (mutualism)。' },
        { stem: 'The passage suggests that the structural complexity of reefs is important because:', choices: ['It makes them easier to find', 'It creates microhabitats supporting biodiversity', 'It generates ocean currents', 'It produces oxygen'], answer: '1', explanation: '「The structural complexity of reefs ... creates countless microhabitats for fish, invertebrates, and algae」が直接の根拠。' },
      ],
    },
    l_lect1: {
      audio_script: `Professor: Today we'll explore why some scientific theories persist long after they're disproven. Consider the case of phlogiston theory in chemistry. From the late 1600s, scientists believed that flammable materials contained an invisible substance called phlogiston, which was released during combustion. This theory elegantly explained many observations: why metals lose mass when heated, for instance. But by the 1770s, Antoine Lavoisier conducted careful experiments showing that combustion actually involves combining with oxygen—not releasing phlogiston. Crucially, materials gain mass when burned, not lose it. So why didn't phlogiston theory immediately collapse? The answer lies in what historians of science call "rescue strategies." Defenders of phlogiston proposed that it had negative weight—a clearly absurd modification, but one that preserved the theory's core. This pattern repeats throughout science history: established theories don't die from a single contradicting experiment. They erode gradually as alternative frameworks demonstrate broader explanatory power.`,
      questions: [
        { stem: 'What is the main topic of the lecture?', choices: ['The chemistry of combustion', 'Why disproven scientific theories persist', 'Lavoisier\'s biography', 'The history of metals'], answer: '1', explanation: '冒頭「why some scientific theories persist long after they\'re disproven」が thesis。phlogiston は事例。' },
        { stem: 'According to the professor, what did Lavoisier\'s experiments demonstrate?', choices: ['Metals lose mass when heated', 'Phlogiston has negative weight', 'Combustion involves combining with oxygen', 'Fire is a separate element'], answer: '2', explanation: '「combustion actually involves combining with oxygen—not releasing phlogiston」が根拠。' },
        { stem: 'What is meant by "rescue strategies"?', choices: ['Methods to save endangered species', 'Modifications proposed to preserve a failing theory', 'Emergency lab safety procedures', 'New experimental designs'], answer: '1', explanation: '「modifications [...] but one that preserved the theory\'s core」と説明されている。' },
        { stem: 'Why does the professor mention "negative weight"?', choices: ['To praise creative scientific thinking', 'As an example of an absurd rescue strategy', 'To contradict modern physics', 'To explain mass conservation'], answer: '1', explanation: '「a clearly absurd modification, but one that preserved the theory\'s core」=絶望的な擁護策の例として挙げている。' },
        { stem: 'What conclusion does the professor draw about scientific change?', choices: ['Theories die instantly when disproven', 'Old theories erode gradually as alternatives prove more powerful', 'Most scientists are stubborn', 'Experimental evidence is unimportant'], answer: '1', explanation: '結論「They erode gradually as alternative frameworks demonstrate broader explanatory power」' },
      ],
    },
    s_task1: {
      prompt: 'Talk about a teacher or mentor who influenced you. Describe what made them special and how they impacted your life. You have 15 seconds to prepare and 45 seconds to respond.',
      sample: `One teacher who profoundly influenced me was my high school English instructor, Ms. Tanaka. What made her special was her unwavering belief in every student's potential. When I struggled with essay writing, she didn't just correct my mistakes—she sat with me after class, asking questions that helped me discover my own ideas. Her patience taught me that good writing comes from genuine thinking, not formulas. Today, whenever I face a challenging task, I remember her approach: break it down, ask the right questions, and trust the process. That mindset has shaped my approach to every problem I encounter.`,
    },
    s_task2: {
      prompt: 'Reading (45 seconds): The university announces it will close the campus library at 10 PM instead of midnight to reduce operating costs.\n\nListening (60-80 seconds): Two students discuss this announcement. The man strongly opposes it, citing two reasons.\n\nNow summarize the man\'s opinion and the reasons he gives. (60 seconds)',
      sample: `The university plans to close the campus library two hours earlier to save costs. The man strongly disagrees with this decision for two reasons. First, he argues that many students, particularly those with part-time jobs, can only study late at night when the library is quiet, and closing earlier would severely limit their study time. Second, he points out that the cost savings claim is misleading because the library staff already work fixed shifts, and the actual savings on electricity would be minimal compared to the impact on students' academic performance. He suggests the university should explore other cost-cutting measures rather than reducing essential study resources.`,
    },
    w_integrated: {
      prompt: 'Reading: Some scientists argue that solar geoengineering could be a viable short-term solution to climate change. The reading lists three potential benefits.\n\nLecture: The professor explains that the lecture casts doubt on each of the three benefits mentioned in the reading.\n\nWrite a 150-225 word response summarizing how the lecture challenges the reading\'s arguments.',
      sample: `The reading argues that solar geoengineering offers three benefits as a short-term climate solution. However, the lecture systematically challenges each of these claims.\n\nFirst, while the reading suggests that geoengineering could quickly cool global temperatures, the professor counters that this approach would only mask warming, not address the underlying CO2 accumulation. Once the intervention stops, temperatures would rebound rapidly.\n\nSecond, the reading praises the relatively low cost of geoengineering deployment. The professor refutes this by noting that long-term maintenance and monitoring expenses are substantial, and any system failure could trigger catastrophic climate disruption.\n\nFinally, regarding the reading's claim that geoengineering buys time for emission reductions, the lecture argues this assumption is flawed. Historical evidence shows that "moral hazard" effects emerge: societies tend to reduce mitigation efforts once they perceive a backup solution exists.\n\nThus, the lecture demonstrates that what appears to be benefits in the reading actually mask significant risks and unintended consequences, making solar geoengineering a far less promising solution than the reading suggests.`,
    },
    w_academic_disc: {
      prompt: 'Your professor is teaching a class on environmental policy. Write a post responding to the professor\'s question.\n\nProfessor: "If you were designing a city\'s climate policy, what single change would have the greatest positive impact: investing in public transportation, requiring all new buildings to be carbon-neutral, or planting massive amounts of urban trees? Why?"\n\n(Write at least 100 words. 10 minutes.)',
      sample: `I believe investing in public transportation would have the greatest positive impact, primarily because transportation is typically the largest source of urban emissions and reaches every demographic. While carbon-neutral buildings address future construction, they don't reduce emissions from existing structures, which dominate most cities for decades. Urban trees provide important benefits but cannot offset the millions of tons of CO2 from daily commutes.\n\nSuperior public transit, by contrast, can immediately reduce car dependency. Cities like Copenhagen demonstrate that high-quality transit systems shift commuter behavior dramatically, cutting per-capita emissions by 30-40%. Additionally, transit investment improves air quality, reduces traffic congestion, and provides equitable mobility for low-income residents who cannot afford cars. Unlike one-time building requirements, transit creates ongoing emission reductions throughout its operational lifetime.`,
    },
  },

  // ========================================================================
  // TOEIC L&R
  // ========================================================================
  toeic: {
    l_part2: {
      audio_script: 'Sample Part 2 question stems (10):\n1. Where did you put the quarterly report?\n2. Could you remind me when the meeting starts?\n3. How was the conference last week?\n4. Have you spoken with the new manager yet?\n5. Why has the deadline been extended?\n6. Don\'t you think we should hire more staff?\n7. The shipment arrived this morning, didn\'t it?\n8. Would you prefer to meet in person or via video call?\n9. Is the conference room available at 3 PM?\n10. When will the new policy take effect?',
      questions: [
        { stem: 'Where did you put the quarterly report?', choices: ['On your desk, near the monitor.', 'Yes, it was a productive quarter.', 'About thirty pages long.'], answer: '0', explanation: 'Where → 場所で答える。(B)(C) は同音語 quarter/pages の引っかけ。' },
        { stem: 'Could you remind me when the meeting starts?', choices: ['The conference room is upstairs.', 'It begins at 2:30 PM.', 'She remembered to call.'], answer: '1', explanation: 'when → 時刻で答える。(A)場所、(C)同音語 remind/remembered。' },
        { stem: 'How was the conference last week?', choices: ['It was very informative, actually.', 'Yes, every Monday.', 'The hotel is on Main Street.'], answer: '0', explanation: 'How was X? は感想・評価を尋ねる。(A) very informative が自然。' },
        { stem: 'Have you spoken with the new manager yet?', choices: ['I think she starts on Monday.', 'No, but I\'m planning to next week.', 'Yes, the meeting was yesterday.'], answer: '1', explanation: 'Have you...? は経験・完了。No, but I\'m planning to (まだだが今後予定) が自然な応答。' },
        { stem: 'Why has the deadline been extended?', choices: ['Until Friday afternoon.', 'Several team members are still finalizing data.', 'The previous deadline was last week.'], answer: '1', explanation: 'Why → 理由で答える。(A)期限、(C)前提情報の繰り返しは引っかけ。' },
        { stem: 'Don\'t you think we should hire more staff?', choices: ['Actually, I think we have enough.', 'No, the office is on the third floor.', 'They started last month.'], answer: '0', explanation: '否定疑問文 → 同意 or 反対意見で答える。Actually = 控えめな反対表明。' },
        { stem: 'The shipment arrived this morning, didn\'t it?', choices: ['Yes, around 9 AM.', 'It will leave tomorrow.', 'About fifty boxes.'], answer: '0', explanation: '付加疑問文 → Yes/No + 詳細。Yes, around 9 AM が完璧。' },
        { stem: 'Would you prefer to meet in person or via video call?', choices: ['Either works for me.', 'No, I\'m not free today.', 'It\'s a long meeting.'], answer: '0', explanation: '選択疑問文 → どちらか or「どちらでも」(Either) が頻出パターン。' },
        { stem: 'Is the conference room available at 3 PM?', choices: ['Let me check the schedule.', 'It\'s on the fourth floor.', 'Yes, it was a great room.'], answer: '0', explanation: 'Yes/No 疑問文だが「確認する」(Let me check) も TOEIC 頻出の正解パターン。' },
        { stem: 'When will the new policy take effect?', choices: ['Starting next month, I believe.', 'It\'s a major change.', 'Yes, everyone has been notified.'], answer: '0', explanation: 'When → 時で答える。「Starting + 時期」は TOEIC 定型。' },
      ],
    },
    r_part5: {
      questions: [
        { stem: 'The new software allows employees to ___ their work hours more efficiently.', choices: ['manage', 'manager', 'management', 'managed'], answer: '0', explanation: 'allow + O + to V (動詞原形)。manage = 動詞原形。' },
        { stem: 'All employees are required to submit their expense reports ___ Friday.', choices: ['until', 'by', 'on', 'in'], answer: '1', explanation: 'by Friday = 金曜日までに (期限)。until は継続、on は曜日上の動作、in は月。' },
        { stem: 'The CEO announced that the company ___ its operations to Asia next year.', choices: ['expands', 'expanded', 'will expand', 'has expanded'], answer: '2', explanation: 'next year = 未来 → will expand。announced との時制ずれは「未来への発表」で正解。' },
        { stem: 'Please make sure to ___ all confidential documents in the locked cabinet.', choices: ['store', 'storing', 'stored', 'storage'], answer: '0', explanation: 'to + 動詞原形。to store。' },
        { stem: 'The marketing team has ___ been working on the new campaign for three months.', choices: ['recently', 'currently', 'already', 'rarely'], answer: '2', explanation: '現在完了進行形 (has been working) と「3ヶ月間」→ already (もうすでに)。currently は現在進行と相性が良いが期間を伴わない。' },
        { stem: 'The proposal was rejected ___ it lacked specific budget details.', choices: ['although', 'because', 'despite', 'unless'], answer: '1', explanation: '「却下された ← 予算の詳細が無かった」=理由。because。although は逆接、despite は名詞前。' },
        { stem: 'Mr. Tanaka, ___ has been with the company for 20 years, will retire next month.', choices: ['who', 'which', 'whose', 'where'], answer: '0', explanation: '人 (Mr. Tanaka) を先行詞とする主格関係代名詞 → who。' },
        { stem: 'The renovation is expected to be completed ___ schedule.', choices: ['in', 'on', 'at', 'with'], answer: '1', explanation: 'on schedule = 予定通り。on time (時間通り) と並んで頻出イディオム。' },
        { stem: 'We need to find ___ supplier for our packaging materials by the end of the month.', choices: ['reliable', 'reliably', 'reliability', 'reliance'], answer: '0', explanation: '名詞 (supplier) を修飾 → 形容詞。reliable supplier = 信頼できる業者。' },
        { stem: 'The presentation was ___ informative that everyone took detailed notes.', choices: ['such', 'so', 'too', 'very'], answer: '1', explanation: 'so + 形容詞 + that S V = 非常に〜なので S が V する。such は名詞前。' },
        { stem: 'Customer feedback ___ regularly to identify areas for improvement.', choices: ['reviews', 'reviewing', 'is reviewed', 'has reviewing'], answer: '2', explanation: 'feedback は「レビューされる」=受動態。is reviewed。' },
        { stem: 'The hotel offers ___ amenities, including a gym, spa, and rooftop pool.', choices: ['various', 'variety', 'varied', 'variously'], answer: '0', explanation: '名詞 (amenities) を修飾 → 形容詞。various = 様々な。' },
      ],
    },
    r_part6: {
      passage: `To: All Department Heads\nFrom: HR Department\nSubject: Updated Remote Work Policy\n\nEffective next month, our updated remote work policy will allow employees to work from home up to three days per week. (1) ___ , supervisors must approve weekly schedules in advance to ensure adequate office coverage.\n\nEmployees who wish to take advantage of this option should submit their preferred schedule by the 25th of each month. Approval will be (2) ___ on team needs and individual performance. We believe this flexibility (3) ___ employee satisfaction while maintaining productivity.`,
      questions: [
        { stem: '(1) ___ : 接続詞・副詞の選択', choices: ['Therefore', 'However', 'Otherwise', 'Furthermore'], answer: '1', explanation: '前文「3日まで在宅可能」と後文「事前承認必須」の関係 = 譲歩・対比 → However。' },
        { stem: '(2) ___ : 動詞句の選択', choices: ['based', 'caused', 'made', 'taken'], answer: '0', explanation: 'be based on = 〜に基づく。承認はチーム必要性と個人実績に基づく。' },
        { stem: '(3) ___ : 時制と語法', choices: ['will improve', 'has improved', 'improving', 'is improved'], answer: '0', explanation: '主節 (We believe) + that 節の中で「未来の効果」を述べる → will improve。' },
        { stem: '次の文を文中の最も適切な位置に挿入してください: "We will hold a Q&A session next Friday for any questions about implementation."', choices: ['段落1の冒頭', '段落1の末尾', '段落2の冒頭', '段落2の末尾'], answer: '3', explanation: '実施詳細を述べた最後に「質問あれば金曜のQ&A」と告知するのが論理的。' },
      ],
    },
  },

  // ========================================================================
  // IELTS Academic
  // ========================================================================
  ielts: {
    l_sec1: {
      audio_script: `Receptionist: Hello, City Library. How can I help you?\nCustomer: Hi, I\'d like to register for a library card.\nReceptionist: Of course. May I have your full name?\nCustomer: It\'s Sarah Mitchell. M-I-T-C-H-E-L-L.\nReceptionist: And your address?\nCustomer: 47 Oakwood Avenue, postcode SE19 3PN.\nReceptionist: Phone number?\nCustomer: 0207 555 4892.\nReceptionist: Thank you. The annual membership fee is £15. Would you like to pay by card or cash?\nCustomer: Card, please. Also, can I borrow audiobooks?\nReceptionist: Yes, but you\'ll need to download our app first. Up to 6 audiobooks at a time.`,
      questions: [
        { stem: 'What is the customer\'s last name?', choices: ['Mitchel', 'Mitchell', 'Michell', 'Mitchel'], answer: '1', explanation: 'スペル「M-I-T-C-H-E-L-L」を聞き取る。L が2つ。' },
        { stem: 'What is the customer\'s house number?', choices: ['17', '47', '74', '57'], answer: '1', explanation: '「47 Oakwood Avenue」と聞き取る。数字の聞き取りは IELTS 頻出。' },
        { stem: 'What is the postcode?', choices: ['SE19 3PN', 'SE9 3PM', 'SE19 3PM', 'SC19 3PN'], answer: '0', explanation: 'SE19 3PN を正確に聞き取る。アルファベット+数字の混合は要練習。' },
        { stem: 'What is the annual membership fee?', choices: ['£5', '£15', '£50', '£55'], answer: '1', explanation: 'fifteen pounds = £15。fifty (£50) と混同しないよう注意。' },
        { stem: 'How many audiobooks can the customer borrow at one time?', choices: ['3', '6', '10', '16'], answer: '1', explanation: '「Up to 6 audiobooks at a time」が根拠。6 と 16 の聞き分けは難しいので注意。' },
      ],
    },
    r_p1: {
      passage: `The Lost City of Mohenjo-Daro\n\nIn the early 1920s, archaeologists excavating in the Indus Valley uncovered the remains of an ancient city later named Mohenjo-Daro, which means "Mound of the Dead." Built around 2500 BCE, this remarkable settlement was home to an estimated 40,000 inhabitants at its peak, making it one of the largest cities of the Bronze Age. What astonished researchers was its sophistication: rectangular street grids organized into precise blocks, brick houses with private bathrooms, and an elaborate drainage system that rivaled anything in the ancient world.\n\nUnlike contemporary civilizations in Mesopotamia and Egypt, Mohenjo-Daro shows no evidence of monumental temples, palaces, or royal tombs. This absence has puzzled archaeologists for decades. Some scholars argue that this points to an unusually egalitarian society without rigid class hierarchies. Others suggest that political power was distributed across the city's various administrative districts. The absence of large-scale weaponry similarly suggests a relatively peaceful civilization.\n\nDespite extensive excavations, the script used by Mohenjo-Daro\'s inhabitants—known as the Indus script—remains undeciphered. Hundreds of seals bearing brief inscriptions have been recovered, but without a bilingual reference text like the Rosetta Stone, scholars cannot definitively translate the language. Around 1900 BCE, the city was mysteriously abandoned. Theories range from climate change and shifting river courses to invasion by outside groups, though current evidence increasingly favors environmental causes.`,
      questions: [
        { stem: 'According to the passage, Mohenjo-Daro was built around:', choices: ['1900 BCE', '2500 BCE', '1920 CE', '4000 BCE'], answer: '1', explanation: '本文「Built around 2500 BCE」が根拠。1900 BCE は abandoned の年。' },
        { stem: 'TRUE / FALSE / NOT GIVEN: Mohenjo-Daro had a population larger than any other Bronze Age city.', choices: ['TRUE', 'FALSE', 'NOT GIVEN'], answer: '2', explanation: '本文は「one of the largest」と書かれており、最大とは断定していない → NOT GIVEN。' },
        { stem: 'TRUE / FALSE / NOT GIVEN: No evidence of royal palaces has been found at Mohenjo-Daro.', choices: ['TRUE', 'FALSE', 'NOT GIVEN'], answer: '0', explanation: '本文「shows no evidence of monumental temples, palaces, or royal tombs」と完全一致 → TRUE。' },
        { stem: 'Why is the Indus script still undeciphered?', choices: ['It has been lost', 'There is no bilingual reference text', 'Scholars are not interested', 'The seals are damaged'], answer: '1', explanation: '本文「without a bilingual reference text like the Rosetta Stone」が根拠。' },
        { stem: 'Choose the correct ending: Current evidence suggests Mohenjo-Daro was abandoned primarily due to ___', choices: ['invasion', 'environmental causes', 'disease', 'religious conflict'], answer: '1', explanation: '本文「current evidence increasingly favors environmental causes」が根拠。' },
        { stem: 'TRUE / FALSE / NOT GIVEN: Mohenjo-Daro had more advanced drainage than any other ancient city.', choices: ['TRUE', 'FALSE', 'NOT GIVEN'], answer: '0', explanation: '本文「an elaborate drainage system that rivaled anything in the ancient world」が示唆 → TRUE。' },
      ],
    },
    w_task1: {
      prompt: 'The chart below shows the percentage of households in the UK with internet access from 2000 to 2020.\n\n[Chart data: 2000 = 25%, 2005 = 55%, 2010 = 75%, 2015 = 88%, 2020 = 96%]\n\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant. (Write at least 150 words. 20 minutes.)',
      sample: `The line chart illustrates the proportion of UK households with internet access over a 20-year period from 2000 to 2020.\n\nOverall, internet access among UK households increased dramatically across the entire period, rising from a quarter to nearly universal coverage by 2020.\n\nIn 2000, only 25% of households had internet access. This figure grew rapidly during the first decade, reaching 55% by 2005 and climbing further to 75% by 2010. The most significant growth occurred between 2000 and 2010, with household connectivity tripling within ten years.\n\nFollowing this period of rapid expansion, the rate of growth gradually slowed as the market approached saturation. Between 2010 and 2015, household internet access rose from 75% to 88%, a more modest increase of 13 percentage points. By 2020, the figure had reached 96%, indicating that internet access had become nearly ubiquitous in UK households.\n\nThe data demonstrates a clear S-curve pattern typical of technology adoption: slow initial growth, rapid mid-period expansion, and eventual leveling-off as market penetration approaches its limit.\n(192 words)`,
    },
    w_task2: {
      prompt: 'Some people believe that universities should focus on practical skills that prepare students for employment, while others argue that universities should emphasize academic knowledge and critical thinking. Discuss both views and give your own opinion. (Write at least 250 words. 40 minutes.)',
      sample: `Higher education has long been a subject of debate, with some advocating for vocational, employment-focused training and others championing pure academic inquiry. While both perspectives have merit, I believe a balanced approach best serves students and society.\n\nProponents of practical training argue that universities should equip graduates with employable skills. In an increasingly competitive job market, students invest heavily in their education and reasonably expect tangible career outcomes. Programs in engineering, computer science, and business administration explicitly train students for specific industries, producing workforce-ready professionals who contribute immediately to economic growth.\n\nHowever, those favoring academic depth contend that universities should cultivate critical thinking, intellectual curiosity, and broad knowledge. They argue that overly vocational training narrows students' perspectives and fails to prepare them for the unpredictable, evolving demands of modern careers. Studying philosophy, literature, or pure mathematics develops analytical capacities transferable to any field, fostering adaptable, lifelong learners rather than narrowly-trained technicians.\n\nIn my view, these perspectives are not mutually exclusive. The most effective university education integrates rigorous academic foundations with applied learning opportunities. For instance, a computer science degree should combine theoretical algorithms with practical projects; a literature degree benefits from internships in publishing or journalism. This dual approach produces graduates who possess both intellectual depth and real-world competence.\n\nIn conclusion, while practical employability and academic rigor each have value, universities serve students best by combining both. Education should prepare individuals not only for their first job but for a lifetime of meaningful work and citizenship.\n(258 words)`,
    },
  },

  // ========================================================================
  // 英検 (級ごとに part 構成異なる)
  // ========================================================================
  eiken: {
    // 英検 1級 — 短文穴埋め (語彙)
    g1_r_q1: {
      questions: [
        { stem: 'The professor gave a ( ) lecture on quantum mechanics that left even physics majors scratching their heads.', choices: ['mundane', 'recondite', 'jovial', 'tepid'], answer: '1', explanation: 'recondite = 難解な、深遠な (C1レベル語彙)。「quantum mechanics で physics majors も困惑」=非常に難解。' },
        { stem: 'The CEO\'s ( ) approach to negotiations earned her respect across the industry.', choices: ['perfunctory', 'sagacious', 'lugubrious', 'turgid'], answer: '1', explanation: 'sagacious = 賢明な、洞察力のある。CEO の交渉姿勢として「業界で尊敬される」と整合。' },
        { stem: 'The witness gave a ( ) account of the incident, omitting no relevant detail.', choices: ['curt', 'meticulous', 'ambiguous', 'impromptu'], answer: '1', explanation: 'meticulous = 綿密な、几帳面な。「omitting no relevant detail」と完全に整合。' },
      ],
    },
    // 英検 準1級 — Reading 大問1
    gp1_r_q1: {
      questions: [
        { stem: 'The economy showed signs of ( ) after years of stagnation, with consumer spending finally on the rise.', choices: ['recovery', 'decline', 'collapse', 'isolation'], answer: '0', explanation: 'recovery = 回復 (B2レベル)。「stagnation の後」「consumer spending on the rise」と整合。' },
        { stem: 'Despite the company\'s best efforts, the new product launch was ( ) by supply chain issues.', choices: ['enhanced', 'hampered', 'celebrated', 'announced'], answer: '1', explanation: 'hampered = 妨げられた (B2)。「Despite best efforts」「supply chain issues」=ネガティブ要素 → 妨害動詞。' },
        { stem: 'The research findings have significant ( ) for educational policy worldwide.', choices: ['implications', 'descriptions', 'celebrations', 'occupations'], answer: '0', explanation: 'implications = 含意・影響 (B2 頻出)。「research findings」と「policy」を結ぶ自然な語。' },
        { stem: 'She decided to ( ) her career as a lawyer to pursue her passion for art.', choices: ['enhance', 'abandon', 'establish', 'multiply'], answer: '1', explanation: 'abandon = 放棄する (B1-B2)。「弁護士の仕事を諦めて美術を追求」と整合。' },
        { stem: 'The committee unanimously ( ) the proposal after a thorough review.', choices: ['rejected', 'approved', 'criticized', 'submitted'], answer: '1', explanation: 'unanimously approved = 全会一致で承認。「thorough review の後」=肯定的判断のニュアンス。' },
      ],
    },
    // 英検 準1級 — Writing エッセイ
    gp1_w_essay: {
      prompt: 'TOPIC: Should the government invest more in renewable energy?\n\nPOINTS\n- Cost\n- Environment\n- Energy security\n- Job creation\n\nWrite an essay on the topic above. Use TWO of the points above to support your answer. (120-150 words)',
      sample: `Yes, the government should invest more heavily in renewable energy, primarily because of its environmental benefits and contribution to long-term energy security.\n\nFirst, renewable sources such as solar and wind power generate electricity without producing carbon emissions, which is crucial for combating climate change. Traditional fossil fuels release vast amounts of greenhouse gases, accelerating global warming and threatening ecosystems. By prioritizing renewables, governments can significantly reduce their nation's carbon footprint and meet international climate commitments.\n\nSecond, renewable energy enhances energy security by reducing dependence on imported fossil fuels. Countries reliant on foreign oil and gas are vulnerable to price fluctuations and geopolitical conflicts. Domestic renewable infrastructure provides stable, predictable energy supplies that strengthen national independence.\n\nFor these reasons, increased government investment in renewable energy is essential for both environmental sustainability and national security.\n(132 words)`,
    },
    // 英検 2級 — Reading 大問1
    g2_r_q1: {
      questions: [
        { stem: 'The teacher told us to ( ) our textbooks to page 23.', choices: ['turn', 'open', 'put', 'show'], answer: '1', explanation: 'open ~ to page X (B1レベル)。turn to a page も使われるが open がより一般的。' },
        { stem: 'I\'m really ( ) about the test results. I studied so hard.', choices: ['nervous', 'famous', 'noisy', 'angry'], answer: '0', explanation: 'nervous = 緊張している。「一生懸命勉強した」と整合。' },
        { stem: 'My grandmother lives in a small ( ) in the countryside.', choices: ['village', 'building', 'station', 'office'], answer: '0', explanation: 'in the countryside (田舎) との整合。' },
        { stem: 'Could you ( ) me how to use this machine?', choices: ['show', 'see', 'look', 'watch'], answer: '0', explanation: 'show O how to V = O に〜の仕方を教える。see/look は不可。' },
        { stem: 'The library is ( ) from 9 AM to 8 PM every day.', choices: ['closed', 'open', 'broken', 'empty'], answer: '1', explanation: 'open from X to Y = X時から Y時まで開いている。営業時間の典型表現。' },
      ],
    },
    // 英検 3級 — Reading 大問1
    g3_r_q1: {
      questions: [
        { stem: 'A: Do you like ( ) ? B: Yes, I love it. I read every day.', choices: ['cooking', 'reading', 'singing', 'swimming'], answer: '1', explanation: 'B の応答「I read every day」と整合 → reading。' },
        { stem: 'My mother always ( ) breakfast for me before I go to school.', choices: ['makes', 'opens', 'plays', 'goes'], answer: '0', explanation: 'make breakfast = 朝食を作る (中学初級)。' },
        { stem: 'Tom is good ( ) playing the guitar.', choices: ['at', 'in', 'for', 'on'], answer: '0', explanation: 'be good at + Ving = 〜が上手 (中学頻出)。' },
        { stem: 'It\'s very cold today. You should wear ( ) jacket.', choices: ['a warm', 'an warm', 'warm', 'warmly'], answer: '0', explanation: '可算名詞 jacket + 形容詞 warm + 不定冠詞 a。warm は子音 w で始まるので a。' },
      ],
    },
  },
};

// ============================================================================
// 🇯🇵 大学入試対策 SAMPLE_BANKS (国公立 + 私立 + 医学部 + 共通テスト)
// ============================================================================
// 大学入試の過去問は著作権が大学・出題者に帰属するため、
// 本サービスでは「○○大学型」AI生成類題を中心に提供する。
// 過去問そのものを引用する場合は出典 (大学名+年度+問題番号) を必ず明記。
window.SAMPLE_BANKS.daigaku = {
  // ========== 東京大学 ==========
  todai_r_long: {
    passage: `Memory is often described as a kind of recording device, faithfully preserving experiences for later retrieval. This metaphor, however, is fundamentally misleading. Modern neuroscience reveals that memory is reconstructive rather than reproductive: every act of remembering reshapes the very memory being recalled. When we retrieve a memory, the brain does not play back a stored file; it actively reassembles fragments of sensory, emotional, and contextual information. During this reconstruction, current beliefs, moods, and subsequent experiences seep into the memory, subtly altering it. This explains why eyewitness testimony, once considered the gold standard of evidence, is now known to be remarkably unreliable. Two witnesses to the same event may produce contradictory accounts not because either is lying, but because their reconstructions diverge based on what each individual brings to the act of remembering.\n\nThis discovery has profound implications. If memory is malleable, then identity itself—built upon our remembered experiences—becomes more fluid than we imagine. Yet this fluidity is not a defect but a feature: it allows us to integrate new knowledge with old, to revise our understanding of past events in light of present wisdom, and to maintain a coherent narrative of self despite the constant flux of experience.`,
    questions: [
      { stem: '本文の内容に最も近いものを選べ。', choices: ['記憶は録音装置のように忠実に保存される', '記憶は思い出すたびに再構築され変化する', '目撃証言は最も信頼できる証拠である', '記憶の流動性は人格の欠陥である'], answer: '1', explanation: '本文「memory is reconstructive rather than reproductive」「every act of remembering reshapes the very memory」が直接の根拠。東大型は「本文の主旨」を問う設問が頻出。' },
      { stem: 'なぜ目撃証言は信頼性が低いと現在では考えられているのか?', choices: ['証人が嘘をつくから', '記憶の再構築が個人ごとに異なる方向へ進むから', '事件直後の混乱で記憶が消えるから', '法廷で緊張して言葉が出ないから'], answer: '1', explanation: '本文「their reconstructions diverge based on what each individual brings to the act of remembering」が根拠。' },
      { stem: '下線部「This fluidity is not a defect but a feature」の意味として最も適切なものは?', choices: ['記憶の流動性は人格の弱点である', '記憶の流動性は本来あるべき機能である', '記憶の流動性は治療すべき症状である', '記憶の流動性は教育で克服すべきものである'], answer: '1', explanation: 'not A but B = AではなくB。defect (欠陥) ではなく feature (機能・特徴)。東大型「下線部解釈」の典型。' },
    ],
  },
  todai_r_summary: {
    passage: `[要約問題用] Climate change is altering the timing of natural events worldwide. Scientists call this phenomenon "phenological mismatch": when species that depend on each other—predator and prey, pollinator and flower—respond differently to warming temperatures, their life cycles fall out of sync. For instance, in some forests, caterpillars now emerge two weeks before the migratory birds that have historically fed their chicks on these caterpillars arrive. The chicks face starvation, while the unconsumed caterpillars defoliate trees. Such mismatches are accumulating across ecosystems, threatening the intricate webs of dependency built over millennia.`,
    questions: [
      { stem: '本文を50字程度で要約しなさい (東大型 大問1B)', choices: ['気候変動による生物間の同期ずれ「フェノロジー・ミスマッチ」が、捕食者と被食者の相互依存を崩し生態系に脅威をもたらしている。', '気候変動は鳥に良い影響を与え、毛虫を減らす。', 'キャタピラーが森を枯らしている。', '生態系は何千年もかけて形成された。'], answer: '0', explanation: '東大型 大問1B は「与えられた英文を所定字数で日本語要約」。本文の主旨「phenological mismatch が生態系の依存関係を脅かす」を簡潔に。' },
    ],
  },
  todai_w_essay: {
    prompt: `次の意見について、あなたの考えを60-80語の英語で述べよ。 (東大型 大問2A 自由英作)\n\n"Some people believe that traveling abroad is the most effective way to broaden one's perspective. Do you agree?"`,
    sample: `I partially agree. While traveling abroad does expose us to different cultures, languages, and ways of thinking, it is not the only way to broaden one's perspective. Reading diverse books, engaging in conversations with people from different backgrounds, and exploring new disciplines can be equally transformative. Furthermore, travel itself does not guarantee growth; it depends on one's openness and willingness to engage deeply with unfamiliar experiences. (78 words)\n\n【採点ポイント】60-80語の語数厳守 / 立場明示 (partially agree) / 理由2-3点 / 具体例 / 結論。東大型は「単純Yes/Noではない nuanced な意見」が高得点。`,
  },
  todai_r_translation: {
    prompt: `次の下線部を日本語に訳しなさい。(東大型 大問4B 和訳)\n\nThe widespread adoption of artificial intelligence in education has reignited a debate that has accompanied every technological revolution: <underline>whether the new tool will liberate human potential or merely automate the practices it was meant to enhance, ultimately diminishing the very capacities it promised to develop.</underline>`,
    sample: `【模範訳】その新しい道具が人間の可能性を解放するのか、それとも本来高めるべきはずだった営みを単に自動化してしまい、結果として、本来育てるはずだった能力そのものを衰えさせてしまうのか、という問題である。\n\n【採点ポイント】whether A or B 構造の正確な把握 / 関係詞節 (it was meant to enhance / it promised to develop) の処理 / ultimately diminishing... の分詞構文の意味取り。東大型和訳は文構造の正確な再現が最優先。`,
  },

  // ========== 京都大学 ==========
  kyodai_r_long: {
    passage: `Philosophy of mind has long grappled with the question of consciousness: how does subjective experience—the feeling of seeing red, tasting coffee, or feeling pain—arise from objective physical processes in the brain? David Chalmers famously distinguished the "easy problems" of consciousness (explaining cognitive functions like attention, memory, and behavior) from the "hard problem" (explaining why these functions are accompanied by subjective experience at all). The easy problems, while technically demanding, are at least tractable through standard scientific methods. The hard problem, however, seems to resist all such approaches. We can describe in exquisite detail the neural activity correlated with seeing red, but no amount of such description seems to explain why there should be any subjective experience accompanying that activity, rather than mere unconscious information processing.`,
    questions: [
      { stem: '"the hard problem" とは何か。本文に即して説明せよ。', choices: ['認知機能を解明する技術的困難', '主観的経験がなぜ物理プロセスから生じるのかという問題', '脳の神経活動を観察する難しさ', '哲学者間の意見対立'], answer: '1', explanation: '本文「explaining why these functions are accompanied by subjective experience at all」が定義。京大型は本文を踏まえた説明問題が頻出。' },
      { stem: '京大型 和訳問題: "no amount of such description seems to explain why there should be any subjective experience accompanying that activity"', choices: ['そのような記述をいくら積み重ねても、なぜその活動に主観的経験が伴うのかを説明することはできないように思われる。', 'このような記述は経験を説明する。', '主観的経験は脳活動と無関係である。', '科学は主観性を証明済みである。'], answer: '0', explanation: '京大型は構造把握型和訳。no amount of X seems to Y = いかに X を重ねても Y することはできないように思われる。' },
    ],
  },

  // ========== 早稲田大学 ==========
  waseda_r_long: {
    passage: `The proliferation of digital communication has fundamentally altered how humans form and maintain relationships. While previous generations relied on letters, telephone calls, and face-to-face meetings, today's interactions occur predominantly through screens. This shift has produced both democratizing effects—enabling connections across vast distances and social barriers—and unforeseen consequences for the texture of human bonds. Researchers studying online friendships have found that while digital networks can sustain relationships across time and space, they often lack the depth that emerges from shared physical presence. The absence of nonverbal cues—facial expressions, tone of voice, body language—removes layers of meaning that face-to-face conversation conveys effortlessly. Moreover, the curated nature of online self-presentation can create an illusion of intimacy while actually obscuring the messy, contradictory reality of human personality.`,
    questions: [
      { stem: 'According to the passage, what is one downside of digital communication?', choices: ['It only works for short distances', 'It lacks nonverbal cues that convey meaning', 'It is too expensive for most people', 'It requires special training'], answer: '1', explanation: '本文「The absence of nonverbal cues...removes layers of meaning」が根拠。' },
      { stem: 'What does "the curated nature of online self-presentation" suggest?', choices: ['Online identities are always genuine', 'People carefully select what they share online', 'Curators design social media platforms', 'Self-presentation is forbidden online'], answer: '1', explanation: 'curated = 厳選された/編集された。早大型 (政経・社学・国際) では語彙の文脈推定問題が頻出。' },
      { stem: 'The author\'s overall stance toward digital communication is best described as:', choices: ['Strongly opposed', 'Uncritically enthusiastic', 'Balanced, recognizing both benefits and drawbacks', 'Indifferent'], answer: '2', explanation: '本文「democratizing effects」(肯定面) と「lack the depth」「illusion of intimacy」(否定面) の両論併記が根拠。早大型「筆者の立場」問題。' },
    ],
  },

  // ========== 慶應義塾大学 ==========
  keio_r_long: {
    passage: `In the field of behavioral economics, scholars have repeatedly demonstrated that humans are not the rational utility-maximizers assumed by classical economic theory. Daniel Kahneman and Amos Tversky's groundbreaking work on cognitive biases revealed systematic patterns in how people deviate from rational decision-making. The "anchoring effect," for instance, shows that initial information disproportionately influences subsequent judgments, even when that information is arbitrary or irrelevant. The "loss aversion" phenomenon demonstrates that the pain of losing something is psychologically about twice as powerful as the pleasure of gaining the equivalent. These findings have transformed not only economics but also public policy, marketing, and even medical decision-making. Governments now design "nudges"—subtle policy interventions that guide citizens toward beneficial choices without restricting freedom—based on behavioral insights. For instance, making organ donation an opt-out rather than opt-in choice has dramatically increased donation rates in countries that have adopted this policy.`,
    questions: [
      { stem: 'What does "loss aversion" refer to according to the passage?', choices: ['People prefer to avoid all losses', 'The psychological pain of loss exceeds the pleasure of equivalent gain', 'Losses are mathematically larger than gains', 'Investors should never sell at a loss'], answer: '1', explanation: '本文「the pain of losing... is psychologically about twice as powerful as the pleasure of gaining the equivalent」が根拠。慶應 (経済・商) 頻出テーマ。' },
      { stem: 'How have governments applied behavioral economics insights?', choices: ['By restricting individual freedom', 'By designing "nudges" that guide choices without coercion', 'By eliminating organ donation programs', 'By ignoring psychological factors'], answer: '1', explanation: '本文「nudges—subtle policy interventions that guide citizens toward beneficial choices without restricting freedom」が根拠。' },
      { stem: 'The opt-out organ donation policy is mentioned as an example of:', choices: ['A failed government intervention', 'Successful application of behavioral insights', 'Restriction of personal freedom', 'A controversial medical practice'], answer: '1', explanation: 'For instance 直前の文「Governments now design nudges」の具体例として提示されている。' },
    ],
  },

  // ========== 共通テスト ==========
  kyotsu_r_long: {
    passage: `(共通テスト Reading 大問6型) Sustainable fashion has emerged as a major movement in the textile industry. Traditional fashion production consumes vast amounts of water—producing a single cotton T-shirt requires approximately 2,700 liters, equivalent to one person's drinking water for 2.5 years. Additionally, the industry generates roughly 10% of global carbon emissions, more than international flights and maritime shipping combined. In response, many brands now offer "eco-conscious" collections using recycled materials, organic cotton, and innovative fabrics made from agricultural waste. However, critics argue that "fast fashion" companies engaging in such initiatives often produce these collections in small quantities while continuing to manufacture much larger amounts of conventional, environmentally harmful clothing—a practice known as "greenwashing." True sustainability, experts contend, requires fundamental changes to production volumes, supply chain transparency, and consumer behavior, including embracing concepts like clothing repair, secondhand shopping, and longer garment lifespans.`,
    questions: [
      { stem: 'According to the passage, how much water is used to produce one cotton T-shirt?', choices: ['About 270 liters', 'About 2,700 liters', 'About 27,000 liters', 'About 270,000 liters'], answer: '1', explanation: '本文「approximately 2,700 liters」が直接の根拠。共通テスト Reading は数字の正確な聞き取り (Listening) と読み取り (Reading) が必須。' },
      { stem: 'What is "greenwashing"?', choices: ['Cleaning clothes with eco-friendly detergent', 'Marketing oneself as eco-friendly while continuing harmful practices', 'A new dyeing technique', 'A government certification process'], answer: '1', explanation: '本文「producing these collections in small quantities while continuing to manufacture much larger amounts of conventional, environmentally harmful clothing」が greenwashing の説明。' },
      { stem: 'According to experts, what does true sustainability require?', choices: ['Only using organic cotton', 'Fundamental changes including consumer behavior', 'Banning all conventional clothing', 'Government subsidies'], answer: '1', explanation: '本文「True sustainability...requires fundamental changes to production volumes, supply chain transparency, and consumer behavior」が根拠。' },
    ],
  },

  // ========== 国公立医学部 ==========
  igakubu_r_long: {
    passage: `(医学部型) The development of CRISPR-Cas9 gene-editing technology has revolutionized biomedical research and opened unprecedented possibilities for treating genetic diseases. Originally identified as part of bacterial immune systems, CRISPR allows scientists to make precise modifications to DNA sequences in living cells with remarkable efficiency and accuracy. Clinical trials have already demonstrated promising results in treating previously incurable conditions: sickle cell disease, beta-thalassemia, and certain inherited forms of blindness. However, the same technology that promises medical breakthroughs also raises profound ethical questions, particularly regarding germline editing—modifications that would be inherited by future generations. The 2018 case of He Jiankui, a Chinese scientist who created the first gene-edited babies, sparked international condemnation and intensified debates about the boundaries of permissible genetic intervention. Most scientific bodies now advocate for strict regulation of germline modifications, though some researchers argue that complete prohibition would impede medical progress for serious genetic disorders.`,
    questions: [
      { stem: 'What is the medical significance of CRISPR-Cas9 technology?', choices: ['It cures all diseases automatically', 'It allows precise modification of DNA to treat genetic diseases', 'It replaces traditional surgery', 'It is only used for research, not treatment'], answer: '1', explanation: '本文「CRISPR allows scientists to make precise modifications to DNA sequences...treating previously incurable conditions」が根拠。医学部入試では先端医療技術の文章が頻出。' },
      { stem: 'Why is germline editing particularly controversial?', choices: ['It is too expensive', 'Modifications would be inherited by future generations', 'It does not work effectively', 'Only one country can perform it'], answer: '1', explanation: '本文「germline editing—modifications that would be inherited by future generations」が controversial の理由。世代を超えた影響が倫理問題。' },
      { stem: 'What do most scientific bodies currently recommend regarding germline modifications?', choices: ['Complete unrestricted use', 'Strict regulation', 'Total prohibition with no exceptions', 'No formal position'], answer: '1', explanation: '本文「Most scientific bodies now advocate for strict regulation of germline modifications」が根拠。' },
    ],
  },

  // ========== 私立医学部 ==========
  igakubu_shiritsu_r_long: {
    passage: `(私立医学部型) Antibiotic resistance has emerged as one of the most pressing global health crises of the 21st century. The widespread overuse and misuse of antibiotics—both in human medicine and in agriculture—has accelerated the evolution of resistant bacterial strains. The World Health Organization estimates that antimicrobial resistance directly causes 1.27 million deaths annually and contributes to nearly 5 million additional deaths worldwide. Common infections that were once easily treatable, such as urinary tract infections and pneumonia, are increasingly difficult to manage. The development of new antibiotics has stagnated for decades because pharmaceutical companies find such drugs commercially unattractive: courses of treatment are short, prices are typically low, and resistance can render investments worthless within years of introduction. Addressing this crisis requires coordinated action across multiple fronts: stricter prescribing practices, improved infection control in healthcare settings, reduced antibiotic use in livestock production, public education about appropriate use, and renewed investment incentives for pharmaceutical research. Without such interventions, experts warn that we may be entering a "post-antibiotic era" in which routine medical procedures, from minor surgery to childbirth, become dangerously risky.`,
    questions: [
      { stem: 'How many deaths does antimicrobial resistance directly cause annually according to WHO?', choices: ['127,000', '1.27 million', '5 million', '12.7 million'], answer: '1', explanation: '本文「directly causes 1.27 million deaths annually」が直接の根拠。' },
      { stem: 'Why has new antibiotic development stagnated?', choices: ['Antibiotics are no longer needed', 'Government regulations are too strict', 'Pharmaceutical companies find them commercially unattractive', 'Scientific knowledge is insufficient'], answer: '2', explanation: '本文「pharmaceutical companies find such drugs commercially unattractive」が根拠。' },
      { stem: 'What characterizes a "post-antibiotic era"?', choices: ['No antibiotics will be needed', 'Routine medical procedures become dangerous due to untreatable infections', 'Antibiotics will be free for everyone', 'New diseases will emerge'], answer: '1', explanation: '本文「routine medical procedures...become dangerously risky」が根拠。' },
    ],
  },
};

// AI 接続が安定後、バックエンドが生成した問題を window.AUTO_GENERATED_BANKS に格納可能
// english-exam.js は SAMPLE_BANKS と AUTO_GENERATED_BANKS の両方から出題を試みる
window.AUTO_GENERATED_BANKS = window.AUTO_GENERATED_BANKS || {};
