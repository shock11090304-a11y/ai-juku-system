// ==========================================================================
// 🎓 英語試験対策スタジオ — 4試験完全対応
// TOEFL iBT / TOEIC L&R / IELTS Academic / 英検
// ==========================================================================

const API_URL = 'https://api.anthropic.com/v1/messages';
const MODEL_DEFAULT = 'claude-sonnet-4-6';
const MODEL_HEAVY = 'claude-opus-4-7';  // スコア予測・採点はopus

// ==========================================================================
// 試験定義 (公式形式に準拠)
// ==========================================================================
const EXAMS = {
  toefl: {
    id: 'toefl',
    name: 'TOEFL iBT',
    flag: '🇺🇸',
    color: '#1e40af',
    scoreMin: 0, scoreMax: 120, scoreUnit: '点',
    sections: [
      // Reading
      { key: 'r_passage1', name: 'Reading Passage 1', icon: '📖', timeMin: 18, qCount: 10, scoreMax: 15, desc: '学術文 (生物/歴史等) 700語×10問: 詳細・推論・要約' },
      { key: 'r_passage2', name: 'Reading Passage 2', icon: '📖', timeMin: 18, qCount: 10, scoreMax: 15, desc: '学術文 別ジャンル 10問: 語彙・指示語・修辞目的' },
      // Listening
      { key: 'l_conv1',    name: 'Listening Conversation 1', icon: '💬', timeMin: 5, qCount: 5, scoreMax: 7,  desc: '学生×職員/教授の3-5分会話・5問' },
      { key: 'l_lect1',    name: 'Listening Lecture 1',      icon: '🎓', timeMin: 8, qCount: 6, scoreMax: 8,  desc: '講義3-5分 (専門分野)・6問: 要旨/詳細/態度' },
      { key: 'l_lect2',    name: 'Listening Lecture 2',      icon: '🎓', timeMin: 8, qCount: 6, scoreMax: 8,  desc: '講義3-5分 別ジャンル・6問: 構成把握/再聴問' },
      // Speaking
      { key: 's_task1',    name: 'Speaking Task 1 (Independent)', icon: '🎙', timeMin: 1, qCount: 1, scoreMax: 4, desc: '個人意見 15秒準備+45秒回答 (テンプレ運用が鍵)' },
      { key: 's_task2',    name: 'Speaking Task 2 (Integrated R+L+S)', icon: '🎙', timeMin: 4, qCount: 1, scoreMax: 4, desc: '読解+講義要約 30秒準備+60秒回答 (大学キャンパス系)' },
      { key: 's_task3',    name: 'Speaking Task 3 (Integrated R+L+S 学術)', icon: '🎙', timeMin: 4, qCount: 1, scoreMax: 4, desc: '読解+講義要約 30秒準備+60秒回答 (学術概念系)' },
      { key: 's_task4',    name: 'Speaking Task 4 (Integrated L+S)', icon: '🎙', timeMin: 4, qCount: 1, scoreMax: 4, desc: '講義のみ要約 20秒準備+60秒回答' },
      // Writing
      { key: 'w_integrated', name: 'Writing Integrated (R+L+W)', icon: '✍️', timeMin: 20, qCount: 1, scoreMax: 5, desc: '読解+講義の対比 150-225語 20分' },
      { key: 'w_academic_disc', name: 'Writing Academic Discussion', icon: '✍️', timeMin: 10, qCount: 1, scoreMax: 5, desc: '討論への参加 100語以上 10分 (新形式 2023〜)' },
    ],
    topics: ['Biology', 'Geology', 'History', 'Psychology', 'Astronomy', 'Linguistics', 'Art History', 'Environmental Science'],
  },
  toeic: {
    id: 'toeic',
    name: 'TOEIC L&R',
    flag: '💼',
    color: '#ea580c',
    scoreMin: 10, scoreMax: 990, scoreUnit: '点',
    sections: [
      { key: 'l_part1', name: 'Listening Part 1', icon: '🖼', timeMin: 4,  qCount: 6,  scoreMax: 30,  desc: '写真描写問題 (4択)' },
      { key: 'l_part2', name: 'Listening Part 2', icon: '💬', timeMin: 9,  qCount: 25, scoreMax: 125, desc: '応答問題 (3択)' },
      { key: 'l_part3', name: 'Listening Part 3', icon: '👥', timeMin: 17, qCount: 39, scoreMax: 195, desc: '会話問題 (4択・3問1セット×13)' },
      { key: 'l_part4', name: 'Listening Part 4', icon: '📢', timeMin: 15, qCount: 30, scoreMax: 150, desc: '説明文問題 (4択・3問1セット×10)' },
      { key: 'r_part5', name: 'Reading Part 5',   icon: '📝', timeMin: 10, qCount: 30, scoreMax: 150, desc: '短文穴埋め (語彙・文法 4択)' },
      { key: 'r_part6', name: 'Reading Part 6',   icon: '📄', timeMin: 10, qCount: 16, scoreMax: 80,  desc: '長文穴埋め (4択・4問1セット×4)' },
      { key: 'r_part7_single', name: 'Reading Part 7 シングル', icon: '📚', timeMin: 25, qCount: 29, scoreMax: 145, desc: '1文書 読解 (29問)' },
      { key: 'r_part7_multi',  name: 'Reading Part 7 マルチ',   icon: '📚', timeMin: 30, qCount: 25, scoreMax: 125, desc: '2-3文書クロス読解 (5セット×5問)' },
    ],
    topics: ['Business meetings', 'Office communication', 'Travel arrangements', 'Customer service', 'Marketing', 'HR/Hiring', 'Logistics', 'Finance reports'],
  },
  ielts: {
    id: 'ielts',
    name: 'IELTS Academic',
    flag: '🇬🇧',
    color: '#7c3aed',
    scoreMin: 0, scoreMax: 9.0, scoreUnit: 'バンド',
    sections: [
      // Listening 4 sections
      { key: 'l_sec1', name: 'Listening Section 1 (社会的会話)', icon: '🎧', timeMin: 8,  qCount: 10, scoreMax: 9.0, desc: '日常的な2人の会話 (予約/手続き等)' },
      { key: 'l_sec2', name: 'Listening Section 2 (社会的モノローグ)', icon: '🎧', timeMin: 8,  qCount: 10, scoreMax: 9.0, desc: '1人による説明 (観光案内/施設紹介等)' },
      { key: 'l_sec3', name: 'Listening Section 3 (学術的会話)', icon: '🎧', timeMin: 8,  qCount: 10, scoreMax: 9.0, desc: '学生同士・指導教官との会話' },
      { key: 'l_sec4', name: 'Listening Section 4 (学術的講義)', icon: '🎧', timeMin: 8,  qCount: 10, scoreMax: 9.0, desc: '大学講義モノローグ (アカデミック)' },
      // Reading 3 passages
      { key: 'r_p1', name: 'Reading Passage 1', icon: '📖', timeMin: 20, qCount: 13, scoreMax: 9.0, desc: '一般向け学術文 13問: T/F/NG・穴埋め' },
      { key: 'r_p2', name: 'Reading Passage 2', icon: '📖', timeMin: 20, qCount: 13, scoreMax: 9.0, desc: '専門学術文 13問: 見出し選択・要約完成' },
      { key: 'r_p3', name: 'Reading Passage 3', icon: '📖', timeMin: 20, qCount: 14, scoreMax: 9.0, desc: '高難度学術文 14問: 推論・著者の見解' },
      // Writing
      { key: 'w_task1', name: 'Writing Task 1 (グラフ/図描写)', icon: '📊', timeMin: 20, qCount: 1, scoreMax: 9.0, desc: 'グラフ/表/図/プロセスを150語で描写' },
      { key: 'w_task2', name: 'Writing Task 2 (エッセイ)', icon: '✍️', timeMin: 40, qCount: 1, scoreMax: 9.0, desc: '社会的論題に250語で意見論述 (Task1の2倍配点)' },
      // Speaking
      { key: 's_p1', name: 'Speaking Part 1 (自己紹介Q&A)', icon: '🎙', timeMin: 5, qCount: 12, scoreMax: 9.0, desc: '個人的トピック (家族/仕事/趣味) 4-5分' },
      { key: 's_p2', name: 'Speaking Part 2 (2分スピーチ)', icon: '🎙', timeMin: 4, qCount: 1,  scoreMax: 9.0, desc: 'カードのトピックを1分準備→2分独白' },
      { key: 's_p3', name: 'Speaking Part 3 (ディスカッション)', icon: '🎙', timeMin: 5, qCount: 6,  scoreMax: 9.0, desc: 'Part2の話題を抽象化した議論 4-5分' },
    ],
    topics: ['Climate change', 'Urban planning', 'Education systems', 'Healthcare', 'Technology impact', 'Globalization', 'Social inequality', 'Cultural identity'],
  },
  eiken: {
    id: 'eiken',
    name: '英検',
    flag: '🇯🇵',
    color: '#dc2626',
    scoreMin: 0, scoreMax: 0, scoreUnit: '級',
    requiresGrade: true,
    grades: [
      { key: 'g1',  name: '1級',     cefr: 'C1',     target: '英字新聞・専門書・国連職員レベル' },
      { key: 'gp1', name: '準1級',   cefr: 'B2',     target: '海外留学・大学入試優遇・社会問題に意見' },
      { key: 'g2',  name: '2級',     cefr: 'B1',     target: '高校卒業・海外短期留学・実用英会話' },
      { key: 'gp2', name: '準2級',   cefr: 'A2-B1',  target: '高校在学中・大学入試・身近な英会話' },
      { key: 'g3',  name: '3級',     cefr: 'A2',     target: '中学卒業・短文/対話の理解' },
      { key: 'g4',  name: '4級',     cefr: 'A1',     target: '中学中級・基礎英文の理解' },
      { key: 'g5',  name: '5級',     cefr: 'A1',     target: '中学初級・あいさつ/簡単な質問' },
    ],
    // 級別の part 構成 (公式準拠 + 2024年新形式反映)
    sectionsByGrade: {
      g1: [
        { key: 'r_q1', name: 'Reading 大問1 (短文穴埋め・語彙)', icon: '📝', timeMin: 25, qCount: 25, scoreMax: 25, desc: '高度な語彙・熟語 (4択)。1級は語彙が最大の関門' },
        { key: 'r_q2', name: 'Reading 大問2 (長文穴埋め)',       icon: '📄', timeMin: 12, qCount: 6,  scoreMax: 6,  desc: '長文の論理展開を読み取り穴埋め' },
        { key: 'r_q3', name: 'Reading 大問3 (長文内容一致)',     icon: '📚', timeMin: 30, qCount: 10, scoreMax: 10, desc: '長文の主旨/詳細/推論' },
        { key: 'w_summary', name: 'Writing 要約 (新形式)',       icon: '📋', timeMin: 20, qCount: 1,  scoreMax: 16, desc: '90-110語の要約' },
        { key: 'w_essay',   name: 'Writing エッセイ',             icon: '✍️', timeMin: 35, qCount: 1,  scoreMax: 16, desc: '社会問題への意見 200-240語' },
        { key: 'l_part1', name: 'Listening Part 1 (会話)',       icon: '💬', timeMin: 10, qCount: 12, scoreMax: 12, desc: '会話を聞いて応答' },
        { key: 'l_part2', name: 'Listening Part 2 (パッセージ)', icon: '🎙', timeMin: 10, qCount: 12, scoreMax: 12, desc: '長めのパッセージ理解' },
        { key: 'l_part3', name: 'Listening Part 3 (Real-Life)',  icon: '🌐', timeMin: 5,  qCount: 5,  scoreMax: 5,  desc: 'アナウンス等の状況把握' },
        { key: 'l_part4', name: 'Listening Part 4 (インタビュー)', icon: '🎤', timeMin: 4,  qCount: 2,  scoreMax: 2,  desc: 'インタビュー2問 (1級のみ)' },
        { key: 's_q1',    name: '二次 自由会話',                  icon: '🗣', timeMin: 1,  qCount: 1,  scoreMax: 5,  desc: '冒頭の自由対話' },
        { key: 's_q2',    name: '二次 トピックスピーチ',          icon: '🗣', timeMin: 3,  qCount: 1,  scoreMax: 10, desc: '5トピックから1つ選び2分スピーチ' },
        { key: 's_q3',    name: '二次 Q&A (Q1-Q4)',               icon: '🗣', timeMin: 6,  qCount: 4,  scoreMax: 10, desc: 'スピーチに関する質問4つ' },
      ],
      gp1: [
        { key: 'r_q1', name: 'Reading 大問1 (短文穴埋め)',       icon: '📝', timeMin: 18, qCount: 18, scoreMax: 18, desc: '語彙・熟語の文脈穴埋め (4択)' },
        { key: 'r_q2', name: 'Reading 大問2 (長文穴埋め)',       icon: '📄', timeMin: 12, qCount: 6,  scoreMax: 6,  desc: '長文の論理展開を読み取り穴埋め' },
        { key: 'r_q3', name: 'Reading 大問3 (長文内容一致)',     icon: '📚', timeMin: 25, qCount: 7,  scoreMax: 7,  desc: '長文の主旨・詳細・推測' },
        { key: 'r_q4', name: 'Reading 大問4 (Eメール返信・新形式)', icon: '✉️', timeMin: 5, qCount: 1, scoreMax: 1, desc: 'Eメール内容に応じた質問回答' },
        { key: 'w_summary', name: 'Writing 要約 (新形式 2024〜)', icon: '📋', timeMin: 15, qCount: 1, scoreMax: 16, desc: 'パッセージを60-70語で要約' },
        { key: 'w_essay',   name: 'Writing エッセイ',             icon: '✍️', timeMin: 25, qCount: 1, scoreMax: 16, desc: '社会問題に対する意見 120-150語' },
        { key: 'l_part1', name: 'Listening Part 1 (会話)',       icon: '💬', timeMin: 10, qCount: 12, scoreMax: 12, desc: '会話を聞いて応答' },
        { key: 'l_part2', name: 'Listening Part 2 (パッセージ)', icon: '🎙', timeMin: 10, qCount: 12, scoreMax: 12, desc: '長めのパッセージ理解' },
        { key: 'l_part3', name: 'Listening Part 3 (Real-Life)',  icon: '🌐', timeMin: 5,  qCount: 5,  scoreMax: 5,  desc: 'アナウンス等の状況把握' },
        { key: 's_read',  name: '二次 パッセージ音読',            icon: '🗣', timeMin: 1, qCount: 1, scoreMax: 5,  desc: '示されたパッセージを音読' },
        { key: 's_q1',    name: '二次 Q1 (パッセージ理解)',       icon: '🗣', timeMin: 1, qCount: 1, scoreMax: 5,  desc: '読んだパッセージへの質問' },
        { key: 's_qa',    name: '二次 Q2-Q4 (即興回答)',          icon: '🗣', timeMin: 5, qCount: 3, scoreMax: 15, desc: 'トピックに対する即興回答' },
      ],
      g2: [
        { key: 'r_q1',  name: 'Reading 大問1 (短文穴埋め)',  icon: '📝', timeMin: 12, qCount: 17, scoreMax: 17, desc: '語彙・熟語・文法の穴埋め' },
        { key: 'r_q2',  name: 'Reading 大問2 (長文穴埋め)',  icon: '📄', timeMin: 12, qCount: 6,  scoreMax: 6,  desc: '長文の論理展開' },
        { key: 'r_q3a', name: 'Reading 大問3A (Eメール)',    icon: '✉️', timeMin: 8,  qCount: 3,  scoreMax: 3,  desc: 'Eメール本文の理解' },
        { key: 'r_q3b', name: 'Reading 大問3B (長文内容一致)', icon: '📚', timeMin: 18, qCount: 5, scoreMax: 5, desc: '長文の主旨・詳細' },
        { key: 'w_summary', name: 'Writing 要約 (新形式 2024〜)', icon: '📋', timeMin: 15, qCount: 1, scoreMax: 16, desc: 'パッセージ要約 45-55語' },
        { key: 'w_opinion', name: 'Writing 意見論述',         icon: '✍️', timeMin: 20, qCount: 1, scoreMax: 16, desc: 'TOPICへの意見 80-100語' },
        { key: 'l_part1', name: 'Listening Part 1 (会話)',    icon: '💬', timeMin: 12, qCount: 15, scoreMax: 15, desc: '会話の応答' },
        { key: 'l_part2', name: 'Listening Part 2 (パッセージ)', icon: '🎙', timeMin: 12, qCount: 15, scoreMax: 15, desc: '長めのパッセージ理解' },
        { key: 's_read',  name: '二次 パッセージ音読',         icon: '🗣', timeMin: 1, qCount: 1, scoreMax: 5,  desc: 'パッセージを音読' },
        { key: 's_q1',    name: '二次 Q1 (パッセージ理解)',    icon: '🗣', timeMin: 1, qCount: 1, scoreMax: 5,  desc: 'パッセージ内容への質問' },
        { key: 's_q2_3',  name: '二次 Q2-3 (イラスト)',         icon: '🗣', timeMin: 3, qCount: 2, scoreMax: 10, desc: 'イラスト描写・人物状況説明' },
        { key: 's_q4',    name: '二次 Q4 (社会問題)',           icon: '🗣', timeMin: 2, qCount: 1, scoreMax: 5,  desc: '社会的トピックへの意見' },
      ],
      gp2: [
        { key: 'r_q1',  name: 'Reading 大問1 (短文穴埋め)', icon: '📝', timeMin: 10, qCount: 15, scoreMax: 15, desc: '基本的な語彙・熟語・文法' },
        { key: 'r_q2',  name: 'Reading 大問2 (会話穴埋め)', icon: '💬', timeMin: 8,  qCount: 5,  scoreMax: 5,  desc: '会話の自然な流れを完成' },
        { key: 'r_q3a', name: 'Reading 大問3A (Eメール)',   icon: '✉️', timeMin: 8,  qCount: 3,  scoreMax: 3,  desc: 'Eメール本文の理解' },
        { key: 'r_q3b', name: 'Reading 大問3B (長文内容一致)', icon: '📚', timeMin: 15, qCount: 7, scoreMax: 7, desc: '長文の主旨・詳細' },
        { key: 'w_email',   name: 'Writing Eメール返信 (新形式 2024〜)', icon: '✉️', timeMin: 15, qCount: 1, scoreMax: 16, desc: 'Eメールへの返信 40-50語' },
        { key: 'w_opinion', name: 'Writing 意見論述',         icon: '✍️', timeMin: 15, qCount: 1, scoreMax: 16, desc: '質問への意見 50-60語' },
        { key: 'l_part1', name: 'Listening Part 1 (会話の応答)', icon: '💬', timeMin: 8,  qCount: 10, scoreMax: 10, desc: '会話の最後の発言を選ぶ' },
        { key: 'l_part2', name: 'Listening Part 2 (会話の質問)', icon: '👥', timeMin: 10, qCount: 10, scoreMax: 10, desc: '会話を聞いて質問に答える' },
        { key: 'l_part3', name: 'Listening Part 3 (パッセージ)', icon: '🎙', timeMin: 8, qCount: 10, scoreMax: 10, desc: '短いパッセージ理解' },
        { key: 's_read',  name: '二次 パッセージ音読',         icon: '🗣', timeMin: 1, qCount: 1, scoreMax: 5,  desc: 'パッセージを音読' },
        { key: 's_q1',    name: '二次 Q1 (パッセージ理解)',    icon: '🗣', timeMin: 1, qCount: 1, scoreMax: 5,  desc: 'パッセージ内容への質問' },
        { key: 's_q2_3',  name: '二次 Q2-3 (イラスト)',         icon: '🗣', timeMin: 2, qCount: 2, scoreMax: 10, desc: 'イラスト描写' },
        { key: 's_q4',    name: '二次 Q4 (個人的意見)',         icon: '🗣', timeMin: 2, qCount: 1, scoreMax: 5,  desc: '日常的トピックへの意見' },
      ],
      g3: [
        { key: 'r_q1',  name: 'Reading 大問1 (短文穴埋め)', icon: '📝', timeMin: 10, qCount: 15, scoreMax: 15, desc: '基本語彙・文法' },
        { key: 'r_q2',  name: 'Reading 大問2 (会話穴埋め)', icon: '💬', timeMin: 5,  qCount: 5,  scoreMax: 5,  desc: '会話の自然な流れ' },
        { key: 'r_q3a', name: 'Reading 大問3A (掲示物)',     icon: '📋', timeMin: 4,  qCount: 2,  scoreMax: 2,  desc: '掲示・案内文の読み取り' },
        { key: 'r_q3b', name: 'Reading 大問3B (Eメール)',    icon: '✉️', timeMin: 6,  qCount: 3,  scoreMax: 3,  desc: 'Eメールの内容理解' },
        { key: 'r_q3c', name: 'Reading 大問3C (長文)',       icon: '📚', timeMin: 10, qCount: 5,  scoreMax: 5,  desc: '物語・説明文の理解' },
        { key: 'w_email',   name: 'Writing Eメール返信 (新形式 2024〜)', icon: '✉️', timeMin: 15, qCount: 1, scoreMax: 16, desc: 'Eメール返信 15-25語' },
        { key: 'w_opinion', name: 'Writing 意見論述',         icon: '✍️', timeMin: 15, qCount: 1, scoreMax: 16, desc: '質問への意見 25-35語' },
        { key: 'l_part1', name: 'Listening Part 1 (会話の応答)', icon: '💬', timeMin: 6, qCount: 10, scoreMax: 10, desc: '会話最後の応答' },
        { key: 'l_part2', name: 'Listening Part 2 (会話の質問)', icon: '👥', timeMin: 8, qCount: 10, scoreMax: 10, desc: '会話への質問' },
        { key: 'l_part3', name: 'Listening Part 3 (パッセージ)', icon: '🎙', timeMin: 6, qCount: 10, scoreMax: 10, desc: '短いパッセージ' },
        { key: 's_read', name: '二次 パッセージ音読',         icon: '🗣', timeMin: 1, qCount: 1, scoreMax: 5,  desc: '短いパッセージ音読' },
        { key: 's_q1',   name: '二次 Q1 (パッセージ理解)',    icon: '🗣', timeMin: 1, qCount: 1, scoreMax: 5,  desc: 'パッセージへの質問' },
        { key: 's_q2',   name: '二次 Q2 (イラスト)',           icon: '🗣', timeMin: 2, qCount: 1, scoreMax: 5,  desc: 'イラストの状況説明' },
        { key: 's_q3_4', name: '二次 Q3-4 (個人的意見)',       icon: '🗣', timeMin: 2, qCount: 2, scoreMax: 10, desc: '日常質問への回答' },
      ],
      g4: [
        { key: 'r_q1', name: 'Reading 大問1 (短文穴埋め)', icon: '📝', timeMin: 8,  qCount: 15, scoreMax: 15, desc: '中学中級レベルの語彙・文法' },
        { key: 'r_q2', name: 'Reading 大問2 (会話穴埋め)', icon: '💬', timeMin: 5,  qCount: 5,  scoreMax: 5,  desc: '簡単な会話の流れ' },
        { key: 'r_q3', name: 'Reading 大問3 (並べ替え)',   icon: '🔀', timeMin: 5,  qCount: 5,  scoreMax: 5,  desc: '日本文に合う英文を完成' },
        { key: 'r_q4', name: 'Reading 大問4 (掲示+Eメール+長文)', icon: '📚', timeMin: 12, qCount: 7, scoreMax: 7, desc: '3種類の文章を読み取り' },
        { key: 'w_q',  name: 'Writing 質問への回答 (新形式 2024〜)', icon: '✍️', timeMin: 10, qCount: 1, scoreMax: 16, desc: '簡単な質問に英語で返信 15語以上' },
        { key: 'l_part1', name: 'Listening Part 1 (会話の応答)', icon: '💬', timeMin: 5, qCount: 10, scoreMax: 10, desc: '会話最後の応答' },
        { key: 'l_part2', name: 'Listening Part 2 (会話の質問)', icon: '👥', timeMin: 7, qCount: 10, scoreMax: 10, desc: '会話への質問' },
        { key: 'l_part3', name: 'Listening Part 3 (パッセージ)', icon: '🎙', timeMin: 5, qCount: 10, scoreMax: 10, desc: '短い説明文' },
        // 4級は二次なし
      ],
      g5: [
        { key: 'r_q1', name: 'Reading 大問1 (短文穴埋め)', icon: '📝', timeMin: 8,  qCount: 15, scoreMax: 15, desc: '中学初級語彙・基本文法' },
        { key: 'r_q2', name: 'Reading 大問2 (会話穴埋め)', icon: '💬', timeMin: 5,  qCount: 5,  scoreMax: 5,  desc: 'あいさつ・簡単な質問の応答' },
        { key: 'r_q3', name: 'Reading 大問3 (並べ替え)',   icon: '🔀', timeMin: 5,  qCount: 5,  scoreMax: 5,  desc: '日本文に合う英文を完成' },
        { key: 'r_q4', name: 'Reading 大問4 (長文)',       icon: '📚', timeMin: 8,  qCount: 5,  scoreMax: 5,  desc: '簡単な掲示・Eメール・物語' },
        { key: 'w_q',  name: 'Writing Yes/Noと理由 (新形式 2024〜)', icon: '✍️', timeMin: 10, qCount: 1, scoreMax: 16, desc: '質問にYes/Noと理由を1-2文で' },
        { key: 'l_part1', name: 'Listening Part 1 (会話の応答)', icon: '💬', timeMin: 5, qCount: 10, scoreMax: 10, desc: '簡単な応答選択' },
        { key: 'l_part2', name: 'Listening Part 2 (会話の質問)', icon: '👥', timeMin: 4, qCount: 5,  scoreMax: 5,  desc: '簡単な会話への質問' },
        { key: 'l_part3', name: 'Listening Part 3 (イラスト)',   icon: '🖼', timeMin: 4, qCount: 5,  scoreMax: 5,  desc: 'イラストに合う英文選択' },
        // 5級は二次なし
      ],
    },
    topics: ['Daily life', 'School', 'Travel', 'Environment', 'Technology', 'Health', 'Culture', 'Future plans'],
  },
};

// 英検: 級から sections を取得 (sectionsByGrade を sections として返す)
function getEikenSections(gradeKey) {
  return EXAMS.eiken.sectionsByGrade[gradeKey] || EXAMS.eiken.sectionsByGrade.gp1;
}

// ==========================================================================
// CEFR ベース スコア換算 (4試験を相互変換)
// ==========================================================================
const CEFR_LEVELS = [
  { cefr: 'C2', toefl: [110, 120], toeic: [945, 990], ielts: [8.5, 9.0], eiken: '1級' },
  { cefr: 'C1', toefl: [95, 109],  toeic: [785, 944], ielts: [7.0, 8.0], eiken: '準1級' },
  { cefr: 'B2', toefl: [72, 94],   toeic: [605, 784], ielts: [5.5, 6.5], eiken: '2級' },
  { cefr: 'B1', toefl: [42, 71],   toeic: [405, 604], ielts: [4.0, 5.0], eiken: '準2級' },
  { cefr: 'A2', toefl: [25, 41],   toeic: [225, 404], ielts: [3.0, 3.5], eiken: '3級' },
  { cefr: 'A1', toefl: [0, 24],    toeic: [10, 224],  ielts: [1.0, 2.5], eiken: '4-5級' },
];

function scoreToCefr(examId, score) {
  for (const lv of CEFR_LEVELS) {
    const range = lv[examId];
    if (!range) continue;
    if (typeof range === 'string') {
      if (score === range) return lv.cefr;
    } else if (score >= range[0] && score <= range[1]) {
      return lv.cefr;
    }
  }
  return 'A1';
}

function cefrToAllScores(cefr) {
  const lv = CEFR_LEVELS.find(l => l.cefr === cefr) || CEFR_LEVELS[CEFR_LEVELS.length - 1];
  return {
    toefl: lv.toefl[0] + '-' + lv.toefl[1],
    toeic: lv.toeic[0] + '-' + lv.toeic[1],
    ielts: lv.ielts[0] + '-' + lv.ielts[1],
    eiken: lv.eiken,
    cefr: lv.cefr,
  };
}

// ==========================================================================
// State
// ==========================================================================
const state = {
  examId: null,
  sectionKey: null,
  questions: [],          // 現在の問題セット
  userAnswers: {},        // {qId: answer}
  startedAt: null,
  timerInterval: null,
  result: null,
};

// ==========================================================================
// API Key 管理 (既存 app.js と同じ規約)
// ==========================================================================
function getApiKey() {
  return localStorage.getItem('ai_juku_api_key') || '';
}
function isLiveMode() {
  // 生徒ログイン済み (backend proxy 経由) or 管理者APIキーあり (直接呼び出し)
  return !!(localStorage.getItem('ai_juku_session_token')
    || localStorage.getItem('ai_juku_admin_token')
    || getApiKey());
}
function updateModeBadge() {
  // 生徒可視のため常に「🟢 AI接続中」固定。デモ表記は塾の信頼性に影響するため厳禁。
  // 内部の isLiveMode() は AI 呼び出し時のフォールバック判定に引き続き使用。
  const el = document.getElementById('modeIndicator');
  if (!el) return;
  el.textContent = '🟢 AI接続中';
  el.className = 'ee-mode-badge live';
  el.title = isLiveMode() ? 'AI機能 稼働中' : 'AI機能 稼働中 (準備中)';
}

// ==========================================================================
// Claude API 呼び出し (JSON出力強制)
// ==========================================================================
async function callClaudeJson({ system, user, model = MODEL_DEFAULT, maxTokens = 4000 }) {
  // 1) 生徒ログイン済みなら backend proxy 経由 (生徒ブラウザにキー不要・本番Live)
  // 2) フォールバック: localStorage に APIキーがあれば従来の直接呼び出し (CEO/管理者用)
  const sessionToken = localStorage.getItem('ai_juku_session_token')
    || localStorage.getItem('ai_juku_admin_token');
  const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
    ? 'http://localhost:8000' : window.location.origin;

  let data;
  if (sessionToken) {
    // Backend proxy 経由 (Anthropic key はサーバー側に存在)
    const res = await fetch(`${backend}/api/ai/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + sessionToken,
      },
      body: JSON.stringify({
        model,
        max_tokens: maxTokens,
        system,
        messages: [{ role: 'user', content: user }],
      }),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`Backend AI ${res.status}: ${t.slice(0, 200)}`);
    }
    data = await res.json();
  } else {
    // 直接呼び出し (ログインしていない/プレビュー用)
    const apiKey = getApiKey();
    if (!apiKey) throw new Error('NO_AUTH');
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model,
        max_tokens: maxTokens,
        system,
        messages: [{ role: 'user', content: user }],
      }),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`Claude API ${res.status}: ${t.slice(0, 200)}`);
    }
    data = await res.json();
  }

  let text = (data.content?.[0]?.text || '').trim();
  // コードブロック除去
  if (text.startsWith('```')) {
    text = text.replace(/^```(?:json)?\s*/, '').replace(/```\s*$/, '').trim();
  }
  return JSON.parse(text);
}

// ==========================================================================
// 試験選択画面
// ==========================================================================
function bindExamCards() {
  document.querySelectorAll('.exam-card').forEach(card => {
    card.addEventListener('click', () => {
      const examId = card.dataset.exam;
      pickExam(examId);
    });
  });
  document.getElementById('backToExamPickBtn')?.addEventListener('click', () => {
    document.getElementById('examDetailSection').style.display = 'none';
    document.getElementById('examPickSection').style.display = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  document.getElementById('gradeBackBtn')?.addEventListener('click', () => {
    document.getElementById('gradePickSection').style.display = 'none';
    document.getElementById('examPickSection').style.display = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

function showGradePicker() {
  document.getElementById('examPickSection').style.display = 'none';
  document.getElementById('examDetailSection').style.display = 'none';
  document.getElementById('gradePickSection').style.display = '';
  const grid = document.getElementById('gradeGrid');
  grid.innerHTML = '';
  EXAMS.eiken.grades.forEach(g => {
    const hasSecondary = g.key === 'g1' || g.key === 'gp1' || g.key === 'g2' || g.key === 'gp2' || g.key === 'g3';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'grade-card';
    btn.dataset.grade = g.key;
    btn.innerHTML = `
      ${hasSecondary ? '<span class="grade-card-secondary">+二次面接</span>' : '<span class="grade-card-secondary" style="background:rgba(148,163,184,0.18);color:#94a3b8;">一次のみ</span>'}
      <div class="grade-card-name">英検 ${escapeHtml(g.name)}</div>
      <div class="grade-card-cefr">CEFR ${escapeHtml(g.cefr)} 相当</div>
      <div class="grade-card-target">${escapeHtml(g.target)}</div>
    `;
    btn.addEventListener('click', () => {
      state.eikenGrade = g.key;
      state.eikenGradeName = g.name;
      pickExamSections('eiken');
    });
    grid.appendChild(btn);
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function pickExam(examId) {
  const exam = EXAMS[examId];
  if (!exam) return;
  state.examId = examId;
  state.sectionKey = null;
  state.eikenGrade = null;
  // 英検は級選択を先に挟む
  if (examId === 'eiken') {
    showGradePicker();
    return;
  }
  pickExamSections(examId);
}

function pickExamSections(examId) {
  const exam = EXAMS[examId];
  if (!exam) return;

  document.getElementById('examPickSection').style.display = 'none';
  document.getElementById('gradePickSection').style.display = 'none';
  document.getElementById('examDetailSection').style.display = '';
  const gradeLabel = (examId === 'eiken' && state.eikenGradeName) ? ` ${state.eikenGradeName}` : '';
  document.getElementById('examDetailTitle').textContent = `${exam.flag} ${exam.name}${gradeLabel} 対策`;

  // 説明文
  let desc = '';
  if (exam.scoreMax) {
    desc = `スコア範囲: ${exam.scoreMin}〜${exam.scoreMax}${exam.scoreUnit}・出題形式は公式準拠`;
  } else if (exam.grades) {
    desc = `7段階の級別 (5級〜1級) を完全カバー・出題形式は公式準拠`;
  }
  document.getElementById('examDetailDesc').textContent = desc;

  // 目標スコアのプレースホルダ
  const ts = document.getElementById('targetScore');
  ts.placeholder = exam.id === 'toefl' ? '例: 100' : exam.id === 'toeic' ? '例: 800' : exam.id === 'ielts' ? '例: 7.0' : '例: 準1級';
  document.getElementById('targetScoreHint').textContent = exam.id === 'eiken'
    ? '受験する級を入力 (例: 準1級)'
    : `${exam.scoreMin}〜${exam.scoreMax}${exam.scoreUnit}`;

  // セクションカード生成 (英検は級別 sectionsByGrade を使う)
  const sections = (examId === 'eiken' && state.eikenGrade)
    ? getEikenSections(state.eikenGrade)
    : exam.sections;
  state.currentSections = sections;
  const grid = document.getElementById('sectionGrid');
  grid.innerHTML = '';
  sections.forEach(sec => {
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'section-card';
    card.dataset.section = sec.key;
    card.innerHTML = `
      <div class="section-card-icon">${sec.icon}</div>
      <div class="section-card-name">${sec.name}</div>
      <div class="section-card-spec">${sec.timeMin}分 / ${sec.qCount}問</div>
      <div class="section-card-desc">${sec.desc}</div>
    `;
    card.addEventListener('click', () => {
      document.querySelectorAll('.section-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      state.sectionKey = sec.key;
      startSection(sec);
    });
    grid.appendChild(card);
  });

  // 試験日カウントダウン
  const dateInput = document.getElementById('examDate');
  dateInput.onchange = () => {
    const d = new Date(dateInput.value);
    const days = Math.ceil((d - new Date()) / 86400000);
    document.getElementById('daysUntilExam').textContent = days > 0 ? `あと ${days} 日` : '日付を選択';
  };

  // 模試 (フル) ボタン
  document.getElementById('startMockBtn').onclick = () => startFullMock(exam);

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================================================
// セクション or 模試開始
// ==========================================================================
async function startSection(section) {
  const exam = EXAMS[state.examId];
  showRunner(exam, section);
  await generateAndShowQuestions(exam, section, /*full=*/false);
}

async function startFullMock(exam) {
  // フル模試: Reading + Listening を抜粋した縮小版
  const sections = state.currentSections || exam.sections;
  const targetSec = sections.find(s => s.key === 'reading' || s.key === 'r_part5' || s.key === 'l_part1' || s.key === 'r_q1') || sections[0];
  state.sectionKey = targetSec.key;
  showRunner(exam, targetSec, /*isMock=*/true);
  await generateAndShowQuestions(exam, targetSec, /*full=*/true);
}

function showRunner(exam, section, isMock = false) {
  document.getElementById('examPickSection').style.display = 'none';
  document.getElementById('examDetailSection').style.display = 'none';
  document.getElementById('examResultSection').style.display = 'none';
  document.getElementById('examRunnerSection').style.display = '';
  document.getElementById('runnerExamLabel').textContent = `${exam.flag} ${exam.name}${isMock ? ' • 模試 (縮小版)' : ''}`;
  document.getElementById('runnerSectionTitle').textContent = `${section.icon} ${section.name}`;
  document.getElementById('questionBox').innerHTML = '<p class="ee-loading">⏳ AI が問題を生成中... (10〜30秒)</p>';
  document.getElementById('submitAnswersBtn').disabled = true;
  state.startedAt = Date.now();
  startTimer(section.timeMin);
  document.getElementById('cancelRunBtn').onclick = () => {
    stopTimer();
    document.getElementById('examRunnerSection').style.display = 'none';
    document.getElementById('examDetailSection').style.display = '';
  };
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function startTimer(minutes) {
  stopTimer();
  let remain = minutes * 60;
  const el = document.getElementById('examTimer');
  const update = () => {
    const m = Math.floor(remain / 60);
    const s = remain % 60;
    el.textContent = `⏱ ${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    if (remain <= 60) el.classList.add('ee-timer-warn');
    if (remain <= 0) {
      stopTimer();
      el.textContent = '⏱ 終了';
      submitAnswers();
    }
    remain--;
  };
  update();
  state.timerInterval = setInterval(update, 1000);
}
function stopTimer() {
  if (state.timerInterval) {
    clearInterval(state.timerInterval);
    state.timerInterval = null;
  }
  document.getElementById('examTimer')?.classList.remove('ee-timer-warn');
}

// ==========================================================================
// 問題生成 (Claude API)
// ==========================================================================
async function generateAndShowQuestions(exam, section, full = false) {
  const qCount = full ? Math.min(section.qCount, 8) : Math.min(section.qCount, 6); // ブラウザ実行は短めに
  const topic = exam.topics[Math.floor(Math.random() * exam.topics.length)];

  // part 別のジャンル/形式ヒント
  const isReading = /^r_/.test(section.key) || section.key === 'reading';
  const isListening = /^l_/.test(section.key) || section.key === 'listening';
  const isSpeaking = /^s_/.test(section.key) || section.key === 'speaking';
  const isWriting = /^w_/.test(section.key) || section.key === 'writing';

  // 英検級ラベル
  const eikenGradeLabel = (state.examId === 'eiken' && state.eikenGradeName)
    ? `（${state.eikenGradeName}・CEFR ${(EXAMS.eiken.grades.find(g => g.key === state.eikenGrade) || {}).cefr || ''} 相当）`
    : '';

  // 試験別の出題ニュアンス
  const examFlavor = {
    toefl: '英語圏大学院・学部留学。Reading/Listening は学術 (lecture, journal article 風)。Speaking/Writing は明確なテンプレ運用が高得点の鍵。',
    toeic: 'ビジネス英語。実務シーン (会議/メール/出張/契約) のみ。難解な学術語彙NG。Part固有の典型パターンを必ず再現。',
    ielts: '英国系学術。Reading は T/F/NG・見出し選択など IELTS 独自形式。Writing Task 1 はデータ描写、Task 2 はエッセイで構造重視。Speaking Part 2 は1分準備→2分独白の独特形式。',
    eiken: `日本英検 ${state.eikenGradeName || ''}${eikenGradeLabel ? '' : ''}。級ごとに語彙難易度が大きく異なる。新形式 (2024〜): 準1級以下は要約/Eメール返信が追加。二次は面接形式 (1-3級)。日本人受験者の弱点 (冠詞/前置詞/イディオム) を踏まえて出題。`,
  }[exam.id] || '';

  const system = `あなたは ${exam.name} 対策の専門コーチで、過去20年の出題傾向と公式採点基準を完全に把握しています。

【今回の対象 part】
- 試験: ${exam.name}${eikenGradeLabel}
- Part: ${section.name}
- 形式: ${section.desc}
- 制限時間: ${section.timeMin}分 / 公式問題数: ${section.qCount}問 / 配点上限: ${section.scoreMax}
- 受験者の自己申告レベル: CEFR ${state.currentLevel || 'B1'}

【試験固有の方針】
${examFlavor}

【厳守】
- 公式の出題形式と完全に一致させる (TOEIC Part 2 なら3択、TOEFL Reading なら長文+設問、IELTS Listening Section 1 なら社会的会話のみ、英検準1級 Reading 大問1 なら短文穴埋め4択 18問形式)
- 設問の英文は ETS / British Council / 英検協会 が出すレベルのナチュラル英語 (機械翻訳臭/不自然な語彙NG)
- 解説は日本語で、正解の根拠 + 他選択肢の誤りポイント + 関連語彙/文法 を3行以上
- Speaking / Writing は採点ルーブリック (構成 / 語彙 / 文法 / 流暢さ or 一貫性) に基づく評価コメント付きの模範解答
- 英検なら級レベルの語彙統制 (1級は CEFR C1 語彙、5級は中学初級語彙)`;

  const user = `${exam.name}${eikenGradeLabel} の **${section.name}** の問題を ${qCount} 問生成してください。

トピック: ${topic}
ターゲット: 日本人受験者 (CEFR ${state.currentLevel || 'B1'})

【part 形式の必須遵守事項】
- ${section.desc}
- ${isListening ? 'Listening: audio_script に台本を入れる (英語のみ・自然な会話/講義/ナレーション)。speaker label 付き。' : ''}
- ${isReading ? 'Reading: passage に本文を入れる (英語のみ・指定 part の典型ジャンル)。' : ''}
- ${isSpeaking ? 'Speaking: prompt に英語の出題、answer に模範回答 (口頭で60-90秒で言える長さ・テンプレ的構成)。type は "speaking"。' : ''}
- ${isWriting ? 'Writing: prompt に英語の出題、answer に模範エッセイ (指定語数を満たす完全な英文)。type は "essay"。' : ''}

【出力形式】純粋なJSONのみ (他の文字を含めない):
{
  "passage": "(Reading の場合は本文、それ以外は空文字)",
  "audio_script": "(Listening の場合はスクリプト、それ以外は空文字)",
  "prompt": "(Speaking/Writing の場合の英語の出題文、それ以外は空文字)",
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice|short_answer|essay|speaking",
      "stem": "問題文",
      "choices": ["A", "B", "C", "D"],
      "answer": "正解(選択肢index 0始まり、または模範解答テキスト)",
      "explanation": "解説 (日本語、3行以上)"
    }
  ]
}
Speaking/Writing の場合: choices=[], answer に模範解答テキスト全文 (採点ルーブリック別評価コメント込み), type="essay" or "speaking"。`;

  let payload;
  // 1) Live モード優先 (backend AI proxy or 直接APIキー)
  if (isLiveMode()) {
    try {
      payload = await callClaudeJson({ system, user, model: MODEL_DEFAULT, maxTokens: 4000 });
    } catch (e) {
      console.warn('[exam] AI generation failed, falling back to sample bank:', e);
      payload = null;
    }
  }
  // 2) Live失敗 or デモモード → SAMPLE_BANKS / AUTO_GENERATED_BANKS から
  if (!payload || !payload.questions || !payload.questions.length) {
    payload = demoQuestions(exam, section, qCount, topic);
  }
  try {
    state.questions = payload.questions || [];
    state.passage = payload.passage || '';
    state.audioScript = payload.audio_script || '';
    state.prompt = payload.prompt || '';
    state.userAnswers = {};
    renderQuestions();
    document.getElementById('submitAnswersBtn').disabled = false;
    document.getElementById('submitAnswersBtn').onclick = submitAnswers;
  } catch (e) {
    console.error(e);
    document.getElementById('questionBox').innerHTML = `
      <div class="ee-error">
        <strong>⚠️ 問題生成に失敗しました</strong>
        <p>サーバーが混み合っている可能性があります。少し時間をおいて再度お試しください。</p>
      </div>`;
  }
}

function renderQuestions() {
  const box = document.getElementById('questionBox');
  let html = '';
  if (state.passage) {
    html += `<div class="ee-passage"><h3>📖 Passage</h3><p>${escapeHtml(state.passage).replace(/\n/g,'<br>')}</p></div>`;
  }
  if (state.audioScript) {
    html += `<div class="ee-passage ee-audio"><h3>🎧 Listening Script (本来は音声)</h3><p>${escapeHtml(state.audioScript).replace(/\n/g,'<br>')}</p>
      <p class="ee-note">💡 本物の試験では音声のみ。ここではスクリプトを表示しています。</p></div>`;
  }
  if (state.prompt) {
    html += `<div class="ee-passage"><h3>✍️ Prompt</h3><p>${escapeHtml(state.prompt).replace(/\n/g,'<br>')}</p></div>`;
  }
  state.questions.forEach((q, idx) => {
    html += `<div class="ee-question" data-qid="${q.id}">
      <div class="ee-question-num">Q${idx + 1}</div>
      <div class="ee-question-stem">${escapeHtml(q.stem || '')}</div>`;
    if (q.type === 'multiple_choice' && Array.isArray(q.choices) && q.choices.length) {
      html += '<div class="ee-choices">';
      q.choices.forEach((c, ci) => {
        html += `<label class="ee-choice">
          <input type="radio" name="${q.id}" value="${ci}">
          <span class="ee-choice-letter">${String.fromCharCode(65 + ci)}</span>
          <span class="ee-choice-text">${escapeHtml(c)}</span>
        </label>`;
      });
      html += '</div>';
    } else if (q.type === 'short_answer') {
      html += `<input type="text" class="ee-text-input" name="${q.id}" placeholder="回答を入力">`;
    } else {
      html += `<textarea class="ee-textarea" name="${q.id}" rows="6" placeholder="${q.type === 'speaking' ? '口頭で話す内容を文字に書き起こしてください' : 'エッセイをここに書いてください'}"></textarea>`;
    }
    html += '</div>';
  });
  box.innerHTML = html;

  // 入力イベントで state.userAnswers を更新
  state.questions.forEach(q => {
    const inputs = box.querySelectorAll(`[name="${q.id}"]`);
    inputs.forEach(inp => {
      inp.addEventListener('change', () => {
        if (inp.type === 'radio') state.userAnswers[q.id] = parseInt(inp.value, 10);
        else state.userAnswers[q.id] = inp.value;
      });
      inp.addEventListener('input', () => {
        if (inp.tagName === 'INPUT' || inp.tagName === 'TEXTAREA') state.userAnswers[q.id] = inp.value;
      });
    });
  });
}

// ==========================================================================
// 採点
// ==========================================================================
async function submitAnswers() {
  stopTimer();
  document.getElementById('submitAnswersBtn').disabled = true;
  document.getElementById('submitAnswersBtn').textContent = '⏳ 採点中...';

  const exam = EXAMS[state.examId];
  const sections = state.currentSections || exam.sections;
  const section = sections.find(s => s.key === state.sectionKey);
  let result;
  try {
    if (isLiveMode()) {
      result = await scoreWithClaude(exam, section);
    } else {
      result = scoreLocally(exam, section);
    }
  } catch (e) {
    console.error(e);
    alert('採点中にエラーが発生しました: ' + (e.message || e));
    document.getElementById('submitAnswersBtn').disabled = false;
    document.getElementById('submitAnswersBtn').textContent = '📤 回答を提出して採点';
    return;
  }
  state.result = result;
  showResult(exam, section, result);
}

async function scoreWithClaude(exam, section) {
  // ローカル採点 (multiple_choice) は即座に正誤判定。
  // Speaking/Writing/short_answer は Claude opus に投げる。
  let mcScore = 0, mcTotal = 0;
  const perQuestion = [];
  for (const q of state.questions) {
    if (q.type === 'multiple_choice') {
      mcTotal += 1;
      const correct = parseInt(q.answer, 10);
      const user = state.userAnswers[q.id];
      const isCorrect = (typeof user === 'number') && user === correct;
      if (isCorrect) mcScore += 1;
      perQuestion.push({
        qid: q.id, stem: q.stem,
        userAnswer: typeof user === 'number' ? q.choices[user] : '(未回答)',
        correctAnswer: q.choices[correct],
        isCorrect, explanation: q.explanation,
      });
    } else {
      perQuestion.push({
        qid: q.id, stem: q.stem,
        userAnswer: state.userAnswers[q.id] || '(未回答)',
        modelAnswer: q.answer || '',
        explanation: q.explanation,
      });
    }
  }

  // Claude にスコア予測 + 弱点分析を依頼
  const system = `あなたは ${exam.name} の経験豊富な採点者です。受験者の回答を採点し、${exam.name} の公式スコア基準に基づいて予測スコアを出してください。`;
  const sectionScoreMax = section.scoreMax || 30;
  const userPayload = {
    exam: exam.name,
    section: section.name,
    sectionScoreMax,
    multiple_choice_correct: mcScore,
    multiple_choice_total: mcTotal,
    open_answers: perQuestion.filter(q => q.modelAnswer !== undefined).map(q => ({
      stem: q.stem, user_answer: q.userAnswer, model_answer: q.modelAnswer
    })),
    target_level: state.currentLevel || 'B1',
  };
  const userMsg = `以下の受験データを採点してください:
${JSON.stringify(userPayload, null, 2)}

【出力形式】純粋なJSONのみ:
{
  "section_score": (このセクションの推定スコア 0〜${sectionScoreMax}),
  "overall_score": (この試験全体に換算した推定スコア。${exam.name}の総合スコア基準で),
  "cefr": "A1|A2|B1|B2|C1|C2",
  "strengths": ["具体的な強み1", "強み2"],
  "weaknesses": ["弱点1 (具体的に何ができてないか)", "弱点2"],
  "feedback_per_open_answer": [
    {"stem": "...", "score_breakdown": "構成X/語彙Y/文法Z/流暢さW", "comment": "具体的な改善コメント (日本語)"}
  ],
  "study_plan": "今後2-4週間の学習プラン (毎日のタスクと推奨教材を具体的に・日本語)"
}`;

  let aiResult;
  try {
    aiResult = await callClaudeJson({ system, user: userMsg, model: MODEL_HEAVY, maxTokens: 3500 });
  } catch (e) {
    console.warn('[score] Heavy model failed, fallback:', e);
    aiResult = await callClaudeJson({ system, user: userMsg, model: MODEL_DEFAULT, maxTokens: 3500 });
  }

  return {
    sectionScore: aiResult.section_score ?? Math.round((mcScore / Math.max(1, mcTotal)) * sectionScoreMax),
    overallScore: aiResult.overall_score ?? Math.round((mcScore / Math.max(1, mcTotal)) * exam.scoreMax),
    cefr: aiResult.cefr || 'B1',
    strengths: aiResult.strengths || [],
    weaknesses: aiResult.weaknesses || [],
    feedback: aiResult.feedback_per_open_answer || [],
    studyPlan: aiResult.study_plan || '',
    perQuestion,
    mcScore, mcTotal,
  };
}

function scoreLocally(exam, section) {
  let mcScore = 0, mcTotal = 0;
  const perQuestion = [];
  for (const q of state.questions) {
    if (q.type === 'multiple_choice') {
      mcTotal += 1;
      const correct = parseInt(q.answer, 10);
      const user = state.userAnswers[q.id];
      const isCorrect = (typeof user === 'number') && user === correct;
      if (isCorrect) mcScore += 1;
      perQuestion.push({
        qid: q.id, stem: q.stem,
        userAnswer: typeof user === 'number' ? q.choices[user] : '(未回答)',
        correctAnswer: q.choices[correct],
        isCorrect, explanation: q.explanation,
      });
    } else {
      perQuestion.push({
        qid: q.id, stem: q.stem,
        userAnswer: state.userAnswers[q.id] || '(未回答)',
        modelAnswer: q.answer || '',
        explanation: q.explanation,
      });
    }
  }
  const sectionScoreMax = section.scoreMax || 30;
  const ratio = mcTotal > 0 ? mcScore / mcTotal : 0;
  const sectionScore = Math.round(ratio * sectionScoreMax * 10) / 10;
  const overallScore = Math.round(ratio * exam.scoreMax * 10) / 10;
  const cefr = scoreToCefr(exam.id, overallScore);
  return {
    sectionScore, overallScore, cefr,
    strengths: ['基本的な解答パターンを理解しています'],
    weaknesses: ['詳細な分析は次回 AI 接続が安定した時にご提供します'],
    feedback: [],
    studyPlan: '今回の結果を踏まえ、毎日30分の集中学習を推奨します。次回ログイン時に AI による詳細プランをご提示します。',
    perQuestion,
    mcScore, mcTotal,
  };
}

// ==========================================================================
// 結果表示
// ==========================================================================
function showResult(exam, section, result) {
  document.getElementById('examRunnerSection').style.display = 'none';
  document.getElementById('examResultSection').style.display = '';

  // ヒーロー
  const targetScore = parseFloat(document.getElementById('targetScore')?.value || '0');
  const percent = Math.round((result.overallScore / exam.scoreMax) * 100);
  document.getElementById('resultScoreHero').innerHTML = `
    <div class="result-hero-inner" style="border-color:${exam.color}">
      <div class="result-hero-flag">${exam.flag}</div>
      <div class="result-hero-exam">${exam.name}</div>
      <div class="result-hero-score" style="color:${exam.color}">
        <span class="result-hero-num">${result.overallScore}</span>
        <span class="result-hero-unit">/ ${exam.scoreMax}${exam.scoreUnit}</span>
      </div>
      <div class="result-hero-cefr">CEFR <strong>${result.cefr}</strong> 相当</div>
      <div class="result-hero-section">${section.icon} ${section.name}: ${result.sectionScore} / ${section.scoreMax}</div>
      ${targetScore > 0 ? `<div class="result-hero-target">🎯 目標 ${targetScore} まで <strong>${(targetScore - result.overallScore).toFixed(1)}</strong></div>` : ''}
      <div class="result-hero-bar"><div class="result-hero-bar-fill" style="width:${percent}%;background:${exam.color}"></div></div>
    </div>`;

  // 4試験換算
  const allScores = cefrToAllScores(result.cefr);
  document.getElementById('resultConverterGrid').innerHTML = `
    <div class="conv-card"><div class="conv-flag">🇺🇸</div><div class="conv-name">TOEFL iBT</div><div class="conv-score">${allScores.toefl}</div></div>
    <div class="conv-card"><div class="conv-flag">💼</div><div class="conv-name">TOEIC L&R</div><div class="conv-score">${allScores.toeic}</div></div>
    <div class="conv-card"><div class="conv-flag">🇬🇧</div><div class="conv-name">IELTS</div><div class="conv-score">${allScores.ielts}</div></div>
    <div class="conv-card"><div class="conv-flag">🇯🇵</div><div class="conv-name">英検</div><div class="conv-score">${allScores.eiken}</div></div>
  `;

  // 強み・弱点・解説
  let fb = '<h3>🔍 強み</h3><ul>';
  result.strengths.forEach(s => fb += `<li>✅ ${escapeHtml(s)}</li>`);
  fb += '</ul><h3>🛠 弱点</h3><ul>';
  result.weaknesses.forEach(s => fb += `<li>⚠️ ${escapeHtml(s)}</li>`);
  fb += '</ul>';

  fb += '<h3>📝 設問別フィードバック</h3>';
  result.perQuestion.forEach((q, i) => {
    if (q.isCorrect !== undefined) {
      fb += `<div class="result-q ${q.isCorrect ? 'correct' : 'wrong'}">
        <div class="result-q-head">Q${i+1} ${q.isCorrect ? '✅ 正解' : '❌ 誤答'}</div>
        <div class="result-q-stem">${escapeHtml(q.stem || '')}</div>
        <div class="result-q-user">あなたの回答: <strong>${escapeHtml(String(q.userAnswer))}</strong></div>
        <div class="result-q-correct">正解: <strong>${escapeHtml(String(q.correctAnswer))}</strong></div>
        <div class="result-q-exp">💡 ${escapeHtml(q.explanation || '')}</div>
      </div>`;
    } else {
      const aiFb = (result.feedback || []).find(f => f.stem === q.stem);
      fb += `<div class="result-q open">
        <div class="result-q-head">Q${i+1} ✍️ 自由記述/口頭</div>
        <div class="result-q-stem">${escapeHtml(q.stem || '')}</div>
        <div class="result-q-user"><strong>あなたの回答:</strong><br>${escapeHtml(String(q.userAnswer)).replace(/\n/g,'<br>')}</div>
        <div class="result-q-model"><strong>模範解答:</strong><br>${escapeHtml(String(q.modelAnswer)).replace(/\n/g,'<br>')}</div>
        ${aiFb ? `<div class="result-q-exp">📊 ${escapeHtml(aiFb.score_breakdown || '')}<br>💡 ${escapeHtml(aiFb.comment || '')}</div>` : ''}
      </div>`;
    }
  });
  document.getElementById('resultFeedback').innerHTML = fb;

  // 学習プラン
  document.getElementById('learningPlanBox').innerHTML = `<div class="plan-text">${escapeHtml(result.studyPlan).replace(/\n/g,'<br>')}</div>`;

  // ボタン
  document.getElementById('retryBtn').onclick = () => {
    const sections = state.currentSections || exam.sections;
    const sec = sections.find(s => s.key === state.sectionKey);
    startSection(sec);
  };
  document.getElementById('newExamBtn').onclick = () => {
    document.getElementById('examResultSection').style.display = 'none';
    document.getElementById('examDetailSection').style.display = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  document.getElementById('backToTopBtn').onclick = () => {
    document.getElementById('examResultSection').style.display = 'none';
    document.getElementById('examDetailSection').style.display = 'none';
    document.getElementById('examPickSection').style.display = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================================================
// プレビュー fallback (API 未接続時の限定問題セット・ユーザーには「準備中」と見せる)
// ==========================================================================
// ==========================================================================
// 試験別×part別 サンプル問題バンク → english-exam-banks.js に分離
// window.SAMPLE_BANKS と window.AUTO_GENERATED_BANKS を統合参照
// ==========================================================================
const SAMPLE_BANKS = (typeof window !== 'undefined' && window.SAMPLE_BANKS) ? window.SAMPLE_BANKS : {};

function getPartBank(examId, sectionKey) {
  // 1) AI生成バンク (バックエンドが日々追加・優先) → ローテで多様性確保
  const auto = (typeof window !== 'undefined' && window.AUTO_GENERATED_BANKS) ? window.AUTO_GENERATED_BANKS : {};
  const autoBank = auto[examId] && auto[examId][sectionKey];
  // 2) 静的サンプル
  const staticBank = SAMPLE_BANKS[examId] && SAMPLE_BANKS[examId][sectionKey];
  // 英検は g{N}_{key} 形式で sectionsByGrade を区別 (例: gp1_r_q1)
  if (!autoBank && !staticBank && examId === 'eiken' && state && state.eikenGrade) {
    const compoundKey = state.eikenGrade + '_' + sectionKey;
    return SAMPLE_BANKS.eiken && SAMPLE_BANKS.eiken[compoundKey];
  }
  // ランダム選択 (AI生成があれば優先・無ければ静的)
  if (autoBank && staticBank) {
    return Math.random() < 0.6 ? autoBank : staticBank;
  }
  return autoBank || staticBank;
}



function demoQuestions(exam, section, qCount, topic) {
  const isReading = section.key.startsWith('r_') || section.key === 'reading';
  const isListening = section.key.startsWith('l_') || section.key === 'listening';
  const isSpeaking = section.key.startsWith('s_') || section.key === 'speaking';
  const isWriting = section.key.startsWith('w_') || section.key === 'writing';

  // 1) part 別の本格サンプル (静的バンク + AI生成バンク 統合) を取得
  const partBank = getPartBank(exam.id, section.key);

  if (partBank) {
    if (partBank.questions) {
      // multiple_choice 系
      const qs = partBank.questions.slice(0, qCount).map((q, i) => ({
        id: `q${i + 1}`,
        type: 'multiple_choice',
        stem: q.stem,
        choices: q.choices,
        answer: q.answer,
        explanation: q.explanation,
      }));
      // qCount に足りない分は generic で埋める
      while (qs.length < qCount) {
        const i = qs.length + 1;
        qs.push({
          id: `q${i}`,
          type: 'multiple_choice',
          stem: `Q${i}: ${section.name} のサンプル問題 (本文に基づき推論せよ)`,
          choices: ['Option A', 'Option B', 'Option C', 'Option D'],
          answer: '1',
          explanation: 'AI 接続が安定すると、より詳細なオリジナル問題と解説をご提供します。',
        });
      }
      return {
        passage: partBank.passage || '',
        audio_script: partBank.audio_script || '',
        prompt: partBank.prompt || '',
        questions: qs,
      };
    }
    if (partBank.prompt) {
      // Speaking / Writing 系: 単題
      return {
        passage: '',
        audio_script: '',
        prompt: partBank.prompt,
        questions: [{
          id: 'q1',
          type: isSpeaking ? 'speaking' : 'essay',
          stem: partBank.prompt,
          choices: [],
          answer: partBank.sample || `Sample response for ${exam.name} ${section.name}.`,
          explanation: 'AI 接続が安定すると、構成・語彙・文法・流暢さ別の評価コメント付き模範解答をご提供します。',
        }],
      };
    }
  }

  // 2) フォールバック: generic な汎用問題
  const passage = isReading ? `[Sample passage] In recent decades, researchers have observed significant changes in ${topic}. Multiple studies suggest that the underlying mechanisms are far more complex than initially believed. The implications extend across various disciplines.` : '';
  const audioScript = isListening ? `[Sample listening on ${topic}] Speaker A: I noticed something interesting about this in our recent study. Speaker B: Really? What did you find? Speaker A: The data suggests we need to reconsider our assumptions.` : '';
  const prompt = isSpeaking ? `Talk about your experience related to ${topic}. You have 45 seconds to prepare and 60 seconds to speak.` : isWriting ? `Some people believe ${topic} should be a priority in modern education. Others disagree. Discuss both views and give your opinion. (250+ words)` : '';
  const questions = [];
  for (let i = 1; i <= qCount; i++) {
    if (isSpeaking || isWriting) {
      questions.push({
        id: `q${i}`,
        type: isSpeaking ? 'speaking' : 'essay',
        stem: prompt || `Q${i}: ${topic} について意見を述べてください`,
        choices: [],
        answer: `A well-structured response would address ${topic} with concrete examples and clear reasoning, demonstrating mastery of vocabulary, grammar, and logical organization.`,
        explanation: 'AI 接続を準備中です。安定接続後はより詳細な解説を表示します。',
      });
    } else {
      questions.push({
        id: `q${i}`,
        type: 'multiple_choice',
        stem: `Q${i}: According to the passage, what is the main point about ${topic}?`,
        choices: [
          'It has remained unchanged for decades',
          'It is more complex than once thought',
          'It is unrelated to other disciplines',
          'It has no practical implications',
        ],
        answer: '1',
        explanation: 'サンプル解説: 本文の "more complex than initially believed" が根拠。実際の試験では選択肢の難度が上がります。',
      });
    }
  }
  return { passage, audio_script: audioScript, prompt, questions };
}

// ==========================================================================
// Utility
// ==========================================================================
function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

// ==========================================================================
// Listening TTS (Web Speech API SpeechSynthesis)
// ==========================================================================
function playTTS(text, opts = {}) {
  if (!('speechSynthesis' in window)) {
    alert('お使いのブラウザは音声合成に対応していません (Chrome/Safari/Edge推奨)');
    return;
  }
  window.speechSynthesis.cancel(); // 重複再生防止
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = opts.lang || 'en-US';
  utt.rate = opts.rate || 0.95;  // やや遅め (試験本番に近い速度)
  utt.pitch = opts.pitch || 1.0;
  // 英語ナレーターを優先選択
  const voices = window.speechSynthesis.getVoices();
  const enVoice = voices.find(v => v.lang.startsWith('en') && /Samantha|Alex|Daniel|Karen|Google US|Microsoft/.test(v.name))
    || voices.find(v => v.lang === utt.lang)
    || voices.find(v => v.lang.startsWith('en'));
  if (enVoice) utt.voice = enVoice;
  window.speechSynthesis.speak(utt);
}
function stopTTS() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
}

// ==========================================================================
// Speaking 音声認識 (Web Speech API SpeechRecognition)
// ==========================================================================
function setupSpeechRecognition(targetTextarea, btn) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { btn.disabled = true; btn.textContent = '🚫 音声認識非対応 (Chrome/Edge推奨)'; return; }
  const rec = new SR();
  rec.lang = 'en-US';
  rec.continuous = true;
  rec.interimResults = true;
  let finalText = targetTextarea.value || '';
  rec.onresult = (e) => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i];
      if (r.isFinal) finalText += r[0].transcript + ' ';
      else interim += r[0].transcript;
    }
    targetTextarea.value = finalText + interim;
    // state 同期
    const qid = targetTextarea.name;
    if (qid) state.userAnswers[qid] = targetTextarea.value;
  };
  rec.onerror = (e) => {
    console.warn('[STT] error:', e.error);
    btn.classList.remove('recording');
    btn.textContent = '🎤 録音開始';
  };
  rec.onend = () => {
    btn.classList.remove('recording');
    btn.textContent = '🎤 録音開始';
  };
  let recording = false;
  btn.onclick = () => {
    if (recording) { rec.stop(); recording = false; }
    else {
      finalText = targetTextarea.value || '';
      rec.start(); recording = true;
      btn.classList.add('recording');
      btn.textContent = '⏹ 録音停止';
    }
  };
}

// renderQuestions の拡張: TTS ボタン + STT ボタン追加
const _origRenderQuestions = renderQuestions;
renderQuestions = function() {
  _origRenderQuestions();
  const box = document.getElementById('questionBox');
  // Listening パッセージに TTS ボタン追加
  if (state.audioScript) {
    const audioBox = box.querySelector('.ee-audio');
    if (audioBox) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ee-tts-btn';
      btn.textContent = '🔊 音声を再生 (本物の試験に近いスピード)';
      btn.onclick = () => playTTS(state.audioScript);
      audioBox.appendChild(btn);
      const stop = document.createElement('button');
      stop.type = 'button';
      stop.className = 'ee-tts-btn';
      stop.style.marginLeft = '0.5rem';
      stop.textContent = '⏹ 停止';
      stop.onclick = () => stopTTS();
      audioBox.appendChild(stop);
    }
  }
  // Speaking 問題に音声認識ボタン追加
  state.questions.forEach(q => {
    if (q.type === 'speaking') {
      const ta = box.querySelector(`textarea[name="${q.id}"]`);
      if (ta) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'ee-mic-btn';
        btn.textContent = '🎤 録音開始';
        ta.insertAdjacentElement('afterend', btn);
        setupSpeechRecognition(ta, btn);
      }
    }
  });
};

// ==========================================================================
// 学習履歴 (localStorage 永続化)
// ==========================================================================
const HIST_KEY = 'ai_juku_eng_exam_history';

function saveHistory(record) {
  let arr = [];
  try { arr = JSON.parse(localStorage.getItem(HIST_KEY) || '[]'); } catch {}
  arr.unshift(record);
  arr = arr.slice(0, 50); // 最大50件保持
  localStorage.setItem(HIST_KEY, JSON.stringify(arr));
}
function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HIST_KEY) || '[]'); } catch { return []; }
}

// showResult を拡張して履歴保存
const _origShowResult = showResult;
showResult = function(exam, section, result) {
  _origShowResult(exam, section, result);
  saveHistory({
    ts: new Date().toISOString(),
    examId: state.examId,
    examName: exam.name,
    examFlag: exam.flag,
    sectionKey: state.sectionKey,
    sectionName: section.name,
    overallScore: result.overallScore,
    sectionScore: result.sectionScore,
    cefr: result.cefr,
  });
  renderHistorySection();
};

function renderHistorySection() {
  let host = document.getElementById('historySection');
  if (!host) {
    host = document.createElement('section');
    host.id = 'historySection';
    host.className = 'ee-section';
    host.innerHTML = `
      <div class="ee-section-head">
        <div class="ee-eyebrow">PROGRESS</div>
        <h2>📈 あなたの学習履歴 (直近10件)</h2>
        <p class="ee-section-desc">スコアの推移・伸び率を確認</p>
      </div>
      <div id="historyContent"></div>`;
    document.querySelector('.ee-section-cta').insertAdjacentElement('beforebegin', host);
  }
  const hist = loadHistory().slice(0, 10);
  const content = document.getElementById('historyContent');
  if (!hist.length) {
    content.innerHTML = '<p style="color:#9ca3af;text-align:center;">まだ受験記録がありません。模試に挑戦すると履歴が蓄積されます。</p>';
    return;
  }
  let html = '<div class="ee-history-grid">';
  hist.forEach(h => {
    const d = new Date(h.ts);
    const dateStr = `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    html += `<div class="ee-history-card">
      <div class="ee-history-date">${dateStr}</div>
      <div class="ee-history-exam">${h.examFlag} ${h.examName} - ${h.sectionName}</div>
      <div class="ee-history-score">${h.overallScore}<span style="font-size:0.78rem;color:#9ca3af;"> (CEFR ${h.cefr})</span></div>
    </div>`;
  });
  html += '</div>';
  content.innerHTML = html;
}

// ==========================================================================
// 頻出語彙トレーニング (フラッシュカード)
// ==========================================================================
const VOCAB_BANKS = {
  toefl: [
    { word: 'ubiquitous', meaning: '遍在する、至る所にある', example: 'Smartphones have become ubiquitous in modern society.' },
    { word: 'paradigm', meaning: '枠組み、規範', example: 'The new theory represents a paradigm shift in physics.' },
    { word: 'inherent', meaning: '本来備わっている、固有の', example: 'Risk is inherent in any investment.' },
    { word: 'mitigate', meaning: '和らげる、緩和する', example: 'Vaccines mitigate the spread of disease.' },
    { word: 'plausible', meaning: 'もっともらしい', example: 'His explanation sounded plausible at first.' },
    { word: 'comprehensive', meaning: '包括的な', example: 'The book provides a comprehensive overview.' },
    { word: 'detrimental', meaning: '有害な', example: 'Smoking is detrimental to health.' },
    { word: 'profound', meaning: '深い、重大な', example: 'The discovery had a profound impact on science.' },
  ],
  toeic: [
    { word: 'reimbursement', meaning: '払い戻し、経費精算', example: 'Please submit receipts for reimbursement.' },
    { word: 'invoice', meaning: '請求書', example: 'The invoice will be sent next week.' },
    { word: 'agenda', meaning: '議題', example: 'Let\'s review the agenda for today\'s meeting.' },
    { word: 'deadline', meaning: '締切', example: 'The deadline for this project is Friday.' },
    { word: 'subsidiary', meaning: '子会社', example: 'The subsidiary reports to headquarters.' },
    { word: 'inventory', meaning: '在庫', example: 'We need to take inventory at the end of each month.' },
    { word: 'procurement', meaning: '調達、購入', example: 'The procurement department handles all purchases.' },
    { word: 'remittance', meaning: '送金', example: 'Please confirm the remittance amount.' },
  ],
  ielts: [
    { word: 'sustainable', meaning: '持続可能な', example: 'We need sustainable energy sources.' },
    { word: 'urbanization', meaning: '都市化', example: 'Rapid urbanization causes environmental issues.' },
    { word: 'infrastructure', meaning: 'インフラ、社会基盤', example: 'Investment in infrastructure boosts the economy.' },
    { word: 'demographic', meaning: '人口統計の', example: 'Demographic changes affect housing demand.' },
    { word: 'biodiversity', meaning: '生物多様性', example: 'Tropical rainforests have high biodiversity.' },
    { word: 'globalization', meaning: 'グローバル化', example: 'Globalization has both benefits and drawbacks.' },
    { word: 'discrimination', meaning: '差別', example: 'Laws prohibit workplace discrimination.' },
    { word: 'controversy', meaning: '論争', example: 'The new policy sparked controversy.' },
  ],
  eiken: [
    { word: 'recommend', meaning: '推薦する、勧める', example: 'I recommend this restaurant.' },
    { word: 'environment', meaning: '環境', example: 'We must protect the environment.' },
    { word: 'opportunity', meaning: '機会', example: 'This is a great opportunity to learn.' },
    { word: 'experience', meaning: '経験', example: 'I have experience in teaching.' },
    { word: 'communication', meaning: 'コミュニケーション', example: 'Good communication is important.' },
    { word: 'community', meaning: '地域社会', example: 'Our community is very friendly.' },
    { word: 'achievement', meaning: '達成', example: 'Winning the prize was a great achievement.' },
    { word: 'responsibility', meaning: '責任', example: 'Parents have a responsibility to their children.' },
  ],
};
const VOCAB_KEY = 'ai_juku_vocab_progress';

function showVocabTrainer(examId) {
  const bank = VOCAB_BANKS[examId] || VOCAB_BANKS.toefl;
  const wrap = document.createElement('div');
  wrap.id = 'vocabTrainer';
  wrap.className = 'vocab-card';
  let idx = 0;
  const render = () => {
    const w = bank[idx];
    wrap.classList.remove('revealed');
    wrap.innerHTML = `
      <div style="font-size:0.78rem;color:#9ca3af;margin-bottom:0.5rem;">${EXAMS[examId].name} 頻出語彙 ${idx+1}/${bank.length}</div>
      <div class="vocab-word">${w.word}</div>
      <div class="vocab-meaning">${w.meaning}</div>
      <div class="vocab-example">"${w.example}"</div>
      <div class="vocab-actions">
        <button class="ee-btn ee-btn-secondary" id="vocabReveal">💡 意味を見る</button>
        <button class="ee-btn ee-btn-ghost" id="vocabSpeak">🔊 発音</button>
        <button class="ee-btn ee-btn-secondary" id="vocabNext">次へ →</button>
      </div>`;
    wrap.querySelector('#vocabReveal').onclick = () => wrap.classList.toggle('revealed');
    wrap.querySelector('#vocabSpeak').onclick = () => playTTS(w.word + '. ' + w.example, { rate: 0.85 });
    wrap.querySelector('#vocabNext').onclick = () => {
      idx = (idx + 1) % bank.length;
      // 既知マーク
      try {
        const prog = JSON.parse(localStorage.getItem(VOCAB_KEY) || '{}');
        prog[w.word] = (prog[w.word] || 0) + 1;
        localStorage.setItem(VOCAB_KEY, JSON.stringify(prog));
      } catch {}
      render();
    };
  };
  render();
  return wrap;
}

// ==========================================================================
// 試験別ストラテジー集
// ==========================================================================
const STRATEGIES = {
  toefl: [
    'Reading: 最初の段落を熟読し、各段落の topic sentence を読むだけで6-7割は意味が取れる。詳細問題は本文に戻って scan。',
    'Listening: 会話/講義の出題は3-6問。最初の30秒で「目的」を掴むこと。メモは構造のみ取る (誰が・何を・なぜ)。',
    'Speaking: Independent は 15秒準備 + 45秒回答。テンプレ "I prefer X for two reasons. First... Second..." で時間管理。',
    'Speaking Integrated: パッセージのキーワード3-4個 + 講義の対比点を必ず含める。45-60秒で結論まで言い切る。',
    'Writing Integrated: 講義が読解を「補足」or「反論」しているかをまず判定。150-225語で3パラ構成。',
    'Writing Independent: 序論 (背景+主張) + 本論2-3パラ + 結論。300語以上、具体例必須。',
  ],
  toeic: [
    'Part 1: 主語 → 動詞 → 目的語 の順で写真と一致するか確認。誤答に「写真にない人物・物」「ありえない動作」が頻出。',
    'Part 2: 疑問詞 (What/Where/Who/When/Why/How) を聞き逃すな。Yes/No 疑問文は応答も Yes/No が多いが「I don\'t know」「Let me check」も正解候補。',
    'Part 3-4: 設問先読みが鉄則。3問の設問を25秒で読んで、放送を聞きながら順に解答。',
    'Part 5: 30問を10分以内で解く。空所前後の品詞を見て「文法 or 語彙」を瞬時に判断。',
    'Part 6: 文挿入は「前後の繋がり」が鍵。代名詞・接続詞がヒント。',
    'Part 7: シングルパッセージは1問1分、ダブル/トリプルは1問1.5分目安。NOT問題は時間がかかるので最後に回す。',
  ],
  ielts: [
    'Listening: 解答用紙への転記時間が10分ある (CDIS版を除く)。解答中は本問用紙にメモ → 後でクリアにペンで書く。',
    'Reading: パッセージ3つを20分ずつ。最初に title → 各段落の最初の文 → 設問の順でスキャン。',
    'Reading T-F-NG: 「Not Given」を選ぶ勇気を持て。本文に書いてないなら NG。',
    'Writing Task 1: 全データを書こうとせず、最も顕著な傾向2-3個に絞る。「overall」段落で全体傾向を最初に書く。',
    'Writing Task 2: Introduction (主張明示) + Body 2 paragraphs (1論点1段落・例あり) + Conclusion (主張再強調) で250語以上。',
    'Speaking: Part 2 で2分話す訓練が最重要。タイマーで毎日3トピック練習。',
  ],
  eiken: [
    '1級・準1級: 語彙問題 (Part 1) が最も配点が高い。単語帳は「パス単」を毎日30語×30日。',
    'Reading: 長文は「設問先読み → 該当段落をスキャン」。全文読む必要なし。',
    'Listening: 1級・準1級は1回しか流れない。メモは固有名詞と数字のみ。',
    'Writing: 構成テンプレを暗記する。「Introduction (意見) + Body 2 reasons + Conclusion」の4段落構成。',
    '二次試験 (面接): 入室から退室まで全て英語。「Sorry, could you repeat?」で聞き返し可能。',
    '中学英語ベース (3-5級): 教科書レベル + 過去問演習で十分合格可能。',
  ],
};

function renderStrategySection(examId) {
  const list = STRATEGIES[examId] || [];
  if (!list.length) return null;
  const wrap = document.createElement('section');
  wrap.className = 'ee-section';
  wrap.innerHTML = `
    <div class="ee-section-head">
      <div class="ee-eyebrow">EXPERT TIPS</div>
      <h2>🎯 ${EXAMS[examId].name} 専門ストラテジー</h2>
      <p class="ee-section-desc">10年塾講師の現場知見 + AI が分析した出題パターン</p>
    </div>
    <ul class="strategy-list">
      ${list.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
    </ul>
    <div style="margin-top:1.5rem;text-align:center;">
      <h3 style="margin:0 0 0.6rem;font-size:1rem;">📚 頻出語彙トレーニング</h3>
      <div id="vocabTrainerHost"></div>
    </div>
  `;
  setTimeout(() => {
    const host = wrap.querySelector('#vocabTrainerHost');
    if (host) host.appendChild(showVocabTrainer(examId));
  }, 0);
  return wrap;
}

// pickExam を拡張: 試験詳細セクションの後にストラテジー + 履歴を表示
const _origPickExam = pickExam;
pickExam = function(examId) {
  _origPickExam(examId);
  // 既存のストラテジー section を削除
  document.querySelectorAll('.ee-section-strategy').forEach(el => el.remove());
  const strat = renderStrategySection(examId);
  if (strat) {
    strat.classList.add('ee-section-strategy');
    document.getElementById('examDetailSection').insertAdjacentElement('afterend', strat);
  }
  renderHistorySection();
};

// ==========================================================================
// Init
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  updateModeBadge();
  bindExamCards();
  // currentLevel state 同期
  document.getElementById('currentLevel').addEventListener('change', e => {
    state.currentLevel = e.target.value;
  });
  state.currentLevel = document.getElementById('currentLevel').value || 'B1';
  // 起動時に履歴セクションを描画
  renderHistorySection();
  // 音声合成の voices ロードを待つ (Chrome は遅延ロード)
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {};
  }
});
