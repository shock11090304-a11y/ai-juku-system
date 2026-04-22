// ==========================================================================
// 教材データベース — 具体的な書名・レベル・使い方ガイド
// カリキュラム生成AIが参照し、生徒に最適な教材を具体的に指定するためのマスター
// ==========================================================================

const TEXTBOOKS_DB = {
  '英語': {
    '英単語': [
      { name: 'システム英単語 (シス単)', publisher: '駿台文庫', level: ['基礎','標準','応用'], vol: '2021語', use: 'ミニマルフレーズで記憶。第1-2章=共通テスト、第3-4章=難関大', recommended: ['高1-3','共通テスト','GMARCH','早慶','国立難関'] },
      { name: 'ターゲット1900', publisher: '旺文社', level: ['基礎','標準'], vol: '1900語', use: 'レベル別Part1/2/3。1日100語×19日で1周', recommended: ['高1-3','共通テスト','日東駒専','GMARCH'] },
      { name: '速読英単語 必修編', publisher: 'Z会', level: ['標準'], vol: '1900語+70長文', use: '文脈で覚えるので忘れにくい。音読推奨', recommended: ['高2-3','GMARCH','早慶'] },
      { name: '速読英単語 上級編', publisher: 'Z会', level: ['応用','難関'], vol: '1300語+50長文', use: '準1級〜1級レベル。早慶・国立難関用', recommended: ['高3','早慶','東大','京大'] },
      { name: 'DUO 3.0', publisher: 'アイシーピー', level: ['標準','応用'], vol: '1600語', use: '560例文で熟語も同時習得。音声CD併用', recommended: ['TOEIC','英検','高2-3'] },
      { name: 'パス単 英検準1級', publisher: '旺文社', level: ['応用'], vol: '1700語', use: '英検準1級専用。頻出順配列', recommended: ['英検準1級'] },
      { name: 'パス単 英検1級', publisher: '旺文社', level: ['難関'], vol: '2100語', use: '英検1級専用。学術語彙多い', recommended: ['英検1級'] },
      { name: '鉄緑会 東大英単語熟語 鉄壁', publisher: 'KADOKAWA', level: ['応用','難関'], vol: '約3000語', use: '東大頻出語を網羅。1年かけて完成', recommended: ['高2-3','東大','京大'] },
    ],
    '英文法': [
      { name: '大岩のいちばんはじめの英文法 超基礎編', publisher: 'ナガセ', level: ['基礎'], vol: '10講', use: '中学レベルの復習。英語苦手生の最初の1冊', recommended: ['中3-高1','英語苦手'] },
      { name: 'Vintage', publisher: 'いいずな書店', level: ['標準','応用'], vol: '1500問', use: '私大・共通テスト頻出文法・語法。章末問題で習熟', recommended: ['高2-3','共通テスト','GMARCH'] },
      { name: 'Next Stage (ネクステ)', publisher: '桐原書店', level: ['標準','応用'], vol: '1500問', use: 'Vintageと同系統。問題密度高い', recommended: ['高2-3','GMARCH','早慶'] },
      { name: 'スクランブル英文法・語法', publisher: '旺文社', level: ['標準','応用'], vol: '2100問', use: 'ランダム配列で実戦的。難関大対策', recommended: ['高3','早慶','国立'] },
      { name: '英文法・語法 Vintage', publisher: 'いいずな書店', level: ['応用','難関'], vol: '難関大向け', use: '上記の発展版。挑戦的な語法問題', recommended: ['早慶','国立難関'] },
      { name: 'Forest (総合英語)', publisher: '桐原書店', level: ['基礎','標準','応用'], vol: '参考書', use: '文法の辞書的参照用。問題集併用必須', recommended: ['高1-3'] },
      { name: 'ロイヤル英文法', publisher: '旺文社', level: ['応用','難関'], vol: '参考書', use: '最高峰の文法事典。論理的理解用', recommended: ['東大','京大','英検1級'] },
    ],
    '英文解釈': [
      { name: 'ビジュアル英文解釈 Part I', publisher: '駿台文庫', level: ['標準'], vol: '60課', use: 'SVO把握から始める。解説豊富', recommended: ['高2-3','GMARCH','早慶'] },
      { name: 'ポレポレ英文読解プロセス50', publisher: '代々木ライブラリー', level: ['応用','難関'], vol: '50題', use: '難構文50題。国立二次で威力', recommended: ['高3','早慶','国立難関'] },
      { name: '英文熟考 上', publisher: '旺文社', level: ['応用'], vol: '70題', use: '著者竹岡の名著。動画授業付き', recommended: ['高3','早慶','国立'] },
      { name: '英文解釈の技術100', publisher: '桐原書店', level: ['応用'], vol: '100技法', use: 'レベル別シリーズあり (基礎70/100/上級)', recommended: ['高3','難関大'] },
    ],
    '英語長文': [
      { name: 'やっておきたい英語長文 300', publisher: '河合出版', level: ['標準'], vol: '30題', use: '共通テスト〜GMARCH。1日1題15日で完成', recommended: ['高2-3','共通テスト'] },
      { name: 'やっておきたい英語長文 500/700/1000', publisher: '河合出版', level: ['標準','応用','難関'], vol: '各30題', use: 'レベル別。500=GMARCH / 700=早慶 / 1000=東大', recommended: ['高3','各大学別'] },
      { name: '英語長文ハイパートレーニング', publisher: '桐原書店', level: ['標準'], vol: 'Lv1-3', use: '音声CD付き、全文音読推奨', recommended: ['高2-3'] },
      { name: 'ポラリス英語長文', publisher: 'KADOKAWA', level: ['基礎','標準','応用'], vol: '各10-12題', use: '比較的新しい教材。動画解説豊富', recommended: ['高1-3'] },
    ],
    '英作文': [
      { name: 'ドラゴン・イングリッシュ基本英文100', publisher: '講談社', level: ['標準','応用'], vol: '100文', use: '英作文の基本骨格100パターン暗記', recommended: ['高2-3','英検準1級','国立二次'] },
      { name: '竹岡の英作文が面白いほど書ける本', publisher: 'KADOKAWA', level: ['応用'], vol: '入試頻出', use: '思考プロセス重視。論理展開の型を習得', recommended: ['高3','早慶','国立難関'] },
      { name: '減点されない英作文', publisher: '学研', level: ['応用'], vol: 'コツ集', use: 'ミスを避けるテクニック集', recommended: ['高3','国立二次'] },
    ],
    '英検': [
      { name: '英検準1級 過去問集', publisher: '旺文社', level: ['応用'], vol: '6回分', use: '過去問は必ず。音声CD必須', recommended: ['英検準1級'] },
      { name: '英検準1級 でる順パス単', publisher: '旺文社', level: ['応用'], vol: '1700語', use: '単語は必須。1日50語×1ヶ月', recommended: ['英検準1級'] },
      { name: '英検準1級 ライティング大特訓', publisher: 'テイエス企画', level: ['応用'], vol: '実例豊富', use: '採点基準に沿った書き方マスター', recommended: ['英検準1級'] },
    ],
  },
  '数学': {
    '基礎〜標準': [
      { name: '基礎問題精講 (数IA/IIB/III)', publisher: '旺文社', level: ['基礎'], vol: '約145題×3冊', use: '入試の最も基本的な型を押さえる。共通テスト7割への道', recommended: ['高1-2','共通テスト','日東駒専'] },
      { name: '青チャート (数IA/IIB/III)', publisher: '数研出版', level: ['基礎','標準'], vol: '約1000問×3冊', use: '典型問題網羅。例題のみでも良い。1冊3周が目安', recommended: ['高1-3','共通テスト','GMARCH','地方国立'] },
      { name: 'Focus Gold (数IA/IIB/III)', publisher: '啓林館', level: ['標準','応用'], vol: '青チャより難易度高め', use: '青チャの上位互換。難関大志望で青チャ→Focus Goldも可', recommended: ['高1-3','難関大志望'] },
      { name: '標準問題精講 (数IA/IIB/III)', publisher: '旺文社', level: ['標準','応用'], vol: '各100題+', use: '青チャ例題レベル終了後。記述演習に最適', recommended: ['高3','GMARCH','早慶'] },
    ],
    '応用〜難関': [
      { name: '1対1対応の演習 (数IA/IIB/III)', publisher: '東京出版', level: ['応用','難関'], vol: '各100題', use: '青チャ後の定番。解法パターンの体系化', recommended: ['高3','早慶','国立難関'] },
      { name: '新スタンダード演習', publisher: '東京出版', level: ['応用','難関'], vol: '難関大頻出', use: '大学への数学シリーズ。最難関準備', recommended: ['高3','東大','京大','医学部'] },
      { name: '理系プラチカ (数IA・IIB)', publisher: '河合出版', level: ['応用','難関'], vol: '各153題', use: '国立二次型記述演習の定番', recommended: ['高3','国立難関','医学部'] },
      { name: 'やさしい理系数学', publisher: '河合出版', level: ['難関'], vol: '50題', use: 'タイトル詐欺級に難しい。京大・東大向け', recommended: ['高3','東大','京大','医学部'] },
      { name: 'ハイレベル理系数学', publisher: '河合出版', level: ['難関'], vol: '200題', use: '最難関レベル。数学オリンピック的発想力', recommended: ['東大','京大','医学部'] },
      { name: '新数学演習 (大学への数学)', publisher: '東京出版', level: ['難関'], vol: '月刊+年1冊', use: '医学部・東大レベル最高峰問題集', recommended: ['東大','京大','医学部'] },
    ],
  },
  '現代文': [
    { name: '現代文読解力の開発講座', publisher: '駿台文庫', level: ['標準','応用'], vol: '10講', use: '評論文の読み方の基礎。筆者の主張把握訓練', recommended: ['高2-3','GMARCH','早慶'] },
    { name: '現代文と格闘する', publisher: '河合出版', level: ['応用','難関'], vol: '古典的名著', use: '難関大読解の王道。思考プロセスが学べる', recommended: ['高3','早慶','国立難関'] },
    { name: '現代文キーワード読解', publisher: 'Z会', level: ['基礎','標準','応用'], vol: '頻出単語集', use: '現代文の背景知識。読解前の必携書', recommended: ['高1-3'] },
    { name: '上級現代文 I/II', publisher: '桐原書店', level: ['応用','難関'], vol: '各30題', use: '超上級演習。東大・京大向け', recommended: ['高3','東大','京大'] },
    { name: 'マーク式基礎問題集 現代文', publisher: '河合出版', level: ['基礎','標準'], vol: '多数', use: '共通テスト対策の定番', recommended: ['共通テスト'] },
  ],
  '古文': [
    { name: '古文単語ゴロゴ', publisher: 'スタディカンパニー', level: ['基礎','標準'], vol: '565語', use: 'ゴロ合わせで暗記。即効性重視', recommended: ['高2-3','共通テスト'] },
    { name: '古文単語330 (マドンナ古文単語230の後継)', publisher: '学研', level: ['標準'], vol: '330語', use: '文化背景まで学べる。意味の深い理解', recommended: ['高2-3','国立'] },
    { name: 'ステップアップノート30 古典文法', publisher: '河合出版', level: ['基礎'], vol: '30項目', use: '古文文法の基礎固めに最適', recommended: ['高2','基礎'] },
    { name: '富井の古文読解をはじめからていねいに', publisher: 'ナガセ', level: ['基礎','標準'], vol: '講義本', use: '苦手生の救世主。読み方を基礎から', recommended: ['古文苦手'] },
    { name: '古文上達', publisher: 'Z会', level: ['標準','応用'], vol: '45講+演習50', use: '文法+読解の総合本。MARCH〜早慶向け', recommended: ['高3','GMARCH','早慶'] },
    { name: '得点奪取古文', publisher: '河合出版', level: ['応用','難関'], vol: '記述演習', use: '国立二次の記述対策', recommended: ['高3','国立難関'] },
  ],
  '漢文': [
    { name: '漢文早覚え速答法', publisher: 'Gakken', level: ['基礎','標準'], vol: '約1週間', use: '「いがよみ」「やろかよもよも」の定番。短期間で完成', recommended: ['共通テスト','速習'] },
    { name: '漢文ヤマのヤマ', publisher: '学研', level: ['標準','応用'], vol: '66句形', use: '句形網羅。私大・国立両対応', recommended: ['高3','GMARCH','国立'] },
    { name: 'ステップアップノート10 漢文句法', publisher: '河合出版', level: ['基礎'], vol: '10項目', use: '超基礎から始める漢文', recommended: ['高2','基礎'] },
    { name: '得点奪取漢文', publisher: '河合出版', level: ['応用','難関'], vol: '記述演習', use: '国立二次の記述対策', recommended: ['国立難関'] },
  ],
  '物理': [
    { name: '物理のエッセンス (力学・波動/電磁気・熱・原子)', publisher: '河合出版', level: ['基礎','標準'], vol: '2冊', use: '物理の王道入門書。基礎完成', recommended: ['高2-3','共通テスト','GMARCH'] },
    { name: '良問の風', publisher: '河合出版', level: ['標準'], vol: '約150題', use: 'エッセンス後の演習。共通テスト〜GMARCH', recommended: ['高3','GMARCH'] },
    { name: '名問の森 (力学・熱・波動I/波動II・電磁気・原子)', publisher: '河合出版', level: ['応用','難関'], vol: '2冊', use: '難関大レベル。早慶・国立に必須', recommended: ['高3','早慶','国立難関'] },
    { name: '難問題の系統とその解き方', publisher: 'ニュートンプレス', level: ['難関'], vol: '約400題', use: '物理最高峰問題集。東大・京大・医学部', recommended: ['東大','京大','医学部'] },
  ],
  '化学': [
    { name: '化学の新研究', publisher: '三省堂', level: ['標準','応用','難関'], vol: '参考書', use: '化学の辞書。分からない時の参照用', recommended: ['高2-3','難関大'] },
    { name: '化学重要問題集', publisher: '数研出版', level: ['標準','応用'], vol: '約300題', use: '化学の定番演習書。A/B問題でレベル別', recommended: ['高3','GMARCH','早慶','国立'] },
    { name: '化学の新演習', publisher: '三省堂', level: ['応用','難関'], vol: '約330題', use: '新研究の姉妹書。難関大向け', recommended: ['高3','早慶','国立難関'] },
    { name: '鎌田の有機化学', publisher: 'KADOKAWA', level: ['標準','応用'], vol: '講義本', use: '有機化学の名著。福間の無機と対', recommended: ['高3','難関大'] },
    { name: '福間の無機化学', publisher: 'KADOKAWA', level: ['標準','応用'], vol: '講義本', use: '無機化学の名著', recommended: ['高3','難関大'] },
  ],
  '生物': [
    { name: '大森徹の最強問題集159問', publisher: '学研', level: ['標準','応用'], vol: '159題', use: '生物の定番演習書', recommended: ['高3','GMARCH','早慶','国立'] },
    { name: '生物基礎問題精講', publisher: '旺文社', level: ['基礎','標準'], vol: '約100題', use: '基礎を固めるのに最適', recommended: ['高2-3','共通テスト'] },
    { name: '大学入試 生物の良問問題集', publisher: '旺文社', level: ['標準','応用'], vol: '多数', use: '幅広い大学対応', recommended: ['高3','難関大'] },
  ],
  '日本史': [
    { name: '石川晶康 日本史B講義の実況中継', publisher: '語学春秋社', level: ['基礎','標準','応用'], vol: '5冊', use: '通史理解の王道。マンガ並みに読める', recommended: ['高1-3','早慶','国立'] },
    { name: '金谷の日本史 なぜと流れがわかる本', publisher: 'ナガセ', level: ['基礎','標準'], vol: '3冊', use: '「なぜ」にフォーカス。因果理解', recommended: ['高1-3','共通テスト','GMARCH'] },
    { name: '日本史B 標準問題精講', publisher: '旺文社', level: ['応用','難関'], vol: '約80題', use: '論述対策の名著', recommended: ['高3','早慶','国立難関'] },
    { name: '詳説日本史B (教科書)', publisher: '山川出版社', level: ['基礎','標準','応用','難関'], vol: '教科書', use: '一次資料。通読+問題集必須', recommended: ['高1-3'] },
  ],
  '世界史': [
    { name: '荒巻の新世界史の見取り図 (古代〜中世/近世〜近代/現代)', publisher: 'ナガセ', level: ['標準','応用'], vol: '3冊', use: '通史理解の王道', recommended: ['高2-3','早慶','国立'] },
    { name: '世界史B 標準問題精講', publisher: '旺文社', level: ['応用','難関'], vol: '約100題', use: '論述対策', recommended: ['高3','早慶','国立難関'] },
    { name: '詳説世界史B (教科書)', publisher: '山川出版社', level: ['基礎','標準','応用'], vol: '教科書', use: '基本の通読用', recommended: ['高1-3'] },
  ],
};

// Helper: 志望校・学年から推奨教材を取得
function getRecommendedTextbooks(subject, targetLevel, grade) {
  const subjectData = TEXTBOOKS_DB[subject];
  if (!subjectData) return [];

  const allBooks = [];
  const traverse = (obj) => {
    if (Array.isArray(obj)) allBooks.push(...obj);
    else if (typeof obj === 'object') Object.values(obj).forEach(traverse);
  };
  traverse(subjectData);

  return allBooks.filter(b =>
    b.level.includes(targetLevel) ||
    (b.recommended && b.recommended.some(r => r.includes(grade) || r.includes(targetLevel)))
  );
}

// データを系統立てて文字列で返す（AIへのプロンプトに挿入するため）
function getTextbookContextForAI(subjects) {
  let context = '【利用可能な市販教材データベース】（以下の教材から生徒に合うものを具体的に指定してください）\n\n';
  for (const subject of subjects) {
    const data = TEXTBOOKS_DB[subject];
    if (!data) continue;
    context += `\n■ ${subject}\n`;
    const traverse = (obj, indent = '') => {
      if (Array.isArray(obj)) {
        obj.forEach(b => {
          context += `${indent}・『${b.name}』(${b.publisher}) Lv:${b.level.join('/')} — ${b.use}\n`;
        });
      } else if (typeof obj === 'object') {
        for (const [category, value] of Object.entries(obj)) {
          context += `${indent}【${category}】\n`;
          traverse(value, indent + '  ');
        }
      }
    };
    traverse(data);
  }
  return context;
}

// Browser環境ではwindowへ、Node環境ではmodule.exportsへ
if (typeof window !== 'undefined') {
  window.TEXTBOOKS_DB = TEXTBOOKS_DB;
  window.getTextbookContextForAI = getTextbookContextForAI;
  window.getRecommendedTextbooks = getRecommendedTextbooks;
}
