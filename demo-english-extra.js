// 英語専門家Agent統合版: 英作文/長文読解/語彙
// 2026-04-22 追加

function buildDemoEnglishWriting(topic) {
  const t = String(topic || '');
  if (/要約|summary/i.test(t)) {
    return { title: '英語（英作文・要約） 練習問題', subtitle: '要約', problems: [
      { number: 1, difficulty: '基礎', question: '日本語で15〜25字に要約しなさい。\n\n"Reading every day is one of the simplest habits, yet its benefits are enormous."', answer: '毎日の読書は簡単だが、語彙・集中力・異文化理解を養う。（26字）', explanation: '主題＋根拠の骨。' },
      { number: 2, difficulty: '標準', question: '30語程度に要約。\n\n"Social media was designed to connect people, but evidence suggests they often have the opposite effect."', answer: 'Although social media aims to connect, research shows heavy use increases isolation. (13 words)', explanation: '譲歩 but を保持し具体→抽象。' },
      { number: 3, difficulty: '標準', question: '主張を英語15語以内で。\n\n"Cities face a dilemma. Cars improve mobility but worsen air quality."', answer: 'Cities must limit cars not to reduce mobility, but to protect air quality.', explanation: 'not ... but で論理圧縮。' },
      { number: 4, difficulty: '応用', question: '40〜60語で要約。\n\n"Anthropologists once argued language shapes thought; most linguists now agree the influence is modest."', answer: 'The hypothesis that language shapes thought was once widely held but is now generally rejected in its strong form. Recent research confirms only a mild influence.', explanation: 'once held / now rejected の論文定型。' },
      { number: 5, difficulty: '難関', question: '70〜90語で要約。(東京大・前期 2022 改題)\n\n"It is tempting to blame digital media for declines in reading. Yet long before smartphones, declines were already observable."', answer: 'It is tempting but too simple to blame digital media for declines in reading. Reading had already been declining before smartphones, and many young people still read extensively on screens. The real question is what forms of attention we now value.', explanation: '東大要約「通説→部分肯定→反証→問いの再定義」の4段構造。' }
    ], summary: '【要約】\n1. 論理構造を先に\n2. 具体→抽象\n3. 譲歩保持\n4. 語数±10%\n\n💡 APIキー設定で、毎回異なるオリジナル問題を自動生成できます。' };
  }
  if (/自由英作文|エッセイ|opinion|essay|自由/.test(t)) {
    return { title: '英語（英作文・自由英作文） 練習問題', subtitle: '自由英作文', problems: [
      { number: 1, difficulty: '基礎', question: '30〜40語で答えなさい。\n\n"Which do you prefer, paper books or e-books?"', answer: 'I prefer paper books because they help me concentrate. I am less tempted to check my phone, so I can focus on the story. (34 words)', explanation: '主張→理由→具体例。' },
      { number: 2, difficulty: '標準', question: '60〜80語で立場を明示。\n\n"High school students should not be allowed to have part-time jobs."', answer: 'I disagree with banning part-time jobs. First, working teaches skills no classroom can provide. Second, many students use income to support studies. Schools should set reasonable limits. (42 words)', explanation: 'First/Second/再主張の4段。' },
      { number: 3, difficulty: '標準', question: '反対の立場で80〜100語。\n\n"University admissions should rely entirely on a single national test."', answer: 'I strongly disagree with relying on a single test. First, one test cannot capture creativity, teamwork, perseverance. Second, a single test magnifies luck. A fairer system would combine the test with school records, interviews, and essays. (51 words)', explanation: '反論型構造。' },
      { number: 4, difficulty: '応用', question: '100〜120語で論述。具体例必須。\n\n"Should governments prioritize economic growth or environmental protection?"', answer: 'Governments should prioritize the environment. An economy depends on a habitable planet. Consider rivers poisoned by industry; the short-term profit was dwarfed by the public cost. Long-term environmental damage is a transfer of cost to people who cannot vote today. (66 words)', explanation: '主張→根拠→具体例→倫理的前提。' },
      { number: 5, difficulty: '難関', question: '120〜150語で論述しなさい。(慶應・法 2021 改題)\n\n"To what extent should freedom of speech be limited to protect people from harm?"', answer: 'Freedom of speech should be protected as fully as possible, but cannot be absolute. The classic principle, attributed to Mill, is that speech may be restricted only when it causes direct harm. Shouting "fire" in a theater is the obvious example. However, we should be cautious about restrictions based on offense or political opinion. The test is not whether speech is unpleasant, but whether it produces concrete serious harm. (99 words)', explanation: '5段構造: 抽象原理→権威引用→具体例→警告→判定基準。' }
    ], summary: '【自由英作文】\n1. 主張→理由→具体例→再主張\n2. 立場を明確に\n3. 具体例必須\n\n💡 APIキー設定で、毎回異なるオリジナル問題を自動生成できます。' };
  }
  return { title: '英語（英作文・和文英訳） 練習問題', subtitle: '和文英訳', problems: [
    { number: 1, difficulty: '基礎', question: '英訳しなさい。\n\n「私は昨日、友達と一緒に映画を見に行きました。」', answer: 'I went to see a movie with my friends yesterday.', explanation: '過去形 went。「友達」は複数 my friends。' },
    { number: 2, difficulty: '標準', question: '形式主語 It を用いて英訳。\n\n「高校生にとって、毎日英語に触れることは、長期的には何よりも重要だ。」', answer: 'For high school students, it is more important than anything else, in the long run, to be exposed to English every day.', explanation: 'be exposed to が自然。touch English は不可。' },
    { number: 3, difficulty: '標準', question: '現在完了と関係代名詞を用いて英訳。\n\n「彼は10年間この会社で働いており、今では誰もが尊敬する技術者となっている。」', answer: 'He has worked for this company for ten years and has become an engineer whom everyone respects.', explanation: 'have worked for（継続）＋目的格関係詞 whom。' },
    { number: 4, difficulty: '応用', question: '仮定法で英訳。\n\n「もし私があの時、彼の助言に耳を傾けていたなら、今ごろはもう少しまともな人間になっていたかもしれない。」', answer: 'If I had listened to his advice back then, I might have become a somewhat more decent person by now.', explanation: '混合仮定法（過去の仮定、現在への影響）。' },
    { number: 5, difficulty: '難関', question: '英訳しなさい。(京都大・前期 2018 改題)\n\n「どれほど理性に自信を持っている人であっても、自分の判断の多くが無意識のうちに感情や偏見に左右されているという事実から、完全に自由でいることはできない。」', answer: 'No matter how confident one may be in one\'s own reason, no one can be entirely free from the fact that many of one\'s judgments are, often without one\'s awareness, shaped by emotion and prejudice.', explanation: 'No matter how の譲歩倒置。be shaped by。' }
  ], summary: '【和文英訳】\n1. 主語を必ず補う\n2. 時制を正確に\n3. 自然なコロケーション\n4. 仮定法・倒置で格調up\n\n💡 APIキー設定で、毎回異なるオリジナル問題を自動生成できます。' };
}

function buildDemoEnglishReading(topic) {
  const t = String(topic || '');
  if (/整序|並べ替え|word order/i.test(t)) {
    return { title: '英語（長文読解・語句整序） 練習問題', subtitle: '語句整序', problems: [
      { number: 1, difficulty: '基礎', question: '並べ替えなさい。\n\n[ a / book / this / very / is / interesting ]', answer: 'This is a very interesting book.', explanation: '「冠詞→副詞→形容詞→名詞」の順。' },
      { number: 2, difficulty: '標準', question: '並べ替えなさい。\n\n「彼は私が今までに会った中で最も親切な人の一人だ。」\n[ he / the / is / kindest / people / one / I / of / ever / have / met ]', answer: 'He is one of the kindest people I have ever met.', explanation: 'one of the + 最上級 + 複数名詞 + (that) I have ever + PP。' },
      { number: 3, difficulty: '標準', question: '並べ替えなさい。不要語1つ。\n\n「この問題は難しすぎて、私には答えられなかった。」\n[ this / so / was / that / problem / difficult / too / could / solve / not / I / it ]', answer: 'This problem was so difficult that I could not solve it. ／ 不要: too', explanation: 'so ... that と too ... to は両立しない。' },
      { number: 4, difficulty: '応用', question: '並べ替えなさい。\n\n「こんなに美しい朝焼けを見たのは生まれて初めてだった。」\n[ never / life / my / beautiful / a / such / sunrise / had / seen / I / in / before ]', answer: 'Never in my life had I seen such a beautiful sunrise before.', explanation: 'Never 文頭 → 倒置 had I。' },
      { number: 5, difficulty: '難関', question: '並べ替えなさい。不要語1つ。(早稲田・国際教養 2019 改題)\n\n「人間は、理性に従って生きているつもりでも、どれほど感情に動かされているかを、ほとんど意識していない。」\n[ little / aware / of / how / much / are / humans / they / actually / are / moved / by / even / while / they / think / reason / live / by / they ]', answer: 'Humans are little aware of how much they are actually moved by emotion, even while they think they live by reason.', explanation: 'be little aware of の後は間接疑問。' }
    ], summary: '【語句整序】\n1. SV で骨格\n2. 定型構文認識\n3. 倒置トリガー\n\n💡 APIキー設定で、毎回異なるオリジナル問題を自動生成できます。' };
  }
  if (/内容一致|内容真偽|選択/i.test(t)) {
    return { title: '英語（長文読解・内容一致） 練習問題', subtitle: '内容一致', problems: [
      { number: 1, difficulty: '基礎', question: '内容に一致するものを選びなさい。\n\n"Many assume creativity is a gift. Research tells a different story. Creativity is less a talent than a set of habits."\n\n(a) Creativity is innate.\n(b) Creativity is primarily habits that most can develop.\n(c) Creativity cannot be studied.\n(d) Only patient people are creative.', answer: '(b)', explanation: 'less ... than ... で核心を提示。' },
      { number: 2, difficulty: '標準', question: '本文の内容と一致するものを選びなさい。\n\n"Sleep was considered passive. Modern research has overturned this view."\n\n(a) Sleep is passive.\n(b) The brain does little.\n(c) Sleep plays an active role in learning.\n(d) Closing a textbook ends learning.', answer: '(c)', explanation: 'overturned this view が転換点。' },
      { number: 3, difficulty: '標準', question: '主張と一致しないものを選びなさい。\n\n"Reading fiction has been dismissed as escapism. Yet studies suggest readers develop understanding of others\' minds."\n\n(a) Fiction has been criticized.\n(b) Studies indicate fiction sharpens understanding.\n(c) Theory of mind involves inferring thoughts.\n(d) Fiction is primarily escapism.', answer: '(d)', explanation: 'Yet で反転。最終立場は「単なる逃避ではない」。' },
      { number: 4, difficulty: '応用', question: '一致するものを2つ選びなさい。\n\n"Globalization has brought benefits. But it deepened inequalities. Factory labour has lifted millions out of poverty, yet at the cost of long hours."\n\n(a) Both benefits and unequal outcomes.\n(b) Skilled workers uniformly lost.\n(c) Factory work reduced poverty but raised concerns.\n(d) Life-saving tech is negative.', answer: '(a) と (c)', explanation: '(a) 全体要旨、(c) 「yet at the cost」と一致。' },
      { number: 5, difficulty: '難関', question: '筆者の主張に合致するものを選びなさい。(慶應・経済 2022 改題)\n\n"Whether the coming decades are remembered as triumph or betrayal will depend less on technology than on the choices societies make."\n\n(a) AI will inevitably cause unemployment.\n(b) Past patterns guarantee work will expand.\n(c) The outcome depends primarily on policy choices.\n(d) Historical parallels are irrelevant.', answer: '(c)', explanation: 'less A than B の B に核心。' }
    ], summary: '【内容一致】\n1. 逆接語の前後で反転\n2. 極端な語は誤答の定番\n3. 最終段落に筆者の総合判断\n\n💡 APIキー設定で、毎回異なるオリジナル長文を自動生成できます。' };
  }
  return { title: '英語（長文読解） 練習問題', subtitle: 'パラグラフリーディング', problems: [
    { number: 1, difficulty: '基礎', question: '筆者の主張を40字以内で述べなさい。\n\n"Reading books is one of the most valuable habits. It expands vocabulary, enhances thinking, and opens a window onto cultures."', answer: '読書は語彙・批判的思考力・異文化理解を養う最も価値ある習慣である。（34字）', explanation: '第1文トピックセンテンス。' },
    { number: 2, difficulty: '標準', question: '空所の接続詞を選びなさい。\n\n"The experiment was a success. ( ), the results cannot be generalized."\n(a) Therefore (b) However (c) Moreover (d) Similarly', answer: '(b) However', explanation: '逆接関係。' },
    { number: 3, difficulty: '標準', question: '"this" が指す内容を日本語で。\n\n"Students cram the night before exams. However, this is not effective."', answer: '試験前夜の詰め込み学習。', explanation: '指示語 this は行為全体を指す。' },
    { number: 4, difficulty: '応用', question: '主旨を選びなさい。\n\n"AI is transforming lives. The question is not whether to adopt AI, but how—on what terms, with what safeguards."\n(a) Safe.\n(b) Banned.\n(c) Both benefits and risks; how to adopt responsibly.\n(d) More jobs.', answer: '(c)', explanation: 'not A but B 構文の B が核心。' },
    { number: 5, difficulty: '難関', question: '論点を60〜80字でまとめなさい。(東京大・前期 2023 改題)\n\n"Urban pollution is treated as technical. Nevertheless, our cities were designed around assumptions now unsustainable. Any credible response must operate on technological and structural levels."', answer: '都市公害は技術的対策だけでは解決できず、都市のあり方といった構造的な改革なしには根本的な対応にならないこと。（55字）', explanation: '3段構成: 通説→限界→構造改革。' }
  ], summary: '【パラグラフリーディング】\n1. トピックセンテンス\n2. 接続詞で論理\n3. 指示語\n4. 対比構造\n5. 最終段落に結論\n\n💡 APIキー設定で、毎回異なるオリジナル長文を自動生成できます。' };
}

function buildDemoEnglishVocab(topic) {
  const t = String(topic || '');
  if (/イディオム|熟語|慣用|idiom|phrasal/i.test(t)) {
    return { title: '英語（語彙・イディオム） 練習問題', subtitle: 'イディオム', problems: [
      { number: 1, difficulty: '基礎', question: '意味を答えなさい。\n\n(1) break the ice (2) hit the books (3) a piece of cake', answer: '(1) 緊張をほぐす (2) 一生懸命勉強する (3) 簡単なこと', explanation: 'break the ice は氷（緊張）を割る比喩。' },
      { number: 2, difficulty: '標準', question: '最も適切なイディオムを選びなさい。\n\n"The project was on the verge of collapse, but the team managed to ( )."\n(a) pull through (b) put off (c) give in (d) turn down', answer: '(a) pull through', explanation: 'pull through = 困難を乗り切る。' },
      { number: 3, difficulty: '標準', question: '同義1語を答えなさい。\n\n(1) call off (2) figure out (3) put up with', answer: '(1) cancel (2) understand (3) tolerate', explanation: '句動詞は1語動詞に言い換え可。' },
      { number: 4, difficulty: '応用', question: '下線部の意味を推測しなさい。\n\n"Most analysts suspect the CEO will eventually throw in the towel."', answer: 'throw in the towel = あきらめる、降参する。', explanation: 'ボクシング由来の比喩。' },
      { number: 5, difficulty: '難関', question: '下線部の意味を含めて和訳しなさい。(早稲田・政経 2017 改題)\n\n"The minister\'s denial was an attempt to paper over the cracks, impossible to conceal from anyone who read between the lines."', answer: 'paper over the cracks = ごまかす。read between the lines = 真意を察する。', explanation: '政治報道で頻用される批判的イディオム。' }
    ], summary: '【イディオム】\n1. 定型比喩表現\n2. 由来を知ると記憶が深まる\n3. 句動詞は1語動詞に言い換え可\n\n💡 APIキー設定で、毎回異なるオリジナル問題を自動生成できます。' };
  }
  if (/派生|接頭辞|接尾辞|prefix|suffix/i.test(t)) {
    return { title: '英語（語彙・派生語） 練習問題', subtitle: '派生語', problems: [
      { number: 1, difficulty: '基礎', question: '名詞形と形容詞形を作りなさい。\n\n(1) create (2) decide', answer: '(1) creation, creative (2) decision, decisive', explanation: '-tion=名詞化、-ive=形容詞化。' },
      { number: 2, difficulty: '標準', question: '派生形を入れなさい。\n\n(1) Her ( ) to the plan surprised us. (oppose)\n(2) He gave a ( ) speech. (memory)\n(3) The ( ) of the law. (effective)', answer: '(1) opposition (2) memorable (3) effectiveness', explanation: '-tion, -able, -ness の典型的接尾辞。' },
      { number: 3, difficulty: '標準', question: '接辞で分解しなさい。\n\n(1) incomprehensible (2) unemployment', answer: '(1) in-(否定)+com-+prehend+-ible = 理解できない (2) un-+employ+-ment = 失業', explanation: '接辞分析で7-8割の意味を推測可能。' },
      { number: 4, difficulty: '応用', question: '反義語を接頭辞で作りなさい。\n\n(1) possible (2) literate (3) regular (4) moral (5) logical', answer: '(1) impossible (2) illiterate (3) irregular (4) immoral (5) illogical', explanation: '否定接頭辞 in- は後続音で変化。' },
      { number: 5, difficulty: '難関', question: '派生語を補いなさい。(東京大・前期 2020 改題)\n\n(1) The treaty has proved ( transcend ) of its purpose.\n(2) morally ( fault ) is a moral error.\n(3) turns out to be ( side ).', answer: '(1) transcendent (2) infallible (3) one-sided', explanation: '語根+接辞分析。' }
    ], summary: '【派生語】\n1. 接頭辞 un-/in-/im-/dis-\n2. 接尾辞(名詞) -tion/-ment/-ness\n3. 接尾辞(形容詞) -ive/-able/-ful\n4. 語根を知ると7割推測可\n\n💡 APIキー設定で、毎回異なるオリジナル問題を自動生成できます。' };
  }
  if (/同義|反義|類義|対義|synonym|antonym/i.test(t)) {
    return { title: '英語（語彙・同義反義語） 練習問題', subtitle: '同義反義', problems: [
      { number: 1, difficulty: '基礎', question: '類義語を選びなさい。\n\n"significant"\n(a) trivial (b) important (c) ancient (d) visible', answer: '(b) important', explanation: '類義: crucial, vital。対義: trivial。' },
      { number: 2, difficulty: '標準', question: '反義語を選びなさい。\n\n"diligent"\n(a) hardworking (b) honest (c) lazy (d) clever', answer: '(c) lazy', explanation: 'diligent = 勤勉な。' },
      { number: 3, difficulty: '標準', question: '仲間はずれを選びなさい。\n\n(a) obtain (b) acquire (c) discard (d) gain', answer: '(c) discard', explanation: '他は「獲得」の類義、discard は「捨てる」。' },
      { number: 4, difficulty: '応用', question: '最も近い語を選びなさい。\n\n"ambiguous"\n(a) straightforward (b) vague (c) precise (d) remarkable', answer: '(b) vague', explanation: 'ambiguous = 曖昧。ambi-=両方／二重。' },
      { number: 5, difficulty: '難関', question: '類義語と対義語を1語ずつ。(慶應・文 2018 改題)\n\n"The speaker\'s laconic reply suggested lost interest."', answer: '類義: concise／対義: verbose', explanation: 'laconic = 簡潔（ラコニア＝スパルタ由来）。' }
    ], summary: '【同義反義】\n1. 類義語は束で覚える\n2. 反義語は否定接頭辞\n3. 英検1級は語源から連想\n\n💡 APIキー設定で、毎回異なるオリジナル問題を自動生成できます。' };
  }
  return { title: '英語（語彙） 練習問題', subtitle: '英検準1級〜1級', problems: [
    { number: 1, difficulty: '基礎', question: '次の英単語の意味を答えなさい。\n\n(1) abandon (2) acquire (3) beneficial (4) complicated (5) demonstrate', answer: '(1) 見捨てる (2) 獲得する (3) 有益な (4) 複雑な (5) 実証する', explanation: '英検2級〜準1級の基礎単語。' },
    { number: 2, difficulty: '標準', question: '最も適切な動詞を選びなさい。\n\n"The teacher tried to ( ) the concept with a simple example."\n(a) illustrate (b) illuminate (c) eliminate (d) imitate', answer: '(a) illustrate', explanation: 'illustrate = 例で説明する。' },
    { number: 3, difficulty: '標準', question: '英語で説明し日本語訳を添えなさい。\n\n(1) inevitable (2) comprehensive (3) contradict', answer: '(1) impossible to avoid／避けられない (2) covering all aspects／包括的な (3) to state the opposite／矛盾する', explanation: 'inevitable は in-（否定）+ evitable（避けうる）。' },
    { number: 4, difficulty: '応用', question: '文脈に最も合う語を選びなさい。\n\n"The committee showed a stubborn ( ) to acknowledge any flaw."\n(a) reluctance (b) enthusiasm (c) obedience (d) sympathy', answer: '(a) reluctance', explanation: 'reluctance = 気が進まないこと。' },
    { number: 5, difficulty: '難関', question: '下線部の意味と類義語を挙げなさい。(東京大・前期 2019 改題)\n\n"The scientist\'s theory, once dismissed as preposterous, has been vindicated and is now considered plausible."', answer: 'preposterous = ばかげた（類義: absurd, ridiculous）／plausible = もっともらしい（類義: credible, reasonable）', explanation: 'preposterous はラテン語 prae（前）+ post（後）由来「前後逆さま」。' }
  ], summary: '【英検準1級〜1級】\n1. 語源で意味推測\n2. 類義語は束で覚える\n3. 英検1級語は長文読解頻出\n\n💡 APIキー設定で、毎回異なるオリジナル問題を自動生成できます。' };
}
