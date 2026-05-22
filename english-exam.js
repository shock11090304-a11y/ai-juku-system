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
      // 📘 基礎 / 定期テスト (2026-05-13 塾長指示で追加)
      { key: 'kiso',      name: '基礎',             cefr: 'A2-B1', target: '高校英語の基礎固め・受験勉強の入り口・200-400 語の標準英文' },
      { key: 'teiki',     name: '定期テスト対策',   cefr: 'A2-B1', target: '高校 中間/期末試験・教科書傍用・学校文法 単元別カバー' },
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
      // 📘 基礎 (kiso) ・受験勉強の入り口・高校 1-2 年レベル
      kiso: [
        { key: 'r_short',   name: '基礎短文読解',     icon: '📝', timeMin: 15, qCount: 5,  scoreMax: 20, desc: '広告/メール/お知らせ等の実用英語 (100-200 語)' },
        { key: 'r_long',    name: '基礎長文読解',     icon: '📖', timeMin: 25, qCount: 5,  scoreMax: 30, desc: '読みやすい標準英文 (200-400 語) ・主旨と詳細を捉える' },
        { key: 'r_grammar', name: '基礎文法・語法',   icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 30, desc: '高校 1-2 年で学習する文法事項 (関係詞/分詞/不定詞/仮定法 基本形)' },
        { key: 'w_essay',   name: '基礎英作文',       icon: '✍️', timeMin: 15, qCount: 1,  scoreMax: 20, desc: '30-50 語の身近なテーマ (賛否/好み/経験)' },
      ],
      // 📗 定期テスト対策 (teiki) ・高校 中間/期末・教科書傍用
      teiki: [
        { key: 'r_short',   name: '定期テスト短文',   icon: '📝', timeMin: 15, qCount: 5,  scoreMax: 20, desc: '会話/物語の入門 (100-200 語) ・教科書トピック' },
        { key: 'r_long',    name: '定期テスト長文',   icon: '📖', timeMin: 25, qCount: 5,  scoreMax: 35, desc: '教科書系長文 (400-500 語) ・授業で扱う標準英文' },
        { key: 'r_grammar', name: '定期テスト文法',   icon: '🔀', timeMin: 15, qCount: 10, scoreMax: 30, desc: '関係詞節/分詞構文/仮定法/比較構文 単元別' },
        { key: 'w_essay',   name: '定期テスト英作文', icon: '✍️', timeMin: 15, qCount: 1,  scoreMax: 20, desc: '40-60 語の授業ノート活用テーマ (環境/教育/技術 入門)' },
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
      // 上智 理工 (2026-05-22 塾長指示: 上級レベル UI mismatch fix)
      // note: sophia 機能創造/情報理工は生物選択不可 → bio_q1 を意図的に含めない
      sophia_rikei: [
        { key: 'math_q1',  name: '数学 大問1', icon: '📐', timeMin: 25, qCount: 1, scoreMax: 25, desc: '機能創造/情報理工 数学' },
        { key: 'math_q2',  name: '数学 大問2', icon: '📐', timeMin: 25, qCount: 1, scoreMax: 25, desc: 'ベクトル/数列/複素数 標準' },
        { key: 'phys_q1',  name: '物理 大問1', icon: '⚛️', timeMin: 25, qCount: 1, scoreMax: 25, desc: '力学/電磁気/波動' },
        { key: 'chem_q1',  name: '化学 大問1', icon: '🧪', timeMin: 25, qCount: 1, scoreMax: 25, desc: '理論/無機/有機' },
      ],
      // 私立医学部 (2026-05-22 塾長指示: 上級レベル UI mismatch fix)
      igakubu_shiritsu_rikei: [
        { key: 'math_q1',  name: '数学 大問1', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 25, desc: '医療系数学 (微積/確率)' },
        { key: 'math_q2',  name: '数学 大問2', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 25, desc: 'ベクトル/数列/複素数' },
        { key: 'phys_q1',  name: '物理 大問1', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 25, desc: '医療系物理 (放射線/光学)' },
        { key: 'chem_q1',  name: '化学 大問1', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 25, desc: '医薬化学/生化学' },
        { key: 'bio_q1',   name: '生物 大問1', icon: '🧬', timeMin: 30, qCount: 1, scoreMax: 25, desc: 'DNA/タンパク質/免疫/代謝' },
      ],
      // 阪大 理工 (2026-05-22 塾長指示: math_q2 + UI mismatch fix)
      osaka_rikei: [
        { key: 'math_q1',  name: '数学 大問1', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 30, desc: '微積/極限/数列 等の難関融合' },
        { key: 'math_q2',  name: '数学 大問2', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 30, desc: 'ベクトル/複素数/整数' },
        { key: 'phys_q1',  name: '物理 大問1', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 30, desc: '力学/電磁気 (理工系)' },
      ],
      // 名大 理工 (2026-05-23 塾長指示「名大が極端に少ない」: phys/chem/bio 系を全 part 追加して他大学と揃える)
      nagoya_rikei: [
        { key: 'math_q1',  name: '数学 大問1', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 30, desc: '微積/ベクトル/確率 標準' },
        { key: 'math_q2',  name: '数学 大問2', icon: '📐', timeMin: 30, qCount: 1, scoreMax: 30, desc: '整数論/複素数/数列' },
        { key: 'phys_q1',  name: '物理 大問1', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 30, desc: '力学 + 電磁気 融合' },
        { key: 'phys_q2',  name: '物理 大問2', icon: '⚛️', timeMin: 30, qCount: 1, scoreMax: 30, desc: '波動/熱力学/原子物理' },
        { key: 'chem_q1',  name: '化学 大問1', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 30, desc: '理論化学 (平衡/反応速度)' },
        { key: 'chem_q2',  name: '化学 大問2', icon: '🧪', timeMin: 30, qCount: 1, scoreMax: 30, desc: '有機化学 (構造決定/合成)' },
        { key: 'bio_q1',   name: '生物 大問1', icon: '🧬', timeMin: 30, qCount: 1, scoreMax: 30, desc: '分子生物/遺伝/代謝 (医学部含)' },
      ],
      // MARCH 理工 (2026-05-22 塾長指示: 中レベル本試水準 q1 系を追加)
      march_rikei: [
        { key: 'math_basic',   name: '数学 (基礎演習)', icon: '📐', timeMin: 25, qCount: 5, scoreMax: 50, desc: '微積分/ベクトル/確率/数列' },
        { key: 'phys_basic_q', name: '物理 (基礎演習)', icon: '⚛️', timeMin: 25, qCount: 5, scoreMax: 50, desc: '力学/電磁気/波動/熱' },
        { key: 'chem_basic_q', name: '化学 (基礎演習)', icon: '🧪', timeMin: 25, qCount: 5, scoreMax: 50, desc: '理論/無機/有機' },
        { key: 'math_q1',  name: '数学 大問1 (本試水準)', icon: '📐', timeMin: 25, qCount: 1, scoreMax: 25, desc: '明治/青学/立教/中央/法政 標準' },
        { key: 'phys_q1',  name: '物理 大問1 (本試水準)', icon: '⚛️', timeMin: 25, qCount: 1, scoreMax: 25, desc: '力学/電磁気/波動 標準' },
        { key: 'chem_q1',  name: '化学 大問1 (本試水準)', icon: '🧪', timeMin: 25, qCount: 1, scoreMax: 25, desc: '理論+有機 標準型' },
        { key: 'bio_q1',   name: '生物 大問1 (本試水準)', icon: '🧬', timeMin: 25, qCount: 1, scoreMax: 25, desc: '細胞/遺伝/生態 標準' },
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

  // 📚 大学入試 文系 (古文・漢文・現代文要約・日本史・世界史・地理・公民) - 塾長指示 2026-05-14
  // exam_id は backend では 'daigaku' に mapping される (_getBackendExamParams 経由)
  bunkei: {
    id: 'bunkei',
    name: '大学入試 文系',
    flag: '📚',
    color: '#f472b6',
    scoreMin: 0, scoreMax: 100, scoreUnit: '点',
    requiresGrade: true,
    grades: [
      // 古文
      { key: 'kobun_kyotsu',    name: '古文 (共通テスト)',  cefr: '基礎',   target: '共通テスト 古文 (本文 + 設問・現代語訳・文法)' },
      { key: 'kobun_todai',     name: '古文 (東大)',        cefr: '最難関', target: '東大 国語 古文 (記述式・心理把握・比喩解釈)' },
      { key: 'kobun_kyodai',    name: '古文 (京大)',        cefr: '最難関', target: '京大 国語 古文 (記述式)' },
      // 漢文
      { key: 'kanbun_kyotsu',   name: '漢文 (共通テスト)',  cefr: '基礎',   target: '共通テスト 漢文 (返り点・書き下し・現代語訳)' },
      { key: 'kanbun_todai',    name: '漢文 (東大)',        cefr: '最難関', target: '東大 国語 漢文 (記述式・思想把握)' },
      { key: 'kanbun_kyodai',   name: '漢文 (京大)',        cefr: '最難関', target: '京大 国語 漢文 (記述式)' },
      // 現代文要約
      { key: 'r_summary_todai', name: '現代文要約 (東大)', cefr: '最難関', target: '東大 国語 大問1B 要約 60-80字' },
      // 社会
      { key: 'nihonshi_kyotsu', name: '日本史 (共通テスト)', cefr: '基礎',  target: '共通テスト 日本史 (古代~近現代 通史・史料読解)' },
      { key: 'sekaishi_kyotsu', name: '世界史 (共通テスト)', cefr: '基礎',  target: '共通テスト 世界史 (古代~現代 東西通史)' },
      { key: 'chiri_kyotsu',    name: '地理 (共通テスト)',   cefr: '基礎',  target: '共通テスト 地理 (自然/人文/地誌)' },
      { key: 'kouminka_kyotsu', name: '公民 (共通テスト)',   cefr: '基礎',  target: '共通テスト 公民 (政経/倫理 融合)' },
    ],
    // 各 grade に対する単一 section。_backendPart/_backendGrade で backend マッピング
    sectionsByGrade: {
      kobun_kyotsu:    [{ key: 'kobun',     name: '古文 演習 (共通テスト型)', icon: '📜', timeMin: 25, qCount: 5, scoreMax: 50, desc: '本文 + 設問・現代語訳・文法', _backendPart: 'kobun',     _backendGrade: 'kyotsu' }],
      kobun_todai:     [{ key: 'kobun',     name: '古文 演習 (東大型)',       icon: '📜', timeMin: 30, qCount: 5, scoreMax: 50, desc: '東大型 記述式古文 (心理把握・比喩解釈)', _backendPart: 'kobun',     _backendGrade: 'todai' }],
      kobun_kyodai:    [{ key: 'kobun',     name: '古文 演習 (京大型)',       icon: '📜', timeMin: 30, qCount: 5, scoreMax: 50, desc: '京大型 記述式古文 (抽象的論理思想)', _backendPart: 'kobun',     _backendGrade: 'kyodai' }],
      kanbun_kyotsu:   [{ key: 'kanbun',    name: '漢文 演習 (共通テスト型)', icon: '🀄', timeMin: 25, qCount: 5, scoreMax: 50, desc: '返り点 + 書き下し + 現代語訳', _backendPart: 'kanbun',    _backendGrade: 'kyotsu' }],
      kanbun_todai:    [{ key: 'kanbun',    name: '漢文 演習 (東大型)',       icon: '🀄', timeMin: 30, qCount: 5, scoreMax: 50, desc: '東大型 記述式漢文 (思想把握・哲学的議論)', _backendPart: 'kanbun',    _backendGrade: 'todai' }],
      kanbun_kyodai:   [{ key: 'kanbun',    name: '漢文 演習 (京大型)',       icon: '🀄', timeMin: 30, qCount: 5, scoreMax: 50, desc: '京大型 記述式漢文 (抽象的論理思想)', _backendPart: 'kanbun',    _backendGrade: 'kyodai' }],
      r_summary_todai: [{ key: 'r_summary', name: '現代文要約 演習 (東大型)', icon: '✍️', timeMin: 25, qCount: 1, scoreMax: 30, desc: '東大 国語 大問1B 要約 60-80字', _backendPart: 'r_summary', _backendGrade: 'todai' }],
      nihonshi_kyotsu: [{ key: 'nihonshi',  name: '日本史 演習 (共通テスト型)', icon: '🗾', timeMin: 25, qCount: 5, scoreMax: 50, desc: '古代~近現代 通史・年代並べ替え・史料読解', _backendPart: 'nihonshi',  _backendGrade: 'kyotsu' }],
      sekaishi_kyotsu: [{ key: 'sekaishi',  name: '世界史 演習 (共通テスト型)', icon: '🌍', timeMin: 25, qCount: 5, scoreMax: 50, desc: '東西通史・年代/文化史', _backendPart: 'sekaishi',  _backendGrade: 'kyotsu' }],
      chiri_kyotsu:    [{ key: 'chiri',     name: '地理 演習 (共通テスト型)',   icon: '🗺️', timeMin: 25, qCount: 5, scoreMax: 50, desc: '自然/人文/地誌・気候/プレート/災害', _backendPart: 'chiri',     _backendGrade: 'kyotsu' }],
      kouminka_kyotsu: [{ key: 'kouminka',  name: '公民 演習 (共通テスト型)',   icon: '⚖️', timeMin: 25, qCount: 5, scoreMax: 50, desc: '政経/倫理 融合・憲法/三権分立/基本的人権', _backendPart: 'kouminka',  _backendGrade: 'kyotsu' }],
    },
    topics: ['古典文法', '助動詞', '係り結び', '敬語', '漢文句法', '再読文字', '通史 (日本史)', '通史 (世界史)', '気候区分', 'プレートテクトニクス', '人口', '憲法', '三権分立', '基本的人権'],
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
async function callClaudeJson({ system, user, model = MODEL_DEFAULT, maxTokens = 4000, images = null, timeoutMs = 30000 }) {
  // 1) 生徒ログイン済みなら backend proxy 経由 (生徒ブラウザにキー不要・本番Live)
  // 2) フォールバック: localStorage に APIキーがあれば従来の直接呼び出し (CEO/管理者用)
  // 🚨 2026-05-21 塾長指示「pool/AI 両 hang で『準備中』永遠 pending 防止」:
  //   AbortController + 30s timeout を実装 (Anthropic API は通常 5-20s で返るので 30s は十分なマージン)
  const sessionToken = localStorage.getItem('ai_juku_session_token')
    || localStorage.getItem('ai_juku_admin_token');
  const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
    ? 'http://localhost:8000' : window.location.origin;

  // 🆕 2026-05-13: 写真採点対応 - images があれば Anthropic content array に image block を追加
  // images: [{ media_type: 'image/jpeg', data: 'base64...', label: 'Q1' }, ...]
  let content;
  if (Array.isArray(images) && images.length > 0) {
    content = [];
    images.forEach(img => {
      if (img.label) content.push({ type: 'text', text: `--- ${img.label} (写真で提出された答案) ---` });
      content.push({
        type: 'image',
        source: { type: 'base64', media_type: img.media_type, data: img.data },
      });
    });
    content.push({ type: 'text', text: user });
  } else {
    content = user;
  }

  // 🛟 AbortController で hang を物理的に断つ (clearTimeout で正常完了時の memory leak 防止)
  const _ctrl = new AbortController();
  const _timer = setTimeout(() => _ctrl.abort(), timeoutMs);

  let data;
  try {
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
          messages: [{ role: 'user', content: content }],
        }),
        signal: _ctrl.signal,
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
          messages: [{ role: 'user', content: content }],
        }),
        signal: _ctrl.signal,
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`Claude API ${res.status}: ${t.slice(0, 200)}`);
      }
      data = await res.json();
    }
  } catch (e) {
    if (e && e.name === 'AbortError') {
      throw new Error(`AI 応答タイムアウト (${Math.round(timeoutMs / 1000)} 秒)。再試行してください。`);
    }
    throw e;
  } finally {
    clearTimeout(_timer);
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

// 🎯 2026-05-15 塾長指示「科目別に変更」: クイックスタートで選んだ科目 (math/phys/chem/bio/earth/
//   kokugo/jhist/whist/geo/civ/ethics) を localStorage から取得して、grade/section をフィルタする。
const QS_SUBJECT_HINT_KEY = 'ai_juku_qs_subject_hint';
function _getQsSubjectHint() {
  try { return localStorage.getItem(QS_SUBJECT_HINT_KEY) || ''; } catch (_) { return ''; }
}
function _qsSubjectHintLabel(hint) {
  return ({
    math:'📐 数学', phys:'⚛️ 物理', chem:'🧪 化学', bio:'🧬 生物', earth:'🌍 地学',
    kokugo:'📖 国語', jhist:'🗾 日本史', whist:'🌐 世界史', geo:'🗺 地理', civ:'⚖️ 政経', ethics:'📿 倫理',
  })[hint] || '';
}
function _qsHintMatchesKey(key, hint) {
  if (!hint || !key) return true;
  // section の key prefix で判定 (math_q1, phys_basic, kobun, kanbun, nihonshi 等)
  const prefixMap = {
    math:   /^math/,
    phys:   /^phys/,
    chem:   /^chem/,
    bio:    /^bio/,
    earth:  /^earth/,
    kokugo: /^(kobun|kanbun|r_summary)/,
    jhist:  /^nihonshi/,
    whist:  /^sekaishi/,
    geo:    /^chiri/,
    civ:    /^kouminka/,  // 公民は政経/倫理一体
    ethics: /^kouminka/,
  };
  return prefixMap[hint] ? prefixMap[hint].test(key) : true;
}
// 大学が subject hint に該当する section を持つかチェック (大学プルダウン filter 用)
function _univHasSubjectSections(examId, univKey, hint) {
  if (!hint) return true;
  const exam = EXAMS[examId];
  if (!exam || !exam.sectionsByGrade) return true;
  const sections = exam.sectionsByGrade[univKey] || exam.sectionsByGrade._default || [];
  return sections.some(s => _qsHintMatchesKey(s.key, hint));
}
// 大学プルダウン option の subject-specific label を生成
// (例: hint=phys + univKey=todai_rikei → "物理 大問1 (力学) / 物理 大問2 (電磁気) / 物理 大問3 (波/熱)")
function _univSubjectLabel(examId, univKey, hint) {
  if (!hint) return '';
  const exam = EXAMS[examId];
  if (!exam || !exam.sectionsByGrade) return '';
  const matching = (exam.sectionsByGrade[univKey] || exam.sectionsByGrade._default || [])
    .filter(s => _qsHintMatchesKey(s.key, hint));
  if (matching.length === 0) return '';
  if (matching.length > 3) {
    return matching.slice(0, 3).map(s => s.name).join(' / ') + ` 他 ${matching.length - 3} 大問`;
  }
  return matching.map(s => s.name).join(' / ');
}

// 🎯 2026-05-13: daigaku/rikei 用 select-based grade picker
// 30+ 大学を category 別 optgroup でまとめる + select change で即遷移
function _renderGradeSelect(grid, examId, items) {
  // カテゴリ分類
  const categorize = (k) => {
    if (examId === 'daigaku') {
      if (['todai', 'kyodai', 'osaka', 'tokoda', 'hitotsu', 'nagoya', 'hokudai', 'tohoku', 'kyushu', 'kobe', 'yokokoku', 'chiba', 'tsukuba'].includes(k)) return { cat: '国公立', order: 1 };
      if (['igakubu_kokoritsu', 'igakubu_shiritsu'].includes(k)) return { cat: '医学部', order: 4 };
      if (k === 'kyotsu' || k === 'center') return { cat: '共通テスト・センター', order: 0 };
      return { cat: '私立', order: 2 };
    } else if (examId === 'rikei') {
      if (k === 'kyotsu_rikei') return { cat: '共通テスト・センター', order: 0 };
      if (['todai_rikei', 'kyodai_rikei', 'osaka_rikei', 'tokoda_rikei', 'nagoya_rikei'].includes(k)) return { cat: '国公立', order: 1 };
      if (['igakubu_kokoritsu_rikei', 'igakubu_shiritsu_rikei'].includes(k)) return { cat: '医学部', order: 4 };
      if (k === 'march_rikei') return { cat: '私立 (MARCH 等)', order: 3 };
      return { cat: '私立', order: 2 };
    } else if (examId === 'bunkei') {
      // 大学入試文系: 科目別グルーピング (塾長指示 2026-05-14)
      if (k.startsWith('kobun_'))     return { cat: '📜 古文', order: 0 };
      if (k.startsWith('kanbun_'))    return { cat: '🀄 漢文', order: 1 };
      if (k.startsWith('r_summary_')) return { cat: '✍️ 現代文要約', order: 2 };
      if (k.startsWith('nihonshi_'))  return { cat: '🗾 日本史', order: 3 };
      if (k.startsWith('sekaishi_'))  return { cat: '🌍 世界史', order: 4 };
      if (k.startsWith('chiri_'))     return { cat: '🗺️ 地理', order: 5 };
      if (k.startsWith('kouminka_'))  return { cat: '⚖️ 公民', order: 6 };
      return { cat: 'その他', order: 99 };
    }
    return { cat: 'その他', order: 99 };
  };
  // 🎯 2026-05-15 クイックスタート科目フィルタ:
  //   bunkei は grade key そのものが subject を表すので prefix で絞り込む (例: hint=kokugo → kobun_*)
  //   rikei は大学 key で subject 別に区別できないので sectionsByGrade を見て「その subject の大問がある大学のみ」表示
  // どちらも該当 0 件なら fallback で全表示
  const _qsHint = _getQsSubjectHint();
  let _filteredItems = items;
  if (examId === 'bunkei' && _qsHint) {
    _filteredItems = items.filter(g => _qsHintMatchesKey(g.key, _qsHint));
    if (_filteredItems.length === 0) _filteredItems = items;
  } else if (examId === 'rikei' && _qsHint) {
    _filteredItems = items.filter(g => _univHasSubjectSections('rikei', g.key, _qsHint));
    if (_filteredItems.length === 0) _filteredItems = items;
  }
  // group by category
  const groups = {};
  _filteredItems.forEach(g => {
    const cat = categorize(g.key);
    if (!groups[cat.cat]) groups[cat.cat] = { order: cat.order, items: [] };
    groups[cat.cat].items.push(g);
  });
  const sortedCats = Object.keys(groups).sort((a, b) => groups[a].order - groups[b].order);

  // build select
  const wrapper = document.createElement('div');
  wrapper.className = 'grade-select-wrapper';
  wrapper.style.cssText = 'max-width: 640px; margin: 1.5rem auto; padding: 0 1rem;';
  // 🎯 2026-05-15 hint が設定されているときはラベルに subject を明示
  const _subjLabel = _qsHint ? _qsSubjectHintLabel(_qsHint) : '';
  const label = examId === 'daigaku' ? '🎓 受験する大学/試験を選択'
              : examId === 'rikei'   ? (_subjLabel ? `${_subjLabel} を受験する大学/レベルを選択` : '🔬 大学/レベルを選択')
              : examId === 'bunkei'  ? (_subjLabel ? `${_subjLabel} を学ぶ大学/レベルを選択` : '📚 科目とレベルを選択')
              : '大学/レベルを選択';
  // 🎯 hint clear ボタン (科目フィルタが効いている時のみ)
  const _clearBtnHtml = _qsHint
    ? `<button type="button" id="qsGradeClearBtn" style="margin-left:0.6rem; padding:0.3rem 0.7rem; background:rgba(99,102,241,0.4); border:0; border-radius:6px; color:#fff; font-weight:700; font-size:0.78rem; cursor:pointer;">✕ ${escapeHtml(_subjLabel)} 解除</button>`
    : '';
  // 🎚️ 2026-05-21 塾長指示: 難易度レベル絞り込みプルダウン (rikei + bunkei 用)
  // cefr フィールドを使った filter。レベル選択で大学プルダウン options を hide/show 連動
  // 🚨 daigaku の cefr は "B2-C1"/"B1-B2" 等 CEFR 表記なので、日本語ラベル (基礎/最難関 等) のみ抽出
  const _levelOrder = ['基礎', '中上級', '上級', '難関', '最難関'];
  const _availableLevels = Array.from(new Set(_filteredItems.map(g => g.cefr).filter(lv => lv && _levelOrder.includes(lv))));
  const _levelEmojis = { '基礎': '🌱', '中上級': '📘', '上級': '🔬', '難関': '🎯', '最難関': '🏆' };
  const _levelTooltips = {
    '基礎': '共通テスト・基礎演習中心 (高 1-2 / 基礎固め)',
    '中上級': 'MARCH 理工・標準演習',
    '上級': '早慶上智・東工大・私立医 等',
    '難関': '阪大・名大・東工大',
    '最難関': '東大・京大・国公立医学部',
  };
  _availableLevels.sort((a, b) => (_levelOrder.indexOf(a) - _levelOrder.indexOf(b)));
  const _levelSelectHtml = (_availableLevels.length >= 2) ? `
    <div style="margin-bottom: 0.9rem;">
      <label style="display:block; font-size:0.95rem; color:#10b981; font-weight:700; margin-bottom:0.4rem;">🎚️ 難易度レベルで絞り込み (任意)</label>
      <select id="levelSelectPulldown" style="
        width: 100%;
        padding: 0.7rem 1rem;
        background: rgba(16,185,129,0.08);
        border: 2px solid rgba(16,185,129,0.4);
        border-radius: 10px;
        color: #fff;
        font-size: 0.95rem;
        font-weight: 600;
        cursor: pointer;
        appearance: auto;
        -webkit-appearance: menulist;
      ">
        <option value="">すべてのレベル (${_filteredItems.length}校)</option>
        ${_availableLevels.map(lv => {
          const cnt = _filteredItems.filter(g => g.cefr === lv).length;
          const emoji = _levelEmojis[lv] || '';
          const tip = _levelTooltips[lv] || '';
          return `<option value="${escapeHtml(lv)}" style="background:#0f172a; color:#fff;">${emoji} ${escapeHtml(lv)} (${cnt}校${tip ? '・' + escapeHtml(tip) : ''})</option>`;
        }).join('')}
      </select>
      <p style="margin-top: 0.3rem; font-size: 0.78rem; color: #94a3b8;">レベルを選ぶと、下の大学プルダウンが絞り込まれます。</p>
    </div>
  ` : '';
  wrapper.innerHTML = `
    <label style="display:block; font-size:1rem; color:#a78bfa; font-weight:700; margin-bottom:0.6rem;">${label}${_clearBtnHtml}</label>
    ${_levelSelectHtml}
    <select id="gradeSelectPulldown" style="
      width: 100%;
      padding: 0.9rem 1rem;
      background: rgba(0,0,0,0.4);
      border: 2px solid rgba(167,139,250,0.5);
      border-radius: 12px;
      color: #fff;
      font-size: 1.05rem;
      font-weight: 600;
      cursor: pointer;
      appearance: auto;
      -webkit-appearance: menulist;
    ">
      <option value="">-- 選んでください --</option>
      ${sortedCats.map(catName => {
        const grp = groups[catName];
        return `<optgroup label="${escapeHtml(catName)} (${grp.items.length}校)" style="background:#1f2937; color:#fbbf24;">
          ${grp.items.map(g => {
            // 🎯 hint があれば subject-specific label を優先表示 (例: "東京大学 理系 — 物理 大問1/2/3")
            const subjText = _qsHint ? _univSubjectLabel(examId, g.key, _qsHint) : '';
            const suffix = subjText ? (' — ' + subjText) : (g.target ? ' — ' + g.target : '');
            return `<option value="${escapeHtml(g.key)}" style="background:#0f172a; color:#fff;">${escapeHtml(g.name)}${escapeHtml(suffix)}</option>`;
          }).join('')}
        </optgroup>`;
      }).join('')}
    </select>
    <p style="margin-top: 0.6rem; font-size: 0.82rem; color: #94a3b8; line-height: 1.55;">
      💡 ${examId === 'daigaku' ? '志望大学の出題傾向に完全準拠した問題で演習できます。共通テスト・センター試験 (2005年〜) も網羅。' : examId === 'bunkei' ? '古文・漢文・現代文要約・日本史・世界史・地理・公民 — 共通テスト / 東大型 / 京大型 に完全準拠。' : '大学ごとの数学/物理/化学/生物の出題傾向に準拠。図/数式 (LaTeX) 対応。'}
    </p>
    <div id="gradeSelectInfo" style="margin-top: 1rem; padding: 1rem; background: rgba(167,139,250,0.06); border: 1px solid rgba(167,139,250,0.20); border-radius: 10px; display: none;">
      <div id="gradeSelectInfoName" style="font-size:1.05rem; color:#fbbf24; font-weight:800; margin-bottom:0.3rem;"></div>
      <div id="gradeSelectInfoTarget" style="font-size:0.88rem; color:#cbd5e1; margin-bottom:0.4rem;"></div>
      <div id="gradeSelectInfoCefr" style="font-size:0.85rem; color:#94a3b8;"></div>
    </div>
  `;
  grid.appendChild(wrapper);

  const sel = document.getElementById('gradeSelectPulldown');
  const info = document.getElementById('gradeSelectInfo');
  const infoName = document.getElementById('gradeSelectInfoName');
  const infoTarget = document.getElementById('gradeSelectInfoTarget');
  const infoCefr = document.getElementById('gradeSelectInfoCefr');

  // 🎚️ 2026-05-21 塾長指示: レベル絞り込みプルダウンの change ハンドラ
  // レベル選択 → 大学プルダウンの option を cefr で hide/show + optgroup の visible 制御
  const levelSel = document.getElementById('levelSelectPulldown');
  if (levelSel && sel) {
    levelSel.addEventListener('change', () => {
      const level = levelSel.value;
      // 全 option を見て、cefr 一致のものだけ hidden=false に
      // 🚨 2026-05-22 塾長指摘 fix: Safari の <select> 内 option は hidden 属性を無視するため、
      //    display:none + disabled 多重化で WebKit でも確実に hide (Chrome/Firefox の hidden も維持)
      Array.from(sel.querySelectorAll('option')).forEach(opt => {
        if (!opt.value) { opt.hidden = false; opt.disabled = false; opt.style.display = ''; return; } // -- 選んでください --
        const g = _filteredItems.find(x => x.key === opt.value);
        if (!g) { opt.hidden = false; opt.disabled = false; opt.style.display = ''; return; }
        const shouldHide = !!level && g.cefr !== level;
        opt.hidden = shouldHide;
        opt.disabled = shouldHide;           // Safari: hidden 無視するが disabled は効く (選択不可化)
        opt.style.display = shouldHide ? 'none' : '';  // Chrome/Firefox: display:none で完全消失
      });
      // optgroup の表示制御 (全 option が hidden なら optgroup も hide)
      Array.from(sel.querySelectorAll('optgroup')).forEach(grp => {
        const visible = Array.from(grp.querySelectorAll('option')).some(o => !o.hidden);
        grp.hidden = !visible;
        grp.disabled = !visible;             // Safari fallback (optgroup ごと選択不可)
        grp.style.display = visible ? '' : 'none';  // Chrome/Firefox: 完全消失
        // 件数表示も更新
        const visibleCount = Array.from(grp.querySelectorAll('option')).filter(o => !o.hidden).length;
        const origLabel = (grp.getAttribute('data-orig-label') || grp.label || '').replace(/ \(\d+校\)$/, '');
        if (!grp.getAttribute('data-orig-label')) grp.setAttribute('data-orig-label', origLabel);
        grp.label = `${origLabel} (${visibleCount}校)`;
      });
      // 既存選択をクリア + info を隠す
      sel.value = '';
      if (info) info.style.display = 'none';
    });
  }

  sel.addEventListener('change', () => {
    const key = sel.value;
    if (!key) {
      info.style.display = 'none';
      return;
    }
    const g = items.find(x => x.key === key);
    if (!g) return;
    // 選択した大学の info を表示
    if (info) info.style.display = '';
    if (infoName) infoName.textContent = g.name;
    if (infoTarget) infoTarget.textContent = g.target ? '🎯 ' + g.target : '';
    if (infoCefr) infoCefr.textContent = g.cefr ? 'CEFR ' + g.cefr + ' 相当' : '';
    // state 更新 + pickExamSections へ自動遷移 (300ms 遅延でアニメーション表示)
    state.eikenGrade = g.key;
    state.eikenGradeName = g.name;
    setTimeout(() => pickExamSections(examId), 250);
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
    } else if (examId === 'bunkei') {
      if (eyebrow) eyebrow.textContent = 'STEP 2 / 大学入試 文系';
      if (h2) h2.textContent = '📚 科目とレベルを選んでください';
      if (desc) desc.textContent = '古文・漢文・現代文要約・日本史・世界史・地理・公民 — 共通テスト / 東大型 / 京大型 を網羅。';
    } else {
      if (eyebrow) eyebrow.textContent = 'STEP 2 / 英検';
      if (h2) h2.textContent = '🇯🇵 受験する級を選んでください';
      if (desc) desc.textContent = '級ごとに part 構成・配点・難易度が異なります。各 part 個別対策が可能です。';
    }
  }
  const grid = document.getElementById('gradeGrid');
  grid.innerHTML = '';
  const items = exam.grades || EXAMS.eiken.grades;

  // 🎯 2026-05-13 塾長指示「もっと選択しやすいプルダウン式」:
  // daigaku (30+ 大学) / rikei (11 大学) はカテゴリ別 optgroup の select に切替。
  // bunkei (11 グレード) も同じく optgroup pulldown (塾長指示 2026-05-14)。
  // 英検 (12 級) はカード式のままにする (適切な数 + 視覚的に魅力的)。
  if (examId === 'daigaku' || examId === 'rikei' || examId === 'bunkei') {
    _renderGradeSelect(grid, examId, items);
    // 🎯 ページ最上部ではなく gradePickSection にスクロール (プルダウンが画面中央)
    const gradeSec = document.getElementById('gradePickSection');
    if (gradeSec) {
      setTimeout(() => gradeSec.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
    }
    return;
  }

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
  // 🎯 2026-05-13: ページ最上部ではなく gradePickSection (= 級/大学選択画面) にスクロール
  const gradeSec = document.getElementById('gradePickSection');
  if (gradeSec) {
    setTimeout(() => gradeSec.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
  } else {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function pickExam(examId) {
  const exam = EXAMS[examId];
  if (!exam) return;
  state.examId = examId;
  state.sectionKey = null;
  state.eikenGrade = null;
  // 🎯 2026-05-13 pool-first 戦略: 試験を切り替えた時点で「復習モード」を解除
  //    (これがないと一度 ?topic= URL で入った生徒が永続 AI モードになり API 課金が発生する致命傷)
  state.currentTopic = null;
  state.isReviewMode = false;
  try {
    const url = new URL(window.location.href);
    let dirty = false;
    if (url.searchParams.has('review')) { url.searchParams.delete('review'); dirty = true; }
    if (url.searchParams.has('topic')) { url.searchParams.delete('topic'); dirty = true; }
    if (dirty) window.history.replaceState({}, '', url);
  } catch (e) { /* silent */ }
  // 🚫 2026-05-13 塾長指示「大学入試の部分にこれは不要」: 大学入試/理系では LIVE NEWS READING を非表示
  // 英語試験 (英検/TOEFL/TOEIC/IELTS) でのみ意味があるセクション
  const newsSec = document.getElementById('newsReadingSection');
  if (newsSec) {
    if (examId === 'daigaku' || examId === 'rikei') {
      newsSec.style.display = 'none';
    } else {
      newsSec.style.display = '';
    }
  }
  // 英検 / 大学入試 は級・大学選択を先に挟む (requiresGrade=true)
  if (exam.requiresGrade) {
    showGradePicker(examId);
    return;
  }
  pickExamSections(examId);
}

// 🆕 2026-05-23 塾長指示「P0: qCount vs 実 pool ミスマッチ可視化」
// pool-counts public endpoint からの cache (TTL 5min)
// 致命対応 (3 視点 review): null sentinel で「fetch 失敗 → 在庫表示なし fallback」を表現
// 致命対応: 1.5s timeout で section card 描画固まり防止
let _poolCountCache = null;
let _poolCountCacheAt = 0;
async function _fetchPoolCounts() {
  const now = Date.now();
  if (_poolCountCache && (now - _poolCountCacheAt) < 5 * 60 * 1000) return _poolCountCache;
  try {
    const ctrl = (typeof AbortController !== 'undefined') ? new AbortController() : null;
    const timer = ctrl ? setTimeout(() => { try { ctrl.abort(); } catch (_) {} }, 1500) : null;
    const r = await fetch(`${BACKEND_URL}/api/exam-questions/pool-counts`, ctrl ? { signal: ctrl.signal } : {});
    if (timer) clearTimeout(timer);
    if (!r.ok) return null; // sentinel: fetch 失敗 → 在庫表示なし fallback
    const d = await r.json();
    const map = {};
    for (const it of (d.items || [])) {
      map[`${it.exam}/${it.part}/${it.grade}`] = Number(it.count) || 0;
    }
    _poolCountCache = map;
    _poolCountCacheAt = now;
    return map;
  } catch (e) {
    return null; // sentinel: timeout/network エラー → 在庫表示なし fallback (全 disable は致命傷)
  }
}
function _getPoolCount(poolMap, examId, partKey, grade) {
  if (poolMap === null || poolMap === undefined) return null; // sentinel propagate
  const g = grade || '_default';
  // 大学入試は eiken_grade に大学キーが入っている (rikei/daigaku/bunkei は state.eikenGrade)
  const v = poolMap[`${examId}/${partKey}/${g}`];
  return (v === undefined) ? 0 : v;
}

async function pickExamSections(examId) {
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
        : (examId === 'bunkei' && state.eikenGrade)
          ? ((EXAMS.bunkei && EXAMS.bunkei.sectionsByGrade && EXAMS.bunkei.sectionsByGrade[state.eikenGrade]) || [])
          : exam.sections;
  // 🎯 2026-05-15 クイックスタート科目フィルタ: rikei/bunkei では subject hint で sections を絞り込む
  const _qsHint2 = _getQsSubjectHint();
  let _filteredSections = sections;
  if ((examId === 'rikei' || examId === 'bunkei') && _qsHint2) {
    _filteredSections = sections.filter(s => _qsHintMatchesKey(s.key, _qsHint2));
    if (_filteredSections.length === 0) _filteredSections = sections; // 該当無しは全表示
  }
  state.currentSections = _filteredSections;
  const grid = document.getElementById('sectionGrid');
  grid.innerHTML = '';
  // フィルタ表示バナー (hint があり実際に絞られた場合のみ)
  if (_qsHint2 && _filteredSections.length < sections.length) {
    const banner = document.createElement('div');
    banner.className = 'qs-filter-banner';
    banner.style.cssText = 'grid-column:1/-1; margin-bottom:0.8rem; padding:0.7rem 1rem; background:rgba(251,191,36,0.15); border:1px solid rgba(251,191,36,0.5); border-radius:10px; color:#fef3c7; font-size:0.88rem; font-weight:700; display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;';
    banner.innerHTML = `
      <span>⚡ クイックスタート: ${escapeHtml(_qsSubjectHintLabel(_qsHint2))} の大問のみ表示中</span>
      <button type="button" id="qsClearFilterBtn" style="margin-left:auto; padding:0.35rem 0.8rem; background:rgba(99,102,241,0.4); border:0; border-radius:6px; color:#fff; font-weight:700; font-size:0.82rem; cursor:pointer;">すべて表示</button>
    `;
    grid.appendChild(banner);
    banner.querySelector('#qsClearFilterBtn').addEventListener('click', () => {
      try { localStorage.removeItem(QS_SUBJECT_HINT_KEY); } catch (_) {}
      pickExamSections(examId); // 再描画
    });
  }
  // 🆕 P0: 各 section の実 pool 在庫を取得 (cache 5min・1 fetch で全 ROTATION の count を得る)
  const poolMap = await _fetchPoolCounts();
  const _grade = state.eikenGrade || '_default';

  _filteredSections.forEach(sec => {
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'section-card';
    card.dataset.section = sec.key;
    // 🆕 P0: pool 在庫を qCount と比較し UI 表示制御
    // poolCount === null → fetch 失敗 (sentinel) → 在庫表示なし・従来通り (致命対応)
    const poolCount = _getPoolCount(poolMap, examId, sec.key, _grade);
    const hasPool = poolCount !== null;
    const isZero = hasPool && poolCount === 0;
    const isLow = hasPool && poolCount > 0 && poolCount < (sec.qCount || 1);
    let specHtml;
    if (isZero) {
      // pool=0: 「準備中」+ disable
      specHtml = `${sec.timeMin}分 / <span style="color:#f87171;font-weight:700;">⚠️ 準備中</span>`;
    } else if (isLow) {
      // pool < qCount: 在庫数を黄色で併記
      specHtml = `${sec.timeMin}分 / ${sec.qCount}問 <span style="color:#fbbf24;font-size:0.85em;font-weight:700;">(在庫 ${poolCount}問)</span>`;
    } else {
      // 在庫充足 or fetch 失敗 (sentinel フォールバック・従来表示)
      specHtml = `${sec.timeMin}分 / ${sec.qCount}問`;
    }
    card.innerHTML = `
      <div class="section-card-icon">${sec.icon}</div>
      <div class="section-card-name">${sec.name}</div>
      <div class="section-card-spec">${specHtml}</div>
      <div class="section-card-desc">${sec.desc}</div>
    `;
    if (isZero) {
      card.disabled = true;
      card.style.opacity = '0.5';
      card.style.cursor = 'not-allowed';
      card.setAttribute('aria-disabled', 'true');
      card.setAttribute('aria-label', `${sec.name}: 問題プール準備中・別の大問を選んでください`);
      card.title = '問題プール準備中: 別の大問を選んでください';
    }
    card.addEventListener('click', () => {
      // disabled は HTML attribute で click event が発火しないため alert 不要 (UX 視点改善案)
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

  // 🎯 2026-05-13 塾長指示「上にスクロールされて探すのが面倒」: ページ最上部ではなく
  // examDetailSection (= 大問選択画面) にスムーズスクロールしてユーザの注意を導く
  const detail = document.getElementById('examDetailSection');
  if (detail) {
    setTimeout(() => detail.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
  } else {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
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
  // 🎯 2026-05-13 pool-first: 通常は pool から即取り出し (~0.5 秒) なので
  //    「AI が生成中」と決めつけない。
  // 🛠 2026-05-18 fix (塾長指摘「30秒かかる」): topic 指定 (state.currentTopic) 時も
  //    backend が topic LIKE 検索対応済 (main.py:14292) のため pool-first で十分。
  //    ?review=1 明示時のみ AI 生成 message 表示。
  const _isReviewLoading = (() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      return sp.get('review') === '1';
    } catch { return false; }
  })();
  document.getElementById('questionBox').innerHTML = _isReviewLoading
    ? '<p class="ee-loading">🤖 AI が復習用に類題を生成中... <span style="color:#94a3b8; font-size:0.85em;">(個別最適化のため 10〜30 秒)</span></p>'
    : '<p class="ee-loading">📚 問題を準備中... <span style="color:#94a3b8; font-size:0.85em;">(pool から即取得 ~0.5 秒)</span></p>';
  document.getElementById('submitAnswersBtn').disabled = true;
  // 💡 「解答・解説を見る」ボタンも問題ロード前は無効化 (renderQuestions 完了後に有効化)
  const _revealBtnReset = document.getElementById('revealAnswersBtn');
  if (_revealBtnReset) {
    _revealBtnReset.disabled = true;
    _revealBtnReset.textContent = '💡 解答・解説を見る';
  }
  state.startedAt = Date.now();
  startTimer(section.timeMin);
  document.getElementById('cancelRunBtn').onclick = () => {
    stopTimer();
    document.getElementById('examRunnerSection').style.display = 'none';
    document.getElementById('examDetailSection').style.display = '';
  };
  // 塾長指示 2026-04-30: 問題本文 (examRunnerSection) 位置まで自動スクロール
  // 旧: window.scrollTo({ top: 0 }) はページ最上部に戻すだけで、問題本文は画面外のまま
  // 新: examRunnerSection の位置に nav bar 60px offset 込みで移動
  setTimeout(() => {
    const runner = document.getElementById('examRunnerSection');
    if (runner) {
      const rect = runner.getBoundingClientRect();
      const targetY = window.scrollY + rect.top - 60;
      window.scrollTo({ top: Math.max(0, targetY), behavior: 'smooth' });
    }
  }, 50);
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
/**
 * 現在ログイン中の生徒 ID を取得 (auth-guard.js 経由)。
 * 生徒解答履歴に基づく重複/学習進捗フィルタを backend に効かせる。
 * 取得失敗時は null (未ログイン or 古い localStorage)。
 */
function getCurrentStudentId() {
  try {
    if (window.AuthGuard && typeof window.AuthGuard.getStudent === 'function') {
      const student = window.AuthGuard.getStudent();
      if (student && student.id) return student.id;
    }
    // fallback: 旧 localStorage キーから直接 (後方互換)
    const raw = localStorage.getItem('ai_juku_session_student');
    if (raw) {
      const s = JSON.parse(raw);
      if (s && s.id) return s.id;
    }
  } catch (e) { /* silent */ }
  return null;
}

/**
 * 現在 state から「主要トピック」を1つ推定して返す。
 * 大学入試/英検は eikenGradeName・examTopics 配列・section name から優先順位で抽出。
 * 該当無ければ null (param 付加スキップ)。
 */
function getCurrentTopicHint() {
  try {
    const exam = (state && state.examId) ? EXAMS[state.examId] : null;
    if (exam && Array.isArray(exam.topics) && exam.topics.length > 0) {
      // exam.topics は固定配列なので最初の要素をヒントとして使う
      // (renderProblems / generateAndShowQuestions と同じく state に明示があれば優先)
      if (state.currentTopic) return String(state.currentTopic);
      return String(exam.topics[0]);
    }
  } catch (e) { /* silent */ }
  return null;
}

// バックエンドから DB蓄積問題を取得して AUTO_GENERATED_BANKS にセット
// 戻り値: { selected, count, all } または null (失敗時)
// 📚 大学入試文系 (bunkei) → backend は daigaku 扱い (塾長指示 2026-05-14)
// state.examId='bunkei' / state.eikenGrade='kobun_todai' / state.sectionKey='kobun'
// → backend (exam_id='daigaku', part_key='kobun', eiken_grade='todai')
function _getBackendExamParams(examId, sectionKey, eikenGrade) {
  if (examId === 'bunkei') {
    const sections = (EXAMS.bunkei && EXAMS.bunkei.sectionsByGrade && EXAMS.bunkei.sectionsByGrade[eikenGrade]) || [];
    const sec = sections.find(s => s.key === sectionKey) || sections[0];
    return {
      exam: 'daigaku',
      part: (sec && sec._backendPart) || sectionKey,
      grade: (sec && sec._backendGrade) || eikenGrade,
    };
  }
  return { exam: examId, part: sectionKey, grade: eikenGrade };
}

// 🎯 pool-first 戦略 (2026-05-13): generateAndShowQuestions が await して即時利用する
//
// 🛟 2026-05-16 塾長指示「pool がまだないと出てくる」対策:
//   localhost preview (port 8090) で localhost:8000 が起動していない場合に
//   fallback メッセージを表示する事故が発生していた。CORS allowlist に
//   localhost:8090 → production が登録済なので、localhost で fetch 失敗時は
//   production URL に retry することで preview でも本番 pool を使えるようにする。
const PRODUCTION_API_BASE = 'https://ai-juku-api-production.up.railway.app';
async function prefetchAutoGenerated(examId, sectionKey, eikenGrade) {
  // bunkei → daigaku に backend params をマッピング (塾長指示 2026-05-14)
  const _be = _getBackendExamParams(examId, sectionKey, eikenGrade);
  const backendExam = _be.exam;
  const backendPart = _be.part;
  const backendGrade = _be.grade;
  const params = new URLSearchParams({ exam: backendExam, part: backendPart, limit: 20 });
  if (backendGrade) params.set('eiken_grade', backendGrade);
  if (backendExam === 'daigaku' && backendGrade) params.set('univ', backendGrade);
  // 新 backend ロジック: student_id があれば「既出題回避 + 弱点優先」、topic があれば単元一致優先
  const studentId = getCurrentStudentId();
  if (studentId) params.set('student_id', String(studentId));
  const topicHint = getCurrentTopicHint();
  if (topicHint) params.set('topic', topicHint);
  const isLocalhost = (window.location.hostname === 'localhost' && window.location.port === '8090');
  const primaryBackend = isLocalhost ? 'http://localhost:8000' : window.location.origin;
  // 試行する URL list (primary 失敗時に production にフォールバック)
  const backends = isLocalhost ? [primaryBackend, PRODUCTION_API_BASE] : [primaryBackend];
  // 🛟 2026-05-16 塾長指示「pool 部分提供で時短+解決」+ 3 視点 review (Resilience Architect):
  //   localStorage 5 分 TTL cache を併設し、production cold start や瞬断時に graceful degrade。
  const cacheKey = `exam_pool_cache:${examId}/${(eikenGrade || '_')}/${sectionKey}`;
  const CACHE_TTL_MS = 5 * 60 * 1000;
  try {
    let res = null;
    let lastErr = null;
    let fallbackUsed = false;
    let data = null;
    // 🔁 silent auto-retry: 1 回失敗で諦めず 800ms 待って再試行 (transient 5xx / cold start 吸収)
    for (let attempt = 0; attempt < 2 && (!data || !data.selected); attempt++) {
      for (let bi = 0; bi < backends.length; bi++) {
        const backend = backends[bi];
        // 🛟 timeout: localhost=3s (fast-fail to production fallback), production=12s (cold start 許容)
        const isLocalBackend = backend.startsWith('http://localhost');
        const timeoutMs = isLocalBackend ? 3000 : 12000;
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), timeoutMs);
        // 🛡 production fallback 時は dev_preview=1 を付けて Railway access log を分離
        let url = `${backend}/api/exam-questions/bank?` + params;
        if (bi > 0 && backend === PRODUCTION_API_BASE) {
          url += '&dev_preview=1';
        }
        try {
          // 🛟 cache: 'no-store' で Service Worker / browser cache の古い JS 応答を回避
          //    credentials: 'same-origin' で session cookie を送信 (cross-origin は送らない)
          res = await fetch(url, {
            signal: ctrl.signal,
            cache: 'no-store',
            credentials: 'same-origin',
          });
          clearTimeout(timer);
          if (res && res.ok) {
            if (bi > 0) fallbackUsed = true;
            break;
          }
          lastErr = `HTTP ${res ? res.status : '?'} from ${backend}`;
          res = null;
        } catch (e) {
          clearTimeout(timer);
          lastErr = `${backend}: ${e?.message || e}`;
          res = null;
        }
      }
      // parse して selected があれば成功 break
      if (res && res.ok) {
        try { data = await res.json(); } catch (e) { data = null; }
        if (data && data.selected) break;
      }
      // 1 回目失敗 → 800ms wait → retry (合計 2 試行)
      if (attempt === 0) {
        await new Promise(r => setTimeout(r, 800));
        console.warn('[exam] pool fetch retry (attempt 2/2):', lastErr);
      }
    }
    if (fallbackUsed) {
      console.log('[exam] 🔁 production fallback used (localhost backend unreachable)');
    }
    if (!data || !data.selected) {
      // 🛟 全試行失敗 → localStorage cache から graceful degrade
      try {
        const raw = localStorage.getItem(cacheKey);
        if (raw) {
          const cached = JSON.parse(raw);
          if (cached && cached.t && (Date.now() - cached.t) < CACHE_TTL_MS && cached.data && cached.data.selected) {
            console.log(`[exam] 💾 pool cache hit (${Math.round((Date.now() - cached.t)/1000)}s old)`);
            return cached.data;
          }
        }
      } catch (e) { /* localStorage 失敗は ignore */ }
      console.warn('[exam] pool fetch failed on all attempts + cache miss:', lastErr);
      if (data) {
        // backend は応答したが selected null (count=0 等)
        console.log(`[exam] pool miss for ${examId}/${sectionKey}/${eikenGrade || '-'} (count=${data.count || 0})`);
        return data;
      }
      return null;
    }
    window.AUTO_GENERATED_BANKS = window.AUTO_GENERATED_BANKS || {};
    window.AUTO_GENERATED_BANKS[examId] = window.AUTO_GENERATED_BANKS[examId] || {};
    // 英検 / 大学入試 は compoundKey で保存
    const storeKey = ((examId === 'eiken' || examId === 'daigaku' || examId === 'bunkei') && eikenGrade) ? `${eikenGrade}_${sectionKey}` : sectionKey;
    window.AUTO_GENERATED_BANKS[examId][storeKey] = data.selected;
    console.log(`[exam] 📚 pool hit ${data.count} questions for ${examId}/${storeKey}` + (studentId ? ` (student=${studentId})` : '') + (topicHint ? ` topic=${topicHint}` : ''));
    // 🛟 localStorage cache 保存 (次回 fetch 失敗時の graceful degrade 用)
    try {
      localStorage.setItem(cacheKey, JSON.stringify({ t: Date.now(), data }));
    } catch (e) { /* QuotaExceeded 等は ignore */ }
    // セッション attempt push hook (app.js の sessionState を共有・関数があれば活用)
    try {
      // data.selected は単一の payload (passage + questions[]) — questions 配列を push
      const questions = (data.selected && Array.isArray(data.selected.questions)) ? data.selected.questions : [];
      if (questions.length && typeof window._pushSessionAttempt === 'function') {
        if (window.__examSessionState && window.__examSessionState.active) {
          window.__examSessionState.problems = window.__examSessionState.problems || [];
          questions.forEach(q => {
            const pid = q.id || q.pid || ('q_' + Math.random().toString(36).slice(2, 10));
            if (!window.__examSessionState.problems.some(p => p.pid === pid)) {
              window.__examSessionState.problems.push({
                pid,
                topic: q.topic || topicHint || '',
                univ: (examId === 'daigaku' || examId === 'rikei' || examId === 'bunkei') ? (eikenGrade || '') : '',
                year: q.year || (data.selected && data.selected.year_simulated) || '',
                source: examId + '/' + (storeKey || sectionKey),
              });
            }
          });
        }
      }
    } catch (e) { /* silent: session hook 失敗で bank 読み込みを止めない */ }
    return data;
  } catch (e) {
    console.warn('[exam] Failed to prefetch auto-generated bank:', e);
    return null;
  }
}

async function generateAndShowQuestions(exam, section, full = false) {
  // 🎯 Pool-first 戦略 (2026-05-13 塾長指示):
  // 「元々データがあるものは即時 pool から取り出し (¥0・~200ms)、
  //  AI を使うのは復習で最適化したい時のみ」
  //
  // 判定ルール (2026-05-18 fix・pool-first 徹底):
  // - URL ?review=1 → 明示的に復習モード (AI で弱点最適化)
  // - ?topic=XXX or state.currentTopic → topic LIKE 検索の hint として pool fetch に渡す
  //   (backend は topic 一致を優先・miss しても全 pool fallback で返却)
  // - 通常 → pool から即取り出し (¥0・~0.5 秒)
  // - pool miss (count=0) → AI 生成 → AI 失敗 → 静的フォールバック
  const reviewParams = (() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      const topicParam = sp.get('topic');
      if (topicParam) state.currentTopic = topicParam;
      // 🛠 fix: topic 指定でも pool-first にする (backend が topic LIKE 対応済)
      // ?review=1 明示時のみ AI 生成直行
      return { isReview: sp.get('review') === '1', topicParam };
    } catch { return { isReview: false, topicParam: null }; }
  })();
  const isReviewMode = reviewParams.isReview;
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
  } else if (state.examId === 'bunkei' && state.eikenGradeName) {
    eikenGradeLabel = `（${state.eikenGradeName}・${(EXAMS.bunkei.grades.find(g => g.key === state.eikenGrade) || {}).cefr || ''}）`;
  }

  // 大学入試: ランダムに 2005-2026 の年度を選んで「○○大学 ○年度入試の類題」スタイルで生成
  const daigakuYear = (state.examId === 'daigaku' || state.examId === 'rikei' || state.examId === 'bunkei') ? (2005 + Math.floor(Math.random() * 22)) : null;

  // 試験別の出題ニュアンス
  const daigakuUniv = state.examId === 'daigaku' ? (state.eikenGradeName || '大学入試') : '';
  const daigakuTargets = state.examId === 'daigaku' ? ((EXAMS.daigaku.grades.find(g => g.key === state.eikenGrade) || {}).target || '') : '';
  const rikeiUniv = state.examId === 'rikei' ? (state.eikenGradeName || '大学入試 理系') : '';
  const rikeiTargets = state.examId === 'rikei' ? ((EXAMS.rikei.grades.find(g => g.key === state.eikenGrade) || {}).target || '') : '';
  // 文系科目 (bunkei) の科目・レベル抽出
  const bunkeiTargets = state.examId === 'bunkei' ? ((EXAMS.bunkei.grades.find(g => g.key === state.eikenGrade) || {}).target || '') : '';
  const bunkeiName = state.examId === 'bunkei' ? (state.eikenGradeName || '大学入試 文系') : '';
  const bunkeiBackendPart = state.examId === 'bunkei' && section ? (section._backendPart || section.key) : '';
  const bunkeiBackendGrade = state.examId === 'bunkei' && section ? (section._backendGrade || '') : '';
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
    bunkei: `日本の大学入試 文系科目 (${bunkeiName}・${daigakuYear || 2024}年度入試レベル相当)。出題傾向: ${bunkeiTargets}。
重要原則:
- **問題文・選択肢・解答・解説のすべてを日本語で出力** (英語 NG)。古典 (古文・漢文) は原文 + 書き下し + 現代語訳を含む。
- 過去問の丸写しは著作権上 NG。「出題形式に完全準拠した類題」を作成すること。
- ${bunkeiBackendPart === 'kobun' ? '古文: 公有財産の古典 (枕草子/徒然草/源氏物語/伊勢物語/土佐日記/紫式部日記 等) または教育用創作。本文末に【出典】を明記。古典文法 (助動詞・係り結び・敬語) と古今異義語を必ず織り込む。'
       : bunkeiBackendPart === 'kanbun' ? '漢文: 公有財産の古典 (論語/孟子/荘子/史記/老子/韓非子/荀子 等 pre-1500 PD)。【白文】【書き下し文】【現代語訳】の 3 段構成。再読文字・反語・使役・置き字を必ず織り込む。'
       : bunkeiBackendPart === 'r_summary' ? '現代文要約: 評論/エッセイ系の本格的日本語文章 (800-1200 字)。設問は「60-80字で要約」型。論理構造把握と圧縮表現が中核。'
       : bunkeiBackendPart === 'nihonshi' ? '日本史: 古代~近現代の通史。年代並べ替え・史料読解・テーマ史 (政治/経済/外交/文化) を織り交ぜる。1 史料 + 5 設問構成が標準。'
       : bunkeiBackendPart === 'sekaishi' ? '世界史: 古代~現代の東西通史。年代/文化史/西洋哲学/東洋思想を織り交ぜる。地図/系図/年表があれば figure_svg に inline SVG で。'
       : bunkeiBackendPart === 'chiri' ? '地理: 自然 (気候/プレート/災害) ・人文 (人口/都市/農業) ・地誌の融合。ケッペン気候区分・統計データ読解・地図問題が頻出。'
       : bunkeiBackendPart === 'kouminka' ? '公民: 日本国憲法・三権分立・基本的人権・国際政治経済の融合。政経 (経済理論/財政/金融) と倫理 (西洋哲学/東洋思想) を織り交ぜる。'
       : '文系科目の出題傾向に準拠。'}
- ${bunkeiBackendGrade === 'todai' ? '東大型: 記述式中心。心理把握・比喩解釈・思想史的構造把握など深い論理力を問う設問。'
       : bunkeiBackendGrade === 'kyodai' ? '京大型: 抽象的論理・思想対比 (東洋 vs 西洋哲学等) ・難解な記述式。'
       : '共通テスト型: 4 択多肢選択中心。教科書頻出範囲から出題、基礎~標準難度。'}
- 解説は **日本語** で「本文の解釈→正解の根拠→誤答の不適切な理由→関連知識」の構造。
- **絶対遵守**: 出力に教師名 (関正生・富田・林修 等) を一切含めない。`,
  }[exam.id] || '';

  // 📚 bunkei (文系科目) / rikei (理系科目) は日本語問題で英語前提を除外する
  const isJapaneseSubject = (state.examId === 'bunkei' || state.examId === 'rikei');
  const _commonStrict = isJapaneseSubject
    ? `- 公式の出題形式と完全に一致させる
- 問題文・選択肢・解答・解説のすべてを **日本語** で出力 (英語の使用は引用/原典のみ)
- 解説は日本語で、正解の根拠 + 誤答の不適切な理由 + 関連知識を3行以上
- ${state.examId === 'bunkei' ? '古典 (古文・漢文) は本文 + 書き下し (漢文の場合) + 現代語訳 + 出典を必ず含める' : '理系は数式 LaTeX + 図 SVG (必要に応じて)'}`
    : `- 公式の出題形式と完全に一致させる (TOEIC Part 2 なら3択、TOEFL Reading なら長文+設問、IELTS Listening Section 1 なら社会的会話のみ、英検準1級 Reading 大問1 なら短文穴埋め4択 18問形式)
- 設問の英文は ETS / British Council / 英検協会 が出すレベルのナチュラル英語 (機械翻訳臭/不自然な語彙NG)
- 解説は日本語で、正解の根拠 + 他選択肢の誤りポイント + 関連語彙/文法 を3行以上
- Speaking / Writing は採点ルーブリック (構成 / 語彙 / 文法 / 流暢さ or 一貫性) に基づく評価コメント付きの模範解答
- 英検なら級レベルの語彙統制 (1級は CEFR C1 語彙、5級は中学初級語彙)`;
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
${_commonStrict}`;

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

  let payload = null;
  // questionSource: 'pool' | 'ai_review' | 'ai_fresh' | 'fallback' | 'unknown' (UI badge 用)
  let questionSource = 'unknown';

  // 1) Pool-first: 通常モードなら DB 蓄積問題を即時取り出し (¥0・~200ms)
  //    復習モード (isReviewMode) のみ AI 生成にスキップ
  if (!isReviewMode) {
    try {
      const poolStart = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
      const poolData = await prefetchAutoGenerated(exam.id, section.key, state.eikenGrade);
      const poolMs = ((typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now()) - poolStart;
      if (poolData && poolData.selected && Array.isArray(poolData.selected.questions) && poolData.selected.questions.length > 0) {
        // 🎯 Pool HIT: 即時利用 (AI 呼び出しなし・コスト¥0)
        const sel = poolData.selected;
        // 🎯 A 案 (2026-05-13): qCount 未達なら data.all から複数 payload の questions を集約
        //   - context-bound (passage/audio_script/prompt あり) は単一 payload のみ使用 (Reading 等で
        //     異なる passage の question を混ぜると教材として破綻するため)
        //   - 大問サブ問題チェーン ((1)→(2)→(3) で前問の結果を使う共テ/二次型) も集約禁止
        //   - 図/グラフを参照する question は parent payload の figure_svg と一緒でないと破綻
        //   - 重複 dedup は backend が割る _question_id (server/main.py:13607) を優先・stem 比較は fallback

        // 🛡 review fix #1: 空白文字列も context として扱う (whitespace truthy 落とし穴)
        const _ctxStr = (s) => (typeof s === 'string' ? s.trim() : '');
        const hasContext = !!(_ctxStr(sel.passage) || _ctxStr(sel.audio_script) || _ctxStr(sel.prompt));

        // 🛡 review fix #2 (pedagogy CRITICAL): 大問サブ問題チェーン検知
        //   primary payload が「(1)(2)(3)...」または「問1 問2」の連続 sub-question 型なら
        //   chain 内の問題は単一 payload で完結させる必要があるため aggregation を禁止
        const _isSubQuestionStem = (s) => {
          const t = (typeof s === 'string' ? s.trim() : '');
          if (!t) return false;
          // 数字 (半/全角)・丸数字・括弧書き・問N
          return /^(\(?\s*[12２３3]\s*\)?|（\s*[12２３3]\s*）|[②③]|問\s*[2-9])/.test(t);
        };
        const isDaimonChain = sel.questions.length >= 2 && _isSubQuestionStem(sel.questions[1]?.stem);

        // 🛡 review fix #3 (UX CRITICAL): 図参照を含む質問は parent payload の figure_svg が
        //   無いと破綻 (「図1を見よ」「the graph below」等)。集約候補に取り込まない。
        const _refsFigure = (q) => {
          const s = (typeof q?.stem === 'string' ? q.stem : '') + ' ' + (typeof q?.explanation === 'string' ? q.explanation : '');
          return /図\s*\d*|グラフ|表\s*\d|the\s+(figure|graph|diagram|chart)|下\s*記?\s*の\s*(図|グラフ|表)/i.test(s);
        };

        let aggregated = [...sel.questions];
        let aggregatedFrom = 1; // 集約元の payload 数
        let aggregateBlocked = ''; // 集約禁止理由 (UI 用)
        // 🎯 2026-05-15 塾長指示「600 問の反映数が少ない」: context-bound (長文付き) でも
        //   passage を「【長文1】【長文2】」と連結して複数 payload から集約するように変更。
        //   大問サブ問題チェーンは引き続き禁止 (1 問だけ取り出すと破綻)。
        if (isDaimonChain) aggregateBlocked = 'daimon_chain';

        // 🎯 multi-passage 集約用: 長文 block を順に保持
        const passageBlocks = [];
        if (hasContext) {
          passageBlocks.push({
            passage: _ctxStr(sel.passage),
            audio_script: _ctxStr(sel.audio_script),
            prompt: _ctxStr(sel.prompt),
            figure_svg: _ctxStr(sel.figure_svg),
            label: '長文 1',
          });
        }

        if (!aggregateBlocked && aggregated.length < qCount && Array.isArray(poolData.all)) {
          // dedup 用: selected の _question_id と stem を baseline に
          const seenIds = new Set();
          const seenStems = new Set();
          if (sel._question_id != null) seenIds.add(sel._question_id);
          aggregated.forEach(q => { if (q?.stem) seenStems.add(String(q.stem).trim()); });

          for (const item of poolData.all) {
            if (aggregated.length >= qCount) break;
            if (!item) continue;
            // 重複 payload skip (selected と同一)
            if (item._question_id != null && seenIds.has(item._question_id)) continue;
            if (!Array.isArray(item.questions) || item.questions.length === 0) continue;
            // この item 自体が大問チェーン型なら丸ごと skip
            if (item.questions.length >= 2 && _isSubQuestionStem(item.questions[1]?.stem)) continue;

            const itemHasAudio = !!_ctxStr(item.audio_script);
            const itemHasPassage = !!_ctxStr(item.passage);
            const itemHasPrompt = !!_ctxStr(item.prompt);
            const itemHasContext = itemHasAudio || itemHasPassage || itemHasPrompt;
            const itemHasFigure = !!_ctxStr(item.figure_svg);

            // 🎯 context-bound section では context-bound payload のみ採用 (passage 混在は OK)。
            //    context-free section では context-bound payload を skip (既存挙動)。
            //    ただし audio (listening) の混在は UX 破綻のため別 audio を持つ payload は skip。
            if (hasContext && !itemHasContext) continue;
            if (!hasContext && itemHasContext) continue;
            if (hasContext && _ctxStr(sel.audio_script) && itemHasAudio
                && _ctxStr(sel.audio_script) !== _ctxStr(item.audio_script)) {
              // 元 selected が audio script を持つ場合、別 script との混在は禁止 (listening UX 破綻)
              continue;
            }

            const need = qCount - aggregated.length;
            let takenFromItem = 0;
            const _willBePassageNum = passageBlocks.length + 1; // この item から取った question に付ける長文番号
            for (const q of item.questions) {
              if (aggregated.length >= qCount || takenFromItem >= need) break;
              if (!q) continue;
              // 図参照 question は parent の figure_svg が無いと skip
              if (_refsFigure(q) && !itemHasFigure) continue;
              const qStem = (typeof q.stem === 'string' ? q.stem.trim() : '');
              if (qStem && seenStems.has(qStem)) continue;
              const taken = hasContext ? { ...q, _passageLabel: `長文 ${_willBePassageNum}` } : q;
              aggregated.push(taken);
              if (qStem) seenStems.add(qStem);
              takenFromItem++;
            }
            if (item._question_id != null) seenIds.add(item._question_id);
            if (takenFromItem > 0) {
              aggregatedFrom++;
              if (hasContext) {
                passageBlocks.push({
                  passage: _ctxStr(item.passage),
                  audio_script: _ctxStr(item.audio_script),
                  prompt: _ctxStr(item.prompt),
                  figure_svg: _ctxStr(item.figure_svg),
                  label: `長文 ${_willBePassageNum}`,
                });
              }
            }
          }
        }

        // 🎯 hasContext mode で multi-passage 集約が発生した場合: passage を結合 + 各 question に prefix
        let _outPassage = sel.passage || '';
        let _outAudio = sel.audio_script || '';
        let _outPrompt = sel.prompt || '';
        let _outFigure = sel.figure_svg || '';
        if (hasContext && passageBlocks.length > 1) {
          // selected の questions (最初の n 問) には「長文 1」prefix を付与
          const firstLabel = passageBlocks[0].label;
          const _selCount = sel.questions.length;
          aggregated = aggregated.map((q, idx) => {
            const stem = (q && typeof q.stem === 'string') ? q.stem : '';
            const cleanStem = stem.replace(/^【長文\s*\d+】\s*/, '');
            const label = q?._passageLabel || (idx < _selCount ? firstLabel : firstLabel);
            return { ...q, stem: `【${label}】 ${cleanStem}` };
          });
          _outPassage = passageBlocks
            .filter(p => p.passage)
            .map(p => `【${p.label}】\n\n${p.passage}`)
            .join('\n\n──────────\n\n');
          _outAudio = passageBlocks.filter(p => p.audio_script)
            .map(p => `【${p.label}】\n${p.audio_script}`).join('\n\n');
          _outPrompt = passageBlocks.filter(p => p.prompt)
            .map(p => `【${p.label}】 ${p.prompt}`).join('\n\n');
          // figure_svg は最初に見つかった 1 つを表示 (multi-figure は UI 困難)
          const firstFig = passageBlocks.find(p => p.figure_svg);
          if (firstFig) _outFigure = firstFig.figure_svg;
        }

        // ID を q1, q2, ... に振り直し (集約で衝突する可能性があるため)
        aggregated = aggregated.map((q, i) => ({ ...q, id: `q${i + 1}` }));
        payload = {
          passage: _outPassage,
          audio_script: _outAudio,
          prompt: _outPrompt,
          figure_svg: _outFigure,
          questions: aggregated.slice(0, qCount),
        };
        // 🛡 review fix #5: warning 文言は「pool/集約」等の技術用語を避け生徒向けに
        if (payload.questions.length < qCount) {
          if (aggregateBlocked === 'daimon_chain') {
            payload._warning = `📝 ${payload.questions.length} 問を表示中 (リクエスト ${qCount} 問)・本問は大問サブ問題が連結しているため単一の組から出題しています。`;
          } else {
            payload._warning = `📝 ${payload.questions.length} 問を表示中 (リクエスト ${qCount} 問)。本セクションのストックが不足しています。「🎯 復習用に AI で類題作成」で個別最適化された残りを生成できます。`;
          }
        } else if (aggregatedFrom > 1) {
          if (hasContext && passageBlocks.length > 1) {
            payload._warning = `📚 ${passageBlocks.length} つの長文 (本セクションのストック) から計 ${payload.questions.length} 問を出題`;
          } else {
            payload._warning = `📚 本セクション全体から ${payload.questions.length} 問を組み合わせて出題`;
          }
        }
        questionSource = 'pool';
        console.log(`[exam] 📚 pool hit: ${payload.questions.length}/${qCount} questions (aggregated from ${aggregatedFrom} payloads, blocked=${aggregateBlocked || 'none'}, ${Math.round(poolMs)}ms, total in pool=${poolData.count})`);
      } else {
        console.log(`[exam] 📚 pool miss for ${exam.id}/${section.key}/${state.eikenGrade || '-'} (${Math.round(poolMs)}ms) → AI 生成にフォールバック`);
      }
    } catch (e) {
      console.warn('[exam] pool fetch failed, will try AI generation:', e);
    }
  } else {
    console.log(`[exam] 🤖 review mode (topic="${reviewParams.topicParam || state.currentTopic}") → AI 生成で個別最適化`);
  }

  // 2) Pool miss or 復習モード → AI 生成
  if (!payload && isLiveMode()) {
    try {
      payload = await callClaudeJson({ system, user, model: MODEL_DEFAULT, maxTokens: 4000 });
      questionSource = isReviewMode ? 'ai_review' : 'ai_fresh';
      console.log(`[exam] 🤖 AI generated (${questionSource}): ${(payload && payload.questions || []).length} questions`);
    } catch (e) {
      // 🚨 2026-05-21 塾長指示 fix: timeout / network error を state.lastAiError に保存 (silent fallback の罠回避)
      //   旧: console.warn のみ → demo にすり替え → 生徒は「タイムアウトしたから再試行を」と気付けない
      //   新: state.lastAiError に message 保存 → renderQuestions で生徒に明示エラー + 再試行 button 表示
      console.warn('[exam] AI generation failed, falling back to sample bank:', e);
      state.lastAiError = (e && e.message) || String(e || 'AI 生成失敗');
      payload = null;
    }
  } else if (!payload && !isLiveMode()) {
    // 🛡 C1: AI 未接続 (デモ build / 設定不備) は別 badge で識別
    console.warn('[exam] live mode disabled (no session/admin/api key); skipping AI');
  }
  // 3) 最終フォールバック: 静的バンク or 警告メッセージ
  if (!payload || !payload.questions || !payload.questions.length) {
    const prevSource = questionSource;
    payload = demoQuestions(exam, section, qCount, topic);
    // pool miss → AI fail → demo の場合と、no-live の場合を区別
    questionSource = (!isLiveMode() && prevSource === 'unknown') ? 'fallback_no_live' : 'fallback';
    // lastAiError がある時は「タイムアウト/通信エラーで再試行を」と payload に明示メッセージ
    if (state.lastAiError) {
      payload._warning = `⚠️ AI 生成に失敗 (${state.lastAiError.slice(0, 80)})。下記は参考問題です。`;
      payload._retryable = true;
    }
  } else {
    // 成功 path で lastAiError を clear (前回失敗 → 今回成功なら badge 不要)
    delete state.lastAiError;
  }

  // UI badge 用: state に源泉を記録
  state.questionSource = questionSource;
  state.isReviewMode = isReviewMode;

  try {
    state.questions = payload.questions || [];
    state.passage = payload.passage || '';
    state.audioScript = payload.audio_script || '';
    state.prompt = payload.prompt || '';
    state.figureSvg = payload.figure_svg || '';
    state.warning = payload._warning || '';  // フォールバック警告 (偽問題なし設計)
    state.retryable = payload._retryable === true;  // 🚨 2026-05-21: AI 失敗 → demo fallback 時の retry button gate (silent fallback 防止)
    state.userAnswers = {};
    renderQuestions();
    document.getElementById('submitAnswersBtn').disabled = false;
    document.getElementById('submitAnswersBtn').onclick = submitAnswers;
    // 💡 「解答・解説を見る」ボタンも有効化 (解かずに学習する用)
    const _revealBtn = document.getElementById('revealAnswersBtn');
    if (_revealBtn) {
      _revealBtn.disabled = false;
      _revealBtn.onclick = revealAllAnswersAndExplanations;
    }
  } catch (e) {
    console.error(e);
    document.getElementById('questionBox').innerHTML = `
      <div class="ee-error">
        <strong>⚠️ 問題生成に失敗しました</strong>
        <p>サーバーが混み合っている可能性があります。少し時間をおいて再度お試しください。</p>
      </div>`;
  }
}

// 💡 2026-05-16 塾長指示「解かなくても解説が出るようにシステムを追加」:
// 「解答・解説を見る」button → 全問の正解 + 解説を一括表示 (採点 endpoint を経由せず即時)
// multiple_choice: 正答 choice をハイライト + 解説をその場に展開
// short_answer/essay/speaking/translation: 模範解答 + 解説 を展開
function revealAllAnswersAndExplanations() {
  if (!Array.isArray(state.questions) || state.questions.length === 0) {
    alert('問題が読み込まれていません。');
    return;
  }
  if (!confirm('解かずに全問の正解と解説を表示します。\n\n⚠️ 学習用機能のため:\n・採点記録・スコア換算には残りません\n・弱点 TOP3 分析の対象外になります\n・本番想定なら「📤 提出して採点」を選んでください\n\n表示しますか?')) return;
  const box = document.getElementById('questionBox');
  if (!box) return;
  state.questions.forEach((q) => {
    // 1) multiple_choice: 正答ハイライト + 解説展開
    if (q.type === 'multiple_choice' && Array.isArray(q.choices) && q.choices.length) {
      const correct = parseInt(q.answer, 10);
      const validIdx = Number.isInteger(correct) && correct >= 0 && correct < q.choices.length;
      box.querySelectorAll(`.ee-choice-btn[data-qid="${q.id}"]`).forEach(b => {
        b.classList.add('graded');
        const cci = parseInt(b.dataset.choice, 10);
        if (validIdx && cci === correct) b.classList.add('is-correct');
        b.disabled = true;
      });
      const explainBox = box.querySelector(`.ee-instant-explain[data-qid="${q.id}"]`);
      if (explainBox) {
        explainBox.style.display = '';
        explainBox.classList.add('locked', 'reveal');
        const correctLabel = validIdx
          ? `${String.fromCharCode(65 + correct)} (${escapeTextWithMath(q.choices[correct] || '')})`
          : '(正答未登録)';
        explainBox.innerHTML = `
          <div class="ee-instant-head" style="color:#fbbf24;">📖 解答表示 (学習用) <span class="ee-instant-correct">正解: ${correctLabel}</span></div>
          <div class="ee-instant-body">${escapeTextWithMath(q.explanation || '解説はありません。')}</div>`;
        if (typeof applyKatex === 'function') applyKatex(explainBox);
      }
    } else {
      // 2) 記述系 (short_answer/essay/speaking/translation): 模範解答 + 解説
      const qBlock = box.querySelector(`.ee-question[data-qid="${q.id}"]`);
      if (qBlock && !qBlock.querySelector('.ee-reveal-essay')) {
        // q.answer は string 想定だが、import 経路によっては object/array の可能性 → safe stringify
        const modelAnswer = (typeof q.answer === 'string' && q.answer.trim())
          ? q.answer
          : (q.answer != null ? JSON.stringify(q.answer) : '(模範解答が登録されていません)');
        const div = document.createElement('div');
        div.className = 'ee-reveal-essay ee-instant-explain locked reveal';
        div.style.cssText = 'display:block; margin-top:0.8rem; padding:1rem; background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.35); border-radius:10px;';
        div.innerHTML = `
          <div class="ee-instant-head" style="color:#fbbf24; font-weight:700; margin-bottom:0.5rem;">📖 解答表示 (学習用)</div>
          <div style="margin-bottom:0.6rem; color:#e5e7eb;"><strong style="color:#fbbf24;">模範解答:</strong><br>${escapeTextWithMath(modelAnswer)}</div>
          <div style="color:#cbd5e1; line-height:1.7;"><strong style="color:#fbbf24;">解説:</strong><br>${escapeTextWithMath(q.explanation || '解説はありません。')}</div>`;
        qBlock.appendChild(div);
        if (typeof applyKatex === 'function') applyKatex(div);
      }
      // textarea は disabled に
      qBlock?.querySelectorAll('textarea, .ee-text-input').forEach(el => { el.disabled = true; });
    }
  });
  // 💡 events 記録: study_mode reveal 使用回数を analytics で追跡 (CEO ダッシュ集計用)
  try {
    const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
      ? 'http://localhost:8000' : window.location.origin;
    const studentId = (typeof getCurrentStudentId === 'function') ? getCurrentStudentId() : null;
    const meta = {
      student_id: studentId, exam_id: state.examId, part_key: state.sectionKey,
      eiken_grade: state.eikenGrade, q_count: state.questions.length,
      revealed_at: new Date().toISOString(),
    };
    if (typeof fetch === 'function') {
      fetch(backend + '/api/track', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'exam_answer_revealed', props: meta,
          session_id: studentId ? `student:${studentId}` : 'anonymous',
        }),
      }).catch(() => {});  // fire-and-forget
    }
  } catch (e) { /* analytics 失敗は学習体験に影響させない */ }
  // 採点ボタンは無効化 (学習モードと整合)
  const submitBtn = document.getElementById('submitAnswersBtn');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = '✓ 学習モード (採点対象外)';
  }
  const revealBtn = document.getElementById('revealAnswersBtn');
  if (revealBtn) {
    revealBtn.disabled = true;
    revealBtn.textContent = '✓ 表示済み';
  }
  // 最初の解説までスクロール
  setTimeout(() => {
    const firstExplain = box.querySelector('.ee-instant-explain.reveal');
    if (firstExplain) firstExplain.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 100);
}
// global export (HTML inline onclick から呼ばれない設計だが、testability + IIFE 対策で export)
if (typeof window !== 'undefined') window.revealAllAnswersAndExplanations = revealAllAnswersAndExplanations;

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
// 2026-05-13 塾長指示「紙の参考書のような数式」: $..$ inline delimiter を追加 + pretifyMath 前処理
// 🚩 2026-05-13 塾長指示「選択肢が間違っている問題もある」:
// 生徒からの問題違和感報告を backend に POST → 塾長 CEO ダッシュで集計表示
async function _reportQuestionIssue(q, reason) {
  const sessionToken = localStorage.getItem('ai_juku_session_token')
    || localStorage.getItem('ai_juku_admin_token');
  const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
    ? 'http://localhost:8000' : window.location.origin;
  const payload = {
    question_id: q.id,
    exam_id: state.examId,
    section_key: state.sectionKey,
    grade_key: state.eikenGrade,
    stem: (q.stem || '').slice(0, 500),
    choices: q.choices || null,
    correct_answer: q.answer,
    explanation: (q.explanation || '').slice(0, 800),
    reason: String(reason).slice(0, 500),
    reported_at: new Date().toISOString(),
    page_url: window.location.href,
    user_agent: navigator.userAgent.slice(0, 200),
  };
  // 専用 endpoint があれば使う・なければ既存 events 経由
  // ai-juku backend に /api/student/report-question-issue を将来追加するが、
  // 暫定は既存 /api/events/client (sendBeacon 形式) でも可
  try {
    const res = await fetch(`${backend}/api/student/report-question-issue`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(sessionToken ? { 'Authorization': 'Bearer ' + sessionToken } : {}),
      },
      body: JSON.stringify(payload),
    });
    if (res.ok) return true;
    // 404 等で endpoint 不在の場合: localStorage に貯めて塾長が後で確認
    throw new Error('endpoint_missing:' + res.status);
  } catch (e) {
    // フォールバック: localStorage に蓄積 (塾長が CEO ダッシュで確認できる将来)
    try {
      const KEY = 'ai_juku_question_issues';
      const arr = JSON.parse(localStorage.getItem(KEY) || '[]');
      arr.push(payload);
      // 最新 50 件のみ保持
      if (arr.length > 50) arr.splice(0, arr.length - 50);
      localStorage.setItem(KEY, JSON.stringify(arr));
      console.info('[issue-report] saved to localStorage (' + arr.length + ' items pending sync)');
      return true; // localStorage に貯めたので「成功」扱い
    } catch (_) {
      throw e;
    }
  }
}

// 🎯 2026-05-13 教育アプリ UX: 進捗バー (Q3/10 + bar fill + 残り表示)
function _initProgressBar() {
  const wrap = document.getElementById('progressWrap');
  if (!wrap) return;
  const total = (state.questions || []).length;
  if (total === 0) {
    wrap.style.display = 'none';
    return;
  }
  wrap.style.display = '';
  _updateProgressBar();
}

function _updateProgressBar() {
  const wrap = document.getElementById('progressWrap');
  if (!wrap) return;
  const questions = state.questions || [];
  const total = questions.length;
  if (total === 0) return;

  // 回答済 = userAnswers に値があるか photo upload 済
  let done = 0;
  questions.forEach(q => {
    const ans = state.userAnswers ? state.userAnswers[q.id] : undefined;
    const photo = state.userAnswerPhotos ? state.userAnswerPhotos[q.id] : undefined;
    if ((ans !== undefined && ans !== null && String(ans).trim() !== '') || photo) {
      done++;
    }
  });

  const todo = total - done;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  const labelEl = document.getElementById('progressLabel');
  const doneEl = document.getElementById('progressDone');
  const todoEl = document.getElementById('progressTodo');
  const fillEl = document.getElementById('progressBarFill');

  if (labelEl) labelEl.textContent = `進捗: ${done} / ${total} 問 (${pct}%)`;
  if (doneEl) doneEl.textContent = done;
  if (todoEl) todoEl.textContent = todo;
  if (fillEl) fillEl.style.width = pct + '%';

  // 全問回答済になったら submit ボタンを目立たせる
  const submitBtn = document.getElementById('submitAnswersBtn');
  if (submitBtn && done === total && total > 0) {
    submitBtn.style.animation = 'ee-pulse 2s ease-in-out infinite';
    submitBtn.style.boxShadow = '0 0 24px rgba(167,139,250,0.6)';
  }
}

function applyKatex(rootEl) {
  if (!rootEl) return;
  // 🔢 Plain text 数式 (π/2, √5, x^2 等) を先に $LaTeX$ に変換 (AI tutor と同じ品質)
  try { pretifyMath(rootEl); } catch (e) { console.warn('[katex] pretifyMath failed', e); }
  if (typeof window.renderMathInElement !== 'function') return;
  try {
    window.renderMathInElement(rootEl, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\[', right: '\\]', display: true },
        { left: '\\(', right: '\\)', display: false },
      ],
      throwOnError: false,
      errorColor: '#f87171',
      strict: 'ignore',
    });
  } catch (e) { console.warn('[katex] render failed', e); }
}

// 🔢 2026-05-13: Plain text 数式記号 → $LaTeX$ 変換 (AI tutor と共通仕様)
// 既存の exam_questions pool データ (主に AI 生成・plain text 数式) を紙の参考書品質に昇格。
// 既に $ を含む text node は触らない (二重変換防止)・code/pre/.katex 内は触らない (DOM 保護)
function pretifyMath(container) {
  if (!container || !window.NodeFilter) return;
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode: function(node) {
      let p = node.parentNode;
      while (p && p !== container) {
        const tag = (p.tagName || '').toLowerCase();
        if (tag === 'code' || tag === 'pre' || tag === 'kbd' || tag === 'samp') return NodeFilter.FILTER_REJECT;
        if (p.classList && (p.classList.contains('katex') || p.classList.contains('katex-display') || p.classList.contains('katex-html'))) return NodeFilter.FILTER_REJECT;
        p = p.parentNode;
      }
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  const nodes = [];
  let n;
  while ((n = walker.nextNode())) nodes.push(n);

  nodes.forEach(function(node) {
    const original = node.nodeValue;
    if (!original || original.length < 2) return;
    if (original.indexOf('$') >= 0 || original.indexOf('\\(') >= 0 || original.indexOf('\\[') >= 0) return;

    let t = original;
    // 1. 分数 (π/n, √n/m, π/√n)
    t = t.replace(/(π|√\d+)\s*\/\s*(\d+|π|√\d+)/g, function(_m, a, b) {
      const conv = function(s) { return s.replace(/π/g, '\\pi').replace(/√(\d+)/g, '\\sqrt{$1}'); };
      return '$\\dfrac{' + conv(a) + '}{' + conv(b) + '}$';
    });
    // 2. √n → $\sqrt{n}$
    t = t.replace(/√(\d+)/g, '$\\sqrt{$1}$');
    // 3. 単独 π → $\pi$
    t = t.replace(/π/g, '$\\pi$');
    // 4. 指数 x^2, t^{n}
    t = t.replace(/([a-zA-Z0-9\)])\^(\{[^{}]+\}|-?\d+|[a-zA-Z])/g, function(_m, base, exp) {
      const e = exp.charAt(0) === '{' ? exp : '{' + exp + '}';
      return '$' + base + '^' + e + '$';
    });
    // 5. 不等号 / 同値
    t = t.replace(/≦/g, '$\\leqq$').replace(/≧/g, '$\\geqq$').replace(/≠/g, '$\\neq$')
         .replace(/⇔/g, '$\\iff$').replace(/⇒/g, '$\\Rightarrow$').replace(/⇐/g, '$\\Leftarrow$');
    // 6. ギリシャ文字
    t = t.replace(/α/g, '$\\alpha$').replace(/β/g, '$\\beta$').replace(/γ/g, '$\\gamma$')
         .replace(/θ/g, '$\\theta$').replace(/φ/g, '$\\phi$').replace(/ω/g, '$\\omega$')
         .replace(/Δ/g, '$\\Delta$').replace(/Σ/g, '$\\Sigma$');
    // 7. 数学記号
    t = t.replace(/±/g, '$\\pm$').replace(/×/g, '$\\times$').replace(/÷/g, '$\\div$')
         .replace(/∞/g, '$\\infty$').replace(/[≈≒]/g, '$\\approx$');
    // 連続 $$ を空白に
    t = t.replace(/\$\s*\$/g, ' ');

    if (t === original) return;

    const fragments = document.createDocumentFragment();
    const re = /\$[^$\n]+?\$/g;
    let lastIdx = 0;
    let match;
    while ((match = re.exec(t)) !== null) {
      if (match.index > lastIdx) {
        fragments.appendChild(document.createTextNode(t.substring(lastIdx, match.index)));
      }
      const mathSpan = document.createElement('span');
      mathSpan.textContent = match[0];
      fragments.appendChild(mathSpan);
      lastIdx = match.index + match[0].length;
    }
    if (lastIdx < t.length) {
      fragments.appendChild(document.createTextNode(t.substring(lastIdx)));
    }
    if (fragments.childNodes.length > 0) {
      node.parentNode.replaceChild(fragments, node);
    }
  });
}

// 数式を含むテキストの安全レンダリング: HTML escape → \(...\) のバックスラッシュは保持
function escapeTextWithMath(s) {
  if (s == null) return '';
  // HTML escape (XSS 防御)
  let out = String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/\n/g, '<br>');
  // 🎯 2026-05-21 塾長指示「下線部を実際の模試のように」:
  //    AI 出力 `<u>(1) ...</u>` が literal text として表示される問題を解消。
  //    HTML escape 後の `&lt;u&gt;` / `&lt;/u&gt;` のみを実タグに戻す (whitelist 方式・他タグは escape 維持で XSS 安全)。
  //    .exam-underline class で 模試風の太い underline + 番号 (N) を視覚強調。
  out = out
    .replace(/&lt;u&gt;/gi, '<u class="exam-underline">')
    .replace(/&lt;\/u&gt;/gi, '</u>')
    // 模試らしい強調: <em>/<strong> も AI が emit する可能性あり (XSS リスク無し)
    .replace(/&lt;em&gt;/gi, '<em>')
    .replace(/&lt;\/em&gt;/gi, '</em>')
    .replace(/&lt;strong&gt;/gi, '<strong>')
    .replace(/&lt;\/strong&gt;/gi, '</strong>');
  return out;
}

// 🀄 漢文の返り点 (一二三・上中下・甲乙丙・レ点) を視覚的にマーク (塾長指示 2026-05-18)
// 「不レ亦説乎」「不二亦説一乎」等の選択肢で、レ点・一二点が CJK 文字と同サイズで並ぶと判別困難。
// <span class="kaeriten"> で小さく右下配置。
//
// ⚠️ 過剰検出回避 (塾長フィードバック 2026-05-18 「天下」「適中」等の通常熟語まで誤マーク):
//   1. state.sectionKey === 'kanbun' 時のみ適用
//   2. テキストに ひらがな・カタカナ (レ 除く) が含まれていれば skip
//      → 「天下に五方の地有り」(書き下し) / 「天下には」(現代語訳) 等は不適用
//   3. 白文 passage は混在テキスト (白文 + 書き下し + 現代語訳) のため呼び出し側で除外
//      → 選択肢 (choices) と設問 (stem) のみに適用
function _maybeMarkKaeriten(html) {
  if (!html) return html;
  try {
    if (!state || state.sectionKey !== 'kanbun') return html;
  } catch (_) { return html; }
  const text = String(html);
  // 長文 skip (passage 等で誤検出回避): 選択肢は通常 30 字以下なので 60 字超えたら skip
  // 万一 passage 描画ルートに渡されても、長さで弾いて誤マーク防止
  if (text.length > 60) return html;
  // ひらがな or レ 以外のカタカナを含む = 書き下し/現代語訳 → skip
  // 純粋な classical Chinese choices は基本的に hiragana/katakana を含まない (レ点除く)
  const hasKana = /[ぁ-んァ-ヶ]/.test(text);
  if (hasKana) {
    // レ点のみ含む例外: テキスト全体がカタカナ非含 OR レ のみ → 適用継続
    const nonReKana = text.replace(/レ/g, '').match(/[ぁ-んァ-ヶ]/);
    if (nonReKana) return html;  // ひらがな or レ 以外のカタカナあり → skip
  }
  // 漢字熟語の誤検出回避: 「天下」「適中」「上下」等の通常2字熟語は kaeriten ではない
  // 既知の誤検出パターンを explicit に除外 (純漢文選択肢には影響しないリスト)
  const COMMON_COMPOUNDS = ['天下', '適中', '上下', '左右', '中央', '中心', '中国', '下記', '上記', '以下', '以上'];
  let result = text;
  // 一旦 marker 候補を全て探す → COMMON_COMPOUNDS と重複しないものだけ wrap
  result = result.replace(
    /([一-鿿])([一二三四上中下甲乙丙レ])(?=[一-鿿、。，,.\s<]|$)/g,
    (match, k1, marker) => {
      const compound = k1 + marker;
      if (COMMON_COMPOUNDS.includes(compound)) return match; // 通常熟語 → skip
      return `${k1}<span class="kaeriten">${marker}</span>`;
    }
  );
  return result;
}

// 🛟 緊急救済: AI が multiple_choice なのに choices: [] を返した場合、
// stem 内の ①②③④⑤⑥⑦⑧ を検出して自動的に選択肢へ昇格させる
// (下線部誤り選択問題で AI が「番号は問題文に既にある」と判断して空配列を返すケース)
function _autoExtractChoicesFromStem(q) {
  if (!q || q.type !== 'multiple_choice') return q;
  if (Array.isArray(q.choices) && q.choices.length > 0) return q;
  const text = (q.stem || '') + ' ' + (q.passage || '');
  const pattern = /[①②③④⑤⑥⑦⑧]/g;
  const found = text.match(pattern) || [];
  // 出現順を保つかつ重複排除
  const seen = new Set();
  const matches = [];
  for (const m of found) {
    if (!seen.has(m)) {
      seen.add(m);
      matches.push(m);
    }
  }
  if (matches.length >= 2) {
    q.choices = matches;
    q._auto_extracted_choices = true;  // デバッグ用フラグ + UI ヒント表示用
    try { console.warn('[exam] choices auto-extracted from stem ①②...:', q.id, matches); } catch (e) {}
  }
  return q;
}

function renderQuestions() {
  const box = document.getElementById('questionBox');
  const instant = getUserInstantPref();
  // 🛟 各 question を auto-extract で前処理 (choices=[] の致命的 UI 詰まり救済)
  if (Array.isArray(state.questions)) {
    state.questions.forEach(_autoExtractChoicesFromStem);
  }
  let html = '';
  // 🎯 Pool-first 戦略の出典バッジ (2026-05-13)
  // 「pool から即取得」=¥0・速い / 「AI が新規生成」= 復習用個別最適化
  if (state.questionSource && state.questionSource !== 'unknown') {
    const badges = {
      pool: {
        text: '📚 問題プールから即取得',
        sub: '蓄積された厳選問題を使用 (¥0・高速)',
        bg: 'rgba(34,197,94,0.10)',
        border: 'rgba(34,197,94,0.35)',
        color: '#86efac',
      },
      ai_review: {
        text: '🤖 AI が復習用に個別生成',
        sub: '弱点に最適化した類題を新規作成',
        bg: 'rgba(167,139,250,0.10)',
        border: 'rgba(167,139,250,0.35)',
        color: '#c4b5fd',
      },
      ai_fresh: {
        text: '🤖 AI が新規生成',
        sub: 'pool に該当データ無しのため AI 生成',
        bg: 'rgba(99,102,241,0.10)',
        border: 'rgba(99,102,241,0.35)',
        color: '#a5b4fc',
      },
      fallback: {
        text: '⚠️ 代替問題',
        sub: 'pool/AI どちらも応答せず静的サンプルから抽出',
        bg: 'rgba(245,158,11,0.08)',
        border: 'rgba(245,158,11,0.30)',
        color: '#fbbf24',
      },
      fallback_no_live: {
        text: '⚠️ 代替問題 (AI 未接続)',
        sub: 'ログインまたは管理者キー設定で AI 生成が有効に',
        bg: 'rgba(220,38,38,0.08)',
        border: 'rgba(220,38,38,0.30)',
        color: '#fca5a5',
      },
    };
    const b = badges[state.questionSource];
    if (b) {
      // pool 出典時は「復習用に AI で類題生成」CTA を併設 (個別最適化が必要な生徒向け)
      const ctaHtml = (state.questionSource === 'pool')
        ? `<button type="button" id="switchToReviewBtn" style="margin-left:auto; padding:0.35rem 0.75rem; background:rgba(167,139,250,0.18); border:1px solid rgba(167,139,250,0.4); color:#c4b5fd; font-size:0.78rem; font-weight:700; border-radius:6px; cursor:pointer; min-height:32px;" title="弱点単元を指定して AI が個別最適化した類題を作成します">🎯 復習用に AI で類題作成</button>`
        : '';
      html += `<div class="ee-source-badge" style="margin-bottom:0.8rem; padding:0.6rem 0.9rem; background:${b.bg}; border:1px solid ${b.border}; border-radius:8px; display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
        <span style="font-size:0.92rem; font-weight:800; color:${b.color};">${b.text}</span>
        <span style="font-size:0.75rem; color:#94a3b8;">${escapeHtml(b.sub)}</span>
        ${ctaHtml}
      </div>`;
    }
  }
  // ⚠️ AI 接続失敗・問題不足時の明示警告 (偽プレースホルダ廃止に伴う)
  if (state.warning) {
    // 🔁 2026-05-16 塾長指示: 「再試行」ボタンを warning 内に併設
    //   従来 warning だけ表示で「次に何をすればいいか」が不明 → button で明示
    // 🚨 2026-05-21 fix: questions が空でなくても (AI 失敗 → demo fallback 時)、_retryable=true
    //   なら再試行ボタンを表示 (生徒が「タイムアウトしたから再試行を」と気付ける)
    const showRetry = (!state.questions || state.questions.length === 0) || state.retryable === true;
    const retryBtn = showRetry
      ? `<button type="button" id="retryLoadBtn" style="margin-top:0.75rem; padding:0.6rem 1.2rem; background:linear-gradient(135deg,#a78bfa 0%,#6366f1 100%); border:none; color:white; font-weight:800; border-radius:8px; cursor:pointer; font-size:0.95rem;">🔁 もう一度読み込む</button>`
      : '';
    html += `<div class="ee-warning-box">${escapeHtml(state.warning)}${retryBtn}</div>`;
  }
  if (state.passage) {
    // 漢文 passage は【白文】【書き下し文】【現代語訳】の混在テキストのため kaeriten 自動マーキングを適用しない
    // (「天下」「適中」等の通常熟語を誤マークする問題のため・塾長指示 2026-05-18)
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
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem; margin-bottom:0.4rem; flex-wrap:wrap;">
        <div class="ee-question-num">Q${idx + 1}</div>
        <button type="button" class="ee-flag-btn" data-qid="${q.id}" title="この問題に違和感があれば塾長に報告" style="padding:0.3rem 0.7rem; background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.30); border-radius:6px; color:#fbbf24; font-size:0.75rem; font-weight:700; cursor:pointer; min-height:32px;">🚩 違和感あり</button>
      </div>
      <div class="ee-question-stem">${_maybeMarkKaeriten(escapeTextWithMath(q.stem || ''))}</div>`;
    if (q.type === 'multiple_choice' && Array.isArray(q.choices) && q.choices.length) {
      // 🛟 auto-extract された下線部番号選択肢の場合はヒント表示
      if (q._auto_extracted_choices) {
        html += `<div class="ee-choices-hint">💡 下線部の該当番号を選択してください</div>`;
      }
      // 🎯 ボタン式 4択 (radio は隠して label をボタンに)
      html += `<div class="ee-choices ee-choices-btn" role="radiogroup" aria-label="Q${idx + 1} の選択肢">`;
      q.choices.forEach((c, ci) => {
        html += `<button type="button" class="ee-choice-btn" data-qid="${q.id}" data-choice="${ci}" role="radio" aria-checked="false">
          <span class="ee-choice-letter">${String.fromCharCode(65 + ci)}</span>
          <span class="ee-choice-text">${_maybeMarkKaeriten(escapeTextWithMath(c))}</span>
          <span class="ee-choice-icon"></span>
        </button>`;
      });
      html += '</div>';
      // 即時採点モード時の解説エリア (デフォルト非表示)
      html += `<div class="ee-instant-explain" data-qid="${q.id}" style="display:none;"></div>`;
    } else if (q.type === 'short_answer') {
      html += `<input type="text" class="ee-text-input" name="${q.id}" placeholder="回答を入力">`;
    } else {
      // 🆕 2026-05-13: 記述式 (essay/speaking/translation) に写真アップロード機能追加
      // 紙に書いた答えを撮影 → AI が OCR + 採点 (textarea/photo どちらでも OK)
      html += `<div class="ee-answer-tabs" data-qid="${q.id}" style="display:flex; gap:0.4rem; margin-bottom:0.5rem;">
        <button type="button" class="ee-tab-btn ee-tab-active" data-mode="text" data-qid="${q.id}" style="padding:0.45rem 0.9rem; border-radius:8px; background:rgba(167,139,250,0.20); border:1px solid rgba(167,139,250,0.5); color:#fff; font-weight:700; font-size:0.85rem; cursor:pointer;">📝 テキストで入力</button>
        <button type="button" class="ee-tab-btn" data-mode="photo" data-qid="${q.id}" style="padding:0.45rem 0.9rem; border-radius:8px; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.15); color:#a1a1aa; font-weight:700; font-size:0.85rem; cursor:pointer;">📷 写真で提出</button>
      </div>
      <div class="ee-answer-text" data-qid="${q.id}">
        <textarea class="ee-textarea" name="${q.id}" rows="6" placeholder="${q.type === 'speaking' ? '口頭で話す内容を文字に書き起こしてください' : 'エッセイをここに書いてください'}"></textarea>
      </div>
      <div class="ee-answer-photo" data-qid="${q.id}" style="display:none;">
        <!-- 🎯 2026-05-13 教育アプリ UX: 撮影ガイドを 開く前 / 後で表示 -->
        <div style="padding:0.7rem 0.9rem; background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.30); border-radius:10px; margin-bottom:0.6rem; font-size:0.85rem; line-height:1.6; color:#93c5fd;">
          <strong style="color:#3b82f6;">📸 きれいに撮るコツ</strong><br>
          ① ☀️ <strong>明るい場所</strong>で撮影 (蛍光灯の真下 or 窓際)<br>
          ② 📱 答案を<strong>正面から</strong> (斜めは避ける・影が入らないように)<br>
          ③ 🔍 文字が<strong>くっきり読める</strong>大きさで (ぼやけは AI 読み取り失敗の原因)<br>
          ④ 📄 答案全体が<strong>1 枚に収まる</strong>ように (複数枚は最後の 1 枚のみ採点)
        </div>
        <label class="ee-photo-drop" for="ee-photo-${q.id}" style="display:block; border:2px dashed rgba(167,139,250,0.4); border-radius:12px; padding:1.5rem 1rem; text-align:center; cursor:pointer; background:rgba(99,102,241,0.04); transition: all 0.2s;">
          <div style="font-size:2.2rem; margin-bottom:0.4rem;">📷</div>
          <div style="color:#a78bfa; font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">タップして紙の答案を撮影</div>
          <div style="color:#94a3b8; font-size:0.78rem; line-height:1.5;">JPG / PNG / HEIC 対応・最大 10MB<br>AI が OCR + 採点します (テキスト入力と同じ結果)</div>
          <input type="file" id="ee-photo-${q.id}" data-qid="${q.id}" accept="image/*" capture="environment" style="display:none;">
        </label>
        <div class="ee-photo-preview" data-qid="${q.id}" style="display:none; margin-top:0.6rem;">
          <img class="ee-photo-img" data-qid="${q.id}" alt="アップロードした答案" style="max-width:100%; max-height:300px; border-radius:8px; border:1px solid rgba(255,255,255,0.15);">
          <div style="display:flex; gap:0.5rem; align-items:center; margin-top:0.4rem; flex-wrap:wrap;">
            <span class="ee-photo-status" data-qid="${q.id}" style="font-size:0.82rem; color:#86efac;">✅ 撮影完了 (採点時に AI が読み取ります)</span>
            <button type="button" class="ee-photo-remove" data-qid="${q.id}" style="padding:0.3rem 0.7rem; background:rgba(248,113,113,0.15); border:1px solid rgba(248,113,113,0.4); border-radius:6px; color:#fca5a5; font-size:0.78rem; cursor:pointer;">🗑 削除</button>
          </div>
        </div>
      </div>`;
    }
    html += '</div>';
  });
  box.innerHTML = html;

  // 🔁 「もう一度読み込む」ボタン (warning + questions 空時のみ表示)
  const retryBtn = box.querySelector('#retryLoadBtn');
  if (retryBtn) {
    retryBtn.addEventListener('click', () => {
      retryBtn.disabled = true;
      retryBtn.textContent = '⏳ 再取得中...';
      try {
        // 現在の section を再呼び出し
        const examObj = state.examId ? EXAMS[state.examId] : null;
        const sections = (typeof getSections === 'function')
          ? getSections(state.examId, state.eikenGrade)
          : (examObj?.sectionsByGrade?.[state.eikenGrade] || examObj?.sections || []);
        const sec = sections.find(s => s.key === state.sectionKey) || sections[0];
        if (examObj && sec && typeof generateAndShowQuestions === 'function') {
          generateAndShowQuestions(examObj, sec, !!state.isFullMock);
        } else {
          retryBtn.disabled = false;
          retryBtn.textContent = '🔁 もう一度読み込む';
        }
      } catch (e) {
        console.warn('[exam] retry failed', e);
        retryBtn.disabled = false;
        retryBtn.textContent = '🔁 もう一度読み込む';
      }
    });
  }

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

  // 🚩 2026-05-13 塾長指示「選択肢が間違っている問題もある」: 違和感報告ボタン bind
  box.querySelectorAll('.ee-flag-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const qid = btn.dataset.qid;
      const q = state.questions.find(x => x.id === qid);
      if (!q) return;
      // 違和感の種類を選んでもらう
      const reason = prompt(
        '🚩 この問題のどこに違和感がありますか?\n\n' +
        '1: 問題文と選択肢が噛み合わない\n' +
        '2: 正解とされる選択肢が実は間違いに見える\n' +
        '3: 日本語訳・解説がおかしい\n' +
        '4: 誤字・脱字・表記ミス\n' +
        '5: その他 (自由記述)\n\n' +
        '番号 (1-5) または詳細を入力してください:',
        ''
      );
      if (reason === null || reason.trim() === '') return;
      // 即座に UI で「報告受付」を示す + 塾長への通知 endpoint に POST
      btn.disabled = true;
      btn.textContent = '⏳ 報告中...';
      btn.style.background = 'rgba(167,139,250,0.20)';
      btn.style.borderColor = 'rgba(167,139,250,0.50)';
      btn.style.color = '#a78bfa';
      try {
        await _reportQuestionIssue(q, reason);
        btn.textContent = '✅ 塾長に報告済 (ありがとうございます!)';
        btn.style.background = 'rgba(16,185,129,0.15)';
        btn.style.borderColor = 'rgba(16,185,129,0.45)';
        btn.style.color = '#86efac';
      } catch (e) {
        console.warn('report failed:', e);
        btn.disabled = false;
        btn.textContent = '🚩 違和感あり';
        btn.style.background = 'rgba(245,158,11,0.10)';
        btn.style.borderColor = 'rgba(245,158,11,0.30)';
        btn.style.color = '#fbbf24';
        alert('報告に失敗しました。直接塾長 LINE までご連絡ください: ' + (e.message || e));
      }
    });
  });

  // 🎯 2026-05-13 pool-first: 「復習用 AI 類題生成」CTA
  // pool 出典時のみ表示。クリックで弱点単元を聞いて AI 生成にスイッチ
  const switchBtn = document.getElementById('switchToReviewBtn');
  if (switchBtn) {
    switchBtn.addEventListener('click', async () => {
      const topicHint = prompt(
        '🎯 復習したい弱点単元を入力してください:\n\n' +
        '例: 関係代名詞 / 仮定法 / 不定詞 / 受動態 / 比較\n' +
        '英作文型なら: 自分の意見 / 賛否両論 / 図表描写\n\n' +
        '※ 単元を指定すると AI がその単元に特化した類題を生成します。\n' +
        '※ 単元なしでただ問題が欲しい場合は「キャンセル」を押し、pool の問題を続けてください (¥0)',
        ''
      );
      if (topicHint === null) return; // cancel
      const cleanedTopic = (topicHint || '').trim();
      if (!cleanedTopic) {
        // 🛡 H3 対策: 空欄で AI 呼ぶと「pool 充分なのに無料路線を捨てる」ことになるので拒否
        alert('🙅 単元の指定が無いと AI 生成のコストメリットが無いため、pool の問題を続けて使います。\n弱点単元 (例: 関係代名詞) を入力してから再度押してください。');
        return;
      }
      // state にセット + URL を更新 (リロード対策・共有 URL 化)
      state.currentTopic = cleanedTopic;
      try {
        const url = new URL(window.location.href);
        url.searchParams.set('review', '1');
        if (state.currentTopic) url.searchParams.set('topic', state.currentTopic);
        else url.searchParams.delete('topic');
        window.history.replaceState({}, '', url);
      } catch (e) { /* silent */ }
      switchBtn.disabled = true;
      switchBtn.textContent = '⏳ AI で類題生成中...';
      // 同じ exam/section で再生成
      const exam = EXAMS[state.examId];
      const section = (exam.sections || []).find(s => s.key === state.sectionKey) || (exam.sections || [])[0];
      if (exam && section) {
        try {
          await generateAndShowQuestions(exam, section, false);
        } catch (e) {
          console.error('AI 類題生成失敗:', e);
          alert('AI 類題生成に失敗しました。少し時間をおいて再度お試しください。');
          switchBtn.disabled = false;
          switchBtn.textContent = '🎯 復習用に AI で類題作成';
        }
      }
    });
  }

  // 🎯 2026-05-13 教育アプリ UX: 進捗バー初期化 + 更新 hook
  _initProgressBar();
  // 全 input/textarea/button change で progress 更新
  box.querySelectorAll('input, textarea, button').forEach(el => {
    el.addEventListener('change', _updateProgressBar);
    if (el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && el.type === 'text')) {
      el.addEventListener('input', _updateProgressBar);
    }
    if (el.classList && el.classList.contains('ee-choice-btn')) {
      el.addEventListener('click', _updateProgressBar);
    }
  });

  // 🆕 2026-05-13: 写真アップロード handlers (記述式 essay/translation/speaking 用)
  if (!state.userAnswerPhotos) state.userAnswerPhotos = {};

  // タブ切替 (テキスト ⇄ 写真)
  box.querySelectorAll('.ee-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const qid = btn.dataset.qid;
      const mode = btn.dataset.mode;
      // タブのアクティブ状態切替
      box.querySelectorAll(`.ee-tab-btn[data-qid="${qid}"]`).forEach(b => {
        const isActive = b.dataset.mode === mode;
        b.classList.toggle('ee-tab-active', isActive);
        b.style.background = isActive ? 'rgba(167,139,250,0.20)' : 'rgba(0,0,0,0.3)';
        b.style.borderColor = isActive ? 'rgba(167,139,250,0.5)' : 'rgba(255,255,255,0.15)';
        b.style.color = isActive ? '#fff' : '#a1a1aa';
      });
      // 表示切替
      const textPanel = box.querySelector(`.ee-answer-text[data-qid="${qid}"]`);
      const photoPanel = box.querySelector(`.ee-answer-photo[data-qid="${qid}"]`);
      if (textPanel) textPanel.style.display = mode === 'text' ? '' : 'none';
      if (photoPanel) photoPanel.style.display = mode === 'photo' ? '' : 'none';
    });
  });

  // 写真 file input handler
  box.querySelectorAll('input[type="file"][id^="ee-photo-"]').forEach(input => {
    input.addEventListener('change', async (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      const qid = input.dataset.qid;
      // サイズ check (10 MB 上限)
      if (file.size > 10 * 1024 * 1024) {
        alert('画像が大きすぎます (最大 10MB)。別の写真でお試しください。');
        return;
      }
      // base64 化
      try {
        const dataUrl = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = () => reject(reader.error);
          reader.readAsDataURL(file);
        });
        state.userAnswerPhotos[qid] = {
          dataUrl: dataUrl,
          mimeType: file.type || 'image/jpeg',
          fileName: file.name || 'answer.jpg',
          sizeKb: Math.round(file.size / 1024),
        };
        // preview 表示
        const preview = box.querySelector(`.ee-photo-preview[data-qid="${qid}"]`);
        const img = box.querySelector(`.ee-photo-img[data-qid="${qid}"]`);
        if (img) img.src = dataUrl;
        if (preview) preview.style.display = '';
        // userAnswers に「写真で提出」マーカーを入れる (空欄判定回避)
        state.userAnswers[qid] = '[📷 写真で提出済み]';
      } catch (err) {
        console.error('photo read failed:', err);
        alert('写真の読み込みに失敗しました: ' + (err.message || err));
      }
    });
  });

  // 写真 削除
  box.querySelectorAll('.ee-photo-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      const qid = btn.dataset.qid;
      delete state.userAnswerPhotos[qid];
      const input = box.querySelector(`input[type="file"][id="ee-photo-${qid}"]`);
      if (input) input.value = '';
      const preview = box.querySelector(`.ee-photo-preview[data-qid="${qid}"]`);
      if (preview) preview.style.display = 'none';
      if (state.userAnswers[qid] === '[📷 写真で提出済み]') {
        delete state.userAnswers[qid];
      }
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
  if (!exam) {
    alert('試験データが見つかりません (state.examId=' + state.examId + ')。最初からやり直してください。');
    document.getElementById('submitAnswersBtn').disabled = false;
    document.getElementById('submitAnswersBtn').textContent = '📤 回答を提出して採点';
    return;
  }
  const sections = state.currentSections || exam.sections || [];
  // 🚨 2026-05-13 致命傷 fix: section が undefined になる経路を完全防御
  // 原因: state.sectionKey が currentSections のどの key とも一致しない
  // (例: 大学入試/理系で sectionKey が古い形式・archive 復元時の不整合等)
  // 対策: find で見つからない場合は fallback object を構築して採点続行
  let section = sections.find(s => s.key === state.sectionKey);
  if (!section) {
    console.warn('[submitAnswers] section not found in currentSections - using fallback', {
      examId: state.examId, sectionKey: state.sectionKey, sectionsCount: sections.length,
      availableKeys: sections.map(s => s.key),
    });
    // sections の先頭 or 完全 fallback object
    section = sections[0] || {
      key: state.sectionKey || 'unknown',
      name: state.sectionKey || '採点',
      icon: '📝',
      timeMin: 30,
      qCount: (state.questions || []).length || 5,
      scoreMax: 30,
      desc: '',
    };
  }
  // 🎯 2026-05-13 塾長指示「最初に解答を用意している問題なので記述以外は AI 採点不要」:
  // 採点方式を ハイブリッド化:
  //   - 全問が multiple_choice/short_answer のみ → ローカル即時採点 (1 秒・AI コスト 0)
  //   - 記述問題 (essay/translation/speaking/open) を含む → AI 採点
  // 大学入試・英検等で multiple_choice 中心の問題は瞬時に結果が出る
  const hasOpenAnswer = (state.questions || []).some(q => {
    const t = (q && q.type) || 'multiple_choice';
    return t !== 'multiple_choice' && t !== 'short_answer';
  });
  // submit ボタン表示更新 (採点中の心理的ケア)
  const submitBtn = document.getElementById('submitAnswersBtn');
  if (submitBtn) {
    submitBtn.textContent = hasOpenAnswer
      ? '⏳ AI が記述採点中... (10-30 秒)'
      : '⚡ 即採点中...';
  }
  let result;
  try {
    if (hasOpenAnswer && isLiveMode()) {
      // 記述問題あり: AI 採点 (Claude による多視点採点)
      result = await scoreWithClaude(exam, section);
    } else {
      // 全問 mc/short のみ OR Live mode 無効: ローカル即時採点
      result = scoreLocally(exam, section);
    }
  } catch (e) {
    console.error(e);
    // 🎯 2026-05-13 教育アプリ UX: エラー時に塾長 LINE 連絡 CTA + 応援メッセージ
    // 単なる alert ではなく、生徒が「諦めずに次に進める」UX
    const errMsg = (e && (e.message || String(e))) || '不明なエラー';
    // フレンドリーな error message を box 内に表示
    const box = document.getElementById('questionBox');
    if (box) {
      const errBanner = document.createElement('div');
      errBanner.style.cssText = 'margin: 1rem 0; padding: 1.2rem; background: rgba(245,158,11,0.10); border: 1px solid rgba(245,158,11,0.40); border-radius: 12px; color: #fde68a;';
      errBanner.innerHTML = `
        <div style="font-size:1.05rem; font-weight:800; color:#fbbf24; margin-bottom:0.5rem;">⚠️ 採点処理が止まってしまいました</div>
        <p style="margin:0.5rem 0; font-size:0.88rem; line-height:1.6;">
          一時的なエラーのようです。あなたの回答自体は問題なく入力できています。<br>
          以下のいずれかで再開してください:
        </p>
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin:0.8rem 0;">
          <button id="ee-retry-submit" style="padding:0.7rem 1.1rem; background:linear-gradient(135deg,#6366f1,#8b5cf6); border:0; border-radius:8px; color:#fff; font-weight:700; cursor:pointer; min-height:44px;">🔄 もう一度採点する</button>
          <button id="ee-back-top" style="padding:0.7rem 1.1rem; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.20); border-radius:8px; color:#a1a1aa; font-weight:700; cursor:pointer; min-height:44px;">← 一覧に戻る</button>
        </div>
        <details style="margin-top:0.7rem; font-size:0.82rem; color:#a1a1aa;">
          <summary style="cursor:pointer; color:#fbbf24;">⚙️ エラー詳細 (塾長に共有用)</summary>
          <code style="display:block; margin-top:0.4rem; padding:0.5rem; background:rgba(0,0,0,0.3); border-radius:6px; font-size:0.78rem; word-break:break-all;">${escapeHtml(errMsg)}</code>
          <div style="margin-top:0.5rem;">💬 解決しない場合は <strong>塾長 LINE</strong> にこの詳細を貼り付けてご連絡ください。</div>
        </details>
        <p style="margin:0.8rem 0 0; font-size:0.85rem; color:#86efac; text-align:center;">
          💪 採点が動かなくても、あなたの今日の頑張りは記録に残っています。次の問題に進みましょう!
        </p>
      `;
      box.prepend(errBanner);
      // 「もう一度」ボタン
      const retryBtn = document.getElementById('ee-retry-submit');
      if (retryBtn) retryBtn.addEventListener('click', () => {
        errBanner.remove();
        document.getElementById('submitAnswersBtn').click();
      });
      const backBtn = document.getElementById('ee-back-top');
      if (backBtn) backBtn.addEventListener('click', () => {
        document.getElementById('examRunnerSection').style.display = 'none';
        document.getElementById('examPickSection').style.display = '';
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    } else {
      // box が存在しないなら fallback alert
      alert('採点中にエラーが発生しました: ' + errMsg + '\n\n塾長 LINE までご連絡ください。');
    }
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
      // セッション統計: 採点直後に attempt push (app.js の sessionState を共有)
      try {
        if (typeof window._pushSessionAttempt === 'function') {
          window._pushSessionAttempt(q.id, isCorrect);
        }
      } catch (e) { /* silent */ }
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
    open_answers: perQuestion.filter(q => q.modelAnswer !== undefined).map(q => {
      // 🆕 写真で提出されている場合は user_answer に photo マーカー + 画像参照を明示
      const hasPhoto = state.userAnswerPhotos && state.userAnswerPhotos[q.qid];
      return {
        stem: q.stem,
        user_answer: hasPhoto ? `[📷 写真で提出 - 画像内容を OCR して採点してください]` : q.userAnswer,
        model_answer: q.modelAnswer,
        is_photo_answer: !!hasPhoto,
      };
    }),
    target_level: state.currentLevel || 'B1',
  };
  let userMsg = `以下の受験データを採点してください:
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

  // 🆕 2026-05-13: 写真採点 - userAnswerPhotos があれば画像を Claude vision に渡す
  // photo answer のある質問: Claude が OCR + 採点する
  let photoImages = null;
  if (state.userAnswerPhotos && Object.keys(state.userAnswerPhotos).length > 0) {
    photoImages = [];
    state.questions.forEach((q, idx) => {
      const p = state.userAnswerPhotos[q.id];
      if (p && p.dataUrl) {
        // dataUrl から base64 部分を抽出
        const m = p.dataUrl.match(/^data:(image\/[a-z+]+);base64,(.+)$/);
        if (m) {
          photoImages.push({
            media_type: m[1],
            data: m[2],
            label: `Q${idx + 1} (${q.stem ? q.stem.slice(0, 40) + '...' : ''}) の答案`,
          });
        }
      }
    });
    if (photoImages.length > 0) {
      // user prompt の最後に「写真の答案も含めて採点」指示を追記
      const photoInstruction = `\n\n【🆕 写真で提出された答案 (${photoImages.length} 件)】\n上の画像 ${photoImages.length} 枚は生徒が紙に書いた答案を撮影したものです。\n各画像の冒頭ラベル (例: \"Q1 ... の答案\") で対応問題を確認し、画像内の手書き答案を OCR で読み取った上で、テキスト入力と同じ基準で採点してください。\n- 手書き文字の読み取り誤差は考慮 (致命的誤読でない限り減点しない)\n- 解答ロジック・キーワード・構成・文法を重視\n- feedback_per_open_answer の comment 冒頭に「📷 (写真から判読)」と明示`;
      userMsg = userMsg + photoInstruction;
    } else {
      photoImages = null;
    }
  }

  let aiResult;
  try {
    aiResult = await callClaudeJson({ system, user: userMsg, model: MODEL_HEAVY, maxTokens: 3500, images: photoImages });
  } catch (e) {
    console.warn('[score] Heavy model failed, fallback:', e);
    aiResult = await callClaudeJson({ system, user: userMsg, model: MODEL_DEFAULT, maxTokens: 3500, images: photoImages });
  }

  return {
    sectionScore: aiResult.section_score ?? Math.round((mcScore / Math.max(1, mcTotal)) * sectionScoreMax),
    overallScore: aiResult.overall_score ?? Math.round((mcScore / Math.max(1, mcTotal)) * (exam.scoreMax || sectionScoreMax || 30)),
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
      // セッション統計: 採点直後に attempt push (app.js の sessionState を共有)
      try {
        if (typeof window._pushSessionAttempt === 'function') {
          window._pushSessionAttempt(q.id, isCorrect);
        }
      } catch (e) { /* silent */ }
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
  const examScoreMaxLocal = exam.scoreMax || sectionScoreMax || 30;
  const ratio = mcTotal > 0 ? mcScore / mcTotal : 0;
  const sectionScore = Math.round(ratio * sectionScoreMax * 10) / 10;
  const overallScore = Math.round(ratio * examScoreMaxLocal * 10) / 10;
  const cefr = scoreToCefr(exam.id, overallScore);

  // 🎯 2026-05-13 塾長指示「mc は AI 採点不要」: ローカル採点でも質の高い feedback を生成
  // 正答率に応じた具体的な strengths/weaknesses/studyPlan を出す
  const correctCount = mcScore;
  const wrongCount = mcTotal - mcScore;
  const accuracy = mcTotal > 0 ? Math.round((mcScore / mcTotal) * 100) : 0;

  const strengths = [];
  const weaknesses = [];
  if (correctCount >= mcTotal * 0.8 && mcTotal > 0) {
    strengths.push(`正答率 ${accuracy}% — このレベルの問題は十分対応できています`);
    strengths.push('ケアレスミス防止と時間配分の最適化が次のステップ');
  } else if (correctCount >= mcTotal * 0.5 && mcTotal > 0) {
    strengths.push(`正答率 ${accuracy}% — 基礎力は身についています`);
    weaknesses.push(`誤答した ${wrongCount} 問について、解説をしっかり読み込んで類題を解きましょう`);
  } else if (mcTotal > 0) {
    weaknesses.push(`正答率 ${accuracy}% — まずは「解説」を熟読して類題演習が必要`);
    weaknesses.push('1 問ずつ「なぜその答えになるのか」を声に出して説明する練習が効果的');
  } else {
    strengths.push('全問記述式のため、ローカル即時採点には対応していません');
  }

  // 誤答した問題の単元を集計 (subject ベース)
  const wrongSubjects = {};
  perQuestion.forEach(pq => {
    if (pq.isCorrect === false) {
      const stem = (pq.stem || '').slice(0, 30);
      wrongSubjects[stem] = (wrongSubjects[stem] || 0) + 1;
    }
  });

  // 学習プラン
  let studyPlan;
  if (correctCount >= mcTotal * 0.8 && mcTotal > 0) {
    studyPlan = `🏆 高得点おめでとうございます!次は ${exam.name} の更に上のレベルや、別の大問形式に挑戦して総合力を伸ばしましょう。\n\n` +
      `毎日の推奨:\n` +
      `- ${section.name} を週 3 回 (15-20 分) で時間配分を最適化\n` +
      `- 他の大問 (長文・文法・英作文等) を週 2 回 ローテーション\n` +
      `- 誤答した ${wrongCount} 問の解説を翌日再確認 (記憶定着)`;
  } else if (correctCount >= mcTotal * 0.5 && mcTotal > 0) {
    studyPlan = `👍 良いペース!誤答した ${wrongCount} 問の「解説」を必ず読み、自分の言葉で言い換えてノートに書いてください。\n\n` +
      `毎日の推奨:\n` +
      `- ${section.name} の類題を毎日 5-10 問 (15 分)\n` +
      `- 誤答パターンの分析 (なぜ間違えたかをノート化)\n` +
      `- 1 週間後に同じ問題を再挑戦して定着確認`;
  } else if (mcTotal > 0) {
    studyPlan = `💪 まだ伸び代があります。焦らず基礎から積み上げましょう。\n\n` +
      `毎日の推奨:\n` +
      `- 解説 を熟読 → 用語・文法事項をノート化\n` +
      `- ${section.name} の簡単な類題から段階的に\n` +
      `- 1 週間後に同じ問題を再挑戦 (正答率が上がれば定着の証拠)\n` +
      `- 困ったら塾長 LINE で個別質問してください`;
  } else {
    studyPlan = '記述式問題は AI 採点が必要なので、改めて AI 接続が安定した時に再提出してください。';
  }

  return {
    sectionScore, overallScore, cefr,
    strengths,
    weaknesses,
    feedback: [],
    studyPlan,
    perQuestion,
    mcScore, mcTotal,
    scoringMethod: 'local-instant', // 採点方式を明示 (UI で「⚡ 即採点」を表示する用)
  };
}

// ==========================================================================
// 結果表示
// ==========================================================================
function showResult(exam, section, result) {
  document.getElementById('examRunnerSection').style.display = 'none';
  document.getElementById('examResultSection').style.display = '';

  // 🚨 2026-05-13 致命傷防御: section / exam が undefined でも crash しない
  if (!section) {
    section = { key: 'unknown', name: '採点', icon: '📝', scoreMax: 30, qCount: (state.questions || []).length || 5, timeMin: 30, desc: '' };
  }
  if (!exam) {
    exam = { name: state.examId || '試験', flag: '📝', color: '#a78bfa', scoreMax: section.scoreMax || 30, scoreUnit: '点', sections: [section] };
  }

  // ヒーロー
  const targetScore = parseFloat(document.getElementById('targetScore')?.value || '0');
  const examScoreMax = exam.scoreMax || section.scoreMax || 30;
  const sectionScoreMaxSafe = section.scoreMax || 30;
  const percent = Math.round((result.overallScore / examScoreMax) * 100);

  // 🎯 2026-05-13 教育アプリ UX: 一言評価 + 大アイコン (Duolingo 流)
  // ユーザーが結果画面を見た瞬間に「自分の状態」が分かる
  let bigIcon, summaryText, summaryColor, summaryBg;
  if (percent >= 80) {
    bigIcon = '🏆';
    summaryText = 'お見事!合格圏内の高得点です';
    summaryColor = '#10b981';
    summaryBg = 'rgba(16,185,129,0.10)';
  } else if (percent >= 60) {
    bigIcon = '👍';
    summaryText = '良いペース!あと少しで合格圏内';
    summaryColor = '#3b82f6';
    summaryBg = 'rgba(59,130,246,0.10)';
  } else if (percent >= 40) {
    bigIcon = '💪';
    summaryText = '基礎は固まっています。重点復習で伸びます';
    summaryColor = '#f59e0b';
    summaryBg = 'rgba(245,158,11,0.10)';
  } else {
    bigIcon = '🌱';
    summaryText = '基礎から積み上げよう。1問ずつ着実に';
    summaryColor = '#a78bfa';
    summaryBg = 'rgba(167,139,250,0.10)';
  }

  document.getElementById('resultScoreHero').innerHTML = `
    <div class="result-hero-inner" style="border-color:${exam.color}">
      <!-- 🎯 大アイコン + 一言評価 (一目で「できた/できなかった」が分かる) -->
      <div style="text-align:center; padding:1.2rem 1rem; margin-bottom:1rem; background:${summaryBg}; border-radius:14px; border:1px solid ${summaryColor}55;">
        <div style="font-size:3.5rem; line-height:1; margin-bottom:0.4rem;">${bigIcon}</div>
        <div style="font-size:1.05rem; color:${summaryColor}; font-weight:800; line-height:1.4;">${summaryText}</div>
      </div>

      <div class="result-hero-flag">${exam.flag}</div>
      <div class="result-hero-exam">${exam.name}</div>
      <div class="result-hero-score" style="color:${exam.color}">
        <span class="result-hero-num">${result.overallScore}</span>
        <span class="result-hero-unit">/ ${examScoreMax}${exam.scoreUnit || '点'}</span>
      </div>
      ${(['eiken','toefl','toeic','ielts'].indexOf(state.examId) >= 0) ? `<div class="result-hero-cefr">CEFR <strong>${result.cefr}</strong> 相当</div>` : ''}
      <div class="result-hero-section">${section.icon || '📝'} ${section.name || ''}: ${result.sectionScore} / ${sectionScoreMaxSafe}</div>
      ${targetScore > 0 ? `<div class="result-hero-target">🎯 目標 ${targetScore} まで <strong>${(targetScore - result.overallScore).toFixed(1)}</strong></div>` : ''}
      <div class="result-hero-bar"><div class="result-hero-bar-fill" style="width:${percent}%;background:${exam.color}"></div></div>
    </div>`;

  // 4試験換算 (大学入試・理系科目では非表示・2026-05-13 塾長指示)
  // 英検/TOEFL/TOEIC/IELTS は 4 試験対策の試験 (eiken/toefl/toeic/ielts) でのみ意味がある。
  // 大学入試 (daigaku) や 理系 (rikei) では CEFR 換算は文脈不一致なので hide。
  const converterEl = document.getElementById('resultConverter');
  const titleEl = document.getElementById('examResultTitle');
  const isEnglishExam = ['eiken', 'toefl', 'toeic', 'ielts'].indexOf(state.examId) >= 0;
  if (isEnglishExam) {
    if (converterEl) converterEl.style.display = '';
    if (titleEl) titleEl.textContent = '🎯 採点結果 + 4試験スコア換算';
    const allScores = cefrToAllScores(result.cefr);
    document.getElementById('resultConverterGrid').innerHTML = `
      <div class="conv-card"><div class="conv-flag">🇺🇸</div><div class="conv-name">TOEFL iBT</div><div class="conv-score">${allScores.toefl}</div></div>
      <div class="conv-card"><div class="conv-flag">💼</div><div class="conv-name">TOEIC L&R</div><div class="conv-score">${allScores.toeic}</div></div>
      <div class="conv-card"><div class="conv-flag">🇬🇧</div><div class="conv-name">IELTS</div><div class="conv-score">${allScores.ielts}</div></div>
      <div class="conv-card"><div class="conv-flag">🇯🇵</div><div class="conv-name">英検</div><div class="conv-score">${allScores.eiken}</div></div>
    `;
  } else {
    // 大学入試・理系では converter 全体を非表示・タイトルも適切に
    if (converterEl) converterEl.style.display = 'none';
    if (titleEl) {
      // 🎯 2026-05-13: 採点方式 (即採点 or AI) をタイトルに併記
      const methodBadge = result.scoringMethod === 'local-instant' ? ' <span style="font-size:0.6em;background:rgba(16,185,129,0.2);color:#86efac;padding:0.15rem 0.5rem;border-radius:6px;margin-left:0.5rem;vertical-align:middle;">⚡ 即採点</span>' : ' <span style="font-size:0.6em;background:rgba(167,139,250,0.2);color:#a78bfa;padding:0.15rem 0.5rem;border-radius:6px;margin-left:0.5rem;vertical-align:middle;">🤖 AI 採点</span>';
      titleEl.innerHTML = '🎯 採点結果' + methodBadge;
    }
  }

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
  // 🔢 2026-05-13: 結果フィードバックの数式を KaTeX 組版 (大学入試 r_long/解説/理系問題対応)
  try { applyKatex(document.getElementById('resultFeedback')); } catch (_) {}

  // 学習プラン
  document.getElementById('learningPlanBox').innerHTML = `<div class="plan-text">${escapeHtml(result.studyPlan).replace(/\n/g,'<br>')}</div>`;
  // 学習プランにも数式が含まれる可能性 (rikei 理系等)
  try { applyKatex(document.getElementById('learningPlanBox')); } catch (_) {}

  // ボタン
  document.getElementById('retryBtn').onclick = () => {
    const sections = state.currentSections || exam.sections;
    const sec = sections.find(s => s.key === state.sectionKey);
    startSection(sec);
  };
  document.getElementById('newExamBtn').onclick = () => {
    document.getElementById('examResultSection').style.display = 'none';
    document.getElementById('examDetailSection').style.display = '';
    // 🎯 pool-first 戦略: 別 part 選択画面に戻る時も復習モードをクリア
    //    (これがないと同じ exam 内で「次のセクション」を選んだ際に永続 AI モードが続く)
    state.currentTopic = null;
    state.isReviewMode = false;
    try {
      const url = new URL(window.location.href);
      let dirty = false;
      if (url.searchParams.has('review')) { url.searchParams.delete('review'); dirty = true; }
      if (url.searchParams.has('topic')) { url.searchParams.delete('topic'); dirty = true; }
      if (dirty) window.history.replaceState({}, '', url);
    } catch (e) { /* silent */ }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  document.getElementById('backToTopBtn').onclick = () => {
    document.getElementById('examResultSection').style.display = 'none';
    document.getElementById('examDetailSection').style.display = 'none';
    document.getElementById('examPickSection').style.display = '';
    // 🎯 pool-first 戦略: トップ復帰時に復習モードをクリア (永続 AI モード防止)
    state.currentTopic = null;
    state.isReviewMode = false;
    try {
      const url = new URL(window.location.href);
      let dirty = false;
      if (url.searchParams.has('review')) { url.searchParams.delete('review'); dirty = true; }
      if (url.searchParams.has('topic')) { url.searchParams.delete('topic'); dirty = true; }
      if (dirty) window.history.replaceState({}, '', url);
    } catch (e) { /* silent */ }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 📥 解答解説 DL ボタン (2026-05-21 塾長指示) — global cache + click bind
  window._lastExamResult = result;
  window._lastExamSection = section;
  window._lastExamExam = exam;
  const _dlBtn = document.getElementById('downloadExamResultBtn');
  if (_dlBtn) {
    _dlBtn.onclick = () => {
      try { downloadExamResultMarkdown(result, exam, section); }
      catch (e) { console.warn('[exam-result-dl] failed:', e); alert('ダウンロード失敗: ' + (e.message || e)); }
    };
  }
  // 📄 PDF 保存ボタン (2026-05-21 塾長指示「PDF で保存できるように」)
  //    window.print() で browser の印刷ダイアログを呼び出し、ユーザーが「PDF として保存」を選択する pattern。
  //    @media print stylesheet で .ee-section-result のみを A4 white background で表示 (CSS で実装)。
  const _pdfBtn = document.getElementById('downloadExamResultPdfBtn');
  if (_pdfBtn) {
    _pdfBtn.onclick = () => {
      try { window.print(); }
      catch (e) { console.warn('[exam-result-pdf] failed:', e); alert('印刷ダイアログ起動失敗: ' + (e.message || e)); }
    };
  }

  // 🎯 2026-05-21 塾長指示「点数が画面トップに来るように」:
  //   旧: window.scrollTo({top:0}) → header しか見えず採点結果は画面外
  //   新: #resultScoreHero (点数 hero) を直接 viewport top に揃える (sticky header 越しに点数最優先)
  //   fallback: examResultSection → window.scrollTo({top:0})
  //   setTimeout で display 反映後の layout を待つ
  setTimeout(() => {
    const _hero = document.getElementById('resultScoreHero');
    const _section = document.getElementById('examResultSection');
    if (_hero) _hero.scrollIntoView({ behavior: 'smooth', block: 'start' });
    else if (_section) _section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    else window.scrollTo({ top: 0, behavior: 'smooth' });
  }, 80);
}

// 📥 採点結果を Markdown でダウンロード (2026-05-21 塾長指示「解答解説も DL できるように」)
// result.perQuestion[].{stem, userAnswer, correctAnswer, isCorrect, explanation, modelAnswer} を整形
// section.name と日時をファイル名に含めて履歴管理しやすく
function downloadExamResultMarkdown(result, exam, section) {
  if (!result || !Array.isArray(result.perQuestion)) {
    throw new Error('採点結果データが見つかりません');
  }
  const lines = [];
  const examName = (exam && exam.name) || '試験';
  const sectionName = (section && section.name) || '採点';
  const scoreMax = (section && section.scoreMax) || (exam && exam.scoreMax) || 30;
  const score = (typeof result.overallScore === 'number') ? result.overallScore : 0;
  const percent = scoreMax > 0 ? Math.round((score / scoreMax) * 100) : 0;
  const now = new Date();
  const dateStr = now.toLocaleString('ja-JP', { hour12: false });

  lines.push(`# 📝 ${examName} / ${sectionName} 採点結果`);
  lines.push('');
  lines.push(`- **得点**: ${score.toFixed(1)} / ${scoreMax} 点 (${percent}%)`);
  lines.push(`- **日時**: ${dateStr}`);
  if (result.scoringMethod) lines.push(`- **採点方式**: ${result.scoringMethod}`);
  lines.push('');

  if (Array.isArray(result.strengths) && result.strengths.length) {
    lines.push('## 🔍 強み');
    result.strengths.forEach(s => lines.push(`- ✅ ${s}`));
    lines.push('');
  }
  if (Array.isArray(result.weaknesses) && result.weaknesses.length) {
    lines.push('## 🛠 弱点');
    result.weaknesses.forEach(s => lines.push(`- ⚠️ ${s}`));
    lines.push('');
  }

  lines.push('## 📝 設問別フィードバック');
  lines.push('');
  result.perQuestion.forEach((q, i) => {
    const isCorrect = q.isCorrect;
    const status = (isCorrect === true) ? '✅ 正解' : (isCorrect === false ? '❌ 誤答' : '✍️ 自由記述');
    lines.push(`### Q${i + 1} ${status}`);
    lines.push('');
    if (q.stem) {
      lines.push(`**問題**:`);
      lines.push('');
      lines.push(String(q.stem));
      lines.push('');
    }
    if (q.userAnswer !== undefined && q.userAnswer !== null) {
      lines.push(`**あなたの回答**: ${String(q.userAnswer) || '(未回答)'}`);
      lines.push('');
    }
    if (q.correctAnswer !== undefined && q.correctAnswer !== null) {
      lines.push(`**正解**: ${String(q.correctAnswer)}`);
      lines.push('');
    }
    if (q.modelAnswer !== undefined && q.modelAnswer !== null && String(q.modelAnswer)) {
      lines.push(`**模範解答**:`);
      lines.push('');
      lines.push(String(q.modelAnswer));
      lines.push('');
    }
    if (q.explanation) {
      lines.push(`**解説**:`);
      lines.push('');
      lines.push(String(q.explanation));
      lines.push('');
    }
    // 自由記述で AI feedback がある場合 (resultFeedback 内で aiFb から拾っているもの)
    const aiFb = Array.isArray(result.feedback) ? result.feedback.find(f => f.stem === q.stem) : null;
    if (aiFb && (aiFb.score_breakdown || aiFb.comment)) {
      if (aiFb.score_breakdown) lines.push(`**採点詳細**: ${aiFb.score_breakdown}`);
      if (aiFb.comment) { lines.push(''); lines.push(`**コメント**: ${aiFb.comment}`); }
      lines.push('');
    }
    lines.push('---');
    lines.push('');
  });

  if (result.studyPlan) {
    lines.push('## 📋 学習プラン');
    lines.push('');
    lines.push(String(result.studyPlan));
    lines.push('');
  }

  lines.push('---');
  lines.push(`*Generated by トリリオン AI コーチング (${dateStr})*`);
  lines.push('');

  const md = lines.join('\n');
  const blob = new Blob([md], { type: 'text/markdown; charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  // file 名: 採点結果_<sectionName>_<YYYYMMDD-HHMM>.md (date-safe・OS 共通)
  const dtStamp = now.getFullYear()
    + String(now.getMonth() + 1).padStart(2, '0')
    + String(now.getDate()).padStart(2, '0') + '-'
    + String(now.getHours()).padStart(2, '0')
    + String(now.getMinutes()).padStart(2, '0');
  // file 名に含めない記号: / \ : * ? " < > | + 半角空白を _ に
  const safeName = sectionName.replace(/[\/\\:*?"<>|\s]+/g, '_');
  a.href = url;
  a.download = `採点結果_${safeName}_${dtStamp}.md`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { try { document.body.removeChild(a); URL.revokeObjectURL(url); } catch (_) {} }, 200);
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
  // 英検は g{N}_{key}、大学入試 (英語/文系/理系) は {univ}_{key} の compound key で sectionsByGrade を区別
  // 🛟 2026-05-16 QA audit (3 視点 review): rikei が compound list から除外されていた致命バグ修正
  //   旧: rikei では auto[rikei][todai_rikei_phys_q1] / SAMPLE_BANKS[rikei][todai_rikei_phys_q1] を
  //       lookup できず、未来 univ 別 bank 追加でもヒットしなかった。rikei を fallback list に追加。
  if (!autoBank && !staticBank && (examId === 'eiken' || examId === 'daigaku' || examId === 'bunkei' || examId === 'rikei') && state && state.eikenGrade) {
    const compoundKey = state.eikenGrade + '_' + sectionKey;
    // AUTO_GENERATED_BANKS にも compound key で問い合わせ
    const autoCompound = auto[examId] && auto[examId][compoundKey];
    const staticCompound = SAMPLE_BANKS[examId] && SAMPLE_BANKS[examId][compoundKey];
    if (autoCompound && staticCompound) return Math.random() < 0.6 ? autoCompound : staticCompound;
    if (autoCompound || staticCompound) return autoCompound || staticCompound;
    // 🛟 compound miss でも flat lookup を最後に試行 (rikei の math_basic/phys_basic_q 等
    //    _default grade での共通バンク用)
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
  // 🛟 2026-05-16 塾長指示: 「ローカル環境では preview のみ」は誤解を招いていた
  //   → localhost preview 検知時のみ明示し、本番では一般的なリトライ案内に統一。
  const isLocalPreview = (typeof window !== 'undefined'
    && window.location.hostname === 'localhost'
    && window.location.port === '8090');
  const isProduction = (typeof window !== 'undefined'
    && (window.location.hostname === 'trillion-ai-juku.com'
        || window.location.hostname === 'www.trillion-ai-juku.com'));
  let warningMsg;
  if (isProduction) {
    warningMsg = `🔄 ${exam.name} ${section.name} の問題を読み込み中です。下の「🔁 もう一度読み込む」ボタンを押すか、ページを再読み込みしてください (問題は順次表示されます)。`;
  } else if (isLocalPreview) {
    warningMsg = `⚠️ ローカル preview 環境では問題プールに接続できないことがあります。本番 URL (trillion-ai-juku.com) で問題プールから即時取り出されます。`;
  } else {
    warningMsg = `🔄 ${exam.name} ${section.name} の問題を読み込み中です。通信が不安定なようです。下の「🔁 もう一度読み込む」ボタンで再試行してください。`;
  }
  return {
    passage: '',
    audio_script: '',
    prompt: '',
    questions: [],
    _warning: warningMsg,
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
  // 📝 2026-05-22 塾長指示: question_attempts に DB 保存 (弱点プリント基盤)
  // localStorage に加えてサーバ側にも記録し、_run_weakness_aggregation で集計
  try { _postQuestionAttempt(exam, section, result); } catch (e) { console.warn('postQuestionAttempt failed (non-fatal):', e); }
};

// 📝 2026-05-22 弱点プリント基盤: 解答結果を /api/question-attempts に POST
async function _postQuestionAttempt(exam, section, result) {
  // ログインしている生徒のみ送信 (auth token なしの体験中は localStorage のみ)
  // ✅ 2026-05-22 fix: 既存 key 'ai_juku_session_token' に統一 (mypage.html L1102 と同一)
  const token = localStorage.getItem('ai_juku_session_token') || null;
  if (!token) return;
  // backend 用に exam_id / part_key を mapping
  const exam_id = (typeof _getBackendExamParams === 'function') ? (_getBackendExamParams(state.examId)?.exam || state.examId) : state.examId;
  const part_key = state.sectionKey || section.key || null;
  // ✅ 2026-05-22 P1 fix: section.scoreMax が undefined のとき max(score_got, 100) で score_max が膨らみ
  // is_correct 常に 0 誤判定。明示的に section.scoreMax → result.sectionScoreMax → 100 の順で取得し
  // score_got > score_max にならないよう先に max を確定する。
  const score_got = Math.max(0, Math.round(result.sectionScore ?? result.overallScore ?? 0));
  // ⚠️ score_max は section.scoreMax を最優先 (score_got とは独立に決定)
  let score_max = section.scoreMax;
  if (typeof score_max !== 'number' || score_max <= 0) score_max = result.sectionScoreMax;
  if (typeof score_max !== 'number' || score_max <= 0) score_max = 100;
  score_max = Math.round(score_max);
  // is_correct 判定 (score_max >= score_got を保証してから比率判定)
  const safe_max = Math.max(score_max, score_got, 1);
  const is_correct = (safe_max > 0 && score_got / safe_max >= 0.7) ? 1 : 0;
  const body = {
    source: 'practice',
    exam_id,
    part_key,
    subject: null,  // backend で _infer_subject_from_pool が推定
    // ✅ 2026-05-22 P0 fix: topic は学習単元名を入れる列で grade 名 ("東大"/"準1級") は意味的に汚染。
    // grade 情報は metadata.grade に既に入っているため null を送信。
    topic: null,
    is_correct,
    score_got,
    score_max,
    metadata: {
      examId: state.examId,
      sectionKey: state.sectionKey,
      grade: state.eikenGrade,
      gradeName: state.eikenGradeName,
      cefr: result.cefr,
    }
  };
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 5000);
  try {
    await fetch('/api/question-attempts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

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
    // escapeTextWithMath で <u>/<em>/<strong> を whitelist 復活 (2026-05-21 塾長指示「下線部を模試のように」)
    html += `<div class="ee-passage"><h3>📖 Reading Passage (AI が記事テーマで独自執筆・250-350語)</h3><p>${escapeTextWithMath(q.passage)}</p></div>`;
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

// part キー (例 r_q1) → 日本語の section 名 (例 「📝 Reading 大問1 (短文穴埋め)」)
// archive list の問題カードで「何の問題か」を分かりやすく表示するため
function _archGetPartLabel(exam, grade, partKey) {
  if (!exam || !partKey) return partKey || '';
  let secs = [];
  try {
    if (exam === 'eiken' && grade) secs = getEikenSections(grade);
    else if (exam === 'daigaku' && grade) secs = getDaigakuSections(grade);
    else if (exam === 'rikei' && grade && typeof getRikeiSections === 'function') secs = getRikeiSections(grade);
    else secs = (EXAMS[exam] && EXAMS[exam].sections) || [];
  } catch (e) { secs = []; }
  const sec = (secs || []).find(s => s.key === partKey);
  if (sec) return `${sec.icon || ''} ${sec.name}`.trim();
  return partKey;
}

// 試験キー → 表示ラベル + 大カテゴリ (大タブ filter 用)
// rikei/todai/kyodai/kyotsu 等 backend が返す全 key を網羅
function _archGetGroupMeta(exam, grade) {
  // 試験名 label (icon + 名前)
  const examLabels = {
    toefl: '🇺🇸 TOEFL',
    toeic: '💼 TOEIC',
    ielts: '🇬🇧 IELTS',
    eiken: '🇯🇵 英検',
    daigaku: '🎓 大学入試',
    rikei: '🔬 理系大学',
  };
  // grade (級・大学キー) → 表示名
  const gradeLabels = {
    // 英検
    g1: '1級', gp1: '準1級', g2: '2級', gp2: '準2級', g3: '3級', g4: '4級', g5: '5級',
    // 大学入試 (主要)
    todai: '東大', kyodai: '京大', osaka: '阪大', tokoda: '東工大',
    hitotsu: '一橋', nagoya: '名大', tohoku: '東北大', kyushu: '九大', hokudai: '北大',
    waseda: '早稲田', keio: '慶應', sophia: '上智', icu: '国際基督教',
    meiji: '明治', aoyama: '青山学院', rikkyo: '立教', chuo: '中央', hosei: '法政',
    kansai: '関西', kangaku: '関学', doshisha: '同志社', ritsumei: '立命館',
    kyotsu: '共通テスト', center: 'センター',
    igakubu_kokoritsu: '医学部 (国公立)', igakubu_shiritsu: '医学部 (私立)',
    todai_rikei: '東大 理系', kyodai_rikei: '京大 理系',
    osaka_rikei: '阪大 理系', tokoda_rikei: '東工大 理系',
    kokoritsu_rikei: '国公立 理系', kyotsu_rikei: '共通テスト 理系',
    igakubu_kokoritsu_rikei: '医学部 (国公立) 理系',
  };
  // 大カテゴリ判定 (タブ filter 用)
  let category;
  if (exam === 'eiken') category = 'eiken';
  else if (exam === 'toefl' || exam === 'toeic' || exam === 'ielts') category = 'overseas';
  else if (exam === 'rikei' || /rikei/.test(grade || '')) category = 'rikei';
  else if (exam === 'daigaku') category = 'daigaku';
  else category = 'other';
  // 表示名 (label + grade)
  const examLbl = examLabels[exam] || `📋 ${exam}`;
  const gradeLbl = gradeLabels[grade] || (grade || '');
  return { category, examLbl, gradeLbl };
}

// 大カテゴリタブ + 検索バーで client side filter
let _ARCH_OVERVIEW_CACHE = null;  // 全カード data (フェッチ後キャッシュ)

async function loadArchiveOverview(examId = null) {
  const box = document.getElementById('archOverview');
  const list = document.getElementById('archList');
  box.style.display = '';
  list.style.display = 'none';
  // キャッシュ済なら fetch せず render のみ (タブ切替・検索 input 用)
  if (_ARCH_OVERVIEW_CACHE && !examId) {
    _renderArchiveOverview(_ARCH_OVERVIEW_CACHE);
    return;
  }
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
    const byKey = new Map();
    data.groups.forEach(g => {
      const k = `${g.exam}/${g.grade || '_'}`;
      if (!byKey.has(k)) byKey.set(k, { exam: g.exam, grade: g.grade, parts: [], total: 0 });
      const o = byKey.get(k);
      o.parts.push({ part: g.part, count: g.count });
      o.total += g.count;
    });
    const cards = [...byKey.values()].sort((a, b) => b.total - a.total).map(o => {
      const meta = _archGetGroupMeta(o.exam, o.grade);
      // 検索 hit 用: 空白あり版 + 空白なし版の両方を持つ (「英検2級」「英検 2級」両方 hit)
      const baseText = `${meta.examLbl} ${meta.gradeLbl} ${o.exam} ${o.grade || ''}`.toLowerCase();
      return { ...o, ...meta, searchText: baseText + ' ' + baseText.replace(/\s+/g, '') };
    });
    _ARCH_OVERVIEW_CACHE = { total: data.total, cards };
    _renderArchiveOverview(_ARCH_OVERVIEW_CACHE);
  } catch (e) {
    console.warn('[archive] overview failed:', e);
    box.innerHTML = `<p class="ee-error">⚠️ 取得失敗: ${escapeHtml(String(e.message || e))}</p>`;
  }
}

function _renderArchiveOverview({ total, cards }) {
  const box = document.getElementById('archOverview');
  if (!box) return;

  // タブの可視性を card 数で判定 (空カテゴリのタブは hide。塾長指示 2026-04-30)
  // 「all」は常時表示、それ以外はカードがあるカテゴリのみ
  const tabCounts = {};
  cards.forEach(c => { tabCounts[c.category] = (tabCounts[c.category] || 0) + 1; });
  document.querySelectorAll('.archive-cat-tab').forEach(tab => {
    const cat = tab.dataset.cat;
    if (cat === 'all') { tab.style.display = ''; return; }
    tab.style.display = (tabCounts[cat] || 0) > 0 ? '' : 'none';
  });
  // 現在 active なタブが空カテゴリだった場合は all に戻す
  const activeTabPrev = document.querySelector('.archive-cat-tab.active');
  if (activeTabPrev && activeTabPrev.dataset.cat !== 'all' && (tabCounts[activeTabPrev.dataset.cat] || 0) === 0) {
    activeTabPrev.classList.remove('active');
    document.querySelector('.archive-cat-tab[data-cat="all"]')?.classList.add('active');
  }

  // 現在のカテゴリタブと検索クエリで filter
  const activeTab = document.querySelector('.archive-cat-tab.active');
  const cat = activeTab ? activeTab.dataset.cat : 'all';
  const query = (document.getElementById('archSearchInput')?.value || '').trim().toLowerCase();

  let filtered = cards;
  if (cat !== 'all') {
    filtered = filtered.filter(c => c.category === cat);
  }
  if (query) {
    // 検索クエリも空白除去版を作って hit 判定 (「英検2級」「東大 理系」両方ヒット)
    const q1 = query;
    const q2 = query.replace(/\s+/g, '');
    filtered = filtered.filter(c => c.searchText.includes(q1) || c.searchText.includes(q2));
  }

  let html = `<div class="archive-overview-head">📊 蓄積総数: <strong>${total}</strong> 問 (絞り込み: ${filtered.length} カテゴリ)</div>`;
  if (filtered.length === 0) {
    html += `<p class="ee-empty">📭 該当するカードがありません。タブを切り替えるか、検索キーワードを変更してください。</p>`;
    box.innerHTML = html;
    return;
  }
  html += '<div class="archive-overview-grid">';
  filtered.forEach(o => {
    const gradeBadge = o.gradeLbl ? ` <span class="arch-grade-tag">${escapeHtml(o.gradeLbl)}</span>` : '';
    html += `<button type="button" class="archive-group-card" data-exam="${escapeHtml(o.exam)}" data-grade="${escapeHtml(o.grade || '')}">
      <div class="arch-group-name">${escapeHtml(o.examLbl)}${gradeBadge}</div>
      <div class="arch-group-count">${o.total} 問</div>
      <div class="arch-group-parts">${o.parts.length} 大問 → クリックで一覧</div>
    </button>`;
  });
  html += '</div>';
  box.innerHTML = html;
  // カードクリック = 即遷移 (絞り込みボタン不要) + 問題リストまで自動スクロール
  box.querySelectorAll('.archive-group-card').forEach(btn => {
    btn.addEventListener('click', () => {
      ARCH_STATE.exam = btn.dataset.exam;
      ARCH_STATE.grade = btn.dataset.grade || null;
      ARCH_STATE.part = null;
      ARCH_STATE.year = null;
      // 旧 hidden filter UI も同期 (loadArchiveList 内部で参照されるため)
      const examF = document.getElementById('archExamFilter');
      const gradeF = document.getElementById('archGradeFilter');
      if (examF) examF.value = ARCH_STATE.exam;
      if (typeof populateArchGradeOptions === 'function') populateArchGradeOptions();
      if (gradeF) gradeF.value = ARCH_STATE.grade || '';
      if (typeof populateArchPartOptions === 'function') populateArchPartOptions();
      loadArchiveList();
      // 塾長指示 2026-04-30: クリック後に問題一覧まで自動スクロール
      // (loadArchiveList で archList が表示される → 80ms 後に scrollIntoView)
      setTimeout(() => {
        const list = document.getElementById('archList');
        if (list) {
          // 一覧 + ヘッダ全体が見えるように nav bar 分の offset (60px) を確保
          const rect = list.getBoundingClientRect();
          const targetY = window.scrollY + rect.top - 60;
          window.scrollTo({ top: Math.max(0, targetY), behavior: 'smooth' });
        }
      }, 100);
    });
  });
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
    // 試験名 + 大学/級ラベルを取得 (ARCH_STATE 優先、なければ data.items[0] から)
    const headExam = ARCH_STATE.exam || (data.items[0] && data.items[0].exam);
    const headGrade = ARCH_STATE.grade || (data.items[0] && data.items[0].grade);
    const headMeta = headExam ? _archGetGroupMeta(headExam, headGrade) : { examLbl: '', gradeLbl: '' };
    const headTitle = `${headMeta.examLbl}${headMeta.gradeLbl ? ' ' + headMeta.gradeLbl : ''}`.trim();

    let html = `<div class="archive-list-head">
      <div class="arch-list-head-title">
        <span class="arch-list-head-exam">${escapeHtml(headTitle || '問題一覧')}</span>
        <span class="arch-list-head-count"><strong>${data.total} 問</strong> 該当 (上位 ${data.items.length} 件)</span>
      </div>
      <button class="ee-btn ee-btn-ghost ee-btn-mini" id="archBackBtn">← 全体ビューに戻る</button>
    </div>`;
    html += '<div class="archive-items">';
    data.items.forEach(it => {
      const yearTag = it.year ? `<span class="arch-year-tag">${it.year}年度</span>` : '';
      // 大学/級名: backend が univ_simulated 返してくれば優先、なければ ARCH_STATE.grade or it.grade から正規化
      let univDisplay = it.univ_simulated || '';
      if (!univDisplay) {
        const meta = _archGetGroupMeta(it.exam, it.grade);
        univDisplay = meta.gradeLbl || '';
      }
      const univTag = univDisplay ? `<span class="arch-univ-tag">🎓 ${escapeHtml(univDisplay)}</span>` : '';
      // part キー (r_q1 等) → 日本語ラベル「📝 Reading 大問1 (短文穴埋め)」(塾長指示 2026-04-30)
      const partLabel = _archGetPartLabel(it.exam, it.grade, it.part);
      html += `<div class="archive-item-card">
        <div class="arch-item-meta">${univTag}${yearTag}<span class="arch-item-part" title="${escapeHtml(it.part)}">${escapeHtml(partLabel)}</span><span class="arch-item-q">${it.question_count}問</span></div>
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
  // 大カテゴリタブ
  const tabs = document.querySelectorAll('.archive-cat-tab');
  tabs.forEach(t => {
    t.addEventListener('click', () => {
      tabs.forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      // キャッシュ済データから即 re-render (fetch 不要)
      if (_ARCH_OVERVIEW_CACHE) _renderArchiveOverview(_ARCH_OVERVIEW_CACHE);
    });
  });
  // 検索バー (リアルタイム filter・debounce 200ms)
  const searchInp = document.getElementById('archSearchInput');
  if (searchInp) {
    let _searchTimer = null;
    searchInp.addEventListener('input', () => {
      clearTimeout(_searchTimer);
      _searchTimer = setTimeout(() => {
        if (_ARCH_OVERVIEW_CACHE) _renderArchiveOverview(_ARCH_OVERVIEW_CACHE);
      }, 200);
    });
  }
  // 旧 hidden filter UI (loadArchiveList 内部で参照されるため残置)
  const examSel = document.getElementById('archExamFilter');
  const gradeSel = document.getElementById('archGradeFilter');
  const partSel = document.getElementById('archPartFilter');
  const yearInp = document.getElementById('archYearFilter');
  const searchBtn = document.getElementById('archSearchBtn');
  if (!examSel) return;
  // 旧経路: hidden になってるが値変更 → state 同期 (history 復元等で動く)
  examSel.addEventListener('change', () => {
    ARCH_STATE.exam = examSel.value || null;
  });
  gradeSel.addEventListener('change', () => {
    ARCH_STATE.grade = gradeSel.value || null;
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
    // 📚 マイ参考書 inject (塾長指示 2026-05-14): ログイン済なら Authorization header 付与
    // backend `public_curriculum_generate` が Authorization を opportunistic に解釈して使用中マイ参考書を inject する
    const headers = { 'Content-Type': 'application/json' };
    try {
      const token = localStorage.getItem('ai_juku_session_token');
      if (token) headers['Authorization'] = 'Bearer ' + token;
    } catch (_) {}
    const res = await fetch(`${backend}/api/curriculum/generate`, {
      method: 'POST', headers,
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

  // 🎯 2026-05-13 塾長指示「画像の部分は生徒には見せる必要はないので隠して」:
  //   アーカイブ overview (pool 蓄積数を可視化) は admin/CEO 内部用 → 生徒画面では非表示
  //   admin token 保持時のみ archiveSection を表示。生徒 session token のみなら完全 hide。
  try {
    const hasAdmin = !!localStorage.getItem('ai_juku_admin_token');
    if (!hasAdmin) {
      const archSec = document.getElementById('archiveSection');
      if (archSec) archSec.style.display = 'none';
    }
  } catch (e) { /* silent: localStorage 不可ブラウザでもエラー化させない */ }

  // ⚠️ DEPRECATED (2026-05-21 塾長指示): クイックスタート + 定期テスト勉強モードは quick-start.html に分離。
  //   このページの quickStartBar / teikiUnitBar セクションは削除済 → 以下の handler は DOM 要素無しで no-op になる。
  //   実体は quick-start.js (TEIKI_UNIT_INDEX も含む)。URL ?focus= / ?teiki_unit=1 経由でこのページに戻る。
  //   将来 quickStartBar を復活させたい場合のために handler は残置 (Chesterton's Fence)。

  // 🎯 2026-05-15 (deprecated 2026-05-21) クイックスタートを 5 科目 (国語/英語/理科/社会/数学) に再編
  // 1) プルダウン toggle (▾ ボタン)
  document.querySelectorAll('.qs-toggle').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const dropdown = btn.closest('.qs-dropdown');
      const menu = dropdown ? dropdown.querySelector('.qs-menu') : null;
      if (!menu) return;
      // 他の menu を全て閉じる
      document.querySelectorAll('.qs-menu').forEach(m => { if (m !== menu) m.hidden = true; });
      document.querySelectorAll('.qs-toggle').forEach(t => { if (t !== btn) t.setAttribute('aria-expanded', 'false'); });
      const willOpen = menu.hidden;
      menu.hidden = !willOpen;
      btn.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });
  });

  // 2) document クリックで全 menu を閉じる
  document.addEventListener('click', (e) => {
    if (e.target.closest('.qs-dropdown')) return; // dropdown 内クリックは無視
    document.querySelectorAll('.qs-menu').forEach(m => { m.hidden = true; });
    document.querySelectorAll('.qs-toggle').forEach(t => t.setAttribute('aria-expanded', 'false'));
  });

  // 3) 全 [data-qs-exam] 要素 (直接ボタン + プルダウン内ボタン) を bind
  document.querySelectorAll('[data-qs-exam]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const examId = btn.dataset.qsExam;
      if (!examId) return;
      const subject = btn.dataset.qsSubject;
      // subject hint を localStorage に保存 (sections フィルタで参照)
      try {
        if (subject) localStorage.setItem(QS_SUBJECT_HINT_KEY, subject);
        else localStorage.removeItem(QS_SUBJECT_HINT_KEY);
      } catch (_) { /* localStorage 不可ブラウザ無視 */ }
      // menu を閉じる
      document.querySelectorAll('.qs-menu').forEach(m => { m.hidden = true; });
      document.querySelectorAll('.qs-toggle').forEach(t => t.setAttribute('aria-expanded', 'false'));
      try { pickExam(examId); } catch (err) { console.warn('quick-start failed:', err); }
      // gradePickSection or examDetailSection までスクロール
      setTimeout(() => {
        const target = document.getElementById('gradePickSection') || document.getElementById('examDetailSection');
        if (target && target.style.display !== 'none') {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    });
  });

  // ⚠️ DEPRECATED (2026-05-21): TEIKI_UNIT_INDEX + bindTeikiUnit IIFE は quick-start.js に移植済。
  //   teikiUnitBar セクション削除に伴い、bindTeikiUnit() 内の getElementById は全 null → 早期 return で no-op。
  //   実体 (live source) は quick-start.js を編集すること。ここは Chesterton's Fence で残置 (復活時の reference)。
  // 🎯 2026-05-15 (deprecated 2026-05-21) 定期テスト単元プルダウンの単元インデックス
  const TEIKI_UNIT_INDEX = {
    '📐 数学 IA (共通テスト基礎)': [
      { label: '二次関数 (最大最小・頂点)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'二次関数' },
      { label: '図形と計量 (正弦/余弦定理)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'図形と計量' },
      { label: 'データの分析 (分散/相関/箱ひげ)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'データ' },
      { label: '場合の数と確率 (順列/組合せ/条件付)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'確率' },
      { label: '整数の性質 (合同式/不定方程式)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'整数' },
      { label: '二次方程式 (判別式・解の公式)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'二次方程式' },
      { label: '円と直線 (接線/弦)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'円と直線' },
    ],
    '📐 数学 IIB (共通テスト基礎)': [
      { label: '三角関数 (加法定理/合成)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'三角関数' },
      { label: '指数対数 (方程式/不等式/桁数)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'指数対数' },
      { label: '微分積分 (極値/定積分/面積)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'微積' },
      { label: '数列 (等差/等比/漸化式)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'数列' },
      { label: 'ベクトル (内積/成分/空間)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'ベクトル' },
    ],
    '⚛️ 物理基礎': [
      { label: '運動 (等加速度/自由落下)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'運動' },
      { label: '力 (F=ma/摩擦/円運動)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'力' },
      { label: '仕事とエネルギー', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'エネルギー' },
      { label: '熱 (比熱/熱効率)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'熱' },
      { label: '波 (音波/光波)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'波' },
      { label: '電気回路 (オーム法則/電力)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'電気' },
      { label: '運動量と力積', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'運動量' },
      { label: '単振動', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'単振動' },
    ],
    '🧪 化学基礎': [
      { label: 'mol 計算 (物質量)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'mol' },
      { label: '原子の構造と周期表', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'周期表' },
      { label: '化学結合 (イオン/共有)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'結合' },
      { label: '酸と塩基 (pH/中和)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'酸塩基' },
      { label: '酸化還元 (滴定含む)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'酸化還元' },
      { label: '化学反応 (反応式/量的関係)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'反応' },
      { label: '熱化学 (燃焼熱/ヘスの法則)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'熱化学' },
      { label: '反応速度', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'反応速度' },
    ],
    '🧬 生物基礎': [
      { label: '細胞 (小器官/構造)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'細胞' },
      { label: 'DNA (転写/翻訳/複製)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'DNA' },
      { label: '体内環境 (恒常性/腎臓/肝臓)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'体内環境' },
      { label: '免疫 (自然/獲得/血液型)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'免疫' },
      { label: '生態系 (物質循環/植生遷移)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'生態系' },
      { label: 'ATP とエネルギー代謝', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'ATP' },
      { label: '酵素・タンパク質', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'酵素' },
      { label: '自律神経・ホルモン', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'自律神経' },
    ],
    '🇬🇧 英語 文法 (定期テスト)': [
      { label: '関係代名詞 (who/which/whose)', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'関係' },
      { label: '分詞構文', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'分詞' },
      { label: '仮定法', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'仮定法' },
      { label: '比較', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'比較' },
      { label: '受動態 (完了形含む)', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'受動態' },
      { label: '不定詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'不定詞' },
      { label: '時制 (現在完了)', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'時制' },
      { label: '前置詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'前置詞' },
      { label: '接続詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'接続詞' },
      { label: '助動詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'助動詞' },
      { label: '動名詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'動名詞' },
    ],
    '📖 英語 長文 (定期テスト)': [
      { label: '長文読解 (教科書系トピック)', exam_id:'daigaku', part_key:'r_long', eiken_grade:'teiki', topic:'' },
    ],
    '✉️ 英語 実用短文 (定期テスト)': [
      { label: '実用文 (案内/メール/広告)', exam_id:'daigaku', part_key:'r_short', eiken_grade:'teiki', topic:'' },
    ],
    '✍️ 英作文 (定期テスト)': [
      { label: '英作文 (40-60 語の意見)', exam_id:'daigaku', part_key:'w_essay', eiken_grade:'teiki', topic:'' },
    ],
    // 🛠 国語/社会は bunkei flow (sectionsByGrade に <part>_kyotsu 形式で定義) — backend は _getBackendExamParams で daigaku に翻訳
    '📜 古文 (共通テスト基礎)': [
      { label: '動詞の活用', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'活用' },
      { label: '助動詞 (けり/む/べし)', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'助動詞' },
      { label: '敬語 (尊敬/謙譲/丁寧)', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'敬語' },
      { label: '古典単語', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'単語' },
      { label: '係り結びの法則', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'係り結び' },
      { label: '識別問題 (に/なむ)', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'識別' },
      { label: '読解 (竹取/枕草子/平家)', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'読解' },
    ],
    '🀄 漢文 (共通テスト基礎)': [
      { label: '返り点 (レ点/一二点)', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'返り点' },
      { label: '書き下し文', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'書き下し' },
      { label: '再読文字', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'再読文字' },
      { label: '句法 (使役/受身/反語/比較)', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'句法' },
      { label: '読解 (論語/孟子/史記)', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'読解' },
    ],
    '🗾 日本史 (共通テスト基礎)': [
      { label: '古代 (大化の改新/律令制)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'古代' },
      { label: '中世 (鎌倉/室町/応仁の乱)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'中世' },
      { label: '近世 (江戸/鎖国/享保改革)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'近世' },
      { label: '近代 (明治維新/自由民権)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'近代' },
      { label: '現代 (戦後復興/高度経済成長)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'現代' },
      { label: '文化史 (国風/天平/化政)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'文化' },
    ],
    '🌍 世界史 (共通テスト基礎)': [
      { label: '古代 (ギリシア/ローマ)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'古代' },
      { label: '中世 (十字軍/百年戦争)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'中世' },
      { label: 'イスラーム史', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'イスラーム' },
      { label: 'アジア (中国通史/インド)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'中国' },
      { label: '近代 (フランス革命/産業革命)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'近代' },
      { label: '現代 (冷戦/中東/グローバル化)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'現代' },
    ],
    '🗺 地理 (共通テスト基礎)': [
      { label: '気候 (ケッペン区分)', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'気候' },
      { label: '地形 (プレート/河川/バイオーム)', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'地形' },
      { label: '人口・都市 (メガシティ)', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'人口' },
      { label: '農業・食料', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'農業' },
      { label: '工業・鉱産資源', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'工業' },
      { label: '環境問題・エネルギー', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'環境' },
    ],
    '⚖️ 公民 (共通テスト基礎)': [
      { label: '憲法 (三大原則/9条)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'憲法' },
      { label: '三権分立 (国会/内閣/裁判所)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'三権' },
      { label: '基本的人権', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'人権' },
      { label: '地方自治・選挙', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'地方' },
      { label: '経済 (需給/GDP/金融)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'経済' },
      { label: '国際政治 (国連/EU)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'国際' },
      { label: '倫理 (思想家)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'倫理' },
    ],
  };

  // 単元プルダウン bind
  (function bindTeikiUnit(){
    const subjSel = document.getElementById('teikiSubjectSel');
    const unitSel = document.getElementById('teikiUnitSel');
    const goBtn = document.getElementById('teikiUnitGo');
    if (!subjSel || !unitSel || !goBtn) return;
    // 科目 select を populate
    Object.keys(TEIKI_UNIT_INDEX).forEach(subj => {
      const opt = document.createElement('option');
      opt.value = subj; opt.textContent = subj;
      subjSel.appendChild(opt);
    });
    subjSel.addEventListener('change', () => {
      const subj = subjSel.value;
      // 単元 select をリセット & populate
      unitSel.innerHTML = '<option value="">-- 単元を選択 --</option>';
      if (!subj || !TEIKI_UNIT_INDEX[subj]) {
        unitSel.disabled = true;
        goBtn.disabled = true;
        return;
      }
      TEIKI_UNIT_INDEX[subj].forEach((u, i) => {
        const opt = document.createElement('option');
        opt.value = String(i);
        opt.textContent = u.label;
        unitSel.appendChild(opt);
      });
      unitSel.disabled = false;
      goBtn.disabled = true;
    });
    unitSel.addEventListener('change', () => {
      goBtn.disabled = !unitSel.value;
    });
    goBtn.addEventListener('click', () => {
      const subj = subjSel.value;
      const idx = parseInt(unitSel.value, 10);
      if (!subj || isNaN(idx)) return;
      const unit = (TEIKI_UNIT_INDEX[subj] || [])[idx];
      if (!unit) return;
      // state にセット
      const exam = EXAMS[unit.exam_id];
      if (!exam) {
        console.warn('[teiki-unit] unknown exam:', unit.exam_id);
        return;
      }
      state.examId = unit.exam_id;
      state.eikenGrade = unit.eiken_grade;
      // grade name を items から取得
      const gradeItem = (exam.grades || []).find(g => g.key === unit.eiken_grade);
      state.eikenGradeName = gradeItem ? gradeItem.name : unit.eiken_grade;
      state.currentTopic = unit.topic || null;
      state.isReviewMode = false;
      // section を取得 (sectionsByGrade に該当 part_key があるか確認)
      const allSections = (exam.sectionsByGrade && exam.sectionsByGrade[unit.eiken_grade])
        || exam.sections || [];
      const section = allSections.find(s => s.key === unit.part_key) || allSections[0];
      if (!section) {
        alert('該当する大問が見つかりませんでした。');
        return;
      }
      state.sectionKey = section.key;
      // 直接 examDetailSection を表示 + section card 自動選択 + startSection
      try { pickExamSections(unit.exam_id); } catch (e) { console.warn(e); }
      setTimeout(() => {
        // section card を selected 化
        document.querySelectorAll('.section-card').forEach(c => {
          c.classList.toggle('selected', c.dataset.section === section.key);
        });
        try { startSection(section); } catch (e) { console.warn('[teiki-unit] startSection failed:', e); }
        // scroll to question area
        const qBox = document.getElementById('questionBox') || document.getElementById('examDetailSection');
        if (qBox) setTimeout(() => qBox.scrollIntoView({ behavior:'smooth', block:'start' }), 200);
      }, 80);
    });
  })();

  // 🎯 URL ?focus= で初期 exam-card auto-select (2026-05-13 塾長指示・大学入試問題演習 tab 分離対応)
  // index.html の「📚 大学入試問題演習」タブ → english-exam.html?focus=daigaku で自動選択
  try {
    const focusExam = new URLSearchParams(window.location.search).get('focus');
    const allowedFocus = ['toefl', 'toeic', 'ielts', 'eiken', 'daigaku', 'rikei', 'bunkei'];
    if (focusExam && allowedFocus.includes(focusExam)) {
      const card = document.querySelector(`.exam-card[data-exam="${focusExam}"]`);
      if (card) {
        // DOM bind 完了後に発火させるため 1 tick 遅延 + 完了後に gradePickSection へスクロール
        setTimeout(() => {
          try { card.click(); } catch (e) {}
          // gradePicker が出たらそこにスクロール (200ms 後)
          setTimeout(() => {
            const target = document.getElementById('gradePickSection');
            if (target && target.style.display !== 'none') {
              target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }, 250);
        }, 0);
      }
    }
  } catch (e) { /* silent */ }

  // 🎯 URL ?teiki_unit=1&exam_id=...&part_key=...&eiken_grade=...&topic=... で定期テスト単元演習を直接起動
  // (2026-05-21 塾長指示: quick-start.html 分離対応・元の bindTeikiUnit goBtn click ハンドラを URL params 駆動化)
  // 🔒 URL params は untrusted — 全 4 値を whitelist 検証 (eikenGrade / partKey も exam.grades / allSections に存在チェック)。
  //    検証漏れは AI prompt injection 経路になる (state.eikenGradeName / state.currentTopic が prompt template に注入されるため)。
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get('teiki_unit') === '1') {
      const examId = params.get('exam_id');
      const partKey = params.get('part_key');
      const eikenGrade = params.get('eiken_grade');
      // topic は AI prompt に流入 → 長さ制限 + 改行/タブ除去で injection 緩和
      const topic = (params.get('topic') || '').slice(0, 40).replace(/[\n\r\t]/g, ' ').trim();
      const allowedExam = ['daigaku', 'rikei', 'bunkei'];
      if (examId && partKey && eikenGrade && allowedExam.includes(examId)) {
        const exam = EXAMS[examId];
        // 🔒 eikenGrade は exam.grades の登録キーに限定 (一致しない値の raw 注入を遮断)
        const gradeItem = exam ? (exam.grades || []).find(g => g.key === eikenGrade) : null;
        if (exam && gradeItem) {
          // 🔒 partKey は実際の allSections に存在するキーに限定 (silent fallback で別大問が暴発するのを防ぐ)
          const allSections = (exam.sectionsByGrade && exam.sectionsByGrade[eikenGrade])
            || exam.sections || [];
          const section = allSections.find(s => s.key === partKey);
          if (section) {
            state.examId = examId;
            state.eikenGrade = eikenGrade;
            state.eikenGradeName = gradeItem.name;
            state.currentTopic = topic || null;
            state.isReviewMode = false;
            state.sectionKey = section.key;
            // DOM bind 完了後に発火 (focus= と同じ 1 tick 遅延パターン)
            setTimeout(() => {
              try { pickExamSections(examId); } catch (e) { console.warn('[teiki-unit-url] pickExamSections failed:', e); }
              setTimeout(() => {
                document.querySelectorAll('.section-card').forEach(c => {
                  c.classList.toggle('selected', c.dataset.section === section.key);
                });
                try { startSection(section); } catch (e) { console.warn('[teiki-unit-url] startSection failed:', e); }
                const qBox = document.getElementById('questionBox') || document.getElementById('examDetailSection');
                if (qBox) setTimeout(() => qBox.scrollIntoView({ behavior:'smooth', block:'start' }), 200);
              }, 80);
            }, 0);
          } else {
            console.warn('[teiki-unit-url] invalid part_key, ignored:', partKey);
          }
        } else {
          console.warn('[teiki-unit-url] invalid exam_id / eiken_grade, ignored:', examId, eikenGrade);
        }
      }
    }
  } catch (e) { /* silent */ }
  // 🎯 2026-05-13 塾長指示「現在の CEFR は不要」: UI から削除済。
  //    AI prompt 用に内部デフォルト ('B1') のみ保持。受験予定試験の grade/score で
  //    十分にレベルが推定できるため自己申告 UI は冗長だった。
  const _curLvEl = document.getElementById('currentLevel');
  if (_curLvEl) {
    _curLvEl.addEventListener('change', e => { state.currentLevel = e.target.value; });
    state.currentLevel = _curLvEl.value || 'B1';
  } else {
    state.currentLevel = 'B1';
  }

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
  // 🖨 印刷ボタン (塾長指示 2026-04-30): 問題本文のみ印刷 (CSS @media print で他要素を隠す)
  document.getElementById('printRunnerBtn')?.addEventListener('click', () => {
    window.print();
  });

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
