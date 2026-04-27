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
  daigaku: {
    id: 'daigaku',
    name: '大学入試対策',
    flag: '🎓',
    color: '#0ea5e9',
    scoreMin: 0, scoreMax: 100, scoreUnit: '点',
    requiresGrade: true,  // 大学選択ステップを挟む (英検と同じパターン)
    grades: [
      // 国公立 トップ
      { key: 'todai',     name: '東京大学',         cefr: 'B2-C1', target: '日本最難関・要約/和訳/英作文の総合力' },
      { key: 'kyodai',    name: '京都大学',         cefr: 'B2-C1', target: '骨太な構造把握・難解な英文和訳' },
      { key: 'osaka',     name: '大阪大学',         cefr: 'B2',    target: '英文要旨把握・自由英作文' },
      { key: 'tokoda',    name: '東京工業大学',     cefr: 'B2',    target: '理工系語彙・科学技術系長文' },
      { key: 'hitotsu',   name: '一橋大学',         cefr: 'B2',    target: '社会科学系・抽象的英文の和訳' },
      { key: 'nagoya',    name: '名古屋大学',       cefr: 'B1-B2', target: '長文+英作のバランス型' },
      // 私立 早慶上智ICU
      { key: 'waseda',    name: '早稲田大学',       cefr: 'B2',    target: '学部別出題傾向 (政経/法/商/文/国際教養)' },
      { key: 'keio',      name: '慶應義塾大学',     cefr: 'B2',    target: '経済学部=英作・SFC=長文・医=医学英文' },
      { key: 'sophia',    name: '上智大学',         cefr: 'B2',    target: '英語重視学部・TEAP活用' },
      { key: 'icu',       name: 'ICU 国際基督教大学', cefr: 'B2-C1', target: 'リベラルアーツ・ATLAS型独自試験' },
      // 私立 MARCH
      { key: 'meiji',     name: '明治大学',         cefr: 'B1-B2', target: '長文+文法+整序の標準型' },
      { key: 'aogaku',    name: '青山学院大学',     cefr: 'B1-B2', target: '英米文学部=高レベル英文' },
      { key: 'rikkyo',    name: '立教大学',         cefr: 'B1-B2', target: '英語自由英作文・全学部統一日程' },
      { key: 'chuo',      name: '中央大学',         cefr: 'B1-B2', target: '法学部=論理的英文・経済=ビジネス系' },
      { key: 'hosei',     name: '法政大学',         cefr: 'B1',    target: '標準的長文+文法' },
      // 関関同立
      { key: 'kandai',    name: '関西大学',         cefr: 'B1',    target: '長文中心・標準難度' },
      { key: 'kangaku',   name: '関西学院大学',     cefr: 'B1-B2', target: '英語独自試験・実用英語重視' },
      { key: 'doshisha',  name: '同志社大学',       cefr: 'B2',    target: '長文+和訳+整序の総合' },
      { key: 'ritsumei',  name: '立命館大学',       cefr: 'B1-B2', target: '英語選択幅広い学部対応' },
      // 医学部
      { key: 'igakubu_kokoritsu',  name: '国公立医学部',   cefr: 'B2-C1', target: '東大理三/京大医/阪大医/慈恵/順天堂等' },
      { key: 'igakubu_shiritsu',   name: '私立医学部',     cefr: 'B2',    target: '東医/日医/慶應医/慈恵/順天堂等' },
      // 共通テスト・センター
      { key: 'kyotsu',    name: '共通テスト',       cefr: 'A2-B2', target: '2021年〜・全国共通・Reading 80分/Listening 60分' },
      { key: 'center',    name: 'センター試験',     cefr: 'A2-B1', target: '2020年廃止・1990-2020年過去問・基礎重視' },
    ],
    // 大学別 part 構造 (主要大学のみ実装、他は generic)
    sectionsByGrade: {
      todai: [
        { key: 'r_long',        name: '長文読解 (大問1A・5)', icon: '📖', timeMin: 25, qCount: 4, scoreMax: 25, desc: '物語/評論/エッセイ系長文 + 内容一致・段落整序' },
        { key: 'r_summary',     name: '要約 (大問1B)',         icon: '📋', timeMin: 15, qCount: 1, scoreMax: 10, desc: '英文を 60-80字で日本語要約' },
        { key: 'w_essay',       name: '自由英作文 (大問2A)',   icon: '✍️', timeMin: 20, qCount: 1, scoreMax: 15, desc: '60-80語の意見論述' },
        { key: 'w_freeform',    name: '形式自由英作文 (大問2B)', icon: '✍️', timeMin: 15, qCount: 1, scoreMax: 10, desc: 'イラスト説明や情景描写' },
        { key: 'l_listening',   name: 'リスニング (大問3)',    icon: '🎧', timeMin: 30, qCount: 15, scoreMax: 30, desc: '対話/講義/Real-Life 各5問' },
        { key: 'r_grammar',     name: '文法整序 (大問4A)',     icon: '🔀', timeMin: 10, qCount: 5, scoreMax: 10, desc: '誤文訂正・並べ替え' },
        { key: 'r_translation', name: '和訳 (大問4B)',         icon: '🇯🇵', timeMin: 15, qCount: 3, scoreMax: 15, desc: '構造把握型の長文部分和訳' },
      ],
      kyodai: [
        { key: 'r_long',        name: '長文読解 (大問1)',  icon: '📖', timeMin: 30, qCount: 5, scoreMax: 30, desc: '抽象的論理的英文 + 要旨把握' },
        { key: 'r_translation', name: '和訳 (大問1・2)',   icon: '🇯🇵', timeMin: 30, qCount: 4, scoreMax: 40, desc: '京大型は長文中の和訳が中心 (1段落丸ごと等)' },
        { key: 'w_essay',       name: '英作文 (大問4)',    icon: '✍️', timeMin: 30, qCount: 1, scoreMax: 30, desc: '日本語の文章を英訳 (新傾向)' },
      ],
      waseda: [
        { key: 'r_long',     name: '長文読解 (政経/法/商等)', icon: '📖', timeMin: 30, qCount: 8, scoreMax: 40, desc: '学部別の出題テーマ' },
        { key: 'r_grammar',  name: '文法・語彙',              icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 20, desc: '4択穴埋め・整序' },
        { key: 'w_essay',    name: '自由英作文 (国際教養等)', icon: '✍️', timeMin: 20, qCount: 1, scoreMax: 20, desc: '100-150語の意見論述' },
      ],
      keio: [
        { key: 'r_long',  name: '長文読解 (経済/商/文)',  icon: '📖', timeMin: 30, qCount: 8, scoreMax: 40, desc: 'やや長めの本格的英文' },
        { key: 'w_essay', name: '英作文 (経済学部)',       icon: '✍️', timeMin: 30, qCount: 1, scoreMax: 25, desc: '120-150語のエッセイ・テーマ重視' },
      ],
      sophia: [
        { key: 'r_long',  name: '長文読解',         icon: '📖', timeMin: 30, qCount: 8, scoreMax: 40, desc: 'TEAP活用も含めた英語重視' },
        { key: 'r_grammar', name: '文法・整序',     icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 20, desc: '4択・整序' },
      ],
      icu: [
        { key: 'r_long',     name: 'ATLAS 長文 (リベラルアーツ)', icon: '📖', timeMin: 30, qCount: 10, scoreMax: 40, desc: 'ICU独自・抽象度高' },
        { key: 'l_listening', name: 'リスニング (講義型)',         icon: '🎧', timeMin: 30, qCount: 10, scoreMax: 30, desc: '長めの講義+設問' },
      ],
      osaka: [
        { key: 'r_long',     name: '長文要旨把握 (大問1)',        icon: '📖', timeMin: 30, qCount: 6, scoreMax: 30, desc: '抽象的英文の主旨をまとめる' },
        { key: 'r_translation', name: '和訳 (大問2)',             icon: '🇯🇵', timeMin: 25, qCount: 3, scoreMax: 25, desc: '構造把握型の長文和訳' },
        { key: 'w_essay',    name: '自由英作文 (大問3)',          icon: '✍️', timeMin: 25, qCount: 1, scoreMax: 25, desc: '70-100語の意見論述' },
      ],
      tokoda: [
        { key: 'r_long',     name: '長文 (理工系)',                icon: '📖', timeMin: 30, qCount: 6, scoreMax: 40, desc: '科学技術・工学系英文 (例: AI/ロボティクス/材料)' },
        { key: 'r_translation', name: '和訳 (技術文)',             icon: '🇯🇵', timeMin: 20, qCount: 3, scoreMax: 25, desc: '専門用語を含む技術英文の和訳' },
        { key: 'w_essay',    name: '英作文 (技術系トピック)',     icon: '✍️', timeMin: 20, qCount: 1, scoreMax: 20, desc: '科学技術系の意見論述' },
      ],
      hitotsu: [
        { key: 'r_long',        name: '長文読解 (社会科学系)',     icon: '📖', timeMin: 30, qCount: 6, scoreMax: 30, desc: '経済/社会/法律の抽象英文' },
        { key: 'r_translation', name: '和訳 (抽象英文)',           icon: '🇯🇵', timeMin: 25, qCount: 3, scoreMax: 30, desc: '関係詞節/分詞構文の構造把握型和訳' },
        { key: 'w_essay',       name: '自由英作文 (商学部頻出)',   icon: '✍️', timeMin: 25, qCount: 1, scoreMax: 20, desc: '100-150語の論述' },
        { key: 'l_listening',   name: 'リスニング (社会学部)',     icon: '🎧', timeMin: 25, qCount: 10, scoreMax: 20, desc: '対話/講義' },
      ],
      nagoya: [
        { key: 'r_long',        name: '長文読解 (大問1・2)',        icon: '📖', timeMin: 35, qCount: 8, scoreMax: 50, desc: '評論/論説系の英文' },
        { key: 'w_essay',       name: '英作文 (大問3)',             icon: '✍️', timeMin: 25, qCount: 1, scoreMax: 30, desc: '自由英作文 (テーマ与えあり)' },
        { key: 'r_translation', name: '和訳',                       icon: '🇯🇵', timeMin: 20, qCount: 3, scoreMax: 20, desc: '長文中の和訳' },
      ],
      igakubu_kokoritsu: [
        { key: 'r_long',        name: '医学/生命科学 長文',         icon: '🩺', timeMin: 30, qCount: 6, scoreMax: 40, desc: 'CRISPR/iPS/ゲノム/感染症/疫学などの英文' },
        { key: 'r_translation', name: '医学英文 和訳',              icon: '🇯🇵', timeMin: 25, qCount: 3, scoreMax: 30, desc: '医学論文型の構造把握和訳' },
        { key: 'w_essay',       name: '医療倫理 英作文',            icon: '✍️', timeMin: 25, qCount: 1, scoreMax: 30, desc: '医療倫理/AI診断/遺伝子治療等のテーマ' },
        { key: 'l_listening',   name: '面接英語 (二次面接対策)',   icon: '🎧', timeMin: 15, qCount: 5, scoreMax: 0, desc: '医学部二次面接で問われる英語Q&A' },
      ],
      igakubu_shiritsu: [
        { key: 'r_long',        name: '医療系 長文 (慈恵/順天/日医)', icon: '🩺', timeMin: 30, qCount: 8, scoreMax: 50, desc: '医療現場/疾患/薬学/公衆衛生' },
        { key: 'r_grammar',     name: '医療系 文法・語彙',          icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 20, desc: '医学英語の語彙穴埋め (4択)' },
        { key: 'w_essay',       name: '英作文',                     icon: '✍️', timeMin: 20, qCount: 1, scoreMax: 20, desc: '70-100語の意見論述 (医療テーマ)' },
      ],
      meiji: [
        { key: 'r_long',     name: '長文読解 (大問1・2)',          icon: '📖', timeMin: 30, qCount: 10, scoreMax: 50, desc: '社会/科学/文化系の英文' },
        { key: 'r_grammar',  name: '文法・語彙・整序 (大問3-4)',   icon: '🔀', timeMin: 20, qCount: 15, scoreMax: 30, desc: '4択穴埋め+整序' },
        { key: 'r_translation', name: '和訳',                      icon: '🇯🇵', timeMin: 10, qCount: 2, scoreMax: 20, desc: '長文中の部分和訳' },
      ],
      aogaku: [
        { key: 'r_long',     name: '長文読解 (英米文学部=高難度)', icon: '📖', timeMin: 30, qCount: 8, scoreMax: 50, desc: '文学/論説系の英文' },
        { key: 'r_grammar',  name: '文法・語法',                   icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 25, desc: '4択・整序' },
        { key: 'w_essay',    name: '英作文',                       icon: '✍️', timeMin: 20, qCount: 1, scoreMax: 25, desc: '自由英作文' },
      ],
      rikkyo: [
        { key: 'r_long',     name: '長文読解 (全学部統一日程型)',   icon: '📖', timeMin: 30, qCount: 8, scoreMax: 50, desc: '評論/物語/エッセイ系' },
        { key: 'w_essay',    name: '英語自由英作文',                icon: '✍️', timeMin: 25, qCount: 1, scoreMax: 30, desc: '立教型 (テーマ自由度高め)' },
        { key: 'r_grammar',  name: '文法・語彙',                    icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 20, desc: '4択穴埋め' },
      ],
      chuo: [
        { key: 'r_long',     name: '長文読解 (法学部=論理重視)',    icon: '📖', timeMin: 30, qCount: 8, scoreMax: 50, desc: '法律/政治/経済の論理的英文' },
        { key: 'r_grammar',  name: '文法・整序',                    icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 25, desc: '4択+整序' },
        { key: 'r_translation', name: '和訳 (法学部)',             icon: '🇯🇵', timeMin: 15, qCount: 3, scoreMax: 25, desc: '法律英語の構造把握和訳' },
      ],
      hosei: [
        { key: 'r_long',     name: '長文読解',                      icon: '📖', timeMin: 25, qCount: 8, scoreMax: 50, desc: '標準的英文・各学部共通' },
        { key: 'r_grammar',  name: '文法・語彙',                    icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 25, desc: '4択穴埋め' },
        { key: 'w_essay',    name: '英作文 (一部学部)',             icon: '✍️', timeMin: 15, qCount: 1, scoreMax: 25, desc: '基礎的な意見論述' },
      ],
      doshisha: [
        { key: 'r_long',        name: '長文読解 (大問1・2)',         icon: '📖', timeMin: 35, qCount: 10, scoreMax: 50, desc: '評論/エッセイ系・やや長め' },
        { key: 'r_grammar',     name: '整序 (大問3)',                icon: '🔀', timeMin: 15, qCount: 5, scoreMax: 20, desc: '同志社型整序問題' },
        { key: 'r_translation', name: '和訳',                        icon: '🇯🇵', timeMin: 15, qCount: 3, scoreMax: 30, desc: '長文中の部分和訳' },
      ],
      kangaku: [
        { key: 'r_long',     name: '長文読解 (実用英語重視)',       icon: '📖', timeMin: 30, qCount: 10, scoreMax: 60, desc: '実用的なテーマの英文' },
        { key: 'r_grammar',  name: '文法・語彙',                    icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 20, desc: '4択穴埋め' },
        { key: 'w_essay',    name: '英作文',                        icon: '✍️', timeMin: 15, qCount: 1, scoreMax: 20, desc: '英文要約 or 短い意見論述' },
      ],
      ritsumei: [
        { key: 'r_long',     name: '長文読解',                      icon: '📖', timeMin: 30, qCount: 10, scoreMax: 50, desc: '英語選択幅広い学部対応' },
        { key: 'r_grammar',  name: '文法・整序',                    icon: '🔀', timeMin: 15, qCount: 12, scoreMax: 25, desc: '4択+整序' },
        { key: 'w_essay',    name: '英作文 (一部学部)',             icon: '✍️', timeMin: 15, qCount: 1, scoreMax: 25, desc: '自由英作文' },
      ],
      kandai: [
        { key: 'r_long',     name: '長文読解 (関大型)',             icon: '📖', timeMin: 30, qCount: 10, scoreMax: 60, desc: '長文中心・標準難度' },
        { key: 'r_grammar',  name: '文法・語彙・整序',              icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 20, desc: '4択穴埋め+整序' },
        { key: 'r_translation', name: '和訳',                       icon: '🇯🇵', timeMin: 15, qCount: 2, scoreMax: 20, desc: '部分和訳' },
      ],
      kyotsu: [
        { key: 'r_short',     name: 'Reading 大問1-3 (短文中心)',   icon: '📝', timeMin: 25, qCount: 15, scoreMax: 30, desc: '広告/Eメール/SNS/レビュー 等の実用英語' },
        { key: 'r_long',      name: 'Reading 大問4-6 (長文)',        icon: '📖', timeMin: 55, qCount: 20, scoreMax: 70, desc: '記事/学術/物語 等の長文' },
        { key: 'l_part1_2',   name: 'Listening 大問1-2 (短い対話)',  icon: '💬', timeMin: 15, qCount: 10, scoreMax: 25, desc: '日常会話の聞き取り' },
        { key: 'l_part3_4',   name: 'Listening 大問3-4 (長い対話)',  icon: '🎙', timeMin: 25, qCount: 12, scoreMax: 35, desc: '討論/講義' },
        { key: 'l_part5_6',   name: 'Listening 大問5-6 (講義+討論)', icon: '🎓', timeMin: 20, qCount: 8, scoreMax: 40, desc: 'グラフ含む情報統合型' },
      ],
      center: [
        { key: 'r_grammar',   name: '発音・アクセント・文法 (大問1-3)', icon: '📝', timeMin: 25, qCount: 20, scoreMax: 50, desc: '2020年廃止のセンター型・基礎重視' },
        { key: 'r_long',      name: '長文読解 (大問4-6)',               icon: '📖', timeMin: 50, qCount: 20, scoreMax: 100, desc: 'グラフ/評論/物語の3題' },
        { key: 'l_listening', name: 'リスニング',                       icon: '🎧', timeMin: 30, qCount: 25, scoreMax: 50, desc: '日常会話/講義 (大問1-4)' },
      ],
      // 他大学のデフォルト (汎用 4 part)
      _default: [
        { key: 'r_long',        name: '長文読解',     icon: '📖', timeMin: 30, qCount: 8, scoreMax: 40, desc: '大学別の出題傾向に応じた長文' },
        { key: 'r_grammar',     name: '文法・語法',   icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 20, desc: '4択穴埋め・整序' },
        { key: 'r_translation', name: '和訳',         icon: '🇯🇵', timeMin: 15, qCount: 3, scoreMax: 15, desc: '英文の部分和訳' },
        { key: 'w_essay',       name: '英作文',       icon: '✍️', timeMin: 20, qCount: 1, scoreMax: 15, desc: '自由英作文 or 和文英訳' },
      ],
    },
    topics: ['Climate change', 'AI ethics', 'Education reform', 'Globalization', 'Aging society', 'Mental health', 'Gender equality', 'Technology impact', 'Cultural identity'],
  },

  // 🔬 理系科目 (数学/物理/化学/生物/地学) — KaTeX 数式 + SVG 図表対応
  rikei: {
    id: 'rikei',
    name: '理系科目',
    flag: '🔬',
    color: '#10b981',
    scoreMin: 0, scoreMax: 100, scoreUnit: '点',
    requiresGrade: true,  // 大学/レベル選択を挟む
    grades: [
      // 共通テスト・基礎
      { key: 'kyotsu_rikei', name: '共通テスト 理系',  cefr: '基礎',   target: '共通テスト 数学IA/IIB・物理基礎/化学基礎/生物基礎/地学基礎' },
      // 国公立トップ
      { key: 'todai_rikei',   name: '東京大学 理系',    cefr: '最難関', target: '東大 数学(理系)・物理・化学・生物' },
      { key: 'kyodai_rikei',  name: '京都大学 理系',    cefr: '最難関', target: '京大 数学(理系)・物理・化学・生物' },
      { key: 'osaka_rikei',   name: '大阪大学 理系',    cefr: '難関',   target: '阪大 理系 (理工/医)' },
      { key: 'tokoda_rikei',  name: '東京工業大学',     cefr: '難関',   target: '東工大 数学/物理/化学 (情報・電気・機械系)' },
      { key: 'nagoya_rikei',  name: '名古屋大学 理系',  cefr: '難関',   target: '名大 理系' },
      // 私立 早慶上智
      { key: 'waseda_rikei',  name: '早稲田大学 理工',  cefr: '上級',   target: '早稲田 基幹/創造/先進理工' },
      { key: 'keio_rikei',    name: '慶應義塾大学 理工/医', cefr: '上級', target: '慶應 理工・医・看護医療' },
      { key: 'sophia_rikei',  name: '上智大学 理工',    cefr: '上級',   target: '上智 理工 (機能創造・情報理工)' },
      // 医学部
      { key: 'igakubu_kokoritsu_rikei', name: '国公立医学部', cefr: '最難関', target: '東大理三/京大医/阪大医/医歯/慈恵 等' },
      { key: 'igakubu_shiritsu_rikei',  name: '私立医学部',   cefr: '上級',   target: '東医/日医/慶應医/慈恵/順天堂 等' },
      // MARCH 理工
      { key: 'march_rikei',   name: 'MARCH 理工',      cefr: '中上級', target: '明治/青学/立教/中央/法政 理工系' },
    ],
    sectionsByGrade: {
      // 共通テスト 理系: 数IA/IIB + 物理/化学/生物/地学 基礎
      kyotsu_rikei: [
        { key: 'math_1a',     name: '数学 IA (大問1-5)',      icon: '📐', timeMin: 70, qCount: 8, scoreMax: 100, desc: '二次関数・図形と計量・データ・確率・整数' },
        { key: 'math_2b',     name: '数学 IIB (大問1-5)',     icon: '📐', timeMin: 70, qCount: 8, scoreMax: 100, desc: '三角関数・指数対数・微積・数列・ベクトル' },
        { key: 'phys_basic',  name: '物理基礎',               icon: '⚛️', timeMin: 30, qCount: 5, scoreMax: 50, desc: '力学・熱・波・電気の基礎' },
        { key: 'chem_basic',  name: '化学基礎',               icon: '🧪', timeMin: 30, qCount: 5, scoreMax: 50, desc: '物質量・酸塩基・酸化還元の基礎' },
        { key: 'bio_basic',   name: '生物基礎',               icon: '🧬', timeMin: 30, qCount: 5, scoreMax: 50, desc: '細胞・遺伝・生態系の基礎' },
        { key: 'earth_basic', name: '地学基礎',               icon: '🌍', timeMin: 30, qCount: 5, scoreMax: 50, desc: '地球・宇宙・地震・気象の基礎' },
      ],
      // 東大 理系: 数学+物理+化学+生物 (各 大問構成)
      todai_rikei: [
        { key: 'math_q1', name: '数学 大問1',  icon: '📐', timeMin: 30, qCount: 1, scoreMax: 20, desc: '微積分/数列/確率 等の融合問題' },
        { key: 'math_q2', name: '数学 大問2',  icon: '📐', timeMin: 30, qCount: 1, scoreMax: 20, desc: '図形と方程式/ベクトル/複素数平面' },
        { key: 'math_q3', name: '数学 大問3',  icon: '📐', timeMin: 30, qCount: 1, scoreMax: 20, desc: '微積分/極限の応用' },
        { key: 'phys_q1', name: '物理 大問1 (力学)', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 20, desc: '剛体/単振動/万有引力 等' },
        { key: 'phys_q2', name: '物理 大問2 (電磁気)', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 20, desc: '回路/電磁誘導/コイル' },
        { key: 'phys_q3', name: '物理 大問3 (波/熱)', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 20, desc: '光波/音波/熱力学' },
        { key: 'chem_q1', name: '化学 大問1 (理論)', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 20, desc: '熱化学/平衡/電気化学' },
        { key: 'chem_q2', name: '化学 大問2 (無機)', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 20, desc: '無機物質/沈殿反応/錯体' },
        { key: 'chem_q3', name: '化学 大問3 (有機)', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 20, desc: '構造決定/高分子' },
      ],
      // 京大 理系: シンプル (大問少なめ・記述深掘り)
      kyodai_rikei: [
        { key: 'math_q1', name: '数学 大問1',  icon: '📐', timeMin: 30, qCount: 1, scoreMax: 30, desc: '骨太な解析・抽象的思考' },
        { key: 'math_q2', name: '数学 大問2',  icon: '📐', timeMin: 30, qCount: 1, scoreMax: 30, desc: '京大型 整数論・確率' },
        { key: 'phys_q1', name: '物理 (力学)',  icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 30, desc: '記述重視・物理的考察' },
        { key: 'phys_q2', name: '物理 (電磁気)', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 30, desc: '回路・磁場・電磁誘導' },
        { key: 'chem_q1', name: '化学 (理論+無機)', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 30, desc: '京大型 反応速度/平衡' },
        { key: 'chem_q2', name: '化学 (有機)', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 30, desc: '構造推定・合成経路' },
      ],
      // 国公立医学部
      igakubu_kokoritsu_rikei: [
        { key: 'math_q1',  name: '数学 大問1', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 25, desc: '医学部レベルの解析・確率' },
        { key: 'math_q2',  name: '数学 大問2', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 25, desc: 'ベクトル/複素数/数列' },
        { key: 'phys_q1',  name: '物理 (力学)', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 25, desc: '医学部頻出: 振動/円運動' },
        { key: 'chem_q1',  name: '化学 (理論)', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 25, desc: '反応熱/電気分解/平衡' },
        { key: 'bio_q1',   name: '生物 (生化学/医学)', icon: '🧬', timeMin: 30, qCount: 1, scoreMax: 25, desc: 'DNA/タンパク質/免疫/代謝' },
      ],
      // 東工大 (情報・電気重視)
      tokoda_rikei: [
        { key: 'math_q1',  name: '数学 大問1', icon: '📐', timeMin: 35, qCount: 1, scoreMax: 30, desc: '微積分の応用・極限' },
        { key: 'math_q2',  name: '数学 大問2', icon: '📐', timeMin: 35, qCount: 1, scoreMax: 30, desc: 'ベクトル/行列/複素数' },
        { key: 'phys_q1',  name: '物理 (電磁気)', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 30, desc: '工学系: 回路解析・コイル' },
        { key: 'phys_q2',  name: '物理 (力学)',  icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 30, desc: '剛体/振動/慣性モーメント' },
        { key: 'chem_q1',  name: '化学 (材料系)', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 30, desc: '材料/触媒/工業化学' },
      ],
      // 早慶上智 理系
      waseda_rikei: [
        { key: 'math_q1',  name: '数学 大問1', icon: '📐', timeMin: 25, qCount: 1, scoreMax: 25, desc: '基幹/創造/先進理工 数学' },
        { key: 'math_q2',  name: '数学 大問2', icon: '📐', timeMin: 25, qCount: 1, scoreMax: 25, desc: '微積/ベクトル/数列' },
        { key: 'phys_q1',  name: '物理 大問1', icon: '⚛️', timeMin: 25, qCount: 1, scoreMax: 25, desc: '力学/電磁気' },
        { key: 'chem_q1',  name: '化学 大問1', icon: '🧪', timeMin: 25, qCount: 1, scoreMax: 25, desc: '理論/有機 標準型' },
      ],
      keio_rikei: [
        { key: 'math_q1',  name: '数学 大問1', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 30, desc: '理工/医 数学' },
        { key: 'math_q2',  name: '数学 大問2', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 30, desc: '微積分/数列' },
        { key: 'phys_q1',  name: '物理 大問1', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 25, desc: '理工 物理' },
        { key: 'chem_q1',  name: '化学 大問1', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 25, desc: '理工 化学' },
        { key: 'bio_q1',   name: '生物 (医学部)', icon: '🧬', timeMin: 30, qCount: 1, scoreMax: 25, desc: '医学部 生物' },
      ],
      // 汎用 (デフォルト)
      _default: [
        { key: 'math_basic',   name: '数学 (基礎演習)', icon: '📐', timeMin: 25, qCount: 5, scoreMax: 50, desc: '微積分/ベクトル/確率/数列' },
        { key: 'phys_basic_q', name: '物理 (基礎演習)', icon: '⚛️', timeMin: 25, qCount: 5, scoreMax: 50, desc: '力学/電磁気/波動/熱' },
        { key: 'chem_basic_q', name: '化学 (基礎演習)', icon: '🧪', timeMin: 25, qCount: 5, scoreMax: 50, desc: '理論/無機/有機' },
        { key: 'bio_basic_q',  name: '生物 (基礎演習)', icon: '🧬', timeMin: 25, qCount: 5, scoreMax: 50, desc: '細胞/遺伝/生態' },
      ],
    },
    topics: ['二次関数', '微積分', 'ベクトル', '確率', '整数', '力学', '電磁気', '波動', '熱力学', '化学平衡', '酸化還元', '有機化学', '遺伝子発現', '生態系'],
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

// 大学入試: 大学から sections を取得 (大学別の出題形式 / 未定義は _default 汎用4 part)
function getDaigakuSections(univKey) {
  const map = EXAMS.daigaku.sectionsByGrade;
  return map[univKey] || map._default;
}

// 🔬 理系: 大学/レベルから sections を取得
function getRikeiSections(gradeKey) {
  const map = EXAMS.rikei.sectionsByGrade;
  return map[gradeKey] || map._default;
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

function showGradePicker(examId = 'eiken') {
  document.getElementById('examPickSection').style.display = 'none';
  document.getElementById('examDetailSection').style.display = 'none';
  document.getElementById('gradePickSection').style.display = '';
  const exam = EXAMS[examId];
  // 見出しを試験別に切替
  const head = document.querySelector('#gradePickSection .ee-section-head');
  if (head) {
    const eyebrow = head.querySelector('.ee-eyebrow');
    const h2 = head.querySelector('h2');
    const desc = head.querySelector('.ee-section-desc');
    if (examId === 'daigaku') {
      if (eyebrow) eyebrow.textContent = 'STEP 2 / 大学入試';
      if (h2) h2.textContent = '🎓 受験する大学を選んでください';
      if (desc) desc.textContent = '大学ごとの出題傾向 (長文/和訳/英作/要約) と過去問形式に完全準拠。共通テスト・センター試験 (2005年〜) も網羅。';
    } else if (examId === 'rikei') {
      if (eyebrow) eyebrow.textContent = 'STEP 2 / 理系科目';
      if (h2) h2.textContent = '🔬 大学/レベルを選んでください';
      if (desc) desc.textContent = '大学ごとの数学/物理/化学/生物の出題傾向に準拠。図やグラフ・数式 (LaTeX) を含む本格問題を AI が即時生成。';
    } else {
      if (eyebrow) eyebrow.textContent = 'STEP 2 / 英検';
      if (h2) h2.textContent = '🇯🇵 受験する級を選んでください';
      if (desc) desc.textContent = '級ごとに part 構成・配点・難易度が異なります。各 part 個別対策が可能です。';
    }
  }
  const grid = document.getElementById('gradeGrid');
  grid.innerHTML = '';
  const items = exam.grades || EXAMS.eiken.grades;
  items.forEach(g => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'grade-card';
    btn.dataset.grade = g.key;
    if (examId === 'daigaku') {
      // 大学カテゴリ別バッジ (国公立/私立/医学部/共通テスト)
      const k = g.key;
      let badge = '私立';
      let badgeColor = '#6366f1';
      if (['todai','kyodai','osaka','tokoda','hitotsu','nagoya'].includes(k)) { badge = '国公立'; badgeColor = '#0ea5e9'; }
      else if (['igakubu_kokoritsu','igakubu_shiritsu'].includes(k)) { badge = '医学部'; badgeColor = '#dc2626'; }
      else if (k === 'kyotsu') { badge = '共通テスト'; badgeColor = '#10b981'; }
      else if (k === 'center') { badge = 'センター試験'; badgeColor = '#94a3b8'; }
      btn.innerHTML = `
        <span class="grade-card-secondary" style="background:${badgeColor}1a;color:${badgeColor};">${badge}</span>
        <div class="grade-card-name">${escapeHtml(g.name)}</div>
        <div class="grade-card-cefr">CEFR ${escapeHtml(g.cefr)} 相当</div>
        <div class="grade-card-target">${escapeHtml(g.target)}</div>
      `;
      btn.addEventListener('click', () => {
        state.eikenGrade = g.key;       // 互換: section 取得時の汎用「級キー」として共有
        state.eikenGradeName = g.name;
        pickExamSections('daigaku');
      });
    } else if (examId === 'rikei') {
      const k = g.key;
      let badge = '私立';
      let badgeColor = '#6366f1';
      if (['todai_rikei','kyodai_rikei','osaka_rikei','tokoda_rikei','nagoya_rikei'].includes(k)) { badge = '国公立'; badgeColor = '#0ea5e9'; }
      else if (['igakubu_kokoritsu_rikei','igakubu_shiritsu_rikei'].includes(k)) { badge = '医学部'; badgeColor = '#dc2626'; }
      else if (k === 'kyotsu_rikei') { badge = '共通テスト'; badgeColor = '#10b981'; }
      else if (k === 'march_rikei') { badge = 'MARCH'; badgeColor = '#a78bfa'; }
      btn.innerHTML = `
        <span class="grade-card-secondary" style="background:${badgeColor}1a;color:${badgeColor};">${badge}</span>
        <div class="grade-card-name">${escapeHtml(g.name)}</div>
        <div class="grade-card-cefr">${escapeHtml(g.cefr)}</div>
        <div class="grade-card-target">${escapeHtml(g.target)}</div>
      `;
      btn.addEventListener('click', () => {
        state.eikenGrade = g.key;
        state.eikenGradeName = g.name;
        pickExamSections('rikei');
      });
    } else {
      const hasSecondary = g.key === 'g1' || g.key === 'gp1' || g.key === 'g2' || g.key === 'gp2' || g.key === 'g3';
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
    }
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
  // 英検 / 大学入試 は級・大学選択を先に挟む (requiresGrade=true)
  if (exam.requiresGrade) {
    showGradePicker(examId);
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
  const gradeLabel = ((examId === 'eiken' || examId === 'daigaku') && state.eikenGradeName) ? ` ${state.eikenGradeName}` : '';
  document.getElementById('examDetailTitle').textContent = `${exam.flag} ${exam.name}${gradeLabel} 対策`;

  // 説明文
  let desc = '';
  if (examId === 'daigaku') {
    desc = `${state.eikenGradeName || '大学入試'} の出題傾向に完全準拠 (2005年〜2026年・21年分の過去問パターンを学習済み)・大問別個別対策`;
  } else if (exam.scoreMax) {
    desc = `スコア範囲: ${exam.scoreMin}〜${exam.scoreMax}${exam.scoreUnit}・出題形式は公式準拠`;
  } else if (exam.grades) {
    desc = `7段階の級別 (5級〜1級) を完全カバー・出題形式は公式準拠`;
  }
  document.getElementById('examDetailDesc').textContent = desc;

  // 目標スコアのプレースホルダ
  const ts = document.getElementById('targetScore');
  ts.placeholder = exam.id === 'toefl' ? '例: 100' : exam.id === 'toeic' ? '例: 800' : exam.id === 'ielts' ? '例: 7.0' : exam.id === 'daigaku' ? '例: 80' : '例: 準1級';
  document.getElementById('targetScoreHint').textContent = exam.id === 'eiken'
    ? '受験する級を入力 (例: 準1級)'
    : exam.id === 'daigaku'
      ? '目標得点率/換算点 (大学・年度により配点異なる)'
      : `${exam.scoreMin}〜${exam.scoreMax}${exam.scoreUnit}`;

  // セクションカード生成 (英検は級別、大学入試・理系は大学別の sectionsByGrade を使う)
  const sections = (examId === 'eiken' && state.eikenGrade)
    ? getEikenSections(state.eikenGrade)
    : (examId === 'daigaku' && state.eikenGrade)
      ? getDaigakuSections(state.eikenGrade)
      : (examId === 'rikei' && state.eikenGrade)
        ? getRikeiSections(state.eikenGrade)
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
// バックエンドから DB蓄積問題を取得して AUTO_GENERATED_BANKS にセット
async function prefetchAutoGenerated(examId, sectionKey, eikenGrade) {
  try {
    const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
      ? 'http://localhost:8000' : window.location.origin;
    const params = new URLSearchParams({ exam: examId, part: sectionKey, limit: 20 });
    if (eikenGrade) params.set('eiken_grade', eikenGrade);
    if (examId === 'daigaku' && eikenGrade) params.set('univ', eikenGrade);
    const res = await fetch(`${backend}/api/exam-questions/bank?` + params);
    if (!res.ok) return;
    const data = await res.json();
    if (!data.selected) return;
    window.AUTO_GENERATED_BANKS = window.AUTO_GENERATED_BANKS || {};
    window.AUTO_GENERATED_BANKS[examId] = window.AUTO_GENERATED_BANKS[examId] || {};
    // 英検 / 大学入試 は compoundKey で保存
    const storeKey = ((examId === 'eiken' || examId === 'daigaku') && eikenGrade) ? `${eikenGrade}_${sectionKey}` : sectionKey;
    window.AUTO_GENERATED_BANKS[examId][storeKey] = data.selected;
    console.log(`[exam] Loaded ${data.count} AI-generated questions for ${examId}/${storeKey}`);
  } catch (e) {
    console.warn('[exam] Failed to prefetch auto-generated bank:', e);
  }
}

async function generateAndShowQuestions(exam, section, full = false) {
  // バックエンド DB から最新の AI生成問題を取得 (非同期で並行)
  prefetchAutoGenerated(exam.id, section.key, state.eikenGrade);
  // 問題数: ユーザー設定 (5/10/15/20/公式どおり) を優先・上限は section の公式数または 30
  // ブラウザ実行で重くなりすぎない範囲で生徒が選択可能
  const userPref = getUserQCountPref(); // null = 公式問題数そのまま
  const officialCount = section.qCount || 5;
  const requested = userPref == null ? officialCount : userPref;
  const qCount = Math.max(1, Math.min(requested, officialCount, 30)); // hard cap 30
  const topic = exam.topics[Math.floor(Math.random() * exam.topics.length)];

  // part 別のジャンル/形式ヒント
  const isReading = /^r_/.test(section.key) || section.key === 'reading';
  const isListening = /^l_/.test(section.key) || section.key === 'listening';
  const isSpeaking = /^s_/.test(section.key) || section.key === 'speaking';
  const isWriting = /^w_/.test(section.key) || section.key === 'writing';

  // 英検級 / 大学入試 ラベル
  let eikenGradeLabel = '';
  if (state.examId === 'eiken' && state.eikenGradeName) {
    eikenGradeLabel = `（${state.eikenGradeName}・CEFR ${(EXAMS.eiken.grades.find(g => g.key === state.eikenGrade) || {}).cefr || ''} 相当）`;
  } else if (state.examId === 'daigaku' && state.eikenGradeName) {
    eikenGradeLabel = `（${state.eikenGradeName}・CEFR ${(EXAMS.daigaku.grades.find(g => g.key === state.eikenGrade) || {}).cefr || ''} 相当）`;
  } else if (state.examId === 'rikei' && state.eikenGradeName) {
    eikenGradeLabel = `（${state.eikenGradeName}・${(EXAMS.rikei.grades.find(g => g.key === state.eikenGrade) || {}).cefr || ''}）`;
  }

  // 大学入試: ランダムに 2005-2026 の年度を選んで「○○大学 ○年度入試の類題」スタイルで生成
  const daigakuYear = (state.examId === 'daigaku' || state.examId === 'rikei') ? (2005 + Math.floor(Math.random() * 22)) : null;

  // 試験別の出題ニュアンス
  const daigakuUniv = state.examId === 'daigaku' ? (state.eikenGradeName || '大学入試') : '';
  const daigakuTargets = state.examId === 'daigaku' ? ((EXAMS.daigaku.grades.find(g => g.key === state.eikenGrade) || {}).target || '') : '';
  const rikeiUniv = state.examId === 'rikei' ? (state.eikenGradeName || '大学入試 理系') : '';
  const rikeiTargets = state.examId === 'rikei' ? ((EXAMS.rikei.grades.find(g => g.key === state.eikenGrade) || {}).target || '') : '';
  // 科目判定 (section.key の prefix から: math_/phys_/chem_/bio_/earth_)
  const subjectMap = { math: '数学', phys: '物理', chem: '化学', bio: '生物', earth: '地学' };
  const subjectKey = (section.key.match(/^(math|phys|chem|bio|earth)/) || [])[1] || '';
  const rikeiSubject = subjectMap[subjectKey] || '理系';
  const examFlavor = {
    toefl: '英語圏大学院・学部留学。Reading/Listening は学術 (lecture, journal article 風)。Speaking/Writing は明確なテンプレ運用が高得点の鍵。',
    toeic: 'ビジネス英語。実務シーン (会議/メール/出張/契約) のみ。難解な学術語彙NG。Part固有の典型パターンを必ず再現。',
    ielts: '英国系学術。Reading は T/F/NG・見出し選択など IELTS 独自形式。Writing Task 1 はデータ描写、Task 2 はエッセイで構造重視。Speaking Part 2 は1分準備→2分独白の独特形式。',
    eiken: `日本英検 ${state.eikenGradeName || ''}${eikenGradeLabel ? '' : ''}。級ごとに語彙難易度が大きく異なる。新形式 (2024〜): 準1級以下は要約/Eメール返信が追加。二次は面接形式 (1-3級)。日本人受験者の弱点 (冠詞/前置詞/イディオム) を踏まえて出題。`,
    daigaku: `日本の大学入試英語 (${daigakuUniv}・${daigakuYear || 2024}年度入試レベル相当)。出題傾向: ${daigakuTargets}。
重要原則:
- 過去問の丸写しは著作権上 NG。「${daigakuUniv} ${daigakuYear || 2024}年度の出題形式に完全準拠した類題」を作成すること (テーマ・難度・形式は本物の過去問と同等)。
- 2005年〜現在 (21年分) の出題傾向を踏まえる: 時事性 (AI/環境/格差/感染症/ジェンダー)・古典的論題 (記憶/言語/科学哲学/教育)・物語/エッセイ系を年度に応じて織り交ぜる。
- 日本人受験生の典型的弱点 (冠詞・関係詞節・分詞構文・無生物主語の和訳) を必ず踏まえた解説。
- 共通テストは 2021年〜 (実用英語重視・複数情報源統合)、センター試験は 1990-2020 (発音/アクセント/文法問題が大問1-3に出題)。
- 東大型は構造把握型和訳/要約 60-80字、京大型は段落丸ごとの和訳、早慶型は学部別テーマ、医学部型は医学/生命科学系英文。`,
    rikei: `日本の大学入試 理系科目 (${rikeiUniv}・${rikeiSubject}・${daigakuYear || 2024}年度入試レベル相当)。出題傾向: ${rikeiTargets}。
重要原則:
- 過去問の丸写しは著作権上 NG。「${rikeiUniv} ${daigakuYear || 2024}年度の${rikeiSubject}の出題形式に完全準拠した類題」を作成すること。
- **必ず数式は LaTeX 構文** で出力 (\\(x^2 + y^2 = r^2\\) のインライン形式・\\[\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}\\] のディスプレイ形式)。フロントは KaTeX で自動レンダリング。
- **図やグラフが必要な問題は figure_svg フィールドに inline SVG を出力** (viewBox 0 0 400 300 推奨・stroke="white" stroke-width="2" fill="none"・暗背景に映える色)。<script> タグや on* 属性は禁止 (XSS)。
  - 数学: 関数のグラフ (放物線/三角関数/円・座標軸)・図形問題 (三角形/円/立体)・ベクトル (矢印)
  - 物理: 力の図 (矢印 + 物体)・回路 (抵抗・電池・コンデンサ記号)・運動軌道・波形
  - 化学: 構造式 (Skeletal formula)・実験装置・反応式
  - 生物: 細胞模式図・遺伝子発現フロー・代謝経路
- ${rikeiSubject} 特有の頻出パターン: ${
      rikeiSubject === '数学' ? '微積分(極限/連続性)・ベクトル・確率(条件付/独立)・整数論・複素数平面・図形と方程式。京大型なら抽象的・東大型なら計算量多め。'
      : rikeiSubject === '物理' ? '力学(運動方程式/エネルギー保存/円運動/単振動)・電磁気(キルヒホッフ/誘導起電力)・波動(干渉/反射屈折)・熱力学(状態方程式/熱効率)。図解必須。'
      : rikeiSubject === '化学' ? '理論化学(平衡定数/反応速度/熱化学)・無機(沈殿生成/錯体)・有機(構造決定/反応経路/高分子)。構造式 SVG 必須。'
      : rikeiSubject === '生物' ? '遺伝(メンデル/連鎖/分子遺伝)・代謝(光合成/呼吸/酵素)・神経/筋肉・進化・生態系。模式図あれば SVG。'
      : '地学(地震波/プレート/天体運動/気象)。図やグラフ必須。'
    }
- 解答は記述式 (途中式 + 計算過程 + 答え) または 4択 (プレ計算済み)。choices には LaTeX を使う。
- 解説は日本語で「考え方→立式→計算→答え→補足」を必ず段階分け (3行以上)。`,
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
  "passage": "(Reading の場合は本文、それ以外は空文字。理系の場合は前提条件・問題設定の文章)",
  "audio_script": "(Listening の場合はスクリプト、それ以外は空文字)",
  "prompt": "(Speaking/Writing の場合の英語の出題文、それ以外は空文字)",
  "figure_svg": "(理系で図/グラフ/構造式が必要な時のみ inline SVG 文字列。<svg viewBox=\\"0 0 400 300\\" xmlns=\\"http://www.w3.org/2000/svg\\">...</svg> 形式。<script> や on* 属性は禁止)",
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice|short_answer|essay|speaking",
      "stem": "問題文 (理系の数式は LaTeX: \\\\(x^2\\\\) インライン / \\\\[\\\\int_0^1 f(x)dx\\\\] ディスプレイ)",
      "choices": ["A", "B", "C", "D"],
      "answer": "正解(選択肢index 0始まり、または模範解答テキスト・記述式は完全解答)",
      "explanation": "解説 (日本語、3行以上、LaTeX 数式可)"
    }
  ]
}
Speaking/Writing の場合: choices=[], answer に模範解答テキスト全文, type="essay" or "speaking"。
理系の場合: 数式はすべて LaTeX 構文。図が必要なら figure_svg に SVG を必ず入れる (空文字 NG)。`;

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
    state.figureSvg = payload.figure_svg || '';
    state.warning = payload._warning || '';  // フォールバック警告 (偽問題なし設計)
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

// ==========================================================================
// ⚙️ 学習設定 (問題数・即時採点モード) - localStorage 永続化
// ==========================================================================
const QPREF_KEY = 'ee_qpref_v1';
function getUserQCountPref() {
  try { return JSON.parse(localStorage.getItem(QPREF_KEY) || 'null')?.qCount ?? null; } catch { return null; }
}
function getUserInstantPref() {
  try { return !!JSON.parse(localStorage.getItem(QPREF_KEY) || 'null')?.instant; } catch { return false; }
}
function saveUserPref(patch) {
  let cur = {};
  try { cur = JSON.parse(localStorage.getItem(QPREF_KEY) || '{}'); } catch {}
  Object.assign(cur, patch);
  localStorage.setItem(QPREF_KEY, JSON.stringify(cur));
}

// 🛡️ SVG sanitizer (XSS 防止): <script>, on*, javascript: を除去
function sanitizeSvg(svgStr) {
  if (typeof svgStr !== 'string' || !svgStr.trim()) return '';
  // <svg ...> から始まらない場合は無視
  if (!/^\s*<svg[\s>]/.test(svgStr)) return '';
  // 既知の危険パターンを除去
  let s = svgStr;
  s = s.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  s = s.replace(/\s+on[a-z]+\s*=\s*"[^"]*"/gi, '');
  s = s.replace(/\s+on[a-z]+\s*=\s*'[^']*'/gi, '');
  s = s.replace(/\s+on[a-z]+\s*=\s*[^\s>]+/gi, '');
  s = s.replace(/javascript:/gi, '');
  s = s.replace(/<foreignObject\b[\s\S]*?<\/foreignObject>/gi, '');
  return s;
}

// 🧮 KaTeX で要素内の数式を自動レンダリング (CDN ロード後に呼出)
function applyKatex(rootEl) {
  if (!rootEl || typeof window.renderMathInElement !== 'function') return;
  try {
    window.renderMathInElement(rootEl, {
      delimiters: [
        { left: '\\[', right: '\\]', display: true },
        { left: '\\(', right: '\\)', display: false },
        { left: '$$', right: '$$', display: true },
      ],
      throwOnError: false,
      errorColor: '#f87171',
    });
  } catch (e) { console.warn('[katex] render failed', e); }
}

// 数式を含むテキストの安全レンダリング: HTML escape → \(...\) のバックスラッシュは保持
function escapeTextWithMath(s) {
  if (s == null) return '';
  // HTML escape
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/\n/g, '<br>');
}

function renderQuestions() {
  const box = document.getElementById('questionBox');
  const instant = getUserInstantPref();
  let html = '';
  // ⚠️ AI 接続失敗・問題不足時の明示警告 (偽プレースホルダ廃止に伴う)
  if (state.warning) {
    html += `<div class="ee-warning-box">${escapeHtml(state.warning)}</div>`;
  }
  if (state.passage) {
    html += `<div class="ee-passage"><h3>📖 ${state.examId === 'rikei' ? '問題設定' : 'Passage'}</h3><p>${escapeTextWithMath(state.passage)}</p></div>`;
  }
  // 🔬 理系: figure_svg を表示 (sanitize 後 inline)
  if (state.figureSvg) {
    const safe = sanitizeSvg(state.figureSvg);
    if (safe) {
      html += `<div class="ee-figure"><h3>📐 図</h3><div class="ee-figure-svg">${safe}</div></div>`;
    }
  }
  if (state.audioScript) {
    html += `<div class="ee-passage ee-audio"><h3>🎧 Listening Script (本来は音声)</h3><p>${escapeTextWithMath(state.audioScript)}</p>
      <p class="ee-note">💡 本物の試験では音声のみ。ここではスクリプトを表示しています。</p></div>`;
  }
  if (state.prompt) {
    html += `<div class="ee-passage"><h3>✍️ Prompt</h3><p>${escapeTextWithMath(state.prompt)}</p></div>`;
  }
  state.questions.forEach((q, idx) => {
    html += `<div class="ee-question" data-qid="${q.id}">
      <div class="ee-question-num">Q${idx + 1}</div>
      <div class="ee-question-stem">${escapeTextWithMath(q.stem || '')}</div>`;
    if (q.type === 'multiple_choice' && Array.isArray(q.choices) && q.choices.length) {
      // 🎯 ボタン式 4択 (radio は隠して label をボタンに)
      html += `<div class="ee-choices ee-choices-btn" role="radiogroup" aria-label="Q${idx + 1} の選択肢">`;
      q.choices.forEach((c, ci) => {
        html += `<button type="button" class="ee-choice-btn" data-qid="${q.id}" data-choice="${ci}" role="radio" aria-checked="false">
          <span class="ee-choice-letter">${String.fromCharCode(65 + ci)}</span>
          <span class="ee-choice-text">${escapeTextWithMath(c)}</span>
          <span class="ee-choice-icon"></span>
        </button>`;
      });
      html += '</div>';
      // 即時採点モード時の解説エリア (デフォルト非表示)
      html += `<div class="ee-instant-explain" data-qid="${q.id}" style="display:none;"></div>`;
    } else if (q.type === 'short_answer') {
      html += `<input type="text" class="ee-text-input" name="${q.id}" placeholder="回答を入力">`;
    } else {
      html += `<textarea class="ee-textarea" name="${q.id}" rows="6" placeholder="${q.type === 'speaking' ? '口頭で話す内容を文字に書き起こしてください' : 'エッセイをここに書いてください'}"></textarea>`;
    }
    html += '</div>';
  });
  box.innerHTML = html;

  // 🎯 ボタン式 4択 のイベント (タップで選択 + 即時採点モード時は正誤判定)
  box.querySelectorAll('.ee-choice-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const qid = btn.dataset.qid;
      const ci = parseInt(btn.dataset.choice, 10);
      const q = state.questions.find(x => x.id === qid);
      if (!q) return;
      // 既に即時採点で確定していたら無効
      const explainBox = box.querySelector(`.ee-instant-explain[data-qid="${qid}"]`);
      if (explainBox && explainBox.classList.contains('locked')) return;
      // 同 group の他ボタンを deselect
      box.querySelectorAll(`.ee-choice-btn[data-qid="${qid}"]`).forEach(b => {
        b.classList.remove('selected');
        b.setAttribute('aria-checked', 'false');
      });
      btn.classList.add('selected');
      btn.setAttribute('aria-checked', 'true');
      state.userAnswers[qid] = ci;

      // 即時採点モード: タップ瞬間に正誤判定 + 解説表示
      if (instant && q.type === 'multiple_choice') {
        const correct = parseInt(q.answer, 10);
        const isCorrect = ci === correct;
        // ボタンに正誤色を反映
        box.querySelectorAll(`.ee-choice-btn[data-qid="${qid}"]`).forEach(b => {
          b.classList.add('graded');
          const cci = parseInt(b.dataset.choice, 10);
          if (cci === correct) b.classList.add('is-correct');
          else if (cci === ci) b.classList.add('is-wrong');
          b.disabled = true;
        });
        // 解説エリア
        if (explainBox) {
          explainBox.style.display = '';
          explainBox.classList.add('locked');
          explainBox.classList.add(isCorrect ? 'correct' : 'wrong');
          explainBox.innerHTML = `
            <div class="ee-instant-head">${isCorrect ? '✅ 正解!' : '❌ 不正解'} <span class="ee-instant-correct">正解: ${String.fromCharCode(65 + correct)} (${escapeTextWithMath(q.choices[correct] || '')})</span></div>
            <div class="ee-instant-body">${escapeTextWithMath(q.explanation || '')}</div>`;
          // 解説に LaTeX が含まれていたら再レンダリング
          applyKatex(explainBox);
        }
      }
    });
  });

  // テキスト/エッセイ系の input
  state.questions.forEach(q => {
    const inputs = box.querySelectorAll(`input[name="${q.id}"], textarea[name="${q.id}"]`);
    inputs.forEach(inp => {
      inp.addEventListener('change', () => { state.userAnswers[q.id] = inp.value; });
      inp.addEventListener('input', () => { state.userAnswers[q.id] = inp.value; });
    });
  });

  // 🧮 KaTeX 全体レンダリング (理系問題の数式を一括変換)
  // CDN 読込が遅延の場合は loaded 後に再実行
  if (typeof window.renderMathInElement === 'function') {
    applyKatex(box);
  } else {
    let tries = 0;
    const id = setInterval(() => {
      tries++;
      if (typeof window.renderMathInElement === 'function') {
        clearInterval(id);
        applyKatex(box);
      } else if (tries > 20) {
        clearInterval(id);
      }
    }, 200);
  }
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
  // 英検は g{N}_{key}、大学入試は {univ}_{key} の compound key で sectionsByGrade を区別
  if (!autoBank && !staticBank && (examId === 'eiken' || examId === 'daigaku') && state && state.eikenGrade) {
    const compoundKey = state.eikenGrade + '_' + sectionKey;
    // AUTO_GENERATED_BANKS にも compound key で問い合わせ
    const autoCompound = auto[examId] && auto[examId][compoundKey];
    const staticCompound = SAMPLE_BANKS[examId] && SAMPLE_BANKS[examId][compoundKey];
    if (autoCompound && staticCompound) return Math.random() < 0.6 ? autoCompound : staticCompound;
    return autoCompound || staticCompound;
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
      // multiple_choice 系: 偽プレースホルダで埋めず、実問題数だけ返す
      const available = partBank.questions.length;
      const limit = Math.min(qCount, available);
      const qs = partBank.questions.slice(0, limit).map((q, i) => ({
        id: `q${i + 1}`,
        type: 'multiple_choice',
        stem: q.stem,
        choices: q.choices,
        answer: q.answer,
        explanation: q.explanation,
      }));
      const warning = (qCount > available)
        ? `📝 表示中: ${available}問 (リクエスト ${qCount}問)・残りは AI バックエンド接続後に自動生成されます`
        : '';
      return {
        passage: partBank.passage || '',
        audio_script: partBank.audio_script || '',
        prompt: partBank.prompt || '',
        questions: qs,
        _warning: warning,
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

  // 2) フォールバック: バンクが完全になく AI も使えない時
  // 偽の placeholder ではなく、ユーザーへの明示メッセージを返す
  return {
    passage: '',
    audio_script: '',
    prompt: '',
    questions: [],
    _warning: `⚠️ AI バックエンドに接続できませんでした。問題プールの蓄積も該当 part にありません。${exam.name} ${section.name} の問題は本番環境で AI が即時生成します (ローカル環境では preview のみ)。`,
  };
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
    grade: state.eikenGrade || null,        // 英検級 or 大学キー (todai/kyodai/...)
    gradeName: state.eikenGradeName || null,
    overallScore: result.overallScore,
    sectionScore: result.sectionScore,
    sectionScoreMax: section.scoreMax || null,
    cefr: result.cefr,
  });
  renderHistorySection();
  // ヒートマップも自動更新
  if (typeof renderHeatmap === 'function') renderHeatmap();
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
// ==========================================================================
// 📰 LIVE NEWS READING (CNN / Japan Times / BBC ...) — backend へ問い合わせて
// 最新記事一覧を表示し、選択した記事を AI で読解問題化する
// ==========================================================================
const NEWS_FEEDS_META = [
  { key: 'cnn',           name: 'CNN',           emoji: '🇺🇸', tag: 'Top Stories', level: 'B2-C1' },
  { key: 'cnn_world',     name: 'CNN World',     emoji: '🌍', tag: 'World',       level: 'B2-C1' },
  { key: 'japan_times',   name: 'Japan Times',   emoji: '🇯🇵', tag: 'Top',         level: 'B2'    },
  { key: 'japan_times_news', name: 'Japan Times News', emoji: '🗾', tag: 'News',  level: 'B2'    },
  { key: 'bbc',           name: 'BBC',           emoji: '🇬🇧', tag: 'Top',         level: 'B2'    },
  { key: 'bbc_world',     name: 'BBC World',     emoji: '🌐', tag: 'World',       level: 'B2'    },
  { key: 'nyt',           name: 'NY Times',      emoji: '🗽', tag: 'Home',        level: 'C1'    },
  { key: 'guardian',      name: 'The Guardian',  emoji: '🇬🇧', tag: 'World',       level: 'B2-C1' },
  { key: 'reuters_world', name: 'Reuters World', emoji: '📡', tag: 'World',       level: 'B2'    },
  { key: 'nhk_world',     name: 'NHK World',     emoji: '🗾', tag: 'JP→EN',       level: 'B1-B2' },
];

function renderNewsFeedGrid() {
  const grid = document.getElementById('newsFeedGrid');
  if (!grid) return;
  grid.innerHTML = '';
  NEWS_FEEDS_META.forEach(f => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'news-feed-card';
    btn.dataset.feed = f.key;
    btn.innerHTML = `
      <div class="news-feed-emoji">${f.emoji}</div>
      <div class="news-feed-name">${f.name}</div>
      <div class="news-feed-tag">${f.tag} · CEFR ${f.level}</div>
    `;
    btn.addEventListener('click', () => loadNewsArticles(f.key));
    grid.appendChild(btn);
  });
}

async function loadNewsArticles(feedKey) {
  const box = document.getElementById('newsArticlesBox');
  box.style.display = '';
  box.innerHTML = '<p class="ee-loading">⏳ 最新記事を取得中...</p>';
  document.getElementById('newsQuestionBox').style.display = 'none';
  const meta = NEWS_FEEDS_META.find(f => f.key === feedKey) || {};
  try {
    const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
      ? 'http://localhost:8000' : window.location.origin;
    const res = await fetch(`${backend}/api/news/articles?feed=${encodeURIComponent(feedKey)}&limit=5`);
    if (!res.ok) throw new Error('fetch_failed:' + res.status);
    const data = await res.json();
    if (!data.articles || !data.articles.length) {
      box.innerHTML = '<p class="ee-error">記事を取得できませんでした。少し時間をおいて再度お試しください。</p>';
      return;
    }
    let html = `<div class="news-articles-head"><strong>${meta.emoji || ''} ${escapeHtml(data.feed_name || feedKey)}</strong> · 最新 ${data.articles.length} 件 · 任意の記事を選んで読解問題を作成</div>`;
    html += '<div class="news-articles-list">';
    data.articles.forEach((a, i) => {
      html += `<button type="button" class="news-article-card" data-idx="${i}" data-feed="${feedKey}">
        <div class="news-article-title">${escapeHtml(a.title)}</div>
        <div class="news-article-summary">${escapeHtml((a.summary || '').slice(0, 220))}${a.summary && a.summary.length > 220 ? '…' : ''}</div>
        <div class="news-article-meta">
          ${a.published ? `<span>${escapeHtml(a.published)}</span>` : ''}
          <span class="news-article-go">📝 この記事で問題を作る →</span>
        </div>
      </button>`;
    });
    html += '</div>';
    box.innerHTML = html;
    box.querySelectorAll('.news-article-card').forEach(btn => {
      btn.addEventListener('click', () => generateNewsQuestion(feedKey, parseInt(btn.dataset.idx, 10)));
    });
  } catch (e) {
    console.error('[news] articles failed', e);
    box.innerHTML = `<p class="ee-error">⚠️ 記事の取得に失敗しました (${escapeHtml(String(e.message || e))})。バックエンド未接続かもしれません。</p>`;
  }
}

async function generateNewsQuestion(feedKey, idx) {
  const qBox = document.getElementById('newsQuestionBox');
  qBox.style.display = '';
  qBox.innerHTML = '<p class="ee-loading">⏳ AI が読解問題を作成中... (15〜45秒)</p>';
  qBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
  try {
    const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
      ? 'http://localhost:8000' : window.location.origin;
    const res = await fetch(`${backend}/api/news/generate-question`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feed: feedKey, index: idx }),
    });
    if (!res.ok) throw new Error('gen_failed:' + res.status);
    const data = await res.json();
    renderNewsQuestion(data);
  } catch (e) {
    console.error('[news] generate failed', e);
    qBox.innerHTML = `<p class="ee-error">⚠️ 問題生成に失敗しました (${escapeHtml(String(e.message || e))})</p>`;
  }
}

function renderNewsQuestion(data) {
  const qBox = document.getElementById('newsQuestionBox');
  const q = data.question || {};
  const article = data.article || {};
  let html = `<div class="news-q-head">
    <span class="news-q-feed">📰 ${escapeHtml(data.feed_name || data.feed)} · CEFR ${escapeHtml(data.level || '')}</span>
    <span class="news-q-source">出典: <a href="${escapeHtml(article.link || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(article.title || '原文記事')}</a></span>
  </div>`;
  if (q.passage) {
    html += `<div class="ee-passage"><h3>📖 Reading Passage (AI が記事テーマで独自執筆・250-350語)</h3><p>${escapeHtml(q.passage).replace(/\n/g, '<br>')}</p></div>`;
  }
  if (q.included_link_message) {
    html += `<div class="news-q-cta">${escapeHtml(q.included_link_message)} → <a href="${escapeHtml(article.link || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(article.link || '')}</a></div>`;
  }
  if (Array.isArray(q.questions)) {
    q.questions.forEach((qq, i) => {
      html += `<div class="ee-question" data-qid="${qq.id || ('nq'+i)}">
        <div class="ee-question-num">Q${i + 1}</div>
        <div class="ee-question-stem">${escapeHtml(qq.stem || '')}</div>`;
      if (Array.isArray(qq.choices) && qq.choices.length) {
        html += '<div class="ee-choices">';
        qq.choices.forEach((c, ci) => {
          html += `<label class="ee-choice"><input type="radio" name="news-${i}" value="${ci}"><span class="ee-choice-letter">${String.fromCharCode(65 + ci)}</span><span class="ee-choice-text">${escapeHtml(c)}</span></label>`;
        });
        html += '</div>';
      }
      html += `<details class="news-q-explain"><summary>📝 解答・解説を見る</summary>
        <div><strong>正解:</strong> ${escapeHtml(String(qq.answer))}${(typeof qq.answer === 'string' && /^\d+$/.test(qq.answer) && Array.isArray(qq.choices)) ? ' (= ' + escapeHtml(qq.choices[parseInt(qq.answer,10)] || '') + ')' : ''}</div>
        <div class="news-q-explain-text">${escapeHtml(qq.explanation || '').replace(/\n/g,'<br>')}</div>
      </details>`;
      html += '</div>';
    });
  }
  qBox.innerHTML = html;
}

// ==========================================================================
// 📚 蓄積問題アーカイブ (Phase 5-1: AI 自動生成プールを直接ブラウズ)
// ==========================================================================
const ARCH_STATE = { exam: null, grade: null, part: null, year: null };

function getEEBackend() {
  return (window.location.hostname === 'localhost' && window.location.port === '8090')
    ? 'http://localhost:8000' : window.location.origin;
}

async function loadArchiveOverview(examId = null) {
  const box = document.getElementById('archOverview');
  const list = document.getElementById('archList');
  box.style.display = '';
  list.style.display = 'none';
  box.innerHTML = '<p class="ee-loading">⏳ 蓄積状況を読み込み中…</p>';
  try {
    const url = `${getEEBackend()}/api/exam-questions/archive` + (examId ? `?exam=${encodeURIComponent(examId)}` : '');
    const res = await fetch(url);
    if (!res.ok) throw new Error('http_' + res.status);
    const data = await res.json();
    if (!data.groups || !data.groups.length) {
      box.innerHTML = `<p class="ee-empty">📭 ${examId ? 'この試験の' : ''}蓄積問題はまだありません。AI が随時自動生成中です (毎日 6時間おきに増加)。</p>`;
      return;
    }
    // 試験+grade ごとに集計
    const labels = { toefl: '🇺🇸 TOEFL', toeic: '💼 TOEIC', ielts: '🇬🇧 IELTS', eiken: '🇯🇵 英検', daigaku: '🎓 大学入試' };
    const byKey = new Map();
    data.groups.forEach(g => {
      const k = `${g.exam}/${g.grade || '_'}`;
      if (!byKey.has(k)) byKey.set(k, { exam: g.exam, grade: g.grade, parts: [], total: 0 });
      const o = byKey.get(k);
      o.parts.push({ part: g.part, count: g.count });
      o.total += g.count;
    });
    let html = `<div class="archive-overview-head">📊 蓄積総数: <strong>${data.total}</strong> 問 (試験/級・大学/枠ごと)</div><div class="archive-overview-grid">`;
    [...byKey.values()].sort((a,b)=>b.total-a.total).forEach(o => {
      const gradeLabel = o.grade ? ` <span class="arch-grade-tag">${o.grade}</span>` : '';
      html += `<button type="button" class="archive-group-card" data-exam="${o.exam}" data-grade="${o.grade || ''}">
        <div class="arch-group-name">${labels[o.exam] || o.exam}${gradeLabel}</div>
        <div class="arch-group-count">${o.total} 問</div>
        <div class="arch-group-parts">${o.parts.length} 大問</div>
      </button>`;
    });
    html += '</div>';
    box.innerHTML = html;
    box.querySelectorAll('.archive-group-card').forEach(btn => {
      btn.addEventListener('click', () => {
        ARCH_STATE.exam = btn.dataset.exam;
        ARCH_STATE.grade = btn.dataset.grade || null;
        ARCH_STATE.part = null;
        ARCH_STATE.year = null;
        // フィルタ UI を反映
        document.getElementById('archExamFilter').value = ARCH_STATE.exam;
        populateArchGradeOptions();
        document.getElementById('archGradeFilter').value = ARCH_STATE.grade || '';
        populateArchPartOptions();
        document.getElementById('archYearFilter').style.display = ARCH_STATE.exam === 'daigaku' ? '' : 'none';
        document.getElementById('archSearchBtn').style.display = '';
        loadArchiveList();
      });
    });
  } catch (e) {
    console.warn('[archive] overview failed:', e);
    box.innerHTML = `<p class="ee-error">⚠️ 取得失敗: ${escapeHtml(String(e.message || e))}</p>`;
  }
}

function populateArchGradeOptions() {
  const sel = document.getElementById('archGradeFilter');
  sel.innerHTML = '<option value="">大学/級 すべて</option>';
  const exam = ARCH_STATE.exam;
  if (exam === 'eiken') {
    EXAMS.eiken.grades.forEach(g => {
      sel.innerHTML += `<option value="${g.key}">${escapeHtml(g.name)}</option>`;
    });
    sel.style.display = '';
  } else if (exam === 'daigaku') {
    EXAMS.daigaku.grades.forEach(g => {
      sel.innerHTML += `<option value="${g.key}">${escapeHtml(g.name)}</option>`;
    });
    sel.style.display = '';
  } else {
    sel.style.display = 'none';
  }
}

function populateArchPartOptions() {
  const sel = document.getElementById('archPartFilter');
  sel.innerHTML = '<option value="">大問 すべて</option>';
  const exam = ARCH_STATE.exam;
  if (!exam) { sel.style.display = 'none'; return; }
  let secs = [];
  if (exam === 'eiken' && ARCH_STATE.grade) {
    secs = getEikenSections(ARCH_STATE.grade);
  } else if (exam === 'daigaku' && ARCH_STATE.grade) {
    secs = getDaigakuSections(ARCH_STATE.grade);
  } else {
    secs = (EXAMS[exam] && EXAMS[exam].sections) || [];
  }
  secs.forEach(s => {
    sel.innerHTML += `<option value="${s.key}">${escapeHtml(s.icon + ' ' + s.name)}</option>`;
  });
  sel.style.display = '';
}

async function loadArchiveList() {
  const list = document.getElementById('archList');
  const overview = document.getElementById('archOverview');
  list.style.display = '';
  list.innerHTML = '<p class="ee-loading">⏳ 該当問題を読み込み中…</p>';
  const params = new URLSearchParams();
  if (ARCH_STATE.exam) params.set('exam', ARCH_STATE.exam);
  if (ARCH_STATE.grade) {
    if (ARCH_STATE.exam === 'daigaku') params.set('univ', ARCH_STATE.grade);
    else params.set('eiken_grade', ARCH_STATE.grade);
  }
  if (ARCH_STATE.part) params.set('part', ARCH_STATE.part);
  if (ARCH_STATE.year) params.set('year', String(ARCH_STATE.year));
  params.set('limit', '50');
  try {
    const res = await fetch(`${getEEBackend()}/api/exam-questions/archive?${params}`);
    if (!res.ok) throw new Error('http_' + res.status);
    const data = await res.json();
    if (!data.items || !data.items.length) {
      list.innerHTML = `<p class="ee-empty">📭 条件に該当する問題が見つかりませんでした。</p>
        <button class="ee-btn ee-btn-ghost" id="archBackBtn">← 全体ビューに戻る</button>`;
      document.getElementById('archBackBtn').addEventListener('click', () => loadArchiveOverview());
      return;
    }
    let html = `<div class="archive-list-head">
      <strong>${data.total} 問</strong> 該当 (上位 ${data.items.length} 件表示)
      <button class="ee-btn ee-btn-ghost ee-btn-mini" id="archBackBtn">← 全体ビューに戻る</button>
    </div>`;
    html += '<div class="archive-items">';
    data.items.forEach(it => {
      const yearTag = it.year ? `<span class="arch-year-tag">${it.year}年度</span>` : '';
      const univTag = it.univ_simulated ? `<span class="arch-univ-tag">${escapeHtml(it.univ_simulated)}</span>` : '';
      html += `<div class="archive-item-card">
        <div class="arch-item-meta">${yearTag}${univTag}<span class="arch-item-part">${escapeHtml(it.part)}</span><span class="arch-item-q">${it.question_count}問</span></div>
        <div class="arch-item-preview">${escapeHtml(it.passage_preview || '(プレビュー無し)')}…</div>
        <button class="ee-btn ee-btn-primary ee-btn-mini" data-qid="${it.id}">📝 これを解く</button>
      </div>`;
    });
    html += '</div>';
    list.innerHTML = html;
    document.getElementById('archBackBtn').addEventListener('click', () => loadArchiveOverview());
    list.querySelectorAll('button[data-qid]').forEach(btn => {
      btn.addEventListener('click', () => loadArchiveQuestion(parseInt(btn.dataset.qid, 10)));
    });
  } catch (e) {
    console.warn('[archive] list failed:', e);
    list.innerHTML = `<p class="ee-error">⚠️ 取得失敗: ${escapeHtml(String(e.message || e))}</p>`;
  }
}

async function loadArchiveQuestion(qid) {
  try {
    const res = await fetch(`${getEEBackend()}/api/exam-questions/archive/${qid}`);
    if (!res.ok) throw new Error('http_' + res.status);
    const data = await res.json();
    const exam = EXAMS[data.exam];
    if (!exam) throw new Error('unknown_exam:' + data.exam);
    state.examId = data.exam;
    state.eikenGrade = data.grade || null;
    if (data.grade) {
      const grades = exam.grades || [];
      const g = grades.find(x => x.key === data.grade);
      state.eikenGradeName = g ? g.name : data.grade;
    }
    let secs = [];
    if (data.exam === 'eiken' && data.grade) secs = getEikenSections(data.grade);
    else if (data.exam === 'daigaku' && data.grade) secs = getDaigakuSections(data.grade);
    else secs = exam.sections || [];
    state.currentSections = secs;
    const section = secs.find(s => s.key === data.part) || (secs[0] || { key: data.part, name: data.part, timeMin: 30, qCount: data.question.questions ? data.question.questions.length : 5, scoreMax: 30, desc: '' });
    state.sectionKey = section.key;
    // ランナーを開く
    showRunner(exam, section);
    // 蓄積済の問題をそのまま使用 (AI 再生成しない)
    const q = data.question;
    state.questions = q.questions || [];
    state.passage = q.passage || '';
    state.audioScript = q.audio_script || '';
    state.prompt = q.prompt || '';
    state.userAnswers = {};
    renderQuestions();
    document.getElementById('submitAnswersBtn').disabled = false;
    document.getElementById('submitAnswersBtn').onclick = submitAnswers;
  } catch (e) {
    console.error('[archive] load question failed:', e);
    alert('問題の読込に失敗しました: ' + (e.message || e));
  }
}

// ==========================================================================
// 📊 弱点ヒートマップ + AI 推奨次題 (Phase 5-3)
// ==========================================================================
function buildHeatmapStats(history) {
  // (examId, sectionKey, grade) で集計
  const map = new Map();
  history.forEach(h => {
    const examId = h.examId; const part = h.sectionKey; const grade = h.grade || '_';
    if (!examId || !part) return;
    const key = `${examId}/${part}/${grade}`;
    if (!map.has(key)) map.set(key, { examId, part, grade: h.grade || null, gradeName: h.gradeName, attempts: 0, scoreSum: 0, maxSum: 0, lastTs: '' });
    const o = map.get(key);
    o.attempts += 1;
    if (typeof h.sectionScore === 'number' && typeof h.sectionScoreMax === 'number' && h.sectionScoreMax > 0) {
      o.scoreSum += h.sectionScore;
      o.maxSum += h.sectionScoreMax;
    } else if (typeof h.overallScore === 'number') {
      // overall しか無い場合の代替 (CEFR%換算は不正確なのでスコア比は出さない)
    }
    if (h.ts > o.lastTs) o.lastTs = h.ts;
  });
  const rows = [...map.values()].map(o => ({
    ...o,
    ratio: o.maxSum > 0 ? (o.scoreSum / o.maxSum) : null,
  }));
  rows.sort((a,b) => {
    const ra = a.ratio == null ? 1.0 : a.ratio;
    const rb = b.ratio == null ? 1.0 : b.ratio;
    return ra - rb; // 弱い順
  });
  return rows;
}

function renderHeatmap() {
  const hist = loadHistory();
  const statsBox = document.getElementById('heatmapStats');
  const gridBox = document.getElementById('heatmapGrid');
  if (!statsBox || !gridBox) return;
  if (!hist.length) {
    statsBox.innerHTML = '<p class="ee-empty">📭 まだ受験記録がありません。模試・大問演習に挑戦すると履歴が蓄積され、ここに弱点が可視化されます。</p>';
    gridBox.innerHTML = '';
    return;
  }
  const rows = buildHeatmapStats(hist);
  // KPI
  const totalAttempts = hist.length;
  const totalRatio = rows.filter(r => r.ratio != null).reduce((s, r) => s + (r.ratio * (r.maxSum)), 0);
  const totalMax = rows.reduce((s, r) => s + r.maxSum, 0);
  const avgRatio = totalMax > 0 ? Math.round(100 * totalRatio / totalMax) : null;
  statsBox.innerHTML = `
    <div class="heatmap-kpi-row">
      <div class="heatmap-kpi"><div class="hm-kpi-label">総受験回数</div><div class="hm-kpi-value">${totalAttempts}</div></div>
      <div class="heatmap-kpi"><div class="hm-kpi-label">平均得点率</div><div class="hm-kpi-value">${avgRatio != null ? avgRatio + '%' : '—'}</div></div>
      <div class="heatmap-kpi"><div class="hm-kpi-label">挑戦 part 数</div><div class="hm-kpi-value">${rows.length}</div></div>
      <div class="heatmap-kpi"><div class="hm-kpi-label">最も伸びしろ</div><div class="hm-kpi-value">${rows[0] ? rows[0].part : '—'}</div></div>
    </div>`;
  // grid (rows = exam+grade, cols = part)
  let html = '<div class="heatmap-rows">';
  rows.forEach(r => {
    const ratio = r.ratio;
    const pct = ratio != null ? Math.round(ratio * 100) : null;
    const color = pct == null ? '#475569' : (pct >= 80 ? '#22c55e' : pct >= 60 ? '#fbbf24' : '#f87171');
    const labelMap = { toefl: '🇺🇸 TOEFL', toeic: '💼 TOEIC', ielts: '🇬🇧 IELTS', eiken: '🇯🇵 英検', daigaku: '🎓 大学入試' };
    const examLabel = labelMap[r.examId] || r.examId;
    const gradeLabel = r.gradeName || (r.grade ? `[${r.grade}]` : '');
    html += `<div class="heatmap-row">
      <div class="hm-row-label">${examLabel} ${escapeHtml(gradeLabel)} <code>${escapeHtml(r.part)}</code></div>
      <div class="hm-row-bar"><div class="hm-row-fill" style="width:${pct == null ? 0 : pct}%;background:${color};"></div></div>
      <div class="hm-row-pct" style="color:${color};">${pct != null ? pct + '%' : '—'} <span class="hm-row-n">(n=${r.attempts})</span></div>
    </div>`;
  });
  html += '</div>';
  gridBox.innerHTML = html;
}

async function aiRecommendNext() {
  const btn = document.getElementById('aiRecommendBtn');
  if (!btn) return;
  const hist = loadHistory();
  btn.disabled = true; btn.textContent = '⏳ AI が分析中...';
  try {
    const res = await fetch(`${getEEBackend()}/api/exam-questions/recommend`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        history: hist.map(h => ({
          exam: h.examId, part: h.sectionKey, grade: h.grade,
          score: h.sectionScore, scoreMax: h.sectionScoreMax,
          date: h.ts,
        })),
        target: { exam: state.examId || null, grade: state.eikenGrade || null },
      }),
    });
    if (!res.ok) throw new Error('http_' + res.status);
    const data = await res.json();
    const wrap = document.getElementById('heatmapRecommend');
    let html = '<div class="recommend-card">';
    if (data.ai_advice) {
      const a = data.ai_advice;
      html += `<div class="recommend-head">🤖 AI からの推薦</div>
        <div class="recommend-target">📌 次に解くべき part: <strong>${escapeHtml(a.recommended_exam || '')}/${escapeHtml(a.recommended_part || '')}${a.recommended_grade ? ' [' + escapeHtml(a.recommended_grade) + ']' : ''}</strong></div>
        <div class="recommend-reason">💡 理由: ${escapeHtml(a.reason_jp || '')}</div>
        <div class="recommend-tip">📚 今日のヒント: ${escapeHtml(a.study_tip_jp || '')}</div>`;
    } else if (data.fallback_recommendations && data.fallback_recommendations.length) {
      const f = data.fallback_recommendations[0];
      html += `<div class="recommend-head">📊 履歴ベース推薦</div>
        <div class="recommend-target">📌 次に解くべき part: <strong>${escapeHtml(f.exam)}/${escapeHtml(f.part)}${f.grade ? ' [' + escapeHtml(f.grade) + ']' : ''}</strong></div>
        <div class="recommend-reason">💡 ${escapeHtml(f.reason_jp || '')}</div>`;
    } else {
      html += '<div class="recommend-head">まだ履歴が不足しています</div><div>いくつか問題を解いてから再度お試しください。</div>';
    }
    html += `<button class="ee-btn ee-btn-ghost" id="aiRecommendBtn">🔁 もう一度 AI に聞く</button></div>`;
    wrap.innerHTML = html;
    document.getElementById('aiRecommendBtn').addEventListener('click', aiRecommendNext);
  } catch (e) {
    console.error('[recommend] failed:', e);
    btn.disabled = false; btn.textContent = '🤖 AI に「次は何を解くべき?」を聞く';
    alert('推薦の取得に失敗しました: ' + (e.message || e));
  }
}

function bindArchiveFilters() {
  const examSel = document.getElementById('archExamFilter');
  const gradeSel = document.getElementById('archGradeFilter');
  const partSel = document.getElementById('archPartFilter');
  const yearInp = document.getElementById('archYearFilter');
  const searchBtn = document.getElementById('archSearchBtn');
  if (!examSel) return;
  examSel.addEventListener('change', () => {
    ARCH_STATE.exam = examSel.value || null;
    ARCH_STATE.grade = null;
    ARCH_STATE.part = null;
    ARCH_STATE.year = null;
    populateArchGradeOptions();
    populateArchPartOptions();
    yearInp.style.display = ARCH_STATE.exam === 'daigaku' ? '' : 'none';
    searchBtn.style.display = ARCH_STATE.exam ? '' : 'none';
    loadArchiveOverview(ARCH_STATE.exam);
  });
  gradeSel.addEventListener('change', () => {
    ARCH_STATE.grade = gradeSel.value || null;
    ARCH_STATE.part = null;
    populateArchPartOptions();
  });
  partSel.addEventListener('change', () => {
    ARCH_STATE.part = partSel.value || null;
  });
  yearInp.addEventListener('change', () => {
    const y = parseInt(yearInp.value, 10);
    ARCH_STATE.year = (y >= 2005 && y <= 2026) ? y : null;
  });
  searchBtn.addEventListener('click', loadArchiveList);
}

// ==========================================================================
// 🎯 受験日カウントダウン + 個別 AI カリキュラム (Phase 7)
// ==========================================================================
const CURRICULUM_KEY = 'ee_curriculum_v1';

function loadCurriculumState() {
  try { return JSON.parse(localStorage.getItem(CURRICULUM_KEY) || 'null'); } catch { return null; }
}
function saveCurriculumState(data) {
  try { localStorage.setItem(CURRICULUM_KEY, JSON.stringify(data)); } catch {}
}

function bindCurriculumForm() {
  const examSel = document.getElementById('curExamSelect');
  const gradeSel = document.getElementById('curGradeSelect');
  const dateInp = document.getElementById('curExamDate');
  const daysHint = document.getElementById('curDaysRemaining');
  const genBtn = document.getElementById('curGenerateBtn');
  if (!examSel) return;

  // 日付の min/max を today / +5年 に
  const today = new Date();
  dateInp.min = today.toISOString().slice(0, 10);
  dateInp.max = new Date(today.getTime() + 365 * 5 * 86400000).toISOString().slice(0, 10);

  examSel.addEventListener('change', () => {
    const ex = examSel.value;
    if (!ex) { gradeSel.style.display = 'none'; return; }
    if (ex === 'eiken' || ex === 'daigaku') {
      gradeSel.innerHTML = '<option value="">大学/級を選ぶ…</option>';
      const grades = (EXAMS[ex] && EXAMS[ex].grades) || [];
      grades.forEach(g => {
        gradeSel.innerHTML += `<option value="${g.key}">${escapeHtml(g.name)}</option>`;
      });
      gradeSel.style.display = '';
    } else {
      gradeSel.style.display = 'none';
    }
  });

  dateInp.addEventListener('change', () => {
    if (!dateInp.value) { daysHint.textContent = '--'; return; }
    const d = new Date(dateInp.value);
    const diff = Math.ceil((d - new Date()) / 86400000);
    daysHint.textContent = diff > 0 ? `あと ${diff} 日 (約${Math.ceil(diff/7)}週間)` : '受験日を未来日付に';
  });

  genBtn.addEventListener('click', generateCurriculum);

  // 既存のカリキュラムがあれば復元
  const saved = loadCurriculumState();
  if (saved && saved.exam_id) {
    examSel.value = saved.exam_id;
    examSel.dispatchEvent(new Event('change'));
    if (saved.target_grade) gradeSel.value = saved.target_grade;
    if (saved.exam_date) {
      dateInp.value = saved.exam_date.slice(0, 10);
      dateInp.dispatchEvent(new Event('change'));
    }
    if (saved.current_level) document.getElementById('curCurrentLevel').value = saved.current_level;
    if (saved.daily_minutes) document.getElementById('curDailyMinutes').value = saved.daily_minutes;
    renderCurriculum(saved);
  }
}

async function generateCurriculum() {
  const examSel = document.getElementById('curExamSelect');
  const gradeSel = document.getElementById('curGradeSelect');
  const dateInp = document.getElementById('curExamDate');
  const lvSel = document.getElementById('curCurrentLevel');
  const minInp = document.getElementById('curDailyMinutes');
  const genBtn = document.getElementById('curGenerateBtn');
  const resultBox = document.getElementById('curriculumResult');
  if (!examSel.value) return alert('試験を選択してください');
  if (!dateInp.value) return alert('受験日を選択してください');
  // 弱点 part を Phase 5 history から自動抽出
  const hist = loadHistory();
  const stats = buildHeatmapStats(hist);
  const weak_parts = stats.filter(s => (s.ratio || 1.0) < 0.7).slice(0, 3).map(s => s.part);
  const history_summary = stats.slice(0, 8).map(s => ({
    exam: s.examId, part: s.part, grade: s.grade,
    attempts: s.attempts, score_ratio: s.ratio,
  }));
  const grade = gradeSel.value || null;
  const grade_name = gradeSel.value ? gradeSel.options[gradeSel.selectedIndex].text : null;
  const payload = {
    exam_id: examSel.value,
    target_grade: grade,
    target_grade_name: grade_name,
    exam_date: dateInp.value,
    current_level: lvSel.value,
    daily_minutes: parseInt(minInp.value, 10) || 60,
    weak_parts,
    history_summary,
  };
  resultBox.innerHTML = '<p class="ee-loading">⏳ AI が個別カリキュラムを設計中… (30〜90秒)</p>';
  resultBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
  genBtn.disabled = true; genBtn.textContent = '⏳ 生成中...';
  try {
    const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
      ? 'http://localhost:8000' : window.location.origin;
    const res = await fetch(`${backend}/api/curriculum/generate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error('http_' + res.status + ' ' + err.slice(0, 100));
    }
    const data = await res.json();
    // 永続化
    saveCurriculumState({ ...data, ...payload, saved_at: new Date().toISOString() });
    renderCurriculum(data);
  } catch (e) {
    console.error('[curriculum] failed', e);
    resultBox.innerHTML = `<p class="ee-error">⚠️ 生成失敗: ${escapeHtml(String(e.message || e))}</p>`;
  } finally {
    genBtn.disabled = false; genBtn.textContent = '🤖 AI に学習プランを生成してもらう';
  }
}

function renderCurriculum(data) {
  const box = document.getElementById('curriculumResult');
  if (!box || !data) return;
  const phases = data.phases || [];
  const roadmap = data.weekly_roadmap || [];
  const principles = data.study_principles || [];
  const milestones = data.milestone_assessments || [];

  // 進捗チェック (localStorage の completed_weeks)
  const progress = loadCurriculumState() || {};
  const completed = new Set(progress.completed_weeks || []);

  let html = `<div class="cur-result-card">`;
  html += `<div class="cur-head">
    <div class="cur-head-title">🎯 ${escapeHtml(data.target_grade_name || '受験対策')} (${escapeHtml(data.exam_id || '')})</div>
    <div class="cur-head-meta">📅 残 <strong>${data.days_remaining}</strong> 日 (約 <strong>${data.weeks_remaining}</strong> 週間) ${data.fallback ? '<span class="cur-fallback-tag">⚠ AI不調・簡易版</span>' : ''}</div>
    ${data.estimated_score_at_exam ? `<div class="cur-head-pred">🎯 予測到達: <strong>${escapeHtml(data.estimated_score_at_exam)}</strong></div>` : ''}
  </div>`;

  // フェーズ
  if (phases.length) {
    html += '<div class="cur-phases">';
    const colors = ['#22c55e', '#fbbf24', '#f87171'];
    phases.forEach((p, i) => {
      html += `<div class="cur-phase-card" style="border-color:${colors[i] || '#94a3b8'}33;">
        <div class="cur-phase-name" style="color:${colors[i] || '#94a3b8'};">${escapeHtml(p.phase || `Phase ${i+1}`)}</div>
        <div class="cur-phase-weeks">${p.weeks_count || 0} 週間</div>
        <div class="cur-phase-obj">${escapeHtml(p.objective_jp || '')}</div>
      </div>`;
    });
    html += '</div>';
  }

  // 学習原則
  if (principles.length) {
    html += '<details class="cur-principles" open><summary>📚 コーチング指針</summary><ul>';
    principles.forEach(p => { html += `<li>${escapeHtml(p)}</li>`; });
    html += '</ul></details>';
  }

  // 週次ロードマップ
  if (roadmap.length) {
    html += '<div class="cur-roadmap-head">📋 週次ロードマップ (チェックを入れて進捗管理)</div>';
    html += '<div class="cur-roadmap">';
    roadmap.forEach(w => {
      const isDone = completed.has(w.week);
      const phaseColor = w.phase === '基礎固め' ? '#22c55e' : w.phase === '応用強化' ? '#fbbf24' : '#f87171';
      html += `<div class="cur-week-card${isDone ? ' done' : ''}" data-week="${w.week}">
        <div class="cur-week-head">
          <label class="cur-week-check">
            <input type="checkbox" ${isDone ? 'checked' : ''} data-week="${w.week}">
            <span>Week ${w.week}</span>
          </label>
          <span class="cur-week-phase" style="background:${phaseColor}22;color:${phaseColor};">${escapeHtml(w.phase || '')}</span>
          <span class="cur-week-min">${w.estimated_total_minutes || 0} 分</span>
        </div>
        <div class="cur-week-focus">🎯 ${escapeHtml(w.focus_jp || '')}</div>
        ${(w.tasks || []).length ? '<ul class="cur-week-tasks">' + (w.tasks).map(t => `<li><span class="cur-task-cat">${escapeHtml(t.category || '')}</span> <strong>${escapeHtml(t.title_jp || '')}</strong> <span class="cur-task-min">${t.minutes || 0}分</span><div class="cur-task-detail">${escapeHtml(t.detail_jp || '')}</div></li>`).join('') + '</ul>' : ''}
        ${w.milestone_jp ? `<div class="cur-week-mile">📌 ${escapeHtml(w.milestone_jp)}</div>` : ''}
      </div>`;
    });
    html += '</div>';
  }

  // マイルストーン
  if (milestones.length) {
    html += '<details class="cur-milestones"><summary>🏁 マイルストーン</summary><ul>';
    milestones.forEach(m => {
      html += `<li>Week ${m.week} · ${escapeHtml(m.type || '')}: ${escapeHtml(m.target_jp || '')}</li>`;
    });
    html += '</ul></details>';
  }

  html += '<div class="cur-actions"><button id="curRegenBtn" class="ee-btn ee-btn-ghost">🔁 別の条件で再生成</button></div>';
  html += '</div>';
  box.innerHTML = html;

  // 進捗チェック バインド
  box.querySelectorAll('input[type="checkbox"][data-week]').forEach(cb => {
    cb.addEventListener('change', () => {
      const w = parseInt(cb.dataset.week, 10);
      const cur = loadCurriculumState() || {};
      const list = new Set(cur.completed_weeks || []);
      if (cb.checked) list.add(w); else list.delete(w);
      cur.completed_weeks = [...list];
      saveCurriculumState(cur);
      cb.closest('.cur-week-card').classList.toggle('done', cb.checked);
    });
  });
  document.getElementById('curRegenBtn')?.addEventListener('click', () => {
    document.getElementById('curriculumForm').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  updateModeBadge();
  bindExamCards();
  // currentLevel state 同期
  document.getElementById('currentLevel').addEventListener('change', e => {
    state.currentLevel = e.target.value;
  });
  state.currentLevel = document.getElementById('currentLevel').value || 'B1';

  // 問題数 / 即時採点モード 設定 (localStorage 永続化)
  const qcSel = document.getElementById('qCountPref');
  const instCb = document.getElementById('instantGradingPref');
  const instText = document.getElementById('instantGradingText');
  if (qcSel) {
    const cur = getUserQCountPref();
    qcSel.value = cur == null ? '' : String(cur);
    qcSel.addEventListener('change', () => {
      const v = qcSel.value;
      saveUserPref({ qCount: v ? parseInt(v, 10) : null });
    });
  }
  if (instCb && instText) {
    instCb.checked = getUserInstantPref();
    instText.textContent = instCb.checked ? 'ON (タップで即解説)' : 'OFF (まとめて採点)';
    instCb.addEventListener('change', () => {
      saveUserPref({ instant: instCb.checked });
      instText.textContent = instCb.checked ? 'ON (タップで即解説)' : 'OFF (まとめて採点)';
    });
  }
  // 起動時に履歴セクションを描画
  renderHistorySection();
  // ニュースフィード選択 UI
  renderNewsFeedGrid();
  // アーカイブ + ヒートマップ
  bindArchiveFilters();
  loadArchiveOverview();
  renderHeatmap();
  document.getElementById('aiRecommendBtn')?.addEventListener('click', aiRecommendNext);
  // カリキュラム
  bindCurriculumForm();
  // 音声合成の voices ロードを待つ (Chrome は遅延ロード)
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {};
  }
});
